# Corpus extraction summary

The full `academia-archives` corpus has been reverse-engineered into schema-validated instances.

## Coverage

| | count |
|---|---|
| Total archives (`academia-archives/repos`) | 189 |
| Sample instances (`instances/sample/`) | 18 |
| Corpus instances (`instances/corpus/`) | 171 |
| **Covered** | **189 / 189 (100%)** |
| Valid against schema 1.0.0 | 189 / 189 |
| Missing / uncovered | 0 |

Run history: a first bulk run extracted 104 cleanly but lost 85 to a tooling failure mode — the
agents wrote valid YAML but failed to emit the forced ~100-field `StructuredOutput` status object
(counted as "failed" though the artifact existed). A recovery run with `USE_SCHEMA=false` (the only
deliverable being the written+validated YAML, status returned as a plain line) recovered all 85 in
~17 min, 85/85 ok. Coverage is reconciled from disk (`validate.py`), not from workflow status.

## Distributions (across all 189)

**mechanism_status** — burn is pervasive: ~106 of 189 instances involve some burn or dormancy.

| status | count |
|---|---|
| partial_burn | 51 |
| active | 50 |
| mixed | 35 |
| (unset — mostly pre-`mechanism_status` sample instances) | 17 |
| unknown | 16 |
| full_burn | 15 |
| dormant | 5 |

**implementation_lang**

| lang | count |
|---|---|
| python | 164 |
| none_docs_only | 11 |
| typescript | 5 |
| rust | 4 |
| mixed | 3 |
| go | 2 |

## Headline finding: the `other` value-tail is long and flat

The single most important schema result. Counting the free-text `*_other` values across all 189
instances:

| field | distinct values | total uses | max repeat |
|---|---|---|---|
| `metric_kind_other` | 75 | 75 | 1 |
| `kind_other` (ground-truth + anti-gaming) | 83 | 84 | 2 |
| `normalization_other` | 46 | 47 | 2 |
| `submission_format_other` | 21 | 21 | 1 |
| `enforcement_other` | 17 | 17 | 1 |

Almost nothing recurs (only `ip_region_concentration_cap` and one normalization note hit 2×). The
diversity of real incentive-mechanism vocabulary is genuinely flat-tailed: each subnet's "other" is
bespoke. **Therefore v1.1 does NOT promote these to enum members** — doing so would over-fit single
instances and violate the ≥2× governance bar. The enum-plus-escape-hatch design is working as intended:
common cases stay machine-aggregatable, the long tail is captured without distortion. This is a finding
about the domain, not a gap in the schema.

## What DID recur (structural, not value) → v1.1 candidates

Type/shape stress that recurred ≥2× and is worth a governed bump (see `schema/CHANGELOG.md`):

- `aggregation.burn_allocation.address_or_uid` is `string|null` but on-chain burn targets are integer
  UIDs (agents had to quote `"0"`, `"199"`). → accept integer.
- `task` had no `notes` field (parallel to the `ground_truth_sources[].notes` added in v1).
- Recurrent but genuinely diverse (left to `notes`/`extensions`, NOT structural fields): per-round
  leader-weight decay; rank→weight mapping functions; dead/dormant scoring code vs live burn (already
  captured by `mechanism_status` + `documentation`).

See `reports/schema-stress-corpus.md` for the full per-field, per-repo breakdown.
