# SUMMARY — 2021-06 / V2-A

- decisions **6336**, plans **14**, independent theses **14**, settled 14, expired 0
- settled on their own entry candle: **8**
- mean R -0.994, median R -1.192, sum -13.921
- bootstrap 95% CI of the mean R: [-1.360, -0.517] over 2000 resamples (contains 0: False)
- max drawdown (verified formula) -13.921; longest negative streak 9
- stop distance median 1.45 pips, 0.192 of the setup candle's range
- median R:R to T1 8.83, to T2 10.23
- half-spread cost as fraction of the stop, median 0.212
- NULL baseline (random direction, same distances): mean R -0.524, CI [-1.398, 0.965], n=12
- elapsed 8.0 s, peak RSS 81172 kB, stopped None

## No-plan reasons

| reason | count |
|---|---|
| outside_session_window | 5544 |
| range_position_premium | 261 |
| range_position_discount | 228 |
| zone_not_touched | 197 |
| thesis_already_consumed | 45 |
| no_zone_in_direction | 18 |
| range_position_undefined | 12 |
| no_target_ahead | 11 |
| criteria_conflict | 6 |

## Fault locator (HYPOTHESIS)

| plan | verdict | category | evidence |
|---|---|---|---|
| `plan:2021-06-02T06:30:00+00:00:15m:fvg:bearish:10307` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-06-03T08:35:00+00:00:15m:fvg:bearish:10405` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-06-04T07:00:00+00:00:15m:fvg:bearish:10491` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-06-09T06:20:00+00:00:15m:fvg:bearish:10779` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-06-09T06:30:00+00:00:15m:sweep:high:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-06-10T07:30:00+00:00:15m:sweep:low:None` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-06-15T08:55:00+00:00:15m:fvg:bullish:11173` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-06-16T06:15:00+00:00:15m:fvg:bullish:11261` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-06-16T07:15:00+00:00:15m:fvg:bullish:11257` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-06-17T08:30:00+00:00:15m:fvg:bearish:11369` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-06-18T06:15:00+00:00:15m:fvg:bearish:11456` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-06-23T07:00:00+00:00:15m:fvg:bullish:11747` | settled_stop | stop | the stop was reached on a later bar, before T1 |
| `plan:2021-06-28T08:20:00+00:00:15m:fvg:bullish:12037` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |
| `plan:2021-06-30T06:35:00+00:00:15m:fvg:bearish:12227` | settled_stop | execution assumption | the entry bar itself reached the stop; entry and stop sit inside one 5m bar |

## What this does NOT establish

- A settled R is an accounting identity under a stated fill assumption, not a result about a market.
- The bootstrap interval is wide by construction when plans are few; it is reported to be read, not to be beaten.
- The NULL baseline is geometry plus spread, not a strategy.
