#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lab_v45_1month_microscope.py -- v45 STEP 2 (engine, 8 cells).

Two 1-month windows, four arms each, at 0 and 2 bps exit slippage:

    JAN24  2024-01-01 .. 2024-01-31   data/binance_5m_jan24
    JAN26  2026-01-01 .. 2026-01-31   data/binance_5m_jan26
    arms   B0 | step_ladder | stall_or_run | wick_touch_guard

Every cell keeps the champion's shipped configuration (CAPITAL forced to 100,
single seat, 100% deployment) and the v43/v44 knobs inert, so the ONLY thing
that changes between arms is V45_BRAIN_MODE. Exits are 100% of the position,
always: there is no partial scale-out path in this build.

A 60-day warmup is mandatory. Measured on JAN24, a 21-day warmup returns
+16.6566 and a 14-day +16.5590 against the true +17.4095 -- the boxes are not
drawn yet and the book is simply a different book. Cutting the warmup to buy
runtime would be fabricating the baseline, so it is not done.

USAGE  python3 lab_v45_1month_microscope.py [cell ...]
       python3 lab_v45_1month_microscope.py            # all 8 cells
       python3 lab_v45_1month_microscope.py jan24/b0 jan26/step_ladder
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import strategy_v36_ict_champion as S            # noqa: E402
import lab_v37_anti_fragile as L                  # noqa: E402

HERE = Path(__file__).resolve().parent
RES = HERE / "results"
WINDOWS = {"jan24": ("data/binance_5m_jan24", "2024-01-01", "2024-01-31"),
           "jan26": ("data/binance_5m_jan26", "2026-01-01", "2026-01-31")}
ARMS = ["b0", "step_ladder", "stall_or_run", "wick_touch_guard"]
WARMUP = 60


def load_runs() -> dict:
    f = RES / "lab_v45_runs.json"
    return json.loads(f.read_text()) if f.exists() else {}


def save_runs(d: dict) -> None:
    (RES / "lab_v45_runs.json").write_text(json.dumps(d, indent=1, default=str))


def apply_config(mode: str, slip_bps: float):
    """Shipped champion, capital forced to 100, v43/v44 knobs inert."""
    for k, v in L.SHIPPED.items():
        setattr(S, k, v)
    S.CAPITAL = 100.0
    S.FULL_100_DEPLOY = True
    S.MAX_OPEN_POSITIONS = 1
    # ---- the v43/v44 partial-scale experiments stay OFF: 100% exits only ----
    for k, v in (("V43_POST3R_MODE", "off"), ("V44_PARTIAL_3R_FRAC", 0.0),
                 ("V44_RUNNER_POST3R_MODE", "off"), ("V44_EXIT_BRAIN_MODE", "off")):
        if hasattr(S, k):
            setattr(S, k, v)
    # ---- the one variable ----
    S.V45_BRAIN_MODE = "off" if mode == "b0" else mode
    S.SLIPPAGE_BPS = 0.0
    S.EXIT_SLIPPAGE_BPS = float(slip_bps)
    S.EXIT_SLIP = S.EXIT_SLIPPAGE_BPS / 10000.0


def summarize(run: dict, win: str, mode: str, slip: float) -> dict:
    tr = pd.DataFrame(run["trades"])
    tr["entry_ts"] = pd.to_datetime(tr.entry_time, utc=True, format="mixed")
    tr = tr.sort_values("entry_ts").reset_index(drop=True)
    tr["ym"] = tr.entry_ts.dt.strftime("%Y-%m")
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
    out = {"win": win, "mode": "B0" if mode == "b0" else mode,
           "slip_bps": slip, "n": int(len(tr)),
           "gross": round(float(gross), 2), "fees": round(float(fees), 2),
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
           "reasons": dict(tr.exit_reason.value_counts()),
           "trades": tr[["entry_time", "symbol", "exec_tf", "entry_price",
                         "stop_price", "exit_price", "exit_reason", "qty0",
                         "net_pnl", "R"]].to_dict("records"),
           "counts": {k: v for k, v in (run.get("count") or {}).items()
                      if "v45" in k or "emergency" in k}}
    tr.to_csv(RES / f"trades_v45_{win}_{out['mode']}_{int(slip)}.csv",
              index=False)
    return out


def run_cell(win: str, mode: str, slip: float, force: bool = False) -> dict:
    key = f"{win}/{mode}@{int(slip)}"
    runs = load_runs()
    if key in runs and not force:
        print(f"[skip] {key} already done", flush=True)
        return runs[key]
    dd, a, b = WINDOWS[win]
    apply_config(mode, slip)
    S.V32_DATA_DIR = dd
    t0 = time.time()
    run = S.run_backtest(S.v34_data_dir(), a, b, warmup_days=WARMUP, tag=key)
    el = time.time() - t0
    out = summarize(run, win, mode, slip)
    out["secs"] = round(el, 1)
    runs[key] = out
    save_runs(runs)
    print(f"[done] {key:28s} n={out['n']:3d} net={out['net']:+8.2f} "
          f"pf={out['pf']} dd={out['maxDD']:.1f}% {el:.0f}s", flush=True)
    return out


def main() -> int:
    want = sys.argv[1:]
    cells = []
    # ESSENTIAL SET (user-selected): both windows, B0 + the strongest arm,
    # 0 bps. The 2 bps duplicates and the two weaker brains are dropped.
    for w in ("jan24", "jan26"):
        for m in ("b0", "step_ladder"):
            cells.append((w, m, 0.0))
    if want:
        cells = [c for c in cells
                 if any(f"{c[0]}/{c[1]}" == w or f"{c[0]}/{c[1]}@{int(c[2])}" == w
                        or w == c[0] for w in want)]
    t0 = time.time()
    for w, m, s in cells:
        run_cell(w, m, s)
    print(f"\ntotal {time.time()-t0:.0f}s over {len(cells)} cells")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
