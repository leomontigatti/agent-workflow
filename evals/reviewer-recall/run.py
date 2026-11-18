#!/usr/bin/env python3
"""Reviewer recall: which known bugs each correctness reviewer catches.

Each case in cases.json is a bug a correctness reviewer once found and a later commit fixed. The
eval checks out the commit before the fix, hands each model the prompt `implement` step 5 gives a
correctness reviewer, and asks a judge whether the review reports that bug.

Usage, from anywhere:
  python3 -I run.py review [--models opus,sol,luna] [--repeats 2] [--cases id,id] [--effort medium] [--jobs 4]
                            [--cases-file cases.json] [--brief FILE] [--out DIR]
  python3 -I run.py consult ...      the same options; asks for the hazards before the change exists
  python3 -I run.py grade DIR        judge every review in DIR that has no verdict yet
  python3 -I run.py report DIR       print recall, time and cost per model, and recall per case

A model in --models may name its own effort, `fable:low,opus:medium`; a bare one takes --effort.
Each review's wall time, cost and tokens go beside it in `<case>.<model>.<k>.meta.json`.

--cases-file picks the case set (a file beside run.py), --brief a variant of CORRECTNESS.md's brief
(a file whose `>` lines are the brief, like CORRECTNESS.md's own). A directory records both and holds
one of each, so its recall is one brief on one case set; `grade` and `report` read them from it.

DIR defaults to ~/.local/state/reviewer-recall/<today>. `review` skips a review already on disk, so
a stopped run resumes. Repos are read from ~/.t3/projects/<repo>, else cloned once into ~/.cache/reviewer-recall; a missing commit is fetched from
the PR's head ref. Worktrees are made under a temporary directory and removed at the end.

`consult` measures foresight instead: it checks out the PR's merge-base, where none of the change
exists, hands each model the PR title, the linked issue's body and the paths the change went on to
touch, and asks for the hazards an implementer should design out. The judge then decides whether a
consult warned of the case's bug. A directory holds reviews or consults, never both.
"""

import concurrent.futures
import datetime
import fcntl
import hashlib
import json
import os
import re
import statistics
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
PROJECTS = os.path.expanduser("~/.t3/projects")
CACHE = os.path.expanduser("~/.cache/reviewer-recall")  # a clone for a repo with no project checkout
TIMEOUT = 1800

# The models agents/models.md names for review roles, and the candidates for one. An alias is a
# run key's middle part, so it holds no dot. Effort defaults to the correctness role's.
EFFORTS = ("low", "medium", "high", "xhigh", "max")
CLAUDE_TOOLS = "Read,Grep,Glob,Bash(git diff:*),Bash(git log:*),Bash(git show:*)"
MODEL_IDS = {"opus": "claude-opus-5-5", "sonnet": "claude-sonnet-5-5", "fable": "claude-fable-5-2",
             "sol": "gpt-6.1-sol", "terra": "gpt-6.1-terra", "luna": "gpt-6-luna"}
FAMILY = {"opus": "claude", "sonnet": "claude", "fable": "claude", "sol": "codex", "terra": "codex", "luna": "codex"}
JUDGE = ["claude", "-p", "--model", "claude-sonnet-5-5", "--effort", "low",
         "--no-session-persistence"]


def command(family, model, prompt, wt, out, effort):
    if family == "claude":
        return ["claude", "-p", "--model", model, "--effort", effort, "--output-format", "json",
                "--allowedTools", CLAUDE_TOOLS, "--no-session-persistence", prompt]
    return ["codex", "exec", "--json", "-m", model, "-c", f'model_reasoning_effort="{effort}"',
            "-s", "read-only", "--ephemeral", "-C", wt, "-o", out, prompt]


def parse_output(family, stdout, out_file):
    """The review text and its measurements, from one reviewer call's output. Claude prints one
    JSON result whose `result` is the review; Codex prints JSONL events and writes the review to
    `out_file`, and reports tokens but no price."""
    if family == "claude":
        try:
            data = json.loads(stdout)
        except ValueError:
            return "", {}
        usage = data.get("usage") or {}
        meta = {"cost_usd": data.get("total_cost_usd"), "duration_ms": data.get("duration_ms"),
                "num_turns": data.get("num_turns"),
                "usage": {k: usage[k] for k in ("input_tokens", "cache_creation_input_tokens",
                                                "cache_read_input_tokens", "output_tokens") if k in usage}}
        return ("" if data.get("is_error") else data.get("result") or ""), meta
    usage = {}
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict) and event.get("type") == "turn.completed":
            for k, v in (event.get("usage") or {}).items():
                if isinstance(v, int):
                    usage[k] = usage.get(k, 0) + v
    text = open(out_file, encoding="utf-8").read() if out_file and os.path.exists(out_file) else ""
    return text, {"cost_usd": None, "usage": usage}


def parse_models(spec, effort):
    """`fable:low,opus` into {alias: {model, effort}}; a bare alias takes `effort`."""
    models = {}
    for item in spec.split(","):
        alias, _, own = item.partition(":")
        if alias not in MODEL_IDS:
            sys.exit(f"--models: {alias!r} is not one of {', '.join(MODEL_IDS)}")
        if (own or effort) not in EFFORTS:
            sys.exit(f"effort is one of {', '.join(EFFORTS)}")
        models[alias] = {"model": MODEL_IDS[alias], "effort": own or effort}
    return models


def normalize(manifest):
    """A manifest from before each model recorded its effort held a model id per alias and one
    top-level effort, medium when absent."""
    effort = manifest.pop("effort", "medium")
    manifest["models"] = {a: v if isinstance(v, dict) else {"model": v, "effort": effort}
                          for a, v in manifest["models"].items()}
    return manifest


DEFAULT_SETUP = {"brief": "CORRECTNESS.md", "cases": "cases.json"}


def setup_of(manifest):
    """The brief and case set a directory measures; one from before they were recorded measured
    CORRECTNESS.md's brief on cases.json."""
    return {k: manifest.get(k, v) for k, v in DEFAULT_SETUP.items()}


def claim(out, models, prompts, asked, kind="review", setup=None):
    """Record what this directory measures: a review on disk is reused only when its model, effort,
    prompt, brief and case set are the ones asked for now. The lock makes the check and the write
    one step, so two runs started together on one directory cannot both pass it."""
    manifest_path = os.path.join(out, "manifest.json")
    with open(os.path.join(out, ".lock"), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        manifest = (normalize(json.load(open(manifest_path))) if os.path.exists(manifest_path)
                    else {"models": {}, "prompts": {}, "runs": []})
        if manifest.setdefault("kind", "review" if manifest["runs"] else kind) != kind:
            sys.exit(f"{out} holds {manifest['kind']}s: use a new directory")
        # The brief's hash catches an edited brief under the same name, which the per-case prompt
        # hashes miss when the new run asks for other cases. A manifest from before it was recorded
        # takes the one asked for now.
        wanted = dict(DEFAULT_SETUP, **(setup or {}))
        held = dict(setup_of(manifest), brief_sha=manifest.get("brief_sha")) if manifest["runs"] else wanted
        clash = [f"{k} {held[k]}" for k, v in wanted.items() if held.get(k) not in (None, v)]
        if clash:
            sys.exit(f"{out} holds the {', '.join(clash)}: use a new directory")
        manifest.update({k: v if held.get(k) is None else held[k] for k, v in wanted.items()})
        for key, wanted in (("models", models), ("prompts", prompts)):
            clash = [k for k, v in wanted.items() if manifest[key].get(k, v) != v]
            if clash:
                sys.exit(f"{out} holds a different {key[:-1]} or effort for {', '.join(clash)}: use a new directory")
            manifest[key].update(wanted)
        manifest["runs"] = sorted(set(manifest["runs"]) | set(asked))  # only the runs someone asked for
        json.dump(manifest, open(manifest_path, "w"), indent=2)


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True, text=True).stdout


def correctness_brief(path=None):
    """The `>` lines of CORRECTNESS.md, or of a variant brief beside run.py."""
    path = os.path.join(HERE, path) if path else os.path.join(ROOT, "skills", "code-review", "CORRECTNESS.md")
    text = open(path, encoding="utf-8").read()
    return "\n".join(re.sub(r"^\s*>\s?", "", line) for line in text.splitlines() if line.lstrip().startswith(">"))


def hotspots(repo, sha):
    try:
        text = git(repo, "show", f"{sha}:docs/agents/review.md")
    except subprocess.CalledProcessError:
        return "none listed"
    m = re.search(r"^## Hotspots\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1).strip() if m else "none listed"


def gh_json(case, *args):
    return json.loads(subprocess.run(["gh", *args, "-R", f"leomontigatti/{case['repo']}"], check=True,
                                     capture_output=True, text=True).stdout)


def consult_prompt(case, repo, pr):
    """What a session knows at the end of `implement` step 1: the intent, the ticket and the files
    in play. The issue's comments and the PR body stay out: they record the review's findings."""
    issues = [gh_json(case, "issue", "view", str(i["number"]), "--json", "title,body")
              for i in pr["closingIssuesReferences"]]
    ticket = "\n\n".join(f"### {i['title']}\n\n{i['body']}" for i in issues) or "None: the title is all there is."
    paths = git(repo, "diff", "--name-status", f"{case['base']}...{case['before']}").strip()
    return ("You are consulted before a change is written. None of it exists yet: this checkout is the code "
            "it starts from. Read only; edit nothing.\n\n"
            f"The change: {pr['title']}\n\n<ticket>\n{ticket}\n</ticket>\n\n"
            f"The paths the author expects to touch (A is a new file, M an existing one):\n{paths}\n\n"
            "Read the existing code behind those paths and its callers. Then name the hazards this "
            "implementation is most likely to get wrong: a race between concurrent actors, a stale read, an "
            "edge case in the input or the stored state, a failure path. For each one give what goes wrong "
            "and for whom, the interleaving or input that triggers it, where in the code it would live, and "
            "the simplest design that avoids it. Report at most 8, the likeliest first, each traced to this "
            "code or this ticket: a hazard any change could have is noise.\n")


def prompt_for(case, repo, kind="review", brief_path=None):
    pr = gh_json(case, "pr", "view", str(case["pr"]), "--json", "title,closingIssuesReferences")
    if kind == "consult":
        return consult_prompt(case, repo, pr)
    title = pr["title"]
    commits = git(repo, "log", "--oneline", "--no-merges", f"{case['base']}..{case['before']}").strip()
    brief = correctness_brief(brief_path).replace("<the project's hotspots>", hotspots(repo, case["before"]))
    return (f"Before anything else, read `~/.agents/workflow/agents/reviewer.md` and follow it. "
            f"Axis: correctness.\n\nDiff: `git diff {case['base']}...{case['before']}`\n\n"
            f"Commits:\n{commits}\n\nWhat the change is meant to do: {title}\n\n{brief}\n")


def ensure(case):
    repo = os.path.join(PROJECTS, case["repo"])
    origin = subprocess.run(["git", "-C", repo, "remote", "get-url", "origin"], capture_output=True, text=True).stdout
    if f"leomontigatti/{case['repo']}." not in origin + ".":
        repo = os.path.join(CACHE, case["repo"])
        if not os.path.isdir(repo):
            subprocess.run(["gh", "repo", "clone", f"leomontigatti/{case['repo']}", repo, "--", "-q",
                            "--filter=blob:none"], check=True, capture_output=True)
    for sha in (case["base"], case["before"]):
        if subprocess.run(["git", "-C", repo, "cat-file", "-e", f"{sha}^{{commit}}"], capture_output=True).returncode:
            git(repo, "fetch", "-q", "origin", f"pull/{case['pr']}/head")
    return repo


def review(args, kind="review"):
    if kind == "consult" and "brief" in args:
        sys.exit("--brief is a review's: a consult has no correctness brief")
    setup = {"brief": args.get("brief", DEFAULT_SETUP["brief"]), "cases": args.get("cases-file", DEFAULT_SETUP["cases"])}
    for key, path in setup.items():
        if path != DEFAULT_SETUP[key] and not os.path.isfile(os.path.join(HERE, path)):
            sys.exit(f"--{'brief' if key == 'brief' else 'cases-file'}: no file {path} beside run.py")
    cases = load_cases(args.get("cases"), setup["cases"])
    if not cases:
        sys.exit(f"no case in {setup['cases']} matches --cases")
    models = parse_models(args.get("models", "opus,sol,luna"), args.get("effort", "medium"))
    repeats = int(args.get("repeats", 2))
    out = args["out"]
    os.makedirs(out, exist_ok=True)
    brief = None if setup["brief"] == DEFAULT_SETUP["brief"] else setup["brief"]
    if kind == "review":
        setup["brief_sha"] = hashlib.sha256(correctness_brief(brief).encode()).hexdigest()
    prompts = {c["id"]: prompt_for(c, ensure(c), kind, brief) for c in cases}
    asked = [f"{c['id']}.{m}.{k}" for c in cases for m in models for k in range(1, repeats + 1)]
    claim(out, models, {i: hashlib.sha256(p.encode()).hexdigest() for i, p in prompts.items()}, asked, kind, setup)
    tmp = tempfile.mkdtemp(prefix="reviewer-recall-")
    jobs, worktrees = [], []
    for case in cases:
        repo = ensure(case)
        wt = os.path.join(tmp, case["id"])
        git(repo, "worktree", "add", "-q", "--detach", wt, case["before" if kind == "review" else "base"])
        worktrees.append((repo, wt))
        prompt = prompts[case["id"]]
        for model in models:
            for k in range(1, repeats + 1):
                path = os.path.join(out, f"{case['id']}.{model}.{k}.md")
                if os.path.exists(path + ".err"):
                    os.remove(path + ".err")  # a failed run is retried
                if not os.path.exists(path):
                    jobs.append((models[model], model, prompt, wt, path))
    print(f"{len(jobs)} {kind}s to run", flush=True)
    try:
        with concurrent.futures.ThreadPoolExecutor(int(args.get("jobs", 4))) as pool:
            for path, status in pool.map(lambda j: run_one(*j), jobs):
                print(f"{status:7} {os.path.basename(path)}", flush=True)
    finally:
        for repo, wt in worktrees:
            subprocess.run(["git", "-C", repo, "worktree", "remove", "--force", wt], capture_output=True)


def run_one(spec, alias, prompt, wt, path):
    family, out_file = FAMILY[alias], path + ".tmp"
    started = time.monotonic()
    try:
        run = subprocess.run(command(family, spec["model"], prompt, wt, out_file, spec["effort"]), cwd=wt,
                             capture_output=True, text=True, timeout=TIMEOUT, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return path, "timeout"
    wall = round(time.monotonic() - started, 1)
    text, meta = parse_output(family, run.stdout, out_file)
    if os.path.exists(out_file):
        os.remove(out_file)
    if run.returncode or not text.strip():
        open(path + ".err", "w", encoding="utf-8").write((run.stderr + run.stdout)[-4000:])
        return path, "failed"
    meta_path = path[:-3] + ".meta.json"
    with open(meta_path + ".tmp", "w", encoding="utf-8") as f:
        json.dump({"model": spec["model"], "effort": spec["effort"], "wall_s": wall, **meta}, f, indent=2)
    os.replace(meta_path + ".tmp", meta_path)  # `report` never reads a half-written file
    open(path, "w", encoding="utf-8").write(text)  # last: a review on disk always has its measurements
    return path, "ok"


def grade(args):
    out = args["out"]
    manifest = json.load(open(os.path.join(out, "manifest.json")))
    cases = {c["id"]: c for c in load_cases(None, setup_of(manifest)["cases"])}
    consult = manifest.get("kind") == "consult"
    todo = [f for f in sorted(os.listdir(out)) if f.endswith(".md") and not os.path.exists(os.path.join(out, f[:-3] + ".json"))]

    def judge(name):
        case = cases[name.split(".")[0]]
        text = open(os.path.join(out, name), encoding="utf-8").read()
        rule = ("The review below was written before the change existed, as a list of hazards to design "
                "out; the bug is what the change then shipped. found is true only when a hazard warns of "
                "this bug: the same failure from the same cause, specific enough that an implementer who "
                "read it would have avoided the bug, even in other words. A different hazard in the same "
                "area, or a vague worry with no path to this failure, is false.\n\n" if consult else
                "found is true only when the review reports this bug: the same failure from the same "
                "cause, in the same place, even in other words. A different problem in the same file, "
                "or a vague worry with no path to this failure, is false.\n\n")
        prompt = ("You grade a code review against one known bug. Reply with JSON only: "
                  '{"found": true|false, "evidence": "<the review\'s matching sentence, or empty>"}.\n'
                  + rule +
                  f"Known bug: {case['bug']}\nFiles: {', '.join(case['files'])}\n\n"
                  f"<review>\n{text}\n</review>\n")
        try:
            run = subprocess.run(JUDGE + [prompt], capture_output=True, text=True, timeout=600,
                                 stdin=subprocess.DEVNULL)
            verdict = json.loads(re.search(r"\{.*\}", run.stdout, re.S).group(0))
        except (subprocess.TimeoutExpired, AttributeError, ValueError):
            return name, "error"  # nothing saved: the next `grade` retries it
        if run.returncode or not isinstance(verdict.get("found"), bool):
            return name, "error"
        json.dump(verdict, open(os.path.join(out, name[:-3] + ".json"), "w", encoding="utf-8"))
        return name, verdict["found"]

    with concurrent.futures.ThreadPoolExecutor(4) as pool:
        for name, found in pool.map(judge, todo):
            print(f"{str(found):5} {name}", flush=True)


def report(args):
    out = args["out"]
    manifest = normalize(json.load(open(os.path.join(out, "manifest.json"))))
    models = sorted(manifest["models"])
    label = {m: f"{m} ({manifest['models'][m]['effort']})" for m in models}
    setup = setup_of(manifest)
    cases = {c["id"]: c for c in load_cases(None, setup["cases"]) if c["id"] in manifest["prompts"]}
    print(f"brief: {setup['brief']}; cases: {setup['cases']}\n")
    # Every run asked for is True, False, or missing (failed, timed out, or not graded yet), so a
    # model that failed half its runs shows it instead of reporting recall on the rest.
    runs = {case: {m: [] for m in models} for case in cases}
    for run in manifest["runs"]:
        case, m, _ = run.split(".")
        path = os.path.join(out, run + ".json")
        runs[case][m].append(json.load(open(path))["found"] if os.path.exists(path) else None)
    print("| case | severity | first found by | " + " | ".join(label[m] for m in models) + " |")
    print("| -- | -- | -- | " + " | ".join("--" for _ in models) + " |")
    for case, by in sorted(runs.items()):
        cells = [(f"{sum(v is True for v in by[m])}/{sum(v is not None for v in by[m])}"
                  + ("" if None not in by[m] else f" ({by[m].count(None)} missing)")) if by[m] else "" for m in models]
        print(f"| {case} | {cases[case]['severity']} | {cases[case]['found_by']} | " + " | ".join(cells) + " |")
    print()
    for m in models:
        done = [v for by in runs.values() for v in by[m] if v is not None]
        missing = sum(by[m].count(None) for by in runs.values())
        caught = sum(done)
        print(f"{m}: {caught}/{len(done)} graded reviews caught their bug ({100 * caught // max(len(done), 1)}%)"
              + (f"; {missing} runs missing, so this is incomplete" if missing else ""))
    # Every case was caught once, by the model in `found_by`: a model's recall on its own family's
    # cases is inflated, so compare on the cases the other family first found.
    for m in models if any(FAMILY.get(c["found_by"].lower()) for c in cases.values()) else ():
        other = [v for case, by in runs.items() for v in by[m]
                 if v is not None and FAMILY.get(cases[case]["found_by"].lower()) not in (None, FAMILY[m])]
        print(f"{m} on the other family's cases: {sum(other)}/{len(other)}")
    for a in models:
        for b in models:
            if a < b:
                full = [by for by in runs.values() if by[a] and by[b] and None not in by[a] + by[b]]
                union = sum(any(by[a]) or any(by[b]) for by in full)
                print(f"{a}+{b}: {union}/{len(full)} fully graded cases caught by at least one run of either")
    print()
    for m in models:
        asked = [r for r in manifest["runs"] if r.split(".")[1] == m and r.split(".")[0] in cases]
        metas = [json.load(open(p)) for p in (os.path.join(out, r + ".meta.json") for r in asked) if os.path.exists(p)]
        walls = [x["wall_s"] for x in metas]
        costs = [x["cost_usd"] for x in metas if x.get("cost_usd") is not None]
        if not walls:
            print(f"{m}: no review timed")
            continue
        price = (f"cost mean ${statistics.mean(costs):.2f} per review, total ${sum(costs):.2f}" if costs
                 else "cost not reported")
        # Claude's three input counts are disjoint; Codex's input_tokens already holds its cached ones.
        tokens = [sum(x.get("usage", {}).get(k, 0) for k in ("input_tokens", "cache_creation_input_tokens",
                                                            "cache_read_input_tokens")) for x in metas]
        outs = [x.get("usage", {}).get("output_tokens", 0) for x in metas]
        print(f"{m}: time mean {statistics.mean(walls):.0f}s, median {statistics.median(walls):.0f}s; {price} "
              f"({len(walls)}/{len(asked)} reviews timed, {len(costs)} priced); "
              f"tokens mean {statistics.mean(tokens):,.0f} in, {statistics.mean(outs):,.0f} out")


def load_cases(ids, path="cases.json"):
    cases = json.load(open(os.path.join(HERE, path), encoding="utf-8"))
    return [c for c in cases if not ids or c["id"] in ids.split(",")]


def main(argv):
    if not argv or argv[0] not in ("review", "consult", "grade", "report"):
        sys.exit(__doc__)
    args, rest = {}, argv[1:]
    while rest:
        a = rest.pop(0)
        if a.startswith("--"):
            args[a[2:]] = rest.pop(0)
        else:
            args["out"] = a
    args.setdefault("out", os.path.expanduser(f"~/.local/state/reviewer-recall/{datetime.date.today()}"))
    {"review": review, "consult": lambda a: review(a, "consult"), "grade": grade, "report": report}[argv[0]](args)


if __name__ == "__main__":
    main(sys.argv[1:])
