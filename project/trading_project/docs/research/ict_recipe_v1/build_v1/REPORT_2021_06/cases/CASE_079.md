# CASE 79 — EURUSD 5m, decision at 2021-06-23T08:45:00+00:00 (bar index 35263)

## A. AS OF t — only what existed at t
A.1 context: daily bias `UP`, weekly bias `DOWN`, resolved `UP`, **bias_conflict**
A.2 dealing range: low `1.19354`, high `1.19447`, equilibrium `1.194005`, position `discount`, ratio `0.2043` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.19447` high `relative_equal_pair`, formed at bar 5759, age 29504 bars
  - `1.1945400000000002` high `relative_equal_pair`, formed at bar 5759, age 29504 bars
  - `1.19526` high `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.19354` low `relative_equal_pair`, formed at bar 5759, age 29504 bars
  - `1.19296` low `relative_equal_pair`, formed at bar 5759, age 29504 bars
  - `1.18808` low `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.1921000000000002` low `relative_equal_pair`, formed at bar 5759, age 29504 bars
  - `1.19113` low `relative_equal_pair`, formed at bar 5759, age 29504 bars
A.4 concepts at t: swing `[{'side': 'low', 'price': 1.19354, 'level_index': 5758}]`, FVG `none on this bar`, displacement `NO` (V-D-01, ratio 0.26666666666702854), sweep high `NO`, sweep low `NO`, structure shift `none`
A.5 candidate zones, ranked:
  - `fvg:bullish:35254` fvg [1.19333, 1.1937300000000002] fresh=False bias_agrees=True distance_ratio=0.2150537634411041
  - `fvg:bullish:35249` fvg [1.1926100000000002, 1.19297] fresh=False bias_agrees=True distance_ratio=1.0107526881723536
  - `fvg:bullish:35228` fvg [1.1919700000000002, 1.19208] fresh=False bias_agrees=True distance_ratio=1.8333333333336517
  - `fvg:bullish:35227` fvg [1.1919000000000002, 1.19192] fresh=False bias_agrees=True distance_ratio=1.9569892473122568
  - `fvg:bullish:35226` fvg [1.19178, 1.1918300000000002] fresh=False bias_agrees=True distance_ratio=2.0698924731187467
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.2150537634411041}}
A.6 competing hypotheses:
  - **bullish continuation with the UP daily bias** — for: daily bias UP; weekly bias DOWN; range position discount; 5 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bearish reversal / range fade** — for: 3 untaken pool(s) on that side; no opposite zone; against: daily bias is UP; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bullish** plan from the `fvg` zone `fvg:bullish:35254` was armed at 2021-06-23T08:45:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.1937300000000002` (touch of the zone edge nearest the trade direction), stop `1.19333` (far side of fvg), T1 `1.19447`, T2 `1.1945400000000002` (two targets existed), measured R:R T1 `1.85` / T2 `2.025`, half-spread at decision `1.0000000000065512e-05`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-23T08:45:00+00:00  high 1.19404  low 1.1935900000000002  close 1.1937300000000002  state armed
  - 2021-06-23T08:50:00+00:00  high 1.1938000000000002  low 1.19357  close 1.1937000000000002  state triggered
  - 2021-06-23T08:55:00+00:00  high 1.1938300000000002  low 1.19325  close 1.19325  state triggered
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_stop` (stop_touched), R = -1.0375, exit price `1.19333` at bar 35265.
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
  - category: `stop`
  - verdict: `settled_stop`
  - evidence: the stop was touched before T1
