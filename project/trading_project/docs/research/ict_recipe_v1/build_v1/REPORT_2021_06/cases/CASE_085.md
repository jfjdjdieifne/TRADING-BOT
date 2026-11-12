# CASE 85 — EURUSD 5m, decision at 2021-06-24T06:45:00+00:00 (bar index 35527)

## A. AS OF t — only what existed at t
A.1 context: daily bias `DOWN`, weekly bias `DOWN`, resolved `DOWN`
A.2 dealing range: low `1.19294`, high `1.19355`, equilibrium `1.1932450000000001`, position `premium`, ratio `0.5738` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.19355` high `relative_equal_pair`, formed at bar 5759, age 29768 bars
  - `1.197` high `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.19294` low `relative_equal_pair`, formed at bar 5759, age 29768 bars
  - `1.19257` low `relative_equal_pair`, formed at bar 5759, age 29768 bars
  - `1.1917600000000002` low `relative_equal_pair`, formed at bar 5759, age 29768 bars
  - `1.19113` low `higher_timeframe_extreme`, formed at bar -1, age None bars
A.4 concepts at t: swing `[{'side': 'low', 'price': 1.19294, 'level_index': 5758}]`, FVG `none on this bar`, displacement `NO` (V-D-01, ratio 0.11904761904731695), sweep high `NO`, sweep low `NO`, structure shift `none`
A.5 candidate zones, ranked:
  - `fvg:bearish:35381` fvg [1.19317, 1.19338] fresh=False bias_agrees=True distance_ratio=0.024590163934578396
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.024590163934578396}}
A.6 competing hypotheses:
  - **bearish continuation with the DOWN daily bias** — for: daily bias DOWN; weekly bias DOWN; range position premium; 1 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bullish reversal / range fade** — for: 4 untaken pool(s) on that side; opposite zone exists; against: daily bias is DOWN; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bearish** plan from the `fvg` zone `fvg:bearish:35381` was armed at 2021-06-24T06:45:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.19317` (touch of the zone edge nearest the trade direction), stop `1.19338` (far side of fvg), T1 `1.19294`, T2 `1.19257` (two targets existed), measured R:R T1 `1.095` / T2 `2.857`, half-spread at decision `2.000000000002e-05`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-24T06:45:00+00:00  high 1.19343  low 1.19301  close 1.1932900000000002  state armed
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_stop` (stop_touched), R = -1.1905, exit price `1.19338` at bar 35527.
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
