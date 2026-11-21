#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lab_v31_compounding_brain.py — the live laboratory for the v31
COMPOUNDING BRAIN: four structural arms, each measured ALONE and IN
COMBINATION by running the REAL engine
(`strategy_v31_ict_compounding.run_backtest`) and scoring it with the
engine's own `summarize()`.

The prize, measured on the shipped v30 book (_m31a.py):
  * 33/44 winners (75%) were killed by the +3.00R floor and booked
    EXACTLY 3.00R out of a median 4.21R close extension (max 11.64R);
  * 55 trades booked BE/LOSS had already closed at >= +1.5R (35 at
    >= +2.0R, 26 at >= +2.5R) and cost totR -23.79;
  * cadence 0.64 wins/month, 29% profitable months, 0.79%/month.

ARMS
  1 STRUCT_TRAIL / STRUCT_TRAIL_MIN_R / _SRC / _NEEDS_DISP  (+ SWIN class)
  2 LOCK_MODE floor|htf|trail · LOCK_ARM_R · HARVEST_PCT
  3 IMPULSE_PURPLE / IMPULSE_MAX_BARS
  4 VIGILANCE_SCOPE none|shield  +  SHIELD_RULE_V30 MID|BOS / A0.5

USAGE
    python3 lab_v31_compounding_brain.py combos
    python3 lab_v31_compounding_brain.py smoke [COMBO ...]   # ~40 s/arm
    python3 lab_v31_compounding_brain.py run   [COMBO ...]   # ~7 min/arm
    python3 lab_v31_compounding_brain.py diag  COMBO         # vs v30/v27
    python3 lab_v31_compounding_brain.py score               # re-score files

Every full run writes results/trades_v31_<combo>.csv +
summary_v31_<combo>.json and appends its row to the sweep CSV
(V31_SWEEP env var lets parallel batches keep separate files).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
sys.path.insert(0, str(HERE))

YEARS = [str(y) for y in range(2021, 2027)]
MIN_R = 3.0
FULL = ("2021-01-01", "2026-10-31")
SMOKE = ("2021-01-01", "2021-07-01")
SWEEP_CSV = Path(os.environ.get("V31_SWEEP",
                                str(RESULTS / "lab_v31_sweep.csv")))

# --------------------------------------------------------------------- #
# BASE = the shipped v30 champion (VIGILANCE_SCOPE="shield+be"), so every
# v31 arm is measured as a DELTA against a book we already know.
# --------------------------------------------------------------------- #
BASE = dict(
    ENTRY_ARM="seam", FILL_MODE="blind", MANAGE_5M=False,
    ENTRY_BRAIN="sniper", BE_STREAK_MODE="reset",
    VIGILANCE_SCOPE="shield+be", SHIELD_RULE_V30="MID+BOS",
    RISK_FLOOR_PCT=0.10, RISK_FLOOR_STAGE="both", SIZING="allcash",
    DOLLAR_R_PCT=0.3267, SLIPPAGE_BPS=0.0,
    # ---- v31 arms, all OFF in the base ----
    STRUCT_TRAIL=False, STRUCT_TRAIL_MIN_R=1.0, STRUCT_TRAIL_SRC="exec",
    STRUCT_TRAIL_NEEDS_DISP=False, SWIN_MIN_R=0.05,
    SWIN_CLEARS_VIGIL=False,
    LOCK_ARM_R=3.0, LOCK_MODE="floor", HARVEST_PCT=0.0,
    IMPULSE_PURPLE=False, IMPULSE_MAX_BARS=240,
)

COMBOS = {
    "base":       {},                      # = the shipped v30 champion
    "v27base":    dict(VIGILANCE_SCOPE="none"),   # = v27/v29 seam book
    # ---- ARM 1: structural profit trail (kill the death zone) -------
    "A1_t05":     dict(STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=0.5),
    "A1_t10":     dict(STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=1.0),
    "A1_t15":     dict(STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=1.5),
    "A1_t20":     dict(STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=2.0),
    "A1_t10_htf": dict(STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=1.0,
                       STRUCT_TRAIL_SRC="htf"),
    "A1_t10_both": dict(STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=1.0,
                        STRUCT_TRAIL_SRC="both"),
    "A1_t10_disp": dict(STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=1.0,
                        STRUCT_TRAIL_NEEDS_DISP=True),
    # ---- ARM 2: anti-choke runner + split weekly harvester ----------
    "A2_trail":   dict(LOCK_MODE="trail"),
    "A2_htf":     dict(LOCK_MODE="htf"),
    "A2_arm4":    dict(LOCK_ARM_R=4.0),
    "A2_arm4_tr": dict(LOCK_ARM_R=4.0, LOCK_MODE="trail"),
    "A2_h50_fl":  dict(HARVEST_PCT=0.5),
    "A2_h50_htf": dict(HARVEST_PCT=0.5, LOCK_MODE="htf"),
    "A2_h50_tr":  dict(HARVEST_PCT=0.5, LOCK_MODE="trail"),
    # ---- ARM 2, honest reading: the floor is a LIVE STOP ------------
    "A2_stop":    dict(LOCK_MODE="stop"),
    "A2_arm4_st": dict(LOCK_ARM_R=4.0, LOCK_MODE="stop"),
    "A2_h50_st":  dict(HARVEST_PCT=0.5, LOCK_MODE="stop"),
    "C_12s":      dict(STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=1.0,
                       LOCK_MODE="stop"),
    "C_12s_t20":  dict(STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=2.0,
                       LOCK_MODE="stop"),
    "C_12sh":     dict(STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=1.0,
                       HARVEST_PCT=0.5, LOCK_MODE="stop"),
    "C_123s":     dict(STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=1.0,
                       LOCK_MODE="stop", IMPULSE_PURPLE=True),
    "C_124s":     dict(STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=1.0,
                       LOCK_MODE="stop", VIGILANCE_SCOPE="none",
                       SHIELD_RULE_V30="MID|BOS"),
    # ---- refinements of the measured leader C_124 -------------------
    # (structural trail + unchoked runner + no BE-at-entry + MID|BOS)
    "C_124_h":    dict(STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=1.0,
                       LOCK_MODE="trail", HARVEST_PCT=0.5,
                       VIGILANCE_SCOPE="none", SHIELD_RULE_V30="MID|BOS"),
    "C_124_imp":  dict(STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=1.0,
                       LOCK_MODE="trail", IMPULSE_PURPLE=True,
                       VIGILANCE_SCOPE="none", SHIELD_RULE_V30="MID|BOS"),
    "C_124_t20":  dict(STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=2.0,
                       LOCK_MODE="trail",
                       VIGILANCE_SCOPE="none", SHIELD_RULE_V30="MID|BOS"),
    "C_124_t05":  dict(STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=0.5,
                       LOCK_MODE="trail",
                       VIGILANCE_SCOPE="none", SHIELD_RULE_V30="MID|BOS"),
    "C_124_htf":  dict(STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=1.0,
                       LOCK_MODE="htf",
                       VIGILANCE_SCOPE="none", SHIELD_RULE_V30="MID|BOS"),
    "C_124_vig":  dict(STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=1.0,
                       LOCK_MODE="trail", VIGILANCE_SCOPE="shield+be",
                       SHIELD_RULE_V30="MID|BOS"),
    # ---- C_124 family with the floor defended as a live stop ---------
    "C_124_st":     dict(STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=1.0,
                         LOCK_MODE="stop",
                         VIGILANCE_SCOPE="none", SHIELD_RULE_V30="MID|BOS"),
    "C_124_htf_st": dict(STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=1.0,
                         LOCK_MODE="stop", LOCK_FLOOR_HTF=True,
                         VIGILANCE_SCOPE="none", SHIELD_RULE_V30="MID|BOS"),
    "C_124_t20_st": dict(STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=2.0,
                         LOCK_MODE="stop",
                         VIGILANCE_SCOPE="none", SHIELD_RULE_V30="MID|BOS"),
    "C_124_st_imp": dict(STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=1.0,
                         LOCK_MODE="stop", IMPULSE_PURPLE=True,
                         VIGILANCE_SCOPE="none", SHIELD_RULE_V30="MID|BOS"),
    "C_124_st_h":   dict(STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=1.0,
                         LOCK_MODE="stop", HARVEST_PCT=0.5,
                         VIGILANCE_SCOPE="none", SHIELD_RULE_V30="MID|BOS"),
    # ---- final refinements of the measured leader (close-based floor)
    "C_124_t15":  dict(STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=1.5,
                       LOCK_MODE="trail",
                       VIGILANCE_SCOPE="none", SHIELD_RULE_V30="MID|BOS"),
    "C_124_a4":   dict(STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=1.0,
                       LOCK_MODE="trail", LOCK_ARM_R=4.0,
                       VIGILANCE_SCOPE="none", SHIELD_RULE_V30="MID|BOS"),
    "C_124_t20a4": dict(STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=2.0,
                        LOCK_MODE="trail", LOCK_ARM_R=4.0,
                        VIGILANCE_SCOPE="none", SHIELD_RULE_V30="MID|BOS"),
    # ---- execution-cost stress on the SHIPPED config (as in v30) -----
    "SHIP_sl5":   dict(STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=1.0,
                       LOCK_MODE="trail", VIGILANCE_SCOPE="none",
                       SHIELD_RULE_V30="MID|BOS", SLIPPAGE_BPS=5.0),
    "SHIP_sl10":  dict(STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=1.0,
                       LOCK_MODE="trail", VIGILANCE_SCOPE="none",
                       SHIELD_RULE_V30="MID|BOS", SLIPPAGE_BPS=10.0),
    # ---- ARM 3: dynamic impulse-leg purple box ----------------------
    "A3_imp":     dict(IMPULSE_PURPLE=True),
    "A3_imp120":  dict(IMPULSE_PURPLE=True, IMPULSE_MAX_BARS=120),
    "A3_imp480":  dict(IMPULSE_PURPLE=True, IMPULSE_MAX_BARS=480),
    # ---- ARM 4: unthrottled entry + smart vigilance -----------------
    "A4_nobe_or":  dict(VIGILANCE_SCOPE="none", SHIELD_RULE_V30="MID|BOS"),
    "A4_nobe_a05": dict(VIGILANCE_SCOPE="none", SHIELD_RULE_V30="A0.5"),
    "A4_shield_or": dict(VIGILANCE_SCOPE="shield",
                        SHIELD_RULE_V30="MID|BOS"),
    # ---- combinations ------------------------------------------------
    "C_12":       dict(STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=1.0,
                       LOCK_MODE="trail"),
    "C_12h":      dict(STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=1.0,
                       HARVEST_PCT=0.5, LOCK_MODE="trail"),
    "C_12h4":     dict(STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=1.0,
                       HARVEST_PCT=0.5, LOCK_ARM_R=4.0,
                       LOCK_MODE="trail"),
    "C_124":      dict(STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=1.0,
                       LOCK_MODE="trail", VIGILANCE_SCOPE="none",
                       SHIELD_RULE_V30="MID|BOS"),
    "C_123":      dict(STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=1.0,
                       LOCK_MODE="trail", IMPULSE_PURPLE=True),
    "C_all":      dict(STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=1.0,
                       HARVEST_PCT=0.5, LOCK_MODE="trail",
                       IMPULSE_PURPLE=True, VIGILANCE_SCOPE="none",
                       SHIELD_RULE_V30="MID|BOS"),
}


# --------------------------------------------------------------------- #
def drive(combo, window=FULL, save=True):
    import strategy_v31_ict_compounding as S
    cfg = dict(BASE)
    cfg.update(COMBOS.get(combo, {}))
    for k, v in cfg.items():
        setattr(S, k, v)
    print(f"\n########## LIVE ENGINE · combo={combo} · "
          f"{window[0]}..{window[1]} ##########", flush=True)
    print("    config: " + "  ".join(
        f"{k}={v}" for k, v in cfg.items()
        if k not in ("ENTRY_ARM", "FILL_MODE", "MANAGE_5M", "SWIN_MIN_R",
                     "DOLLAR_R_PCT", "SLIPPAGE_BPS", "RISK_FLOOR_PCT",
                     "RISK_FLOOR_STAGE", "SIZING", "ENTRY_BRAIN")
        and v != BASE.get(k)) or "    config: = BASE", flush=True)
    run = S.run_backtest(S.DATA_DIR, window[0], window[1], tag=f"v31{combo}")
    tr = pd.DataFrame(run["trades"])
    try:
        summ = S.summarize(run)
    except AssertionError as e:
        print(f"    !! summarize() raised: {e}", flush=True)
        summ = {"_l1_violation": str(e)}
    if save and window == FULL:
        tr.to_csv(RESULTS / f"trades_v31_{combo}.csv", index=False)
        with open(RESULTS / f"summary_v31_{combo}.json", "w") as f:
            json.dump(summ, f, indent=2, default=str)
    m = metrics(combo, tr, summ, run["count"], cfg)
    show(m)
    append_sweep(m, window)
    return m, tr


def metrics(combo, tr, summ, count, cfg):
    n = len(tr)

    def cls(k):
        return int((tr["class"] == k).sum()) if n else 0
    W, SW, B, L = cls("WIN"), cls("SWIN"), cls("BE"), cls("LOSS")
    wr = 100 * W / (W + L) if W + L else 0.0
    wr_i = 100 * (W + SW) / (W + SW + L) if W + SW + L else 0.0
    wins = tr[tr["class"] == "WIN"] if n else tr
    sw = tr[tr["class"] == "SWIN"] if n else tr
    yr = (tr.entry_time.astype(str).str[:4].value_counts()
          .reindex(YEARS).fillna(0).astype(int).to_dict()) if n else \
        {y: 0 for y in YEARS}
    cur = best = cons = cons_best = 0
    for c in (tr["class"] if n else []):
        if c == "LOSS":
            cur += 1; cons += 1
            best = max(best, cur); cons_best = max(cons_best, cons)
        elif c in ("WIN", "SWIN"):
            cur = cons = 0
        else:
            cur = 0

    def fnum(k, dv=None):
        v = summ.get(k)
        return float(v) if isinstance(v, (int, float)) else dv

    m = dict(
        combo=combo, n=n, W=W, SWIN=SW, BE=B, L=L,
        wr=round(wr, 2), wr_incl=round(wr_i, 2),
        min_win_R=round(float(wins.R.min()), 2) if len(wins) else None,
        min_swin_R=round(float(sw.R.min()), 2) if len(sw) else None,
        max_swin_R=round(float(sw.R.max()), 2) if len(sw) else None,
        min_target_R=fnum("min_entry_target_R"),
        ge4R=int((tr.R >= 4).sum()) if n else 0,
        ge10R=int((tr.R >= 10).sum()) if n else 0,
        maxR=round(float(tr.R.max()), 2) if n else 0.0,
        totR=round(float(tr.R.sum()), 2) if n else 0.0,
        streak=best, streak_cons=cons_best, yearly=yr,
        ymin=min(yr[y] for y in YEARS[:5]),
        net_pct=round(fnum("net_pct", 0.0), 2),
        end_eq=round(fnum("end_equity", 200.0), 2),
        pf=round(fnum("profit_factor", 0.0), 3),
        maxDD=round(fnum("max_drawdown_pct", 0.0), 2),
        fees=round(fnum("fees", 0.0), 2),
        prof_months=fnum("profitable_months_pct"),
        comp_month=fnum("compounded_monthly_pct"),
        med_month=fnum("monthly_net_pct_med"),
        wins_mo=fnum("wins_per_month"),
        trades_mo=fnum("trades_per_month"),
        struct_trail=int((count or {}).get("v31_struct_trail", 0)),
        harvests=int((count or {}).get("v31_harvest_split", 0)),
        impulse=int((count or {}).get("v31_impulse_anchored", 0)),
        sacred_impulse=int((count or {}).get("sacred_law_impulse_ok", 0)),
        floor_htf=int((count or {}).get("v31_floor_htf_close", 0)),
        be_at_entry=int((count or {}).get("tier3_be_armed_at_entry", 0)),
        exits=json.dumps(summ.get("exit_reasons", {})),
        cfg=json.dumps(cfg),
    )
    m["A1"] = bool(m["wr_incl"] >= 60.0)
    m["A2"] = bool(m["min_win_R"] is None or m["min_win_R"] >= MIN_R - 1e-9)
    m["A2g"] = bool(m["min_target_R"] is None
                    or m["min_target_R"] >= MIN_R - 1e-9)
    m["A3"] = bool(m["ge4R"] >= 5 and m["maxR"] >= 6.0)
    m["A4"] = bool(m["streak"] <= 3)
    m["A5"] = bool(m["n"] >= 150 and m["ymin"] >= 12)
    m["passed"] = sum(m[k] for k in ("A1", "A2", "A3", "A4", "A5"))
    return m


def show(m):
    print(f"[{m['combo']:>12}] n={m['n']:4d}  {m['W']:3d}W/{m['SWIN']:3d}SW/"
          f"{m['BE']:3d}BE/{m['L']:3d}L  WR={m['wr']:6.2f}% "
          f"(incl {m['wr_incl']:6.2f}%)  minWin={m['min_win_R']}  "
          f"SWIN[{m['min_swin_R']}..{m['max_swin_R']}]  "
          f">=4R={m['ge4R']:3d}  maxR={m['maxR']:6.2f}  "
          f"totR={m['totR']:8.2f}", flush=True)
    print(f"               net={m['net_pct']:+7.2f}% (${m['end_eq']})  "
          f"PF={m['pf']}  maxDD={m['maxDD']}%  fees=${m['fees']}  "
          f"streak={m['streak']}/{m['streak_cons']}  "
          f"yearly={m['yearly']}", flush=True)
    print(f"               CADENCE: profitable months={m['prof_months']}%  "
          f"compounded={m['comp_month']}%/mo  median month="
          f"{m['med_month']}%  wins/mo={m['wins_mo']}  "
          f"trades/mo={m['trades_mo']}", flush=True)
    print(f"               MECH: struct_trail={m['struct_trail']} "
          f"harvests={m['harvests']} impulse={m['impulse']} "
          f"sacred_impulse={m['sacred_impulse']} floor_htf={m['floor_htf']} "
          f"be_at_entry={m['be_at_entry']} minTargetR={m['min_target_R']}",
          flush=True)
    a = "".join("P" if m[k] else "F"
                for k in ("A1", "A2", "A3", "A4", "A5"))
    print(f"               asserts A1..A5 = {a} -> {m['passed']}/5 "
          f"(A2 entry-gate {'P' if m['A2g'] else 'F'})  "
          f"exits={m['exits']}", flush=True)


def append_sweep(m, window):
    if window != FULL:
        return
    row = dict(m)
    df = pd.DataFrame([row])
    if SWEEP_CSV.exists():
        old = pd.read_csv(SWEEP_CSV)
        df = pd.concat([old[old.combo != m["combo"]], df], ignore_index=True)
    df.to_csv(SWEEP_CSV, index=False)


def diag(combo):
    f = RESULTS / f"trades_v31_{combo}.csv"
    if not f.exists():
        print(f"missing {f}")
        return
    b = pd.read_csv(f)
    print(f"\n=== DIAG {combo}: n={len(b)} ===")
    for ref, name in (("trades_v30_M1v_shbe_rst.csv", "v30 shipped"),
                      ("trades_v27.csv", "v27 base")):
        p = RESULTS / ref
        if not p.exists():
            continue
        a = pd.read_csv(p)
        m = a.merge(b, on="entry_time", suffixes=("_a", "_b"))
        print(f"  vs {name}: matched {len(m)} of {len(a)}")
        if len(m):
            print(pd.crosstab(m.class_a, m.class_b).to_string())
            print(f"    totR {m.R_a.sum():+.2f} -> {m.R_b.sum():+.2f} | "
                  f"net$ {m.net_pnl_a.sum():+.2f} -> "
                  f"{m.net_pnl_b.sum():+.2f}")
    if "mfe_close_R" in b:
        for cls in ("SWIN", "BE", "LOSS", "WIN"):
            s = b[b["class"] == cls]
            if not len(s):
                continue
            print(f"  {cls:5s} n={len(s):3d} bookedR med={s.R.median():6.2f} "
                  f"totR={s.R.sum():8.2f} | mfe_R med={s.mfe_R.median():5.2f} "
                  f"max={s.mfe_R.max():6.2f} | mfe_close med="
                  f"{s.mfe_close_R.median():5.2f} max="
                  f"{s.mfe_close_R.max():6.2f}")
        lf = b[b.exit_reason.astype(str).str.startswith("LOCK_FLOOR")]
        if len(lf):
            print(f"  floor kills n={len(lf)} bookedR med={lf.R.median():.2f} "
                  f"mfe_close med={lf.mfe_close_R.median():.2f} "
                  f"max={lf.mfe_close_R.max():.2f}")


def table(ms):
    ref = []
    for tag, fn in (("v25", "summary_v25.json"), ("v27", "summary_v27.json"),
                    ("v30", "summary_v30.json")):
        p = RESULTS / fn
        if p.exists():
            j = json.load(open(p))
            ref.append(dict(combo=tag, n=j.get("trades"), W=j.get("wins"),
                            SWIN=j.get("struct_wins", 0),
                            BE=j.get("breakevens"),
                            L=(j.get("trades", 0) - j.get("wins", 0)
                               - j.get("breakevens", 0)
                               - j.get("struct_wins", 0)),
                            wr=j.get("win_rate_pct"),
                            wr_incl=j.get("win_rate_incl_swin_pct"),
                            min_win_R=j.get("min_winner_R"),
                            ge4R=j.get("runners_4r_plus"),
                            maxR=j.get("max_winner_R"),
                            totR=j.get("totR"),
                            net_pct=j.get("net_pct"),
                            pf=j.get("profit_factor"),
                            maxDD=j.get("max_drawdown_pct"),
                            streak=j.get("max_consecutive_losses"),
                            ymin=None, passed=None,
                            prof_months=j.get("profitable_months_pct"),
                            comp_month=j.get("compounded_monthly_pct"),
                            wins_mo=j.get("wins_per_month")))
    rows = ref + list(ms)

    def nz(v, d=0.0):
        return v if isinstance(v, (int, float)) else d
    print("\n================= v31 LIVE COMPARISON TABLE =================")
    hdr = (f"{'combo':>12} {'n':>4} {'W':>4}{'SW':>4}{'BE':>5}{'L':>5} "
           f"{'WR%':>6} {'WRi%':>6} {'minW':>5} {'>=4R':>5} {'maxR':>6} "
           f"{'totR':>8} {'net%':>8} {'PF':>5} {'maxDD%':>7} {'mo+%':>5} "
           f"{'c%/mo':>6} {'w/mo':>5} {'strk':>5} {'5as':>4}")
    print(hdr)
    for r in rows:
        pa = f"{r['passed']}/5" if r.get("passed") is not None else "-"
        print(f"{r['combo']:>12} {int(nz(r['n'])):4d} {int(nz(r['W'])):4d}"
              f"{int(nz(r.get('SWIN'))):4d}{int(nz(r['BE'])):5d}"
              f"{int(nz(r['L'])):5d} {nz(r['wr']):6.2f} "
              f"{nz(r.get('wr_incl')):6.2f} {str(r.get('min_win_R')):>5} "
              f"{int(nz(r['ge4R'])):5d} {nz(r['maxR']):6.2f} "
              f"{nz(r.get('totR')):8.2f} {nz(r['net_pct']):+8.2f} "
              f"{nz(r['pf']):5.2f} {nz(r['maxDD']):7.2f} "
              f"{nz(r.get('prof_months')):5.1f} "
              f"{nz(r.get('comp_month')):6.2f} {nz(r.get('wins_mo')):5.2f} "
              f"{str(nz(r.get('streak'), 0)):>5} {pa:>4}")
    print("=============================================================")
    for r in rows:
        if r.get("yearly"):
            print(f"  {r['combo']:>12} yearly: {r['yearly']}")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "run"
    args = sys.argv[2:]
    if mode == "combos":
        for k, v in COMBOS.items():
            print(f"{k:14s} {v}")
        return
    if mode == "smoke":
        out = [drive(c, SMOKE, save=False)[0] for c in (args or ["base"])]
        table(out)
    elif mode == "run":
        out = [drive(c, FULL)[0] for c in (args or ["base"])]
        table(out)
    elif mode == "diag":
        for c in (args or ["A1_t10"]):
            diag(c)
    elif mode == "score":
        out = []
        for c in (args or list(COMBOS)):
            f = RESULTS / f"trades_v31_{c}.csv"
            sj = RESULTS / f"summary_v31_{c}.json"
            if not f.exists():
                continue
            tr = pd.read_csv(f)
            summ = json.load(open(sj)) if sj.exists() else {}
            m = metrics(c, tr, summ, summ.get("count", {}), {})
            show(m)
            out.append(m)
        table(out)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
