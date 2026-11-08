# Understanding card — smt divergence (`smt_divergence`)

Windows extracted and read in full (`±100` words) this session: **15** (target 15) across **15** distinct transcripts (`E1_EARLY_SERIES`: 3, `E2_2016`: 3, `E3_2017`: 3, `E4_2019_2022`: 3, `E5_2023_2024`: 3). Meets the 15-window budget.
Claims: U3K3-231, U3K3-232, U3K3-233, U3K3-234, U3K3-235, U3K3-236, U3K3-237, U3K3-238, U3K3-239, U3K3-240, U3K3-241, U3K3-242

Every quoted line below is verbatim (≤25 words) from a `±100`-word window logged and read in full this session. Per Rule 2, `statement` in `claims.jsonl` carries the verbatim quote, `reading` carries the interpretation below, and `added_words` lists every word in `reading` absent from the window. Section (c) is explicitly an `ENGINEERING_HYPOTHESIS`, not his words. Empty sections read `NOT_IN_SOURCES`.

## (a) PURPOSE
- He defines SMT divergence ('Smart Money Technique' or 'Smart Money Tool') as his method for reading cracks in correlation between closely or inversely correlated assets.
  > "smt is a smart money technique or smart money tool I've never settled in on what the T stands for"
  `[U3K3-231]` · `ICT-Mentorship-2023-September-27-2023-PM-Session-Market-Review-001.json` (E5_2023_2024) · window `W0305` · `added_words: ['smart, assets, closely, correlated, defines, inversely, method, technique', tool']` · note: core definition and purpose of SMT divergence
- A failure of the US Dollar Index and a foreign currency pair to make symmetrical highs/lows reveals active institutional accumulation or distribution.
  > "if the us dollar index or a foreign currency pair fails to move symmetrically smart money is actively trading"
  `[U3K3-232]` · `ICT-Mentorship-Core-Content-Month-03-Institutional-Market-Structure-001.json` (E2_2016) · window `W0302` · `added_words: [accumulation, active, distribution, failure, highs, institutional, lows, make, reveals, symmetrical]` · note: institutional footprint purpose

## (b) RECOGNITION (his criteria and his rejections)
- He recognizes a bearish foreign-currency SMT divergence when the Dollar Index makes a lower low (turtle soup long) while the foreign currency fails to make a higher high.
  > "when a dollar makes a lower low and the foreign currency fails make a higher high the weakness is in the foreign currency"
  `[U3K3-233]` · `ICT-Forex-The-ICT-Smart-Money-Technique-or-SMT-001.json` (E1_EARLY_SERIES) · window `W0301` · `added_words: [index, recognizes]` · note: inversely correlated recognition rule (DXY vs GBPUSD)
- Between positively correlated equity indices, he recognizes a bullish SMT divergence when Nasdaq makes a lower low while S&P 500 makes a higher low.
  > "smt divergence here lower low higher low here we have the lower low in nasdaq higher low in s p"
  `[U3K3-234]` · `2022-ICT-Mentorship-Episode-38-001.json` (E4_2019_2022) · window `W0314` · `added_words: [500, bullish, correlated, equity, indices, positively, recognizes]` · note: positively correlated recognition rule (NQ vs ES)
- He rejects classifying a lagging index ('sick sister theory') as a bullish SMT divergence when the stronger sister already swept its inefficiency and the lagging sister is still drawing down into its own inefficiency.
  > "NASDAQ just entered it today what does that mean to me I don't see that as an smt Divergence that's bullish"
  `[U3K3-235]` · `ICT-Mentorship-2023-September-27-2023-PM-Session-Market-Review-001.json` (E5_2023_2024) · window `W0305` · `added_words: ['sick, classifying, drawing, index, lagging, rejects, still, stronger, swept, theory']` · note: REJECTION of false SMT vs 'sick sister theory'
- He rejects forcing or squinting to find minor daily cracks in correlation; if an SMT divergence is not immediately obvious, he assumes it is not there.
  > "don't strain your eye looking for them what do I mean by that when it's not obvious assume it's not there"
  `[U3K3-236]` · `ICT-Mentorship-Core-Content-Month-10-Index-Futures-AM-Trend-001.json` (E3_2017) · window `W0313` · `added_words: [assumes, cracks, daily, forcing, immediately, minor, rejects, squinting]` · note: REJECTION of non-obvious minor SMT cracks

## (c) OBSERVABLES — ENGINEERING_HYPOTHESIS (needs owner approval)
- at a synchronized swing timestamp across two positively correlated instruments (e.g., ES vs NQ vs YM, EURUSD vs GBPUSD, ZB vs ZN vs ZF), one instrument prints a lower low (or higher high) while the peer prints a higher low (or lower high); for inversely correlated pairs (DXY vs EURUSD/GBPUSD, ZB vs DXY), one fails to print the opposing extreme when the other makes a new extreme
  `candle_observable: true` · derived from `U3K3-233`, `U3K3-232`, `U3K3-238`, `U3K3-239`, `U3K3-240`, `U3K3-234` · **ENGINEERING_HYPOTHESIS — needs owner approval**
- distinguishing a genuine bullish SMT divergence from 'sick sister' delayed drawdown into an unreached inefficiency requires inspecting whether both instruments have already satisfied their respective higher-timeframe draws on liquidity
  `candle_observable: true` · derived from `U3K3-231`, `U3K3-235` · **ENGINEERING_HYPOTHESIS — needs owner approval**

## (d) HOW HE TREATS IT
- Before executing a swing short at a monthly, weekly, or daily premium array on a currency or metal, he confirms the level with Dollar Index SMT divergence.
  > "confirm a monthly weekly daily array entry at resistance with the dollar index strength for smt divergence"
  `[U3K3-237]` · `ICT-Mentorship-Core-Content-Month-06-The-Million-Dollar-Swing-Setup-001.json` (E3_2017) · window `W0303` · `added_words: [executing, level, short, swing]` · note: execution confirmation at HTF PD arrays

## (e) COMPARING INSTANCES
- Unlike a standard breaker setup (low -> high -> lower low), he only trusts buying a failure-swing higher low when it is backed by an SMT divergence in a correlated pair.
  > "it comes off the low and turns with a higher low and starts to trade higher this one here i like to see this form"
  `[U3K3-238]` · `ICT-Forex-Market-Maker-Series-Vol-3-of-5-001.json` (E1_EARLY_SERIES) · window `W0306` · `added_words: [backed, buying, failure, pair, setup, standard, trusts, unlike]` · note: comparative requirement: failure-swing higher low requires SMT divergence, whereas a lower-low breaker stands on its own

## (f) INTERACTIONS
- For a bond mega-trade, the May–June seasonal tendency and higher-timeframe PD array must be qualified by triad SMT divergence across 5-year, 10-year, and 30-year Treasury futures.
  > "that can't be qualified until you see an smt Divergence Across The Five-Year the ten year in the 30-year bond market"
  `[U3K3-239]` · `ICT-Mentorship-Core-Content-Month-11-Bond-Mega-Trades-001.json` (E3_2017) · window `W0308` · `added_words: [array, futures, timeframe, treasury, triad]` · note: interaction with seasonal tendency and Treasury yield-curve triad

## (g) TIMEFRAME
- He applies SMT divergence across macro quarterly horizons (every 3–4 months between bonds and DXY, W0312), weekly/daily swing arrays (W0303), and intraday AM trend sessions (W0313, W0315).
  > "around every three to four months there's going to be this shift that takes this underlying change in trend is seen in the dollar index"
  `[U3K3-240]` · `ICT-Mentorship-Core-Content-Month-03-Macro-Economic-To-Micro-Technical-001.json` (E2_2016) · window `W0312` · `added_words: [applies, arrays, bonds, daily, dxy, horizons, intraday, macro, quarterly, sessions, swing, w0303, w0312, w0313, w0315, weekly]` · note: multi-horizon application from macro quarterly shifts to intraday AM sessions

## (h) FAILURE / INVALIDATION and DISCRETION
- Even when a setup has a short-term high break, a sell-side sweep, and SMT divergence, it can still fail on choppy event days, so traders must accept losing trades without forcing revenge entries.
  > "short-term High taken here we retraced we took sell side out and we have a Divergence smt"
  `[U3K3-241]` · `Price-Action-Chronicles-February-07-2023-003.json` (E5_2023_2024) · window `W0310` · `added_words: [accept, break, choppy, entries, even, event, fail, losing, revenge, setup, still, sweep, traders]` · note: failure of valid SMT setup on choppy days

## (i) VARIANTS (kept parallel, never merged)
- He uses SMT across four asset families: (1) inversely correlated DXY vs foreign currencies (W0301, W0309), (2) positively correlated FX pairs like EURUSD/GBPUSD or AUDUSD/NZDUSD (W0306, W0315), (3) US equity index triad ES/NQ/YM (W0305, W0313), and (4) Treasury triad ZB/ZN/ZF and bonds vs DXY (W0308, W0312).
  > "understanding what smt divergence is and correlated smt divergence understand what that cracking correlation means"
  `[U3K3-242]` · `ICT-Mentorship-Core-Content-Month-02-The-Secrets-To-Selecting-High-Reward-Setups-001.json` (E2_2016) · window `W0307` · `added_words: [asset, audusd, bonds, currencies, dxy, equity, eurusd, families, foreign, four, gbpusd, index, inversely, like, nzdusd, pairs, positively, treasury, triad, uses, w0301, w0305, w0306, w0308, w0309, w0312, w0313, w0315]` · note: four correlated/inversely correlated SMT families

## Windows Logged and Read This Session (`±100` words each)
| Window | Era | Match | Transcript | Word Range | SHA-256 (prefix) |
|---|---|---|---|---|---|
| `W0301` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-Forex-The-ICT-Smart-Money-Technique-or-SMT-001.json` | `2322..2523` (201w) | `2643327a4ae3` |
| `W0302` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-03-Institutional-Market-Structure-001.json` | `109..310` (201w) | `18b779be4dc2` |
| `W0303` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-06-The-Million-Dollar-Swing-Setup-001.json` | `2119..2320` (201w) | `49b7b198b4ff` |
| `W0304` | `E4_2019_2022` | `exact_kept_tsv` | `2022-ICT-Mentorship-Episode-34-001.json` | `0..186` (186w) | `852ecdaca8e6` |
| `W0305` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-Mentorship-2023-September-27-2023-PM-Session-Market-Review-001.json` | `8856..9057` (201w) | `bd17f3702ed9` |
| `W0306` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-Forex-Market-Maker-Series-Vol-3-of-5-001.json` | `626..827` (201w) | `a93d2b59b004` |
| `W0307` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-02-The-Secrets-To-Selecting-High-Reward-Setups-001.json` | `8474..8675` (201w) | `04fe064cf1e5` |
| `W0308` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-11-Bond-Mega-Trades-001.json` | `643..844` (201w) | `14a487e72001` |
| `W0309` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-11-Day-Trading-001.json` | `5380..5581` (201w) | `9e7945f6f83b` |
| `W0310` | `E5_2023_2024` | `exact_kept_tsv` | `Price-Action-Chronicles-February-07-2023-003.json` | `2075..2276` (201w) | `22e4cf9a7f26` |
| `W0311` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-W-E-N-T-Series-4-of-5-003.json` | `2991..3192` (201w) | `5eef84dc272f` |
| `W0312` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-03-Macro-Economic-To-Micro-Technical-001.json` | `1015..1216` (201w) | `bf3d98cb4554` |
| `W0313` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-10-Index-Futures-AM-Trend-001.json` | `2360..2561` (201w) | `e6c51d1eb45e` |
| `W0314` | `E4_2019_2022` | `exact_kept_tsv` | `2022-ICT-Mentorship-Episode-38-001.json` | `8296..8497` (201w) | `e4a7f95e3212` |
| `W0315` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-Mentorship-2023-September-21-2023-Commentary-Livestream-001.json` | `1651..1852` (201w) | `230e9d57d660` |
