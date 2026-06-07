# IMQL coding conventions

These follow Qt's [QML Coding Conventions](https://doc.qt.io/qt-6/qml-codingconventions.html) as closely
as IMQL's structure allows, and are **enforced by a formatter** — `tooling/fmt.py` (imql-fmt), the analog
of [`qmlformat`](https://doc.qt.io/qt-6/qtqml-tooling-qmlformat.html). Write a mechanism, then run
`fmt.py -i your.imql`; gate in CI with `fmt.py --check`.

## Member ordering

QML orders an object's members as: **id → property declarations → signal declarations → JavaScript
functions → object properties → child objects**, with *"an empty line"* separating the groups. IMQL has
no signals or JavaScript, so the mapping is:

| QML | IMQL |
|---|---|
| id (first line) | `mechanism <Name>` + the identifying `netuid` |
| property declarations | header properties: `netuid`, `lang`, `status`, `submission` |
| object properties | overlays: `@burn`, `@guards`, `@state` (attached-property style) |
| child objects | the combinator block (`pipeline` / `multiplex` / …) |

The three IMQL groups are separated by a single blank line, exactly as QML separates its member groups.

## Indentation & layout

- **4-space indentation**, never tabs (the `qmlformat` default).
- **One property per line** in the header — *"we generally declare each property on a separate line, even
  for simple expressions."*
- One mechanism per file, extension `.imql`; the mechanism name is PascalCase.

## Grouped properties — semicolons

A grouped-property block is written inline with **semicolons**, matching QML exactly
(`anchors { left: parent.left; top: parent.top; leftMargin: 20 }`):

```text
score: metric win_rate fam classification_quality spec pairwise_win_rate { direction: higher_is_better; normalization: none }
aggregate: aggregator weighted_average { composition: weighted_sum; normalization: sum_to_one }
emit: set_weights { cadence: per_epoch; tempo: "360 blocks" }
```

Single space after each `:`, `; ` between entries, a space inside the braces, and **null-valued
properties are omitted** (an absent property *is* null; spelling out `decay_rate: -` is noise).

## Lists — omit brackets for a single element

Per the QML list convention, *a list with one element omits the square brackets*:

```text
submission: signals                 # one element
submission: [model_weights, commitment_hash]   # several
```

## Overlays & child objects

- `@burn` and `@state` are inline grouped properties: `@burn { uid: 0; fraction: dynamic }`,
  `@state { cumulative_score, registration_age }`.
- `@guards` holds *child objects* (guards), so it follows the child-object rule: a single guard is inline
  (`@guards { commit_reveal { enforcement: rejection } }`); **two or more go one per line**:

```text
@guards {
    commit_reveal { enforcement: rejection }
    deterministic_check { enforcement: rejection }
}
```

## The combinator body

Items appear in canonical order — `score` (per signal), `gt` (per ground-truth source), `aggregate`,
`smooth`, `emit`, `tracks` — one per line. The metric leaf reads left to right:
`metric <kind> [fam <family>] [spec <specific>] [raw "…"] [extern]`.

## Literals & whitespace

- `null` is `-`; the dynamic burn fraction is the keyword `dynamic`.
- Strings are double-quoted; identifiers and enum values are bare.
- Files end with a single newline and carry no trailing whitespace.

## Worked example

```text
mechanism PairwiseArena {
    netuid: 42
    lang: python
    status: active
    submission: model_weights

    @burn { uid: 0; fraction: dynamic }
    @guards {
        commit_reveal { enforcement: rejection }
        deterministic_check { enforcement: rejection }
    }
    @state { cumulative_score }

    pipeline {
        score: metric win_rate fam classification_quality spec pairwise_win_rate { direction: higher_is_better; normalization: none }
        gt: llm_judgment { trust_model: adversarial }
        aggregate: aggregator weighted_average { normalization: sum_to_one }
        smooth: smoother ema(alpha: 0.1)
        emit: set_weights { cadence: per_epoch; tempo: "360 blocks" }
    }
}
```

## Comments

`# …` runs to end of line and is ignored by the tooling. Because IMQL is purely structural, the
**formatter does not preserve comments** (like `qmlformat` historically reformatted aggressively) — keep
commentary in surrounding prose/docs, not inside canonical `.imql`.

## The formatter

```bash
./.venv/bin/python tooling/fmt.py mechanism.imql        # print formatted
./.venv/bin/python tooling/fmt.py -i mechanism.imql     # rewrite in place (cf. qmlformat -i)
./.venv/bin/python tooling/fmt.py --check examples/     # CI gate: non-zero if any file is unformatted
```
