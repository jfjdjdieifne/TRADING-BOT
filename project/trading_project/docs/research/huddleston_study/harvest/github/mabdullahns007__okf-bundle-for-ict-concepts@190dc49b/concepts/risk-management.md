---
type: Concept
title: Risk Management
description: ICT's risk doctrine — stops beyond liquidity pools, partials at short-term targets, strict position sizing, and one-shot-one-kill selectivity.
tags: [concept, risk, money-management]
generated: { by: ox-alpha/opencode, at: 2026-08-25T10:57:21Z }
---

# Definition

ICT frames risk management as the survival layer of trading: small fixed risk per trade, stops placed relative to liquidity rather than arbitrary dollar amounts, and a low-frequency "one-shot-one-kill" approach that trades only A+ setups in defined time windows.

# Mechanics

- **Stop placement**: above buyside liquidity / below sellside liquidity — e.g., beyond the sweep extreme of a turtle-soup raid or OTE impulse leg ([/concepts/liquidity.md], [/concepts/optimal-trade-entry.md]). If your stop sits inside an obvious liquidity pool, the algorithm is likely to take it.
- **Position sizing**: risk a small fixed fraction per trade so no single loss impairs the account; size derives from stop distance, not conviction.
- **Partials**: scale out at intermediate draw-on-liquidity targets (relative equal highs/lows, FVGs — [/concepts/fair-value-gap.md]) to bank gains while letting a runner seek external range liquidity.
- **Avoidance rules**: stand aside around NFP, CPI, FOMC releases unless trading them deliberately; early mentorships repeatedly show avoiding news spikes.

# Application

The [If I Could Go Back](/sources/if-i-could-go-back.md) series stresses that overtrading and oversized risk cost ICT years, while the [New Forex Traders Guide](/sources/new-forex-traders-guide.md) prescribes demo mastery before live capital and one setup traded repeatedly.

# Related

- [/concepts/risk-management.md] pairs with [/concepts/trading-psychology.md](/concepts/trading-psychology.md)
- [/concepts/turtle-soup.md](/concepts/turtle-soup.md)
- [/concepts/premium-discount.md](/concepts/premium-discount.md)
- [/sources/if-i-could-go-back.md](/sources/if-i-could-go-back.md)
