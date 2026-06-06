# CLAUDE.md — incentive-schema/

Guidance for working in this subtree.

## What this is
A formal JSON Schema for Bittensor incentive mechanisms (`schema/incentive-mechanism.schema.json`,
Draft 2020-12) plus reverse-engineered YAML instances and a skill-based extraction pipeline. Read
`spec/00-overview.md` first.

## Hard rules
- **The schema is versioned and governed.** Do not add/remove/retype a field without a
  `schema/CHANGELOG.md` entry citing the schema-stress evidence that motivated it, and a matching
  bump to `schema/VERSION` and the `$id` in the schema file. Every instance's `schema_version` must
  match `schema/VERSION`.
- **Extraction is evidence-based.** Every non-trivial field in an `extracted` instance needs a
  `provenance.evidence` item (source_path + line_ref + verbatim quote). Never invent numeric
  constants. Unknowable facts go in `provenance.unresolved`, not guessed. See `spec/03-extraction-guide.md`.
- **`instances/corpus/` is populated only by the `extract-corpus` bulk run.** The sample gate (M5) has
  passed (`reports/extraction-accuracy.md`); the sample loop lives in `instances/sample/`.

## Commands
```bash
./.venv/bin/python tooling/validate.py <path|dir>          # gate; non-zero exit on any failure
./.venv/bin/python tooling/stress-report.py <dir> --out reports/schema-stress-v0.md
```

## Related skills (compose at conversation level; they do not call each other)
- `im-extract <repo-path>` — one subnet → one instance.
- `im-schema validate|new-instance|bump|stress-report` — schema ops + authoring.
- `extract-corpus` Workflow (`../.claude/workflows/extract-corpus.js`) — bulk fan-out. Enumerate the
  pending repos with `bash tooling/list-pending.sh --json` and pass them as the workflow `args` (the
  script can't read the filesystem). Each agent writes `instances/corpus/<repo>.yaml` + self-validates;
  the workflow returns a summary to persist under `reports/`.
