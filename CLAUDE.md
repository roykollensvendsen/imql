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
- **Incentive simulator (chain-grounded, validated)** — a suite, NOT published to the docs site
  (per-subnet "gameable" verdicts are reputationally sensitive). Optional deps in
  `tooling/requirements-sim.txt` (cadCAD + bittensor, now installed in `.venv`).
  - `tooling/simulate.py`: strategic miners vs a mechanism's structure → honest-dominance / gameability /
    Gini / sybil-resistance; drives 173/180 by their real spec. Modes: `--corpus`; `--attack`
    (best-response search + Goodhart field-gaming, guard-aware); `--calibrate` (predicted vs real Gini).
  - `tooling/chain.py`: REAL finney economics per netuid (recycle/burn/emission/kappa/stake-Gini/
    top-bloc stake fractions/sybil_cost_ratio), cached in `vocab/chain-params.json` (~103 subnets warmed).
  - `tooling/simulate_cadcad.py`: cadCAD Monte-Carlo; modes `--sweep-reg` (registration barrier threshold),
    `--temporal` (ramp-then-defect under EMA), `--yuma` (validator collusion on real stake + verified
    clipped-median consensus — finding: one validator with 55–88% stake exceeds κ on most subnets).
  - `tooling/validate_sim.py`: correlates verdicts vs real chain over 148 subnets. **CRITICAL FINDING:
    sybil-resistance verdicts AGREE with reality, but the concentration/Gini prediction does NOT (r≈0) —
    real reward concentration is validator-stake-driven, not scoring-driven. Trust the strategic/sybil/
    economic verdicts; do NOT trust the sim's Gini standalone (use `--calibrate`/`--yuma`).**
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
4. **Simulator** — chain economics, cadCAD, best-response/Goodhart, temporal, Yuma collusion, and
   validation are all done (see Current state). Next, in priority order: (a) **fix concentration** — wire
   the validator-stake layer (Yuma + real stake) into the main verdict so the Gini becomes credible (the
   validation showed scoring-only Gini is uncorrelated with reality); (b) **equilibrium dynamics** — iterate
   best-response to a fixed point (does the mechanism collapse to all-cheaters?) rather than one deviation;
   (c) the residual blocker is **per-subnet submission semantics** (`submission.<field>` is one stylized
   quality axis; needs a real validator — not closeable from the corpus). Also: promote `spec:` from
   `extensions` to a governed schema field once ≥2× corpus instances use it.
5. Full-subnet description — extend the IR to facets (chain_config/architecture/economics/health).
   `bittensor` is now installed and finney is reachable (`tooling/chain.py` is the adapter), so chain
   facets are now buildable.

Re-running bulk extraction needs the `academia-archives` corpus (not vendored): set
`ARCHIVES=/path/to/academia-archives/repos` for `tooling/list-pending.sh`. The `extract-corpus` workflow
script lives in the `~/mining/sn109` workspace, not in this repo.
