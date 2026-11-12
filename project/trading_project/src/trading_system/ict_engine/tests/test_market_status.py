from __future__ import annotations

from datetime import datetime, timedelta, timezone

from trading_system.ict_engine.causal import assert_prefix_invariance
from trading_system.ict_engine.data import parse_eurusd_5m
from trading_system.ict_engine.market_status import (
    MarketStatus,
    is_no_market,
    market_status,
)

from .helpers import source_row

UTC = timezone.utc


def _candle(start: datetime, *, volume: float = 0, flat: bool = True):
    high = 1.10 if flat else 1.11
    row = source_row(
        start,
        BidOpen=1.10,
        BidHigh=high,
        BidLow=1.10,
        BidClose=1.10,
        BidVolume=volume,
        AskOpen=1.1002,
        AskHigh=high + 0.0002,
        AskLow=1.1002,
        AskClose=1.1002,
        AskVolume=volume,
    )
    return parse_eurusd_5m([row], expected_year=start.year).candles[0]


def test_weekend_and_intraweek_filler_are_no_market() -> None:
    friday = _candle(datetime(2022, 1, 7, 21, 30, tzinfo=UTC))
    saturday = _candle(datetime(2022, 1, 8, 3, 0, tzinfo=UTC))
    sunday = _candle(datetime(2022, 1, 9, 12, 0, tzinfo=UTC))
    monday = _candle(datetime(2022, 1, 3, 12, 0, tzinfo=UTC))

    assert market_status(friday) is MarketStatus.NO_MARKET_WEEKEND_FILLER
    assert market_status(saturday) is MarketStatus.NO_MARKET_WEEKEND_FILLER
    assert market_status(sunday) is MarketStatus.NO_MARKET_WEEKEND_FILLER
    assert market_status(monday) is MarketStatus.NO_MARKET_INTRAWEEK_FLAT
    assert all(is_no_market(candle) for candle in (friday, saturday, sunday, monday))


def test_positive_volume_flat_bar_remains_a_market_candle() -> None:
    candle = _candle(datetime(2022, 1, 3, 12, 0, tzinfo=UTC), volume=1.0)
    assert market_status(candle) is MarketStatus.MARKET
    assert not is_no_market(candle)


def test_nonflat_zero_volume_is_unresolved_not_silently_dropped() -> None:
    candle = _candle(datetime(2022, 1, 3, 12, 0, tzinfo=UTC), flat=False)
    assert market_status(candle) is MarketStatus.UNRESOLVED_ZERO_VOLUME
    assert not is_no_market(candle)


def test_status_trace_is_prefix_invariant_and_deterministic() -> None:
    origin = datetime(2022, 1, 7, 21, 0, tzinfo=UTC)
    candles = tuple(_candle(origin + timedelta(minutes=5 * i)) for i in range(8))
    function = lambda rows: [market_status(candle) for candle in rows]
    assert_prefix_invariance(function, candles)
    assert function(candles) == function(candles)
