# Understanding card — market maker (`market_maker`)

Windows extracted and read in full (`±100` words) this session: **15** (target 15) across **15** distinct transcripts (`E1_EARLY_SERIES`: 3, `E2_2016`: 4, `E3_2017`: 3, `E4_2019_2022`: 3, `E5_2023_2024`: 2). Meets the 15-window budget.
Claims: U3K3-106, U3K3-107, U3K3-108, U3K3-109, U3K3-110, U3K3-111, U3K3-112, U3K3-113, U3K3-114, U3K3-115, U3K3-116, U3K3-117

Every quoted line below is verbatim (≤25 words) from a `±100`-word window logged and read in full this session. Per Rule 2, `statement` in `claims.jsonl` carries the verbatim quote, `reading` carries the interpretation below, and `added_words` lists every word in `reading` absent from the window. Section (c) is explicitly an `ENGINEERING_HYPOTHESIS`, not his words. Empty sections read `NOT_IN_SOURCES`.

## (a) PURPOSE
- He defines the market maker as the entity that controls and delivers price, stating traders cannot beat them and must align with their delivery.
  > "you're not beating the market maker ever it never happens because you can't control price they do"
  `[U3K3-106]` · `April-11-2023-Live-Tape-Reading-Emini-S&P-AM-Session-003.json` (E5_2023_2024) · window `W0141` · `added_words: [align, beat, cannot, defines, delivery, entity, stating, traders]` · note: definition and role of market maker

## (b) RECOGNITION (his criteria and his rejections)
- He characterizes market maker delivery as always beginning from a consolidation (holding pattern) before moving into an expansion impulse swing.
  > "all markets start from a consolidation and move into an expansion that means there's an impulse move or an impulse price swing"
  `[U3K3-107]` · `ICT-Mentorship-Core-Content-Month-1-Elements-Of-A-Trade-Setup-001.json` (E2_2016) · window `W0136` · `added_words: [always, beginning, characterizes, delivery, moving]` · note: K2 seed window deepened
- He identifies a bullish market maker footprint when sell stops below consolidations are repeatedly run followed by expansions through buy stops.
  > "every time the sell stocks would be ran below a consolidation it runs higher and it goes through the buy stops"
  `[U3K3-108]` · `ICT-Mentorship-Core-Content-Month-02-Market-Maker-Trap-False-Breakouts-001.json` (E2_2016) · window `W0143` · `added_words: [consolidations, expansions, followed, footprint, identifies, repeatedly, run]` · note: observable footprint of market maker booking; [sic-asr] 'sell stocks'
- He rejects obvious retail trendline resistance as a market maker trap engineered to attract uninformed sellers and provide liquidity for a rally.
  > "if the trend line looks so obvious to me I look at that as a trap retail Bears trend line resistance"
  `[U3K3-109]` · `ICT-Mentorship-Core-Content-Month-03-Market-Maker-Trap-Trendline-Phantoms-001.json` (E2_2016) · window `W0148` · `added_words: [attract, engineered, provide, rejects, sellers, trendline, uninformed]` · note: REJECTION of obvious retail trendlines as market maker traps

## (c) OBSERVABLES — ENGINEERING_HYPOTHESIS (needs owner approval)
- a multi-stage price delivery sequence (original consolidation -> distribution/accumulation leg -> smart-money reversal at a higher-timeframe PD array/liquidity pool -> reaccumulation/redistribution -> return to or past the original consolidation level)
  `candle_observable: true` · derived from `U3K3-107`, `U3K3-114`, `U3K3-111`, `U3K3-112` · **ENGINEERING_HYPOTHESIS — needs owner approval**
- whether central banks or an algorithm ('IPDA') intentionally control price to punish uninformed traders is an interpretive narrative not directly observable on candles
  `candle_observable: false` · derived from `U3K3-110`, `U3K3-106`, `U3K3-117` · **ENGINEERING_HYPOTHESIS — needs owner approval**

## (d) HOW HE TREATS IT
- Rather than treating the market maker as an enemy, he tracks how smart money prices toward uninformed liquidity to trade alongside them.
  > "we don't vilify the market maker we don't vilify smart money we don't beat up or make fun of the uninformed money"
  `[U3K3-110]` · `ICT-Mentorship-Core-Content-Month-1-What-To-Focus-On-Right-Now-001.json` (E2_2016) · window `W0138` · `added_words: [alongside, enemy, liquidity, prices, rather, toward, tracks, treating]` · note: mindset/treatment of market maker behavior
- When shorting, he covers at targeted discount liquidity because price can initiate a market maker buy profile and rally from that pool.
  > "we limit it to wanting to take our short cover here not looking for a longer term because the likelihood is is we may come"
  `[U3K3-111]` · `ICT-Charter-Price-Action-Model-7-Universal-Trading-Model-001.json` (E4_2019_2022) · window `W0140` · `added_words: [covers, discount, initiate, pool, shorting]` · note: exit discipline anticipating opposing market maker buy model

## (e) COMPARING INSTANCES
- In a market maker sell model, once equal lows of the original consolidation have already been swept, he does not require price to return there again.
  > "this would not need to come down here to clear this original consolidation over here because n is these equal loads have already ran out"
  `[U3K3-112]` · `ICT-Charter-Price-Action-Model-6-2-Amplified-Lesson-001.json` (E4_2019_2022) · window `W0150` · `added_words: [lows, once, require, swept]` · note: comparison of swept vs unswept original consolidation; [sic-asr] 'equal loads'

## (f) INTERACTIONS
- Recognizing a market maker buy or sell model in real time requires knowing every PD array—including breakers, mitigation blocks, and inversion FVGs.
  > "a market maker model is relying on your understanding of every PD I've made available"
  `[U3K3-113]` · `ICT-Mentorship-2023-Market-Maker-Models-001.json` (E5_2023_2024) · window `W0146` · `added_words: [array, blocks, breakers, fvgs, including, knowing, recognizing, requires]` · note: synthesis of all PD arrays inside a market maker model

## (g) TIMEFRAME
- In a market maker template, if entry is framed off a monthly discount liquidity pool, the upside target is a weekly or daily premium PD array.
  > "you're looking for a time frame lesser than the discount liquidity pool that you used to buy off of for an example if you bought"
  `[U3K3-114]` · `ICT-Mentorship-Core-Content-Month-07-Short-Term-Trading-Market-Maker-Manipulation-Templates-001.json` (E3_2017) · window `W0139` · `added_words: [entry, framed, target, upside]` · note: cross-timeframe pairing rule between discount trigger and premium target
- Market maker profiles occur on any timeframe (1m to daily), but he states they are most apt to be framed on daily, 4-hour, or hourly levels.
  > "they can occur on any time frame but the more apt to occur on a daily for hour and or hourly timeframe"
  `[U3K3-115]` · `ICT-Forex-Scout-Sniper-Basic-Field-Guide-Vol-3-002.json` (E1_EARLY_SERIES) · window `W0147` · `added_words: [framed, profiles, states]` · note: timeframe distribution of market maker profiles

## (h) FAILURE / INVALIDATION and DISCRETION
- He states every market maker profile is ambiguous in isolation: one trader may trade the buy side while another trades the sell side of the same fractal.
  > "every one of these profiles is ambiguous okay in other words it can be viewed even though I present it as a bullish market profile"
  `[U3K3-116]` · `ICT-Trading-Plan-Development-6-001.json` (E1_EARLY_SERIES) · window `W0142` · `added_words: [isolation, side, states, trader, trades]` · note: explicit ambiguity caveat

## (i) VARIANTS (kept parallel, never merged)
- He contrasts historical human market makers with modern algorithmic price delivery (IPDA), stating the process is now automated by computer program.
  > "it used to be a manual thing where the market maker was a real person they sat there and they worked with a team"
  `[U3K3-117]` · `ICT-Mentorship-Core-Content-Month-05-Using-IPDA-Data-Ranges-001.json` (E3_2017) · window `W0149` · `added_words: [algorithmic, automated, contrasts, historical, human, ipda, makers, modern, process, stating]` · note: parallel conceptual framing: human market maker team vs IPDA computer algorithm

## Windows Logged and Read This Session (`±100` words each)
| Window | Era | Match | Transcript | Word Range | SHA-256 (prefix) |
|---|---|---|---|---|---|
| `W0136` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-1-Elements-Of-A-Trade-Setup-001.json` | `876..1077` (201w) | `17b293605788` |
| `W0137` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-Forex-Market-Maker-Series-Vol-5-of-5-001.json` | `2458..2659` (201w) | `caf943c37c43` |
| `W0138` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-1-What-To-Focus-On-Right-Now-001.json` | `1224..1425` (201w) | `fa2a5bf0731a` |
| `W0139` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-07-Short-Term-Trading-Market-Maker-Manipulation-Templates-001.json` | `368..569` (201w) | `1c08571f5863` |
| `W0140` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-7-Universal-Trading-Model-001.json` | `8613..8814` (201w) | `a707fe1d2e53` |
| `W0141` | `E5_2023_2024` | `exact_kept_tsv` | `April-11-2023-Live-Tape-Reading-Emini-S&P-AM-Session-003.json` | `6100..6301` (201w) | `abe15c6d2544` |
| `W0142` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-Trading-Plan-Development-6-001.json` | `1133..1334` (201w) | `50e1d39cb18e` |
| `W0143` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-02-Market-Maker-Trap-False-Breakouts-001.json` | `2834..3035` (201w) | `410f56f11cc8` |
| `W0144` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-11-Stock-Mega-Trades-001.json` | `2815..3016` (201w) | `b711d1b4a986` |
| `W0145` | `E4_2019_2022` | `exact_kept_tsv` | `2022-ICT-Mentorship-Episode-20-001.json` | `236..437` (201w) | `af05701eaa4e` |
| `W0146` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-Mentorship-2023-Market-Maker-Models-001.json` | `0..191` (191w) | `643d9f19046c` |
| `W0147` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-Forex-Scout-Sniper-Basic-Field-Guide-Vol-3-002.json` | `8685..8886` (201w) | `25545778d51a` |
| `W0148` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-03-Market-Maker-Trap-Trendline-Phantoms-001.json` | `1353..1554` (201w) | `4f84b5c757d8` |
| `W0149` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-05-Using-IPDA-Data-Ranges-001.json` | `4597..4798` (201w) | `fd247dcc7730` |
| `W0150` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-6-2-Amplified-Lesson-001.json` | `2681..2882` (201w) | `7d82a845c710` |
