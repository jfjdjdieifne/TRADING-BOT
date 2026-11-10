# CASE 4 — EURUSD 5m, decision at 2021-06-02T07:20:00+00:00 (bar index 30926)

## A. AS OF t — only what existed at t
A.1 context: daily bias `DOWN`, weekly bias `UP`, resolved `DOWN`, **bias_conflict**
A.2 dealing range: low `1.22045`, high `1.2211`, equilibrium `1.2207750000000002`, position `premium`, ratio `0.8` (id `ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS`)
A.3 liquidity map (untaken, newest first):
  - `1.2217900000000002` high `relative_equal_pair`, formed at bar 5759, age 25167 bars
  - `1.2254200000000002` high `higher_timeframe_extreme`, formed at bar -1, age None bars
  - `1.22194` high `relative_equal_pair`, formed at bar 5759, age 25167 bars
  - `1.2219600000000002` high `relative_equal_pair`, formed at bar 5759, age 25167 bars
  - `1.22206` high `relative_equal_pair`, formed at bar 5759, age 25167 bars
  - `1.22211` high `relative_equal_pair`, formed at bar 5759, age 25167 bars
  - `1.22218` high `relative_equal_pair`, formed at bar 5759, age 25167 bars
  - `1.2223000000000002` high `relative_equal_pair`, formed at bar 5759, age 25167 bars
A.4 concepts at t: swing `[{'side': 'low', 'price': 1.22045, 'level_index': 5758}]`, FVG `none on this bar`, displacement `NO` (V-D-01, ratio 0.1355932203391489), sweep high `YES`, sweep low `NO`, structure shift `none`
A.5 candidate zones, ranked:
  - `sweep:high:None` sweep_level [1.22097, 1.2211] fresh=True bias_agrees=True distance_ratio=0.09999999999996584
  - `fvg:bearish:30918` fvg [1.2210800000000002, 1.22153] fresh=False bias_agrees=True distance_ratio=0.5153846153845444
  - `fvg:bearish:30910` fvg [1.2215200000000002, 1.22182] fresh=False bias_agrees=True distance_ratio=1.076923076922893
  - `fvg:bearish:30896` fvg [1.22188, 1.22198] fresh=False bias_agrees=True distance_ratio=1.4769230769227564
  - `fvg:bearish:30880` fvg [1.22223, 1.2224000000000002] fresh=False bias_agrees=True distance_ratio=2.0692307692305354
  criteria: {"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": true}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.09999999999996584}}
A.6 competing hypotheses:
  - **bearish continuation with the DOWN daily bias** — for: daily bias DOWN; weekly bias UP; range position premium; 11 zone(s) in this direction; against: the opposing pool may be swept before the entry is reached; a bar that spans the zone settles at the stop first (conservative rule)
  - **bullish reversal / range fade** — for: 1 untaken pool(s) on that side; no opposite zone; against: daily bias is DOWN; no confirmed swing against the thesis yet
A.7 the decision in plain words: a **bearish** plan from the `sweep_level` zone `sweep:high:None` was armed at 2021-06-02T07:20:00+00:00; it is hypothetical and assumes no execution contract.
A.8 the hypothetical plan: entry `1.22097` (touch of the zone edge nearest the trade direction), stop `1.2211` (sweep wick), T1 `1.22045`, T2 `None` (only one untaken opposing pool existed; T2 = None), measured R:R T1 `4.0` / T2 `None`, half-spread at decision `1.4999999999987246e-05`.
   what would change this: a confirmed swing against the thesis; the opposing pool taken before entry; a displacement in the opposite direction; the zone closed through; the session window ending
A.9 not looked at: no weekly FVG / weekly order block; no news or calendar data; no volume profile; no other instrument; no bar after the decision bar

## B. HINDSIGHT — everything after t, kept separate
B.1 bars after the decision, in order:
  - 2021-06-02T07:20:00+00:00  high 1.22116  low 1.2205700000000002  close 1.22097  state armed
B.3 fill assumption: limit at the zone edge, settled by the conservative stop-first rule; cost = half the spread at entry + half at exit.
   outcome: `settled_stop` (stop_touched), R = -1.2308, exit price `1.2211` at bar 30926.
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
