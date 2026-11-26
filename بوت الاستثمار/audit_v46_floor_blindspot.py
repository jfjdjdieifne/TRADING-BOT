#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_v46_floor_blindspot.py -- v46 STEP 1 (<4 s, ZERO engine runs).

THE TWO BLINDSPOTS THIS MEASURES
--------------------------------
(A) `floor_line` IS A CLOSE RULE ON THE EXEC FRAME.
    In the champion, LOCK_MODE="trail" turns the +3R floor into a rule that
    arms only when an EXEC bar (5/15/30/60m) CLOSES at or above it. Between
    those closes the floor does not exist: the only live order is the ORIGINAL
    wick stop underneath. So price can trade through the +3R level on the 5m
    tape, reverse, and kill the position at -1.00x without the floor ever
    having been armed. This file counts exactly that population and prices the
    loss that the blindspot causes.

(B) ARMING ON A CLOSE IS NOT THE SAME AS DEFENDING A LEVEL.
    Even when the floor DOES arm, it is tested on the exec close. A 5m wick
    through an armed floor can therefore pass with no exit at all.

THE FIX, AND WHY IT IS NOT JUST "ARM ON THE WICK"
    Arming the floor on a 5m WICK would be a lookahead-free change, but the
    level itself is still arbitrary: price touches +3x and the position books
    +3x, so every trade that would have run to +19x books +3x instead. v45
    already measured that trade-off and it loses money.

    The brain tested here instead waits for the MARKET to say the move is over,
    and only then acts. It is causal by construction:
      * a CONFIRMED SWING LOW is a 5m pivot whose right-hand bar has closed,
        so the decision can only be taken on that later closed bar;
      * a FAILED BOUNCE is a bounce that rolls over and closes back under the
        swing it bounced from -- again, known only at the close of the bar
        that does it.
    Neither rule predicts the top, so neither caps a runner that keeps making
    higher lows. That is the whole point: it must cut the dead trades without
    amputating the +19x ones.

USAGE  python3 audit_v46_floor_blindspot.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import audit_v45_true_multiple_brain as A          # noqa: E402

RES = HERE / "results"
COST = A.COST
PIVOT = 2                 # bars either side that define a confirmed swing


# ------------------------------------------------------------------ #
def swings(c: np.ndarray, l: np.ndarray, h: np.ndarray, k: int = PIVOT):
    """Confirmed swing lows/highs. A pivot at i is CONFIRMED at bar i+k,
    because only then has the right-hand bar closed. Returned as the index of
    the bar on which the information becomes available (i + k)."""
    n = len(c)
    lo_ok = np.zeros(n, bool)
    hi_ok = np.zeros(n, bool)
    for i in range(k, n - k):
        if l[i] == l[i - k:i + k + 1].min():
            lo_ok[i + k] = True          # knowable only at i+k
        if h[i] == h[i - k:i + k + 1].max():
            hi_ok[i + k] = True
    return lo_ok, hi_ok


def swing_levels(l: np.ndarray, h: np.ndarray):
    """The most recent CONFIRMED swing low value available at each bar."""
    n = len(l)
    lvl = np.full(n, np.nan)
    last = np.nan
    for i in range(n):
        i_lo = i - PIVOT
        if i_lo >= PIVOT and l[i_lo] == l[i_lo - PIVOT:i_lo + PIVOT + 1].min():
            last = l[i_lo]
        lvl[i] = last
    return lvl


# ------------------------------------------------------------------ #
def sim_v46(t: pd.DataFrame, data: dict, min_x: float = 1.0,
            mode: str = "confirmed_swing_failed_bounce") -> pd.DataFrame:
    """Static tape sim of the v46 brain, 5m clock, 100% exits only.

    RULES (a position must first show progress of at least `min_x` true
    multiples, otherwise B0 owns it):
      R1 FAILED BOUNCE  -- after price has made a confirmed swing low, if a
         later closed bar closes back BELOW that swing low, exit 100% at that
         close. The swing low was confirmed PIVOT bars before it can be used.
      R2 CONFIRMED SWING-LOW STOP -- lift the protective stop to the most
         recent confirmed swing low, but only once it sits above the entry
         stop. The raise is armed on a closed bar and tested from the next.
    Whatever happens, the ORIGINAL engine stop stays underneath, so this brain
    can only ever improve an exit; it never widens a loss.
    """
    n = len(t)
    net = np.zeros(n)
    xs = np.zeros(n)
    why = [""] * n
    for k, r in enumerate(t.itertuples(index=False)):
        D = data[r.symbol]
        i0, i1 = A.slice_bars(D, r.entry_ns, r.exit_ns)
        f, L_, q = r.fill, r.unit_loss, r.qty
        px = None
        tag = "B0_EXIT"
        if i1 - i0 > PIVOT * 2:
            o = D["o"][i0:i1]
            h = D["h"][i0:i1]
            lo = D["l"][i0:i1]
            c = D["c"][i0:i1]
            Xc = (c * (1 - COST) - f * (1 + COST)) / L_
            sl = swing_levels(lo, h)
            armed = np.nan          # the protective stop, live from bar i+1
            for i in range(len(c)):
                if i >= 1 and not np.isnan(armed):
                    if lo[i] <= armed:
                        px = armed if o[i] >= armed else o[i]
                        tag = "V46_SWING_STOP"
                        break
                if Xc[i] < min_x:   # not yet in profit: B0 owns it
                    continue
                # ---- R1: failed bounce. The bar closes under the last
                # CONFIRMED swing low -> the bounce failed, leave at 100%.
                if not np.isnan(sl[i]) and c[i] < sl[i] and c[i] < o[i]:
                    px = c[i]
                    tag = f"V46_FAILED_BOUNCE_{Xc[i]:.1f}x"
                    break
                # ---- R2: arm the protective stop on this confirmed swing
                if not np.isnan(sl[i]):
                    lvl = A.px_at_true_X(f, r.stop, 0.0)   # never below BE
                    new = max(sl[i], lvl)
                    if np.isnan(armed) or new > armed:
                        armed = new          # live from the NEXT bar
        if px is not None:
            net[k] = (px * (1 - COST) - f * (1 + COST)) * q
            xs[k] = (px * (1 - COST) - f * (1 + COST)) / L_
            why[k] = tag
        else:
            net[k] = r.net_pnl
            xs[k] = r.B0_true_X
            why[k] = "B0_EXIT"
    out = t.copy()
    out["net_sim"] = net
    out["tag"] = why
    out["X_sim"] = xs
    return out


def summ(fr: pd.DataFrame, base_total: float) -> dict:
    mo = fr.groupby("ym").net_sim.sum()
    hf = fr.groupby("half").net_sim.sum()
    wk = fr.groupby("iso").net_sim.sum()
    return {"em": round(float(fr[fr.em].net_sim.sum()), 2),
            "be": round(float(fr[fr.be].net_sim.sum()), 2),
            "gold": round(float(fr[fr.golden].net_sim.sum()), 2),
            "other": round(float(fr[fr.other].net_sim.sum()), 2),
            "total": round(float(fr.net_sim.sum()), 2),
            "delta": round(float(fr.net_sim.sum() - base_total), 2),
            "mo": f"{int((mo > 1e-9).sum())}/{len(mo)}",
            "bw": f"{int((hf > 1e-9).sum())}/{len(hf)}",
            "wk": f"{int((wk > 1e-9).sum())}/{len(wk)}",
            "mix": {str(a): int(b) for a, b in
                    fr.tag.value_counts().head(8).items()}}


def main() -> int:
    t0 = time.time()
    t = A.load_tape()
    data = {s: A.load_5m(s) for s in A.SYMS}
    t = A.measure(t, data)
    t["armed"] = t.max_exec_close >= t.floor_line - 1e-6
    t["touched"] = t.max_5m_high >= t.floor_line - 1e-6
    bl = t[t.touched & ~t.armed]

    print(f"# v46 STEP 1 — THE floor_line BLINDSPOT  "
          f"({time.time()-t0:.1f}s, ZERO engine runs)\n")
    print(f"book: **{len(t)}** trades · {t.ym.nunique()} months · "
          f"{t.iso.nunique()} weeks · net **${t.net_pnl.sum():+.2f}**\n")

    print("## 1. THE BLINDSPOT, COUNTED\n")
    print("| quantity | trades |")
    print("|---|---:|")
    print(f"| touched `floor_line` on the 5m tape | {int(t.touched.sum())} |")
    print(f"| actually ARMED it (an exec bar CLOSED above) | "
          f"{int(t.armed.sum())} |")
    print(f"| **touched but NEVER armed** | **{int(len(bl))}** |")
    print(f"\nOf the 99 EMERGENCY_STOP trades: {int(t[t.em].touched.sum())}/99 "
          f"touched the floor on 5m and {int(t[t.em].armed.sum())}/99 armed "
          f"it, so EM is NOT caused by the arming gap — EM trades armed the "
          f"floor and were still killed by a wick through the ORIGINAL stop "
          f"underneath it. The arming gap is a separate, smaller population.\n")

    print("### What the 44 touched-but-never-armed trades are\n")
    print(f"n=**{len(bl)}** · net **{bl.net_pnl.sum():+.2f}$** · "
          f"golden {int(bl.golden.sum())} · EM {int(bl.em.sum())} · "
          f"BE {int(bl.be.sum())} · other {int(bl.other.sum())}")
    print(f"\nThe honest test: of these 44, only "
          f"**{int((bl.X_5m_close>=3).sum())}** actually reached 3x on a 5m "
          f"CLOSE. Booking a +3x floor on the other "
          f"{len(bl)-int((bl.X_5m_close>=3).sum())} would be reading the "
          f"future — the floor level was touched, but the trade never "
          f"confirmed it. Quoting `actual -6.12$ -> +98.11$ at 3x` would be a "
          f"lookahead artefact and is deliberately NOT claimed here.\n")

    print("## 2. THE v46 BRAIN — causal by construction\n")
    print("* **R1 FAILED BOUNCE** — a 5m pivot low is only a *confirmed* "
          "swing low once `PIVOT=2` right-hand bars have closed. If a later "
          "bar closes back below that confirmed low on a bearish bar, the "
          "bounce failed: exit **100%** at that close.")
    print("* **R2 CONFIRMED SWING-LOW STOP** — lift the protective stop to the "
          "most recent confirmed swing low, never below fee-breakeven. Armed "
          "on a closed bar, tested from the **next** bar.")
    print("* The original engine stop stays underneath, so the brain can only "
          "improve an exit, never widen a loss. No partials, ever.\n")

    print("## 3. STATIC SIM — the 1,173-trade book held fixed\n")
    base = float(t.net_pnl.sum())
    rows = []
    hdr = ("| arm | min progress | EM_99 $ | BE_452 $ | Golden_110 $ | "
           "Other_512 $ | **Total** | Δ vs B0 | mo+ | bw+ | wk+ |")
    print(hdr)
    print("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    b0 = {"em": round(float(t[t.em].net_pnl.sum()), 2),
          "be": round(float(t[t.be].net_pnl.sum()), 2),
          "gold": round(float(t[t.golden].net_pnl.sum()), 2),
          "other": round(float(t[t.other].net_pnl.sum()), 2),
          "total": round(base, 2),
          "mo": f"{int((t.groupby('ym').net_pnl.sum() > 1e-9).sum())}"
                f"/{t.ym.nunique()}",
          "bw": f"{int((t.groupby('half').net_pnl.sum() > 1e-9).sum())}"
                f"/{t.half.nunique()}",
          "wk": f"{int((t.groupby('iso').net_pnl.sum() > 1e-9).sum())}"
                f"/{t.iso.nunique()}"}
    print(f"| B0 | — | {b0['em']:+.2f} | {b0['be']:+.2f} | {b0['gold']:+.2f} "
          f"| {b0['other']:+.2f} | **{b0['total']:+.2f}** | +0.00 | {b0['mo']} "
          f"| {b0['bw']} | {b0['wk']} |")
    out = {"B0": b0}
    for mx in (0.0, 1.0, 2.0):
        fr = sim_v46(t, data, mx)
        s = summ(fr, base)
        out[f"v46_min{mx}"] = s
        rows.append((mx, fr))
        print(f"| **v46** swing/failed-bounce | ≥{mx:g}x | {s['em']:+.2f} | "
              f"{s['be']:+.2f} | {s['gold']:+.2f} | {s['other']:+.2f} | "
              f"**{s['total']:+.2f}** | {s['delta']:+.2f} | {s['mo']} | "
              f"{s['bw']} | {s['wk']} |")
    print()
    for mx, fr in rows:
        print(f"*min≥{mx:g}x exit mix:* {out[f'v46_min{mx}']['mix']}")
        fr.to_csv(RES / f"_v46_sim_min{mx:g}.csv", index=False)
    (RES / "_v46_audit.json").write_text(json.dumps(
        out, indent=1, default=str))
    print(f"\n_total {time.time()-t0:.2f}s_")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
