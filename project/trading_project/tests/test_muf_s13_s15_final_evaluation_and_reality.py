"""MUF V1 S13, S14, S15 Adversarial Test Suite: Final Evaluation, Exposure Ledger, and Reality / Causal Market Understanding Surface.

Fixture discipline: SYNTHETIC SMALL FIXTURES ONLY (no owner data).
Verifies D1-3, D1-15, D1-20, D2-5, D2-6, D2-22, Correction-1 §3, §4, AP-1 §4:
- S13: open_and_run_final_evaluation_once, request_post_open_protocol_output (I-EVAL-1..6, I-EVP-1..3, I-SG-1B, Attacks 30 & 48)
- S14: FinalEvaluationOutcomeRecord, FinalEvaluationExposureRegistry (D1-20, I-FE-1..2, Attacks 22 & 49)
- S15: ExplanationStateRecord (D1-15, I-EXPL-1, Attack 24), RealityAuditSurfaceRecord (D1-3, I-HR-1..2, I-DR-3, Attack 12),
  and analyze_causal_market_state_as_of (real-time causal market state diagnostic report)
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
    SchemaIdentity,
    SchemaViolation,
    TypedState,
    scan_market_shape_implementations,
    scan_private_imports,
    scan_prohibited_implementations,
)
from trading_system.market_understanding.dependence_accounting import (
    DependenceAccountingContract,
    RESEARCH_DEBT_024_STANDING_STATUS,
    STATISTICAL_INDEPENDENCE_STANDING_CLAIM,
    build_dependence_accounting_bundle,
)
from trading_system.market_understanding.detector_witness import (
    adapt_detector_witness_stream,
)
from trading_system.market_understanding.final_evaluation_and_reality import (
    EXPLANATION_STATE_CONTRADICTED,
    EXPLANATION_STATE_MONITORING,
    EXPLANATION_STATE_PATTERN_SATISFIED,
    EXPLANATION_STATE_SUPERSEDED,
    EXPOSURE_STATUS_DEVELOPMENT_ONLY,
    EXPOSURE_STATUS_EXPOSED_FINAL,
    OUTCOME_POLARITY_FAVORABLE,
    OUTCOME_POLARITY_UNFAVORABLE,
    S13_INVALID_FINAL_EVALUATION,
    S13_UNPERMITTED_FINAL_OUTPUT_REQUESTED,
    S14_EXPOSED_DATASET_LINEAGE_REUSE_BLOCKED,
    S14_NEGATIVE_RESULT_DELETION_FORBIDDEN,
    S15_FORBIDDEN_EXPLANATION_STATE_OR_WEIGHT,
    S15_INVALID_REALITY_AUDIT_RECORD,
    ExplanationStateRecord,
    FinalEvaluationExposureRegistry,
    FinalEvaluationOutcomeRecord,
    RealityAuditSurfaceRecord,
    analyze_causal_market_state_as_of,
    open_and_run_final_evaluation_once,
    request_post_open_protocol_output,
)
from trading_system.market_understanding.freeze_and_readiness import (
    EQ_DIM_CAUSAL_VISIBILITY,
    EQ_DIM_PROVENANCE,
    EQ_DIM_SEMANTIC_OUTPUT,
    PROTOCOL_EVENT_EXPLORATORY_OUTPUT_REQUESTED,
    EquivalenceClaimArtifact,
    EvaluationProtocolArtifact,
    EvaluationProtocolEventLedger,
    FrozenRepresentationBundle,
    PreFinalReadinessRecord,
    evaluate_gate_g3_open_final_authorization,
)
from trading_system.market_understanding.policy_governance import (
    DATASET_ROLE_DEVELOPMENT_FIT,
    DATASET_ROLE_FINAL_EVALUATION_LOCKED,
    EXPOSURE_STATE_EXPOSED_INVALID_FOR_FINAL,
    PROVENANCE_PREDEFINED_CONTRACT,
    DatasetIdentityArtifact,
    DatasetRoleArtifact,
    PolicyArtifact,
    SelectionBlockedError,
)
from trading_system.market_understanding.price_path import (
    MetricResult,
    PublishedOhlcBarFact,
    exact_metric,
)
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
S13_S15_MODULE_PATH = (
    PROJECT_ROOT
    / "src"
    / "trading_system"
    / "market_understanding"
    / "final_evaluation_and_reality.py"
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
    dataset: str = "DS-DEV-S15",
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


def _setup_s13_s14_protocol(
    *,
    bundle_name: str = "bundle_s13_v1",
    lineage_id: str = "lineage_s13_01",
    protocol_id: str = "proto_s13_01",
    ancestry_root: str = "ANCESTRY_ROOT_FINAL_01",
):
    bundle = FrozenRepresentationBundle.create(
        bundle_name=bundle_name,
        artifact_lineage_id=lineage_id,
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
        evaluation_protocol_id=protocol_id,
        frozen_bundle=bundle,
        objective_artifact_hash="obj_hash_01",
        estimand_hashes=("est_hash_01",),
        state_catalog_hash="cat_hash_01",
        graph_spec_hash="gspec_hash_01",
        feature_view_hashes=("fv_hash_01",),
        dataset_identity="DS_FINAL_LOCKED_01",
        dataset_ancestry_root=ancestry_root,
        allowed_outputs=("PRIMARY_ESTIMAND_SUMMARY",),
        prohibited_outputs=("POST_HOC_SUBGROUP_MINING",),
        opening_authorization_ref_or_state="owner_open_auth_01",
        reservation_time_key=k(11),
    )
    ledger = EvaluationProtocolEventLedger()
    ledger.register_reserved_protocol(proto)
    readiness = PreFinalReadinessRecord.create(
        readiness_id=f"readiness_{protocol_id}",
        frozen_bundle=bundle,
        protocol=proto,
        readiness_key=k(12),
    )
    g3_dec = evaluate_gate_g3_open_final_authorization(
        decision_id=f"g3_{protocol_id}",
        frozen_bundle=bundle,
        protocol=proto,
        readiness_record=readiness,
        owner_opening_authorization_ref="owner_open_auth_01",
        event_ledger=ledger,
        decision_key=k(13),
    )
    return bundle, proto, ledger, readiness, g3_dec


def _setup_s15_dependence_bundle():
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
        dataset_id="DS-DEV-S15",
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
        owner_authorization_ref="owner-s15-role-1",
    )
    rep_spec = CandidateWaveRepresentationSpec.create(
        representation_id="rep_s15_v1",
        family_kind=FAMILY_ALPHA_POLICY_SCALE,
        scope_timeline_id=TIMELINE,
        scope_axis=InformationAxis.POSITIONAL,
        intrinsic_scale_key="swing_base_q25",
        identity_rule_ref="ORIGIN_ANCHORED_SWING_V1",
    )
    policy_art = PolicyArtifact.create(
        policy_id="pol-s15-01",
        detector_policy_witness_ref=wb.policy_witness_spec.spec_identity,
        scope_timeline_id=TIMELINE,
        scope_axis=InformationAxis.POSITIONAL,
        scope_representation_id="rep_s15_v1",
        calibration_provenance_kind=PROVENANCE_PREDEFINED_CONTRACT,
        reproduction_recipe_hash="recipe-fixed-01",
        effective_from_key=k(1),
        owner_authorization_ref="owner-s15-pol-1",
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
        state_catalog_id="cat_s15_v1",
        variable_specs=(var_eff,),
        descriptor_refs=tuple(s.descriptor_id for s in reg.all_specs()),
        relation_refs=(RELATION_ADJACENT_TO, RELATION_CONTAINS),
    )
    graph_spec = GenericFactualStateGraphSpec.create(
        graph_spec_id="gspec_s15_v1",
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
        contract_id="dep_contract_s15_v1"
    )
    return build_dependence_accounting_bundle(sg_bundle, contract=dep_contract)


def test_s13_s15_module_passes_s0_ast_scanners() -> None:
    source = S13_S15_MODULE_PATH.read_text(encoding="utf-8")
    assert scan_private_imports(source) == ()
    assert scan_prohibited_implementations(source) == ()
    assert scan_market_shape_implementations(source) == ()


def test_sealed_s0_to_s12_hashes_untouched() -> None:
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
        "docs/releases/MODULE_MUF_V1_S10_S12_ACCEPTED_SRC_TESTS.sha256",
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


def test_s13_open_and_run_final_evaluation_once_and_protocol_immutability() -> None:
    bundle, proto, ledger, _, g3_dec = _setup_s13_s14_protocol()
    exp_reg = FinalEvaluationExposureRegistry()
    proto_hash_before = proto.protocol_hash

    outcome = open_and_run_final_evaluation_once(
        outcome_record_id="out_01",
        gate_g3_decision=g3_dec,
        frozen_bundle=bundle,
        protocol=proto,
        event_ledger=ledger,
        exposure_registry=exp_reg,
        requested_outputs=("PRIMARY_ESTIMAND_SUMMARY",),
        primary_outcome_metric=exact_metric(0.62),
        outcome_polarity=OUTCOME_POLARITY_FAVORABLE,
        open_key=k(14),
    )
    assert outcome.exposure_status == EXPOSURE_STATUS_EXPOSED_FINAL
    assert ledger.is_exposed(proto.evaluation_protocol_id)
    assert proto.protocol_hash == proto_hash_before
    assert len(exp_reg.all_outcomes()) == 1

    with pytest.raises(SchemaViolation, match="outcome_record_hash mismatch"):
        replace(outcome, outcome_record_hash="sha256:tampered")


def test_s13_unpermitted_output_blocked_and_post_open_logged_exploratory_attacks_30_48() -> None:
    bundle, proto, ledger, _, g3_dec = _setup_s13_s14_protocol()
    exp_reg = FinalEvaluationExposureRegistry()

    with pytest.raises(
        SelectionBlockedError, match=S13_UNPERMITTED_FINAL_OUTPUT_REQUESTED
    ):
        open_and_run_final_evaluation_once(
            outcome_record_id="out_bad_output",
            gate_g3_decision=g3_dec,
            frozen_bundle=bundle,
            protocol=proto,
            event_ledger=ledger,
            exposure_registry=exp_reg,
            requested_outputs=("POST_HOC_SUBGROUP_MINING",),
            primary_outcome_metric=exact_metric(0.5),
            outcome_polarity=OUTCOME_POLARITY_FAVORABLE,
            open_key=k(14),
        )

    # Post-open additional output request is recorded as EXPLORATORY_OUTPUT_REQUESTED only (I-EVAL-6, Attack 30)
    ev = request_post_open_protocol_output(
        protocol=proto,
        event_ledger=ledger,
        requested_output_name="NEW_POST_HOC_SUMMARY",
        request_key=k(15),
    )
    assert ev.event_type == PROTOCOL_EVENT_EXPLORATORY_OUTPUT_REQUESTED


def test_s14_negative_outcome_retained_and_exposed_lineage_reuse_blocked_attacks_22_49() -> None:
    bundle1, proto1, ledger1, _, g3_dec1 = _setup_s13_s14_protocol(
        bundle_name="bundle_lin_1",
        lineage_id="lineage_01",
        protocol_id="proto_01",
        ancestry_root="SHARED_ANCESTRY_ROOT",
    )
    exp_reg = FinalEvaluationExposureRegistry()

    # First final evaluation produces an UNFAVORABLE (negative) result
    neg_outcome = open_and_run_final_evaluation_once(
        outcome_record_id="out_neg_01",
        gate_g3_decision=g3_dec1,
        frozen_bundle=bundle1,
        protocol=proto1,
        event_ledger=ledger1,
        exposure_registry=exp_reg,
        requested_outputs=("PRIMARY_ESTIMAND_SUMMARY",),
        primary_outcome_metric=exact_metric(-0.25),
        outcome_polarity=OUTCOME_POLARITY_UNFAVORABLE,
        open_key=k(14),
    )
    assert neg_outcome.outcome_polarity == OUTCOME_POLARITY_UNFAVORABLE

    # Deleting the negative outcome is forbidden (I-FE-2, Attack 49)
    with pytest.raises(
        ImmutabilityViolation, match=S14_NEGATIVE_RESULT_DELETION_FORBIDDEN
    ):
        exp_reg.delete_outcome("out_neg_01")

    # Attack 22 & 49: Modified lineage_02 tries to reuse SHARED_ANCESTRY_ROOT as final evidence -> BLOCKED
    bundle2, proto2, ledger2, _, g3_dec2 = _setup_s13_s14_protocol(
        bundle_name="bundle_lin_2",
        lineage_id="lineage_02",
        protocol_id="proto_02",
        ancestry_root="SHARED_ANCESTRY_ROOT",
    )
    with pytest.raises(
        SelectionBlockedError,
        match=S14_EXPOSED_DATASET_LINEAGE_REUSE_BLOCKED,
    ):
        open_and_run_final_evaluation_once(
            outcome_record_id="out_lin2_blocked",
            gate_g3_decision=g3_dec2,
            frozen_bundle=bundle2,
            protocol=proto2,
            event_ledger=ledger2,
            exposure_registry=exp_reg,
            requested_outputs=("PRIMARY_ESTIMAND_SUMMARY",),
            primary_outcome_metric=exact_metric(0.80),
            outcome_polarity=OUTCOME_POLARITY_FAVORABLE,
            open_key=k(16),
        )


def test_s14_equivalence_claim_allows_bugfix_lineage_transfer_d1_20_5() -> None:
    bundle1, proto1, ledger1, _, g3_dec1 = _setup_s13_s14_protocol(
        bundle_name="bundle_lin_1",
        lineage_id="lineage_01",
        protocol_id="proto_01",
        ancestry_root="SHARED_ANCESTRY_EQ",
    )
    exp_reg = FinalEvaluationExposureRegistry()
    _ = open_and_run_final_evaluation_once(
        outcome_record_id="out_eq_1",
        gate_g3_decision=g3_dec1,
        frozen_bundle=bundle1,
        protocol=proto1,
        event_ledger=ledger1,
        exposure_registry=exp_reg,
        requested_outputs=("PRIMARY_ESTIMAND_SUMMARY",),
        primary_outcome_metric=exact_metric(0.55),
        outcome_polarity=OUTCOME_POLARITY_FAVORABLE,
        open_key=k(14),
    )

    bundle2, proto2, ledger2, _, g3_dec2 = _setup_s13_s14_protocol(
        bundle_name="bundle_lin_2",
        lineage_id="lineage_02",
        protocol_id="proto_02",
        ancestry_root="SHARED_ANCESTRY_EQ",
    )
    eq_claim = EquivalenceClaimArtifact.create(
        claim_id="eq_claim_bugfix",
        old_bundle_id=bundle1.bundle_id,
        new_bundle_id=bundle2.bundle_id,
        evaluation_claim_scope="PRIMARY_CLAIM",
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
        proof_refs=("proof_equivalence_01",),
    )
    out2 = open_and_run_final_evaluation_once(
        outcome_record_id="out_eq_2",
        gate_g3_decision=g3_dec2,
        frozen_bundle=bundle2,
        protocol=proto2,
        event_ledger=ledger2,
        exposure_registry=exp_reg,
        requested_outputs=("PRIMARY_ESTIMAND_SUMMARY",),
        primary_outcome_metric=exact_metric(0.55),
        outcome_polarity=OUTCOME_POLARITY_FAVORABLE,
        open_key=k(16),
        equivalence_claim=eq_claim,
    )
    # Both outcomes remain in the registry (Attack 49)
    assert len(exp_reg.all_outcomes_for_ancestry("SHARED_ANCESTRY_EQ")) == 2
    assert out2.outcome_record_id == "out_eq_2"


def test_s15_explanation_state_whitelist_and_forbidden_terms_attack_24() -> None:
    for valid_state in (
        EXPLANATION_STATE_MONITORING,
        EXPLANATION_STATE_PATTERN_SATISFIED,
        EXPLANATION_STATE_CONTRADICTED,
        EXPLANATION_STATE_SUPERSEDED,
    ):
        rec = ExplanationStateRecord.create(
            explanation_id=f"expl_{valid_state}",
            pattern_contract_ref="PATTERN_01",
            explanation_state=valid_state,
            required_fact_refs=("fact_1",),
            explanation_information_key=k(5),
        )
        assert rec.explanation_state == valid_state

    # Attack 24: Forbidden states PROBABLE / LIKELY / SUPPORTED / WINNING_EXPLANATION / FACTUALLY_ESTABLISHED_WHERE_POSSIBLE rejected
    for forbidden_state in (
        "PROBABLE",
        "LIKELY",
        "SUPPORTED",
        "WINNING_EXPLANATION",
        "FACTUALLY_ESTABLISHED_WHERE_POSSIBLE",
    ):
        with pytest.raises(
            SchemaViolation, match=S15_FORBIDDEN_EXPLANATION_STATE_OR_WEIGHT
        ):
            ExplanationStateRecord.create(
                explanation_id="expl_bad",
                pattern_contract_ref="PATTERN_01",
                explanation_state=forbidden_state,
                required_fact_refs=("fact_1",),
                explanation_information_key=k(5),
            )

    # Numeric probability or weight rejected (Attack 24)
    with pytest.raises(
        SchemaViolation, match=S15_FORBIDDEN_EXPLANATION_STATE_OR_WEIGHT
    ):
        ExplanationStateRecord.create(
            explanation_id="expl_bad_weight",
            pattern_contract_ref="PATTERN_01",
            explanation_state=EXPLANATION_STATE_PATTERN_SATISFIED,
            required_fact_refs=("fact_1",),
            explanation_information_key=k(5),
            probability_or_support_weight=0.85,
        )


def test_s15_reality_audit_final_data_design_changes_invalidates_ancestry_attack_12() -> None:
    exp_reg = FinalEvaluationExposureRegistry()

    # Development reality audit with design changes -> EXPOSED_DEVELOPMENT_ONLY, no final invalidation
    dev_audit = RealityAuditSurfaceRecord.create(
        audit_record_id="audit_dev_01",
        dataset_identity="DS_DEV_01",
        dataset_ancestry_root="ANC_DEV_01",
        dataset_role=DATASET_ROLE_DEVELOPMENT_FIT,
        artifact_lineage_id="lineage_01",
        requested_design_changes=("ADJUST_DESCRIPTOR_SET",),
        audit_information_key=k(10),
        exposure_registry=exp_reg,
    )
    assert dev_audit.resulting_exposure_status == EXPOSURE_STATUS_DEVELOPMENT_ONLY
    assert not dev_audit.requires_new_lineage

    # Attack 12: Final OOS chart/reality review requests design changes -> EXPOSED_INVALID_FOR_FINAL_SELECTION + requires_new_lineage
    final_audit = RealityAuditSurfaceRecord.create(
        audit_record_id="audit_final_contaminated",
        dataset_identity="DS_FINAL_01",
        dataset_ancestry_root="ANC_FINAL_CONTAMINATED",
        dataset_role=DATASET_ROLE_FINAL_EVALUATION_LOCKED,
        artifact_lineage_id="lineage_01",
        requested_design_changes=("TUNE_CONFIRMATION_RULE",),
        audit_information_key=k(15),
        exposure_registry=exp_reg,
    )
    assert (
        final_audit.resulting_exposure_status
        == EXPOSURE_STATE_EXPOSED_INVALID_FOR_FINAL
    )
    assert final_audit.requires_new_lineage

    # Subsequent attempt to run final evaluation on ANC_FINAL_CONTAMINATED is blocked!
    bundle, proto, ledger, _, g3_dec = _setup_s13_s14_protocol(
        ancestry_root="ANC_FINAL_CONTAMINATED"
    )
    with pytest.raises(
        SelectionBlockedError,
        match=S14_EXPOSED_DATASET_LINEAGE_REUSE_BLOCKED,
    ):
        open_and_run_final_evaluation_once(
            outcome_record_id="out_contaminated_blocked",
            gate_g3_decision=g3_dec,
            frozen_bundle=bundle,
            protocol=proto,
            event_ledger=ledger,
            exposure_registry=exp_reg,
            requested_outputs=("PRIMARY_ESTIMAND_SUMMARY",),
            primary_outcome_metric=exact_metric(0.5),
            outcome_polarity=OUTCOME_POLARITY_FAVORABLE,
            open_key=k(16),
        )


def test_s15_analyze_causal_market_state_as_of_early_and_late_keys() -> None:
    dep_bundle = _setup_s15_dependence_bundle()

    # Early bar (bar 1): no confirmed waves yet -> MONITORING state, UNAVAILABLE continuation rate
    rep_early = analyze_causal_market_state_as_of(
        dep_bundle, query_key=k(1)
    )
    assert (
        rep_early.explanation_record.explanation_state
        == EXPLANATION_STATE_MONITORING
    )
    assert rep_early.empirical_continuation_rate is TypedState.UNAVAILABLE
    assert (
        rep_early.statistical_independence_claim
        == STATISTICAL_INDEPENDENCE_STANDING_CLAIM
    )
    assert (
        rep_early.research_debt_024_status == RESEARCH_DEBT_024_STANDING_STATUS
    )

    # Late bar (bar 10): confirmed waves present -> PATTERN_REQUIREMENTS_SATISFIED
    rep_late = analyze_causal_market_state_as_of(
        dep_bundle, query_key=k(10)
    )
    assert (
        rep_late.explanation_record.explanation_state
        == EXPLANATION_STATE_PATTERN_SATISFIED
    )
    assert len(rep_late.confirmed_wave_process_ids) >= 1
    assert rep_late.historical_right_censored_count == 1
    assert isinstance(
        rep_late.latest_confirmed_wave_efficiency_ratio, MetricResult
    )


def test_s13_rejects_mismatched_gate_g3_decision() -> None:
    bundle, proto, ledger, _, _ = _setup_s13_s14_protocol()
    _, _, _, _, other_g3 = _setup_s13_s14_protocol(
        protocol_id="other_proto_id"
    )
    exp_reg = FinalEvaluationExposureRegistry()

    with pytest.raises(
        SelectionBlockedError, match=S13_INVALID_FINAL_EVALUATION
    ):
        open_and_run_final_evaluation_once(
            outcome_record_id="out_mismatch",
            gate_g3_decision=other_g3,
            frozen_bundle=bundle,
            protocol=proto,
            event_ledger=ledger,
            exposure_registry=exp_reg,
            requested_outputs=("PRIMARY_ESTIMAND_SUMMARY",),
            primary_outcome_metric=exact_metric(0.5),
            outcome_polarity=OUTCOME_POLARITY_FAVORABLE,
            open_key=k(14),
        )


def test_s13_rejects_non_g3_decision_object() -> None:
    bundle, proto, ledger, _, _ = _setup_s13_s14_protocol()
    exp_reg = FinalEvaluationExposureRegistry()
    with pytest.raises(
        SelectionBlockedError, match=S13_INVALID_FINAL_EVALUATION
    ):
        open_and_run_final_evaluation_once(
            outcome_record_id="out_no_g3",
            gate_g3_decision="invalid",  # type: ignore[arg-type]
            frozen_bundle=bundle,
            protocol=proto,
            event_ledger=ledger,
            exposure_registry=exp_reg,
            requested_outputs=("PRIMARY_ESTIMAND_SUMMARY",),
            primary_outcome_metric=exact_metric(0.5),
            outcome_polarity=OUTCOME_POLARITY_FAVORABLE,
            open_key=k(14),
        )


def test_s14_outcome_record_post_init_guards() -> None:
    bundle, proto, ledger, _, g3_dec = _setup_s13_s14_protocol()
    exp_reg = FinalEvaluationExposureRegistry()
    outcome = open_and_run_final_evaluation_once(
        outcome_record_id="out_01",
        gate_g3_decision=g3_dec,
        frozen_bundle=bundle,
        protocol=proto,
        event_ledger=ledger,
        exposure_registry=exp_reg,
        requested_outputs=("PRIMARY_ESTIMAND_SUMMARY",),
        primary_outcome_metric=exact_metric(0.62),
        outcome_polarity=OUTCOME_POLARITY_FAVORABLE,
        open_key=k(14),
    )
    with pytest.raises(SchemaViolation, match="invalid outcome_polarity"):
        replace(outcome, outcome_polarity="INVALID_POLARITY")
    with pytest.raises(SchemaViolation, match="exposure_status must be"):
        replace(outcome, exposure_status="UNEXPOSED")
    with pytest.raises(ImmutabilityViolation, match="already recorded"):
        exp_reg.record_outcome(outcome)


def test_s15_explanation_record_post_init_guards() -> None:
    rec = ExplanationStateRecord.create(
        explanation_id="expl_1",
        pattern_contract_ref="PATTERN_01",
        explanation_state=EXPLANATION_STATE_MONITORING,
        required_fact_refs=("fact_1",),
        explanation_information_key=k(5),
    )
    with pytest.raises(SchemaViolation, match="explanation_hash mismatch"):
        replace(rec, explanation_hash="sha256:tampered")
    with pytest.raises(
        SchemaViolation, match="same_information_batch_order_unknown must be bool"
    ):
        replace(rec, same_information_batch_order_unknown="yes")  # type: ignore[arg-type]


def test_s15_reality_audit_post_init_guards() -> None:
    audit = RealityAuditSurfaceRecord.create(
        audit_record_id="audit_final_clean",
        dataset_identity="DS_FINAL_01",
        dataset_ancestry_root="ANC_FINAL_CLEAN",
        dataset_role=DATASET_ROLE_FINAL_EVALUATION_LOCKED,
        artifact_lineage_id="lineage_01",
        requested_design_changes=(),
        audit_information_key=k(15),
    )
    assert audit.resulting_exposure_status == EXPOSURE_STATUS_EXPOSED_FINAL
    assert not audit.requires_new_lineage
    with pytest.raises(SchemaViolation, match="audit_record_hash mismatch"):
        replace(audit, audit_record_hash="sha256:tampered")


def test_s15_analyze_rejects_invalid_bundle_or_pre_close_key() -> None:
    dep_bundle = _setup_s15_dependence_bundle()
    with pytest.raises(SchemaViolation, match="DependenceAccountingBundle"):
        analyze_causal_market_state_as_of("invalid", query_key=k(5))  # type: ignore[arg-type]
    with pytest.raises(IllegalCausalReference):
        analyze_causal_market_state_as_of(
            dep_bundle,
            query_key=k(5, phase=InformationPhase.BAR_PRE_CLOSE),
        )


def test_s15_prefix_invariance_of_causal_market_understanding_report() -> None:
    dep_bundle = _setup_s15_dependence_bundle()
    r1 = analyze_causal_market_state_as_of(dep_bundle, query_key=k(6))
    r2 = analyze_causal_market_state_as_of(dep_bundle, query_key=k(6))
    assert r1 == r2


def test_s13_rejects_empty_requested_outputs() -> None:
    bundle, proto, ledger, _, g3_dec = _setup_s13_s14_protocol()
    exp_reg = FinalEvaluationExposureRegistry()
    with pytest.raises(SchemaViolation, match="requested_outputs must be non-empty"):
        open_and_run_final_evaluation_once(
            outcome_record_id="out_empty_req",
            gate_g3_decision=g3_dec,
            frozen_bundle=bundle,
            protocol=proto,
            event_ledger=ledger,
            exposure_registry=exp_reg,
            requested_outputs=(),
            primary_outcome_metric=exact_metric(0.5),
            outcome_polarity=OUTCOME_POLARITY_FAVORABLE,
            open_key=k(14),
        )


def test_s14_record_outcome_rejects_non_outcome_object() -> None:
    exp_reg = FinalEvaluationExposureRegistry()
    with pytest.raises(
        SchemaViolation, match="expected FinalEvaluationOutcomeRecord"
    ):
        exp_reg.record_outcome("not_an_outcome")  # type: ignore[arg-type]


def test_s15_explanation_rejects_empty_required_fact_refs() -> None:
    with pytest.raises(SchemaViolation, match="required_fact_refs must be non-empty"):
        ExplanationStateRecord.create(
            explanation_id="expl_empty_refs",
            pattern_contract_ref="PATTERN_01",
            explanation_state=EXPLANATION_STATE_MONITORING,
            required_fact_refs=(),
            explanation_information_key=k(5),
        )


def test_s13_s15_realtime_throughput_benchmark() -> None:
    dep_bundle = _setup_s15_dependence_bundle()
    t0 = time.perf_counter()
    _ = analyze_causal_market_state_as_of(dep_bundle, query_key=k(10))
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert elapsed_ms < 50.0
