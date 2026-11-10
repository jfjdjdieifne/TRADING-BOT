# CASE 73 — EURUSD 5m, decision at 2021-06-23T06:20:00+00:00 (bar index 35234)

## A. AS OF t — only what existed at t
A.1 context: daily bias `UP`, weekly bias `DOWN`, resolved `UP`, **bias_conflict**
A.2 dealing range: low `1.19252`, high `1.19294`, equilibrium `1.19273`, position `discount`, ratio `-0.5238` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.19294` high `relative_equal_pair`, formed at bar 5759, age 29475 bars
  - `1.19297` high `relative_equal_pair`, formed at bar 5759, age 29475 bars
  - `1.19325` high `relative_equal_pair`, formed at bar 5759, age 29475 bars
  - `1.19343` high `relative_equal_pair`, formed at bar 5759, age 29475 bars
  - `1.19345` high `relative_equal_pair`, formed at bar 5759, age 29475 bars
  - `1.19354` high `relative_equal_pair`, formed at bar 5759, age 29475 bars
  - `1.19398` high `relative_equal_pair`, formed at bar 5759, age 29475 bars
  - `1.19526` high `higher_timeframe_extreme`, formed at bar -1, age None bars
A.4 concepts at t: swing `none confirmed on this bar`, FVG `[{'direction': 'bearish', 'lower': 1.1924800000000002, 'upper': 1.1925400000000002, 'level_index': 5759, 'version': 'V-B-00', 'invalidation': 'KNOWLEDGE_GAP: FVG_INVALIDATION', 'gates': ['INVALIDATION_UNDECIDED']}]`, displacement `NO` (V-D-01, ratio 0.29629629629635723), sweep high `NO`, sweep low `NO`, structure shift `{'direction': 'DOWN', 'level': 1.19252, 'level_index': 5758}`
A.5 candidate zones, ranked:
  - `fvg:bullish:35229` fvg [1.19212, 1.19263] fresh=False bias_agrees=True distance_ratio=0.17857142857212718
  - `fvg:bullish:35228` fvg [1.1919700000000002, 1.19208] fresh=False bias_agrees=True distance_ratio=0.6547619047616468
  - `fvg:bullish:35227` fvg [1.1919000000000002, 1.19192] fresh=False bias_agrees=True distance_ratio=0.9285714285714664
  - `fvg:bullish:35226` fvg [1.19178, 1.1918300000000002] fresh=False bias_agrees=True distance_ratio=1.1785714285715985
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.17857142857212718}}
A.6 competing hypotheses:
  - **bullish continuation with the UP daily bias** — for: daily bias UP; weekly bias DOWN; range position discount; 4 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bearish reversal / range fade** — for: 10 untaken pool(s) on that side; opposite zone exists; against: daily bias is UP; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bullish** plan from the `fvg` zone `fvg:bullish:35229` was armed at 2021-06-23T06:20:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.19263` (touch of the zone edge nearest the trade direction), stop `1.19212` (far side of fvg), T1 `1.19294`, T2 `1.19297` (two targets existed), measured R:R T1 `0.608` / T2 `0.667`, half-spread at decision `1.5000000000098268e-05`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-23T06:20:00+00:00  high 1.1924800000000002  low 1.19221  close 1.1923  state armed
  - 2021-06-23T06:25:00+00:00  high 1.19267  low 1.1923100000000002  close 1.19266  state armed
  - 2021-06-23T06:30:00+00:00  high 1.19301  low 1.19266  close 1.19277  state triggered
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_target` (t1_touched), R = 0.549, exit price `1.19294` at bar 35236.
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
