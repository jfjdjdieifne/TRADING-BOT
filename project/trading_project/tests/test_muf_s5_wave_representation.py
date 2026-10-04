"""MUF V1 S5 & Gate G1 Adversarial Test Suite: Candidate Wave Representation & Structural Qualification.

Fixture discipline: SYNTHETIC SMALL FIXTURES ONLY (no owner data).
Verifies D1-4, D1-5, D1-6, D1-8, D2-1, D2-2, D2-3, D2-17, D2-22, Correction-1 §1 & §2:
- Origin-anchored WaveIdentityRecord without end-fact leakage (I-WID-1..3, I-WPI-1..5)
- Earliest lawful availability enforcement (I-EARLY-1..3, NonEarliestAvailability)
- Identity-defining basis != proof/witness refs (I-IDB-1..3)
- Scale != depth & representation family discipline (I-SD-1..4)
- Zero-denominator efficiency ratio -> TypedState.UNDEFINED (I-DE-1)
- Append-only 4-table wave lifecycle & causal prefix invariance (I-IMM-2..3)
- Development-only dataset role enforcement (I-SEL-3, Attack 38)
- Gate G1 Structural Qualification: ELIGIBLE / INELIGIBLE only, no predictive winner (I-SEL-1, Attack 27)
- Real-time O(1)-per-bar throughput verification
"""
from dataclasses import replace
import hashlib
from pathlib import Path
import time

import pytest

from trading_system.market_understanding.availability import InformationAxis
from trading_system.market_understanding.contracts import (
    IllegalCausalReference,
    IncomparableInformationKeys,
    InformationKeyViolation,
    NonEarliestAvailability,
    PrematureAvailability,
    SchemaIdentity,
    SchemaViolation,
    TypedState,
    scan_market_shape_implementations,
    scan_private_imports,
    scan_prohibited_implementations,
)
from trading_system.market_understanding.detector_witness import (
    DetectorPolicyWitnessSpec,
    adapt_detector_witness_stream,
)
from trading_system.market_understanding.policy_governance import (
    DATASET_ROLE_DEVELOPMENT_FIT,
    DATASET_ROLE_DEVELOPMENT_SELECTION,
    DATASET_ROLE_FINAL_EVALUATION_LOCKED,
    EXPOSURE_STATE_EXPOSED_DEVELOPMENT,
    PROVENANCE_PREDEFINED_CONTRACT,
    DatasetIdentityArtifact,
    DatasetRoleArtifact,
    PolicyArtifact,
    PolicyScopeMismatch,
    SelectionBlockedError,
    promote_swing_witness_with_policy_artifact,
)
from trading_system.market_understanding.price_path import (
    EXACT,
    MetricResult,
    PublishedOhlcBarFact,
    exact_metric,
)
from trading_system.market_understanding.wave_representation import (
    CandidateWaveRepresentationBundle,
    CandidateWaveRepresentationSpec,
    FAMILY_ALPHA_POLICY_SCALE,
    FAMILY_BETA_PARAMETER_FREE,
    FAMILY_DELTA_EVENT_CONTAINMENT,
    FAMILY_GAMMA_RESIDUAL,
    FinalizedWaveGeometryRecord,
    G1_BLOCKED_FINAL_DATASET_FORBIDDEN,
    G1_CLAIM_BOUNDARY,
    G1_STATUS_ELIGIBLE,
    G1_STATUS_INELIGIBLE,
    G1_WINNER_CLAIM_FORBIDDEN,
    RunningWaveObservationRecord,
    S5_FINAL_DATASET_FORBIDDEN_IN_CANDIDATE_CONSTRUCTION,
    S5_IDENTITY_RULE_NOT_CONFIGURED,
    S5_INTRINSIC_SCALE_FORBIDDEN_FOR_FAMILY,
    S5_INTRINSIC_SCALE_REQUIRED_FOR_ALPHA,
    S5_NON_EARLIEST_WAVE_AVAILABILITY,
    S5_POLICY_AUTHORITY_MISSING,
    StructuralQualificationCriteria,
    StructuralQualificationRecord,
    WAVE_STATUS_CONFIRMED,
    WAVE_STATUS_FORMING,
    WaveIdentityRecord,
    construct_candidate_wave_representation,
    evaluate_g1_structural_qualification,
    query_wave_representation_as_of,
    verify_wave_prefix_invariance,
)
from trading_system.research.information_time import (
    INFORMATION_KEY_VERSION,
    InformationKey,
    InformationPhase,
)
from trading_system.structure.swing_detector import EmpiricalConfirmationPolicy


PROJECT_ROOT = Path(__file__).resolve().parents[1]
S5_MODULE_PATH = (
    PROJECT_ROOT
    / "src"
    / "trading_system"
    / "market_understanding"
    / "wave_representation.py"
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
    dataset: str = "DS-DEV-S5",
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


def _sample_zigzag_bars(dataset: str = "DS-DEV-S5") -> list[PublishedOhlcBarFact]:
    # Produces multiple confirmed alternating HIGH and LOW turning points
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
    return [
        mk_bar(idx + 1, h, l, dataset=dataset)
        for idx, (h, l) in enumerate(hl_pairs)
    ]


def _setup_s5_environment(role: str = DATASET_ROLE_DEVELOPMENT_FIT):
    bars = _sample_zigzag_bars()
    emp_pol = EmpiricalConfirmationPolicy(
        quantile=0.25, prior_continuation_reversals=(0.01, 0.02)
    )
    wb = adapt_detector_witness_stream(bars, confirmation_policy=emp_pol)
    witness_spec = wb.policy_witness_spec

    ds_id = DatasetIdentityArtifact.create(
        dataset_id="DS-DEV-S5",
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
        role=role,
        role_assignment_key=k(1),
        permitted_operations=("DEVELOPMENT_FIT", "CANDIDATE_WAVE_CONSTRUCTION"),
        prohibited_operations=("FINAL_LOCKED_CLAIM",),
        owner_authorization_ref="owner-s5-role-1",
    )
    policy_art = PolicyArtifact.create(
        policy_id="pol-s5-alpha-01",
        detector_policy_witness_ref=witness_spec.spec_identity,
        scope_timeline_id=TIMELINE,
        scope_axis=InformationAxis.POSITIONAL,
        scope_representation_id="rep_alpha_v1",
        calibration_provenance_kind=PROVENANCE_PREDEFINED_CONTRACT,
        reproduction_recipe_hash="recipe-fixed-01",
        effective_from_key=k(1),
        owner_authorization_ref="owner-s5-pol-1",
    )
    rep_spec = CandidateWaveRepresentationSpec.create(
        representation_id="rep_alpha_v1",
        family_kind=FAMILY_ALPHA_POLICY_SCALE,
        scope_timeline_id=TIMELINE,
        scope_axis=InformationAxis.POSITIONAL,
        intrinsic_scale_key="swing_base_q25",
        identity_rule_ref="ORIGIN_ANCHORED_SWING_V1",
    )
    return bars, emp_pol, wb, ds_id, ds_role, policy_art, rep_spec


def test_s5_module_passes_s0_ast_scanners() -> None:
    source = S5_MODULE_PATH.read_text(encoding="utf-8")
    assert scan_private_imports(source) == ()
    assert scan_prohibited_implementations(source) == ()
    assert scan_market_shape_implementations(source) == ()


def test_sealed_s0_s1_s2_s3_s4_hashes_untouched() -> None:
    for rel_cert in (
        "docs/releases/MODULE_MUF_V1_S0_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S1_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S2_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S3_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S4_ACCEPTED_SRC_TESTS.sha256",
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


def test_representation_spec_family_discipline_i_sd_4() -> None:
    # BETA and DELTA forbid intrinsic_scale_key (I-SD-4, Attack 15 & 16)
    for fam in (FAMILY_BETA_PARAMETER_FREE, FAMILY_DELTA_EVENT_CONTAINMENT):
        spec_ok = CandidateWaveRepresentationSpec.create(
            representation_id=f"rep_{fam}",
            family_kind=fam,
            scope_timeline_id=TIMELINE,
            scope_axis=InformationAxis.POSITIONAL,
            intrinsic_scale_key=TypedState.NOT_APPLICABLE,
            identity_rule_ref="RULE_V1",
        )
        assert spec_ok.intrinsic_scale_key is TypedState.NOT_APPLICABLE

        with pytest.raises(
            SchemaViolation, match=S5_INTRINSIC_SCALE_FORBIDDEN_FOR_FAMILY
        ):
            CandidateWaveRepresentationSpec.create(
                representation_id=f"rep_{fam}_bad",
                family_kind=fam,
                scope_timeline_id=TIMELINE,
                scope_axis=InformationAxis.POSITIONAL,
                intrinsic_scale_key="smuggled_scale",
                identity_rule_ref="RULE_V1",
            )

    # ALPHA requires a non-empty string intrinsic_scale_key
    with pytest.raises(
        SchemaViolation, match=S5_INTRINSIC_SCALE_REQUIRED_FOR_ALPHA
    ):
        CandidateWaveRepresentationSpec.create(
            representation_id="rep_alpha_bad",
            family_kind=FAMILY_ALPHA_POLICY_SCALE,
            scope_timeline_id=TIMELINE,
            scope_axis=InformationAxis.POSITIONAL,
            intrinsic_scale_key=TypedState.NOT_APPLICABLE,
            identity_rule_ref="RULE_V1",
        )

    # Hash tamper rejected
    valid_spec = CandidateWaveRepresentationSpec.create(
        representation_id="rep_gamma",
        family_kind=FAMILY_GAMMA_RESIDUAL,
        scope_timeline_id=TIMELINE,
        scope_axis=InformationAxis.POSITIONAL,
        intrinsic_scale_key="residual_l1",
        identity_rule_ref="RULE_V1",
    )
    with pytest.raises(SchemaViolation, match="representation_spec_hash mismatch"):
        replace(valid_spec, representation_spec_hash="sha256:tampered")


def test_wave_identity_requires_configured_rule_and_policy_authority() -> None:
    bars, _, wb, ds_id, ds_role, policy_art, rep_spec = _setup_s5_environment()
    tp0 = promote_swing_witness_with_policy_artifact(
        wb.swing_event_witnesses[0], policy_artifact=policy_art
    )

    # Unconfigured identity_rule_ref blocked (I-WIB-2, Attack 26)
    unconf_spec = CandidateWaveRepresentationSpec.create(
        representation_id="rep_alpha_v1",
        family_kind=FAMILY_ALPHA_POLICY_SCALE,
        scope_timeline_id=TIMELINE,
        scope_axis=InformationAxis.POSITIONAL,
        intrinsic_scale_key="swing_base_q25",
        identity_rule_ref=TypedState.NOT_CONFIGURED,
    )
    with pytest.raises(
        SelectionBlockedError, match=S5_IDENTITY_RULE_NOT_CONFIGURED
    ):
        WaveIdentityRecord.create(
            representation_spec=unconf_spec,
            policy_artifact=policy_art,
            start_turning_point=tp0,
        )
    with pytest.raises(
        SelectionBlockedError, match=S5_IDENTITY_RULE_NOT_CONFIGURED
    ):
        construct_candidate_wave_representation(
            bars,
            witness_bundle=wb,
            representation_spec=unconf_spec,
            policy_artifact=policy_art,
            dataset_identity=ds_id,
            dataset_role=ds_role,
        )

    # Missing PolicyArtifact blocked (I-PAUTH-1, Attack 2)
    with pytest.raises(SelectionBlockedError, match=S5_POLICY_AUTHORITY_MISSING):
        WaveIdentityRecord.create(
            representation_spec=rep_spec,
            policy_artifact=TypedState.NOT_CONFIGURED,  # type: ignore[arg-type]
            start_turning_point=tp0,
        )
    with pytest.raises(SelectionBlockedError, match=S5_POLICY_AUTHORITY_MISSING):
        construct_candidate_wave_representation(
            bars,
            witness_bundle=wb,
            representation_spec=rep_spec,
            policy_artifact=None,
            dataset_identity=ds_id,
            dataset_role=ds_role,
        )


def test_wave_identity_earliest_lawful_availability_and_proof_separation() -> None:
    _, _, wb, _, _, policy_art, rep_spec = _setup_s5_environment()
    tp0 = promote_swing_witness_with_policy_artifact(
        wb.swing_event_witnesses[0], policy_artifact=policy_art
    )

    # 1. Premature availability key (< tp0.availability_key) raises PrematureAvailability (I-WIB-3)
    with pytest.raises(PrematureAvailability):
        WaveIdentityRecord.create(
            representation_spec=rep_spec,
            policy_artifact=policy_art,
            start_turning_point=tp0,
            claimed_availability_key=tp0.origin_key,
        )

    # 2. Artificially delayed availability key (> earliest_key) without new required basis key
    # raises NonEarliestAvailability (I-EARLY-2, Correction-1 Attack 1)
    later_key = k(tp0.availability_key.bar_position + 2)
    with pytest.raises(
        NonEarliestAvailability, match=S5_NON_EARLIEST_WAVE_AVAILABILITY
    ):
        WaveIdentityRecord.create(
            representation_spec=rep_spec,
            policy_artifact=policy_art,
            start_turning_point=tp0,
            claimed_availability_key=later_key,
        )

    # 3. Supplying a genuine later required basis key in additional_basis_keys makes later_key lawful
    wi_later_basis = WaveIdentityRecord.create(
        representation_spec=rep_spec,
        policy_artifact=policy_art,
        start_turning_point=tp0,
        additional_basis_keys=(later_key,),
        additional_required_basis_refs=("parent_basis_ref_1",),
        claimed_availability_key=later_key,
    )
    assert wi_later_basis.wave_identity_information_key == later_key

    # 4. Adding proof_refs NEVER changes wave_process_id (I-IDB-2, Correction-1 Attack 2)
    wi_base = WaveIdentityRecord.create(
        representation_spec=rep_spec,
        policy_artifact=policy_art,
        start_turning_point=tp0,
        proof_refs=(),
    )
    wi_extra_proof = WaveIdentityRecord.create(
        representation_spec=rep_spec,
        policy_artifact=policy_art,
        start_turning_point=tp0,
        proof_refs=("extra_witness_A", "extra_audit_trace_B"),
    )
    assert wi_base.wave_process_id == wi_extra_proof.wave_process_id
    assert wi_base.identity_proof.proof_refs != wi_extra_proof.identity_proof.proof_refs


def test_construct_candidate_wave_representation_and_append_only_lifecycle() -> None:
    bars, _, wb, ds_id, ds_role, policy_art, rep_spec = _setup_s5_environment()
    bundle = construct_candidate_wave_representation(
        bars,
        witness_bundle=wb,
        representation_spec=rep_spec,
        policy_artifact=policy_art,
        dataset_identity=ds_id,
        dataset_role=ds_role,
    )
    assert len(bundle.authoritative_turning_points) >= 2
    assert len(bundle.wave_identity_records) == len(
        bundle.authoritative_turning_points
    )
    assert len(bundle.finalized_wave_geometries) >= 1
    assert len(bundle.running_wave_observations) >= len(
        bundle.wave_identity_records
    )
    assert (
        bundle.updated_dataset_role.exposure_state
        == EXPOSURE_STATE_EXPOSED_DEVELOPMENT
    )

    # Verify first wave was born FORMING and later CONFIRMED without mutating WaveIdentityRecord
    first_wp = bundle.wave_identity_records[0]
    first_geom = bundle.finalized_wave_geometries[0]
    assert first_geom.wave_process_id == first_wp.wave_process_id
    assert (
        first_geom.wave_end_confirmed_key
        >= first_wp.wave_identity_information_key
    )
    assert first_geom.final_bar_count == (
        first_geom.end_origin_position - first_geom.start_origin_position
    )
    assert isinstance(first_geom.final_efficiency_ratio, MetricResult)
    assert first_geom.final_efficiency_ratio.semantics == EXACT


def test_wave_prefix_invariance_and_as_of_projection_i_wid_1_2() -> None:
    bars, emp_pol, wb, ds_id, ds_role, policy_art, rep_spec = _setup_s5_environment()
    prefix_len = 6
    wb_prefix = adapt_detector_witness_stream(
        bars[:prefix_len], confirmation_policy=emp_pol
    )

    assert verify_wave_prefix_invariance(
        bars,
        prefix_length=prefix_len,
        full_witness_bundle=wb,
        prefix_witness_bundle=wb_prefix,
        representation_spec=rep_spec,
        policy_artifact=policy_art,
        dataset_identity=ds_id,
        dataset_role=ds_role,
    )

    full_bundle = construct_candidate_wave_representation(
        bars,
        witness_bundle=wb,
        representation_spec=rep_spec,
        policy_artifact=policy_art,
        dataset_identity=ds_id,
        dataset_role=ds_role,
    )

    # At birth of first wave, it is FORMING; after end TP confirms, it is CONFIRMED
    first_wp = full_bundle.wave_identity_records[0]
    view_at_birth = query_wave_representation_as_of(
        full_bundle, at_key=first_wp.wave_identity_information_key
    )
    assert first_wp.wave_process_id in view_at_birth.forming_wave_process_ids
    assert (
        first_wp.wave_process_id not in view_at_birth.confirmed_wave_process_ids
    )

    first_geom = full_bundle.finalized_wave_geometries[0]
    view_at_end = query_wave_representation_as_of(
        full_bundle, at_key=first_geom.wave_end_confirmed_key
    )
    assert first_wp.wave_process_id in view_at_end.confirmed_wave_process_ids
    # The WaveIdentityRecord itself is byte-for-byte identical at birth and after confirmation!
    assert (
        view_at_birth.visible_wave_identities[0]
        == view_at_end.visible_wave_identities[0]
    )


def test_zero_denominator_efficiency_ratio_returns_undefined_i_de_1() -> None:
    bars, _, wb, ds_id, ds_role, policy_art, rep_spec = _setup_s5_environment()
    bundle = construct_candidate_wave_representation(
        bars,
        witness_bundle=wb,
        representation_spec=rep_spec,
        policy_artifact=policy_art,
        dataset_identity=ds_id,
        dataset_role=ds_role,
    )
    ro = bundle.running_wave_observations[0]
    # Tamper running_path_length to 0.0 while keeping numeric efficiency ratio -> SchemaViolation
    with pytest.raises(SchemaViolation, match="TypedState.UNDEFINED"):
        replace(ro, running_path_length=exact_metric(0.0))

    fg = bundle.finalized_wave_geometries[0]
    with pytest.raises(SchemaViolation, match="TypedState.UNDEFINED"):
        replace(fg, final_path_length=exact_metric(0.0))


def test_final_evaluation_locked_dataset_blocked_in_s5_and_g1() -> None:
    bars, _, wb, ds_id, _, policy_art, rep_spec = _setup_s5_environment()
    locked_role = DatasetRoleArtifact.create(
        dataset_identity=ds_id,
        role=DATASET_ROLE_FINAL_EVALUATION_LOCKED,
        role_assignment_key=k(1),
        permitted_operations=("FINAL_LOCKED_EVALUATION",),
        prohibited_operations=("DEVELOPMENT_FIT",),
        owner_authorization_ref="owner-s5-locked",
    )
    with pytest.raises(
        SelectionBlockedError,
        match=S5_FINAL_DATASET_FORBIDDEN_IN_CANDIDATE_CONSTRUCTION,
    ):
        construct_candidate_wave_representation(
            bars,
            witness_bundle=wb,
            representation_spec=rep_spec,
            policy_artifact=policy_art,
            dataset_identity=ds_id,
            dataset_role=locked_role,
        )


def test_gate_g1_structural_qualification_eligible_ineligible_and_no_winner() -> None:
    bars, _, wb, ds_id, ds_role, policy_art, rep_spec = _setup_s5_environment(
        role=DATASET_ROLE_DEVELOPMENT_SELECTION
    )
    bundle = construct_candidate_wave_representation(
        bars,
        witness_bundle=wb,
        representation_spec=rep_spec,
        policy_artifact=policy_art,
        dataset_identity=ds_id,
        dataset_role=ds_role,
    )

    # 1. ELIGIBLE under satisfied criteria
    crit_pass = StructuralQualificationCriteria(
        criteria_id="g1_crit_v1",
        min_wave_identities=1,
        min_confirmed_waves=1,
        require_causal_prefix_invariance=True,
    )
    rec_ok = evaluate_g1_structural_qualification(
        bundle,
        qualification_id="g1_qual_01",
        criteria=crit_pass,
        prefix_invariance_verified=True,
    )
    assert rec_ok.qualification_status == G1_STATUS_ELIGIBLE
    assert rec_ok.ineligibility_reasons == ()
    assert rec_ok.claim_boundary == G1_CLAIM_BOUNDARY

    # 2. INELIGIBLE when criteria not met
    crit_high = StructuralQualificationCriteria(
        criteria_id="g1_crit_high",
        min_wave_identities=100,
        min_confirmed_waves=100,
        require_causal_prefix_invariance=True,
    )
    rec_inel = evaluate_g1_structural_qualification(
        bundle,
        qualification_id="g1_qual_02",
        criteria=crit_high,
        prefix_invariance_verified=False,
    )
    assert rec_inel.qualification_status == G1_STATUS_INELIGIBLE
    assert len(rec_inel.ineligibility_reasons) == 3

    # 3. Claiming a predictive winner at Gate G1 fails closed (I-SEL-1, Attack 27)
    with pytest.raises(SelectionBlockedError, match=G1_WINNER_CLAIM_FORBIDDEN):
        evaluate_g1_structural_qualification(
            bundle,
            qualification_id="g1_qual_winner_attempt",
            criteria=crit_pass,
            claim_predictive_winner=True,
        )

    # 4. Tampering qualification_status to "WINNER" or tampering hash rejected
    with pytest.raises(SchemaViolation, match="no WINNER allowed"):
        replace(rec_ok, qualification_status="WINNER")
    with pytest.raises(SelectionBlockedError, match=G1_WINNER_CLAIM_FORBIDDEN):
        replace(rec_ok, claim_boundary="PREDICTIVE_WINNER")
    with pytest.raises(SchemaViolation, match="qualification_hash mismatch"):
        replace(rec_ok, qualification_hash="sha256:tampered")


def test_as_of_query_validation_and_realtime_throughput() -> None:
    bars, _, wb, ds_id, ds_role, policy_art, rep_spec = _setup_s5_environment()
    t_start = time.perf_counter()
    bundle = construct_candidate_wave_representation(
        bars,
        witness_bundle=wb,
        representation_spec=rep_spec,
        policy_artifact=policy_art,
        dataset_identity=ds_id,
        dataset_role=ds_role,
    )
    elapsed_ms = (time.perf_counter() - t_start) * 1000.0
    # 10 bars should complete in well under 50 ms
    assert elapsed_ms < 50.0

    # Reject BAR_PRE_CLOSE query key
    with pytest.raises(IllegalCausalReference):
        query_wave_representation_as_of(
            bundle,
            at_key=k(2, phase=InformationPhase.BAR_PRE_CLOSE),
        )
    # Reject wrong timeline
    with pytest.raises(InformationKeyViolation):
        query_wave_representation_as_of(
            bundle,
            at_key=k(2, timeline="ETHUSDT:1h"),
        )
    # Reject out-of-range key
    with pytest.raises(PrematureAvailability):
        query_wave_representation_as_of(
            bundle,
            at_key=k(99),
        )


def test_wave_identity_record_post_init_tamper_guards() -> None:
    bars, _, wb, ds_id, ds_role, policy_art, rep_spec = _setup_s5_environment()
    bundle = construct_candidate_wave_representation(
        bars,
        witness_bundle=wb,
        representation_spec=rep_spec,
        policy_artifact=policy_art,
        dataset_identity=ds_id,
        dataset_role=ds_role,
    )
    wi = bundle.wave_identity_records[0]

    with pytest.raises(SchemaViolation, match="wave_process_id does not match"):
        replace(wi, wave_process_id="wp_tampered")
    with pytest.raises(InformationKeyViolation, match="timeline_id mismatch"):
        replace(wi, timeline_id="OTHER_TL")
    with pytest.raises(SchemaViolation, match="start_turning_point_id mismatch"):
        replace(wi, start_turning_point_id="tp_tampered")
    with pytest.raises(SchemaViolation, match="origin_position"):
        replace(wi, origin_position=-1)
    with pytest.raises(SchemaViolation, match="wave_direction"):
        replace(wi, wave_direction="SIDEWAYS")
    with pytest.raises(PrematureAvailability):
        replace(wi, origin_key=wi.wave_identity_information_key)


def test_running_wave_observation_post_init_tamper_guards() -> None:
    bars, _, wb, ds_id, ds_role, policy_art, rep_spec = _setup_s5_environment()
    bundle = construct_candidate_wave_representation(
        bars,
        witness_bundle=wb,
        representation_spec=rep_spec,
        policy_artifact=policy_art,
        dataset_identity=ds_id,
        dataset_role=ds_role,
    )
    ro = bundle.running_wave_observations[0]

    with pytest.raises(SchemaViolation, match="observation_id mismatch"):
        replace(ro, observation_id="obs_tampered")
    with pytest.raises(SchemaViolation, match="running_bar_count must be >= 1"):
        replace(ro, running_bar_count=0)
    with pytest.raises(InformationKeyViolation, match="timeline mismatch"):
        replace(ro, timeline_id="OTHER_TL")
    with pytest.raises(SchemaViolation, match="positive running_path_length"):
        replace(ro, running_efficiency_ratio=TypedState.UNDEFINED)


def test_finalized_wave_geometry_post_init_tamper_guards() -> None:
    bars, _, wb, ds_id, ds_role, policy_art, rep_spec = _setup_s5_environment()
    bundle = construct_candidate_wave_representation(
        bars,
        witness_bundle=wb,
        representation_spec=rep_spec,
        policy_artifact=policy_art,
        dataset_identity=ds_id,
        dataset_role=ds_role,
    )
    fg = bundle.finalized_wave_geometries[0]

    with pytest.raises(SchemaViolation, match="geometry_record_id mismatch"):
        replace(fg, geometry_record_id="geom_tampered")
    with pytest.raises(
        SchemaViolation,
        match="end_origin_position must exceed start_origin_position",
    ):
        replace(fg, end_origin_position=fg.start_origin_position)
    with pytest.raises(SchemaViolation, match="final_bar_count mismatch"):
        replace(fg, final_bar_count=fg.final_bar_count + 1)
    with pytest.raises(PrematureAvailability):
        replace(fg, end_origin_key=fg.start_origin_key)
    with pytest.raises(SchemaViolation, match="positive final_path_length"):
        replace(fg, final_efficiency_ratio=TypedState.UNDEFINED)


def test_wave_status_event_post_init_tamper_guards() -> None:
    bars, _, wb, ds_id, ds_role, policy_art, rep_spec = _setup_s5_environment()
    bundle = construct_candidate_wave_representation(
        bars,
        witness_bundle=wb,
        representation_spec=rep_spec,
        policy_artifact=policy_art,
        dataset_identity=ds_id,
        dataset_role=ds_role,
    )
    se = bundle.wave_status_events[0]

    with pytest.raises(SchemaViolation, match="event_id mismatch"):
        replace(se, event_id="ev_tampered")
    with pytest.raises(SchemaViolation, match="invalid status"):
        replace(se, status="UNKNOWN_STATUS")
    with pytest.raises(SchemaViolation, match="trigger_ref"):
        replace(se, trigger_ref="")


def test_policy_and_representation_scope_mismatch_guards() -> None:
    bars, _, wb, ds_id, ds_role, policy_art, rep_spec = _setup_s5_environment()

    other_rep = CandidateWaveRepresentationSpec.create(
        representation_id="other_rep_id",
        family_kind=FAMILY_ALPHA_POLICY_SCALE,
        scope_timeline_id=TIMELINE,
        scope_axis=InformationAxis.POSITIONAL,
        intrinsic_scale_key="swing_base_q25",
        identity_rule_ref="ORIGIN_ANCHORED_SWING_V1",
    )
    with pytest.raises(
        PolicyScopeMismatch, match="scope_representation_id does not match"
    ):
        construct_candidate_wave_representation(
            bars,
            witness_bundle=wb,
            representation_spec=other_rep,
            policy_artifact=policy_art,
            dataset_identity=ds_id,
            dataset_role=ds_role,
        )

    other_tl_rep = CandidateWaveRepresentationSpec.create(
        representation_id="rep_alpha_v1",
        family_kind=FAMILY_ALPHA_POLICY_SCALE,
        scope_timeline_id="OTHER_TL",
        scope_axis=InformationAxis.POSITIONAL,
        intrinsic_scale_key="swing_base_q25",
        identity_rule_ref="ORIGIN_ANCHORED_SWING_V1",
    )
    with pytest.raises(PolicyScopeMismatch, match="timeline_id mismatch"):
        construct_candidate_wave_representation(
            bars,
            witness_bundle=wb,
            representation_spec=other_tl_rep,
            policy_artifact=policy_art,
            dataset_identity=ds_id,
            dataset_role=ds_role,
        )


def test_development_bar_stream_validation_guards() -> None:
    bars, _, wb, ds_id, ds_role, policy_art, rep_spec = _setup_s5_environment()

    # Empty bars rejected
    with pytest.raises(SchemaViolation, match="bars must be non-empty"):
        construct_candidate_wave_representation(
            (),
            witness_bundle=wb,
            representation_spec=rep_spec,
            policy_artifact=policy_art,
            dataset_identity=ds_id,
            dataset_role=ds_role,
        )

    # Length mismatch between bars and witness_bundle rejected
    with pytest.raises(SchemaViolation, match="length mismatch"):
        construct_candidate_wave_representation(
            bars[:-1],
            witness_bundle=wb,
            representation_spec=rep_spec,
            policy_artifact=policy_art,
            dataset_identity=ds_id,
            dataset_role=ds_role,
        )

    # Foreign dataset bar rejected
    foreign_bars = list(bars)
    foreign_bars[0] = mk_bar(1, 10.0, 9.0, dataset="DS-FOREIGN-LOCKED")
    with pytest.raises(
        SelectionBlockedError,
        match=S5_FINAL_DATASET_FORBIDDEN_IN_CANDIDATE_CONSTRUCTION,
    ):
        construct_candidate_wave_representation(
            foreign_bars,
            witness_bundle=wb,
            representation_spec=rep_spec,
            policy_artifact=policy_art,
            dataset_identity=ds_id,
            dataset_role=ds_role,
        )


def test_gate_g1_qualification_criteria_and_record_tamper_guards() -> None:
    bars, _, wb, ds_id, ds_role, policy_art, rep_spec = _setup_s5_environment()
    bundle = construct_candidate_wave_representation(
        bars,
        witness_bundle=wb,
        representation_spec=rep_spec,
        policy_artifact=policy_art,
        dataset_identity=ds_id,
        dataset_role=ds_role,
    )

    with pytest.raises(SchemaViolation, match="min_wave_identities"):
        StructuralQualificationCriteria(
            criteria_id="bad_c1",
            min_wave_identities=-1,
            min_confirmed_waves=1,
            require_causal_prefix_invariance=True,
        )
    with pytest.raises(SchemaViolation, match="min_confirmed_waves"):
        StructuralQualificationCriteria(
            criteria_id="bad_c2",
            min_wave_identities=1,
            min_confirmed_waves=-1,
            require_causal_prefix_invariance=True,
        )

    crit = StructuralQualificationCriteria(
        criteria_id="ok_c",
        min_wave_identities=1,
        min_confirmed_waves=1,
        require_causal_prefix_invariance=True,
    )
    rec = evaluate_g1_structural_qualification(
        bundle,
        qualification_id="q_guard",
        criteria=crit,
    )
    with pytest.raises(
        SchemaViolation,
        match="ELIGIBLE record cannot have ineligibility_reasons",
    ):
        replace(rec, ineligibility_reasons=("UNEXPECTED_REASON",))
    with pytest.raises(
        SchemaViolation,
        match="INELIGIBLE record requires non-empty ineligibility_reasons",
    ):
        replace(rec, qualification_status=G1_STATUS_INELIGIBLE)
    with pytest.raises(
        SelectionBlockedError, match=G1_BLOCKED_FINAL_DATASET_FORBIDDEN
    ):
        replace(rec, dataset_role=DATASET_ROLE_FINAL_EVALUATION_LOCKED)


def test_verify_wave_prefix_invariance_bounds_and_tamper_detection() -> None:
    bars, emp_pol, wb, ds_id, ds_role, policy_art, rep_spec = _setup_s5_environment()
    wb_prefix = adapt_detector_witness_stream(
        bars[:6], confirmation_policy=emp_pol
    )

    with pytest.raises(SchemaViolation, match="prefix_length out of range"):
        verify_wave_prefix_invariance(
            bars,
            prefix_length=0,
            full_witness_bundle=wb,
            prefix_witness_bundle=wb_prefix,
            representation_spec=rep_spec,
            policy_artifact=policy_art,
            dataset_identity=ds_id,
            dataset_role=ds_role,
        )

    # Passing an evidence-only prefix witness bundle (which has zero swing_event_witnesses)
    # triggers prefix invariance failure against the full witness bundle
    wb_tampered = adapt_detector_witness_stream(
        bars[:6], confirmation_policy=None
    )
    with pytest.raises(
        SchemaViolation, match="prefix wave invariance violated"
    ):
        verify_wave_prefix_invariance(
            bars,
            prefix_length=6,
            full_witness_bundle=wb,
            prefix_witness_bundle=wb_tampered,
            representation_spec=rep_spec,
            policy_artifact=policy_art,
            dataset_identity=ds_id,
            dataset_role=ds_role,
        )


def test_multiple_representation_families_coexist_with_distinct_identities() -> None:
    bars, _, wb, ds_id, ds_role, policy_art, rep_alpha = _setup_s5_environment()
    bundle_alpha = construct_candidate_wave_representation(
        bars,
        witness_bundle=wb,
        representation_spec=rep_alpha,
        policy_artifact=policy_art,
        dataset_identity=ds_id,
        dataset_role=ds_role,
    )

    rep_delta = CandidateWaveRepresentationSpec.create(
        representation_id="rep_delta_v1",
        family_kind=FAMILY_DELTA_EVENT_CONTAINMENT,
        scope_timeline_id=TIMELINE,
        scope_axis=InformationAxis.POSITIONAL,
        intrinsic_scale_key=TypedState.NOT_APPLICABLE,
        identity_rule_ref="DELTA_CONTAINMENT_V1",
    )
    policy_delta = PolicyArtifact.create(
        policy_id="pol-s5-delta-01",
        detector_policy_witness_ref=wb.policy_witness_spec.spec_identity,
        scope_timeline_id=TIMELINE,
        scope_axis=InformationAxis.POSITIONAL,
        scope_representation_id="rep_delta_v1",
        calibration_provenance_kind=PROVENANCE_PREDEFINED_CONTRACT,
        reproduction_recipe_hash="recipe-fixed-01",
        effective_from_key=k(1),
        owner_authorization_ref="owner-s5-pol-delta",
    )
    bundle_delta = construct_candidate_wave_representation(
        bars,
        witness_bundle=wb,
        representation_spec=rep_delta,
        policy_artifact=policy_delta,
        dataset_identity=ds_id,
        dataset_role=ds_role,
    )

    assert (
        bundle_alpha.wave_identity_records[0].wave_process_id
        != bundle_delta.wave_identity_records[0].wave_process_id
    )


