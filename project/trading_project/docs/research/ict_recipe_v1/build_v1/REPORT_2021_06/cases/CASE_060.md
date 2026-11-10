# CASE 60 — EURUSD 5m, decision at 2021-06-18T06:20:00+00:00 (bar index 34370)

## A. AS OF t — only what existed at t
A.1 context: daily bias `DOWN`, weekly bias `DOWN`, resolved `DOWN`
A.2 dealing range: low `1.18962`, high `1.1907800000000002`, equilibrium `1.1902`, position `premium`, ratio `0.5431` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.19164` high `relative_equal_pair`, formed at bar 5759, age 28611 bars
  - `1.20062` high `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.18962` low `relative_equal_pair`, formed at bar 5759, age 28611 bars
  - `1.18961` low `relative_equal_pair`, formed at bar 5759, age 28611 bars
  - `1.1895300000000002` low `relative_equal_pair`, formed at bar 5759, age 28611 bars
  - `1.18916` low `higher_timeframe_extreme`, formed at bar -1, age None bars
A.4 concepts at t: swing `none confirmed on this bar`, FVG `none on this bar`, displacement `YES` (V-D-01, ratio 0.6718750000002657), sweep high `YES`, sweep low `NO`, structure shift `none`
A.5 candidate zones, ranked:
  - `sweep:high:None` sweep_level [1.19025, 1.1907800000000002] fresh=True bias_agrees=True distance_ratio=0.2284482758619807
  - `fvg:bearish:34357` fvg [1.19039, 1.19076] fresh=False bias_agrees=True distance_ratio=0.28017241379295904
  - `fvg:bearish:34356` fvg [1.19081, 1.19082] fresh=False bias_agrees=True distance_ratio=0.48706896551706397
  - `fvg:bearish:34355` fvg [1.19098, 1.19128] fresh=False bias_agrees=True distance_ratio=0.7586206896547962
  - `fvg:bearish:34354` fvg [1.19141, 1.19145] fresh=False bias_agrees=True distance_ratio=1.017241379310071
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": true}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.2284482758619807}}
A.6 competing hypotheses:
  - **bearish continuation with the DOWN daily bias** — for: daily bias DOWN; weekly bias DOWN; range position premium; 12 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bullish reversal / range fade** — for: 4 untaken pool(s) on that side; no opposite zone; against: daily bias is DOWN; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bearish** plan from the `sweep_level` zone `sweep:high:None` was armed at 2021-06-18T06:20:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.19025` (touch of the zone edge nearest the trade direction), stop `1.1907800000000002` (sweep wick), T1 `1.18962`, T2 `1.18961` (two targets existed), measured R:R T1 `1.189` / T2 `1.208`, half-spread at decision `9.99999999995449e-06`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-18T06:20:00+00:00  high 1.19086  low 1.19022  close 1.19025  state armed
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_stop` (stop_touched), R = -1.0377, exit price `1.1907800000000002` at bar 34370.
B.4 a plan that never triggered is counted as expired, not as resolved.

## C. MECHANICAL RECOMPUTATION — counts only
  - risk_price: match
  - rr_t1_measured: match
  - rr_t2_measured: match
  - stop_on_the_far_side: match
  - t1_ahead_of_entry: match
  - r_measured_from_prices: match
C.2 mismatches: 0 of 6 checks.
C.3 the numbers in A come from records already tagged with their source; this section only re-derives the arithmetic.

## D. FAULT LOCATOR — HYPOTHESIS
  - category: `execution assumption / stop`
  - verdict: `settled_stop`
  - evidence: the triggering bar spanned the whole zone, so the conservative stop-first rule settles it on the entry bar
