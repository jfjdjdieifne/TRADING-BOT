---
type: Concept
title: Killzones and Time
description: ICT's thesis that specific time windows (London/NY killzones, macros, midnight open) drive algorithmic price delivery more than indicators or patterns.
tags: [concept, time, sessions, killzones]
generated: { by: ox-alpha/opencode, at: 2026-08-25T10:57:21Z }
---

# Definition

Killzones are recurring intraday windows during which ICT claims the algorithmic engine delivers its intended price moves: London Open (~2:00–5:00 AM NY), New York AM Open (~8:30–11:00 AM), London Close (~10:00–12:00 PM NY), and the Asian range session that builds the overnight consolidation those later moves run from.

# Mechanics

- **Asian Range**: the overnight high/low formed roughly 7 PM–midnight NY acts as manipulation fuel for London raids (see [/concepts/liquidity.md]).
- **NY AM Killzone**: primary window for index futures expansion, often following a premarket manipulation against the daily bias.
- **Macros**: short algorithmic windows — notably 9:50–10:10 AM, 10:50–11:10 AM NY, and the MOC (market-on-close) window near 3:50–4:00 PM — where price reliably seeks PD arrays (see [/concepts/fair-value-gap.md]).
- **Midnight Open**: the 12:00 AM NY reference price used for opening-range logic and judging the day's true direction (see [/concepts/opening-range-gaps.md]).

# Application

ICT's workflow is time-first: pick the window, then look for structure, liquidity raids, and PD arrays inside it. The 2022 Mentorship ([/sources/mentorship-2022.md](/sources/mentorship-2022.md)) dedicates multiple episodes to timing by session; the [2017 Mentorship Month 08](/sources/2017-mentorship-month-08.md) covers intraday profiles and when *not* to trade London. The [2025 Lecture Series](/sources/lecture-series-2025.md) formalizes NY lunch macro rules and MOC behavior.

# Evolution

Time-of-day framing has grown from "trade London" advice in early mentorships into a precise algorithmic-timing doctrine with named macro windows — the backbone of models like Silver Bullet.

# Related

- [/concepts/opening-range-gaps.md](/concepts/opening-range-gaps.md)
- [/concepts/power-of-three.md](/concepts/power-of-three.md)
- [/concepts/turtle-soup.md](/concepts/turtle-soup.md)
- [/concepts/market-structure.md](/concepts/market-structure.md)
