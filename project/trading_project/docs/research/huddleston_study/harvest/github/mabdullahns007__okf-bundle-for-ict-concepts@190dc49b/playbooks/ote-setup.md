---
type: Playbook
title: Optimal Trade Entry (OTE) Setup
description: Step-by-step workflow for entering a trending delivery at the 62-79% retracement of the impulse leg, refined with a lower-timeframe PD array.
tags: [playbook, ote, fibonacci, entries]
generated: { by: ox-alpha/opencode, at: 2026-08-25T10:57:21Z }
---

# Prerequisites

- [Optimal Trade Entry](/concepts/optimal-trade-entry.md)
- [Market Structure](/concepts/market-structure.md)
- [Premium, Discount & the PD Array Matrix](/concepts/premium-discount.md)
- [Killzones and Time](/concepts/killzones-and-time.md)
- [Fair Value Gap](/concepts/fair-value-gap.md)

# Steps

1. Establish HTF bias: identify the draw on liquidity and the direction of HTF delivery ([/concepts/liquidity.md]).
2. Define the dealing range created by the most recent market structure shift — that impulse leg is what you measure.
3. Wait for a killzone or macro window before engaging; OTE entries outside timed windows are lower quality.
4. Draw the fib retracement on the impulse leg; the entry zone is 62%–79%, with 70.5% as the sweet spot.
5. Refine the entry with a lower-TF array inside the zone: FVG, order block, or breaker forming on 1–5 minute charts.
6. Enter on displacement out of the array in the bias direction.
7. Stop goes beyond the impulse extreme / sweep low or high.
8. Targets: first the internal liquidity pool ahead, then external liquidity at the opposing range extreme.

# Invalidation

Price closes through the full 79% level and beyond the impulse origin; structure shifts against the bias before the zone is tapped; or the killzone expires without an entry trigger.

# Sources

- [OTE Pattern Recognition Series](/sources/ote-pattern-recognition-series.md)
- [Forex Market Maker Primer](/sources/forex-market-maker-primer.md)
- [2022 Mentorship](/sources/mentorship-2022.md)
- [2024 Mentorship](/sources/mentorship-2024.md)
