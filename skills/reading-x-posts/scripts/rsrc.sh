#!/usr/bin/env bash
#
# Runs the X reader CLI at the commit its source's `pin` in upstreams/sources.json names, so every
# machine runs the same code until a PR moves the pin. The first run on a machine fetches and caches
# that commit; later runs reuse the cache.
#
#   rsrc.sh x read URL_OR_ID [URL_OR_ID ...]
#   rsrc.sh x --help

set -euo pipefail

sources="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../../../upstreams/sources.json"

if ! command -v uvx >/dev/null; then
  echo "rsrc.sh: uvx is not on PATH, so the X reader cannot run on this machine" >&2
  exit 2
fi

spec="$(python3 -I - "$sources" <<'PY'
import json, sys
source = next(s for s in json.load(open(sys.argv[1], encoding="utf-8"))["sources"] if s.get("tool") == "rsrc")
print(f"git+https://github.com/{source['repo']}@{source['pin']}")
PY
)"

exec uvx -q --from "$spec" rsrc "$@"
