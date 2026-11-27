#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_v56_milk_forensics.py -- v56 STAGE 1.
1.1 from saved mfe_R; 1.2/1.3 by causal replay of saved 5m data for the
golden / cents subsets only (fast, no engine runs)."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RES = HERE / "results"
DATA = HERE / "data" / "binance_5m"
WINS = ("W1", "W2", "OLD7", "MOD_Y1", "MOD_Y2")
COST = 0.001

def book(eng, arm):
    out = []
    for w in WINS:
        p = RES / eng / f"{arm}__{w}__0.csv"
        if not p.exists(): continue
        d = pd.read_csv(p)
        d["entry_time"] = pd.to_datetime(d.entry_time, utc=True, format="mixed")
        d["exit_time"] = pd.to_datetime(d.exit_time, utc=True, format="mixed")
        d["win"] = w; out.append(d)
    return pd.concat(out, ignore_index=True)

_cache = {}
def bars5(sym, t0, t1):
    """5m bars of sym between t0-1d and t1+1d from monthly gz files."""
    key = (sym, str(t0)[:7], str(t1)[:7])
    months = pd.period_range(t0 - pd.Timedelta(days=2), t1 + pd.Timedelta(days=2), freq="M")
    frames = []
    for m in months:
        p = DATA / sym / f"{m}.csv.gz"
        if not p.exists(): continue
        if p not in _cache:
            d = pd.read_csv(p)
            tcol = [c for c in d.columns if "time" in c.lower() or c.lower() in ("timestamp", "date")][0]
            d["ts"] = pd.to_datetime(d[tcol], utc=True, format="mixed")
            ren = {c: c.capitalize() for c in d.columns
                   if c.capitalize() in ("Open", "High", "Low", "Close")}
            d = d.rename(columns=ren)
            _cache[p] = d[["ts", "Open", "High", "Low", "Close"]].sort_values("ts")
        frames.append(_cache[p])
    if not frames: return pd.DataFrame(columns=["ts", "Open", "High", "Low", "Close"])
    d = pd.concat(frames).drop_duplicates("ts").sort_values("ts")
    return d[(d.ts >= t0 - pd.Timedelta(days=1)) & (d.ts <= t1 + pd.Timedelta(days=2))].reset_index(drop=True)

def main():
    out = {}
    m5 = book("v52_engine", "m5_kz")
    m5["raw_risk"] = m5.entry_price - m5.stop_price
    be = m5[m5["class"] == "BE"].copy()
    print(f"BE n={len(be)}")

    # ---- 1.1 MFE distribution of BE trades --------------------------------
    rows = []
    for lo, hi in ((1.0, 1.5), (1.5, 2.0), (2.0, 2.5), (2.5, 3.0)):
        g = be[(be.mfe_R >= lo) & (be.mfe_R < hi)]
        # $ left on table: peak gross at mfe_R minus what was banked (~0 net),
        # valued on the trade's own sizing, minus round-trip cost drag 0.2%
        left = float((g.mfe_R * g.raw_risk * g.qty0 * (1 - 2 * COST)).sum())
        rows.append({"bucket": f"{lo}-{hi}R", "n": len(g),
                     "avg_max_profit": round(float((g.mfe_R * g.raw_risk * g.qty0).mean()), 2) if len(g) else 0.0,
                     "left_on_table": round(left, 2)})
    out["1.1_be_mfe"] = rows
    for th in (1.8, 2.0, 2.2):
        g = be[be.mfe_R >= th]
        left = float((g.mfe_R * g.raw_risk * g.qty0 * (1 - 2 * COST)).sum())
        out[f"1.1_ge_{th}R"] = {"n": len(g), "left_on_table": round(left, 2)}
    print("1.1", rows, {k: v for k, v in out.items() if k.startswith("1.1_ge")})

    # ---- 1.2 golden: min 15m close after first +2R touch ------------------
    gold = m5[(m5.exit_reason == "TARGET_REJECTION") | ((m5.exit_reason == "STOP_BLUE") & (m5.R >= 3.0))].copy()
    mins = []
    for _, r in gold.iterrows():
        b = bars5(r.symbol, r.entry_time, r.exit_time)
        if not len(b): continue
        b = b[(b.ts >= r.entry_time) & (b.ts <= r.exit_time)]
        if not len(b): continue
        R = r.raw_risk
        if R <= 0: continue
        lvl2, lvl3 = r.entry_price + 2 * R, r.entry_price + 3 * R
        hit2 = b.index[b.High >= lvl2]
        if not len(hit2): continue
        i2 = hit2[0]
        seg = b.loc[i2:]
        hit3 = seg.index[seg.High >= lvl3]
        i3 = hit3[0] if len(hit3) else seg.index[-1]
        seg = seg.loc[:i3]
        c15 = seg.set_index("ts").Close.resample("15min").last().dropna()
        if not len(c15): continue
        mins.append(float(((c15 - r.entry_price) / R).min()))
    mins = np.array(mins)
    out["1.2_golden"] = {"n_analysed": len(mins),
                         "never_15m_close_below_1.2R_pct": round(float((mins >= 1.2).mean() * 100), 1) if len(mins) else None,
                         "never_15m_close_below_1.4R_pct": round(float((mins >= 1.4).mean() * 100), 1) if len(mins) else None,
                         "min_close_R_p10": round(float(np.percentile(mins, 10)), 2) if len(mins) else None,
                         "min_close_R_median": round(float(np.median(mins)), 2) if len(mins) else None}
    print("1.2", out["1.2_golden"])

    # ---- 1.3 cents exits at +3R: 12h forward -------------------------------
    cents = m5[(m5.net_pnl < 1.0) & (m5.R >= 2.9)].copy()
    fwd = []
    for _, r in cents.iterrows():
        b = bars5(r.symbol, r.exit_time, r.exit_time + pd.Timedelta(hours=12))
        b = b[(b.ts > r.exit_time) & (b.ts <= r.exit_time + pd.Timedelta(hours=12))]
        if not len(b): continue
        fwd.append({"sym": str(r.symbol), "exit": str(r.exit_time), "net": round(float(r.net_pnl), 2),
                    "risk_pct": round(float(r.risk_pct), 3),
                    "fwd12h_max_pct": round(float((b.High.max() / r.exit_price - 1) * 100), 2),
                    "fwd12h_close_pct": round(float((b.Close.iloc[-1] / r.exit_price - 1) * 100), 2)})
    out["1.3_cents"] = {"n_lt1_at_3R": len(cents), "n_risk_lt035": int((cents.risk_pct < 0.35).sum()), "rows": fwd}
    print("1.3", out["1.3_cents"])

    (RES / "_v56_stage1.json").write_text(json.dumps(out, indent=1, default=str))
    print("saved")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
