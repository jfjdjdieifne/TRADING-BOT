"""Adversarial test suite for Module 7.0 — Causal Multi-Timeframe ICT Recommendation & Dynamic Trade Lifecycle Engine."""

import time
import pytest

from trading_system.market_understanding.availability import (
    InformationKey,
    InformationPhase,
)
from trading_system.research.information_time import INFORMATION_KEY_VERSION
from trading_system.market_understanding.contracts import (
    IllegalCausalReference,
    PrematureAvailability,
    SchemaViolation,
    TypedState,
)
from trading_system.market_understanding.final_evaluation_and_reality import (
    CausalMarketUnderstandingDiagnosticReport,
    ExplanationStateRecord,
)
from trading_system.market_understanding.price_path import exact_metric
from trading_system.recommendation.causal_ict_lifecycle import (
    ACTION_EMIT_CONTINUATION_REENTRY_FOR_HIGHER_TARGETS,
    ACTION_EXIT_FULL_AT_FINAL_TARGET,
    ACTION_EXIT_FULL_ON_EXHAUSTION_OR_REVERSAL,
    ACTION_EXIT_STOP_LOSS_HIT,
    ACTION_HOLD_INITIAL_STRUCTURAL_STOP,
    ACTION_RATCHET_STOP_TO_CONFIRMED_SWING,
    ACTION_TAKE_PARTIAL_AND_TRAIL_RUNNER,
    ACTION_UNLOCK_HIGHER_TARGET_AND_RATCHET_STOP,
    DECISION_CONTINUATION_REENTRY_LONG,
    DECISION_CONTINUATION_REENTRY_SHORT,
    DECISION_ENTER_LONG,
    DECISION_ENTER_SHORT,
    DECISION_WAIT_NO_QUALIFYING_SETUP,
    DIRECTION_LONG,
    DIRECTION_SHORT,
    FLOW_REGIME_ABSORPTION_AGAINST,
    FLOW_REGIME_NEUTRAL,
    FLOW_REGIME_SUPPORTIVE_DISPLACEMENT,
    RANGE_ZONE_DISCOUNT,
    RANGE_ZONE_EQUILIBRIUM,
    RANGE_ZONE_PREMIUM,
    CausalICTConfluenceObservation,
    ConfirmedStructuralTrailSwing,
    ContinuationPullbackSetup,
    OpenTradeLifecycleState,
    StructuralLiquidityTargetPool,
    StructuralTargetLadder,
    TradeRiskAndQualificationContract,
    evaluate_causal_ict_recommendation_as_of,
    evaluate_open_trade_lifecycle_as_of,
)


def _pos_key(index: int, timeline_id: str = "BTCUSDT_1M") -> InformationKey:
    return InformationKey(
        information_key_version=INFORMATION_KEY_VERSION,
        timeline_id=timeline_id,
        bar_position=index,
        event_time_utc=None,
        information_phase=InformationPhase.COMPLETED_ROW_AVAILABLE,
        deterministic_sequence=0,
    )


def _make_muf_report(
    at_index: int = 50,
    cont_rate: float = 0.65,
    visible_episodes: int = 24,
    non_overlapping_clusters: int = 18,
    right_censored: int = 3,
) -> CausalMarketUnderstandingDiagnosticReport:
    qkey = _pos_key(at_index)
    expl = ExplanationStateRecord.create(
        explanation_id=f"expl_{at_index}",
        pattern_contract_ref="CAUSAL_WAVE_STATE_CONTINUATION_PATTERN_V1",
        explanation_state="PATTERN_REQUIREMENTS_SATISFIED",
        required_fact_refs=("wave_conf_1", "wave_conf_2"),
        contradicting_fact_refs=(),
        same_information_batch_order_unknown=False,
        explanation_information_key=qkey,
    )
    return CausalMarketUnderstandingDiagnosticReport(
        timeline_id="BTCUSDT_1M",
        query_key=qkey,
        representation_spec_hash="rep_hash_001",
        authority_policy_hash="pol_hash_001",
        state_catalog_hash="scat_hash_001",
        graph_spec_hash="gspec_hash_001",
        forming_wave_process_ids=("wave_active_1",),
        confirmed_wave_process_ids=("wave_conf_1", "wave_conf_2"),
        active_running_efficiency_ratio=exact_metric(0.82),
        latest_confirmed_wave_efficiency_ratio=exact_metric(0.79),
        latest_confirmed_relative_amplitude_ratio=exact_metric(1.35),
        visible_episode_count=visible_episodes,
        non_overlapping_span_cluster_count=non_overlapping_clusters,
        historical_uncensored_continuation_count=int(
            round((visible_episodes - right_censored) * cont_rate)
        ),
        historical_right_censored_count=right_censored,
        empirical_continuation_rate=exact_metric(cont_rate),
        explanation_record=expl,
        statistical_independence_claim="NOT_CLAIMED",
        research_debt_024_status="OPEN",
    )


def _make_risk_contract() -> TradeRiskAndQualificationContract:
    return TradeRiskAndQualificationContract(
        account_equity=10000.0,
        capital_risk_fraction=0.01,
        min_qualification_rr=3.0,
        transaction_cost_in_r=0.05,
        impulse_expansion_min_causal_rank=0.70,
        exhaustion_max_causal_rank=0.30,
    )


def _make_long_pools() -> tuple[StructuralLiquidityTargetPool, ...]:
    return (
        StructuralLiquidityTargetPool(
            pool_id="POOL_T1_3R",
            pool_kind="INTERNAL_BSL_AND_FVG",
            scale_label="M15",
            target_price=103000.0,
            origin_key=_pos_key(10),
            available_key=_pos_key(15),
        ),
        StructuralLiquidityTargetPool(
            pool_id="POOL_T2_6R",
            pool_kind="HTF_H1_SWING_HIGH_LIQUIDITY",
            scale_label="H1",
            target_price=106000.0,
            origin_key=_pos_key(5),
            available_key=_pos_key(12),
        ),
        StructuralLiquidityTargetPool(
            pool_id="POOL_T3_12R_RUNNER",
            pool_kind="MAJOR_H4_EXTERNAL_BSL_POOL",
            scale_label="H4",
            target_price=112000.0,
            origin_key=_pos_key(1),
            available_key=_pos_key(8),
        ),
    )


def _make_long_confluence(
    at_index: int = 50,
    zone: str = RANGE_ZONE_DISCOUNT,
    poi_mitigated: bool = True,
    ltf_confirmed: bool = True,
    ltf_dir: str = DIRECTION_LONG,
    stop_price: float = 99000.0,
    eff_rank: float = 0.80,
    vel_rank: float = 0.78,
    proxy_flow: str = FLOW_REGIME_SUPPORTIVE_DISPLACEMENT,
    actual_flow: str | TypedState = FLOW_REGIME_SUPPORTIVE_DISPLACEMENT,
) -> CausalICTConfluenceObservation:
    return CausalICTConfluenceObservation(
        at_key=_pos_key(at_index),
        htf_parent_direction=DIRECTION_LONG,
        htf_dealing_range_zone=zone,
        htf_poi_mitigated=poi_mitigated,
        htf_poi_kind="HTF_ORDER_BLOCK_AND_FVG",
        htf_poi_origin_key=_pos_key(20),
        htf_poi_available_key=_pos_key(25),
        ltf_break_confirmed=ltf_confirmed,
        ltf_break_kind="CHOCH_AND_BOS",
        ltf_break_direction=ltf_dir,
        ltf_break_origin_key=_pos_key(42),
        ltf_break_available_key=_pos_key(48),
        ltf_invalidation_swing_price=stop_price,
        ltf_invalidation_origin_key=_pos_key(40),
        ltf_invalidation_available_key=_pos_key(45),
        child_wave_efficiency_rank=eff_rank,
        child_wave_velocity_rank=vel_rank,
        proxy_flow_regime=proxy_flow,
        actual_flow_regime=actual_flow,
    )


def test_01_risk_contract_validation_rejects_invalid_inputs():
    with pytest.raises(SchemaViolation):
        TradeRiskAndQualificationContract(
            account_equity=0.0,
            capital_risk_fraction=0.01,
            min_qualification_rr=3.0,
            transaction_cost_in_r=0.05,
            impulse_expansion_min_causal_rank=0.70,
            exhaustion_max_causal_rank=0.30,
        )
    with pytest.raises(SchemaViolation):
        TradeRiskAndQualificationContract(
            account_equity=10000.0,
            capital_risk_fraction=0.0,
            min_qualification_rr=3.0,
            transaction_cost_in_r=0.05,
            impulse_expansion_min_causal_rank=0.70,
            exhaustion_max_causal_rank=0.30,
        )
    with pytest.raises(SchemaViolation):
        TradeRiskAndQualificationContract(
            account_equity=10000.0,
            capital_risk_fraction=0.01,
            min_qualification_rr=0.5,
            transaction_cost_in_r=0.05,
            impulse_expansion_min_causal_rank=0.70,
            exhaustion_max_causal_rank=0.30,
        )
    with pytest.raises(SchemaViolation):
        TradeRiskAndQualificationContract(
            account_equity=10000.0,
            capital_risk_fraction=0.01,
            min_qualification_rr=3.0,
            transaction_cost_in_r=0.05,
            impulse_expansion_min_causal_rank=0.40,
            exhaustion_max_causal_rank=0.50,
        )


def test_02_origin_vs_availability_and_as_of_visibility_firewall():
    with pytest.raises(PrematureAvailability):
        StructuralLiquidityTargetPool(
            pool_id="BAD_POOL",
            pool_kind="BSL",
            scale_label="H1",
            target_price=105000.0,
            origin_key=_pos_key(20),
            available_key=_pos_key(19),
        )

    future_pool = StructuralLiquidityTargetPool(
        pool_id="FUTURE_POOL",
        pool_kind="BSL",
        scale_label="H1",
        target_price=105000.0,
        origin_key=_pos_key(45),
        available_key=_pos_key(55),
    )
    with pytest.raises(IllegalCausalReference):
        StructuralTargetLadder.build_causal_ladder(
            direction=DIRECTION_LONG,
            entry_price=100000.0,
            structural_stop_price=99000.0,
            candidate_pools=(future_pool,),
            at_key=_pos_key(50),
        )


def test_03_qualifying_long_recommendation_1pct_sizing_and_3r_to_12r_blueprint():
    report = _make_muf_report(at_index=50)
    confluence = _make_long_confluence(at_index=50, stop_price=99000.0)
    contract = _make_risk_contract()
    pools = _make_long_pools()

    rec = evaluate_causal_ict_recommendation_as_of(
        muf_report=report,
        confluence=confluence,
        candidate_liquidity_pools=pools,
        entry_price=100000.0,
        risk_contract=contract,
    )

    assert rec.decision == DECISION_ENTER_LONG
    assert rec.direction == DIRECTION_LONG
    assert pytest.approx(rec.risk_capital_amount) == 100.0
    assert pytest.approx(rec.stop_distance) == 1000.0
    assert pytest.approx(rec.position_units) == 0.1
    assert pytest.approx(rec.qualifying_target_price) == 103000.0
    assert pytest.approx(rec.qualifying_rr_multiple) == 3.0
    assert pytest.approx(rec.runner_target_price) == 112000.0
    assert pytest.approx(rec.runner_rr_multiple) == 12.0
    assert rec.expected_value_in_r > 0.0

    bp = rec.execution_blueprint
    assert bp is not None
    assert pytest.approx(bp.live_resting_exchange_tp_price) == 112000.0
    assert pytest.approx(bp.live_t1_checkpoint_price) == 103000.0
    assert len(bp.pending_order_split_legs) == 3
    assert pytest.approx(sum(leg.position_fraction for leg in bp.pending_order_split_legs)) == 1.0
    assert pytest.approx(sum(leg.position_units for leg in bp.pending_order_split_legs)) == 0.1
    assert pytest.approx(bp.pending_order_split_legs[0].position_fraction) == 0.25


def test_04_rejects_long_in_premium_zone_or_unconfirmed_ltf_break():
    report = _make_muf_report(at_index=50)
    confluence_premium = _make_long_confluence(at_index=50, zone=RANGE_ZONE_PREMIUM)
    rec = evaluate_causal_ict_recommendation_as_of(
        muf_report=report,
        confluence=confluence_premium,
        candidate_liquidity_pools=_make_long_pools(),
        entry_price=100000.0,
        risk_contract=_make_risk_contract(),
    )
    assert rec.decision == DECISION_WAIT_NO_QUALIFYING_SETUP
    assert "HTF_ZONE_NOT_DISCOUNT_FOR_LONG" in rec.reason_codes


def test_05_proxy_and_actual_flow_kept_strictly_separate_and_block_on_absorption():
    report = _make_muf_report(at_index=50)
    conf_unavail = _make_long_confluence(
        at_index=50,
        proxy_flow=FLOW_REGIME_SUPPORTIVE_DISPLACEMENT,
        actual_flow=TypedState.UNAVAILABLE,
    )
    rec_ok = evaluate_causal_ict_recommendation_as_of(
        muf_report=report,
        confluence=conf_unavail,
        candidate_liquidity_pools=_make_long_pools(),
        entry_price=100000.0,
        risk_contract=_make_risk_contract(),
    )
    assert rec_ok.decision == DECISION_ENTER_LONG
    assert rec_ok.actual_flow_regime is TypedState.UNAVAILABLE

    conf_abs = _make_long_confluence(
        at_index=50,
        proxy_flow=FLOW_REGIME_SUPPORTIVE_DISPLACEMENT,
        actual_flow=FLOW_REGIME_ABSORPTION_AGAINST,
    )
    rec_blocked = evaluate_causal_ict_recommendation_as_of(
        muf_report=report,
        confluence=conf_abs,
        candidate_liquidity_pools=_make_long_pools(),
        entry_price=100000.0,
        risk_contract=_make_risk_contract(),
    )
    assert rec_blocked.decision == DECISION_WAIT_NO_QUALIFYING_SETUP
    assert "ACTUAL_FLOW_ABSORPTION_AGAINST_DIRECTION" in rec_blocked.reason_codes


def test_06_rejects_when_no_liquidity_target_meets_min_3r():
    report = _make_muf_report(at_index=50)
    confluence = _make_long_confluence(at_index=50, stop_price=99000.0)
    low_rr_pool = (
        StructuralLiquidityTargetPool(
            pool_id="LOW_RR_2R",
            pool_kind="BSL",
            scale_label="M15",
            target_price=102000.0,
            origin_key=_pos_key(10),
            available_key=_pos_key(15),
        ),
    )
    rec = evaluate_causal_ict_recommendation_as_of(
        muf_report=report,
        confluence=confluence,
        candidate_liquidity_pools=low_rr_pool,
        entry_price=100000.0,
        risk_contract=_make_risk_contract(),
    )
    assert rec.decision == DECISION_WAIT_NO_QUALIFYING_SETUP
    assert "NO_STRUCTURAL_LIQUIDITY_TARGET_MEETS_MIN_RR" in rec.reason_codes


def test_07_rejects_when_competing_risk_expected_value_is_negative():
    bad_report = _make_muf_report(
        at_index=50,
        cont_rate=0.10,
        visible_episodes=30,
        non_overlapping_clusters=28,
        right_censored=2,
    )
    rec = evaluate_causal_ict_recommendation_as_of(
        muf_report=bad_report,
        confluence=_make_long_confluence(at_index=50),
        candidate_liquidity_pools=(_make_long_pools()[0],),
        entry_price=100000.0,
        risk_contract=_make_risk_contract(),
    )
    assert rec.decision == DECISION_WAIT_NO_QUALIFYING_SETUP
    assert "NON_POSITIVE_COMPETING_RISK_EXPECTED_VALUE" in rec.reason_codes


def test_08_lifecycle_holds_initial_stop_while_wave_forming_without_premature_move():
    ladder = StructuralTargetLadder.build_causal_ladder(
        direction=DIRECTION_LONG,
        entry_price=100000.0,
        structural_stop_price=99000.0,
        candidate_pools=_make_long_pools(),
        at_key=_pos_key(50),
    )
    state = OpenTradeLifecycleState(
        trade_id="TRADE_001",
        direction=DIRECTION_LONG,
        entry_price=100000.0,
        initial_stop_price=99000.0,
        current_stop_price=99000.0,
        stop_distance=1000.0,
        remaining_position_fraction=1.0,
        realized_r_banked=0.0,
        active_target_index=0,
        target_ladder=ladder.targets_with_rr,
    )
    unconfirmed_bos_swing = ConfirmedStructuralTrailSwing(
        swing_id="SW_1",
        swing_price=100500.0,
        origin_key=_pos_key(52),
        available_key=_pos_key(55),
        followed_by_bos_in_direction=False,
    )
    action = evaluate_open_trade_lifecycle_as_of(
        state=state,
        at_key=_pos_key(56),
        bar_low=100800.0,
        bar_high=101500.0,
        bar_close=101200.0,
        current_wave_efficiency_rank=0.75,
        current_wave_velocity_rank=0.72,
        opposing_ltf_choch_confirmed=False,
        proxy_flow_regime=FLOW_REGIME_SUPPORTIVE_DISPLACEMENT,
        actual_flow_regime=FLOW_REGIME_SUPPORTIVE_DISPLACEMENT,
        confirmed_trail_swings=(unconfirmed_bos_swing,),
        risk_contract=_make_risk_contract(),
    )
    assert action.action == ACTION_HOLD_INITIAL_STRUCTURAL_STOP
    assert pytest.approx(action.updated_stop_price) == 99000.0


def test_09_lifecycle_ratchets_stop_only_on_confirmed_swing_with_bos():
    ladder = StructuralTargetLadder.build_causal_ladder(
        direction=DIRECTION_LONG,
        entry_price=100000.0,
        structural_stop_price=99000.0,
        candidate_pools=_make_long_pools(),
        at_key=_pos_key(50),
    )
    state = OpenTradeLifecycleState(
        trade_id="TRADE_001",
        direction=DIRECTION_LONG,
        entry_price=100000.0,
        initial_stop_price=99000.0,
        current_stop_price=99000.0,
        stop_distance=1000.0,
        remaining_position_fraction=1.0,
        realized_r_banked=0.0,
        active_target_index=0,
        target_ladder=ladder.targets_with_rr,
    )
    confirmed_swing = ConfirmedStructuralTrailSwing(
        swing_id="SW_BOS_1",
        swing_price=101000.0,
        origin_key=_pos_key(53),
        available_key=_pos_key(57),
        followed_by_bos_in_direction=True,
    )
    action = evaluate_open_trade_lifecycle_as_of(
        state=state,
        at_key=_pos_key(58),
        bar_low=101500.0,
        bar_high=102400.0,
        bar_close=102200.0,
        current_wave_efficiency_rank=0.75,
        current_wave_velocity_rank=0.75,
        opposing_ltf_choch_confirmed=False,
        proxy_flow_regime=FLOW_REGIME_SUPPORTIVE_DISPLACEMENT,
        actual_flow_regime=FLOW_REGIME_SUPPORTIVE_DISPLACEMENT,
        confirmed_trail_swings=(confirmed_swing,),
        risk_contract=_make_risk_contract(),
    )
    assert action.action == ACTION_RATCHET_STOP_TO_CONFIRMED_SWING
    assert pytest.approx(action.updated_stop_price) == 101000.0
    assert pytest.approx(action.cumulative_locked_r) == 1.0


def test_10_impulse_expansion_at_t1_unlocks_higher_targets_to_capture_12r_runner():
    ladder = StructuralTargetLadder.build_causal_ladder(
        direction=DIRECTION_LONG,
        entry_price=100000.0,
        structural_stop_price=99000.0,
        candidate_pools=_make_long_pools(),
        at_key=_pos_key(50),
    )
    state = OpenTradeLifecycleState(
        trade_id="TRADE_RUNNER_12R",
        direction=DIRECTION_LONG,
        entry_price=100000.0,
        initial_stop_price=99000.0,
        current_stop_price=99000.0,
        stop_distance=1000.0,
        remaining_position_fraction=1.0,
        realized_r_banked=0.0,
        active_target_index=0,
        target_ladder=ladder.targets_with_rr,
    )
    contract = _make_risk_contract()

    sw_t1 = ConfirmedStructuralTrailSwing(
        swing_id="SW_FLOOR_2R",
        swing_price=102000.0,
        origin_key=_pos_key(55),
        available_key=_pos_key(59),
        followed_by_bos_in_direction=True,
    )
    act_t1 = evaluate_open_trade_lifecycle_as_of(
        state=state,
        at_key=_pos_key(60),
        bar_low=102200.0,
        bar_high=103400.0,
        bar_close=103300.0,
        current_wave_efficiency_rank=0.88,
        current_wave_velocity_rank=0.85,
        opposing_ltf_choch_confirmed=False,
        proxy_flow_regime=FLOW_REGIME_SUPPORTIVE_DISPLACEMENT,
        actual_flow_regime=FLOW_REGIME_SUPPORTIVE_DISPLACEMENT,
        confirmed_trail_swings=(sw_t1,),
        risk_contract=contract,
    )
    assert act_t1.action == ACTION_UNLOCK_HIGHER_TARGET_AND_RATCHET_STOP
    assert pytest.approx(act_t1.remaining_position_fraction) == 1.0
    assert pytest.approx(act_t1.updated_stop_price) == 102000.0
    assert pytest.approx(act_t1.active_target_price) == 106000.0
    assert pytest.approx(act_t1.active_target_rr) == 6.0
    assert pytest.approx(act_t1.cumulative_locked_r) == 2.0

    sw_t2 = ConfirmedStructuralTrailSwing(
        swing_id="SW_FLOOR_5R",
        swing_price=105000.0,
        origin_key=_pos_key(64),
        available_key=_pos_key(68),
        followed_by_bos_in_direction=True,
    )
    act_t2 = evaluate_open_trade_lifecycle_as_of(
        state=act_t1.updated_state,
        at_key=_pos_key(70),
        bar_low=105200.0,
        bar_high=106500.0,
        bar_close=106400.0,
        current_wave_efficiency_rank=0.84,
        current_wave_velocity_rank=0.81,
        opposing_ltf_choch_confirmed=False,
        proxy_flow_regime=FLOW_REGIME_SUPPORTIVE_DISPLACEMENT,
        actual_flow_regime=FLOW_REGIME_SUPPORTIVE_DISPLACEMENT,
        confirmed_trail_swings=(sw_t2,),
        risk_contract=contract,
    )
    assert act_t2.action == ACTION_UNLOCK_HIGHER_TARGET_AND_RATCHET_STOP
    assert pytest.approx(act_t2.remaining_position_fraction) == 1.0
    assert pytest.approx(act_t2.updated_stop_price) == 105000.0
    assert pytest.approx(act_t2.active_target_price) == 112000.0
    assert pytest.approx(act_t2.active_target_rr) == 12.0
    assert pytest.approx(act_t2.cumulative_locked_r) == 5.0

    act_t3 = evaluate_open_trade_lifecycle_as_of(
        state=act_t2.updated_state,
        at_key=_pos_key(80),
        bar_low=109000.0,
        bar_high=112200.0,
        bar_close=112050.0,
        current_wave_efficiency_rank=0.80,
        current_wave_velocity_rank=0.78,
        opposing_ltf_choch_confirmed=False,
        proxy_flow_regime=FLOW_REGIME_SUPPORTIVE_DISPLACEMENT,
        actual_flow_regime=FLOW_REGIME_SUPPORTIVE_DISPLACEMENT,
        confirmed_trail_swings=(sw_t2,),
        risk_contract=contract,
    )
    assert act_t3.action == ACTION_EXIT_FULL_AT_FINAL_TARGET
    assert pytest.approx(act_t3.remaining_position_fraction) == 0.0
    assert pytest.approx(act_t3.realized_r_increment) == 12.0
    assert pytest.approx(act_t3.cumulative_locked_r) == 12.0


def test_11_post_t1_continuation_reentry_when_external_limit_order_closed_at_3r():
    ladder = StructuralTargetLadder.build_causal_ladder(
        direction=DIRECTION_LONG,
        entry_price=100000.0,
        structural_stop_price=99000.0,
        candidate_pools=_make_long_pools(),
        at_key=_pos_key(50),
    )
    externally_closed_state = OpenTradeLifecycleState(
        trade_id="TRADE_EXT_CLOSED_AT_3R",
        direction=DIRECTION_LONG,
        entry_price=100000.0,
        initial_stop_price=99000.0,
        current_stop_price=100000.0,
        stop_distance=1000.0,
        remaining_position_fraction=0.0,
        realized_r_banked=3.0,
        active_target_index=1,
        target_ladder=ladder.targets_with_rr,
        external_limit_closed_at_t1=True,
    )
    pullback = ContinuationPullbackSetup(
        pullback_poi_kind="CONTINUATION_BULLISH_FVG_ABOVE_T1",
        pullback_entry_price=103200.0,
        pullback_invalidation_stop_price=102400.0,
        origin_key=_pos_key(62),
        available_key=_pos_key(65),
        ltf_continuation_break_confirmed=True,
    )
    report_at_66 = _make_muf_report(at_index=66)
    action = evaluate_open_trade_lifecycle_as_of(
        state=externally_closed_state,
        at_key=_pos_key(66),
        bar_low=103100.0,
        bar_high=103800.0,
        bar_close=103600.0,
        current_wave_efficiency_rank=0.82,
        current_wave_velocity_rank=0.80,
        opposing_ltf_choch_confirmed=False,
        proxy_flow_regime=FLOW_REGIME_SUPPORTIVE_DISPLACEMENT,
        actual_flow_regime=FLOW_REGIME_SUPPORTIVE_DISPLACEMENT,
        confirmed_trail_swings=(),
        risk_contract=_make_risk_contract(),
        muf_report=report_at_66,
        continuation_pullback=pullback,
    )
    assert action.action == ACTION_EMIT_CONTINUATION_REENTRY_FOR_HIGHER_TARGETS
    reentry = action.continuation_reentry_recommendation
    assert reentry is not None
    assert reentry.decision == DECISION_CONTINUATION_REENTRY_LONG
    assert pytest.approx(reentry.entry_price) == 103200.0
    assert pytest.approx(reentry.structural_stop_price) == 102400.0
    assert pytest.approx(reentry.qualifying_target_price) == 106000.0
    assert pytest.approx(reentry.qualifying_rr_multiple) == 3.5
    assert pytest.approx(reentry.runner_target_price) == 112000.0
    assert pytest.approx(reentry.runner_rr_multiple) == 11.0


def test_12_moderate_velocity_at_t1_takes_partial_and_trails_runner():
    ladder = StructuralTargetLadder.build_causal_ladder(
        direction=DIRECTION_LONG,
        entry_price=100000.0,
        structural_stop_price=99000.0,
        candidate_pools=_make_long_pools(),
        at_key=_pos_key(50),
    )
    state = OpenTradeLifecycleState(
        trade_id="TRADE_PARTIAL",
        direction=DIRECTION_LONG,
        entry_price=100000.0,
        initial_stop_price=99000.0,
        current_stop_price=99000.0,
        stop_distance=1000.0,
        remaining_position_fraction=1.0,
        realized_r_banked=0.0,
        active_target_index=0,
        target_ladder=ladder.targets_with_rr,
    )
    action = evaluate_open_trade_lifecycle_as_of(
        state=state,
        at_key=_pos_key(60),
        bar_low=102000.0,
        bar_high=103100.0,
        bar_close=102900.0,
        current_wave_efficiency_rank=0.55,
        current_wave_velocity_rank=0.50,
        opposing_ltf_choch_confirmed=False,
        proxy_flow_regime=FLOW_REGIME_NEUTRAL,
        actual_flow_regime=FLOW_REGIME_NEUTRAL,
        confirmed_trail_swings=(),
        risk_contract=_make_risk_contract(),
    )
    assert action.action == ACTION_TAKE_PARTIAL_AND_TRAIL_RUNNER
    assert pytest.approx(action.remaining_position_fraction) == 0.75
    assert pytest.approx(action.realized_r_increment) == 0.75
    assert pytest.approx(action.updated_stop_price) == 100000.0
    assert pytest.approx(action.active_target_price) == 106000.0


def test_13_exhaustion_or_absorption_at_t1_exits_full_position():
    ladder = StructuralTargetLadder.build_causal_ladder(
        direction=DIRECTION_LONG,
        entry_price=100000.0,
        structural_stop_price=99000.0,
        candidate_pools=_make_long_pools(),
        at_key=_pos_key(50),
    )
    state = OpenTradeLifecycleState(
        trade_id="TRADE_EXHAUST",
        direction=DIRECTION_LONG,
        entry_price=100000.0,
        initial_stop_price=99000.0,
        current_stop_price=99000.0,
        stop_distance=1000.0,
        remaining_position_fraction=1.0,
        realized_r_banked=0.0,
        active_target_index=0,
        target_ladder=ladder.targets_with_rr,
    )
    action = evaluate_open_trade_lifecycle_as_of(
        state=state,
        at_key=_pos_key(60),
        bar_low=102100.0,
        bar_high=103100.0,
        bar_close=102500.0,
        current_wave_efficiency_rank=0.22,
        current_wave_velocity_rank=0.45,
        opposing_ltf_choch_confirmed=False,
        proxy_flow_regime=FLOW_REGIME_ABSORPTION_AGAINST,
        actual_flow_regime=FLOW_REGIME_NEUTRAL,
        confirmed_trail_swings=(),
        risk_contract=_make_risk_contract(),
    )
    assert action.action == ACTION_EXIT_FULL_ON_EXHAUSTION_OR_REVERSAL
    assert pytest.approx(action.remaining_position_fraction) == 0.0
    assert pytest.approx(action.realized_r_increment) == 3.0


def test_14_mid_flight_opposing_ltf_choch_exits_immediately():
    ladder = StructuralTargetLadder.build_causal_ladder(
        direction=DIRECTION_LONG,
        entry_price=100000.0,
        structural_stop_price=99000.0,
        candidate_pools=_make_long_pools(),
        at_key=_pos_key(50),
    )
    state = OpenTradeLifecycleState(
        trade_id="TRADE_MID_REV",
        direction=DIRECTION_LONG,
        entry_price=100000.0,
        initial_stop_price=99000.0,
        current_stop_price=99000.0,
        stop_distance=1000.0,
        remaining_position_fraction=1.0,
        realized_r_banked=0.0,
        active_target_index=0,
        target_ladder=ladder.targets_with_rr,
    )
    action = evaluate_open_trade_lifecycle_as_of(
        state=state,
        at_key=_pos_key(58),
        bar_low=101200.0,
        bar_high=102000.0,
        bar_close=101500.0,
        current_wave_efficiency_rank=0.40,
        current_wave_velocity_rank=0.40,
        opposing_ltf_choch_confirmed=True,
        proxy_flow_regime=FLOW_REGIME_NEUTRAL,
        actual_flow_regime=FLOW_REGIME_NEUTRAL,
        confirmed_trail_swings=(),
        risk_contract=_make_risk_contract(),
    )
    assert action.action == ACTION_EXIT_FULL_ON_EXHAUSTION_OR_REVERSAL
    assert pytest.approx(action.remaining_position_fraction) == 0.0
    assert pytest.approx(action.realized_r_increment) == 1.5


def test_15_stop_loss_hit_exits_with_exact_locked_r():
    ladder = StructuralTargetLadder.build_causal_ladder(
        direction=DIRECTION_LONG,
        entry_price=100000.0,
        structural_stop_price=99000.0,
        candidate_pools=_make_long_pools(),
        at_key=_pos_key(50),
    )
    state = OpenTradeLifecycleState(
        trade_id="TRADE_STOP",
        direction=DIRECTION_LONG,
        entry_price=100000.0,
        initial_stop_price=99000.0,
        current_stop_price=99000.0,
        stop_distance=1000.0,
        remaining_position_fraction=1.0,
        realized_r_banked=0.0,
        active_target_index=0,
        target_ladder=ladder.targets_with_rr,
    )
    action = evaluate_open_trade_lifecycle_as_of(
        state=state,
        at_key=_pos_key(54),
        bar_low=98950.0,
        bar_high=99800.0,
        bar_close=99050.0,
        current_wave_efficiency_rank=0.50,
        current_wave_velocity_rank=0.50,
        opposing_ltf_choch_confirmed=False,
        proxy_flow_regime=FLOW_REGIME_NEUTRAL,
        actual_flow_regime=FLOW_REGIME_NEUTRAL,
        confirmed_trail_swings=(),
        risk_contract=_make_risk_contract(),
    )
    assert action.action == ACTION_EXIT_STOP_LOSS_HIT
    assert pytest.approx(action.remaining_position_fraction) == 0.0
    assert pytest.approx(action.realized_r_increment) == -1.0
    assert pytest.approx(action.cumulative_locked_r) == -1.0


def test_16_short_direction_recommendation_and_impulse_unlock_symmetry():
    report = _make_muf_report(at_index=50)
    short_conf = CausalICTConfluenceObservation(
        at_key=_pos_key(50),
        htf_parent_direction=DIRECTION_SHORT,
        htf_dealing_range_zone=RANGE_ZONE_PREMIUM,
        htf_poi_mitigated=True,
        htf_poi_kind="HTF_BEARISH_OB",
        htf_poi_origin_key=_pos_key(20),
        htf_poi_available_key=_pos_key(25),
        ltf_break_confirmed=True,
        ltf_break_kind="BEARISH_CHOCH",
        ltf_break_direction=DIRECTION_SHORT,
        ltf_break_origin_key=_pos_key(40),
        ltf_break_available_key=_pos_key(45),
        ltf_invalidation_swing_price=101000.0,
        ltf_invalidation_origin_key=_pos_key(38),
        ltf_invalidation_available_key=_pos_key(43),
        child_wave_efficiency_rank=0.85,
        child_wave_velocity_rank=0.82,
        proxy_flow_regime=FLOW_REGIME_SUPPORTIVE_DISPLACEMENT,
        actual_flow_regime=FLOW_REGIME_SUPPORTIVE_DISPLACEMENT,
    )
    short_pools = (
        StructuralLiquidityTargetPool(
            pool_id="SSL_T1_3R",
            pool_kind="SSL",
            scale_label="M15",
            target_price=97000.0,
            origin_key=_pos_key(10),
            available_key=_pos_key(15),
        ),
        StructuralLiquidityTargetPool(
            pool_id="SSL_T2_10R",
            pool_kind="HTF_SSL",
            scale_label="H4",
            target_price=90000.0,
            origin_key=_pos_key(2),
            available_key=_pos_key(8),
        ),
    )
    rec = evaluate_causal_ict_recommendation_as_of(
        muf_report=report,
        confluence=short_conf,
        candidate_liquidity_pools=short_pools,
        entry_price=100000.0,
        risk_contract=_make_risk_contract(),
    )
    assert rec.decision == DECISION_ENTER_SHORT
    assert pytest.approx(rec.qualifying_rr_multiple) == 3.0
    assert pytest.approx(rec.runner_rr_multiple) == 10.0


def test_17_sub_millisecond_realtime_execution_benchmark():
    report = _make_muf_report(at_index=50)
    confluence = _make_long_confluence(at_index=50)
    pools = _make_long_pools()
    contract = _make_risk_contract()

    t0 = time.perf_counter()
    for _ in range(200):
        evaluate_causal_ict_recommendation_as_of(
            muf_report=report,
            confluence=confluence,
            candidate_liquidity_pools=pools,
            entry_price=100000.0,
            risk_contract=contract,
        )
    elapsed_ms_per_call = ((time.perf_counter() - t0) * 1000.0) / 200.0
    assert elapsed_ms_per_call < 1.0


def test_18_mismatched_at_key_between_muf_report_and_confluence_rejected():
    report = _make_muf_report(at_index=50)
    confluence = _make_long_confluence(at_index=51)
    with pytest.raises(IllegalCausalReference):
        evaluate_causal_ict_recommendation_as_of(
            muf_report=report,
            confluence=confluence,
            candidate_liquidity_pools=_make_long_pools(),
            entry_price=100000.0,
            risk_contract=_make_risk_contract(),
        )


def test_19_future_trail_swing_availability_rejected_in_lifecycle():
    ladder = StructuralTargetLadder.build_causal_ladder(
        direction=DIRECTION_LONG,
        entry_price=100000.0,
        structural_stop_price=99000.0,
        candidate_pools=_make_long_pools(),
        at_key=_pos_key(50),
    )
    state = OpenTradeLifecycleState(
        trade_id="TRADE_FUTURE_SW",
        direction=DIRECTION_LONG,
        entry_price=100000.0,
        initial_stop_price=99000.0,
        current_stop_price=99000.0,
        stop_distance=1000.0,
        remaining_position_fraction=1.0,
        realized_r_banked=0.0,
        active_target_index=0,
        target_ladder=ladder.targets_with_rr,
    )
    future_swing = ConfirmedStructuralTrailSwing(
        swing_id="SW_FUTURE",
        swing_price=101000.0,
        origin_key=_pos_key(55),
        available_key=_pos_key(62),
        followed_by_bos_in_direction=True,
    )
    with pytest.raises(IllegalCausalReference):
        evaluate_open_trade_lifecycle_as_of(
            state=state,
            at_key=_pos_key(60),
            bar_low=101200.0,
            bar_high=102000.0,
            bar_close=101800.0,
            current_wave_efficiency_rank=0.80,
            current_wave_velocity_rank=0.80,
            opposing_ltf_choch_confirmed=False,
            proxy_flow_regime=FLOW_REGIME_SUPPORTIVE_DISPLACEMENT,
            actual_flow_regime=FLOW_REGIME_SUPPORTIVE_DISPLACEMENT,
            confirmed_trail_swings=(future_swing,),
            risk_contract=_make_risk_contract(),
        )


def test_20_invalid_stop_geometry_returns_wait_with_explicit_reason():
    report = _make_muf_report(at_index=50)
    bad_stop_conf = _make_long_confluence(at_index=50, stop_price=101000.0)
    rec = evaluate_causal_ict_recommendation_as_of(
        muf_report=report,
        confluence=bad_stop_conf,
        candidate_liquidity_pools=_make_long_pools(),
        entry_price=100000.0,
        risk_contract=_make_risk_contract(),
    )
    assert rec.decision == DECISION_WAIT_NO_QUALIFYING_SETUP
    assert "INVALID_STRUCTURAL_STOP_GEOMETRY" in rec.reason_codes
