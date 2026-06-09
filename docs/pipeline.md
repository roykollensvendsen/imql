# The full picture

IMML is built around one empirical claim: in a Bittensor incentive mechanism, the **structure**
(combinators, overlays, aggregation, weight-setting, guards, ground-truth) recurs and composes — but the
**scoring metric** is bespoke to every subnet and does not recur. So the design isolates the metric as a
typed *hole*, makes the boundary explicit, and then progressively fills, measures, and stress-tests it.

This page is the end-to-end map of what that produced. Each layer is real, gated, and reproducible.

## 1. The language — describe any mechanism

A QML-style declarative surface that compiles to a versioned JSON-Schema IR and **round-trips at 100%
fidelity over all 189 corpus subnets**. Every node is `name: [Type] { props }`, with lists where the IR
has arrays:

```text
Mechanism {
    id: pairwiseArena

    netuid: 42
    @guards { CommitReveal { enforcement: rejection } }

    Pipeline {
        score: Metric { kind: win_rate; family: classification_quality; direction: higher_is_better }
        groundTruth: LlmJudgment { trust_model: adversarial }
        aggregate: WeightedAverage { normalization: sum_to_one }
        smooth: Ema { alpha: 0.1 }
        publish: SetWeights { cadence: per_epoch }
    }
}
```

`lift` (IR→IMML) and `compile` (IMML→IR) are inverse over the structural signature — the gate.

## 2. The metric hole → a typed spec algebra

The metric is the one part that doesn't generalize (75 distinct corpus metrics, 0 recurring). Rather than
pretend, IMML expresses it as a **small typed algebra** — a metric is a term over
`(submission, groundTruth, task, peers)` built from ~21 generators (`measure`, `gate`, `penalty`, `rate`,
`share`, `score_rule`, `beats`, …). It is parsed, **type-checked**, and **evaluated** by
`tooling/metric_spec.py`.

Measured (machine-checked, `vocab/metric-tail-specs.yaml` + `metric-kind-specs.yaml`):

- **64/75 (85%)** of one-off tail metrics are expressible, at a mean of **0.7 generator-calls each** —
  the MDL upper bound. The surface tail is flat; the *structural* tail is nearly trivial.
- All **20 named metric kinds** (503 signals) have a canonical spec.

A metric resolves in three states: `family/specific` (library), `spec: "<term>"` (the algebra, wired into
the surface via the sanctioned `extensions` hatch — no schema change), or `extern` (the genuine residual).

## 3. Dataflow diagrams — see the computation

Every mechanism and every metric spec renders as a top-down **Mermaid dataflow graph** (inputs at the
top, weights on-chain at the bottom), live on each example page's **Dataflow** tab. This is the visual
substrate for the simulator.

## 4. The simulator — measure incentive-compatibility

`tooling/simulate.py` instantiates a mechanism's structure (guards, aggregation, burn, sybil economics)
and runs strategic miners — honest / lazy / sybil / plagiarist / colluder — for N rounds, scoring each by
the subnet's **actual metric spec** where expressible (**173/180** subnets), then reports: honest-dominant?
gameable-by? concentration (Gini)? sybil-resistant? — and, with `--equilibrium`, whether honest is the
*evolutionary attractor* or the population collapses to a dominant cheat.

The headline corpus finding (stylized model, directional): **the aggregation method is the dominant
incentive lever** — only the winner-take-all / tournament family is reliably honest-dominant (at the cost
of extreme concentration), while proportional-family methods are gameable unless guards and a real
registration barrier hold. It is a structural red-flag screen, not a verdict — see the honest boundaries
below.

**Chain-grounded + Monte-Carlo.** `tooling/chain.py` pulls *real* per-subnet economics from finney via
bittensor — registration (recycle) cost, burn, emission, on-chain stake-Gini, top-validator stake
fractions — cached for offline use, so the sybil barrier and stake distribution are no longer stylized.
`tooling/simulate_cadcad.py` runs the model as a **cadCAD** simulation across N Monte-Carlo trajectories
(a verdict reads "honest-dominant in X% of runs"). Six analyses, none needing a real validator:

- **Monte-Carlo + reg-cost sweep** — robustness of the verdict, and the registration barrier needed for
  sybil-resistance vs the subnet's *actual* on-chain barrier (apex flips at reg_cost ~2.0 but its real
  `sybil_cost_ratio` is 0.17 → sybil-vulnerable).
- **Best-response + Goodhart** (`simulate.py --attack`) — searches the attack space for the *optimal*
  deviation and lets it inflate the exact field the metric rewards; field-gaming is caught by verification
  guards. (apex: 5 sybils + ×4 field-boost = 4.2× honest; affine: honest wins.)
- **Temporal** (`--temporal`) — does the real EMA smoothing let a ramp-then-defect miner free-ride? (slow
  α=0.05 → 1.28× exploit; no smoothing → safe.)
- **Yuma validator-collusion** (`--yuma`) — applies the verified clipped-median consensus to the real
  stake distribution: on netuids 1/4/8 a *single* validator (55–88% of stake) exceeds κ=50% and can
  unilaterally skew the weight consensus.
- **Chain calibration** (`--calibrate`) — concentration at two layers vs real on-chain emission Gini: the
  scoring-only Gini is uncorrelated (r ≈ 0), but the **effective Gini** — which layers the real dTAO
  emission split (validator dividends by on-chain stake + the registered-uid tail) over the scoring layer —
  tracks reality (**r ≈ 0.75** over 148 subnets). A proportional rule that looks fair carries
  validator-stake-driven concentration, and the effective layer captures it.
- **Equilibrium dynamics** (`simulate.py --equilibrium`) — replicator dynamics with a mutation floor: is
  honest the attractor, or does the population converge to a dominant cheat? `--equilibrium --corpus` agrees
  with the one-shot verdict on **91% of 180** mechanisms; the disagreements are the frequency-dependent
  cases (a cheat that pays only when rare, or one that self-limits once common — e.g. plagiarists need
  honest work to copy). The better predictor of which mechanisms hold up under play.

## 5. Theory — why this framing is the right one

A focused, adversarially-verified literature pass (`reports/metric-language-research.md`) grounds the
design in primary sources: describing the tail is a **compressibility / MDL question, not an
impossibility one**. Kolmogorov complexity is uncomputable (so no minimality *proof* exists), but every
computable metric is describable (so strict impossibility is false); No-Free-Lunch explains the diversity;
and bounding the spec language to a *total* combinator set (à la Turner) sidesteps the halting problem by
construction — which the algebra already does.

## Tooling map

| tool | does | gate / command |
|---|---|---|
| `tooling/lift.py` / `compile.py` | IR ⇄ IMML | — |
| `tooling/coverage.py` | round-trip all 189 | **100% fidelity** (gate) |
| `tooling/validate.py` | schema-validate instances | **190/190** (gate) |
| `tooling/generate.py` | IR → validator scaffold | **53/53** (gate) |
| `tooling/fmt.py` | canonical formatter (`imml-fmt`) | `--check` (gate) |
| `tooling/metric_spec.py` | spec parse / type-check / evaluate / graph | `--report`, `--selftest`, `--graph` |
| `tooling/graph.py` | mechanism → Mermaid dataflow | `graph.py <instance>` |
| `tooling/simulate.py` | incentive sim + best-response/Goodhart + chain calibration + equilibrium | `--corpus`, `--attack`, `--calibrate`, `--equilibrium` |
| `tooling/chain.py` | real per-subnet economics from finney (cached) | `chain.py <netuid>`, `--warm` |
| `tooling/simulate_cadcad.py` | cadCAD Monte-Carlo, reg-sweep, temporal, Yuma collusion | `--sweep-reg`, `--temporal`, `--yuma` |

## Honest boundaries

- The **metric residual** (`extern`, ~10% of the tail) is genuinely opaque — by design and by evidence.
- The **simulator's economics are now chain-grounded** (real registration cost, burn, stake-Gini from
  finney) — that blocker is closed where the chain is reachable. **But the submission semantics are still
  stylized**: there is no per-subnet schema for *what a miner actually delivers*, so a miner remains an
  abstract quality/effort/cheat profile and `submission.<field>` is derived from one quality axis. The
  mechanism's *shape* and *economics* are faithful; the per-field submission *content* is not. Read a
  verdict as a strong, chain-grounded hypothesis — triage, not a proof of a runnable exploit.
- **Validated where it counts** (`tooling/validate_sim.py`, 148 chain-confirmed subnets): the sim's
  **sybil-resistance verdict agrees** with the real registration barrier. Concentration is reported at two
  layers — the **scoring-only Gini is uncorrelated** with real emission Gini (r ≈ 0), because real reward
  concentration is validator-stake-driven, not scoring-driven; the **effective Gini** folds in the real
  validator-stake dividend layer + the registered-uid tail and **tracks reality (r ≈ 0.75)**. Trust the
  effective Gini and the strategic / sybil / economic verdicts; the scoring-only Gini is the within-miner
  signal, not the headline. **Still unvalidated**: the honest-dominant / gameable verdicts — there is no
  clean on-chain "is this gamed" signal to correlate against.
- The **theory** conclusions are primary-sourced for the compressibility framing; the Bittensor /
  simulator-framework regions of the research remain partly unverified.
