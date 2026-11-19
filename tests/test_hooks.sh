#!/usr/bin/env bash
#
# Feeds each hook the JSON a harness sends and checks which commands it blocks (exit 2) and which
# it lets by: hooks/block-push-default-branch.sh from a throwaway repo whose origin's default
# branch is main, then hooks/block-pkill-f.sh.

set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
hook="$repo/hooks/block-push-default-branch.sh"
fail=0
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
git init -q --bare -b main "$tmp/origin.git"
git clone -q "$tmp/origin.git" "$tmp/work" 2>/dev/null
git -C "$tmp/work" -c user.email=t@t -c user.name=t commit -q --allow-empty -m base
git -C "$tmp/work" push -q origin main
git -C "$tmp/work" remote set-head origin main
git -C "$tmp/work" switch -q -c feat/x

# check <blocked|allowed> <command> [cwd]
check() {
  local want="$1" command="$2" cwd="${3:-$tmp/work}" code=0
  printf '%s' "$command" >"$tmp/command"
  jq -n --rawfile c "$tmp/command" --arg d "$cwd" '{tool_input: {command: $c}, cwd: $d}' |
    "$hook" >/dev/null 2>&1 || code=$?
  local got="crashed"
  [ "$code" -eq 0 ] && got=allowed
  [ "$code" -eq 2 ] && got=blocked
  local shown="${command:0:80}"
  shown="${shown//$'\n'/\\n}"
  if [ "$got" = "$want" ]; then echo "ok   $want: $shown"; else echo "FAIL want $want, got $got (exit $code): $shown"; fail=1; fi
}

check blocked "git push origin main"
check blocked "git push -u origin HEAD:main"
check blocked "git push origin +HEAD:refs/heads/main"
check blocked "git push --force origin main"
check blocked "git fetch -q && git push origin main"
check blocked "git -C $tmp/work push origin main" /
check blocked "git push --all origin"
check blocked "git push --mirror origin"
check allowed "git push -u origin feat/x"
check allowed "git push origin HEAD:feat/x"
check allowed "git push origin v1.0.1"
check allowed "git push"
check allowed "git push --delete origin feat/x"
check blocked "git push --delete origin feat/x main"
check blocked "git push origin :main"
check allowed "git log --oneline main"
check allowed "echo 'git push origin main' > notes.md"
check blocked $'# Publish\ngit push origin HEAD:main'
check blocked "if true; then git push origin HEAD:main; fi"
check allowed $'cat <<\'EOF\' > notes.md\ngit push origin main\nEOF'
check blocked $'cat <<EOF > notes.md\nx\nEOF\ngit push origin main'
check blocked "$(head -c 200000 /dev/zero | tr '\0' 'x'); git push origin main"
git -C "$tmp/work" branch -q --track feat/up origin/main
git -C "$tmp/work" switch -q feat/up
git -C "$tmp/work" config push.default upstream
check blocked "git push"
git -C "$tmp/work" config --unset push.default
git -C "$tmp/work" switch -q feat/x

git -C "$tmp/work" switch -q main
check blocked "git push"
check blocked "git push origin"
check blocked "git push origin HEAD"
check allowed "git push origin v1.0.1"
check allowed "git push --tags origin"

git -C "$tmp/work" switch -q feat/x
check blocked $'cat <<<EOF\ngit push origin HEAD:main'
check allowed $'cat <<\'123\' > notes.md\ngit push origin main\n123'
check blocked $'git push \\\n  origin HEAD:main'
check blocked "git push --repo origin HEAD:main"
check blocked "env -i PATH=/usr/bin git push origin HEAD:main"
check blocked "command -- git push origin HEAD:main"
git -C "$tmp/work" config push.default matching
check blocked "git push"
git -C "$tmp/work" config --unset push.default
git -C "$tmp/work" config remote.origin.push HEAD:main
check blocked "git push"
git -C "$tmp/work" config --unset remote.origin.push
check allowed "git push"
git -C "$tmp/work" config remote.origin.push 'refs/heads/*:refs/heads/*'
check blocked "git push"
git -C "$tmp/work" config --unset remote.origin.push
git -C "$tmp/work" remote add publish "$tmp/origin.git"
git -C "$tmp/work" config remote.pushDefault publish
git -C "$tmp/work" config remote.publish.push HEAD:main
check blocked "git push"
git -C "$tmp/work" config --unset remote.pushDefault
check allowed "git push"
check blocked $'cat <<\\EOF > notes.md\nx\nEOF\ngit push origin HEAD:main'
check allowed $'cat <<\'END OF FILE\' > notes.md\ngit push origin main\nEND OF FILE'

hook="$repo/hooks/block-pkill-f.sh"
check blocked "pkill -f node"
check blocked "pkill -fx node"
check blocked "pkill --full node"
check blocked "pkill -9 -f node"
check blocked "pkill -u t3 -f node"
check blocked "pkill --signal TERM -f node"
check blocked "pkill -u t3 --full node"
check blocked "sleep 1; pkill -u t3 -f node"
check blocked $'echo hi\npkill -u t3 -f node'
check allowed "pkill node"
check allowed "pkill -u t3 node"
check allowed "pgrep -f node"
check allowed "echo never run pkill -f in a hook"
check allowed "pkill node; grep -f x y"
check allowed "pkill -u t3 node && grep -f x y"
check allowed "pkill node | grep -f x"
check allowed $'pkill node\ngrep -f x y'

exit "$fail"
