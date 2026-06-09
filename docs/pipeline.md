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
gameable-by? Gini concentration? sybil-resistant?

The headline corpus finding (stylized model, directional): **the aggregation method is the dominant
incentive lever** — only the winner-take-all / tournament family is reliably honest-dominant (at the cost
of extreme concentration), while proportional-family methods are gameable unless guards and a real
registration barrier hold. It is a structural red-flag screen, not a verdict — see the honest boundaries
below.

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
| `tooling/simulate.py` | incentive simulation | `simulate.py <instance>`, `--corpus` |

## Honest boundaries

- The **metric residual** (`extern`, ~10% of the tail) is genuinely opaque — by design and by evidence.
- The **simulator is stylized**: no per-subnet submission schema, so a miner is an abstract
  quality/effort/cheat profile and the registration cost is a fixed constant. The mechanism's *shape*
  (which cheats its guards catch, how scores become weights, sybil economics) is faithful; the magnitudes
  are not. Read it as triage, not proof.
- The **theory** conclusions are primary-sourced for the compressibility framing; the Bittensor /
  simulator-framework regions of the research remain partly unverified.
