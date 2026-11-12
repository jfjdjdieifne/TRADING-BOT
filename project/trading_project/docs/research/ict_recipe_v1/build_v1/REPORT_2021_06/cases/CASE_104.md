# CASE 104 — EURUSD 5m, decision at 2021-06-30T06:55:00+00:00 (bar index 36681)

## A. AS OF t — only what existed at t
A.1 context: daily bias `DOWN`, weekly bias `UP`, resolved `DOWN`, **bias_conflict**
A.2 dealing range: low `1.1900000000000002`, high `1.19052`, equilibrium `1.19026`, position `premium`, ratio `0.9038` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.1929500000000002` high `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.1909` high `relative_equal_pair`, formed at bar 5759, age 30922 bars
  - `1.18775` low `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.1900000000000002` low `relative_equal_pair`, formed at bar 5759, age 30922 bars
  - `1.1898700000000002` low `relative_equal_pair`, formed at bar 5759, age 30922 bars
  - `1.1894` low `relative_equal_pair`, formed at bar 5759, age 30922 bars
A.4 concepts at t: swing `none confirmed on this bar`, FVG `[{'direction': 'bullish', 'lower': 1.1904100000000002, 'upper': 1.19047, 'level_index': 5759, 'version': 'V-B-00', 'invalidation': 'KNOWLEDGE_GAP: FVG_INVALIDATION', 'gates': ['INVALIDATION_UNDECIDED']}]`, displacement `NO` (V-D-01, ratio 0.34375000000075895), sweep high `YES`, sweep low `NO`, structure shift `none`
A.5 candidate zones, ranked:
  - `sweep:high:None` sweep_level [1.19047, 1.19052] fresh=True bias_agrees=True distance_ratio=0.04807692307682453
  - `fvg:bearish:36628` fvg [1.1906800000000002, 1.19077] fresh=False bias_agrees=True distance_ratio=0.4903846153849767
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": true}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.04807692307682453}}
A.6 competing hypotheses:
  - **bearish continuation with the DOWN daily bias** — for: daily bias DOWN; weekly bias UP; range position premium; 2 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bullish reversal / range fade** — for: 4 untaken pool(s) on that side; opposite zone exists; against: daily bias is DOWN; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bearish** plan from the `sweep_level` zone `sweep:high:None` was armed at 2021-06-30T06:55:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.19047` (touch of the zone edge nearest the trade direction), stop `1.19052` (sweep wick), T1 `1.1900000000000002`, T2 `1.1898700000000002` (two targets existed), measured R:R T1 `9.4` / T2 `12.0`, half-spread at decision `4.999999999921734e-06`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-30T06:55:00+00:00  high 1.19079  low 1.19047  close 1.19047  state armed
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_stop` (stop_touched), R = -1.2, exit price `1.19052` at bar 36681.
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
