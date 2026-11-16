#!/usr/bin/env python3
"""Plot the honest train-vs-test equity of the best research config.

Shows exactly how an in-sample "winning" scalping config behaves on data it never
saw. Usage:
    python3 make_chart.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from scalping_engine import data
from scalping_engine.engine import EngineConfig, simulate
from scalping_engine.metrics import compute_metrics

OUT = Path(__file__).resolve().parent / "outputs"

# best TRAIN config from run_research.py --asset btc5m
CFG = EngineConfig(entry_mode="vwap", rr=2.5, sl_atr_mult=0.5, sl_min_atr=0.5,
                   max_holding_bars=24, use_breakeven=False)


def equity(df, cfg):
    eng, eq = simulate(df, cfg, initial_equity=100.0, risk_pct=0.01)
    m = compute_metrics(eng.trades, eq, 100.0)
    return eq, m


def main():
    train = data.load_btc_5m([2025])
    test = data.load_btc_5m([2026])
    eq_tr, m_tr = equity(train, CFG)
    eq_te, m_te = equity(test, CFG)

    fig, ax = plt.subplots(1, 2, figsize=(13, 4.5))
    ax[0].plot(train.index, eq_tr, lw=1, color="tab:blue")
    ax[0].set_title(f"TRAIN 2025  N={m_tr['n']}  WR={m_tr['wr_pct']:.1f}%  "
                    f"net={m_tr['net_r']:+.1f}R  t={m_tr['t_stat']:.2f}")
    ax[0].set_ylabel("equity ($)")
    ax[1].plot(test.index, eq_te, lw=1, color="tab:red")
    ax[1].set_title(f"TEST 2026 (held-out)  N={m_te['n']}  WR={m_te['wr_pct']:.1f}%  "
                    f"net={m_te['net_r']:+.1f}R  t={m_te['t_stat']:.2f}")
    for a in ax:
        a.grid(alpha=0.3)
    fig.suptitle("BTC 5m scalping — best in-sample config vs held-out data "
                 "(vwap rr=2.5 sl=0.5 bars=24)", fontsize=11)
    fig.tight_layout()
    OUT.mkdir(exist_ok=True)
    fig.savefig(OUT / "research_btc5m_chart.png", dpi=120)
    print("saved", OUT / "research_btc5m_chart.png")
    print(f"TRAIN 2025: {m_tr['net_r']:+.1f}R  WR={m_tr['wr_pct']:.1f}%  t={m_tr['t_stat']:.2f}")
    print(f"TEST  2026: {m_te['net_r']:+.1f}R  WR={m_te['wr_pct']:.1f}%  t={m_te['t_stat']:.2f}")


if __name__ == "__main__":
    main()
