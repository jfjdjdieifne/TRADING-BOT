---
type: Concept
title: Premium, Discount & the PD Array Matrix
description: ICT's dealing-range framework that grades every price level as premium or discount around equilibrium, organized in later years into a ranked matrix of algorithmic price-delivery arrays.
tags: [concept, premium-discount, core]
generated: { by: ox-alpha/opencode, at: 2026-08-25T10:57:21Z }
---

# Definition
A **dealing range** is the significant high-to-low span within which price is currently delivering. Its 50% level is **equilibrium**; the upper half is **premium** (expensive — where shorts belong), the lower half is **discount** (cheap — where longs belong). "PD arrays" are the ordered family of price levels ICT stacks on that range — old highs/lows, fair value gaps, order blocks, breakers, and specific ratios — and the **PD array matrix**, formalized in the 2025 lecture series, is his map of which array the algorithm should engage next when trading toward its draw ([/sources/lecture-series-2025.md]).

# Mechanics
The dealing range is anchored at swing points established by structure breaks ([/concepts/market-structure.md]); liquidity pools sit at its extremes ([/concepts/liquidity.md]). Price is said to seek one side's draw, purge it, then reprice to the opposite array. Optimal price levels follow directly: longs only below equilibrium (ideally at OTE ratios or an FVG inside discount), shorts only above equilibrium ([/concepts/optimal-trade-entry.md], [/concepts/fair-value-gap.md]). Arrays nearer the current price with untested status rank higher in the matrix.

# Application
Daily workflow: define HTF dealing range → locate equilibrium → accept only setups whose entry array sits in the correct half relative to bias → target the opposing extreme/pool. This single filter kills most counter-trend mistakes and underpins position sizing discipline ([/concepts/risk-management.md]). The 2022 mentorship drills premium/discount framing on live ES/NQ throughout ([/sources/mentorship-2022.md]).

# Evolution
Premium/discount language appears in the 2016–2017 private mentorships but matured publicly through the 2022–2023 series. In 2025 ICT unveiled the PD Array Matrix explicitly, including selecting arrays at all-time highs where no traditional range exists ([/sources/lecture-series-2025.md]); 2026 refines it further ("shadows validating PD arrays," trading ATH in the matrix) ([/sources/smart-money-lectures-2026.md]). Note honestly: the matrix's exact ranking has shifted between lectures — it is a heuristic, not a fixed table.

# Related
- [/concepts/liquidity.md](liquidity.md)
- [/concepts/fair-value-gap.md](fair-value-gap.md)
- [/concepts/order-blocks.md](order-blocks.md)
- [/concepts/opening-range-gaps.md](opening-range-gaps.md)
