#!/usr/bin/env python3
"""Run the causal scalping engine on local archives and print honest metrics.

Examples
--------
  python run_backtest.py --asset btc5m --years 2025 2026
  python run_backtest.py --asset xau1m --months 2026-08 2026-09 2026-10
  python run_backtest.py --asset btc5m --mode sweep --rr 2.0 --risk 0.02
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scalping_engine import data
from scalping_engine.engine import EngineConfig, simulate
from scalping_engine.metrics import compute_metrics, fmt

OUT = Path(__file__).resolve().parent / "outputs"


def build_config(a) -> EngineConfig:
    return EngineConfig(
        entry_mode=a.mode,
        rr=a.rr,
        sl_atr_mult=a.sl_atr,
        sl_min_atr=a.sl_min_atr,
        require_candle_confirm=not a.no_confirm,
        require_htf_align=not a.no_htf,
        risk_pct=a.risk,
        fee_pct=a.fee,
        entry_fee_pct=a.entry_fee,
        exit_fee_pct=a.exit_fee,
        slippage_pct=a.slip,
        max_holding_bars=a.max_bars,
        killzone=(a.kz_lo, a.kz_hi),
        max_trades_per_day=a.max_trades,
        daily_loss_pct=a.daily_loss,
        use_breakeven=not a.no_be,
        mr_z=a.mr_z,
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--asset", choices=["btc5m", "xau1m", "nsx1m"], default="btc5m")
    p.add_argument("--years", type=int, nargs="*", default=[2025, 2026])
    p.add_argument("--months", nargs="*", default=None)
    p.add_argument("--mode", choices=["sweep", "ob", "vwap", "bos", "reclaim", "mr", "combo"],
                   default="combo")
    p.add_argument("--rr", type=float, default=1.5)
    p.add_argument("--sl-atr", type=float, default=0.5)
    p.add_argument("--sl-min-atr", type=float, default=0.5)
    p.add_argument("--risk", type=float, default=0.01)
    p.add_argument("--fee", type=float, default=0.00075)
    p.add_argument("--entry-fee", type=float, default=None,
                   help="default: same as --fee; set 0.0002 for maker limit entries")
    p.add_argument("--exit-fee", type=float, default=None)
    p.add_argument("--slip", type=float, default=0.0002)
    p.add_argument("--max-bars", type=int, default=12)
    p.add_argument("--kz-lo", type=int, default=7)
    p.add_argument("--kz-hi", type=int, default=16)
    p.add_argument("--max-trades", type=int, default=6)
    p.add_argument("--daily-loss", type=float, default=0.03)
    p.add_argument("--mr-z", type=float, default=2.0)
    p.add_argument("--no-confirm", action="store_true")
    p.add_argument("--no-htf", action="store_true")
    p.add_argument("--no-be", action="store_true")
    p.add_argument("--capital", type=float, default=100.0)
    p.add_argument("--tag", default="")
    a = p.parse_args()

    if a.asset == "btc5m":
        df = data.load_btc_5m(a.years)
    elif a.asset == "xau1m":
        df = data.load_xau_1m(a.months)
    else:
        df = data.load_nsx_1m(a.months)

    cfg = build_config(a)
    eng, eq = simulate(df, cfg, initial_equity=a.capital)
    m = compute_metrics(eng.trades, eq, a.capital)
    m["asset"] = a.asset
    m["window"] = [str(df.index[0]), str(df.index[-1])]
    m["bars"] = int(len(df))
    m["config"] = vars(a)

    print("=" * 78)
    print(f"SCALPING BACKTEST  {a.asset}  {df.index[0]} -> {df.index[-1]}  ({len(df)} bars)")
    print("-" * 78)
    print(fmt(m))
    print(f"avg_win={m['avg_win_r']:.3f}R  avg_loss={m['avg_loss_r']:.3f}R  "
          f"avg_bars={m['avg_bars']:.1f}")
    print("reasons:", m["reasons"])
    print("exits  :", m["exits"])
    print("=" * 78)

    OUT.mkdir(exist_ok=True)
    tag = a.tag or f"{a.asset}_{a.mode}"
    with open(OUT / f"summary_{tag}.json", "w") as f:
        json.dump(m, f, indent=2, default=str)
    if eng.trades:
        import pandas as pd
        t = pd.DataFrame([vars(tr) for tr in eng.trades])
        t.to_csv(OUT / f"trades_{tag}.csv", index=False)
        pd.DataFrame({"Datetime": df.index, "equity": eq}).to_csv(
            OUT / f"equity_{tag}.csv", index=False)
    print(f"saved -> {OUT}/summary_{tag}.json")


if __name__ == "__main__":
    main()
