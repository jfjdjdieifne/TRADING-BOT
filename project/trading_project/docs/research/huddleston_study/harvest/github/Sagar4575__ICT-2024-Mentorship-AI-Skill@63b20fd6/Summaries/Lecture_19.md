# ICT 2024 Mentorship - Lecture 19: Trade Management & Algorithmic Spooling

## 1. Trade Management & Taking Partials

### The Dynamic Trail Partial
When the market has broken heavily into your favor (e.g., dropping below a major daily low) and you want to hold for a massive runner without giving up guaranteed profit:
*   Wait for price to slice through the target liquidity pool and start accelerating.
*   Instead of placing a fixed limit order to take partials right below the old low (which often cuts you out of huge extensions), use a dynamic trail.
*   **The Technique:** Identify each successive down-close candle that creates an imbalance as price drops. Place a Buy Stop (to cover a partial) exactly one tick above the high of that candle. 
*   Continue trailing this Buy Stop down with every new one-minute candlestick high as it spools lower. You will get knocked out of your partial dynamically, often incredibly close to the absolute low of the move, while retaining the rest of your core position.

### Grading Price Swings ("Heaviness")
*   When price is targeting a massive draw on liquidity (like an old daily low), it should act "heavy."
*   **Signatures of Heaviness:** Lower highs on every candle, failure to close the upper half of bearish fair value gaps, and immediate rejection from premium arrays. It shouldn't dally; it should drop quickly.

---

## 2. Market Structure & Retail Traps

### The "Fake Bull Flag"
*   **Setup:** When the algorithm is fundamentally predisposed to go lower, it will often bounce and form relative equal highs on a retracement.
*   **The Trap:** Retail traders see this consolidation and slant it upward, drawing trendlines and calling it a "bull flag breakout."
*   **The Reality:** The algorithm is simply engineering a shallow pool of buy stops above those relative equal highs. It sweeps them quickly, spends virtually no time up there, and then displaces aggressively lower into the true draw on liquidity.

### The Breakaway Gap & The Institutional Order Entry Drill
*   **Breakaway Gap:** An inefficiency created right after a major shift in market structure or as price rips away from a consolidation. It signals extreme momentum. Ideally, a true Breakaway Gap remains unfilled.
*   **Institutional Order Entry Drill:** When price returns to a gap, but only pierces it by one or two ticks before immediately violently rejecting, leaving the maximum amount of the gap's range open. This is a hallmark of algorithmic precision and confirms the Breakaway Gap's validity.

---

## 3. Time-Based Macros & Daily Liquidity

### The 3-Day Lookback
*   The highest high and lowest low of the last **three trading days** (excluding Sundays) are paramount. The algorithm uses time as its primary reference point, and these levels hold massive clusters of institutional stop-loss orders. Price will constantly gravitate to them.

### The 2:50 PM Spooling Macro
*   At exactly 2:50 PM EST, the late afternoon algorithm kicks in. 
*   **The Fishing Analogy:** If the draw on liquidity is obvious (like a resting pool of stops just above/below price), the algorithm acts like a fishing reel spooling line. It will accelerate violently ("spooling") to hit that Terminus directly before the 4:00 PM close.
