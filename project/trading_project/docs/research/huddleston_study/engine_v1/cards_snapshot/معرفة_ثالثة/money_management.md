# Understanding card — money management (`money_management`)

Windows extracted and read in full (`±100` words) this session: **15** (target 15) across **15** distinct transcripts (`E1_EARLY_SERIES`: 4, `E2_2016`: 1, `E3_2017`: 4, `E4_2019_2022`: 3, `E5_2023_2024`: 3). Meets the 15-window budget.
Claims: U3K3-129, U3K3-130, U3K3-131, U3K3-132, U3K3-133, U3K3-134, U3K3-135, U3K3-136, U3K3-137, U3K3-138, U3K3-139, U3K3-140

Every quoted line below is verbatim (≤25 words) from a `±100`-word window logged and read in full this session. Per Rule 2, `statement` in `claims.jsonl` carries the verbatim quote, `reading` carries the interpretation below, and `added_words` lists every word in `reading` absent from the window. Section (c) is explicitly an `ENGINEERING_HYPOTHESIS`, not his words. Empty sections read `NOT_IN_SOURCES`.

## (a) PURPOSE
- He states that proper money management—not pattern selection or a high strike rate—is what makes profitable traders profitable.
  > "the money management is what made most people profitable not the actual trading"
  `[U3K3-129]` · `February-15-2023-ES-Session-Review-002.json` (E5_2023_2024) · window `W0178` · `added_words: [high, makes, selection, states]` · note: core purpose statement on profitability vs strike rate

## (b) RECOGNITION (his criteria and his rejections)
- He identifies money management by how a trader respects account equity and handles drawdown when losses mount.
  > "the first hurdle you're going to have when you're trading with live money is money management you're going to have to learn to respect"
  `[U3K3-130]` · `Real-Money-Real-Results-First-Year-Trading-Expectations-Part-3-of-3-001.json` (E1_EARLY_SERIES) · window `W0175` · `added_words: [handles, identifies, mount, respects]` · note: drawdown handling as the test of money management
- He rejects taking an additional valid trade setup if existing open trades already consume the permitted percentage risk allocation.
  > "we cannot assume more risk than a specific percentage just because the trades there doesn't mean we break our money management rules"
  `[U3K3-131]` · `ICT-Mentorship-Core-Content-Month-06-Elements-To-Successful-Swing-Trading-001.json` (E3_2017) · window `W0168` · `added_words: [additional, consume, permitted, rejects, taking]` · note: REJECTION of exceeding total portfolio risk cap for a new setup
- He explicitly rejects William O'Neil's 8%-per-stock risk figure as nonsense.
  > "William J Neal talks about risking up to eight percent for each stock well that's nonsense you don't need to do that either"
  `[U3K3-132]` · `ICT-Mentorship-Core-Content-Month-10-Stock-Trading-Using-Options-001.json` (E3_2017) · window `W0176` · `added_words: [explicitly, figure, o'neil's, per, rejects, risk]` · note: REJECTION of 8% risk per trade

## (c) OBSERVABLES — ENGINEERING_HYPOTHESIS (needs owner approval)
- Sense 1 (account sizing & risk control): capping total open portfolio risk at a fixed percentage of equity and rejecting new entries when existing open trades already fill that cap unless an existing trade is replaced by a higher-payout candidate
  `candle_observable: false` · derived from `U3K3-131`, `U3K3-135`, `U3K3-133`, `U3K3-130`, `U3K3-136` · **ENGINEERING_HYPOTHESIS — needs owner approval**
- Sense 2 (institutional money movement, W0167): divergence across 30-year bond, 10-year note, and 5-year note futures highs/lows (interest-rate triad SMT)
  `candle_observable: true` · derived from `U3K3-140` · **ENGINEERING_HYPOTHESIS — needs owner approval**

## (d) HOW HE TREATS IT
- He applies a fixed percentage risk rate that grows in dollar terms as equity compounds but never increases as a percentage of equity.
  > "your risk isn't any larger percentage-wise it's a fixed rate of percentage risk that increases monetarily but never percentage-wise"
  `[U3K3-133]` · `Price-Action-Chronicles-February-07-2023-002.json` (E5_2023_2024) · window `W0170` · `added_words: [applies, dollar, grows, terms]` · note: fixed percentage risk compounding rule
- When journaling money management or leveraging errors, he forbids using self-deprecating negative language so the subconscious does not associate charts with stress.
  > "where ever you struggled in the execution or the application of money management or your leveraging or if you ever traded"
  `[U3K3-134]` · `ICT-Forex-Trade-Psychology-&-Effective-Journaling-001.json` (E1_EARLY_SERIES) · window `W0171` · `added_words: [associate, deprecating, forbids, journaling, language, self, using]` · note: journaling discipline for money management errors

## (e) COMPARING INSTANCES
- When at maximum risk allocation, a new setup is compared against open positions by whether it is more valid or offers a better potential payout.
  > "weigh out whether or not that new trade is more valid than the ones that we have existing or if it's a better potential payer"
  `[U3K3-135]` · `ICT-Mentorship-Core-Content-Month-06-Elements-To-Successful-Swing-Trading-001.json` (E3_2017) · window `W0168` · `added_words: [against, compared, maximum, offers, positions]` · note: comparative portfolio allocation rule
- Between two forms of drawdown, he ranks gradual equity erosion as less damaging to a new trader than a sharp, sudden drawdown from overleveraging.
  > "the gradual erosion of equity over time while very uncomfortable it's better"
  `[U3K3-136]` · `Real-Money-Real-Results-First-Year-Trading-Expectations-Part-3-of-3-001.json` (E1_EARLY_SERIES) · window `W0175` · `added_words: [damaging, forms, overleveraging, ranks, two]` · note: comparative: gradual drawdown vs sharp sudden drawdown

## (f) INTERACTIONS
- Money management is coupled directly with the daily bias, the optimal trade entry level, and the predetermined target.
  > "knowing where your target is where your entry is and how to use that in terms of your money management"
  `[U3K3-137]` · `Getting-Started-In-ICT-Scalping-Concepts-001.json` (E5_2023_2024) · window `W0174` · `added_words: [coupled, directly, level, predetermined]` · note: integration with entry and target selection

## (g) TIMEFRAME
- On higher timeframes (long-term position trading), money management entails low trade frequency and slow compounding rather than rapid parlaying.
  > "yes you're managing money no it's not going to be a whole lot of trades it's not going to allow you to parlay"
  `[U3K3-138]` · `ICT-Mentorship-Core-Content-Month-05-Money-Management-001.json` (E3_2017) · window `W0172` · `added_words: [compounding, entails, frequency, higher, low, parlaying, rapid, rather, slow, timeframes]` · note: timeframe impact on trade frequency and compounding speed

## (h) FAILURE / INVALIDATION and DISCRETION
- He warns that aggressive compounding is a double-edged sword that can take an account down just as fast if a trader rushes profits by increasing trade frequency.
  > "you discover the power of compound interest but you don't at that time understand the depths that it can take you down with"
  `[U3K3-139]` · `If-I-Could-Go-Back-&-Tell-Myself-What-I-Know-Now-Part-4-of-4-001.json` (E1_EARLY_SERIES) · window `W0166` · `added_words: [account, aggressive, compounding, fast, increasing, rushes, trader, warns]` · note: failure mode: rushing profits and overtrading with compound sizing

## (i) VARIANTS (kept parallel, never merged)
- In macro lectures he also uses 'money management' to mean institutional capital rotation tracked via 30-year, 10-year, and 5-year interest-rate futures triads.
  > "technical analysis and key interest rates can unlock professional money management movement"
  `[U3K3-140]` · `ICT-Mentorship-Core-Content-Month-04-Interest-Rate-Effects-On-Currency-Trades-001.json` (E2_2016) · window `W0167` · `added_words: ['money, capital, institutional, lectures, macro, management', mean, rotation, tracked, uses, via]` · note: K2 seed window verified: parallel macro sense (institutional capital movement) vs trader account sizing (W0168/W0170)

## Windows Logged and Read This Session (`±100` words each)
| Window | Era | Match | Transcript | Word Range | SHA-256 (prefix) |
|---|---|---|---|---|---|
| `W0166` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `If-I-Could-Go-Back-&-Tell-Myself-What-I-Know-Now-Part-4-of-4-001.json` | `1021..1222` (201w) | `df98d1c4db6c` |
| `W0167` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-04-Interest-Rate-Effects-On-Currency-Trades-001.json` | `0..170` (170w) | `c794286a1e56` |
| `W0168` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-06-Elements-To-Successful-Swing-Trading-001.json` | `1705..1906` (201w) | `60258117ddbb` |
| `W0169` | `E4_2019_2022` | `exact_kept_tsv` | `2022-ICT-Mentorship-Episode-24-001.json` | `6602..6803` (201w) | `4dbf850b169a` |
| `W0170` | `E5_2023_2024` | `exact_kept_tsv` | `Price-Action-Chronicles-February-07-2023-002.json` | `955..1156` (201w) | `472c4eb2e14c` |
| `W0171` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-Forex-Trade-Psychology-&-Effective-Journaling-001.json` | `7160..7361` (201w) | `4afc17198548` |
| `W0172` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-05-Money-Management-001.json` | `3760..3961` (201w) | `d759090429a2` |
| `W0173` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-5-Supplementary-Lesson-001.json` | `6171..6372` (201w) | `3206373db8b3` |
| `W0174` | `E5_2023_2024` | `exact_kept_tsv` | `Getting-Started-In-ICT-Scalping-Concepts-001.json` | `6528..6729` (201w) | `cb4f7c3b9bd3` |
| `W0175` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `Real-Money-Real-Results-First-Year-Trading-Expectations-Part-3-of-3-001.json` | `1470..1671` (201w) | `c5ad56bbffd7` |
| `W0176` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-10-Stock-Trading-Using-Options-001.json` | `4726..4927` (201w) | `5af71ebc6be3` |
| `W0177` | `E4_2019_2022` | `exact_kept_tsv` | `2022-ICT-Mentorship-Ends-Series-Part-2-of-4-002.json` | `0..173` (173w) | `8eadf84b9809` |
| `W0178` | `E5_2023_2024` | `exact_kept_tsv` | `February-15-2023-ES-Session-Review-002.json` | `614..815` (201w) | `206e4fe603f6` |
| `W0179` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `NQ-Live-Execution-&-Commentary-Final-Trading-Day-Of-2023-001.json` | `5791..5992` (201w) | `0e24f7f16b11` |
| `W0180` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-05-Defining-HTF-PD-Arrays-001.json` | `1690..1891` (201w) | `60393f36f9d7` |
