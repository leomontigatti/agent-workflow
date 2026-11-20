#!/usr/bin/env python3
"""Ask triage: whether a model rules on a found race or edge case the way the user did.

Each case in cases.json is an issue for a race or an edge case a session found beside its work, and
the user's ruling on it: `drop` (closed as not planned) or `ask` (fixed or parked, so worth
raising); null when the user has not ruled. The eval checks out the default branch as it was when
the issue was opened, hands each model the issue's title and body with the rule of `implement`
step 2 from this checkout, and reads the ruling off the reply's last `RULING:` line.

Usage, from anywhere:
  python3 -I run.py rule [--models opus,fable:low] [--repeats 2] [--cases 1732,283] [--effort medium] [--jobs 4] [--out DIR]
  python3 -I run.py report DIR

DIR defaults to ~/.local/state/ask-triage/<today>. `rule` skips a reply already on disk.
"""

import concurrent.futures
import datetime
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.realpath(__file__))
# The reviewer calls, their output parsing and the manifest. Loaded by path: both files are run.py.
_spec = importlib.util.spec_from_file_location("recall", os.path.join(HERE, "..", "reviewer-recall", "run.py"))
recall = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(recall)


def rule_text():
    text = open(os.path.join(recall.ROOT, "skills", "implement", "WEIGHING.md"), encoding="utf-8").read()
    return text[text.index("A race the change itself brings in"):].strip()


def repo_for(name):
    repo = os.path.join(recall.PROJECTS, name)
    origin = subprocess.run(["git", "-C", repo, "remote", "get-url", "origin"], capture_output=True, text=True).stdout
    if f"leomontigatti/{name}." not in origin + ".":
        repo = os.path.join(recall.CACHE, name)
        if not os.path.isdir(repo):
            subprocess.run(["gh", "repo", "clone", f"leomontigatti/{name}", repo, "--", "-q", "--filter=blob:none"],
                           check=True, capture_output=True)
    recall.git(repo, "fetch", "-q", "origin")
    return repo


def prepare(case):
    """The commit the finder stood on and the prompt. The body is cut at its wake-up trigger or its
    recommendation, which record a ruling; comments stay out for the same reason."""
    repo = repo_for(case["repo"])
    issue = recall.gh_json(case, "issue", "view", str(case["issue"]), "--json", "title,body,createdAt")
    head = recall.git(repo, "rev-parse", "--abbrev-ref", "origin/HEAD").strip()
    sha = recall.git(repo, "rev-list", "-1", "--first-parent", f"--before={issue['createdAt']}", head).strip()
    body = re.split(r"^#+ (?:Wake-up trigger|Recommendation)", issue["body"], flags=re.M)[0].strip()
    prompt = ("A session working in this repo found the problem below beside the change it was making. This "
              "checkout is the code as it stood then. Read only; edit nothing.\n\n"
              f"<problem>\n# {issue['title']}\n\n{body}\n</problem>\n\n"
              "Rule on it by this rule, reading the code for what the ruling turns on (who reaches each "
              f"side and how often, and whether a hit is silent or loud):\n\n<rule>\n{rule_text()}\n</rule>\n\n"
              "Reply with the weighing in three short lines (likelihood, hit, fix), then end on one line: "
              "`RULING: drop` or `RULING: ask`.\n")
    return repo, sha, prompt


def rule(args):
    cases = load_cases(args.get("cases"))
    models = recall.parse_models(args.get("models", "opus,fable:low"), args.get("effort", "medium"))
    repeats, out = int(args.get("repeats", 2)), args["out"]
    os.makedirs(out, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="ask-triage-")
    jobs, worktrees, prompts = [], [], {}
    for case in cases:
        repo, sha, prompt = prepare(case)
        cid = f"{case['repo']}-{case['issue']}"
        prompts[cid] = hashlib.sha256(prompt.encode()).hexdigest()
        wt = os.path.join(tmp, cid)
        recall.git(repo, "worktree", "add", "-q", "--detach", wt, sha)
        worktrees.append((repo, wt))
        for model in models:
            for k in range(1, repeats + 1):
                path = os.path.join(out, f"{cid}.{model}.{k}.md")
                if not os.path.exists(path):
                    jobs.append((models[model], model, prompt, wt, path))
    asked = [f"{cid}.{m}.{k}" for cid in prompts for m in models for k in range(1, repeats + 1)]
    recall.claim(out, models, prompts, asked, "ruling")
    print(f"{len(jobs)} rulings to run", flush=True)
    try:
        with concurrent.futures.ThreadPoolExecutor(int(args.get("jobs", 4))) as pool:
            for path, status in pool.map(lambda j: recall.run_one(*j), jobs):
                print(f"{status:7} {os.path.basename(path)}", flush=True)
    finally:
        for repo, wt in worktrees:
            subprocess.run(["git", "-C", repo, "worktree", "remove", "--force", wt], capture_output=True)


def verdict(path):
    if not os.path.exists(path):
        return None
    found = re.findall(r"RULING:\s*`?(drop|ask)", open(path, encoding="utf-8").read())
    return found[-1] if found else None


def report(args):
    out = args["out"]
    manifest = json.load(open(os.path.join(out, "manifest.json")))
    models = sorted(manifest["models"])
    label = {m: f"{m} ({manifest['models'][m]['effort']})" for m in models}
    print("| issue | the user | " + " | ".join(label[m] for m in models) + " |")
    print("| -- | -- | " + " | ".join("--" for _ in models) + " |")
    score = {m: {"drop": [0, 0], "ask": [0, 0]} for m in models}
    for case in load_cases(None):
        cid = f"{case['repo']}-{case['issue']}"
        cells = []
        for m in models:
            got = [verdict(os.path.join(out, f"{r}.md")) for r in manifest["runs"] if r.startswith(f"{cid}.{m}.")]
            cells.append(", ".join(v or "none" for v in got))
            for v in got:
                if case["ruling"] and v:
                    score[m][case["ruling"]][0] += v == case["ruling"]
                    score[m][case["ruling"]][1] += 1
        if any(cells):
            print(f"| {cid} | {case['ruling'] or '-'} ({case['how']}) | " + " | ".join(cells) + " |")
    print()
    for m in models:
        d, a = score[m]["drop"], score[m]["ask"]
        print(f"{m}: dropped {d[0]}/{d[1]} of what the user dropped; raised {a[0]}/{a[1]} of what the user fixed or parked")
        metas = [json.load(open(p)) for p in (os.path.join(out, r + ".meta.json") for r in manifest["runs"]
                                              if r.split(".")[1] == m) if os.path.exists(p)]
        costs = [x["cost_usd"] for x in metas if x.get("cost_usd") is not None]
        if costs:
            print(f"{m}: cost mean ${sum(costs) / len(costs):.2f} per ruling, total ${sum(costs):.2f}; "
                  f"time mean {sum(x['wall_s'] for x in metas) / len(metas):.0f}s")


def load_cases(ids):
    cases = json.load(open(os.path.join(HERE, "cases.json"), encoding="utf-8"))
    return [c for c in cases if not ids or str(c["issue"]) in ids.split(",")]


def main(argv):
    if not argv or argv[0] not in ("rule", "report"):
        sys.exit(__doc__)
    args, rest = {}, argv[1:]
    while rest:
        a = rest.pop(0)
        if a.startswith("--"):
            args[a[2:]] = rest.pop(0)
        else:
            args["out"] = a
    args.setdefault("out", os.path.expanduser(f"~/.local/state/ask-triage/{datetime.date.today()}"))
    {"rule": rule, "report": report}[argv[0]](args)


if __name__ == "__main__":
    main(sys.argv[1:])
