# CASE 96 — EURUSD 5m, decision at 2021-06-29T06:50:00+00:00 (bar index 36392)

## A. AS OF t — only what existed at t
A.1 context: daily bias `DOWN`, weekly bias `UP`, resolved `DOWN`, **bias_conflict**
A.2 dealing range: low `1.19151`, high `1.1923`, equilibrium `1.191905`, position `premium`, ratio `0.8228` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.1944400000000002` high `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.1923` high `relative_equal_pair`, formed at bar 5759, age 30633 bars
  - `1.19246` high `relative_equal_pair`, formed at bar 5759, age 30633 bars
  - `1.19151` low `relative_equal_pair`, formed at bar 5759, age 30633 bars
  - `1.19022` low `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.19101` low `relative_equal_pair`, formed at bar 5759, age 30633 bars
  - `1.19076` low `relative_equal_pair`, formed at bar 5759, age 30633 bars
A.4 concepts at t: swing `[{'side': 'low', 'price': 1.19151, 'level_index': 5758}]`, FVG `none on this bar`, displacement `YES` (V-D-01, ratio 0.875000000000347), sweep high `NO`, sweep low `NO`, structure shift `none`
A.5 candidate zones, ranked:
  - `fvg:bearish:36330` fvg [1.19206, 1.19216] fresh=False bias_agrees=True distance_ratio=0.0632911392406522
  - `fvg:bearish:36329` fvg [1.19221, 1.1922700000000002] fresh=False bias_agrees=True distance_ratio=0.10126582278465003
  - `fvg:bearish:36312` fvg [1.1926100000000002, 1.1927] fresh=False bias_agrees=True distance_ratio=0.6265822784813044
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.0632911392406522}}
A.6 competing hypotheses:
  - **bearish continuation with the DOWN daily bias** — for: daily bias DOWN; weekly bias UP; range position premium; 3 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bullish reversal / range fade** — for: 4 untaken pool(s) on that side; opposite zone exists; against: daily bias is DOWN; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bearish** plan from the `fvg` zone `fvg:bearish:36330` was armed at 2021-06-29T06:50:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.19206` (touch of the zone edge nearest the trade direction), stop `1.19216` (far side of fvg), T1 `1.19151`, T2 `1.19101` (two targets existed), measured R:R T1 `5.5` / T2 `10.5`, half-spread at decision `1.5000000000098268e-05`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-29T06:50:00+00:00  high 1.19222  low 1.1916600000000002  close 1.19216  state armed
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_stop` (stop_touched), R = -1.3, exit price `1.19216` at bar 36392.
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
