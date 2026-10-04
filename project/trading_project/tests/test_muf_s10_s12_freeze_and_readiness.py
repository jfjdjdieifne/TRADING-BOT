"""MUF V1 S10, S11, S12 & Gate G3 Adversarial Test Suite: Freeze, Protocol, Readiness, Comparability & Equivalence.

Fixture discipline: SYNTHETIC SMALL FIXTURES ONLY (no owner data).
Verifies D1-18, D1-19, D2-5, D2-6, D2-13, D2-14, D2-15, D2-19, D2-22, Correction-1 §3, §4, Δ3, Δ5, AP-1 §4.2, §4.3:
- FrozenRepresentationBundle (S10, D2-15, I-FREEZE-1..4)
- EvaluationProtocolArtifact & EvaluationProtocolEventLedger (S11, D2-5, D2-6, Correction-1 §3, I-EVP-1..3, I-EVAL-1..6, I-RES-1..2, I-SG-1B)
- PreFinalReadinessRecord & evaluate_gate_g3_open_final_authorization (S12 & Gate G3, D2-19, I-PFR-1..3)
- EquivalenceClaimArtifact (D2-13, I-EQ-1..4)
- ComparabilitySnapshotSpec, evaluate_snapshot_comparability, compute_comparable_snapshot_distance (D1-18, D1-19, D2-14, I-CMP-1..2, I-CMPL-1..3, I-MSN-1)
"""
from dataclasses import replace
import hashlib
from pathlib import Path
import time

import pytest

from trading_system.market_understanding.contracts import (
    IllegalCausalReference,
    ImmutabilityViolation,
    SchemaIdentity,
    SchemaViolation,
    TypedState,
    scan_market_shape_implementations,
    scan_private_imports,
    scan_prohibited_implementations,
)
from trading_system.market_understanding.freeze_and_readiness import (
    COMPARABILITY_IDENTICAL_CONTRACT,
    COMPARABILITY_NOT_COMPARABLE,
    EQ_DIM_CAUSAL_VISIBILITY,
    EQ_DIM_PROVENANCE,
    EQ_DIM_SEMANTIC_OUTPUT,
    EQUIVALENCE_RESULT_CERTIFIED,
    EQUIVALENCE_RESULT_REJECTED,
    G3_OPEN_FINAL_BLOCKED,
    GATE_G3_AUTHORIZED_TO_OPEN,
    PROTOCOL_EVENT_OPENED,
    PROTOCOL_EVENT_OUTPUT_EMITTED,
    PROTOCOL_EVENT_RESERVED,
    READINESS_RESULT_FAILED,
    READINESS_RESULT_READY,
    S10_INVALID_EQUIVALENCE_CLAIM,
    S10_INVALID_FROZEN_BUNDLE,
    S10_NOT_COMPARABLE_DISTANCE_FORBIDDEN,
    S11_BUNDLE_DEPENDENCY_CLOSURE_MISSING,
    S11_INVALID_EVALUATION_PROTOCOL,
    S11_PROTOCOL_ALREADY_OPENED_FOR_LINEAGE,
    S12_PROTECTED_FINAL_DATA_USED_IN_READINESS,
    ComparabilitySnapshotSpec,
    EquivalenceClaimArtifact,
    EvaluationProtocolArtifact,
    EvaluationProtocolEventLedger,
    FrozenRepresentationBundle,
    PreFinalReadinessRecord,
    compute_comparable_snapshot_distance,
    evaluate_gate_g3_open_final_authorization,
    evaluate_snapshot_comparability,
    verify_final_protocol_bundle_closure,
)
from trading_system.market_understanding.policy_governance import (
    SelectionBlockedError,
)
from trading_system.research.information_time import (
    INFORMATION_KEY_VERSION,
    InformationKey,
    InformationPhase,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
S10_S12_MODULE_PATH = (
    PROJECT_ROOT
    / "src"
    / "trading_system"
    / "market_understanding"
    / "freeze_and_readiness.py"
)

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


def _setup_s10_s12_environment():
    bundle = FrozenRepresentationBundle.create(
        bundle_name="bundle_alpha_v1",
        artifact_lineage_id="lineage_alpha_01",
        representation_spec_hash="rep_hash_01",
        policy_artifact_hashes=("pol_hash_01",),
        objective_artifact_hash_or_state="obj_hash_01",
        state_catalog_hash="cat_hash_01",
        graph_spec_hash="gspec_hash_01",
        feature_view_hashes=("fv_hash_01",),
        descriptor_contract_hashes=("desc_hash_01",),
        dependence_contract_hashes=("dep_hash_01",),
        estimand_hashes=("est_hash_01",),
        fit_protocol_hash_or_state="fit_proto_01",
        selection_protocol_hash_or_state="sel_proto_01",
        dataset_role_artifact_hashes=("ds_role_01",),
        fold_protocol_hash_or_state=TypedState.NOT_CONFIGURED,
        code_artifact_hashes=("code_hash_01",),
        experiment_registry_root="exp_root_01",
        schema_contract_hashes=("schema_hash_01",),
        freeze_information_key=k(10),
        owner_freeze_authorization_ref="owner_freeze_auth_01",
    )
    proto = EvaluationProtocolArtifact.create(
        evaluation_protocol_id="final_proto_01",
        frozen_bundle=bundle,
        objective_artifact_hash="obj_hash_01",
        estimand_hashes=("est_hash_01",),
        state_catalog_hash="cat_hash_01",
        graph_spec_hash="gspec_hash_01",
        feature_view_hashes=("fv_hash_01",),
        dataset_identity="DS_FINAL_LOCKED_01",
        dataset_ancestry_root="DS_ANCESTRY_ROOT_01",
        allowed_outputs=("PRIMARY_ESTIMAND_SUMMARY",),
        prohibited_outputs=("POST_HOC_SUBGROUP_MINING",),
        opening_authorization_ref_or_state=TypedState.NOT_CONFIGURED,
        reservation_time_key=k(11),
    )
    ledger = EvaluationProtocolEventLedger()
    ledger.register_reserved_protocol(proto)
    readiness = PreFinalReadinessRecord.create(
        readiness_id="readiness_01",
        frozen_bundle=bundle,
        protocol=proto,
        readiness_key=k(12),
    )
    return bundle, proto, ledger, readiness


def test_s10_s12_module_passes_s0_ast_scanners() -> None:
    source = S10_S12_MODULE_PATH.read_text(encoding="utf-8")
    assert scan_private_imports(source) == ()
    assert scan_prohibited_implementations(source) == ()
    assert scan_market_shape_implementations(source) == ()


def test_sealed_s0_to_s9_hashes_untouched() -> None:
    for rel_cert in (
        "docs/releases/MODULE_MUF_V1_S0_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S1_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S2_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S3_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S4_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S5_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S6_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S7_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S8_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S9_ACCEPTED_SRC_TESTS.sha256",
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


def test_frozen_representation_bundle_identity_sensitivity_attack_43() -> None:
    bundle, _, _, _ = _setup_s10_s12_environment()
    bundle_changed_policy = FrozenRepresentationBundle.create(
        bundle_name="bundle_alpha_v1",
        artifact_lineage_id="lineage_alpha_01",
        representation_spec_hash="rep_hash_01",
        policy_artifact_hashes=("pol_hash_CHANGED",),
        objective_artifact_hash_or_state="obj_hash_01",
        state_catalog_hash="cat_hash_01",
        graph_spec_hash="gspec_hash_01",
        feature_view_hashes=("fv_hash_01",),
        descriptor_contract_hashes=("desc_hash_01",),
        dependence_contract_hashes=("dep_hash_01",),
        estimand_hashes=("est_hash_01",),
        fit_protocol_hash_or_state="fit_proto_01",
        selection_protocol_hash_or_state="sel_proto_01",
        dataset_role_artifact_hashes=("ds_role_01",),
        fold_protocol_hash_or_state=TypedState.NOT_CONFIGURED,
        code_artifact_hashes=("code_hash_01",),
        experiment_registry_root="exp_root_01",
        schema_contract_hashes=("schema_hash_01",),
        freeze_information_key=k(10),
        owner_freeze_authorization_ref="owner_freeze_auth_01",
    )
    assert bundle.bundle_id != bundle_changed_policy.bundle_id

    with pytest.raises(SchemaViolation, match="bundle_id mismatch"):
        replace(bundle, policy_artifact_hashes=("pol_hash_CHANGED",))


def test_evaluation_protocol_dependency_closure_i_sg_1b_correction1_attack_5() -> None:
    bundle, proto, _, _ = _setup_s10_s12_environment()
    assert verify_final_protocol_bundle_closure(proto, frozen_bundle=bundle)

    # Referencing feature_view_hash absent from FrozenRepresentationBundle fails closed (I-SG-1B)
    with pytest.raises(
        SelectionBlockedError, match=S11_BUNDLE_DEPENDENCY_CLOSURE_MISSING
    ):
        EvaluationProtocolArtifact.create(
            evaluation_protocol_id="final_proto_bad_fv",
            frozen_bundle=bundle,
            objective_artifact_hash="obj_hash_01",
            estimand_hashes=("est_hash_01",),
            state_catalog_hash="cat_hash_01",
            graph_spec_hash="gspec_hash_01",
            feature_view_hashes=("fv_hash_NOT_IN_BUNDLE",),
            dataset_identity="DS_FINAL_LOCKED_01",
            dataset_ancestry_root="DS_ANCESTRY_ROOT_01",
            allowed_outputs=("PRIMARY_ESTIMAND_SUMMARY",),
            reservation_time_key=k(11),
        )


def test_protocol_hash_byte_identical_before_and_after_open_correction1_attack_4() -> None:
    bundle, proto, ledger, readiness = _setup_s10_s12_environment()
    hash_before_open = proto.protocol_hash

    # Reservation is NOT exposure (I-RES-1)
    assert not ledger.is_exposed(proto.evaluation_protocol_id)

    # Authorize Gate G3 and open
    g3_dec = evaluate_gate_g3_open_final_authorization(
        decision_id="g3_dec_01",
        frozen_bundle=bundle,
        protocol=proto,
        readiness_record=readiness,
        owner_opening_authorization_ref="owner_open_auth_01",
        event_ledger=ledger,
        decision_key=k(13),
    )
    assert g3_dec.gate_g3_status == GATE_G3_AUTHORIZED_TO_OPEN

    ledger.append_event(
        protocol_id=proto.evaluation_protocol_id,
        event_type=PROTOCOL_EVENT_OPENED,
        event_information_key=k(14),
        payload_ref="open_execution_01",
    )
    assert ledger.is_exposed(proto.evaluation_protocol_id)
    assert ledger.protocol(proto.evaluation_protocol_id).protocol_hash == hash_before_open


def test_protocol_cannot_open_twice_for_same_lineage_i_eval_1() -> None:
    _, proto, ledger, _ = _setup_s10_s12_environment()
    ledger.append_event(
        protocol_id=proto.evaluation_protocol_id,
        event_type=PROTOCOL_EVENT_OPENED,
        event_information_key=k(14),
        payload_ref="open_1",
    )
    with pytest.raises(
        SelectionBlockedError, match=S11_PROTOCOL_ALREADY_OPENED_FOR_LINEAGE
    ):
        ledger.append_event(
            protocol_id=proto.evaluation_protocol_id,
            event_type=PROTOCOL_EVENT_OPENED,
            event_information_key=k(15),
            payload_ref="open_2",
        )


def test_pre_final_readiness_rejects_protected_final_outcomes_i_pfr_2_3() -> None:
    bundle, proto, _, _ = _setup_s10_s12_environment()
    with pytest.raises(
        SelectionBlockedError,
        match=S12_PROTECTED_FINAL_DATA_USED_IN_READINESS,
    ):
        PreFinalReadinessRecord.create(
            readiness_id="readiness_illegal_final",
            frozen_bundle=bundle,
            protocol=proto,
            protected_final_outcomes_accessed=True,
            readiness_key=k(12),
        )


def test_gate_g3_blocks_when_readiness_failed_or_owner_auth_missing_attack_44() -> None:
    bundle, proto, ledger, readiness = _setup_s10_s12_environment()
    failed_readiness = PreFinalReadinessRecord.create(
        readiness_id="readiness_failed_01",
        frozen_bundle=bundle,
        protocol=proto,
        synthetic_dry_run_valid=False,
        readiness_key=k(12),
    )
    assert failed_readiness.readiness_result == READINESS_RESULT_FAILED

    with pytest.raises(SelectionBlockedError, match=G3_OPEN_FINAL_BLOCKED):
        evaluate_gate_g3_open_final_authorization(
            decision_id="g3_blocked_readiness",
            frozen_bundle=bundle,
            protocol=proto,
            readiness_record=failed_readiness,
            owner_opening_authorization_ref="owner_open_auth_01",
            event_ledger=ledger,
            decision_key=k(13),
        )

    with pytest.raises(SelectionBlockedError, match=G3_OPEN_FINAL_BLOCKED):
        evaluate_gate_g3_open_final_authorization(
            decision_id="g3_blocked_no_owner_auth",
            frozen_bundle=bundle,
            protocol=proto,
            readiness_record=readiness,
            owner_opening_authorization_ref=TypedState.NOT_CONFIGURED,
            event_ledger=ledger,
            decision_key=k(13),
        )


def test_equivalence_claim_rejects_numeric_only_or_unproven_dimensions_attack_41() -> None:
    # Numeric/semantic output equality alone is rejected (Attack 41, I-EQ-1)
    with pytest.raises(SchemaViolation, match=S10_INVALID_EQUIVALENCE_CLAIM):
        EquivalenceClaimArtifact.create(
            claim_id="eq_numeric_only",
            old_bundle_id="bundle_1",
            new_bundle_id="bundle_2",
            evaluation_claim_scope="CLAIM_01",
            required_equivalence_dimensions=(EQ_DIM_SEMANTIC_OUTPUT,),
            proven_equivalence_dimensions=(EQ_DIM_SEMANTIC_OUTPUT,),
            proof_refs=("proof_1",),
        )

    # Missing required dimension -> EQUIVALENCE_RESULT_REJECTED (I-EQ-3)
    eq_rej = EquivalenceClaimArtifact.create(
        claim_id="eq_missing_prov",
        old_bundle_id="bundle_1",
        new_bundle_id="bundle_2",
        evaluation_claim_scope="CLAIM_01",
        required_equivalence_dimensions=(
            EQ_DIM_SEMANTIC_OUTPUT,
            EQ_DIM_PROVENANCE,
        ),
        proven_equivalence_dimensions=(EQ_DIM_SEMANTIC_OUTPUT,),
        proof_refs=("proof_1",),
    )
    assert eq_rej.equivalence_result == EQUIVALENCE_RESULT_REJECTED

    # All required dimensions proven -> EQUIVALENCE_RESULT_CERTIFIED
    eq_ok = EquivalenceClaimArtifact.create(
        claim_id="eq_certified",
        old_bundle_id="bundle_1",
        new_bundle_id="bundle_2",
        evaluation_claim_scope="CLAIM_01",
        required_equivalence_dimensions=(
            EQ_DIM_SEMANTIC_OUTPUT,
            EQ_DIM_CAUSAL_VISIBILITY,
            EQ_DIM_PROVENANCE,
        ),
        proven_equivalence_dimensions=(
            EQ_DIM_SEMANTIC_OUTPUT,
            EQ_DIM_CAUSAL_VISIBILITY,
            EQ_DIM_PROVENANCE,
        ),
        proof_refs=("proof_1", "proof_2"),
    )
    assert eq_ok.equivalence_result == EQUIVALENCE_RESULT_CERTIFIED


def test_snapshot_comparability_and_missingness_mask_attacks_16_23_42() -> None:
    snap_base = ComparabilitySnapshotSpec(
        snapshot_id="s1",
        representation_spec_hash="rep_1",
        policy_hash_lineage="pol_1",
        descriptor_set_hash="desc_1",
        information_key_version="V1",
        history_boundary_kind="ORIGIN_ANCHORED",
        source_semantic_identities=("BINANCE_SPOT_OHLC_V1",),
        actual_proxy_availability_mask=("ACTUAL:PRESENT",),
        schema_version="V1",
    )
    snap_same = ComparabilitySnapshotSpec(
        snapshot_id="s2",
        representation_spec_hash="rep_1",
        policy_hash_lineage="pol_1",
        descriptor_set_hash="desc_1",
        information_key_version="V1",
        history_boundary_kind="ORIGIN_ANCHORED",
        source_semantic_identities=("BINANCE_SPOT_OHLC_V1",),
        actual_proxy_availability_mask=("ACTUAL:PRESENT",),
        schema_version="V1",
    )
    res_ok = evaluate_snapshot_comparability(snap_base, snap_same)
    assert res_ok.comparability_level == COMPARABILITY_IDENTICAL_CONTRACT
    dist = compute_comparable_snapshot_distance(
        snap_base, snap_same, left_values=(1.0, 2.0), right_values=(1.5, 1.0)
    )
    assert dist == pytest.approx(1.5)

    # Attack 16: ACTUAL missing replaced by PROXY -> AVAILABILITY_MASK_DIFFERS -> NOT_COMPARABLE
    snap_proxy = replace(
        snap_same, actual_proxy_availability_mask=("PROXY:PRESENT",)
    )
    res_proxy = evaluate_snapshot_comparability(snap_base, snap_proxy)
    assert res_proxy.comparability_level == COMPARABILITY_NOT_COMPARABLE
    assert "AVAILABILITY_MASK_DIFFERS" in res_proxy.reasons

    # Attack 23/42: Distance computation when NOT_COMPARABLE raises SelectionBlockedError (I-CMP-1)
    with pytest.raises(
        SelectionBlockedError, match=S10_NOT_COMPARABLE_DISTANCE_FORBIDDEN
    ):
        compute_comparable_snapshot_distance(
            snap_base,
            snap_proxy,
            left_values=(1.0, 2.0),
            right_values=(1.0, 2.0),
        )


def test_evaluation_protocol_rejects_overlapping_allowed_and_prohibited_outputs() -> None:
    bundle, proto, _, _ = _setup_s10_s12_environment()
    with pytest.raises(SchemaViolation, match="cannot overlap"):
        EvaluationProtocolArtifact.create(
            evaluation_protocol_id="proto_overlap",
            frozen_bundle=bundle,
            objective_artifact_hash="obj_hash_01",
            estimand_hashes=("est_hash_01",),
            state_catalog_hash="cat_hash_01",
            graph_spec_hash="gspec_hash_01",
            feature_view_hashes=("fv_hash_01",),
            dataset_identity="DS_FINAL_LOCKED_01",
            dataset_ancestry_root="DS_ANCESTRY_ROOT_01",
            allowed_outputs=("SUMMARY_A",),
            prohibited_outputs=("SUMMARY_A",),
            reservation_time_key=k(11),
        )

    with pytest.raises(SchemaViolation, match="protocol_hash mismatch"):
        replace(proto, protocol_hash="sha256:tampered")


def test_event_ledger_hash_chain_and_duplicate_protocol_registration() -> None:
    _, proto, ledger, _ = _setup_s10_s12_environment()
    with pytest.raises(ImmutabilityViolation, match="already registered"):
        ledger.register_reserved_protocol(proto)

    ev2 = ledger.append_event(
        protocol_id=proto.evaluation_protocol_id,
        event_type=PROTOCOL_EVENT_OUTPUT_EMITTED,
        event_information_key=k(15),
        payload_ref="output_1",
    )
    evs = ledger.events(proto.evaluation_protocol_id)
    assert len(evs) == 2
    assert evs[0].event_type == PROTOCOL_EVENT_RESERVED
    assert evs[0].previous_event_hash == "GENESIS"
    assert ev2.previous_event_hash == evs[0].event_hash


def test_event_ledger_rejects_unknown_protocol_or_tampered_event() -> None:
    _, proto, ledger, _ = _setup_s10_s12_environment()
    with pytest.raises(SchemaViolation, match="unknown protocol_id"):
        ledger.events("unknown_proto")

    ev0 = ledger.events(proto.evaluation_protocol_id)[0]
    with pytest.raises(SchemaViolation, match="event_hash mismatch"):
        replace(ev0, event_hash="sha256:tampered")


def test_readiness_record_post_init_guards() -> None:
    _, _, _, readiness = _setup_s10_s12_environment()
    with pytest.raises(SchemaViolation, match="readiness_hash mismatch"):
        replace(readiness, readiness_hash="sha256:tampered")
    with pytest.raises(
        SchemaViolation,
        match="readiness_result cannot be READY when a check failed",
    ):
        replace(readiness, schema_valid=False)


def test_gate_g3_decision_post_init_guards() -> None:
    bundle, proto, ledger, readiness = _setup_s10_s12_environment()
    g3_dec = evaluate_gate_g3_open_final_authorization(
        decision_id="g3_dec_01",
        frozen_bundle=bundle,
        protocol=proto,
        readiness_record=readiness,
        owner_opening_authorization_ref="owner_open_auth_01",
        event_ledger=ledger,
        decision_key=k(13),
    )
    with pytest.raises(SchemaViolation, match="decision_hash mismatch"):
        replace(g3_dec, decision_hash="sha256:tampered")
    with pytest.raises(SchemaViolation, match="invalid gate_g3_status"):
        replace(g3_dec, gate_g3_status="BAD_STATUS")


def test_equivalence_claim_post_init_guards() -> None:
    eq_ok = EquivalenceClaimArtifact.create(
        claim_id="eq_certified",
        old_bundle_id="bundle_1",
        new_bundle_id="bundle_2",
        evaluation_claim_scope="CLAIM_01",
        required_equivalence_dimensions=(
            EQ_DIM_SEMANTIC_OUTPUT,
            EQ_DIM_PROVENANCE,
        ),
        proven_equivalence_dimensions=(
            EQ_DIM_SEMANTIC_OUTPUT,
            EQ_DIM_PROVENANCE,
        ),
        proof_refs=("proof_1",),
    )
    with pytest.raises(SchemaViolation, match="claim_hash mismatch"):
        replace(eq_ok, claim_hash="sha256:tampered")
    with pytest.raises(
        SchemaViolation,
        match="cannot certify equivalence when required dimensions are unproven",
    ):
        replace(eq_ok, proven_equivalence_dimensions=(EQ_DIM_SEMANTIC_OUTPUT,))


def test_frozen_bundle_rejects_pre_close_key_or_empty_hashes() -> None:
    bundle, _, _, _ = _setup_s10_s12_environment()
    with pytest.raises(IllegalCausalReference):
        replace(
            bundle,
            freeze_information_key=k(
                10, phase=InformationPhase.BAR_PRE_CLOSE
            ),
        )
    with pytest.raises(SchemaViolation, match="policy_artifact_hashes"):
        replace(bundle, policy_artifact_hashes=())


def test_verify_final_protocol_bundle_closure_rejects_mismatched_bundle() -> None:
    bundle, proto, _, _ = _setup_s10_s12_environment()
    other_bundle = FrozenRepresentationBundle.create(
        bundle_name="bundle_other",
        artifact_lineage_id="lineage_other",
        representation_spec_hash="rep_hash_01",
        policy_artifact_hashes=("pol_hash_01",),
        objective_artifact_hash_or_state="obj_hash_01",
        state_catalog_hash="cat_hash_01",
        graph_spec_hash="gspec_hash_01",
        feature_view_hashes=("fv_hash_01",),
        descriptor_contract_hashes=("desc_hash_01",),
        dependence_contract_hashes=("dep_hash_01",),
        estimand_hashes=("est_hash_01",),
        fit_protocol_hash_or_state="fit_proto_01",
        selection_protocol_hash_or_state="sel_proto_01",
        dataset_role_artifact_hashes=("ds_role_01",),
        fold_protocol_hash_or_state=TypedState.NOT_CONFIGURED,
        code_artifact_hashes=("code_hash_01",),
        experiment_registry_root="exp_root_01",
        schema_contract_hashes=("schema_hash_01",),
        freeze_information_key=k(10),
        owner_freeze_authorization_ref="owner_freeze_auth_01",
    )
    with pytest.raises(
        SelectionBlockedError, match=S11_BUNDLE_DEPENDENCY_CLOSURE_MISSING
    ):
        verify_final_protocol_bundle_closure(proto, frozen_bundle=other_bundle)


def test_comparable_distance_rejects_mismatched_vector_lengths() -> None:
    snap = ComparabilitySnapshotSpec(
        snapshot_id="s1",
        representation_spec_hash="rep_1",
        policy_hash_lineage="pol_1",
        descriptor_set_hash="desc_1",
        information_key_version="V1",
        history_boundary_kind="ORIGIN_ANCHORED",
        source_semantic_identities=("BINANCE_SPOT_OHLC_V1",),
        actual_proxy_availability_mask=("ACTUAL:PRESENT",),
        schema_version="V1",
    )
    with pytest.raises(SchemaViolation, match="equal non-zero length"):
        compute_comparable_snapshot_distance(
            snap, snap, left_values=(1.0,), right_values=(1.0, 2.0)
        )


def test_s10_s12_realtime_throughput_benchmark() -> None:
    t0 = time.perf_counter()
    bundle, proto, ledger, readiness = _setup_s10_s12_environment()
    _ = evaluate_gate_g3_open_final_authorization(
        decision_id="g3_perf",
        frozen_bundle=bundle,
        protocol=proto,
        readiness_record=readiness,
        owner_opening_authorization_ref="owner_open_auth_01",
        event_ledger=ledger,
        decision_key=k(13),
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert elapsed_ms < 50.0
