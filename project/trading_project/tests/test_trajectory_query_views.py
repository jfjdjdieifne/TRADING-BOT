from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
import inspect

import pandas as pd
import pytest

from trading_system.research.hashing import canonical_sha256
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
    ExcursionReference,
    ExcursionReferenceKind,
    HorizonCompletionState,
    HorizonPolicyIdentity,
    HorizonRequest,
    InteractionStatus,
    ObservedEntityLocator,
    ObservedTargetReference,
    PairOrderStatus,
    QueryProtocolIdentity,
    QueryResolutionState,
    ProjectedInvalidationReference,
    ProjectedTargetReference,
    SamplingAlgorithmIdentity,
    SamplingMembershipState,
    SamplingPolicyIdentity,
    SUPPORTED_OBSERVED_PRODUCER_DOMAINS,
    TrajectoryQueryError,
    TrajectoryWindow,
    bind_sampling_membership,
    build_trajectory_window,
    decision_close_excursion_reference,
    create_asof_surface_view,
    create_trajectory_query_reference,
    decision_surface_view,
    derive_excursion_view,
    derive_observed_target_interaction,
    derive_projected_invalidation_interaction,
    derive_projected_target_interaction,
    derive_target_invalidation_view,
    derive_timing_view,
    resolve_observed_entity,
    verify_trajectory_window_source,
)
from trading_system.research.trajectory import trajectory_stage4a as s4a
from trading_system.research.trajectory import trajectory_stage4b1 as s4b1
from trading_system.research.trajectory import trajectory_stage4b2 as s4b2
from trading_system.research.trajectory import trajectory_stage4c as s4c
from trading_system.structure.swing_detector import EmpiricalConfirmationPolicy


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


def _b2_market(n: int = 90) -> pd.DataFrame:
    open_values, high_values, low_values, close_values = [], [], [], []
    level = 100.0
    for position in range(n):
        if position < 65:
            if position % 7 < 4:
                open_values.append(level)
                close_values.append(level + 5.0)
                level = close_values[-1]
            else:
                open_values.append(level)
                close_values.append(level - 3.0)
                level = close_values[-1]
        else:
            open_values.append(level)
            close_values.append(level - 6.0)
            level = close_values[-1]
        high_values.append(max(open_values[-1], close_values[-1]) + 1.0)
        low_values.append(min(open_values[-1], close_values[-1]) - 1.0)
    return pd.DataFrame(
        {"open": open_values, "high": high_values, "low": low_values, "close": close_values},
        index=pd.RangeIndex(n),
        dtype=float,
    )


def _b2_policy():
    return EmpiricalConfirmationPolicy(
        quantile=0.1,
        prior_continuation_reversals=tuple(0.01 * index for index in range(1, 50)),
    )


@pytest.fixture(scope="module")
def _b2_sources():
    market = _b2_market()
    adapter = PositionalTimelineAdapter("trajectory-b2-entity-fixture")
    timeline = MarketObservationTimeline.seal(adapter=adapter, market_history=market)
    structure = s4b1.build_structure_surface(
        timeline=timeline,
        adapter=adapter,
        market_history=market,
        swing_policy=_b2_policy(),
    )
    surfaces = {
        "LIQUIDITY": s4b2.build_liquidity_surface(
            timeline=timeline,
            adapter=adapter,
            market_history=market,
            structure_surface=structure,
        ),
        "ORDER_BLOCK": s4b2.build_order_block_surface(
            timeline=timeline,
            adapter=adapter,
            market_history=market,
            structure_surface=structure,
        ),
        "FVG": s4b2.build_fvg_surface(timeline=timeline, adapter=adapter, market_history=market),
        "DEALING_RANGE": s4b2.build_dealing_range_surface(
            timeline=timeline,
            adapter=adapter,
            market_history=market,
            structure_surface=structure,
        ),
    }
    return market, adapter, timeline, structure, surfaces


def _b2_case(sources, *, decision_position: int = 7, surfaces_override=None):
    market, adapter, timeline, _, surfaces = sources
    decision_key = adapter.key_for_position(
        market.index,
        decision_position,
        InformationPhase.COMPLETED_ROW_AVAILABLE,
    )
    case = create_trajectory_decision_case(
        timeline=timeline,
        adapter=adapter,
        market_history=market,
        decision_key=decision_key,
        surfaces=tuple(surfaces.values()) if surfaces_override is None else tuple(surfaces_override),
        parent_snapshot=None,
    )
    return case, decision_key


def _protocol_identity(**overrides):
    values = {
        "query_contract_type": "OBSERVED_ENTITY_CONTACT",
        "query_contract_version": "1",
        "protocol_id": "inclusive-ohlc-contact",
        "protocol_version": "1",
        "protocol_sha256": "a" * 64,
        "canonical_parameters": (("bar_set", "post-decision"), ("boundary", "inclusive")),
    }
    values.update(overrides)
    return QueryProtocolIdentity(**values)


def _sampling_membership(case, **overrides):
    adapter_key = PositionalTimelineAdapter(case.timeline_id).key_for_position(
        pd.RangeIndex(90), 0, InformationPhase.COMPLETED_ROW_AVAILABLE
    )
    values = {
        "case": case,
        "policy_identity": SamplingPolicyIdentity("sampling-protocol", "1", "1" * 64),
        "candidate_universe_id": "universe-A",
        "candidate_universe_sha256": "2" * 64,
        "selection_run_id": "run-A",
        "membership_id": "membership-A",
        "membership_role": "primary",
        "selection_key": adapter_key,
        "state": SamplingMembershipState.INCLUDED,
        "rationale_reference": "audit://selection/rationale-A",
        "deterministic_seed": 11,
        "algorithm_identity": SamplingAlgorithmIdentity("fixed-order", "1", "3" * 64),
        "paired_control_reference": "control-A",
        "attrition_rejection_reference": "attrition-A",
    }
    values.update(overrides)
    return bind_sampling_membership(**values)


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
    empty_reference = decision_close_excursion_reference(window)
    assert derive_excursion_view(window=window, reference=empty_reference).status is DerivedViewStatus.NO_POST_DECISION_ROWS
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


def test_observed_entity_resolves_verified_stage4b2_row_and_stays_distinct_from_projection(_b2_sources):
    market, adapter, timeline, _, surfaces = _b2_sources
    case, _ = _b2_case(_b2_sources, decision_position=7)
    end = adapter.key_for_position(market.index, 14, InformationPhase.COMPLETED_ROW_AVAILABLE)
    window = build_trajectory_window(
        case=case,
        timeline=timeline,
        adapter=adapter,
        market_history=market,
        horizon_request=_horizon(end),
        coverage_contract=_coverage(None),
    )
    liquidity_binding = next(
        binding for binding in case.surface_prefix_bindings if binding.domain == "LIQUIDITY"
    )
    observed = ObservedEntityLocator(
        producer_domain="LIQUIDITY",
        stable_binding_hash=liquidity_binding.stable_binding_hash,
        canonical_entity_id="0",
    )
    resolved = resolve_observed_entity(
        case=case,
        surfaces=tuple(surfaces.values()),
        locator=observed,
    )
    assert resolved.canonical_price == 121.0
    assert resolved.side_or_direction == "HIGH_SIDE"
    assert resolved.origin_positions == (3,)
    assert resolved.confirmation_positions == (5,)
    assert resolved.availability_position == 5
    assert "observed_price" not in {field.name for field in fields(ObservedEntityLocator)}
    with pytest.raises(TypeError):
        ObservedEntityLocator(
            producer_domain="LIQUIDITY",
            stable_binding_hash=liquidity_binding.stable_binding_hash,
            canonical_entity_id="0",
            observed_price=999999.0,
        )  # type: ignore[call-arg]
    with pytest.raises(TrajectoryQueryError, match="MARKET_TIMELINE"):
        ObservedEntityLocator(
            producer_domain="MARKET_TIMELINE",
            stable_binding_hash=case.decision_prefix_hash,
            canonical_entity_id="0",
        )

    projected = _pair(case, target_price=121.0).projected_target
    projected_view = derive_projected_target_interaction(window=window, projected_target=projected)
    observed_view = derive_observed_target_interaction(
        window=window,
        case=case,
        surfaces=tuple(surfaces.values()),
        observed_target=observed,
    )
    assert projected.identity_hash != resolved.identity_hash
    assert projected_view.view_hash != observed_view.view_hash
    assert projected_view.touch_positions == observed_view.touch_positions
    assert observed_view.touch_positions
    assert observed_view.observed_target_identity == resolved.identity_hash
    assert observed_view.query_resolution is QueryResolutionState.RESOLVED
    query_with_entity = create_trajectory_query_reference(
        case=case,
        protocol_identity=_protocol_identity(),
        horizon_request=_horizon(end),
        candidate_pair=None,
        sampling_membership=None,
        observed_entity=observed,
    )
    query_without_entity = create_trajectory_query_reference(
        case=case,
        protocol_identity=_protocol_identity(),
        horizon_request=_horizon(end),
        candidate_pair=None,
        sampling_membership=None,
    )
    assert query_with_entity.query_id != query_without_entity.query_id
    assert query_with_entity.case_id == query_without_entity.case_id == case.case_id
    assert observed_view.horizon_completion is HorizonCompletionState.COMPLETE
    assert observed_view.source_censoring is CensoringState.OBSERVED_TO_REQUESTED_END
    with pytest.raises(TypeError, match="different type"):
        derive_observed_target_interaction(
            window=window,
            case=case,
            surfaces=tuple(surfaces.values()),
            observed_target=projected,  # type: ignore[arg-type]
        )
    with pytest.raises(TypeError, match="different type"):
        derive_projected_target_interaction(
            window=window,
            projected_target=observed,  # type: ignore[arg-type]
        )
    with pytest.raises(TrajectoryQueryError, match="projected target reference"):
        CandidatePricePair(
            candidate_pair_id="invalid-observed-invalidation",
            projected_target=observed,  # type: ignore[arg-type]
            projected_invalidation=_pair(case).projected_invalidation,
        )
    assert derive_timing_view(window=window, target_reference=projected).observed_bar_offset is not None
    timing = derive_timing_view(
        window=window,
        target_reference=observed,
        case=case,
        surfaces=tuple(surfaces.values()),
    )
    assert timing.reference_identity == resolved.identity_hash
    invalidation = _pair(case, invalidation_price=121.0).projected_invalidation
    assert derive_timing_view(window=window, target_reference=invalidation).observed_bar_offset is not None
    excursion_reference = decision_close_excursion_reference(window)
    excursion = derive_excursion_view(window=window, reference=excursion_reference)
    assert excursion.reference_kind is ExcursionReferenceKind.MARKET_MARK
    assert excursion.observed_max_high == max(bar.high for bar in window.bars)
    assert excursion.observed_min_low == min(bar.low for bar in window.bars)
    assert excursion.observed_high_delta_from_reference == excursion.observed_max_high - window.decision_close_observation.value
    assert excursion.observed_low_delta_from_reference == excursion.observed_min_low - window.decision_close_observation.value
    with pytest.raises(TrajectoryQueryError, match="close"):
        ExcursionReference(
            kind=ExcursionReferenceKind.MARKET_MARK,
            information_key=case.decision_key,
            value=999999.0,
            source_binding_sha256=excursion_reference.source_binding_sha256,
            source_field="execution_fill",
        )
    forged_mark = ExcursionReference(
        kind=ExcursionReferenceKind.MARKET_MARK,
        information_key=case.decision_key,
        value=999999.0,
        source_binding_sha256=excursion_reference.source_binding_sha256,
        source_field="close",
    )
    with pytest.raises(TrajectoryQueryError, match="verified decision MARKET_MARK"):
        derive_excursion_view(window=window, reference=forged_mark)


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


def test_query_protocol_sampling_candidate_and_horizon_identities_do_not_change_case():
    market = _market(7)
    case, _, adapter, _ = _case(market, timeline_id="identity-separation")
    end = adapter.key_for_position(market.index, 5, InformationPhase.COMPLETED_ROW_AVAILABLE)
    horizon_a = _horizon(end, "horizon-A")
    horizon_b = _horizon(end, "horizon-B")
    included = _sampling_membership(case)
    excluded = _sampling_membership(case, membership_id="membership-B", state=SamplingMembershipState.EXCLUDED)
    pair_a = _pair(case, pair_id="pair-a")
    pair_b = _pair(case, pair_id="pair-b", target_price=106.0)
    query_a = create_trajectory_query_reference(
        case=case,
        protocol_identity=_protocol_identity(),
        horizon_request=horizon_a,
        candidate_pair=pair_a,
        sampling_membership=included,
    )
    query_b = create_trajectory_query_reference(
        case=case,
        protocol_identity=_protocol_identity(protocol_id="different-protocol"),
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
    assert not {
        "window", "trajectory", "market_history", "future_rows", "outcome", "future_outcome"
    }.intersection(signature.parameters)
    with pytest.raises(TypeError, match="QueryProtocolIdentity"):
        create_trajectory_query_reference(
            case=case,
            protocol_identity=None,  # type: ignore[arg-type]
            horizon_request=horizon_a,
            candidate_pair=None,
            sampling_membership=None,
        )
    with pytest.raises(TrajectoryQueryError, match="HorizonPolicyIdentity"):
        HorizonRequest(policy_identity=SamplingPolicyIdentity("sample-X", "1", "9" * 64), requested_end_key=end)  # type: ignore[arg-type]


def test_each_query_protocol_field_and_study_identity_changes_query_id_without_changing_case():
    market = _market(7)
    case, _, adapter, _ = _case(market, timeline_id="protocol-id-fields")
    end = adapter.key_for_position(market.index, 5, InformationPhase.COMPLETED_ROW_AVAILABLE)
    horizon = _horizon(end)
    base_protocol = _protocol_identity()
    baseline = create_trajectory_query_reference(
        case=case,
        protocol_identity=base_protocol,
        horizon_request=horizon,
        candidate_pair=None,
        sampling_membership=None,
    )
    changed_protocols = (
        _protocol_identity(query_contract_type="OTHER_QUERY"),
        _protocol_identity(query_contract_version="2"),
        _protocol_identity(protocol_id="other-protocol"),
        _protocol_identity(protocol_version="2"),
        _protocol_identity(protocol_sha256="b" * 64),
        _protocol_identity(canonical_parameters=(("bar_set", "post-decision"), ("boundary", "exclusive"))),
    )
    changed_ids = {
        create_trajectory_query_reference(
            case=case,
            protocol_identity=protocol,
            horizon_request=horizon,
            candidate_pair=None,
            sampling_membership=None,
        ).query_id
        for protocol in changed_protocols
    }
    assert baseline.query_id not in changed_ids
    assert len(changed_ids) == len(changed_protocols)
    with_study = create_trajectory_query_reference(
        case=case,
        protocol_identity=base_protocol,
        horizon_request=horizon,
        candidate_pair=None,
        sampling_membership=None,
        study_identity="4" * 64,
    )
    assert with_study.query_id != baseline.query_id
    assert baseline.case_id == with_study.case_id == case.case_id
    assert not {"outcome", "future_answer", "result"}.intersection(
        inspect.signature(create_trajectory_query_reference).parameters
    )


def test_coverage_contract_identity_changes_path_and_derived_view_not_query_id():
    index = pd.date_range("2024-01-01 00:00", periods=8, freq="min", tz="UTC")
    market = _market(8, index=index)
    case, timeline, adapter, _ = _case(
        market, timeline_id="coverage-contract-identity", time_indexed=True
    )
    end = adapter.key_for_position(market.index, 6, InformationPhase.COMPLETED_ROW_AVAILABLE)
    horizon = _horizon(end)
    pair = _pair(case, target_price=250.0)
    protocol = _protocol_identity()
    query = create_trajectory_query_reference(
        case=case,
        protocol_identity=protocol,
        horizon_request=horizon,
        candidate_pair=pair,
        sampling_membership=None,
    )
    baseline_contract = _coverage(pd.Timedelta(minutes=1))
    variants = (
        replace(baseline_contract, contract_id="other-grid"),
        replace(baseline_contract, contract_version="2"),
        replace(baseline_contract, contract_sha256="d" * 64),
        replace(baseline_contract, expected_step=pd.Timedelta(minutes=2)),
    )

    baseline_window = build_trajectory_window(
        case=case,
        timeline=timeline,
        adapter=adapter,
        market_history=market,
        horizon_request=horizon,
        coverage_contract=baseline_contract,
    )
    baseline_result = derive_projected_target_interaction(
        window=baseline_window, projected_target=pair.projected_target
    )
    changed_paths = set()
    changed_results = set()
    for contract in variants:
        window = build_trajectory_window(
            case=case,
            timeline=timeline,
            adapter=adapter,
            market_history=market,
            horizon_request=horizon,
            coverage_contract=contract,
        )
        result = derive_projected_target_interaction(
            window=window, projected_target=pair.projected_target
        )
        repeated_query = create_trajectory_query_reference(
            case=case,
            protocol_identity=protocol,
            horizon_request=horizon,
            candidate_pair=pair,
            sampling_membership=None,
        )
        assert repeated_query.query_id == query.query_id
        assert window.reference.path_id != baseline_window.reference.path_id
        assert result.view_hash != baseline_result.view_hash
        changed_paths.add(window.reference.path_id)
        changed_results.add(result.view_hash)

    assert len(changed_paths) == len(variants)
    assert len(changed_results) == len(variants)
    assert query.case_id == case.case_id


def test_every_sampling_audit_identity_field_participates_and_is_path_free():
    market = _market(7)
    case, _, adapter, _ = _case(market, timeline_id="sampling-audit-fields")
    base = _sampling_membership(case)
    alternate_key = adapter.key_for_position(market.index, 1, InformationPhase.COMPLETED_ROW_AVAILABLE)
    changes = (
        {"policy_identity": SamplingPolicyIdentity("sampling-protocol-2", "1", "1" * 64)},
        {"policy_identity": SamplingPolicyIdentity("sampling-protocol", "2", "1" * 64)},
        {"policy_identity": SamplingPolicyIdentity("sampling-protocol", "1", "5" * 64)},
        {"candidate_universe_id": "universe-B"},
        {"candidate_universe_sha256": "6" * 64},
        {"selection_run_id": "run-B"},
        {"membership_id": "membership-B"},
        {"membership_role": "control"},
        {"selection_key": alternate_key},
        {"state": SamplingMembershipState.EXCLUDED},
        {"rationale_reference": "audit://selection/rationale-B"},
        {"deterministic_seed": 12},
        {"algorithm_identity": SamplingAlgorithmIdentity("other-order", "1", "7" * 64)},
        {"paired_control_reference": "control-B"},
        {"attrition_rejection_reference": "attrition-B"},
    )
    identities = {base.identity_hash}
    for change in changes:
        identities.add(_sampling_membership(case, **change).identity_hash)
    assert len(identities) == len(changes) + 1

    later_case, _, _, _ = _case(market, timeline_id="sampling-audit-fields", decision_position=2)
    assert _sampling_membership(later_case).identity_hash != base.identity_hash
    signature = inspect.signature(bind_sampling_membership)
    assert not {
        "window", "trajectory", "future_rows", "outcome", "future_outcome", "path"
    }.intersection(signature.parameters)


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


def test_all_supported_stage4b2_domains_resolve_frozen_producer_rows(_b2_sources):
    market, _, _, _, surfaces = _b2_sources
    case, _ = _b2_case(_b2_sources, decision_position=20)
    assert set(SUPPORTED_OBSERVED_PRODUCER_DOMAINS) == {
        "LIQUIDITY", "ORDER_BLOCK", "FVG", "DEALING_RANGE"
    }
    id_columns = {
        "LIQUIDITY": "level_id",
        "ORDER_BLOCK": "zone_id",
        "FVG": "fvg_id",
        "DEALING_RANGE": "range_id",
    }
    availability_columns = {
        "LIQUIDITY": "source_confirmation_position",
        "ORDER_BLOCK": "creation_position",
        "FVG": "creation_position",
        "DEALING_RANGE": "creation_position",
    }
    for domain in SUPPORTED_OBSERVED_PRODUCER_DOMAINS:
        frame = surfaces[domain].normalized_entity_frame
        visible = frame.loc[frame[availability_columns[domain]] <= case.decision_key.bar_position]
        assert not visible.empty
        canonical_id = str(visible.iloc[0][id_columns[domain]])
        binding = next(item for item in case.surface_prefix_bindings if item.domain == domain)
        resolved = resolve_observed_entity(
            case=case,
            surfaces=tuple(surfaces.values()),
            locator=ObservedEntityLocator(domain, binding.stable_binding_hash, canonical_id),
        )
        assert resolved.locator.canonical_entity_id == canonical_id
        assert resolved.availability_position <= case.decision_key.bar_position
        assert resolved.row and resolved.canonical_row_sha256
        assert resolved.canonical_price is not None or (
            resolved.lower_bound is not None and resolved.upper_bound is not None
        )


def test_unknown_duplicate_and_future_unavailable_entity_ids_fail_closed(_b2_sources):
    market, adapter, timeline, _, surfaces = _b2_sources
    early_case, _ = _b2_case(_b2_sources, decision_position=4)
    early_binding = next(item for item in early_case.surface_prefix_bindings if item.domain == "LIQUIDITY")
    unavailable_origin_first = ObservedEntityLocator(
        "LIQUIDITY", early_binding.stable_binding_hash, "0"
    )
    with pytest.raises(TrajectoryQueryError, match="exactly one decision-visible row"):
        resolve_observed_entity(
            case=early_case,
            surfaces=tuple(surfaces.values()),
            locator=unavailable_origin_first,
        )

    available_case, _ = _b2_case(_b2_sources, decision_position=5)
    available_binding = next(item for item in available_case.surface_prefix_bindings if item.domain == "LIQUIDITY")
    liquidity = resolve_observed_entity(
        case=available_case,
        surfaces=tuple(surfaces.values()),
        locator=ObservedEntityLocator("LIQUIDITY", available_binding.stable_binding_hash, "0"),
    )
    assert liquidity.origin_positions == (3,)
    assert liquidity.confirmation_positions == (5,)
    assert liquidity.availability_position == 5
    assert liquidity.origin_positions[0] < liquidity.availability_position

    unknown = ObservedEntityLocator("LIQUIDITY", available_binding.stable_binding_hash, "999999")
    with pytest.raises(TrajectoryQueryError, match="exactly one decision-visible row"):
        resolve_observed_entity(case=available_case, surfaces=tuple(surfaces.values()), locator=unknown)

    fvg_early_case, _ = _b2_case(_b2_sources, decision_position=1)
    fvg_early_binding = next(item for item in fvg_early_case.surface_prefix_bindings if item.domain == "FVG")
    with pytest.raises(TrajectoryQueryError, match="exactly one decision-visible row"):
        resolve_observed_entity(
            case=fvg_early_case,
            surfaces=tuple(surfaces.values()),
            locator=ObservedEntityLocator("FVG", fvg_early_binding.stable_binding_hash, "0"),
        )
    fvg_case, _ = _b2_case(_b2_sources, decision_position=2)
    fvg_binding = next(item for item in fvg_case.surface_prefix_bindings if item.domain == "FVG")
    fvg = resolve_observed_entity(
        case=fvg_case,
        surfaces=tuple(surfaces.values()),
        locator=ObservedEntityLocator("FVG", fvg_binding.stable_binding_hash, "0"),
    )
    assert fvg.origin_positions == (0,)
    assert fvg.creation_position == fvg.availability_position == 2

    # Recompute the normalized-entity and surface IDs around a duplicate. The
    # new local consistency pass must reject this cross-table inconsistency before
    # a decision case can bind the surface.
    original = surfaces["LIQUIDITY"]
    duplicated_rows = pd.concat(
        [original.normalized_entity_frame, original.normalized_entity_frame.iloc[[0]]],
        ignore_index=True,
    )
    entity_hash = canonical_sha256(
        domain="STAGE4B2_NORMALIZED_ENTITY_V1", payload=duplicated_rows
    )
    duplicate_surface_id = canonical_sha256(
        domain="STAGE4B2_SURFACE_IDENTITY_V1",
        payload={
            "surface_class": original.__class__.__name__,
            "domain": "LIQUIDITY",
            "contract_version": s4b2.CONTRACT_LIQUIDITY,
            "timeline_id": original.timeline_id,
            "timeline_hash": original.timeline_hash,
            "adapter_kind": original.adapter_kind,
            "structure_surface_id": original.structure_surface_id,
            "reconstruction_input_hash": original.reconstruction_input_hash,
            "complete_result_hash": original.complete_result_hash,
            "normalized_entity_hash": entity_hash,
            "normalized_event_hash": original.normalized_event_hash,
        },
    )
    duplicate_surface = replace(
        original,
        normalized_entity_frame=duplicated_rows,
        normalized_entity_hash=entity_hash,
        surface_id=duplicate_surface_id,
    )
    duplicate_surfaces = (duplicate_surface,) + tuple(
        surface for domain, surface in surfaces.items() if domain != "LIQUIDITY"
    )
    with pytest.raises(TrajectoryCaseError, match="normalized entity rows"):
        _b2_case(
            _b2_sources,
            decision_position=20,
            surfaces_override=duplicate_surfaces,
        )


def test_observed_resolution_never_replays_stage4_producer_engines(monkeypatch, _b2_sources):
    case, _ = _b2_case(_b2_sources, decision_position=20)
    surfaces = _b2_sources[4]
    binding = next(item for item in case.surface_prefix_bindings if item.domain == "LIQUIDITY")
    locator = ObservedEntityLocator("LIQUIDITY", binding.stable_binding_hash, "0")

    def forbidden(*args, **kwargs):
        raise AssertionError("producer engine replay is forbidden during entity resolution")

    monkeypatch.setattr(s4b2, "build_liquidity_surface", forbidden)
    monkeypatch.setattr(s4b1, "build_structure_surface", forbidden)
    resolved = resolve_observed_entity(
        case=case,
        surfaces=tuple(surfaces.values()),
        locator=locator,
    )
    assert resolved.canonical_price == 121.0


def test_full_surface_id_stays_provenance_only_under_future_append():
    short_market = _b2_market(70)
    long_market = _b2_market(90)
    short_adapter = PositionalTimelineAdapter("future-surface-identity")
    long_adapter = PositionalTimelineAdapter("future-surface-identity")
    short_timeline = MarketObservationTimeline.seal(adapter=short_adapter, market_history=short_market)
    long_timeline = MarketObservationTimeline.seal(adapter=long_adapter, market_history=long_market)
    short_structure = s4b1.build_structure_surface(
        timeline=short_timeline,
        adapter=short_adapter,
        market_history=short_market,
        swing_policy=_b2_policy(),
    )
    long_structure = s4b1.build_structure_surface(
        timeline=long_timeline,
        adapter=long_adapter,
        market_history=long_market,
        swing_policy=_b2_policy(),
    )
    short_surface = s4b2.build_liquidity_surface(
        timeline=short_timeline,
        adapter=short_adapter,
        market_history=short_market,
        structure_surface=short_structure,
    )
    long_surface = s4b2.build_liquidity_surface(
        timeline=long_timeline,
        adapter=long_adapter,
        market_history=long_market,
        structure_surface=long_structure,
    )
    decision = short_adapter.key_for_position(
        short_market.index, 60, InformationPhase.COMPLETED_ROW_AVAILABLE
    )
    short_case = create_trajectory_decision_case(
        timeline=short_timeline,
        adapter=short_adapter,
        market_history=short_market,
        decision_key=decision,
        surfaces=(short_surface,),
        parent_snapshot=None,
    )
    long_case = create_trajectory_decision_case(
        timeline=long_timeline,
        adapter=long_adapter,
        market_history=long_market,
        decision_key=decision,
        surfaces=(long_surface,),
        parent_snapshot=None,
    )
    assert short_surface.surface_id != long_surface.surface_id
    assert short_case.case_id == long_case.case_id
    assert short_case.surface_prefix_bindings[0].stable_binding_hash == long_case.surface_prefix_bindings[0].stable_binding_hash
    assert short_case.source_provenance.provenance_binding_hash != long_case.source_provenance.provenance_binding_hash
    locator = ObservedEntityLocator(
        "LIQUIDITY", short_case.surface_prefix_bindings[0].stable_binding_hash, "0"
    )
    short_entity = resolve_observed_entity(case=short_case, surfaces=(short_surface,), locator=locator)
    long_entity = resolve_observed_entity(case=short_case, surfaces=(long_surface,), locator=locator)
    assert short_entity.identity_hash == long_entity.identity_hash
    assert short_entity.canonical_row_sha256 == long_entity.canonical_row_sha256


def test_market_mutation_after_verification_does_not_change_window_snapshot(monkeypatch):
    market = _market(6)
    baseline_high = float(market.loc[2, "high"])
    case, timeline, adapter, _ = _case(market, timeline_id="market-toctou")
    end = adapter.key_for_position(market.index, 5, InformationPhase.COMPLETED_ROW_AVAILABLE)
    original_verify = MarketObservationTimeline.verify

    def verify_then_mutate_original(self, *, adapter, market_history):
        result = original_verify(self, adapter=adapter, market_history=market_history)
        if self.timeline_id == "market-toctou":
            market.loc[2, "high"] = 999999.0
        return result

    monkeypatch.setattr(MarketObservationTimeline, "verify", verify_then_mutate_original)
    window = build_trajectory_window(
        case=case,
        timeline=timeline,
        adapter=adapter,
        market_history=market,
        horizon_request=_horizon(end),
        coverage_contract=_coverage(None),
    )
    assert market.loc[2, "high"] == 999999.0
    assert next(bar for bar in window.bars if bar.position == 2).high == baseline_high


def test_stage4_mutation_after_prefix_projection_cannot_change_frozen_view(monkeypatch, _b2_sources):
    market, adapter, timeline, _, source_surfaces = _b2_sources
    local_liquidity = replace(
        source_surfaces["LIQUIDITY"],
        normalized_entity_frame=source_surfaces["LIQUIDITY"].normalized_entity_frame.copy(deep=True),
    )
    surfaces = (local_liquidity,) + tuple(
        surface for domain, surface in source_surfaces.items() if domain != "LIQUIDITY"
    )
    case, decision = _b2_case(_b2_sources, decision_position=20, surfaces_override=surfaces)
    expected_price = float(local_liquidity.normalized_entity_frame.iloc[0]["immutable_level_price"])
    original_project = s4b2.project_domain_prefix

    def project_then_mutate_caller_surface(*, surface, boundary_key):
        result = original_project(surface=surface, boundary_key=boundary_key)
        local_liquidity.normalized_entity_frame.loc[0, "immutable_level_price"] = 999999.0
        return result

    monkeypatch.setattr(s4b2, "project_domain_prefix", project_then_mutate_caller_surface)
    view = decision_surface_view(case=case, surfaces=surfaces)
    liquidity_instance = next(item for item in view.surfaces if item.domain == "LIQUIDITY")
    entity_table = liquidity_instance.tables[2]
    price_index = entity_table.columns.index("immutable_level_price")
    assert float(entity_table.rows[0][price_index].value) == expected_price
    assert float(local_liquidity.normalized_entity_frame.iloc[0]["immutable_level_price"]) == 999999.0
    assert view.as_of_key == decision


def test_nested_mutable_surface_cells_fail_closed(_b2_sources):
    case, decision = _b2_case(_b2_sources, decision_position=20)
    surfaces = _b2_sources[4]
    original = surfaces["LIQUIDITY"]
    frame = original.normalized_entity_frame.copy(deep=True)
    frame["level_id"] = frame["level_id"].astype(object)
    frame.at[0, "level_id"] = {"forged": "nested"}
    unsafe = replace(original, normalized_entity_frame=frame)
    unsafe_surfaces = (unsafe,) + tuple(
        surface for domain, surface in surfaces.items() if domain != "LIQUIDITY"
    )
    with pytest.raises(TrajectoryQueryError, match="unsupported mutable"):
        decision_surface_view(case=case, surfaces=unsafe_surfaces)


def test_standalone_views_preserve_gap_and_right_censoring_independently():
    index = pd.DatetimeIndex(
        [
            pd.Timestamp("2024-01-01 00:00", tz="UTC"),
            pd.Timestamp("2024-01-01 00:01", tz="UTC"),
            pd.Timestamp("2024-01-01 00:03", tz="UTC"),
            pd.Timestamp("2024-01-01 00:04", tz="UTC"),
        ]
    )
    market = _market(4, index=index)
    case, timeline, adapter, _ = _case(market, timeline_id="gap-right-censor", time_indexed=True)
    requested = _future_key(
        adapter,
        market,
        6,
        time_after_data=index[-1] + pd.Timedelta(minutes=2),
    )
    window = build_trajectory_window(
        case=case,
        timeline=timeline,
        adapter=adapter,
        market_history=market,
        horizon_request=_horizon(requested),
        coverage_contract=_coverage(pd.Timedelta(minutes=1)),
    )
    target = _pair(case, target_price=500.0).projected_target
    interaction = derive_projected_target_interaction(window=window, projected_target=target)
    timing = derive_timing_view(window=window, target_reference=target)
    pair_view = derive_target_invalidation_view(
        window=window,
        candidate_pair=_pair(case, target_price=500.0, invalidation_price=600.0),
    )
    assert pair_view.ordering is PairOrderStatus.NO_OBSERVED_TOUCH_RIGHT_CENSORED_WITH_COVERAGE_GAPS
    assert pair_view.horizon_completion is HorizonCompletionState.INCOMPLETE
    assert pair_view.coverage_assessment is CoverageAssessment.GAPS_OR_CADENCE_DEVIATION
    assert pair_view.coverage_issues and pair_view.censoring_state is CensoringState.RIGHT_CENSORED
    assert pair_view.query_resolution is QueryResolutionState.RESOLVED
    assert interaction.status is InteractionStatus.NOT_OBSERVED_RIGHT_CENSORED_WITH_COVERAGE_GAPS
    assert interaction.horizon_completion is HorizonCompletionState.INCOMPLETE
    assert interaction.source_censoring is CensoringState.RIGHT_CENSORED
    assert interaction.coverage_assessment is CoverageAssessment.GAPS_OR_CADENCE_DEVIATION
    assert interaction.coverage_issues
    assert interaction.query_resolution is QueryResolutionState.RESOLVED
    assert timing.source_censoring is interaction.source_censoring
    assert timing.coverage_assessment is interaction.coverage_assessment
    assert timing.coverage_issues == interaction.coverage_issues
    assert timing.horizon_completion is interaction.horizon_completion
    assert timing.interaction_status is not InteractionStatus.NOT_OBSERVED_RIGHT_CENSORED


def test_horizon_completion_is_independent_from_source_end_censoring():
    market = _market(5)
    case, timeline, adapter, _ = _case(market, timeline_id="complete-at-source-end")
    last_key = adapter.key_for_position(market.index, 4, InformationPhase.COMPLETED_ROW_AVAILABLE)
    window = build_trajectory_window(
        case=case,
        timeline=timeline,
        adapter=adapter,
        market_history=market,
        horizon_request=_horizon(last_key),
        coverage_contract=_coverage(None),
    )
    interaction = derive_projected_target_interaction(
        window=window,
        projected_target=_pair(case, target_price=500.0).projected_target,
    )
    assert interaction.horizon_completion is HorizonCompletionState.COMPLETE
    assert interaction.source_censoring is CensoringState.RIGHT_CENSORED


def test_invalid_or_unresolved_entity_query_never_becomes_no_touch(_b2_sources):
    case, _ = _b2_case(_b2_sources, decision_position=20)
    surfaces = tuple(_b2_sources[4].values())
    binding = next(item for item in case.surface_prefix_bindings if item.domain == "LIQUIDITY")
    unknown = ObservedEntityLocator("LIQUIDITY", binding.stable_binding_hash, "999999")
    with pytest.raises(TrajectoryQueryError, match="exactly one decision-visible row"):
        resolve_observed_entity(case=case, surfaces=surfaces, locator=unknown)
