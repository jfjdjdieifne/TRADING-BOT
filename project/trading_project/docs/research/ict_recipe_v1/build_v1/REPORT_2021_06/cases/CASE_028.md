# CASE 28 — EURUSD 5m, decision at 2021-06-09T07:50:00+00:00 (bar index 32372)

## A. AS OF t — only what existed at t
A.1 context: daily bias `DOWN`, weekly bias `DOWN`, resolved `DOWN`
A.2 dealing range: low `1.2177`, high `1.21821`, equilibrium `1.217955`, position `premium`, ratio `0.5686` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.21843` high `relative_equal_pair`, formed at bar 5759, age 26613 bars
  - `1.21941` high `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.2177` low `relative_equal_pair`, formed at bar 5759, age 26613 bars
  - `1.2176` low `relative_equal_pair`, formed at bar 5759, age 26613 bars
  - `1.21642` low `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.21755` low `relative_equal_pair`, formed at bar 5759, age 26613 bars
A.4 concepts at t: swing `none confirmed on this bar`, FVG `none on this bar`, displacement `NO` (V-D-01, ratio 0.22727272727281903), sweep high `YES`, sweep low `NO`, structure shift `none`
A.5 candidate zones, ranked:
  - `sweep:high:None` sweep_level [1.21799, 1.21821] fresh=True bias_agrees=True distance_ratio=0.21568627450990635
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": true}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.21568627450990635}}
A.6 competing hypotheses:
  - **bearish continuation with the DOWN daily bias** — for: daily bias DOWN; weekly bias DOWN; range position premium; 1 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bullish reversal / range fade** — for: 4 untaken pool(s) on that side; opposite zone exists; against: daily bias is DOWN; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bearish** plan from the `sweep_level` zone `sweep:high:None` was armed at 2021-06-09T07:50:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.21799` (touch of the zone edge nearest the trade direction), stop `1.21821` (sweep wick), T1 `1.2177`, T2 `1.2176` (two targets existed), measured R:R T1 `1.318` / T2 `1.773`, half-spread at decision `9.99999999995449e-06`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-09T07:50:00+00:00  high 1.21823  low 1.2177900000000002  close 1.21799  state armed
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_stop` (stop_touched), R = -1.0909, exit price `1.21821` at bar 32372.
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
