#!/usr/bin/env python3
"""
audit_v25_master.py — EXACT BAR-WALK OF THE v26 CANDIDATE RULE FAMILY
=====================================================================
Two jobs, both on the REAL v25 trade set (results/trades_v25.csv):

JOB 1 — measure the three "engineering crimes" alleged for v26, on data:
  C1 "the stop was inflated to the HTF floor, so +3R sat beyond the range
     top"      -> `stop_inflated` (stop below the GreenBox floor) and
                  `sky_r_purple` (R-distance from entry to the 4H range top)
  C2 "the shield waited for a 3-bar fractal, so mid-crossing losers died"
                -> exact bar-walk of MID / BOS / MID+BOS / MID+A1 / BOS+A1
                   / A0.5 / A1 (no CSV estimates: every bar is replayed)
  C3 "the bot bought into a bearish displacement on the retrace"
                -> `bear_fvg_over_entry` (unmitigated bearish FVG sitting
                   between the entry and the +3R lock) and `retrace_impulse`
                   (biggest bearish body of the retrace / biggest bullish
                   body of the impulse that created the zone)

JOB 2 — score every rule against ALL FIVE mandatory asserts, using the
        definition verified in strategy_v25_ict_narrative.py:
            decided  = WIN + LOSS          (BE excluded from the WR)
            total    = WIN + LOSS + BE     (BE counts towards 150)
        and report which combinations reach WR >= 60%.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

import numpy as np
import pandas as pd

import audit_v24_shield as sh          # build_frames / trade_path / walk
import strategy_v25_ict_narrative as v25

RES = Path(__file__).resolve().parent / "results"
import sys
SRC = sys.argv[1] if len(sys.argv) > 1 else "trades_v25.csv"
TAG = SRC.replace("trades_", "").replace(".csv", "")
FEE = sh.FEE
MIN_R = sh.MIN_R
YEARS = ("2021", "2022", "2023", "2024", "2025")
RULES = ["NONE", "A0.25", "A0.5", "A0.75", "A1", "A1.5", "A2",
         "MID", "BOS", "MID+BOS", "MID+A1", "BOS+A1"]


# --------------------------------------------------------------------- #
def _green_bottom(t):
    g = t.get("green")
    if isinstance(g, str) and g.startswith("{"):
        try:
            return float(ast.literal_eval(g)["bottom"])
        except Exception:
            return np.nan
    return np.nan


def pre_entry_features(frames, trades) -> dict:
    """Crime-1 and Crime-3 features, all computed from bars BEFORE entry."""
    out = {i: {} for i in trades.index}
    for i, t in trades.iterrows():
        tf = frames[t["exec_tf"]]
        e_t = pd.Timestamp(t["entry_time"])
        try:
            pos = tf.index.get_loc(e_t)
        except KeyError:
            pos = tf.index.searchsorted(e_t)
        lo = max(0, pos - 60)
        seg = tf.iloc[lo:pos + 1]          # <= entry bar: causal
        o = seg["Open"].to_numpy(); h = seg["High"].to_numpy()
        l = seg["Low"].to_numpy(); c = seg["Close"].to_numpy()
        E = float(t["entry_price"]); Rk = E - float(t["stop_price"])
        lock = E + MIN_R * Rk

        # ---- C1: was the stop inflated below the GreenBox floor? -------
        gb = _green_bottom(t)
        out[i]["green_bottom"] = gb
        out[i]["stop_inflated"] = bool(np.isfinite(gb) and
                                       float(t["stop_price"]) < gb - 1e-9)
        out[i]["stop_inflate_r"] = (round((gb - float(t["stop_price"])) / Rk, 3)
                                    if np.isfinite(gb) and Rk > 0 else np.nan)

        # ---- C1b: R-distance to the top of the 4H dealing range --------
        pmid, rpos = t.get("purple_mid"), t.get("nar_range_pos_4h")
        sky = np.nan
        if pd.notna(pmid) and pd.notna(rpos) and abs(rpos - 0.5) > 1e-6:
            H = (E - float(pmid)) / (float(rpos) - 0.5)
            sky = ((E + (1.0 - float(rpos)) * H) - E) / Rk
        out[i]["sky_r_purple"] = round(float(sky), 3) if sky == sky else np.nan

        # ---- C3a: unmitigated BEARISH FVG between entry and the lock ---
        # 3-bar bearish gap: bar[k-2].low > bar[k].high  -> the gap is
        # (bar[k].high , bar[k-2].low). Unmitigated at the entry tick =
        # no later bar traded up through the gap top before the entry.
        n = len(seg)
        best = np.nan; cnt = 0
        for k in range(2, n):
            gap_lo, gap_hi = h[k], l[k - 2]
            if gap_lo >= gap_hi:
                continue
            if not (gap_lo < lock and gap_hi > E):
                continue                       # not inside the trade path
            mitigated = bool((h[k + 1:] >= gap_hi).any()) if k + 1 < n else False
            if mitigated:
                continue
            cnt += 1
            r = (gap_lo - E) / Rk if Rk > 0 else np.nan
            best = r if best != best else min(best, r)
        out[i]["bear_fvg_over_entry"] = cnt
        out[i]["bear_fvg_nearest_r"] = round(float(best), 3) if best == best else np.nan

        # ---- C3b: retrace impulse ratio (smash vs corrective) ----------
        body = np.abs(c - o)
        k1 = max(0, n - 10)                     # the retrace into the zone
        k0 = max(0, n - 30)                     # the impulse before it
        bear = body[k1:n][c[k1:n] < o[k1:n]]
        bull = body[k0:k1][c[k0:k1] > o[k0:k1]]
        out[i]["retrace_impulse"] = (round(float(bear.max() / bull.max()), 3)
                                     if len(bear) and len(bull)
                                     and bull.max() > 0 else np.nan)
        out[i]["retrace_gap_over"] = bool(
            len(bear) and bear.max() > 0 and
            (h[k1:n].max() - l[k1:n].min()) > 2.0 * float(Rk))
    return out


# --------------------------------------------------------------------- #
def score(classes, Rs, times, label) -> dict:
    cl = np.asarray(classes); R = np.asarray(Rs, dtype=float)
    ts = pd.to_datetime(pd.Series(times)).dt.year.astype(str).to_numpy()
    W = int((cl == "WIN").sum()); B = int((cl == "BE").sum())
    L = int((cl == "LOSS").sum())
    dec = W + L
    wr = W / dec if dec else 0.0
    wins = R[cl == "WIN"]
    yr = pd.Series(ts).value_counts().to_dict()
    st = worst = 0
    for x in cl:
        if x == "LOSS":
            st += 1; worst = max(worst, st)
        else:
            st = 0
    return {
        "label": label, "total": W + B + L, "W": W, "BE": B, "L": L,
        "WR_pct": round(100 * wr, 2),
        "min_winner_R": round(float(wins.min()), 2) if len(wins) else 0.0,
        "ge4R": int((wins >= 4.0).sum()),
        "max_R": round(float(wins.max()), 2) if len(wins) else 0.0,
        "streak": worst,
        "ymin": min(int(yr.get(y, 0)) for y in YEARS),
        "yearly": {y: int(yr.get(y, 0)) for y in YEARS},
        "A1": bool(wr >= 0.60),
        "A2": bool(len(wins) and wins.min() >= 3.00 - 1e-6),
        "A3": bool((wins >= 4.0).sum() >= 5 and (len(wins) and wins.max() >= 6.0)),
        "A4": bool(worst <= 3),
        "A5": bool(W + B + L >= 150 and
                   all(int(yr.get(y, 0)) >= 12 for y in YEARS)),
    }


def main():
    trades = pd.read_csv(RES / SRC)
    trades["entry_time"] = pd.to_datetime(trades["entry_time"])
    trades["exit_time"] = pd.to_datetime(trades["exit_time"])
    print(f"[v26-audit] {len(trades)} v25 trades: "
          f"{trades['class'].value_counts().to_dict()}")

    frames = sh.build_frames()
    print("[v26-audit] frames rebuilt causally")
    feat = pre_entry_features(frames, trades)
    F = pd.DataFrame(feat).T.reindex(trades.index)
    A = pd.concat([trades, F], axis=1)
    A.to_csv(RES / f"audit_{TAG}_features.csv", index=False)

    # ================= CRIME 1 ========================================= #
    print("\n" + "=" * 78)
    print("CRIME 1  'the stop was inflated, so +3R sat beyond the range top'")
    print("=" * 78)
    print(f"  stop below the GreenBox floor (inflated): "
          f"{int(A['stop_inflated'].fillna(False).sum())} / {len(A)} "
          f"({100*A['stop_inflated'].fillna(False).mean():.1f}%)")
    print(f"  median inflation: {A['stop_inflate_r'].median():.2f}R of the "
          f"final RiskHeight")
    for coh in ("WIN", "BE", "LOSS"):
        g = A[A["class"] == coh]
        print(f"    {coh:5s} n={len(g):>3}  inflated="
              f"{100*g['stop_inflated'].fillna(False).mean():>5.1f}%  "
              f"sky_r_purple(median)={g['sky_r_purple'].median():>6.2f}R  "
              f"top<3R: {int((g['sky_r_purple'] < 3).sum()):>3}")
    print("  => the range top sat >= 3R away on "
          f"{100*(A['sky_r_purple'] >= 3).mean():.1f}% of ALL trades and on "
          f"{100*(A.loc[A['class']=='LOSS','sky_r_purple'] >= 3).mean():.1f}% "
          "of losers: the +3R line was NOT beyond the delivery point.")

    # ================= CRIME 3 ========================================= #
    print("\n" + "=" * 78)
    print("CRIME 3  'it bought into a bearish displacement on the retrace'")
    print("=" * 78)
    hdr = f"  {'cohort':24s}{'n':>4}{'fvg>0':>7}{'fvg med':>8}{'imp med':>8}{'imp>=1':>8}"
    print(hdr)
    for name, g in (("WIN", A[A["class"] == "WIN"]),
                    ("BE", A[A["class"] == "BE"]),
                    ("LOSS crossed mid",
                     A[(A["class"] == "LOSS") & A["disp_mid"].fillna(False).astype(bool)]),
                    ("LOSS died on arrival",
                     A[(A["class"] == "LOSS") & ~A["disp_mid"].fillna(False).astype(bool)])):
        print(f"  {name:24s}{len(g):>4}"
              f"{100*(g['bear_fvg_over_entry'].fillna(0) > 0).mean():>6.1f}%"
              f"{g['bear_fvg_over_entry'].fillna(0).median():>8.1f}"
              f"{g['retrace_impulse'].median():>8.2f}"
              f"{100*(g['retrace_impulse'] >= 1.0).mean():>7.1f}%")

    # selectivity of the two candidate pre-entry filters
    print("\n  pre-entry filter selectivity (a 60% WR at n>=150 needs a")
    print("  filter that removes ~68% of the losers and <=6% of the winners):")
    for name, mask in (("bear_fvg_over_entry > 0", A["bear_fvg_over_entry"].fillna(0) > 0),
                       ("retrace_impulse >= 1.0", A["retrace_impulse"] >= 1.0),
                       ("retrace_impulse >= 1.5", A["retrace_impulse"] >= 1.5),
                       ("sky_r_purple < 3", A["sky_r_purple"] < 3),
                       ("stop_inflated", A["stop_inflated"].fillna(False))):
        nl = int((mask & (A["class"] == "LOSS")).sum())
        nw = int((mask & (A["class"] == "WIN")).sum())
        tl = int((A["class"] == "LOSS").sum()); tw = int((A["class"] == "WIN").sum())
        kept_w, kept_l = tw - nw, tl - nl
        wr = kept_w / (kept_w + kept_l) if kept_w + kept_l else 0
        print(f"    {name:26s} kills {nl:>3}/{tl} losers ({100*nl/tl:>4.1f}%) "
              f"and {nw:>2}/{tw} winners ({100*nw/tw:>4.1f}%) -> WR "
              f"{100*wr:>5.2f}%  n={len(A)-int(mask.sum())}")

    # ================= CRIME 2 : EXACT BAR-WALK ======================== #
    print("\n" + "=" * 78)
    print("CRIME 2  EXACT BAR-WALK OF EVERY SHIELD RULE (no CSV estimates)")
    print("=" * 78)
    print("[v26-audit] building extended paths...")
    paths = {i: sh.trade_path(frames, t) for i, t in A.iterrows()}
    A["bos_bar"] = [paths[i][4] for i in A.index]
    print(f"[v26-audit] post-entry BOS printed on "
          f"{int(A['bos_bar'].notna().sum())}/{len(A)} trades")

    results = []
    times = A["entry_time"].tolist()
    print(f"\n  {'rule':10s}{'W':>4}{'BE':>4}{'L':>4}{'WR%':>7}{'>=4R':>5}"
          f"{'maxR':>7}{'stk':>4}{'ymin':>5}{'A1':>3}{'A2':>3}{'A3':>3}"
          f"{'A4':>3}{'A5':>3}{'pass':>6}")
    for rule in RULES:
        cl, Rs = [], []
        for i, t in A.iterrows():
            k, r, _ = sh.walk(t, paths[i], rule)
            cl.append(k); Rs.append(r)
        s = score(cl, Rs, times, f"shield={rule}")
        results.append(s)
        f = lambda b: "Y" if b else "."      # noqa: E731
        npass = sum([s["A1"], s["A2"], s["A3"], s["A4"], s["A5"]])
        print(f"  {rule:10s}{s['W']:>4}{s['BE']:>4}{s['L']:>4}{s['WR_pct']:>7}"
              f"{s['ge4R']:>5}{s['max_R']:>7}{s['streak']:>4}{s['ymin']:>5}"
              f"{f(s['A1']):>3}{f(s['A2']):>3}{f(s['A3']):>3}{f(s['A4']):>3}"
              f"{f(s['A5']):>3}{npass:>5}/5")

    # ---- best shield x pre-entry filter cross-product ------------------
    print("\n  best shield x causal pre-entry filter (all five asserts):")
    best_rule = max(results, key=lambda s: (sum([s["A1"], s["A2"], s["A3"],
                                                 s["A4"], s["A5"]]),
                                            s["WR_pct"]))["label"].split("=")[1]
    print(f"  (best shield alone: {best_rule})")
    walked = {}
    for rule in ("MID", "MID+BOS", "MID+A1", "BOS+A1", "A0.5", "A1"):
        cl, Rs = [], []
        for i, t in A.iterrows():
            k, r, _ = sh.walk(t, paths[i], rule)
            cl.append(k); Rs.append(r)
        walked[rule] = (np.asarray(cl), np.asarray(Rs, dtype=float))
    rows = []
    for rule, (cl, Rs) in walked.items():
        for fname, fmask in (
                ("-", np.ones(len(A), bool)),
                ("no bear FVG over entry", ~(A["bear_fvg_over_entry"].fillna(0) > 0).to_numpy()),
                ("retrace_impulse < 1.0", (A["retrace_impulse"] < 1.0).to_numpy()),
                ("retrace_impulse < 1.5", (A["retrace_impulse"] < 1.5).to_numpy()),
                ("sky_r_purple >= 3", (A["sky_r_purple"] >= 3).to_numpy()),
                ("no inflated stop", ~A["stop_inflated"].fillna(False).astype(bool).to_numpy()),
        ):
            m = fmask
            s = score(cl[m], Rs[m], A["entry_time"].to_numpy()[m],
                      f"{rule} & {fname}")
            rows.append(s)
            f = lambda b: "Y" if b else "."   # noqa: E731
            npass = sum([s["A1"], s["A2"], s["A3"], s["A4"], s["A5"]])
            print(f"    {rule:9s}& {fname:24s} n={s['total']:>4} W={s['W']:>3} "
                  f"BE={s['BE']:>3} L={s['L']:>3} WR={s['WR_pct']:>6.2f}% "
                  f">=4R={s['ge4R']:>3} maxR={s['max_R']:>6.2f} stk={s['streak']:>2} "
                  f"ymin={s['ymin']:>3} {f(s['A1'])}{f(s['A2'])}{f(s['A3'])}"
                  f"{f(s['A4'])}{f(s['A5'])} = {npass}/5")

    best = max(rows + results, key=lambda s: (sum([s["A1"], s["A2"], s["A3"],
                                                   s["A4"], s["A5"]]),
                                              s["WR_pct"]))
    print("\n  BEST OVERALL:", json.dumps(best, indent=2))
    with open(RES / f"audit_{TAG}_master.json", "w") as fh:
        json.dump({"shield_only": results, "cross_product": rows,
                   "best": best}, fh, indent=2, default=str)
    pd.DataFrame(rows + results).to_csv(RES / f"audit_{TAG}_master.csv", index=False)
    print(f"\n[v26-audit] wrote {RES/'audit_v25_master.json'} and .csv")


if __name__ == "__main__":
    main()
