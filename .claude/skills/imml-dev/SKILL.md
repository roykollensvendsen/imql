---
name: imml-dev
description: >-
  Develop and extend the IMML language (this repo): the schema/IR, the lark grammar + lift/compile
  round-trip, the metric ontology, the generator, and the tooling. Use when adding a primitive or enum,
  a metric family, a grammar/emitter change, a new tooling script, or when bumping the schema/ontology
  versions. Encodes the hard invariants and the gates that every change must pass.
---

# imml-dev — developing the IMML language

IMML is a declarative language for Bittensor incentive mechanisms. This repo holds the schema (the IR),
the grammar + round-trip tooling, a metric ontology, a generator, a 189-subnet corpus, and a docs site.
Read `spec/04-imml-language.md` and `spec/05-imml-style.md` first.

## Environment
```bash
python3 -m venv .venv && ./.venv/bin/pip install -r tooling/requirements.txt -r requirements-docs.txt
```
Run all tooling with `./.venv/bin/python`. A git **pre-commit hook** (`tooling/pre-commit.sh`, install:
`ln -sf ../../tooling/pre-commit.sh .git/hooks/pre-commit`) blocks any commit that touches
`instances|schema|templates` unless `validate.py` passes.

## The gates — every change must keep these green
```bash
./.venv/bin/python tooling/validate.py instances/ templates/blank-instance.yaml   # 190/190 valid
./.venv/bin/python tooling/coverage.py instances/                                  # PASS: 100% fidelity, >=90% structural
./.venv/bin/python tooling/generate.py --check instances/                          # 53/53 pipeline scaffolds
./.venv/bin/python tooling/fmt.py --check <lifted .imml>                            # canonical
./.venv/bin/mkdocs build --strict                                                  # docs clean
```

## Hard invariants (do not break)
- **Round-trip fidelity = 100%.** `coverage.py` lifts every IR to IMML, compiles back, and compares the
  **structural signature** (`imml_core.signature` — enums, params, typed nodes, composition; it
  deliberately EXCLUDES prose/provenance: subnet.name, *.summary, *.notes, provenance.*). A change that
  drops a structural field fails here.
- **Governed versioning.** No schema field or enum value or ontology entry without: ≥2× recurrence
  evidence, a CHANGELOG entry (`schema/CHANGELOG.md` / `vocab/CHANGELOG.md`), a VERSION bump
  (`schema/VERSION` / `vocab/VERSION` + the schema `$id`), and re-validating/re-stamping all instances.
- **The metric tail is flat — do NOT bloat enums.** The corpus census showed ~75/75 distinct
  `metric_kind_other` (almost nothing recurs ≥2×). Promoting one-off metrics to enums over-fits. Use the
  `other` + `*_other` escape hatch; canonicalize downstream (the ontology), never force-fit.
- **Extraction stays faithful (ELT).** `im-extract` records the raw metric string; canonicalization is a
  separate downstream layer (`vocab/metric-ontology.yaml` + `canonicalize.py`) that resolves families at
  read time and never mutates the raw level. Reversible by construction.
- **The IR IS the schema** (schema ⊂ IR, additive). One file, one VERSION, one validator.

## Architecture / file map
- `schema/incentive-mechanism.schema.json` — the IR (JSON Schema 2020-12). Enum + `*_other` escape hatch
  on every closed vocab; `extensions` for novelty; thin required core.
- `tooling/imml_core.py` — the heart: `signature()`, `lift()` (IR→IMML), `compile_text()` (IMML→IR, lark
  grammar `GRAMMAR`), `resolve_metric()` (ontology lookup). **lift and compile must stay inverse over the
  signature.** Property blocks are generic `{ k: v }` written one property per line (the parser also
  accepts `;`/`,` separators); `pb(pairs, indent)` in `lift()` emits them, indent-aware.
- `tooling/{lift,compile,coverage,fmt,canonicalize,generate,derive-composition,validate,stress-report}.py`
  — CLIs (thin wrappers over imml_core + the schema).
- `vocab/metric-ontology.yaml` — 3-level metric vocab (raw→specific→family); single source for the IR's
  `metric_family` enum AND the IMML metric types.
- `lang/imml.ebnf` — the documented grammar. **KNOWN DIVERGENCE:** the EBNF describes a richer surface
  (`from groundtruth`, `metric family(specific)`) that the *live* lark grammar in `imml_core.py` does NOT
  implement (it uses separate `gt:` items and `metric <kind> fam X spec Y`). Reconcile before promising
  the EBNF form (see backlog).
- `templates/scaffold/metric_library.py` + `tooling/generate.py` — IR → runnable validator scaffold
  (pipeline archetype only; `extern` leaves → `NotImplementedError`).
- `instances/sample/` (18) + `instances/corpus/` (171) — the 189-subnet round-trip test set.
- `docs/` + `mkdocs.yml` — see the `imml-docs` skill.

## How to extend safely
- **Add an enum value (primitive):** only with ≥2× evidence. Edit the schema enum, CHANGELOG, bump
  VERSION + `$id`, re-stamp all instances' `schema_version`, re-run the gates. (Additive → instances stay
  valid; just the version string changes.)
- **Add a metric family/specific/alias:** edit `vocab/metric-ontology.yaml`, bump `vocab/VERSION` +
  CHANGELOG, keep families ⊆ the schema `metric_family` enum, re-run `canonicalize.py --report` and
  `coverage.py`.
- **Change the grammar/emitter:** edit `GRAMMAR` + the `_T` transformer + `lift()` together so
  round-trip stays 100%. Test with `coverage.py instances/` and re-format the docs examples
  (`fmt.py --check`). Keep `lift` output canonical (it must pass `fmt --check`).
- **Touch the schema:** then `derive-composition.py` may need re-running, and the docs auto-regenerate.

## Backlog (next work)
1. **Reconcile `lang/imml.ebnf` with the live parser** — either implement the richer surface
   (`from groundtruth`, `metric family(specific)`) in the lark grammar, or trim the EBNF to match.
2. **Comment-preserving formatter** — `fmt.py` currently parses→re-emits (drops `#` comments). A
   CST-based formatter would preserve them (like modern qmlformat).
3. **Generation beyond the pipeline archetype** — multiplex/gated/tournament currently emit a flat
   scaffold; wire real multiplex/gating.
4. **Mechanism simulator (the improvement arc)** — instantiate an IMML spec against strategic miner
   policies (honest/lazy/sybil/plagiarist/colluder) to *measure* incentive-compatibility. This is the
   biggest next phase; the language is the substrate that makes it possible.
5. **Full-subnet description** — extend the IR from incentive-mechanism-only to facets (chain_config,
   architecture, economics, health). Chain facets need `btcli`/`bittensor` (not installed) or a taostats
   key; repo-derived facets (architecture) are buildable from the corpus now.

## Related
- `imml-docs` skill — build/preview/deploy the documentation site.
- Re-running bulk extraction needs the `academia-archives` corpus (not vendored): set
  `ARCHIVES=/path/to/academia-archives/repos` for `tooling/list-pending.sh`.
