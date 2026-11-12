# CASE 9 — EURUSD 5m, decision at 2021-06-04T06:00:00+00:00 (bar index 31486)

## A. AS OF t — only what existed at t
A.1 context: daily bias `DOWN`, weekly bias `UP`, resolved `DOWN`, **bias_conflict**
A.2 dealing range: low `1.2105`, high `1.21097`, equilibrium `1.2107350000000001`, position `premium`, ratio `0.7021` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.21144` high `relative_equal_pair`, formed at bar 5759, age 25727 bars
  - `1.21162` high `relative_equal_pair`, formed at bar 5759, age 25727 bars
  - `1.21178` high `relative_equal_pair`, formed at bar 5759, age 25727 bars
  - `1.21184` high `relative_equal_pair`, formed at bar 5759, age 25727 bars
  - `1.21215` high `relative_equal_pair`, formed at bar 5759, age 25727 bars
  - `1.2128500000000002` high `relative_equal_pair`, formed at bar 5759, age 25727 bars
  - `1.2130200000000002` high `relative_equal_pair`, formed at bar 5759, age 25727 bars
  - `1.22141` high `higher_timeframe_extreme`, formed at bar -1, age None bars
A.4 concepts at t: swing `[{'side': 'low', 'price': 1.2105, 'level_index': 5758}]`, FVG `none on this bar`, displacement `NO` (V-D-01, ratio 0.37499999999972244), sweep high `YES`, sweep low `NO`, structure shift `none`
A.5 candidate zones, ranked:
  - `sweep:high:None` sweep_level [1.21083, 1.21097] fresh=True bias_agrees=True distance_ratio=0.1489361702127358
  - `fvg:bearish:31480` fvg [1.21123, 1.21127] fresh=False bias_agrees=True distance_ratio=0.8936170212764148
  - `fvg:bearish:31473` fvg [1.21136, 1.21147] fresh=False bias_agrees=True distance_ratio=1.2446808510634428
  - `fvg:bearish:31462` fvg [1.21154, 1.2115600000000002] fresh=False bias_agrees=True distance_ratio=1.5319148936165086
  - `fvg:bearish:31453` fvg [1.21184, 1.21188] fresh=False bias_agrees=True distance_ratio=2.191489361701414
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": true}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.1489361702127358}}
A.6 competing hypotheses:
  - **bearish continuation with the DOWN daily bias** — for: daily bias DOWN; weekly bias UP; range position premium; 12 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bullish reversal / range fade** — for: 1 untaken pool(s) on that side; no opposite zone; against: daily bias is DOWN; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bearish** plan from the `sweep_level` zone `sweep:high:None` was armed at 2021-06-04T06:00:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.21083` (touch of the zone edge nearest the trade direction), stop `1.21097` (sweep wick), T1 `1.2105`, T2 `None` (only one untaken opposing pool existed; T2 = None), measured R:R T1 `2.357` / T2 `None`, half-spread at decision `9.99999999995449e-06`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-04T06:00:00+00:00  high 1.21099  low 1.21059  close 1.21083  state armed
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_stop` (stop_touched), R = -1.1429, exit price `1.21097` at bar 31486.
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
  - category: `execution assumption / stop`
  - verdict: `settled_stop`
  - evidence: the triggering bar spanned the whole zone, so the conservative stop-first rule settles it on the entry bar
