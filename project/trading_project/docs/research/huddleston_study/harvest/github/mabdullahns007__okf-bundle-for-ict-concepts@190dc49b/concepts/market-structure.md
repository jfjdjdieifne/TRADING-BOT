---
type: Concept
title: Market Structure
description: ICT's fractal framework of swing highs and lows, breaks of structure, and changes in the state of price delivery used to define bias across time frames.
tags: [concept, structure, core]
generated: { by: ox-alpha/opencode, at: 2026-08-25T10:57:21Z }
---

# Definition
Structure is the sequence of swing highs and swing lows formed by price delivery. A **break of structure (BOS)** is displacement through a swing point *in the direction of the prevailing trend* (continuation); a **change of state of delivery** — more commonly called a market structure shift (MSS) or break of structure in the opposite sense — is displacement through a swing point *against* the prior trend, signaling reversal. ICT separates **external structure** (the visible range extremes — old highs/lows where liquidity rests) from **internal structure** (intermediate highs/lows inside the range), and reads **short-term structure** (intraday swings) nested inside **higher-time-frame structure** (daily/weekly narrative).

# Mechanics
Because external extremes hold liquidity pools, ICT treats an external run as suspect: the classic sequence is a run on buy-side above an old high, a displacement lower breaking internal short-term lows (the MSS with a fair value gap left behind), then continuation ([/concepts/liquidity.md]). Higher-time-frame structure sets the dealing range and premium/discount context ([/concepts/premium-discount.md]); short-term structure supplies entries aligned to it.

# Application
Workflow used throughout the 2022 mentorship and later series: establish HTF bias from weekly/daily structure and draw on liquidity, drop to a killzone time frame, wait for a manipulation and MSS in the bias direction, then enter on the displaced imbalance ([/concepts/fair-value-gap.md], [/concepts/optimal-trade-entry.md], [/playbooks/daily-bias-workflow.md]). Counter-trend trades are framed as engaging internal structure while respecting external structure ([/sources/mentorship-2022.md]).

# Evolution
Early 2016–2017 mentorships taught swing analysis largely via "market structure shifts" around specific arrays; the 2022+ era standardized BOS/MSS terminology and the internal/external distinction; 2025–2026 lectures fold structure into the algorithmic price-delivery continuum and chain-of-custody framing ([/sources/lecture-series-2025.md], [/sources/smart-money-lectures-2026.md]). Terminology shifted over the years — older material says "change of state of delivery," newer material mostly says MSS.

# Related
- [/concepts/liquidity.md](liquidity.md)
- [/concepts/premium-discount.md](premium-discount.md)
- [/concepts/fair-value-gap.md](fair-value-gap.md)
- [/concepts/killzones-and-time.md](killzones-and-time.md)
