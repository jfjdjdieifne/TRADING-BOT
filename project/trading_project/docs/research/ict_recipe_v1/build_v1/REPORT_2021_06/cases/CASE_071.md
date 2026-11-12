# CASE 71 — EURUSD 5m, decision at 2021-06-23T06:05:00+00:00 (bar index 35231)

## A. AS OF t — only what existed at t
A.1 context: daily bias `UP`, weekly bias `DOWN`, resolved `UP`, **bias_conflict**
A.2 dealing range: low `1.19252`, high `1.19297`, equilibrium `1.192745`, position `discount`, ratio `0.2` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.19297` high `relative_equal_pair`, formed at bar 5759, age 29472 bars
  - `1.19325` high `relative_equal_pair`, formed at bar 5759, age 29472 bars
  - `1.19343` high `relative_equal_pair`, formed at bar 5759, age 29472 bars
  - `1.19345` high `relative_equal_pair`, formed at bar 5759, age 29472 bars
  - `1.19354` high `relative_equal_pair`, formed at bar 5759, age 29472 bars
  - `1.19398` high `relative_equal_pair`, formed at bar 5759, age 29472 bars
  - `1.19526` high `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.19421` high `relative_equal_pair`, formed at bar 5759, age 29472 bars
A.4 concepts at t: swing `[{'side': 'high', 'price': 1.19297, 'level_index': 5758}, {'side': 'low', 'price': 1.19252, 'level_index': 5758}]`, FVG `none on this bar`, displacement `NO` (V-D-01, ratio 0.14285714285646312), sweep high `NO`, sweep low `NO`, structure shift `none`
A.5 candidate zones, ranked:
  - `fvg:bullish:35229` fvg [1.19212, 1.19263] fresh=False bias_agrees=True distance_ratio=0.522222222222118
  - `fvg:bullish:35228` fvg [1.1919700000000002, 1.19208] fresh=False bias_agrees=True distance_ratio=1.2999999999999508
  - `fvg:bullish:35227` fvg [1.1919000000000002, 1.19192] fresh=False bias_agrees=True distance_ratio=1.5555555555556653
  - `fvg:bullish:35226` fvg [1.19178, 1.1918300000000002] fresh=False bias_agrees=True distance_ratio=1.788888888889015
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.522222222222118}}
A.6 competing hypotheses:
  - **bullish continuation with the UP daily bias** — for: daily bias UP; weekly bias DOWN; range position discount; 4 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bearish reversal / range fade** — for: 9 untaken pool(s) on that side; opposite zone exists; against: daily bias is UP; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bullish** plan from the `fvg` zone `fvg:bullish:35229` was armed at 2021-06-23T06:05:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.19263` (touch of the zone edge nearest the trade direction), stop `1.19212` (far side of fvg), T1 `1.19297`, T2 `1.19325` (two targets existed), measured R:R T1 `0.667` / T2 `1.216`, half-spread at decision `9.99999999995449e-06`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-23T06:05:00+00:00  high 1.19273  low 1.19259  close 1.1926100000000002  state armed
  - 2021-06-23T06:10:00+00:00  high 1.19294  low 1.1925400000000002  close 1.19272  state triggered
  - 2021-06-23T06:15:00+00:00  high 1.19287  low 1.19233  close 1.1923700000000002  state triggered
  - 2021-06-23T06:20:00+00:00  high 1.1924800000000002  low 1.19221  close 1.1923  state triggered
  - 2021-06-23T06:25:00+00:00  high 1.19267  low 1.1923100000000002  close 1.19266  state triggered
  - 2021-06-23T06:30:00+00:00  high 1.19301  low 1.19266  close 1.19277  state triggered
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_target` (t1_touched), R = 0.6176, exit price `1.19297` at bar 35236.
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
