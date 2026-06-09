# Step 1 — Design the mechanism

Before writing a line of IMML, you make five decisions. They're the same five for *every* mechanism, and
together they fully describe one. Let's answer them for Price Oracle.

!!! note "The five questions"
    1. What do miners **submit**?
    2. How do we **score** one submission?
    3. What's the **ground truth** we score against?
    4. How do per-miner scores become **weights** (who gets paid)?
    5. How might someone **cheat**, and what **guards** stop them?

### 1. What do miners submit?

A price forecast — a number. In IMML the *shape* of the submission is captured as a
[submission format](../../reference/glossary.md); for us it's a plain signal value. → `submission: signals`

### 2. How do we score one submission?

By **accuracy**: how close the forecast was to the real price. Higher is better, and we won't normalize the
raw score. This is the [metric](../../reference/glossary.md) — the one bespoke part of the mechanism.
→ a `Metric` with `kind: accuracy`, `direction: higher_is_better`.

### 3. What's the ground truth?

The real price, once it's known. That's a deterministic, trusted dataset — no human judgment, no model in
the loop. → `groundTruth: DeterministicDataset { trust_model: trusted }`

### 4. How do scores become weights?

We pay miners **in proportion** to their accuracy: twice as accurate, twice the reward. That's
*proportional* [aggregation](../../reference/glossary.md). We'll also **smooth** weights across rounds with
an exponential moving average so a single lucky round doesn't dominate, and **publish** once per epoch.
→ `aggregate: Proportional`, `smooth: Ema`, `publish: SetWeights`.

### 5. How might someone cheat?

Plenty of ways — but let's start with the obvious guard and **deliberately leave the rest open**, so the
simulator can show us what we missed later. We'll add a deterministic check (reject malformed submissions)
and nothing else for now. → `@guards { DeterministicCheck }`

!!! warning "We're leaving a hole on purpose"
    A proportional payout with no anti-copying guard is *begging* to be gamed. We're going to feel that pain
    in [Step 5](05-simulate.md) and fix it — because seeing the simulator catch it is more instructive than
    being told.

## What just happened

You made the five decisions that define a mechanism. Notice that four of them (submit, ground truth,
aggregate, guards) came from **reusable vocabulary** — and only one, the metric, is specific to Price
Oracle. That split is the whole idea behind IMML (see [Why IMML](../why.md)).

---

**[Step 2: Write it in IMML →](02-write.md)**
