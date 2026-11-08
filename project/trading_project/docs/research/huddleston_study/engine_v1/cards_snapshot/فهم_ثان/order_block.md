# Understanding card — order block

Windows extracted for this concept: **15** (target 15). Meets the 15-window budget.
Claims: U0045, U0046, U0047, U0048, U0049, U0050, U0051, U0052, U0053, U0054

Every quoted line below is verbatim (≤25 words) from a window logged this session. Section (c) is explicitly an ENGINEERING_HYPOTHESIS, not his words. Empty sections read NOT_IN_SOURCES.

## (a) PURPOSE
- Price trading down into a down candle or bullish order block takes over the role of price support.
  > "down into a down candle or bullish order block and takes over the role of price support"
  `[U0049]` · `ICT-Mentorship-Core-Content-Month-04-ICT-Propulsion-Block-001.json` · window `W0092`

## (b) RECOGNITION (his criteria and his rejections)
- He rejects the last candle: the order block really begins at this candle's opening, not this last one.
  > "the order block really begins at this candle's opening not this last one"
  `[U0045]` · `ICT-Mentorship-Core-Content-Month-05-Trade-Conditions-&-Setup-Progressions-001.json` · window `W0099` · note: REJECTION "not this last one"
- Two down candles are activated as a bullish order block.
  > "we have activated two two down candles as a bullish order block"
  `[U0047]` · `ICT-Mentorship-Core-Content-Month-03-The-Next-Setup-Anticipatory-Skill-Development-001.json` · window `W0101`
- He explicitly allows that something is not an order block even though price trades there.
  > "even though this is not an order block by"
  `[U0051]` · `ICT-Precision-Trading-Concepts-2-001.json` · window `W0098` · note: REJECTION; the criterion after "by" is outside the quote - recorded as a gap

## (c) OBSERVABLES — ENGINEERING_HYPOTHESIS (needs owner approval)
- a run of same-direction closes whose START is the opening of the first candle in the run, not the last candle before the move
  `candle_observable: true` · derived from `U0045`, `U0047` · **ENGINEERING_HYPOTHESIS — needs owner approval**
- the competing single-candle framing must be carried as a separate definition_id, not averaged
  `candle_observable: true` · derived from `U0046` · **ENGINEERING_HYPOTHESIS — needs owner approval**
- violation is observable as price trading through the far side of that run
  `candle_observable: true` · derived from `U0048` · **ENGINEERING_HYPOTHESIS — needs owner approval**
- what makes something NOT an order block is cut off in the read window
  `candle_observable: unknown` · derived from `U0051` · **ENGINEERING_HYPOTHESIS — needs owner approval**

## (d) HOW HE TREATS IT
- For risk he takes attention back down to the bullish order block because it gives everything needed.
  > "we take our attention back down to that bullish order block because it's going to give you everything you need"
  `[U0050]` · `ICT-Mentorship-Core-Content-Month-04-Orderblocks-001.json` · window `W0095`
- Near the high of the order block he sets an alert.
  > "that high of that order block when we're close to it we can now set an alert"
  `[U0054]` · `ICT-Mentorship-Core-Content-Month-04-Orderblocks-001.json` · window `W0096`

## (e) COMPARING INSTANCES
NOT_IN_SOURCES

## (f) INTERACTIONS
NOT_IN_SOURCES

## (g) TIMEFRAME
- Dropping to a daily chart shows a lot more definition of the bullish candle which is the bears order block.
  > "you see a lot more definition on the daily chart bullish candle which is the bears order block"
  `[U0052]` · `ICT-Mentorship-Core-Content-Month-03-Institutional-Order-Flow-001.json` · window `W0103` · note: comparative: "a lot more definition"
- Price back up into a monthly order block level becomes a weekly order block level as well.
  > "back up into a monthly order Block Level and becomes a weekly order Block Level as well"
  `[U0053]` · `ICT-Mentorship-Core-Content-Month-06-High-Probability-Swing-Trade-Setups-In-Bear-Markets-001.json` · window `W0094`

## (h) FAILURE / INVALIDATION and DISCRETION
- He describes price violating the two down candles.
  > "it violates the two down candles"
  `[U0048]` · `ICT-Mentorship-Core-Content-Month-03-The-Next-Setup-Anticipatory-Skill-Development-001.json` · window `W0101` · note: short quote, failure wording

## (i) VARIANTS (kept parallel, never merged)
- Elsewhere he calls the last up candle the bearish order block.
  > "we have this last up candle that's the bearish order block"
  `[U0046]` · `ICT-Mentorship-Core-Content-Month-04-ICT-Propulsion-Block-001.json` · window `W0091` · note: parallel alternative to the opening-based framing; kept, not merged

