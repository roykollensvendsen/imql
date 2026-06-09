#!/usr/bin/env bash
# Validate a commit message subject against Conventional Commits.
#
# Usage:
#   tooling/lint-commit-msg.sh <path-to-message-file>     # used by the commit-msg hook
#   git log -1 --format=%B <sha> | tooling/lint-commit-msg.sh -   # used by CI / ad-hoc
#
# Spec: https://www.conventionalcommits.org/en/v1.0.0/
#   <type>[(scope)][!]: <description>
# Both a malformed type/scope and an over-long subject (> 72 chars) fail (exit 1).
set -euo pipefail

TYPES='feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert'
MAXLEN=72

src="${1:-}"
if [ -z "$src" ]; then
  echo "lint-commit-msg: missing argument — pass a message file path, or '-' for stdin" >&2
  exit 2
fi
if [ "$src" = "-" ]; then
  subject="$(sed -n '1p')"
else
  subject="$(sed -n '1p' "$src")"
fi

# Skip git-generated commits that are not hand-authored.
case "$subject" in
  Merge\ *|Revert\ \"*|fixup!\ *|squash!\ *|amend!\ *) exit 0 ;;
esac

if ! printf '%s' "$subject" | grep -Eq "^(${TYPES})(\([a-z0-9._/-]+\))?(!)?: .+"; then
  cat >&2 <<EOF
✗ Commit message must follow Conventional Commits.
  got:      $subject
  format:   <type>[(scope)][!]: <description>
  types:    ${TYPES//|/, }
  examples: feat(lang): add multiplex combinator
            fix(tooling): handle empty propblock in lift
            docs(skill): document commit cadence
            refactor(lang)!: drop comma separator in property blocks
  (bypass once with: git commit --no-verify)
EOF
  exit 1
fi

if [ "${#subject}" -gt "$MAXLEN" ]; then
  cat >&2 <<EOF
✗ Commit subject is ${#subject} chars — keep it ≤ ${MAXLEN}.
  got:    $subject
  fix:    tighten the subject; move detail into the body (blank line, then prose).
  (bypass once with: git commit --no-verify)
EOF
  exit 1
fi

exit 0
