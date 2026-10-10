# FVG creation-time movement-context empirical slice — V1

**Status:** build-only protocol and software; not accepted, not independently audited, and not empirical market evidence. No owner files were available in Arena or run here. This is not a trading rule, signal, strategy, or accepted market model.

## Question, unit, and limits

For **every** Stage4B2 normalized FVG creation entity, compare the two separate continuous outcomes of the next exact UTC hour's observed OHLC path against the creation row's published close. The descriptive question is whether a fixed, joint block of factual movement context available at creation reduces each target's out-of-time ordinary-least-squares RMSE relative to the same FVG's creation-time fields alone.

The unit is one Stage4B2 `FVG_CREATED` entity. Every such entity is retained in `candidate_context.csv` and `excursion_outcomes.csv`, including candidates with missing context, an unavailable boundary, gaps, right-censoring, or no post-decision rows. Only rows meeting the frozen complete-case outcome and feature rules enter the numerical comparison.

For a positive creation close `C`, the targets are `(max observed high in (creation, creation + 1 hour] - C) / C` and `(min observed low in (creation, creation + 1 hour] - C) / C`. They are not first-touch labels, success/failure labels, FVG-importance scores, trade results, or inferred market episodes. The requested endpoint is the exact UTC timestamp of the creation row plus one elapsed hour; no nearest-row substitution or “60 later rows” approximation is used.

This tests a fixed descriptive comparison, not a causal effect. A lower M1 RMSE is only a result on the specified case set. It does not establish predictive validity, market theory, ICT support, intent, trading value, or independent evidence. Price-derived M1 fields are correlated representations and are assessed as one joint block, not independent evidence or a field-ranking exercise.

## Existing interfaces and evidence boundaries

The command-line route uses these existing public interfaces:

1. `load_binance_spot_klines` from `trading_system.sources.binance_spot_kline_ohlc_source`, with `SourceArtifactIdentity`, the exact `BINANCE_SPOT_PUBLIC_DATA_KLINES_1M_V1` schema contract, and the source artifact's SHA-256. Its canonical OHLC index is the bar-completion time (`open_time + 1 minute`). Interior gaps are preserved (`require_full_coverage=False`) and counted, not filled. The loader validates format and declared period; it does **not** authenticate who supplied or downloaded the file.
2. `MarketObservationTimeline.seal` / `verify` to bind the exact caller-supplied canonical rows. This is an integrity binding, not trusted-source authentication.
3. Stage4B2 `build_fvg_surface` and its `normalized_entity_frame` / `normalized_event_frame`. Only structure-independent FVG creation entities/events are the candidate source. No post-creation lifecycle event is a predictor.
4. Stage4A `build_volatility_surface`, restricted to the actual `VOLATILITY` domain and its seven published output columns. No session or proxy-flow domain is added.
5. Stage4C `build_htf_scale_surface` with explicit `HtfScaleSpec("H1", 1 hour)` and a one-minute UTC `CadenceGridContract` fixed to epoch `1970-01-01T00:00:00Z`; already-built surfaces with a different cadence identity are rejected. The as-of projected completed raw H1 OHLC, coverage, projectability, and `close_batch_order_unknown` metadata are retained. A same-timestamp LTF/HTF close is not ordered by this runner.
6. MUF S1's public `CausalObservationStream` and `PublishedOhlcBarFact`, with the actual `PRICE_PATH_SCHEMA` and public descriptor identities. S1 grid-dependent descriptors remain `NOT_CONFIGURED` because no S1 `DeclaredGrid` is supplied. The stream is used for factual completed-row / observation-adjacent measurements only; this does not add an episode, anchor, segment, or narrative.
7. Outcome checks use the public trajectory `build_trajectory_window`, `decision_close_excursion_reference`, and `derive_excursion_view` contracts as the parity oracle. The batch extractor is parity-tested on complete, gapped, source-final-row-censored, and dataset-end-censored paths. An absent in-range boundary is not approximated; the public query API rejects the unavailable key.

The experiment entrypoints are `run_from_binance_csv(csv_path, identity, development_cutoff_utc, output_dir)` for the offline file route; `build_experiment(market_history, source_identity, source_file_sha256, development_cutoff_utc, timeline_id)` for shared timeline/surface construction; `build_experiment_from_surfaces(...)` for already-built public surfaces and tests; and `write_outputs(bundle, market_history, output_dir)` for timeline-verified output. Direct build calls default to caller-supplied/unverified source metadata unless the optional `source_validation` adapter result is supplied; `write_outputs` verifies the sealed timeline, not provider origin.

The experiment records source identity, source contract and validation state, full producer/surface identities, candidate keys, source/timeline hashes, missingness, and experiment-specific ordered prefix-chain hashes. The prefix-chain hashes are **not** represented as native Stage4 prefix hashes. Full-file, timeline, and full-surface identities may change when later rows are appended; they are provenance identities, not creation-time predictors. Candidate as-of context hashes are tested for prefix invariance under future append.

## Frozen information sets

**M0 — creation-time FVG information** (the exact predictor list is stored in `protocol.json`):

- FVG direction as a numeric indicator;
- creation-row close;
- FVG midpoint distance from that close, divided by the close;
- Stage4B2 gap-width fraction, gap-width percentile and gap-width history count;
- middle-candle body fraction and signed body fraction.

Raw zone bounds, midpoint, width, origin/middle/creation positions, creation `InformationKey`, and same-information-batch ambiguity are also retained as non-predictor fields. Redundant geometry is not added as duplicate regressors. The exact M0 field names are `fvg_is_bullish`, `fvg_creation_close_price`, `fvg_midpoint_distance_fraction`, `fvg_gap_width_fraction`, `fvg_gap_width_percentile`, `fvg_gap_width_history_count`, `fvg_middle_body_fraction`, and `fvg_middle_signed_body_fraction`.

**M1 — M0 plus one fixed joint context block:**

- **MUF S1:** signed observation-adjacent close step divided by creation close; absolute observation-adjacent close step divided by creation close; cumulative observed close-path length divided by creation close; running high and low distances from creation close; net close displacement from the first input-stream close divided by creation close; and accepted observation count. S1 `observed_close_path_length` is over accepted close observations, not a reconstructed intrabar path or guaranteed continuous path. Running extrema and net displacement use the input-stream prefix from the dataset start, not a new event/episode origin. First-observation movement fields carry explicit missing states. Grid-specific path length and grid bar count remain not configured.
- **Stage4A VOLATILITY:** normalized true range, true-range percentile, normalized TR change, and expansion percentile. All seven Stage4A volatility values—including raw true range and history counts—and each field's missing state are retained in the candidate artifact.
- **Stage4C completed H1:** completed bucket open, high, low, and close, each expressed relative to creation close. Completed-bucket timestamp, source/grid coverage counts/status, as-of projectability, and same-batch ambiguity are retained as metadata.

The exact M1 additions are `s1_close_step_fraction`, `s1_close_path_step_fraction`, `s1_observed_close_path_length_fraction`, `s1_running_high_distance_fraction`, `s1_running_low_distance_fraction`, `s1_sum_close_displacement_fraction`, `s1_bar_count_observed`, `stage4a_normalized_true_range`, `stage4a_true_range_percentile`, `stage4a_normalized_tr_change`, `stage4a_expansion_percentile`, `h1_open_relative_to_creation_close`, `h1_high_relative_to_creation_close`, `h1_low_relative_to_creation_close`, and `h1_close_relative_to_creation_close`.

Every predictor is read at the same creation completed-row key. `same_information_batch_order_unknown` is preserved; neither OHLC intrabar chronology nor an ordering within an LTF/HTF close batch is invented.

## Fit and evaluation protocol

- Fixed unregularized OLS (`numpy.linalg.lstsq`) with an intercept; no feature selection, interactions, tuning, regularization, ML, or coefficient interpretation.
- Feature means and population standard deviations are fitted on development rows only. Zero standard deviation uses scale one. Rank or sample deficiency yields an explicit inconclusive state; the feature set is not changed to force a fit.
- A training case must have creation before the caller-supplied UTC cutoff, an exact one-hour endpoint, a complete contiguous uncensored outcome, complete M1 features, and an outcome ending **strictly before** the cutoff.
- An evaluation case must have creation at/after the cutoff, the same complete M1 feature set, and an exact contiguous uncensored one-hour outcome. Pre-cutoff outcomes reaching/crossing the cutoff stay in the artifacts but enter neither role.
- M0 and M1 always use identical training and evaluation candidate IDs. No feature imputation occurs. Training, evaluation, and combined case-set hashes are recorded.
- For each target separately, report M0 RMSE, M1 RMSE, and M1-minus-M0 RMSE. No combined score, p-value, standard error, confidence interval, or IID assumption is produced. Observed-window overlap pairs and maximum concurrency are counted separately for training, evaluation, and combined model cases; these are dependence descriptions, not an uncertainty estimator.

A one-month May run is only a within-file temporal diagnostic. A later part of the same file is not an independent holdout, especially if outcomes have already been inspected. The owner-reported 44,640 one-minute bars / 18,560 FVG creations are **unverified here and not Arena-accessible input**.

## Missing, boundary, censoring, and inconclusive states

The runner looks up the exact `creation_time + 1 hour` timestamp. It preserves partial observed paths and does not shift a horizon to a neighboring timestamp.

| Situation | Recorded behavior | Enters OLS? |
|---|---|---:|
| Exact boundary observed before the dataset's final row, with one-minute deltas throughout | `HORIZON_BOUNDARY_OBSERVED`, `COMPLETE`, `OBSERVED_TO_REQUESTED_END`, `CONTIGUOUS_UNDER_DECLARED_STEP` | Yes, if all M1 fields are available and split rules pass |
| Exact boundary is the source's final row | Preserve the observed excursion; `COMPLETE` but `RIGHT_CENSORED` under the trajectory source-end contract | No |
| Requested boundary is after the final row | Preserve rows through the last source row; `RIGHT_CENSORED_AT_DATASET_END`, explicit future boundary key, `INCOMPLETE` | No |
| Requested time is inside the observed time range but the exact timestamp is absent | `IN_RANGE_BOUNDARY_UNOBSERVED`, no substitute key, observed path only before the missing timestamp | No |
| Exact boundary exists but the interval contains a timestamp gap/cadence deviation | Preserve observed excursion and all `coverage_issues_json`; `GAPS_OR_CADENCE_DEVIATION` | No |
| No rows follow the decision | Preserve candidate; `NO_POST_DECISION_ROWS`; excursion values unavailable | No |
| One or more M1 fields are unavailable | Candidate/field retained with null value and its `__state`; no imputation | No; same candidate is excluded from both M0 and M1 |
| No eligible training or evaluation cases | `INCONCLUSIVE_NO_TRAINING_OR_EVALUATION_CASES` with counts and empty case-set hashes | No fit |
| OLS design is rank/sample deficient | `INCONCLUSIVE_ONE_OR_MORE_MODEL_DESIGNS`; target/model diagnostics explain deficiency | No RMSE comparison for the deficient target |
| Source CSV, timeline, or surface validation fails | Adapter/source exception or `MovementContextExperimentError`; no valid output bundle is written | Blocked / not run |

`scoreable_under_frozen_protocol` and `model_target_state` describe outcome-path eligibility; `_fit_comparison` additionally requires every M1 feature state to be `AVAILABLE`. A zero-candidate population still emits an empty, stable candidate schema and an inconclusive comparison; it is not reported as evidence of no relationship.

## Output schemas and interpretation

All files are written to a caller-selected **new or empty directory outside the repository**. `write_outputs` re-verifies the supplied output market frame against the sealed experiment timeline and refuses a non-empty destination.

- **`candidate_context.csv` — one row per FVG creation entity.** Keys: `candidate_id` / `fvg_id`, `event_type`, direction, origin/middle/creation positions, UTC creation time, and all public `InformationKey` coordinates. Raw creation geometry and event ambiguity are retained. Source fields include the file SHA-256, caller-declared symbol/market/period, exact source schema contract, adapter-validation state, and an explicit `source_origin_authenticated=false`. Producer fields include Stage4B2 surface/result/entity/event identities, Stage4A contract/configuration identities, Stage4C H1 scale/cadence identities, and MUF S1 source/schema/descriptor identities. `market_prefix_chain_sha256`, `fvg_creation_prefix_chain_sha256`, `s1_prefix_chain_sha256`, `stage4a_prefix_chain_sha256`, and `stage4c_prefix_chain_sha256` are experiment-local as-of row chains; `candidate_context_sha256` binds the candidate key, fixed feature values/states, and those chains. Every model field has a paired `__state`; all seven Stage4A volatility fields, S1 raw descriptors/grid states, and Stage4C H1 OHLC/coverage/projectability metadata are also retained.
- **`excursion_outcomes.csv` — one row per candidate.** Its columns are `candidate_id`, `decision_position`, `decision_time_utc`, `requested_horizon_end_utc`, `requested_end_bar_position`, `requested_end_key_state`, `requested_end_key_timeline_id`, `requested_end_key_event_time_utc`, `actual_end_position`, `actual_end_time_utc`, `path_start_position_exclusive`, `path_start_position_inclusive`, `path_end_position_inclusive`, `path_row_count`, `path_status`, `horizon_completion`, `censoring_state`, `coverage_assessment`, `coverage_issues_json`, `observed_value_state`, `observed_max_high`, `observed_min_low`, `observed_high_delta_from_creation_close`, `observed_low_delta_from_creation_close`, `observed_high_excursion_fraction`, `observed_low_excursion_fraction`, `model_target_state`, `high_excursion_fraction`, `low_excursion_fraction`, `max_high_position`, `min_low_position`, `source_path_slice_sha256`, `path_id`, `outcome_id`, `horizon_policy_sha256`, `scoreable_under_frozen_protocol`, `development_cutoff_utc`, and `model_split_state`. The observed excursion is preserved even when a gap/censoring rule makes the model target non-scoreable.
- **`observed_paths.csv` — one row for every observed OHLC row in each candidate's post-decision path.** Columns are `candidate_id`, `path_id`, `bar_position`, `event_time_utc`, `open`, `high`, `low`, `close`, and `intrabar_high_low_order`. The last field is `UNPROVEN_FROM_PUBLISHED_OHLC`. Overlapping rows are intentionally repeated per candidate so paths are reconstructable.
- **`protocol.json`** contains the frozen question, feature names/semantics, one-hour horizon, split, estimator, source/contract/surface identities, and caveats. **`comparison.json`** contains case hashes, per-target model diagnostics/RMSE, split counts, and overlap accounting. **`summary.json`** contains candidate/outcome/source coverage counts and status. **`OUTPUT_MANIFEST.sha256`** hashes the six preceding output files (not itself).

A negative `M1_MINUS_M0_RMSE` means lower descriptive evaluation RMSE on that fixed case set; a positive value means higher. Neither direction licenses a predictive-validity, causal-effect, market-theory, or trading claim. `DESCRIPTIVE_TEMPORAL_COMPARISON_NOT_INDEPENDENT` only means both specified OLS fits produced those descriptive RMSE values.

The direct Python builders accept caller-supplied frames and hashes for tests/audit; they mark that path `CALLER_SUPPLIED_FRAME_NOT_VERIFIED_BY_BINANCE_ADAPTER`. The CLI route records `BINANCE_KLINE_SCHEMA_AND_DECLARED_PERIOD_VALIDATED_NOT_ORIGIN_AUTHENTICATED`. In either route, the source origin is not authenticated and a timeline seal is not provider authentication.

## Offline Windows PowerShell command

Use a local checkout with the project's declared Python dependencies installed. The input is the official-format 12-column headerless Binance Spot 1m kline CSV. For May 2026, the declared period is inclusive `open_time` 2026-05-01 00:00 UTC through exclusive 2026-06-01 00:00 UTC; the final expected candle completes at 2026-06-01 00:00 UTC.

```powershell
Set-Location "C:\work\TRADING-BOT\project\trading_project"
$env:PYTHONPATH = (Resolve-Path ".\src").Path
python -m trading_system.research.trajectory.movement_context_empirical `
  --csv "C:\market-data\BTCUSDT-1m-2026-05.csv" `
  --symbol BTCUSDT `
  --period-start-utc "2026-05-01T00:00:00Z" `
  --period-end-utc "2026-06-01T00:00:00Z" `
  --development-cutoff-utc "2026-05-21T00:00:00Z" `
  --output-dir "D:\research\fvg-movement-context\btc-may-2026-v1"
```

The program is offline: it does not download data or contact an exchange. Gaps are reported, not filled. Choose an output directory outside the repository; non-empty directories are refused.

## Software tests, seals, and independent audit

The focused test file is `tests/test_movement_context_empirical.py` (12 tests). Its synthetic fixtures establish software behavior only, never empirical usefulness. The tests cover complete and zero-candidate Stage4B2 populations; future-append as-of prefix invariance; public excursion parity for complete, gapped, final-row-censored, and dataset-end-censored paths; rejection of an absent in-range endpoint; gap/censor/no-post-row states; same M0/M1 cases and explicit rank-deficiency behavior; overlap counting; surface/timeline and frozen-HTF-cadence mismatch; output timeline verification, deterministic manifest bytes, and overwrite refusal; and the offline CSV-loader route's validation metadata without origin authentication. All 12 focused tests pass. The focused tests plus existing Stage4A, Stage4B2, MUF S1 price-path, and Binance kline-adapter tests also pass in the validation environment.

The full existing suite does **not** pass under the available Python 3.11 / pandas 3.0.6 / NumPy 2.4.6 environment. Failures include existing timestamp-resolution/dtype mismatches (for example, seconds or microseconds where sealed tests expect nanoseconds), broad eligibility/research-dataset/manifest compatibility failures, and failures in 12 direct Stage4C tests, including tests that receive empty H1 buckets from microsecond-resolution test indexes. The new runner normalizes its own input to nanoseconds before Stage4C; no sealed Stage4C source or accepted test was changed to address these broader pre-existing environment failures.

No closed producer, existing accepted source/test seal, release record, or project `MANIFEST.sha256` entry was changed. This slice is not accepted or sealed; an additive main-manifest/release update is deferred until a separately authorized audit/acceptance. Existing accepted source/test records remain the authority for the reused modules.

Before interpreting any owner-data result, an independent auditor should:

1. verify the current branch, base/implementation commit, unchanged accepted release seals, and `sha256sum -c MANIFEST.sha256`; hash the new source/test/docs files separately because this build-only slice has no accepted release seal;
2. independently inspect the listed public APIs, feature transformations, source adapter checks, same-batch flags, exact boundary logic, missingness, and lifecycle exclusion;
3. reproduce input file, candidate, outcome, path, and output-manifest hashes without treating a supplied source hash/timeline seal as origin authentication;
4. independently check the batch excursion implementation against public trajectory windows/views, including the exact boundary, gaps, final-row censoring, dataset-end censoring, and absent in-range boundary;
5. verify temporal eligibility and equal M0/M1 case-set hashes; inspect training/evaluation overlap counts without IID-based inference;
6. treat May-only results as exploratory. A predictive-validity claim would need a genuinely untouched independent dataset and a separately audited dependence/uncertainty protocol.

MUF S7/S8/S9 are not used or altered. This slice does not close `RESEARCH-DEBT-023/024/025`, introduce a general dependency graph, or add market episodes, movement segmentation, swing/structure/liquidity/order-block logic, execution, fills, PnL, or a strategy.
