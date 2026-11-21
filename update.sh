#!/usr/bin/env bash
#
# Brings this clone to the newest release and installs it: a project's Setup runs it on every
# boot, so a machine restored from an old snapshot still starts on the current workflow.
#
#   ./update.sh
#
# The newest release is the highest `vX.Y.Z` tag, so a commit on `main` reaches a project only
# once a tag is on it. An origin that cannot be reached is reported and the newest tag already
# here is used: a boot does not fail on it. A checkout with uncommitted changes is someone's
# work, and is refused and left alone.

set -euo pipefail

# The whole script is read before any of it runs: the checkout below may replace this file.
main() {
  cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
  if ! git diff --quiet HEAD; then
    echo "update.sh: $(pwd) has uncommitted changes; left alone" >&2
    exit 1
  fi
  git fetch -q --tags origin || echo "update.sh: could not reach origin; using the newest tag already here" >&2
  local tag
  tag="$(git tag --list --sort=-v:refname | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | head -n 1 || true)"
  if [ -z "$tag" ]; then
    echo "update.sh: no release tag in $(pwd)" >&2
    exit 1
  fi
  git checkout -q --detach "$tag"
  echo "workflow at $tag"
  exec ./install.sh
}

main "$@"
