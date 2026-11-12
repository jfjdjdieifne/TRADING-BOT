# SUMMARY — 2021-07 / V2-A-OFF

- decisions **6300**, plans **109**, independent theses **109**, settled 106, expired 3
- settled on their own entry candle: **48**
- mean R -0.612, median R -1.115, sum -64.852
- bootstrap 95% CI of the mean R: [-0.951, -0.240] over 2000 resamples (contains 0: False)
- max drawdown (verified formula) -64.852; longest negative streak 21
- stop distance median 2.0 pips, 0.462 of the setup candle's range
- median R:R to T1 4.36, to T2 7.2
- half-spread cost as fraction of the stop, median 0.138
- NULL baseline (random direction, same distances): mean R -0.558, CI [-1.059, 0.008], n=99
- elapsed 9.11 s, peak RSS 81304 kB, stopped None

## No-plan reasons

| reason | count |
|---|---|
| zone_not_touched | 1594 |
| range_position_premium | 1593 |
| range_position_discount | 1491 |
| thesis_already_consumed | 957 |
| no_zone_in_direction | 390 |
| range_position_undefined | 90 |
| criteria_conflict | 59 |
| no_target_ahead | 17 |

## Fault locator (HYPOTHESIS)

| plan | verdict | category | evidence |
|---|---|---|---|
| `plan:2021-07-01T03:45:00+00:00:15m:sweep:high:None` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-01T11:40:00+00:00:15m:fvg:bearish:12256` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-01T19:30:00+00:00:15m:fvg:bearish:12372` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-01T21:15:00+00:00:15m:fvg:bearish:12371` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-02T09:05:00+00:00:15m:fvg:bearish:12424` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-07-02T15:05:00+00:00:15m:fvg:bearish:12449` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-02T20:15:00+00:00:15m:fvg:bearish:12474` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-07-04T22:55:00+00:00:15m:fvg:bullish:12466` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-02T17:30:00+00:00:15m:fvg:bearish:12360` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-04T23:55:00+00:00:15m:fvg:bullish:12465` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-07-05T01:35:00+00:00:15m:fvg:bearish:12486` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-07-05T05:20:00+00:00:15m:fvg:bearish:12500` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-05T07:45:00+00:00:15m:fvg:bearish:12471` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-05T15:15:00+00:00:15m:fvg:bearish:12540` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-05T21:30:00+00:00:15m:fvg:bearish:12574` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-06T08:00:00+00:00:15m:fvg:bullish:12599` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-06T01:30:00+00:00:15m:sweep:low:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-06T08:05:00+00:00:15m:fvg:bullish:12595` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-06T10:35:00+00:00:15m:fvg:bullish:12628` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-06T19:20:00+00:00:15m:fvg:bullish:12659` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-07-07T00:55:00+00:00:15m:fvg:bearish:12684` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-07T06:35:00+00:00:15m:fvg:bearish:12708` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-07T15:00:00+00:00:15m:fvg:bearish:12740` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-07T22:40:00+00:00:15m:fvg:bearish:12763` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-07-08T01:40:00+00:00:15m:fvg:bearish:12779` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-07-08T09:30:00+00:00:15m:fvg:bearish:12734` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-08T19:30:00+00:00:15m:fvg:bearish:12841` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-09T01:00:00+00:00:15m:fvg:bullish:12855` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-09T06:30:00+00:00:15m:fvg:bullish:12818` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-07-09T13:50:00+00:00:15m:fvg:bullish:12927` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |

## What this does NOT establish

- A settled R is an accounting identity under a stated fill assumption, not a result about a market.
- The bootstrap interval is wide by construction when plans are few; it is reported to be read, not to be beaten.
- The NULL baseline is geometry plus spread, not a strategy.
