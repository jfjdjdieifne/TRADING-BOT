# ICT 2024 Mentorship - Lecture 8 (August 14, 2024)

## Core Technical Concepts & Topics

### 1. The Change in the State of Delivery
- Represents the precise moment the algorithm switches its operating script from buy-side delivery to sell-side delivery (or vice versa).
- **Bearish Order Block Validation:** When price breaks down and closes below the opening price of the highest up-close candle(s) that formed a swing high, the state of delivery flips to sell-side. That exact opening price becomes the key reference level and the true order block.

### 2. Advanced Wick Analysis & Wicks as Targets
- Always measure wicks (swing highs/lows) precisely from the absolute tip to the candle body.
- The **Consequent Encroachment** (midpoint) of a wick is a critical algorithmic level. Treat a wick as if it were a gap.
- If a price retracement fails to reach the consequent encroachment of a wick and immediately reverses, it indicates significant algorithmic weakness in that direction.
- **Wick Projection:** When projecting a target below a major low that terminates in a wick, measure the range of the wick. Project 25% (0.25) of that range below the low to find the next algorithmic liquidity target.

### 3. Balanced Price Ranges Inside FVGs
- If a fair value gap forms, but the prior candle and the following candle's bodies overlap—leaving the gap completely void of wicks—this creates a **Balanced Price Range** inside the inefficiency.
- Price will often flush through this zone quickly to overlap the void, hit the opposing body, and tap out without continuing deeper.

### 4. Inversion Fair Value Gaps
- When the state of delivery flips (e.g., from buy-side to sell-side after hitting a premium objective), the discount PD arrays (like bullish FVGs) formed during the run-up will invert their roles.
- An old bullish fair value gap will become an **Inversion Fair Value Gap** and act as resistance.
- *Rule for Weakness:* When price retraces up into a bearish inversion FVG, it should preferably leave the upper half open. If it completely fills the gap, the sell program is weaker than anticipated.

### 5. Turtle Soup: Reversals vs. Entry Mechanisms
- **Reversal Turtle Soup:** A run on liquidity above an old high or below an old low that results in a sustained change in directional bias.
- **Entry Mechanism Turtle Soup:** Used within an *existing* and *unfolding* price run. 
    - *Example:* Entering short exactly at the high of the first candle forming a bearish fair value gap (an old short-term high). This acts as a Turtle Soup on a lower timeframe.

### 6. The "Mark" at the Table
- A conceptual rule for liquidity: If you do not know who the victim or the "mark" is in the marketplace (i.e., where the engineered liquidity and retail stops are resting), then *you* are the liquidity.

### 7. Trade Execution & Stop Loss Placement
- **Low Threshold Entry:** Instead of demanding an entry deep inside a FVG, enter at the very high of a bullish FVG or the very low of a bearish FVG. Add to the position at the midpoint (Consequent Encroachment).
- **Bearish Order Block Stop Loss:** Standard placement is above the bearish order block's high.
- **Advanced Tight Stop Loss:** If the candle prior to the bearish order block features a large premium wick, you can place your stop loss precisely **two ticks** above the Consequent Encroachment of that wick, rather than above the absolute highest high.

### 8. High-Impact News Intervention
- During the release of major reports (CPI, PPI, FOMC, NFP), the algorithm is manually intervened with and disrupted.
- Price will typically intentionally fall just short of logical objectives, or blow completely past them to wipe out stops.
- *Rule:* Do not trade during the exact release window of these high-impact news drivers.

## Important Definitions
- **Buy-Side Delivery:** The algorithm offering higher prices to seek out premium liquidity or premium inefficiencies.
- **Sell-Side Delivery:** The algorithm offering lower prices to seek out discount liquidity or discount inefficiencies.
- **Consequent Encroachment (Wicks):** The exact midpoint of a candle's wick.
- **Inversion Fair Value Gap:** An old fair value gap that fails as support/resistance and subsequently reverses its role (e.g., old support becomes new resistance).
- **Balanced Price Range:** A gap defined by overlapping candle bodies with an absolute absence of wicks in the void.
- **Turtle Soup:** A false breakout or run on liquidity, serving either as a major macro reversal or an entry mechanism within a sustained trend.
