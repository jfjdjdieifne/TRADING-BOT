#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lab_v28_live_5m.py — the v28 laboratory: 5m causal management + LIVE
structural quality filtering, swept against the five mandatory asserts.

WHY THIS LAB IS DIFFERENT FROM lab_v27_exact.py
------------------------------------------------
lab_v27_exact.py re-simulated the 297 v27 trades on the 5m tape and had to
discount every winner by BOOK_RATIO = 0.673 (the measured median of booked R
over max-5m-close R) because the re-simulation could not reproduce the old
engine's slow-frame management. The v28 brief is right that this is the wrong
tool for the v28 question: a discount factor calibrated on the OLD engine says
nothing about a NEW engine, and a static post-hoc filter applied to a frozen
trade list cannot show what happens when a rejected setup stops occupying the
engine's single position slot.

So this lab has two independent halves:

  offline  — measurement only, no engine. Bounded strictly by each trade's own
             lifetime (entry_time .. exit_time) so nothing can look ahead.
             It answers: how many trades really locked +3R on a 5m close while
             alive, and what each management rule would have done to them.
  live     — drives the REAL engine (strategy_v28_ict_5m_supreme.run_backtest)
             with the flags monkey-patched, so the trade set, the slot
             contention, the compounding and the fees are all genuine. One
             combo per process, ~6 minutes. This is the arbiter.

USAGE
-----
    python3 lab_v28_live_5m.py offline [trades_vXX.csv]
    python3 lab_v28_live_5m.py live COMBO [COMBO ...]
    python3 lab_v28_live_5m.py combos

LIVE COMBOS
-----------
    v27base    MANAGE_5M=off  CTX_MODE=or      (reproduces v26/v27)
    5mlock     MANAGE_5M=on   CTX_MODE=or      (claim 1 alone)
    gate       MANAGE_5M=off  CTX_MODE=v28q    (claim 2 alone)
    both       MANAGE_5M=on   CTX_MODE=v28q    (claims 1+2, the brief)
    shield5m   MANAGE_5M=on   MANAGE_5M_SHIELD=on CTX_MODE=or
               (claim 1b: a PERMANENT BE shield armed on 5m closes, for every
                trade including loss_streak == 0)

Nothing here invents a magic number: every threshold is either the sacred
MIN_R = 3.0 lock, or a feature threshold scanned on the v27 book and reported
with its own sample size in the offline half (`scan`).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
FEE = 0.001          # must match the engine
MIN_R = 3.0          # sacred: a winner is >= +3.00R NET of fees
YEARS = range(2021, 2026)


# ==================================================================== #
# OFFLINE HALF — measurement bounded by each trade's own life
# ==================================================================== #
def _tape():
    sys.path.insert(0, str(HERE))
    from engine.causal_primitives import (load_asset_ohlcv,
                                          resample_causal_tf)
    raw = load_asset_ohlcv(HERE / "data" / "BTCUSD_5m", include_stems=None)
    tf5 = resample_causal_tf(raw, "5min")
    return tf5


def _lines(entry_px: float, stop_px: float):
    """The engine's own fee-adjusted lines (strategy_v28 L1596 / L1430)."""
    risk = entry_px - stop_px
    lock = (entry_px * (1 + FEE) + MIN_R * risk) / (1 - FEE)
    be = entry_px * (1 + 2 * FEE)
    return risk, lock, be


def _R(entry_px: float, risk: float, px: float) -> float:
    """The engine's own net-R formula (gross - entry fee - exit fee) / risk."""
    return ((px - entry_px) - entry_px * FEE - px * FEE) / risk


def offline(trades_csv: str = "trades_v27.csv"):
    tf5 = _tape()
    idx = tf5.index
    a = pd.read_csv(RESULTS / trades_csv)
    a["yr"] = a.entry_time.str[:4].astype(int)
    print(f"\n=== OFFLINE: {trades_csv} · {len(a)} trades · "
          f"{len(tf5)} 5m bars ===")

    # ---- (1) how many trades REALLY locked +3R on a 5m close, alive ----
    # The window is entry_time..exit_time. An unbounded window is a lie:
    # measured with a 3000-bar (10.4 day) horizon, 259 of 297 trades see a
    # 5m close above the lock, but 184 of those happen days AFTER the trade
    # was already closed. That contaminated pass printed "189 lost winners /
    # WR ceiling 90.56%"; it is void and must never be reused.
    rows = []
    for _, t in a.iterrows():
        E = float(t.entry_price)
        SP = float(t.stop_price)
        if not np.isfinite(SP) or E - SP <= 0:
            continue
        risk, lock, be = _lines(E, SP)
        et = pd.Timestamp(t.entry_time)
        xt = pd.Timestamp(t.exit_time)
        i0 = idx.searchsorted(et, side="right")   # bars strictly after fill
        i1 = idx.searchsorted(xt, side="left")    # bounded by the exit
        w = tf5.iloc[i0:i1]
        c = w.Close.values
        l = w.Low.values
        o = w.Open.values
        lk = np.where(c >= lock)[0]
        rec = dict(entry_time=t.entry_time, cls=t["class"], R_v27=float(t.R),
                   exec_tf=t.exec_tf, n_bars=int(len(w)), locked=bool(len(lk)))
        if len(lk):
            k = int(lk[0])
            rec["lock_bar"] = k
            # the stop is armed by the CLOSE of bar k, so only bar k+1.. can
            # breach it. Including bar k exits on the locking bar itself
            # (its own low is below the lock by construction) and clips every
            # runner to +3.00R — measured, and wrong.
            br = np.where(l[k + 1:] <= lock)[0]
            if len(br):
                j = k + 1 + int(br[0])
                fill = lock if o[j] >= lock else o[j]
                rec["R_wick5"] = _R(E, risk, fill)
            bc = np.where(c[k + 1:] <= lock)[0]
            if len(bc):
                j = k + 1 + int(bc[0])
                rec["R_close5"] = _R(E, risk, c[j])
        rows.append(rec)
    d = pd.DataFrame(rows)
    print("\n--- (1) the +3R lock, bounded by each trade's own life ---")
    for cls in ("WIN", "BE", "LOSS"):
        s = d[d.cls == cls]
        print(f"    {cls:5s} n={len(s):4d}   closed a 5m bar >= lock_line "
              f"while ALIVE: {int(s.locked.sum()):4d}")
    lost = d[(d.cls != "WIN") & d.locked]
    print(f"    => lost winners = {len(lost)} of {int(d.locked.sum())} locked "
          f"({100 * len(lost) / max(1, int(d.locked.sum())):.1f}%)"
          f"   [the v28 brief claims 32.7%]")
    W = int((d.cls == "WIN").sum()) + len(lost)
    B = int((d.cls == "BE").sum()) - int((lost.cls == "BE").sum())
    L = int((d.cls == "LOSS").sum()) - int((lost.cls == "LOSS").sum())
    print(f"    => WR CEILING of the whole claim-1 fix: "
          f"{100 * W / (W + L):.2f}%  ({W}W/{B}BE/{L}L)"
          f"   [today {100 * (d.cls == 'WIN').sum() / ((d.cls == 'WIN').sum() + (d.cls == 'LOSS').sum()):.2f}%]")
    for _, r in lost.iterrows():
        print(f"       lost winner: {r.entry_time}  frame={r.exec_tf}  "
              f"locked at 5m bar #{int(r.lock_bar)} of {int(r.n_bars)} alive")

    # ---- (2) the three management rules, applied causally --------------
    print("\n--- (2) management rules on the 5m tape (offline estimate) ---")
    print(f"    {'rule':28s} {'n':>4} {'W':>4}{'BE':>5}{'L':>5} {'WR%':>7} "
          f"{'>=4R':>5} {'maxR':>7} {'totR':>8}")

    def rep(name, R):
        R = np.asarray(R, dtype=float)
        w = int((R >= MIN_R - 1e-9).sum())
        be = int(((R < MIN_R - 1e-9) & (R >= -0.05)).sum())
        lo = int((R < -0.05).sum())
        print(f"    {name:28s} {len(R):4d} {w:4d}{be:5d}{lo:5d} "
              f"{100 * w / (w + lo):7.2f} {int((R >= 4).sum()):5d} "
              f"{np.nanmax(R):7.2f} {np.nansum(R):8.2f}")
        return w, be, lo

    rep("v27 booked (exec frame)", d.R_v27)
    rw = np.where(d.R_wick5.notna(), d.R_wick5, d.R_v27)
    rep("5m lock + 5m WICK defence", rw)
    rc = np.where(d.R_close5.notna(), d.R_close5, d.R_v27)
    rep("5m lock + 5m CLOSE exit", rc)
    big = d[(d.cls == "WIN") & (d.R_v27 >= 6)]
    print("    what the wick defence does to the runners >= 6R:")
    for _, r in big.sort_values("R_v27", ascending=False).iterrows():
        new = r.R_wick5 if pd.notna(r.get("R_wick5")) else r.R_v27
        print(f"       {r.entry_time}  {r.R_v27:6.2f}R -> {new:6.2f}R")

    # ---- (3) the causal pre-entry gate scan ---------------------------
    print("\n--- (3) causal pre-entry gates (available at the entry tick) ---")
    print("    POST-HOC features are excluded by construction: disp_mid and")
    print("    disp_bos look spectacular (73.53% @108 / 62.50% @145) but they")
    print("    are set inside _manage at L1763/L1767 - AFTER the fill - and")
    print("    written to the trade row at exit (L1681/L1682). Filtering on")
    print("    them is the same lookahead trap as v24's crossed_purple_mid.")
    CAUSAL_BOOL = ["nar_raid_high_4h", "nar_in_demand_4h", "nar_in_demand_1h",
                   "nar_raid_low_1h", "nar_raid_high_1h",
                   "nar_stop_in_demand_4h", "nar_unicorn_4h",
                   "nar_unicorn_1h", "nar_unicorn_exec", "be_at_entry"]
    CAUSAL_NUM = [("nar_range_pos_4h", [0.0, -0.25, 0.25]),
                  ("nar_sky_r_4h", [6.0, 10.0, 15.0]),
                  ("nar_ifvg_r_4h", [0.05, 0.1]),
                  ("nar_ifvg_r_1h", [0.03, 0.05]),
                  ("nar_sky_r_1h", [0.0, -1.0])]

    def st(m):
        s = a[m]
        w = int((s["class"] == "WIN").sum())
        lo = int((s["class"] == "LOSS").sum())
        be = int((s["class"] == "BE").sum())
        yr = s.yr.value_counts().reindex(list(YEARS)).fillna(0)
        return dict(n=len(s), W=w, BE=be, L=lo,
                    wr=round(100 * w / (w + lo), 2) if w + lo else 0.0,
                    totR=round(float(s.R.sum()), 1),
                    ge4R=int((s.R >= 4).sum()), maxR=round(float(s.R.max()), 2),
                    ymin=int(yr.min()) if len(yr) else 0,
                    A5=bool(len(s) >= 150 and (len(yr) and yr.min() >= 12)),
                    A3=bool(int((s.R >= 4).sum()) >= 5 and s.R.max() >= 6.0))

    import itertools
    cands = {}
    for c in CAUSAL_BOOL:
        cands[f"{c}=1"] = a[c].astype(bool)
        cands[f"{c}=0"] = ~a[c].astype(bool)
    for c, ths in CAUSAL_NUM:
        for th in ths:
            cands[f"{c}>{th}"] = a[c] > th
            cands[f"{c}<={th}"] = a[c] <= th
    for c1, c2 in itertools.combinations(CAUSAL_BOOL, 2):
        for v1, v2 in itertools.product([True, False], repeat=2):
            m = (a[c1].astype(bool) == v1) & (a[c2].astype(bool) == v2)
            cands[f"{c1}={int(v1)}&{c2}={int(v2)}"] = m
    ok = []
    for k, m in cands.items():
        s = st(m)
        if s["A5"]:
            ok.append((k, s))
    ok.sort(key=lambda r: -r[1]["wr"])
    print(f"    gates scanned: {len(cands)}   passing ASSERT5: {len(ok)}")
    print(f"    {'gate':44s} {'n':>4} {'W':>4}{'BE':>5}{'L':>5} {'WR%':>7} "
          f"{'>=4R':>5} {'maxR':>7} {'totR':>8} ymin A3")
    for k, s in ok[:12]:
        print(f"    {k:44s} {s['n']:4d} {s['W']:4d}{s['BE']:5d}{s['L']:5d} "
              f"{s['wr']:7.2f} {s['ge4R']:5d} {s['maxR']:7.2f} "
              f"{s['totR']:8.1f} {s['ymin']:4d} {'Y' if s['A3'] else '.'}")
    best = ok[0] if ok else None
    if best:
        print(f"    => BEST causal A5-passing gate: {best[0]}  "
              f"WR {best[1]['wr']}% @ n={best[1]['n']}")
    print("    NOTE: these are post-hoc readings of a frozen list. Claim 2 says")
    print("    a LIVE gate can beat them, because rejecting a setup frees the")
    print("    engine's single slot and exposes the setups queued behind it.")
    print("    Only the `live` half can answer that - see below.")

    out = dict(trades_csv=trades_csv, n_trades=int(len(a)),
               locked_while_alive=int(d.locked.sum()),
               lost_winners=int(len(lost)),
               wr_ceiling_pct=round(100 * W / (W + L), 2),
               best_causal_gate=(best[0] if best else None),
               best_causal_gate_wr=(best[1]["wr"] if best else None),
               best_causal_gate_n=(best[1]["n"] if best else None))
    with open(RESULTS / "lab_v28_offline.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"\n    wrote results/lab_v28_offline.json")
    return out


# ==================================================================== #
# LIVE HALF — drive the real engine
# ==================================================================== #
COMBOS = {
    "v27base":  dict(MANAGE_5M=False, CTX_MODE="or"),
    "5mlock":   dict(MANAGE_5M=True,  MANAGE_5M_WICK=True,
                     MANAGE_5M_SHIELD=False, CTX_MODE="or"),
    "gate":     dict(MANAGE_5M=False, CTX_MODE="v28q"),
    "both":     dict(MANAGE_5M=True,  MANAGE_5M_WICK=True,
                     MANAGE_5M_SHIELD=False, CTX_MODE="v28q"),
    "shield5m": dict(MANAGE_5M=True,  MANAGE_5M_WICK=True,
                     MANAGE_5M_SHIELD=True, CTX_MODE="or"),
    "gate_raid": dict(MANAGE_5M=False, CTX_MODE="v28raid"),
    "gate_q":   dict(MANAGE_5M=False, CTX_MODE="v28q"),
}


def live(names):
    sys.path.insert(0, str(HERE))
    import strategy_v28_ict_5m_supreme as S
    res = {}
    for name in names:
        if name not in COMBOS:
            print(f"unknown combo {name}; see `combos`")
            continue
        for k, v in COMBOS[name].items():
            setattr(S, k, v)
        print(f"\n########## LIVE COMBO: {name}  {COMBOS[name]} ##########")
        run = S.run_backtest(S.DATA_DIR, S.FULL_START, S.FULL_END,
                             tag=name)
        tr = pd.DataFrame(run["trades"]) if isinstance(run, dict) else None
        if tr is None:                      # run_backtest may return a tuple
            tr = pd.DataFrame(run[0])
        tr.to_csv(RESULTS / f"trades_v28_live_{name}.csv", index=False)
        res[name] = score(name, tr)
    with open(RESULTS / "lab_v28_live.json", "w") as f:
        json.dump(res, f, indent=2, default=str)
    table(res)
    return res


def score(name, tr):
    tr = tr.copy()
    tr["yr"] = tr.entry_time.astype(str).str[:4].astype(int)
    W = int((tr["class"] == "WIN").sum())
    B = int((tr["class"] == "BE").sum())
    L = int((tr["class"] == "LOSS").sum())
    wr = 100 * W / (W + L) if W + L else 0.0
    wins = tr[tr["class"] == "WIN"]
    yr = tr.yr.value_counts().reindex(list(YEARS)).fillna(0).astype(int)
    ge4 = int((tr.R >= 4).sum())
    mx = float(tr.R.max()) if len(tr) else 0.0
    # streak, both readings (disclosed side by side, as always)
    cur = best = cons = 0
    for c in tr["class"]:
        if c == "LOSS":
            cur += 1
            best = max(best, cur)
            cons += 1
        elif c == "WIN":
            cur = 0
            cons = 0
        else:
            cur = 0
    A = dict(
        A1=(wr >= 60.0, f"WR >= 60% :: {wr:.2f}% ({W}W/{L}L)"),
        A2=((len(wins) == 0 or float(wins.R.min()) >= MIN_R - 1e-9),
            f"min_winner_R >= 3.00 :: "
            f"{float(wins.R.min()) if len(wins) else float('nan'):.2f}R"),
        A3=(ge4 >= 5 and mx >= 6.0, f"runners_4r_plus >= 5 AND max >= 6.0 :: "
                                    f">=4R:{ge4} max:{mx:.2f}R"),
        A4=(best <= 3, f"max_consecutive_losses <= 3 :: {best}"),
        A5=(len(tr) >= 150 and int(yr.min()) >= 12,
            f"total >= 150 AND yearly >= 12 :: total:{len(tr)} "
            f"yearly:{dict(yr)}"),
    )
    print(f"[{name}] n={len(tr)} {W}W/{B}BE/{L}L WR={wr:.2f}% "
          f"totR={tr.R.sum():.2f} maxR={mx:.2f} >=4R={ge4}")
    for k, (okv, det) in A.items():
        print(f"[{name}] ASSERT{k[-1]} {'PASSED' if okv else 'FAILED'} :: {det}")
    print(f"[{name}] streak: BE-resets={best} conservative={cons}")
    return dict(n=int(len(tr)), W=W, BE=B, L=L, wr=round(wr, 2),
                totR=round(float(tr.R.sum()), 2), maxR=round(mx, 2), ge4R=ge4,
                yearly={int(k): int(v) for k, v in yr.items()},
                streak_be_resets=best, streak_conservative=cons,
                asserts={k: dict(passed=bool(v[0]), observed=v[1])
                         for k, v in A.items()})


def table(res):
    if not res:
        return
    print("\n================ LIVE COMPARISON TABLE ================")
    hdr = f"{'combo':10s} {'n':>4} {'W':>4}{'BE':>5}{'L':>5} {'WR%':>7} {'totR':>8} {'>=4R':>5} {'maxR':>7}  asserts"
    print(hdr)
    for k, s in res.items():
        a = "".join("P" if s["asserts"][x]["passed"] else "F"
                    for x in ("A1", "A2", "A3", "A4", "A5"))
        print(f"{k:10s} {s['n']:4d} {s['W']:4d}{s['BE']:5d}{s['L']:5d} "
              f"{s['wr']:7.2f} {s['totR']:8.2f} {s['ge4R']:5d} "
              f"{s['maxR']:7.2f}  {a}")
    print("========================================================")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "offline"
    if mode == "offline":
        offline(sys.argv[2] if len(sys.argv) > 2 else "trades_v27.csv")
    elif mode == "live":
        live(sys.argv[2:] or ["5mlock", "gate", "both"])
    elif mode == "combos":
        for k, v in COMBOS.items():
            print(f"{k:10s} {v}")
    else:
        print(__doc__)
