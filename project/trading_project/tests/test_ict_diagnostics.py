from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from trading_system.ict_diagnostics.context import EntryContext
from trading_system.ict_diagnostics.direction import (
    mirrored_result,
    random_entry_index,
    resolve_barriers,
)
from trading_system.ict_diagnostics.post_stop import analyze_post_stop_case
from trading_system.ict_diagnostics.prediction_v2 import (
    _pair_choice,
    _random_pool,
    _resolve_first_pool,
    stand_aside_rows,
)
from trading_system.ict_engine.data import Candle
from trading_system.ict_engine.liquidity import LiquidityPool, PoolKind
from trading_system.ict_engine.order_blocks import (
    OrderBlockDirection,
    OrderBlockZone,
)
from trading_system.ict_engine.predictions import Prediction, PredictionType
from trading_system.ict_engine.price import PriceBasis
from trading_system.ict_engine.score_ledger import load_dev_2022
from trading_system.ict_engine.scoring import MarketBars
from trading_system.ict_engine.swings import SwingSide
from trading_system.ict_engine.variants import REFERENCE

UTC = timezone.utc
START = datetime(2022, 1, 3, tzinfo=UTC)


def candle(
    index: int,
    op: float = 1.0,
    high: float = 1.001,
    low: float = 0.999,
    close: float = 1.0,
) -> Candle:
    spread = 0.0001
    return Candle(
        start=START + timedelta(minutes=5 * index),
        bid_open=op,
        bid_high=high,
        bid_low=low,
        bid_close=close,
        bid_volume=1.0,
        ask_open=op + spread,
        ask_high=high + spread,
        ask_low=low + spread,
        ask_close=close + spread,
        ask_volume=1.0,
        spread_open=spread,
        spread_open_pips=1.0,
        spread_high=spread,
        spread_high_pips=1.0,
        spread_low=spread,
        spread_low_pips=1.0,
        spread_close=spread,
        spread_close_pips=1.0,
    )


def pool(pool_id: str, level: float, timeframe: str = "DAILY") -> LiquidityPool:
    return LiquidityPool(
        pool_id=pool_id,
        side=SwingSide.HIGH,
        kind=PoolKind.HIGHER_TIMEFRAME_EXTREME if timeframe == "DAILY" else PoolKind.OLD_EXTREME,
        level=level,
        member_levels=(level,),
        formed_at=START,
        source_time=START,
        timeframe=timeframe,
        equality_ratio=None,
        cleanliness_rank=None,
        intervening_market_bars=None,
        claim_ids=("U0024",),
        definition_id="TEST_POOL",
    )


def context_for(
    candles: list[Candle],
    *,
    target: float = 1.03,
    stop: float = 0.99,
    opening: float = 1.0,
    zone_id: str = "ob:test",
    with_prediction: bool = True,
) -> EntryContext:
    direction = OrderBlockDirection.BULLISH
    zone = OrderBlockZone(
        zone_id=zone_id,
        variant=REFERENCE.order_block,
        direction=direction,
        opening=opening,
        far_side=stop,
        run_first_time=START,
        run_last_time=START,
        created_at=START,
        claim_ids=("U0045",),
    )
    prediction = None
    if with_prediction:
        prediction = Prediction(
            prediction_id=f"p:R00:setup:{zone_id}",
            available_at=candles[0].end,
            variant_id="R00",
            concept="candidate_first_retracement_continuation",
            prediction_type=PredictionType.SETUP_TARGET_BEFORE_STOP,
            direction=direction,
            basis=PriceBasis.BID,
            claim_ids=("K2C-004",),
            expectation="test",
            invalidation="test",
            source_event_id="test",
            entry_price=1.0,
            target_id="pool:target",
            target_price=target,
            stop_price=stop,
            reward_risk=str((target - 1.0) / (1.0 - stop)),
        )
    return EntryContext(
        variant_id="R00",
        available_at=candles[0].end,
        zone=zone,
        prediction=prediction,
        aside_reason=None if with_prediction else "below_three",
        range_observation=SimpleNamespace(
            dealing_range=SimpleNamespace(high=1.1, low=0.9)
        ),
        active_pools=(pool("pool:target", target),),
    )


def test_post_stop_then_target_records_pre_stop_progress_and_zone_reaction():
    candles = [
        candle(0),
        candle(1, high=1.005, low=0.995, close=1.001),
        candle(2, high=1.0, low=0.989, close=0.995),
        candle(3, high=1.001, low=0.989, close=1.0),
        candle(4, high=1.031, low=0.999, close=1.02),
    ]
    context = context_for(candles)
    case, rows = analyze_post_stop_case(context, REFERENCE, MarketBars.from_candles(candles))
    assert case["original"]["outcome"] == "STOP_FIRST"
    assert case["original"]["bars_from_entry"] == 2
    assert case["primary_class"] == "DIRECTION-RIGHT-STOP-TOO-TIGHT"
    assert case["post_stop"]["stop_to_target_bars"] == 2
    assert case["post_stop"]["entry_to_later_target_bars"] == 4
    assert case["post_stop"]["target_after_stop_within_original"] is True
    assert case["post_stop"]["slow"] is False
    assert case["before_stop"]["best_favorable"] == pytest.approx(0.005)
    assert case["before_stop"]["best_fraction_of_target"] == pytest.approx(1 / 6)
    assert case["before_stop"]["best_multiple_of_stop"] == pytest.approx(0.5)
    assert case["before_target"]["worst_adverse"] == pytest.approx(0.011)
    assert case["zone"]["tested"] is True
    assert case["zone"]["class"] == "REACTION_THEN_SLICE"
    assert case["observed_reward_risk"] == pytest.approx(3.0)
    assert case["target_audit"]["selected_is_nearest"] is True
    assert len(rows) == 5
    assert rows[2]["bars_from_stop"] is None
    assert rows[3]["bars_from_stop"] == 1


def test_stopped_then_extended_target_is_slow_and_direct_slice():
    candles = [candle(0), candle(1, high=1.0, low=0.989, close=0.995)]
    candles += [candle(index, high=1.001, low=0.998, close=1.0) for index in range(2, 10)]
    candles.append(candle(10, high=1.031, low=0.999, close=1.02))
    case, _ = analyze_post_stop_case(
        context_for(candles), REFERENCE, MarketBars.from_candles(candles)
    )
    assert case["primary_class"] == "DIRECTION-RIGHT-STOP-TOO-TIGHT"
    assert case["post_stop"]["stop_to_target_bars"] == 9
    assert case["post_stop"]["slow"] is True
    assert case["zone"]["class"] == "DIRECT_SLICE"
    assert case["before_stop"]["bars"] == 0


def test_stopped_then_moved_away_without_target_is_direction_wrong():
    candles = [candle(0), candle(1, high=1.0, low=0.989, close=0.995)]
    candles += [candle(index, high=1.0, low=0.988, close=0.995) for index in range(2, 1153)]
    case, _ = analyze_post_stop_case(
        context_for(candles), REFERENCE, MarketBars.from_candles(candles)
    )
    assert case["primary_class"] == "DIRECTION-WRONG"
    assert case["post_stop"]["never_reached_complete_extended"] is True
    assert case["post_stop"]["observed_until"] == candles[-1].end.isoformat()


def test_symmetric_barriers_tie_no_touch_truncation_and_mirror():
    tied = [candle(0), candle(1, high=1.011, low=0.989)]
    result = resolve_barriers(
        MarketBars.from_candles(tied),
        entry_index=0,
        entry=1.0,
        distance=0.01,
        direction=OrderBlockDirection.BULLISH,
        basis=PriceBasis.BID,
    )
    assert result["outcome"] == "UNJUDGEABLE_SAME_BAR"
    assert mirrored_result(result)["outcome"] == "UNJUDGEABLE_SAME_BAR"

    no_touch = [candle(index, high=1.005, low=0.995) for index in range(289)]
    result = resolve_barriers(
        MarketBars.from_candles(no_touch),
        entry_index=0,
        entry=1.0,
        distance=0.01,
        direction=OrderBlockDirection.BULLISH,
        basis=PriceBasis.BID,
    )
    assert result["outcome"] == "NO_TOUCH"
    truncated = resolve_barriers(
        MarketBars.from_candles(no_touch[:2]),
        entry_index=0,
        entry=1.0,
        distance=0.01,
        direction=OrderBlockDirection.BULLISH,
        basis=PriceBasis.BID,
    )
    assert truncated["outcome"] == "TRUNCATED"


def test_seeded_selection_is_stable_and_first_pool_tie_is_unjudgeable():
    candles = [candle(0), candle(1, high=1.031, low=0.999)]
    context = context_for(candles)
    candidates = (pool("pool:b", 1.02), pool("pool:a", 1.01))
    resolution = _resolve_first_pool(
        context, candidates, MarketBars.from_candles(candles), REFERENCE
    )
    assert resolution["status"] == "FIRST_TOUCH_TIE"
    assert resolution["winner_ids"] == ["pool:a", "pool:b"]
    assert random_entry_index((1, 2, 3), variant_id="R00", case_id="case", multiple=4) == random_entry_index((1, 2, 3), variant_id="R00", case_id="case", multiple=4)
    assert _random_pool(candidates, "cluster").pool_id == _random_pool(candidates, "cluster").pool_id


def test_entry_pair_partial_ranking_and_stand_aside_excursion():
    candles = [candle(index, high=1.002, low=0.998, close=1.001) for index in range(49)]
    deeper = context_for(candles, opening=0.999, zone_id="ob:deep")
    shallower = context_for(candles, opening=1.0, zone_id="ob:shallow")
    chosen, other = _pair_choice((shallower, deeper))
    assert chosen.zone.zone_id == "ob:deep"
    aside = context_for(candles, with_prediction=False)
    rows = stand_aside_rows((aside,), REFERENCE, MarketBars.from_candles(candles))
    assert len(rows) == 1
    assert rows[0]["category"] == "ASIDE"
    assert rows[0]["observed_bars"] == 48
    assert rows[0]["mfe"] == pytest.approx(0.001)
    assert rows[0]["mae"] == pytest.approx(0.003)
    assert rows[0]["terminal"] == pytest.approx(0.0)


def test_2023_is_rejected_before_open(tmp_path):
    with pytest.raises(ValueError, match="refuses"):
        load_dev_2022(tmp_path / "2023.csv.gz")
