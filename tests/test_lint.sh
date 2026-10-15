#!/usr/bin/env bash
#
# Proves tests/lint_skills.py fails on each rule it enforces: for every case, a copy of the repo
# gets one bad line, and the lint must exit 1 naming it.

# The cases below write Markdown backticks literally, on purpose.
# shellcheck disable=SC2016

set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail=0

expect_failure() {
  local name="$1" file="$2" line="$3" want="$4" work
  work="$(mktemp -d)"
  cp -r "$repo/." "$work"
  rm -rf "$work/.git"
  printf '\n%s\n' "$line" >>"$work/$file"
  if out="$(python3 -I "$work/tests/lint_skills.py" 2>&1)"; then
    echo "FAIL $name: the lint passed"; fail=1
  elif ! grep -q -- "$want" <<<"$out"; then
    echo "FAIL $name: expected '$want' in:"; echo "$out"; fail=1
  else
    echo "ok   $name"
  fi
  rm -rf "$work"
}

expect_failure "command in inline code" skills/tdd/SKILL.md 'Run `pnpm test` first.' "project command in inline code: pnpm"
expect_failure "command in a code block" skills/tdd/SKILL.md $'```sh\nuv run just test mod\n```' "project command in a code block"
expect_failure "command in prose" skills/tdd/SKILL.md 'Then pnpm builds it.' "project command in prose: pnpm"
expect_failure "file outside contract" skills/tdd/SKILL.md 'Read `docs/agents/coding-standards.md`.' "outside contract.md: docs/agents/coding-standards.md"
expect_failure "root doc outside contract" skills/tdd/SKILL.md 'Read `CONTEXT.md`.' "outside contract.md: CONTEXT.md"
expect_failure "broken link" skills/tdd/SKILL.md 'See [this](missing.md).' "broken link: missing.md"
expect_failure "broken anchor" skills/tdd/SKILL.md 'See [this](tests.md#no-such-heading).' "broken anchor"
expect_failure "upstream mention" skills/tdd/SKILL.md 'Taken from mattpocock/skills.' "mentions an upstream"
expect_failure "former upstream" agents/reviewer.md 'Adapted from show-me.' "mentions an upstream: show-me"

if python3 -I "$repo/tests/lint_skills.py" >/dev/null; then echo "ok   the repo itself passes"; else echo "FAIL the repo itself"; fail=1; fi
exit "$fail"
