---
type: Playbook
title: Daily Bias Determination Workflow
description: Top-down pre-session routine — HTF draw on liquidity, weekly profile, PD arrays, and news awareness — used to fix the day's directional premise before any entry.
tags: [playbook, bias, top-down, pd-arrays]
generated: { by: ox-alpha/opencode, at: 2026-08-25T10:57:21Z }
---

# Prerequisites

- [Liquidity](/concepts/liquidity.md)
- [Premium, Discount & the PD Array Matrix](/concepts/premium-discount.md)
- [Power of Three](/concepts/power-of-three.md)
- [Killzones and Time](/concepts/killzones-and-time.md)

# Steps

1. Start on the highest timeframe (weekly → daily): locate the current **draw on liquidity** — the untapped pool the algorithm is presumably delivering toward (old high, old low, imbalance).
2. Assess the **weekly profile**: where is price within the weekly Power of Three (accumulation/manipulation/distribution)? Is this week expanding off a manipulation or distributing into a pool?
3. Map the daily dealing range: mark equilibrium, then list PD arrays above and below current price — untested order blocks, FVGs, breakers — ranked per the matrix heuristic.
4. Ask which side must be purged first: bias is the direction price should travel *after* taking the nearer opposing pool.
5. Check the economic calendar: red-folder news (CPI, FOMC, NFP) can replace technical delivery; avoid bias conviction straddling major releases.
6. Write the premise: expected manipulation leg, expected expansion leg, key invalidation level. Only then hunt intraday setups aligned to it.

# Invalidation

A daily close through the presumed draw-side pool, a higher-TF structure shift against the premise, or an unscheduled news shock re-pricing the range — re-run the workflow rather than forcing yesterday's bias.

# Sources

- [2022 Mentorship](/sources/mentorship-2022.md)
- [2024 Mentorship](/sources/mentorship-2024.md)
- [2025 Lecture Series](/sources/lecture-series-2025.md)
