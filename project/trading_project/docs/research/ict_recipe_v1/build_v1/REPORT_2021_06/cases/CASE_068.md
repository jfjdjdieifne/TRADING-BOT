# CASE 68 — EURUSD 5m, decision at 2021-06-18T08:25:00+00:00 (bar index 34395)

## A. AS OF t — only what existed at t
A.1 context: daily bias `DOWN`, weekly bias `DOWN`, resolved `DOWN`
A.2 dealing range: low `1.19108`, high `1.19198`, equilibrium `1.19153`, position `premium`, ratio `1.3889` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.20062` high `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.19108` low `relative_equal_pair`, formed at bar 5759, age 28636 bars
  - `1.18947` low `relative_equal_pair`, formed at bar 5759, age 28636 bars
  - `1.18916` low `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.18941` low `relative_equal_pair`, formed at bar 5759, age 28636 bars
  - `1.18853` low `relative_equal_pair`, formed at bar 5759, age 28636 bars
A.4 concepts at t: swing `none confirmed on this bar`, FVG `none on this bar`, displacement `YES` (V-D-01, ratio 0.8412698412694832), sweep high `NO`, sweep low `NO`, structure shift `{'direction': 'UP', 'level': 1.19198, 'level_index': 5758}`
A.5 candidate zones, ranked:
  - `fvg:bearish:34338` fvg [1.19232, 1.19235] fresh=False bias_agrees=True distance_ratio=0.005555555555591192
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.005555555555591192}}
A.6 competing hypotheses:
  - **bearish continuation with the DOWN daily bias** — for: daily bias DOWN; weekly bias DOWN; range position premium; 1 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bullish reversal / range fade** — for: 5 untaken pool(s) on that side; opposite zone exists; against: daily bias is DOWN; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bearish** plan from the `fvg` zone `fvg:bearish:34338` was armed at 2021-06-18T08:25:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.19232` (touch of the zone edge nearest the trade direction), stop `1.19235` (far side of fvg), T1 `1.19108`, T2 `1.18947` (two targets existed), measured R:R T1 `41.333` / T2 `95.0`, half-spread at decision `4.999999999921734e-06`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-18T08:25:00+00:00  high 1.19243  low 1.1918000000000002  close 1.19233  state armed
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_stop` (stop_touched), R = -1.3333, exit price `1.19235` at bar 34395.
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
