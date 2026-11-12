# CASE 43 — EURUSD 5m, decision at 2021-06-16T06:10:00+00:00 (bar index 33792)

## A. AS OF t — only what existed at t
A.1 context: daily bias `UP`, weekly bias `DOWN`, resolved `UP`, **bias_conflict**
A.2 dealing range: low `1.21283`, high `1.2130800000000002`, equilibrium `1.212955`, position `discount`, ratio `-1.4` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.21473` high `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.2130800000000002` high `relative_equal_pair`, formed at bar 5759, age 28033 bars
  - `1.21013` low `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.2122000000000002` low `relative_equal_pair`, formed at bar 5759, age 28033 bars
  - `1.21206` low `relative_equal_pair`, formed at bar 5759, age 28033 bars
  - `1.21165` low `relative_equal_pair`, formed at bar 5759, age 28033 bars
A.4 concepts at t: swing `none confirmed on this bar`, FVG `none on this bar`, displacement `NO` (V-D-01, ratio 0.09374999999989159), sweep high `NO`, sweep low `NO`, structure shift `{'direction': 'DOWN', 'level': 1.21283, 'level_index': 5758}`
A.5 candidate zones, ranked:
  - `fvg:bullish:33771` fvg [1.21239, 1.21249] fresh=False bias_agrees=True distance_ratio=0.16000000000010658
  - `fvg:bullish:33758` fvg [1.21216, 1.21226] fresh=False bias_agrees=True distance_ratio=1.0800000000004975
  - `fvg:bullish:33754` fvg [1.21197, 1.2121000000000002] fresh=False bias_agrees=True distance_ratio=1.7799999999986322
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.16000000000010658}}
A.6 competing hypotheses:
  - **bullish continuation with the UP daily bias** — for: daily bias UP; weekly bias DOWN; range position discount; 3 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bearish reversal / range fade** — for: 2 untaken pool(s) on that side; opposite zone exists; against: daily bias is UP; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bullish** plan from the `fvg` zone `fvg:bullish:33771` was armed at 2021-06-16T06:10:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.21249` (touch of the zone edge nearest the trade direction), stop `1.21239` (far side of fvg), T1 `1.2130800000000002`, T2 `1.21473` (two targets existed), measured R:R T1 `5.9` / T2 `22.4`, half-spread at decision `5.000000000032756e-06`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-16T06:10:00+00:00  high 1.21265  low 1.21233  close 1.21248  state armed
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_stop` (stop_touched), R = -1.1, exit price `1.21239` at bar 33792.
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
