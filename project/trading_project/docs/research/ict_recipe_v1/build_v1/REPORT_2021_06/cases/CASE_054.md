# CASE 54 — EURUSD 5m, decision at 2021-06-16T08:45:00+00:00 (bar index 33823)

## A. AS OF t — only what existed at t
A.1 context: daily bias `UP`, weekly bias `DOWN`, resolved `UP`, **bias_conflict**
A.2 dealing range: low `1.21232`, high `1.2129100000000002`, equilibrium `1.212615`, position `discount`, ratio `0.4576` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.2129100000000002` high `relative_equal_pair`, formed at bar 5759, age 28064 bars
  - `1.21301` high `relative_equal_pair`, formed at bar 5759, age 28064 bars
  - `1.21337` high `relative_equal_pair`, formed at bar 5759, age 28064 bars
  - `1.21347` high `relative_equal_pair`, formed at bar 5759, age 28064 bars
  - `1.21473` high `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.21232` low `relative_equal_pair`, formed at bar 5759, age 28064 bars
  - `1.2118300000000002` low `relative_equal_pair`, formed at bar 5759, age 28064 bars
  - `1.21013` low `higher_timeframe_extreme`, formed at bar -1, age None bars
A.4 concepts at t: swing `[{'side': 'low', 'price': 1.21232, 'level_index': 5758}]`, FVG `none on this bar`, displacement `YES` (V-D-01, ratio 0.7187499999996314), sweep high `NO`, sweep low `NO`, structure shift `none`
A.5 candidate zones, ranked:
  - `fvg:bullish:33807` fvg [1.2122700000000002, 1.21282] fresh=False bias_agrees=True distance_ratio=0.07627118644078959
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.07627118644078959}}
A.6 competing hypotheses:
  - **bullish continuation with the UP daily bias** — for: daily bias UP; weekly bias DOWN; range position discount; 1 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bearish reversal / range fade** — for: 5 untaken pool(s) on that side; no opposite zone; against: daily bias is UP; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bullish** plan from the `fvg` zone `fvg:bullish:33807` was armed at 2021-06-16T08:45:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.21282` (touch of the zone edge nearest the trade direction), stop `1.2122700000000002` (far side of fvg), T1 `1.2129100000000002`, T2 `1.21301` (two targets existed), measured R:R T1 `0.164` / T2 `0.345`, half-spread at decision `1.5000000000098268e-05`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-16T08:45:00+00:00  high 1.2129  low 1.21258  close 1.21259  state armed
  - 2021-06-16T08:50:00+00:00  high 1.21287  low 1.21249  close 1.2126800000000002  state triggered
  - 2021-06-16T08:55:00+00:00  high 1.2129100000000002  low 1.2127100000000002  close 1.21287  state triggered
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_target` (t1_touched), R = 0.1273, exit price `1.2129100000000002` at bar 33825.
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
