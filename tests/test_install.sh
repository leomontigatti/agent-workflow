#!/usr/bin/env bash
#
# Runs install.sh against a throwaway HOME, never the real one: a first install, a second run that
# must change nothing, --check on a clean and on a drifted install, a conflict left alone, and the
# merge into a settings file that already has hooks of its own. The install-check hook runs from
# a copy of the repo, so a skill can be added to the checkout without touching this one.

set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOME="$(mktemp -d)"
export HOME
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
if [ "$(readlink "$HOME/.agents/workflow")" = "$repo" ] && [ "$(readlink "$HOME/.claude/skills/tdd")" = "$HOME/.agents/skills/tdd" ]; then ok "install root linked"; else bad "install root linked"; fi
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
if jq -e '[.hooks.PreToolUse[].hooks[].command] | any(endswith("/block-push-default-branch.sh"))' "$HOME/.claude/settings.json" >/dev/null; then ok "push hook wired for Claude"; else bad "push hook wired for Claude"; fi
if jq -e '[.hooks.SessionStart[].hooks[].command] | any(endswith("/check-tool-path.sh"))' "$HOME/.codex/hooks.json" >/dev/null; then ok "path hook wired for Codex"; else bad "path hook wired for Codex"; fi
for f in "$HOME/.claude/settings.json" "$HOME/.codex/hooks.json"; do
  if jq -e --arg c "$HOME/.agents/workflow/hooks/check-install.sh" '[.hooks.SessionStart[].hooks[].command] | index($c) != null' "$f" >/dev/null; then ok "install hook wired in $(basename "$f")"; else bad "install hook wired in $(basename "$f")"; fi
done

second="$("$repo/install.sh")"
if [ "$second" = "done" ]; then ok "second run changes nothing"; else bad "second run changes nothing"; fi
if "$repo/install.sh" --check >/dev/null; then ok "--check is clean after install"; else bad "--check is clean after install"; fi

rm "$HOME/.agents/skills/tdd"
ln -s "$HOME/.agents/skills/gone" "$HOME/.claude/skills/gone"
out="$("$repo/install.sh" --check || true)"
if grep -q "MISSING  $HOME/.agents/skills/tdd" <<<"$out"; then ok "--check reports a missing link"; else bad "--check reports a missing link"; fi
if grep -q "STALE    $HOME/.claude/skills/gone" <<<"$out"; then ok "--check reports a stale link"; else bad "--check reports a stale link"; fi
if [ ! -e "$HOME/.agents/skills/tdd" ]; then ok "--check changes nothing"; else bad "--check changes nothing"; fi

"$repo/install.sh" >/dev/null
if [ -L "$HOME/.agents/skills/tdd" ] && [ ! -L "$HOME/.claude/skills/gone" ]; then ok "install repairs drift"; else bad "install repairs drift"; fi

# The install-check hook, run through the stable path the way a harness runs it, against a copy.
copy="$HOME/checkout"
mkdir -p "$copy"
tar -C "$repo" --exclude=.git -cf - . | tar -C "$copy" -xf -
ln -sfn "$copy" "$HOME/.agents/workflow"
"$copy/install.sh" >/dev/null
hook="$HOME/.agents/workflow/hooks/check-install.sh"
out="$("$hook")"
if [ -z "$out" ]; then ok "install hook is silent when clean"; else bad "install hook is silent when clean: $out"; fi
mkdir "$copy/skills/new-skill" && echo '# new' >"$copy/skills/new-skill/SKILL.md"
out="$("$hook")"
if jq -e '.hookSpecificOutput.hookEventName == "SessionStart"' <<<"$out" >/dev/null; then ok "install hook prints SessionStart JSON"; else bad "install hook prints SessionStart JSON: $out"; fi
ctx="$(jq -r '.hookSpecificOutput.additionalContext' <<<"$out" 2>/dev/null || true)"
if grep -q "skills/new-skill" <<<"$ctx" && grep -q "install.sh" <<<"$ctx"; then ok "install hook names the new skill and the fix"; else bad "install hook names the new skill and the fix: $ctx"; fi
if [ "$(wc -l <<<"$ctx")" -eq 1 ]; then ok "install hook warning is one line"; else bad "install hook warning is one line"; fi
if [ ! -e "$HOME/.agents/skills/new-skill" ]; then ok "install hook installs nothing"; else bad "install hook installs nothing"; fi
"$copy/install.sh" >/dev/null
out="$("$hook")"
if [ -z "$out" ]; then ok "install hook is silent after install"; else bad "install hook is silent after install: $out"; fi
rm -r "$copy/skills/new-skill"
out="$("$hook")"
if grep -q "new-skill" <<<"$out"; then ok "install hook reports a removed skill"; else bad "install hook reports a removed skill"; fi

exit "$fail"
