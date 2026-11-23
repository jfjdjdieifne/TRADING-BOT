"""v38 PART 2 -- the 100% deploy ICT DOL & trail lab.

Every arm here is a DEFAULT-OFF engine knob. This file only turns them on,
one at a time, and measures. Nothing ships unless a window matrix says so.

WHY THE ARMS ARE NOT THE ONES THE BRIEF NAMED, VERBATIM
  Part 1 (audit_v38_spot_reality.py) measured four of the five premises
  and three of them came back the other way. The arms below are the same
  IDEAS, wired to what the engine actually owns:

  1. TRAIL_TF_AFTER_3R       kept. Part 1 Q3 3.1: the 4H lens breached on
                             402 of 424 locked trades (95%). Q3 3.2: a
                             confirmed 1H swing low sat above entry on ~100%
                             of those same trades. This is the one arm with
                             direct evidence behind it.
  2. DOL_TARGET_LOCK         kept, but Q3 3.3 already says most locked
                             trades DID reach a draw and still gave it back
                             (45-55% exited <= +0.2%), so this is the arm
                             most likely to pay.
  3. ANTI_SHAKEOUT_BE        kept. Q2 quantified it: 2-11% of BE trades per
                             window never revisited the stop and ran >= +2%
                             without us; conservative cost $10-$100.
  4. MIN_DOL_ROOM_PCT        kept ONLY as a falsification test. Q4 (a)
                             measured the SMALLEST-room bucket as the most
                             profitable ($/tr 2.46 and 3.01 in W1/W2), i.e.
                             the brief's premise is inverted. A positive
                             value here is expected to lose; running it
                             proves the claim instead of arguing it.
  5. ADAPT_4H_RATCHET        kept. v37 measured RATCHET_2R as a regime
                             trade (rescues MOD_Y2, clips MOD_Y1); Q4b
                             shows the same split by lock distance. This
                             applies the 2R floor only in bearish 4H flow.

Run:  python lab_v38_dol_harvester.py arms
      python lab_v38_dol_harvester.py run ARM --window W1
      python lab_v38_dol_harvester.py matrix
      python lab_v38_dol_harvester.py report
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

# ---- the v38 knobs, with their OFF value ----------------------------- #
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

# the v37 knobs also have to be reset, or an arm inherits the last one
_V37_KNOBS = {
    "POST_3R_RATCHET": "",
    "POST_3R_RATCHET_TF": "5min",
    "HTF_ENTRY_GATE": "",
    "COOLDOWN_BOS_TF": "",
    "FIX_BE_COOLDOWN_BUG": False,
    "EXIT_SLIPPAGE_BPS": 0.0,
}

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

COMBOS = {
    "B0":             dict(),
    "TRAIL_1H":       dict(TRAIL_TF_AFTER_3R="1h"),
    "TRAIL_1H_1PCT":  dict(TRAIL_TF_AFTER_3R="1h",
                           TRAIL_AFTER_3R_MIN_PCT=1.0),
    "TRAIL_1H_30M":   dict(TRAIL_TF_AFTER_3R="1h30m"),
    "TRAIL_1H_30M_15M": dict(TRAIL_TF_AFTER_3R="1h30m15m"),
    "DOL_LOCK":       dict(DOL_TARGET_LOCK=True),
    "DOL_LOCK_2_5":   dict(DOL_TARGET_LOCK=True, DOL_LOCK_MIN_PCT=2.5),
    "ANTI_BE_12":     dict(ANTI_SHAKEOUT_BE=True, MIN_BE_DISPLACEMENT_PCT=1.2),
    "ANTI_BE_15":     dict(ANTI_SHAKEOUT_BE=True, MIN_BE_DISPLACEMENT_PCT=1.5),
    "MIN_ROOM_1":     dict(MIN_DOL_ROOM_PCT=1.0),
    "ADAPT_4H":       dict(ADAPT_4H_RATCHET=True),
    "TRAIL_DOL":      dict(TRAIL_TF_AFTER_3R="1h", DOL_TARGET_LOCK=True),
}


def _snapshot(S):
    out = {k: getattr(S, k) for k in _V38_KNOBS}
    out.update({k: getattr(S, k) for k in _V37_KNOBS})
    # the knobs this lab ASSIGNS must be snapshotted too, or the leak check
    # below cannot restore them and the next arm inherits this one's book
    out.update({k: getattr(S, k) for k in SHIPPED})
    return out


def _restore(S, snap):
    for k, v in snap.items():
        setattr(S, k, v)


def monthly(tr: pd.DataFrame, capital: float) -> dict:
    if tr.empty:
        return {}
    d = tr.copy()
    d["exit_time"] = pd.to_datetime(d.exit_time.astype(str),
                                    utc=True, format="mixed")
    d["ym"] = d.exit_time.dt.strftime("%Y-%m")
    d["net_pnl"] = d.net_pnl.astype(float)
    eq = capital + d.sort_values("exit_time").net_pnl.cumsum()
    d["cum"] = eq.values
    out = {}
    for ym, g in d.groupby("ym"):
        out[ym] = {"net$": round(float(g.net_pnl.sum()), 4),
                   "end": round(float(g.cum.iloc[-1]), 4)}
    return out


def _assert_wired(S, combo: str) -> None:
    """Refuse to run an arm whose knobs the engine only DEFINES.

    v37 shipped a knob wired to a function that never ran; the arm then
    returned numbers identical to B0 and read like a null result. v38
    repeated it: DOL_TARGET_LOCK and MIN_DOL_ROOM_PCT were constants with
    zero logic, and DOL_LOCK came back at exactly $158.0240 -- B0 to the
    cent. That is now an ERROR, not a finding: a knob the engine never
    reads cannot be measured, so it must not be reported.
    """
    import inspect
    src = inspect.getsource(S)
    for k in COMBOS[combo]:
        if k in ("CAPITAL",) or k in SHIPPED and k not in COMBOS[combo]:
            continue
        # A knob is wired if the name appears anywhere OTHER than its
        # own assignment line -- i.e. the engine actually evaluates it.
        # (2 occurrences = "NAME = value" plus one read; that is WIRED.
        #  A constant-only knob appears once, in the header block.)
        n = src.count(k)
        if n < 2:
            raise SystemExit(
                f"ARM {combo}: knob {k!r} appears {n}x in the engine -- "
                f"it is a constant, not a control. Wire it before measuring.")


def drive(combo: str, win: str, save: bool = True) -> dict:
    import strategy_v36_ict_champion as S

    if combo not in COMBOS:
        raise SystemExit(f"unknown combo {combo!r}")
    _assert_wired(S, combo)
    pre = _snapshot(S)
    try:
        for k, v in {**_V38_KNOBS, **_V37_KNOBS}.items():
            setattr(S, k, v)                     # hard reset to OFF
        for k, v in {**SHIPPED, **COMBOS[combo]}.items():
            if not hasattr(S, k):
                raise SystemExit(f"{combo}: engine has no knob {k!r}")
            setattr(S, k, v)
        S.V32_DATA_DIR = BASKET
        start, end = WINDOWS[win]
        print(f"\n##### v38 combo={combo} {win} {start}..{end} #####",
              flush=True)
        show = {k: v for k, v in COMBOS[combo].items()}
        print("    overrides: " + (json.dumps(show, default=str) or "-"),
              flush=True)
        t0 = time.time()
        run = S.run_backtest(S.v34_data_dir(), start, end,
                             tag=f"v38{combo}{win}")
        secs = time.time() - t0

        tr = pd.DataFrame(run["trades"])
        res = {"arm": combo, "window": win, "start": start, "end": end,
               "seconds": round(secs, 1), "n": int(len(tr)),
               "capital": float(S.CAPITAL)}
        if len(tr):
            tr["net_pnl"] = tr.net_pnl.astype(float)
            tr["R"] = tr.R.astype(float)
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
                monthly=monthly(tr, float(S.CAPITAL)),
            )
            res["months_pos"] = sum(1 for m in res["monthly"].values()
                                    if m["net$"] > 0)
            res["months_n"] = len(res["monthly"])
            eq = run["equity"]
            if len(eq):
                e = eq["equity"].astype(float)
                peak = e.cummax()
                res["maxDD_pct"] = round(float(
                    ((e - peak) / peak).min() * 100.0), 3)
        if save:
            (RESULTS / f"lab_v38_{combo}_{win}.json").write_text(
                json.dumps(res, indent=1, default=str))
            if len(tr):
                tr.to_csv(RESULTS / f"trades_v38_{combo}_{win}.csv",
                          index=False)
        print(f"    n={res['n']} end=${res['end_equity']:.4f} "
              f"PF={res.get('pf')} DD={res.get('maxDD_pct')}% "
              f"mo+={res.get('months_pos')}/{res.get('months_n')} "
              f"({res['seconds']}s)", flush=True)
        return res
    finally:
        _restore(S, pre)          # NO STATE LEAKS BETWEEN ARMS
        for k, v in {**_V38_KNOBS, **_V37_KNOBS}.items():
            if getattr(S, k) != v:
                raise SystemExit(
                    f"STATE LEAK after {combo}/{win}: "
                    f"{k}={getattr(S, k)!r}, expected {v!r}")
        if S.CAPITAL != pre["CAPITAL"]:
            raise SystemExit("STATE LEAK: CAPITAL")


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "arms"
    if cmd == "arms":
        for k, v in COMBOS.items():
            print(f"  {k:18s} {v or '(shipped B0)'}")
        return
    if cmd == "run":
        arm = sys.argv[2]
        win = "W1"
        if "--window" in sys.argv:
            win = sys.argv[sys.argv.index("--window") + 1]
        drive(arm, win)
        return
    if cmd == "matrix":
        arms = [a for a in COMBOS if a != "B0"] if "--all" in sys.argv \
            else [sys.argv[2]] if len(sys.argv) > 2 and \
            sys.argv[2] in COMBOS else ["TRAIL_1H"]
        wins = ["W1", "W2", "FULL15", "OLD7", "MOD_Y1", "MOD_Y2"]
        for a in arms:
            for w in wins:
                drive(a, w)
        return
    if cmd == "report":
        print(f"{'arm':18s}{'window':10s}{'n':>6s}{'end$':>10s}"
              f"{'PF':>7s}{'DD%':>8s}{'mo+':>7s}{'net-top3':>10s}")
        for f in sorted(RESULTS.glob("lab_v38_*_*.json")):
            j = json.loads(f.read_text())
            print(f"{j['arm']:18s}{j['window']:10s}{j['n']:>6d}"
                  f"{j.get('end_equity', 0):>10.2f}"
                  f"{(j.get('pf') or 0):>7.2f}"
                  f"{j.get('maxDD_pct', 0):>8.2f}"
                  f"{j.get('months_pos', 0)}/{j.get('months_n', 0):<4d}"
                  f"{j.get('net_minus_top3', 0):>10.2f}")
        return
    raise SystemExit(f"unknown command {cmd!r}")


if __name__ == "__main__":
    main()
