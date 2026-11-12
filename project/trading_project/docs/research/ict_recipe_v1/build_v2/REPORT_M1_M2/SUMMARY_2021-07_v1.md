# SUMMARY — 2021-07 / v1

- decisions **6300**, plans **104**, independent theses **104**, settled 103, expired 1
- settled on their own entry candle: **74**
- mean R -0.954, median R -1.2, sum -98.24
- bootstrap 95% CI of the mean R: [-1.198, -0.671] over 2000 resamples (contains 0: False)
- max drawdown (verified formula) -106.697; longest negative streak 24
- stop distance median 1.5 pips, None of the setup candle's range
- median R:R to T1 4.0, to T2 6.0
- half-spread cost as fraction of the stop, median None
- NULL baseline (random direction, same distances): mean R -0.285, CI [-0.869, 0.437], n=93
- elapsed 52.381 s, peak RSS 81180 kB, stopped None

## No-plan reasons

| reason | count |
|---|---|
| outside_session_window | 5508 |
| range_position_discount | 218 |
| range_position_premium | 177 |
| no_zone_in_direction | 146 |
| zone_not_touched | 126 |
| range_position_undefined | 10 |
| no_target_ahead | 5 |
| range_position_equilibrium | 3 |
| criteria_conflict | 3 |

## Fault locator (HYPOTHESIS)

| plan | verdict | category | evidence |
|---|---|---|---|
| `plan:2021-07-01T06:55:00+00:00:fvg:bearish:36888` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-01T08:15:00+00:00:fvg:bearish:36983` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-02T08:20:00+00:00:sweep:high:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-02T08:30:00+00:00:sweep:high:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-02T08:35:00+00:00:sweep:high:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-05T07:55:00+00:00:sweep:high:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-05T08:10:00+00:00:sweep:high:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-05T08:40:00+00:00:sweep:high:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-05T08:45:00+00:00:sweep:high:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-06T06:40:00+00:00:sweep:low:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-06T06:50:00+00:00:sweep:low:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-06T07:05:00+00:00:sweep:low:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-06T06:45:00+00:00:fvg:bullish:37823` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-06T07:00:00+00:00:fvg:bullish:37823` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-06T07:40:00+00:00:fvg:bullish:37813` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-06T08:05:00+00:00:fvg:bullish:37773` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-06T08:30:00+00:00:sweep:low:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-07T06:55:00+00:00:fvg:bearish:38120` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-07T07:15:00+00:00:fvg:bearish:38124` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-07-07T07:20:00+00:00:fvg:bearish:38124` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-07-07T07:25:00+00:00:fvg:bearish:38124` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-07-07T07:45:00+00:00:fvg:bearish:38124` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-08T06:45:00+00:00:fvg:bearish:38405` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-08T06:55:00+00:00:fvg:bearish:38405` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-07-08T07:00:00+00:00:fvg:bearish:38405` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-08T07:25:00+00:00:sweep:high:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-08T07:30:00+00:00:sweep:high:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-08T07:35:00+00:00:sweep:high:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-09T06:20:00+00:00:sweep:low:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-07-09T07:00:00+00:00:sweep:low:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |

## What this does NOT establish

- A settled R is an accounting identity under a stated fill assumption, not a result about a market.
- The bootstrap interval is wide by construction when plans are few; it is reported to be read, not to be beaten.
- The NULL baseline is geometry plus spread, not a strategy.
