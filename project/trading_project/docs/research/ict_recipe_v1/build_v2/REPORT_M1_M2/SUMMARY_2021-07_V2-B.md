# SUMMARY — 2021-07 / V2-B

- decisions **6300**, plans **10**, independent theses **10**, settled 9, expired 1
- settled on their own entry candle: **3**
- mean R 0.127, median R -1.019, sum 1.141
- bootstrap 95% CI of the mean R: [-0.855, 1.213] over 2000 resamples (contains 0: True)
- max drawdown (verified formula) -3.815; longest negative streak 3
- stop distance median 6.7 pips, 0.489 of the setup candle's range
- median R:R to T1 3.32, to T2 3.96
- half-spread cost as fraction of the stop, median 0.045
- NULL baseline (random direction, same distances): mean R 0.24, CI [-0.850, 1.459], n=9
- elapsed 2.12 s, peak RSS 81340 kB, stopped None

## No-plan reasons

| reason | count |
|---|---|
| outside_session_window | 5508 |
| zone_not_touched | 301 |
| range_position_discount | 216 |
| range_position_premium | 132 |
| range_position_undefined | 60 |
| thesis_already_consumed | 47 |
| no_target_ahead | 12 |
| no_zone_in_direction | 12 |
| criteria_conflict | 2 |

## Fault locator (HYPOTHESIS)

| plan | verdict | category | evidence |
|---|---|---|---|
| `plan:2021-07-06T08:00:00+00:00:1h:fvg:bullish:3150` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-08T07:30:00+00:00:1h:fvg:bearish:3185` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-12T06:00:00+00:00:1h:fvg:bullish:3236` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-14T06:20:00+00:00:1h:fvg:bearish:3285` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-07-14T08:00:00+00:00:1h:sweep:high:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-19T07:00:00+00:00:1h:fvg:bullish:3302` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-07-22T08:10:00+00:00:1h:fvg:bullish:3425` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-07-23T07:10:00+00:00:1h:fvg:bearish:3451` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-27T06:00:00+00:00:1h:fvg:bullish:3497` | settled_target | none visible | T1 touched before the stop under the conservative rule |

## What this does NOT establish

- A settled R is an accounting identity under a stated fill assumption, not a result about a market.
- The bootstrap interval is wide by construction when plans are few; it is reported to be read, not to be beaten.
- The NULL baseline is geometry plus spread, not a strategy.
