#!/usr/bin/env bash
#
# PreToolUse hook (matcher: Bash), wired at user level by install.sh for Claude Code and Codex;
# both harnesses send the command as `tool_input.command` and the session's directory as `cwd`.
#
# Blocks a `git push` that would update the repo's default branch. Every project takes changes to
# its default branch through a PR, but branch protection does not hold the user to it, and agents
# push as the user: a push to `main` simply lands. The user can still push there from their own
# terminal.
#
# Blocked: a refspec whose destination is the default branch (`main`, `HEAD:main`,
# `+HEAD:refs/heads/main`, `:main`), a push with no refspec or `HEAD` while the default branch is
# checked out, the same destinations under `--delete`, and `--all`, `--branches` or `--mirror`.
# The default branch is `origin/HEAD`, else both `main` and `master`. Only a `git` in command
# position counts: at the start or after `;`, `&&`, `||`, `|`, `&` or `(`, past env assignments
# and `sudo`.

set -euo pipefail

# The input goes through a file: a large command (a long heredoc) overflows an environment variable.
input="$(mktemp)"
trap 'rm -f "$input"' EXIT
cat >"$input"

python3 -I - "$input" <<'PY'
import json, os, re, shlex, subprocess, sys

data = json.loads(open(sys.argv[1], encoding="utf-8").read() or "{}")
command = (data.get("tool_input") or {}).get("command") or ""
cwd = data.get("cwd") or os.getcwd()
SEPARATORS = {";", "&&", "||", "|", "&", "(", ")", ";;", "|&"}
PREFIXES = {"sudo", "then", "do", "else", "elif", "if", "while", "until", "!", "{", "time", "command",
            "exec", "nohup", "env"}
HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")


def drop_heredoc_bodies(text):
    """A heredoc's body is data, not commands: keep its opening line and drop the rest."""
    kept, ends = [], []
    for line in text.split("\n"):
        if ends:
            if line.strip() == ends[0] or line == ends[0]:
                ends.pop(0)
            continue
        kept.append(line)
        ends = [m.group(2) for m in HEREDOC.finditer(line)]
    return "\n".join(kept)


def git(where, *args):
    run = subprocess.run(["git", "-C", where, *args], capture_output=True, text=True)
    return run.stdout.strip() if run.returncode == 0 else ""


def segments(text):
    # A newline ends a command; the `;` after it keeps a `#` comment from swallowing the next line.
    lexer = shlex.shlex(drop_heredoc_bodies(text).replace("\n", "\n;"), posix=True,
                        punctuation_chars=";&|()")
    lexer.whitespace_split = True
    current = []
    try:
        for token in lexer:
            if token in SEPARATORS:
                yield current
                current = []
            else:
                current.append(token)
    except ValueError:  # unbalanced quotes: judge what was read
        pass
    yield current


def blocked(tokens):
    while tokens and ("=" in tokens[0] and not tokens[0].startswith("-") or tokens[0] in PREFIXES):
        tokens = tokens[1:]
    if not tokens or os.path.basename(tokens[0]) != "git":
        return None
    where, rest = cwd, tokens[1:]
    while rest and rest[0].startswith("-"):
        flag = rest.pop(0)
        if flag in ("-C", "-c", "--git-dir", "--work-tree", "--namespace") and rest:
            value = rest.pop(0)
            if flag == "-C":
                where = os.path.join(where, value)
    if not rest or rest[0] != "push":
        return None
    positional, tags, args = [], False, rest[1:]
    while args:
        arg = args.pop(0)
        if arg in ("--all", "--branches", "--mirror"):
            return f"git push {arg}"
        if arg == "--tags":
            tags = True
        elif arg in ("-d", "--delete") or arg.startswith("--prune"):
            continue  # a deleted ref is a destination too: deleting the default branch is blocked
        elif arg in ("-o", "--push-option", "--repo", "--receive-pack", "--exec") and args:
            args.pop(0)
        elif not arg.startswith("-"):
            positional.append(arg)
    remote = positional[0] if positional else "origin"
    head = git(where, "symbolic-ref", "--short", f"refs/remotes/{remote}/HEAD")
    defaults = {head.split("/", 1)[1]} if "/" in head else {"main", "master"}
    current = git(where, "symbolic-ref", "--short", "HEAD")
    if not positional[1:]:
        if tags:
            return None  # `--tags` alone pushes tags only
        # Where a bare push goes follows push.default and the upstream: ask git.
        target = git(where, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{push}")
        dst = target.split("/", 1)[1] if "/" in target else current
        return f"git push to {dst}" if dst in defaults else None
    for refspec in positional[1:]:
        dst = refspec.lstrip("+").rsplit(":", 1)[-1] or refspec
        if dst == "HEAD":
            dst = current
        dst = dst.removeprefix("refs/heads/")
        if dst in defaults:
            return f"git push to {dst}"
    return None


for tokens in segments(command):
    reason = blocked(tokens)
    if reason:
        print(f"Blocked: {reason}, the default branch. Changes reach it through a PR: push a branch "
              "of your own and open a PR (the `pr` skill). If the user wants this push, they run it "
              "from their own terminal.", file=sys.stderr)
        sys.exit(2)
sys.exit(0)
PY
