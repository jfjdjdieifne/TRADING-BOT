# CASE — V2-A — looks wrong

plan `plan:2021-09-09T07:50:00+00:00:15m:fvg:bearish:17079` · setup frame `15m` · decision 2021-09-09T07:50:00+00:00 (bar 51379)

## A. AS OF t
- zone `15m:fvg:bearish:17079` (fvg) [1.1825100000000002, 1.18281], formed at setup index 17079 on the 15m frame
- direction `bearish`; bias `DOWN`; range position `premium`; session `euro_0200_0500`
- entry `1.1825100000000002` (touch of the zone edge nearest the trade direction)
- stop `1.18281` (far side of fvg, 3.00 pips, 0.43478260869523244 of the setup candle's range)
- T1 `1.18135` (15m pool) · T2 `1.18117` (15m pool, informational only)
- measured R:R to T1 `3.867`; half-spread `0.000020`; cost as fraction of stop `0.133`
- criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.12037037037031516}}

## B. HINDSIGHT
- state `settled_stop` / `stop_touched` at bar 51383, exit price `1.18281`
- R (half-spread both sides) = **-1.1167**
- trigger bar 51380 is the exit bar: False

## C. MECHANICAL RECOMPUTATION
- risk = |entry − stop| = 0.000300 (record: 0.000300)
- rr_t1 recomputed = 3.8667

## D. FAULT LOCATOR — HYPOTHESIS
- stop: the stop was reached on a later bar, before T1

## What this does NOT establish

- This case is one plan; it does not show that the variant is right or wrong.
- The fault category is a reading of stored fields, marked HYPOTHESIS.
