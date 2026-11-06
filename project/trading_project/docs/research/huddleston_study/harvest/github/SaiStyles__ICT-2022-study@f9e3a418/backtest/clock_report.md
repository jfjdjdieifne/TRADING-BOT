# The clock, and the vetoes against matched nulls

`dev` slice, **2,970 full sessions**. Ledger n = 165. Reserve untouched, holdout SEALED.

**The bar is |z| > 3.0**, not 2.0. `[OUTSIDE]` Harvey, Liu and Zhu
documented 316+ tested factors and concluded a new one must clear t = 3.0.
With this ledger at n = 165, 2.0 is meaningless here.

## A. Is his clock special?

Every result before this was measured INSIDE the killzone, which assumes
the answer. `[OUTSIDE]` Intraday volume and volatility are U-shaped, so his
windows beat a random-TIME null whether or not they carry information. The
control here is **other windows of the same sessions**, and opportunity is
divided by window length - otherwise the test just rewards longer windows.

**Percentile is the answer, not the raw number.** 100 means his window beat
every same-length control; 50 means it is an average time of day.

| his window | from-to | mins | opportunity | **pctile** | efficiency | **pctile** | best control |
|---|---|---|---|---|---|---|---|
| AM killzone 0830-1100 (ep02 42:40) | 08:30-11:00 | 150 | 32.2pt | **100** | 0.467 | **100** | 10:00 (30.8pt) |
| 0930-1100 (ep06 33:16) | 09:30-11:00 | 90 | 30.5pt | **100** | 0.479 | **100** | 08:30 (24.2pt) |
| London close 1000-1100 (ep40 17:36) | 10:00-11:00 | 60 | 22.2pt | **93** | 0.467 | **90** | 09:30 (26.5pt) |
| on-close macro 1500-1600 (ep32 11:32) | 15:00-16:00 | 60 | 15.8pt | **83** | 0.456 | **73** | 09:30 (26.5pt) |
| PM 1330-1600 (ep41 06:20) | 13:30-16:00 | 150 | 23.8pt | **68** | 0.451 | **40** | 09:30 (35.5pt) |
| LUNCH 1200-1300 (ep05 10:04) | 12:00-13:00 | 60 | 13.8pt | **63** | 0.442 | **33** | 09:30 (26.5pt) |
| 0830-0930 only (ep25 34:43) | 08:30-09:30 | 60 | 10.8pt | **50** | 0.435 | **13** | 09:30 (26.5pt) |
| London killzone (ep03 32:59) | 02:00-05:00 | 180 | 15.5pt | **32** | 0.453 | **59** | 09:30 (37.5pt) |
| pre-830 (ep09 12:44 overnight) | 05:00-08:30 | 210 | 15.5pt | **11** | 0.440 | **5** | 09:30 (39.0pt) |

## B. Vetoes against a volatility-matched null

Controls are drawn to match the selection's **prior-day range** decile by
decile. `overnight_run`'s old z = -18.6 against random days was measuring
volatility autocorrelation - volatile days have wider mornings. Matching
removes that by construction, so what is left is the rule.

Prior-day range is known **before** the session opens, so it is a legitimate
control rather than a peek.

| veto | refused | refused-day efficiency | vs traded | **matched z** | refused-day opportunity | vs traded | **matched z** |
|---|---|---|---|---|---|---|---|
| wednesday_done (ep37 05:18) | 40% | 0.459 | 0.475 | **-2.65** | 35pt | 32pt | **+nan** |
| midrange band=0.05 (ep32 04:56) | 7% | 0.439 | 0.468 | **-1.23** | 34pt | 32pt | **+1.02** |
| midrange band=0.10 (ep32 04:56) | 14% | 0.460 | 0.468 | **-0.69** | 34pt | 32pt | **+2.18** |
| midrange band=0.20 (ep32 04:56) | 30% | 0.455 | 0.476 | **-2.30** | 32pt | 33pt | **+nan** |

A `nan` z means the matched null had too little spread to support one -
`nulls.py` refuses to print a spectacular number rather than a real one.
