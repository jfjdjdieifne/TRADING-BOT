from __future__ import annotations

import pytest

from trading_system.ict_engine.causal import assert_prefix_invariance
from trading_system.ict_engine.displacement import Energy, displacement_trace

from .primitive_helpers import market_series


def displacement_candles():
    return market_series([
        (1.010, 1.050, 1.000, 1.040),
        (1.100, 1.200, 1.100, 1.180),
        (1.150, 1.160, 1.090, 1.100),
        (1.150, 1.160, 1.120, 1.130),
        (1.130, 1.300, 1.120, 1.250),
        (1.250, 1.255, 1.240, 1.245),
    ])


def test_energy_is_relative_and_displacement_requires_close_beyond_swing() -> None:
    candles = displacement_candles()
    trace = displacement_trace(candles)
    assert [item.energy for item in trace[:3]] == [Energy.WAITING] * 3
    event = trace[4]
    assert event.energy is Energy.ENERGETIC
    assert event.range_rank == 1
    assert event.range_to_prior_max == pytest.approx(1.8)
    assert event.broken_swing is not None
    assert event.broken_swing.price == 1.20
    assert event.is_displacement
    assert "U0056" in event.claim_ids
    assert trace[5].energy is Energy.LETHARGIC
    assert not trace[5].is_displacement
    assert_prefix_invariance(displacement_trace, candles)
    assert trace == displacement_trace(candles)


def test_energy_without_swing_close_is_not_displacement() -> None:
    candles = list(displacement_candles()[:5])
    candles[4] = market_series([(1.130, 1.300, 1.120, 1.190)])[0]
    # Replace the timestamp to keep strict ordering with the hand-built series.
    from dataclasses import replace
    candles[4] = replace(candles[4], start=candles[3].start.replace(minute=candles[3].start.minute + 5))
    event = displacement_trace(tuple(candles))[4]
    assert event.energy is Energy.ENERGETIC
    assert event.broken_swing is None
    assert not event.is_displacement
