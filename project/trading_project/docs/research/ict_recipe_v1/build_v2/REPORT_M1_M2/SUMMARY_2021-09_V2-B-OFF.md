# SUMMARY — 2021-09 / V2-B-OFF

- decisions **6336**, plans **39**, independent theses **39**, settled 37, expired 2
- settled on their own entry candle: **7**
- mean R -0.048, median R -1.051, sum -1.788
- bootstrap 95% CI of the mean R: [-0.604, 0.590] over 2000 resamples (contains 0: True)
- max drawdown (verified formula) -9.828; longest negative streak 9
- stop distance median 4.8 pips, 0.629 of the setup candle's range
- median R:R to T1 3.51, to T2 6.03
- half-spread cost as fraction of the stop, median 0.07
- NULL baseline (random direction, same distances): mean R 0.09, CI [-0.560, 0.870], n=31
- elapsed 2.51 s, peak RSS 81304 kB, stopped None

## No-plan reasons

| reason | count |
|---|---|
| range_position_discount | 2196 |
| zone_not_touched | 1765 |
| range_position_premium | 1092 |
| thesis_already_consumed | 742 |
| no_zone_in_direction | 348 |
| range_position_undefined | 72 |
| criteria_conflict | 46 |
| no_target_ahead | 24 |
| range_position_equilibrium | 12 |

## Fault locator (HYPOTHESIS)

| plan | verdict | category | evidence |
|---|---|---|---|
| `plan:2021-09-02T03:00:00+00:00:1h:sweep:low:None` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-03T04:10:00+00:00:1h:fvg:bullish:4180` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-03T09:00:00+00:00:1h:fvg:bullish:4174` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-06T03:25:00+00:00:1h:fvg:bullish:4173` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-07T00:05:00+00:00:1h:fvg:bearish:4206` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-09-07T00:45:00+00:00:1h:fvg:bearish:4199` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-09-07T08:55:00+00:00:1h:fvg:bearish:4232` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-07T23:00:00+00:00:1h:fvg:bearish:4247` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-08T16:50:00+00:00:1h:fvg:bearish:4265` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-08T22:05:00+00:00:1h:fvg:bearish:4271` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-08T19:00:00+00:00:1h:sweep:high:None` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-08T16:25:00+00:00:1h:fvg:bearish:4260` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-09T11:55:00+00:00:1h:fvg:bearish:4257` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-10T00:00:00+00:00:1h:fvg:bullish:4291` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-10T10:45:00+00:00:1h:fvg:bullish:4302` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-13T19:00:00+00:00:1h:fvg:bullish:4338` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-09-14T08:00:00+00:00:1h:fvg:bearish:4315` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-09-14T13:10:00+00:00:1h:fvg:bearish:4309` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-15T01:30:00+00:00:1h:fvg:bearish:4366` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-09-16T05:50:00+00:00:1h:fvg:bullish:4372` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-16T06:55:00+00:00:1h:fvg:bullish:4337` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-16T07:50:00+00:00:1h:fvg:bullish:4336` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-17T04:20:00+00:00:1h:fvg:bearish:4405` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-17T07:35:00+00:00:1h:fvg:bearish:4404` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-17T11:55:00+00:00:1h:fvg:bearish:4403` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-09-20T19:00:00+00:00:1h:fvg:bullish:4458` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-09-21T12:00:00+00:00:1h:fvg:bearish:4434` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-09-22T07:05:00+00:00:1h:fvg:bearish:4481` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-23T05:40:00+00:00:1h:fvg:bearish:4510` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-24T04:50:00+00:00:1h:fvg:bullish:4529` | settled_stop | stop | the stop was reached on a later bar, before T1 |

## What this does NOT establish

- A settled R is an accounting identity under a stated fill assumption, not a result about a market.
- The bootstrap interval is wide by construction when plans are few; it is reported to be read, not to be beaten.
- The NULL baseline is geometry plus spread, not a strategy.
