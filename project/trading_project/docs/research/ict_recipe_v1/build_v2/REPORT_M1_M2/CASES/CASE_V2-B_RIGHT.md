# CASE — V2-B — looks right

plan `plan:2021-09-14T08:00:00+00:00:1h:fvg:bearish:4315` · setup frame `1h` · decision 2021-09-14T08:00:00+00:00 (bar 52245)

## A. AS OF t
- zone `1h:fvg:bearish:4315` (fvg) [1.18232, 1.18296], formed at setup index 4315 on the 1h frame
- direction `bearish`; bias `DOWN`; range position `premium`; session `euro_0200_0500`
- entry `1.18232` (touch of the zone edge nearest the trade direction)
- stop `1.18296` (far side of fvg, 6.40 pips, 0.38554216867468427 of the setup candle's range)
- T1 `1.18066` (1h pool) · T2 `1.18054` (1h pool, informational only)
- measured R:R to T1 `2.594`; half-spread `0.000010`; cost as fraction of stop `0.031`
- criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.26363636363650494}}

## B. HINDSIGHT
- state `settled_target` / `t1_touched` at bar 52272, exit price `1.18066`
- R (half-spread both sides) = **2.5703**
- trigger bar 52246 is the exit bar: False

## C. MECHANICAL RECOMPUTATION
- risk = |entry − stop| = 0.000640 (record: 0.000640)
- rr_t1 recomputed = 2.5938

## D. FAULT LOCATOR — HYPOTHESIS
- none visible: T1 touched before the stop under the conservative rule

## What this does NOT establish

- This case is one plan; it does not show that the variant is right or wrong.
- The fault category is a reading of stored fields, marked HYPOTHESIS.
