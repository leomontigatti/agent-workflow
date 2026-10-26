#!/usr/bin/env bash
#
# Feeds hooks/block-push-default-branch.sh the JSON a harness sends, from a throwaway repo whose
# origin's default branch is main, and checks which pushes it blocks (exit 2) and which it lets by.

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
  jq -n --arg c "$command" --arg d "$cwd" '{tool_input: {command: $c}, cwd: $d}' |
    "$hook" >/dev/null 2>&1 || code=$?
  local got=allowed
  [ "$code" -eq 2 ] && got=blocked
  if [ "$got" = "$want" ]; then echo "ok   $want: $command"; else echo "FAIL want $want, got $got (exit $code): $command"; fail=1; fi
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
check allowed "git log --oneline main"
check allowed "echo 'git push origin main' > notes.md"

git -C "$tmp/work" switch -q main
check blocked "git push"
check blocked "git push origin"
check blocked "git push origin HEAD"
check allowed "git push origin v1.0.1"

exit "$fail"
