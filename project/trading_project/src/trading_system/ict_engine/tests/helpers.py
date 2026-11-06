"""Synthetic rows with the exact pinned source schema."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from trading_system.ict_engine.data import SCHEMA, Candle, parse_eurusd_5m

UTC = timezone.utc


def source_row(start: datetime, **changes: Any) -> dict[str, Any]:
    values: dict[str, Any] = {
        "Datetime": start.isoformat().replace("+00:00", "Z"),
        "BidOpen": 1.10,
        "BidHigh": 1.11,
        "BidLow": 1.09,
        "BidClose": 1.105,
        "BidVolume": 2.0,
        "AskOpen": 1.1002,
        "AskHigh": 1.1102,
        "AskLow": 1.0902,
        "AskClose": 1.1052,
        "AskVolume": 3.0,
        "SpreadOpen": 0.0002,
        "SpreadOpenPips": 2.0,
        "SpreadHigh": 0.0002,
        "SpreadHighPips": 2.0,
        "SpreadLow": 0.0002,
        "SpreadLowPips": 2.0,
        "SpreadClose": 0.0002,
        "SpreadClosePips": 2.0,
    }
    assert set(values) == set(SCHEMA)
    values.update(changes)
    return values


def synthetic_candles(count: int = 8) -> tuple[Candle, ...]:
    origin = datetime(2022, 1, 3, tzinfo=UTC)
    rows = []
    for index in range(count):
        close = 1.09 + (index % 3) * 0.005
        rows.append(
            source_row(
                origin + index * timedelta(minutes=5),
                BidOpen=close,
                BidClose=close,
                AskOpen=close + 0.0002,
                AskClose=close + 0.0002,
            )
        )
    return parse_eurusd_5m(rows, expected_year=2022).candles
