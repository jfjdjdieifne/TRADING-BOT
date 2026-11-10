# CASE 39 — EURUSD 5m, decision at 2021-06-14T08:55:00+00:00 (bar index 33249)

## A. AS OF t — only what existed at t
A.1 context: daily bias `UP`, weekly bias `DOWN`, resolved `UP`, **bias_conflict**
A.2 dealing range: low `1.21063`, high `1.21154`, equilibrium `1.2110850000000002`, position `discount`, ratio `0.2857` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.21154` high `relative_equal_pair`, formed at bar 5759, age 27490 bars
  - `1.21188` high `relative_equal_pair`, formed at bar 5759, age 27490 bars
  - `1.21206` high `relative_equal_pair`, formed at bar 5759, age 27490 bars
  - `1.21063` low `relative_equal_pair`, formed at bar 5759, age 27490 bars
  - `1.2094200000000002` low `relative_equal_pair`, formed at bar 5759, age 27490 bars
A.4 concepts at t: swing `none confirmed on this bar`, FVG `none on this bar`, displacement `YES` (V-D-01, ratio 0.9782608695655531), sweep high `NO`, sweep low `NO`, structure shift `none`
A.5 candidate zones, ranked:
  - `fvg:bullish:33232` fvg [1.21082, 1.21093] fresh=False bias_agrees=True distance_ratio=0.016483516483381075
  - `fvg:bullish:33230` fvg [1.21018, 1.2104] fresh=False bias_agrees=True distance_ratio=0.659340659340611
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.016483516483381075}}
A.6 competing hypotheses:
  - **bullish continuation with the UP daily bias** — for: daily bias UP; weekly bias DOWN; range position discount; 2 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bearish reversal / range fade** — for: 3 untaken pool(s) on that side; opposite zone exists; against: daily bias is UP; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bullish** plan from the `fvg` zone `fvg:bullish:33232` was armed at 2021-06-14T08:55:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.21093` (touch of the zone edge nearest the trade direction), stop `1.21082` (far side of fvg), T1 `1.21154`, T2 `1.21188` (two targets existed), measured R:R T1 `5.545` / T2 `8.636`, half-spread at decision `9.99999999995449e-06`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-14T08:55:00+00:00  high 1.21134  low 1.2108800000000002  close 1.21089  state armed
  - 2021-06-14T09:00:00+00:00  high 1.21138  low 1.2108500000000002  close 1.21135  state triggered
  - 2021-06-14T09:05:00+00:00  high 1.21154  low 1.21136  close 1.2113900000000002  state triggered
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_target` (t1_touched), R = 5.4091, exit price `1.21154` at bar 33251.
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
