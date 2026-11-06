# The liquidity sweep and the order block, isolated

`dev` slice. Ledger n = 152. Reserve untouched, holdout SEALED. Bar is |z| > 3.0 (DECISIONS.md 24).

Same matched design that settled the FVG (findings.md 4): every event is
paired with a **same-sized move, same direction, same hour, no event**.

- **Liquidity sweep** (ep25 [28:36]): after price takes the previous
  session's high or low, does it REVERSE more than a matched move? The
  `event` column is signed so positive = reversed as the corpus claims.
- **Order block** (ep17 [11:10]): formation is near-universal, so this
  measures the real claim - the reaction when price RETURNS to the zone.
  Positive = reacted in the direction the block predicts.

| test | what | tf | horizon | n | event | matched ctrl | **z** |
|---|---|---|---|---|---|---|---|
| liquidity sweep | sweep of prev HIGH | 5m | +30min | 5,739 | +0.213pt | -0.275pt | **+1.59** |
| liquidity sweep | sweep of prev HIGH | 5m | +60min | 5,672 | +0.187pt | -0.451pt | **+1.57** |
| liquidity sweep | sweep of prev HIGH | 5m | +120min | 5,510 | +0.447pt | -1.378pt | **+3.10** |
| liquidity sweep | sweep of prev LOW | 5m | +30min | 4,044 | +0.119pt | +0.252pt | **-0.29** |
| liquidity sweep | sweep of prev LOW | 5m | +60min | 3,991 | +0.330pt | +0.426pt | **-0.16** |
| liquidity sweep | sweep of prev LOW | 5m | +120min | 3,885 | +0.710pt | +1.033pt | **-0.36** |
| order block | bullish order block (on return) | 5m | +30min | 67,578 | +0.035pt | +0.655pt | **-7.58** |
| order block | bullish order block (on return) | 5m | +60min | 66,213 | +0.136pt | +0.737pt | **-5.20** |
| order block | bullish order block (on return) | 5m | +120min | 63,294 | +0.411pt | +0.628pt | **-1.29** |
| order block | bearish order block (on return) | 5m | +30min | 67,052 | -0.100pt | +0.601pt | **-8.98** |
| order block | bearish order block (on return) | 5m | +60min | 65,637 | -0.211pt | +0.849pt | **-9.35** |
| order block | bearish order block (on return) | 5m | +120min | 62,722 | -0.456pt | +0.838pt | **-7.92** |
| liquidity sweep | sweep of prev HIGH | 15m | +90min | 3,520 | +0.015pt | -0.018pt | **+0.05** |
| liquidity sweep | sweep of prev HIGH | 15m | +180min | 3,377 | +0.194pt | +0.564pt | **-0.39** |
| liquidity sweep | sweep of prev HIGH | 15m | +360min | 3,088 | +0.236pt | -2.151pt | **+1.86** |
| liquidity sweep | sweep of prev LOW | 15m | +90min | 2,567 | +0.576pt | +0.127pt | **+0.46** |
| liquidity sweep | sweep of prev LOW | 15m | +180min | 2,465 | +1.968pt | +2.178pt | **-0.16** |
| liquidity sweep | sweep of prev LOW | 15m | +360min | 2,209 | +4.522pt | +2.761pt | **+0.96** |
| order block | bullish order block (on return) | 15m | +90min | 24,371 | +0.192pt | +1.532pt | **-5.82** |
| order block | bullish order block (on return) | 15m | +180min | 22,699 | +0.439pt | +1.326pt | **-2.64** |
| order block | bullish order block (on return) | 15m | +360min | 19,479 | +1.264pt | +1.664pt | **-0.76** |
| order block | bearish order block (on return) | 15m | +90min | 23,459 | -0.386pt | +1.562pt | **-8.64** |
| order block | bearish order block (on return) | 15m | +180min | 21,809 | -0.680pt | +1.971pt | **-8.01** |
| order block | bearish order block (on return) | 15m | +360min | 18,774 | -0.899pt | +2.060pt | **-5.58** |
