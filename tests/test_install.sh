#!/usr/bin/env bash
#
# Runs install.sh against a throwaway HOME, never the real one: a first install, a second run that
# must change nothing, --check on a clean and on a drifted install, and a conflict left alone.

set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOME="$(mktemp -d)"
export HOME
trap 'rm -rf "$HOME"' EXIT
fail=0
ok() { echo "ok   $*"; }
bad() { echo "FAIL $*"; fail=1; }

mkdir -p "$HOME/.agents/skills/grilling"

if "$repo/install.sh" >/dev/null; then bad "a conflict makes install exit 1"; else ok "a conflict makes install exit 1"; fi
if [ -d "$HOME/.agents/skills/grilling" ] && [ ! -L "$HOME/.agents/skills/grilling" ]; then ok "the conflicting dir is left alone"; else bad "the conflicting dir is left alone"; fi
rm -rf "$HOME/.agents/skills/grilling"

"$repo/install.sh" >/dev/null || bad "install exited non-zero"
if [ "$(readlink "$HOME/.agents/workflow")" = "$repo" ]; then ok "install root linked"; else bad "install root linked"; fi
for d in "$repo"/skills/*/; do
  n="$(basename "$d")"
  [ -f "$HOME/.agents/skills/$n/SKILL.md" ] || bad "skill $n not linked"
done
ok "every skill linked"

second="$("$repo/install.sh")"
if [ "$second" = "done" ]; then ok "second run changes nothing"; else bad "second run changes nothing"; fi
if "$repo/install.sh" --check >/dev/null; then ok "--check is clean after install"; else bad "--check is clean after install"; fi

rm "$HOME/.agents/skills/tdd"
ln -s "$HOME/.agents/workflow/skills/gone" "$HOME/.agents/skills/gone"
out="$("$repo/install.sh" --check || true)"
if grep -q "MISSING  $HOME/.agents/skills/tdd" <<<"$out"; then ok "--check reports a missing link"; else bad "--check reports a missing link"; fi
if grep -q "STALE    $HOME/.agents/skills/gone" <<<"$out"; then ok "--check reports a stale link"; else bad "--check reports a stale link"; fi
if [ ! -e "$HOME/.agents/skills/tdd" ]; then ok "--check changes nothing"; else bad "--check changes nothing"; fi

"$repo/install.sh" >/dev/null
if [ -L "$HOME/.agents/skills/tdd" ] && [ ! -L "$HOME/.agents/skills/gone" ]; then ok "install repairs drift"; else bad "install repairs drift"; fi

exit "$fail"
