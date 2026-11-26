#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_v51_slippage_forensics.py -- <5s forensic diff of the v50 @2bps
non-causal seat-shift + TRUE CAUSAL 2/4bps exit-slippage on saved books.

Causal model: the trade SEQUENCE (entries, exit bars, reasons) is frozen
from the saved 0bps book. Only the exit fill worsens:
    exit_px' = exit_px*(1-slip);  dNet = -slip*exit_px*qty0*(1-COST)
applied to every market sell (all reasons except END_OF_DATA), then cash
compounds forward: each later trade's $ size scales by cash'/cash at entry.
"""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
RES = HERE / "results"
WINS = ("W1", "W2", "OLD7", "MOD_Y1", "MOD_Y2")
COST = 0.001

BOOKS = {
    "B0":   lambda w: RES / f"trades_v37_B0_{w}.csv",
    "C4":   lambda w: RES / "v49_engine" / f"c4_exec_m030__{w}__0.csv",
    "P1":   lambda w: RES / "v50_engine" / f"p1_c4_m025__{w}__0.csv",
    "P3":   lambda w: RES / "v50_engine" / f"p3_c4_m035__{w}__0.csv",
    "S3":   lambda w: RES / "v50_engine" / f"s3_knife__{w}__0.csv",
    "V51":  lambda w: RES / "v51_engine" / f"v51_p1_knife__{w}__0.csv",
}
BUGGY = {  # engine EXIT_SLIP books produced in v50
    "B0@eng2": lambda w: RES / "v50_engine" / f"B0__{w}__2.csv",
    "C4@eng2": lambda w: RES / "v50_engine" / f"p2_c4_m030__{w}__2.csv",
    "S3@eng2": lambda w: RES / "v50_engine" / f"s3_knife__{w}__2.csv",
}

def load(p):
    d = pd.read_csv(p)
    d["entry_time"] = pd.to_datetime(d.entry_time, utc=True, format="mixed")
    d["exit_time"] = pd.to_datetime(d.exit_time, utc=True, format="mixed")
    return d.sort_values("entry_time").reset_index(drop=True)

def causal(d: pd.DataFrame, slip_bps: float) -> float:
    slip = slip_bps * 1e-4
    cash0 = cash = 100.0
    for _, t in d.iterrows():
        scale = cash / cash0 if cash0 > 0 else 0.0
        net = float(t.net_pnl) * scale
        if slip > 0 and str(t.exit_reason) != "END_OF_DATA":
            net -= slip * float(t.exit_price) * float(t.qty0) * (1 - COST) * scale
        cash += net
        cash0 += float(t.net_pnl)
    return round(cash - 100.0, 2)

def keyset(d):
    return set(zip(d.entry_time.astype(str), d.symbol, d.exit_time.astype(str)))

def main():
    out = {"causal": {}, "buggy_engine_2bps": {}, "diffs": {}}
    # ---- 1. code lines -------------------------------------------------
    src = (HERE / "strategy_v36_ict_champion.py").read_text().splitlines()
    lines = {}
    for i, ln in enumerate(src, 1):
        if "px = px * (1.0 - EXIT_SLIP)" in ln: lines["slip_apply"] = (i, ln.strip())
        if "self._v35_note_exit(bool(is_win), time)" in ln: lines["streak_feed"] = (i, ln.strip())
        if 'self.pool["cash"] += px * self.qty - exit_fee' in ln: lines["cash_feed"] = (i, ln.strip())
        if "is_win = net > 0" in ln: lines["is_win"] = (i, ln.strip())
    lab = (HERE / "lab_v50_tournament.py").read_text().splitlines()
    for i, ln in enumerate(lab, 1):
        if "S.EXIT_SLIPPAGE_BPS = float(bps)" in ln: lines["lab_set"] = (i, ln.strip())
    out["code_lines"] = {k: {"line": v[0], "text": v[1]} for k, v in lines.items()}
    print("CODE:", json.dumps(out["code_lines"], indent=1))

    # ---- 2. CSV diffs 0 vs engine-2 ------------------------------------
    for (arm0, arm2) in (("B0", "B0@eng2"), ("C4", "C4@eng2")):
        for w in ("W1", "OLD7"):
            a = load(BOOKS[arm0](w)); b = load(BUGGY[arm2](w))
            ka, kb = keyset(a), keyset(b)
            only_a = a[[(e, s, x) in ka - kb for e, s, x in zip(a.entry_time.astype(str), a.symbol, a.exit_time.astype(str))]]
            only_b = b[[(e, s, x) in kb - ka for e, s, x in zip(b.entry_time.astype(str), b.symbol, b.exit_time.astype(str))]]
            rec = {"n0": len(a), "n2": len(b), "net0": round(a.net_pnl.sum(), 2),
                   "net2": round(b.net_pnl.sum(), 2),
                   "only_in_0": only_a[["entry_time", "symbol", "exit_reason", "net_pnl"]].astype(str).values.tolist()[:12],
                   "only_in_2": only_b[["entry_time", "symbol", "exit_reason", "net_pnl"]].astype(str).values.tolist()[:12],
                   "top0": a.loc[a.net_pnl.idxmax(), ["entry_time", "symbol", "net_pnl"]].astype(str).tolist(),
                   "top2": b.loc[b.net_pnl.idxmax(), ["entry_time", "symbol", "net_pnl"]].astype(str).tolist()}
            out["diffs"][f"{arm0}:{w}"] = rec
            print(f"\nDIFF {arm0} {w}: n {len(a)}->{len(b)} net {rec['net0']:+.2f}->{rec['net2']:+.2f}")
            print(" only@0:", rec["only_in_0"][:6])
            print(" only@2:", rec["only_in_2"][:6])
            print(" top:", rec["top0"], "->", rec["top2"])

    # ---- 3. causal table ----------------------------------------------
    for arm, fn in list(BOOKS.items()):
        if not all(fn(w).exists() for w in WINS):
            print(f"[wait] {arm} book incomplete"); continue
        row = {}
        for w in WINS:
            d = load(fn(w))
            row[w] = {"n": len(d), "bps0": round(float(d.net_pnl.sum()), 2),
                      "causal2": causal(d, 2), "causal4": causal(d, 4)}
        row["TOTAL"] = {k: round(sum(row[w][k] for w in WINS), 2) for k in ("bps0", "causal2", "causal4")}
        out["causal"][arm] = row
    for arm, fn in BUGGY.items():
        if all(fn(w).exists() for w in WINS):
            out["buggy_engine_2bps"][arm] = round(sum(float(load(fn(w)).net_pnl.sum()) for w in WINS), 2)
    (RES / "_v51_causal.json").write_text(json.dumps(out, indent=1, default=str))
    print("\nCAUSAL TOTALS:", {a: r["TOTAL"] for a, r in out["causal"].items()})
    print("BUGGY ENGINE @2 TOTALS:", out["buggy_engine_2bps"])
    return out

if __name__ == "__main__":
    main()
