from __future__ import annotations

import hashlib
import json

import numpy as np
import pandas as pd
import pytest

from trading_system.research.information_time import (
    INFORMATION_KEY_VERSION,
    InformationKey,
    InformationPhase,
    TimeIndexedTimelineAdapter,
)
from trading_system.research.trajectory.trajectory_case_adapter import create_trajectory_decision_case
from trading_system.research.trajectory.trajectory_contract import MarketObservationTimeline
from trading_system.research.trajectory.trajectory_query_views import (
    CoverageContract,
    CoverageAssessment,
    CensoringState,
    HorizonPolicyIdentity,
    HorizonRequest,
    build_trajectory_window,
    decision_close_excursion_reference,
    derive_excursion_view,
)
from trading_system.research.trajectory import trajectory_stage4a as s4a
from trading_system.research.trajectory import trajectory_stage4b2 as s4b2
from trading_system.research.trajectory import trajectory_stage4c as s4c
from trading_system.research.trajectory.movement_context_empirical import (
    EXPERIMENT_ID,
    HORIZON,
    M0_FEATURES,
    M1_ADDITIONAL_FEATURES,
    M1_FEATURES,
    _empty_candidate_columns,
    _OUTCOME_COLUMNS,
    _fit_comparison,
    _outcome_rows,
    _overlap_summary,
    build_experiment,
    build_experiment_from_surfaces,
    write_outputs,
    run_from_binance_csv,
    MovementContextExperimentError,
)
from trading_system.sources import SourceArtifactIdentity


def _market(n: int = 240, *, missing_positions: tuple[int, ...] = ()) -> pd.DataFrame:
    """Synthetic software fixture only; never empirical evidence."""
    full_index = pd.date_range("2026-05-01T00:01:00Z", periods=n, freq="min")
    close = []
    level = 100.0
    for position in range(n):
        group = position // 3
        if position > 0 and position % 3 == 0:
            level += 1.5 + (group % 7) * 0.13
        close.append(level + 0.02 * (position % 3))
    close_values = np.asarray(close, dtype="float64")
    open_values = close_values - 0.04
    high_values = np.maximum(open_values, close_values) + 0.08
    low_values = np.minimum(open_values, close_values) - 0.08
    frame = pd.DataFrame(
        {
            "open": open_values,
            "high": high_values,
            "low": low_values,
            "close": close_values,
            "volume": np.full(n, 10.0, dtype="float64"),
        },
        index=full_index,
    )
    if missing_positions:
        frame = frame.drop(frame.index[list(missing_positions)])
    return frame


def _identity(end: str = "2026-05-01T04:00:00Z") -> SourceArtifactIdentity:
    return SourceArtifactIdentity(
        symbol="BTCUSDT",
        market_type="SPOT",
        interval="1m",
        period_start_utc="2026-05-01T00:00:00Z",
        period_end_utc=end,
    )


def _build_surfaces(market: pd.DataFrame, *, timeline_id: str = "movement-test"):
    # The experiment seals nanosecond-resolution UTC keys; conversion is exact
    # because source rows are minute boundaries.
    normalized = market.copy(deep=True)
    normalized.index = normalized.index.tz_convert("UTC").as_unit("ns")
    adapter = TimeIndexedTimelineAdapter(timeline_id)
    timeline = MarketObservationTimeline.seal(adapter=adapter, market_history=normalized)
    fvg = s4b2.build_fvg_surface(timeline=timeline, adapter=adapter, market_history=normalized)
    volatility = s4a.build_volatility_surface(timeline=timeline, adapter=adapter, market_history=normalized)
    htf = s4c.build_htf_scale_surface(
        timeline=timeline,
        adapter=adapter,
        market_history=normalized,
        scale_spec=s4c.HtfScaleSpec("H1", pd.Timedelta(hours=1)),
        cadence=s4c.CadenceGridContract(
            grid_epoch_utc=pd.Timestamp("1970-01-01T00:00:00Z"),
            period=pd.Timedelta(minutes=1),
        ),
    )
    return normalized, timeline, adapter, fvg, volatility, htf


def _bundle_for(market: pd.DataFrame, *, source_hash: str = "a" * 64, cutoff: str = "2026-05-01T02:00:00Z"):
    return build_experiment(
        market_history=market,
        source_identity=_identity(),
        source_file_sha256=source_hash,
        development_cutoff_utc=cutoff,
        timeline_id="movement-test-run",
    )


def test_candidate_universe_is_all_creation_entities_and_excludes_lifecycle_predictors():
    market = _market()
    normalized, timeline, adapter, fvg, volatility, htf = _build_surfaces(market)
    bundle = build_experiment_from_surfaces(
        market_history=normalized,
        timeline=timeline,
        adapter=adapter,
        source_identity=_identity(),
        source_file_sha256="a" * 64,
        fvg_surface=fvg,
        volatility_surface=volatility,
        htf_surface=htf,
        development_cutoff_utc="2026-05-01T02:00:00Z",
    )

    created_ids = set(
        fvg.normalized_event_frame.loc[
            fvg.normalized_event_frame["event_type"] == "FVG_CREATED", "fvg_id"
        ].astype(str)
    )
    assert len(bundle.candidate_context) == len(fvg.normalized_entity_frame)
    assert list(bundle.candidate_context.columns) == _empty_candidate_columns()
    assert set(bundle.candidate_context["candidate_id"]) == created_ids
    assert set(bundle.candidate_context["event_type"]) == {"FVG_CREATED"}
    assert bundle.summary["all_stage4b2_creation_entities_preserved"] is True
    forbidden = ("first_touch", "far_side", "reclaim", "fvg_age", "lifecycle")
    assert not any(any(token in column.lower() for token in forbidden) for column in bundle.candidate_context.columns)
    assert bundle.candidate_context["same_information_batch_order_unknown"].dtype == bool
    assert bundle.candidate_context["creation_key_information_phase"].eq("COMPLETED_ROW_AVAILABLE").all()
    assert bundle.candidate_context["stage4c_h1_close_batch_order_unknown__state"].notna().all()
    assert bundle.candidate_context["stage4a_true_range_history_count__state"].notna().all()
    assert bundle.protocol["outcome"]["horizon_ns"] == HORIZON.value
    assert bundle.protocol["experiment_id"] == EXPERIMENT_ID
    assert bundle.protocol["m0_fields"] == list(M0_FEATURES)
    assert bundle.protocol["m1_additional_fields"] == list(M1_ADDITIONAL_FEATURES)
    assert set(M1_FEATURES) == set(M0_FEATURES).union(M1_ADDITIONAL_FEATURES)
    assert bundle.summary["source"]["source_validation"]["state"] == (
        "CALLER_SUPPLIED_FRAME_NOT_VERIFIED_BY_BINANCE_ADAPTER"
    )
    assert bundle.summary["source"]["source_contract"]["schema_contract"].endswith("_V1")
    assert bundle.summary["source"]["source_contract"]["source_origin_authenticated"] is False
    assert bundle.protocol["source_and_surface_identity"]["muf_s1_contract"]["declared_grid"].startswith("NONE;")
    cadence_payload = bundle.protocol["source_and_surface_identity"]["stage4c_h1_surface"]["cadence_contract_payload"]
    assert cadence_payload["grid_epoch_utc_ns"] == pd.Timestamp("1970-01-01T00:00:00Z").value
    assert cadence_payload["period_ns"] == pd.Timedelta(minutes=1).value
    assert bundle.candidate_context["source_validation_state"].eq(
        "CALLER_SUPPLIED_FRAME_NOT_VERIFIED_BY_BINANCE_ADAPTER"
    ).all()


def test_zero_candidate_population_keeps_empty_schema_and_returns_inconclusive():
    market = _market(3)
    bundle = build_experiment(
        market_history=market,
        source_identity=_identity(end="2026-05-01T00:03:00Z"),
        source_file_sha256="d" * 64,
        development_cutoff_utc="2026-05-01T00:02:00Z",
        timeline_id="no-fvg-entities",
    )
    assert bundle.candidate_context.empty
    assert bundle.excursion_outcomes.empty
    assert list(bundle.candidate_context.columns) == _empty_candidate_columns()
    assert list(bundle.excursion_outcomes.columns) == list(_OUTCOME_COLUMNS)
    assert len(bundle.candidate_context.columns) > len(M1_FEATURES)
    assert all(feature in bundle.candidate_context.columns for feature in M1_FEATURES)
    assert "source_validation_state" in bundle.candidate_context.columns
    assert bundle.summary["candidate_count"] == 0
    assert bundle.summary["all_stage4b2_creation_entities_preserved"] is True
    assert bundle.comparison["status"] == "INCONCLUSIVE_NO_TRAINING_OR_EVALUATION_CASES"


def test_experiment_prefix_chains_and_asof_context_are_invariant_to_future_append():
    full = _market(240)
    short = full.iloc[:180].copy(deep=True)
    full_n, full_t, full_a, full_fvg, full_vol, full_htf = _build_surfaces(full, timeline_id="same-timeline-label")
    short_n, short_t, short_a, short_fvg, short_vol, short_htf = _build_surfaces(short, timeline_id="same-timeline-label")
    cutoff = "2026-05-01T02:15:00Z"
    full_bundle = build_experiment_from_surfaces(
        market_history=full_n,
        timeline=full_t,
        adapter=full_a,
        source_identity=_identity(),
        source_file_sha256="b" * 64,
        fvg_surface=full_fvg,
        volatility_surface=full_vol,
        htf_surface=full_htf,
        development_cutoff_utc=cutoff,
    )
    short_bundle = build_experiment_from_surfaces(
        market_history=short_n,
        timeline=short_t,
        adapter=short_a,
        source_identity=_identity(),
        source_file_sha256="c" * 64,
        fvg_surface=short_fvg,
        volatility_surface=short_vol,
        htf_surface=short_htf,
        development_cutoff_utc=cutoff,
    )
    full_rows = full_bundle.candidate_context.set_index("candidate_id")
    short_rows = short_bundle.candidate_context.set_index("candidate_id")
    common = sorted(set(full_rows.index) & set(short_rows.index))
    common = [
        candidate_id
        for candidate_id in common
        if int(full_rows.loc[candidate_id, "creation_position"]) < 120
    ]
    assert common
    chain_columns = (
        "market_prefix_chain_sha256",
        "fvg_creation_prefix_chain_sha256",
        "s1_prefix_chain_sha256",
        "stage4a_prefix_chain_sha256",
        "stage4c_prefix_chain_sha256",
        "candidate_context_sha256",
    )
    feature_columns = list(M1_FEATURES)
    for candidate_id in common:
        pd.testing.assert_series_equal(
            full_rows.loc[candidate_id, list(chain_columns)],
            short_rows.loc[candidate_id, list(chain_columns)],
            check_names=False,
        )
        pd.testing.assert_series_equal(
            full_rows.loc[candidate_id, feature_columns],
            short_rows.loc[candidate_id, feature_columns],
            check_names=False,
        )
    assert full_t.timeline_hash != short_t.timeline_hash
    assert full_fvg.surface_id != short_fvg.surface_id
    assert full_rows.loc[common[0], "source_file_sha256"] != short_rows.loc[common[0], "source_file_sha256"]


def _query_case(market: pd.DataFrame, *, decision_position: int, end_position: int | None = None, future_time: pd.Timestamp | None = None):
    normalized = market.copy(deep=True)
    normalized.index = normalized.index.tz_convert("UTC").as_unit("ns")
    adapter = TimeIndexedTimelineAdapter("trajectory-parity")
    timeline = MarketObservationTimeline.seal(adapter=adapter, market_history=normalized)
    decision_key = adapter.key_for_position(
        normalized.index,
        decision_position,
        InformationPhase.COMPLETED_ROW_AVAILABLE,
    )
    case = create_trajectory_decision_case(
        timeline=timeline,
        adapter=adapter,
        market_history=normalized,
        decision_key=decision_key,
        surfaces=(),
        parent_snapshot=None,
    )
    if end_position is not None:
        end_key = adapter.key_for_position(
            normalized.index,
            end_position,
            InformationPhase.COMPLETED_ROW_AVAILABLE,
        )
    else:
        end_key = InformationKey(
            information_key_version=INFORMATION_KEY_VERSION,
            timeline_id=adapter.timeline_id,
            bar_position=len(normalized),
            event_time_utc=future_time,
            information_phase=InformationPhase.COMPLETED_ROW_AVAILABLE,
            deterministic_sequence=0,
        )
    horizon = HorizonRequest(
        policy_identity=HorizonPolicyIdentity(
            policy_id="TEST_EXACT_ONE_HOUR",
            policy_version="V1",
            policy_sha256=hashlib.sha256(b"test horizon").hexdigest(),
        ),
        requested_end_key=end_key,
    )
    coverage = CoverageContract(
        contract_id="TEST_1M_COVERAGE",
        contract_version="V1",
        contract_sha256=hashlib.sha256(b"test coverage").hexdigest(),
        expected_step=pd.Timedelta(minutes=1),
    )
    return normalized, timeline, adapter, case, horizon, coverage


def _assert_batch_public_excursion_parity(
    market: pd.DataFrame,
    *,
    decision_position: int,
    end_position: int | None = None,
    future_time: pd.Timestamp | None = None,
    candidate_id: str = "query-candidate",
):
    normalized, timeline, adapter, case, horizon, coverage = _query_case(
        market,
        decision_position=decision_position,
        end_position=end_position,
        future_time=future_time,
    )
    window = build_trajectory_window(
        case=case,
        timeline=timeline,
        adapter=adapter,
        market_history=normalized,
        horizon_request=horizon,
        coverage_contract=coverage,
    )
    view = derive_excursion_view(
        window=window,
        reference=decision_close_excursion_reference(window),
    )
    batch = _outcome_rows(
        pd.DataFrame(
            [{"candidate_id": candidate_id, "creation_position": decision_position}]
        ),
        normalized,
        adapter=adapter,
        horizon_policy_hash=hashlib.sha256(b"batch protocol").hexdigest(),
    ).iloc[0]
    assert batch["coverage_assessment"] == view.coverage_assessment.value
    assert batch["censoring_state"] == view.censoring_state.value
    assert batch["horizon_completion"] == view.horizon_completion.value
    assert batch["observed_max_high"] == view.observed_max_high
    assert batch["observed_min_low"] == view.observed_min_low
    assert batch["observed_high_delta_from_creation_close"] == view.observed_high_delta_from_reference
    assert batch["observed_low_delta_from_creation_close"] == view.observed_low_delta_from_reference
    assert batch["max_high_position"] == view.max_high_position
    assert batch["min_low_position"] == view.min_low_position
    assert batch["actual_end_position"] == (
        None
        if window.reference.actual_end_key is None
        else window.reference.actual_end_key.bar_position
    )
    return batch, view


def test_batch_excursion_matches_public_trajectory_excursion_view():
    complete, complete_view = _assert_batch_public_excursion_parity(
        _market(),
        decision_position=3,
        end_position=63,
    )
    assert complete["path_status"] == "HORIZON_BOUNDARY_OBSERVED"
    assert complete_view.censoring_state is CensoringState.OBSERVED_TO_REQUESTED_END

    full_market = _market()
    gapped_market = full_market.drop(full_market.index[30 + 25]).copy(deep=True)
    gapped_market.index = gapped_market.index.tz_convert("UTC").as_unit("ns")
    gap_boundary = gapped_market.index[30] + HORIZON
    gap_end_position = int(gapped_market.index.get_loc(gap_boundary))
    gapped, gapped_view = _assert_batch_public_excursion_parity(
        gapped_market,
        decision_position=30,
        end_position=gap_end_position,
        candidate_id="gap-parity",
    )
    assert gapped["path_status"] == "HORIZON_BOUNDARY_OBSERVED"
    assert gapped_view.coverage_assessment is CoverageAssessment.GAPS_OR_CADENCE_DEVIATION

    final, final_view = _assert_batch_public_excursion_parity(
        _market(240),
        decision_position=179,
        end_position=239,
        candidate_id="final-boundary-parity",
    )
    assert final["horizon_completion"] == "COMPLETE"
    assert final_view.censoring_state is CensoringState.RIGHT_CENSORED

    partial_market = _market(240)
    partial = _assert_batch_public_excursion_parity(
        partial_market,
        decision_position=230,
        future_time=partial_market.index[230] + HORIZON,
        candidate_id="dataset-end-parity",
    )[0]
    assert partial["path_status"] == "RIGHT_CENSORED_AT_DATASET_END"
    assert partial["path_row_count"] == 9


def test_in_range_missing_horizon_boundary_is_not_approximated_and_public_key_validation_rejects_it():
    full = _market(240)
    decision_position = 30
    missing_target_position = decision_position + 60
    gapped = full.drop(full.index[missing_target_position])
    # The experiment's new timeline uses the gapped observed rows, not a synthetic bar.
    normalized = gapped.copy(deep=True)
    normalized.index = normalized.index.tz_convert("UTC").as_unit("ns")
    adapter = TimeIndexedTimelineAdapter("missing-boundary")
    timeline = MarketObservationTimeline.seal(adapter=adapter, market_history=normalized)
    output = _outcome_rows(
        pd.DataFrame([{"candidate_id": "missing-boundary-candidate", "creation_position": decision_position}]),
        normalized,
        adapter=adapter,
        horizon_policy_hash=hashlib.sha256(b"missing boundary").hexdigest(),
    ).iloc[0]
    assert output["path_status"] == "IN_RANGE_BOUNDARY_UNOBSERVED"
    assert output["requested_end_key_state"] == "IN_RANGE_TIMESTAMP_ABSENT_NO_KEY"
    assert pd.isna(output["requested_end_bar_position"])
    assert bool(output["scoreable_under_frozen_protocol"]) is False
    assert pd.Timestamp(output["actual_end_time_utc"]) < pd.Timestamp(output["requested_horizon_end_utc"])

    decision_key = adapter.key_for_position(normalized.index, decision_position, InformationPhase.COMPLETED_ROW_AVAILABLE)
    case = create_trajectory_decision_case(
        timeline=timeline,
        adapter=adapter,
        market_history=normalized,
        decision_key=decision_key,
        surfaces=(),
        parent_snapshot=None,
    )
    insertion = missing_target_position
    missing_boundary = InformationKey(
        information_key_version=INFORMATION_KEY_VERSION,
        timeline_id=adapter.timeline_id,
        bar_position=insertion,
        event_time_utc=pd.Timestamp(full.index[missing_target_position]).tz_convert("UTC").as_unit("ns"),
        information_phase=InformationPhase.COMPLETED_ROW_AVAILABLE,
        deterministic_sequence=0,
    )
    horizon = HorizonRequest(
        policy_identity=HorizonPolicyIdentity("TEST", "V1", hashlib.sha256(b"test").hexdigest()),
        requested_end_key=missing_boundary,
    )
    coverage = CoverageContract("TEST", "V1", hashlib.sha256(b"coverage").hexdigest(), pd.Timedelta(minutes=1))
    with pytest.raises(Exception, match="requested end key is unavailable"):
        build_trajectory_window(
            case=case,
            timeline=timeline,
            adapter=adapter,
            market_history=normalized,
            horizon_request=horizon,
            coverage_contract=coverage,
        )


def test_gap_censoring_and_final_source_row_follow_explicit_states():
    full = _market(240)
    decision_position = 30
    gap_market = full.drop(full.index[decision_position + 25])
    gap_market = gap_market.copy(deep=True)
    gap_market.index = gap_market.index.tz_convert("UTC").as_unit("ns")
    gap_adapter = TimeIndexedTimelineAdapter("gap-window")
    gap_row = _outcome_rows(
        pd.DataFrame([{"candidate_id": "gap", "creation_position": decision_position}]),
        gap_market,
        adapter=gap_adapter,
        horizon_policy_hash=hashlib.sha256(b"gap").hexdigest(),
    ).iloc[0]
    assert gap_row["path_status"] == "HORIZON_BOUNDARY_OBSERVED"
    assert gap_row["coverage_assessment"] == CoverageAssessment.GAPS_OR_CADENCE_DEVIATION.value
    assert bool(gap_row["scoreable_under_frozen_protocol"]) is False
    assert gap_row["model_target_state"] == "NOT_SCOREABLE_COVERAGE_GAPS_OR_CADENCE_DEVIATION"
    assert json.loads(gap_row["coverage_issues_json"])

    contiguous = _market(240)
    contiguous.index = contiguous.index.tz_convert("UTC").as_unit("ns")
    adapter = TimeIndexedTimelineAdapter("final-row")
    final_boundary = _outcome_rows(
        pd.DataFrame([{"candidate_id": "final-boundary", "creation_position": 179}]),
        contiguous,
        adapter=adapter,
        horizon_policy_hash=hashlib.sha256(b"final").hexdigest(),
    ).iloc[0]
    assert final_boundary["path_status"] == "HORIZON_BOUNDARY_OBSERVED"
    assert final_boundary["horizon_completion"] == "COMPLETE"
    assert final_boundary["censoring_state"] == CensoringState.RIGHT_CENSORED.value
    assert bool(final_boundary["scoreable_under_frozen_protocol"]) is False

    right_censored = _outcome_rows(
        pd.DataFrame([{"candidate_id": "right", "creation_position": 230}]),
        contiguous,
        adapter=adapter,
        horizon_policy_hash=hashlib.sha256(b"right").hexdigest(),
    ).iloc[0]
    assert right_censored["path_status"] == "RIGHT_CENSORED_AT_DATASET_END"
    assert right_censored["censoring_state"] == CensoringState.RIGHT_CENSORED.value
    assert right_censored["path_row_count"] == 9
    assert pd.isna(right_censored["high_excursion_fraction"])

    no_post_rows = _outcome_rows(
        pd.DataFrame([{"candidate_id": "no-post", "creation_position": 239}]),
        contiguous,
        adapter=adapter,
        horizon_policy_hash=hashlib.sha256(b"no-post").hexdigest(),
    ).iloc[0]
    assert no_post_rows["path_row_count"] == 0
    assert no_post_rows["observed_value_state"] == "NO_POST_DECISION_ROWS"
    assert no_post_rows["model_target_state"] == "NO_POST_DECISION_ROWS"


def test_ols_uses_same_candidate_ids_and_reports_rank_deficiency_without_inference():
    rng = np.random.default_rng(19)
    train_count, evaluation_count = 90, 25
    total = train_count + evaluation_count
    start = pd.Timestamp("2026-05-01T00:00:00Z")
    cutoff = start + pd.Timedelta(hours=2 * train_count)
    candidate_rows = []
    outcome_rows = []
    for position in range(total):
        timestamp = (
            cutoff - pd.Timedelta(minutes=30)
            if position == train_count - 1
            else start + pd.Timedelta(hours=2 * position)
        )
        candidate_id = f"c{position:04d}"
        candidate = {
            "candidate_id": candidate_id,
            "creation_time_utc": timestamp.isoformat().replace("+00:00", "Z"),
        }
        for feature in M1_FEATURES:
            candidate[feature] = float(rng.normal())
            candidate[f"{feature}__state"] = "AVAILABLE"
        candidate_rows.append(candidate)
        value_a = float(rng.normal())
        value_b = float(rng.normal())
        outcome_rows.append(
            {
                "candidate_id": candidate_id,
                "decision_position": position * 120,
                "actual_end_position": position * 120 + 60,
                "requested_horizon_end_utc": (timestamp + HORIZON).isoformat().replace("+00:00", "Z"),
                "scoreable_under_frozen_protocol": True,
                "high_excursion_fraction": value_a,
                "low_excursion_fraction": value_b,
            }
        )
    result = _fit_comparison(pd.DataFrame(candidate_rows), pd.DataFrame(outcome_rows), cutoff=cutoff)
    assert result["status"] == "DESCRIPTIVE_TEMPORAL_COMPARISON_NOT_INDEPENDENT"
    assert result["training_candidate_count"] == train_count - 1
    assert result["evaluation_candidate_count"] == evaluation_count
    assert result["same_m0_m1_case_set"] is True
    assert result["overlap"]["training"]["overlapping_interval_pair_count"] == 0
    assert result["overlap"]["evaluation"]["overlapping_interval_pair_count"] == 0
    assert result["overlap"]["all_model_cases"]["overlapping_interval_pair_count"] == 0
    for target in result["target_comparison"].values():
        assert target["status"] == "DESCRIPTIVE_RMSE_AVAILABLE_NOT_INFERENTIAL"
        assert target["M0_RMSE"] is not None
        assert target["M1_RMSE"] is not None
    assert "standard errors" in result["inference"].lower()

    deficient_candidates = pd.DataFrame(candidate_rows)
    for feature in M1_FEATURES:
        deficient_candidates[feature] = 1.0
    deficient = _fit_comparison(
        deficient_candidates,
        pd.DataFrame(outcome_rows),
        cutoff=cutoff,
    )
    assert deficient["status"] == "INCONCLUSIVE_ONE_OR_MORE_MODEL_DESIGNS"
    for target in deficient["target_comparison"].values():
        assert target["status"] == "INCONCLUSIVE_MODEL_FIT"
        assert target["M0"]["status"] == "INCONCLUSIVE_RANK_OR_SAMPLE_DEFICIENT"
        assert target["M1"]["status"] == "INCONCLUSIVE_RANK_OR_SAMPLE_DEFICIENT"


def test_overlap_accounting_counts_shared_observed_rows_without_iid_claim():
    outcomes = pd.DataFrame(
        [
            {"candidate_id": "a", "decision_position": 0, "actual_end_position": 60},
            {"candidate_id": "b", "decision_position": 30, "actual_end_position": 90},
            {"candidate_id": "c", "decision_position": 60, "actual_end_position": 120},
            {"candidate_id": "d", "decision_position": 120, "actual_end_position": 150},
        ]
    )
    summary = _overlap_summary(outcomes, {"a", "b", "c", "d"})
    assert summary["overlapping_interval_pair_count"] == 2
    assert summary["candidate_count_with_any_observed_path_overlap"] == 3
    assert summary["max_concurrent_observed_path_intervals"] == 2
    assert summary["independence_claim"].startswith("NONE")


def test_surface_timeline_mismatch_fails_closed():
    market = _market()
    normalized, timeline, adapter, fvg, volatility, htf = _build_surfaces(market, timeline_id="correct")
    foreign_adapter = TimeIndexedTimelineAdapter("foreign")
    foreign_timeline = MarketObservationTimeline.seal(adapter=foreign_adapter, market_history=normalized)
    with pytest.raises(MovementContextExperimentError, match="surface/timeline identity mismatch"):
        build_experiment_from_surfaces(
            market_history=normalized,
            timeline=foreign_timeline,
            adapter=foreign_adapter,
            source_identity=_identity(),
            source_file_sha256="a" * 64,
            fvg_surface=fvg,
            volatility_surface=volatility,
            htf_surface=htf,
            development_cutoff_utc="2026-05-01T02:00:00Z",
        )


def test_htf_surface_with_non_frozen_cadence_identity_is_rejected():
    market = _market()
    normalized, timeline, adapter, fvg, volatility, _ = _build_surfaces(market)
    alternate_cadence = s4c.CadenceGridContract(
        grid_epoch_utc=pd.Timestamp("1970-01-01T00:01:00Z"),
        period=pd.Timedelta(minutes=1),
    )
    alternate_htf = s4c.build_htf_scale_surface(
        timeline=timeline,
        adapter=adapter,
        market_history=normalized,
        scale_spec=s4c.HtfScaleSpec("H1", pd.Timedelta(hours=1)),
        cadence=alternate_cadence,
    )
    with pytest.raises(
        MovementContextExperimentError,
        match="frozen completed raw H1 and one-minute cadence contracts",
    ):
        build_experiment_from_surfaces(
            market_history=normalized,
            timeline=timeline,
            adapter=adapter,
            source_identity=_identity(),
            source_file_sha256="a" * 64,
            fvg_surface=fvg,
            volatility_surface=volatility,
            htf_surface=alternate_htf,
            development_cutoff_utc="2026-05-01T02:00:00Z",
        )


def test_outputs_are_external_reproducible_and_refuse_overwrite(tmp_path):
    market = _market()
    bundle = _bundle_for(market)
    wrong_market = market.copy(deep=True)
    wrong_market.iloc[0, wrong_market.columns.get_loc("volume")] += 1.0
    wrong_output = tmp_path / "wrong-market"
    with pytest.raises(MovementContextExperimentError, match="does not match the sealed experiment timeline"):
        write_outputs(bundle, market_history=wrong_market, output_dir=wrong_output)
    assert not wrong_output.exists()

    output = tmp_path / "research-output"
    write_outputs(bundle, market_history=market, output_dir=output)
    expected = {
        "candidate_context.csv",
        "excursion_outcomes.csv",
        "observed_paths.csv",
        "protocol.json",
        "comparison.json",
        "summary.json",
        "OUTPUT_MANIFEST.sha256",
    }
    assert expected == {path.name for path in output.iterdir()}
    manifest_lines = (output / "OUTPUT_MANIFEST.sha256").read_text(encoding="utf-8").splitlines()
    assert len(manifest_lines) == 6
    for line in manifest_lines:
        digest, filename = line.split("  ", 1)
        assert hashlib.sha256((output / filename).read_bytes()).hexdigest() == digest

    second_output = tmp_path / "research-output-repeat"
    second_bundle = _bundle_for(market)
    write_outputs(second_bundle, market_history=market, output_dir=second_output)
    assert (second_output / "OUTPUT_MANIFEST.sha256").read_bytes() == (
        output / "OUTPUT_MANIFEST.sha256"
    ).read_bytes()

    with pytest.raises(MovementContextExperimentError, match="refusing to overwrite"):
        write_outputs(bundle, market_history=market, output_dir=output)


def test_offline_binance_csv_entrypoint_records_adapter_validation_without_authenticating_origin(tmp_path):
    market = _market(240)
    csv_path = tmp_path / "synthetic-binance-klines.csv"
    lines = []
    for close_time, row in market.iterrows():
        open_time_us = (pd.Timestamp(close_time).value - int(pd.Timedelta(minutes=1).value)) // 1000
        close_time_us = open_time_us + 60_000_000 - 1
        lines.append(
            ",".join(
                (
                    str(open_time_us),
                    f"{float(row['open']):.8f}",
                    f"{float(row['high']):.8f}",
                    f"{float(row['low']):.8f}",
                    f"{float(row['close']):.8f}",
                    "10.00000000",
                    str(close_time_us),
                    "1000.00000000",
                    "1",
                    "5.00000000",
                    "500.00000000",
                    "0",
                )
            )
        )
    csv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    output = tmp_path / "offline-cli-output"
    bundle = run_from_binance_csv(
        csv_path=csv_path,
        identity=_identity(),
        development_cutoff_utc="2026-05-01T02:00:00Z",
        output_dir=output,
    )
    validation = bundle.summary["source"]["source_validation"]
    assert validation["state"] == (
        "BINANCE_KLINE_SCHEMA_AND_DECLARED_PERIOD_VALIDATED_NOT_ORIGIN_AUTHENTICATED"
    )
    assert validation["source_rows"] == len(market)
    assert validation["period_coverage"]["missing_expected_minute_count"] == 0
    assert validation["source_origin_authenticated"] is False
    assert (output / "OUTPUT_MANIFEST.sha256").exists()
