# CASE 1 — EURUSD 5m, decision at 2021-06-01T06:10:00+00:00 (bar index 30624)

## A. AS OF t — only what existed at t
A.1 context: daily bias `UP`, weekly bias `UP`, resolved `UP`
A.2 dealing range: low `1.22181`, high `1.2227100000000002`, equilibrium `1.2222600000000001`, position `discount`, ratio `0.3222` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.2227100000000002` high `relative_equal_pair`, formed at bar 5759, age 24865 bars
  - `1.22272` high `relative_equal_pair`, formed at bar 5759, age 24865 bars
  - `1.2232` high `relative_equal_pair`, formed at bar 5759, age 24865 bars
  - `1.22321` high `relative_equal_pair`, formed at bar 5759, age 24865 bars
  - `1.22357` high `relative_equal_pair`, formed at bar 5759, age 24865 bars
  - `1.22364` high `relative_equal_pair`, formed at bar 5759, age 24865 bars
  - `1.22181` low `relative_equal_pair`, formed at bar 5759, age 24865 bars
  - `1.21832` low `higher_timeframe_extreme`, formed at bar -1, age None bars
A.4 concepts at t: swing `[{'side': 'high', 'price': 1.2227100000000002, 'level_index': 5758}]`, FVG `[{'direction': 'bearish', 'lower': 1.2222700000000002, 'upper': 1.2224400000000002, 'level_index': 5759, 'version': 'V-B-00', 'invalidation': 'KNOWLEDGE_GAP: FVG_INVALIDATION', 'gates': ['INVALIDATION_UNDECIDED']}]`, displacement `NO` (V-D-01, ratio 0.09999999999985197), sweep high `NO`, sweep low `NO`, structure shift `none`
A.5 candidate zones, ranked:
  - `fvg:bullish:30620` fvg [1.22198, 1.2222000000000002] fresh=False bias_agrees=True distance_ratio=0.011111111111182384
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.011111111111182384}}
A.6 competing hypotheses:
  - **bullish continuation with the UP daily bias** — for: daily bias UP; weekly bias UP; range position discount; 1 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bearish reversal / range fade** — for: 6 untaken pool(s) on that side; opposite zone exists; against: daily bias is UP; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bullish** plan from the `fvg` zone `fvg:bullish:30620` was armed at 2021-06-01T06:10:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.2222000000000002` (touch of the zone edge nearest the trade direction), stop `1.22198` (far side of fvg), T1 `1.2227100000000002`, T2 `1.22272` (two targets existed), measured R:R T1 `2.318` / T2 `2.364`, half-spread at decision `1.4999999999987246e-05`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-01T06:10:00+00:00  high 1.2222700000000002  low 1.22197  close 1.2221000000000002  state armed
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_stop` (stop_touched), R = -1.1364, exit price `1.22198` at bar 30624.
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
