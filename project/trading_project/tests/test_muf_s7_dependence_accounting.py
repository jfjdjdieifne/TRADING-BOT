"""MUF V1 S7 Adversarial Test Suite: Dependence Accounting Contracts & Causal Episode Ledger.

Fixture discipline: SYNTHETIC SMALL FIXTURES ONLY (no owner data).
Verifies D1-14, D1-17, D2-10, D2-15, D2-22, AP-1 §3.5:
- DependenceAccountingContract (I-EP-3: RESEARCH-DEBT-024 OPEN, no statistical independence claim)
- EpisodeAnchorIdentityRecord (I-EP-1: episode_id anchored on creation facts only, never member set)
- EpisodeMembershipEventRecord & CausalEpisodeLedger (I-EP-1..2, D2-10, I-IKA-1)
- Historical member deletion forbidden (S7_HISTORICAL_MEMBER_DELETION_FORBIDDEN)
- Non-overlapping span cluster accounting & causal as-of projection
"""
from dataclasses import replace
import hashlib
from pathlib import Path
import time

import pytest

from trading_system.market_understanding.availability import InformationAxis
from trading_system.market_understanding.contracts import (
    IllegalCausalReference,
    ImmutabilityViolation,
    InformationKeyViolation,
    PrematureAvailability,
    SchemaIdentity,
    SchemaViolation,
    TypedState,
    scan_market_shape_implementations,
    scan_private_imports,
    scan_prohibited_implementations,
)
from trading_system.market_understanding.dependence_accounting import (
    CausalEpisodeLedger,
    DependenceAccountingContract,
    EpisodeAnchorIdentityRecord,
    EpisodeMembershipEventRecord,
    MEMBERSHIP_EVENT_ADDED,
    MEMBERSHIP_EVENT_SUPERSEDED,
    RESEARCH_DEBT_024_STANDING_STATUS,
    S7_HISTORICAL_MEMBER_DELETION_FORBIDDEN,
    S7_ILLEGAL_INDEPENDENCE_CLAIM,
    S7_RESEARCH_DEBT_024_MUST_REMAIN_OPEN,
    S7_UNKNOWN_EPISODE_ID,
    STATISTICAL_INDEPENDENCE_STANDING_CLAIM,
    build_dependence_accounting_bundle,
    query_dependence_accounting_as_of,
)
from trading_system.market_understanding.detector_witness import (
    adapt_detector_witness_stream,
)
from trading_system.market_understanding.policy_governance import (
    DATASET_ROLE_DEVELOPMENT_FIT,
    PROVENANCE_PREDEFINED_CONTRACT,
    DatasetIdentityArtifact,
    DatasetRoleArtifact,
    PolicyArtifact,
)
from trading_system.market_understanding.price_path import PublishedOhlcBarFact
from trading_system.market_understanding.state_graph import (
    GenericFactualStateGraphSpec,
    RELATION_ADJACENT_TO,
    RELATION_CONTAINS,
    StateCatalogArtifact,
    StateVariableSpec,
    build_generic_factual_state_graph,
    create_standard_wave_descriptor_registry,
)
from trading_system.market_understanding.wave_representation import (
    CandidateWaveRepresentationSpec,
    FAMILY_ALPHA_POLICY_SCALE,
    construct_candidate_wave_representation,
)
from trading_system.research.information_time import (
    INFORMATION_KEY_VERSION,
    InformationKey,
    InformationPhase,
)
from trading_system.structure.swing_detector import EmpiricalConfirmationPolicy


PROJECT_ROOT = Path(__file__).resolve().parents[1]
S7_MODULE_PATH = (
    PROJECT_ROOT
    / "src"
    / "trading_system"
    / "market_understanding"
    / "dependence_accounting.py"
)

SOURCE = SchemaIdentity("BinanceSpotKlinePublishedOhlc", "V1")
TIMELINE = "SYNTH_1m|1d"


def k(
    pos: int,
    *,
    seq: int = 0,
    ts=None,
    phase: InformationPhase = InformationPhase.COMPLETED_ROW_AVAILABLE,
    timeline: str = TIMELINE,
) -> InformationKey:
    return InformationKey(
        information_key_version=INFORMATION_KEY_VERSION,
        timeline_id=timeline,
        bar_position=pos,
        event_time_utc=ts,
        information_phase=phase,
        deterministic_sequence=seq,
    )


def mk_bar(
    pos: int,
    high: float,
    low: float,
    *,
    dataset: str = "DS-DEV-S7",
    source: SchemaIdentity = SOURCE,
    timeline: str = TIMELINE,
) -> PublishedOhlcBarFact:
    mid = (high + low) / 2.0
    return PublishedOhlcBarFact(
        open_price=mid,
        high_price=high,
        low_price=low,
        close_price=mid,
        availability_key=k(pos, timeline=timeline),
        source_identity=source,
        dataset_identity=dataset,
        published_bar_record_ref=f"bar#{pos}",
    )


def _setup_s7_environment():
    hl_pairs = [
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
    bars = [mk_bar(idx + 1, h, l) for idx, (h, l) in enumerate(hl_pairs)]
    emp_pol = EmpiricalConfirmationPolicy(
        quantile=0.25, prior_continuation_reversals=(0.01, 0.02)
    )
    wb = adapt_detector_witness_stream(bars, confirmation_policy=emp_pol)

    ds_id = DatasetIdentityArtifact.create(
        dataset_id="DS-DEV-S7",
        content_hash="1" * 64,
        source_identity=SOURCE,
        timeline_id=TIMELINE,
        start_key=k(1),
        end_key=k(20),
        transformation_spec_hash="2" * 64,
        parent_dataset_ids=(),
        creation_code_hash="3" * 64,
        semantic_schema_hash="4" * 64,
    )
    ds_role = DatasetRoleArtifact.create(
        dataset_identity=ds_id,
        role=DATASET_ROLE_DEVELOPMENT_FIT,
        role_assignment_key=k(1),
        permitted_operations=("DEVELOPMENT_FIT", "CANDIDATE_WAVE_CONSTRUCTION"),
        prohibited_operations=("FINAL_LOCKED_CLAIM",),
        owner_authorization_ref="owner-s7-role-1",
    )
    rep_spec = CandidateWaveRepresentationSpec.create(
        representation_id="rep_s7_v1",
        family_kind=FAMILY_ALPHA_POLICY_SCALE,
        scope_timeline_id=TIMELINE,
        scope_axis=InformationAxis.POSITIONAL,
        intrinsic_scale_key="swing_base_q25",
        identity_rule_ref="ORIGIN_ANCHORED_SWING_V1",
    )
    policy_art = PolicyArtifact.create(
        policy_id="pol-s7-01",
        detector_policy_witness_ref=wb.policy_witness_spec.spec_identity,
        scope_timeline_id=TIMELINE,
        scope_axis=InformationAxis.POSITIONAL,
        scope_representation_id="rep_s7_v1",
        calibration_provenance_kind=PROVENANCE_PREDEFINED_CONTRACT,
        reproduction_recipe_hash="recipe-fixed-01",
        effective_from_key=k(1),
        owner_authorization_ref="owner-s7-pol-1",
    )
    wave_bundle = construct_candidate_wave_representation(
        bars,
        witness_bundle=wb,
        representation_spec=rep_spec,
        policy_artifact=policy_art,
        dataset_identity=ds_id,
        dataset_role=ds_role,
    )
    reg = create_standard_wave_descriptor_registry()
    var_eff = StateVariableSpec.create(
        variable_id="SV_WAVE_EFFICIENCY",
        semantic_definition="Confirmed wave efficiency ratio state variable",
        value_domain_kind="CONTINUOUS_BOUNDED_0_1",
        source_descriptor_refs=("FINAL_EFFICIENCY_RATIO",),
        source_relation_refs=(RELATION_ADJACENT_TO,),
    )
    catalog = StateCatalogArtifact.create(
        state_catalog_id="cat_s7_v1",
        variable_specs=(var_eff,),
        descriptor_refs=tuple(s.descriptor_id for s in reg.all_specs()),
        relation_refs=(RELATION_ADJACENT_TO, RELATION_CONTAINS),
    )
    graph_spec = GenericFactualStateGraphSpec.create(
        graph_spec_id="gspec_s7_v1",
        state_catalog=catalog,
        source_contract_hashes=("SRC_BINANCE_V1",),
        representation_contract_hashes=(rep_spec.representation_spec_hash,),
        descriptor_contract_hashes=tuple(
            s.descriptor_hash for s in reg.all_specs()
        ),
        relation_contract_hashes=("REL_ADJACENT_V1", "REL_CONTAINS_V1"),
    )
    sg_bundle = build_generic_factual_state_graph(
        wave_bundle,
        descriptor_registry=reg,
        state_catalog=catalog,
        graph_spec=graph_spec,
    )
    dep_contract = DependenceAccountingContract.create(
        contract_id="dep_contract_s7_v1"
    )
    return sg_bundle, dep_contract


def test_s7_module_passes_s0_ast_scanners() -> None:
    source = S7_MODULE_PATH.read_text(encoding="utf-8")
    assert scan_private_imports(source) == ()
    assert scan_prohibited_implementations(source) == ()
    assert scan_market_shape_implementations(source) == ()


def test_sealed_s0_to_s6_hashes_untouched() -> None:
    for rel_cert in (
        "docs/releases/MODULE_MUF_V1_S0_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S1_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S2_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S3_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S4_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S5_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S6_ACCEPTED_SRC_TESTS.sha256",
    ):
        cert_path = PROJECT_ROOT / rel_cert
        for line in cert_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            expected_hash, rel_file = line.split()
            actual_hash = hashlib.sha256(
                (PROJECT_ROOT / rel_file).read_bytes()
            ).hexdigest()
            assert actual_hash == expected_hash, f"Modified sealed file: {rel_file}"


def test_dependence_contract_enforces_i_ep_3_and_research_debt_024() -> None:
    c = DependenceAccountingContract.create(contract_id="dep_ok")
    assert (
        c.statistical_independence_claim
        == STATISTICAL_INDEPENDENCE_STANDING_CLAIM
    )
    assert c.research_debt_024_status == RESEARCH_DEBT_024_STANDING_STATUS

    # Claiming statistical independence fails closed (I-EP-3)
    with pytest.raises(SchemaViolation, match=S7_ILLEGAL_INDEPENDENCE_CLAIM):
        DependenceAccountingContract.create(
            contract_id="dep_bad_indep",
            statistical_independence_claim="PROVEN_INDEPENDENT",
        )

    # Claiming RESEARCH-DEBT-024 is CLOSED fails closed (I-EP-3)
    with pytest.raises(
        SchemaViolation, match=S7_RESEARCH_DEBT_024_MUST_REMAIN_OPEN
    ):
        DependenceAccountingContract.create(
            contract_id="dep_bad_debt",
            research_debt_024_status="CLOSED",
        )

    with pytest.raises(SchemaViolation, match="contract_hash mismatch"):
        replace(c, contract_hash="sha256:tampered")


def test_episode_anchor_identity_immutable_under_member_additions_i_ep_1() -> None:
    anc = EpisodeAnchorIdentityRecord.create(
        timeline_id=TIMELINE,
        anchor_wave_process_id="wp_anchor_1",
        anchor_origin_position=1,
        anchor_origin_key=k(1),
        episode_creation_key=k(3),
        representation_spec_hash="rep_hash_1",
        authority_policy_hash="pol_hash_1",
    )
    orig_episode_id = anc.episode_id

    ledger = CausalEpisodeLedger()
    ledger.register_anchor(anc)

    ev1 = EpisodeMembershipEventRecord.create(
        anchor=anc,
        member_ref="obs_1",
        member_availability_key=k(3),
    )
    ev2 = EpisodeMembershipEventRecord.create(
        anchor=anc,
        member_ref="obs_2",
        member_availability_key=k(4),
    )
    ledger.append_membership_event(ev1)
    ledger.append_membership_event(ev2)

    # I-EP-1: Adding members NEVER changes episode_id
    assert ledger.anchors()[0].episode_id == orig_episode_id
    assert len(ledger.membership_events()) == 2


def test_historical_member_deletion_forbidden_and_supersession_supported_i_ep_2() -> None:
    anc = EpisodeAnchorIdentityRecord.create(
        timeline_id=TIMELINE,
        anchor_wave_process_id="wp_anchor_1",
        anchor_origin_position=1,
        anchor_origin_key=k(1),
        episode_creation_key=k(3),
        representation_spec_hash="rep_hash_1",
        authority_policy_hash="pol_hash_1",
    )
    ledger = CausalEpisodeLedger()
    ledger.register_anchor(anc)
    ev1 = EpisodeMembershipEventRecord.create(
        anchor=anc,
        member_ref="obs_1",
        member_availability_key=k(3),
    )
    ledger.append_membership_event(ev1)

    # I-EP-2: Deleting a historical member raises ImmutabilityViolation
    with pytest.raises(
        ImmutabilityViolation, match=S7_HISTORICAL_MEMBER_DELETION_FORBIDDEN
    ):
        ledger.delete_member(anc.episode_id, "obs_1")

    # Lawful correction via append-only MEMBER_SUPERSEDED event
    sup = EpisodeMembershipEventRecord.create(
        anchor=anc,
        member_ref="obs_1",
        member_availability_key=k(4),
        event_type=MEMBERSHIP_EVENT_SUPERSEDED,
        supersedes_event_id=ev1.event_id,
    )
    ledger.append_membership_event(sup)
    assert len(ledger.membership_events()) == 2


def test_unknown_and_duplicate_episode_guards() -> None:
    anc = EpisodeAnchorIdentityRecord.create(
        timeline_id=TIMELINE,
        anchor_wave_process_id="wp_anchor_1",
        anchor_origin_position=1,
        anchor_origin_key=k(1),
        episode_creation_key=k(3),
        representation_spec_hash="rep_hash_1",
        authority_policy_hash="pol_hash_1",
    )
    ledger = CausalEpisodeLedger()
    ledger.register_anchor(anc)

    with pytest.raises(ImmutabilityViolation, match="duplicate episode_id"):
        ledger.register_anchor(anc)

    other_anc = EpisodeAnchorIdentityRecord.create(
        timeline_id=TIMELINE,
        anchor_wave_process_id="wp_anchor_2",
        anchor_origin_position=2,
        anchor_origin_key=k(2),
        episode_creation_key=k(4),
        representation_spec_hash="rep_hash_1",
        authority_policy_hash="pol_hash_1",
    )
    ev_unreg = EpisodeMembershipEventRecord.create(
        anchor=other_anc,
        member_ref="obs_x",
        member_availability_key=k(4),
    )
    with pytest.raises(SchemaViolation, match=S7_UNKNOWN_EPISODE_ID):
        ledger.append_membership_event(ev_unreg)


def test_build_dependence_accounting_bundle_and_as_of_query() -> None:
    sg_bundle, dep_contract = _setup_s7_environment()
    bundle = build_dependence_accounting_bundle(
        sg_bundle, contract=dep_contract
    )
    assert len(bundle.episode_anchors) == len(
        sg_bundle.wave_bundle.wave_identity_records
    )
    assert len(bundle.membership_events) >= len(bundle.episode_anchors)
    assert bundle.non_overlapping_span_cluster_count >= 1
    assert (
        bundle.statistical_independence_claim
        == STATISTICAL_INDEPENDENCE_STANDING_CLAIM
    )
    assert bundle.research_debt_024_status == RESEARCH_DEBT_024_STANDING_STATUS

    view = query_dependence_accounting_as_of(
        bundle, at_key=sg_bundle.wave_bundle.observation_keys[-1]
    )
    assert view.distinct_episode_count == len(bundle.episode_anchors)
    assert view.raw_active_member_count == len(bundle.membership_events)


def test_supersession_reduces_active_member_count_at_later_query_key() -> None:
    sg_bundle, dep_contract = _setup_s7_environment()
    bundle = build_dependence_accounting_bundle(
        sg_bundle, contract=dep_contract
    )
    first_anc = bundle.episode_anchors[0]
    first_ev = bundle.membership_events[0]
    last_key = sg_bundle.wave_bundle.observation_keys[-1]

    sup_ev = EpisodeMembershipEventRecord.create(
        anchor=first_anc,
        member_ref=first_ev.member_ref,
        member_availability_key=last_key,
        event_type=MEMBERSHIP_EVENT_SUPERSEDED,
        supersedes_event_id=first_ev.event_id,
    )
    bundle_with_sup = replace(
        bundle, membership_events=bundle.membership_events + (sup_ev,)
    )
    view_after = query_dependence_accounting_as_of(
        bundle_with_sup, at_key=last_key
    )
    assert view_after.raw_active_member_count == len(bundle.membership_events) - 1


def test_episode_anchor_post_init_tamper_guards() -> None:
    anc = EpisodeAnchorIdentityRecord.create(
        timeline_id=TIMELINE,
        anchor_wave_process_id="wp_1",
        anchor_origin_position=1,
        anchor_origin_key=k(1),
        episode_creation_key=k(3),
        representation_spec_hash="rep_1",
        authority_policy_hash="pol_1",
    )
    with pytest.raises(SchemaViolation, match="episode_id mismatch"):
        replace(anc, episode_id="ep_tampered")
    with pytest.raises(SchemaViolation, match="anchor_origin_position"):
        replace(anc, anchor_origin_position=-1)
    with pytest.raises(InformationKeyViolation):
        replace(anc, timeline_id="OTHER_TL")
    with pytest.raises(IllegalCausalReference):
        replace(anc, anchor_origin_key=k(5))


def test_membership_event_post_init_tamper_guards() -> None:
    anc = EpisodeAnchorIdentityRecord.create(
        timeline_id=TIMELINE,
        anchor_wave_process_id="wp_1",
        anchor_origin_position=1,
        anchor_origin_key=k(1),
        episode_creation_key=k(3),
        representation_spec_hash="rep_1",
        authority_policy_hash="pol_1",
    )
    ev = EpisodeMembershipEventRecord.create(
        anchor=anc,
        member_ref="m_1",
        member_availability_key=k(3),
    )
    with pytest.raises(SchemaViolation, match="event_id mismatch"):
        replace(ev, event_id="ev_tampered")
    with pytest.raises(SchemaViolation, match="invalid event_type"):
        replace(ev, event_type="DELETED")
    with pytest.raises(
        SchemaViolation,
        match="MEMBER_ADDED requires supersedes_event_id = NOT_APPLICABLE",
    ):
        replace(ev, supersedes_event_id="ev_old")
    with pytest.raises(SchemaViolation, match="supersedes_event_id"):
        EpisodeMembershipEventRecord.create(
            anchor=anc,
            member_ref="m_1",
            member_availability_key=k(4),
            event_type=MEMBERSHIP_EVENT_SUPERSEDED,
            supersedes_event_id=TypedState.NOT_APPLICABLE,
        )


def test_as_of_query_validation_and_realtime_speed() -> None:
    sg_bundle, dep_contract = _setup_s7_environment()
    t0 = time.perf_counter()
    bundle = build_dependence_accounting_bundle(
        sg_bundle, contract=dep_contract
    )
    _ = query_dependence_accounting_as_of(
        bundle, at_key=sg_bundle.wave_bundle.observation_keys[-1]
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert elapsed_ms < 50.0

    with pytest.raises(IllegalCausalReference):
        query_dependence_accounting_as_of(
            bundle, at_key=k(2, phase=InformationPhase.BAR_PRE_CLOSE)
        )
    with pytest.raises(InformationKeyViolation):
        query_dependence_accounting_as_of(
            bundle, at_key=k(2, timeline="OTHER_TL")
        )
    with pytest.raises(PrematureAvailability):
        query_dependence_accounting_as_of(bundle, at_key=k(99))


def test_dependence_contract_empty_field_guards() -> None:
    with pytest.raises(SchemaViolation, match="contract_id"):
        DependenceAccountingContract.create(contract_id="")
    with pytest.raises(SchemaViolation, match="grouping_rule_ref"):
        DependenceAccountingContract.create(
            contract_id="c1", grouping_rule_ref=""
        )
    with pytest.raises(SchemaViolation, match="overlap_rule_ref"):
        DependenceAccountingContract.create(
            contract_id="c1", overlap_rule_ref=""
        )
    with pytest.raises(SchemaViolation, match="supersession_rule_ref"):
        DependenceAccountingContract.create(
            contract_id="c1", supersession_rule_ref=""
        )


def test_episode_anchor_pre_close_key_rejected() -> None:
    with pytest.raises(IllegalCausalReference):
        EpisodeAnchorIdentityRecord.create(
            timeline_id=TIMELINE,
            anchor_wave_process_id="wp_1",
            anchor_origin_position=1,
            anchor_origin_key=k(1, phase=InformationPhase.BAR_PRE_CLOSE),
            episode_creation_key=k(3),
            representation_spec_hash="rep_1",
            authority_policy_hash="pol_1",
        )


def test_episode_anchor_published_record_tamper_rejected() -> None:
    anc = EpisodeAnchorIdentityRecord.create(
        timeline_id=TIMELINE,
        anchor_wave_process_id="wp_1",
        anchor_origin_position=1,
        anchor_origin_key=k(1),
        episode_creation_key=k(3),
        representation_spec_hash="rep_1",
        authority_policy_hash="pol_1",
    )
    with pytest.raises(SchemaViolation, match="published_record mismatch"):
        replace(anc, published_record="not_a_published_record")  # type: ignore[arg-type]


def test_membership_event_published_record_tamper_rejected() -> None:
    anc = EpisodeAnchorIdentityRecord.create(
        timeline_id=TIMELINE,
        anchor_wave_process_id="wp_1",
        anchor_origin_position=1,
        anchor_origin_key=k(1),
        episode_creation_key=k(3),
        representation_spec_hash="rep_1",
        authority_policy_hash="pol_1",
    )
    ev = EpisodeMembershipEventRecord.create(
        anchor=anc,
        member_ref="m_1",
        member_availability_key=k(3),
    )
    with pytest.raises(SchemaViolation, match="published_record mismatch"):
        replace(ev, published_record="not_a_published_record")  # type: ignore[arg-type]


def test_membership_event_before_anchor_creation_rejected() -> None:
    anc = EpisodeAnchorIdentityRecord.create(
        timeline_id=TIMELINE,
        anchor_wave_process_id="wp_1",
        anchor_origin_position=1,
        anchor_origin_key=k(1),
        episode_creation_key=k(4),
        representation_spec_hash="rep_1",
        authority_policy_hash="pol_1",
    )
    with pytest.raises(IllegalCausalReference):
        EpisodeMembershipEventRecord.create(
            anchor=anc,
            member_ref="m_1",
            member_availability_key=k(2),
            event_key_override=k(2),
        )


def test_ledger_rejects_invalid_anchor_and_event_types() -> None:
    ledger = CausalEpisodeLedger()
    with pytest.raises(SchemaViolation, match="expected EpisodeAnchorIdentityRecord"):
        ledger.register_anchor("invalid")  # type: ignore[arg-type]
    with pytest.raises(SchemaViolation, match="expected EpisodeMembershipEventRecord"):
        ledger.append_membership_event("invalid")  # type: ignore[arg-type]


def test_build_dependence_bundle_rejects_invalid_inputs() -> None:
    sg_bundle, dep_contract = _setup_s7_environment()
    with pytest.raises(SchemaViolation, match="GenericFactualStateGraphBundle"):
        build_dependence_accounting_bundle(
            "invalid",  # type: ignore[arg-type]
            contract=dep_contract,
        )
    with pytest.raises(SchemaViolation, match="DependenceAccountingContract"):
        build_dependence_accounting_bundle(
            sg_bundle,
            contract="invalid",  # type: ignore[arg-type]
        )


def test_query_dependence_as_of_rejects_invalid_bundle() -> None:
    with pytest.raises(SchemaViolation, match="DependenceAccountingBundle"):
        query_dependence_accounting_as_of(
            "invalid",  # type: ignore[arg-type]
            at_key=k(2),
        )


def test_as_of_cluster_count_monotonic_across_prefix_keys() -> None:
    sg_bundle, dep_contract = _setup_s7_environment()
    bundle = build_dependence_accounting_bundle(
        sg_bundle, contract=dep_contract
    )
    obs_keys = sg_bundle.wave_bundle.observation_keys
    v_early = query_dependence_accounting_as_of(bundle, at_key=obs_keys[2])
    v_late = query_dependence_accounting_as_of(bundle, at_key=obs_keys[-1])
    assert (
        v_early.non_overlapping_span_cluster_count
        <= v_late.non_overlapping_span_cluster_count
    )

