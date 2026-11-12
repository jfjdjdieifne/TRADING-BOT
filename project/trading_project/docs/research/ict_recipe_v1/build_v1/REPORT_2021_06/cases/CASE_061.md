# CASE 61 — EURUSD 5m, decision at 2021-06-18T06:30:00+00:00 (bar index 34372)

## A. AS OF t — only what existed at t
A.1 context: daily bias `DOWN`, weekly bias `DOWN`, resolved `DOWN`
A.2 dealing range: low `1.18962`, high `1.19086`, equilibrium `1.19024`, position `premium`, ratio `0.6694` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.19086` high `relative_equal_pair`, formed at bar 5759, age 28613 bars
  - `1.19164` high `relative_equal_pair`, formed at bar 5759, age 28613 bars
  - `1.20062` high `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.18962` low `relative_equal_pair`, formed at bar 5759, age 28613 bars
  - `1.18961` low `relative_equal_pair`, formed at bar 5759, age 28613 bars
  - `1.1895300000000002` low `relative_equal_pair`, formed at bar 5759, age 28613 bars
  - `1.18916` low `higher_timeframe_extreme`, formed at bar -1, age None bars
A.4 concepts at t: swing `none confirmed on this bar`, FVG `none on this bar`, displacement `NO` (V-D-01, ratio 0.21568627450947098), sweep high `NO`, sweep low `NO`, structure shift `none`
A.5 candidate zones, ranked:
  - `fvg:bearish:34357` fvg [1.19039, 1.19076] fresh=False bias_agrees=True distance_ratio=0.1008064516128368
  - `fvg:bearish:34356` fvg [1.19081, 1.19082] fresh=False bias_agrees=True distance_ratio=0.2943548387096052
  - `fvg:bearish:34355` fvg [1.19098, 1.19128] fresh=False bias_agrees=True distance_ratio=0.5483870967739682
  - `fvg:bearish:34354` fvg [1.19141, 1.19145] fresh=False bias_agrees=True distance_ratio=0.7903225806450631
  - `fvg:bearish:34350` fvg [1.19144, 1.1915300000000002] fresh=False bias_agrees=True distance_ratio=0.8346774193548474
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.1008064516128368}}
A.6 competing hypotheses:
  - **bearish continuation with the DOWN daily bias** — for: daily bias DOWN; weekly bias DOWN; range position premium; 11 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bullish reversal / range fade** — for: 4 untaken pool(s) on that side; no opposite zone; against: daily bias is DOWN; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bearish** plan from the `fvg` zone `fvg:bearish:34357` was armed at 2021-06-18T06:30:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.19039` (touch of the zone edge nearest the trade direction), stop `1.19076` (far side of fvg), T1 `1.18962`, T2 `1.18961` (two targets existed), measured R:R T1 `2.081` / T2 `2.108`, half-spread at decision `9.99999999995449e-06`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-18T06:30:00+00:00  high 1.1904800000000002  low 1.1899700000000002  close 1.19045  state armed
  - 2021-06-18T06:35:00+00:00  high 1.19053  low 1.19023  close 1.19033  state triggered
  - 2021-06-18T06:40:00+00:00  high 1.1905400000000002  low 1.18984  close 1.1899300000000002  state triggered
  - 2021-06-18T06:45:00+00:00  high 1.19013  low 1.18944  close 1.18945  state triggered
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_target` (t1_touched), R = 2.0135, exit price `1.18962` at bar 34375.
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
  - category: `none visible`
  - verdict: `settled_target`
  - evidence: T1 touched before the stop under the conservative rule
