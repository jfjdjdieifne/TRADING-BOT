"""MUF V1 S9 & Gate G2 Adversarial Test Suite: Development Information Evaluation & Selection.

Fixture discipline: SYNTHETIC SMALL FIXTURES ONLY (no owner data).
Verifies D2-3, D2-4, D2-17, D2-22, and AP-1 §4.1..4.4:
- CandidateInformationEvaluationRecord (I-SEL-1..3, I-FVIEW-1, I-SG-1A)
- GateG2InformationSelectionDecision & run_gate_g2_information_selection (D2-17, I-SEL-1..5)
- GATE_G2_NOT_CONFIGURED when ObjectiveArtifact is NOT_CONFIGURED/UNDEFINED (I-SEL-4)
- GATE_G2_TIED_NO_UNIQUE_WINNER when top candidates tie (I-SEL-5)
- Rejection of visual preference tie-breaker (I-SEL-5)
- Rejection of INELIGIBLE candidates (I-SEL-1) and FINAL_EVALUATION_LOCKED datasets (I-SEL-3)
"""
from dataclasses import replace
import hashlib
from pathlib import Path
import time

import pytest

from trading_system.market_understanding.availability import InformationAxis
from trading_system.market_understanding.contracts import (
    IllegalCausalReference,
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
    build_dependence_accounting_bundle,
)
from trading_system.market_understanding.detector_witness import (
    adapt_detector_witness_stream,
)
from trading_system.market_understanding.estimand_catalog import (
    DevelopmentEvaluationProtocol,
    EstimandArtifact,
    FeatureViewSpec,
)
from trading_system.market_understanding.information_selection import (
    CANDIDATE_INFORMATION_EVALUATION_SCHEMA,
    GATE_G2_NOT_CONFIGURED,
    GATE_G2_SELECTED,
    GATE_G2_SELECTION_DECISION_SCHEMA,
    GATE_G2_TIED_NO_UNIQUE_WINNER,
    S9_FINAL_DATASET_FORBIDDEN_IN_G2,
    S9_INCONSISTENT_CANDIDATE_COMPARISON,
    S9_INELIGIBLE_CANDIDATE_REJECTED,
    S9_INVALID_CANDIDATE_EVALUATION,
    S9_INVALID_GATE_G2_DECISION,
    S9_MISSING_INFORMATION_OBJECTIVE,
    S9_VISUAL_TIE_BREAKER_FORBIDDEN,
    CandidateInformationEvaluationRecord,
    GateG2InformationSelectionDecision,
    evaluate_candidate_information_on_development,
    run_gate_g2_information_selection,
)
from trading_system.market_understanding.identity import (
    canonical_artifact_identity,
)
from trading_system.market_understanding.policy_governance import (
    DATASET_ROLE_DEVELOPMENT_FIT,
    DATASET_ROLE_DEVELOPMENT_SELECTION,
    DATASET_ROLE_FINAL_EVALUATION_LOCKED,
    OBJECTIVE_KIND_INFORMATION,
    OBJECTIVE_KIND_REPRESENTATION_DIAGNOSTIC,
    PROVENANCE_PREDEFINED_CONTRACT,
    DatasetIdentityArtifact,
    DatasetRoleArtifact,
    ExperimentRegistry,
    ObjectiveArtifact,
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
    G1_STATUS_ELIGIBLE,
    G1_STATUS_INELIGIBLE,
    construct_candidate_wave_representation,
)
from trading_system.research.information_time import (
    INFORMATION_KEY_VERSION,
    InformationKey,
    InformationPhase,
)
from trading_system.structure.swing_detector import EmpiricalConfirmationPolicy


PROJECT_ROOT = Path(__file__).resolve().parents[1]
S9_MODULE_PATH = (
    PROJECT_ROOT
    / "src"
    / "trading_system"
    / "market_understanding"
    / "information_selection.py"
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
    dataset: str = "DS-DEV-SEL-S9",
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


def _setup_s9_environment():
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
        dataset_id="DS-DEV-SEL-S9",
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
        role=DATASET_ROLE_DEVELOPMENT_SELECTION,
        role_assignment_key=k(1),
        permitted_operations=(
            "DEVELOPMENT_SELECTION",
            "CANDIDATE_WAVE_CONSTRUCTION",
        ),
        prohibited_operations=("FINAL_LOCKED_CLAIM",),
        owner_authorization_ref="owner-s9-role-1",
    )
    rep_spec = CandidateWaveRepresentationSpec.create(
        representation_id="rep_s9_v1",
        family_kind=FAMILY_ALPHA_POLICY_SCALE,
        scope_timeline_id=TIMELINE,
        scope_axis=InformationAxis.POSITIONAL,
        intrinsic_scale_key="swing_base_q25",
        identity_rule_ref="ORIGIN_ANCHORED_SWING_V1",
    )
    policy_art = PolicyArtifact.create(
        policy_id="pol-s9-01",
        detector_policy_witness_ref=wb.policy_witness_spec.spec_identity,
        scope_timeline_id=TIMELINE,
        scope_axis=InformationAxis.POSITIONAL,
        scope_representation_id="rep_s9_v1",
        calibration_provenance_kind=PROVENANCE_PREDEFINED_CONTRACT,
        reproduction_recipe_hash="recipe-fixed-01",
        effective_from_key=k(1),
        owner_authorization_ref="owner-s9-pol-1",
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
        state_catalog_id="cat_s9_v1",
        variable_specs=(var_eff,),
        descriptor_refs=tuple(s.descriptor_id for s in reg.all_specs()),
        relation_refs=(RELATION_ADJACENT_TO, RELATION_CONTAINS),
    )
    graph_spec = GenericFactualStateGraphSpec.create(
        graph_spec_id="gspec_s9_v1",
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
        contract_id="dep_contract_s9_v1"
    )
    dep_bundle = build_dependence_accounting_bundle(
        sg_bundle, contract=dep_contract
    )
    estimand = EstimandArtifact.create(
        estimand_id="est_s9_01",
        state_catalog=catalog,
        population_variable_refs=("SV_WAVE_EFFICIENCY",),
        conditioning_variable_refs=("SV_WAVE_EFFICIENCY",),
        preregistration_key=k(1),
    )
    fv_spec = FeatureViewSpec.create(
        feature_view_id="fv_s9_01",
        state_catalog=catalog,
        estimand=estimand,
        selected_state_variable_refs=("SV_WAVE_EFFICIENCY",),
    )
    obj_art = ObjectiveArtifact.create(
        objective_id="obj_info_s9",
        objective_kind=OBJECTIVE_KIND_INFORMATION,
        semantic_definition="Evaluate conditional wave continuation information",
        estimand_refs=(estimand.estimand_hash,),
        dataset_role_permissions=(
            DATASET_ROLE_DEVELOPMENT_FIT,
            DATASET_ROLE_DEVELOPMENT_SELECTION,
        ),
        aggregation_contract="EPISODE_CLUSTER_WEIGHTED_MEAN",
        missingness_contract="FAIL_CLOSED",
        tie_contract="PRESERVE_TIED_CANDIDATES_NO_WINNER",
        comparison_direction="MAXIMIZE",
        creation_key=k(1),
        code_hash="c" * 64,
        owner_authorization_ref="owner-s9-obj-1",
    )
    exp_reg = ExperimentRegistry()
    exp_reg.preregister(
        experiment_id="exp_s9_01",
        preregistration_key=k(1),
        representation_spec_hash=rep_spec.representation_spec_hash,
        policy_artifact_hashes=(policy_art.policy_hash,),
        objective_artifact_hash=obj_art.objective_hash,
        dataset_identities_by_role={
            DATASET_ROLE_DEVELOPMENT_SELECTION: "DS-DEV-SEL-S9"
        },
        code_hash="code-s9-1",
        fit_protocol_hash="fit-proto-s9",
    )
    protocol = DevelopmentEvaluationProtocol.create(
        protocol_id="dev_proto_s9_01",
        estimand=estimand,
        feature_view=fv_spec,
        state_catalog=catalog,
        graph_spec=graph_spec,
        dependence_contract=dep_contract,
        objective_artifact=obj_art,
        dataset_id="DS-DEV-SEL-S9",
        dataset_role=DATASET_ROLE_DEVELOPMENT_SELECTION,
        experiment_id="exp_s9_01",
        preregistration_key=k(1),
    )
    return (
        dep_bundle,
        catalog,
        graph_spec,
        dep_contract,
        estimand,
        fv_spec,
        obj_art,
        exp_reg,
        protocol,
    )


def _mk_eval_record(
    base_rec: CandidateInformationEvaluationRecord,
    *,
    evaluation_id: str,
    candidate_id: str,
    score_val: float,
    dataset_role: str = DATASET_ROLE_DEVELOPMENT_SELECTION,
    structural_eligibility_status: str = G1_STATUS_ELIGIBLE,
    estimand_hash: str | None = None,
) -> CandidateInformationEvaluationRecord:
    est_h = estimand_hash or base_rec.estimand_hash
    score = exact_metric(score_val)
    r_hash = canonical_artifact_identity(
        CANDIDATE_INFORMATION_EVALUATION_SCHEMA,
        identity_payload={
            "evaluation_id": evaluation_id,
            "candidate_id": candidate_id,
            "experiment_id": base_rec.experiment_id,
            "representation_spec_hash": base_rec.representation_spec_hash,
            "policy_hash": base_rec.policy_hash,
            "protocol_hash": base_rec.protocol_hash,
            "estimand_hash": est_h,
            "feature_view_hash": base_rec.feature_view_hash,
            "state_catalog_hash": base_rec.state_catalog_hash,
            "graph_spec_hash": base_rec.graph_spec_hash,
            "dependence_contract_hash": base_rec.dependence_contract_hash,
            "objective_hash": base_rec.objective_hash,
            "dataset_id": base_rec.dataset_id,
            "dataset_role": dataset_role,
            "structural_eligibility_status": structural_eligibility_status,
            "uncensored_realization_count": str(
                base_rec.uncensored_realization_count
            ),
            "right_censored_realization_count": str(
                base_rec.right_censored_realization_count
            ),
            "non_overlapping_span_cluster_count": str(
                base_rec.non_overlapping_span_cluster_count
            ),
            "cluster_weighted_information_score": repr(score.value),
            "evaluation_key": base_rec.evaluation_key,
        },
    )
    return CandidateInformationEvaluationRecord(
        evaluation_id=evaluation_id,
        candidate_id=candidate_id,
        experiment_id=base_rec.experiment_id,
        representation_spec_hash=base_rec.representation_spec_hash,
        policy_hash=base_rec.policy_hash,
        protocol_hash=base_rec.protocol_hash,
        estimand_hash=est_h,
        feature_view_hash=base_rec.feature_view_hash,
        state_catalog_hash=base_rec.state_catalog_hash,
        graph_spec_hash=base_rec.graph_spec_hash,
        dependence_contract_hash=base_rec.dependence_contract_hash,
        objective_hash=base_rec.objective_hash,
        dataset_id=base_rec.dataset_id,
        dataset_role=dataset_role,
        structural_eligibility_status=structural_eligibility_status,
        uncensored_realization_count=base_rec.uncensored_realization_count,
        right_censored_realization_count=base_rec.right_censored_realization_count,
        non_overlapping_span_cluster_count=base_rec.non_overlapping_span_cluster_count,
        cluster_weighted_information_score=score,
        evaluation_key=base_rec.evaluation_key,
        evaluation_record_hash=r_hash,
    )


def test_s9_module_passes_s0_ast_scanners() -> None:
    source = S9_MODULE_PATH.read_text(encoding="utf-8")
    assert scan_private_imports(source) == ()
    assert scan_prohibited_implementations(source) == ()
    assert scan_market_shape_implementations(source) == ()


def test_sealed_s0_to_s8_hashes_untouched() -> None:
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


def test_evaluate_candidate_information_on_development_valid() -> None:
    (
        dep_bundle,
        _,
        _,
        _,
        estimand,
        fv_spec,
        obj_art,
        exp_reg,
        protocol,
    ) = _setup_s9_environment()

    rec, eval_bundle = evaluate_candidate_information_on_development(
        dep_bundle,
        evaluation_id="eval_s9_c1",
        candidate_id="cand_alpha_q25",
        protocol=protocol,
        estimand=estimand,
        feature_view=fv_spec,
        objective_artifact=obj_art,
        experiment_registry=exp_reg,
    )
    assert rec.structural_eligibility_status == G1_STATUS_ELIGIBLE
    assert rec.uncensored_realization_count == eval_bundle.uncensored_count
    assert (
        rec.right_censored_realization_count == eval_bundle.right_censored_count
    )
    assert isinstance(rec.cluster_weighted_information_score, MetricResult)

    with pytest.raises(
        SchemaViolation, match="evaluation_record_hash mismatch"
    ):
        replace(rec, evaluation_record_hash="sha256:tampered")


def test_gate_g2_not_configured_when_objective_undefined_d2_17_i_sel_4() -> None:
    dec = run_gate_g2_information_selection(
        decision_id="g2_not_cfg_01",
        eligible_candidate_ids=("cand_a", "cand_b"),
        objective_artifact=TypedState.NOT_CONFIGURED,
        candidate_evaluations=(),
        decision_key=k(10),
    )
    assert dec.gate_status == GATE_G2_NOT_CONFIGURED
    assert dec.selected_winner_candidate_id is TypedState.NOT_CONFIGURED
    assert dec.eligible_candidate_ids == ("cand_a", "cand_b")
    assert dec.research_debt_024_status == RESEARCH_DEBT_024_STANDING_STATUS


def test_gate_g2_selects_unique_winner_maximize_and_minimize() -> None:
    (
        dep_bundle,
        _,
        _,
        _,
        estimand,
        fv_spec,
        obj_art,
        exp_reg,
        protocol,
    ) = _setup_s9_environment()

    base_rec, _ = evaluate_candidate_information_on_development(
        dep_bundle,
        evaluation_id="eval_base",
        candidate_id="cand_a",
        protocol=protocol,
        estimand=estimand,
        feature_view=fv_spec,
        objective_artifact=obj_art,
        experiment_registry=exp_reg,
    )
    rec_a = _mk_eval_record(
        base_rec, evaluation_id="ev_a", candidate_id="cand_a", score_val=0.45
    )
    rec_b = _mk_eval_record(
        base_rec, evaluation_id="ev_b", candidate_id="cand_b", score_val=0.82
    )

    dec = run_gate_g2_information_selection(
        decision_id="g2_sel_01",
        eligible_candidate_ids=("cand_a", "cand_b"),
        objective_artifact=obj_art,
        candidate_evaluations=(rec_a, rec_b),
        decision_key=k(10),
    )
    assert dec.gate_status == GATE_G2_SELECTED
    assert dec.selected_winner_candidate_id == "cand_b"
    assert dec.tied_top_candidate_ids == ()

    with pytest.raises(SchemaViolation, match="decision_hash mismatch"):
        replace(dec, decision_hash="sha256:tampered")


def test_gate_g2_preserves_ties_without_inventing_winner_i_sel_5() -> None:
    (
        dep_bundle,
        _,
        _,
        _,
        estimand,
        fv_spec,
        obj_art,
        exp_reg,
        protocol,
    ) = _setup_s9_environment()

    base_rec, _ = evaluate_candidate_information_on_development(
        dep_bundle,
        evaluation_id="eval_base",
        candidate_id="cand_a",
        protocol=protocol,
        estimand=estimand,
        feature_view=fv_spec,
        objective_artifact=obj_art,
        experiment_registry=exp_reg,
    )
    rec_a = _mk_eval_record(
        base_rec, evaluation_id="ev_a", candidate_id="cand_a", score_val=0.75
    )
    rec_b = _mk_eval_record(
        base_rec, evaluation_id="ev_b", candidate_id="cand_b", score_val=0.75
    )

    dec_tie = run_gate_g2_information_selection(
        decision_id="g2_tie_01",
        eligible_candidate_ids=("cand_a", "cand_b"),
        objective_artifact=obj_art,
        candidate_evaluations=(rec_a, rec_b),
        decision_key=k(10),
    )
    assert dec_tie.gate_status == GATE_G2_TIED_NO_UNIQUE_WINNER
    assert dec_tie.selected_winner_candidate_id is TypedState.UNDEFINED
    assert dec_tie.tied_top_candidate_ids == ("cand_a", "cand_b")


def test_visual_preference_tie_breaker_rejected_i_sel_5() -> None:
    with pytest.raises(
        SelectionBlockedError, match=S9_VISUAL_TIE_BREAKER_FORBIDDEN
    ):
        run_gate_g2_information_selection(
            decision_id="g2_vis_bad",
            eligible_candidate_ids=("cand_a", "cand_b"),
            objective_artifact=TypedState.NOT_CONFIGURED,
            candidate_evaluations=(),
            decision_key=k(10),
            visual_preference_candidate_id="cand_a",
        )


def test_ineligible_candidate_rejected_i_sel_1() -> None:
    (
        dep_bundle,
        _,
        _,
        _,
        estimand,
        fv_spec,
        obj_art,
        exp_reg,
        protocol,
    ) = _setup_s9_environment()

    base_rec, _ = evaluate_candidate_information_on_development(
        dep_bundle,
        evaluation_id="eval_base",
        candidate_id="cand_a",
        protocol=protocol,
        estimand=estimand,
        feature_view=fv_spec,
        objective_artifact=obj_art,
        experiment_registry=exp_reg,
    )
    with pytest.raises(
        SelectionBlockedError, match=S9_INELIGIBLE_CANDIDATE_REJECTED
    ):
        _mk_eval_record(
            base_rec,
            evaluation_id="ev_inelig",
            candidate_id="cand_inelig",
            score_val=0.5,
            structural_eligibility_status=G1_STATUS_INELIGIBLE,
        )


def test_final_evaluation_locked_role_rejected_in_s9_i_sel_3() -> None:
    (
        dep_bundle,
        _,
        _,
        _,
        estimand,
        fv_spec,
        obj_art,
        exp_reg,
        protocol,
    ) = _setup_s9_environment()

    base_rec, _ = evaluate_candidate_information_on_development(
        dep_bundle,
        evaluation_id="eval_base",
        candidate_id="cand_a",
        protocol=protocol,
        estimand=estimand,
        feature_view=fv_spec,
        objective_artifact=obj_art,
        experiment_registry=exp_reg,
    )
    with pytest.raises(
        SelectionBlockedError, match=S9_FINAL_DATASET_FORBIDDEN_IN_G2
    ):
        _mk_eval_record(
            base_rec,
            evaluation_id="ev_final_role",
            candidate_id="cand_a",
            score_val=0.5,
            dataset_role=DATASET_ROLE_FINAL_EVALUATION_LOCKED,
        )


def test_inconsistent_candidate_comparison_rejected() -> None:
    (
        dep_bundle,
        _,
        _,
        _,
        estimand,
        fv_spec,
        obj_art,
        exp_reg,
        protocol,
    ) = _setup_s9_environment()

    base_rec, _ = evaluate_candidate_information_on_development(
        dep_bundle,
        evaluation_id="eval_base",
        candidate_id="cand_a",
        protocol=protocol,
        estimand=estimand,
        feature_view=fv_spec,
        objective_artifact=obj_art,
        experiment_registry=exp_reg,
    )
    rec_a = _mk_eval_record(
        base_rec, evaluation_id="ev_a", candidate_id="cand_a", score_val=0.5
    )
    rec_b_diff_est = _mk_eval_record(
        base_rec,
        evaluation_id="ev_b",
        candidate_id="cand_b",
        score_val=0.6,
        estimand_hash="sha256:different_estimand",
    )
    with pytest.raises(
        SelectionBlockedError, match=S9_INCONSISTENT_CANDIDATE_COMPARISON
    ):
        run_gate_g2_information_selection(
            decision_id="g2_inconsistent",
            eligible_candidate_ids=("cand_a", "cand_b"),
            objective_artifact=obj_art,
            candidate_evaluations=(rec_a, rec_b_diff_est),
            decision_key=k(10),
        )


def test_evaluate_candidate_rejects_missing_or_wrong_objective_kind() -> None:
    (
        dep_bundle,
        _,
        _,
        _,
        estimand,
        fv_spec,
        _,
        exp_reg,
        protocol,
    ) = _setup_s9_environment()

    with pytest.raises(
        SelectionBlockedError, match=S9_MISSING_INFORMATION_OBJECTIVE
    ):
        evaluate_candidate_information_on_development(
            dep_bundle,
            evaluation_id="ev_no_obj",
            candidate_id="cand_a",
            protocol=protocol,
            estimand=estimand,
            feature_view=fv_spec,
            objective_artifact=TypedState.NOT_CONFIGURED,
            experiment_registry=exp_reg,
        )

    qual_obj = ObjectiveArtifact.create(
        objective_id="obj_qual_only",
        objective_kind=OBJECTIVE_KIND_REPRESENTATION_DIAGNOSTIC,
        semantic_definition="Structural qualification only",
        estimand_refs=(),
        dataset_role_permissions=(DATASET_ROLE_DEVELOPMENT_FIT,),
        aggregation_contract="ALL_MUST_PASS",
        missingness_contract="FAIL_CLOSED",
        tie_contract="PRESERVE_TIED_CANDIDATES_NO_WINNER",
        comparison_direction="MAXIMIZE",
        creation_key=k(1),
        code_hash="c" * 64,
        owner_authorization_ref="owner-qual-1",
    )
    with pytest.raises(
        SelectionBlockedError, match=S9_MISSING_INFORMATION_OBJECTIVE
    ):
        evaluate_candidate_information_on_development(
            dep_bundle,
            evaluation_id="ev_qual_obj",
            candidate_id="cand_a",
            protocol=protocol,
            estimand=estimand,
            feature_view=fv_spec,
            objective_artifact=qual_obj,
            experiment_registry=exp_reg,
        )


def test_gate_g2_rejects_candidate_not_in_eligible_set() -> None:
    (
        dep_bundle,
        _,
        _,
        _,
        estimand,
        fv_spec,
        obj_art,
        exp_reg,
        protocol,
    ) = _setup_s9_environment()

    base_rec, _ = evaluate_candidate_information_on_development(
        dep_bundle,
        evaluation_id="eval_base",
        candidate_id="cand_a",
        protocol=protocol,
        estimand=estimand,
        feature_view=fv_spec,
        objective_artifact=obj_art,
        experiment_registry=exp_reg,
    )
    with pytest.raises(
        SelectionBlockedError, match=S9_INELIGIBLE_CANDIDATE_REJECTED
    ):
        run_gate_g2_information_selection(
            decision_id="g2_unlisted_cand",
            eligible_candidate_ids=("cand_other",),
            objective_artifact=obj_art,
            candidate_evaluations=(base_rec,),
            decision_key=k(10),
        )


def test_gate_g2_rejects_duplicate_candidate_evaluations() -> None:
    (
        dep_bundle,
        _,
        _,
        _,
        estimand,
        fv_spec,
        obj_art,
        exp_reg,
        protocol,
    ) = _setup_s9_environment()

    base_rec, _ = evaluate_candidate_information_on_development(
        dep_bundle,
        evaluation_id="eval_base",
        candidate_id="cand_a",
        protocol=protocol,
        estimand=estimand,
        feature_view=fv_spec,
        objective_artifact=obj_art,
        experiment_registry=exp_reg,
    )
    with pytest.raises(SchemaViolation, match="duplicate evaluation"):
        run_gate_g2_information_selection(
            decision_id="g2_dup_cand",
            eligible_candidate_ids=("cand_a",),
            objective_artifact=obj_art,
            candidate_evaluations=(base_rec, base_rec),
            decision_key=k(10),
        )


def test_gate_g2_rejects_empty_eligible_candidates_or_empty_evals() -> None:
    (
        _,
        _,
        _,
        _,
        _,
        _,
        obj_art,
        _,
        _,
    ) = _setup_s9_environment()

    with pytest.raises(
        SelectionBlockedError, match=S9_INELIGIBLE_CANDIDATE_REJECTED
    ):
        run_gate_g2_information_selection(
            decision_id="g2_empty_elig",
            eligible_candidate_ids=(),
            objective_artifact=TypedState.NOT_CONFIGURED,
            candidate_evaluations=(),
            decision_key=k(10),
        )

    with pytest.raises(
        SelectionBlockedError, match=S9_INVALID_CANDIDATE_EVALUATION
    ):
        run_gate_g2_information_selection(
            decision_id="g2_empty_evals",
            eligible_candidate_ids=("cand_a",),
            objective_artifact=obj_art,
            candidate_evaluations=(),
            decision_key=k(10),
        )


def test_gate_g2_decision_post_init_guards() -> None:
    dec = run_gate_g2_information_selection(
        decision_id="g2_not_cfg_01",
        eligible_candidate_ids=("cand_a", "cand_b"),
        objective_artifact=TypedState.NOT_CONFIGURED,
        candidate_evaluations=(),
        decision_key=k(10),
    )
    with pytest.raises(SchemaViolation, match="invalid gate_status"):
        replace(dec, gate_status="BAD_STATUS")
    with pytest.raises(SchemaViolation, match="research_debt_024_status"):
        replace(dec, research_debt_024_status="CLOSED_ILLEGALLY")
    with pytest.raises(IllegalCausalReference):
        replace(
            dec,
            decision_key=k(10, phase=InformationPhase.BAR_PRE_CLOSE),
        )


def test_gate_g2_decision_rejects_winner_when_not_configured() -> None:
    dec = run_gate_g2_information_selection(
        decision_id="g2_not_cfg_01",
        eligible_candidate_ids=("cand_a", "cand_b"),
        objective_artifact=TypedState.NOT_CONFIGURED,
        candidate_evaluations=(),
        decision_key=k(10),
    )
    with pytest.raises(
        SchemaViolation, match="requires selected_winner_candidate_id=TypedState.NOT_CONFIGURED"
    ):
        replace(dec, selected_winner_candidate_id="cand_a")


def test_gate_g2_decision_rejects_winner_when_tied() -> None:
    (
        dep_bundle,
        _,
        _,
        _,
        estimand,
        fv_spec,
        obj_art,
        exp_reg,
        protocol,
    ) = _setup_s9_environment()

    base_rec, _ = evaluate_candidate_information_on_development(
        dep_bundle,
        evaluation_id="eval_base",
        candidate_id="cand_a",
        protocol=protocol,
        estimand=estimand,
        feature_view=fv_spec,
        objective_artifact=obj_art,
        experiment_registry=exp_reg,
    )
    rec_a = _mk_eval_record(
        base_rec, evaluation_id="ev_a", candidate_id="cand_a", score_val=0.75
    )
    rec_b = _mk_eval_record(
        base_rec, evaluation_id="ev_b", candidate_id="cand_b", score_val=0.75
    )
    dec_tie = run_gate_g2_information_selection(
        decision_id="g2_tie_01",
        eligible_candidate_ids=("cand_a", "cand_b"),
        objective_artifact=obj_art,
        candidate_evaluations=(rec_a, rec_b),
        decision_key=k(10),
    )
    with pytest.raises(
        SchemaViolation,
        match="requires selected_winner_candidate_id=TypedState.UNDEFINED",
    ):
        replace(dec_tie, selected_winner_candidate_id="cand_a")


def test_candidate_evaluation_record_post_init_guards() -> None:
    (
        dep_bundle,
        _,
        _,
        _,
        estimand,
        fv_spec,
        obj_art,
        exp_reg,
        protocol,
    ) = _setup_s9_environment()

    base_rec, _ = evaluate_candidate_information_on_development(
        dep_bundle,
        evaluation_id="eval_base",
        candidate_id="cand_a",
        protocol=protocol,
        estimand=estimand,
        feature_view=fv_spec,
        objective_artifact=obj_art,
        experiment_registry=exp_reg,
    )
    with pytest.raises(SchemaViolation, match="must be a non-negative int"):
        replace(base_rec, uncensored_realization_count=-1)
    with pytest.raises(
        SchemaViolation,
        match="cluster_weighted_information_score must be MetricResult or TypedState",
    ):
        replace(base_rec, cluster_weighted_information_score=0.5)  # type: ignore[arg-type]


def test_evaluate_candidate_rejects_invalid_dependence_bundle() -> None:
    (
        _,
        _,
        _,
        _,
        estimand,
        fv_spec,
        obj_art,
        exp_reg,
        protocol,
    ) = _setup_s9_environment()

    with pytest.raises(SchemaViolation, match="DependenceAccountingBundle"):
        evaluate_candidate_information_on_development(
            "invalid",  # type: ignore[arg-type]
            evaluation_id="ev_bad",
            candidate_id="cand_a",
            protocol=protocol,
            estimand=estimand,
            feature_view=fv_spec,
            objective_artifact=obj_art,
            experiment_registry=exp_reg,
        )


def test_s9_realtime_throughput_benchmark() -> None:
    (
        dep_bundle,
        _,
        _,
        _,
        estimand,
        fv_spec,
        obj_art,
        exp_reg,
        protocol,
    ) = _setup_s9_environment()

    t0 = time.perf_counter()
    rec, _ = evaluate_candidate_information_on_development(
        dep_bundle,
        evaluation_id="eval_perf",
        candidate_id="cand_a",
        protocol=protocol,
        estimand=estimand,
        feature_view=fv_spec,
        objective_artifact=obj_art,
        experiment_registry=exp_reg,
    )
    _ = run_gate_g2_information_selection(
        decision_id="g2_perf",
        eligible_candidate_ids=("cand_a",),
        objective_artifact=obj_art,
        candidate_evaluations=(rec,),
        decision_key=k(10),
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert elapsed_ms < 50.0
