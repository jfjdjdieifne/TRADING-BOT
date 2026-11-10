# CASE 90 — EURUSD 5m, decision at 2021-06-25T08:55:00+00:00 (bar index 35841)

## A. AS OF t — only what existed at t
A.1 context: daily bias `DOWN`, weekly bias `DOWN`, resolved `DOWN`
A.2 dealing range: low `1.19385`, high `1.19436`, equilibrium `1.194105`, position `premium`, ratio `0.902` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.1947800000000002` high `relative_equal_pair`, formed at bar 5759, age 30082 bars
  - `1.1950500000000002` high `relative_equal_pair`, formed at bar 5759, age 30082 bars
  - `1.19562` high `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.19385` low `relative_equal_pair`, formed at bar 5759, age 30082 bars
  - `1.1917600000000002` low `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.19374` low `relative_equal_pair`, formed at bar 5759, age 30082 bars
  - `1.1935` low `relative_equal_pair`, formed at bar 5759, age 30082 bars
A.4 concepts at t: swing `[{'side': 'low', 'price': 1.19385, 'level_index': 5758}]`, FVG `none on this bar`, displacement `YES` (V-D-01, ratio 0.6744186046519074), sweep high `YES`, sweep low `NO`, structure shift `none`
A.5 candidate zones, ranked:
  - `sweep:high:None` sweep_level [1.1943100000000002, 1.19436] fresh=True bias_agrees=True distance_ratio=0.049019607843022006
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": true}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.049019607843022006}}
A.6 competing hypotheses:
  - **bearish continuation with the DOWN daily bias** — for: daily bias DOWN; weekly bias DOWN; range position premium; 1 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bullish reversal / range fade** — for: 4 untaken pool(s) on that side; opposite zone exists; against: daily bias is DOWN; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bearish** plan from the `sweep_level` zone `sweep:high:None` was armed at 2021-06-25T08:55:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.1943100000000002` (touch of the zone edge nearest the trade direction), stop `1.19436` (sweep wick), T1 `1.19385`, T2 `1.19374` (two targets existed), measured R:R T1 `9.2` / T2 `11.4`, half-spread at decision `1.4999999999987246e-05`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-25T08:55:00+00:00  high 1.1944  low 1.1939700000000002  close 1.1943100000000002  state armed
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_stop` (stop_touched), R = -1.6, exit price `1.19436` at bar 35841.
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
