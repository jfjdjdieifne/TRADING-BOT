"""Parallel order-block boundary doctrines with unresolved qualification."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .data import Candle
from .displacement import displacement_trace
from .market_status import MarketStatus, market_status
from .price import PriceBasis, ohlc


class OrderBlockVariant(str, Enum):
    OPENING_OF_OPPOSITE_CLOSE_RUN = "opening_of_opposite_close_run"
    LAST_OPPOSITE_CLOSE_CANDLE = "last_opposite_close_candle"


class OrderBlockDirection(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"


class OrderBlockEventKind(str, Enum):
    CANDIDATE_CREATED = "candidate_created"
    VIOLATED = "violated"


@dataclass(frozen=True, slots=True)
class OrderBlockZone:
    zone_id: str
    variant: OrderBlockVariant
    direction: OrderBlockDirection
    opening: float
    far_side: float
    run_first_time: datetime
    run_last_time: datetime
    created_at: datetime
    claim_ids: tuple[str, ...]
    qualification: str = "CANDIDATE_REJECTION_CRITERION_WAITING_U0051"


@dataclass(frozen=True, slots=True)
class OrderBlockEvent:
    kind: OrderBlockEventKind
    zone: OrderBlockZone
    available_at: datetime
    claim_ids: tuple[str, ...]


def order_block_trace(
    candles: Sequence[Candle],
    variant: OrderBlockVariant,
    basis: PriceBasis = PriceBasis.BID,
) -> tuple[tuple[OrderBlockEvent, ...], ...]:
    """Create candidates at opposite displacement and record far-side violation.

    The missing rejection text in U0051 prevents promotion from candidate to a
    fully qualified order block. The two boundary definitions are separate runs;
    neither is averaged or selected.
    """

    displacements = displacement_trace(candles, basis)
    market: list[Candle] = []
    active: dict[str, OrderBlockZone] = {}
    trace: list[tuple[OrderBlockEvent, ...]] = []

    for candle, displacement in zip(candles, displacements, strict=True):
        events: list[OrderBlockEvent] = []
        if market_status(candle) is MarketStatus.MARKET:
            _, high, low, _ = ohlc(candle, basis)
            for zone_id in tuple(sorted(active)):
                zone = active[zone_id]
                violated = (
                    zone.direction is OrderBlockDirection.BULLISH and low < zone.far_side
                ) or (
                    zone.direction is OrderBlockDirection.BEARISH and high > zone.far_side
                )
                if violated:
                    events.append(
                        OrderBlockEvent(
                            OrderBlockEventKind.VIOLATED, zone, candle.end, ("U0048",)
                        )
                    )
                    del active[zone_id]

            if displacement.is_displacement and displacement.broken_swing is not None:
                direction = (
                    OrderBlockDirection.BULLISH
                    if displacement.broken_swing.side.value == "high"
                    else OrderBlockDirection.BEARISH
                )
                wanted_close = (
                    (lambda op, close: close < op)
                    if direction is OrderBlockDirection.BULLISH
                    else (lambda op, close: close > op)
                )
                run: list[Candle] = []
                for previous in reversed(market):
                    op, _, _, close = ohlc(previous, basis)
                    if not wanted_close(op, close):
                        break
                    run.append(previous)
                run.reverse()
                if run:
                    selected = run if variant is OrderBlockVariant.OPENING_OF_OPPOSITE_CLOSE_RUN else run[-1:]
                    first, last = selected[0], selected[-1]
                    first_op, _, _, _ = ohlc(first, basis)
                    if direction is OrderBlockDirection.BULLISH:
                        far_side = min(ohlc(item, basis)[2] for item in selected)
                    else:
                        far_side = max(ohlc(item, basis)[1] for item in selected)
                    claims = (
                        ("U0045", "U0047", "U0048", "U0051")
                        if variant is OrderBlockVariant.OPENING_OF_OPPOSITE_CLOSE_RUN
                        else ("U0046", "U0048", "U0051")
                    )
                    zone = OrderBlockZone(
                        zone_id=(
                            f"ob:{variant.value}:{direction.value}:"
                            f"{first.start.isoformat()}:{candle.end.isoformat()}"
                        ),
                        variant=variant,
                        direction=direction,
                        opening=first_op,
                        far_side=far_side,
                        run_first_time=first.start,
                        run_last_time=last.start,
                        created_at=candle.end,
                        claim_ids=claims,
                    )
                    active[zone.zone_id] = zone
                    events.append(
                        OrderBlockEvent(
                            OrderBlockEventKind.CANDIDATE_CREATED, zone, candle.end, claims
                        )
                    )
            market.append(candle)
        trace.append(tuple(events))
    return tuple(trace)
