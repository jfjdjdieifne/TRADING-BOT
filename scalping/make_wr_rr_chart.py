#!/usr/bin/env python3
"""Plot the empirical win-rate vs reward:risk trade-off (BTC 5m, ORB, zero cost)."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from scalping_engine import data
from scalping_engine.engine import EngineConfig, simulate
from scalping_engine.metrics import compute_metrics

OUT = Path(__file__).resolve().parent / "outputs"


def main():
    df = data.load_btc_5m([2025, 2026])
    rrs = [0.2, 0.5, 0.8, 1.0, 1.5, 2.0, 3.0]
    rows = []
    for rr in rrs:
        cfg = EngineConfig(entry_mode="orb", rr=rr, sl_atr_mult=0.5, sl_min_atr=0.5,
                           max_holding_bars=24, use_breakeven=False,
                           fee_pct=0.0, slippage_pct=0.0)
        eng, eq = simulate(df, cfg, initial_equity=100.0, risk_pct=0.01)
        m = compute_metrics(eng.trades, eq, 100.0)
        rows.append((rr, m["wr_pct"], m["expectancy_r"], m["pf"], m["net_r"]))
        print(f"rr={rr}: WR={m['wr_pct']:.1f}% exp={m['expectancy_r']:+.3f}R "
              f"PF={m['pf']:.3f} net={m['net_r']:+.1f}R")
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
    ax[0].plot([r[0] for r in rows], [r[1] for r in rows], "o-", color="tab:blue")
    ax[0].set_xlabel("reward:risk (target / stop)")
    ax[0].set_ylabel("win rate %")
    ax[0].set_title("Higher target -> lower win rate")
    ax[0].grid(alpha=0.3)
    ax[1].plot([r[0] for r in rows], [r[2] for r in rows], "o-", color="tab:red")
    ax[1].axhline(0, color="k", lw=0.8)
    ax[1].set_xlabel("reward:risk")
    ax[1].set_ylabel("expectancy (R per trade)")
    ax[1].set_title("Expectancy peaks near 1:1, not at 90% WR")
    ax[1].grid(alpha=0.3)
    fig.suptitle("BTC 5m ORB — the win-rate / R:R trade-off (zero costs)", fontsize=11)
    fig.tight_layout()
    OUT.mkdir(exist_ok=True)
    fig.savefig(OUT / "wr_rr_tradeoff.png", dpi=120)
    print("saved", OUT / "wr_rr_tradeoff.png")


if __name__ == "__main__":
    main()
