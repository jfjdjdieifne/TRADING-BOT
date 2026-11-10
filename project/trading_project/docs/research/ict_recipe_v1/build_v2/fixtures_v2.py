#!/usr/bin/env python3
"""Fixtures V2 — frozen expectations for the setup-frame separation and the D1-D4 repairs.

    python3 fixtures_v2.py --freeze     # writes EXPECTED_V2/*.json (never after a failure)
    python3 fixtures_v2.py --check      # re-runs and compares

Every fixture is hand-made candles. No market data, no network, no pandas. A failing expectation is a
DEFECT record; the EXPECTED file is never edited to match a result.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "build_v1"))

from frame_v2 import FrameAggregator, bucket_start                      # noqa: E402
from plan_v1 import build_plan                                          # noqa: E402
from stream_v1 import Bar, SwingState, Window, swing_now                # noqa: E402
from wrapper_v2 import FrameState, _range_repaired                      # noqa: E402

UTC = timezone.utc
EXPECTED = HERE / "EXPECTED_V2"
FIXTURE_TAG = "FIXTURE"


def bar(minute: int, o: float, h: float, l: float, c: float, spread: float = 0.0001) -> Bar:
    start = datetime(2021, 3, 1, tzinfo=UTC) + timedelta(minutes=5 * minute)
    return Bar(
        start=start, bid_open=o, bid_high=h, bid_low=l, bid_close=c, bid_volume=1.0,
        ask_open=o + spread, ask_high=h + spread, ask_low=l + spread, ask_close=c + spread,
        ask_volume=1.0,
        spread_open=spread, spread_open_pips=spread * 10000, spread_high=spread,
        spread_high_pips=spread * 10000, spread_low=spread, spread_low_pips=spread * 10000,
        spread_close=spread, spread_close_pips=spread * 10000)


# ---------------------------------------------------------------- causal aggregation
def fx_15m_not_before_third_close() -> dict:
    agg = FrameAggregator(15)
    out = [agg.push(bar(i, 1.10, 1.101, 1.099, 1.1005)) for i in range(3)]
    return {"emitted": [o is not None for o in out]}


def fx_15m_emits_on_bucket_change() -> dict:
    agg = FrameAggregator(15)
    outs = [agg.push(bar(i, 1.10 + i * 0.0001, 1.101 + i * 0.0001, 1.099 + i * 0.0001,
                         1.1005 + i * 0.0001)) for i in range(4)]
    emitted = [i for i, o in enumerate(outs) if o is not None]
    cand = outs[emitted[0]] if emitted else None
    return {"first_emitted_at_push": emitted[0] if emitted else None,
            "candle_high": cand.bid_high if cand else None,
            "candle_low": cand.bid_low if cand else None,
            "candle_open": cand.bid_open if cand else None,
            "candle_close": cand.bid_close if cand else None}


def fx_no_partial_high_low_leak() -> dict:
    """While a 15m candle is forming, the frame's window must not contain it."""
    state = FrameState("15m", 64)
    seen = []
    for i in range(3):
        state.push(bar(i, 1.10, 1.101 + i * 0.001, 1.099, 1.1005))
        seen.append(len(state.window))
    before = len(state.window)
    state.push(bar(3, 1.10, 1.1013, 1.099, 1.1005))      # closes the first 15m candle
    return {"window_lengths_during": seen, "window_after_close": len(state.window),
            "grew_by_exactly_one": len(state.window) == before + 1,
            "last_is_none_while_forming": before == 0}


def fx_swing_needs_right_bar() -> dict:
    """A swing on the setup frame is confirmed only after its right-hand candle closes."""
    w = Window(64)
    highs = [1.100, 1.100, 1.106, 1.100]
    got = []
    for i, h in enumerate(highs):
        w.push(bar(i, 1.100, h, 1.099, 1.100))
        got.append(len(swing_now(w)))
    return {"per_candle_swing_count": got}


# ---------------------------------------------------------------- repairs
def fx_d1_age_same_index_space() -> dict:
    """Two 15m candles make a swing, the swing makes a pool, and its age is index - formed."""
    state = FrameState("15m", 8)
    highs = [1.1000, 1.0900, 1.0905, 1.0902, 1.0950, 1.0903, 1.0901,
             1.0930, 1.0904, 1.0906, 1.0940, 1.0902, 1.0900, 1.0955,
             1.0901, 1.0903, 1.0905, 1.0960, 1.0902, 1.0900, 1.0904,
             1.0906, 1.0902, 1.0950, 1.0901]
    for i, h in enumerate(highs):
        state.push(bar(i, 1.0890, h, 1.0880, 1.0895))
    pools = state.pool_view()
    formed = [p["formed_index"] for p in pools]
    ages = [p["age_bars"] for p in pools]
    return {"n_pools": len(pools), "frame_index": state.index,
            "formed_indices": formed, "ages": ages,
            "ages_equal_index_minus_formed":
                all(a is not None and f is not None and a == state.index - f
                    for a, f in zip(ages, formed)),
            "all_ages_plausible": all(a is not None and 0 <= a < 100 for a in ages)}


def fx_d2_minus_one_index() -> dict:
    state = FrameState("15m", 8)
    state.pools.push_htf({"daily": {"high": 1.2, "low": 1.1, "open": 1.12, "close": 1.15,
                                    "bias": "UP", "bucket_start": "2021-03-01T00:00:00+00:00",
                                    "available_at": "2021-03-02T00:00:00+00:00"},
                          "weekly": None})
    pools = state.pool_view()
    return {"n": len(pools),
            "ages": [p["age_bars"] for p in pools],
            "states": [p["age_state"] for p in pools]}


def fx_d3_ratio_state() -> dict:
    above = _range_repaired({"position": "premium", "position_ratio": 1.0189})
    below = _range_repaired({"position": "discount", "position_ratio": -0.2})
    inside = _range_repaired({"position": "discount", "position_ratio": 0.3})
    return {"above": (above["position_ratio"], above["position_state"]),
            "below": (below["position_ratio"], below["position_state"]),
            "inside": (inside["position_ratio"], inside["position_state"])}


# ---------------------------------------------------------------- plan geometry
def _ctx(targets: list[dict], position: str = "discount") -> dict:
    return {"bias": "UP", "bias_daily": "UP", "bias_weekly": "UP", "bias_direction": "UP",
            "range": {"position": position, "low": 1.09, "high": 1.11, "equilibrium": 1.10,
                      "position_ratio": 0.4},
            "session": {"declared_window": "EURO_0200_0500", "in_window": True},
            "ranking": {"ranked": [], "criteria": {}, "criteria_conflict": False},
            "targets": targets, "close": 1.1000,
            "what_would_change": ["a confirmed swing against the thesis on the setup frame"]}


def _zone(kind: str = "fvg", lower: float = 1.0990, upper: float = 1.1000) -> dict:
    return {"zone_id": "15m:fvg:bullish:4", "kind": kind, "direction": "bullish",
            "lower": lower, "upper": upper, "formed_index": 4, "state": "untouched",
            "freshness": "untouched", "invalidation": None, "claim_ids": ("B1",),
            "frame": "15m"}


def fx_stop_far_edge_vs_sweep() -> dict:
    targets = [{"pool_id": "p1", "level": 1.1040, "kind": "old_extreme", "side": "high",
                "distance_rank": 1, "distance_ratio": 0.4, "timeframe_significance_rank": 1}]
    fvg_plan = build_plan(decision_index=1, decided_at=datetime(2021, 3, 1, tzinfo=UTC),
                          bar=bar(0, 1.10, 1.101, 1.099, 1.1000),
                          zone=_zone(), entry=1.1000, ctx=_ctx(targets))
    sweep_zone = dict(_zone(kind="sweep_level", lower=1.0980, upper=1.1000))
    sweep_plan = build_plan(decision_index=1, decided_at=datetime(2021, 3, 1, tzinfo=UTC),
                            bar=bar(0, 1.10, 1.101, 1.099, 1.1000),
                            zone=sweep_zone, entry=1.1000, ctx=_ctx(targets))
    return {"fvg_stop": fvg_plan["stop"], "fvg_rule": fvg_plan["stop_rule"],
            "sweep_stop": sweep_plan["stop"], "sweep_rule": sweep_plan["stop_rule"]}


def fx_two_targets_and_one_target() -> dict:
    two = [{"pool_id": "p1", "level": 1.1040, "kind": "old_extreme", "side": "high",
            "distance_rank": 1, "distance_ratio": 0.4, "timeframe_significance_rank": 1},
           {"pool_id": "p2", "level": 1.1080, "kind": "relative_equal_pair", "side": "high",
            "distance_rank": 2, "distance_ratio": 0.8, "timeframe_significance_rank": None}]
    plan_two = build_plan(decision_index=1, decided_at=datetime(2021, 3, 1, tzinfo=UTC),
                          bar=bar(0, 1.10, 1.101, 1.099, 1.1000), zone=_zone(),
                          entry=1.1000, ctx=_ctx(two))
    plan_one = build_plan(decision_index=1, decided_at=datetime(2021, 3, 1, tzinfo=UTC),
                          bar=bar(0, 1.10, 1.101, 1.099, 1.1000), zone=_zone(),
                          entry=1.1000, ctx=_ctx(two[:1]))
    return {"t1": plan_two["t1"]["level"], "t2": plan_two["t2"]["level"],
            "rr_t1": round(plan_two["rr_t1_measured"], 4),
            "rr_t2": round(plan_two["rr_t2_measured"], 4),
            "one_t2": plan_one["t2"], "one_note": plan_one["t2_note"]}


def fx_no_plan_when_stop_equals_entry() -> dict:
    plan = build_plan(decision_index=1, decided_at=datetime(2021, 3, 1, tzinfo=UTC),
                      bar=bar(0, 1.10, 1.101, 1.099, 1.1000),
                      zone=_zone(lower=1.1000, upper=1.1000), entry=1.1000, ctx=_ctx([]))
    return {"error": plan.get("error")}


# ---------------------------------------------------------------- thesis identity (D4)
def fx_thesis_identity() -> dict:
    """The identity is a pure function of frame + zone + direction; a settled id is never re-armed."""
    zone_a = _zone()
    zone_b = dict(_zone(), zone_id="15m:fvg:bullish:9", lower=1.0980, upper=1.0990)
    thesis_a = f"{zone_a['zone_id']}:bullish"
    thesis_b = f"{zone_b['zone_id']}:bullish"
    consumed = {thesis_a}
    return {"a_blocked": thesis_a in consumed, "b_allowed": thesis_b not in consumed,
            "identity_includes_frame": thesis_a.startswith("15m:")}


def fx_bucket_alignment() -> dict:
    t = datetime(2021, 3, 1, 10, 47, tzinfo=UTC)
    return {"m5": bucket_start(t, 5).isoformat(), "m15": bucket_start(t, 15).isoformat(),
            "h1": bucket_start(t, 60).isoformat()}


FIXTURES = {
    "fx_15m_not_before_third_close": fx_15m_not_before_third_close,
    "fx_15m_emits_on_bucket_change": fx_15m_emits_on_bucket_change,
    "fx_no_partial_high_low_leak": fx_no_partial_high_low_leak,
    "fx_swing_needs_right_bar": fx_swing_needs_right_bar,
    "fx_d1_age_same_index_space": fx_d1_age_same_index_space,
    "fx_d2_minus_one_index": fx_d2_minus_one_index,
    "fx_d3_ratio_state": fx_d3_ratio_state,
    "fx_stop_far_edge_vs_sweep": fx_stop_far_edge_vs_sweep,
    "fx_two_targets_and_one_target": fx_two_targets_and_one_target,
    "fx_no_plan_when_stop_equals_entry": fx_no_plan_when_stop_equals_entry,
    "fx_thesis_identity": fx_thesis_identity,
    "fx_bucket_alignment": fx_bucket_alignment,
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    EXPECTED.mkdir(exist_ok=True)
    ok = bad = 0
    for name, fn in FIXTURES.items():
        got = fn()
        path = EXPECTED / f"EXPECTED_{name}.json"
        if args.freeze:
            path.write_text(json.dumps({"_tag": FIXTURE_TAG, "_fixture": name, "value": got},
                                       indent=1, sort_keys=True), encoding="utf-8")
            print(f"frozen  {name}")
            continue
        want = json.loads(path.read_text(encoding="utf-8"))["value"]
        if want == json.loads(json.dumps(got, sort_keys=True)) or want == got:
            ok += 1
            print(f"ok      {name}")
        else:
            bad += 1
            print(f"FAILED  {name}\n  want {want}\n  got  {json.loads(json.dumps(got, sort_keys=True))}")
    if not args.freeze:
        print(f"\n{ok} ok, {bad} failed, {ok + bad} total")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
