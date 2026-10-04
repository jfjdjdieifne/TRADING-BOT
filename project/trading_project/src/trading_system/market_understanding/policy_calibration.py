"""MUF V1 S4: Development Policy Calibration Harness.

Implements the causal, G0-gated development policy calibration pipeline on
``DEVELOPMENT_FIT`` datasets only (D1-1, D1-2, D1-4, D1-16, D1-21, D2-1, D2-3,
D2-4, D2-7, D2-22):
- ``PolicyCandidateScoreCard``
- ``PolicyCalibrationRecipe``
- ``PolicyCalibrationReceipt``
- ``validate_development_fit_bar_stream``
- ``calibrate_development_policy_artifact``
- ``reproduce_and_verify_calibrated_policy``

S4 invents ZERO market parameters, thresholds, quantiles, windows, or
objectives. It requires an explicit ``G0CalibrationGateCertificate`` and
operates strictly within the causal boundaries of a ``DEVELOPMENT_FIT`` dataset.
"""
from dataclasses import dataclass
import math
from typing import Any, Callable, Mapping, Optional, Sequence, Tuple, Union

from trading_system.market_understanding.availability import (
    InformationAxis,
    require_visible_at,
)
from trading_system.market_understanding.contracts import (
    IllegalCausalReference,
    ImmutabilityViolation,
    IncomparableInformationKeys,
    InformationKeyViolation,
    PrematureAvailability,
    SchemaIdentity,
    SchemaViolation,
    TypedState,
)
from trading_system.market_understanding.detector_witness import (
    DetectorPolicyWitnessSpec,
    DetectorWitnessBundle,
    S2_ADAPTER_ENGINE_IDENTITY,
    adapt_detector_witness_stream,
)
from trading_system.market_understanding.identity import (
    ArtifactIdentitySchema,
    canonical_artifact_identity,
)
from trading_system.market_understanding.policy_governance import (
    DATASET_ROLE_DEVELOPMENT_FIT,
    EXPERIMENT_STATUS_COMPLETED,
    EXPERIMENT_STATUS_FAILED,
    EXPERIMENT_STATUS_PREREGISTERED,
    EXPERIMENT_STATUS_RUNNING,
    EXPOSURE_STATE_EXPOSED_DEVELOPMENT,
    EXPOSURE_STATE_UNEXPOSED,
    OBJECTIVE_KIND_DETECTION_VALIDITY,
    OBJECTIVE_KIND_REPRESENTATION_DIAGNOSTIC,
    POLICY_AUTHORITY_KIND_MUF,
    PROVENANCE_DEVELOPMENT_FIT,
    QUALIFICATION_OBJECTIVE_DEFAULT,
    S3_POLICY_REPRODUCTION_MISMATCH,
    DatasetIdentityArtifact,
    DatasetRoleArtifact,
    ExperimentRegistry,
    G0CalibrationGateCertificate,
    ObjectiveArtifact,
    PolicyArtifact,
    RepresentationExperimentRecord,
    SelectionBlockedError,
    evaluate_g0_calibration_gate,
    record_dataset_exposure,
    verify_policy_artifact_reproduction,
)
from trading_system.market_understanding.price_path import (
    EXACT,
    MetricResult,
    PublishedOhlcBarFact,
    key_axis,
    metric_payload,
)
from trading_system.market_understanding.records import ImmutableRecord
from trading_system.research.information_time import (
    InformationKey,
    InformationKeyError,
    InformationPhase,
)
from trading_system.structure.swing_detector import SwingConfirmationPolicy


S4_SCHEMA_IDENTITY = SchemaIdentity("MUF_S4_POLICY_CALIBRATION", "V1")

# Outcome statuses for PolicyCalibrationReceipt
CALIBRATION_OUTCOME_UNIQUE = "CALIBRATED_UNIQUE"
CALIBRATION_OUTCOME_TIE_NO_WINNER = "TIE_PRESERVED_NO_WINNER"
CALIBRATION_OUTCOME_NONE_SATISFIED = "NO_CANDIDATE_SATISFIED_OBJECTIVE"
LEGAL_CALIBRATION_OUTCOMES = frozenset(
    {
        CALIBRATION_OUTCOME_UNIQUE,
        CALIBRATION_OUTCOME_TIE_NO_WINNER,
        CALIBRATION_OUTCOME_NONE_SATISFIED,
    }
)

# Deterministic S4 error reason codes
S4_MISSING_OR_MISMATCHED_G0_CERTIFICATE = "S4_MISSING_OR_MISMATCHED_G0_CERTIFICATE"
S4_INVALID_FIT_BAR_STREAM = "S4_INVALID_FIT_BAR_STREAM"
S4_FIT_STREAM_OUTSIDE_DECLARED_DATASET = "S4_FIT_STREAM_OUTSIDE_DECLARED_DATASET"
S4_EMPTY_CANDIDATE_POLICY_SET = "S4_EMPTY_CANDIDATE_POLICY_SET"
S4_DUPLICATE_CANDIDATE_POLICY = "S4_DUPLICATE_CANDIDATE_POLICY"
S4_INFORMATION_OBJECTIVE_NOT_VALID_FOR_DETECTOR_FIT = (
    "S4_INFORMATION_OBJECTIVE_NOT_VALID_FOR_DETECTOR_FIT"
)
S4_INVALID_OBJECTIVE_EVALUATOR_OUTPUT = "S4_INVALID_OBJECTIVE_EVALUATOR_OUTPUT"
S4_INVALID_CALIBRATION_RECIPE = "S4_INVALID_CALIBRATION_RECIPE"
S4_INVALID_CALIBRATION_RECEIPT = "S4_INVALID_CALIBRATION_RECEIPT"
S4_INVALID_SCORECARD = "S4_INVALID_SCORECARD"


CALIBRATION_RECIPE_IDENTITY_SCHEMA = ArtifactIdentitySchema(
    artifact_type="MUF_S4_POLICY_CALIBRATION_RECIPE",
    schema_identity=S4_SCHEMA_IDENTITY,
    identity_defining_fields=(
        "recipe_id",
        "objective_artifact_hash",
        "fit_dataset_id",
        "fit_dataset_identity_hash",
        "fit_dataset_role_hash",
        "experiment_id",
        "experiment_hash",
        "owner_fit_authorization_ref",
        "scope_timeline_id",
        "scope_axis",
        "scope_representation_id",
        "candidate_policy_witness_refs",
        "fit_cutoff_key",
    ),
)

CALIBRATION_RECEIPT_IDENTITY_SCHEMA = ArtifactIdentitySchema(
    artifact_type="MUF_S4_POLICY_CALIBRATION_RECEIPT",
    schema_identity=S4_SCHEMA_IDENTITY,
    identity_defining_fields=(
        "receipt_id",
        "recipe_hash",
        "outcome_status",
        "selected_policy_hash",
        "tied_policy_witness_refs",
    ),
    proof_fields=(
        "scorecards",
        "updated_role_exposure_state",
        "updated_experiment_status",
    ),
)


def _require_non_empty_str(val: Any, name: str, err_code: str) -> str:
    if not isinstance(val, str) or not val.strip():
        raise SchemaViolation(f"{err_code}: {name} must be a non-empty string")
    return val


def _serialize_seq(items: Sequence[str]) -> Mapping[str, str]:
    return {f"i_{idx}": val for idx, val in enumerate(items)}


@dataclass(frozen=True)
class PolicyCandidateScoreCard(ImmutableRecord):
    """Deterministic evaluation scorecard for one candidate detector policy on DEVELOPMENT_FIT."""

    candidate_policy_witness_ref: str
    policy_spec: DetectorPolicyWitnessSpec
    confirmed_swing_count: int
    candidate_observation_count: int
    objective_metric: Union[MetricResult, TypedState]
    constraint_satisfied: bool
    evaluation_cutoff_key: InformationKey

    def __post_init__(self) -> None:
        _require_non_empty_str(
            self.candidate_policy_witness_ref,
            "candidate_policy_witness_ref",
            S4_INVALID_SCORECARD,
        )
        if not isinstance(self.policy_spec, DetectorPolicyWitnessSpec):
            raise SchemaViolation(
                f"{S4_INVALID_SCORECARD}: policy_spec must be a DetectorPolicyWitnessSpec"
            )
        if str(self.policy_spec.spec_identity) != self.candidate_policy_witness_ref:
            raise SchemaViolation(
                f"{S4_INVALID_SCORECARD}: candidate_policy_witness_ref does not match "
                "policy_spec.spec_identity"
            )
        if (
            isinstance(self.confirmed_swing_count, bool)
            or not isinstance(self.confirmed_swing_count, int)
            or self.confirmed_swing_count < 0
        ):
            raise SchemaViolation(
                f"{S4_INVALID_SCORECARD}: confirmed_swing_count must be a non-negative int"
            )
        if (
            isinstance(self.candidate_observation_count, bool)
            or not isinstance(self.candidate_observation_count, int)
            or self.candidate_observation_count <= 0
        ):
            raise SchemaViolation(
                f"{S4_INVALID_SCORECARD}: candidate_observation_count must be a positive int"
            )
        if isinstance(self.objective_metric, MetricResult):
            if self.objective_metric.semantics != EXACT:
                raise SchemaViolation(
                    f"{S4_INVALID_SCORECARD}: objective_metric must be EXACT when defined"
                )
        elif self.objective_metric is not TypedState.UNDEFINED:
            raise SchemaViolation(
                f"{S4_INVALID_SCORECARD}: objective_metric must be MetricResult or TypedState.UNDEFINED"
            )
        if not isinstance(self.constraint_satisfied, bool):
            raise SchemaViolation(
                f"{S4_INVALID_SCORECARD}: constraint_satisfied must be a bool"
            )
        if not isinstance(self.evaluation_cutoff_key, InformationKey):
            raise InformationKeyViolation(
                f"{S4_INVALID_SCORECARD}: evaluation_cutoff_key must be an InformationKey"
            )
        if (
            self.evaluation_cutoff_key.information_phase
            == InformationPhase.BAR_PRE_CLOSE
        ):
            raise IllegalCausalReference(
                f"{S4_INVALID_SCORECARD}: evaluation_cutoff_key cannot be BAR_PRE_CLOSE"
            )


@dataclass(frozen=True)
class PolicyCalibrationRecipe(ImmutableRecord):
    """Canonical reproduction recipe for an S4 DEVELOPMENT_FIT policy calibration."""

    recipe_id: str
    g0_certificate: G0CalibrationGateCertificate
    objective_artifact_hash: str
    fit_dataset_id: str
    fit_dataset_identity_hash: str
    fit_dataset_role_hash: str
    experiment_id: str
    experiment_hash: str
    owner_fit_authorization_ref: str
    scope_timeline_id: str
    scope_axis: InformationAxis
    scope_representation_id: str
    candidate_policy_witness_refs: Tuple[str, ...]
    fit_cutoff_key: InformationKey
    recipe_hash: str

    def __post_init__(self) -> None:
        _require_non_empty_str(
            self.recipe_id, "recipe_id", S4_INVALID_CALIBRATION_RECIPE
        )
        if not isinstance(self.g0_certificate, G0CalibrationGateCertificate):
            raise SelectionBlockedError(
                f"{S4_MISSING_OR_MISMATCHED_G0_CERTIFICATE}: g0_certificate must be "
                "a G0CalibrationGateCertificate"
            )
        if (
            self.g0_certificate.objective_artifact_hash != self.objective_artifact_hash
            or self.g0_certificate.fit_dataset_id != self.fit_dataset_id
            or self.g0_certificate.fit_dataset_identity_hash
            != self.fit_dataset_identity_hash
            or self.g0_certificate.fit_dataset_role_hash != self.fit_dataset_role_hash
            or self.g0_certificate.experiment_id != self.experiment_id
            or self.g0_certificate.experiment_hash != self.experiment_hash
            or self.g0_certificate.owner_fit_authorization_ref
            != self.owner_fit_authorization_ref
        ):
            raise SelectionBlockedError(
                f"{S4_MISSING_OR_MISMATCHED_G0_CERTIFICATE}: recipe fields do not match "
                "g0_certificate"
            )
        _require_non_empty_str(
            self.scope_timeline_id,
            "scope_timeline_id",
            S4_INVALID_CALIBRATION_RECIPE,
        )
        if not isinstance(self.scope_axis, InformationAxis):
            raise SchemaViolation(
                f"{S4_INVALID_CALIBRATION_RECIPE}: scope_axis must be an InformationAxis"
            )
        _require_non_empty_str(
            self.scope_representation_id,
            "scope_representation_id",
            S4_INVALID_CALIBRATION_RECIPE,
        )
        cand_tuple = tuple(self.candidate_policy_witness_refs)
        if len(cand_tuple) == 0:
            raise SchemaViolation(
                f"{S4_EMPTY_CANDIDATE_POLICY_SET}: candidate_policy_witness_refs must be non-empty"
            )
        if len(set(cand_tuple)) != len(cand_tuple):
            raise SchemaViolation(
                f"{S4_DUPLICATE_CANDIDATE_POLICY}: duplicate candidate_policy_witness_refs"
            )
        for ref in cand_tuple:
            _require_non_empty_str(
                ref, "candidate_policy_witness_refs[]", S4_INVALID_CALIBRATION_RECIPE
            )
        object.__setattr__(self, "candidate_policy_witness_refs", cand_tuple)

        if not isinstance(self.fit_cutoff_key, InformationKey):
            raise InformationKeyViolation(
                f"{S4_INVALID_CALIBRATION_RECIPE}: fit_cutoff_key must be an InformationKey"
            )
        if self.fit_cutoff_key.information_phase == InformationPhase.BAR_PRE_CLOSE:
            raise IllegalCausalReference(
                f"{S4_INVALID_CALIBRATION_RECIPE}: fit_cutoff_key cannot be BAR_PRE_CLOSE"
            )
        if self.fit_cutoff_key.timeline_id != self.scope_timeline_id:
            raise InformationKeyViolation(
                f"{S4_INVALID_CALIBRATION_RECIPE}: fit_cutoff_key timeline mismatch"
            )
        if key_axis(self.fit_cutoff_key) is not self.scope_axis:
            raise IncomparableInformationKeys(
                f"{S4_INVALID_CALIBRATION_RECIPE}: fit_cutoff_key axis mismatch"
            )

        expected_hash = canonical_artifact_identity(
            CALIBRATION_RECIPE_IDENTITY_SCHEMA,
            identity_payload={
                "recipe_id": self.recipe_id,
                "objective_artifact_hash": self.objective_artifact_hash,
                "fit_dataset_id": self.fit_dataset_id,
                "fit_dataset_identity_hash": self.fit_dataset_identity_hash,
                "fit_dataset_role_hash": self.fit_dataset_role_hash,
                "experiment_id": self.experiment_id,
                "experiment_hash": self.experiment_hash,
                "owner_fit_authorization_ref": self.owner_fit_authorization_ref,
                "scope_timeline_id": self.scope_timeline_id,
                "scope_axis": self.scope_axis.value,
                "scope_representation_id": self.scope_representation_id,
                "candidate_policy_witness_refs": _serialize_seq(cand_tuple),
                "fit_cutoff_key": self.fit_cutoff_key,
            },
        )
        if self.recipe_hash != expected_hash:
            raise SchemaViolation(
                f"{S4_INVALID_CALIBRATION_RECIPE}: recipe_hash mismatch"
            )

    @classmethod
    def create(
        cls,
        *,
        recipe_id: str,
        g0_certificate: G0CalibrationGateCertificate,
        scope_timeline_id: str,
        scope_axis: InformationAxis,
        scope_representation_id: str,
        candidate_policy_witness_refs: Sequence[str],
        fit_cutoff_key: InformationKey,
    ) -> "PolicyCalibrationRecipe":
        if not isinstance(g0_certificate, G0CalibrationGateCertificate):
            raise SelectionBlockedError(
                f"{S4_MISSING_OR_MISMATCHED_G0_CERTIFICATE}: g0_certificate must be "
                "a G0CalibrationGateCertificate"
            )
        if not isinstance(scope_axis, InformationAxis):
            raise SchemaViolation(
                f"{S4_INVALID_CALIBRATION_RECIPE}: scope_axis must be an InformationAxis"
            )
        cand_tuple = tuple(candidate_policy_witness_refs)
        r_hash = canonical_artifact_identity(
            CALIBRATION_RECIPE_IDENTITY_SCHEMA,
            identity_payload={
                "recipe_id": recipe_id,
                "objective_artifact_hash": g0_certificate.objective_artifact_hash,
                "fit_dataset_id": g0_certificate.fit_dataset_id,
                "fit_dataset_identity_hash": g0_certificate.fit_dataset_identity_hash,
                "fit_dataset_role_hash": g0_certificate.fit_dataset_role_hash,
                "experiment_id": g0_certificate.experiment_id,
                "experiment_hash": g0_certificate.experiment_hash,
                "owner_fit_authorization_ref": g0_certificate.owner_fit_authorization_ref,
                "scope_timeline_id": scope_timeline_id,
                "scope_axis": scope_axis.value,
                "scope_representation_id": scope_representation_id,
                "candidate_policy_witness_refs": _serialize_seq(cand_tuple),
                "fit_cutoff_key": fit_cutoff_key,
            },
        )
        return cls(
            recipe_id=recipe_id,
            g0_certificate=g0_certificate,
            objective_artifact_hash=g0_certificate.objective_artifact_hash,
            fit_dataset_id=g0_certificate.fit_dataset_id,
            fit_dataset_identity_hash=g0_certificate.fit_dataset_identity_hash,
            fit_dataset_role_hash=g0_certificate.fit_dataset_role_hash,
            experiment_id=g0_certificate.experiment_id,
            experiment_hash=g0_certificate.experiment_hash,
            owner_fit_authorization_ref=g0_certificate.owner_fit_authorization_ref,
            scope_timeline_id=scope_timeline_id,
            scope_axis=scope_axis,
            scope_representation_id=scope_representation_id,
            candidate_policy_witness_refs=cand_tuple,
            fit_cutoff_key=fit_cutoff_key,
            recipe_hash=r_hash,
        )


@dataclass(frozen=True)
class PolicyCalibrationReceipt(ImmutableRecord):
    """Immutable receipt of an S4 DEVELOPMENT_FIT policy calibration run."""

    receipt_id: str
    recipe: PolicyCalibrationRecipe
    scorecards: Tuple[PolicyCandidateScoreCard, ...]
    outcome_status: str
    selected_policy_artifact: Union[PolicyArtifact, TypedState]
    tied_policy_witness_refs: Tuple[str, ...]
    updated_fit_dataset_role: DatasetRoleArtifact
    updated_experiment_record: RepresentationExperimentRecord
    receipt_hash: str

    def __post_init__(self) -> None:
        _require_non_empty_str(
            self.receipt_id, "receipt_id", S4_INVALID_CALIBRATION_RECEIPT
        )
        if not isinstance(self.recipe, PolicyCalibrationRecipe):
            raise SchemaViolation(
                f"{S4_INVALID_CALIBRATION_RECEIPT}: recipe must be a PolicyCalibrationRecipe"
            )
        sc_tuple = tuple(self.scorecards)
        if len(sc_tuple) == 0:
            raise SchemaViolation(
                f"{S4_INVALID_CALIBRATION_RECEIPT}: scorecards must be non-empty"
            )
        for sc in sc_tuple:
            if not isinstance(sc, PolicyCandidateScoreCard):
                raise SchemaViolation(
                    f"{S4_INVALID_CALIBRATION_RECEIPT}: scorecards must contain PolicyCandidateScoreCard"
                )
        object.__setattr__(self, "scorecards", sc_tuple)

        if self.outcome_status not in LEGAL_CALIBRATION_OUTCOMES:
            raise SchemaViolation(
                f"{S4_INVALID_CALIBRATION_RECEIPT}: invalid outcome_status {self.outcome_status!r}"
            )
        tied_tuple = tuple(self.tied_policy_witness_refs)
        object.__setattr__(self, "tied_policy_witness_refs", tied_tuple)

        if self.outcome_status == CALIBRATION_OUTCOME_UNIQUE:
            if not isinstance(self.selected_policy_artifact, PolicyArtifact):
                raise SchemaViolation(
                    f"{S4_INVALID_CALIBRATION_RECEIPT}: CALIBRATED_UNIQUE requires "
                    "selected_policy_artifact to be a PolicyArtifact"
                )
            if len(tied_tuple) != 0:
                raise SchemaViolation(
                    f"{S4_INVALID_CALIBRATION_RECEIPT}: CALIBRATED_UNIQUE requires empty tied_policy_witness_refs"
                )
            if (
                self.selected_policy_artifact.reproduction_recipe_hash
                != self.recipe.recipe_hash
            ):
                raise SchemaViolation(
                    f"{S4_INVALID_CALIBRATION_RECEIPT}: selected_policy_artifact.reproduction_recipe_hash "
                    "does not match recipe.recipe_hash"
                )
            sel_hash: Union[str, TypedState] = self.selected_policy_artifact.policy_hash
        elif self.outcome_status == CALIBRATION_OUTCOME_TIE_NO_WINNER:
            if self.selected_policy_artifact is not TypedState.UNDEFINED:
                raise SchemaViolation(
                    f"{S4_INVALID_CALIBRATION_RECEIPT}: TIE_PRESERVED_NO_WINNER requires "
                    "selected_policy_artifact = TypedState.UNDEFINED"
                )
            if len(tied_tuple) <= 1:
                raise SchemaViolation(
                    f"{S4_INVALID_CALIBRATION_RECEIPT}: TIE_PRESERVED_NO_WINNER requires multiple tied candidates"
                )
            sel_hash = TypedState.UNDEFINED
        else:
            if self.selected_policy_artifact is not TypedState.UNDEFINED:
                raise SchemaViolation(
                    f"{S4_INVALID_CALIBRATION_RECEIPT}: NO_CANDIDATE_SATISFIED_OBJECTIVE requires "
                    "selected_policy_artifact = TypedState.UNDEFINED"
                )
            if len(tied_tuple) != 0:
                raise SchemaViolation(
                    f"{S4_INVALID_CALIBRATION_RECEIPT}: NO_CANDIDATE_SATISFIED_OBJECTIVE requires "
                    "empty tied_policy_witness_refs"
                )
            sel_hash = TypedState.UNDEFINED

        if not isinstance(self.updated_fit_dataset_role, DatasetRoleArtifact):
            raise SchemaViolation(
                f"{S4_INVALID_CALIBRATION_RECEIPT}: updated_fit_dataset_role must be a DatasetRoleArtifact"
            )
        if not isinstance(
            self.updated_experiment_record, RepresentationExperimentRecord
        ):
            raise SchemaViolation(
                f"{S4_INVALID_CALIBRATION_RECEIPT}: updated_experiment_record must be a RepresentationExperimentRecord"
            )

        sc_ser = {
            f"sc_{idx}": {
                "ref": sc.candidate_policy_witness_ref,
                "swings": sc.confirmed_swing_count,
                "obs": sc.candidate_observation_count,
                "metric": (
                    metric_payload(sc.objective_metric)
                    if isinstance(sc.objective_metric, MetricResult)
                    else sc.objective_metric
                ),
                "satisfied": sc.constraint_satisfied,
            }
            for idx, sc in enumerate(sc_tuple)
        }
        expected_hash = canonical_artifact_identity(
            CALIBRATION_RECEIPT_IDENTITY_SCHEMA,
            identity_payload={
                "receipt_id": self.receipt_id,
                "recipe_hash": self.recipe.recipe_hash,
                "outcome_status": self.outcome_status,
                "selected_policy_hash": sel_hash,
                "tied_policy_witness_refs": _serialize_seq(tied_tuple),
            },
            proof_payload={
                "scorecards": sc_ser,
                "updated_role_exposure_state": self.updated_fit_dataset_role.exposure_state,
                "updated_experiment_status": self.updated_experiment_record.status,
            },
        )
        if self.receipt_hash != expected_hash:
            raise SchemaViolation(
                f"{S4_INVALID_CALIBRATION_RECEIPT}: receipt_hash mismatch"
            )


def validate_development_fit_bar_stream(
    bars: Sequence[PublishedOhlcBarFact],
    *,
    fit_dataset_identity: DatasetIdentityArtifact,
    fit_dataset_role: DatasetRoleArtifact,
    fit_cutoff_key: Optional[InformationKey] = None,
) -> Tuple[Tuple[PublishedOhlcBarFact, ...], InformationKey]:
    """Validate that a bar stream belongs strictly to a DEVELOPMENT_FIT dataset within [start_key, cutoff_key].

    Fails closed if any bar comes from another dataset (such as DEVELOPMENT_SELECTION
    or FINAL_EVALUATION_LOCKED), violates causal ordering, or lies outside
    ``[fit_dataset_identity.start_key, effective_cutoff_key]``.
    """
    if not isinstance(fit_dataset_identity, DatasetIdentityArtifact) or not isinstance(
        fit_dataset_role, DatasetRoleArtifact
    ):
        raise SelectionBlockedError(
            f"{S4_INVALID_FIT_BAR_STREAM}: fit_dataset_identity and fit_dataset_role required"
        )
    if (
        fit_dataset_role.dataset_id != fit_dataset_identity.dataset_id
        or fit_dataset_role.dataset_identity_hash
        != fit_dataset_identity.dataset_identity_hash
    ):
        raise SelectionBlockedError(
            f"{S4_INVALID_FIT_BAR_STREAM}: fit_dataset_role does not match fit_dataset_identity"
        )
    if fit_dataset_role.role != DATASET_ROLE_DEVELOPMENT_FIT:
        raise SelectionBlockedError(
            f"{S4_FIT_STREAM_OUTSIDE_DECLARED_DATASET}: calibration requires DEVELOPMENT_FIT role, "
            f"got {fit_dataset_role.role!r}"
        )
    if fit_dataset_role.exposure_state not in (
        EXPOSURE_STATE_UNEXPOSED,
        EXPOSURE_STATE_EXPOSED_DEVELOPMENT,
    ):
        raise SelectionBlockedError(
            f"{S4_FIT_STREAM_OUTSIDE_DECLARED_DATASET}: invalid exposure_state "
            f"{fit_dataset_role.exposure_state!r}"
        )

    effective_cutoff = (
        fit_dataset_identity.end_key if fit_cutoff_key is None else fit_cutoff_key
    )
    if not isinstance(effective_cutoff, InformationKey):
        raise InformationKeyViolation(
            f"{S4_INVALID_FIT_BAR_STREAM}: fit_cutoff_key must be an InformationKey"
        )
    if effective_cutoff.information_phase == InformationPhase.BAR_PRE_CLOSE:
        raise IllegalCausalReference(
            f"{S4_INVALID_FIT_BAR_STREAM}: fit_cutoff_key cannot be BAR_PRE_CLOSE"
        )
    if effective_cutoff.timeline_id != fit_dataset_identity.timeline_id:
        raise InformationKeyViolation(
            f"{S4_INVALID_FIT_BAR_STREAM}: fit_cutoff_key timeline mismatch"
        )
    if key_axis(effective_cutoff) is not fit_dataset_identity.axis:
        raise IncomparableInformationKeys(
            f"{S4_INVALID_FIT_BAR_STREAM}: fit_cutoff_key axis mismatch"
        )
    try:
        cutoff_in_bounds = (
            fit_dataset_identity.start_key
            <= effective_cutoff
            <= fit_dataset_identity.end_key
        )
    except InformationKeyError as exc:
        raise IncomparableInformationKeys(str(exc)) from exc
    if not cutoff_in_bounds:
        raise PrematureAvailability(
            f"{S4_FIT_STREAM_OUTSIDE_DECLARED_DATASET}: fit_cutoff_key must lie within "
            "[fit_dataset_identity.start_key, fit_dataset_identity.end_key]"
        )

    if isinstance(bars, (str, bytes)) or not isinstance(bars, Sequence):
        raise SchemaViolation(
            f"{S4_INVALID_FIT_BAR_STREAM}: bars must be a sequence of PublishedOhlcBarFact"
        )
    bar_tuple = tuple(bars)
    if len(bar_tuple) == 0:
        raise SchemaViolation(
            f"{S4_INVALID_FIT_BAR_STREAM}: bars must be non-empty"
        )

    prev_key: Optional[InformationKey] = None
    for idx, bar in enumerate(bar_tuple):
        if not isinstance(bar, PublishedOhlcBarFact):
            raise SchemaViolation(
                f"{S4_INVALID_FIT_BAR_STREAM}: element at index {idx} is not a PublishedOhlcBarFact"
            )
        if bar.dataset_identity != fit_dataset_identity.dataset_id:
            raise SelectionBlockedError(
                f"{S4_FIT_STREAM_OUTSIDE_DECLARED_DATASET}: bar at index {idx} has dataset_identity "
                f"{bar.dataset_identity!r} != {fit_dataset_identity.dataset_id!r}"
            )
        if bar.source_identity != fit_dataset_identity.source_identity:
            raise SchemaViolation(
                f"{S4_INVALID_FIT_BAR_STREAM}: bar at index {idx} source_identity mismatch"
            )
        b_key = bar.availability_key
        if b_key.timeline_id != fit_dataset_identity.timeline_id:
            raise InformationKeyViolation(
                f"{S4_INVALID_FIT_BAR_STREAM}: bar at index {idx} timeline mismatch"
            )
        if key_axis(b_key) is not fit_dataset_identity.axis:
            raise IncomparableInformationKeys(
                f"{S4_INVALID_FIT_BAR_STREAM}: bar at index {idx} axis mismatch"
            )
        try:
            after_start = fit_dataset_identity.start_key <= b_key
            before_cutoff = b_key <= effective_cutoff
        except InformationKeyError as exc:
            raise IncomparableInformationKeys(str(exc)) from exc
        if not after_start or not before_cutoff:
            raise PrematureAvailability(
                f"{S4_FIT_STREAM_OUTSIDE_DECLARED_DATASET}: bar at index {idx} lies outside "
                "[start_key, fit_cutoff_key]"
            )
        require_visible_at(fact_key=b_key, at_key=effective_cutoff)
        if prev_key is not None:
            try:
                strictly_increasing = prev_key < b_key
            except InformationKeyError as exc:
                raise IncomparableInformationKeys(str(exc)) from exc
            if not strictly_increasing:
                raise SchemaViolation(
                    f"{S4_INVALID_FIT_BAR_STREAM}: bar stream is not strictly increasing at index {idx}"
                )
        prev_key = b_key

    return bar_tuple, effective_cutoff


ObjectiveEvaluatorFn = Callable[
    [DetectorWitnessBundle, ObjectiveArtifact],
    Tuple[Union[MetricResult, TypedState], bool],
]


def _evaluate_candidate_scorecards(
    validated_bars: Tuple[PublishedOhlcBarFact, ...],
    *,
    candidate_policies: Sequence[SwingConfirmationPolicy],
    objective_artifact: ObjectiveArtifact,
    objective_evaluator: ObjectiveEvaluatorFn,
    effective_cutoff: InformationKey,
) -> Tuple[PolicyCandidateScoreCard, ...]:
    if len(candidate_policies) == 0:
        raise SchemaViolation(
            f"{S4_EMPTY_CANDIDATE_POLICY_SET}: candidate_policies must be non-empty"
        )
    seen_refs: set[str] = set()
    cards: list[PolicyCandidateScoreCard] = []
    for pol in candidate_policies:
        if not isinstance(pol, SwingConfirmationPolicy):
            raise SchemaViolation(
                f"{S4_EMPTY_CANDIDATE_POLICY_SET}: each candidate policy must be a SwingConfirmationPolicy"
            )
        spec = DetectorPolicyWitnessSpec.from_policy(pol)
        ref = str(spec.spec_identity)
        if ref in seen_refs:
            raise SchemaViolation(
                f"{S4_DUPLICATE_CANDIDATE_POLICY}: duplicate candidate policy witness ref {ref!r}"
            )
        seen_refs.add(ref)

        bundle = adapt_detector_witness_stream(
            validated_bars, confirmation_policy=pol
        )
        eval_out = objective_evaluator(bundle, objective_artifact)
        if not isinstance(eval_out, tuple):
            raise SchemaViolation(
                f"{S4_INVALID_OBJECTIVE_EVALUATOR_OUTPUT}: objective_evaluator must return "
                "(MetricResult | TypedState.UNDEFINED, bool)"
            )
        try:
            metric_val, satisfied, *extra_eval_items = eval_out
        except ValueError as exc:
            raise SchemaViolation(
                f"{S4_INVALID_OBJECTIVE_EVALUATOR_OUTPUT}: objective_evaluator must return "
                "(MetricResult | TypedState.UNDEFINED, bool)"
            ) from exc
        if len(extra_eval_items) != 0:
            raise SchemaViolation(
                f"{S4_INVALID_OBJECTIVE_EVALUATOR_OUTPUT}: objective_evaluator must return "
                "(MetricResult | TypedState.UNDEFINED, bool)"
            )
        if not isinstance(satisfied, bool):
            raise SchemaViolation(
                f"{S4_INVALID_OBJECTIVE_EVALUATOR_OUTPUT}: constraint_satisfied must be a bool"
            )
        if isinstance(metric_val, MetricResult):
            if (
                metric_val.semantics != EXACT
                or not isinstance(metric_val.value, float)
                or not math.isfinite(metric_val.value)
            ):
                raise SchemaViolation(
                    f"{S4_INVALID_OBJECTIVE_EVALUATOR_OUTPUT}: MetricResult must be finite EXACT"
                )
        elif metric_val is not TypedState.UNDEFINED:
            raise SchemaViolation(
                f"{S4_INVALID_OBJECTIVE_EVALUATOR_OUTPUT}: metric must be MetricResult or TypedState.UNDEFINED"
            )

        cards.append(
            PolicyCandidateScoreCard(
                candidate_policy_witness_ref=ref,
                policy_spec=spec,
                confirmed_swing_count=len(bundle.swing_event_witnesses),
                candidate_observation_count=len(bundle.candidate_witnesses),
                objective_metric=metric_val,
                constraint_satisfied=satisfied,
                evaluation_cutoff_key=effective_cutoff,
            )
        )
    return tuple(cards)


def _select_from_scorecards(
    scorecards: Tuple[PolicyCandidateScoreCard, ...],
    *,
    objective_artifact: ObjectiveArtifact,
) -> Tuple[str, Optional[PolicyCandidateScoreCard], Tuple[str, ...]]:
    satisfied_cards = [sc for sc in scorecards if sc.constraint_satisfied]
    if len(satisfied_cards) == 0:
        return CALIBRATION_OUTCOME_NONE_SATISFIED, None, ()

    comp_dir = objective_artifact.comparison_direction
    if comp_dir in (TypedState.NOT_APPLICABLE, "SATISFY_CONSTRAINT"):
        if len(satisfied_cards) == 1:
            return CALIBRATION_OUTCOME_UNIQUE, satisfied_cards[0], ()
        return (
            CALIBRATION_OUTCOME_TIE_NO_WINNER,
            None,
            tuple(sc.candidate_policy_witness_ref for sc in satisfied_cards),
        )

    # MAXIMIZE or MINIMIZE requires defined MetricResult on all satisfied candidates
    for sc in satisfied_cards:
        if not isinstance(sc.objective_metric, MetricResult):
            raise SchemaViolation(
                f"{S4_INVALID_OBJECTIVE_EVALUATOR_OUTPUT}: {comp_dir} objective requires "
                "defined MetricResult on all constraint-satisfying candidates"
            )

    if comp_dir == "MAXIMIZE":
        best_val = max(
            sc.objective_metric.value  # type: ignore[union-attr]
            for sc in satisfied_cards
        )
    else:
        best_val = min(
            sc.objective_metric.value  # type: ignore[union-attr]
            for sc in satisfied_cards
        )

    winners = [
        sc
        for sc in satisfied_cards
        if sc.objective_metric.value == best_val  # type: ignore[union-attr]
    ]
    if len(winners) == 1:
        return CALIBRATION_OUTCOME_UNIQUE, winners[0], ()
    return (
        CALIBRATION_OUTCOME_TIE_NO_WINNER,
        None,
        tuple(sc.candidate_policy_witness_ref for sc in winners),
    )


def calibrate_development_policy_artifact(
    bars: Sequence[PublishedOhlcBarFact],
    *,
    recipe_id: str,
    receipt_id: str,
    policy_id: str,
    g0_certificate: Any,
    objective_artifact: Any = QUALIFICATION_OBJECTIVE_DEFAULT,
    fit_dataset_identity: Any = TypedState.NOT_CONFIGURED,
    fit_dataset_role: Any = TypedState.NOT_CONFIGURED,
    known_dataset_identities: Sequence[DatasetIdentityArtifact] = (),
    known_dataset_roles: Optional[Mapping[str, DatasetRoleArtifact]] = None,
    experiment_registry: Optional[ExperimentRegistry] = None,
    experiment_id: Union[str, TypedState] = TypedState.NOT_CONFIGURED,
    owner_fit_authorization_ref: Union[str, TypedState] = TypedState.NOT_CONFIGURED,
    scope_representation_id: str,
    candidate_policies: Sequence[SwingConfirmationPolicy],
    objective_evaluator: ObjectiveEvaluatorFn,
    fit_cutoff_key: Optional[InformationKey] = None,
) -> PolicyCalibrationReceipt:
    """Execute a G0-gated DEVELOPMENT_FIT policy calibration and emit an immutable receipt.

    Enforces:
    1. Gate G0 re-verification + exact match against ``g0_certificate``;
    2. Objective kind in ``{DETECTION_VALIDITY, REPRESENTATION_DIAGNOSTIC}``;
    3. ``DEVELOPMENT_FIT`` bar stream causal & boundary validation;
    4. Automatic ``ExperimentRegistry`` transition and ``DatasetRoleArtifact`` exposure logging;
    5. Tie preservation without inventing a winner when multiple candidates tie.
    """
    if not isinstance(g0_certificate, G0CalibrationGateCertificate):
        raise SelectionBlockedError(
            f"{S4_MISSING_OR_MISMATCHED_G0_CERTIFICATE}: valid G0CalibrationGateCertificate required"
        )

    # Re-evaluate Gate G0 on live governance artifacts
    live_g0 = evaluate_g0_calibration_gate(
        objective_artifact=objective_artifact,
        fit_dataset_identity=fit_dataset_identity,
        fit_dataset_role=fit_dataset_role,
        known_dataset_identities=known_dataset_identities,
        known_dataset_roles=known_dataset_roles,
        experiment_registry=experiment_registry,
        experiment_id=experiment_id,
        owner_fit_authorization_ref=owner_fit_authorization_ref,
    )
    if live_g0 != g0_certificate:
        raise SelectionBlockedError(
            f"{S4_MISSING_OR_MISMATCHED_G0_CERTIFICATE}: supplied g0_certificate does not match "
            "live G0 gate evaluation"
        )

    assert isinstance(objective_artifact, ObjectiveArtifact)
    assert isinstance(fit_dataset_identity, DatasetIdentityArtifact)
    assert isinstance(fit_dataset_role, DatasetRoleArtifact)
    assert isinstance(experiment_registry, ExperimentRegistry)
    assert isinstance(experiment_id, str)
    assert isinstance(owner_fit_authorization_ref, str)

    if objective_artifact.objective_kind not in (
        OBJECTIVE_KIND_DETECTION_VALIDITY,
        OBJECTIVE_KIND_REPRESENTATION_DIAGNOSTIC,
    ):
        raise SelectionBlockedError(
            f"{S4_INFORMATION_OBJECTIVE_NOT_VALID_FOR_DETECTOR_FIT}: S4 detector policy "
            f"calibration requires DETECTION_VALIDITY or REPRESENTATION_DIAGNOSTIC objective, "
            f"got {objective_artifact.objective_kind!r}"
        )

    validated_bars, effective_cutoff = validate_development_fit_bar_stream(
        bars,
        fit_dataset_identity=fit_dataset_identity,
        fit_dataset_role=fit_dataset_role,
        fit_cutoff_key=fit_cutoff_key,
    )

    scorecards = _evaluate_candidate_scorecards(
        validated_bars,
        candidate_policies=candidate_policies,
        objective_artifact=objective_artifact,
        objective_evaluator=objective_evaluator,
        effective_cutoff=effective_cutoff,
    )

    recipe = PolicyCalibrationRecipe.create(
        recipe_id=recipe_id,
        g0_certificate=g0_certificate,
        scope_timeline_id=fit_dataset_identity.timeline_id,
        scope_axis=fit_dataset_identity.axis,
        scope_representation_id=scope_representation_id,
        candidate_policy_witness_refs=tuple(
            sc.candidate_policy_witness_ref for sc in scorecards
        ),
        fit_cutoff_key=effective_cutoff,
    )

    # Record RUNNING transition if currently PREREGISTERED
    current_exp = experiment_registry.get(experiment_id)
    if current_exp.status == EXPERIMENT_STATUS_PREREGISTERED:
        experiment_registry.record_transition(
            experiment_id=experiment_id,
            new_status=EXPERIMENT_STATUS_RUNNING,
            transition_key=effective_cutoff,
        )

    # Record DEVELOPMENT_FIT dataset exposure
    updated_role = record_dataset_exposure(
        fit_dataset_role,
        event_id=f"s4_fit:{receipt_id}",
        exposure_key=effective_cutoff,
        exposure_kind="S4_DEVELOPMENT_POLICY_CALIBRATION",
        actor_or_protocol_ref=recipe.recipe_hash,
    )

    outcome_status, winner_card, tied_refs = _select_from_scorecards(
        scorecards,
        objective_artifact=objective_artifact,
    )

    if outcome_status == CALIBRATION_OUTCOME_UNIQUE:
        assert winner_card is not None
        pol_art: Union[PolicyArtifact, TypedState] = PolicyArtifact.create(
            policy_id=policy_id,
            authority_kind=POLICY_AUTHORITY_KIND_MUF,
            target_engine_identity=S2_ADAPTER_ENGINE_IDENTITY,
            detector_policy_witness_ref=winner_card.candidate_policy_witness_ref,
            scope_timeline_id=fit_dataset_identity.timeline_id,
            scope_axis=fit_dataset_identity.axis,
            scope_representation_id=scope_representation_id,
            calibration_provenance_kind=PROVENANCE_DEVELOPMENT_FIT,
            fit_dataset_id=fit_dataset_identity.dataset_id,
            objective_artifact_hash=objective_artifact.objective_hash,
            experiment_id=experiment_id,
            fit_dataset_role_hash=fit_dataset_role.role_artifact_hash,
            reproduction_recipe_hash=recipe.recipe_hash,
            effective_from_key=effective_cutoff,
            owner_authorization_ref=owner_fit_authorization_ref,
        )
        updated_exp = experiment_registry.record_transition(
            experiment_id=experiment_id,
            new_status=EXPERIMENT_STATUS_COMPLETED,
            transition_key=effective_cutoff,
            result_refs=(pol_art.policy_hash,),
        )
        sel_hash: Union[str, TypedState] = pol_art.policy_hash
    elif outcome_status == CALIBRATION_OUTCOME_TIE_NO_WINNER:
        pol_art = TypedState.UNDEFINED
        updated_exp = experiment_registry.record_transition(
            experiment_id=experiment_id,
            new_status=EXPERIMENT_STATUS_COMPLETED,
            transition_key=effective_cutoff,
            result_refs=tied_refs,
        )
        sel_hash = TypedState.UNDEFINED
    else:
        pol_art = TypedState.UNDEFINED
        updated_exp = experiment_registry.record_transition(
            experiment_id=experiment_id,
            new_status=EXPERIMENT_STATUS_FAILED,
            transition_key=effective_cutoff,
            failure_refs=(f"no_candidate_satisfied:{recipe.recipe_hash}",),
        )
        sel_hash = TypedState.UNDEFINED

    sc_ser = {
        f"sc_{idx}": {
            "ref": sc.candidate_policy_witness_ref,
            "swings": sc.confirmed_swing_count,
            "obs": sc.candidate_observation_count,
            "metric": (
                metric_payload(sc.objective_metric)
                if isinstance(sc.objective_metric, MetricResult)
                else sc.objective_metric
            ),
            "satisfied": sc.constraint_satisfied,
        }
        for idx, sc in enumerate(scorecards)
    }
    rec_hash = canonical_artifact_identity(
        CALIBRATION_RECEIPT_IDENTITY_SCHEMA,
        identity_payload={
            "receipt_id": receipt_id,
            "recipe_hash": recipe.recipe_hash,
            "outcome_status": outcome_status,
            "selected_policy_hash": sel_hash,
            "tied_policy_witness_refs": _serialize_seq(tied_refs),
        },
        proof_payload={
            "scorecards": sc_ser,
            "updated_role_exposure_state": updated_role.exposure_state,
            "updated_experiment_status": updated_exp.status,
        },
    )
    return PolicyCalibrationReceipt(
        receipt_id=receipt_id,
        recipe=recipe,
        scorecards=scorecards,
        outcome_status=outcome_status,
        selected_policy_artifact=pol_art,
        tied_policy_witness_refs=tied_refs,
        updated_fit_dataset_role=updated_role,
        updated_experiment_record=updated_exp,
        receipt_hash=rec_hash,
    )


def reproduce_and_verify_calibrated_policy(
    policy_artifact: PolicyArtifact,
    *,
    bars: Sequence[PublishedOhlcBarFact],
    recipe: PolicyCalibrationRecipe,
    objective_artifact: ObjectiveArtifact,
    fit_dataset_identity: DatasetIdentityArtifact,
    fit_dataset_role: DatasetRoleArtifact,
    candidate_policies: Sequence[SwingConfirmationPolicy],
    objective_evaluator: ObjectiveEvaluatorFn,
) -> bool:
    """Re-execute an S4 calibration recipe on ``bars`` and verify exact PolicyArtifact reproduction."""
    if not isinstance(policy_artifact, PolicyArtifact):
        raise SchemaViolation("policy_artifact must be a PolicyArtifact")
    if not isinstance(recipe, PolicyCalibrationRecipe):
        raise SchemaViolation("recipe must be a PolicyCalibrationRecipe")

    if recipe.objective_artifact_hash != objective_artifact.objective_hash:
        raise SchemaViolation(
            f"{S3_POLICY_REPRODUCTION_MISMATCH}: objective_artifact_hash mismatch"
        )
    if (
        recipe.fit_dataset_id != fit_dataset_identity.dataset_id
        or recipe.fit_dataset_identity_hash
        != fit_dataset_identity.dataset_identity_hash
    ):
        raise SchemaViolation(
            f"{S3_POLICY_REPRODUCTION_MISMATCH}: fit_dataset_identity mismatch"
        )

    validated_bars, effective_cutoff = validate_development_fit_bar_stream(
        bars,
        fit_dataset_identity=fit_dataset_identity,
        fit_dataset_role=fit_dataset_role,
        fit_cutoff_key=recipe.fit_cutoff_key,
    )
    scorecards = _evaluate_candidate_scorecards(
        validated_bars,
        candidate_policies=candidate_policies,
        objective_artifact=objective_artifact,
        objective_evaluator=objective_evaluator,
        effective_cutoff=effective_cutoff,
    )
    recomputed_recipe = PolicyCalibrationRecipe.create(
        recipe_id=recipe.recipe_id,
        g0_certificate=recipe.g0_certificate,
        scope_timeline_id=fit_dataset_identity.timeline_id,
        scope_axis=fit_dataset_identity.axis,
        scope_representation_id=recipe.scope_representation_id,
        candidate_policy_witness_refs=tuple(
            sc.candidate_policy_witness_ref for sc in scorecards
        ),
        fit_cutoff_key=effective_cutoff,
    )
    outcome_status, winner_card, _ = _select_from_scorecards(
        scorecards,
        objective_artifact=objective_artifact,
    )
    if outcome_status != CALIBRATION_OUTCOME_UNIQUE or winner_card is None:
        raise SchemaViolation(
            f"{S3_POLICY_REPRODUCTION_MISMATCH}: reproduction did not yield a unique winner "
            f"(outcome_status={outcome_status!r})"
        )

    verify_policy_artifact_reproduction(
        policy_artifact,
        recomputed_detector_policy_witness_ref=winner_card.candidate_policy_witness_ref,
        recomputed_recipe_hash=recomputed_recipe.recipe_hash,
    )

    recomputed_policy = PolicyArtifact.create(
        policy_id=policy_artifact.policy_id,
        authority_kind=policy_artifact.authority_kind,
        target_engine_identity=policy_artifact.target_engine_identity,
        detector_policy_witness_ref=winner_card.candidate_policy_witness_ref,
        scope_timeline_id=fit_dataset_identity.timeline_id,
        scope_axis=fit_dataset_identity.axis,
        scope_representation_id=recipe.scope_representation_id,
        calibration_provenance_kind=PROVENANCE_DEVELOPMENT_FIT,
        fit_dataset_id=fit_dataset_identity.dataset_id,
        objective_artifact_hash=objective_artifact.objective_hash,
        experiment_id=recipe.experiment_id,
        fit_dataset_role_hash=recipe.fit_dataset_role_hash,
        reproduction_recipe_hash=recomputed_recipe.recipe_hash,
        effective_from_key=effective_cutoff,
        owner_authorization_ref=recipe.owner_fit_authorization_ref,
    )
    if recomputed_policy.policy_hash != policy_artifact.policy_hash:
        raise SchemaViolation(
            f"{S3_POLICY_REPRODUCTION_MISMATCH}: recomputed policy_hash mismatch"
        )
    return True


__all__ = [
    "CALIBRATION_OUTCOME_NONE_SATISFIED",
    "CALIBRATION_OUTCOME_TIE_NO_WINNER",
    "CALIBRATION_OUTCOME_UNIQUE",
    "CALIBRATION_RECEIPT_IDENTITY_SCHEMA",
    "CALIBRATION_RECIPE_IDENTITY_SCHEMA",
    "LEGAL_CALIBRATION_OUTCOMES",
    "ObjectiveEvaluatorFn",
    "PolicyCalibrationReceipt",
    "PolicyCalibrationRecipe",
    "PolicyCandidateScoreCard",
    "S4_DUPLICATE_CANDIDATE_POLICY",
    "S4_EMPTY_CANDIDATE_POLICY_SET",
    "S4_FIT_STREAM_OUTSIDE_DECLARED_DATASET",
    "S4_INFORMATION_OBJECTIVE_NOT_VALID_FOR_DETECTOR_FIT",
    "S4_INVALID_CALIBRATION_RECEIPT",
    "S4_INVALID_CALIBRATION_RECIPE",
    "S4_INVALID_FIT_BAR_STREAM",
    "S4_INVALID_OBJECTIVE_EVALUATOR_OUTPUT",
    "S4_INVALID_SCORECARD",
    "S4_MISSING_OR_MISMATCHED_G0_CERTIFICATE",
    "S4_SCHEMA_IDENTITY",
    "calibrate_development_policy_artifact",
    "reproduce_and_verify_calibrated_policy",
    "validate_development_fit_bar_stream",
]
