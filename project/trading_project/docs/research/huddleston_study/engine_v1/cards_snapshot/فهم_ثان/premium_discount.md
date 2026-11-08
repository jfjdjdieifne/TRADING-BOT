# Understanding card — premium discount

Windows extracted for this concept: **15** (target 15). Meets the 15-window budget.
Claims: U0083, U0084, U0085, U0086, U0087, U0088

Every quoted line below is verbatim (≤25 words) from a window logged this session. Section (c) is explicitly an ENGINEERING_HYPOTHESIS, not his words. Empty sections read NOT_IN_SOURCES.

## (a) PURPOSE
NOT_IN_SOURCES

## (b) RECOGNITION (his criteria and his rejections)
- A premium market means it is at a really high price relative to its current trading range.
  > "a premium market that means it's at a really high price relative to its current trading range"
  `[U0083]` · `ICT-Mentorship-Core-Content-Month-1-Equilibrium-Vs-Premium-001.json` · window `W0172` · note: definition; explicitly RELATIVE to the current trading range
- From an old high and old low he can see where the premium and discount market ranges exist.
  > "its old High and it's old low we can see where the premium and discount Market ranges exist"
  `[U0085]` · `ICT-Mentorship-Core-Content-Month-07-Short-Term-Trading-Blending-IPDA-Data-Ranges-&-PD-Arrays-001.json` · window `W0174`

## (c) OBSERVABLES — ENGINEERING_HYPOTHESIS (needs owner approval)
- position within the current range, expressed as above/below its midpoint; no absolute price meaning
  `candle_observable: true` · derived from `U0082`, `U0084` · **ENGINEERING_HYPOTHESIS — needs owner approval**
- the carrying-charge sense of premium is a different observable entirely (near vs deferred contract price) and needs contract data, not candles
  `candle_observable: false` · derived from `U0087` · **ENGINEERING_HYPOTHESIS — needs owner approval**

## (d) HOW HE TREATS IT
- When markets are bearish he works from a premium market down to a discount.
  > "when the markets are bearish we work from a premium Market down to a discount"
  `[U0084]` · `ICT-Mentorship-Core-Content-Month-07-Short-Term-Trading-Blending-IPDA-Data-Ranges-&-PD-Arrays-001.json` · window `W0174`

## (e) COMPARING INSTANCES
- He refers to the most active premium arrays.
  > "you're going to refer to the most active premium arrays"
  `[U0087]` · `ICT-Mentorship-Core-Content-Month-06-Classic-Swing-Trading-Approach-001.json` · window `W0176` · note: comparative: "most active"

## (f) INTERACTIONS
- The premium PD array matrix is where the bearish order blocks, liquidity voids, breakers and mitigation blocks live.
  > "this is where all the bearish order blocks bearish liquidity voids bearish Breakers Bears mitigation"
  `[U0086]` · `ICT-Mentorship-Core-Content-Month-06-Classic-Swing-Trading-Approach-001.json` · window `W0176`

## (g) TIMEFRAME
NOT_IN_SOURCES

## (h) FAILURE / INVALIDATION and DISCRETION
NOT_IN_SOURCES

## (i) VARIANTS (kept parallel, never merged)
- In a carrying charge market premium means today's price being higher than that of the deferred month, a different sense of the word.
  > "we're seeing a clear obvious premium and that's seen by today's price being higher than that of the"
  `[U0088]` · `ICT-Mentorship-Core-Content-Month-10-Premium-Vs-Carrying-Charge-Market-001.json` · window `W0168` · note: parallel meaning: commodity carry, NOT range position; kept separate

