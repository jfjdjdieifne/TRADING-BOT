# Analysis-process spec — how he thinks with a chart open

Scope: reconstructed **only** from SAID / DEMONSTRATED claims in `claims.jsonl`, all of which passed
`tools/verify_claims.py`. Almost all evidence comes from one worked example (Episode 12, NASDAQ March
2022 contract, C008). Where the sources do not say, the step reads `NOT_IN_SOURCES`. Steps are **not**
smoothed into a complete algorithm, and differences between examples are listed rather than merged.

Legend: `[Cxxx]` = claim id. A branch with no claim is written as a gap, not filled.

---

## Step 1 — Before looking for an entry: what is price likely doing?

**Q1. What is the current market narrative — what is it likely to be doing right now?** [C002]
He calls this the number one question he has before he sits down in front of his charts. [C001]

**Q2. Which of the alternatives is it?** The alternatives as he states them:
- up for stops, or down for stops [C003]
- up for buy side liquidity [C004]
- higher to rebalance, or lower to rebalance [C003 context; C043]

**Q3. What is the next draw on liquidity?** He treats "where's the market going next" as the next draw
on liquidity. [C005]

Branch: if he cannot justify one-sidedness → **neutral, do nothing** (Step 7). [C037, C036]

`NOT_IN_SOURCES`: how he enumerates candidate draws; how he ranks two competing draws; any checklist
order beyond the questions above.

---

## Step 2 — Which chart frames the idea?

**Q4. What is the daily chart likely to do over the next day or two?** He says the majority of study
time goes here. [C020] For a developing student he states a 5-day horizon. [C021]

**Q5. How do the timeframes relate?** When he expects the daily to be the parent of the price
structure, all minor lower-timeframe swings are subordinate to it. [C013]

**Q6. Which timeframe gives the actual get in / get out?** In this example he names the 15-minute
timeframe. [C025] The chart he is describing at the start is 1 hour. [C007]

`NOT_IN_SOURCES`: a general rule for choosing which higher timeframe to use; what to do when the daily
and the hourly disagree; timeframe selection outside this example.

---

## Step 3 — Label the swings

**Q7. Which swings are long-term, short-term, intermediate?** He says he outlined market structure as
long-term high/low, short-term high/low, with an intermediate term high and low between the two swing
points. [C006]

**Q8. Has an old imbalance been rebalanced?** Every rebalance of an old imbalance creates a swing he
immediately labels in his mind as an intermediate term high (or low). [C010, C011]

**Q9. Which of the two classifications applies?**
- a short-term high with lower short-term highs to the left and right [C027]
- or, "the main one", a swing that trades back up to rebalance an imbalance [C028]

For lows he describes an intermediate term low as having higher short-term lows on both sides. [C012]

`NOT_IN_SOURCES`: how many candles make a swing; how far left/right to look; any tolerance.

---

## Step 4 — Frame the trade zone

**Q10. Where is the order block?** In this example he uses the up closed candles as the range for the
hourly order block, and says the order block is one consecutive series of up closed candles, **not**
the last candle before the down move. [C017, C016]

**Q11. What is inside that range?** Inside that range he says he can be hunting fair value gaps. [C018]

**Q12. Where did price trade relative to the gap?** In the example price trades down to what he calls
the discount level of the low end of that fair value gap. [C054]

`NOT_IN_SOURCES`: how to decide that a series of candles has ended; how to pick among several gaps
inside one block; any minimum gap size.

---

## Step 5 — Evidence for and against the idea

**Evidence against (he names these):**
- price trading above the intermediate term high → the trade idea is probably flawed [C051]; that high
  should not be traded above [C053]
- key highs/lows being violated → the idea is wrong, cancel it [C032]

**Evidence for (he names these):**
- while the market moves in his favour, keep trusting the move and hold the trade [C033]
- in bullish swings down closed candles act as support; in bearish swings up closed candles act as
  resistance [C034]

**Structural break:** a break below an intermediate low he calls a significant break in market
structure [C022]; in the model he teaches, the short-term low being broken is the market structure
shift, then price goes up into the imbalance and then you can go short [C026]

`NOT_IN_SOURCES`: how much of a violation counts; whether a wick versus a close matters; how many
confirmations are required.

---

## Step 6 — Entry, stop, target

**Q13. Aggressive or confirmation entry?** He presents both:
- aggressive: no swing low needs to be broken [C029]
- classic higher-confirmation: the return back to an order block after trading down below it [C030]

**Q14. Where is the stop?** In the worked example: above that candle's high. [C031]

**Q15. Which target?** He gives more than one and does **not** rank them in the retrieved text:
- the range between the long-term high and long-term low is used for targeting purposes [C019]
- in the example he anchors the fib to the intermediate term high down to the long-term low [C023] and
  reads the projection at **-1 1/2 standard deviation** [C024]

`NOT_IN_SOURCES`: how he chooses between the range-based target and the fib projection when they
disagree; partial exits; scaling.

---

## Step 7 — When he decides not to trade

- Back above the old low in the example → "do nothing we're neutral right now". [C036]
- Reason given: he cannot justify one-sidedness. [C037]
- Having an account open and having time in front of the charts are listed as conditions that do not
  by themselves justify acting. [C040]
- In the example he states he is not trading anything and will let the rest of February pass without
  engaging. [C041]
- If his analysis level is violated he demands more information by studying more price action and
  "sitting on my hands". [C014]

`NOT_IN_SOURCES`: a rule for how long to stand aside; a re-entry trigger.

---

## Step 8 — When he decides he is wrong, and what he does then

1. Key high/low violated → idea is wrong → **cancel the idea**. [C032]
2. Do not force the trade again. [C051]
3. Wait for market structure to get back in sync with what he is expecting. [C052]
4. A stop-out is described as managing risk, not as proof the model is flawed. [C015]

`NOT_IN_SOURCES`: whether he reverses; whether he re-enters on the same level; any cooling-off rule.

---

## Differences between examples — listed, NOT merged

| item | Episode 12 (2022, mirror, FULL) | OB16 (2016 core content, PARTIAL chunk 0) |
|---|---|---|
| order block | "one consecutive series of up closed candles ... not the last candle before the down move" [C017] | "the lowest candle or price bar with a down close that has the most range" [C047]; validation = a later candle trades through its high [C048] |
| status | contradiction recorded as [C050], **not resolved** | |

Other non-merged items:
- FVG16 defines a fair value gap as a range in price delivery where one side of market liquidity is
  offered, typically confirmed with a lower-timeframe liquidity void [C049]. Episode 12 uses fair value
  gaps as objects to hunt inside an order block [C018]. These are different usages; not merged.
- Episode 3 points at an old low and relative equal highs and assigns sell stops below / buy stops
  above [C045], and says he will use the equal highs if higher than an old high [C046]. Episode 12 never
  uses the phrase "equal highs" in the retrieved text. Not merged.
- Episode 6 states time is the most important thing and time of day is vital [C044]. Episode 12's
  worked example gives no time-of-day condition. **The sequence above therefore has no time-of-day
  gate**, and none is invented.
- FVG24 (PARTIAL chunk 0) uses "discount opening range Gap", a different usage from Episode 12's
  "discount level of the low end of that fair value Gap" [C054]. No claim was extracted for the FVG24
  usage; recorded as a gap.

## Explicitly absent from the retrieved sequence

`NOT_IN_SOURCES`: dealing range, premium, equilibrium, equal lows, kill-zone/session time windows,
invalidation as a named rule, position sizing, risk percentage, news handling, and any numeric
threshold other than the two he states himself (5-day horizon [C021]; -1 1/2 standard deviation
[C024]) and the timeframe names he states (1 hour [C007], 15-minute [C025]).
