"""Displacement as relative energy plus a close beyond a known swing."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .data import Candle
from .market_status import MarketStatus, market_status
from .price import PriceBasis, ohlc
from .swings import SwingPoint, SwingSide, swing_trace

DISPLACEMENT_PRIOR_MARKET_BARS = 3
DISPLACEMENT_DEFINITION_ID = "ENGINEERING_HYPOTHESIS_RANK_AGAINST_THREE_PRIOR_MARKET_BARS"
DISPLACEMENT_CLAIM_IDS = ("U0055", "U0056", "U0057", "U0058")


class Energy(str, Enum):
    ENERGETIC = "energetic"
    LETHARGIC = "lethargic"
    WAITING = "waiting"


@dataclass(frozen=True, slots=True)
class DisplacementObservation:
    available_at: datetime
    energy: Energy
    range_rank: int | None
    body_rank: int | None
    range_to_prior_max: float | None
    body_to_prior_max: float | None
    broken_swing: SwingPoint | None
    is_displacement: bool
    basis: PriceBasis
    definition_id: str = DISPLACEMENT_DEFINITION_ID
    claim_ids: tuple[str, ...] = DISPLACEMENT_CLAIM_IDS


def _rank(value: float, previous: list[float]) -> int:
    return 1 + sum(other > value for other in previous)


def _ratio(value: float, previous: list[float]) -> float | None:
    denominator = max(previous)
    return value / denominator if denominator > 0 else None


def displacement_trace(
    candles: Sequence[Candle], basis: PriceBasis = PriceBasis.BID
) -> tuple[DisplacementObservation, ...]:
    """Rank current energy against exactly three prior market bars.

    Rank one is the card hypothesis's contrast with 'no larger than neighbours'.
    No multiplier or minimum range is imposed. A displacement additionally needs
    a close beyond an already confirmed swing; a wick alone is insufficient.
    """

    swings = swing_trace(candles, basis)
    market: list[Candle] = []
    latest_high: SwingPoint | None = None
    latest_low: SwingPoint | None = None
    trace: list[DisplacementObservation] = []

    for candle, new_swings in zip(candles, swings, strict=True):
        for swing in new_swings:
            if swing.side is SwingSide.HIGH:
                latest_high = swing
            else:
                latest_low = swing

        if market_status(candle) is not MarketStatus.MARKET:
            trace.append(
                DisplacementObservation(
                    candle.end, Energy.WAITING, None, None, None, None, None, False, basis
                )
            )
            continue

        op, high, low, close = ohlc(candle, basis)
        current_range = high - low
        current_body = abs(close - op)
        previous_market = market[-DISPLACEMENT_PRIOR_MARKET_BARS:]
        broken = None
        if latest_high is not None and close > latest_high.price:
            broken = latest_high
        elif latest_low is not None and close < latest_low.price:
            broken = latest_low

        if len(previous_market) < DISPLACEMENT_PRIOR_MARKET_BARS:
            observation = DisplacementObservation(
                candle.end, Energy.WAITING, None, None, None, None, broken, False, basis
            )
        else:
            prior_ranges = []
            prior_bodies = []
            for previous in previous_market:
                p_op, p_high, p_low, p_close = ohlc(previous, basis)
                prior_ranges.append(p_high - p_low)
                prior_bodies.append(abs(p_close - p_op))
            range_rank = _rank(current_range, prior_ranges)
            body_rank = _rank(current_body, prior_bodies)
            energy = Energy.ENERGETIC if range_rank == 1 else Energy.LETHARGIC
            observation = DisplacementObservation(
                available_at=candle.end,
                energy=energy,
                range_rank=range_rank,
                body_rank=body_rank,
                range_to_prior_max=_ratio(current_range, prior_ranges),
                body_to_prior_max=_ratio(current_body, prior_bodies),
                broken_swing=broken,
                is_displacement=energy is Energy.ENERGETIC and broken is not None,
                basis=basis,
            )
        trace.append(observation)
        market.append(candle)
    return tuple(trace)
