#!/usr/bin/env bash
#
# Installs this repo as the user-level agent workflow, for Claude Code and Codex. Idempotent: a
# second run changes nothing. `--check` changes nothing and reports drift, exiting 1 when there
# is any.
#
#   ./install.sh           link everything, wire the hooks
#   ./install.sh --check   report what is missing, wrong or stale
#
# What goes where:
#
#   ~/.local/share/agent-workflow   -> this repo: the stable path skills, briefs and wrappers
#                                      name, whichever harness reads them
#   ~/.claude/skills/<name>         -> skills/<name>    Claude Code's personal skills
#   ~/.agents/skills/<name>         -> skills/<name>    Codex's user skills (its docs name
#                                      $HOME/.agents/skills; ~/.codex/skills is the deprecated
#                                      location, set CODEX_SKILLS_DIR to use it)
#   ~/.claude/agents/<name>.md      -> agents/claude/   Claude Code's user subagents
#   ~/.codex/agents/<name>.toml     -> agents/codex/    Codex's personal agents
#   ~/.claude/settings.json hooks   the hooks/ scripts, merged into its "hooks" block
#   ~/.codex/hooks.json hooks       the same, in Codex's user hooks file
#
# A target that exists and is not this repo's link is a conflict: it is reported and left alone,
# never overwritten. Links into this repo whose source is gone are stale, and removed.

set -euo pipefail

repo="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
root_link="$HOME/.local/share/agent-workflow"
claude_skills="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
codex_skills="${CODEX_SKILLS_DIR:-$HOME/.agents/skills}"
claude_agents="$HOME/.claude/agents"
codex_agents="$HOME/.codex/agents"
claude_settings="$HOME/.claude/settings.json"
codex_hooks="$HOME/.codex/hooks.json"

check=false
case "${1:-}" in
  "") ;;
  --check) check=true ;;
  *) echo "usage: $0 [--check]" >&2; exit 64 ;;
esac

drift=0
note() { printf '%s\n' "$*"; }
drifted() { drift=1; note "$*"; }

command -v jq >/dev/null 2>&1 || { echo "install.sh needs jq" >&2; exit 1; }

# link <source> <target>: make <target> a symlink to <source>.
link() {
  local src="$1" dst="$2"
  if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
    return
  fi
  if [ -e "$dst" ] || [ -L "$dst" ]; then
    if [ -L "$dst" ] && [[ "$(readlink "$dst")" == "$repo"/* || "$(readlink "$dst")" == "$root_link"/* ]]; then
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
    [[ "$target" == "$repo"/* || "$target" == "$root_link"/* ]] || continue
    [ -e "$entry" ] && continue
    if $check; then drifted "STALE    $entry -> $target"; continue; fi
    rm "$entry"; note "removed  $entry (stale)"
  done
}

# The hooks block both harnesses read, pointing at the scripts through the stable path.
hooks_json() {
  jq -n --arg dir "$root_link/hooks" '{
    SessionStart: [{hooks: [{type: "command", command: ($dir + "/check-tool-path.sh")}]}],
    PreToolUse: [{matcher: "Bash", hooks: [{type: "command", command: ($dir + "/block-pkill-f.sh")}]}]
  }'
}

# wire_hooks <file>: merge hooks_json into the file's "hooks" block. Entries whose commands live
# under this repo's hooks/ are replaced; every other entry is kept as it was.
wire_hooks() {
  local file="$1" want current merged existed=false
  want="$(hooks_json)"
  if [ -f "$file" ]; then
    existed=true
    current="$(cat "$file")"
    jq -e . >/dev/null 2>&1 <<<"$current" || { drifted "CONFLICT $file is not valid JSON; left alone"; return; }
  else
    current='{}'
  fi
  merged="$(jq --argjson want "$want" --arg dir "$root_link/hooks/" '
    def ours: (.hooks // []) | any(.command | startswith($dir));
    .hooks = ((.hooks // {})
      | with_entries(.value |= map(select(ours | not)))
      | reduce ($want | keys[]) as $event (.; .[$event] = ((.[$event] // []) + $want[$event]))
      | with_entries(select(.value | length > 0)))' <<<"$current")"
  if [ "$(jq -S . <<<"$current")" = "$(jq -S . <<<"$merged")" ]; then
    return
  fi
  if $check; then drifted "HOOKS    $file is missing or has stale entries for $root_link/hooks"; return; fi
  mkdir -p "$(dirname "$file")"
  if $existed; then cp "$file" "$file.bak"; fi
  printf '%s\n' "$merged" >"$file.tmp" && mv "$file.tmp" "$file"
  if $existed; then note "wired    hooks in $file (previous copy: $file.bak)"; else note "wired    hooks in $file"; fi
}

link "$repo" "$root_link"

for dir in "$repo"/skills/*/; do
  name="$(basename "$dir")"
  link "$root_link/skills/$name" "$claude_skills/$name"
  link "$root_link/skills/$name" "$codex_skills/$name"
done
prune "$claude_skills"
prune "$codex_skills"

for file in "$repo"/agents/claude/*.md; do
  link "$root_link/agents/claude/$(basename "$file")" "$claude_agents/$(basename "$file")"
done
for file in "$repo"/agents/codex/*.toml; do
  link "$root_link/agents/codex/$(basename "$file")" "$codex_agents/$(basename "$file")"
done
prune "$claude_agents"
prune "$codex_agents"

wire_hooks "$claude_settings"
wire_hooks "$codex_hooks"

if $check; then
  [ "$drift" -eq 0 ] && note "no drift"
  exit "$drift"
fi
[ "$drift" -eq 0 ] || { note "done, with conflicts above left alone"; exit 1; }
note "done"
