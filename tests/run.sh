#!/usr/bin/env bash
#
# Every check of the repo's scripts, in one place: CI's `scripts` job and the project Setup's
# `Test` command both run this file, so a new tests/test_*.py or tests/test_*.sh is picked up by
# both with no list to edit. The lint and its own test (tests/test_lint.sh) are CI's `skills` job.

set -euo pipefail
shopt -s nullglob

cd "$(dirname "${BASH_SOURCE[0]}")/.."

echo "== shellcheck"
shellcheck install.sh update.sh tests/*.sh skills/*/scripts/*.sh

echo "== python syntax"
python3 -m py_compile skills/*/scripts/*.py lib/*.py tests/*.py evals/*/*.py

for t in tests/test_*.py; do
  echo "== $t"
  python3 -I "$t"
done

for t in tests/test_*.sh; do
  [ "$t" = tests/test_lint.sh ] && continue
  echo "== $t"
  "$t"
done
