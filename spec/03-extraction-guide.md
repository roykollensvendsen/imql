# Extraction guide (descriptive path)

Reverse-engineer one subnet from `academia-archives/repos/<Owner>__<repo>/` into an
`instance_kind: extracted` instance. The `im-extract` skill automates this; the discipline below is
what makes the result trustworthy.

## Locate (where the mechanism lives)

| Language | weights call | reward/scoring | hyperparameters | docs |
|---|---|---|---|---|
| Python (~81%) | `neurons/validator.py` (`.set_weights`) | `<pkg>/validator/reward.py` \| `scorer.py` | `constants.py`, `utils/config.py` | `README.md`, `docs/incentive*.md` |
| Go | `*/weights_util.go` | `internal/validator/score_task.go` | `*.json` configs | `README.md`, `docs/` |
| TypeScript | `utils/setWeights.ts` | `validator/*.ts`, `*poolWeights*` | `config/` | `README.md` |
| Docs-only | — | — | — | `README.md`, `*.pdf`, versioned `vN/` dirs |

`im-extract/scripts/locate.py` ranks these anchors automatically.

## Evidence discipline (non-negotiable)

Every non-trivial field MUST be backed by a `provenance.evidence` entry: a `source_path`, a `line_ref`,
and a short verbatim `quote`. Specifically:

- **No field without a quote.** If you cannot point to source text, leave the field null/empty and add
  a line to `provenance.unresolved`.
- **Never invent numeric constants.** `decay_rate`, `min_weight_floor`, burn fractions, multipliers,
  thresholds — only fill them if they appear literally in the code/config. A fabricated constant is a
  hard failure of the extraction.
- **Docs-only ⇒ low confidence.** Set `documentation.status` to `docs_only`/`whitepaper_only`/`absent`
  and `provenance.confidence_overall: low`. Leave code-derived fields empty.
- **Quote, don't paraphrase, in evidence.** The `quote` must be copyable text that a reviewer can grep.

## Procedure

1. Classify language/archetype (`locate.py`).
2. Read the located files (weights call, reward fn, constants, incentive docs).
3. Fill the schema top-down; attach an evidence item per claim with `claim_field` as a JSON Pointer
   (e.g. `/aggregation/decay_rate`).
4. Set `instance_kind: extracted`, `subnet.owner_repo` to the corpus dir name.
5. Self-validate: `python tooling/validate.py <instance>`; fix and repeat until clean.
6. Record any enum `other`, missing-home fact, or over-required field — this is the stress signal that
   `tooling/stress-report.py` aggregates for the v0→v1 refinement.

## Audit

A reviewer (or an adversarial verifier subagent) takes any field, opens its cited `source_path:line_ref`,
and confirms the `quote` actually supports the value. Target: ≥90% of audited fields supported; zero
fabricated constants.
