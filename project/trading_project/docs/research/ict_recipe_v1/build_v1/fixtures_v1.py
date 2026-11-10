#!/usr/bin/env python3
"""Hand-made candle fixtures, frozen expected files, and the memory-bound proof.

Two modes:

    python3 fixtures_v1.py --freeze   # write EXPECTED_*.json (done once; a human reviews the numbers)
    python3 fixtures_v1.py --check    # compare against the frozen files; never edits them

An EXPECTED file is never edited after a failure.  A mismatch is printed with both values and the
exit code is non-zero; the report carries the mismatch, not a repaired fixture.

Coverage (the brief's list):
  * bullish dealing range with price in premium
  * bearish dealing range with price in discount
  * price exactly at equilibrium
  * an untaken pool and a taken pool
  * a sweep followed by displacement
  * a sweep with no displacement
  * a structure shift
  * an FVG respected and an FVG closed through
  * three candidate FVGs where ranking must pick one, with reasons
  * a plan with T1 and T2
  * a plan with only T1 (T2 = None)
  * a no-plan case with the reason
  * the memory bound (state at t identical with and without older history)
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from plan_v1 import build_plan, gates, gather_zones, rank_zones, targets_ahead
from stream_v1 import (
    Bar,
    DealingRangeState,
    GapState,
    LiquidityState,
    OrderBlockState,
    SwingState,
    Window,
    displacement_now,
    fvg_now,
    structure_shift,
    sweep_now,
    swing_now,
)

UTC = timezone.utc
HERE = Path(__file__).resolve().parent
EXPECTED = HERE / "EXPECTED"
START = datetime(2021, 1, 4, 0, 0, tzinfo=UTC)   # a Monday, 00:00 UTC


def bar(i: int, o: float, h: float, l: float, c: float, spread: float = 0.00010) -> Bar:
    """One synthetic bar at START + 5*i minutes; ask = bid + spread."""

    return Bar(
        start=START + timedelta(minutes=5 * i),
        bid_open=o, bid_high=h, bid_low=l, bid_close=c, bid_volume=1.0,
        ask_open=o + spread, ask_high=h + spread, ask_low=l + spread, ask_close=c + spread,
        ask_volume=1.0,
        spread_open=spread, spread_open_pips=spread * 10000,
        spread_high=spread, spread_high_pips=spread * 10000,
        spread_low=spread, spread_low_pips=spread * 10000,
        spread_close=spread, spread_close_pips=spread * 10000,
    )


def series(rows, spread: float = 0.00010) -> list[Bar]:
    return [bar(i, *row, spread=spread) for i, row in enumerate(rows)]


def r(value, digits: int = 8):
    return None if value is None else round(float(value), digits)


# ------------------------------------------------------------------ fixtures
def fixture_dealing_range() -> dict:
    """Premium, discount and exactly-at-equilibrium for the same confirmed pair."""

    state = DealingRangeState()
    swings = SwingState()
    swings.push([{"side": "low", "price": 1.1000, "level_index": 1, "confirm_index": 2},
                 {"side": "high", "price": 1.1100, "level_index": 5, "confirm_index": 6}])
    out = {}
    for key, close in (("premium", 1.1070), ("discount", 1.1030), ("equilibrium", 1.1050)):
        result = state.compute(swings, close)
        out[key] = {"position": result["position"],
                    "low": r(result["low"]), "high": r(result["high"]),
                    "equilibrium": r(result["equilibrium"]),
                    "position_ratio": r(result["position_ratio"])}
    out["definition_id"] = state.DEFINITION_ID
    return out


def fixture_liquidity_pools() -> dict:
    """One pool stays untaken, one is taken by a later wick."""

    pools = LiquidityState()
    swings = SwingState()
    found = [{"side": "high", "price": 1.1050, "level_index": 1, "confirm_index": 3},
             {"side": "low", "price": 1.0980, "level_index": 5, "confirm_index": 7},
             {"side": "high", "price": 1.1060, "level_index": 9, "confirm_index": 11}]
    swings.push(found)
    pools.push_swings(found, swings)
    # a bar that trades through 1.1050 (takes the first high pool) but stays under 1.1060
    pools.push_bar(bar(12, 1.1040, 1.1055, 1.1035, 1.1045), 12)
    return {
        "untaken_high_levels": sorted({r(p["level"]) for p in pools.untaken("high")}),
        "taken_levels": sorted({r(p["level"]) for p in pools.taken()}),
        "kinds": sorted({p["kind"] for p in pools.pools}),
        "states": sorted({p["state"] for p in pools.pools}),
        "equal_highs_ratio": "KNOWLEDGE_GAP: EQUAL_HIGHS_RATIO",
    }


def fixture_sweep_and_displacement() -> dict:
    """A sweep of the swing high, on the same bar as a displacement candle, and separately without."""

    # bars 1..4 build a swing high at bar 3 (confirm 4), bar 5 sweeps it and closes back below.
    rows = [
        (1.1000, 1.1010, 1.0990, 1.1005),
        (1.1005, 1.1015, 1.0995, 1.1010),
        (1.1010, 1.1050, 1.1008, 1.1015),   # 2: swing high wick 1.1050 (middle candle is index 2)
        (1.1015, 1.1020, 1.1000, 1.1005),
        # 4: wick above 1.1050, closes back below, body/range 0.83 -> displacement V-D-01 YES
        (1.1055, 1.1060, 1.1000, 1.1005),
    ]
    bars = series(rows)
    win = Window(20)
    swings = SwingState()
    out = {}
    for i, b in enumerate(bars):
        win.push(b)
        swings.push(swing_now(win) if len(win.b1) >= 3 else [])
        if i == 4:
            high = swings.last("high")
            sweep = sweep_now(win, "high", high.price if high else None)
            disp = displacement_now(win)
            out["sweep_with_wide_body"] = {
                "answer": sweep["answer"], "level": r(sweep["level"]),
                "variant": sweep["variant_id"],
            }
            out["displacement_same_bar"] = {"answer": disp["answer"],
                                            "ratio": r(disp["ratio"]),
                                            "variant": disp["variant_id"]}
    # the same sweep shape with a narrow body: the sweep still fires, displacement does not
    # same sweep geometry with a marubozu-thin body: sweep YES, displacement NO (body/range 0.02)
    rows_narrow = list(rows[:4]) + [(1.1006, 1.1060, 1.1004, 1.1007)]
    win2 = Window(20)
    swings2 = SwingState()
    for i, b in enumerate(series(rows_narrow)):
        win2.push(b)
        swings2.push(swing_now(win2) if len(win2.b1) >= 3 else [])
        if i == 4:
            high = swings2.last("high")
            sweep = sweep_now(win2, "high", high.price if high else None)
            disp = displacement_now(win2)
            out["sweep_with_narrow_body"] = {"sweep": sweep["answer"],
                                             "displacement": disp["answer"],
                                             "ratio": r(disp["ratio"])}
    return out


def fixture_structure_shift() -> dict:
    """A close beyond the most recent confirmed swing high, with and without displacement."""

    swings = SwingState()
    swings.push([{"side": "high", "price": 1.1050, "level_index": 1, "confirm_index": 3},
                 {"side": "low", "price": 1.0980, "level_index": 5, "confirm_index": 7}])
    up = structure_shift(bar(8, 1.1040, 1.1065, 1.1038, 1.1060), swings,
                         {"answer": "YES"})
    down = structure_shift(bar(9, 1.1060, 1.1062, 1.0975, 1.0978), swings, {"answer": "NO"})
    return {
        "up": {"direction": up["shift"]["direction"], "level": r(up["shift"]["level"]),
               "with_displacement": up["with_displacement"],
               "qualification": up["qualification"]},
        "down": {"direction": down["shift"]["direction"], "level": r(down["shift"]["level"]),
                 "with_displacement": down["with_displacement"]},
    }


def _fvg_bars() -> list[Bar]:
    """bar 2 is the middle candle; low(3) > high(1) makes a bullish gap [high(1), low(3)]."""

    return series([
        (1.1000, 1.1015, 1.0995, 1.1010),   # 0  high 1.1015
        (1.1010, 1.1060, 1.1008, 1.1055),   # 1
        (1.1055, 1.1070, 1.1030, 1.1065),   # 2  low 1.1030 > 1.1015 -> gap
    ])


def fixture_fvg_respected() -> dict:
    """The gap is touched (wick inside it) but never closed through."""

    gaps = GapState()
    win = Window(20)
    for i, b in enumerate(_fvg_bars()):
        win.push(b)
        new = fvg_now(win) if len(win.b1) >= 3 else []
        if new:
            gaps.push(new, i)
    accepted = gaps.active("bullish")
    gaps.push_bar(bar(3, 1.1060, 1.1065, 1.1025, 1.1055))     # wick into the gap, close above it
    return {
        "created": [{"direction": g["direction"], "lower": r(g["lower"]), "upper": r(g["upper"])}
                    for g in accepted],
        "state_after_touch": gaps.active("bullish")[0]["state"],
        "invalidation": gaps.active("bullish")[0]["invalidation"],
    }


def fixture_fvg_invalidated() -> dict:
    """The gap is closed through, which the build labels closed_through (invalidation stays a gap)."""

    gaps = GapState()
    win = Window(20)
    for i, b in enumerate(_fvg_bars()):
        win.push(b)
        new = fvg_now(win) if len(win.b1) >= 3 else []
        if new:
            gaps.push(new, i)
    gaps.push_bar(bar(3, 1.1055, 1.1058, 1.1000, 1.1010))     # closes below the gap's lower bound
    return {
        "state_after_close_through": gaps.zones[0]["state"],
        "active_after": len(gaps.active("bullish")),
        "invalidation_rule": "KNOWLEDGE_GAP: FVG_INVALIDATION",
    }


def fixture_ranking_three_zones() -> dict:
    """Three candidate bullish zones; the ranking must pick one and print every criterion."""

    zones = [
        {"zone_id": "fvg:bullish:10", "kind": "fvg", "direction": "bullish",
         "lower": 1.1010, "upper": 1.1020, "formed_index": 10, "state": "untouched",
         "freshness": "untouched", "invalidation": "KNOWLEDGE_GAP: FVG_INVALIDATION",
         "claim_ids": ("B1",)},
        {"zone_id": "ob:bullish:14", "kind": "order_block", "direction": "bullish",
         "lower": 1.1000, "upper": 1.1008, "formed_index": 14, "state": "valid",
         "freshness": "untouched", "invalidation": "far edge", "claim_ids": ("C-OB-01",)},
        {"zone_id": "sweep:low:18", "kind": "sweep_level", "direction": "bullish",
         "lower": 1.0985, "upper": 1.1005, "formed_index": 18, "state": "untouched",
         "freshness": "untouched", "invalidation": "sweep wick", "claim_ids": ("E1",)},
    ]
    up = rank_zones(zones, bias="UP", close=1.1015, range_high=1.1100, range_low=1.0980)
    down = rank_zones(zones, bias="DOWN", close=1.1015, range_high=1.1100, range_low=1.0980)
    # a bearish zone far above price: it agrees with a DOWN bias while the nearest zone does not,
    # so criterion (i) and criterion (iii) name different zones -> criteria_conflict
    conflicted_zones = zones + [{
        "zone_id": "ob:bearish:22", "kind": "order_block", "direction": "bearish",
        "lower": 1.1060, "upper": 1.1070, "formed_index": 22, "state": "valid",
        "freshness": "untouched", "invalidation": "far edge", "claim_ids": ("C-OB-02",)}]
    conflict = rank_zones(conflicted_zones, bias="DOWN", close=1.1015,
                         range_high=1.1100, range_low=1.0980)
    return {
        "with_bias_up": {
            "order": [z["zone_id"] for z in up["ranked"]],
            "first": up["ranked"][0]["zone_id"],
            "criteria_conflict": up["criteria_conflict"],
            "priority": up["priority"],
            "criteria_i_value": up["criteria"]["i"]["value"],
            "criteria_iii_value": r(up["criteria"]["iii"]["value"]),
        },
        "with_bias_down": {
            "first": down["ranked"][0]["zone_id"],
            "criteria_conflict": down["criteria_conflict"],
            "priority": down["priority"],
        },
        "conflict_case": {
            "by_bias_first": conflict["ranked"][0]["zone_id"],
            "by_distance_first": conflict["by_distance_first"],
            "criteria_conflict": conflict["criteria_conflict"],
            "priority": conflict["priority"],
        },
    }


def _ctx_for_plan(targets, *, position="discount", bias="UP", in_window=True):
    return {
        "bias": bias, "bias_daily": bias, "bias_weekly": bias, "bias_direction": bias,
        "range": {"position": position},
        "session": {"declared_window": "euro_0200_0500", "in_window": in_window},
        "ranking": {"criteria": {"i": {"name": "bias agreement", "tag": "ENGINEERING_CHOICE"},
                                 "ii": {"name": "freshness", "tag": "ENGINEERING_CHOICE"},
                                 "iii": {"name": "distance", "tag": "SOURCE_NUMBER"}},
                    "criteria_conflict": False},
        "targets": targets, "close": 1.1015,
        "what_would_change": ["a confirmed swing against the thesis"],
    }


def fixture_plan_two_targets() -> dict:
    targets = [
        {"pool_id": "pool:high:old_extreme:3:1.10500000", "kind": "old_extreme", "level": 1.1050,
         "distance_ratio": 0.03, "distance_rank": 1, "timeframe_significance_rank": 1},
        {"pool_id": "pool:high:higher_timeframe_extreme:4:1.11000000",
         "kind": "higher_timeframe_extreme", "level": 1.1100, "distance_ratio": 0.07,
         "distance_rank": 2, "timeframe_significance_rank": 2},
    ]
    zone = {"zone_id": "fvg:bullish:10", "kind": "fvg", "direction": "bullish",
            "lower": 1.1010, "upper": 1.1020, "formed_index": 10, "claim_ids": ("B1",)}
    plan = build_plan(decision_index=42, decided_at=START, bar=bar(42, 1.1012, 1.1016, 1.1008, 1.1015),
                      zone=zone, entry=1.1020, ctx=_ctx_for_plan(targets))
    return {
        "entry": r(plan["entry"]), "stop": r(plan["stop"]),
        "t1": r(plan["t1"]["level"]), "t2": r(plan["t2"]["level"]),
        "t2_note": plan["t2_note"],
        "rr_t1": r(plan["rr_t1_measured"], 4), "rr_t2": r(plan["rr_t2_measured"], 4),
        "contract_status": plan["contract_status"],
        "stop_rule": plan["stop_rule"],
    }


def fixture_plan_one_target() -> dict:
    targets = [{"pool_id": "pool:high:old_extreme:3:1.10500000", "kind": "old_extreme",
                "level": 1.1050, "distance_ratio": 0.03, "distance_rank": 1,
                "timeframe_significance_rank": 1}]
    zone = {"zone_id": "fvg:bullish:10", "kind": "fvg", "direction": "bullish",
            "lower": 1.1010, "upper": 1.1020, "formed_index": 10, "claim_ids": ("B1",)}
    plan = build_plan(decision_index=43, decided_at=START, bar=bar(43, 1.1012, 1.1016, 1.1008, 1.1015),
                      zone=zone, entry=1.1020, ctx=_ctx_for_plan(targets))
    return {"t1": r(plan["t1"]["level"]), "t2": plan["t2"], "t2_note": plan["t2_note"],
            "rr_t2": plan["rr_t2_measured"]}


def fixture_no_plan_reasons() -> dict:
    zone = {"zone_id": "fvg:bullish:10", "kind": "fvg", "direction": "bullish",
            "lower": 1.1010, "upper": 1.1020, "formed_index": 10, "claim_ids": ("B1",)}
    targets = [{"pool_id": "p", "kind": "old_extreme", "level": 1.1100, "distance_ratio": 0.05,
                "distance_rank": 1, "timeframe_significance_rank": 1}]
    out = {}
    out["outside_window"] = gates(ctx=_ctx_for_plan(targets, in_window=False), zones=[zone],
                                  direction="bullish", entry=1.1015)[1]
    out["premium_for_a_long"] = gates(ctx=_ctx_for_plan(targets, position="premium"), zones=[zone],
                                      direction="bullish", entry=1.1015)[1]
    out["no_zone"] = gates(ctx=_ctx_for_plan(targets), zones=[], direction="bullish",
                           entry=1.1015)[1]
    out["no_target"] = gates(ctx=_ctx_for_plan([]), zones=[zone], direction="bullish",
                             entry=1.1015)[1]
    far_zone = dict(zone, lower=1.0900, upper=1.0910)
    out["zone_not_touched"] = gates(ctx=_ctx_for_plan(targets), zones=[far_zone],
                                    direction="bullish", entry=1.1015)[1]
    conflict = _ctx_for_plan(targets)
    conflict["ranking"]["criteria_conflict"] = True
    out["criteria_conflict"] = gates(ctx=conflict, zones=[zone], direction="bullish",
                                     entry=1.1015)[1]
    return out


def fixture_memory_bound() -> dict:
    """State at t must not depend on bars older than the window.

    A strictly monotone series has no confirmed swing (every high is exceeded by the next bar), so
    nothing older than the window is ever referenced; the state at the last bar must be identical
    whether the run started 40 bars earlier or not.
    """

    def run(extra: int) -> dict:
        # `extra` bars are *older* bars prepended to the SAME final 80 bars, so both runs end on
        # the identical bar and only the amount of history before it differs.
        first = -extra
        rows = [(1.1000 + 0.0001 * i, 1.1002 + 0.0001 * i, 1.0998 + 0.0001 * i,
                 1.1001 + 0.0001 * i) for i in range(first, 80)]
        win = Window(60)
        swings = SwingState()
        pools = LiquidityState()
        gaps = GapState()
        for i, b in enumerate(series(rows)):
            win.push(b)
            found = swing_now(win) if len(win.b1) >= 3 else []
            swings.push(found)
            pools.push_swings(found, swings)
            pools.push_bar(b, i)
            gaps.push(fvg_now(win) if len(win.b1) >= 3 else [], i)
            gaps.push_bar(b)
        return {
            "swing_count": len(swings.swings),
            "pool_count": len(pools.pools),
            "gap_count": len(gaps.zones),
            "last_close": r(win.bars[-1].bid_close),
            "dealing_range": DealingRangeState().compute(swings, win.bars[-1].bid_close)["position"],
            "window_len": len(win),
        }

    short = run(0)
    long = run(40)
    return {"with_40_older_bars": long, "window_only": short, "identical": long == short}


ALL_FIXTURES = {
    "dealing_range": fixture_dealing_range,
    "liquidity_pools": fixture_liquidity_pools,
    "sweep_and_displacement": fixture_sweep_and_displacement,
    "structure_shift": fixture_structure_shift,
    "fvg_respected": fixture_fvg_respected,
    "fvg_invalidated": fixture_fvg_invalidated,
    "ranking_three_zones": fixture_ranking_three_zones,
    "plan_two_targets": fixture_plan_two_targets,
    "plan_one_target": fixture_plan_one_target,
    "no_plan_reasons": fixture_no_plan_reasons,
    "memory_bound": fixture_memory_bound,
}


def main() -> int:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--freeze", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = ap.parse_args()

    EXPECTED.mkdir(exist_ok=True)
    failures = 0
    for name, fn in ALL_FIXTURES.items():
        path = EXPECTED / f"EXPECTED_{name}.json"
        actual = fn()
        if args.freeze:
            path.write_text(json.dumps(actual, indent=1, sort_keys=True))
            print(f"frozen  {path.name}")
            continue
        if not path.exists():
            print(f"MISSING {path.name}")
            failures += 1
            continue
        expected = json.loads(path.read_text())
        if expected == json.loads(json.dumps(actual, default=str)):
            print(f"ok      {name}")
        else:
            failures += 1
            print(f"FAIL    {name}")
            for key in sorted(set(expected) | set(actual)):
                if expected.get(key) != actual.get(key):
                    print(f"        {key}: expected={expected.get(key)!r} actual={actual.get(key)!r}")
    if args.check:
        print(f"\nfixtures: {len(ALL_FIXTURES) - failures}/{len(ALL_FIXTURES)} ok, {failures} failed")
    return 0 if failures == 0 or args.freeze else 1


if __name__ == "__main__":
    raise SystemExit(main())
