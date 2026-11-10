# CASE 23 — EURUSD 5m, decision at 2021-06-09T06:05:00+00:00 (bar index 32351)

## A. AS OF t — only what existed at t
A.1 context: daily bias `DOWN`, weekly bias `DOWN`, resolved `DOWN`
A.2 dealing range: low `1.21755`, high `1.2178600000000002`, equilibrium `1.217705`, position `premium`, ratio `0.5806` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.2178600000000002` high `relative_equal_pair`, formed at bar 5759, age 26592 bars
  - `1.21941` high `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.2180000000000002` high `relative_equal_pair`, formed at bar 5759, age 26592 bars
  - `1.21801` high `relative_equal_pair`, formed at bar 5759, age 26592 bars
  - `1.2180700000000002` high `relative_equal_pair`, formed at bar 5759, age 26592 bars
  - `1.21815` high `relative_equal_pair`, formed at bar 5759, age 26592 bars
  - `1.21843` high `relative_equal_pair`, formed at bar 5759, age 26592 bars
  - `1.2185` high `relative_equal_pair`, formed at bar 5759, age 26592 bars
A.4 concepts at t: swing `[{'side': 'high', 'price': 1.2178600000000002, 'level_index': 5758}]`, FVG `none on this bar`, displacement `NO` (V-D-01, ratio 0.06666666666558112), sweep high `NO`, sweep low `NO`, structure shift `none`
A.5 candidate zones, ranked:
  - `fvg:bearish:32348` fvg [1.21768, 1.2178] fresh=False bias_agrees=True distance_ratio=0.0322580645155976
  - `fvg:bearish:32346` fvg [1.21788, 1.21789] fresh=False bias_agrees=True distance_ratio=0.4999999999985675
  - `fvg:bearish:32327` fvg [1.21795, 1.2180300000000002] fresh=False bias_agrees=True distance_ratio=0.8387096774184306
  - `fvg:bearish:32324` fvg [1.2181300000000002, 1.2182700000000002] fresh=False bias_agrees=True distance_ratio=1.5161290322567245
  - `fvg:bearish:32319` fvg [1.21826, 1.2183700000000002] fresh=False bias_agrees=True distance_ratio=1.8870967741914688
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.0322580645155976}}
A.6 competing hypotheses:
  - **bearish continuation with the DOWN daily bias** — for: daily bias DOWN; weekly bias DOWN; range position premium; 5 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bullish reversal / range fade** — for: 5 untaken pool(s) on that side; opposite zone exists; against: daily bias is DOWN; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bearish** plan from the `fvg` zone `fvg:bearish:32348` was armed at 2021-06-09T06:05:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.21768` (touch of the zone edge nearest the trade direction), stop `1.2178` (far side of fvg), T1 `1.21755`, T2 `1.2174` (two targets existed), measured R:R T1 `1.083` / T2 `2.333`, half-spread at decision `1.0000000000065512e-05`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-09T06:05:00+00:00  high 1.2178  low 1.21765  close 1.2177300000000002  state armed
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_stop` (stop_touched), R = -1.1667, exit price `1.2178` at bar 32351.
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
