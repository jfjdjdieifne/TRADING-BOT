#!/usr/bin/env python3
"""SEPARATE REFERENCE TEST — daily time-series momentum (not MOMENTUM-X).

This script tests a simple daily moving-average rule on local BTC/XAU/NSX data.
It does NOT test the 12-condition 5m MOMENTUM-X rules in strategy.py and does
NOT test the full Binance USDT-M universe.

Walk-forward: for each test year Y, pick the lookback n using ONLY data up to
Y-1, then trade year Y with that n, with execution delay and assumed costs.

    python3 run_momentum.py
    python3 run_momentum.py --stress     # double assumed costs
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from scalping_engine import data

OUT = Path(__file__).resolve().parent / "outputs"
NS = [10, 20, 50, 100, 200]           # daily-bar lookbacks (pre-specified grid)


def daily(df: pd.DataFrame) -> pd.DataFrame:
    return df.resample("1D").agg(
        {"Open": "first", "High": "max", "Low": "min",
         "Close": "last", "Volume": "sum"}).dropna()


def signal(close: pd.Series, n: int, gate: bool) -> pd.Series:
    ma = close.rolling(n).mean()
    s = (close > ma)
    if gate:
        s = s & (close > close.shift(n))     # all-horizon-return positive gate
    return s.astype(float)


def run(c: pd.Series, n: int, gate: bool, cost: float, delay: int) -> pd.Series:
    """Net daily returns. Signal at t -> position during t+delay (no lookahead)."""
    r = c.pct_change().fillna(0.0).to_numpy()
    sig = np.nan_to_num(signal(c, n, gate).to_numpy(), nan=0.0)
    pos = np.roll(sig, delay)
    pos[:delay] = 0.0
    turn = np.abs(np.diff(np.r_[0.0, pos]))
    return pd.Series(pos * r - cost * turn, index=c.index)


def stats(net: pd.Series) -> dict:
    eq = (1 + net).cumprod()
    dd = ((eq.cummax() - eq) / eq.cummax()).max()
    t = net.mean() / (net.std(ddof=1) / np.sqrt(len(net))) if net.std() > 0 else 0.0
    w = (1 + net).resample("W").prod() - 1
    m = (1 + net).resample("ME").prod() - 1
    d = net
    return {
        "total_pct": round(100 * (eq.iloc[-1] - 1), 1),
        "t_stat": round(float(t), 2),
        "max_dd_pct": round(100 * float(dd), 1),
        "pos_days_pct": round(100 * float((d > 1e-12).mean()), 1),
        "nonneg_days_pct": round(100 * float((d >= -1e-12).mean()), 1),
        "pos_weeks_pct": round(100 * float((w > 1e-12).mean()), 1),
        "pos_months_pct": round(100 * float((m > 1e-12).mean()), 1),
        "best_week_pct": round(100 * float(w.max()), 1),
        "best_month_pct": round(100 * float(m.max()), 1),
        "avg_pos_month_pct": round(100 * float(m[m > 0].mean()), 1),
        "final_100usd": round(100 * float(eq.iloc[-1]), 2),
    }


def walk_forward(c: pd.Series, gate: bool, cost: float, delay: int,
                 first_test: int = 2020):
    """For each year, choose n on all PRIOR years only, then trade that year."""
    rows, parts = [], []
    for year in range(first_test, c.index[-1].year + 1):
        tr = c[c.index.year < year]
        te = c[c.index.year == year]
        if len(tr) < 250 or len(te) < 30:
            continue
        fits = []
        for n in NS:
            nr = run(tr, n, gate, cost, delay)
            eq = (1 + nr).cumprod()
            # objective: t-stat of daily net returns, tie-break by total
            t = nr.mean() / (nr.std(ddof=1) / np.sqrt(len(nr))) if nr.std() > 0 else 0
            fits.append((t, float(eq.iloc[-1]), n))
        _, _, best_n = max(fits)
        # IMPORTANT: recompute signal on the full series (rolling MA needs history),
        # but the parameter was chosen using past data only.
        full = run(c, best_n, gate, cost, delay)
        y = full[full.index.year == year]
        rows.append({"year": year, "n_chosen_prior": best_n,
                     "ret_pct": round(100 * ((1 + y).prod() - 1), 1),
                     "bh_pct": round(100 * (c[c.index.year == year].iloc[-1] /
                                            c[c.index.year == year].iloc[0] - 1), 1)})
        parts.append(y)
    oos = pd.concat(parts) if parts else pd.Series(dtype=float)
    return pd.DataFrame(rows), oos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cost", type=float, default=0.00095,
                    help="fee+slippage per side on 1x notional (default 0.075%+0.02%)")
    ap.add_argument("--stress", action="store_true", help="double the cost")
    ap.add_argument("--delay", type=int, default=2,
                    help="bars between signal and fill (default 2 = conservative)")
    ap.add_argument("--gate", action="store_true",
                    help="also require positive n-bar return (time-series gate)")
    ap.add_argument("--first-test", type=int, default=2020)
    a = ap.parse_args()
    cost = a.cost * (2 if a.stress else 1)

    print("=" * 88)
    print("WALK-FORWARD TIME-SERIES MOMENTUM  |  parameter chosen ONLY on prior years")
    print(f"cost/side={cost:.4%}  execution_delay={a.delay} bars  gate={a.gate}  "
          f"grid={NS}")
    print("=" * 88)

    assets = {}
    assets["BTCUSD 1D"] = daily(data.load_btc_5m())
    for name, loader in (("XAUUSD 1D", data.load_xau_1m), ("NSXUSD 1D", data.load_nsx_1m)):
        try:
            assets[name] = daily(loader())
        except Exception as e:  # noqa: BLE001
            print(f"[skip] {name}: {e}")

    all_oos = []
    for name, d in assets.items():
        rows, oos = walk_forward(d["Close"], a.gate, cost, a.delay, a.first_test)
        if oos.empty:
            continue
        s = stats(oos)
        print(f"\n--- {name}  ({len(d)} daily bars, OOS {oos.index[0].date()}.."
              f"{oos.index[-1].date()}) ---")
        print(f"{'year':>6} {'n(past)':>8} {'strategy%':>10} {'buy&hold%':>10}")
        for _, r in rows.iterrows():
            print(f"{r['year']:>6} {r['n_chosen_prior']:>8} "
                  f"{r['ret_pct']:>+10.1f} {r['bh_pct']:>+10.1f}")
        print(f"\nOOS AGGREGATE: total {s['total_pct']:+.1f}%  t={s['t_stat']}  "
              f"maxDD {s['max_dd_pct']}%  $100 -> ${s['final_100usd']}")
        print(f"  daily: positive {s['pos_days_pct']}%  non-negative "
              f"{s['nonneg_days_pct']}%   |   positive weeks {s['pos_weeks_pct']}%  "
              f"positive months {s['pos_months_pct']}%")
        print(f"  best week {s['best_week_pct']:+.1f}%  best month "
              f"{s['best_month_pct']:+.1f}%  avg positive month "
              f"{s['avg_pos_month_pct']:+.1f}%")
        OUT.mkdir(exist_ok=True)
        rows.to_csv(OUT / f"momentum_{name.split()[0]}_by_year.csv", index=False)
        all_oos.append((name, oos, s))
        print(f"  positive years: {sum(1 for _, r in rows.iterrows() if r['ret_pct'] > 0)}"
              f"/{len(rows)}")

    if all_oos:
        combined = pd.concat([x[1] for x in all_oos], axis=1).fillna(0.0).mean(axis=1)
        cs = stats(combined)
        print("\n" + "=" * 88)
        print("3-ASSET EQUAL-WEIGHT PORTFOLIO (OOS, no leverage, costs included)")
        print(f"  total {cs['total_pct']:+.1f}%  t={cs['t_stat']}  "
              f"maxDD {cs['max_dd_pct']}%  $100 -> ${cs['final_100usd']}")
        print(f"  positive weeks {cs['pos_weeks_pct']}%  positive months "
              f"{cs['pos_months_pct']}%  non-negative days {cs['nonneg_days_pct']}%")
        print("=" * 88)
        payload = {n: s for n, _, s in all_oos} | {"PORTFOLIO": cs}
        variant = "stress" if a.stress else ("gate" if a.gate else "base")
        (OUT / f"momentum_walkforward_{variant}.json").write_text(
            json.dumps(payload, indent=2))
        if variant == "base":
            (OUT / "momentum_walkforward_summary.json").write_text(
                json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
