# IMML — language sources

- `imml.ebnf` — the grammar (v0.1, targets IR schema 1.2.0).
- The language guide, worked example, and IR mapping: [`../spec/04-imml-language.md`](../spec/04-imml-language.md).

IMML is a declarative composition language for Bittensor incentive mechanisms. It compiles to the IR
(`../schema/incentive-mechanism.schema.json`) and round-trips losslessly with every corpus instance. The
four combinators (pipeline, multiplex, gate/product, overlay prefix) are the only composition operators;
the per-subnet hole is the `Metric { … }` leaf — `kind`/`family`/`specific`, a `spec:` term in the typed
metric algebra (`../spec/06-metric-spec-language.md`), or the `extern` residual.

> The EBNF documents the intended surface; a few constructs (e.g. the `multiplex` track form) still differ
> from the live lark grammar in `../tooling/imml_core.py` — see the backlog in `../CLAUDE.md`.

Round-trip / build / analysis tooling lives in `../tooling/` (`lift.py`, `compile.py`, `coverage.py`,
`generate.py`, `metric_spec.py`, `graph.py`, `simulate.py`).
