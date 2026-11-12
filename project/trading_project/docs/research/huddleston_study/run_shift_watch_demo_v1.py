#!/usr/bin/env python3
"""Runnable example — E03-A/B slice: reference-crossing shift-watch.

SYNTHETIC scene (labeled synthetic; NOT market data, NOT a trade).
Sequence demonstrated:
  1. a confirmed swing low reference exists (engine's F-K points);
  2. a DOWNWARD close-to-close transition across that level opens a
     shift-watch — "a context for WATCHING a possible shift, not proof
     of one" (E03-A);
  3. the watch's questions are recorded (E03-B): closed-bar
     displacement/non-overlap, local-swing crossing, and "do NOT assume
     a reversal/trade after a raid";
  4. a non-overlap closed bar and later a local-swing crossing are
     recorded as EVIDENCE ONLY — there is no 'shift confirmed' state
     and no reversal/trade signal anywhere.

Run:
  python run_shift_watch_demo_v1.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
PROJECT_SRC = HERE.parents[1] / "project" / "trading_project" / "src"
if not PROJECT_SRC.exists():
    PROJECT_SRC = HERE.parents[2] / "src"
sys.path.insert(0, str(PROJECT_SRC))

from trading_system.research.contextual_selection.csm import (  # noqa: E402
    InterpretationLedger,
)
from trading_system.research.contextual_selection.study_links import (  # noqa: E402
    SHIFT_QUESTIONS,
    SHIFT_STATUSES,
    StudyReasoningLayer,
)


class _Interp:
    interpretation_id = "I-primary"
    data = {"direction": "up"}
    state = "PLAUSIBLE"


class _Rec:
    def __init__(self, as_of_bar, as_of_time):
        self.as_of_bar = as_of_bar
        self.as_of_time = as_of_time
        self.interpretations = [_Interp()]
        self.structural_facts = []


SCENE = [
    (0, 110.0, 110.5, 108.0, 108.5),
    (1, 108.5, 109.0, 105.0, 105.5),
    (2, 105.5, 106.0, 101.0, 101.5),
    (3, 101.5, 102.0, 100.0, 101.0),    # swing low 100.0
    (4, 101.0, 104.0, 100.8, 103.5),
    (5, 103.5, 106.5, 103.0, 106.0),
    (6, 106.0, 108.5, 105.5, 108.0),
    (7, 108.0, 111.5, 107.5, 111.0),    # local swing high 111.5
    (8, 111.0, 111.5, 107.0, 107.5),
    (9, 107.5, 108.0, 103.5, 104.0),
    (10, 104.0, 104.5, 100.5, 101.0),
    (11, 101.0, 101.2, 99.0, 99.5),     # close-through 100 (downward)
    (12, 98.8, 98.9, 97.5, 98.0),       # non-overlap displacement
    (13, 98.0, 100.0, 97.8, 99.8),
    (14, 99.8, 112.5, 99.5, 112.0),     # local-swing crossing 111.5
]


def main() -> int:
    idx = pd.date_range("2025-09-01 04:00", periods=len(SCENE), freq="4h",
                        tz="UTC")
    bars = pd.DataFrame(
        [{"open": o, "high": h, "low": lo, "close": c, "volume": 1.0}
         for (_, o, h, lo, c) in SCENE], index=idx)
    layer = StudyReasoningLayer(run_id="shift-demo", k=2, task_scale="4h")
    ledger = InterpretationLedger()

    print("== E03 shift-watch demo (SYNTHETIC scene; not market data) ==")
    for j in range(len(SCENE)):
        rec = _Rec(j, pd.Timestamp(bars.index[j]))
        changes = layer.on_boundary(rec, {"4h": bars}, ledger)
        for ch in changes:
            if ch.get("aspect") == "shift_watch":
                print(f"[bar {j:2d} {bars.index[j]}] {ch['before']} -> "
                      f"{ch['after']}: {ch['reason']}")

    assert layer.shift_watches, "the crossing must open a watch"
    w = layer.shift_watches[0]
    print(f"\nwatch {w.watch_id}: status={w.status} "
          f"(allowed: {list(SHIFT_STATUSES)})")
    print(f"crossing: {w.crossing['direction']} through "
          f"{w.crossing['ref_level']} at bar {w.crossing['bar']} "
          f"({w.crossing['bar_time']})")
    print(f"transition: {w.crossing['transition']}")
    print("questions recorded at open:")
    for q in w.questions:
        print(f"  - {q}")
    print("evidence (append-only; each is 'evidence only' — never "
          "proof of a shift):")
    for e in w.evidence:
        print(f"  - {e['kind']} at bar {e['at_bar']} ({e['at']}): "
              f"{e['note']}")
    print("\nHONESTY: no 'shift confirmed' state exists; no reversal "
          "or trade signal is generated; the intrabar path across the "
          "level is NOT established by completed bars.")
    print("selection_quality = NOT_ESTABLISHED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
