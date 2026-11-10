#!/usr/bin/env python3
"""Zone ranking, hypothetical plans, tracking and the per-bar story state.

Every quantity here is either a fact the primitives in `stream_v1` produced, a value declared in
DECLARED_CHOICES.md, or an explicit KNOWLEDGE_GAP.  The ranking's third criterion is the existing
`ict_engine.liquidity.rank_draws` — the module's own context-relative distance ranking — not a
threshold invented here.
"""

from __future__ import annotations

from datetime import datetime

from stream_v1 import LiquidityState, memory_rss_kb
from trading_system.ict_engine.liquidity import DrawCandidate, rank_draws

# ---------------------------------------------------------------- declared values
PLAN_EXPIRY_BARS = 288            # ENGINEERING_CHOICE, DECLARED_CHOICES row 19 (one trading day)
GATE_RANGE_POSITION = {           # reused gate: narrator.py `_setup_at_first_touch` (claims below)
    "bullish": ("discount", "equilibrium"),
    "bearish": ("premium",),
}
GATE_RANGE_CLAIMS = ("K2C-002", "K2C-003", "K2C-016", "K2C-037", "K2C-038")


# ---------------------------------------------------------------- targets
def targets_ahead(pools: list[dict], *, entry: float, range_high: float, range_low: float,
                  direction: str, fallback_formed_at: datetime) -> list[dict]:
    """T1/T2 by `rank_draws` (relative distance), on the side the trade is aiming at."""

    side = "high" if direction == "bullish" else "low"
    candidates = []
    for pool in pools:
        if pool["side"] != side:
            continue
        ahead = pool["level"] > entry if direction == "bullish" else pool["level"] < entry
        if not ahead:
            continue
        candidates.append(pool)
    if not candidates:
        return []
    draws = [
        DrawCandidate(
            candidate_id=pool["pool_id"],
            kind=pool["kind"],
            lower=pool["level"],
            upper=pool["level"],
            formed_at=pool.get("formed_at", fallback_formed_at),
            timeframe="DAILY" if pool["kind"] == "higher_timeframe_extreme" else "M5",
            claim_ids=tuple(pool.get("claim_ids", ())),
        )
        for pool in candidates
    ]
    recent_range = float(range_high) - float(range_low)
    if recent_range <= 0:
        return []
    ranked = rank_draws(draws, current_price=entry, recent_range=recent_range)
    by_id = {pool["pool_id"]: pool for pool in candidates}
    out = []
    for item in ranked:
        pool = dict(by_id[item.draw.candidate_id])
        pool["distance_ratio"] = item.distance_ratio
        pool["distance_rank"] = item.distance_rank
        pool["timeframe_significance_rank"] = item.timeframe_significance_rank
        out.append(pool)
    return out


# ---------------------------------------------------------------- zones and ranking
def gather_zones(*, direction: str, gaps, blocks, sweep: dict, close: float) -> list[dict]:
    """Every zone that could host an entry in `direction`, with its provenance."""

    zones: list[dict] = []
    for gap in gaps.active(direction):
        zones.append({
            "zone_id": f"fvg:{gap['direction']}:{gap['formed_index']}",
            "kind": "fvg", "direction": gap["direction"],
            "lower": gap["lower"], "upper": gap["upper"],
            "formed_index": gap["formed_index"], "state": gap["state"],
            "freshness": "untouched" if gap["state"] == "untouched" else gap["state"],
            "invalidation": gap["invalidation"],
            "claim_ids": ("B1", "B2", "B3", "B4"),
        })
    for block in blocks.valid(direction):
        zones.append({
            "zone_id": f"ob:{block['direction']}:{block['block_index']}",
            "kind": "order_block", "direction": block["direction"],
            "lower": block["lower"], "upper": block["upper"],
            "formed_index": block["formed_index"], "state": block["state"],
            "freshness": "untouched",
            "invalidation": block.get("invalidation"),
            "claim_ids": tuple(block.get("claim_ids", ())),
        })
    answer = sweep.get("answer")
    if answer == "YES" and sweep.get("level") is not None:
        level = float(sweep["level"])
        # a sweep of highs is a bearish signal and vice versa
        sweep_direction = "bearish" if sweep["side"] == "high" else "bullish"
        if sweep_direction == direction:
            zones.append({
                "zone_id": f"sweep:{sweep['side']}:{sweep['level_index']}",
                "kind": "sweep_level", "direction": sweep_direction,
                "lower": min(level, close), "upper": max(level, close),
                "formed_index": sweep["level_index"], "state": "untouched",
                "freshness": "untouched",
                "invalidation": "sweep wick",
                "claim_ids": tuple(sweep.get("claim_ids", ())),
            })
    return zones


def rank_zones(zones: list[dict], *, bias: str, close: float, range_high: float,
               range_low: float) -> dict:
    """Rank by (i) bias agreement, (ii) freshness, (iii) context-relative distance.

    Returns the ordering *and* whether criteria (i) and (iii) disagree, in which case the caller must
    not pick a winner (DECLARED_CHOICES row 8).
    """

    if not zones:
        return {"ranked": [], "criteria_conflict": False, "reason": "no zone in this direction",
                "by_distance_first": None,
                "criteria": {
                    "i": {"name": "bias agreement with completed daily bias",
                          "tag": "ENGINEERING_CHOICE", "value": None},
                    "ii": {"name": "freshness (never closed through)",
                           "tag": "ENGINEERING_CHOICE", "value": None},
                    "iii": {"name": "context-relative distance (rank_draws ratio)",
                            "tag": "SOURCE_NUMBER", "value": None}},
                "priority": "no_zone"}
    recent_range = float(range_high) - float(range_low)
    scored = []
    for zone in zones:
        mid = (zone["lower"] + zone["upper"]) / 2.0
        distance = abs(mid - close) / recent_range if recent_range > 0 else None
        agrees = ((zone["direction"] == "bullish" and bias == "UP")
                  or (zone["direction"] == "bearish" and bias == "DOWN"))
        fresh = zone.get("freshness") == "untouched"
        scored.append({**zone, "bias_agrees": agrees, "distance_ratio": distance,
                       "fresh": fresh})
    by_bias = sorted(scored, key=lambda z: (not z["bias_agrees"], not z["fresh"],
                                            z["distance_ratio"] if z["distance_ratio"] is not None else 1e9,
                                            z["zone_id"]))
    by_distance = sorted(scored, key=lambda z: (z["distance_ratio"] if z["distance_ratio"] is not None else 1e9,
                                                z["zone_id"]))
    conflict = by_bias[0]["zone_id"] != by_distance[0]["zone_id"] and len(scored) > 1
    return {
        "ranked": by_bias,
        "by_distance_first": by_distance[0]["zone_id"],
        "criteria_conflict": conflict,
        "criteria": {
            "i": {"name": "bias agreement with completed daily bias",
                  "tag": "ENGINEERING_CHOICE", "value": by_bias[0]["bias_agrees"]},
            "ii": {"name": "freshness (never closed through)",
                   "tag": "ENGINEERING_CHOICE", "value": by_bias[0]["fresh"]},
            "iii": {"name": "context-relative distance (rank_draws ratio)",
                    "tag": "SOURCE_NUMBER", "value": by_bias[0]["distance_ratio"]},
        },
        "priority": "KNOWLEDGE_GAP: ZONE_RANKING_PRIORITY" if not conflict else "criteria_conflict",
    }


# ---------------------------------------------------------------- plan construction
def build_plan(*, decision_index: int, decided_at: datetime, bar, zone: dict, entry: float,
               ctx: dict) -> dict:
    """Assemble the hypothetical plan.  All fields are facts or declared values."""

    direction = zone["direction"]
    if direction == "bullish":
        stop = zone["lower"]          # far side of the zone = the block/gap invalidation (row 5)
        stop_rule = f"far side of {zone['kind']}"
    else:
        stop = zone["upper"]
        stop_rule = f"far side of {zone['kind']}"
    if zone["kind"] == "sweep_level":
        # the sweep's own wick is the invalidation, not the zone body
        stop = zone["upper"] if direction == "bearish" else zone["lower"]
        stop_rule = "sweep wick"
    pools = ctx["targets"]
    t1 = pools[0] if pools else None
    t2 = pools[1] if len(pools) > 1 else None
    risk = abs(entry - stop)
    if risk <= 0:
        return {"error": "stop equals entry; no plan"}
    reward1 = abs(t1["level"] - entry) if t1 else None
    reward2 = abs(t2["level"] - entry) if t2 else None
    return {
        "plan_id": f"plan:{decided_at.isoformat()}:{zone['zone_id']}",
        "decided_at": decided_at.isoformat(),
        "decision_index": decision_index,
        "direction": direction,
        "zone": {"zone_id": zone["zone_id"], "kind": zone["kind"],
                 "lower": zone["lower"], "upper": zone["upper"],
                 "formed_index": zone["formed_index"], "claim_ids": list(zone.get("claim_ids", ()))},
        "entry": entry,
        "entry_rule": "touch of the zone edge nearest the trade direction",
        "stop": stop,
        "stop_rule": stop_rule,
        "risk_price": risk,
        "t1": None if t1 is None else {"level": t1["level"], "kind": t1["kind"],
                                       "distance_rank": t1["distance_rank"],
                                       "distance_ratio": t1["distance_ratio"],
                                       "timeframe_significance_rank": t1["timeframe_significance_rank"]},
        "t2": None if t2 is None else {"level": t2["level"], "kind": t2["kind"],
                                       "distance_rank": t2["distance_rank"]},
        "t2_note": None if t2 else "only one untaken opposing pool existed; T2 = None",
        "rr_t1_measured": None if reward1 is None else reward1 / risk,
        "rr_t2_measured": None if reward2 is None else reward2 / risk,
        "rr_is_recorded_never_filtered": True,
        "half_spread_at_decision": bar.spread_open / 2.0,
        "bias": ctx["bias"],
        "range_position": ctx["range"]["position"],
        "session": ctx["session"]["declared_window"],
        "criteria": ctx["ranking"]["criteria"],
        "criteria_conflict": ctx["ranking"]["criteria_conflict"],
        "what_would_change": ctx["what_would_change"],
        "gaps": [
            "KNOWLEDGE_GAP: FVG_INVALIDATION",
            "KNOWLEDGE_GAP: EQUAL_HIGHS_RATIO",
            "KNOWLEDGE_GAP: ZONE_RANKING_PRIORITY",
            "KNOWLEDGE_GAP: DISPLACEMENT_NO_REFERENCE_VARIANT",
            "KNOWLEDGE_GAP: STRUCTURE_SHIFT_QUALIFICATION",
        ],
        "contract_status": "HYPOTHETICAL_NO_EXECUTION_CONTRACT",
        "state": "armed",
        "trigger_index": None,
        "exit_index": None,
        "exit_reason": None,
        "r_measured": None,
    }


def gates(*, ctx: dict, zones: list[dict], direction: str, entry: float) -> tuple[bool, str, dict]:
    """The gate chain, in order.  The first failing gate is the no-plan reason."""

    detail = {}
    if ctx["session"]["in_window"] is not True:
        return False, "outside_session_window", detail
    allowed = GATE_RANGE_POSITION[direction]
    if ctx["range"]["position"] not in allowed:
        return False, f"range_position_{ctx['range']['position']}", {
            "gate_claims": GATE_RANGE_CLAIMS}
    if not zones:
        return False, "no_zone_in_direction", detail
    if ctx["ranking"]["criteria_conflict"]:
        return False, "criteria_conflict", detail
    if not ctx["targets"]:
        return False, "no_target_ahead", detail
    zone = zones[0]
    touched = zone["lower"] <= ctx["close"] <= zone["upper"]
    if not touched:
        return False, "zone_not_touched", {"zone": zone["zone_id"],
                                           "distance": abs(ctx["close"] - zone["upper"])
                                           if direction == "bullish" else abs(zone["lower"] - ctx["close"])}
    if ctx["bias_direction"] != ("UP" if direction == "bullish" else "DOWN"):
        return False, "bias_disagrees", {"bias": ctx["bias"], "bias_daily": ctx["bias_daily"],
                                         "bias_weekly": ctx["bias_weekly"]}
    return True, "plan", detail


# ---------------------------------------------------------------- tracking
class PlanTracker:
    """Bar-by-bar state of every open hypothetical plan, with half-spread cost."""

    EXPIRY = PLAN_EXPIRY_BARS  # ENGINEERING_CHOICE row 19

    def __init__(self) -> None:
        self.open: list[dict] = []
        self.settled: list[dict] = []

    MAX_TRAIL = 320   # ENGINEERING_CHOICE: bounded hindsight trail kept with an open plan

    def add(self, plan: dict) -> None:
        plan.setdefault("exit_trail", [])
        self.open.append(plan)

    def update(self, bar, index: int) -> None:
        still_open = []
        for plan in self.open:
            if plan["state"] in ("armed", "triggered") and len(plan["exit_trail"]) < self.MAX_TRAIL:
                plan["exit_trail"].append({"at": bar.start.isoformat(), "high": bar.bid_high,
                                           "low": bar.bid_low, "close": bar.bid_close,
                                           "state": plan["state"]})
            direction = plan["direction"]
            entry, stop = plan["entry"], plan["stop"]
            t1 = plan["t1"]["level"] if plan["t1"] else None

            if plan["state"] == "armed":
                touched = bar.bid_low <= entry <= bar.bid_high
                if touched:
                    plan["state"] = "triggered"
                    plan["trigger_index"] = index
                    plan["triggered_at"] = bar.start.isoformat()
                elif index - plan["decision_index"] >= self.EXPIRY:
                    plan["state"] = "expired"
                    plan["exit_index"] = index
                    plan["exit_reason"] = "entry_zone_not_touched_within_288_bars"
                    plan["r_measured"] = 0.0
                    self.settled.append(plan)
                    continue
                else:
                    still_open.append(plan)
                    continue

            if plan["state"] != "triggered":
                if plan["state"] == "armed":
                    still_open.append(plan)
                continue

            hit_stop = bar.bid_low <= stop if direction == "bullish" else bar.bid_high >= stop
            hit_target = (bar.bid_high >= t1 if direction == "bullish" else bar.bid_low <= t1) \
                if t1 is not None else False
            # conservative rule (DECLARED_CHOICES row 18): the stop is assumed first
            if hit_stop:
                plan["state"] = "settled_stop"
                plan["exit_index"] = index
                plan["exit_reason"] = "stop_touched"
                plan["exit_price"] = stop
            elif hit_target:
                plan["state"] = "settled_target"
                plan["exit_index"] = index
                plan["exit_reason"] = "t1_touched"
                plan["exit_price"] = t1
            elif index - plan["trigger_index"] >= self.EXPIRY:
                plan["state"] = "expired"
                plan["exit_index"] = index
                plan["exit_reason"] = "neither_stop_nor_target_within_288_bars"
                plan["exit_price"] = bar.bid_close
            if plan["state"] == "triggered":
                still_open.append(plan)
            else:
                risk = abs(entry - stop)
                gross = ((plan["exit_price"] - entry) if direction == "bullish"
                         else (entry - plan["exit_price"]))
                cost = (plan.get("half_spread_at_decision", 0.0) + bar.spread_open / 2.0)
                plan["r_measured"] = (gross - cost) / risk
                plan["cost_price"] = cost
                self.settled.append(plan)
        self.open = still_open


# ---------------------------------------------------------------- story state
class StoryState:
    """What the engine believes at t and why; changes only when evidence changes."""

    def __init__(self) -> None:
        self.current: dict | None = None
        self.changes = 0

    def update(self, *, index: int, bar, ctx: dict, zone: dict | None) -> dict:
        proposed = {
            "direction": zone["direction"] if zone else None,
            "zone": zone["zone_id"] if zone else None,
            "stop": (zone["lower"] if zone and zone["direction"] == "bullish"
                     else zone["upper"] if zone else None),
            "t1": ctx["targets"][0]["level"] if ctx["targets"] else None,
            "t2": ctx["targets"][1]["level"] if len(ctx["targets"]) > 1 else None,
            "bias": ctx["bias"],
            "range_position": ctx["range"]["position"],
        }
        reasons = []
        if self.current is None:
            if proposed["direction"] is None:
                return {"index": index, "at": bar.start.isoformat(), "state": "no_thesis",
                        "reason": "no zone in the bias direction"}
            reasons.append("thesis_opened")
        else:
            for key in ("direction", "zone", "stop", "t1", "t2", "bias", "range_position"):
                if self.current.get(key) != proposed[key]:
                    reasons.append(f"{key}_changed:{self.current.get(key)}->{proposed[key]}")
        if reasons or self.current is None:
            if proposed["direction"] is not None:
                self.current = proposed
                self.changes += 1
                return {"index": index, "at": bar.start.isoformat(), "state": "thesis",
                        "direction": proposed["direction"], "zone": proposed["zone"],
                        "stop": proposed["stop"], "t1": proposed["t1"], "t2": proposed["t2"],
                        "bias": proposed["bias"], "range_position": proposed["range_position"],
                        "changed": bool(reasons), "reasons": reasons or ["thesis_opened"]}
        return {"index": index, "at": bar.start.isoformat(), "state": "carried",
                "direction": (self.current or {}).get("direction"),
                "changed": False, "reasons": []}


def memory_margin_ok(cap_kb: int | None) -> bool:
    rss = memory_rss_kb()
    return cap_kb is None or rss is None or rss < cap_kb
