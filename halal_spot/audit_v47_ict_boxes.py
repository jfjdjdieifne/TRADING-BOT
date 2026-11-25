#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_v47_ict_boxes.py -- v47 STAGE 1 (< 10 s, ZERO engine runs).

PART 1A  re-entry / streak anatomy on the 1,173 saved B0 trades, and the
         entry-side same-symbol cooldown families.
PART 1B  the `floor_only` window, measured.

WHY `floor_only` IS A REAL BLINDSPOT -- read straight off _manage():
    floor_only = (self.ratchet and self.stop_px <= floor_line + 1e-9)
    defend     = ((not floor_only) or LOCK_MODE == "stop"
                  or (tf5 and MANAGE_5M_WICK and self.ratchet))
With the shipped LOCK_MODE="trail" and MANAGE_5M=False (so the `tf5` branch
never runs), `defend` is False for the WHOLE of floor_only. And when
defend is False:
    * `if defend and hit:` is skipped -> the stop at floor_line is NOT tested;
    * the SHIELD block is guarded by `if not self.be_armed:` -> skipped;
    * STRUCT_TRAIL is guarded by `if STRUCT_TRAIL and not self.ratchet:` ->
      skipped.
The ONLY thing still live is EMERGENCY_WICK_STOP at orig_stop_px, i.e. -1R.
That is exactly how a trade that armed +3R ends as EMERGENCY_STOP at -1.00x.
`floor_only` ends only when a 4H BlueBox forms with y_bottom >= floor_line
(on_struct -> trail_4h_structural). If none does, the hole never closes.

Everything here is measured against the trade CSVs and the 5m archive; no
indicator is used, only boxes-equivalent price structure, and the true_X
basis from v45 (two-sided 0.10%).

USAGE  python3 audit_v47_ict_boxes.py [1a|1b|all]
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
TF_NS = A.TF_NS
X_GRID = [-0.2, 0.0, 0.3, 0.5, 0.8, 1.0, 1.2, 1.5]
H1_NS = 3600 * 10 ** 9
H4_NS = 4 * 3600 * 10 ** 9


# ------------------------------------------------------------------ #
def tf_closes(D, a, b, tf_ns):
    """Completed bars of tf_ns inside the trade: (end_ns, close_px)."""
    i0, i1 = A.slice_bars(D, a, b)
    if i1 <= i0:
        return None
    ns = D["ns"][i0:i1]
    bucket = (ns // tf_ns) * tf_ns
    last = np.r_[bucket[1:] != bucket[:-1], True]
    idx = np.nonzero(last)[0] + i0
    return bucket[last] + tf_ns, D["c"][idx]


def arm_bar(D, r, tf_ns):
    """Index into the 5m slice where the exec frame first CLOSES >= floor."""
    i0, i1 = A.slice_bars(D, r.entry_ns, r.exit_ns)
    if i1 <= i0:
        return None
    ns = D["ns"][i0:i1]
    bucket = (ns // tf_ns) * tf_ns
    last = np.r_[bucket[1:] != bucket[:-1], True]
    idx = np.nonzero(last)[0] + i0
    end = bucket[last] + tf_ns
    hit = np.nonzero(D["c"][idx] >= r.floor_line - 1e-6)[0]
    if not hit.size:
        return None
    # the 5m bar at/after that exec bar's close
    pos = int(np.searchsorted(ns, end[hit[0]], "left"))
    return (i0, i1, min(pos, i1 - i0))


def px_at(fill, stop, M):
    u = fill * (1 + COST) - stop * (1 - COST)
    return (fill * (1 + COST) + M * u) / (1 - COST)


# ================================================================== #
# PART 1A -- streak / re-entry / cooldown
# ================================================================== #
def part1a(t: pd.DataFrame) -> dict:
    d = t.sort_values(["symbol", "entry_ns"]).reset_index(drop=True)
    d["is_loss"] = d.net_pnl < -0.05
    prev_loss_h, consec, last_loss_ns = [], [], {}
    for r in d.itertuples(index=False):
        key = r.symbol
        pl = last_loss_ns.get(key)
        prev_loss_h.append((r.entry_ns - pl) / 3.6e12 if pl is not None
                           else np.nan)
        last_loss_ns[key] = r.entry_ns if r.is_loss else pl
        consec.append(0)
    d["h_since_loss"] = prev_loss_h
    # consecutive losses on this symbol immediately before each trade
    cur: dict = {}
    cc = []
    for r in d.itertuples(index=False):
        cc.append(cur.get(r.symbol, 0))
        cur[r.symbol] = (cur.get(r.symbol, 0) + 1) if r.is_loss else 0
    d["consec_losses"] = cc

    buckets = [(-np.inf, 2, "≤2h"), (2, 4, "2–4h"), (4, 8, "4–8h"),
               (8, 16, "8–16h"), (16, 24, "16–24h"), (24, np.inf, ">24h")]
    out: dict = {"by_hours": [], "by_consec": []}

    def row(g):
        return {"n": int(len(g)),
                "gross": round(float(((g.exit_price - g.fill)
                                      * g.qty).sum()), 2),
                "fees": round(float(g.fees.sum()), 2),
                "net": round(float(g.net_pnl.sum()), 2),
                "avg": round(float(g.net_pnl.mean()), 3) if len(g) else 0.0,
                "wr": round(float((g.net_pnl > 0).mean() * 100), 1)
                if len(g) else 0.0}

    for lo, hi, lab in buckets:
        g = d[d.h_since_loss.between(lo, hi, inclusive="left")]
        g = d[(d.h_since_loss > lo) & (d.h_since_loss <= hi)] if np.isfinite(lo) \
            else d[(d.h_since_loss.isna()) | (d.h_since_loss <= hi)]
        r_ = {"bucket": lab, **row(g)}
        for k in ("golden", "em", "be", "other"):
            r_[k] = int(g[k].sum())
        out["by_hours"].append(r_)
    for c in (0, 1, 2):
        g = d[d.consec_losses == c] if c < 2 else d[d.consec_losses >= 2]
        r_ = {"consec": f"{c}" if c < 2 else "≥2", **row(g)}
        for k in ("golden", "em", "be", "other"):
            r_[k] = int(g[k].sum())
        out["by_consec"].append(r_)

    # ---- static cooldown: drop later trades on a symbol inside the window --
    base = float(t.net_pnl.sum())
    cd_rows = []
    for hrs in (4, 8, 12, 16):
        for trig in ("after_loss", "after_2_nonwin"):
            keep = []
            blocked: dict = {}
            streak: dict = {}
            for idx, r in d.iterrows():
                b = blocked.get(r.symbol)
                if b is not None and r.entry_ns < b:
                    continue
                keep.append(idx)
                is_loss = r.net_pnl < -0.05
                is_nonwin = r.net_pnl <= 0
                if trig == "after_loss" and is_loss:
                    blocked[r.symbol] = r.entry_ns + hrs * 3.6e12
                if trig == "after_2_nonwin":
                    streak[r.symbol] = (streak.get(r.symbol, 0) + 1) \
                        if is_nonwin else 0
                    if streak[r.symbol] >= 2:
                        blocked[r.symbol] = r.entry_ns + hrs * 3.6e12
                        streak[r.symbol] = 0
            k = d.loc[keep]
            cd_rows.append({"hours": hrs, "trigger": trig, "kept": int(len(k)),
                            "dropped": int(len(d) - len(k)),
                            "net": round(float(k.net_pnl.sum()), 2),
                            "delta": round(float(k.net_pnl.sum()) - base, 2),
                            "gold_lost": int(d.golden.sum() - k.golden.sum()),
                            "loss_dropped": int(d.is_loss.sum()
                                                - k.is_loss.sum())})
    out["cooldown"] = cd_rows
    out["_d"] = d
    return out


# ================================================================== #
# PART 1B -- the floor_only window
# ================================================================== #
def part1b(t: pd.DataFrame, data: dict) -> dict:
    rows = []
    for r in t.itertuples(index=False):
        D = data[r.symbol]
        tf = TF_NS[r.exec_tf]
        ab = arm_bar(D, r, tf)
        if ab is None:
            continue
        i0, i1, k = ab
        if k >= i1 - i0:
            continue                          # armed on the last bar
        ns = D["ns"][i0:i1]
        c5 = D["c"][i0:i1]
        f, s = r.fill, r.stop
        X5 = (c5 * (1 - COST) - f * (1 + COST)) / r.unit_loss
        # ---- minimum closes AFTER arming, per lens, while X < 5.0 --------
        def min_close(tf_ns, series_px):
            ends, cls = tf_closes(D, r.entry_ns, r.exit_ns, tf_ns)
            if ends is None:
                return np.nan
            m = ends > ns[k]                     # strictly after the arm
            keep = m & (ends <= r.exit_ns)
            if not keep.any():
                return np.nan
            X = (cls[keep] * (1 - COST) - f * (1 + COST)) / r.unit_loss
            sel = X5[k] < 5.0
            return float(X.min()) if X.size else np.nan

        x5_after = X5[k + 1:]
        min_exec = float(x5_after.min()) if x5_after.size else np.nan
        min_1h = min_close(H1_NS, None)
        min_4h = min_close(H4_NS, None)
        rows.append({"win": r.win, "entry_time": r.entry_time,
                     "symbol": r.symbol, "exec_tf": r.exec_tf,
                     "golden": bool(r.golden), "em": bool(r.em),
                     "be": bool(r.be), "other": bool(r.other),
                     "net_pnl": float(r.net_pnl),
                     "X_arm": float(X5[k]),
                     "min_exec": min_exec, "min_1h": min_1h,
                     "min_4h": min_4h,
                     "b0_x": float(r.B0_true_X)})
    return pd.DataFrame(rows)


BINS = [(-np.inf, -0.5, "≤−0.5x"), (-0.5, 0.0, "−0.5..0x"),
        (0.0, 0.5, "0..+0.5x"), (0.5, 1.0, "+0.5..+1.0x"),
        (1.0, 1.5, "+1.0..+1.5x"), (1.5, 2.0, "+1.5..+2.0x"),
        (2.0, np.inf, "≥+2.0x")]


def bin_table(df: pd.DataFrame) -> str:
    L = ["| min close | Golden_Armed n | share | EM_Armed n | share |",
         "|---|---:|---:|---:|---:|"]
    for lo, hi, lab in BINS:
        for col in ("min_exec", "min_1h", "min_4h"):
            pass
        break
    return "\n".join(L)


def main() -> int:
    t0 = time.time()
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    t = A.load_tape()
    data = {s: A.load_5m(s) for s in A.SYMS}
    if which in ("all", "1b"):
        t = A.measure(t, data)      # adds B0_true_X / X_* columns for 1B
    out: dict = {}
    print(f"# v47 STAGE 1 — ICT BOX / STREAK FORENSIC AUDIT "
          f"({time.time()-t0:.1f}s, ZERO engine runs)\n")
    print(f"book **{len(t)}** trades · net **${t.net_pnl.sum():+.2f}** · "
          f"windows 5 · months {t.ym.nunique()}\n")

    if which in ("all", "1a"):
        a = part1a(t)
        d = a.pop("_d")
        print("## 1A. Same-symbol re-entry anatomy\n")
        print("| hours since previous loss on this symbol | n | Golden | EM | "
              "BE | Other | Gross $ | Fees $ | Net $ | Avg $ | WR % |")
        print("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
        for r in a["by_hours"]:
            print(f"| {r['bucket']} | {r['n']} | {r['golden']} | {r['em']} "
                  f"| {r['be']} | {r['other']} | {r['gross']:+.2f} | "
                  f"{r['fees']:.2f} | {r['net']:+.2f} | {r['avg']:+.3f} | "
                  f"{r['wr']} |")
        print("\n| consecutive losses on this symbol before entry | n | Golden "
              "| EM | BE | Other | Net $ | Avg $ | WR % |")
        print("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
        for r in a["by_consec"]:
            print(f"| {r['consec']} | {r['n']} | {r['golden']} | {r['em']} | "
                  f"{r['be']} | {r['other']} | {r['net']:+.2f} | "
                  f"{r['avg']:+.3f} | {r['wr']} |")
        print("\n### Static same-symbol cooldown (entry side)\n")
        print("| cooldown | trigger | kept | dropped | Net $ | Δ vs B0 | "
              "golden lost | losses avoided |")
        print("|---|---|---:|---:|---:|---:|---:|---:|")
        for r in a["cooldown"]:
            print(f"| {r['hours']}h | {r['trigger']} | {r['kept']} | "
                  f"{r['dropped']} | {r['net']:+.2f} | {r['delta']:+.2f} | "
                  f"{r['gold_lost']} | {r['loss_dropped']} |")
        print()
        out["1a"] = {k: v for k, v in a.items()}

    if which in ("all", "1b"):
        b = part1b(t, data)
        b.to_csv(RES / "_v47_floor_only.csv", index=False)
        g = b[b.golden]
        e = b[b.em]
        print(f"## 1B. The `floor_only` window — {len(b)} armed trades\n")
        print(f"Golden_Armed **{len(g)}** · EM_Armed **{len(e)}** · "
              f"Other_Armed **{len(b)-len(g)-len(e)}**\n")
        for col, name in (("min_exec", "exec_tf close"),
                          ("min_1h", "1H candle close"),
                          ("min_4h", "4H candle close")):
            print(f"### minimum {name} after arming\n")
            print("| bin | Golden n | Golden share | EM n | EM share |")
            print("|---|---:|---:|---:|---:|")
            for lo, hi, lab in BINS:
                gg = int(g[col].between(lo, hi, inclusive="left").sum())
                ee = int(e[col].between(lo, hi, inclusive="left").sum())
                print(f"| {lab} | {gg} | {gg/max(len(g),1)*100:.1f}% | "
                      f"{ee} | {ee/max(len(e),1)*100:.1f}% |")
            print(f"\nmedian — Golden {g[col].median():+.2f}x vs "
                  f"EM {e[col].median():+.2f}x\n")
        out["1b"] = {"armed": int(len(b)), "golden": int(len(g)),
                     "em": int(len(e)),
                     "med_exec": [float(g.min_exec.median()),
                                  float(e.min_exec.median())],
                     "med_1h": [float(g.min_1h.median()),
                                float(e.min_1h.median())],
                     "med_4h": [float(g.min_4h.median()),
                                float(e.min_4h.median())]}
    if which in ("all", "1b"):
        # ---- Stage 1C: the family matrix passing the v46 gate ----------
        bb = pd.DataFrame(pd.read_csv(RES / "_v47_floor_only.csv"))
        loss = np.where(np.abs(bb.b0_x) > 1e-9,
                        bb.net_pnl / np.where(np.abs(bb.b0_x) > 1e-9,
                                              bb.b0_x, 1), np.nan)
        bb["loss_usd"] = pd.Series(loss).fillna(0)
        print("## 1C. floor_only exit families vs the v46 gate\n")
        print("| lens | X | Δ vs B0 | Ex-Top-1 Δ | W1/W2/OLD7/MY1/MY2 Δ | "
              "windows+ | GATE |")
        print("|---|---:|---:|---:|---|---:|---|")
        gate_rows = []
        for lens, lname in (("min_exec", "exec_tf close"),
                            ("min_1h", "1H close"), ("min_4h", "4H close")):
            for X in X_GRID:
                cut = bb[lens] <= X
                nn = pd.Series(np.where(cut.values,
                                        X * bb["loss_usd"].values,
                                        bb.net_pnl.values), index=bb.index)
                dl = nn - bb.net_pnl
                d, top = float(dl.sum()), float(dl.max())
                per = {w: float(dl[bb.win == w].sum())
                       for w in ("W1", "W2", "OLD7", "MOD_Y1", "MOD_Y2")}
                npos = sum(1 for v in per.values() if v > 0)
                ok = d > 0 and (d - top) > 0 and npos >= 3
                pw = "/".join(f"{per[w]:+.1f}" for w in
                              ("W1", "W2", "OLD7", "MOD_Y1", "MOD_Y2"))
                print(f"| {lname} | {X:+.1f}x | {d:+.2f} | {d-top:+.2f} | "
                      f"{pw} | {npos}/5 | {'**PASS**' if ok else 'fail'} |")
                gate_rows.append({"lens": lname, "X": X, "delta": round(d, 2),
                                  "ex_top1": round(d - top, 2),
                                  "windows_pos": npos, "pass": bool(ok)})
        out["1c_gate"] = gate_rows
        print()
    (RES / "_v47_stage1.json").write_text(json.dumps(out, indent=1,
                                                      default=str))
    print(f"_total {time.time()-t0:.2f}s_")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
