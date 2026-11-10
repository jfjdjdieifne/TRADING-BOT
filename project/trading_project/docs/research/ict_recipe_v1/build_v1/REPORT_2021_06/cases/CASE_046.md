# CASE 46 — EURUSD 5m, decision at 2021-06-16T06:55:00+00:00 (bar index 33801)

## A. AS OF t — only what existed at t
A.1 context: daily bias `UP`, weekly bias `DOWN`, resolved `UP`, **bias_conflict**
A.2 dealing range: low `1.21267`, high `1.21347`, equilibrium `1.21307`, position `discount`, ratio `0.325` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.21347` high `relative_equal_pair`, formed at bar 5759, age 28042 bars
  - `1.21473` high `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.21267` low `relative_equal_pair`, formed at bar 5759, age 28042 bars
  - `1.2122700000000002` low `relative_equal_pair`, formed at bar 5759, age 28042 bars
  - `1.21013` low `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.2122000000000002` low `relative_equal_pair`, formed at bar 5759, age 28042 bars
  - `1.21206` low `relative_equal_pair`, formed at bar 5759, age 28042 bars
  - `1.21165` low `relative_equal_pair`, formed at bar 5759, age 28042 bars
A.4 concepts at t: swing `[{'side': 'low', 'price': 1.21267, 'level_index': 5758}]`, FVG `none on this bar`, displacement `NO` (V-D-01, ratio 0.3902439024393942), sweep high `NO`, sweep low `NO`, structure shift `none`
A.5 candidate zones, ranked:
  - `fvg:bullish:33797` fvg [1.2126800000000002, 1.2129500000000002] fresh=False bias_agrees=True distance_ratio=0.14374999999980745
  - `fvg:bullish:33796` fvg [1.21255, 1.2126100000000002] fresh=False bias_agrees=True distance_ratio=0.4375000000000173
  - `fvg:bullish:33795` fvg [1.21248, 1.21252] fresh=False bias_agrees=True distance_ratio=0.5375000000001006
  - `fvg:bullish:33771` fvg [1.21239, 1.21249] fresh=False bias_agrees=True distance_ratio=0.6125000000000242
  - `fvg:bullish:33758` fvg [1.21216, 1.21226] fresh=False bias_agrees=True distance_ratio=0.9000000000001943
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.14374999999980745}}
A.6 competing hypotheses:
  - **bullish continuation with the UP daily bias** — for: daily bias UP; weekly bias DOWN; range position discount; 6 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bearish reversal / range fade** — for: 2 untaken pool(s) on that side; opposite zone exists; against: daily bias is UP; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bullish** plan from the `fvg` zone `fvg:bullish:33797` was armed at 2021-06-16T06:55:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.2129500000000002` (touch of the zone edge nearest the trade direction), stop `1.2126800000000002` (far side of fvg), T1 `1.21347`, T2 `1.21473` (two targets existed), measured R:R T1 `1.926` / T2 `6.593`, half-spread at decision `1.4999999999987246e-05`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-16T06:55:00+00:00  high 1.21317  low 1.21276  close 1.21293  state armed
  - 2021-06-16T07:00:00+00:00  high 1.21297  low 1.21239  close 1.21245  state triggered
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_stop` (stop_touched), R = -1.0741, exit price `1.2126800000000002` at bar 33802.
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
