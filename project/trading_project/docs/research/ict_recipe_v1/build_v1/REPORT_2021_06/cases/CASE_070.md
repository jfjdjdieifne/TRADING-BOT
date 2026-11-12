# CASE 70 — EURUSD 5m, decision at 2021-06-21T08:20:00+00:00 (bar index 34682)

## A. AS OF t — only what existed at t
A.1 context: daily bias `UP`, weekly bias `DOWN`, resolved `UP`, **bias_conflict**
A.2 dealing range: low `1.1879000000000002`, high `1.18911`, equilibrium `1.1885050000000001`, position `discount`, ratio `0.4876` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.18911` high `relative_equal_pair`, formed at bar 5759, age 28923 bars
  - `1.1879000000000002` low `relative_equal_pair`, formed at bar 5759, age 28923 bars
  - `1.18511` low `relative_equal_pair`, formed at bar 5759, age 28923 bars
  - `1.18476` low `relative_equal_pair`, formed at bar 5759, age 28923 bars
A.4 concepts at t: swing `none confirmed on this bar`, FVG `none on this bar`, displacement `YES` (V-D-01, ratio 0.675675675675335), sweep high `NO`, sweep low `NO`, structure shift `none`
A.5 candidate zones, ranked:
  - `fvg:bullish:34680` fvg [1.1884800000000002, 1.18853] fresh=False bias_agrees=True distance_ratio=0.012396694214960204
  - `fvg:bullish:34676` fvg [1.18769, 1.1878000000000002] fresh=False bias_agrees=True distance_ratio=0.6157024793389863
  - `fvg:bullish:34674` fvg [1.1871, 1.1871200000000002] fresh=False bias_agrees=True distance_ratio=1.1404958677688148
  - `fvg:bullish:34673` fvg [1.1861700000000002, 1.18691] fresh=False bias_agrees=True distance_ratio=1.6115702479343665
  - `fvg:bullish:34672` fvg [1.18561, 1.18603] fresh=False bias_agrees=True distance_ratio=2.2066115702484193
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.012396694214960204}}
A.6 competing hypotheses:
  - **bullish continuation with the UP daily bias** — for: daily bias UP; weekly bias DOWN; range position discount; 6 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bearish reversal / range fade** — for: 1 untaken pool(s) on that side; no opposite zone; against: daily bias is UP; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bullish** plan from the `fvg` zone `fvg:bullish:34680` was armed at 2021-06-21T08:20:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.18853` (touch of the zone edge nearest the trade direction), stop `1.1884800000000002` (far side of fvg), T1 `1.18911`, T2 `None` (only one untaken opposing pool existed; T2 = None), measured R:R T1 `11.6` / T2 `None`, half-spread at decision `1.4999999999987246e-05`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-21T08:20:00+00:00  high 1.18879  low 1.18842  close 1.18849  state armed
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_stop` (stop_touched), R = -1.6, exit price `1.1884800000000002` at bar 34682.
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
  - category: `execution assumption / stop`
  - verdict: `settled_stop`
  - evidence: the triggering bar spanned the whole zone, so the conservative stop-first rule settles it on the entry bar
