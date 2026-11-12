#!/usr/bin/env python3
"""Run the frozen V3 fixtures.  Prints checks/failures; a failure is recorded, never repaired here."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import v3_core as C

UTC = timezone.utc
EXPECTED = json.loads((HERE / "EXPECTED_V3_FIXTURES.json").read_text())
CHECKS = 0
FAILS: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    global CHECKS
    CHECKS += 1
    if not ok:
        FAILS.append(f"{name}: {detail}")


def bar(spec: dict, start: str):
    from stream_v1 import Bar
    bid_o, bid_h, bid_l, bid_c = spec["bid"]
    ask_o, ask_h, ask_l, ask_c = spec["ask"]
    sp = spec.get("spread_open", 0.0004)
    return Bar(start=datetime.fromisoformat(start), bid_open=bid_o, bid_high=bid_h, bid_low=bid_l,
               bid_close=bid_c, bid_volume=1.0, ask_open=ask_o, ask_high=ask_h, ask_low=ask_l,
               ask_close=ask_c, ask_volume=1.0, spread_open=sp, spread_open_pips=sp * 10000,
               spread_high=sp, spread_high_pips=sp * 10000, spread_low=sp, spread_low_pips=sp * 10000,
               spread_close=sp, spread_close_pips=sp * 10000)


def execution_case(name: str, spec: dict) -> None:
    plan = dict(spec["plan"])
    plan.setdefault("entry_mode", "limit")
    plan["t1"] = {"level": plan["t1"]}
    ex = C.Execution(plan)
    for offset, raw in enumerate(spec["bars"], start=1):
        ex.update(offset, bar(raw, f"2021-10-01T{offset:02d}:00:00+00:00"))
    return ex


def main() -> None:
    # H1
    ex = execution_case("H1", EXPECTED["hygiene"]["H1_side_correct"])
    want = EXPECTED["hygiene"]["H1_side_correct"]["expected"]
    check("H1.state", ex.state == want["state"], f"{ex.state}")
    check("H1.reason", ex.exit_reason == want["exit_reason"], f"{ex.exit_reason}")
    check("H1.r", ex.r_measured is not None and abs(ex.r_measured - want["r_measured"]) < 1e-9,
          f"{ex.r_measured}")

    # H2
    ex = execution_case("H2", EXPECTED["hygiene"]["H2_stale_cancel"])
    want = EXPECTED["hygiene"]["H2_stale_cancel"]["expected"]
    check("H2.state", ex.state == want["state"], f"{ex.state}")
    check("H2.reason", ex.exit_reason == want["exit_reason"], f"{ex.exit_reason}")

    # H7
    spec = EXPECTED["hygiene"]["H7_first_bar_after_arming"]
    plan = dict(spec["plan"]); plan.setdefault("entry_mode", "limit"); plan["t1"] = {"level": plan["t1"]}
    ex = C.Execution(plan)
    ex.update(0, bar(spec["bars"][0], "2021-10-01T00:00:00+00:00"))
    check("H7.armed", ex.state == "armed", f"{ex.state}")
    ex.update(1, bar(spec["bars"][0], "2021-10-01T00:05:00+00:00"))
    check("H7.filled_on_next_bar", ex.state == "filled", f"{ex.state}")

    # H4
    for case in EXPECTED["hygiene"]["H4_geometry_reject"]["cases"]:
        got = C.target_behind(case["entry"], case["t1"], case["direction"])
        check(f"H4.{case['direction']}.{case['entry']}", got == case["expected"], f"{got}")

    # H3
    spec = EXPECTED["hygiene"]["H3_pool_identity"]
    merged = C.merge_pools([dict(p, pool_id=f"p{i}", kind="k", formed_index=1) for i, p in enumerate(spec["pools"])])
    check("H3.merged_count", len(merged) == spec["expected_merged"], f"{len(merged)}")
    check("H3.frames_joined", any(m["frames"] == ["15m", "1h"] for m in merged), f"{[m['frames'] for m in merged]}")

    # D concept
    for case in EXPECTED["switches"]["D_concept"]["cases"]:
        got = C.d_new_answer(case["break"], case["gap"])
        check(f"D.{case['break']}.{case['gap']}", got == case["expected"], f"{got}")

    # L class
    spec = EXPECTED["switches"]["L_class"]
    for case in spec["cases"]:
        got = C.pool_class(case["level"], case["side"], spec["range"])
        check(f"L.{case['side']}.{case['level']}", got == case["expected"], f"{got}")

    # R states
    spec = EXPECTED["switches"]["R_leg_state"]
    for case in spec["cases"]:
        label, ratio = C.range_position(spec["range"], case["price"])
        check(f"R.{case['price']}.label", label == case["expected_label"], f"{label}")
        if "expected_ratio" in case:
            check(f"R.{case['price']}.ratio", ratio is not None and abs(ratio - case["expected_ratio"]) < 1e-9,
                  f"{ratio}")

    # Time
    for case in EXPECTED["time"]["cases"]:
        moment = datetime.fromisoformat(case["utc"])
        got = C.ny_bucket(moment)
        check(f"T.ny.{case['utc']}", got["ny_time"].strftime("%H:%M") == case["expected_ny"],
              got["ny_time"].strftime("%H:%M"))
        if "expected_day_key" in case:
            check(f"T.day.{case['utc']}", list(got["day_key"]) == case["expected_day_key"],
                  f"{list(got['day_key'])}")
    from stream_v1 import session_now
    for case in EXPECTED["time"]["session_window_in_utc"]:
        moment = datetime.fromisoformat(case["utc_start"])
        b = bar({"bid": [1.1, 1.1001, 1.0999, 1.1], "ask": [1.10004, 1.10014, 1.09994, 1.10004]},
                case["utc_start"])
        got = session_now(b)["in_window"]
        check(f"T.session.{case['utc_start']}", got == case["expected_in_window"], f"{got}")

    # Market entry (E)
    spec = EXPECTED["entry_market"]
    plan = dict(spec["plan"]); plan["entry_mode"] = "market"; plan["t1"] = {"level": plan["t1"]}
    ex = C.Execution(plan)
    for offset, raw in enumerate(spec["bars"], start=1):
        ex.update(offset, bar(raw, f"2021-10-01T{offset:02d}:00:00+00:00"))
    check("E.fill_index", ex.fill_index == spec["expected"]["fill_index_bar"], f"{ex.fill_index}")
    check("E.fill_price", ex.fill_price == spec["expected"]["fill_price"], f"{ex.fill_price}")

    print(f"checks: {CHECKS}")
    print(f"failures: {len(FAILS)}")
    for item in FAILS:
        print("  FAIL", item)
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
