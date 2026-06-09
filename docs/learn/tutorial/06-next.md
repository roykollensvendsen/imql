# Step 6 — Where to go next

You've gone end to end: designed a mechanism, written it in IMML, compiled it to a validated IR, generated a
validator, and used the simulator to catch and fix a real attack. That's the whole loop. Here's where to go
depending on what you want next.

## Go deeper on the ideas

- **[Why IMML exists](../why.md)** — the one insight (structure recurs, the metric doesn't) that the whole
  language rests on.
- **[The mental model](../mental-model.md)** — the anatomy diagram and the four combinator shapes, in one
  page.
- **[The full picture](../../understand/pipeline.md)** — the metric hole, the typed metric algebra, dataflow
  diagrams, and the simulator's chain-grounded modes, in depth.

## Do real work

- **[Author a mechanism](../../guides/author.md)** — the prescriptive checklist for designing your own,
  beyond the toy example.
- **[Read existing subnets](../../examples/index.md)** — all 189 real corpus mechanisms, each lifted to IMML
  with a dataflow diagram. Find one close to your problem and learn from it.
- **[Quick start](../../guides/quick-start.md)** — the commands from this tutorial, condensed, for when you
  just need the recipe.

## Reach for the reference

- **[All primitives](../../reference/index.md)** — every aggregator, smoother, guard, and ground-truth source,
  with how often each appears in the corpus.
- **[The metric spec language](../../language/metric-spec.md)** — for when your metric is more than
  `accuracy`: the typed algebra that expresses the bespoke part.
- **[Glossary](../../reference/glossary.md)** — every term, one line each.

!!! tip "The fastest way to learn more"
    Open the [examples gallery](../../examples/index.md) and read a few real mechanisms in the subnets you
    care about. Now that you know the five decisions and the pipeline shape, you can read any of them at a
    glance — which is the entire point.

---

← back to **[the tutorial start](index.md)**  ·  or jump to **[the examples gallery](../../examples/index.md)**
