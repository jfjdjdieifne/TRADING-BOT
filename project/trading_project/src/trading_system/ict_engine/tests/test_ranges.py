from __future__ import annotations

import pytest

from trading_system.ict_engine.causal import assert_prefix_invariance
from trading_system.ict_engine.ranges import (
    Outside,
    RangePosition,
    dealing_range_trace,
)

from .primitive_helpers import market_series


def range_candles():
    return market_series([
        (1.070, 1.100, 1.050, 1.080),
        (1.060, 1.080, 1.000, 1.040),
        (1.050, 1.120, 1.040, 1.100),
        (1.100, 1.200, 1.050, 1.180),
        (1.150, 1.160, 1.060, 1.150),
        (1.150, 1.160, 1.040, 1.050),
        (1.050, 1.210, 1.045, 1.180),
    ])


def test_latest_confirmed_leg_has_midpoint_and_relative_position() -> None:
    candles = range_candles()
    trace = dealing_range_trace(candles)
    current = trace[4].dealing_range
    assert current is not None
    assert (current.low, current.high, current.equilibrium) == (1.0, 1.2, 1.1)
    assert trace[4].position is RangePosition.PREMIUM
    assert trace[4].position_ratio == pytest.approx(0.75)
    assert trace[5].position is RangePosition.DISCOUNT
    assert trace[6].traded_outside is Outside.ABOVE
    assert trace[4].carrying_charge_status == "WAITING_CONTRACT_DATA"
    assert "U0072" in current.claim_ids and "U0083" in current.claim_ids
    assert_prefix_invariance(dealing_range_trace, candles)
    assert trace == dealing_range_trace(candles)
