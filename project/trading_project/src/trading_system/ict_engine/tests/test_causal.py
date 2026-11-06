from __future__ import annotations

import pytest

from trading_system.ict_engine.causal import (
    PrefixInvarianceError,
    assert_prefix_invariance,
)

from .helpers import synthetic_candles


def running_maximum(candles):
    result = []
    maximum = None
    for candle in candles:
        maximum = (
            candle.bid_high if maximum is None else max(maximum, candle.bid_high)
        )
        result.append(maximum)
    return result


def test_causal_trace_passes_every_prefix() -> None:
    assert_prefix_invariance(running_maximum, synthetic_candles())


def test_causal_trace_passes_selected_real_data_style_prefixes() -> None:
    candles = synthetic_candles()
    assert_prefix_invariance(
        running_maximum, candles, lengths=(0, 1, 3, len(candles))
    )


def test_future_dependent_trace_fails() -> None:
    def last_close_for_every_bar(candles):
        return [candles[-1].bid_close] * len(candles) if candles else []

    with pytest.raises(PrefixInvarianceError, match="Future truncation changed"):
        assert_prefix_invariance(last_close_for_every_bar, synthetic_candles())


def test_wrong_output_cardinality_fails_explicitly() -> None:
    with pytest.raises(PrefixInvarianceError, match="one output per input"):
        assert_prefix_invariance(lambda candles: [1], synthetic_candles(2))


def test_invalid_requested_prefix_is_rejected() -> None:
    candles = synthetic_candles(2)
    with pytest.raises(ValueError, match="outside"):
        assert_prefix_invariance(running_maximum, candles, lengths=(3,))
