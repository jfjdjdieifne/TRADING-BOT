#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lab_v52_ict_fullstack.py -- v52 tournament inside the Investment Bot copy.
Single process, resumable. Foundation = V51 (V50_MODE=p1_knife, X=-0.25),
except m4_tap2 which uses the v50 S2 re-entry machinery at X=-0.25.
JAN24/JAN26 standalone data dirs no longer exist, so the Stage-2 screen is
W1 (contains 2024-01) + MOD_Y2 (contains 2026-01); jan months are reported
from those books. USAGE: run <mode,mode> <win,win> | all
"""
from __future__ import annotations
import sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import strategy_v36_ict_champion as S
import lab_v50_tournament as T

ENG = T.RES / "v52_engine"
ENG.mkdir(parents=True, exist_ok=True)
T.ENG = ENG
T.REP.render = lambda: None

MODES = {
    "v51_base":  ("off",      "p1_knife"),
    "m1_depth":  ("m1_depth", "p1_knife"),
    "m2_cisd":   ("m2_cisd",  "p1_knife"),
    "m3_dol":    ("m3_dol",   "p1_knife"),
    "m4_tap2":   ("off",      "s2_reentry"),
    "m5_kz":     ("m5_kz",    "p1_knife"),
    "m6_full":   ("m6_full",  "p1_knife"),
    "m7_depth_kz": ("m7_depth_kz", "p1_knife"),
}
for name in MODES:
    T.V50_SPEC[name] = (MODES[name][1], -0.25)

_orig_apply = T.apply
def apply52(mode, bps):
    _orig_apply(mode, bps)
    S.V52_MODE = MODES[mode][0]
    S.V52_DEPTH = 0.35
T.apply = apply52

def main():
    modes = sys.argv[1].split(",") if len(sys.argv) > 1 else list(MODES)
    wins = sys.argv[2].split(",") if len(sys.argv) > 2 else ["W1", "MOD_Y2"]
    t0 = time.time()
    for mode in modes:
        for win in wins:
            a, b = T.WINDOWS[win]
            T.run_cell(mode, win, 0, T.DEFAULT_DATA, a, b)
    print(f"\nv52 {'/'.join(modes)} total {time.time()-t0:.0f}s")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
