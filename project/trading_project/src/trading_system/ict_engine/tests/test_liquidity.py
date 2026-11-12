from __future__ import annotations

from datetime import datetime, timezone

import pytest

from trading_system.ict_engine.causal import assert_prefix_invariance
from trading_system.ict_engine.liquidity import (
    DrawCandidate,
    PoolEventKind,
    PoolKind,
    rank_draws,
    liquidity_trace,
)
from trading_system.ict_engine.swings import SwingSide

from .primitive_helpers import market_series

UTC = timezone.utc


def pool_candles():
    return market_series([
        (1.030, 1.050, 1.000, 1.040),
        (1.050, 1.100, 1.020, 1.080),
        (1.050, 1.060, 1.040, 1.050),
        (1.050, 1.080, 1.010, 1.030),
        (1.040, 1.090, 1.030, 1.080),
        (1.080, 1.120, 1.040, 1.100),
        (1.060, 1.070, 1.030, 1.040),
        (1.050, 1.130, 1.045, 1.080),
    ])


def test_relative_pair_has_ratio_rank_and_run_return_sequence() -> None:
    candles = pool_candles()
    trace = liquidity_trace(candles)
    formed = [event.pool for event in trace[6] if event.kind is PoolEventKind.FORMED]
    pair = next(pool for pool in formed if pool.kind is PoolKind.RELATIVE_EQUAL_PAIR)
    assert pair.side is SwingSide.HIGH
    assert pair.member_levels == (1.10, 1.12)
    assert pair.level == 1.12
    assert pair.equality_ratio == pytest.approx(0.02 / 0.11)
    assert pair.cleanliness_rank == 1
    assert pair.intervening_market_bars == 4
    kinds = [event.kind for event in trace[7] if event.pool.pool_id == pair.pool_id]
    assert kinds == [PoolEventKind.TAKEN, PoolEventKind.RETURNED_INSIDE]
    assert "U0022" in pair.claim_ids
    assert_prefix_invariance(liquidity_trace, candles)
    assert trace == liquidity_trace(candles)


def test_draw_distance_and_timeframe_significance_are_separate_rankings() -> None:
    now = datetime(2022, 1, 3, tzinfo=UTC)
    near = DrawCandidate("near", "old_extreme", 1.10, 1.10, now, "M5", ("U0004",))
    far_daily = DrawCandidate("far", "old_extreme", 1.30, 1.30, now, "DAILY", ("U0024",))
    ranked = rank_draws((far_daily, near), current_price=1.0, recent_range=0.2)
    assert ranked[0].draw.candidate_id == "near"
    assert ranked[0].distance_ratio == pytest.approx(0.5)
    assert ranked[0].distance_rank == 1
    assert ranked[0].timeframe_significance_rank == 2
    assert ranked[1].timeframe_significance_rank == 1


def test_weekly_monthly_significance_order_is_not_invented() -> None:
    now = datetime(2022, 1, 3, tzinfo=UTC)
    weekly = DrawCandidate("week", "old_extreme", 1.2, 1.2, now, "WEEKLY", ())
    monthly = DrawCandidate("month", "old_extreme", 1.3, 1.3, now, "MONTHLY", ())
    ranked = rank_draws((weekly, monthly), current_price=1.0, recent_range=0.2)
    assert all(item.timeframe_significance_rank is None for item in ranked)


def test_nonpositive_recent_range_cannot_hide_distance_comparison() -> None:
    now = datetime(2022, 1, 3, tzinfo=UTC)
    draw = DrawCandidate("x", "old_extreme", 1.1, 1.1, now, "M5", ())
    with pytest.raises(ValueError, match="positive"):
        rank_draws((draw,), current_price=1.0, recent_range=0)
