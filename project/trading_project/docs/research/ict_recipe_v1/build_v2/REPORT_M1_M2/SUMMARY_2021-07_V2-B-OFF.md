# SUMMARY — 2021-07 / V2-B-OFF

- decisions **6300**, plans **39**, independent theses **39**, settled 36, expired 3
- settled on their own entry candle: **6**
- mean R -0.429, median R -1.05, sum -15.432
- bootstrap 95% CI of the mean R: [-0.863, 0.064] over 2000 resamples (contains 0: True)
- max drawdown (verified formula) -17.312; longest negative streak 9
- stop distance median 3.55 pips, 0.354 of the setup candle's range
- median R:R to T1 4.3, to T2 6.0
- half-spread cost as fraction of the stop, median 0.052
- NULL baseline (random direction, same distances): mean R -0.334, CI [-0.803, 0.215], n=32
- elapsed 2.22 s, peak RSS 81340 kB, stopped None

## No-plan reasons

| reason | count |
|---|---|
| zone_not_touched | 1963 |
| range_position_premium | 1608 |
| range_position_discount | 1428 |
| thesis_already_consumed | 896 |
| no_zone_in_direction | 204 |
| range_position_undefined | 96 |
| criteria_conflict | 29 |
| no_target_ahead | 25 |
| range_position_equilibrium | 12 |

## Fault locator (HYPOTHESIS)

| plan | verdict | category | evidence |
|---|---|---|---|
| `plan:2021-07-01T10:20:00+00:00:1h:fvg:bearish:3076` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-01T11:40:00+00:00:1h:fvg:bearish:3065` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-02T05:35:00+00:00:1h:fvg:bearish:3098` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-07-02T14:00:00+00:00:1h:sweep:high:None` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-05T23:05:00+00:00:1h:fvg:bearish:3144` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-05T23:15:00+00:00:1h:fvg:bearish:3143` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-06T00:00:00+00:00:1h:fvg:bullish:3117` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-07-06T08:00:00+00:00:1h:fvg:bullish:3150` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-06T14:00:00+00:00:1h:sweep:low:None` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-06T19:20:00+00:00:1h:fvg:bullish:3165` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-08T05:15:00+00:00:1h:fvg:bearish:3191` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-07T18:10:00+00:00:1h:fvg:bearish:3185` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-08T19:30:00+00:00:1h:fvg:bearish:3211` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-12T02:00:00+00:00:1h:fvg:bullish:3237` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-12T04:05:00+00:00:1h:fvg:bullish:3236` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-12T10:05:00+00:00:1h:fvg:bullish:3229` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-12T17:00:00+00:00:1h:fvg:bullish:3257` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-07-13T03:15:00+00:00:1h:fvg:bearish:3155` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-07-14T02:00:00+00:00:1h:fvg:bearish:3287` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-14T03:15:00+00:00:1h:fvg:bearish:3286` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-14T06:20:00+00:00:1h:fvg:bearish:3285` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-07-14T16:00:00+00:00:1h:fvg:bearish:3280` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-15T11:30:00+00:00:1h:fvg:bullish:3304` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-15T16:05:00+00:00:1h:fvg:bullish:3303` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-16T15:00:00+00:00:1h:fvg:bearish:3350` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-19T07:00:00+00:00:1h:fvg:bullish:3302` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-07-22T08:10:00+00:00:1h:fvg:bullish:3425` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-07-22T15:35:00+00:00:1h:fvg:bullish:3420` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-22T20:00:00+00:00:1h:fvg:bullish:3454` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-23T00:00:00+00:00:1h:fvg:bearish:3451` | settled_stop | stop | the stop was reached on a later bar, before T1 |

## What this does NOT establish

- A settled R is an accounting identity under a stated fill assumption, not a result about a market.
- The bootstrap interval is wide by construction when plans are few; it is reported to be read, not to be beaten.
- The NULL baseline is geometry plus spread, not a strategy.
