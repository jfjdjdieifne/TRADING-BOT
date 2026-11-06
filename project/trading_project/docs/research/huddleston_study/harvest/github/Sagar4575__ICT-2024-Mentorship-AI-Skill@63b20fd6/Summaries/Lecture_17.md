# ICT 2024 Mentorship - Lecture 17: Impeding Barriers

## 1. Core Technical Concepts

### Impeding Barriers & Small/Anemic Gaps
*   **Definition:** An "impeding barrier" is a market condition that makes trading problematic and lacks clear momentum.
*   **Small Gaps:** A primary example is a "small" or "anemic" gap, where the market opens very close to the previous day's settlement (less than 30-40 handles away in NQ/ES).
*   **Implications:** When this occurs, it indicates a lack of excitement, urgency, or algorithmic displacement at the open.
*   **Actionable Protocol:** In these conditions, do not look for immediate entries. Instead, sit out the entire 30-minute opening range (9:30 AM to 10:00 AM) to allow the market to establish a clearer narrative before engaging.

### The Immediate Rebalance (Reinforced)
*   **Definition:** When a large displacement candle (e.g., a strong down candle) is followed by a very next candle that immediately trades all the way back to the low/high of that previous candle, completely filling the implied imbalance.
*   **Significance:** This is a highly reliable signature of algorithmic speed and directional certainty. It acts as a major tell that price is locked onto a specific direction and is moving with purpose. If the rebalance does not occur on the immediate next candle (or occasionally the second), the signature is invalidated.

### Inversion Fair Value Gaps (In-Depth Execution)
*   **Validation:** A 15-minute FVG becomes an Inversion FVG only after the bodies of the candles completely violate it and close outside of it, proving the original FVG has failed.
*   **Rules of Engagement:** 
    *   Once inverted (e.g., a Bullish FVG turns into a Bearish Inversion FVG), the market should respect the *lower half* of the inversion area.
    *   Price should not trade back above the midpoint (Consequent Encroachment) of the inversion gap.
    *   **Entry Trigger:** Once price respects the inversion FVG, drop to a lower timeframe (e.g., 1-minute or even 15-second) and look for the *very next* FVG that forms as price displaces away from the inversion level. Use that lower timeframe FVG for entry.

---

## 2. Market Psychology & Risk Management

### Trading Without a Stop Loss is Idiotic
*   **The Reality of Stops:** Placing a stop loss forces a trader to define exactly where their trade idea is wrong. Many traders refuse to use stops because of ego—they do not want to admit they are wrong.
*   **Risk Principle:** Trading without a stop loss is mathematically reckless and proves a complete lack of risk management. A losing trade with a respected stop loss is not a failure; it is paying "tuition" for experience.

### Impulse Control, FOMO, and EGO
*   **Impatience:** The natural urge to "push buttons" and force trades when the model is not present is the number one destroyer of accounts. Sitting still and not losing money is a *win*.
*   **The "Superman" Complex:** ICT notes a stark difference in how men and women approach trading. Men often struggle with the need to be "superheroes," battling the market to prove their worth, show off on social media, or feed their egos (leading to over-leveraging and blowing accounts). Women, generally, are more process-oriented, follow rules strictly, lack the toxic ego to show off, and are thus consistently better and more profitable traders.
*   **Overtrading:** Taking trades outside of your model generates massive commission costs. Even if you eke out a gross profit, overtrading will cause your net profit to be eaten alive by fees. Less is always more. Wait for the highest probability setups.
