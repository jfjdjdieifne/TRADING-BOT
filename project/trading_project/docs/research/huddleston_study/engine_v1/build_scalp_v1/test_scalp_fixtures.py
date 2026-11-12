#!/usr/bin/env python3
"""Run the frozen S-candle fixtures.  A failure is recorded, never repaired here."""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import scalp_sweep as S

CHECKS = 0
FAILS: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    global CHECKS
    CHECKS += 1
    if not ok:
        FAILS.append(f"{name}: {detail}")


def main() -> None:
    spec = json.loads((HERE / "EXPECTED_SCALP_FIXTURES.json").read_text())
    for case in spec["cases"]:
        candles = S.as_candles(case["candles"])
        events = S.sweep_events(candles, "long")
        got = "S" if events else "NOT_S"
        check(f"{case['id']}.label", got == case["expected"], f"{got} vs {case['expected']}")
        if case["expected"] == "S":
            check(f"{case['id']}.index", bool(events) and events[0]["index"] == case["s_index"],
                  f"{events[0]['index'] if events else None}")
            if "swing_low" in case:
                check(f"{case['id']}.level",
                      bool(events) and abs(events[0]["swing_price"] - case["swing_low"]) < 1e-12,
                      f"{events[0]['swing_price'] if events else None}")
    # windows
    check("window.primary", S.entry_window(10, S.WINDOW_PRIMARY) == [11, 12, 13],
          str(S.entry_window(10, S.WINDOW_PRIMARY)))
    check("window.secondary", S.entry_window(10, S.WINDOW_SECONDARY) == [11, 12],
          str(S.entry_window(10, S.WINDOW_SECONDARY)))
    # causality: the sweep candle can never confirm the swing it sweeps
    candles = S.as_candles(spec["cases"][0]["candles"])
    events = S.sweep_events(candles, "long")
    check("causality.confirmed_before_S",
          all(e["swing_confirmed_at"] < e["index"] for e in events), str(events))
    # malformed candles raise
    try:
        S.as_candles([[1.1, 1.2, 1.15, 1.18]])
        check("malformed.raises", False, "no exception")
    except ValueError:
        check("malformed.raises", True)

    print(f"checks: {CHECKS}")
    print(f"failures: {len(FAILS)}")
    for item in FAILS:
        print("  FAIL", item)
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
