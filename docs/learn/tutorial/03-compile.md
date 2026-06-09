# Step 3 — Compile and read the IR

IMML text is the form *you* read. The [IR](../../reference/glossary.md) (intermediate representation) is the
form *tools* read — schema-validated YAML. Compiling converts one to the other.

## Compile

```bash
./.venv/bin/python tooling/compile.py price-oracle.imml > price-oracle.yaml
```

Then check it's structurally complete:

```bash
./.venv/bin/python tooling/validate.py price-oracle.yaml
```

```text
OK       price-oracle.yaml

1/1 valid  (schema 1.2.0)
```

A clean validate means the **structure** of your mechanism is complete and well-formed.

## The two forms, side by side

It's the same mechanism in both tabs — the readable surface and the machine IR:

=== "IMML (what you wrote)"

    ```text
    --8<-- "docs/_snippets/tutorial.imml"
    ```

=== "IR (what tools read)"

    ```yaml
    --8<-- "docs/_snippets/tutorial.ir.yaml"
    ```

Notice the IR is flatter and more verbose — `Proportional` became `aggregation: { method: proportional }`,
`Ema` became `weight_setting: { smoothing: { kind: ema, alpha: 0.2 } }`, and so on. That's the point: IMML
is the ergonomic view, the IR is the canonical one.

!!! note "The round-trip guarantee"
    Compile and its inverse, **lift**, are exact opposites over a mechanism's structure. Lift the IR back and
    you recover the IMML:
    ```bash
    ./.venv/bin/python tooling/lift.py price-oracle.yaml
    ```
    IMML guarantees this [round-trips](../../reference/glossary.md) losslessly for all 189 corpus subnets —
    the invariant that keeps the two forms from ever drifting apart.

## A word about `extern`

Look at the IR's `composition` block: `extern_count: 0`. Our `accuracy` metric resolved to a known shape, so
nothing is left unmodeled. When a subnet's metric *can't* be expressed in the
[metric vocabulary](../../language/metric-spec.md), it compiles to an
[`extern`](../../reference/glossary.md) leaf — an explicit "this judgment is bespoke, hand-write it" marker,
and `extern_count` rises. IMML never hides that gap; it counts it.

## What just happened

You have a validated IR — proof your mechanism's structure is complete. Next, we turn it into actual code.

---

**[Step 4: Generate a validator scaffold →](04-generate.md)**
