#!/usr/bin/env bash
#
# Runs update.sh in clones of a throwaway origin whose install.sh only records the version it was
# run from: the newest release tag is taken, an untagged commit is not, a dirty checkout is left
# alone, an origin that cannot be reached keeps the version already there, and two runs at once
# take turns.

set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
export HOME="$tmp/home" GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
mkdir -p "$HOME"
fail=0
ok() { echo "ok   $*"; }
bad() { echo "FAIL $*"; fail=1; }

git init -q -b main "$tmp/origin"
cd "$tmp/origin"
git config user.email t@t && git config user.name t
cp "$repo/update.sh" update.sh
release() {
  # The stub's $HOME is expanded when it runs, not here. With $HOME/slow present it also holds
  # a directory for a second, and records an install that started inside another's.
  # shellcheck disable=SC2016
  printf '#!/usr/bin/env bash\necho "%s" >"$HOME/installed"\n[ -e "$HOME/slow" ] || exit 0\nmkdir "$HOME/installing" 2>/dev/null || echo x >>"$HOME/overlap"\nsleep 1\nrmdir "$HOME/installing" 2>/dev/null || true\n' "$1" >install.sh
  chmod +x install.sh update.sh
  git add -A && git commit -q -m "$1"
}
release v1.0.0 && git tag v1.0.0
release v1.9.0 && git tag v1.9.0
release v1.10.0 && newest="$(git rev-parse HEAD)"
release v1.11.0-rc.1 && git tag v1.11.0-rc.1 && git tag v99
release untagged

clone() { git clone -q "$tmp/origin" "$tmp/$1" && git -C "$tmp/$1" checkout -q v1.0.0; }

clone a
# Tagged after the clone was made: only a fetch brings it in.
git -C "$tmp/origin" tag v1.10.0 "$newest"
"$tmp/a/update.sh" >/dev/null || bad "update exited non-zero"
if [ "$(git -C "$tmp/a" describe --tags --exact-match)" = v1.10.0 ]; then ok "the newest release is fetched and checked out, not a pre-release or the untagged head"; else bad "the newest release is fetched and checked out, not a pre-release or the untagged head"; fi
if [ "$(cat "$HOME/installed")" = v1.10.0 ]; then ok "install runs from the new version"; else bad "install runs from the new version"; fi

clone b
echo edit >>"$tmp/b/install.sh"
if "$tmp/b/update.sh" >/dev/null 2>&1; then bad "a dirty checkout makes update exit non-zero"; else ok "a dirty checkout makes update exit non-zero"; fi
if [ "$(git -C "$tmp/b" describe --tags --exact-match)" = v1.0.0 ] && grep -q edit "$tmp/b/install.sh"; then ok "a dirty checkout is left as it was"; else bad "a dirty checkout is left as it was"; fi

clone c
git -C "$tmp/c" remote set-url origin "$tmp/gone"
rm -f "$HOME/installed"
"$tmp/c/update.sh" >/dev/null 2>&1 || bad "an unreachable origin makes update exit non-zero"
if [ "$(git -C "$tmp/c" describe --tags --exact-match)" = v1.10.0 ] && [ "$(cat "$HOME/installed")" = v1.10.0 ]; then ok "an unreachable origin still installs the newest tag it has"; else bad "an unreachable origin still installs the newest tag it has"; fi

clone d
touch "$HOME/slow"
"$tmp/d/update.sh" >/dev/null 2>&1 &
first=$!
"$tmp/d/update.sh" >/dev/null 2>&1 &
second=$!
if wait "$first" && wait "$second"; then ok "two runs at once both exit zero"; else bad "two runs at once both exit zero"; fi
if [ ! -e "$HOME/overlap" ] && [ "$(git -C "$tmp/d" describe --tags --exact-match)" = v1.10.0 ]; then ok "two runs at once install one after the other"; else bad "two runs at once install one after the other"; fi

exit "$fail"
