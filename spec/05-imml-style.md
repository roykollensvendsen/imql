# IMML coding conventions

These follow Qt's [QML Coding Conventions](https://doc.qt.io/qt-6/qml-codingconventions.html) as closely
as IMML's structure allows, and are **enforced by a formatter** — `tooling/fmt.py` (imml-fmt), the analog
of [`qmlformat`](https://doc.qt.io/qt-6/qtqml-tooling-qmlformat.html). Write a mechanism, then run
`fmt.py -i your.imml`; gate in CI with `fmt.py --check`.

## Member ordering

QML orders an object's members as: **id → property declarations → signal declarations → JavaScript
functions → object properties → child objects**, with *"an empty line"* separating the groups. IMML has
no signals or JavaScript, so the mapping is:

| QML | IMML |
|---|---|
| id (first line) | `id: <Name>` inside the `Mechanism { … }` root object |
| property declarations | header properties: `netuid`, `lang`, `status`, `submission` |
| object properties | overlays: `@burn`, `@guards`, `@state` (attached-property style) |
| child objects | the combinator block (`Pipeline` / `Multiplex` / …) and guards — PascalCase, like QML types |

Each IMML group is separated from the next by a single blank line, exactly as QML separates its member
groups — including the `id`, which sits alone above the header properties.

## Indentation & layout

- **4-space indentation**, never tabs (the `qmlformat` default).
- **One property per line** in the header — *"we generally declare each property on a separate line, even
  for simple expressions."*
- One mechanism per file, extension `.imml`; the `id` is camelCase (QML ids are camelCase; PascalCase is
  reserved for types — here the root type `Mechanism`).
- **Casing follows QML's type-vs-value split: child objects are PascalCase, everything else is lowercase.**
  Child objects (a `TypeName { … }` instantiation) — the combinator (`Pipeline`, `Multiplex<single>`,
  `Gated`, `Multiplicative`, `OverlayOnly`, `Opaque`) and the guards (`CommitReveal`, `ProofOfWork`, …) —
  are PascalCase. Property names (`score`, `aggregate`, `publish`, `direction`) and enum values
  (`weighted_average`, `set_weights`, `rejection`, `higher_is_better`) stay lowercase. The IR keeps its
  lowercase snake_case enums; the PascalCase is purely the surface (lift/compile convert).

## Grouped properties — one per line

A grouped-property block puts **one property per line**, each indented four spaces under its owner, with
the closing brace aligned to the owner — exactly as QML lays out an expanded grouped property
(`font { family: "..."; pixelSize: 12 }` may also be written multi-line):

```text
score: metric win_rate fam classification_quality spec pairwise_win_rate {
    direction: higher_is_better
    normalization: none
}
aggregate: WeightedAverage {
    composition: weighted_sum
    normalization: sum_to_one
}
publish: SetWeights {
    cadence: per_epoch
    tempo: "360 blocks"
}
```

Single space after each `:`, no separator between lines (`;` is also accepted by the parser; commas are
not — they are reserved for genuine lists like `@state` and `submission`),
and **null-valued properties are omitted** (an absent property *is* null; spelling out `decay_rate: -` is
noise). An empty block collapses to `{}`.

## Lists — omit brackets for a single element

Per the QML list convention, *a list with one element omits the square brackets*:

```text
submission: signals                 # one element
submission: [model_weights, commitment_hash]   # several
```

## Overlays & child objects

- `@burn` is a grouped property, so its members go one per line:

```text
@burn {
    uid: 0
    fraction: dynamic
}
```

- `@state` is the exception — a bare flag *list*, not key/value properties — so it stays inline:
  `@state { cumulative_score, registration_age }`.
- `@guards` holds *child objects* (guards), one per line; each guard's own property block expands too:

```text
@guards {
    CommitReveal {
        enforcement: rejection
    }
    DeterministicCheck {
        enforcement: rejection
    }
}
```

## The combinator body

Items appear in canonical order — `score` (per signal), `groundTruth` (per ground-truth source), `aggregate`,
`smooth`, `publish`, `tracks` — one per line. The metric leaf reads left to right:
`metric <kind> [fam <family>] [spec <specific>] [raw "…"] [extern]`.

## Literals & whitespace

- `null` is `-`; the dynamic burn fraction is the keyword `dynamic`.
- Strings are double-quoted; identifiers and enum values are bare.
- Files end with a single newline and carry no trailing whitespace.

## Worked example

```text
Mechanism {
    id: pairwiseArena

    netuid: 42
    lang: python
    status: active
    submission: model_weights

    @burn {
        uid: 0
        fraction: dynamic
    }
    @guards {
        CommitReveal {
            enforcement: rejection
        }
        DeterministicCheck {
            enforcement: rejection
        }
    }
    @state { cumulative_score }

    Pipeline {
        score: metric win_rate fam classification_quality spec pairwise_win_rate {
            direction: higher_is_better
            normalization: none
        }
        groundTruth: LlmJudgment {
            trust_model: adversarial
        }
        aggregate: WeightedAverage {
            normalization: sum_to_one
        }
        smooth: smoother ema(alpha: 0.1)
        publish: SetWeights {
            cadence: per_epoch
            tempo: "360 blocks"
        }
    }
}
```

## Comments

`# …` runs to end of line and is ignored by the tooling. Because IMML is purely structural, the
**formatter does not preserve comments** (like `qmlformat` historically reformatted aggressively) — keep
commentary in surrounding prose/docs, not inside canonical `.imml`.

## The formatter

```bash
./.venv/bin/python tooling/fmt.py mechanism.imml        # print formatted
./.venv/bin/python tooling/fmt.py -i mechanism.imml     # rewrite in place (cf. qmlformat -i)
./.venv/bin/python tooling/fmt.py --check examples/     # CI gate: non-zero if any file is unformatted
```
