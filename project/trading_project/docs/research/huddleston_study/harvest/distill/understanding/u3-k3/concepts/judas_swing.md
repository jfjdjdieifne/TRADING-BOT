# Understanding card — judas swing (`judas_swing`)

Windows extracted and read in full (`±100` words) this session: **15** (target 15) across **15** distinct transcripts (`E1_EARLY_SERIES`: 3, `E2_2016`: 3, `E3_2017`: 3, `E4_2019_2022`: 3, `E5_2023_2024`: 3). Meets the 15-window budget.
Claims: U3K3-072, U3K3-073, U3K3-074, U3K3-075, U3K3-076, U3K3-077, U3K3-078, U3K3-079, U3K3-080, U3K3-081, U3K3-082

Every quoted line below is verbatim (≤25 words) from a `±100`-word window logged and read in full this session. Per Rule 2, `statement` in `claims.jsonl` carries the verbatim quote, `reading` carries the interpretation below, and `added_words` lists every word in `reading` absent from the window. Section (c) is explicitly an `ENGINEERING_HYPOTHESIS`, not his words. Empty sections read `NOT_IN_SOURCES`.

## (a) PURPOSE
- The Judas swing is the false trap move beyond the opening price and Asian range boundary designed to trip traders in the wrong direction.
  > "that movement above the opening price above the asian range high that is the Judas swing this is the false or trap move"
  `[U3K3-072]` · `ICT-Forex-Understanding-The-ICT-Judas-Swing-001.json` (E1_EARLY_SERIES) · window `W0097` · `added_words: [beyond, boundary, designed, direction, wrong]` · note: purpose and definition of Judas swing
- It serves as a fake-out move to convince traders price is going the other way and clear stops before the real move unfolds.
  > "that little subtle judas swing that fake out move that gets everybody thinking it's going the other way just to offset get the shorts out"
  `[U3K3-073]` · `ICT-Live-Session-June-12-2022-001.json` (E5_2023_2024) · window `W0101` · `added_words: [clear, convince, price, serves, stops, traders, unfolds]` · note: counterparty stop-clearing purpose

## (b) RECOGNITION (his criteria and his rejections)
- Following the Asian range consolidation, the Judas swing manipulation comes with a news event driver before range expansion.
  > "there's a manipulation and that's always going to come by way of some news event some news driver either at the time"
  `[U3K3-074]` · `ICT-Mentorship-Core-Content-Month-1-How-Market-Makers-Condition-The-Market-001.json` (E2_2016) · window `W0091` · `added_words: [comes, following]` · note: K2 seed claim verified in full window
- He recognizes a Judas swing when price sharply rams through an old high's buy stops and then breaks back below the lowest down-close candle.
  > "the market rams through that and this action right here is what I teach as a Judas swing I know it's it's a fake move"
  `[U3K3-075]` · `OTE-Pattern-Recognition-Series-Vol-04-001.json` (E4_2019_2022) · window `W0104` · `added_words: [high's, recognizes, sharply]` · note: structural confirmation via break of lowest down-close candle

## (c) OBSERVABLES — ENGINEERING_HYPOTHESIS (needs owner approval)
- an initial post-open excursion counter to the higher-timeframe directional bias (above the session/midnight opening price and Asian range high when bearish, or below when bullish) that sweeps local stops before reversing back inside the range
  `candle_observable: true` · derived from `U3K3-074`, `U3K3-078`, `U3K3-072`, `U3K3-076`, `U3K3-075` · **ENGINEERING_HYPOTHESIS — needs owner approval**
- scales fractally across intraday London (post-midnight/2:00 AM NY), New York (post-7:00/8:30 AM NY), and weekly (Monday false swing) horizons
  `candle_observable: true` · derived from `U3K3-080`, `U3K3-078`, `U3K3-076`, `U3K3-082` · **ENGINEERING_HYPOTHESIS — needs owner approval**

## (d) HOW HE TREATS IT
- When bearish, he looks for a false rally (Judas swing) above the midnight or 8:30 NY opening price and fades it by selling into the rally.
  > "that opening price fund bears i want to see a move above that's what i dub a judas swing a false rally"
  `[U3K3-076]` · `2022-ICT-Mentorship-Episode-21-001.json` (E4_2019_2022) · window `W0100` · `added_words: [fades, looks, selling]` · note: fading the Judas swing above opening price; [sic-asr] 'fund bears' for 'if I'm bearish'
- When bullish, he buys during the Judas swing drop below the opening price rather than chasing price after expansion.
  > "you want to be buying on the Judas swing down or below the opening price and don't chase price"
  `[U3K3-077]` · `ICT-Mentorship-Core-Content-Month-09-Bread-&-Butter-Buy-Setups-001.json` (E3_2017) · window `W0094` · `added_words: [bullish, buys, chasing, drop, expansion, rather]` · note: rule: buy on the Judas swing below opening price, do not chase

## (e) COMPARING INSTANCES
- He ranks fading the Judas swing directly above the Asian range high after 2:00 AM as better than waiting for a stop-entry confirmation.
  > "if you don't trust this part of it which is in my mind the better way of doing it but I understand some of you"
  `[U3K3-078]` · `ICT-Charter-Price-Action-Model-2-Trade-Plan-&-Algorithmic-Theory-001.json` (E4_2019_2022) · window `W0095` · `added_words: [directly, entry, fading, ranks]` · note: comparative: fading Judas swing directly is 'the better way of doing it' vs waiting for confirmation

## (f) INTERACTIONS
- The Judas swing protraction direction is framed by daily PD arrays, IPDA data ranges, quarterly shift, seasonal tendency, and day of week (Mon–Wed).
  > "so if we set our daily bias based on the daily PD arrays and if the data ranges and the quarterly shift is still bullish"
  `[U3K3-079]` · `ICT-Mentorship-Core-Content-Month-08-Integrating-Daytrades-With-HTF-Trade-Entries-001.json` (E3_2017) · window `W0099` · `added_words: [day, direction, framed, ipda, mon, protraction, wed, week]` · note: multi-factor interaction framing the London Judas swing

## (g) TIMEFRAME
- He specifies session clock gates for intraday Judas swings: after 4:00 GMT (midnight/2:00 AM NY) in London and after 7:00 AM NY (or 8:30 AM in W0100) in New York.
  > "same thing occurs in after new york's seven o'clock in the morning time we anticipate a round up off the london high"
  `[U3K3-080]` · `ICT-Mentorship-Core-Content-Month-1-Impulse-Price-Swings-&-Market-Protraction-001.json` (E2_2016) · window `W0093` · `added_words: [clock, gates, intraday, specifies, swings, w0100]` · note: session timing windows for London and NY Judas swings

## (h) FAILURE / INVALIDATION and DISCRETION
- On the day before a major release like CPI, he treats a morning rally as a potential Judas swing with extreme caution and low conviction.
  > "what makes me extremely cautious and not have any strong convictions on where I think it's going to go is because we have CPI tomorrow"
  `[U3K3-081]` · `February-13-2023-ES-Tape-Reading-AM-Session-001.json` (E5_2023_2024) · window `W0105` · `added_words: [caution, conviction, day, extreme, like, low, major, potential, rally, release, treats]` · note: discretion/caution ahead of CPI release

## (i) VARIANTS (kept parallel, never merged)
- Beyond intraday London and New York sessions, he also applies a weekly Judas swing variant where Monday's initial rally is a false move for the week.
  > "measurements that I use to to more or less nail down the power three or dare I say it weekly Judas swing"
  `[U3K3-082]` · `ICT-Mentorship-Core-Content-Month-07-One-Shot-One-Kill-Model-001.json` (E3_2017) · window `W0103` · `added_words: [applies, beyond, london, monday's, move, new, sessions, variant, week, york]` · note: parallel scale variant: weekly Judas swing (Monday false move) vs intraday London/NY Judas swing

## Windows Logged and Read This Session (`±100` words each)
| Window | Era | Match | Transcript | Word Range | SHA-256 (prefix) |
|---|---|---|---|---|---|
| `W0091` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-1-How-Market-Makers-Condition-The-Market-001.json` | `2312..2513` (201w) | `5aa74c544fb0` |
| `W0092` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-W-E-N-T-Series-5-of-5-001.json` | `6242..6443` (201w) | `d8482cef7970` |
| `W0093` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-1-Impulse-Price-Swings-&-Market-Protraction-001.json` | `684..885` (201w) | `9d74168ea389` |
| `W0094` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-09-Bread-&-Butter-Buy-Setups-001.json` | `2772..2973` (201w) | `a0f805b27ddc` |
| `W0095` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-2-Trade-Plan-&-Algorithmic-Theory-001.json` | `7101..7302` (201w) | `4f8d9e46895a` |
| `W0096` | `E5_2023_2024` | `exact_kept_tsv` | `Thursday-June-15-2023-ICT-Price-Action-Workshop-003.json` | `8709..8910` (201w) | `7c6d2a979f13` |
| `W0097` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-Forex-Understanding-The-ICT-Judas-Swing-001.json` | `1451..1652` (201w) | `a62b3e471b29` |
| `W0098` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-02-The-Secrets-To-Selecting-High-Reward-Setups-001.json` | `2825..3026` (201w) | `04fe064cf1e5` |
| `W0099` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-08-Integrating-Daytrades-With-HTF-Trade-Entries-001.json` | `1655..1856` (201w) | `67cb6ba4a98e` |
| `W0100` | `E4_2019_2022` | `exact_kept_tsv` | `2022-ICT-Mentorship-Episode-21-001.json` | `2739..2940` (201w) | `c03874d68305` |
| `W0101` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-Live-Session-June-12-2022-001.json` | `5289..5490` (201w) | `f8c658c29002` |
| `W0102` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-Trading-Plan-Development-4-001.json` | `3861..4062` (201w) | `b67a17e18672` |
| `W0103` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-07-One-Shot-One-Kill-Model-001.json` | `4898..5099` (201w) | `41baf05ac47e` |
| `W0104` | `E4_2019_2022` | `exact_kept_tsv` | `OTE-Pattern-Recognition-Series-Vol-04-001.json` | `355..556` (201w) | `749b97876e5d` |
| `W0105` | `E5_2023_2024` | `exact_kept_tsv` | `February-13-2023-ES-Tape-Reading-AM-Session-001.json` | `1487..1688` (201w) | `4b6014de8c85` |
