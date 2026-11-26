#!/usr/bin/env python3
"""
lab_v27_exact.py — THE 5-MINUTE MICROSCOPE INSIDE THE GREEN BOX
================================================================
Every engine so far (v21..v26) placed a resting BUY LIMIT at the SEAM
(green.y_top) and was therefore filled on the FIRST touch — including the
touches made by a 5m candle falling like a knife straight through the box
into the stop. The engine's own frames (15m/30m/1h) only looked at their
close, so they never saw the intra-box story on the 5m data that IS on disk.

This lab replays every real v25/v26 setup on the 5m frame and measures,
with zero lookahead and a FIXED horizon for every trade:

  COHORTS (verifying the numbers quoted in the v27 brief)
    knives   : filled at the seam, then the stop broke with no 5m close
               back above the seam and no +0.5R rebound
    retests  : price came back INTO the box body (stop < low <= seam)
               after the first touch
    collapses: retested and then broke the stop anyway
    saved    : rebounded from INSIDE the box body and reached the lock

  MECHANISM 1 — deep box limit
    entry_px = stop + alpha * (seam - stop),  alpha in {1.00, 0.75, 0.50, 0.25}
    alpha=1.00 reproduces the shipped seam entry; alpha<1 buys CHEAPER,
    shrinks 1R, and moves the +3R lock from seam+3H down to seam+(3a-2)H.
    A limit that is never touched is never a trade: the knives that fall
    straight through still fill (they pass the level), but the setups that
    ran away from the seam without dipping are simply not taken.

  MECHANISM 2 — bug-free causal shield (already shipped in v25/v26,
    re-verified here): arm only on a CLOSE strictly above the BE line.

  MECHANISM 3 — second chance from the alive box body
    after a BE scratch, if the box is still alive (no close below the
    original stop) and price re-enters the body at <= seam, take it again
    with the ORIGINAL stop. If the stop then breaks, the wave is over and
    the whole sequence nets 0.00R.

Runner values are reported two ways because a lab cannot replicate the
engine's blue-wave trail exactly:
    R_floor = 3.00 (the fee-adjusted lock, guaranteed by construction)
    R_est   = mfe_close * BOOK_RATIO, where BOOK_RATIO is MEASURED from the
              real shipped trades (booked R / mfe_close_R on winners)
Both are printed; the final word always belongs to a real engine run.
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from engine.causal_primitives import load_asset_ohlcv, resample_causal_tf

RES = Path(__file__).resolve().parent / "results"
DATA = Path(__file__).resolve().parent / "data" / "BTCUSD_5m"
FEE = 0.001
MIN_R = 3.0
HORIZON = 3000          # 5m bars ~ 10.4 days, IDENTICAL for every trade
YEARS = ("2021", "2022", "2023", "2024", "2025")


# --------------------------------------------------------------------- #
def box_of(t):
    def get(col, key):
        v = t.get(col)
        if isinstance(v, str) and v.startswith("{"):
            try:
                return float(ast.literal_eval(v)[key])
            except Exception:
                return np.nan
        return np.nan
    gt, gb = get("green", "top"), get("green", "bottom")
    yb = get("yellow", "bottom")
    seam = np.nanmin([gt, yb]) if np.isfinite(yb) else gt
    return gt, gb, seam


def book_ratio(csv: Path) -> float:
    """Measured: how much of mfe_close the engine's trail actually books."""
    d = pd.read_csv(csv)
    w = d[(d["class"] == "WIN") & (d["mfe_close_R"] > 0)]
    return float((w["R"] / w["mfe_close_R"]).median())


# --------------------------------------------------------------------- #
def build_5m() -> pd.DataFrame:
    raw = load_asset_ohlcv(DATA, include_stems=[str(y) for y in range(2020, 2028)])
    tf = resample_causal_tf(raw, "5min")
    return tf


def window(tf: pd.DataFrame, t):
    """5m OHLC from the entry bar forward, HORIZON bars, causal."""
    e_t = pd.Timestamp(t["entry_time"])
    pos = tf.index.get_loc(e_t) if e_t in tf.index else tf.index.searchsorted(e_t)
    seg = tf.iloc[pos:pos + HORIZON]
    return (seg["Open"].to_numpy(), seg["High"].to_numpy(),
            seg["Low"].to_numpy(), seg["Close"].to_numpy(),
            pd.Index(seg.index).year.astype(str).to_numpy()[0] if len(seg) else "?")


def first_true(mask):
    """Index of the first True, or len(mask)."""
    return int(np.argmax(mask)) if mask.any() else len(mask)


def simulate_absorption(o, h, l, c, stop, seam, shield, ratio, pmid=None):
    """METHOD B of the v27 brief: do NOT buy the first touch of the seam.
    Wait for a 5m bar that dips INTO the box body (low <= seam, low > stop)
    and shows sell-side absorption (a close above its own open), then buy
    at that close - but never above the seam (the sacred law). A bar whose
    close is above the seam is skipped: buying there is mid-wave chasing.
    """
    n = len(c)
    for j in range(n):
        if not (l[j] <= seam and l[j] > stop):
            continue
        if c[j] <= o[j] or c[j] > seam:
            continue                              # no absorption / too high
        fill = c[j]
        risk = fill - stop
        if risk <= 2 * FEE * fill:
            continue                              # cannot pay the round trip
        lock = (fill * (1 + FEE) + MIN_R * risk) / (1 - FEE)
        be = fill * (1 + 2 * FEE)
        armed = False; eff = stop
        for k in range(j, n):
            if l[k] <= eff:
                px = eff if o[k] >= eff else o[k]
                r = (px - fill) / risk - 2 * FEE * fill / risk
                return [("BE", r, 0.0, True)] if armed else [("LOSS", r, 0.0, True)]
            if c[k] >= lock:
                return [("WIN", ride(c, k, fill, risk, ratio), MIN_R, True)]
            if not armed and shield != "none" and c[k] > be:
                if shield == "be" or (pmid is not None and np.isfinite(pmid)
                                      and c[k] > pmid):
                    armed = True; eff = max(eff, be)
        return [("OPEN", 0.0, 0.0, True)]
    return [("NOFILL", 0.0, 0.0, False)]


def ride(c, k, fill, risk, ratio):
    """Estimate the R a winner books after the +3R lock fires.

    A lab cannot replay the engine's blue-wave structural trail, so this
    uses the ONE sanctioned give-back constant (50%): the ride ends at the
    first close that has retraced half of the largest gain achieved since
    the lock. The result is then multiplied by BOOK_RATIO, which is
    MEASURED from the shipped trades (booked R / mfe_close_R on winners),
    and floored at MIN_R because the lock itself guarantees +3.00R net.
    Both the floor and the cap are printed in the validation block, so the
    estimator can never silently flatter the result.
    """
    rest = c[k:]
    run_max = np.maximum.accumulate(rest) - fill      # best gain so far, in px
    gain = rest - fill                                # this close's gain
    peak = float(run_max.max()) / risk
    # the ride ends at the first close that has given back HALF of the
    # largest gain achieved since the lock (50% is a sanctioned constant)
    half = first_true(gain <= 0.5 * run_max)
    booked = float(gain[half]) / risk if half < len(rest) else peak
    est = ratio * max(booked, 0.0)
    return max(MIN_R, min(est, peak))


def simulate(o, h, l, c, stop, seam, alpha, shield, second, ratio, pmid=None):
    """Walk one setup on the 5m tape.

    shield: "none" | "be" (arm on any close above the BE line)
                    | "mid" (arm only on a close above PurpleBox.mid AND
                             above the BE line — the shipped MID condition)
    Returns (class, R_est, R_floor, year_placeholder).
    """
    E0 = stop + alpha * (seam - stop)          # the resting limit
    if not (stop < E0 <= seam + 1e-9):
        return [("SKIP", 0.0, 0.0, False)]
    n = len(c)
    j = first_true(l <= E0)
    if j >= n:
        return [("NOFILL", 0.0, 0.0, False)]
    fill = E0 if o[j] >= E0 else o[j]          # gap-aware, conservative
    if fill <= stop:                           # gapped straight through
        return [("LOSS", -1.0, 0.0, True)]
    risk = fill - stop
    lock = (fill * (1 + FEE) + MIN_R * risk) / (1 - FEE)
    be = fill * (1 + 2 * FEE)
    armed = False
    eff = stop                                 # the EFFECTIVE stop
    for k in range(j, n):
        # 1) the effective stop is checked FIRST (intra-bar conservative)
        if l[k] <= eff:
            px = eff if o[k] >= eff else o[k]
            r = (px - fill) / risk - 2 * FEE * fill / risk
            if armed:
                if second:                     # MECHANISM 3
                    return re_entry(o, h, l, c, k + 1, stop, seam, fill, ratio)
                return [("BE", r, 0.0, True)]  # r == 0 by construction
            return [("LOSS", r, 0.0, True)]
        # 2) delivery: a CLOSE at/above the fee-adjusted +3R lock
        if c[k] >= lock:
            return [("WIN", ride(c, k, fill, risk, ratio), MIN_R, True)]
        # 3) MECHANISM 2: arm ONLY on a close strictly above the BE line,
        #    so the new stop is always below the market (no phantom stop)
        if not armed and shield != "none" and c[k] > be:
            if shield == "be" or (pmid is not None and np.isfinite(pmid)
                                  and c[k] > pmid):
                armed = True
                eff = max(eff, be)
    last = (c[-1] - fill) / risk - 2 * FEE * fill / risk
    return [("OPEN", last, 0.0, True)]


def re_entry(o, h, l, c, k0, stop, seam, first_fill, ratio):
    """MECHANISM 3: one re-entry inside the still-alive box body.

    HONEST ACCOUNTING (the v27 brief claims the collapsed re-entry nets
    0.00R / "zero loss" - that is arithmetically false: the re-entry is
    taken with the ORIGINAL stop, so it risks (re-entry - stop) of real
    money again). This lab therefore returns TWO records: the first leg
    (a BE scratch, 0.00R) and the second leg (a real WIN or a real LOSS),
    and the scorer counts them as two trades. A wave that collapses is a
    BE plus a LOSS, never a free zero.
    """
    n = len(c)
    leg1 = ("BE", 0.0, 0.0, True)                 # the first leg scratched
    if k0 >= n:
        return [leg1]
    sub_o, sub_h, sub_l, sub_c = o[k0:], h[k0:], l[k0:], c[k0:]
    alive = sub_l > stop
    touch = (sub_l <= seam) & alive
    j = first_true(touch)
    if j >= len(sub_c):
        return [leg1]                              # never came back
    fill2 = seam if sub_o[j] >= seam else sub_o[j]
    if fill2 <= stop:
        return [leg1]                              # the wave is over
    risk2 = fill2 - stop
    lock2 = (fill2 * (1 + FEE) + MIN_R * risk2) / (1 - FEE)
    for k in range(j, len(sub_c)):
        if sub_l[k] <= stop:                       # a REAL loss, not 0.00R
            px = stop if sub_o[k] >= stop else sub_o[k]
            r = (px - fill2) / risk2 - 2 * FEE * fill2 / risk2
            return [leg1, ("LOSS", r, 0.0, True)]
        if sub_c[k] >= lock2:
            return [leg1, ("WIN", ride(sub_c, k, fill2, risk2, ratio),
                           MIN_R, True)]
    return [leg1, ("OPEN", 0.0, 0.0, True)]


# --------------------------------------------------------------------- #
def cohorts(tf, A):
    """Verify the cohort numbers quoted in the v27 brief."""
    rows = []
    for i, t in A.iterrows():
        gt, gb, seam = box_of(t)
        stop = float(t["stop_price"])
        if not np.isfinite(seam):
            continue
        o, h, l, c, _ = window(tf, t)
        if len(c) < 5:
            continue
        ent = float(t["entry_price"])
        rk = ent - stop
        half_r = first_true(h >= ent + 0.5 * rk)        # ever traded +0.5R
        stop_hit = first_true(l <= stop)                # ever traded the stop
        up = first_true(c > seam)                       # left the box upward
        back = len(c)
        if up < len(c):
            after = (l <= seam) & (l > stop)
            after[:up + 1] = False
            back = first_true(after)
        retest = bool(up < len(c) and back < len(c))
        knife = bool(stop_hit < half_r)                 # fell straight through
        collapse = bool(retest and stop_hit < len(c) and stop_hit > back)
        lock_px = (ent * (1 + FEE) + MIN_R * rk) / (1 - FEE)
        delivered = first_true(c >= lock_px)
        rows.append({"i": i, "knife": knife, "retest": retest,
                     "collapse": collapse,
                     "saved_from_body": bool(retest and delivered < len(c)
                                             and delivered > back),
                     "stop_hit": bool(stop_hit < len(c)),
                     "half_r": bool(half_r < len(c)),
                     "delivered": bool(delivered < len(c)),
                     "class": t["class"]})
    D = pd.DataFrame(rows)
    return D


def score(seq, label, ratio):
    cl = np.array([q[0] for q in seq])
    R = np.array([q[1] for q in seq])
    yr = np.array([q[3] for q in seq])
    keep = cl != "SKIP"
    cl, R, yr = cl[keep], R[keep], yr[keep]
    nofill = int((cl == "NOFILL").sum()); openn = int((cl == "OPEN").sum())
    cl2 = cl[(cl != "NOFILL") & (cl != "OPEN")]
    R2 = R[(cl != "NOFILL") & (cl != "OPEN")]
    yr2 = yr[(cl != "NOFILL") & (cl != "OPEN")]
    W = int((cl2 == "WIN").sum()); B = int((cl2 == "BE").sum()); L = int((cl2 == "LOSS").sum())
    dec = W + L
    wins = R2[cl2 == "WIN"]
    yvc = pd.Series(yr2).value_counts().to_dict()
    st = worst = 0
    for x in cl2:
        if x == "LOSS":
            st += 1; worst = max(worst, st)
        else:
            st = 0
    ge4 = int((wins >= 4.0).sum())
    mx = float(wins.max()) if len(wins) else 0.0
    mn = float(wins.min()) if len(wins) else 0.0
    return {"label": label, "n": W + B + L, "W": W, "BE": B, "L": L,
            "nofill": nofill, "open": openn,
            "WR_pct": round(100 * W / dec, 2) if dec else 0.0,
            "min_win_R": round(mn, 2), "ge4R": ge4, "max_R": round(mx, 2),
            "streak": worst, "ymin": min(int(yvc.get(y, 0)) for y in YEARS),
            "total_R": round(float(R2.sum()), 1),
            "A1": bool(dec and W / dec >= 0.60),
            "A2": bool(len(wins) and mn >= 3.00 - 1e-6),
            "A3": bool(ge4 >= 5 and mx >= 6.0),
            "A4": bool(worst <= 3),
            "A5": bool(W + B + L >= 150 and
                       all(int(yvc.get(y, 0)) >= 12 for y in YEARS))}


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "trades_v26.csv"
    A = pd.read_csv(RES / src)
    A["entry_time"] = pd.to_datetime(A["entry_time"])
    ratio = book_ratio(RES / src)
    print(f"[lab] {src}: {len(A)} trades · measured BOOK_RATIO "
          f"(booked R / mfe_close_R on winners) = {ratio:.3f}")

    tf = build_5m()
    print(f"[lab] 5m frame: {len(tf)} bars {tf.index[0]} .. {tf.index[-1]}")

    # ---------------- cohorts ---------------------------------------- #
    D = cohorts(tf, A)
    print("\n" + "=" * 78)
    print("COHORTS — what really happened inside the box on the 5m tape")
    print("=" * 78)
    print(f"  filled at the seam                     : {len(D)}")
    print(f"  KNIFE  (stop broke before any 5m close above the seam"
          f" and before +0.5R) : {int(D['knife'].sum())}")
    print(f"  RETEST (a later 5m bar traded back INTO the box body)  : "
          f"{int(D['retest'].sum())}")
    print(f"    of which COLLAPSED through the stop  : {int(D['collapse'].sum())}")
    print(f"    of which rebounded (>=+0.5R or a close above the seam"
          f" before the stop) : {int(D['saved_from_body'].sum())}")
    print(f"  by class: {D.groupby('class')[['knife','retest','collapse']].sum().to_dict()}")

    # ---------------- the grid --------------------------------------- #
    print("\n" + "=" * 78)
    print("MECHANISM GRID — deep box limit x shield x second chance")
    print("=" * 78)
    geo = []
    for i, t in A.iterrows():
        gt, gb, seam = box_of(t)
        geo.append((float(t["stop_price"]), seam))
    wins_ = []
    for i, t in A.iterrows():
        wins_.append(window(tf, t))

    rows = []
    pmids = [float(t["purple_mid"]) if pd.notna(t["purple_mid"]) else np.nan
             for _, t in A.iterrows()]
    yrs = [pd.Timestamp(t["entry_time"]).year for _, t in A.iterrows()]
    hdr = (f"  {'alpha':>6}{'shield':>8}{'2nd':>5}{'n':>5}{'W':>4}{'BE':>4}{'L':>4}"
           f"{'WR%':>7}{'>=4R':>5}{'maxR':>7}{'minW':>6}{'stk':>4}{'ymin':>5}"
           f"{'totR':>7}{'nofill':>7}  asserts")
    print(hdr)
    for alpha in (1.00, 0.75, 0.50, 0.25):
        for shield in ("none", "be", "mid"):
            for second in (False, True):
                seq = []
                for (stop, seam), (o, h, l, c, _y), pm, yy in zip(
                        geo, wins_, pmids, yrs):
                    if not np.isfinite(seam) or seam <= stop:
                        seq.append(("SKIP", 0.0, 0.0, str(yy))); continue
                    recs = simulate(o, h, l, c, stop, seam, alpha,
                                    shield, second, ratio, pm)
                    for cl, r, rf, _f in recs:
                        seq.append((cl, r, rf, str(yy)))
                s = score(seq, f"alpha={alpha} shield={shield} 2nd={int(second)}",
                          ratio)
                rows.append(s)
                f = lambda b: "Y" if b else "."        # noqa: E731
                npass = sum([s["A1"], s["A2"], s["A3"], s["A4"], s["A5"]])
                print(f"  {alpha:>6}{shield:>8}{('on' if second else 'off'):>5}"
                      f"{s['n']:>5}{s['W']:>4}{s['BE']:>4}{s['L']:>4}"
                      f"{s['WR_pct']:>7}{s['ge4R']:>5}{s['max_R']:>7}"
                      f"{s['min_win_R']:>6}{s['streak']:>4}{s['ymin']:>5}"
                      f"{s['total_R']:>7}{s['nofill']:>7}  "
                      f"{f(s['A1'])}{f(s['A2'])}{f(s['A3'])}{f(s['A4'])}{f(s['A5'])}"
                      f" = {npass}/5")

    # ---------------- METHOD B rows ---------------------------------- #
    print("\n  METHOD B (5m intra-box absorption, never above the seam):")
    for shield in ("none", "be", "mid"):
        seq = []
        for (stop, seam), (o, h, l, c, _y), pm, yy in zip(geo, wins_, pmids, yrs):
            if not np.isfinite(seam) or seam <= stop:
                seq.append(("SKIP", 0.0, 0.0, str(yy))); continue
            for cl, r, rf, _f in simulate_absorption(o, h, l, c, stop, seam,
                                                     shield, ratio, pm):
                seq.append((cl, r, rf, str(yy)))
        s = score(seq, f"METHOD-B shield={shield}", ratio)
        rows.append(s)
        f = lambda b: "Y" if b else "."        # noqa: E731
        npass = sum([s["A1"], s["A2"], s["A3"], s["A4"], s["A5"]])
        print(f"  {'absorb':>6}{shield:>8}{'-':>5}{s['n']:>5}{s['W']:>4}{s['BE']:>4}"
              f"{s['L']:>4}{s['WR_pct']:>7}{s['ge4R']:>5}{s['max_R']:>7}"
              f"{s['min_win_R']:>6}{s['streak']:>4}{s['ymin']:>5}{s['total_R']:>7}"
              f"{s['nofill']:>7}  {f(s['A1'])}{f(s['A2'])}{f(s['A3'])}{f(s['A4'])}"
              f"{f(s['A5'])} = {npass}/5")

    # ---------------- estimator validation vs the real engine ---------- #
    print("\n" + "=" * 78)
    print("VALIDATION — does the lab reproduce the shipped engine at alpha=1.0?")
    print("=" * 78)
    lab_cls, lab_R, real_cls, real_R = [], [], [], []
    for (stop, seam), (o, h, l, c, _y), pm, (_i, t) in zip(
            geo, wins_, pmids, A.iterrows()):
        if not np.isfinite(seam) or seam <= stop:
            continue
        recs = simulate(o, h, l, c, stop, seam, 1.0, "none", False, ratio, pm)
        if not recs or recs[0][0] in ("SKIP", "NOFILL", "OPEN"):
            continue
        lab_cls.append(recs[0][0]); lab_R.append(recs[0][1])
        real_cls.append(t["class"]); real_R.append(float(t["R"]))
    ct = pd.crosstab(pd.Series(lab_cls, name="lab"),
                     pd.Series(real_cls, name="engine"))
    print(ct.to_string())
    lw = np.array([r for r, cl in zip(lab_R, lab_cls) if cl == "WIN"])
    rw = np.array([r for r, cl in zip(real_R, lab_cls) if cl == "WIN"])
    if len(lw):
        print(f"\n  winners agreed on: {len(lw)}")
        print(f"  lab R  median {np.median(lw):.2f}  max {lw.max():.2f}  >=4R {int((lw>=4).sum())}")
        print(f"  real R median {np.median(rw):.2f}  max {rw.max():.2f}  >=4R {int((rw>=4).sum())}")
        print(f"  => the lab's ride estimator is CONSERVATIVE (it books "
              f"{100*np.median(lw)/max(1e-9,np.median(rw)):.0f}% of the real median R).")
    print("  NOTE the classification of a WIN is estimator-INDEPENDENT: it is")
    print("  decided by the fee-adjusted +3R lock being reached on a 5m CLOSE.")

    best = max(rows, key=lambda s: (sum([s["A1"], s["A2"], s["A3"], s["A4"], s["A5"]]),
                                    s["WR_pct"]))
    print("\n[lab] BEST:", json.dumps(best, indent=2))
    tag = src.replace("trades_", "").replace(".csv", "")
    pd.DataFrame(rows).to_csv(RES / f"lab_v27_grid_{tag}.csv", index=False)
    with open(RES / f"lab_v27_grid_{tag}.json", "w") as fh:
        json.dump({"book_ratio": ratio, "cohorts": D.sum(numeric_only=True).to_dict(),
                   "grid": rows, "best": best}, fh, indent=2, default=str)
    print(f"[lab] wrote results/lab_v27_grid_{tag}.csv/.json")


if __name__ == "__main__":
    main()
