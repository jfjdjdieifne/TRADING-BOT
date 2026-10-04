# Current Authoritative Validation — Through Module 6.2A-4 V1 Stage 3 Closure

## Collected tests

```text
tests/test_absorption.py: 18
tests/test_adaptive_confluence_calibration.py: 27
tests/test_adaptive_confluence_calibration_integration.py: 2
tests/test_binance_executed_flow_source.py: 6
tests/test_binance_spot_kline_ohlc_source.py: 20
tests/test_binance_spot_minute_facts_source.py: 19
tests/test_causal_adaptive_smoothing.py: 37
tests/test_causal_htf.py: 10
tests/test_causal_percentile.py: 24
tests/test_confluence_matrix.py: 9
tests/test_dealing_range.py: 11
tests/test_dynamic_volatility.py: 20
tests/test_evidence_family_reasoning.py: 34
tests/test_evidence_family_reasoning_integration.py: 1
tests/test_evidence_family_reasoning_v1_1.py: 30
tests/test_evidence_vector.py: 54
tests/test_fvg.py: 16
tests/test_liquidity_map.py: 20
tests/test_narrative.py: 53
tests/test_order_blocks.py: 12
tests/test_research_dataset_builder.py: 22
tests/test_research_dataset_integration.py: 1
tests/test_research_eligibility.py: 25
tests/test_research_eligibility_integration.py: 1
tests/test_research_hashing.py: 18
tests/test_research_information_time.py: 16
tests/test_research_manifest_identity.py: 19
tests/test_research_outcome_integration.py: 2
tests/test_research_outcome_observer.py: 55
tests/test_research_visibility.py: 44
tests/test_session_context.py: 26
tests/test_structural_breaks.py: 25
tests/test_swing_detector.py: 28
tests/test_swing_sequence.py: 31
tests/test_trajectory_contract.py: 18
tests/test_trajectory_stage2.py: 36
tests/test_trajectory_stage3.py: 81
tests/test_trajectory_stage4a.py: 72
tests/test_trajectory_stage4b1.py: 37
tests/test_trajectory_stage4b2.py: 37
tests/test_trajectory_stage4c.py: 36
tests/test_volume_delta.py: 19
TOTAL: 1072
```

## Exact pytest result

```text
........................................................................ [  6%]
........................................................................ [ 13%]
........................................................................ [ 20%]
........................................................................ [ 26%]
........................................................................ [ 33%]
........................................................................ [ 40%]
........................................................................ [ 47%]
........................................................................ [ 53%]
........................................................................ [ 60%]
........................................................................ [ 67%]
........................................................................ [ 73%]
........................................................................ [ 80%]
........................................................................ [ 87%]
........................................................................ [ 94%]
................................................................         [100%]
```

```text
1072 collected
1072 passed
exit code 0
```

## Status

```text
Layers 0–5: CLOSED
D1/D1.1: PRELIMINARY SOURCE AUDIT — ACCEPTED / APPLIED
Module 6.1A V1.3: CLOSED
Module 6.1B V1.2: CLOSED
Module 6.2A-0 V1.2: CLOSED
Module 6.2A-1 V1.2: CLOSED
Module 6.2A-2 V1: CLOSED
Module 6.2A-3 V1.1: CLOSED
Module 6.2A-4 V1 Stage 1: CLOSED
Module 6.2A-4 V1 Stage 2: CLOSED
Module 6.2A-4 V1 Stage 3: CLOSED
Module 6.2A-4 V1 Stage 4A: CLOSED
Module 6.2A-4 V1 Stage 4B-1: CLOSED
Module 6.2A-4 V1 Stage 4B-2: CLOSED
Module 6.2A-4 V1 Stage 4C-1: CLOSED
Module 6.2B-0 V1.2: CLOSED
Module 6.2B-1 V1.1: CLOSED
Binance Source Adapter V1: CLOSED
EXACT PERFORMANCE V2 + TEST-SUITE ACCELERATION (unified): CLOSED
MUF V1 S0 Core Contracts Foundation: CLOSED
6.2A-4 Stage 4C-2 HTF structure / MTF confluence: NOT STARTED
6.2C geometry / 6.2D execution / model / scorer / signals: NOT STARTED
QualificationObjective: NOT DEFINED
```

## Module 6.2B-0 closure boundary

Closure certifies within tested scope:

1. exact hypothesis-creation same-row `InformationKey` boundary;
2. rejection of prior/future rows and future semantic payload before use within the representable parent envelope;
3. exact revalidation of the CLOSED creation snapshot integrity hashes;
4. no current source upgraded to predictive `SUPPORT`;
5. explicit orthogonal semantic states and MTF directional-conflict preservation;
6. separate ACTUAL and PROXY epistemic classes;
7. three-state open-world provenance: certified shared, certified distinct, or not certified;
8. deterministic derivation kept orthogonal to provenance and co-derivation;
9. formula-faithful 6.1A availability lineage with COUNT_SUPPORT excluded from value parents;
10. formula-faithful CLOSED 5.2 MTF DAG without manifest-order inference;
11. no false statistical-independence admission (`included_for_independent_calibration=False` for all current records);
12. final record hash, family semantic hash, global semantic reasoning hash, and exact upstream storage hash separation;
13. canonical source-order-insensitive semantic identity;
14. stateless A→A, A→B→A, fresh-instance, prefix/future-history invariance, and full caller-input immutability;
15. reasoning firewall: no outcomes, model, scorer, geometry, or execution dependencies.

Closure does not certify:

- predictive support or edge;
- statistical independence or incremental predictive information;
- confluence strength or score;
- learned weights or calibration;
- qualification threshold or probability;
- preprocessing, model, estimator, classifier, or scorer;
- entity-level geometry adapter;
- entry, stop, target, fill, execution, or trade lifecycle;
- BUY/SELL signals or PnL/WIN/LOSS;
- overlapping-hypothesis dependence resolution.

## Module 6.2B-1 closure boundary

Closure certifies within tested scope:

1. TRAIN-only descriptive calibration/reference foundation;
2. authoritative CLOSED 6.2A-3 source-fold verification (full fold seal) before any TRAIN projection;
3. canonical TRAIN sample binding through CLOSED `_sample_id`;
4. authoritative B-0 reasoning re-analysis/membership for every admitted sample;
5. exact TRAIN raw feature row binding;
6. TEST/OOS descriptive-content firewall: TEST cannot alter TRAIN calibration content;
7. descriptive empirical CDFs labelled `TRAIN_EMPIRICAL_CDF_NOT_PROBABILITY`;
8. descriptive observation coverage labelled not semantic or predictive SUPPORT;
9. explicit NULL / SIMPLE / FULL baseline and FAMILY_ABLATION admission contracts;
10. chained experiment accounting with an external trusted-head boundary;
11. caller-reported OOS-access accounting explicitly NOT access-control proof;
12. separated source-fold provenance, TRAIN content identity, and final artifact identity;
13. public artifact verification recomputing all component/content/artifact hashes without TEST payload access;
14. ACTUAL/PROXY separation and UNKNOWN/UNAVAILABLE separation with no zero-fill or renormalization;
15. `DEPENDENCE_NOT_RESOLVED` for unresolved overlap/non-IID semantics;
16. no target-conditioned fitting while the objective is undefined.

Closure does not certify:

- predictive edge or predictive SUPPORT;
- feature importance or learned confluence weights;
- a qualification objective or threshold;
- probability or profitability;
- statistical independence or effective independent sample size;
- untouched OOS merely from caller-reported access count;
- geometry, entry/stop/target, execution/fills, signals, or PnL/WIN/LOSS;
- future live performance.

## Module 6.2A-4 Stage 1 closure boundary

Closure certifies within tested scope:

1. shared authenticated `MarketObservationTimeline` foundation with no per-hypothesis market duplication;
2. decision/outcome two-clock semantics: `observation_information_key` may precede `factual_available_at_information_key`, and visibility uses the available-at key;
3. decision anchor contains no future information and no future feature preselection;
4. creation bar excluded from the post-hypothesis path `(decision_batch, end_inclusive]`;
5. FACTUAL_EVENT vs STATE_OBSERVATION distinction, hash-bound;
6. deterministic as-of projection;
7. immutable prior as-of snapshots (later facts create new identities, never rewrite earlier ones);
8. shared timeline storage rather than per-hypothesis market copies;
9. OHLC source-resolution limitations (no intrabar chronology, no tick/L2 claims);
10. integrity sealing explicitly not integrity binding (not issuer authentication);
11. literal terminal lifecycle semantics with no success/profit interpretation;
12. canonical identities/hashing via the project serializer;
13. research/live firewall (no live module imports the trajectory package).

Closure does not certify:

- actual domain trajectory observations (liquidity / OB / FVG / flow / MTF ingestion);
- path descriptors;
- learning estimands;
- predictive edge, probabilities, or any model/scorer;
- geometry, entry/stop/target, execution, or profitability.

## Module 6.2A-4 Stage 2 closure boundary

Closure certifies within tested scope:

1. per-bar favorable/adverse excursion formulas per CLOSED 6.2A-1 orientation;
2. running maximum favorable/adverse with strict-greater tie preservation (first occurrence);
3. SAME_INFORMATION_BATCH_ORDER_UNKNOWN when both extremes in same OHLC bar;
4. close displacement = (close - ref) / ref, bar offset = bar_position - decision_bar_position;
5. new-running-extreme flags, extreme price/position/InformationKey capture;
6. shared timeline architecture preserved (no per-hypothesis market copy);
7. consumed CLOSED 2.1A→2.1B→2.1C structure chain with prefix causality (market_history truncated to interval end);
8. swing origin < confirmation enforced, confirmation is factual-available-at;
9. full taxonomy from CLOSED contracts: SWING, SEQUENCE, BREACH, BREAK, STATE transition;
10. consumed CLOSED 6.1B lifecycle ledger with literal terminal states only: CONTRADICTED, SUPERSEDED, OBSERVED_DIRECTION_ESTABLISHED;
11. no second state machine, no price-inferred terminal;
12. mature interval boundary at terminal factual-availability, unresolved as-of returns empty;
13. SUCCESS/WIN/LOSS/PROFIT rejected as terminal states;
14. two-clock semantics, creation bar exclusion, input immutability, determinism, firewall preserved.

Closure does NOT certify:

- true_range / normalized true range / volatility trajectory;
- liquidity / OB / FVG / dealing range / volume delta / absorption trajectory;
- session / HTF / MTF trajectory;
- censor-series implementation (Stage 3);
- path descriptors, quality, efficiency;
- learning estimands;
- predictive model, scorer, weights, probabilities;
- geometry, entry/stop/target, execution, PnL;
- WIN/LOSS/SUCCESS interpretation.

## Module 6.2A-4 Stage 3 closure boundary

Closure certifies within tested scope:

1. immutable mature terminal snapshot and immutable right-censored-as-of snapshot;
2. append-only as-of snapshot series (strictly increasing research-as-of, prior snapshots unchanged);
3. CLOSED 6.2A-1 as authoritative for mature-vs-censored classification, `factual_outcome_id`,
   `research_snapshot_id`, terminal state, and terminal position;
4. CLOSED Stage 2 as authoritative for the PRICE / STRUCTURE / LIFECYCLE trajectory prefix;
5. complete Stage 2 public-result deterministic-equivalence verification
   (`STAGE2_PUBLIC_RESULT_EQUIVALENCE_V1`) over `price.price_bars` + price final scalars +
   `structure.structure_events` + `lifecycle.lifecycle_events` + lifecycle terminal fields +
   envelope count + envelope prefix hash;
6. envelope-context verification: every supplied and reconstructed envelope proven to belong to
   the expected timeline / timeline_hash / anchor / interval (with CLOSED `envelope.verify()`);
7. separation of terminal factual availability from research as-of (two distinct InformationKeys);
8. compact snapshot identity (hashes/counts only; no raw market, no full envelope tuple, no
   duplicated running payloads);
9. reconstruction / derivation-witness semantics;
10. origin preserved exactly from the supplied Stage 2 artifact's own embedded lifecycle rows
    (Int64 position, not a manufactured InformationKey);
11. literal terminal states only (CONTRADICTED, SUPERSEDED, OBSERVED_DIRECTION_ESTABLISHED);
12. right-censor semantics `RIGHT_CENSORED_AS_OF_BOUNDARY` only, matching CLOSED 6.2A-1;
13. positional and time-indexed timelines (timezone-aware, DST/irregular UTC), cross-timeline
    rejection, same-information-batch determinism;
14. determinism (A→A, A→B→A, fresh-instance), caller-input immutability, frozen snapshots;
15. research/live firewall (no live module imports Stage 3).

Closure does NOT certify:

- the historical generating-input identity of a supplied Stage 2 artifact
  (`reconstruction_swing_policy_hash`, `reconstruction_ledger_seal`,
  `stage2_reconstruction_binding_hash` are derivation witnesses only; generating-input
  provenance remains NOT CERTIFIED / UNVERIFIABLE);
- Stage 4 trajectory domains (volatility / liquidity / OB / FVG / dealing range / orderflow /
  session / HTF / MTF trajectory);
- path descriptors;
- learning estimands;
- hazard / survival model, competing-risk probabilities, or any censor estimand;
- predictive model, scorer, weights, probabilities, confluence scores;
- geometry, entry/stop/target, execution, fills, trade lifecycle;
- PnL, WIN/LOSS/SUCCESS semantics, signals;
- fixed horizons;
- statistical independence or overlapping-hypothesis dependence resolution.

## Module 6.2A-4 Stage 4A closure boundary

Closure certifies within tested scope:

1. factual shared per-bar market-state trajectory for Dynamic Volatility, Session Context,
   Volume Delta / Order Flow in OHLCV_PROXY mode, and Absorption / Response in OHLCV_PROXY mode;
2. shared domain surfaces computed once per exact domain-surface identity, independent of
   hypothesis identity (not merely per timeline);
3. compact hypothesis prefix binding with no per-hypothesis row duplication;
4. complete public-result hashing over the full CLOSED factual output per domain;
5. surface self-integrity verification: recomputes public-result hash and surface identity from
   current content; rejects stale-identity / mutable-DataFrame tampering;
6. exact output-schema verification from the CLOSED contract + frozen config payload;
7. reconstruction / derivation witness semantics (NOT historical generating-input provenance);
8. legal InformationKey boundary validation (positional and time-indexed); BAR_PRE_CLOSE rejected
   for completed-bar facts; timestamp consistency enforced for time-indexed boundaries;
9. no post-boundary projected facts; future-prefix invariance under legally rebuilt future surfaces.

Closure does NOT certify:

- ACTUAL_AGGRESSOR order flow or ACTUAL absorption (the CLOSED MarketObservationTimeline does not
  seal buy_volume/sell_volume and no authoritative external factual-availability contract exists;
  ACTUAL is rejected with no fallback);
- OHLCV_PROXY == ACTUAL (PROXY is completed-bar OHLCV geometry only);
- predictive quality for PROXY or ACTUAL;
- historical generating-input provenance;
- Stage 4B (liquidity / OB / FVG / dealing range) or Stage 4C (HTF / MTF);
- descriptors, estimands, hazard/survival/competing-risk models;
- predictive model, scorer, weights, probabilities, confluence scores;
- geometry, entry/stop/target, execution, fills, trade lifecycle;
- PnL, WIN/LOSS/SUCCESS semantics, signals, predictive edge, fixed horizons;
- statistical independence or overlapping-hypothesis dependence resolution.

## Module 6.2A-4 Stage 4B-1 closure boundary

Closure certifies within tested scope (the shared causal structure surface contract only):

1. one shared, hypothesis-independent structure surface from the CLOSED public chain
   2.1A → 2.1B → 2.1C;
2. complete public factual result of 2.1A + 2.1B + 2.1C bound by canonical component hashes and a
   composed public-result hash;
3. shared storage (one surface per surface identity) + compact hypothesis prefix binding;
4. factual availability governed by confirmation/event row, never origin; origin preserved as
   positional Int64, never a manufactured InformationKey;
5. compact prefix identity through a legal boundary T (full-surface identity changes on append,
   prefix identity preserved — verified on the real CLOSED chain);
6. boundary legality mirroring CLOSED Stage 1/Stage 4A;
7. self-integrity verification + supplied-vs-authoritative reconstruction comparison;
8. deterministic reconstruction witness semantics only.

Accepted limitations (NON-BLOCKING): (1) `verify_surface_integrity` provides internal
self-consistency for stored witness metadata; coherent witness-token forgery is not independently
disproven by self-integrity alone. (2) `verify_surface_matches_reconstruction` compares against a
supplied authoritative surface; it does not itself independently reconstruct the CLOSED chain.
(3) Passthrough market fields are reconstruction inputs bound through the CLOSED timeline seal; the
public-result hash covers the complete derived structure result. (4) `prefix_hash` is factual content
identity; complete binding carries surface/timeline/boundary identity.

Closure does NOT certify: historical generating-input provenance (NOT_CERTIFIED / UNVERIFIABLE);
Liquidity / OB / FVG / Dealing Range trajectory surfaces (Stage 4B-2); Stage 4C (HTF/MTF);
predictive usefulness, trading edge, profitability, or statistical independence; descriptors,
estimands, hazard/survival/competing-risk; model/scorer/weights; geometry/execution; PnL,
WIN/LOSS/SUCCESS.

## Module 6.2A-4 Stage 4B-2 closure boundary

Closure certifies within tested scope the four shared, hypothesis-independent factual
entity/lifecycle trajectory surfaces only:

1. Liquidity surface (CLOSED 2.2 consumed over Stage 4B-1): 23 derived bar columns + 16 event
   columns, 15 entities on the deterministic fixture;
2. Order-Block surface (CLOSED 4.1 over Stage 4B-1): 26 + 20, 14-column entity table, 7 entities;
3. FVG surface (CLOSED 4.2A, structurally independent — OHLC only, sealed market directly,
   `structure_surface_id=None` mandatory): 27 + 21 source event columns, 15-column entity table,
   50 entities; normalized event frame is 21 + same-information-batch ambiguity flag = 22;
4. Dealing-Range surface (CLOSED 4.2B over Stage 4B-1, original CLOSED 17-column range table):
   30 derived bar columns, 14 ranges;
5. schema authority from the concrete surface class plus local Final frozen CLOSED-output mirrors,
   with independent dynamic verification that builds the real CLOSED engines and rejects any
   added/dropped/reordered public column — a coherently recomputed hash cannot bypass it;
6. four-component factual prefix binding through T (derived bars + events <= T + entities at
   factual availability position + normalized events) with canonical reset_index treatment;
   prefix changes under pre-T fact mutation/removal and is invariant under legal post-T extension;
7. distinct immutable per-domain class identity (coherent cross-domain / cross-table / cross-class
   switching rejected); same-information-batch flags equal to literal duplicated(event_position);
   normalized entities traceable 1:1 to creation events (or the original range table for DR);
8. self-integrity verification, boundary legality mirroring CLOSED Stage 1/4A/4B-1
   (BAR_PRE_CLOSE rejected, cross-timeline rejected, positional/time-indexed correctness),
   intact research/live firewall, reconstruction/derivation-witness semantics only.

Consumed market passthrough verified as high/low/close (liquidity), OHLC (order block, FVG),
close (dealing range); none of the four engines consumes volume.

Accepted limitations (NON-BLOCKING): (1) a foreign column injected between the passthrough block
and the derived tail is accepted while tail append is rejected; hashing binds the derived tail and
exact event/entity/range tables, so no derived fact is forgeable through this channel; future
hardening may enforce exact whole-frame column equality. (2) Passthrough cells are bound through
the CLOSED timeline seal rather than re-hashed, as in Stage 4A/4B-1. (3) Reconstruction/mirror
equivalence is a derivation witness; historical generating-input provenance remains
NOT_CERTIFIED / UNVERIFIABLE. (4) Series.equals does not distinguish +0.0/-0.0 while content
hashing does; the deterministic fixture does not exercise signed zero. (5) The fixture generates
neither a DR rejection nor a far OB-retrieval restoration; those CLOSED paths are consumed but not
fixture-exercised.

Closure does NOT certify: Stage 4C (HTF/MTF future surfaces; NOT_IMPLEMENTED / NOT STARTED);
descriptors; estimands; hazard/survival/competing-risk; model/scorer/weights/probabilities;
QualificationObjective; predictive SUPPORT, statistical independence, incremental information,
predictive usefulness, trading edge, or profitability; geometry/entry/stop/target/execution/fills;
PnL, WIN/LOSS/SUCCESS, signals, fixed horizons. RESEARCH-DEBT-020..025 remain open.

## Module 6.2A-4 Stage 4C-1 closure boundary

Closure certifies within tested scope (the shared causal raw HTF observation surface, optional
declared-grid coverage metadata, and causal as-of projection only):

1. raw HTF observed OHLC surfaces: completed HTF bucket observations (time, open, high, low,
   close) consumed solely from the CLOSED public 5.1 aggregator as sealed observation truth;
   bucket truth accepted only under `COMPLETED_ROW_AVAILABLE`; `BAR_PRE_CLOSE` rejected; the LTF
   close and the HTF close are one information batch with `close_batch_order_unknown` set at
   exact-boundary visibility rows and no intra-batch chronology claim;
2. optional cadence-grid coverage metadata: completeness decided by timestamp-SET comparison
   against the declared grid (never counts alone) with `GRID_OBSERVATIONS_COMPLETE` /
   `GRID_OBSERVATIONS_MISSING` / `OFF_GRID_OBSERVATIONS_PRESENT` / `GRID_OBSERVATIONS_DEFECT_BOTH`
   / `GRID_COMPLETENESS_UNKNOWN`; without a declared grid coverage is
   `GRID_COMPLETENESS_UNKNOWN`; as-of rows carry `COVERAGE_UNAVAILABLE` (`UNAVAILABLE`) when no
   projectable grid status exists;
3. causal as-of projection through a legal boundary T inside the sealed timeline
   (`project_htf_scale_prefix`), TIME_INDEXED only (`POSITIONAL` is a contract error);
   exact-boundary visibility only at an observed LTF row whose timestamp equals the bucket close
   (interval `(start, end]`) on the SAME timeline and only in phase `COMPLETED_ROW_AVAILABLE`;
   cross-timeline and `BAR_PRE_CLOSE` boundaries rejected;
4. in-progress / not-yet-observed buckets and their high/low/close (including extreme spikes) are
   invisible until the close is observed; a feed gap delays projectability to the first observed
   as-of position at/after the close (a theoretically elapsed bucket is not visible before its
   first observed as-of row) — verified against real CLOSED 5.1 outputs;
5. `first_observed_asof_*` semantics = sealed-timeline projectability ONLY, with an explicit
   semantic-inflation guard
   (`SEALED_TIMELINE_PROJECTION_NOT_FEED_ARRIVAL_PROVENANCE_NOT_MARKET_AVAILABILITY`,
   `PROJECTABLE_AT_CLOSE_ONLY_IN_COMPLETED_ROW_AVAILABLE_SAME_TIMELINE`);
6. grid coverage claims completeness only of sealed observations versus the DECLARED grid — never
   feed completeness, never market completeness; a partial bucket remains honest observation
   truth with its observed rows and incompleteness metadata (no fill, no drop, no interpolation);
   no HTF volume and no HTF entities are consumed or produced;
7. derived-only frames with exact whole-frame schema equality to the declared derived schema (no
   market passthrough injection surface); sealed-timeline optional `volume` presence/absence
   never enters Stage 4C-1 derived content;
8. deterministic identity/hashing and live surface self-integrity verification (whole-frame schema
   equality + projection recomputation); deterministic reconstruction / derivation-witness
   semantics only.

Accepted limitations (NON-BLOCKING — recorded as constraints/debts; not fixed during closure):
(1) no `mirror_verification_hash` field exists (owner correction: a verification pass/fail is not
a hashable witness); (2) the observed-asof walk-back visibility gate is semantically redundant
over genuine CLOSED 5.1 outputs (external deletion probe) and is retained as defense-in-depth;
(3) sealed-timeline optional `volume` presence legitimately changes timeline identity but never
enters derived content; (4) coherent witness-token forgery remains outside self-integrity scope
(the accepted 4A/4B-1/4B-2 convention); (5) the first warm-up bucket is honestly declared
`GRID_OBSERVATIONS_MISSING` when incomplete under a declared grid; (6) `POSITIONAL` rejection is
by design (TIME_INDEXED only); (7) partial buckets are displayed with their observed rows plus
incompleteness metadata by design.

Closure does NOT certify: feed-arrival provenance (`projectable_asof` is sealed-timeline
projectability only) or historical market availability; feed completeness or market completeness;
historical generating-input provenance (NOT_CERTIFIED / UNVERIFIABLE); HTF structure; HTF
transitions; MTF confluence surfaces (Stage 4C-2; NOT STARTED); HTF volume or HTF entities;
predictive SUPPORT, statistical independence, incremental information; probability, weights,
QualificationObjective; model, scorer, calibration, geometry, entry/stop/target, execution, fills,
signals; PnL, WIN/LOSS/SUCCESS, fixed horizons; predictive usefulness, trading edge, or
profitability. RESEARCH-DEBT-020..025 remain open.

## Binance Source Adapter V1 closure boundary

Closure certifies within tested scope:

1. Binance published Kline OHLC source contract — the 12-column Binance kline artifact schema
   (Spot >= 2025-01-01 microsecond timestamp unit; `close_time = open_time + interval - 1us`;
   canonical minute mapping at `CLOSE_TIME`); Kline is a Binance-published bar fact;
2. Binance executed/initiated-flow source contract — `buy_volume` / `sell_volume` / `volume` from
   `buy_initiated_base_volume` / `sell_initiated_base_volume` / `base_volume` with
   `buy + sell == volume` exactness and single declared base-unit semantics
   (`EXECUTED_INITIATED_FLOW_FROM_BINANCE_SPOT`);
3. exact cross-witness (Decimal exactness, no tolerance — minute key, high, low, base volume,
   quote volume, taker-buy base, and taker-buy quote under literal-precision compatibility;
   `number_of_trades` / `agg_trade_count` declared `NON_COMPARABLE_PAIRS` and never compared;
   unambiguous O/C = EXPECTED_MATCH; ambiguous O/C never demanded equal);
4. `SOURCE_INCONSISTENCY` fail-closed (no skip, no silent repair, no coercion);
5. `CLOSE_TIME` semantics (canonical mapping at kline `CLOSE_TIME` only; build-list coverage maps
   half-open `[start, end)` from minute starts, never from closes);
6. generic source adapters (symbol/period/market-type generic; no instance hard-coding in
   production);
7. public reuse boundary for CLOSED 3.1/3.2 (consumed via public API only; 3.1/3.2 not modified);
8. `TIE_ORDER_CONTRACT = NOT_PROVEN` always; ambiguous open/close stays ambiguous
   (`open_ambiguous`/`close_ambiguous`); reconstructed open/close are deterministic convention
   witnesses only and never canonical OHLC; canonical O/C from the kline source exclusively.

Closure semantics: `ACTUAL` here means only `EXECUTED_INITIATED_FLOW_FROM_BINANCE_SPOT` per source
semantics. `ACTUAL` does NOT mean order-book truth, buying pressure, institutional activity, whale
activity, or market-wide flow. Historical generating provenance: NOT_CERTIFIED beyond the bound
source artifacts.

Closure does NOT certify:

- predictive edge;
- profitability;
- strategy;
- model;
- PnL;
- live availability.

RESEARCH-DEBT-020..025 remain open.

## EXACT PERFORMANCE V2 + TEST-SUITE ACCELERATION unified closure boundary

Closure certifies within tested scope (unified work unit: EXACT PERFORMANCE V2 +
TEST-SUITE ACCELERATION):

1. EXACT PERFORMANCE V2 — exact performance semantics preserved with zero semantic change
   (bitwise/behavioral equivalence within the accepted regression batteries); any output
   difference without a contract basis was a DO-NOT-SHIP stop condition;
2. TEST-SUITE ACCELERATION — test-suite runtime acceleration with identical test semantics
   (no test-logic change); the certified suite stands at 1072 collected / 1072 passed
   (up from the 1045 baseline; +27 tests inside the 5 accepted test files);
3. certified baseline: 1072 collected / 1072 passed / exit code 0;
4. external tool suite (field_runner `runner_tests`; outside this repository): 36 passed —
   context for the unified acceptance only, not part of this repository's test suite;
5. manifest pre-closure identity: 183 lines,
   sha256 `7796a73fc30fc311902d7ba8e033eb1699a73c5db10e824d02653fbdd1681587`,
   173 OK / 10 accepted stale / 0 missing; the 10 accepted stale entries were replaced in
   place with the accepted fingerprints (entry replacement, not deletion);
6. performance/equivalence gates: accepted equivalence/regression batteries pass; no
   semantic/causal/contract change;
7. accepted fingerprints (10 files: 5 source + 5 tests) sealed in
   `docs/releases/MODULE_EXACT_PERF_V2_TESTSUITE_ACCEL_UNIFIED_ACCEPTED_SRC_TESTS.sha256`;
   unified independent re-audit accepted both work units.

Closure does NOT certify: predictive support; edge; profitability; MUF correctness; Model;
Strategy; Signal; PnL. RESEARCH-DEBT-020..025 remain open.

## MUF V1 S0 closure boundary

Closure certifies within tested scope (core contracts foundation):

1. **immutable payload guarantee** — published record/event payloads are
   recursively canonically frozen into structural immutable storage
   (`FrozenPayloadMapping`: key-sorted immutable tuple pairs; no dict/list/set
   backing object reachable in the semantic graph; base-class mutation attacks
   impossible by type; attribute rebinding refused); closed fail-closed value
   domain (str/bool/int/float/None, approved Enum members, InformationKey,
   SchemaIdentity, str-keyed mappings, sequences as tuples; sets/frozensets,
   non-str keys, arbitrary and execution objects raise `SchemaViolation`; no
   blind deepcopy); canonical-hash compatibility via deterministic
   `payload_canonical_view` with `canonical_sha256` as the only hash authority;
   mapping insertion order never alters identity; list/tuple canonical
   equivalence preserved; copy/deepcopy/pickle fail closed;
2. **append-only ledger** — ordered event history, O(n) cumulative construction,
   O(1) amortized duplicate detection (identity index; no history uniqueness
   scan; no max-history threshold); documented append transaction (validate ->
   duplicate check -> history -> index) with rollback + invariant verification
   on stage failure and loud `ImmutabilityViolation` if rollback itself fails;
   injected-failure proofs cover history failure, index failure, duplicate
   rejection, invalid event, and retry-after-failure;
3. **earliest lawful availability** — O(R+S) single-scan computation using only
   the public CLOSED InformationKey comparison semantics; permutation
   invariant; fail-closed on incomparable keys
   (`IncomparableInformationKeys` / `NOT_COMPARABLE`); no fabricated ordering;
4. InformationKey bindings, information-batch foundations, canonical identity
   contracts, WaveProcess identity schema only, typed causal-reference
   foundations, typed missing-state foundations, and S0 error/schema-version
   contracts within tested scope (`TIE_ORDER_CONTRACT = NOT_PROVEN` remains);
5. certified baseline: **67 S0 dedicated / 67 passed**; **1139 collected /
   1139 passed** for the full suite; exit code 0;
6. external tool suite (field_runner `runner_tests`; outside this repository):
   36 passed pre-closure — context for the acceptance only. The external
   baseline guard pins the pre-S0 clean manifest baseline (185 lines /
   `12c66abe6f18300f2e00cb5c4befeafe1e3dc67c2ca50bc71db74db9ba8b367d`);
   this closure legitimately advances the official MANIFEST, so that external
   pin requires a separately authorized re-pin. The external guard was NOT
   modified during S0 closure;
7. pre-closure manifest identity: 185 lines,
   sha256 `12c66abe6f18300f2e00cb5c4befeafe1e3dc67c2ca50bc71db74db9ba8b367d`,
   185 OK / 0 stale / 0 missing; the 9 accepted S0 artifacts were unmanifested
   build artifacts (not replacements of existing MANIFEST paths) and are added
   with their accepted digests; accepted fingerprints (9 files: 5 source + 4
   tests) sealed in
   `docs/releases/MODULE_MUF_V1_S0_ACCEPTED_SRC_TESTS.sha256`;
8. independent implementation audit history: original audit (PATCH REQUIRED —
   P1) -> P1 (PATCHED) -> independent P1 re-audit (PATCH REQUIRED — P2) -> P2
   (PATCHED) -> final independent P2 re-audit **ACCEPTED FOR CLOSURE**.

Closure does NOT certify: wave detection; turning-point quality; hierarchy
usefulness; α/β/γ/δ superiority; predictive support; statistical independence;
edge; profitability; Model; Strategy; Signal; PnL; human-like understanding.
RESEARCH-DEBT-020..025 remain open. No S1 work is started or implied.

## Important identity boundary

Module 6.2A-3 remains:

```text
module release: V1.1
dataset contract string: CAUSAL_RESEARCH_DATASET_V1
```

This naming mismatch is preserved as an explicit known boundary; it was not silently patched.

## Open research debts

```text
RESEARCH-DEBT-020 — Hypothesis Lifecycle Termination Semantics
RESEARCH-DEBT-021 — Evidence-Bearing Calibration
RESEARCH-DEBT-022 — Entity-Level Narrative Provenance Contract
RESEARCH-DEBT-023 — Outcome Censoring and Competing-Risk Estimand
RESEARCH-DEBT-024 — Overlapping Hypothesis Dependence / Non-IID Samples
RESEARCH-DEBT-025 — Reference-Price and Market-Time Alignment
```

No debt above is claimed solved by closure.


## MUF V1 S1 closure boundary (Price Path Primitives)

Owner authorization: CLOSURE AUTHORIZED for MUF V1 S1 only; S1 = ACCEPTED FOR
CLOSURE. No S2 authorized.

Design chain: FINAL DESIGN → H1 → RC1. Implementation audit accepted; P1 patch
(4 schema foundations + LB gate) and P2 patch (membership earliest-lawful
availability) each re-audited — final state ACCEPTED FOR CLOSURE.

Final accepted S1 artifacts (see `docs/releases/MODULE_MUF_V1_S1_ACCEPTED_SRC_TESTS.sha256`):

```text
2ab56ad35c4a68e89ee6134b3d20f8968b0aad872abade49d121dd99d025f990  src/trading_system/market_understanding/price_path.py
707a1b7ba17b1bf370317c2634aa4c6a6c8b8cd6f1d1b21e8c29efa69e8b6aa6  src/trading_system/market_understanding/path_schemas.py
836240cf552ff0fdf7c447b983335281bcca166e740273f32de7462f661b3259  tests/test_muf_s1_price_path.py
f9908b04feff7ce0527085d640a9bd7f5198fc032558d5cbaf5d21a957b3387c  tests/test_muf_s1_path_schemas.py
```

Gate record (actual counts): S1 89/89 · S0 67/67 · full 1228/1228 · field_runner
36/36 (pre-closure). Closure touched documentation, release files and
`MANIFEST.sha256` only — no `src/` or `tests/` modification.

Certification boundary (mandatory): MUF V1 S1 proves **only factual causal
price-path representation**. It does NOT prove: turning-point quality, waves,
hierarchy, predictive support, edge, profitability, Model, Strategy, Signal,
PnL. `TIE_ORDER_CONTRACT = NOT_PROVEN`; PROXY is never ACTUAL; RESEARCH-DEBT-020
through RESEARCH-DEBT-025 remain OPEN (no independence claim in S1).

**MUF S1 = CLOSED.**


## MUF V1 S2 closure boundary (Detector Witness Adapter)

Owner authorization: CLOSURE AUTHORIZED for MUF V1 S2 (Detector Witness Adapter
ONLY); S2 = ACCEPTED FOR CLOSURE.

Final accepted S2 artifacts (see `docs/releases/MODULE_MUF_V1_S2_ACCEPTED_SRC_TESTS.sha256`):

```text
b6b09db548e78cf7ea551b2e37f4592500d24935fcea34dae67c8437262fd9f6  src/trading_system/market_understanding/detector_witness.py
35dcacbffd5fa3bcff04e2e2f136dfacf8a2658f4f4d91a2c125a4798949406b  tests/test_muf_s2_detector_witness.py
```

Gate record (actual counts): S2 30/30 · S1 89/89 · S0 67/67 · full 1258/1258 ·
field_runner 36/36 · mutation battery 8/8 KILLED.

Certification boundary (mandatory): MUF V1 S2 proves **only causal Detector
Witness Adaptation over Closed Module 2.1A (`Origin != Availability`,
`WITNESS_ONLY_NOT_MUF_AUTHORITATIVE`, `I-PAUTH-1..4` promotion blocking)**. It
does NOT prove: authoritative turning points, `PolicyArtifact` calibration,
waves, hierarchy, predictive support, edge, profitability, Model, Strategy,
Signal, PnL. `TIE_ORDER_CONTRACT = NOT_PROVEN`; PROXY is never ACTUAL;
RESEARCH-DEBT-020 through RESEARCH-DEBT-025 remain OPEN.

**MUF S2 = CLOSED.**


## MUF V1 S3 closure boundary (Research-Governance Infrastructure & Gate G0)

Owner authorization: CLOSURE AUTHORIZED for MUF V1 S3 (Research-Governance
Infrastructure & Authority Gate G0 ONLY); S3 = ACCEPTED FOR CLOSURE.

Final accepted S3 artifacts (see `docs/releases/MODULE_MUF_V1_S3_ACCEPTED_SRC_TESTS.sha256`):

```text
1564eca58b971ffc5bfa2ae1e1c4ad2944d630d264db9a468f910f608a33fc3b  src/trading_system/market_understanding/policy_governance.py
fee189f4689010fd1cedca37011729bcb22206c4a13fcef0ac940ca0af1d003f  tests/test_muf_s3_policy_governance.py
```

Gate record (actual counts): S3 30/30 · S2 30/30 · S1 89/89 · S0 67/67 ·
full 1288/1288 · field_runner 36/36 · mutation battery 8/8 KILLED.

Certification boundary (mandatory): MUF V1 S3 proves **only Research-Governance
Infrastructure (`ObjectiveArtifact`, `DatasetIdentityArtifact`,
`DatasetRoleArtifact`, `FoldProtocolArtifact`, `HumanReviewRecord`,
`RepresentationExperimentRecord`, `ExperimentRegistry`, `PolicyArtifact`,
`AuthoritativeTurningPointRecord` promotion contract) and Authority Gate `G0`
(`evaluate_g0_calibration_gate`)**. `QualificationObjective` remains
`TypedState.UNDEFINED` until an authorized `ObjectiveArtifact` is supplied. It
does NOT prove: calibrated detector policies (`S4`), waves (`S5`), hierarchy
(`S6`), predictive support (`S8`), edge, profitability, Model, Strategy, Signal,
PnL. `TIE_ORDER_CONTRACT = NOT_PROVEN`; PROXY is never ACTUAL; RESEARCH-DEBT-020
through RESEARCH-DEBT-025 remain OPEN.

**MUF S3 = CLOSED.**


## MUF V1 S4 closure boundary (Development Policy Calibration Harness)

Owner authorization: CLOSURE AUTHORIZED for MUF V1 S4 (Development Policy
Calibration Harness ONLY); S4 = ACCEPTED FOR CLOSURE.

Final accepted S4 artifacts (see `docs/releases/MODULE_MUF_V1_S4_ACCEPTED_SRC_TESTS.sha256`):

```text
0c765a6c261838cb36d4f096b764e9762541ffbb4b2e33ebf994a5fe96b07204  src/trading_system/market_understanding/policy_calibration.py
1549449b8531230da6afec0953c9fba47b1a17c6a422481c20acf52b34d9b46d  tests/test_muf_s4_policy_calibration.py
```

Gate record (actual counts): S4 20/20 · S3 30/30 · S2 30/30 · S1 89/89 ·
S0 67/67 · full 1308/1308 · field_runner 36/36 · mutation battery 8/8 KILLED.

Certification boundary (mandatory): MUF V1 S4 proves **only the G0-gated
Development Policy Calibration Harness (`PolicyCandidateScoreCard`,
`PolicyCalibrationRecipe`, `PolicyCalibrationReceipt`,
`validate_development_fit_bar_stream`, `calibrate_development_policy_artifact`,
`reproduce_and_verify_calibrated_policy`) on `DEVELOPMENT_FIT` datasets**. It
invents zero numerical parameters or objectives, preserves tied candidates
without inventing a winner, and does NOT prove: wave construction (`S5`),
structural qualification (`G1`), hierarchy, predictive support, edge,
profitability, Model, Strategy, Signal, PnL. `TIE_ORDER_CONTRACT = NOT_PROVEN`;
PROXY is never ACTUAL; RESEARCH-DEBT-020 through RESEARCH-DEBT-025 remain OPEN.

**MUF S4 = CLOSED.**


## MUF V1 S5 closure boundary (Candidate Wave Representation Construction & Gate G1)

Owner authorization: CLOSURE AUTHORIZED for MUF V1 S5 (Candidate Wave
Representation Construction & Structural Qualification Gate G1 ONLY);
S5 = ACCEPTED FOR CLOSURE.

Final accepted S5 artifacts (see `docs/releases/MODULE_MUF_V1_S5_ACCEPTED_SRC_TESTS.sha256`):

```text
851ce362b066ad4c0b1a85f2969ac0f7f3acb0476fa893e0512bfa09af4ff881  src/trading_system/market_understanding/wave_representation.py
695d340e8a2d0f8c01d2eec56eef41d846fd04ae5a9a59a638b5fb011b974772  tests/test_muf_s5_wave_representation.py
```

Gate record (actual counts): S5 20/20 · S4 20/20 · S3 30/30 · S2 30/30 ·
S1 89/89 · S0 67/67 · full 1328/1328 · field_runner 36/36 · mutation battery
8/8 KILLED.

Certification boundary (mandatory): MUF V1 S5 proves **only causal Candidate
Wave Representation Construction (`CandidateWaveRepresentationSpec`,
`WaveIdentityRecord`, `RunningWaveObservationRecord`,
`FinalizedWaveGeometryRecord`, `WaveStatusEventRecord`,
`CandidateWaveRepresentationBundle`, `query_wave_representation_as_of`,
`verify_wave_prefix_invariance`) on DEVELOPMENT datasets (`DEVELOPMENT_FIT` /
`DEVELOPMENT_SELECTION`) and Gate `G1` Structural Qualification
(`evaluate_g1_structural_qualification`: `ELIGIBLE / INELIGIBLE`, never a
predictive winner)**. It does NOT prove: state catalog / hierarchy (`S6`),
dependence accounting (`S7`), estimands (`S8`), predictive information
selection (`S9 + G2`), edge, profitability, Model, Strategy, Signal, PnL.
`TIE_ORDER_CONTRACT = NOT_PROVEN`; PROXY is never ACTUAL; RESEARCH-DEBT-020
through RESEARCH-DEBT-025 remain OPEN.

**MUF S5 = CLOSED.**


## MUF V1 S6 closure boundary (Descriptor Registry, StateCatalogArtifact, and GenericFactualStateGraphSpec)

Final accepted S6 artifacts (see `docs/releases/MODULE_MUF_V1_S6_ACCEPTED_SRC_TESTS.sha256`):

```text
9636529b60a9ab9ce2339319da1290417bfd93279b813ec7edaaac1a7a5a8e56  src/trading_system/market_understanding/state_graph.py
cb06fa6d4f283434643a446272baa3599419b68cabfc6f500b425eb9d46df49f  tests/test_muf_s6_state_graph.py
```

Gate record: S6 20/20 · full 1348/1348 · mutation battery 8/8 KILLED.
**MUF S6 = CLOSED.**


## MUF V1 S7 closure boundary (Dependence Accounting Contracts & Causal Episode Ledger)

Final accepted S7 artifacts (see `docs/releases/MODULE_MUF_V1_S7_ACCEPTED_SRC_TESTS.sha256`):

```text
376233810d980c38625b4b5db5bb79bfd9b792324f57d9a076724d41ce48bf24  src/trading_system/market_understanding/dependence_accounting.py
4a916832b3eb60e9250766fae20f391a02b06095b718600be6e260158f1fcd0a  tests/test_muf_s7_dependence_accounting.py
```

Gate record: S7 20/20 · full 1368/1368 · mutation battery 8/8 KILLED. `RESEARCH-DEBT-024` remains `OPEN`.
**MUF S7 = CLOSED.**


## MUF V1 S8 & S8.5 closure boundary (Estimand Catalog, FeatureViewSpec, and DevelopmentEvaluationProtocol)

Final accepted S8 & S8.5 artifacts (see `docs/releases/MODULE_MUF_V1_S8_ACCEPTED_SRC_TESTS.sha256`):

```text
8813ecf9d55da861a650016d8cb2e91a4e792a2f708f8a32d38af79d63a3a967  src/trading_system/market_understanding/estimand_catalog.py
5b8eaa3a18c5e75a90e6b7f66884d395b7fb8eab3e06b25ec02a3792531b6b3d  tests/test_muf_s8_estimand_catalog.py
```

Gate record: S8 20/20 · full 1388/1388 · mutation battery 8/8 KILLED.
**MUF S8 & S8.5 = CLOSED.**


## MUF V1 S9 & Gate G2 closure boundary (Development Information Selection)

Final accepted S9 & Gate G2 artifacts (see `docs/releases/MODULE_MUF_V1_S9_ACCEPTED_SRC_TESTS.sha256`):

```text
fc53d2990086e3b48c2d9a73e6ca62193edc4d38c8e1297d7fe1c1670354bf86  src/trading_system/market_understanding/information_selection.py
01b65b0dd7da0f7516dfc58b961ecc7c3bd04702813420f33f1a257832835435  tests/test_muf_s9_information_selection.py
```

Gate record: S9 20/20 · full 1408/1408 · mutation battery 8/8 KILLED.
**MUF S9 & Gate G2 = CLOSED.**


## MUF V1 S10–S12 & Gate G3 closure boundary (FrozenRepresentationBundle, EvaluationProtocolArtifact, PreFinalReadinessRecord, Comparability & Equivalence)

Final accepted S10–S12 & Gate G3 artifacts (see `docs/releases/MODULE_MUF_V1_S10_S12_ACCEPTED_SRC_TESTS.sha256`):

```text
532637ea86605176bc101990d432922c517a0c241a30349d38bb069d3789221b  src/trading_system/market_understanding/freeze_and_readiness.py
2d2985923c2e3114215949ba5ae210c9140fc80268c94dbcf99e2a72f7cda64b  tests/test_muf_s10_s12_freeze_and_readiness.py
```

Gate record: S10–S12 20/20 · full 1428/1428 · mutation battery 8/8 KILLED.
**MUF S10–S12 & Gate G3 = CLOSED.**


## MUF V1 S13–S15 closure boundary (Final Evaluation Execution, Exposure Ledger, and Reality / Causal Market Understanding Surface)

Final accepted S13–S15 artifacts (see `docs/releases/MODULE_MUF_V1_S13_S15_ACCEPTED_SRC_TESTS.sha256`):

```text
bce55a3846165277d00d0f713f10421266be00e0f7235c0d2cffa7ad8fe35947  src/trading_system/market_understanding/final_evaluation_and_reality.py
879372788481531d822ab27d0446834aae832404ff69270933401eac844d426d  tests/test_muf_s13_s15_final_evaluation_and_reality.py
```

Gate record: S13–S15 20/20 · full 1448/1448 · field_runner 36/36 · mutation battery 8/8 KILLED.
Certification boundary (D1-23 / D2-23): MUF V1 S0–S15 + G0–G3 proves causal structured market representation under the defined contracts with auditable provenance, availability, and selection boundaries. It does NOT prove predictive edge, statistical independence (`RESEARCH-DEBT-020`..`025` OPEN), profitability, Model, Strategy, Signal, or PnL.
**MUF S13–S15 = CLOSED.**


## Module 7.0 closure boundary (Causal Multi-Timeframe ICT Recommendation & Dynamic Trade Lifecycle Engine)

Final accepted Module 7.0 artifacts (see `docs/releases/MODULE_CAUSAL_ICT_LIFECYCLE_V1_ACCEPTED_SRC_TESTS.sha256`):

```text
dfe894070bdb0b2e016d5fabc61979209e7f605dc546567c179d9eeb1f8f56e6  src/trading_system/recommendation/__init__.py
ee91180d68e6229225848efed31070a2c8b955b38317fb7a01f9149c26ddc98f  src/trading_system/recommendation/causal_ict_lifecycle.py
a5edbd23b23cda64d2ce0c2c1939d0a7d6cae8deb178da3f4c02c674b3dd0c03  tests/test_causal_ict_lifecycle.py
```

Gate record: Module 7.0 20/20 · full 1468/1468 · field_runner 36/36 · mutation battery 8/8 KILLED.
**Module 7.0 = CLOSED.**






