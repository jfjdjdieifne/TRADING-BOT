#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lab_v46_2cells.py -- v46 STEP 2. EXACTLY TWO engine runs.

Per the brief: the B0 and v45 baselines are REUSED from results/
lab_v45_runs.json and are NOT re-run. Only the v46 brain is executed, once on
JAN24 and once on JAN26, at 0 bps, with the mandatory 60-day warmup.

    JAN24  2024-01-01 .. 2024-01-31   data/binance_5m_jan24
    JAN26  2026-01-01 .. 2026-01-31   data/binance_5m_jan26

Everything else is the shipped champion: CAPITAL forced to 100, one seat,
100% deployment, every v43/v44 partial-scale knob off, 100% exits only.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import strategy_v36_ict_champion as S            # noqa: E402
import lab_v37_anti_fragile as L                  # noqa: E402

RES = HERE / "results"
WINDOWS = {"jan24": ("data/binance_5m_jan24", "2024-01-01", "2024-01-31"),
           "jan26": ("data/binance_5m_jan26", "2026-01-01", "2026-01-31")}
WARMUP = 60


def apply_config():
    for k, v in L.SHIPPED.items():
        setattr(S, k, v)
    S.CAPITAL = 100.0
    S.FULL_100_DEPLOY = True
    S.MAX_OPEN_POSITIONS = 1
    for k, v in (("V43_POST3R_MODE", "off"), ("V44_PARTIAL_3R_FRAC", 0.0),
                 ("V44_RUNNER_POST3R_MODE", "off"), ("V44_EXIT_BRAIN_MODE", "off")):
        if hasattr(S, k):
            setattr(S, k, v)
    S.V45_BRAIN_MODE = "off"          # the v45 brain stays off
    S.V46_BRAIN_MODE = "swing_bounce"
    S.V46_MIN_X = 1.0
    S.V46_PIVOT = 2
    S.SLIPPAGE_BPS = 0.0
    S.EXIT_SLIPPAGE_BPS = 0.0
    S.EXIT_SLIP = 0.0


def summarize(run, win):
    tr = pd.DataFrame(run["trades"])
    tr["entry_ts"] = pd.to_datetime(tr.entry_time, utc=True, format="mixed")
    tr = tr.sort_values("entry_ts").reset_index(drop=True)
    wk = tr.entry_ts.dt.isocalendar()
    tr["iso"] = (wk.year.astype(int).astype(str) + "-W"
                 + wk.week.astype(int).astype(str).str.zfill(2))
    tr["half"] = ["H1" if d.day <= 16 else "H2" for d in tr.entry_ts]
    wins = tr[tr.net_pnl > 0]
    gross = ((tr.exit_price - tr.entry_price) * tr.qty0).sum()
    fees = (tr.entry_fee + tr.exit_price * tr.qty0 * 0.001).sum()
    eq = run.get("equity")
    dd = 0.0
    if eq is not None and len(eq):
        ser = eq["equity"].astype(float)
        dd = float(((ser.cummax() - ser) / ser.cummax()).max() * 100)
    out = {"win": win, "mode": "v46_swing_bounce", "slip_bps": 0,
           "n": int(len(tr)), "gross": round(float(gross), 2),
           "fees": round(float(fees), 2),
           "net": round(float(tr.net_pnl.sum()), 2),
           "maxDD": round(dd, 2),
           "pf": round(float(wins.net_pnl.sum()
                             / -tr[tr.net_pnl < 0].net_pnl.sum()), 3)
           if (tr.net_pnl < 0).any() else float("inf"),
           "wr": round(float((tr.net_pnl > 0).mean() * 100), 1),
           "wk": {k: round(float(v), 2)
                  for k, v in tr.groupby("iso").net_pnl.sum().items()},
           "wkplus": f"{int((tr.groupby('iso').net_pnl.sum() > 1e-9).sum())}"
                     f"/{tr.iso.nunique()}",
           "half": {k: round(float(v), 2)
                    for k, v in tr.groupby("half").net_pnl.sum().items()},
           "reasons": {str(a): int(b) for a, b in
                       tr.exit_reason.value_counts().items()},
           "trades": tr[["entry_time", "symbol", "exec_tf", "entry_price",
                         "stop_price", "exit_price", "exit_reason", "qty0",
                         "net_pnl", "R"]].to_dict("records"),
           "counts": {k: v for k, v in (run.get("count") or {}).items()
                      if "v46" in k or "v45" in k or "emergency" in k}}
    tr.to_csv(RES / f"trades_v46_{win}_v46_0.csv", index=False)
    return out


def main() -> int:
    f = RES / "lab_v46_runs.json"
    runs = json.loads(f.read_text()) if f.exists() else {}
    t0 = time.time()
    for win in ("jan24", "jan26"):
        key = f"{win}/v46@0"
        if key in runs:
            print(f"[skip] {key} already done", flush=True)
            continue
        dd, a, b = WINDOWS[win]
        apply_config()
        S.V32_DATA_DIR = dd
        t1 = time.time()
        run = S.run_backtest(S.v34_data_dir(), a, b, warmup_days=WARMUP,
                             tag=key)
        out = summarize(run, win)
        out["secs"] = round(time.time() - t1, 1)
        runs[key] = out
        f.write_text(json.dumps(runs, indent=1, default=str))
        print(f"[done] {key:16s} n={out['n']:3d} net={out['net']:+8.2f} "
              f"pf={out['pf']} dd={out['maxDD']:.1f}% {out['secs']:.0f}s",
              flush=True)
    print(f"\ntotal {time.time()-t0:.0f}s for 2 cells")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
