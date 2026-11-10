# CASE 91 — EURUSD 5m, decision at 2021-06-28T06:00:00+00:00 (bar index 36094)

## A. AS OF t — only what existed at t
A.1 context: daily bias `UP`, weekly bias `UP`, resolved `UP`
A.2 dealing range: low `1.19255`, high `1.19287`, equilibrium `1.19271`, position `discount`, ratio `-0.0625` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.19287` high `relative_equal_pair`, formed at bar 5759, age 30335 bars
  - `1.19381` high `relative_equal_pair`, formed at bar 5759, age 30335 bars
  - `1.19419` high `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.19225` low `relative_equal_pair`, formed at bar 5759, age 30335 bars
  - `1.19218` low `relative_equal_pair`, formed at bar 5759, age 30335 bars
  - `1.19216` low `relative_equal_pair`, formed at bar 5759, age 30335 bars
  - `1.19211` low `relative_equal_pair`, formed at bar 5759, age 30335 bars
  - `1.1920000000000002` low `relative_equal_pair`, formed at bar 5759, age 30335 bars
A.4 concepts at t: swing `none confirmed on this bar`, FVG `none on this bar`, displacement `NO` (V-D-01, ratio 0.13043478260854874), sweep high `NO`, sweep low `NO`, structure shift `{'direction': 'DOWN', 'level': 1.19255, 'level_index': 5758}`
A.5 candidate zones, ranked:
  - `fvg:bullish:36088` fvg [1.19252, 1.19256] fresh=False bias_agrees=True distance_ratio=0.031250000000195156
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.031250000000195156}}
A.6 competing hypotheses:
  - **bullish continuation with the UP daily bias** — for: daily bias UP; weekly bias UP; range position discount; 1 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bearish reversal / range fade** — for: 3 untaken pool(s) on that side; opposite zone exists; against: daily bias is UP; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bullish** plan from the `fvg` zone `fvg:bullish:36088` was armed at 2021-06-28T06:00:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.19256` (touch of the zone edge nearest the trade direction), stop `1.19252` (far side of fvg), T1 `1.19287`, T2 `1.19381` (two targets existed), measured R:R T1 `7.75` / T2 `31.25`, half-spread at decision `1.4999999999987246e-05`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-28T06:00:00+00:00  high 1.19276  low 1.1923  close 1.19253  state armed
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_stop` (stop_touched), R = -1.75, exit price `1.19252` at bar 36094.
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
