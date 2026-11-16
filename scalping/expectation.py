#!/usr/bin/env python3
"""The honest math of "$100 -> $1000 in 2 days".

Monte-Carlo of fixed-fractional compounding:
    equity_{i+1} = equity_i * (1 + f*r)   on a win
    equity_{i+1} = equity_i * (1 - f)     on a loss
where f = fraction risked per trade, r = reward:risk, p = win rate.

It answers two questions:
  1. What risk fraction f is *required* to turn $100 into $1000 in n trades?
  2. What is the probability of actually getting there, and of blowing up?

No strategy is assumed. This is pure arithmetic.
"""

from __future__ import annotations

import argparse
import numpy as np


def required_f(p: float, r: float, n: int, target_mult: float = 10.0) -> float:
    """Smallest f such that the *expected* compound result reaches the target."""
    lo, hi = 1e-6, 0.999
    for _ in range(80):
        mid = (lo + hi) / 2
        exp_log = n * (p * np.log(1 + mid * r) + (1 - p) * np.log(1 - mid))
        if exp_log < np.log(target_mult):
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def monte_carlo(p: float, r: float, f: float, n: int, start: float = 100.0,
                target: float = 1000.0, ruin: float = 10.0,
                sims: int = 200_000, seed: int = 7):
    rng = np.random.default_rng(seed)
    eq = np.full(sims, start)
    hit_target = np.zeros(sims, dtype=bool)
    ruined = np.zeros(sims, dtype=bool)
    wins = rng.random((sims, n)) < p
    for i in range(n):
        eq = np.where(wins[:, i], eq * (1 + f * r), eq * (1 - f))
        hit_target |= eq >= target
        ruined |= eq <= ruin
    return {
        "p_reach_target": float(hit_target.mean() * 100),
        "p_ruin": float(ruined.mean() * 100),
        "median_final": float(np.median(eq)),
        "mean_final": float(eq.mean()),
        "p10_final": float(np.percentile(eq, 10)),
        "p90_final": float(np.percentile(eq, 90)),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--win-rate", type=float, default=0.50)
    ap.add_argument("--rr", type=float, default=1.0)
    ap.add_argument("--trades", type=int, default=40,
                    help="trades in 2 days (e.g. 20/day)")
    ap.add_argument("--target", type=float, default=1000.0)
    ap.add_argument("--start", type=float, default=100.0)
    a = ap.parse_args()

    n = a.trades
    target_mult = a.target / a.start
    print("=" * 78)
    print(f"$100 -> ${a.target:.0f} in {n} trades  (target = {target_mult:.1f}x)  "
          f"win rate={a.win_rate:.0%}  R:R={a.rr}:1")
    print("-" * 78)
    f_req = required_f(a.win_rate, a.rr, n, target_mult)
    print(f"Required risk per trade (to make the EXPECTED value reach target): "
          f"{f_req:.1%} of equity")
    print()
    print(f"{'risk/trade':>10} | {'P(reach $1000)':>15} | {'P(ruin <=$10)':>14} | "
          f"{'median $':>9} | {'mean $':>9} | {'p10 $':>8} | {'p90 $':>8}")
    for f in [0.01, 0.02, 0.05, 0.10, 0.25, 0.50, f_req]:
        if f <= 0 or f >= 1:
            continue
        m = monte_carlo(a.win_rate, a.rr, f, n, a.start, a.target)
        print(f"{f:>10.1%} | {m['p_reach_target']:>14.2f}% | {m['p_ruin']:>13.2f}% | "
              f"{m['median_final']:>9.1f} | {m['mean_final']:>9.1f} | "
              f"{m['p10_final']:>8.1f} | {m['p90_final']:>8.1f}")
    print("-" * 78)
    print("Reading: a '90% win rate' strategy still needs a huge risk fraction to")
    print("10x in 2 days, and the ruin probability stays high. This is gambling,")
    print("not an edge. The realistic path is small risk per trade, many trades,")
    print("and time (see README.md).")
    print("=" * 78)


if __name__ == "__main__":
    main()
