#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lab_v53_tournament.py -- v53 arms on the m5_kz foundation (V51 + Sat block).
Single process, resumable, writes results/v53_engine/.
USAGE: run <modes csv> <wins csv>
"""
from __future__ import annotations
import sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import strategy_v36_ict_champion as S
import lab_v50_tournament as T

ENG = T.RES / "v53_engine"
ENG.mkdir(parents=True, exist_ok=True)
T.ENG = ENG
T.REP.render = lambda: None

# mode -> (V53_MODE, V50_MODE)
MODES = {
    "m5_base":  ("off",          "p1_knife"),
    "a1_cap":   ("a1_cap",       "p1_knife"),
    "a2_adapt": ("a2_adapt",     "p1_knife"),
    "a3_shield": ("a3_shieldote", "p1_knife"),
    "a4_reentry": ("off",        "s2_reentry"),
    "a5_wknd":  ("a5_wknd",      "p1_knife"),
    "a6_combo": ("a6_combo",     "p1_knife"),
}
for name in MODES:
    T.V50_SPEC[name] = (MODES[name][1], -0.25)

_orig_apply = T.apply
def apply53(mode, bps):
    _orig_apply(mode, bps)
    S.V52_MODE = "m5_kz"          # Saturday-block foundation for every arm
    S.V52_DEPTH = 0.35
    S.V53_MODE = MODES[mode][0]
    S.V53_MAX_RISK = 0.0100
    S.V53_T_TIGHT = 0.0055
    S.V53_DEPTH = 0.35
T.apply = apply53

def main():
    modes = sys.argv[1].split(",") if len(sys.argv) > 1 else list(MODES)
    wins = sys.argv[2].split(",") if len(sys.argv) > 2 else ["W1", "MOD_Y2"]
    t0 = time.time()
    for mode in modes:
        for win in wins:
            a, b = T.WINDOWS[win]
            T.run_cell(mode, win, 0, T.DEFAULT_DATA, a, b)
    print(f"\nv53 total {time.time()-t0:.0f}s")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
