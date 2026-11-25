#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_v48_zero_choke.py -- v48 STAGE 1 (static, ZERO engine runs).

PART 1A  Ultra-safe `floor_only` guards: X in [-0.30 .. +0.30] across
         Lens A (exec_tf close), Lens B (1H close), Lens C (2 exec_tf
         closes IN A ROW). For every (lens, X) we report exactly the two
         numbers the mission asks for:
             Golden_110_Touched  -- how many of the 110 armed golden
                                    runners the guard would clip
             EM_99_Saved         -- how many of the 99 armed EMERGENCY_STOP
                                    losers the guard would cut short
         plus the dollar effect of replacing those exits at X, the
         Ex-Top-1 robustness check, the per-window sign, and whether the
         four benchmark runners survive.

PART 1B  Forensic anatomy of the 962 trades that never arm floor_line:
         Other_512 (-$422.48) vs BE_452 (-$0.42) vs Golden_110.
         time-to-+0.5x, max true_X in the first 4h/8h/12h, pre-arm peak
         decay, and entry characteristics (exec_tf, risk_pct deciles).

USAGE  python3 audit_v48_zero_choke.py [1a|1b|all]
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
X_GRID = [-0.30, -0.20, -0.10, 0.00, 0.10, 0.20, 0.30]
WINS = ("W1", "W2", "OLD7", "MOD_Y1", "MOD_Y2")

# the four benchmark runners the mission demands we preserve
BENCH = [("2024-01-13 02:05", "LINKUSDT_5m", 10.08),
         ("2024-01-01 03:45", "ADAUSDT_5m", 4.70),
         ("2024-01-08 05:15", "ETHUSDT_5m", 4.41),
         ("2026-01-01 16:30", "SOLUSDT_5m", 6.89)]


# ================================================================== #
# PART 1A -- ultra-safe guards
# ================================================================== #
def floor_path(t: pd.DataFrame, data: dict) -> pd.DataFrame:
    """Walk each armed trade bar by bar from the arm to the real exit and
    record, for every (lens, X), whether the guard would have fired and at
    what true_X the trade would then have been closed.

    Firing rules (all strictly INSIDE the floor_only window, i.e. only
    after the exec frame first CLOSES at/above floor_line):
        A: one exec_tf close <= X
        B: one closed 1H candle <= X
        C: two exec_tf closes IN A ROW <= X
    Once fired the trade is over -- later bars are irrelevant, because the
    engine would have left the position.
    """
    rows = []
    for r in t.itertuples(index=False):
        D = data[r.symbol]
        tf = A.TF_NS[r.exec_tf]
        ab = V.arm_bar(D, r, tf)
        if ab is None:
            continue
        i0, i1, k = ab
        f, L, q = r.fill, r.unit_loss, r.qty

        def Xc(px): return (px * (1 - COST) - f * (1 + COST)) / L

        ns = D["ns"][i0:i1]
        c5 = D["c"][i0:i1]
        # ---- exec_tf closes, only bars the engine actually SAW ----------
        E = A.exec_closes(D, r.entry_ns, r.exit_ns, tf)
        if E is None or not len(E["c"]):
            continue
        # ---- ONLY bars after the arm: the guard lives inside floor_only -
        # The arm bar itself is the first exec close at/above floor_line;
        # everything before it is pre-floor and belongs to B0 untouched.
        arm_ns = ns[k] if k < len(ns) else ns[-1]
        seen = (E["end"] <= r.exit_ns) & (E["end"] > arm_ns)
        e_end, e_c = E["end"][seen], E["c"][seen]
        if not len(e_c):
            continue
        # ---- 1H closes, same causality + post-arm rule ------------------
        E1 = A.exec_closes(D, r.entry_ns, r.exit_ns, V.H1_NS)
        if E1 is not None and len(E1["c"]):
            s1 = (E1["end"] <= r.exit_ns) & (E1["end"] > arm_ns)
            h_end, h_c = E1["end"][s1], E1["c"][s1]
        else:
            h_end, h_c = np.array([]), np.array([])
        rec = {"win": r.win, "entry_time": r.entry_time, "symbol": r.symbol,
               "exec_tf": r.exec_tf, "golden": bool(r.golden),
               "em": bool(r.em), "be": bool(r.be), "other": bool(r.other),
               "net_pnl": float(r.net_pnl), "b0_x": float(r.B0_true_X),
               "loss_usd": float(r.unit_loss * r.qty),
               "risk_pct": float(r.risk_pct),
               "peak_x": float(Xc(max(float(np.max(c5)), float(r.exit_price)))),
               "max_x_after_arm": float(Xc(float(np.max(e_c))))}
        for X in X_GRID:
            px = V.px_at(f, r.stop, X)
            tag = f"{X:+.2f}"
            # ---- A: single exec close ----------------------------------
            a_hit = e_c <= px
            rec[f"A{tag}"] = (float(Xc(e_c[np.argmax(a_hit)]))
                              if a_hit.any() else np.nan)
            # ---- B: single 1H close ------------------------------------
            if len(h_c):
                b_hit = h_c <= px
                rec[f"B{tag}"] = (float(Xc(h_c[np.argmax(b_hit)]))
                                  if b_hit.any() else np.nan)
            else:
                rec[f"B{tag}"] = np.nan
            # ---- C: two exec closes in a row ---------------------------
            two = a_hit[:-1] & a_hit[1:] if a_hit.size > 1 else np.array([])
            if two.size and two.any():
                j = int(np.argmax(two)) + 1
                rec[f"C{tag}"] = float(Xc(e_c[j]))
            else:
                rec[f"C{tag}"] = np.nan
        rows.append(rec)
    return pd.DataFrame(rows)


def part1a(t: pd.DataFrame, data: dict) -> dict:
    p = floor_path(t, data)
    p.to_csv(RES / "_v48_guard_path.csv", index=False)
    g, e = p[p.golden], p[p.em]
    b0 = float(t.net_pnl.sum())
    out_rows = []
    print("## 1A. Ultra-safe `floor_only` guards — the zero-choke question\n")
    print(f"armed trades **{len(p)}** · Golden **{len(g)}** · "
          f"EM **{len(e)}** · Other **{len(p)-len(g)-len(e)}**\n")
    print("| Lens | X | Golden touched | Golden Δ $ | EM saved | EM Δ $ | "
          "Total Δ $ | Ex-Top1 Δ $ | Pos win/5 | LINK +10.08 | 4 runners |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|")
    for lens, lname in (("A", "exec_tf close"), ("B", "1H close"),
                        ("C", "2 × exec_tf close")):
        for X in X_GRID:
            col = f"{lens}{X:+.2f}"
            # ---- who does the guard touch? -----------------------------
            g_hit = g[col].notna()
            e_hit = e[col].notna()
            # dollars: replace the B0 exit by an exit AT X, same size
            def delta(df, hit):
                d = df[hit]
                return float(((X * d.loss_usd) - d.net_pnl).sum())
            dg = delta(g, g_hit)
            de = delta(e, e_hit)
            tot = dg + de
            # per-trade delta for Ex-Top-1 and per-window sign
            dl = pd.Series(0.0, index=p.index)
            for hit, df in ((g_hit, g), (e_hit, e)):
                s_ = df[hit]                      # ONLY the trades it fires on
                dd = X * s_.loss_usd - s_.net_pnl
                dl.loc[dd.index] = dd
            top = float(dl.max())
            per = {w: float(dl[p.win == w].sum()) for w in WINS}
            npos = sum(1 for v in per.values() if v > 0)
            # ---- the four benchmark runners ----------------------------
            def survives(when, sym):
                m = p[(p.entry_time.astype(str).str[:16] == when)
                      & (p.symbol == sym)]
                return (not len(m)) or bool(m[col].isna().all())
            link_ok = survives(BENCH[0][0], BENCH[0][1])
            n_all = sum(1 for when, sym, _ in BENCH if survives(when, sym))
            print(f"| {lname} | {X:+.2f}x | {int(g_hit.sum())} | {dg:+.2f} | "
                  f"{int(e_hit.sum())} | {de:+.2f} | {tot:+.2f} | "
                  f"{tot-top:+.2f} | {npos}/5 | "
                  f"{'yes' if link_ok else '**KILLED**'} | "
                  f"{n_all}/4 |")
            out_rows.append({"lens": lname, "X": X,
                             "g_touched": int(g_hit.sum()), "g_delta": round(dg, 2),
                             "e_saved": int(e_hit.sum()), "e_delta": round(de, 2),
                             "total": round(tot, 2),
                             "ex_top1": round(tot - top, 2),
                             "windows_pos": npos,
                             "link_ok": bool(link_ok), "runners_ok": n_all,
                             "per_win": {k: round(v, 2) for k, v in per.items()}})
    print()
    # ---- which cells are genuinely zero-choke? -------------------------
    ok = [r for r in out_rows if r["g_touched"] <= 3 and r["runners_ok"] == 4]
    print("### Zero-choke candidates (Golden touched ≤ 3 of 110 AND all 4 "
          "runners preserved)\n")
    if not ok:
        print("_none_\n")
    else:
        print("| Lens | X | Golden touched | EM saved | Total Δ $ | "
              "Ex-Top1 Δ $ | Pos win/5 |")
        print("|---|---:|---:|---:|---:|---:|---:|")
        for r in sorted(ok, key=lambda r: -r["total"]):
            print(f"| {r['lens']} | {r['X']:+.2f}x | {r['g_touched']} | "
                  f"{r['e_saved']} | {r['total']:+.2f} | {r['ex_top1']:+.2f} | "
                  f"{r['windows_pos']}/5 |")
        print()
    print(f"_B0 book on the armed subset: ${b0:+.2f} over {len(t)} trades_")
    return {"rows": out_rows, "armed": int(len(p)), "golden": int(len(g)),
            "em": int(len(e)), "b0": round(b0, 2)}


# ================================================================== #
# PART 1B -- forensic anatomy of the 962 non-arming trades
# ================================================================== #
TIER = [(-np.inf, 0.0, "Other_512"), (0.0, 1e-9, "BE_452"),
        (1e-9, np.inf, "Golden_110")]


def tier_of(r):
    if r.golden:
        return "Golden_110"
    if r.em:
        return "EM_99"
    if r.be:
        return "BE_452"
    return "Other_512"


def part1b(t: pd.DataFrame, data: dict) -> dict:
    # time to first +0.50x close, and the peak reached in the first N hours
    rows = []
    for r in t.itertuples(index=False):
        D = data[r.symbol]
        tf = A.TF_NS[r.exec_tf]
        i0, i1 = A.slice_bars(D, r.entry_ns, r.exit_ns)
        f, L = r.fill, r.unit_loss

        def Xc(px): return (px * (1 - COST) - f * (1 + COST)) / L
        E = A.exec_closes(D, r.entry_ns, r.exit_ns, tf)
        if E is None or not len(E["c"]):
            continue
        seen = E["end"] <= r.exit_ns
        e_end, e_c = E["end"][seen], E["c"][seen]
        if not len(e_c):
            continue
        Xe = Xc(e_c)
        hit = np.nonzero(Xe >= 0.5)[0]
        t05 = (float((e_end[hit[0]] - r.entry_ns) / 3.6e12)
               if hit.size else np.nan)
        rec = {"win": r.win, "entry_time": r.entry_time, "symbol": r.symbol,
               "exec_tf": r.exec_tf, "tier": tier_of(r),
               "risk_pct": float(r.risk_pct), "net_pnl": float(r.net_pnl),
               "b0_x": float(r.B0_true_X), "n_exec_bars": int(len(e_c)),
               "time_to_05x_h": t05}
        for H in (4, 8, 12):
            m = (e_end - r.entry_ns) <= H * 3.6e12
            rec[f"max_x_{H}h"] = float(Xe[m].max()) if m.any() else np.nan
            rec[f"bars_{H}h"] = int(m.sum())
        # how many exec bars printed before the trade first reached +0.5x
        rec["bars_without_05x"] = int(hit[0]) if hit.size else int(len(e_c))
        rows.append(rec)
    d = pd.DataFrame(rows)
    d.to_csv(RES / "_v48_tiers.csv", index=False)

    print("## 1B. Forensic anatomy of the trades that never arm `floor_line`\n")
    n = d.tier.value_counts()
    print("| tier | n | median time to +0.5x (h) | median bars to +0.5x | "
          "reached +0.5x % | median max_x_4h | median max_x_8h | "
          "median risk_pct |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|")
    for tier in ("Golden_110", "EM_99", "BE_452", "Other_512"):
        s = d[d.tier == tier]
        if not len(s):
            continue
        print(f"| {tier} | {len(s)} | {s.time_to_05x_h.median():.1f} | "
              f"{s.bars_without_05x.median():.0f} | "
              f"{s.time_to_05x_h.notna().mean()*100:.1f}% | "
              f"{s.max_x_4h.median():+.2f}x | {s.max_x_8h.median():+.2f}x | "
              f"{s.risk_pct.median():.2f}% |")
    print()

    # ---- 1B.2 pre-floor peak decay -----------------------------------
    be = d[d.tier == "BE_452"]
    print("### 1B.2 Pre-`floor_line` peak decay (the 452 BE trades)\n")
    print("| reached max true_X ≥ | BE_452 count | share | net $ of those |")
    print("|---|---:|---:|---:|")
    for th in (1.0, 1.5, 1.8, 2.0, 2.4, 2.8):
        s = be[be.max_x_12h >= th]
        print(f"| {th:.1f}x | {len(s)} | {len(s)/max(len(be),1)*100:.1f}% | "
              f"{s.net_pnl.sum():+.2f} |")
    print()
    g = d[d.tier == "Golden_110"]
    print("**The asymmetry the mission suspected** — how many Golden runners "
          "ducked below the guard threshold BEFORE running:\n")
    print("| Golden_110 that ... | count | share |")
    print("|---|---:|---:|")
    for th in (0.0, 0.2, 0.5):
        s = g[g.max_x_12h.notna()]
        print(f"| never reached +{th:.1f}x in the first 12h | "
              f"{int((s.max_x_12h < th).sum())} | "
              f"{(s.max_x_12h < th).mean()*100:.1f}% |")
    print()

    # ---- 1B.3 entry characteristics ----------------------------------
    print("### 1B.3 Entry characteristics\n")
    print("| tier | 5min | 15min | 30min | 1h |")
    print("|---|---:|---:|---:|---:|")
    for tier in ("Golden_110", "EM_99", "BE_452", "Other_512"):
        s = d[d.tier == tier]
        if not len(s):
            continue
        v = s.exec_tf.value_counts()
        print(f"| {tier} | {v.get('5min',0)} | {v.get('15min',0)} | "
              f"{v.get('30min',0)} | {v.get('1h',0)} |")
    print()
    print("| risk_pct band | Golden_110 | EM_99 | BE_452 | Other_512 | "
          "Golden win % | Other win % |")
    print("|---|---:|---:|---:|---:|---:|---:|")
    bands = [(-np.inf, 0.35, "< 0.35%"), (0.35, 0.60, "0.35–0.60%"),
             (0.60, 1.00, "0.60–1.00%"), (1.00, 1.80, "1.00–1.80%"),
             (1.80, np.inf, "> 1.80%")]
    for lo, hi, lab in bands:
        m = (d.risk_pct >= lo) & (d.risk_pct < hi)
        gg = d[m & (d.tier == "Golden_110")]
        oo = d[m & (d.tier == "Other_512")]
        print(f"| {lab} | {len(gg)} | {int((m & (d.tier=='EM_99')).sum())} | "
              f"{int((m & (d.tier=='BE_452')).sum())} | {len(oo)} | "
              f"{(gg.b0_x >= 3).mean()*100:.1f}% | "
              f"{(oo.b0_x >= 3).mean()*100:.1f}% |")
    print()
    return {"tiers": {k: int(v) for k, v in n.items()}}


# ================================================================== #
def main() -> int:
    t0 = time.time()
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    print(f"# v48 STAGE 1 — ZERO-CHOKE GUARD & TIER FORENSICS "
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
    (RES / "_v48_stage1.json").write_text(json.dumps(out, indent=1,
                                                     default=str))
    print(f"_total {time.time()-t0:.2f}s_")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
