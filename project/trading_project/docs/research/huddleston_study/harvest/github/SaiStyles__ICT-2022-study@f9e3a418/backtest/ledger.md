# Hypothesis ledger

**Opened 2026-09-03, before the first test was run.** DECISIONS.md sections 4 and 17.

## n = 154

Last run 2026-09-03. All on the `dev` slice; `reserve` untouched, holdout SEALED.

---

## The rule

**One row per hypothesis ever tested. Every run. The failures especially.**

Run 500 rule combinations and dozens will show excellent returns from **pure chance**.
That is arithmetic, not bad code. A backtest result is uninterpretable without the count
of attempts that produced it - you cannot separate a real edge from the best of 500 coin
flips.

**Write the row at the time.** Human memory fails in one direction here: it keeps the
winner and quietly deletes the forty failures. Not carelessness - that is how remembering
works. Hence: at the time, every time, including the rubbish ones.

**A sweep is not one hypothesis.** Six displacement thresholds tested is `n += 6`, not
`n += 1`. Reporting the best of six as a single result is the exact error this file exists
to prevent.

## The columns

| field | why |
|---|---|
| `n` | the running count. **This is the whole point** |
| `date` | when |
| `hypothesis` | the rule or model combination |
| `params` | thresholds, sessions, timeframes |
| `data` | slice and date range used |
| `result` | what it returned - **including "nothing"** |

## Rows

> **CORRECTION 2026-09-04: `n` reduced from 213 to 86.**
>
> The dedup key in the runners included the `data` field, which for the FVG
> study carried the realised gap count. Control selection is random, so that
> count moved by one or two between runs and **every re-run of the same
> hypothesis was logged as a new one** - 16 spurious rows per run, 50 duplicated
> keys in total.
>
> **Removing them is the honest direction.** Section 17 forbids deleting a
> hypothesis that was really tested, because that makes survivors look better
> than they earned. But testing ONE hypothesis three times does not give it three
> chances at a false positive - counting it three times *overstates* the
> multiple-testing burden. The runners' idempotency rule always said this; the
> key was simply broken. It now excludes `data`, and no runner puts a
> run-varying number there.
>
> **A second cause, found the same day.** The `params` text for the FVG study
> contained a literal `|` (in `|3-bar move|`). The ledger is a markdown table,
> so that split the row into extra columns, the dedup read the wrong fields, and
> `n` climbed 86 -> 102 -> 118 across two runs of one script. Every runner now
> sanitises each field through `_clean()` before writing, and no field may
> contain a pipe.
>
> Where a hypothesis appeared more than once, **the last result is kept** - later
> runs are the corrected ones.


> **Rows 140-152 used a SUPERSEDED METHOD. Read them with this note.**
>
> They are kept because DECISIONS.md 17 is explicit that the count cannot be
> reconstructed after the fact - deleting a bad test shrinks `n` and makes every
> surviving result look better than it earned. But two of them are wrong in ways
> a future session must not read as findings:
>
> - **140-148** rank his windows by *opportunity per minute*. Maximum favourable
>   excursion grows sub-linearly with time, so that measure mechanically rewards
>   short windows - it ranked his 60-minute London close first for arithmetic
>   reasons. **Rows 153-161 redo this against same-length controls.**
> - **149-152** report z-scores around **9.5e13**. The selection passed to the
>   matched null was the *majority* class, leaving no pool to draw controls from,
>   so the null had ~zero variance. **Rows 162-165 redo this correctly**, and
>   `nulls.py` now returns `nan` rather than a spectacular number.
>
> Both are counted in `n`. They were real tests; they were just answering the
> wrong question. DECISIONS.md section 24.


| n | date | hypothesis | params | data | result |
|---|---|---|---|---|---|
| 153 | 2026-09-04 | RESERVE: killzone 08:30-11:00 (ep02 42:40) beats same-length windows of the same sessions | pre-registered in findings.md 3, reserve look 1 of 1 | reserve 2023-01-01..2024-02-29 | n=300 sessions; opportunity 128.8pt = 100th pctile, efficiency 0.441 = 26th pctile of 23 controls |
| 154 | 2026-09-04 | RESERVE: sweep of prev session HIGH reverses vs a matched no-sweep move (ep25 28:36) | tf=5m, horizon=120min, pre-registered in findings.md 8 | reserve 2023-01-01..2024-02-29 | n=531; event -3.678pt vs control -3.092pt, z=-0.15 (bar 3.0) |
| 129 | 2026-09-04 | liquidity sweep: sweep of prev HIGH vs a matched no-event move (hour x move octile x sign) | tf=5m, horizon=30min | dev 2010-06-06..2021-12-31, full slice | n=5739; event +0.213pt vs control -0.275pt, z=+1.59 (bar 3.0) |
| 130 | 2026-09-04 | liquidity sweep: sweep of prev HIGH vs a matched no-event move (hour x move octile x sign) | tf=5m, horizon=60min | dev 2010-06-06..2021-12-31, full slice | n=5672; event +0.187pt vs control -0.451pt, z=+1.57 (bar 3.0) |
| 131 | 2026-09-04 | liquidity sweep: sweep of prev HIGH vs a matched no-event move (hour x move octile x sign) | tf=5m, horizon=120min | dev 2010-06-06..2021-12-31, full slice | n=5510; event +0.447pt vs control -1.378pt, z=+3.10 (bar 3.0) |
| 132 | 2026-09-04 | liquidity sweep: sweep of prev LOW vs a matched no-event move (hour x move octile x sign) | tf=5m, horizon=30min | dev 2010-06-06..2021-12-31, full slice | n=4044; event +0.119pt vs control +0.252pt, z=-0.29 (bar 3.0) |
| 133 | 2026-09-04 | liquidity sweep: sweep of prev LOW vs a matched no-event move (hour x move octile x sign) | tf=5m, horizon=60min | dev 2010-06-06..2021-12-31, full slice | n=3991; event +0.330pt vs control +0.426pt, z=-0.16 (bar 3.0) |
| 134 | 2026-09-04 | liquidity sweep: sweep of prev LOW vs a matched no-event move (hour x move octile x sign) | tf=5m, horizon=120min | dev 2010-06-06..2021-12-31, full slice | n=3885; event +0.710pt vs control +1.033pt, z=-0.36 (bar 3.0) |
| 135 | 2026-09-04 | order block: bullish order block (on return) vs a matched no-event move (hour x move octile x sign) | tf=5m, horizon=30min | dev 2010-06-06..2021-12-31, full slice | n=67578; event +0.035pt vs control +0.655pt, z=-7.58 (bar 3.0) |
| 136 | 2026-09-04 | order block: bullish order block (on return) vs a matched no-event move (hour x move octile x sign) | tf=5m, horizon=60min | dev 2010-06-06..2021-12-31, full slice | n=66213; event +0.136pt vs control +0.737pt, z=-5.20 (bar 3.0) |
| 137 | 2026-09-04 | order block: bullish order block (on return) vs a matched no-event move (hour x move octile x sign) | tf=5m, horizon=120min | dev 2010-06-06..2021-12-31, full slice | n=63294; event +0.411pt vs control +0.628pt, z=-1.29 (bar 3.0) |
| 138 | 2026-09-04 | order block: bearish order block (on return) vs a matched no-event move (hour x move octile x sign) | tf=5m, horizon=30min | dev 2010-06-06..2021-12-31, full slice | n=67052; event -0.100pt vs control +0.601pt, z=-8.98 (bar 3.0) |
| 139 | 2026-09-04 | order block: bearish order block (on return) vs a matched no-event move (hour x move octile x sign) | tf=5m, horizon=60min | dev 2010-06-06..2021-12-31, full slice | n=65637; event -0.211pt vs control +0.849pt, z=-9.35 (bar 3.0) |
| 140 | 2026-09-04 | order block: bearish order block (on return) vs a matched no-event move (hour x move octile x sign) | tf=5m, horizon=120min | dev 2010-06-06..2021-12-31, full slice | n=62722; event -0.456pt vs control +0.838pt, z=-7.92 (bar 3.0) |
| 141 | 2026-09-04 | liquidity sweep: sweep of prev HIGH vs a matched no-event move (hour x move octile x sign) | tf=15m, horizon=90min | dev 2010-06-06..2021-12-31, full slice | n=3520; event +0.015pt vs control -0.018pt, z=+0.05 (bar 3.0) |
| 142 | 2026-09-04 | liquidity sweep: sweep of prev HIGH vs a matched no-event move (hour x move octile x sign) | tf=15m, horizon=180min | dev 2010-06-06..2021-12-31, full slice | n=3377; event +0.194pt vs control +0.564pt, z=-0.39 (bar 3.0) |
| 143 | 2026-09-04 | liquidity sweep: sweep of prev HIGH vs a matched no-event move (hour x move octile x sign) | tf=15m, horizon=360min | dev 2010-06-06..2021-12-31, full slice | n=3088; event +0.236pt vs control -2.151pt, z=+1.86 (bar 3.0) |
| 144 | 2026-09-04 | liquidity sweep: sweep of prev LOW vs a matched no-event move (hour x move octile x sign) | tf=15m, horizon=90min | dev 2010-06-06..2021-12-31, full slice | n=2567; event +0.576pt vs control +0.127pt, z=+0.46 (bar 3.0) |
| 145 | 2026-09-04 | liquidity sweep: sweep of prev LOW vs a matched no-event move (hour x move octile x sign) | tf=15m, horizon=180min | dev 2010-06-06..2021-12-31, full slice | n=2465; event +1.968pt vs control +2.178pt, z=-0.16 (bar 3.0) |
| 146 | 2026-09-04 | liquidity sweep: sweep of prev LOW vs a matched no-event move (hour x move octile x sign) | tf=15m, horizon=360min | dev 2010-06-06..2021-12-31, full slice | n=2209; event +4.522pt vs control +2.761pt, z=+0.96 (bar 3.0) |
| 147 | 2026-09-04 | order block: bullish order block (on return) vs a matched no-event move (hour x move octile x sign) | tf=15m, horizon=90min | dev 2010-06-06..2021-12-31, full slice | n=24371; event +0.192pt vs control +1.532pt, z=-5.82 (bar 3.0) |
| 148 | 2026-09-04 | order block: bullish order block (on return) vs a matched no-event move (hour x move octile x sign) | tf=15m, horizon=180min | dev 2010-06-06..2021-12-31, full slice | n=22699; event +0.439pt vs control +1.326pt, z=-2.64 (bar 3.0) |
| 149 | 2026-09-04 | order block: bullish order block (on return) vs a matched no-event move (hour x move octile x sign) | tf=15m, horizon=360min | dev 2010-06-06..2021-12-31, full slice | n=19479; event +1.264pt vs control +1.664pt, z=-0.76 (bar 3.0) |
| 150 | 2026-09-04 | order block: bearish order block (on return) vs a matched no-event move (hour x move octile x sign) | tf=15m, horizon=90min | dev 2010-06-06..2021-12-31, full slice | n=23459; event -0.386pt vs control +1.562pt, z=-8.64 (bar 3.0) |
| 151 | 2026-09-04 | order block: bearish order block (on return) vs a matched no-event move (hour x move octile x sign) | tf=15m, horizon=180min | dev 2010-06-06..2021-12-31, full slice | n=21809; event -0.680pt vs control +1.971pt, z=-8.01 (bar 3.0) |
| 152 | 2026-09-04 | order block: bearish order block (on return) vs a matched no-event move (hour x move octile x sign) | tf=15m, horizon=360min | dev 2010-06-06..2021-12-31, full slice | n=18774; event -0.899pt vs control +2.060pt, z=-5.58 (bar 3.0) |
| 125 | 2026-09-04 | gate g2_liquidity_taken: does it earn its place? refused vs accepted, SAME 2R target (ep24 [17:41]) | baseline config, target_mode=fixed_2r both sides | dev 2010-06-06..2021-12-31, full slice | refused n=3571 at -0.029R (win 32%) vs accepted n=171 at -0.185R; z=-1.54, bar is 3.0 |
| 126 | 2026-09-04 | gate g3_displacement: does it earn its place? refused vs accepted, SAME 2R target (ep24 [17:41]) | baseline config, target_mode=fixed_2r both sides | dev 2010-06-06..2021-12-31, full slice | refused n=635 at +0.111R (win 37%) vs accepted n=171 at -0.185R; z=-2.60, bar is 3.0 |
| 127 | 2026-09-04 | gate g5_gap_in_discount: does it earn its place? refused vs accepted, SAME 2R target (ep24 [17:41]) | baseline config, target_mode=fixed_2r both sides | dev 2010-06-06..2021-12-31, full slice | refused n=252 at -0.089R (win 31%) vs accepted n=171 at -0.185R; z=-0.73, bar is 3.0 |
| 128 | 2026-09-04 | gate g7_ote: does it earn its place? refused vs accepted, SAME 2R target (ep24 [17:41]) | baseline config, target_mode=fixed_2r both sides | dev 2010-06-06..2021-12-31, full slice | refused n=117 at -0.179R (win 27%) vs accepted n=171 at -0.185R; z=-0.04, bar is 3.0 |
| 124 | 2026-09-04 | gate g7_ote counterfactual: what the setups it REFUSED went on to do (ep24 [17:41]) | baseline config, 2R target, stop beyond the gap | dev 2010-06-06..2021-12-31, full slice | n=117 refused; expectancy -0.179R, win 27%; accepted trades -0.245R |
| 93 | 2026-09-04 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | baseline / defaults | dev 2010-06-06..2021-12-31, 400 sessions | 2 trades, win 0%, expectancy -1.000R, total -2.0R |
| 94 | 2026-09-04 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | disp=0pt / disp_pts=0.0 | dev 2010-06-06..2021-12-31, 400 sessions | 10 trades, win 30%, expectancy -0.102R, total -1.0R |
| 95 | 2026-09-04 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | disp=10pt / disp_pts=10.0 | dev 2010-06-06..2021-12-31, 400 sessions | 5 trades, win 20%, expectancy -0.467R, total -2.3R |
| 96 | 2026-09-04 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | disp=20pt / disp_pts=20.0 | dev 2010-06-06..2021-12-31, 400 sessions | 2 trades, win 0%, expectancy -1.000R, total -2.0R |
| 97 | 2026-09-04 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | disp=40pt / disp_pts=40.0 | dev 2010-06-06..2021-12-31, 400 sessions | no trades formed |
| 98 | 2026-09-04 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | disp=80pt / disp_pts=80.0 | dev 2010-06-06..2021-12-31, 400 sessions | no trades formed |
| 99 | 2026-09-04 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | ob=ep03_opening_price / ob_variant=ep03_opening_price | dev 2010-06-06..2021-12-31, 400 sessions | 2 trades, win 0%, expectancy -1.000R, total -2.0R |
| 100 | 2026-09-04 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | ob=ep12_series / ob_variant=ep12_series | dev 2010-06-06..2021-12-31, 400 sessions | 2 trades, win 0%, expectancy -1.000R, total -2.0R |
| 101 | 2026-09-04 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | ob=ep17_last_opposite / ob_variant=ep17_last_opposite | dev 2010-06-06..2021-12-31, 400 sessions | 2 trades, win 0%, expectancy -1.000R, total -2.0R |
| 102 | 2026-09-04 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | ote_hi=0.7 / ote_hi=0.7 | dev 2010-06-06..2021-12-31, 400 sessions | 2 trades, win 0%, expectancy -1.000R, total -2.0R |
| 103 | 2026-09-04 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | ote_hi=0.79 / ote_hi=0.79 | dev 2010-06-06..2021-12-31, 400 sessions | 3 trades, win 0%, expectancy -1.000R, total -3.0R |
| 104 | 2026-09-04 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | struct_tf=5m / struct_tf=5 | dev 2010-06-06..2021-12-31, 400 sessions | 11 trades, win 55%, expectancy +0.238R, total +2.6R |
| 105 | 2026-09-04 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | struct_tf=15m / struct_tf=15 | dev 2010-06-06..2021-12-31, 400 sessions | 2 trades, win 0%, expectancy -1.000R, total -2.0R |
| 106 | 2026-09-04 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | struct_tf=60m / struct_tf=60 | dev 2010-06-06..2021-12-31, 400 sessions | 3 trades, win 33%, expectancy +0.061R, total +0.2R |
| 107 | 2026-09-04 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | fvg_tf=1m / fvg_tf=1 | dev 2010-06-06..2021-12-31, 400 sessions | 8 trades, win 12%, expectancy -0.385R, total -3.1R |
| 108 | 2026-09-04 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | fvg_tf=5m / fvg_tf=5 | dev 2010-06-06..2021-12-31, 400 sessions | 2 trades, win 0%, expectancy -1.000R, total -2.0R |
| 109 | 2026-09-04 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | fvg_tf=15m / fvg_tf=15 | dev 2010-06-06..2021-12-31, 400 sessions | 8 trades, win 50%, expectancy +0.049R, total +0.4R |
| 110 | 2026-09-04 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | stop=gap / stop_mode=gap | dev 2010-06-06..2021-12-31, 400 sessions | 2 trades, win 0%, expectancy -1.000R, total -2.0R |
| 111 | 2026-09-04 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | stop=leg / stop_mode=leg | dev 2010-06-06..2021-12-31, 400 sessions | 2 trades, win 0%, expectancy -1.000R, total -2.0R |
| 112 | 2026-09-04 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | target=leg_extreme / target_mode=leg_extreme | dev 2010-06-06..2021-12-31, 400 sessions | 2 trades, win 0%, expectancy -1.000R, total -2.0R |
| 113 | 2026-09-04 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | target=nearest_pivot / target_mode=nearest_pivot | dev 2010-06-06..2021-12-31, 400 sessions | 2 trades, win 50%, expectancy -0.413R, total -0.8R |
| 114 | 2026-09-04 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | min_rr=0 / min_rr=0.0 | dev 2010-06-06..2021-12-31, 400 sessions | 2 trades, win 0%, expectancy -1.000R, total -2.0R |
| 115 | 2026-09-04 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | min_rr=1 / min_rr=1.0 | dev 2010-06-06..2021-12-31, 400 sessions | 2 trades, win 0%, expectancy -1.000R, total -2.0R |
| 116 | 2026-09-04 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | min_rr=2 / min_rr=2.0 | dev 2010-06-06..2021-12-31, 400 sessions | 1 trades, win 0%, expectancy -1.000R, total -1.0R |
| 117 | 2026-09-04 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | no_ob / require_ob=False | dev 2010-06-06..2021-12-31, 400 sessions | 2 trades, win 0%, expectancy -1.000R, total -2.0R |
| 118 | 2026-09-04 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | no_ote / require_ote=False | dev 2010-06-06..2021-12-31, 400 sessions | 4 trades, win 0%, expectancy -1.000R, total -4.0R |
| 119 | 2026-09-04 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | no_shift / require_shift=False | dev 2010-06-06..2021-12-31, 400 sessions | 3 trades, win 0%, expectancy -1.000R, total -3.0R |
| 120 | 2026-09-04 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | skip_0930 / skip_0930=True | dev 2010-06-06..2021-12-31, 400 sessions | 2 trades, win 0%, expectancy -1.000R, total -2.0R |
| 121 | 2026-09-04 | gate g2_liquidity_taken counterfactual: what the setups it REFUSED went on to do (ep24 [17:41]) | baseline config, 2R target, stop beyond the gap | dev 2010-06-06..2021-12-31, full slice | n=1430 refused; expectancy +0.089R, win 36%; accepted trades -1.000R |
| 122 | 2026-09-04 | gate g3_displacement counterfactual: what the setups it REFUSED went on to do (ep24 [17:41]) | baseline config, 2R target, stop beyond the gap | dev 2010-06-06..2021-12-31, full slice | n=494 refused; expectancy +0.101R, win 37%; accepted trades -1.000R |
| 123 | 2026-09-04 | gate g5_gap_in_discount counterfactual: what the setups it REFUSED went on to do (ep24 [17:41]) | baseline config, 2R target, stop beyond the gap | dev 2010-06-06..2021-12-31, full slice | n=90 refused; expectancy +0.000R, win 33%; accepted trades -1.000R |
| 87 | 2026-09-04 | intraday momentum in on-close macro 1500-1600 (ep32 11:32): does the day's prior return predict this window? (published anomaly, JFE 2021) | 15:00-16:00, anchor=prev_close, 31 same-length controls | dev 2010-06-06..2021-12-31, full slice | n=2969; momentum spread +2.41bp (t=+1.62); directional hit 48.0%; signed return +1.18bp (t=+1.64); 94th pctile of controls, best control 11:30 t=+1.64 |
| 88 | 2026-09-04 | intraday momentum in last 30min 1530-1600 (the paper's window): does the day's prior return predict this window? (published anomaly, JFE 2021) | 15:30-16:00, anchor=prev_close, 32 same-length controls | dev 2010-06-06..2021-12-31, full slice | n=2969; momentum spread +1.95bp (t=+1.68); directional hit 47.3%; signed return +0.97bp (t=+1.72); 94th pctile of controls, best control 01:00 t=+1.68 |
| 89 | 2026-09-04 | intraday momentum in 1540-1600 (ep05 26:53): does the day's prior return predict this window? (published anomaly, JFE 2021) | 15:40-16:00, anchor=prev_close, 32 same-length controls | dev 2010-06-06..2021-12-31, full slice | n=2969; momentum spread +1.58bp (t=+1.55); directional hit 47.1%; signed return +0.72bp (t=+1.44); 94th pctile of controls, best control 03:30 t=+2.19 |
| 90 | 2026-09-04 | intraday momentum in on-close macro 1500-1600 (ep32 11:32): does the day's prior return predict this window? (published anomaly, JFE 2021) | 15:00-16:00, anchor=midnight, 30 same-length controls | dev 2010-06-06..2021-12-31, full slice | n=2641; momentum spread +2.63bp (t=+1.68); directional hit 48.9%; signed return +1.29bp (t=+1.67); 93th pctile of controls, best control 03:30 t=+1.80 |
| 91 | 2026-09-04 | intraday momentum in last 30min 1530-1600 (the paper's window): does the day's prior return predict this window? (published anomaly, JFE 2021) | 15:30-16:00, anchor=midnight, 31 same-length controls | dev 2010-06-06..2021-12-31, full slice | n=2641; momentum spread +1.76bp (t=+1.43); directional hit 47.4%; signed return +0.88bp (t=+1.45); 90th pctile of controls, best control 03:30 t=+2.17 |
| 92 | 2026-09-04 | intraday momentum in 1540-1600 (ep05 26:53): does the day's prior return predict this window? (published anomaly, JFE 2021) | 15:40-16:00, anchor=midnight, 31 same-length controls | dev 2010-06-06..2021-12-31, full slice | n=2641; momentum spread +1.38bp (t=+1.26); directional hit 47.3%; signed return +0.63bp (t=+1.17); 81th pctile of controls, best control 03:30 t=+2.50 |
| 1 | 2026-09-03 | veto: overnight_run (ep09 [15:15]) | threshold_pts=25 | dev 2010-06-06..2021-12-31, 2969 sessions | refused 21%; efficiency 0.466->0.466 (z=-0.4); opportunity 32->28pt (z=-16.5) |
| 2 | 2026-09-03 | veto: overnight_run (ep09 [15:15]) | threshold_pts=50 | dev 2010-06-06..2021-12-31, 2969 sessions | refused 9%; efficiency 0.466->0.468 (z=+0.5); opportunity 32->30pt (z=-11.3) |
| 3 | 2026-09-03 | veto: overnight_run (ep09 [15:15]) | threshold_pts=75 | dev 2010-06-06..2021-12-31, 2969 sessions | refused 5%; efficiency 0.466->0.469 (z=+1.4); opportunity 32->31pt (z=-7.5) |
| 4 | 2026-09-03 | veto: overnight_run (ep09 [15:15]) | threshold_pts=100 | dev 2010-06-06..2021-12-31, 2969 sessions | refused 2%; efficiency 0.466->0.468 (z=+0.8); opportunity 32->32pt (z=-5.0) |
| 5 | 2026-09-03 | veto: overnight_run (ep09 [15:15]) | threshold_pts=150 | dev 2010-06-06..2021-12-31, 2969 sessions | refused 1%; efficiency 0.466->0.468 (z=+1.2); opportunity 32->32pt (z=-0.9) |
| 6 | 2026-09-03 | veto: wednesday_done (ep37 [05:18]) | none | dev 2010-06-06..2021-12-31, 2969 sessions | refused 40%; efficiency 0.466->0.475 (z=+1.3); opportunity 32->32pt (z=-2.0) |
| 7 | 2026-09-03 | veto: midrange (ep32 [04:56]) | band=0.05 | dev 2010-06-06..2021-12-31, 2969 sessions | refused 7%; efficiency 0.466->0.468 (z=+0.7); opportunity 32->32pt (z=-0.8) |
| 8 | 2026-09-03 | veto: midrange (ep32 [04:56]) | band=0.1 | dev 2010-06-06..2021-12-31, 2969 sessions | refused 14%; efficiency 0.466->0.468 (z=+0.4); opportunity 32->32pt (z=-0.6) |
| 9 | 2026-09-03 | veto: midrange (ep32 [04:56]) | band=0.2 | dev 2010-06-06..2021-12-31, 2969 sessions | refused 30%; efficiency 0.466->0.476 (z=+1.8); opportunity 32->33pt (z=+0.8) |
| 10 | 2026-09-03 | ep09 [15:15] as stated: after a big overnight run, the PM takes the morning's extreme | threshold_pts=25 | dev 2010-06-06..2021-12-31, 626 qualifying sessions | PM took AM low 40.3% vs base 37.4% (z=+1.7); AM high 49.8% vs 47.4% (z=+1.4); directional reversal 44.2% |
| 11 | 2026-09-03 | ep09 [15:15] as stated: after a big overnight run, the PM takes the morning's extreme | threshold_pts=50 | dev 2010-06-06..2021-12-31, 254 qualifying sessions | PM took AM low 38.2% vs base 37.4% (z=+0.3); AM high 53.1% vs 47.4% (z=+1.9); directional reversal 40.9% |
| 12 | 2026-09-03 | ep09 [15:15] as stated: after a big overnight run, the PM takes the morning's extreme | threshold_pts=75 | dev 2010-06-06..2021-12-31, 136 qualifying sessions | PM took AM low 36.8% vs base 37.4% (z=-0.1); AM high 56.6% vs 47.4% (z=+2.2); directional reversal 42.6% |
| 13 | 2026-09-03 | ep09 [15:15] as stated: after a big overnight run, the PM takes the morning's extreme | threshold_pts=100 | dev 2010-06-06..2021-12-31, 73 qualifying sessions | PM took AM low 39.7% vs base 37.4% (z=+0.4); AM high 56.2% vs 47.4% (z=+1.5); directional reversal 43.8% |
| 14 | 2026-09-03 | veto: overnight_run (ep09 [15:15]) | threshold_pts=25 [overnight=02:00-05:00 range, ep09 12:44] | dev 2010-06-06..2021-12-31, 2962 sessions | refused 32%; efficiency 0.467->0.470 (z=+0.5); opportunity 32->25pt (z=-18.6) |
| 15 | 2026-09-03 | veto: overnight_run (ep09 [15:15]) | threshold_pts=50 [overnight=02:00-05:00 range, ep09 12:44] | dev 2010-06-06..2021-12-31, 2962 sessions | refused 14%; efficiency 0.467->0.466 (z=-0.4); opportunity 32->29pt (z=-14.5) |
| 16 | 2026-09-03 | veto: overnight_run (ep09 [15:15]) | threshold_pts=75 [overnight=02:00-05:00 range, ep09 12:44] | dev 2010-06-06..2021-12-31, 2962 sessions | refused 7%; efficiency 0.467->0.466 (z=-0.4); opportunity 32->31pt (z=-9.3) |
| 17 | 2026-09-03 | veto: overnight_run (ep09 [15:15]) | threshold_pts=100 [overnight=02:00-05:00 range, ep09 12:44] | dev 2010-06-06..2021-12-31, 2962 sessions | refused 4%; efficiency 0.467->0.469 (z=+1.4); opportunity 32->32pt (z=-6.5) |
| 18 | 2026-09-03 | veto: overnight_run (ep09 [15:15]) | threshold_pts=150 [overnight=02:00-05:00 range, ep09 12:44] | dev 2010-06-06..2021-12-31, 2962 sessions | refused 1%; efficiency 0.467->0.468 (z=+1.1); opportunity 32->32pt (z=-4.2) |
| 19 | 2026-09-03 | ep09 [15:15] as stated: after a big overnight run, the PM takes the morning's extreme | threshold_pts=25 [overnight=02:00-05:00 range, ep09 12:44] | dev 2010-06-06..2021-12-31, 957 qualifying sessions | PM took AM low 39.4% vs base 37.3% (z=+1.6); AM high 49.6% vs 47.4% (z=+1.7); directional reversal 44.8% |
| 20 | 2026-09-03 | ep09 [15:15] as stated: after a big overnight run, the PM takes the morning's extreme | threshold_pts=50 [overnight=02:00-05:00 range, ep09 12:44] | dev 2010-06-06..2021-12-31, 421 qualifying sessions | PM took AM low 42.5% vs base 37.3% (z=+2.3); AM high 50.1% vs 47.4% (z=+1.2); directional reversal 44.5% |
| 21 | 2026-09-03 | ep09 [15:15] as stated: after a big overnight run, the PM takes the morning's extreme | threshold_pts=75 [overnight=02:00-05:00 range, ep09 12:44] | dev 2010-06-06..2021-12-31, 205 qualifying sessions | PM took AM low 41.5% vs base 37.3% (z=+1.3); AM high 54.6% vs 47.4% (z=+2.2); directional reversal 46.6% |
| 22 | 2026-09-03 | ep09 [15:15] as stated: after a big overnight run, the PM takes the morning's extreme | threshold_pts=100 [overnight=02:00-05:00 range, ep09 12:44] | dev 2010-06-06..2021-12-31, 112 qualifying sessions | PM took AM low 37.5% vs base 37.3% (z=-0.0); AM high 59.8% vs 47.4% (z=+2.7); directional reversal 47.7% |
| 23 | 2026-09-03 | ep09 [15:15] as stated: after a big overnight run, the PM takes the morning's extreme | threshold_pts=150 [overnight=02:00-05:00 range, ep09 12:44] | dev 2010-06-06..2021-12-31, 38 qualifying sessions | PM took AM low 34.2% vs base 37.3% (z=-0.4); AM high 57.9% vs 47.4% (z=+1.3); directional reversal 31.6% |
| 24 | 2026-09-03 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | baseline | defaults | dev 2010-06-06..2021-12-31, 400 sessions |
| 25 | 2026-09-03 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | disp=0pt | disp_pts=0.0 | dev 2010-06-06..2021-12-31, 400 sessions |
| 26 | 2026-09-03 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | disp=10pt | disp_pts=10.0 | dev 2010-06-06..2021-12-31, 400 sessions |
| 27 | 2026-09-03 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | disp=20pt | disp_pts=20.0 | dev 2010-06-06..2021-12-31, 400 sessions |
| 28 | 2026-09-03 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | disp=40pt | disp_pts=40.0 | dev 2010-06-06..2021-12-31, 400 sessions |
| 29 | 2026-09-03 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | disp=80pt | disp_pts=80.0 | dev 2010-06-06..2021-12-31, 400 sessions |
| 30 | 2026-09-03 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | ob=ep03_opening_price | ob_variant=ep03_opening_price | dev 2010-06-06..2021-12-31, 400 sessions |
| 31 | 2026-09-03 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | ob=ep12_series | ob_variant=ep12_series | dev 2010-06-06..2021-12-31, 400 sessions |
| 32 | 2026-09-03 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | ob=ep17_last_opposite | ob_variant=ep17_last_opposite | dev 2010-06-06..2021-12-31, 400 sessions |
| 33 | 2026-09-03 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | ote_hi=0.7 | ote_hi=0.7 | dev 2010-06-06..2021-12-31, 400 sessions |
| 34 | 2026-09-03 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | ote_hi=0.79 | ote_hi=0.79 | dev 2010-06-06..2021-12-31, 400 sessions |
| 35 | 2026-09-03 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | no_ob | require_ob=False | dev 2010-06-06..2021-12-31, 400 sessions |
| 36 | 2026-09-03 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | no_ote | require_ote=False | dev 2010-06-06..2021-12-31, 400 sessions |
| 37 | 2026-09-03 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | no_shift | require_shift=False | dev 2010-06-06..2021-12-31, 400 sessions |
| 38 | 2026-09-03 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | skip_0930 | skip_0930=True | dev 2010-06-06..2021-12-31, 400 sessions |
| 39 | 2026-09-03 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | struct_tf=5m | struct_tf=5 | dev 2010-06-06..2021-12-31, 400 sessions |
| 40 | 2026-09-03 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | struct_tf=15m | struct_tf=15 | dev 2010-06-06..2021-12-31, 400 sessions |
| 41 | 2026-09-03 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | struct_tf=60m | struct_tf=60 | dev 2010-06-06..2021-12-31, 400 sessions |
| 42 | 2026-09-03 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | stop=gap | stop_mode=gap | dev 2010-06-06..2021-12-31, 400 sessions |
| 43 | 2026-09-03 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | stop=leg | stop_mode=leg | dev 2010-06-06..2021-12-31, 400 sessions |
| 44 | 2026-09-03 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | target=leg_extreme | target_mode=leg_extreme | dev 2010-06-06..2021-12-31, 400 sessions |
| 45 | 2026-09-03 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | target=nearest_pivot | target_mode=nearest_pivot | dev 2010-06-06..2021-12-31, 400 sessions |
| 46 | 2026-09-03 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | min_rr=0 | min_rr=0.0 | dev 2010-06-06..2021-12-31, 400 sessions |
| 47 | 2026-09-03 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | min_rr=1 | min_rr=1.0 | dev 2010-06-06..2021-12-31, 400 sessions |
| 48 | 2026-09-03 | gold-standard pipeline (ep41 [16:36]: FVG+OB+OTE) | min_rr=2 | min_rr=2.0 | dev 2010-06-06..2021-12-31, 400 sessions |
| 49 | 2026-09-03 | clock: is London close 1000-1100 (ep40 17:36) special vs other windows of equal length (length-normalised) | 10:00-11:00, 60min | dev 2010-06-06..2021-12-31, 2966 sessions | opp/min 0.3708, efficiency 0.467, median range 22.2pt |
| 50 | 2026-09-03 | clock: is 0930-1100 (ep06 33:16) special vs other windows of equal length (length-normalised) | 09:30-11:00, 90min | dev 2010-06-06..2021-12-31, 2967 sessions | opp/min 0.3389, efficiency 0.479, median range 30.5pt |
| 51 | 2026-09-03 | clock: is on-close macro 1500-1600 (ep32 11:32) special vs other windows of equal length (length-normalised) | 15:00-16:00, 60min | dev 2010-06-06..2021-12-31, 2881 sessions | opp/min 0.2625, efficiency 0.456, median range 15.8pt |
| 52 | 2026-09-03 | clock: is LUNCH 1200-1300 (ep05 10:04) special vs other windows of equal length (length-normalised) | 12:00-13:00, 60min | dev 2010-06-06..2021-12-31, 2951 sessions | opp/min 0.2292, efficiency 0.442, median range 13.8pt |
| 53 | 2026-09-03 | clock: is AM killzone 0830-1100 (ep02 42:40) special vs other windows of equal length (length-normalised) | 08:30-11:00, 150min | dev 2010-06-06..2021-12-31, 2970 sessions | opp/min 0.2150, efficiency 0.467, median range 32.2pt |
| 54 | 2026-09-03 | clock: is 0830-0930 only (ep25 34:43) special vs other windows of equal length (length-normalised) | 08:30-09:30, 60min | dev 2010-06-06..2021-12-31, 2968 sessions | opp/min 0.1792, efficiency 0.435, median range 10.8pt |
| 55 | 2026-09-03 | clock: is PM 1330-1600 (ep41 06:20) special vs other windows of equal length (length-normalised) | 13:30-16:00, 150min | dev 2010-06-06..2021-12-31, 2881 sessions | opp/min 0.1583, efficiency 0.451, median range 23.8pt |
| 56 | 2026-09-03 | clock: is London killzone (ep03 32:59) special vs other windows of equal length (length-normalised) | 02:00-05:00, 180min | dev 2010-06-06..2021-12-31, 2963 sessions | opp/min 0.0861, efficiency 0.453, median range 15.5pt |
| 57 | 2026-09-03 | clock: is pre-830 (ep09 12:44 overnight) special vs other windows of equal length (length-normalised) | 05:00-08:30, 210min | dev 2010-06-06..2021-12-31, 2969 sessions | opp/min 0.0738, efficiency 0.440, median range 15.5pt |
| 58 | 2026-09-03 | veto wednesday_done (ep37 05:18) vs VOLATILITY-MATCHED null | matched on prior-day range, 10 strata | dev 2010-06-06..2021-12-31, 1783 traded sessions | refused 40%; efficiency z=+95472607193108.67, opportunity z=+nan (Harvey hurdle |
| 59 | 2026-09-03 | veto midrange band=0.05 (ep32 04:56) vs VOLATILITY-MATCHED null | matched on prior-day range, 10 strata | dev 2010-06-06..2021-12-31, 2759 traded sessions | refused 7%; efficiency z=+527967854625726.00, opportunity z=+nan (Harvey hurdle |
| 60 | 2026-09-03 | veto midrange band=0.10 (ep32 04:56) vs VOLATILITY-MATCHED null | matched on prior-day range, 10 strata | dev 2010-06-06..2021-12-31, 2541 traded sessions | refused 14%; efficiency z=+149697114374567.00, opportunity z=+nan (Harvey hurdle |
| 61 | 2026-09-03 | veto midrange band=0.20 (ep32 04:56) vs VOLATILITY-MATCHED null | matched on prior-day range, 10 strata | dev 2010-06-06..2021-12-31, 2079 traded sessions | refused 30%; efficiency z=+127197871205522.67, opportunity z=+nan (Harvey hurdle |
| 62 | 2026-09-03 | clock: is AM killzone 0830-1100 (ep02 42:40) special vs same-length windows of the same sessions | 08:30-11:00, 150min, 23 controls | dev 2010-06-06..2021-12-31, 2970 sessions | opportunity 32.2pt = 100th pctile of controls; efficiency 0.467 = 100th; best control 10:00 at 30.8pt |
| 63 | 2026-09-03 | clock: is 0930-1100 (ep06 33:16) special vs same-length windows of the same sessions | 09:30-11:00, 90min, 27 controls | dev 2010-06-06..2021-12-31, 2967 sessions | opportunity 30.5pt = 100th pctile of controls; efficiency 0.479 = 100th; best control 08:30 at 24.2pt |
| 64 | 2026-09-03 | clock: is London close 1000-1100 (ep40 17:36) special vs same-length windows of the same sessions | 10:00-11:00, 60min, 30 controls | dev 2010-06-06..2021-12-31, 2966 sessions | opportunity 22.2pt = 93th pctile of controls; efficiency 0.467 = 90th; best control 09:30 at 26.5pt |
| 65 | 2026-09-03 | clock: is on-close macro 1500-1600 (ep32 11:32) special vs same-length windows of the same sessions | 15:00-16:00, 60min, 30 controls | dev 2010-06-06..2021-12-31, 2881 sessions | opportunity 15.8pt = 83th pctile of controls; efficiency 0.456 = 73th; best control 09:30 at 26.5pt |
| 66 | 2026-09-03 | clock: is PM 1330-1600 (ep41 06:20) special vs same-length windows of the same sessions | 13:30-16:00, 150min, 25 controls | dev 2010-06-06..2021-12-31, 2881 sessions | opportunity 23.8pt = 68th pctile of controls; efficiency 0.451 = 40th; best control 09:30 at 35.5pt |
| 67 | 2026-09-03 | clock: is LUNCH 1200-1300 (ep05 10:04) special vs same-length windows of the same sessions | 12:00-13:00, 60min, 30 controls | dev 2010-06-06..2021-12-31, 2951 sessions | opportunity 13.8pt = 63th pctile of controls; efficiency 0.442 = 33th; best control 09:30 at 26.5pt |
| 68 | 2026-09-03 | clock: is 0830-0930 only (ep25 34:43) special vs same-length windows of the same sessions | 08:30-09:30, 60min, 30 controls | dev 2010-06-06..2021-12-31, 2968 sessions | opportunity 10.8pt = 50th pctile of controls; efficiency 0.435 = 13th; best control 09:30 at 26.5pt |
| 69 | 2026-09-03 | clock: is London killzone (ep03 32:59) special vs same-length windows of the same sessions | 02:00-05:00, 180min, 22 controls | dev 2010-06-06..2021-12-31, 2963 sessions | opportunity 15.5pt = 32th pctile of controls; efficiency 0.453 = 59th; best control 09:30 at 37.5pt |
| 70 | 2026-09-03 | clock: is pre-830 (ep09 12:44 overnight) special vs same-length windows of the same sessions | 05:00-08:30, 210min, 19 controls | dev 2010-06-06..2021-12-31, 2969 sessions | opportunity 15.5pt = 11th pctile of controls; efficiency 0.440 = 5th; best control 09:30 at 39.0pt |
| 71 | 2026-09-04 | FVG (ep02 [17:53]) bullish on 5m: does the gap change what happens next, vs a matched no-gap move? | tf=5m, horizon=20min, controls matched on hour x abs(3-bar move) octile x sign | dev 2010-06-06..2021-12-31, full slice | n=89106 gaps; touch 69.9% vs ctrl 78.3% (z=-40.5); fill 48.0% vs 62.1% (z=-59.9); signed fwd return +0.10pt vs -0.07pt (z=+2.8) |
| 72 | 2026-09-04 | FVG (ep02 [17:53]) bullish on 5m: does the gap change what happens next, vs a matched no-gap move? | tf=5m, horizon=60min, controls matched on hour x abs(3-bar move) octile x sign | dev 2010-06-06..2021-12-31, full slice | n=85770 gaps; touch 81.5% vs ctrl 86.7% (z=-29.3); fill 66.6% vs 76.2% (z=-44.1); signed fwd return +0.20pt vs +0.27pt (z=-0.7) |
| 73 | 2026-09-04 | FVG (ep02 [17:53]) bullish on 5m: does the gap change what happens next, vs a matched no-gap move? | tf=5m, horizon=120min, controls matched on hour x abs(3-bar move) octile x sign | dev 2010-06-06..2021-12-31, full slice | n=80829 gaps; touch 86.5% vs ctrl 90.0% (z=-21.8); fill 75.5% vs 82.2% (z=-32.6); signed fwd return +0.45pt vs +0.70pt (z=-1.7) |
| 74 | 2026-09-04 | FVG (ep02 [17:53]) bearish on 5m: does the gap change what happens next, vs a matched no-gap move? | tf=5m, horizon=20min, controls matched on hour x abs(3-bar move) octile x sign | dev 2010-06-06..2021-12-31, full slice | n=81307 gaps; touch 71.6% vs ctrl 79.2% (z=-35.6); fill 50.0% vs 64.2% (z=-57.9); signed fwd return -0.05pt vs -0.35pt (z=+4.7) |
| 75 | 2026-09-04 | FVG (ep02 [17:53]) bearish on 5m: does the gap change what happens next, vs a matched no-gap move? | tf=5m, horizon=60min, controls matched on hour x abs(3-bar move) octile x sign | dev 2010-06-06..2021-12-31, full slice | n=78279 gaps; touch 83.1% vs ctrl 87.5% (z=-24.5); fill 69.0% vs 77.7% (z=-38.8); signed fwd return -0.15pt vs -0.54pt (z=+3.4) |
| 76 | 2026-09-04 | FVG (ep02 [17:53]) bearish on 5m: does the gap change what happens next, vs a matched no-gap move? | tf=5m, horizon=120min, controls matched on hour x abs(3-bar move) octile x sign | dev 2010-06-06..2021-12-31, full slice | n=73774 gaps; touch 88.0% vs ctrl 91.0% (z=-18.6); fill 77.9% vs 84.1% (z=-30.6); signed fwd return -0.42pt vs -0.83pt (z=+2.4) |
| 77 | 2026-09-04 | FVG (ep02 [17:53]) bullish on 15m: does the gap change what happens next, vs a matched no-gap move? | tf=15m, horizon=60min, controls matched on hour x abs(3-bar move) octile x sign | dev 2010-06-06..2021-12-31, full slice | n=28010 gaps; touch 67.4% vs ctrl 76.0% (z=-22.8); fill 47.5% vs 60.4% (z=-30.7); signed fwd return +0.34pt vs +0.46pt (z=-0.7) |
| 78 | 2026-09-04 | FVG (ep02 [17:53]) bullish on 15m: does the gap change what happens next, vs a matched no-gap move? | tf=15m, horizon=180min, controls matched on hour x abs(3-bar move) octile x sign | dev 2010-06-06..2021-12-31, full slice | n=24937 gaps; touch 79.9% vs ctrl 85.1% (z=-15.2); fill 66.5% vs 74.7% (z=-20.0); signed fwd return +0.81pt vs +1.22pt (z=-1.2) |
| 79 | 2026-09-04 | FVG (ep02 [17:53]) bullish on 15m: does the gap change what happens next, vs a matched no-gap move? | tf=15m, horizon=360min, controls matched on hour x abs(3-bar move) octile x sign | dev 2010-06-06..2021-12-31, full slice | n=19999 gaps; touch 85.4% vs ctrl 89.1% (z=-11.2); fill 76.0% vs 81.6% (z=-13.6); signed fwd return +1.15pt vs +3.00pt (z=-3.3) |
| 80 | 2026-09-04 | FVG (ep02 [17:53]) bearish on 15m: does the gap change what happens next, vs a matched no-gap move? | tf=15m, horizon=60min, controls matched on hour x abs(3-bar move) octile x sign | dev 2010-06-06..2021-12-31, full slice | n=24302 gaps; touch 70.1% vs ctrl 78.1% (z=-20.1); fill 49.8% vs 63.8% (z=-31.2); signed fwd return +0.01pt vs -0.74pt (z=+3.4) |
| 81 | 2026-09-04 | FVG (ep02 [17:53]) bearish on 15m: does the gap change what happens next, vs a matched no-gap move? | tf=15m, horizon=180min, controls matched on hour x abs(3-bar move) octile x sign | dev 2010-06-06..2021-12-31, full slice | n=21660 gaps; touch 82.2% vs ctrl 86.5% (z=-12.3); fill 68.9% vs 77.3% (z=-19.6); signed fwd return -0.30pt vs -1.19pt (z=+2.2) |
| 82 | 2026-09-04 | FVG (ep02 [17:53]) bearish on 15m: does the gap change what happens next, vs a matched no-gap move? | tf=15m, horizon=360min, controls matched on hour x abs(3-bar move) octile x sign | dev 2010-06-06..2021-12-31, full slice | n=17212 gaps; touch 87.4% vs ctrl 90.3% (z=-8.6); fill 78.3% vs 83.8% (z=-13.0); signed fwd return -0.62pt vs -1.67pt (z=+1.6) |
| 83 | 2026-09-04 | FVG (ep02 [17:53]) bullish on 60m: does the gap change what happens next, vs a matched no-gap move? | tf=60m, horizon=240min, controls matched on hour x abs(3-bar move) octile x sign | dev 2010-06-06..2021-12-31, full slice | n=6358 gaps; touch 64.0% vs ctrl 74.9% (z=-13.4); fill 46.4% vs 61.2% (z=-16.8); signed fwd return +1.14pt vs +0.40pt (z=+0.9) |
| 84 | 2026-09-04 | FVG (ep02 [17:53]) bullish on 60m: does the gap change what happens next, vs a matched no-gap move? | tf=60m, horizon=720min, controls matched on hour x abs(3-bar move) octile x sign | dev 2010-06-06..2021-12-31, full slice | n=3321 gaps; touch 81.3% vs ctrl 86.4% (z=-5.6); fill 72.2% vs 79.3% (z=-6.7); signed fwd return +1.33pt vs +5.50pt (z=-2.1) |
| 85 | 2026-09-04 | FVG (ep02 [17:53]) bearish on 60m: does the gap change what happens next, vs a matched no-gap move? | tf=60m, horizon=240min, controls matched on hour x abs(3-bar move) octile x sign | dev 2010-06-06..2021-12-31, full slice | n=5047 gaps; touch 68.8% vs ctrl 76.1% (z=-8.3); fill 48.5% vs 62.6% (z=-14.2); signed fwd return -0.23pt vs -4.22pt (z=+4.2) |
| 86 | 2026-09-04 | FVG (ep02 [17:53]) bearish on 60m: does the gap change what happens next, vs a matched no-gap move? | tf=60m, horizon=720min, controls matched on hour x abs(3-bar move) octile x sign | dev 2010-06-06..2021-12-31, full slice | n=2601 gaps; touch 83.6% vs ctrl 88.4% (z=-4.9); fill 74.7% vs 81.2% (z=-5.6); signed fwd return -0.69pt vs -6.83pt (z=+2.5) |

---

## Pre-registered, not yet run

Declared before seeing any result, so nobody can later claim a swept parameter was the
intended one all along. **These do not count toward `n` until they are actually run.**

### Displacement magnitude - 6 points

`THE-MODEL.md` 8.1: outside research found **no canonical ICT threshold exists** - it is
discretionary by design. So it is swept, not adopted.

| candidate | source |
|---|---|
| body-to-range >= 0.60 | `[OUTSIDE]` |
| ATR(14) x 1.5 | `[OUTSIDE]` |
| range vs ~20-bar comparison | `[OUTSIDE]` |
| 2+ consecutive closes | `[OUTSIDE]` |
| 3+ consecutive closes | `[OUTSIDE]` |
| no magnitude gate at all - **the negative control** | DECISIONS.md 14 |

**The last one matters most.** Section 14: never audit without a case where the answer
should be "nothing here". If results are flat across the whole sweep, magnitude barely
matters and his structural gates are doing the work. If they are sharply peaked, the
model's edge depends on a number **he never gave** - which is a finding about the model,
not about the market.

### The roll proxy - 2 points

Ep05 [04:47] rolls on open interest; we have only volume (DECISIONS.md 21.3).
`bars/build_bars.py --roll-shift +3` and `-3`.

The ledger entry that matters is not "we used volume". It is **"we used volume, and
shifting every roll three days each way changed nothing"** - or that it did, which would be
a finding about the model's fragility.

### Money management - 2 points

Ep41's ladder (1% -> 0.5% -> 0.25%, restore after recovering half the loss) against flat
1% sizing, on identical trades. **No entry model needs to be correct for this to be
measurable**, which makes it the cheapest real result available.

---

## Holdout status

**SEALED.** `2024-03-01 -> 2026-02-25`. Never opened.

`slices.py` refuses it without an explicit unseal, and unsealing writes a permanent record
to `holdout_opened.md`. If that file exists, the holdout is spent and no later result on it
is clean.

**After you look, every later choice is contaminated and you cannot un-look.**
