#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_v50_shield_and_reentry.py -- v50 STAGE 1 (static, ZERO engine runs).

PART 1A  C4 parameter plateau with the CORRECTED real-close exit math
         (v49 section 1.4): the exit fills at the bar's actual close, not
         at an idealised px_at_true_X(X).

PART 1B  Post-exit autopsy of all 452 SHIELD_BE trades:
           1. what price did AFTER the 0.00x exit (24h / 48h)
           2. which were premature shakeouts vs true saves
           3. static test of giving SHIELD_BE breathing room
         plus the code-level reason only 41 of 452 re-entered.

PART 1C  Bar-0 / Bar-1 entry-candle reaction anatomy: is the falling
         knife visible on the entry bar itself?

USAGE  python3 audit_v50_shield_and_reentry.py [1a|1b|1c|all]
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
import audit_v47_ict_boxes as V                    # noqa: E402

RES = HERE / "results"
COST = A.COST
WINS = ("W1", "W2", "OLD7", "MOD_Y1", "MOD_Y2")
XGRID = [-0.15, -0.20, -0.25, -0.30, -0.35, -0.40, -0.45, -0.50]
BENCH = [("2024-01-13 02:05", "LINKUSDT_5m", 10.08),
         ("2024-01-01 03:45", "ADAUSDT_5m", 4.70),
         ("2024-01-08 05:15", "ETHUSDT_5m", 4.41),
         ("2026-01-01 16:30", "SOLUSDT_5m", 6.89)]


# ================================================================== #
def arm_paths(t: pd.DataFrame, data: dict) -> list:
    """Every armed trade: the causal post-arm exec closes with their real
    close price, plus the peak reached before the arm (for reference)."""
    out = []
    for r in t.itertuples(index=False):
        D = data[r.symbol]
        tf = A.TF_NS[r.exec_tf]
        ab = V.arm_bar(D, r, tf)
        if ab is None:
            continue
        i0, i1, k = ab
        ns = D["ns"][i0:i1]
        arm_ns = ns[k] if k < len(ns) else ns[-1]
        E = A.exec_closes(D, r.entry_ns, r.exit_ns, tf)
        if E is None or not len(E["c"]):
            continue
        seen = (E["end"] <= r.exit_ns) & (E["end"] > arm_ns)
        e_end, e_c = E["end"][seen], E["c"][seen]
        if not len(e_c):
            continue
        f, L = r.fill, r.unit_loss
        x = (e_c * (1 - COST) - f * (1 + COST)) / L
        out.append({"r": r, "x": x, "px": e_c})
    return out


def gate(paths, X: float) -> dict:
    """Real-close delta: exit at the FIRST post-arm close <= X, priced at
    that close. Unfired trades keep their B0 result."""
    dg = de = 0.0
    gt = et = 0
    per = {w: 0.0 for w in WINS}
    alls = []
    for p in paths:
        r = p["r"]
        hit = np.nonzero(p["x"] <= X)[0]
        if not hit.size:
            continue
        j = int(hit[0])
        new_net = p["x"][j] * r.unit_loss * r.qty
        delta = new_net - r.net_pnl
        alls.append(delta)
        per[r.win] += delta
        if r.golden:
            dg += delta
            gt += 1
        elif r.em:
            de += delta
            et += 1
    tot = dg + de
    top = max(alls) if alls else 0.0
    npos = sum(1 for v in per.values() if v > 0)
    return {"X": X, "g_touched": gt, "g_delta": round(dg, 2),
            "e_saved": et, "e_delta": round(de, 2),
            "total": round(tot, 2), "ex_top1": round(tot - top, 2),
            "windows_pos": npos,
            "per_win": {k: round(v, 2) for k, v in per.items()}}


def part1a(t, data):
    paths = arm_paths(t, data)
    print("## 1A. C4 plateau — CORRECTED real-close exit math\n")
    print(f"armed trades with a post-arm path **{len(paths)}**\n")
    print("| X | Golden touched | Δ Golden $ | EM saved | Δ EM $ | "
          "Δ total $ | Ex-Top-1 $ | Pos win/5 |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|")
    rows = []
    for X in XGRID:
        g = gate(paths, X)
        rows.append(g)
        print(f"| {X:+.2f}x | **{g['g_touched']}** | {g['g_delta']:+.2f} | "
              f"{g['e_saved']} | {g['e_delta']:+.2f} | "
              f"**{g['total']:+.2f}** | {g['ex_top1']:+.2f} | "
              f"{g['windows_pos']}/5 |")
    print()
    print("Per-window detail:\n")
    print("| X | " + " | ".join(WINS) + " |")
    print("|---|" + "---:|" * len(WINS))
    for g in rows:
        print(f"| {g['X']:+.2f}x | " +
              " | ".join(f"{g['per_win'][w]:+.2f}" for w in WINS) + " |")
    print()
    # plateau verdict
    good = [g for g in rows if g["windows_pos"] >= 5 and g["total"] > 0]
    print(f"**Cells with positive delta in 5/5 windows: {len(good)}**\n")
    if good:
        print("| X | Δ total | Ex-Top-1 |")
        print("|---|---:|---:|")
        for g in good:
            print(f"| {g['X']:+.2f}x | {g['total']:+.2f} | "
                  f"{g['ex_top1']:+.2f} |")
        print()
    return {"rows": rows, "armed": len(paths)}


# ================================================================== #
def part1b(t, data):
    """What happens to price AFTER each SHIELD_BE exit."""
    be = t[t.exit_reason.isin(["SHIELD_BE", "BREAKEVEN"])].copy()
    print("## 1B. Post-exit autopsy of the SHIELD_BE trades\n")
    print(f"`SHIELD_BE`/`BREAKEVEN` exits: **{len(be)}** · net "
          f"**{be.net_pnl.sum():+.2f}$**\n")
    H24 = 24 * 3.6e12
    H48 = 48 * 3.6e12
    rows = []
    for r in be.itertuples(index=False):
        D = data[r.symbol]
        ns = D["ns"]
        f, L = r.fill, r.unit_loss

        def X_of(px):
            return (px * (1 - COST) - f * (1 + COST)) / L

        j0 = int(np.searchsorted(ns, r.exit_ns, "left"))
        j24 = int(np.searchsorted(ns, r.exit_ns + H24, "right"))
        j48 = int(np.searchsorted(ns, r.exit_ns + H48, "right"))
        if j48 <= j0:
            continue
        seg = slice(j0, j48)
        hi48 = D["h"][seg]
        lo48 = D["l"][seg]
        xh = X_of(hi48)
        xl = X_of(lo48)
        xh24 = X_of(D["h"][j0:j24]) if j24 > j0 else np.array([])
        # does price break orig_stop (-1.0x) later, and WHEN relative to a
        # +2x/+3x print
        broke_stop = bool((xl <= -1.0).any())
        first_stop = (int(np.argmax(xl <= -1.0))
                      if broke_stop else 10 ** 9)
        rec = {"symbol": r.symbol, "entry_time": r.entry_time,
               "net": float(r.net_pnl), "risk_pct": float(r.risk_pct),
               "max48": float(xh.max()), "min48": float(xl.min()),
               "max24": float(xh24.max()) if xh24.size else np.nan,
               "broke_stop": broke_stop, "first_stop": first_stop}
        for th in (2.0, 3.0, 5.0):
            hit = np.nonzero(xh >= th)[0]
            rec[f"t{int(th*10):02d}"] = int(hit[0]) if hit.size else 10 ** 9
        rows.append(rec)
    d = pd.DataFrame(rows)
    d.to_csv(RES / "_v50_shield_post.csv", index=False)
    n = len(d)
    # ---- the three buckets the mission asks for ---------------------
    reached2 = d["t20"] < 10 ** 9
    reached3 = d["t30"] < 10 ** 9
    reached5 = d["t50"] < 10 ** 9
    stop_first = d["broke_stop"] & (d["first_stop"] < d["t20"])
    premature = reached2 & (~d["broke_stop"] | (d["t20"] < d["first_stop"]))
    print("### 1B.1 What price did in the 48h after the 0.00x exit\n")
    print("| outcome after the exit | n | % | median max_X_48h |")
    print("|---|---:|---:|---:|")
    def line(lab, mask):
        s = d[mask]
        print(f"| {lab} | {len(s)} | {len(s)/n*100:.1f}% | "
              f"{s.max48.median():+.2f}x |" if len(s) else
              f"| {lab} | 0 | 0.0% | — |")
    line("**a. Premature shakeout** — reached +2.0x without breaking "
         "orig_stop", premature)
    line("reached +3.0x (would re-arm floor_line)", reached3 & ~stop_first)
    line("reached +5.0x", reached5 & ~stop_first)
    line("**c. True save** — broke orig_stop without ever reaching +2.0x",
         stop_first & ~reached2)
    line("b. broke stop but had reached +2.0x first",
         d.broke_stop & reached2)
    line("never reached +2.0x and never broke stop",
         ~reached2 & ~d.broke_stop)
    print()
    print(f"* median max_X over 48h = **{d.max48.median():+.2f}x** · "
          f"median min_X = **{d.min48.median():+.2f}x**\n")
    # ---- 1B.3 breathing room static test ---------------------------
    print("### 1B.2 Static test — give SHIELD_BE breathing room\n")
    print("Instead of exiting at 0.00x, let the trade run until it either "
          "closes at/below Xb, or hits +3.0x (floor_line).\n")
    print("| Xb | saved to golden (+3x) | kept as loss at Xb | "
      "Δ net $ | Ex-Top-1 $ |")
    print("|---|---:|---:|---:|---:|")
    br_rows = []
    # we need the in-trade path; approximate with the 48h forward window
    # measured from the SHIELD_BE exit itself (the trade WAS still open at
    # 0.00x -- the shield closed it -- so the forward tape is exactly the
    # path the trade would have lived through).
    for Xb in (-0.15, -0.20, -0.25, -0.30):
        tot = 0.0
        n_gold = n_loss = 0
        per_trade = []
        for r in be.itertuples(index=False):
            D = data[r.symbol]
            ns = D["ns"]
            f, L, q = r.fill, r.unit_loss, r.qty

            def X_of(px):
                return (px * (1 - COST) - f * (1 + COST)) / L

            j0 = int(np.searchsorted(ns, r.exit_ns, "left"))
            j48 = int(np.searchsorted(ns, r.exit_ns + H48, "right"))
            if j48 <= j0:
                continue
            tf = A.TF_NS[r.exec_tf]
            E = A.exec_closes(D, r.exit_ns, r.exit_ns + H48, tf)
            if E is None or not len(E["c"]):
                continue
            xc = X_of(E["c"])
            xh = X_of(D["h"][j0:j48])
            jg = np.nonzero(xh >= 3.0)[0]
            jl = np.nonzero(xc <= Xb)[0]
            # simplest causal comparison: whichever comes first, by 5m index
            idx_g = int(jg[0]) if jg.size else 10 ** 9
            # find the exec bar that closes <= Xb, and its position in 5m
            if jl.size:
                t_l_end = E["end"][jl[0]]
                idx_l = int(np.searchsorted(ns, t_l_end, "left")) - j0
            else:
                idx_l = 10 ** 9
            if idx_g <= idx_l:
                new = 3.0 * L * q
                n_gold += 1
            elif idx_l < 10 ** 9:
                new = Xb * L * q
                n_loss += 1
            else:
                new = r.net_pnl        # unchanged (48h window exhausted)
            per_trade.append(new - r.net_pnl)
        tot = float(np.sum(per_trade)) if per_trade else 0.0
        top = float(np.max(per_trade)) if per_trade else 0.0
        br_rows.append({"Xb": Xb, "gold": n_gold, "loss": n_loss,
                        "total": round(tot, 2),
                        "ex_top1": round(tot - top, 2)})
        print(f"| {Xb:+.2f}x | {n_gold} | {n_loss} | **{tot:+.2f}** | "
              f"{tot-top:+.2f} |")
    print()
    print("**Reading.** A \"premature shakeout\" bucket only has value if "
          "letting the trade live longer actually pays. The two numbers "
          "that matter are the golden count (it became a +3R winner) and "
          "the net delta.\n")
    return {"n": n, "premature": int(premature.sum()),
            "true_save": int((stop_first & ~reached2).sum()),
            "med_max48": round(float(d.max48.median()), 2),
            "br": br_rows}


# ================================================================== #
def part1c(t, data):
    """Bar-0 / Bar-1 entry reaction."""
    rows = []
    for r in t.itertuples(index=False):
        D = data[r.symbol]
        tf = A.TF_NS[r.exec_tf]
        E = A.exec_closes(D, r.entry_ns, r.exit_ns, tf)
        if E is None or not len(E["c"]):
            continue
        f, L = r.fill, r.unit_loss

        def X_of(px):
            return (px * (1 - COST) - f * (1 + COST)) / L

        n = min(2, len(E["c"]))
        xc = X_of(E["c"][:n])
        xh = X_of(E["h"][:n])
        xl = X_of(E["l"][:n])
        rec = {"tier": ("Golden_110" if r.golden else
                        ("EM_99" if r.em else
                         ("BE_452" if r.be else "Other_512"))),
               "bar0_close": float(xc[0]) if n >= 1 else np.nan,
               "bar1_close": float(xc[1]) if n >= 2 else np.nan,
               "max_bar0_1": float(xh.max()),
               "min_bar0_1": float(xl.min()),
               "net": float(r.net_pnl)}
        rows.append(rec)
    d = pd.DataFrame(rows)
    d.to_csv(RES / "_v50_bar01.csv", index=False)
    print("## 1C. Bar-0 / Bar-1 entry-candle reaction\n")
    print("| tier | n | median bar0 close | median bar1 close | "
          "median max(bar0,bar1) | median min(bar0,bar1) |")
    print("|---|---:|---:|---:|---:|---:|")
    for tier in ("Golden_110", "EM_99", "BE_452", "Other_512"):
        s = d[d.tier == tier]
        if not len(s):
            continue
        print(f"| {tier} | {len(s)} | {s.bar0_close.median():+.3f}x | "
              f"{s.bar1_close.median():+.3f}x | "
              f"{s.max_bar0_1.median():+.3f}x | "
              f"{s.min_bar0_1.median():+.3f}x |")
    print()
    # ---- the falling-knife bucket the mission specifies --------------
    print("### 1C.1 The falling-knife bucket\n")
    print("Rule: by the close of Bar 1, `max_high_X < +0.15x` AND "
          "`close_X <= -0.55x` — never bounced a tick off the seam and "
          "already halfway to -1R.\n")
    knife = (d.max_bar0_1 < 0.15) & (d.bar1_close <= -0.55)
    print("| tier | n | in the knife bucket | share |")
    print("|---|---:|---:|---:|")
    for tier in ("Golden_110", "EM_99", "BE_452", "Other_512"):
        s = d[d.tier == tier]
        if not len(s):
            continue
        k = int((knife & (d.tier == tier)).sum())
        print(f"| {tier} | {len(s)} | **{k}** | {k/len(s)*100:.1f}% |")
    print()
    # sweep adjacent thresholds for a plateau
    print("### 1C.2 Threshold sweep (Golden touched vs Other caught)\n")
    print("| max_hi < | close <= | Golden caught | EM caught | BE caught | "
          "Other caught | Δ net $ | Ex-Top-1 $ |")
    print("|---|---|---:|---:|---:|---:|")
    sweep = []
    for mh in (0.10, 0.15, 0.20, 0.25, 0.30):
        for cl in (-0.45, -0.55, -0.65):
            m = (d.max_bar0_1 < mh) & (d.bar1_close <= cl)
            if not m.any():
                continue
            g = int((m & (d.tier == "Golden_110")).sum())
            e = int((m & (d.tier == "EM_99")).sum())
            b = int((m & (d.tier == "BE_452")).sum())
            o = int((m & (d.tier == "Other_512")).sum())
            # exit at the bar1 close instead of the real outcome
            new = np.where(m, d.bar1_close * 0 + 0, d.net)
            # true_X at bar1 close is the price we exit at; convert via net
            delta = float(((-1.0 * 0)) + 0)
            # we cannot rebuild $ from X without size, so use the measured
            # per-tier average loss instead: report counts only here and
            # let the engine arm decide the dollars.
            print(f"| {mh:.2f} | {cl:.2f} | {g} | {e} | {b} | {o} | — | — |")
            sweep.append({"max_hi": mh, "close": cl, "g": g, "e": e,
                          "b": b, "o": o})
    print()
    print("**Note on dollars.** The static dollar effect of a Bar-1 exit "
          "needs the position size, which the B0 CSV carries (`qty0`) but "
          "the bar-1 close price in true_X must be multiplied by unit_loss. "
          "Section 4 tests the surviving thresholds on the real engine, "
          "where size and fills are exact.\n")
    return {"knife": {tier: int((knife & (d.tier == tier)).sum())
                      for tier in ("Golden_110", "EM_99", "BE_452",
                                   "Other_512")},
            "sweep": sweep}


# ================================================================== #
def main() -> int:
    t0 = time.time()
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    print(f"# v50 STAGE 1 — C4 plateau, SHIELD_BE autopsy, bar-0/1 anatomy "
          f"({time.time()-t0:.1f}s, ZERO engine runs)\n")
    t = A.load_tape()
    data = {s: A.load_5m(s) for s in A.SYMS}
    t = A.measure(t, data)
    print(f"book **{len(t)}** trades · net **${t.net_pnl.sum():+.2f}** · "
          f"Golden {int(t.golden.sum())} · EM {int(t.em.sum())} · "
          f"BE {int(t.be.sum())} · Other {int(t.other.sum())}\n")
    out = {}
    if which in ("all", "1a"):
        out["1a"] = part1a(t, data)
    if which in ("all", "1b"):
        out["1b"] = part1b(t, data)
    if which in ("all", "1c"):
        out["1c"] = part1c(t, data)
    (RES / "_v50_stage1.json").write_text(json.dumps(out, indent=1,
                                                     default=str))
    print(f"_total {time.time()-t0:.2f}s_")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
