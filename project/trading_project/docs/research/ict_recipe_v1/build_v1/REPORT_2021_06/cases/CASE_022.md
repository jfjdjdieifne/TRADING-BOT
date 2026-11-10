# CASE 22 — EURUSD 5m, decision at 2021-06-08T08:25:00+00:00 (bar index 32091)

## A. AS OF t — only what existed at t
A.1 context: daily bias `UP`, weekly bias `DOWN`, resolved `UP`, **bias_conflict**
A.2 dealing range: low `1.21675`, high `1.21748`, equilibrium `1.217115`, position `discount`, ratio `0.4384` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.21748` high `relative_equal_pair`, formed at bar 5759, age 26332 bars
  - `1.2175900000000002` high `relative_equal_pair`, formed at bar 5759, age 26332 bars
  - `1.2201700000000002` high `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.2183700000000002` high `relative_equal_pair`, formed at bar 5759, age 26332 bars
  - `1.21852` high `relative_equal_pair`, formed at bar 5759, age 26332 bars
  - `1.21884` high `relative_equal_pair`, formed at bar 5759, age 26332 bars
  - `1.21906` high `relative_equal_pair`, formed at bar 5759, age 26332 bars
  - `1.2190800000000002` high `relative_equal_pair`, formed at bar 5759, age 26332 bars
A.4 concepts at t: swing `none confirmed on this bar`, FVG `none on this bar`, displacement `NO` (V-D-01, ratio 0.21276595744669793), sweep high `NO`, sweep low `YES`, structure shift `none`
A.5 candidate zones, ranked:
  - `sweep:low:None` sweep_level [1.21675, 1.21707] fresh=True bias_agrees=True distance_ratio=0.21917808219203083
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": true}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.21917808219203083}}
A.6 competing hypotheses:
  - **bullish continuation with the UP daily bias** — for: daily bias UP; weekly bias DOWN; range position discount; 1 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bearish reversal / range fade** — for: 8 untaken pool(s) on that side; opposite zone exists; against: daily bias is UP; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bullish** plan from the `sweep_level` zone `sweep:low:None` was armed at 2021-06-08T08:25:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.21707` (touch of the zone edge nearest the trade direction), stop `1.21675` (sweep wick), T1 `1.21748`, T2 `1.2175900000000002` (two targets existed), measured R:R T1 `1.281` / T2 `1.625`, half-spread at decision `9.99999999995449e-06`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-08T08:25:00+00:00  high 1.2171200000000002  low 1.21665  close 1.21707  state armed
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_stop` (stop_touched), R = -1.0625, exit price `1.21675` at bar 32091.
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
