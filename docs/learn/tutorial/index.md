# Tutorial: zero to hero

Welcome. By the end of this tutorial you will have **designed a subnet's incentive mechanism, written it in
IMML, compiled it, generated a runnable validator, and stress-tested it against cheaters** — and you'll have
caught a real attack and fixed it.

You don't need to know Bittensor or read anything else first. We'll build one concrete example together and
explain every decision as we go. Any unfamiliar word links to the [glossary](../../reference/glossary.md).

!!! abstract "What you'll have built"
    - `price-oracle.imml` — a mechanism in the readable IMML surface language
    - `price-oracle.yaml` — its compiled, schema-validated [IR](../../reference/glossary.md)
    - `validator.py` — a generated validator scaffold
    - a **simulator verdict** telling you whether honest miners actually win — and how to fix it when they don't

## The subnet we'll design

We'll build the incentive mechanism for an imaginary subnet — call it **Price Oracle**:

> Miners submit a **price forecast** each round. The validator scores each forecast for **accuracy** against
> the real price once it's known, then pays miners in proportion to how accurate they were.

It's deliberately simple. That's the point — a clean example shows the moving parts without the noise of a
real subnet. (For a real, more elaborate analogue, see any of the prediction subnets in the
[examples gallery](../../examples/index.md).)

## Setup

You need the repo and a Python virtualenv:

```bash
cd incentive-schema
python3 -m venv .venv
./.venv/bin/pip install -r tooling/requirements.txt
```

That's it — the tooling (`compile`, `validate`, `generate`, `simulate`) is pure-Python and runs offline.

!!! tip "In a hurry?"
    If you just want the commands without the teaching, the [quick start](../../guides/quick-start.md) is the
    five-minute version. This tutorial is the slow, explained path — recommended for your first time.

---

**[Step 1: Design the mechanism →](01-design.md)**
