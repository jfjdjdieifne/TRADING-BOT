# ICT RECIPE SPEC V1 — a bounded-memory streaming wrapper over 5m bid/ask

**Status: DESIGN ONLY.** No code is written in this task, nothing here is run, and no bar of
market data is read. This document specifies a *new* package — `ict_recipe_v1/` — that may import
existing modules and may not edit one line of them.

The purpose is single: at each decision time `t`, produce a **glass-box** reading of the chart and
one hypothetical plan, with every quantity traceable to a function and a candle index, and with
memory bounded by a *declared* lookback rather than by a machine's luck.

---

## 0. Two findings from the code that shape the whole design

1. **Most of the concepts already exist, but as batch panel engines** (`CAPABILITY_VERIFICATION_V0.md`
   §1): `zones/fvg.py`, `zones/order_blocks.py`, `zones/dealing_range.py`,
   `liquidity/liquidity_map.py`, `structure/structural_breaks.py`, `structure/swing_sequence.py`,
   `structure/swing_detector.py`, `ict_engine/liquidity.py`, `ict_engine/ranges.py`. They take a
   DataFrame and return a DataFrame. They are causally constructed, but they are not streaming.
2. **The streaming loop that exists accumulates without bound** (`MEMORY_ANALYSIS_V0.md`): it
   keeps a journal entry per 5m observation, an analysis record per boundary, and a study-layer
   ledger whose payloads are JSON-copies of the above.

Therefore the wrapper is **not** "a new ICT engine". It is a **window manager + assembler**:
a fixed-length causal window of 5m bars, re-fed to the closed batch engines at each decision
time, with the results immediately reduced to a small frozen record and the heavy objects
discarded.

---

## 1. The pipeline, step by step

Notation: `bars` = the causal window of 5m bars ending at the decision bar; `t` = its last index;
`frames` = resampled 15m/1h/4h/1D/1W views of `bars` built **only** from bars ≤ `t`.

| # | step | supplier (existing) | MISSING | smallest new function |
|---|---|---|---|---|
| 1 | **Load and normalise** | `run_forex_intraday_v1.load_bidask` (`:90`) + `mid_rows` (`:181`) for the mid series; bid/ask kept beside it for cost | nothing | `W0.load_year(dir, year) -> (bidask, mid)` — a thin call, no logic |
| 2 | **Window** | — | a bounded, causal buffer | `W0.Window(capacity).push(bar)` returning `frames`; drops the oldest bar, never the newest; every frame rebuild uses `bars ≤ t` only |
| 3 | **HTF context** (5m → 15m → 1h → 4h → 1D → 1W) | `run_forex_intraday_v1.frames_builder` (`:119`) already builds 15m/1h/4h/1D with completion labels; `study_links.HigherFrameHypothesis` (`:373`) supplies the "bias + failure reference" object | **weekly** aggregation is absent | `W0.weekly_frame(bars)` — 5 trading days → one bucket, completion-labelled; and `W0.bias(frames, t)` returning `UP/DOWN/UNDEFINED` + the level whose close breaks it |
| 4 | **Dealing range + position** | `ict_engine/ranges.py:80 dealing_range_trace` (causal, gives `low/high/equilibrium/position/position_ratio/traded_outside`) **or** `zones/dealing_range.py:170 analyze` (panel, gives depth fractions) | a per-`t` single-row call (the trace returns one row per bar; the wrapper takes `[-1]`) | `W0.range_at(bars, t) -> dict` — 12 lines: call the trace on the window, take the last observation, refuse if `position is UNDEFINED` |
| 5 | **Liquidity map** (which swing highs/lows are still untaken) | `ict_engine/liquidity.py:85 liquidity_trace` → `PoolEventKind.FORMED/TAKEN/RETURNED_INSIDE`; `liquidity_map.py:351 analyze` → `*_first_touch_count` (0 ⇒ untaken) | nothing conceptual; needs the *live set at t* rather than the whole trace | `W0.untaken_at(bars, t) -> list[Level]` — fold the event trace up to `t`, keep pools whose last event is `FORMED` |
| 6 | **Sweep** | `c1_catalog/liquidity_sweep.py:294 sweep_at_swing_level(candles, t, side, variant)` | `candles` must be `Candle` objects (`b1_candles/candle.build_candles`) | `W0.sweep_at(bars, t) -> dict` — build candles from the window, call both sides, return the record unchanged (it already carries `answer/status/gaps`) |
| 7 | **Displacement** | `c1_catalog/displacement.py:176 displacement_at(candles, t, variant, previous_window=None)`; `zones/order_blocks.py` also yields `created_ob_displacement_percentile` | a choice of variant is a **source** question, not a design one | `W0.displacement_at(bars, t) -> dict` — call the declared variant; if `UNDEFINED` (the `V-D-C` ATR gap) record the gap verbatim |
| 8 | **Structure shift** | `structure/structural_breaks.py:571 analyze(df)` (`structure_state`, first close breach, overshoot rank) | streaming call over the window | `W0.shift_at(bars, t) -> dict` — take the last row; report `structure_state` and the breach row |
| 9 | **Candidate entry zones** | `zones/fvg.py:38 analyze(d)` (gap width **percentile**), `zones/order_blocks.py:91 analyze(df)` (displacement **percentile**, body/full zone), `zones/dealing_range.py` (range edges) | **selection among them** — deliberately absent everywhere in the repo | `W0.zones_at(frames, t) -> list[Zone]` and then `W0.choose_zone(zones, ctx) -> Zone | None` — the second is the only place where a *rule* is invented, and §4 states exactly which rank it uses |
| 10 | **Plan** | entry = the chosen zone's edge/body; **stop = invalidation point** — reuse the semantics of `trade_plan.py:296` (`first completed task-scale bar whose CLOSE is strictly beyond the falsifier reference`), but bound to the zone/sweep extreme rather than a leg end | a plan object with a liquidity target | `W0.plan(zone, ctx, levels) -> Plan` — fields: `entry_zone_low/high`, `entry_trigger`, `stop_price` + its reference index, `t1`, `t2`, `rr_measured`, `what_would_change` |
| 11 | **Targets** | `ict_engine/liquidity.py:259 rank_draws(draws, *, current_price, recent_range)` — relative-distance ranking, no cutoff | a join between the zone and the ranked draws | `W0.targets(levels, price, recent_range) -> (t1, t2)` — take `distance_rank` 1 and 2 **on the side opposite the trade**, unchanged from `rank_draws` |
| 12 | **Measured R:R** | — | nothing exists | `W0.rr(entry, stop, t1, t2, spread, pip) -> dict` — arithmetic only, **recorded, never used as a filter** |
| 13 | **Record** | `c1_catalog/common.py`: `gap`, `gap_ids_of`, `dimension_gaps` | the record schema | `W0.write_case(record)` — append one JSON line per decision, keep nothing in memory |

**Everything the wrapper builds is thrown away at the end of the boundary except the one-line
record.** That is the memory bound; §5 states it numerically.

---

## 2. "How much" questions — the rule, applied case by case

The project forbids invented thresholds. Where a quantity is unavoidable, the wrapper uses a
**context-relative rank within the same chart up to `t`**, printed with `RELATIVE_ONLY` and its
denominator. Three cases:

| quantity | how the wrapper decides it | why this and not a number |
|---|---|---|
| **equal highs / lows tolerance** | no tolerance. Two levels are "equal" only when `SwingSide` prices are **exactly** equal (the code's `EH`/`EL`), or they are grouped by `RELATIVE_EQUAL_PAIR` with the ratio the module itself computes. Both are printed with their denominator. | any pip tolerance would be a number no source prints; exactness is falsifiable and `equality_ratio` is reported so a reader can see how loose the grouping is |
| **displacement "big enough"** | the `gap_width_percentile` / `displacement_percentile` the zone engines already compute over that chart's own history up to `t` (`CausalPercentileTracker`), printed as "this move ranks 7 of 31 comparable moves" | "ranks 7 of 31" is a fact about the chart; "≥ 1.5 × mean range" would be an invention |
| **which zone to enter** | rank the surviving zones by (i) agreement with the HTF failure-reference side, then (ii) the zone's own percentile, then (iii) `distance_rank` from `rank_draws`. The **ordering** is declared now and is not tuned; the *cutoff* is `None` — the top-ranked zone is used or the decision is `NO_SELECTION` | a rank order needs no threshold and cannot overfit silently, because it is printed on every case |

**KNOWLEDGE_GAP markers.** Where even a rank cannot be justified from a source, the record says so
instead of choosing: `GAP_PDA_DEPTH` (how deep into discount counts as "discount" beyond `ratio`),
`GAP_TARGET_PREFERENCE` (why T1 rather than T2 as the objective), `GAP_ZONE_AGE` (whether an old
FVG outranks a new one).

---

## 3. The plan, in plain words

For a long candidate:

- **entry** — a limit at the chosen zone's near edge (FVG near edge, or the order block's body
  edge), valid only while the zone is untapped. The trigger is *touch*, and the record states
  that a touch is not a fill (`contract_status = HYPOTHETICAL_NO_EXECUTION_CONTRACT`).
- **stop = invalidation** — placed at the extreme that would make the reading wrong: below the
  swing low that produced the structure (for a long), or below the sweep's wick if the entry is
  a sweep-reversal. The record names which, with its candle index.
- **T1** — the nearest *untaken* opposing liquidity (nearest sell-side pool above price by
  `distance_rank == 1`).
- **T2** — the next one beyond it (`distance_rank == 2`). If only one exists, `T2 = None` and
  that is printed, never filled in.
- **measured R:R** — `(T1 − entry) / (entry − stop)` in price, with spread and pip size the
  record's own; **recorded and never filtered on**. A plan with R:R 0.3 is kept and printed.
- **what would change this** — one sentence, generated from the record's own fields: the close
  level that voids the zone, the level whose break flips `structure_state`, and the hypothesis
  whose failure-reference is nearest.

---

## 4. Glass-box CASE template (identical to the dev-month prompt's sections)

```markdown
# CASE <n> — <instrument> 5m, decision at <t ISO> (bar index <i>)

## A. AS OF t — only what exists at t
A.1 context: HTF frames and their bias, WITH the failure-reference level
A.2 dealing range: low, high, equilibrium, position, position_ratio
A.3 liquidity map: untaken levels by side, with their formation index and age in bars
A.4 every concept, with candle indices: swing / FVG / order block / sweep / displacement /
    structure state — each one either a value or an explicit NO_SELECTION_STEP
A.5 candidate zones: ranked list with the rank order printed and its tie-breaks
A.6 competing hypotheses: at least two, each with what is FOR and what is AGAINST
A.7 the decision in plain words
A.8 the hypothetical plan: entry zone, stop + its reference index, T1, T2, measured R:R,
    "what would change this"
A.9 what the wrapper did NOT look at (absent concepts, off-by-design steps, data not held)

## B. HINDSIGHT — separated absolutely from A
B.1 bar-by-bar from t+1 to exit, invalidation or censoring, in order
B.2 same-bar ambiguity recorded as ambiguity (AMBIGUOUS_CENSORED), never resolved in favour
B.3 R and pips, including half-spread, with the fill assumption named (next_open)
B.4 censored counted separately from resolved

## C. MECHANICAL RECOMPUTATION — counts only
C.1 each numeric claim in A re-derived from the fixture/window by an independent call
C.2 mismatches listed with the exact field name; no interpretation
C.3 honesty flags: every quantity tagged SOURCE_NUMBER / ENGINEERING_CHOICE / KNOWLEDGE_GAP

## D. FAULT LOCATOR — HYPOTHESIS, one row
D.1 where the reading failed, if it did: facts / structure / bias / selection / stop / target /
    execution assumption / none visible
```

---

## 5. Memory bound (the reason this document exists)

Declared bound: the wrapper holds **one window of `WINDOW_BARS` 5m bars** plus one record per
decision, and nothing else that grows. With `WINDOW_BARS = 5,760` (20 trading days × 288 bars) the
peak working set is the window plus one batch pass of the panel engines, and it is **constant in
the number of decisions** — measured on the fixture in `MEMORY_ANALYSIS_V0.md`, no journal, no
ledger, and no per-boundary record list is retained.

`WINDOW_BARS` is not a tuning knob:

- **justification, without an invented number:** to state a *daily* bias you need daily bars; to
  confirm a daily swing the code needs three; to form a dealing range you need two alternating
  confirmed swings, i.e. at least three daily bars after the first; 20 daily bars is the smallest
  round window that always contains them, and it is the same order as the "one month" the owner
  already uses for dev.
- **tag:** `ENGINEERING_CHOICE`.
- **the honest control:** the dev run reports the same case set at `WINDOW_BARS ∈ {2,880, 5,760,
  11,520}` (10 / 20 / 40 days) as three separately labelled sweeps, and **the default is not
  changed to whichever looks better**. If the three sweeps cannot be produced, that is printed.

---

## 6. Fixtures-first test plan (no code before the expected files exist)

Every fixture is a hand-written candle list in the repository, in the same shape the engines
consume, with its expected output frozen in `EXPECTED_W0.json` **before** the wrapper function is
written. A fixture that the closed engine disagrees with is a *finding*, not a test to adjust.

| id | fixture (hand-made bars) | what it pins | expected file |
|---|---|---|---|
| F01 | 3 bars forming a bullish FVG (b1.high < b3.low) | `fvg_at` YES at bar 3, no value at bar 2 | `EXPECTED_W0.json` |
| F02 | 5 bars with a clean middle swing high | `swing_at` YES only at the third bar | same |
| F03 | bar wicking above the prior swing high and closing back below | `sweep_at_swing_level` → `answer=YES`, `candle_indices.sweep` correct | same |
| F04 | same but the close is exactly the level | `answer=UNDECIDED`, `GAP_SWEEP_EQUAL_CLOSE` present | same |
| F05 | displacement bar with body > 3× previous bodies | `displacement_at` record; percentile printed | same |
| F06 | opposing candle immediately before F05 | `order_block_at` zone bounds + `origin_prior_use_count` | same |
| F07 | two alternating confirmed swings, close in the upper half | `dealing_range_trace` `position=PREMIUM`, `equilibrium` exact | same |
| F08 | two highs at *exactly* the same price | swing class `EH`; pool `RELATIVE_EQUAL_PAIR` with `equality_ratio=1.0` | same |
| F09 | a level formed and never touched for 50 bars | `liquidity_trace` last event `FORMED`; untaken at `t` | same |
| F10 | the same level touched, then closed through | events `TAKEN` (`RETURNED_INSIDE` if it closes back) | same |
| F11 | close beyond the prior confirmed high | `structure_state` flips to `UP_STRUCTURE`, breach row named | same |
| F12 | Friday 21:55 → Sunday 22:00 gap (weekend) | 1W bucket spans 5 trading days only; no phantom bar | same |
| F13 | a bar whose range contains both stop and target | `AMBIGUOUS_CENSORED`, ordering never resolved | same |
| F14 | a chart where no untaken level exists on the trade side | `NO_SELECTION_STEP` / `t2=None`, and the record says why | same |
| F15 | a 60-bar window truncated at both ends | window drop-oldest keeps the last 60 bars, indices stable | same |

Test order is fixed: (1) expected files reviewed and frozen; (2) wrapper functions written;
(3) `python3 test_w0.py` run **in place** (the repo's convention — pytest does not collect these
directories); (4) any disagreement is reported before any market data is touched.

---

## 7. Decisions the owner must make (the single list)

1. **Scope of `OLD_PIPELINE_DO_NOT_REUSE.md`.** May the new wrapper *import* `structure/`,
   `zones/`, `liquidity/`, `ict_engine/{ranges,liquidity}.py`? That file's exclusion table does
   not name them, but it forbids carrying "rules, numbers and thresholds" into `engine_v1`. Import
   without copying is the design assumed here. **If the answer is no, six of the eleven pipeline
   steps need new code and this spec is roughly three times larger.**
2. **Clause (d) of `D3`.** Is the memory fix done *before* the phase opens (this document's
   assumption), or is `PATCH ONLY` permitted inside it? Without an answer, half of §1 cannot be
   built, because streaming the batch engines row-by-row would mean editing them.
3. **`WINDOW_BARS`.** Accept 5,760 (20 trading days), with the three-way sensitivity sweep in §5?
   Or name a different value, in which case it is the owner's `SOURCE_NUMBER`, not mine.
4. **Targets.** Confirm T1 = nearest untaken opposing liquidity, T2 = the next one beyond, both by
   `rank_draws` relative distance — and confirm that when only one exists, `T2 = None` (never
   invented).
5. **Zone ranking order** (§2, third row). Confirm the declared order, or replace it; it must be
   fixed before the dev run and never revisited after it.
6. **Dropping the loop journal.** Confirm the wrapper may discard `MonitoringLoop.journal`
   (it changes the exported state, not the decisions — see `MEMORY_ANALYSIS_V0.md` §4).
7. **Dev month.** Confirm `2021-06` as the next dev month (already declared in
   `PREREGISTRATION_V1.md` §9A before any load).
8. **Weekly aggregation.** Confirm it is required. It costs a five-day minimum window and adds a
   frame nothing in the repository currently produces.
9. **R:R discipline.** Confirm that measured R:R is *recorded and never filtered on*, including
   when it is below 1.
10. **What counts as "no result"** for the dev run (see `DEV_RUN_PLAN_V1.md` §5): is a month with
    zero plans a valid dev outcome to publish, or does it force a diagnostic pass first?

## What this does NOT establish

- It does **not** establish that this recipe is an ICT method, or that any source describes it:
  it is an assembly of existing repository functions in the order the concepts are normally
  presented, and the ordering itself is `ENGINEERING_CHOICE`.
- It does **not** establish that the recipe produces plans, or good ones. Nothing here has been
  run, and no number in this document is a result.
- It does **not** establish edge, profitability or accuracy — the words do not appear as claims,
  and measured R:R is explicitly a *record*, not a filter or a score.
- It does **not** resolve the governance question in §7.1; until the owner answers, the design
  assumes import-only reuse and says so on every record it would produce.
- It does **not** guarantee the memory bound: the bound is *declared and measured on the fixture*
  (`MEMORY_ANALYSIS_V0.md`), not proven for real data with heavier structure.
- It does **not** revise any frozen document, and it imports no data.
