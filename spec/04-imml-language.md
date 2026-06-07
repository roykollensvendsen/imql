# IMML — the incentive-mechanism language

IMML is a **declarative composition language** for Bittensor incentive mechanisms: a textual surface you
write by hand to *design* a mechanism, that compiles to the IR (the JSON-Schema YAML instance) and can
**fully describe every existing subnet** and (Phase B) **generate a runnable validator scaffold**.

It is to the IR what QML is to its scene graph — you compose typed nodes by nesting, decorate them with
orthogonal overlays, and leave the one per-subnet thing (the leaf metric) as a typed hole. There is no
control flow; the four empirical combinators are the only composition operators. Grammar: `lang/imml.ebnf`.

## The model in one breath
```
mechanism = overlays( combinator )
combinator ∈ { pipeline, multiplex, gate/product, leaf }
pipeline   = emit ∘ smooth ∘ aggregate ∘ score
overlays   = @burn ∘ @guards ∘ @state          (three orthogonal decorators)
score      = metric family(specific) from groundtruth     -- or `extern "raw"` (the long tail)
```

## Why these shapes
Derived inductively from all 189 corpus subnets:
- **4 combinators** cover the corpus: pipeline (90.5% as inner shape), overlay/wrapper (96.8%), parallel
  multiplex / sub-competitions (55.6%), gated/multiplicative (27%).
- **~50 reusable primitives** (9 aggregators, 5 smoothers, 16 guards, 9 ground-truth sources, 7 state
  kinds, burn) — each IMML primitive name is a closed enum value in the IR schema, so the vocabulary is
  governed by the same ≥2× bar.
- **The bespoke axis is one leaf**: the metric. Everything else recurs and composes; the metric is the
  irreducible per-subnet judgment. IMML makes that boundary explicit via the `extern` hole.

## Worked example
```imml
Mechanism {
    id: pairwiseArena
    netuid: 42
    lang: python
    status: active
    submission: model_weights

    @burn {
        uid: 0
        fraction: dynamic
    }
    @guards {
        commit_reveal {
            enforcement: rejection
        }
        deterministic_check {
            enforcement: rejection
        }
    }
    @state { cumulative_score }

    pipeline {
        score: metric win_rate fam classification_quality spec pairwise_win_rate {
            direction: higher_is_better
            normalization: none
        }
        gt: llm_judgment {
            trust_model: adversarial
        }
        aggregate: aggregator weighted_average {
            normalization: sum_to_one
        }
        smooth: smoother ema(alpha: 0.1)
        emit: set_weights {
            cadence: per_epoch
            tempo: "360 blocks"
        }
    }
}
```

## The metric hole (3 levels)
A `metric` leaf has three resolution states, mirroring `vocab/metric-ontology.yaml`:

| form | meaning | structural? |
|---|---|---|
| `metric FAMILY(SPECIFIC)` | family + canonical specific both known | yes — generable |
| `metric FAMILY(extern "raw")` | family known, specific unresolved | yes at family level |
| `extern "raw"` | neither resolves — opaque judgment | **no — the counted long tail** |

`raw` is always the verbatim source string and is never lost. `coverage.py` counts `extern` leaves;
their total IS the measured long tail. An `extern` that recurs ≥2× is a promotion candidate for the
ontology, not a permanent hole.

## How IMML maps to the IR (round-trip)
`.imml` ⇄ YAML instance is lossless. The mapping:

| IMML | IR field |
|---|---|
| `Mechanism { id: NAME; netuid, task, submission }` | `subnet`, `task` |
| `status: …` | `mechanism_status` |
| `@burn{…}` | `aggregation.burn_allocation` + `mechanism_status` + `composition.overlays:[burn]` |
| `@guards{…}` | `anti_gaming[]` + `composition.overlays:[guards]` |
| `@state{…}` | `per_miner_state` + `composition.overlays:[state]` |
| top-level combinator | `composition.shape` (pipeline/multiplex/gated/multiplicative/overlay_only/opaque) |
| `pipeline{score,aggregate,smooth,emit}` | `scoring_signals[]` + `aggregation` + `weight_setting` |
| `multiplex<structure>{track…}` | `sub_competitions` (+ tracks) |
| `metric FAMILY(SPECIFIC)` | `scoring_signals[].{metric_family, metric_specific, metric_kind/_other}` |
| `extern "raw"` | `scoring_signals[].{extern:true, metric_kind:other, metric_kind_other:"raw"}` |
| `from groundtruth KIND {…}` | `ground_truth_sources[]` |
| `aggregator METHOD {…}` | `aggregation.{method,…}` |
| `smoother ema(alpha)` | `weight_setting.smoothing` |
| `set_weights/commit_reveal {…}` | `weight_setting.{on_chain_call,cadence,tempo_or_interval}` |

## Tooling (built across M2–M4)
- `tooling/lift.py` — IR → IMML (one corpus instance to a `.imml`).
- `tooling/compile.py` — IMML → IR (the parser; validates against the schema).
- `tooling/coverage.py` — round-trips all 189; reports fidelity, structural-expressibility, and the
  extern residual (the gate: 100% fidelity, ≥90% structural, ≥80% per archetype).
- `tooling/generate.py` (Phase B) — IR → runnable Python validator scaffold for the pipeline archetype.

## Authoring a new mechanism (the prescriptive path)
Write a `.imml` file, then `compile.py mything.imml > mything.yaml && validate.py mything.yaml`. A clean
compile + validate means the design is structurally complete; any `extern` leaf is the part you must
hand-write (the actual `score()`), surfaced explicitly rather than hidden.
