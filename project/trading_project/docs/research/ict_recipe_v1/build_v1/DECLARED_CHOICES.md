# DECLARED CHOICES V1 — every number and rule, declared before the code that uses it

Written **before** any file in this folder that computes anything. Each row carries one of three tags:

- **`SOURCE_NUMBER`** — the value is printed by a source and is copied from the module that carries it
  (with its claim/source ids in the code).
- **`ENGINEERING_CHOICE`** — no source prints it; the value is a build decision with a stated reason, and
  it is printed on every record that depends on it.
- **`KNOWLEDGE_GAP`** — no source settles it and no build decision is defensible; the record says so and
  the build refuses to fill it in.

| # | quantity / rule | value | tag | reason and where it is printed |
|---|---|---|---|---|
| 1 | `WINDOW_BARS` (bounded causal lookback, 5m bars) | **5,760** = 20 trading days × 288 bars | `ENGINEERING_CHOICE` | the brief's value. 20 trading days is one calendar month of 24h FX bars less weekends, i.e. exactly the horizon a monthly decision month can be read against; it is also larger than every lookback any reused primitive asks for (3 candles, 10-candle window, one HTF bucket pair). Sensitivity design: re-running with 2,880 / 5,760 / 11,520 bars is the three-way sweep already specified in `ICT_RECIPE_SPEC_V1` §5; **no sweep is run in this task**, and the report states the window on every record |
| 2 | decision cadence | **one decision per closed 5m bar** | `ENGINEERING_CHOICE` | a bar is decision-available at its `end` (`Candle.end`); deciding on every closed bar is the only cadence with no free parameter. The alternative (one decision per HTF boundary) would import the old pipeline's boundary logic, which is forbidden |
| 3 | T1 | nearest **untaken** opposing liquidity ahead of entry, ranked by `ict_engine.liquidity.rank_draws` (`distance_ratio` relative to the current dealing range) | `SOURCE_NUMBER` for the ranking function; the *choice* of T1 = rank 1 | `rank_draws` computes distance relative to the chart's own recent range, so no absolute level is invented |
| 4 | T2 | the **next** draw beyond T1 in the same ordering; `None` when only one exists | `ENGINEERING_CHOICE` | the modules rank but never name a second target; when the list has one element the record says `t2: null`, never fills it |
| 5 | stop | **invalidation point**: for a block entry the far side of the block; for a sweep entry the sweep wick | `ENGINEERING_CHOICE` | no buffer is specified anywhere; the stop sits **exactly** on the level and every plan prints `stop_rule` with the candle index of that level |
| 6 | measured R:R | `(T1 − entry) / (entry − stop)` on bid, **recorded, never filtered** | `ENGINEERING_CHOICE` | the brief forbids filtering on it; the summary reports its distribution and nothing is discarded |
| 7 | cost model | **half the bar's own spread at entry and at exit** (`SpreadOpen` of the decision bar), deducted from every hypothetical R | `SOURCE_NUMBER` (the spread is in the data) + `ENGINEERING_CHOICE` (halving it) | a market-order fill pays half the quoted spread on each side; the assumed fill is at the zone edge, so the cost is applied once per side |
| 8 | zone ranking criteria | (i) direction agreement with the **completed daily bias**; (ii) **freshness** — never closed through since formation; (iii) `distance_rank` from `rank_draws` | (ii) is a mechanical fact (`ENGINEERING_CHOICE` for using it); (iii) is `SOURCE_NUMBER` (module ranking); (i) is `ENGINEERING_CHOICE` | no source gives priority between the three. **When (i) and (iii) disagree on which zone is best the zone is reported `criteria_conflict` and no plan is issued** — the build never invents an order. This is the only place a rule is composed, and it composes printed facts |
| 9 | HTF bias | **daily and weekly are both required**; bias = sign of (last completed HTF close − last completed HTF open); a completed bucket is only used at `available_at` (one bucket later) | `ENGINEERING_CHOICE` with `SOURCE_NUMBER` input | the aggregation is `ict_engine.htf` (calendar-anchored, completion-labelled); the *sign* rule is threshold-free, unlike "above the 50 %" which would be a choice. Where daily and weekly disagree the record says `bias_conflict` |
| 10 | session window | `EURO_0200_0500` is the trading window; all six printed windows are evaluated and stored | `SOURCE_NUMBER` for the windows (claim ids U0089–U0095), `ENGINEERING_CHOICE` for picking one | the same clock as the pre-registered `R00` variant; picking a different window would be tuning |
| 11 | displacement variant | `V-D-01` (body/range > 60, equality → `UNDECIDED`) | `SOURCE_NUMBER` (claim F1 prints 60); **owner decision D2 says there is no reference variant**, so the record prints `displacement_variant: V-D-01` and `KNOWLEDGE_GAP: DISPLACEMENT_NO_REFERENCE_VARIANT` on every plan | V-D-02/03 read a caller-named window (3/4/5/10) — a choice on top of a source number; V-D-C is undefined (ATR formula gap). V-D-01 is the only fully printed variant |
| 12 | sweep variant | `V-E-00` (wick beyond + body closes back) | `SOURCE_NUMBER` (claim set E1/E3/E4/E5) | `V-E-01` needs one extra bar to confirm and is evaluated at the confirming bar; it is computed and reported beside, not used for entry |
| 13 | equal-highs tolerance | **no tolerance**: two same-side confirmed swing levels form a `relative_equal_pair` whatever their distance, and the module's own `equality_ratio` is printed | `KNOWLEDGE_GAP: EQUAL_HIGHS_RATIO` | any pip tolerance is a number no source prints. Pools are therefore *relative pairs*, and every plan that uses one says so |
| 14 | FVG invalidation | not computed; a gap is reported **untouched / touched / closed-through** as a mechanical fact, and the closure rule is `KNOWLEDGE_GAP: FVG_INVALIDATION` | `KNOWLEDGE_GAP` | `b1_candles/fvg.py` refuses invalidation on purpose (`INVALIDATION_UNDECIDED`) |
| 15 | structure-shift qualification | a **close** beyond the most recent confirmed opposing swing | `ENGINEERING_CHOICE` + `KNOWLEDGE_GAP: STRUCTURE_SHIFT_QUALIFICATION` | Module 2.1C qualifies a break with an upstream surface this build does not produce; the build uses the plain close break and says so |
| 16 | "how much" questions (any magnitude) | answered by **context-relative rank within the same chart up to t** (e.g. "distance rank 2 of 7 untaken pools"), never by an absolute threshold | `ENGINEERING_CHOICE` | the project forbids invented thresholds; a rank is a fact about the chart and is falsifiable |
| 17 | memory cap | **70 % of physical RAM**, checked every 60 bars; on breach the wrapper writes `partial_status.json` and exits with code 3 | `ENGINEERING_CHOICE` | the brief's value; it must stop itself rather than be killed by the kernel (the earlier dev run died at 3.87 GB of 3.94 GB) |
| 18 | intrabar order when a bar touches both stop and target | **stop first** | `ENGINEERING_CHOICE` | the 5m bar has no path information; choosing the adverse order is the conservative reading and it is printed on every tracked plan |
| 19 | plan expiry | a plan whose entry zone is not touched within **288 bars (one trading day)** expires | `ENGINEERING_CHOICE` | a stale zone is no longer the zone the thesis was about; the count is the same 288 that makes one day, printed on the record |
| 20 | entry trigger | a **touch** of the zone edge (low ≤ edge for a long, high ≥ edge for a short), not a fill | `ENGINEERING_CHOICE` | the record marks `contract_status = HYPOTHETICAL_NO_EXECUTION_CONTRACT`; a touch is not an execution |

## Rules that are not numbers

- **Causal reads only.** Every primitive receives candles `[:t+1]`; the wrapper never passes a bar whose
  `end` is after the decision time. `assert_prefix_invariance` is applied to the reused engine output in
  the fixtures.
- **Malformed candles raise `ValueError`.** A bar with `high < low`, a non-numeric price, or a bar whose
  `start` is not strictly increasing stops the run (no silent repair).
- **No tuning on 2021-06.** Any change made after the run is written to `VARIANT_LOG.md` and would need a
  different month and a new authorisation.
- **Wording.** Plans are `HYPOTHETICAL_`; the words win/loss/profit do not appear in an output; a result is
  `R` and a plan is `settled_target / settled_stop / open / expired`.

## What this does NOT establish

- These are declared *before* seeing 2021-06; that is what makes them admissible, not any evidence that they
  are the right values.
- `WINDOW_BARS = 5760` is not validated: the sensitivity sweep that would test it is specified and **not run**.
- The ranking in row 8 is a composition of printed facts, but the *choice* to compose them in that order is
  the build's own, and a different composition would produce different plans.
- Rows 3, 12 and 15 reuse a definition; rows 4, 5, 9, 16, 18, 19, 20 are engineering decisions and are
  labelled as such on every record they touch.
