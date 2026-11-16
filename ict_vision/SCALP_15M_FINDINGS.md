# The 15m "hammer after the raid" scalper — measured, on XAUUSD and NAS100

```bash
.venv/bin/python ict_vision/scripts/scalp_15m.py --label XAUUSD --spread 0.5
.venv/bin/python ict_vision/scripts/scalp_15m.py \
    --data smc_v4_multisleeve_package/data/NSXUSD_1m_histdata \
    --label NSXUSD --cache /tmp/scalp_nsx.pkl --spread 2.5
```

6.8 years (2020-01 → 2026-10), 2.36M one-minute bars on gold, 2.28M on Nasdaq.
Decisions on 15m, **fills resolved on 1-minute bars**, stop assumed to fill
before the target inside the same bar (pessimistic). Costs: 0.50 round-trip on
gold, 2.5 on Nasdaq.

---

## 1. The setup, as specified

1. On 15m, a low gets raided: a candle drives its wick under it, body closes back above.
2. Two to three candles later: **C1** = big bullish reversal candle; **C2** =
   the next bearish candle whose wick does **not** reach the midpoint of C1
   (even a hair above the 50% counts).
3. Entry = close of C2. Stop = below C2's low by a fixed fraction.
   Target = the first swing high before the raided low, a hair under its wick.
4. **Variant A** (called strongest): the move left a fair value gap.
   **Variant B** (weaker): same, no FVG.

486 candidates on gold, 440 on Nasdaq — roughly **4 a month, one a week.**

## 2. The stop is the whole trade

Your spec says **0.02%**. On gold that is about **$0.40**; on Nasdaq about
**4 points**. Here is what that does:

| stop distance | gold win% | gold meanR | Nasdaq win% | Nasdaq meanR |
|---|---|---|---|---|
| **0.02% (yours)** | 15.7% | **−0.689** | 18.7% | **−0.142** |
| 0.05% | 23.7% | −0.308 | 26.4% | −0.065 |
| 0.10% | 34.6% | −0.147 | 35.1% | −0.147 |
| 0.20% | 46.9% | −0.082 | 47.4% | +0.019 |
| 0.40% | 60.3% | −0.035 | **62.5%** | **+0.099** (t=+1.53) |
| 0.80% | **73.4%** | +0.014 | 73.3% | **+0.086** (t=+1.91) |
| 1.50% | 78.0% | +0.001 | 76.8% | +0.026 |

**Why: the median maximum adverse excursion is 12–14× the stop you specified.**
The typical trade travels twelve times deeper against you before it resolves.
A 0.02% stop is not "tight risk", it is a coin that almost always lands tails,
and on gold the round-trip cost (0.50) is *larger than the entire risk* (0.40).

## 3. Where the 90% win rate actually comes from

This is the important part, and it is not a criticism — it is the explanation.

| scenario | target hit | never stopped out |
|---|---|---|
| stop 0.02% | 18% | 18% |
| stop 0.80% | 73% | 77% |
| **no stop, hold to target or 24h** | **77%** | **100%** |

**If you do not use a hard stop — or you move it, or you are still in the trade
when it eventually comes back — you win about three times out of four, and with
any leniency about what counts as a win you would honestly report "around 90%".**
That is almost certainly your lived experience, and it is real.

But it is the same coin seen from the other side. The expectancy does not
improve — meanR goes from +0.014 to +0.001 when you remove the stop. What
changes is *when* the loss lands and *how large it is*: with no stop the loss
is unbounded and shows up as one catastrophic trade instead of many small ones.
Gold's total P&L is **negative in all three scenarios** (−204, −222, −201).

## 4. What survives

**Your variant ranking is correct, and I could not have guessed it.** On both
instruments the fair-value-gap version hits the target more often:

| | gold win% | gold target-hit | Nasdaq win% | Nasdaq target-hit |
|---|---|---|---|---|
| **A: with FVG** (you: strongest) | 74.5% | 75% | 64.5% | 66% |
| **B: no FVG** (you: weaker) | 71.3% | 67% | 58.6% | 59% |

Confirmed on two independent instruments. That part of your read is real.

**The pattern has a small, non-significant edge on Nasdaq and none on gold.**
Best Nasdaq cell: +0.099R at a 0.4% stop, t = +1.53; +0.086R at 0.8%, t = +1.91.
Neither clears significance. Gold's best cell is +0.014R, t = +0.41 — zero.

## 5. Monthly — the horizon you actually asked about

Gold, stop 0.8%: **79 months, 44 of them profitable (56%)**. Median 4 trades a
month. Full table in `ict_vision/results_scalp/scalp_XAUUSD_monthly.csv`.

By year (Nasdaq, 0.4% stop): 2020 +0.249, 2021 −0.083, 2022 +0.269, 2023 +0.086.
Gold, 0.8% stop: 2020 +0.240, 2021 −0.059, 2022 +0.049, 2023 −0.004,
2024 +0.210, 2025 +0.148, **2026 −0.285**.

**2026 breaks on both instruments.** Whatever the edge was, it is not there now.

## 6. The frequency problem — this is the real blocker

~4 setups a month, ~1 a week. You said you want **daily** profit on small
capital. At 0.1R expectancy and one trade a week that is ~0.4R a month; at 1%
risk that is **0.4% a month** — about $4 on a $1,000 account. Daily income is
arithmetically impossible with this pattern at this frequency, no matter how
good the execution is.

## 7. What I would change, and why

1. **Stop: 0.02% → structure-based, ≈0.4–0.8%.** Not a fixed fraction — put it
   below the swing that C2 made, then verify it is at least ~15× the spread.
   The sweep says the sweet spot is 20–40× your current distance.
2. **Keep the FVG filter.** It is the one thing that measurably separates the
   two variants on both instruments.
3. **Target: take partial at the first swing high, not all of it.** Median time
   to target is 156 one-minute bars on gold (2.6 hours) and 88 on Nasdaq. Most
   of the give-back happens after a long hold.
4. **Trade Nasdaq, not gold.** Gold's cost-to-risk ratio at any sane stop is
   unfavourable; Nasdaq is the only one of the two with a positive expectancy.
5. **Do not trade 2026-style regimes.** The last year is negative on both.

## 8. Honest bottom line

The FVG filter is a genuine, reproducible observation — that is worth keeping.
Everything else I measured says the setup, taken literally, is break-even before
costs and slightly negative after, and that the 90% win rate comes from not
taking the stop rather than from the entry being unusually accurate.

I may still be mis-reading one thing: whether "0.02%" is really the stop
distance you use, or whether it is the *risk per trade as a fraction of
account* (which would be a completely different and much more workable rule).
Tell me which and I will re-run it in an afternoon.
