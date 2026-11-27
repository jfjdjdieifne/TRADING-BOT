#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lab_v54_tournament.py -- v54 arms on m5_kz foundation. Single process."""
from __future__ import annotations
import sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import strategy_v36_ict_champion as S
import lab_v50_tournament as T

ENG = T.RES / "v54_engine"; ENG.mkdir(parents=True, exist_ok=True)
T.ENG = ENG
T.REP.render = lambda: None

MODES = {
    "m5_base": "off", "b1_mfloor": "b1_mfloor", "b2_min035": "b2_min035",
    "b3_inv": "b3_inv", "b4_deadband": "b4_deadband", "b5_streak": "b5_streak",
    "b6_seat": "b6_seat",
}
for name in MODES: T.V50_SPEC[name] = ("p1_knife", -0.25)

_orig = T.apply
def apply54(mode, bps):
    _orig(mode, bps)
    S.V52_MODE = "m5_kz"; S.V52_DEPTH = 0.35
    S.V53_MODE = "off"
    S.V54_MODE = MODES[mode]
    S.V54_MFLOOR = 0.0040; S.V54_BAND = 0.0035; S.V54_DEPTH = 0.35
T.apply = apply54

def main():
    modes = sys.argv[1].split(",") if len(sys.argv) > 1 else list(MODES)
    wins = sys.argv[2].split(",") if len(sys.argv) > 2 else ["W1", "MOD_Y2"]
    t0 = time.time()
    for mode in modes:
        for win in wins:
            a, b = T.WINDOWS[win]
            T.run_cell(mode, win, 0, T.DEFAULT_DATA, a, b)
    print(f"\nv54 total {time.time()-t0:.0f}s"); return 0

if __name__ == "__main__": raise SystemExit(main())
