#!/usr/bin/env python3
"""Collect what changed in each watched upstream since its watermark.

Usage:
  python3 -I upstreams.py collect [--out DIR]
  python3 -I upstreams.py mark --report <path> [--out DIR]

The sources and their watermarks are `upstreams/sources.json` in the shared-workflow repo, found
from this script's real path. `collect` resolves each source's branch head, diffs the watched
paths between the watermark and that head, and writes, under --out:

  <id>.commits.md   the commits in the range, oldest first
  <id>.diff         the unified diff of the watched files
  heads.json        the head each source was diffed against, for `mark`

It changes nothing else. `mark` sets each source's `reviewed` to the head `collect` recorded, in
the repo's working tree, and refuses unless the report file exists: the watermark moves only once
the review it stands for is written down.
"""

import argparse
import base64
import difflib
import fnmatch
import json
import os
import subprocess
import sys
from datetime import date

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", ".."))
SOURCES = os.path.join(ROOT, "upstreams", "sources.json")
STATE_DIR = os.path.expanduser("~/.local/state/upstream-review")


def gh(*args):
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def gh_json(path):
    return json.loads(gh("api", path))


def watched(path, globs):
    return any(fnmatch.fnmatch(path, g) for g in globs)


def content(repo, path, sha):
    try:
        out = gh("api", f"repos/{repo}/contents/{path}?ref={sha}", "-q", ".content")
    except subprocess.CalledProcessError:
        return ""
    return base64.b64decode(out).decode("utf-8", "replace")


def collect(out):
    sources = json.load(open(SOURCES))["sources"]
    os.makedirs(out, exist_ok=True)
    for name in os.listdir(out):
        os.remove(os.path.join(out, name))

    heads = {}
    for s in sources:
        sid, repo, base = s["id"], s["repo"], s["reviewed"]
        head = gh_json(f"repos/{repo}/commits/{s['branch']}")["sha"]
        heads[sid] = head
        if head == base:
            print(f"{sid}: UP TO DATE at {head[:7]}")
            continue

        cmp = gh_json(f"repos/{repo}/compare/{base}...{head}?per_page=100")
        commits = cmp.get("commits", [])
        files = [f for f in cmp.get("files", []) if watched(f["filename"], s["paths"])
                 or watched(f.get("previous_filename", ""), s["paths"])]

        with open(os.path.join(out, f"{sid}.commits.md"), "w") as f:
            for c in commits:
                subject = c["commit"]["message"].splitlines()[0]
                f.write(f"- {c['sha'][:7]} {c['commit']['committer']['date'][:10]} {subject}\n")

        with open(os.path.join(out, f"{sid}.diff"), "w") as f:
            for fl in files:
                name = fl["filename"]
                if fl.get("patch"):
                    f.write(f"--- a/{fl.get('previous_filename', name)}@{base[:7]}\n+++ b/{name}@{head[:7]}\n")
                    f.write(fl["patch"] + "\n")
                    continue
                old = content(repo, fl.get("previous_filename", name), base) if fl["status"] != "added" else ""
                new = content(repo, name, head) if fl["status"] != "removed" else ""
                f.writelines(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                                                  f"a/{name}@{base[:7]}", f"b/{name}@{head[:7]}"))

        truncated = len(cmp.get("files", [])) >= 300 or cmp.get("total_commits", 0) > len(commits)
        print(f"{sid}: {base[:7]} -> {head[:7]}, {cmp.get('total_commits', len(commits))} commits, "
              f"{len(files)} watched files changed -> {out}/{sid}.diff")
        for fl in files:
            print(f"  {fl['status'].upper()} {fl['filename']}")
        if truncated:
            print(f"  TRUNCATED: the compare API capped the range; read the rest at "
                  f"https://github.com/{repo}/compare/{base}...{head}")

    with open(os.path.join(out, "heads.json"), "w") as f:
        json.dump(heads, f, indent=2)


def mark(out, report):
    if not os.path.isfile(report):
        sys.exit(f"no report at {report}: write it before moving the watermarks")
    heads = json.load(open(os.path.join(out, "heads.json")))
    data = json.load(open(SOURCES))
    for s in data["sources"]:
        if s["id"] in heads and s["reviewed"] != heads[s["id"]]:
            s["reviewed"] = heads[s["id"]]
            s["reviewedAt"] = date.today().isoformat()
            print(f"{s['id']}: reviewed -> {s['reviewed'][:7]}")
    with open(SOURCES, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["collect", "mark"])
    ap.add_argument("--out", default=os.path.join(STATE_DIR, "work"))
    ap.add_argument("--report")
    a = ap.parse_args()
    if a.command == "collect":
        collect(a.out)
    else:
        if not a.report:
            sys.exit("mark needs --report <path>")
        mark(a.out, a.report)


if __name__ == "__main__":
    main()
