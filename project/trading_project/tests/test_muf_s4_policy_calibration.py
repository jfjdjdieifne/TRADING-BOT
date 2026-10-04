"""MUF V1 S4 — Development Policy Calibration Harness adversarial test suite.

Fixture discipline: SYNTHETIC SMALL FIXTURES ONLY (no owner data).
Verifies PolicyCandidateScoreCard, PolicyCalibrationRecipe, PolicyCalibrationReceipt,
validate_development_fit_bar_stream, calibrate_development_policy_artifact, and
reproduce_and_verify_calibrated_policy.
"""
from dataclasses import replace
from pathlib import Path
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
    DetectorPolicyWitnessSpec,
    DetectorWitnessBundle,
    adapt_detector_witness_stream,
)
from trading_system.market_understanding.policy_calibration import (
    CALIBRATION_OUTCOME_NONE_SATISFIED,
    CALIBRATION_OUTCOME_TIE_NO_WINNER,
    CALIBRATION_OUTCOME_UNIQUE,
    PolicyCalibrationReceipt,
    PolicyCalibrationRecipe,
    PolicyCandidateScoreCard,
    S4_DUPLICATE_CANDIDATE_POLICY,
    S4_EMPTY_CANDIDATE_POLICY_SET,
    S4_FIT_STREAM_OUTSIDE_DECLARED_DATASET,
    S4_INFORMATION_OBJECTIVE_NOT_VALID_FOR_DETECTOR_FIT,
    S4_INVALID_CALIBRATION_RECEIPT,
    S4_INVALID_CALIBRATION_RECIPE,
    S4_INVALID_FIT_BAR_STREAM,
    S4_INVALID_OBJECTIVE_EVALUATOR_OUTPUT,
    S4_INVALID_SCORECARD,
    S4_MISSING_OR_MISMATCHED_G0_CERTIFICATE,
    calibrate_development_policy_artifact,
    reproduce_and_verify_calibrated_policy,
    validate_development_fit_bar_stream,
)
import trading_system.market_understanding.policy_calibration as policy_calibration_mod
from trading_system.market_understanding.policy_governance import (
    DATASET_ROLE_DEVELOPMENT_FIT,
    DATASET_ROLE_DEVELOPMENT_SELECTION,
    DATASET_ROLE_FINAL_EVALUATION_LOCKED,
    EXPERIMENT_STATUS_COMPLETED,
    EXPERIMENT_STATUS_FAILED,
    EXPOSURE_STATE_EXPOSED_DEVELOPMENT,
    OBJECTIVE_KIND_DETECTION_VALIDITY,
    OBJECTIVE_KIND_INFORMATION,
    OBJECTIVE_KIND_REPRESENTATION_DIAGNOSTIC,
    PROVENANCE_DEVELOPMENT_FIT,
    S3_POLICY_REPRODUCTION_MISMATCH,
    DatasetIdentityArtifact,
    DatasetRoleArtifact,
    ExperimentRegistry,
    ObjectiveArtifact,
    PolicyArtifact,
    SelectionBlockedError,
    evaluate_g0_calibration_gate,
    promote_swing_witness_with_policy_artifact,
)
from trading_system.market_understanding.price_path import (
    PROXY,
    MetricResult,
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


def mk_bar(
    pos: int,
    high: float,
    low: float,
    *,
    dataset: str = "DS-DEV-FIT",
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


def sample_fit_bars() -> list[PublishedOhlcBarFact]:
    return [
        mk_bar(1, 10.0, 9.0),
        mk_bar(2, 11.0, 10.0),
        mk_bar(3, 10.8, 10.5),
        mk_bar(4, 10.6, 10.0),
        mk_bar(5, 11.2, 10.2),
    ]


def sample_setup(
    *,
    comparison_direction= "MAXIMIZE",
    obj_kind: str = OBJECTIVE_KIND_DETECTION_VALIDITY,
    estimands: tuple[str, ...] = (),
):
    obj = ObjectiveArtifact.create(
        objective_id="obj-s4-fit",
        objective_kind=obj_kind,
        semantic_definition="Evaluate confirmed swing structural detection on DEVELOPMENT_FIT",
        estimand_refs=estimands,
        dataset_role_permissions=(
            DATASET_ROLE_DEVELOPMENT_FIT,
            DATASET_ROLE_DEVELOPMENT_SELECTION,
        ),
        aggregation_contract="EXACT_COUNT",
        missingness_contract="FAIL_CLOSED",
        tie_contract="PRESERVE_TIED_CANDIDATES_NO_WINNER",
        comparison_direction=comparison_direction,
        creation_key=k(1),
        code_hash="c" * 64,
        owner_authorization_ref="owner-obj-1",
    )
    ds_fit = DatasetIdentityArtifact.create(
        dataset_id="DS-DEV-FIT",
        content_hash="1" * 64,
        source_identity=SOURCE,
        timeline_id=TIMELINE,
        start_key=k(1),
        end_key=k(10),
        transformation_spec_hash="2" * 64,
        parent_dataset_ids=(),
        creation_code_hash="3" * 64,
        semantic_schema_hash="4" * 64,
    )
    r_fit = DatasetRoleArtifact.create(
        dataset_identity=ds_fit,
        role=DATASET_ROLE_DEVELOPMENT_FIT,
        role_assignment_key=k(1),
        permitted_operations=("DEVELOPMENT_FIT", "PARAMETER_CALIBRATION"),
        prohibited_operations=("FINAL_LOCKED_CLAIM",),
        owner_authorization_ref="owner-role-1",
    )
    reg = ExperimentRegistry()
    reg.preregister(
        experiment_id="exp-s4-01",
        preregistration_key=k(1),
        representation_spec_hash="rep-alpha-v1",
        policy_artifact_hashes=("cand-pol-1", "cand-pol-2"),
        objective_artifact_hash=obj.objective_hash,
        dataset_identities_by_role={DATASET_ROLE_DEVELOPMENT_FIT: "DS-DEV-FIT"},
        code_hash="code-s4-1",
        fit_protocol_hash="fit-proto-1",
    )
    g0_cert = evaluate_g0_calibration_gate(
        objective_artifact=obj,
        fit_dataset_identity=ds_fit,
        fit_dataset_role=r_fit,
        experiment_registry=reg,
        experiment_id="exp-s4-01",
        owner_fit_authorization_ref="owner-fit-auth-1",
    )
    return obj, ds_fit, r_fit, reg, g0_cert


# 1 — End-to-end S4 calibration with unique winner produces valid PolicyArtifact, updates role & registry
def test_muf_s4_01_end_to_end_unique_calibration_and_reproduction():
    obj, ds_fit, r_fit, reg, g0_cert = sample_setup(comparison_direction="MAXIMIZE")
    bars = sample_fit_bars()

    pol_strict = EmpiricalConfirmationPolicy(
        quantile=0.9, prior_continuation_reversals=(0.01, 0.15)
    )
    pol_lenient = EmpiricalConfirmationPolicy(
        quantile=0.25, prior_continuation_reversals=(0.01, 0.02)
    )

    def evaluator(bundle: DetectorWitnessBundle, _obj: ObjectiveArtifact):
        count = len(bundle.swing_event_witnesses)
        return exact_metric(float(count)), count >= 1

    receipt = calibrate_development_policy_artifact(
        bars,
        recipe_id="recipe-01",
        receipt_id="receipt-01",
        policy_id="pol-alpha-dev-01",
        g0_certificate=g0_cert,
        objective_artifact=obj,
        fit_dataset_identity=ds_fit,
        fit_dataset_role=r_fit,
        experiment_registry=reg,
        experiment_id="exp-s4-01",
        owner_fit_authorization_ref="owner-fit-auth-1",
        scope_representation_id="ALPHA_V1",
        candidate_policies=(pol_strict, pol_lenient),
        objective_evaluator=evaluator,
        fit_cutoff_key=k(5),
    )

    assert receipt.outcome_status == CALIBRATION_OUTCOME_UNIQUE
    assert isinstance(receipt.selected_policy_artifact, PolicyArtifact)
    assert receipt.tied_policy_witness_refs == ()
    assert (
        receipt.updated_fit_dataset_role.exposure_state
        == EXPOSURE_STATE_EXPOSED_DEVELOPMENT
    )
    assert receipt.updated_experiment_record.status == EXPERIMENT_STATUS_COMPLETED
    assert (
        receipt.selected_policy_artifact.calibration_provenance_kind
        == PROVENANCE_DEVELOPMENT_FIT
    )
    assert (
        receipt.selected_policy_artifact.reproduction_recipe_hash
        == receipt.recipe.recipe_hash
    )

    # Exact reproduction verification succeeds
    assert reproduce_and_verify_calibrated_policy(
        receipt.selected_policy_artifact,
        bars=bars,
        recipe=receipt.recipe,
        objective_artifact=obj,
        fit_dataset_identity=ds_fit,
        fit_dataset_role=r_fit,
        candidate_policies=(pol_strict, pol_lenient),
        objective_evaluator=evaluator,
    )


# 2 — S4-calibrated PolicyArtifact promotes S2 SwingEventWitnessRecord to AuthoritativeTurningPointRecord
def test_muf_s4_02_calibrated_policy_promotes_s2_witness():
    obj, ds_fit, r_fit, reg, g0_cert = sample_setup(comparison_direction="MAXIMIZE")
    bars = sample_fit_bars()
    pol_lenient = EmpiricalConfirmationPolicy(
        quantile=0.25, prior_continuation_reversals=(0.01, 0.02)
    )

    def evaluator(bundle: DetectorWitnessBundle, _obj: ObjectiveArtifact):
        return exact_metric(float(len(bundle.swing_event_witnesses))), True

    # Fit on bars[:2] up to fit_cutoff_key=k(2), then promote swing confirmed at k(3) >= k(2)
    receipt = calibrate_development_policy_artifact(
        bars[:2],
        recipe_id="recipe-02",
        receipt_id="receipt-02",
        policy_id="pol-alpha-dev-02",
        g0_certificate=g0_cert,
        objective_artifact=obj,
        fit_dataset_identity=ds_fit,
        fit_dataset_role=r_fit,
        experiment_registry=reg,
        experiment_id="exp-s4-01",
        owner_fit_authorization_ref="owner-fit-auth-1",
        scope_representation_id="ALPHA_V1",
        candidate_policies=(pol_lenient,),
        objective_evaluator=evaluator,
        fit_cutoff_key=k(2),
    )
    pol_art = receipt.selected_policy_artifact
    assert isinstance(pol_art, PolicyArtifact)

    bundle = adapt_detector_witness_stream(bars, confirmation_policy=pol_lenient)
    tp = promote_swing_witness_with_policy_artifact(
        bundle.swing_event_witnesses[0], policy_artifact=pol_art
    )
    assert tp.authority_policy_hash == pol_art.policy_hash
    assert tp.origin_key == bars[1].availability_key
    assert tp.availability_key == bars[2].availability_key


# 3 — Tie preservation: when multiple candidates tie, NO winner is invented
def test_muf_s4_03_tie_preservation_no_winner_invented():
    obj, ds_fit, r_fit, reg, g0_cert = sample_setup(comparison_direction="MAXIMIZE")
    bars = sample_fit_bars()

    pol_1 = EmpiricalConfirmationPolicy(
        quantile=0.25, prior_continuation_reversals=(0.01, 0.02)
    )
    pol_2 = EmpiricalConfirmationPolicy(
        quantile=0.50, prior_continuation_reversals=(0.01, 0.02)
    )

    def evaluator(bundle: DetectorWitnessBundle, _obj: ObjectiveArtifact):
        # Both policies confirm 1 swing on sample_fit_bars -> tie!
        return exact_metric(float(len(bundle.swing_event_witnesses))), True

    receipt = calibrate_development_policy_artifact(
        bars,
        recipe_id="recipe-tie",
        receipt_id="receipt-tie",
        policy_id="pol-tie",
        g0_certificate=g0_cert,
        objective_artifact=obj,
        fit_dataset_identity=ds_fit,
        fit_dataset_role=r_fit,
        experiment_registry=reg,
        experiment_id="exp-s4-01",
        owner_fit_authorization_ref="owner-fit-auth-1",
        scope_representation_id="ALPHA_V1",
        candidate_policies=(pol_1, pol_2),
        objective_evaluator=evaluator,
        fit_cutoff_key=k(5),
    )
    assert receipt.outcome_status == CALIBRATION_OUTCOME_TIE_NO_WINNER
    assert receipt.selected_policy_artifact is TypedState.UNDEFINED
    assert len(receipt.tied_policy_witness_refs) == 2
    assert receipt.updated_experiment_record.status == EXPERIMENT_STATUS_COMPLETED


# 4 — When zero candidates satisfy objective constraint, experiment transitions to FAILED
def test_muf_s4_04_no_candidate_satisfied_transitions_to_failed():
    obj, ds_fit, r_fit, reg, g0_cert = sample_setup(
        comparison_direction="SATISFY_CONSTRAINT"
    )
    bars = sample_fit_bars()
    pol_1 = EmpiricalConfirmationPolicy(
        quantile=0.25, prior_continuation_reversals=(0.01, 0.02)
    )

    def evaluator(_bundle: DetectorWitnessBundle, _obj: ObjectiveArtifact):
        return TypedState.UNDEFINED, False

    receipt = calibrate_development_policy_artifact(
        bars,
        recipe_id="recipe-fail",
        receipt_id="receipt-fail",
        policy_id="pol-fail",
        g0_certificate=g0_cert,
        objective_artifact=obj,
        fit_dataset_identity=ds_fit,
        fit_dataset_role=r_fit,
        experiment_registry=reg,
        experiment_id="exp-s4-01",
        owner_fit_authorization_ref="owner-fit-auth-1",
        scope_representation_id="ALPHA_V1",
        candidate_policies=(pol_1,),
        objective_evaluator=evaluator,
        fit_cutoff_key=k(5),
    )
    assert receipt.outcome_status == CALIBRATION_OUTCOME_NONE_SATISFIED
    assert receipt.selected_policy_artifact is TypedState.UNDEFINED
    assert receipt.tied_policy_witness_refs == ()
    assert receipt.updated_experiment_record.status == EXPERIMENT_STATUS_FAILED
    assert len(receipt.updated_experiment_record.failure_refs) == 1


# 5 — Missing or mismatched G0 certificate fails closed with SelectionBlockedError
def test_muf_s4_05_missing_or_mismatched_g0_certificate_blocked():
    obj, ds_fit, r_fit, reg, g0_cert = sample_setup()
    bars = sample_fit_bars()
    pol_1 = EmpiricalConfirmationPolicy(
        quantile=0.25, prior_continuation_reversals=(0.01, 0.02)
    )

    def evaluator(bundle: DetectorWitnessBundle, _obj: ObjectiveArtifact):
        return exact_metric(float(len(bundle.swing_event_witnesses))), True

    # Missing G0 certificate
    with pytest.raises(SelectionBlockedError) as exc_missing:
        calibrate_development_policy_artifact(
            bars,
            recipe_id="r1",
            receipt_id="rc1",
            policy_id="p1",
            g0_certificate=TypedState.NOT_CONFIGURED,
            objective_artifact=obj,
            fit_dataset_identity=ds_fit,
            fit_dataset_role=r_fit,
            experiment_registry=reg,
            experiment_id="exp-s4-01",
            owner_fit_authorization_ref="owner-fit-auth-1",
            scope_representation_id="ALPHA_V1",
            candidate_policies=(pol_1,),
            objective_evaluator=evaluator,
        )
    assert S4_MISSING_OR_MISMATCHED_G0_CERTIFICATE in str(exc_missing.value)

    # Forged/mismatched G0 certificate (different owner_fit_authorization_ref)
    forged_cert = replace(g0_cert, owner_fit_authorization_ref="other-owner-ref")
    with pytest.raises(SelectionBlockedError) as exc_forged:
        calibrate_development_policy_artifact(
            bars,
            recipe_id="r1",
            receipt_id="rc1",
            policy_id="p1",
            g0_certificate=forged_cert,
            objective_artifact=obj,
            fit_dataset_identity=ds_fit,
            fit_dataset_role=r_fit,
            experiment_registry=reg,
            experiment_id="exp-s4-01",
            owner_fit_authorization_ref="owner-fit-auth-1",
            scope_representation_id="ALPHA_V1",
            candidate_policies=(pol_1,),
            objective_evaluator=evaluator,
        )
    assert S4_MISSING_OR_MISMATCHED_G0_CERTIFICATE in str(exc_forged.value)


# 6 — INFORMATION_OBJECTIVE rejected in S4 detector policy calibration
def test_muf_s4_06_information_objective_rejected_in_s4():
    obj_info, ds_fit, r_fit, reg, g0_cert = sample_setup(
        obj_kind=OBJECTIVE_KIND_INFORMATION,
        estimands=("estimand-hash-01",),
    )
    bars = sample_fit_bars()
    pol_1 = EmpiricalConfirmationPolicy(
        quantile=0.25, prior_continuation_reversals=(0.01, 0.02)
    )

    def evaluator(bundle: DetectorWitnessBundle, _obj: ObjectiveArtifact):
        return exact_metric(float(len(bundle.swing_event_witnesses))), True

    with pytest.raises(SelectionBlockedError) as exc_info:
        calibrate_development_policy_artifact(
            bars,
            recipe_id="r1",
            receipt_id="rc1",
            policy_id="p1",
            g0_certificate=g0_cert,
            objective_artifact=obj_info,
            fit_dataset_identity=ds_fit,
            fit_dataset_role=r_fit,
            experiment_registry=reg,
            experiment_id="exp-s4-01",
            owner_fit_authorization_ref="owner-fit-auth-1",
            scope_representation_id="ALPHA_V1",
            candidate_policies=(pol_1,),
            objective_evaluator=evaluator,
        )
    assert S4_INFORMATION_OBJECTIVE_NOT_VALID_FOR_DETECTOR_FIT in str(exc_info.value)


# 7 — Bar stream outside [start_key, fit_cutoff_key] or from another dataset fails closed
def test_muf_s4_07_bar_stream_causal_and_dataset_boundaries():
    _obj, ds_fit, r_fit, _reg, _g0_cert = sample_setup()
    bars = sample_fit_bars()

    # Bar at position 5 exceeds fit_cutoff_key k(4) -> PrematureAvailability
    with pytest.raises(PrematureAvailability) as exc_future:
        validate_development_fit_bar_stream(
            bars,
            fit_dataset_identity=ds_fit,
            fit_dataset_role=r_fit,
            fit_cutoff_key=k(4),
        )
    assert S4_FIT_STREAM_OUTSIDE_DECLARED_DATASET in str(exc_future.value)

    # Bar at position 11 exceeds ds_fit.end_key k(10) -> PrematureAvailability
    with pytest.raises(PrematureAvailability):
        validate_development_fit_bar_stream(
            bars + [mk_bar(11, 12.0, 11.0)],
            fit_dataset_identity=ds_fit,
            fit_dataset_role=r_fit,
        )

    # Bar from FINAL_EVALUATION_LOCKED dataset injected into fit stream -> SelectionBlockedError
    with pytest.raises(SelectionBlockedError) as exc_leak:
        validate_development_fit_bar_stream(
            bars + [mk_bar(6, 12.0, 11.0, dataset="DS-FINAL-LOCKED")],
            fit_dataset_identity=ds_fit,
            fit_dataset_role=r_fit,
        )
    assert S4_FIT_STREAM_OUTSIDE_DECLARED_DATASET in str(exc_leak.value)

    # Non-DEVELOPMENT_FIT role rejected
    ds_sel = DatasetIdentityArtifact.create(
        dataset_id="DS-SEL",
        content_hash="9" * 64,
        source_identity=SOURCE,
        timeline_id=TIMELINE,
        start_key=k(1),
        end_key=k(10),
        transformation_spec_hash="2" * 64,
        parent_dataset_ids=(),
        creation_code_hash="3" * 64,
        semantic_schema_hash="4" * 64,
    )
    r_sel = DatasetRoleArtifact.create(
        dataset_identity=ds_sel,
        role=DATASET_ROLE_DEVELOPMENT_SELECTION,
        role_assignment_key=k(1),
        permitted_operations=("DEVELOPMENT_SELECTION",),
        prohibited_operations=("FINAL_LOCKED_CLAIM",),
        owner_authorization_ref="owner-sel",
    )
    with pytest.raises(SelectionBlockedError):
        validate_development_fit_bar_stream(
            [mk_bar(1, 10.0, 9.0, dataset="DS-SEL")],
            fit_dataset_identity=ds_sel,
            fit_dataset_role=r_sel,
        )


# 8 — Out-of-order or duplicate bars in DEVELOPMENT_FIT stream rejected
def test_muf_s4_08_non_monotonic_fit_bar_stream_rejected():
    _obj, ds_fit, r_fit, _reg, _g0_cert = sample_setup()
    b1 = mk_bar(1, 10.0, 9.0)
    b2 = mk_bar(2, 11.0, 10.0)
    with pytest.raises(SchemaViolation) as exc_ord:
        validate_development_fit_bar_stream(
            [b2, b1],
            fit_dataset_identity=ds_fit,
            fit_dataset_role=r_fit,
        )
    assert S4_INVALID_FIT_BAR_STREAM in str(exc_ord.value)


# 9 — Empty or duplicate candidate policies rejected
def test_muf_s4_09_empty_or_duplicate_candidate_policies_rejected():
    obj, ds_fit, r_fit, reg, g0_cert = sample_setup()
    bars = sample_fit_bars()
    pol_1 = EmpiricalConfirmationPolicy(
        quantile=0.25, prior_continuation_reversals=(0.01, 0.02)
    )

    def evaluator(bundle: DetectorWitnessBundle, _obj: ObjectiveArtifact):
        return exact_metric(float(len(bundle.swing_event_witnesses))), True

    with pytest.raises(SchemaViolation) as exc_empty:
        calibrate_development_policy_artifact(
            bars,
            recipe_id="r1",
            receipt_id="rc1",
            policy_id="p1",
            g0_certificate=g0_cert,
            objective_artifact=obj,
            fit_dataset_identity=ds_fit,
            fit_dataset_role=r_fit,
            experiment_registry=reg,
            experiment_id="exp-s4-01",
            owner_fit_authorization_ref="owner-fit-auth-1",
            scope_representation_id="ALPHA_V1",
            candidate_policies=(),
            objective_evaluator=evaluator,
        )
    assert S4_EMPTY_CANDIDATE_POLICY_SET in str(exc_empty.value)

    with pytest.raises(SchemaViolation) as exc_dup:
        calibrate_development_policy_artifact(
            bars,
            recipe_id="r1",
            receipt_id="rc1",
            policy_id="p1",
            g0_certificate=g0_cert,
            objective_artifact=obj,
            fit_dataset_identity=ds_fit,
            fit_dataset_role=r_fit,
            experiment_registry=reg,
            experiment_id="exp-s4-01",
            owner_fit_authorization_ref="owner-fit-auth-1",
            scope_representation_id="ALPHA_V1",
            candidate_policies=(pol_1, pol_1),
            objective_evaluator=evaluator,
        )
    assert S4_DUPLICATE_CANDIDATE_POLICY in str(exc_dup.value)


# 10 — MINIMIZE objective direction selects minimum metric candidate
def test_muf_s4_10_minimize_objective_direction():
    obj, ds_fit, r_fit, reg, g0_cert = sample_setup(
        comparison_direction="MINIMIZE",
        obj_kind=OBJECTIVE_KIND_REPRESENTATION_DIAGNOSTIC,
    )
    bars = sample_fit_bars()
    pol_strict = EmpiricalConfirmationPolicy(
        quantile=0.9, prior_continuation_reversals=(0.01, 0.15)
    )
    pol_lenient = EmpiricalConfirmationPolicy(
        quantile=0.25, prior_continuation_reversals=(0.01, 0.02)
    )

    def evaluator(bundle: DetectorWitnessBundle, _obj: ObjectiveArtifact):
        return exact_metric(float(len(bundle.swing_event_witnesses))), True

    receipt = calibrate_development_policy_artifact(
        bars,
        recipe_id="r-min",
        receipt_id="rc-min",
        policy_id="p-min",
        g0_certificate=g0_cert,
        objective_artifact=obj,
        fit_dataset_identity=ds_fit,
        fit_dataset_role=r_fit,
        experiment_registry=reg,
        experiment_id="exp-s4-01",
        owner_fit_authorization_ref="owner-fit-auth-1",
        scope_representation_id="ALPHA_V1",
        candidate_policies=(pol_strict, pol_lenient),
        objective_evaluator=evaluator,
        fit_cutoff_key=k(5),
    )
    assert receipt.outcome_status == CALIBRATION_OUTCOME_UNIQUE
    spec_strict = DetectorPolicyWitnessSpec.from_policy(pol_strict)
    assert isinstance(receipt.selected_policy_artifact, PolicyArtifact)
    assert (
        receipt.selected_policy_artifact.detector_policy_witness_ref
        == str(spec_strict.spec_identity)
    )


# 11 — Reproduction mismatch detection when bars or candidates are altered
def test_muf_s4_11_reproduction_mismatch_detection():
    obj, ds_fit, r_fit, reg, g0_cert = sample_setup(comparison_direction="MAXIMIZE")
    bars = sample_fit_bars()
    pol_strict = EmpiricalConfirmationPolicy(
        quantile=0.9, prior_continuation_reversals=(0.01, 0.15)
    )
    pol_lenient = EmpiricalConfirmationPolicy(
        quantile=0.25, prior_continuation_reversals=(0.01, 0.02)
    )

    def evaluator(bundle: DetectorWitnessBundle, _obj: ObjectiveArtifact):
        count = len(bundle.swing_event_witnesses)
        return exact_metric(float(count)), count >= 1

    receipt = calibrate_development_policy_artifact(
        bars,
        recipe_id="recipe-11",
        receipt_id="receipt-11",
        policy_id="pol-11",
        g0_certificate=g0_cert,
        objective_artifact=obj,
        fit_dataset_identity=ds_fit,
        fit_dataset_role=r_fit,
        experiment_registry=reg,
        experiment_id="exp-s4-01",
        owner_fit_authorization_ref="owner-fit-auth-1",
        scope_representation_id="ALPHA_V1",
        candidate_policies=(pol_strict, pol_lenient),
        objective_evaluator=evaluator,
        fit_cutoff_key=k(5),
    )
    pol_art = receipt.selected_policy_artifact
    assert isinstance(pol_art, PolicyArtifact)

    # Reproducing with only pol_lenient (different candidate set -> different recipe_hash) fails closed
    with pytest.raises(SchemaViolation) as exc_repro:
        reproduce_and_verify_calibrated_policy(
            pol_art,
            bars=bars,
            recipe=receipt.recipe,
            objective_artifact=obj,
            fit_dataset_identity=ds_fit,
            fit_dataset_role=r_fit,
            candidate_policies=(pol_lenient,),
            objective_evaluator=evaluator,
        )
    assert S3_POLICY_REPRODUCTION_MISMATCH in str(exc_repro.value)

    # PolicyArtifact with matching witness_ref and recipe_hash but different scope_representation_id fails policy_hash check
    pol_art_diff_scope = PolicyArtifact.create(
        policy_id=pol_art.policy_id,
        authority_kind=pol_art.authority_kind,
        target_engine_identity=pol_art.target_engine_identity,
        detector_policy_witness_ref=pol_art.detector_policy_witness_ref,
        scope_timeline_id=pol_art.scope_timeline_id,
        scope_axis=pol_art.scope_axis,
        scope_representation_id="BETA_V1",
        calibration_provenance_kind=PROVENANCE_DEVELOPMENT_FIT,
        fit_dataset_id=ds_fit.dataset_id,
        objective_artifact_hash=obj.objective_hash,
        experiment_id="exp-s4-01",
        fit_dataset_role_hash=r_fit.role_artifact_hash,
        reproduction_recipe_hash=receipt.recipe.recipe_hash,
        effective_from_key=k(5),
        owner_authorization_ref="owner-fit-auth-1",
    )
    with pytest.raises(SchemaViolation) as exc_scope_hash:
        reproduce_and_verify_calibrated_policy(
            pol_art_diff_scope,
            bars=bars,
            recipe=receipt.recipe,
            objective_artifact=obj,
            fit_dataset_identity=ds_fit,
            fit_dataset_role=r_fit,
            candidate_policies=(pol_strict, pol_lenient),
            objective_evaluator=evaluator,
        )
    assert S3_POLICY_REPRODUCTION_MISMATCH in str(exc_scope_hash.value)


# 12 — Invalid evaluator output (APPROXIMATE metric, non-tuple, or UNDEFINED under MAXIMIZE) fails closed
def test_muf_s4_12_invalid_objective_evaluator_outputs_rejected():
    obj, ds_fit, r_fit, reg, g0_cert = sample_setup(comparison_direction="MAXIMIZE")
    bars = sample_fit_bars()
    pol_1 = EmpiricalConfirmationPolicy(
        quantile=0.25, prior_continuation_reversals=(0.01, 0.02)
    )

    # PROXY metric rejected
    def bad_eval_approx(_b: DetectorWitnessBundle, _o: ObjectiveArtifact):
        return MetricResult(semantics=PROXY, value=1.0), True

    with pytest.raises(SchemaViolation) as exc_app:
        calibrate_development_policy_artifact(
            bars,
            recipe_id="r1",
            receipt_id="rc1",
            policy_id="p1",
            g0_certificate=g0_cert,
            objective_artifact=obj,
            fit_dataset_identity=ds_fit,
            fit_dataset_role=r_fit,
            experiment_registry=reg,
            experiment_id="exp-s4-01",
            owner_fit_authorization_ref="owner-fit-auth-1",
            scope_representation_id="ALPHA_V1",
            candidate_policies=(pol_1,),
            objective_evaluator=bad_eval_approx,
        )
    assert S4_INVALID_OBJECTIVE_EVALUATOR_OUTPUT in str(exc_app.value)

    # UNDEFINED metric on a satisfied candidate under MAXIMIZE rejected
    def bad_eval_undef(_b: DetectorWitnessBundle, _o: ObjectiveArtifact):
        return TypedState.UNDEFINED, True

    with pytest.raises(SchemaViolation) as exc_und:
        calibrate_development_policy_artifact(
            bars,
            recipe_id="r1",
            receipt_id="rc1",
            policy_id="p1",
            g0_certificate=g0_cert,
            objective_artifact=obj,
            fit_dataset_identity=ds_fit,
            fit_dataset_role=r_fit,
            experiment_registry=reg,
            experiment_id="exp-s4-01",
            owner_fit_authorization_ref="owner-fit-auth-1",
            scope_representation_id="ALPHA_V1",
            candidate_policies=(pol_1,),
            objective_evaluator=bad_eval_undef,
        )
    assert S4_INVALID_OBJECTIVE_EVALUATOR_OUTPUT in str(exc_und.value)


# 13 — Deep immutability & constructor tamper resistance across S4 records
def test_muf_s4_13_deep_immutability_and_tamper_resistance():
    obj, ds_fit, r_fit, reg, g0_cert = sample_setup(comparison_direction="MAXIMIZE")
    bars = sample_fit_bars()
    pol_lenient = EmpiricalConfirmationPolicy(
        quantile=0.25, prior_continuation_reversals=(0.01, 0.02)
    )

    def evaluator(bundle: DetectorWitnessBundle, _obj: ObjectiveArtifact):
        return exact_metric(float(len(bundle.swing_event_witnesses))), True

    receipt = calibrate_development_policy_artifact(
        bars,
        recipe_id="recipe-13",
        receipt_id="receipt-13",
        policy_id="pol-13",
        g0_certificate=g0_cert,
        objective_artifact=obj,
        fit_dataset_identity=ds_fit,
        fit_dataset_role=r_fit,
        experiment_registry=reg,
        experiment_id="exp-s4-01",
        owner_fit_authorization_ref="owner-fit-auth-1",
        scope_representation_id="ALPHA_V1",
        candidate_policies=(pol_lenient,),
        objective_evaluator=evaluator,
        fit_cutoff_key=k(5),
    )

    with pytest.raises((ImmutabilityViolation, TypeError, AttributeError)):
        receipt.outcome_status = CALIBRATION_OUTCOME_NONE_SATISFIED  # type: ignore[misc]
    with pytest.raises((ImmutabilityViolation, TypeError, AttributeError)):
        receipt.recipe.recipe_id = "mutated"  # type: ignore[misc]

    # Tampering receipt_hash or recipe_hash via replace fails closed
    with pytest.raises(SchemaViolation):
        replace(receipt.recipe, scope_representation_id="TAMPERED")
    with pytest.raises(SchemaViolation):
        replace(receipt, receipt_id="tampered-id")


# 14 — S0 AST guards on policy_calibration.py & sealed S0/S1/S2/S3 certificate integrity
def test_muf_s4_14_ast_guards_and_sealed_s0_s1_s2_s3_certificates_untouched():
    import hashlib

    source_text = Path(policy_calibration_mod.__file__).read_text(encoding="utf-8")
    assert scan_private_imports(source_text) == ()
    assert scan_prohibited_implementations(source_text) == ()
    assert scan_market_shape_implementations(source_text) == ()

    root = Path(__file__).resolve().parent.parent
    for cert_rel in (
        "docs/releases/MODULE_MUF_V1_S0_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S1_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S2_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S3_ACCEPTED_SRC_TESTS.sha256",
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


# 15 — SATISFY_CONSTRAINT with single satisfying candidate selects unique PolicyArtifact; with two -> tie
def test_muf_s4_15_satisfy_constraint_unique_vs_tie():
    obj, ds_fit, r_fit, reg, g0_cert = sample_setup(
        comparison_direction="SATISFY_CONSTRAINT"
    )
    bars = sample_fit_bars()
    pol_strict = EmpiricalConfirmationPolicy(
        quantile=0.9, prior_continuation_reversals=(0.01, 0.15)
    )
    pol_lenient = EmpiricalConfirmationPolicy(
        quantile=0.25, prior_continuation_reversals=(0.01, 0.02)
    )

    def eval_one_sat(bundle: DetectorWitnessBundle, _obj: ObjectiveArtifact):
        return TypedState.UNDEFINED, len(bundle.swing_event_witnesses) >= 1

    rec_unique = calibrate_development_policy_artifact(
        bars,
        recipe_id="r-sat-1",
        receipt_id="rc-sat-1",
        policy_id="p-sat-1",
        g0_certificate=g0_cert,
        objective_artifact=obj,
        fit_dataset_identity=ds_fit,
        fit_dataset_role=r_fit,
        experiment_registry=reg,
        experiment_id="exp-s4-01",
        owner_fit_authorization_ref="owner-fit-auth-1",
        scope_representation_id="ALPHA_V1",
        candidate_policies=(pol_strict, pol_lenient),
        objective_evaluator=eval_one_sat,
        fit_cutoff_key=k(5),
    )
    assert rec_unique.outcome_status == CALIBRATION_OUTCOME_UNIQUE
    assert isinstance(rec_unique.selected_policy_artifact, PolicyArtifact)

    # Second experiment where both satisfy -> TIE_PRESERVED_NO_WINNER
    reg2 = ExperimentRegistry()
    reg2.preregister(
        experiment_id="exp-s4-02",
        preregistration_key=k(1),
        representation_spec_hash="rep-alpha-v1",
        policy_artifact_hashes=("cand-1", "cand-2"),
        objective_artifact_hash=obj.objective_hash,
        dataset_identities_by_role={DATASET_ROLE_DEVELOPMENT_FIT: "DS-DEV-FIT"},
        code_hash="code-s4-1",
        fit_protocol_hash="fit-proto-1",
    )
    g0_2 = evaluate_g0_calibration_gate(
        objective_artifact=obj,
        fit_dataset_identity=ds_fit,
        fit_dataset_role=r_fit,
        experiment_registry=reg2,
        experiment_id="exp-s4-02",
        owner_fit_authorization_ref="owner-fit-auth-1",
    )

    def eval_both_sat(_bundle: DetectorWitnessBundle, _obj: ObjectiveArtifact):
        return TypedState.UNDEFINED, True

    rec_tie = calibrate_development_policy_artifact(
        bars,
        recipe_id="r-sat-2",
        receipt_id="rc-sat-2",
        policy_id="p-sat-2",
        g0_certificate=g0_2,
        objective_artifact=obj,
        fit_dataset_identity=ds_fit,
        fit_dataset_role=r_fit,
        experiment_registry=reg2,
        experiment_id="exp-s4-02",
        owner_fit_authorization_ref="owner-fit-auth-1",
        scope_representation_id="ALPHA_V1",
        candidate_policies=(pol_strict, pol_lenient),
        objective_evaluator=eval_both_sat,
        fit_cutoff_key=k(5),
    )
    assert rec_tie.outcome_status == CALIBRATION_OUTCOME_TIE_NO_WINNER
    assert rec_tie.selected_policy_artifact is TypedState.UNDEFINED
    assert len(rec_tie.tied_policy_witness_refs) == 2


# 16 — PolicyCandidateScoreCard constructor boundary validation
def test_muf_s4_16_scorecard_boundary_validation():
    pol = EmpiricalConfirmationPolicy(
        quantile=0.25, prior_continuation_reversals=(0.01, 0.02)
    )
    spec = DetectorPolicyWitnessSpec.from_policy(pol)

    # Mismatched candidate_policy_witness_ref rejected
    with pytest.raises(SchemaViolation) as exc_ref:
        PolicyCandidateScoreCard(
            candidate_policy_witness_ref="wrong-ref",
            policy_spec=spec,
            confirmed_swing_count=1,
            candidate_observation_count=5,
            objective_metric=exact_metric(1.0),
            constraint_satisfied=True,
            evaluation_cutoff_key=k(5),
        )
    assert S4_INVALID_SCORECARD in str(exc_ref.value)

    # BAR_PRE_CLOSE evaluation_cutoff_key rejected
    with pytest.raises(IllegalCausalReference):
        PolicyCandidateScoreCard(
            candidate_policy_witness_ref=str(spec.spec_identity),
            policy_spec=spec,
            confirmed_swing_count=1,
            candidate_observation_count=5,
            objective_metric=exact_metric(1.0),
            constraint_satisfied=True,
            evaluation_cutoff_key=k(5, phase=InformationPhase.BAR_PRE_CLOSE),
        )


# 17 — PolicyCalibrationRecipe constructor boundary validation
def test_muf_s4_17_recipe_boundary_validation():
    _obj, _ds_fit, _r_fit, _reg, g0_cert = sample_setup()

    # Empty candidate_policy_witness_refs rejected
    with pytest.raises(SchemaViolation) as exc_emp:
        PolicyCalibrationRecipe.create(
            recipe_id="r-emp",
            g0_certificate=g0_cert,
            scope_timeline_id=TIMELINE,
            scope_axis=InformationAxis.POSITIONAL,
            scope_representation_id="ALPHA_V1",
            candidate_policy_witness_refs=(),
            fit_cutoff_key=k(5),
        )
    assert S4_EMPTY_CANDIDATE_POLICY_SET in str(exc_emp.value)

    # Timeline mismatch on fit_cutoff_key rejected
    with pytest.raises(InformationKeyViolation):
        PolicyCalibrationRecipe.create(
            recipe_id="r-tl",
            g0_certificate=g0_cert,
            scope_timeline_id=TIMELINE,
            scope_axis=InformationAxis.POSITIONAL,
            scope_representation_id="ALPHA_V1",
            candidate_policy_witness_refs=("ref-1",),
            fit_cutoff_key=k(5, timeline="OTHER_TL"),
        )


# 18 — PolicyCalibrationReceipt constructor contradiction checks
def test_muf_s4_18_receipt_contradiction_checks():
    obj, ds_fit, r_fit, reg, g0_cert = sample_setup(comparison_direction="MAXIMIZE")
    bars = sample_fit_bars()
    pol_lenient = EmpiricalConfirmationPolicy(
        quantile=0.25, prior_continuation_reversals=(0.01, 0.02)
    )

    def evaluator(bundle: DetectorWitnessBundle, _obj: ObjectiveArtifact):
        return exact_metric(float(len(bundle.swing_event_witnesses))), True

    receipt = calibrate_development_policy_artifact(
        bars,
        recipe_id="r-18",
        receipt_id="rc-18",
        policy_id="p-18",
        g0_certificate=g0_cert,
        objective_artifact=obj,
        fit_dataset_identity=ds_fit,
        fit_dataset_role=r_fit,
        experiment_registry=reg,
        experiment_id="exp-s4-01",
        owner_fit_authorization_ref="owner-fit-auth-1",
        scope_representation_id="ALPHA_V1",
        candidate_policies=(pol_lenient,),
        objective_evaluator=evaluator,
        fit_cutoff_key=k(5),
    )

    # CALIBRATED_UNIQUE with selected_policy_artifact=UNDEFINED fails closed
    with pytest.raises(SchemaViolation) as exc_c1:
        replace(receipt, selected_policy_artifact=TypedState.UNDEFINED)
    assert S4_INVALID_CALIBRATION_RECEIPT in str(exc_c1.value)

    # CALIBRATED_UNIQUE with non-empty tied_policy_witness_refs fails closed
    with pytest.raises(SchemaViolation) as exc_c2:
        replace(receipt, tied_policy_witness_refs=("ref-1", "ref-2"))
    assert S4_INVALID_CALIBRATION_RECEIPT in str(exc_c2.value)


# 19 — validate_development_fit_bar_stream rejects empty bars, wrong source, or BAR_PRE_CLOSE cutoff
def test_muf_s4_19_validate_bar_stream_edge_cases():
    _obj, ds_fit, r_fit, _reg, _g0_cert = sample_setup()
    bars = sample_fit_bars()

    with pytest.raises(SchemaViolation):
        validate_development_fit_bar_stream(
            (),
            fit_dataset_identity=ds_fit,
            fit_dataset_role=r_fit,
        )

    with pytest.raises(IllegalCausalReference):
        validate_development_fit_bar_stream(
            bars,
            fit_dataset_identity=ds_fit,
            fit_dataset_role=r_fit,
            fit_cutoff_key=k(5, phase=InformationPhase.BAR_PRE_CLOSE),
        )

    other_source = SchemaIdentity("OtherExchangeSource", "V1")
    with pytest.raises(SchemaViolation):
        validate_development_fit_bar_stream(
            [mk_bar(1, 10.0, 9.0, source=other_source)],
            fit_dataset_identity=ds_fit,
            fit_dataset_role=r_fit,
        )


# 20 — Deterministic replay of S4 calibration produces identical recipe_hash, policy_hash, and receipt_hash
def test_muf_s4_20_deterministic_replay_equivalence():
    obj1, ds1, r1, reg1, g0_1 = sample_setup(comparison_direction="MAXIMIZE")
    obj2, ds2, r2, reg2, g0_2 = sample_setup(comparison_direction="MAXIMIZE")
    bars1 = sample_fit_bars()
    bars2 = sample_fit_bars()
    pol = EmpiricalConfirmationPolicy(
        quantile=0.25, prior_continuation_reversals=(0.01, 0.02)
    )

    def evaluator(bundle: DetectorWitnessBundle, _obj: ObjectiveArtifact):
        return exact_metric(float(len(bundle.swing_event_witnesses))), True

    rec1 = calibrate_development_policy_artifact(
        bars1,
        recipe_id="r-det",
        receipt_id="rc-det",
        policy_id="p-det",
        g0_certificate=g0_1,
        objective_artifact=obj1,
        fit_dataset_identity=ds1,
        fit_dataset_role=r1,
        experiment_registry=reg1,
        experiment_id="exp-s4-01",
        owner_fit_authorization_ref="owner-fit-auth-1",
        scope_representation_id="ALPHA_V1",
        candidate_policies=(pol,),
        objective_evaluator=evaluator,
        fit_cutoff_key=k(5),
    )
    rec2 = calibrate_development_policy_artifact(
        bars2,
        recipe_id="r-det",
        receipt_id="rc-det",
        policy_id="p-det",
        g0_certificate=g0_2,
        objective_artifact=obj2,
        fit_dataset_identity=ds2,
        fit_dataset_role=r2,
        experiment_registry=reg2,
        experiment_id="exp-s4-01",
        owner_fit_authorization_ref="owner-fit-auth-1",
        scope_representation_id="ALPHA_V1",
        candidate_policies=(pol,),
        objective_evaluator=evaluator,
        fit_cutoff_key=k(5),
    )
    assert rec1 == rec2
    assert rec1.receipt_hash == rec2.receipt_hash
    assert rec1.recipe.recipe_hash == rec2.recipe.recipe_hash
    assert rec1.selected_policy_artifact == rec2.selected_policy_artifact

