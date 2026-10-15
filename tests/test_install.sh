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

if "$repo/install.sh" >/dev/null; then bad "a conflict makes install exit 1"; else ok "a conflict makes install exit 1"; fi
if [ -d "$HOME/.claude/skills/handoff" ] && [ ! -L "$HOME/.claude/skills/handoff" ]; then ok "the conflicting dir is left alone"; else bad "the conflicting dir is left alone"; fi
rm -rf "$HOME/.claude/skills/handoff"

"$repo/install.sh" >/dev/null || bad "install exited non-zero"
if [ "$(readlink "$HOME/.local/share/agent-workflow")" = "$repo" ]; then ok "install root linked"; else bad "install root linked"; fi
for d in "$repo"/skills/*/; do
  n="$(basename "$d")"
  if [ ! -f "$HOME/.claude/skills/$n/SKILL.md" ] || [ ! -f "$HOME/.agents/skills/$n/SKILL.md" ]; then
    bad "skill $n not linked for both harnesses"
  fi
done
ok "every skill linked for both harnesses"
if [ -f "$HOME/.claude/agents/reviewer-opus.md" ] && [ -f "$HOME/.codex/agents/reviewer.toml" ]; then ok "agents linked"; else bad "agents linked"; fi
if jq -e '.permissions.allow == ["Bash(git status)"]' "$HOME/.claude/settings.json" >/dev/null; then ok "other settings kept"; else bad "other settings kept"; fi
if jq -e '[.hooks.PreToolUse[].hooks[].command] | index("/own/hook.sh") != null' "$HOME/.claude/settings.json" >/dev/null; then ok "own hook kept"; else bad "own hook kept"; fi
if jq -e '[.hooks.PreToolUse[].hooks[].command] | any(endswith("/block-pkill-f.sh"))' "$HOME/.claude/settings.json" >/dev/null; then ok "pkill hook wired for Claude"; else bad "pkill hook wired for Claude"; fi
if jq -e '[.hooks.SessionStart[].hooks[].command] | any(endswith("/check-tool-path.sh"))' "$HOME/.codex/hooks.json" >/dev/null; then ok "path hook wired for Codex"; else bad "path hook wired for Codex"; fi

second="$("$repo/install.sh")"
if [ "$second" = "done" ]; then ok "second run changes nothing"; else bad "second run changes nothing"; fi
if "$repo/install.sh" --check >/dev/null; then ok "--check is clean after install"; else bad "--check is clean after install"; fi

rm "$HOME/.agents/skills/tdd"
ln -s "$HOME/.local/share/agent-workflow/skills/gone" "$HOME/.claude/skills/gone"
out="$("$repo/install.sh" --check || true)"
if grep -q "MISSING  $HOME/.agents/skills/tdd" <<<"$out"; then ok "--check reports a missing link"; else bad "--check reports a missing link"; fi
if grep -q "STALE    $HOME/.claude/skills/gone" <<<"$out"; then ok "--check reports a stale link"; else bad "--check reports a stale link"; fi
if [ ! -e "$HOME/.agents/skills/tdd" ]; then ok "--check changes nothing"; else bad "--check changes nothing"; fi

"$repo/install.sh" >/dev/null
if [ -L "$HOME/.agents/skills/tdd" ] && [ ! -L "$HOME/.claude/skills/gone" ]; then ok "install repairs drift"; else bad "install repairs drift"; fi

exit "$fail"
