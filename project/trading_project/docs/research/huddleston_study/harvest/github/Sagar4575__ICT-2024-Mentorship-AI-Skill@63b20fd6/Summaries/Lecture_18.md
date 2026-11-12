# ICT 2024 Mentorship - Lecture 18: Unveiling the Algorithmic Tapestry

## 1. The Opening Range and its Significance

### The Opening Range Gap & Midpoint
*   **Definition:** The Opening Range Gap is the void between the 9:30 AM Eastern Time opening price and the previous day's settlement price (typically marked at 4:14 PM or 5:00 PM for index futures).
*   **The 70% Rule:** There is a 70% probability that between 9:30 AM and 10:00 AM, the market will trade back to the precise midpoint (Consequent Encroachment) of this Opening Range Gap.
*   **Application:** This serves as a highly reliable, high-probability initial draw on liquidity, regardless of your overall daily bias. 

### The First FVG of the Day
*   **Identification:** Pay absolute attention to the very first Fair Value Gap (FVG) that forms after 9:30 AM (specifically between 9:31 AM and 10:00 AM).
*   **Significance:** This initial FVG acts as a foundational anchor for the algorithm throughout the rest of the day. Extend its High, Low, and Midpoint in perpetuity across your chart. Price will continually reference it to build momentum or accumulate positions.

---

## 2. Advanced PD Array Mechanics

### Inversion FVGs vs. Reclaimed FVGs
*   **Inversion:** When price slices completely through an existing FVG (e.g., a bullish FVG) and closes below it, that zone inverts to become resistance (a bearish Inversion FVG).
*   **Reclaimed:** If price then stages a strong displacement back *above* that Inversion FVG, and subsequently trades down into it, it reverts to its original character. It becomes a **Reclaimed** Bullish FVG and should act as strong support.

### The "Mohawk"
*   **Definition:** A Mohawk occurs when a wick pierces just one or two ticks outside the strict boundaries of a PD array (such as going slightly above a bearish FVG or slightly below an order block) but the candle body closes cleanly inside the array.
*   **Implication:** This is simply the algorithm "coloring outside the lines" to do damage (hunting tight stops) without breaking the true structural integrity of the level. It does not invalidate the setup.

### The Propulsion Block
*   **Definition:** An order block that forms *inside* an existing inefficiency (like an FVG).
*   **Validation Rule:** The very next candle's body cannot close past the halfway point (Mean Threshold) of the propulsion block. This confirms its strength to vigorously repel price.

---

## 3. Liquidity Pools & Market Delivery

### 3-Day Lookback for Liquidity
*   **Rule:** Always mark the highest high and lowest low of the last **three trading days** (ignore Sundays). 
*   **Significance:** These levels are absolute magnets for price. When the market is dropping heavy, it is not "running out of sellers"—it is speeding up to tap the massive pool of sell stops resting below these significant multi-day lows. Smart money buys these sell stops to accumulate their longs.

### The "Black Hole" Effect (Nested Gaps)
*   **Concept:** When you have a New Day Opening Gap (NDOG) overlapping closely with a New Week Opening Gap (NWOG), it creates an algorithmic "black hole." 
*   **Action:** Price will be continually drawn back into this cluster. Keep these gaps on your charts up to 20-40 trading days back, as they remain highly active reference points.

---

## 4. Psychology & Journaling

### Programming the Subconscious
*   **Journaling as "Pillow Talk":** Your journal is not just a ledger; it is a tool to program your Reticular Activating System. Do not log negative rants or beat yourself up over mistakes.
*   **Positive Reinforcement:** When backtesting, find perfect setups and write detailed, positive annotations ("I'm excited to see how perfectly price respected this level"). By repeatedly flooding your subconscious with positive reinforcement of the model, you train your brain to naturally spot these setups in live conditions without fear.
*   **The Hunting Analogy:** When backtesting, you are a hunter looking *only* for the deer track. Ignore all other noise and variations. Focus strictly on mastering one footprint.
