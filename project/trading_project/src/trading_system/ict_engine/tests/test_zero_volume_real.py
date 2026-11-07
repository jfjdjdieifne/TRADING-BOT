"""Opt-in verification of the published zero-volume accounting."""

from __future__ import annotations

import os
from collections import Counter

import pytest

from trading_system.ict_engine.data import load_eurusd_5m
from trading_system.ict_engine.market_status import MarketStatus, market_status

_DATA_DIR = os.environ.get("ICT_ENGINE_M0_DATA_DIR")
pytestmark = pytest.mark.skipif(
    _DATA_DIR is None,
    reason="Set ICT_ENGINE_M0_DATA_DIR to the local 2022/2023-only data directory",
)

_EXPECTED = {
    2022: {
        MarketStatus.NO_MARKET_WEEKEND_FILLER: 30_244,
        MarketStatus.NO_MARKET_INTRAWEEK_FLAT: 3,
        MarketStatus.UNRESOLVED_ZERO_VOLUME: 0,
    },
    2023: {
        MarketStatus.NO_MARKET_WEEKEND_FILLER: 30_264,
        MarketStatus.NO_MARKET_INTRAWEEK_FLAT: 200,
        MarketStatus.UNRESOLVED_ZERO_VOLUME: 0,
    },
}
_WEEKDAY_COUNTS = {
    2022: {0: 1, 1: 1, 2: 1, 3: 0, 4: 1_656, 5: 15_264, 6: 13_324},
    2023: {0: 180, 1: 4, 2: 8, 3: 8, 4: 1_656, 5: 14_976, 6: 13_632},
}


@pytest.mark.parametrize("year", (2022, 2023))
def test_real_zero_volume_counts_by_year_weekday_and_hour(year) -> None:
    batch = load_eurusd_5m(f"{_DATA_DIR}/{year}.csv.gz")
    statuses = [market_status(candle) for candle in batch.candles]
    category_counts = Counter(statuses)
    for status, count in _EXPECTED[year].items():
        assert category_counts[status] == count

    zero_candles = [
        candle
        for candle, status in zip(batch.candles, statuses, strict=True)
        if status is not MarketStatus.MARKET
    ]
    assert Counter(candle.start.weekday() for candle in zero_candles) == Counter(
        _WEEKDAY_COUNTS[year]
    )

    by_hour = Counter(candle.start.hour for candle in zero_candles)
    assert sum(by_hour.values()) == sum(_EXPECTED[year].values())
    assert set(by_hour) == set(range(24))
    assert sum(
        candle.start.hour == 21 and candle.start.weekday() < 4
        for candle in zero_candles
    ) == (2 if year == 2022 else 34)
    assert sum(
        candle.start.hour == 22 and candle.start.weekday() < 4
        for candle in zero_candles
    ) == (1 if year == 2022 else 5)
