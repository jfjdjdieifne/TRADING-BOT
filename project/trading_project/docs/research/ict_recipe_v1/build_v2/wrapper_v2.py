#!/usr/bin/env python3
"""Streaming wrapper v2: the thesis is built on a setup frame, the touch happens on 5m.

Composition, not copying: every primitive, state object, ranking function, gate chain, plan builder
and tracker is imported from `build_v1/` (frozen).  What is new here is only (a) the setup-frame
aggregation, (b) which frame feeds zones / stop / target pools, (c) the D1-D4 repairs, and (d) the
record of what the run consumed.

No `MonitoringLoop`.  Memory cap = 42.5 % of physical RAM?  No: 70 %, declared in v1 row 17 and kept
(DECLARED_CHOICES_V2 row O).
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

from frame_v2 import FRAME_MINUTES, FrameAggregator
from plan_v1 import (
    PlanTracker,
    StoryState,
    build_plan,
    gates,
    gather_zones,
    rank_zones,
    targets_ahead,
)
from stream_v1 import (
    Bar,
    DealingRangeState,
    GapState,
    HtfState,
    LiquidityState,
    OrderBlockState,
    SwingState,
    Window,
    displacement_now,
    fvg_now,
    memory_rss_kb,
    memory_total_kb,
    peak_rss_kb,
    session_now,
    structure_shift,
    sweep_now,
    swing_now,
)

MEMORY_CAP_FRACTION = 0.70         # ENGINEERING_CHOICE (vile v1 row 17, unchanged)
MEMORY_CHECK_EVERY = 60            # ENGINEERING_CHOICE: one hour of 5m bars
WINDOW_5M = 5760                   # 20 trading days of 5m, v1 row 1
WINDOW_BY_FRAME = {"5m": 5760, "15m": 1920, "1h": 480}   # same 20 trading days, v2 row L
NON_PLAN_SAMPLE_SIZE = 10
NON_PLAN_SAMPLE_SEED = 20261109


def _jsonl(fh, record: dict) -> None:
    fh.write(json.dumps(record, default=str) + "\n")


class FrameState:
    """One setup frame: its own candle window, its own states, its own index space."""

    def __init__(self, label: str, capacity: int) -> None:
        self.label = label
        self.minutes = FRAME_MINUTES[label]
        self.agg = FrameAggregator(self.minutes)
        self.window = Window(capacity)
        self.swings = SwingState()
        self.ranges = DealingRangeState()
        self.pools = LiquidityState()
        self.gaps = GapState()
        self.blocks = OrderBlockState()
        self.index = -1
        self.last: dict | None = None
        self.closed_count = 0

    def push(self, bar: Bar) -> Bar | None:
        """Feed a 5m bar; update everything only when this frame's candle has CLOSED."""

        closed = self.agg.push(bar)
        if closed is None:
            return None
        self.index += 1
        self.closed_count += 1
        self.window.push(closed)
        found = swing_now(self.window)
        self.swings.push(found)
        self.pools.push_swings(found, self.swings)
        # D1 repair: the pool index and the age are computed in the SAME index space (this frame's)
        self.pools.push_bar(closed, self.index)
        new_gaps = fvg_now(self.window)
        self.gaps.push(new_gaps, self.index)
        self.gaps.push_bar(closed)
        disp = displacement_now(self.window)
        self.blocks.push_bar(closed)
        high_ref = self.swings.last("high")
        low_ref = self.swings.last("low")
        sweep_high = sweep_now(self.window, "high", high_ref.price if high_ref else None)
        sweep_low = sweep_now(self.window, "low", low_ref.price if low_ref else None)
        block = None
        if disp.get("answer") == "YES" and self.window.t >= 2:
            direction = "bullish" if closed.bid_close > closed.bid_open else "bearish"
            block = self.blocks.maybe_create(
                self.window, disp, direction,
                fvg_below=any(z["direction"] == direction for z in new_gaps),
                sweep_evidence=(sweep_high.get("answer") == "YES" if direction == "bearish"
                                else sweep_low.get("answer") == "YES"),
                structure_break=bool(structure_shift(closed, self.swings, disp)["shift"]),
            )
        self.last = {
            "bar": closed, "swings": found, "gaps": new_gaps, "displacement": disp,
            "sweep_high": sweep_high, "sweep_low": sweep_low, "block": block,
            "range": self.ranges.compute(self.swings, closed.bid_close),
            "shift": structure_shift(closed, self.swings, disp),
        }
        return closed

    def pool_view(self) -> list[dict]:
        """Untaken pools with the frame label and the repaired age (D1/D2)."""

        out = []
        for side in ("high", "low"):
            for pool in self.pools.untaken(side):
                item = dict(pool)
                item["frame"] = self.label
                formed = pool.get("formed_index")
                if formed is None or formed < 0:
                    item["formed_index"] = None
                    item["age_bars"] = None
                    item["age_state"] = "NO_FORMATION_BAR"        # D2 repair
                else:
                    item["age_bars"] = self.index - formed        # D1 repair
                    item["age_state"] = "MEASURED"
                out.append(item)
        return out


def _range_repaired(rg: dict) -> dict:
    """D3 repair: never report a ratio outside [0, 1] without saying so."""

    out = dict(rg)
    ratio = rg.get("position_ratio")
    if ratio is None:
        return out
    if ratio > 1.0:
        out["position_ratio"] = 1.0
        out["position_state"] = "ABOVE_RANGE"
    elif ratio < 0.0:
        out["position_ratio"] = 0.0
        out["position_state"] = "BELOW_RANGE"
    else:
        out["position_state"] = "INSIDE_RANGE"
    return out


def run_stream_v2(
    bars: list[Bar],
    *,
    out_dir: Path,
    variant: str,
    setup_frame: str,
    target_frames: tuple[str, ...],
    session_filter: bool,
    decide_from: datetime | None = None,
    decide_to: datetime | None = None,
    max_decisions: int | None = None,
) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)

    frames: dict[str, FrameState] = {}
    for label in {setup_frame, *target_frames}:
        frames[label] = FrameState(label, WINDOW_BY_FRAME[label])
    setup = frames[setup_frame]

    htf = HtfState()
    tracker = PlanTracker()
    story = StoryState()

    total_kb = memory_total_kb()
    cap_kb = int(total_kb * MEMORY_CAP_FRACTION) if total_kb else None

    started = time.time()
    counts = {"bars": 0, "decisions": 0, "plans": 0, "no_plan": 0, "armings": 0,
              "same_bar_settled": 0}
    reasons: dict[str, int] = {}
    concepts = {"swing": 0, "fvg": 0, "order_block": 0, "order_block_created": 0,
                "dealing_range": 0, "liquidity_pool_formed": 0, "pool_taken": 0,
                "sweep": 0, "displacement": 0, "structure_shift": 0, "bias_defined": 0,
                "zone_touched": 0}
    rss_curve: list[dict] = []
    non_plan: list[dict] = []
    theses: dict[str, dict] = {}
    consumed: set[str] = set()
    stopped = None

    with open(out_dir / "decisions.jsonl", "w", encoding="utf-8") as fd, \
            open(out_dir / "plans.jsonl", "w", encoding="utf-8") as fp, \
            open(out_dir / "story.jsonl", "w", encoding="utf-8") as fs:
        for index, bar in enumerate(bars):
            counts["bars"] += 1
            htf.push(bar)
            for label, state in frames.items():
                closed = state.push(bar)
                if closed is not None:
                    concepts["swing"] += len(state.last["swings"])
                    concepts["liquidity_pool_formed"] += len(state.last["swings"])
                    if state.last["gaps"]:
                        concepts["fvg"] += 1
                    if state.last["block"]:
                        concepts["order_block_created"] += 1
                        if state.last["block"]["state"] == "valid":
                            concepts["order_block"] += 1
                    if (state.last["sweep_high"]["answer"] == "YES"
                            or state.last["sweep_low"]["answer"] == "YES"):
                        concepts["sweep"] += 1
                    if state.last["displacement"]["answer"] == "YES":
                        concepts["displacement"] += 1
                    if state.last["shift"]["shift"]:
                        concepts["structure_shift"] += 1
                    if state.last["range"]["position"] != "undefined":
                        concepts["dealing_range"] += 1
            if htf.view()["daily"]:
                concepts["bias_defined"] += 1

            # ---- plans are tracked on the 5m bar, always
            before = len(tracker.settled)
            tracker.update(bar, index)
            for settled in tracker.settled[before:]:
                thesis_id = settled.get("thesis_id")
                if thesis_id:
                    consumed.add(thesis_id)
                    theses[thesis_id]["settled_at_index"] = index
                    theses[thesis_id]["r_measured"] = settled.get("r_measured")
                if settled.get("trigger_index") == settled.get("exit_index"):
                    counts["same_bar_settled"] += 1

            if total_kb and index % MEMORY_CHECK_EVERY == 0:
                rss = memory_rss_kb()
                if rss is not None:
                    rss_curve.append({"bar": index, "rss_kb": rss})
                    if cap_kb and rss > cap_kb:
                        stopped = {"reason": "memory_cap", "bar": index, "rss_kb": rss,
                                   "cap_kb": cap_kb}
                        (out_dir / "partial_status.json").write_text(
                            json.dumps({"stopped": stopped, "decisions": counts["decisions"]},
                                       indent=1), encoding="utf-8")
                        break

            if decide_from is not None and bar.start < decide_from:
                continue
            if decide_to is not None and bar.start >= decide_to:
                continue
            if max_decisions is not None and counts["decisions"] >= max_decisions:
                break

            session = session_now(bar)
            htf_view = htf.view()
            daily, weekly = htf_view["daily"], htf_view["weekly"]
            bias_daily = daily["bias"] if daily else None
            bias_weekly = weekly["bias"] if weekly else None
            bias = bias_daily or bias_weekly
            bias_conflict = bool(bias_daily and bias_weekly and bias_daily != bias_weekly)
            bias_direction = "UP" if bias == "UP" else "DOWN" if bias == "DOWN" else None

            view = setup.last
            counts["decisions"] += 1
            decision = {
                "index": index,
                "decided_at": bar.start.isoformat(),
                "variant": variant,
                "setup_frame": setup_frame,
                "setup_candles_closed": setup.closed_count,
                "close": bar.bid_close,
                "bias": {"daily": bias_daily, "weekly": bias_weekly, "resolved": bias,
                         "bias_conflict": bias_conflict},
                "session": {"declared_window": session["declared_window"],
                            "in_window": session["in_window"],
                            "filtered": session_filter},
                "range": _range_repaired(view["range"] if view else {"position": "undefined"}),
                "setup_context": None if view is None else {
                    "bar_start": view["bar"].start.isoformat(),
                    "swings": [{"side": s["side"], "price": s["price"],
                                "level_index": s["level_index"]} for s in view["swings"]],
                    "gaps": view["gaps"],
                    "displacement": {"answer": view["displacement"]["answer"],
                                     "ratio": view["displacement"].get("ratio")},
                    "sweep_high": {"answer": view["sweep_high"]["answer"],
                                   "level": view["sweep_high"].get("level")},
                    "sweep_low": {"answer": view["sweep_low"]["answer"],
                                  "level": view["sweep_low"].get("level")},
                    "shift": view["shift"]["shift"],
                    "order_block": None if not view["block"] else
                    {"state": view["block"]["state"], "lower": view["block"]["lower"],
                     "upper": view["block"]["upper"]},
                },
                "untaken": [p for p in setup.pool_view()][:12],
                "target_pools": [],
            }

            if view is None or bias_direction is None:
                reason = "no_setup_candle" if view is None else (
                    "bias_undefined" if not bias else "bias_flat")
                reasons[reason] = reasons.get(reason, 0) + 1
                counts["no_plan"] += 1
                decision["decision"] = "NO_PLAN"
                decision["reason"] = reason
                _jsonl(fd, decision)
                _jsonl(fs, story.update(index=index, bar=bar,
                                        ctx={"bias": bias, "targets": [], "range": decision["range"],
                                             "ranking": {"ranked": []}}, zone=None))
                continue

            direction = "bullish" if bias_direction == "UP" else "bearish"
            rg = decision["range"]

            pools = []
            for label in target_frames:
                pools.extend(frames[label].pool_view())
            labels_seen = {p["pool_id"]: p["frame"] for p in pools}
            targets = targets_ahead(pools,
                                    entry=bar.bid_close,
                                    range_high=rg.get("high", bar.bid_close),
                                    range_low=rg.get("low", bar.bid_close),
                                    direction=direction,
                                    fallback_formed_at=bar.start)
            for target in targets:
                target["frame"] = labels_seen.get(target["pool_id"], "?")
            decision["target_pools"] = [{"level": t["level"], "kind": t["kind"],
                                         "frame": t["frame"], "distance_ratio": t["distance_ratio"]}
                                        for t in targets[:4]]

            candidates = gather_zones(direction=direction, gaps=setup.gaps, blocks=setup.blocks,
                                      sweep=(view["sweep_low"] if direction == "bullish"
                                             else view["sweep_high"]),
                                      close=bar.bid_close)
            for zone in candidates:
                zone["zone_id"] = f"{setup_frame}:{zone['zone_id']}"
                zone["frame"] = setup_frame
            ranking = rank_zones(candidates, bias=bias_direction,
                                 close=bar.bid_close,
                                 range_high=rg.get("high", bar.bid_close),
                                 range_low=rg.get("low", bar.bid_close))
            decision["zones_ranked"] = [
                {"zone_id": z["zone_id"], "kind": z["kind"], "lower": z["lower"],
                 "upper": z["upper"], "fresh": z["fresh"], "bias_agrees": z["bias_agrees"],
                 "distance_ratio": z["distance_ratio"]} for z in ranking["ranked"][:5]]
            decision["criteria"] = ranking["criteria"]
            decision["criteria_conflict"] = ranking["criteria_conflict"]

            session_ctx = dict(session)
            if not session_filter:
                session_ctx["in_window"] = True       # SESSION_OFF, declared in row J
            ctx = {
                "bias": bias, "bias_daily": bias_daily, "bias_weekly": bias_weekly,
                "bias_direction": bias_direction, "range": rg, "session": session_ctx,
                "ranking": ranking, "targets": targets, "close": bar.bid_close,
                "what_would_change": ["a confirmed swing against the thesis on the setup frame",
                                      "the opposing pool taken before entry",
                                      "a displacement against the thesis on the setup frame",
                                      "the setup-frame zone closed through",
                                      "the session window ending"],
            }
            ok, reason_code, detail = gates(ctx=ctx, zones=ranking["ranked"],
                                            direction=direction, entry=bar.bid_close)
            if ok:
                zone = ranking["ranked"][0]
                thesis_id = f"{zone['zone_id']}:{direction}"
                if thesis_id in consumed or thesis_id in theses:
                    ok, reason_code = False, "thesis_already_consumed"     # D4 repair
                    detail = {"thesis_id": thesis_id}
            if ok:
                entry = zone["upper"] if direction == "bullish" else zone["lower"]
                plan = build_plan(decision_index=index, decided_at=bar.start, bar=bar,
                                  zone=zone, entry=entry, ctx=ctx)
                if "error" in plan:
                    ok, reason_code, detail = False, plan["error"], {}
                else:
                    plan["thesis_id"] = thesis_id
                    plan["setup_frame"] = setup_frame
                    plan["variant"] = variant
                    plan["stop_frame"] = setup_frame
                    plan["t1_frame"] = targets[0]["frame"] if targets else None
                    plan["t2_frame"] = targets[1]["frame"] if len(targets) > 1 else None
                    plan["entry_bar_range"] = bar.bid_high - bar.bid_low
                    plan["stop_distance_pips"] = abs(entry - plan["stop"]) * 10000.0
                    setup_range = float(view["bar"].bid_high - view["bar"].bid_low)
                    plan["stop_fraction_of_setup_candle"] = (
                        (abs(entry - plan["stop"]) / setup_range) if setup_range > 0 else None)
                    plan["half_spread_pips"] = bar.spread_open * 0.5 * 10000.0
                    plan["cost_fraction_of_stop"] = (
                        (bar.spread_open / 2.0 + bar.spread_open / 2.0) / abs(entry - plan["stop"])
                        if abs(entry - plan["stop"]) > 0 else None)
                    tracker.add(plan)
                    theses[thesis_id] = {"zone_id": zone["zone_id"], "direction": direction,
                                         "sweep_ref": zone.get("formed_index"),
                                         "armed_at_index": index, "setup_frame": setup_frame}
                    counts["plans"] += 1
                    counts["armings"] += 1
                    _jsonl(fp, plan)
                    decision["plan_id"] = plan["plan_id"]
                    decision["thesis_id"] = thesis_id
                    decision["decision"] = "HYPOTHETICAL_PLAN"
            if not ok:
                reasons[reason_code] = reasons.get(reason_code, 0) + 1
                counts["no_plan"] += 1
                decision["decision"] = "NO_PLAN"
                decision["reason"] = reason_code
                decision["gate_detail"] = detail
                if len(non_plan) < 4000:
                    non_plan.append({"index": index, "at": bar.start.isoformat(),
                                     "reason": reason_code, "detail": detail,
                                     "close": bar.bid_close,
                                     "range_position": rg.get("position"),
                                     "zones": len(ranking["ranked"]),
                                     "targets": len(targets)})
            _jsonl(fd, decision)
            _jsonl(fs, story.update(index=index, bar=bar, ctx=ctx,
                                    zone=ranking["ranked"][0] if ranking["ranked"] else None))

    settled = tracker.settled
    final = settled + tracker.open
    (out_dir / "plans_final.jsonl").write_text(
        "".join(json.dumps(p, default=str) + "\n" for p in final), encoding="utf-8")

    r_values = [p["r_measured"] for p in settled if p.get("r_measured") is not None]
    summary = {
        "variant": variant, "setup_frame": setup_frame, "target_frames": list(target_frames),
        "session_filter": session_filter,
        "bars_consumed": counts["bars"], "decisions": counts["decisions"],
        "plans": counts["plans"], "no_plan": counts["no_plan"],
        "armings": counts["armings"], "independent_theses": len(theses),
        "same_bar_settled": counts["same_bar_settled"],
        "settled_plans": final, "open_plans": [p["plan_id"] for p in tracker.open],
        "no_plan_reasons": dict(sorted(reasons.items(), key=lambda kv: -kv[1])),
        "concept_hits": concepts,
        "r_values": r_values,
        "elapsed_seconds": round(time.time() - started, 2),
        "memory": {"total_kb": total_kb, "cap_kb": cap_kb,
                   "peak_rss_kb": peak_rss_kb(), "rss_curve": rss_curve},
        "stopped": stopped,
        "non_plan_sample": non_plan[:60],
    }
    (out_dir / "run_summary.json").write_text(json.dumps(summary, indent=1, default=str),
                                              encoding="utf-8")
    return summary
