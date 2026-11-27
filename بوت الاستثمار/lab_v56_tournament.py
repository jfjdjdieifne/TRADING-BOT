#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lab_v56_tournament.py -- Gate1 W1+OLD7+MOD_Y2, Gate2 survivors->W2+MOD_Y1.
USAGE: gate1 | gate2 <modes csv>. Single process, resumable."""
from __future__ import annotations
import sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import strategy_v36_ict_champion as S
import lab_v50_tournament as T

ENG = T.RES / "v56_engine"; ENG.mkdir(parents=True, exist_ok=True)
T.ENG = ENG
T.REP.render = lambda: None

MODES = {"m5_base": "off", "h1_harvest": "h1_harvest", "h2_asym": "h2_asym",
         "h3_cisd": "h3_cisd", "h4_s3harvest": "h4_s3harvest", "h5_master": "h5_master"}
ARMS = ["h1_harvest", "h2_asym", "h3_cisd", "h4_s3harvest", "h5_master"]
for n in MODES: T.V50_SPEC[n] = ("p1_knife", -0.25)

_orig = T.apply
def apply56(mode, bps):
    _orig(mode, bps)
    S.V52_MODE = "m5_kz"; S.V52_DEPTH = 0.35
    S.V53_MODE = "off"; S.V54_MODE = "off"; S.V55_MODE = "off"
    S.V56_MODE = MODES[mode]
    S.V56_PROFIT_FLOOR = 0.0050; S.V56_UNFREEZE_H = 24.0
T.apply = apply56

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
        v = [net(m, w) for w in ("W1", "OLD7", "MOD_Y2")]
        if None not in v: scored.append((m, round(sum(v), 2)))
    passed = [m for m, s in scored if s > 128.49]
    surv = list(dict.fromkeys(passed + [m for m, _ in sorted(scored, key=lambda x: -x[1])[:3]]))[:max(3, len(passed))]
    print("GATE1:", scored, "-> survivors:", surv, flush=True)
    return surv

def main():
    t0 = time.time()
    what = sys.argv[1] if len(sys.argv) > 1 else "gate1"
    if what == "gate1":
        run(["m5_base"] + ARMS, ["W1", "OLD7", "MOD_Y2"]); pick()
    elif what == "gate2":
        modes = sys.argv[2].split(",") if len(sys.argv) > 2 else pick()
        run(modes, ["W2", "MOD_Y1"])
    print(f"\nv56 {what} total {time.time()-t0:.0f}s"); return 0

if __name__ == "__main__": raise SystemExit(main())
