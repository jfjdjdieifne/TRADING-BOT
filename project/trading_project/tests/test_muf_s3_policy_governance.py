"""MUF V1 S3 — Research-Governance Infrastructure & Gate G0 adversarial test suite.

Fixture discipline: SYNTHETIC SMALL FIXTURES ONLY (no owner data).
Verifies ObjectiveArtifact, DatasetIdentityArtifact, DatasetRoleArtifact,
ExposureAncestry, FoldProtocolArtifact, HumanReviewRecord,
RepresentationExperimentRecord, ExperimentRegistry, PolicyArtifact,
AuthoritativeTurningPointRecord promotion, and Gate G0 (evaluate_g0_calibration_gate),
including D1/D2 adversarial attacks 1, 2, 12, 13, 14, 25, 28, 30, 31, 32, 33,
40, 46, 47, 49, and 50.
"""
from dataclasses import replace
from pathlib import Path
import pandas as pd
import pytest

from trading_system.market_understanding.availability import InformationAxis
from trading_system.market_understanding.contracts import (
    IllegalCausalReference,
    ImmutabilityViolation,
    IncomparableInformationKeys,
    InformationKeyViolation,
    PrematureAvailability,
    SchemaIdentity,
    SchemaViolation,
    TypedState,
    scan_market_shape_implementations,
    scan_private_imports,
    scan_prohibited_implementations,
)
from trading_system.market_understanding.detector_witness import (
    adapt_detector_witness_stream,
)
from trading_system.market_understanding.identity import (
    TURNING_POINT_RECORD_TYPE,
    WaveProcessIdentityBasis,
    wave_process_identity,
)
from trading_system.market_understanding.policy_governance import (
    DATASET_ROLE_DEVELOPMENT_FIT,
    DATASET_ROLE_DEVELOPMENT_SELECTION,
    DATASET_ROLE_FINAL_EVALUATION_LOCKED,
    EXPERIMENT_STATUS_COMPLETED,
    EXPERIMENT_STATUS_FAILED,
    EXPERIMENT_STATUS_PREREGISTERED,
    EXPERIMENT_STATUS_RUNNING,
    EXPERIMENT_STATUS_SUPERSEDED,
    EXPOSURE_STATE_EXPOSED_DEVELOPMENT,
    EXPOSURE_STATE_EXPOSED_FINAL,
    EXPOSURE_STATE_EXPOSED_INVALID_FOR_FINAL,
    EXPOSURE_STATE_UNEXPOSED,
    FOLD_PROTOCOL_DEFAULT,
    G0_BLOCKED_FINAL_DATA_LEAKAGE,
    G0_BLOCKED_INVALID_DATASET_ROLE,
    G0_BLOCKED_MISSING_OWNER_AUTHORIZATION,
    G0_BLOCKED_OBJECTIVE_UNDEFINED,
    G0_BLOCKED_UNREGISTERED_EXPERIMENT,
    INFLUENCE_DESIGN_INFLUENCING,
    INFLUENCE_DIAGNOSTIC_ONLY,
    INFLUENCE_NONE,
    OBJECTIVE_KIND_DETECTION_VALIDITY,
    OBJECTIVE_KIND_ECONOMIC_FORBIDDEN,
    OBJECTIVE_KIND_INFORMATION,
    OBJECTIVE_KIND_REPRESENTATION_DIAGNOSTIC,
    POLICY_AUTHORITY_KIND_MUF,
    PROVENANCE_DEVELOPMENT_FIT,
    PROVENANCE_PREDEFINED_CONTRACT,
    QUALIFICATION_OBJECTIVE_DEFAULT,
    RESERVATION_STATUS_FINAL_INVALIDATED,
    RESERVATION_STATUS_FINAL_OPENED,
    RESERVATION_STATUS_FINAL_RESERVED,
    RESERVATION_STATUS_NOT_APPLICABLE,
    REVIEW_KIND_DEVELOPMENT_AUDIT,
    REVIEW_KIND_FINAL_AUDIT,
    S3_CONTRADICTORY_REVIEW_INFLUENCE,
    S3_ECONOMIC_OBJECTIVE_OUT_OF_SCOPE,
    S3_EXPERIMENT_DELETION_FORBIDDEN,
    S3_EXPERIMENT_IDENTITY_COLLISION,
    S3_EXPOSED_ANCESTRY_CONTAMINATION,
    S3_FINAL_DATA_LEAKED_INTO_WALK_FORWARD,
    S3_ILLEGAL_FINAL_DATA_OPERATION,
    S3_INFORMATION_OBJECTIVE_REQUIRES_ESTIMAND,
    S3_INVALID_DATASET_IDENTITY,
    S3_INVALID_DATASET_ROLE,
    S3_INVALID_EXPERIMENT_RECORD,
    S3_INVALID_FOLD_PROTOCOL,
    S3_INVALID_HUMAN_REVIEW,
    S3_INVALID_OBJECTIVE_ARTIFACT,
    S3_INVALID_POLICY_ARTIFACT,
    S3_INVALID_TURNING_POINT_PROMOTION,
    S3_NON_INFORMATION_OBJECTIVE_FORBIDS_ESTIMAND,
    S3_POLICY_REPRODUCTION_MISMATCH,
    S3_POLICY_SCOPE_MISMATCH,
    S3_ROLE_REASSIGNMENT_AFTER_EXPOSURE,
    S3_TEMPORAL_OVERLAP_NOT_INDEPENDENT,
    S3_UNDECLARED_SHARED_CONTENT_ANCESTRY,
    S3_UNREGISTERED_EXPERIMENT,
    AuthoritativeTurningPointRecord,
    DatasetIdentityArtifact,
    DatasetRoleArtifact,
    ExperimentRegistry,
    FoldPairSpec,
    FoldProtocolArtifact,
    G0CalibrationGateCertificate,
    HumanReviewRecord,
    ObjectiveArtifact,
    PolicyArtifact,
    PolicyScopeMismatch,
    SelectionBlockedError,
    evaluate_g0_calibration_gate,
    promote_swing_witness_with_policy_artifact,
    query_promoted_turning_points_as_of,
    reassign_dataset_role,
    record_dataset_exposure,
    verify_dataset_independence_and_ancestry,
    verify_policy_artifact_reproduction,
)
import trading_system.market_understanding.policy_governance as policy_governance_mod
from trading_system.market_understanding.price_path import (
    PublishedOhlcBarFact,
    exact_metric,
)
from trading_system.research.information_time import (
    INFORMATION_KEY_VERSION,
    InformationKey,
    InformationPhase,
)
from trading_system.structure.swing_detector import EmpiricalConfirmationPolicy


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


def mk_bar(pos: int, high: float, low: float, *, dataset: str = "DS-DEV-FIT") -> PublishedOhlcBarFact:
    mid = (high + low) / 2.0
    return PublishedOhlcBarFact(
        open_price=mid,
        high_price=high,
        low_price=low,
        close_price=mid,
        availability_key=k(pos),
        source_identity=SOURCE,
        dataset_identity=dataset,
        published_bar_record_ref=f"bar#{pos}",
    )


def sample_bars() -> list[PublishedOhlcBarFact]:
    return [
        mk_bar(1, 10.0, 9.0),
        mk_bar(2, 11.0, 10.0),
        mk_bar(3, 10.8, 10.5),
        mk_bar(4, 10.6, 10.0),
        mk_bar(5, 11.2, 10.2),
    ]


def sample_objective(
    *,
    obj_id: str = "obj-det-v1",
    kind: str = OBJECTIVE_KIND_DETECTION_VALIDITY,
    estimands: tuple[str, ...] = (),
    roles: tuple[str, ...] = (DATASET_ROLE_DEVELOPMENT_FIT, DATASET_ROLE_DEVELOPMENT_SELECTION),
) -> ObjectiveArtifact:
    return ObjectiveArtifact.create(
        objective_id=obj_id,
        objective_kind=kind,
        semantic_definition="Causal structural detection validity check on development data",
        estimand_refs=estimands,
        dataset_role_permissions=roles,
        aggregation_contract="EXACT_COUNT_AND_PASS_RATE",
        missingness_contract="FAIL_CLOSED_ON_UNEXPECTED_MISSING",
        tie_contract="PRESERVE_TIED_CANDIDATES_NO_WINNER",
        comparison_direction=TypedState.NOT_APPLICABLE,
        creation_key=k(1),
        code_hash="c" * 64,
        owner_authorization_ref="owner-auth-obj-01",
    )


def sample_ds_identity(
    ds_id: str = "DS-DEV-FIT",
    *,
    content_hash: str = "1" * 64,
    start_pos: int = 1,
    end_pos: int = 100,
    parents: tuple[str, ...] = (),
    timeline: str = TIMELINE,
) -> DatasetIdentityArtifact:
    return DatasetIdentityArtifact.create(
        dataset_id=ds_id,
        content_hash=content_hash,
        source_identity=SOURCE,
        timeline_id=timeline,
        start_key=k(start_pos, timeline=timeline),
        end_key=k(end_pos, timeline=timeline),
        transformation_spec_hash="2" * 64,
        parent_dataset_ids=parents,
        creation_code_hash="3" * 64,
        semantic_schema_hash="4" * 64,
    )


def sample_ds_role(
    ds_identity: DatasetIdentityArtifact,
    *,
    role: str = DATASET_ROLE_DEVELOPMENT_FIT,
    assign_pos: int = 1,
) -> DatasetRoleArtifact:
    if role == DATASET_ROLE_FINAL_EVALUATION_LOCKED:
        perm = ("FINAL_LOCKED_PROTOCOL_EVALUATION",)
        proh = ("DEVELOPMENT_FIT", "PARAMETER_CALIBRATION", "REPRESENTATION_SELECTION")
    elif role == DATASET_ROLE_DEVELOPMENT_SELECTION:
        perm = ("DEVELOPMENT_SELECTION", "STRUCTURAL_QUALIFICATION")
        proh = ("FINAL_LOCKED_CLAIM",)
    else:
        perm = ("DEVELOPMENT_FIT", "PARAMETER_CALIBRATION")
        proh = ("FINAL_LOCKED_CLAIM",)
    return DatasetRoleArtifact.create(
        dataset_identity=ds_identity,
        role=role,
        role_assignment_key=k(assign_pos, timeline=ds_identity.timeline_id),
        permitted_operations=perm,
        prohibited_operations=proh,
        owner_authorization_ref=f"owner-auth-role-{ds_identity.dataset_id}",
    )


# 1 — Standing defaults: QualificationObjective is UNDEFINED and FoldProtocol is NOT_CONFIGURED
def test_muf_s3_01_standing_defaults_and_objective_contracts():
    assert QUALIFICATION_OBJECTIVE_DEFAULT is TypedState.UNDEFINED
    assert FOLD_PROTOCOL_DEFAULT is TypedState.NOT_CONFIGURED

    obj_det = sample_objective(kind=OBJECTIVE_KIND_DETECTION_VALIDITY)
    assert obj_det.objective_kind == OBJECTIVE_KIND_DETECTION_VALIDITY
    assert obj_det.estimand_refs == ()

    obj_diag = sample_objective(
        obj_id="obj-diag-v1", kind=OBJECTIVE_KIND_REPRESENTATION_DIAGNOSTIC
    )
    assert obj_diag.objective_kind == OBJECTIVE_KIND_REPRESENTATION_DIAGNOSTIC

    obj_info = sample_objective(
        obj_id="obj-info-v1",
        kind=OBJECTIVE_KIND_INFORMATION,
        estimands=("estimand-hash-01",),
    )
    assert obj_info.estimand_refs == ("estimand-hash-01",)


# 2 — ObjectiveArtifact gates: ECONOMIC_OBJECTIVE forbidden, INFORMATION_OBJECTIVE requires Estimand (Attack 28)
def test_muf_s3_02_objective_fail_closed_gates():
    # ECONOMIC_OBJECTIVE is out of scope in MUF (D1-1)
    with pytest.raises(SchemaViolation) as exc_econ:
        sample_objective(kind=OBJECTIVE_KIND_ECONOMIC_FORBIDDEN)
    assert S3_ECONOMIC_OBJECTIVE_OUT_OF_SCOPE in str(exc_econ.value)

    # INFORMATION_OBJECTIVE without Estimand rejected (D1-1, D1-17, Attack 28)
    with pytest.raises(SchemaViolation) as exc_info:
        sample_objective(kind=OBJECTIVE_KIND_INFORMATION, estimands=())
    assert S3_INFORMATION_OBJECTIVE_REQUIRES_ESTIMAND in str(exc_info.value)

    # Non-information objective with Estimand rejected
    with pytest.raises(SchemaViolation) as exc_non_info:
        sample_objective(
            kind=OBJECTIVE_KIND_DETECTION_VALIDITY, estimands=("estimand-01",)
        )
    assert S3_NON_INFORMATION_OBJECTIVE_FORBIDS_ESTIMAND in str(exc_non_info.value)

    # Tampered objective_hash rejected (Attack 40)
    obj = sample_objective()
    with pytest.raises(SchemaViolation) as exc_hash:
        replace(obj, semantic_definition="altered definition")
    assert S3_INVALID_OBJECTIVE_ARTIFACT in str(exc_hash.value)


# 3 — DatasetIdentityArtifact & ancestry/overlap detection (Attacks 31, 32, 33)
def test_muf_s3_03_dataset_identity_and_ancestry_firewall():
    ds_raw_final = sample_ds_identity(
        "DS-FINAL-RAW", content_hash="a" * 64, start_pos=201, end_pos=300
    )
    role_raw_final = sample_ds_role(
        ds_raw_final, role=DATASET_ROLE_FINAL_EVALUATION_LOCKED
    )
    # Expose the final dataset
    role_raw_final_exposed = record_dataset_exposure(
        role_raw_final,
        event_id="exp-final-1",
        exposure_key=k(301),
        exposure_kind="FINAL_OPEN",
        actor_or_protocol_ref="proto-1",
        authorized_final_open=True,
    )
    assert role_raw_final_exposed.exposure_state == EXPOSURE_STATE_EXPOSED_FINAL

    # Attack 31: derived dataset from exposed final data cannot claim fresh unexposed final eligibility
    ds_derived = sample_ds_identity(
        "DS-FINAL-DERIVED",
        content_hash="b" * 64,
        start_pos=201,
        end_pos=300,
        parents=("DS-FINAL-RAW",),
    )
    with pytest.raises(SchemaViolation) as exc_a31:
        verify_dataset_independence_and_ancestry(
            ds_derived,
            known_identities=(ds_raw_final,),
            known_roles={"DS-FINAL-RAW": role_raw_final_exposed},
            require_unexposed_final_eligibility=True,
        )
    assert S3_EXPOSED_ANCESTRY_CONTAMINATION in str(exc_a31.value)

    # Attack 32: dataset with identical content_hash hiding parent_dataset_ids=() rejected
    ds_hidden_copy = sample_ds_identity(
        "DS-HIDDEN-COPY",
        content_hash="a" * 64,
        start_pos=401,
        end_pos=500,
        parents=(),
    )
    with pytest.raises(SchemaViolation) as exc_a32:
        verify_dataset_independence_and_ancestry(
            ds_hidden_copy,
            known_identities=(ds_raw_final,),
            known_roles={"DS-FINAL-RAW": role_raw_final_exposed},
        )
    assert S3_UNDECLARED_SHARED_CONTENT_ANCESTRY in str(exc_a32.value)

    # Attack 33: temporally overlapping dataset on same source/timeline without parent link rejected
    ds_overlapping = sample_ds_identity(
        "DS-OVERLAP",
        content_hash="e" * 64,
        start_pos=250,
        end_pos=350,
        parents=(),
    )
    with pytest.raises(SchemaViolation) as exc_a33:
        verify_dataset_independence_and_ancestry(
            ds_overlapping,
            known_identities=(ds_raw_final,),
            known_roles={"DS-FINAL-RAW": role_raw_final_exposed},
        )
    assert S3_TEMPORAL_OVERLAP_NOT_INDEPENDENT in str(exc_a33.value)


# 4 — DatasetRoleArtifact: Reserve != Open (D2-6), second open invalidation (Attacks 30 & 49), and no reassignment after exposure (Attack 46)
def test_muf_s3_04_dataset_role_reserve_vs_open_and_reassignment_firewall():
    ds_final = sample_ds_identity("DS-FINAL", start_pos=201, end_pos=300)
    role_final = sample_ds_role(ds_final, role=DATASET_ROLE_FINAL_EVALUATION_LOCKED)

    # D2-6 (I-RES-1): Reservation is NOT exposure
    assert role_final.reservation_status == RESERVATION_STATUS_FINAL_RESERVED
    assert role_final.exposure_state == EXPOSURE_STATE_UNEXPOSED
    assert role_final.exposure_events == ()

    # First authorized open -> EXPOSED_FINAL / FINAL_EVALUATION_OPENED
    opened_once = record_dataset_exposure(
        role_final,
        event_id="open-1",
        exposure_key=k(301),
        exposure_kind="AUTHORIZED_PROTOCOL_OPEN",
        actor_or_protocol_ref="protocol-v1",
        authorized_final_open=True,
    )
    assert opened_once.exposure_state == EXPOSURE_STATE_EXPOSED_FINAL
    assert opened_once.reservation_status == RESERVATION_STATUS_FINAL_OPENED

    # Attacks 30 & 49: second open attempt on already-exposed final dataset transitions to EXPOSED_INVALID_FOR_FINAL_SELECTION
    opened_twice = record_dataset_exposure(
        opened_once,
        event_id="open-2",
        exposure_key=k(302),
        exposure_kind="SECOND_PROTOCOL_OPEN",
        actor_or_protocol_ref="protocol-v2",
        authorized_final_open=True,
    )
    assert opened_twice.exposure_state == EXPOSURE_STATE_EXPOSED_INVALID_FOR_FINAL
    assert opened_twice.reservation_status == RESERVATION_STATUS_FINAL_INVALIDATED

    # Premature inspection without authorized_final_open on reserved final data invalidates it immediately (I-RES-2)
    premature_inspected = record_dataset_exposure(
        role_final,
        event_id="peek-1",
        exposure_key=k(250),
        exposure_kind="UNAUTHORIZED_INSPECTION",
        actor_or_protocol_ref="user-peek",
        authorized_final_open=False,
    )
    assert premature_inspected.exposure_state == EXPOSURE_STATE_EXPOSED_INVALID_FOR_FINAL

    # Attack 46: Development fold cannot be reassigned to FINAL_EVALUATION_LOCKED after exposure (I-DR-1, I-WF-1)
    ds_dev = sample_ds_identity("DS-DEV", start_pos=1, end_pos=100)
    role_dev = sample_ds_role(ds_dev, role=DATASET_ROLE_DEVELOPMENT_SELECTION)
    role_dev_exposed = record_dataset_exposure(
        role_dev,
        event_id="dev-eval-1",
        exposure_key=k(101),
        exposure_kind="DEV_SELECTION_RUN",
        actor_or_protocol_ref="exp-1",
    )
    assert role_dev_exposed.exposure_state == EXPOSURE_STATE_EXPOSED_DEVELOPMENT

    with pytest.raises(SchemaViolation) as exc_a46:
        reassign_dataset_role(
            role_dev_exposed,
            dataset_identity=ds_dev,
            new_role=DATASET_ROLE_FINAL_EVALUATION_LOCKED,
            reassignment_key=k(102),
            permitted_operations=("FINAL_LOCKED_PROTOCOL_EVALUATION",),
            prohibited_operations=("DEVELOPMENT_FIT",),
            owner_authorization_ref="owner-re-auth",
        )
    assert S3_ROLE_REASSIGNMENT_AFTER_EXPOSURE in str(exc_a46.value)


# 5 — FoldProtocolArtifact & Walk-Forward vs Final Data Firewall (D2-18, Attack 47)
def test_muf_s3_05_fold_protocol_and_walk_forward_firewall():
    ds_fit = sample_ds_identity("DS-FIT-1", content_hash="1" * 64, start_pos=1, end_pos=50)
    ds_sel = sample_ds_identity("DS-SEL-1", content_hash="2" * 64, start_pos=51, end_pos=100)
    ds_final = sample_ds_identity("DS-FINAL-1", content_hash="3" * 64, start_pos=101, end_pos=150)

    r_fit = sample_ds_role(ds_fit, role=DATASET_ROLE_DEVELOPMENT_FIT)
    r_sel = sample_ds_role(ds_sel, role=DATASET_ROLE_DEVELOPMENT_SELECTION)
    r_final = sample_ds_role(ds_final, role=DATASET_ROLE_FINAL_EVALUATION_LOCKED)

    id_map = {d.dataset_id: d for d in (ds_fit, ds_sel, ds_final)}
    role_map = {r.dataset_id: r for r in (r_fit, r_sel, r_final)}

    # Valid walk-forward protocol
    proto = FoldProtocolArtifact.create(
        protocol_id="wf-proto-v1",
        timeline_id=TIMELINE,
        folds=(FoldPairSpec(0, "DS-FIT-1", "DS-SEL-1"),),
        dataset_identities=id_map,
        dataset_roles=role_map,
        owner_authorization_ref="owner-wf-auth-1",
    )
    assert len(proto.folds) == 1

    # Attack 47a: Walk-forward fold directly referencing FINAL_EVALUATION_LOCKED dataset rejected
    with pytest.raises(SchemaViolation) as exc_a47a:
        FoldProtocolArtifact.create(
            protocol_id="wf-bad-1",
            timeline_id=TIMELINE,
            folds=(FoldPairSpec(0, "DS-FIT-1", "DS-FINAL-1"),),
            dataset_identities=id_map,
            dataset_roles=role_map,
            owner_authorization_ref="owner-wf-auth-1",
        )
    assert S3_FINAL_DATA_LEAKED_INTO_WALK_FORWARD in str(exc_a47a.value)

    # Attack 47b: Expanding TRAIN fold overlapping reserved FINAL_EVALUATION_LOCKED region rejected
    ds_expanding_fit = sample_ds_identity(
        "DS-FIT-EXPANDED", content_hash="9" * 64, start_pos=1, end_pos=120
    )
    r_expanding_fit = sample_ds_role(ds_expanding_fit, role=DATASET_ROLE_DEVELOPMENT_FIT)
    ds_sel_late = sample_ds_identity(
        "DS-SEL-LATE", content_hash="8" * 64, start_pos=121, end_pos=140
    )
    r_sel_late = sample_ds_role(ds_sel_late, role=DATASET_ROLE_DEVELOPMENT_SELECTION)

    with pytest.raises(SchemaViolation) as exc_a47b:
        FoldProtocolArtifact.create(
            protocol_id="wf-bad-2",
            timeline_id=TIMELINE,
            folds=(FoldPairSpec(0, "DS-FIT-EXPANDED", "DS-SEL-LATE"),),
            dataset_identities={
                **id_map,
                "DS-FIT-EXPANDED": ds_expanding_fit,
                "DS-SEL-LATE": ds_sel_late,
            },
            dataset_roles={
                **role_map,
                "DS-FIT-EXPANDED": r_expanding_fit,
                "DS-SEL-LATE": r_sel_late,
            },
            owner_authorization_ref="owner-wf-auth-1",
        )
    assert S3_FINAL_DATA_LEAKED_INTO_WALK_FORWARD in str(exc_a47b.value)


# 6 — HumanReviewRecord & Automatic Final Contamination Tripwire (D1-3, I-HR-1..2, Attack 12)
def test_muf_s3_06_human_review_and_final_contamination_tripwire():
    ds_final = sample_ds_identity("DS-FINAL", start_pos=201, end_pos=300)
    role_final = sample_ds_role(ds_final, role=DATASET_ROLE_FINAL_EVALUATION_LOCKED)

    # Purely diagnostic final audit with zero requested_changes -> EXPOSED_FINAL
    rev_clean, role_after_clean = HumanReviewRecord.create_and_apply(
        review_id="rev-final-clean",
        role_artifact=role_final,
        review_kind=REVIEW_KIND_FINAL_AUDIT,
        review_key=k(305),
        reviewer="owner",
        charts_viewed=("chart-final-1",),
        observations=("Structure looks consistent with contract",),
        requested_changes=(),
        change_influence=INFLUENCE_DIAGNOSTIC_ONLY,
    )
    assert rev_clean.change_influence == INFLUENCE_DIAGNOSTIC_ONLY
    assert role_after_clean.exposure_state == EXPOSURE_STATE_EXPOSED_FINAL

    # Attack 12: OOS/Final chart review requests changes -> automatically invalidates final dataset!
    rev_dirty, role_after_dirty = HumanReviewRecord.create_and_apply(
        review_id="rev-final-dirty",
        role_artifact=role_final,
        review_kind=REVIEW_KIND_FINAL_AUDIT,
        review_key=k(305),
        reviewer="owner",
        charts_viewed=("chart-final-1",),
        observations=("Missed a small pullback on bar 240",),
        requested_changes=("Lower confirmation quantile to catch bar 240",),
        change_influence=INFLUENCE_DESIGN_INFLUENCING,
    )
    assert rev_dirty.change_influence == INFLUENCE_DESIGN_INFLUENCING
    assert role_after_dirty.exposure_state == EXPOSURE_STATE_EXPOSED_INVALID_FOR_FINAL
    assert role_after_dirty.reservation_status == RESERVATION_STATUS_FINAL_INVALIDATED

    # Lying about change_influence=NONE when requested_changes is non-empty fails closed
    with pytest.raises(SchemaViolation) as exc_lie:
        HumanReviewRecord.create_and_apply(
            review_id="rev-lie",
            role_artifact=role_final,
            review_kind=REVIEW_KIND_FINAL_AUDIT,
            review_key=k(305),
            reviewer="owner",
            charts_viewed=("chart-1",),
            observations=("obs",),
            requested_changes=("change parameter X",),
            change_influence=INFLUENCE_NONE,
        )
    assert S3_CONTRADICTORY_REVIEW_INFLUENCE in str(exc_lie.value)


# 7 — ExperimentRegistry: preregistration, append-only failure retention (Attack 13), and collision prevention (Attack 14)
def test_muf_s3_07_experiment_registry_attacks_13_and_14():
    reg = ExperimentRegistry()
    obj = sample_objective()

    # Transition before preregistration rejected (I-ER-1)
    with pytest.raises(SchemaViolation) as exc_unreg:
        reg.record_transition(
            experiment_id="exp-001",
            new_status=EXPERIMENT_STATUS_RUNNING,
            transition_key=k(2),
        )
    assert S3_UNREGISTERED_EXPERIMENT in str(exc_unreg.value)

    rec0 = reg.preregister(
        experiment_id="exp-001",
        preregistration_key=k(1),
        representation_spec_hash="rep-alpha-v1",
        policy_artifact_hashes=("pol-hash-1",),
        objective_artifact_hash=obj.objective_hash,
        dataset_identities_by_role={DATASET_ROLE_DEVELOPMENT_FIT: "DS-DEV-FIT"},
        code_hash="code-v1",
        fit_protocol_hash="fit-proto-v1",
    )
    assert rec0.status == EXPERIMENT_STATUS_PREREGISTERED

    # Attack 14: Re-registering same experiment_id with different objective/parameters rejected (I-ER-3)
    obj2 = sample_objective(obj_id="obj-det-v2")
    with pytest.raises(SchemaViolation) as exc_a14:
        reg.preregister(
            experiment_id="exp-001",
            preregistration_key=k(2),
            representation_spec_hash="rep-alpha-v1",
            policy_artifact_hashes=("pol-hash-1",),
            objective_artifact_hash=obj2.objective_hash,
            dataset_identities_by_role={DATASET_ROLE_DEVELOPMENT_FIT: "DS-DEV-FIT"},
            code_hash="code-v1",
            fit_protocol_hash="fit-proto-v1",
        )
    assert S3_EXPERIMENT_IDENTITY_COLLISION in str(exc_a14.value)

    # Transition to RUNNING then FAILED
    reg.record_transition(
        experiment_id="exp-001",
        new_status=EXPERIMENT_STATUS_RUNNING,
        transition_key=k(2),
    )
    failed_rec = reg.record_transition(
        experiment_id="exp-001",
        new_status=EXPERIMENT_STATUS_FAILED,
        transition_key=k(3),
        failure_refs=("failure-log-001",),
    )
    assert failed_rec.status == EXPERIMENT_STATUS_FAILED
    assert failed_rec.experiment_hash == rec0.experiment_hash

    # Attack 13a: Deleting failed experiment fails closed (I-ER-2, I-ER-4)
    with pytest.raises(ImmutabilityViolation) as exc_a13a:
        reg.delete_experiment("exp-001")
    assert S3_EXPERIMENT_DELETION_FORBIDDEN in str(exc_a13a.value)

    # Attack 13b: Overwriting FAILED experiment as COMPLETED fails closed
    with pytest.raises(SchemaViolation) as exc_a13b:
        reg.record_transition(
            experiment_id="exp-001",
            new_status=EXPERIMENT_STATUS_COMPLETED,
            transition_key=k(4),
            result_refs=("forged-success",),
        )
    assert S3_EXPERIMENT_DELETION_FORBIDDEN in str(exc_a13b.value)

    # Superseding a failed experiment with a new experiment_id is permitted and preserves full history
    rec_new = reg.preregister(
        experiment_id="exp-002",
        preregistration_key=k(4),
        representation_spec_hash="rep-alpha-v2",
        policy_artifact_hashes=("pol-hash-2",),
        objective_artifact_hash=obj.objective_hash,
        dataset_identities_by_role={DATASET_ROLE_DEVELOPMENT_FIT: "DS-DEV-FIT"},
        code_hash="code-v2",
        fit_protocol_hash="fit-proto-v1",
        supersedes_experiment_id="exp-001",
    )
    assert rec_new.supersedes_experiment_id == "exp-001"
    sup_old = reg.record_transition(
        experiment_id="exp-001",
        new_status=EXPERIMENT_STATUS_SUPERSEDED,
        transition_key=k(4),
    )
    assert sup_old.status == EXPERIMENT_STATUS_SUPERSEDED
    assert len(reg.history()) == 5


# 8 — PolicyArtifact & AuthoritativeTurningPointRecord promotion from S2 witness (D1-4, D2-1, Attack 25)
def test_muf_s3_08_policy_artifact_and_turning_point_promotion_attack_25():
    bars = sample_bars()
    pol_1 = EmpiricalConfirmationPolicy(
        quantile=0.5, prior_continuation_reversals=(0.01, 0.02)
    )
    pol_2 = EmpiricalConfirmationPolicy(
        quantile=0.25, prior_continuation_reversals=(0.01, 0.02)
    )
    bundle_1 = adapt_detector_witness_stream(bars, confirmation_policy=pol_1)
    bundle_2 = adapt_detector_witness_stream(bars, confirmation_policy=pol_2)

    ev_w1 = bundle_1.swing_event_witnesses[0]
    ev_w2 = bundle_2.swing_event_witnesses[0]
    # Both confirmed the same HIGH origin at bar index 1, confirmed at bar index 2
    assert ev_w1.origin_key == ev_w2.origin_key
    assert ev_w1.availability_key == ev_w2.availability_key

    p_art_1 = PolicyArtifact.create(
        policy_id="muf-pol-1",
        detector_policy_witness_ref=str(bundle_1.policy_witness_ref),
        scope_timeline_id=TIMELINE,
        scope_axis=InformationAxis.POSITIONAL,
        scope_representation_id="ALPHA_V1",
        calibration_provenance_kind=PROVENANCE_PREDEFINED_CONTRACT,
        reproduction_recipe_hash="recipe-1",
        effective_from_key=k(1),
        owner_authorization_ref="owner-pol-auth-1",
    )
    p_art_2 = PolicyArtifact.create(
        policy_id="muf-pol-2",
        detector_policy_witness_ref=str(bundle_2.policy_witness_ref),
        scope_timeline_id=TIMELINE,
        scope_axis=InformationAxis.POSITIONAL,
        scope_representation_id="ALPHA_V1",
        calibration_provenance_kind=PROVENANCE_PREDEFINED_CONTRACT,
        reproduction_recipe_hash="recipe-2",
        effective_from_key=k(1),
        owner_authorization_ref="owner-pol-auth-2",
    )

    assert verify_policy_artifact_reproduction(
        p_art_1,
        recomputed_detector_policy_witness_ref=str(bundle_1.policy_witness_ref),
        recomputed_recipe_hash="recipe-1",
    )
    with pytest.raises(SchemaViolation) as exc_repro:
        verify_policy_artifact_reproduction(
            p_art_1,
            recomputed_detector_policy_witness_ref="wrong-ref",
            recomputed_recipe_hash="recipe-1",
        )
    assert S3_POLICY_REPRODUCTION_MISMATCH in str(exc_repro.value)

    tp_1 = promote_swing_witness_with_policy_artifact(ev_w1, policy_artifact=p_art_1)
    tp_2 = promote_swing_witness_with_policy_artifact(ev_w2, policy_artifact=p_art_2)

    assert tp_1.as_record().record_type == TURNING_POINT_RECORD_TYPE
    assert tp_1.origin_key == bars[1].availability_key
    assert tp_1.availability_key == bars[2].availability_key
    assert tp_1.authority_policy_hash == p_art_1.policy_hash

    # Attack 25 (I-WPI-1/4): Same origin under two different PolicyArtifacts produces two distinct
    # AuthoritativeTurningPointRecord identities and two distinct WaveProcessIdentityBasis hashes!
    assert tp_1.turning_point_id != tp_2.turning_point_id

    basis_1 = WaveProcessIdentityBasis(
        representation_spec_hash="rep-alpha-v1",
        authoritative_start_turning_point_id=tp_1.to_turning_point_reference(),
        authority_policy_hash=p_art_1.policy_hash,
        timeline_id=TIMELINE,
        intrinsic_representation_key_or_NOT_APPLICABLE=TypedState.NOT_APPLICABLE,
    )
    basis_2 = WaveProcessIdentityBasis(
        representation_spec_hash="rep-alpha-v1",
        authoritative_start_turning_point_id=tp_2.to_turning_point_reference(),
        authority_policy_hash=p_art_2.policy_hash,
        timeline_id=TIMELINE,
        intrinsic_representation_key_or_NOT_APPLICABLE=TypedState.NOT_APPLICABLE,
    )
    assert wave_process_identity(basis_1) != wave_process_identity(basis_2)


# 9 — Promotion scope mismatch & Origin != Availability on promoted turning points
def test_muf_s3_09_promotion_scope_mismatch_and_causal_as_of_query():
    bars = sample_bars()
    pol = EmpiricalConfirmationPolicy(
        quantile=0.5, prior_continuation_reversals=(0.01, 0.02)
    )
    bundle = adapt_detector_witness_stream(bars, confirmation_policy=pol)
    ev = bundle.swing_event_witnesses[0]

    p_art = PolicyArtifact.create(
        policy_id="muf-pol-1",
        detector_policy_witness_ref=str(bundle.policy_witness_ref),
        scope_timeline_id=TIMELINE,
        scope_axis=InformationAxis.POSITIONAL,
        scope_representation_id="ALPHA_V1",
        calibration_provenance_kind=PROVENANCE_PREDEFINED_CONTRACT,
        reproduction_recipe_hash="recipe-1",
        effective_from_key=k(1),
        owner_authorization_ref="owner-pol-auth-1",
    )

    # CandidateWitnessRecord cannot be promoted (only SwingEventWitnessRecord)
    with pytest.raises(SchemaViolation):
        promote_swing_witness_with_policy_artifact(
            bundle.candidate_witnesses[2],  # type: ignore[arg-type]
            policy_artifact=p_art,
        )

    # Mismatched timeline scope rejected (I-PAUTH-3: PolicyScopeMismatch)
    p_other_tl = PolicyArtifact.create(
        policy_id="muf-pol-other-tl",
        detector_policy_witness_ref=str(bundle.policy_witness_ref),
        scope_timeline_id="OTHER_TL",
        scope_axis=InformationAxis.POSITIONAL,
        scope_representation_id="ALPHA_V1",
        calibration_provenance_kind=PROVENANCE_PREDEFINED_CONTRACT,
        reproduction_recipe_hash="recipe-1",
        effective_from_key=k(1, timeline="OTHER_TL"),
        owner_authorization_ref="owner-pol-auth-1",
    )
    with pytest.raises(PolicyScopeMismatch):
        promote_swing_witness_with_policy_artifact(ev, policy_artifact=p_other_tl)

    # Mismatched detector_policy_witness_ref rejected (PolicyScopeMismatch)
    p_other_ref = PolicyArtifact.create(
        policy_id="muf-pol-other-ref",
        detector_policy_witness_ref="different-witness-spec-hash",
        scope_timeline_id=TIMELINE,
        scope_axis=InformationAxis.POSITIONAL,
        scope_representation_id="ALPHA_V1",
        calibration_provenance_kind=PROVENANCE_PREDEFINED_CONTRACT,
        reproduction_recipe_hash="recipe-1",
        effective_from_key=k(1),
        owner_authorization_ref="owner-pol-auth-1",
    )
    with pytest.raises(PolicyScopeMismatch):
        promote_swing_witness_with_policy_artifact(ev, policy_artifact=p_other_ref)

    # Policy effective_from_key after witness availability_key rejected (PrematureAvailability)
    p_future = PolicyArtifact.create(
        policy_id="muf-pol-future",
        detector_policy_witness_ref=str(bundle.policy_witness_ref),
        scope_timeline_id=TIMELINE,
        scope_axis=InformationAxis.POSITIONAL,
        scope_representation_id="ALPHA_V1",
        calibration_provenance_kind=PROVENANCE_PREDEFINED_CONTRACT,
        reproduction_recipe_hash="recipe-1",
        effective_from_key=k(5),
        owner_authorization_ref="owner-pol-auth-1",
    )
    with pytest.raises(PrematureAvailability):
        promote_swing_witness_with_policy_artifact(ev, policy_artifact=p_future)

    # Promoted turning point respects Origin != Availability in query_promoted_turning_points_as_of
    tp = promote_swing_witness_with_policy_artifact(ev, policy_artifact=p_art)
    # Invisible at origin bar (index 1, key k(2))
    assert (
        query_promoted_turning_points_as_of(
            (tp,),
            timeline_id=TIMELINE,
            axis=InformationAxis.POSITIONAL,
            at_key=bars[1].availability_key,
        )
        == ()
    )
    # Visible at confirmation bar (index 2, key k(3))
    assert query_promoted_turning_points_as_of(
        (tp,),
        timeline_id=TIMELINE,
        axis=InformationAxis.POSITIONAL,
        at_key=bars[2].availability_key,
    ) == (tp,)

    # Rejects unpromoted witness in factual query (I-PAUTH-1)
    with pytest.raises(SchemaViolation):
        query_promoted_turning_points_as_of(
            (ev,),  # type: ignore[arg-type]
            timeline_id=TIMELINE,
            axis=InformationAxis.POSITIONAL,
            at_key=bars[2].availability_key,
        )


# 10 — Gate G0 (evaluate_g0_calibration_gate): blocks missing/invalid prerequisites and passes when complete
def test_muf_s3_10_gate_g0_calibration_authority_firewall():
    obj = sample_objective()
    ds_fit = sample_ds_identity("DS-DEV-FIT", content_hash="1" * 64, start_pos=1, end_pos=100)
    r_fit = sample_ds_role(ds_fit, role=DATASET_ROLE_DEVELOPMENT_FIT)
    ds_final = sample_ds_identity("DS-FINAL", content_hash="9" * 64, start_pos=201, end_pos=300)
    r_final = sample_ds_role(ds_final, role=DATASET_ROLE_FINAL_EVALUATION_LOCKED)

    reg = ExperimentRegistry()
    reg.preregister(
        experiment_id="exp-fit-01",
        preregistration_key=k(1),
        representation_spec_hash="rep-alpha-v1",
        policy_artifact_hashes=("pol-candidate-1",),
        objective_artifact_hash=obj.objective_hash,
        dataset_identities_by_role={DATASET_ROLE_DEVELOPMENT_FIT: "DS-DEV-FIT"},
        code_hash="code-v1",
        fit_protocol_hash="fit-proto-v1",
    )

    # 1) Missing objective -> G0_BLOCKED_OBJECTIVE_UNDEFINED
    with pytest.raises(SelectionBlockedError) as exc_g0_obj:
        evaluate_g0_calibration_gate(
            objective_artifact=QUALIFICATION_OBJECTIVE_DEFAULT,
            fit_dataset_identity=ds_fit,
            fit_dataset_role=r_fit,
            experiment_registry=reg,
            experiment_id="exp-fit-01",
            owner_fit_authorization_ref="owner-fit-auth-1",
        )
    assert G0_BLOCKED_OBJECTIVE_UNDEFINED in str(exc_g0_obj.value)

    # 2) Wrong dataset role (FINAL_EVALUATION_LOCKED instead of DEVELOPMENT_FIT) -> G0_BLOCKED_INVALID_DATASET_ROLE
    with pytest.raises(SelectionBlockedError) as exc_g0_role:
        evaluate_g0_calibration_gate(
            objective_artifact=obj,
            fit_dataset_identity=ds_final,
            fit_dataset_role=r_final,
            experiment_registry=reg,
            experiment_id="exp-fit-01",
            owner_fit_authorization_ref="owner-fit-auth-1",
        )
    assert G0_BLOCKED_INVALID_DATASET_ROLE in str(exc_g0_role.value)

    # 3) Fit dataset overlapping FINAL_EVALUATION_LOCKED dataset -> G0_BLOCKED_FINAL_DATA_LEAKAGE
    ds_fit_leaked = sample_ds_identity(
        "DS-DEV-FIT", content_hash="7" * 64, start_pos=150, end_pos=250
    )
    r_fit_leaked = sample_ds_role(ds_fit_leaked, role=DATASET_ROLE_DEVELOPMENT_FIT)
    with pytest.raises(SelectionBlockedError) as exc_g0_leak:
        evaluate_g0_calibration_gate(
            objective_artifact=obj,
            fit_dataset_identity=ds_fit_leaked,
            fit_dataset_role=r_fit_leaked,
            known_dataset_identities=(ds_final,),
            known_dataset_roles={"DS-FINAL": r_final},
            experiment_registry=reg,
            experiment_id="exp-fit-01",
            owner_fit_authorization_ref="owner-fit-auth-1",
        )
    assert G0_BLOCKED_FINAL_DATA_LEAKAGE in str(exc_g0_leak.value)

    # 4) Unregistered experiment -> G0_BLOCKED_UNREGISTERED_EXPERIMENT
    with pytest.raises(SelectionBlockedError) as exc_g0_exp:
        evaluate_g0_calibration_gate(
            objective_artifact=obj,
            fit_dataset_identity=ds_fit,
            fit_dataset_role=r_fit,
            known_dataset_identities=(ds_final,),
            known_dataset_roles={"DS-FINAL": r_final},
            experiment_registry=reg,
            experiment_id="non-existent-exp",
            owner_fit_authorization_ref="owner-fit-auth-1",
        )
    assert G0_BLOCKED_UNREGISTERED_EXPERIMENT in str(exc_g0_exp.value)

    # 5) Missing owner_fit_authorization_ref -> G0_BLOCKED_MISSING_OWNER_AUTHORIZATION
    with pytest.raises(SelectionBlockedError) as exc_g0_auth:
        evaluate_g0_calibration_gate(
            objective_artifact=obj,
            fit_dataset_identity=ds_fit,
            fit_dataset_role=r_fit,
            known_dataset_identities=(ds_final,),
            known_dataset_roles={"DS-FINAL": r_final},
            experiment_registry=reg,
            experiment_id="exp-fit-01",
            owner_fit_authorization_ref=TypedState.NOT_CONFIGURED,
        )
    assert G0_BLOCKED_MISSING_OWNER_AUTHORIZATION in str(exc_g0_auth.value)

    # 6) All 5 prerequisites satisfied -> emits immutable G0CalibrationGateCertificate
    cert = evaluate_g0_calibration_gate(
        objective_artifact=obj,
        fit_dataset_identity=ds_fit,
        fit_dataset_role=r_fit,
        known_dataset_identities=(ds_final,),
        known_dataset_roles={"DS-FINAL": r_final},
        experiment_registry=reg,
        experiment_id="exp-fit-01",
        owner_fit_authorization_ref="owner-fit-auth-1",
    )
    assert isinstance(cert, G0CalibrationGateCertificate)
    assert cert.gate_passed is True
    assert cert.objective_artifact_hash == obj.objective_hash


# 11 — Deep immutability & constructor tamper resistance across all S3 artifacts
def test_muf_s3_11_deep_immutability_and_tamper_resistance():
    obj = sample_objective()
    ds = sample_ds_identity()
    role = sample_ds_role(ds)

    with pytest.raises((ImmutabilityViolation, TypeError, AttributeError)):
        obj.objective_id = "mutated"  # type: ignore[misc]
    with pytest.raises((ImmutabilityViolation, TypeError, AttributeError)):
        ds.content_hash = "mutated"  # type: ignore[misc]
    with pytest.raises((ImmutabilityViolation, TypeError, AttributeError)):
        role.exposure_state = EXPOSURE_STATE_EXPOSED_FINAL  # type: ignore[misc]

    # Direct constructor tamper on role_artifact_hash or exposure_state without event
    with pytest.raises(SchemaViolation):
        replace(role, exposure_state=EXPOSURE_STATE_EXPOSED_DEVELOPMENT)
    with pytest.raises(SchemaViolation):
        replace(ds, content_hash="f" * 64)


# 12 — S0 AST guards on policy_governance.py & sealed S0/S1/S2 certificate integrity
def test_muf_s3_12_ast_guards_and_sealed_s0_s1_s2_certificates_untouched():
    import hashlib

    source_text = Path(policy_governance_mod.__file__).read_text(encoding="utf-8")
    assert scan_private_imports(source_text) == ()
    assert scan_prohibited_implementations(source_text) == ()
    assert scan_market_shape_implementations(source_text) == ()

    root = Path(__file__).resolve().parent.parent
    for cert_rel in (
        "docs/releases/MODULE_MUF_V1_S0_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S1_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S2_ACCEPTED_SRC_TESTS.sha256",
    ):
        cert_path = root / cert_rel
        lines = [
            ln.strip()
            for ln in cert_path.read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
        assert len(lines) > 0
        for line in lines:
            expected_sha, rel_file = line.split(None, 1)
            actual_sha = hashlib.sha256((root / rel_file).read_bytes()).hexdigest()
            assert actual_sha == expected_sha, (cert_rel, rel_file)


# 13 — ObjectiveArtifact boundary validation: empty roles, invalid comparison_direction, BAR_PRE_CLOSE creation_key
def test_muf_s3_13_objective_boundary_validation():
    with pytest.raises(SchemaViolation):
        sample_objective(roles=())
    with pytest.raises(SchemaViolation):
        sample_objective(roles=("UNKNOWN_ROLE",))
    with pytest.raises(SchemaViolation):
        ObjectiveArtifact.create(
            objective_id="obj-bad-dir",
            objective_kind=OBJECTIVE_KIND_DETECTION_VALIDITY,
            semantic_definition="def",
            estimand_refs=(),
            dataset_role_permissions=(DATASET_ROLE_DEVELOPMENT_FIT,),
            aggregation_contract="AGG",
            missingness_contract="MISS",
            tie_contract="TIE",
            comparison_direction="SIDEWAYS",
            creation_key=k(1),
            code_hash="c" * 64,
            owner_authorization_ref="auth-1",
        )
    with pytest.raises(IllegalCausalReference):
        ObjectiveArtifact.create(
            objective_id="obj-pre-close",
            objective_kind=OBJECTIVE_KIND_DETECTION_VALIDITY,
            semantic_definition="def",
            estimand_refs=(),
            dataset_role_permissions=(DATASET_ROLE_DEVELOPMENT_FIT,),
            aggregation_contract="AGG",
            missingness_contract="MISS",
            tie_contract="TIE",
            comparison_direction="MAXIMIZE",
            creation_key=k(1, phase=InformationPhase.BAR_PRE_CLOSE),
            code_hash="c" * 64,
            owner_authorization_ref="auth-1",
        )


# 14 — DatasetIdentityArtifact boundary validation: end_key < start_key, self-parenting, timeline mismatch
def test_muf_s3_14_dataset_identity_boundary_validation():
    # end_key < start_key rejected
    with pytest.raises(SchemaViolation):
        sample_ds_identity("DS-BAD-RANGE", start_pos=50, end_pos=10)

    # Self-parenting rejected
    with pytest.raises(SchemaViolation):
        sample_ds_identity("DS-SELF", parents=("DS-SELF",))

    # Timeline mismatch between timeline_id and start_key/end_key rejected
    with pytest.raises(InformationKeyViolation):
        DatasetIdentityArtifact.create(
            dataset_id="DS-TL-MISMATCH",
            content_hash="1" * 64,
            source_identity=SOURCE,
            timeline_id="TL_A",
            start_key=k(1, timeline="TL_B"),
            end_key=k(10, timeline="TL_B"),
            transformation_spec_hash="2" * 64,
            parent_dataset_ids=(),
            creation_code_hash="3" * 64,
            semantic_schema_hash="4" * 64,
        )


# 15 — DatasetRoleArtifact illegal final operations & contradictory permissions
def test_muf_s3_15_dataset_role_illegal_final_operations():
    ds_final = sample_ds_identity("DS-FINAL", start_pos=201, end_pos=300)

    # FINAL_EVALUATION_LOCKED cannot permit DEVELOPMENT_FIT (I-DR-2)
    with pytest.raises(SchemaViolation) as exc_ill:
        DatasetRoleArtifact.create(
            dataset_identity=ds_final,
            role=DATASET_ROLE_FINAL_EVALUATION_LOCKED,
            role_assignment_key=k(1),
            permitted_operations=("DEVELOPMENT_FIT",),
            prohibited_operations=("REPRESENTATION_SELECTION",),
            owner_authorization_ref="owner-1",
        )
    assert S3_ILLEGAL_FINAL_DATA_OPERATION in str(exc_ill.value)

    # Overlapping permitted and prohibited operations rejected
    with pytest.raises(SchemaViolation):
        DatasetRoleArtifact.create(
            dataset_identity=ds_final,
            role=DATASET_ROLE_DEVELOPMENT_FIT,
            role_assignment_key=k(1),
            permitted_operations=("DEVELOPMENT_FIT",),
            prohibited_operations=("DEVELOPMENT_FIT",),
            owner_authorization_ref="owner-1",
        )


# 16 — DatasetRoleArtifact reassignment before exposure succeeds; out-of-order exposure_events rejected
def test_muf_s3_16_reassignment_before_exposure_and_exposure_event_ordering():
    ds = sample_ds_identity("DS-1", start_pos=1, end_pos=100)
    r0 = sample_ds_role(ds, role=DATASET_ROLE_DEVELOPMENT_FIT, assign_pos=1)

    # Unexposed dataset CAN be reassigned at a non-decreasing key
    r1 = reassign_dataset_role(
        r0,
        dataset_identity=ds,
        new_role=DATASET_ROLE_DEVELOPMENT_SELECTION,
        reassignment_key=k(2),
        permitted_operations=("DEVELOPMENT_SELECTION",),
        prohibited_operations=("FINAL_LOCKED_CLAIM",),
        owner_authorization_ref="owner-2",
    )
    assert r1.role == DATASET_ROLE_DEVELOPMENT_SELECTION
    assert r1.exposure_state == EXPOSURE_STATE_UNEXPOSED

    # Backdated exposure event (< previous exposure event) rejected with PrematureAvailability
    r_exp1 = record_dataset_exposure(
        r1,
        event_id="ev-1",
        exposure_key=k(50),
        exposure_kind="DEV_EVAL",
        actor_or_protocol_ref="actor-1",
    )
    with pytest.raises(PrematureAvailability):
        record_dataset_exposure(
            r_exp1,
            event_id="ev-2",
            exposure_key=k(40),
            exposure_kind="DEV_EVAL_BACKDATED",
            actor_or_protocol_ref="actor-1",
        )


# 17 — FoldProtocolArtifact ordering & causal chronology checks (I-WF-1..3)
def test_muf_s3_17_fold_protocol_chronology_and_indexing():
    ds_fit = sample_ds_identity("DS-FIT", content_hash="1" * 64, start_pos=51, end_pos=100)
    ds_sel = sample_ds_identity("DS-SEL", content_hash="2" * 64, start_pos=1, end_pos=50)
    r_fit = sample_ds_role(ds_fit, role=DATASET_ROLE_DEVELOPMENT_FIT)
    r_sel = sample_ds_role(ds_sel, role=DATASET_ROLE_DEVELOPMENT_SELECTION)

    # Selection fold earlier than or overlapping fit fold rejected with PrematureAvailability
    with pytest.raises(PrematureAvailability):
        FoldProtocolArtifact.create(
            protocol_id="wf-reversed",
            timeline_id=TIMELINE,
            folds=(FoldPairSpec(0, "DS-FIT", "DS-SEL"),),
            dataset_identities={"DS-FIT": ds_fit, "DS-SEL": ds_sel},
            dataset_roles={"DS-FIT": r_fit, "DS-SEL": r_sel},
            owner_authorization_ref="owner-wf",
        )

    # Non-contiguous fold_index (starting at 1 instead of 0) rejected
    ds_fit_ok = sample_ds_identity("DS-FIT-OK", content_hash="3" * 64, start_pos=1, end_pos=50)
    ds_sel_ok = sample_ds_identity("DS-SEL-OK", content_hash="4" * 64, start_pos=51, end_pos=100)
    r_fit_ok = sample_ds_role(ds_fit_ok, role=DATASET_ROLE_DEVELOPMENT_FIT)
    r_sel_ok = sample_ds_role(ds_sel_ok, role=DATASET_ROLE_DEVELOPMENT_SELECTION)
    with pytest.raises(SchemaViolation) as exc_idx:
        FoldProtocolArtifact.create(
            protocol_id="wf-bad-idx",
            timeline_id=TIMELINE,
            folds=(FoldPairSpec(1, "DS-FIT-OK", "DS-SEL-OK"),),
            dataset_identities={"DS-FIT-OK": ds_fit_ok, "DS-SEL-OK": ds_sel_ok},
            dataset_roles={"DS-FIT-OK": r_fit_ok, "DS-SEL-OK": r_sel_ok},
            owner_authorization_ref="owner-wf",
        )
    assert S3_INVALID_FOLD_PROTOCOL in str(exc_idx.value)


# 18 — ExperimentRegistry: idempotent re-preregistration, terminal SUPERSEDED state, andCOMPLETED overwrite protection
def test_muf_s3_18_experiment_registry_idempotency_and_terminal_transitions():
    reg = ExperimentRegistry()
    obj = sample_objective()
    rec1 = reg.preregister(
        experiment_id="exp-idem",
        preregistration_key=k(1),
        representation_spec_hash="rep-alpha-v1",
        policy_artifact_hashes=("pol-1",),
        objective_artifact_hash=obj.objective_hash,
        dataset_identities_by_role={DATASET_ROLE_DEVELOPMENT_FIT: "DS-DEV-FIT"},
        code_hash="code-1",
        fit_protocol_hash="fit-1",
    )
    # Identical re-preregistration is idempotent
    rec1_again = reg.preregister(
        experiment_id="exp-idem",
        preregistration_key=k(1),
        representation_spec_hash="rep-alpha-v1",
        policy_artifact_hashes=("pol-1",),
        objective_artifact_hash=obj.objective_hash,
        dataset_identities_by_role={DATASET_ROLE_DEVELOPMENT_FIT: "DS-DEV-FIT"},
        code_hash="code-1",
        fit_protocol_hash="fit-1",
    )
    assert rec1_again == rec1
    assert len(reg.history()) == 1

    # Complete the experiment
    reg.record_transition(
        experiment_id="exp-idem",
        new_status=EXPERIMENT_STATUS_COMPLETED,
        transition_key=k(2),
        result_refs=("res-1",),
    )
    # Overwriting COMPLETED as FAILED or RUNNING is forbidden
    with pytest.raises(SchemaViolation) as exc_comp:
        reg.record_transition(
            experiment_id="exp-idem",
            new_status=EXPERIMENT_STATUS_FAILED,
            transition_key=k(3),
            failure_refs=("fail-1",),
        )
    assert S3_EXPERIMENT_DELETION_FORBIDDEN in str(exc_comp.value)

    # Transition COMPLETED -> SUPERSEDED is allowed; further transitions from SUPERSEDED are forbidden
    reg.record_transition(
        experiment_id="exp-idem",
        new_status=EXPERIMENT_STATUS_SUPERSEDED,
        transition_key=k(3),
    )
    with pytest.raises(SchemaViolation) as exc_term:
        reg.record_transition(
            experiment_id="exp-idem",
            new_status=EXPERIMENT_STATUS_SUPERSEDED,
            transition_key=k(4),
        )
    assert S3_EXPERIMENT_DELETION_FORBIDDEN in str(exc_term.value)


# 19 — PolicyArtifact provenance contract: DEVELOPMENT_FIT_CALIBRATION requires fit_dataset_id, objective_hash, experiment_id
def test_muf_s3_19_policy_artifact_provenance_contracts():
    # DEVELOPMENT_FIT_CALIBRATION missing fit_dataset_id / objective_artifact_hash / experiment_id fails closed
    with pytest.raises(SchemaViolation) as exc_fit:
        PolicyArtifact.create(
            policy_id="pol-fit-missing",
            detector_policy_witness_ref="wit-ref-1",
            scope_timeline_id=TIMELINE,
            scope_axis=InformationAxis.POSITIONAL,
            scope_representation_id="ALPHA_V1",
            calibration_provenance_kind=PROVENANCE_DEVELOPMENT_FIT,
            reproduction_recipe_hash="recipe-1",
            effective_from_key=k(1),
            owner_authorization_ref="owner-auth-1",
        )
    assert S3_INVALID_POLICY_ARTIFACT in str(exc_fit.value)

    # Complete DEVELOPMENT_FIT_CALIBRATION PolicyArtifact succeeds
    p_fit = PolicyArtifact.create(
        policy_id="pol-fit-ok",
        detector_policy_witness_ref="wit-ref-1",
        scope_timeline_id=TIMELINE,
        scope_axis=InformationAxis.POSITIONAL,
        scope_representation_id="ALPHA_V1",
        calibration_provenance_kind=PROVENANCE_DEVELOPMENT_FIT,
        fit_dataset_id="DS-DEV-FIT",
        objective_artifact_hash="obj-hash-1",
        experiment_id="exp-fit-01",
        reproduction_recipe_hash="recipe-1",
        effective_from_key=k(1),
        owner_authorization_ref="owner-auth-1",
    )
    assert p_fit.calibration_provenance_kind == PROVENANCE_DEVELOPMENT_FIT
    assert p_fit.fit_dataset_id == "DS-DEV-FIT"

    # PREDEFINED_STRUCTURAL_CONTRACT with fit_dataset_id populated fails closed
    with pytest.raises(SchemaViolation):
        PolicyArtifact.create(
            policy_id="pol-predef-bad",
            detector_policy_witness_ref="wit-ref-1",
            scope_timeline_id=TIMELINE,
            scope_axis=InformationAxis.POSITIONAL,
            scope_representation_id="ALPHA_V1",
            calibration_provenance_kind=PROVENANCE_PREDEFINED_CONTRACT,
            fit_dataset_id="DS-DEV-FIT",
            reproduction_recipe_hash="recipe-1",
            effective_from_key=k(1),
            owner_authorization_ref="owner-auth-1",
        )


# 20 — Gate G0 blocks when experiment's registered objective or fit dataset mismatches
def test_muf_s3_20_gate_g0_experiment_binding_mismatches():
    obj1 = sample_objective(obj_id="obj-1")
    obj2 = sample_objective(obj_id="obj-2")
    ds_fit = sample_ds_identity("DS-DEV-FIT", content_hash="1" * 64, start_pos=1, end_pos=100)
    r_fit = sample_ds_role(ds_fit, role=DATASET_ROLE_DEVELOPMENT_FIT)

    reg = ExperimentRegistry()
    reg.preregister(
        experiment_id="exp-1",
        preregistration_key=k(1),
        representation_spec_hash="rep-alpha-v1",
        policy_artifact_hashes=("pol-1",),
        objective_artifact_hash=obj1.objective_hash,
        dataset_identities_by_role={DATASET_ROLE_DEVELOPMENT_FIT: "DS-DEV-FIT"},
        code_hash="code-1",
        fit_protocol_hash="fit-1",
    )

    # Experiment registered with obj1, but G0 called with obj2 -> blocked!
    with pytest.raises(SelectionBlockedError) as exc_obj_mis:
        evaluate_g0_calibration_gate(
            objective_artifact=obj2,
            fit_dataset_identity=ds_fit,
            fit_dataset_role=r_fit,
            experiment_registry=reg,
            experiment_id="exp-1",
            owner_fit_authorization_ref="owner-auth-1",
        )
    assert G0_BLOCKED_UNREGISTERED_EXPERIMENT in str(exc_obj_mis.value)

    # Experiment in FAILED state -> G0 blocks calibration!
    reg.record_transition(
        experiment_id="exp-1",
        new_status=EXPERIMENT_STATUS_FAILED,
        transition_key=k(2),
        failure_refs=("fail-1",),
    )
    with pytest.raises(SelectionBlockedError) as exc_failed:
        evaluate_g0_calibration_gate(
            objective_artifact=obj1,
            fit_dataset_identity=ds_fit,
            fit_dataset_role=r_fit,
            experiment_registry=reg,
            experiment_id="exp-1",
            owner_fit_authorization_ref="owner-auth-1",
        )
    assert G0_BLOCKED_UNREGISTERED_EXPERIMENT in str(exc_failed.value)


# 21 — HumanReviewRecord on DEVELOPMENT role: DESIGN_INFLUENCING keeps exposure_state EXPOSED_DEVELOPMENT
def test_muf_s3_21_human_review_on_development_dataset():
    ds_dev = sample_ds_identity("DS-DEV", start_pos=1, end_pos=100)
    r_dev = sample_ds_role(ds_dev, role=DATASET_ROLE_DEVELOPMENT_FIT)

    rev, r_dev_after = HumanReviewRecord.create_and_apply(
        review_id="rev-dev-01",
        role_artifact=r_dev,
        review_kind=REVIEW_KIND_DEVELOPMENT_AUDIT,
        review_key=k(105),
        reviewer="owner",
        charts_viewed=("chart-dev-1",),
        observations=("Normal development diagnostic review",),
        requested_changes=("Adjust candidate diagnostic reporting",),
        change_influence=INFLUENCE_DESIGN_INFLUENCING,
    )
    assert rev.change_influence == INFLUENCE_DESIGN_INFLUENCING
    assert r_dev_after.exposure_state == EXPOSURE_STATE_EXPOSED_DEVELOPMENT
    assert r_dev_after.reservation_status == RESERVATION_STATUS_NOT_APPLICABLE

    # Tampered review_hash rejected
    with pytest.raises(SchemaViolation):
        replace(rev, reviewer="forged-reviewer")


# 22 — AuthoritativeTurningPointRecord constructor tamper resistance (origin/availability/metric/published_record)
def test_muf_s3_22_authoritative_turning_point_tamper_resistance():
    bars = sample_bars()
    pol = EmpiricalConfirmationPolicy(
        quantile=0.5, prior_continuation_reversals=(0.01, 0.02)
    )
    bundle = adapt_detector_witness_stream(bars, confirmation_policy=pol)
    ev = bundle.swing_event_witnesses[0]
    p_art = PolicyArtifact.create(
        policy_id="muf-pol-1",
        detector_policy_witness_ref=str(bundle.policy_witness_ref),
        scope_timeline_id=TIMELINE,
        scope_axis=InformationAxis.POSITIONAL,
        scope_representation_id="ALPHA_V1",
        calibration_provenance_kind=PROVENANCE_PREDEFINED_CONTRACT,
        reproduction_recipe_hash="recipe-1",
        effective_from_key=k(1),
        owner_authorization_ref="owner-pol-auth-1",
    )
    tp = promote_swing_witness_with_policy_artifact(ev, policy_artifact=p_art)

    # Tampering swing_price fails closed
    with pytest.raises(SchemaViolation):
        replace(tp, swing_price=exact_metric(999.0))

    # Tampering authority_policy_hash fails closed
    with pytest.raises(SchemaViolation):
        replace(tp, authority_policy_hash="forged-hash")

    # Tampering availability_key to equal origin_key (confirmation_position == origin_position) fails closed
    with pytest.raises((PrematureAvailability, SchemaViolation)):
        replace(
            tp,
            confirmation_position=tp.origin_position,
            availability_key=tp.origin_key,
        )


# 23 — AuthoritativeTurningPointReference round-trip and WaveProcessIdentityBasis integration
def test_muf_s3_23_turning_point_reference_and_wave_process_basis():
    bars = sample_bars()
    pol = EmpiricalConfirmationPolicy(
        quantile=0.5, prior_continuation_reversals=(0.01, 0.02)
    )
    bundle = adapt_detector_witness_stream(bars, confirmation_policy=pol)
    ev = bundle.swing_event_witnesses[0]
    p_art = PolicyArtifact.create(
        policy_id="muf-pol-1",
        detector_policy_witness_ref=str(bundle.policy_witness_ref),
        scope_timeline_id=TIMELINE,
        scope_axis=InformationAxis.POSITIONAL,
        scope_representation_id="ALPHA_V1",
        calibration_provenance_kind=PROVENANCE_PREDEFINED_CONTRACT,
        reproduction_recipe_hash="recipe-1",
        effective_from_key=k(1),
        owner_authorization_ref="owner-pol-auth-1",
    )
    tp = promote_swing_witness_with_policy_artifact(ev, policy_artifact=p_art)
    tp_ref = tp.to_turning_point_reference()

    assert tp_ref.turning_point_identity == tp.turning_point_id
    assert tp_ref.record_type == TURNING_POINT_RECORD_TYPE
    assert tp_ref.timeline_id == tp.timeline_id
    assert tp_ref.availability_key == tp.availability_key


# 24 — query_promoted_turning_points_as_of: BAR_PRE_CLOSE, timeline mismatch, and axis mismatch rejected
def test_muf_s3_24_query_promoted_turning_points_causal_guards():
    bars = sample_bars()
    pol = EmpiricalConfirmationPolicy(
        quantile=0.5, prior_continuation_reversals=(0.01, 0.02)
    )
    bundle = adapt_detector_witness_stream(bars, confirmation_policy=pol)
    ev = bundle.swing_event_witnesses[0]
    p_art = PolicyArtifact.create(
        policy_id="muf-pol-1",
        detector_policy_witness_ref=str(bundle.policy_witness_ref),
        scope_timeline_id=TIMELINE,
        scope_axis=InformationAxis.POSITIONAL,
        scope_representation_id="ALPHA_V1",
        calibration_provenance_kind=PROVENANCE_PREDEFINED_CONTRACT,
        reproduction_recipe_hash="recipe-1",
        effective_from_key=k(1),
        owner_authorization_ref="owner-pol-auth-1",
    )
    tp = promote_swing_witness_with_policy_artifact(ev, policy_artifact=p_art)

    # BAR_PRE_CLOSE query rejected
    with pytest.raises(IllegalCausalReference):
        query_promoted_turning_points_as_of(
            (tp,),
            timeline_id=TIMELINE,
            axis=InformationAxis.POSITIONAL,
            at_key=k(3, phase=InformationPhase.BAR_PRE_CLOSE),
        )

    # Timeline mismatch rejected
    with pytest.raises(InformationKeyViolation):
        query_promoted_turning_points_as_of(
            (tp,),
            timeline_id="OTHER_TL",
            axis=InformationAxis.POSITIONAL,
            at_key=k(3, timeline="OTHER_TL"),
        )

    # Axis mismatch rejected
    with pytest.raises(IncomparableInformationKeys):
        query_promoted_turning_points_as_of(
            (tp,),
            timeline_id=TIMELINE,
            axis=InformationAxis.TIME_INDEXED,
            at_key=k(3),
        )


# 25 — Dataset ancestry multi-hop transitive contamination (grandparent exposed final -> grandchild blocked)
def test_muf_s3_25_transitive_multi_hop_ancestry_contamination():
    ds_gp = sample_ds_identity("DS-GP-FINAL", content_hash="1" * 64, start_pos=201, end_pos=300)
    r_gp = sample_ds_role(ds_gp, role=DATASET_ROLE_FINAL_EVALUATION_LOCKED)
    r_gp_exp = record_dataset_exposure(
        r_gp,
        event_id="exp-gp",
        exposure_key=k(301),
        exposure_kind="FINAL_OPEN",
        actor_or_protocol_ref="proto-1",
        authorized_final_open=True,
    )

    ds_parent = sample_ds_identity(
        "DS-PARENT",
        content_hash="2" * 64,
        start_pos=201,
        end_pos=300,
        parents=("DS-GP-FINAL",),
    )
    ds_child = sample_ds_identity(
        "DS-CHILD",
        content_hash="3" * 64,
        start_pos=201,
        end_pos=300,
        parents=("DS-PARENT",),
    )

    # 2-hop descendant of exposed final dataset is blocked from unexposed final eligibility
    with pytest.raises(SchemaViolation) as exc_hop:
        verify_dataset_independence_and_ancestry(
            ds_child,
            known_identities=(ds_gp, ds_parent),
            known_roles={"DS-GP-FINAL": r_gp_exp},
            require_unexposed_final_eligibility=True,
        )
    assert S3_EXPOSED_ANCESTRY_CONTAMINATION in str(exc_hop.value)


# 26 — Gate G0 blocks DEVELOPMENT_FIT dataset that transitively derives from FINAL_EVALUATION_LOCKED dataset
def test_muf_s3_26_gate_g0_blocks_transitive_final_ancestry():
    obj = sample_objective()
    ds_final = sample_ds_identity("DS-FINAL", content_hash="9" * 64, start_pos=201, end_pos=300)
    r_final = sample_ds_role(ds_final, role=DATASET_ROLE_FINAL_EVALUATION_LOCKED)

    ds_mid = sample_ds_identity(
        "DS-MID",
        content_hash="8" * 64,
        start_pos=1,
        end_pos=100,
        parents=("DS-FINAL",),
    )
    ds_fit = sample_ds_identity(
        "DS-DEV-FIT",
        content_hash="7" * 64,
        start_pos=1,
        end_pos=100,
        parents=("DS-MID",),
    )
    r_fit = sample_ds_role(ds_fit, role=DATASET_ROLE_DEVELOPMENT_FIT)

    reg = ExperimentRegistry()
    reg.preregister(
        experiment_id="exp-1",
        preregistration_key=k(1),
        representation_spec_hash="rep-alpha-v1",
        policy_artifact_hashes=("pol-1",),
        objective_artifact_hash=obj.objective_hash,
        dataset_identities_by_role={DATASET_ROLE_DEVELOPMENT_FIT: "DS-DEV-FIT"},
        code_hash="code-1",
        fit_protocol_hash="fit-1",
    )

    with pytest.raises(SelectionBlockedError) as exc_g0:
        evaluate_g0_calibration_gate(
            objective_artifact=obj,
            fit_dataset_identity=ds_fit,
            fit_dataset_role=r_fit,
            known_dataset_identities=(ds_final, ds_mid),
            known_dataset_roles={"DS-FINAL": r_final},
            experiment_registry=reg,
            experiment_id="exp-1",
            owner_fit_authorization_ref="owner-auth-1",
        )
    assert G0_BLOCKED_FINAL_DATA_LEAKAGE in str(exc_g0.value)


# 27 — FoldProtocolArtifact multi-fold non-decreasing order enforcement
def test_muf_s3_27_fold_protocol_multi_fold_ordering():
    ds_fit0 = sample_ds_identity("F0", content_hash="1" * 64, start_pos=1, end_pos=50)
    ds_sel0 = sample_ds_identity("S0", content_hash="2" * 64, start_pos=51, end_pos=100)
    ds_fit1 = sample_ds_identity("F1", content_hash="3" * 64, start_pos=1, end_pos=100)
    ds_sel1 = sample_ds_identity("S1", content_hash="4" * 64, start_pos=101, end_pos=150)

    id_map = {d.dataset_id: d for d in (ds_fit0, ds_sel0, ds_fit1, ds_sel1)}
    role_map = {
        "F0": sample_ds_role(ds_fit0, role=DATASET_ROLE_DEVELOPMENT_FIT),
        "S0": sample_ds_role(ds_sel0, role=DATASET_ROLE_DEVELOPMENT_SELECTION),
        "F1": sample_ds_role(ds_fit1, role=DATASET_ROLE_DEVELOPMENT_FIT),
        "S1": sample_ds_role(ds_sel1, role=DATASET_ROLE_DEVELOPMENT_SELECTION),
    }

    # Fold 0 selection window (101..150) after Fold 1 selection window (51..100) rejected
    with pytest.raises(PrematureAvailability):
        FoldProtocolArtifact.create(
            protocol_id="wf-backwards-folds",
            timeline_id=TIMELINE,
            folds=(
                FoldPairSpec(0, "F1", "S1"),
                FoldPairSpec(1, "F0", "S0"),
            ),
            dataset_identities=id_map,
            dataset_roles=role_map,
            owner_authorization_ref="owner-wf",
        )


# 28 — RepresentationExperimentRecord requires failure_refs on FAILED and result_refs on COMPLETED
def test_muf_s3_28_experiment_transition_required_refs():
    reg = ExperimentRegistry()
    obj = sample_objective()
    reg.preregister(
        experiment_id="exp-refs",
        preregistration_key=k(1),
        representation_spec_hash="rep-alpha-v1",
        policy_artifact_hashes=("pol-1",),
        objective_artifact_hash=obj.objective_hash,
        dataset_identities_by_role={DATASET_ROLE_DEVELOPMENT_FIT: "DS-DEV-FIT"},
        code_hash="code-1",
        fit_protocol_hash="fit-1",
    )

    # FAILED without failure_refs rejected
    with pytest.raises(SchemaViolation):
        reg.record_transition(
            experiment_id="exp-refs",
            new_status=EXPERIMENT_STATUS_FAILED,
            transition_key=k(2),
            failure_refs=(),
        )

    # COMPLETED without result_refs rejected
    with pytest.raises(SchemaViolation):
        reg.record_transition(
            experiment_id="exp-refs",
            new_status=EXPERIMENT_STATUS_COMPLETED,
            transition_key=k(2),
            result_refs=(),
        )


# 29 — G0CalibrationGateCertificate direct constructor validation
def test_muf_s3_29_g0_certificate_constructor_validation():
    with pytest.raises(SelectionBlockedError):
        G0CalibrationGateCertificate(
            objective_artifact_hash="obj-1",
            fit_dataset_id="DS-1",
            fit_dataset_identity_hash="id-1",
            fit_dataset_role_hash="role-1",
            experiment_id="exp-1",
            experiment_hash="eh-1",
            owner_fit_authorization_ref="auth-1",
            gate_passed=False,
        )


# 30 — End-to-end deterministic replay of all S3 governance artifacts
def test_muf_s3_30_end_to_end_deterministic_replay():
    obj_a = sample_objective()
    obj_b = sample_objective()
    assert obj_a == obj_b
    assert obj_a.objective_hash == obj_b.objective_hash

    ds_a = sample_ds_identity()
    ds_b = sample_ds_identity()
    assert ds_a == ds_b
    assert ds_a.dataset_identity_hash == ds_b.dataset_identity_hash

    r_a = sample_ds_role(ds_a)
    r_b = sample_ds_role(ds_b)
    assert r_a == r_b
    assert r_a.role_artifact_hash == r_b.role_artifact_hash


