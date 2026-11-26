#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_v52_ict_arsenal.py -- v52 STAGE 1 (static, ZERO engine runs).
5 ICT pillars on the saved B0 43-month book (1,173 trades) + 5m archive.
All numbers are STATIC ceilings: seat reallocation is the engine's job.
"""
from __future__ import annotations
import json, time
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
import sys; sys.path.insert(0, str(HERE))
import audit_v45_true_multiple_brain as A

RES = HERE / "results"
COST = A.COST
DEPTHS = [0.15, 0.25, 0.35, 0.50, 0.618, 0.705]
NS5 = 5 * 60 * 10**9

def cls(r):
    return "Golden" if r.golden else "EM" if r.em else "BE" if r.be else "Other"

def main():
    t0 = time.time()
    t = A.load_tape()
    data = {s: A.load_5m(s) for s in A.SYMS}
    t = A.measure(t, data)
    print(f"book {len(t)} net {t.net_pnl.sum():+.2f} ({time.time()-t0:.1f}s)")
    out = {}

    # ---------- Pillar 1: depth -------------------------------------------
    rows = []
    for d in DEPTHS:
        filled = golden_dip = be_dip = be_to_gold = 0
        net_d = 0.0
        for r in t.itertuples(index=False):
            D = data[r.symbol]
            i0, i1 = A.slice_bars(D, r.entry_ns, r.exit_ns)
            if i1 <= i0: continue
            px_d = r.fill - d * (r.fill - r.stop)
            lows = D["l"][i0:i1]
            hit = bool((lows <= px_d).any())
            if cls(r) == "Golden" and hit: golden_dip += 1
            if cls(r) == "BE":
                if hit:
                    be_dip += 1
                    r_new = px_d - r.stop
                    if r_new > 0 and (r.max_5m_high - px_d) / r_new >= 3.0:
                        be_to_gold += 1
            if hit:
                filled += 1
                net_d += r.net_pnl + (r.fill - px_d) * r.qty
            else:
                net_d += 0.0  # no fill, no trade (cash idle, static ceiling ignores seat reuse)
        rows.append({"d": d, "filled": filled, "golden_dipped": golden_dip,
                     "be_dipped": be_dip, "be_becomes_3R": be_to_gold,
                     "static_net_filled_only": round(net_d, 2)})
        print(f"P1 d={d:<6} filled={filled:4d} goldenDip={golden_dip:3d}/110 "
              f"beDip={be_dip:3d}/452 be->3R={be_to_gold:3d} staticNetFilled={net_d:+.2f}")
    out["pillar1_depth"] = rows

    # ---------- Pillar 2: CISD after tap ----------------------------------
    stat = {}
    cisd_net = cisd_n = 0
    for r in t.itertuples(index=False):
        D = data[r.symbol]
        i0 = int(np.searchsorted(D["ns"], r.entry_ns, "left"))
        seg = slice(i0, min(i0 + 7, len(D["ns"])))
        o, h, l, c = D["o"][seg], D["h"][seg], D["l"][seg], D["c"][seg]
        ok = False
        for k in range(1, len(c)):
            if l[k] > r.stop and (c[k] > o[k] or c[k] > h[k-1]):
                ok = True; break
        cc = cls(r)
        s = stat.setdefault(cc, [0, 0]); s[1] += 1; s[0] += int(ok)
        if ok:
            cisd_n += 1; cisd_net += r.net_pnl
    out["pillar2_cisd"] = {k: {"cisd": v[0], "n": v[1], "pct": round(100*v[0]/max(v[1],1),1)} for k, v in stat.items()}
    print("P2 CISD<=6bars:", out["pillar2_cisd"], f"book-net of CISD trades (unfiltered outcome) {cisd_net:+.2f} n={cisd_n}")

    # ---------- Pillar 3: DOL / PDH + bearish CISD bank -------------------
    be_reach = em_reach = gold_reach = 0
    bank_gain = 0.0
    for r in t.itertuples(index=False):
        D = data[r.symbol]
        day0 = (r.entry_ns // (24*3600*10**9)) * (24*3600*10**9)
        j0 = int(np.searchsorted(D["ns"], day0 - 24*3600*10**9, "left"))
        j1 = int(np.searchsorted(D["ns"], day0, "left"))
        pdh = float(D["h"][j0:j1].max()) if j1 > j0 else np.inf
        reached = (r.max_5m_high >= pdh) or (r.X_5m_high >= 2.0)
        if not reached: continue
        if cls(r) == "BE": be_reach += 1
        elif cls(r) == "EM": em_reach += 1
        elif cls(r) == "Golden": gold_reach += 1
        if cls(r) in ("BE", "EM"):
            bank_gain += 2.0 * abs(r.unit_loss) * r.qty - r.net_pnl
    out["pillar3_dol"] = {"BE_reached_PDH_or_2x": be_reach, "EM_reached": em_reach,
                          "Golden_reached": gold_reach,
                          "static_bank_at_+2R_gain_vs_actual_BE_EM": round(bank_gain, 2)}
    print("P3 DOL:", out["pillar3_dol"])

    # ---------- Pillar 4: SMT (4h lookback vs BTC/ETH) --------------------
    def swept(sym, ns, lb=48):
        D = data[sym]; i = int(np.searchsorted(D["ns"], ns, "left"))
        if i < lb or i >= len(D["ns"]): return None
        return bool(D["l"][i] <= D["l"][i-lb:i].min() + 1e-12)
    smt_stat = {}
    for r in t.itertuples(index=False):
        b = swept("BTCUSDT_5m", r.entry_ns); e = swept("ETHUSDT_5m", r.entry_ns)
        own = swept(r.symbol, r.entry_ns)
        if b is None or own is None: continue
        smt = bool(own != b or (e is not None and own != e))
        s = smt_stat.setdefault((cls(r), smt), [0, 0.0]); s[0] += 1; s[1] += r.net_pnl
    out["pillar4_smt"] = {f"{k[0]}|SMT={k[1]}": {"n": v[0], "net": round(v[1],2)} for k, v in sorted(smt_stat.items(), key=lambda x: str(x[0]))}
    print("P4 SMT:", out["pillar4_smt"])

    # ---------- Pillar 5: Killzones / DOW / Judas --------------------------
    def zone(h):
        return ("Asia 00-06" if h < 7 else "LondonKZ 07-10" if h < 10 else
                "Lunch 10-12" if h < 12 else "NYKZ 12-16" if h < 16 else
                "SilverBullet 18-20" if 18 <= h < 20 else "Dead 20-24/16-18")
    t["kz"] = [zone(h) for h in t.entry_ts.dt.hour]
    t["dow"] = t.entry_ts.dt.day_name().str[:3]
    kz = t.groupby("kz").agg(n=("net_pnl", "size"), net=("net_pnl", "sum")).round(2)
    dow = t.groupby("dow").agg(n=("net_pnl", "size"), net=("net_pnl", "sum")).round(2)
    out["pillar5_kz"] = kz.reset_index().astype(str).values.tolist()
    out["pillar5_dow"] = dow.reset_index().astype(str).values.tolist()
    print("P5 KZ:\n", kz); print("P5 DOW:\n", dow)

    (RES / "_v52_stage1.json").write_text(json.dumps(out, indent=1, default=str))
    print(f"total {time.time()-t0:.1f}s")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
