"""Focused software-contract tests for the offline movement research adapter.

All OHLC, policy values, authorization references, and S5 identities here are
synthetic fixtures. The fixture policy values are reused from existing S5 and
Stage4B1 tests; they are not owner policies or market evidence.
"""
from __future__ import annotations

import json

import pandas as pd
import pytest

from trading_system.market_understanding.availability import InformationAxis
from trading_system.market_understanding.contracts import SchemaIdentity
from trading_system.market_understanding.detector_witness import (
    DetectorPolicyWitnessSpec,
    adapt_detector_witness_stream,
    query_witness_surface_as_of,
    verify_prefix_witness_invariance,
)
from trading_system.market_understanding.price_path import PublishedOhlcBarFact
from trading_system.market_understanding.policy_governance import (
    DATASET_ROLE_DEVELOPMENT_FIT,
    PROVENANCE_PREDEFINED_CONTRACT,
    DatasetIdentityArtifact,
    DatasetRoleArtifact,
    PolicyArtifact,
)
from trading_system.market_understanding.wave_representation import (
    CandidateWaveRepresentationSpec,
    FAMILY_ALPHA_POLICY_SCALE,
    query_wave_representation_as_of,
    verify_wave_prefix_invariance,
)
from trading_system.research.hashing import canonical_sha256
from trading_system.research.information_time import InformationPhase, TimeIndexedTimelineAdapter
from trading_system.research.trajectory.causal_market_context_core import (
    ReplayLimits,
    SwingPolicyConfig,
    build_causal_market_context_core,
)
from trading_system.research.trajectory.market_movement_representation_research import (
    BLOCKED_MISSING_AUTHORIZED_POLICY,
    DeclaredSwingPolicy,
    S5RepresentationPlan,
    SUITABILITY_NOT_ESTABLISHED,
    run_market_movement_representation_research,
    verify_replay_prefix_invariance,
)
from trading_system.sources import SourceArtifactIdentity
from trading_system.structure.swing_detector import EmpiricalConfirmationPolicy


CALLER_SOURCE = SchemaIdentity("CALLER_SUPPLIED_OHLC", "CALLER_FRAME_V1")
TIMELINE = "synthetic-movement-research-test"


def _identity(end: str = "2026-05-01T04:00:00Z") -> SourceArtifactIdentity:
    return SourceArtifactIdentity("BTCUSDT", "SPOT", "1m", "2026-05-01T00:00:00Z", end)


def _simple_market() -> pd.DataFrame:
    # Same synthetic software fixture used by test_causal_market_context_core.
    index = pd.date_range("2026-05-01T00:01:00Z", periods=6, freq="min")
    return pd.DataFrame(
        {
            "open": [100, 102, 104, 106, 107, 103],
            "high": [102, 103, 106, 108, 109, 105],
            "low": [99, 101, 103, 102.5, 101, 100],
            "close": [101, 102.5, 105, 107, 102, 101],
            "volume": [100, 120, 110, 90, 95, 80],
        },
        index=index,
    )


def _zigzag_market() -> pd.DataFrame:
    # OHLC sequence copied from the existing S5 software-test fixture, not a
    # market pattern claim. It provides multiple confirmed swings for contracts.
    pairs = [
        (10.0, 9.0),
        (12.0, 11.0),
        (14.0, 13.0),
        (11.0, 10.0),
        (9.0, 8.0),
        (11.5, 10.5),
        (14.5, 13.5),
        (11.0, 10.0),
        (8.5, 7.5),
        (12.0, 11.0),
    ]
    index = pd.date_range("2026-05-01T00:01:00Z", periods=len(pairs), freq="min")
    mid = [(high + low) / 2.0 for high, low in pairs]
    return pd.DataFrame(
        {
            "open": mid,
            "high": [high for high, _ in pairs],
            "low": [low for _, low in pairs],
            "close": mid,
            "volume": [1.0] * len(pairs),
        },
        index=index,
    )


def _rich_market(rows: int = 70) -> pd.DataFrame:
    # Reuses the fixed rise/pullback shape from existing Stage4B1/4B2 test
    # fixtures; it is synthetic test input only.
    close, high, low = [], [], []
    level = 100.0
    position = 0
    while position < rows:
        for _ in range(4):
            if position >= rows:
                break
            level += 5.0
            close.append(level)
            high.append(level + 1.0)
            low.append(level - 1.0)
            position += 1
        for _ in range(3):
            if position >= rows:
                break
            level -= 3.0
            close.append(level)
            high.append(level + 1.0)
            low.append(level - 1.0)
            position += 1
    index = pd.date_range("2026-05-01T00:01:00Z", periods=rows, freq="min")
    return pd.DataFrame(
        {"open": close, "high": high, "low": low, "close": close, "volume": [2.0] * rows},
        index=index,
    )


def _downstream_market(rows: int = 90) -> pd.DataFrame:
    # Reuses the existing Stage4B2 test sequence: step/decline, then a terminal
    # collapse. Synthetic producer-coverage fixture only.
    opens, closes = [], []
    level = 100.0
    for position in range(rows):
        opening = level
        closing = level + 5.0 if position < 65 and position % 7 < 4 else level - (3.0 if position < 65 else 6.0)
        opens.append(opening)
        closes.append(closing)
        level = closing
    index = pd.date_range("2026-05-01T00:01:00Z", periods=rows, freq="min")
    return pd.DataFrame(
        {"open": opens, "close": closes, "high": [max(o, c) + 1.0 for o, c in zip(opens, closes)], "low": [min(o, c) - 1.0 for o, c in zip(opens, closes)], "volume": [2.0] * rows},
        index=index,
    )


def _test_policy_a() -> EmpiricalConfirmationPolicy:
    # Existing Stage4B1 fixture policy: explicit and synthetic, never used by CLI.
    priors = tuple(0.01 * value for value in range(1, 50))
    return EmpiricalConfirmationPolicy(quantile=0.1, prior_continuation_reversals=priors)


def _test_policy_b() -> EmpiricalConfirmationPolicy:
    # Existing Stage3 competing-policy test value, paired with the Stage4B1
    # synthetic prior fixture above. Not an owner-selected threshold.
    priors = tuple(0.01 * value for value in range(1, 50))
    return EmpiricalConfirmationPolicy(quantile=0.95, prior_continuation_reversals=priors)


def _declarations() -> tuple[DeclaredSwingPolicy, DeclaredSwingPolicy]:
    return (
        DeclaredSwingPolicy(
            SwingPolicyConfig("synthetic-policy-a", _test_policy_a()),
            "synthetic-test-only-auth-ref-a",
        ),
        DeclaredSwingPolicy(
            SwingPolicyConfig("synthetic-policy-b", _test_policy_b()),
            "synthetic-test-only-auth-ref-b",
        ),
    )


def _run(frame: pd.DataFrame, *, policies=(), s5_plans=(), timeline: str = TIMELINE, limits=None, output_dir=None, measure_python_allocations=False):
    identity = _identity("2026-05-01T04:00:00Z")
    return run_market_movement_representation_research(
        market_history=frame,
        source_identity=identity,
        timeline_id=timeline,
        swing_policies=policies,
        s5_plans=s5_plans,
        replay_limits=limits or ReplayLimits(),
        output_dir=output_dir,
        measure_python_allocations=measure_python_allocations,
    )


def _s5_plan(frame: pd.DataFrame, *, wrong_witness_ref: bool = False, wrong_content_hash: bool = False) -> S5RepresentationPlan:
    policy = EmpiricalConfirmationPolicy(
        quantile=0.25,
        prior_continuation_reversals=(0.01, 0.02),
    )
    timeline = "synthetic-s5-movement-test"
    adapter = TimeIndexedTimelineAdapter(timeline)
    start_key = adapter.key_for_position(frame.index, 0, InformationPhase.COMPLETED_ROW_AVAILABLE, 0)
    end_key = adapter.key_for_position(frame.index, len(frame) - 1, InformationPhase.COMPLETED_ROW_AVAILABLE, 0)
    normalized_frame = frame.copy(deep=True)
    normalized_frame.index = normalized_frame.index.tz_convert("UTC").as_unit("ns")
    dataset_content_hash = canonical_sha256(domain="CORE_CALLER_FRAME_HASH_V1", payload=normalized_frame)
    if wrong_content_hash:
        dataset_content_hash = "f" * 64
    dataset = DatasetIdentityArtifact.create(
        dataset_id="DS-SYNTHETIC-S5-MOVEMENT-TEST",
        content_hash=dataset_content_hash,
        source_identity=CALLER_SOURCE,
        timeline_id=timeline,
        start_key=start_key,
        end_key=end_key,
        transformation_spec_hash="synthetic-transform-contract",
        parent_dataset_ids=(),
        creation_code_hash="synthetic-test-code-ref",
        semantic_schema_hash="synthetic-ohcl-schema-ref",
    )
    role = DatasetRoleArtifact.create(
        dataset_identity=dataset,
        role=DATASET_ROLE_DEVELOPMENT_FIT,
        role_assignment_key=start_key,
        permitted_operations=("CANDIDATE_WAVE_CONSTRUCTION",),
        prohibited_operations=("FINAL_LOCKED_CLAIM",),
        owner_authorization_ref="synthetic-test-only-role-auth",
    )
    spec = CandidateWaveRepresentationSpec.create(
        representation_id="synthetic-alpha-representation",
        family_kind=FAMILY_ALPHA_POLICY_SCALE,
        scope_timeline_id=timeline,
        scope_axis=InformationAxis.TIME_INDEXED,
        intrinsic_scale_key="synthetic-owner-scale-reference",
        identity_rule_ref="synthetic-owner-identity-rule-reference",
    )
    witness_ref = DetectorPolicyWitnessSpec.from_policy(policy).spec_identity
    artifact = PolicyArtifact.create(
        policy_id="synthetic-s5-authority",
        detector_policy_witness_ref="deliberately-wrong-witness" if wrong_witness_ref else witness_ref,
        scope_timeline_id=timeline,
        scope_axis=InformationAxis.TIME_INDEXED,
        scope_representation_id=spec.representation_id,
        calibration_provenance_kind=PROVENANCE_PREDEFINED_CONTRACT,
        reproduction_recipe_hash="synthetic-recipe-reference",
        effective_from_key=start_key,
        owner_authorization_ref="synthetic-test-only-policy-auth",
    )
    return S5RepresentationPlan(
        representation_spec=spec,
        policy_artifact=artifact,
        confirmation_policy=policy,
        dataset_identity=dataset,
        dataset_role=role,
        recomputed_recipe_hash="synthetic-recipe-reference",
    )


def test_missing_swing_policy_is_explicit_and_fvg_remains_available() -> None:
    result = _run(_simple_market())

    assert result.report["available_views"]["S1_PRICE_PATH"]["state"] == "AVAILABLE"
    assert result.report["available_views"]["STAGE4B1"]["state"] == BLOCKED_MISSING_AUTHORIZED_POLICY
    assert result.report["available_views"]["STAGE4B2_FVG"]["policy_dependence"] == "STRUCTURE_INDEPENDENT"
    assert result.report["available_views"]["S5_WAVE_REPRESENTATION"]["state"] == BLOCKED_MISSING_AUTHORIZED_POLICY
    assert {row["status"] for row in result.report["policy_candidates"]["s5_families"]} == {BLOCKED_MISSING_AUTHORIZED_POLICY}
    assert result.report["coverage"]["candidate_universe_pruned"] is False


def test_prefix_replay_and_s2_asof_witness_invariance() -> None:
    frame = _rich_market(70)
    policies = (_declarations()[0],)
    full = _run(frame, policies=policies)
    prefix = _run(frame.iloc[:45].copy(), policies=policies)

    assert verify_replay_prefix_invariance(full_bundle=full.core_bundle, prefix_bundle=prefix.core_bundle)
    policy_ref = next(iter(full.witness_bundles))
    full_witness = full.witness_bundles[policy_ref]
    prefix_witness = prefix.witness_bundles[policy_ref]
    at_key = full.core_bundle.adapter.key_for_position(
        full.core_bundle.market.index, 44, InformationPhase.COMPLETED_ROW_AVAILABLE, 0
    )
    assert verify_prefix_witness_invariance(prefix_witness, full_witness, at_key=at_key)


def test_turning_point_origin_is_not_availability_and_asof_query_is_strict() -> None:
    result = _run(_rich_market(70), policies=(_declarations()[0],))
    records = [
        record for record in result.turning_point_records
        if record["record_type"] == "STAGE4B1_CONFIRMED_SWING_WITNESS_VIEW"
    ]
    assert result.report["causal_turning_points"]["record_count"] == len(result.turning_point_records)
    assert records
    record = records[0]
    assert record["origin_position"] < record["confirmation_position"]
    assert record["availability_key"]["bar_position"] == record["confirmation_position"]
    assert record["authority_status"] == "WITNESS_ONLY_NOT_MUF_AUTHORITATIVE"

    witness = next(iter(result.witness_bundles.values()))
    event = witness.swing_event_witnesses[0]
    emitted_s2 = [
        row for row in result.turning_point_records
        if row["record_type"] == "S2_SWING_EVENT_WITNESS_RECORD"
        and row["consumer_scope"] == "CMC_STAGE4B1_POLICY_VIEW"
    ]
    s2_row = next(row for row in emitted_s2 if row["record_identity"] == event.record_identity)
    assert s2_row["availability_key"]["bar_position"] == event.confirmation_position
    assert s2_row["origin_key"]["bar_position"] == event.origin_position

    prior_key = result.core_bundle.adapter.key_for_position(
        result.core_bundle.market.index,
        event.confirmation_position - 1,
        InformationPhase.COMPLETED_ROW_AVAILABLE,
        0,
    )
    at_confirmation = result.core_bundle.adapter.key_for_position(
        result.core_bundle.market.index,
        event.confirmation_position,
        InformationPhase.COMPLETED_ROW_AVAILABLE,
        0,
    )
    assert all(item.record_identity != event.record_identity for item in query_witness_surface_as_of(witness, at_key=prior_key).swing_event_witnesses)
    assert any(item.record_identity == event.record_identity for item in query_witness_surface_as_of(witness, at_key=at_confirmation).swing_event_witnesses)


def test_competing_policy_views_separate_geometric_operational_and_availability_differences() -> None:
    result = _run(_rich_market(70), policies=_declarations())
    pairs = result.report["disagreements"]["geometric"]["stage4b1_policy_pairs"]

    assert len(pairs) == 1
    assert pairs[0]["left_representation_id"] != pairs[0]["right_representation_id"]
    all_categories = result.report["disagreements"]
    assert len(all_categories["operational_definition"]["stage4b1_policy_pairs"]) == 1
    assert len(all_categories["information_availability"]["stage4b1_policy_pairs"]) == 1
    assert all_categories["task_relevant"]["state"] == "NOT_ASSESSED_MISSING_TASK_AND_OUTCOME_AUTHORITY"
    assert all_categories["no_universal_winner_selected"] is True


def test_downstream_disagreement_references_are_actual_core_producer_ids() -> None:
    result = _run(_downstream_market(90), policies=_declarations())
    counts = result.report["affected_downstream_references"]["candidate_counts_by_domain_representation"]
    assert any(key.startswith("STAGE4B1_CONFIRMED_SWING:") for key in counts)
    assert any(key.startswith("LIQUIDITY:") for key in counts)
    assert any(key.startswith("ORDER_BLOCK:") for key in counts)
    assert "FVG:REP-STRUCTURE-INDEPENDENT-FVG" in counts
    assert result.replay.summary.disagreement_count > 0
    assert result.disagreement_reference_rows
    assert result.report["affected_downstream_references"]["references_are_emitted_producer_record_ids_only"] is True
    for row in result.disagreement_reference_rows:
        assert row["boundary_record_identity"].startswith("BOUNDARY-")
        assert all(item.startswith("DIFF-") for item in row["representation_disagreement_ids"])


def test_s5_requires_matching_policy_identity_and_never_fabricates_authority() -> None:
    frame = _zigzag_market()
    plan = _s5_plan(frame, wrong_witness_ref=True)
    result = _run(frame, timeline="synthetic-s5-movement-test", s5_plans=(plan,))

    assert result.s5_bundles == {}
    assert result.s5_blocked[0]["status"] == "BLOCKED_POLICY_MISMATCH"
    assert result.report["available_views"]["S5_WAVE_REPRESENTATION"]["state"] == "BLOCKED_POLICY_MISMATCH"
    assert result.report["suitability"]["overall"] == SUITABILITY_NOT_ESTABLISHED
    assert result.report["suitability"]["winner_or_recommendation"] is None
    assert result.report["replay"]["evaluation_state"] == "NOT_ESTABLISHED_MISSING_TASK_AUTHORITY"
    assert not any("signal" in key.lower() or "pnl" in key.lower() for key in result.report)


def test_s5_dataset_hash_mismatch_blocks_plan_before_its_policy_is_reused() -> None:
    frame = _zigzag_market()
    plan = _s5_plan(frame, wrong_content_hash=True)
    result = _run(frame, timeline="synthetic-s5-movement-test", s5_plans=(plan,))

    assert result.s5_bundles == {}
    assert result.core_bundle.structures == ()
    assert result.s5_blocked[0]["status"] == "BLOCKED_DATASET_SCOPE_MISMATCH"
    assert result.report["available_views"]["S5_WAVE_REPRESENTATION"]["state"] == "BLOCKED_DATASET_SCOPE_MISMATCH"
    assert result.report["available_views"]["STAGE4B1"]["state"] == BLOCKED_MISSING_AUTHORIZED_POLICY


def test_valid_s5_contract_retains_scale_scope_and_authoritative_availability() -> None:
    frame = _zigzag_market()
    plan = _s5_plan(frame)
    result = _run(frame, timeline="synthetic-s5-movement-test", s5_plans=(plan,))

    assert "synthetic-alpha-representation" in result.s5_bundles
    candidate = result.s5_bundles["synthetic-alpha-representation"]
    s5_witness = result.s5_witness_bundles["synthetic-alpha-representation"]
    s5_event_ids = {
        row["record_identity"]
        for row in result.turning_point_records
        if row["record_type"] == "S2_SWING_EVENT_WITNESS_RECORD"
        and row["consumer_scope"] == "S5_REPRESENTATION_PLAN"
    }
    assert all(tp.witness_record_ref in s5_event_ids for tp in candidate.authoritative_turning_points)
    assert result.report["causal_turning_points"]["record_count"] == len(result.turning_point_records)
    assert candidate.representation_spec.intrinsic_scale_key == "synthetic-owner-scale-reference"
    assert candidate.representation_spec.identity_rule_ref == "synthetic-owner-identity-rule-reference"
    assert all(tp.origin_position < tp.availability_key.bar_position for tp in candidate.authoritative_turning_points)
    if candidate.authoritative_turning_points:
        turning_point = candidate.authoritative_turning_points[0]
        before_key = result.core_bundle.adapter.key_for_position(
            frame.index,
            turning_point.availability_key.bar_position - 1,
            InformationPhase.COMPLETED_ROW_AVAILABLE,
            0,
        )
        view_before = query_wave_representation_as_of(candidate, at_key=before_key)
        view_at = query_wave_representation_as_of(candidate, at_key=turning_point.availability_key)
        assert all(item.turning_point_id != turning_point.turning_point_id for item in view_before.visible_turning_points)
        assert any(item.turning_point_id == turning_point.turning_point_id for item in view_at.visible_turning_points)

    bars = []
    for position, (_, row) in enumerate(result.core_bundle.market.iterrows()):
        bars.append(PublishedOhlcBarFact(
            open_price=float(row["open"]),
            high_price=float(row["high"]),
            low_price=float(row["low"]),
            close_price=float(row["close"]),
            availability_key=result.core_bundle.adapter.key_for_position(frame.index, position, InformationPhase.COMPLETED_ROW_AVAILABLE, 0),
            source_identity=CALLER_SOURCE,
            dataset_identity=plan.dataset_identity.dataset_id,
            published_bar_record_ref=f"movement-research-input:{plan.dataset_identity.dataset_id}:{position}",
        ))
    prefix_length = 6
    prefix_witness = adapt_detector_witness_stream(bars[:prefix_length], confirmation_policy=plan.confirmation_policy)
    assert verify_wave_prefix_invariance(
        bars,
        prefix_length=prefix_length,
        full_witness_bundle=s5_witness,
        prefix_witness_bundle=prefix_witness,
        representation_spec=plan.representation_spec,
        policy_artifact=plan.policy_artifact,
        dataset_identity=plan.dataset_identity,
        dataset_role=plan.dataset_role,
    )
    assert result.report["available_views"]["S5_WAVE_REPRESENTATION"]["state"] == "AVAILABLE_CONTRACT_VALID"
    spec = result.report["policy_candidates"]["s5_representation_specs"][0]
    assert spec["intrinsic_scale_key"] == "synthetic-owner-scale-reference"
    assert spec["scope_axis"] == "TIME_INDEXED"
    assert spec["authorization_reference_state"] == "REFERENCE_PRESENT_NOT_AUTHENTICATED"


def test_s5_output_file_resolves_actual_s2_witness_references(tmp_path) -> None:
    frame = _zigzag_market()
    plan = _s5_plan(frame)
    output_dir = tmp_path / "movement-run"
    result = _run(
        frame,
        timeline="synthetic-s5-movement-test",
        s5_plans=(plan,),
        output_dir=output_dir,
    )

    rows = [json.loads(line) for line in (output_dir / "causal_turning_point_records.jsonl").read_text().splitlines()]
    s2_ids = {
        row["record_identity"]
        for row in rows
        if row["record_type"] == "S2_SWING_EVENT_WITNESS_RECORD"
        and row["consumer_scope"] == "S5_REPRESENTATION_PLAN"
    }
    s5_turning_points = [row for row in rows if row["record_type"] == "S5_AUTHORITATIVE_TURNING_POINT_RECORD"]
    assert s5_turning_points
    assert all(row["witness_record_ref"] in s2_ids for row in s5_turning_points)
    assert result.report["record_files"]["causal_turning_point_records"]["records"] == len(rows)
    assert result.report["causal_turning_points"]["record_count"] == len(rows)
    manifest = json.loads((output_dir / "movement_research_manifest.json").read_text())
    assert any(item["path"] == "causal_turning_point_records.jsonl" for item in manifest["files"])


def test_candidate_universe_is_preserved_when_spatial_relationship_budget_is_exhausted() -> None:
    limits = ReplayLimits(max_spatial_relations_per_boundary=0, max_spatial_relations_total=0)
    result = _run(_rich_market(70), policies=_declarations(), limits=limits)

    assert result.report["coverage"]["candidate_universe_complete"] is True
    assert result.report["coverage"]["candidate_universe_pruned"] is False
    assert result.replay.summary.entity_count == sum(result.replay.summary.candidates_by_domain_representation.values())
    assert result.replay.summary.relationship_coverage_state in {
        "PARTIAL_GLOBAL_SPATIAL_RELATIONSHIP_BUDGET",
        "PARTIAL_QUERY_OR_BOUNDARY_LIMIT",
    }


def test_resource_exhaustion_is_visible_and_does_not_prune_policy_or_candidate_sets() -> None:
    limits = ReplayLimits(max_registered_entities=0)
    result = _run(_simple_market(), policies=(_declarations()[0],), limits=limits)

    assert result.report["run_state"] == "BLOCKED_RESOURCE_EXHAUSTION"
    assert result.report["coverage"]["candidate_universe_pruned"] is False
    assert result.report["coverage"]["candidate_universe_complete"] is False
    assert "candidate entity count exceeds" in result.report["coverage"]["detail"]
    assert result.replay is None
    assert result.report["candidate_policy_status"][0]["status"] == "NOT_RUN_RESOURCE_LIMIT"


def test_nonempty_output_directory_is_rejected_without_mutation(tmp_path) -> None:
    output_dir = tmp_path / "occupied"
    output_dir.mkdir()
    sentinel = output_dir / "keep.txt"
    sentinel.write_text("user data", encoding="utf-8")

    with pytest.raises(ValueError, match="must be new or empty"):
        _run(_simple_market(), output_dir=output_dir)

    assert list(output_dir.iterdir()) == [sentinel]
    assert sentinel.read_text(encoding="utf-8") == "user data"


def test_optional_python_allocation_measurement_is_explicit() -> None:
    result = _run(_simple_market(), measure_python_allocations=True)
    measurements = result.report["measurements"]
    assert measurements["python_allocation_tracing_enabled"] is True
    assert measurements["python_tracemalloc_current_bytes_after_core_run"] is not None
    assert measurements["python_tracemalloc_peak_bytes_during_core_run"] is not None
    assert measurements["python_tracemalloc_scope"] == "THIS_RUN_TRACING_STARTED_BY_RUNNER"


def test_replay_is_deterministic_excluding_runtime_measurements() -> None:
    frame = _rich_market(70)
    policies = _declarations()
    first = _run(frame, policies=policies)
    second = _run(frame, policies=policies)

    assert first.report["deterministic_fingerprint_sha256"] == second.report["deterministic_fingerprint_sha256"]
    assert first.report["replay"]["prefix_chain_sha256"] == second.report["replay"]["prefix_chain_sha256"]
    assert [row["record_identity"] for row in first.turning_point_records if row["record_type"] == "S5_AUTHORITATIVE_TURNING_POINT_RECORD"] == [
        row["record_identity"] for row in second.turning_point_records if row["record_type"] == "S5_AUTHORITATIVE_TURNING_POINT_RECORD"
    ]
    assert first.report["measurements"]["wall_clock_seconds"] >= 0
    assert first.report["measurements"]["process_peak_rss_bytes"] is None or first.report["measurements"]["process_peak_rss_bytes"] >= 0
    assert first.report["measurements"]["python_allocation_tracing_enabled"] is False
