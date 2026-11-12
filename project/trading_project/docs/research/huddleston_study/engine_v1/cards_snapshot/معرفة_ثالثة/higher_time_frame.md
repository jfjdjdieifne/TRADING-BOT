# Understanding card — higher time frame (`higher_time_frame`)

Windows extracted and read in full (`±100` words) this session: **15** (target 15) across **15** distinct transcripts (`E1_EARLY_SERIES`: 3, `E2_2016`: 4, `E3_2017`: 3, `E4_2019_2022`: 3, `E5_2023_2024`: 2). Meets the 15-window budget.
Claims: U3K3-037, U3K3-038, U3K3-039, U3K3-040, U3K3-041, U3K3-042, U3K3-043, U3K3-044, U3K3-045, U3K3-046, U3K3-047, U3K3-048

Every quoted line below is verbatim (≤25 words) from a `±100`-word window logged and read in full this session. Per Rule 2, `statement` in `claims.jsonl` carries the verbatim quote, `reading` carries the interpretation below, and `added_words` lists every word in `reading` absent from the window. Section (c) is explicitly an `ENGINEERING_HYPOTHESIS`, not his words. Empty sections read `NOT_IN_SOURCES`.

## (a) PURPOSE
- Large fund traders anchor their analysis on monthly, weekly, and daily charts because their transaction volume cannot be executed on small charts.
  > "their analysis is predominantly linked and founded on the monthly weekly and daily time frames because the volume that they work in"
  `[U3K3-037]` · `ICT-Forex-Market-Maker-Series-Vol-3-of-5-001.json` (E1_EARLY_SERIES) · window `W0057` · `added_words: [anchor, cannot, executed, small, transaction]` · note: institutional volume rationale for HTF

## (b) RECOGNITION (his criteria and his rejections)
- He rejects hunting patterns on lower timeframes first; analysis must start on the higher timeframe at obvious key levels.
  > "we don't go to the lower timeframes hunting a pattern or a signal or a setup and then try to find the level"
  `[U3K3-038]` · `ICT-Forex-Scout-Sniper-Basic-Field-Guide-Vol-2-001.json` (E1_EARLY_SERIES) · window `W0047` · `added_words: [analysis, patterns, rejects, timeframe]` · note: REJECTION of bottom-up lower-timeframe pattern hunting
- Dynamic price displacement on a higher timeframe (daily chart) is his evidence of institutional sponsorship entering the market.
  > "this is higher time frame price displacement that means there is clear evidence that there is a large entity entering the marketplace"
  `[U3K3-039]` · `ICT-Mentorship-Core-Content-Month-03-Institutional-Sponsorship-001.json` (E2_2016) · window `W0048` · `added_words: [market, timeframe]` · note: HTF displacement as recognition of sponsorship
- He rejects the idea that charts or down-close candles magically support price; a 4-hour higher-timeframe intraday chart simply reflects order bases.
  > "don't think that there's any particular magic that a down close candle will support your price that's not it either order blocks are not"
  `[U3K3-040]` · `Getting-Started-In-ICT-Scalping-Concepts-001.json` (E5_2023_2024) · window `W0056` · `added_words: [bases, candles, idea, magically, reflects, rejects, simply, timeframe]` · note: REJECTION of mechanical candle/order-block magic

## (c) OBSERVABLES — ENGINEERING_HYPOTHESIS (needs owner approval)
- levels and PD arrays located on monthly, weekly, and daily bars (with 4-hour ranked secondary), requiring price on the lower timeframe to reach the higher-timeframe level before lower-timeframe entry patterns are evaluated
  `candle_observable: true` · derived from `U3K3-038`, `U3K3-043`, `U3K3-044`, `U3K3-037`, `U3K3-046` · **ENGINEERING_HYPOTHESIS — needs owner approval**
- alignment across monthly, weekly, and daily candle direction (e.g. daily finding support at down-close candles while weekly/monthly are bullish) increases setup rank relative to unaligned setups
  `candle_observable: true` · derived from `U3K3-043`, `U3K3-042` · **ENGINEERING_HYPOTHESIS — needs owner approval**

## (d) HOW HE TREATS IT
- For swing setups on higher timeframes, he removes high leverage (e.g. down to 3-to-1) and pairs the setup with high reward-to-risk.
  > "by removing High leverage and coupling higher time frame setups with high ours this is key"
  `[U3K3-041]` · `ICT-Mentorship-Core-Content-Month-06-Reducing-Risk-&-Maximizing-Potential-Reward-In-Swing-Setups-001.json` (E3_2017) · window `W0054` · `added_words: [pairs, removes, reward, risk, setup, timeframes]` · note: leverage reduction with HTF setups; [sic-asr] 'high ours' for 'high Rs'

## (e) COMPARING INSTANCES
- Day trades have higher odds the more higher-timeframe factors (such as trading in the direction of the weekly range) support them.
  > "the more higher time frame ideas that you can find to support the day trade this is going to increase the odds"
  `[U3K3-042]` · `ICT-Mentorship-Core-Content-Month-08-Essentials-To-ICT-Daytrading-001.json` (E3_2017) · window `W0059` · `added_words: [factors, timeframe]` · note: comparative: 'the more higher time frame ideas ... increase the odds'
- Among higher timeframes, he ranks daily institutional order flow as the single most important chart if a trader looks at no higher chart.
  > "the daily order flow is the most important one to know if you don't look at any other time frame"
  `[U3K3-043]` · `ICT-Mentorship-Core-Content-Month-12-Short-Term-Top-Down-Analysis-001.json` (E3_2017) · window `W0049` · `added_words: [chart, looks, ranks, single, timeframes, trader]` · note: comparative superlative: 'the daily order flow is the most important one to know'

## (f) INTERACTIONS
- Once the draw on liquidity from the daily/weekly higher timeframe is known, he drops directly to the 15-minute bellwether chart for execution.
  > "if I understand where my draw and liquidity is from higher time frame daily and or what my expansion is going to be for weekly"
  `[U3K3-044]` · `ICT-Mentorship-ES-Market-Review-January-26-2023-001.json` (E5_2023_2024) · window `W0051` · `added_words: [directly, drops, execution, known, once, timeframe]` · note: interaction between HTF daily/weekly draw and 15-minute execution chart

## (g) TIMEFRAME
- He states that all concepts taught on a 15-minute chart are universal and apply identically on higher-timeframe daily charts.
  > "don't discount it that i'm teaching you in a 15-minute basis because all the concepts are universal"
  `[U3K3-045]` · `ICT-Mentorship-Core-Content-Month-1-Equilibrium-Vs-Premium-001.json` (E2_2016) · window `W0046` · `added_words: [apply, identically, states, taught, timeframe]` · note: K2 seed claim verified in full window: fractal universality across timeframes
- He defines higher-timeframe key levels as monthly, weekly, daily, and 4-hour, placing less significance on the 4-hour than on daily/weekly/monthly.
  > "what makes it a key level is it's on a monthly weekly daily or four hour less importance and significance place on the four hour"
  `[U3K3-046]` · `ICT-Forex-Market-Maker-Series-Vol-3-of-5-001.json` (E1_EARLY_SERIES) · window `W0057` · `added_words: [defines, placing, timeframe]` · note: explicit ranking within HTF set: monthly/weekly/daily > 4-hour

## (h) FAILURE / INVALIDATION and DISCRETION
- When delivering toward a higher-timeframe objective, violation of the intermediate-term rebalanced high or low invalidates the trade idea.
  > "those key highs and lows with them not being violated if they are violated that means your idea is wrong and you cancel"
  `[U3K3-047]` · `2022-ICT-Mentorship-Episode-12-001.json` (E4_2019_2022) · window `W0050` · `added_words: [delivering, invalidates, timeframe, toward, violation]` · note: explicit invalidation rule when targeting HTF objective

## (i) VARIANTS (kept parallel, never merged)
- Rather than holding long-term swing trades, he prefers applying higher-timeframe analysis to day trading and weekly-range setups.
  > "I'm a day trader at at at best with the higher time frame shortterm one shot one kill you know the weekly range"
  `[U3K3-048]` · `ICT-Charter-Price-Action-Model-3-Amplified-Lecture-001.json` (E4_2019_2022) · window `W0055` · `added_words: [analysis, applying, holding, prefers, rather, setups, timeframe, trades]` · note: personal execution variant using HTF for intraday/weekly range

## Windows Logged and Read This Session (`±100` words each)
| Window | Era | Match | Transcript | Word Range | SHA-256 (prefix) |
|---|---|---|---|---|---|
| `W0046` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-1-Equilibrium-Vs-Premium-001.json` | `3073..3274` (201w) | `d34d757e7339` |
| `W0047` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-Forex-Scout-Sniper-Basic-Field-Guide-Vol-2-001.json` | `6400..6601` (201w) | `60b9ea139ec0` |
| `W0048` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-03-Institutional-Sponsorship-001.json` | `1814..2015` (201w) | `38dd52ef429a` |
| `W0049` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-12-Short-Term-Top-Down-Analysis-001.json` | `2067..2268` (201w) | `755eaf35c8fa` |
| `W0050` | `E4_2019_2022` | `exact_kept_tsv` | `2022-ICT-Mentorship-Episode-12-001.json` | `7845..8046` (201w) | `b9c3df11f891` |
| `W0051` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-Mentorship-ES-Market-Review-January-26-2023-001.json` | `367..568` (201w) | `51914ff16f5c` |
| `W0052` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-W-E-N-T-Series-Part-3-of-5-002.json` | `4120..4321` (201w) | `5a0263141f98` |
| `W0053` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-1-Equilibrium-Vs-Discount-001.json` | `2829..3030` (201w) | `580ba219cc71` |
| `W0054` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-06-Reducing-Risk-&-Maximizing-Potential-Reward-In-Swing-Setups-001.json` | `2475..2676` (201w) | `995eefb493aa` |
| `W0055` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-3-Amplified-Lecture-001.json` | `3831..4032` (201w) | `73fca94b3005` |
| `W0056` | `E5_2023_2024` | `exact_kept_tsv` | `Getting-Started-In-ICT-Scalping-Concepts-001.json` | `3499..3700` (201w) | `cb4f7c3b9bd3` |
| `W0057` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-Forex-Market-Maker-Series-Vol-3-of-5-001.json` | `52..253` (201w) | `a93d2b59b004` |
| `W0058` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-04-Reinforcing-Liquidity-Concepts-&-Price-Delivery-001.json` | `5961..6162` (201w) | `267dc1bd4caf` |
| `W0059` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-08-Essentials-To-ICT-Daytrading-001.json` | `406..607` (201w) | `053114e9f048` |
| `W0060` | `E4_2019_2022` | `exact_kept_tsv` | `Pattern-Recognition-Fiber-OTE-NYO-and-Asian-Session-001.json` | `119..320` (201w) | `fb914f552e32` |
