#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_v24_shield.py — EXACT counterfactual bar-walk for the v25 shield.

For every v24 trade it replays the trade's own exec-frame path bar by
bar — EXTENDED past v24's actual exit, because v24's entry-tick
breakeven choke killed 50 trades before their story could develop —
and answers with real prices:

  "If the breakeven shield had been armed by rule X, and ONLY by a real
   displacement event (never at the entry tick), how many of the 144
   losses become scratches, how many choked trades come back as wins,
   and what happens to the win rate?"

Event priority inside each bar (conservative, zero-lookahead):
  1. an armed BE stop is intrabar and sits above the structural stop,
     so it is hit first
  2. the +3R lock engages on a CLOSE (end of bar) -> from there the
     trade can never book less than +3.00R net
  3. the structural stop is intrabar
Arming itself happens on a bar's CLOSE, so the BE stop only lives from
the NEXT bar onward.

Arm rules (all user-sanctioned ICT events, no invented numbers):
  A_k  : first CLOSE >= entry + k*R              (displacement in R)
  MID  : first CLOSE above the 4H PurpleBox.mid  (50% — sanctioned)
  BOS  : first CLOSE above the nearest internal RedBox live at entry
         (post-entry bullish break of structure)
  MID+BOS, MID+A1, BOS+A1 : conjunctions
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import strategy_v24_boxes as v24
from engine.causal_primitives import load_asset_ohlcv, resample_causal_tf

RESULTS = Path(__file__).resolve().parent / "results"
DATA = Path(__file__).resolve().parent / "data" / "BTCUSD_5m"
FEE = v24.FEE
MIN_R = v24.MIN_R
LOOKBACK = 300        # infrastructure: context bars for fractals/gaps
HORIZON = 1200        # infrastructure: bars after entry we keep watching


def build_frames():
    raw = load_asset_ohlcv(DATA, include_stems=[str(y) for y in
                                                range(2020, 2027)])
    return {f: resample_causal_tf(raw, f)
            for f in ("5min", "15min", "30min", "1h", "4h")}


def trade_path(frames, t):
    """Extended OHLC path from the entry bar onward + the bar index of
    the first post-entry bullish break of structure (BOS).

    NOTE: located BY TIME, never by trade["entry_idx"] — that index is a
    position inside the engine's WARM-FILTERED canvas, not inside the raw
    frame, so using it here shifted every path by ~10 months of bars."""
    tf = frames[t["exec_tf"]]
    e_t = pd.Timestamp(t["entry_time"])
    pos = tf.index.get_loc(e_t)
    lo = max(0, pos - LOOKBACK)
    hi = min(len(tf) - 1, pos + HORIZON)
    seg = tf.iloc[lo:hi + 1]
    rel = pos - lo
    # BOS: nearest internal RedBox live at the entry bar, broken by a
    # later CLOSE (causal canvas replay over the same window)
    cv = v24.ChartCanvas(t["exec_tf"])
    bos_bar = None
    ceiling = None
    for k in range(len(seg)):
        r = seg.iloc[k]
        cv.on_bar(r.Open, r.High, r.Low, r.Close, 0.0, k, seg.index[k])
        if k == rel:
            reds = [b.y_top for b in cv.reds
                    if b.state == "ACTIVE" and b.y_top > r.Close]
            ceiling = min(reds) if reds else None
        elif k > rel and ceiling is not None and r.Close > ceiling:
            bos_bar = k - rel
            break
    post = seg.iloc[rel:]
    return (post["Open"].to_numpy(), post["High"].to_numpy(),
            post["Low"].to_numpy(), post["Close"].to_numpy(), bos_bar)


def walk(t, path, rule):
    o, h, l, c, bos_bar = path
    E = float(t["entry_price"]); SP = float(t["stop_price"])
    Rk = E - SP
    pmid = float(t["purple_mid"]) if pd.notna(t["purple_mid"]) else None
    be_line = E * (1 + 2 * FEE)
    lock = (E * (1 + FEE) + MIN_R * Rk) / (1 - FEE)
    armed = False
    for j in range(len(c)):
        if armed and l[j] <= be_line:
            return "BE", 0.0, j                       # scratched
        if c[j] >= lock:                              # +3R lock on close
            if t["class"] == "WIN":
                return "WIN", float(t["R"]), j        # real booked ride
            return "WIN", MIN_R, j                    # floor: +3.00R
        if l[j] <= SP:
            return "LOSS", -1.0, j
        if not armed:
            if rule == "NONE":
                pass
            elif rule.startswith("A"):
                armed = c[j] >= E + float(rule[1:]) * Rk
            elif rule == "MID":
                armed = pmid is not None and c[j] > pmid
            elif rule == "BOS":
                armed = bos_bar is not None and j >= bos_bar
            elif rule == "MID+BOS":
                armed = (pmid is not None and c[j] > pmid
                         and bos_bar is not None and j >= bos_bar)
            elif rule == "MID+A1":
                armed = (pmid is not None and c[j] > pmid
                         and c[j] >= E + Rk)
            elif rule == "BOS+A1":
                armed = (bos_bar is not None and j >= bos_bar
                         and c[j] >= E + Rk)
    return t["class"], float(t["R"]), len(c) - 1      # never resolved


def main():
    A = pd.read_csv(RESULTS / "audit_v24_features.csv")
    A["entry_time"] = pd.to_datetime(A["entry_time"])
    A["exit_time"] = pd.to_datetime(A["exit_time"])
    A["yr"] = A["entry_time"].dt.year.astype(str)
    frames = build_frames()
    print(f"[shield] building extended paths for {len(A)} trades...")
    paths = {i: trade_path(frames, t) for i, t in A.iterrows()}
    A["bos_bar"] = [paths[i][4] for i in A.index]
    print(f"[shield] post-entry BOS printed on "
          f"{int(A['bos_bar'].notna().sum())} / {len(A)} trades")
    print(f"[shield] median extended path length: "
          f"{int(np.median([len(paths[i][0]) for i in A.index]))} bars")

    rules = ["NONE", "A0.25", "A0.5", "A0.75", "A1", "A1.5", "A2",
             "MID", "BOS", "MID+BOS", "MID+A1", "BOS+A1"]
    out = {}
    print("\n===== EXACT BAR-WALK: what each arm rule really does =====")
    print(f"{'rule':10} {'W':>4} {'BE':>4} {'L':>4} {'WR':>7} "
          f"{'L->scratch':>11} {'BE->WIN':>8} {'W lost':>7} {'maxR':>6}")
    for rule in rules:
        res = [walk(t, paths[i], rule) for i, t in A.iterrows()]
        cls = pd.Series([r[0] for r in res], index=A.index)
        Rs = pd.Series([r[1] for r in res], index=A.index)
        w = int((cls == "WIN").sum()); l = int((cls == "LOSS").sum())
        b = int((cls == "BE").sum()); wr = w / max(w + l, 1)
        saved = int(((A["class"] == "LOSS") & (cls != "LOSS")).sum())
        revived = int(((A["class"] == "BE") & (cls == "WIN")).sum())
        wlost = int(((A["class"] == "WIN") & (cls != "WIN")).sum())
        print(f"{rule:10} {w:4} {b:4} {l:4} {wr:7.1%} {saved:11} "
              f"{revived:8} {wlost:7} {Rs.max():6.2f}")
        A[f"cls_{rule}"] = cls
        A[f"R_{rule}"] = Rs
        out[rule] = {"W": w, "BE": b, "L": l, "WR": round(wr, 4),
                     "losses_to_scratch": saved, "be_revived_to_win": revived,
                     "winners_lost": wlost, "max_R": round(float(Rs.max()), 2),
                     "runners_4r": int((Rs[cls == "WIN"] >= 4).sum())}

    # ---- gates x shield ------------------------------------------ #
    A["wall_r_4h"] = pd.to_numeric(A["wall_r_4h"], errors="coerce")
    A["range_pos_4h"] = pd.to_numeric(A["range_pos_4h"], errors="coerce")
    q = A["range_pos_4h"] <= 0.25
    s6 = A["wall_r_4h"].isna() | (A["wall_r_4h"] >= 6)
    s10 = A["wall_r_4h"].isna() | (A["wall_r_4h"] >= 10)
    d4 = A["in_demand_4h"].astype(bool)
    G = {"none": pd.Series(True, index=A.index), "quarter": q,
         "sky6": s6, "sky10": s10, "demand4h": d4,
         "quarter+sky6": q & s6, "quarter+sky10": q & s10,
         "demand4h+sky6": d4 & s6, "quarter+demand4h": q & d4,
         "q+d+sky6": q & d4 & s6, "q+d+sky10": q & d4 & s10}
    print("\n===== GATE x SHIELD MATRIX  (rule:WR/n[assert5]) =====")
    best = []
    for gname, gm in G.items():
        gm = gm.fillna(False)
        line = [f"  {gname:16}"]
        for rule in rules:
            k = A[gm]
            cls = k[f"cls_{rule}"]
            w = int((cls == "WIN").sum()); l = int((cls == "LOSS").sum())
            wr = w / max(w + l, 1)
            yrs = k.groupby("yr").size().to_dict()
            a5 = len(k) >= 150 and all(yrs.get(str(y), 0) >= 12
                                       for y in range(2021, 2026))
            line.append(f"{rule}:{wr:5.1%}/{len(k):3}{ 'Y' if a5 else '-'}")
            best.append({"gate": gname, "rule": rule, "WR": round(wr, 4),
                         "n": int(len(k)), "W": w, "L": l,
                         "assert5": bool(a5),
                         "yearly": {str(a): int(b2) for a, b2 in
                                    yrs.items()}})
        print(" ".join(line))

    ok = [b for b in best if b["assert5"]]
    print("\n===== BEST COMBOS SATISFYING ASSERT 5 (n>=150, >=12/yr) =====")
    for b in sorted(ok, key=lambda x: -x["WR"])[:15]:
        print(f"  gate={b['gate']:16} rule={b['rule']:8} WR={b['WR']:.1%} "
              f"n={b['n']} W={b['W']} L={b['L']} yearly={b['yearly']}")
    print("\n===== BEST COMBOS IGNORING ASSERT 5 (upper WR bound) =====")
    for b in sorted(best, key=lambda x: -x["WR"])[:10]:
        print(f"  gate={b['gate']:16} rule={b['rule']:8} WR={b['WR']:.1%} "
              f"n={b['n']} W={b['W']} L={b['L']} yearly={b['yearly']}")

    A.to_csv(RESULTS / "audit_v24_shield.csv", index=False)
    with open(RESULTS / "audit_v24_shield.json", "w") as f:
        json.dump({"rules": out, "matrix": best}, f, indent=2, default=str)
    print("\n[shield] wrote results/audit_v24_shield.csv + .json")


if __name__ == "__main__":
    main()
