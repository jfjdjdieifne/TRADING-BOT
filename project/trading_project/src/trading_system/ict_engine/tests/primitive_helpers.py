"""Hand-built OHLC candles for doctrine-level primitive tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from trading_system.ict_engine.data import Candle, parse_eurusd_5m

from .helpers import source_row

UTC = timezone.utc


def candle_at(
    start: datetime,
    op: float,
    high: float,
    low: float,
    close: float,
    *,
    volume: float = 1.0,
) -> Candle:
    assert low <= min(op, close) <= max(op, close) <= high
    row = source_row(
        start,
        BidOpen=op,
        BidHigh=high,
        BidLow=low,
        BidClose=close,
        BidVolume=volume,
        AskOpen=op + 0.0002,
        AskHigh=high + 0.0002,
        AskLow=low + 0.0002,
        AskClose=close + 0.0002,
        AskVolume=volume,
    )
    return parse_eurusd_5m([row], expected_year=start.year).candles[0]


def market_series(
    specifications: list[tuple[float, float, float, float]],
    *,
    origin: datetime = datetime(2022, 1, 3, tzinfo=UTC),
) -> tuple[Candle, ...]:
    return tuple(
        candle_at(origin + timedelta(minutes=5 * index), *values)
        for index, values in enumerate(specifications)
    )
