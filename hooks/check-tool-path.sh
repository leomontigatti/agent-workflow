#!/usr/bin/env bash
#
# SessionStart hook, wired at user level by install.sh for Claude Code and Codex. Both harnesses
# add a SessionStart hook's `hookSpecificOutput.additionalContext` to the session's context.
#
# Warns at the start of a session whose shell cannot find a tool the work needs: the ones every
# shared skill uses, plus one per line in the project's `.agents/required-tools`, when it exists.
# The harness inherits PATH from the desktop login session, which reads `~/.profile`, not
# `~/.bashrc`, so a directory added only in `~/.bashrc` is missing from an agent's shell. Agents
# that prefix every command with `export PATH=...` hide that cause from the next session. The hook
# only reports: it never edits PATH, so the fix stays at the source.

set -uo pipefail

tools=(git gh jq python3)

project_dir="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
if [ -f "$project_dir/.agents/required-tools" ]; then
  while IFS= read -r line; do
    line="${line%%#*}"
    line="${line//[[:space:]]/}"
    [ -n "$line" ] && tools+=("$line")
  done <"$project_dir/.agents/required-tools"
fi

missing=()
for tool in "${tools[@]}"; do
  command -v "$tool" >/dev/null 2>&1 || missing+=("$tool")
done

if [ "${#missing[@]}" -eq 0 ]; then
  exit 0
fi

# The tool names come from a file the project controls: keep only characters a command name uses,
# so the message below needs no JSON escaping.
names="$(printf '%s ' "${missing[@]}" | tr -cd 'A-Za-z0-9._+ -')"
names="${names% }"

message="This session's shell cannot find ${names} on PATH. The harness inherits PATH from the desktop login session, so a tool directory added only in ~/.bashrc is missing here; ~/.profile is where it belongs. Do not prefix commands with \`export PATH=...\`: tell the user, who fixes it at the source. Work that needs a missing tool stops and says so, instead of working around it."

# Printed without jq, so the warning needs nothing but bash. The message holds no double quote or
# backslash, the two characters JSON would need escaped.
printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$message"
