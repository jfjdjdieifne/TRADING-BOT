# DECLARED CHOICES — SCALP v1 (written before any code and before any run)

Tags: **SOURCE_NUMBER: OWNER_SPEC** (the owner's specification, quoted), **ENGINEERING_CHOICE**
(a decision of this build, with its reason), **KNOWLEDGE_GAP** (the material does not settle it),
**FIXTURE** (a value in `EXPECTED_SCALP_FIXTURES_2.json`). `ENGINEERING_HYPOTHESIS` is not used.

## 1. Frames and data

- Setup frame **15m**, built causally from 5m bid candles (open = first 5m open, high = max, low = min,
  close = last 5m close, spread from the last 5m bar). A 15m candle is usable only after it completes.
- Path after entry simulated on **5m** bars — ENGINEERING_CHOICE: the finer frame orders the stop and
  the target inside the 15m candle that contains them; the owner gave no execution frame.
- Exploratory pool: EURUSD 5m months **2021-06, 2021-07, 2021-09, 2021-10, 2021-11**.
  **Forbidden and never constructed**: 2021-03, 2021-08, 2021-12, any 2022-2026 EURUSD month, any BTC
  month. The loader filters the CSV by timestamp **before** constructing a Bar, so a forbidden month
  is never materialised.
- Warmup: the first **WARMUP_15M = 40** 15m candles of each loaded month are never used for events —
  ENGINEERING_CHOICE: the swing detector needs confirmed swings and the "large" percentile needs 20
  prior candles.

## 2. The event (SOURCE_NUMBER: OWNER_SPEC)

```
S  sweep candle: low below a confirmed previous swing low, CLOSE back above it
   (detector: scalp_sweep.sweep_events, frozen, unchanged)
R  a large bullish rebound candle; R may be S itself or a later candle
FVG bullish fair value gap with R as the middle candle, known only at the close of the
   candle after R (in variant 1A that candle is H)
H  a bearish candle (hammer ideal, NOT required); H.low stays strictly above the 50% level
   of R's range, even slightly
Window  H closes within S+1..S+3 (primary); window 2 = H within S+1..S+2 (separate)
1A  R then H directly (H = R+1)
1B  R, one more bullish candle, then H (H = R+2)
Form 1 "strong": R created an FVG.   Form 2 "weak": R created no FVG.
```

### 2a. "Large" — one functional definition, declared before running

**Primary (L-RANGE):** `R.true_range ≥ P80 of the true ranges of the 20 completed 15m candles before R`,
where `true_range = high - low`. No pip threshold anywhere; the cut moves with the month.
Reason: relative to the candles actually present, which is what "large" can mean without a number.

Sensitivity only, reported, never chosen after seeing a result:
- **L-BODY**: `R body ≥ P80 of the bodies of the 20 candles before R`.
- **L-LOOSE**: `R.true_range ≥ P50 of the true ranges of the 20 candles before R`.

**KNOWLEDGE_GAP: LARGE_CANDLE_DEFINITION** — the owner gave no number and no comparison set.

### 2b. R and H selection

- `R ∈ {S, S+1, S+2}` for 1A and `{S, S+1}` for 1B, so that H can satisfy the window.
- ONE thesis per S: the **first** H that satisfies the rules is taken; later ones for the same S are
  ignored and counted in `later_h_ignored` — ENGINEERING_CHOICE.
- The FVG test is evaluated at H's close only (R's gap needs the candle after R), so nothing read at
  the H bar comes from a candle that has not closed — ENGINEERING_CHOICE, causal.

## 3. Entry, stop, target, cost (SOURCE_NUMBER: OWNER_SPEC except where tagged)

| element | rule |
|---|---|
| entry | at the **close of H**, buy on the **ask** (ask close of the last 5m bar of H) |
| stop | `H.low − 0.02 % of price` |
| target T | the last confirmed swing high **before** the swept swing low, minus `0.02 % of price` |
| buffer reason | ENGINEERING_CHOICE: symmetry with the stop buffer; the owner gave no number for T. **KNOWLEDGE_GAP: TARGET_BUFFER_INTENT** |
| T at or behind entry | `TARGET_BEHIND_ENTRY`, counted, excluded from outcomes, reported |
| risk < 1 pip | flagged `SUB_PIP_RISK`, kept in the main tables and reported apart in a separate row |
| cost | entry on ask, every exit on **bid** → the spread is counted exactly **once**; no extra cost term. (Note: `build_v3` charged an additional half-spread at the exit bar; that is V3's choice and is not repeated here, because asking on entry and bidding on exit already pays the full spread.) |
| sensitivity | entry at the **open of the next 15m bar**, reported only |

## 4. Path and outcome

- Forward window **WINDOW_BARS = 288** 5m bars (one trading day) — ENGINEERING_CHOICE, declared.
- Long: stop hit when `bid.low ≤ stop`; target hit when `bid.high ≥ T`. If both are true in the same
  5m bar the **stop** is taken and the bar is counted in `ambiguous_bars`.
- Hit = target reached before stop. `R_net = (exit − entry_ask)/risk`, risk = `entry_ask − stop`.
- Expiry: neither level inside the window → `expired`, excluded from excess-hit, reported apart.

## 5. Filters

**None.** No session filter, no bias filter — SOURCE_NUMBER: OWNER_SPEC. Bias is reported as a
**split** (one declared test per concept) and never used to select.

## 6. Control (seeded)

For every event, draw **M = 5** random 15m bars from the **same month** and the **same New-York
hour-of-day** (the NY hour of the event's entry bar), outside a **declared exclusion zone of ±2 hours**
around that event's S candle. Same direction (long), **same stop distance in pips and same target
distance in pips** as the event (so identical cost share and R:R), entry at the ask close of the
matched bar, path simulated on 5m with the same rules. Seed **20261109**, drawn per month in a fixed
order (months ascending, events in time order, five draws each).

## 7. Statistics (declared before running)

- Primary metric: **excess-hit** = `hit − 1/(1+RR_i)` with `RR_i` from the executed levels; secondary:
  **mean R**.
- **Declared test family: 20 tests = 5 months × 2 forms × 2 metrics**, all against the hour-matched
  control, all on LONG / variant 1A / window 3 / L-RANGE / primary entry. Holm over these 20.
- Everything else (1B, window 2, Form×Form splits, L-BODY, L-LOOSE, next-bar entry, sub-pip excluded,
  shorts, bias split) is **descriptive** and outside the Holm family; it is labelled as such in the
  report and can never promote a strategy.
- Cluster-by-day bootstrap B = 10,000 (seed 20261109); permutation 10,000 (seed 20261109).
- Per month: n events, n days, the CI half-width as the **minimum detectable effect**, sign consistency,
  leave-one-day-out, first-event-per-day sensitivity.
- Label per month/form: `CANDIDATE_FOR_CONFIRMATION` only if the paired difference to control has a CI
  excluding 0 in **at least two months** with the same sign AND survives Holm AND leave-one-day-out.
  Otherwise `NO_SIGNAL` (CI includes 0 and the point estimate is small) or `UNDERPOWERED` (CI includes 0
  and the half-width is larger than the effect the design could hope to see, declared as 0.10 excess-hit).
- Plain hit rate is printed next to break-even `1/(1+RR)`.
- Wording: `HYPOTHETICAL_` only; no WIN/LOSS/profit/PnL anywhere.

## 8. Shorts and case cards

- Shorts are the exact mirror, reported as a **separate secondary test**, never pooled.
- Case cards: 12 seeded cases (6 Form 1, 6 Form 2) from the exploratory months; candles **up to and
  including the entry candle only**; the outcome goes into `ANSWER_KEY.json`, whose sha256 is committed
  **before** the cards are written.

## 9. Deferred

Multiple H per S, other entry models, other target sources (e.g. the FVG edge), trailing exits,
partial fills, multi-pair, intraday seasonality of the target buffer. Reason: one authorisation, one
round, no tuning on results.

## What this does NOT establish

- It does not establish that "large", the 0.02 % buffers or the target choice are what the owner meant;
  they are declared engineering choices with the gaps named.
- It does not establish that the exploratory months can prove anything; they are all seen months.
- Declaring 20 tests does not make them powerful; the report must state the minimum detectable effect.
