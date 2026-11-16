#!/usr/bin/env python3
"""Honest parameter research for the scalping engine.

Runs a curated grid on a *train* window, then validates the top configs on a
held-out *test* window. Reports gross (pre-cost) and net (after fees+slippage)
side by side so the cost hurdle is explicit. No cherry-picking: every config is
printed, and the test window is only touched once for validation.

  python run_research.py --asset btc5m
  python run_research.py --asset xau1m
  python run_research.py --asset btc5m --quick
"""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import pandas as pd

from scalping_engine import data
from scalping_engine.engine import EngineConfig, simulate
from scalping_engine.metrics import compute_metrics

OUT = Path(__file__).resolve().parent / "outputs"


def grid(quick: bool):
    modes = ["sweep", "bos", "vwap", "mr"] if quick else ["sweep", "bos", "vwap", "mr", "combo"]
    rrs = [1.5, 2.0, 2.5]
    sl_atrs = [0.5, 0.8]
    max_bars = [12, 24]
    for mode, rr, sl, mb in itertools.product(modes, rrs, sl_atrs, max_bars):
        yield dict(entry_mode=mode, rr=rr, sl_atr_mult=sl, sl_min_atr=0.5,
                   max_holding_bars=mb, use_breakeven=False)


def orb_grid():
    """Opening-range breakout grid with the cheapest realistic Binance futures
    fee schedule (maker entry / taker exit). Wider stops lower the cost/R."""
    rrs = [1.0, 1.5, 2.0]
    sl_atrs = [0.5, 1.0, 2.0]
    max_bars = [12, 24]
    for rr, sl, mb in itertools.product(rrs, sl_atrs, max_bars):
        yield dict(entry_mode="orb", rr=rr, sl_atr_mult=sl, sl_min_atr=sl,
                   max_holding_bars=mb, use_breakeven=False,
                   entry_fee_pct=0.0002, exit_fee_pct=0.0005,
                   slippage_pct=0.0002)


def cfg_from_row(r, extra_fees: bool = False):
    kw = dict(entry_mode=r["entry_mode"], rr=float(r["rr"]),
              sl_atr_mult=float(r["sl_atr_mult"]),
              sl_min_atr=float(r["sl_min_atr"]) if "sl_min_atr" in r else 0.5,
              max_holding_bars=int(r["max_holding_bars"]),
              use_breakeven=False)
    if extra_fees:
        for k in ("entry_fee_pct", "exit_fee_pct", "slippage_pct", "min_confluence"):
            if k in r:
                kw[k] = float(r[k])
    return EngineConfig(**kw)


def run_one(df, cfg: EngineConfig, risk=0.01):
    eng, eq = simulate(df, cfg, initial_equity=100.0, risk_pct=risk)
    return compute_metrics(eng.trades, eq, 100.0), eng


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--asset", choices=["btc5m", "xau1m", "nsx1m"], default="btc5m")
    p.add_argument("--quick", action="store_true")
    p.add_argument("--orb", action="store_true",
                   help="use the session-opening-range (ORB) grid with futures-maker fees")
    p.add_argument("--risk", type=float, default=0.01)
    p.add_argument("--top", type=int, default=6)
    a = p.parse_args()
    tag = f"orb_{a.asset}" if a.orb else a.asset

    if a.asset == "btc5m":
        train = data.load_btc_5m([2025])
        test = data.load_btc_5m([2026])
    elif a.asset == "xau1m":
        train = data.load_xau_1m(["2026-06", "2026-07", "2026-08", "2026-09"])
        test = data.load_xau_1m(["2026-10"])
    else:
        train = data.load_nsx_1m(["2026-06", "2026-07", "2026-08", "2026-09"])
        test = data.load_nsx_1m(["2026-10"])

    rows = []
    for g in (orb_grid() if a.orb else grid(a.quick)):
        cfg = EngineConfig(**g)
        try:
            m, _ = run_one(train, cfg, a.risk)
        except Exception as e:  # noqa: BLE001
            print("skip", g, e)
            continue
        rows.append({**g, "n": m["n"], "wr": round(m["wr_pct"], 1),
                     "gross_r": round(m["gross_r"], 1), "net_r": round(m["net_r"], 1),
                     "avg_cost_r": round(m.get("avg_cost_r", 0.0), 3),
                     "pf": round(m["pf"], 3), "dd": round(m["max_dd_pct"], 1),
                     "t": round(m["t_stat"], 2), "exp": round(m["expectancy_r"], 3)})

    df = pd.DataFrame(rows).sort_values("net_r", ascending=False)
    OUT.mkdir(exist_ok=True)
    df.to_csv(OUT / f"research_{tag}_train.csv", index=False)

    print("=" * 96)
    print(f"TRAIN {tag}  {train.index[0].date()}..{train.index[-1].date()}  "
          f"({len(train)} bars)   configs={len(df)}")
    print("-" * 96)
    print(f"{'mode':7} {'rr':>4} {'sl':>4} {'bars':>4} | {'N':>4} {'WR%':>5} "
          f"{'grossR':>7} {'netR':>7} {'PF':>6} {'DD%':>5} {'t':>6} {'expR':>6}")
    for _, r in df.head(15).iterrows():
        print(f"{r['entry_mode']:7} {r['rr']:>4} {r['sl_atr_mult']:>4} "
              f"{r['max_holding_bars']:>4} | {r['n']:>4} {r['wr']:>5} "
              f"{r['gross_r']:>7} {r['net_r']:>7} {r['pf']:>6} {r['dd']:>5} "
              f"{r['t']:>6} {r['exp']:>6}")

    # ---- held-out validation of the top configs (touched once) ----------- #
    print("-" * 96)
    print(f"TEST (held-out) {a.asset}  {test.index[0].date()}..{test.index[-1].date()}")
    val = []
    for _, r in df.head(a.top).iterrows():
        cfg = cfg_from_row(r, extra_fees=a.orb)
        m, _ = run_one(test, cfg, a.risk)
        val.append({**r.to_dict(), "test_n": m["n"], "test_wr": round(m["wr_pct"], 1),
                    "test_gross_r": round(m["gross_r"], 1),
                    "test_net_r": round(m["net_r"], 1), "test_pf": round(m["pf"], 3),
                    "test_dd": round(m["max_dd_pct"], 1), "test_t": round(m["t_stat"], 2)})
    vdf = pd.DataFrame(val)
    vdf.to_csv(OUT / f"research_{tag}_test.csv", index=False)
    for _, r in vdf.iterrows():
        print(f"{r['entry_mode']:7} rr={r['rr']} sl={r['sl_atr_mult']} "
              f"bars={r['max_holding_bars']} -> TEST N={r['test_n']} "
              f"WR={r['test_wr']}% gross={r['test_gross_r']}R net={r['test_net_r']}R "
              f"PF={r['test_pf']} DD={r['test_dd']}% t={r['test_t']}")

    best = df.iloc[0]
    print("-" * 96)
    print(f"BEST TRAIN: {best['entry_mode']} rr={best['rr']} sl={best['sl_atr_mult']} "
          f"bars={best['max_holding_bars']}  net={best['net_r']}R  gross={best['gross_r']}R")
    print("NOTE: grossR is before fees/slippage; netR is after. A positive grossR with")
    print("negative netR means the signal has edge but not enough to pay costs.")
    print("=" * 96)


if __name__ == "__main__":
    main()
