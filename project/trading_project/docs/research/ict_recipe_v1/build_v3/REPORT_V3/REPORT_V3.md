# REPORT V3 — repairs, six switches, two unseen months

Nothing here is a winner. Zero signal is a valid result, and at these plan counts it is the result.

## 6.10 Plain English (12 lines)

1. We first fixed the mechanics the dossiers exposed: which price a buy and a sell actually deal at,
   plans that were already invalid before they could fill, the same pool counted twice as T1 and T2,
   and targets that sat behind the entry.
2. Then we built six switches — a wider stop, a mean-threshold stop, extra liquidity pools, a
   structure-break displacement rule, a New-York day clock, a market entry, and a range taken from the
   leg that made the zone — and measured each one against the repaired control.
3. The months were drawn by hash: **2021-11** and **2021-10** were run now; 2021-08 and 2021-12 stay
   sealed.
4. After the repairs, the control still loses on these two months (mean R −0.69 and −0.83 per plan at
   15m); the switches move that by small amounts in both directions.
5. The wider stop (S1) produces more hits and a better mean R, but it also makes the risk much bigger,
   so its excess-hit advantage is not distinguishable from zero on either month.
6. The mean-threshold stop (S2) and the liquidity pools (L) land in the same "cannot tell" bucket.
7. The market entry (E) cancels most plans before it can fill them, so it mostly measures the cancel.
8. The leg range (R) removes about half the plans and does not improve the ones that remain.
9. The New-York clock (T) changed nothing that could be measured: the session window was already in
   New-York time.
10. The full concept version (FULL) is left with 5 to 9 plans a month — too few to conclude anything.
11. No switch reached the pre-declared bar for "candidate for confirmation"; nothing is promoted.
12. What is still unknown: whether any of this holds on the sealed months, and whether the concepts
    themselves carry an edge at all.

## Draw (declared before running)

| month | sha256("EURUSD\|ICT_RECIPE_V3\|20261109\|month") | role |
|---|---|---|
| 2021-11 | `a1092f61dd411b08284855b586c5bc58b62a840144b2c8a24f848224a9aac64e` | **N1** |
| 2021-10 | `beb02fdfcefc4aa68865b1a03ede349c907e45ffd6364f3450aa21f751b2836f` | **N2** |
| 2021-08 | `cccee6f5b752363195d5b2937d4301853415ec4225c2d4cfc1fa9916105706b1` | RESERVED X1 |
| 2021-12 | `344eb8c5d7c642e6ca6efb1f699d0be2d5a526cb9dd741922131cf5b33ec1c45` | RESERVED X2 |

The loader is called with `t1 = first day of the month after the run month`, so no bar of 2021-12 or
2021-08 can be constructed in any run of this task (`run_v3.month_bounds` + `load_bars(t0, t1)`);
`reserved_months_loaded` is `[]` in every `run_summary.json`.

## 6.1 per run, 6.2 paired deltas

Full tables: `TABLES_6_1_6_2.md` (generated from `STATS_V3.json`). Run facts: `RUN_FACTS.md`.

## 6.3-6.7

`TABLES_6_3_6_7.md`, from `ANALYSIS_6_3_6_7.json`:
- 6.3 WIDE feature audit (40 partition tests, Holm over 40): nothing survives the correction. The
  smallest raw p is D-new on N1/15m (diff −0.120, p = 0.016, Holm 0.48) and its sign is negative.
- 6.4 excursion curves: at 15m on N1 the share reaching 0.25·r is 0.717 against a random-walk 0.800;
  on N2 0.594. The curves sit at or below the random-walk reference at every k on both months.
- 6.5 sweep event study: 335 events (N1/15m) and 293 (N2/15m); the shares are close to 1/(1+k) and
  cross it in both directions — e.g. N1/15m k=0.25 0.794 vs 0.800, k=1 0.522 vs 0.500.
- 6.6 hour-of-day and day concentration: in the generated table.
- 6.7 hygiene effect (IN_SAMPLE, paired): 2021-06 15m +0.169 (11 pairs), 2021-07 15m −0.351 (18),
  2021-09 15m −4.726 (8, driven by one sub-pip-risk plan), 1h +0.507 / +0.079 / −0.773.

## 6.8 Dossiers

`DOSSIER_V3-FULL_15m_2021-11.md` (`plan:2021-11-17T07:15:00+00:00:15m:fvg:bearish:21813`, replay
MATCH) and `DOSSIER_V3-S1_15m_2021-11.md` (`plan:2021-11-19T07:50:00+00:00:15m:fvg:bullish:21962`,
cancelled before fill, replay MATCH on "no fill").

## 6.9 Fault locator (all rows HYPOTHESIS)

| locus | observation | evidence |
|---|---|---|
| facts | the 5m file is one symbol, one year, and the mid is never used for execution | 6.5 says "mid, spread ignored" |
| structure | the daily-bias gate cannot fail: zones are gathered **in the bias direction**, so `bias_agrees` is True for 163/163 WIDE plans | 6.3 table, `bias_agrees 163 / 0` |
| selection | 77.8 % of v2 plans were armed with the entry edge already crossed (DIAGNOSIS 1c); V3 keeps arming on the 5m close | 1c, WIDE cancels 24/218 on N1 |
| stop | S1 widens the stop (median 2.10 → 9.95 pips on N1/15m) and lifts hits 2 → 10, but excess-hit CI includes 0 | 6.1, 6.2 |
| target | T2 identity fixed (21 cases), T1 is still simply the nearest untaken pool | 6.1 |
| execution | 18 % of v2 plans were stale before fill; the market entry (E) cancels 24/32 on N1/15m | 1b, 6.1 |
| none visible | at 5-32 plans a month, every one of these effects is smaller than its interval | 6.2 CIs |

Ranked missing/wrong list:
1. No detectable edge in the control or in any switch on these two months.
2. The bias-agreement gate is vacuous by construction (structure).
3. Market entry (E) is dominated by cancellations, so it is uninformative as built.
4. Sub-pip risks still exist and make single plans dominate means (see 6.7 for 2021-09).
5. The leg range (R) halves the plan count with no measurable gain.
6. FULL is too sparse (5-9 plans) to be judged at all.
7. T is a no-op on these months because the window was already New-York anchored.
8. Not reached in this task: the judge pack (Stage 7) and any use of the reserved months.

## What this does NOT establish

- It does not establish that any switch is wrong or right; it establishes only that none clears the
  pre-declared bar on two months.
- It does not establish that a null result here would repeat on the sealed months.
- It does not establish ICT validity: the readings are declared engineering choices, not the source's
  own definitions.
