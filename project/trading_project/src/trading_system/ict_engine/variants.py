"""Pre-registered M2 reference and one-dimension-at-a-time variants."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .htf import CalendarAnchor
from .order_blocks import OrderBlockVariant
from .price import PriceBasis
from .sessions import ClockDefinition


class TargetRanking(str, Enum):
    DAILY_THEN_DISTANCE = "daily_then_distance"
    DISTANCE_ONLY = "distance_only"


@dataclass(frozen=True, slots=True)
class EngineVariant:
    variant_id: str
    basis: PriceBasis
    order_block: OrderBlockVariant
    clock: ClockDefinition
    target_ranking: TargetRanking
    daily_anchor: CalendarAnchor


REFERENCE = EngineVariant(
    variant_id="R00",
    basis=PriceBasis.BID,
    order_block=OrderBlockVariant.OPENING_OF_OPPOSITE_CLOSE_RUN,
    clock=ClockDefinition.EURO_0200_0500,
    target_ranking=TargetRanking.DAILY_THEN_DISTANCE,
    daily_anchor=CalendarAnchor.UTC,
)

VARIANTS = (
    REFERENCE,
    EngineVariant(
        "V01",
        PriceBasis.ASK,
        REFERENCE.order_block,
        REFERENCE.clock,
        REFERENCE.target_ranking,
        REFERENCE.daily_anchor,
    ),
    EngineVariant(
        "V02",
        REFERENCE.basis,
        OrderBlockVariant.LAST_OPPOSITE_CLOSE_CANDLE,
        REFERENCE.clock,
        REFERENCE.target_ranking,
        REFERENCE.daily_anchor,
    ),
    EngineVariant(
        "V03",
        REFERENCE.basis,
        REFERENCE.order_block,
        REFERENCE.clock,
        TargetRanking.DISTANCE_ONLY,
        REFERENCE.daily_anchor,
    ),
    EngineVariant(
        "V04",
        REFERENCE.basis,
        REFERENCE.order_block,
        REFERENCE.clock,
        REFERENCE.target_ranking,
        CalendarAnchor.NEW_YORK,
    ),
    EngineVariant(
        "V05",
        REFERENCE.basis,
        REFERENCE.order_block,
        ClockDefinition.LONDON_CLOSE_1000_1200,
        REFERENCE.target_ranking,
        REFERENCE.daily_anchor,
    ),
)

VARIANT_BY_ID = {variant.variant_id: variant for variant in VARIANTS}
assert len(VARIANT_BY_ID) == len(VARIANTS)
