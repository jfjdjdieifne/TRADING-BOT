#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lab_v48_tournament.py -- v48 STAGE 2/3. Single process, resumable.

Runs V47_MODE arms on JAN24/JAN26 and then the 43-month suite, writing
results/v47_engine/<mode>__<window>__<bps>.csv after EVERY cell and
re-rendering results/REPORT_AR_v47.md after every cell.

B0 baselines are never re-run: lab_v45_runs.json already holds JAN24 and
JAN26 at 0 bps, and results/trades_v37_B0_<W>.csv holds the 43-month book.

USAGE  python3 lab_v47_tournament.py stage2
       python3 lab_v47_tournament.py stage3 <MODE>
       python3 lab_v47_tournament.py stage3bps <MODE>
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import strategy_v36_ict_champion as S            # noqa: E402
import lab_v37_anti_fragile as L                  # noqa: E402
import lab_v48_report as REP                      # noqa: E402

RES = HERE / "results"
ENG = RES / "v48_engine"
ENG.mkdir(parents=True, exist_ok=True)
WARMUP = 60

MONTHS = {"jan24": ("data/binance_5m_jan24", "2024-01-01", "2024-01-31"),
          "jan26": ("data/binance_5m_jan26", "2026-01-01", "2026-01-31")}
DEFAULT_DATA = "data/binance_5m"
WINDOWS = {"W1": ("2023-10-01", "2024-03-31"),
           "MOD_Y2": ("2025-11-01", "2026-10-31"),
           "W2": ("2024-05-01", "2024-10-31"),
           "OLD7": ("2023-01-01", "2023-07-31"),
           "MOD_Y1": ("2024-11-01", "2025-10-31")}
ARMS = ["g1_exec_m02", "g2_exec_00", "g3_exec2_00", "g4_1h_00"]


def apply(mode: str, bps: float):
    for k, v in L.SHIPPED.items():
        setattr(S, k, v)
    S.CAPITAL = 100.0
    S.FULL_100_DEPLOY = True
    S.MAX_OPEN_POSITIONS = 1
    for k, v in (("V43_POST3R_MODE", "off"), ("V44_PARTIAL_3R_FRAC", 0.0),
                 ("V44_RUNNER_POST3R_MODE", "off"),
                 ("V44_EXIT_BRAIN_MODE", "off"),
                 ("V45_BRAIN_MODE", "off"), ("V46_BRAIN_MODE", "off")):
        if hasattr(S, k):
            setattr(S, k, v)
    S.V47_MODE = "off"
    S.V48_MODE = "off" if mode == "B0" else mode
    S.V48_X = -0.20
    S.V47_X1 = 1.0
    S.V47_X2 = 1.5
    S.V47_RAISE_AT = 4.0
    S.V47_COOLDOWN_H = 8.0
    S.SLIPPAGE_BPS = 0.0
    S.EXIT_SLIPPAGE_BPS = float(bps)
    S.EXIT_SLIP = S.EXIT_SLIPPAGE_BPS / 10000.0


def cell_path(mode, win, bps):
    return ENG / f"{mode}__{win}__{int(bps)}.csv"


def summarise(tr: pd.DataFrame, mode, win, bps):
    tr = tr.copy()
    tr["entry_ts"] = pd.to_datetime(tr.entry_time, utc=True, format="mixed")
    tr = tr.sort_values("entry_ts").reset_index(drop=True)
    wk = tr.entry_ts.dt.isocalendar()
    tr["iso"] = (wk.year.astype(int).astype(str) + "-W"
                 + wk.week.astype(int).astype(str).str.zfill(2))
    tr["half"] = ["H1" if d.day <= 16 else "H2" for d in tr.entry_ts]
    tr["ym"] = tr.entry_ts.dt.strftime("%Y-%m")
    wins = tr[tr.net_pnl > 0]
    gross = float(((tr.exit_price - tr.entry_price) * tr.qty0).sum())
    fees = float((tr.entry_fee + tr.exit_price * tr.qty0 * 0.001).sum())
    return {"mode": mode, "win": win, "bps": bps, "n": int(len(tr)),
            "gross": round(gross, 2), "fees": round(fees, 2),
            "net": round(float(tr.net_pnl.sum()), 2),
            "pf": round(float(wins.net_pnl.sum()
                              / -tr[tr.net_pnl < 0].net_pnl.sum()), 3)
            if (tr.net_pnl < 0).any() else float("inf"),
            "wr": round(float((tr.net_pnl > 0).mean() * 100), 1),
            "wk": {k: round(float(v), 2)
                   for k, v in tr.groupby("iso").net_pnl.sum().items()},
            "yk": {k: round(float(v), 2)
                   for k, v in tr.groupby("ym").net_pnl.sum().items()},
            "half": {k: round(float(v), 2)
                     for k, v in tr.groupby("half").net_pnl.sum().items()},
            "reasons": {str(a): int(b) for a, b in
                        tr.exit_reason.value_counts().items()}}


def run_cell(mode, win, bps, data_dir, start, end):
    p = cell_path(mode, win, bps)
    meta = p.with_suffix(".json")
    if p.exists() and meta.exists():
        print(f"[skip] {p.name}", flush=True)
        return json.loads(meta.read_text())
    apply(mode, bps)
    S.V32_DATA_DIR = data_dir
    t0 = time.time()
    run = S.run_backtest(S.v34_data_dir(), start, end, warmup_days=WARMUP,
                         tag=f"{mode}__{win}__{int(bps)}")
    tr = pd.DataFrame(run["trades"])
    tr.to_csv(p, index=False)                     # checkpoint the CSV first
    s = summarise(tr, mode, win, bps)
    s["secs"] = round(time.time() - t0, 1)
    eq = run.get("equity")
    if eq is not None and len(eq):
        ser = eq["equity"].astype(float)
        s["maxDD"] = round(float(((ser.cummax() - ser) / ser.cummax()).max()
                                 * 100), 2)
    else:
        s["maxDD"] = 0.0
    s["counts"] = {k: v for k, v in (run.get("count") or {}).items()
                   if "v48" in k}
    meta.write_text(json.dumps(s, indent=1, default=str))
    print(f"[done] {p.name:38s} n={s['n']:3d} net={s['net']:+8.2f} "
          f"pf={s['pf']} dd={s['maxDD']:.1f}% {s['secs']:.0f}s "
          f"v47fires={s['counts']}", flush=True)
    REP.render()                                  # re-render after every cell
    return s


def main() -> int:
    what = sys.argv[1] if len(sys.argv) > 1 else "stage2"
    t0 = time.time()
    if what == "stage2":
        for mode in ARMS:
            for win in ("jan24", "jan26"):
                dd, a, b = MONTHS[win]
                run_cell(mode, win, 0, dd, a, b)
        REP.render()
        print(f"\nstage2 total {time.time()-t0:.0f}s")
    elif what == "stage3":
        mode = sys.argv[2]
        for win in ("W1", "MOD_Y2", "W2", "OLD7", "MOD_Y1"):
            a, b = WINDOWS[win]
            run_cell(mode, win, 0, DEFAULT_DATA, a, b)
        REP.render()
        print(f"\nstage3 {mode} total {time.time()-t0:.0f}s")
    elif what == "stage3bps":
        mode = sys.argv[2]
        wins = sys.argv[3].split(",") if len(sys.argv) > 3 else list(WINDOWS)
        for win in wins:
            a, b = WINDOWS[win]
            run_cell(mode, win, 2, DEFAULT_DATA, a, b)
        REP.render()
        print(f"\nstage3bps {mode} total {time.time()-t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
