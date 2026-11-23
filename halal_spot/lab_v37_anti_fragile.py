#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lab_v37_anti_fragile.py -- the anti-fragile ICT lab.

Tests the v37 knobs across every window, and judges only by money:
net_$, end_eq, maxDD_pct, PF, winning/losing months. NEVER by totR (v36
proved totR is economically empty here: AVAX booked +147R while losing
$12.67, because a 0.13% stop makes $0.14 of risk look like 195R).

THE STATE GUARD
---------------
`_V37_KNOBS` is snapshotted before a run and restored after it, so no arm
can inherit the previous arm's values. This is the bug v33 shipped (an arm
printed as LEAD2 actually carried TEL's trail lens, because drive() only
setattr()s the keys a combo lists). Here every knob is explicitly reset to
its OFF value between arms, and the guard raises if a knob is left set.

ARMS
----
  B0            the v37 engine at defaults = the shipped v36 champion.
                Must reproduce $158.024 on W1, or the patch broke identity.
  RATCHET_*     POST_3R_RATCHET = 2R / 3R / 3R_TIGHT / LADDER_A / LADDER_B
  GATE_*        HTF_ENTRY_GATE   = 4H_BULL / 1H_BULL / BOTH_BULL
  CD_1H         COOLDOWN_BOS_TF  = "1h"
  FIXBE         FIX_BE_COOLDOWN_BUG = True
  best combos   the ratchet that wins + the gate that survives, together

USAGE
    python3 lab_v37_anti_fragile.py arms
    python3 lab_v37_anti_fragile.py run ARM --window W1
    python3 lab_v37_anti_fragile.py matrix            # the full grid
    python3 lab_v37_anti_fragile.py report
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
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
    "APR_MAY_24": ("2024-04-01", "2024-05-31"),
}

# ---- the v37 knobs, with their OFF value ----------------------------- #
_V37_KNOBS = {
    "POST_3R_RATCHET": "",
    "POST_3R_RATCHET_TF": "5min",
    "HTF_ENTRY_GATE": "",
    "COOLDOWN_BOS_TF": "",
    "FIX_BE_COOLDOWN_BUG": False,
    "EXIT_SLIPPAGE_BPS": 0.0,
}

# ---- the shipped champion, stated explicitly so an arm is readable --- #
SHIPPED = dict(
    # CAPITAL MUST BE STATED: the engine module's own default is 200.0, and
    # the shipped champion book is a $100 account. Leaving this out made B0
    # report end=$216.05 (200 + 116 net) instead of the $158.02 that the
    # n=181 / totR +227.8481 / DD -14.064% book actually earns. The other
    # numbers were already identical, which is what proved it was only the
    # capital base.
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
    "B0":            dict(),
    "RATCHET_2R":    dict(POST_3R_RATCHET="2R"),
    "RATCHET_3R":    dict(POST_3R_RATCHET="3R"),
    "RATCHET_3RT":   dict(POST_3R_RATCHET="3R_TIGHT"),
    "RATCHET_LAD_A": dict(POST_3R_RATCHET="LADDER_A"),
    "RATCHET_LAD_B": dict(POST_3R_RATCHET="LADDER_B"),
    "GATE_4H":       dict(HTF_ENTRY_GATE="4H_BULL"),
    "GATE_1H":       dict(HTF_ENTRY_GATE="1H_BULL"),
    "GATE_BOTH":     dict(HTF_ENTRY_GATE="BOTH_BULL"),
    "CD_1H":         dict(COOLDOWN_BOS_TF="1h"),
    "FIXBE":         dict(FIX_BE_COOLDOWN_BUG=True),
    "BEST_RATCHET":  dict(POST_3R_RATCHET="__best__"),
    "BEST_RATCHET_GATE": dict(POST_3R_RATCHET="__best__",
                              HTF_ENTRY_GATE="4H_BULL"),
}
ORDER = list(COMBOS)


def _snapshot(S) -> dict:
    return {k: getattr(S, k) for k in _V37_KNOBS}


def _restore(S, snap: dict) -> None:
    for k, v in snap.items():
        setattr(S, k, v)


def drive(combo: str, win: str, save: bool = True) -> dict:
    import strategy_v36_ict_champion as S

    if combo not in COMBOS:
        raise SystemExit(f"unknown combo {combo!r} would silently run defaults")
    pre = _snapshot(S)
    try:
        for k, v in _V37_KNOBS.items():          # hard reset to OFF
            setattr(S, k, v)
        arm = COMBOS[combo]
        if "__best__" in arm.values():
            best = json.loads((RESULTS / "_v37_best_ratchet.json").read_text())
            arm = dict(arm)
            arm["POST_3R_RATCHET"] = best["name"]
        for k, v in {**SHIPPED, **arm}.items():
            if not hasattr(S, k):
                raise SystemExit(f"combo {combo}: engine has no knob {k!r}")
            setattr(S, k, v)
        S.V32_DATA_DIR = BASKET
        start, end = WINDOWS[win]
        print(f"\n##### v37 combo={combo} {win} {start}..{end} #####", flush=True)
        show = {k: v for k, v in {**SHIPPED, **arm}.items() if v != SHIPPED.get(k)}
        print("    overrides: " + (json.dumps(show, default=str) or "-"), flush=True)
        t0 = time.time()
        run = S.run_backtest(S.v34_data_dir(), start, end, tag=f"v37{combo}{win}")
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
            res.update(
                totR=round(float(tr.R.sum()), 4),
                net=round(float(tr.net_pnl.sum()), 4),
                end_equity=round(100.0 + float(tr.net_pnl.sum()), 4),
                pf=round(gp / gl, 3) if gl > 1e-9 else None,
                wr=round(100.0 * cls.isin(["WIN", "SWIN"]).mean(), 2),
                wins=int(cls.isin(["WIN", "SWIN"]).sum()),
                be=int(cls.isin(["BE", "BREAKEVEN"]).sum()),
                losses=int((cls == "LOSS").sum()),
                fees=round(float(run["fees"]), 4),
                by_coin={k: [len(g), round(float(g.net_pnl.sum()), 3)]
                         for k, g in tr.groupby("symbol")},
                exits=tr.exit_reason.value_counts().to_dict(),
                monthly=monthly(tr, float(S.CAPITAL)),
            )
            res["months_pos"] = sum(1 for m in res["monthly"].values() if m["net$"] > 0)
            res["months_n"] = len(res["monthly"])
        eq = run["equity"]
        if len(eq):
            e = eq["equity"].astype(float)
            res["maxDD_pct"] = round(float(((e / e.cummax()) - 1).min() * 100), 3)
            res["eq_end"] = round(float(e.iloc[-1]), 4)
        res["counters"] = {k: int(v) for k, v in run["count"].items()
                           if ("v37" in k or "cooldown" in k)}
        print(f"    n={res['n']} end=${res.get('end_equity')} "
              f"PF={res.get('pf')} DD={res.get('maxDD_pct')}% "
              f"mo+={res.get('months_pos')}/{res.get('months_n')} ({secs:.0f}s)",
              flush=True)
        if save:
            (RESULTS / f"lab_v37_{combo}_{win}.json").write_text(
                json.dumps(res, indent=1, default=str))
            if len(tr):
                tr.to_csv(RESULTS / f"trades_v37_{combo}_{win}.csv", index=False)
    finally:
        _restore(S, pre)
        leak = {k: (v, getattr(S, k)) for k, v in _V37_KNOBS.items()
                if getattr(S, k) != pre[k]}
        if leak:                     # the v33 lesson, enforced
            raise SystemExit(f"STATE LEAK after {combo}/{win}: {leak}")
    return res


def monthly(tr: pd.DataFrame, cap: float) -> dict:
    tr = tr.copy()
    tr["ym"] = pd.to_datetime(tr.exit_time, utc=True,
                              format="mixed").dt.strftime("%Y-%m")
    out, bal = {}, cap
    for ym, g in tr.groupby("ym"):
        bal += float(g.net_pnl.sum())
        gp = float(g.loc[g.net_pnl > 0, "net_pnl"].sum())
        gl = float(-g.loc[g.net_pnl < 0, "net_pnl"].sum())
        out[ym] = {"net$": round(float(g.net_pnl.sum()), 2),
                   "end$": round(bal, 2), "n": int(len(g)),
                   "PF": round(gp / gl, 2) if gl > 1e-9 else None}
    return out


def report() -> int:
    W = 118
    print("\n" + "=" * W)
    print("v37 ANTI-FRAGILE LAB -- money only (totR is shown for continuity, never used)")
    print("=" * W)
    hdr = (f"{'arm':18s}" + "".join(f"{w:>17s}" for w in
                                    ("W1", "W2", "FULL15", "OLD7", "MOD_Y1", "MOD_Y2")))
    print(hdr)
    print(f"{'':18s}" + "".join(f"{'end$ / mo+':>17s}" for _ in range(6)))
    rows = []
    for arm in ORDER:
        cells, ok = [], True
        for w in ("W1", "W2", "FULL15", "OLD7", "MOD_Y1", "MOD_Y2"):
            f = RESULTS / f"lab_v37_{arm}_{w}.json"
            if not f.exists():
                cells.append(f"{'-':>17s}")
                ok = False
                continue
            j = json.loads(f.read_text())
            cells.append(f"{j.get('end_equity'):>10.2f} {j.get('months_pos')}/{j.get('months_n'):<2}")
        line = f"{arm:18s}" + "".join(cells)
        print(line)
        if ok:
            rows.append(arm)
    if rows:
        print("\n  PF / maxDD% per arm (MOD_Y2 = the most recent live regime):")
        for arm in rows:
            j = json.loads((RESULTS / f"lab_v37_{arm}_MOD_Y2.json").read_text())
            print(f"    {arm:18s} PF {j.get('pf')}  DD {j.get('maxDD_pct')}%  "
                  f"net {j.get('net')}  fees {j.get('fees')}")
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    cmd = sys.argv[1]
    if cmd == "arms":
        for k, v in COMBOS.items():
            print(f"{k:20s} {json.dumps(v, default=str)}")
        return 0
    if cmd == "run":
        wins = ["W1"]
        if "--window" in sys.argv:
            wins = [sys.argv[sys.argv.index("--window") + 1]]
        elif "--all-windows" in sys.argv:
            wins = list(WINDOWS)
        args = [a for a in sys.argv[2:] if not a.startswith("--") and a not in wins]
        for combo in args or ["B0"]:
            for w in wins:
                drive(combo, w)
        return 0
    if cmd == "matrix":
        arms = [a for a in ORDER if a not in ("BEST_RATCHET", "BEST_RATCHET_GATE")]
        for w in ("W1", "W2", "FULL15", "OLD7", "MOD_Y1", "MOD_Y2"):
            for a in arms:
                drive(a, w)
        return 0
    if cmd == "report":
        return report()
    raise SystemExit(f"unknown command {cmd!r}")


if __name__ == "__main__":
    raise SystemExit(main())
