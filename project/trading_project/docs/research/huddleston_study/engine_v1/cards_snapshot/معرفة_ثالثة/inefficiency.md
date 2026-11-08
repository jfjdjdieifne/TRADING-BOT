# Understanding card — inefficiency (`inefficiency`)

Windows extracted and read in full (`±100` words) this session: **15** (target 15) across **15** distinct transcripts (`E1_EARLY_SERIES`: 4, `E2_2016`: 1, `E4_2019_2022`: 5, `E5_2023_2024`: 5). Meets the 15-window budget.
Claims: U3K3-049, U3K3-050, U3K3-051, U3K3-052, U3K3-053, U3K3-054, U3K3-055, U3K3-056, U3K3-057, U3K3-058, U3K3-059

Every quoted line below is verbatim (≤25 words) from a `±100`-word window logged and read in full this session. Per Rule 2, `statement` in `claims.jsonl` carries the verbatim quote, `reading` carries the interpretation below, and `added_words` lists every word in `reading` absent from the window. Section (c) is explicitly an `ENGINEERING_HYPOTHESIS`, not his words. Empty sections read `NOT_IN_SOURCES`.

## (a) PURPOSE
- He reduces all algorithmic price delivery to two targets: running liquidity pools at old highs/lows or returning to rebalance an inefficiency.
  > "either buy side liquidity above old highs or it runs sell side liquidity below old lows or it runs to an area of inefficiency"
  `[U3K3-049]` · `ICT-Institutional-Price-Action-Micro-Market-Structure-&-Time-&-Price-Concepts-Part-02-001.json` (E1_EARLY_SERIES) · window `W0065` · `added_words: [algorithmic, pools, reduces, returning, targets]` · note: foundational two-outcome purpose statement

## (b) RECOGNITION (his criteria and his rejections)
- He recognizes inefficiency as one-sided price delivery where candles move in only one direction without opposing movement.
  > "when we see inefficiency in price like we see here with these candles just only going down no up movement only going down"
  `[U3K3-050]` · `ICT-Mentorship-Core-Content-Month-1-Fair-Valuation-001.json` (E2_2016) · window `W0062` · `added_words: [delivery, direction, one, opposing, recognizes, sided]` · note: visual recognition criterion: one-directional candle delivery
- A sell-side imbalance buy-side inefficiency (SIBI) means too much selling occurred in that range without enough buying offered.
  > "there has been too much selling in here so it's a sell side imbalance buys side inefficiency too much selling not enough buying offered"
  `[U3K3-051]` · `ICT-Charter-Price-Action-Model-8-Targeting-6%-Per-Month-001.json` (E4_2019_2022) · window `W0069` · `added_words: [buy, means, occurred, range, sibi]` · note: definition of SIBI inefficiency; optimal trade entry requires an inefficiency/FVG inside the fib zone
- When bounding a SIBI inefficiency, he rejects using the prior swing high if the breakdown candle wicked up first, starting from where buy-side stopped being offered.
  > "do we look at that high to this low for a Cy no we look at this candle's High because it opens"
  `[U3K3-052]` · `ICT-Charter-Price-Action-Model-11-Day-Trading-001.json` (E4_2019_2022) · window `W0074` · `added_words: [bounding, breakdown, first, rejects, sibi, starting, stopped, wicked]` · note: REJECTION of wrong boundary when marking an inefficiency; [sic-asr] 'Cy' for 'SIBI'

## (c) OBSERVABLES — ENGINEERING_HYPOTHESIS (needs owner approval)
- a single-sided price span (BISI on an up-move or SIBI on a down-move) bounded by the exact price where opposing delivery ceased on the flanking candles, leaving an unoverlapped range
  `candle_observable: true` · derived from `U3K3-050`, `U3K3-059`, `U3K3-051`, `U3K3-056`, `U3K3-052` · **ENGINEERING_HYPOTHESIS — needs owner approval**
- in the strongest continuation moves, retracements into the inefficiency halt at or before the 50% midpoint (consequent encroachment) without trading into the far boundary of the inefficiency
  `candle_observable: true` · derived from `U3K3-051`, `U3K3-056`, `U3K3-055` · **ENGINEERING_HYPOTHESIS — needs owner approval**

## (d) HOW HE TREATS IT
- Once a fresh inefficiency forms during a break lower, he expects price to retrace back into that inefficiency before digging deeper.
  > "if there's an inefficiency just formed I'm expecting it to reach back up into that like it's doing here here and then digging Down Deeper"
  `[U3K3-053]` · `ICT-Mentorship-2023-Immediate-Rebalance-&-Institutional-Order-Flow-002.json` (E5_2023_2024) · window `W0064` · `added_words: [break, expects, forms, fresh, once, price, retrace]` · note: retracement expectation into newly formed inefficiency
- He strictly forbids trailing a stop loss inside or right at an inefficiency/fair value gap after a market structure shift because price gravitates back to rebalance it.
  > "we have a shift in Market structure here never put your stop loss in or at a fair bag Gap after a shift"
  `[U3K3-054]` · `ICT-Mentorship-2023-August-18-2023-Live-trade-Walkthrough-001.json` (E5_2023_2024) · window `W0073` · `added_words: [forbids, gravitates, rebalance, right, strictly, trailing, value]` · note: REJECTION / stop-placement rule: 'never put your stop loss in or at a fair bag Gap'

## (e) COMPARING INSTANCES
- In a bearish model, the strongest runners respect the midpoint (consequent encroachment) and never retrade the upper extreme of the inefficiency.
  > "we don't want to see the high end of any inefficiency be retraded to if we're bearish if the market is really in fact"
  `[U3K3-055]` · `Thursday-June-15-2023-ICT-Price-Action-Workshop-002.json` (E5_2023_2024) · window `W0075` · `added_words: [never, respect, retrade]` · note: comparative: 'the best ones the strongest delivering obvious Runners' leave the upper portion untraded

## (f) INTERACTIONS
- An optimal trade entry fibonacci zone will not work by itself unless it contains an inefficiency/fair value gap drawing price back to it.
  > "the opal trade entry by default is always going to be in the ideal premium or ideal discount level but it doesn't work"
  `[U3K3-056]` · `ICT-Charter-Price-Action-Model-8-Targeting-6%-Per-Month-001.json` (E4_2019_2022) · window `W0069` · `added_words: [contains, drawing, fibonacci, itself, optimal, zone]` · note: interaction: OTE requires an internal inefficiency/FVG; [sic-asr] 'opal trade entry'

## (g) TIMEFRAME
- He tracks micro inefficiencies down to a 10-second chart, while noting a 1-minute chart is sufficient for standard Silver Bullet setups.
  > "all this congestion in here that's being shown on a 10 second chart all through here but this level of detail you can't glean"
  `[U3K3-057]` · `ICT-Mentorship-2023-Immediate-Rebalance-&-Institutional-Order-Flow-002.json` (E5_2023_2024) · window `W0064` · `added_words: [inefficiencies, micro, noting, setups, standard, sufficient, tracks]` · note: sub-minute (10s) vs 1-minute timeframe comparison

## (h) FAILURE / INVALIDATION and DISCRETION
- He treats a small local inefficiency as a line in the sand: if price fails to rally from it, price is likely to drop deeper into the 4-hour fair value gap.
  > "there's a little inefficiency here so in a way it's kind of like a breaker kind of like a um a reason for it needs"
  `[U3K3-058]` · `December-2023-Non-Farm-Payroll-Live-Execution-&-Explanations-001.json` (E1_EARLY_SERIES) · window `W0068` · `added_words: [drop, fails, local, price, rally, small, treats]` · note: failure of minor inefficiency leads to deeper retracement to HTF FVG

## (i) VARIANTS (kept parallel, never merged)
- He distinguishes directional variants: Buy-Side Imbalance Sell-Side Inefficiency (BISI, missing sell-side) vs Sell-Side Imbalance Buy-Side Inefficiency (SIBI, missing buy-side, W0069).
  > "repriced close in this fair value gap here to the buy side imbalance sell side inefficiency what was missing in this range"
  `[U3K3-059]` · `ICT-Emini-S&P500-AM-&-PM-Session-Review-09-01-22-001.json` (E4_2019_2022) · window `W0066` · `added_words: [bisi, directional, distinguishes, sibi, variants, w0069]` · note: parallel directional variants: BISI vs SIBI

## Windows Logged and Read This Session (`±100` words each)
| Window | Era | Match | Transcript | Word Range | SHA-256 (prefix) |
|---|---|---|---|---|---|
| `W0061` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `NQ-Live-Execution-&-Commentary-Final-Trading-Day-Of-2023-002.json` | `31..232` (201w) | `14d24591945c` |
| `W0062` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-1-Fair-Valuation-001.json` | `2632..2833` (201w) | `7a2e72f79d24` |
| `W0063` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-9-One-Shot-One-Kill-001.json` | `1122..1323` (201w) | `01faa385c57e` |
| `W0064` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-Mentorship-2023-Immediate-Rebalance-&-Institutional-Order-Flow-002.json` | `3977..4178` (201w) | `457c66642aa6` |
| `W0065` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-Institutional-Price-Action-Micro-Market-Structure-&-Time-&-Price-Concepts-Part-02-001.json` | `877..1078` (201w) | `ce0961b396b1` |
| `W0066` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Emini-S&P500-AM-&-PM-Session-Review-09-01-22-001.json` | `69..270` (201w) | `8d62aebd9f30` |
| `W0067` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-Forex-Review-January-09-2023-001.json` | `107..308` (201w) | `c224abc24ad3` |
| `W0068` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `December-2023-Non-Farm-Payroll-Live-Execution-&-Explanations-001.json` | `4751..4952` (201w) | `a87428327996` |
| `W0069` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-8-Targeting-6%-Per-Month-001.json` | `7108..7309` (201w) | `f4e96835c500` |
| `W0070` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-Mentorship-2023-September-12-2023-NQ-Algorithmic-Price-Delivery-001.json` | `7824..8025` (201w) | `27a2a4eda981` |
| `W0071` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `NQ-Live-Execution-&-Commentary-Final-Trading-Day-Of-2023-001.json` | `10068..10197` (129w) | `0e24f7f16b11` |
| `W0072` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-2-Amplified-Lecture-001.json` | `4814..5015` (201w) | `3fe1d012a146` |
| `W0073` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-Mentorship-2023-August-18-2023-Live-trade-Walkthrough-001.json` | `3125..3326` (201w) | `430e7bc296e1` |
| `W0074` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-11-Day-Trading-001.json` | `5856..6057` (201w) | `9e7945f6f83b` |
| `W0075` | `E5_2023_2024` | `exact_kept_tsv` | `Thursday-June-15-2023-ICT-Price-Action-Workshop-002.json` | `9076..9277` (201w) | `6bc9db6bf768` |
