# CASE 64 — EURUSD 5m, decision at 2021-06-18T07:35:00+00:00 (bar index 34385)

## A. AS OF t — only what existed at t
A.1 context: daily bias `DOWN`, weekly bias `DOWN`, resolved `DOWN`
A.2 dealing range: low `1.18947`, high `1.1906500000000002`, equilibrium `1.1900600000000001`, position `premium`, ratio `0.8136` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.20062` high `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.1906500000000002` high `relative_equal_pair`, formed at bar 5759, age 28626 bars
  - `1.19086` high `relative_equal_pair`, formed at bar 5759, age 28626 bars
  - `1.19164` high `relative_equal_pair`, formed at bar 5759, age 28626 bars
  - `1.18947` low `relative_equal_pair`, formed at bar 5759, age 28626 bars
  - `1.18916` low `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.18941` low `relative_equal_pair`, formed at bar 5759, age 28626 bars
  - `1.18853` low `relative_equal_pair`, formed at bar 5759, age 28626 bars
A.4 concepts at t: swing `[{'side': 'low', 'price': 1.18947, 'level_index': 5758}]`, FVG `[{'direction': 'bullish', 'lower': 1.19004, 'upper': 1.1901400000000002, 'level_index': 5759, 'version': 'V-B-00', 'invalidation': 'KNOWLEDGE_GAP: FVG_INVALIDATION', 'gates': ['INVALIDATION_UNDECIDED']}]`, displacement `YES` (V-D-01, ratio 0.6923076923078675), sweep high `NO`, sweep low `NO`, structure shift `none`
A.5 candidate zones, ranked:
  - `fvg:bearish:34357` fvg [1.19039, 1.19076] fresh=False bias_agrees=True distance_ratio=0.1228813559320487
  - `fvg:bearish:34356` fvg [1.19081, 1.19082] fresh=False bias_agrees=True distance_ratio=0.32627118644050734
  - `fvg:bearish:34355` fvg [1.19098, 1.19128] fresh=False bias_agrees=True distance_ratio=0.5932203389827064
  - `fvg:bearish:34354` fvg [1.19141, 1.19145] fresh=False bias_agrees=True distance_ratio=0.8474576271184208
  - `fvg:bearish:34350` fvg [1.19144, 1.1915300000000002] fresh=False bias_agrees=True distance_ratio=0.8940677966100563
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.1228813559320487}}
A.6 competing hypotheses:
  - **bearish continuation with the DOWN daily bias** — for: daily bias DOWN; weekly bias DOWN; range position premium; 11 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bullish reversal / range fade** — for: 4 untaken pool(s) on that side; opposite zone exists; against: daily bias is DOWN; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bearish** plan from the `fvg` zone `fvg:bearish:34357` was armed at 2021-06-18T07:35:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.19039` (touch of the zone edge nearest the trade direction), stop `1.19076` (far side of fvg), T1 `1.18947`, T2 `1.18941` (two targets existed), measured R:R T1 `2.486` / T2 `2.649`, half-spread at decision `9.99999999995449e-06`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-18T07:35:00+00:00  high 1.19053  low 1.1901400000000002  close 1.19043  state armed
  - 2021-06-18T07:40:00+00:00  high 1.1907800000000002  low 1.1902700000000002  close 1.1907800000000002  state triggered
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_stop` (stop_touched), R = -1.0541, exit price `1.19076` at bar 34386.
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
