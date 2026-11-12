# CASE 94 — EURUSD 5m, decision at 2021-06-28T08:00:00+00:00 (bar index 36118)

## A. AS OF t — only what existed at t
A.1 context: daily bias `UP`, weekly bias `UP`, resolved `UP`
A.2 dealing range: low `1.19377`, high `1.1942000000000002`, equilibrium `1.193985`, position `discount`, ratio `0.1628` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.1942000000000002` high `relative_equal_pair`, formed at bar 5759, age 30359 bars
  - `1.19442` high `relative_equal_pair`, formed at bar 5759, age 30359 bars
  - `1.1944400000000002` high `relative_equal_pair`, formed at bar 5759, age 30359 bars
  - `1.19377` low `relative_equal_pair`, formed at bar 5759, age 30359 bars
  - `1.1937000000000002` low `relative_equal_pair`, formed at bar 5759, age 30359 bars
  - `1.1927500000000002` low `relative_equal_pair`, formed at bar 5759, age 30359 bars
  - `1.19236` low `relative_equal_pair`, formed at bar 5759, age 30359 bars
  - `1.1923` low `relative_equal_pair`, formed at bar 5759, age 30359 bars
A.4 concepts at t: swing `[{'side': 'high', 'price': 1.1942000000000002, 'level_index': 5758}]`, FVG `none on this bar`, displacement `YES` (V-D-01, ratio 0.8421052631580485), sweep high `NO`, sweep low `NO`, structure shift `none`
A.5 candidate zones, ranked:
  - `fvg:bullish:36107` fvg [1.1933, 1.19401] fresh=False bias_agrees=True distance_ratio=0.43023255813910255
  - `fvg:bullish:36100` fvg [1.19286, 1.19296] fresh=False bias_agrees=True distance_ratio=2.162790697673878
  - `fvg:bullish:36088` fvg [1.19252, 1.19256] fresh=False bias_agrees=True distance_ratio=3.0232558139520833
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.43023255813910255}}
A.6 competing hypotheses:
  - **bullish continuation with the UP daily bias** — for: daily bias UP; weekly bias UP; range position discount; 3 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bearish reversal / range fade** — for: 3 untaken pool(s) on that side; no opposite zone; against: daily bias is UP; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bullish** plan from the `fvg` zone `fvg:bullish:36107` was armed at 2021-06-28T08:00:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.19401` (touch of the zone edge nearest the trade direction), stop `1.1933` (far side of fvg), T1 `1.1942000000000002`, T2 `1.19442` (two targets existed), measured R:R T1 `0.268` / T2 `0.577`, half-spread at decision `9.99999999995449e-06`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-28T08:00:00+00:00  high 1.19419  low 1.19381  close 1.19384  state armed
  - 2021-06-28T08:05:00+00:00  high 1.19385  low 1.19337  close 1.19341  state triggered
  - 2021-06-28T08:10:00+00:00  high 1.19351  low 1.1931500000000002  close 1.19324  state triggered
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_stop` (stop_touched), R = -1.0352, exit price `1.1933` at bar 36120.
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
