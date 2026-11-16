# The 15m raid-hammer scalper on BTCUSD

```bash
.venv/bin/python ict_vision/scripts/scalp_15m.py \
    --data smc_v4_multisleeve_package/data/BTCUSD_5m --label BTCUSD \
    --cache /tmp/btc.pkl --fill-minutes 5 --spread 0.0
```

7.87 years (2018-12 → 2026-11), 275,667 fifteen-minute bars.
**Caveat: the crypto source is 5-minute, so fills are resolved on 5m bars, not
1m.** That makes every stop/target resolution slightly coarser than the gold
and Nasdaq runs and biases results a little optimistic. The effect is small
but it is there.

**Stop definition corrected this run:** the stop is now a *distance below C2's
low*, `stop = low × (1 − pct)` — not a fraction of the entry.

---

## Stop sweep — BTCUSD, 669 tradable setups

| stop below the low | win % | mean R | t | target hit | mean R:R |
|---|---|---|---|---|---|
| **0.20% (as clarified)** | 31.4% | **−0.113** | −1.75 | 30% | 3.85 |
| 0.50% | 45.3% | −0.048 | −0.95 | 43% | 1.87 |
| 1.00% | 60.7% | +0.017 | +0.46 | 58% | 1.03 |
| 2.00% | 71.4% | +0.004 | +0.15 | 66% | 0.55 |
| 3.50% | 75.2% | −0.008 | −0.43 | 69% | 0.32 |
| 6.00% | 76.8% | −0.000 | −0.03 | 70% | 0.19 |
| 10.00% | 77.4% | +0.006 | +0.83 | 70% | 0.12 |

Same shape as gold and Nasdaq: **win rate rises, expectancy does not.**
0.2% gives 31% wins and −0.11R; widening the stop buys win rate and sells
R:R at exactly the rate that keeps expectancy at zero. Best cell is +0.017R
with t = +0.46. There is no edge here.

## The FVG split is the one real signal — and it is biggest on crypto

| variant | n | win % | mean R | t | target hit |
|---|---|---|---|---|---|
| **A: with fair value gap** (you: strongest) | 466 | **64.2%** | **+0.046** | +1.05 | 62% |
| **B: no fair value gap** (you: weaker) | 203 | 52.7% | **−0.050** | −0.71 | 47% |

The gap between the variants is far wider on Bitcoin (0.096R) than on gold
(0.034R) or Nasdaq (0.031R). **Your ranking is right on all three
instruments**, but it is most decisive on the one you actually trade.

## By year

| year | n | win % | mean R |
|---|---|---|---|
| 2019 | 87 | 60.9 | +0.002 |
| 2020 | 105 | 48.6 | −0.167 |
| 2021 | 97 | 55.7 | +0.168 |
| 2022 | 70 | 57.1 | −0.061 |
| 2023 | 92 | 67.4 | +0.065 |
| 2024 | 71 | 64.8 | +0.122 |
| 2025 | 71 | 71.8 | +0.006 |
| 2026 | 76 | 64.5 | +0.023 |

## By month

**94 months, 52 with positive meanR (55%).** ~8.8 setups a month — better
frequency than gold or Nasdaq, roughly 2 a week.

## Frequency

833 setups / 94 months ≈ **8.8 a month, ~2 a week.** Better than the 4/month on
gold, but still not a daily-income engine, and the expectancy is ~0.

## What this run changes

1. **The stop is confirmed as the whole trade.** 0.2% below the low is still
   too tight: 31% win rate. The R:R it offers (3.85) is illusory because the
   target is almost never reached before the stop.
2. **Trade variant A only.** Dropping variant B takes the book from +0.017R to
   +0.046R and is the single biggest improvement available.
3. **Expectancy is zero on crypto too.** +0.046R on variant A with t = +1.05 is
   not statistically significant.
