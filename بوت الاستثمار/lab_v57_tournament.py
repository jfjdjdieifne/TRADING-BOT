#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lab_v57_tournament.py -- Gate1 W1+MOD_Y2 (pass >= +95), Gate2 rest.
USAGE: gate1 | gate2 <modes csv>. Single process, resumable."""
from __future__ import annotations
import sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import strategy_v36_ict_champion as S
import lab_v50_tournament as T

ENG = T.RES / "v57_engine"; ENG.mkdir(parents=True, exist_ok=True)
T.ENG = ENG
T.REP.render = lambda: None

MODES = {"m5_base": "off", "u1_stop_streak": "u1_stop_streak", "u2_oneshot": "u2_oneshot",
         "u3_milk": "u3_milk", "u4_subfloor": "u4_subfloor", "u5_machine": "u5_machine"}
ARMS = ["u1_stop_streak", "u2_oneshot", "u3_milk", "u4_subfloor", "u5_machine"]
for n in MODES: T.V50_SPEC[n] = ("p1_knife", -0.25)

_orig = T.apply
def apply57(mode, bps):
    _orig(mode, bps)
    S.V52_MODE = "m5_kz"; S.V52_DEPTH = 0.35
    S.V53_MODE = "off"; S.V54_MODE = "off"; S.V55_MODE = "off"; S.V56_MODE = "off"
    S.V57_MODE = MODES[mode]
T.apply = apply57

def run(modes, wins):
    for mode in modes:
        for win in wins:
            a, b = T.WINDOWS[win]
            T.run_cell(mode, win, 0, T.DEFAULT_DATA, a, b)

def pick():
    import json
    def net(m, w):
        p = ENG / f"{m}__{w}__0.json"
        return json.loads(p.read_text())["net"] if p.exists() else None
    scored = []
    for m in ARMS:
        v = [net(m, w) for w in ("W1", "MOD_Y2")]
        if None not in v: scored.append((m, round(sum(v), 2)))
    passed = [m for m, s in scored if s >= 95.0]
    surv = list(dict.fromkeys(passed + [m for m, _ in sorted(scored, key=lambda x: -x[1])[:2]]))
    print("GATE1:", scored, "-> survivors:", surv, flush=True)
    return surv

def main():
    t0 = time.time()
    what = sys.argv[1] if len(sys.argv) > 1 else "gate1"
    if what == "gate1":
        run(["m5_base"] + ARMS, ["W1", "MOD_Y2"]); pick()
    elif what == "gate2":
        modes = sys.argv[2].split(",") if len(sys.argv) > 2 else pick()
        run(modes, ["OLD7", "W2", "MOD_Y1"])
    print(f"\nv57 {what} total {time.time()-t0:.0f}s"); return 0

if __name__ == "__main__": raise SystemExit(main())
