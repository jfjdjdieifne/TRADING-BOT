from __future__ import annotations

from trading_system.ict_engine.causal import assert_prefix_invariance
from trading_system.ict_engine.order_blocks import (
    OrderBlockDirection,
    OrderBlockEventKind,
    OrderBlockVariant,
    order_block_trace,
)

from .primitive_helpers import market_series


def ob_candles():
    return market_series([
        (1.010, 1.050, 1.000, 1.040),
        (1.100, 1.200, 1.100, 1.180),
        (1.140, 1.160, 1.090, 1.100),
        (1.150, 1.160, 1.120, 1.130),
        (1.130, 1.300, 1.120, 1.250),
        (1.240, 1.250, 1.080, 1.100),
    ])


def test_two_order_block_boundaries_remain_separate_candidates() -> None:
    candles = ob_candles()
    opening = order_block_trace(candles, OrderBlockVariant.OPENING_OF_OPPOSITE_CLOSE_RUN)
    last = order_block_trace(candles, OrderBlockVariant.LAST_OPPOSITE_CLOSE_CANDLE)
    first_zone = opening[4][0].zone
    second_zone = last[4][0].zone
    assert opening[4][0].kind is OrderBlockEventKind.CANDIDATE_CREATED
    assert first_zone.direction is OrderBlockDirection.BULLISH
    assert first_zone.opening == 1.14
    assert first_zone.far_side == 1.09
    assert second_zone.opening == 1.15
    assert second_zone.far_side == 1.12
    assert first_zone.claim_ids != second_zone.claim_ids
    assert "U0051" in first_zone.claim_ids
    assert first_zone.qualification.startswith("CANDIDATE_")
    assert opening[5][0].kind is OrderBlockEventKind.VIOLATED
    assert_prefix_invariance(
        lambda rows: order_block_trace(rows, OrderBlockVariant.OPENING_OF_OPPOSITE_CLOSE_RUN),
        candles,
    )
    assert opening == order_block_trace(candles, OrderBlockVariant.OPENING_OF_OPPOSITE_CLOSE_RUN)


def test_bearish_last_up_candle_variant() -> None:
    # Exact mirror of the bullish energy/swing fixture, with two up-close bars.
    candles = market_series([
        (0.990, 1.000, 0.950, 0.960),
        (0.900, 0.900, 0.800, 0.820),
        (0.850, 0.910, 0.840, 0.900),
        (0.850, 0.880, 0.840, 0.870),
        (0.870, 0.880, 0.700, 0.750),
        (0.760, 0.920, 0.750, 0.900),
    ])
    trace = order_block_trace(candles, OrderBlockVariant.LAST_OPPOSITE_CLOSE_CANDLE)
    created = trace[4][0]
    assert created.kind is OrderBlockEventKind.CANDIDATE_CREATED
    assert created.zone.direction is OrderBlockDirection.BEARISH
    assert created.zone.opening == 0.85
    assert created.zone.far_side == 0.88
    assert "U0046" in created.zone.claim_ids
    assert trace[5][0].kind is OrderBlockEventKind.VIOLATED
