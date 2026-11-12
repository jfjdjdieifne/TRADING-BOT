# CASE 25 — EURUSD 5m, decision at 2021-06-09T06:15:00+00:00 (bar index 32353)

## A. AS OF t — only what existed at t
A.1 context: daily bias `DOWN`, weekly bias `DOWN`, resolved `DOWN`
A.2 dealing range: low `1.21765`, high `1.2178600000000002`, equilibrium `1.217755`, position `premium`, ratio `1.6667` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.21941` high `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.21843` high `relative_equal_pair`, formed at bar 5759, age 26594 bars
  - `1.2185` high `relative_equal_pair`, formed at bar 5759, age 26594 bars
  - `1.21852` high `relative_equal_pair`, formed at bar 5759, age 26594 bars
  - `1.21765` low `relative_equal_pair`, formed at bar 5759, age 26594 bars
  - `1.21642` low `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.21755` low `relative_equal_pair`, formed at bar 5759, age 26594 bars
  - `1.2174` low `relative_equal_pair`, formed at bar 5759, age 26594 bars
A.4 concepts at t: swing `none confirmed on this bar`, FVG `[{'direction': 'bullish', 'lower': 1.2178, 'upper': 1.21799, 'level_index': 5759, 'version': 'V-B-00', 'invalidation': 'KNOWLEDGE_GAP: FVG_INVALIDATION', 'gates': ['INVALIDATION_UNDECIDED']}]`, displacement `NO` (V-D-01, ratio 0.1304347826084858), sweep high `NO`, sweep low `NO`, structure shift `{'direction': 'UP', 'level': 1.2178600000000002, 'level_index': 5758}`
A.5 candidate zones, ranked:
  - `fvg:bearish:32327` fvg [1.21795, 1.2180300000000002] fresh=False bias_agrees=True distance_ratio=0.04761904761929937
  - `fvg:bearish:32324` fvg [1.2181300000000002, 1.2182700000000002] fresh=False bias_agrees=True distance_ratio=0.9523809523796433
  - `fvg:bearish:32319` fvg [1.21826, 1.2183700000000002] fresh=False bias_agrees=True distance_ratio=1.4999999999973566
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.04761904761929937}}
A.6 competing hypotheses:
  - **bearish continuation with the DOWN daily bias** — for: daily bias DOWN; weekly bias DOWN; range position premium; 3 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bullish reversal / range fade** — for: 6 untaken pool(s) on that side; opposite zone exists; against: daily bias is DOWN; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bearish** plan from the `fvg` zone `fvg:bearish:32327` was armed at 2021-06-09T06:15:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.21795` (touch of the zone edge nearest the trade direction), stop `1.2180300000000002` (far side of fvg), T1 `1.21765`, T2 `1.21755` (two targets existed), measured R:R T1 `3.75` / T2 `5.0`, half-spread at decision `2.000000000002e-05`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-09T06:15:00+00:00  high 1.21822  low 1.21799  close 1.2180000000000002  state armed
  - 2021-06-09T06:20:00+00:00  high 1.21809  low 1.21795  close 1.21809  state armed
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_stop` (stop_touched), R = -1.5, exit price `1.2180300000000002` at bar 32354.
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
