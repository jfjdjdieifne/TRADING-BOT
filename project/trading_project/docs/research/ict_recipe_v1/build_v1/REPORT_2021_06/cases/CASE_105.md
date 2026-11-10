# CASE 105 — EURUSD 5m, decision at 2021-06-30T07:50:00+00:00 (bar index 36692)

## A. AS OF t — only what existed at t
A.1 context: daily bias `DOWN`, weekly bias `UP`, resolved `DOWN`, **bias_conflict**
A.2 dealing range: low `1.1893`, high `1.1903400000000002`, equilibrium `1.18982`, position `premium`, ratio `0.9135` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.1903400000000002` high `relative_equal_pair`, formed at bar 5759, age 30933 bars
  - `1.19079` high `relative_equal_pair`, formed at bar 5759, age 30933 bars
  - `1.1929500000000002` high `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.1909` high `relative_equal_pair`, formed at bar 5759, age 30933 bars
  - `1.1893` low `relative_equal_pair`, formed at bar 5759, age 30933 bars
  - `1.18775` low `higher_timeframe_extreme`, formed at bar -1, age None bars
A.4 concepts at t: swing `none confirmed on this bar`, FVG `none on this bar`, displacement `YES` (V-D-01, ratio 0.6749999999996809), sweep high `NO`, sweep low `NO`, structure shift `none`
A.5 candidate zones, ranked:
  - `fvg:bearish:36683` fvg [1.1900700000000002, 1.19047] fresh=False bias_agrees=True distance_ratio=0.0192307692306789
  - `fvg:bearish:36628` fvg [1.1906800000000002, 1.19077] fresh=False bias_agrees=True distance_ratio=0.4567307692307056
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.0192307692306789}}
A.6 competing hypotheses:
  - **bearish continuation with the DOWN daily bias** — for: daily bias DOWN; weekly bias UP; range position premium; 2 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bullish reversal / range fade** — for: 2 untaken pool(s) on that side; no opposite zone; against: daily bias is DOWN; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bearish** plan from the `fvg` zone `fvg:bearish:36683` was armed at 2021-06-30T07:50:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.1900700000000002` (touch of the zone edge nearest the trade direction), stop `1.19047` (far side of fvg), T1 `1.1893`, T2 `1.18775` (two targets existed), measured R:R T1 `1.925` / T2 `5.8`, half-spread at decision `1.4999999999987246e-05`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-30T07:50:00+00:00  high 1.19029  low 1.18989  close 1.19025  state armed
  - 2021-06-30T07:55:00+00:00  high 1.19049  low 1.19003  close 1.1900700000000002  state triggered
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_stop` (stop_touched), R = -1.0625, exit price `1.19047` at bar 36693.
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
