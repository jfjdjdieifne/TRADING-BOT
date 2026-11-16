#!/usr/bin/env python3
"""Does stacking confluence conditions actually raise the hit rate / expectancy?

Runs a base mode (orb / sweep / bos) at several confluence-score thresholds and
reports the result. If a high threshold raises the hit rate but the expectancy
stays negative, the conditions are not predictive (or the target is too small).

    python3 run_confluence.py --asset btc5m --mode orb
    python3 run_confluence.py --asset xau1m --mode sweep
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from scalping_engine import data
from scalping_engine.engine import EngineConfig, simulate
from scalping_engine.metrics import compute_metrics

OUT = Path(__file__).resolve().parent / "outputs"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--asset", choices=["btc5m", "xau1m", "nsx1m"], default="btc5m")
    ap.add_argument("--mode", default="orb")
    ap.add_argument("--years", type=int, nargs="*", default=[2025, 2026])
    ap.add_argument("--months", nargs="*", default=None)
    ap.add_argument("--rr", type=float, default=1.5)
    ap.add_argument("--sl-atr", type=float, default=0.5)
    ap.add_argument("--max-bars", type=int, default=24)
    ap.add_argument("--entry-fee", type=float, default=0.0002)
    ap.add_argument("--exit-fee", type=float, default=0.0005)
    ap.add_argument("--slip", type=float, default=0.0002)
    a = ap.parse_args()

    if a.asset == "btc5m":
        df = data.load_btc_5m(a.years)
    elif a.asset == "xau1m":
        df = data.load_xau_1m(a.months)
    else:
        df = data.load_nsx_1m(a.months)

    rows = []
    for mc in [0.0, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
        cfg = EngineConfig(entry_mode=a.mode, rr=a.rr, sl_atr_mult=a.sl_atr,
                           sl_min_atr=0.5, max_holding_bars=a.max_bars,
                           use_breakeven=False, entry_fee_pct=a.entry_fee,
                           exit_fee_pct=a.exit_fee, slippage_pct=a.slip,
                           min_confluence=mc)
        eng, eq = simulate(df, cfg, initial_equity=100.0, risk_pct=0.01)
        m = compute_metrics(eng.trades, eq, 100.0)
        rows.append({"min_confluence": mc, "n": m["n"],
                     "wr": round(m["wr_pct"], 1), "pf": round(m["pf"], 3),
                     "net_r": round(m["net_r"], 1), "gross_r": round(m["gross_r"], 1),
                     "cost_r": round(m.get("avg_cost_r", 0), 3),
                     "exp": round(m["expectancy_r"], 3),
                     "dd": round(m["max_dd_pct"], 1), "t": round(m["t_stat"], 2)})
    d = pd.DataFrame(rows)
    OUT.mkdir(exist_ok=True)
    d.to_csv(OUT / f"confluence_{a.asset}_{a.mode}.csv", index=False)
    print("=" * 92)
    print(f"CONFLUENCE TEST  {a.asset}  mode={a.mode}  rr={a.rr}  "
          f"sl={a.sl_atr}  bars={a.max_bars}")
    print("-" * 92)
    print(f"{'min_conf':>8} | {'N':>5} {'WR%':>6} {'PF':>6} {'grossR':>7} "
          f"{'netR':>7} {'costR/tr':>8} {'expR':>6} {'DD%':>5} {'t':>6}")
    for _, r in d.iterrows():
        print(f"{r['min_confluence']:>8} | {r['n']:>5} {r['wr']:>6} {r['pf']:>6} "
              f"{r['gross_r']:>7} {r['net_r']:>7} {r['cost_r']:>8} "
              f"{r['exp']:>6} {r['dd']:>5} {r['t']:>6}")
    print("-" * 92)
    print("If WR rises with min_conf but exp stays <= 0, the confluence conditions")
    print("are not predictive enough to pay the cost hurdle.")
    print("=" * 92)


if __name__ == "__main__":
    main()
