#!/usr/bin/env python3
"""Sweep concept pack (declared before code) and loop-level isolation / memory-bound fixtures."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import v3_core as C
from stream_v1 import Bar, Window

UTC = timezone.utc
CHECKS = 0
FAILS: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    global CHECKS
    CHECKS += 1
    if not ok:
        FAILS.append(f"{name}: {detail}")


def mk(ohlc: list[tuple], start: str, spread: float = 0.0002) -> Bar:
    o, h, l, c = ohlc
    return Bar(start=datetime.fromisoformat(start), bid_open=o, bid_high=h, bid_low=l, bid_close=c,
               bid_volume=1.0, ask_open=o + spread, ask_high=h + spread, ask_low=l + spread,
               ask_close=c + spread, ask_volume=1.0, spread_open=spread,
               spread_open_pips=spread * 10000, spread_high=spread, spread_high_pips=spread * 10000,
               spread_low=spread, spread_low_pips=spread * 10000, spread_close=spread,
               spread_close_pips=spread * 10000)


SWEEP_CASES = {
    "sw01": ([(1.0980, 1.0990, 1.0975, 1.0985), (1.0985, 1.1020, 1.0980, 1.0990)], 1.1000, "high"),
    "sw02": ([(1.0980, 1.0990, 1.0975, 1.0985), (1.0985, 1.1020, 1.0980, 1.1008)], 1.1000, "high"),
    "sw03": ([(1.0980, 1.0990, 1.0975, 1.0985), (1.0985, 1.0999, 1.0980, 1.0990)], 1.1000, "high"),
    "sw04": ([(1.0980, 1.0990, 1.0975, 1.0985), (1.0985, 1.10001, 1.0980, 1.0995)], 1.1000, "high"),
    "sw05": ([(1.0980, 1.0990, 1.0975, 1.0985), (1.0985, 1.1005, 1.0980, 1.1003),
              (1.1003, 1.1008, 1.0990, 1.0996)], 1.1000, "high"),
    "sw06": ([(1.0980, 1.1000, 1.0975, 1.0990), (1.0990, 1.1002, 1.0985, 1.0998),
              (1.0998, 1.1005, 1.0990, 1.0997)], 1.1002, "high"),
}


def sweep_pack() -> None:
    expected = json.loads((HERE / "EXPECTED_V3_FIXTURES.json").read_text())["sweep_pack"]
    concept = expected["concept_map"]
    labels = {c["id"]: c["expected"] for c in expected["cases"]}
    for case_id, (candles, level, side) in SWEEP_CASES.items():
        window = Window(16)
        base = datetime(2021, 10, 1, tzinfo=UTC)
        for i, ohlc in enumerate(candles):
            window.push(mk(ohlc, (base + timedelta(minutes=15 * i)).isoformat()))
        got = C.sweep_now(window, side, level)
        want = concept[labels[case_id]]
        check(f"sweep.{case_id}.{labels[case_id]}", got.get("answer") == want,
              f"module={got.get('answer')} concept={labels[case_id]}")


def main() -> None:
    sweep_pack()

    # loop-level: determinism, isolation, memory-bound equivalence
    import run_v3
    out = Path("/tmp/v3fixtures")
    common = dict(month="2021-09", frame_label="15m")

    a = run_v3.run(variant="V3-0", out_dir=out / "iso_a", **common)
    b = run_v3.run(variant="V3-0", out_dir=out / "iso_b", **common)
    plans_a = [json.loads(x) for x in (out / "iso_a" / "plans_final.jsonl").read_text().splitlines()]
    plans_b = [json.loads(x) for x in (out / "iso_b" / "plans_final.jsonl").read_text().splitlines()]
    check("loop.deterministic", [p["plan_id"] for p in plans_a] == [p["plan_id"] for p in plans_b],
          f"{len(plans_a)} vs {len(plans_b)}")
    check("loop.deterministic_r", [p.get("r_measured") for p in plans_a] == [p.get("r_measured") for p in plans_b])

    lq = run_v3.run(variant="V3-L", out_dir=out / "iso_l", **common)
    plans_l = [json.loads(x) for x in (out / "iso_l" / "plans_final.jsonl").read_text().splitlines()]
    same_ids = [p["plan_id"] for p in plans_l] == [p["plan_id"] for p in plans_a]
    entries_same = all(abs(x["entry"] - y["entry"]) < 1e-12 for x, y in zip(plans_l, plans_a))
    stops_same = all(abs(x["stop"] - y["stop"]) < 1e-12 for x, y in zip(plans_l, plans_a))
    check("iso.L.same_plan_ids", same_ids)
    check("iso.L.same_entry", entries_same)
    check("iso.L.same_stop", stops_same)

    deep = run_v3.run(variant="V3-0", out_dir=out / "mem_deep", history_start="2021-01-01", **common)
    shallow = run_v3.run(variant="V3-0", out_dir=out / "mem_shallow", history_start="2021-08-01", **common)
    p_deep = [json.loads(x) for x in (out / "mem_deep" / "plans_final.jsonl").read_text().splitlines()]
    p_shallow = [json.loads(x) for x in (out / "mem_shallow" / "plans_final.jsonl").read_text().splitlines()]
    check("mem.decision_count_equal", deep["decisions"] == shallow["decisions"],
          f"{deep['decisions']} vs {shallow['decisions']}")
    # absolute indices are counted from the run's history start (declared: run-relative index space),
    # so equality is checked on the state the index is attached to, not on the index digits
    def signature(plan):
        return (plan["decided_at"], round(plan["entry"], 10), round(plan["stop"], 10),
                None if not plan.get("t1") else round(plan["t1"]["level"], 10), plan.get("r_measured"))
    check("mem.state_signature_equal", [signature(p) for p in p_deep] == [signature(p) for p in p_shallow],
          f"{len(p_deep)} vs {len(p_shallow)}")
    import re

    def tail(plan):
        found = re.findall(r"(\d+)$", plan["plan_id"])
        return int(found[0]) if found else None
    offsets = {tail(p) - tail(q) for p, q in zip(p_deep, p_shallow)
               if tail(p) is not None and tail(q) is not None}
    check("mem.constant_index_offset", len(offsets) == 1 or not offsets, f"{sorted(offsets)[:4]}")

    print(f"checks: {CHECKS}")
    print(f"failures: {len(FAILS)}")
    for item in FAILS:
        print("  FAIL", item)
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
