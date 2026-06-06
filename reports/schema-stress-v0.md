# Schema stress report

Instances analyzed: **18**  
Repos: Barbariandev__MANTIS, Bitsec-AI__subnet, Datura-ai__compute-subnet, It-s-AI__llm-detection, backend-developers-ltd__ComputeHorde, bigideaafrica__polaris, bitcast-network__bitcast, coinmetrics__precog, fx-integral__merit, gradients-ai__G.O.D, macrocosm-os__finetuning, macrocosm-os__pretraining, macrocosm-os__prompting, mode-network__synth-subnet, sportstensor__sn41, taoshidev__proprietary-trading-network, tensorplex-labs__dojo, v0idai__SN106


## Enum 'other' usage (candidate new enum values)

| field | count | repos |
|---|---|---|
| `/anti_gaming/1` | 7 | Bitsec-AI__subnet, backend-developers-ltd__ComputeHorde, fx-integral__merit, gradients-ai__G.O.D, mode-network__synth-subnet, taoshidev__proprietary-trading-network, tensorplex-labs__dojo |
| `/scoring_signals/1` | 6 | It-s-AI__llm-detection, backend-developers-ltd__ComputeHorde, bigideaafrica__polaris, gradients-ai__G.O.D, taoshidev__proprietary-trading-network, v0idai__SN106 |
| `/scoring_signals/0` | 5 | Barbariandev__MANTIS, fx-integral__merit, macrocosm-os__prompting, mode-network__synth-subnet, v0idai__SN106 |
| `/weight_setting` | 4 | bigideaafrica__polaris, bitcast-network__bitcast, tensorplex-labs__dojo, v0idai__SN106 |
| `/anti_gaming/3` | 3 | It-s-AI__llm-detection, bitcast-network__bitcast, macrocosm-os__finetuning |
| `/anti_gaming/0` | 3 | fx-integral__merit, macrocosm-os__finetuning, tensorplex-labs__dojo |
| `/scoring_signals/2` | 3 | gradients-ai__G.O.D, taoshidev__proprietary-trading-network, v0idai__SN106 |
| `/scoring_signals/3` | 2 | It-s-AI__llm-detection, taoshidev__proprietary-trading-network |
| `/anti_gaming/2` | 2 | It-s-AI__llm-detection, bitcast-network__bitcast |
| `/aggregation` | 2 | bigideaafrica__polaris, macrocosm-os__pretraining |
| `/scoring_signals/4` | 2 | macrocosm-os__finetuning, taoshidev__proprietary-trading-network |
| `/sub_competitions` | 2 | tensorplex-labs__dojo, v0idai__SN106 |
| `/anti_gaming/4` | 1 | bitcast-network__bitcast |
| `/ground_truth_sources/0` | 1 | fx-integral__merit |
| `/scoring_signals/5` | 1 | taoshidev__proprietary-trading-network |
| `/scoring_signals/6` | 1 | taoshidev__proprietary-trading-network |

_Bar for a schema change: count >= 2._

## Unresolved fields (missing-home / unknowable facts)

| repo | note |
|---|---|
| Barbariandev__MANTIS | source_version: no git tag / version string present in the repo. |
| Barbariandev__MANTIS | BURN_PCT documentation conflict: README Key Parameters table lists 0.30 for UID 0 while config.py defines BURN_PCT = 0.45; code value used. |
| Barbariandev__MANTIS | TLOCK lock duration (TLOCK_DEFAULT_LOCK_SECONDS=30 / suggested 3600) defines the embargo/maturation window but exact enforced Drand-round lag per payload is set by miners, not a single fixed constant. |
| Bitsec-AI__subnet | min_weight_floor / burn allocation: no floor or burn fraction present in code. |
| Bitsec-AI__subnet | scoring_signal weights: reward() returns the raw Jaccard score directly; there is no explicit per-signal weighting constant to cite. |
| Bitsec-AI__subnet | source_version: no version tag found (__version__ = '0.0.0' is a template placeholder). |
| Bitsec-AI__subnet | Severity and line_range matching are present in the protocol but marked TODO/unused in the live reward path. |
| Datura-ai__compute-subnet | /scoring_signals/*/weight — no scalar per-signal weights; checks are binary gates and multiplicative penalties, not a weighted sum. |
| Datura-ai__compute-subnet | /aggregation/min_weight_floor — _convert_weights_with_positive_floor applies a positive floor to nonzero weights but no literal floor constant was located. |
| Datura-ai__compute-subnet | /aggregation/burn_allocation/address_or_uid — burner UIDs come from runtime settings.NEW_BURNERS / settings.BURNERS, not a literal in the read source. |
| Datura-ai__compute-subnet | Exact active incentive algorithm (DefaultIncentive vs rental_price) depends on settings.incentive at deploy time; not pinned in read source. |
| Datura-ai__compute-subnet | Collateral default behavior: ENABLE_NO_COLLATERAL=True and SKIP_COLLATERAL_PENALTY=True in config defaults soften collateral gating; production env may override. |
| It-s-AI__llm-detection | burn_allocation: no burn / owner-take mechanism appears in the weight-setting code. |
| It-s-AI__llm-detection | aggregation.decay_rate and min_weight_floor: not expressed as literal constants (EMA uses alpha 0.2/0.3, not a decay_rate; no explicit weight floor). |
| It-s-AI__llm-detection | out_of_domain_alpha=0.2 is hardcoded in neurons/validator.py (self.out_of_domain_alpha = 0.2) but the schema has no dedicated field for this secondary EMA rate. |
| backend-developers-ltd__ComputeHorde | aggregation.decay_rate / min_weight_floor: no exponential decay or explicit weight floor found; on-chain min/max bounds come from chain hyperparameters (min_allowed_weights, max_weights_limit), not literals in this repo. |
| backend-developers-ltd__ComputeHorde | burn_allocation.address_or_uid / fraction: configured at runtime via DYNAMIC_BURN_TARGET_SS58ADDRESSES and DYNAMIC_BURN_RATE (defaults empty / 0.0); no concrete on-chain target literal in source. |
| backend-developers-ltd__ComputeHorde | Exact live combination of synthetic-job scores with organic allowance scores: scoring README describes combining both per executor class, but the active engine.py path scores only allowance-paid (organic) jobs; the synthetic-vs-organic blend in production is not pinned to one code site. |
| backend-developers-ltd__ComputeHorde | scoring_signals[1].weight: no literal numeric weight for the fixed-per-job organic score relative to allowance-seconds; left null. |
| backend-developers-ltd__ComputeHorde | per_miner_state.status_values: no closed status enum literal extracted for miner lifecycle states. |
| bigideaafrica__polaris | aggregation.method — no score-to-weight aggregation algorithm is described in any README. |
| bigideaafrica__polaris | aggregation.decay_rate / min_weight_floor — no numeric constants documented anywhere. |
| bigideaafrica__polaris | weight_setting.cadence / on_chain_call / tempo_or_interval — no on-chain weight-setting described. |
| bigideaafrica__polaris | scoring_signals[*].weight — no relative weighting of signals documented. |
| bigideaafrica__polaris | self_validation_benchmark — metric definition, units, scoring formula, and thresholds undocumented. |
| bigideaafrica__polaris | gpu_reward_qualification — exact reward function beyond the 24GB VRAM / NVIDIA-only gate is undocumented. |
| bigideaafrica__polaris | subnet.netuid — Bittensor netuid is not stated in the distribution docs. |
| bigideaafrica__polaris | per_miner_state status_values / reset_policy — concrete per-miner state model not documented. |
| bigideaafrica__polaris | burn_allocation — presence/absence of any burn not documented; assumed disabled, not confirmed. |
| bitcast-network__bitcast | subnet.netuid: not stated in repo source/config (netuid passed via runtime config self.config.netuid). |
| bitcast-network__bitcast | aggregation.decay_rate / min_weight_floor: no decay-rate or weight-floor constant in scoring; emission floor YT_MIN_EMISSIONS=0 disables the global-minimum scaling path. |
| bitcast-network__bitcast | weight_setting.tempo_or_interval: VALIDATOR_STEPS_INTERVAL=240 with inline comment '4 hours'; the 240->4h mapping is the comment's claim, exact unit (steps vs seconds) not independently confirmed. |
| bitcast-network__bitcast | sub_competitions.count: number of concurrent briefs is dynamic (fetched from briefs server), no literal count in source. |
| bitcast-network__bitcast | scoring_signals weights: the three signals are not combined by fixed numeric weights; revenue/minutes are alternatives by account type and brief-match is a gate, so per-signal 'weight' is not a literal constant. |
| bitcast-network__bitcast | per-brief 'boost', 'cap', 'max_count', 'unique_identifier', 'start_date'/'end_date' are supplied per-brief by the off-repo briefs server, not as in-repo constants. |
| coinmetrics__precog | Exact weights_rate_limit value: read from chain hyperparameters at runtime (subtensor.get_subnet_hyperparameters), not a literal in the repo, so tempo cannot be pinned to a block count. |
| coinmetrics__precog | burn_allocation: no burn/null-UID routing found in the code; left disabled rather than asserted absent. |
| coinmetrics__precog | EVALUATION_WINDOW_HOURS=6 constant is defined but its role is not exercised in calc_rewards (which uses PREDICTION_FUTURE_HOURS=1 for the prediction window); its effect on scoring is unresolved. |
| coinmetrics__precog | min_weight_floor: no explicit floor found; if-all-zero fallback emits uniform [1]*n weights but that is not a per-miner floor. |
| fx-integral__merit | /scoring_signals/*/weight: BMPS has no per-signal numeric weight. The two signals (cross-subnet incentive, liveness) are not additively weighted — liveness is a binary gate that zeroes BMPS, while the incentive average is the sole positive magnitude. Left null. |
| fx-integral__merit | /aggregation/decay_rate and /min_weight_floor: no temporal decay/EMA or weight floor exists in the code. The S-curve polynomial coefficients (-1.038e-7, 6.214e-5, -0.0129, -0.0118) are rank-reward shape constants, not a decay rate or floor, so they are documented in aggregation.notes rather than forced into those numeric fields. |
| fx-integral__merit | Whitepaper "Max Validators 64" and per-signal "weight" balance between ping and incentive ("ping acts as a small fine-tuning adjustment") are descriptive only; in code the ping is a hard zero gate, not a fractional adjustment. No field captures the validator cap. |
| gradients-ai__G.O.D | /aggregation/burn_allocation/fraction: burn fraction is computed dynamically (1 - sum of tournament weights + undistributed); no fixed literal. |
| gradients-ai__G.O.D | /aggregation/min_weight_floor: no global per-miner weight floor found; only progressive championship threshold floor (0.03) which governs boss-round dethroning, not weights. |
| gradients-ai__G.O.D | /scoring_signals/*/weight: individual signal numeric weights are not assigned; ranking is positional within each task type. |
| gradients-ai__G.O.D | Exact per-task-type GPU-size thresholds (4.0/12.0/40.0B) influence compute allocation, not score, so omitted from scoring_signals. |
| macrocosm-os__finetuning | Exact CompetitionTracker EMA update formula and get_subnet_weights merge math live in the external 'taoverse' package, which is not vendored in this repo; alpha=0.90 and the 0.18 threshold are confirmed locally but the precise normalization step is not directly citable here. |
| macrocosm-os__finetuning | normalize_score / INVERSE_EXPONENTIAL exact transform is in taoverse (not in-repo); only the ceiling kwargs (20.0, 40.0) are citable locally. |
| macrocosm-os__finetuning | Whether multiple competitions are concurrently active at the current chain block (vs. only the latest scheduled one) depends on live block height vs. SUNSET_* blocks; not determinable from source alone. |
| macrocosm-os__pretraining | Schema v0 has no dedicated field for softmax temperature (0.01); recorded in notes/per_miner_state. |
| macrocosm-os__pretraining | Active vs documented divergence: archived validator burns 100% to owner UID while the README documents the loss/win-rate mechanism. Schema has no first-class 'mechanism status: active|dormant' field. |
| macrocosm-os__prompting | Exact per-competition incentive_weight values and the live burn_factor (orchestrator-owned, not in repo). |
| macrocosm-os__prompting | The recipient address/UID of burned emissions and the precise burn fraction beyond the 0.9 base_burn_rate floor. |
| macrocosm-os__prompting | Cross-competition aggregation: how per-competition leaderboards combine into the single per-UID global weight returned to validators. |
| macrocosm-os__prompting | Decay rate / min weight floor: no such constant present in this repo. |
| macrocosm-os__prompting | Whether any LLM/reference-model judging is used (none found in this repo; competitions are deterministic simulations/games). |
| mode-network__synth-subnet | subnet.netuid: not stated in code or README; config default --netuid=1 is a placeholder, not the live netuid. |
| mode-network__synth-subnet | aggregation.decay_rate: README mentions an exponential decay function, but extracted code uses a flat windowed rolling average with no decay-rate literal. |
| mode-network__synth-subnet | aggregation.min_weight_floor: no minimum-weight floor literal found in extracted code. |
| mode-network__synth-subnet | burn_allocation: no burn / owner-take found in extracted reward or weight-setting code. |
| mode-network__synth-subnet | README emission formula states beta=0.1 while prompt_config sets softmax_beta=-0.1 (low) / -0.2 (high); sign/per-competition values differ between docs and code. |
| sportstensor__sn41 | scoring_signals[].weight: no fixed scalar weights exist; ROI vs qualified-volume tradeoff is set by the CVXPY optimizer's objectives/duals, not a constant. |
| sportstensor__sn41 | aggregation.burn_allocation.fraction: burn is a per-epoch residual (1.0 - allocated + general-pool weight), not a literal constant. |
| sportstensor__sn41 | aggregation.min_weight_floor: no per-miner minimum weight floor found; EXCESS_MINER_MIN_WEIGHT=0 applies only to the (disabled) excess-miner UID. |
| sportstensor__sn41 | subnet 'sports prediction' framing: README frames trades as predictions evaluating accuracy/timing/informational value, but the implemented scoring uses realized PnL/ROI and qualified volume, not an explicit accuracy or closing-line-value (CLV) metric. |
| sportstensor__sn41 | task.submission_format: no per-prediction CLV/closing-line scoring is implemented in this snapshot despite the prompt's expectation; scoring is profitability-based. |
| taoshidev__proprietary-trading-network | /aggregation/burn_allocation/fraction: dynamic (1.0 - sum of weights), no fixed literal constant exists. |
| taoshidev__proprietary-trading-network | Exact metric_kind for calmar/sharpe/sortino/omega/statistical_confidence has no schema enum (used 'other'); they are zero-weighted in current config so do not affect emissions. |
| taoshidev__proprietary-trading-network | Subaccount/entity buckets (SUBACCOUNT_CHALLENGE/FUNDED/ALPHA, ENTITY) belong to a separate entity-miner system not fully traced here; included in status_values from the enum but their full ladder is not mapped. |
| taoshidev__proprietary-trading-network | Precise on-chain weights_rate_limit / tempo hyperparameter not found in repo (set off-chain); only the 5-minute compute refresh and weekly payout target are cited. |
| tensorplex-labs__dojo | scoring_signals weights: per-signal weighting is not explicit — task scores are summed raw per UID with no per-signal multiplier; left null. |
| tensorplex-labs__dojo | min_weight_floor / decay_rate: no decay or weight floor found in the read scoring/weight code; left null. |
| tensorplex-labs__dojo | Exact PvP discriminator scoring (1/totalDiscriminators regardless of vote) vs the doc-comment claim of -1 for trap: trap doc-comment says -1 but TrapPenalty constant is -0.4; code uses the -0.4 constant, so the -0.4 value is authoritative. |
| tensorplex-labs__dojo | VALIDATOR/PvV reference output trust model: classified as crowd, but the validator-provided output in PvV acts as a quasi-oracle reference; schema trust_model lacks a precise fit. |
| tensorplex-labs__dojo | Tempo / commit-reveal period are read from on-chain subnet hyperparams at runtime, not constants in repo — actual numeric tempo unknowable from source. |
| v0idai__SN106 | /aggregation/decay_rate: EMA_ALPHA default is 0.3 in validator/index.ts but 0.8 in docs/TECHNICAL_IMPLEMENTATION.md; it is config-driven (CONFIG.VALIDATOR.EMA_ALPHA) and only used in the inactive reference path, so left null rather than commit to a constant. |
| v0idai__SN106 | scoring_signals/weight: individual signal weights are not numeric coefficients; score is a multiplicative composite (widthPenalty * centerWeight * liquidity) with no per-signal weight, so weights left null. |
| v0idai__SN106 | min_weight_floor: no explicit floor; EMA_EPSILON thresholds tiny weights to 0 but is a config value with no literal in source. |
| v0idai__SN106 | reserved-share constants: poolWeights default signature uses 0.85/0.15 (matching index.ts call), but the function default header and docs cite 0.25; only the index.ts call-site values (0.85 subnet-0, 0.15 subnet-106) are the actually-passed constants. |
| v0idai__SN106 | Active-vs-reference ambiguity: runValidator (full burn) is the invoked entry point; runValidatorWithEmissions (position scoring) is shipped but never called. Whether burn is a temporary launch state or permanent is not stated in source. |

## Extension usage (novelty the schema didn't model)

| extension pointer | repos |
|---|---|
| `/task/extensions` | macrocosm-os__finetuning, sportstensor__sn41 |
| `/extensions` | bigideaafrica__polaris |
| `/aggregation/extensions` | macrocosm-os__finetuning |
| `/ground_truth_sources/0/extensions` | sportstensor__sn41 |
| `/per_miner_state/extensions` | v0idai__SN106 |

## Possibly dead optional sub-objects (absent across ALL instances)

_None — every optional top-level sub-object was used at least once._
