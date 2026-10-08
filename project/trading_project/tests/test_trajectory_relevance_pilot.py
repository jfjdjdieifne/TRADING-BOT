from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
import inspect
import pickle

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
    VerifiedCandidateResearchLedger,
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
    verify_candidate_research_ledger,
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


def _verify_ledger(ledger, sources):
    if isinstance(ledger, VerifiedCandidateResearchLedger):
        return ledger
    return verify_candidate_research_ledger(
        ledger=ledger,
        timeline=sources[2],
        adapter=sources[1],
        market_history=sources[0],
        fvg_surface=sources[4]["FVG"],
    )


def _append_initial_assessment(
    ledger, candidate_id: str, sources, question_id: str = "q-context"
):
    ledger = _verify_ledger(ledger, sources)
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


def _revision_inputs(
    ledger,
    sources,
    candidate_id: str,
    as_of_key,
    *,
    protocol_id: str = "later-review",
    category: AssessmentCategory = AssessmentCategory.UNKNOWN,
    provisional_status: ProvisionalStatus = ProvisionalStatus.UNKNOWN,
    reason: str = "New source facts remain explicitly unknown for this question.",
    **overrides,
):
    inputs = {
        "ledger": ledger,
        "candidate_id": candidate_id,
        "question_id": "q-context",
        "category": category,
        "protocol": _protocol(protocol_id),
        "as_of_key": as_of_key,
        "timeline": sources[2],
        "adapter": sources[1],
        "market_history": sources[0],
        "fvg_surface": sources[4]["FVG"],
        "provisional_status": provisional_status,
        "reason": reason,
    }
    inputs.update(overrides)
    return inputs


def _revise(ledger, sources, candidate_id: str, as_of_key, **kwargs):
    return revise_candidate_assessment(**_revision_inputs(ledger, sources, candidate_id, as_of_key, **kwargs))


def _candidate_with_later_event(universe, surface, start_position: int = 7) -> str:
    candidate_ids = set(universe.eligible_candidate_ids)
    later = surface.normalized_event_frame
    later = later[(later["event_position"] > start_position) & later["fvg_id"].astype(str).isin(candidate_ids)]
    assert not later.empty, "the existing synthetic FVG fixture must expose a later lifecycle event"
    return str(later.iloc[0]["fvg_id"])


def _row_with_cell(ref, column: str, kind, value):
    row = list(ref.row)
    row[ref.row_columns.index(column)] = pilot.FrozenCell(kind, value)
    return tuple(row)


def _reference_variant(ref, **overrides):
    values = {
        "candidate_id": ref.candidate_id,
        "evidence_kind": ref.evidence_kind,
        "producer_domain": ref.producer_domain,
        "source_binding_hash": ref.source_binding_hash,
        "source_prefix_hash": ref.source_prefix_hash,
        "available_at": ref.available_at,
        "row_columns": ref.row_columns,
        "row": ref.row,
    }
    values.update(overrides)
    return pilot._make_evidence_reference(**values)


def _batch_variant(batch, evidence, **overrides):
    values = {
        "case_id": batch.case_id,
        "candidate_id": batch.candidate_id,
        "source_binding_hash": batch.source_binding_hash,
        "start_key": batch.start_key,
        "as_of_key": batch.as_of_key,
        "source_prefix_hash": batch.source_prefix_hash,
        "asof_view_hash": batch.asof_view_hash,
        "evidence": tuple(evidence),
    }
    values.update(overrides)
    values["batch_id"] = pilot._evidence_batch_id(
        case_id=values["case_id"],
        candidate_id=values["candidate_id"],
        source_binding_hash=values["source_binding_hash"],
        start_key=values["start_key"],
        as_of_key=values["as_of_key"],
        source_prefix_hash=values["source_prefix_hash"],
        asof_view_hash=values["asof_view_hash"],
        reference_ids=tuple(ref.reference_id for ref in values["evidence"]),
    )
    return pilot.EvidenceBatch(**values)


def _forged_source_revision_record(
    verified, sources, candidate_id, as_of_key, *, mutation="event_type"
):
    """Build self-hashed history whose event row/metadata is not source exact."""
    raw = object.__getattribute__(verified, "_record")
    previous = raw.latest_assessment(candidate_id, "q-context")
    assert previous is not None
    source_batch = retrieve_new_fvg_factual_evidence(
        universe=raw.universe,
        candidate_id=candidate_id,
        timeline=sources[2],
        adapter=sources[1],
        market_history=sources[0],
        fvg_surface=sources[4]["FVG"],
        start_key=previous.as_of_key,
        as_of_key=as_of_key,
    )
    assert source_batch.evidence
    original_ref = source_batch.evidence[0]
    batch_overrides = {}
    if mutation == "event_type":
        forged_ref = _reference_variant(
            original_ref,
            row=_row_with_cell(
                original_ref,
                "event_type",
                pilot.FrozenCellKind.STRING,
                "FABRICATED_SOURCE_EVENT",
            ),
        )
    elif mutation == "event_position":
        first_position = source_batch.start_key.bar_position + 1
        last_position = source_batch.as_of_key.bar_position
        old_position = original_ref.available_at.bar_position
        replacement_position = old_position + 1 if old_position < last_position else old_position - 1
        assert first_position <= replacement_position <= last_position
        forged_ref = _reference_variant(
            original_ref,
            available_at=_key(sources, replacement_position),
            row=_row_with_cell(
                original_ref,
                "event_position",
                pilot.FrozenCellKind.NUMBER,
                str(replacement_position),
            ),
        )
    elif mutation == "source_prefix_hash":
        stale_prefix = "e" * 64
        forged_ref = _reference_variant(original_ref, source_prefix_hash=stale_prefix)
        batch_overrides["source_prefix_hash"] = stale_prefix
    else:
        raise AssertionError(f"unknown forged-history mutation: {mutation}")
    forged_batch = _batch_variant(source_batch, (forged_ref,), **batch_overrides)
    new_ids = (forged_ref.reference_id,)
    assessment = pilot._make_assessment(
        candidate_id=candidate_id,
        candidate_identity_hash=raw.universe.candidate(candidate_id).candidate_identity_hash,
        question=raw.questions[0],
        category=AssessmentCategory.UNKNOWN,
        protocol=_protocol("forged-history"),
        as_of_key=as_of_key,
        evidence_reference_ids=tuple(dict.fromkeys((*previous.evidence_reference_ids, *new_ids))),
        supporting_reference_ids=(),
        conflicting_reference_ids=(),
        unknown_reference_ids=new_ids,
        provisional_status=ProvisionalStatus.UNKNOWN,
        reason="Self-hashed but not present in the Stage4B2 source.",
        declaration_reference=None,
        previous_assessment_id=previous.assessment_id,
        new_evidence_reference_ids=new_ids,
        evidence_batch_id=forged_batch.batch_id,
    )
    latest_coverage = raw.latest_coverage(candidate_id, "q-context")
    coverage = pilot._make_coverage(
        candidate_id=candidate_id,
        question_id="q-context",
        state=CandidateCoverageState.UNRESOLVED,
        as_of_key=as_of_key,
        reason="Fabricated revision remains unverified.",
        assessment_id=None,
        previous_coverage_id=latest_coverage.coverage_id,
    )
    # Direct construction intentionally succeeds: structural self-consistency
    # is exactly what must not be mistaken for source authenticity.
    return CandidateResearchLedger(
        universe=raw.universe,
        questions=raw.questions,
        assessments=raw.assessments + (assessment,),
        coverage_history=raw.coverage_history + (coverage,),
        factual_evidence=raw.factual_evidence + (forged_ref,),
        evidence_batches=raw.evidence_batches + (forged_batch,),
    )


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
    prefix_sources = (prefix_market, prefix_adapter, prefix_timeline, None, {"FVG": prefix_surface})
    assert full_universe.case_id == prefix_universe.case_id
    assert full_universe == prefix_universe
    assert full_universe.universe_id == prefix_universe.universe_id
    assert full_universe.source_prefix_hash == prefix_universe.source_prefix_hash
    assert full_universe.eligible_candidate_ids == prefix_universe.eligible_candidate_ids
    assert full_universe.candidate("0").candidate_identity_hash == prefix_universe.candidate("0").candidate_identity_hash
    assert full_universe.candidate("0").source_provenance.source_surface_id != prefix_universe.candidate("0").source_provenance.source_surface_id

    question = _question()
    full_ledger = _append_initial_assessment(_ledger(full_universe, question), "0", _b2_sources)
    prefix_ledger = _append_initial_assessment(_ledger(prefix_universe, question), "0", prefix_sources)
    assert full_ledger.assessments[0].assessment_id == prefix_ledger.assessments[0].assessment_id
    assert pickle.dumps(full_ledger.assessments[0], protocol=5) == pickle.dumps(
        prefix_ledger.assessments[0], protocol=5
    )


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
    ledger = _verify_ledger(_ledger(universe, q_one, q_two), _b2_sources)
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
    ledger = _verify_ledger(_ledger(universe), _b2_sources)
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
    ledger = _append_initial_assessment(_ledger(universe), candidate_id, _b2_sources)
    candidate_identity_before = universe.candidate(candidate_id).candidate_identity_hash
    question_identity_before = ledger.questions[0].identity_hash
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
    assert all(ref.producer_domain == "FVG" for ref in batch.evidence)
    assert all(ref.source_binding_hash == universe.source_binding_hash for ref in batch.evidence)
    assert all(ref.source_prefix_hash == batch.source_prefix_hash for ref in batch.evidence)
    assert all(ref.row_columns == tuple(surface.normalized_event_frame.columns) for ref in batch.evidence)
    assert all(
        dict(zip(ref.row_columns, ref.row))["fvg_id"].value == candidate_id
        and dict(zip(ref.row_columns, ref.row))["event_position"].value == str(ref.available_at.bar_position)
        for ref in batch.evidence
    )
    old = ledger.assessments[0]
    new_ids = tuple(item.reference_id for item in batch.evidence)
    ledger2 = _revise(
        ledger,
        _b2_sources,
        candidate_id,
        later_key,
        protocol_id="later-review",
        category=AssessmentCategory.UNKNOWN,
        unknown_reference_ids=new_ids,
        reason="New source lifecycle rows are factual; their investigation meaning remains unknown.",
    )
    revision = ledger2.assessments[-1]
    assert revision.previous_assessment_id == old.assessment_id
    assert revision.new_evidence_reference_ids == new_ids
    assert revision.evidence_batch_id == batch.batch_id
    assert set(new_ids).issubset(revision.unknown_reference_ids)
    assert revision.as_of_key == later_key
    assert revision.category is AssessmentCategory.UNKNOWN
    assert ledger2.universe.candidate(candidate_id).candidate_identity_hash == candidate_identity_before
    assert ledger2.questions[0].identity_hash == question_identity_before


def test_fabricated_future_or_invalid_positions_fail_evidence_batch_validation(_b2_sources):
    universe = _universe(_b2_sources)
    candidate_id = _candidate_with_later_event(universe, _b2_sources[4]["FVG"])
    batch = retrieve_new_fvg_factual_evidence(
        universe=universe,
        candidate_id=candidate_id,
        timeline=_b2_sources[2],
        adapter=_b2_sources[1],
        market_history=_b2_sources[0],
        fvg_surface=_b2_sources[4]["FVG"],
        start_key=universe.decision_key,
        as_of_key=_key(_b2_sources, 20),
    )
    ref = batch.evidence[0]
    future_ref = _reference_variant(
        ref,
        available_at=_key(_b2_sources, 89),
        row=_row_with_cell(ref, "event_position", pilot.FrozenCellKind.NUMBER, "89"),
    )
    with pytest.raises(CandidatePilotError, match="outside its causal interval"):
        _batch_variant(batch, (future_ref,))

    negative_position_ref = _reference_variant(
        ref,
        row=_row_with_cell(ref, "event_position", pilot.FrozenCellKind.NUMBER, "-1"),
    )
    with pytest.raises(CandidatePilotError, match="nonnegative integer position"):
        _batch_variant(batch, (negative_position_ref,))


def test_unrelated_candidate_and_non_fvg_producer_rows_are_rejected(_b2_sources):
    universe = _universe(_b2_sources)
    candidate_id = _candidate_with_later_event(universe, _b2_sources[4]["FVG"])
    batch = retrieve_new_fvg_factual_evidence(
        universe=universe,
        candidate_id=candidate_id,
        timeline=_b2_sources[2],
        adapter=_b2_sources[1],
        market_history=_b2_sources[0],
        fvg_surface=_b2_sources[4]["FVG"],
        start_key=universe.decision_key,
        as_of_key=_key(_b2_sources, 20),
    )
    ref = batch.evidence[0]
    unrelated_id = _reference_variant(
        ref,
        row=_row_with_cell(ref, "fvg_id", pilot.FrozenCellKind.STRING, "unrelated-fvg-id"),
    )
    with pytest.raises(CandidatePilotError, match="another canonical FVG ID"):
        _batch_variant(batch, (unrelated_id,))

    wrong_producer = _reference_variant(ref, producer_domain="LIQUIDITY")
    with pytest.raises(CandidatePilotError, match="only this candidate's FVG lifecycle events"):
        _batch_variant(batch, (wrong_producer,))


def test_stale_batch_binding_and_prefix_metadata_are_rejected(_b2_sources):
    universe = _universe(_b2_sources)
    candidate_id = _candidate_with_later_event(universe, _b2_sources[4]["FVG"])
    ledger = _append_initial_assessment(_ledger(universe), candidate_id, _b2_sources)
    batch = retrieve_new_fvg_factual_evidence(
        universe=universe,
        candidate_id=candidate_id,
        timeline=_b2_sources[2],
        adapter=_b2_sources[1],
        market_history=_b2_sources[0],
        fvg_surface=_b2_sources[4]["FVG"],
        start_key=universe.decision_key,
        as_of_key=_key(_b2_sources, 20),
    )
    for field_name, stale_hash in (
        ("source_binding_hash", "a" * 64),
        ("source_prefix_hash", "b" * 64),
    ):
        with pytest.raises(CandidatePilotError, match="per-reference source"):
            _batch_variant(batch, batch.evidence, **{field_name: stale_hash})

    stale_binding = "d" * 64
    stale_prefix = "e" * 64
    stale_ref = _reference_variant(
        batch.evidence[0],
        source_binding_hash=stale_binding,
        source_prefix_hash=stale_prefix,
    )
    self_consistent_stale_batch = _batch_variant(
        batch,
        (stale_ref,),
        source_binding_hash=stale_binding,
        source_prefix_hash=stale_prefix,
    )
    inputs = _revision_inputs(ledger, _b2_sources, candidate_id, _key(_b2_sources, 20))
    with pytest.raises(TypeError, match="evidence_batch"):
        revise_candidate_assessment(**inputs, evidence_batch=self_consistent_stale_batch)


def test_per_reference_binding_must_match_valid_universe_binding(_b2_sources):
    universe = _universe(_b2_sources)
    candidate_id = _candidate_with_later_event(universe, _b2_sources[4]["FVG"])
    batch = retrieve_new_fvg_factual_evidence(
        universe=universe,
        candidate_id=candidate_id,
        timeline=_b2_sources[2],
        adapter=_b2_sources[1],
        market_history=_b2_sources[0],
        fvg_surface=_b2_sources[4]["FVG"],
        start_key=universe.decision_key,
        as_of_key=_key(_b2_sources, 20),
    )
    assert batch.source_binding_hash == universe.source_binding_hash
    stale_ref = _reference_variant(batch.evidence[0], source_binding_hash="c" * 64)
    with pytest.raises(CandidatePilotError, match="per-reference source binding"):
        _batch_variant(batch, (stale_ref,))


def test_availability_position_mismatch_is_rejected(_b2_sources):
    universe = _universe(_b2_sources)
    candidate_id = _candidate_with_later_event(universe, _b2_sources[4]["FVG"])
    batch = retrieve_new_fvg_factual_evidence(
        universe=universe,
        candidate_id=candidate_id,
        timeline=_b2_sources[2],
        adapter=_b2_sources[1],
        market_history=_b2_sources[0],
        fvg_surface=_b2_sources[4]["FVG"],
        start_key=universe.decision_key,
        as_of_key=_key(_b2_sources, 20),
    )
    ref = batch.evidence[0]
    mismatched = _reference_variant(ref, available_at=_key(_b2_sources, ref.available_at.bar_position + 1))
    with pytest.raises(CandidatePilotError, match="event position and claimed availability position disagree"):
        _batch_variant(batch, (mismatched,))


def test_empty_and_duplicate_batches_cannot_create_a_revision(_b2_sources):
    universe = _universe(_b2_sources)
    candidate_id = _candidate_with_later_event(universe, _b2_sources[4]["FVG"])
    source_batch = retrieve_new_fvg_factual_evidence(
        universe=universe,
        candidate_id=candidate_id,
        timeline=_b2_sources[2],
        adapter=_b2_sources[1],
        market_history=_b2_sources[0],
        fvg_surface=_b2_sources[4]["FVG"],
        start_key=universe.decision_key,
        as_of_key=_key(_b2_sources, 20),
    )
    empty = _batch_variant(source_batch, ())
    assert empty.evidence == ()
    ref = source_batch.evidence[0]
    with pytest.raises(CandidatePilotError, match="duplicate references"):
        _batch_variant(source_batch, (ref, ref))

    no_event_candidate_id = "0"
    ledger = _append_initial_assessment(_ledger(universe), no_event_candidate_id, _b2_sources)
    unchanged = ledger
    with pytest.raises(CandidatePilotError, match="no eligible new FVG factual evidence"):
        _revise(ledger, _b2_sources, no_event_candidate_id, _key(_b2_sources, 20))
    assert ledger is unchanged
    assert ledger.evidence_batches == ()


def test_self_rehashed_non_source_row_cannot_enter_public_revision_api(_b2_sources):
    universe = _universe(_b2_sources)
    candidate_id = _candidate_with_later_event(universe, _b2_sources[4]["FVG"])
    ledger = _append_initial_assessment(_ledger(universe), candidate_id, _b2_sources)
    source_batch = retrieve_new_fvg_factual_evidence(
        universe=universe,
        candidate_id=candidate_id,
        timeline=_b2_sources[2],
        adapter=_b2_sources[1],
        market_history=_b2_sources[0],
        fvg_surface=_b2_sources[4]["FVG"],
        start_key=universe.decision_key,
        as_of_key=_key(_b2_sources, 20),
    )
    ref = source_batch.evidence[0]
    forged_ref = _reference_variant(
        ref,
        row=_row_with_cell(ref, "event_type", pilot.FrozenCellKind.STRING, "FABRICATED_SOURCE_EVENT"),
    )
    forged_batch = _batch_variant(source_batch, (forged_ref,))
    assert forged_ref.row != ref.row
    assert forged_ref.row_sha256 != ref.row_sha256
    assert forged_batch.batch_id != source_batch.batch_id
    assert "evidence_batch" not in inspect.signature(revise_candidate_assessment).parameters
    assert "evidence_batch" not in inspect.signature(append_candidate_assessment).parameters

    inputs = _revision_inputs(ledger, _b2_sources, candidate_id, _key(_b2_sources, 20))
    with pytest.raises(TypeError, match="evidence_batch"):
        revise_candidate_assessment(**inputs, evidence_batch=forged_batch)
    with pytest.raises(TypeError, match="evidence_batch"):
        append_candidate_assessment(
            ledger=ledger,
            candidate_id=candidate_id,
            question_id="q-context",
            category=AssessmentCategory.UNKNOWN,
            protocol=_protocol("batch-rejection"),
            as_of_key=universe.decision_key,
            evidence_reference_ids=(universe.candidate(candidate_id).entity_evidence.reference_id,),
            reason="Caller-authored evidence batches are not accepted.",
            evidence_batch=forged_batch,
        )


def test_revision_cannot_replay_prior_interval_evidence(_b2_sources):
    universe = _universe(_b2_sources)
    candidate_id = _candidate_with_later_event(universe, _b2_sources[4]["FVG"])
    ledger = _append_initial_assessment(_ledger(universe), candidate_id, _b2_sources)
    first_key = _key(_b2_sources, 20)
    first_revision = _revise(ledger, _b2_sources, candidate_id, first_key)
    first_ids = set(first_revision.assessments[-1].new_evidence_reference_ids)

    second_key = _key(_b2_sources, 82)
    second_revision = _revise(first_revision, _b2_sources, candidate_id, second_key, protocol_id="later-again")
    second_ids = set(second_revision.assessments[-1].new_evidence_reference_ids)
    assert first_ids
    assert second_ids
    assert first_ids.isdisjoint(second_ids)
    assert second_revision.evidence_batches[-1].start_key == first_key
    assert all(first_key < ref.available_at <= second_key for ref in second_revision.evidence_batches[-1].evidence)
    with pytest.raises(CandidatePilotError, match="must advance beyond the prior assessment"):
        _revise(second_revision, _b2_sources, candidate_id, second_key)


def test_same_information_batch_ambiguity_is_preserved_without_order_inference(_b2_sources):
    universe = _universe(_b2_sources)
    candidate_id = "0"
    ledger = _append_initial_assessment(_ledger(universe), candidate_id, _b2_sources)
    as_of_key = _key(_b2_sources, 82)
    batch = retrieve_new_fvg_factual_evidence(
        universe=universe,
        candidate_id=candidate_id,
        timeline=_b2_sources[2],
        adapter=_b2_sources[1],
        market_history=_b2_sources[0],
        fvg_surface=_b2_sources[4]["FVG"],
        start_key=universe.decision_key,
        as_of_key=as_of_key,
    )
    ambiguous_rows = [
        ref for ref in batch.evidence
        if dict(zip(ref.row_columns, ref.row))["event_position"].value == "81"
    ]
    assert len(ambiguous_rows) >= 2
    assert all(
        dict(zip(ref.row_columns, ref.row))["same_information_batch_order_unknown"]
        == pilot.FrozenCell(pilot.FrozenCellKind.BOOLEAN, True)
        for ref in ambiguous_rows
    )

    revised = _revise(ledger, _b2_sources, candidate_id, as_of_key)
    revision = revised.assessments[-1]
    assert set(revision.new_evidence_reference_ids) == {ref.reference_id for ref in batch.evidence}
    assert set(revision.new_evidence_reference_ids).issubset(revision.unknown_reference_ids)
    assert revision.supporting_reference_ids == ()
    assert revision.conflicting_reference_ids == ()
    assert all(
        dict(zip(ref.row_columns, ref.row))["same_information_batch_order_unknown"].kind
        is pilot.FrozenCellKind.BOOLEAN
        for ref in revised.evidence_batches[-1].evidence
    )


def test_revision_reuses_the_verified_surface_without_closed_engine_replay(_b2_sources, monkeypatch):
    universe = _universe(_b2_sources)
    candidate_id = _candidate_with_later_event(universe, _b2_sources[4]["FVG"])
    ledger = _append_initial_assessment(_ledger(universe), candidate_id, _b2_sources)

    def forbidden_replay(**kwargs):
        pytest.fail("revision must not replay the closed Stage4B2 producer")

    monkeypatch.setattr(s4b2, "build_fvg_surface", forbidden_replay)
    revised = _revise(ledger, _b2_sources, candidate_id, _key(_b2_sources, 20))
    assert revised.assessments[-1].new_evidence_reference_ids


def test_historical_assessment_records_are_immutable(_b2_sources):
    universe = _universe(_b2_sources)
    surface = _b2_sources[4]["FVG"]
    candidate_id = _candidate_with_later_event(universe, surface)
    ledger = _append_initial_assessment(_ledger(universe), candidate_id, _b2_sources)
    old = ledger.assessments[0]
    old_bytes = pickle.dumps(old, protocol=5)
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
    ledger2 = _revise(
        ledger,
        _b2_sources,
        candidate_id,
        later_key,
        protocol_id="immutable-revision",
        unknown_reference_ids=refs,
        reason="Append new facts without rewriting the first record.",
    )
    assert ledger.assessments[0] is old
    assert ledger2.assessments[0] is old
    assert ledger2.assessments[0].assessment_id == old.assessment_id
    assert pickle.dumps(ledger2.assessments[0], protocol=5) == old_bytes
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
    ledger = _verify_ledger(_ledger(universe), _b2_sources)
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
    ledger = _append_initial_assessment(_ledger(universe), candidate_id, _b2_sources)
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
    ledger2 = _revise(
        ledger,
        _b2_sources,
        candidate_id,
        later_key,
        protocol_id="append-check",
        unknown_reference_ids=refs,
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


def test_mutated_or_missing_source_fails_closed_without_appending(_b2_sources):
    universe = _universe(_b2_sources)
    surface = _b2_sources[4]["FVG"]
    candidate_id = _candidate_with_later_event(universe, surface)
    ledger = _append_initial_assessment(_ledger(universe), candidate_id, _b2_sources)
    initial_assessments = ledger.assessments
    later_key = _key(_b2_sources, 20)
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
            as_of_key=later_key,
        )
    with pytest.raises(CandidatePilotError, match="verification failed closed"):
        _revise(ledger, _b2_sources, candidate_id, later_key, fvg_surface=mutated_surface)

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
            as_of_key=later_key,
        )
    with pytest.raises(CandidatePilotError, match="verification failed closed"):
        _revise(ledger, _b2_sources, candidate_id, later_key, market_history=mutated_market)
    with pytest.raises(CandidatePilotError, match="public Stage4B2 FVG surface"):
        _revise(ledger, _b2_sources, candidate_id, later_key, fvg_surface=None)
    assert ledger.assessments is initial_assessments
    assert ledger.evidence_batches == ()


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
    ledger = _append_initial_assessment(ledger, "3", _b2_sources)
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


def test_direct_ledger_construction_is_raw_and_rejected_by_factual_consumers(_b2_sources):
    universe = _universe(_b2_sources)
    initial = _ledger(universe)
    raw = CandidateResearchLedger(
        universe=initial.universe,
        questions=initial.questions,
        assessments=initial.assessments,
        coverage_history=initial.coverage_history,
        factual_evidence=initial.factual_evidence,
        evidence_batches=initial.evidence_batches,
    )
    assert isinstance(raw, CandidateResearchLedger)
    assert not isinstance(raw, VerifiedCandidateResearchLedger)

    candidate_id = universe.eligible_candidate_ids[0]
    candidate = universe.candidate(candidate_id)
    append_args = dict(
        ledger=raw,
        candidate_id=candidate_id,
        question_id="q-context",
        category=AssessmentCategory.FACTUAL_CONTEXT,
        protocol=_protocol("raw-must-not-append"),
        as_of_key=universe.decision_key,
        evidence_reference_ids=(candidate.entity_evidence.reference_id,),
        reason="Raw records must not be treated as verified source history.",
    )
    with pytest.raises(CandidatePilotError, match="source-verified.*raw ledgers"):
        append_candidate_assessment(**append_args)
    with pytest.raises(CandidatePilotError, match="source-verified.*raw ledgers"):
        revise_candidate_assessment(
            **_revision_inputs(raw, _b2_sources, candidate_id, _key(_b2_sources, 20))
        )
    with pytest.raises(CandidatePilotError, match="source-verified.*raw ledgers"):
        pilot._append_candidate_assessment_record(**append_args)


def test_valid_source_backed_ledger_and_historical_revision_reverify(_b2_sources):
    universe = _universe(_b2_sources)
    candidate_id = _candidate_with_later_event(universe, _b2_sources[4]["FVG"])
    verified_initial = _append_initial_assessment(_ledger(universe), candidate_id, _b2_sources)
    assert isinstance(verified_initial, VerifiedCandidateResearchLedger)

    initial_record = object.__getattribute__(verified_initial, "_record")
    reverified_initial = _verify_ledger(initial_record, _b2_sources)
    assert isinstance(reverified_initial, VerifiedCandidateResearchLedger)
    assert reverified_initial.assessments == verified_initial.assessments
    assert reverified_initial.factual_evidence == verified_initial.factual_evidence

    later_key = _key(_b2_sources, 20)
    revised = _revise(verified_initial, _b2_sources, candidate_id, later_key)
    assert isinstance(revised, VerifiedCandidateResearchLedger)
    assert len(revised.assessments) == 2
    assert len(revised.evidence_batches) == 1
    revised_record = object.__getattribute__(revised, "_record")
    reverified_revision = _verify_ledger(revised_record, _b2_sources)
    assert reverified_revision.assessments == revised.assessments
    assert reverified_revision.evidence_batches == revised.evidence_batches
    assert reverified_revision.factual_evidence == revised.factual_evidence


@pytest.mark.parametrize("mutation", ("event_type", "event_position", "source_prefix_hash"))
def test_self_hashed_fabricated_source_history_cannot_be_promoted(_b2_sources, mutation):
    universe = _universe(_b2_sources)
    candidate_id = _candidate_with_later_event(universe, _b2_sources[4]["FVG"])
    verified = _append_initial_assessment(_ledger(universe), candidate_id, _b2_sources)
    fabricated = _forged_source_revision_record(
        verified,
        _b2_sources,
        candidate_id,
        _key(_b2_sources, 20),
        mutation=mutation,
    )
    # The direct dataclass construction, row/reference/batch/assessment/coverage
    # identities agree structurally, but the changed source row/metadata does not.
    assert fabricated.evidence_batches[-1].batch_id
    assert fabricated.evidence_batches[-1].evidence[0].evidence_kind == pilot.FVG_EVENT_EVIDENCE_KIND
    if mutation == "event_type":
        assert "FABRICATED_SOURCE_EVENT" in {
            dict(zip(ref.row_columns, ref.row))["event_type"].value
            for ref in fabricated.evidence_batches[-1].evidence
        }
    with pytest.raises(CandidatePilotError, match="exact verified Stage4B2 FVG retrieval result"):
        _verify_ledger(fabricated, _b2_sources)

    with pytest.raises(CandidatePilotError, match="source-verified.*raw ledgers"):
        revise_candidate_assessment(
            **_revision_inputs(fabricated, _b2_sources, candidate_id, _key(_b2_sources, 82))
        )


def test_verifier_requires_exact_universe_and_discards_untrusted_artifact_provenance(_b2_sources):
    universe = _universe(_b2_sources)
    assert len(universe.candidates) > 1
    subset = replace(universe, universe_id="", candidates=universe.candidates[:-1])
    subset_record = _ledger(subset)
    with pytest.raises(CandidatePilotError, match="candidate universe/source/timeline prefix"):
        _verify_ledger(subset_record, _b2_sources)

    candidate = universe.candidates[0]
    forged_provenance = replace(
        candidate.source_provenance,
        source_timeline_id="caller-invented-timeline",
    )
    forged_candidate = replace(candidate, source_provenance=forged_provenance, context_id="")
    forged_candidates = (forged_candidate,) + universe.candidates[1:]
    forged_universe = replace(universe, universe_id="", candidates=forged_candidates)
    forged_record = _ledger(forged_universe)
    with pytest.raises(CandidatePilotError, match="timeline/source producer identity"):
        _verify_ledger(forged_record, _b2_sources)


def test_rehashing_fabricated_initial_entity_row_does_not_pass_source_verification(_b2_sources):
    universe = _universe(_b2_sources)
    candidate = universe.candidates[0]
    ref = candidate.entity_evidence
    numeric_column, numeric_cell = next(
        (column, cell)
        for column, cell in zip(ref.row_columns, ref.row)
        if cell.kind is pilot.FrozenCellKind.NUMBER
    )
    forged_ref = _reference_variant(
        ref,
        row=_row_with_cell(
            ref,
            numeric_column,
            pilot.FrozenCellKind.NUMBER,
            "987654321.25",
        ),
    )
    forged_candidate = replace(
        candidate,
        factual_attributes=tuple(zip(ref.row_columns, forged_ref.row)),
        entity_evidence=forged_ref,
        context_id="",
    )
    forged_universe = replace(
        universe,
        universe_id="",
        candidates=(forged_candidate,) + universe.candidates[1:],
    )
    forged_record = _ledger(forged_universe)
    assert forged_record.factual_evidence[0].row_sha256 != ref.row_sha256
    with pytest.raises(CandidatePilotError, match="candidate universe/source/timeline prefix"):
        _verify_ledger(forged_record, _b2_sources)


def test_missing_or_wrong_timeline_source_fails_closed(_b2_sources):
    universe = _universe(_b2_sources)
    record = _ledger(universe)
    with pytest.raises(CandidatePilotError):
        verify_candidate_research_ledger(
            ledger=record,
            timeline=_b2_sources[2],
            adapter=_b2_sources[1],
            market_history=_b2_sources[0],
            fvg_surface=None,
        )

    other_adapter = type(_b2_sources[1])("unrelated-timeline")
    other_timeline = MarketObservationTimeline.seal(
        adapter=other_adapter,
        market_history=_b2_sources[0],
    )
    with pytest.raises(CandidatePilotError):
        verify_candidate_research_ledger(
            ledger=record,
            timeline=other_timeline,
            adapter=other_adapter,
            market_history=_b2_sources[0],
            fvg_surface=_b2_sources[4]["FVG"],
        )


def test_future_appended_source_preserves_verified_prefix_and_old_assessments(_b2_sources):
    market, adapter, _, _, _ = _b2_sources
    prefix_market = market.iloc[:8].copy(deep=True)
    prefix_adapter = type(adapter)(adapter.timeline_id)
    prefix_timeline = MarketObservationTimeline.seal(
        adapter=prefix_adapter,
        market_history=prefix_market,
    )
    prefix_surface = s4b2.build_fvg_surface(
        timeline=prefix_timeline,
        adapter=prefix_adapter,
        market_history=prefix_market,
    )
    prefix_sources = (prefix_market, prefix_adapter, prefix_timeline, None, {"FVG": prefix_surface})
    prefix_universe = _universe(prefix_sources, position=7)
    raw_prefix_ledger = _ledger(prefix_universe)

    # The supplied source contains future-appended rows. Verification compares
    # the exact causal decision prefix and timeline identity, not mutable
    # whole-artifact hashes; the issued record keeps freshly rebuilt provenance.
    verified = _verify_ledger(raw_prefix_ledger, _b2_sources)
    full_universe = _universe(_b2_sources, position=7)
    assert verified.universe == full_universe
    assert verified.universe.candidate("0").source_provenance.source_surface_id == (
        full_universe.candidate("0").source_provenance.source_surface_id
    )

    candidate_id = _candidate_with_later_event(full_universe, _b2_sources[4]["FVG"])
    assessed = _append_initial_assessment(verified, candidate_id, _b2_sources)
    original_history = assessed.assessments
    original_record = object.__getattribute__(assessed, "_record")
    revised = _revise(assessed, _b2_sources, candidate_id, _key(_b2_sources, 20))
    assert assessed.assessments is original_history
    assert len(assessed.assessments) == 1
    assert object.__getattribute__(assessed, "_record") is original_record
    assert len(revised.assessments) == 2
    assert revised.assessments[0] == assessed.assessments[0]
    _verify_ledger(object.__getattribute__(revised, "_record"), _b2_sources)


def test_raw_coverage_operations_do_not_promote_factual_history(_b2_sources):
    universe = _universe(_b2_sources)
    raw = _ledger(universe)
    coverage_only = record_candidate_coverage(
        ledger=raw,
        candidate_id=universe.eligible_candidate_ids[0],
        question_id="q-context",
        state=CandidateCoverageState.DEFERRED,
        as_of_key=universe.decision_key,
        reason="Coverage-only deferral; it is not factual relevance evidence.",
    )
    assert isinstance(coverage_only, CandidateResearchLedger)
    assert not isinstance(coverage_only, VerifiedCandidateResearchLedger)
    assert coverage_only.factual_evidence == raw.factual_evidence
    assert reconcile_candidate_coverage(ledger=coverage_only, question_id="q-context").reconciled

    verified = _verify_ledger(raw, _b2_sources)
    verified_coverage = record_candidate_coverage(
        ledger=verified,
        candidate_id=universe.eligible_candidate_ids[0],
        question_id="q-context",
        state=CandidateCoverageState.DEFERRED,
        as_of_key=universe.decision_key,
        reason="Coverage-only deferral; no factual judgment.",
    )
    assert isinstance(verified_coverage, VerifiedCandidateResearchLedger)
    restored = restore_deferred_candidate(
        ledger=verified_coverage,
        candidate_id=universe.eligible_candidate_ids[0],
        question_id="q-context",
        as_of_key=universe.decision_key,
        reason="Return to investigation only.",
    )
    assert isinstance(restored, VerifiedCandidateResearchLedger)
    assert restored.factual_evidence == verified.factual_evidence
    assert restored.assessments == verified.assessments
    assert restored.latest_coverage(
        universe.eligible_candidate_ids[0], "q-context"
    ).restoration_is_not_utility_evidence


def test_verified_ledger_snapshot_is_immutable_and_not_a_claim_of_empirical_truth(_b2_sources):
    universe = _universe(_b2_sources)
    candidate_id = universe.eligible_candidate_ids[0]
    verified = _append_initial_assessment(_ledger(universe), candidate_id, _b2_sources)
    assert isinstance(verified, VerifiedCandidateResearchLedger)
    with pytest.raises(AttributeError, match="immutable"):
        verified.assessments = ()
    with pytest.raises(AttributeError, match="immutable"):
        verified._record = _ledger(universe)
    raw = object.__getattribute__(verified, "_record")
    with pytest.raises(FrozenInstanceError):
        raw.assessments = ()
    with pytest.raises(CandidatePilotError, match="verify_candidate_research_ledger"):
        VerifiedCandidateResearchLedger(universe=universe)

    assessment = verified.assessments[0]
    assert assessment.provisional_status is ProvisionalStatus.PROVISIONAL
    assert assessment.category is AssessmentCategory.DECLARED_HUMAN_ASSESSMENT
    assert not hasattr(verified, "relevance_score")
    assert not hasattr(verified, "trading_signal")
    assert not any(
        token in name.lower()
        for name in pilot.__all__
        for token in ("prediction", "probability", "trade_signal", "execution")
    )
