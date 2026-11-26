#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lab_v50_tournament.py -- v50 STAGE 2/3. Single process, resumable.

Runs V50_MODE arms on JAN24/JAN26 and then the 43-month suite, writing
results/v50_engine/<mode>__<window>__<bps>.csv after EVERY cell and
re-rendering results/REPORT_AR_v50.md after every cell.

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
import lab_v50_report as REP                      # noqa: E402

RES = HERE / "results"
ENG = RES / "v50_engine"
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
ARMS = ["p1_c4_m025", "p2_c4_m030", "p3_c4_m035",
        "s1_shield_br", "s2_reentry", "s3_knife", "s1s3_combo",
        "s1s2s3_combo"]
# each arm name -> (V50_MODE, V50_X)
V50_SPEC = {
    "p1_c4_m025":   ("p1_c4_m025", -0.25),
    "p2_c4_m030":   ("p2_c4_m030", -0.30),
    "p3_c4_m035":   ("p3_c4_m035", -0.35),
    "s1_shield_br": ("s1_shield_br", -0.30),
    "s2_reentry":   ("s2_reentry",  -0.30),
    "s3_knife":     ("s3_knife",    -0.30),
    "s1s3_combo":   ("s1s3_combo",  -0.30),
    "s1s2s3_combo": ("s1s2s3_combo", -0.30),
    "B0":           ("off",         -0.30),
}


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
    S.V48_MODE = "off"
    S.V49_MODE = "off"
    _m, _x = V50_SPEC.get(mode, ("off", -0.30))
    S.V50_MODE = _m
    S.V50_X = _x
    S.V50_SHIELD_X = -0.30
    S.V50_KNIFE_X = -0.65
    S.V49_CAP = 4.0
    S.V49_BOX_HOURS = 24.0
    S.V49_BOX_TOL = 0.0025
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
    if tr is None or not len(tr) or "entry_time" not in tr.columns:
        return {"mode": mode, "win": win, "bps": bps, "n": 0, "gross": 0.0,
                "fees": 0.0, "net": 0.0, "pf": 0.0, "wr": 0.0, "wk": {},
                "yk": {}, "half": {}, "reasons": {}}
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
                   if "v50" in k}
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
    elif what == "stage2s2":
        # the two arms added after stage2 was launched
        for mode in ("s2_reentry", "s1s2s3_combo"):
            for win in ("jan24", "jan26"):
                dd, a, b = MONTHS[win]
                run_cell(mode, win, 0, dd, a, b)
        REP.render()
        print(f"\nstage2s2 total {time.time()-t0:.0f}s")
    elif what == "stage3all":
        # Stage 3(b): the remaining plateau cells at 0 bps. The -0.20x cell
        # already exists as v48's G1 (identical threshold AND identical
        # floor_only window), so it is NOT re-run; the report reads it from
        # results/v48_engine/. P2 (-0.30x) is already done in stage2.
        for mode in ("p1_c4_m025", "p3_c4_m035"):
            for win in list(WINDOWS):
                a, b = WINDOWS[win]
                run_cell(mode, win, 0, DEFAULT_DATA, a, b)
        REP.render()
        print(f"\nstage3all total {time.time()-t0:.0f}s")
    elif what == "b0bps":
        # Stage 3(a) needs a B0 book at 2bps for every window: none exists.
        for win in list(WINDOWS):
            a, b = WINDOWS[win]
            run_cell("B0", win, 2, DEFAULT_DATA, a, b)
        REP.render()
        print(f"\nb0bps total {time.time()-t0:.0f}s")
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
