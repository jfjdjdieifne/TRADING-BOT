"""Pinned EURUSD five-minute input, with a hard information cutoff.

The source repository labels each candle by its UTC bar start.  A candle whose
label is 12:30 covers [12:30, 12:35) and is decision-available at 12:35 only.
See docs/research/huddleston_study/engine_v1/M0_DATA_AND_TIME.md.
"""

from __future__ import annotations

import csv
import gzip
import math
import re
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ALLOWED_YEARS = frozenset({2022, 2023})
DATA_CUTOFF = datetime(2025, 5, 1, tzinfo=timezone.utc)
BAR_WIDTH = timedelta(minutes=5)
UTC = timezone.utc

SCHEMA = (
    "Datetime",
    "BidOpen",
    "BidHigh",
    "BidLow",
    "BidClose",
    "BidVolume",
    "AskOpen",
    "AskHigh",
    "AskLow",
    "AskClose",
    "AskVolume",
    "SpreadOpen",
    "SpreadOpenPips",
    "SpreadHigh",
    "SpreadHighPips",
    "SpreadLow",
    "SpreadLowPips",
    "SpreadClose",
    "SpreadClosePips",
)

_PRICE_FIELDS = (
    "BidOpen",
    "BidHigh",
    "BidLow",
    "BidClose",
    "AskOpen",
    "AskHigh",
    "AskLow",
    "AskClose",
    "SpreadOpen",
    "SpreadHigh",
    "SpreadLow",
    "SpreadClose",
)
_VOLUME_FIELDS = ("BidVolume", "AskVolume")
_NON_NEGATIVE_FIELDS = _VOLUME_FIELDS + (
    "SpreadOpen",
    "SpreadOpenPips",
    "SpreadHigh",
    "SpreadHighPips",
    "SpreadLow",
    "SpreadLowPips",
    "SpreadClose",
    "SpreadClosePips",
)
_YEAR_FILE = re.compile(r"(?P<year>20\d\d)\.csv\.gz\Z")
_CAMEL_BOUNDARY = re.compile(r"(?<!^)(?=[A-Z])")


def _field_name(source_name: str) -> str:
    return _CAMEL_BOUNDARY.sub("_", source_name).lower()


class DataValidationError(ValueError):
    """Input differs from the pinned, causal data contract."""


@dataclass(frozen=True, slots=True)
class Candle:
    """One complete five-minute BID/ASK candle, labelled by UTC bar start."""

    start: datetime
    bid_open: float
    bid_high: float
    bid_low: float
    bid_close: float
    bid_volume: float
    ask_open: float
    ask_high: float
    ask_low: float
    ask_close: float
    ask_volume: float
    spread_open: float
    spread_open_pips: float
    spread_high: float
    spread_high_pips: float
    spread_low: float
    spread_low_pips: float
    spread_close: float
    spread_close_pips: float

    @property
    def end(self) -> datetime:
        """Exclusive bar end, and therefore its earliest decision time."""

        return self.start + BAR_WIDTH


@dataclass(frozen=True, slots=True)
class CandleBatch:
    """Parsed candles plus accounting needed to audit the cutoff."""

    candles: tuple[Candle, ...]
    source_year: int
    rows_seen: int
    rows_dropped_at_cutoff: int

    def __len__(self) -> int:
        return len(self.candles)

    def __iter__(self) -> Iterator[Candle]:
        return iter(self.candles)


def _year_from_path(path: Path) -> int:
    match = _YEAR_FILE.fullmatch(path.name)
    if match is None:
        raise DataValidationError(
            f"Expected a pinned annual file named YYYY.csv.gz, got {path.name!r}"
        )
    return int(match.group("year"))


def _parse_timestamp(value: Any, row_number: int) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise DataValidationError(
            f"Row {row_number}: invalid Datetime {value!r}"
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise DataValidationError(
            f"Row {row_number}: Datetime must include an explicit timezone"
        )
    return parsed.astimezone(UTC)


def _parse_number(row: Mapping[str, Any], field: str, row_number: int) -> float:
    try:
        value = float(row[field])
    except (KeyError, TypeError, ValueError) as exc:
        raise DataValidationError(
            f"Row {row_number}: invalid numeric field {field}={row.get(field)!r}"
        ) from exc
    if not math.isfinite(value):
        raise DataValidationError(
            f"Row {row_number}: non-finite numeric field {field}"
        )
    return value


def _validate_candle_values(values: dict[str, float], row_number: int) -> None:
    for field in _NON_NEGATIVE_FIELDS:
        if values[field] < 0:
            raise DataValidationError(
                f"Row {row_number}: {field} must not be negative"
            )

    for side in ("Bid", "Ask"):
        op = values[f"{side}Open"]
        high = values[f"{side}High"]
        low = values[f"{side}Low"]
        close = values[f"{side}Close"]
        if high < max(op, close, low) or low > min(op, close, high):
            raise DataValidationError(
                f"Row {row_number}: inconsistent {side} OHLC envelope"
            )

    for field in ("Open", "High", "Low", "Close"):
        if values[f"Ask{field}"] < values[f"Bid{field}"]:
            raise DataValidationError(
                f"Row {row_number}: Ask{field} is below Bid{field}"
            )


def parse_eurusd_5m(
    rows: Iterable[Mapping[str, Any]], *, expected_year: int
) -> CandleBatch:
    """Parse rows, dropping every timestamp at/after the cutoff immediately.

    Rows beyond the cutoff are not numerically parsed, sorted, or returned.
    Retained rows must already be strictly ordered; sorting could conceal a
    broken time source and is therefore intentionally not performed.
    """

    if expected_year not in ALLOWED_YEARS:
        raise DataValidationError(
            f"Stage M0 permits only {sorted(ALLOWED_YEARS)}, not {expected_year}"
        )

    candles: list[Candle] = []
    rows_seen = 0
    dropped = 0
    previous_start: datetime | None = None

    for row_number, row in enumerate(rows, start=1):
        rows_seen += 1
        start = _parse_timestamp(row.get("Datetime"), row_number)

        # This is deliberately the first operation after timestamp parsing.
        if start >= DATA_CUTOFF:
            dropped += 1
            continue

        if start.year != expected_year:
            raise DataValidationError(
                f"Row {row_number}: {start.isoformat()} is outside {expected_year}"
            )
        if (
            start.minute % 5
            or start.second
            or start.microsecond
        ):
            raise DataValidationError(
                f"Row {row_number}: timestamp is not aligned to a five-minute grid"
            )
        if previous_start is not None and start <= previous_start:
            raise DataValidationError(
                f"Row {row_number}: timestamps are not strictly increasing"
            )

        values = {
            field: _parse_number(row, field, row_number)
            for field in SCHEMA
            if field != "Datetime"
        }
        _validate_candle_values(values, row_number)
        candles.append(
            Candle(
                start=start,
                **{_field_name(field): value for field, value in values.items()},
            )
        )
        previous_start = start

    result = tuple(candles)
    # Required defensive assertion: no code path may return sealed timestamps.
    assert all(candle.start < DATA_CUTOFF for candle in result)
    return CandleBatch(
        candles=result,
        source_year=expected_year,
        rows_seen=rows_seen,
        rows_dropped_at_cutoff=dropped,
    )


def load_eurusd_5m(path: str | Path) -> CandleBatch:
    """Load one pinned 2022/2023 ``YYYY.csv.gz`` file without network access."""

    source = Path(path)
    expected_year = _year_from_path(source)
    if expected_year not in ALLOWED_YEARS:
        # In particular, this refuses the 2026 file before opening it.
        raise DataValidationError(
            f"Refusing year {expected_year}: M0 allows only 2022 and 2023"
        )

    with gzip.open(source, mode="rt", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != SCHEMA:
            raise DataValidationError(
                f"{source}: header does not match the pinned 19-column schema"
            )
        return parse_eurusd_5m(reader, expected_year=expected_year)
