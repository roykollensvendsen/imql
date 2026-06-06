#!/usr/bin/env bash
# Print the archives that still need extraction (all repos minus those already
# present in instances/sample/ or instances/corpus/), one "Owner__repo" per line.
#
#   bash tooling/list-pending.sh                 # plain list
#   bash tooling/list-pending.sh --json          # JSON array (paste into Workflow args)
#   bash tooling/list-pending.sh --json | head   # a test slice
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPOS="$ROOT/../academia-archives/repos"

all=$(ls "$REPOS")
done=$(ls "$ROOT/instances/sample" "$ROOT/instances/corpus" 2>/dev/null | grep '\.yaml$' | sed 's/\.yaml$//' | sort -u || true)
pending=$(comm -23 <(echo "$all" | sort) <(echo "$done"))

if [ "${1:-}" = "--json" ]; then
  echo "$pending" | python3 -c "import json,sys; print(json.dumps([l.strip() for l in sys.stdin if l.strip()]))"
else
  echo "$pending"
fi
