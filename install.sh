#!/usr/bin/env bash
#
# Installs this repo as the user-level agent workflow on one machine. On Capy every thread has a
# machine of its own, and the project's Setup script runs this there before the agent starts.
# Idempotent: a second run changes nothing. `--check` changes nothing and reports drift, exiting 1
# when there is any.
#
#   ./install.sh           link everything
#   ./install.sh --check   report what is missing, wrong or stale
#
# What goes where:
#
#   ~/.agents/workflow              -> this repo: the stable path skills and briefs name
#   ~/.agents/skills/<name>         -> ~/.agents/workflow/skills/<name>
#                                      the skills folder a session reads each skill from, by path
#
# A target that exists and is not this repo's link is a conflict: it is reported and left alone,
# never overwritten. Links into this repo whose source is gone are stale, and removed.

set -euo pipefail

repo="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
root_link="$HOME/.agents/workflow"
agents_skills="$HOME/.agents/skills"

check=false
case "${1:-}" in
  "") ;;
  --check) check=true ;;
  *) echo "usage: $0 [--check]" >&2; exit 64 ;;
esac

drift=0
note() { printf '%s\n' "$*"; }
drifted() { drift=1; note "$*"; }

# ours <path>: whether a link target is one this script makes.
ours() {
  [[ "$1" == "$repo"/* || "$1" == "$root_link"/* ]]
}

# link <source> <target>: make <target> a symlink to <source>.
link() {
  local src="$1" dst="$2"
  if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
    return
  fi
  if [ -e "$dst" ] || [ -L "$dst" ]; then
    if [ -L "$dst" ] && ours "$(readlink "$dst")"; then
      if $check; then drifted "WRONG    $dst -> $(readlink "$dst") (want $src)"; return; fi
      ln -sfn "$src" "$dst"; note "relinked $dst"; return
    fi
    drifted "CONFLICT $dst exists and is not this repo's link; left alone"
    return
  fi
  if $check; then drifted "MISSING  $dst -> $src"; return; fi
  mkdir -p "$(dirname "$dst")"
  ln -s "$src" "$dst"
  note "linked   $dst"
}

# prune <dir>: remove links in <dir> that point into this repo at something that is gone.
prune() {
  local dir="$1" entry target
  [ -d "$dir" ] || return 0
  for entry in "$dir"/* "$dir"/.[!.]*; do
    [ -L "$entry" ] || continue
    target="$(readlink "$entry")"
    ours "$target" || continue
    [ -e "$entry" ] && continue
    if $check; then drifted "STALE    $entry -> $target"; continue; fi
    rm "$entry"; note "removed  $entry (stale)"
  done
}

link "$repo" "$root_link"

for dir in "$repo"/skills/*/; do
  name="$(basename "$dir")"
  link "$root_link/skills/$name" "$agents_skills/$name"
done
prune "$agents_skills"

if $check; then
  [ "$drift" -eq 0 ] && note "no drift"
  exit "$drift"
fi
[ "$drift" -eq 0 ] || { note "done, with conflicts above left alone"; exit 1; }
note "done"
