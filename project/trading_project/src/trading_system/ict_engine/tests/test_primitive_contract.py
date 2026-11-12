"""One causal/determinism contract across every primitive variant."""

from __future__ import annotations

import pytest

from trading_system.ict_engine.causal import assert_prefix_invariance
from trading_system.ict_engine.displacement import displacement_trace
from trading_system.ict_engine.gaps import fvg_trace
from trading_system.ict_engine.htf import CalendarAnchor, HigherTimeframe, htf_trace
from trading_system.ict_engine.liquidity import liquidity_trace
from trading_system.ict_engine.order_blocks import OrderBlockVariant, order_block_trace
from trading_system.ict_engine.price import PriceBasis
from trading_system.ict_engine.ranges import dealing_range_trace
from trading_system.ict_engine.swings import swing_trace

from .test_order_blocks import ob_candles

PRICE_FUNCTIONS = (swing_trace, fvg_trace, displacement_trace, dealing_range_trace, liquidity_trace)


@pytest.mark.parametrize("function", PRICE_FUNCTIONS)
@pytest.mark.parametrize("basis", PriceBasis)
def test_every_price_variant_is_prefix_invariant_and_deterministic(function, basis) -> None:
    candles = ob_candles()
    adapted = lambda rows: function(rows, basis)
    assert_prefix_invariance(adapted, candles)
    assert adapted(candles) == adapted(candles)


@pytest.mark.parametrize("variant", OrderBlockVariant)
def test_every_order_block_variant_is_prefix_invariant_and_deterministic(variant) -> None:
    candles = ob_candles()
    adapted = lambda rows: order_block_trace(rows, variant)
    assert_prefix_invariance(adapted, candles)
    assert adapted(candles) == adapted(candles)


@pytest.mark.parametrize("timeframe", HigherTimeframe)
@pytest.mark.parametrize("anchor", CalendarAnchor)
def test_every_htf_variant_is_prefix_invariant_and_deterministic(timeframe, anchor) -> None:
    candles = ob_candles()
    adapted = lambda rows: htf_trace(rows, timeframe, anchor)
    assert_prefix_invariance(adapted, candles)
    assert adapted(candles) == adapted(candles)
