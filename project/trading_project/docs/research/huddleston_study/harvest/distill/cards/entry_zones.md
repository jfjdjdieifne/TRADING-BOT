# Entry zones (fair value gap, order block)

Every content line ends with the claim id(s) that support it. Fields the sources do not answer are marked `NOT_IN_SOURCES`.

## Essence

- A FVG is a 3-candle wick-to-wick imbalance: on candle n+1 the low trades above candle n-1's high (bullish), or the high trades below candle n-1's low (bearish). (CLM-0027)
  > "on candle n+1 the low trades above candle n-1's high (bullish), or the high trades below candle n-1's low (bearish)"
  > source: SrsBlack/ict-knowledge-library@9b089669 | concepts/06-fair-value-gaps/fair-value-gap.md | SrsBlack | BOOK_OR_COURSE — Definition section

## Properties

- 2016 definition: the extreme candle (lowest down-close for bullish, highest up-close for bearish) with the greatest open-to-close range among candidates. (CLM-0094)
  > "the extreme candle (lowest down-close for bullish, highest up-close for bearish) with the greatest open-to-close range among candidates" — SrsBlack/ict-knowledge-library@9b089669 | concepts/07-order-blocks/order-block-criteria.md | SrsBlack | BOOK_OR_COURSE
- Bullish Order Block: the last bearish candle before a strong bullish impulse move. (CLM-0086)
  > "(I) Bullish Order Block — the last bearish candle before a strong bullish impulse move." — innercircletrader.net (harvest web record) | web/pages/005_innercircletrader.net_ict-order-block.md | "Ayub Rana" shown in the page's own advertisement block ("Ayub Rana · based on ICT's methodology"); first-person article voice ("Used correctly, the Order Block tells me where institutional buyers or sellers are positioned") | EXPLAINER
- The second candle (bullish) must grab the low of the previous bearish candle before reversing. (CLM-0100)
  > "The second candle (bullish) must grab the low of the previous bearish candle — price goes below the low of the bearish OB before reversing." — innercircletrader.net (harvest web record) | web/pages/005_innercircletrader.net_ict-order-block.md | "Ayub Rana" shown in the page's own advertisement block ("Ayub Rana · based on ICT's methodology"); first-person article voice ("Used correctly, the Order Block tells me where institutional buyers or sellers are positioned") | EXPLAINER
- You are looking to buy with internal range liquidity or a bullish order block inside a previous range. (CLM-0021)
  > "you're looking to buy with internal range liquidity or a bullish order block inside a previous range" — newsqlguru/ict-index@e8c40a8d | transcriptions/2016-ICT-Private-Mentorship-Core-Content-Month-04/ICT-Mentorship-Core-Content-Month-04-Reinforcing-Liquidity-Concepts-&-Price-Delivery-001.json | newsqlguru | MICHAEL_WORDS
- Definition of a bullish order block is the lowest candle or price bar with a down close that has the most range. (CLM-0071)
  > "definition of a bullish order block is the lowest candle or price bar with a down close that has the most range" — Klout9/ict-strat@067d737e | Month 04 - Order Blocks Liquidity/03_Orderblocks.md | Klout9 | BOOK_OR_COURSE
- Validation of a bullish order block is when the high of the lowest down candle or price bar is traded through. (CLM-0072)
  > "validation of a bullish order block is when the high of the lowest down candle or price bar is traded through" — Klout9/ict-strat@067d737e | Month 04 - Order Blocks Liquidity/03_Orderblocks.md | Klout9 | BOOK_OR_COURSE
- The library quotes ICT: label number one candle[,] the number two candle is always going to be where the gap resides. (CLM-0028)
  > "label number one candle[,] the number two candle is always going to be where the gap resides" — SrsBlack/ict-knowledge-library@9b089669 | concepts/06-fair-value-gaps/fair-value-gap.md | SrsBlack | BOOK_OR_COURSE
- Candle n's range is left unworked in one direction. (CLM-0029)
  > "leaving candle n's range unworked in one direction" — SrsBlack/ict-knowledge-library@9b089669 | concepts/06-fair-value-gaps/fair-value-gap.md | SrsBlack | BOOK_OR_COURSE
- The gap that exists between the high of the first candle and the low of the third candle is the fair value gap. (CLM-0085)
  > "The gap that exists between the high of the first candle and the low of the third candle is the fair value gap." — innercircletraders.net (harvest web record) | web/pages/001_innercircletraders.net_ict-fair-value-gap.md | no byline visible on the retrieved chunk; site name "Inner Circle Traders" | EXPLAINER

## Relations

- Order blocks inside the trading range will be populated with new buys and or sells. (CLM-0018)
  > "order blocks inside the trading range will be populated with new buys and or sells" — newsqlguru/ict-index@e8c40a8d | transcriptions/2016-ICT-Private-Mentorship-Core-Content-Month-04/ICT-Mentorship-Core-Content-Month-04-Reinforcing-Liquidity-Concepts-&-Price-Delivery-001.json | newsqlguru | MICHAEL_WORDS
- Where a fair value Gap exists, if we start to trade higher we can expect to see the market want to reach up. (CLM-0019)
  > "we have a fair value Gap so if we start to trade higher we can expect to see the market want to reach up" — newsqlguru/ict-index@e8c40a8d | transcriptions/2016-ICT-Private-Mentorship-Core-Content-Month-04/ICT-Mentorship-Core-Content-Month-04-Reinforcing-Liquidity-Concepts-&-Price-Delivery-001.json | newsqlguru | MICHAEL_WORDS

## Context

- If you trade short at a bearish order block which is the last up candle that's going to be a return to internal range liquidity. (CLM-0014)
  > "if you trade short at a bearish order block which is the last up candle that's going to be a return to internal range liquidity" — newsqlguru/ict-index@e8c40a8d | transcriptions/2016-ICT-Private-Mentorship-Core-Content-Month-04/ICT-Mentorship-Core-Content-Month-04-Reinforcing-Liquidity-Concepts-&-Price-Delivery-001.json | newsqlguru | MICHAEL_WORDS
- Behavioral signature listed: frequent sweeps + displacement + FVG sequences. (CLM-0032)
  > "Frequent sweeps + displacement + FVG sequences." — SrsBlack/ict-knowledge-library@9b089669 | concepts/10-killzones/killzone-overview.md | SrsBlack | BOOK_OR_COURSE

## What it is chosen over

- CONFLICTED (CF-06)
- If you are optimising for fill probability, enter from the FVG. (CLM-0097)
  > "If you are optimising for fill probability (making sure you actually get into the trade), enter from the FVG." — theinnercircletraders.com (harvest web record) | web/pages/007_theinnercircletraders.com_fvg-vs-order-block.md | "The Inner Circle Traders" (site byline); "Updated July 2026"; labelled "Article 15 of 137" in cluster "PD Array Tools" | EXPLAINER
- The library states ICT's own Jan-2017 hierarchy lists the order block before the FVG. (CLM-0098)
  > "ICT's own Jan-2017 hierarchy lists the order block before the FVG" — SrsBlack/ict-knowledge-library@9b089669 | concepts/06-fair-value-gaps/fair-value-gap.md | SrsBlack | BOOK_OR_COURSE

## What invalidates it

- The library's audit note says displacement was removed as a formal criterion and was never part of ICT's geometric definition. (CLM-0093)
  > "Displacement was removed as a formal criterion — it was never part of ICT's geometric definition" — SrsBlack/ict-knowledge-library@9b089669 | concepts/06-fair-value-gaps/fair-value-gap.md | SrsBlack | BOOK_OR_COURSE
- The library says the prior last opposite candle criteria are not ICT's definition in either era. (CLM-0096)
  > "The prior "last opposite candle / displacement in 1–3 candles / breaks structure / ALL of" criteria are" — SrsBlack/ict-knowledge-library@9b089669 | concepts/07-order-blocks/order-block-criteria.md | SrsBlack | BOOK_OR_COURSE
- Without a strong, impulsive middle candle, there is no fair value gap in the ICT sense. (CLM-0084)
  > "Without a strong, impulsive middle candle, there is no fair value gap in the ICT sense." — innercircletraders.net (harvest web record) | web/pages/001_innercircletraders.net_ict-fair-value-gap.md | no byline visible on the retrieved chunk; site name "Inner Circle Traders" | EXPLAINER

## Worked examples in the sources

- Where a fair value Gap exists, if we start to trade higher we can expect to see the market want to reach up. (CLM-0019)
  > "we have a fair value Gap so if we start to trade higher we can expect to see the market want to reach up" — newsqlguru/ict-index@e8c40a8d | transcriptions/2016-ICT-Private-Mentorship-Core-Content-Month-04/ICT-Mentorship-Core-Content-Month-04-Reinforcing-Liquidity-Concepts-&-Price-Delivery-001.json | newsqlguru | MICHAEL_WORDS
- A low delineated for a potential liquidity run on sell stops below the low, then expect a turtle soup or false break below an old low. (CLM-0079)
  > "we have a low delineated for potential liquidity run on sell stops below the low" — SrsBlack/ict-knowledge-library@9b089669 | concepts/29-stop-runs/stop-run-into-fvg.md | SrsBlack | BOOK_OR_COURSE

## All claims tagged to this concept

- `CLM-0014` [SAID] If you trade short at a bearish order block which is the last up candle that's going to be a return to internal range liquidity.
  - quote: "if you trade short at a bearish order block which is the last up candle that's going to be a return to internal range liquidity"
  - source: newsqlguru/ict-index@e8c40a8d | transcriptions/2016-ICT-Private-Mentorship-Core-Content-Month-04/ICT-Mentorship-Core-Content-Month-04-Reinforcing-Liquidity-Concepts-&-Price-Delivery-001.json | newsqlguru | MICHAEL_WORDS
  - location: read window stop_invalidation hit word 1329, ctx 80
- `CLM-0018` [SAID] Order blocks inside the trading range will be populated with new buys and or sells.
  - quote: "order blocks inside the trading range will be populated with new buys and or sells"
  - source: newsqlguru/ict-index@e8c40a8d | transcriptions/2016-ICT-Private-Mentorship-Core-Content-Month-04/ICT-Mentorship-Core-Content-Month-04-Reinforcing-Liquidity-Concepts-&-Price-Delivery-001.json | newsqlguru | MICHAEL_WORDS
  - location: read window entry_zones hit word 282, ctx 75
- `CLM-0019` [SAID] Where a fair value Gap exists, if we start to trade higher we can expect to see the market want to reach up.
  - quote: "we have a fair value Gap so if we start to trade higher we can expect to see the market want to reach up"
  - source: newsqlguru/ict-index@e8c40a8d | transcriptions/2016-ICT-Private-Mentorship-Core-Content-Month-04/ICT-Mentorship-Core-Content-Month-04-Reinforcing-Liquidity-Concepts-&-Price-Delivery-001.json | newsqlguru | MICHAEL_WORDS
  - location: read window entry_zones hit word 877, ctx 75
- `CLM-0021` [SAID] You are looking to buy with internal range liquidity or a bullish order block inside a previous range.
  - quote: "you're looking to buy with internal range liquidity or a bullish order block inside a previous range"
  - source: newsqlguru/ict-index@e8c40a8d | transcriptions/2016-ICT-Private-Mentorship-Core-Content-Month-04/ICT-Mentorship-Core-Content-Month-04-Reinforcing-Liquidity-Concepts-&-Price-Delivery-001.json | newsqlguru | MICHAEL_WORDS
  - location: read window htf_ltf hit word 2714, ctx 80
- `CLM-0027` [DEFINED] A FVG is a 3-candle wick-to-wick imbalance: on candle n+1 the low trades above candle n-1's high (bullish), or the high trades below candle n-1's low (bearish).
  - quote: "on candle n+1 the low trades above candle n-1's high (bullish), or the high trades below candle n-1's low (bearish)"
  - source: SrsBlack/ict-knowledge-library@9b089669 | concepts/06-fair-value-gaps/fair-value-gap.md | SrsBlack | BOOK_OR_COURSE
  - location: Definition section
- `CLM-0028` [SAID] The library quotes ICT: label number one candle[,] the number two candle is always going to be where the gap resides.
  - quote: "label number one candle[,] the number two candle is always going to be where the gap resides"
  - source: SrsBlack/ict-knowledge-library@9b089669 | concepts/06-fair-value-gaps/fair-value-gap.md | SrsBlack | BOOK_OR_COURSE
  - location: Definition section (embedded citation ICT-2022-MENTORSHIP-EP06 [16:41]-[17:09] as given by the library)
- `CLM-0029` [DEFINED] Candle n's range is left unworked in one direction.
  - quote: "leaving candle n's range unworked in one direction"
  - source: SrsBlack/ict-knowledge-library@9b089669 | concepts/06-fair-value-gaps/fair-value-gap.md | SrsBlack | BOOK_OR_COURSE
  - location: Definition section
- `CLM-0030` [DEFINED] An order block (OB) is ICT's reference zone for the institutional candle(s) that precede a directional move.
  - quote: "An order block (OB) is ICT's reference zone for the institutional candle(s) that precede a directional move."
  - source: SrsBlack/ict-knowledge-library@9b089669 | concepts/07-order-blocks/order-block-criteria.md | SrsBlack | BOOK_OR_COURSE
  - location: Definition section
- `CLM-0071` [DEFINED] Definition of a bullish order block is the lowest candle or price bar with a down close that has the most range.
  - quote: "definition of a bullish order block is the lowest candle or price bar with a down close that has the most range"
  - source: Klout9/ict-strat@067d737e | Month 04 - Order Blocks Liquidity/03_Orderblocks.md | Klout9 | BOOK_OR_COURSE
  - location: file text after header (chars 300-1100 read)
- `CLM-0072` [DEFINED] Validation of a bullish order block is when the high of the lowest down candle or price bar is traded through.
  - quote: "validation of a bullish order block is when the high of the lowest down candle or price bar is traded through"
  - source: Klout9/ict-strat@067d737e | Month 04 - Order Blocks Liquidity/03_Orderblocks.md | Klout9 | BOOK_OR_COURSE
  - location: same window
- `CLM-0079` [SAID] A low delineated for a potential liquidity run on sell stops below the low, then expect a turtle soup or false break below an old low.
  - quote: "we have a low delineated for potential liquidity run on sell stops below the low"
  - source: SrsBlack/ict-knowledge-library@9b089669 | concepts/29-stop-runs/stop-run-into-fvg.md | SrsBlack | BOOK_OR_COURSE
  - location: Dating note quoting ICT-2016-FVG-REINFORCED 06:42-07:09
- `CLM-0084` [SAID] Without a strong, impulsive middle candle, there is no fair value gap in the ICT sense.
  - quote: "Without a strong, impulsive middle candle, there is no fair value gap in the ICT sense."
  - source: innercircletraders.net (harvest web record) | web/pages/001_innercircletraders.net_ict-fair-value-gap.md | no byline visible on the retrieved chunk; site name "Inner Circle Traders" | EXPLAINER
  - location: web record, quote 4 of 8 (chunk 0 of 3)
- `CLM-0085` [DEFINED] The gap that exists between the high of the first candle and the low of the third candle is the fair value gap.
  - quote: "The gap that exists between the high of the first candle and the low of the third candle is the fair value gap."
  - source: innercircletraders.net (harvest web record) | web/pages/001_innercircletraders.net_ict-fair-value-gap.md | no byline visible on the retrieved chunk; site name "Inner Circle Traders" | EXPLAINER
  - location: web record, quote 3 of 8
- `CLM-0086` [DEFINED] Bullish Order Block: the last bearish candle before a strong bullish impulse move.
  - quote: "(I) Bullish Order Block — the last bearish candle before a strong bullish impulse move."
  - source: innercircletrader.net (harvest web record) | web/pages/005_innercircletrader.net_ict-order-block.md | "Ayub Rana" shown in the page's own advertisement block ("Ayub Rana · based on ICT's methodology"); first-person article voice ("Used correctly, the Order Block tells me where institutional buyers or sellers are positioned") | EXPLAINER
  - location: web record, quote 4 of 9 (chunk 0 of 4)
- `CLM-0088` [DEFINED] OTE (Optimal Trade Entry) is the 62–79% Fibonacci retracement zone.
  - quote: "**OTE (Optimal Trade Entry)** — the 62–79% Fibonacci retracement zone, treated as the high-probability entry pocket inside a swing."
  - source: propnavi.io (harvest web record) | web/pages/009_propnavi.io_ict-trading-strategy.md | no individual byline in the retrieved page; site "PROP NAVI" | EXPLAINER
  - location: web record, quote 6 of 10 (complete page)
- `CLM-0092` [DEFINED] Optimal Trade Entry (OTE) is described as the 0.62–0.79 retrace zone.
  - quote: "Optimal Trade Entry (OTE) — the 0.62–0.79 retrace zone"
  - source: nqbacktest.online (harvest web record) | web/pages/004_nqbacktest.online_inner-circle-trader.md | no individual byline; site "NQ Replay / nqbacktest.online" | EXPLAINER
  - location: web record, quote 7 of 10
- `CLM-0093` [AMBIGUOUS] The library's audit note says displacement was removed as a formal criterion and was never part of ICT's geometric definition.
  - quote: "Displacement was removed as a formal criterion — it was never part of ICT's geometric definition"
  - source: SrsBlack/ict-knowledge-library@9b089669 | concepts/06-fair-value-gaps/fair-value-gap.md | SrsBlack | BOOK_OR_COURSE
  - location: file edit note above the Definition section (chars 900-1500 read)
- `CLM-0094` [DEFINED] 2016 definition: the extreme candle (lowest down-close for bullish, highest up-close for bearish) with the greatest open-to-close range among candidates.
  - quote: "the extreme candle (lowest down-close for bullish, highest up-close for bearish) with the greatest open-to-close range among candidates"
  - source: SrsBlack/ict-knowledge-library@9b089669 | concepts/07-order-blocks/order-block-criteria.md | SrsBlack | BOOK_OR_COURSE
  - location: Definition section
- `CLM-0095` [SAID] 2022: it's just [a] change in the state of delivery.
  - quote: "it's just [a] change in the state of delivery"
  - source: SrsBlack/ict-knowledge-library@9b089669 | concepts/07-order-blocks/order-block-criteria.md | SrsBlack | BOOK_OR_COURSE
  - location: Definition section citing ICT-2022-MENTORSHIP-EP03 [24:16]
- `CLM-0096` [AMBIGUOUS] The library says the prior last opposite candle criteria are not ICT's definition in either era.
  - quote: "The prior "last opposite candle / displacement in 1–3 candles / breaks structure / ALL of" criteria are"
  - source: SrsBlack/ict-knowledge-library@9b089669 | concepts/07-order-blocks/order-block-criteria.md | SrsBlack | BOOK_OR_COURSE
  - location: file edit note above Definition
- `CLM-0097` [SAID] If you are optimising for fill probability, enter from the FVG.
  - quote: "If you are optimising for fill probability (making sure you actually get into the trade), enter from the FVG."
  - source: theinnercircletraders.com (harvest web record) | web/pages/007_theinnercircletraders.com_fvg-vs-order-block.md | "The Inner Circle Traders" (site byline); "Updated July 2026"; labelled "Article 15 of 137" in cluster "PD Array Tools" | EXPLAINER
  - location: web record, quote 8 of 8 (chunk 0 of 3)
- `CLM-0098` [AMBIGUOUS] The library states ICT's own Jan-2017 hierarchy lists the order block before the FVG.
  - quote: "ICT's own Jan-2017 hierarchy lists the order block before the FVG"
  - source: SrsBlack/ict-knowledge-library@9b089669 | concepts/06-fair-value-gaps/fair-value-gap.md | SrsBlack | BOOK_OR_COURSE
  - location: file edit note above Definition (chars 900-1500 read)
- `CLM-0100` [DEFINED] The second candle (bullish) must grab the low of the previous bearish candle before reversing.
  - quote: "The second candle (bullish) must grab the low of the previous bearish candle — price goes below the low of the bearish OB before reversing."
  - source: innercircletrader.net (harvest web record) | web/pages/005_innercircletrader.net_ict-order-block.md | "Ayub Rana" shown in the page's own advertisement block ("Ayub Rana · based on ICT's methodology"); first-person article voice ("Used correctly, the Order Block tells me where institutional buyers or sellers are positioned") | EXPLAINER
  - location: web record, quote 6 of 9
