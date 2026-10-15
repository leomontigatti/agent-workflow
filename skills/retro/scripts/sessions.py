#!/usr/bin/env python3
"""List the agent sessions that worked in a repo, with friction counters.

Usage: sessions.py [--repo PATH] [--since ISO-DATE | --days N]
       sessions.py --skeleton TRANSCRIPT


Matches Claude Code transcripts (~/.claude/projects/*/*.jsonl) and Codex
rollouts (~/.codex/sessions/**/rollout-*.jsonl) to the repo by their cwd:
the main checkout, any live worktree, or a deleted sibling of one. Without
--since/--days the window starts at the end of the last retro, found by its
`retro-window: FROM..TO` line, else 14 days ago.

--skeleton prints one transcript as a numbered timeline (user turns in full,
assistant text, tool calls and failing or oversized results clipped), so a
reader finds the friction without loading the raw JSONL.
"""

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HOME = Path.home()
CLAUDE_DIR = HOME / ".claude" / "projects"
CODEX_DIR = HOME / ".codex" / "sessions"
MARKER = re.compile(r"retro-window: (\d{4}-\d\d-\d\dT[\d:.]+Z?)\.\.(\d{4}-\d\d-\d\dT[\d:.]+Z?)")
BIG_OUTPUT = 20_000  # characters in one tool result


def git(repo, *args):
    out = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else ""


def repo_paths(repo):
    common = Path(git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    if not common.name:
        sys.exit(f"not a git repository: {repo}")
    main = common.parent if common.name == ".git" else common
    trees = [Path(l[9:]) for l in git(repo, "worktree", "list", "--porcelain").splitlines() if l.startswith("worktree ")]
    siblings = {t.parent for t in trees if t != main}
    return main, trees, siblings


def matches(cwd, main, trees, siblings):
    if not cwd:
        return None
    p = Path(cwd)
    for root in [main, *trees]:
        if p == root or root in p.parents:
            return "live"
    if any(s == p.parent or s in p.parents for s in siblings):
        return "live" if p.exists() else "gone"
    return None


def parse_ts(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") in ("text", "input_text", "output_text"))
    return ""


def new_stats(path, agent):
    return dict(agent=agent, path=str(path), id=path.stem, cwd=None, branch="", start=None, end=None,
                user=0, tools=0, errors=0, interrupts=0, big=0, compacts=0, markers=[], retro_cmd=False)


def scan_claude(path):
    s = new_stats(path, "claude")
    with open(path, errors="replace") as f:
        for line in f:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            ts = r.get("timestamp")
            if ts:
                s["start"] = s["start"] or ts
                s["end"] = ts
            s["cwd"] = s["cwd"] or r.get("cwd")
            s["branch"] = r.get("gitBranch") or s["branch"]
            if r.get("isCompactSummary"):
                s["compacts"] += 1
            msg = r.get("message") or {}
            content = msg.get("content")
            if r.get("type") == "assistant" and isinstance(content, list):
                s["tools"] += sum(1 for c in content if c.get("type") == "tool_use")
                for m in MARKER.finditer(text_of(content)):
                    s["markers"].append(m.group(2))
            elif r.get("type") == "user" and not r.get("isMeta"):
                if isinstance(content, list) and any(c.get("type") == "tool_result" for c in content):
                    for c in content:
                        if c.get("type") == "tool_result":
                            s["errors"] += bool(c.get("is_error"))
                            s["big"] += len(json.dumps(c.get("content"))) > BIG_OUTPUT
                    continue
                t = text_of(content)
                if t.startswith("[Request interrupted"):
                    s["interrupts"] += 1
                elif "<command-name>/compact<" in t:
                    s["compacts"] += 1
                elif t and not t.startswith(("<local-command", "<command-message", "<task-notification", "<system-reminder", "Caveat:")):
                    s["user"] += 1
                    s["retro_cmd"] |= "<command-name>/retro<" in t
    sub = path.with_suffix("") / "subagents"
    s["subagents"] = len(list(sub.glob("*.jsonl"))) if sub.is_dir() else 0
    return s


def scan_codex(path):
    s = new_stats(path, "codex")
    s["subagents"] = 0
    with open(path, errors="replace") as f:
        for line in f:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            ts = r.get("timestamp")
            if ts:
                s["start"] = s["start"] or ts
                s["end"] = ts
            p = r.get("payload") or {}
            if r.get("type") == "session_meta":
                s["cwd"] = p.get("cwd")
                s["branch"] = (p.get("git") or {}).get("branch") or ""
            elif r.get("type") == "response_item":
                kind = p.get("type")
                if kind in ("function_call", "custom_tool_call", "local_shell_call"):
                    s["tools"] += 1
                elif kind in ("function_call_output", "custom_tool_call_output"):
                    out = str(p.get("output", ""))
                    s["big"] += len(out) > BIG_OUTPUT
                    s["errors"] += bool(re.search(r'"exit_code":\s*[1-9]|Exit code: [1-9]', out))
                elif kind == "message":
                    t = text_of(p.get("content"))
                    if p.get("role") == "user" and t and not t.startswith(("<environment_context", "<user_instructions", "# AGENTS.md")):
                        s["user"] += 1
                        s["retro_cmd"] |= bool(re.match(r"\s*[$/]retro\b", t))
                    elif p.get("role") == "assistant":
                        s["markers"] += [m.group(2) for m in MARKER.finditer(t)]
            elif r.get("type") == "compacted":
                s["compacts"] += 1
            elif r.get("type") == "event_msg" and p.get("type") == "turn_aborted":
                s["interrupts"] += 1
    return s


def clip(t, n):
    t = " ".join(str(t).split())
    return t if len(t) <= n else t[:n] + f"…(+{len(t) - n})"


def skeleton(path):
    codex = path.name.startswith("rollout-")
    with open(path, errors="replace") as f:
        for n, line in enumerate(f, 1):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            ts = (r.get("timestamp") or "")[11:16]
            if codex:
                p = r.get("payload") or {}
                kind = p.get("type")
                if r.get("type") != "response_item":
                    if kind == "turn_aborted":
                        print(f"{n} {ts} INTERRUPT")
                    continue
                if kind == "message" and p.get("role") in ("user", "assistant"):
                    t = text_of(p.get("content"))
                    if p["role"] == "user" and not t.startswith(("<environment_context", "<user_instructions", "# AGENTS.md")):
                        print(f"{n} {ts} USER {clip(t, 1500)}")
                    elif p["role"] == "assistant":
                        print(f"{n} {ts} SAY {clip(t, 300)}")
                elif kind in ("function_call", "custom_tool_call", "local_shell_call"):
                    print(f"{n} {ts} CALL {p.get('name', kind)} {clip(p.get('arguments') or p.get('input') or p.get('action'), 200)}")
                elif kind in ("function_call_output", "custom_tool_call_output"):
                    out = str(p.get("output", ""))
                    if len(out) > BIG_OUTPUT or re.search(r'"exit_code":\s*[1-9]|Exit code: [1-9]', out):
                        print(f"{n} {ts} RESULT[{len(out)} chars] {clip(out, 400)}")
                continue
            msg = r.get("message") or {}
            content = msg.get("content")
            if r.get("isCompactSummary"):
                print(f"{n} {ts} COMPACTED")
            elif r.get("type") == "assistant" and isinstance(content, list):
                for c in content:
                    if c.get("type") == "text":
                        print(f"{n} {ts} SAY {clip(c['text'], 300)}")
                    elif c.get("type") == "tool_use":
                        print(f"{n} {ts} CALL {c.get('name')} {clip(json.dumps(c.get('input')), 200)}")
            elif r.get("type") == "user" and not r.get("isMeta"):
                if isinstance(content, list) and any(c.get("type") == "tool_result" for c in content):
                    for c in content:
                        size = len(json.dumps(c.get("content")))
                        if c.get("type") == "tool_result" and (c.get("is_error") or size > BIG_OUTPUT):
                            tag = "ERROR" if c.get("is_error") else f"BIG[{size} chars]"
                            print(f"{n} {ts} {tag} {clip(text_of(c.get('content')) or c.get('content'), 400)}")
                    continue
                t = text_of(content)
                if t.startswith("[Request interrupted"):
                    print(f"{n} {ts} INTERRUPT")
                elif t.startswith("<task-notification"):
                    print(f"{n} {ts} NOTIFY {clip(t, 200)}")
                elif t and not t.startswith(("<local-command", "<command-message", "<system-reminder", "Caveat:")):
                    print(f"{n} {ts} USER {clip(t, 1500)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.getcwd())
    ap.add_argument("--since")
    ap.add_argument("--days", type=int)
    ap.add_argument("--skeleton", type=Path)
    a = ap.parse_args()
    if a.skeleton:
        return skeleton(a.skeleton)

    main_root, trees, siblings = repo_paths(a.repo)
    now = dt.datetime.now(dt.timezone.utc)
    files = [(p, scan_claude) for p in CLAUDE_DIR.glob("*/*.jsonl")] + [(p, scan_codex) for p in CODEX_DIR.glob("**/rollout-*.jsonl")]

    sessions, noise = [], 0
    for path, scan in files:
        s = scan(path)
        s["where"] = matches(s["cwd"], main_root, trees, siblings)
        if not s["where"] or not s["end"]:
            continue
        if s["tools"] <= 1 and s["user"] <= 1:
            noise += 1  # title and branch-name generators (one structured reply), aborted starts
            continue
        sessions.append(s)

    if a.since:
        since, source = parse_ts(a.since if "T" in a.since else a.since + "T00:00:00Z"), "--since"
    elif a.days:
        since, source = now - dt.timedelta(days=a.days), f"--days {a.days}"
    else:
        last = max(((m, s["id"]) for s in sessions for m in s["markers"]), default=None)
        cmd = max(((s["end"], s["id"]) for s in sessions if s["retro_cmd"] and not s["markers"]), default=None)
        best = max(filter(None, [last, cmd]), default=None)
        if best:
            since, source = parse_ts(best[0]), f"last retro (session {best[1]})"
        else:
            since, source = now - dt.timedelta(days=14), "default 14 days (no earlier retro found)"

    window = sorted((s for s in sessions if parse_ts(s["end"]) > since), key=lambda s: s["start"])
    agents = sorted({s["agent"] for s in window})
    print(f"repo\t{main_root}")
    print(f"window\t{since.strftime('%Y-%m-%dT%H:%M:%SZ')}..{now.strftime('%Y-%m-%dT%H:%M:%SZ')}\t{source}")
    print(f"sessions\t{len(window)} in window ({', '.join(agents) or 'none'}); {noise} noise sessions skipped; codex logs {'found' if CODEX_DIR.is_dir() else 'absent'}")
    cols = ["id", "agent", "start", "end", "branch", "where", "user", "tools", "errors", "interrupts", "big", "compacts", "subagents", "mb", "path"]
    print("\t".join(cols))
    for s in window:
        s["mb"] = f"{os.path.getsize(s['path']) / 1e6:.1f}"
        s["start"], s["end"] = s["start"][:16], s["end"][:16]
        print("\t".join(str(s[c]) for c in cols))


if __name__ == "__main__":
    main()
