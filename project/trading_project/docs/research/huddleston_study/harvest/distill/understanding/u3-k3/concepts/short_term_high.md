# Understanding card — short term high (`short_term_high`)

Windows extracted and read in full (`±100` words) this session: **15** (target 15) across **15** distinct transcripts (`E1_EARLY_SERIES`: 3, `E2_2016`: 3, `E3_2017`: 3, `E4_2019_2022`: 3, `E5_2023_2024`: 3). Meets the 15-window budget.
Claims: U3K3-220, U3K3-221, U3K3-222, U3K3-223, U3K3-224, U3K3-225, U3K3-226, U3K3-227, U3K3-228, U3K3-229, U3K3-230

Every quoted line below is verbatim (≤25 words) from a `±100`-word window logged and read in full this session. Per Rule 2, `statement` in `claims.jsonl` carries the verbatim quote, `reading` carries the interpretation below, and `added_words` lists every word in `reading` absent from the window. Section (c) is explicitly an `ENGINEERING_HYPOTHESIS`, not his words. Empty sections read `NOT_IN_SOURCES`.

## (a) PURPOSE
- After price hits a higher-timeframe support level, breaking above a short-term high confirms an upward market structure break and sets up an optimal trade entry retracement.
  > "this break above that short term high is a market structure break okay so now from an algorithmic standpoint the price will want to retrace"
  `[U3K3-220]` · `OTE-Primer-Intro-To-ICT-Optimal-Trade-Entry-001.json` (E1_EARLY_SERIES) · window `W0296` · `added_words: [breaking, confirms, entry, optimal, retracement, sets, support, timeframe, trade, upward]` · note: role of short-term high break as a bullish market structure break
- In a bullish trend, intermediate short-term highs serve as stepping-stone pools of buy-stop liquidity on the way to the longer-term high.
  > "obviously we have by stop liquidity above this short term high that short-term high and ultimately we have those buy stop liquidity"
  `[U3K3-221]` · `ICT-Mentorship-Core-Content-Month-03-Institutional-Sponsorship-001.json` (E2_2016) · window `W0287` · `added_words: [highs, intermediate, pools, serve, stepping, stone, trend, way]` · note: role of short-term highs as stepping-stone buy-stop liquidity pools

## (b) RECOGNITION (his criteria and his rejections)
- He situates the short-term high at the base of his three-tier swing hierarchy, where a high flanked by lower short-term highs becomes an intermediate-term high.
  > "there's specific highs that are higher than two previous short-term highs again that being animated term high"
  `[U3K3-222]` · `ICT-Trading-Plan-Development-6-001.json` (E1_EARLY_SERIES) · window `W0291` · `added_words: [base, becomes, flanked, hierarchy, intermediate, situates, swing, three, tier]` · note: hierarchical recognition: short-term high -> intermediate-term high -> long-term high; [sic-asr] 'animated term' for 'intermediate term'
- When institutional sponsorship is bullish, he rejects collapsing the entire long position or looking for reversal patterns just because price clears a short-term high.
  > "each time the market goes up and takes out a level of bicep liquidity we don't collapse the trade entirely"
  `[U3K3-223]` · `ICT-Mentorship-Core-Content-Month-03-Institutional-Sponsorship-001.json` (E2_2016) · window `W0287` · `added_words: [clears, collapsing, entire, institutional, long, position, rejects, sponsorship]` · note: REJECTION of reversing or fully exiting on the first short-term high sweep in a bull trend

## (c) OBSERVABLES — ENGINEERING_HYPOTHESIS (needs owner approval)
- a local three-candle (or multi-bar) swing high at the base of the swing hierarchy, measured at its wick high for buy-stop sweeps, stop-loss placement, and market-structure/breaker breaks, and at its candle-body high for Fibonacci OTE anchoring
  `candle_observable: true` · derived from `U3K3-221`, `U3K3-223`, `U3K3-222`, `U3K3-227`, `U3K3-224`, `U3K3-228`, `U3K3-230` · **ENGINEERING_HYPOTHESIS — needs owner approval**

## (d) HOW HE TREATS IT
- Once a short-term high is broken at a higher-timeframe level, he anchors his Fibonacci across the candle bodies from the low to the new high to buy the OTE retracement.
  > "there's a short term high right here so when it's high is broken that's a break in market structure"
  `[U3K3-224]` · `Pattern-Recognition-Fiber-OTE-NYO-and-Asian-Session-001.json` (E4_2019_2022) · window `W0294` · `added_words: [anchors, buy, candle, higher, new, ote, retracement, timeframe]` · note: body-to-body Fibonacci anchor after breaking a short-term high
- When managing a swing short after scaling partial profits, he trails the protective stop loss above the most recent 4-hour short-term high, waiting until past 50% of the range before tightening.
  > "trail stop loss above the most recent four hour short term high be mindful the market cannon will likely make it run for buy stops"
  `[U3K3-225]` · `ICT-Mentorship-Core-Content-Month-06-The-Million-Dollar-Swing-Setup-001.json` (E3_2017) · window `W0298` · `added_words: [managing, partial, past, profits, tightening, trails, waiting]` · note: stop-trailing rule above the most recent 4-hour short-term high

## (e) COMPARING INSTANCES
- He distinguishes a minor internal short-term high (suitable only for a quick scalp) from a more significant 15-minute short-term high needed to frame the daily range.
  > "we're running above a short term high right here there's a fair value got right there hit that now watch it should sell off"
  `[U3K3-226]` · `2022-ICT-Mentorship-Episode-6-001.json` (E4_2019_2022) · window `W0289` · `added_words: [distinguishes, frame, internal, minor, needed, scalp, suitable]` · note: comparative significance: minor internal short-term high vs 15-minute daily-range short-term high

## (f) INTERACTIONS
- A short-term high formed between two lows (where the second low sweeps the first) becomes a bullish breaker block once price rallies through that short-term high.
  > "you have the market creating a low and then the market trades down lower one more time and runs through the short term high"
  `[U3K3-227]` · `ICT-Mentorship-Core-Content-Month-04-ICT-Breaker-Block-001.json` (E2_2016) · window `W0292` · `added_words: [becomes, block, first, lows, rallies, second, sweeps, two]` · note: interaction: short-term high between a low and a lower low forms the bullish breaker

## (g) TIMEFRAME
- After price reaches a higher-timeframe level, he drops to a 15-minute (or 1-minute, W0295) chart during a Killzone to watch for a short-term high break.
  > "drop down into a 15-minute time frame and we're gonna be looking at the time of day"
  `[U3K3-228]` · `Pattern-Recognition-Fiber-OTE-NYO-and-Asian-Session-001.json` (E4_2019_2022) · window `W0294` · `added_words: [chart, drops, higher, killzone, reaches, timeframe, w0295, watch]` · note: multi-timeframe drilldown to 15m/1m for short-term high break

## (h) FAILURE / INVALIDATION and DISCRETION
- After running above a short-term high, price can retrace deep enough to stop out a break-even stop before resuming, which is why he takes partials on the short-term high run.
  > "runs above this short term High you watch me do the execution of partials here I'll take a long you want a fair value Gap"
  `[U3K3-229]` · `ICT-Mentorship-2023-ES-Review-Precision-Results-001.json` (E5_2023_2024) · window `W0295` · `added_words: [deep, enough, price, resuming, retrace, running, takes]` · note: retracement after a short-term high run stopping out break-even runners

## (i) VARIANTS (kept parallel, never merged)
- When measuring a short-term high for Fibonacci OTE placement, he anchors on the candle bodies where the bulk of the volume resides rather than the wick extreme (W0294, W0299, W0300), whereas for stop placement or liquidity sweeps he references the wick high.
  > "you can see this one's slightly higher than this one but this one's where all the volume is"
  `[U3K3-230]` · `OTE-Pattern-Recognition-Series-Vol-13-001.json` (E4_2019_2022) · window `W0299` · `added_words: [anchors, bodies, bulk, candle, extreme, fibonacci, liquidity, measuring, ote, placement, rather, references, resides, stop, sweeps, w0294, w0299, w0300, whereas]` · note: dual measurement convention: candle bodies for Fibonacci valuation vs wick extreme for stops and liquidity sweeps

## Windows Logged and Read This Session (`±100` words each)
| Window | Era | Match | Transcript | Word Range | SHA-256 (prefix) |
|---|---|---|---|---|---|
| `W0286` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-Forex-Scout-Sniper-Basic-Field-Guide-Vol-3-002.json` | `6447..6648` (201w) | `25545778d51a` |
| `W0287` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-03-Institutional-Sponsorship-001.json` | `4120..4321` (201w) | `38dd52ef429a` |
| `W0288` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-12-Intraday-Top-Down-Analysis-002.json` | `152..353` (201w) | `122e3d969528` |
| `W0289` | `E4_2019_2022` | `exact_kept_tsv` | `2022-ICT-Mentorship-Episode-6-001.json` | `5085..5286` (201w) | `31c87ae62b51` |
| `W0290` | `E5_2023_2024` | `exact_kept_tsv` | `Getting-Started-In-ICT-Scalping-Concepts-001.json` | `3751..3952` (201w) | `cb4f7c3b9bd3` |
| `W0291` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-Trading-Plan-Development-6-001.json` | `5540..5741` (201w) | `50e1d39cb18e` |
| `W0292` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-04-ICT-Breaker-Block-001.json` | `1078..1279` (201w) | `39bbfc0cfc89` |
| `W0293` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-05-Defining-Institutional-Swing-Points-001.json` | `3674..3875` (201w) | `46b799145b2f` |
| `W0294` | `E4_2019_2022` | `exact_kept_tsv` | `Pattern-Recognition-Fiber-OTE-NYO-and-Asian-Session-001.json` | `311..512` (201w) | `fb914f552e32` |
| `W0295` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-Mentorship-2023-ES-Review-Precision-Results-001.json` | `1947..2148` (201w) | `e8e54107442c` |
| `W0296` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `OTE-Primer-Intro-To-ICT-Optimal-Trade-Entry-001.json` | `4511..4712` (201w) | `a1b5e6e4d900` |
| `W0297` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-1-Fair-Valuation-001.json` | `2359..2560` (201w) | `7a2e72f79d24` |
| `W0298` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-06-The-Million-Dollar-Swing-Setup-001.json` | `2547..2748` (201w) | `49b7b198b4ff` |
| `W0299` | `E4_2019_2022` | `exact_kept_tsv` | `OTE-Pattern-Recognition-Series-Vol-13-001.json` | `392..593` (201w) | `93a142982a7f` |
| `W0300` | `E5_2023_2024` | `exact_kept_tsv` | `Pattern-Recognition-Selecting-Precision-Price-Objectives-001.json` | `1510..1711` (201w) | `077af20f593a` |
