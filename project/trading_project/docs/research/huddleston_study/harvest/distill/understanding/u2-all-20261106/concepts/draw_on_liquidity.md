# Understanding card — draw on liquidity

Windows extracted for this concept: **15** (target 15). Meets the 15-window budget.
Claims: U0001, U0002, U0003, U0004, U0005, U0006, U0007

Every quoted line below is verbatim (≤25 words) from a window logged this session. Section (c) is explicitly an ENGINEERING_HYPOTHESIS, not his words. Empty sections read NOT_IN_SOURCES.

## (a) PURPOSE
- He says knowing the location of the draw on liquidity is a requirement.
  > "you have to know where the draw on liquidity is"
  `[U0001]` · `ICT-Forex-Market-Maker-Series-Vol-2-of-5-001.json` · window `W0003`
- He reduces the whole reading task to locating the next likely draw on liquidity.
  > "all I need to know is where's the next likely draw on liquidity so I'm stripping the market down"
  `[U0002]` · `ICT-Charter-Price-Action-Model-10-Trade-Plan-&-Algorithmic-Theory-001.json` · window `W0006`

## (b) RECOGNITION (his criteria and his rejections)
- Old lows/highs and the previous weekly high or low are named as candidates for the draw.
  > "those old lows or highs previous weekly high or low as a draw on liquidity"
  `[U0004]` · `2023-ICT-Mentorship-ICT-Silver-Bullet-Time-Based-Trading-Model-001.json` · window `W0009`

## (c) OBSERVABLES — ENGINEERING_HYPOTHESIS (needs owner approval)
- a candidate target is a prior swing extreme or an unfilled range that price has not yet returned into, ranked by whether it is still untouched rather than by distance
  `candle_observable: true` · derived from `U0004`, `U0005` · **ENGINEERING_HYPOTHESIS — needs owner approval**
- arrival is not bound to the next bar or next day; the observable is eventual return, not elapsed time
  `candle_observable: unknown` · derived from `U0006` · **ENGINEERING_HYPOTHESIS — needs owner approval**

## (d) HOW HE TREATS IT
- He insists a trade need not be held all the way to the draw on liquidity.
  > "I did not need to trade to the draw on liquidity this is a crucial Point folks don't insist"
  `[U0007]` · `ICT-Emini-S&P-500-AM-Session-Review-09-06-22-001.json` · window `W0004`

## (e) COMPARING INSTANCES
- He ranks locating the next draw on liquidity above holding a bias.
  > "necessarily the bias you just predominantly have to consider where the next draw on liquidity is"
  `[U0003]` · `2023-ICT-Mentorship-ICT-Silver-Bullet-Time-Based-Trading-Model-001.json` · window `W0008` · note: comparative: "predominantly" over bias

## (f) INTERACTIONS
- An unfilled gap is itself named a draw on liquidity because price generally looks to fill it.
  > "price will generally look to fill these gaps okay that is a draw on liquidity"
  `[U0005]` · `OTE-Pattern-Recognition-Series-Vol-16-001.json` · window `W0013`

## (g) TIMEFRAME
- A draw identified on one day is not a promise of arrival the next day; it is a tendency over a period of time.
  > "Monday doesn't mean it's going to go there Tuesday it just means over a period of time"
  `[U0006]` · `OTE-Pattern-Recognition-Series-Vol-16-001.json` · window `W0014` · note: timing discretion

## (h) FAILURE / INVALIDATION and DISCRETION
NOT_IN_SOURCES

## (i) VARIANTS (kept parallel, never merged)
NOT_IN_SOURCES

