---
type: Concept
title: Opening Range Gaps
description: ICT's framework of opening prices and gaps — midnight opening range, RTH opening range, NWOG/NYOG/NDOG — used as daily reference architecture and rebalance magnets.
tags: [concept, opening-range, gaps, time]
generated: { by: ox-alpha/opencode, at: 2026-08-25T10:57:21Z }
---

# Definition

A family of daily reference levels derived from session opens: the **midnight opening range** (price action around 12:00 AM NY), the **RTH opening range / ORG** (first minutes after the 9:30 cash open), and opening **gaps** — NWOG/NYOG (new week/year opening gaps) and NDOG (new day opening gap).

# Mechanics

- **Midnight open** divides the trading day; price above/below it informs bias, and the midnight-to-8:30 consolidation frames the NY manipulation-expansion sequence ([/concepts/power-of-three.md]).
- **ORG**: the high/low of the first presented candles after 9:30 acts as intraday support/resistance; raids of it often precede expansion.
- **NWOG**: the unfilled gap between Friday's close and Sunday's open is treated as a standing imbalance the algorithm periodically returns to rebalance.
- **1st Presented FVG logic**: in the [2025 Lecture Series](/sources/lecture-series-2025.md) ICT teaches that the first fair value gap presented at or near the open is the algorithm's preferred rebalancing zone — with explicit rules for disqualifying it ([/concepts/fair-value-gap.md]).

# Application

Used to anchor daily bias, select PD arrays for macro-window entries ([/concepts/killzones-and-time.md]), and locate turtle-soup raids of the ORG extremes ([/concepts/turtle-soup.md]). Gaps act as draw-on-liquidity targets alongside classical liquidity pools ([/concepts/liquidity.md]).

# Evolution

Opening-range theory was a minor thread in early mentorships but became a central 2025–2026 doctrine — dedicated midnight opening range lectures, the PD Array Matrix framing, and heavy emphasis on NWOG/NDOG across the 2025 Lecture Series and [Smart Money Lectures 2026](/sources/smart-money-lectures-2026.md).

# Related

- [/concepts/killzones-and-time.md](/concepts/killzones-and-time.md)
- [/concepts/fair-value-gap.md](/concepts/fair-value-gap.md)
- [/concepts/power-of-three.md](/concepts/power-of-three.md)
- [/sources/lecture-series-2025.md](/sources/lecture-series-2025.md)
