# Understanding card — inversion fair value gap (`inversion_fair_value_gap`)

Windows extracted and read in full (`±100` words) this session: **15** (target 15) across **15** distinct transcripts (`E1_EARLY_SERIES`: 2, `E5_2023_2024`: 13). Meets the 15-window budget.
Claims: U3K3-060, U3K3-061, U3K3-062, U3K3-063, U3K3-064, U3K3-065, U3K3-066, U3K3-067, U3K3-068, U3K3-069, U3K3-070, U3K3-071

Every quoted line below is verbatim (≤25 words) from a `±100`-word window logged and read in full this session. Per Rule 2, `statement` in `claims.jsonl` carries the verbatim quote, `reading` carries the interpretation below, and `added_words` lists every word in `reading` absent from the window. Section (c) is explicitly an `ENGINEERING_HYPOTHESIS`, not his words. Empty sections read `NOT_IN_SOURCES`.

## (a) PURPOSE
- When a fair value gap fails in its initial bullish or bearish function, it is repurposed as an inversion fair value gap upon return.
  > "a fair value Gap that fails in its function of bullishness or bearishness if it fails it will become an inversion fair value Gap"
  `[U3K3-060]` · `ICT-Mentorship-2023-October-15-2023-Market-Review-002.json` (E5_2023_2024) · window `W0079` · `added_words: [bearish, bullish, initial, repurposed, return, upon]` · note: definition and purpose of inversion fair value gap

## (b) RECOGNITION (his criteria and his rejections)
- He recognizes an inversion fair value gap being respected by watching the candle bodies stay on one side of the inverted gap.
  > "look at the bodies of the candles here respecting the inversion fair value Gap"
  `[U3K3-061]` · `NQ-Live-Execution-&-Commentary-Final-Trading-Day-Of-2023-001.json` (E1_EARLY_SERIES) · window `W0078` · `added_words: [candle, inverted, recognizes, respected, side, stay, watching]` · note: body respect criterion
- When treating an old fair value gap as a bearish inversion fair value gap, he rejects setups where price trades to its high end.
  > "we don't want to see the high end of a old fair value Gap if it's being treated as an inversion fair value Gap"
  `[U3K3-062]` · `Thursday-June-15-2023-ICT-Price-Action-Workshop-002.json` (E5_2023_2024) · window `W0077` · `added_words: [bearish, rejects, trades, treating]` · note: REJECTION of trading to the far extreme of a bearish IFVG
- He contrasts an inversion fair value gap with retail broken-resistance-turned-support, which he rejects as flawed logic.
  > "here is classic support and resistance where resistance is broken now turn support um that is a unfortunate flawed logic"
  `[U3K3-063]` · `NQ-Employment-Number-Live-Execution-December-07-2023-001.json` (E1_EARLY_SERIES) · window `W0076` · `added_words: [contrasts, rejects, turned]` · note: REJECTION of retail support-turned-resistance textbook framing

## (c) OBSERVABLES — ENGINEERING_HYPOTHESIS (needs owner approval)
- a prior fair value gap whose directional support/resistance failed when price traded through it, subsequently acting as opposing support/resistance when price returns to its bounds, evaluated by whether candle bodies respect the zone
  `candle_observable: true` · derived from `U3K3-061`, `U3K3-060`, `U3K3-064` · **ENGINEERING_HYPOTHESIS — needs owner approval**
- competing penetration rules — strict midpoint/consequent encroachment respect rejecting the far edge (W0077) vs permissible full traversal ('mohawk') when only a single pass crossed the gap (W0090) — must be kept as parallel variants
  `candle_observable: true` · derived from `U3K3-062`, `U3K3-071` · **ENGINEERING_HYPOTHESIS — needs owner approval**

## (d) HOW HE TREATS IT
- If stopped out trying to buy a fair value gap that fails, he waits for price to return up into it and shorts the inversion fair value gap.
  > "all I got to do is sit back and wait when it comes back up and hits it I'll treat it as a shorting opportunity"
  `[U3K3-064]` · `ICT-Mentorship-2023-October-15-2023-Market-Review-002.json` (E5_2023_2024) · window `W0079` · `added_words: [buy, price, return, shorts, trying, waits]` · note: recovery/reversal execution treatment
- He warns against trailing a stop loss tightly underneath a newly formed inversion fair value gap when wicks already show retracement risk.
  > "just because they created another inversion fair value Gap don't run your stop loss up underneath that keep it in here"
  `[U3K3-065]` · `ICT-Mentorship-2023-August-18-2023-Live-trade-Walkthrough-001.json` (E5_2023_2024) · window `W0088` · `added_words: [against, formed, newly, retracement, risk, show, tightly, trailing, warns, wicks]` · note: stop-management rule on subsequent IFVGs

## (e) COMPARING INSTANCES
- When price is unwilling to retrace up into a 4-hour inversion fair value gap, he favors the larger 4-hour liquidity pool below as the stronger draw.
  > "that to me is a better draw than this will be and it's going to be in my opinion in a hurry to get down"
  `[U3K3-066]` · `ICT-Mentorship-2023-October-22-2023-Market-Review-001.json` (E5_2023_2024) · window `W0089` · `added_words: [favors, hour, pool, price, retrace, stronger]` · note: comparative: 4h liquidity draw below vs waiting for 4h IFVG retracement

## (f) INTERACTIONS
- Recognizing an inversion fair value gap alongside breakers and mitigation blocks is required to spot a market maker buy or sell model in real time.
  > "if you don't know what a inversion fair value Gap is the observation of seeing it real time as a market maker buy or sell"
  `[U3K3-067]` · `ICT-Mentorship-2023-Market-Maker-Models-001.json` (E5_2023_2024) · window `W0081` · `added_words: [alongside, blocks, breakers, recognizing, required, spot]` · note: interaction with market maker models, breakers, and mitigation blocks
- Confluence of a 5-minute breaker and an inversion fair value gap during the London session forms a bearish Silver Bullet entry.
  > "the market leaves that five minute breaker and it bumps into the inversion fair value Gap and the five minute breaker right on that candle"
  `[U3K3-068]` · `ICT-Mentorship-2023-September-12-2023-NQ-Algorithmic-Price-Delivery-001.json` (E5_2023_2024) · window `W0084` · `added_words: [confluence, entry, forms]` · note: interaction with 5m breaker and London Silver Bullet

## (g) TIMEFRAME
- He tracks inversion fair value gaps across timeframes from 30-second and 3-minute charts (W0084, W0085) up to the weekly chart.
  > "we have a small little Fairway Gap there and we trade it back down into the old weekly inversion fair value Gap"
  `[U3K3-069]` · `ICT-Mentorship-2023-Advanced-Gap-Theory-Introduction-001.json` (E5_2023_2024) · window `W0087` · `added_words: [charts, gaps, minute, second, timeframes, tracks, w0084, w0085]` · note: weekly timeframe application; [sic-asr] 'Fairway Gap'

## (h) FAILURE / INVALIDATION and DISCRETION
- An expected inversion fair value gap setup can fail to materialize when heavy price action runs directly to lower liquidity without retracing.
  > "we failed to get into that 4our old buyid bound sell efficiency that I wanted to see act as an inversion fair value Gap"
  `[U3K3-070]` · `ICT-Mentorship-2023-October-22-2023-Market-Review-001.json` (E5_2023_2024) · window `W0089` · `added_words: [action, directly, expected, fail, heavy, lower, materialize, price, retracing, runs, setup]` · note: unreached IFVG retracement; [sic-asr] '4our old buyid bound'

## (i) VARIANTS (kept parallel, never merged)
- In contrast to W0077 (rejecting the high end), when only a single pass went through the gap he allows price to trade all the way through its high.
  > "in this instance we can allow for it to completely trade back to through and have a mohawk and that's completely permissible"
  `[U3K3-071]` · `ICT-Mentorship-2023-October-15-2023-Market-Review-003.json` (E5_2023_2024) · window `W0090` · `added_words: [allows, contrast, end, price, rejecting, w0077]` · note: parallel variant kept separate from W0077: single-pass IFVG permits a 'mohawk' through the far side

## Windows Logged and Read This Session (`±100` words each)
| Window | Era | Match | Transcript | Word Range | SHA-256 (prefix) |
|---|---|---|---|---|---|
| `W0076` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `NQ-Employment-Number-Live-Execution-December-07-2023-001.json` | `299..500` (201w) | `87d9b3424537` |
| `W0077` | `E5_2023_2024` | `exact_kept_tsv` | `Thursday-June-15-2023-ICT-Price-Action-Workshop-002.json` | `4816..5017` (201w) | `6bc9db6bf768` |
| `W0078` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `NQ-Live-Execution-&-Commentary-Final-Trading-Day-Of-2023-001.json` | `7395..7596` (201w) | `0e24f7f16b11` |
| `W0079` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-Mentorship-2023-October-15-2023-Market-Review-002.json` | `584..785` (201w) | `4b55c453e58d` |
| `W0080` | `E5_2023_2024` | `exact_kept_tsv` | `Tuesday-June-06-2023-Market-Review-&-Price-Action-Lecture-001.json` | `3895..4096` (201w) | `7462fb51b897` |
| `W0081` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-Mentorship-2023-Market-Maker-Models-001.json` | `49..250` (201w) | `643d9f19046c` |
| `W0082` | `E5_2023_2024` | `exact_kept_tsv` | `April-13-2023-Live-Tape-Reading-Emini-S&P-AM-Session-001.json` | `3503..3704` (201w) | `44b06797cb01` |
| `W0083` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-Mentorship-2023-September-08-2023-Review-&-ICT-Ma-Deuce-Model-001.json` | `3257..3458` (201w) | `2d613ad125b1` |
| `W0084` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-Mentorship-2023-September-12-2023-NQ-Algorithmic-Price-Delivery-001.json` | `7629..7830` (201w) | `27a2a4eda981` |
| `W0085` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-Mentorship-2023-Algorithmic-Price-Delivery-&-Time-Macros-Intro-001.json` | `1802..2003` (201w) | `65a789a111c1` |
| `W0086` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-Mentorship-2023-Advanced-Theory-On-ICT-Breaker-001.json` | `2656..2857` (201w) | `f0732e5e652b` |
| `W0087` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-Mentorship-2023-Advanced-Gap-Theory-Introduction-001.json` | `112..313` (201w) | `15f2a89d7934` |
| `W0088` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-Mentorship-2023-August-18-2023-Live-trade-Walkthrough-001.json` | `3009..3210` (201w) | `430e7bc296e1` |
| `W0089` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-Mentorship-2023-October-22-2023-Market-Review-001.json` | `4709..4910` (201w) | `e945de501336` |
| `W0090` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-Mentorship-2023-October-15-2023-Market-Review-003.json` | `2350..2551` (201w) | `aa41b76f364c` |
