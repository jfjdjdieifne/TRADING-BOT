"""Causal daily/weekly/monthly aggregation with explicit calendar anchors."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from enum import Enum
from zoneinfo import ZoneInfo

from .data import Candle
from .liquidity import LiquidityPool, PoolKind
from .market_status import MarketStatus, market_status
from .swings import SwingSide

UTC = ZoneInfo("UTC")
NEW_YORK = ZoneInfo("America/New_York")


class HigherTimeframe(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


class CalendarAnchor(str, Enum):
    UTC = "UTC"
    NEW_YORK = "NEW_YORK"


@dataclass(frozen=True, slots=True)
class AggregatedCandle:
    timeframe: HigherTimeframe
    anchor: CalendarAnchor
    bucket_start: datetime
    bucket_end: datetime
    first_source_time: datetime
    last_source_time: datetime
    bid_open: float
    bid_high: float
    bid_low: float
    bid_close: float
    bid_volume: float
    ask_open: float
    ask_high: float
    ask_low: float
    ask_close: float
    ask_volume: float
    source_bar_count: int


@dataclass(frozen=True, slots=True)
class HTFState:
    available_at: datetime
    newly_completed: tuple[AggregatedCandle, ...]
    last_completed: AggregatedCandle | None
    forming: AggregatedCandle | None


def _zone(anchor: CalendarAnchor) -> ZoneInfo:
    return UTC if anchor is CalendarAnchor.UTC else NEW_YORK


def bucket_bounds(
    source_time: datetime, timeframe: HigherTimeframe, anchor: CalendarAnchor
) -> tuple[datetime, datetime]:
    zone = _zone(anchor)
    local = source_time.astimezone(zone)
    if timeframe is HigherTimeframe.DAILY:
        start_date = local.date()
        end_date = start_date + timedelta(days=1)
    elif timeframe is HigherTimeframe.WEEKLY:
        start_date = local.date() - timedelta(days=local.weekday())
        end_date = start_date + timedelta(days=7)
    else:
        start_date = local.date().replace(day=1)
        end_date = (
            date(start_date.year + 1, 1, 1)
            if start_date.month == 12
            else date(start_date.year, start_date.month + 1, 1)
        )
    start = datetime.combine(start_date, time(), tzinfo=zone).astimezone(UTC)
    end = datetime.combine(end_date, time(), tzinfo=zone).astimezone(UTC)
    return start, end


def _aggregate(candle: Candle, bucket: tuple[datetime, datetime], timeframe: HigherTimeframe, anchor: CalendarAnchor) -> AggregatedCandle:
    return AggregatedCandle(
        timeframe=timeframe,
        anchor=anchor,
        bucket_start=bucket[0],
        bucket_end=bucket[1],
        first_source_time=candle.start,
        last_source_time=candle.start,
        bid_open=candle.bid_open,
        bid_high=candle.bid_high,
        bid_low=candle.bid_low,
        bid_close=candle.bid_close,
        bid_volume=candle.bid_volume,
        ask_open=candle.ask_open,
        ask_high=candle.ask_high,
        ask_low=candle.ask_low,
        ask_close=candle.ask_close,
        ask_volume=candle.ask_volume,
        source_bar_count=1,
    )


def _append(forming: AggregatedCandle, candle: Candle) -> AggregatedCandle:
    return AggregatedCandle(
        timeframe=forming.timeframe,
        anchor=forming.anchor,
        bucket_start=forming.bucket_start,
        bucket_end=forming.bucket_end,
        first_source_time=forming.first_source_time,
        last_source_time=candle.start,
        bid_open=forming.bid_open,
        bid_high=max(forming.bid_high, candle.bid_high),
        bid_low=min(forming.bid_low, candle.bid_low),
        bid_close=candle.bid_close,
        bid_volume=forming.bid_volume + candle.bid_volume,
        ask_open=forming.ask_open,
        ask_high=max(forming.ask_high, candle.ask_high),
        ask_low=min(forming.ask_low, candle.ask_low),
        ask_close=candle.ask_close,
        ask_volume=forming.ask_volume + candle.ask_volume,
        source_bar_count=forming.source_bar_count + 1,
    )


def htf_trace(
    candles: Sequence[Candle], timeframe: HigherTimeframe, anchor: CalendarAnchor
) -> tuple[HTFState, ...]:
    """Expose a bucket as completed only when a later bucket is observed."""

    current_bucket: tuple[datetime, datetime] | None = None
    forming: AggregatedCandle | None = None
    last_completed: AggregatedCandle | None = None
    trace: list[HTFState] = []

    for candle in candles:
        bucket = bucket_bounds(candle.start, timeframe, anchor)
        newly: tuple[AggregatedCandle, ...] = ()
        if current_bucket != bucket:
            if forming is not None:
                last_completed = forming
                newly = (forming,)
            current_bucket = bucket
            forming = None
        if market_status(candle) is MarketStatus.MARKET:
            forming = (
                _aggregate(candle, bucket, timeframe, anchor)
                if forming is None
                else _append(forming, candle)
            )
        trace.append(HTFState(candle.end, newly, last_completed, forming))
    return tuple(trace)


def htf_extreme_pools(
    completed: AggregatedCandle, *, available_at: datetime
) -> tuple[LiquidityPool, LiquidityPool]:
    """Previous completed HTF high/low as parallel old-extreme pools."""

    pools = []
    for side, level in ((SwingSide.HIGH, completed.bid_high), (SwingSide.LOW, completed.bid_low)):
        claims = ["U0004", "U0024", "U0025"]
        if completed.timeframe is HigherTimeframe.DAILY and side is SwingSide.HIGH:
            claims.append("U0074")
        if completed.timeframe is HigherTimeframe.MONTHLY and side is SwingSide.LOW:
            claims.append("U0017")
        pools.append(
            LiquidityPool(
                pool_id=f"pool:{side.value}:htf:{completed.anchor.value}:{completed.timeframe.value}:{completed.bucket_start.isoformat()}",
                side=side,
                kind=PoolKind.HIGHER_TIMEFRAME_EXTREME,
                level=level,
                member_levels=(level,),
                formed_at=available_at,
                source_time=completed.bucket_start,
                timeframe=completed.timeframe.value,
                equality_ratio=None,
                cleanliness_rank=None,
                intervening_market_bars=None,
                claim_ids=tuple(claims),
                definition_id=f"PREVIOUS_COMPLETED_{completed.timeframe.value}_EXTREME",
            )
        )
    return pools[0], pools[1]
