"""Opt-in checks against the two pinned local files; never downloads data."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from trading_system.ict_engine.causal import assert_prefix_invariance
from trading_system.ict_engine.data import DATA_CUTOFF, load_eurusd_5m
from trading_system.ict_engine.timestamp_evidence import (
    annual_event_alignment,
    nfp_release_times,
)

_DATA_DIR = os.environ.get("ICT_ENGINE_M0_DATA_DIR")
pytestmark = pytest.mark.skipif(
    _DATA_DIR is None,
    reason="Set ICT_ENGINE_M0_DATA_DIR to the local 2022/2023-only data directory",
)

_EXPECTED = {
    2022: {
        "rows": 105_120,
        "sha256": "490d4fb9f1a07a1d7909477debbd935efc568fe1885475a7704a855ade9ab17e",
        "zero_volume": 30_247,
        "release_largest": 11,
        "plus5_largest": 1,
    },
    2023: {
        "rows": 104_544,
        "sha256": "4aaacd30e944b474003c5ceb595dcf74011c81a4b7841d341f02909c6a270a96",
        "zero_volume": 30_464,
        "release_largest": 12,
        "plus5_largest": 0,
    },
}


@pytest.fixture(scope="module")
def real_batches():
    root = Path(_DATA_DIR) if _DATA_DIR is not None else Path(".")
    return {year: load_eurusd_5m(root / f"{year}.csv.gz") for year in _EXPECTED}


def _running_maximum(candles):
    trace = []
    maximum = None
    for candle in candles:
        maximum = (
            candle.bid_high if maximum is None else max(maximum, candle.bid_high)
        )
        trace.append(maximum)
    return trace


@pytest.mark.parametrize("year", (2022, 2023))
def test_real_loader_identity_cutoff_and_prefix(year, real_batches) -> None:
    batch = real_batches[year]
    candles = batch.candles
    expected = _EXPECTED[year]
    source = Path(_DATA_DIR) / f"{year}.csv.gz"

    assert hashlib.sha256(source.read_bytes()).hexdigest() == expected["sha256"]
    assert batch.rows_seen == len(candles) == expected["rows"]
    assert batch.rows_dropped_at_cutoff == 0
    assert all(candle.start < DATA_CUTOFF for candle in candles)
    assert sum(
        candle.bid_volume == 0 and candle.ask_volume == 0 for candle in candles
    ) == expected["zero_volume"]

    first_release = nfp_release_times(year)[0]
    event_index = next(
        index for index, candle in enumerate(candles) if candle.start == first_release
    )
    assert_prefix_invariance(
        _running_maximum,
        candles,
        lengths=(0, 1, 288, event_index, event_index + 1, len(candles) - 1, len(candles)),
    )


@pytest.mark.parametrize("year", (2022, 2023))
def test_real_timestamp_alignment_unchanged(year, real_batches) -> None:
    events = annual_event_alignment(real_batches[year].candles, year)
    expected = _EXPECTED[year]

    assert len(events) == 12
    assert sum(event.largest_offset_minutes == (0,) for event in events) == expected[
        "release_largest"
    ]
    assert sum(event.largest_offset_minutes == (5,) for event in events) == expected[
        "plus5_largest"
    ]
    assert all(
        event.release_bar_rank_on_utc_day is not None
        and event.release_bar_rank_on_utc_day <= 10
        for event in events
    )
