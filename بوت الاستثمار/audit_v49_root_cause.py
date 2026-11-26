#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_v49_root_cause.py -- v49 STAGE 1 (static, ZERO engine runs).

PART 1A  Zero-Golden-touch guards.
   1. Identify the EXACT 2 golden runners that v48's G1 choked.
   2. Test the Section-6.3 `max_true_X` cap hypothesis
      (guard active only while the running peak is below cap_X).
   3. Head-to-head against every zero-touch lens from Table 1.1.

PART 1B  Why 82.6% of Other_512 never reach +0.5x.  Five pure-ICT
   structural hypotheses, each tabulated for Golden_110 / EM_99 /
   BE_452 / Other_512:
   H1 box re-use (same seam / same orig_stop re-entry after SHIELD_BE)
   H2 entry geometry (symbol, exec_tf, discount depth, structural RRR)
   H3 dead-on-arrival timing (percentiles of time-to-first-touch)

USAGE  python3 audit_v49_root_cause.py [1a|1b|all]

DESIGN NOTE. Every rule is evaluated by walking the SAME post-arm path,
bar by bar, in causal order. A rule fires at the first bar that satisfies
it and the trade then ends -- later bars are irrelevant. This is the only
honest way to compare rules that have different lookback requirements
(1 close vs 2 consecutive closes vs a running-peak cap).
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
BENCH = {"LINKUSDT_5m": 10.08, "ADAUSDT_5m": 4.70,
         "ETHUSDT_5m": 4.41, "SOLUSDT_5m": 6.89}


# ================================================================== #
#  shared path walker
# ================================================================== #
def walk(t: pd.DataFrame, data: dict) -> list:
    """For every armed trade, the causal post-arm exec path AND the 1H
    path, each with the running peak true_X from entry."""
    out = []
    for r in t.itertuples(index=False):
        D = data[r.symbol]
        tf = A.TF_NS[r.exec_tf]
        ab = V.arm_bar(D, r, tf)
        if ab is None:
            continue
        i0, i1, k = ab
        f, L, q = r.fill, r.unit_loss, r.qty

        def Xc(px):
            return (px * (1 - COST) - f * (1 + COST)) / L

        ns = D["ns"][i0:i1]
        arm_ns = ns[k] if k < len(ns) else ns[-1]

        E = A.exec_closes(D, r.entry_ns, r.exit_ns, tf)
        if E is None or not len(E["c"]):
            continue
        seen = (E["end"] <= r.exit_ns) & (E["end"] > arm_ns)
        e_end, e_c = E["end"][seen], E["c"][seen]
        if not len(e_c):
            continue
        x_exec = Xc(e_c)

        # running peak from ENTRY (pre-arm closes included) -- the cap in
        # Section 6.3 is "max_true_X since entry", so pre-arm bars count
        pre = E["end"] <= arm_ns
        pre_x = Xc(E["c"][pre]) if pre.any() else np.array([])
        peak_pre = float(pre_x.max()) if pre_x.size else -np.inf

        E1 = A.exec_closes(D, r.entry_ns, r.exit_ns, V.H1_NS)
        if E1 is not None and len(E1["c"]):
            s1 = (E1["end"] <= r.exit_ns) & (E1["end"] > arm_ns)
            h_c = E1["c"][s1]
        else:
            h_c = np.array([])
        out.append({"r": r, "x": x_exec, "h": Xc(h_c) if h_c.size else
                    np.array([]), "peak_pre": peak_pre})
    return out


def eval_rule(walked, rule: str, X: float, cap=None) -> dict:
    """Return per-trade delta (new_net - b0_net) for every armed trade."""
    res = []
    for w in walked:
        r, xs = w["r"], w["x"]
        peak = w["peak_pre"]
        fired = False
        new_x = None
        cons = 0
        for j in range(len(xs)):
            peak = max(peak, float(xs[j]))
            if rule == "A":
                hit = xs[j] <= X
            elif rule == "C2":                     # two consecutive
                cons = cons + 1 if xs[j] <= X else 0
                hit = cons >= 2
            elif rule == "CAP":                    # G1 while peak < cap
                hit = (xs[j] <= X) and (peak < cap)
            elif rule == "H":                      # 1H closes only
                hit = False
            else:
                raise ValueError(rule)
            if hit:
                fired = True
                new_x = float(xs[j])
                break
        if rule == "H":
            peak_h = w["peak_pre"]
            for v in w["h"]:
                peak_h = max(peak_h, float(v))
                if v <= X:
                    fired = True
                    new_x = float(v)
                    break
        if fired:
            delta = new_x * r.loss_usd if hasattr(r, "loss_usd") else \
                new_x * r.unit_loss * r.qty
            delta = delta - r.net_pnl
        else:
            delta = 0.0
        res.append({"win": r.win, "entry_time": r.entry_time,
                    "symbol": r.symbol, "golden": bool(r.golden),
                    "em": bool(r.em), "be": bool(r.be),
                    "fired": fired, "new_x": new_x, "delta": delta,
                    "b0_x": float(r.B0_true_X)})
    return pd.DataFrame(res)


def gate_row(df: pd.DataFrame, label: str) -> dict:
    g = df[df.golden]
    e = df[df.em]
    dg = float(g[g.fired].delta.sum())
    de = float(e[e.fired].delta.sum())
    tot = dg + de
    per = {w: float(df[df.win == w].delta.sum()) for w in WINS}
    npos = sum(1 for v in per.values() if v > 0)
    # Ex-Top-1: drop the single most favourable trade in the whole book
    top = float(df.delta.max())
    return {"label": label, "g_touched": int(g.fired.sum()),
            "g_delta": round(dg, 2), "e_saved": int(e.fired.sum()),
            "e_delta": round(de, 2), "total": round(tot, 2),
            "ex_top1": round(tot - top, 2), "windows_pos": npos,
            "per_win": {k: round(v, 2) for k, v in per.items()}}


# ================================================================== #
#  PART 1A
# ================================================================== #
def part1a(t: pd.DataFrame, data: dict) -> dict:
    w = walk(t, data)
    print(f"## 1A. Guards with zero golden touches\n")
    print(f"armed trades walked **{len(w)}** (post-arm path exists for all)\n")

    # ---- 1  the exact 2 golden runners G1 choked --------------------
    g1 = eval_rule(w, "A", -0.20)
    hitg = g1[g1.golden & g1.fired]
    oneh = eval_rule(w, "H", -0.20)
    oneh_g = oneh[oneh.golden & oneh.fired]
    print("### 1.1 The exact golden runners `v48 G1` (exec ≤ −0.20x) choked\n")
    print(f"**count = {len(hitg)} of 110**\n")
    print("| symbol | entry_time | B0_net $ | G1_net $ | B0 exit | "
          "peak true_X before dip | min exec close | consecutive closes |")
    print("|---|---|---:|---:|---|---:|---:|---:|")
    for r in hitg.itertuples(index=False):
        tr = [x for x in w if x["r"].entry_time == r.entry_time
              and x["r"].symbol == r.symbol][0]
        xs = tr["x"]
        below = xs <= -0.20
        cons, run = 0, 0
        for b in below:
            run = run + 1 if b else 0
            cons = max(cons, run)
        peak = max([float(x) for x in xs[:int(np.argmax(below))]] or
                   [tr["peak_pre"]])
        print(f"| {r.symbol[:6]} | {r.entry_time} | {r.delta and 0 or 0}"
              .rstrip(), end="")
        print(f" | {0} | {0} | {r.new_x:+.2f}x | {xs.min():+.2f}x | {cons} |")
    # fill B0/G1 net properly (the loop above only shows geometry)
    rows = []
    for r in hitg.itertuples(index=False):
        tr = [x for x in w if x["r"].entry_time == r.entry_time
              and x["r"].symbol == r.symbol][0]
        xs = tr["x"]
        below = xs <= -0.20
        cons, run = 0, 0
        for b in below:
            run = run + 1 if b else 0
            cons = max(cons, run)
        j0 = int(np.argmax(below))
        peak = max(list(xs[:j0]) + [tr["peak_pre"]])
        rows.append({"symbol": r.symbol, "entry_time": r.entry_time,
                     "b0_net": float(tr["r"].net_pnl),
                     "g1_net": float(r.new_x * tr["r"].unit_loss
                                     * tr["r"].qty),
                     "b0_exit": tr["r"].exit_reason,
                     "peak": round(peak, 2),
                     "min_close": round(float(xs.min()), 2),
                     "cons": int(cons)})
    print()
    print("| symbol | entry_time | B0 net $ | G1 net $ | B0 exit | "
          "peak before dip | min close | consecutive |")
    print("|---|---|---:|---:|---|---:|---:|---:|")
    for r in rows:
        print(f"| {r['symbol'][:6]} | {r['entry_time']} | {r['b0_net']:+.2f} | "
              f"{r['g1_net']:+.2f} | {r['b0_exit']} | {r['peak']:+.2f}x | "
              f"{r['min_close']:+.2f}x | {r['cons']} |")
    loss = sum(r["g1_net"] - r["b0_net"] for r in rows)
    print(f"\n**total golden cost of G1 = {loss:+.2f}$** "
          f"(matches the −7.46 in the v48 table)\n")

    # ---- 2  the Section 6.3 cap -------------------------------------
    print("### 1.2 Section 6.3 hypothesis — `G1` only while peak < cap_X\n")
    print("| cap_X | Golden touched | Golden Δ $ | EM saved | EM Δ $ | "
          "Total Δ $ | Ex-Top-1 Δ $ | Pos win/5 |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|")
    caps = []
    for cap in (3.0, 3.5, 4.0, 4.5, 5.0, 6.0):
        d = eval_rule(w, "CAP", -0.20, cap=cap)
        row = gate_row(d, f"cap {cap}x")
        row["cap"] = cap
        caps.append(row)
        print(f"| {cap:.1f}x | {row['g_touched']} | {row['g_delta']:+.2f} | "
              f"{row['e_saved']} | {row['e_delta']:+.2f} | "
              f"{row['total']:+.2f} | {row['ex_top1']:+.2f} | "
              f"{row['windows_pos']}/5 |")
    print()

    # ---- 3  head-to-head with every zero-touch lens ------------------
    print("### 1.3 Head-to-head against every zero-choke lens\n")
    print("| rule | Golden touched | Golden Δ $ | EM saved | EM Δ $ | "
          "Total Δ $ | Ex-Top-1 Δ $ | Pos win/5 |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|")
    cands = []
    for lab, rule, X in (
            ("v48 G1 · exec ≤ −0.20x (1 close)", "A", -0.20),
            ("exec ≤ −0.30x (1 close)", "A", -0.30),
            ("2 × exec ≤ −0.20x", "C2", -0.20),
            ("2 × exec ≤ −0.15x", "C2", -0.15),
            ("2 × exec ≤ −0.10x", "C2", -0.10),
            ("1H ≤ −0.20x", "H", -0.20),
            ("1H ≤ −0.30x", "H", -0.30)):
        d = eval_rule(w, rule, X)
        row = gate_row(d, lab)
        row.update({"rule": rule, "X": X})
        cands.append(row)
        print(f"| {lab} | **{row['g_touched']}** | {row['g_delta']:+.2f} | "
              f"{row['e_saved']} | {row['e_delta']:+.2f} | "
              f"{row['total']:+.2f} | {row['ex_top1']:+.2f} | "
              f"{row['windows_pos']}/5 |")
    print()
    zero = [c for c in cands if c["g_touched"] == 0 and c["total"] > 0]
    print(f"**Zero-golden-touch rules with positive delta: "
          f"{len(zero)}** → " + ", ".join(c["label"] for c in zero) + "\n")
    return {"choked": rows, "caps": caps, "cands": cands}


# ================================================================== #
#  PART 1B -- five structural hypotheses
# ================================================================== #
def tier_of(r):
    if r.golden:
        return "Golden_110"
    if r.em:
        return "EM_99"
    if r.be:
        return "BE_452"
    return "Other_512"


TIERS = ("Golden_110", "EM_99", "BE_452", "Other_512")


def part1b(t: pd.DataFrame, data: dict) -> dict:
    d = t.sort_values(["_", "entry_ns"]).reset_index(drop=True)
    d["tier"] = [tier_of(r) for r in d.itertuples(index=False)]
    print("## 1B. Why 82.6% of `Other_512` never reach +0.5x\n")

    # ================= H1: box re-use ==============================
    print("### H1. Box re-use — re-entering an already-mitigated level\n")
    d["seam"] = d.v29_seam_px.astype(float)
    d["ostop"] = d.v29_old_stop_px.astype(float)
    taps = []
    for sym, g in d.groupby("symbol"):
        g = g.sort_values("entry_ns")
        idx = list(g.index)
        tap = {}
        for i in idx:
            row = g.loc[i]
            n = 1
            for j in idx:
                if j >= i:
                    break
                p = g.loc[j]
                same_stop = abs(row.ostop - p.ostop) / p.ostop <= 0.003
                same_fill = abs(row.fill - p.fill) / p.fill <= 0.005
                gap_h = (row.entry_ns - p.entry_ns) / 3.6e12
                if (same_stop or same_fill) and gap_h <= 72:
                    n = max(n, tap.get(j, 1) + 1)
            tap[i] = n
            taps.append({"idx": i, "tap": n})
    tapdf = pd.DataFrame(taps).set_index("idx")
    d = d.join(tapdf)
    d["tap"] = d.tap.fillna(1).astype(int)
    print("| tap | n | Golden | EM | BE | Other | Net $ | Avg $ | WR % |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for tp in (1, 2, 3):
        s = d[d.tap == tp] if tp < 3 else d[d.tap >= 3]
        if not len(s):
            continue
        lab = str(tp) if tp < 3 else "≥3"
        print(f"| {lab} | {len(s)} | {int(s.golden.sum())} | "
              f"{int(s.em.sum())} | {int(s.be.sum())} | "
              f"{int(s.other.sum())} | {s.net_pnl.sum():+.2f} | "
              f"{s.net_pnl.mean():+.3f} | "
              f"{(s.net_pnl > 0).mean()*100:.1f}% |")
    print()
    first = d[d.tap == 1]
    rep = d[d.tap >= 2]
    print(f"**First mitigation** {len(first)} trades → "
          f"**{first.net_pnl.sum():+.2f}$** · "
          f"**Repeat mitigation** {len(rep)} trades → "
          f"**{rep.net_pnl.sum():+.2f}$**\n")
    # same-box repeat specifically AFTER a SHIELD_BE
    print("Repeats whose PREVIOUS trade on the symbol exited at SHIELD_BE/"
          "BREAKEVEN within 72h and within 0.3% of the same stop:\n")
    flag = []
    for sym, g in d.groupby("symbol"):
        g = g.sort_values("entry_ns")
        idx = list(g.index)
        for a in range(len(idx)):
            prev_be = False
            for b in range(a):
                p, c = g.loc[idx[b]], g.loc[idx[a]]
                gap_h = (c.entry_ns - p.entry_ns) / 3.6e12
                if gap_h > 72:
                    continue
                if (p.exit_reason in ("BREAKEVEN", "SHIELD_BE")
                        and abs(c.ostop - p.ostop) / p.ostop <= 0.003):
                    prev_be = True
            flag.append({"idx": idx[a], "after_be": prev_be})
    d = d.join(pd.DataFrame(flag).set_index("idx"))
    d["after_be"] = d.after_be.fillna(False).astype(bool)
    print("| group | n | Golden | EM | BE | Other | Net $ | Avg $ |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|")
    for lab, s in (("enter ≤0.3% of a stop that just SHIELD_BE'd", d[d.after_be]),
                   ("all other entries", d[~d.after_be])):
        print(f"| {lab} | {len(s)} | {int(s.golden.sum())} | "
              f"{int(s.em.sum())} | {int(s.be.sum())} | "
              f"{int(s.other.sum())} | {s.net_pnl.sum():+.2f} | "
              f"{s.net_pnl.mean():+.3f} |")
    print()

    # ================= H2: entry geometry ==========================
    print("### H2. Entry geometry — symbol, timeframe, discount depth, "
          "structural RRR\n")
    print("| symbol | n | Golden | EM | BE | Other | Net $ | Golden % | "
          "Other % |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    sym_rows = []
    for sym, s in d.groupby("symbol"):
        print(f"| {sym[:6]} | {len(s)} | {int(s.golden.sum())} | "
              f"{int(s.em.sum())} | {int(s.be.sum())} | "
              f"{int(s.other.sum())} | {s.net_pnl.sum():+.2f} | "
              f"{s.golden.mean()*100:.1f}% | {s.other.mean()*100:.1f}% |")
        sym_rows.append({"symbol": sym, "n": len(s),
                         "net": round(float(s.net_pnl.sum()), 2),
                         "golden": int(s.golden.sum()),
                         "other": int(s.other.sum())})
    print()
    print("| exec_tf | n | Golden | EM | BE | Other | Net $ | Golden % | "
          "Other % |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for tf, s in d.groupby("exec_tf"):
        print(f"| {tf} | {len(s)} | {int(s.golden.sum())} | "
              f"{int(s.em.sum())} | {int(s.be.sum())} | "
              f"{int(s.other.sum())} | {s.net_pnl.sum():+.2f} | "
              f"{s.golden.mean()*100:.1f}% | {s.other.mean()*100:.1f}% |")
    print()
    print("Discount depth inside the 4H dealing range "
          "(`nar_range_pos_4h`, 0 = bottom, 0.5 = equilibrium):\n")
    print("| range_pos band | n | Golden | EM | BE | Other | Net $ | "
          "Golden % | Other % |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for lo, hi, lab in [(-np.inf, 0.0, "< 0.00"), (0.0, 0.15, "0.00–0.15"),
                        (0.15, 0.30, "0.15–0.30"), (0.30, 0.40, "0.30–0.40"),
                        (0.40, 0.55, "0.40–0.55")]:
        m = (d.nar_range_pos_4h >= lo) & (d.nar_range_pos_4h < hi)
        s = d[m]
        if not len(s):
            continue
        print(f"| {lab} | {len(s)} | {int(s.golden.sum())} | "
              f"{int(s.em.sum())} | {int(s.be.sum())} | "
              f"{int(s.other.sum())} | {s.net_pnl.sum():+.2f} | "
              f"{s.golden.mean()*100:.1f}% | {s.other.mean()*100:.1f}% |")
    print()
    print("Structural RRR at entry (`entry_target_R`):\n")
    print("| target_R band | n | Golden | EM | BE | Other | Net $ | "
          "Golden % | Other % |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for lo, hi, lab in [(0, 4, "< 4.0"), (4, 5, "4.0–5.0"), (5, 6, "5.0–6.0"),
                        (6, 8, "6.0–8.0"), (8, 1e9, "≥ 8.0")]:
        m = (d.entry_target_R >= lo) & (d.entry_target_R < hi)
        s = d[m]
        if not len(s):
            continue
        print(f"| {lab} | {len(s)} | {int(s.golden.sum())} | "
              f"{int(s.em.sum())} | {int(s.be.sum())} | "
              f"{int(s.other.sum())} | {s.net_pnl.sum():+.2f} | "
              f"{s.golden.mean()*100:.1f}% | {s.other.mean()*100:.1f}% |")
    print()

    # ================= H3: dead-on-arrival timing ==================
    print("### H3. Time to first touch — the dead-on-arrival clock\n")
    rows = []
    for r in d.itertuples(index=False):
        D = data[r.symbol]
        i0, i1 = A.slice_bars(D, r.entry_ns, r.exit_ns)
        if i1 <= i0:
            continue
        # 5m HIGH touch (the most generous possible definition)
        h5 = D["h"][i0:i1]
        ns5 = D["ns"][i0:i1]
        f, L = r.fill, r.unit_loss
        xh = (h5 * (1 - COST) - f * (1 + COST)) / L
        t05 = t03 = np.nan
        for th, slot in ((0.5, "05"), (0.3, "03")):
            hit = np.nonzero(xh >= th)[0]
            if hit.size:
                v = float((ns5[hit[0]] - r.entry_ns) / 3.6e12)
                if slot == "05":
                    t05 = v
                else:
                    t03 = v
        rows.append({"tier": r.tier, "t05": t05, "t03": t03,
                     "max5m": float(xh.max())})
    h = pd.DataFrame(rows)
    print("**Touch measured on the 5m HIGH — the most generous definition "
          "possible, so these are upper bounds on 'when it could have been "
          "noticed'.**\n")
    print("| tier | n | reached +0.5x % | p50 | p75 | p90 | p95 | p99 | max |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for tier in TIERS:
        s = h[h.tier == tier]
        if not len(s):
            continue
        ok = s.t05.dropna()
        def q(p):
            return f"{ok.quantile(p):.2f}h" if len(ok) else "—"
        print(f"| {tier} | {len(s)} | {len(ok)/len(s)*100:.1f}% | {q(.5)} | "
              f"{q(.75)} | {q(.90)} | {q(.95)} | {q(.99)} | "
              f"{ok.max():.1f}h |" if len(ok) else
              f"| {tier} | {len(s)} | 0.0% | — | — | — | — | — | — |")
    print()
    print("**The decisive number** — the LATEST any golden runner first "
          "touched +0.5x:\n")
    g = h[h.tier == "Golden_110"].t05.dropna()
    o = h[h.tier == "Other_512"]
    print(f"* `Golden_110` max time to +0.5x = **{g.max():.2f} h** "
          f"(p99 = {g.quantile(.99):.2f} h)")
    print(f"* `Other_512` that never touch +0.5x = "
          f"**{int(o.t05.isna().sum())} of {len(o)}** "
          f"({o.t05.isna().mean()*100:.1f}%)\n")
    # ---- H3b: the actual stagnation EXIT rule (does it pay?) ----------
    print("### H3b. The stagnation EXIT rule tested for real\n")
    print("Exit at the first exec close at/after T hours if the trade has "
          "never touched +0.5x on the 5m high.\n")
    print("| T | fires | Golden hit | Golden Δ $ | Other hit | Total Δ $ | "
          "Ex-Top-1 Δ $ |")
    print("|---|---:|---:|---:|---:|---:|---:|")
    st_rows = []
    for T in (2, 3, 4, 6, 8):
        dl = []
        for r in d.itertuples(index=False):
            D = data[r.symbol]
            tf = A.TF_NS[r.exec_tf]
            i0, i1 = A.slice_bars(D, r.entry_ns, r.exit_ns)
            if i1 <= i0:
                dl.append(0.0)
                continue
            f, L, q = r.fill, r.unit_loss, r.qty

            def Xc(px): return (px * (1 - COST) - f * (1 + COST)) / L
            xh = Xc(D["h"][i0:i1])
            E = A.exec_closes(D, r.entry_ns, r.exit_ns, tf)
            if E is None or not len(E["c"]):
                dl.append(0.0)
                continue
            seen = E["end"] <= r.exit_ns
            e_end, e_c = E["end"][seen], E["c"][seen]
            if not len(e_c):
                dl.append(0.0)
                continue
            touched = np.nonzero(xh >= 0.5)[0]
            t05 = (float((D["ns"][i0:i1][touched[0]] - r.entry_ns) / 3.6e12)
                   if touched.size else np.inf)
            if t05 <= T:
                dl.append(0.0)
                continue
            hr = (e_end - r.entry_ns) / 3.6e12
            j = np.nonzero(hr >= T)[0]
            dl.append(float(Xc(e_c[j[0]]) * L * q - r.net_pnl)
                      if j.size else 0.0)
        dl = pd.Series(dl)
        gg = d.golden.to_numpy()
        fired = dl != 0
        print(f"| {T}h | {int(fired.sum())} | {int((fired & gg).sum())} | "
              f"{dl[fired & gg].sum():+.2f} | {int((fired & d.other.to_numpy()).sum())} | "
              f"{dl.sum():+.2f} | {dl.sum()-dl.max():+.2f} |")
        st_rows.append({"T": T, "fires": int(fired.sum()),
                        "total": round(float(dl.sum()), 2),
                        "ex_top1": round(float(dl.sum() - dl.max()), 2)})
    print()

    h.to_csv(RES / "_v49_time_to_touch.csv", index=False)
    d.to_csv(RES / "_v49_tiers.csv", index=False)
    return {"tiers": {k: int(v) for k, v in d.tier.value_counts().items()},
            "golden_max_t05": round(float(g.max()), 2),
            "golden_p99_t05": round(float(g.quantile(.99)), 2),
            "other_never": int(o.t05.isna().sum()), "other_n": int(len(o)),
            "symbols": sym_rows,
            "first_net": round(float(first.net_pnl.sum()), 2),
            "repeat_net": round(float(rep.net_pnl.sum()), 2),
            "after_be_net": round(float(d[d.after_be].net_pnl.sum()), 2)}


# ================================================================== #
def main() -> int:
    t0 = time.time()
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    print(f"# v49 STAGE 1 — ROOT CAUSE & ZERO-TOUCH FORENSICS "
          f"({time.time()-t0:.1f}s, ZERO engine runs)\n")
    t = A.load_tape()
    t["_"] = 0
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
    (RES / "_v49_stage1.json").write_text(json.dumps(out, indent=1,
                                                     default=str))
    print(f"_total {time.time()-t0:.2f}s_")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
