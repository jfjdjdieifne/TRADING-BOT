# CASE 57 — EURUSD 5m, decision at 2021-06-17T06:25:00+00:00 (bar index 34083)

## A. AS OF t — only what existed at t
A.1 context: daily bias `DOWN`, weekly bias `DOWN`, resolved `DOWN`
A.2 dealing range: low `1.19733`, high `1.20062`, equilibrium `1.198975`, position `premium`, ratio `0.5137` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.20062` high `relative_equal_pair`, formed at bar 5759, age 28324 bars
  - `1.21347` high `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.19733` low `relative_equal_pair`, formed at bar 5759, age 28324 bars
A.4 concepts at t: swing `none confirmed on this bar`, FVG `none on this bar`, displacement `NO` (V-D-01, ratio 0.25000000000034694), sweep high `NO`, sweep low `NO`, structure shift `none`
A.5 candidate zones, ranked:
  - `fvg:bearish:34079` fvg [1.19893, 1.2000300000000002] fresh=False bias_agrees=True distance_ratio=0.13981762917930177
  - `fvg:bearish:34078` fvg [1.2001400000000002, 1.20029] fresh=False bias_agrees=True distance_ratio=0.36322188449842846
  - `fvg:bearish:33961` fvg [1.20033, 1.2005800000000002] fresh=False bias_agrees=True distance_ratio=0.4361702127659108
  - `fvg:bearish:33953` fvg [1.20155, 1.20158] fresh=False bias_agrees=True distance_ratio=0.7735562310029744
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.13981762917930177}}
A.6 competing hypotheses:
  - **bearish continuation with the DOWN daily bias** — for: daily bias DOWN; weekly bias DOWN; range position premium; 4 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bullish reversal / range fade** — for: 1 untaken pool(s) on that side; opposite zone exists; against: daily bias is DOWN; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bearish** plan from the `fvg` zone `fvg:bearish:34079` was armed at 2021-06-17T06:25:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.19893` (touch of the zone edge nearest the trade direction), stop `1.2000300000000002` (far side of fvg), T1 `1.19733`, T2 `None` (only one untaken opposing pool existed; T2 = None), measured R:R T1 `1.455` / T2 `None`, half-spread at decision `2.000000000002e-05`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-17T06:25:00+00:00  high 1.19935  low 1.19887  close 1.1990200000000002  state armed
  - 2021-06-17T06:30:00+00:00  high 1.19927  low 1.19867  close 1.1988  state triggered
  - 2021-06-17T06:35:00+00:00  high 1.19889  low 1.19853  close 1.19872  state triggered
  - 2021-06-17T06:40:00+00:00  high 1.1987800000000002  low 1.19798  close 1.19802  state triggered
  - 2021-06-17T06:45:00+00:00  high 1.1985100000000002  low 1.1979300000000002  close 1.19825  state triggered
  - 2021-06-17T06:50:00+00:00  high 1.1988  low 1.19812  close 1.19819  state triggered
  - 2021-06-17T06:55:00+00:00  high 1.19894  low 1.1982000000000002  close 1.19867  state triggered
  - 2021-06-17T07:00:00+00:00  high 1.19894  low 1.19811  close 1.19816  state triggered
  - 2021-06-17T07:05:00+00:00  high 1.19818  low 1.1970200000000002  close 1.1972  state triggered
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_target` (t1_touched), R = 1.4227, exit price `1.19733` at bar 34091.
B.4 a plan that never triggered is counted as expired, not as resolved.

## C. MECHANICAL RECOMPUTATION — counts only
  - risk_price: match
  - rr_t1_measured: match
  - stop_on_the_far_side: match
  - t1_ahead_of_entry: match
  - r_measured_from_prices: match
C.2 mismatches: 0 of 5 checks.
C.3 the numbers in A come from records already tagged with their source; this section only re-derives the arithmetic.

## D. FAULT LOCATOR — HYPOTHESIS
  - category: `none visible`
  - verdict: `settled_target`
  - evidence: T1 touched before the stop under the conservative rule
