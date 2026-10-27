#!/usr/bin/env python3
"""Collect what changed in T3 Code between the last reviewed build and the installed one.

Usage: python3 -I changes.py <installed-version> [--since <version>] [--out DIR]

Reads the last reviewed version from STATE (unless --since is given), lists the
releases in between (same channel as the installed one), gathers their
"What's Changed" items, and diffs the T3 source files our workflows depend on
(WATCHED_PATHS) between the two commits. Writes everything under --out and
prints a short summary. Changes nothing else; `--mark` records the installed
version as reviewed.
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

REPO = "pingdotgg/t3code"
STATE_DIR = os.path.expanduser("~/.local/state/t3-update-review")
STATE = os.path.join(STATE_DIR, "state.json")

# T3 source that defines behavior our workflows rely on. Directories are
# listed so new files in them (e.g. a new MCP toolkit) show up too.
WATCHED_DIRS = ["apps/server/src/mcp/toolkits"]
WATCHED_PATHS = [
    "packages/provider-core/src/server/orchestrationInstructions.ts",
    "apps/server/src/storageCleanup.ts",
    "packages/contracts/src/worktreeSetup.ts",
    "packages/shared/src/projectScripts.ts",
    "apps/marketing/src/pages/schema/t3.json.ts",
    "apps/server/src/git/linkCreatedPullRequest.ts",
    "apps/server/src/orchestration-v2/ThreadLaunchService.ts",
    "apps/server/src/orchestration-v2/ThreadPullRequestService.ts",
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
    "apps/web/src/components/settings/ScheduledTasksSettings.tsx",
    "packages/contracts/src/settings.ts",
]

PR_LINE = re.compile(r"^\* (.+?) by @\S+ in (https://github\.com/\S+/pull/(\d+))\s*$")
NAME_SHA = re.compile(r"\(([0-9a-f]{7,40})\)\s*$")


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("installed")
    ap.add_argument("--since")
    ap.add_argument("--out", default=os.path.join(STATE_DIR, "work"))
    ap.add_argument("--mark", action="store_true", help="record the installed version as reviewed and exit")
    a = ap.parse_args()
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
    with open(os.path.join(a.out, "release-items.md"), "w") as f:
        f.write("\n".join(items) + "\n")

    old_sha, new_sha = sha_of(since), sha_of(installed)
    old_tree, new_tree = tree(old_sha), tree(new_sha)
    paths = set(WATCHED_PATHS)
    for d in WATCHED_DIRS:
        paths |= {p for p in old_tree | new_tree if p.startswith(d + "/") and ".test." not in p}
    changed = []
    with open(os.path.join(a.out, "watched.diff"), "w") as f:
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
            f.writelines(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                                              f"a/{p}@{old_sha}", f"b/{p}@{new_sha}"))

    print(f"RANGE: {since} ({old_sha}) -> {installed} ({new_sha}), {len(span)} {ch} releases")
    print(f"RELEASE ITEMS: {len(items)} -> {a.out}/release-items.md")
    print(f"WATCHED SOURCE: {len(changed)} changed -> {a.out}/watched.diff")
    for c in changed:
        print("  " + c)


if __name__ == "__main__":
    main()
