---
type: Playbook
title: Turtle Soup Fade Setup
description: Step-by-step workflow for fading a raid of an obvious prior high or low once stops are swept and price rejects back into range.
tags: [playbook, turtle-soup, liquidity, fade]
generated: { by: ox-alpha/opencode, at: 2026-08-25T10:57:21Z }
---

# Prerequisites

- [Turtle Soup](/concepts/turtle-soup.md)
- [Liquidity](/concepts/liquidity.md)
- [Killzones and Time](/concepts/killzones-and-time.md)
- [Fair Value Gap](/concepts/fair-value-gap.md)

# Steps

1. Mark obvious reference levels: prior session high/low, Asian range extremes, opening-range gap boundaries, or equal highs/lows — anything the crowd watches.
2. Confirm HTF context: prefer fades that align with the daily bias or a Power-of-Three manipulation leg.
3. Wait for a killzone window (London open raids of the Asian range, NY AM premarket raids on NQ) for the sweep to occur.
4. Let price trade through the level, purging resting stops — do not front-run the raid.
5. Confirm rejection: swift return back inside the range, ideally with a displacement leg or FVG left behind.
6. Enter against the breakout on the rejection signal, or defer entry to a retrace into the newly formed FVG.
7. Stop just beyond the raid extreme.
8. Target the opposite side of the range first; runner toward external liquidity if displacement is strong.

# Invalidation

Price accepts beyond the swept level (sustained bodies and closes outside), no rejection forms within the killzone, or the sweep occurs without stop-run character (slow grind rather than raid).

# Sources

- [2017 Mentorship Month 08](/sources/2017-mentorship-month-08.md)
- [Forex Market Maker Primer](/sources/forex-market-maker-primer.md)
- [2025 Lecture Series](/sources/lecture-series-2025.md)
