from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace

import pandas as pd
import pytest

from trading_system.research.information_time import InformationPhase
from trading_system.research.trajectory import trajectory_stage4b2 as s4b2
from trading_system.research.trajectory.trajectory_contract import MarketObservationTimeline
from trading_system.research.trajectory.trajectory_query_views import decision_surface_view
from trading_system.research.trajectory.trajectory_relevance_pilot import (
    UNSAFE_BLOCKER_DECLARATIONS,
    AssessmentCategory,
    AssessmentProtocolIdentity,
    CandidateCoverageState,
    CandidatePilotError,
    CandidateResearchLedger,
    ProvisionalStatus,
    ResearchQuestion,
    append_candidate_assessment,
    build_fvg_candidate_universe,
    initialize_candidate_research_ledger,
    reconcile_candidate_coverage,
    record_candidate_coverage,
    restore_deferred_candidate,
    retrieve_new_fvg_factual_evidence,
    revise_candidate_assessment,
)
from test_trajectory_query_views import _b2_sources
import trading_system.research.trajectory.trajectory_relevance_pilot as pilot


def _key(sources, position: int):
    market, adapter, *_ = sources
    return adapter.key_for_position(
        market.index,
        position,
        InformationPhase.COMPLETED_ROW_AVAILABLE,
    )


def _universe(sources, position: int = 7):
    market, adapter, timeline, _, surfaces = sources
    return build_fvg_candidate_universe(
        timeline=timeline,
        adapter=adapter,
        market_history=market,
        fvg_surface=surfaces["FVG"],
        decision_key=_key(sources, position),
    )


def _question(question_id: str = "q-context"):
    return ResearchQuestion.declare(
        question_id=question_id,
        version="1",
        text=f"Declared investigation question {question_id}; no prediction or utility claim.",
    )


def _protocol(protocol_id: str = "protocol-human"):
    return AssessmentProtocolIdentity.declare(
        protocol_id=protocol_id,
        version="1",
        description="Declared provisional review protocol; no empirical validation.",
    )


def _ledger(universe, *questions):
    return initialize_candidate_research_ledger(
        universe=universe,
        questions=questions or (_question(),),
    )


def _append_initial_assessment(ledger, candidate_id: str, question_id: str = "q-context"):
    candidate = ledger.universe.candidate(candidate_id)
    evidence_id = candidate.entity_evidence.reference_id
    return append_candidate_assessment(
        ledger=ledger,
        candidate_id=candidate_id,
        question_id=question_id,
        category=AssessmentCategory.DECLARED_HUMAN_ASSESSMENT,
        protocol=_protocol(),
        as_of_key=ledger.universe.decision_key,
        evidence_reference_ids=(evidence_id,),
        supporting_reference_ids=(evidence_id,),
        provisional_status=ProvisionalStatus.PROVISIONAL,
        reason="Declared provisional context review; no outcome or trading-use claim.",
        declaration_reference="annotator:pilot-test",
    )


def _candidate_with_later_event(universe, surface, start_position: int = 7) -> str:
    candidate_ids = set(universe.eligible_candidate_ids)
    later = surface.normalized_event_frame
    later = later[(later["event_position"] > start_position) & later["fvg_id"].astype(str).isin(candidate_ids)]
    assert not later.empty, "the existing synthetic FVG fixture must expose a later lifecycle event"
    return str(later.iloc[0]["fvg_id"])


def test_complete_visible_enumeration_uses_every_asof_fvg_entity(_b2_sources):
    universe = _universe(_b2_sources)
    case = universe._case
    view = decision_surface_view(case=case, surfaces=(_b2_sources[4]["FVG"],))
    instance = view.surfaces[0]
    entity_table = instance.tables[2]
    id_column = entity_table.columns.index("fvg_id")
    source_ids = tuple(str(row[id_column].value) for row in entity_table.rows)
    assert universe.eligible_candidate_ids == source_ids
    assert universe.source_visible_entity_count == len(entity_table.rows) == 3
    assert universe.eligibility_policy_id == pilot.FVG_ELIGIBILITY_POLICY_ID


def test_future_candidates_and_events_do_not_leak_into_registration(_b2_sources):
    universe = _universe(_b2_sources, position=7)
    surface = _b2_sources[4]["FVG"]
    future_candidates = set(
        surface.normalized_entity_frame.loc[
            surface.normalized_entity_frame["creation_position"] > 7, "fvg_id"
        ].astype(str)
    )
    assert future_candidates
    assert not future_candidates.intersection(universe.eligible_candidate_ids)
    assert all(event.available_at.bar_position <= 7 for item in universe.candidates for event in item.visible_lifecycle_events)
    candidate_id = _candidate_with_later_event(universe, surface)
    assert all(
        event.available_at.bar_position <= 7
        for event in universe.candidate(candidate_id).visible_lifecycle_events
    )


def test_historical_universe_and_assessment_identities_survive_future_append(_b2_sources):
    market, _, _, _, surfaces = _b2_sources
    full_universe = _universe(_b2_sources, position=7)
    prefix_market = market.iloc[:8].copy(deep=True)
    prefix_adapter = type(_b2_sources[1])(_b2_sources[1].timeline_id)
    prefix_timeline = MarketObservationTimeline.seal(
        adapter=prefix_adapter,
        market_history=prefix_market,
    )
    prefix_surface = s4b2.build_fvg_surface(
        timeline=prefix_timeline,
        adapter=prefix_adapter,
        market_history=prefix_market,
    )
    prefix_key = prefix_adapter.key_for_position(
        prefix_market.index,
        7,
        InformationPhase.COMPLETED_ROW_AVAILABLE,
    )
    prefix_universe = build_fvg_candidate_universe(
        timeline=prefix_timeline,
        adapter=prefix_adapter,
        market_history=prefix_market,
        fvg_surface=prefix_surface,
        decision_key=prefix_key,
    )
    assert full_universe.case_id == prefix_universe.case_id
    assert full_universe == prefix_universe
    assert full_universe.universe_id == prefix_universe.universe_id
    assert full_universe.source_prefix_hash == prefix_universe.source_prefix_hash
    assert full_universe.eligible_candidate_ids == prefix_universe.eligible_candidate_ids
    assert full_universe.candidate("0").candidate_identity_hash == prefix_universe.candidate("0").candidate_identity_hash
    assert full_universe.candidate("0").source_provenance.source_surface_id != prefix_universe.candidate("0").source_provenance.source_surface_id

    question = _question()
    full_ledger = _append_initial_assessment(_ledger(full_universe, question), "0")
    prefix_ledger = _append_initial_assessment(_ledger(prefix_universe, question), "0")
    assert full_ledger.assessments[0].assessment_id == prefix_ledger.assessments[0].assessment_id


def test_candidate_context_is_source_backed_and_preserves_producer_fields(_b2_sources):
    universe = _universe(_b2_sources)
    for candidate in universe.candidates:
        attributes = dict(candidate.factual_attributes)
        assert candidate.entity_evidence.row == tuple(cell for _, cell in candidate.factual_attributes)
        assert attributes["fvg_id"].value == candidate.candidate_id
        assert int(attributes["origin_position"].value) == candidate.origin_positions[0]
        assert int(attributes["creation_position"].value) == candidate.creation_position
        assert candidate.availability_position == candidate.creation_position
        assert candidate.availability_key.bar_position == candidate.availability_position
        assert candidate.entity_evidence.source_binding_hash == universe.source_binding_hash
        assert candidate.entity_evidence.source_prefix_hash == universe.source_prefix_hash
        assert any(
            dict(zip(event.row_columns, event.row))["event_type"].value == "FVG_CREATED"
            and event.available_at == candidate.availability_key
            for event in candidate.visible_lifecycle_events
        )
        assert candidate.source_provenance.producer_policy_identity.policy_id == "STAGE4B2_FVG_PUBLIC_CONTRACT"
        assert candidate.source_provenance.verification_scope


def test_missing_and_unbound_context_stays_explicitly_unknown(_b2_sources):
    universe = _universe(_b2_sources)
    candidate = universe.candidate("0")
    statuses = {domain: (status, count) for domain, status, count in candidate.domain_availability}
    assert statuses["FVG"] == ("AVAILABLE", 1)
    assert statuses["HTF_SCALE_RAW"] == ("NOT_SUPPLIED", 0)
    assert statuses["LIQUIDITY"] == ("NOT_SUPPLIED", 0)
    assert any(
        ref.evidence_kind == "CONTEXT_DOMAIN_NOT_SUPPLIED"
        and ref.producer_domain == "HTF_SCALE_RAW"
        for ref in candidate.unknown_context_references
    )
    assert dict(candidate.factual_attributes)["gap_width_percentile"].kind.value == "MISSING"
    assert any(
        ref.evidence_kind == "SOURCE_ATTRIBUTE_MISSING"
        and dict(zip(ref.row_columns, ref.row))["field"].value == "gap_width_percentile"
        for ref in candidate.unknown_context_references
    )
    assert not hasattr(candidate, "inferred_htf_bias")


def test_assessments_are_scoped_to_registered_research_questions(_b2_sources):
    universe = _universe(_b2_sources)
    q_one = _question("q-one")
    q_two = _question("q-two")
    ledger = _ledger(universe, q_one, q_two)
    candidate = universe.candidate("0")
    ref = candidate.entity_evidence.reference_id
    ledger = append_candidate_assessment(
        ledger=ledger,
        candidate_id="0",
        question_id="q-one",
        category=AssessmentCategory.FACTUAL_CONTEXT,
        protocol=_protocol(),
        as_of_key=universe.decision_key,
        evidence_reference_ids=(ref,),
        reason="Source-row facts recorded for q-one only.",
    )
    assert ledger.assessments[0].question.question_id == "q-one"
    assert ledger.assessments_for("0", "q-two") == ()
    assert ledger.latest_coverage("0", "q-two").state is CandidateCoverageState.REGISTERED


def test_multiple_provisional_assessments_are_preserved_append_only(_b2_sources):
    universe = _universe(_b2_sources)
    ledger = _ledger(universe)
    candidate = universe.candidate("1")
    factual = candidate.entity_evidence.reference_id
    unknown = candidate.unknown_context_references[0].reference_id
    event = candidate.visible_lifecycle_events[-1].reference_id
    ledger = append_candidate_assessment(
        ledger=ledger,
        candidate_id="1",
        question_id="q-context",
        category=AssessmentCategory.DECLARED_HUMAN_ASSESSMENT,
        protocol=_protocol("human-review"),
        as_of_key=universe.decision_key,
        evidence_reference_ids=(factual,),
        supporting_reference_ids=(factual,),
        provisional_status=ProvisionalStatus.PROVISIONAL,
        reason="Human view A: investigate; not empirical relevance.",
        declaration_reference="annotator:A",
    )
    first = ledger.assessments[0]
    ledger = append_candidate_assessment(
        ledger=ledger,
        candidate_id="1",
        question_id="q-context",
        category=AssessmentCategory.DECLARED_OPERATIONAL_POLICY,
        protocol=_protocol("operational-review"),
        as_of_key=universe.decision_key,
        evidence_reference_ids=(unknown, event),
        conflicting_reference_ids=(event,),
        unknown_reference_ids=(unknown,),
        provisional_status=ProvisionalStatus.PROVISIONAL,
        reason="Declared operational review remains provisional; reference classes are not empirical labels.",
        declaration_reference="policy:review-rule-1",
    )
    pair = ledger.assessments_for("1", "q-context")
    assert len(pair) == 2
    assert all(item.provisional_status is ProvisionalStatus.PROVISIONAL for item in pair)
    assert pair[1].previous_assessment_id == first.assessment_id
    assert pair[0].category is AssessmentCategory.DECLARED_HUMAN_ASSESSMENT
    assert pair[1].category is AssessmentCategory.DECLARED_OPERATIONAL_POLICY
    assert pair[1].conflicting_reference_ids == (event,)
    assert pair[1].unknown_reference_ids == (unknown,)


def test_later_revision_contains_only_new_asof_lifecycle_evidence(_b2_sources):
    universe = _universe(_b2_sources)
    surface = _b2_sources[4]["FVG"]
    candidate_id = _candidate_with_later_event(universe, surface)
    ledger = _append_initial_assessment(_ledger(universe), candidate_id)
    candidate = universe.candidate(candidate_id)
    later_key = _key(_b2_sources, 20)
    batch = retrieve_new_fvg_factual_evidence(
        universe=universe,
        candidate_id=candidate_id,
        timeline=_b2_sources[2],
        adapter=_b2_sources[1],
        market_history=_b2_sources[0],
        fvg_surface=surface,
        start_key=universe.decision_key,
        as_of_key=later_key,
    )
    assert batch.evidence
    assert all(universe.decision_key < ref.available_at <= later_key for ref in batch.evidence)
    assert all(ref.evidence_kind == pilot.FVG_EVENT_EVIDENCE_KIND for ref in batch.evidence)
    old = ledger.assessments[0]
    new_ids = tuple(item.reference_id for item in batch.evidence)
    ledger2 = revise_candidate_assessment(
        ledger=ledger,
        candidate_id=candidate_id,
        question_id="q-context",
        category=AssessmentCategory.UNKNOWN,
        protocol=_protocol("later-review"),
        evidence_batch=batch,
        evidence_reference_ids=(candidate.entity_evidence.reference_id, *new_ids),
        unknown_reference_ids=new_ids,
        provisional_status=ProvisionalStatus.UNKNOWN,
        reason="New source lifecycle rows are factual; their investigation meaning remains unknown.",
    )
    revision = ledger2.assessments[-1]
    assert revision.previous_assessment_id == old.assessment_id
    assert revision.new_evidence_reference_ids == new_ids
    assert revision.as_of_key == later_key
    assert revision.category is AssessmentCategory.UNKNOWN


def test_historical_assessment_records_are_immutable(_b2_sources):
    universe = _universe(_b2_sources)
    surface = _b2_sources[4]["FVG"]
    candidate_id = _candidate_with_later_event(universe, surface)
    ledger = _append_initial_assessment(_ledger(universe), candidate_id)
    old = ledger.assessments[0]
    later_key = _key(_b2_sources, 20)
    batch = retrieve_new_fvg_factual_evidence(
        universe=universe,
        candidate_id=candidate_id,
        timeline=_b2_sources[2],
        adapter=_b2_sources[1],
        market_history=_b2_sources[0],
        fvg_surface=surface,
        start_key=universe.decision_key,
        as_of_key=later_key,
    )
    refs = tuple(item.reference_id for item in batch.evidence)
    ledger2 = revise_candidate_assessment(
        ledger=ledger,
        candidate_id=candidate_id,
        question_id="q-context",
        category=AssessmentCategory.UNKNOWN,
        protocol=_protocol("immutable-revision"),
        evidence_batch=batch,
        evidence_reference_ids=(old.evidence_reference_ids[0], *refs),
        unknown_reference_ids=refs,
        provisional_status=ProvisionalStatus.UNKNOWN,
        reason="Append new facts without rewriting the first record.",
    )
    assert ledger.assessments[0] is old
    assert ledger2.assessments[0] is old
    assert ledger2.assessments[0].assessment_id == old.assessment_id
    with pytest.raises(FrozenInstanceError):
        old.reason = "rewritten"


def test_deferred_candidate_can_be_restored_for_investigation_only(_b2_sources):
    universe = _universe(_b2_sources)
    ledger = _ledger(universe)
    ledger = record_candidate_coverage(
        ledger=ledger,
        candidate_id="0",
        question_id="q-context",
        state=CandidateCoverageState.DEFERRED,
        as_of_key=universe.decision_key,
        reason="Explicitly deferred; no irrelevance judgment.",
    )
    before_assessments = ledger.assessments
    restored = restore_deferred_candidate(
        ledger=ledger,
        candidate_id="0",
        question_id="q-context",
        as_of_key=universe.decision_key,
        reason="Re-open for contextual review.",
    )
    state = restored.latest_coverage("0", "q-context")
    assert state.state is CandidateCoverageState.REGISTERED
    assert state.restoration_is_not_utility_evidence
    assert "not evidence of trading utility" in state.reason
    assert restored.assessments == before_assessments


def test_pilot_has_no_universal_score_and_rejects_empirical_relevance(_b2_sources):
    universe = _universe(_b2_sources)
    ledger = _ledger(universe)
    record_fields = {item.name for item in fields(pilot.CandidateAssessmentRecord)}
    context_fields = {item.name for item in fields(pilot.CandidateContext)}
    assert not any("score" in name.lower() for name in record_fields | context_fields)
    assert not any("score" in name.lower() for name in pilot.__all__)
    candidate = universe.candidate("0")
    with pytest.raises(CandidatePilotError, match="cannot generate empirically validated relevance"):
        append_candidate_assessment(
            ledger=ledger,
            candidate_id="0",
            question_id="q-context",
            category=AssessmentCategory.EMPIRICALLY_VALIDATED_RELEVANCE,
            protocol=_protocol(),
            as_of_key=universe.decision_key,
            evidence_reference_ids=(candidate.entity_evidence.reference_id,),
            supporting_reference_ids=(candidate.entity_evidence.reference_id,),
            provisional_status=ProvisionalStatus.PROVISIONAL,
            reason="This category is reserved for independently validated evidence.",
        )


def test_pilot_exposes_no_prediction_or_trade_signal_and_keeps_s8_s9_blockers(_b2_sources):
    forbidden = ("predict", "probability", "trade_signal", "execution", "model")
    assert not any(any(token in name.lower() for token in forbidden) for name in pilot.__all__)
    assert not any(item.name.lower() in {"prediction", "probability", "trade_signal"} for item in fields(pilot.CandidateAssessmentRecord))
    assert any("COMPETING_BOUNDARY_FIRST_PASSAGE" in item and "BLOCKED" in item for item in UNSAFE_BLOCKER_DECLARATIONS)
    assert any("SATISFY_CONSTRAINT" in item and "BLOCKED" in item for item in UNSAFE_BLOCKER_DECLARATIONS)


def test_append_keeps_registered_historical_prefix_and_prior_ids_stable(_b2_sources):
    universe = _universe(_b2_sources)
    surface = _b2_sources[4]["FVG"]
    candidate_id = _candidate_with_later_event(universe, surface)
    ledger = _append_initial_assessment(_ledger(universe), candidate_id)
    before = (
        universe.universe_id,
        universe.decision_market_prefix_hash,
        universe.source_prefix_hash,
        universe.candidate(candidate_id).context_id,
        ledger.assessments[0].assessment_id,
    )
    later_key = _key(_b2_sources, 20)
    batch = retrieve_new_fvg_factual_evidence(
        universe=universe,
        candidate_id=candidate_id,
        timeline=_b2_sources[2],
        adapter=_b2_sources[1],
        market_history=_b2_sources[0],
        fvg_surface=surface,
        start_key=universe.decision_key,
        as_of_key=later_key,
    )
    refs = tuple(item.reference_id for item in batch.evidence)
    ledger2 = revise_candidate_assessment(
        ledger=ledger,
        candidate_id=candidate_id,
        question_id="q-context",
        category=AssessmentCategory.UNKNOWN,
        protocol=_protocol("append-check"),
        evidence_batch=batch,
        evidence_reference_ids=(ledger.assessments[0].evidence_reference_ids[0], *refs),
        unknown_reference_ids=refs,
        provisional_status=ProvisionalStatus.UNKNOWN,
        reason="The registration snapshot and first assessment remain historical records.",
    )
    after = (
        ledger2.universe.universe_id,
        ledger2.universe.decision_market_prefix_hash,
        ledger2.universe.source_prefix_hash,
        ledger2.universe.candidate(candidate_id).context_id,
        ledger2.assessments[0].assessment_id,
    )
    assert before == after
    assert ledger2.assessments[1].previous_assessment_id == before[-1]


def test_mutated_source_surface_or_market_fails_closed(_b2_sources):
    universe = _universe(_b2_sources)
    surface = _b2_sources[4]["FVG"]
    candidate_id = _candidate_with_later_event(universe, surface)
    mutated_surface = replace(surface, normalized_event_frame=surface.normalized_event_frame.copy(deep=True))
    mutated_surface.normalized_event_frame.loc[0, "event_type"] = "MUTATED_EVENT"
    with pytest.raises(CandidatePilotError, match="verification failed closed"):
        retrieve_new_fvg_factual_evidence(
            universe=universe,
            candidate_id=candidate_id,
            timeline=_b2_sources[2],
            adapter=_b2_sources[1],
            market_history=_b2_sources[0],
            fvg_surface=mutated_surface,
            start_key=universe.decision_key,
            as_of_key=_key(_b2_sources, 20),
        )
    mutated_market = _b2_sources[0].copy(deep=True)
    mutated_market.iloc[3, mutated_market.columns.get_loc("close")] += 0.25
    with pytest.raises(CandidatePilotError, match="verification failed closed"):
        retrieve_new_fvg_factual_evidence(
            universe=universe,
            candidate_id=candidate_id,
            timeline=_b2_sources[2],
            adapter=_b2_sources[1],
            market_history=mutated_market,
            fvg_surface=surface,
            start_key=universe.decision_key,
            as_of_key=_key(_b2_sources, 20),
        )


def test_registration_coverage_reconciles_exactly_to_eligible_universe(_b2_sources):
    universe = _universe(_b2_sources, position=20)
    ledger = _ledger(universe)
    for candidate_id, state in (
        ("0", CandidateCoverageState.NOT_EVALUATED),
        ("1", CandidateCoverageState.UNRESOLVED),
        ("2", CandidateCoverageState.DEFERRED),
    ):
        ledger = record_candidate_coverage(
            ledger=ledger,
            candidate_id=candidate_id,
            question_id="q-context",
            state=state,
            as_of_key=universe.decision_key,
            reason=f"Explicit {state.value}; not an irrelevance finding.",
        )
    ledger = _append_initial_assessment(ledger, "3")
    reconciliation = reconcile_candidate_coverage(ledger=ledger, question_id="q-context")
    counts = dict(reconciliation.state_counts)
    assert reconciliation.reconciled
    assert reconciliation.eligible_candidate_ids == universe.eligible_candidate_ids
    assert reconciliation.accounted_candidate_ids == universe.eligible_candidate_ids
    assert reconciliation.missing_candidate_ids == ()
    assert reconciliation.extra_candidate_ids == ()
    assert counts[CandidateCoverageState.REGISTERED.value] == len(universe.candidates) - 4
    assert counts[CandidateCoverageState.ASSESSED.value] == 1
    assert counts[CandidateCoverageState.DEFERRED.value] == 1
    assert counts[CandidateCoverageState.UNRESOLVED.value] == 1
    assert counts[CandidateCoverageState.NOT_EVALUATED.value] == 1
    assert sum(counts.values()) == len(universe.candidates)
