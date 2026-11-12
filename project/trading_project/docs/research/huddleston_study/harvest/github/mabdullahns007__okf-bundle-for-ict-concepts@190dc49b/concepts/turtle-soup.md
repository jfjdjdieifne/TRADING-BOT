---
type: Concept
title: Turtle Soup
description: ICT's false-breakout fade setup — entering against a raid of a prior session high or low once liquidity is swept and price rejects back into range.
tags: [concept, turtle-soup, liquidity, entries]
generated: { by: ox-alpha/opencode, at: 2026-08-25T10:57:21Z }
---

# Definition

Turtle soup is ICT's adaptation of the classic Linda Raschke counter-turtle fade: when price takes out an obvious prior high or low (old range high, Asian range low, ORG extreme), stop-hunting orders fill, and if the move fails to extend, price reverses — allowing a trade in the opposite direction of the breakout (see [/concepts/liquidity.md]).

# Mechanics

1. Mark a clean prior session high/low or opening-range extreme that everyone can see.
2. Wait for a raid — price trades through it, grabbing stops ([/concepts/killzones-and-time.md] windows make raids more reliable).
3. Confirm rejection: swift return back inside the range, often leaving an FVG or displacement leg ([/concepts/fair-value-gap.md], [/concepts/market-structure.md]).
4. Enter against the sweep with a stop beyond the raid extreme; target the opposite side of the range or external liquidity.

# Application

Classic teaching (2017 Mentorship Month 08, [Forex Market Maker Primer](/sources/forex-market-maker-primer.md)) applied it to London raids of the Asian range. Modern usage ([2025 Lecture Series](/sources/lecture-series-2025.md)) emphasizes premarket buyside turtle soup on NQ and NY lunch-macro variants, including deferred entry with rejection confirmation.

# Evolution

From a generic false-breakout fade, turtle soup evolved into a time-conditioned model nested inside macros and Power of Three manipulation legs ([/concepts/power-of-three.md]).

# Related

- [/concepts/opening-range-gaps.md](/concepts/opening-range-gaps.md)
- [/concepts/killzones-and-time.md](/concepts/killzones-and-time.md)
- [/concepts/order-blocks.md](/concepts/order-blocks.md)
- [/concepts/premium-discount.md](/concepts/premium-discount.md)
