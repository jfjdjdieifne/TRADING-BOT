#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lab_v55_tournament.py -- cascading knockout. Single process, resumable.
USAGE: gate1 | gate2 <modes csv>
Gate1: OLD7+W1 @0bps for m5_base + s1..s5 (12 cells max, checkpointed).
Gate2: MOD_Y2,W2,MOD_Y1 @0bps for survivors only (causal 2bps is computed
analytically from the frozen 0bps books in the report, as in v51-v54)."""
from __future__ import annotations
import sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import strategy_v36_ict_champion as S
import lab_v50_tournament as T

ENG = T.RES / "v55_engine"; ENG.mkdir(parents=True, exist_ok=True)
T.ENG = ENG
T.REP.render = lambda: None

MODES = {"m5_base": "off", "s1_streak2": "s1_streak2", "s2_streak3": "s2_streak3",
         "s3_unfreeze": "s3_unfreeze", "s4_bull": "s4_bull", "s5_synergy": "s5_synergy"}
ARMS = ["s1_streak2", "s2_streak3", "s3_unfreeze", "s4_bull", "s5_synergy"]
for n in MODES: T.V50_SPEC[n] = ("p1_knife", -0.25)

_orig = T.apply
def apply55(mode, bps):
    _orig(mode, bps)
    S.V52_MODE = "m5_kz"; S.V52_DEPTH = 0.35
    S.V53_MODE = "off"; S.V54_MODE = "off"
    S.V55_MODE = MODES[mode]
    S.V55_DEPTH = 0.35; S.V55_UNFREEZE_H = 48.0
T.apply = apply55

def run(modes, wins):
    for mode in modes:
        for win in wins:
            a, b = T.WINDOWS[win]
            T.run_cell(mode, win, 0, T.DEFAULT_DATA, a, b)

def gate_pick():
    import json
    def net(m, w):
        p = ENG / f"{m}__{w}__0.json"
        return json.loads(p.read_text())["net"] if p.exists() else None
    scored = []
    for m in ARMS:
        o, w = net(m, "OLD7"), net(m, "W1")
        if o is None or w is None: continue
        scored.append((m, o, w, o + w))
    passed = [x for x in scored if x[1] > 0 and x[2] >= 65.0]
    pool = passed if passed else sorted(scored, key=lambda x: -x[3])
    surv = [x[0] for x in sorted(pool, key=lambda x: -x[3])[:2]]
    print("GATE1:", scored, "-> survivors:", surv, flush=True)
    return surv

def main():
    t0 = time.time()
    what = sys.argv[1] if len(sys.argv) > 1 else "gate1"
    if what == "gate1":
        run(["m5_base"] + ARMS, ["OLD7", "W1"])
        gate_pick()
    elif what == "gate2":
        modes = sys.argv[2].split(",") if len(sys.argv) > 2 else gate_pick()
        run(modes, ["MOD_Y2", "W2", "MOD_Y1"])
    print(f"\nv55 {what} total {time.time()-t0:.0f}s"); return 0

if __name__ == "__main__": raise SystemExit(main())
