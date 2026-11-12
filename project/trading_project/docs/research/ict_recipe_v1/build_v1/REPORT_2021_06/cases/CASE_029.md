# CASE 29 — EURUSD 5m, decision at 2021-06-10T06:55:00+00:00 (bar index 32649)

## A. AS OF t — only what existed at t
A.1 context: daily bias `UP`, weekly bias `DOWN`, resolved `UP`, **bias_conflict**
A.2 dealing range: low `1.21649`, high `1.2174`, equilibrium `1.216945`, position `discount`, ratio `0.2747` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.2174` high `relative_equal_pair`, formed at bar 5759, age 26890 bars
  - `1.2217900000000002` high `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.21754` high `relative_equal_pair`, formed at bar 5759, age 26890 bars
  - `1.21757` high `relative_equal_pair`, formed at bar 5759, age 26890 bars
  - `1.2180300000000002` high `relative_equal_pair`, formed at bar 5759, age 26890 bars
  - `1.21649` low `relative_equal_pair`, formed at bar 5759, age 26890 bars
  - `1.2162000000000002` low `relative_equal_pair`, formed at bar 5759, age 26890 bars
  - `1.21616` low `relative_equal_pair`, formed at bar 5759, age 26890 bars
A.4 concepts at t: swing `none confirmed on this bar`, FVG `[{'direction': 'bearish', 'lower': 1.21711, 'upper': 1.21721, 'level_index': 5759, 'version': 'V-B-00', 'invalidation': 'KNOWLEDGE_GAP: FVG_INVALIDATION', 'gates': ['INVALIDATION_UNDECIDED']}]`, displacement `YES` (V-D-01, ratio 0.9024390243896099), sweep high `NO`, sweep low `NO`, structure shift `none`
A.5 candidate zones, ranked:
  - `fvg:bullish:32643` fvg [1.21667, 1.21682] fresh=False bias_agrees=True distance_ratio=0.005494505494297688
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.005494505494297688}}
A.6 competing hypotheses:
  - **bullish continuation with the UP daily bias** — for: daily bias UP; weekly bias DOWN; range position discount; 1 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bearish reversal / range fade** — for: 5 untaken pool(s) on that side; opposite zone exists; against: daily bias is UP; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bullish** plan from the `fvg` zone `fvg:bullish:32643` was armed at 2021-06-10T06:55:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.21682` (touch of the zone edge nearest the trade direction), stop `1.21667` (far side of fvg), T1 `1.2174`, T2 `1.21754` (two targets existed), measured R:R T1 `3.867` / T2 `4.8`, half-spread at decision `9.99999999995449e-06`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-10T06:55:00+00:00  high 1.21711  low 1.2167  close 1.2167400000000002  state armed
  - 2021-06-10T07:00:00+00:00  high 1.21676  low 1.21632  close 1.21673  state triggered
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_stop` (stop_touched), R = -1.1667, exit price `1.21667` at bar 32650.
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
