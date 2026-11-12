"""Reconstruct prefix-only entry and liquidity contexts without changing the engine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from trading_system.ict_engine.data import Candle
from trading_system.ict_engine.htf import HigherTimeframe, htf_trace
from trading_system.ict_engine.liquidity import (
    LiquidityPool,
    PoolEventKind,
    liquidity_trace,
)
from trading_system.ict_engine.market_status import MarketStatus, market_status
from trading_system.ict_engine.narrator import (
    ChartReading,
    DecisionType,
    _daily_pools_for_basis,
    reading_trace,
    select_target,
)
from trading_system.ict_engine.order_blocks import (
    OrderBlockZone,
    order_block_trace,
)
from trading_system.ict_engine.predictions import Prediction, PredictionType
from trading_system.ict_engine.price import ohlc
from trading_system.ict_engine.ranges import RangeObservation, dealing_range_trace
from trading_system.ict_engine.variants import EngineVariant

_ASIDE_REASONS = (
    "touch_violation_collision",
    "range_position",
    "outside_window",
    "invalid_geometry",
    "below_three",
    "no_target",
)
_SETUP_PREFIX = "setup:"
_STAND_ASIDE_INFIX = ":stand_aside:"


@dataclass(frozen=True, slots=True)
class EntryContext:
    variant_id: str
    available_at: datetime
    zone: OrderBlockZone
    prediction: Prediction | None
    aside_reason: str | None
    range_observation: RangeObservation
    active_pools: tuple[LiquidityPool, ...]

    @property
    def direction(self):
        return self.zone.direction

    @property
    def category(self) -> str:
        return "NOT_ASIDE" if self.prediction is not None else "ASIDE"


@dataclass(frozen=True, slots=True)
class VariantContext:
    variant: EngineVariant
    readings: tuple[ChartReading, ...]
    entries: tuple[EntryContext, ...]


def _setup_zone_id(prediction: Prediction) -> str:
    prefix = f"p:{prediction.variant_id}:{_SETUP_PREFIX}"
    if not prediction.prediction_id.startswith(prefix):
        raise ValueError(f"Cannot derive setup zone: {prediction.prediction_id}")
    return prediction.prediction_id[len(prefix) :]


def _aside_zone_and_reason(decision_id: str, variant_id: str) -> tuple[str, str]:
    prefix = f"d:{variant_id}{_STAND_ASIDE_INFIX}"
    if not decision_id.startswith(prefix):
        raise ValueError(f"Cannot parse stand-aside decision: {decision_id}")
    suffix = decision_id[len(prefix) :]
    for reason in _ASIDE_REASONS:
        ending = f":{reason}"
        if suffix.endswith(ending):
            return suffix[: -len(ending)], reason
    raise ValueError(f"Unknown stand-aside reason: {decision_id}")


def build_variant_context(
    candles: tuple[Candle, ...], variant: EngineVariant
) -> VariantContext:
    """Replay pool lifecycle and retain snapshots only at first-touch decisions.

    The ordering mirrors reading_trace: existing daily pools are updated first,
    then ordinary pool events, then newly completed daily pools. Snapshots are
    therefore the exact inputs available to _setup_at_first_touch on that bar.
    """

    readings = reading_trace(candles, variant)
    zones: dict[str, OrderBlockZone] = {}
    predictions: dict[tuple[datetime, str], Prediction] = {}
    asides: dict[tuple[datetime, str], str] = {}
    needed_times: set[datetime] = set()

    for reading in readings:
        for prediction in reading.predictions:
            if prediction.prediction_type is PredictionType.SETUP_TARGET_BEFORE_STOP:
                zone_id = _setup_zone_id(prediction)
                key = (reading.available_at, zone_id)
                predictions[key] = prediction
                needed_times.add(reading.available_at)
        for decision in reading.decisions:
            if decision.decision_type is DecisionType.STAND_ASIDE:
                zone_id, reason = _aside_zone_and_reason(
                    decision.decision_id, variant.variant_id
                )
                key = (reading.available_at, zone_id)
                if key in asides:
                    raise ValueError(f"Duplicate stand-aside context: {key}")
                asides[key] = reason
                needed_times.add(reading.available_at)

    order_blocks = order_block_trace(candles, variant.order_block, variant.basis)
    for events in order_blocks:
        for event in events:
            zones.setdefault(event.zone.zone_id, event.zone)

    missing_zones = {
        zone_id
        for _, zone_id in (*predictions.keys(), *asides.keys())
        if zone_id not in zones
    }
    if missing_zones:
        raise ValueError(f"Entry decisions lack zone objects: {sorted(missing_zones)[:3]}")

    ranges = dealing_range_trace(candles, variant.basis)
    pool_events = liquidity_trace(candles, variant.basis)
    daily = htf_trace(candles, HigherTimeframe.DAILY, variant.daily_anchor)

    active_pools: dict[str, LiquidityPool] = {}
    daily_pool_ids: set[str] = set()
    daily_awaiting_return: dict[str, LiquidityPool] = {}
    snapshots: dict[datetime, tuple[LiquidityPool, ...]] = {}

    for index, candle in enumerate(candles):
        status = market_status(candle)
        _, high, low, close = ohlc(candle, variant.basis)

        for pool_id in tuple(sorted(daily_awaiting_return)):
            pool = daily_awaiting_return[pool_id]
            returned = (pool.side.value == "high" and close < pool.level) or (
                pool.side.value == "low" and close > pool.level
            )
            if status is MarketStatus.MARKET and returned:
                del daily_awaiting_return[pool_id]

        for pool_id in tuple(sorted(daily_pool_ids)):
            pool = active_pools.get(pool_id)
            if pool is None or status is not MarketStatus.MARKET:
                continue
            taken = (pool.side.value == "high" and high > pool.level) or (
                pool.side.value == "low" and low < pool.level
            )
            if not taken:
                continue
            del active_pools[pool_id]
            daily_pool_ids.remove(pool_id)
            returned = (pool.side.value == "high" and close < pool.level) or (
                pool.side.value == "low" and close > pool.level
            )
            if not returned:
                daily_awaiting_return[pool_id] = pool

        for event in pool_events[index]:
            pool = event.pool
            if event.kind is PoolEventKind.FORMED:
                active_pools[pool.pool_id] = pool
            elif event.kind is PoolEventKind.TAKEN:
                active_pools.pop(pool.pool_id, None)

        for completed in daily[index].newly_completed:
            for pool in _daily_pools_for_basis(
                completed, available_at=candle.end, basis=variant.basis
            ):
                active_pools[pool.pool_id] = pool
                daily_pool_ids.add(pool.pool_id)

        if candle.end in needed_times:
            snapshots[candle.end] = tuple(
                active_pools[key] for key in sorted(active_pools)
            )

    keys = sorted(set(predictions) | set(asides))
    entries: list[EntryContext] = []
    candle_by_end = {candle.end: candle for candle in candles}
    index_by_end = {candle.end: index for index, candle in enumerate(candles)}
    for available_at, zone_id in keys:
        prediction = predictions.get((available_at, zone_id))
        reason = asides.get((available_at, zone_id))
        if (prediction is None) == (reason is None):
            raise ValueError(f"Entry must be exactly one of setup/aside: {available_at} {zone_id}")
        zone = zones[zone_id]
        pools = snapshots[available_at]
        range_observation = ranges[index_by_end[available_at]]
        if prediction is not None:
            entry = ohlc(candle_by_end[available_at], variant.basis)[3]
            selected = select_target(
                pools,
                direction=zone.direction,
                entry=entry,
                range_observation=range_observation,
                ranking=variant.target_ranking,
            )
            if selected is None or selected[0].pool_id != prediction.target_id:
                raise ValueError(
                    f"Replayed target differs for {prediction.prediction_id}: "
                    f"{selected[0].pool_id if selected else None} != {prediction.target_id}"
                )
        entries.append(
            EntryContext(
                variant_id=variant.variant_id,
                available_at=available_at,
                zone=zone,
                prediction=prediction,
                aside_reason=reason,
                range_observation=range_observation,
                active_pools=pools,
            )
        )

    return VariantContext(variant=variant, readings=readings, entries=tuple(entries))
