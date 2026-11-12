# SUMMARY — 2021-09 / V2-A

- decisions **6336**, plans **17**, independent theses **17**, settled 17, expired 0
- settled on their own entry candle: **7**
- mean R 1.524, median R -1.096, sum 25.905
- bootstrap 95% CI of the mean R: [-0.880, 5.720] over 2000 resamples (contains 0: True)
- max drawdown (verified formula) -4.636; longest negative streak 4
- stop distance median 2.5 pips, 0.595 of the setup candle's range
- median R:R to T1 3.39, to T2 3.66
- half-spread cost as fraction of the stop, median 0.12
- NULL baseline (random direction, same distances): mean R -0.483, CI [-1.146, 0.401], n=15
- elapsed 11.41 s, peak RSS 81396 kB, stopped None

## No-plan reasons

| reason | count |
|---|---|
| outside_session_window | 5544 |
| range_position_discount | 219 |
| zone_not_touched | 198 |
| range_position_premium | 141 |
| thesis_already_consumed | 101 |
| no_zone_in_direction | 96 |
| criteria_conflict | 8 |
| range_position_undefined | 6 |
| range_position_equilibrium | 6 |

## Fault locator (HYPOTHESIS)

| plan | verdict | category | evidence |
|---|---|---|---|
| `plan:2021-09-01T06:30:00+00:00:15m:sweep:low:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-01T07:40:00+00:00:15m:fvg:bullish:16551` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-03T06:30:00+00:00:15m:fvg:bullish:16716` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-03T07:50:00+00:00:15m:fvg:bullish:16695` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-07T07:40:00+00:00:15m:fvg:bearish:16922` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-09-08T07:15:00+00:00:15m:sweep:high:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-09T07:50:00+00:00:15m:fvg:bearish:17079` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-09T08:25:00+00:00:15m:fvg:bearish:17036` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-09T08:40:00+00:00:15m:fvg:bearish:17035` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-10T06:50:00+00:00:15m:fvg:bullish:17205` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-09-15T07:15:00+00:00:15m:fvg:bearish:17462` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-15T07:30:00+00:00:15m:fvg:bearish:17461` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-21T06:10:00+00:00:15m:fvg:bearish:17877` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-09-23T06:30:00+00:00:15m:fvg:bearish:18038` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-09-24T06:45:00+00:00:15m:fvg:bullish:18114` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-29T08:45:00+00:00:15m:fvg:bearish:18472` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-09-30T06:45:00+00:00:15m:fvg:bearish:18563` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |

## What this does NOT establish

- A settled R is an accounting identity under a stated fill assumption, not a result about a market.
- The bootstrap interval is wide by construction when plans are few; it is reported to be read, not to be beaten.
- The NULL baseline is geometry plus spread, not a strategy.
