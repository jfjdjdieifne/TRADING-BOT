"""Relative-equality pools, old extremes, runs, and unfilled draws."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .data import Candle
from .gaps import FairValueGap
from .market_status import MarketStatus, market_status
from .price import PriceBasis, ohlc
from .swings import SwingPoint, SwingSide, swing_trace


class PoolKind(str, Enum):
    OLD_EXTREME = "old_extreme"
    RELATIVE_EQUAL_PAIR = "relative_equal_pair"
    HIGHER_TIMEFRAME_EXTREME = "higher_timeframe_extreme"


class PoolEventKind(str, Enum):
    FORMED = "formed"
    TAKEN = "taken"
    RETURNED_INSIDE = "returned_inside"


@dataclass(frozen=True, slots=True)
class LiquidityPool:
    pool_id: str
    side: SwingSide
    kind: PoolKind
    level: float
    member_levels: tuple[float, ...]
    formed_at: datetime
    source_time: datetime
    timeframe: str
    equality_ratio: float | None
    cleanliness_rank: int | None
    intervening_market_bars: int | None
    claim_ids: tuple[str, ...]
    definition_id: str


@dataclass(frozen=True, slots=True)
class PoolEvent:
    kind: PoolEventKind
    pool: LiquidityPool
    available_at: datetime
    claim_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DrawCandidate:
    candidate_id: str
    kind: str
    lower: float
    upper: float
    formed_at: datetime
    timeframe: str
    claim_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RankedDraw:
    draw: DrawCandidate
    distance_ratio: float | None
    distance_rank: int
    timeframe_significance_rank: int | None


def _claims_for(side: SwingSide, kind: PoolKind) -> tuple[str, ...]:
    if kind is PoolKind.OLD_EXTREME:
        return ("U0004", "U0012") if side is SwingSide.HIGH else ("U0004", "U0016", "U0017")
    if kind is PoolKind.HIGHER_TIMEFRAME_EXTREME:
        return ("U0004", "U0024", "U0025")
    return ("U0008", "U0022", "U0027") if side is SwingSide.HIGH else ("U0030", "U0032", "U0035")


def _pool_id(side: SwingSide, kind: PoolKind, source_time: datetime, level: float) -> str:
    return f"pool:{side.value}:{kind.value}:{source_time.isoformat()}:{level:.12g}"


def liquidity_trace(
    candles: Sequence[Candle], basis: PriceBasis = PriceBasis.BID
) -> tuple[tuple[PoolEvent, ...], ...]:
    """Form old-extreme and nearest-prior-pair pools without an equality cutoff."""

    swings = swing_trace(candles, basis)
    active: dict[str, LiquidityPool] = {}
    awaiting_return: dict[str, LiquidityPool] = {}
    previous_by_side: dict[SwingSide, SwingPoint] = {}
    trace: list[tuple[PoolEvent, ...]] = []

    for candle, new_swings in zip(candles, swings, strict=True):
        events: list[PoolEvent] = []
        if market_status(candle) is MarketStatus.MARKET:
            _, high, low, close = ohlc(candle, basis)

            for pool_id in tuple(sorted(awaiting_return)):
                pool = awaiting_return[pool_id]
                returned = (
                    pool.side is SwingSide.HIGH and close < pool.level
                ) or (
                    pool.side is SwingSide.LOW and close > pool.level
                )
                if returned:
                    events.append(
                        PoolEvent(
                            PoolEventKind.RETURNED_INSIDE,
                            pool,
                            candle.end,
                            ("U0011", "U0013") if pool.side is SwingSide.HIGH else ("U0019", "U0029"),
                        )
                    )
                    del awaiting_return[pool_id]

            for pool_id in tuple(sorted(active)):
                pool = active[pool_id]
                taken = (
                    pool.side is SwingSide.HIGH and high > pool.level
                ) or (
                    pool.side is SwingSide.LOW and low < pool.level
                )
                if not taken:
                    continue
                events.append(
                    PoolEvent(
                        PoolEventKind.TAKEN,
                        pool,
                        candle.end,
                        ("U0011", "U0026") if pool.side is SwingSide.HIGH else ("U0016", "U0035"),
                    )
                )
                del active[pool_id]
                returned = (
                    pool.side is SwingSide.HIGH and close < pool.level
                ) or (
                    pool.side is SwingSide.LOW and close > pool.level
                )
                if returned:
                    events.append(
                        PoolEvent(
                            PoolEventKind.RETURNED_INSIDE,
                            pool,
                            candle.end,
                            ("U0011", "U0013") if pool.side is SwingSide.HIGH else ("U0019", "U0029"),
                        )
                    )
                else:
                    awaiting_return[pool_id] = pool

            for swing in new_swings:
                single = LiquidityPool(
                    pool_id=_pool_id(swing.side, PoolKind.OLD_EXTREME, swing.source_time, swing.price),
                    side=swing.side,
                    kind=PoolKind.OLD_EXTREME,
                    level=swing.price,
                    member_levels=(swing.price,),
                    formed_at=candle.end,
                    source_time=swing.source_time,
                    timeframe="M5",
                    equality_ratio=None,
                    cleanliness_rank=None,
                    intervening_market_bars=None,
                    claim_ids=_claims_for(swing.side, PoolKind.OLD_EXTREME),
                    definition_id="OLD_CONFIRMED_SWING_EXTREME",
                )
                active[single.pool_id] = single
                events.append(PoolEvent(PoolEventKind.FORMED, single, candle.end, single.claim_ids))

                previous = previous_by_side.get(swing.side)
                opposite = previous_by_side.get(
                    SwingSide.LOW if swing.side is SwingSide.HIGH else SwingSide.HIGH
                )
                if previous is not None:
                    amplitude = (
                        abs(swing.price - opposite.price)
                        if opposite is not None and swing.price != opposite.price
                        else None
                    )
                    ratio = (
                        abs(swing.price - previous.price) / amplitude
                        if amplitude is not None
                        else None
                    )
                    rank = (
                        1 + sum(
                            other.equality_ratio < ratio
                            for other in active.values()
                            if other.kind is PoolKind.RELATIVE_EQUAL_PAIR
                            and other.side is swing.side
                            and other.equality_ratio is not None
                        )
                        if ratio is not None
                        else None
                    )
                    level = (
                        max(swing.price, previous.price)
                        if swing.side is SwingSide.HIGH
                        else min(swing.price, previous.price)
                    )
                    pair = LiquidityPool(
                        pool_id=_pool_id(swing.side, PoolKind.RELATIVE_EQUAL_PAIR, swing.source_time, level),
                        side=swing.side,
                        kind=PoolKind.RELATIVE_EQUAL_PAIR,
                        level=level,
                        member_levels=(previous.price, swing.price),
                        formed_at=candle.end,
                        source_time=swing.source_time,
                        timeframe="M5",
                        equality_ratio=ratio,
                        cleanliness_rank=rank,
                        intervening_market_bars=swing.market_ordinal - previous.market_ordinal,
                        claim_ids=_claims_for(swing.side, PoolKind.RELATIVE_EQUAL_PAIR),
                        definition_id="ENGINEERING_HYPOTHESIS_NEAREST_PRIOR_RELATIVE_EQUAL_PAIR",
                    )
                    active[pair.pool_id] = pair
                    events.append(PoolEvent(PoolEventKind.FORMED, pair, candle.end, pair.claim_ids))
                previous_by_side[swing.side] = swing
        trace.append(tuple(events))
    return tuple(trace)


def pool_draw(pool: LiquidityPool) -> DrawCandidate:
    return DrawCandidate(
        candidate_id=pool.pool_id,
        kind=pool.kind.value,
        lower=pool.level,
        upper=pool.level,
        formed_at=pool.formed_at,
        timeframe=pool.timeframe,
        claim_ids=pool.claim_ids,
    )


def gap_draw(gap: FairValueGap) -> DrawCandidate:
    return DrawCandidate(
        candidate_id=gap.gap_id,
        kind="unfilled_fair_value_gap",
        lower=gap.lower,
        upper=gap.upper,
        formed_at=gap.created_at,
        timeframe="M5",
        claim_ids=("U0005",),
    )


def _distance(draw: DrawCandidate, price: float) -> float:
    if price < draw.lower:
        return draw.lower - price
    if price > draw.upper:
        return price - draw.upper
    return 0.0


def rank_draws(
    draws: Sequence[DrawCandidate], *, current_price: float, recent_range: float
) -> tuple[RankedDraw, ...]:
    """Rank untouched inputs by relative distance; expose timeframe rank separately."""

    if recent_range <= 0:
        raise ValueError("recent_range must be positive")
    if not draws:
        return ()
    ratios = {
        draw.candidate_id: _distance(draw, current_price) / recent_range
        for draw in draws
    }
    ordered = sorted(
        draws,
        key=lambda draw: (ratios[draw.candidate_id], draw.formed_at, draw.candidate_id),
    )
    # U0024/U0025 support daily > lower timeframe only. No weekly/monthly
    # complete hierarchy is invented when those frames are present.
    if {draw.timeframe for draw in draws} <= {"M5", "DAILY"}:
        timeframe_order = {"M5": 1, "DAILY": 2}
        significance_sorted = sorted(
            draws,
            key=lambda draw: (
                -timeframe_order[draw.timeframe],
                draw.formed_at,
                draw.candidate_id,
            ),
        )
        significance_ranks: dict[str, int | None] = {
            draw.candidate_id: index
            for index, draw in enumerate(significance_sorted, start=1)
        }
    else:
        significance_ranks = {draw.candidate_id: None for draw in draws}
    return tuple(
        RankedDraw(draw, ratios[draw.candidate_id], index, significance_ranks[draw.candidate_id])
        for index, draw in enumerate(ordered, start=1)
    )
