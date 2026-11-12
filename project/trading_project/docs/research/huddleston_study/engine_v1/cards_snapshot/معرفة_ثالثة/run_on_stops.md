# Understanding card — run on stops (`run_on_stops`)

Windows extracted and read in full (`±100` words) this session: **15** (target 15) across **15** distinct transcripts (`E1_EARLY_SERIES`: 2, `E2_2016`: 4, `E3_2017`: 2, `E4_2019_2022`: 4, `E5_2023_2024`: 3). Meets the 15-window budget.
Claims: U3K3-209, U3K3-210, U3K3-211, U3K3-212, U3K3-213, U3K3-214, U3K3-215, U3K3-216, U3K3-217, U3K3-218, U3K3-219

Every quoted line below is verbatim (≤25 words) from a `±100`-word window logged and read in full this session. Per Rule 2, `statement` in `claims.jsonl` carries the verbatim quote, `reading` carries the interpretation below, and `added_words` lists every word in `reading` absent from the window. Section (c) is explicitly an `ENGINEERING_HYPOTHESIS`, not his words. Empty sections read `NOT_IN_SOURCES`.

## (a) PURPOSE
- He watches the alternation of runs on stops above and below the market to determine which side of the open float the algorithm is drawing toward.
  > "what you're watching for is the tug of war that takes place between each new run on stops below the market and above the market"
  `[U3K3-209]` · `ICT-Mentorship-Core-Content-Month-05-Open-Float-001.json` (E3_2017) · window `W0273` · `added_words: [algorithm, alternation, determine, drawing, runs, toward, watches]` · note: directional-bias purpose of tracking runs on stops

## (b) RECOGNITION (his criteria and his rejections)
- At the 9:30 AM equity open after a consolidation, a rally that sets a high and then spikes above that high a second time is recognized as a run on stops.
  > "after consolidation it runs up creates a high and then runs up again takes out the high that right there is your run on stops"
  `[U3K3-210]` · `2022-ICT-Mentorship-Episode-11-001.json` (E4_2019_2022) · window `W0279` · `added_words: [rally, recognized, second, sets, spikes]` · note: intraday recognition of a 9:30 open run on stops
- After an old low is violated, he waits for price to break back through the intervening swing high to confirm the move below the low was a run on stops.
  > "we have to wait for price to break through that swing high to confirm that there has been a run on stops"
  `[U3K3-211]` · `ICT-Mentorship-Core-Content-Month-04-ICT-Breaker-Block-001.json` (E2_2016) · window `W0277` · `added_words: [intervening, move, waits]` · note: structural confirmation of a run on stops via breaker swing high violation
- On the final accelerated leg into Terminus (within 10–30 pips of target), he rejects expecting a deep retracement or a run on stops before Terminus is reached.
  > "generally they don't want to have a run on stops and this will be the last push in that price move"
  `[U3K3-212]` · `ICT-Charter-Price-Action-Model-6-Amplified-Lesson-001.json` (E4_2019_2022) · window `W0274` · `added_words: [deep, expecting, final, leg, reached, rejects, retracement, target]` · note: REJECTION of expecting a stop run during the final accelerated leg into Terminus

## (c) OBSERVABLES — ENGINEERING_HYPOTHESIS (needs owner approval)
- price trading beyond a prior single or double swing high/low (or equilibrium consolidation extreme) to trigger resting stops, discriminated into a reversal stop-run when price rapidly rejects back across the swept level and breaks the intervening swing point (breaker), versus continuation when price accelerates away
  `candle_observable: true` · derived from `U3K3-216`, `U3K3-211`, `U3K3-210`, `U3K3-213`, `U3K3-215`, `U3K3-218` · **ENGINEERING_HYPOTHESIS — needs owner approval**
- distinguishing a Wednesday sweep of trailed stops from a genuine bearish market structure break depends on the weekly accumulation narrative and Dollar Index SMT
  `candle_observable: false` · derived from `U3K3-219` · **ENGINEERING_HYPOTHESIS — needs owner approval**

## (d) HOW HE TREATS IT
- When bearish, he sells short into the run on stops above an old high or double top during a Killzone and covers when an opposing old low is violated.
  > "you want to be a a short seller above when you're bearish above a old high or double top selling short there"
  `[U3K3-213]` · `ICT-Charter-Price-Action-Model-10-Swing-Trading-001.json` (E4_2019_2022) · window `W0282` · `added_words: [covers, killzone, opposing, sells]` · note: execution rule for fading a run on stops; [sic-asr] 'lad' for 'low'
- When scalping a run on stops, he takes partial profits along the way to reduce risk before the market reverses after sweeping the stops.
  > "I profited along the way taking out small portions because you never know you never know if it's gonna go down to your objective"
  `[U3K3-214]` · `ICT-Forex-What-New-Traders-Should-Focus-On-001.json` (E1_EARLY_SERIES) · window `W0276` · `added_words: [market, partial, profits, reduce, reverses, scalping, sweeping, takes]` · note: risk-reduction scaling during a run-on-stops scalp

## (e) COMPARING INSTANCES
- A run on stops does not require a textbook double top or double bottom; running a single high or single low in alignment with bias is equally valid.
  > "it doesn't rather require double tops or double bottoms it could be a single high and single low that it run stops on"
  `[U3K3-215]` · `ICT-Charter-Price-Action-Model-10-Swing-Trading-001.json` (E4_2019_2022) · window `W0282` · `added_words: [alignment, equally, running, textbook, valid]` · note: comparative equivalence: single high/low vs double top/bottom stop run

## (f) INTERACTIONS
- At the 50% equilibrium of a dealing range, he expects a run on stops (often sweeping twice) that returns into an inversion fair value gap and reclaimed order block.
  > "equilibrium is where you're going to anticipate you're going to predict you're going to expect a stop hunt that's what the algorithm will do"
  `[U3K3-216]` · `2023-ICT-Mentorship-Deep-Dive-Into-Institutional-Order-Flow-002.json` (E5_2023_2024) · window `W0275` · `added_words: [dealing, expects, often, returns, sweeping, twice]` · note: interaction of run on stops with dealing-range equilibrium, inversion FVG, and reclaimed OB

## (g) TIMEFRAME
- Intraday, the post-midnight Judas swing in London (and the 9:30–10:30 AM NY opening range in futures, W0278) is the primary daily time window for a run on stops.
  > "it's making the higher low in london that's the london swing for a reversal that's a run on stops"
  `[U3K3-217]` · `ICT-Mentorship-Core-Content-Month-1-How-Market-Makers-Condition-The-Market-001.json` (E2_2016) · window `W0281` · `added_words: [futures, judas, opening, post, primary, w0278, window]` · note: session timing of intraday runs on stops

## (h) FAILURE / INVALIDATION and DISCRETION
- When price sweeps below a dealing-range low, if it fails to reject back inside and instead accelerates down treating the breaker as an inversion level, he abandons the bullish stop-run thesis.
  > "do we view it as a run on stops that rejects and goes back above here or does it accelerate down"
  `[U3K3-218]` · `April-13-2023-Live-Tape-Reading-Emini-S&P-AM-Session-002.json` (E5_2023_2024) · window `W0283` · `added_words: [abandons, accelerates, bullish, fails, instead, reject, stop, sweeps, thesis, treating]` · note: invalidation of a stop-run reversal thesis when price accelerates instead of rejecting

## (i) VARIANTS (kept parallel, never merged)
- He distinguishes between (1) a false-breakout run on stops against retail breakouts (W0284), (2) an intra-week wick sweep of trailed stops in trend direction (W0285), and (3) a scalp targeting the stop pool itself (W0276).
  > "Wednesday we have a run on stops from Tuesday's trading on that week that is not a market structure break to the downside"
  `[U3K3-219]` · `ICT-Charter-Price-Action-Model-6-2-Amplified-Lesson-001.json` (E4_2019_2022) · window `W0285` · `added_words: [against, breakout, breakouts, direction, distinguishes, false, intra, itself, pool, scalp, sweep, targeting, trend, w0276, w0284, w0285]` · note: three parallel operational contexts for a run on stops

## Windows Logged and Read This Session (`±100` words each)
| Window | Era | Match | Transcript | Word Range | SHA-256 (prefix) |
|---|---|---|---|---|---|
| `W0271` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-Forex-Understanding-The-ICT-Judas-Swing-001.json` | `4..205` (201w) | `a62b3e471b29` |
| `W0272` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-03-Timeframe-Selection-&-Defining-Setups-001.json` | `8272..8473` (201w) | `226c3232a82c` |
| `W0273` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-05-Open-Float-001.json` | `2277..2478` (201w) | `50c77a3c28ea` |
| `W0274` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-6-Amplified-Lesson-001.json` | `4942..5143` (201w) | `fa8e2c2c6564` |
| `W0275` | `E5_2023_2024` | `exact_kept_tsv` | `2023-ICT-Mentorship-Deep-Dive-Into-Institutional-Order-Flow-002.json` | `5997..6198` (201w) | `64996247486f` |
| `W0276` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-Forex-What-New-Traders-Should-Focus-On-001.json` | `4207..4365` (158w) | `89c6c751b589` |
| `W0277` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-04-ICT-Breaker-Block-001.json` | `646..847` (201w) | `39bbfc0cfc89` |
| `W0278` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-10-Index-Futures-Basics-&-Opening-Range-Concept-001.json` | `386..587` (201w) | `df442b0186e9` |
| `W0279` | `E4_2019_2022` | `exact_kept_tsv` | `2022-ICT-Mentorship-Episode-11-001.json` | `4029..4230` (201w) | `e7439d9cd50f` |
| `W0280` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-Mentorship-2023-Deep-Dive-Into-Institutional-Order-Flow-002.json` | `5997..6198` (201w) | `64996247486f` |
| `W0281` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-1-How-Market-Makers-Condition-The-Market-001.json` | `2144..2345` (201w) | `5aa74c544fb0` |
| `W0282` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-10-Swing-Trading-001.json` | `2631..2832` (201w) | `32af78246341` |
| `W0283` | `E5_2023_2024` | `exact_kept_tsv` | `April-13-2023-Live-Tape-Reading-Emini-S&P-AM-Session-002.json` | `8100..8301` (201w) | `7a0e7c95b328` |
| `W0284` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-03-Institutional-Market-Structure-001.json` | `1215..1416` (201w) | `18b779be4dc2` |
| `W0285` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-6-2-Amplified-Lesson-001.json` | `5096..5297` (201w) | `7d82a845c710` |
