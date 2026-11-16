#!/usr/bin/env python3
"""Historical day/week/month aggregation for the separate V8.3 ledger.

This is NOT a backtest of MOMENTUM-X and does NOT simulate realistic portfolio
capital, concurrent positions, margin or equity sizing. It only sums the
existing V8.3 trade-ledger net-R by exit date. V8 files remain read-only.

    python3 run_horizons.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TRADES = ROOT / "smc_v4_multisleeve_package/results/trades_v8_3asset_1pos_each.csv"
OUT = Path(__file__).resolve().parent / "outputs"


def load():
    df = pd.read_csv(TRADES)
    df["exit_time"] = pd.to_datetime(df["exit_time"], utc=True)
    return df.sort_values("exit_time")


def main():
    d = load()
    d["day"] = d["exit_time"].dt.date
    horizon = {}
    for label, rule in (("DAY", "D"), ("WEEK", "W"), ("MONTH", "ME"), ("YEAR", "YE")):
        g = d.set_index("exit_time").resample(rule).agg(
            n=("net_r", "size"), net_r=("net_r", "sum"))
        if label == "DAY":
            g = g[g["n"] > 0]          # only days that actually traded
        else:
            g = g[g["net_r"] != 0]
        horizon[label] = g

    print("=" * 88)
    print("V8.3 HISTORICAL LEDGER — net-R summed by exit day/week/month/year")
    print("This is an aggregation of the existing ledger, not a portfolio simulation.")
    print(f"trades={len(d)}  {d['exit_time'].iloc[0].date()}..{d['exit_time'].iloc[-1].date()}  "
          f"total={d['net_r'].sum():.1f}R")
    print("=" * 88)
    out = {}
    for label, g in horizon.items():
        pos = (g["net_r"] > 0).sum()
        s = {
            "periods": int(len(g)),
            "positive": int(pos),
            "positive_pct": round(100 * pos / len(g), 1),
            "total_r": round(float(g["net_r"].sum()), 1),
            "best_r": round(float(g["net_r"].max()), 1),
            "avg_positive_r": round(float(g.loc[g["net_r"] > 0, "net_r"].mean()), 2),
            "worst_r": round(float(g["net_r"].min()), 1),
        }
        out[label] = s
        print(f"{label:6} periods={s['periods']:>4}  positive={s['positive']:>4} "
              f"({s['positive_pct']:>5.1f}%)  total={s['total_r']:>+8.1f}R  "
              f"best={s['best_r']:>+6.1f}R  avg_win={s['avg_positive_r']:>+5.2f}R  "
              f"worst={s['worst_r']:>+6.1f}R")

    print("-" * 88)
    yrs = horizon["YEAR"]
    print("YEARLY:", ", ".join(f"{i.year} {v:+.1f}R" for i, v in yrs["net_r"].items()))
    print(f"MONTHS positive: {out['MONTH']['positive']}/{out['MONTH']['periods']}  |  "
          f"WEEKS positive: {out['WEEK']['positive']}/{out['WEEK']['periods']}")
    print("Best MONTHS (R):", ", ".join(
        f"{i.strftime('%Y-%m')} {v:+.1f}" for i, v in
        horizon["MONTH"]["net_r"].nlargest(6).items()))
    print("Best WEEKS (R):", ", ".join(
        f"{i.strftime('%Y-%m-%d')} {v:+.1f}" for i, v in
        horizon["WEEK"]["net_r"].nlargest(6).items()))
    print("Best DAYS (R):", ", ".join(
        f"{i.strftime('%Y-%m-%d')} {v:+.1f}" for i, v in
        horizon["DAY"]["net_r"].nlargest(6).items()))

    m = horizon["MONTH"].copy()
    print("-" * 88)
    print("LAST 12 MONTHS (net-R by exit month):")
    print(m[["n", "net_r"]].tail(12).round(2).to_string())
    OUT.mkdir(exist_ok=True)
    (OUT / "horizons_summary.json").write_text(json.dumps(out, indent=2))
    m.reset_index().to_csv(OUT / "horizons_monthly_v8.csv", index=False)
    print("=" * 88)
    print("saved outputs/horizons_summary.json + horizons_monthly_v8.csv")


if __name__ == "__main__":
    main()
