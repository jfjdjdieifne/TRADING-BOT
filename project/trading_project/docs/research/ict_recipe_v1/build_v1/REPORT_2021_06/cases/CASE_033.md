# CASE 33 — EURUSD 5m, decision at 2021-06-11T07:40:00+00:00 (bar index 32946)

## A. AS OF t — only what existed at t
A.1 context: daily bias `DOWN`, weekly bias `DOWN`, resolved `DOWN`
A.2 dealing range: low `1.2174600000000002`, high `1.21873`, equilibrium `1.2180950000000001`, position `premium`, ratio `0.5827` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.21873` high `relative_equal_pair`, formed at bar 5759, age 27187 bars
  - `1.21945` high `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.2191800000000002` high `relative_equal_pair`, formed at bar 5759, age 27187 bars
  - `1.2192900000000002` high `relative_equal_pair`, formed at bar 5759, age 27187 bars
  - `1.2174600000000002` low `relative_equal_pair`, formed at bar 5759, age 27187 bars
  - `1.21433` low `higher_timeframe_extreme`, formed at bar -1, age None bars
A.4 concepts at t: swing `none confirmed on this bar`, FVG `[{'direction': 'bullish', 'lower': 1.2179000000000002, 'upper': 1.21792, 'level_index': 5759, 'version': 'V-B-00', 'invalidation': 'KNOWLEDGE_GAP: FVG_INVALIDATION', 'gates': ['INVALIDATION_UNDECIDED']}]`, displacement `NO` (V-D-01, ratio 0.3777777777775475), sweep high `NO`, sweep low `NO`, structure shift `none`
A.5 candidate zones, ranked:
  - `fvg:bearish:32944` fvg [1.2179000000000002, 1.21839] fresh=False bias_agrees=True distance_ratio=0.04330708661411128
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.04330708661411128}}
A.6 competing hypotheses:
  - **bearish continuation with the DOWN daily bias** — for: daily bias DOWN; weekly bias DOWN; range position premium; 1 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bullish reversal / range fade** — for: 2 untaken pool(s) on that side; opposite zone exists; against: daily bias is DOWN; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bearish** plan from the `fvg` zone `fvg:bearish:32944` was armed at 2021-06-11T07:40:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.2179000000000002` (touch of the zone edge nearest the trade direction), stop `1.21839` (far side of fvg), T1 `1.2174600000000002`, T2 `1.21433` (two targets existed), measured R:R T1 `0.898` / T2 `7.286`, half-spread at decision `4.999999999921734e-06`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-11T07:40:00+00:00  high 1.2183700000000002  low 1.21792  close 1.2182000000000002  state armed
  - 2021-06-11T07:45:00+00:00  high 1.21849  low 1.21798  close 1.21848  state armed
  - 2021-06-11T07:50:00+00:00  high 1.21869  low 1.21832  close 1.2183400000000002  state armed
  - 2021-06-11T07:55:00+00:00  high 1.21846  low 1.21823  close 1.21828  state armed
  - 2021-06-11T08:00:00+00:00  high 1.21835  low 1.21797  close 1.21823  state armed
  - 2021-06-11T08:05:00+00:00  high 1.21829  low 1.2177  close 1.21809  state armed
  - 2021-06-11T08:10:00+00:00  high 1.21831  low 1.2178300000000002  close 1.21784  state triggered
  - 2021-06-11T08:15:00+00:00  high 1.21809  low 1.2177300000000002  close 1.21774  state triggered
  - 2021-06-11T08:20:00+00:00  high 1.2179600000000002  low 1.2174600000000002  close 1.2174900000000002  state triggered
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_target` (t1_touched), R = 0.8776, exit price `1.2174600000000002` at bar 32954.
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
  - category: `none visible`
  - verdict: `settled_target`
  - evidence: T1 touched before the stop under the conservative rule
