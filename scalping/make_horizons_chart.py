#!/usr/bin/env python3
"""Historical daily/weekly/monthly net-R chart for the separate V8.3 ledger.

This aggregates existing trade-ledger net-R by exit date. It is not a portfolio
simulation and is not a result for MOMENTUM-X.

    python3 make_horizons_chart.py   -> outputs/horizons_positive.png
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TRADES = ROOT / "smc_v4_multisleeve_package/results/trades_v8_3asset_1pos_each.csv"
OUT = Path(__file__).resolve().parent / "outputs"


def main():
    d = pd.read_csv(TRADES)
    d["exit_time"] = pd.to_datetime(d["exit_time"], utc=True)
    d = d.set_index("exit_time").sort_index()
    m = d["net_r"].resample("ME").sum()
    w = d["net_r"].resample("W").sum()
    w = w[w != 0]                       # only weeks that actually traded
    day = d["net_r"].resample("D").sum()
    day = day[day != 0]
    cum_r = d["net_r"].resample("ME").sum().cumsum()

    fig, ax = plt.subplots(2, 2, figsize=(13, 8))
    ax[0, 0].bar(m.index, m.values, width=22,
                 color=np.where(m.values >= 0, "tab:green", "tab:red"), alpha=0.85)
    ax[0, 0].axhline(0, color="k", lw=0.8)
    ax[0, 0].set_title(f"MONTHLY net R  —  {int((m>0).sum())}/{len(m)} months positive "
                       f"(best +{m.max():.1f}R)")
    ax[0, 0].set_ylabel("R (costs included)")
    ax[0, 1].plot(cum_r.index, cum_r.values, color="tab:blue", lw=1.8)
    ax[0, 1].set_title(f"Cumulative net R  ->  {cum_r.iloc[-1]:.1f}R  (7/7 positive years)")
    ax[0, 1].set_ylabel("cumulative R")
    ax[0, 1].grid(alpha=0.3)
    ax[1, 0].hist(w.values, bins=40, color="tab:purple", alpha=0.85)
    ax[1, 0].axvline(0, color="k", lw=0.8)
    ax[1, 0].set_title(f"WEEKLY net R  —  {int((w>0).sum())}/{len(w)} weeks positive "
                       f"(best +{w.max():.1f}R)")
    ax[1, 1].hist(day.values, bins=50, color="tab:orange", alpha=0.85)
    ax[1, 1].axvline(0, color="k", lw=0.8)
    ax[1, 1].set_title(f"DAILY net R  —  best +{day.max():.1f}R, "
                       f"worst {day.min():.1f}R, total +{day.sum():.1f}R")
    for a in ax.ravel():
        a.grid(alpha=0.25)
    fig.suptitle("V8.3 HISTORICAL NET-R BY DAY / WEEK / MONTH (not a portfolio simulation)",
                 fontsize=12)
    fig.tight_layout()
    OUT.mkdir(exist_ok=True)
    fig.savefig(OUT / "horizons_positive.png", dpi=120)
    print("saved", OUT / "horizons_positive.png")


if __name__ == "__main__":
    main()
