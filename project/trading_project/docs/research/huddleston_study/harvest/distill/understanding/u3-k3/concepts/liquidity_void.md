# Understanding card — liquidity void (`liquidity_void`)

Windows extracted and read in full (`±100` words) this session: **15** (target 15) across **15** distinct transcripts (`E2_2016`: 5, `E3_2017`: 4, `E4_2019_2022`: 3, `E5_2023_2024`: 3). Meets the 15-window budget.
Claims: U3K3-083, U3K3-084, U3K3-085, U3K3-086, U3K3-087, U3K3-088, U3K3-089, U3K3-090, U3K3-091, U3K3-092, U3K3-093, U3K3-094

Every quoted line below is verbatim (≤25 words) from a `±100`-word window logged and read in full this session. Per Rule 2, `statement` in `claims.jsonl` carries the verbatim quote, `reading` carries the interpretation below, and `added_words` lists every word in `reading` absent from the window. Section (c) is explicitly an `ENGINEERING_HYPOTHESIS`, not his words. Empty sections read `NOT_IN_SOURCES`.

## (a) PURPOSE
- Because a downward liquidity void reflects a lack of buy-side liquidity during an aggressive drop, price is expected to return and fill the void.
  > "the nature of a liquidity void is that we'll probably see with a great deal probability I'll move back up into that 104.76 level"
  `[U3K3-083]` · `ICT-Mentorship-Core-Content-Month-04-Liquidity-Voids-001.json` (E2_2016) · window `W0111` · `added_words: [aggressive, expected, lack, reflects, return]` · note: purpose/expectation of return to fill the void

## (b) RECOGNITION (his criteria and his rejections)
- In early lectures he recognizes a liquidity void when price drops so aggressively with large candles that price levels are skipped.
  > "as the market drops aggressively like that there's going to be pockets where the price wasn't actually delivered on every um available price level"
  `[U3K3-084]` · `ICT-Mentorship-Core-Content-Month-1-Elements-Of-A-Trade-Setup-001.json` (E2_2016) · window `W0106` · `added_words: [candles, early, large, lectures, levels, recognizes]` · note: K2 seed window deepened
- Visually, he identifies that displacement form of liquidity void as sudden movement with large candle ranges and very small wicks.
  > "this is what we call a liquidity void where the market makes a a sudden movement lower and large ranges very little wicks"
  `[U3K3-085]` · `ICT-Mentorship-Core-Content-Month-1-Fair-Valuation-001.json` (E2_2016) · window `W0115` · `added_words: [displacement, form, identifies, small, visually]` · note: candle recognition: large ranges, very little wicks
- In 2023 he explicitly rejects calling a fair value gap a liquidity void because a fair value gap still had liquidity offered on overlapping candles.
  > "this is a fair value Gap that's not a liquidity void by the way because it did have liquidity offered on both sides"
  `[U3K3-086]` · `ICT-Mentorship-2023-October-04-2023-Market-Commentary-&-Review-001.json` (E5_2023_2024) · window `W0110` · `added_words: [2023, calling, candles, explicitly, overlapping, rejects, still]` · note: REJECTION: distinguishes fair value gap from a true liquidity void

## (c) OBSERVABLES — ENGINEERING_HYPOTHESIS (needs owner approval)
- Definition A (2016–2019 lectures): a multi-candle or single-candle displacement span with large candle bodies and minimal wicks relative to adjacent consolidation bars, creating a one-sided range that subsequent price retraces into
  `candle_observable: true` · derived from `U3K3-084`, `U3K3-087`, `U3K3-083`, `U3K3-085` · **ENGINEERING_HYPOTHESIS — needs owner approval**
- Definition B (2023 lectures, kept parallel and never merged with Definition A): a literal price gap between two closes/opens (e.g. Friday close to Sunday open) containing zero printed ticks or wicks, explicitly distinguished from a three-candle fair value gap
  `candle_observable: true` · derived from `U3K3-086`, `U3K3-093` · **ENGINEERING_HYPOTHESIS — needs owner approval**

## (d) HOW HE TREATS IT
- Rather than chasing an aggressive drop, he waits either to trade the retracement filling the liquidity void or to short once the void is filled.
  > "we won't chase price we'll wait and say okay well there's going to be either an indication of getting long and try to fill"
  `[U3K3-087]` · `ICT-Mentorship-Core-Content-Month-1-Elements-Of-A-Trade-Setup-001.json` (E2_2016) · window `W0106` · `added_words: [aggressive, chasing, drop, filled, filling, rather, retracement, short, trade, waits]` · note: two-way treatment: trade into the void or resume trend after fill
- He classifies a liquidity void being filled in as an internal range entry (paired with external range liquidity exits) or vice versa.
  > "so if we look for internal range entries it's fair gaps liquidity void being filled in or order blocks"
  `[U3K3-088]` · `ICT-Charter-Price-Action-Model-9-One-Shot-One-Kill-001.json` (E4_2019_2022) · window `W0109` · `added_words: [classifies, entry, paired, versa, vice]` · note: internal vs external range role

## (e) COMPARING INSTANCES
- Between an order block, fair value gap, or liquidity void consequent encroachment, he states no fixed rule ranks one PD array over another in advance.
  > "one PD is going to make more sense to you relative to the the present Market condition and Market structure I cannot predict"
  `[U3K3-089]` · `ICT-Charter-Price-Action-Model-11-Day-Trading-001.json` (E4_2019_2022) · window `W0113` · `added_words: [advance, encroachment, fixed, ranks, rule, states]` · note: explicit refusal of a static cookie-cutter ranking across all situations

## (f) INTERACTIONS
- London shorts are ideal when the daily chart is poised to trade lower from a premium array to close a liquidity void or fair value gap in discount.
  > "that means a bullish order block closing a fair value got the below market price closing a liquidity void below market price"
  `[U3K3-090]` · `ICT-Mentorship-Core-Content-Month-08-When-To-Avoid-The-London-Session-001.json` (E3_2017) · window `W0116` · `added_words: [chart, close, gap]` · note: interaction between daily liquidity void target and London session shorts

## (g) TIMEFRAME
- He maps liquidity voids as upside/downside objectives across monthly, weekly, daily (W0116), and 5-minute charts (W0119).
  > "we're seeing that on the monthly chart for silver and on the weekly chart we saw our levels react"
  `[U3K3-091]` · `ICT-Mentorship-Core-Content-Month-06-High-Probability-Swing-Trade-Setups-In-Bull-Markets-001.json` (E3_2017) · window `W0108` · `added_words: [charts, daily, downside, maps, minute, objectives, upside, voids, w0116, w0119]` · note: multi-timeframe application from monthly/weekly down to 5-minute

## (h) FAILURE / INVALIDATION and DISCRETION
- A liquidity void may not fill on the first pass; price can drive lower again before returning to close the void.
  > "a liquidity void that didn't initially fill in the first pass lower and then dries lower then closes it in"
  `[U3K3-092]` · `ICT-Mentorship-Core-Content-Month-05-Defining-Institutional-Swing-Points-001.json` (E3_2017) · window `W0120` · `added_words: [close, returning]` · note: delayed fill behavior

## (i) VARIANTS (kept parallel, never merged)
- In 2023 he defines a 'real liquidity void' strictly as an opening gap (such as Friday close to Sunday open, NWOG) with zero printed price data, contrasting with the 2016 large-bodied candle definition (W0115).
  > "now a real liquidity void is an absence of any buying and selling there's no printed data between two specific price points"
  `[U3K3-093]` · `NWOG-New-Week-Opening-Gap-001.json` (E5_2023_2024) · window `W0118` · `added_words: ['real, 2016, 2023, bodied, candle, contrasting, defines, definition, large, nwog, open, strictly, sunday, void', w0115, zero]` · note: parallel variant kept separate: 2016 large-candle displacement void (W0111/W0115) vs 2023 zero-printed-data gap (W0110/W0118)
- He notes that he adopted the phrase 'liquidity void' on BabyPips as shorthand before introducing his own BISI/SIBI terminology.
  > "I did not learn liquidity void from Mr Chris Laurie I just used that term when I was on baby Pips"
  `[U3K3-094]` · `Deep-Learning-On-Nasdaq-Futures-Trade-January-04-2023-001.json` (E5_2023_2024) · window `W0114` · `added_words: ['liquidity, adopted, babypips, bisi, introducing, notes, phrase, shorthand, sibi, terminology, void']` · note: terminological provenance variant

## Windows Logged and Read This Session (`±100` words each)
| Window | Era | Match | Transcript | Word Range | SHA-256 (prefix) |
|---|---|---|---|---|---|
| `W0106` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-1-Elements-Of-A-Trade-Setup-001.json` | `2245..2446` (201w) | `17b293605788` |
| `W0107` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-03-Institutional-Sponsorship-001.json` | `1495..1696` (201w) | `38dd52ef429a` |
| `W0108` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-06-High-Probability-Swing-Trade-Setups-In-Bull-Markets-001.json` | `4185..4386` (201w) | `b2c2e7f91e1b` |
| `W0109` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-9-One-Shot-One-Kill-001.json` | `2165..2366` (201w) | `01faa385c57e` |
| `W0110` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-Mentorship-2023-October-04-2023-Market-Commentary-&-Review-001.json` | `8963..9164` (201w) | `50edfade7d0d` |
| `W0111` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-04-Liquidity-Voids-001.json` | `571..772` (201w) | `6572ff70d339` |
| `W0112` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-10-Relative-Strength-Analysis-Accumulation-&-Distribution-001.json` | `3249..3450` (201w) | `21f06c0a2d01` |
| `W0113` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-11-Day-Trading-001.json` | `1783..1984` (201w) | `9e7945f6f83b` |
| `W0114` | `E5_2023_2024` | `exact_kept_tsv` | `Deep-Learning-On-Nasdaq-Futures-Trade-January-04-2023-001.json` | `5245..5446` (201w) | `d50f31b90663` |
| `W0115` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-1-Fair-Valuation-001.json` | `259..460` (201w) | `7a2e72f79d24` |
| `W0116` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-08-When-To-Avoid-The-London-Session-001.json` | `3795..3996` (201w) | `81cc5e41e6a4` |
| `W0117` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-10-Swing-Trading-001.json` | `427..628` (201w) | `32af78246341` |
| `W0118` | `E5_2023_2024` | `exact_kept_tsv` | `NWOG-New-Week-Opening-Gap-001.json` | `354..555` (201w) | `e8f948ee4602` |
| `W0119` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-02-Market-Maker-Trap-False-Flag-001.json` | `2138..2339` (201w) | `558d360fb897` |
| `W0120` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-05-Defining-Institutional-Swing-Points-001.json` | `1234..1435` (201w) | `46b799145b2f` |
