"""Latest confirmed delivery-leg range and range-position premium/discount."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .data import Candle
from .market_status import MarketStatus, is_no_market, market_status
from .price import PriceBasis, ohlc
from .swings import SwingPoint, SwingSide, swing_trace

RANGE_DEFINITION_ID = "ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS"
RANGE_CLAIM_IDS = ("U0070", "U0072", "U0079", "U0080", "U0083", "U0085")


class RangePosition(str, Enum):
    PREMIUM = "premium"
    DISCOUNT = "discount"
    EQUILIBRIUM = "equilibrium"
    UNDEFINED = "undefined"
    NO_MARKET = "no_market"


class Outside(str, Enum):
    ABOVE = "above"
    BELOW = "below"
    INSIDE = "inside"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True, slots=True)
class DealingRange:
    lower: SwingPoint
    upper: SwingPoint
    low: float
    high: float
    equilibrium: float
    selected_at: datetime
    basis: PriceBasis
    definition_id: str = RANGE_DEFINITION_ID
    claim_ids: tuple[str, ...] = RANGE_CLAIM_IDS


@dataclass(frozen=True, slots=True)
class RangeObservation:
    available_at: datetime
    dealing_range: DealingRange | None
    position: RangePosition
    position_ratio: float | None
    traded_outside: Outside
    carrying_charge_status: str = "WAITING_CONTRACT_DATA"


def _range_from_pair(
    first: SwingPoint, second: SwingPoint, selected_at: datetime, basis: PriceBasis
) -> DealingRange | None:
    if first.side is second.side:
        return None
    lower, upper = (first, second) if first.side is SwingSide.LOW else (second, first)
    if lower.price >= upper.price:
        return None
    return DealingRange(
        lower=lower,
        upper=upper,
        low=lower.price,
        high=upper.price,
        equilibrium=(lower.price + upper.price) / 2,
        selected_at=selected_at,
        basis=basis,
    )


def dealing_range_trace(
    candles: Sequence[Candle], basis: PriceBasis = PriceBasis.BID
) -> tuple[RangeObservation, ...]:
    """Keep the latest alternating confirmed pair, preferring a newer same-side extreme."""

    swings = swing_trace(candles, basis)
    legs: list[SwingPoint] = []
    current_range: DealingRange | None = None
    trace: list[RangeObservation] = []

    for candle, new_swings in zip(candles, swings, strict=True):
        for swing in new_swings:
            if not legs:
                legs.append(swing)
            elif swing.side is legs[-1].side:
                more_extreme = (
                    swing.side is SwingSide.HIGH and swing.price > legs[-1].price
                ) or (
                    swing.side is SwingSide.LOW and swing.price < legs[-1].price
                )
                if more_extreme:
                    legs[-1] = swing
            else:
                legs.append(swing)
            if len(legs) >= 2:
                candidate = _range_from_pair(legs[-2], legs[-1], candle.end, basis)
                if candidate is not None:
                    current_range = candidate

        status = market_status(candle)
        if status is not MarketStatus.MARKET or current_range is None:
            position = RangePosition.NO_MARKET if is_no_market(candle) else RangePosition.UNDEFINED
            trace.append(
                RangeObservation(candle.end, current_range, position, None, Outside.NOT_APPLICABLE)
            )
            continue

        _, high, low, close = ohlc(candle, basis)
        ratio = (close - current_range.low) / (current_range.high - current_range.low)
        position = (
            RangePosition.EQUILIBRIUM
            if close == current_range.equilibrium
            else RangePosition.PREMIUM
            if close > current_range.equilibrium
            else RangePosition.DISCOUNT
        )
        outside = (
            Outside.ABOVE
            if high > current_range.high
            else Outside.BELOW
            if low < current_range.low
            else Outside.INSIDE
        )
        trace.append(
            RangeObservation(candle.end, current_range, position, ratio, outside)
        )
    return tuple(trace)
