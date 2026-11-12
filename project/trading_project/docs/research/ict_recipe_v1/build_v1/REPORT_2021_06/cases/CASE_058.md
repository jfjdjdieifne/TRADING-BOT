# CASE 58 — EURUSD 5m, decision at 2021-06-17T08:25:00+00:00 (bar index 34107)

## A. AS OF t — only what existed at t
A.1 context: daily bias `DOWN`, weekly bias `DOWN`, resolved `DOWN`
A.2 dealing range: low `1.19464`, high `1.19643`, equilibrium `1.195535`, position `premium`, ratio `0.5307` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.19643` high `relative_equal_pair`, formed at bar 5759, age 28348 bars
  - `1.21347` high `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.19935` high `relative_equal_pair`, formed at bar 5759, age 28348 bars
  - `1.20062` high `relative_equal_pair`, formed at bar 5759, age 28348 bars
  - `1.19464` low `relative_equal_pair`, formed at bar 5759, age 28348 bars
  - `1.19457` low `relative_equal_pair`, formed at bar 5759, age 28348 bars
  - `1.19425` low `relative_equal_pair`, formed at bar 5759, age 28348 bars
A.4 concepts at t: swing `[{'side': 'low', 'price': 1.19464, 'level_index': 5758}]`, FVG `none on this bar`, displacement `YES` (V-D-01, ratio 0.6250000000000631), sweep high `NO`, sweep low `NO`, structure shift `none`
A.5 candidate zones, ranked:
  - `fvg:bearish:34106` fvg [1.1953900000000002, 1.1957300000000002] fresh=False bias_agrees=True distance_ratio=0.01675977653629691
  - `fvg:bearish:34093` fvg [1.1962000000000002, 1.1970200000000002] fresh=False bias_agrees=True distance_ratio=0.5698324022345911
  - `fvg:bearish:34092` fvg [1.19721, 1.19811] fresh=False bias_agrees=True distance_ratio=1.156424581005355
  - `fvg:bearish:34091` fvg [1.19818, 1.1982000000000002] fresh=False bias_agrees=True distance_ratio=1.4525139664802647
  - `fvg:bearish:34079` fvg [1.19893, 1.2000300000000002] fresh=False bias_agrees=True distance_ratio=2.173184357541652
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.01675977653629691}}
A.6 competing hypotheses:
  - **bearish continuation with the DOWN daily bias** — for: daily bias DOWN; weekly bias DOWN; range position premium; 6 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bullish reversal / range fade** — for: 3 untaken pool(s) on that side; no opposite zone; against: daily bias is DOWN; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bearish** plan from the `fvg` zone `fvg:bearish:34106` was armed at 2021-06-17T08:25:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.1953900000000002` (touch of the zone edge nearest the trade direction), stop `1.1957300000000002` (far side of fvg), T1 `1.19464`, T2 `1.19457` (two targets existed), measured R:R T1 `2.206` / T2 `2.412`, half-spread at decision `9.99999999995449e-06`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-17T08:25:00+00:00  high 1.19562  low 1.19474  close 1.1955900000000002  state armed
  - 2021-06-17T08:30:00+00:00  high 1.19568  low 1.19518  close 1.19521  state triggered
  - 2021-06-17T08:35:00+00:00  high 1.19543  low 1.19508  close 1.1952900000000002  state triggered
  - 2021-06-17T08:40:00+00:00  high 1.19531  low 1.19455  close 1.19494  state triggered
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_target` (t1_touched), R = 2.1324, exit price `1.19464` at bar 34110.
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
