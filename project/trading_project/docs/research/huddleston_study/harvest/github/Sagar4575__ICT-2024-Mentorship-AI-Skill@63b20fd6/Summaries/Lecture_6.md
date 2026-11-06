# ICT 2024 Mentorship - Lecture 6 Summary (August 12, 2024)

## Trading Environment Ahead of High-Impact News
- **The Monday Problem:** When high-impact economic data (like CPI or PPI) is scheduled for Tuesday and Wednesday, the market behavior on Monday is generally extremely choppy.
- **Seek and Destroy Profile:** The algorithm enters a "Seek and Destroy" mode, meaning it will continually run short-term highs and short-term lows in a back-and-forth consolidation without offering sustained, one-directional price runs.
- **Early Execution:** If you decide to trade on such a Monday, your highest probability of success is executing *before* the 9:30 AM EST equities opening bell (e.g., utilizing the 7:00 AM to 8:30 AM window). Once the 9:30 AM bell rings, volatility and erratic price action make holding a position very difficult.

## Establishing Daily & Session Bias
- **The 7:00 AM Checkpoint:** When you sit at your charts at 7:00 AM EST, immediately locate price relative to the New Week Opening Gap (NWOG) and previous New Day Opening Gaps (NDOGs).
- **The Gravitational Draw:**
  - If price is **above** the NWOG and NDOGs, the algorithmic draw on liquidity is downward (Sell-Side Delivery). The market will seek the discount of those gaps.
  - If price is **below** the NWOG and NDOGs, the algorithmic draw is upward (Buy-Side Delivery).
- **Delayed TGIF:** If a trending market failed to give a "Thank God It's Friday" (TGIF) 20% to 30% retracement on Friday, expect that retracement to simply be deferred to Monday's trading session.

## The Entry Setup and Execution
1. **Identify the 7:00 AM Price:** Draw a line at the 7:00 AM EST starting point. 
2. **Wait for Relative Equal Highs/Lows:** Let the algorithm engineer initial liquidity by leaving clean highs or lows. 
3. **The Stop Hunt (Manipulation):** Watch price sweep/pierce those relative equal highs (or lows) to trigger stops. Note: Do not view this as an "institutional FU candle" (a retail myth). It is simply the algorithm accessing liquidity.
4. **Identify the Premium/Discount Array:** After the sweep, watch for immediate displacement the other way.
   - **Order Block Entries:** If entering short on a Bearish Order Block (the last up-close candle before the drop), aim for a fill at the **opening price** of that candle. Your stop loss should be placed at the **Mean Threshold** (the exact midpoint) of that candle's body.
   - **Fair Value Gap (FVG) Entries:** If entering short on a Fair Value Gap, use the lowest threshold (the very bottom of the gap) for your entry limit order to guarantee a fill. 
5. **The Signature of a Valid Premium FVG:** When price returns to a bearish FVG, the upper half of that gap should remain untouched. The wicks may tag the bottom half, but respecting the top half signals immediate algorithmic displacement is imminent.

## Risk Management & Trading Psychology
- **Taking Partials:** Taking partial profits and moving the stop to break even is paramount. It removes emotional tension and makes the remainder of the trade "free."
- **Handling Mistakes:** If you enter a trade erroneously (e.g., a misclick, a fat-finger, or an environmental distraction), close the trade immediately. Do not try to hold it and hope it becomes a winner to save face.
- **Stop Loss Acceptance:** A stop loss should be placed exactly at the point where the trade idea is technically invalidated. If you are stopped out, accept it. Do not attempt to revenge trade or fix the problem on a Monday ahead of big news. Close the charts and walk away.
