# Understanding card — buy side liquidity

Windows extracted for this concept: **15** (target 15). Meets the 15-window budget.
Claims: U0008, U0009, U0010, U0011, U0012, U0013, U0014

Every quoted line below is verbatim (≤25 words) from a window logged this session. Section (c) is explicitly an ENGINEERING_HYPOTHESIS, not his words. Empty sections read NOT_IN_SOURCES.

## (a) PURPOSE
NOT_IN_SOURCES

## (b) RECOGNITION (his criteria and his rejections)
- Buy side liquidity is what resides above relative equal highs.
  > "they leave up here relative equal highs so what's residing above here buy side liquidity"
  `[U0008]` · `ICT-Institutional-Price-Action-Micro-Market-Structure-&-Time-&-Price-Concepts-Part-02-001.json` · window `W0030`
- A void of buy side liquidity means the market moved aggressively away from a consolidation.
  > "there's a void of buy side liquidity that means the markets aggressively moved away from that consolidation"
  `[U0009]` · `ICT-Mentorship-Core-Content-Month-04-Liquidity-Voids-001.json` · window `W0026` · note: definition pattern "that means"

## (c) OBSERVABLES — ENGINEERING_HYPOTHESIS (needs owner approval)
- a level qualifies by having two or more near-equal highs above which resting orders are presumed; the observable is near-equality relative to local swing spacing, not an absolute tolerance
  `candle_observable: true` · derived from `U0008` · **ENGINEERING_HYPOTHESIS — needs owner approval**
- a run is observable as a trade above that level followed by closes back below it
  `candle_observable: true` · derived from `U0011`, `U0013` · **ENGINEERING_HYPOTHESIS — needs owner approval**
- that orders actually rest there is not visible on candles
  `candle_observable: false` · derived from `U0008` · **ENGINEERING_HYPOTHESIS — needs owner approval**

## (d) HOW HE TREATS IT
- After price runs the buy side liquidity above a high he looks to short and wait.
  > "Right Above This high would be buy side liquidity it runs it we look to short that and wait"
  `[U0011]` · `ICT-Charter-Price-Action-Model-10-Trade-Plan-&-Algorithmic-Theory-001.json` · window `W0023`

## (e) COMPARING INSTANCES
NOT_IN_SOURCES

## (f) INTERACTIONS
- A rejection block wick above the candle body runs the buy side liquidity out before price declines.
  > "up above the body of the candle or candles to run the buy side liquidity out before the price declines"
  `[U0013]` · `ICT-Mentorship-Core-Content-Month-04-ICT-Rejection-Block-001.json` · window `W0024`
- In the worked example the market rallies at 9:30 and trades up to a buy side liquidity pool shown on the 15-minute timeframe.
  > "the market rallies at 9 30. trades up to the buy side liquidity pool that I showed you on the 15-minute time frame"
  `[U0014]` · `2023-ICT-Mentorship-Opening-Range-Gap-Repricing-Macro-001.json` · window `W0028` · note: numbers 9 30 and 15-minute are his, not thresholds I chose

## (g) TIMEFRAME
- He locates buy side liquidity above a high on a weekly chart and says the market will want to seek it.
  > "this is a weekly chart the market will want to seek the buy side liquidity above"
  `[U0012]` · `ICT-Charter-Price-Action-Model-6-3-Supplementary-Lesson-001.json` · window `W0020`

## (h) FAILURE / INVALIDATION and DISCRETION
NOT_IN_SOURCES

## (i) VARIANTS (kept parallel, never merged)
- He reduces delivery to an enumeration: buy side run, sell side run, or inefficiency run/rebalance.
  > "there's either buy side liquidity run south side liquidity run or inefficient run rebalance"
  `[U0010]` · `ICT-Institutional-Price-Action-Micro-Market-Structure-&-Time-&-Price-Concepts-Part-02-001.json` · window `W0029` · note: [sic-asr] "south side" = sell side; not corrected

