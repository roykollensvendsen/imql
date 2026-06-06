#!/usr/bin/env bash
# Git pre-commit gate for the incentive-schema corpus.
#
# Blocks the commit unless every YAML instance under incentive-schema/instances/
# validates against the schema AND its schema_version matches schema/VERSION.
# This enforces the project invariant: every commit leaves validate.py green.
#
# Install (from repo root):
#   ln -sf ../../incentive-schema/tooling/pre-commit.sh .git/hooks/pre-commit
#   chmod +x incentive-schema/tooling/pre-commit.sh
# (or just copy it to .git/hooks/pre-commit and chmod +x)
#
# Skip once if you must:  git commit --no-verify
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
SCHEMA_DIR="$REPO_ROOT/incentive-schema"
PY="$SCHEMA_DIR/.venv/bin/python"
VALIDATE="$SCHEMA_DIR/tooling/validate.py"

# Only gate when incentive-schema instances/schema/template are part of this commit.
if ! git diff --cached --name-only | grep -qE '^incentive-schema/(instances|schema|templates)/'; then
  exit 0
fi

if [ ! -x "$PY" ]; then
  echo "pre-commit: incentive-schema venv missing ($PY)." >&2
  echo "  cd incentive-schema && python3 -m venv .venv && ./.venv/bin/pip install -r tooling/requirements.txt" >&2
  echo "  (or 'git commit --no-verify' to skip this gate)" >&2
  exit 1
fi

echo "pre-commit: validating incentive-schema instances..."
if ! "$PY" "$VALIDATE" "$SCHEMA_DIR/instances/" "$SCHEMA_DIR/templates/blank-instance.yaml"; then
  echo "pre-commit: BLOCKED — instances fail schema validation (see above)." >&2
  echo "  Fix them, or 'git commit --no-verify' to bypass." >&2
  exit 1
fi
echo "pre-commit: OK"
