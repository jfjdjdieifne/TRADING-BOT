# DOSSIER P1 — 2021-09_V2-A — plan:2021-09-21T06:10:00+00:00:15m:fvg:bearish:17877

Raw-material dossier. Prepared from saved outputs only; no engine run. Source selection line: `{"run": "2021-09_V2-A", "why": "seeded random", "plan_id": "plan:2021-09-21T06:10:00+00:00:15m:fvg:bearish:17877", "r": 1.4666666666668147, "meta": {"seed": 8195888506664408296, "index": 12, "n": 17}, "state": "settled_target", "file": "CARDS/2021-09_V2-A__seeded__plan_2021-09-21T06_10_00p00_00_15m_fvg_bearish_17877.md"}`

## D1. Identity and outcome
```
plan id          plan:2021-09-21T06:10:00+00:00:15m:fvg:bearish:17877
thesis id        15m:fvg:bearish:17877:bearish
direction        bearish
setup frame      15m   (target frames 15m / 15m)
entry            1.17343  (bearish limit at the zone edge)
stop             1.17373  (far side of fvg, 3.00 pips)
T1               1.17297  (4.60 pips)
T2               1.17296  (informational only)
R:R to T1        1.533
settlement       settled_target / t1_touched at bar 53671 (price 1.17297)
hypothetical R   1.4667
decision time    2021-09-21T06:10:00+00:00   (bar 53663)
trigger bar      53665
```

- arming events of this thesis: **1** (thesis id is unique in `plans_final.jsonl`; the D4 guard forbids re-arming). Confirmed by counting records with the same `thesis_id`.

## D2. Raw data rows (exact source-file rows, 5m)
```
timestamp                BidOpen BidHigh BidLow  BidClose BidVol  AskOpen AskHigh AskLow  AskClose AskVol  SprOpen
2021-09-21T01:10:00Z  1.17277 1.17297 1.17271 1.17282 134.8  1.17280 1.17300 1.17274 1.17285 123.3  0.000030
2021-09-21T01:15:00Z  1.17283 1.17288 1.17264 1.17265 151.0  1.17286 1.17290 1.17266 1.17268 104.3  0.000030
2021-09-21T01:20:00Z  1.17265 1.17267 1.17245 1.17247 106.0  1.17266 1.17268 1.17248 1.17250 49.7  0.000010
2021-09-21T01:25:00Z  1.17250 1.17257 1.17247 1.17251 93.8  1.17252 1.17260 1.17250 1.17254 38.6  0.000020
2021-09-21T01:30:00Z  1.17250 1.17267 1.17236 1.17266 226.5  1.17253 1.17270 1.17239 1.17269 117.2  0.000030
2021-09-21T01:35:00Z  1.17267 1.17277 1.17262 1.17265 144.6  1.17270 1.17280 1.17264 1.17268 267.2  0.000030
2021-09-21T01:40:00Z  1.17265 1.17294 1.17261 1.17290 125.8  1.17267 1.17297 1.17264 1.17292 304.5  0.000020
2021-09-21T01:45:00Z  1.17289 1.17323 1.17286 1.17323 153.9  1.17292 1.17326 1.17289 1.17326 214.9  0.000030
2021-09-21T01:50:00Z  1.17324 1.17348 1.17315 1.17348 270.3  1.17327 1.17351 1.17317 1.17350 150.0  0.000030
2021-09-21T01:55:00Z  1.17347 1.17394 1.17345 1.17388 264.6  1.17350 1.17396 1.17348 1.17391 207.8  0.000030
2021-09-21T02:00:00Z  1.17388 1.17395 1.17383 1.17394 108.9  1.17390 1.17398 1.17386 1.17397 118.0  0.000020
2021-09-21T02:05:00Z  1.17395 1.17399 1.17380 1.17385 131.0  1.17398 1.17403 1.17383 1.17388 166.9  0.000030
2021-09-21T02:10:00Z  1.17383 1.17389 1.17373 1.17373 80.6  1.17385 1.17392 1.17375 1.17376 80.5  0.000020
2021-09-21T02:15:00Z  1.17373 1.17373 1.17346 1.17346 153.3  1.17374 1.17375 1.17348 1.17350 85.0  0.000010
2021-09-21T02:20:00Z  1.17345 1.17352 1.17342 1.17349 94.7  1.17348 1.17355 1.17344 1.17352 64.7  0.000030
2021-09-21T02:25:00Z  1.17348 1.17350 1.17337 1.17343 149.8  1.17351 1.17352 1.17340 1.17345 71.3  0.000030
2021-09-21T02:30:00Z  1.17341 1.17343 1.17328 1.17328 157.1  1.17342 1.17346 1.17330 1.17330 66.1  0.000010
2021-09-21T02:35:00Z  1.17328 1.17335 1.17326 1.17326 148.0  1.17331 1.17337 1.17329 1.17329 106.9  0.000030
2021-09-21T02:40:00Z  1.17327 1.17327 1.17321 1.17322 49.5  1.17329 1.17329 1.17324 1.17325 26.8  0.000020
2021-09-21T02:45:00Z  1.17322 1.17334 1.17322 1.17333 41.5  1.17324 1.17336 1.17324 1.17336 28.7  0.000020
2021-09-21T02:50:00Z  1.17333 1.17333 1.17326 1.17326 64.7  1.17335 1.17335 1.17329 1.17329 29.5  0.000020
2021-09-21T02:55:00Z  1.17327 1.17328 1.17322 1.17323 46.6  1.17330 1.17331 1.17325 1.17327 49.0  0.000030
2021-09-21T03:00:00Z  1.17323 1.17323 1.17300 1.17300 76.7  1.17326 1.17326 1.17303 1.17303 74.7  0.000030
2021-09-21T03:05:00Z  1.17300 1.17317 1.17300 1.17315 48.1  1.17304 1.17321 1.17304 1.17316 37.5  0.000040
2021-09-21T03:10:00Z  1.17313 1.17319 1.17312 1.17315 45.6  1.17317 1.17322 1.17315 1.17318 58.1  0.000040
2021-09-21T03:15:00Z  1.17314 1.17314 1.17296 1.17302 125.4  1.17316 1.17318 1.17299 1.17306 76.9  0.000020
2021-09-21T03:20:00Z  1.17303 1.17309 1.17296 1.17303 151.2  1.17306 1.17312 1.17299 1.17307 101.8  0.000030
2021-09-21T03:25:00Z  1.17303 1.17309 1.17303 1.17304 92.1  1.17306 1.17312 1.17306 1.17306 69.1  0.000030
2021-09-21T03:30:00Z  1.17304 1.17311 1.17298 1.17298 114.1  1.17307 1.17315 1.17301 1.17301 68.7  0.000030
2021-09-21T03:35:00Z  1.17297 1.17317 1.17297 1.17312 144.0  1.17301 1.17320 1.17300 1.17316 73.6  0.000040
2021-09-21T03:40:00Z  1.17312 1.17319 1.17307 1.17318 101.4  1.17315 1.17323 1.17311 1.17322 47.8  0.000030
2021-09-21T03:45:00Z  1.17317 1.17324 1.17317 1.17317 100.7  1.17321 1.17328 1.17320 1.17321 57.5  0.000040
2021-09-21T03:50:00Z  1.17318 1.17322 1.17317 1.17322 35.2  1.17321 1.17326 1.17319 1.17326 17.0  0.000030
2021-09-21T03:55:00Z  1.17321 1.17325 1.17315 1.17319 84.8  1.17322 1.17327 1.17319 1.17322 57.3  0.000010
2021-09-21T04:00:00Z  1.17320 1.17334 1.17319 1.17334 76.5  1.17322 1.17338 1.17321 1.17338 98.9  0.000020
2021-09-21T04:05:00Z  1.17334 1.17340 1.17333 1.17340 28.3  1.17337 1.17342 1.17336 1.17342 44.6  0.000030
2021-09-21T04:10:00Z  1.17340 1.17349 1.17334 1.17345 86.4  1.17343 1.17352 1.17338 1.17348 146.7  0.000030
2021-09-21T04:15:00Z  1.17344 1.17345 1.17336 1.17337 154.8  1.17348 1.17348 1.17338 1.17341 94.4  0.000040
2021-09-21T04:20:00Z  1.17336 1.17342 1.17327 1.17327 58.3  1.17340 1.17345 1.17330 1.17330 42.0  0.000040
2021-09-21T04:25:00Z  1.17326 1.17326 1.17317 1.17317 36.1  1.17329 1.17329 1.17319 1.17320 58.6  0.000030
2021-09-21T04:30:00Z  1.17318 1.17320 1.17312 1.17314 39.9  1.17320 1.17323 1.17314 1.17317 69.6  0.000020
2021-09-21T04:35:00Z  1.17314 1.17317 1.17306 1.17309 61.8  1.17316 1.17320 1.17309 1.17312 91.0  0.000020
2021-09-21T04:40:00Z  1.17309 1.17309 1.17297 1.17309 60.3  1.17311 1.17312 1.17300 1.17312 59.0  0.000020
2021-09-21T04:45:00Z  1.17307 1.17315 1.17303 1.17309 59.3  1.17311 1.17317 1.17306 1.17310 18.9  0.000040
2021-09-21T04:50:00Z  1.17308 1.17313 1.17308 1.17311 53.3  1.17312 1.17317 1.17310 1.17315 55.6  0.000040
2021-09-21T04:55:00Z  1.17312 1.17319 1.17312 1.17317 50.5  1.17315 1.17323 1.17314 1.17320 76.5  0.000030
2021-09-21T05:00:00Z  1.17317 1.17324 1.17313 1.17323 89.1  1.17321 1.17328 1.17316 1.17325 87.7  0.000040
2021-09-21T05:05:00Z  1.17323 1.17335 1.17323 1.17330 67.7  1.17326 1.17338 1.17326 1.17332 109.8  0.000030
2021-09-21T05:10:00Z  1.17331 1.17335 1.17325 1.17328 48.7  1.17333 1.17338 1.17328 1.17332 65.3  0.000020
2021-09-21T05:15:00Z  1.17329 1.17335 1.17323 1.17335 75.7  1.17332 1.17338 1.17326 1.17337 106.5  0.000030
2021-09-21T05:20:00Z  1.17335 1.17344 1.17334 1.17339 103.0  1.17338 1.17348 1.17337 1.17343 111.8  0.000030
2021-09-21T05:25:00Z  1.17340 1.17359 1.17339 1.17355 125.0  1.17343 1.17362 1.17342 1.17358 173.8  0.000030
2021-09-21T05:30:00Z  1.17354 1.17356 1.17343 1.17344 86.9  1.17358 1.17359 1.17346 1.17347 102.8  0.000040
2021-09-21T05:35:00Z  1.17344 1.17348 1.17333 1.17337 134.1  1.17348 1.17351 1.17336 1.17341 66.1  0.000040
2021-09-21T05:40:00Z  1.17338 1.17348 1.17330 1.17344 211.7  1.17341 1.17352 1.17333 1.17347 110.3  0.000030
2021-09-21T05:45:00Z  1.17348 1.17353 1.17339 1.17350 156.6  1.17350 1.17356 1.17342 1.17354 160.3  0.000020
2021-09-21T05:50:00Z  1.17350 1.17355 1.17334 1.17336 123.1  1.17353 1.17358 1.17337 1.17339 135.3  0.000030
2021-09-21T05:55:00Z  1.17338 1.17350 1.17334 1.17334 103.6  1.17339 1.17353 1.17337 1.17337 109.5  0.000010
2021-09-21T06:00:00Z  1.17335 1.17340 1.17306 1.17309 266.8  1.17337 1.17342 1.17309 1.17312 219.0  0.000020
2021-09-21T06:05:00Z  1.17308 1.17330 1.17299 1.17329 158.1  1.17311 1.17333 1.17302 1.17332 148.1  0.000030
2021-09-21T06:10:00Z  1.17330 1.17361 1.17329 1.17359 165.4  1.17332 1.17364 1.17332 1.17362 228.7  0.000020
2021-09-21T06:15:00Z  1.17360 1.17374 1.17350 1.17362 135.9  1.17362 1.17377 1.17353 1.17365 142.9  0.000020
2021-09-21T06:20:00Z  1.17360 1.17364 1.17342 1.17361 543.1  1.17363 1.17366 1.17344 1.17363 234.2  0.000030
2021-09-21T06:25:00Z  1.17361 1.17368 1.17347 1.17362 373.3  1.17365 1.17372 1.17350 1.17366 392.4  0.000040
2021-09-21T06:30:00Z  1.17360 1.17372 1.17352 1.17356 373.7  1.17364 1.17376 1.17355 1.17360 361.6  0.000040
2021-09-21T06:35:00Z  1.17356 1.17368 1.17338 1.17343 329.7  1.17361 1.17373 1.17342 1.17345 189.8  0.000050
2021-09-21T06:40:00Z  1.17345 1.17346 1.17318 1.17326 317.7  1.17347 1.17350 1.17321 1.17330 251.3  0.000020
2021-09-21T06:45:00Z  1.17329 1.17342 1.17312 1.17313 510.4  1.17331 1.17345 1.17314 1.17316 392.5  0.000020
2021-09-21T06:50:00Z  1.17314 1.17320 1.17294 1.17308 151.0  1.17316 1.17323 1.17296 1.17311 194.6  0.000020
```
- 69 rows shown: 60 5m candles of context before the decision bar, then every 5m candle to settlement. Data file sha256 `38be0503fd56269686a6f3d25f5e537e2ac5682ea9a5d79af1765acd224a6ab4`.

## D3. Aggregation provenance
- setup frame `15m` = 15 minutes; built from 5m **bid** candles. open = first 5m open, high = max of 5m highs, low = min of 5m lows, close = last 5m close; volume summed; spread fields taken from the last 5m bar (declared in DECLARED_CHOICES_V2 row B).
- bid is used because the entry, stop and targets are all bid prices in this build; the ask is carried through the data rows only for the spread.
```
setup candle #17875  open 2021-09-21T02:00:00+00:00  close 2021-09-21T02:15:00+00:00  O 1.17388  H 1.17399  L 1.17373  C 1.17373
  built from 3 5m bars: 2021-09-21T02:00:00+00:00 .. 2021-09-21T02:10:00+00:00
  high = max(1.17395, 1.17399, 1.17389) = 1.17399
  low  = min(1.17383, 1.17380, 1.17373) = 1.17373
  open = 1.17388 (first 5m open), close = 1.17373 (last 5m close)
setup candle #17876  open 2021-09-21T02:15:00+00:00  close 2021-09-21T02:30:00+00:00  O 1.17373  H 1.17373  L 1.17337  C 1.17343
  built from 3 5m bars: 2021-09-21T02:15:00+00:00 .. 2021-09-21T02:25:00+00:00
  high = max(1.17373, 1.17352, 1.17350) = 1.17373
  low  = min(1.17346, 1.17342, 1.17337) = 1.17337
  open = 1.17373 (first 5m open), close = 1.17343 (last 5m close)
setup candle #17877  open 2021-09-21T02:30:00+00:00  close 2021-09-21T02:45:00+00:00  O 1.17341  H 1.17343  L 1.17321  C 1.17322
  built from 3 5m bars: 2021-09-21T02:30:00+00:00 .. 2021-09-21T02:40:00+00:00
  high = max(1.17343, 1.17335, 1.17327) = 1.17343
  low  = min(1.17328, 1.17326, 1.17321) = 1.17321
  open = 1.17341 (first 5m open), close = 1.17322 (last 5m close)
setup candle #17878  open 2021-09-21T02:45:00+00:00  close 2021-09-21T03:00:00+00:00  O 1.17322  H 1.17334  L 1.17322  C 1.17323
  built from 3 5m bars: 2021-09-21T02:45:00+00:00 .. 2021-09-21T02:55:00+00:00
  high = max(1.17334, 1.17333, 1.17328) = 1.17334
  low  = min(1.17322, 1.17326, 1.17322) = 1.17322
  open = 1.17322 (first 5m open), close = 1.17323 (last 5m close)
```

## D4. Higher-frame context used for the bias
```
daily  2021-09-19  O 1.17288 H 1.17305 L 1.17232 C 1.17292  completed/available at 2021-09-20T00:00:00+00:00
daily  2021-09-20  O 1.17293 H 1.17364 L 1.17001 C 1.17266  completed/available at 2021-09-21T00:00:00+00:00
weekly 2021-W37  O 1.18114 H 1.18458 L 1.17232 C 1.17292  completed/available at 2021-09-20T00:00:00+00:00
```
- bias as recorded at the decision: daily `DOWN`, weekly `DOWN`, resolved `DOWN`, conflict `False`.
- rule: `stream_v1.HtfState.bias` returns `UP` when the completed bucket's close is above its open, `DOWN` below, `FLAT` when equal. The recorded source string in every decision row is `ict_engine.htf aggregation, completion-labelled`. Direction for the plan = the **daily** value (DECLARED_CHOICES row 9), weekly recorded as context.

## D5. Dealing range
```
range low  1.17297  (swing candle #1918)
range high 1.17359  (swing candle #1918)
midpoint   1.17328
entry position ratio 0.5968  label `premium`  state `INSIDE_RANGE`
```
- the swing indices printed above are **window-local positions** in the rolling buffer at read time (`stream_v1.swing_now` stores `candle_indices['c2']` from the window, not an absolute candle index). Their timestamps and right-side confirmation candles are therefore **NOT_RECOVERABLE_WITHOUT_RERUN** — recorded as defect D11. What is certain from the record is that both swings were confirmed before the decision, because the range existed at the decision bar and the buffer holds only closed candles.

## D6. Liquidity and sweep
```
level    side   kind                        frame  formed_bar  age_bars  state
1.17359  high   relative_equal_pair         15m          1919     15971  untaken
1.17399  high   relative_equal_pair         15m          1919     15971  untaken
1.17297  low    relative_equal_pair         15m          1919     15971  untaken
1.17296  low    relative_equal_pair         15m          1919     15971  untaken
1.17236  low    relative_equal_pair         15m          1919     15971  untaken
1.17232  low    relative_equal_pair         15m          1919     15971  untaken
1.17231  low    relative_equal_pair         15m          1919     15971  untaken
1.17221  low    relative_equal_pair         15m          1919     15971  untaken
1.17219  low    relative_equal_pair         15m          1919     15971  untaken
1.17126  low    relative_equal_pair         15m          1919     15971  untaken
1.17113  low    relative_equal_pair         15m          1919     15971  untaken
```
- sweep reference at the decision: high `{'answer': 'NO', 'level': 1.17359}` · low `{'answer': 'NO', 'level': 1.17297}`. The zone's own formation index is `17877`; for a `sweep_level` zone the sweep candle is that index, otherwise the sweep did not define this zone.
- ranked target pools at the decision: `[{'level': 1.17297, 'kind': 'relative_equal_pair', 'frame': '15m', 'distance_ratio': 1.0}, {'level': 1.17296, 'kind': 'relative_equal_pair', 'frame': '15m', 'distance_ratio': 1.0161290322581742}, {'level': 1.17296, 'kind': 'relative_equal_pair', 'frame': '1h', 'distance_ratio': 1.0161290322581742}, {'level': 1.17236, 'kind': 'relative_equal_pair', 'frame': '15m', 'distance_ratio': 1.983870967742184}]`
- why T1 and not the pools between: T1 is the first entry of `rank_draws` among the pools on the trade's side that lie beyond the entry price; T2 is the second. Pools behind the entry are excluded by `plan_v1.targets_ahead` (`ahead = level > entry` for bullish). The formation index of each target pool is **NOT_RECOVERABLE_WITHOUT_RERUN** (defect D5) — the plan record stores only the level, kind and frame.

## D7. Displacement and structure
```
displacement   {'answer': 'YES', 'ratio': 0.6666666666666666}
sweep high     {'answer': 'NO', 'level': 1.17359}
sweep low      {'answer': 'NO', 'level': 1.17297}
structure      None
order block    None
```
- displacement variant is `V-D-01`: body/range above 60 (`SOURCE_NUMBER`, claim F1), equality → UNDECIDED, read over `candles[:t+1]`. The ratio printed above is the value the module returned.

## D8. Zone and candidate list
```
zone id     15m:fvg:bearish:17877
kind        fvg   direction bearish
lower/upper 1.17343 / 1.17373
formed at   setup candle #17877
existed from 2021-09-21T02:45:00+00:00 (that candle's close); decision 2021-09-21T06:10:00+00:00 → OK
```
- forming candle #17875: 2021-09-21T02:00:00+00:00 O 1.17388 H 1.17399 L 1.17373 C 1.17373
- forming candle #17876: 2021-09-21T02:15:00+00:00 O 1.17373 H 1.17373 L 1.17337 C 1.17343
- forming candle #17877: 2021-09-21T02:30:00+00:00 O 1.17341 H 1.17343 L 1.17321 C 1.17322

Candidates considered at the arming moment, in the order the engine ranked them:
```
15m:fvg:bearish:17877              fvg         [1.17343, 1.17373]  fresh=False  bias_agrees=True  distance_ratio=0.0161
```
- criteria in the order applied: `{"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.016129032257457994}}`
- criteria conflict logged: **False** (a conflict ⇒ no plan, so a plan implies no conflict)
- why this zone won: first by bias agreement, then freshness, then the smallest context-relative distance (`rank_zones` in `build_v1/plan_v1.py`).

## D9. Decision trace
Decision rows at the setup-frame closes between the zone formation and the arming:
```
time                      decision      reason
2021-09-21T02:15:00+00:00  setup candle #17875 closed
2021-09-21T02:30:00+00:00  setup candle #17876 closed
2021-09-21T02:45:00+00:00  setup candle #17877 closed
2021-09-21T06:10:00+00:00  ARMED         V2-A / V2-A
```
- the per-candle sub-decisions (every gate answer between those closes) are written to `decisions.jsonl` at the **5m decision cadence**, not at setup-frame closes; the saved run writes one row per 5m bar. The set of gate answers at the exact setup closes is **NOT_RECOVERABLE_WITHOUT_RERUN** only for bars outside the decision window; inside it every 5m row is saved and the rows at the closing 5m bars carry the question and answer.
- 5m touch: first touching bar **53665** (2021-09-21T06:20:00+00:00); fill convention = limit at the zone edge (v1 convention), fill price 1.17343.

## D10. Levels and costs
```
stop            1.17373   rule: `far side of fvg` (DECLARED_CHOICES_V2 row D: the far edge of the setup-frame zone; sweep zones use the sweep wick; no pip minimum, no filter)
stop distance   3.00 pips = 1.4286 of the setup candle's range
half-spread     0.10 pips = 0.0667 of the stop
T1 distance     4.60 pips
T2 distance     4.70 pips
R:R T1 / T2     1.533 / 1.567
```

## D11. Candle-by-candle execution
```
bar    time                   bid O/H/L/C                 ask O/H/L/C                 touch  in-zone  stop  T1   spread
53664  2021-09-21T06:15:00+00:00  1.17360/1.17374/1.17350/1.17362  1.17362/1.17377/1.17353/1.17365  no     yes      YES   no   0.000020
53665  2021-09-21T06:20:00+00:00  1.17360/1.17364/1.17342/1.17361  1.17363/1.17366/1.17344/1.17363  yes    yes      no    no   0.000030
53666  2021-09-21T06:25:00+00:00  1.17361/1.17368/1.17347/1.17362  1.17365/1.17372/1.17350/1.17366  no     yes      no    no   0.000040
53667  2021-09-21T06:30:00+00:00  1.17360/1.17372/1.17352/1.17356  1.17364/1.17376/1.17355/1.17360  no     yes      no    no   0.000040
53668  2021-09-21T06:35:00+00:00  1.17356/1.17368/1.17338/1.17343  1.17361/1.17373/1.17342/1.17345  yes    yes      no    no   0.000050
53669  2021-09-21T06:40:00+00:00  1.17345/1.17346/1.17318/1.17326  1.17347/1.17350/1.17321/1.17330  yes    no       no    no   0.000020
53670  2021-09-21T06:45:00+00:00  1.17329/1.17342/1.17312/1.17313  1.17331/1.17345/1.17314/1.17316  no     no       no    no   0.000020
53671  2021-09-21T06:50:00+00:00  1.17314/1.17320/1.17294/1.17308  1.17316/1.17323/1.17296/1.17311  no     no       no    YES  0.000020
53672  2021-09-21T06:55:00+00:00  1.17308/1.17327/1.17295/1.17312  1.17310/1.17330/1.17298/1.17315  no     no       no    YES  0.000020
```
```
independent replay (this file does not import settlement code):
  for each 5m bar from decision+1, up to 288 bars:
    if not triggered: skip unless low <= entry <= high; if 288 bars pass -> expired, R = 0
    if stop reached (bullish low <= stop / bearish high >= stop) -> settle at stop
    elif T1 reached (bullish high >= T1 / bearish low <= T1) -> settle at T1
    cost = half_spread_at_decision + spread_of_exit_bar/2 ; R = (gross - cost)/|entry-stop|
  result: t1_touched at bar 53671 price 1.17297 -> R 1.466667
  engine: t1_touched at bar 53671 price 1.17297 -> R 1.466667
  verdict: MATCH (tolerance 1e-9, floating point only)
```

## D12. What the engine did not look at (checked in the code path)
```
item                          used?  evidence
weekly/monthly FVG or OB      no     build_v2/wrapper_v2.py gathers zones only from the setup
                                     frame's gaps/blocks/sweep (gather_zones call, line ~330)
session context beyond flag   partial gates() reads only ctx['session']['in_window']
                                     (build_v1/plan_v1.py gates, first condition)
volume                        no     no volume field is read after loading; grep 'bid_volume'
                                     in build_v2 = only the Bar constructor
previous-day high/low         no     HtfState produces daily open/high/low/close; only the
                                     bias (close vs open) is consumed
equal highs/lows as pools     partial LiquidityState.push_swings forms relative_equal_pair
                                     without an equality cutoff (KNOWLEDGE_GAP)
news / calendar               no     no such source exists in the repository path
other instruments             no     one data file, one symbol
```

## D13. Defects observed and questions for an expert
```
D5  T1/T2 pool formation index not saved        -> that check is NOT_RECOVERABLE_WITHOUT_RERUN
D6  v1 evaluates on the decision bar, v2 on the next bar (does not affect this plan: variant
    V2-*)
D9  cards show setup candle 0 when formed_index is None (sweep zones only)
D10 NOT_EVALUABLE rendered as PASS in the card checklist
D11 swing level_index/confirm_index are window-local -> swing timestamps not recoverable from
    the record without a re-run
```
Questions for an ICT expert — NOT JUDGED BY THE AGENT:
1. Is this fvg on the 15m frame a valid zone, and are these the candles you would use?
2. Was the bearish expectation right for this session window and this dealing-range position (`premium`)?
3. Would you place the stop at the far edge of the zone (1.17373) or inside it at the mean threshold, as the source's sentence suggests?

## D14. What this does NOT establish

- It does not establish that the reading is correct ICT: nothing here is judged, only reported.
- It does not establish the plan's merit: R is hypothetical under one stated fill convention.
- The dossier is assembled from saved records plus recomputed aggregation; anything the records do not carry is marked NOT_RECOVERABLE_WITHOUT_RERUN rather than reconstructed.
