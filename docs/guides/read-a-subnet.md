# Read an existing subnet

You want to understand how a real subnet scores its miners. There are two ways: browse the gallery, or lift
a subnet yourself.

## Browse the gallery

All **189 corpus subnets** are in the [examples gallery](../examples/index.md), each on its own page with
three tabs:

- **Dataflow** — the mechanism as a top-down diagram (inputs at the top, on-chain weights at the bottom).
- **IMML** — the readable surface form.
- **IR (YAML)** — the raw, schema-valid instance.

Use the gallery's search to filter by name, primitive, or metric.

## Lift one yourself

Any instance lifts to IMML on the command line:

```bash
./.venv/bin/python tooling/lift.py instances/corpus/<Owner>__<repo>.yaml
```

## What to look for

Once you know the [mental model](../learn/mental-model.md), you can read any mechanism at a glance. Scan for:

- **the `aggregate` method** — the dominant incentive lever (proportional? winner-take-all? rank-based?).
- **the `@guards`** — what cheating the design defends against, and how (reject / penalize / barrier).
- **the `score` metric** — is it a known `family/specific`, a `spec` term, or an
  [`extern`](../reference/glossary.md) hole? The hole is where the subnet's real judgment lives.

Any unfamiliar term is one line away in the [glossary](../reference/glossary.md).

!!! tip "Want to stress-test it?"
    Reading tells you the design; the [simulator](simulate.md) tells you whether it holds up against
    strategic miners.
