# Understanding card — premium (`premium`)

Windows extracted and read in full (`±100` words) this session: **15** (target 15) across **15** distinct transcripts (`E1_EARLY_SERIES`: 3, `E2_2016`: 3, `E3_2017`: 3, `E4_2019_2022`: 3, `E5_2023_2024`: 3). Meets the 15-window budget.
Claims: U3K3-187, U3K3-188, U3K3-189, U3K3-190, U3K3-191, U3K3-192, U3K3-193, U3K3-194, U3K3-195, U3K3-196, U3K3-197

Every quoted line below is verbatim (≤25 words) from a `±100`-word window logged and read in full this session. Per Rule 2, `statement` in `claims.jsonl` carries the verbatim quote, `reading` carries the interpretation below, and `added_words` lists every word in `reading` absent from the window. Section (c) is explicitly an `ENGINEERING_HYPOTHESIS`, not his words. Empty sections read `NOT_IN_SOURCES`.

## (a) PURPOSE
- In bearish conditions, the algorithm reprices higher into a premium array so smart money can distribute or redistribute short positions at premium prices.
  > "ifta Will reprice the Market higher to a fair value price array to provide smart money premium pricing for short entries"
  `[U3K3-187]` · `ICT-Mentorship-Core-Content-Month-09-Bread-&-Butter-Sell-Setups-001.json` (E3_2017) · window `W0243` · `added_words: [algorithm, distribute, positions, reprices]` · note: algorithmic purpose of repricing into a premium; [sic-asr] 'ifta' for 'IPDA'
- He views a rally into a premium during a sell program not as genuine buying pressure, but as manipulation to give smart money better prices to short into.
  > "the market is manipulated higher to allow for even more premium to short into for smart money it's not buying pressure"
  `[U3K3-188]` · `ICT-Emini-S&P-500-AM-&-PM-Session-Review-09-02-22-001.json` (E4_2019_2022) · window `W0249` · `added_words: [better, genuine, give, prices, rally, sell, views]` · note: manipulation into premium in AMD sell program

## (b) RECOGNITION (his criteria and his rejections)
- He defines premium relative to a specific dealing range high and low, with 50% (equilibrium) dividing premium above from discount below.
  > "the dealing range high in the dealing range low here that's the range that you're looking for to look at the relationship between premium"
  `[U3K3-189]` · `The-Inner-Circle-Trader-Live-Test-Stream-001.json` (E5_2023_2024) · window `W0250` · `added_words: [defines, dividing, relative, specific]` · note: recognition of premium above 50% of the active dealing range
- After price has already completed three downward stages running successive lows, he rejects shorting the next retracement into a premium fair value gap.
  > "not that it can't go up here and treat that as a sell-time balance Boston efficiency or a premium fair value got to go short"
  `[U3K3-190]` · `April-13-2023-Live-Tape-Reading-Emini-S&P-AM-Session-002.json` (E5_2023_2024) · window `W0245` · `added_words: [completed, downward, gap, lows, next, price, rejects, retracement, running, shorting, successive]` · note: REJECTION of shorting a premium FVG after three completed downward stages

## (c) OBSERVABLES — ENGINEERING_HYPOTHESIS (needs owner approval)
- Sense 1 (dealing-range valuation): any price above the 50% midpoint (equilibrium) between the active dealing-range low and high (or above the session/daily opening price), used as the zone for short entries and long profit-taking
  `candle_observable: true` · derived from `U3K3-187`, `U3K3-189`, `U3K3-192`, `U3K3-193`, `U3K3-191` · **ENGINEERING_HYPOTHESIS — needs owner approval**
- Sense 2 (futures term structure, W0241): front-month contract price exceeding the next deferred contract month price (backwardation), which requires multi-contract term-structure data
  `candle_observable: false` · derived from `U3K3-197` · **ENGINEERING_HYPOTHESIS — needs owner approval**

## (d) HOW HE TREATS IT
- When long from a discount, he targets a fair value gap located above equilibrium in the premium half of the range.
  > "there is a fair value gap at the 680 level and it's above equilibrium so it would be a premium market"
  `[U3K3-191]` · `2022-ICT-Mentorship-Episode-15-001.json` (E4_2019_2022) · window `W0254` · `added_words: [discount, half, located, long, range, targets]` · note: using a premium array above equilibrium as a long profit target
- When holding a multi-timeframe long, he scales partial profits sequentially as price reaches 4-hour, daily, and weekly premium arrays.
  > "you're going to take something off at the premium arrays on the four hour chart and at the daily chart and at the weekly chart"
  `[U3K3-192]` · `ICT-Mentorship-Core-Content-Month-06-Classic-Swing-Trading-Approach-001.json` (E3_2017) · window `W0253` · `added_words: [holding, long, multi, partial, price, reaches, scales, sequentially, timeframe]` · note: multi-timeframe partial profit scaling at successive premium arrays

## (e) COMPARING INSTANCES
- He ranks long setups by whether the distance from entry to the closest premium array across all timeframes offers at least a 3-to-1 reward-to-risk range.
  > "we look to trade setups that offer at least three and preferably more times the range between your entry and the closest premium array"
  `[U3K3-193]` · `ICT-Mentorship-Core-Content-Month-06-Classic-Swing-Trading-Approach-001.json` (E3_2017) · window `W0253` · `added_words: [distance, long, offers, ranks, reward, risk, timeframes, whether]` · note: comparative filter: >=3x range to closest premium array

## (f) INTERACTIONS
- When GBPUSD rallies to an old high while the Dollar Index refuses to make a lower low (SMT), premium is being built into GBPUSD to distribute longs into retail breakout buyers.
  > "it's because it can't go lower because of pricing it's being kept while the premium is being built into the pound dollar"
  `[U3K3-194]` · `ICT-Mentorship-Core-Content-Month-03-Institutional-Market-Structure-001.json` (E2_2016) · window `W0252` · `added_words: [distribute, gbpusd, low, make, rallies, refuses, smt]` · note: interaction of premium distribution with Dollar Index SMT divergence

## (g) TIMEFRAME
- He applies premium-versus-equilibrium range trading identically across 15-minute, hourly, 4-hour, daily, weekly, and monthly charts.
  > "don't discount it that i'm teaching you in a 15-minute basis because all the concepts are universal"
  `[U3K3-195]` · `ICT-Mentorship-Core-Content-Month-1-Equilibrium-Vs-Premium-001.json` (E2_2016) · window `W0242` · `added_words: [applies, equilibrium, hour, identically, monthly, range, versus, weekly]` · note: universal cross-timeframe applicability of premium

## (h) FAILURE / INVALIDATION and DISCRETION
- Under heavy institutional accumulation and high demand, an asset can refuse to retrace to a discount, forcing buyers to pay a premium.
  > "it will be forced upon the buyer to pay a premium on it it will not ever it won't ever go to a discount"
  `[U3K3-196]` · `ICT-Mentorship-Core-Content-Month-04-Interest-Rate-Effects-On-Currency-Trades-001.json` (E2_2016) · window `W0247` · `added_words: [buyers, forcing, institutional, refuse, retrace]` · note: exception/failure of discount retracement during runaway institutional demand

## (i) VARIANTS (kept parallel, never merged)
- Alongside his dealing-range sense (above 50% equilibrium, W0250), he also uses 'premium' in commodities/futures for backwardation where the nearby contract trades above the deferred month.
  > "when you have a premium in the futures contracts that means the nearby contract is selling at a higher price than the next month out"
  `[U3K3-197]` · `ICT-Trading-Plan-Development-1-001.json` (E1_EARLY_SERIES) · window `W0241` · `added_words: ['premium', alongside, backwardation, commodities, dealing, deferred, equilibrium, range, sense, trades, uses, w0250]` · note: two distinct senses kept parallel: (1) upper 50% of a dealing range (W0250/W0254) vs (2) futures term-structure backwardation (W0241)

## Windows Logged and Read This Session (`±100` words each)
| Window | Era | Match | Transcript | Word Range | SHA-256 (prefix) |
|---|---|---|---|---|---|
| `W0241` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-Trading-Plan-Development-1-001.json` | `8660..8861` (201w) | `6251cf47513e` |
| `W0242` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-1-Equilibrium-Vs-Premium-001.json` | `3147..3348` (201w) | `d34d757e7339` |
| `W0243` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-09-Bread-&-Butter-Sell-Setups-001.json` | `168..369` (201w) | `7eddfae47861` |
| `W0244` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-1-Amplified-Lecture-001.json` | `5701..5902` (201w) | `44daad67c023` |
| `W0245` | `E5_2023_2024` | `exact_kept_tsv` | `April-13-2023-Live-Tape-Reading-Emini-S&P-AM-Session-002.json` | `1304..1505` (201w) | `7a0e7c95b328` |
| `W0246` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-Forex-Time-&-Price-Theory-001.json` | `0..162` (162w) | `4e2f48cb5422` |
| `W0247` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-04-Interest-Rate-Effects-On-Currency-Trades-001.json` | `632..833` (201w) | `c794286a1e56` |
| `W0248` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-12-Long-Term-Top-Down-Analysis-001.json` | `1754..1955` (201w) | `e7905426fe98` |
| `W0249` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Emini-S&P-500-AM-&-PM-Session-Review-09-02-22-001.json` | `1580..1781` (201w) | `7995d5376cfc` |
| `W0250` | `E5_2023_2024` | `exact_kept_tsv` | `The-Inner-Circle-Trader-Live-Test-Stream-001.json` | `4277..4478` (201w) | `132cee7565a1` |
| `W0251` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `NQ-Live-Execution-&-Commentary-Final-Trading-Day-Of-2023-001.json` | `2986..3187` (201w) | `0e24f7f16b11` |
| `W0252` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-03-Institutional-Market-Structure-001.json` | `1852..2053` (201w) | `18b779be4dc2` |
| `W0253` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-06-Classic-Swing-Trading-Approach-001.json` | `3519..3720` (201w) | `7084446fc55e` |
| `W0254` | `E4_2019_2022` | `exact_kept_tsv` | `2022-ICT-Mentorship-Episode-15-001.json` | `688..889` (201w) | `07fa6fa588f4` |
| `W0255` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-Mentorship-2023-July-23-2023-Market-Review-001.json` | `860..1061` (201w) | `614605d7ae56` |
