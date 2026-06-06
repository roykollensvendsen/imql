# Field reference

Authoritative definitions live in `schema/incentive-mechanism.schema.json`. This is the human-readable
companion. Enum values are listed; `other` + the sibling `*_other` field covers anything unlisted.

## Top level

| field | req | type | meaning |
|---|---|---|---|
| `schema_version` | ✓ | semver string | must equal `schema/VERSION` (currently `1.0.0`) |
| `instance_kind` | ✓ | `extracted` \| `authored` | extracted ⇒ `provenance` + `subnet.owner_repo` required |
| `mechanism_status` | – | enum | `active`\|`partial_burn`\|`full_burn`\|`dormant`\|`mixed`\|`unknown` — operative reality vs documented mechanism |
| `subnet` | ✓ | object | identity |
| `task` | ✓ | object | what miners produce |
| `scoring_signals` | ✓ | array | measured quantities (may be empty for docs-only) |
| `ground_truth_sources` | – | array | where the "correct answer" comes from |
| `aggregation` | – | object | raw scores → on-chain weights |
| `weight_setting` | – | object | cadence + on-chain method |
| `anti_gaming` | – | array | controls against gaming/sybil/plagiarism |
| `sub_competitions` | – | object | multi-mechanism / ladder / tournament structure |
| `per_miner_state` | – | object | persistent per-miner state (debt ledgers, status enums) |
| `documentation` | ✓ | object | status of the source material |
| `provenance` | cond | object | audit trail; required for `extracted` |
| `extensions` | – | object | novelty escape hatch |

## `subnet`
`name` (✓), `owner_repo` (`Owner__repo`; req for extracted), `netuid`, `implementation_lang`
(`python|go|typescript|rust|mixed|none_docs_only|other`).

## `task`
`summary` (✓), `submission_format` (✓, array of `model_weights|source_code|signals|content_link|
commitment_hash|api_response|compute_service|other`).

## `scoring_signals[]`
`name` (✓), `metric_kind` (✓: `loss|accuracy|regression_error|pnl|win_rate|similarity|engagement|
uptime|hardware_spec|llm_judgment|vlm_judgment|human_judgment|throughput|latency|risk_adjusted_ratio|
probabilistic_forecast|predictive_contribution|reward|composite|volume|other`),
`direction` (✓: `higher_is_better|lower_is_better|target_band`), `weight` (null for gated/multiplicative
signals), `normalization` (`none|min_max|zscore|rank|softmax|ema|other`) + `normalization_other`.

## `ground_truth_sources[]`
`kind` (✓: `deterministic_dataset|reference_model|market_data|llm_judgment|hardware_probe|
real_engagement|commit_reveal|organic_traffic|other`), `source_identifier`, `trust_model`
(`trusted|adversarial|oracle|crowd|unknown`), `notes`.

## `aggregation`
`method` (✓: `rank_based|softmax|exponential_decay_ema|weighted_average|tournament_bracket|
binary_threshold|winner_take_all|proportional|convex_optimization|undocumented|other`),
`composition` (`weighted_sum|multiplicative|gated|rank|tournament|hybrid|other` — how signals combine),
`normalization` (`none|sum_to_one|min_max|softmax|l1|other`) + `normalization_other`,
`temperature` (softmax temperature), `decay_rate` (within-aggregation rank/temporal decay — NOT the EMA),
`min_weight_floor`, `burn_allocation{enabled✓, address_or_uid, fraction, dynamic, notes}`.

## `weight_setting`
`cadence` (✓: `per_epoch|per_round|continuous|rate_limited|weekly|daily|per_brief|per_tournament|
undocumented|other`), `method`, `on_chain_call` (`set_weights|commit_reveal|other|unknown`),
`tempo_or_interval` (string or integer), `smoothing{kind✓: none|ema|sma|other, alpha, window, notes}`
— **this is the EMA home** (the dominant Bittensor final-reward smoother), distinct from `aggregation.decay_rate`.

## `anti_gaming[]`
`kind` (✓: `proof_of_work|plagiarism_detection|deduplication|collateral|challenge_period|
hardware_validation|deterministic_check|commit_reveal|stake_weighting|rate_limit|code_inspection|
data_augmentation|risk_limit|liveness_check|honeypot|other`),
`enforcement` (✓: `elimination|penalty|rejection|barrier|other`) + `enforcement_other`, `description`.

## `sub_competitions`
`structure` (✓: `none|single|multi_mechanism|ladder|tournament|multi_asset|multi_brief|per_task_type|
tiered|other`),
`stages[]` (`name✓`, `role✓: challenge|probation|main|qualifier|group|knockout|final|boss|other`,
`advancement_rule`, `multipliers`), `count`.

## `per_miner_state`
`tracked` (✓), `state_kinds[]` (`debt_ledger|performance_ledger|status_enum|cumulative_score|
cooldown|reputation|registration_age|other`), `status_values[]`, `reset_policy`.

## `documentation`
`status` (✓: `code_authoritative|docs_authoritative|docs_and_code|docs_only|whitepaper_only|
sparse|absent`), `source_version`, `primary_docs[]`, `completeness` (`high|medium|low`).

## `provenance` (required for `extracted`)
`confidence_overall` (✓: `high|medium|low`), `evidence[]` (✓, ≥1 item: `claim_field✓` JSON Pointer,
`source_path✓`, `line_ref`, `quote`, `confidence`), `unresolved[]`, `extracted_by`, `extractor_notes`.
