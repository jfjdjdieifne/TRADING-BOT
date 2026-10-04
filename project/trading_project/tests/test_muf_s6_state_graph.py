"""MUF V1 S6 Adversarial Test Suite: Descriptor Registry, StateCatalogArtifact, and GenericFactualStateGraphSpec.

Fixture discipline: SYNTHETIC SMALL FIXTURES ONLY (no owner data).
Verifies D1-6..13, D2-8, D2-9, D2-10, D2-16, D2-22, Correction-1 §4, AP-1 §1, §2, §4:
- DescriptorSpec & DescriptorRegistry (D2-16, I-DESC-1..3, I-DE-1)
- StateVariableSpec & StateCatalogArtifact preceding any Estimand (AP-1 §2, I-SCAT-1..3)
- GenericFactualStateGraphSpec (AP-1 §1, I-GSG-1..4)
- Adjacency != Alternatives & batch chronology for ADJACENT_TO (D2-9, I-DELTA-1..4)
- Cycle-safe deterministic snapshot closure (D2-8, I-CLOS-1..3)
- Scale != Depth on FactualStateGraphNodeRecord (D1-6, I-SD-1..4)
- Causal scale-invariant wave descriptors & as-of state graph projection
"""
from dataclasses import replace
import hashlib
from pathlib import Path
import time

import pytest

from trading_system.market_understanding.availability import (
    BatchRelation,
    InformationAxis,
)
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
from trading_system.market_understanding.detector_witness import (
    adapt_detector_witness_stream,
)
from trading_system.market_understanding.policy_governance import (
    DATASET_ROLE_DEVELOPMENT_FIT,
    PROVENANCE_PREDEFINED_CONTRACT,
    DatasetIdentityArtifact,
    DatasetRoleArtifact,
    PolicyArtifact,
    SelectionBlockedError,
)
from trading_system.market_understanding.price_path import (
    EXACT,
    MetricResult,
    PublishedOhlcBarFact,
    exact_metric,
)
from trading_system.market_understanding.state_graph import (
    CausalDescriptorObservationRecord,
    CycleSafeGraphClosureRecord,
    DELTA_CONTAINMENT_HIERARCHY_STANDING_STATUS,
    DESCRIPTOR_STAGE_BOTH_SEPARATE_FORMULAE,
    DESCRIPTOR_STAGE_FINAL_ONLY,
    DESCRIPTOR_STAGE_RUNNING_ONLY,
    DescriptorRegistry,
    DescriptorSpec,
    FactualStateGraphNodeRecord,
    GenericFactualStateGraphSpec,
    RELATION_ADJACENT_TO,
    RELATION_ALTERNATES_WITH,
    RELATION_CONTAINS,
    RELATION_GENERAL_REFERENCE,
    S6_ALTERNATES_WITH_NOT_ADJACENCY,
    S6_DELTA_POPULATED_HIERARCHY_NOT_CONFIGURED,
    S6_DUPLICATE_DESCRIPTOR_REGISTRATION,
    S6_ESTIMAND_OR_OBJECTIVE_FORBIDDEN_IN_GENERIC_STATE_GRAPH,
    S6_FUTURE_FACT_IN_RUNNING_DESCRIPTOR,
    S6_ILLEGAL_WAVE_CONTAINMENT_CYCLE,
    S6_SCALE_DEPTH_COLLAPSE_FORBIDDEN,
    S6_SEPARATE_FORMULAE_REQUIRED,
    S6_UNDECLARED_CATALOG_REFERENCE,
    S6_UNKNOWN_DESCRIPTOR_REF,
    S6_UNPROVEN_CHRONOLOGY_FOR_ADJACENT_TO,
    StateCatalogArtifact,
    StateVariableSpec,
    WaveRelationRecord,
    build_generic_factual_state_graph,
    compute_cycle_safe_graph_closure,
    create_standard_wave_descriptor_registry,
    query_state_graph_as_of,
)
from trading_system.market_understanding.wave_representation import (
    CandidateWaveRepresentationSpec,
    FAMILY_ALPHA_POLICY_SCALE,
    FAMILY_DELTA_EVENT_CONTAINMENT,
    construct_candidate_wave_representation,
)
from trading_system.research.information_time import (
    INFORMATION_KEY_VERSION,
    InformationKey,
    InformationPhase,
)
from trading_system.structure.swing_detector import EmpiricalConfirmationPolicy


PROJECT_ROOT = Path(__file__).resolve().parents[1]
S6_MODULE_PATH = (
    PROJECT_ROOT
    / "src"
    / "trading_system"
    / "market_understanding"
    / "state_graph.py"
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
    dataset: str = "DS-DEV-S6",
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


def _setup_s6_environment(family: str = FAMILY_ALPHA_POLICY_SCALE):
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
        dataset_id="DS-DEV-S6",
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
        owner_authorization_ref="owner-s6-role-1",
    )
    rep_id = "rep_s6_v1"
    scale_key = (
        "swing_base_q25"
        if family == FAMILY_ALPHA_POLICY_SCALE
        else TypedState.NOT_APPLICABLE
    )
    rep_spec = CandidateWaveRepresentationSpec.create(
        representation_id=rep_id,
        family_kind=family,
        scope_timeline_id=TIMELINE,
        scope_axis=InformationAxis.POSITIONAL,
        intrinsic_scale_key=scale_key,
        identity_rule_ref="ORIGIN_ANCHORED_SWING_V1",
    )
    policy_art = PolicyArtifact.create(
        policy_id="pol-s6-01",
        detector_policy_witness_ref=wb.policy_witness_spec.spec_identity,
        scope_timeline_id=TIMELINE,
        scope_axis=InformationAxis.POSITIONAL,
        scope_representation_id=rep_id,
        calibration_provenance_kind=PROVENANCE_PREDEFINED_CONTRACT,
        reproduction_recipe_hash="recipe-fixed-01",
        effective_from_key=k(1),
        owner_authorization_ref="owner-s6-pol-1",
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
        state_catalog_id="cat_s6_v1",
        variable_specs=(var_eff,),
        descriptor_refs=tuple(s.descriptor_id for s in reg.all_specs()),
        relation_refs=(RELATION_ADJACENT_TO, RELATION_CONTAINS),
    )
    graph_spec = GenericFactualStateGraphSpec.create(
        graph_spec_id="gspec_s6_v1",
        state_catalog=catalog,
        source_contract_hashes=("SRC_BINANCE_V1",),
        representation_contract_hashes=(rep_spec.representation_spec_hash,),
        descriptor_contract_hashes=tuple(
            s.descriptor_hash for s in reg.all_specs()
        ),
        relation_contract_hashes=("REL_ADJACENT_V1", "REL_CONTAINS_V1"),
    )
    return wave_bundle, reg, catalog, graph_spec


def test_s6_module_passes_s0_ast_scanners() -> None:
    source = S6_MODULE_PATH.read_text(encoding="utf-8")
    assert scan_private_imports(source) == ()
    assert scan_prohibited_implementations(source) == ()
    assert scan_market_shape_implementations(source) == ()


def test_sealed_s0_to_s5_hashes_untouched() -> None:
    for rel_cert in (
        "docs/releases/MODULE_MUF_V1_S0_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S1_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S2_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S3_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S4_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S5_ACCEPTED_SRC_TESTS.sha256",
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


def test_descriptor_spec_running_vs_final_and_separate_formulae_d2_16() -> None:
    # RUNNING_ONLY rejects end/final wave facts (I-DESC-1..2)
    with pytest.raises(
        IllegalCausalReference, match=S6_FUTURE_FACT_IN_RUNNING_DESCRIPTOR
    ):
        DescriptorSpec.create(
            descriptor_id="BAD_RUNNING_DESC",
            semantic_definition="Leaks final duration into running wave",
            stage=DESCRIPTOR_STAGE_RUNNING_ONLY,
            required_input_refs=("running_displacement", "final_bar_count"),
            availability_rule_ref="RULE_V1",
            running_formula_hash="F_RUN_1",
        )

    # BOTH_SEPARATE_FORMULAE requires distinct running and final formula hashes (D2-16)
    with pytest.raises(SchemaViolation, match=S6_SEPARATE_FORMULAE_REQUIRED):
        DescriptorSpec.create(
            descriptor_id="BAD_BOTH_DESC",
            semantic_definition="Collapsed formula hash across running and final",
            stage=DESCRIPTOR_STAGE_BOTH_SEPARATE_FORMULAE,
            required_input_refs=("displacement",),
            availability_rule_ref="RULE_V1",
            running_formula_hash="SAME_HASH",
            final_formula_hash="SAME_HASH",
        )

    both_ok = DescriptorSpec.create(
        descriptor_id="OK_BOTH_DESC",
        semantic_definition="Separate formulae for running and final",
        stage=DESCRIPTOR_STAGE_BOTH_SEPARATE_FORMULAE,
        required_input_refs=("displacement",),
        availability_rule_ref="RULE_V1",
        running_formula_hash="HASH_RUN_V1",
        final_formula_hash="HASH_FINAL_V1",
    )
    assert both_ok.running_formula_hash != both_ok.final_formula_hash
    with pytest.raises(SchemaViolation, match="descriptor_hash mismatch"):
        replace(both_ok, descriptor_hash="sha256:tampered")


def test_descriptor_registry_append_only_and_lookup() -> None:
    reg = create_standard_wave_descriptor_registry()
    spec = reg.get("RUNNING_EFFICIENCY_RATIO")
    assert spec.descriptor_id == "RUNNING_EFFICIENCY_RATIO"

    with pytest.raises(
        ImmutabilityViolation, match=S6_DUPLICATE_DESCRIPTOR_REGISTRATION
    ):
        reg.register(spec)

    with pytest.raises(SchemaViolation, match=S6_UNKNOWN_DESCRIPTOR_REF):
        reg.get("NON_EXISTENT_DESCRIPTOR")


def test_estimand_and_objective_tokens_rejected_in_generic_specs_ap1_i_gsg_2() -> None:
    with pytest.raises(
        SchemaViolation,
        match=S6_ESTIMAND_OR_OBJECTIVE_FORBIDDEN_IN_GENERIC_STATE_GRAPH,
    ):
        DescriptorSpec.create(
            descriptor_id="DESC_FOR_ESTIMAND_1",
            semantic_definition="Tailored to estimand",
            stage=DESCRIPTOR_STAGE_FINAL_ONLY,
            required_input_refs=("final_displacement",),
            availability_rule_ref="RULE_V1",
            final_formula_hash="F_1",
        )

    with pytest.raises(
        SchemaViolation,
        match=S6_ESTIMAND_OR_OBJECTIVE_FORBIDDEN_IN_GENERIC_STATE_GRAPH,
    ):
        StateVariableSpec.create(
            variable_id="SV_FUTURE_OBSERVABLE",
            semantic_definition="Leaks future_observable",
            value_domain_kind="REAL",
            source_descriptor_refs=("FINAL_EFFICIENCY_RATIO",),
        )


def test_state_variable_spec_and_state_catalog_artifact_i_scat_1_3() -> None:
    v1 = StateVariableSpec.create(
        variable_id="SV_1",
        semantic_definition="Wave efficiency variable",
        value_domain_kind="BOUNDED_0_1",
        source_descriptor_refs=("FINAL_EFFICIENCY_RATIO",),
    )
    # Referencing an undeclared descriptor_ref in StateCatalogArtifact fails closed (I-SCAT-1)
    with pytest.raises(SchemaViolation, match=S6_UNDECLARED_CATALOG_REFERENCE):
        StateCatalogArtifact.create(
            state_catalog_id="cat_bad",
            variable_specs=(v1,),
            descriptor_refs=("OTHER_DESC",),
            relation_refs=(),
        )

    cat1 = StateCatalogArtifact.create(
        state_catalog_id="cat_ok",
        variable_specs=(v1,),
        descriptor_refs=("FINAL_EFFICIENCY_RATIO",),
        relation_refs=(),
    )
    v2 = StateVariableSpec.create(
        variable_id="SV_1",
        semantic_definition="Modified semantic definition of SV_1",
        value_domain_kind="BOUNDED_0_1",
        source_descriptor_refs=("FINAL_EFFICIENCY_RATIO",),
    )
    cat2 = StateCatalogArtifact.create(
        state_catalog_id="cat_ok",
        variable_specs=(v2,),
        descriptor_refs=("FINAL_EFFICIENCY_RATIO",),
        relation_refs=(),
    )
    # I-SCAT-3: semantic change in variable spec produces new state_catalog_hash
    assert cat1.state_catalog_hash != cat2.state_catalog_hash
    with pytest.raises(SchemaViolation, match="state_catalog_hash mismatch"):
        replace(cat1, state_catalog_hash="sha256:tampered")


def test_generic_factual_state_graph_spec_validation_i_gsg_1_4() -> None:
    _, _, catalog, graph_spec = _setup_s6_environment()
    with pytest.raises(SchemaViolation, match="graph_spec_hash mismatch"):
        replace(graph_spec, graph_spec_hash="sha256:tampered")

    with pytest.raises(
        SchemaViolation,
        match="representation and descriptor contract hashes must be non-empty",
    ):
        GenericFactualStateGraphSpec.create(
            graph_spec_id="bad_gs",
            state_catalog=catalog,
            source_contract_hashes=("SRC_1",),
            representation_contract_hashes=(),
            descriptor_contract_hashes=("DESC_1",),
            relation_contract_hashes=(),
        )


def test_scale_vs_depth_separation_on_graph_node_i_sd_1() -> None:
    node = FactualStateGraphNodeRecord(
        node_id="wp_1",
        timeline_id=TIMELINE,
        node_availability_key=k(3),
        intrinsic_scale_key="swing_q25",
        containment_depth=TypedState.NOT_APPLICABLE,
    )
    assert node.intrinsic_scale_key == "swing_q25"
    assert node.containment_depth is TypedState.NOT_APPLICABLE

    with pytest.raises(
        SchemaViolation, match=S6_SCALE_DEPTH_COLLAPSE_FORBIDDEN
    ):
        FactualStateGraphNodeRecord(
            node_id="wp_bad",
            timeline_id=TIMELINE,
            node_availability_key=k(3),
            intrinsic_scale_key="swing_q25",
            containment_depth=-1,
        )


def test_wave_relation_adjacency_not_alternatives_and_batch_chronology_d2_9() -> None:
    # I-DELTA-1: ALTERNATES_WITH cannot be used as adjacency or parent containment
    with pytest.raises(
        SchemaViolation, match=S6_ALTERNATES_WITH_NOT_ADJACENCY
    ):
        WaveRelationRecord.create(
            relation_type=RELATION_ALTERNATES_WITH,
            source_wave_process_id="wp_a",
            target_wave_process_id="wp_b",
            timeline_id=TIMELINE,
            source_availability_key=k(2),
            target_availability_key=k(4),
            batch_relation=BatchRelation.DIFFERENT_BATCH,
            used_for_adjacency_or_parent=True,
        )

    # I-DELTA-2: ADJACENT_TO requires DIFFERENT_BATCH (rejects KNOWN_SAME_BATCH / UNKNOWN_IF_SAME_BATCH)
    with pytest.raises(
        SchemaViolation, match=S6_UNPROVEN_CHRONOLOGY_FOR_ADJACENT_TO
    ):
        WaveRelationRecord.create(
            relation_type=RELATION_ADJACENT_TO,
            source_wave_process_id="wp_a",
            target_wave_process_id="wp_b",
            timeline_id=TIMELINE,
            source_availability_key=k(2),
            target_availability_key=k(2),
            batch_relation=BatchRelation.KNOWN_SAME_BATCH,
            used_for_adjacency_or_parent=True,
        )


def test_cycle_safe_graph_closure_contains_vs_general_reference_d2_8() -> None:
    n_a = FactualStateGraphNodeRecord(
        node_id="node_A",
        timeline_id=TIMELINE,
        node_availability_key=k(2),
        intrinsic_scale_key="s1",
        containment_depth=0,
    )
    n_b = FactualStateGraphNodeRecord(
        node_id="node_B",
        timeline_id=TIMELINE,
        node_availability_key=k(3),
        intrinsic_scale_key="s1",
        containment_depth=1,
    )

    # 1. CONTAINS cycle A -> B -> A is rejected with S6_ILLEGAL_WAVE_CONTAINMENT_CYCLE (D2-8)
    c_ab = WaveRelationRecord.create(
        relation_type=RELATION_CONTAINS,
        source_wave_process_id="node_A",
        target_wave_process_id="node_B",
        timeline_id=TIMELINE,
        source_availability_key=k(2),
        target_availability_key=k(3),
    )
    c_ba = WaveRelationRecord.create(
        relation_type=RELATION_CONTAINS,
        source_wave_process_id="node_B",
        target_wave_process_id="node_A",
        timeline_id=TIMELINE,
        source_availability_key=k(3),
        target_availability_key=k(2),
    )
    with pytest.raises(
        SchemaViolation, match=S6_ILLEGAL_WAVE_CONTAINMENT_CYCLE
    ):
        compute_cycle_safe_graph_closure(
            (n_a, n_b),
            (c_ab, c_ba),
            seed_node_ids=("node_A",),
            at_key=k(5),
        )

    # 2. GENERAL_REFERENCE cycle A -> B -> A is traversed deterministically once without infinite recursion (I-CLOS-1..3)
    g_ab = WaveRelationRecord.create(
        relation_type=RELATION_GENERAL_REFERENCE,
        source_wave_process_id="node_A",
        target_wave_process_id="node_B",
        timeline_id=TIMELINE,
        source_availability_key=k(2),
        target_availability_key=k(3),
    )
    g_ba = WaveRelationRecord.create(
        relation_type=RELATION_GENERAL_REFERENCE,
        source_wave_process_id="node_B",
        target_wave_process_id="node_A",
        timeline_id=TIMELINE,
        source_availability_key=k(3),
        target_availability_key=k(2),
    )
    cl_1 = compute_cycle_safe_graph_closure(
        (n_a, n_b),
        (g_ab, g_ba),
        seed_node_ids=("node_A", "node_B"),
        at_key=k(5),
    )
    cl_2 = compute_cycle_safe_graph_closure(
        (n_b, n_a),
        (g_ba, g_ab),
        seed_node_ids=("node_B", "node_A"),
        at_key=k(5),
    )
    assert cl_1.general_reference_cycle_detected is True
    assert cl_1.closure_hash == cl_2.closure_hash

    # 3. I-CLOS-2: cycle does not bypass availability check when at_key < node_B availability
    with pytest.raises(IllegalCausalReference):
        compute_cycle_safe_graph_closure(
            (n_a, n_b),
            (g_ab, g_ba),
            seed_node_ids=("node_A",),
            at_key=k(2),
        )


def test_delta_containment_hierarchy_contract_only_standing_status_i_delta_4() -> None:
    wave_bundle, reg, catalog, graph_spec = _setup_s6_environment(
        family=FAMILY_DELTA_EVENT_CONTAINMENT
    )
    with pytest.raises(
        SelectionBlockedError,
        match=S6_DELTA_POPULATED_HIERARCHY_NOT_CONFIGURED,
    ):
        build_generic_factual_state_graph(
            wave_bundle,
            descriptor_registry=reg,
            state_catalog=catalog,
            graph_spec=graph_spec,
            request_populated_delta_hierarchy=True,
        )

    bundle = build_generic_factual_state_graph(
        wave_bundle,
        descriptor_registry=reg,
        state_catalog=catalog,
        graph_spec=graph_spec,
        request_populated_delta_hierarchy=False,
    )
    assert (
        bundle.delta_hierarchy_standing_status
        == DELTA_CONTAINMENT_HIERARCHY_STANDING_STATUS
    )


def test_end_to_end_build_generic_factual_state_graph_and_causal_descriptors() -> None:
    wave_bundle, reg, catalog, graph_spec = _setup_s6_environment()
    bundle = build_generic_factual_state_graph(
        wave_bundle,
        descriptor_registry=reg,
        state_catalog=catalog,
        graph_spec=graph_spec,
    )
    assert len(bundle.nodes) == len(wave_bundle.wave_identity_records)
    assert len(bundle.relations) >= 1
    assert len(bundle.descriptor_observations) >= 4
    assert len(bundle.state_observations) == len(
        wave_bundle.finalized_wave_geometries
    )


def test_query_state_graph_as_of_and_causal_visibility() -> None:
    wave_bundle, reg, catalog, graph_spec = _setup_s6_environment()
    bundle = build_generic_factual_state_graph(
        wave_bundle,
        descriptor_registry=reg,
        state_catalog=catalog,
        graph_spec=graph_spec,
    )
    view = query_state_graph_as_of(
        bundle, at_key=wave_bundle.observation_keys[-1]
    )
    assert len(view.visible_nodes) == len(bundle.nodes)
    assert len(view.closure_record.reachable_node_ids) == len(bundle.nodes)

    with pytest.raises(IllegalCausalReference):
        query_state_graph_as_of(
            bundle, at_key=k(2, phase=InformationPhase.BAR_PRE_CLOSE)
        )
    with pytest.raises(InformationKeyViolation):
        query_state_graph_as_of(bundle, at_key=k(2, timeline="OTHER_TL"))
    with pytest.raises(PrematureAvailability):
        query_state_graph_as_of(bundle, at_key=k(99))


def test_state_graph_mismatched_catalog_hash_rejected() -> None:
    wave_bundle, reg, catalog, graph_spec = _setup_s6_environment()
    other_var = StateVariableSpec.create(
        variable_id="SV_OTHER",
        semantic_definition="Other state variable",
        value_domain_kind="REAL",
        source_descriptor_refs=("FINAL_EFFICIENCY_RATIO",),
    )
    other_cat = StateCatalogArtifact.create(
        state_catalog_id="cat_other",
        variable_specs=(other_var,),
        descriptor_refs=("FINAL_EFFICIENCY_RATIO",),
        relation_refs=(),
    )
    with pytest.raises(
        SchemaViolation,
        match="graph_spec.state_catalog_hash != state_catalog.state_catalog_hash",
    ):
        build_generic_factual_state_graph(
            wave_bundle,
            descriptor_registry=reg,
            state_catalog=other_cat,
            graph_spec=graph_spec,
        )


def test_wave_relation_record_tamper_guards() -> None:
    rel = WaveRelationRecord.create(
        relation_type=RELATION_ADJACENT_TO,
        source_wave_process_id="wp_1",
        target_wave_process_id="wp_2",
        timeline_id=TIMELINE,
        source_availability_key=k(2),
        target_availability_key=k(4),
    )
    with pytest.raises(SchemaViolation, match="relation_id mismatch"):
        replace(rel, relation_id="rel_tampered")
    with pytest.raises(SchemaViolation, match="invalid relation_type"):
        replace(rel, relation_type="INVALID_REL")


def test_closure_record_tamper_guards() -> None:
    wave_bundle, reg, catalog, graph_spec = _setup_s6_environment()
    bundle = build_generic_factual_state_graph(
        wave_bundle,
        descriptor_registry=reg,
        state_catalog=catalog,
        graph_spec=graph_spec,
    )
    view = query_state_graph_as_of(
        bundle, at_key=wave_bundle.observation_keys[-1]
    )
    with pytest.raises(SchemaViolation, match="closure_hash mismatch"):
        replace(view.closure_record, closure_hash="sha256:tampered")


def test_descriptor_observation_record_tamper_guards() -> None:
    wave_bundle, reg, catalog, graph_spec = _setup_s6_environment()
    bundle = build_generic_factual_state_graph(
        wave_bundle,
        descriptor_registry=reg,
        state_catalog=catalog,
        graph_spec=graph_spec,
    )
    dobs = bundle.descriptor_observations[0]
    with pytest.raises(SchemaViolation, match="observation stage"):
        replace(dobs, stage=DESCRIPTOR_STAGE_BOTH_SEPARATE_FORMULAE)
    with pytest.raises(IllegalCausalReference):
        replace(
            dobs, observation_key=k(2, phase=InformationPhase.BAR_PRE_CLOSE)
        )


def test_state_variable_spec_empty_sources_and_tamper_guards() -> None:
    with pytest.raises(
        SchemaViolation,
        match="require at least one source_descriptor_ref or source_relation_ref",
    ):
        StateVariableSpec.create(
            variable_id="SV_EMPTY",
            semantic_definition="No sources",
            value_domain_kind="REAL",
            source_descriptor_refs=(),
            source_relation_refs=(),
        )
    sv = StateVariableSpec.create(
        variable_id="SV_OK",
        semantic_definition="Valid source",
        value_domain_kind="REAL",
        source_descriptor_refs=("FINAL_EFFICIENCY_RATIO",),
    )
    with pytest.raises(SchemaViolation, match="variable_hash mismatch"):
        replace(sv, variable_hash="sha256:tampered")


def test_descriptor_spec_stage_formula_mismatch_guards() -> None:
    with pytest.raises(
        SchemaViolation,
        match="RUNNING_ONLY requires final_formula_hash = TypedState.NOT_APPLICABLE",
    ):
        DescriptorSpec.create(
            descriptor_id="BAD_RUN_F",
            semantic_definition="Running with final formula",
            stage=DESCRIPTOR_STAGE_RUNNING_ONLY,
            required_input_refs=("running_displacement",),
            availability_rule_ref="RULE_V1",
            running_formula_hash="F_RUN",
            final_formula_hash="F_FINAL",
        )
    with pytest.raises(
        SchemaViolation,
        match="FINAL_ONLY requires running_formula_hash = TypedState.NOT_APPLICABLE",
    ):
        DescriptorSpec.create(
            descriptor_id="BAD_FINAL_F",
            semantic_definition="Final with running formula",
            stage=DESCRIPTOR_STAGE_FINAL_ONLY,
            required_input_refs=("final_displacement",),
            availability_rule_ref="RULE_V1",
            running_formula_hash="F_RUN",
            final_formula_hash="F_FINAL",
        )


def test_s6_realtime_performance_benchmark() -> None:
    wave_bundle, reg, catalog, graph_spec = _setup_s6_environment()
    t0 = time.perf_counter()
    bundle = build_generic_factual_state_graph(
        wave_bundle,
        descriptor_registry=reg,
        state_catalog=catalog,
        graph_spec=graph_spec,
    )
    _ = query_state_graph_as_of(
        bundle, at_key=wave_bundle.observation_keys[-1]
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert elapsed_ms < 50.0
