#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_v53_synergy.py -- v53 STAGE 1 (static, ZERO engine runs, <15s)."""
from __future__ import annotations
import json, time
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RES = HERE / "results"
ENG = RES / "v52_engine"
WINS = ("W1", "W2", "OLD7", "MOD_Y1", "MOD_Y2")

def load(arm, w):
    p = ENG / f"{arm}__{w}__0.csv"
    if not p.exists() or p.stat().st_size < 10: return pd.DataFrame()
    d = pd.read_csv(p)
    d["entry_time"] = pd.to_datetime(d.entry_time, utc=True, format="mixed")
    d["exit_time"] = pd.to_datetime(d.exit_time, utc=True, format="mixed")
    d["win"] = w
    return d

def book(arm, wins=WINS):
    parts = [load(arm, w) for w in wins]
    parts = [p for p in parts if len(p)]
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()

def cls(d):
    g = (d.exit_reason == "TARGET_REJECTION") | ((d.exit_reason == "STOP_BLUE") & (d.R >= 3.0))
    return np.where(g, "Golden", np.where(d.exit_reason == "EMERGENCY_STOP", "EM",
           np.where(d.exit_reason.isin(["BREAKEVEN", "SHIELD_BE"]), "BE", "Other")))

def main():
    t0 = time.time()
    out = {}
    m5 = book("m5_kz"); m1 = book("m1_depth"); v51 = book("m5_kz")  # placeholder
    v51p = [RES / "v51_engine" / f"v51_p1_knife__{w}__0.csv" for w in WINS]
    v51 = pd.concat([pd.read_csv(p) for p in v51p], ignore_index=True)
    v51["entry_time"] = pd.to_datetime(v51.entry_time, utc=True, format="mixed")

    # ---- 1A: top m1 winners on MOD_Y2/OLD7 vs what m5 was doing ----------
    rows1a = []
    for w in ("MOD_Y2", "OLD7"):
        a = load("m1_depth", w); b = load("m5_kz", w)
        if not len(a): continue
        for _, r in a.nlargest(10, "net_pnl").iterrows():
            same = b[(b.entry_time == r.entry_time) & (b.symbol == r.symbol)]
            occ = b[(b.entry_time <= r.entry_time) & (b.exit_time >= r.entry_time)]
            rows1a.append({"win": w, "entry": str(r.entry_time), "sym": r.symbol.replace("_5m", ""),
                           "m1_net": round(float(r.net_pnl), 2),
                           "raw_risk_pct": round(float(r.risk_pct), 3) if "risk_pct" in r else None,
                           "m5_same_setup": (f"{same.iloc[0].exit_reason}:{same.iloc[0].net_pnl:+.2f}" if len(same) else "—"),
                           "m5_seat": (f"{occ.iloc[0].symbol.replace('_5m','')} ({occ.iloc[0].exit_reason})" if len(occ) and not len(same) else "free/same")})
    out["1a_top_m1"] = rows1a
    for r in rows1a: print(r)

    # ---- 1B: risk_pct buckets on m5 --------------------------------------
    d = m5.copy()
    d["rp"] = d.risk_pct.astype(float)
    d["cls"] = cls(d)
    edges = [0, .25, .35, .50, .65, .80, 1.00, 1.30, 99]
    labels = ["<0.25", ".25-.35", ".35-.50", ".50-.65", ".65-.80", ".80-1.00", "1.00-1.30", ">1.30"]
    d["bucket"] = pd.cut(d.rp, edges, labels=labels)
    rows = []
    for lab, g in d.groupby("bucket", observed=True):
        pos, neg = g[g.net_pnl > 0].net_pnl.sum(), g[g.net_pnl < 0].net_pnl.sum()
        rows.append({"bucket": str(lab), "n": len(g), "Golden": int((g.cls == "Golden").sum()),
                     "EM": int((g.cls == "EM").sum()), "BE": int((g.cls == "BE").sum()),
                     "Other": int((g.cls == "Other").sum()),
                     "net": round(float(g.net_pnl.sum()), 2),
                     "avg": round(float(g.net_pnl.mean()), 3),
                     "pf": round(float(pos / -neg), 3) if neg < 0 else None,
                     "wr": round(float((g.net_pnl > 0).mean() * 100), 1),
                     "avg_loss": round(float(g[g.net_pnl < 0].net_pnl.mean()), 2) if (g.net_pnl < 0).any() else 0.0})
    out["1b_buckets"] = rows
    print("\n1B m5 risk buckets:"); [print(r) for r in rows]
    caps = {}
    for cap in (0.75, 0.85, 0.95, 1.00, 1.10, 1.25):
        kept = d[d.rp <= cap]
        caps[str(cap)] = {"kept": len(kept), "net_static": round(float(kept.net_pnl.sum()), 2),
                          "removed_net": round(float(d[d.rp > cap].net_pnl.sum()), 2)}
    out["1b_caps_static"] = caps
    print("1B caps:", caps)

    # ---- 1C: DOW/session/symbol on V51 & m5 -------------------------------
    def tab(dd):
        dd = dd.copy(); dd["cls"] = cls(dd)
        dow = dd.groupby(dd.entry_time.dt.day_name().str[:3]).agg(
            n=("net_pnl", "size"), net=("net_pnl", "sum"),
            golden=("cls", lambda s: int((s == "Golden").sum())),
            other=("cls", lambda s: int((s == "Other").sum()))).round(2)
        sym = dd.groupby(dd.symbol.str.replace("_5m", "", regex=False)).agg(
            n=("net_pnl", "size"), net=("net_pnl", "sum")).round(2)
        return {"dow": dow.reset_index().astype(str).values.tolist(),
                "sym": sym.reset_index().astype(str).values.tolist()}
    out["1c_v51"] = tab(v51); out["1c_m5"] = tab(m5)
    print("\n1C V51 dow:", out["1c_v51"]["dow"]); print("1C m5 dow:", out["1c_m5"]["dow"])
    print("1C m5 sym:", out["1c_m5"]["sym"])
    # per-symbol per-window sign (m5)
    neg = {}
    for (sym, w), g in m5.groupby([m5.symbol, m5.win]):
        neg.setdefault(sym.replace("_5m", ""), {})[w] = round(float(g.net_pnl.sum()), 2)
    out["1c_sym_win"] = neg
    print("1C sym x win:", neg)

    (RES / "_v53_stage1.json").write_text(json.dumps(out, indent=1, default=str))
    print(f"\ntotal {time.time()-t0:.1f}s")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
