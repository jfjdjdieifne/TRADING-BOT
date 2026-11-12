"""Parallel New York clock doctrines; incomplete bounds stay incomplete."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, time
from enum import Enum
from zoneinfo import ZoneInfo

from .data import Candle
from .market_status import MarketStatus, market_status

NEW_YORK = ZoneInfo("America/New_York")


class ClockDefinition(str, Enum):
    LONDON_START_0100_OPEN_END = "london_start_0100_open_end"
    LONDON_START_0200_OPEN_END = "london_start_0200_open_end"
    EURO_0200_0500 = "euro_0200_0500"
    LONDON_CLOSE_1000_1200 = "london_close_1000_1200"
    NEW_YORK_SESSION_NOT_KILLZONE = "new_york_session_not_killzone"
    WIDE_0830_NOT_NY_KILLZONE_OPEN_END = "wide_0830_not_ny_killzone_open_end"


@dataclass(frozen=True, slots=True)
class ClockVariant:
    definition_id: ClockDefinition
    start: time | None
    end: time | None
    killzone_label_allowed: bool
    claim_ids: tuple[str, ...]


CLOCK_VARIANTS = (
    ClockVariant(ClockDefinition.LONDON_START_0100_OPEN_END, time(1), None, True, ("U0089",)),
    ClockVariant(ClockDefinition.LONDON_START_0200_OPEN_END, time(2), None, True, ("U0090", "U0091")),
    ClockVariant(ClockDefinition.EURO_0200_0500, time(2), time(5), True, ("U0092",)),
    ClockVariant(ClockDefinition.LONDON_CLOSE_1000_1200, time(10), time(12), True, ("U0093",)),
    ClockVariant(ClockDefinition.NEW_YORK_SESSION_NOT_KILLZONE, None, None, False, ("U0094",)),
    ClockVariant(ClockDefinition.WIDE_0830_NOT_NY_KILLZONE_OPEN_END, time(8, 30), None, False, ("U0095",)),
)


@dataclass(frozen=True, slots=True)
class SessionObservation:
    available_at: datetime
    local_bar_start: datetime
    definition_id: ClockDefinition
    starts_here: bool
    in_window: bool | None
    killzone_label_allowed: bool
    market_status: MarketStatus
    claim_ids: tuple[str, ...]


def observe_session(candle: Candle, variant: ClockVariant) -> SessionObservation:
    local = candle.start.astimezone(NEW_YORK)
    local_time = local.time().replace(tzinfo=None)
    starts = variant.start is not None and local_time == variant.start
    if variant.start is None:
        inside = None
    elif variant.end is None:
        inside = False if local_time < variant.start else None
    else:
        inside = variant.start <= local_time < variant.end
    return SessionObservation(
        available_at=candle.end,
        local_bar_start=local,
        definition_id=variant.definition_id,
        starts_here=starts,
        in_window=inside,
        killzone_label_allowed=variant.killzone_label_allowed,
        market_status=market_status(candle),
        claim_ids=variant.claim_ids,
    )


def session_trace(candles: Sequence[Candle]) -> tuple[tuple[SessionObservation, ...], ...]:
    return tuple(
        tuple(observe_session(candle, variant) for variant in CLOCK_VARIANTS)
        for candle in candles
    )
