#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_v55_fast.py -- v55 STAGE 1: static read of v54_engine books only."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
RES = HERE / "results"
WINS = ("W1", "W2", "OLD7", "MOD_Y1", "MOD_Y2")

def load(eng, arm, w):
    p = RES / eng / f"{arm}__{w}__0.csv"
    if not p.exists() or p.stat().st_size < 10: return pd.DataFrame()
    d = pd.read_csv(p)
    d["entry_time"] = pd.to_datetime(d.entry_time, utc=True, format="mixed")
    d["exit_time"] = pd.to_datetime(d.exit_time, utc=True, format="mixed")
    d["win"] = w
    return d

def book(eng, arm):
    return pd.concat([load(eng, arm, w) for w in WINS], ignore_index=True)

def is_gold(d):
    return (d.exit_reason == "TARGET_REJECTION") | ((d.exit_reason == "STOP_BLUE") & (d.R >= 3.0))

def is_be_row(r):
    return str(r.get("class", "")) == "BE" or str(r.exit_reason) in ("BREAKEVEN", "SHIELD_BE")

def main():
    out = {}
    m5 = book("v52_engine", "m5_kz")
    b1 = book("v54_engine", "b1_mfloor")
    b5 = book("v54_engine", "b5_streak")

    # ---- 1.1 month-by-month ----------------------------------------------
    def monthly(d):
        return d.assign(ym=d.entry_time.dt.strftime("%Y-%m")).groupby("ym").net_pnl.sum()
    mm5, mb1, mb5 = monthly(m5), monthly(b1), monthly(b5)
    months = sorted(set(mm5.index) | set(mb1.index) | set(mb5.index))
    rows = []
    for m in months:
        a, b, c = float(mm5.get(m, 0)), float(mb1.get(m, 0)), float(mb5.get(m, 0))
        rows.append({"month": m, "m5": round(a, 2), "b1": round(b, 2),
                     "b5": round(c, 2), "delta_b5_m5": round(c - a, 2)})
    out["1.1_months"] = rows
    ex = [r for r in rows if r["month"] != "2024-11"]
    out["1.1_b5_vs_m5_ex_2024_11"] = {
        "b5_wins_months": int(sum(1 for r in ex if r["delta_b5_m5"] > 0)),
        "of": len(ex), "sum_delta_ex_nov24": round(sum(r["delta_b5_m5"] for r in ex), 2)}
    # excluding W1 window entirely: use window books, drop W1 rows
    m5nw = m5[m5.win != "W1"]; b5nw = b5[b5.win != "W1"]
    out["1.1_excl_W1_and_2024_11_note"] = (
        f"excl W1 window: m5 {m5nw.net_pnl.sum():+.2f} vs b5 {b5nw.net_pnl.sum():+.2f}")
    print("1.1 months:")
    for r in rows: print(r)
    print(out["1.1_b5_vs_m5_ex_2024_11"], out["1.1_excl_W1_and_2024_11_note"])

    # ---- 1.2 frozen-streak forensics --------------------------------------
    # replay b5 streak per window (v54 rule: loss & not BE -> +1; R>0.05 -> 0)
    frozen = {}   # win -> list of (start_ts, end_ts) frozen intervals + BE count inside
    for w in WINS:
        d = b5[b5.win == w].sort_values("entry_time")
        st = 0; start = None; ivs = []
        be_frozen = 0
        events = []
        for _, r in d.iterrows():
            events.append((r.exit_time, r))
        for ts, r in sorted(events, key=lambda x: x[0]):
            if st >= 2 and is_be_row(r): be_frozen += 1
            if (not is_be_row(r)) and float(r.R) < -0.05:
                st += 1
                if st == 2 and start is None: start = ts
            elif float(r.R) > 0.05:
                if start is not None: ivs.append((start, ts))
                st = 0; start = None
        if start is not None: ivs.append((start, d.exit_time.max() if len(d) else start))
        frozen[w] = {"intervals": [(str(a), str(b)) for a, b in ivs],
                     "be_while_frozen": be_frozen}
    out["1.2_frozen"] = frozen
    print("1.2 frozen:", {k: (len(v["intervals"]), v["be_while_frozen"]) for k, v in frozen.items()})

    def frozen_hours(win, ts):
        # hours into the CURRENT frozen spell at ts (0 = not frozen then)
        for a, b in frozen[win]["intervals"]:
            a, b = pd.Timestamp(a), pd.Timestamp(b)
            if a <= ts <= b: return round((ts - a).total_seconds() / 3600, 1)
        return 0.0

    missed = []
    for w, sub in (("W1", m5[m5.win == "W1"]), ("MOD_Y1", m5[(m5.win == "MOD_Y1") & (m5.entry_time.dt.strftime("%Y-%m") == "2024-11")])):
        g = sub[is_gold(sub)]
        b5w = b5[b5.win == w]
        keys = set(zip(b5w.symbol, b5w.entry_time))
        for _, r in g.iterrows():
            if (r.symbol, r.entry_time) in keys: continue
            missed.append({"win": w, "entry": str(r.entry_time), "sym": str(r.symbol),
                           "m5_net": round(float(r.net_pnl), 2),
                           "frozen_hours_before": frozen_hours(w, r.entry_time),
                           "nar_flow_4h": str(r.get("nar_flow_4h", "")),
                           "nar_flow_1h": str(r.get("nar_flow_1h", ""))})
    out["1.2_missed_golden"] = missed
    print(f"1.2 missed golden ({len(missed)}):")
    for r in missed: print(r)

    (RES / "_v55_stage1.json").write_text(json.dumps(out, indent=1, default=str))
    print("saved results/_v55_stage1.json")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
