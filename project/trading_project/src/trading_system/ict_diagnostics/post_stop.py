"""Per-case post-stop paths and target audit under the frozen diagnostic contract."""

from __future__ import annotations

from statistics import median
from typing import Any

from trading_system.ict_engine.liquidity import rank_draws, pool_draw
from trading_system.ict_engine.order_blocks import OrderBlockDirection
from trading_system.ict_engine.predictions import prediction_to_dict
from trading_system.ict_engine.price import PriceBasis, ohlc
from trading_system.ict_engine.scoring import MarketBars, Outcome, resolve_market_window
from trading_system.ict_engine.variants import EngineVariant, TargetRanking

from .common import ahead_pools, distribution, iso, pool_distance
from .context import EntryContext

ORIGINAL_HORIZON = 288
EXTENDED_HORIZON = 1152
NOISE_BARS = 48
SLOW_RATIO = 4.0


def _favorable_adverse(
    candle, basis: PriceBasis, direction: OrderBlockDirection, entry: float
) -> tuple[float, float]:
    _, high, low, _ = ohlc(candle, basis)
    if direction is OrderBlockDirection.BULLISH:
        return max(high - entry, 0.0), max(entry - low, 0.0)
    return max(entry - low, 0.0), max(high - entry, 0.0)


def _target_hit(candle, basis: PriceBasis, direction: OrderBlockDirection, target: float) -> bool:
    _, high, low, _ = ohlc(candle, basis)
    return high > target if direction is OrderBlockDirection.BULLISH else low < target


def _stop_hit(candle, basis: PriceBasis, direction: OrderBlockDirection, stop: float) -> bool:
    _, high, low, _ = ohlc(candle, basis)
    return low < stop if direction is OrderBlockDirection.BULLISH else high > stop


def _extreme_before(
    candles,
    basis: PriceBasis,
    direction: OrderBlockDirection,
    entry: float,
) -> dict[str, Any]:
    best = 0.0
    worst = 0.0
    best_at = None
    worst_at = None
    for candle in candles:
        favorable, adverse = _favorable_adverse(candle, basis, direction, entry)
        if favorable > best:
            best = favorable
            best_at = candle.end
        if adverse > worst:
            worst = adverse
            worst_at = candle.end
    return {
        "bars": len(candles),
        "best_favorable": best,
        "best_favorable_at": iso(best_at),
        "worst_adverse": worst,
        "worst_adverse_at": iso(worst_at),
    }


def target_audit(context: EntryContext, variant: EngineVariant) -> dict[str, Any]:
    prediction = context.prediction
    assert prediction is not None
    entry = float(prediction.entry_price)
    candidates = ahead_pools(context.active_pools, context.direction, entry)
    by_id = {pool.pool_id: pool for pool in candidates}
    if prediction.target_id not in by_id:
        raise ValueError(f"Target absent from replayed candidates: {prediction.prediction_id}")
    target = by_id[prediction.target_id]
    dealing_range = context.range_observation.dealing_range
    if dealing_range is None:
        raise ValueError(f"Setup lacks dealing range: {prediction.prediction_id}")
    ranked = rank_draws(
        tuple(pool_draw(pool) for pool in candidates),
        current_price=entry,
        recent_range=dealing_range.high - dealing_range.low,
    )
    rank_by_id = {item.draw.candidate_id: item.distance_rank for item in ranked}
    nearest = min(candidates, key=lambda pool: (pool_distance(pool, context.direction, entry), pool.pool_id))
    target_distance = pool_distance(target, context.direction, entry)
    nearest_distance = pool_distance(nearest, context.direction, entry)
    is_nearest = target.pool_id == nearest.pool_id
    if is_nearest:
        consequence = "SELECTED_IS_NEAREST"
    elif variant.target_ranking is TargetRanking.DAILY_THEN_DISTANCE and target.timeframe == "DAILY":
        consequence = "DAILY_PRIORITY_RULE_CONSEQUENCE"
    elif variant.target_ranking is TargetRanking.DISTANCE_ONLY:
        # Equal-distance ordering also includes formation time inside rank_draws.
        tied = [pool for pool in candidates if pool_distance(pool, context.direction, entry) == nearest_distance]
        consequence = "DISTANCE_TIE_RULE_CONSEQUENCE" if len(tied) > 1 and target_distance == nearest_distance else "REPLAY_MISMATCH_NEEDS_AUDIT"
    else:
        consequence = "REPLAY_MISMATCH_NEEDS_AUDIT"
    return {
        "target_id": target.pool_id,
        "target_kind": target.kind.value,
        "target_timeframe": target.timeframe,
        "target_definition_id": target.definition_id,
        "target_formed_at": iso(target.formed_at),
        "target_source_time": iso(target.source_time),
        "target_claim_ids": list(target.claim_ids),
        "target_distance": target_distance,
        "candidate_count": len(candidates),
        "distance_rank": rank_by_id[target.pool_id],
        "nearest_pool_id": nearest.pool_id,
        "nearest_pool_kind": nearest.kind.value,
        "nearest_pool_timeframe": nearest.timeframe,
        "nearest_pool_distance": nearest_distance,
        "selected_is_nearest": is_nearest,
        "selected_minus_nearest_distance": target_distance - nearest_distance,
        "rule_consequence": consequence,
    }


def analyze_post_stop_case(
    context: EntryContext, variant: EngineVariant, market: MarketBars
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    prediction = context.prediction
    if prediction is None:
        raise ValueError("Post-stop analysis requires a complete setup prediction")
    row = prediction_to_dict(prediction)
    start = market.start_after(prediction.available_at)
    entry_index = start - 1
    resolution = resolve_market_window(row, market.candles, start=start)
    direction = context.direction
    basis = variant.basis
    entry = float(prediction.entry_price)
    target = float(prediction.target_price)
    stop = float(prediction.stop_price)
    target_distance = target - entry if direction is OrderBlockDirection.BULLISH else entry - target
    stop_distance = entry - stop if direction is OrderBlockDirection.BULLISH else stop - entry
    if target_distance <= 0 or stop_distance <= 0:
        raise ValueError(f"Invalid setup geometry: {prediction.prediction_id}")

    original_end = start + resolution.bars_observed
    resolved_index = original_end - 1 if resolution.bars_observed else None
    original_kind = ""
    if resolution.outcome is Outcome.TRUE:
        original_kind = "TARGET_FIRST"
    elif resolution.outcome is Outcome.UNJUDGEABLE_SAME_BAR:
        original_kind = "UNJUDGEABLE_SAME_BAR"
    elif resolution.outcome is Outcome.UNJUDGEABLE_TRUNCATED:
        original_kind = "TRUNCATED"
    elif resolved_index is not None and _stop_hit(market.candles[resolved_index], basis, direction, stop):
        original_kind = "STOP_FIRST"
    else:
        original_kind = "HORIZON_EXPIRED"

    stop_index = resolved_index if original_kind == "STOP_FIRST" else None
    extended_target_index = None
    extended_end = min(start + EXTENDED_HORIZON, len(market.candles))
    if stop_index is not None:
        for index in range(stop_index + 1, extended_end):
            if _target_hit(market.candles[index], basis, direction, target):
                extended_target_index = index
                break

    extended_complete = start + EXTENDED_HORIZON <= len(market.candles)
    target_after_original = bool(
        extended_target_index is not None and extended_target_index < start + ORIGINAL_HORIZON
    )
    if original_kind == "STOP_FIRST":
        if extended_target_index is not None:
            primary_class = "DIRECTION-RIGHT-STOP-TOO-TIGHT"
        elif not extended_complete:
            primary_class = "UNRESOLVED"
        else:
            moved_away = any(
                _stop_hit(candle, basis, direction, stop)
                for candle in market.candles[stop_index + 1 : start + EXTENDED_HORIZON]
            )
            primary_class = "DIRECTION-WRONG" if moved_away else "UNRESOLVED"
    elif original_kind in {"HORIZON_EXPIRED", "TRUNCATED", "UNJUDGEABLE_SAME_BAR"}:
        primary_class = "UNRESOLVED"
    else:
        primary_class = "TARGET_FIRST"

    pre_stop = _extreme_before(
        market.candles[start:stop_index] if stop_index is not None else (),
        basis,
        direction,
        entry,
    )
    pre_stop["best_fraction_of_target"] = pre_stop["best_favorable"] / target_distance
    pre_stop["best_multiple_of_stop"] = pre_stop["best_favorable"] / stop_distance
    pre_stop["worst_multiple_of_stop"] = pre_stop["worst_adverse"] / stop_distance

    final_target_index = None
    if original_kind == "TARGET_FIRST":
        final_target_index = resolved_index
    elif extended_target_index is not None:
        final_target_index = extended_target_index
    before_target = None
    if final_target_index is not None:
        before_target = _extreme_before(
            market.candles[start:final_target_index], basis, direction, entry
        )
        before_target["worst_multiple_of_stop"] = before_target["worst_adverse"] / stop_distance
        before_target["before_stop"] = pre_stop
        if stop_index is not None:
            before_target["from_stop_to_before_target"] = _extreme_before(
                market.candles[stop_index:final_target_index], basis, direction, entry
            )

    noise_start = max(0, entry_index - NOISE_BARS)
    preceding = market.candles[noise_start:entry_index]
    ranges = [ohlc(candle, basis)[1] - ohlc(candle, basis)[2] for candle in preceding]
    typical_range = median(ranges) if len(ranges) == NOISE_BARS else None
    entry_candle = market.candles[entry_index]
    entry_spread = entry_candle.ask_close - entry_candle.bid_close
    noise = {
        "preceding_bars": len(preceding),
        "median_bar_range": typical_range,
        "stop_to_median_range": stop_distance / typical_range if typical_range and typical_range > 0 else None,
        "entry_spread": entry_spread,
        "stop_to_spread": stop_distance / entry_spread if entry_spread > 0 else None,
        "stop_smaller_than_typical_bar": stop_distance < typical_range if typical_range and typical_range > 0 else None,
    }

    zone = context.zone
    lower = min(zone.opening, zone.far_side)
    upper = max(zone.opening, zone.far_side)
    width = upper - lower
    _, entry_high, entry_low, _ = ohlc(entry_candle, basis)
    tested = entry_high > lower and entry_low < upper
    penetration = None
    if width > 0:
        penetration = (zone.opening - entry_low) / width if direction is OrderBlockDirection.BULLISH else (entry_high - zone.opening) / width

    zone_event_end = stop_index if stop_index is not None else resolved_index
    reacted = False
    reaction_at = None
    if zone_event_end is not None:
        for candle in market.candles[start:zone_event_end]:
            close = ohlc(candle, basis)[3]
            if (direction is OrderBlockDirection.BULLISH and close > upper) or (
                direction is OrderBlockDirection.BEARISH and close < lower
            ):
                reacted = True
                reaction_at = candle.end
                break
    if original_kind == "TARGET_FIRST":
        reacted = True
        reaction_at = reaction_at or resolution.resolved_at
    sliced = original_kind == "STOP_FIRST"
    if original_kind in {"TRUNCATED", "UNJUDGEABLE_SAME_BAR"} or width <= 0:
        zone_class = "ZONE_UNRESOLVED"
    elif sliced and reacted:
        zone_class = "REACTION_THEN_SLICE"
    elif sliced:
        zone_class = "DIRECT_SLICE"
    elif reacted:
        zone_class = "REACTION_NO_STOP"
    else:
        zone_class = "NO_REACTION_NO_STOP"
    zone_result = {
        "tested": tested,
        "lower": lower,
        "upper": upper,
        "width": width,
        "entry_penetration_fraction": penetration,
        "reacted_before_stop_or_resolution": reacted,
        "reaction_at": iso(reaction_at),
        "sliced": sliced,
        "class": zone_class,
    }

    entry_to_stop = stop_index - start + 1 if stop_index is not None else None
    stop_to_target = extended_target_index - stop_index if extended_target_index is not None and stop_index is not None else None
    slow = bool(stop_to_target is not None and entry_to_stop and stop_to_target > SLOW_RATIO * entry_to_stop)
    post_stop = {
        "stop_at": iso(market.candles[stop_index].end) if stop_index is not None else None,
        "entry_to_stop_bars": entry_to_stop,
        "extended_horizon_bars": EXTENDED_HORIZON,
        "extended_complete": extended_complete,
        "observed_until": iso(market.candles[extended_end - 1].end) if stop_index is not None and extended_end > start else None,
        "target_after_stop_within_original": target_after_original,
        "target_after_stop_within_extended": extended_target_index is not None,
        "target_after_stop_at": iso(market.candles[extended_target_index].end) if extended_target_index is not None else None,
        "entry_to_later_target_bars": extended_target_index - start + 1 if extended_target_index is not None else None,
        "stop_to_target_bars": stop_to_target,
        "stop_to_target_over_entry_to_stop": stop_to_target / entry_to_stop if stop_to_target is not None and entry_to_stop else None,
        "slow": slow,
        "never_reached_complete_original": stop_index is not None and not target_after_original and start + ORIGINAL_HORIZON <= len(market.candles),
        "never_reached_complete_extended": stop_index is not None and extended_target_index is None and extended_complete,
        "truncated_after_stop": stop_index is not None and extended_target_index is None and not extended_complete,
    }

    case = {
        "case_id": prediction.prediction_id,
        "prediction_id": prediction.prediction_id,
        "variant_id": variant.variant_id,
        "available_at": iso(prediction.available_at),
        "month": prediction.available_at.strftime("%Y-%m"),
        "direction": direction.value,
        "basis": basis.value,
        "entry_price": entry,
        "target_price": target,
        "stop_price": stop,
        "target_distance": target_distance,
        "stop_distance": stop_distance,
        "observed_reward_risk": target_distance / stop_distance,
        "original": {
            "outcome": original_kind,
            "resolved_at": iso(resolution.resolved_at),
            "bars_from_entry": resolution.bars_observed,
            "engine_outcome": resolution.outcome.value,
        },
        "primary_class": primary_class,
        "post_stop": post_stop,
        "before_stop": pre_stop,
        "before_target": before_target,
        "noise": noise,
        "zone": zone_result,
        "target_audit": target_audit(context, variant),
    }

    if stop_index is not None:
        record_end = extended_target_index + 1 if extended_target_index is not None else extended_end
    else:
        record_end = original_end
    candle_rows: list[dict[str, Any]] = []
    best = 0.0
    worst = 0.0
    for index in range(entry_index, record_end):
        candle = market.candles[index]
        offset = index - entry_index
        if index >= start:
            favorable, adverse = _favorable_adverse(candle, basis, direction, entry)
            best = max(best, favorable)
            worst = max(worst, adverse)
        else:
            favorable = adverse = 0.0
        op, high, low, close = ohlc(candle, basis)
        candle_rows.append(
            {
                "case_id": prediction.prediction_id,
                "variant_id": variant.variant_id,
                "bar_from_entry": offset,
                "start": iso(candle.start),
                "end": iso(candle.end),
                "bid_open": candle.bid_open,
                "bid_high": candle.bid_high,
                "bid_low": candle.bid_low,
                "bid_close": candle.bid_close,
                "ask_open": candle.ask_open,
                "ask_high": candle.ask_high,
                "ask_low": candle.ask_low,
                "ask_close": candle.ask_close,
                "basis_open": op,
                "basis_high": high,
                "basis_low": low,
                "basis_close": close,
                "close_spread": candle.ask_close - candle.bid_close,
                "in_resolution_window": index >= start,
                "raw_target_touch": _target_hit(candle, basis, direction, target),
                "raw_stop_touch": _stop_hit(candle, basis, direction, stop),
                "favorable_this_bar": favorable,
                "adverse_this_bar": adverse,
                "cumulative_favorable": best,
                "cumulative_adverse": worst,
                "bars_from_stop": offset - entry_to_stop if entry_to_stop is not None and offset > entry_to_stop else None,
                "zone_close_reaction": (close > upper if direction is OrderBlockDirection.BULLISH else close < lower) if index >= start else False,
            }
        )
    return case, candle_rows


def summarise_post_stop(cases: list[dict[str, Any]]) -> dict[str, Any]:
    stopped = [case for case in cases if case["original"]["outcome"] == "STOP_FIRST"]
    ratios = [case["observed_reward_risk"] for case in cases]
    return {
        "cases": len(cases),
        "original_outcomes": {
            name: sum(case["original"]["outcome"] == name for case in cases)
            for name in ["TARGET_FIRST", "STOP_FIRST", "HORIZON_EXPIRED", "UNJUDGEABLE_SAME_BAR", "TRUNCATED"]
        },
        "classes": {
            name: sum(case["primary_class"] == name for case in stopped)
            for name in ["DIRECTION-RIGHT-STOP-TOO-TIGHT", "DIRECTION-WRONG", "UNRESOLVED"]
        },
        "slow": sum(case["post_stop"]["slow"] for case in stopped),
        "target_after_stop_original": sum(case["post_stop"]["target_after_stop_within_original"] for case in stopped),
        "target_after_stop_extended": sum(case["post_stop"]["target_after_stop_within_extended"] for case in stopped),
        "reward_risk_output": distribution(ratios),
        "zones": {
            name: sum(case["zone"]["class"] == name for case in cases)
            for name in ["REACTION_THEN_SLICE", "DIRECT_SLICE", "REACTION_NO_STOP", "NO_REACTION_NO_STOP", "ZONE_UNRESOLVED"]
        },
    }
