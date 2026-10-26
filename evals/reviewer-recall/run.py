#!/usr/bin/env python3
"""Reviewer recall: which known bugs each correctness reviewer catches.

Each case in cases.json is a bug a correctness reviewer once found and a later commit fixed. The
eval checks out the commit before the fix, hands each model the prompt `implement` step 5 gives a
correctness reviewer, and asks a judge whether the review reports that bug.

Usage, from anywhere:
  python3 -I run.py review [--models opus,sol,luna] [--repeats 2] [--cases id,id] [--jobs 4] [--out DIR]
  python3 -I run.py grade DIR        judge every review in DIR that has no verdict yet
  python3 -I run.py report DIR       print recall per model and per case

DIR defaults to ~/.local/state/reviewer-recall/<today>. `review` skips a review already on disk, so
a stopped run resumes. Repos are read from ~/.t3/projects/<repo>, else cloned once into ~/.cache/reviewer-recall; a missing commit is fetched from
the PR's head ref. Worktrees are made under a temporary directory and removed at the end.
"""

import concurrent.futures
import datetime
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
PROJECTS = os.path.expanduser("~/.t3/projects")
CACHE = os.path.expanduser("~/.cache/reviewer-recall")  # a clone for a repo with no project checkout
TIMEOUT = 1800

# The models agents/models.md names for review roles, at the correctness role's effort.
CLAUDE_TOOLS = "Read,Grep,Glob,Bash(git diff:*),Bash(git log:*),Bash(git show:*)"


def claude(model):
    return lambda prompt, wt, out: (["claude", "-p", "--model", model, "--effort", "medium",
                                     "--allowedTools", CLAUDE_TOOLS, "--no-session-persistence",
                                     prompt], wt, None)


def codex(model):
    return lambda prompt, wt, out: (["codex", "exec", "-m", model, "-c", 'model_reasoning_effort="medium"',
                                     "-s", "read-only", "--ephemeral", "-C", wt, "-o", out, prompt], wt, out)


MODELS = {"opus": claude("claude-opus-5-5"), "sonnet": claude("claude-sonnet-5-5"),
          "sol": codex("gpt-6.1-sol"), "luna": codex("gpt-6-luna")}
JUDGE = ["claude", "-p", "--model", "claude-sonnet-5-5", "--effort", "low",
         "--no-session-persistence"]


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True, text=True).stdout


def correctness_brief():
    text = open(os.path.join(ROOT, "skills", "code-review", "CORRECTNESS.md"), encoding="utf-8").read()
    return "\n".join(re.sub(r"^\s*>\s?", "", line) for line in text.splitlines() if line.lstrip().startswith(">"))


def hotspots(repo, sha):
    try:
        text = git(repo, "show", f"{sha}:docs/agents/review.md")
    except subprocess.CalledProcessError:
        return "none listed"
    m = re.search(r"^## Hotspots\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1).strip() if m else "none listed"


def prompt_for(case, repo):
    title = json.loads(subprocess.run(["gh", "pr", "view", str(case["pr"]), "-R", f"leomontigatti/{case['repo']}",
                                       "--json", "title"], check=True, capture_output=True, text=True).stdout)["title"]
    commits = git(repo, "log", "--oneline", "--no-merges", f"{case['base']}..{case['before']}").strip()
    brief = correctness_brief().replace("<the project's hotspots>", hotspots(repo, case["before"]))
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


def review(args):
    cases = load_cases(args.get("cases"))
    models = args.get("models", "opus,sol,luna").split(",")
    repeats = int(args.get("repeats", 2))
    out = args["out"]
    os.makedirs(out, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="reviewer-recall-")
    jobs, worktrees = [], []
    for case in cases:
        repo = ensure(case)
        wt = os.path.join(tmp, case["id"])
        git(repo, "worktree", "add", "-q", "--detach", wt, case["before"])
        worktrees.append((repo, wt))
        prompt = prompt_for(case, repo)
        for model in models:
            for k in range(1, repeats + 1):
                path = os.path.join(out, f"{case['id']}.{model}.{k}.md")
                if not os.path.exists(path):
                    jobs.append((model, prompt, wt, path))
    print(f"{len(jobs)} reviews to run", flush=True)
    try:
        with concurrent.futures.ThreadPoolExecutor(int(args.get("jobs", 4))) as pool:
            for path, status in pool.map(lambda j: run_one(*j), jobs):
                print(f"{status:7} {os.path.basename(path)}", flush=True)
    finally:
        for repo, wt in worktrees:
            subprocess.run(["git", "-C", repo, "worktree", "remove", "--force", wt], capture_output=True)


def run_one(model, prompt, wt, path):
    tmp_out = path + ".tmp"
    cmd, cwd, out_file = MODELS[model](prompt, wt, tmp_out)
    try:
        run = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=TIMEOUT,
                             stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return path, "timeout"
    text = open(out_file, encoding="utf-8").read() if out_file and os.path.exists(out_file) else run.stdout
    if run.returncode or not text.strip():
        open(path + ".err", "w", encoding="utf-8").write(run.stderr[-4000:])
        return path, "failed"
    open(path, "w", encoding="utf-8").write(text)
    if out_file and os.path.exists(out_file):
        os.remove(out_file)
    return path, "ok"


def grade(args):
    out = args["out"]
    cases = {c["id"]: c for c in load_cases(None)}
    todo = [f for f in sorted(os.listdir(out)) if f.endswith(".md") and not os.path.exists(os.path.join(out, f[:-3] + ".json"))]

    def judge(name):
        case = cases[name.split(".")[0]]
        text = open(os.path.join(out, name), encoding="utf-8").read()
        prompt = ("You grade a code review against one known bug. Reply with JSON only: "
                  '{"found": true|false, "evidence": "<the review\'s matching sentence, or empty>"}.\n'
                  "found is true only when the review reports this bug: the same failure from the same "
                  "cause, in the same place, even in other words. A different problem in the same file, "
                  "or a vague worry with no path to this failure, is false.\n\n"
                  f"Known bug: {case['bug']}\nFiles: {', '.join(case['files'])}\n\n"
                  f"<review>\n{text}\n</review>\n")
        run = subprocess.run(JUDGE + [prompt], capture_output=True, text=True, timeout=600, stdin=subprocess.DEVNULL)
        m = re.search(r"\{.*\}", run.stdout, re.S)
        verdict = json.loads(m.group(0)) if m else {"found": None, "evidence": run.stdout[-500:]}
        json.dump(verdict, open(os.path.join(out, name[:-3] + ".json"), "w", encoding="utf-8"))
        return name, verdict["found"]

    with concurrent.futures.ThreadPoolExecutor(4) as pool:
        for name, found in pool.map(judge, todo):
            print(f"{str(found):5} {name}", flush=True)


def report(args):
    out = args["out"]
    rows = {}
    for name in sorted(os.listdir(out)):
        if name.endswith(".json"):
            case, model, _ = name[:-5].split(".")
            rows.setdefault(case, {}).setdefault(model, []).append(json.load(open(os.path.join(out, name)))["found"])
    models = sorted({m for r in rows.values() for m in r})
    cases = {c["id"]: c for c in load_cases(None)}
    print("| case | severity | first found by | " + " | ".join(models) + " |")
    print("| -- | -- | -- | " + " | ".join("--" for _ in models) + " |")
    for case, by in sorted(rows.items()):
        cells = [f"{sum(v is True for v in by.get(m, []))}/{len(by.get(m, []))}" if m in by else "" for m in models]
        print(f"| {case} | {cases[case]['severity']} | {cases[case]['found_by']} | " + " | ".join(cells) + " |")
    print()
    for m in models:
        runs = [v for r in rows.values() for v in r.get(m, [])]
        caught = sum(v is True for v in runs)
        print(f"{m}: {caught}/{len(runs)} reviews caught their bug ({100 * caught // max(len(runs), 1)}%)")
    for a in models:
        for b in models:
            if a < b:
                both = [r for r in rows.values() if a in r and b in r]
                union = sum(any(r[a]) or any(r[b]) for r in both)
                print(f"{a}+{b}: {union}/{len(both)} cases caught by at least one run of either")


def load_cases(ids):
    cases = json.load(open(os.path.join(HERE, "cases.json"), encoding="utf-8"))
    return [c for c in cases if not ids or c["id"] in ids.split(",")]


def main(argv):
    if not argv or argv[0] not in ("review", "grade", "report"):
        sys.exit(__doc__)
    args, rest = {}, argv[1:]
    while rest:
        a = rest.pop(0)
        if a.startswith("--"):
            args[a[2:]] = rest.pop(0)
        else:
            args["out"] = a
    args.setdefault("out", os.path.expanduser(f"~/.local/state/reviewer-recall/{datetime.date.today()}"))
    {"review": review, "grade": grade, "report": report}[argv[0]](args)


if __name__ == "__main__":
    main(sys.argv[1:])
