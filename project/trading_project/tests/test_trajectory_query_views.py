from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import inspect

import pandas as pd
import pytest

from trading_system.research.information_time import (
    INFORMATION_KEY_VERSION,
    InformationKey,
    InformationPhase,
    PositionalTimelineAdapter,
    TimeIndexedTimelineAdapter,
)
from trading_system.research.trajectory.trajectory_case_adapter import (
    TrajectoryCaseError,
    create_trajectory_decision_case,
)
from trading_system.research.trajectory.trajectory_contract import MarketObservationTimeline
from trading_system.research.trajectory.trajectory_query_views import (
    AsOfSurfaceView,
    AvailabilityStatus,
    CandidatePricePair,
    CoverageAssessment,
    CoverageContract,
    CensoringState,
    DecisionCloseObservation,
    DerivedViewStatus,
    HorizonPolicyIdentity,
    HorizonRequest,
    InteractionStatus,
    ObservedTargetReference,
    PairOrderStatus,
    ProjectedInvalidationReference,
    ProjectedTargetReference,
    SamplingMembershipState,
    SamplingPolicyIdentity,
    TrajectoryQueryError,
    TrajectoryWindow,
    bind_sampling_membership,
    build_trajectory_window,
    create_asof_surface_view,
    create_trajectory_query_reference,
    decision_surface_view,
    derive_excursion_view,
    derive_observed_target_interaction,
    derive_projected_invalidation_interaction,
    derive_projected_target_interaction,
    derive_target_invalidation_view,
    derive_timing_view,
    verify_trajectory_window_source,
)
from trading_system.research.trajectory import trajectory_stage4a as s4a
from trading_system.research.trajectory import trajectory_stage4b1 as s4b1
from trading_system.research.trajectory import trajectory_stage4b2 as s4b2
from trading_system.research.trajectory import trajectory_stage4c as s4c


def _market(n: int, *, index: pd.Index | None = None, highs=None, lows=None, closes=None) -> pd.DataFrame:
    close = [100.0] * n if closes is None else [float(value) for value in closes]
    high = [101.0] * n if highs is None else [float(value) for value in highs]
    low = [99.0] * n if lows is None else [float(value) for value in lows]
    frame = pd.DataFrame(
        {
            "open": close,
            "high": high,
            "low": low,
            "close": close,
            "volume": [10.0] * n,
        },
        index=pd.RangeIndex(n) if index is None else index,
    )
    return frame


def _case(market: pd.DataFrame, *, timeline_id: str, decision_position: int = 1, time_indexed: bool = False):
    adapter = (
        TimeIndexedTimelineAdapter(timeline_id)
        if time_indexed
        else PositionalTimelineAdapter(timeline_id)
    )
    timeline = MarketObservationTimeline.seal(adapter=adapter, market_history=market)
    decision = adapter.key_for_position(
        market.index,
        decision_position,
        InformationPhase.COMPLETED_ROW_AVAILABLE,
    )
    case = create_trajectory_decision_case(
        timeline=timeline,
        adapter=adapter,
        market_history=market,
        decision_key=decision,
        surfaces=(),
        parent_snapshot=None,
    )
    return case, timeline, adapter, decision


def _future_key(adapter, market, position: int, *, time_after_data: pd.Timestamp | None = None):
    if position < len(market):
        return adapter.key_for_position(
            market.index,
            position,
            InformationPhase.COMPLETED_ROW_AVAILABLE,
        )
    timestamp = time_after_data
    if isinstance(adapter, TimeIndexedTimelineAdapter) and timestamp is None:
        timestamp = pd.Timestamp(market.index[-1]) + pd.Timedelta(minutes=2)
    return InformationKey(
        information_key_version=INFORMATION_KEY_VERSION,
        timeline_id=adapter.timeline_id,
        bar_position=position,
        event_time_utc=timestamp,
        information_phase=InformationPhase.COMPLETED_ROW_AVAILABLE,
        deterministic_sequence=0,
    )


def _horizon(end_key: InformationKey, policy_id: str = "horizon-A"):
    return HorizonRequest(
        policy_identity=HorizonPolicyIdentity(
            policy_id=policy_id,
            policy_version="1",
            policy_sha256=("a" if policy_id.endswith("A") else "f") * 64,
        ),
        requested_end_key=end_key,
    )


def _coverage(expected_step: pd.Timedelta | None):
    return CoverageContract(
        contract_id="declared-grid",
        contract_version="1",
        contract_sha256="c" * 64,
        expected_step=expected_step,
    )


def _pair(case, *, target_price=105.0, invalidation_price=95.0, pair_id="pair-1"):
    target = ProjectedTargetReference(
        candidate_id="candidate-1",
        projection_id=f"{pair_id}-target",
        projection_sha256="d" * 64,
        projected_price=target_price,
        available_at=case.decision_key,
    )
    invalidation = ProjectedInvalidationReference(
        candidate_id="candidate-1",
        projection_id=f"{pair_id}-invalidation",
        projection_sha256="e" * 64,
        projected_price=invalidation_price,
        available_at=case.decision_key,
    )
    return CandidatePricePair(pair_id, target, invalidation)


def test_asof_views_are_fresh_immutable_and_do_not_include_rows_after_key():
    market = _market(9)
    adapter = PositionalTimelineAdapter("asof-view")
    timeline = MarketObservationTimeline.seal(adapter=adapter, market_history=market)
    decision = adapter.key_for_position(market.index, 3, InformationPhase.COMPLETED_ROW_AVAILABLE)
    surface = s4a.build_volatility_surface(timeline=timeline, adapter=adapter, market_history=market)
    case = create_trajectory_decision_case(
        timeline=timeline,
        adapter=adapter,
        market_history=market,
        decision_key=decision,
        surfaces=(surface,),
        parent_snapshot=None,
    )

    at_decision = decision_surface_view(case=case, surfaces=(surface,))
    later_key = adapter.key_for_position(market.index, 6, InformationPhase.COMPLETED_ROW_AVAILABLE)
    later_view = create_asof_surface_view(case=case, surfaces=(surface,), as_of_key=later_key)

    assert isinstance(at_decision, AsOfSurfaceView)
    assert at_decision is not later_view
    assert at_decision.as_of_key == decision
    assert later_view.as_of_key == later_key
    assert len(at_decision.surfaces[0].tables[0].rows) == 4
    assert len(later_view.surfaces[0].tables[0].rows) == 7
    assert at_decision.surfaces[0].tables[0].content_hash != later_view.surfaces[0].tables[0].content_hash
    availability = {entry.domain: entry.status for entry in at_decision.availability}
    assert availability["VOLATILITY"] is AvailabilityStatus.AVAILABLE
    assert availability["SESSION"] is AvailabilityStatus.NOT_SUPPLIED

    with pytest.raises(FrozenInstanceError):
        at_decision.surfaces[0].tables[0].rows[0][0].value = "mutated"
    with pytest.raises(TypeError):
        at_decision.surfaces[0].tables[0].rows[0][0] = "mutated"


def test_asof_query_requires_all_frozen_bindings_and_legal_availability_key():
    market = _market(8)
    adapter = PositionalTimelineAdapter("asof-strict")
    timeline = MarketObservationTimeline.seal(adapter=adapter, market_history=market)
    decision = adapter.key_for_position(market.index, 3, InformationPhase.COMPLETED_ROW_AVAILABLE)
    surface = s4a.build_volatility_surface(timeline=timeline, adapter=adapter, market_history=market)
    case = create_trajectory_decision_case(
        timeline=timeline,
        adapter=adapter,
        market_history=market,
        decision_key=decision,
        surfaces=(surface,),
        parent_snapshot=None,
    )
    with pytest.raises(TrajectoryQueryError, match="unavailable"):
        create_asof_surface_view(case=case, surfaces=(), as_of_key=decision)
    preclose = adapter.key_for_position(market.index, 4, InformationPhase.BAR_PRE_CLOSE)
    with pytest.raises(TrajectoryQueryError, match="completed-row"):
        create_asof_surface_view(case=case, surfaces=(surface,), as_of_key=preclose)
    before_decision = adapter.key_for_position(market.index, 2, InformationPhase.COMPLETED_ROW_AVAILABLE)
    with pytest.raises(TrajectoryQueryError, match="cannot be projected backward"):
        create_asof_surface_view(case=case, surfaces=(surface,), as_of_key=before_decision)

    damaged = s4a.build_volatility_surface(timeline=timeline, adapter=adapter, market_history=market)
    first_output = damaged.output_columns[0]
    damaged.surface.loc[market.index[0], first_output] = float(damaged.surface.loc[market.index[0], first_output]) + 3.0
    with pytest.raises(Exception, match="self-integrity|hash|identity"):
        create_asof_surface_view(case=case, surfaces=(damaged,), as_of_key=decision)


def test_stage4b1_b2_and_c_prefixes_reuse_public_projectors_across_future_append():
    n_short, n_long, decision_position = 24, 31, 10
    close_short = [100.0 + i * 0.2 + (1.0 if i % 4 < 2 else -1.0) for i in range(n_short)]
    close_long = [100.0 + i * 0.2 + (1.0 if i % 4 < 2 else -1.0) for i in range(n_long)]

    def positional_market(close_values):
        return pd.DataFrame(
            {
                "open": close_values,
                "high": [value + 1.0 for value in close_values],
                "low": [value - 1.0 for value in close_values],
                "close": close_values,
            },
            index=pd.RangeIndex(len(close_values)),
        )

    short_market = positional_market(close_short)
    long_market = positional_market(close_long)
    positional = PositionalTimelineAdapter("stage4b-asof")
    short_timeline = MarketObservationTimeline.seal(adapter=positional, market_history=short_market)
    long_timeline = MarketObservationTimeline.seal(adapter=positional, market_history=long_market)
    decision = positional.key_for_position(
        short_market.index, decision_position, InformationPhase.COMPLETED_ROW_AVAILABLE
    )
    short_structure = s4b1.build_structure_surface(
        timeline=short_timeline, adapter=positional, market_history=short_market
    )
    long_structure = s4b1.build_structure_surface(
        timeline=long_timeline, adapter=positional, market_history=long_market
    )
    assert short_structure.surface_id != long_structure.surface_id
    structure_case = create_trajectory_decision_case(
        timeline=short_timeline,
        adapter=positional,
        market_history=short_market,
        decision_key=decision,
        surfaces=(short_structure,),
        parent_snapshot=None,
    )
    structure_view = decision_surface_view(case=structure_case, surfaces=(long_structure,))
    assert len(structure_view.surfaces[0].tables[0].rows) == decision_position + 1

    short_liquidity = s4b2.build_liquidity_surface(
        timeline=short_timeline,
        adapter=positional,
        market_history=short_market,
        structure_surface=short_structure,
    )
    long_liquidity = s4b2.build_liquidity_surface(
        timeline=long_timeline,
        adapter=positional,
        market_history=long_market,
        structure_surface=long_structure,
    )
    liquidity_case = create_trajectory_decision_case(
        timeline=short_timeline,
        adapter=positional,
        market_history=short_market,
        decision_key=decision,
        surfaces=(short_liquidity,),
        parent_snapshot=None,
    )
    short_liquidity_view = decision_surface_view(
        case=liquidity_case, surfaces=(short_liquidity,)
    )
    long_liquidity_view = decision_surface_view(
        case=liquidity_case, surfaces=(long_liquidity,)
    )
    assert short_liquidity_view.view_hash == long_liquidity_view.view_hash
    assert tuple(len(table.rows) for table in long_liquidity_view.surfaces[0].tables)[0] == decision_position + 1

    def time_market(n):
        index = pd.date_range("2024-01-01 08:01", periods=n, freq="min", tz="UTC")
        close = [100.0 + i * 0.2 for i in range(n)]
        return pd.DataFrame(
            {
                "open": close,
                "high": [value + 1.0 for value in close],
                "low": [value - 1.0 for value in close],
                "close": close,
            },
            index=index,
        )

    short_time_market = time_market(16)
    long_time_market = time_market(22)
    temporal = TimeIndexedTimelineAdapter("stage4c-asof")
    short_time_timeline = MarketObservationTimeline.seal(
        adapter=temporal, market_history=short_time_market
    )
    long_time_timeline = MarketObservationTimeline.seal(
        adapter=temporal, market_history=long_time_market
    )
    time_decision = temporal.key_for_position(
        short_time_market.index, 10, InformationPhase.COMPLETED_ROW_AVAILABLE
    )
    scale_spec = s4c.HtfScaleSpec("m5", pd.Timedelta(minutes=5))
    short_scale = s4c.build_htf_scale_surface(
        timeline=short_time_timeline,
        adapter=temporal,
        market_history=short_time_market,
        scale_spec=scale_spec,
    )
    long_scale = s4c.build_htf_scale_surface(
        timeline=long_time_timeline,
        adapter=temporal,
        market_history=long_time_market,
        scale_spec=scale_spec,
    )
    scale_case = create_trajectory_decision_case(
        timeline=short_time_timeline,
        adapter=temporal,
        market_history=short_time_market,
        decision_key=time_decision,
        surfaces=(short_scale,),
        parent_snapshot=None,
    )
    short_scale_view = decision_surface_view(case=scale_case, surfaces=(short_scale,))
    long_scale_view = decision_surface_view(case=scale_case, surfaces=(long_scale,))
    assert short_scale_view.view_hash == long_scale_view.view_hash
    assert len(long_scale_view.surfaces[0].tables[0].rows) == time_decision.bar_position + 1


def test_empty_surface_availability_is_explicit_not_silently_filled():
    market = _market(5)
    case, _, _, decision = _case(market, timeline_id="no-surfaces")
    view = decision_surface_view(case=case, surfaces=())
    assert view.surfaces == ()
    assert all(item.status is AvailabilityStatus.NOT_SUPPLIED for item in view.availability)
    later = PositionalTimelineAdapter("no-surfaces").key_for_position(
        market.index, 2, InformationPhase.COMPLETED_ROW_AVAILABLE
    )
    with pytest.raises(TrajectoryQueryError, match="without a bound surface"):
        create_asof_surface_view(case=case, surfaces=(), as_of_key=later)
    assert decision == case.decision_key


def test_trajectory_window_uses_open_decision_exclusive_interval_and_is_verifiable():
    market = _market(6)
    case, timeline, adapter, decision = _case(market, timeline_id="window-basic")
    end = adapter.key_for_position(market.index, 4, InformationPhase.COMPLETED_ROW_AVAILABLE)
    request = _horizon(end)
    window = build_trajectory_window(
        case=case,
        timeline=timeline,
        adapter=adapter,
        market_history=market,
        horizon_request=request,
        coverage_contract=_coverage(None),
    )
    assert tuple(bar.position for bar in window.bars) == (2, 3, 4)
    assert window.reference.decision_key == decision
    assert window.reference.actual_end_key.bar_position == 4
    assert window.reference.censoring_state is CensoringState.OBSERVED_TO_REQUESTED_END
    assert window.reference.coverage_assessment is CoverageAssessment.UNASSESSED
    assert window.reference.source_artifact_reference is None
    verify_trajectory_window_source(
        window=window,
        case=case,
        timeline=timeline,
        adapter=adapter,
        market_history=market,
    )
    with pytest.raises(FrozenInstanceError):
        window.bars[0].high = 500.0
    forged_close = replace(
        window.decision_close_observation,
        value=window.decision_close_observation.value + 1.0,
    )
    with pytest.raises(TrajectoryQueryError, match="differs from path identity"):
        replace(window, decision_close_observation=forged_close)


def test_right_censoring_preserves_requested_and_actual_ends_and_never_calls_no_hit_false():
    market = _market(4)
    case, timeline, adapter, _ = _case(market, timeline_id="right-censored")
    requested_end = _future_key(adapter, market, 7)
    request = _horizon(requested_end)
    window = build_trajectory_window(
        case=case,
        timeline=timeline,
        adapter=adapter,
        market_history=market,
        horizon_request=request,
        coverage_contract=_coverage(None),
    )
    assert window.reference.censoring_state is CensoringState.RIGHT_CENSORED
    assert window.reference.horizon_request.requested_end_key.bar_position == 7
    assert window.reference.actual_end_key.bar_position == 3
    assert tuple(bar.position for bar in window.bars) == (2, 3)

    projected = _pair(case, target_price=250.0, invalidation_price=300.0)
    target_view = derive_projected_target_interaction(
        window=window,
        projected_target=projected.projected_target,
    )
    pair_view = derive_target_invalidation_view(window=window, candidate_pair=projected)
    assert target_view.status is InteractionStatus.NOT_OBSERVED_RIGHT_CENSORED
    assert pair_view.ordering is PairOrderStatus.NO_OBSERVED_TOUCH_RIGHT_CENSORED


def test_right_censoring_at_decision_row_preserves_an_empty_path():
    market = _market(3)
    case, timeline, adapter, _ = _case(
        market,
        timeline_id="censor-at-decision",
        decision_position=2,
    )
    request = _horizon(_future_key(adapter, market, 5))
    window = build_trajectory_window(
        case=case,
        timeline=timeline,
        adapter=adapter,
        market_history=market,
        horizon_request=request,
        coverage_contract=_coverage(None),
    )
    assert window.bars == ()
    assert window.reference.actual_end_key is None
    assert window.reference.observed_row_count == 0
    assert window.reference.censoring_state is CensoringState.RIGHT_CENSORED
    pair = _pair(case, target_price=250.0, invalidation_price=300.0)
    assert derive_target_invalidation_view(window=window, candidate_pair=pair).ordering is PairOrderStatus.NO_OBSERVED_TOUCH_RIGHT_CENSORED
    assert derive_excursion_view(window=window).status is DerivedViewStatus.NO_POST_DECISION_ROWS
    assert derive_timing_view(window=window, target_reference=pair.projected_target).interaction_status is InteractionStatus.RIGHT_CENSORED_NO_POST_DECISION_ROWS
    verify_trajectory_window_source(
        window=window,
        case=case,
        timeline=timeline,
        adapter=adapter,
        market_history=market,
    )


def test_same_ohlc_bar_touching_both_levels_is_explicitly_order_unknown():
    market = _market(5, highs=[101, 101, 110, 101, 101], lows=[99, 99, 90, 99, 99])
    case, timeline, adapter, _ = _case(market, timeline_id="same-bar")
    end = adapter.key_for_position(market.index, 4, InformationPhase.COMPLETED_ROW_AVAILABLE)
    window = build_trajectory_window(
        case=case,
        timeline=timeline,
        adapter=adapter,
        market_history=market,
        horizon_request=_horizon(end),
        coverage_contract=_coverage(None),
    )
    assert window.reference.censoring_state is CensoringState.RIGHT_CENSORED
    result = derive_target_invalidation_view(window=window, candidate_pair=_pair(case))
    assert result.target_touch_positions[0] == 2
    assert result.invalidation_touch_positions[0] == 2
    assert result.ordering is PairOrderStatus.BOTH_SAME_BAR_ORDER_UNKNOWN


def test_separate_bar_order_requires_declared_contiguous_time_coverage():
    index = pd.date_range("2024-01-01 00:00", periods=5, freq="min", tz="UTC")
    market = _market(5, index=index, highs=[101, 101, 110, 101, 101], lows=[99, 99, 99, 90, 99])
    case, timeline, adapter, _ = _case(
        market, timeline_id="time-ordered", time_indexed=True
    )
    end = adapter.key_for_position(market.index, 4, InformationPhase.COMPLETED_ROW_AVAILABLE)
    window = build_trajectory_window(
        case=case,
        timeline=timeline,
        adapter=adapter,
        market_history=market,
        horizon_request=_horizon(end),
        coverage_contract=_coverage(pd.Timedelta(minutes=1)),
    )
    assert window.reference.coverage_assessment is CoverageAssessment.CONTIGUOUS
    result = derive_target_invalidation_view(window=window, candidate_pair=_pair(case))
    assert result.ordering is PairOrderStatus.TARGET_OBSERVED_FIRST


def test_internal_time_gap_is_retained_as_coverage_condition_and_blocks_order_claim():
    index = pd.DatetimeIndex(
        [
            pd.Timestamp("2024-01-01 00:00", tz="UTC"),
            pd.Timestamp("2024-01-01 00:01", tz="UTC"),
            pd.Timestamp("2024-01-01 00:03", tz="UTC"),
            pd.Timestamp("2024-01-01 00:04", tz="UTC"),
        ]
    )
    market = _market(4, index=index, highs=[101, 101, 110, 101], lows=[99, 99, 99, 90])
    case, timeline, adapter, _ = _case(market, timeline_id="gap-coverage", time_indexed=True)
    end = adapter.key_for_position(market.index, 3, InformationPhase.COMPLETED_ROW_AVAILABLE)
    window = build_trajectory_window(
        case=case,
        timeline=timeline,
        adapter=adapter,
        market_history=market,
        horizon_request=_horizon(end),
        coverage_contract=_coverage(pd.Timedelta(minutes=1)),
    )
    assert window.reference.coverage_assessment is CoverageAssessment.GAPS_OR_CADENCE_DEVIATION
    assert len(window.reference.coverage_issues) == 1
    assert window.reference.coverage_issues[0].left_position == 1
    assert window.reference.coverage_issues[0].right_position == 2
    result = derive_target_invalidation_view(window=window, candidate_pair=_pair(case))
    assert result.ordering is PairOrderStatus.ORDER_UNDETERMINED_COVERAGE


def test_observed_target_and_projected_target_are_distinct_types_and_hash_domains():
    market = _market(5, highs=[101, 101, 110, 101, 101], lows=[99, 99, 99, 99, 99])
    case, timeline, adapter, _ = _case(market, timeline_id="target-types")
    end = adapter.key_for_position(market.index, 4, InformationPhase.COMPLETED_ROW_AVAILABLE)
    window = build_trajectory_window(
        case=case,
        timeline=timeline,
        adapter=adapter,
        market_history=market,
        horizon_request=_horizon(end),
        coverage_contract=_coverage(None),
    )
    projected = _pair(case, target_price=105.0).projected_target
    observed = ObservedTargetReference(
        observation_id="observed-level-1",
        source_domain="MARKET_TIMELINE",
        source_binding_sha256=case.decision_prefix_hash,
        observed_price=105.0,
        observed_at=case.decision_key,
    )
    unbound_observed = ObservedTargetReference(
        observation_id="unbound-level-1",
        source_domain="UNBOUND_FIXTURE",
        source_binding_sha256="b" * 64,
        observed_price=105.0,
        observed_at=case.decision_key,
    )
    with pytest.raises(TrajectoryQueryError, match="not bound to the decision case"):
        derive_observed_target_interaction(window=window, observed_target=unbound_observed)
    projected_view = derive_projected_target_interaction(window=window, projected_target=projected)
    observed_view = derive_observed_target_interaction(window=window, observed_target=observed)
    assert projected.identity_hash != observed.identity_hash
    assert projected_view.view_hash != observed_view.view_hash
    assert projected_view.touch_positions == observed_view.touch_positions == (2,)
    with pytest.raises(TypeError, match="different type"):
        derive_observed_target_interaction(window=window, observed_target=projected)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="different type"):
        derive_projected_target_interaction(window=window, projected_target=observed)  # type: ignore[arg-type]
    assert derive_timing_view(window=window, target_reference=projected).observed_bar_offset == 1
    invalidation = _pair(case, invalidation_price=99.0).projected_invalidation
    assert derive_timing_view(window=window, target_reference=invalidation).observed_bar_offset == 1
    excursion = derive_excursion_view(window=window)
    assert excursion.observed_max_high == 110.0
    assert excursion.observed_min_low == 99.0
    assert excursion.observed_high_delta_from_decision_close == 10.0
    assert excursion.observed_low_delta_from_decision_close == -1.0


def test_no_touch_states_distinguish_complete_window_from_coverage_unknown():
    index = pd.date_range("2024-01-01 00:00", periods=6, freq="min", tz="UTC")
    market = _market(6, index=index)
    case, timeline, adapter, _ = _case(market, timeline_id="no-hit", time_indexed=True)
    end = adapter.key_for_position(market.index, 4, InformationPhase.COMPLETED_ROW_AVAILABLE)
    pair = _pair(case, target_price=250.0, invalidation_price=300.0)

    complete = build_trajectory_window(
        case=case,
        timeline=timeline,
        adapter=adapter,
        market_history=market,
        horizon_request=_horizon(end),
        coverage_contract=_coverage(pd.Timedelta(minutes=1)),
    )
    unknown = build_trajectory_window(
        case=case,
        timeline=timeline,
        adapter=adapter,
        market_history=market,
        horizon_request=_horizon(end),
        coverage_contract=_coverage(None),
    )
    assert derive_target_invalidation_view(window=complete, candidate_pair=pair).ordering is PairOrderStatus.NO_OBSERVED_TOUCH_COMPLETE_WINDOW
    assert derive_target_invalidation_view(window=unknown, candidate_pair=pair).ordering is PairOrderStatus.NO_OBSERVED_TOUCH_COVERAGE_UNASSESSED


def test_future_row_tamper_is_detected_but_never_changes_frozen_case_identity():
    market = _market(6)
    case, timeline, adapter, _ = _case(market, timeline_id="future-tamper")
    end = adapter.key_for_position(market.index, 5, InformationPhase.COMPLETED_ROW_AVAILABLE)
    request = _horizon(end)
    original_window = build_trajectory_window(
        case=case,
        timeline=timeline,
        adapter=adapter,
        market_history=market,
        horizon_request=request,
        coverage_contract=_coverage(None),
    )
    verify_trajectory_window_source(
        window=original_window,
        case=case,
        timeline=timeline,
        adapter=adapter,
        market_history=market,
    )

    tampered = market.copy(deep=True)
    tampered.loc[3, "high"] = 130.0
    changed_timeline = MarketObservationTimeline.seal(adapter=adapter, market_history=tampered)
    changed_window = build_trajectory_window(
        case=case,
        timeline=changed_timeline,
        adapter=adapter,
        market_history=tampered,
        horizon_request=request,
        coverage_contract=_coverage(None),
    )
    assert case.case_id == original_window.reference.case_id == changed_window.reference.case_id
    assert case.case_hash
    assert original_window.reference.path_id != changed_window.reference.path_id
    with pytest.raises(TrajectoryQueryError, match="source timeline hash mismatch"):
        verify_trajectory_window_source(
            window=original_window,
            case=case,
            timeline=changed_timeline,
            adapter=adapter,
            market_history=tampered,
        )


def test_horizon_sampling_candidate_and_query_identities_are_separate_from_case():
    market = _market(7)
    case, _, adapter, _ = _case(market, timeline_id="identity-separation")
    end = adapter.key_for_position(market.index, 5, InformationPhase.COMPLETED_ROW_AVAILABLE)
    horizon_a = _horizon(end, "horizon-A")
    horizon_b = _horizon(end, "horizon-B")
    sampling_policy = SamplingPolicyIdentity("sample-X", "v1", "9" * 64)
    earlier_key = adapter.key_for_position(market.index, 0, InformationPhase.COMPLETED_ROW_AVAILABLE)
    included = bind_sampling_membership(
        case=case,
        policy_identity=sampling_policy,
        membership_id="membership-included",
        membership_key=earlier_key,
        state=SamplingMembershipState.INCLUDED,
    )
    excluded = bind_sampling_membership(
        case=case,
        policy_identity=sampling_policy,
        membership_id="membership-excluded",
        membership_key=earlier_key,
        state=SamplingMembershipState.EXCLUDED,
    )
    pair_a = _pair(case, pair_id="pair-a")
    pair_b = _pair(case, pair_id="pair-b", target_price=106.0)
    query_a = create_trajectory_query_reference(
        case=case,
        horizon_request=horizon_a,
        candidate_pair=pair_a,
        sampling_membership=included,
    )
    query_b = create_trajectory_query_reference(
        case=case,
        horizon_request=horizon_b,
        candidate_pair=pair_b,
        sampling_membership=excluded,
    )
    assert query_a.query_id != query_b.query_id
    assert query_a.case_id == query_b.case_id == case.case_id
    assert pair_a.identity_hash != pair_b.identity_hash
    assert horizon_a.identity_hash != horizon_b.identity_hash
    assert included.identity_hash != excluded.identity_hash

    signature = inspect.signature(bind_sampling_membership)
    assert not {"window", "trajectory", "market_history", "future_rows"}.intersection(signature.parameters)
    with pytest.raises(TrajectoryQueryError, match="HorizonPolicyIdentity"):
        HorizonRequest(policy_identity=sampling_policy, requested_end_key=end)  # type: ignore[arg-type]


def test_time_indexed_future_end_requires_explicit_future_timestamp_and_right_censors():
    index = pd.date_range("2024-01-01 00:00", periods=3, freq="min", tz="UTC")
    market = _market(3, index=index)
    case, timeline, adapter, _ = _case(market, timeline_id="time-censor", time_indexed=True)
    future_timestamp = index[-1] + pd.Timedelta(minutes=2)
    request = _horizon(_future_key(adapter, market, 5, time_after_data=future_timestamp))
    window = build_trajectory_window(
        case=case,
        timeline=timeline,
        adapter=adapter,
        market_history=market,
        horizon_request=request,
        coverage_contract=_coverage(pd.Timedelta(minutes=1)),
    )
    assert window.reference.censoring_state is CensoringState.RIGHT_CENSORED
    assert window.reference.actual_end_key.bar_position == 2
    assert window.reference.requested_end_key.event_time_utc == future_timestamp

    bad = _horizon(_future_key(adapter, market, 5, time_after_data=index[-1]))
    with pytest.raises(TrajectoryQueryError, match="must follow the last observation"):
        build_trajectory_window(
            case=case,
            timeline=timeline,
            adapter=adapter,
            market_history=market,
            horizon_request=bad,
            coverage_contract=_coverage(pd.Timedelta(minutes=1)),
        )
