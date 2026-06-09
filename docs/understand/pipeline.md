# The full picture

This section is for when you want to understand *why* IMML is built the way it is, beyond how to use it. If
you haven't yet, the [mental model](../learn/mental-model.md) is the gentler starting point; this page is the
map of everything that idea produced.

## The one claim everything rests on

> In a Bittensor incentive mechanism, the **structure** (combinators, overlays, aggregation, weight-setting,
> guards, ground-truth) recurs and composes — but the **scoring metric** is bespoke to every subnet and does
> not recur.

So IMML isolates the metric as a typed *hole*, makes the boundary explicit, and then progressively fills,
measures, and stress-tests it. Each layer below is real, gated, and reproducible.

## The layers

1. **[The language](../language/index.md)** — a declarative surface that compiles to a versioned JSON-Schema
   [IR](../reference/glossary.md) and **round-trips at 100% fidelity over all 189 corpus subnets**. `lift`
   (IR→IMML) and `compile` (IMML→IR) are inverse over the structural signature — the gate.

2. **[The metric hole → a typed spec algebra](metric-hole.md)** — the one part that doesn't generalize,
   expressed as a small typed algebra instead of free text: parsed, type-checked, and evaluated.

3. **Dataflow diagrams** — every mechanism and every metric renders as a top-down Mermaid graph (inputs at
   the top, on-chain weights at the bottom), live on each [example page](../examples/index.md)'s **Dataflow**
   tab. This is the visual substrate for the simulator.

4. **[The simulator](simulator.md)** — runs strategic miners against a mechanism's structure to measure
   whether honest work actually wins: honest-dominant? gameable? sybil-resistant? — grounded in real chain
   economics.

5. **[The theory](theory.md)** — why this framing (a compressibility / MDL question, not an impossibility
   one) is the right one, grounded in primary sources.

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

IMML is precise about what it does *not* settle. Each deeper page carries the caveats for its own layer:

- the **metric residual** (`extern`, ~10% of the tail) is genuinely opaque — see [the metric hole](metric-hole.md);
- the **simulator** is a chain-grounded screen, not a proof, and some verdicts are validated while others
  aren't — see [the simulator](simulator.md);
- the **theory** is primary-sourced for the compressibility framing, partly unverified elsewhere — see
  [the theory](theory.md).
