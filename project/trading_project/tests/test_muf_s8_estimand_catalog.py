"""MUF V1 S8 & S8.5 Adversarial Test Suite: Estimand Catalog, FeatureViewSpec, and DevelopmentEvaluationProtocol.

Fixture discipline: SYNTHETIC SMALL FIXTURES ONLY (no owner data).
Verifies D1-17, D2-3, D2-4, D2-15, D2-22, AP-1 §2, §3, §4:
- EstimandArtifact & EstimandCatalog (D1-17, I-EST-1, I-SCAT-1..3, I-GSG-4)
- FeatureViewSpec (AP-1 §3.1..3.4, I-FVIEW-1..5)
- DevelopmentEvaluationProtocol & verify_development_protocol_dependency_closure (AP-1 §3.3 & §4.3, I-SG-1A)
- Causal competing-risk & wave continuation outcome realization with explicit right-censoring
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
    build_dependence_accounting_bundle,
)
from trading_system.market_understanding.detector_witness import (
    adapt_detector_witness_stream,
)
from trading_system.market_understanding.estimand_catalog import (
    CENSORING_STATUS_RIGHT_CENSORED,
    CENSORING_STATUS_UNCENSORED,
    DevelopmentEvaluationProtocol,
    EstimandArtifact,
    EstimandCatalog,
    FeatureViewSpec,
    OBSERVABLE_SUBSEQUENT_WAVE_DISPLACEMENT_RATIO,
    OBSERVABLE_SUBSEQUENT_WAVE_EFFICIENCY,
    S8_DUPLICATE_ESTIMAND_REGISTRATION,
    S8_EVALUATION_WITHOUT_PREREGISTERED_ESTIMAND,
    S8_FEATURE_VIEW_UNDECLARED_VARIABLE,
    S8_FINAL_DATASET_FORBIDDEN_IN_DEVELOPMENT_PROTOCOL,
    S8_PROTOCOL_DEPENDENCY_CLOSURE_MISMATCH,
    S8_UNDEFINED_STATE_VARIABLE_IN_ESTIMAND,
    S8_UNKNOWN_ESTIMAND_REF,
    evaluate_development_estimand_realizations,
    verify_development_protocol_dependency_closure,
)
from trading_system.market_understanding.policy_governance import (
    DATASET_ROLE_DEVELOPMENT_FIT,
    DATASET_ROLE_DEVELOPMENT_SELECTION,
    DATASET_ROLE_FINAL_EVALUATION_LOCKED,
    OBJECTIVE_KIND_INFORMATION,
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
S8_MODULE_PATH = (
    PROJECT_ROOT
    / "src"
    / "trading_system"
    / "market_understanding"
    / "estimand_catalog.py"
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
    dataset: str = "DS-DEV-S8",
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


def _setup_s8_environment():
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
        dataset_id="DS-DEV-S8",
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
        owner_authorization_ref="owner-s8-role-1",
    )
    rep_spec = CandidateWaveRepresentationSpec.create(
        representation_id="rep_s8_v1",
        family_kind=FAMILY_ALPHA_POLICY_SCALE,
        scope_timeline_id=TIMELINE,
        scope_axis=InformationAxis.POSITIONAL,
        intrinsic_scale_key="swing_base_q25",
        identity_rule_ref="ORIGIN_ANCHORED_SWING_V1",
    )
    policy_art = PolicyArtifact.create(
        policy_id="pol-s8-01",
        detector_policy_witness_ref=wb.policy_witness_spec.spec_identity,
        scope_timeline_id=TIMELINE,
        scope_axis=InformationAxis.POSITIONAL,
        scope_representation_id="rep_s8_v1",
        calibration_provenance_kind=PROVENANCE_PREDEFINED_CONTRACT,
        reproduction_recipe_hash="recipe-fixed-01",
        effective_from_key=k(1),
        owner_authorization_ref="owner-s8-pol-1",
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
        state_catalog_id="cat_s8_v1",
        variable_specs=(var_eff,),
        descriptor_refs=tuple(s.descriptor_id for s in reg.all_specs()),
        relation_refs=(RELATION_ADJACENT_TO, RELATION_CONTAINS),
    )
    graph_spec = GenericFactualStateGraphSpec.create(
        graph_spec_id="gspec_s8_v1",
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
        contract_id="dep_contract_s8_v1"
    )
    dep_bundle = build_dependence_accounting_bundle(
        sg_bundle, contract=dep_contract
    )
    estimand = EstimandArtifact.create(
        estimand_id="est_s8_01",
        state_catalog=catalog,
        population_variable_refs=("SV_WAVE_EFFICIENCY",),
        conditioning_variable_refs=("SV_WAVE_EFFICIENCY",),
        preregistration_key=k(1),
    )
    fv_spec = FeatureViewSpec.create(
        feature_view_id="fv_s8_01",
        state_catalog=catalog,
        estimand=estimand,
        selected_state_variable_refs=("SV_WAVE_EFFICIENCY",),
    )
    obj_art = ObjectiveArtifact.create(
        objective_id="obj_info_s8",
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
        owner_authorization_ref="owner-s8-obj-1",
    )
    exp_reg = ExperimentRegistry()
    exp_reg.preregister(
        experiment_id="exp_s8_01",
        preregistration_key=k(1),
        representation_spec_hash=rep_spec.representation_spec_hash,
        policy_artifact_hashes=(policy_art.policy_hash,),
        objective_artifact_hash=obj_art.objective_hash,
        dataset_identities_by_role={DATASET_ROLE_DEVELOPMENT_FIT: "DS-DEV-S8"},
        code_hash="code-s8-1",
        fit_protocol_hash="fit-proto-s8",
    )
    protocol = DevelopmentEvaluationProtocol.create(
        protocol_id="dev_proto_s8_01",
        estimand=estimand,
        feature_view=fv_spec,
        state_catalog=catalog,
        graph_spec=graph_spec,
        dependence_contract=dep_contract,
        objective_artifact=obj_art,
        dataset_id="DS-DEV-S8",
        dataset_role=DATASET_ROLE_DEVELOPMENT_FIT,
        experiment_id="exp_s8_01",
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


def test_s8_module_passes_s0_ast_scanners() -> None:
    source = S8_MODULE_PATH.read_text(encoding="utf-8")
    assert scan_private_imports(source) == ()
    assert scan_prohibited_implementations(source) == ()
    assert scan_market_shape_implementations(source) == ()


def test_sealed_s0_to_s7_hashes_untouched() -> None:
    for rel_cert in (
        "docs/releases/MODULE_MUF_V1_S0_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S1_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S2_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S3_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S4_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S5_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S6_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S7_ACCEPTED_SRC_TESTS.sha256",
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


def test_estimand_rejects_undefined_state_variables_ap1_i_scat_1() -> None:
    _, catalog, _, _, estimand, _, _, _, _ = _setup_s8_environment()
    with pytest.raises(
        SchemaViolation, match=S8_UNDEFINED_STATE_VARIABLE_IN_ESTIMAND
    ):
        EstimandArtifact.create(
            estimand_id="est_bad_var",
            state_catalog=catalog,
            population_variable_refs=("SV_UNDEFINED_IN_CATALOG",),
            preregistration_key=k(1),
        )

    with pytest.raises(SchemaViolation, match="estimand_hash mismatch"):
        replace(estimand, estimand_hash="sha256:tampered")


def test_estimand_catalog_append_only_and_lookup() -> None:
    _, catalog, _, _, estimand, _, _, _, _ = _setup_s8_environment()
    est_cat = EstimandCatalog()
    est_cat.register(estimand, state_catalog=catalog)
    assert est_cat.get(estimand.estimand_id) == estimand
    assert len(est_cat.all_estimands()) == 1

    with pytest.raises(
        ImmutabilityViolation, match=S8_DUPLICATE_ESTIMAND_REGISTRATION
    ):
        est_cat.register(estimand, state_catalog=catalog)

    with pytest.raises(SelectionBlockedError, match=S8_UNKNOWN_ESTIMAND_REF):
        est_cat.get("unknown_estimand")


def test_feature_view_spec_validation_and_lineage_ap1_i_fview_1_2() -> None:
    _, catalog, _, _, estimand, fv_spec, _, _, _ = _setup_s8_environment()

    # Referencing undeclared state variable rejected (I-FVIEW-1, I-SCAT-1)
    with pytest.raises(
        SchemaViolation, match=S8_FEATURE_VIEW_UNDECLARED_VARIABLE
    ):
        FeatureViewSpec.create(
            feature_view_id="fv_bad",
            state_catalog=catalog,
            estimand=estimand,
            selected_state_variable_refs=("SV_NOT_IN_CATALOG",),
        )

    # Changing transformation_refs produces new feature_view_hash (I-FVIEW-2)
    fv_alt = FeatureViewSpec.create(
        feature_view_id="fv_s8_01",
        state_catalog=catalog,
        estimand=estimand,
        selected_state_variable_refs=("SV_WAVE_EFFICIENCY",),
        transformation_refs=("CAUSAL_RANK_TRANSFORM_V1",),
    )
    assert fv_spec.feature_view_hash != fv_alt.feature_view_hash

    with pytest.raises(SchemaViolation, match="feature_view_hash mismatch"):
        replace(fv_spec, feature_view_hash="sha256:tampered")


def test_development_evaluation_protocol_dependency_closure_ap1_i_sg_1a() -> None:
    (
        dep_bundle,
        catalog,
        graph_spec,
        dep_contract,
        estimand,
        fv_spec,
        obj_art,
        exp_reg,
        protocol,
    ) = _setup_s8_environment()

    assert verify_development_protocol_dependency_closure(
        protocol,
        estimand=estimand,
        feature_view=fv_spec,
        state_catalog=catalog,
        graph_spec=graph_spec,
        dependence_contract=dep_contract,
        objective_artifact=obj_art,
        experiment_registry=exp_reg,
    )

    # Mismatched feature_view fails closed with S8_PROTOCOL_DEPENDENCY_CLOSURE_MISMATCH (I-SG-1A)
    fv_other = FeatureViewSpec.create(
        feature_view_id="fv_other",
        state_catalog=catalog,
        estimand=estimand,
        selected_state_variable_refs=("SV_WAVE_EFFICIENCY",),
    )
    with pytest.raises(
        SelectionBlockedError, match=S8_PROTOCOL_DEPENDENCY_CLOSURE_MISMATCH
    ):
        verify_development_protocol_dependency_closure(
            protocol,
            estimand=estimand,
            feature_view=fv_other,
            state_catalog=catalog,
            graph_spec=graph_spec,
            dependence_contract=dep_contract,
            objective_artifact=obj_art,
            experiment_registry=exp_reg,
        )


def test_final_evaluation_locked_role_forbidden_in_development_protocol() -> None:
    (
        _,
        catalog,
        graph_spec,
        dep_contract,
        estimand,
        fv_spec,
        obj_art,
        _,
        protocol,
    ) = _setup_s8_environment()

    with pytest.raises(
        SelectionBlockedError,
        match=S8_FINAL_DATASET_FORBIDDEN_IN_DEVELOPMENT_PROTOCOL,
    ):
        DevelopmentEvaluationProtocol.create(
            protocol_id="bad_locked_proto",
            estimand=estimand,
            feature_view=fv_spec,
            state_catalog=catalog,
            graph_spec=graph_spec,
            dependence_contract=dep_contract,
            objective_artifact=obj_art,
            dataset_id="DS-DEV-S8",
            dataset_role=DATASET_ROLE_FINAL_EVALUATION_LOCKED,
            experiment_id="exp_s8_01",
            preregistration_key=k(1),
        )
    with pytest.raises(SchemaViolation, match="protocol_hash mismatch"):
        replace(protocol, protocol_hash="sha256:tampered")


def test_evaluate_development_estimand_realizations_and_right_censoring() -> None:
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
    ) = _setup_s8_environment()

    eval_bundle = evaluate_development_estimand_realizations(
        dep_bundle,
        protocol=protocol,
        estimand=estimand,
        feature_view=fv_spec,
        objective_artifact=obj_art,
        experiment_registry=exp_reg,
    )
    total_geoms = len(
        dep_bundle.state_graph_bundle.wave_bundle.finalized_wave_geometries
    )
    assert len(eval_bundle.realizations) == total_geoms
    assert eval_bundle.right_censored_count == 1
    assert eval_bundle.uncensored_count == total_geoms - 1

    # Last confirmed wave has no subsequent confirmed wave in dataset -> explicitly RIGHT_CENSORED
    last_real = eval_bundle.realizations[-1]
    assert last_real.censoring_status == CENSORING_STATUS_RIGHT_CENSORED
    assert last_real.outcome_value is TypedState.UNAVAILABLE

    if eval_bundle.uncensored_count >= 1:
        first_real = eval_bundle.realizations[0]
        assert first_real.censoring_status == CENSORING_STATUS_UNCENSORED
        assert isinstance(first_real.outcome_value, MetricResult)


def test_evaluation_without_preregistered_estimand_or_feature_view_blocked() -> None:
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
    ) = _setup_s8_environment()

    with pytest.raises(
        SelectionBlockedError,
        match=S8_EVALUATION_WITHOUT_PREREGISTERED_ESTIMAND,
    ):
        evaluate_development_estimand_realizations(
            dep_bundle,
            protocol=protocol,
            estimand=TypedState.NOT_CONFIGURED,
            feature_view=fv_spec,
            objective_artifact=obj_art,
            experiment_registry=exp_reg,
        )

    with pytest.raises(SelectionBlockedError, match="FeatureViewSpec required"):
        evaluate_development_estimand_realizations(
            dep_bundle,
            protocol=protocol,
            estimand=estimand,
            feature_view=TypedState.NOT_CONFIGURED,
            objective_artifact=obj_art,
            experiment_registry=exp_reg,
        )


def test_subsequent_wave_efficiency_observable_realization() -> None:
    (
        dep_bundle,
        catalog,
        graph_spec,
        dep_contract,
        _,
        _,
        obj_art,
        exp_reg,
        _,
    ) = _setup_s8_environment()

    est_eff = EstimandArtifact.create(
        estimand_id="est_eff_01",
        state_catalog=catalog,
        population_variable_refs=("SV_WAVE_EFFICIENCY",),
        future_observable_kind=OBSERVABLE_SUBSEQUENT_WAVE_EFFICIENCY,
        preregistration_key=k(1),
    )
    fv_eff = FeatureViewSpec.create(
        feature_view_id="fv_eff_01",
        state_catalog=catalog,
        estimand=est_eff,
        selected_state_variable_refs=("SV_WAVE_EFFICIENCY",),
    )
    proto_eff = DevelopmentEvaluationProtocol.create(
        protocol_id="proto_eff_01",
        estimand=est_eff,
        feature_view=fv_eff,
        state_catalog=catalog,
        graph_spec=graph_spec,
        dependence_contract=dep_contract,
        objective_artifact=obj_art,
        dataset_id="DS-DEV-S8",
        dataset_role=DATASET_ROLE_DEVELOPMENT_FIT,
        experiment_id="exp_s8_01",
        preregistration_key=k(1),
    )
    res = evaluate_development_estimand_realizations(
        dep_bundle,
        protocol=proto_eff,
        estimand=est_eff,
        feature_view=fv_eff,
        objective_artifact=obj_art,
        experiment_registry=exp_reg,
    )
    assert len(res.realizations) >= 1


def test_estimand_artifact_post_init_guards() -> None:
    _, catalog, _, _, estimand, _, _, _, _ = _setup_s8_environment()
    with pytest.raises(SchemaViolation, match="population_variable_refs"):
        EstimandArtifact.create(
            estimand_id="est_empty_pop",
            state_catalog=catalog,
            population_variable_refs=(),
            preregistration_key=k(1),
        )
    with pytest.raises(SchemaViolation, match="invalid future_observable_kind"):
        EstimandArtifact.create(
            estimand_id="est_bad_obs",
            state_catalog=catalog,
            population_variable_refs=("SV_WAVE_EFFICIENCY",),
            future_observable_kind="UNSUPPORTED_OBSERVABLE",
            preregistration_key=k(1),
        )
    with pytest.raises(IllegalCausalReference):
        EstimandArtifact.create(
            estimand_id="est_pre_close",
            state_catalog=catalog,
            population_variable_refs=("SV_WAVE_EFFICIENCY",),
            preregistration_key=k(1, phase=InformationPhase.BAR_PRE_CLOSE),
        )


def test_estimand_catalog_rejects_mismatched_catalog() -> None:
    _, catalog, _, _, estimand, _, _, _, _ = _setup_s8_environment()
    other_var = StateVariableSpec.create(
        variable_id="SV_WAVE_EFFICIENCY",
        semantic_definition="Different definition",
        value_domain_kind="REAL",
        source_descriptor_refs=("FINAL_EFFICIENCY_RATIO",),
    )
    other_cat = StateCatalogArtifact.create(
        state_catalog_id="cat_other",
        variable_specs=(other_var,),
        descriptor_refs=("FINAL_EFFICIENCY_RATIO",),
        relation_refs=(),
    )
    est_cat = EstimandCatalog()
    with pytest.raises(
        SchemaViolation, match=S8_UNDEFINED_STATE_VARIABLE_IN_ESTIMAND
    ):
        est_cat.register(estimand, state_catalog=other_cat)


def test_feature_view_rejects_mismatched_catalog_or_empty_vars() -> None:
    _, catalog, _, _, estimand, _, _, _, _ = _setup_s8_environment()
    with pytest.raises(SchemaViolation, match="selected_state_variable_refs"):
        FeatureViewSpec.create(
            feature_view_id="fv_empty",
            state_catalog=catalog,
            estimand=estimand,
            selected_state_variable_refs=(),
        )


def test_protocol_creation_rejects_mismatched_hashes() -> None:
    (
        _,
        catalog,
        graph_spec,
        dep_contract,
        estimand,
        _,
        obj_art,
        _,
        _,
    ) = _setup_s8_environment()
    other_est = EstimandArtifact.create(
        estimand_id="est_other",
        state_catalog=catalog,
        population_variable_refs=("SV_WAVE_EFFICIENCY",),
        preregistration_key=k(1),
    )
    fv_other = FeatureViewSpec.create(
        feature_view_id="fv_for_other",
        state_catalog=catalog,
        estimand=other_est,
        selected_state_variable_refs=("SV_WAVE_EFFICIENCY",),
    )
    with pytest.raises(
        SchemaViolation, match=S8_PROTOCOL_DEPENDENCY_CLOSURE_MISMATCH
    ):
        DevelopmentEvaluationProtocol.create(
            protocol_id="bad_proto_mismatch",
            estimand=estimand,
            feature_view=fv_other,
            state_catalog=catalog,
            graph_spec=graph_spec,
            dependence_contract=dep_contract,
            objective_artifact=obj_art,
            dataset_id="DS-DEV-S8",
            dataset_role=DATASET_ROLE_DEVELOPMENT_FIT,
            experiment_id="exp_s8_01",
            preregistration_key=k(1),
        )


def test_protocol_dataset_mismatch_in_evaluation_blocked() -> None:
    (
        dep_bundle,
        catalog,
        graph_spec,
        dep_contract,
        estimand,
        fv_spec,
        obj_art,
        exp_reg,
        _,
    ) = _setup_s8_environment()
    proto_wrong_ds = DevelopmentEvaluationProtocol.create(
        protocol_id="proto_wrong_ds",
        estimand=estimand,
        feature_view=fv_spec,
        state_catalog=catalog,
        graph_spec=graph_spec,
        dependence_contract=dep_contract,
        objective_artifact=obj_art,
        dataset_id="WRONG_DATASET_ID",
        dataset_role=DATASET_ROLE_DEVELOPMENT_FIT,
        experiment_id="exp_s8_01",
        preregistration_key=k(1),
    )
    with pytest.raises(
        SelectionBlockedError, match=S8_PROTOCOL_DEPENDENCY_CLOSURE_MISMATCH
    ):
        evaluate_development_estimand_realizations(
            dep_bundle,
            protocol=proto_wrong_ds,
            estimand=estimand,
            feature_view=fv_spec,
            objective_artifact=obj_art,
            experiment_registry=exp_reg,
        )


def test_protocol_unpermitted_dataset_role_blocked() -> None:
    (
        dep_bundle,
        catalog,
        graph_spec,
        dep_contract,
        _,
        _,
        obj_art,
        exp_reg,
        _,
    ) = _setup_s8_environment()
    est_sel_only = EstimandArtifact.create(
        estimand_id="est_sel_only",
        state_catalog=catalog,
        population_variable_refs=("SV_WAVE_EFFICIENCY",),
        permitted_dataset_roles=(DATASET_ROLE_DEVELOPMENT_SELECTION,),
        preregistration_key=k(1),
    )
    fv_sel = FeatureViewSpec.create(
        feature_view_id="fv_sel",
        state_catalog=catalog,
        estimand=est_sel_only,
        selected_state_variable_refs=("SV_WAVE_EFFICIENCY",),
    )
    proto_fit = DevelopmentEvaluationProtocol.create(
        protocol_id="proto_fit_on_sel_est",
        estimand=est_sel_only,
        feature_view=fv_sel,
        state_catalog=catalog,
        graph_spec=graph_spec,
        dependence_contract=dep_contract,
        objective_artifact=obj_art,
        dataset_id="DS-DEV-S8",
        dataset_role=DATASET_ROLE_DEVELOPMENT_FIT,
        experiment_id="exp_s8_01",
        preregistration_key=k(1),
    )
    with pytest.raises(
        SelectionBlockedError,
        match=S8_FINAL_DATASET_FORBIDDEN_IN_DEVELOPMENT_PROTOCOL,
    ):
        evaluate_development_estimand_realizations(
            dep_bundle,
            protocol=proto_fit,
            estimand=est_sel_only,
            feature_view=fv_sel,
            objective_artifact=obj_art,
            experiment_registry=exp_reg,
        )


def test_estimand_does_not_mutate_generic_state_graph_or_catalog_i_gsg_4() -> None:
    (
        dep_bundle,
        catalog,
        graph_spec,
        _,
        estimand,
        fv_spec,
        obj_art,
        exp_reg,
        protocol,
    ) = _setup_s8_environment()
    cat_hash_before = catalog.state_catalog_hash
    gs_hash_before = graph_spec.graph_spec_hash
    _ = evaluate_development_estimand_realizations(
        dep_bundle,
        protocol=protocol,
        estimand=estimand,
        feature_view=fv_spec,
        objective_artifact=obj_art,
        experiment_registry=exp_reg,
    )
    assert catalog.state_catalog_hash == cat_hash_before
    assert graph_spec.graph_spec_hash == gs_hash_before


def test_verify_protocol_rejects_non_protocol_object() -> None:
    (
        _,
        catalog,
        graph_spec,
        dep_contract,
        estimand,
        fv_spec,
        obj_art,
        exp_reg,
        _,
    ) = _setup_s8_environment()
    with pytest.raises(
        SelectionBlockedError,
        match=S8_EVALUATION_WITHOUT_PREREGISTERED_ESTIMAND,
    ):
        verify_development_protocol_dependency_closure(
            "not_a_protocol",  # type: ignore[arg-type]
            estimand=estimand,
            feature_view=fv_spec,
            state_catalog=catalog,
            graph_spec=graph_spec,
            dependence_contract=dep_contract,
            objective_artifact=obj_art,
            experiment_registry=exp_reg,
        )


def test_evaluate_realizations_rejects_invalid_dependence_bundle() -> None:
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
    ) = _setup_s8_environment()
    with pytest.raises(SchemaViolation, match="DependenceAccountingBundle"):
        evaluate_development_estimand_realizations(
            "invalid",  # type: ignore[arg-type]
            protocol=protocol,
            estimand=estimand,
            feature_view=fv_spec,
            objective_artifact=obj_art,
            experiment_registry=exp_reg,
        )


def test_s8_realtime_throughput_benchmark() -> None:
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
    ) = _setup_s8_environment()
    t0 = time.perf_counter()
    _ = evaluate_development_estimand_realizations(
        dep_bundle,
        protocol=protocol,
        estimand=estimand,
        feature_view=fv_spec,
        objective_artifact=obj_art,
        experiment_registry=exp_reg,
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert elapsed_ms < 50.0
