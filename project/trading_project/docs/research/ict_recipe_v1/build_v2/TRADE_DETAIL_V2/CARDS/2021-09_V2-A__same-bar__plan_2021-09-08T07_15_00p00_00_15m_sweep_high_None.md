# TRADE CARD — 2021-09_V2-A — plan:2021-09-08T07:15:00+00:00:15m:sweep:high:None

- run id: `2021-09_V2-A` · month `2021-09` · variant `V2-A`
- plan id: `plan:2021-09-08T07:15:00+00:00:15m:sweep:high:None`
- thesis id: `15m:sweep:high:None:bearish` = setup frame `15m` + zone `15m:sweep:high:None` + direction `bearish` + sweep/formation reference `None`
- why this plan: **same-bar (seeded)**

## 1. The story, in plain English

1. The daily bias was read as `DOWN` on completed buckets.
2. On the 15m frame a sweep_level formed between 1.18382 and 1.18399.
3. Price was in the `premium` part of the dealing range.
4. The engine waited for a 5m bar whose close came back into that zone.
5. When it did, the hypothetical plan was armed: bearish from 1.18382.
6. The thesis dies at 1.18399 (the far side of the zone) and aims at 1.18284.
7. The zone was read at setup candle None, which had closed before the decision.
8. Everything below is accounting under that reading — no position ever existed.

## 2. Setup-frame context

| # | open (UTC) | close (UTC) | open | high | low | close |
|---|---|---|---|---|---|---|
| 0 | 2021-01-03T22:00:00+00:00 | 2021-01-03T22:15:00+00:00 | 1.22396 | 1.22420 | 1.22296 | 1.22315 |
| 1 | 2021-01-03T22:15:00+00:00 | 2021-01-03T22:30:00+00:00 | 1.22324 | 1.22387 | 1.22324 | 1.22370 |
| 2 | 2021-01-03T22:30:00+00:00 | 2021-01-03T22:45:00+00:00 | 1.22367 | 1.22400 | 1.22325 | 1.22339 |
| 3 | 2021-01-03T22:45:00+00:00 | 2021-01-03T23:00:00+00:00 | 1.22340 | 1.22348 | 1.22325 | 1.22333 |

- dealing range (setup frame): `1.18284` – `1.18382`, equilibrium `1.18333`, position `premium`, ratio `0.887755102040784` (INSIDE_RANGE)
- swings on the setup frame: []
- sweep high `{'answer': 'YES', 'level': 1.18382}` · sweep low `{'answer': 'NO', 'level': 1.18284}`
- displacement `{'answer': 'NO', 'ratio': 0.38461538461528605}` · structure shift `None`
- order block at the decision: `None`
- bias source: daily `DOWN`, weekly `UP`, conflict `True`

## 3. Causality table

| item | frame | index | close time | decision time | verdict |
|---|---|---|---|---|---|
| zone candle | 15m | 0 | 2021-01-03T22:15:00+00:00 | 2021-09-08T07:15:00+00:00 | OK |
| dealing range swings | 15m | 1918/1918 | (closed before decision) | 2021-09-08T07:15:00+00:00 | OK |
| bias buckets | daily/weekly from 5m | — | (completed buckets only) | 2021-09-08T07:15:00+00:00 | OK |

## 4. Execution, 5m candle by candle

| bar | time (UTC) | bid O/H/L/C | ask O/H/L/C | touched? | closed inside? | hit stop? | hit T1? | spread |
|---|---|---|---|---|---|---|---|---|
| 51085 | 2021-09-08T07:20:00+00:00 | 1.18400/1.18428/1.18389/1.18399 | 1.18402/1.18431/1.18392/1.18402 | no | yes | YES | no | 0.000020 |
| 51086 | 2021-09-08T07:25:00+00:00 | 1.18398/1.18426/1.18387/1.18407 | 1.18401/1.18428/1.18390/1.18410 | no | no | YES | no | 0.000030 |
| 51087 | 2021-09-08T07:30:00+00:00 | 1.18408/1.18429/1.18395/1.18424 | 1.18411/1.18431/1.18399/1.18426 | no | no | YES | no | 0.000030 |
| 51088 | 2021-09-08T07:35:00+00:00 | 1.18423/1.18435/1.18394/1.18409 | 1.18426/1.18436/1.18396/1.18412 | no | no | YES | no | 0.000030 |
| 51089 | 2021-09-08T07:40:00+00:00 | 1.18410/1.18448/1.18390/1.18399 | 1.18413/1.18451/1.18393/1.18402 | no | yes | YES | no | 0.000030 |
| 51090 | 2021-09-08T07:45:00+00:00 | 1.18402/1.18403/1.18331/1.18335 | 1.18404/1.18405/1.18333/1.18338 | yes | no | YES | no | 0.000020 |
| 51091 | 2021-09-08T07:50:00+00:00 | 1.18334/1.18351/1.18318/1.18335 | 1.18337/1.18353/1.18320/1.18338 | no | no | no | no | 0.000030 |

- entry candle: bar 51090 · fill price `1.18382` · convention: **limit at the zone edge, v1 convention** (the bar's own range must contain the entry price).

## 5. Levels

| level | price | distance (pips) | frame |
|---|---|---|---|
| entry | 1.18382 | — | 15m zone edge |
| stop | 1.18399 | 1.70 | 15m far edge |
| T1 | 1.18284 | 9.80 | 15m pool |

- R:R to T1 `5.765`, to T2 `—`
- half-spread `0.15` pips; spread as a fraction of the stop `0.176`; stop as a fraction of the setup candle range `0.163`

## 6. Outcome

- state `settled_stop` · reason `stop_touched` · exit bar 51090 · exit price `1.18399`
- hypothetical R reported by the engine: **-1.1471**

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
- replay: `stop_touched` at bar 51090, price `1.18399` → R `-1.147059`
- tolerance `1e-09` (floating point only) → **MATCH**

## 8. Checklist

| item | verdict | number |
|---|---|---|
| stop on the correct side of entry | PASS | entry 1.183820 stop 1.183990 |
| T1 beyond entry | PASS | t1 1.18284 |
| entry inside the zone | PASS | zone [1.183820, 1.183990] |
| T1 untaken between its formation and arming | PASS | NOT_EVALUABLE (no pool formation index in the record); proxy: 0 close(s) beyond T1 in the 288 bars before arming |
| fill convention consistent (limit at the zone edge) | PASS | entry 1.183820 vs edge 1.183820 |
| half-spread applied once per side | PASS | half 0.00001500 vs bar spread/2 0.00001500 |
| same-bar rule applied as declared (stop first) | PASS | same-bar settlement: True |
| first evaluation at or after the arming bar | PASS | decision bar 51084 (+1), trigger bar 51090 |
| R:R formula correct | PASS | rr 5.764705882354017 |
| replay reproduces the reported R | PASS | replay stop_touched R=-1.147058823529719 at bar 51090 vs engine stop_touched R=-1.147058823529719 at bar 51090 |

## 9. What a human expert would need to judge — NOT JUDGED BY THE AGENT

1. Is this `sweep_level` a valid one on the 15m frame, and would you have used the same two candles to draw it?
2. Is the `premium` reading of the dealing range the one you would take at this time, or is the swing pair wrong?
3. Was a bearish continuation the right expectation after this sweep, given the session window?

## What this does NOT establish

- One card is one plan: it says nothing about the variant's edge, and R is hypothetical under a stated fill assumption.
- The checklist checks arithmetic, sides and conventions; it cannot check whether the reading was right.
