# CASE 52 — EURUSD 5m, decision at 2021-06-16T08:20:00+00:00 (bar index 33818)

## A. AS OF t — only what existed at t
A.1 context: daily bias `UP`, weekly bias `DOWN`, resolved `UP`, **bias_conflict**
A.2 dealing range: low `1.21266`, high `1.21337`, equilibrium `1.213015`, position `discount`, ratio `0.1831` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.21337` high `relative_equal_pair`, formed at bar 5759, age 28059 bars
  - `1.21347` high `relative_equal_pair`, formed at bar 5759, age 28059 bars
  - `1.21473` high `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.21266` low `relative_equal_pair`, formed at bar 5759, age 28059 bars
  - `1.21242` low `relative_equal_pair`, formed at bar 5759, age 28059 bars
  - `1.2118300000000002` low `relative_equal_pair`, formed at bar 5759, age 28059 bars
  - `1.21013` low `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.21165` low `relative_equal_pair`, formed at bar 5759, age 28059 bars
A.4 concepts at t: swing `none confirmed on this bar`, FVG `none on this bar`, displacement `NO` (V-D-01, ratio 0.4583333333335261), sweep high `NO`, sweep low `NO`, structure shift `none`
A.5 candidate zones, ranked:
  - `fvg:bullish:33812` fvg [1.21277, 1.21283] fresh=False bias_agrees=True distance_ratio=0.014084507042346022
  - `fvg:bullish:33807` fvg [1.2122700000000002, 1.21282] fresh=False bias_agrees=True distance_ratio=0.34507042253528836
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.014084507042346022}}
A.6 competing hypotheses:
  - **bullish continuation with the UP daily bias** — for: daily bias UP; weekly bias DOWN; range position discount; 2 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bearish reversal / range fade** — for: 3 untaken pool(s) on that side; no opposite zone; against: daily bias is UP; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bullish** plan from the `fvg` zone `fvg:bullish:33812` was armed at 2021-06-16T08:20:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.21283` (touch of the zone edge nearest the trade direction), stop `1.21277` (far side of fvg), T1 `1.21337`, T2 `1.21347` (two targets existed), measured R:R T1 `9.0` / T2 `10.667`, half-spread at decision `1.4999999999987246e-05`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-16T08:20:00+00:00  high 1.21301  low 1.21277  close 1.21279  state armed
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_stop` (stop_touched), R = -1.5, exit price `1.21277` at bar 33818.
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
