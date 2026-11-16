# =============================================================================
#  "HAMMER AFTER THE RAID" — the 15-minute scalper, built literally.
# =============================================================================
#
#  THE SETUP, AS DESCRIBED
#  -----------------------
#   1. On 15m, find a LOW whose liquidity got raided: a candle drives its WICK
#      under that low but its BODY CLOSES back above it.
#   2. Two to three candles later the entry forms:
#        C1 = a big BULLISH reversal candle
#        C2 = a BEARISH candle (a "hammer" shape is ideal, not required).
#             Its wick must NOT reach the midpoint of C1 — even a hair above
#             the 50% counts.
#        ENTRY  = close of C2
#        STOP   = below C2's low by a fixed fraction
#        TARGET = the first swing HIGH that preceded the raided low, taken a
#                 hair under the wick of that high's candle.
#   3. Variant A (called strongest): the move left a FAIR VALUE GAP.
#      Variant B (weaker): same, no FVG.
#
#  TESTING RULES
#  -------------
#   * 15m decisions, FILLS RESOLVED ON 1-MINUTE BARS.  Inside one bar the stop
#     is assumed to fill before the target (pessimistic).
#   * Entry = open of the first 1m bar after C2 closes.  You cannot trade a
#     close you have not seen yet.
#   * Geometry is built ONCE; the stop distance is swept afterwards, because
#     the stop is the parameter the whole thing lives or dies on.
# =============================================================================

from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ict_vision.data.loader import load_all, to_bars


def swing_pivots(bars, left=3, right=3):
    """Pivot highs/lows.  A pivot at i is only KNOWN at i+right; downstream
    code uses the confirmation bar, never i itself, so nothing peeks."""
    n = bars.n
    h, l = bars.h, bars.l
    hi_conf = np.full(n, -1, np.int64)
    lo_conf = np.full(n, -1, np.int64)
    for i in range(left, n - right):
        sh = h[i - left:i + right + 1]
        sl = l[i - left:i + right + 1]
        if h[i] == sh.max() and np.count_nonzero(sh == h[i]) == 1:
            hi_conf[i] = i + right
        if l[i] == sl.min() and np.count_nonzero(sl == l[i]) == 1:
            lo_conf[i] = i + right
    return hi_conf, lo_conf


def build_setups(b15, *, piv_left=3, piv_right=3, wait_lo=2, wait_hi=3,
                 big_body_q=0.70, big_body_mult=1.2, mid_mode="body",
                 max_look=3):
    """Geometry only.  Stop/target are applied later so they can be swept."""
    n = b15.n
    o, h, l, c = b15.o, b15.h, b15.l, b15.c
    hi_conf, lo_conf = swing_pivots(b15, piv_left, piv_right)

    body = np.abs(c - o)
    med_body = pd.Series(body).rolling(200, min_periods=40).median().to_numpy()

    out = []
    last_hi_i, last_hi_p = -1, np.nan
    pending_lo = []                      # (pivot_i, price, confirmed_at)

    for t in range(300, n):
        for i in np.nonzero((lo_conf >= 0) & (lo_conf == t))[0]:
            pending_lo.append((int(i), float(l[i])))
        for i in np.nonzero((hi_conf >= 0) & (hi_conf == t))[0]:
            last_hi_i, last_hi_p = int(i), float(h[i])
        if not pending_lo:
            continue

        for (li, lp) in list(pending_lo):
            if t <= li:
                continue
            # ---- 1. THE RAID: wick under the low, body closes back above
            if not (l[t] < lp and c[t] > lp):
                continue
            if not (last_hi_i >= 0 and last_hi_i < li):
                continue
            tgt_hi = last_hi_p
            found = False
            # ---- 2. ENTRY PATTERN, wait_lo..wait_hi bars after the raid
            for k in range(wait_lo, wait_hi + 1):
                i1 = t + k
                if i1 + max_look + 2 >= n:
                    break
                # C1 = big bullish reversal candle
                if not (c[i1] > o[i1]):
                    continue
                ref = med_body[i1]
                if not np.isfinite(ref) or body[i1] < big_body_mult * ref:
                    continue
                if body[i1] < np.quantile(body[max(0, i1 - 200):i1], big_body_q):
                    continue
                mid = (0.5 * (o[i1] + c[i1]) if mid_mode == "body"
                       else 0.5 * (h[i1] + l[i1]))
                # C2 = first BEARISH candle after C1 (a bullish one may sit
                # between them: "either another bullish candle [then] bearish")
                for j in range(i1 + 1, i1 + 1 + max_look):
                    if not (c[j] < o[j]):
                        continue
                    if l[j] < mid:                 # wick must not reach 50%
                        continue
                    fvg = bool(h[i1 - 1] < l[j]) if i1 - 1 >= 0 else False
                    out.append(dict(
                        t_raid=int(t), raid_level=float(lp), t_c1=int(i1), t_c2=int(j),
                        entry=float(c[j]), c2_low=float(l[j]), c1_high=float(h[i1]),
                        c1_low=float(l[i1]), c1_body=float(body[i1]),
                        tgt_hi=float(tgt_hi),
                        fvg=fvg, fvg_gap=float(l[j] - h[i1 - 1]) if i1 - 1 >= 0 else 0.0,
                        depth=float((h[i1] - l[j]) / max(h[i1] - l[i1], 1e-12)),
                        raid_depth=float((lp - l[t]) / max(lp, 1e-12)),
                    ))
                    found = True
                    break
                if found:
                    break
            if found:
                pending_lo.remove((li, lp))
        pending_lo = [x for x in pending_lo if t - x[0] < 400]
    return pd.DataFrame(out)


def map_15m_to_1m(b15, b1):
    a = np.searchsorted(b1.idx, b15.idx, side="left")
    b = np.searchsorted(b1.idx, b15.idx + pd.Timedelta(minutes=15), side="left")
    return a, np.maximum(np.minimum(b, b1.n), a + 1)


def resolve_all(setup_df, b1, m15_a, m15_b, *, stop_pct=0.0002, tp_pct=0.0002,
                cost_rt=0.0, max_hold_m15=96):
    """Vectorised per-trade resolution on 1m bars.  Stop before target."""
    recs = []
    for tr in setup_df.to_dict("records"):
        j = int(tr["t_c2"])
        if j + 1 >= len(m15_a):
            continue
        a = int(m15_a[j + 1])
        end = int(m15_b[min(len(m15_a) - 1, j + max_hold_m15)])
        if end <= a:
            continue
        entry = float(b1.o[a])
        stop = float(tr["c2_low"]) * (1.0 - stop_pct)   # distance below the low
        tgt = float(tr["tgt_hi"]) * (1.0 - tp_pct)
        risk = entry - stop
        if risk <= 0 or tgt <= entry:
            continue
        sl = b1.l[a:end]
        sh = b1.h[a:end]
        si = np.nonzero(sl <= stop)[0]
        ti = np.nonzero(sh >= tgt)[0]
        i_s = int(si[0]) if si.size else 10 ** 9
        i_t = int(ti[0]) if ti.size else 10 ** 9
        # --- direction quality with NO stop at all (was the read right?)
        ni = np.nonzero(sl <= stop)[0]      # unused; keep for clarity
        if i_t < 10 ** 9:
            dir_ok = 1
            bars_to_tgt = i_t
        else:
            dir_ok = 0
            bars_to_tgt = -1
        if i_s < 10 ** 9 and i_s <= i_t:
            res, pnl, bars = "stop", stop - entry, i_s
        elif i_t < 10 ** 9:
            res, pnl, bars = "target", tgt - entry, i_t
        else:
            res, pnl, bars = "timeout", float(b1.c[end - 1]) - entry, end - 1 - a
        recs.append(dict(res=res, r=float((pnl - cost_rt) / risk), pnl=float(pnl),
                         risk=float(risk), rr=float((tgt - entry) / risk),
                         bars=int(bars), t_c2=j, exit_time=b1.idx[a + int(bars)],
                         fvg=tr["fvg"], depth=tr["depth"], entry=entry))
    return pd.DataFrame(recs)


def period_table(df, keyfn, label, show=False):
    g = df.groupby(df["exit_time"].map(keyfn))
    rows = [dict(period=k, n=len(s), win=float((s.r > 0).mean()), meanR=float(s.r.mean()),
                 pnl=float(s.pnl.sum()), tpn=float((s.res == "target").mean()))
            for k, s in g if len(s)]
    t = pd.DataFrame(rows).sort_values("period")
    npos = int((t.meanR > 0).sum())
    print(f"\n  {label}: {len(t)} periods, {npos} with meanR>0 ({npos/max(len(t),1)*100:.0f}%)")
    if show:
        print(t.round(3).to_string(index=False))
    return t


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="smc_v4_multisleeve_package/data/XAUUSD_1m_histdata")
    ap.add_argument("--label", default="XAUUSD")
    ap.add_argument("--out", default="ict_vision/results_scalp")
    ap.add_argument("--cache", default="/tmp/scalp_15m.pkl")
    ap.add_argument("--spread", type=float, default=0.0)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--mid", default="body", choices=["body", "range"])
    ap.add_argument("--fill-minutes", type=int, default=1,
                    help="resolution used for fills (1 for histdata, 5 for BTC)")
    a = ap.parse_args()

    print(f"loading {a.label} …")
    b1 = load_all(a.data, minutes=a.fill_minutes, cache=a.cache)
    b15 = load_all(a.data, minutes=15, cache=a.cache)
    if a.limit:
        b15 = to_bars(pd.DataFrame({"o": b15.o[:a.limit], "h": b15.h[:a.limit],
                                    "l": b15.l[:a.limit], "c": b15.c[:a.limit]},
                                   index=b15.idx[:a.limit]))
    print(f"  fill {a.fill_minutes}m {b1.n:,}   15m {b15.n:,}   {b15.idx[0]} -> {b15.idx[-1]}")
    m15_a, m15_b = map_15m_to_1m(b15, b1)

    setups = build_setups(b15, mid_mode=a.mid)
    print(f"\n  candidate setups found: {len(setups)}")
    if not len(setups):
        print("  the pattern never occurs as specified.")
        return 0
    print(f"  with FVG (variant A)  : {int(setups.fvg.sum())}")
    print(f"  without FVG (variant B): {int((~setups.fvg).sum())}")

    # -------------------------------------------------- the stop is everything
    print("\n================= STOP-DISTANCE SWEEP (the decisive parameter) =================")
    print("   stop%      n    win%   meanR      t   tgt%   mean RR")
    best = None
    for sp in (0.0002, 0.002, 0.005, 0.010, 0.020, 0.035, 0.060, 0.100):
        df = resolve_all(setups, b1, m15_a, m15_b, stop_pct=sp, cost_rt=a.spread)
        if len(df) < 20:
            continue
        R = df.r.to_numpy()
        t = R.mean() / (R.std() / np.sqrt(len(R)))
        line = (f"  {sp*100:6.3f}%  {len(df):5d}  {np.mean(R>0)*100:5.1f}%  "
                f"{R.mean():+7.3f}  {t:+6.2f}  {np.mean(df.res=='target')*100:4.0f}%  {df.rr.mean():7.2f}")
        print(line)
        if best is None or R.mean() > best[1]:
            best = (sp, R.mean(), df)
    sp_star, _, df = best
    print(f"\n  -> best stop distance {sp_star*100:.3f}%  (you specified 0.020%)")

    R = df.r.to_numpy()
    tstat = R.mean() / (R.std() / np.sqrt(len(R)))
    print("\n================= THE PATTERN AT THAT STOP =================")
    print(f"  trades {len(R)}   win {np.mean(R>0)*100:.1f}%   meanR {R.mean():+.3f}   t {tstat:+.2f}")
    print(f"  medianR {np.median(R):+.3f}   worst {R.min():+.2f}   best {R.max():+.2f}")
    print(f"  exits   {df.res.value_counts().to_dict()}")
    print(f"  mean R:R offered {df.rr.mean():.2f}  mean retrace depth into C1 {df.depth.mean():.2f}")

    print("\n  --- VARIANT SPLIT (your ranking) ---")
    for fvg, sub in df.groupby("fvg"):
        tag = "A: WITH fair value gap (you call this strongest)" if fvg else "B: NO fair value gap (you call this weaker)"
        rr = sub.r.to_numpy()
        print(f"  {tag}\n     n={len(sub)}  win {np.mean(rr>0)*100:.1f}%  meanR {rr.mean():+.3f}  "
              f"t {rr.mean()/(rr.std()/np.sqrt(len(rr))):+.2f}  "
              f"target-hit {np.mean(sub.res=='target')*100:.0f}%")

    print("\n  --- DIRECTION QUALITY WITH NO STOP AT ALL ---")
    print(f"  reached the target before timing out: {np.mean(df.res!='timeout')*100:.0f}%"
          f"   (target {np.mean(df.res=='target')*100:.0f}%)")
    print(f"  mean bars to target: {df[df.res=='target'].bars.median() if (df.res=='target').any() else float('nan')}")

    print("\n  --- BY YEAR ---")
    yr = df.groupby(df.exit_time.dt.year)
    print(pd.DataFrame({"n": yr.size(), "win": yr.r.apply(lambda s: (s > 0).mean()),
                        "meanR": yr.r.mean(), "pnl": yr.pnl.sum()}).round(3).to_string())

    pm = period_table(df, lambda d: f"{d.year}-{d.month:02d}", "BY MONTH", show=True)
    pw = period_table(df, lambda d: f"{d.isocalendar()[0]}-W{d.isocalendar()[1]:02d}", "BY WEEK")
    pdd = period_table(df, lambda d: str(d.date()), "BY DAY")
    print(f"\n  trades per month: median {pm.n.median():.1f}, mean {pm.n.mean():.1f}")
    print(f"  trades per week : median {pw.n.median():.1f}, mean {pw.n.mean():.1f}")
    print(f"  trades per day  : median {pdd.n.median():.1f}, mean {pdd.n.mean():.1f}")

    os.makedirs(a.out, exist_ok=True)
    df.to_csv(os.path.join(a.out, f"scalp_{a.label}_trades.csv"), index=False)
    pm.to_csv(os.path.join(a.out, f"scalp_{a.label}_monthly.csv"), index=False)
    print(f"\nwrote {a.out}/scalp_{a.label}_trades.csv, _monthly.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
