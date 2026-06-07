# IMQL coding conventions

Conventions for writing `.imql`, in the spirit of the [QML coding
conventions](https://doc.qt.io/qt-6/qml-codingconventions.html). They are **enforced by a formatter** —
`tooling/fmt.py` (imql-fmt) — so you rarely apply them by hand: write a mechanism, then run
`fmt.py -i your.imql`. CI can gate with `fmt.py --check`.

## Layout

- **4-space indentation.** Never tabs.
- **One mechanism per file**, extension `.imql`. The mechanism name is PascalCase.
- A mechanism body is written in three groups, separated by a single blank line, in this order
  (the QML "id → properties → children" idea):

```text
mechanism PairwiseArena {
    netuid: 42                    # 1. header properties — one per line, canonical order:
    lang: python                  #    netuid, lang, status, submission
    status: active
    submission: [model_weights]

    @burn { uid: 0, fraction: dynamic }          # 2. overlays — @burn, @guards, @state
    @guards {
        commit_reveal { enforcement: rejection }
        deterministic_check { enforcement: rejection }
    }
    @state { cumulative_score }

    pipeline {                                   # 3. the combinator block
        score: metric win_rate fam classification_quality spec pairwise_win_rate { direction: higher_is_better, normalization: none }
        gt: llm_judgment { trust_model: adversarial }
        aggregate: aggregator weighted_average { normalization: sum_to_one }
        smooth: smoother ema(alpha: 0.1)
        emit: set_weights { cadence: per_epoch, tempo: "360 blocks" }
    }
}
```

## Property blocks

- A property block is `{ key: value, key: value }` — a single space inside the braces, `, ` between
  entries, one space after each colon.
- **Omit properties whose value is null.** Write `aggregator other { composition: rank, temperature: 0.01 }`,
  not `... { composition: rank, normalization: -, temperature: 0.01, decay_rate: -, min_weight_floor: - }`.
  An absent property *is* null; spelling it out is noise.

## Overlays

- `@burn` and `@state` are written **inline**: `@burn { uid: 0, fraction: dynamic }`,
  `@state { cumulative_score, registration_age }`.
- `@guards` holds *elements*, not properties: a single guard is inline
  (`@guards { commit_reveal { enforcement: rejection } }`); **two or more guards go one per line**.

## The combinator body

- Items appear in canonical order — `score` (one per signal), `gt` (one per ground-truth source),
  `aggregate`, `smooth`, `emit`, `tracks` — one per line.
- The metric leaf reads left to right: `metric <kind> [fam <family>] [spec <specific>] [raw "…"] [extern]`.
  A fully opaque metric is `extern "…"` (or `metric <kind> raw "…" extern`).

## Literals

- `null` is written `-`. The dynamic burn fraction is the keyword `dynamic`.
- Strings are double-quoted; identifiers and enum values are bare.
- Files end with a single newline and carry no trailing whitespace.

## Comments

`# …` runs to end of line and is ignored by the tooling. Because IMQL is purely structural, the
**formatter does not preserve comments** — keep commentary in surrounding prose/docs, not inside
canonical `.imql` files.

## The formatter

```bash
./.venv/bin/python tooling/fmt.py mechanism.imql        # print formatted
./.venv/bin/python tooling/fmt.py -i mechanism.imql     # rewrite in place
./.venv/bin/python tooling/fmt.py --check examples/     # CI gate: non-zero if any file is unformatted
```

It works by parsing and re-emitting, so its output is the single source of truth for "formatted" —
there is nothing to argue about. Every `.imql` lifted from a corpus instance (`tooling/lift.py`) is
already in canonical form.
