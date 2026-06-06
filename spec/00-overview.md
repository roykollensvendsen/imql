# Overview

This directory defines a **formal, machine-checkable schema** for Bittensor subnet incentive
mechanisms, and a corpus of instances built against it.

The schema serves two purposes:

- **Descriptive** — reverse-engineer an existing subnet (from the `academia-archives` corpus) into an
  `instance_kind: extracted` YAML instance, with a `provenance` block that ties every non-trivial claim
  to a file + line + quote in the source. These are auditable.
- **Prescriptive** — author a brand-new mechanism as an `instance_kind: authored` instance, starting
  from `templates/blank-instance.yaml`. The schema doubles as a design checklist.

## Canonical artifact

`schema/incentive-mechanism.schema.json` (JSON Schema Draft 2020-12) is the single source of truth.
Its version lives in the `$id` and is mirrored in `schema/VERSION`. Every instance carries a
`schema_version` that must match.

## How the schema stays both open and structured

1. **Enum + escape hatch.** Closed vocabularies are `enum [...known, "other"]`. Selecting `other`
   makes the sibling `*_other` free-text field required (enforced via `if/then`). Common cases stay
   machine-aggregatable; outliers are never blocked.
2. **Strict objects + sanctioned `extensions`.** Structural objects set `additionalProperties: false`
   (catches typos), but each carries an optional `extensions` object (`additionalProperties: true`)
   for genuine novelty.
3. **Thin required core.** Only `schema_version`, `instance_kind`, `subnet`, `task`,
   `scoring_signals`, and `documentation` are required. Everything describing mechanism internals is
   optional, so a docs-only repo and a blank authored spec both validate.

## Workflow

| Step | Tool |
|---|---|
| Author a new mechanism | copy `templates/blank-instance.yaml`, fill, validate |
| Reverse-engineer one subnet | the `im-extract` skill |
| Validate instance(s) | `tooling/validate.py <path|dir>` (or the `im-schema` skill) |
| Find where the schema doesn't fit | `tooling/stress-report.py <dir>` |
| Bulk-extract the whole corpus | the `extract-corpus` Workflow (after the sample gate) |

See `01-field-reference.md` for every field, `02-authoring-guide.md` for the prescriptive path, and
`03-extraction-guide.md` for the descriptive path and evidence discipline.
