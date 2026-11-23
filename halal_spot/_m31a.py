#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_m31a.py — the v31 prize measurement, read straight off the books the live
engine already wrote (no re-simulation).

Answers, for the shipped v30 arm and for the v27 base:
  1. of the BE scratches and of the LOSSes, how many actually reached
     +1.0R / +1.5R / +2.0R / +2.5R / +3.0R during their own life
     (both readings: intrabar MFE and the honest CLOSE-based MFE)?
  2. what was the maximum extension of the trades killed by the +3.00R
     floor (LOCK_FLOOR_CLOSE), and what did they book?
  3. what does the fee bill really cost, and how big is 1R in dollars?
  4. monthly cadence: wins/month, net/month, the compounding rate.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

R = Path(__file__).resolve().parent / "results"
LEVELS = (1.0, 1.5, 2.0, 2.5, 3.0)


def load(name):
    f = R / (f"trades_v30_{name}.csv" if name not in ("v27", "v25")
             else f"trades_{name}.csv")
    return pd.read_csv(f)


def mfe_table(t, title):
    print(f"\n--- {title}: n={len(t)} ---")
    for cls in ("BE", "LOSS", "WIN"):
        s = t[t["class"] == cls]
        if not len(s):
            continue
        row = []
        for L in LEVELS:
            row.append(f">={L}R: {int((s.mfe_R >= L).sum()):3d}"
                       f"/close {int((s.mfe_close_R >= L).sum()):3d}")
        print(f"  {cls:5s} n={len(s):3d}  " + "  ".join(row))
        print(f"         mfe_R  med={s.mfe_R.median():5.2f} "
              f"p75={s.mfe_R.quantile(.75):5.2f} max={s.mfe_R.max():6.2f} | "
              f"mfe_close med={s.mfe_close_R.median():5.2f} "
              f"p75={s.mfe_close_R.quantile(.75):5.2f} "
              f"max={s.mfe_close_R.max():6.2f} | booked R med={s.R.median():5.2f}")
    # the leakage: what the death zone costs
    for L in (1.5, 2.0, 2.5):
        leak = t[(t["class"].isin(["BE", "LOSS"])) & (t.mfe_close_R >= L)]
        leak_w = t[(t["class"].isin(["BE", "LOSS"])) & (t.mfe_R >= L)]
        print(f"  LEAK close-MFE>={L}R but booked BE/LOSS: n={len(leak):3d} "
              f"(intrabar reading: n={len(leak_w):3d})  "
              f"their booked totR={leak.R.sum():+.2f}")


def floor_kills(t, title):
    s = t[t.exit_reason == "LOCK_FLOOR_CLOSE"]
    print(f"\n--- {title}: LOCK_FLOOR_CLOSE kills n={len(s)} ---")
    if not len(s):
        return
    print(f"  booked R: med={s.R.median():.2f} min={s.R.min():.2f} "
          f"max={s.R.max():.2f} totR={s.R.sum():+.2f}")
    print(f"  mfe_R (intrabar max extension): med={s.mfe_R.median():.2f} "
          f"p75={s.mfe_R.quantile(.75):.2f} max={s.mfe_R.max():.2f} "
          f"mean={s.mfe_R.mean():.2f}")
    print(f"  mfe_close_R (close-based):      med={s.mfe_close_R.median():.2f} "
          f"p75={s.mfe_close_R.quantile(.75):.2f} max={s.mfe_close_R.max():.2f}")
    for L in (4, 5, 6, 8, 10):
        print(f"    reached >={L}R then booked at the floor: "
              f"{int((s.mfe_R >= L).sum())} (close-based "
              f"{int((s.mfe_close_R >= L).sum())})")
    w = t[t["class"] == "WIN"]
    print(f"  share of all winners killed by the floor: "
          f"{len(s)}/{len(w)} = {100*len(s)/max(len(w),1):.1f}%")
    print(f"  winners by exit_reason: "
          f"{w.exit_reason.value_counts().to_dict()}")
    print(f"  winners booked R: "
          f"{np.round(sorted(w.R.values)[:12], 2).tolist()} ...")


def money(t, title, summ=None):
    print(f"\n--- {title}: money & cadence ---")
    if summ is None:
        sj = R / ("summary_v30.json" if title.startswith("v30 SHIPPED")
                  else f"summary_{title.split()[0]}.json")
        summ = json.load(open(sj)) if sj.exists() else {}
    fees = float(summ.get("fees", 0.0))
    net = float(t.net_pnl.sum())
    gross = net + fees
    print(f"  net=${net:.2f}  fees=${fees:.2f}  gross=${gross:.2f}  "
          f"fees/gross={100*fees/gross:.1f}%  fees per trade=${fees/len(t):.3f}")
    risk = (t.entry_price - t.stop_price)
    d1r = t.notional * (risk / t.entry_price) if "notional" in t else None
    if d1r is not None:
        print(f"  dollar-1R: med=${d1r.median():.2f} max=${d1r.max():.2f} "
              f"=> a +3R win moves the book by "
              f"{3*d1r.median()/200*100:.2f}% of a $200 start (median trade)")
    t2 = t.copy()
    t2["m"] = t2.entry_time.astype(str).str[:7]
    g = t2.groupby("m").agg(n=("R", "size"), W=("class", lambda s: (s == "WIN").sum()),
                            net=("net_pnl", "sum"))
    months = len(g)
    print(f"  months covered={months}  wins/month={g.W.sum()/months:.2f}  "
          f"trades/month={g.n.sum()/months:.1f}  "
          f"net/month(avg $)={g.net.sum()/months:.2f}")
    pos = (g.net > 0).sum()
    print(f"  profitable months={pos}/{months} = {100*pos/months:.0f}%  "
          f"worst month=${g.net.min():.2f} best=${g.net.max():.2f}")
    eq = 200.0
    # cadence over the WHOLE calendar span, not only the months that traded
    span = pd.period_range(t2.m.min(), t2.m.max(), freq="M")
    cal = len(span)
    cagr_m = ((eq + net) / eq) ** (1 / cal) - 1 if cal else 0
    print(f"  calendar months={cal} (traded={months})  "
          f"compounded monthly rate={100*cagr_m:.2f}%/month  "
          f"arithmetic net/month={100*net/eq/cal:.2f}% of the $200 start")
    print(f"  wins/calendar-month={g.W.sum()/cal:.2f}  "
          f"trades/calendar-month={g.n.sum()/cal:.1f}")


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "M1v_shbe_rst"
    for name, title in ((which, f"v30 SHIPPED ({which})"), ("base", "v30 base = v27")):
        t = load(name)
        if t is None:
            print(f"missing book for {name}")
            continue
        print(f"\n{'='*72}\n{title}\n{'='*72}")
        mfe_table(t, title)
        floor_kills(t, title)
        money(t, title)


if __name__ == "__main__":
    main()
