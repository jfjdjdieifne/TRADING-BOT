# Understanding card — midnight (`midnight`)

Windows extracted and read in full (`±100` words) this session: **15** (target 15) across **15** distinct transcripts (`E1_EARLY_SERIES`: 3, `E2_2016`: 4, `E3_2017`: 3, `E4_2019_2022`: 3, `E5_2023_2024`: 2). Meets the 15-window budget.
Claims: U3K3-118, U3K3-119, U3K3-120, U3K3-121, U3K3-122, U3K3-123, U3K3-124, U3K3-125, U3K3-126, U3K3-127, U3K3-128

Every quoted line below is verbatim (≤25 words) from a `±100`-word window logged and read in full this session. Per Rule 2, `statement` in `claims.jsonl` carries the verbatim quote, `reading` carries the interpretation below, and `added_words` lists every word in `reading` absent from the window. Section (c) is explicitly an `ENGINEERING_HYPOTHESIS`, not his words. Empty sections read `NOT_IN_SOURCES`.

## (a) PURPOSE
- He defines New York midnight time as the true start of his new trading day and daily range.
  > "I'm referencing New York midnight time as the beginning of my new trading day"
  `[U3K3-118]` · `ICT-W-E-N-T-Series-5-of-5-001.json` (E1_EARLY_SERIES) · window `W0152` · `added_words: [defines, start, true]` · note: definition and purpose of New York midnight
- He states that at midnight New York time the daily high and daily low are already predetermined by the algorithm.
  > "price is 100% manipulated and the daily high and daily low are already predetermined at midnight in New York time"
  `[U3K3-119]` · `Getting-Started-In-ICT-Scalping-Concepts-001.json` (E5_2023_2024) · window `W0161` · `added_words: [algorithm, states]` · note: algorithmic predetermination claim at midnight NY

## (b) RECOGNITION (his criteria and his rejections)
- On a buy day, right after midnight New York time price drops down in a false manipulation move before expanding higher.
  > "right after midnight new york time there's a drop down in price that's the manipulation making the false move"
  `[U3K3-120]` · `ICT-Mentorship-Core-Content-Month-1-How-Market-Makers-Condition-The-Market-001.json` (E2_2016) · window `W0151` · `added_words: [buy, drops]` · note: K2 seed claim verified in full window
- He rejects trading the post-midnight protraction state when the CBDR or Asian range prior to midnight is trending or wide rather than a tight consolidation.
  > "if the Asian range gets really wild or widens up that again lessens the statistical Edge that ipta will give us"
  `[U3K3-121]` · `ICT-Mentorship-Core-Content-Month-08-When-To-Avoid-The-London-Session-001.json` (E3_2017) · window `W0154` · `added_words: [cbdr, post, prior, protraction, rather, rejects, trading, wide]` · note: REJECTION of post-midnight setup when pre-midnight ranges trend

## (c) OBSERVABLES — ENGINEERING_HYPOTHESIS (needs owner approval)
- the opening price of the 00:00 America/New_York candle, used as a horizontal intraday reference line separating post-midnight discount (below) from post-midnight premium (above)
  `candle_observable: true` · derived from `U3K3-118`, `U3K3-123`, `U3K3-122`, `U3K3-127` · **ENGINEERING_HYPOTHESIS — needs owner approval**
- when intraday price trends away from the 00:00 NY open without retracing across it, the reference shifts to the 08:30 NY session open as a parallel intraday anchor
  `candle_observable: true` · derived from `U3K3-122`, `U3K3-127`, `U3K3-128` · **ENGINEERING_HYPOTHESIS — needs owner approval**

## (d) HOW HE TREATS IT
- He sets the chart timezone to New York, extends the midnight candle's opening price across the day, and looks to buy below it when bullish.
  > "draw that out in time and that's your new york midnight opening price this is the price i want to preferably be buying below"
  `[U3K3-122]` · `2022-ICT-Mentorship-Episode-19-002.json` (E4_2019_2022) · window `W0160` · `added_words: [bullish, candle's, day, extends, looks, sets, timezone]` · note: chart annotation and execution rule
- When the daily chart and dollar index favor lower prices, he day-trades by selling above the New York midnight candle's opening price.
  > "you could be a day trader selling it above the opening price above the midnight candle in new york"
  `[U3K3-123]` · `ICT-Mentorship-Core-Content-Month-03-Institutional-Market-Structure-001.json` (E2_2016) · window `W0158` · `added_words: [candle's, favor, trades]` · note: bearish execution rule above midnight opening price

## (e) COMPARING INSTANCES
- He prefers focusing on midnight New York time over the earlier 0:00 GMT start because trading at 0:00 GMT promotes overtrading and double attempts.
  > "never worry about having to get that zero GMT early start of the daily range and just focusing on midnight"
  `[U3K3-124]` · `ICT-Mentorship-Core-Content-Month-09-ICT-Day-Trade-Routine-001.json` (E3_2017) · window `W0159` · `added_words: [attempts, double, earlier, overtrading, prefers]` · note: comparative preference: midnight NY > 0:00 GMT

## (f) INTERACTIONS
- After midnight New York, he combines a drop below the midnight opening price with standard deviations of the Asian range, flout, or CBDR into a 15-minute discount PD array.
  > "below that opening price to some measure of standard deviations of the Asian range the flout or Central Bank dealers range"
  `[U3K3-125]` · `ICT-Mentorship-Core-Content-Month-09-ICT-Day-Trade-Routine-001.json` (E3_2017) · window `W0159` · `added_words: [cbdr, combines, drop]` · note: interaction of midnight open with CBDR/Asian range/flout and 15m PD array

## (g) TIMEFRAME
- He marks the midnight opening price on a 15-minute chart alongside day-of-week accumulation (Mon–Wed) and session timing (London low, NY OTE).
  > "on a 15-minute time frame i'm going to incorporate day of week and time of day here's that opening price at midnight"
  `[U3K3-126]` · `ICT-Forex-Market-Maker-Series-Vol-4-of-5-001.json` (E1_EARLY_SERIES) · window `W0162` · `added_words: [accumulation, alongside, chart, marks, mon, ote, session, timing, wed]` · note: 15-minute chart integration with weekly and intraday time

## (h) FAILURE / INVALIDATION and DISCRETION
- When a bullish market expands higher without ever retracing back below the midnight opening price, he switches to the 8:30 AM New York opening price.
  > "the opening price will be lower and then the market is trading higher but doesn't go back below the midnight opening price"
  `[U3K3-127]` · `2022-ICT-Mentorship-Episode-19-002.json` (E4_2019_2022) · window `W0160` · `added_words: [bullish, ever, expands, retracing, switches]` · note: fallback rule when price fails to retrace below midnight opening price

## (i) VARIANTS (kept parallel, never merged)
- For the weekly range profile he keeps two parallel anchors: Sunday's natural opening price and Monday's midnight New York opening price.
  > "the standard natural Sunday's opening price and then I have midnight opening on Monday so it's midnight in Monday morning in New York"
  `[U3K3-128]` · `ICT-Mentorship-Core-Content-Month-12-Short-Term-Top-Down-Analysis-001.json` (E3_2017) · window `W0164` · `added_words: [anchors, keeps, monday's, parallel]` · note: parallel weekly variant: Sunday open vs Monday midnight NY open

## Windows Logged and Read This Session (`±100` words each)
| Window | Era | Match | Transcript | Word Range | SHA-256 (prefix) |
|---|---|---|---|---|---|
| `W0151` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-1-How-Market-Makers-Condition-The-Market-001.json` | `2383..2584` (201w) | `5aa74c544fb0` |
| `W0152` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-W-E-N-T-Series-5-of-5-001.json` | `6286..6487` (201w) | `d8482cef7970` |
| `W0153` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-1-Impulse-Price-Swings-&-Market-Protraction-001.json` | `751..952` (201w) | `9d74168ea389` |
| `W0154` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-08-When-To-Avoid-The-London-Session-001.json` | `1720..1921` (201w) | `81cc5e41e6a4` |
| `W0155` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-5-Day-Trading-Intraday-Volatility-Expansions-001.json` | `2562..2763` (201w) | `3932ce412c57` |
| `W0156` | `E5_2023_2024` | `exact_kept_tsv` | `March-31-2023-Live-Tape-Reading-AM-Session-003.json` | `6233..6434` (201w) | `ec96259c40bf` |
| `W0157` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-Mastering-High-Probability-Scalping-Vol-3-of-3-001.json` | `575..776` (201w) | `a22831c6105f` |
| `W0158` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-03-Institutional-Market-Structure-001.json` | `2824..3025` (201w) | `18b779be4dc2` |
| `W0159` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-09-ICT-Day-Trade-Routine-001.json` | `7549..7750` (201w) | `9f8913e03f11` |
| `W0160` | `E4_2019_2022` | `exact_kept_tsv` | `2022-ICT-Mentorship-Episode-19-002.json` | `7616..7817` (201w) | `e7984f244145` |
| `W0161` | `E5_2023_2024` | `exact_kept_tsv` | `Getting-Started-In-ICT-Scalping-Concepts-001.json` | `2134..2335` (201w) | `cb4f7c3b9bd3` |
| `W0162` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-Forex-Market-Maker-Series-Vol-4-of-5-001.json` | `1655..1856` (201w) | `cce95919eecf` |
| `W0163` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-02-The-Secrets-To-Selecting-High-Reward-Setups-001.json` | `2831..3032` (201w) | `04fe064cf1e5` |
| `W0164` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-12-Short-Term-Top-Down-Analysis-001.json` | `3611..3812` (201w) | `755eaf35c8fa` |
| `W0165` | `E4_2019_2022` | `exact_kept_tsv` | `OTE-Pattern-Recognition-Series-Vol-01-001.json` | `5620..5821` (201w) | `23a1c57b935d` |
