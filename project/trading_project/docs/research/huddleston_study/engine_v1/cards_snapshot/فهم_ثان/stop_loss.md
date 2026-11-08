# Understanding card — stop loss

Windows extracted for this concept: **15** (target 15). Meets the 15-window budget.
Claims: U0107, U0108, U0109, U0110, U0111, U0112

Every quoted line below is verbatim (≤25 words) from a window logged this session. Section (c) is explicitly an ENGINEERING_HYPOTHESIS, not his words. Empty sections read NOT_IN_SOURCES.

## (a) PURPOSE
NOT_IN_SOURCES

## (b) RECOGNITION (his criteria and his rejections)
- The stop loss goes below the mean threshold in the framed low risk setup.
  > "this is where our stop loss would be which would be below the mean threshold"
  `[U0107]` · `ICT-Mentorship-Core-Content-Month-02-Framing-Low-Risk-Trade-Setups-001.json` · window `W0233` · note: he also states a 20 pip stop in that example
- He wants the stop loss below the low of that down closed candle.
  > "that down closed candle I want to have my stop loss below that low"
  `[U0110]` · `ICT-2023-Mentorship-ES-Live-Execution-&-Mean-Threshold-Risk-Management-001.json` · window `W0240`

## (c) OBSERVABLES — ENGINEERING_HYPOTHESIS (needs owner approval)
- placement is structural: beyond the low/high of the specific candle or the mean threshold of the zone, not a fixed distance
  `candle_observable: true` · derived from `U0106`, `U0109` · **ENGINEERING_HYPOTHESIS — needs owner approval**
- a hit stop is not evidence the idea was invalid; invalidation and stop placement are separate observables
  `candle_observable: unknown` · derived from `U0108` · **ENGINEERING_HYPOTHESIS — needs owner approval**

## (d) HOW HE TREATS IT
- He uses a four handle stop loss because the gap might completely close.
  > "use a four handle stop loss because it might completely close that in"
  `[U0111]` · `2022-ICT-Mentorship-Ends-Series-Part-4-of-4-001.json` · window `W0236` · note: number four is his

## (e) COMPARING INSTANCES
- Applying higher time frame levels to lower time frame charts allows smaller stop loss placement and by default lower risk.
  > "higher time frame levels to lower time frame charts allows for smaller stop loss placement and by default lower risk"
  `[U0108]` · `ICT-Mentorship-Core-Content-Month-02-Framing-Low-Risk-Trade-Setups-001.json` · window `W0234` · note: comparative: smaller / lower
- A different order type creates more gap between the entry and where the stop loss goes.
  > "that creates a little bit more Gap in between where you're entering and where your stop loss is going"
  `[U0112]` · `ICT-Mentorship-Core-Content-Month-05-Position-Trade-Management-001.json` · window `W0229` · note: comparative: "more Gap"

## (f) INTERACTIONS
NOT_IN_SOURCES

## (g) TIMEFRAME
NOT_IN_SOURCES

## (h) FAILURE / INVALIDATION and DISCRETION
- A stop being hit does not mean the trade is no longer viable; it may mean the stop placement was inaccurate.
  > "it doesn't mean the trades completely no longer viable it just means that we probably were just inaccurate in terms of where our stop loss"
  `[U0109]` · `ICT-Mentorship-Core-Content-Month-02-How-To-Mitigate-Losing-Trades-Effectively-001.json` · window `W0237` · note: failure semantics, not invalidation of the idea

## (i) VARIANTS (kept parallel, never merged)
NOT_IN_SOURCES

