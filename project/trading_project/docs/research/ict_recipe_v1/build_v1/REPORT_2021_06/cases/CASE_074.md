# CASE 74 — EURUSD 5m, decision at 2021-06-23T06:55:00+00:00 (bar index 35241)

## A. AS OF t — only what existed at t
A.1 context: daily bias `UP`, weekly bias `DOWN`, resolved `UP`, **bias_conflict**
A.2 dealing range: low `1.19221`, high `1.1937000000000002`, equilibrium `1.192955`, position `discount`, ratio `0.3557` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.1937000000000002` high `relative_equal_pair`, formed at bar 5759, age 29482 bars
  - `1.19398` high `relative_equal_pair`, formed at bar 5759, age 29482 bars
  - `1.19526` high `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.19421` high `relative_equal_pair`, formed at bar 5759, age 29482 bars
  - `1.19221` low `relative_equal_pair`, formed at bar 5759, age 29482 bars
  - `1.19159` low `relative_equal_pair`, formed at bar 5759, age 29482 bars
  - `1.18808` low `higher_timeframe_extreme`, formed at bar -1, age None bars
A.4 concepts at t: swing `none confirmed on this bar`, FVG `none on this bar`, displacement `NO` (V-D-01, ratio 0.5058823529414777), sweep high `NO`, sweep low `NO`, structure shift `none`
A.5 candidate zones, ranked:
  - `fvg:bullish:35237` fvg [1.19267, 1.19276] fresh=False bias_agrees=True distance_ratio=0.01677852348989138
  - `fvg:bullish:35236` fvg [1.1924800000000002, 1.19266] fresh=False bias_agrees=True distance_ratio=0.1140939597313806
  - `fvg:bullish:35229` fvg [1.19212, 1.19263] fresh=False bias_agrees=True distance_ratio=0.2449664429528016
  - `fvg:bullish:35228` fvg [1.1919700000000002, 1.19208] fresh=False bias_agrees=True distance_ratio=0.479865771811877
  - `fvg:bullish:35227` fvg [1.1919000000000002, 1.19192] fresh=False bias_agrees=True distance_ratio=0.5570469798656158
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.01677852348989138}}
A.6 competing hypotheses:
  - **bullish continuation with the UP daily bias** — for: daily bias UP; weekly bias DOWN; range position discount; 6 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bearish reversal / range fade** — for: 4 untaken pool(s) on that side; opposite zone exists; against: daily bias is UP; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bullish** plan from the `fvg` zone `fvg:bullish:35237` was armed at 2021-06-23T06:55:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.19276` (touch of the zone edge nearest the trade direction), stop `1.19267` (far side of fvg), T1 `1.1937000000000002`, T2 `1.19398` (two targets existed), measured R:R T1 `10.444` / T2 `13.556`, half-spread at decision `1.4999999999987246e-05`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-23T06:55:00+00:00  high 1.19326  low 1.1924100000000002  close 1.19274  state armed
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_stop` (stop_touched), R = -1.3333, exit price `1.19267` at bar 35241.
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
