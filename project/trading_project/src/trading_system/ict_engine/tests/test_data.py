from __future__ import annotations

import csv
import gzip
from datetime import datetime, timedelta, timezone

import pytest

from trading_system.ict_engine.data import (
    DATA_CUTOFF,
    SCHEMA,
    DataValidationError,
    load_eurusd_5m,
    parse_eurusd_5m,
)

from .helpers import source_row, synthetic_candles

UTC = timezone.utc


def test_parse_uses_bar_start_and_exclusive_end() -> None:
    start = datetime(2022, 1, 3, 12, 30, tzinfo=UTC)
    batch = parse_eurusd_5m([source_row(start)], expected_year=2022)

    assert len(batch) == 1
    assert batch.candles[0].start == start
    assert batch.candles[0].end == datetime(2022, 1, 3, 12, 35, tzinfo=UTC)
    assert batch.rows_seen == 1
    assert batch.rows_dropped_at_cutoff == 0


def test_cutoff_drops_rows_before_numeric_parsing_and_asserts_output() -> None:
    allowed = source_row(datetime(2022, 12, 31, 23, 55, tzinfo=UTC))
    sealed = source_row(DATA_CUTOFF, BidOpen="not-a-number", BidVolume=None)
    after_sealed = source_row(
        DATA_CUTOFF + timedelta(minutes=5), AskClose="also-not-a-number"
    )

    batch = parse_eurusd_5m(
        [allowed, sealed, after_sealed], expected_year=2022
    )

    assert batch.rows_seen == 3
    assert batch.rows_dropped_at_cutoff == 2
    assert len(batch) == 1
    assert all(candle.start < DATA_CUTOFF for candle in batch.candles)


def test_only_2022_and_2023_are_accepted() -> None:
    for year in (2021, 2024, 2025, 2026):
        with pytest.raises(DataValidationError, match="permits only"):
            parse_eurusd_5m([], expected_year=year)


def test_loader_refuses_2026_before_opening_file(tmp_path) -> None:
    missing_2026 = tmp_path / "2026.csv.gz"
    with pytest.raises(DataValidationError, match="Refusing year 2026"):
        load_eurusd_5m(missing_2026)


def test_gzip_loader_round_trip_is_deterministic(tmp_path) -> None:
    source = tmp_path / "2022.csv.gz"
    rows = [
        source_row(datetime(2022, 1, 3, tzinfo=UTC)),
        source_row(datetime(2022, 1, 3, 0, 5, tzinfo=UTC)),
    ]
    with gzip.open(source, "wt", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SCHEMA)
        writer.writeheader()
        writer.writerows(rows)

    first = load_eurusd_5m(source)
    second = load_eurusd_5m(source)
    assert first == second
    assert len(first) == 2


def test_naive_timestamp_is_rejected() -> None:
    row = source_row(datetime(2022, 1, 3, tzinfo=UTC))
    row["Datetime"] = "2022-01-03T00:00:00"
    with pytest.raises(DataValidationError, match="explicit timezone"):
        parse_eurusd_5m([row], expected_year=2022)


def test_unaligned_timestamp_is_rejected() -> None:
    row = source_row(datetime(2022, 1, 3, 0, 1, tzinfo=UTC))
    with pytest.raises(DataValidationError, match="five-minute grid"):
        parse_eurusd_5m([row], expected_year=2022)


def test_duplicate_or_reordered_timestamps_are_not_sorted_into_validity() -> None:
    start = datetime(2022, 1, 3, tzinfo=UTC)
    rows = [source_row(start), source_row(start)]
    with pytest.raises(DataValidationError, match="strictly increasing"):
        parse_eurusd_5m(rows, expected_year=2022)


def test_invalid_ohlc_is_rejected() -> None:
    row = source_row(datetime(2022, 1, 3, tzinfo=UTC), BidHigh=1.0)
    with pytest.raises(DataValidationError, match="Bid OHLC envelope"):
        parse_eurusd_5m([row], expected_year=2022)


def test_loader_rejects_changed_schema(tmp_path) -> None:
    source = tmp_path / "2022.csv.gz"
    with gzip.open(source, "wt", encoding="utf-8", newline="") as handle:
        handle.write("Datetime,BidOpen\n")
    with pytest.raises(DataValidationError, match="19-column schema"):
        load_eurusd_5m(source)


def test_synthetic_fixture_has_expected_cardinality() -> None:
    candles = synthetic_candles(8)
    assert len(candles) == 8
    assert all(
        later.start - earlier.start == timedelta(minutes=5)
        for earlier, later in zip(candles, candles[1:], strict=False)
    )
