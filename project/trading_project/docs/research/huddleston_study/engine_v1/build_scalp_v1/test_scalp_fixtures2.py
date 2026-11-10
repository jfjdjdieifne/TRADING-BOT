#!/usr/bin/env python3
"""Frozen fixtures 2: the pattern, the plan, the path and the control.  Failures are recorded."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import scalp_core as C
import scalp_run as R

UTC = timezone.utc
CHECKS = 0
FAILS: list[str] = []


def check(name, ok, detail=""):
    global CHECKS
    CHECKS += 1
    if not ok:
        FAILS.append(f"{name}: {detail}")


PAD = 45
FLAT = [1.1040, 1.1050, 1.1030, 1.1040]


def as_dicts(rows):
    out = []
    for i, row in enumerate(rows):
        o, h, l, c = row
        out.append({"start": datetime(2021, 10, 1, tzinfo=UTC) + timedelta(minutes=15 * i),
                    "end": datetime(2021, 10, 1, tzinfo=UTC) + timedelta(minutes=15 * (i + 1)),
                    "open": o, "high": h, "low": l, "close": c, "ask_close": c + 0.00004,
                    "spread_open": 0.00004, "first_bar": i * 3, "last_bar": i * 3 + 2})
    return out


def load_specs():
    """Fixtures 2 plus the numbered supersessions in fixtures 3 (fixtures 2 are never edited)."""

    base = json.loads((HERE / "EXPECTED_SCALP_FIXTURES_2.json").read_text())
    extra = json.loads((HERE / "EXPECTED_SCALP_FIXTURES_3.json").read_text())
    superseded = {c["supersedes"] for c in extra["cases"]}
    cases = {c["id"]: c for c in base["cases"] if c["id"] not in superseded}
    cases.update({c["id"]: c for c in extra["cases"]})
    return base, cases, superseded


def build(case, extra=None):
    spec = json.loads((HERE / "EXPECTED_SCALP_FIXTURES_2.json").read_text())
    base = [list(c) for c in spec["base_structure"]["candles"]]
    if "candle_5" in case:
        base[5] = case["candle_5"]
    if extra is None:
        extra = case.get("candles_extra", {})
    for key, value in extra.items():
        base[int(key)] = value
    rows = [FLAT] * PAD + base
    return as_dicts(rows), spec


def main():
    spec, cases, superseded = load_specs()
    check("fixtures3.supersede_count", len(superseded) == 2, str(sorted(superseded)))

    # fvg_yes / fvg_no / h_below_half
    for cid, expect in (("fvg_yes", (1, True)), ("fvg_no", (2, False))):
        candles, _ = build(cases[cid])
        found = C.events(candles, variant="1A")
        check(f"{cid}.count", len(found) == 1, str(len(found)))
        if found:
            check(f"{cid}.form", found[0]["form"] == expect[0], str(found[0]["form"]))
            check(f"{cid}.fvg", found[0]["fvg"] == expect[1], str(found[0]["fvg"]))
            check(f"{cid}.h_index", found[0]["h_index"] == PAD + 5, str(found[0]["h_index"]))
    candles, _ = build(cases["h_below_half"])
    check("h_below_half.rejected", len(C.events(candles, variant="1A")) == 0)

    # 1B cases
    for cid in ("variant_1B_fixed", "fvg_in_1B_fixed"):
        candles, _ = build(cases[cid])
        found = C.events(candles, variant="1B")
        exp = cases[cid]["expected"]
        check(f"{cid}.valid", (len(found) == 1) == exp["valid"], str(len(found)))
        if found and exp["valid"]:
            check(f"{cid}.h_index", found[0]["h_index"] == PAD + exp["h_index"], str(found[0]["h_index"]))
            check(f"{cid}.fvg", found[0]["fvg"] == exp["fvg"], str(found[0]["fvg"]))

    # windows
    candles_5, _ = build(cases["fvg_no"])
    found3 = C.events(candles_5, window=C.WINDOW_PRIMARY)
    found2 = C.events(candles_5, window=C.WINDOW_SECONDARY)
    check("window.h_at_S+1.primary", len(found3) == 1)
    check("window.h_at_S+1.secondary", len(found2) == 1)
    late = [list(c) for c in spec["base_structure"]["candles"]]
    late[5] = [1.10300, 1.10350, 1.10250, 1.10340]     # bullish, cannot be H
    late[6] = [1.10340, 1.10700, 1.10290, 1.10660]     # R at S+2: bullish, range 0.0041 > P80 of the 20 before it
    late[7] = [1.10660, 1.10680, 1.10510, 1.10550]     # H at S+3: bearish, low 1.10510 above the half level 1.10495
    rows = [FLAT] * PAD + late
    candles_late = as_dicts(rows)
    check("window.h_at_S+3.primary", len(C.events(candles_late, window=C.WINDOW_PRIMARY)) == 1)
    check("window.h_at_S+3.secondary", len(C.events(candles_late, window=C.WINDOW_SECONDARY)) == 0)

    # R equals S
    candles, _ = build(cases["fvg_no"])
    found = C.events(candles, variant="1A")
    check("R_equals_S", bool(found) and found[0]["r_index"] == found[0]["s_index"], "R must be S itself")

    # target behind
    for case in cases["target_behind"]["cases"]:
        got = C.target_state(case["entry"], case["target"])
        check(f"target.{case['target']}", got == case["expected"], got)

    # side correctness
    side = cases["side_correct"]
    entry = side["entry_bar"]["ask_close"]
    buffer_price = C.BUFFER_FRACTION * entry
    stop = side["h_low"] - buffer_price
    target = side["target_before_buffer"] - buffer_price
    exp = side["expected"]
    check("side.entry", abs(entry - exp["entry"]) < 1e-12, str(entry))
    check("side.buffer", abs(buffer_price - exp["buffer"]) < 1e-12, str(buffer_price))
    check("side.stop", abs(stop - exp["stop"]) < 1e-12, str(stop))
    check("side.target", abs(target - exp["target"]) < 1e-12, str(target))
    check("side.rr", abs((target - entry) / (entry - stop) - exp["rr"]) < 1e-12, "")
    plan = {"entry": entry, "stop": stop, "target": target, "entry_index_5m": 0}

    # path ordering
    path = cases["path_ordering"]
    class FakeBar:
        def __init__(self, bid):
            self.bid_open, self.bid_high, self.bid_low, self.bid_close = bid
    bars = [FakeBar(b["bid"]) for b in path["bars"]]
    out = C.simulate({**plan, "stop": path["stop"], "target": path["target"],
                      "entry": path["entry"], "entry_index_5m": 1}, bars)
    check("path.reason", out["exit_reason"] == path["expected"]["exit_reason"], out["exit_reason"])
    check("path.ambiguous", out["ambiguous_bars"] == path["expected"]["ambiguous_bars"], str(out["ambiguous_bars"]))
    check("path.r", abs(out["r"] - path["expected"]["r"]) < 1e-9, str(out["r"]))

    # truncation: the plan at H must not change when later candles are removed
    candles, _ = build(cases["fvg_no"])
    full = C.events(candles, variant="1A")
    cut = candles[:PAD + 6]
    trunc = C.events(cut, variant="1A")
    check("truncation.identical",
          bool(full) and bool(trunc) and
          (full[0]["r_index"], full[0]["h_index"], full[0]["form"]) ==
          (trunc[0]["r_index"], trunc[0]["h_index"], trunc[0]["form"]),
          f"{full[:1]} vs {trunc[:1]}")

    # hour-matched control
    hours = []
    for i in range(96 * 10):
        row = {"start": datetime(2021, 10, 4, tzinfo=UTC) + timedelta(minutes=15 * i),
               "end": datetime(2021, 10, 4, tzinfo=UTC) + timedelta(minutes=15 * (i + 1)),
               "open": 1.1, "high": 1.101, "low": 1.099, "close": 1.1005, "ask_close": 1.10054,
               "spread_open": 0.00004, "first_bar": i * 3, "last_bar": i * 3 + 2}
        hours.append(row)
    event = {"h_index": 20, "s_index": 18}
    import random
    draws = R.control_draws(hours, event, {"risk": 0.001, "target": 1.102, "rr": 2.0},
                            random.Random(20261109), n_bars=96 * 10 * 3)
    ev_hour = C.ny_hour(hours[20]["start"])
    check("control.count", len(draws) == C.M_CONTROL, str(len(draws)))
    check("control.same_hour", all(d["hour"] == ev_hour for d in draws))
    check("control.outside_zone",
          all(abs((d["matched_candle"]["start"] - hours[18]["start"]).total_seconds()) > 2 * 3600
              for d in draws))

    print(f"checks: {CHECKS}")
    print(f"failures: {len(FAILS)}")
    for item in FAILS:
        print("  FAIL", item)
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()

# What this does NOT establish: it does not establish strategy validity or profitability.
