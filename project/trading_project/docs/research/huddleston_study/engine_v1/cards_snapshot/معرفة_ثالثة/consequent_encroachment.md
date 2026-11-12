# Understanding card — consequent encroachment (`consequent_encroachment`)

Windows extracted and read in full (`±100` words) this session: **15** (target 15) across **15** distinct transcripts (`E1_EARLY_SERIES`: 2, `E4_2019_2022`: 6, `E5_2023_2024`: 7). Meets the 15-window budget.
Claims: U3K3-013, U3K3-014, U3K3-015, U3K3-016, U3K3-017, U3K3-018, U3K3-019, U3K3-020, U3K3-021, U3K3-022, U3K3-023, U3K3-024, U3K3-025

Every quoted line below is verbatim (≤25 words) from a `±100`-word window logged and read in full this session. Per Rule 2, `statement` in `claims.jsonl` carries the verbatim quote, `reading` carries the interpretation below, and `added_words` lists every word in `reading` absent from the window. Section (c) is explicitly an `ENGINEERING_HYPOTHESIS`, not his words. Empty sections read `NOT_IN_SOURCES`.

## (a) PURPOSE
- Consequent encroachment is the midpoint of a fair value gap where a retracement can stop and still count as filling fair value.
  > "the midpoint of that is called consequent encroachment and what that means is this is expected and it could stop there"
  `[U3K3-013]` · `ICT-Charter-Price-Action-Model-8-Targeting-6%-Per-Month-001.json` (E4_2019_2022) · window `W0024` · `added_words: [count, retracement]` · note: definition and purpose of consequent encroachment

## (b) RECOGNITION (his criteria and his rejections)
- He identifies consequent encroachment as the midpoint of a gap (SIBI/FVG) where price trades up and reverses before reaching old lows.
  > "it trades up to consequent encroachment which is the midpoint of that okay this is a gap"
  `[U3K3-014]` · `ICT-Forex-Review-January-09-2023-001.json` (E5_2023_2024) · window `W0016` · `added_words: [fvg, identifies, price, reaching, reverses]` · note: K2 seed claim verified in full window
- He treats a candle wick as a gap and measures its 50% midpoint as consequent encroachment, rejecting closes beyond it.
  > "it's working inside this Wick which is what a gap we do gradients on wicks 75 of the wick 50 of the wick"
  `[U3K3-015]` · `2023-ICT-Mentorship-Deep-Dive-Into-Institutional-Order-Flow-002.json` (E5_2023_2024) · window `W0017` · `added_words: [beyond, candle, closes, measures, rejecting, treats]` · note: recognition on wicks as well as gaps; K2 seed window
- When an old gap acts as a bearish inversion fair value gap, he checks low, consequent encroachment, and high, rejecting trades to the high end.
  > "if it's being treated as an inversion fair value Gap the better setups form if the high if you're looking at it as a resistance"
  `[U3K3-016]` · `Thursday-June-15-2023-ICT-Price-Action-Workshop-002.json` (E5_2023_2024) · window `W0027` · `added_words: [acts, bearish, checks, rejecting, trades]` · note: REJECTION: 'we don't want to see the high traded to'

## (c) OBSERVABLES — ENGINEERING_HYPOTHESIS (needs owner approval)
- the 50% arithmetic midpoint of an unfilled gap (FVG/SIBI/BISI) or candle wick/tail, evaluated by whether subsequent candle bodies close beyond the midpoint vs remain on the respecting side
  `candle_observable: true` · derived from `U3K3-014`, `U3K3-015`, `U3K3-023`, `U3K3-019`, `U3K3-013`, `U3K3-021` · **ENGINEERING_HYPOTHESIS — needs owner approval**
- reversal from the 50% midpoint without filling the far half of the gap is ranked as stronger directional weakness/strength than a full gap fill
  `candle_observable: true` · derived from `U3K3-019`, `U3K3-020` · **ENGINEERING_HYPOTHESIS — needs owner approval**

## (d) HOW HE TREATS IT
- When a fair value gap is wide (e.g. seven and a half handles), he uses consequent encroachment (the middle of the gap) as the short entry.
  > "when you have a fair value Gap that you want to go short in use the middle of the gap that's consequent encroachment"
  `[U3K3-017]` · `2022-ICT-Mentorship-Ends-Series-Part-4-of-4-001.json` (E4_2019_2022) · window `W0022` · `added_words: [uses]` · note: entry adjustment when FVG is wide
- Because price only needs to reach the middle point (consequent encroachment) without closing the entire gap, he enters at the bottom of the gap.
  > "it only needs to get to the middle point doesn't have to completely close it in this is the reason why I like"
  `[U3K3-018]` · `ICT-Charter-Price-Action-Model-9-One-Shot-One-Kill-001.json` (E4_2019_2022) · window `W0026` · `added_words: [closing, enters, entire, price, reach]` · note: entry vs stop placement relative to CE

## (e) COMPARING INSTANCES
- Rolling over directly from consequent encroachment (the 50% level) signals a stronger trade idea than going all the way up to fill the gap.
  > "if we get straight up to that price point and start to roll over many times that sign that signals a very stronger trade idea"
  `[U3K3-019]` · `ICT-Charter-Price-Action-Model-2-Amplified-Lecture-001.json` (E4_2019_2022) · window `W0019` · `added_words: [directly, going, rolling]` · note: comparative: 'a very stronger trade idea than if it was to go all way up and fill the Gap'
- Inside a daily gap, he distinguishes lower-half imbalances (better left open) from upper-half imbalances above consequent encroachment.
  > "the ones in the upper half of this Fair Vegas on the daily chart above consequent encroachment I want to see those filled"
  `[U3K3-020]` · `ICT-2023-Mentorship-Analysis-January-25-2023-001.json` (E5_2023_2024) · window `W0029` · `added_words: [distinguishes, gap, inside, left]` · note: comparative ranking of imbalances above vs below CE; [sic-asr] 'Fair Vegas'

## (f) INTERACTIONS
- He contrasts consequent encroachment (the midpoint of a fair value gap) with mean threshold (the middle of an order block).
  > "with order blocks the middle of it we refer to it as mean threshold when we're looking at a fair value Gap"
  `[U3K3-021]` · `ICT-Charter-Price-Action-Model-8-Targeting-6%-Per-Month-001.json` (E4_2019_2022) · window `W0024` · `added_words: [block, contrasts]` · note: terminology distinction between FVG midpoint (CE) and order block midpoint (mean threshold)

## (g) TIMEFRAME
- On the daily timeframe, bodies respecting consequent encroachment of a SIBI frame a swing trade without dropping below the daily chart.
  > "that right there is a swing trade for those of you that don't have the ability to sit and watch day trades"
  `[U3K3-022]` · `ICT-Mentorship-2023-September-27-2023-Market-Review-Commentary-001.json` (E5_2023_2024) · window `W0025` · `added_words: [respecting, sibi, timeframe]` · note: daily timeframe application

## (h) FAILURE / INVALIDATION and DISCRETION
- He judges invalidation by whether candle bodies breach consequent encroachment on a closing basis rather than wicking into it.
  > "it's going down but it won't breach on a closing basis midpoint of that Wick which is consequent encouragement"
  `[U3K3-023]` · `2023-ICT-Mentorship-Deep-Dive-Into-Institutional-Order-Flow-002.json` (E5_2023_2024) · window `W0017` · `added_words: [bodies, candle, invalidation, judges, rather, whether, wicking]` · note: [sic-asr] 'consequent encouragement'; body close vs wick distinction
- When trading through an opposing gap on a 5-minute chart, he requires a candle close above consequent encroachment to trust continuation.
  > "I want to see it close above the consequent encroachment level if this candle can close above it then that to me indicates"
  `[U3K3-024]` · `December-2023-Non-Farm-Payroll-Live-Execution-&-Explanations-001.json` (E1_EARLY_SERIES) · window `W0021` · `added_words: [continuation, gap, opposing, requires, through, trading]` · note: close above CE as continuation confirmation

## (i) VARIANTS (kept parallel, never merged)
- He also measures consequent encroachment as the 50% level of a rejection-block tail (between the candle's open/close and its extreme low).
  > "we're going to get a measurement on the consequent encroachment of that tail okay and what I'm doing is I'm measuring the 50 level"
  `[U3K3-025]` · `ICT-Charter-Price-Action-Model-2-Trade-Plan-&-Algorithmic-Theory-001.json` (E4_2019_2022) · window `W0030` · `added_words: [candle's, close, extreme, measures]` · note: parallel object: CE applied to a fair value gap (W0024), a full candle wick (W0017), or a rejection-block tail (W0030)

## Windows Logged and Read This Session (`±100` words each)
| Window | Era | Match | Transcript | Word Range | SHA-256 (prefix) |
|---|---|---|---|---|---|
| `W0016` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-Forex-Review-January-09-2023-001.json` | `266..467` (201w) | `c224abc24ad3` |
| `W0017` | `E5_2023_2024` | `exact_kept_tsv` | `2023-ICT-Mentorship-Deep-Dive-Into-Institutional-Order-Flow-002.json` | `1573..1774` (201w) | `64996247486f` |
| `W0018` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `NQ-Live-Execution-&-Commentary-Final-Trading-Day-Of-2023-001.json` | `4543..4744` (201w) | `0e24f7f16b11` |
| `W0019` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-2-Amplified-Lecture-001.json` | `9082..9283` (201w) | `3fe1d012a146` |
| `W0020` | `E5_2023_2024` | `exact_kept_tsv` | `February-14-2023-ES-Live-Commentary-CPI-Release-001.json` | `7487..7688` (201w) | `d839ae36bcb3` |
| `W0021` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `December-2023-Non-Farm-Payroll-Live-Execution-&-Explanations-001.json` | `2123..2324` (201w) | `a87428327996` |
| `W0022` | `E4_2019_2022` | `exact_kept_tsv` | `2022-ICT-Mentorship-Ends-Series-Part-4-of-4-001.json` | `5064..5265` (201w) | `e28ffcae4ca6` |
| `W0023` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-Mentorship-2023-Deep-Dive-Into-Institutional-Order-Flow-002.json` | `1573..1774` (201w) | `64996247486f` |
| `W0024` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-8-Targeting-6%-Per-Month-001.json` | `4757..4958` (201w) | `f4e96835c500` |
| `W0025` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-Mentorship-2023-September-27-2023-Market-Review-Commentary-001.json` | `1405..1606` (201w) | `9c5684bb561a` |
| `W0026` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-9-One-Shot-One-Kill-001.json` | `9444..9645` (201w) | `01faa385c57e` |
| `W0027` | `E5_2023_2024` | `exact_kept_tsv` | `Thursday-June-15-2023-ICT-Price-Action-Workshop-002.json` | `4788..4989` (201w) | `6bc9db6bf768` |
| `W0028` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-11-Day-Trading-001.json` | `9119..9320` (201w) | `9e7945f6f83b` |
| `W0029` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-2023-Mentorship-Analysis-January-25-2023-001.json` | `2930..3131` (201w) | `7f1c316cef24` |
| `W0030` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-2-Trade-Plan-&-Algorithmic-Theory-001.json` | `4076..4277` (201w) | `4f8d9e46895a` |
