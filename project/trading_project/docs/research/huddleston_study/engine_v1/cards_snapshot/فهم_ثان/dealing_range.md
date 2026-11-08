# Understanding card — dealing range

Windows extracted for this concept: **15** (target 15). Meets the 15-window budget.
Claims: U0070, U0071, U0072, U0073, U0074, U0075, U0076, U0077

Every quoted line below is verbatim (≤25 words) from a window logged this session. Section (c) is explicitly an ENGINEERING_HYPOTHESIS, not his words. Empty sections read NOT_IN_SOURCES.

## (a) PURPOSE
- He asks where we are in the range and which dealing range highs and lows we are working within.
  > "where are we at in the range what dealing range highs and lows are we working within"
  `[U0077]` · `ICT-Precision-Trading-Concepts-3-001.json` · window `W0143`

## (b) RECOGNITION (his criteria and his rejections)
- He is asked what he means by dealing range and answers that it is where market structure has provided a means for a trading opportunity.
  > "a dealing range is where market structure has provided a means for a trading opportunity"
  `[U0070]` · `The-Inner-Circle-Trader-Live-Test-Stream-001.json` · window `W0144` · note: definition pattern "is where"
- He rejects one candidate: that is where you start and define the dealing range, not this.
  > "that is where you start and you define the dealing range not this because this"
  `[U0071]` · `ICT-Charter-Price-Action-Model-#4-Supplementary-Lesson-002.json` · window `W0138` · note: REJECTION "not this"

## (c) OBSERVABLES — ENGINEERING_HYPOTHESIS (needs owner approval)
- the range is bounded by the high and low of the most recent delivery leg, chosen over older legs
  `candle_observable: true` · derived from `U0071`, `U0076` · **ENGINEERING_HYPOTHESIS — needs owner approval**
- failure is observable as trading outside those bounds
  `candle_observable: true` · derived from `U0072` · **ENGINEERING_HYPOTHESIS — needs owner approval**
- which structure has provided a means for opportunity is a judgement he does not reduce to candles
  `candle_observable: unknown` · derived from `U0069` · **ENGINEERING_HYPOTHESIS — needs owner approval**

## (d) HOW HE TREATS IT
- He works within a defined dealing range; if bullish he looks at previous days highs.
  > "you work within a defined dealing range if you're bullish you're looking at previous days highs"
  `[U0074]` · `ICT-Charter-Price-Action-Model-1-Amplified-Lecture-001.json` · window `W0146`
- Inside the current dealing range at a discount, the ideal scenario for buying is to see a low that is violated.
  > "if we're in a discount the ideal scenario for buying is we want to see a low that's violated"
  `[U0075]` · `ICT-Charter-Price-Action-Model-1-Amplified-Lecture-001.json` · window `W0147` · note: degree word "ideal scenario"

## (e) COMPARING INSTANCES
- With two stages to the delivery he wants to use the most recent one as his dealing range.
  > "i had two stages to this delivery i want to use this most recent one and this is my dealing range"
  `[U0072]` · `2022-ICT-Mentorship-Episode-35-001.json` · window `W0140` · note: preference between instances: "most recent"

## (f) INTERACTIONS
- He waits for the market to break below a dealing range for external range liquidity in the form of sell side.
  > "we wait for the market to break below a dealing range for external range liquidity in the form of cell side"
  `[U0076]` · `ICT-Charter-Price-Action-Model-10-Trade-Plan-&-Algorithmic-Theory-001.json` · window `W0137` · note: [sic-asr] "cell side" = sell side

## (g) TIMEFRAME
NOT_IN_SOURCES

## (h) FAILURE / INVALIDATION and DISCRETION
- Price trading outside of its dealing range high is not what he wants to see.
  > "traded outside of its dealing Range High that's not what we want to see"
  `[U0073]` · `April-13-2023-Live-Tape-Reading-Emini-S&P-AM-Session-002.json` · window `W0149` · note: REJECTION

## (i) VARIANTS (kept parallel, never merged)
NOT_IN_SOURCES

