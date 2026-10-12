from __future__ import annotations

import json

import pandas as pd
import pytest

from trading_system.research.information_time import InformationPhase
from trading_system.research.trajectory.causal_market_context_core import (
    build_causal_market_context_core,
    replay_causal_market_context,
)
from trading_system.research.trajectory.contextual_hypothesis_resolution_core import (
    AnalysisMode,
    AuthorizationScope,
    AuthorizedHypothesisPolicy,
    ExactValueDiscriminatorContract,
    HypothesisDisposition,
    HypothesisDraft,
    HypothesisResolutionError,
    HypothesisResolutionSession,
    PolicyIdentity,
    ReassessmentCause,
    ResolutionLimits,
    SUPPORTED_RESOLUTION_RULE,
    SUPPORTED_RESOLUTION_RULE_SHA256,
    TerminationStatus,
    verify_asof_context,
)
from trading_system.sources import SourceArtifactIdentity


def _source() -> SourceArtifactIdentity:
    return SourceArtifactIdentity(
        symbol="BTCUSDT",
        market_type="SPOT",
        interval="1m",
        period_start_utc="2026-05-01T00:00:00Z",
        period_end_utc="2026-05-01T01:00:00Z",
    )


def _market(*, changed_first_close: bool = False) -> pd.DataFrame:
    close = [100.5 if changed_first_close else 101.0, 102.5, 105.0, 107.0, 102.0, 101.0]
    return pd.DataFrame(
        {
            "open": [100.0, 102.0, 104.0, 106.0, 107.0, 103.0],
            "high": [102.0, 103.0, 106.0, 108.0, 109.0, 105.0],
            "low": [99.0, 101.0, 103.0, 102.5, 101.0, 100.0],
            "close": close,
            "volume": [100.0, 120.0, 110.0, 90.0, 95.0, 80.0],
        },
        index=pd.date_range("2026-05-01T00:01:00Z", periods=6, freq="min"),
    )


def _bundle(*, changed_first_close: bool = False, timeline_id: str = "hypothesis-test-timeline"):
    return build_causal_market_context_core(
        market_history=_market(changed_first_close=changed_first_close),
        source_identity=_source(),
        timeline_id=timeline_id,
    )


def _key(bundle, position: int):
    return bundle.adapter.key_for_position(
        bundle.market.index,
        position,
        InformationPhase.COMPLETED_ROW_AVAILABLE,
        0,
    )


def _policy_identity(
    *,
    policy_id: str = "SYNTHETIC_BINARY_FIXTURE_POLICY",
    policy_sha256: str = "a" * 64,
    implementation_sha256: str = "b" * 64,
) -> PolicyIdentity:
    return PolicyIdentity(
        policy_id=policy_id,
        policy_version="SOFTWARE_TEST_V1",
        policy_sha256=policy_sha256,
        implementation_sha256=implementation_sha256,
        authorization_reference="TEST_ONLY:synthetic-software-correctness",
        authorization_scope=AuthorizationScope.SOFTWARE_TEST_ONLY,
        authorization_status="AUTHORIZED",
        resolution_rule_id=SUPPORTED_RESOLUTION_RULE,
        resolution_rule_sha256=SUPPORTED_RESOLUTION_RULE_SHA256,
    )


class _StaticPolicy:
    def __init__(self, drafts_factory):
        self.drafts_factory = drafts_factory
        self.seen_inputs = []

    def generate(self, context):
        self.seen_inputs.append(context)
        return self.drafts_factory(context)


def _binary_drafts(context, *, left="FIXTURE_CLOSE_102_5", right="FIXTURE_CLOSE_101"):
    boundary_id = next(
        item.evidence_id
        for item in context.evidence
        if item.record_type == "CAUSAL_MARKET_CONTEXT_BOUNDARY"
    )
    return (
        HypothesisDraft(
            left,
            "SYNTHETIC_BINARY_OBSERVATION",
            "TEST ONLY: the first new synthetic boundary reports close exactly 102.5",
            (boundary_id,),
            (boundary_id,),
            ("synthetic fixture semantics only; no market interpretation",),
        ),
        HypothesisDraft(
            right,
            "SYNTHETIC_BINARY_OBSERVATION",
            "TEST ONLY: the first new synthetic boundary reports close exactly 101.0",
            (boundary_id,),
            (boundary_id,),
            ("synthetic fixture semantics only; no market interpretation",),
        ),
    )


def _exact_contract(policy: PolicyIdentity, left: str, right: str, *, group: str = "SYNTHETIC_BINARY_OBSERVATION", record_type: str = "CAUSAL_MARKET_CONTEXT_BOUNDARY", path=("facts", "published_bar_record", "content", "ohlcv", "close"), expected=(("FIXTURE_CLOSE_102_5", 102.5), ("FIXTURE_CLOSE_101", 101.0)), contract_id="FIXTURE_CLOSE_EXACT_V1"):
    return ExactValueDiscriminatorContract(
        contract_id=contract_id,
        contract_version="SOFTWARE_TEST_V1",
        policy_sha256=policy.policy_sha256,
        authorization_reference="TEST_ONLY:synthetic-discriminator",
        alternative_group_id=group,
        hypothesis_ids=(left, right),
        evidence_record_type=record_type,
        field_path=tuple(path),
        expected_values_by_hypothesis=tuple(expected),
        require_evidence_after_generation=True,
        closed_world=True,
        selection_rule_id="FIRST_MATCHING_INFORMATION_BATCH",
    )


def _replay(*, changed_first_close: bool = False, timeline_id: str = "hypothesis-test-timeline"):
    bundle = _bundle(changed_first_close=changed_first_close, timeline_id=timeline_id)
    return bundle, replay_causal_market_context(bundle)


def test_synthetic_competing_hypotheses_resolve_on_new_declared_evidence_and_keep_history():
    bundle, replay = _replay()
    context0 = verify_asof_context(replay, _key(bundle, 0))
    context1 = verify_asof_context(replay, _key(bundle, 1))
    identity = _policy_identity()
    producer = _StaticPolicy(_binary_drafts)
    policy = AuthorizedHypothesisPolicy(identity, producer)
    contract = _exact_contract(identity, "FIXTURE_CLOSE_102_5", "FIXTURE_CLOSE_101")
    session = HypothesisResolutionSession()

    initial = session.analyze(
        context0,
        policy=policy,
        discriminators=(contract,),
        mode=AnalysisMode.SOFTWARE_TEST_ONLY,
    )
    assert initial.cycle.termination_status is TerminationStatus.UNRESOLVED_WAITING_FOR_SPECIFIC_EVIDENCE
    assert initial.cycle.hypothesis_generation_state == "AUTHORIZED_HYPOTHESES_GENERATED"
    assert len(initial.hypotheses) == 2
    assert all(item.alternative_hypothesis_ids == ("FIXTURE_CLOSE_101", "FIXTURE_CLOSE_102_5") for item in initial.hypotheses)
    prior = initial.pair_assessments[0]
    assert prior.pair_status == "UNRESOLVED_WAITING_FOR_SPECIFIC_EVIDENCE"
    assert prior.required_evidence["state"] == "FUTURE_OBSERVATION_NEEDED"
    assert prior.required_evidence["strictly_after_key"]["bar_position"] == 0
    assert prior.required_evidence["already_available_but_not_eligible_evidence_ids"] == tuple(
        item.evidence_id for item in context0.evidence if item.record_type == "CAUSAL_MARKET_CONTEXT_BOUNDARY"
    )
    assert context0.as_of_key.bar_position == 0
    assert max(item.information_key.bar_position for item in producer.seen_inputs[0].evidence) == 0
    assert not hasattr(producer.seen_inputs[0], "source_file_sha256")
    assert all(not hasattr(item, "surface_ids") for item in producer.seen_inputs[0].representation_policies)
    assert context0.provenance_payload()["representation_surface_ids_are_full_run_provenance_only"] is True
    assert all(item.information_key <= context0.as_of_key for item in producer.seen_inputs[0].evidence)
    policy_boundary = next(item for item in producer.seen_inputs[0].evidence if item.record_type == "CAUSAL_MARKET_CONTEXT_BOUNDARY")
    assert "source_identity" not in policy_boundary.payload["facts"]["published_bar_record"]["content"]
    assert context0.provenance_payload()["source_identity"]["symbol"] == "BTCUSDT"

    prior_record = prior.record
    prior_payload = dict(prior_record.content)
    reassessed = session.reassess(context1)
    assert reassessed.cycle.termination_status is TerminationStatus.RESOLVED_UNDER_DECLARED_POLICY
    assert reassessed.cycle.reassessment_cause == ReassessmentCause.EVIDENCE_ARRIVED.value
    assert reassessed.cycle.affected_pair_ids == (prior.pair_id,)
    current = reassessed.pair_assessments[0]
    assert current.supersedes_assessment_id == prior.assessment_id
    assert current.observed_value == 102.5
    assert dict(current.dispositions) == {
        "FIXTURE_CLOSE_101": HypothesisDisposition.CONTRADICTED_BY_DECLARED_EVIDENCE.value,
        "FIXTURE_CLOSE_102_5": HypothesisDisposition.SUPPORTED_BY_DECLARED_EVIDENCE.value,
    }
    assert current.record.content["resolution_semantics"] == "CONTRACT_RELATIVE_MECHANICAL_RESULT_NOT_MARKET_TRUTH"
    assert current.record.content["probability_relevance_score_and_empirical_proof_emitted"] is False
    assert '"termination_status": "RESOLVED_UNDER_DECLARED_POLICY"' in json.dumps(reassessed.payload(), sort_keys=True)

    stored_prior = next(item for item in session.ledger.records if item.record_identity == prior_record.record_identity)
    assert stored_prior is prior_record
    assert dict(stored_prior.content) == prior_payload
    assert session.ledger.status_of(prior_record.record_identity) == prior.pair_status
    assert len(session.ledger.events) == len(session.ledger.records)
    assert session.ledger.events[-1].event_payload["ledger_storage_order_is_not_information_order"] is True

    later_context = verify_asof_context(replay, _key(bundle, 2))
    later = session.reassess(later_context)
    assert later.cycle.reassessment_cause == ReassessmentCause.NO_NEW_RELEVANT_EVIDENCE.value
    assert later.cycle.affected_pair_ids == ()
    assert later.pair_assessments[0].assessment_id == current.assessment_id
    assert not any(item.record_type == "CONTEXTUAL_HYPOTHESIS_PAIR_ASSESSMENT" for item in later.records_added)


def test_unmapped_declared_outcome_remains_unresolved_without_confidence_or_fallback():
    bundle, replay = _replay()
    context0 = verify_asof_context(replay, _key(bundle, 0))
    context1 = verify_asof_context(replay, _key(bundle, 1))
    identity = _policy_identity()
    policy = AuthorizedHypothesisPolicy(identity, _StaticPolicy(_binary_drafts))
    contract = _exact_contract(
        identity,
        "FIXTURE_CLOSE_102_5",
        "FIXTURE_CLOSE_101",
        expected=(("FIXTURE_CLOSE_102_5", 999.0), ("FIXTURE_CLOSE_101", 888.0)),
        contract_id="FIXTURE_CLOSE_UNMAPPED_OUTCOME",
    )
    session = HypothesisResolutionSession()
    initial = session.analyze(context0, policy=policy, discriminators=(contract,), mode=AnalysisMode.SOFTWARE_TEST_ONLY)
    assert initial.cycle.termination_status is TerminationStatus.UNRESOLVED_WAITING_FOR_SPECIFIC_EVIDENCE

    result = session.reassess(context1)
    assessment = result.pair_assessments[0]
    assert result.cycle.termination_status is TerminationStatus.INSUFFICIENT_EVIDENCE
    assert assessment.pair_status == "UNRESOLVED"
    assert all(value == HypothesisDisposition.REMAINS_UNRESOLVED.value for _, value in assessment.dispositions)
    assert assessment.required_evidence["state"] == "OBSERVATION_NOT_MAPPED_TO_A_DECLARED_ALTERNATIVE"
    assert assessment.record.content["probability_relevance_score_and_empirical_proof_emitted"] is False


def test_ambiguous_same_information_batch_is_insufficient_not_arbitrarily_ordered():
    bundle, replay = _replay()
    context3 = verify_asof_context(replay, _key(bundle, 3))
    context4 = verify_asof_context(replay, _key(bundle, 4))
    identity = _policy_identity()
    policy = AuthorizedHypothesisPolicy(identity, _StaticPolicy(_binary_drafts))
    contract = _exact_contract(
        identity,
        "FIXTURE_CLOSE_102_5",
        "FIXTURE_CLOSE_101",
        record_type="CAUSAL_MARKET_PRODUCER_EVENT::FVG",
        path=("event_type",),
        expected=(("FIXTURE_CLOSE_102_5", "FIRST_FULL_RANGE_COVERAGE"), ("FIXTURE_CLOSE_101", "FIRST_FAR_SIDE_WICK_BREACH")),
        contract_id="SAME_BATCH_EVENT_TYPE_TEST",
    )
    session = HypothesisResolutionSession()
    initial = session.analyze(context3, policy=policy, discriminators=(contract,), mode=AnalysisMode.SOFTWARE_TEST_ONLY)
    assert initial.cycle.termination_status is TerminationStatus.UNRESOLVED_WAITING_FOR_SPECIFIC_EVIDENCE

    result = session.reassess(context4)
    assessment = result.pair_assessments[0]
    assert result.cycle.termination_status is TerminationStatus.INSUFFICIENT_EVIDENCE
    assert assessment.pair_status == "INSUFFICIENT_INFORMATION"
    assert len(assessment.evidence_ids) == 2
    assert assessment.required_evidence["state"] == "AMBIGUOUS_FIRST_INFORMATION_BATCH"
    assert assessment.required_evidence["same_information_batch_order_claimed"] is False


def test_no_policy_returns_explicit_unauthorized_generation_state():
    bundle, replay = _replay()
    context = verify_asof_context(replay, _key(bundle, 0))
    result = HypothesisResolutionSession().analyze(context)
    assert result.cycle.termination_status is TerminationStatus.NO_AUTHORIZED_HYPOTHESES
    assert result.cycle.hypothesis_generation_state == "HYPOTHESIS_GENERATION_NOT_AUTHORIZED"
    assert not result.hypotheses
    assert not result.pair_assessments


def test_software_test_policy_cannot_generate_operational_hypotheses():
    bundle, replay = _replay()
    context = verify_asof_context(replay, _key(bundle, 0))
    producer = _StaticPolicy(_binary_drafts)
    result = HypothesisResolutionSession().analyze(
        context,
        policy=AuthorizedHypothesisPolicy(_policy_identity(), producer),
        mode=AnalysisMode.OPERATIONAL,
    )
    assert result.cycle.termination_status is TerminationStatus.NO_AUTHORIZED_HYPOTHESES
    assert result.cycle.hypothesis_generation_state == "HYPOTHESIS_GENERATION_NOT_AUTHORIZED"
    assert not producer.seen_inputs


def test_missing_discriminator_fails_closed_instead_of_inventing_one():
    bundle, replay = _replay()
    context = verify_asof_context(replay, _key(bundle, 0))
    identity = _policy_identity()
    policy = AuthorizedHypothesisPolicy(identity, _StaticPolicy(_binary_drafts))
    result = HypothesisResolutionSession().analyze(
        context,
        policy=policy,
        discriminators=(),
        mode=AnalysisMode.SOFTWARE_TEST_ONLY,
    )
    assert result.cycle.termination_status is TerminationStatus.INSUFFICIENT_EVIDENCE
    assert result.pair_assessments[0].pair_status == "DISCRIMINATOR_NOT_ESTABLISHED"
    assert all(value == HypothesisDisposition.DISCRIMINATOR_NOT_ESTABLISHED.value for _, value in result.pair_assessments[0].dispositions)


def test_full_source_metadata_is_not_an_eligible_discriminator_feature():
    bundle, replay = _replay()
    context0 = verify_asof_context(replay, _key(bundle, 0))
    context1 = verify_asof_context(replay, _key(bundle, 1))
    identity = _policy_identity()
    policy = AuthorizedHypothesisPolicy(identity, _StaticPolicy(_binary_drafts))
    source_end = context0.provenance_payload()["source_identity"]["period_end_utc"]
    contract = _exact_contract(
        identity,
        "FIXTURE_CLOSE_102_5",
        "FIXTURE_CLOSE_101",
        path=("facts", "published_bar_record", "content", "source_identity", "period_end_utc"),
        expected=(("FIXTURE_CLOSE_102_5", source_end), ("FIXTURE_CLOSE_101", "OTHER_END")),
        contract_id="SOURCE_METADATA_MUST_NOT_DISCRIMINATE",
    )
    session = HypothesisResolutionSession()
    initial = session.analyze(context0, policy=policy, discriminators=(contract,), mode=AnalysisMode.SOFTWARE_TEST_ONLY)
    later = session.reassess(context1)
    assert initial.cycle.termination_status is TerminationStatus.UNRESOLVED_WAITING_FOR_SPECIFIC_EVIDENCE
    assert later.cycle.termination_status is TerminationStatus.UNRESOLVED_WAITING_FOR_SPECIFIC_EVIDENCE
    assert later.cycle.affected_pair_ids == ()


def test_policy_cannot_cite_a_future_record_not_visible_at_its_asof_cut():
    bundle, replay = _replay()
    context0 = verify_asof_context(replay, _key(bundle, 0))
    context1 = verify_asof_context(replay, _key(bundle, 1))
    future_id = next(item.evidence_id for item in context1.evidence if item.record_type == "CAUSAL_MARKET_CONTEXT_BOUNDARY" and item.information_key.bar_position == 1)
    identity = _policy_identity()

    def leak(_context):
        return (
            HypothesisDraft("FUTURE_A", "FUTURE_TEST", "TEST ONLY", (future_id,), (future_id,), ("future not admitted",)),
            HypothesisDraft("FUTURE_B", "FUTURE_TEST", "TEST ONLY ALTERNATIVE", (future_id,), (future_id,), ("future not admitted",)),
        )

    result = HypothesisResolutionSession().analyze(
        context0,
        policy=AuthorizedHypothesisPolicy(identity, _StaticPolicy(leak)),
        mode=AnalysisMode.SOFTWARE_TEST_ONLY,
    )
    assert result.cycle.termination_status is TerminationStatus.INVALID_FOUNDATION
    assert result.cycle.hypothesis_generation_state == "AUTHORIZED_POLICY_OUTPUT_REJECTED"
    assert result.cycle.details["no_partial_hypothesis_set_admitted"] is True
    assert not result.hypotheses


def test_corrected_prior_input_invalidates_without_rewriting_old_assessments():
    old_bundle, old_replay = _replay()
    new_bundle, new_replay = _replay(changed_first_close=True)
    old_context = verify_asof_context(old_replay, _key(old_bundle, 0))
    corrected_context = verify_asof_context(new_replay, _key(new_bundle, 1))
    identity = _policy_identity()
    policy = AuthorizedHypothesisPolicy(identity, _StaticPolicy(_binary_drafts))
    contract = _exact_contract(identity, "FIXTURE_CLOSE_102_5", "FIXTURE_CLOSE_101")
    session = HypothesisResolutionSession()
    initial = session.analyze(old_context, policy=policy, discriminators=(contract,), mode=AnalysisMode.SOFTWARE_TEST_ONLY)
    old_assessment = initial.pair_assessments[0]

    invalidation = session.reassess(corrected_context)
    assert invalidation.cycle.termination_status is TerminationStatus.INVALID_FOUNDATION
    assert invalidation.cycle.reassessment_cause == ReassessmentCause.CORRECTED_INPUT.value
    assert invalidation.pair_assessments[0].pair_status == "INVALID_FOUNDATION"
    assert invalidation.pair_assessments[0].supersedes_assessment_id == old_assessment.assessment_id
    retained = next(item for item in session.ledger.records if item.record_identity == old_assessment.record.record_identity)
    assert retained is old_assessment.record
    assert retained.content["pair_status"] == "UNRESOLVED_WAITING_FOR_SPECIFIC_EVIDENCE"


def test_only_pairs_affected_by_new_evidence_are_reassessed():
    bundle, replay = _replay()
    context0 = verify_asof_context(replay, _key(bundle, 0))
    context1 = verify_asof_context(replay, _key(bundle, 1))
    identity = _policy_identity()

    def two_groups(context):
        boundary_id = next(item.evidence_id for item in context.evidence if item.record_type == "CAUSAL_MARKET_CONTEXT_BOUNDARY")
        return (
            HypothesisDraft("A1", "GROUP_A", "TEST ONLY: A1", (boundary_id,), (boundary_id,), ("synthetic",)),
            HypothesisDraft("A2", "GROUP_A", "TEST ONLY: A2", (boundary_id,), (boundary_id,), ("synthetic",)),
            HypothesisDraft("B1", "GROUP_B", "TEST ONLY: B1", (boundary_id,), (boundary_id,), ("synthetic",)),
            HypothesisDraft("B2", "GROUP_B", "TEST ONLY: B2", (boundary_id,), (boundary_id,), ("synthetic",)),
        )

    contract_a = _exact_contract(
        identity,
        "A1",
        "A2",
        group="GROUP_A",
        expected=(("A1", 102.5), ("A2", 101.0)),
        contract_id="GROUP_A_EXACT_CLOSE",
    )
    contract_b = _exact_contract(
        identity,
        "B1",
        "B2",
        group="GROUP_B",
        record_type="DECLARED_BUT_NOT_YET_PRODUCED_TEST_RECORD",
        path=("value",),
        expected=(("B1", "LEFT"), ("B2", "RIGHT")),
        contract_id="GROUP_B_FUTURE_RECORD",
    )
    session = HypothesisResolutionSession()
    first = session.analyze(
        context0,
        policy=AuthorizedHypothesisPolicy(identity, _StaticPolicy(two_groups)),
        discriminators=(contract_a, contract_b),
        mode=AnalysisMode.SOFTWARE_TEST_ONLY,
    )
    by_pair = {item.pair_id: item for item in first.pair_assessments}
    pair_a = next(item.pair_id for item in first.pair_assessments if set(item.hypothesis_ids) == {"A1", "A2"})
    pair_b = next(item.pair_id for item in first.pair_assessments if set(item.hypothesis_ids) == {"B1", "B2"})

    later = session.reassess(context1)
    assert later.cycle.affected_pair_ids == (pair_a,)
    assert later.cycle.unaffected_pair_ids == (pair_b,)
    assert len(later.pair_assessments) == 1
    assert later.pair_assessments[0].pair_id == pair_a
    assert session.generation.assessments_by_pair[pair_b] is by_pair[pair_b]
    assert session.generation.assessments_by_pair[pair_b].pair_status == "UNRESOLVED_WAITING_FOR_SPECIFIC_EVIDENCE"


def test_policy_change_is_recorded_as_policy_change_not_evidence_reassessment():
    bundle, replay = _replay()
    context = verify_asof_context(replay, _key(bundle, 0))
    first_identity = _policy_identity()
    first_policy = AuthorizedHypothesisPolicy(first_identity, _StaticPolicy(_binary_drafts))
    first_contract = _exact_contract(first_identity, "FIXTURE_CLOSE_102_5", "FIXTURE_CLOSE_101")
    session = HypothesisResolutionSession()
    initial = session.analyze(context, policy=first_policy, discriminators=(first_contract,), mode=AnalysisMode.SOFTWARE_TEST_ONLY)

    second_identity = _policy_identity(policy_id="SYNTHETIC_BINARY_FIXTURE_POLICY_V2", policy_sha256="c" * 64, implementation_sha256="d" * 64)
    second_policy = AuthorizedHypothesisPolicy(second_identity, _StaticPolicy(_binary_drafts))
    second_contract = _exact_contract(second_identity, "FIXTURE_CLOSE_102_5", "FIXTURE_CLOSE_101", contract_id="FIXTURE_CLOSE_EXACT_V2")
    changed = session.reassess(context, policy=second_policy, discriminators=(second_contract,))
    assert changed.cycle.reassessment_cause == ReassessmentCause.INTERPRETATION_POLICY_CHANGE.value
    assert changed.cycle.termination_status is TerminationStatus.UNRESOLVED_WAITING_FOR_SPECIFIC_EVIDENCE
    assert changed.hypotheses[0].policy_identity["policy_id"] == second_identity.policy_id
    prior_ids = {item.record.record_identity for item in initial.hypotheses}
    assert prior_ids.issubset({item.record_identity for item in session.ledger.records if item.record_type == "CONTEXTUAL_HYPOTHESIS"})


def test_resource_budget_marks_pair_coverage_incomplete_without_dropping_hypotheses():
    bundle, replay = _replay()
    context = verify_asof_context(replay, _key(bundle, 0))
    identity = _policy_identity()

    def three(context):
        boundary_id = next(item.evidence_id for item in context.evidence if item.record_type == "CAUSAL_MARKET_CONTEXT_BOUNDARY")
        return tuple(
            HypothesisDraft(f"H{i}", "THREE_WAY_FIXTURE", f"TEST ONLY {i}", (boundary_id,), (boundary_id,), ("synthetic",))
            for i in range(3)
        )

    result = HypothesisResolutionSession(limits=ResolutionLimits(max_pair_evaluations=1)).analyze(
        context,
        policy=AuthorizedHypothesisPolicy(identity, _StaticPolicy(three)),
        mode=AnalysisMode.SOFTWARE_TEST_ONLY,
    )
    assert result.cycle.termination_status is TerminationStatus.INCOMPLETE_COVERAGE
    assert result.cycle.total_competing_pairs == 3
    assert result.cycle.unexamined_pair_count == 3
    assert len(result.hypotheses) == 3
    assert result.cycle.details["hypotheses_pruned"] is False


def test_discriminator_evidence_scan_budget_is_explicit_and_does_not_prune_pairs():
    bundle, replay = _replay()
    context0 = verify_asof_context(replay, _key(bundle, 0))
    context1 = verify_asof_context(replay, _key(bundle, 1))
    identity = _policy_identity()
    policy = AuthorizedHypothesisPolicy(identity, _StaticPolicy(_binary_drafts))
    contract = _exact_contract(identity, "FIXTURE_CLOSE_102_5", "FIXTURE_CLOSE_101")
    session = HypothesisResolutionSession(limits=ResolutionLimits(max_discriminator_evidence_checks=1))

    initial = session.analyze(context0, policy=policy, discriminators=(contract,), mode=AnalysisMode.SOFTWARE_TEST_ONLY)
    assert initial.cycle.termination_status is TerminationStatus.INCOMPLETE_COVERAGE
    assert initial.cycle.unexamined_pair_count == 1
    assert not initial.pair_assessments
    assert initial.cycle.details["pair_ids_pruned"] is False

    later = session.reassess(context1)
    assert later.cycle.termination_status is TerminationStatus.INCOMPLETE_COVERAGE
    assert later.cycle.reassessment_cause == ReassessmentCause.RESOURCE_LIMIT_INCOMPLETE.value
    assert later.cycle.details["evidence_used_to_fill_prior_coverage_gap"] is False


def test_prefix_corruption_rejected_before_policy_receives_context():
    bundle, replay = _replay()
    replay.boundaries[0]["content"]["facts"]["same_information_batch_rule"] = "MUTATED"
    with pytest.raises(HypothesisResolutionError, match="facts hash mismatch"):
        verify_asof_context(replay, _key(bundle, 0))


def test_exact_value_contract_rejects_non_distinguishing_expected_values():
    identity = _policy_identity()
    with pytest.raises(HypothesisResolutionError, match="must differ"):
        _exact_contract(
            identity,
            "A",
            "B",
            expected=(("A", 1.0), ("B", 1.0)),
        )


def test_context_requires_real_core_memory_result_and_legal_information_key():
    bundle, replay = _replay()
    with pytest.raises(HypothesisResolutionError, match="ReplayMemoryResult"):
        verify_asof_context(object(), _key(bundle, 0))
    preclose = bundle.adapter.key_for_position(bundle.market.index, 0, InformationPhase.BAR_PRE_CLOSE, 0)
    with pytest.raises(HypothesisResolutionError, match="legal completed-row"):
        verify_asof_context(replay, preclose)
