---
type: Concept
title: Order Blocks
description: ICT's family of institutional footprints — the last opposing candle before displacement — extended across breaker, mitigation, rejection, propulsion, and suspension block variants.
tags: [concept, order-blocks, entry]
generated: { by: ox-alpha/opencode, at: 2026-08-25T10:57:21Z }
---

# Definition
An **order block** is the final down-close candle before an upward displacement (bullish) or up-close candle before downward displacement (bearish), treated as the footprint of institutional buying or selling. Validation requires a later candle trading *through* the defining candle's extreme; entries are taken on the return to the block, with stops below its low or its 50% ([/sources/2016-mentorship-month-04.md]). The taxonomy grew around it:

- **Breaker block** — an order block that failed as price ran the liquidity beyond it; after the run it flips polarity and acts as oppositional support/resistance.
- **Mitigation block** — similar flip without the liquidity sweep; price returns to unfilled institutional interest before continuing.
- **Rejection block** — formed from a wick-heavy rejection; traded off the wick's origin.
- **Propulsion block** — a small refresher block inside a leg that "propels" continuation.
- **Suspension block** — later-era term for blocks suspending a move at extremes (used sparingly in 2025–2026 lectures).

# Mechanics
Blocks derive their meaning from displacement: a candle only matters if what follows breaks structure and leaves imbalance ([/concepts/fair-value-gap.md]). Location filters quality — bullish blocks in discount of a dealing range are tradeable; the same block in premium is ignored ([/concepts/premium-discount.md]). Purge-then-flip logic ties breakers directly to liquidity runs ([/concepts/liquidity.md]).

# Application
Traders use order blocks/breakers as precise entry arrays with tight, structurally-defined risk ([/concepts/risk-management.md]), often stacked with an overlapping FVG for confluence, timed to killzones ([/concepts/killzones-and-time.md]). The 2024 mentorship explicitly teaches how ICT selects among candidate blocks rather than taking every one ([/sources/mentorship-2024.md]).

# Evolution
The full taxonomy was catalogued in 2016 Month 4 (including now-rare vacuum blocks). Through 2022–2023 order blocks were de-emphasized relative to FVGs; the 2025–2026 era resurrects them inside the PD array matrix with stricter selection rules ([/sources/lecture-series-2025.md], [/sources/smart-money-lectures-2026.md]). Terminology drifted: some block types were taught once and quietly retired — treat the taxonomy as historical, not fixed.

# Related
- [/concepts/fair-value-gap.md](fair-value-gap.md)
- [/concepts/market-structure.md](market-structure.md)
- [/concepts/optimal-trade-entry.md](optimal-trade-entry.md)
- [/sources/2016-mentorship-month-04.md](/sources/2016-mentorship-month-04.md)
