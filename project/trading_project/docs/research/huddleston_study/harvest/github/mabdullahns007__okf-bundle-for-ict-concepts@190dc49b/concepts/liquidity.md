---
type: Concept
title: Liquidity
description: The pools of resting stop orders (buyside and sellside) that ICT claims smart money engineers price toward, forming the basis of runs, purges, and draw-on-liquidity bias.
tags: [concept, liquidity, core]
generated: { by: ox-alpha/opencode, at: 2026-08-25T10:57:21Z }
---

# Definition
Liquidity in ICT methodology is clusters of pending orders — chiefly retail stop losses — sitting above old highs (buyside liquidity) and below old lows (sellside liquidity). Equal highs/equal lows, trendline liquidity, and session highs/lows are classic "pools." A **liquidity run** (purge, stop hunt) is a push into such a pool that fills institutional orders before reversing. **Draw on liquidity** is the higher-time-frame magnet — the nearest unfilled pool that price is currently "drawn" toward, and the backbone of daily bias.

# Mechanics
Price delivery allegedly seeks liquidity rather than efficiency alone: an up-move that only trades into buyside without displacing is treated as a run for orders, not a breakout. ICT distinguishes **low-resistance liquidity runs** (easy, one-sided moves through thin opposing interest — trending conditions) from **high-resistance liquidity runs** (price grinds against heavy opposing order flow, whipsawing and repeatedly failing — taught as a condition filter extensively in the 2024 mentorship). A purge typically leaves behind displacement, fair value gaps, and structure breaks on the return leg.

# Application
Traders use prior highs/lows, equal highs/lows, and weekly/monthly extremes as targets and as manipulation zones: expect a judas-style run through one side of a range, then trade back toward the opposite pool (see [/concepts/power-of-three.md]). Entries are taken on the retracement after the purge (FVG or order block; [/concepts/fair-value-gap.md], [/concepts/order-blocks.md]), with stops beyond the purge extreme. High-resistance conditions are grounds to stand aside or shrink risk ([/concepts/risk-management.md]).

# Evolution
The 2016–2017 private mentorship built the base vocabulary of pools, voids, and stops ([/sources/2016-mentorship-month-04.md]). The 2022 free mentorship popularized "draw on liquidity" as explicit daily-bias language ([/sources/mentorship-2022.md]). From 2024 onward the emphasis shifted to classifying the *condition* of the run — high vs low resistance — as a veto filter ([/sources/mentorship-2024.md], [/sources/lecture-series-2025.md]).

# Related
- [/concepts/market-structure.md](market-structure.md)
- [/concepts/premium-discount.md](premium-discount.md)
- [/concepts/optimal-trade-entry.md](optimal-trade-entry.md)
- [/concepts/killzones-and-time.md](killzones-and-time.md)
- [/sources/mentorship-2024.md](/sources/mentorship-2024.md)
