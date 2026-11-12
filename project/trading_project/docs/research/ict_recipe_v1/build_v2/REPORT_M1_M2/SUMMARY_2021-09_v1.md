# SUMMARY — 2021-09 / v1

- decisions **6336**, plans **103**, independent theses **103**, settled 103, expired 0
- settled on their own entry candle: **67**
- mean R -0.607, median R -1.167, sum -62.482
- bootstrap 95% CI of the mean R: [-1.257, 0.446] over 2000 resamples (contains 0: True)
- max drawdown (verified formula) -70.938; longest negative streak 29
- stop distance median 1.3 pips, None of the setup candle's range
- median R:R to T1 3.23, to T2 6.75
- half-spread cost as fraction of the stop, median None
- NULL baseline (random direction, same distances): mean R -0.393, CI [-0.834, 0.091], n=80
- elapsed 66.536 s, peak RSS 81172 kB, stopped None

## No-plan reasons

| reason | count |
|---|---|
| outside_session_window | 5544 |
| range_position_discount | 222 |
| no_zone_in_direction | 164 |
| range_position_premium | 158 |
| zone_not_touched | 132 |
| criteria_conflict | 6 |
| range_position_undefined | 5 |
| no_target_ahead | 2 |

## Fault locator (HYPOTHESIS)

| plan | verdict | category | evidence |
|---|---|---|---|
| `plan:2021-09-01T06:20:00+00:00:sweep:low:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-01T06:50:00+00:00:sweep:low:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-01T07:10:00+00:00:fvg:bullish:49641` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-01T07:20:00+00:00:fvg:bullish:49641` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-09-01T07:30:00+00:00:fvg:bullish:49641` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-09-01T08:55:00+00:00:sweep:low:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-02T06:20:00+00:00:fvg:bullish:49915` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-02T06:25:00+00:00:fvg:bullish:49915` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-02T06:35:00+00:00:fvg:bullish:49915` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-02T08:05:00+00:00:fvg:bullish:49934` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-02T07:55:00+00:00:fvg:bullish:49936` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-03T06:00:00+00:00:sweep:low:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-03T06:05:00+00:00:sweep:low:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-03T06:10:00+00:00:sweep:low:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-03T06:15:00+00:00:fvg:bullish:50199` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-03T06:30:00+00:00:fvg:bullish:50134` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-03T06:35:00+00:00:fvg:bullish:50134` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-03T07:35:00+00:00:sweep:low:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-03T07:40:00+00:00:fvg:bullish:50134` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-03T07:45:00+00:00:fvg:bullish:50134` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-03T07:50:00+00:00:fvg:bullish:50073` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-03T08:50:00+00:00:fvg:bullish:50230` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-06T06:10:00+00:00:sweep:low:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-06T06:55:00+00:00:fvg:bullish:50498` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-06T07:55:00+00:00:sweep:low:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-06T08:35:00+00:00:sweep:low:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-07T06:50:00+00:00:fvg:bearish:50787` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-09-07T07:00:00+00:00:sweep:high:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-07T07:35:00+00:00:fvg:bearish:50766` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-09-07T07:40:00+00:00:fvg:bearish:50766` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |

## What this does NOT establish

- A settled R is an accounting identity under a stated fill assumption, not a result about a market.
- The bootstrap interval is wide by construction when plans are few; it is reported to be read, not to be beaten.
- The NULL baseline is geometry plus spread, not a strategy.
