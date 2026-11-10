# SUMMARY — 2021-09 / V2-B

- decisions **6336**, plans **16**, independent theses **16**, settled 16, expired 0
- settled on their own entry candle: **3**
- mean R -0.627, median R -1.051, sum -10.033
- bootstrap 95% CI of the mean R: [-1.169, 0.040] over 2000 resamples (contains 0: True)
- max drawdown (verified formula) -13.048; longest negative streak 9
- stop distance median 4.9 pips, 0.39 of the setup candle's range
- median R:R to T1 5.71, to T2 7.36
- half-spread cost as fraction of the stop, median 0.061
- NULL baseline (random direction, same distances): mean R -0.599, CI [-1.409, 0.714], n=13
- elapsed 2.68 s, peak RSS 81340 kB, stopped None

## No-plan reasons

| reason | count |
|---|---|
| outside_session_window | 5544 |
| range_position_discount | 264 |
| zone_not_touched | 179 |
| range_position_premium | 120 |
| thesis_already_consumed | 117 |
| range_position_undefined | 36 |
| criteria_conflict | 31 |
| no_zone_in_direction | 24 |
| no_target_ahead | 5 |

## Fault locator (HYPOTHESIS)

| plan | verdict | category | evidence |
|---|---|---|---|
| `plan:2021-09-03T08:10:00+00:00:1h:sweep:low:None` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-06T06:05:00+00:00:1h:fvg:bullish:4173` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-07T08:55:00+00:00:1h:fvg:bearish:4232` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-09T08:00:00+00:00:1h:sweep:high:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-14T08:00:00+00:00:1h:fvg:bearish:4315` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-09-15T08:00:00+00:00:1h:fvg:bearish:4366` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-16T06:20:00+00:00:1h:fvg:bullish:4372` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-16T06:30:00+00:00:1h:fvg:bullish:4338` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-16T06:55:00+00:00:1h:fvg:bullish:4337` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-16T07:50:00+00:00:1h:fvg:bullish:4336` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-17T07:35:00+00:00:1h:fvg:bearish:4404` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-22T07:05:00+00:00:1h:fvg:bearish:4481` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-23T06:20:00+00:00:1h:fvg:bearish:4510` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-24T06:05:00+00:00:1h:fvg:bullish:4529` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-28T06:00:00+00:00:1h:fvg:bearish:4571` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-09-30T07:25:00+00:00:1h:fvg:bearish:4628` | settled_target | none visible | T1 touched before the stop under the conservative rule |

## What this does NOT establish

- A settled R is an accounting identity under a stated fill assumption, not a result about a market.
- The bootstrap interval is wide by construction when plans are few; it is reported to be read, not to be beaten.
- The NULL baseline is geometry plus spread, not a strategy.
