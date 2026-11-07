# GAPS — Understanding Round v3, Session `u3-k3`

Everything documented here is an explicit corpus or visual-context gap, conflict kept parallel, or unrecovered threshold from the 345 windows (`W0001..W0345`) read in session `u3-k3`. Nothing below is filled from memory or external trading lore.

## 1. Deixis: "this high", "that low", "in here" without a named price in the transcript

Because the speaker narrates over live or recorded TradingView / Barchart screens, specific candles and swing points are often pointed to with the cursor rather than spoken by price or timestamp:

| claim | concept | verbatim quote | what is missing without the video frame |
|---|---|---|---|
| `U3K3-035` | `directional_bias` | `"when price goes below the low in mid-september and rejects..."` | the exact mid-September candle date and price level on the daily chart |
| `U3K3-042` | `higher_time_frame` | `"you have to use the swing high that starts from here down to that low"` | the specific higher-timeframe swing high and low anchors on screen |
| `U3K3-061` | `inversion_fair_value_gap` | `"look at the bodies of these candles here nothing goes above..."` | which sibling candles inside the inversion FVG are being compared |
| `U3K3-173` | `opening_price` | `"with this short-term High it breaks above it so there's a shift in Market structure there"` | the exact intraday candle timestamp of the short-term high break |
| `U3K3-190` | `premium` | `"It's Already Done three stages a low that went below here this one over here"` | the three visual downward stage lows pointed to on the E-mini S&P chart |
| `U3K3-207` | `rejection_block` | `"so you use like the rejection block here which is this price that closing price right there"` | which specific candle body close in the cluster around 4112.50 was selected |
| `U3K3-218` | `run_on_stops` | `"do we view it as a run on stops that rejects and goes back above here"` | the exact breaker boundary price on the intraday chart |

## 2. Parallel Definitions & Conflicts Kept Separate (Never Merged or Averaged)

In accordance with session rules, wherever the speaker uses multiple boundaries, definitions, or operational rules across different eras or asset classes, all positions are preserved in parallel in the `VARIANTS` and `OBSERVABLES` sections:

1. **`asian_range` time window**:
   - `U3K3-010` (`W0010`): `"from 7:00 in the evening till midnight New York time"` (`19:00–00:00` NY).
   - `U3K3-012` (`W0014`): `"whether you use an eight o'clock to midnight..."` (`20:00–00:00` NY, also extending to `02:00` NY in earlier FX tutorials).
   - Kept parallel as a parameterized session start (`19:00` or `20:00` America/New_York to `00:00` America/New_York).
2. **`consequent_encroachment` vs `mean_threshold`**:
   - `U3K3-014` (`W0019`): explicitly distinguishes `"mean threshold"` (50% of a candle body / order block) from `"consequent encroachment"` (50% of a gap or wick).
   - `U3K3-025` (`W0021`): uses `"consequent encroachment"` loosely in live narration to refer to the midpoint of a bullish order block (`"didn't even get to consequent encroachment of the bullish order block"`). Both usages are preserved.
3. **`inefficiency` vs `liquidity_void`**:
   - `U3K3-094` (`W0112`, 2016): defines `"liquidity void"` as a multi-candle momentum run requiring multiple passes to fill, contrasted with a single-candle fair value gap.
   - `U3K3-059` (`W0075`, 2022): states `"when you see a fair value gap what you're seeing is what I taught years ago as a liquidity void"` while preferring the directional labels `"bisi"` and `"sibi"`.
4. **`opening_price` and `midnight` anchors**:
   - Daily intraday open: `00:00` America/New_York midnight candle open (`U3K3-118`, `U3K3-168`), with fallback to `08:30` NY when a strong trend fails to retrace across the midnight open (`U3K3-127`), or `09:30` NY for equity indices (`U3K3-172`).
   - Weekly open: tracks both Sunday's natural opening price and Monday's `00:00` NY midnight opening price in parallel (`U3K3-128`, `U3K3-174`).
   - Candle-structure open: also uses `"opening price"` to mean the open of the down-close or up-close order-block candle extended horizontally (`U3K3-172`, `W0221`, `W0223`).
5. **`premium` and `money_management` dual senses**:
   - `premium`: dealing-range valuation above the 50% equilibrium (`U3K3-189`) vs futures term-structure backwardation where the front month trades above the deferred month (`U3K3-197`).
   - `money_management`: trader equity/risk-percentage sizing (`U3K3-131`, `U3K3-133`) vs institutional capital rotation across the 5Y/10Y/30Y Treasury yield triad (`U3K3-140`).
6. **`non_farm_payroll` execution stance**:
   - Standard rule (`U3K3-143`, `W0184`, `W0185`): NFP and FOMC days are `"no setup"` days; students stop trading after Wednesday's NY session of NFP week.
   - Parallel exceptions (`U3K3-146`, `U3K3-152`, `W0181`, `W0182`): late-Friday position entry after an NFP Judas swing confirmed by SMT and seasonal tendency, or live ultra-short-term demonstration scalps.
7. **`short_term_high` body vs wick measurement**:
   - Measured at candle bodies (where the bulk of the volume resides) when anchoring Fibonacci OTE ranges (`U3K3-224`, `U3K3-230`), but measured at the wick extreme for buy-stop sweeps, market structure breaks, and protective stop-loss placement (`U3K3-221`, `U3K3-225`).

## 3. Literal-Phrase Scarcity (`THIN` Flags on Exact Unhyphenated String)

Two of the 23 concepts have fewer than 15 occurrences of the literal unhyphenated singular string in `kept_concepts.tsv` across the 490 transcripts, due to ASR hyphenation and pluralization:

- `non_farm_payroll`: literal `"non farm payroll"` occurs **1 time in 1 file** (`W0181`), whereas `"non-farm payroll"` / `"nonfarm payroll"` occur **145 times across 52 files**. Marked `thin: true` on the literal unhyphenated string, and supplemented with 14 era-stratified windows (`W0182..W0195`) of the hyphenated/compound spellings so all 15 windows are read and verified.
- `long_term_high`: literal `"long term high"` occurs **10 times in 8 files** (`W0121..W0128`), whereas `"long-term high"` / `"long term highs"` / `"long-term highs"` occur **25 times across 14 files**. Marked `thin: true` on the literal unhyphenated singular string, and supplemented with 7 era-stratified windows (`W0129..W0135`) across 7 additional files to reach 15 distinct transcripts.

## 4. Cumulative Coverage Status Across `u2` + `u3-k1` + `u3-k3`

With the completion of the 23 concept cards in `u3-k3`, **all 66 concepts in `kept_concepts.tsv` are now 100% covered** by full, `>=15`-window verified concept cards across `u2` (21 cards), `u3-k1` (23 cards), and `u3-k3` (23 cards, including dedicated standalone cards for both `premium` and the 6 other concepts that K1/K2's 45-vs-46 index shift previously missed).
