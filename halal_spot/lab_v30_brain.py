#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lab_v30_brain.py — the live laboratory for the v30 Cognitive Multi-State
Brain: three modules, each measured ALONE and IN COMBINATION, always by
running the REAL engine (`strategy_v30_ict_brain.run_backtest`) and scoring
it with the engine's own `summarize()` — the same code path that prints the
five mandatory asserts in an official run.

No re-simulation, no discount factor, no post-hoc filtering of a frozen
trade list. The v28/v29 lesson is built into this lab: a post-hoc reading
of the 297-trade book has not survived contact with the live engine once
(a filter reading 33.12% @ n=199 became 24.24% @ n=40 live), because
changing one decision changes which setups are drawn next.

MODULES
  1a persistent vigilance   BE_STREAK_MODE  reset | hold | decay
  1b structural proof shield SHIELD_RULE_V30  MID+BOS | MID|BOS | MID | BOS | A0.5 | A0.75
  2  regime-aware dual entry ENTRY_BRAIN  sniper | dual   (+ CISD_NEEDS_GREEN_BODY)
  3a institutional box floor RISK_FLOOR_PCT  0.10 | 0.30 | 0.40
  3b spot dollar-R sizing    SIZING  allcash | dollarR   (+ DOLLAR_R_PCT)

USAGE
    python3 lab_v30_brain.py smoke [COMBO ...]   # 6-month sanity, ~1 min each
    python3 lab_v30_brain.py run   [COMBO ...]   # full 2021-2026, ~6 min each
    python3 lab_v30_brain.py combos              # list the combos
    python3 lab_v30_brain.py score [COMBO ...]   # re-score saved trade files
    python3 lab_v30_brain.py diag  COMBO         # crosstab vs the v27 book

Every combo writes results/trades_v30_<combo>.csv and
results/summary_v30_<combo>.json, and the sweep appends its row to
results/lab_v30_sweep.csv so nothing is lost to a sandbox wipe.
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

# --------------------------------------------------------------------- #
# the combos: every module alone, then the combinations that matter
# --------------------------------------------------------------------- #
BASE = dict(BE_STREAK_MODE="reset", SHIELD_RULE_V30="MID+BOS",
            ENTRY_BRAIN="sniper", CISD_NEEDS_GREEN_BODY=True,
            RISK_FLOOR_PCT=0.10, SIZING="allcash", DOLLAR_R_PCT=0.3267,
            CISD_TIER3_EXEMPT=False, CISD_IGNORE_NOCHASE=False, ABSORB_MAX_BARS=6,
            ENTRY_ARM="seam", MANAGE_5M=False)

COMBOS = {
    "base":        {},
    # --- module 1a: persistent vigilance -----------------------------
    "M1a_hold":    dict(BE_STREAK_MODE="hold"),
    "M1a_decay":   dict(BE_STREAK_MODE="decay"),
    # --- module 1b: which structural proof arms the BE shield --------
    "M1b_or":      dict(SHIELD_RULE_V30="MID|BOS"),
    "M1b_mid":     dict(SHIELD_RULE_V30="MID"),
    "M1b_bos":     dict(SHIELD_RULE_V30="BOS"),
    "M1b_a05":     dict(SHIELD_RULE_V30="A0.5"),
    "M1b_a075":    dict(SHIELD_RULE_V30="A0.75"),
    # --- module 1 as a whole (a + b) ---------------------------------
    "M1_ab":       dict(BE_STREAK_MODE="hold", SHIELD_RULE_V30="MID|BOS"),
    # --- module 2: the dual entry brain ------------------------------
    "M2_dual":     dict(ENTRY_BRAIN="dual"),
    "M2_dual_loose": dict(ENTRY_BRAIN="dual", CISD_NEEDS_GREEN_BODY=False),
    "M2_dual_x3":  dict(ENTRY_BRAIN="dual", CISD_TIER3_EXEMPT=True),
    "M2_dual_nc":  dict(ENTRY_BRAIN="dual", CISD_IGNORE_NOCHASE=True),
    "M2_dual_nc3": dict(ENTRY_BRAIN="dual", CISD_IGNORE_NOCHASE=True,
                        ABSORB_MAX_BARS=3),
    "M2_dual_nc12": dict(ENTRY_BRAIN="dual", CISD_IGNORE_NOCHASE=True,
                         ABSORB_MAX_BARS=12),
    "M2_dual_full": dict(ENTRY_BRAIN="dual", CISD_IGNORE_NOCHASE=True,
                         CISD_TIER3_EXEMPT=True),
    # --- module 3a: the dust-box floor -------------------------------
    "M3a_030":     dict(RISK_FLOOR_PCT=0.30),
    "M3a_040":     dict(RISK_FLOOR_PCT=0.40),
    # --- module 3b: spot dollar-R equalization -----------------------
    "M3b_dollarR": dict(SIZING="dollarR"),
    # --- combinations -------------------------------------------------
    "M12":         dict(BE_STREAK_MODE="hold", SHIELD_RULE_V30="MID|BOS",
                        ENTRY_BRAIN="dual", CISD_TIER3_EXEMPT=True),
    "M13":         dict(BE_STREAK_MODE="hold", SHIELD_RULE_V30="MID|BOS",
                        RISK_FLOOR_PCT=0.30, SIZING="dollarR"),
    "M23":         dict(ENTRY_BRAIN="dual", RISK_FLOOR_PCT=0.30,
                        SIZING="dollarR"),
    "all":         dict(BE_STREAK_MODE="hold", SHIELD_RULE_V30="MID|BOS",
                        ENTRY_BRAIN="dual", CISD_TIER3_EXEMPT=True,
                        RISK_FLOOR_PCT=0.30, SIZING="dollarR"),
}
SWEEP_CSV = Path(os.environ.get("V30_SWEEP",
                               str(RESULTS / "lab_v30_sweep.csv")))


# --------------------------------------------------------------------- #
def drive(combo: str, window=FULL, save=True):
    import strategy_v30_ict_brain as S
    cfg = dict(BASE)
    cfg.update(COMBOS.get(combo, {}))
    for k, v in cfg.items():
        setattr(S, k, v)
    print(f"\n########## LIVE ENGINE · combo={combo} · "
          f"{window[0]}..{window[1]} ##########", flush=True)
    print(f"    config: " + "  ".join(f"{k}={v}" for k, v in cfg.items()
                                     if k not in ("ENTRY_ARM", "MANAGE_5M")),
          flush=True)
    run = S.run_backtest(S.DATA_DIR, window[0], window[1], tag=f"v30{combo}")
    tr = pd.DataFrame(run["trades"])
    try:
        summ = S.summarize(run)
    except AssertionError as e:
        # the engine's own L1 law: a winner below +3.00R. That is a real
        # finding (ASSERT2 violated), not a lab crash - record and go on.
        print(f"    !! summarize() raised: {e}", flush=True)
        summ = {"_l1_violation": str(e)}
    if save and window == FULL:
        tr.to_csv(RESULTS / f"trades_v30_{combo}.csv", index=False)
        with open(RESULTS / f"summary_v30_{combo}.json", "w") as f:
            json.dump(summ, f, indent=2, default=str)
        if len(run["equity"]):
            run["equity"].to_csv(RESULTS / f"equity_v30_{combo}.csv")
    m = metrics(combo, tr, summ, run["count"], cfg)
    show(m)
    append_sweep(m, window)
    return m, tr


def metrics(combo, tr, summ, count, cfg):
    n = len(tr)
    W = int((tr["class"] == "WIN").sum()) if n else 0
    B = int((tr["class"] == "BE").sum()) if n else 0
    L = int((tr["class"] == "LOSS").sum()) if n else 0
    wr = 100 * W / (W + L) if W + L else 0.0
    wins = tr[tr["class"] == "WIN"] if n else tr
    yr = (tr.entry_time.astype(str).str[:4].value_counts()
          .reindex(YEARS).fillna(0).astype(int).to_dict()) if n else \
        {y: 0 for y in YEARS}
    cur = best = cons = cons_best = 0
    for c in (tr["class"] if n else []):
        if c == "LOSS":
            cur += 1; best = max(best, cur)
            cons += 1; cons_best = max(cons_best, cons)
        elif c == "WIN":
            cur = 0; cons = 0
        else:
            cur = 0

    def fnum(k, dv=0.0):
        v = summ.get(k)
        return float(v) if isinstance(v, (int, float)) else dv

    risk = (tr.entry_price - tr.stop_price) / tr.entry_price * 100 if n \
        else pd.Series(dtype=float)
    feeR = (2 * 0.001 * tr.entry_price / (tr.entry_price - tr.stop_price)) \
        if n else pd.Series(dtype=float)
    m = dict(
        combo=combo, window="full", n=n, W=W, BE=B, L=L, wr=round(wr, 2),
        min_win_R=round(float(wins.R.min()), 2) if len(wins) else None,
        ge4R=int((tr.R >= 4).sum()) if n else 0,
        ge10R=int((tr.R >= 10).sum()) if n else 0,
        maxR=round(float(tr.R.max()), 2) if n else 0.0,
        totR=round(float(tr.R.sum()), 2) if n else 0.0,
        streak=best, streak_cons=cons_best,
        yearly=yr, ymin=min(yr[y] for y in YEARS[:5]),
        net_pct=round(fnum("net_pct", 100 * float(tr.net_pnl.sum()) / 200
                           if n else 0.0), 2),
        end_eq=round(fnum("end_equity", 200.0), 2),
        pf=round(fnum("profit_factor"), 3),
        maxDD=round(fnum("max_drawdown_pct"), 2),
        med_risk_pct=round(float(risk.median()), 4) if n else None,
        share_fee_ge_1R=round(float((feeR >= 1).mean() * 100), 1) if n else None,
        med_fee_in_R=round(float(feeR.median()), 3) if n else None,
        cisd_fills=int((count or {}).get("fill_v30_cisd", 0)),
        cisd_reclaim=int((count or {}).get("v30_cisd_reclaim", 0)),
        await_cisd=int((count or {}).get("v30_await_cisd", 0)),
        calm_fills=int((count or {}).get("v30_calm_seam_fill", 0)),
        cisd_armed=int((count or {}).get("v30_cisd_armed", 0)),
        sacred_seam=int((count or {}).get("sacred_law_seam_ok", 0)),
        sacred_cisd=int((count or {}).get("sacred_law_cisd_ok", 0)),
        shield_armed=int((count or {}).get("shield_armed_disp", 0)),
        be_holds=int((count or {}).get("shield_be_holds_streak", 0)),
        be_decays=int((count or {}).get("v30_be_decays_streak", 0)),
        dollarR_sized=int((count or {}).get("v30_dollarR_sized", 0)),
        dollarR_capped=int((count or {}).get("v30_dollarR_capped", 0)),
        cfg=json.dumps(cfg),
    )
    m["A1"] = bool(m["wr"] >= 60.0)
    m["A2"] = bool(m["min_win_R"] is None or m["min_win_R"] >= MIN_R - 1e-9)
    m["A3"] = bool(m["ge4R"] >= 5 and m["maxR"] >= 6.0)
    m["A4"] = bool(m["streak"] <= 3)
    m["A5"] = bool(m["n"] >= 150 and m["ymin"] >= 12)
    m["passed"] = sum(m[k] for k in ("A1", "A2", "A3", "A4", "A5"))
    return m


def show(m):
    print(f"[{m['combo']:>13}] n={m['n']:4d}  {m['W']:3d}W/{m['BE']:3d}BE/"
          f"{m['L']:3d}L  WR={m['wr']:6.2f}%  minWin={m['min_win_R']}  "
          f">=4R={m['ge4R']:3d}  maxR={m['maxR']:6.2f}  totR={m['totR']:8.2f}",
          flush=True)
    print(f"                net={m['net_pct']:+7.2f}% (${m['end_eq']})  "
          f"PF={m['pf']}  maxDD={m['maxDD']}%  streak={m['streak']}/"
          f"{m['streak_cons']}  yearly={m['yearly']}", flush=True)
    print(f"                medRisk%={m['med_risk_pct']}  "
          f"share(fee>=1R)={m['share_fee_ge_1R']}%  "
          f"CISD arm/reclaim/fill={m['cisd_armed']}/{m['cisd_reclaim']}/"
          f"{m['cisd_fills']}  calm={m['calm_fills']}  "
          f"shield_armed={m['shield_armed']}  "
          f"sacred(seam/cisd)={m['sacred_seam']}/{m['sacred_cisd']}",
          flush=True)
    a = "".join("P" if m[k] else "F"
                for k in ("A1", "A2", "A3", "A4", "A5"))
    print(f"                asserts A1..A5 = {a}  -> {m['passed']}/5",
          flush=True)
    for k in ("A1", "A2", "A3", "A4", "A5"):
        print(f"                ASSERT{k[-1]} "
              f"{'PASSED' if m[k] else 'FAILED'}", flush=True)


def append_sweep(m, window):
    row = {k: v for k, v in m.items()}
    row["window"] = "full" if window == FULL else "smoke"
    row["yearly"] = json.dumps(row["yearly"])
    df = pd.DataFrame([row])
    if SWEEP_CSV.exists() and window == FULL:
        old = pd.read_csv(SWEEP_CSV)
        old = old[old.combo != m["combo"]]
        df = pd.concat([old, df], ignore_index=True)
    if window == FULL:
        df.to_csv(SWEEP_CSV, index=False)


# --------------------------------------------------------------------- #
def diag(combo):
    """Crosstab against the v27 book, matched on entry_time. Module 1 and
    3a keep the entries, so the match rate is high and the crosstab shows
    exactly how many of v27's 161 losses became scratches."""
    f = RESULTS / f"trades_v30_{combo}.csv"
    if not f.exists():
        print(f"missing {f}")
        return None
    a = pd.read_csv(RESULTS / "trades_v27.csv")
    b = pd.read_csv(f)
    m = a.merge(b, on="entry_time", suffixes=("_27", "_30"))
    print(f"\n=== DIAG {combo}: matched {len(m)} of v27's {len(a)} trades "
          f"on entry_time (v30 book has {len(b)}) ===")
    if len(m):
        print(pd.crosstab(m.class_27, m.class_30).to_string())
        for src in ("LOSS", "BE", "WIN"):
            sub = m[m.class_27 == src]
            if not len(sub):
                continue
            vc = sub.class_30.value_counts().to_dict()
            print(f"    v27 {src:5s} n={len(sub):3d} -> "
                  + "  ".join(f"{k}:{v}" for k, v in sorted(vc.items())))
        print(f"    totR matched: v27 {m.R_27.sum():.2f} -> "
              f"v30 {m.R_30.sum():.2f}")
        print(f"    net$ matched: v27 {m.net_pnl_27.sum():.2f} -> "
              f"v30 {m.net_pnl_30.sum():.2f}")
    return m


def table(ms):
    ref = []
    for tag, fn in (("v25", "summary_v25.json"), ("v27", "summary_v27.json")):
        p = RESULTS / fn
        if p.exists():
            j = json.load(open(p))
            ref.append(dict(combo=tag, n=j.get("trades"), W=j.get("wins"),
                            BE=j.get("breakevens"), L=j.get("losses"),
                            wr=j.get("win_rate_pct"),
                            min_win_R=j.get("min_winner_R"),
                            ge4R=j.get("runners_4r_plus"),
                            maxR=j.get("max_winner_R"),
                            net_pct=j.get("net_pct"),
                            pf=j.get("profit_factor"),
                            maxDD=j.get("max_drawdown_pct"),
                            streak=j.get("max_consecutive_losses"),
                            streak_cons=None, ymin=None, passed=None,
                            totR=None, yearly=None))
    rows = ref + list(ms)

    def nz(v, d=0.0):
        return v if isinstance(v, (int, float)) else d
    print("\n=============== v30 LIVE COMPARISON TABLE ===============")
    print(f"{'combo':>13} {'n':>4} {'W':>4}{'BE':>5}{'L':>5} {'WR%':>7} "
          f"{'minW':>5} {'>=4R':>5} {'maxR':>7} {'totR':>8} {'net%':>8} "
          f"{'PF':>6} {'maxDD%':>7} {'strk':>5} {'ymin':>5} {'5as':>4}")
    for r in rows:
        pa = f"{r['passed']}/5" if r.get("passed") is not None else "-"
        ymin = r.get("ymin") if r.get("ymin") is not None else "-"
        print(f"{r['combo']:>13} {int(nz(r['n'])):4d} {int(nz(r['W'])):4d}"
              f"{int(nz(r['BE'])):5d}{int(nz(r['L'])):5d} {nz(r['wr']):7.2f} "
              f"{str(r.get('min_win_R')):>5} {int(nz(r['ge4R'])):5d} "
              f"{nz(r['maxR']):7.2f} "
              f"{nz(r.get('totR')) if r.get('totR') is not None else 0.0:8.2f} "
              f"{nz(r['net_pct']):+8.2f} {nz(r['pf']):6.2f} "
              f"{nz(r['maxDD']):7.2f} {str(nz(r.get('streak'),0)):>5} "
              f"{str(ymin):>5} {pa:>4}")
    print("=========================================================")
    for r in rows:
        if r.get("yearly"):
            print(f"  {r['combo']:>13} yearly: {r['yearly']}")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "run"
    args = sys.argv[2:]
    if mode == "combos":
        for k, v in COMBOS.items():
            print(f"{k:14s} {v}")
        return
    if mode == "smoke":
        out = []
        for combo in (args or ["base"]):
            m, _ = drive(combo, SMOKE, save=False)
            m["window"] = "smoke"
            out.append(m)
        table(out)
    elif mode == "run":
        out = []
        for combo in (args or ["base"]):
            m, _ = drive(combo, FULL)
            out.append(m)
        table(out)
        for combo in (args or []):
            if combo != "base":
                diag(combo)
    elif mode == "score":
        out = []
        for combo in (args or list(COMBOS)):
            f = RESULTS / f"trades_v30_{combo}.csv"
            if not f.exists():
                continue
            tr = pd.read_csv(f)
            sj = RESULTS / f"summary_v30_{combo}.json"
            summ = json.load(open(sj)) if sj.exists() else {}
            m = metrics(combo, tr, summ, {}, json.loads(
                tr.v30_brain.iloc[0]) if False else {})
            show(m)
            out.append(m)
        table(out)
    elif mode == "diag":
        for combo in (args or ["M1a_hold"]):
            diag(combo)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
