#!/usr/bin/env python3
"""Collect what changed in T3 Code between the last reviewed build and the installed one.

Usage: python3 -I changes.py <installed-version> [--since <version>] [--out DIR]
       python3 -I changes.py --digest FILE... [--out DIR]

Reads the last reviewed version from STATE (unless --since is given), lists the
releases in between (same channel as the installed one), gathers their
"What's Changed" items, and diffs the T3 source files our workflows depend on
(WATCHED_PATHS) between the two commits. Writes everything under --out, cut
into parts that each fit one Read (`release-items.<n>.md`, `watched.<n>.diff`)
and listed in `index.md`, and prints a short summary. Changes nothing else; `--mark` records the installed
version as reviewed.

--digest writes `entries.md` under --out: one line per `### ` entry of each
dependency file given, with its file and line, its status (the `## ` section it
sits in) and its **Breaks if** / **Would improve if** clauses cut to one line.
"""

import argparse
import base64
import difflib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", "..", "lib"))
import parts  # noqa: E402

REPO = "pingdotgg/t3code"
STATE_DIR = os.path.expanduser("~/.local/state/t3-update-review")
STATE = os.path.join(STATE_DIR, "state.json")

# T3 source that defines behavior our workflows rely on. Directories are
# listed so new files in them (e.g. a new MCP toolkit) show up too.
WATCHED_DIRS = ["apps/server/src/mcp/toolkits"]
WATCHED_PATHS = [
    "packages/provider-core/src/server/orchestrationInstructions.ts",
    "packages/provider-core/src/server/runtimeInstructions.ts",
    "apps/server/src/storageCleanup.ts",
    "packages/contracts/src/worktreeSetup.ts",
    "packages/shared/src/projectScripts.ts",
    "apps/marketing/src/pages/schema/t3.json.ts",
    "apps/server/src/git/linkCreatedPullRequest.ts",
    "apps/server/src/orchestration-v2/ThreadLaunchService.ts",
    "apps/server/src/orchestration-v2/ThreadPullRequestService.ts",
    "apps/server/src/orchestration-v2/WorktreeBranchSync.ts",
    "apps/server/src/orchestration-v2/ProviderTurnStartService.ts",
    "apps/server/src/project/ProjectSetupScriptRunner.ts",
    "apps/server/src/preview/ServerBrowserPage.ts",
    "packages/contracts/src/orchestratorMcp.ts",
    "packages/contracts/src/t3ProjectFile.ts",
    "packages/contracts/src/threadPullRequest.ts",
    "docs/user/project-settings.md",
    "docs/user/background-service.md",
    "apps/server/src/mcp/OrchestratorMcpService.ts",
    "apps/server/src/mcp/threadAccess.ts",
    "apps/server/src/scheduledTasks/ScheduledTaskService.ts",
    "apps/server/src/scheduledTasks/Schedule.ts",
    "apps/server/src/worktreesDirectory.ts",
    "apps/server/src/workspace/restoreMissingWorktree.ts",
    "apps/server/src/orchestration-v2/ThreadDeletion.ts",
    "apps/web/src/components/settings/ScheduledTasksSettings.tsx",
    "packages/contracts/src/settings.ts",
    "apps/server/src/process/agentScope.ts",
    "apps/desktop/src/shell/DesktopShellEnvironment.ts",
    "docs/user/permission-modes.md",
]

PR_LINE = re.compile(r"^\* (.+?) by @\S+ in (https://github\.com/\S+/pull/(\d+))\s*$")
NAME_SHA = re.compile(r"\(([0-9a-f]{7,40})\)\s*$")
CLAUSES = ("Breaks if", "Would improve if")
CLAUSE_CHARS = 160


def gh(*args):
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def channel(version):
    m = re.search(r"-(nightly|preview)\.", version)
    return m.group(1) if m else "stable"


def releases():
    out = gh("release", "list", "-R", REPO, "-L", "300", "--json", "tagName,name,publishedAt")
    return sorted(json.loads(out), key=lambda r: r["publishedAt"])


def tree(sha):
    out = gh("api", f"repos/{REPO}/git/trees/{sha}?recursive=1", "-q", ".tree[] | select(.type==\"blob\") | .path")
    return set(out.split())


def content(path, sha):
    try:
        out = gh("api", f"repos/{REPO}/contents/{path}?ref={sha}", "-q", ".content")
    except subprocess.CalledProcessError:
        return None
    return base64.b64decode(out).decode("utf-8", "replace")


def clip(text):
    text = " ".join(text.split())
    return text if len(text) <= CLAUSE_CHARS else text[:CLAUSE_CHARS - 1].rstrip() + "…"


def digest(paths):
    out = []
    for path in paths:
        status, entry, fields, field = None, None, {}, None

        def flush():
            if entry:
                clauses = "; ".join(f"{k}: {clip(fields[k])}" for k in CLAUSES if k in fields)
                out.append(f"- {path}:{entry[1]} `{entry[0]}` ({status})" + (f" {clauses}" if clauses else ""))

        for n, line in enumerate(open(path, encoding="utf-8"), 1):
            line = line.rstrip("\n")
            if line.startswith("## ") or line.startswith("### "):
                flush()
                entry, fields, field = None, {}, None
                if line.startswith("## "):
                    status = line[3:].strip().lower()
                else:
                    entry = (line[4:].strip(), n)
            elif entry and (m := re.match(r"^- \*\*([^*]+?):\*\*\s*(.*)$", line)):
                field = m.group(1)
                fields[field] = m.group(2)
            elif entry and field and line.startswith("  "):
                fields[field] += " " + line.strip()
            else:
                field = None
        flush()
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("installed", nargs="?")
    ap.add_argument("--digest", nargs="+", metavar="FILE", help="write entries.md for these dependency files and exit")
    ap.add_argument("--since")
    ap.add_argument("--out", default=os.path.join(STATE_DIR, "work"))
    ap.add_argument("--mark", action="store_true", help="record the installed version as reviewed and exit")
    a = ap.parse_args()
    if a.digest:
        os.makedirs(a.out, exist_ok=True)
        path = os.path.join(a.out, "entries.md")
        text = digest(a.digest)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"ENTRIES: {text.count(chr(10))} in {path}, {len(text)} chars")
        return
    if not a.installed:
        ap.error("the installed version is required")
    installed = a.installed.lstrip("v")

    rels = releases()
    by_version = {r["tagName"].lstrip("v"): r for r in rels}
    if installed not in by_version:
        sys.exit(f"installed version {installed} has no release in {REPO}")

    def sha_of(v):
        m = NAME_SHA.search(by_version[v]["name"])
        return m.group(1) if m else "v" + v

    if a.mark:
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(STATE, "w") as f:
            json.dump({"version": installed, "commit": sha_of(installed),
                       "reviewedAt": datetime.now(timezone.utc).isoformat(timespec="seconds")}, f, indent=2)
        print(f"marked {installed} as reviewed")
        return

    since = a.since
    if not since and os.path.exists(STATE):
        since = json.load(open(STATE))["version"]
    if not since:
        sys.exit("no reviewed version recorded; pass --since <version> or run --mark")
    since = since.lstrip("v")
    if since == installed:
        print(f"UP TO DATE: {installed} already reviewed")
        return
    if since not in by_version:
        sys.exit(f"reviewed version {since} has no release in {REPO}")

    lo, hi = by_version[since]["publishedAt"], by_version[installed]["publishedAt"]
    ch = channel(installed)
    span = [r for r in rels if lo < r["publishedAt"] <= hi and channel(r["tagName"]) == ch]

    os.makedirs(a.out, exist_ok=True)
    for name in os.listdir(a.out):
        os.remove(os.path.join(a.out, name))

    items, seen = [], set()
    for r in span:
        body = gh("release", "view", r["tagName"], "-R", REPO, "--json", "body", "-q", ".body")
        for line in body.splitlines():
            m = PR_LINE.match(line.strip())
            if m and m.group(3) not in seen:
                seen.add(m.group(3))
                items.append(f"- #{m.group(3)} {m.group(1)} ({r['tagName']})")
    out = parts.Parts(a.out)
    out.add("release-items", "md", [("", item + "\n") for item in items])

    old_sha, new_sha = sha_of(since), sha_of(installed)
    old_tree, new_tree = tree(old_sha), tree(new_sha)
    paths = set(WATCHED_PATHS)
    for d in WATCHED_DIRS:
        paths |= {p for p in old_tree | new_tree if p.startswith(d + "/") and ".test." not in p}
    changed, diffs = [], []
    for p in sorted(paths):
        if p not in old_tree and p not in new_tree:
            changed.append(f"MISSING {p} (watched path no longer exists; update WATCHED_PATHS)")
            continue
        old = content(p, old_sha) if p in old_tree else ""
        new = content(p, new_sha) if p in new_tree else ""
        if old == new:
            continue
        kind = "ADDED" if p not in old_tree else "REMOVED" if p not in new_tree else "CHANGED"
        changed.append(f"{kind} {p}")
        diffs.append((p, "".join(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                                                      f"a/{p}@{old_sha}", f"b/{p}@{new_sha}"))))
    out.add("watched", "diff", diffs)
    index = out.write_index()

    print(f"RANGE: {since} ({old_sha}) -> {installed} ({new_sha}), {len(span)} {ch} releases")
    print(f"RELEASE ITEMS: {len(items)}")
    print(f"WATCHED SOURCE: {len(changed)} changed")
    print(f"PARTS: {len(out.rows)}, listed in {index}")
    for c in changed:
        print("  " + c)


if __name__ == "__main__":
    main()
