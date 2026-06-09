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
Phases complete and committed (see `docs/pipeline.md` — "The full picture" — for the consolidated map):
- **schema→IR v1.2.0** + the **IMML language**, fully QML-faithful (`Mechanism { id: … }`, PascalCase
  types, `groundTruth`/`publish`, list-valued `score`/`groundTruth`, `Metric { … }`); lift/compile
  round-trip at **100% over 189 subnets**. The metric ontology (95.8% structural); the generator (53/53).
- **Metric spec language (Layer 2)** — `tooling/metric_spec.py`: a typed combinator algebra for the metric
  hole with parser + sort type-checker + **evaluator**. 85% of the 75-metric tail expressible at 0.7
  generators each (`vocab/metric-tail-specs.yaml`); all 20 named kinds spec'd (`metric-kind-specs.yaml`).
  Wired into the surface as `Metric { spec: "…" }`, validated at compile, stored in the `extensions` hatch
  (no schema field yet — accumulating ≥2× evidence). Spec: `spec/06-metric-spec-language.md`.
- **Dataflow diagrams** — `tooling/graph.py` (mechanism) + `metric_spec.to_mermaid` (spec) → Mermaid, live
  on each example page's Dataflow tab.
- **Incentive simulator (MVP)** — `tooling/simulate.py`: strategic miners (honest/lazy/sybil/plagiarist/
  colluder) vs a mechanism's structure; reports honest-dominance / gameability / Gini / sybil-resistance.
  Drives 173/180 subnets by their real metric spec. Stylized (no per-subnet submission schema) — triage,
  not proof. NOT published to the docs site (per-subnet "gameable" verdicts are reputationally sensitive).
- **Research** — `reports/metric-language-research.md`: adversarially-verified, primary-sourced — the tail
  is a compressibility/MDL question, not impossibility.
- **Process** — Conventional Commits enforced (commit-msg hook + CI); one commit per task.

QML-faithful coding conventions + `imml-fmt`; docs live at https://roykollensvendsen.github.io/imml/. This
repo is the source of truth; referenced as the `incentive-schema` submodule in `~/mining/sn109`.

## Backlog / next work
1. Reconcile the rest of `lang/imml.ebnf` with the live grammar (root/metric/gt/publish/smoother now match;
   the `multiplex` track/combine surface still differs).
2. Comment-preserving formatter (`fmt.py` currently drops `#` comments).
3. Generation beyond the pipeline archetype (multiplex/gated/tournament) — and wire the spec evaluator into
   generated validator code (`spec:` → a runnable `score_i()`).
4. **Simulator fidelity** — MVP + the cadCAD backend (`tooling/simulate_cadcad.py`, Monte-Carlo +
   reg-cost sweep) and the live chain adapter (`tooling/chain.py` → real recycle/burn/stake-Gini from
   finney, cached in `vocab/chain-params.json`) are done; the economics blocker is closed where the chain
   is reachable. **Remaining blocker: per-subnet submission semantics** — `submission.<field>` is still
   derived from one stylized quality axis (no data source for what each subnet's miners actually deliver).
   Also: promote `spec:` from `extensions` to a governed schema field once ≥2× corpus instances use it
   (`vocab/metric-*-specs.yaml` is the evidence base).
5. Full-subnet description — extend the IR to facets (chain_config/architecture/economics/health);
   chain facets need `btcli`/`bittensor` (not installed).

Re-running bulk extraction needs the `academia-archives` corpus (not vendored): set
`ARCHIVES=/path/to/academia-archives/repos` for `tooling/list-pending.sh`. The `extract-corpus` workflow
script lives in the `~/mining/sn109` workspace, not in this repo.
