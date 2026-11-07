from __future__ import annotations

from datetime import datetime, timedelta

from trading_system.ict_engine.causal import assert_prefix_invariance
from trading_system.ict_engine.htf import (
    CalendarAnchor,
    HigherTimeframe,
    bucket_bounds,
    htf_extreme_pools,
    htf_trace,
)
from trading_system.ict_engine.swings import SwingSide

from .primitive_helpers import UTC, candle_at


def test_daily_completes_only_when_later_bucket_is_observed() -> None:
    candles = (
        candle_at(datetime(2022, 1, 3, 23, 55, tzinfo=UTC), 1.0, 1.1, 0.9, 1.05),
        candle_at(datetime(2022, 1, 4, 0, 0, tzinfo=UTC), 1.05, 1.2, 1.0, 1.15),
    )
    trace = htf_trace(candles, HigherTimeframe.DAILY, CalendarAnchor.UTC)
    assert trace[0].newly_completed == ()
    assert trace[0].last_completed is None
    assert trace[0].forming is not None
    completed = trace[1].newly_completed[0]
    assert completed.source_bar_count == 1
    assert completed.bid_high == 1.1
    assert trace[1].last_completed == completed
    assert trace[1].forming is not None
    pools = htf_extreme_pools(completed, available_at=candles[1].end)
    assert pools[0].side is SwingSide.HIGH and pools[0].level == 1.1
    assert "U0004" in pools[0].claim_ids
    assert_prefix_invariance(
        lambda rows: htf_trace(rows, HigherTimeframe.DAILY, CalendarAnchor.UTC), candles
    )


def test_utc_and_new_york_anchors_are_parallel_not_merged() -> None:
    candles = (
        candle_at(datetime(2022, 1, 3, 23, 55, tzinfo=UTC), 1.0, 1.1, 0.9, 1.05),
        candle_at(datetime(2022, 1, 4, 0, 0, tzinfo=UTC), 1.05, 1.2, 1.0, 1.15),
    )
    new_york = htf_trace(candles, HigherTimeframe.DAILY, CalendarAnchor.NEW_YORK)
    assert new_york[1].newly_completed == ()
    assert new_york[1].forming is not None
    assert new_york[1].forming.source_bar_count == 2


def test_weekly_monthly_and_dst_bucket_boundaries() -> None:
    source = datetime(2022, 7, 6, 12, tzinfo=UTC)
    week = bucket_bounds(source, HigherTimeframe.WEEKLY, CalendarAnchor.NEW_YORK)
    month = bucket_bounds(source, HigherTimeframe.MONTHLY, CalendarAnchor.NEW_YORK)
    assert week[0].isoformat() == "2022-07-04T04:00:00+00:00"
    assert week[1].isoformat() == "2022-07-11T04:00:00+00:00"
    assert month[0].isoformat() == "2022-07-01T04:00:00+00:00"
    assert month[1].isoformat() == "2022-08-01T04:00:00+00:00"


def test_all_htf_variants_are_deterministic() -> None:
    origin = datetime(2022, 1, 3, 23, 55, tzinfo=UTC)
    candles = tuple(
        candle_at(origin + timedelta(minutes=5 * i), 1.0, 1.1, 0.9, 1.05)
        for i in range(3)
    )
    for timeframe in HigherTimeframe:
        for anchor in CalendarAnchor:
            trace = htf_trace(candles, timeframe, anchor)
            assert trace == htf_trace(candles, timeframe, anchor)
