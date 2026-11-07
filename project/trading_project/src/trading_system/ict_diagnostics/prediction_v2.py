"""Implementation of the three preregistered v2 comparative analyses."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from typing import Any

from trading_system.ict_engine.liquidity import LiquidityPool
from trading_system.ict_engine.narrator import select_target
from trading_system.ict_engine.order_blocks import OrderBlockDirection
from trading_system.ict_engine.predictions import prediction_to_dict
from trading_system.ict_engine.price import ohlc
from trading_system.ict_engine.scoring import MarketBars, Outcome, resolve_market_window
from trading_system.ict_engine.variants import EngineVariant

from .common import ahead_pools, canonical_hash, distribution, iso, pool_distance
from .context import EntryContext

LIQUIDITY_HORIZON = 288
ENTRY_PAIR_HORIZON = 288
ASIDE_HORIZON = 48
LIQUIDITY_SEED = "ICT-2022-LIQUIDITY-FIRST-V2-SEED-001"
ARMS = ("engine", "nearest", "farthest", "random")


def _resolve_first_pool(
    context: EntryContext,
    candidates: tuple[LiquidityPool, ...],
    market: MarketBars,
    variant: EngineVariant,
) -> dict[str, Any]:
    start = market.start_after(context.available_at)
    observed = min(LIQUIDITY_HORIZON, len(market.candles) - start)
    for offset in range(observed):
        candle = market.candles[start + offset]
        _, high, low, _ = ohlc(candle, variant.basis)
        winners = [
            pool
            for pool in candidates
            if (pool.side.value == "high" and high > pool.level)
            or (pool.side.value == "low" and low < pool.level)
        ]
        if len(winners) > 1:
            return {
                "status": "FIRST_TOUCH_TIE",
                "winner_ids": sorted(pool.pool_id for pool in winners),
                "bars": offset + 1,
                "resolved_at": iso(candle.end),
            }
        if len(winners) == 1:
            return {
                "status": "FIRST_POOL",
                "winner_ids": [winners[0].pool_id],
                "bars": offset + 1,
                "resolved_at": iso(candle.end),
            }
    return {
        "status": "TRUNCATED" if observed < LIQUIDITY_HORIZON else "NO_POOL_REACHED",
        "winner_ids": [],
        "bars": observed,
        "resolved_at": iso(market.candles[start + observed - 1].end) if observed else None,
    }


def _random_pool(candidates: tuple[LiquidityPool, ...], cluster_id: str) -> LiquidityPool:
    ordered = sorted(candidates, key=lambda pool: pool.pool_id)
    digest = hashlib.sha256(
        LIQUIDITY_SEED.encode("utf-8") + b"\0" + cluster_id.encode("utf-8")
    ).digest()
    return ordered[int.from_bytes(digest, "big") % len(ordered)]


def liquidity_choice_rows(
    entries: tuple[EntryContext, ...], variant: EngineVariant, market: MarketBars
) -> list[dict[str, Any]]:
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    excluded = {"range_position", "outside_window", "touch_violation_collision", "no_target"}
    for context in entries:
        if context.aside_reason in excluded:
            continue
        start = market.start_after(context.available_at)
        entry = ohlc(market.candles[start - 1], variant.basis)[3]
        candidates = ahead_pools(context.active_pools, context.direction, entry)
        if len(candidates) < 2:
            continue
        selected = select_target(
            context.active_pools,
            direction=context.direction,
            entry=entry,
            range_observation=context.range_observation,
            ranking=variant.target_ranking,
        )
        if selected is None:
            continue
        engine = selected[0]
        nearest = min(candidates, key=lambda pool: (pool_distance(pool, context.direction, entry), pool.pool_id))
        farthest = sorted(candidates, key=lambda pool: (-pool_distance(pool, context.direction, entry), pool.pool_id))[0]
        cluster_id = canonical_hash(
            {
                "variant_id": variant.variant_id,
                "direction": context.direction.value,
                "pool_ids": sorted(pool.pool_id for pool in candidates),
            }
        )
        random = _random_pool(candidates, cluster_id)
        resolution = _resolve_first_pool(context, candidates, market, variant)
        winner = resolution["winner_ids"][0] if resolution["status"] == "FIRST_POOL" else None
        judgeable = resolution["status"] in {"FIRST_POOL", "NO_POOL_REACHED"}
        choices = {"engine": engine, "nearest": nearest, "farthest": farthest, "random": random}
        outcomes = {
            name: ((pool.pool_id == winner) if resolution["status"] == "FIRST_POOL" else False)
            if judgeable
            else None
            for name, pool in choices.items()
        }
        independent = cluster_id not in seen
        seen.add(cluster_id)
        if context.prediction is not None and context.prediction.target_id != engine.pool_id:
            raise ValueError(f"V2 engine target replay mismatch: {context.prediction.prediction_id}")
        rows.append(
            {
                "analysis_id": "LIQUIDITY_FIRST_CHOICE_V2",
                "cluster_id": cluster_id,
                "variant_id": variant.variant_id,
                "available_at": iso(context.available_at),
                "month": context.available_at.strftime("%Y-%m"),
                "direction": context.direction.value,
                "zone_id": context.zone.zone_id,
                "entry": entry,
                "candidate_count": len(candidates),
                "candidates": [
                    {
                        "pool_id": pool.pool_id,
                        "level": pool.level,
                        "kind": pool.kind.value,
                        "timeframe": pool.timeframe,
                        "formed_at": iso(pool.formed_at),
                    }
                    for pool in sorted(candidates, key=lambda item: item.pool_id)
                ],
                "choice_ids": {name: pool.pool_id for name, pool in choices.items()},
                "outcomes": outcomes,
                "independent": independent,
                "resolution": resolution,
                "judgeable": judgeable,
                "overlaps_with_engine": {
                    name: engine.pool_id == choices[name].pool_id for name in ARMS[1:]
                },
            }
        )
    return rows


def liquidity_summary(rows: list[dict[str, Any]], *, independent_only: bool = True) -> dict[str, Any]:
    selected = [row for row in rows if row["independent"] or not independent_only]
    judged = [row for row in selected if row["judgeable"]]
    result: dict[str, Any] = {
        "raw_rows": len(rows),
        "selected_rows": len(selected),
        "judgeable": len(judged),
        "statuses": {
            name: sum(row["resolution"]["status"] == name for row in selected)
            for name in ["FIRST_POOL", "FIRST_TOUCH_TIE", "NO_POOL_REACHED", "TRUNCATED"]
        },
        "descriptive_only": len(selected) < 30,
        "arms": {},
    }
    for arm in ARMS:
        hits = sum(row["outcomes"][arm] is True for row in judged)
        arm_result: dict[str, Any] = {
            "hits": hits,
            "misses": len(judged) - hits,
            "rate": hits / len(judged) if judged else None,
        }
        if arm != "engine":
            overlaps = sum(row["choice_ids"][arm] == row["choice_ids"]["engine"] for row in selected)
            paired = [
                row
                for row in judged
                if row["choice_ids"][arm] != row["choice_ids"]["engine"]
            ]
            engine_hits = sum(row["outcomes"]["engine"] is True for row in paired)
            arm_hits = sum(row["outcomes"][arm] is True for row in paired)
            arm_result.update(
                {
                    "overlap_with_engine": overlaps,
                    "discriminative_paired_count": len(paired),
                    "paired_engine_hits": engine_hits,
                    "paired_arm_hits": arm_hits,
                    "paired_difference": (arm_hits - engine_hits) / len(paired) if paired else None,
                }
            )
        result["arms"][arm] = arm_result
    return result


def _pair_choice(zones: tuple[EntryContext, EntryContext]) -> tuple[EntryContext, EntryContext] | None:
    first, second = zones
    if first.zone.variant is not second.zone.variant:
        return None
    # Current order-block objects are M5. No cross-timeframe object is invented.
    if first.zone.opening == second.zone.opening:
        return None
    if first.direction is OrderBlockDirection.BULLISH:
        return (first, second) if first.zone.opening < second.zone.opening else (second, first)
    return (first, second) if first.zone.opening > second.zone.opening else (second, first)


def entry_pair_rows(
    entries: tuple[EntryContext, ...], variant: EngineVariant, market: MarketBars
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    groups: dict[tuple[Any, ...], list[EntryContext]] = defaultdict(list)
    for context in entries:
        prediction = context.prediction
        if prediction is None:
            continue
        key = (
            context.available_at,
            context.direction.value,
            prediction.entry_price,
            prediction.target_id,
        )
        groups[key].append(context)
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    for key in sorted(groups):
        members = sorted(groups[key], key=lambda item: item.zone.zone_id)
        if len(members) < 2:
            continue
        available_at, direction_name, entry, target_id = key
        if len(members) != 2:
            exclusions.append(
                {
                    "reason": "UNSUPPORTED_SET_SIZE",
                    "variant_id": variant.variant_id,
                    "available_at": iso(available_at),
                    "zone_ids": [item.zone.zone_id for item in members],
                    "size": len(members),
                }
            )
            continue
        pair = (members[0], members[1])
        cluster_id = canonical_hash(
            {
                "variant_id": variant.variant_id,
                "direction": direction_name,
                "zone_ids": sorted(item.zone.zone_id for item in pair),
                "entry": entry,
                "target_id": target_id,
            }
        )
        independent = cluster_id not in seen
        seen.add(cluster_id)
        ranked = _pair_choice(pair)
        start = market.start_after(available_at)
        zone_results = []
        for context in pair:
            resolution = resolve_market_window(
                prediction_to_dict(context.prediction), market.candles, start=start
            )
            outcome = (
                "HOLD"
                if resolution.outcome is Outcome.TRUE
                else "FAIL"
                if resolution.outcome is Outcome.FALSE
                else "UNJUDGEABLE"
            )
            zone_results.append(
                {
                    "zone_id": context.zone.zone_id,
                    "prediction_id": context.prediction.prediction_id,
                    "opening": context.zone.opening,
                    "far_side": context.zone.far_side,
                    "outcome": outcome,
                    "resolved_at": iso(resolution.resolved_at),
                    "bars": resolution.bars_observed,
                }
            )
        identical_geometry = (
            pair[0].zone.opening == pair[1].zone.opening
            and pair[0].zone.far_side == pair[1].zone.far_side
        )
        comparison = "UNRANKED"
        chosen_zone_id = None
        other_zone_id = None
        if ranked is not None:
            chosen_zone_id = ranked[0].zone.zone_id
            other_zone_id = ranked[1].zone.zone_id
            if identical_geometry:
                comparison = "IDENTICAL_GEOMETRY"
            elif any(item["outcome"] == "UNJUDGEABLE" for item in zone_results):
                comparison = "UNJUDGEABLE"
            else:
                chosen = next(item for item in zone_results if item["zone_id"] == chosen_zone_id)
                other = next(item for item in zone_results if item["zone_id"] == other_zone_id)
                if chosen["outcome"] == "HOLD" and other["outcome"] == "HOLD":
                    comparison = "BOTH_HOLD"
                elif chosen["outcome"] == "FAIL" and other["outcome"] == "FAIL":
                    comparison = "BOTH_FAIL"
                elif chosen["outcome"] == "HOLD":
                    comparison = "CHOSEN_ONLY"
                else:
                    comparison = "OTHER_ONLY"
        rows.append(
            {
                "analysis_id": "ENTRY_ZONE_PAIR_HOLD_V2",
                "cluster_id": cluster_id,
                "variant_id": variant.variant_id,
                "available_at": iso(available_at),
                "month": available_at.strftime("%Y-%m"),
                "direction": direction_name,
                "entry": entry,
                "target_id": target_id,
                "zone_results": zone_results,
                "chosen_zone_id": chosen_zone_id,
                "other_zone_id": other_zone_id,
                "comparison": comparison,
                "identical_geometry": identical_geometry,
                "independent": independent,
            }
        )
    return rows, exclusions


def entry_pair_summary(rows: list[dict[str, Any]], *, independent_only: bool = True) -> dict[str, Any]:
    selected = [row for row in rows if row["independent"] or not independent_only]
    ranked = [
        row
        for row in selected
        if row["chosen_zone_id"] is not None
        and not row["identical_geometry"]
        and row["comparison"] in {"BOTH_HOLD", "BOTH_FAIL", "CHOSEN_ONLY", "OTHER_ONLY"}
    ]
    chosen_holds = sum(row["comparison"] in {"BOTH_HOLD", "CHOSEN_ONLY"} for row in ranked)
    other_holds = sum(row["comparison"] in {"BOTH_HOLD", "OTHER_ONLY"} for row in ranked)
    return {
        "raw_rows": len(rows),
        "selected_rows": len(selected),
        "comparisons": {
            name: sum(row["comparison"] == name for row in selected)
            for name in ["BOTH_HOLD", "BOTH_FAIL", "CHOSEN_ONLY", "OTHER_ONLY", "UNRANKED", "UNJUDGEABLE", "IDENTICAL_GEOMETRY"]
        },
        "ranked_judgeable_pairs": len(ranked),
        "chosen_holds": chosen_holds,
        "other_holds": other_holds,
        "chosen_rate": chosen_holds / len(ranked) if ranked else None,
        "other_rate": other_holds / len(ranked) if ranked else None,
        "difference": (chosen_holds - other_holds) / len(ranked) if ranked else None,
        "descriptive_only": len(selected) < 30,
    }


def stand_aside_rows(
    entries: tuple[EntryContext, ...], variant: EngineVariant, market: MarketBars
) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[EntryContext]] = defaultdict(list)
    for context in entries:
        key = (context.available_at, context.direction.value, context.category)
        groups[key].append(context)
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    for key in sorted(groups):
        available_at, direction_name, category = key
        members = sorted(groups[key], key=lambda item: item.zone.zone_id)
        direction = members[0].direction
        zone_ids = sorted(item.zone.zone_id for item in members)
        reasons = sorted(item.aside_reason or "" for item in members)
        cluster_id = canonical_hash(
            {
                "variant_id": variant.variant_id,
                "direction": direction_name,
                "category": category,
                "zone_ids": zone_ids,
                "reasons": reasons,
            }
        )
        independent = cluster_id not in seen
        seen.add(cluster_id)
        start = market.start_after(available_at)
        entry = ohlc(market.candles[start - 1], variant.basis)[3]
        observed = min(ASIDE_HORIZON, len(market.candles) - start)
        mfe = 0.0
        mae = 0.0
        for candle in market.candles[start : start + observed]:
            _, high, low, _ = ohlc(candle, variant.basis)
            if direction is OrderBlockDirection.BULLISH:
                mfe = max(mfe, high - entry)
                mae = max(mae, entry - low)
            else:
                mfe = max(mfe, entry - low)
                mae = max(mae, high - entry)
        truncated = observed < ASIDE_HORIZON
        terminal = None
        if not truncated:
            close = ohlc(market.candles[start + ASIDE_HORIZON - 1], variant.basis)[3]
            terminal = close - entry if direction is OrderBlockDirection.BULLISH else entry - close
        rows.append(
            {
                "analysis_id": "STAND_ASIDE_EXCURSION_V2",
                "cluster_id": cluster_id,
                "variant_id": variant.variant_id,
                "available_at": iso(available_at),
                "month": available_at.strftime("%Y-%m"),
                "direction": direction_name,
                "category": category,
                "zone_ids": zone_ids,
                "reasons": reasons,
                "entry": entry,
                "observed_bars": observed,
                "truncated": truncated,
                "mfe": mfe,
                "mae": mae,
                "terminal": terminal,
                "independent": independent,
            }
        )
    return rows


def stand_aside_summary(rows: list[dict[str, Any]], *, independent_only: bool = True) -> dict[str, Any]:
    selected = [row for row in rows if row["independent"] or not independent_only]
    complete = [row for row in selected if not row["truncated"]]
    result: dict[str, Any] = {
        "raw_rows": len(rows),
        "selected_rows": len(selected),
        "truncated": sum(row["truncated"] for row in selected),
        "descriptive_only": len(selected) < 30,
        "categories": {},
    }
    for category in ["ASIDE", "NOT_ASIDE"]:
        group = [row for row in complete if row["category"] == category]
        result["categories"][category] = {
            "count": len(group),
            "mfe": distribution([row["mfe"] for row in group]),
            "mae": distribution([row["mae"] for row in group]),
            "terminal": distribution([row["terminal"] for row in group]),
        }
    for metric in ["mfe", "mae", "terminal"]:
        aside = result["categories"]["ASIDE"][metric]["median"]
        not_aside = result["categories"]["NOT_ASIDE"][metric]["median"]
        result[f"{metric}_median_difference"] = aside - not_aside if aside is not None and not_aside is not None else None
    return result
