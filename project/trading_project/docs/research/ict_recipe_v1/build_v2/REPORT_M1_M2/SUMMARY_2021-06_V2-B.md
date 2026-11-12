# SUMMARY — 2021-06 / V2-B

- decisions **6336**, plans **8**, independent theses **8**, settled 8, expired 0
- settled on their own entry candle: **2**
- mean R 0.062, median R -1.056, sum 0.495
- bootstrap 95% CI of the mean R: [-1.062, 1.733] over 2000 resamples (contains 0: True)
- max drawdown (verified formula) -3.343; longest negative streak 2
- stop distance median 4.5 pips, 0.462 of the setup candle's range
- median R:R to T1 5.04, to T2 5.83
- half-spread cost as fraction of the stop, median 0.067
- NULL baseline (random direction, same distances): mean R -0.935, CI [-1.198, -0.534], n=7
- elapsed 2.16 s, peak RSS 81220 kB, stopped None

## No-plan reasons

| reason | count |
|---|---|
| outside_session_window | 5544 |
| zone_not_touched | 236 |
| range_position_premium | 228 |
| range_position_discount | 216 |
| thesis_already_consumed | 99 |
| no_target_ahead | 5 |

## Fault locator (HYPOTHESIS)

| plan | verdict | category | evidence |
|---|---|---|---|
| `plan:2021-06-01T06:00:00+00:00:1h:sweep:low:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-06-07T06:00:00+00:00:1h:fvg:bullish:2632` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-06-08T07:15:00+00:00:1h:fvg:bullish:2657` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-06-11T07:00:00+00:00:1h:sweep:high:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-06-11T06:05:00+00:00:1h:fvg:bearish:2706` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-06-18T08:00:00+00:00:1h:fvg:bearish:2864` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-06-24T07:10:00+00:00:1h:fvg:bearish:2948` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-06-28T06:00:00+00:00:1h:fvg:bullish:2924` | settled_target | none visible | T1 touched before the stop under the conservative rule |

## What this does NOT establish

- A settled R is an accounting identity under a stated fill assumption, not a result about a market.
- The bootstrap interval is wide by construction when plans are few; it is reported to be read, not to be beaten.
- The NULL baseline is geometry plus spread, not a strategy.
