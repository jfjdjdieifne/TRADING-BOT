from __future__ import annotations

from dataclasses import fields
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import re

import pytest

from trading_system.ict_engine.causal import assert_prefix_invariance
from trading_system.ict_engine.liquidity import LiquidityPool, PoolKind
from trading_system.ict_engine.narrator import DecisionType, reading_trace, select_target
from trading_system.ict_engine.predictions import PredictionType
from trading_system.ict_engine.price import PriceBasis
from trading_system.ict_engine.ranges import (
    DealingRange,
    Outside,
    RangeObservation,
    RangePosition,
)
from trading_system.ict_engine.swings import SwingPoint, SwingSide
from trading_system.ict_engine.variants import REFERENCE, VARIANT_BY_ID, VARIANTS, TargetRanking

from .primitive_helpers import market_series
from .test_order_blocks import ob_candles

UTC = timezone.utc


def setup_candles(*, mirror: bool = False):
    specifications = [
        (1.010, 1.050, 1.000, 1.040),
        (1.100, 1.200, 1.100, 1.180),
        (1.140, 1.160, 1.090, 1.100),
        (1.150, 1.160, 1.120, 1.130),
        (1.130, 1.300, 1.120, 1.250),
        (1.160, 1.170, 1.125, 1.140),
    ]
    if mirror:
        specifications = [
            (2.4 - op, 2.4 - low, 2.4 - high, 2.4 - close)
            for op, high, low, close in specifications
        ]
    return market_series(
        specifications, origin=datetime(2022, 1, 3, 7, tzinfo=UTC)
    )


@pytest.mark.parametrize("variant", VARIANTS, ids=lambda item: item.variant_id)
def test_every_m2_variant_is_all_prefix_invariant_and_deterministic(variant) -> None:
    candles = setup_candles()
    adapted = lambda rows: reading_trace(rows, variant)
    assert_prefix_invariance(adapted, candles)
    assert adapted(candles) == adapted(candles)


@pytest.mark.parametrize("mirror,direction", [(False, "bullish"), (True, "bearish")])
def test_first_retracement_setup_is_closed_prefix_only_in_both_directions(
    mirror: bool, direction: str
) -> None:
    candles = setup_candles(mirror=mirror)
    trace = reading_trace(candles, REFERENCE)
    predictions = tuple(
        prediction
        for reading in trace
        for prediction in reading.predictions
        if prediction.prediction_type is PredictionType.SETUP_TARGET_BEFORE_STOP
    )
    assert len(predictions) == 1
    prediction = predictions[0]
    assert prediction.direction.value == direction
    assert prediction.available_at == candles[-1].end
    assert prediction.entry_price == candles[-1].bid_close
    assert prediction.target_price is not None
    assert prediction.stop_price is not None
    assert Decimal(prediction.reward_risk) >= Decimal("3")
    assert "K2C-004" in prediction.claim_ids
    assert "K2C-028" in prediction.claim_ids
    assert "K2C-042" in prediction.claim_ids
    assert "U0048" in prediction.claim_ids
    assert prediction.prediction_id.startswith("p:R00:setup:")
    assert len(trace[-1].management) == 5
    decision_types = {
        decision.decision_type
        for decision in trace[-1].decisions
        if decision.prediction_id == prediction.prediction_id
    }
    assert {
        DecisionType.TARGET_CHOICE,
        DecisionType.ENTRY_CHOICE,
        DecisionType.STOP_CHOICE,
    } <= decision_types


def test_outside_window_is_stand_aside_not_a_fake_prediction() -> None:
    trace = reading_trace(setup_candles(), VARIANT_BY_ID["V05"])
    assert not any(
        prediction.prediction_type is PredictionType.SETUP_TARGET_BEFORE_STOP
        for reading in trace
        for prediction in reading.predictions
    )
    asides = tuple(
        decision
        for reading in trace
        for decision in reading.decisions
        if decision.decision_type is DecisionType.STAND_ASIDE
    )
    assert len(asides) == 1
    assert "خارج نافذة" in asides[0].reason
    assert "K2C-028" in asides[0].claim_ids


def test_touch_and_violation_in_one_bar_is_explicitly_stand_aside() -> None:
    trace = reading_trace(ob_candles(), REFERENCE)
    assert not any(
        prediction.prediction_type is PredictionType.SETUP_TARGET_BEFORE_STOP
        for reading in trace
        for prediction in reading.predictions
    )
    aside = next(
        decision
        for reading in trace
        for decision in reading.decisions
        if decision.decision_type is DecisionType.STAND_ASIDE
    )
    assert "شمعة واحدة" in aside.reason
    assert "U0048" in aside.claim_ids


def test_narration_covers_m1_event_families_without_promoting_candidates() -> None:
    trace = reading_trace(setup_candles(), REFERENCE)
    concepts = {event.concept for reading in trace for event in reading.narration}
    assert {
        "swing_candidate",
        "fair_value_gap",
        "dealing_range",
        "displacement",
        "liquidity_pool",
        "order_block_candidate",
        "order_block_first_retracement",
        "session_clock",
        "break_even_management",
    } <= concepts
    texts = [event.text for reading in trace for event in reading.narration]
    assert any("الاعتماد الكامل في الانتظار" in text for text in texts)
    assert any("رصد لا حكم فشل" in text for text in texts) or any(
        "فجوة" in text for text in texts
    )


def test_all_visible_narrative_fields_are_arabic_not_raw_enum_values() -> None:
    daily = market_series(
        [(1.10, 1.12, 1.09, 1.11), (1.11, 1.13, 1.10, 1.12)],
        origin=datetime(2022, 1, 3, 23, 55, tzinfo=UTC),
    )
    for candles in (setup_candles(), setup_candles(mirror=True), daily):
        for variant in VARIANTS:
            for reading in reading_trace(candles, variant):
                visible = [event.text for event in reading.narration]
                visible += [decision.reason for decision in reading.decisions]
                visible += [
                    text
                    for prediction in reading.predictions
                    for text in (prediction.expectation, prediction.invalidation)
                ]
                assert all(not re.search(r"[A-Za-z]", text) for text in visible)


def test_daily_close_is_narrated_and_becomes_a_candidate_pool() -> None:
    candles = market_series(
        [(1.10, 1.12, 1.09, 1.11), (1.11, 1.13, 1.10, 1.12)],
        origin=datetime(2022, 1, 3, 23, 55, tzinfo=UTC),
    )
    trace = reading_trace(candles, REFERENCE)
    events = [event for reading in trace for event in reading.narration]
    assert any(event.concept == "higher_timeframe_close" for event in events)
    daily = [event for event in events if event.concept == "higher_timeframe_liquidity"]
    assert len(daily) == 2
    assert all(event.available_at == candles[-1].end for event in daily)


def _pool(pool_id: str, level: float, timeframe: str) -> LiquidityPool:
    now = datetime(2022, 1, 4, tzinfo=UTC)
    return LiquidityPool(
        pool_id=pool_id,
        side=SwingSide.HIGH,
        kind=PoolKind.HIGHER_TIMEFRAME_EXTREME if timeframe == "DAILY" else PoolKind.OLD_EXTREME,
        level=level,
        member_levels=(level,),
        formed_at=now,
        source_time=now,
        timeframe=timeframe,
        equality_ratio=None,
        cleanliness_rank=None,
        intervening_market_bars=None,
        claim_ids=("U0004",),
        definition_id="TEST_ONLY",
    )


def test_target_variant_changes_only_daily_priority_not_candidate_universe() -> None:
    now = datetime(2022, 1, 4, tzinfo=UTC)
    low = SwingPoint(SwingSide.LOW, 1.0, now, now, PriceBasis.BID, 1)
    high = SwingPoint(SwingSide.HIGH, 1.4, now, now, PriceBasis.BID, 2)
    dealing_range = DealingRange(low, high, 1.0, 1.4, 1.2, now, PriceBasis.BID)
    observation = RangeObservation(
        now, dealing_range, RangePosition.DISCOUNT, 0.25, Outside.INSIDE
    )
    from trading_system.ict_engine.order_blocks import OrderBlockDirection

    pools = (_pool("daily", 1.3, "DAILY"), _pool("near", 1.11, "M5"))
    daily = select_target(
        pools,
        direction=OrderBlockDirection.BULLISH,
        entry=1.1,
        range_observation=observation,
        ranking=TargetRanking.DAILY_THEN_DISTANCE,
    )
    nearest = select_target(
        pools,
        direction=OrderBlockDirection.BULLISH,
        entry=1.1,
        range_observation=observation,
        ranking=TargetRanking.DISTANCE_ONLY,
    )
    assert daily is not None and daily[0].pool_id == "daily"
    assert nearest is not None and nearest[0].pool_id == "near"


def test_variant_matrix_is_reference_plus_single_dimension_changes() -> None:
    assert len(VARIANTS) == 6
    dimension_names = {field.name for field in fields(REFERENCE)} - {"variant_id"}
    assert len(dimension_names) == 5
    for variant in VARIANTS[1:]:
        changed = {
            name
            for name in dimension_names
            if getattr(variant, name) != getattr(REFERENCE, name)
        }
        assert len(changed) == 1, (variant.variant_id, changed)
