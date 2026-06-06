# IMQL — language sources

- `imql.ebnf` — the grammar (v0.1, targets IR schema 1.2.0).
- The language guide, worked example, and IR mapping: [`../spec/04-imql-language.md`](../spec/04-imql-language.md).

IMQL is a declarative composition language for Bittensor incentive mechanisms. It compiles to the IR
(`../schema/incentive-mechanism.schema.json`) and round-trips losslessly with every corpus instance. The
four combinators (pipeline, multiplex, gate/product, overlay prefix) are the only composition operators;
the leaf `metric` is the single per-subnet hole (`family(specific)` or `extern "raw"`).

Round-trip / build tooling lives in `../tooling/` (`lift.py`, `compile.py`, `coverage.py`, `generate.py`).
