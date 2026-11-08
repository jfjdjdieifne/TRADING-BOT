# Understanding card — swing low (`swing_low`)

Windows extracted and read in full (`±100` words) this session: **15** (target 15) across **15** distinct transcripts (`E1_EARLY_SERIES`: 3, `E2_2016`: 3, `E3_2017`: 3, `E4_2019_2022`: 3, `E5_2023_2024`: 3). Meets the 15-window budget.
Claims: U3K3-243, U3K3-244, U3K3-245, U3K3-246, U3K3-247, U3K3-248, U3K3-249, U3K3-250, U3K3-251, U3K3-252, U3K3-253, U3K3-254

Every quoted line below is verbatim (≤25 words) from a `±100`-word window logged and read in full this session. Per Rule 2, `statement` in `claims.jsonl` carries the verbatim quote, `reading` carries the interpretation below, and `added_words` lists every word in `reading` absent from the window. Section (c) is explicitly an `ENGINEERING_HYPOTHESIS`, not his words. Empty sections read `NOT_IN_SOURCES`.

## (a) PURPOSE
- Once a three-bar daily swing low forms at a support level, he anticipates the market seeking liquidity above the previous day's high.
  > "this is a swing low when we have this the markets going to want to seek the liquidity resting the previous day it's high"
  `[U3K3-243]` · `ICT-New-York-Live-Session-October-10-2017-001.json` (E5_2023_2024) · window `W0325` · `added_words: [anticipates, day's, forms, level, market, seeking, support, three]` · note: liquidity-seeking purpose of a daily swing low
- After buy-side liquidity is swept, a sharp displacement break below a swing low frames a high-probability short setup.
  > "this willingness to break sharply below a swing low after taking buy side this is how you frame higher probability"
  `[U3K3-244]` · `Price-Action-Chronicles-February-07-2023-001.json` (E5_2023_2024) · window `W0330` · `added_words: [frames, liquidity, setup, sharp, swept]` · note: displacement break below a swing low to confirm a bearish shift

## (b) RECOGNITION (his criteria and his rejections)
- He defines a swing low as a three-candle formation consisting of a central low flanked by a higher low to the left and a higher low to the right.
  > "it creates a swing low that means a low with a higher load to the right of it and a higher low to the left"
  `[U3K3-245]` · `2022-ICT-Mentorship-Episode-10-001.json` (E4_2019_2022) · window `W0319` · `added_words: [candle, central, consisting, defines, flanked, formation]` · note: exact three-candle definition of a swing low
- He explicitly rejects the five-bar Williams fractal as requiring way too many candles and causing the trader to miss the move.
  > "you do not need a williams fractal that's way too many candles and you've missed the move"
  `[U3K3-246]` · `2022-ICT-Mentorship-Episode-10-001.json` (E4_2019_2022) · window `W0319` · `added_words: [bar, causing, explicitly, five, miss, rejects, requiring, trader]` · note: REJECTION of 5-bar Williams fractal in favor of 3-candle swing low

## (c) OBSERVABLES — ENGINEERING_HYPOTHESIS (needs owner approval)
- a three-candle formation where candle[i].low < candle[i-1].low and candle[i].low < candle[i+1].low (explicitly 3 bars, never a 5-bar Williams fractal), tracked at both its wick low (stop-sweep threshold) and its lowest body open/close (rejection-block conservative target)
  `candle_observable: true` · derived from `U3K3-245`, `U3K3-246`, `U3K3-249`, `U3K3-243` · **ENGINEERING_HYPOTHESIS — needs owner approval**

## (d) HOW HE TREATS IT
- When shorting from an optimal trade entry, he places his take-profit target just below the prior swing low.
  > "goes right after the 70.5 ote optimal trade entry and then sells off where you take profits at below swing low"
  `[U3K3-247]` · `ICT-Mentorship-Core-Content-Month-1-Equilibrium-Vs-Premium-001.json` (E2_2016) · window `W0317` · `added_words: [places, prior, profit, shorting, target]` · note: using a swing low as a short profit-taking objective
- For a bullish retracement setup, he anchors the Fibonacci range from the swing low up to the swing high to locate the OTE and order block.
  > "what we'll do is we're gonna use this swing low here up to the high here okay using that same range"
  `[U3K3-248]` · `ICT-Forex-Scout-Sniper-Basic-Field-Guide-Vol-4-002.json` (E1_EARLY_SERIES) · window `W0326` · `added_words: [anchors, bullish, fibonacci, locate, ote, retracement, setup]` · note: using the swing low as the lower Fibonacci dealing-range anchor

## (e) COMPARING INSTANCES
- For conservative short profit-taking at a swing low, he prefers covering just below the lowest body open or close (rejection block) rather than demanding price breach the wick low.
  > "covering the short just below the lowest open or close in the previous swing low don't always demand that price gets below the wicks"
  `[U3K3-249]` · `ICT-Mentorship-Core-Content-Month-04-ICT-Rejection-Block-001.json` (E2_2016) · window `W0322` · `added_words: [block, body, breach, conservative, demanding, prefers, rather, wick]` · note: comparative exit precision: below lowest body open/close vs below wick extreme
- When multiple swing lows form inside a top consolidation, breaking the highest swing low on the right side of the curve initiates the bearish sequence.
  > "the highest of whatever swing lows that form here you want to go to the highest one once that's broken"
  `[U3K3-250]` · `ICT-Charter-Price-Action-Model-7-Universal-Trading-Model-001.json` (E4_2019_2022) · window `W0324` · `added_words: [bearish, breaking, consolidation, initiates, inside, multiple, sequence, top]` · note: selecting the highest swing low on the right side of the curve

## (f) INTERACTIONS
- In his Bullish Pattern #1, an impulse off a higher-timeframe discount array leaves a fair value gap near the swing low, and a subsequent drop under the intermediate short-term low into that FVG triggers offset accumulation.
  > "an Impulse swing creates a fair value Gap near the swing low a short-term low forms in Market structure and fails to Rally higher"
  `[U3K3-251]` · `ICT-Mentorship-Core-Content-Month-12-Intraday-Top-Down-Analysis-001.json` (E3_2017) · window `W0323` · `added_words: [fvg, intermediate, leaves, subsequent, timeframe, triggers]` · note: interaction of swing low, FVG, and internal short-term low stop run

## (g) TIMEFRAME
- A single swing low on the daily chart contains multi-candle price structure and fair value gaps when inspected through an hourly chart lens.
  > "inside this swing low all this price action this is a swing on a larger daily chart that we're looking at through the lens"
  `[U3K3-252]` · `ICT-Mentorship-2023-Advanced-Gap-Theory-Introduction-001.json` (E5_2023_2024) · window `W0320` · `added_words: [contains, fair, gaps, inspected, multi, single, structure, value]` · note: fractal decomposition of a daily swing low on the hourly chart

## (h) FAILURE / INVALIDATION and DISCRETION
- In a bearish New York continuation setup, if price fails to retrace at least 20 pips from the London swing low by 9:00 AM NY, he cuts bait and passes on the day.
  > "New York session will typically retrace from a swing low now what's swing low the swing low that was formed in the London decline"
  `[U3K3-253]` · `ICT-Mastering-High-Probability-Scalping-Vol-3-of-3-001.json` (E1_EARLY_SERIES) · window `W0321` · `added_words: [continuation, cuts, fails, passes, setup]` · note: stand-aside rule when NY fails to retrace sufficiently from the London swing low by 9:00 AM

## (i) VARIANTS (kept parallel, never merged)
- Depending on context, a swing low functions as (1) a downside sell-stop target (W0317, W0322), (2) a bullish dealing-range anchor (W0326, W0329), (3) an offset-accumulation turtle-soup trap when swept in an uptrend (W0327), or (4) a bearish mitigation/breaker level once broken at a failure swing (W0318, W0324).
  > "that short term little swing low at the failure swing that's going to be what a potential mitigation block"
  `[U3K3-254]` · `ICT-Mentorship-Core-Content-Month-05-Defining-HTF-PD-Arrays-001.json` (E3_2017) · window `W0318` · `added_words: [accumulation, anchor, bearish, breaker, broken, bullish, dealing, depending, downside, functions, level, offset, once, range, sell, soup, stop, swept, target, trap, turtle, uptrend, w0317, w0318, w0322, w0324, w0326, w0327, w0329]` · note: four structural roles of a swing low across market phases

## Windows Logged and Read This Session (`±100` words each)
| Window | Era | Match | Transcript | Word Range | SHA-256 (prefix) |
|---|---|---|---|---|---|
| `W0316` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `Essentials-To-ICT-Market-Structure-001.json` | `2849..3050` (201w) | `fd6ee5d895f2` |
| `W0317` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-1-Equilibrium-Vs-Premium-001.json` | `2653..2854` (201w) | `d34d757e7339` |
| `W0318` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-05-Defining-HTF-PD-Arrays-001.json` | `1238..1439` (201w) | `60393f36f9d7` |
| `W0319` | `E4_2019_2022` | `exact_kept_tsv` | `2022-ICT-Mentorship-Episode-10-001.json` | `3095..3296` (201w) | `2280c5b845f3` |
| `W0320` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-Mentorship-2023-Advanced-Gap-Theory-Introduction-001.json` | `265..466` (201w) | `15f2a89d7934` |
| `W0321` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-Mastering-High-Probability-Scalping-Vol-3-of-3-001.json` | `662..863` (201w) | `a22831c6105f` |
| `W0322` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-04-ICT-Rejection-Block-001.json` | `1894..2095` (201w) | `e7e291e5cec5` |
| `W0323` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-12-Intraday-Top-Down-Analysis-001.json` | `4633..4834` (201w) | `f7a999fa660f` |
| `W0324` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-7-Universal-Trading-Model-001.json` | `5658..5859` (201w) | `a707fe1d2e53` |
| `W0325` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-New-York-Live-Session-October-10-2017-001.json` | `2594..2795` (201w) | `55899d04c7fc` |
| `W0326` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-Forex-Scout-Sniper-Basic-Field-Guide-Vol-4-002.json` | `8554..8755` (201w) | `00a80517ebb2` |
| `W0327` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-03-Institutional-Market-Structure-001.json` | `405..606` (201w) | `18b779be4dc2` |
| `W0328` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-11-Bond-Mega-Trades-001.json` | `4002..4203` (201w) | `14a487e72001` |
| `W0329` | `E4_2019_2022` | `exact_kept_tsv` | `OTE-Pattern-Recognition-Series-Vol-08-001.json` | `554..755` (201w) | `614bf3e20504` |
| `W0330` | `E5_2023_2024` | `exact_kept_tsv` | `Price-Action-Chronicles-February-07-2023-001.json` | `6254..6455` (201w) | `b017bd154a51` |
