# Step 4 — Generate a validator scaffold

The IR isn't just documentation — it's enough to generate working validator code.

```bash
./.venv/bin/python tooling/generate.py price-oracle.yaml -o validator.py
```

Open `validator.py`:

```python title="validator.py"
--8<-- "docs/_snippets/tutorial-validator.py"
```

## What the generator wrote — and what it didn't

Read it top to bottom and you'll see the generator did the **plumbing** for you:

- `aggregate()` — the real proportional rule (`score / total`), straight from your `aggregate: Proportional`.
- `smooth()` — a working EMA at `alpha=0.2`, from your `smooth: Ema`.
- `run_epoch()` — the loop that scores every miner, applies guards, aggregates, smooths, and would call
  `set_weights` — wired to your `publish: SetWeights` and `per_epoch` cadence.

And it left exactly one thing for you:

```python
def score_0(response, ground_truth):
    """signal: metric  metric=accuracy  direction=higher_is_better"""
    raise NotImplementedError('hand-write the bespoke metric: accuracy')
```

!!! note "This is the metric hole, made concrete"
    Everything reusable was generated. The one bespoke judgment — *what exactly does "accuracy" mean for a
    price forecast?* — is a loud `NotImplementedError`, not a silent guess. That boundary is IMML's whole
    thesis ([Why IMML](../why.md)) showing up in your code: the scaffold gives you ~80% of a validator, and
    the part it can't know is impossible to miss.

The guard is also stubbed for you to enforce:

```python
def apply_guards(uid, response):
    # TODO: enforce the guards above; return False to reject
    return True
```

## What just happened

You went from ~30 lines of IMML to a runnable validator skeleton, with the bespoke metric clearly flagged.
You *could* fill in `score_0`, implement the guard, and ship it. But first — is this mechanism even a good
idea? Let's find out before writing any more code.

---

**[Step 5: Simulate and read the verdict →](05-simulate.md)**
