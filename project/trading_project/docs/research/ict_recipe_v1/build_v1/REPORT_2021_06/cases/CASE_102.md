# CASE 102 — EURUSD 5m, decision at 2021-06-30T06:30:00+00:00 (bar index 36676)

## A. AS OF t — only what existed at t
A.1 context: daily bias `DOWN`, weekly bias `UP`, resolved `DOWN`, **bias_conflict**
A.2 dealing range: low `1.1894`, high `1.19005`, equilibrium `1.1897250000000001`, position `premium`, ratio `1.3077` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.19063` high `relative_equal_pair`, formed at bar 5759, age 30917 bars
  - `1.1909` high `relative_equal_pair`, formed at bar 5759, age 30917 bars
  - `1.1929500000000002` high `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.1894` low `relative_equal_pair`, formed at bar 5759, age 30917 bars
  - `1.18775` low `higher_timeframe_extreme`, formed at bar -1, age None bars
A.4 concepts at t: swing `none confirmed on this bar`, FVG `none on this bar`, displacement `YES` (V-D-01, ratio 0.806451612903272), sweep high `NO`, sweep low `NO`, structure shift `{'direction': 'UP', 'level': 1.19005, 'level_index': 5758}`
A.5 candidate zones, ranked:
  - `fvg:bearish:36667` fvg [1.19022, 1.1903] fresh=False bias_agrees=True distance_ratio=0.015384615384373633
  - `fvg:bearish:36632` fvg [1.19049, 1.19057] fresh=False bias_agrees=True distance_ratio=0.43076923076895224
  - `fvg:bearish:36628` fvg [1.1906800000000002, 1.19077] fresh=False bias_agrees=True distance_ratio=0.7307692307691913
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.015384615384373633}}
A.6 competing hypotheses:
  - **bearish continuation with the DOWN daily bias** — for: daily bias DOWN; weekly bias UP; range position premium; 3 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bullish reversal / range fade** — for: 2 untaken pool(s) on that side; no opposite zone; against: daily bias is DOWN; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bearish** plan from the `fvg` zone `fvg:bearish:36667` was armed at 2021-06-30T06:30:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.19022` (touch of the zone edge nearest the trade direction), stop `1.1903` (far side of fvg), T1 `1.1894`, T2 `1.18775` (two targets existed), measured R:R T1 `10.25` / T2 `30.875`, half-spread at decision `9.99999999995449e-06`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-30T06:30:00+00:00  high 1.19028  low 1.1899700000000002  close 1.19025  state armed
  - 2021-06-30T06:35:00+00:00  high 1.19028  low 1.1898700000000002  close 1.1900700000000002  state triggered
  - 2021-06-30T06:40:00+00:00  high 1.19052  low 1.19008  close 1.1902400000000002  state triggered
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_stop` (stop_touched), R = -1.25, exit price `1.1903` at bar 36678.
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
  - category: `stop`
  - verdict: `settled_stop`
  - evidence: the stop was touched before T1
