#!/usr/bin/env bash
#
# Runs install.sh against a throwaway HOME, never the real one: a first install, a second run that
# must change nothing, --check on a clean and on a drifted install, a conflict left alone, and a
# link another run makes first.

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

# A second run that links skills/tdd between this run's check and its ln: an ln on PATH stands in
# for it, making the link just before the real ln runs. It runs from a copy, because an
# install.sh that links inside the other run's link writes into its own repo.
copy="$HOME/copy" bin="$HOME/bin" race="$HOME/race" broken="$HOME/broken"
mkdir -p "$copy/skills/tdd" "$bin/race" "$bin/broken" "$race"
cp "$repo/install.sh" "$copy/install.sh"
cat >"$bin/race/ln" <<'EOF'
#!/usr/bin/env bash
case "${*: -1}" in
  */.agents/skills/tdd) /usr/bin/ln -s "$HOME/.agents/workflow/skills/tdd" "$HOME/.agents/skills/tdd" && touch "$HOME/raced" ;;
esac
exec /usr/bin/ln "$@"
EOF
# The root link cannot be made, so every skill link dangles: an install that went on would prune them.
cat >"$bin/broken/ln" <<'EOF'
#!/usr/bin/env bash
case "${*: -1}" in
  */.agents/workflow) exit 1 ;;
esac
exec /usr/bin/ln "$@"
EOF
chmod +x "$bin/race/ln" "$bin/broken/ln"

if HOME="$race" PATH="$bin/race:$PATH" "$copy/install.sh" >/dev/null && [ -e "$race/raced" ] && [ "$(readlink "$race/.agents/skills/tdd")" = "$race/.agents/workflow/skills/tdd" ]; then ok "a link another run made first is accepted and kept"; else bad "a link another run made first is accepted and kept"; fi
if [ -z "$(ls -A "$copy/skills/tdd")" ]; then ok "no link is made inside the other run's link"; else bad "no link is made inside the other run's link"; fi

mkdir -p "$broken/.agents/skills"
ln -s "$broken/.agents/workflow/skills/tdd" "$broken/.agents/skills/tdd"
if HOME="$broken" PATH="$bin/broken:$PATH" "$copy/install.sh" >/dev/null 2>&1; then bad "a link that cannot be made makes install exit non-zero"; else ok "a link that cannot be made makes install exit non-zero"; fi
if [ -L "$broken/.agents/skills/tdd" ]; then ok "a link that cannot be made leaves the skill links alone"; else bad "a link that cannot be made leaves the skill links alone"; fi

exit "$fail"
