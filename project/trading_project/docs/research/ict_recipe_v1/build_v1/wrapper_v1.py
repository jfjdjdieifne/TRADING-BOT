#!/usr/bin/env python3
"""The streaming wrapper: one decision per closed 5m bar, bounded memory, glass-box records.

It does **not** use `MonitoringLoop` (MEMORY_ANALYSIS_V0 measured superlinear growth there).  It keeps
a fixed-length candle window, a bounded swing list, a bounded pool list, a bounded zone list, one
open-thesis record and one open-plan list, and writes one JSON line per decision to disk immediately.

Memory guard: RSS is checked every MEMORY_CHECK_EVERY bars against MEMORY_CAP_FRACTION of MemTotal.
On breach the wrapper writes `partial_status.json` and returns, instead of being OOM-killed.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

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
    WINDOW_BARS,
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

UTC = timezone.utc
MEMORY_CAP_FRACTION = 0.70      # ENGINEERING_CHOICE, DECLARED_CHOICES row 17
MEMORY_CHECK_EVERY = 60         # ENGINEERING_CHOICE: one minute of bars
NON_PLAN_SAMPLE_SIZE = 10       # owner brief: 10 seeded non-plan decisions
NON_PLAN_SAMPLE_SEED = 20261109  # owner brief


def _write_jsonl(fh, record: dict) -> None:
    fh.write(json.dumps(record, default=str) + "\n")


def run_stream(
    bars: list[Bar],
    *,
    out_dir: Path,
    decide_from: datetime | None = None,
    decide_to: datetime | None = None,
    max_decisions: int | None = None,
    label: str = "run",
) -> dict:
    """Consume `bars` one at a time and write decisions, plans, story and a manifest."""

    out_dir.mkdir(parents=True, exist_ok=True)
    decisions_path = out_dir / "decisions.jsonl"
    plans_path = out_dir / "plans.jsonl"
    story_path = out_dir / "story.jsonl"
    partial_path = out_dir / "partial_status.json"

    window = Window(WINDOW_BARS)
    swings = SwingState()
    ranges = DealingRangeState()
    pools = LiquidityState()
    gaps = GapState()
    blocks = OrderBlockState()
    htf = HtfState()
    tracker = PlanTracker()
    story = StoryState()

    total_kb = memory_total_kb()
    cap_kb = int(total_kb * MEMORY_CAP_FRACTION) if total_kb else None

    started = time.time()
    counts = {"bars": 0, "decisions": 0, "plans": 0, "no_plan": 0}
    reasons: dict[str, int] = {}
    concept_hits = {"swing": 0, "fvg": 0, "order_block": 0, "order_block_created": 0,
                    "dealing_range": 0,
                    "liquidity_pool_formed": 0, "pool_taken": 0, "sweep": 0,
                    "displacement": 0, "structure_shift": 0, "bias_defined": 0}
    rss_curve: list[dict] = []
    non_plan_samples: list[dict] = []
    stopped = None

    with open(decisions_path, "w", encoding="utf-8") as fd, \
            open(plans_path, "w", encoding="utf-8") as fp, \
            open(story_path, "w", encoding="utf-8") as fs:
        for index, bar in enumerate(bars):
            window.push(bar)
            counts["bars"] += 1
            htf.push(bar)

            # ---- primitives on the closed bar (candles[:t+1] only)
            found_swings = swing_now(window)
            swings.push(found_swings)
            sw = found_swings
            pools.push_swings(sw, swings)
            pools.push_htf(htf.view())
            pools.push_bar(bar, index)

            new_gaps = fvg_now(window)
            gaps.push(new_gaps, index)
            gaps.push_bar(bar)

            displacement = displacement_now(window)
            high_ref = swings.last("high")
            low_ref = swings.last("low")
            sweep_high = sweep_now(window, "high", high_ref.price if high_ref else None)
            sweep_low = sweep_now(window, "low", low_ref.price if low_ref else None)
            shift = structure_shift(bar, swings, displacement)
            blocks.push_bar(bar)
            block = None
            if displacement.get("answer") == "YES" and window.t >= 2:
                direction = "bullish" if bar.bid_close > bar.bid_open else "bearish"
                block = blocks.maybe_create(
                    window, displacement, direction,
                    fvg_below=any(z["direction"] == direction for z in new_gaps),
                    sweep_evidence=(sweep_high.get("answer") == "YES" if direction == "bearish"
                                    else sweep_low.get("answer") == "YES"),
                    structure_break=bool(shift["shift"]),
                )

            # ---- counters (a fact about how often a concept appeared)
            if sw:
                concept_hits["swing"] += 1
                concept_hits["liquidity_pool_formed"] += len(sw)
            if new_gaps:
                concept_hits["fvg"] += 1
            if block:
                concept_hits["order_block_created"] += 1
                if block["state"] == "valid":
                    concept_hits["order_block"] += 1
            if sweep_high.get("answer") == "YES" or sweep_low.get("answer") == "YES":
                concept_hits["sweep"] += 1
            if displacement.get("answer") == "YES" and window.t >= 2:
                concept_hits["displacement"] += 1
            if shift["shift"]:
                concept_hits["structure_shift"] += 1
            concept_hits["pool_taken"] += sum(1 for p in pools.pools
                                              if p["state"] == "taken" and p.get("taken_index") == index)

            session = session_now(bar)
            htf_view = htf.view()
            if htf_view["daily"]:
                concept_hits["bias_defined"] += 1

            # ---- decision window
            if decide_from is not None and bar.start < decide_from:
                continue
            if decide_to is not None and bar.start >= decide_to:
                continue
            if max_decisions is not None and counts["decisions"] >= max_decisions:
                break

            dealing_range = ranges.compute(swings, bar.bid_close)
            if dealing_range["position"] != "undefined":
                concept_hits["dealing_range"] += 1
            daily = htf_view["daily"]
            weekly = htf_view["weekly"]
            bias_daily = daily["bias"] if daily else None
            bias_weekly = weekly["bias"] if weekly else None
            # direction comes from the DAILY bias, because that is what the ranking criterion (i)
            # names (DECLARED_CHOICES row 8); the weekly bias is context and a disagreement is
            # recorded as bias_conflict on the decision, not used as a veto.
            bias = bias_daily or bias_weekly
            bias_conflict = bool(bias_daily and bias_weekly and bias_daily != bias_weekly)
            bias_direction = "UP" if bias == "UP" else "DOWN" if bias == "DOWN" else None

            direction_candidates = [d for d in ("bullish", "bearish")
                                    if (d == "bullish" and bias_direction == "UP")
                                    or (d == "bearish" and bias_direction == "DOWN")]
            decision = {
                "index": index,
                "decided_at": bar.start.isoformat(),
                "available_at": bar.end.isoformat(),
                "close": bar.bid_close,
                "bias": {"daily": bias_daily, "weekly": bias_weekly, "resolved": bias,
                         "bias_conflict": bias_conflict,
                         "source": "ict_engine.htf aggregation, completion-labelled"},
                "range": dealing_range,
                "session": session,
                "swings": [{"side": s["side"], "price": s["price"],
                            "level_index": s["level_index"]} for s in sw],
                "fvg": new_gaps,
                "displacement": displacement,
                "sweep": {"high": sweep_high, "low": sweep_low},
                "structure_shift": shift,
                "pools_untaken_high": len(pools.untaken("high")),
                "pools_untaken_low": len(pools.untaken("low")),
                "untaken": [
                    {"side": pool["side"], "level": pool["level"], "kind": pool["kind"],
                     "formed_index": pool["formed_index"],
                     "age_bars": (index - pool["formed_index"]) if pool["formed_index"] >= 0 else None}
                    for pool in (pools.untaken("high") + pools.untaken("low"))
                ][:12],
                "pools_dropped": pools.dropped,
                "zones_dropped": gaps.dropped + blocks.dropped,
            }
            counts["decisions"] += 1

            zone = None
            plan = None
            no_plan_reason = None
            if not direction_candidates:
                no_plan_reason = ("bias_undefined" if not bias
                                  else "bias_conflict" if bias == "CONFLICT" else "bias_flat")
            else:
                direction = direction_candidates[0]
                candidates = gather_zones(direction=direction, gaps=gaps, blocks=blocks,
                                          sweep=(sweep_low if direction == "bullish" else sweep_high),
                                          close=bar.bid_close)
                rg = dealing_range
                ranking = rank_zones(candidates, bias=bias_direction or "",
                                     close=bar.bid_close,
                                     range_high=rg.get("high", bar.bid_close),
                                     range_low=rg.get("low", bar.bid_close))
                targets = targets_ahead(
                    pools.untaken("high" if direction == "bullish" else "low"),
                    entry=bar.bid_close, range_high=rg.get("high", bar.bid_close),
                    range_low=rg.get("low", bar.bid_close), direction=direction,
                    fallback_formed_at=bar.start,
                )
                ctx = {
                    "bias": bias, "bias_daily": bias_daily, "bias_weekly": bias_weekly,
                    "bias_direction": bias_direction, "range": rg, "session": session,
                    "ranking": ranking, "targets": targets, "close": bar.bid_close,
                    "what_would_change": [
                        "a confirmed swing against the thesis",
                        "the opposing pool taken before entry",
                        "a displacement in the opposite direction",
                        "the zone closed through",
                        "the session window ending",
                    ],
                }
                decision["zones_ranked"] = [
                    {"zone_id": z["zone_id"], "kind": z["kind"], "lower": z["lower"],
                     "upper": z["upper"], "fresh": z["fresh"],
                     "bias_agrees": z["bias_agrees"], "distance_ratio": z["distance_ratio"]}
                    for z in ranking["ranked"][:5]]
                decision["criteria"] = ranking["criteria"]
                decision["criteria_conflict"] = ranking["criteria_conflict"]
                opposite = "bearish" if direction == "bullish" else "bullish"
                decision["hypotheses"] = [
                    {"name": f"{direction} continuation with the {bias} daily bias",
                     "for": [f"daily bias {bias_daily}", f"weekly bias {bias_weekly}",
                             f"range position {rg.get('position')}",
                             f"{len(ranking['ranked'])} zone(s) in this direction"],
                     "against": ["the opposing pool may be swept before the entry is reached",
                                 "a bar that spans the zone settles at the stop first (conservative rule)"]},
                    {"name": f"{opposite} reversal / range fade",
                     "for": [f"{len(pools.untaken('high' if opposite == 'bearish' else 'low'))} "
                             f"untaken pool(s) on that side",
                             "opposite zone exists" if gather_zones(
                                 direction=opposite, gaps=gaps, blocks=blocks,
                                 sweep=(sweep_low if opposite == "bullish" else sweep_high),
                                 close=bar.bid_close) else "no opposite zone"],
                     "against": [f"daily bias is {bias_daily}", "no confirmed swing against the thesis yet"]},
                ]
                decision["not_looked_at"] = [
                    "no weekly FVG / weekly order block", "no news or calendar data",
                    "no volume profile", "no other instrument", "no bar after the decision bar",
                ]
                ok, reason_code, detail = gates(ctx=ctx, zones=ranking["ranked"],
                                                direction=direction, entry=bar.bid_close)
                if ok:
                    zone = ranking["ranked"][0]
                    entry = zone["upper"] if direction == "bullish" else zone["lower"]
                    plan = build_plan(decision_index=index, decided_at=bar.start, bar=bar,
                                      zone=zone, entry=entry, ctx=ctx)
                    if "error" in plan:
                        no_plan_reason = plan["error"]
                        plan = None
                    else:
                        tracker.add(plan)
                        counts["plans"] += 1
                        _write_jsonl(fp, plan)
                else:
                    no_plan_reason = reason_code
                    decision["gate_detail"] = detail
                    if len(non_plan_samples) < NON_PLAN_SAMPLE_SIZE:
                        non_plan_samples.append({"index": index, "at": bar.start.isoformat(),
                                                 "reason": reason_code, "detail": detail,
                                                 "close": bar.bid_close,
                                                 "range_position": rg.get("position"),
                                                 "zones": len(ranking["ranked"]),
                                                 "targets": len(targets)})
            if plan is None:
                counts["no_plan"] += 1
                reasons[no_plan_reason or "unknown"] = reasons.get(no_plan_reason or "unknown", 0) + 1
                decision["decision"] = "NO_PLAN"
                decision["reason"] = no_plan_reason
            else:
                decision["decision"] = "HYPOTHETICAL_PLAN"
                decision["plan_id"] = plan["plan_id"]

            # ---- story state and tracking
            decision["story"] = story.update(index=index, bar=bar, ctx={
                "targets": [], "bias": bias, "range": dealing_range}, zone=zone)
            _write_jsonl(fs, decision["story"])
            tracker.update(bar, index)
            _write_jsonl(fd, decision)

            if counts["decisions"] % MEMORY_CHECK_EVERY == 0:
                rss = memory_rss_kb()
                rss_curve.append({"bar": counts["decisions"], "rss_kb": rss})
                if cap_kb is not None and rss is not None and rss > cap_kb:
                    stopped = {"reason": "memory_cap_reached", "rss_kb": rss, "cap_kb": cap_kb,
                               "at_decision": counts["decisions"], "at": bar.start.isoformat()}
                    break

    elapsed = time.time() - started
    summary = {
        "label": label,
        "started_utc": datetime.fromtimestamp(started, UTC).isoformat(),
        "elapsed_seconds": round(elapsed, 3),
        "bars_consumed": counts["bars"],
        "decisions": counts["decisions"],
        "plans": counts["plans"],
        "no_plan": counts["no_plan"],
        "no_plan_reasons": dict(sorted(reasons.items(), key=lambda kv: -kv[1])),
        "concept_hits": concept_hits,
        "pool_dropped_total": pools.dropped,
        "zone_dropped_total": gaps.dropped + blocks.dropped,
        "swing_dropped_total": swings.dropped,
        "window_bars": WINDOW_BARS,
        "memory": {
            "total_kb": total_kb,
            "cap_kb": cap_kb,
            "cap_fraction": MEMORY_CAP_FRACTION,
            "peak_rss_kb": peak_rss_kb(),
            "rss_curve": rss_curve,
        },
        "stopped": stopped,
        "settled_plans": tracker.settled,
        "open_plans": [p["plan_id"] for p in tracker.open],
        "non_plan_samples": non_plan_samples,
        "outputs": {
            "decisions": str(decisions_path),
            "plans": str(plans_path),
            "story": str(story_path),
        },
    }
    (out_dir / "plans_final.jsonl").write_text(
        "".join(json.dumps(p, default=str) + "\n" for p in tracker.settled + tracker.open),
        encoding="utf-8")
    if stopped:
        partial_path.write_text(json.dumps({"status": "PARTIAL", **stopped,
                                            "summary": summary}, indent=1, default=str))
    (out_dir / "run_summary.json").write_text(json.dumps(summary, indent=1, default=str))
    return summary


def iso(text: str) -> datetime:
    return datetime.fromisoformat(text).replace(tzinfo=UTC)
