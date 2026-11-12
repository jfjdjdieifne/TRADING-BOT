# CAPABILITY VERIFICATION V0 — what the repository actually contains, checked against the code

**Method.** Every row below was established by reading the file named and by `grep` over
`project/trading_project/src/trading_system/**/*.py` on HEAD `ece160f`. No coverage table was used
as evidence; where a table disagrees with the code the disagreement is listed in §5. Three
repository-wide greps were run for the concepts that are *claimed absent*:

```text
dealing_range   24 files, 93 hits      equilibrium  13 hits     premium  31 hits   discount  29 hits
buy_side / sell_side / buyside / sellside : 0 hits each  (the concept exists under other names)
equal_high 2 hits, equal_low 0 hits ("EH"/"EL" are the code's names)
draw on / draw_on / liquidity_draw : 0 hits  (the code's name is DrawCandidate / rank_draws)
```

Two scopes must be kept apart throughout, because confusing them is the error this document
exists to correct:

- **IN-PATH** = reachable from `dev_month_v0/run_dev_month_v0.py` (packages
  `contextual_selection`, the `huddleston_study` runner, and `engine_v1/` if imported).
- **IN-REPO** = anywhere under `src/trading_system/`, including the Layer-2/4 modules and the
  `ict_engine` package, which are **not** imported by the dev path.

Import status was tested, not assumed: `importlib.import_module` succeeded for all nine modules
cited below under numpy 1.26.4 / pandas 2.2.3, with no side effects (no data load, no year
allow-list check — `ict_engine/data.py` enforces `ALLOWED_YEARS` only inside its loaders).

Test status (fixture tests, run in this session): `tests/test_dealing_range.py`,
`test_liquidity_map.py`, `test_order_blocks.py`, `test_structural_breaks.py`,
`test_swing_sequence.py`, `test_evidence_vector.py` → **153 passed, 0 failed**.

---

## 1. Table — the eighteen concepts

Legend — **Causal**: does the function read only information observable at or before the
decision instant? **CLOSED**: does it carry its own frozen fixture suite / expected file, so it
is treated as finished rather than in-progress?

| # | concept | file :: function (signature) | what it returns | causal | CLOSED | in `engine_v1`? | IN-PATH? |
|---|---|---|---|---|---|---|---|
| 1 | **dealing range** | `ict_engine/ranges.py:80` `dealing_range_trace(candles, basis=PriceBasis.BID) -> tuple[RangeObservation,...]` | per bar: `DealingRange(lower/upper SwingPoint, low, high, equilibrium, selected_at)`, `position` (`PREMIUM`/`DISCOUNT`/`EQUILIBRIUM`/`UNDEFINED`/`NO_MARKET`), `position_ratio`, `traded_outside` | **yes** — one forward pass, swing confirmed on the third bar, observation stamped `candle.end` | yes (`ict_engine/tests/test_ranges.py`) | no | **no** |
| | | `zones/dealing_range.py:170` `CausalDealingRangeEngine.analyze(df) -> (bar_surface, events)` | columns `current_range_low/high/midpoint/width/direction`, `current_range_position_raw`, `current_midpoint_displacement`, `current_discount_depth`, `current_premium_depth`, plus `created_*` per new range | **yes** — "creation-row … evaluated after causal creation", unclipped geometry, no Fib/OTE rule | yes (`tests/test_dealing_range.py`, passed) | no | **no** |
| 2 | **equilibrium** | `ict_engine/ranges.py:40` field `equilibrium` = `(low+high)/2`; `zones/dealing_range.py` `current_range_midpoint` | a price; and `RangePosition.EQUILIBRIUM` when the close equals it *exactly* | yes | yes | no | **no** |
| 3 | **premium** | `ict_engine/ranges.py:22` `RangePosition.PREMIUM` (close > equilibrium); `zones/dealing_range.py` `current_premium_depth` | enum + a depth fraction | yes | yes | no | **no** |
| 4 | **discount** | mirror of #3 (`current_discount_depth`, `RangePosition.DISCOUNT`) | enum + depth fraction | yes | yes | no | **no** |
| 5 | **buy-side liquidity** | *no symbol contains `buy_side`*. Supply is by side: `ict_engine/liquidity.py:30` `LiquidityPool.side: SwingSide.HIGH`; `liquidity/liquidity_map.py:351` `analyze(df)` → `created_level_side`, `high_side_first_touch_count`, `known_high_side_level_count` | pool objects / per-bar counts | yes — both are single forward passes that never look ahead | yes (`tests/test_liquidity_map.py`) | no (only the `V-E-EQH` id, which returns `UNDEFINED` by owner decision `D1`) | **no** |
| 6 | **sell-side liquidity** | mirror of #5 (`SwingSide.LOW`, `low_side_*`) | as #5 | yes | yes | no | **no** |
| 7 | **equal highs / equal lows** | `structure/swing_sequence.py:212` returns `"EH"`/`"EL"` on **exact** price equality (`HIGH: greater=HH, lower=LH, exactly equal=EH`); `ict_engine/liquidity.py:85` `liquidity_trace` forms `PoolKind.RELATIVE_EQUAL_PAIR` pools **without an equality cutoff**, exposing `equality_ratio` and `member_levels` | swing class string; pool with its member levels and ratio | yes | yes (`tests/test_swing_sequence.py`) | id only, `UNDEFINED` always | **no** |
| 8 | **liquidity pool not yet taken** | `ict_engine/liquidity.py:85` `liquidity_trace(candles, basis) -> tuple[tuple[PoolEvent,...],...]` with `PoolEventKind.FORMED/TAKEN/RETURNED_INSIDE`; `liquidity_map.py` `high_side_first_touch_count` (= 0 ⇒ untaken) | pool lifecycle events per bar; per-bar touch/breach counters | yes | yes | no | **no** |
| 9 | **sweep** | `engine_v1/c1_catalog/liquidity_sweep.py:279` `sweep_at(candles, t, side, level, variant)`; `:294` `sweep_at_swing_level(candles, t, side, variant)`; helper `:95` `latest_swing_reference(candles, before_index, side)` | dict: `status` (`BUILT`/`UNDEFINED`/`PENDING`), `answer` (`YES`/`NO`/`UNDECIDED`), `level`, `level_basis` (`CALLER_INPUT` vs owner swing), `candle_indices{sweep, confirm, last_read}`, `numbers{wick, close, open, level}`, `claim_ids`, `gaps` | **yes** — "Reads candles[:t+1] only" is stated in the sibling module and enforced by `require_index`; the swing scan walks backwards and stops at the first confirmed swing | yes (`c1_catalog/EXPECTED_C1.json`, `test_c1.py`) | **yes — this is it** | **no** (never imported) |
| 10 | **displacement** | `engine_v1/c1_catalog/displacement.py:176` `displacement_at(candles, t, variant, previous_window=None)`; also `zones/order_blocks.py:91` `analyze(df)` → `created_ob_displacement_fraction`, `created_ob_displacement_percentile`, `created_ob_displacement_history_count` | record with `status`/`answer`/`numbers`; variant `V-D-C` returns `UNDEFINED` + the formula gap because the sources never print the ATR formula | yes | yes (`EXPECTED_C1.json`; `tests/test_order_blocks.py`) | **yes** | **no** |
| 11 | **FVG** | three implementations: `engine_v1/b1_candles/fvg.py:45` `fvg_at(candles, t, direction)`; `contextual_selection/connected_readings.py:399` `scan_fvgs(frames) -> List[dict]`; `zones/fvg.py:38` `CausalFVGEngine.analyze(d)` → `created_fvg_*` + `gap_width_percentile` | record / `FVGRegion` objects / bar+event tables | yes (all three: bar 3 must have closed) | yes (`b1_candles/EXPECTED_FIXTURES.json`; `tests` for zones) | **yes** (`b1_candles`) | **yes** (`scan_fvgs`) |
| 12 | **order block** | `engine_v1/c1_catalog/order_block.py:211` `order_block_at(candles, displacement_start_index, direction, boundaries=None, mean_threshold_basis=None, entry_level=None, invalidation=None, prerequisites=None)`; `zones/order_blocks.py:91` `CausalOrderBlockEngine.analyze(df)` → `created_ob_full_zone_low/high`, `created_ob_body_low/high`, `created_ob_origin_prior_use_count`, touch/breach/reclaim counts | dict record / bar+event tables | yes | yes (`EXPECTED_C1.json`; `tests/test_order_blocks.py`) | **yes** | **partly** — `study_links.OBLikeCandidate` (`:292`) is a **record type with no detector**; nothing computes a block in-path |
| 13 | **structure shift / break** | `structure/structural_breaks.py:571` `CausalStructuralBreakEngine.analyze(df) -> pd.DataFrame` (first wick/close breach vs *eligible* prior levels, `structure_state` `UP_/DOWN_/MIXED/UNDEFINED`, overshoot ranked against prior break history); in-path: `csm.py:82` `STATUS_BROKEN`, `:649` `ShiftWatch` | per-bar break events + structure state | yes — "a level confirmed on row *i* … becomes breakable on row *i+1*" | yes (`tests/test_structural_breaks.py`) | no | **partial** — `ShiftWatch` records a *crossing to watch* and can only `SUSPEND`, never reverse |
| 14 | **HTF bias by multi-timeframe aggregation of 5m** | `run_forex_intraday_v1.py:119` `frames_builder(rows)` builds `1D/4h/1h/15m` from the 5m mid series (completion-labelled buckets); `study_links.py:373` `HigherFrameHypothesis(hypothesis_id, statement, failure_reference_level, failure_reference_id, failure_side, status, events)` with `review(bar_time, bar_high, bar_low, bar_close)`; `StudyReasoningLayer.hf_context` | resampled frames; a hypothesis with a **failure reference level**; crossing suspends, never reverses | yes | not as a unit (no fixture for `hf_context`) — `HigherFrameHypothesis` is a dataclass with no test file | no | **yes** |
| 15 | **draw on liquidity** | *no symbol contains `draw on`*. Code name: `ict_engine/liquidity.py:226` `pool_draw(pool) -> DrawCandidate`, `:238` `gap_draw(gap) -> DrawCandidate`, `:259` `rank_draws(draws, *, current_price, recent_range) -> tuple[RankedDraw,...]` (`distance_ratio`, `distance_rank`, `timeframe_significance_rank`) | candidate price levels; ranking by **relative distance to `recent_range`**, i.e. a context-relative rank with no cutoff | yes (pure functions over already-causal pools/gaps) | yes (`ict_engine/tests/`) | no | **no** |
| 16 | **stop = invalidation point** | in-path: `trade_plan.py:296` `build_components(scenario)` → `PlanComponent(kind="invalidation", definition="the first completed task-scale bar whose CLOSE is strictly beyond the falsifier reference level on its falsifying side", detector="sp03-close-violation")`; `:626` `_objective_exists` | a **rule** plus the level it binds to (`levels["reference"]["level"]`), frozen in the plan record | yes (close of a completed bar) | as part of the plan layer | no | **yes**, as a rule; the price comes from the leg's end extreme |
| 17 | **targets** | `trade_plan.py` objective = "one completed, causally confirmed task-scale F-K leg in the scenario direction whose knowable time is after the entry bar" (`detector="fk-leg-completion"`), while the same file records `"reference_selected": "NOT selectable … without a task and a stated objective"` | an **event** to wait for, not a price | yes | as part of the plan layer | no | **partial** — a target *event* exists; a target *price level* does not. The nearest price-level supplier is `rank_draws` (#15), which is not in path |
| 18 | **session windows** | `study_links.py:247` `SessionClockConvention`, `:264` `US_INDEX_FIRST_GAP_SESSION_CLOCK`; but `StudyReasoningLayer(..., session_clock=None)` at `:725`, so the convention is **off**; `ict_engine/market_status.py:27` `market_status(candle)` distinguishes only `MARKET`/`NO_MARKET` by flat-and-zero-volume | a convention object; an open/closed flag | yes | no fixture exercised with a clock | no | **no** (present, disabled) |

**Reading of the table.** Thirteen of eighteen concepts exist as code, with tests, somewhere in
`src/trading_system/`. Six are reachable from the dev path (FVG, HTF hypothesis, invalidation
rule, partial target-event, partial shift-watch, session convention that is switched off). The
**engine_v1** catalog supplies sweep, displacement, FVG, order block — and nothing else.

---

## 2. `engine_v1` in detail (what the closed catalog actually offers)

| module | public entry point | returns | limits stated in the code |
|---|---|---|---|
| `b1_candles/candle.py:18` | `Candle` (dataclass), `build_candles(rows) -> list` | candle objects with `open/high/low/close`, `closed` flag | bar labelled by start; decision-available at its end |
| `b1_candles/swing.py:52` | `swing_at(candles, t, side) -> dict` | `status` `YES/NO/UNDECIDED/PENDING` | V-A-00: middle of three *market* bars, confirmed at the third |
| `b1_candles/fvg.py:45` | `fvg_at(candles, t, direction) -> dict` | same status vocabulary | three-bar gap; bar 3 must be closed |
| `c1_catalog/liquidity_sweep.py:279` | `sweep_at(...)`, `sweep_at_swing_level(...)` | see row 9 | `latest_swing_reference` needs **no** lookback number: it walks back to the first confirmed swing |
| `c1_catalog/displacement.py:176` | `displacement_at(...)` | see row 10 | `V-D-C` deliberately `UNDEFINED` (no printed ATR formula) |
| `c1_catalog/order_block.py:211` | `order_block_at(...)` | see row 12 | requires the caller to name `boundaries`, `mean_threshold_basis`, `entry_level`, `invalidation` — the code refuses to invent them (`require_choice`) |

`c1_catalog/common.py` also supplies the honesty machinery the new wrapper should reuse:
`gap(gap_id)`, `gap_ids_of(concept)`, `dimension_gaps(concept)`, `require_number`,
`require_index`, `require_choice`.

---

## 3. What is genuinely MISSING (verified by absence, not by assumption)

1. **A selection rule among candidate zones.** `expert_selection` consumes points/legs only;
   nothing ranks FVG vs order block vs range edge. (`PAIRWISE_SELECTION_DESIGN_V1.md` designs it;
   `LEVEL_1B_ZONE_SELECTION = NOT_AVAILABLE_V1`.)
2. **A session/time-of-day filter that is switched on.** The convention exists; the dev path
   passes `None`.
3. **A target price derived from liquidity, in-path.** All the parts exist (`rank_draws`,
   `liquidity_trace`), the join does not.
4. **A single chain that feeds 5m bars → the Layer-2/4 engines → a decision.** The Layer-2/4
   engines are batch, panel-shaped (`analyze(df) -> DataFrame`), and are not wired to the
   streaming loop at all.
5. **A bounded-memory streaming loop.** Measured, not assumed — see `MEMORY_ANALYSIS_V0.md`.

---

## 4. Causal status of the batch engines, stated plainly

`swing_detector`, `swing_sequence`, `structural_breaks`, `liquidity_map`, `zones/dealing_range`,
`zones/fvg`, `zones/order_blocks` are **batch** engines: they take a DataFrame and return a
DataFrame covering every row. They are *causally constructed* (each row uses only rows ≤ i, and
several state this explicitly), but a batch call over a prefix `df[:i+1]` is what makes the
result causal at decision time `i`. Nothing in them prevents that usage; nothing in them
enforces it either. A streaming wrapper must therefore re-run them on the prefix (expensive) or
carry them forward row-by-row (requires editing them, which clause (d) forbids).

---

## 5. Contradictions between earlier documents and the code

| # | document | claim | what the code says | verdict |
|---|---|---|---|---|
| C1 | `dev_month_v0/ICT_CAPABILITY_AUDIT_V0.md` line 110 | "dealing range — **MISSING** — (grep: no `dealing_range`, no `dealing range` in the package)" | `zones/dealing_range.py` (328 lines, `CausalDealingRangeEngine`), `ict_engine/ranges.py` (132 lines, `dealing_range_trace`), `tests/test_dealing_range.py` (passing) | **document wrong.** The grep behind it covered only `engine_v1/` and `contextual_selection/`. Correct statement: absent from the **executed path**, present in the **repository**. |
| C2 | same, line 111 | "equilibrium / premium / discount — **MISSING** — (grep: nothing)" | 13 / 31 / 29 hits; `RangePosition` enum with all three; `current_premium_depth` / `current_discount_depth` | **document wrong**, same scoping error |
| C3 | same, line 112 | "buy-side / sell-side liquidity, equal highs/lows — **MISSING** in path — (grep: nothing)" | "in path" is right; "grep: nothing" is wrong — `SwingSide.HIGH/LOW`, `high_side_*` counters, `EH`/`EL` classes, `RELATIVE_EQUAL_PAIR` pools | **half right**: the in-path claim holds, the absence claim does not |
| C4 | same, line 164 | "any dealing-range or premium/discount number (not …)" — implying none exists | two independent implementations exist | **document wrong** |
| C5 | same, §1 | "`ict_engine/data.py` is not in the run path" | true: the runner has its own `load_bidask` (`run_forex_intraday_v1.py:90`) | **confirmed** |
| C6 | same, §3 | "sweep and displacement exist in `engine_v1` but are not imported by this run" | confirmed by import graph: no `engine_v1` import anywhere in `contextual_selection` or the runner | **confirmed** |
| C7 | `engine_v1/COVERAGE_TABLE_C1.md` rows C1.3, C1.4 | premium/discount and dealing range "لم يبدأ" ("not started") | same finding as C1 | **true for `engine_v1`'s own scope**, which is `C1` only; it must not be read as a statement about `src/trading_system` |
| C8 | `PAIRWISE_SELECTION_DESIGN_V1.md` | `LEVEL_1B_ZONE_SELECTION = NOT_AVAILABLE_V1` | zone **detectors** exist outside the selection layer; the **selection** step still does not | **not contradicted** — selection is missing, detection is not |
| C9 | `dev_month_v0/SUMMARY_V0.md` §6 | ranked gap list items 1–4 (dealing range, equilibrium, liquidity pools, draw on liquidity "absent") | items 1–4 exist as code; items 5–6 (sweep, displacement) are correctly described as "coded, not imported" | **items 1–4 wrong**, items 5–6 right; the ranking itself is unaffected because "not in path" is the operative fact |

The single sentence that renders all of C1–C4 harmless *and* explains them: **every one of those
documents was written about the dev run path, and the dev run path really does lack these
concepts.** What was wrong was the word "package".

---

## What this does NOT establish

- It does **not** establish that any of these modules computes anything *correctly* about a
  market. It establishes that the function exists, its signature, what it returns, whether it
  reads causally, and whether it carries a fixture suite. Correctness of the idea is a separate
  question and is not addressed here.
- It does **not** establish that the Layer-2/4 modules are *usable* under the project's own
  rules: `OLD_PIPELINE_DO_NOT_REUSE.md` forbids carrying rules, numbers and thresholds from the
  old pipeline into `engine_v1`, and whether these modules count as "old pipeline" is an **owner
  decision** (listed in `ICT_RECIPE_SPEC_V1.md` §7), not something this document may settle. It
  should be noted, factually, that the file's exclusion table does **not** name
  `structure/`, `zones/`, `liquidity/` or `ict_engine/{ranges,liquidity}.py`.
- It does **not** benchmark speed or memory: batch engines over a growing prefix are re-run work,
  and the cost is unknown here.
- Passing fixture tests is **not** a claim of closure (K10): closure is an explicit owner act.
  "CLOSED" in the table means "carries a frozen expected-file suite", nothing more.
- It does **not** touch, edit or import any market data; every statement is about source text.
- It does **not** revise `ICT_CAPABILITY_AUDIT_V0.md`: that file is frozen by its own block's
  rules, so the correction lives here and in the owner's reading of both.
