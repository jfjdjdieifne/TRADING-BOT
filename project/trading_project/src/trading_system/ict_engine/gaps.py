"""Three-market-candle fair-value-gap geometry and observable lifecycle."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .data import Candle
from .market_status import MarketStatus, market_status
from .price import PriceBasis, ohlc

FVG_DEFINITION_ID = "ENGINEERING_HYPOTHESIS_THREE_MARKET_CANDLES"
FVG_CLAIM_IDS = ("U0036", "U0038")


class GapDirection(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"


class GapEventKind(str, Enum):
    CREATED = "created"
    FIRST_TOUCH = "first_touch"
    FULLY_CLOSED = "fully_closed"


@dataclass(frozen=True, slots=True)
class FairValueGap:
    gap_id: str
    direction: GapDirection
    lower: float
    upper: float
    first_time: datetime
    middle_time: datetime
    third_time: datetime
    created_at: datetime
    basis: PriceBasis
    definition_id: str = FVG_DEFINITION_ID
    claim_ids: tuple[str, ...] = FVG_CLAIM_IDS


@dataclass(frozen=True, slots=True)
class GapEvent:
    kind: GapEventKind
    gap: FairValueGap
    available_at: datetime
    claim_ids: tuple[str, ...]


@dataclass(slots=True)
class _GapState:
    gap: FairValueGap
    touched: bool = False


def _gap_id(direction: GapDirection, first: Candle, third: Candle, basis: PriceBasis) -> str:
    return (
        f"fvg:{basis.value}:{direction.value}:"
        f"{first.start.isoformat()}:{third.start.isoformat()}"
    )


def fvg_trace(
    candles: Sequence[Candle], basis: PriceBasis = PriceBasis.BID
) -> tuple[tuple[GapEvent, ...], ...]:
    """Emit creation/touch/full-close events without calling full closure failure.

    U0037 says most gaps do not completely close; it does not supply a general
    invalidation rule. FULLY_CLOSED is therefore an observable, not a doctrine
    verdict. Inversion and breakaway subtypes remain WAITING in ``waiting.py``.
    """

    market: list[Candle] = []
    states: dict[str, _GapState] = {}
    trace: list[tuple[GapEvent, ...]] = []

    for candle in candles:
        events: list[GapEvent] = []
        if market_status(candle) is MarketStatus.MARKET:
            _, high, low, _ = ohlc(candle, basis)

            # Existing gaps were knowable before this bar; process them first.
            for gap_id in tuple(states):
                state = states[gap_id]
                gap = state.gap
                touches = high > gap.lower and low < gap.upper
                if touches and not state.touched:
                    state.touched = True
                    events.append(
                        GapEvent(
                            GapEventKind.FIRST_TOUCH,
                            gap,
                            candle.end,
                            ("U0037", "U0041"),
                        )
                    )
                fully_closed = (
                    gap.direction is GapDirection.BULLISH and low <= gap.lower
                ) or (
                    gap.direction is GapDirection.BEARISH and high >= gap.upper
                )
                if fully_closed:
                    events.append(
                        GapEvent(
                            GapEventKind.FULLY_CLOSED,
                            gap,
                            candle.end,
                            ("U0037",),
                        )
                    )
                    del states[gap_id]

            market.append(candle)
            if len(market) >= 3:
                first, middle, third = market[-3], market[-2], market[-1]
                _, first_high, first_low, _ = ohlc(first, basis)
                _, third_high, third_low, _ = ohlc(third, basis)
                direction = None
                lower = upper = None
                if first_high < third_low:
                    direction, lower, upper = GapDirection.BULLISH, first_high, third_low
                elif first_low > third_high:
                    direction, lower, upper = GapDirection.BEARISH, third_high, first_low
                if direction is not None and lower is not None and upper is not None:
                    gap = FairValueGap(
                        gap_id=_gap_id(direction, first, third, basis),
                        direction=direction,
                        lower=lower,
                        upper=upper,
                        first_time=first.start,
                        middle_time=middle.start,
                        third_time=third.start,
                        created_at=candle.end,
                        basis=basis,
                    )
                    states[gap.gap_id] = _GapState(gap)
                    events.append(GapEvent(GapEventKind.CREATED, gap, candle.end, FVG_CLAIM_IDS))
        trace.append(tuple(events))
    return tuple(trace)
