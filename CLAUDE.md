# CLAUDE.md — IMML

Guidance for working in this repository: **IMML**, a declarative language for Bittensor incentive
mechanisms (a versioned JSON Schema / IR, a textual surface + grammar, lift/compile/format/generate
tooling, a metric ontology, a 189-subnet corpus, and a Qt-style docs site).

**Start here:** the repo-scoped skills capture the workflows and invariants —
- **`imml-dev`** — extend the language (schema/grammar/ontology/generator/tooling); the hard invariants
  and the gates every change must pass.
- **`imml-docs`** — build / preview / deploy the documentation site.

Also read `spec/04-imml-language.md` (the language) and `spec/05-imml-style.md` (coding conventions).

## Hard invariants (do not break)
- **Round-trip fidelity = 100%.** `tooling/coverage.py` lifts every IR to IMML, compiles back, and
  compares the *structural signature* (`imml_core.signature`, which excludes prose/provenance). `lift`
  and `compile` must stay inverse over that signature.
- **Governed versioning.** No schema field / enum value / ontology entry without ≥2× evidence + a
  CHANGELOG entry + a VERSION (and `$id`) bump + re-stamping & re-validating all instances.
- **The metric tail is flat — don't bloat enums.** Use the `other` + `*_other` escape hatch; canonicalize
  downstream (`vocab/metric-ontology.yaml`). Extraction stays faithful (ELT); the ontology resolves
  families at read time and never mutates the raw level.
- **Extraction is evidence-based.** Every non-trivial field in an `extracted` instance needs a
  `provenance.evidence` item (source_path + line_ref + verbatim quote); unknowable → `unresolved`, never
  guessed.

## Gates (keep green)
```bash
./.venv/bin/python tooling/validate.py instances/ templates/blank-instance.yaml   # 190/190 valid
./.venv/bin/python tooling/coverage.py instances/                                  # PASS (100% fidelity, 95.8% structural)
./.venv/bin/python tooling/generate.py --check instances/                          # 53/53
./.venv/bin/mkdocs build --strict                                                  # docs clean (~205 pages)
```
A pre-commit hook (`tooling/pre-commit.sh`) enforces `validate.py` on any `instances|schema|templates`
change; a commit-msg hook (`tooling/commit-msg.sh`) enforces [Conventional Commits](https://www.conventionalcommits.org/)
(also checked in CI by `.github/workflows/commitlint.yml`). Install both:
`ln -sf ../../tooling/pre-commit.sh .git/hooks/pre-commit && ln -sf ../../tooling/commit-msg.sh .git/hooks/commit-msg`.

Commits follow `<type>[(scope)][!]: <description>` (e.g. `feat(lang): …`, `fix(tooling): …`, `docs: …`),
one commit per completed task.

## Current state (handoff)
Phases complete and committed: schema→IR v1.2.0; the IMML language (grammar + lift/compile round-trip at
100% over 189 subnets); the metric ontology (95.8% structural); the generator (53/53 pipeline scaffolds);
QML-faithful coding conventions + `imml-fmt`; the docs site (live at
https://roykollensvendsen.github.io/imml/). This repo was extracted from a workspace and is the source of
truth; it is referenced as the `incentive-schema` submodule in `~/mining/sn109` (a Bittensor mining
workspace that also holds the `academia-archives` corpus).

## Backlog / next work
1. Reconcile `lang/imml.ebnf` with the live lark grammar (the EBNF documents `from groundtruth` /
   `metric family(specific)`; the parser uses `gt:` items / `metric <kind> fam X spec Y`).
2. Comment-preserving formatter (`fmt.py` currently drops `#` comments).
3. Generation beyond the pipeline archetype (multiplex/gated/tournament).
4. **Mechanism simulator** — instantiate an IMML spec against strategic miner policies to *measure*
   incentive-compatibility (the big next phase; the language is the substrate).
5. Full-subnet description — extend the IR to facets (chain_config/architecture/economics/health);
   chain facets need `btcli`/`bittensor` (not installed).

Re-running bulk extraction needs the `academia-archives` corpus (not vendored): set
`ARCHIVES=/path/to/academia-archives/repos` for `tooling/list-pending.sh`. The `extract-corpus` workflow
script lives in the `~/mining/sn109` workspace, not in this repo.
