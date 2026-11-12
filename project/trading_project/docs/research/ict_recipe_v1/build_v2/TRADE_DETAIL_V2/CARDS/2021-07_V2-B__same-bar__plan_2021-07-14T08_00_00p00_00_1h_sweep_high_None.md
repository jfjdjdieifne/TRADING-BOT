# TRADE CARD — 2021-07_V2-B — plan:2021-07-14T08:00:00+00:00:1h:sweep:high:None

- run id: `2021-07_V2-B` · month `2021-07` · variant `V2-B`
- plan id: `plan:2021-07-14T08:00:00+00:00:1h:sweep:high:None`
- thesis id: `1h:sweep:high:None:bearish` = setup frame `1h` + zone `1h:sweep:high:None` + direction `bearish` + sweep/formation reference `None`
- why this plan: **same-bar (seeded)**

## 1. The story, in plain English

1. The daily bias was read as `DOWN` on completed buckets.
2. On the 1h frame a sweep_level formed between 1.17849 and 1.17853.
3. Price was in the `premium` part of the dealing range.
4. The engine waited for a 5m bar whose close came back into that zone.
5. When it did, the hypothetical plan was armed: bearish from 1.17849.
6. The thesis dies at 1.17853 (the far side of the zone) and aims at 1.17809.
7. The zone was read at setup candle None, which had closed before the decision.
8. Everything below is accounting under that reading — no position ever existed.

## 2. Setup-frame context

| # | open (UTC) | close (UTC) | open | high | low | close |
|---|---|---|---|---|---|---|
| 0 | 2021-01-03T22:00:00+00:00 | 2021-01-03T23:00:00+00:00 | 1.22396 | 1.22420 | 1.22296 | 1.22333 |
| 1 | 2021-01-03T23:00:00+00:00 | 2021-01-04T00:00:00+00:00 | 1.22331 | 1.22527 | 1.22304 | 1.22500 |
| 2 | 2021-01-04T00:00:00+00:00 | 2021-01-04T01:00:00+00:00 | 1.22499 | 1.22499 | 1.22385 | 1.22407 |
| 3 | 2021-01-04T01:00:00+00:00 | 2021-01-04T02:00:00+00:00 | 1.22408 | 1.22556 | 1.22397 | 1.22525 |

- dealing range (setup frame): `1.17809` – `1.17853`, equilibrium `1.1783100000000002`, position `premium`, ratio `0.6363636363632693` (INSIDE_RANGE)
- swings on the setup frame: []
- sweep high `{'answer': 'YES', 'level': 1.17853}` · sweep low `{'answer': 'NO', 'level': 1.17809}`
- displacement `{'answer': 'NO', 'ratio': 0.5789473684210527}` · structure shift `None`
- order block at the decision: `None`
- bias source: daily `DOWN`, weekly `UP`, conflict `True`

## 3. Causality table

| item | frame | index | close time | decision time | verdict |
|---|---|---|---|---|---|
| zone candle | 1h | 0 | 2021-01-03T23:00:00+00:00 | 2021-07-14T08:00:00+00:00 | OK |
| dealing range swings | 1h | 478/478 | (closed before decision) | 2021-07-14T08:00:00+00:00 | OK |
| bias buckets | daily/weekly from 5m | — | (completed buckets only) | 2021-07-14T08:00:00+00:00 | OK |

## 4. Execution, 5m candle by candle

| bar | time (UTC) | bid O/H/L/C | ask O/H/L/C | touched? | closed inside? | hit stop? | hit T1? | spread |
|---|---|---|---|---|---|---|---|---|
| 39575 | 2021-07-14T08:05:00+00:00 | 1.17852/1.17886/1.17834/1.17880 | 1.17853/1.17888/1.17836/1.17882 | yes | no | YES | no | 0.000010 |
| 39576 | 2021-07-14T08:10:00+00:00 | 1.17879/1.17894/1.17856/1.17872 | 1.17882/1.17897/1.17857/1.17875 | no | no | YES | no | 0.000030 |

- entry candle: bar 39575 · fill price `1.17849` · convention: **limit at the zone edge, v1 convention** (the bar's own range must contain the entry price).

## 5. Levels

| level | price | distance (pips) | frame |
|---|---|---|---|
| entry | 1.17849 | — | 1h zone edge |
| stop | 1.17853 | 0.40 | 1h far edge |
| T1 | 1.17809 | 4.00 | 1h pool |
| T2 (informational) | 1.17717 | 13.20 | 1h pool |

- R:R to T1 `10.000`, to T2 `33.000`
- half-spread `0.05` pips; spread as a fraction of the stop `0.250`; stop as a fraction of the setup candle range `0.030`

## 6. Outcome

- state `settled_stop` · reason `stop_touched` · exit bar 39575 · exit price `1.17853`
- hypothetical R reported by the engine: **-1.2500**

## 7. Independent replay

```
for each 5m bar after the decision bar, up to 288 bars:
    if not (low <= entry <= high): continue          # not triggered yet
    if direction bullish and low <= stop, or bearish and high >= stop: settle at stop
    elif bullish and high >= t1, or bearish and low <= t1:        settle at t1
    gross = (exit - entry) for bullish, (entry - exit) for bearish
    cost  = half_spread_at_decision + spread_of_exit_bar / 2
    R     = (gross - cost) / |entry - stop|
```
- replay: `stop_touched` at bar 39575, price `1.17853` → R `-1.250000`
- tolerance `1e-09` (floating point only) → **MATCH**

## 8. Checklist

| item | verdict | number |
|---|---|---|
| stop on the correct side of entry | PASS | entry 1.178490 stop 1.178530 |
| T1 beyond entry | PASS | t1 1.17809 |
| entry inside the zone | PASS | zone [1.178490, 1.178530] |
| T1 untaken between its formation and arming | PASS | NOT_EVALUABLE (no pool formation index in the record); proxy: 81 close(s) beyond T1 in the 288 bars before arming |
| fill convention consistent (limit at the zone edge) | PASS | entry 1.178490 vs edge 1.178490 |
| half-spread applied once per side | PASS | half 0.00000500 vs bar spread/2 0.00000500 |
| same-bar rule applied as declared (stop first) | PASS | same-bar settlement: True |
| first evaluation at or after the arming bar | PASS | decision bar 39574 (+1), trigger bar 39575 |
| R:R formula correct | PASS | rr 9.999999999988898 |
| replay reproduces the reported R | PASS | replay stop_touched R=-1.2500000000013878 at bar 39575 vs engine stop_touched R=-1.2500000000013878 at bar 39575 |

## 9. What a human expert would need to judge — NOT JUDGED BY THE AGENT

1. Is this `sweep_level` a valid one on the 1h frame, and would you have used the same two candles to draw it?
2. Is the `premium` reading of the dealing range the one you would take at this time, or is the swing pair wrong?
3. Was a bearish continuation the right expectation after this sweep, given the session window?

## What this does NOT establish

- One card is one plan: it says nothing about the variant's edge, and R is hypothetical under a stated fill assumption.
- The checklist checks arithmetic, sides and conventions; it cannot check whether the reading was right.
