# IMML metric spec-language (Layer 2) — design sketch

> **Status: proposal / RFC.** Not implemented in the parser. This sketches a small typed algebra for
> the `Metric` "typed hole" so the bespoke long tail can be *described* compositionally instead of left
> opaque. It complements the taxonomy tags (Layer 1) and is grounded in the research in
> `reports/` and the prior art (proper scoring rules, Composing Contracts, Catala/CDM).

## The model

A metric is, at bottom, a function `inputs → ℝ`. But "function" is the typed hole itself — too flat to
describe. The descriptive structure is to treat a metric as a **typed term in a small many-sorted
algebra** (equivalently, a morphism in a typed category): a composition of a handful of primitive
generators over `(submission, groundTruth, task, peers)`. Generality comes from composition; finite
description comes from the small generator set; *compressibility* comes from the fact that
surface-distinct metrics share structure once decomposed.

## Sorts

| sort | meaning |
|---|---|
| `Item` | one miner's submission (or a field of it) |
| `Items` | the whole population of submissions (for relational/peer metrics) |
| `GT` | a ground-truth source |
| `Task` | the challenge / input |
| `Num` | a scalar in ℝ (the eventual per-miner score) |
| `Vec` | a vector (per-class, per-item, or per-peer) |
| `Dist` | a probability distribution |
| `Bool` | a 0/1 gate value |

## Generators (the closed primitive set)

| generator | signature | covers |
|---|---|---|
| `submission` / `groundTruth` / `task` / `peers` | `→ Item / GT / Task / Items` | selectors (`.field` projects) |
| `measure` | a bare `submission.field : Num` | raw quantities (counts, amounts, sizes, costs) |
| `error` | `(Item∣Vec, GT∣Vec) → Num` | reference-based distance/error |
| `score_rule` | `(G, Dist, GT) → Num` | proper scoring rules; `G` ∈ {`brier`,`log`,`spherical`,`crps`,`energy`} (convex generator) |
| `similarity` | `(a, b) → Num` | embedding/semantic similarity |
| `member` | `(x, set) → Bool` | whitelist / membership |
| `gate` | `Bool → Num` | 1/0 from a condition (validity gates) |
| `threshold` | `(Num, τ) → Bool` | ratio/value thresholds |
| `rate` | `(Items → Bool) → Num` | pass-rate = mean of a gate over items |
| `share` | `(Num, Items) → Num` | `x / Σ peers` (stake/emission share) |
| `winrate` / `rank` | `Items → Vec` | relational/peer outcomes |
| `softmax` / `zscore` | `Vec → Vec` | peer normalization |
| `mean` / `sum` / `max` / `min` / `count` | `(Vec∣Items) → Num` | reductions |
| `clip` / `affine` / `penalty` / `neg` / `sign` / `normalize` | `Num → Num` | transforms |
| `extern` | `STRING → Num` | the genuine opaque residual |

~18 generators. `+ - * /` compose terms (affine/penalty/product composition).

## Grammar (EBNF)

```ebnf
spec      = expr ;
expr      = literal | source | call | "(" , expr , ")" | expr , binop , expr ;
source    = ( "submission" | "groundTruth" | "task" | "peers" ) , { "." , NAME } ;
call      = generator , "(" , [ arg , { "," , arg } ] , ")" ;
arg       = expr | NAME , ":" , literal ;        (* positional, or a named parameter *)
binop     = "+" | "-" | "*" | "/" ;
generator = NAME ;                               (* a name from the generator table above *)
literal   = number | STRING | NAME ;             (* NAME = a named convex generator, e.g. brier *)
```

## Empirical MDL measurement

All **75** distinct raw tail strings from the 189-subnet corpus were written out in this algebra in
[`vocab/metric-tail-specs.yaml`](../vocab/metric-tail-specs.yaml) and **machine type-checked** by
`tooling/metric_spec.py --report`. These are best-effort *structural* assignments (validated to parse +
type-check, not source-verified for exact semantics). The measured result:

| measure | value |
|---|---|
| distinct tail metrics | **75** |
| expressible in the algebra (type-check) | **64 (85%)** |
| genuine `extern` residual (opaque / not-a-metric) | **11 (14%)** |
| mean generator-calls per metric | **0.7** — the MDL upper bound |
| distinct generators actually used | **13** of 18 |

Generator usage (frequency): `gate` 12, `penalty` 9, `error` 4, `rate` 3, `affine` 3, `share` 3,
`mean` 2, `threshold` 2, `sum` 2, `member` 2, `sign` 1, `count` 1, `score_rule` 1.

**85% of the tail is expressible, at a mean depth of <1 generator call per metric** — most are a bare
field projection (`submission.param_count`) or a single wrap (`penalty(submission.api_cost)`). This is
the empirical answer to the theory question: the *surface* tail is flat (75/75 distinct, 0 recur), but
the *structural* tail is nearly trivial — the diversity lived in field names and prose, not in
computation. Two generators (`gate`, `penalty`) cover ~⅓ of the whole tail.

Two structural by-products fall out, and they matter: several "metrics" aren't metrics at all —
**multipliers/bonuses** belong to the existing `Multiplicative` combinator, **EMA-smoothing** belongs to
the `smooth:` stage, and **validity gates** belong to `@guards`. The spec language sharpens *what is
actually a metric* versus what was mis-recorded as one.

Two structural by-products fall out, and they matter: several "metrics" aren't metrics at all —
**multipliers/bonuses** belong to the existing `Multiplicative` combinator, **EMA-smoothing** belongs to
the `smooth:` stage, and **validity gates** belong to `@guards`. The spec language sharpens *what is
actually a metric* versus what was mis-recorded as one.

## Worked examples (real corpus tail metrics)

```text
parameter_count                       ->  submission.param_count
spot_check_pass_rate                  ->  rate(submission.spot_checks)
normalized on-chain stake share       ->  share(submission.stake, peers)
model_whitelist_membership            ->  gate(member(submission.model, task.whitelist))
compression_ratio_threshold           ->  gate(threshold(submission.compression_ratio, τ: 0.5))
api_cost_penalty                       ->  penalty(submission.api_cost)
pairwise win_rate                      ->  mean(winrate(peers))
(probabilistic forecast, Brier)       ->  score_rule(brier, submission.probs, groundTruth.label)
binary overfitting indicator (EMA)    ->  sign(error(submission, task.random) - error(submission, task.own))
                                          # the EMA is the pipeline's `smooth: Ema` stage, not the metric
model_rarity_multiplier               ->  submission.rarity        # composes via the Multiplicative combinator
external challenge weight (opaque)    ->  extern("per-hotkey weight from external challenge")
```

## Binding to the existing `Metric`

A `Metric` resolves in one of three states — a direct generalization of today's model:

```text
Metric { family: F; specific: S; … }   # 1. library reference — resolves to a generator (generable now)
Metric { spec: rate(submission.spot_checks); … }   # 2. a typed term in this algebra (the new layer)
Metric { kind: other; raw: "…"; extern: true; … }  # 3. the genuine opaque residual
```

`coverage.py` would then report the live MDL figure: the share of signals expressed by a `spec:` term
versus those that remain `extern` — turning "how flat is the tail" from a guess into a tracked number,
exactly as round-trip fidelity is tracked today.

## Open questions

- The generator set is seeded, not proven minimal — the right size is whatever expresses the most tail
  per generator (an MDL trade-off to measure, not assert).
- `score_rule`'s convex generators (`brier`/`log`/`crps`/`energy`) tie directly to the proper-scoring-rule
  characterization; the reference-free families (peer prediction, surrogate scoring rules) need their own
  generator(s) (`peer_score`) — see the research report.
- Typing/interpretation: a `spec:` term wants a type-checker (sorts) and one or more evaluation backends
  (à la Composing Contracts: one description, swappable interpreters) before it is more than documentation.
