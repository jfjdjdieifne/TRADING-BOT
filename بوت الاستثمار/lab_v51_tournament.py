#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lab_v51_tournament.py -- V51_P1_KNIFE (P1 -0.25x + bar-1 knife -0.65x).
Single process, resumable. Reuses lab_v50_tournament.run_cell machinery but
writes to results/v51_engine/ and never re-renders the v50 report.
USAGE: ../.venv/bin/python -u lab_v51_tournament.py run
"""
from __future__ import annotations
import sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import strategy_v36_ict_champion as S
import lab_v50_tournament as T

ENG = T.RES / "v51_engine"
ENG.mkdir(parents=True, exist_ok=True)
# register the combo arm: V50_MODE=p1_knife (knife guard), V50_X=-0.25 (P1 floor)
T.V50_SPEC["v51_p1_knife"] = ("p1_knife", -0.25)
T.ENG = ENG
# run_cell calls REP.render() (v50 report) -- harmless no-op guard
T.REP.render = lambda: None

def main():
    t0 = time.time()
    for win in ("W1", "MOD_Y2", "W2", "OLD7", "MOD_Y1"):
        a, b = T.WINDOWS[win]
        T.run_cell("v51_p1_knife", win, 0, T.DEFAULT_DATA, a, b)
    # jan months for the 4-runner check (only if the jan data dirs exist;
    # the runners also live inside the W1/MOD_Y2 window books)
    for win in ("jan24", "jan26"):
        dd, a, b = T.MONTHS[win]
        if (HERE / dd).exists():
            T.run_cell("v51_p1_knife", win, 0, dd, a, b)
    print(f"\nv51 total {time.time()-t0:.0f}s")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
