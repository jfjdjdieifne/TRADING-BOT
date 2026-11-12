---
type: Concept
title: Fair Value Gap (FVG)
description: A three-candle inefficiency in price delivery where a gap between the first candle's wick and the third candle's wick marks an imbalance the algorithm is said to rebalance, serving as ICT's primary entry array.
tags: [concept, fvg, entry]
generated: { by: ox-alpha/opencode, at: 2026-08-25T10:57:21Z }
---

# Definition
A fair value gap (also "inefficiency" or "imbalance") forms when price displaces so quickly that candle 1's high and candle 3's low (in an up-move; mirrored in a down-move) do not overlap, leaving an unfilled price range. ICT holds that efficient markets revisit such gaps — "price seeks efficiency" — making the FVG a magnet and a reaction zone. A **volume imbalance** is the weaker variant: bodies gap but wicks overlap. An **inverse FVG** is a gap that has been traded through and flipped to act in the opposite direction. The **first-presented FVG (1st presented)** is the 2025+ refinement: of all gaps in a displacement leg, the first one presented on the retrace is the algorithm's preferred rebalance zone.

# Mechanics
FVGs appear after displacement — typically through a liquidity purge or structure break ([/concepts/liquidity.md], [/concepts/market-structure.md]). On the retracement, price returns into the gap (often to its mean threshold / consequent encroachment, the 50%) and reacts. Validity depends on context: inside a premium/discount array ([/concepts/premium-discount.md]), during a killzone ([/concepts/killzones-and-time.md]), and not already violated.

# Application
Standard entry: bias → manipulation → displacement leaving an FVG → limit order at the FVG's edge or CE, stop beyond the swing, targets at opposing liquidity ([/concepts/risk-management.md]). FVGs also serve as targets when price must fill older imbalances. Selection matters more than existence — the 2024 mentorship devotes multiple lectures to why most FVGs fail and how ICT picks winning ones ([/sources/mentorship-2024.md]).

# Evolution
Introduced with liquidity voids/pools in the 2016 mentorship Month 4 ([/sources/2016-mentorship-month-04.md]); central but loosely defined through 2022–2023 ([/sources/mentorship-2022.md], [/sources/mentorship-2023.md]). The 2025 lecture series systematized first-presented logic, disqualification rules, and the PD-array ranking of gaps ([/sources/lecture-series-2025.md]); 2026 adds Enigma/Reaper FVG projections and protractions ([/sources/smart-money-lectures-2026.md]).

# Related
- [/concepts/order-blocks.md](order-blocks.md)
- [/concepts/premium-discount.md](premium-discount.md)
- [/concepts/optimal-trade-entry.md](optimal-trade-entry.md)
- [/playbooks/silver-bullet-setup.md](/playbooks/silver-bullet-setup.md)
