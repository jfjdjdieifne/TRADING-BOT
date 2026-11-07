# Understanding card — opening price (`opening_price`)

Windows extracted and read in full (`±100` words) this session: **15** (target 15) across **15** distinct transcripts (`E1_EARLY_SERIES`: 3, `E2_2016`: 4, `E3_2017`: 3, `E4_2019_2022`: 3, `E5_2023_2024`: 2). Meets the 15-window budget.
Claims: U3K3-164, U3K3-165, U3K3-166, U3K3-167, U3K3-168, U3K3-169, U3K3-170, U3K3-171, U3K3-172, U3K3-173, U3K3-174

Every quoted line below is verbatim (≤25 words) from a `±100`-word window logged and read in full this session. Per Rule 2, `statement` in `claims.jsonl` carries the verbatim quote, `reading` carries the interpretation below, and `added_words` lists every word in `reading` absent from the window. Section (c) is explicitly an `ENGINEERING_HYPOTHESIS`, not his words. Empty sections read `NOT_IN_SOURCES`.

## (a) PURPOSE
- He simplifies daily bias to determining whether the daily range is more likely to expand higher or lower from the opening price.
  > "you just need to know is this daily range more likely to expand higher or lower than the opening price that's it"
  `[U3K3-164]` · `2022-ICT-Mentorship-Episode-10-001.json` (E4_2019_2022) · window `W0215` · `added_words: [determining, simplifies, whether]` · note: core purpose of opening price in daily bias
- In his Power of Three framework, the opening price serves as the dividing line to buy at or below on bullish days (and sell above on bearish days).
  > "what i have taught is power three is when you're bullish you want to be buying near or below the opening price"
  `[U3K3-165]` · `ICT-Mentorship-Core-Content-Month-03-Institutional-Sponsorship-001.json` (E2_2016) · window `W0213` · `added_words: [bearish, buy, days, dividing, framework, line, sell, serves]` · note: Power of Three purpose of opening price

## (b) RECOGNITION (his criteria and his rejections)
- On a bearish day, any rally at or above the midnight New York opening price is recognized as the 'selling kill ground'.
  > "the sell signal will occur above the opening price so anything at the opening price or above that is our selling kill ground"
  `[U3K3-166]` · `ICT-W-E-N-T-Series-5-of-5-001.json` (E1_EARLY_SERIES) · window `W0217` · `added_words: ['selling, bearish, day, ground', rally, recognized]` · note: recognition of selling zone above midnight opening price
- He rejects trusting a drop below and reclaim of the weekly opening price on Monday, preferring to wait for Monday's range to form and buy Tuesday.
  > "this right here we dropped down and went back above the opening price I don't trust this because it's Monday"
  `[U3K3-167]` · `ICT-Forex-The-Weekly-Bias-Excellence-In-Short-Term-Trading-001.json` (E1_EARLY_SERIES) · window `W0212` · `added_words: [drop, form, preferring, reclaim, rejects, trusting, wait]` · note: REJECTION of Monday weekly-opening-price reversal (~90% of the time sits out Monday)

## (c) OBSERVABLES — ENGINEERING_HYPOTHESIS (needs owner approval)
- for time-based opens (00:00 NY daily, 08:30/09:30 NY session, Sunday 17:00/18:00 NY or Monday 00:00 NY weekly): the open of the anchor bar projected horizontally, classifying prices below it as discount/accumulation for longs and prices above it as premium/distribution for shorts
  `candle_observable: true` · derived from `U3K3-168`, `U3K3-165`, `U3K3-166`, `U3K3-174` · **ENGINEERING_HYPOTHESIS — needs owner approval**
- for candle-based opens (order block opening price, W0221/W0223): the open price of the last down-close (bullish OB) or up-close (bearish OB) candle before displacement, projected forward as support/resistance
  `candle_observable: true` · derived from `U3K3-164`, `U3K3-165` · **ENGINEERING_HYPOTHESIS — needs owner approval**

## (d) HOW HE TREATS IT
- When higher-timeframe structure is bearish, a day trader sells above the New York midnight opening price to capture downward expansions.
  > "you could be a day trader selling it above the opening price above the midnight candle in new york"
  `[U3K3-168]` · `ICT-Mentorship-Core-Content-Month-03-Institutional-Market-Structure-001.json` (E2_2016) · window `W0211` · `added_words: [bearish, downward, expansions, higher, sells, timeframe]` · note: K2 seed claim verified in full window
- When bullish, he buys during the Judas swing drop below the opening price rather than chasing price higher.
  > "you want to be buying on the Judas swing down or below the opening price and don't chase price"
  `[U3K3-169]` · `ICT-Mentorship-Core-Content-Month-09-Bread-&-Butter-Buy-Setups-001.json` (E3_2017) · window `W0219` · `added_words: [bullish, buys, chasing, drop, rather]` · note: bullish execution rule below opening price

## (e) COMPARING INSTANCES
- For a 100-pip average daily range currency pair, he ranks a 20–30 pip drop below the opening price (up to one-third of ADR, 33 pips) as ideal compared to drops exceeding 40 pips.
  > "if we're bullish we're looking for the opening price and then the market to trade down 20 to 30 Pips ideally no more than 33"
  `[U3K3-170]` · `ICT-Mentorship-Core-Content-Month-08-Central-Bank-Dealers-Range-001.json` (E3_2017) · window `W0214` · `added_words: [adr, compared, currency, drops, exceeding, pair, ranks]` · note: explicitly scaled as one-third of a 100-pip ADR ballpark, not a universal cross-asset constant

## (f) INTERACTIONS
- He combines a drop below the opening price with a shift in market structure inside the active dealing range to confirm algorithmic accumulation.
  > "with this short-term High it breaks above it so there's a shift in Market structure there so I'm looking at all of this area"
  `[U3K3-171]` · `January-2023-NonFarm-Payroll-Review-&-HTF-Concepts-001.json` (E5_2023_2024) · window `W0216` · `added_words: [accumulation, active, algorithmic, combines, confirm, drop]` · note: interaction with shift in market structure and dealing range

## (g) TIMEFRAME
- He applies the opening-price Power of Three concept fractally across the daily candle (midnight NY), the weekly candle (Sunday/Monday open), and the 9:30 AM equity open (W0225).
  > "this opening price in here what we're utilizing is the idea of power three on the weekly chart"
  `[U3K3-172]` · `ICT-Charter-Price-Action-Model-2-Amplified-Lecture-001.json` (E4_2019_2022) · window `W0220` · `added_words: [applies, concept, daily, equity, fractally, midnight, sunday, w0225]` · note: fractal application across weekly, daily, and intraday session opens

## (h) FAILURE / INVALIDATION and DISCRETION
- On a bearish weekly candle, the opening price does not have to sit at the very top of the week; an initial Tuesday Judas swing above the open is expected.
  > "this opening price here may be a little bit lower in the weekly candle which is fine we don't necessarily need it to be"
  `[U3K3-173]` · `ICT-Charter-Price-Action-Model-2-Amplified-Lecture-001.json` (E4_2019_2022) · window `W0220` · `added_words: [expected, initial, judas, open, sit, swing, top]` · note: tolerance for excursion beyond the weekly opening price

## (i) VARIANTS (kept parallel, never merged)
- He uses 'opening price' across four distinct parallel anchors: (1) midnight NY daily open (W0211), (2) Sunday natural vs Monday midnight weekly open (W0224), (3) 9:30 AM NY equity open (W0225), and (4) the opening price of an order-block candle (W0221, W0223).
  > "the standard natural Sunday's opening price and then I have midnight opening on Monday so it's midnight in Monday morning in New York time"
  `[U3K3-174]` · `ICT-Mentorship-Core-Content-Month-12-Short-Term-Top-Down-Analysis-001.json` (E3_2017) · window `W0224` · `added_words: ['opening, anchors, block, candle, daily, distinct, equity, four, open, order, parallel, price', uses, w0211, w0221, w0223, w0224, w0225]` · note: four parallel referents of 'opening price' kept distinct

## Windows Logged and Read This Session (`±100` words each)
| Window | Era | Match | Transcript | Word Range | SHA-256 (prefix) |
|---|---|---|---|---|---|
| `W0211` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-03-Institutional-Market-Structure-001.json` | `2820..3021` (201w) | `18b779be4dc2` |
| `W0212` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-Forex-The-Weekly-Bias-Excellence-In-Short-Term-Trading-001.json` | `2957..3158` (201w) | `c1665c358941` |
| `W0213` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-03-Institutional-Sponsorship-001.json` | `5857..6058` (201w) | `38dd52ef429a` |
| `W0214` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-08-Central-Bank-Dealers-Range-001.json` | `1888..2089` (201w) | `bf06fe8e20dc` |
| `W0215` | `E4_2019_2022` | `exact_kept_tsv` | `2022-ICT-Mentorship-Episode-10-001.json` | `3043..3244` (201w) | `2280c5b845f3` |
| `W0216` | `E5_2023_2024` | `exact_kept_tsv` | `January-2023-NonFarm-Payroll-Review-&-HTF-Concepts-001.json` | `4583..4784` (201w) | `28f000a3d00c` |
| `W0217` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-W-E-N-T-Series-5-of-5-001.json` | `5305..5506` (201w) | `d8482cef7970` |
| `W0218` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-04-Liquidity-Pools-001.json` | `2947..3148` (201w) | `b0a58bfba6e5` |
| `W0219` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-09-Bread-&-Butter-Buy-Setups-001.json` | `2778..2979` (201w) | `a0f805b27ddc` |
| `W0220` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-2-Amplified-Lecture-001.json` | `1527..1728` (201w) | `3fe1d012a146` |
| `W0221` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-Forex-Review-January-09-2023-001.json` | `581..782` (201w) | `c224abc24ad3` |
| `W0222` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-Forex-Market-Maker-Series-Vol-4-of-5-001.json` | `1652..1853` (201w) | `cce95919eecf` |
| `W0223` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-03-Market-Maker-Trap-Trendline-Phantoms-001.json` | `2801..3002` (201w) | `4f84b5c757d8` |
| `W0224` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-12-Short-Term-Top-Down-Analysis-001.json` | `3612..3813` (201w) | `755eaf35c8fa` |
| `W0225` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Emini-S&P-500-AM-&-PM-Session-Review-09-02-22-001.json` | `1788..1989` (201w) | `7995d5376cfc` |
