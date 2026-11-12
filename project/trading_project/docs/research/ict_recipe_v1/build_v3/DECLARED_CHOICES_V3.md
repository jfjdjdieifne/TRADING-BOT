# DECLARED CHOICES V3 — written before any run of the V3 engine

Status: every item below was fixed before the first V3 run. Nothing here was changed after seeing a
result; if a declaration could not be implemented, it is marked DROPPED with the reason.

Tags: **SOURCE_NUMBER** (a number printed in the repository's own material), **ENGINEERING_CHOICE**
(a decision of this build, declared here), **KNOWLEDGE_GAP** (the material does not settle it),
**FIXTURE** (a value in `EXPECTED_V3_FIXTURES.json`).

## A. Frames

Setup frames **15m** and **1h**, kept as two parallel arms (v2 selected neither). Execution frame
**5m**. The 20-trading-day lookback is expressed in time: 1920 bars at 15m, 480 bars at 1h, 5760 at
5m — ENGINEERING_CHOICE, unchanged from v2 row L.

## B. Hygiene, always on in the control V3-0

| id | rule | fixes | can change a decision? |
|---|---|---|---|
| H1 | side-correct execution: buy fills/triggers on ASK, sell on BID; a buy's stop and target are checked on BID, a sell's on ASK; spread charged **once** as spread-at-fill/2 | 1a | yes (fills, stops, targets, R) |
| H2 | a plan is `cancelled_invalidated_before_fill` when the stop-side price is taken on a bar that never traded at the entry; counted, excluded from R, reported | 1b | yes |
| H3 | one level = one pool: pair members and same-exact-level cross-frame pools merge into one pool with frame labels; T2 must be a distinct level | 1d | yes (targets) |
| H4 | a target not beyond the entry on the trade's side is rejected as `TARGET_BEHIND_ENTRY`; targets are filtered against the plan's own entry edge, not the decision close | 1e | yes |
| H5 | absolute indices and timestamps saved for swings, their confirmations, pools and zone candles; indices are **run-relative** (counted from the run's history start) and every such field says so | 1i, D1/D2/D5/D11 | no (record only), except that S1 and R can now read a swing's time |
| H6 | displacement is read on the zone's own candle(s) and the candle index is saved | v2 record gap | no for V3-0; supplies D |
| H7 | the first evaluation bar after arming is the **next 5m bar**; the arming bar never fills | v1 offset 0 vs v2 offset 1 | yes |
| H8 | reporting: NOT_EVALUABLE shown as NOT_EVALUABLE, spread-fraction labels correct, the position-ratio source named | D8/D10 | no |
| H9 | one thesis = one plan (v2 D4 rule kept) | — | yes |

## C. Switches, each a delta from V3-0

**S0 (control stop).** Far edge of the setup-frame zone; a sweep zone uses its wick.

**S1 — stop beyond the origin of the displacement leg.** Bearish: the highest high from the last
confirmed setup-frame swing high before the zone's middle candle up to the zone's first candle.
Bullish: the mirror. Sweep zones keep the sweep wick when it is further. No confirmed origin → **no
plan**, reason `S1_NO_CONFIRMED_ORIGIN`, no fallback. Source: the leg that leaves the gap is the
displacement; its origin is the invalidation. **KNOWLEDGE_GAP: DISPLACEMENT_ORIGIN_DEFINITION** —
the material does not name the origin candle, so "last confirmed swing before the zone's first candle"
is ENGINEERING_CHOICE.

**S2 — mean-threshold stop.** The source sentence is quoted in the study material as a stop "below the
mean threshold", which the repo's order-block module defines as the body midpoint
(`c1_catalog/order_block.py`, `ENTRY_MEAN_THRESHOLD`). Implemented as: for an `order_block` zone the
midpoint of the zone candle's body; for a gap or sweep zone there is no body, so the zone's
equilibrium `(lower+upper)/2` is used — ENGINEERING_CHOICE, with
**KNOWLEDGE_GAP: MEAN_THRESHOLD_FOR_GAPS**. It is not claimed to be the source's meaning.

**L — liquidity.** Adds previous-day and previous-week highs/lows as pools (completed buckets only),
labels every pool and target **INTERNAL** or **EXTERNAL** against the dealing range, and sets
**T2 = the next distinct EXTERNAL pool beyond T1** (None when there is none). The equilibrium level
and the nearest-untaken-external direction are recorded as informational features, never as targets
or gates.

**D — displacement.** Records, for every plan, D-old (v2 body/range on the zone's own candle) and
D-new: the leg that formed the zone closes beyond a prior confirmed swing (structure break) **and**
the zone is a gap — no size ratio. Also records the rank-based range expansion of the formation
candle inside the lookback (no cutoff). D-new is a **gate only in V3-FULL**; elsewhere it is a
feature. Source: the study's structure-break + gap reading; **KNOWLEDGE_GAP: DISPLACEMENT_SIZE**.

**T — time.** Day and week boundaries in America/New_York with DST: the day rolls at 17:00 NY, the week
opens Sunday 17:00 NY. The session window `EURO_0200_0500` is already interpreted in NY local time by
the engine (`sessions.py:38,55`), so T adds only the day/week boundary and the features (NY-midnight
relation, hour of day, rank-based activity). **Because the window was already NY, T does not re-time
the session** — this is stated in DIAGNOSIS 1h.

**E — entry.** Market fill at the **open of the 5m bar after** the bar that touched the zone and closed
inside it, on the side-correct price (buy at ASK open, sell at BID open); cancelled under H2 if the
stop is breached first. Other entry models (midpoint limit, retest-from-outside) are listed in
`VARIANT_LOG_V3.md` for a later authorisation and are not run.

**R — range.** The dealing range of the leg that created the zone: origin = the last confirmed
opposite-side swing before the zone's first candle; end extreme = the leg's extreme between the origin
and the zone's middle candle. Premium/discount is judged on the **zone's entry edge**, not the last
close. A zone outside its own range gets an explicit `ABOVE_RANGE`/`BELOW_RANGE` state, never a clamp.
**KNOWLEDGE_GAP: LEG_RANGE_ENDPOINTS**.

**FULL = S1 + L + D-new gate + T + E + R.** Declared here, before any run. S2 is excluded.

## D. Gates in normal runs

Session window (as T/V3-0 define it), daily-bias agreement, premium/discount agreement against the
range in use, target exists. Under `--wide` the same code records every gate as PASS/FAIL per plan and
applies none of them: every thesis is armed at its first touch.

## E. Statistics (all ENGINEERING_CHOICE, declared before running)

- Primary metric: **mean excess-hit** `mean(hit_i − p*_i)` with `p*_i = 1/(1+RR_i)` from the executed
  levels. Secondary: mean R, median R, hit rate with a Wilson interval.
- Expired and cancelled plans are excluded from the primary metric and reported separately.
- Day-cluster bootstrap: resample trading days, B = 10,000, 95 %, seed 20261109.
- Paired deltas versus V3-0 on the same thesis ids: common / added / removed reported separately.
- Permutation test: 10,000 permutations, seed 20261109, subset versus complement and subset versus
  random subsets of equal size.
- Holm correction over the declared test count: **12 tests** (6 switches × 2 months), per frame.
- Reported alongside: distinct trading days, share of total R from the top day, leave-one-day-out sign
  stability.

## F. Labels

A switch is `CANDIDATE_FOR_CONFIRMATION` only if its paired delta in the primary metric excludes 0 in
**both** round-1 months separately, with the same sign, and the sign survives leave-one-day-out.
Otherwise `INCONCLUSIVE` or `NO_SIGNAL`. CANDIDATE means only "may be run on the reserved months after
a new owner authorisation", never "works".

## G. Deferred

WINDOW_BARS sweep, leave-one-out of FULL, the other entry models, other pairs — deferred for the same
reason: one authorisation, one round of runs, no tuning on results.

## What this does NOT establish

- It does not establish that any switch captures the source's concept; each is one declared reading.
- It does not establish that the gates are the right gates; they are the v2 gates plus the declared
  delta, kept so that V3-0 and V2 differ only by hygiene.
- Declaring a statistic does not make it powerful at these plan counts.
