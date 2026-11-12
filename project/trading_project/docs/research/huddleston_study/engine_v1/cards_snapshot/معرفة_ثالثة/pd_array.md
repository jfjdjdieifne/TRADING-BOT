# Understanding card — pd array (`pd_array`)

Windows extracted and read in full (`±100` words) this session: **15** (target 15) across **15** distinct transcripts (`E1_EARLY_SERIES`: 1, `E3_2017`: 6, `E4_2019_2022`: 4, `E5_2023_2024`: 4). Meets the 15-window budget.
Claims: U3K3-175, U3K3-176, U3K3-177, U3K3-178, U3K3-179, U3K3-180, U3K3-181, U3K3-182, U3K3-183, U3K3-184, U3K3-185, U3K3-186

Every quoted line below is verbatim (≤25 words) from a `±100`-word window logged and read in full this session. Per Rule 2, `statement` in `claims.jsonl` carries the verbatim quote, `reading` carries the interpretation below, and `added_words` lists every word in `reading` absent from the window. Section (c) is explicitly an `ENGINEERING_HYPOTHESIS`, not his words. Empty sections read `NOT_IN_SOURCES`.

## (a) PURPOSE
- He uses the PD Array Matrix to classify the market into premium and discount zones and calibrate specific entry and target price levels.
  > "I look at the PD array Matrix and I want to define the market in terms of a premium and discount"
  `[U3K3-175]` · `ICT-Mentorship-Core-Content-Month-12-Long-Term-Top-Down-Analysis-001.json` (E3_2017) · window `W0228` · `added_words: [classify, specific, target, uses, zones]` · note: core purpose of the PD array matrix
- He states that reading individual PD arrays replaces any need for depth-of-market ladders or volume profile indicators.
  > "reading and interpreting each individual PD array helps you without having to have any kind of like depth of Market"
  `[U3K3-176]` · `Market-Review-February-09-2023-001.json` (E5_2023_2024) · window `W0239` · `added_words: [indicators, replaces, states]` · note: purpose vs DOM/volume profile

## (b) RECOGNITION (his criteria and his rejections)
- Within a defined dealing range, discount PD arrays lie from equilibrium (50%) down to the 0% low, while premium PD arrays lie above equilibrium.
  > "from equilibrium below down to the zero level is your discount pd arrays focusing on the range defined here"
  `[U3K3-177]` · `ICT-Mentorship-Core-Content-Month-06-High-Probability-Swing-Trade-Setups-In-Bull-Markets-001.json` (E3_2017) · window `W0237` · `added_words: [dealing, lie, low]` · note: recognition of discount vs premium PD arrays inside a dealing range
- He rejects acting on a time window alone unless price is simultaneously engaging a key PD array.
  > "time is of no use unless price is at a key pd array"
  `[U3K3-178]` · `2022-ICT-Mentorship-Episode-39-001.json` (E4_2019_2022) · window `W0232` · `added_words: [acting, alone, engaging, rejects, simultaneously, window]` · note: REJECTION of time-of-day without a key PD array
- He rejects taking new longs at deep premium PD arrays (80–90% of the range) or new shorts at deep discount PD arrays (20–30% of the range).
  > "premium at the 90 level and i don't like to see any new logs in these levels here and i don't like to take"
  `[U3K3-179]` · `ICT-Mentorship-Core-Content-Month-06-High-Probability-Swing-Trade-Setups-In-Bull-Markets-001.json` (E3_2017) · window `W0237` · `added_words: [arrays, longs, rejects, taking]` · note: REJECTION of new longs in deep premium and new shorts in deep discount; [sic-asr] 'logs' for 'longs'

## (c) OBSERVABLES — ENGINEERING_HYPOTHESIS (needs owner approval)
- an ordered set of structural price zones partitioned by the 50% equilibrium of the active dealing range into premium arrays (above 50%) and discount arrays (below 50%), ordered outward from equilibrium as mitigation block -> breaker block -> liquidity void / fair value gap -> propulsion / order block -> rejection block -> old high / old low
  `candle_observable: true` · derived from `U3K3-181`, `U3K3-182`, `U3K3-177`, `U3K3-179` · **ENGINEERING_HYPOTHESIS — needs owner approval**
- choosing which specific PD array will halt price when several coexist requires narrative and higher-timeframe context beyond raw candle geometry
  `candle_observable: false` · derived from `U3K3-186` · **ENGINEERING_HYPOTHESIS — needs owner approval**

## (d) HOW HE TREATS IT
- Each time price reaches into a tracked PD array, he anticipates a reaction or retracement and monitors whether newly formed inefficiencies refill.
  > "every time it reaches into one of these levels or another PD array that I may have interest in I'm anticipating some measure of retracement"
  `[U3K3-180]` · `ICT-Mentorship-2023-Immediate-Rebalance-&-Institutional-Order-Flow-002.json` (E5_2023_2024) · window `W0233` · `added_words: [anticipates, inefficiencies, monitors, newly, price, reaction, refill, tracked, whether]` · note: active tape-reading treatment at each PD array

## (e) COMPARING INSTANCES
- Within the PD array hierarchy, when a breaker is present it takes precedence over closing a liquidity void or reaching a further fair value gap or order block.
  > "the breaker is going to take precedence over everything on this list when you're below it in terms of market price"
  `[U3K3-181]` · `ICT-Mentorship-Core-Content-Month-05-Defining-HTF-PD-Arrays-001.json` (E3_2017) · window `W0226` · `added_words: [fair, further, hierarchy, liquidity, present, reaching, takes, value]` · note: K2 seed window verified: explicit precedence ordering in the PD array matrix
- Moving away from equilibrium into discount, the expected PD array sequence starts with a mitigation block, then a bullish breaker, before deeper arrays.
  > "in the form of a discount the first one you would anticipate seeing is a mitigation block bullishly then a"
  `[U3K3-182]` · `ICT-Mentorship-Core-Content-Month-05-Defining-HTF-PD-Arrays-001.json` (E3_2017) · window `W0226` · `added_words: [away, deeper, moving, sequence, starts]` · note: expected sequence of discount PD arrays from equilibrium outward

## (f) INTERACTIONS
- For high-probability London day trades, he couples 1–2 standard deviations of the CBDR or Asian range with a premium PD array between 2:00 and 4:00 AM NY.
  > "looking to sell one to two standard deviations of the Central Bank dealers range and or Asian range coupled with a premium PD array"
  `[U3K3-183]` · `ICT-Mentorship-Core-Content-Month-08-High-Probability-Daytrade-Setups-001.json` (E3_2017) · window `W0234` · `added_words: [cbdr, couples, london, probability]` · note: interaction of premium PD array with CBDR/Asian range standard deviations and London Killzone

## (g) TIMEFRAME
- Keying off monthly, weekly, and daily PD arrays transposed onto a 4-hour chart produces the highest-probability institutional reactions.
  > "if you key off a daily weekly and monthly PD arrays on a four hour chart you're going to get the highest probable trade reactions"
  `[U3K3-184]` · `ICT-Mentorship-Core-Content-Month-07-Short-Term-Trading-Low-Resistance-Liquidity-Runs-Part-2-001.json` (E3_2017) · window `W0231` · `added_words: [institutional, keying, probability, produces, transposed]` · note: cross-timeframe alignment of M/W/D PD arrays on 4H chart

## (h) FAILURE / INVALIDATION and DISCRETION
- When price fails to reach an expected PD array (such as a breakaway gap or wick consequent encroachment), that non-retest signals extreme one-sided momentum.
  > "PDA rate is not traded to when I am allowing for and my algorithm allows for it to trade to it normally"
  `[U3K3-185]` · `ICT-Mentorship-2023-September-27-2023-Market-Review-Commentary-002.json` (E5_2023_2024) · window `W0230` · `added_words: [encroachment, expected, extreme, fails, momentum, non, one, price, retest, sided, signals]` · note: diagnostic meaning when a PD array fails to be retraced to; [sic-asr] 'PDA rate' for 'PD array'

## (i) VARIANTS (kept parallel, never merged)
- A violated PD array is not discarded; it can invert into an opposing array (inversion FVG) or be reclaimed as a reclaimed discount/premium array.
  > "if it went down through it and it came back above it now I would treat it as you know a reclaimed discount array"
  `[U3K3-186]` · `ICT-Mentorship-2023-September-08-2023-Review-&-ICT-Ma-Deuce-Model-001.json` (E5_2023_2024) · window `W0236` · `added_words: [discarded, fvg, invert, opposing, premium, violated]` · note: parallel states of a PD array: standard vs inversion vs reclaimed

## Windows Logged and Read This Session (`±100` words each)
| Window | Era | Match | Transcript | Word Range | SHA-256 (prefix) |
|---|---|---|---|---|---|
| `W0226` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-05-Defining-HTF-PD-Arrays-001.json` | `4761..4962` (201w) | `60393f36f9d7` |
| `W0227` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `Real-Money-Real-People-ICT-Student-Paladin-001.json` | `2074..2275` (201w) | `550e4ab14276` |
| `W0228` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-12-Long-Term-Top-Down-Analysis-001.json` | `1740..1941` (201w) | `e7905426fe98` |
| `W0229` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-7-Universal-Trading-Model-001.json` | `9480..9681` (201w) | `a707fe1d2e53` |
| `W0230` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-Mentorship-2023-September-27-2023-Market-Review-Commentary-002.json` | `1514..1715` (201w) | `cdea3176bcad` |
| `W0231` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-07-Short-Term-Trading-Low-Resistance-Liquidity-Runs-Part-2-001.json` | `3019..3220` (201w) | `82f52645c8a2` |
| `W0232` | `E4_2019_2022` | `exact_kept_tsv` | `2022-ICT-Mentorship-Episode-39-001.json` | `5780..5981` (201w) | `3234b5e2c022` |
| `W0233` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-Mentorship-2023-Immediate-Rebalance-&-Institutional-Order-Flow-002.json` | `3959..4160` (201w) | `457c66642aa6` |
| `W0234` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-08-High-Probability-Daytrade-Setups-001.json` | `3164..3365` (201w) | `3f8c77321097` |
| `W0235` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Emini-S&P-500-AM-&-PM-Session-Review-09-02-22-001.json` | `1439..1640` (201w) | `7995d5376cfc` |
| `W0236` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-Mentorship-2023-September-08-2023-Review-&-ICT-Ma-Deuce-Model-001.json` | `3179..3380` (201w) | `2d613ad125b1` |
| `W0237` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-06-High-Probability-Swing-Trade-Setups-In-Bull-Markets-001.json` | `5302..5503` (201w) | `b2c2e7f91e1b` |
| `W0238` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-6-Universal-Trading-Model-001.json` | `1000..1201` (201w) | `8a17f0d4810d` |
| `W0239` | `E5_2023_2024` | `exact_kept_tsv` | `Market-Review-February-09-2023-001.json` | `3572..3773` (201w) | `b9808bfb9ce5` |
| `W0240` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-09-Trading-In-Consolidations-001.json` | `2839..3040` (201w) | `1efc38ea8297` |
