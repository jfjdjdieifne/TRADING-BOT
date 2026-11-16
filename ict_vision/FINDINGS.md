# Findings — the "chart reader" on 6.8 years of NAS100USD 1-minute data

Everything below is measured, not asserted. Reproduce with:

```bash
.venv/bin/python ict_vision/scripts/run_backtest.py --out ict_vision/results
```

Run: 2020-01-01 → 2026-10-16, 2,277,180 one-minute bars (455,698 five-minute
bars), decisions on the 5-minute bar, fills resolved on the 1-minute bar.
Costs: 1.0 price unit half-spread per side + 0.5 slippage on stops — i.e.
2.5 price units round-trip, applied to every trade including the controls.

---

## 1. The headline

| | trades | win % | mean R | t |
|---|---|---|---|---|
| **This engine** | 206 | 46.6 | **+0.071** | +1.24 |
| Rigid hard-coded ICT | 326 | 35.6 | −0.010 | −0.13 |
| Random entries, same cost model | 824 | 34.6 | −0.287 | −5.70 |

**The honest read: expectancy is +0.07R with t = 1.24. That is not
statistically distinguishable from zero.** The 95% bootstrap CI is
[−0.039, +0.186] — it straddles zero. Anyone who tells you this model is a
money printer is using look-ahead or ignoring costs.

## 2. But the mechanism is real — the ablations prove it

Same 206 trades, one thing changed at a time:

| what we changed | mean R | what it isolates |
|---|---|---|
| engine as-is | **+0.071** | — |
| engine's exact entry level, **coin-flip direction** | −0.796 | does it know **which way**? → worth **+0.87R** |
| same bars, same direction, **enter at market** (no OTE wait) | −0.963 | does the **limit entry** pay? → worth **+1.03R** |

Both ablations destroy the result. So the engine genuinely reads direction and
genuinely benefits from waiting for the retracement rather than chasing —
it is not curve-fit noise. What it does *not* have is enough edge left over
after 2.5 price units of round-trip cost to clear significance.

## 3. The trap I fell into, and how to spot it

My first displacement filter scored each bar and then kept bars where

```python
score[t] >= score[t-3 : t+4].max()      # <-- t+4 is the FUTURE
```

That three-bar peek into the future produced a **fade-the-displacement edge of
+1.31 σ with t = +15.0**, stable in every single year from 2020 to 2026,
monotone in leg size, strongest in exactly the hours ICT says are strongest.
It looked like the holy grail.

Rebuilt causally (trailing window only):

```
w = 0 bars : n=13,587   fade −0.142 σ (t = −2.8)
w = 3 bars : n= 8,870   fade −0.148 σ (t = −2.3)
w = 6 bars : n= 8,266   fade −0.173 σ (t = −2.5), win 49.5%
```

The entire effect was the future. The only thing that survives is a weak
**continuation** drift of +0.173 σ over 12 bars, and it is sign-unstable by
year: 2020 −0.112, 2021 +0.875, 2022 +0.236, 2023 −0.006, 2024 +0.159,
2025 −0.228, 2026 +0.281.

**Rule going forward: any filter referencing a bar index > t is guilty until
proven otherwise.** A second instance of the same bug was found in the FVG
lifecycle scoring (it scanned the full 576-bar outcome window); both are fixed.

For scale: 200,000 random starting bars give mean |z| of 0.883 / 0.971 / 1.201
over 12 / 36 / 144 bars. **A "1 sigma" move is ordinary noise here.** Only
t-statistics mean anything.

## 4. What the model learned (walk-forward, no peeking)

- **Entry depth: 89.9%** of the displacement leg. ICT's prior is 62–79%, mean
  70.5%. The data on this instrument says enter *deeper* than the textbook.
- **Highest-density retracement interval: 100.8%–105.1%** from 327 resolved
  legs — i.e. the modal outcome is price retracing the *entire* leg and a bit
  more before resolving.
- **Extension past the leg extreme: 0.71 × leg** (learned, was 0.51 at 306 legs).
- **Discovered killzones (ET):** 07:30–10:45 scores **3.00×** the day average;
  15:15–16:15 1.46×; 01:00–01:30 1.23×; 03:00–03:45 1.20×.
- **How ICT's canonical windows actually score on this instrument:**

  | window | score |
  |---|---|
  | Macro 08:50 | 2.87× |
  | NY AM killzone | 1.86× |
  | Macro 09:50 | 1.37× |
  | Macro 15:15 | 1.35× |
  | Silver Bullet NY (10:00–11:00) | 1.20× |
  | Silver Bullet AM (03:00–04:00) | 1.12× |
  | London open killzone | **0.98×** |
  | Macro 10:50 | 0.94× |

  The 08:50 macro is a genuinely dominant window. The London open killzone —
  one of the most-repeated rules in the ICT canon — measures **below average**
  on NAS100USD. The model found that on its own; nobody told it.

- **Premium/discount equilibrium:** the time-at-price centroid sits at
  pd = +0.058 instead of the +0.5 arithmetic midpoint. Price spends its time
  near equilibrium and visits the extremes briefly, which is exactly what the
  logit membership function in `core/dealing.py` encodes.

## 5. Year-by-year (this is the weak point)

| year | n | win % | mean R |
|---|---|---|---|
| 2020 | 44 | 45.5 | +0.052 |
| 2021 | 34 | 52.9 | +0.241 |
| 2022 | 56 | 50.0 | +0.043 |
| 2023 | 25 | 40.0 | +0.075 |
| 2024 | 25 | 36.0 | −0.178 |
| 2025 | 10 | 20.0 | −0.120 |
| 2026 | 12 | 75.0 | +0.462 |

Positive in five of seven years, negative in 2024–2025. With 10–12 trades in
the last two years the per-year numbers are mostly noise, but the trend from
2022 → 2025 is not encouraging and should be read as "the edge is decaying or
was never there".

## 6. Known unresolved defects

1. **R(d) degeneracy.** `R = (1+g−entry)/(entry+buffer)` diverges as depth → 1,
   so expected value is monotone increasing in depth and the chosen depth pins
   to the 0.90 cap. It needs a cost/R model that stops improving at deep
   retracement — cap R by the measured extension distribution, or penalise by
   `p_reach` more steeply. **The 89.9% number should be treated as an artefact
   of this until fixed.**
2. **`f1` (the fraction taken at target 1) is always 0.95**, the upper grid
   edge. `_scale_fraction`'s objective keeps improving as f → 1; check the
   `u_miss` branch.
3. **Mean MFE of 13.8→17.3 R** while most trades exit at the stop. Possibly a
   `_r_of` denominator artefact (`risk_cash` fixed at signal time vs at fill).
   Verify before trusting any trade-level statistic.
4. **176 of 206 trades exit at the stop or on the hazard rule**; only one ever
   reached target 2. The target structure is effectively never reached, so the
   "2R first objective" framing is doing no work.

## 7. Bottom line

The framework is sound and it is not a pile of magic numbers — every threshold
is measured from the data and it independently rediscovered the 08:50 macro,
the NY AM session, and the value of entering on a deep retracement rather than
chasing. It beats a rigid textbook ICT implementation and badly beats random.

It does **not** produce a statistically significant edge on this instrument
after realistic costs. Treat it as a research base, not a system to fund.
