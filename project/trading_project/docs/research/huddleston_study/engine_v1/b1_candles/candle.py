"""Candle record for step B1 of engine_v1.

Scope: three TIER2 third-party definitions only (swing high, swing low, fair
value gap). Pure data, no market data reading, no pandas, no network, and no
import from the old pipeline.

Every value here is supplied by the caller (test fixtures or, later, an
explicit adapter). This module holds no thresholds, no ratios and no defaults.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class Candle:
    """One OHLC candle with an explicit closed flag.

    `closed` matters: the design text gives a confirmation state that is only
    reachable after the third candle closes (see swing.py PENDING).
    """

    open: float
    high: float
    low: float
    close: float
    closed: bool = True

    def __post_init__(self) -> None:
        if self.high < self.low:
            raise ValueError("candle high is below its low")
        if not (self.low <= self.open <= self.high):
            raise ValueError("candle open is outside its high/low range")
        if not (self.low <= self.close <= self.high):
            raise ValueError("candle close is outside its high/low range")
        if not isinstance(self.closed, bool):
            raise ValueError("candle closed flag must be a bool")

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "Candle":
        return cls(
            open=float(data["o"]),
            high=float(data["h"]),
            low=float(data["l"]),
            close=float(data["c"]),
            closed=bool(data.get("closed", True)),
        )


def build_candles(rows) -> list:
    """Turn a list of mappings into a list of Candle. Fixture helper only."""

    return [Candle.from_mapping(row) for row in rows]
