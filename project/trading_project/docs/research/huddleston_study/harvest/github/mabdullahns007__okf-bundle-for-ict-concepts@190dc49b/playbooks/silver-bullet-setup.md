---
type: Playbook
title: Silver Bullet Setup
description: Time-based model entering on the first fair value gap formed after a liquidity run inside a one-hour window (10-11 AM ET primary; London 3-4 AM, NY PM 2-3 PM).
tags: [playbook, silver-bullet, fair-value-gap, time-based]
generated: { by: ox-alpha/opencode, at: 2026-08-25T10:57:21Z }
---

# Prerequisites

- [Killzones and Time](/concepts/killzones-and-time.md)
- [Fair Value Gap](/concepts/fair-value-gap.md)
- [Liquidity](/concepts/liquidity.md)
- [Market Structure](/concepts/market-structure.md)

# Steps

1. Choose the window: 10:00–11:00 AM ET (primary), London 3:00–4:00 AM ET, or NY PM 2:00–3:00 PM ET. Trade at most one per day.
2. Establish directional premise from the daily bias and the morning's manipulation: which pool was just raided, which pool is the draw?
3. At the window open, watch for a liquidity run — a sweep of a nearby session high/low or equal highs/lows early in the hour.
4. Identify the **first FVG** created after that run on the 1–5 minute charts, in the direction opposite the raid (toward the draw).
5. Enter on the retracement into that FVG; some variants wait for a market structure shift inside the window first for confirmation.
6. Stop beyond the FVG's origin swing / the sweep extreme.
7. Targets: nearest internal liquidity pool first; external liquidity / opposing session extreme as the extended objective.

# Invalidation

No liquidity run before mid-window; no qualifying FVG forms in the direction of bias; price closes through the entry FVG against you; or the hour expires — Silver Bullet is strictly time-boxed, so an untriggered setup is simply discarded.

# Sources

- [2023 Mentorship](/sources/mentorship-2023.md)
- [2024 Mentorship](/sources/mentorship-2024.md)
- [2025 Lecture Series](/sources/lecture-series-2025.md)
