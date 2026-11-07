from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from trading_system.ict_engine.causal import assert_prefix_invariance
from trading_system.ict_engine.price import PriceBasis
from trading_system.ict_engine.swings import SwingSide, swing_trace

from .primitive_helpers import UTC, candle_at, market_series


def test_immediate_neighbour_swing_is_confirmed_only_at_third_bar() -> None:
    candles = market_series([
        (1.04, 1.08, 1.02, 1.06),
        (1.06, 1.12, 1.04, 1.10),
        (1.09, 1.09, 1.03, 1.05),
    ])
    trace = swing_trace(candles)
    assert trace[0] == trace[1] == ()
    assert len(trace[2]) == 1
    swing = trace[2][0]
    assert swing.side is SwingSide.HIGH
    assert swing.price == 1.12
    assert swing.source_time == candles[1].start
    assert swing.confirmed_at == candles[2].end
    assert "U0056" in swing.claim_ids
    assert swing.qualification == "CANDIDATE_HIERARCHY_WAITING"
    assert_prefix_invariance(swing_trace, candles)
    assert trace == swing_trace(candles)


def test_equal_extreme_has_no_invented_swing_tie_break() -> None:
    candles = market_series([
        (1.04, 1.10, 1.02, 1.06),
        (1.06, 1.10, 1.04, 1.08),
        (1.08, 1.09, 1.03, 1.05),
    ])
    assert all(events == () for events in swing_trace(candles))


def test_filler_is_not_a_candle_in_the_market_neighbourhood() -> None:
    origin = datetime(2022, 1, 3, 12, 0, tzinfo=UTC)
    first = candle_at(origin, 1.04, 1.08, 1.02, 1.06)
    filler = candle_at(origin + timedelta(minutes=5), 1.0, 1.0, 1.0, 1.0, volume=0)
    second = candle_at(origin + timedelta(minutes=10), 1.06, 1.12, 1.04, 1.10)
    third = candle_at(origin + timedelta(minutes=15), 1.09, 1.09, 1.03, 1.05)
    candles = (first, filler, second, third)
    trace = swing_trace(candles)
    assert trace[1] == trace[2] == ()
    assert len(trace[3]) == 1
    assert trace[3][0].source_time == second.start
    assert_prefix_invariance(swing_trace, candles)


def test_ask_basis_is_parallel_not_averaged() -> None:
    candles = market_series([
        (1.04, 1.08, 1.02, 1.06),
        (1.06, 1.12, 1.04, 1.10),
        (1.09, 1.09, 1.03, 1.05),
    ])
    bid = swing_trace(candles, PriceBasis.BID)[2][0]
    ask = swing_trace(candles, PriceBasis.ASK)[2][0]
    assert ask.price - bid.price == pytest.approx(0.0002)
    assert bid.basis is PriceBasis.BID and ask.basis is PriceBasis.ASK
