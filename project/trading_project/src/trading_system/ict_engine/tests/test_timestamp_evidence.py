from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from trading_system.ict_engine.data import parse_eurusd_5m
from trading_system.ict_engine.timestamp_evidence import (
    EVENT_OFFSETS,
    annual_event_alignment,
    event_alignment,
    nfp_release_times,
)

from .helpers import source_row

UTC = timezone.utc


def test_nfp_schedule_is_complete_and_dst_aware() -> None:
    releases_2022 = nfp_release_times(2022)
    releases_2023 = nfp_release_times(2023)

    assert len(releases_2022) == len(releases_2023) == 12
    assert releases_2022[0] == datetime(2022, 1, 7, 13, 30, tzinfo=UTC)
    assert releases_2022[2] == datetime(2022, 3, 4, 13, 30, tzinfo=UTC)
    assert releases_2022[3] == datetime(2022, 4, 1, 12, 30, tzinfo=UTC)
    assert releases_2022[10] == datetime(2022, 11, 4, 12, 30, tzinfo=UTC)
    assert releases_2023[2] == datetime(2023, 3, 10, 13, 30, tzinfo=UTC)
    assert releases_2023[3] == datetime(2023, 4, 7, 12, 30, tzinfo=UTC)


def test_event_alignment_identifies_bar_start_response_without_threshold() -> None:
    release = datetime(2022, 4, 1, 12, 30, tzinfo=UTC)
    ranges = {-5: 0.001, 0: 0.010, 5: 0.002, 10: 0.001}
    rows = []
    for offset in EVENT_OFFSETS:
        minutes = int(offset.total_seconds() // 60)
        size = ranges[minutes]
        start = release + offset
        rows.append(
            source_row(
                start,
                BidOpen=1.10,
                BidHigh=1.10 + size,
                BidLow=1.10,
                BidClose=1.10 + size / 2,
                AskOpen=1.1002,
                AskHigh=1.1002 + size,
                AskLow=1.1002,
                AskClose=1.1002 + size / 2,
            )
        )
    candles = parse_eurusd_5m(rows, expected_year=2022).candles

    evidence = event_alignment(candles, release)
    assert evidence.largest_offset_minutes == (0,)
    assert evidence.release_bar_rank_on_utc_day == 1
    assert evidence.ranges_by_offset_minutes[1][0] == 0
    assert evidence.ranges_by_offset_minutes[1][1] == pytest.approx(0.010)


def test_annual_diagnostic_has_one_result_per_predeclared_release() -> None:
    release = nfp_release_times(2022)[0]
    rows = [
        source_row(release + offset)
        for offset in EVENT_OFFSETS
    ]
    candles = parse_eurusd_5m(rows, expected_year=2022).candles
    # The annual function must not silently select a subset of events.
    try:
        annual_event_alignment(candles, 2022)
    except ValueError as exc:
        assert "No event-neighbouring candles" in str(exc)
    else:
        raise AssertionError("Missing releases must not be silently skipped")
