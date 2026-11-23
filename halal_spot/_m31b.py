#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_m31b.py — the PRIZE CEILING for each v31 arm, computed from the v30 books
(no re-simulation). A ceiling is the best an arm could possibly do if its
exit were placed at the trade's own maximum favourable excursion; a live
trailing stop always captures less, so this bounds the search and keeps the
report honest (the same instrument v28 used to bound its lock claim).

  CEILING A (arm 2, anti-choke): the trades killed by the +3.00R floor,
    re-booked at their own MFE (intrabar) and at their close-based MFE.
  CEILING B (arm 1, structural trail): the trades booked BE/LOSS that had
    already closed at >= +1.5R, re-booked at +1.00R (a conservative
    structural take-profit below the swing low), at +1.5R, and at their
    own close-based MFE.
"""
import sys
from pathlib import Path

import pandas as pd

R = Path(__file__).resolve().parent / "results"


def load(name):
    f = R / (f"trades_v30_{name}.csv" if name not in ("v27", "v25")
             else f"trades_{name}.csv")
    return pd.read_csv(f)


def ceilings(t, title):
    tot = t.R.sum()
    print(f"\n{'='*70}\n{title}: n={len(t)}  booked totR={tot:+.2f}  "
          f"net=${t.net_pnl.sum():+.2f}\n{'='*70}")

    lf = t[t.exit_reason == "LOCK_FLOOR_CLOSE"]
    print(f"\n-- CEILING A (arm 2): floor kills n={len(lf)}, "
          f"booked totR={lf.R.sum():+.2f} (every one at exactly "
          f"{lf.R.min():.2f}..{lf.R.max():.2f}R)")
    if len(lf):
        for lbl, col in (("intrabar MFE (upper bound, needs a perfect "
                          "exit at the high)", "mfe_R"),
                         ("close-based MFE (a close-driven trail could "
                          "actually see this)", "mfe_close_R")):
            gain = lf[col].sum() - lf.R.sum()
            print(f"   re-booked at {lbl}:\n"
                  f"     sum={lf[col].sum():+.2f}R  gain={gain:+.2f}R  "
                  f"=> book totR would be {tot+gain:+.2f}R "
                  f"({100*gain/abs(tot):.0f}% of the booked total)")
        for frac in (0.5, 0.7):
            cap = lf.R.sum() + frac * (lf.mfe_close_R.sum() - lf.R.sum())
            print(f"   capturing {frac:.0%} of the close-based extension: "
                  f"{cap:+.2f}R => book {tot + (cap-lf.R.sum()):+.2f}R")

    leak15 = t[(t["class"].isin(["BE", "LOSS"])) & (t.mfe_close_R >= 1.5)]
    leak_i = t[(t["class"].isin(["BE", "LOSS"])) & (t.mfe_R >= 1.5)]
    print(f"\n-- CEILING B (arm 1): trades booked BE/LOSS that had already "
          f"CLOSED >= +1.5R: n={len(leak15)} "
          f"(intrabar reading n={len(leak_i)}), booked totR="
          f"{leak15.R.sum():+.2f}R")
    if len(leak15):
        for bank in (1.0, 1.5, 2.0):
            gain = bank * len(leak15) - leak15.R.sum()
            print(f"   banked at +{bank:.1f}R each: gain={gain:+.2f}R "
                  f"=> book totR {tot+gain:+.2f}R")
        gain = leak15.mfe_close_R.sum() - leak15.R.sum()
        print(f"   re-booked at their own close-based MFE "
              f"(sum={leak15.mfe_close_R.sum():+.2f}R): gain={gain:+.2f}R "
              f"=> book totR {tot+gain:+.2f}R")
        print(f"   (their classes today: "
              f"{leak15['class'].value_counts().to_dict()})")
    both = lf.R.sum() + leak15.R.sum()
    print(f"\n-- combined: the two leaks sit on {len(lf)+len(leak15)} trades "
          f"({100*(len(lf)+len(leak15))/len(t):.0f}% of the book) whose "
          f"booked totR is {both:+.2f}R")


def main():
    for name, title in ((sys.argv[1] if len(sys.argv) > 1 else
                         "M1v_shbe_rst", "v30 SHIPPED"),
                        ("base", "v30 base = v27")):
        t = load(name)
        if t is not None:
            ceilings(t, title)


if __name__ == "__main__":
    main()
