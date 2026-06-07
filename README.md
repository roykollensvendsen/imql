# IMML

**IMML** — a declarative language for **Bittensor subnet incentive mechanisms**: a formal,
machine-checkable schema (the IR) plus a QML-style textual surface for designing and generating
mechanisms, a metric-type ontology, a corpus of 189 instances reverse-engineered from real subnets, and
a documentation site.

Documentation: build locally with `mkdocs serve` (see [`requirements-docs.txt`](requirements-docs.txt)),
or read the language guide in [`spec/04-imml-language.md`](spec/04-imml-language.md). The corpus was
reverse-engineered from the `academia-archives` collection (not vendored here; the re-extraction tooling
expects it as a sibling checkout — see `tooling/list-pending.sh`).

The schema is used two ways:
- **Descriptively** — capture an existing subnet's mechanism as an auditable `extracted` instance.
- **Prescriptively** — design a new mechanism as an `authored` instance from a blank template.

## Layout

```
schema/      canonical JSON Schema (Draft 2020-12) + VERSION + CHANGELOG
spec/        human-readable field reference, authoring guide, extraction guide
templates/   blank-instance.yaml — start here to author a new mechanism
instances/   sample/  (the bootstrapping set)   corpus/ (bulk run, populated later)
tooling/     validate.py, stress-report.py, requirements.txt
reports/     schema-stress + extraction-accuracy reports
```

## Quick start

```bash
python3 -m venv .venv && ./.venv/bin/pip install -r tooling/requirements.txt

# validate one instance or a whole directory (CI-style gate; non-zero exit on failure)
./.venv/bin/python tooling/validate.py instances/sample/

# author a new mechanism
cp templates/blank-instance.yaml instances/sample/my-design.yaml
./.venv/bin/python tooling/validate.py instances/sample/my-design.yaml

# see where the schema doesn't fit the corpus (drives schema versioning)
./.venv/bin/python tooling/stress-report.py instances/sample/ --out reports/schema-stress-v0.md
```

## Pipeline (skills)

- `im-extract` — reverse-engineer ONE subnet repo into a provenance-tagged, self-validated instance.
- `im-schema` — validate/version the schema and author new instances from the template.
- `extract-corpus` Workflow — bulk fan-out over many archives (one agent per repo). The sample gate
  has passed (`reports/extraction-accuracy.md`), so it is cleared to run.

## Bulk extraction runbook (`extract-corpus`)

The Workflow lives at `../.claude/workflows/extract-corpus.js`. Workflow scripts can't read the
filesystem, so you enumerate the pending repos first and pass them as `args`:

```bash
# the archives not yet extracted (171 at last count), as a JSON array:
bash tooling/list-pending.sh --json            # full pending list
bash tooling/list-pending.sh --json | ...      # or a slice for a test run
```

Then invoke the workflow with that array as `args` (e.g. start with a 5-repo slice to smoke-test).
Each agent writes `instances/corpus/<repo>.yaml` and self-validates; the workflow returns a summary
(ok/failed, mechanism_status & language breakdowns, ranked corpus-wide schema-stress, failures list).
Persist that summary to `reports/`, then sweep:

```bash
./.venv/bin/python tooling/validate.py instances/corpus/
./.venv/bin/python tooling/stress-report.py instances/corpus/ --out reports/schema-stress-corpus.md
```

A second schema-stress pass over the full corpus may surface new recurring signals → a governed
`im-schema bump` to a 1.x schema (re-validate all instances after any bump).

See `spec/00-overview.md` to get oriented.
