#!/usr/bin/env python3
"""
audit_v26_invalidation.py — EXACT BAR-WALK OF THE "IN-TRADE BEARISH
INVALIDATION" EXIT (v26 brief, Crime 2, second half).

Claim under test: when the stop has been widened to the far HTF demand
floor, the trade is already dead the moment a CLOSE prints below the LTF
GreenBox floor (the structure that actually justified the entry) — so why
ride it all the way down to the HTF floor and book the full -1R?

This walks every trade bar by bar and compares three exits:
  (a) the real stop            -> -1.00R
  (b) the structural cut       -> the first close below green.y_bottom,
                                  executed at that close (gap-aware)
  (c) the +3R net lock         -> the booked winner, unchanged
and reports, for each rule, W / BE / L, the decided win rate
WIN/(WIN+LOSS), the runners, the average R and the total R — because an
early cut changes the SIZE of a loss, never its CLASS, so it cannot lift
the win rate; it can only lift PF / net / avg_R.  If it also destroys
winners, it is rejected.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import audit_v24_shield as sh

RES = Path(__file__).resolve().parent / "results"
FEE = sh.FEE
MIN_R = sh.MIN_R
YEARS = ("2021", "2022", "2023", "2024", "2025")


def green_bottom(t):
    g = t.get("green")
    if isinstance(g, str) and g.startswith("{"):
        try:
            return float(ast.literal_eval(g)["bottom"])
        except Exception:
            return np.nan
    return np.nan


def walk_invalidation(t, path, cut: bool, need_fvg: bool):
    """Return (class, R) under the structural-cut rule."""
    o, h, l, c, bos_bar = path
    E = float(t["entry_price"]); SP = float(t["stop_price"]); Rk = E - SP
    if Rk <= 0:
        return t["class"], float(t["R"])
    gb = green_bottom(t)
    lock = (E * (1 + FEE) + MIN_R * Rk) / (1 - FEE)
    for j in range(len(c)):
        if c[j] >= lock:                                  # delivered
            return "WIN", (float(t["R"]) if t["class"] == "WIN" else MIN_R)
        if l[j] <= SP:                                    # real stop first
            px = SP if o[j] >= SP else o[j]
            return "LOSS", (px - E) / Rk - 2 * FEE * E / Rk
        if cut and np.isfinite(gb) and gb > SP and c[j] < gb:
            if need_fvg:
                # a fresh bearish FVG must sit above this close: the gap
                # between bar j-2 low and bar j high, both above the close
                if j >= 2 and not (l[j - 2] > h[j] and c[j] < h[j]):
                    continue
            px = c[j] if o[j] >= gb else o[j]              # gap-aware
            return "LOSS", (px - E) / Rk - 2 * FEE * E / Rk
    return t["class"], float(t["R"])


def score(rows, label):
    cl = np.array([r[0] for r in rows]); R = np.array([r[1] for r in rows])
    W = int((cl == "WIN").sum()); B = int((cl == "BE").sum()); L = int((cl == "LOSS").sum())
    dec = W + L
    wins = R[cl == "WIN"]; losses = R[cl == "LOSS"]
    gp = float(R[R > 0].sum()); gl = float(-R[R < 0].sum())
    return {"label": label, "n": W + B + L, "W": W, "BE": B, "L": L,
            "WR_pct": round(100 * W / dec, 2) if dec else 0.0,
            "ge4R": int((wins >= 4).sum()),
            "maxR": round(float(wins.max()), 2) if len(wins) else 0.0,
            "minW": round(float(wins.min()), 2) if len(wins) else 0.0,
            "avg_R": round(float(R.mean()), 3),
            "avg_loss_R": round(float(losses.mean()), 3) if len(losses) else 0.0,
            "total_R": round(float(R.sum()), 1),
            "R_PF": round(gp / gl, 3) if gl > 0 else float("inf")}


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "trades_v26.csv"
    trades = pd.read_csv(RES / src)
    trades["entry_time"] = pd.to_datetime(trades["entry_time"])
    print(f"[inv] {src}: {len(trades)} trades "
          f"{trades['class'].value_counts().to_dict()}")
    gb = trades.apply(green_bottom, axis=1)
    infl = trades["stop_price"] < gb - 1e-9
    print(f"[inv] stop below the GreenBox floor (inflated): "
          f"{int(infl.sum())}/{len(trades)} ({100*infl.mean():.1f}%)")
    print(f"[inv] median R given up by an inflated stop: "
          f"{((gb - trades['stop_price']) / (trades['entry_price'] - trades['stop_price']))[infl].median():.2f}R")

    frames = sh.build_frames()
    paths = {i: sh.trade_path(frames, t) for i, t in trades.iterrows()}
    print("[inv] paths built")

    variants = [("no cut (reference)", False, False),
                ("cut at close < green floor", True, False),
                ("cut + fresh bearish FVG", True, True)]
    out = []
    print(f"\n  {'rule':32s}{'W':>4}{'BE':>4}{'L':>4}{'WR%':>7}{'>=4R':>5}"
          f"{'maxR':>7}{'avgR':>7}{'avgL':>7}{'totR':>8}{'R-PF':>7}")
    for label, cut, fvg in variants:
        rows = [walk_invalidation(t, paths[i], cut, fvg)
                for i, t in trades.iterrows()]
        s = score(rows, label)
        out.append(s)
        print(f"  {label:32s}{s['W']:>4}{s['BE']:>4}{s['L']:>4}{s['WR_pct']:>7}"
              f"{s['ge4R']:>5}{s['maxR']:>7}{s['avg_R']:>7}{s['avg_loss_R']:>7}"
              f"{s['total_R']:>8}{s['R_PF']:>7}")

    # winners destroyed by the cut?
    base = [walk_invalidation(t, paths[i], False, False)
            for i, t in trades.iterrows()]
    for label, cut, fvg in variants[1:]:
        rows = [walk_invalidation(t, paths[i], cut, fvg)
                for i, t in trades.iterrows()]
        destroyed = sum(1 for a, b in zip(base, rows)
                        if a[0] == "WIN" and b[0] != "WIN")
        saved = sum(1 for a, b in zip(base, rows)
                    if a[0] == "LOSS" and b[1] > a[1] + 1e-9)
        r_saved = sum(b[1] - a[1] for a, b in zip(base, rows)
                      if a[0] == "LOSS" and b[0] == "LOSS")
        print(f"\n  {label}: winners destroyed = {destroyed}, "
              f"losses shortened = {saved}, R recovered = {r_saved:+.1f}R")
    pd.DataFrame(out).to_csv(
        RES / f"audit_invalidation_{src.replace('trades_','').replace('.csv','')}.csv",
        index=False)


if __name__ == "__main__":
    main()
