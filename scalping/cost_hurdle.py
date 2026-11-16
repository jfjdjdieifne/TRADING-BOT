#!/usr/bin/env python3
"""The cost hurdle — why scalping a small account is mathematically brutal.

Per trade, in units of R (risk):
    cost_R = (entry_fee + exit_fee + 2 * slippage) / stop_distance_fraction

because:
    notional   = risk_usd / stop_distance_fraction
    cost_$     = notional * (fees + slippage)
    cost_R     = cost_$ / risk_usd

So the *only* ways to lower the hurdle are: cheaper fees (maker/futures),
wider stops, or less slippage. The gross edge must exceed cost_R.

    python3 cost_hurdle.py
"""

from __future__ import annotations

SCHEDULES = {
    "binance_spot_taker": (0.0010, 0.0010),
    "binance_spot_bnb": (0.00075, 0.00075),
    "binance_futures_taker": (0.0005, 0.0005),
    "binance_futures_maker": (0.0002, 0.0005),   # limit entry, taker exit
    "binance_futures_both_maker": (0.0002, 0.0002),
}


def cost_r(entry_fee: float, exit_fee: float, slip: float, stop_pct: float) -> float:
    return (entry_fee + exit_fee + 2 * slip) / stop_pct


def main():
    slip = 0.0002
    print("=" * 82)
    print("COST HURDLE: how many R does one round trip cost?")
    print(f"(slippage per side = {slip:.3%})")
    print("=" * 82)
    stops = [0.002, 0.005, 0.010, 0.020, 0.030, 0.050]
    print(f"{'fee schedule':28} | " + " | ".join(f"stop {s:.1%}" for s in stops))
    print("-" * 82)
    for name, (ef, xf) in SCHEDULES.items():
        cells = [f"{cost_r(ef, xf, slip, s):>9.3f}" for s in stops]
        print(f"{name:28} | " + " | ".join(cells))
    print("-" * 82)
    print("Read: a BTC 5m scalp with a 0.5% stop and spot taker fees pays ~0.40R per")
    print("trade. The measured gross edge of the ORB strategy on our data is ~0.02R.")
    print("The hurdle is ~20x the edge. That is the whole story of 1m/5m scalping.")
    print("=" * 82)
    print()
    print("Required gross edge (R/trade) to net +0.10R, by schedule and stop:")
    for name, (ef, xf) in SCHEDULES.items():
        cells = [f"{cost_r(ef, xf, slip, s)+0.10:>9.3f}" for s in stops]
        print(f"{name:28} | " + " | ".join(cells))


if __name__ == "__main__":
    main()
