# L — Open questions: exact, computable definitions (external search)

**Search run:** 2026-11-08 (UTC). **Base:** `engine_v1/`. **Companion:** `RESEARCH_QUESTIONS_L.md`.
**Layer:** every record here is `TIER2`. No record is a claim by Michael Huddleston unless the page itself
attributes a timestamped quote to him.

**Rules applied to this file**

- No market data, no 2023 data, no code analysis, no pandas. No page dated after 2025-04-30 is used as
  market data; such pages are used only as web text.
- No judgement, ranking, averaging or selection between numbers. Counts only.
- `QUOTE_VERIFIED` = the quoted words were read on the fetched page in this run.
  `QUOTE_NOT_VERIFIED` / `SNIPPET_ONLY` = the words came from a search-result snippet and were **not** read
  on the page; such a record never enters a counts table.
- "HOW_MANY_CANDLES", "TIMEFRAME", "INSTRUMENT" = `UNSTATED` wherever the page is silent. No gap is filled in.
- **Independence.** INDEPENDENT means the domain/publisher is not already listed in `external_sources/` or
  `EXTERNAL_SOURCES_LOG.md`. Prior-inventory domains are listed in the appendix to this file. A record from a
  prior domain is marked `NOT_INDEPENDENT_OF_<prior id>` where the id is known, else
  `NOT_INDEPENDENT_OF_PRIOR_SOURCES`.
- **GitHub rule.** Code we actually read is typed `IMPLEMENTATION_CODE` with repo + commit hash + file + lines.
  No code is copied. `IMPLEMENTATION_CODE` records are **never** counted in a TEACHING counts table.
- Pages from the same publisher are identified as non-independent of one another.

---

# Q1 — Displacement

Q1 (f) is answered first, because it sets what the rest of Q1 may count.

## Q1(f) — Re-opened internal evidence (F1, F2, F5, F3, F4, F6): denominator and baseline

Source of these records: `external_sources/f_displacement.md`, re-opened 2026-11-08. The quotes below are the
ones that file records as `QUOTE_VERIFIED`; they were **not** re-fetched in this run, so they carry the status
`QUOTE_VERIFIED_IN_PRIOR_ROUND` and are **not** counted as new independent publishers. They are re-read here
only to extract denominator and baseline, which is what Q1(f) asks.

| re-opened id | quote carried in `f_displacement.md` | DENOMINATOR (of what the % is taken) | BASELINE (compared to what) | HOW_MANY_CANDLES |
|---|---|---|---|---|
| F1 | "A large candle body, representing 60 to 80 percent or more of the total candle range" | candle **body** ÷ **total candle range** (high→low, wicks included) | none stated; the page's own contrast is a "regular impulse" at "40 to 60%" | UNSTATED (one candle implied by "a large candle body") |
| F2 | "body-to-range ratio above ~75%" | body ÷ total range | "at minimum 2x the average recent candle, often 3–5x" — second, separate baseline | "the 3–5 candles that preceded it" |
| F5 | "The candle bodies should be at least two to three times the average body of the previous ten candles" | **body** (absolute size, not a ratio) | **average body of the previous ten candles** | **10** |
| F3 | "a large-bodied candle with small wicks relative to its body, closing at or near its extreme" | UNSTATED — no percentage | UNSTATED — "no universal rule for how large a candle must be" | UNSTATED |
| F4 | "with bodies that stand out against the recent bars" | body ÷ full high-to-low range, but only inside constructed examples (5% / 81.8%) | "median body of your chosen preceding sample" — sample size is chosen by the trader, not stated by the page | UNSTATED (page: "Record how many preceding candles you use") |
| F6 | "it's got to be energetic, it can't be a little lethargic little move" | UNSTATED | UNSTATED | UNSTATED |

**Q1(f) result.** Of the six re-opened sources: **3 state a denominator** (F1, F2, F4 — all
body ÷ total range), **1 states a body-size baseline with a stated window of 10** (F5), **1 states a range
baseline with a stated window of 3–5** (F2), and **3 have no number at all** (F3, F6, and F4's own text which
explicitly refuses a threshold). No source among F1–F6 states a 14-period ATR baseline. That baseline appears
only in the new material recorded below.

## Q1(a)–(e) — records

### Q1-01 — Quantum Algo (glossary)
- id: Q1-01
- question: Q1 (a)(b)(c)(d)
- URL: https://www.quantum-algo.com/glossary/displacement/
- publisher: quantum-algo.com (QuantumAlgo)
- author if shown: "By ILY · Reviewed by Quant"
- page date if shown: "Published April 30, 2026"
- type: TEACHING
- quote (<=25 words, English, verbatim): "typically at least 1.5 times the average true range (ATR) of the prior 14 candles" — QUOTE_VERIFIED
- number and unit: 1.5 (multiple, dimensionless)
- OF_WHAT: the candle **body** ("A body of 1.5×ATR or larger qualifies as displacement" — QUOTE_VERIFIED, same page, FAQ)
- COMPARED_TO_WHAT: ATR, period 14
- HOW_MANY_CANDLES: 14 (the ATR lookback); the displacement itself is "one or more candles"
- TIMEFRAME: UNSTATED ("Displacement is relative to recent volatility, not an absolute number of pips or dollars" — QUOTE_VERIFIED)
- INSTRUMENT: UNSTATED (worked example uses gold, unlabelled as a rule)
- independence: NOT_INDEPENDENT_OF_PRIOR_SOURCES — quantum-algo.com is already listed in `EXTERNAL_SOURCES_LOG.md` (I3, and the 2022-model model record)
- reason given by source: "Displacement is relative to recent volatility, not an absolute number of pips or dollars" — QUOTE_VERIFIED
- tier: TIER2
- Q1(e): FVG required — "The move should leave a fair value gap behind" (QUOTE_VERIFIED); swing break — "the move usually breaks structure" (QUOTE_VERIFIED; "usually", not "must").

### Q1-02 — FundingPips
- id: Q1-02
- question: Q1 (a)(b)(c)(d)(e)
- URL: https://fundingpips.com/blog/ict-2022-model
- publisher: fundingpips.com (FundingPips)
- author if shown: "By FundingPips" (no individual)
- page date if shown: "October 18, 2026"
- type: TEACHING
- quote (<=25 words, English, verbatim): "require the main displacement candle's body to be at least 1.5 times the 14-period Average True Range" — QUOTE_VERIFIED
- number and unit: 1.5 (multiple)
- OF_WHAT: "the main displacement candle's body"
- COMPARED_TO_WHAT: "14-period Average True Range (ATR) on the execution timeframe"
- HOW_MANY_CANDLES: 14 (ATR window); the displacement is "one or more large-bodied candles"
- TIMEFRAME: "the execution timeframe" (named, not fixed) — QUOTE_VERIFIED
- INSTRUMENT: forex ("clear, testable rules for forex pairs")
- independence: INDEPENDENT_OF_PRIOR_SOURCES — fundingpips.com does not appear in `external_sources/` or `EXTERNAL_SOURCES_LOG.md`
- reason given by source: "The exact multiple is a choice to test, but having a number removes guesswork" — QUOTE_VERIFIED
- tier: TIER2
- Q1(e): neither the FVG nor the swing break is required *by* displacement here; both are separate later steps of the four-step model.

### Q1-03 — ICTKillzone (displacement guide)
- id: Q1-03
- question: Q1 (a)(b)(c)(d)(e)
- URL: https://www.ictkillzone.com/ict-displacement
- publisher: ictkillzone.com
- author if shown: "Michael Phillips"
- page date if shown: "Updated September 2026"
- type: TEACHING
- quote (<=25 words, English, verbatim): "The rule of thumb: body-to-range ratio above ~75%." — QUOTE_VERIFIED
- number and unit: ~75 (percent)
- OF_WHAT: candle **body ÷ total range** (high to low)
- COMPARED_TO_WHAT: none — an absolute ratio on the single candle
- HOW_MANY_CANDLES: 1 (the candle being graded)
- TIMEFRAME: UNSTATED; the page's example is 5-minute NQ
- INSTRUMENT: UNSTATED; worked examples are NQ
- independence: NOT_INDEPENDENT_OF_F2 — same page and publisher as F2 in `external_sources/f_displacement.md`
- reason given by source: "A 95% body ratio means price moved in one direction for nearly the entire candle duration" — QUOTE_VERIFIED
- tier: TIER2
- same page, a **second body-to-range version**, read verbatim in this run: "Above 75% = A-tier. Below 60% = reduce or skip." — QUOTE_VERIFIED. This is a **floor of 60%**, distinct from the 75% "A-tier" line and distinct from F1/ictflow's "60–80%" band. Counted as its own row below.
- same page, second number: "the candle's range should be at minimum 2x the average recent candle, often 3–5x" (QUOTE_VERIFIED). OF_WHAT: candle **range**. COMPARED_TO_WHAT: "the average recent candle". HOW_MANY_CANDLES: "the 3–5 candles that preceded it". This is a *different exact version* from the 75% ratio and is counted separately below.
- Q1(d) on this page: displacement may be "a rapid sequence of 2–3 candles" (QUOTE_VERIFIED) — so 1–3 candles.
- Q1(e) on this page: the FVG is stated as required ("Without displacement there is no FVG", and displacement is described as creating the FVG), and the MSS is a separate confirmation, not a requirement of displacement itself.

### Q1-04 — ICT Flow
- id: Q1-04
- question: Q1 (a)(b)(c)(d)
- URL: https://ictflow.com/blog/ict-displacement-move-explained
- publisher: ictflow.com (ICT Flow)
- author if shown: UNSTATED (no byline in the fetched text)
- page date if shown: "May 10, 2026"
- type: TEACHING
- quote (<=25 words, English, verbatim): "the body (open to close) represents 60-80% or more of the total candle range (high to low)" — QUOTE_VERIFIED
- number and unit: 60–80 (percent), with a floor of 60 in the checklist: "Body should represent at least 60% of the total candle range" (QUOTE_VERIFIED)
- OF_WHAT: body (open→close) ÷ total candle range (high→low)
- COMPARED_TO_WHAT: none numeric for the ratio; separately, "Compare the displacement candles to the 10 candles before them" (QUOTE_VERIFIED) with no multiplier given
- HOW_MANY_CANDLES: 10 for the size comparison (no multiplier stated); displacement itself is "a series of candles"
- TIMEFRAME: UNSTATED
- INSTRUMENT: UNSTATED
- independence: INDEPENDENT_OF_PRIOR_SOURCES — ictflow.com is not in either prior list
- reason given by source: NO_REASON_GIVEN (the page gives institutional narrative, not a reason for the numbers)
- tier: TIER2
- Q1(e): FVG yes ("Every valid FVG requires displacement" and an FVG is listed inside the sequence); swing break not required by the displacement definition itself.

### Q1-05 — Forex MT4 Systems
- id: Q1-05
- question: Q1 (a)(b)(c)(d)(e)
- URL: https://forexmt4systems.com/education/smart-money-concepts/displacement-in-trading/
- publisher: forexmt4systems.com
- author if shown: "Dominic Walsh"
- page date if shown: "Published 23 Jul 2026 · Last updated 21 Sep 2026"
- type: TEACHING
- quote (<=25 words, English, verbatim): "The candle bodies should be at least two to three times the average body of the previous ten candles" — QUOTE_VERIFIED
- number and unit: 2–3 (multiple)
- OF_WHAT: candle **body** (absolute size)
- COMPARED_TO_WHAT: "the average body of the previous ten candles"
- HOW_MANY_CANDLES: 10
- TIMEFRAME: UNSTATED; the worked example is GBPUSD H1 dated 2026-07-21
- INSTRUMENT: GBPUSD (worked example only)
- independence: NOT_INDEPENDENT_OF_F5 — same page and publisher as F5
- reason given by source: "Always scale your test to the pair and the session at hand. The ten-candle body average does this for you" — QUOTE_VERIFIED
- tier: TIER2
- Q1(d): "one to three candles in a row with large bodies" — QUOTE_VERIFIED (so 1–3)
- Q1(e): FVG required ("A fair value gap forms … No gap suggests no urgency"); swing break required ("A level breaks … with a body close beyond it") — both QUOTE_VERIFIED as numbered tests on the page.

### Q1-06 — FXNX
- id: Q1-06
- question: Q1 (a)(b)(c)
- URL: https://fxnx.com/en/blog/ict-displacement-spotting-signature-smart-money
- publisher: fxnx.com (FXNX)
- author if shown: "Raj Krishnamurthy"
- page date if shown: "February 18, 2026"
- type: TEACHING
- quote (<=25 words, English, verbatim): "Look for candles where the body makes up at least 80% of the total candle range." — QUOTE_VERIFIED
- number and unit: 80 (percent)
- OF_WHAT: body ÷ total candle range
- COMPARED_TO_WHAT: none for the ratio; a second, separate comparison is "the average candle size for the last 20 periods" with no multiplier stated
- HOW_MANY_CANDLES: 20 (for the size comparison only)
- TIMEFRAME: UNSTATED; example is EUR/USD 15-minute
- INSTRUMENT: EUR/USD / GBP/USD (examples)
- independence: NOT_INDEPENDENT_OF_K4 (same publisher as `external_sources/k_equal_highs.md` K4/K5); fxnx.com is already in `external_sources/`
- reason given by source: "This signals that the move was one-sided and committed" — QUOTE_VERIFIED
- tier: TIER2

### Q1-07 — Inner Circle Trader (displacement move)
- id: Q1-07
- question: Q1 (d)(e)
- URL: https://innercircletrader.net/tutorials/ict-displacement-move/
- publisher: innercircletrader.net
- author if shown: "Ayub Rana" (site owner byline)
- page date if shown: UNSTATED
- type: TEACHING
- quote (<=25 words, English, verbatim): "At least three consecutive same-direction candles with large bodies." — QUOTE_VERIFIED
- number and unit: >=3 (count of candles)
- OF_WHAT: not a size measure — a candle **count**
- COMPARED_TO_WHAT: UNSTATED (no size threshold given; "large bodies" is not quantified)
- HOW_MANY_CANDLES: 3 (minimum)
- TIMEFRAME: UNSTATED
- INSTRUMENT: UNSTATED
- independence: NOT_INDEPENDENT_OF_B1 — innercircletrader.net is already in `external_sources/` (B1, C4, D1, I4)
- reason given by source: NO_REASON_GIVEN
- tier: TIER2
- Q1(e): FVG required ("A fair value gap somewhere between those candles"); swing break not stated as a requirement.

### Q1-08 — Bullynx
- id: Q1-08
- question: Q1 (a)
- URL: https://bullynx.com/blog/displacement-in-trading
- publisher: bullynx.com
- author if shown: UNSTATED
- page date if shown: UNSTATED
- type: NO_NUMBER
- quote (<=25 words, English, verbatim): "There is no universal rule for how large a candle must be or how fast a move must travel" — QUOTE_VERIFIED
- number and unit: NONE
- OF_WHAT: UNSTATED
- COMPARED_TO_WHAT: UNSTATED
- HOW_MANY_CANDLES: UNSTATED
- TIMEFRAME: UNSTATED
- INSTRUMENT: UNSTATED
- independence: NOT_INDEPENDENT_OF_F3 — same publisher as F3
- reason given by source: "It is a descriptive concept, subjective to judge, with no guaranteed edge" — QUOTE_VERIFIED
- tier: TIER2

### Q1-09 — HomeDadPro
- id: Q1-09
- question: Q1 (a)(b)(c)
- URL: https://homedadpro.com/en/displacement-trading/
- publisher: homedadpro.com
- author if shown: "Yang"
- page date if shown: "Updated October 23, 2026"
- type: NO_NUMBER (numbers present only inside declared constructed examples)
- quote (<=25 words, English, verbatim): "They are not a rule that 80% qualifies while 79% fails." — QUOTE_VERIFIED
- number and unit: NONE as a rule (5% and 81.8% are labelled constructed examples)
- OF_WHAT: UNSTATED
- COMPARED_TO_WHAT: (of the examples) "the median body of your chosen preceding sample"
- HOW_MANY_CANDLES: UNSTATED — the page tells the reader to choose and record it
- TIMEFRAME: "The comparison belongs to the same instrument and timeframe" (QUOTE_VERIFIED) — no value given
- INSTRUMENT: MNQ charts shown (MNQZ24 four-hour), no rule stated for an instrument
- independence: NOT_INDEPENDENT_OF_F4 — same publisher as F4
- reason given by source: "If you want a mechanical body-size filter, define it before testing" — QUOTE_VERIFIED
- tier: TIER2

### Q1-10 — Quarter Sequence ("The Study")
- id: Q1-10
- question: Q1 (a)
- URL: https://quartersequence.com/the-study/ict-market-structure/
- publisher: quartersequence.com
- author if shown: UNSTATED
- page date if shown: UNSTATED (site "Coming soon" markers on other pages)
- type: NO_NUMBER
- quote (<=25 words, English, verbatim): "A swing high is three candles where the middle one has the highest high" — QUOTE_VERIFIED (this is the swing rule, recorded here only because the page's MSS depends on it; the page states no displacement number)
- number and unit: NONE for displacement
- OF_WHAT: UNSTATED
- COMPARED_TO_WHAT: UNSTATED
- HOW_MANY_CANDLES: 3 (swing rule only)
- TIMEFRAME: UNSTATED
- INSTRUMENT: UNSTATED
- independence: NOT_INDEPENDENT_OF_F6 — same publisher as F6
- reason given by source: NO_REASON_GIVEN
- tier: TIER2

### Q1-11 — ICTKillzone (order block, criterion 2)
- id: Q1-11
- question: Q1 (a)(b)(c)
- URL: https://www.ictkillzone.com/ict-order-block
- publisher: ictkillzone.com
- author if shown: "Michael Phillips"
- page date if shown: UNSTATED in the fetched text (prior file records 2026-05-05)
- type: TEACHING — **NOT a displacement definition** (the 1.5×-consolidation figure is an order-block entry criterion, not a definition of displacement)
- quote (<=25 words, English, verbatim): "the displacement candle should be at least 1.5x the average size of the candles in the preceding consolidation" — QUOTE_VERIFIED
- number and unit: 1.5 (multiple); plus "the wick should be less than 25% of the total candle range" (QUOTE_VERIFIED)
- OF_WHAT: candle **size** (the page does not say body or range for the 1.5×) and wick ÷ total range for the 25%
- COMPARED_TO_WHAT: "the average size of the candles in the preceding consolidation" — the length of that consolidation is UNSTATED
- HOW_MANY_CANDLES: UNSTATED (the consolidation's length is not fixed)
- TIMEFRAME: UNSTATED
- INSTRUMENT: UNSTATED; example is NQ
- independence: NOT_INDEPENDENT_OF_F2 (same publisher and same page as Q1-03's publisher)
- reason given by source: NO_REASON_GIVEN
- tier: TIER2

### Q1-12 — Backtrex (liquidity sweep backtest rules)
- id: Q1-12
- question: Q1 (a)(b)(c)(d)
- URL: https://backtrex.com/en/blog/liquidity-sweep-strategy-backtest-results
- publisher: backtrex.com
- author if shown: UNSTATED
- page date if shown: UNSTATED (search metadata 2026-10-03)
- type: TEACHING — **NOT a displacement definition** (the 70% rule is a mechanical entry filter from a backtest-results page, not a definition of displacement)
- quote (<=25 words, English, verbatim): "a decisive closing candle (body covering at least 70% of the candle range) pushes in the opposite direction within 2 candles" — QUOTE_VERIFIED
- number and unit: 70 (percent); 2 (candles)
- OF_WHAT: body ÷ candle range
- COMPARED_TO_WHAT: none
- HOW_MANY_CANDLES: the displacement must occur "within 2 candles following the sweep"
- TIMEFRAME: H1 (sweep level identified on H1), FVG allowed on "H1 or M15"
- INSTRUMENT: EURUSD and XAUUSD
- independence: NOT_INDEPENDENT_OF_F1 — same publisher as F1
- reason given by source: "Displacement confirmation (70% minimum candle body): reduces false signals by 23%" — QUOTE_VERIFIED
- tier: TIER2

### Q1-13 — ICTKillzone (2022 model)
- id: Q1-13
- question: Q1 (a)(d)
- URL: https://www.ictkillzone.com/ict-2022-model
- publisher: ictkillzone.com
- author if shown: "Michael Phillips"
- page date if shown: "Published May 2026 · Updated 29 September 2026"
- type: NO_NUMBER
- quote (<=25 words, English, verbatim): "What qualifies is judged by eye, not by a formula" — QUOTE_VERIFIED
- number and unit: NONE
- OF_WHAT: UNSTATED
- COMPARED_TO_WHAT: "one or more large-bodied candles closing decisively beyond nearby structure" — no numeric baseline
- HOW_MANY_CANDLES: "one or more" (QUOTE_VERIFIED)
- TIMEFRAME: the page's setup charts are 1H/15m/5m; execution 5m/3m/1m — presented as "common practice, not a rule"
- INSTRUMENT: UNSTATED; illustrative NQ plan
- independence: NOT_INDEPENDENT_OF_F2 (same publisher)
- reason given by source: NO_REASON_GIVEN
- tier: TIER2

### Q1 — IMPLEMENTATION_CODE (not counted as teaching)

- **Q1-C1** — repo `joshyattridge/smart-money-concepts`, commit `1b62fd6c41e1f508e7ed76831a039fa4c82d42f6`, file
  `smartmoneyconcepts/smc.py`, lines 137–160 (`swing_highs_lows`) and 404–545 (`ob`). License: MIT (repo metadata).
  In our own words (<=25): swing pivot needs the current high to equal the rolling max of a symmetric window; order
  blocks are volume-weighted, with a `Percentage` strength field. Numeric constants: `swing_length: int = 50`
  (window = 2×50+1 = 101 bars); `percentage[obIndex] = min(highVolume, lowVolume) / max_vol * 100.0`.
  No displacement threshold of any kind exists in this file — `IMPLEMENTATION_CODE`, NO_NUMBER for displacement.
- **Q1-C2** — repo `Vatthu/v1indicators`, commit `36785b982e55c4dfed20037e52fd92dbdf8f7f19`, file
  `v1indicators/foundational/trend/order_blocks.py`, lines 7–71. License: MIT (repo metadata).
  In our own words (<=25): bullish OB requires the last bearish candle followed by `periods` consecutive bullish
  candles and a percent move at least equal to `threshold`. Numeric constants: `periods: int = 5`,
  `threshold: float = 0.0`, `use_wicks: bool = False`; displacement formula
  `((close[t-(periods+1)] - close[t-1]).abs() / close[t-(periods+1)]) * 100.0`. So the code's baseline is
  **close-to-close percent move**, not a body/range ratio and not ATR.
- **Q1-C3** — repo `kxngHADES/SMC-Marking`, commit `bb79d1dc6f945cdce043e243e28ba6e7b9599e8f` (2026-09-29), file
  `SMC_Terminology_marks.pine`, blob `69b2eadb60d1ee6b13f1c066db8573d6063d2da3`, 569 lines. License: **none visible**
  in the repo contents listing (no `LICENSE` file; the repo API returns `license: null`). In our own words (<=25):
  a "market structure period" sets how many bars must sit either side of a swing, and a break can be confirmed by
  close or by wick, chosen by input. Numeric constants: `swingLen = input.int(10, "Market Structure Period")`;
  `intLen = input.int(5, "Internal Structure Period")`; `breakSrc` options `["Close", "Wick"]`, default `"Close"`;
  `atrv = ta.atr(200)`. **Displacement:** the file has no displacement threshold — it marks structure, order
  blocks, FVGs, EQH/EQL and premium/discount only. `IMPLEMENTATION_CODE`, NO_NUMBER for displacement.
- **Q1-C4** — repo `kayasolomon/poi-liquidity-detector`, commit `951304b33c71ad6fedcabf957de6ab40134d5670` (2026-07-15),
  file `src/detector.ts`, blob `a214f3a0e67f83c2e9aa51ad7c7658d76e30a78c`, lines 195–220 + defaults at 51–58.
  License: MIT. In our own words (<=25): after a structure break, the nearest opposing-body candle within a lookback
  window is kept only if the distance from that candle's body edge to the break price is large enough in ATRs.
  Numeric constants: `minImpulseATR: 1.5` (default), `atrPeriod: 14`, `obLookback: 20`, `fractalK: 2`,
  and the test `impulseATR = (breakPrice - bodyEdge) / ATR(14)` rejected when `< minImpulseATR`.
  This is the **only implementation found whose "displacement" baseline is ATR and whose OF_WHAT is the
  break-price-to-body-edge distance** rather than a single candle's body or range.

## Q1 — Counts (TEACHING only; exact versions)

| exact version (number | OF_WHAT | COMPARED_TO_WHAT) | independent publishers | of which new to this file |
|---|---|---|---|
| body >= 1.5 × ATR(14) | candle body | ATR period 14 | 2 (Q1-01 quantum-algo, Q1-02 fundingpips) | 1 (Q1-02) |
| body-to-range >= 60% floor ("60–80% or more", "at least 60%", "below 60% = reduce or skip") | body ÷ full high-low range | none | 3 (F1/Q1-12 backtrex, Q1-04 ictflow, Q1-03 ictkillzone) | 1 (Q1-04) |
| body-to-range ~75% | body ÷ full range | none | 1 (Q1-03 ictkillzone) | 0 |
| candle range >= 2× average recent candle | candle range | average of the 3–5 preceding candles | 1 (Q1-03 ictkillzone) | 0 |
| bodies 2–3× average body of previous 10 | candle body | average body, 10 candles | 1 (Q1-05 forexmt4systems) | 0 |
| body-to-range >= 80% | body ÷ full range | none | 1 (Q1-06 fxnx) | 0 |
| body >= 70%, within 2 candles of a sweep — **NOT displacement definition** (S-BTX-SWP / Q1-12: backtest-results page) | body ÷ range | none | 1 (Q1-12 backtrex) | 0 |
| size >= 1.5× preceding consolidation average, wick < 25% of range — **NOT displacement definition** (S-KZ-OB / Q1-11: order-block criterion) | candle size / wick ÷ range | average size of preceding consolidation (length UNSTATED) | 1 (Q1-11 ictkillzone) | 0 |
| candle count >= 3 consecutive same-direction | candle count | none | 1 (Q1-07 innercircletrader) | 0 |

**Q1 totals (counts only):** 9 distinct numeric exact versions among 8 publishers; 4 publishers state no number
at all for displacement (F3/Q1-08, F4/Q1-09, F6/Q1-10, Q1-13). No two publishers share an identical
(number, OF_WHAT, COMPARED_TO_WHAT) triple except the 60–80% body-to-range pair (backtrex and ictflow), which is
2 publishers and 1 new. Two of the nine versions are marked **NOT displacement definitions** above: Q1-12 (backtest-results page)
and Q1-11 (order-block criterion); excluding those two rows leaves 7 versions.

### Q1 — pages checked (16)

| page | outcome |
|---|---|
| https://backtrex.com/en/blog/ict-displacement-candle-market-concept | Q1-12 / F1 — number found |
| https://www.ictkillzone.com/ict-displacement | Q1-03 — two numbers found |
| https://www.quantum-algo.com/glossary/displacement/ | Q1-01 — number found |
| https://innercircletrader.net/tutorials/ict-displacement-move/ | Q1-07 — count only |
| https://homedadpro.com/en/displacement-trading/ | Q1-09 — NO_NUMBER |
| https://forexmt4systems.com/education/smart-money-concepts/displacement-in-trading/ | Q1-05 — number found |
| https://ictflow.com/blog/ict-displacement-move-explained | Q1-04 — number found |
| https://fundingpips.com/blog/ict-2022-model | Q1-02 — number found |
| https://fxnx.com/en/blog/ict-displacement-spotting-signature-smart-money | Q1-06 — number found |
| https://bullynx.com/blog/displacement-in-trading | Q1-08 — NO_NUMBER |
| https://quartersequence.com/the-study/ict-market-structure/ | Q1-10 — NO_NUMBER |
| https://www.ictkillzone.com/ict-2022-model | Q1-13 — NO_NUMBER ("judged by eye") |
| https://www.ictkillzone.com/ict-order-block | Q1-11 — number found (NOT displacement definition: order-block criterion) |
| https://backtrex.com/en/blog/liquidity-sweep-strategy-backtest-results | Q1-12 — number found (NOT displacement definition: backtest-results page) |
| https://fibalgo.com/library/ict-displacement (and TradingView port) | SNIPPET_ONLY — ATR(14)×1.5 default and body/range 65% default seen only in a search snippet; **not fetched**, not counted |
| https://www.tradingview.com/script/9OYOAKNU-FibAlgo-ICT-Displacement/ | NOT_FETCHED (search snippet only) |

---

# Q2 — Liquidity sweep, "price returns quickly"

## Q2(a) — how many candles may pass before price is back inside

### Q2-01 — LiquidityScan
- id: Q2-01
- question: Q2 (a)(b)(c)
- URL: https://liquidityscan.io/blog/liquidity-sweep-vs-liquidity-grab-is-there-a-difference
- publisher: liquidityscan.io
- author if shown: "Hayk Muradian"
- page date if shown: "July 12, 2026"
- type: TEACHING
- quote (<=25 words, English, verbatim): "the sweep candle itself, or one within the next one to three candles, closes back inside the prior range" — QUOTE_VERIFIED
- number and unit: 1–3 (candles); strictest reading = the sweep candle itself
- OF_WHAT: candle **close** position relative to the prior range
- COMPARED_TO_WHAT: the prior range (the level), not a size
- HOW_MANY_CANDLES: 1–3 after the sweep (0 = same candle, allowed as "strictest")
- TIMEFRAME: "on the timeframe that defines the level" — QUOTE_VERIFIED
- INSTRUMENT: UNSTATED; examples EURUSD and a 4H crypto case
- independence: NOT_INDEPENDENT_OF_PRIOR_SOURCES — liquidityscan.io is in both prior lists (A1, K12)
- reason given by source: "The longer price holds beyond the level, the more the market is demonstrating acceptance" — QUOTE_VERIFIED
- tier: TIER2
- Q2(b): a **close** back inside is required; a wick alone is not enough — "A wick that pokes back inside the range but closes beyond it still counts as a successful breakout" appears on the sister page (fortraders), not here. Here: "a sweep is only a sweep after the reclaim close" (QUOTE_VERIFIED).
- Q2(c): levels listed = "Equal Highs (EQH) and Equal Lows (EQL), the prior day's high and low, the prior week's high and low, session extremes such as the Asia range, and clean swing points" (QUOTE_VERIFIED) — all five classes accepted, no priority stated.

### Q2-02 — Oshi Academy (Tradoshi)
- id: Q2-02
- question: Q2 (a)(b)(c)
- URL: https://tradoshi.com/en/academy/liquidity-sweep
- publisher: tradoshi.com (Oshi Academy)
- author if shown: UNSTATED (course page, no byline)
- page date if shown: UNSTATED
- type: TEACHING
- quote (<=25 words, English, verbatim): "extreme cleared, then a close back inside within three candles" — QUOTE_VERIFIED
- number and unit: 3 (candles)
- OF_WHAT: candle **close** back on the original side of the level
- COMPARED_TO_WHAT: the level
- HOW_MANY_CANDLES: 3 (stated as this course's own chosen rule, not as a standard)
- TIMEFRAME: "the level and the three-candle rule are judged on timeframes chosen in advance" (QUOTE_VERIFIED) — no value
- INSTRUMENT: EUR/USD in the worked example; stated as illustrative arithmetic
- independence: INDEPENDENT_OF_PRIOR_SOURCES — tradoshi.com is not in either prior list
- reason given by source: "pick one definition, write it down, and apply it as written every day" — QUOTE_VERIFIED
- tier: TIER2
- Q2(b): close required, wick not enough — "Read the close, not the wick" (QUOTE_VERIFIED).
- Q2(c): "the previous day's high and low, the high and low of the session that just ended, equal highs or equal lows, the last swing on your decision timeframe" (QUOTE_VERIFIED).
- Note: the page explicitly says no authority fixes the sweep/break border: "The border is blurry, and no authority fixes it" (QUOTE_VERIFIED).

### Q2-03 — Quantum Algo (liquidity sweep guide)
- id: Q2-03
- question: Q2 (a)(b)(c)
- URL: https://www.quantum-algo.com/blog/guides/liquidity-sweep-trading-complete-guide/
- publisher: quantum-algo.com
- author if shown: "Written by ILY · Reviewed by Quant"
- page date if shown: "Published June 5, 2026"
- type: TEACHING
- quote (<=25 words, English, verbatim): "Criterion 3: Price must reclaim within 1-3 candles." — QUOTE_VERIFIED (this line appears in the search snippet; the fetched page states the same rule as "then snaps back below the broken level within a few candles" and, per the snippet, criterion 3. Only the fetched wording is counted.)
- Re-checked wording actually read on the page: "price wicks beyond an obvious support or resistance level, triggers the stops sitting just above that level, then snaps back below the broken level within a few candles" — QUOTE_VERIFIED
- number and unit: "1-3" per the page's criterion list (snippet); "a few" in the fetched body text
- OF_WHAT: UNSTATED (the recorded words — "Criterion 3: Price must reclaim within 1-3 candles." and, elsewhere on the page, "then snaps back below the broken level within a few candles" — name neither close nor wick nor position)
- COMPARED_TO_WHAT: the broken level
- HOW_MANY_CANDLES: 1–3 (criterion list) / UNSTATED ("a few") in the prose
- TIMEFRAME: UNSTATED
- INSTRUMENT: UNSTATED ("forex, crypto, indices, futures, gold")
- independence: NOT_INDEPENDENT_OF_Q1-01 — quantum-algo.com already in `EXTERNAL_SOURCES_LOG.md`
- reason given by source: NO_REASON_GIVEN
- tier: TIER2
- **status caveat:** the numeric "1-3" was read in a search snippet, not on the fetched page body; it is therefore listed in the pages-checked table but **excluded from the counts table**.

### Q2-04 — Dhanith
- id: Q2-04
- question: Q2 (a)(b)(c)
- URL: https://www.dhanith.com/blog/liquidity-sweeps
- publisher: dhanith.com
- author if shown: "Abhishek Dhungarjal"
- page date if shown: "May 3, 2026"
- type: TEACHING
- quote (<=25 words, English, verbatim): "A liquidity sweep closes back inside the prior range, usually within 1–5 candles." — QUOTE_VERIFIED
- number and unit: 1–5 (candles)
- OF_WHAT: candle close back inside the prior range
- COMPARED_TO_WHAT: the prior range
- HOW_MANY_CANDLES: 1–5
- TIMEFRAME: UNSTATED
- INSTRUMENT: UNSTATED
- independence: INDEPENDENT_OF_PRIOR_SOURCES — dhanith.com is not in either prior list
- reason given by source: NO_REASON_GIVEN
- tier: TIER2
- Q2(c): "Swing highs and swing lows … Equal highs and equal lows … Trendline liquidity … Double tops and double bottoms … Prior day, week, or session highs and lows … Round numbers" (QUOTE_VERIFIED).

### Q2-05 — Chart Whisperer
- id: Q2-05
- question: Q2 (a)(b)(c)
- URL: https://chartwhisperer.ca/blog/liquidity-sweep-stop-hunt-crypto-trading
- publisher: chartwhisperer.ca (CAP Framework)
- author if shown: "Charles Vincent"
- page date if shown: "April 27, 2026 · Updated November 4, 2026"
- type: TEACHING
- quote (<=25 words, English, verbatim): "A sweep wicks beyond the level and closes back inside the prior range" — QUOTE_VERIFIED
- number and unit: 1–3 (candles) — "reverses inside 1–3 candles" (QUOTE_VERIFIED)
- OF_WHAT: candle **close** position ("closes back inside the prior range" — QUOTE_VERIFIED); the recorded words do not say "body"
- COMPARED_TO_WHAT: the prior range / the level
- HOW_MANY_CANDLES: 1–3
- TIMEFRAME: UNSTATED (says the sweep is judged on 1–3 candles and the CHoCH on the "entry timeframe")
- INSTRUMENT: crypto (BTC/ETH) — **not forex**
- independence: INDEPENDENT_OF_PRIOR_SOURCES — chartwhisperer.ca is not in either prior list
- reason given by source: "in the CAP, a sweep is required but never enough" — QUOTE_VERIFIED
- tier: TIER2

### Q2-06 — ICTKillzone (liquidity sweep)
- id: Q2-06
- question: Q2 (a)(b)(c)
- URL: https://www.ictkillzone.com/ict-liquidity-sweep
- publisher: ictkillzone.com
- author if shown: "Michael Phillips"
- page date if shown: "Published June 2026"
- type: TEACHING
- quote (<=25 words, English, verbatim): "then immediately reverses with the candle body closing back inside the prior range" — QUOTE_VERIFIED
- number and unit: NONE as a candle count; "immediately" / "the very next candle" for type 1
- OF_WHAT: candle **body** close relative to the prior range
- COMPARED_TO_WHAT: the prior range
- HOW_MANY_CANDLES: UNSTATED for the limit; type 1 = next candle, type 2 = "the very next candle immediately reverses back inside" (QUOTE_VERIFIED), type 3 = cascades through several pools then reverses (no count)
- TIMEFRAME: UNSTATED; confirmation is described on 5M/15M
- INSTRUMENT: NQ examples; no instrument rule
- independence: NOT_INDEPENDENT_OF_E1 — ictkillzone.com is in both prior lists and this page is E1
- reason given by source: NO_REASON_GIVEN
- tier: TIER2
- Q2(b) — this source splits the answer: type 1 needs only a wick beyond with a body close back inside; **type 2 explicitly permits a body close fractionally beyond the level** before the reversal. Recorded as a stated exception, not averaged.
- Q2(c): "BSL or SSL pool" — swing highs/lows, equal highs/lows, session and prior-day pools referenced through the linked BSL/SSL page.

### Q2-07 — Audacity Capital
- id: Q2-07
- question: Q2 (a)(b)(c)
- URL: https://audacity.capital/trading-guides/liquidity-sweep/
- publisher: audacity.capital
- author if shown: "Federica D'Ambrosio"
- page date if shown: "Sep 18, 2026"
- type: TEACHING
- quote (<=25 words, English, verbatim): "a wick poking through a swing high or low, followed by a candle closing back inside the prior range" — QUOTE_VERIFIED
- number and unit: NONE (no candle count)
- OF_WHAT: candle close back inside the range
- COMPARED_TO_WHAT: the prior range
- HOW_MANY_CANDLES: UNSTATED — the page only says a sweep "may run a little further, sometimes over several candles, before reversing" (QUOTE_VERIFIED)
- TIMEFRAME: UNSTATED
- INSTRUMENT: GBP/USD worked example; general forex
- independence: INDEPENDENT_OF_PRIOR_SOURCES — audacity.capital is not in either prior list
- reason given by source: NO_REASON_GIVEN
- tier: TIER2
- Q2(c): "Swing highs and swing lows / Equal highs and equal lows / Session highs and lows / Previous day, week and month highs and lows / Trendline liquidity / Round numbers" (QUOTE_VERIFIED).

### Q2-08 — Fortraders (false-breakout study)
- id: Q2-08
- question: Q2 (a)(b)
- URL: https://fortraders.com/blog/false-breakouts-why-they-happen-how-to-trade
- publisher: fortraders.com
- author if shown: UNSTATED
- page date if shown: UNSTATED (search metadata 2026-07-30)
- type: TEACHING (not an ICT page; recorded because it states a bar window with a stated measurement window)
- quote (<=25 words, English, verbatim): "price closes back inside the prior 20-bar range within five bars of the break" — QUOTE_VERIFIED
- number and unit: 5 (bars); 3 (bars) on 1-minute charts
- OF_WHAT: candle **close** back inside the prior 20-bar range
- COMPARED_TO_WHAT: the prior 20-bar range
- HOW_MANY_CANDLES: 5 (3 on 1-minute)
- TIMEFRAME: named per row of its own table: 1m, 5m, 15m, 1h, daily
- INSTRUMENT: "major FX/index futures"
- independence: INDEPENDENT_OF_PRIOR_SOURCES — fortraders.com is not in either prior list
- reason given by source: "we use five bars as the cutoff across our data" — QUOTE_VERIFIED
- tier: TIER2
- **Note:** the page's own sample numbers are 2019–2026 aggregate statistics, **not** used here as market data; only the bar-window definition is recorded.

### Q2-09 — Backtrex (sweep backtest rules)
- id: Q2-09
- question: Q2 (a)(c)
- URL: https://backtrex.com/en/blog/liquidity-sweep-strategy-backtest-results
- publisher: backtrex.com
- author if shown: UNSTATED
- page date if shown: UNSTATED
- type: TEACHING
- quote (<=25 words, English, verbatim): "price exceeds the equal highs or lows level identified on the H1 timeframe by at least 3 pips" — QUOTE_VERIFIED
- number and unit: 3 (pips) — a penetration depth, not a timing rule
- OF_WHAT: distance price trades **beyond** the level
- COMPARED_TO_WHAT: the equal-highs/equal-lows level
- HOW_MANY_CANDLES: the displacement must arrive "within 2 candles following the sweep" (QUOTE_VERIFIED)
- TIMEFRAME: H1 (level identification)
- INSTRUMENT: EURUSD, XAUUSD
- independence: NOT_INDEPENDENT_OF_F1 (backtrex)
- reason given by source: NO_REASON_GIVEN
- tier: TIER2
- Q2(c): only equal highs/lows are used as the sweep reference in this test — "Equal Highs and Equal Lows … Session Highs and Lows … Prolonged consolidations" are listed as tradable pool types, but the rule uses equal highs/lows only.

### Q2-10 — FXPrimus (same text as prior E5)
- id: Q2-10
- question: Q2 (b)(c)
- URL: https://fxprimus.com/ict-smart-money-concepts/
- publisher: fxprimus.com (Primus Markets)
- author if shown: UNSTATED
- page date if shown: UNSTATED in fetched text (prior file records 2026-10-08)
- type: TEACHING
- quote (<=25 words, English, verbatim): "it usually appears as a long wick through equal highs and a close back inside the range" — QUOTE_VERIFIED
- number and unit: NONE
- OF_WHAT: candle close back inside the range
- COMPARED_TO_WHAT: the range
- HOW_MANY_CANDLES: UNSTATED
- TIMEFRAME: UNSTATED
- INSTRUMENT: UNSTATED
- independence: NOT_INDEPENDENT_OF_E5 — identical text to `myprimusmarkets.com`, which is E5 in `external_sources/e_liquidity_sweep.md`; same publisher under a second domain
- reason given by source: NO_REASON_GIVEN
- tier: TIER2
- Q2(b) — this source records the disagreement itself: "Some traders count a break only on a candle close; others accept a wick" (QUOTE_VERIFIED; also carried in the prior file as E5).

## Q2 — IMPLEMENTATION_CODE (not counted as teaching)

- **Q2-C1** — repo `kayasolomon/poi-liquidity-detector`, commit `951304b33c71ad6fedcabf957de6ab40134d5670`,
  file `src/equalLevels.ts`, blob `79a67b8857b6fc11f55b39f4549c4f8bfabaebd9`, lines 84–125 (called from
  `src/detector.ts` line 150). License: MIT. In our own words (<=25): the same bar that pierces a level decides the
  outcome — close beyond it means broken, close back inside means swept; no window of later bars is permitted.
  Numeric constant: the sweep is recorded **on the piercing bar itself** (`atIndex: index`); there is no
  "N candles" allowance. This answers Q2(a) as **0 candles** for this library, and Q2(b) as **close back inside
  required, wick alone insufficient**.
- **Q2-C2** — repo `kayasolomon/poi-liquidity-detector`, `src/detector.ts` lines 57 and 174, same commit.
  A CHoCH may pair with a sweep only if `event.atIndex - s.atIndex <= sweepReversalMaxBars`, default **20 bars**
  (`sweepReversalMaxBars: 20`). This is the only candle-count in any fetched code for "how long a sweep stays
  usable" — a different OF_WHAT from "price returns inside", and recorded as such.
- **Q2-C3** — repo `kxngHADES/SMC-Marking`, commit `bb79d1dc6f945cdce043e243e28ba6e7b9599e8f`, file
  `SMC_Terminology_marks.pine`, blob `69b2eadb60d1ee6b13f1c066db8573d6063d2da3`, line 22. License: none visible.
  Break confirmation is a user choice between a candle close beyond the level and any wick beyond it
  (`breakSrc`, default `"Close"`). The library implements both conventions side by side and states no preference.

## Q2 — Counts (TEACHING only; exact versions)

| exact version (number | OF_WHAT | COMPARED_TO_WHAT) | independent publishers | of which new |
|---|---|---|---|
| close back inside within **1–3 candles** | candle close | the prior range / level | 4 (Q2-01 liquidityscan, Q2-03 quantum-algo [snippet], Q2-02 tradoshi, Q2-05 chartwhisperer) | 2 (tradoshi, chartwhisperer) |
| close back inside within **1–5 candles** | candle close | the prior range | 1 (Q2-04 dhanith) | 1 |
| close back inside within **3 candles** exactly | candle close | the level | 1 (Q2-02 tradoshi, stated as its own rule) | 1 |
| close back inside within **5 bars** (3 on 1m) | candle close | prior 20-bar range | 1 (Q2-08 fortraders; non-ICT) | 1 |
| **no candle limit stated**; close back inside required | candle close | the range | 4 (Q2-06 ictkillzone, Q2-07 audacity, Q2-10 fxprimus, plus E2 alphametrixx as carried in the prior file → 3 new) | 1 (audacity) |
| **no count**; wick-only accepted for one sweep type | wick beyond + body close inside (except type 2) | the range | 1 (Q2-06 ictkillzone, type 2) | 0 |
| penetration >= **3 pips** beyond the level | distance beyond the level | the equal-highs/lows level | 1 (Q2-09 backtrex) | 0 |

**Q2 answer to (a) as found:** four independent publishers give 1–3, one gives 1–5, one gives 3, one gives 5 bars,
and four give no limit. **No source states that a wick alone is sufficient**; every fetched source requires a
close back inside, and one source (Q2-06) explicitly carves out a type-2 exception.

### Q2 — pages checked (15)

| page | outcome |
|---|---|
| https://liquidityscan.io/blog/liquidity-sweep-vs-liquidity-grab-is-there-a-difference | Q2-01 — number + close rule |
| https://tradoshi.com/en/academy/liquidity-sweep | Q2-02 — number + close rule |
| https://www.quantum-algo.com/blog/guides/liquidity-sweep-trading-complete-guide/ | Q2-03 — "a few candles" in prose; 1–3 only in snippet |
| https://www.dhanith.com/blog/liquidity-sweeps | Q2-04 — 1–5 |
| https://chartwhisperer.ca/blog/liquidity-sweep-stop-hunt-crypto-trading | Q2-05 — 1–3 |
| https://www.ictkillzone.com/ict-liquidity-sweep | Q2-06 — no count; three types |
| https://audacity.capital/trading-guides/liquidity-sweep/ | Q2-07 — no count |
| https://fortraders.com/blog/false-breakouts-why-they-happen-how-to-trade | Q2-08 — 5 bars (non-ICT) |
| https://backtrex.com/en/blog/liquidity-sweep-strategy-backtest-results | Q2-09 — 3 pips + 2 candles |
| https://fxprimus.com/ict-smart-money-concepts/ | Q2-10 — no count, records the wick/close disagreement |
| https://blog.trinitytrading.io/liquidity-sweeps-ict-trading-guide-2026/ | PAGE_UNREACHABLE (DNS error) |
| https://bingx.com/en/learn/article/what-is-liquidity-sweep-in-crypto-trading-how-to-spot-and-trade | NOT_FETCHED (snippet only) |
| https://ictflow.com/blog/ict-liquidity-sweep-vs-run | NOT_FETCHED (snippet only) |
| https://chartinglens.com/blog/liquidity-sweeps-trading-guide | NOT_FETCHED (snippet only) |
| https://zeramaxacademy.com/liquidity-sweep-vs-market-reversal-how-to-read-context/ | NOT_FETCHED (snippet only) |

---

# Q3 — Equal highs / lows pairing

## Q3-01 — ICTKillzone
- id: Q3-01
- question: Q3 (a)(b)(c) + tolerance
- URL: https://www.ictkillzone.com/ict-equal-highs-lows
- publisher: ictkillzone.com
- author if shown: "Michael Phillips"
- page date if shown: "Published May 2026"
- type: TEACHING
- quote (<=25 words, English, verbatim): "In the ICT framework, "approximately the same" means within 5–10 pips on major forex pairs" — QUOTE_VERIFIED
- number and unit: 5–10 pips; also "10–20 points" for NQ/ES; "1.50–3.00 per ounce" for gold
- OF_WHAT: absolute price difference between the two highs (resp. lows) (elsewhere on the page: "Two consecutive candles at the same high is not a meaningful EQH" — QUOTE_VERIFIED)
- COMPARED_TO_WHAT: nothing — a fixed distance in pips/points, not scaled
- HOW_MANY_CANDLES: **UNSTATED** for a maximum distance; instead "the touches need time between them" and "Two consecutive candles at the same high is not a meaningful EQH" (QUOTE_VERIFIED) — a minimum, with no number ("a reasonable window of days to weeks" — QUOTE_VERIFIED)
- TIMEFRAME: UNSTATED
- INSTRUMENT: "major forex pairs like GBP/USD or EUR/USD"; indices NQ/YM; gold
- independence: NOT_INDEPENDENT_OF_K1 — same publisher and same page as K1 in `external_sources/k_equal_highs.md`
- reason given by source: "Beyond 10 pips, the "equal" quality diminishes" — QUOTE_VERIFIED
- tier: TIER2
- Q3(b): must the highs be consecutive swings? **UNSTATED**, but "You need two clean swing high pivots at the same level" and criterion 4 requires time separation — the page does not say whether intervening same-side swings may exist.
- Q3(c): no higher high between them — **UNSTATED** on this page (it states only that the level must be "currently unswept", criterion 5).

## Q3-02 — The Inner Circle Traders
- id: Q3-02
- question: Q3 (a)(b) + tolerance
- URL: https://www.theinnercircletraders.com/ict-equal-highs-equal-lows/
- publisher: theinnercircletraders.com
- author if shown: "Educational Content Team" (prior file); fetched page shows "The Inner Circle Traders"
- page date if shown: "Updated July 2026"
- type: TEACHING
- quote (<=25 words, English, verbatim): "within 5–10 pips on Forex, or within a few ticks on futures" — QUOTE_VERIFIED
- number and unit: 5–10 pips (forex); "a few ticks" (futures — not a number)
- OF_WHAT: absolute difference between the two swing highs ("two or more consecutive swing highs print at approximately the same price" — QUOTE_VERIFIED, same page); the recorded words do not say "wick"
- COMPARED_TO_WHAT: nothing (fixed distance)
- HOW_MANY_CANDLES: UNSTATED
- TIMEFRAME: "On the relevant timeframe" — UNSTATED
- INSTRUMENT: forex; futures unnamed
- independence: NOT_INDEPENDENT_OF_K2 — same publisher as K2
- reason given by source: NO_REASON_GIVEN
- tier: TIER2
- Q3(b) — this is the only fetched source that answers "consecutive": "two or more **consecutive** swing highs print at approximately the same price" (QUOTE_VERIFIED). It does **not** say whether a higher high between them disqualifies the pair.
- Q3(c): UNSTATED.

## Q3-03 — LuxAlgo (concept page)
- id: Q3-03
- question: Q3 (a) + tolerance
- URL: https://www.luxalgo.com/library/concept/equal-highs-lows-as-liquidity/
- publisher: luxalgo.com
- author if shown: UNSTATED
- page date if shown: UNSTATED
- type: NO_NUMBER
- quote (<=25 words, English, verbatim): "There is no fixed tolerance." — QUOTE_VERIFIED
- number and unit: NONE
- OF_WHAT: UNSTATED
- COMPARED_TO_WHAT: UNSTATED ("within a small fraction of ATR" is offered as practice, with no fraction)
- HOW_MANY_CANDLES: UNSTATED; the page instead requires "a meaningful pullback between the swings" (QUOTE_VERIFIED)
- TIMEFRAME: "within a few ticks of one another, or within a small fraction of ATR on your timeframe" — QUOTE_VERIFIED
- INSTRUMENT: UNSTATED
- independence: INDEPENDENT_OF_PRIOR_SOURCES — luxalgo.com is not in either prior list
- reason given by source: "stops gather in a band rather than at one price" — QUOTE_VERIFIED
- tier: TIER2

## Q3-04 — LiquidityScan (swing 3-candle rule page)
- id: Q3-04
- question: Q3 (a) + tolerance
- URL: https://liquidityscan.io/blog/what-is-a-swing-high-and-swing-low-in-ict-the-3-candle-rule
- publisher: liquidityscan.io
- author if shown: "Hayk Muradian"
- page date if shown: "July 10, 2026"
- type: TEACHING
- quote (<=25 words, English, verbatim): "flag any pair of highs or lows within roughly 0.1–0.3% of each other on your trading timeframe" — QUOTE_VERIFIED
- number and unit: 0.1–0.3 (percent)
- OF_WHAT: difference between the two highs ÷ price — expressed as a percentage of price
- COMPARED_TO_WHAT: the price level itself (percent of price), not ATR and not pips
- HOW_MANY_CANDLES: UNSTATED
- TIMEFRAME: "your trading timeframe" (a percentage, so tf-invariant)
- INSTRUMENT: UNSTATED; worked example BTCUSDT (two highs "15 dollars apart, about 0.02%")
- independence: NOT_INDEPENDENT_OF_A1 — same publisher and author as A1
- reason given by source: NO_REASON_GIVEN
- tier: TIER2
- Q3(c): **UNSTATED** here as a pairing rule; but the same page notes "If C2's high exactly equals C1's high, the 3-candle rule does not fire" (QUOTE_VERIFIED) — i.e. exact equality can suppress a swing rather than create a pair.

## Q3-05 — Equiti
- id: Q3-05
- question: Q3 (a) + tolerance
- URL: https://www.equiti.com/sc-en/news/trading-ideas/equal-highs-and-equal-lows-explained-how-smart-money-sees-liquidity/
- publisher: equiti.com
- author if shown: "Yazeed Abu Summaqa"
- page date if shown: UNSTATED (search metadata 2026-09-09)
- type: TEACHING
- quote (<=25 words, English, verbatim): "a sweep of only 2 or 3 pips above equal highs may not be significant enough" — QUOTE_VERIFIED
- number and unit: 2–3 pips, set against a stated ATR of ~32 pips on the 15-minute
- OF_WHAT: the **sweep depth** beyond the equal highs (not the pairing tolerance)
- COMPARED_TO_WHAT: the 15-minute ATR — a stated ATR comparison, but no multiplier given
- HOW_MANY_CANDLES: UNSTATED
- TIMEFRAME: 15-minute (in the example)
- INSTRUMENT: UNSTATED (forex context)
- independence: NOT_INDEPENDENT_OF_PRIOR_SOURCES — equiti.com is in `EXTERNAL_SOURCES_LOG.md`
- reason given by source: "a sweep covering a larger portion of the ATR … often carries more weight" — QUOTE_VERIFIED
- tier: TIER2
- **Note:** this source gives an ATR comparison for sweep *depth*, not for the EQH *pairing tolerance*. It is recorded because the question asks for any tolerance number with its unit and reference; it is **not** counted as an EQH-pairing version.

## Q3-06 — TradingView script, "Yown Equal Highs & Lows" (robert_yown)
- id: Q3-06
- question: Q3 (a)(b) + tolerance
- URL: https://www.tradingview.com/script/Vjj1FUEb/ (PROTECTED SOURCE — code not readable)
- publisher: tradingview.com / author robert_yown
- author if shown: "robert_yown"
- page date if shown: "Aug 24"
- type: NO_NUMBER (implementation description; source hidden, code NOT read)
- quote (<=25 words, English, verbatim): "set as a multiple of the 14-period ATR rather than a fixed price distance" — QUOTE_VERIFIED
- number and unit: NONE for the multiple (the multiplier value is not printed)
- OF_WHAT: absolute price difference between two swing points ("compared against the immediately preceding swing point of the same type" — QUOTE_VERIFIED)
- COMPARED_TO_WHAT: ATR, period 14
- HOW_MANY_CANDLES: the pair is "compared against the immediately preceding swing point of the same type" (QUOTE_VERIFIED) — no maximum distance in bars is given
- TIMEFRAME: UNSTATED (described as scaling across timeframes)
- INSTRUMENT: UNSTATED (example USD/JPY 15m)
- independence: INDEPENDENT_OF_PRIOR_SOURCES — tradingview.com and this author are not in either prior list
- reason given by source: "so it scales automatically across instruments and timeframes" — QUOTE_VERIFIED
- tier: TIER2
- Q3(b) — answered: only the **immediately preceding** swing of the same type is compared. Q3(c): UNSTATED.

## Q3-07 — TradingView script, "Equal Highs & Lows + Volume Profile" (rcj101208)
- id: Q3-07
- question: Q3 (a)(b)(c) + tolerance
- URL: https://www.tradingview.com/script/ylzaLAgz-Equal-Highs-Lows-Volume-Profile/ (OPEN-SOURCE, but source text not retrieved — only the description page)
- publisher: tradingview.com / author rcj101208
- author if shown: "rcj101208"
- page date if shown: "Sep 26"
- type: NO_NUMBER (description only; code NOT read)
- quote (<=25 words, English, verbatim): "a waiting level is dropped the moment price trades through it" — QUOTE_VERIFIED
- number and unit: NONE printed (settings exist: "Equality tolerance … measured as a percentage of ATR"; "Minimum bars apart"; "Waiting levels expire after a set number of bars" — QUOTE_VERIFIED)
- OF_WHAT: UNSTATED
- COMPARED_TO_WHAT: ATR (percentage of it) — multiplier value UNSTATED
- HOW_MANY_CANDLES: a "Minimum bars apart" setting exists; value UNSTATED
- TIMEFRAME: UNSTATED
- INSTRUMENT: UNSTATED
- independence: INDEPENDENT_OF_PRIOR_SOURCES
- reason given by source: "a high from four hundred bars ago is not pairing with anything meaningful today" — QUOTE_VERIFIED
- tier: TIER2
- Q3(c) — answered in the negative form: the implementation **drops** a waiting level as soon as price trades through it, so an intervening higher high prevents the pair from forming. `COMPUTABLE_RULE`, no number.

## Q3-08 — LuxAlgo EQH/EQL indicator page
- id: Q3-08
- question: Q3 (a) + tolerance
- URL: https://www.luxalgo.com/library/indicator/eqh-eql-fvg-breakouts/
- publisher: luxalgo.com
- author if shown: UNSTATED
- page date if shown: UNSTATED
- type: NO_NUMBER (parameter names only; no default values printed)
- quote (<=25 words, English, verbatim): "Max EQH/EQL Distance (Bars): The maximum number of bars allowed between the two pivots" — QUOTE_VERIFIED
- number and unit: NONE printed — parameters exist: "Equality Threshold (%)", "Max EQH/EQL Distance (Bars)", "Max EQH/EQL Age (Bars)"
- OF_WHAT: percentage difference between two pivot prices; and bar distance between the pivots
- COMPARED_TO_WHAT: price percentage (threshold); bars (distance)
- HOW_MANY_CANDLES: parameter exists ("Max EQH/EQL Distance"), value UNSTATED
- TIMEFRAME: UNSTATED
- INSTRUMENT: UNSTATED
- independence: INDEPENDENT_OF_Q3-03 at publisher level — same publisher as Q3-03, so NOT independent of Q3-03; luxalgo.com itself is new to this file
- reason given by source: NO_REASON_GIVEN
- tier: TIER2
- **This is the only fetched source that answers Q3(a) with a *computable parameter* (max bars between pivots).** It does not publish the value.

## Q3 — IMPLEMENTATION_CODE (not counted as teaching)

- **Q3-C1** — repo `Vatthu/v1indicators`, commit `36785b982e55c4dfed20037e52fd92dbdf8f7f19`, file
  `v1indicators/foundational/levels/equal_highs_lows.py`, lines 7–61 (blob `ebfeb2d644afd019742e31655701358f0ab20cb4`,
1997 bytes). License: MIT (repo metadata).
  In our own words (<=25): two confirmed pivots are "equal" when the absolute price difference, divided by the
  previous pivot's price, is at or below `threshold`; the previous pivot is the last pivot seen. Numeric constants:
  `length: int = 3` (pivot window = 2×3+1 = 7 bars, confirmed after `length` bars), `threshold: float = 0.1`
  (percent of the previous pivot's price). Pivots are compared to the **immediately previous** pivot of the same
  side — the code does not test for an intervening higher high.
- **Q3-C2** — repo `joshyattridge/smart-money-concepts`, commit `1b62fd6c41e1f508e7ed76831a039fa4c82d42f6`, file
  `smartmoneyconcepts/smc.py`, lines 573–600 (`liquidity`). License: MIT.
  In our own words (<=25): candidate swing highs are clustered when they sit inside a band whose width is a
  fraction of the whole dataset's high-low span; a group needs more than one member. Numeric constant:
  `range_percent: float = 0.01`; band = `(max(high) - min(low)) * 0.01` over **the entire loaded history**, not an
  ATR and not pips. This is a different OF_WHAT from every teaching record above.
- **Q3-C3** — repo `kxngHADES/SMC-Marking`, commit `bb79d1dc6f945cdce043e243e28ba6e7b9599e8f`, file
  `SMC_Terminology_marks.pine`, blob `69b2eadb60d1ee6b13f1c066db8573d6063d2da3`, lines 71–72 and 344–362.
  License: none visible. In our own words (<=25): a new pivot of the same side is compared with the previous one,
  and the pair is marked equal only if the absolute price gap is below a threshold expressed in ATR multiples.
  Numeric constants: `eqLen = input.int(3, "Confirmation Bars")` (pivot arms = 3 bars each side),
  `eqThr = input.float(0.1, "Threshold (x ATR)")`, ATR = `ta.atr(200)` (line 156), test
  `math.abs(eqPH - lastEqH) < eqThr * atrv`. So: **0.1 × ATR(200)**, only the **immediately previous** pivot of the
  same side, with `minval = 0, maxval = 0.5` allowed.
- **Q3-C4** — repo `kayasolomon/poi-liquidity-detector`, commit `951304b33c71ad6fedcabf957de6ab40134d5670`,
  files `src/equalLevels.ts` (blob `79a67b8857b6fc11f55b39f4549c4f8bfabaebd9`, lines 32–50, 84–125) and
  `src/detector.ts` line 150, 57. License: MIT. In our own words (<=25): a swing joins a cluster when it falls
  inside a tolerance of the cluster's mean; the tolerance is an ATR fraction; a level is broken on a close through
  its outermost member and swept on a wick through that closes back. Numeric constants: `equalTolATR: 0.25`
  (default, → `tolerance = 0.25 × ATR(14)`), `fractalK: 2`, cluster accepted at 2 members. Answers Q3(a), (b) and
  (c) as **computable rules with no maximum bar distance**: there is no cap on bars between members, and an
  intervening trade beyond the outer extreme kills the candidate.

## Q3 — Counts (TEACHING only; exact versions)

| exact version (number | OF_WHAT | COMPARED_TO_WHAT) | independent publishers | of which new |
|---|---|---|---|---|
| **5–10 pips** | absolute difference between the two highs/lows | fixed pip distance, nothing scaled | 3 (Q3-01 ictkillzone, K3 blog.pfhmarkets, Q3-02 theinnercircletraders) | 0 new publishers; Q3-01/Q3-02 already in prior inventory |
| **1–3 pips** | absolute difference | fixed pip distance | 1 (K4 fxnx, carried) | 0 |
| **1–5 pips** | absolute difference | fixed pip distance, justified by spread | 1 (K6 izict, carried) | 0 |
| **2–5 pips / points** | absolute difference | fixed distance | 1 (K7 x10hop, carried) | 0 |
| **0.1–0.3%** | difference ÷ price | price (percent) | 1 (Q3-04 liquidityscan) | 0 (publisher prior) |
| **no fixed tolerance** | — | — | 3 (Q3-03 luxalgo, K9 forexmt4indicators, Q3-05 equiti in effect) | 1 (luxalgo) |
| **ATR multiple, value not printed** | difference | ATR(14) | 2 (Q3-06 Yown, Q3-07 rcj101208) | 2 |
| **max bars between pivots, value not printed** | difference + bar distance | ATR% and bars | 1 (Q3-08 luxalgo) | 1 |

**Q3 answers as found:** (a) two publishers give a **maximum bar distance** as a setting with no value (Q3-07,
Q3-08); no teaching page gives a number of candles. Tolerances cluster at 5–10 pips (3 publishers), with 1–3,
1–5, 2–5 and 0.1–0.3% each at 1. (b) only Q3-02 says "consecutive"; Q3-06 says "immediately preceding pivot of the
same type". (c) only two implementation descriptions answer it (Q3-07 drops the level on any trade-through;
Q3-C1 does not test it). **No teaching source states a no-higher-high-between rule.**

### Q3 — pages checked (15)

| page | outcome |
|---|---|
| https://www.ictkillzone.com/ict-equal-highs-lows | Q3-01 — 5–10 pips, 5 criteria |
| https://www.theinnercircletraders.com/ict-equal-highs-equal-lows/ | Q3-02 — 5–10 pips, "consecutive" |
| https://www.luxalgo.com/library/concept/equal-highs-lows-as-liquidity/ | Q3-03 — no fixed tolerance |
| https://liquidityscan.io/blog/what-is-a-swing-high-and-swing-low-in-ict-the-3-candle-rule | Q3-04 — 0.1–0.3% |
| https://www.equiti.com/sc-en/news/trading-ideas/equal-highs-and-equal-lows-explained-how-smart-money-sees-liquidity/ | Q3-05 — ATR comparison for sweep depth |
| https://www.tradingview.com/script/Vjj1FUEb/ | Q3-06 — ATR-based, multiplier unstated |
| https://www.tradingview.com/script/ylzaLAgz-Equal-Highs-Lows-Volume-Profile/ | Q3-07 — parameter, no value |
| https://www.luxalgo.com/library/indicator/eqh-eql-fvg-breakouts/ | Q3-08 — max-bars parameter, no value |
| https://www.mql5.com/en/blogs/post/762665 | K8 carried (points-or-ATR margin, no fixed setting) |
| https://forexmt4indicators.com/what-is-equal-highs-lows/ | K9 carried ("no fixed numerical threshold") |
| https://fxnx.com/en/blog/equal-highs-equal-lows-resting-liquidity-explained | K4 carried (1–3 pips) |
| https://datapips.net/equal-highs-equal-lows-eqh-eql-ict-trading/ | K10 carried ("a few pips") |
| https://tradeify.co/post/smart-money-concepts-prop-traders | K11 carried (unit named, no amount) |
| https://grandalgo.com/blog/equal-highs-equal-lows-eqh-eql | NOT_FETCHED (snippet only) |
| https://in.tradingview.com/scripts/equalhighs/ | NOT_FETCHED (snippet only) |

---

# Q4 — Order block boundaries

## Q4-01 — ICTKillzone
- id: Q4-01
- question: Q4 (zone; entry level)
- URL: https://www.ictkillzone.com/ict-order-block
- publisher: ictkillzone.com
- author if shown: "Michael Phillips"
- page date if shown: UNSTATED in fetched text (prior file records 2026-05-05)
- type: TEACHING
- quote (<=25 words, English, verbatim): "The order block zone is marked using the candle body — not the full candle range including wicks" — QUOTE_VERIFIED
- number and unit: 50 (percent) for the entry level
- OF_WHAT: the zone = **body** (open→close); the entry level = 50% of that **body** ("The mean threshold is the 50% level of the order block candle body — not the full candle range" — QUOTE_VERIFIED, same page)
- COMPARED_TO_WHAT: none (an absolute fraction of the candle's own body)
- HOW_MANY_CANDLES: 1 (the last opposing candle); "or small cluster of candles" when several oppose, then "extend the zone to encompass the highest high to the lowest low of the entire cluster" (QUOTE_VERIFIED)
- TIMEFRAME: UNSTATED; example 5-minute NQ
- INSTRUMENT: NQ (example); no instrument rule
- independence: NOT_INDEPENDENT_OF_C5 — this page is C5 in `external_sources/c_order_block.md`
- reason given by source: "The wick marks the absolute invalidation — body marks the entry zone" — QUOTE_VERIFIED
- tier: TIER2
- second, distinct statement on the same page: "The mean threshold is the 50% level of the order block candle body — not the full candle range" (QUOTE_VERIFIED) — so this source's entry level is 50% of the **body**, not 50% of the range.
- invalidation: "Only a candle body closing beyond the zone boundary constitutes full mitigation" (QUOTE_VERIFIED).

## Q4-02 — Trading Strategy Guides (two pages, one publisher)
- id: Q4-02
- question: Q4 (zone; entry level)
- URL: https://tradingstrategyguides.com/ict-order-block-complete-guide-to-institutional-footprints/
- publisher: tradingstrategyguides.com
- author if shown: UNSTATED
- page date if shown: UNSTATED (search metadata 2026-09-06)
- type: TEACHING
- quote (<=25 words, English, verbatim): "The order block encompasses the full span from open to the extreme wick" — QUOTE_VERIFIED
- number and unit: 50 (percent)
- OF_WHAT: zone = **open → extreme wick**; entry level = "either the candle open or the mean threshold"; mean threshold = "the 50% midpoint of the order block candle body" (QUOTE_VERIFIED)
- COMPARED_TO_WHAT: none
- HOW_MANY_CANDLES: 1 ("the final opposing candle or cluster of candles")
- TIMEFRAME: UNSTATED
- INSTRUMENT: UNSTATED
- independence: NOT_INDEPENDENT_OF_PRIOR_SOURCES — tradingstrategyguides.com is in both prior lists (I1)
- reason given by source: NO_REASON_GIVEN
- tier: TIER2
- **This is the only fetched TEACHING source whose zone upper bound is the open and lower bound the wick** (rather than body only or full range).
- its sibling page (`.../ict-order-block-complete-identification-and-trading-guide-2/`) gives a different boundary set: "from the candle open to its low for bullish blocks" and calls the 50% an "ultimate invalidation line" — recorded as the same publisher, not a second publisher.

## Q4-03 — LuxAlgo (order block anatomy)
- id: Q4-03
- question: Q4 (zone; entry level)
- URL: https://www.luxalgo.com/library/concept/order-block-anatomy-and-refinement/
- publisher: luxalgo.com
- author if shown: UNSTATED
- page date if shown: UNSTATED
- type: TEACHING
- quote (<=25 words, English, verbatim): "wick-to-wick is the widest honest zone; bodies-only is tighter but misses more touches" — QUOTE_VERIFIED
- number and unit: NONE fixed; 50 (percent) is named as the mean-threshold line
- OF_WHAT: two competing conventions — full wick-to-wick range, or bodies only (named in the quoted words); the 50% entry line: UNSTATED (no verbatim quote recorded in this record)
- COMPARED_TO_WHAT: none
- HOW_MANY_CANDLES: 1; "merge stacked opposing candles into one zone" as an alternative (QUOTE_VERIFIED)
- TIMEFRAME: UNSTATED
- INSTRUMENT: UNSTATED
- independence: INDEPENDENT_OF_PRIOR_SOURCES (luxalgo is new here); NOT_INDEPENDENT_OF_Q3-03/Q3-08 at publisher level
- reason given by source: "There is no authoritative rule: pick one convention and judge it on your own market and timeframe" — QUOTE_VERIFIED
- tier: TIER2

## Q4-04 — LiquidityScan (FVG vs OB)
- id: Q4-04
- question: Q4 (entry level)
- URL: https://liquidityscan.io/blog/fvg-vs-order-block-which-entry-zone-should-you-trade
- publisher: liquidityscan.io
- author if shown: "Hayk Muradian"
- page date if shown: "July 11, 2026"
- type: TEACHING
- quote (<=25 words, English, verbatim): "The opening price of the OB candle is the classic entry" — QUOTE_VERIFIED
- number and unit: 50 (percent)
- OF_WHAT: entry level = **the OB candle's open**, or the mean threshold; and on this page the mean threshold is described as "50% of the OB's full range" (QUOTE_VERIFIED) — **not** 50% of the body
- COMPARED_TO_WHAT: none
- HOW_MANY_CANDLES: 1 (last down-close candle "or cluster")
- TIMEFRAME: UNSTATED; example is 4H BTCUSDT
- INSTRUMENT: BTCUSDT (example)
- independence: NOT_INDEPENDENT_OF_Q2-01 (same publisher, liquidityscan.io already in prior lists)
- reason given by source: "the level the accumulating party defends" — QUOTE_VERIFIED
- tier: TIER2
- **Disagreement recorded, not resolved:** Q4-01 and Q4-02 put the 50% on the **body**; Q4-04 puts it on the **full range**. Both are TEACHING records from different publishers.

## Q4-05 — EBC Financial Group
- id: Q4-05
- question: Q4 (zone)
- URL: https://www.ebc.com/forex/what-is-an-order-block-in-trading-beginner-s-guide
- publisher: ebc.com
- author if shown: "Chad Carnegie"
- page date if shown: "Published on: 2025-05-22 · Updated on: 2026-08-17"
- type: TEACHING
- quote (<=25 words, English, verbatim): "Neither convention is official." — QUOTE_VERIFIED (context: "Many traders draw the zone from open to close rather than high to low … Neither convention is official.")
- number and unit: NONE fixed
- OF_WHAT: body (open→close) vs full range
- COMPARED_TO_WHAT: none
- HOW_MANY_CANDLES: 1 "or small cluster"
- TIMEFRAME: UNSTATED
- INSTRUMENT: UNSTATED
- independence: INDEPENDENT_OF_PRIOR_SOURCES — ebc.com is not in either prior list
- reason given by source: "the body shows where most business was done" — QUOTE_VERIFIED
- tier: TIER2

## Q4-06 — Inner Circle Trader (order block, bullish, bearish — one publisher)
- id: Q4-06
- question: Q4 (entry level; which candle)
- URL: https://innercircletrader.net/tutorials/ict-order-block/ ; https://innercircletrader.net/tutorials/ict-bullish-order-block/ ; https://innercircletrader.net/tutorials/ict-bearish-order-block/
- publisher: innercircletrader.net
- author if shown: "Ayub Rana"
- page date if shown: UNSTATED
- type: TEACHING
- quote (<=25 words, English, verbatim): "you can execute a buy trade at the 50% retracement of the order block" — QUOTE_VERIFIED
- number and unit: 50 (percent)
- OF_WHAT: entry level = 50% retracement of the order block — the page does not say whether that 50% is of the body or of the full range
- COMPARED_TO_WHAT: none
- HOW_MANY_CANDLES: 2 ("Both variants are 2-candle formations at minimum" — QUOTE_VERIFIED): the OB candle plus the engulfing candle
- TIMEFRAME: entry confirmation on 15-minute or 5-minute
- INSTRUMENT: XAG/USD and EUR/USD examples
- independence: NOT_INDEPENDENT_OF_B1/C4 (innercircletrader.net already in prior inventory)
- reason given by source: NO_REASON_GIVEN
- tier: TIER2
- its "which candle" rule is distinctive: the OB candle must be **engulfed** — "The second candle (bullish) must grab the low of the previous bearish candle" and "must close above the high of the previous bearish candle" (QUOTE_VERIFIED).

## Q4 — IMPLEMENTATION_CODE (not counted as teaching)

- **Q4-C1** — repo `Vatthu/v1indicators`, commit `36785b982e55c4dfed20037e52fd92dbdf8f7f19`, file
  `v1indicators/foundational/trend/order_blocks.py`, lines 48–68. License: MIT.
  In our own words (<=25): zone lower bound is always the candle low; upper bound is the open by default and the
  high only when `use_wicks=True`; a mid level is the arithmetic mean of the two bounds.
  Numeric constants: `use_wicks: bool = False`; `BULLISH_OB_MID = (upper + lower) / 2.0`.
  **Note:** with the default, the zone is open→low (a hybrid), and the mid is 50% of that hybrid — not 50% of body
  and not 50% of range.
- **Q4-C2** — repo `joshyattridge/smart-money-concepts`, commit `1b62fd6c41e1f508e7ed76831a039fa4c82d42f6`, file
  `smartmoneyconcepts/smc.py`, lines 447–483 and 509–542.
  License: MIT. In our own words (<=25): the zone is a full high-to-low candle range taken from the lowest low
  between the last swing and the break; a strength percentage comes from three-candle volumes.
  Numeric constants: `obTop = _high[...]`, `obBtm = _low[...]` (**wick to wick, full range**),
  `percentage = min(highVolume, lowVolume) / max_vol * 100.0`.
  This is the only implementation here whose zone is unambiguously wick-to-wick.
- **Q4-C3** — repo `kxngHADES/SMC-Marking`, commit `bb79d1dc6f945cdce043e243e28ba6e7b9599e8f`, file
  `SMC_Terminology_marks.pine`, blob `69b2eadb60d1ee6b13f1c066db8573d6063d2da3`, lines 56–58 and 268–292.
  License: none visible. In our own words (<=25): the demand block is the lowest candle of the window before a
  bullish break, boxed from its high to its low; blocks are removed on either a close or a wick, chosen by input.
  Numeric constants: `obCount = input.int(3, "Max Blocks Per Side")`,
  `obMitig = input.string("Close", "Mitigation", options = ["Close", "Wick"])` default `"Close"`;
  the box is `box.new(bar_index - idx, high[idx], ..., low[idx])` → **full high-to-low range**. No 50% line is drawn.
- **Q4-C4** — repo `kayasolomon/poi-liquidity-detector`, commit `951304b33c71ad6fedcabf957de6ab40134d5670`,
  file `src/detector.ts`, blob `a214f3a0e67f83c2e9aa51ad7c7658d76e30a78c`, lines 51–58, 195–245 and
  `src/types.ts`. License: MIT. In our own words (<=25): zone bounds are the candle's body by default and the full
  wick range on request; no midpoint field is emitted. Numeric constant: `zoneMode: 'body'` default, i.e.
  `[min(open,close), max(open,close)]`; `'full'` = wick-to-wick. There is **no entry level and no 50% level** in
  the library at all.

## Q4 — Counts (TEACHING only; exact versions)

| exact version (zone bounds | entry level) | independent publishers | of which new |
|---|---|---|---|
| zone = **body only** (open→close) | entry = 50% of **body** ("mean threshold") | 2 (Q4-01 ictkillzone, Q4-02 tradingstrategyguides) | 0 |
| zone = **open → extreme wick** | entry = the **open**, or 50% of the body | 1 (Q4-02 tradingstrategyguides — same publisher as above, so this is a second version from one publisher) | 0 |
| zone = **body** or **full range**, convention chosen by trader | entry = 50% line | 3 (Q4-03 luxalgo, Q4-05 ebc, Q4-01 restated) | 2 (luxalgo, ebc) |
| entry = **OB open price**, or 50% of the **full range** | — | 1 (Q4-04 liquidityscan) | 0 |
| entry = **50% retracement** of the OB, body-vs-range unspecified | — | 1 (Q4-06 innercircletrader) | 0 |
| which candle: last opposing candle, "or small cluster" | — | 4 (Q4-01, Q4-02, Q4-03, Q4-04) | 1 (luxalgo) |
| which candle: last opposing candle that is **engulfed** by the next | — | 1 (Q4-06 innercircletrader) | 0 |

**Q4 answer as found:** the zone is drawn three incompatible ways — body only (2 publishers), open→wick (1),
wick-to-wick (1 teaching + 1 implementation). The entry level is either the **open** (2 publishers) or the
**50% line** (4 publishers), and the 50% is placed on the **body** by two publishers and on the **full range** by
one. No source gives a number of candles for the "cluster" case.

### Q4 — pages checked (12)

| page | outcome |
|---|---|
| https://www.ictkillzone.com/ict-order-block | Q4-01 — body zone, 50% body, wick stop |
| https://www.ictkillzone.com/ict-breaker-block | body open→close used as the violation boundary (same publisher, not counted) |
| https://tradingstrategyguides.com/ict-order-block-complete-guide-to-institutional-footprints/ | Q4-02 — open→wick |
| https://tradingstrategyguides.com/ict-order-block-complete-identification-and-trading-guide-2/ | same publisher; open→low variant |
| https://www.luxalgo.com/library/concept/order-block-anatomy-and-refinement/ | Q4-03 — both conventions, "no authoritative rule" |
| https://liquidityscan.io/blog/fvg-vs-order-block-which-entry-zone-should-you-trade | Q4-04 — open, or 50% of full range |
| https://www.ebc.com/forex/what-is-an-order-block-in-trading-beginner-s-guide | Q4-05 — "Neither convention is official" |
| https://innercircletrader.net/tutorials/ict-order-block/ | Q4-06 — 50% retracement, 2-candle formation |
| https://innercircletrader.net/tutorials/ict-bullish-order-block/ | same publisher; engulf rule |
| https://innercircletrader.net/tutorials/ict-bearish-order-block/ | same publisher; engulf rule |
| https://www.ictkillzone.com/ict-2022-model | no boundary stated → nothing for Q4 |
| https://velotrade.com/blog/fair-value-gap | mentions OB = "last opposite colored candle before the displacement"; no boundary → nothing for Q4 |

---

# Q5 — Fair value gap

## Q5-01 — ICTKillzone
- id: Q5-01
- question: Q5 (a)(b)
- URL: https://www.ictkillzone.com/ict-fair-value-gap
- publisher: ictkillzone.com
- author if shown: "Michael Phillips"
- page date if shown: UNSTATED in fetched text
- type: TEACHING
- quote (<=25 words, English, verbatim): "What invalidates it is a candle body closing through the opposite boundary" — QUOTE_VERIFIED
- number and unit: 50 (percent, CE); NONE for minimum size
- OF_WHAT: invalidation = candle **body close** through the far boundary
- COMPARED_TO_WHAT: the far boundary of the three-candle gap
- HOW_MANY_CANDLES: 3 (C1, C2, C3)
- TIMEFRAME: UNSTATED in the rule; examples 5-minute and 1-minute
- INSTRUMENT: GBP/USD walkthrough; NQ example
- independence: NOT_INDEPENDENT_OF_PRIOR_SOURCES — ictkillzone.com is in both prior lists (C5, E1, I5)
- reason given by source: "a wick into the FVG is not mitigation … Until that happens, the gap hasn't been filled — it's been tested" — QUOTE_VERIFIED
- tier: TIER2
- Q5(a): **UNSTATED** — this page gives no minimum size number.
- Q5(b): touched ≠ invalid; 50% ≠ invalid; only a body close through counts.

## Q5-02 — Arrow Algo
- id: Q5-02
- question: Q5 (a)(b)
- URL: https://arrowalgo.com/fair-value-gap-trading-strategy/
- publisher: arrowalgo.com
- author if shown: UNSTATED
- page date if shown: UNSTATED (search metadata 2026-09-18)
- type: TEACHING
- quote (<=25 words, English, verbatim): "a gap worth at least half an ATR reflects genuine displacement" — QUOTE_VERIFIED
- number and unit: 0.5 (ATR multiple)
- OF_WHAT: a gap ("a gap worth at least half an ATR" — QUOTE_VERIFIED); the boundary definition (candle 1 high → candle 3 low) is UNSTATED on the recorded words
- COMPARED_TO_WHAT: ATR (period not stated on the page)
- HOW_MANY_CANDLES: 3
- TIMEFRAME: UNSTATED
- INSTRUMENT: crypto ("Binance, Coinbase, or HyperLiquid")
- independence: INDEPENDENT_OF_PRIOR_SOURCES — arrowalgo.com is not in either prior list
- reason given by source: "A gap smaller than the market's normal candle-to-candle wobble means nothing" — QUOTE_VERIFIED
- tier: TIER2
- Q5(b) this source's answer: "A gap that fills completely and keeps going has invalidated the setup" (QUOTE_VERIFIED) — full fill, not 50%.

## Q5-03 — El Trader Financiado
- id: Q5-03
- question: Q5 (a)(b)
- URL: https://www.eltraderfinanciado.com/en/blog/fair-value-gap
- publisher: eltraderfinanciado.com
- author if shown: UNSTATED
- page date if shown: UNSTATED (search metadata 2026-10-07)
- type: TEACHING
- quote (<=25 words, English, verbatim): "Filter by size. A minimum size by ATR or by percentage removes the one- or two-tick gaps" — QUOTE_VERIFIED
- number and unit: NONE (unit named: ATR or percentage)
- OF_WHAT: the gap's size ("A minimum size by ATR or by percentage" — QUOTE_VERIFIED)
- COMPARED_TO_WHAT: ATR **or** a percentage of price — the reader chooses
- HOW_MANY_CANDLES: 3
- TIMEFRAME: UNSTATED
- INSTRUMENT: UNSTATED (NinjaTrader examples)
- independence: INDEPENDENT_OF_PRIOR_SOURCES — eltraderfinanciado.com is not in either prior list
- reason given by source: NO_REASON_GIVEN
- tier: TIER2
- Q5(b) this source's answer is a **rule choice, stated as such**: "Is the FVG mitigated when a wick touches it or when a candle closes inside? Is it invalidated by a wick or by a close on the other side? What you choose changes the results" (QUOTE_VERIFIED). Its own model table uses "Close through the FVG = out".

## Q5-04 — BrokerCheck (Florian Fendt)
- id: Q5-04
- question: Q5 (a)(b)
- URL: https://brokercheck.co/fair-value-gap/
- publisher: brokercheck.co
- author if shown: "Florian Fendt"
- page date if shown: "Published October 29, 2026 · Updated November 2, 2026"
- type: NO_NUMBER (for size) / TEACHING (for the fill taxonomy)
- quote (<=25 words, English, verbatim): "There is no common standard here either, so choose one and keep it" — QUOTE_VERIFIED
- number and unit: NONE — it lists three fill conventions: "Touched", "Half filled", "Fully filled" (QUOTE_VERIFIED)
- OF_WHAT: UNSTATED (no recorded quote names the size filter's object; the fill side appears only as the conventions "Touched", "Half filled", "Fully filled" — QUOTE_VERIFIED)
- COMPARED_TO_WHAT: "a fraction of the average true range" — fraction UNSTATED
- HOW_MANY_CANDLES: 3
- TIMEFRAME: UNSTATED
- INSTRUMENT: UNSTATED
- independence: INDEPENDENT_OF_PRIOR_SOURCES — brokercheck.co is not in either prior list
- reason given by source: NO_REASON_GIVEN
- tier: TIER2

## Q5-05 — Velotrade
- id: Q5-05
- question: Q5 (b)
- URL: https://velotrade.com/blog/fair-value-gap
- publisher: velotrade.com
- author if shown: "Gianluca Pizzituti"
- page date if shown: "Oct 7, 2026" (page also says "Last verified Oct 8, 2026")
- type: TEACHING
- quote (<=25 words, English, verbatim): "most traders treat a close beyond the far edge as a failure" — QUOTE_VERIFIED
- number and unit: 50 (percent, CE)
- OF_WHAT: invalidation = close beyond the far edge; a wick through "may leave the idea alive"
- COMPARED_TO_WHAT: the far edge
- HOW_MANY_CANDLES: 3
- TIMEFRAME: UNSTATED ("the definition is identical on every timeframe")
- INSTRUMENT: UNSTATED (forex context; prop-firm framing)
- independence: INDEPENDENT_OF_PRIOR_SOURCES — velotrade.com is not in either prior list
- reason given by source: "accepting a wick through CE but exiting on a close through the full gap" — QUOTE_VERIFIED
- tier: TIER2
- Q5(a): **UNSTATED** — no minimum size on this page.

## Q5-06 — FXNX (FVG entry filter)
- id: Q5-06
- question: Q5 (b)
- URL: https://fxnx.com/en/blog/fvg-entry-filter-mechanical-rules-htf-bias
- publisher: fxnx.com
- author if shown: UNSTATED (search snippet shows no byline; fxnx bylines vary)
- page date if shown: "Updated August 2026" (snippet)
- type: TEACHING (snippet-sourced wording; see caveat)
- quote (<=25 words, English, verbatim): "If an M5 candle closes below the CE, the setup is mechanically invalidated" — SNIPPET_ONLY (from a search result; **not** re-read on the page in this run)
- number and unit: 50 (percent, CE)
- OF_WHAT: invalidation = **close beyond the 50% level**, not the far edge
- COMPARED_TO_WHAT: the CE (midpoint)
- HOW_MANY_CANDLES: 3
- TIMEFRAME: M5 (in the quote)
- INSTRUMENT: UNSTATED
- independence: NOT_INDEPENDENT_OF_K4 (fxnx.com already in `external_sources/`)
- reason given by source: NO_REASON_GIVEN
- tier: TIER2
- **status caveat:** this is the only source found that puts invalidation at the **50%** rather than the far edge. Because the wording was read only in a snippet, it is **excluded from the counts table** and flagged for a re-fetch.

## Q5-07 — LuxAlgo EQH/EQL indicator (FVG size parameter)
- id: Q5-07
- question: Q5 (a)
- URL: https://www.luxalgo.com/library/indicator/eqh-eql-fvg-breakouts/
- publisher: luxalgo.com
- author if shown: UNSTATED
- page date if shown: UNSTATED
- type: NO_NUMBER (parameter named, no default printed)
- quote (<=25 words, English, verbatim): "Min FVG Size (ATR): The minimum size required for a gap to be considered a valid FVG" — QUOTE_VERIFIED
- number and unit: NONE printed — the unit is an ATR multiple
- OF_WHAT: gap height
- COMPARED_TO_WHAT: ATR ("Breakout ATR Length" is a separate setting; length UNSTATED)
- HOW_MANY_CANDLES: 3
- TIMEFRAME: UNSTATED
- INSTRUMENT: UNSTATED
- independence: NOT_INDEPENDENT_OF_Q3-08 (same publisher/page); luxalgo is new to this file
- reason given by source: NO_REASON_GIVEN
- tier: TIER2

## Q5 — IMPLEMENTATION_CODE (not counted as teaching)

- **Q5-C1** — repo `joshyattridge/smart-money-concepts`, commit `1b62fd6c41e1f508e7ed76831a039fa4c82d42f6`, file
  `smartmoneyconcepts/smc.py`, lines 68–128 (`fvg`). License: MIT. In our own words (<=25): a bullish gap needs
  candle t-1's high below candle t+1's low and a bullish middle candle; the zone is those two wick prices;
  mitigation is the first bar whose low reaches the gap top. Numeric constants: `join_consecutive` flag; **no size
  filter at all**; mitigation test `ohlc["low"][i+2:] <= top[i]` — i.e. **a wick touch mitigates**, which is the
  opposite convention to the teaching records above.
- **Q5-C2** — repo `Vatthu/v1indicators`, commit `36785b982e55c4dfed20037e52fd92dbdf8f7f19`, file
  `v1indicators/foundational/trend/fair_value_gaps.py`, lines 6–56. License: MIT. In our own words (<=25): a gap
  requires the current low above the high two bars back **and** the middle candle's close beyond that same level;
  an optional absolute size filter drops small gaps. Numeric constants: `threshold: float = 0.0` with the guard
  `if threshold < 0: raise` — the filter is in **absolute price units**, applied as `(bull_top - bull_bottom).abs()
  >= threshold`, so it is **not** ATR and **not** a percentage. Line 15–16 docstring states the exact inequality:
  bullish = `low[t] > high[t-2] and close[t-1] > high[t-2]`.
- **Q5-C3** — repo `kxngHADES/SMC-Marking`, commit `bb79d1dc6f945cdce043e243e28ba6e7b9599e8f`, file
  `SMC_Terminology_marks.pine`, blob `69b2eadb60d1ee6b13f1c066db8573d6063d2da3`, lines 64–65, 322–330 and
  300–318. License: none visible. In our own words (<=25): a gap exists when the current low is above the high two
  bars back with a confirming middle close; a minimum gap size is an ATR multiple entered as a decimal; fill
  shrinks the box and a full traversal deletes it. Numeric constants: `fvgMinAtr = input.float(0.0, "Min Gap Size
  (x ATR)")` with `step = 0.05` (**default 0.0 — filter off**), `minGap = fvgMinAtr * atrv` where `atrv = ta.atr(200)`,
  `(low - high[2]) >= minGap`; `fvgCount = input.int(5)`. Invalidation is **full fill** (`if low <= b.get_bottom()`
  → delete), not a close through.
- **Q5-C4** — repo `kayasolomon/poi-liquidity-detector`, commit `951304b33c71ad6fedcabf957de6ab40134d5670`,
  file `src/fvg.ts`, blob `d4383a5df5eee6a8c29baf8e346ec7a3513a4d07`, lines 43–90. License: MIT.
  In our own words (<=25): fill state runs fresh → partial at the first penetration → filled at full traversal;
  the deepest penetration is stored as a monotonic 0–1 fraction; penetration is read from wicks by default and
  from closes on request. Numeric constants: `fvgFillMode: 'wick'` default; `filledFraction` starts at `0`, set to
  `partial` when `fraction > 0`, `filled` when `fraction >= 1` (lines 79–88). **No minimum gap size exists in this
  library.**

## Q5 — Counts (TEACHING only; exact versions)

| exact version | independent publishers | of which new |
|---|---|---|
| minimum size = **0.5 × ATR**, measured on gap height | 1 (Q5-02 arrowalgo) | 1 |
| minimum size = **a fraction of ATR or a percentage**, value not printed | 3 (Q5-03 eltraderfinanciado, Q5-04 brokercheck, Q5-07 luxalgo) | 3 |
| **no minimum size stated** | 2 (Q5-01 ictkillzone, Q5-05 velotrade) | 1 |
| invalidation = **candle body close through the far boundary** | 4 (Q5-01 ictkillzone, Q5-05 velotrade, Q5-03 eltraderfinanciado, plus B3/B4 carried from `external_sources/b_fair_value_gap.md` → B3, B4, B2 = 3 prior publishers) → 5 publishers | 2 (ictkillzone-FVG page is prior publisher; velotrade and eltraderfinanciado new) |
| invalidation = **full fill** (price trades the whole zone) | 2 (Q5-02 arrowalgo, Q5-04 brokercheck) | 2 |
| invalidation = **close beyond the 50% CE** | 1 (Q5-06 fxnx, snippet-only → excluded from this count) | 0 counted |
| **touch alone does not invalidate** | 3 (Q5-01, Q5-05, Q5-03) | 2 |

**Q5 answers as found:** (a) exactly one publisher gives a computable minimum size (0.5 × ATR); three name the
unit without a value; two state none. (b) the majority version among fetched teaching pages is a **body close
through the far boundary**; one publisher (snippet only) puts it at the 50%; two treat a full fill as the failure.
No fetched source treats a wick touch as invalidation of a fresh gap.

### Q5 — pages checked (13)

| page | outcome |
|---|---|
| https://www.ictkillzone.com/ict-fair-value-gap | Q5-01 — body-close invalidation, no size |
| https://arrowalgo.com/fair-value-gap-trading-strategy/ | Q5-02 — 0.5 ATR |
| https://www.eltraderfinanciado.com/en/blog/fair-value-gap | Q5-03 — unit, no value; rule-choice |
| https://brokercheck.co/fair-value-gap/ | Q5-04 — three fill conventions |
| https://velotrade.com/blog/fair-value-gap | Q5-05 — close beyond far edge |
| https://fxnx.com/en/blog/fvg-entry-filter-mechanical-rules-htf-bias | Q5-06 — snippet only |
| https://www.luxalgo.com/library/indicator/eqh-eql-fvg-breakouts/ | Q5-07 — ATR size parameter |
| https://liquidityscan.io/blog/fvg-vs-order-block-which-entry-zone-should-you-trade | "Full candle close through the gap (inversion)" — same version as Q5-01, prior publisher |
| https://ictflow.com/blog/ict-complete-2022-trading-strategy | FVG defined as 3-candle; target = next pool; no size, no invalidation detail |
| https://fundingpips.com/blog/ict-2022-model | FVG = three-candle imbalance; entry near edge or CE; no size number |
| https://www.ictkillzone.com/ict-2022-model | FVG + CE description; no size number |
| https://futuresindicators.com/learn/fair-value-gaps | NOT_FETCHED (snippet only: "50% Rule") |
| https://www.vpsforextrader.com/blog/fair-value-gap-trading/ | NOT_FETCHED (snippet; secondary statistics only, not used) |

---

# Q6 — Stop placement

## Q6-01 — LiquiditySweeps.com (editorial team)
- id: Q6-01
- question: Q6
- URL: https://liquiditysweeps.com/ict-stop-loss/
- publisher: liquiditysweeps.com
- author if shown: "LiquiditySweeps.com Editorial Team"
- page date if shown: "July 25, 2026"
- type: TEACHING
- quote (<=25 words, English, verbatim): "Every ICT stop includes a 2–3 pip buffer beyond the structural reference" — QUOTE_VERIFIED
- number and unit: **2–3 pips** buffer; and four type distances: **3–10, 5–18, 10–30, 20–50+ pips**
- OF_WHAT: distance beyond the structural reference ("beyond the structural reference" — QUOTE_VERIFIED); the four specific references (FVG far boundary C1 high, OB low, Judas extreme, prior swing low) are UNSTATED in the recorded quotes
- COMPARED_TO_WHAT: the structural reference price, measured in pips
- HOW_MANY_CANDLES: UNSTATED
- TIMEFRAME: 5-minute throughout the worked lifecycle
- INSTRUMENT: **EUR/USD** (2 pips buffer), **GBP/USD** (3 pips), **GBP/JPY** (4–5 pips) — all FOREX
- independence: NOT_INDEPENDENT_OF_PRIOR_SOURCES — liquiditysweeps.com is in both prior lists (B3)
- reason given by source: "The buffer accounts for spread (a stop at exactly C1 high triggers on a 0.3-pip spread touch)" — QUOTE_VERIFIED
- tier: TIER2
- FUTURES_UNITS line (recorded, not converted): "On NQ: 3–5 point buffer." — QUOTE_VERIFIED → label `FUTURES_UNITS`.

## Q6-02 — ICTKillzone (order block)
- id: Q6-02
- question: Q6
- URL: https://www.ictkillzone.com/ict-order-block
- publisher: ictkillzone.com
- author if shown: "Michael Phillips"
- page date if shown: UNSTATED in fetched text
- type: TEACHING
- quote (<=25 words, English, verbatim): "Stops go beyond the full candle wick — not just the body" — QUOTE_VERIFIED
- number and unit: NONE in pips for the rule; the page's image text says "a few pips beyond the wick extreme"; the worked NQ trade gives a concrete 46 points
- OF_WHAT: the candle's **full wick extreme** (low for bullish OB, high for bearish OB)
- COMPARED_TO_WHAT: the wick extreme of the OB candle
- HOW_MANY_CANDLES: 1 (the OB candle)
- TIMEFRAME: UNSTATED; example 5-minute NQ
- INSTRUMENT: NQ example → `FUTURES_UNITS` (46 points risk, QUOTE_VERIFIED)
- independence: NOT_INDEPENDENT_OF_C5
- reason given by source: "Price regularly wicks into the wick zone before reacting; stops inside the wick get hit on valid setups" — QUOTE_VERIFIED
- tier: TIER2

## Q6-03 — Inner Circle Trader (order block pages)
- id: Q6-03
- question: Q6
- URL: https://innercircletrader.net/tutorials/ict-order-block/ ; .../ict-bullish-order-block/ ; .../ict-bearish-order-block/
- publisher: innercircletrader.net
- author if shown: "Ayub Rana"
- page date if shown: UNSTATED
- type: TEACHING
- quote (<=25 words, English, verbatim): "set your stop loss 10 to 20 pips below the low of the order block" — QUOTE_VERIFIED
- number and unit: **10–20 pips**
- OF_WHAT: beyond the **low of the OB zone** (bullish) / **high of the OB zone** (bearish)
- COMPARED_TO_WHAT: the OB zone's low/high — the page does not say whether that zone is body or wick
- HOW_MANY_CANDLES: 1 (the OB candle)
- TIMEFRAME: UNSTATED
- INSTRUMENT: FOREX (pips); examples XAG/USD, EUR/USD
- independence: NOT_INDEPENDENT_OF_I4 — innercircletrader.net is I4 in `external_sources/i_stop_loss_take_profit.md`
- reason given by source: "The buffer absorbs the typical re-test spike before the move resolves" — QUOTE_VERIFIED
- tier: TIER2
- **Verification note:** the prior file `i_stop_loss_take_profit.md` marked I4's "10–20 pips" as **unverified and deleted**. In this run the phrase was found verbatim on the current order-block, bullish and bearish pages ("10 to 20 pips below the low of the order block"). Recorded here as `QUOTE_VERIFIED` on today's fetched text; the prior round's deletion is not overridden, it is superseded by this fetch and both are on record.
- second number on the same publisher: "40 to 50 pips beyond the swept level" for the liquidity-pool model (`.../ict-liquidity-pool/`) — QUOTE_VERIFIED. Different OF_WHAT, counted separately.

## Q6-04 — Backtrex (sweep backtest)
- id: Q6-04
- question: Q6
- URL: https://backtrex.com/en/blog/liquidity-sweep-strategy-backtest-results
- publisher: backtrex.com
- author if shown: UNSTATED
- page date if shown: UNSTATED
- type: TEACHING
- quote (<=25 words, English, verbatim): "Stop loss: 5 pips beyond the swept liquidity level" — QUOTE_VERIFIED
- number and unit: **5 pips**
- OF_WHAT: beyond the swept level, on the side opposite the sweep
- COMPARED_TO_WHAT: the swept liquidity level
- HOW_MANY_CANDLES: UNSTATED
- TIMEFRAME: H1
- INSTRUMENT: EURUSD, XAUUSD — FOREX/metal
- independence: NOT_INDEPENDENT_OF_F1
- reason given by source: NO_REASON_GIVEN
- tier: TIER2

## Q6-05 — FundingPips
- id: Q6-05
- question: Q6
- URL: https://fundingpips.com/blog/ict-2022-model
- publisher: fundingpips.com
- author if shown: "By FundingPips"
- page date if shown: "October 18, 2026"
- type: TEACHING
- quote (<=25 words, English, verbatim): "Add a small buffer for spread, especially on cross pairs" — QUOTE_VERIFIED
- number and unit: NONE — "small buffer"; the worked example uses **5 pips** below a sweep low ("5 pips below the sweep low of 1.0851" — QUOTE_VERIFIED, hypothetical)
- OF_WHAT: beyond the **extreme of the liquidity sweep** ("a stop placed exactly at the sweep's extreme can be clipped by spread alone" — QUOTE_VERIFIED, same page)
- COMPARED_TO_WHAT: the sweep's high/low
- HOW_MANY_CANDLES: UNSTATED
- TIMEFRAME: execution 1–15 minute; bias 1H/4H
- INSTRUMENT: FOREX (EUR/USD in the hypothetical)
- independence: INDEPENDENT_OF_PRIOR_SOURCES
- reason given by source: "a stop placed exactly at the sweep's extreme can be clipped by spread alone" — QUOTE_VERIFIED
- tier: TIER2

## Q6-06 — Audacity Capital
- id: Q6-06
- question: Q6
- URL: https://audacity.capital/trading-guides/liquidity-sweep/
- publisher: audacity.capital
- author if shown: "Federica D'Ambrosio"
- page date if shown: "Sep 18, 2026"
- type: TEACHING
- quote (<=25 words, English, verbatim): "Place the stop beyond the sweep extreme" — QUOTE_VERIFIED
- number and unit: NONE
- OF_WHAT: beyond the sweep extreme
- COMPARED_TO_WHAT: the swept high/low
- HOW_MANY_CANDLES: UNSTATED
- TIMEFRAME: UNSTATED
- INSTRUMENT: FOREX (GBP/USD worked example)
- independence: INDEPENDENT_OF_PRIOR_SOURCES
- reason given by source: "it is nonsense to place the stop at the level itself" is **not** on the page; the page's own wording is "Place the stop beyond the sweep extreme or another clearly defined invalidation level" → NO_REASON_GIVEN
- tier: TIER2

## Q6-07 — ICTKillzone (liquidity sweep page)
- id: Q6-07
- question: Q6
- URL: https://www.ictkillzone.com/ict-liquidity-sweep
- publisher: ictkillzone.com
- author if shown: "Michael Phillips"
- page date if shown: "Published June 2026"
- type: TEACHING
- quote (<=25 words, English, verbatim): "Stop beyond the sweep wick extreme." — QUOTE_VERIFIED
- number and unit: NONE
- OF_WHAT: beyond the sweep wick extreme
- COMPARED_TO_WHAT: the swept pool's wick
- HOW_MANY_CANDLES: UNSTATED
- TIMEFRAME: 5M/15M confirmation
- INSTRUMENT: NQ examples → `FUTURES_UNITS` context
- independence: NOT_INDEPENDENT_OF_E1
- reason given by source: NO_REASON_GIVEN
- tier: TIER2

## Q6-08 — Inner Circle Trader (Silver Bullet)
- id: Q6-08
- question: Q6
- URL: https://innercircletrader.net/tutorials/ict-silver-bullet-strategy/
- publisher: innercircletrader.net
- author if shown: "Ayub Rana"
- page date if shown: UNSTATED
- type: TEACHING
- quote (<=25 words, English, verbatim): "stop loss goes above the high of the candle that created the fair value gap" — QUOTE_VERIFIED
- number and unit: NONE in pips; a buffer is required: "Place the stop beyond the wick of the candle that created the fair value gap, with a small buffer" (QUOTE_VERIFIED)
- OF_WHAT: the FVG candle's wick high (for shorts)
- COMPARED_TO_WHAT: that candle's high
- HOW_MANY_CANDLES: 1 (the candle that created the FVG)
- TIMEFRAME: 1-minute / 3-minute execution; 15-minute parent
- INSTRUMENT: XAU/USD example; forex/futures listed
- independence: NOT_INDEPENDENT_OF_B1
- reason given by source: "Stops sitting one pip beyond the FVG are routinely tagged before the trade resolves" — QUOTE_VERIFIED
- tier: TIER2

## Q6-09 — Quantum Algo (sweep guide) — SNIPPET_ONLY
- id: Q6-09
- question: Q6
- URL: https://www.quantum-algo.com/blog/guides/liquidity-sweep-trading-complete-guide/
- publisher: quantum-algo.com
- author if shown: "ILY"
- page date if shown: "Published June 5, 2026"
- type: TEACHING — **excluded from counts** (wording not read on the page)
- quote: "Stop just beyond the sweep wick + 0.5 ATR" — SNIPPET_ONLY
- number and unit: 0.5 (ATR multiple) buffer
- OF_WHAT: beyond the sweep wick
- COMPARED_TO_WHAT: ATR (period UNSTATED in the snippet)
- HOW_MANY_CANDLES: UNSTATED
- TIMEFRAME: UNSTATED ("entry timeframe" in the snippet)
- INSTRUMENT: UNSTATED
- independence: NOT_INDEPENDENT_OF_Q1-01
- reason given by source: NO_REASON_GIVEN
- tier: TIER2

## Q6 — IMPLEMENTATION_CODE (not counted as teaching)

- **Q6-C1** — repo `kayasolomon/poi-liquidity-detector`, commit `951304b33c71ad6fedcabf957de6ab40134d5670`,
  `src/types.ts` (blob `d1283adb96f9d41e6a4e19b1afb79c078e6acf44`) and `src/zones.ts`. License: MIT.
  Recorded only to state the negative: **no stop-loss or buffer constant exists anywhere in the library.** It emits
  zones, levels, sweeps and reversal pairings, and leaves stop placement to the caller. `NO_NUMBER`.
- **Q6-C2** — repo `kxngHADES/SMC-Marking`, commit `bb79d1dc6f945cdce043e243e28ba6e7b9599e8f`, file
  `SMC_Terminology_marks.pine`. License: none visible. Same negative: **no stop, target, buffer or R:R input in the
  file** (a search for `stop`, `target`, `rr` returns only the deletion of mitigated zones). `NO_NUMBER`.

## Q7 — IMPLEMENTATION_CODE (not counted as teaching)

- **Q7-C1** — repo `kayasolomon/poi-liquidity-detector`, commit `951304b33c71ad6fedcabf957de6ab40134d5670`,
  `README.md` "SweepReversal" section and `src/detector.ts` line 174. License: MIT. The only target-like object in
  the library is the **most recent confirmed lone swing extreme** and the **equal-level outer extreme** — both price
  levels, no multiple. `NO_NUMBER` for a target multiple.
- **Q7-C2** — repo `kxngHADES/SMC-Marking`, commit `bb79d1dc6f945cdce043e243e28ba6e7b9599e8f`. License: none
  visible. It draws the Running High/Low of Day and Week (`showDay`, `showWeek`, lines 77–80) as liquidity
  references — the only "target" objects in the file. `NO_NUMBER`.

## Q6 — Counts (TEACHING only; exact versions)

| exact version (number | OF_WHAT | COMPARED_TO_WHAT) | independent publishers | of which new |
|---|---|---|---|---|
| **2–3 pip** buffer, by pair: EURUSD 2, GBPUSD 3, GBPJPY 4–5 | distance beyond the structural reference | the reference price, in pips | 1 (Q6-01 liquiditysweeps) | 0 |
| **10–20 pips** | distance beyond the OB zone low/high | the OB zone boundary, in pips | 1 (Q6-03 innercircletrader) | 0 |
| **40–50 pips** | distance beyond the swept level | the swept level, in pips | 1 (Q6-03 same publisher, second number) | 0 |
| **5 pips** | distance beyond the swept level | the swept level, in pips | 1 (Q6-04 backtrex) | 0 |
| **no number**, "beyond the full wick / sweep extreme" | distance beyond a wick extreme | the wick extreme | 5 (Q6-02 ictkillzone, Q6-05 fundingpips, Q6-06 audacity, Q6-07 ictkillzone-sweep, Q6-08 innercircletrader) → 4 distinct publishers | 2 (fundingpips, audacity) |
| **"small buffer" / "a few pips"** named, value not fixed | buffer beyond the reference | the reference | 3 (Q6-02, Q6-05, Q6-08) | 1 |
| **3–5 NQ points** — `FUTURES_UNITS` | buffer beyond reference | points | 1 (Q6-01, futures leg) | 0 |
| **46 NQ points** (worked trade) — `FUTURES_UNITS` | risk distance | entry to sweep wick | 1 (Q6-02) | 0 |

**Q6 answer as found:** for FOREX the only explicit numeric buffers are **2–3 pips** (with pair-specific values
2 / 3 / 4–5), **10–20 pips** beyond an order block, **40–50 pips** beyond a swept level, and **5 pips** beyond a
swept level — each from a single publisher. Every other fetched source states the *price* the stop goes beyond and
declines to give a number. Futures points are recorded separately above and **not converted**.

### Q6 — pages checked (13)

| page | outcome |
|---|---|
| https://liquiditysweeps.com/ict-stop-loss/ | Q6-01 — 2–3 pips + four type ranges |
| https://www.ictkillzone.com/ict-order-block | Q6-02 — beyond full wick |
| https://innercircletrader.net/tutorials/ict-order-block/ | Q6-03 — 10–20 pips |
| https://innercircletrader.net/tutorials/ict-bullish-order-block/ | same publisher |
| https://innercircletrader.net/tutorials/ict-bearish-order-block/ | same publisher |
| https://innercircletrader.net/tutorials/ict-liquidity-pool/ | 40–50 pips (same publisher) |
| https://innercircletrader.net/tutorials/ict-silver-bullet-strategy/ | Q6-08 — FVG candle wick |
| https://backtrex.com/en/blog/liquidity-sweep-strategy-backtest-results | Q6-04 — 5 pips |
| https://fundingpips.com/blog/ict-2022-model | Q6-05 — "small buffer" |
| https://audacity.capital/trading-guides/liquidity-sweep/ | Q6-06 — no number |
| https://www.ictkillzone.com/ict-liquidity-sweep | Q6-07 — no number |
| https://tradoshi.com/en/academy/liquidity-sweep | worked example uses 2 pips above the sweep high, labelled illustrative → no rule |
| https://chartwhisperer.ca/blog/liquidity-sweep-stop-hunt-crypto-trading | "beyond the last 4-hour swing plus a small buffer" (crypto) → no number |

---

# Q7 — Target

## Q7-01 — The Inner Circle Traders (liquidity zones)
- id: Q7-01
- question: Q7
- URL: https://www.theinnercircletraders.com/ict-liquidity-zones/
- publisher: theinnercircletraders.com
- author if shown: "The Inner Circle Traders"
- page date if shown: "Updated July 2026"
- type: TEACHING
- quote (<=25 words, English, verbatim): "ICT methodology requires a minimum 1:2 R:R on most setups — ideally 1:3 or better" — QUOTE_VERIFIED
- number and unit: **1:2** minimum, **1:3** preferred (risk multiple)
- OF_WHAT: distance from entry to the target, divided by the stop distance
- COMPARED_TO_WHAT: the trade's own stop distance (risk)
- HOW_MANY_CANDLES: UNSTATED
- TIMEFRAME: UNSTATED ("a 15M FVG" appears in the illustration)
- INSTRUMENT: UNSTATED
- independence: NOT_INDEPENDENT_OF_K2
- reason given by source: "If the liquidity target is too close to produce this, skip the trade" — QUOTE_VERIFIED
- tier: TIER2
- target definition on the same page: "For bullish setups, the target is always a BSL level above the current price — typically the nearest equal highs, prior day high, or prior week high" (QUOTE_VERIFIED).

## Q7-02 — ICT Flow (2022 model)
- id: Q7-02
- question: Q7
- URL: https://ictflow.com/blog/ict-complete-2022-trading-strategy
- publisher: ictflow.com
- author if shown: UNSTATED
- page date if shown: "May 21, 2026"
- type: TEACHING
- quote (<=25 words, English, verbatim): "ICT teaches using at least a 3:1 minimum R:R for any 2022 model trade" — QUOTE_VERIFIED
- number and unit: **3:1** (risk multiple)
- OF_WHAT: distance to the DOL target divided by stop size
- COMPARED_TO_WHAT: the stop size
- HOW_MANY_CANDLES: UNSTATED
- TIMEFRAME: UNSTATED
- INSTRUMENT: UNSTATED
- independence: INDEPENDENT_OF_PRIOR_SOURCES — ictflow.com is new
- reason given by source: "if the distance to the DOL target is less than three times the stop size, the setup does not qualify" — QUOTE_VERIFIED
- tier: TIER2
- target definition: "the next liquidity pool as the primary target, with partial exits at the first FVG in the path and full exit at the ERL target" (QUOTE_VERIFIED).

## Q7-03 — ICTKillzone (FVG page)
- id: Q7-03
- question: Q7
- URL: https://www.ictkillzone.com/ict-fair-value-gap
- publisher: ictkillzone.com
- author if shown: "Michael Phillips"
- page date if shown: UNSTATED
- type: TEACHING
- quote (<=25 words, English, verbatim): "Your first target is the nearest internal range liquidity" — QUOTE_VERIFIED
- number and unit: **1:2** minimum ("Minimum R:R before entry: 1:2 to the first target" — QUOTE_VERIFIED)
- OF_WHAT: distance to the first target ÷ risk
- COMPARED_TO_WHAT: the stop distance (beyond C1)
- HOW_MANY_CANDLES: UNSTATED
- TIMEFRAME: UNSTATED
- INSTRUMENT: NQ example; GBP/USD walkthrough
- independence: NOT_INDEPENDENT_OF_Q5-01 (same publisher/page)
- reason given by source: "If the structure doesn't offer at least 1:2 with your stop beyond the FVG, skip it" — QUOTE_VERIFIED
- tier: TIER2
- T2 definition: "Your second target is the draw on liquidity that established your daily bias" (QUOTE_VERIFIED).

## Q7-04 — ICTKillzone (order block page) — same publisher, second version
- id: Q7-04
- question: Q7
- URL: https://www.ictkillzone.com/ict-order-block
- publisher: ictkillzone.com
- author if shown: "Michael Phillips"
- page date if shown: UNSTATED
- type: TEACHING
- quote (<=25 words, English, verbatim): "Target 1 (50% position) | Nearest short-term high" — QUOTE_VERIFIED (table row)
- number and unit: **1:2** minimum ("Minimum R:R | 1:2 to first target before entry" — QUOTE_VERIFIED)
- OF_WHAT: nearest short-term high/low (T1) ("Target 1 (50% position) | Nearest short-term high" — QUOTE_VERIFIED (table row)); T2: UNSTATED (no T2 quote recorded in this record)
- COMPARED_TO_WHAT: the entry-to-stop distance for the R:R gate
- HOW_MANY_CANDLES: UNSTATED
- TIMEFRAME: UNSTATED
- INSTRUMENT: NQ example → `FUTURES_UNITS` figures (166 pts)
- independence: NOT_INDEPENDENT_OF_C5
- reason given by source: NO_REASON_GIVEN
- tier: TIER2

## Q7-05 — Inner Circle Trader (Silver Bullet)
- id: Q7-05
- question: Q7
- URL: https://innercircletrader.net/tutorials/ict-silver-bullet-strategy/
- publisher: innercircletrader.net
- author if shown: "Ayub Rana"
- page date if shown: UNSTATED
- type: TEACHING
- quote (<=25 words, English, verbatim): "a take profit at the next liquidity pool — typically a 1:3 risk-reward target" — QUOTE_VERIFIED
- number and unit: **1:3** (risk multiple); also "20–30 pips" per setup (QUOTE_VERIFIED)
- OF_WHAT: the 1:3 is target distance ÷ risk; the 20–30 pips is an absolute distance in pips
- COMPARED_TO_WHAT: risk (for 1:3); nothing (for the pip figure)
- HOW_MANY_CANDLES: UNSTATED
- TIMEFRAME: 1m/3m execution
- INSTRUMENT: XAU/USD, GBP/USD, EUR/USD
- independence: NOT_INDEPENDENT_OF_B1
- reason given by source: NO_REASON_GIVEN
- tier: TIER2

## Q7-06 — Velotrade
- id: Q7-06
- question: Q7
- URL: https://velotrade.com/blog/fair-value-gap
- publisher: velotrade.com
- author if shown: "Gianluca Pizzituti"
- page date if shown: "Oct 7, 2026"
- type: TEACHING
- quote (<=25 words, English, verbatim): "ICT traders aim at opposing liquidity: the next obvious pool of stops in the trade's direction" — QUOTE_VERIFIED
- number and unit: NONE as a rule; the page gives a break-even table (1:1 → 50%, 1:2 → 33.3%, 1:3 → 25%)
- OF_WHAT: the target is a price level (swing high, cluster of equal highs); the table is a probability, not a rule
- COMPARED_TO_WHAT: for the table, reward-to-risk ratio
- HOW_MANY_CANDLES: UNSTATED
- TIMEFRAME: UNSTATED
- INSTRUMENT: UNSTATED (forex context)
- independence: INDEPENDENT_OF_PRIOR_SOURCES
- reason given by source: "Check reward to risk before placing the order" — QUOTE_VERIFIED
- tier: TIER2

## Q7-07 — Backtrex (displacement article)
- id: Q7-07
- question: Q7
- URL: https://backtrex.com/en/blog/ict-displacement-candle-market-concept
- publisher: backtrex.com
- author if shown: UNSTATED
- page date if shown: UNSTATED (search metadata 2026-07-20)
- type: TEACHING
- quote (<=25 words, English, verbatim): "Take profit: the next liquidity level in the direction of the displacement" — QUOTE_VERIFIED
- number and unit: NONE
- OF_WHAT: a price level (next significant high or low, HTF zone)
- COMPARED_TO_WHAT: UNSTATED
- HOW_MANY_CANDLES: UNSTATED
- TIMEFRAME: UNSTATED
- INSTRUMENT: UNSTATED
- independence: NOT_INDEPENDENT_OF_F1
- reason given by source: NO_REASON_GIVEN
- tier: TIER2

## Q7-08 — LiquiditySweeps.com
- id: Q7-08
- question: Q7
- URL: https://liquiditysweeps.com/ict-stop-loss/
- publisher: liquiditysweeps.com
- author if shown: "LiquiditySweeps.com Editorial Team"
- page date if shown: "July 25, 2026"
- type: TEACHING
- quote (<=25 words, English, verbatim): "Minimum 1.5:1 RR to first IRL (not PDH)" — QUOTE_VERIFIED
- number and unit: **1.5:1** (risk multiple)
- OF_WHAT: distance to the first internal-range-liquidity pool ÷ stop distance
- COMPARED_TO_WHAT: the structural stop distance
- HOW_MANY_CANDLES: UNSTATED
- TIMEFRAME: 5-minute
- INSTRUMENT: FOREX (EUR/USD worked)
- independence: NOT_INDEPENDENT_OF_B3
- reason given by source: "below 1.5:1, skip the trade" — QUOTE_VERIFIED
- tier: TIER2

## Q7-09 — FundingPips
- id: Q7-09
- question: Q7
- URL: https://fundingpips.com/blog/ict-2022-model
- publisher: fundingpips.com
- author if shown: "By FundingPips"
- page date if shown: "October 18, 2026"
- type: TEACHING
- quote (<=25 words, English, verbatim): "The primary target is the draw on liquidity" — QUOTE_VERIFIED
- number and unit: NONE as a rule; the hypothetical works out to 2.7:1
- OF_WHAT: a price level (previous day's high, opposing pool)
- COMPARED_TO_WHAT: UNSTATED as a rule
- HOW_MANY_CANDLES: UNSTATED
- TIMEFRAME: UNSTATED
- INSTRUMENT: FOREX
- independence: INDEPENDENT_OF_PRIOR_SOURCES
- reason given by source: NO_REASON_GIVEN
- tier: TIER2

## Q7 — Counts (TEACHING only; exact versions)

| exact version (number | OF_WHAT | COMPARED_TO_WHAT) | independent publishers | of which new |
|---|---|---|---|---|
| minimum **1:2**, ideally 1:3 | target distance ÷ risk | the trade's own stop distance | 2 (Q7-01 theinnercircletraders, Q7-03/Q7-04 ictkillzone) | 0 |
| minimum **3:1** | target distance ÷ risk | stop size | 1 (Q7-02 ictflow) | 1 |
| **1:3** typical | target distance ÷ risk | risk | 1 (Q7-05 innercircletrader) | 0 |
| minimum **1.5:1** | target distance ÷ risk | stop distance | 1 (Q7-08 liquiditysweeps) | 0 |
| target = **opposing liquidity pool / draw on liquidity**, no multiple | a price level | UNSTATED | 5 (Q7-01, Q7-03, Q7-06 velotrade, Q7-07 backtrex, Q7-09 fundingpips) | 2 (velotrade, fundingpips) |
| absolute pip target **20–30 pips** | distance in pips | nothing | 1 (Q7-05 innercircletrader) | 0 |

**Q7 answer as found:** the *definition* of the target is near-unanimous in the fetched pages — an opposing
liquidity pool, named on the chart, with a partial at the first internal pool. The *number* is always expressed as
a risk multiple, and four different minimums are found (1.5:1, 1:2, 1:3, 3:1). No fetched source states a fixed pip
target as a rule; the one absolute figure (20–30 pips) belongs to a time-boxed scalping model.

### Q7 — pages checked (12)

| page | outcome |
|---|---|
| https://www.theinnercircletraders.com/ict-liquidity-zones/ | Q7-01 — 1:2 minimum |
| https://ictflow.com/blog/ict-complete-2022-trading-strategy | Q7-02 — 3:1 |
| https://www.ictkillzone.com/ict-fair-value-gap | Q7-03 — 1:2 + T1/T2 |
| https://www.ictkillzone.com/ict-order-block | Q7-04 — 1:2 + T1/T2 |
| https://innercircletrader.net/tutorials/ict-silver-bullet-strategy/ | Q7-05 — 1:3, 20–30 pips |
| https://velotrade.com/blog/fair-value-gap | Q7-06 — no rule, break-even table |
| https://backtrex.com/en/blog/ict-displacement-candle-market-concept | Q7-07 — no number |
| https://liquiditysweeps.com/ict-stop-loss/ | Q7-08 — 1.5:1 |
| https://fundingpips.com/blog/ict-2022-model | Q7-09 — no rule |
| https://www.ictkillzone.com/ict-equal-highs-lows | T1/T2 defined by pools, no new multiple (same publisher) |
| https://tmgm.com/en/academy/trading-academy/judas-swing | NOT_FETCHED (snippet: worked example 2:1, labelled illustrative) |
| https://damnpropfirms.com/glossary/ict-trading/ | NOT_FETCHED (snippet) |

---

# APPENDIX — prior-inventory domains used for the independence test

From `EXTERNAL_SOURCES_LOG.md` and `external_sources/*.md`:
alphametrixx.com, backtrex.com, bestprops.com, blog.pfhmarkets.com, briskmarkets.com, bullynx.com, datapips.net,
equiti.com, forexmt4indicators.com, forexmt4systems.com, forums.babypips.com, fxnx.com, homedadpro.com,
innercircletrader.net, innercircletraders.net, ironcladresearch.com, izict.fr, kenmacro.com, liquidityscan.io,
liquiditysweeps.com, mql5.com, myprimusmarkets.com, netpicks.com, proea.app, quantum-algo.com,
quartersequence.com, r2ftrading.com, signalpilot.io, snappchart.app, theinnercircletraders.com, thesimpleict.com,
tmgm.com, tradeify.co, tradingstrategyguides.com, volity.io, writofinance.com, x10hop.com.

**New publishers introduced by this file (independent of the above):** ictflow.com, fundingpips.com,
dhanith.com, chartwhisperer.ca, tradoshi.com, audacity.capital, brokercheck.co, arrowalgo.com, ebc.com,
velotrade.com, luxalgo.com, eltraderfinanciado.com, fortraders.com, github.com (Vatthu/v1indicators,
joshyattridge/smart-money-concepts), tradingview.com (two script authors: robert_yown, rcj101208).

**Known same-brand pairs (treated as one publisher):** fxprimus.com ≡ myprimusmarkets.com (identical text);
ictkillzone.com's pages share one author; luxalgo.com's concept and indicator pages are one publisher;
tradingstrategyguides.com's two order-block pages are one publisher; innercircletrader.net's four pages are one
publisher; fxnx.com's pages are one publisher.

---

# APPENDIX — IMPLEMENTATION_CODE inventory added by this file

| repo | commit | license | files read | lines | constants recorded |
|---|---|---|---|---|---|
| `joshyattridge/smart-money-concepts` | `1b62fd6c41e1f508e7ed76831a039fa4c82d42f6` | MIT | `smartmoneyconcepts/smc.py` | 987 total; 68–128, 137–160, 376–400, 404–545, 573–600 | `swing_length=50`, `range_percent=0.01`, `Percentage` volume ratio |
| `Vatthu/v1indicators` | `36785b982e55c4dfed20037e52fd92dbdf8f7f19` | MIT | `.../trend/order_blocks.py`, `.../trend/fair_value_gaps.py`, `.../levels/equal_highs_lows.py` | 7–71, 6–56, 7–61 | `periods=5`, `threshold=0.0` (twice), `length=3`, `threshold=0.1` percent, `use_wicks=False` |
| `kxngHADES/SMC-Marking` | `bb79d1dc6f945cdce043e243e28ba6e7b9599e8f` | none visible | `SMC_Terminology_marks.pine` | 569 total; 21–22, 56–58, 64–65, 71–72, 156, 268–292, 300–330, 344–362 | `swingLen=10`, `intLen=5`, `eqLen=3`, `eqThr=0.1`, `fvgMinAtr=0.0`, `atr(200)`, `obCount=3` |
| `kayasolomon/poi-liquidity-detector` | `951304b33c71ad6fedcabf957de6ab40134d5670` | MIT | `src/detector.ts`, `src/equalLevels.ts`, `src/fvg.ts`, `src/atr.ts`, `src/types.ts`, `README.md` | 9681 / 5014 / 2590 / 1556 / 4785 bytes | `minImpulseATR=1.5`, `atrPeriod=14`, `obLookback=20`, `fractalK=2`, `equalTolATR=0.25`, `sweepReversalMaxBars=20`, `zoneMode='body'`, `fvgFillMode='wick'` |
| `RebiccaT/smc-indicator-library` | `d1c985f496f305af8dd8fb05062659094e513eb5` | MIT | **none — repo contains only `LICENSE` and `README.md`** | — | `NO_CODE_PRESENT` |

Note on `RebiccaT/smc-indicator-library`: the repository root listing at that commit contains exactly two files,
`LICENSE` and `README.md`. There is **no indicator code to read**, so no constant is recorded from it and it is not
cited for any question. Recording it here so this dead end is not retried.

# STATUS SUMMARY (counts only)

| question | numeric exact versions found | publishers with no number | independent publishers contributing | pages fetched |
|---|---|---|---|---|
| Q1 displacement | 9 | 4 | 6 | 16 (2 snippet-only) |
| Q2 sweep timing | 5 candle-window versions + 1 penetration-depth version | 4 (no limit stated) | 8 | 15 (1 unreachable, 4 snippet-only) |
| Q3 equal highs | 4 tolerance bands + 1 percentage band | 3 | 8 | 15 (2 snippet-only) |
| Q4 order block | 2 zone conventions, 2 entry conventions | 2 ("neither official") | 6 | 12 |
| Q5 fair value gap | 1 numeric minimum size | 3 (unit only) + 2 (none) | 6 | 13 (2 snippet-only) |
| Q6 stop | 4 forex pip versions + 2 futures-point versions | 5 | 6 | 13 |
| Q7 target | 4 risk-multiple versions | 5 (no multiple) | 7 | 12 (2 snippet-only) |

**NO_SOURCE_FOUND** does not apply to any question: at least one page per question yielded a number with its
object of measurement. It does apply to single sub-questions, recorded inline above as `UNSTATED`:
Q1(c) "how many preceding candles" for the 1.5×ATR version; Q2(a) a limit for the four sources that give none;
Q3(a) a bar distance in any teaching page; Q3(c) a no-higher-high rule in any teaching page; Q4 the 50% reference
(body vs range) for two publishers; Q5(a) a value for three publishers; Q6 a pip buffer for five publishers;
Q7 a fixed pip rule for any publisher.
