# CASE 40 — EURUSD 5m, decision at 2021-06-15T06:00:00+00:00 (bar index 33502)

## A. AS OF t — only what existed at t
A.1 context: daily bias `UP`, weekly bias `DOWN`, resolved `UP`, **bias_conflict**
A.2 dealing range: low `1.21248`, high `1.21279`, equilibrium `1.2126350000000001`, position `discount`, ratio `0.3871` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.21279` high `relative_equal_pair`, formed at bar 5759, age 27743 bars
  - `1.2130500000000002` high `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.21248` low `relative_equal_pair`, formed at bar 5759, age 27743 bars
  - `1.21242` low `relative_equal_pair`, formed at bar 5759, age 27743 bars
  - `1.2124` low `relative_equal_pair`, formed at bar 5759, age 27743 bars
  - `1.21189` low `relative_equal_pair`, formed at bar 5759, age 27743 bars
  - `1.21162` low `relative_equal_pair`, formed at bar 5759, age 27743 bars
  - `1.2114600000000002` low `relative_equal_pair`, formed at bar 5759, age 27743 bars
A.4 concepts at t: swing `[{'side': 'high', 'price': 1.21279, 'level_index': 5758}]`, FVG `none on this bar`, displacement `YES` (V-D-01, ratio 0.7500000000011565), sweep high `NO`, sweep low `NO`, structure shift `none`
A.5 candidate zones, ranked:
  - `fvg:bullish:33501` fvg [1.21257, 1.21266] fresh=False bias_agrees=True distance_ratio=0.04838709677450547
  - `fvg:bullish:33476` fvg [1.21225, 1.21232] fresh=False bias_agrees=True distance_ratio=1.0161290322574523
  - `fvg:bullish:33473` fvg [1.2120700000000002, 1.21216] fresh=False bias_agrees=True distance_ratio=1.5645161290315996
  - `fvg:bullish:33457` fvg [1.21189, 1.2119300000000002] fresh=False bias_agrees=True distance_ratio=2.2258064516122102
  - `fvg:bullish:33453` fvg [1.21162, 1.21167] fresh=False bias_agrees=True distance_ratio=3.080645161290126
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.04838709677450547}}
A.6 competing hypotheses:
  - **bullish continuation with the UP daily bias** — for: daily bias UP; weekly bias DOWN; range position discount; 5 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bearish reversal / range fade** — for: 2 untaken pool(s) on that side; no opposite zone; against: daily bias is UP; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bullish** plan from the `fvg` zone `fvg:bullish:33501` was armed at 2021-06-15T06:00:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.21266` (touch of the zone edge nearest the trade direction), stop `1.21257` (far side of fvg), T1 `1.21279`, T2 `1.2130500000000002` (two targets existed), measured R:R T1 `1.444` / T2 `4.333`, half-spread at decision `4.999999999921734e-06`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-15T06:00:00+00:00  high 1.2127800000000002  low 1.2125400000000002  close 1.2126  state armed
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_stop` (stop_touched), R = -1.1111, exit price `1.21257` at bar 33502.
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
