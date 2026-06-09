# Step 2 — Write it in IMML

Now we turn those five decisions into IMML. Create a file `price-oracle.imml`. We'll build it block by
block; the whole thing at the end is short.

## The skeleton

Every mechanism starts the same way — a `Mechanism` block with an id and a few facts about the subnet:

```text
Mechanism {
    id: priceOracle

    netuid: 42
    lang: python
    status: active
    submission: signals
    ...
}
```

- `id` is a camelCase handle for the mechanism.
- `netuid` is the subnet's on-chain id (42 is made up for the example).
- `lang` / `status` describe the implementation; `submission: signals` is **decision 1** — what miners send.

## The overlay

Next, the [overlays](../../reference/glossary.md) — cross-cutting rules. We add just one guard for now
(**decision 5**):

```text
    @guards {
        DeterministicCheck {
            enforcement: rejection
        }
    }
```

`DeterministicCheck` rejects submissions that fail a deterministic validity test; `enforcement: rejection`
means a failing submission is thrown out (scored nothing).

## The pipeline

Finally the [pipeline](../../reference/glossary.md) — the four stages, in order. This is decisions 2, 3,
and 4:

```text
    Pipeline {
        score: Metric {                       # decision 2 — the metric (the hole)
            kind: accuracy
            direction: higher_is_better
            normalization: none
        }
        groundTruth: DeterministicDataset {   # decision 3 — what we score against
            trust_model: trusted
        }
        aggregate: Proportional {             # decision 4 — pay in proportion to score
            normalization: sum_to_one
        }
        smooth: Ema {                         # blend across rounds
            alpha: 0.2
        }
        publish: SetWeights {                 # write weights to chain, once per epoch
            cadence: per_epoch
        }
    }
```

Read it top to bottom and it's exactly the [pipeline picture](../mental-model.md): `score → aggregate →
smooth → publish`. The `alpha: 0.2` on the EMA means each round's weight is 20% the new score and 80% the
running history.

## The whole file

Put together, `price-oracle.imml` is just this:

```text title="price-oracle.imml"
--8<-- "docs/_snippets/tutorial.imml"
```

!!! note "Why this reads cleanly"
    Notice there's no scoring *code* here — only the *shape* of the mechanism. The one place real judgment
    lives, the `accuracy` metric, is named but not implemented. IMML surfaces that gap instead of hiding it.
    You'll see it again, marked explicitly, when we generate the validator in [Step 4](04-generate.md).

## What just happened

You wrote a complete mechanism in ~30 lines of readable text. Every block maps back to a decision from
Step 1. Next we'll hand it to the compiler and watch it become the machine-readable [IR](../../reference/glossary.md).

---

**[Step 3: Compile and read the IR →](03-compile.md)**
