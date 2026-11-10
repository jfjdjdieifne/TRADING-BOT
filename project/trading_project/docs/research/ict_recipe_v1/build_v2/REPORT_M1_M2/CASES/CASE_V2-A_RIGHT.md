# CASE — V2-A — looks right

plan `plan:2021-09-07T07:40:00+00:00:15m:fvg:bearish:16922` · setup frame `15m` · decision 2021-09-07T07:40:00+00:00 (bar 50801)

## A. AS OF t
- zone `15m:fvg:bearish:16922` (fvg) [1.18788, 1.1879300000000002], formed at setup index 16922 on the 15m frame
- direction `bearish`; bias `DOWN`; range position `premium`; session `euro_0200_0500`
- entry `1.18788` (touch of the zone edge nearest the trade direction)
- stop `1.1879300000000002` (far side of fvg, 0.50 pips, 0.058823529411887635 of the setup candle's range)
- T1 `1.18628` (15m pool) · T2 `1.18576` (15m pool, informational only)
- measured R:R to T1 `32.0`; half-spread `0.000010`; cost as fraction of stop `0.400`
- criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.012886597938113946}}

## B. HINDSIGHT
- state `settled_target` / `t1_touched` at bar 50810, exit price `1.18628`
- R (half-spread both sides) = **31.4**
- trigger bar 50802 is the exit bar: False

## C. MECHANICAL RECOMPUTATION
- risk = |entry − stop| = 0.000050 (record: 0.000050)
- rr_t1 recomputed = 32.0000

## D. FAULT LOCATOR — HYPOTHESIS
- none visible: T1 touched before the stop under the conservative rule

## What this does NOT establish

- This case is one plan; it does not show that the variant is right or wrong.
- The fault category is a reading of stored fields, marked HYPOTHESIS.
