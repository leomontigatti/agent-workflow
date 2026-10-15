#!/usr/bin/env bash
#
# Runs install.sh against a throwaway HOME, never the real one: a first install, a second run that
# must change nothing, --check on a clean and on a drifted install, a conflict left alone, and the
# merge into a settings file that already has hooks of its own.

set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOME="$(mktemp -d)"
export HOME
unset CLAUDE_SKILLS_DIR CODEX_SKILLS_DIR
trap 'rm -rf "$HOME"' EXIT
fail=0
ok() { echo "ok   $*"; }
bad() { echo "FAIL $*"; fail=1; }

mkdir -p "$HOME/.claude" "$HOME/.claude/skills/handoff"
echo '{"permissions":{"allow":["Bash(git status)"]},"hooks":{"PreToolUse":[{"matcher":"Bash","hooks":[{"type":"command","command":"/own/hook.sh"}]}]}}' >"$HOME/.claude/settings.json"

"$repo/install.sh" >/dev/null && bad "install with a conflict exited 0" || ok "a conflict makes install exit 1"
[ -d "$HOME/.claude/skills/handoff" ] && [ ! -L "$HOME/.claude/skills/handoff" ] && ok "the conflicting dir is left alone" || bad "conflict overwritten"
rm -rf "$HOME/.claude/skills/handoff"

"$repo/install.sh" >/dev/null || bad "install exited non-zero"
[ "$(readlink "$HOME/.local/share/agent-workflow")" = "$repo" ] && ok "install root linked" || bad "install root"
for d in "$repo"/skills/*/; do
  n="$(basename "$d")"
  [ -f "$HOME/.claude/skills/$n/SKILL.md" ] && [ -f "$HOME/.agents/skills/$n/SKILL.md" ] || bad "skill $n not linked for both harnesses"
done
ok "every skill linked for both harnesses"
[ -f "$HOME/.claude/agents/reviewer-opus.md" ] && [ -f "$HOME/.codex/agents/reviewer.toml" ] && ok "agents linked" || bad "agents"
jq -e '.permissions.allow == ["Bash(git status)"]' "$HOME/.claude/settings.json" >/dev/null && ok "other settings kept" || bad "settings lost"
jq -e '[.hooks.PreToolUse[].hooks[].command] | index("/own/hook.sh") != null' "$HOME/.claude/settings.json" >/dev/null && ok "own hook kept" || bad "own hook lost"
jq -e '[.hooks.PreToolUse[].hooks[].command] | any(endswith("/block-pkill-f.sh"))' "$HOME/.claude/settings.json" >/dev/null && ok "pkill hook wired for Claude" || bad "pkill hook (Claude)"
jq -e '[.hooks.SessionStart[].hooks[].command] | any(endswith("/check-tool-path.sh"))' "$HOME/.codex/hooks.json" >/dev/null && ok "path hook wired for Codex" || bad "path hook (Codex)"

second="$("$repo/install.sh")"
[ "$second" = "done" ] && ok "second run changes nothing" || { bad "second run changed:"; echo "$second"; }
"$repo/install.sh" --check >/dev/null && ok "--check is clean after install" || bad "--check reports drift after install"

rm "$HOME/.agents/skills/tdd"
ln -s "$HOME/.local/share/agent-workflow/skills/gone" "$HOME/.claude/skills/gone"
out="$("$repo/install.sh" --check || true)"
grep -q "MISSING  $HOME/.agents/skills/tdd" <<<"$out" && ok "--check reports a missing link" || bad "--check missed a missing link"
grep -q "STALE    $HOME/.claude/skills/gone" <<<"$out" && ok "--check reports a stale link" || bad "--check missed a stale link"
[ ! -e "$HOME/.agents/skills/tdd" ] && ok "--check changes nothing" || bad "--check changed something"

"$repo/install.sh" >/dev/null
[ -L "$HOME/.agents/skills/tdd" ] && [ ! -L "$HOME/.claude/skills/gone" ] && ok "install repairs drift" || bad "install did not repair drift"

exit "$fail"
