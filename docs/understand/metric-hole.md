# The metric hole

Every other part of a mechanism — how you aggregate, smooth, publish, guard — comes from a small reusable
vocabulary. The [metric](../reference/glossary.md) is the exception: the exact function that scores one
submission is bespoke to every subnet. Across the corpus there are **75 distinct metrics, and zero recur**.

The honest response to that isn't to invent a fake taxonomy. It's to make the metric an explicit, typed
**hole** — and then see how much of it can be described after all.

## A typed spec algebra

Rather than treat the metric as free text, IMML expresses it as a **small typed algebra**: a metric is a
*term* over the four inputs `(submission, groundTruth, task, peers)`, built from ~21 generators —
`measure`, `gate`, `penalty`, `rate`, `share`, `score_rule`, `beats`, and so on. The term is parsed,
**type-checked**, and **evaluated** by `tooling/metric_spec.py`. (The full vocabulary is the
[metric spec language](../language/metric-spec.md).)

This turns "the metric is bespoke" from a shrug into a measurement.

## What the measurement found

Machine-checked against the corpus (`vocab/metric-tail-specs.yaml` + `metric-kind-specs.yaml`):

- **64/75 (85%)** of the one-off tail metrics are expressible in the algebra — at a mean of **0.7
  generator-calls each**. The *surface* tail is flat (75 distinct names), but the *structural* tail is nearly
  trivial: the diversity lived in field names and prose, not in computation.
- All **20 named metric kinds** (503 signals across the corpus) have a canonical spec.

A metric resolves to one of three states:

| state | meaning |
| --- | --- |
| `family/specific` | a known shape from the library |
| `spec: "<term>"` | expressible in the algebra (wired in via the sanctioned `extensions` hatch — no schema change) |
| [`extern`](../reference/glossary.md) | the genuine residual — bespoke judgment, hand-written |

## Honest boundary

The `extern` residual — roughly **10% of the tail** — is genuinely opaque, by design and by evidence. It's
not a gap waiting to be filled; it's the irreducible part where a subnet's notion of "good" is a real,
specific judgment. IMML's job is to make that boundary *explicit and small*, not to pretend it away. Why
that residual is irreducible rather than a failure of effort is the subject of [the theory](theory.md).
