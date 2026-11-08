# Understanding card — asian range (`asian_range`)

Windows extracted and read in full (`±100` words) this session: **15** (target 15) across **15** distinct transcripts (`E1_EARLY_SERIES`: 4, `E2_2016`: 1, `E3_2017`: 4, `E4_2019_2022`: 3, `E5_2023_2024`: 3). Meets the 15-window budget.
Claims: U3K3-001, U3K3-002, U3K3-003, U3K3-004, U3K3-005, U3K3-006, U3K3-007, U3K3-008, U3K3-009, U3K3-010, U3K3-011, U3K3-012

Every quoted line below is verbatim (≤25 words) from a `±100`-word window logged and read in full this session. Per Rule 2, `statement` in `claims.jsonl` carries the verbatim quote, `reading` carries the interpretation below, and `added_words` lists every word in `reading` absent from the window. Section (c) is explicitly an `ENGINEERING_HYPOTHESIS`, not his words. Empty sections read `NOT_IN_SOURCES`.

## (a) PURPOSE
- He defines the Asian range as the initial price equilibrium that starts the daily range structure.
  > "the daily range structure can be really broken down and simplified with it starts with a price equilibrium that's asian range"
  `[U3K3-001]` · `ICT-Mentorship-Core-Content-Month-1-How-Market-Makers-Condition-The-Market-001.json` (E2_2016) · window `W0001` · `added_words: [defines, initial]` · note: definition: 'starts with a price equilibrium that's asian range'

## (b) RECOGNITION (his criteria and his rejections)
- He bounds the Asian range for expansion counting between 8:00 pm and midnight New York time when in a clear trading range.
  > "the ideal consideration is when the range between 8:00 pm New York time and midnight New York time is found to be"
  `[U3K3-002]` · `ICT-Charter-Price-Action-Model-5-Day-Trading-Intraday-Volatility-Expansions-001.json` (E4_2019_2022) · window `W0005` · `added_words: [bounds, counting]` · note: clock bounds stated by speaker: 8:00 pm to midnight NY
- He rejects using the Asian range for expansion projections when it is under 20 pips or over 40 pips, switching to the flout.
  > "if the range is less than 20 Pips do not use the Asian range for expansion objectives elect to use the flout"
  `[U3K3-003]` · `ICT-Charter-Price-Action-Model-5-Day-Trading-Intraday-Volatility-Expansions-001.json` (E4_2019_2022) · window `W0005` · `added_words: [projections, rejects, switching, using]` · note: REJECTION: 'if the range is less than 20 Pips do not use the Asian range'
- If the Asian range is not visually consolidating after 8 PM New York, he avoids trading the London session.
  > "if Central Bank dealers range and or Asian range is not visually and it means obviously consolidating I'm going to look to avoid"
  `[U3K3-004]` · `ICT-Mentorship-Core-Content-Month-08-When-To-Avoid-The-London-Session-001.json` (E3_2017) · window `W0004` · `added_words: [avoids]` · note: REJECTION / stand-aside condition

## (c) OBSERVABLES — ENGINEERING_HYPOTHESIS (needs owner approval)
- initial consolidation high and low formed during the Asian session prior to midnight New York time, evaluated by whether price remains in a visually quiet consolidation relative to the preceding London open-to-close range rather than sustaining a directional trend
  `candle_observable: true` · derived from `U3K3-001`, `U3K3-004`, `U3K3-002`, `U3K3-003` · **ENGINEERING_HYPOTHESIS — needs owner approval**
- parallel clock-window definitions (8:00 PM–midnight vs 7:00 PM–midnight NY) and Friday-over-Sunday substitution for Monday trading must be carried as separate parameterisations rather than merged
  `candle_observable: true` · derived from `U3K3-002`, `U3K3-003`, `U3K3-007`, `U3K3-012` · **ENGINEERING_HYPOTHESIS — needs owner approval**
- 20–40 pip range bounds stated in forex lectures are instrument-specific remarks; generalising them to fixed thresholds across assets is not supported
  `candle_observable: unknown` · derived from `U3K3-005`, `U3K3-002`, `U3K3-003` · **ENGINEERING_HYPOTHESIS — needs owner approval**

## (d) HOW HE TREATS IT
- At 8 pm starting the Asian range, he projects the range two standard deviations up to estimate the London high.
  > "starting the Asian range project that range that we created for Central Bank dealers range two standard deviations up that gives us"
  `[U3K3-005]` · `ICT-Mentorship-Core-Content-Month-08-Central-Bank-Dealers-Range-001.json` (E3_2017) · window `W0002` · `added_words: [estimate, projects]` · note: K2 seed claim deepened with full window context
- When bearish and selling on weakness after a Judas swing rally, he places a sell stop below the Asian range low.
  > "all you have to do is go right to the uh the low of the Asian range put a sell stop there"
  `[U3K3-006]` · `ICT-Charter-Price-Action-Model-2-Amplified-Lecture-001.json` (E4_2019_2022) · window `W0013` · `added_words: [judas, places, selling]` · note: execution treatment using sell stop below Asian range low

## (e) COMPARING INSTANCES
- For Monday's trading he rejects Sunday's Asian range and uses Friday's Asian range instead.
  > "I don't look at the Asian range on Sundays for Monday's trading I use Fridays"
  `[U3K3-007]` · `April-11-2023-Live-Tape-Reading-Emini-S&P-AM-Session-001.json` (E5_2023_2024) · window `W0010` · `added_words: [friday's, instead, rejects, sunday's, uses]` · note: comparative preference: Friday's Asian range over Sunday's

## (f) INTERACTIONS
- He looks for a drop below the midnight opening price matching standard deviations of the Asian range, flout, or CBDR into a 15-minute discount array.
  > "below that opening price to some measure of standard deviations of the Asian range the flout or Central Bank dealers range to a discount"
  `[U3K3-008]` · `ICT-Mentorship-Core-Content-Month-09-ICT-Day-Trade-Routine-001.json` (E3_2017) · window `W0012` · `added_words: [cbdr, drop, looks, matching]` · note: interaction with midnight opening price, CBDR, flout, and 15m discount PD array

## (g) TIMEFRAME
- After setting higher-timeframe levels (60-minute to monthly), he marks previous day's session highs/lows and Asian range highs and lows.
  > "identify key price levels from the 60-minute chart up to the monthly nothing less than a 60-minute chart and ideally the daily"
  `[U3K3-009]` · `ICT-Trading-Plan-Development-1-001.json` (E1_EARLY_SERIES) · window `W0011` · `added_words: [higher, marks, setting]` · note: timeframe hierarchy placing Asian range highs/lows below HTF levels

## (h) FAILURE / INVALIDATION and DISCRETION
- He shows a losing trade example where price moves deeper below to run the stops on the Asian range low before rallying.
  > "here's one where it moves deeper below and runs the stops on the Asian range low before running higher"
  `[U3K3-010]` · `ICT-Forex-Scout-Sniper-Basic-Field-Guide-Vol-4-003.json` (E1_EARLY_SERIES) · window `W0007` · `added_words: [example, rallying, run, shows]` · note: failure/stop-run example

## (i) VARIANTS (kept parallel, never merged)
- In the 2022 mentorship model he states traders do not need to use the Asian range or CBDR at all.
  > "i wouldn't worry about doing anything with asian range i wouldn't even worry about doing anything with the"
  `[U3K3-011]` · `2022-ICT-Mentorship-Episode-18-001.json` (E4_2019_2022) · window `W0009` · `added_words: [cbdr, states, traders, use]` · note: parallel variant: 2022 model omits Asian range entirely
- Elsewhere he states the initial Asian range is set between 7:00 p.m. and midnight (versus 8:00 p.m. to midnight in W0005).
  > "because the initial range that was set between 7:00 p.m. and midnight midnight is when HIPAA the interbank price delivery algorithm resets"
  `[U3K3-012]` · `ICT-Forex-Implementing-The-Asian-Range-001.json` (E1_EARLY_SERIES) · window `W0015` · `added_words: [elsewhere, states, versus, w0005]` · note: parallel clock variant: 7:00 p.m. to midnight vs 8:00 p.m. to midnight; [sic-asr] 'HIPAA' for IPDA

## Windows Logged and Read This Session (`±100` words each)
| Window | Era | Match | Transcript | Word Range | SHA-256 (prefix) |
|---|---|---|---|---|---|
| `W0001` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-1-How-Market-Makers-Condition-The-Market-001.json` | `2278..2479` (201w) | `5aa74c544fb0` |
| `W0002` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-08-Central-Bank-Dealers-Range-001.json` | `1592..1793` (201w) | `bf06fe8e20dc` |
| `W0003` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-W-E-N-T-Series-5-of-5-002.json` | `4585..4786` (201w) | `48dd5856afd3` |
| `W0004` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-08-When-To-Avoid-The-London-Session-001.json` | `1596..1797` (201w) | `81cc5e41e6a4` |
| `W0005` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-5-Day-Trading-Intraday-Volatility-Expansions-001.json` | `2628..2829` (201w) | `3932ce412c57` |
| `W0006` | `E5_2023_2024` | `exact_kept_tsv` | `Pattern-Recognition-Selecting-Precision-Price-Objectives-001.json` | `5980..6181` (201w) | `077af20f593a` |
| `W0007` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-Forex-Scout-Sniper-Basic-Field-Guide-Vol-4-003.json` | `1986..2187` (201w) | `f533441190e0` |
| `W0008` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-12-Intraday-Top-Down-Analysis-001.json` | `3132..3333` (201w) | `f7a999fa660f` |
| `W0009` | `E4_2019_2022` | `exact_kept_tsv` | `2022-ICT-Mentorship-Episode-18-001.json` | `951..1152` (201w) | `8c122e79e0c3` |
| `W0010` | `E5_2023_2024` | `exact_kept_tsv` | `April-11-2023-Live-Tape-Reading-Emini-S&P-AM-Session-001.json` | `2619..2820` (201w) | `276ecf21bb4f` |
| `W0011` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-Trading-Plan-Development-1-001.json` | `8125..8326` (201w) | `6251cf47513e` |
| `W0012` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-09-ICT-Day-Trade-Routine-001.json` | `7588..7789` (201w) | `9f8913e03f11` |
| `W0013` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-2-Amplified-Lecture-001.json` | `6451..6652` (201w) | `3fe1d012a146` |
| `W0014` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-New-York-Live-Session-October-10-2017-001.json` | `3968..4169` (201w) | `55899d04c7fc` |
| `W0015` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-Forex-Implementing-The-Asian-Range-001.json` | `3919..4120` (201w) | `8dc23b8c6e91` |
