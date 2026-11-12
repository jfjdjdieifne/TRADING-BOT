# CASE 95 — EURUSD 5m, decision at 2021-06-28T08:05:00+00:00 (bar index 36119)

## A. AS OF t — only what existed at t
A.1 context: daily bias `UP`, weekly bias `UP`, resolved `UP`
A.2 dealing range: low `1.19377`, high `1.1942000000000002`, equilibrium `1.193985`, position `discount`, ratio `-0.8372` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.1942000000000002` high `relative_equal_pair`, formed at bar 5759, age 30360 bars
  - `1.19442` high `relative_equal_pair`, formed at bar 5759, age 30360 bars
  - `1.1944400000000002` high `relative_equal_pair`, formed at bar 5759, age 30360 bars
  - `1.1927500000000002` low `relative_equal_pair`, formed at bar 5759, age 30360 bars
  - `1.19236` low `relative_equal_pair`, formed at bar 5759, age 30360 bars
  - `1.1923` low `relative_equal_pair`, formed at bar 5759, age 30360 bars
  - `1.19225` low `relative_equal_pair`, formed at bar 5759, age 30360 bars
  - `1.19218` low `relative_equal_pair`, formed at bar 5759, age 30360 bars
A.4 concepts at t: swing `none confirmed on this bar`, FVG `none on this bar`, displacement `YES` (V-D-01, ratio 0.8750000000001157), sweep high `NO`, sweep low `NO`, structure shift `{'direction': 'DOWN', 'level': 1.19377, 'level_index': 5758}`
A.5 candidate zones, ranked:
  - `fvg:bullish:36107` fvg [1.1933, 1.19401] fresh=False bias_agrees=True distance_ratio=0.5697674418603811
  - `fvg:bullish:36100` fvg [1.19286, 1.19296] fresh=False bias_agrees=True distance_ratio=1.1627906976743947
  - `fvg:bullish:36088` fvg [1.19252, 1.19256] fresh=False bias_agrees=True distance_ratio=2.0232558139526
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.5697674418603811}}
A.6 competing hypotheses:
  - **bullish continuation with the UP daily bias** — for: daily bias UP; weekly bias UP; range position discount; 3 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bearish reversal / range fade** — for: 3 untaken pool(s) on that side; no opposite zone; against: daily bias is UP; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bullish** plan from the `fvg` zone `fvg:bullish:36107` was armed at 2021-06-28T08:05:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.19401` (touch of the zone edge nearest the trade direction), stop `1.1933` (far side of fvg), T1 `1.1942000000000002`, T2 `1.19442` (two targets existed), measured R:R T1 `0.268` / T2 `0.577`, half-spread at decision `1.999999999990898e-05`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-28T08:05:00+00:00  high 1.19385  low 1.19337  close 1.19341  state armed
  - 2021-06-28T08:10:00+00:00  high 1.19351  low 1.1931500000000002  close 1.19324  state armed
  - 2021-06-28T08:15:00+00:00  high 1.19335  low 1.1927  close 1.19272  state armed
  - 2021-06-28T08:20:00+00:00  high 1.19286  low 1.19255  close 1.19282  state armed
  - 2021-06-28T08:25:00+00:00  high 1.19303  low 1.1927500000000002  close 1.19291  state armed
  - 2021-06-28T08:30:00+00:00  high 1.19325  low 1.1929  close 1.19325  state armed
  - 2021-06-28T08:35:00+00:00  high 1.19352  low 1.1931200000000002  close 1.1931500000000002  state armed
  - 2021-06-28T08:40:00+00:00  high 1.1933600000000002  low 1.19314  close 1.19334  state armed
  - 2021-06-28T08:45:00+00:00  high 1.19411  low 1.19334  close 1.19405  state armed
  - 2021-06-28T08:50:00+00:00  high 1.1940700000000002  low 1.19364  close 1.19372  state triggered
  - 2021-06-28T08:55:00+00:00  high 1.19428  low 1.1937000000000002  close 1.19412  state triggered
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_target` (t1_touched), R = 0.2254, exit price `1.1942000000000002` at bar 36129.
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
