# Generate a validator scaffold

Turn a validated [IR](../reference/glossary.md) into runnable validator code.

```bash
./.venv/bin/python tooling/generate.py <instance>.yaml -o validator.py
```

## What you get

The generator writes the **reusable plumbing** for you, straight from the IR:

- `aggregate()` — the real aggregation rule (proportional, winner-take-all, …).
- `smooth()` — the smoother (e.g. EMA at your `alpha`).
- `run_epoch()` — the loop that scores every miner, applies guards, aggregates, smooths, and sets weights at
  the right cadence.

## What you must fill

Two things are deliberately left as marked stubs:

- **`score_i()`** — each bespoke metric raises `NotImplementedError('hand-write the bespoke metric: …')`. This
  is the [metric hole](../understand/metric-hole.md): the part IMML can't know for you. When a metric resolves
  to a known library primitive, the generator wires it in; otherwise it's yours to write.
- **`apply_guards()`** — a `# TODO` to enforce the guards the IR declared.

!!! note "See it end to end"
    [Step 4 of the tutorial](../learn/tutorial/04-generate.md) walks through a generated `validator.py`
    line by line.

!!! warning "It's a scaffold, not production"
    The header says so on purpose. Generation gives you ~80% of a validator with the bespoke parts clearly
    flagged — it does not replace review, testing, or filling the holes.
