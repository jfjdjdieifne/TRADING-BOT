# CASE 2 — EURUSD 5m, decision at 2021-06-02T06:25:00+00:00 (bar index 30915)

## A. AS OF t — only what existed at t
A.1 context: daily bias `DOWN`, weekly bias `UP`, resolved `DOWN`, **bias_conflict**
A.2 dealing range: low `1.2210500000000002`, high `1.22158`, equilibrium `1.2213150000000002`, position `premium`, ratio `1.0189` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.2254200000000002` high `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.22194` high `relative_equal_pair`, formed at bar 5759, age 25156 bars
  - `1.2219600000000002` high `relative_equal_pair`, formed at bar 5759, age 25156 bars
  - `1.22206` high `relative_equal_pair`, formed at bar 5759, age 25156 bars
  - `1.22211` high `relative_equal_pair`, formed at bar 5759, age 25156 bars
  - `1.22218` high `relative_equal_pair`, formed at bar 5759, age 25156 bars
  - `1.2223000000000002` high `relative_equal_pair`, formed at bar 5759, age 25156 bars
  - `1.22231` high `relative_equal_pair`, formed at bar 5759, age 25156 bars
A.4 concepts at t: swing `none confirmed on this bar`, FVG `none on this bar`, displacement `YES` (V-D-01, ratio 0.7254901960783802), sweep high `NO`, sweep low `NO`, structure shift `{'direction': 'UP', 'level': 1.22158, 'level_index': 5758}`
A.5 candidate zones, ranked:
  - `fvg:bearish:30910` fvg [1.2215200000000002, 1.22182] fresh=False bias_agrees=True distance_ratio=0.15094339622617003
  - `fvg:bearish:30896` fvg [1.22188, 1.22198] fresh=False bias_agrees=True distance_ratio=0.6415094339619558
  - `fvg:bearish:30880` fvg [1.22223, 1.2224000000000002] fresh=False bias_agrees=True distance_ratio=1.3679245283018393
  - `fvg:bearish:30780` fvg [1.2226100000000002, 1.2226400000000002] fresh=False bias_agrees=True distance_ratio=1.952830188679767
  - `fvg:bearish:30779` fvg [1.2226400000000002, 1.22265] fresh=False bias_agrees=True distance_ratio=1.9905660377357859
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.15094339622617003}}
A.6 competing hypotheses:
  - **bearish continuation with the DOWN daily bias** — for: daily bias DOWN; weekly bias UP; range position premium; 11 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bullish reversal / range fade** — for: 1 untaken pool(s) on that side; no opposite zone; against: daily bias is DOWN; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bearish** plan from the `fvg` zone `fvg:bearish:30910` was armed at 2021-06-02T06:25:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.2215200000000002` (touch of the zone edge nearest the trade direction), stop `1.22182` (far side of fvg), T1 `1.2210500000000002`, T2 `None` (only one untaken opposing pool existed; T2 = None), measured R:R T1 `1.567` / T2 `None`, half-spread at decision `1.999999999990898e-05`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-02T06:25:00+00:00  high 1.2215900000000002  low 1.2210800000000002  close 1.2215900000000002  state armed
  - 2021-06-02T06:30:00+00:00  high 1.2217900000000002  low 1.22153  close 1.22163  state triggered
  - 2021-06-02T06:35:00+00:00  high 1.22167  low 1.22066  close 1.2209800000000002  state triggered
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_target` (t1_touched), R = 1.4667, exit price `1.2210500000000002` at bar 30917.
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
