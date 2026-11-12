# SUMMARY — 2021-09 / V2-A-OFF

- decisions **6336**, plans **98**, independent theses **98**, settled 95, expired 3
- settled on their own entry candle: **32**
- mean R -0.12, median R -1.117, sum -11.387
- bootstrap 95% CI of the mean R: [-0.765, 0.763] over 2000 resamples (contains 0: True)
- max drawdown (verified formula) -34.052; longest negative streak 12
- stop distance median 2.1 pips, 0.481 of the setup candle's range
- median R:R to T1 3.49, to T2 4.94
- half-spread cost as fraction of the stop, median 0.133
- NULL baseline (random direction, same distances): mean R 1.903, CI [-0.730, 6.536], n=81
- elapsed 11.22 s, peak RSS 81412 kB, stopped None

## No-plan reasons

| reason | count |
|---|---|
| range_position_discount | 1884 |
| zone_not_touched | 1859 |
| range_position_premium | 1197 |
| thesis_already_consumed | 766 |
| no_zone_in_direction | 363 |
| range_position_undefined | 84 |
| criteria_conflict | 41 |
| range_position_equilibrium | 27 |
| no_target_ahead | 17 |

## Fault locator (HYPOTHESIS)

| plan | verdict | category | evidence |
|---|---|---|---|
| `plan:2021-09-01T04:15:00+00:00:15m:sweep:low:None` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-01T05:50:00+00:00:15m:fvg:bullish:16399` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-01T07:40:00+00:00:15m:fvg:bullish:16551` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-01T17:35:00+00:00:15m:fvg:bullish:16582` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-02T11:20:00+00:00:15m:fvg:bullish:16658` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-02T12:40:00+00:00:15m:fvg:bullish:16643` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-02T16:35:00+00:00:15m:fvg:bullish:16678` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-09-03T05:05:00+00:00:15m:fvg:bullish:16716` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-09-03T07:50:00+00:00:15m:fvg:bullish:16695` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-03T19:15:00+00:00:15m:fvg:bullish:16781` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-06T03:45:00+00:00:15m:fvg:bullish:16690` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-06T12:00:00+00:00:15m:fvg:bullish:16852` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-06T14:30:00+00:00:15m:fvg:bullish:16863` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-06T17:30:00+00:00:15m:fvg:bullish:16879` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-07T01:20:00+00:00:15m:fvg:bearish:16812` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-07T03:05:00+00:00:15m:fvg:bearish:16916` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-07T03:15:00+00:00:15m:sweep:high:None` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-09-07T07:40:00+00:00:15m:fvg:bearish:16922` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-09-07T09:05:00+00:00:15m:fvg:bearish:16939` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-07T13:50:00+00:00:15m:fvg:bearish:16959` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-09-07T15:45:00+00:00:15m:fvg:bearish:16964` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-08T00:40:00+00:00:15m:fvg:bearish:16983` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-08T04:55:00+00:00:15m:fvg:bearish:17017` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-09-08T12:45:00+00:00:15m:fvg:bearish:17036` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-09-08T15:50:00+00:00:15m:fvg:bearish:17056` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-08T22:25:00+00:00:15m:fvg:bearish:17083` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-09T05:15:00+00:00:15m:fvg:bearish:17117` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-09T05:35:00+00:00:15m:fvg:bearish:17116` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-09T07:50:00+00:00:15m:fvg:bearish:17079` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-09T09:35:00+00:00:15m:fvg:bearish:17136` | settled_stop | stop | the stop was reached on a later bar, before T1 |

## What this does NOT establish

- A settled R is an accounting identity under a stated fill assumption, not a result about a market.
- The bootstrap interval is wide by construction when plans are few; it is reported to be read, not to be beaten.
- The NULL baseline is geometry plus spread, not a strategy.
