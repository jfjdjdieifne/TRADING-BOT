#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_m30.py — independent checks on the v30 artefacts already on disk.
Nothing here re-simulates the engine; every number is read from the trade
books the live engine wrote (results/trades_v30_<combo>.csv).

  check base   : is the v30 base book bit-identical to v27?
  check vig    : how many v27 losses become genuine scratches, and what
                 the honest (conservative) loss streak is
  check dollar : does dollar-R sizing actually equalize the DOLLAR value
                 of 1R across trades?
  check fee    : the fee-vs-1R population each arm leaves on the book
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

R = Path(__file__).resolve().parent / "results"
FEE = 0.001


def book(combo):
    f = R / (f"trades_v30_{combo}.csv" if combo not in ("v27", "v25")
             else f"trades_{combo}.csv")
    return pd.read_csv(f) if f.exists() else None


def streaks(t):
    """BE-resets (the engine's ASSERT4 reading) and conservative
    (a scratch does NOT break a losing run — the honest worst case)."""
    a = b = cur = cons = 0
    for c in t["class"]:
        if c == "LOSS":
            cur += 1; cons += 1
            a = max(a, cur); b = max(b, cons)
        elif c == "WIN":
            cur = cons = 0
        else:
            cur = 0
    return a, b


def risk_dollars(t):
    """Dollar value of 1R = notional x risk% / 100 (halal spot: no
    leverage, so this is the cash actually lost on a stop-out)."""
    if "notional" in t and "risk_pct" in t:
        return t.notional * t.risk_pct / 100.0
    return None


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "all"

    if what in ("all", "base"):
        a, b = book("base"), book("v27")
        if a is None or b is None:
            print("base/v27 book missing")
        else:
            same_n = len(a) == len(b)
            cols = [c for c in ("entry_time", "exit_time", "entry_price",
                                "exit_price", "R", "net_pnl", "class")
                    if c in a and c in b]
            diff = {c: int((a[c].astype(str).values
                            != b[c].astype(str).values).sum()) for c in cols}
            print("=== base (v30) vs v27 ===============================")
            print(f"  n: {len(a)} vs {len(b)}   identical rows: {same_n}")
            print(f"  column mismatches: {diff}")
            print(f"  sum R {a.R.sum():.4f} vs {b.R.sum():.4f} | "
                  f"sum net {a.net_pnl.sum():.2f} vs {b.net_pnl.sum():.2f}")

    if what in ("all", "vig"):
        v27 = book("v27")
        print("\n=== module 1: what vigilance does to the v27 book =====")
        for combo in ("M1a_hold", "M1a_decay", "M1v_shieldbe", "M1v_shield",
                      "M1_ab", "M1b_bos", "M1b_or"):
            t = book(combo)
            if t is None:
                continue
            w = int((t["class"] == "WIN").sum())
            be = int((t["class"] == "BE").sum())
            l = int((t["class"] == "LOSS").sum())
            a, b = streaks(t)
            m = v27.merge(t, on="entry_time", suffixes=("_27", "_n"))
            conv = (m[(m.class_27 == "LOSS")].class_n.value_counts().to_dict()
                    if len(m) else {})
            lost_w = (m[(m.class_27 == "WIN")].class_n.value_counts().to_dict()
                      if len(m) else {})
            # every BE must be a genuine scratch: net ~= 0
            bes = t[t["class"] == "BE"]
            worst_be = float(bes.R.min()) if len(bes) else None
            print(f"  {combo:14s} n={len(t):4d} {w:3d}W/{be:3d}BE/{l:3d}L "
                  f"streak={a}/{b} worst_BE_R={worst_be} "
                  f"matched={len(m):3d} v27LOSS->{conv} v27WIN->{lost_w}")

    if what in ("all", "dollar"):
        print("\n=== module 3b: is dollar-1R equalized? =================")
        for combo in ("base", "M3b_dollarR", "M1v_shieldbe"):
            t = book(combo)
            if t is None:
                continue
            d = risk_dollars(t)
            if d is None:
                print(f"  {combo}: no notional column")
                continue
            q = d.quantile([.05, .25, .5, .75, .95]).round(2).to_dict()
            print(f"  {combo:14s} 1R$ min={d.min():.2f} p05={q[0.05]} "
                  f"p25={q[0.25]} med={q[0.5]} p75={q[0.75]} p95={q[0.95]} "
                  f"max={d.max():.2f}  IQR/max={d.quantile(.75)/d.max():.3f}")
            eq = 200.0
            print(f"                 as % of a $200 start: med="
                  f"{q[0.5]/eq*100:.3f}%  max={d.max()/eq*100:.3f}%")

    if what in ("all", "fee"):
        print("\n=== module 3a: the fee-vs-1R population ================")
        rows = []
        for combo in ("v27", "base", "M1v_shieldbe", "M1a_hold", "M3a_030",
                      "M3a_040", "M3b_dollarR"):
            t = book(combo)
            if t is None:
                continue
            risk = t.entry_price - t.stop_price
            feeR = 2 * FEE * t.entry_price / risk
            rows.append(dict(combo=combo, n=len(t),
                             med_risk_pct=round(float(
                                 (risk / t.entry_price * 100).median()), 4),
                             share_fee_ge_1R=round(float(
                                 (feeR >= 1).mean() * 100), 1),
                             n_fee_ge_1R=int((feeR >= 1).sum()),
                             med_fee_in_R=round(float(feeR.median()), 3)))
        print(pd.DataFrame(rows).to_string(index=False))

    if what in ("all", "sweep"):
        print("\n=== every v30 arm measured live so far =================")
        fs = sorted(R.glob("lab_v30_sweep*.csv"))
        if not fs:
            print("  no sweep files yet")
            return
        df = pd.concat([pd.read_csv(f) for f in fs], ignore_index=True)
        df = df.drop_duplicates("combo", keep="last")
        cols = ["combo", "n", "W", "BE", "L", "wr", "ge4R", "maxR", "totR",
                "net_pct", "pf", "maxDD", "streak", "streak_cons", "ymin",
                "passed"]
        print(df[[c for c in cols if c in df]]
              .sort_values("net_pct", ascending=False).to_string(index=False))
        df.to_csv(R / "lab_v30_all_arms.csv", index=False)


if __name__ == "__main__":
    main()
