from __future__ import annotations

from datetime import datetime

from trading_system.ict_engine.causal import assert_prefix_invariance
from trading_system.ict_engine.sessions import (
    CLOCK_VARIANTS,
    NEW_YORK,
    ClockDefinition,
    observe_session,
    session_trace,
)

from .primitive_helpers import UTC, candle_at


def _observations(hour: int, minute: int = 0):
    local = datetime(2022, 7, 5, hour, minute, tzinfo=NEW_YORK)
    candle = candle_at(local.astimezone(UTC), 1.0, 1.01, 0.99, 1.005)
    return {item.definition_id: item for item in (observe_session(candle, variant) for variant in CLOCK_VARIANTS)}


def test_conflicting_london_starts_and_complete_windows_stay_parallel() -> None:
    at_two = _observations(2)
    assert at_two[ClockDefinition.LONDON_START_0200_OPEN_END].starts_here
    assert at_two[ClockDefinition.LONDON_START_0200_OPEN_END].in_window is None
    assert at_two[ClockDefinition.EURO_0200_0500].in_window is True
    assert not at_two[ClockDefinition.LONDON_START_0100_OPEN_END].starts_here

    at_one = _observations(1)
    assert at_one[ClockDefinition.LONDON_START_0100_OPEN_END].starts_here
    assert at_one[ClockDefinition.LONDON_START_0100_OPEN_END].in_window is None


def test_london_close_and_new_york_label_rejections() -> None:
    at_eleven = _observations(11)
    assert at_eleven[ClockDefinition.LONDON_CLOSE_1000_1200].in_window is True
    assert not at_eleven[ClockDefinition.NEW_YORK_SESSION_NOT_KILLZONE].killzone_label_allowed
    wide = _observations(8, 30)[ClockDefinition.WIDE_0830_NOT_NY_KILLZONE_OPEN_END]
    assert wide.starts_here and wide.in_window is None
    assert not wide.killzone_label_allowed


def test_session_trace_is_prefix_invariant_and_deterministic() -> None:
    candles = tuple(
        candle_at(datetime(2022, 7, 5, hour, tzinfo=NEW_YORK).astimezone(UTC), 1.0, 1.01, 0.99, 1.005)
        for hour in (1, 2, 3)
    )
    assert_prefix_invariance(session_trace, candles)
    assert session_trace(candles) == session_trace(candles)
