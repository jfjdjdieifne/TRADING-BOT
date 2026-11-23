#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lab_v29_stop_entry.py — "ضع أمر الشراء مكان الستوب لوس"
Stop-Loss Level as Buy Entry / ICT Turtle Soup inducement.

EVERY number in this lab comes from the LIVE ENGINE
(`strategy_v29_ict_turtle_soup.run_backtest`), never from an external
re-simulation. The lab only monkey-patches `ENTRY_ARM`, runs the real
engine over the real 5m dataset (2021-01-01 .. 2026-10-31), and scores the
result with the engine's OWN `summarize()`, so the metrics are the same
code path that prints the five asserts in an official run.

Why the live engine and not a re-simulation (the v28 lesson):
  * lab_v27_exact.py had to discount winners by BOOK_RATIO = 0.673 because
    it could not reproduce the engine's management; v28 then proved that a
    post-hoc reading of a frozen trade list does not survive contact with
    the engine (a filter reading 33.12% @ n=199 became 24.24% @ n=40 live,
    because rejecting a candidate changes WHICH setup draws next).
  * Moving the order from the seam down to old_stop_px changes the fill
    time, the risk, the lock line, the target ladder, the consumed-range
    book, the loss streak and the slot contention. Only a live run sees
    all of that.

ARMS (geometry frozen at setup-DRAW time, zero lookahead)
    seam  v27/v28 baseline: BUY LIMIT at seam, stop at old_stop_px
    A     Mirror Stop Entry       : order = old_stop_px,   stop = old_stop - H
    B     Deeper BlueBox_SSL      : order = old_stop_px,   stop = nearest
                                    ACTIVE SSL bottom below it, else -1.5H
    C     Turtle Soup sweep&reclaim: no resting order; a bar must hunt
                                    old_stop_px (low <= it) and reclaim it
                                    (old_stop_px < close <= seam); buy that
                                    CLOSE, stop = min(wick, fill - 0.5H)
    D     50% Stop-to-Seam        : order = old_stop + 0.5H, stop = old_stop - 0.5H
    where H = seam - old_stop_px is the v27 RiskHeight. A and D keep risk
    at exactly H, so the 0.2% round-trip fee keeps the same share of 1R
    that it has in v27 (this is the flaw the v29 brief correctly identified
    in lab_v27's alpha sweep, which shrank 1R and let the fee eat it).

USAGE
    python3 lab_v29_stop_entry.py smoke          # 6-month sanity per arm (~1 min each)
    python3 lab_v29_stop_entry.py run [ARM ...]  # full live runs (~6 min each)
    python3 lab_v29_stop_entry.py score          # re-score saved trade files
    python3 lab_v29_stop_entry.py convert ARM    # the 161-loss conversion audit
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
sys.path.insert(0, str(HERE))

ARMS = ["seam", "A", "B", "C", "D"]


def _d(v):
    """Box columns are written as Python dict reprs, not JSON."""
    if isinstance(v, dict):
        return v
    return ast.literal_eval(v)
MIN_R = 3.0
YEARS = [str(y) for y in range(2021, 2027)]


# ==================================================================== #
# live engine driver
# ==================================================================== #
BOX_GATE = None      # set by main() from argv: True/False/None(=engine default)


def drive(arm: str, start: str, end: str, save: bool = True):
    """Run the REAL engine with ENTRY_ARM = arm and score it with the
    engine's own summarize(). Returns (metrics_dict, trades DataFrame)."""
    import strategy_v29_ict_turtle_soup as S
    S.ENTRY_ARM = arm
    S.MANAGE_5M = False            # v29: clean execution-frame management
    if BOX_GATE is not None:
        S.ARM_BOX_GATE = BOX_GATE
    print(f"\n########## LIVE ENGINE RUN · arm={arm} · {start}..{end} ##########",
          flush=True)
    run = S.run_backtest(S.DATA_DIR, start, end, tag=f"v29{arm}")
    tr = pd.DataFrame(run["trades"])
    summ = S.summarize(run)
    if save:
        tag = arm if BOX_GATE in (None, False) else f"{arm}_boxgate"
        tr.to_csv(RESULTS / f"trades_v29_{tag}.csv", index=False)
        with open(RESULTS / f"summary_v29_{tag}.json", "w") as f:
            json.dump(summ, f, indent=2, default=str)
        if len(run["equity"]):
            run["equity"].to_csv(RESULTS / f"equity_v29_{tag}.csv")
    m = metrics(arm, tr, summ, run["count"])
    m["_count"] = run["count"]
    return m, tr


def metrics(arm, tr, summ, count=None):
    """The full measurement the v29 brief asks for, per arm."""
    n = len(tr)
    W = int((tr["class"] == "WIN").sum()) if n else 0
    B = int((tr["class"] == "BE").sum()) if n else 0
    L = int((tr["class"] == "LOSS").sum()) if n else 0
    wr = 100 * W / (W + L) if W + L else 0.0
    wins = tr[tr["class"] == "WIN"] if n else tr
    yr = (tr.entry_time.astype(str).str[:4].value_counts()
          .reindex(YEARS).fillna(0).astype(int).to_dict()) if n else \
        {y: 0 for y in YEARS}
    # both streak readings, disclosed side by side as always
    cur = best = cons = cons_best = 0
    for c in (tr["class"] if n else []):
        if c == "LOSS":
            cur += 1; best = max(best, cur)
            cons += 1; cons_best = max(cons_best, cons)
        elif c == "WIN":
            cur = 0; cons = 0
        else:
            cur = 0          # a BE resets the BE-resets reading only
    net = float(tr.net_pnl.sum()) if n else 0.0
    def fnum(k, d=0.0):
        v = summ.get(k)
        return float(v) if isinstance(v, (int, float)) else d
    m = dict(
        arm=arm, n=n, W=W, BE=B, L=L, wr=round(wr, 2),
        min_winner_R=round(float(wins.R.min()), 2) if len(wins) else None,
        ge4R=int((tr.R >= 4).sum()) if n else 0,
        ge10R=int((tr.R >= 10).sum()) if n else 0,
        maxR=round(float(tr.R.max()), 2) if n else 0.0,
        totR=round(float(tr.R.sum()), 2) if n else 0.0,
        avg_R=round(float(tr.R.mean()), 3) if n else 0.0,
        streak_be_resets=best, streak_conservative=cons_best,
        yearly=yr, ymin=min(yr[y] for y in YEARS[:5]),
        net_pct=round(100 * net / 200.0, 2),
        net_usd=round(net, 2),
        pf=round(fnum("profit_factor"), 3),
        max_dd_pct=round(fnum("max_drawdown_pct"), 2),
        end_equity=round(fnum("end_equity", 200.0), 2),
        fees=round(fnum("fees"), 2),
        median_risk_pct=round(float(tr.risk_pct.median()), 4) if n else None,
        fill_v29=int((count or {}).get(f"fill_v29_{arm}", 0)),
        arm_drawn=int((count or {}).get(f"v29_arm_{arm}_drawn", 0)),
        mit_v29=int((count or {}).get("setup_mitigated_v29", 0)),
        wall_v29=int((count or {}).get("reject_wall_within_3r_v29", 0)),
        sacred=int((count or {}).get("sacred_law_seam_ok", 0)),
    )
    m["A1"] = m["wr"] >= 60.0
    m["A2"] = (m["min_winner_R"] is None) or m["min_winner_R"] >= MIN_R - 1e-9
    m["A3"] = m["ge4R"] >= 5 and m["maxR"] >= 6.0
    m["A4"] = m["streak_be_resets"] <= 3
    m["A5"] = m["n"] >= 150 and m["ymin"] >= 12
    m["passed"] = sum(bool(m[k]) for k in ("A1", "A2", "A3", "A4", "A5"))
    return m


def show(m):
    print(f"[{m['arm']:>4}] n={m['n']:4d}  {m['W']:3d}W/{m['BE']:3d}BE/"
          f"{m['L']:3d}L  WR={m['wr']:6.2f}%  minWin={m['min_winner_R']}  "
          f">=4R={m['ge4R']:3d}  maxR={m['maxR']:6.2f}  totR={m['totR']:8.2f}",
          flush=True)
    print(f"       net={m['net_pct']:+7.2f}% (${m['end_equity']})  "
          f"PF={m['pf']}  maxDD={m['max_dd_pct']}%  "
          f"streak={m['streak_be_resets']}/{m['streak_conservative']}  "
          f"yearly={m['yearly']}", flush=True)
    a = "".join("P" if m[k] else "F" for k in ("A1", "A2", "A3", "A4", "A5"))
    print(f"       asserts A1..A5 = {a}  -> {m['passed']}/5", flush=True)
    for k in ("A1", "A2", "A3", "A4", "A5"):
        print(f"       ASSERT{k[-1]} {'PASSED' if m[k] else 'FAILED'}", flush=True)


# ==================================================================== #
# the conversion audit: what happened to the trades that were hunted
# ==================================================================== #
def setup_key(df, seam_col, stop_col):
    """A setup is identified by its geometry, which is identical across
    arms: the seam (min(green.y_top, yellow.y_bottom)) and old_stop_px,
    plus the execution frame. Rounded to the CSV's 2 decimals."""
    if seam_col in df.columns:
        seam = df[seam_col].astype(float).round(2)
    else:                                   # v27 file: rebuild the seam
        gt = df.green.apply(lambda d: float(_d(d)["top"]))
        yb = df.yellow.apply(lambda d: float(_d(d)["bottom"]))
        seam = pd.concat([gt, yb], axis=1).min(axis=1).round(2)
    stop = df[stop_col].astype(float).round(2)
    return list(zip(seam, stop, df.exec_tf))


def convert(arm):
    v27 = pd.read_csv(RESULTS / "trades_v27.csv")
    f = RESULTS / f"trades_v29_{arm}.csv"
    if not f.exists():
        print(f"no trades_v29_{arm}.csv yet - run: "
              f"python3 lab_v29_stop_entry.py run {arm}")
        return None
    v29 = pd.read_csv(f)
    k27 = setup_key(v27, "v29_seam_px", "stop_price")
    k29 = setup_key(v29, "v29_seam_px", "v29_old_stop_px")
    v27["key"] = k27
    v29["key"] = k29
    # the hunted population in v27: trades whose stop was actually traded
    # into (LOSS = stopped out; BE = shielded on the way; also record WIN)
    idx = {}
    for i, k in enumerate(v29["key"]):
        idx.setdefault(k, []).append(i)
    rows = []
    for i, t in v27.iterrows():
        hits = idx.get(t["key"], [])
        j = hits[0] if hits else None
        rows.append(dict(key=t["key"], v27_class=t["class"],
                         v27_R=round(float(t.R), 2),
                         v27_exit=t.exit_reason,
                         v29_class=(v29.at[j, "class"] if j is not None
                                    else "NO_FILL"),
                         v29_R=(round(float(v29.at[j, "R"]), 2)
                                if j is not None else np.nan),
                         v29_entry=(v29.at[j, "entry_price"]
                                    if j is not None else np.nan)))
    d = pd.DataFrame(rows)
    print(f"\n=== CONVERSION AUDIT · arm {arm} vs v27 (matched on setup "
          f"geometry: seam + old_stop + frame) ===")
    print(f"    v27 trades: {len(d)}   matched to an arm-{arm} trade: "
          f"{int((d.v29_class != 'NO_FILL').sum())}")
    ct = pd.crosstab(d.v27_class, d.v29_class)
    print(ct.to_string())
    for src in ("LOSS", "BE", "WIN"):
        sub = d[d.v27_class == src]
        if not len(sub):
            continue
        w = int((sub.v29_class == "WIN").sum())
        b = int((sub.v29_class == "BE").sum())
        l = int((sub.v29_class == "LOSS").sum())
        nf = int((sub.v29_class == "NO_FILL").sum())
        print(f"    v27 {src:5s} (n={len(sub):3d}) -> arm {arm}: "
              f"WIN {w:3d} · BE {b:3d} · LOSS {l:3d} · never filled {nf:3d}")
    d.to_csv(RESULTS / f"convert_v29_{arm}.csv", index=False)
    print(f"    wrote results/convert_v29_{arm}.csv")
    return d


# ==================================================================== #


# ==================================================================== #
# OFFLINE CROSS-CHECK (not the measurement - the live engine is)
# ==================================================================== #
FEE = 0.001


def predict(arm="A", cap_bars=4032):
    """Independent, zero-lookahead cross-check of what an arm does to the
    v27 population. It walks the 5m tape forward from each v27 FILL, waits
    for price to trade down to the arm's order level (that is the fill),
    then resolves the arm's own lock/stop geometry from there.

    It is NOT a substitute for the live engine: it ignores slot contention,
    the consumed-range book, streak state and the redraw of later setups.
    Its only job is to answer the v29 brief's question - of the trades that
    were hunted through old_stop_px in v27, how many become winners when the
    order rests at the hunted level? - before the 30-minute live runs land.

    cap_bars bounds the walk (4032 x 5m = 14 days); unresolved trades are
    reported separately, never silently booked."""
    from engine.causal_primitives import load_asset_ohlcv, resample_causal_tf
    tf5 = resample_causal_tf(load_asset_ohlcv(
        HERE / "data" / "BTCUSD_5m", include_stems=None), "5min")
    idx = tf5.index
    O = tf5.Open.values; H = tf5.High.values
    L = tf5.Low.values; C = tf5.Close.values
    v27 = pd.read_csv(RESULTS / "trades_v27.csv")
    rows = []
    for _, t in v27.iterrows():
        g = _d(t.green)
        y = _d(t.yellow)
        seam = min(float(g["top"]), float(y["bottom"]))
        ost = float(t.stop_price)
        h = seam - ost
        if h <= 0:
            continue
        if arm in ("A", "B", "C"):
            lvl = ost
        elif arm == "D":
            lvl = ost + 0.5 * h
        else:
            lvl = seam
        if arm == "A":
            nstop = ost - h
        elif arm == "B":
            nstop = ost - 1.5 * h          # offline: the fallback depth
        elif arm == "C":
            nstop = None                   # measured at fill from the wick
        elif arm == "D":
            nstop = ost - 0.5 * h
        else:
            nstop = ost
        i0 = idx.searchsorted(pd.Timestamp(t.entry_time), side="right")
        i1 = min(len(tf5), i0 + cap_bars)
        fill = np.nan; fr = np.nan; res = "NO_FILL"; rmax = np.nan
        back_to_seam = False
        j = i0
        while j < i1:
            if arm == "C":
                if L[j] <= ost and ost < C[j] <= seam:
                    fill = C[j]
                    nstop = min(L[j], fill - 0.5 * h)
                    fr = j
                    break
            elif L[j] <= lvl:
                fill = lvl if O[j] >= lvl else O[j]
                fr = j
                break
            j += 1
        if not np.isnan(fill):
            risk = fill - nstop
            if risk <= 2 * FEE * fill:
                res = "FEE_FLOOR"
            else:
                lock = (fill * (1 + FEE) + MIN_R * risk) / (1 - FEE)
                rmax = 0.0
                k = fr
                while k < i1:
                    if C[k] >= seam:
                        back_to_seam = True
                    r_now = ((C[k] - fill) - fill * FEE - C[k] * FEE) / risk
                    rmax = max(rmax, r_now)
                    # conservative intra-bar order: the stop is honoured
                    # before the lock on the same bar
                    if L[k] <= nstop:
                        px = nstop if O[k] >= nstop else O[k]
                        fr_ = ((px - fill) - fill * FEE - px * FEE) / risk
                        res = "LOSS" if fr_ < -0.05 else "BE"
                        break
                    if C[k] >= lock:
                        res = "WIN"
                        break
                    k += 1
                else:
                    res = "OPEN_AT_CAP"
                fr = rmax
        rows.append(dict(entry_time=t.entry_time, v27_class=t["class"],
                         v27_R=round(float(t.R), 2), v27_exit=t.exit_reason,
                         exec_tf=t.exec_tf, arm=arm, res=res,
                         fill=fill, rmax_close=(None if np.isnan(fr)
                                                else round(float(fr), 2)),
                         back_to_seam=back_to_seam))
    d = pd.DataFrame(rows)
    d.to_csv(RESULTS / f"predict_v29_{arm}.csv", index=False)
    print(f"\n=== OFFLINE CROSS-CHECK · arm {arm} · cap {cap_bars} 5m bars "
          f"(14 days) ===")
    print(f"    v27 trades analysed: {len(d)}")
    print("    outcome of the arm on that population:")
    print(d.res.value_counts().to_string())
    for src in ("LOSS", "BE", "WIN"):
        sub = d[d.v27_class == src]
        if not len(sub):
            continue
        vc = sub.res.value_counts().to_dict()
        print(f"    v27 {src:5s} n={len(sub):3d} -> "
              + "  ".join(f"{k}:{v}" for k, v in sorted(vc.items())))
    dec = d[d.res.isin(["WIN", "LOSS"])]
    if len(dec):
        print(f"    decided WR of the arm on the v27 population: "
              f"{100 * (dec.res == 'WIN').mean():.2f}% "
              f"({(dec.res == 'WIN').sum()}W/{(dec.res == 'LOSS').sum()}L)")
    print(f"    back to the seam (= +1R from the deep fill): "
          f"{int(d.back_to_seam.sum())} of {int((d.res != 'NO_FILL').sum())} "
          f"filled")
    print(f"    wrote results/predict_v29_{arm}.csv")
    return d



def table(ms):
    ref = []
    for tag, fn in (("v25", "summary_v25.json"), ("v27", "summary_v27.json")):
        p = RESULTS / fn
        if p.exists():
            j = json.load(open(p))
            ref.append(dict(arm=tag, n=j.get("trades"), W=j.get("wins"),
                            BE=j.get("breakevens"), L=j.get("losses"),
                            wr=j.get("win_rate_pct"),
                            min_winner_R=j.get("min_winner_R"),
                            ge4R=j.get("runners_4r_plus"),
                            maxR=j.get("max_winner_R"),
                            totR=None, net_pct=j.get("net_pct"),
                            pf=j.get("profit_factor"),
                            max_dd_pct=j.get("max_drawdown_pct"),
                            streak_be_resets=j.get("max_consecutive_losses"),
                            ymin=None, passed=None))
    rows = ref + list(ms)
    print("\n================= v29 LIVE COMPARISON TABLE =================")
    hdr = (f"{'arm':>5} {'n':>4} {'W':>4}{'BE':>5}{'L':>5} {'WR%':>7} "
           f"{'minW':>5} {'>=4R':>5} {'maxR':>7} {'net%':>8} {'PF':>6} "
           f"{'maxDD%':>7} {'strk':>5} {'ymin':>5} {'5as':>4}")
    print(hdr)
    def nz(v, d=0.0):
        return v if isinstance(v, (int, float)) else d
    for r in rows:
        pa = f"{r['passed']}/5" if r.get("passed") is not None else "-"
        ymin = r.get("ymin") if r.get("ymin") is not None else "-"
        mw = r.get("min_winner_R")
        print(f"{r['arm']:>5} {int(nz(r['n'])):4d} {int(nz(r['W'])):4d}"
              f"{int(nz(r['BE'])):5d}{int(nz(r['L'])):5d} "
              f"{nz(r['wr']):7.2f} {str(mw):>5} {int(nz(r['ge4R'])):5d} "
              f"{nz(r['maxR']):7.2f} "
              f"{nz(r['net_pct']):+8.2f} {nz(r['pf']):6.2f} "
              f"{nz(r['max_dd_pct']):7.2f} "
              f"{str(r.get('streak_be_resets')):>5} {str(ymin):>5} {pa:>4}")
    print("=============================================================")
    for r in rows:
        if r.get("yearly"):
            print(f"  {r['arm']:>5} yearly: {r['yearly']}")


def main():
    global BOX_GATE
    mode = sys.argv[1] if len(sys.argv) > 1 else "run"
    if "--boxgate" in sys.argv:
        BOX_GATE = True
        sys.argv = [a for a in sys.argv if a != "--boxgate"]
    if mode == "smoke":
        import strategy_v29_ict_turtle_soup as S
        out = []
        for arm in (sys.argv[2:] or ARMS):
            m, tr = drive(arm, "2021-01-01", "2021-07-01", save=False)
            show(m)
            keys = ("setup_drawn", f"v29_arm_{arm}_drawn", "setup_box_died",
                    "setup_mitigated", "setup_mitigated_v29",
                    "setup_missed_run", "await_order_retrace",
                    "await_soup_sweep", "soup_no_reclaim",
                    "await_seam_retrace", "fill_at_seam", f"fill_v29_{arm}",
                    "reject_risk_below_one_fee", "reject_wall_within_3r_v29",
                    "fill_cancel_target_within_3r", "fill_cancel_board_red",
                    "fill_cancel_premium", "tier3_fill_needs_proof",
                    "sacred_law_seam_ok", "fill")
            cnt = m.pop("_count", {})
            print("       funnel: " + "  ".join(
                f"{k}={cnt.get(k, 0)}" for k in keys if cnt.get(k, 0)),
                flush=True)
            out.append(m)
        table(out)
    elif mode == "run":
        arms = sys.argv[2:] or ARMS
        out = []
        for arm in arms:
            m, tr = drive(arm, "2021-01-01", "2026-10-31")
            show(m)
            out.append(m)
        with open(RESULTS / "lab_v29_arms.json", "w") as f:
            json.dump(out, f, indent=2, default=str)
        table(out)
        for arm in arms:
            if arm != "seam":
                convert(arm)
    elif mode == "score":
        out = []
        for arm in (sys.argv[2:] or ARMS):
            f = RESULTS / f"trades_v29_{arm}.csv"
            if not f.exists():
                print(f"missing {f}")
                continue
            tr = pd.read_csv(f)
            sj = RESULTS / f"summary_v29_{arm}.json"
            summ = json.load(open(sj)) if sj.exists() else {}
            m = metrics(arm, tr, summ)
            show(m)
            out.append(m)
        table(out)
    elif mode == "predict":
        for arm in (sys.argv[2:] or ["A", "B", "C", "D"]):
            predict(arm)
    elif mode == "convert":
        for arm in (sys.argv[2:] or ["A", "B", "C", "D"]):
            convert(arm)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
