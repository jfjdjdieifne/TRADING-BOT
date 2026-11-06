# ICT 2024 Mentorship - Lecture 11 Summary
**Date:** August 19, 2024 (Begins 9:15 AM ET)

## 1. Environmental Context: Jackson Hole Symposium Week
*   **Market Behavior:** The week of the Jackson Hole Symposium is characterized by highly overlapping, back-and-forth price action. The market routinely redelivers and deeply retraces price runs that would normally not retrace in a standard week.
*   **Trading Protocol:** "Seek and destroy" conditions prevail. You must aggressively take partials (early profits) when price clears short-term highs or short-term lows. If you attempt to hold for large, one-directional moves without scaling out, the market will retrace and stop you out. 
*   **FOMC Distinction:** FOMC minutes are not the same as an FOMC rate announcement. During rate announcements, the initial algorithmic spool up into 2:00 PM EST is usually a fake out. At 2:30 PM (when the conference starts), the algorithm typically initiates the true run, which moves aggressively in the opposite direction of the 2:00 PM move.

## 2. Institutional Order Flow Entry Drill (IOED)
*   **Definition:** A high-precision entry technique utilizing a Fair Value Gap (FVG) where price only barely touches the absolute extremity of the gap before immediately reacting. 
*   **Execution:** For a bullish IOED, place a buy limit order exactly one tick below the high of the candle that forms the upper bound of the FVG. 
*   **The Logic:** An IOED entry ideally leaves the majority of the Fair Value Gap *open*. A gap that is left partially unfilled acts as a strong "propellant" or structural support/resistance for the unfolding price run. If the gap closes entirely, the setup is less favorable, though the trade is not necessarily invalidated unless the stop loss is hit.
*   **Stop Placement:** In choppy conditions, do not place your stop loss tightly under the FVG itself. Identify the lowest structural wick that initiated the price leg and place the stop just below that.

## 3. Session Liquidity and The "Power of 3" (AMD)
*   **Dynamic Liquidity:** Session liquidity is dynamic—it exists above (buy side) and below (sell side). You must learn to read the session liquidity draw before attempting to predict a higher timeframe daily bias.
*   **The Judas Swing (Trap):** The algorithm typically targets the wrong side of the marketplace first to trick retail traders. For example, if the daily bias is bullish, the market will open at 9:30 AM, drop to sweep sell-side liquidity (the Judas Swing), and then reverse to draw towards the true buy-side targets.
*   **The "Sweet Spot" for Entry:** In a bullish profile, the ideal "sweet spot" to buy is within the price range between the 9:30 AM open price and the low of the Judas Swing. You do not need to catch the absolute low tick.

## 4. Consequent Encroachment and Price Delivery Continuum
*   **Consequent Encroachment (Midpoint):** Wicks act as gaps. The midpoint of a wick (or an actual gap) is its Consequent Encroachment. If price retraces toward a key support wick but fails to even touch its Consequent Encroachment, this indicates extreme underlying strength.
*   **Price Delivery Continuum:** The algorithm cycles up and down through timeframes continuously. To utilize sub-minute charts (15-second, 30-second), you must anchor your bias to a higher timeframe. The 1-minute chart serves as the higher-timeframe anchor for a 15-second execution.
*   **Sub-Minute Market Structure:** A shift in market structure on a 15-second chart is valid if it aligns with a FVG or IOED occurring simultaneously on the 1-minute chart.

## 5. Balanced Price Ranges and Structural Failure
*   **Balanced Price Range:** Created when price aggressively drops through a specific range (a single large down-close candle) and then shortly thereafter aggressively rallies back through the exact same range. It signifies that both buy-side and sell-side liquidity have been efficiently offered.
*   **Behavior:** A true balanced price range acts like a "brick wall." Price should not violate the extreme boundary of that range once it is established. 
*   **Failure/Intervention:** If price easily cuts through an established balanced price range, it strongly suggests manual intervention in the algorithms or a significant paradigm shift. The trade logic is invalidated.

## 6. The Reaper Fair Value Gap
*   **Definition:** A specific, highly influential Fair Value Gap that the algorithm utilizes repeatedly over long durations (e.g., weeks or an entire month). It acts like a "scythe," slicing through price action and serving as a continuous reference point.
*   **Identification:** Look for the very first pertinent Fair Value Gap that forms on a structurally significant date. For example:
    *   The first FVG that forms after 9:30 AM on a Monday (first day of the trading week).
    *   The first FVG that forms on the first trading day of a new month. 
*   Extend this Reaper FVG forward in time across your charts; the algorithm will return to it repeatedly as a high-probability turning point.

## 7. Exit Strategy Logic
*   **Low Threshold Objectives:** Rather than always holding out for the absolute extreme of a draw on liquidity (e.g., the exact high or the exact midpoint of a large weekly gap), target the nearest logical threshold. For instance, the *lower quadrant* of a New Week Opening Gap is an easier and safer exit objective than its midpoint.
