# ALL PLANS CHECKS — every plan of every run

- sha256 verified: 75 files match, 0 do not
- replay: independent function in `td_lib.py::replay` (no import of build_v1 or build_v2 settlement code); tolerance 1e-9, floating point only

| run | plans | MATCH | MISMATCH | F1 | F2 | F3 | F4 | F5 | F6 | F7 | F8 | F9 | F10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2021-09_v1 | 103 | 103 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2021-09_V2-0 | 30 | 30 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2021-09_V2-A | 17 | 17 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2021-09_V2-B | 16 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2021-09_V2-A-OFF | 98 | 98 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2021-09_V2-B-OFF | 39 | 39 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2021-07_v1 | 104 | 104 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2021-07_V2-0 | 43 | 43 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2021-07_V2-A | 26 | 26 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2021-07_V2-B | 10 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2021-07_V2-A-OFF | 109 | 109 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2021-07_V2-B-OFF | 39 | 39 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2021-06_V2-0 (IN_SAMPLE) | 43 | 43 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2021-06_V2-A (IN_SAMPLE) | 14 | 14 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2021-06_V2-B (IN_SAMPLE) | 8 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Checklist columns: F1 = stop on the correct side of entry; F2 = T1 beyond entry; F3 = entry inside the zone; F4 = T1 not already traded-through before arming (288-bar proxy); F5 = fill convention consistent (limit at the zone edge); F6 = half-spread applied once per side; F7 = same-bar rule applied as declared (stop first); F8 = first evaluation at or after the arming bar; F9 = R:R formula correct; F10 = replay reproduces the reported R

F4 is reported **NOT_EVALUABLE** for every plan: the saved plan record does not persist the T1 pool's formation index, so 'untaken between formation and arming' cannot be reconstructed from the outputs. The proxy count (closes beyond T1 in the 288 bars before arming) is printed in each card but is not a verdict. This is recorded as defect D5.

## Every mismatch

- none: every replay matched the engine to within 1e-9.

## Every FAIL

- **T1 beyond entry** — 2 plans. Examples: `2021-07_V2-A`/`plan:2021-07-27T06:15:00+00:00:15m:fvg:bullish:13986` (t1 1.18023); `2021-07_V2-A-OFF`/`plan:2021-07-13T00:15:00+00:00:15m:fvg:bearish:13011` (t1 1.18585)

## The NULL baseline

- The NULL entries were produced **inside** `report_v2.py::null_baseline`, per run, by replaying the same decision bars with the same stop distance and the same T1 distance, with the direction drawn once per plan from `random.Random(20261109)`.
- It is a **single seeded draw**, not an average of several draws: every plan gets one coin flip, so the NULL column moves by whole plans if the draw changes.
- Entry bars and distances: identical to the real plans by construction (the same `decision_index`, `|entry − stop|` and `|t1 − entry|` objects are used); only the direction is replaced. This is verified by construction, not by a separate check.

## What this does NOT establish

- A MATCH proves two implementations of the same convention agree; it does not prove the convention is right.
- A PASS on 'T1 not already traded-through' uses a 2,880-bar lookback (10 days of 5m); a different lookback would change the count.
