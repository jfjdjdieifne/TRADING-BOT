#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_v54_micro_and_avax.py -- v54 STAGE 1 (static, ZERO engine runs)."""
from __future__ import annotations
import json, time
from pathlib import Path
import numpy as np
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

def main():
    t0 = time.time()
    out = {}
    m5 = book("v52_engine", "m5_kz")
    m1 = book("v52_engine", "m1_depth")
    print(f"m5 book {len(m5)} net {m5.net_pnl.sum():+.2f}")

    # ---- 1.1 micro vs >=0.35 per window + golden anatomy ------------------
    rows = []
    for w in WINS:
        d = m5[m5.win == w]
        for lab, g in (("<0.35", d[d.risk_pct < 0.35]), (">=0.35", d[d.risk_pct >= 0.35])):
            rows.append({"win": w, "band": lab, "n": len(g), "net": round(float(g.net_pnl.sum()), 2)})
    out["1.1_window_bands"] = rows
    print("1.1", rows)
    edges = [(0, .25), (.25, .35), (.35, .50), (.50, .65), (.65, .80), (.80, 1.00), (1.00, 99)]
    grows = []
    for lo, hi in edges:
        g = m5[is_gold(m5) & (m5.risk_pct >= lo) & (m5.risk_pct < hi)]
        if not len(g): continue
        grows.append({"bucket": f"{lo}-{hi}", "golden_n": len(g),
                      "golden_total": round(float(g.net_pnl.sum()), 2),
                      "golden_avg": round(float(g.net_pnl.mean()), 2),
                      "golden_median": round(float(g.net_pnl.median()), 2),
                      "avg_move_pct": round(float(((g.exit_price - g.entry_price) / g.entry_price * 100).mean()), 3),
                      "at_floorline": int((g.exit_reason.isin(["LOCK_FLOOR_STOP", "FLOOR_5M", "STOP_BLUE"])).sum())})
    out["1.1_golden_buckets"] = grows
    print("1.1 golden", grows)
    oth = m5[(m5.risk_pct < 0.35) & ~is_gold(m5)]
    oth = oth[~oth.exit_reason.isin(["BREAKEVEN", "SHIELD_BE"]) & ~(oth.exit_reason == "EMERGENCY_STOP")]
    out["1.1_other_lt035_reasons"] = {str(k): int(v) for k, v in oth.exit_reason.value_counts().items()}
    out["1.1_other_lt035_exit_above_entry"] = int((oth.exit_price >= oth.entry_price).sum())
    out["1.1_other_lt035_n"] = len(oth)
    print("1.1 other<0.35 reasons", out["1.1_other_lt035_reasons"], "exit>=entry", out["1.1_other_lt035_exit_above_entry"], "n", len(oth))

    # ---- 1.2 symbol matrix + seat occupation ------------------------------
    srows = []
    gold = m5[is_gold(m5)]
    for sym, g in m5.groupby("symbol"):
        pos, neg = g[g.net_pnl > 0].net_pnl.sum(), g[g.net_pnl < 0].net_pnl.sum()
        occ = 0
        for _, gt in gold[gold.symbol != sym].iterrows():
            if ((g.entry_time <= gt.entry_time) & (g.exit_time >= gt.entry_time)).any(): occ += 1
        r = {"sym": sym.replace("_5m", ""), "n": len(g), "net": round(float(g.net_pnl.sum()), 2),
             "per": round(float(g.net_pnl.mean()), 3),
             "pf": round(float(pos / -neg), 3) if neg < 0 else None,
             "wr": round(float((g.net_pnl > 0).mean() * 100), 1), "seat_blocked_golden_elsewhere": occ}
        for w in WINS:
            r[w] = round(float(g[g.win == w].net_pnl.sum()), 2)
        srows.append(r)
    out["1.2_symbols"] = srows
    print("1.2"); [print(r) for r in srows]

    # ---- 1.3 Sep-2026 m5 vs m1 + portfolio streak at entry ----------------
    cols = ["entry_time", "exit_time", "symbol", "entry_price", "stop_price", "exit_price", "risk_pct", "net_pnl", "exit_reason"]
    sep = {}
    for arm, d in (("m5", m5), ("m1", m1)):
        s = d[d.entry_time.dt.strftime("%Y-%m") == "2026-09"].sort_values("entry_time")
        sep[arm] = s[cols].astype(str).values.tolist()
    out["1.3_sep2026"] = sep
    print(f"1.3 sep2026 m5 n={len(sep['m5'])} net={m5[m5.entry_time.dt.strftime('%Y-%m')=='2026-09'].net_pnl.sum():+.2f} | m1 n={len(sep['m1'])} net={m1[m1.entry_time.dt.strftime('%Y-%m')=='2026-09'].net_pnl.sum():+.2f}")
    # portfolio streak: walk each window book chronologically
    streak_rows = {}
    for w in WINS:
        d = m5[m5.win == w].sort_values("entry_time")
        st = 0
        for _, r in d.iterrows():
            k = min(st, 4)
            a = streak_rows.setdefault(k, [0, 0.0]); a[0] += 1; a[1] += float(r.net_pnl)
            is_be = r.exit_reason in ("BREAKEVEN", "SHIELD_BE")
            if not is_be and r.R < -0.05: st += 1
            elif r.R > 0.05: st = 0
    out["1.3_streak_at_entry"] = {str(k): {"n": v[0], "net": round(v[1], 2)} for k, v in sorted(streak_rows.items())}
    print("1.3 streak", out["1.3_streak_at_entry"])

    (RES / "_v54_stage1.json").write_text(json.dumps(out, indent=1, default=str))
    print(f"total {time.time()-t0:.1f}s")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
