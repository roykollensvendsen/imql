#!/usr/bin/env bash
# Git pre-commit gate for the IMML corpus.
#
# Blocks the commit unless every YAML instance under instances/ validates against the
# schema AND its schema_version matches schema/VERSION.
# This enforces the project invariant: every commit leaves validate.py green.
#
# Install (from repo root):
#   ln -sf ../../tooling/pre-commit.sh .git/hooks/pre-commit
#   chmod +x tooling/pre-commit.sh
# (or just copy it to .git/hooks/pre-commit and chmod +x)
#
# Skip once if you must:  git commit --no-verify
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
PY="$REPO_ROOT/.venv/bin/python"
VALIDATE="$REPO_ROOT/tooling/validate.py"

# Only gate when instances/schema/template are part of this commit.
if ! git diff --cached --name-only | grep -qE '^(instances|schema|templates)/'; then
  exit 0
fi

if [ ! -x "$PY" ]; then
  echo "pre-commit: venv missing ($PY)." >&2
  echo "  python3 -m venv .venv && ./.venv/bin/pip install -r tooling/requirements.txt" >&2
  echo "  (or 'git commit --no-verify' to skip this gate)" >&2
  exit 1
fi

echo "pre-commit: validating instances..."
if ! "$PY" "$VALIDATE" "$REPO_ROOT/instances/" "$REPO_ROOT/templates/blank-instance.yaml"; then
  echo "pre-commit: BLOCKED — instances fail schema validation (see above)." >&2
  echo "  Fix them, or 'git commit --no-verify' to bypass." >&2
  exit 1
fi
echo "pre-commit: OK"
