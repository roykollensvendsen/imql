# Quick start

## Install

```bash
cd incentive-schema
python3 -m venv .venv
./.venv/bin/pip install -r tooling/requirements.txt
```

## Author a mechanism

Write a `.imml` file:

```text title="my-mechanism.imml"
Mechanism {
    id: myMechanism

    netuid: 123
    lang: python
    status: active
    submission: signals

    @guards {
        DeterministicCheck {
            enforcement: rejection
        }
    }

    Pipeline {
        score: metric accuracy {
            direction: higher_is_better
            normalization: none
        }
        groundTruth: DeterministicDataset {
            trust_model: trusted
        }
        aggregate: WeightedAverage {
            normalization: sum_to_one
        }
        smooth: smoother ema(alpha: 0.1)
        publish: SetWeights {
            cadence: per_epoch
        }
    }
}
```

## Compile → validate

```bash
./.venv/bin/python tooling/compile.py my-mechanism.imml > my-mechanism.yaml
./.venv/bin/python tooling/validate.py my-mechanism.yaml      # -> 1/1 valid
```

A clean compile + validate means the **structure** of your mechanism is complete. Any `extern "…"`
leaf is the bespoke judgment you must hand-write — surfaced explicitly, never hidden.

## Generate a runnable scaffold

```bash
./.venv/bin/python tooling/generate.py my-mechanism.yaml -o validator.py
```

`validator.py` wires the aggregator, smoother, weight-setter, guards, and burn overlay, and gives each
scoring signal a `score_i()` — a real primitive from the metric library when the family resolves, or a
clearly-marked `NotImplementedError` for a bespoke metric.

## Read an existing subnet

Every corpus subnet lifts to IMML:

```bash
./.venv/bin/python tooling/lift.py instances/corpus/<Owner>__<repo>.yaml
```

Browse all 189 in the **[Examples gallery](../examples/index.md)**.
