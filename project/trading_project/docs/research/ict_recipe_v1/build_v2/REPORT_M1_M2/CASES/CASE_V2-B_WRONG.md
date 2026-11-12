# CASE — V2-B — looks wrong

plan `plan:2021-09-03T08:10:00+00:00:1h:sweep:low:None` · setup frame `1h` · decision 2021-09-03T08:10:00+00:00 (bar 50231)

## A. AS OF t
- zone `1h:sweep:low:None` (sweep_level) [1.1873, 1.1879700000000002], formed at setup index None on the 1h frame
- direction `bullish`; bias `UP`; range position `discount`; session `euro_0200_0500`
- entry `1.1879700000000002` (touch of the zone edge nearest the trade direction)
- stop `1.1873` (sweep wick, 6.70 pips, 0.6261682242992807 of the setup candle's range)
- T1 `1.18842` (1h pool) · T2 `None` (None pool, informational only)
- measured R:R to T1 `0.672`; half-spread `0.000010`; cost as fraction of stop `0.030`
- criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": true}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.4350649350648115}}

## B. HINDSIGHT
- state `settled_stop` / `stop_touched` at bar 50241, exit price `1.1873`
- R (half-spread both sides) = **-1.0373**
- trigger bar 50233 is the exit bar: False

## C. MECHANICAL RECOMPUTATION
- risk = |entry − stop| = 0.000670 (record: 0.000670)
- rr_t1 recomputed = 0.6716

## D. FAULT LOCATOR — HYPOTHESIS
- stop: the stop was reached on a later bar, before T1

## What this does NOT establish

- This case is one plan; it does not show that the variant is right or wrong.
- The fault category is a reading of stored fields, marked HYPOTHESIS.
