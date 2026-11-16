#!/usr/bin/env python
"""Run the whole thing: adaptive engine + rigid ICT + random control, 6.8 years.

    .venv/bin/python ict_vision/scripts/run_backtest.py --out ict_vision/results
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ict_vision.backtest.baselines import (market_entry_ablation, random_control,
                                              rigid_ict, time_matched_control)
from ict_vision.backtest.metrics import bootstrap_ci, summarise, trades_frame, yearly
from ict_vision.brain.engine import ChartReader, Cfg
from ict_vision.core import clock as clk
from ict_vision.data.loader import load_all, minutes_of_day, session_ids

DATA = "smc_v4_multisleeve_package/data/NSXUSD_1m_histdata"



def _p_sync():
    """Push the research parameters into the QuantConnect port so the two
    implementations cannot silently drift apart.  The numbers live in one place
    (Cfg) and the QC file is rewritten from them on every run."""
    import re as _re
    from ict_vision.brain.engine import Cfg
    p = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "qc", "main.py"))
    if not os.path.exists(p):
        print("  (qc/main.py not found - skipped sync)")
        return
    c = Cfg()
    n = 0
    s = open(p).read()
    for pat, rep in {
        r"HALF_SPREAD = [0-9.]+":   f"HALF_SPREAD = {c.half_spread:g}",
        r"STOP_SLIP = [0-9.]+":     f"STOP_SLIP = {c.stop_slip:g}",
        r"BOOTSTRAP = [0-9]+":      f"BOOTSTRAP = {c.bootstrap_trades}",
        r"RISK_PCT = [0-9.]+":      f"RISK_PCT = {c.risk_pct}",
        r"KELLY_CAP = [0-9.]+":     f"KELLY_CAP = {c.kelly_cap}",
    }.items():
        s, k = _re.subn(pat, rep, s)
        n += k
    open(p, "w").write(s)
    print(f"  synced {n} parameters into ict_vision/qc/main.py")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=DATA)
    ap.add_argument("--out", default="ict_vision/results")
    ap.add_argument("--cache", default="/tmp/nsx_1m_et.pkl")
    ap.add_argument("--warmup", type=int, default=6000)
    ap.add_argument("--limit", type=int, default=0, help="debug: only run the first N bars")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    t_all = time.time()
    print("loading…", flush=True)
    b1 = load_all(a.data, minutes=1, cache=a.cache)
    b5 = load_all(a.data, minutes=5, cache=a.cache)
    print(f"  1m bars {b1.n:,}   5m bars {b5.n:,}   {b5.idx[0]} -> {b5.idx[-1]}", flush=True)

    # ---------------------------------------------------------------- engine
    print("preparing perception layer…", flush=True)
    t0 = time.time()
    cfg = Cfg(warmup_bars=a.warmup)
    r = ChartReader(b5, b1, cfg)
    print(f"  prep {time.time()-t0:.1f}s", flush=True)
    t0 = time.time()
    end = min(b5.n, a.limit) if a.limit else b5.n
    trades = r.run(t_end=end)
    print(f"  walk  {time.time()-t0:.1f}s   setups={r.n_cand}  orders={r.n_taken}  trades={len(trades)}",
          flush=True)

    df = trades_frame(trades)
    df["time"] = [str(b5.idx[t.t_signal])[:19] for t in trades]
    df.to_csv(os.path.join(a.out, "trades.csv"), index=False)

    # daily equity for Sharpe / drawdown
    sess = session_ids(b5.idx)
    eq = pd.Series(r.equity_curve, index=b5.idx[a.warmup:a.warmup + len(r.equity_curve)])
    daily = eq.groupby(eq.index.normalize()).last().dropna()
    dret = daily.pct_change().dropna()
    years = (b5.idx[-1] - b5.idx[0]).days / 365.25
    sharpe = float(dret.mean() / dret.std() * np.sqrt(252)) if dret.std() > 0 else float("nan")
    peak = daily.cummax()
    maxdd = float((1 - daily / peak).max())
    cagr = float((daily.iloc[-1] / daily.iloc[0]) ** (1 / max(years, 1e-9)) - 1)

    live = [t for t in trades if not t.bootstrap]
    Rlive = np.array([t.r_mult for t in live], float)
    Rall = np.array([t.r_mult for t in trades], float)

    print("\n================ ADAPTIVE ENGINE ================")
    print(f"  trades {len(trades)}  (bootstrap exploration {len(trades)-len(live)}, live {len(live)})")
    print(f"  ALL   : win {np.mean(Rall>0)*100:.1f}%  meanR {Rall.mean():+.3f}  "
          f"95%CI [{bootstrap_ci(Rall)[0]:+.3f},{bootstrap_ci(Rall)[1]:+.3f}]  t {Rall.mean()/(Rall.std()/np.sqrt(len(Rall))):+.2f}")
    if len(live) > 5:
        print(f"  LIVE  : win {np.mean(Rlive>0)*100:.1f}%  meanR {Rlive.mean():+.3f}  "
              f"95%CI [{bootstrap_ci(Rlive)[0]:+.3f},{bootstrap_ci(Rlive)[1]:+.3f}]  t {Rlive.mean()/(Rlive.std()/np.sqrt(len(Rlive))):+.2f}")
    print(f"  equity {daily.iloc[0]:,.0f} -> {daily.iloc[-1]:,.0f}   CAGR {cagr*100:+.2f}%   "
          f"Sharpe {sharpe:.2f}   MaxDD {maxdd*100:.1f}%")
    print("  exits:", pd.Series([t.exit_kind for t in trades]).value_counts().to_dict())
    print("\n  by year:")
    print(yearly(trades, b5.idx).to_string())

    # ---------------------------------------------------------- learned stuff
    sn = r.ret_model.snapshot()
    _p_sync()
    print("\n================ WHAT IT LEARNED ================")
    print(f"  OTE entry depth : {sn['best_depth']*100:.1f}%   (ICT prior 62.0-79.0%, mean 70.5%)")
    print(f"  learned HDI     : {sn['hdi'][0]*100:.1f}% - {sn['hdi'][1]*100:.1f}%   "
          f"from {sn['n_legs_effective']:.0f} resolved legs")
    print(f"  learned extension past the leg extreme: {sn['learned_extension']:.2f} x leg")
    prof = r.clock.profile()
    wins = r.clock.discover_windows()
    print("\n  discovered high-delivery windows (ET):")
    for w in wins[:8]:
        print(f"    {w['start_min']//60:02d}:{w['start_min']%60:02d}-"
              f"{w['end_min']//60:02d}:{w['end_min']%60:02d}   score {w['score']:.2f}x day average")
    print("\n  score of ICT's canonical windows on this instrument:")
    for row in clk.score_ict_windows(r.clock)[:8]:
        print(f"    {row['window']:<20} {row['score']:.2f}x")
    eqp = float(np.nanmean(r.dr['pd'][a.warmup:]))
    print(f"\n  premium/discount equilibrium: time-at-price centroid sits at "
          f"pd={eqp:+.3f} (0 = the model's equilibrium, 0.5 = the arithmetic midpoint would be "
          f"{'above' if eqp>0 else 'below'})")

    # ---------------------------------------------------------------- controls
    print("\n================ CONTROLS ================")
    tod = minutes_of_day(b5.idx)
    rb = rigid_ict(b5, b1, r.m1_a, r.m1_b, tod, start=a.warmup)
    rb = rb[np.isfinite(rb)]
    if len(rb):
        print(f"  RIGID ICT : n={len(rb)}  win {np.mean(rb>0)*100:.1f}%  meanR {rb.mean():+.3f}  "
              f"t {rb.mean()/(rb.std()/np.sqrt(len(rb))):+.2f}")
    else:
        print("  RIGID ICT : no trades")

    rc = random_control(b5, r.m1_a, r.m1_b, max(len(trades) * 4, 500), start=a.warmup)
    if len(rc):
        print(f"  RANDOM x4 : n={len(rc)}  win {np.mean(rc>0)*100:.1f}%  meanR {rc.mean():+.3f}  "
              f"t {rc.mean()/(rc.std()/np.sqrt(len(rc))):+.2f}")
    mc = time_matched_control(b5, trades)
    if len(mc):
        print(f"  COIN FLIP : n={len(mc)}  win {np.mean(mc>0)*100:.1f}%  meanR {mc.mean():+.3f}  "
              f"t {mc.mean()/(mc.std()/np.sqrt(len(mc))):+.2f}   "
              f"(engine's level, random side)")
    ma = market_entry_ablation(b5, trades)
    if len(ma):
        print(f"  MARKET IN : n={len(ma)}  win {np.mean(ma>0)*100:.1f}%  meanR {ma.mean():+.3f}  "
              f"t {ma.mean()/(ma.std()/np.sqrt(len(ma))):+.2f}   "
              f"(same bars, same side, no OTE limit)")

    # ------------------------------------------------------------------ report
    rep = {
        "sample": {"start": str(b5.idx[0]), "end": str(b5.idx[-1]), "years": years,
                   "bars_1m": int(b1.n), "bars_5m": int(b5.n)},
        "engine": {
            "n_setups": int(r.n_cand), "n_orders": int(r.n_taken), "n_trades": len(trades),
            "n_live": len(live), "mean_R_all": float(Rall.mean()) if len(Rall) else None,
            "mean_R_live": float(Rlive.mean()) if len(Rlive) else None,
            "win_rate_all": float(np.mean(Rall > 0)) if len(Rall) else None,
            "ci95_all": list(bootstrap_ci(Rall)) if len(Rall) else None,
            "exits": pd.Series([t.exit_kind for t in trades]).value_counts().to_dict(),
            "cagr": cagr, "sharpe": sharpe, "max_dd": maxdd,
            "equity_start": float(daily.iloc[0]), "equity_end": float(daily.iloc[-1]),
        },
        "learned": {
            "ote_depth": sn["best_depth"], "ote_hdi": list(sn["hdi"]),
            "ote_prior_center": sn["prior_center"], "legs_seen": sn["n_legs_effective"],
            "learned_extension": sn["learned_extension"],
            "discovered_windows": wins,
            "ict_window_scores": clk.score_ict_windows(r.clock),
            "pd_equilibrium_mean": eqp,
            "sweep_overshoot_p70_sig": float(r.sweep_overshoot.quantile(0.70)),
            "comeback_curve": {str(g): r.comeback.p(g) for g in r.comeback.grid},
            "hazard_curve": [float(r.hazard.p(b)) for b in range(0, 288, 12)],
        },
        "controls": {
            "rigid_ict": {"n": int(len(rb)), "mean_R": float(rb.mean()) if len(rb) else None,
                          "win_rate": float(np.mean(rb > 0)) if len(rb) else None},
            "random": {"n": int(len(rc)), "mean_R": float(rc.mean()) if len(rc) else None,
                       "win_rate": float(np.mean(rc > 0)) if len(rc) else None},
            "coin_flip_same_bars": {"n": int(len(mc)), "mean_R": float(mc.mean()) if len(mc) else None,
                                    "win_rate": float(np.mean(mc > 0)) if len(mc) else None},
            "market_entry_ablation": {"n": int(len(ma)), "mean_R": float(ma.mean()) if len(ma) else None,
                                      "win_rate": float(np.mean(ma > 0)) if len(ma) else None},
        },
        "evidence_table": {k: {"edge": v["edge"].round(3).tolist()} for k, v in r.evid.table().items()},
    }
    with open(os.path.join(a.out, "report.json"), "w") as f:
        json.dump(rep, f, indent=2, default=str)
    pd.DataFrame(r.setup_log).to_csv(os.path.join(a.out, "setups.csv"), index=False)
    pd.DataFrame({"day": daily.index, "equity": daily.values}).to_csv(
        os.path.join(a.out, "equity.csv"), index=False)

    print(f"\nwrote {a.out}/report.json, trades.csv, setups.csv, equity.csv")
    print(f"total {time.time()-t_all:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
