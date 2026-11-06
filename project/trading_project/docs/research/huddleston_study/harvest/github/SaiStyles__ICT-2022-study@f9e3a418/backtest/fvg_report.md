# Does the fair value gap carry information?

`dev` slice 2010-06-06..2021-12-31. Ledger n = 86. Reserve untouched, holdout SEALED.

FVG appears in **36 of 41 episodes**. ep02 [17:53]: `one candle passes
higher, previous candle's high and next candle's low do not overlap`.

**A gap only forms after a fast three-bar move**, so a raw fill rate says
nothing - price retraces after any fast move. Every gap here is paired with
a control bar that had a **same-sized move at the same hour and left no
gap**, and the identical measurement runs on both. `touch` = price reached
the near edge; `fill` = price crossed the far edge; `return` = forward move
signed in the direction that made the gap.

**The bar is |z| > 3.0** - DECISIONS.md 24.

| tf | dir | horizon | gaps | far edge | touch | ctrl | **z** | fill | ctrl | **z** | fwd ret | ctrl | **z** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5m | bullish | +20min | 89,106 | 2.2pt | 69.9% | 78.3% | **-40.5** | 48.0% | 62.1% | **-59.9** | +0.10pt | -0.07pt | **+2.8** |
| 5m | bullish | +60min | 85,770 | 2.5pt | 81.5% | 86.7% | **-29.3** | 66.6% | 76.2% | **-44.1** | +0.20pt | +0.27pt | **-0.7** |
| 5m | bullish | +120min | 80,829 | 2.5pt | 86.5% | 90.0% | **-21.8** | 75.5% | 82.2% | **-32.6** | +0.45pt | +0.70pt | **-1.7** |
| 5m | bearish | +20min | 81,307 | 2.2pt | 71.6% | 79.2% | **-35.6** | 50.0% | 64.2% | **-57.9** | -0.05pt | -0.35pt | **+4.7** |
| 5m | bearish | +60min | 78,279 | 2.5pt | 83.1% | 87.5% | **-24.5** | 69.0% | 77.7% | **-38.8** | -0.15pt | -0.54pt | **+3.4** |
| 5m | bearish | +120min | 73,774 | 2.5pt | 88.0% | 91.0% | **-18.6** | 77.9% | 84.1% | **-30.6** | -0.42pt | -0.83pt | **+2.4** |
| 15m | bullish | +60min | 28,010 | 4.5pt | 67.4% | 76.0% | **-22.8** | 47.5% | 60.4% | **-30.7** | +0.34pt | +0.46pt | **-0.7** |
| 15m | bullish | +180min | 24,937 | 4.8pt | 79.9% | 85.1% | **-15.2** | 66.5% | 74.7% | **-20.0** | +0.81pt | +1.22pt | **-1.2** |
| 15m | bullish | +360min | 19,999 | 4.8pt | 85.4% | 89.1% | **-11.2** | 76.0% | 81.6% | **-13.6** | +1.15pt | +3.00pt | **-3.3** |
| 15m | bearish | +60min | 24,302 | 4.8pt | 70.1% | 78.1% | **-20.1** | 49.8% | 63.8% | **-31.2** | +0.01pt | -0.74pt | **+3.4** |
| 15m | bearish | +180min | 21,660 | 4.8pt | 82.2% | 86.5% | **-12.3** | 68.9% | 77.3% | **-19.6** | -0.30pt | -1.19pt | **+2.2** |
| 15m | bearish | +360min | 17,212 | 5.2pt | 87.4% | 90.3% | **-8.6** | 78.3% | 83.8% | **-13.0** | -0.62pt | -1.67pt | **+1.6** |
| 60m | bullish | +240min | 6,358 | 10.2pt | 64.0% | 74.9% | **-13.4** | 46.4% | 61.2% | **-16.8** | +1.14pt | +0.40pt | **+0.9** |
| 60m | bullish | +720min | 3,321 | 9.0pt | 81.3% | 86.4% | **-5.6** | 72.2% | 79.3% | **-6.7** | +1.33pt | +5.50pt | **-2.1** |
| 60m | bearish | +240min | 5,047 | 11.2pt | 68.8% | 76.1% | **-8.3** | 48.5% | 62.6% | **-14.2** | -0.23pt | -4.22pt | **+4.2** |
| 60m | bearish | +720min | 2,601 | 10.2pt | 83.6% | 88.4% | **-4.9** | 74.7% | 81.2% | **-5.6** | -0.69pt | -6.83pt | **+2.5** |

## How to read it

- **touch/fill z > 0**: price returns to a gap MORE than it retraces the
  same distance after a matched move - the gap attracts. This is the claim
  the corpus rests on.
- **fwd return z > 0**: the gap predicts CONTINUATION beyond what the move
  alone predicts. `[OUTSIDE]` the published gap literature expects this sign,
  and it is the opposite of how the gap is usually traded.
- **both near zero**: the gap is a description of a fast move, not a cause
  of anything - and 36 of 41 episodes rest on a redescription.
