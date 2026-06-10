# IMML

**IMML is a language for writing down how a Bittensor subnet rewards its miners** — precisely enough to
read it at a glance, compile it to code, and simulate it against cheaters before you ship.

Every subnet hand-codes that reward rule in its own validator. IMML gives it a shared, readable form: you
compose a mechanism from reusable [primitives](reference/glossary.md), and the one part that's genuinely
bespoke to each subnet — the scoring [metric](reference/glossary.md) — is an explicit, marked hole. The
language was derived from **189 real subnets**, every one of which round-trips through it losslessly.

!!! tip "New here? Start with the story, then build one."
    **[Why IMML exists →](learn/why.md)** (3-minute read) · then **[the hands-on tutorial →](learn/tutorial/index.md)**
    takes you from zero to a simulated, attack-tested mechanism.

<div class="grid cards" markdown>

-   :material-rocket-launch: **[Start here](learn/why.md)**

    Why IMML exists, the mental model in one diagram, and a hand-held tutorial from zero to hero.

-   :material-book-open-variant: **[Guides](guides/author.md)**

    Author a mechanism, read a real subnet, or reverse-engineer one from source.

-   :material-code-braces: **[Language & reference](language/index.md)**

    The grammar, the ~50 reusable primitives, the four combinators, the metric type system, and a
    [glossary](reference/glossary.md).

-   :material-view-gallery: **[Examples](examples/index.md)**

    All 189 corpus subnets, each lifted to IMML with a dataflow diagram — browse by use case, or search by
    name, primitive, or metric.

</div>

## The loop

```
 Extract ─▶ Lift ─▶ IMML (.imml) ─▶ Compile ─▶ IR (YAML) ─▶ Generate ─▶ validator.py
 (faithful)         (declarative)              (= the schema)          (runnable scaffold)
```

## At a glance

| | |
|---|---|
| Corpus coverage | **189 / 189** subnets, all schema-valid |
| Round-trip fidelity | **100%** (structural signature) |
| Structurally expressible | **95.8%** — the rest are explicit `extern` holes |
| Reusable primitives | ~50 (9 aggregators, 5 smoothers, 16 guards, 9 ground-truth sources, …) |
| Combinators | 4 (pipeline · multiplex · gate/product · overlay) |

## A mechanism in IMML

```text
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
        CommitReveal {
            enforcement: rejection
        }
    }
    @state { cumulative_score }

    Pipeline {
        score: Metric {
            kind: win_rate
            family: classification_quality
            specific: pairwise_win_rate
            direction: higher_is_better
            normalization: none
        }
        groundTruth: LlmJudgment {
            trust_model: adversarial
        }
        aggregate: WeightedAverage {
            normalization: sum_to_one
        }
        smooth: Ema {
            alpha: 0.1
        }
        publish: SetWeights {
            cadence: per_epoch
            tempo: "360 blocks"
        }
    }
}
```

New to all this? The line-by-line walkthrough of a (simpler) version of the file above is
**[Step 2 of the tutorial](learn/tutorial/02-write.md)**.
