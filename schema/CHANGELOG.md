# Schema Changelog

All schema changes are evidence-backed: no field is added, removed, or re-typed without a
corresponding entry here citing the schema-stress observation (from `reports/schema-stress-*.md`)
that motivated it. Version is mirrored in `schema/VERSION` and in the `$id` of
`incentive-mechanism.schema.json`.

## 1.0.0 — first refinement (v1)

Driven by the schema-stress report (`reports/schema-stress-v0.md`) aggregated over the 18-subnet
sample. Every change below cites the recurring (≥2×) stress that motivated it. **All changes are
backward-compatible** (new fields are optional; enum changes are supersets), so every v0 sample
instance re-validates after only a `schema_version` bump to `1.0.0`.

Structural fixes (enum/`*_other` asymmetry — these were genuine bugs):
- **`scoring_signals[].normalization_other` and `aggregation.normalization_other` added.** Every other
  closed enum had an `*_other` sibling; `normalization` did not, so agents were forced to dump the real
  normalization into `notes`. Cited by tensorplex-labs__dojo, backend-developers-ltd__ComputeHorde,
  bitcast-network__bitcast, mode-network__synth-subnet, Barbariandev__MANTIS, macrocosm-os__prompting.
- **`anti_gaming[].enforcement_other` added.** `enforcement` had `other` but no free-text sibling.
  Cited by Bitsec-AI__subnet, backend-developers-ltd__ComputeHorde.
- **`weight_setting.tempo_or_interval` now accepts integer** (not only string). Cited by
  Barbariandev__MANTIS (had to stringify a numeric 360-block interval).
- **`ground_truth_sources[].notes` added** (the block lacked any free-text slot). Cited by
  sportstensor__sn41 (notes rejected, rerouted to extensions).

New fields:
- **`weight_setting.smoothing{kind,alpha,window,notes}` added — the single highest-impact change.** EMA
  smoothing of the final reward is the dominant Bittensor pattern, but the only numeric home was
  `aggregation.decay_rate`, which conflates rank-decay with EMA alpha. Cited by coinmetrics__precog
  (two decays: rank 0.8 + EMA 0.05), It-s-AI__llm-detection (alpha 0.2/0.3 + a secondary 0.2),
  Bitsec-AI__subnet (0.1), Datura-ai__compute-subnet (0.3), Barbariandev__MANTIS (0.15),
  macrocosm-os__pretraining (0.5), macrocosm-os__finetuning (0.90), v0idai__SN106 (0.3).
  `aggregation.decay_rate`'s description was narrowed to "within-aggregation decay" accordingly.
- **`mechanism_status` (top-level) + `mechanism_status_notes` added.** Captures the active-vs-documented
  divergence where the live validator burns emissions while the designed scoring is dormant. Cited by
  macrocosm-os__pretraining (full burn to owner UID), v0idai__SN106 (runValidator burns; scoring path
  never called), tensorplex-labs__dojo (BurnWeight 100%), macrocosm-os__prompting (0.9 burn floor),
  taoshidev__proprietary-trading-network, gradients-ai__G.O.D, Datura-ai__compute-subnet (0.91 burn),
  fx-integral__merit (0.75 burn), sportstensor__sn41 (general-pool burn).
- **`aggregation.composition{,_other}` added** (weighted_sum|multiplicative|gated|rank|tournament|
  hybrid|other). The schema assumed additive weighted signals; many subnets multiply penalties (a zero
  zeroes the miner) or gate. Cited by taoshidev__proprietary-trading-network, v0idai__SN106,
  Datura-ai__compute-subnet.
- **`aggregation.temperature` added.** Softmax temperature had no home. Cited by
  macrocosm-os__pretraining (0.01), It-s-AI__llm-detection (softmax·100).
- **`aggregation.burn_allocation.dynamic` added.** Burn fraction is frequently a computed residual
  (`1 - sum`), not a literal. Cited by taoshidev__proprietary-trading-network, gradients-ai__G.O.D,
  sportstensor__sn41, backend-developers-ltd__ComputeHorde, macrocosm-os__prompting.

Enum value additions (supersets — existing `other` usages stay valid; new extractions should prefer
the specific value):
- `scoring_signals[].metric_kind` += `risk_adjusted_ratio` (Sharpe/Sortino/Calmar/Omega — PTN),
  `probabilistic_forecast` (CRPS — synth, precog), `predictive_contribution` (salience — MANTIS),
  `reward` (RL/GRPO — G.O.D, prompting), `composite` (weighted-sum scores — finetuning, prompting,
  llm-detection), `volume` (sportstensor).
- `anti_gaming[].kind` += `code_inspection` (obfuscation detection — G.O.D, Bitsec), `data_augmentation`
  (adversarial perturbation — llm-detection, Bitsec), `risk_limit` (drawdown elimination — PTN),
  `liveness_check` (TOTP ping — merit, ComputeHorde), `honeypot` (trap tasks — dojo).
- `aggregation.method` += `convex_optimization` (sportstensor CVXPY), `undocumented` (docs-only honesty —
  bigideaafrica__polaris).
- `aggregation.normalization` += `l1` (very common final L1 normalize), and `scoring_signals[].normalization` += `ema`.
- `weight_setting.cadence` += `rate_limited` (async loop gated by chain rate limit — bitcast, dojo,
  SN106) and `undocumented` (polaris).
- `sub_competitions.structure` += `per_task_type` (runtime task-type switch — dojo) and `tiered`
  (subnet+position two-tier — SN106).

Deferred (single-occurrence, `extensions` suffices for now): GPU/resource-allocation multipliers that
scale compute not score (gradients-ai__G.O.D, Datura-ai__compute-subnet); per-competition emission-share
as a first-class field (macrocosm-os__finetuning).

## 0.1.0 — initial (v0)

First cut, derived directly from the corpus analysis of `academia-archives` (see the project plan).
Covers: identity, task/submission format, scoring signals, ground-truth sources, aggregation,
weight-setting cadence, anti-gaming controls, sub-competition structure, per-miner state,
documentation status, and per-instance provenance with field-level evidence.

Design choices baked in from the start:
- Enum + `*_other` escape hatch on every closed vocabulary (required via `if/then` when `other`).
- `extensions` object (`additionalProperties: true`) on each structural sub-object for true novelty.
- Thin required core (`schema_version`, `instance_kind`, `subnet`, `task`, `scoring_signals`,
  `documentation`) so docs-only repos and blank authored specs both validate.
- `provenance` (with `evidence[]`, `minItems: 1`) required only for `instance_kind == "extracted"`.

This is the **v0** that the sample loop (M3) stress-tests. Recurring stress will drive **1.0.0**.
