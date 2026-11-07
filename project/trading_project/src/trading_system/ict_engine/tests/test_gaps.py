from __future__ import annotations

import pytest

from trading_system.ict_engine.causal import assert_prefix_invariance
from trading_system.ict_engine.gaps import (
    FairValueGap,
    GapDirection,
    GapEventKind,
    fvg_trace,
)
from trading_system.ict_engine.price import PriceBasis

from .primitive_helpers import market_series


def bullish_candles():
    return market_series([
        (1.095, 1.100, 1.090, 1.098),
        (1.100, 1.130, 1.100, 1.125),
        (1.125, 1.140, 1.110, 1.130),
        (1.130, 1.135, 1.105, 1.120),
        (1.120, 1.121, 1.090, 1.100),
    ])


def test_bullish_fvg_creation_touch_and_full_close_are_separate_observables() -> None:
    candles = bullish_candles()
    trace = fvg_trace(candles)
    created = trace[2][0]
    assert created.kind is GapEventKind.CREATED
    gap = created.gap
    assert gap.direction is GapDirection.BULLISH
    assert (gap.lower, gap.upper) == (1.10, 1.11)
    assert trace[3][0].kind is GapEventKind.FIRST_TOUCH
    assert trace[4][0].kind is GapEventKind.FULLY_CLOSED
    assert trace[4][0].claim_ids == ("U0037",)
    assert_prefix_invariance(fvg_trace, candles)
    assert trace == fvg_trace(candles)


def test_bearish_fvg_geometry() -> None:
    candles = market_series([
        (1.105, 1.110, 1.100, 1.102),
        (1.100, 1.101, 1.070, 1.075),
        (1.075, 1.090, 1.060, 1.070),
    ])
    events = fvg_trace(candles)[2]
    assert len(events) == 1
    assert events[0].gap.direction is GapDirection.BEARISH
    assert (events[0].gap.lower, events[0].gap.upper) == (1.09, 1.10)


def test_bid_and_ask_gap_variants_are_not_mixed() -> None:
    candles = bullish_candles()
    bid = fvg_trace(candles, PriceBasis.BID)[2][0].gap
    ask = fvg_trace(candles, PriceBasis.ASK)[2][0].gap
    assert ask.lower - bid.lower == pytest.approx(0.0002)
    assert ask.upper - bid.upper == pytest.approx(0.0002)
    assert bid.basis is not ask.basis
