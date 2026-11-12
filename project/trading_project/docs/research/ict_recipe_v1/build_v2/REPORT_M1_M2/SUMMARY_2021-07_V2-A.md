# SUMMARY — 2021-07 / V2-A

- decisions **6300**, plans **26**, independent theses **26**, settled 26, expired 0
- settled on their own entry candle: **14**
- mean R -0.278, median R -1.098, sum -7.225
- bootstrap 95% CI of the mean R: [-0.778, 0.298] over 2000 resamples (contains 0: True)
- max drawdown (verified formula) -12.575; longest negative streak 6
- stop distance median 2.9 pips, 0.414 of the setup candle's range
- median R:R to T1 5.07, to T2 7.85
- half-spread cost as fraction of the stop, median 0.095
- NULL baseline (random direction, same distances): mean R 0.101, CI [-1.108, 1.731], n=24
- elapsed 8.7 s, peak RSS 81304 kB, stopped None

## No-plan reasons

| reason | count |
|---|---|
| outside_session_window | 5508 |
| range_position_discount | 195 |
| zone_not_touched | 190 |
| range_position_premium | 180 |
| thesis_already_consumed | 80 |
| no_zone_in_direction | 72 |
| range_position_undefined | 36 |
| no_target_ahead | 7 |
| criteria_conflict | 6 |

## Fault locator (HYPOTHESIS)

| plan | verdict | category | evidence |
|---|---|---|---|
| `plan:2021-07-05T06:30:00+00:00:15m:fvg:bearish:12486` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-05T07:45:00+00:00:15m:fvg:bearish:12471` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-06T08:00:00+00:00:15m:fvg:bullish:12599` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-06T08:05:00+00:00:15m:fvg:bullish:12595` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-07T06:35:00+00:00:15m:fvg:bearish:12708` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-07T08:15:00+00:00:15m:sweep:high:None` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-09T06:30:00+00:00:15m:fvg:bullish:12818` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-07-12T06:05:00+00:00:15m:fvg:bullish:12941` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-15T07:25:00+00:00:15m:fvg:bullish:13274` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-15T08:00:00+00:00:15m:sweep:low:None` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-07-16T08:40:00+00:00:15m:fvg:bearish:13321` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-20T07:15:00+00:00:15m:fvg:bearish:13569` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-20T08:25:00+00:00:15m:fvg:bearish:13560` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-21T08:45:00+00:00:15m:fvg:bearish:13648` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-21T08:50:00+00:00:15m:fvg:bearish:13596` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-22T06:10:00+00:00:15m:fvg:bullish:13746` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-07-22T08:20:00+00:00:15m:fvg:bullish:13698` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-07-23T07:50:00+00:00:15m:fvg:bearish:13843` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-23T08:10:00+00:00:15m:fvg:bearish:13801` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-26T06:15:00+00:00:15m:fvg:bullish:13947` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-26T06:25:00+00:00:15m:fvg:bullish:13953` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-26T08:00:00+00:00:15m:fvg:bullish:13960` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-07-27T07:10:00+00:00:15m:fvg:bullish:13966` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-27T06:15:00+00:00:15m:fvg:bullish:13986` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-07-28T06:45:00+00:00:15m:fvg:bullish:14076` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-07-29T06:45:00+00:00:15m:fvg:bullish:14230` | settled_target | none visible | T1 touched before the stop under the conservative rule |

## What this does NOT establish

- A settled R is an accounting identity under a stated fill assumption, not a result about a market.
- The bootstrap interval is wide by construction when plans are few; it is reported to be read, not to be beaten.
- The NULL baseline is geometry plus spread, not a strategy.
