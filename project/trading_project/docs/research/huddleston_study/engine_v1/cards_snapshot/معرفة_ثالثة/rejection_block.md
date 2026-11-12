# Understanding card — rejection block (`rejection_block`)

Windows extracted and read in full (`±100` words) this session: **15** (target 15) across **15** distinct transcripts (`E2_2016`: 1, `E3_2017`: 5, `E4_2019_2022`: 5, `E5_2023_2024`: 4). Meets the 15-window budget.
Claims: U3K3-198, U3K3-199, U3K3-200, U3K3-201, U3K3-202, U3K3-203, U3K3-204, U3K3-205, U3K3-206, U3K3-207, U3K3-208

Every quoted line below is verbatim (≤25 words) from a `±100`-word window logged and read in full this session. Per Rule 2, `statement` in `claims.jsonl` carries the verbatim quote, `reading` carries the interpretation below, and `added_words` lists every word in `reading` absent from the window. Section (c) is explicitly an `ENGINEERING_HYPOTHESIS`, not his words. Empty sections read `NOT_IN_SOURCES`.

## (a) PURPOSE
- A rejection block captures liquidity hidden inside long candle wicks (above the highest body close or below the lowest body close) before price reverses.
  > "price reaches up above the body of the candle or candles to run the buy side liquidity out before the price declines"
  `[U3K3-198]` · `ICT-Mentorship-Core-Content-Month-04-ICT-Rejection-Block-001.json` (E2_2016) · window `W0256` · `added_words: [captures, close, hidden, highest, inside, lowest, reverses]` · note: purpose of the rejection block in distribution and accumulation

## (b) RECOGNITION (his criteria and his rejections)
- He recognizes a bearish rejection block at a swing high formed with one or more long upper wicks where classic chartists mistakenly see a continuation flag.
  > "the bearish rejection block is when a price high has formed with long wicks on the high or highs"
  `[U3K3-199]` · `ICT-Mentorship-Core-Content-Month-04-ICT-Rejection-Block-001.json` (E2_2016) · window `W0256` · `added_words: [chartists, mistakenly, recognizes, swing, upper]` · note: recognition of bearish rejection block vs classic bull flag
- For a bullish rejection block at a swing low, the reference threshold is the lowest body close/open before the wick low; price only needs to sweep below that body level, not the wick extreme.
  > "it's trading below the rejection block which is the lowest closing price in this swing I don't need that low to be taken out"
  `[U3K3-200]` · `ICT-Mentorship-2023-One-Trading-Setup-For-Life-002.json` (E5_2023_2024) · window `W0262` · `added_words: [body, bullish, close, extreme, level, needs, open, reference, sweep, threshold, wick]` · note: recognition of bullish rejection block threshold at the lowest closing price
- He rejects trying to pick tops in bull runs simply because price sweeps a rejection block high without confirmation inside a bearish breaker/FVG.
  > "I do not try to pick tops in bull runs I don't do it I don't and if you try to do that"
  `[U3K3-201]` · `March-30-2023-Live-Tape-Reading-AM-Session-002.json` (E5_2023_2024) · window `W0259` · `added_words: [bearish, breaker, confirmation, fvg, inside, rejects, simply, sweeps]` · note: REJECTION of counter-trend top-picking on an unconfirmed sweep

## (c) OBSERVABLES — ENGINEERING_HYPOTHESIS (needs owner approval)
- at a swing high (bearish rejection block): the zone between the highest candle-body close/open and the upper wick extreme; at a swing low (bullish rejection block): the zone between the lowest candle-body close/open and the lower wick extreme, including the 50% midpoint of the wick/tail
  `candle_observable: true` · derived from `U3K3-198`, `U3K3-199`, `U3K3-206`, `U3K3-200`, `U3K3-204`, `U3K3-208` · **ENGINEERING_HYPOTHESIS — needs owner approval**
- on index futures, confirming a rejection block via lower candle volume relative to the opening-range extreme requires volume bars alongside OHLC
  `candle_observable: false` · derived from `U3K3-205` · **ENGINEERING_HYPOTHESIS — needs owner approval**

## (d) HOW HE TREATS IT
- When entering at a bullish rejection block, he places a buy limit order rather than a stop order.
  > "if buying on a bullish order block rejection block or below an old low ideal entry technique is buying on a limit"
  `[U3K3-202]` · `ICT-Mentorship-Core-Content-Month-06-The-Million-Dollar-Swing-Setup-001.json` (E3_2017) · window `W0257` · `added_words: [buy, entering, places, rather]` · note: limit-order entry rule for rejection blocks
- When shorting a fair value gap near a swing high, he places his protective stop loss just above the adjacent rejection block (highest up-close body).
  > "my stop needs to be above it what is it what's what's it going to be the rejection block over here the eyes up close"
  `[U3K3-203]` · `ICT-Charter-Price-Action-Model-8-Targeting-6%-Per-Month-001.json` (E4_2019_2022) · window `W0258` · `added_words: [adjacent, body, high, highest, near, places, protective, shorting, swing]` · note: using the rejection block for tight stop-loss placement; [sic-asr] 'eyes up close' for 'highest up close'

## (e) COMPARING INSTANCES
- When price sweeps below a rejection block's body close, respecting the 50% midpoint of the candle's wick/tail signals stronger underlying strength than a full wick sweep.
  > "even the lowest movement here didn't breach or go below the midpoint of that candle's tail"
  `[U3K3-204]` · `ICT-Mentorship-2023-September-05-2023-Live-ES-&-NQ-Tape-Reading-001.json` (E5_2023_2024) · window `W0265` · `added_words: [block's, body, full, respecting, signals, strength, stronger, sweep, sweeps, underlying, wick]` · note: comparative strength: holding above the 50% midpoint of the rejection block's tail/wick

## (f) INTERACTIONS
- On index futures, a sweep into a rejection block on lower volume than the earlier opening-range low confirms a lack of selling pressure and supports reversal higher.
  > "that rejection block seen here did not see a higher run in volume and it was eventually rejected and price traded higher on the day"
  `[U3K3-205]` · `ICT-Mentorship-Core-Content-Month-10-Index-Futures-Basics-&-Opening-Range-Concept-001.json` (E3_2017) · window `W0269` · `added_words: [confirms, futures, index, lack, lower, pressure, reversal, selling, supports, sweep]` · note: interaction of rejection block with volume divergence in index futures

## (g) TIMEFRAME
- He maps rejection blocks on monthly and weekly charts (W0260, W0263) down to 1-hour and 15-minute charts (W0265, W0267) as both entry arrays and profit targets (W0266).
  > "we're back on our Aussie dollars as a monthly and all I did was change some colors to keep it in better Clarity"
  `[U3K3-206]` · `ICT-Mentorship-Core-Content-Month-12-Intermediate-Term-Top-Down-Analysis-001.json` (E3_2017) · window `W0260` · `added_words: [blocks, charts, entry, hour, maps, minute, profit, targets, w0260, w0263, w0265, w0266, w0267]` · note: cross-timeframe application from monthly/weekly down to 1h/15m

## (h) FAILURE / INVALIDATION and DISCRETION
- In choppy, non-clean tape, price can slice straight through a rejection block closing price and fail rapidly.
  > "so you use like the rejection block here which is this price that closing price right there"
  `[U3K3-207]` · `Price-Action-Chronicles-February-07-2023-003.json` (E5_2023_2024) · window `W0268` · `added_words: [choppy, clean, fail, non, rapidly, slice, straight, tape]` · note: failure of a rejection block in choppy intraday tape

## (i) VARIANTS (kept parallel, never merged)
- He applies 'rejection block' both to long-wicked swing extremes (W0256, W0265) and to clusters of equal-body candle closes whose wicks house resting stop liquidity (W0264, W0266).
  > "see that equal Body candles above that we would expect to see a rejection block price reaches through that as well"
  `[U3K3-208]` · `ICT-Mentorship-Core-Content-Month-05-Trade-Conditions-&-Setup-Progressions-001.json` (E3_2017) · window `W0266` · `added_words: ['rejection, applies, block', candle, closes, clusters, extremes, house, liquidity, long, resting, swing, w0256, w0264, w0265, w0266, wicked, wicks]` · note: parallel visual forms: long single/multi-candle tail vs equal-body closes with wicks beyond

## Windows Logged and Read This Session (`±100` words each)
| Window | Era | Match | Transcript | Word Range | SHA-256 (prefix) |
|---|---|---|---|---|---|
| `W0256` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-04-ICT-Rejection-Block-001.json` | `562..763` (201w) | `e7e291e5cec5` |
| `W0257` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-06-The-Million-Dollar-Swing-Setup-001.json` | `2044..2245` (201w) | `49b7b198b4ff` |
| `W0258` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-8-Targeting-6%-Per-Month-001.json` | `7189..7390` (201w) | `f4e96835c500` |
| `W0259` | `E5_2023_2024` | `exact_kept_tsv` | `March-30-2023-Live-Tape-Reading-AM-Session-002.json` | `3020..3221` (201w) | `65e9a696510c` |
| `W0260` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-12-Intermediate-Term-Top-Down-Analysis-001.json` | `3467..3668` (201w) | `3d356d2f79cf` |
| `W0261` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Emini-S&P-500-AM-&-PM-Session-Review-09-02-22-001.json` | `1336..1537` (201w) | `7995d5376cfc` |
| `W0262` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-Mentorship-2023-One-Trading-Setup-For-Life-002.json` | `1070..1271` (201w) | `656e1c87cb8f` |
| `W0263` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-07-Intraweek-Market-Reversals-&-Overlapping-Models-001.json` | `555..756` (201w) | `bb5742ddf5f9` |
| `W0264` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-6-Universal-Trading-Model-001.json` | `3606..3807` (201w) | `8a17f0d4810d` |
| `W0265` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-Mentorship-2023-September-05-2023-Live-ES-&-NQ-Tape-Reading-001.json` | `4344..4545` (201w) | `af4cca959ced` |
| `W0266` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-05-Trade-Conditions-&-Setup-Progressions-001.json` | `2095..2296` (201w) | `625fd2c440e9` |
| `W0267` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-2-Trade-Plan-&-Algorithmic-Theory-001.json` | `6705..6906` (201w) | `4f8d9e46895a` |
| `W0268` | `E5_2023_2024` | `exact_kept_tsv` | `Price-Action-Chronicles-February-07-2023-003.json` | `5520..5721` (201w) | `22e4cf9a7f26` |
| `W0269` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-10-Index-Futures-Basics-&-Opening-Range-Concept-001.json` | `1439..1640` (201w) | `df442b0186e9` |
| `W0270` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-7-Universal-Trading-Model-002.json` | `1520..1721` (201w) | `fac845864e44` |
