#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_v57_machine.py -- v57 STAGE 1: streak + stalled-trade forensics.
Tables 1-2 from saved books; Table 3 replays saved 5m data for subsets."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RES = HERE / "results"
DATA = HERE / "data" / "binance_5m"
WINS = ("W1", "W2", "OLD7", "MOD_Y1", "MOD_Y2")

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
    months = pd.period_range(t0 - pd.Timedelta(days=2), t1 + pd.Timedelta(days=2), freq="M")
    frames = []
    for m in months:
        p = DATA / sym / f"{m}.csv.gz"
        if not p.exists(): continue
        if p not in _cache:
            d = pd.read_csv(p)
            d["ts"] = pd.to_datetime(d["Datetime"], utc=True, format="mixed")
            _cache[p] = d[["ts", "Open", "High", "Low", "Close"]].sort_values("ts")
        frames.append(_cache[p])
    if not frames: return pd.DataFrame(columns=["ts", "Open", "High", "Low", "Close"])
    d = pd.concat(frames).drop_duplicates("ts").sort_values("ts")
    return d[(d.ts >= t0 - pd.Timedelta(days=1)) & (d.ts <= t1 + pd.Timedelta(days=2))].reset_index(drop=True)

def streak_forensics(d, label):
    """Walk each window book by exit time."""
    max_strict = max_be_tolerant = 0
    worst_dollar = 0.0; worst_len = 0
    for w in WINS:
        g = d[d.win == w].sort_values("exit_time")
        s1 = s2 = 0; run_dollar = 0.0
        for _, r in g.iterrows():
            R = float(r.R); be = str(r.get("class", "")) == "BE"
            if R < -0.05 and not be:
                s1 += 1; s2 += 1; run_dollar += float(r.net_pnl)
                worst_dollar = min(worst_dollar, run_dollar)
                worst_len = max(worst_len, s2 if run_dollar == worst_dollar else worst_len)
            elif R > 0.05:
                s1 = 0; s2 = 0; run_dollar = 0.0
            elif be:
                s1 = 0  # BE breaks the strict streak, not the tolerant one
        max_strict = max(max_strict, s1); max_be_tolerant = max(max_be_tolerant, s2)
    return {"book": label, "max_consec_losses_strict": max_strict,
            "max_consec_losses_be_tolerant": max_be_tolerant,
            "worst_streak_dollar_in_window": round(worst_dollar, 2)}

def main():
    out = {}
    m5 = book("v52_engine", "m5_kz"); s3 = book("v55_engine", "s3_unfreeze")
    m5["raw_risk"] = m5.entry_price - m5.stop_price

    # ---- Table 1 -----------------------------------------------------------
    out["1_streaks"] = [streak_forensics(m5, "m5_kz"), streak_forensics(s3, "s3_unfreeze")]
    def cat(r):
        rs, cl = str(r.exit_reason), str(r.get("class", ""))
        if rs == "TARGET_REJECTION" or cl == "WIN": return "Golden/WIN (target & trail)"
        if rs == "STRUCT_PROFIT": return "SWING/STRUCT profit"
        if rs in ("BREAKEVEN", "SHIELD_BE") or cl == "BE": return "BREAKEVEN $0.00"
        if rs == "V50_KNIFE_SCRATCH": return "Bar-1 Knife [-0.65x]"
        if rs == "V50_FLOOR_EXEC": return "P1 floor guard [-0.25x]"
        if rs == "EMERGENCY_STOP": return "EMERGENCY_STOP"
        if rs == "STOP_BLUE": return "STOP_BLUE (full/structural stop)"
        return rs
    m5["cat"] = m5.apply(cat, axis=1)
    rows = []
    for c, g in m5.groupby("cat"):
        rows.append({"type": c, "n": len(g), "pct": round(len(g) / len(m5) * 100, 1),
                     "avg_usd": round(float(g.net_pnl.mean()), 2), "total_usd": round(float(g.net_pnl.sum()), 2)})
    out["1_exit_mix_m5"] = sorted(rows, key=lambda x: -x["n"])
    print("T1 streaks", out["1_streaks"]); [print(r) for r in out["1_exit_mix_m5"]]

    # ---- Table 2: s3 defense activations in W1 / MOD_Y2 --------------------
    t2 = {}
    for w in ("W1", "MOD_Y2"):
        g = s3[s3.win == w].sort_values("exit_time")
        st = 0; act = 0; scratch_caused = real_caused = 0
        frozen = []; fstart = None
        for _, r in g.iterrows():
            R = float(r.R); be = str(r.get("class", "")) == "BE"
            if (not be) and R < -0.05:
                st += 1
                if st == 2:
                    act += 1; fstart = r.exit_time
                    if R <= -0.50: real_caused += 1
                    else: scratch_caused += 1
            elif R > 0.05 or be:
                if fstart is not None: frozen.append((fstart, r.exit_time))
                st = 0; fstart = None
        if fstart is not None and len(g): frozen.append((fstart, g.exit_time.max()))
        mw = m5[m5.win == w]
        missed = 0; missed_usd = 0.0
        keys = set(zip(s3[s3.win == w].symbol, s3[s3.win == w].entry_time))
        for _, r in mw.iterrows():
            if (r.symbol, r.entry_time) in keys: continue
            if any(a <= r.entry_time <= b for a, b in frozen) and float(r.net_pnl) > 0:
                missed += 1; missed_usd += float(r.net_pnl)
        t2[w] = {"activations": act, "by_scratch_-0.35..-0.05": scratch_caused,
                 "by_real_loss_<=-0.50": real_caused, "m5_winners_missed_while_frozen": missed,
                 "missed_usd": round(missed_usd, 2)}
    out["2_s3_defense"] = t2
    print("T2", t2)

    # ---- Table 3: golden vs stalled BE -------------------------------------
    gold = m5[(m5.exit_reason == "TARGET_REJECTION") | ((m5.exit_reason == "STOP_BLUE") & (m5.R >= 3.0))]
    be15 = m5[(m5["class"] == "BE") & (m5.mfe_R >= 1.5)]
    def path_stats(df):
        bars_16_to_25 = []; stall = {12: 0, 18: 0, 24: 0}; milk_usd = 0.0; n_stall_eval = 0
        for _, r in df.iterrows():
            b = bars5(r.symbol, r.entry_time, r.exit_time)
            b = b[(b.ts >= r.entry_time) & (b.ts <= r.exit_time)].reset_index(drop=True)
            if len(b) < 5 or r.raw_risk <= 0: continue
            R = r.raw_risk; e = r.entry_price
            hR = (b.High - e) / R
            i16 = b.index[hR >= 1.6]
            if not len(i16): continue
            i16 = int(i16[0])
            i25 = b.index[hR >= 2.5]
            i25 = int(i25[0]) if len(i25) else None
            if i25 is not None: bars_16_to_25.append(i25 - i16)
            for T in (12, 18, 24):
                j = i16 + T
                if i25 is None or i25 > j:
                    if j < len(b):
                        stall[T] += 1
                        if T == 18:
                            n_stall_eval += 1
                            sl = float(b.Low.iloc[max(0, j - 2):j + 1].min())
                            slR = (sl - e) / R
                            if 0.80 <= slR <= 2.40:
                                milk_usd += max(0.0, (sl * (1 - 0.001) - e * (1 + 0.001)) * float(r.qty0))
        return {"n": len(df), "median_bars_1.6_to_2.5": (float(np.median(bars_16_to_25)) if bars_16_to_25 else None),
                "reached_2.5": len(bars_16_to_25), "stalled_gt_12/18/24_bars": stall,
                "hypothetical_milk_usd_at_18bar_sl": round(milk_usd, 2), "stall18_evaluated": n_stall_eval}
    out["3_golden"] = path_stats(gold)
    out["3_be_mfe15"] = path_stats(be15)
    print("T3 golden", out["3_golden"]); print("T3 be>=1.5", out["3_be_mfe15"])

    (RES / "_v57_stage1.json").write_text(json.dumps(out, indent=1, default=str))
    print("saved")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
