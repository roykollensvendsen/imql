# IMML

**IMML** is a declarative language for **Bittensor incentive-mechanism design, description, and
generation** — a QML-style surface where you compose a mechanism from typed primitives, and the one
per-subnet thing (the scoring metric) is an explicit hole.

It is derived inductively from a corpus of **189 real Bittensor subnets**: every one round-trips through
the language losslessly, and the language compiles to a runnable validator scaffold.

<div class="grid cards" markdown>

-   :material-book-open-variant: **[Guides](guides/overview.md)**

    What IMML is, how to author a mechanism, and how mechanisms were reverse-engineered from real subnets.

-   :material-code-braces: **[Language reference](language/index.md)**

    The grammar, the ~50 reusable primitives, the four combinators, and the metric type system.

-   :material-view-gallery: **[Examples](examples/index.md)**

    All 189 corpus subnets, each lifted to IMML — filter by archetype, language, or burn status.

-   :material-tools: **[Toolchain](toolchain/cli.md)**

    `lift` · `compile` · `validate` · `coverage` · `canonicalize` · `generate`.

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
        score: metric win_rate fam classification_quality spec pairwise_win_rate {
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
