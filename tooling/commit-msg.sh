#!/usr/bin/env bash
# Git commit-msg hook: enforce Conventional Commits on the subject line.
#
# Install (from repo root):
#   ln -sf ../../tooling/commit-msg.sh .git/hooks/commit-msg
#   chmod +x tooling/commit-msg.sh tooling/lint-commit-msg.sh
#
# Bypass once if you must:  git commit --no-verify
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
exec "$REPO_ROOT/tooling/lint-commit-msg.sh" "$1"
