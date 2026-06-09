# IMML — Incentive Mechanism Modeling Language

**IMML** is a declarative language and toolchain for **Bittensor subnet incentive mechanisms**. It lets
you *describe* a mechanism precisely, *generate* a runnable scaffold, *visualise* its dataflow, and
*simulate* it against strategic miners to measure whether the incentives actually hold.

The guiding result: a mechanism's **structure** (combinators, overlays, aggregation, weight-setting,
guards, ground-truth) recurs and composes, but the **scoring metric** is bespoke to every subnet. IMML
captures the structure as a typed language and isolates the metric as an explicit, measurable hole.

📖 **Docs (start here):** https://roykollensvendsen.github.io/imml/ — and
[**The full picture**](https://roykollensvendsen.github.io/imml/latest/pipeline/) for the end-to-end map.

## What's here

- **A versioned IR** — `schema/incentive-mechanism.schema.json` (JSON Schema 2020-12), the single source
  of truth. Used *descriptively* (reverse-engineer a subnet into a provenance-tagged instance) and
  *prescriptively* (author a new mechanism from a template).
- **A QML-style surface** — a readable textual language (`spec/04`, `spec/05`) that `lift`/`compile`
  round-trip against the IR at **100% structural fidelity over all 189 corpus subnets**.
- **A metric spec algebra (Layer 2)** — `tooling/metric_spec.py`: a small typed combinator language for the
  bespoke metric, with a parser, sort type-checker, and **evaluator**. 85% of the metric tail is
  expressible at <1 generator-call each (`spec/06`).
- **Dataflow diagrams** — every mechanism and metric renders as a Mermaid graph (inputs → … → weights),
  live on each example page's *Dataflow* tab.
- **An incentive simulator** — `tooling/simulate.py`: run honest/lazy/sybil/plagiarist/colluder miners
  against a mechanism and measure honest-dominance, gameability, concentration, sybil-resistance.
- **A 189-subnet corpus** + a **metric ontology** + a **Qt-style docs site**.

## Layout

```
schema/      canonical JSON Schema (Draft 2020-12) + VERSION + CHANGELOG
lang/        the grammar (imml.ebnf)
spec/        field reference, the language, coding conventions, the metric spec language
vocab/       metric ontology + the metric-tail / metric-kind spec mappings
templates/   blank-instance.yaml — start here to author a new mechanism
instances/   sample/ (bootstrap set) + corpus/ (189 reverse-engineered subnets)
tooling/     lift, compile, coverage, validate, generate, fmt, metric_spec, graph, simulate
reports/     schema-stress, extraction-accuracy, and the metric-language research report
docs/        the Material-for-MkDocs site (mostly generated from the artifacts above)
```

## Quick start

```bash
python3 -m venv .venv && ./.venv/bin/pip install -r tooling/requirements.txt -r requirements-docs.txt

# round-trip + validate the whole corpus (the core gates)
./.venv/bin/python tooling/coverage.py instances/           # 100% fidelity
./.venv/bin/python tooling/validate.py instances/ templates/blank-instance.yaml

# describe one subnet on the page (top-down dataflow), or simulate its incentives
./.venv/bin/python tooling/graph.py    instances/corpus/<subnet>.yaml
./.venv/bin/python tooling/simulate.py instances/corpus/<subnet>.yaml

# the metric spec algebra: type-check, evaluate, graph, or measure tail coverage
./.venv/bin/python tooling/metric_spec.py "rate(submission.spot_checks)"
./.venv/bin/python tooling/metric_spec.py --report vocab/metric-tail-specs.yaml

# author a new mechanism, then compile + validate
cp templates/blank-instance.yaml instances/sample/my-design.yaml
./.venv/bin/python tooling/validate.py instances/sample/my-design.yaml
```

## Gates (keep green)

```bash
./.venv/bin/python tooling/validate.py instances/ templates/blank-instance.yaml   # 190/190 valid
./.venv/bin/python tooling/coverage.py instances/                                  # 100% fidelity
./.venv/bin/python tooling/generate.py --check instances/                          # 53/53
./.venv/bin/mkdocs build --strict                                                  # docs clean
```

A pre-commit hook enforces `validate.py`; a commit-msg hook enforces
[Conventional Commits](https://www.conventionalcommits.org/) (also checked in CI). Install both:
`ln -sf ../../tooling/pre-commit.sh .git/hooks/pre-commit && ln -sf ../../tooling/commit-msg.sh .git/hooks/commit-msg`.

## Corpus extraction (descriptive path)

The corpus was reverse-engineered from the `academia-archives` collection (not vendored). Re-running bulk
extraction needs it as a sibling checkout (`ARCHIVES=/path/to/academia-archives/repos` for
`tooling/list-pending.sh`); the `extract-corpus` workflow lives in the `~/mining/sn109` workspace. See the
`im-extract` and `im-schema` skills, and `spec/00-overview.md`.
