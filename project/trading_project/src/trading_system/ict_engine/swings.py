"""Immediate-neighbour extreme candidates, not an invented swing hierarchy."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .data import Candle
from .market_status import MarketStatus, market_status
from .price import PriceBasis, ohlc

SWING_NEIGHBOURS = 1
SWING_DEFINITION_ID = "ENGINEERING_HYPOTHESIS_IMMEDIATE_MARKET_NEIGHBOURS"
SWING_CLAIM_IDS = ("U0056", "U0079", "U0096")


class SwingSide(str, Enum):
    HIGH = "high"
    LOW = "low"


@dataclass(frozen=True, slots=True)
class SwingPoint:
    side: SwingSide
    price: float
    source_time: datetime
    confirmed_at: datetime
    basis: PriceBasis
    market_ordinal: int
    definition_id: str = SWING_DEFINITION_ID
    claim_ids: tuple[str, ...] = SWING_CLAIM_IDS
    qualification: str = "CANDIDATE_HIERARCHY_WAITING"


def swing_trace(
    candles: Sequence[Candle], basis: PriceBasis = PriceBasis.BID
) -> tuple[tuple[SwingPoint, ...], ...]:
    """Confirm the middle of three consecutive *market* bars at the third bar.

    One neighbour on each side is the smallest possible local comparison. Strict
    ordering avoids inventing a tie-break. Filler is not a candle; unresolved
    zero-volume rows produce no swing and are not allowed into a market window.
    """

    market: list[Candle] = []
    trace: list[tuple[SwingPoint, ...]] = []
    for candle in candles:
        created: tuple[SwingPoint, ...] = ()
        if market_status(candle) is MarketStatus.MARKET:
            market.append(candle)
            if len(market) >= 2 * SWING_NEIGHBOURS + 1:
                middle = market[-2]
                left, right = market[-3], market[-1]
                _, left_high, left_low, _ = ohlc(left, basis)
                _, high, low, _ = ohlc(middle, basis)
                _, right_high, right_low, _ = ohlc(right, basis)
                side = None
                price = None
                if high > left_high and high > right_high:
                    side, price = SwingSide.HIGH, high
                elif low < left_low and low < right_low:
                    side, price = SwingSide.LOW, low
                if side is not None and price is not None:
                    created = (
                        SwingPoint(
                            side=side,
                            price=price,
                            source_time=middle.start,
                            confirmed_at=candle.end,
                            basis=basis,
                            market_ordinal=len(market) - 2,
                        ),
                    )
        trace.append(created)
    return tuple(trace)
