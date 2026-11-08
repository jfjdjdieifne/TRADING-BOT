# Understanding card — non farm payroll (`non_farm_payroll`)

**Status: THIN on literal `kept_concepts.tsv` phrase** — The literal unhyphenated phrase 'non farm payroll' in kept_concepts.tsv has exactly 1 hit in 1 file in the corpus (W0181). We mark this concept THIN on the literal unhyphenated phrase as required, and supplement W0181 with 14 era-stratified windows of the hyphenated/compound ASR spellings ('non-farm payroll', 'nonfarm payroll', W0182..W0195) across 14 additional transcripts so all 15 windows are read and verified.
Windows extracted and read in full (`±100` words) this session: **15** (**1** exact phrase + **14** hyphenated/plural ASR variant; target 15) across **15** distinct transcripts (`E1_EARLY_SERIES`: 3, `E2_2016`: 2, `E3_2017`: 3, `E4_2019_2022`: 4, `E5_2023_2024`: 3).
Claims: U3K3-141, U3K3-142, U3K3-143, U3K3-144, U3K3-145, U3K3-146, U3K3-147, U3K3-148, U3K3-149, U3K3-150, U3K3-151, U3K3-152

Every quoted line below is verbatim (≤25 words) from a `±100`-word window logged and read in full this session. Per Rule 2, `statement` in `claims.jsonl` carries the verbatim quote, `reading` carries the interpretation below, and `added_words` lists every word in `reading` absent from the window. Section (c) is explicitly an `ENGINEERING_HYPOTHESIS`, not his words. Empty sections read `NOT_IN_SOURCES`.

## (a) PURPOSE
- He views Non-Farm Payroll (alongside FOMC) as an external volatility catalyst capable of driving price through high-resistance liquidity runs that normal price action avoids.
  > "without the evidence of a significant market driver coming into play with like an fomc interest rate announcement or non-farm payroll"
  `[U3K3-141]` · `ICT-Mentorship-Core-Content-Month-1-Liquidity-Runs-001.json` (E2_2016) · window `W0183` · `added_words: [alongside, avoids, capable, catalyst, driving, external, normal, views, volatility]` · note: macro catalyst role in high-resistance liquidity runs

## (b) RECOGNITION (his criteria and his rejections)
- He characterizes Non-Farm Payroll Fridays as highly manipulated, difficult days that frequently deny standard intraday expectations.
  > "non-farm payroll Fridays are difficult trading days because they're highly manipulated meaning that what you might anticipate in any other given day"
  `[U3K3-142]` · `December-2023-Non-Farm-Payroll-Live-Execution-&-Explanations-002.json` (E1_EARLY_SERIES) · window `W0182` · `added_words: [characterizes, expectations, frequently, intraday, standard]` · note: recognition of NFP Friday manipulation
- In his day-trading rules, FOMC and Non-Farm Payroll days are classified as no-setup days where traders stay on the sidelines.
  > "fomc days and non-farm payroll days keep us on the sidelines and they are basically a no setup day"
  `[U3K3-143]` · `ICT-Mentorship-Core-Content-Month-08-Essentials-To-ICT-Daytrading-001.json` (E3_2017) · window `W0184` · `added_words: [classified, rules, traders, trading]` · note: REJECTION / stand-aside rule: 'fomc days and non-farm payroll days keep us on the sidelines'
- He rejects entering at the 8:30 AM New York Non-Farm Payroll release because slippage crushes fills.
  > "new york local time non-farm payroll if you try to take that trade at 8 30 you're going to get crushed with the slippage"
  `[U3K3-144]` · `ICT-Emini-S&P-500-AM-&-PM-Session-Review-09-02-22-001.json` (E4_2019_2022) · window `W0190` · `added_words: [crushes, entering, fills, rejects, release]` · note: REJECTION of 8:30 AM NFP execution due to slippage

## (c) OBSERVABLES — ENGINEERING_HYPOTHESIS (needs owner approval)
- scheduled first-Friday 08:30 America/New_York employment release window, associated with pre-release Monday–Thursday compression ('Seek and Destroy') and an 08:30 volatility spike that can leave a gap ('vacuum block') or sweep both sides of the local range
  `candle_observable: true` · derived from `U3K3-146`, `U3K3-148`, `U3K3-149`, `U3K3-150` · **ENGINEERING_HYPOTHESIS — needs owner approval**
- identifying NFP week requires calendar metadata external to raw OHLC candles
  `candle_observable: false` · derived from `U3K3-143`, `U3K3-145`, `U3K3-147` · **ENGINEERING_HYPOTHESIS — needs owner approval**

## (d) HOW HE TREATS IT
- During Non-Farm Payroll weeks, he instructs students to stop trading after Wednesday's New York session and only observe Thursday and Friday.
  > "i try to teach my students to stop trading by the new york session on wednesday"
  `[U3K3-145]` · `2022-ICT-Mentorship-Episode-37-001.json` (E4_2019_2022) · window `W0185` · `added_words: [instructs, wednesday's]` · note: NFP week cutoff rule: stop trading by Wednesday NY session
- For position traders, if the Non-Farm Payroll Friday move is a Judas swing confirmed by SMT divergence and seasonal tendency, entry is taken late Friday before the close or after Monday's fair value gap.
  > "if we expect this to be a Judith swing non Farm payroll okay late in the day on Friday if you're a position Trader"
  `[U3K3-146]` · `ICT-Charter-Price-Action-Model-#4-Supplementary-Lesson-001.json` (E4_2019_2022) · window `W0181` · `added_words: [confirmed, judas, monday's, move, taken, traders]` · note: exact unhyphenated hit ('non Farm payroll'); position-trading treatment

## (e) COMPARING INSTANCES
- He contrasts Monday–Wednesday of NFP week with Thursday–Friday, stating Thursday and Friday lose precision and become choppy and sporadic.
  > "on the thursday and friday of non-farm payroll weeks they can be choppy they can be sporadic they can come back against you"
  `[U3K3-147]` · `2022-ICT-Mentorship-Episode-37-001.json` (E4_2019_2022) · window `W0185` · `added_words: [become, contrasts, monday, nfp, stating]` · note: comparative: Mon–Wed vs Thu–Fri of NFP week

## (f) INTERACTIONS
- The volatility injection from a Non-Farm Payroll release can create a vacuum block (a liquidity-vacuum gap in price action).
  > "the gap forms by a vacuum of liquidity directly related to an event non-farm payroll can create a vacuum block"
  `[U3K3-148]` · `ICT-Mentorship-Core-Content-Month-04-ICT-Vacuum-Block-001.json` (E2_2016) · window `W0188` · `added_words: [none]` · note: interaction with vacuum block
- Awaiting Non-Farm Payroll (especially in July and August) produces the 'Seek and Destroy Friday' weekly profile where Monday–Thursday consolidate and sweep shallow stops.
  > "when the market is awaiting interest rate announcements and or non-farm payroll can create this profile in the summer months of July and August"
  `[U3K3-149]` · `ICT-Mentorship-Core-Content-Month-07-Short-Term-Trading-Defining-Weekly-Range-Profiles-001.json` (E3_2017) · window `W0189` · `added_words: ['seek, consolidate, especially, friday', produces, sweep]` · note: interaction with Seek and Destroy weekly profile

## (g) TIMEFRAME
- Intraday, Non-Farm Payroll is anchored to the 8:30 AM New York news embargo release window.
  > "there's usually a lot of news that comes out during the New York session okay so the 8:30 news session usually it's like non-farm payroll"
  `[U3K3-150]` · `OTE-Pattern-Recognition-Series-Vol-01-001.json` (E4_2019_2022) · window `W0194` · `added_words: [anchored, embargo, intraday, release, window]` · note: 8:30 AM NY timestamp

## (h) FAILURE / INVALIDATION and DISCRETION
- Because manual intervention at the 8:30 release can whip both sides and set unpredictable highs and lows, trading the release is gambling.
  > "we don't know where non-farm payroll is going to use the high and low that it creates after the initial run at E30"
  `[U3K3-151]` · `Thursday-June-15-2023-ICT-Price-Action-Workshop-003.json` (E5_2023_2024) · window `W0186` · `added_words: [intervention, release, set, sides, trading, unpredictable, whip]` · note: failure of normal algorithmic precision during NFP release; [sic-asr] 'E30' for '8:30'

## (i) VARIANTS (kept parallel, never merged)
- While he avoids NFP days in standard day trading (W0184, W0192), he occasionally demonstrates live NFP scalps for students (W0182) or late-Friday position entries after the Judas swing (W0181).
  > "unless you're ultra short term scalper and you fade that move and I don't like to do it because it's a carnival ride"
  `[U3K3-152]` · `ICT-W-E-N-T-Series-5-of-5-001.json` (E1_EARLY_SERIES) · window `W0187` · `added_words: [avoids, demonstrates, entries, friday, judas, late, live, nfp, occasionally, position, scalps, standard, students, swing, trading, w0181, w0182, w0184, w0192]` · note: parallel practice: general no-trade rule vs live execution demonstration / late-Friday position entry

## Windows Logged and Read This Session (`±100` words each)
| Window | Era | Match | Transcript | Word Range | SHA-256 (prefix) |
|---|---|---|---|---|---|
| `W0181` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-#4-Supplementary-Lesson-001.json` | `10167..10368` (201w) | `1af25061a283` |
| `W0182` | `E1_EARLY_SERIES` | `asr_hyphen_or_plural_variant` | `December-2023-Non-Farm-Payroll-Live-Execution-&-Explanations-002.json` | `2960..3161` (201w) | `fb873eff3a97` |
| `W0183` | `E2_2016` | `asr_hyphen_or_plural_variant` | `ICT-Mentorship-Core-Content-Month-1-Liquidity-Runs-001.json` | `1375..1576` (201w) | `a703894181cc` |
| `W0184` | `E3_2017` | `asr_hyphen_or_plural_variant` | `ICT-Mentorship-Core-Content-Month-08-Essentials-To-ICT-Daytrading-001.json` | `1082..1283` (201w) | `053114e9f048` |
| `W0185` | `E4_2019_2022` | `asr_hyphen_or_plural_variant` | `2022-ICT-Mentorship-Episode-37-001.json` | `826..1027` (201w) | `9a1b46f5aa11` |
| `W0186` | `E5_2023_2024` | `asr_hyphen_or_plural_variant` | `Thursday-June-15-2023-ICT-Price-Action-Workshop-003.json` | `417..618` (201w) | `7c6d2a979f13` |
| `W0187` | `E1_EARLY_SERIES` | `asr_hyphen_or_plural_variant` | `ICT-W-E-N-T-Series-5-of-5-001.json` | `9105..9306` (201w) | `d8482cef7970` |
| `W0188` | `E2_2016` | `asr_hyphen_or_plural_variant` | `ICT-Mentorship-Core-Content-Month-04-ICT-Vacuum-Block-001.json` | `0..156` (156w) | `13990282c4be` |
| `W0189` | `E3_2017` | `asr_hyphen_or_plural_variant` | `ICT-Mentorship-Core-Content-Month-07-Short-Term-Trading-Defining-Weekly-Range-Profiles-001.json` | `1098..1299` (201w) | `ac723a804bfb` |
| `W0190` | `E4_2019_2022` | `asr_hyphen_or_plural_variant` | `ICT-Emini-S&P-500-AM-&-PM-Session-Review-09-02-22-001.json` | `389..590` (201w) | `7995d5376cfc` |
| `W0191` | `E5_2023_2024` | `asr_hyphen_or_plural_variant` | `Pattern-Recognition-Selecting-Precision-Price-Objectives-001.json` | `5450..5651` (201w) | `077af20f593a` |
| `W0192` | `E1_EARLY_SERIES` | `asr_hyphen_or_plural_variant` | `ICT-Trading-Plan-Development-1-001.json` | `5211..5412` (201w) | `6251cf47513e` |
| `W0193` | `E3_2017` | `asr_hyphen_or_plural_variant` | `ICT-Mentorship-Core-Content-Month-10-Bond-Trading-Basics-&-Opening-Range-Concept-001.json` | `1600..1801` (201w) | `a91b4e7fe04a` |
| `W0194` | `E4_2019_2022` | `asr_hyphen_or_plural_variant` | `OTE-Pattern-Recognition-Series-Vol-01-001.json` | `5159..5360` (201w) | `23a1c57b935d` |
| `W0195` | `E5_2023_2024` | `asr_hyphen_or_plural_variant` | `December-2023-Non-Farm-Payroll-Live-Execution-&-Explanations-002.json` | `2960..3161` (201w) | `fb873eff3a97` |
