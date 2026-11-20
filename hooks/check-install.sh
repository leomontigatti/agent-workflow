#!/usr/bin/env bash
#
# SessionStart hook, wired by install.sh into the Claude Code and Codex CLIs' user settings. Both
# add a SessionStart hook's `hookSpecificOutput.additionalContext` to the session's context.
# Capy runs no hooks, so on a Capy thread this one never fires: there the project's Setup runs
# install.sh on each thread's fresh machine, and the install starts in step with its checkout.
#
# Warns at the start of a session when the install has drifted from the checkout it links to.
# A pull goes live for the skills already linked, but a skill a merge adds or removes changes
# only once install.sh runs, and nothing runs it after a pull. The hook runs `install.sh --check`
# and reports what it found; it never installs, since install.sh runs only when the user asks.

set -uo pipefail

repo="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"
# Without jq install.sh cannot check, and the check-tool-path hook already warns about jq.
command -v jq >/dev/null 2>&1 || exit 0
[ -x "$repo/install.sh" ] || exit 0

report="$("$repo/install.sh" --check 2>&1)" && exit 0

# One entry per drifted target, its path shortened to ~ and the link it points at dropped.
report="${report//"$HOME"/\~}"
found="$(sed -e 's/ -> .*//' -e 's/  */ /g' <<<"$report" | paste -sd ';' - | sed 's/;/; /g')"

message="The agent workflow install has drifted from its checkout (a pull added or removed a skill, brief or hook): ${found}. Tell the user; the fix is running ~/.agents/workflow/install.sh, which you run only when the user asks."

jq -cn --arg m "$message" '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $m}}'
