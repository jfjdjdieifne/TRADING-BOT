"""v39 STEP 2 -- wire the golden-sniper discriminators and measure them.

STEP 1 (`audit_v39_golden_sniper.py`) produced exactly one discriminator with
genuine cross-window consistency, and killed three. This driver runs each one
through the real engine on all five windows so the arithmetic can be
confirmed or refuted by the portfolio, not by a column.

WHAT STEP 1 SAID  (see results/_audit_v39_full.txt)
    box_age_bars   [0,6)=7.8% golden, [12,24)=22.8%  --> WIRE (1)
    in_4h_demand   3/5 windows improved              --> WIRE (3), expect weak
    fvg_pct        no monotone separation            --> WIRE (2), expect fail
    time-stop      chaff dies in 0.33h MEDIAN        --> WIRE (4), expect no-op
    weapon A/B     column is CONSTANT                --> NOT MEASURABLE

Every knob is default OFF. Every arm is checked for state leaks.

Run:  python lab_v39_golden_sniper.py arms
      python lab_v39_golden_sniper.py arm AGE12 --window W1
      python lab_v39_golden_sniper.py table
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
RESULTS.mkdir(exist_ok=True)
sys.path.insert(0, str(HERE))

BASKET = str(HERE / "data" / "binance_5m")

WINDOWS = {
    "W1":     ("2023-10-01", "2024-03-31"),
    "W2":     ("2024-05-01", "2024-10-31"),
    "FULL15": ("2023-08-01", "2024-10-31"),
    "OLD7":   ("2023-01-01", "2023-07-31"),
    "MOD_Y1": ("2024-11-01", "2025-10-31"),
    "MOD_Y2": ("2025-11-01", "2026-10-31"),
    "MODERN_24M": ("2024-11-01", "2026-10-31"),
}
FIVE = ["W1", "W2", "OLD7", "MOD_Y1", "MOD_Y2"]

# ---- v39 knobs, with their OFF value --------------------------------- #
_V39_KNOBS = {
    "MIN_BOX_AGE_BARS": 0,
    "TRAIL_ANCHOR": "",
    "HTF_DEMAND_GATE": "",
    "TIME_STOP_BARS": 0,
    "TIME_STOP_R": 1.0,
}

# every earlier round's knobs must also be hard-reset, or an arm inherits
# the previous arm's book and the comparison is meaningless
_V38_KNOBS = {
    "TRAIL_TF_AFTER_3R": "",
    "TRAIL_AFTER_3R_MIN_PCT": 0.0,
    "DOL_TARGET_LOCK": False,
    "DOL_LOCK_MIN_PCT": 2.0,
    "DOL_LOCK_KEEP": 0.75,
    "ANTI_SHAKEOUT_BE": False,
    "MIN_BE_DISPLACEMENT_PCT": 1.2,
    "MIN_DOL_ROOM_PCT": 0.0,
    "ADAPT_4H_RATCHET": False,
}
_V37_KNOBS = {
    "POST_3R_RATCHET": "",
    "POST_3R_RATCHET_TF": "5min",
    "HTF_ENTRY_GATE": "",
    "COOLDOWN_BOS_TF": "",
    "FIX_BE_COOLDOWN_BUG": False,
    "EXIT_SLIPPAGE_BPS": 0.0,
}
ALL_KNOBS = {**_V39_KNOBS, **_V38_KNOBS, **_V37_KNOBS}

SHIPPED = dict(
    CAPITAL=100.0,
    ALLOC_MODE="slot", SLOTS=1, SLOT_FILL="fixed",
    MAX_OPEN_POSITIONS=1, FULL_100_DEPLOY=True,
    PER_COIN_COOLDOWN=2, COOLDOWN_DAYS=14.0, COOLDOWN_NEEDS_BOS=True,
    SMT_BRAIN=True, SMT_GATE="prefer",
    KILLZONE_MODE="exclude", KILLZONE_DOW=(6,),
    MIN_STOP_PCT=0.0, NO_FALL_CLOSE=False,
    FLASH_SELLER_VETO=False, SLIPPAGE_BPS=0.0,
)

# The arms. Each is (knobs, what STEP 1 predicted). The prediction is written
# down BEFORE the run so a failure cannot be quietly reframed as success.
COMBOS = {
    "B0":        dict(),
    "AGE12":     dict(MIN_BOX_AGE_BARS=12),
    "AGE24":     dict(MIN_BOX_AGE_BARS=24),
    "DEMAND4H":  dict(HTF_DEMAND_GATE="4H"),
    "DEMAND1H":  dict(HTF_DEMAND_GATE="1H"),
    "FVG_TRAIL": dict(TRAIL_ANCHOR="fvg"),
    "TSTOP2H":   dict(TIME_STOP_BARS=24),        # 24 exec bars @5m = 2h
    "TSTOP4H":   dict(TIME_STOP_BARS=48),
    "TSTOP12H":  dict(TIME_STOP_BARS=144),
    # the sniper combo: only the two that the audit scored positively
    "SNIPER":    dict(MIN_BOX_AGE_BARS=12, HTF_DEMAND_GATE="4H"),
}

PREDICT = {
    "B0":        "reference -- must reproduce v37 exactly",
    "AGE12":     "WIN: golden rate 7.8%->22.8% in the kept buckets",
    "AGE24":     "win or wash: fewer trades, thinner sample",
    "DEMAND4H":  "weak win: 3/5 windows on the tape",
    "DEMAND1H":  "LOSS: 1/5 windows on the tape",
    "FVG_TRAIL": "LOSS: fvg_pct has no monotone separation",
    "TSTOP2H":   "no-op: chaff already dies in a 0.33h median",
    "TSTOP4H":   "no-op",
    "TSTOP12H":  "no-op or small loss (cuts slow runners)",
    "SNIPER":    "best case: fewer trades, higher PF, lower net",
}


def _snapshot(S):
    out = {k: getattr(S, k) for k in ALL_KNOBS}
    out.update({k: getattr(S, k) for k in SHIPPED})
    return out


def _restore(S, snap):
    for k, v in snap.items():
        setattr(S, k, v)


def _assert_wired(S, combo: str) -> None:
    """Refuse to run an arm whose knob the engine only DEFINES.

    v37 and v38 both shipped a constant that looked like a control; the arm
    then returned B0 to the cent and read like a null result. A knob the
    engine never evaluates cannot be measured, so it is an ERROR.
    """
    import inspect
    import re
    # BUG FOUND IN THIS ROUND'S OWN HARNESS: the first version counted
    # occurrences in the RAW source, so a knob whose name appeared in a
    # header COMMENT passed the check while being completely unwired.
    # TRAIL_ANCHOR did exactly that and returned B0 to the cent. The name
    # must now appear in executable code: comments are stripped first.
    src = inspect.getsource(S)
    code = re.sub(r"#.*", "", src)
    for k in COMBOS[combo]:
        n = code.count(k)
        if n < 2:
            raise SystemExit(
                f"ARM {combo}: knob {k!r} appears {n}x in the engine CODE "
                f"(comments excluded) -- it is a constant, not a control. "
                f"Wire it before measuring.")


def monthly(tr: pd.DataFrame, capital: float) -> dict:
    if tr.empty:
        return {}
    d = tr.copy()
    d["exit_time"] = pd.to_datetime(d.exit_time.astype(str), utc=True,
                                    format="mixed")
    d["ym"] = d.exit_time.dt.strftime("%Y-%m")
    d["net_pnl"] = d.net_pnl.astype(float)
    d = d.sort_values("exit_time")
    d["cum"] = capital + d.net_pnl.cumsum()
    return {ym: {"net$": round(float(g.net_pnl.sum()), 4),
                 "end": round(float(g.cum.iloc[-1]), 4)}
            for ym, g in d.groupby("ym")}


def drive(combo: str, win: str, save: bool = True) -> dict:
    import strategy_v36_ict_champion as S

    if combo not in COMBOS:
        raise SystemExit(f"unknown combo {combo!r}")
    _assert_wired(S, combo)
    pre = _snapshot(S)
    try:
        for k, v in ALL_KNOBS.items():
            setattr(S, k, v)                     # hard reset to OFF
        for k, v in {**SHIPPED, **COMBOS[combo]}.items():
            if not hasattr(S, k):
                raise SystemExit(f"{combo}: engine has no knob {k!r}")
            setattr(S, k, v)
        S.V32_DATA_DIR = BASKET
        start, end = WINDOWS[win]
        print(f"\n##### v39 combo={combo} {win} {start}..{end} #####",
              flush=True)
        print("    overrides: " +
              (json.dumps(COMBOS[combo], default=str) or "-"), flush=True)
        t0 = time.time()
        run = S.run_backtest(S.v34_data_dir(), start, end,
                             tag=f"v39{combo}{win}")
        secs = time.time() - t0

        tr = pd.DataFrame(run["trades"])
        res = {"arm": combo, "window": win, "start": start, "end": end,
               "seconds": round(secs, 1), "n": int(len(tr)),
               "capital": float(S.CAPITAL),
               "predicted": PREDICT.get(combo, "")}
        if len(tr):
            tr["net_pnl"] = tr.net_pnl.astype(float)
            cls = tr["class"].astype(str)
            gp = float(tr.loc[tr.net_pnl > 0, "net_pnl"].sum())
            gl = float(-tr.loc[tr.net_pnl < 0, "net_pnl"].sum())
            n3 = tr.net_pnl.nlargest(3).sum() if len(tr) >= 3 else \
                tr.net_pnl.sum()
            res.update(
                net=round(float(tr.net_pnl.sum()), 4),
                end_equity=round(100.0 + float(tr.net_pnl.sum()), 4),
                pf=round(gp / gl, 3) if gl > 1e-9 else None,
                wr=round(100.0 * cls.isin(["WIN", "SWIN"]).mean(), 2),
                be=int(cls.isin(["BE", "BREAKEVEN"]).sum()),
                losses=int((cls == "LOSS").sum()),
                fees=round(float(run["fees"]), 4),
                net_minus_top3=round(float(tr.net_pnl.sum() - n3), 4),
                exits=tr.exit_reason.value_counts().to_dict(),
                monthly=monthly(tr, float(S.CAPITAL)))
            res["months_pos"] = sum(1 for m in res["monthly"].values()
                                    if m["net$"] > 0)
            res["months_n"] = len(res["monthly"])
            eq = run["equity"]
            if len(eq):
                e = eq["equity"].astype(float)
                peak = e.cummax()
                res["maxDD_pct"] = round(float(((e - peak) / peak).min()
                                               * 100.0), 3)
        if save:
            (RESULTS / f"lab_v39_{combo}_{win}.json").write_text(
                json.dumps(res, indent=1, default=str))
            if len(tr):
                tr.to_csv(RESULTS / f"trades_v39_{combo}_{win}.csv",
                          index=False)
        print(f"    n={res['n']} end=${res['end_equity']:.4f} "
              f"PF={res.get('pf')} DD={res.get('maxDD_pct')}% "
              f"mo+={res.get('months_pos')}/{res.get('months_n')} "
              f"({res['seconds']}s)", flush=True)
        return res
    finally:
        _restore(S, pre)          # NO STATE LEAKS BETWEEN ARMS
        for k, v in ALL_KNOBS.items():
            if getattr(S, k) != v:
                raise SystemExit(f"STATE LEAK after {combo}/{win}: "
                                 f"{k}={getattr(S, k)!r}, expected {v!r}")
        if S.CAPITAL != pre["CAPITAL"]:
            raise SystemExit("STATE LEAK: CAPITAL")


# --------------------------------------------------------------------- #
# reporting
# --------------------------------------------------------------------- #
def true_baseline() -> dict:
    """B0 end_equity per window, computed from the committed v37 tapes.

    The tapes are the shipped engine's own output (v38 proved them
    byte-identical to a fresh B0 run), so they are the only honest
    baseline -- and they exist for all five windows, which a single
    target run does not.
    """
    out = {}
    for w in FIVE:
        f = RESULTS / f"trades_v37_B0_{w}.csv"
        if f.exists():
            d = pd.read_csv(f, usecols=["net_pnl"])
            out[w] = round(100.0 + float(d.net_pnl.astype(float).sum()), 4)
    return out


TRUE_B0 = true_baseline()


def table() -> None:
    print("=" * 108)
    print("v39 STEP 2 RESULTS  --  golden-sniper knobs through the engine")
    print("=" * 108)
    hdr = (f"{'arm':10s}{'W1':>9s}{'W2':>9s}{'OLD7':>9s}"
           f"{'MOD_Y1':>9s}{'MOD_Y2':>9s}{'wins':>6s}{'n_tot':>7s}"
           f"{'golden':>7s}{'fees$':>9s}")
    print(hdr)
    print("-" * len(hdr))
    base = {}
    for a in COMBOS:
        row, wins, ntot, gtot, fee = f"{a:10s}", 0, 0, 0, 0.0
        for w in FIVE:
            # B0's own row is filled from the committed tapes: only W1 was
            # re-run (as the identity check), but the tape exists for all
            # five windows and is the same engine with every knob off.
            if a == "B0":
                if w in TRUE_B0:
                    row += f"{TRUE_B0[w]:9.2f}"
                else:
                    row += f"{'-':>9s}"
                continue
            f = RESULTS / f"lab_v39_{a}_{w}.json"
            if not f.exists():
                row += f"{'-':>9s}"
                continue
            j = json.loads(f.read_text())
            # BUG FOUND IN THIS ROUND'S OWN HARNESS #2: the first version
            # seeded the baseline from whichever arm happened to run first,
            # so B0 was only present for W1 and every other window was
            # scored against W1's $158.02 -- which made DEMAND4H and
            # TSTOP2H look like 2-3 "wins" that were pure artefacts. The
            # baseline is now the committed B0 tape for THAT window.
            if a == "B0":
                base[w] = j["end_equity"]
            elif w in TRUE_B0 and j["end_equity"] > TRUE_B0[w]:
                wins += 1
            ntot += j["n"]
            fee += j.get("fees", 0.0)
            row += f"{j['end_equity']:9.2f}"
            # golden count from the tape
            tf = RESULTS / f"trades_v39_{a}_{w}.csv"
            if tf.exists():
                d = pd.read_csv(tf)
                for c in ("mfe_R", "risk_pct", "net_pnl"):
                    d[c] = d[c].astype(float)
                g = (d.net_pnl > 0) & ((d.mfe_R * d.risk_pct >= 2.5)
                                       | (d.mfe_R >= 3.0))
                gtot += int(g.sum())
        print(f"{row}{wins:6d}{ntot:7d}{gtot:7d}{fee:9.2f}")
    print()
    print("    wins = windows where this arm beat B0 on end_equity (0-5).")
    print("    golden = trades matching the STEP 1 GOLDEN definition.")
    print()

    print("--- SHIP TEST: an arm may ship only if it wins 5/5 AND keeps")
    print("    the golden cohort AND cuts fees. Nothing else is evidence. ---")
    print(f"{'arm':10s}{'wins':>6s}{'net_sum$':>11s}{'fees$':>9s}"
          f"{'golden':>7s}{'n_tot':>7s}{'verdict':>12s}")
    g0 = 0
    for w in FIVE:
        f = RESULTS / f"trades_v37_B0_{w}.csv"
        if f.exists():
            d = pd.read_csv(f)
            for c in ("mfe_R", "risk_pct", "net_pnl"):
                d[c] = d[c].astype(float)
            g0 += int(((d.net_pnl > 0) & ((d.mfe_R * d.risk_pct >= 2.5)
                                          | (d.mfe_R >= 3.0))).sum())
    for a in COMBOS:
        nets, w5, n_t, g_t, fe = 0.0, 0, 0, 0, 0.0
        got = 0
        for w in FIVE:
            f = RESULTS / f"lab_v39_{a}_{w}.json"
            if not f.exists():
                continue
            got += 1
            j = json.loads(f.read_text())
            nets += j.get("net", 0.0)
            fe += j.get("fees", 0.0)
            n_t += j["n"]
            if w in TRUE_B0 and j["end_equity"] > TRUE_B0[w]:
                w5 += 1
            tf = RESULTS / f"trades_v39_{a}_{w}.csv"
            if tf.exists():
                d = pd.read_csv(tf)
                for c in ("mfe_R", "risk_pct", "net_pnl"):
                    d[c] = d[c].astype(float)
                g_t += int(((d.net_pnl > 0) & ((d.mfe_R * d.risk_pct >= 2.5)
                                               | (d.mfe_R >= 3.0))).sum())
        if a == "B0":
            # B0 is measured from the five committed tapes: all knobs off,
            # same engine, and it is the reference every arm is scored on.
            nets, n_t, g_t, fe, got = 0.0, 0, 0, 0.0, 5
            for w in FIVE:
                f = RESULTS / f"trades_v37_B0_{w}.csv"
                if not f.exists():
                    continue
                d = pd.read_csv(f)
                for c in ("mfe_R", "risk_pct", "net_pnl", "notional"):
                    d[c] = d[c].astype(float)
                nets += d.net_pnl.sum()
                n_t += len(d)
                fe += (d.notional * 0.002).sum()
                g_t += int(((d.net_pnl > 0)
                            & ((d.mfe_R * d.risk_pct >= 2.5)
                               | (d.mfe_R >= 3.0))).sum())
        if got == 0:
            continue
        ship = (got == 5 and w5 == 5 and g_t >= g0 and fe < 0)
        print(f"{a:10s}{w5:>4d}/{got:<2d}{nets:11.2f}{fe:9.2f}{g_t:7d}"
              f"{n_t:7d}{'SHIP' if ship else 'reject':>12s}")
    print(f"\n    B0 golden cohort (all 5 windows) = {g0} trades.")
    print()

    print("--- trades per week and fees, B0 vs the sniper combo ---")
    print(f"{'arm':10s}{'win':8s}{'wk':>5s}{'n':>5s}{'tr/wk':>7s}"
          f"{'fees$':>9s}{'net$':>10s}{'PF':>6s}{'DD%':>7s}{'mo+':>6s}")
    for a in ("B0", "AGE12", "SNIPER"):
        for w in FIVE:
            f = RESULTS / f"lab_v39_{a}_{w}.json"
            if not f.exists():
                continue
            j = json.loads(f.read_text())
            s0, s1 = WINDOWS[w]
            wk = ((pd.Timestamp(s1) - pd.Timestamp(s0)).days + 1) / 7.0
            print(f"{a:10s}{w:8s}{wk:5.0f}{j['n']:5d}{j['n']/wk:7.2f}"
                  f"{j.get('fees',0):9.2f}{j.get('net',0):10.2f}"
                  f"{str(j.get('pf')):>6s}{str(j.get('maxDD_pct')):>7s}"
                  f"{j.get('months_pos')}/{j.get('months_n'):<4}")
        print()


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "arms"
    win = None
    if "--window" in sys.argv:
        win = sys.argv[sys.argv.index("--window") + 1]
    if cmd == "arms":
        for w in FIVE:
            for a in COMBOS:
                drive(a, w)
        table()
    elif cmd == "arm":
        w = win or "W1"
        drive(sys.argv[2], w)
    elif cmd == "table":
        table()
    else:
        raise SystemExit(f"unknown command {cmd!r}")


if __name__ == "__main__":
    main()
