# TRADE CARD — 2021-09_v1 — plan:2021-09-03T06:10:00+00:00:sweep:low:None

- run id: `2021-09_v1` · month `2021-09` · variant `v1`
- plan id: `plan:2021-09-03T06:10:00+00:00:sweep:low:None`
- thesis id: `—` = setup frame `5m` + zone `sweep:low:None` + direction `bullish` + sweep/formation reference `None`
- why this plan: **same-bar (seeded)**

## 1. The story, in plain English

1. The daily bias was read as `UP` on completed buckets.
2. On the 5m frame a sweep_level formed between 1.18776 and 1.18777.
3. Price was in the `discount` part of the dealing range.
4. The engine waited for a 5m bar whose close came back into that zone.
5. When it did, the hypothetical plan was armed: bullish from 1.18777.
6. The thesis dies at 1.18776 (the far side of the zone) and aims at 1.18805.
7. The zone was read at setup candle None, which had closed before the decision.
8. Everything below is accounting under that reading — no position ever existed.

## 2. Setup-frame context

| # | open (UTC) | close (UTC) | open | high | low | close |
|---|---|---|---|---|---|---|
| 0 | 2021-01-03T22:00:00+00:00 | 2021-01-03T22:05:00+00:00 | 1.22396 | 1.22420 | 1.22296 | 1.22347 |
| 1 | 2021-01-03T22:05:00+00:00 | 2021-01-03T22:10:00+00:00 | 1.22347 | 1.22347 | 1.22298 | 1.22322 |
| 2 | 2021-01-03T22:10:00+00:00 | 2021-01-03T22:15:00+00:00 | 1.22310 | 1.22319 | 1.22309 | 1.22315 |
| 3 | 2021-01-03T22:15:00+00:00 | 2021-01-03T22:20:00+00:00 | 1.22324 | 1.22365 | 1.22324 | 1.22356 |

- dealing range (setup frame): `1.18776` – `1.18805`, equilibrium `1.187905`, position `discount`, ratio `0.034482758620900875` (None)
- swings on the setup frame: None
- sweep high `None` · sweep low `None`
- displacement `None` · structure shift `None`
- order block at the decision: `None`
- bias source: daily `UP`, weekly `UP`, conflict `False`

## 3. Causality table

| item | frame | index | close time | decision time | verdict |
|---|---|---|---|---|---|
| zone candle | 5m | 0 | 2021-01-03T22:05:00+00:00 | 2021-09-03T06:10:00+00:00 | OK |
| dealing range swings | 5m | 5758/5758 | (closed before decision) | 2021-09-03T06:10:00+00:00 | OK |
| bias buckets | daily/weekly from 5m | — | (completed buckets only) | 2021-09-03T06:10:00+00:00 | OK |

## 4. Execution, 5m candle by candle

| bar | time (UTC) | bid O/H/L/C | ask O/H/L/C | touched? | closed inside? | hit stop? | hit T1? | spread |
|---|---|---|---|---|---|---|---|---|
| 50208 | 2021-09-03T06:15:00+00:00 | 1.18780/1.18783/1.18761/1.18766 | 1.18784/1.18786/1.18764/1.18770 | yes | no | YES | no | 0.000040 |

- entry candle: bar 50207 · fill price `1.18777` · convention: **limit at the zone edge, v1 convention** (the bar's own range must contain the entry price).

## 5. Levels

| level | price | distance (pips) | frame |
|---|---|---|---|
| entry | 1.18777 | — | 5m zone edge |
| stop | 1.18776 | 0.10 | 5m far edge |
| T1 | 1.18805 | 2.80 | ? pool |
| T2 (informational) | 1.18807 | 3.00 | ? pool |

- R:R to T1 `28.000`, to T2 `30.000`
- half-spread `0.15` pips; spread as a fraction of the stop `—`; stop as a fraction of the setup candle range `—`

## 6. Outcome

- state `settled_stop` · reason `stop_touched` · exit bar 50207 · exit price `1.18776`
- hypothetical R reported by the engine: **-4.0000**

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
- replay: `stop_touched` at bar 50207, price `1.18776` → R `-4.000000`
- tolerance `1e-09` (floating point only) → **MATCH**

## 8. Checklist

| item | verdict | number |
|---|---|---|
| stop on the correct side of entry | PASS | entry 1.187770 stop 1.187760 |
| T1 beyond entry | PASS | t1 1.18805 |
| entry inside the zone | PASS | zone [1.187760, 1.187770] |
| T1 untaken between its formation and arming | PASS | NOT_EVALUABLE (no pool formation index in the record); proxy: 22 close(s) beyond T1 in the 288 bars before arming |
| fill convention consistent (limit at the zone edge) | PASS | entry 1.187770 vs edge 1.187770 |
| half-spread applied once per side | PASS | half 0.00001500 vs bar spread/2 0.00001500 |
| same-bar rule applied as declared (stop first) | PASS | same-bar settlement: True |
| first evaluation at or after the arming bar | PASS | decision bar 50207 (+0), trigger bar 50207 |
| R:R formula correct | PASS | rr 27.999999999822364 |
| replay reproduces the reported R | PASS | replay stop_touched R=-3.9999999999777955 at bar 50207 vs engine stop_touched R=-3.9999999999777955 at bar 50207 |

## 9. What a human expert would need to judge — NOT JUDGED BY THE AGENT

1. Is this `sweep_level` a valid one on the 5m frame, and would you have used the same two candles to draw it?
2. Is the `discount` reading of the dealing range the one you would take at this time, or is the swing pair wrong?
3. Was a bullish continuation the right expectation after this sweep, given the session window?

## What this does NOT establish

- One card is one plan: it says nothing about the variant's edge, and R is hypothetical under a stated fill assumption.
- The checklist checks arithmetic, sides and conventions; it cannot check whether the reading was right.
