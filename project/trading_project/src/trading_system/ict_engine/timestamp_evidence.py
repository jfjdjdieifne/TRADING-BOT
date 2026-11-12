"""Reproducible, non-profit timestamp-convention evidence.

The diagnostic uses the official BLS Employment Situation calendar at 08:30
Eastern Time. Dates are explicit because the first-Friday heuristic is not
universally valid (March 2023 was released on 10 March). If labels are bar starts,
the first candle able to contain the response is labelled at the release. If
labels are bar ends, it is labelled five minutes later. This is not a recognizer.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from .data import ALLOWED_YEARS, BAR_WIDTH, Candle

NEW_YORK = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")
RELEASE_CLOCK = time(8, 30)
EVENT_OFFSETS = (-BAR_WIDTH, timedelta(0), BAR_WIDTH, 2 * BAR_WIDTH)
EMPLOYMENT_RELEASE_DATES = {
    2022: tuple(
        date.fromisoformat(value)
        for value in (
            "2022-01-07", "2022-02-04", "2022-03-04", "2022-04-01",
            "2022-05-06", "2022-06-03", "2022-07-08", "2022-08-05",
            "2022-09-02", "2022-10-07", "2022-11-04", "2022-12-02",
        )
    ),
    2023: tuple(
        date.fromisoformat(value)
        for value in (
            "2023-01-06", "2023-02-03", "2023-03-10", "2023-04-07",
            "2023-05-05", "2023-06-02", "2023-07-07", "2023-08-04",
            "2023-09-01", "2023-10-06", "2023-11-03", "2023-12-08",
        )
    ),
}


@dataclass(frozen=True, slots=True)
class EventAlignment:
    release: datetime
    largest_offset_minutes: tuple[int, ...]
    release_bar_rank_on_utc_day: int | None
    ranges_by_offset_minutes: tuple[tuple[int, float | None], ...]


def nfp_release_times(year: int) -> tuple[datetime, ...]:
    """Return the explicit BLS 08:30 Eastern release schedule in UTC."""

    if year not in ALLOWED_YEARS:
        raise ValueError("The M0 evidence protocol covers 2022 and 2023 only")
    return tuple(
        datetime.combine(release_date, RELEASE_CLOCK, tzinfo=NEW_YORK).astimezone(UTC)
        for release_date in EMPLOYMENT_RELEASE_DATES[year]
    )


def _bid_range(candle: Candle | None) -> float | None:
    if candle is None:
        return None
    return candle.bid_high - candle.bid_low


def event_alignment(candles: Sequence[Candle], release: datetime) -> EventAlignment:
    """Compare only event-neighbouring ranges and the release bar's daily rank."""

    by_start = {candle.start: candle for candle in candles}
    day_candles = [
        candle
        for candle in candles
        if candle.start.date() == release.date()
    ]
    ranges = {
        int(offset.total_seconds() // 60): _bid_range(
            by_start.get(release + offset)
        )
        for offset in EVENT_OFFSETS
    }
    present = {offset: value for offset, value in ranges.items() if value is not None}
    if not present:
        raise ValueError(f"No event-neighbouring candles for {release.isoformat()}")

    largest = max(present.values())
    largest_offsets = tuple(
        offset for offset, value in present.items() if value == largest
    )

    release_range = ranges[0]
    if release_range is None:
        rank = None
    else:
        # Competition rank needs no materiality threshold and includes flat bars.
        rank = 1 + sum(
            _bid_range(candle) > release_range for candle in day_candles
        )

    return EventAlignment(
        release=release,
        largest_offset_minutes=largest_offsets,
        release_bar_rank_on_utc_day=rank,
        ranges_by_offset_minutes=tuple(ranges.items()),
    )


def annual_event_alignment(
    candles: Sequence[Candle], year: int
) -> tuple[EventAlignment, ...]:
    return tuple(
        event_alignment(candles, release) for release in nfp_release_times(year)
    )
