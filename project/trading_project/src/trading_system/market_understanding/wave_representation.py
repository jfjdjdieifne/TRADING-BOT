"""MUF V1 S5 & Gate G1: Candidate Wave Representation Construction & Structural Qualification.

Implements causal, origin-anchored candidate wave representation construction
on DEVELOPMENT datasets only, plus Gate G1 Structural Qualification
(D1-4, D1-5, D1-6, D1-8, D2-1, D2-2, D2-3, D2-17, D2-22, Correction-1 §1 & §2):
- ``CandidateWaveRepresentationSpec`` (I-SD-1..4, I-WIB-2)
- ``WaveIdentityRecord`` (I-WID-1..3, I-WPI-1..5, I-IDB-1..3, I-EARLY-1..3)
- ``RunningWaveObservationRecord`` (I-DESC-1, I-DE-1)
- ``FinalizedWaveGeometryRecord`` (I-WID-2, I-DE-1)
- ``WaveStatusEventRecord``
- ``CandidateWaveRepresentationBundle`` & ``WaveRepresentationAsOfView``
- ``construct_candidate_wave_representation`` (single-pass O(N) / O(1) per bar)
- ``query_wave_representation_as_of`` & ``verify_wave_prefix_invariance``
- ``StructuralQualificationCriteria``, ``StructuralQualificationRecord``, and
  ``evaluate_g1_structural_qualification`` (Gate G1, I-SEL-1, I-SEL-3)

S5 invents ZERO numerical thresholds, windows, or objectives, forbids
``FINAL_EVALUATION_LOCKED`` datasets, and outputs ``ELIGIBLE / INELIGIBLE``
only at Gate G1 without ever claiming a predictive winner.
"""
from dataclasses import dataclass
import math
from typing import Any, Mapping, Optional, Sequence, Tuple, Union

from trading_system.market_understanding.availability import (
    InformationAxis,
    require_visible_at,
)
from trading_system.market_understanding.contracts import (
    IllegalCausalReference,
    ImmutabilityViolation,
    IncomparableInformationKeys,
    InformationKeyViolation,
    NonEarliestAvailability,
    PrematureAvailability,
    SchemaIdentity,
    SchemaViolation,
    TypedState,
)
from trading_system.market_understanding.detector_witness import (
    DetectorWitnessBundle,
    SwingEventWitnessRecord,
)
from trading_system.market_understanding.identity import (
    ArtifactIdentitySchema,
    WaveIdentityProof,
    WaveProcessIdentityBasis,
    canonical_artifact_identity,
    wave_process_identity,
)
from trading_system.market_understanding.policy_governance import (
    DATASET_ROLE_DEVELOPMENT_FIT,
    DATASET_ROLE_DEVELOPMENT_SELECTION,
    DATASET_ROLE_FINAL_EVALUATION_LOCKED,
    EXPOSURE_STATE_EXPOSED_DEVELOPMENT,
    EXPOSURE_STATE_UNEXPOSED,
    AuthoritativeTurningPointRecord,
    DatasetIdentityArtifact,
    DatasetRoleArtifact,
    PolicyArtifact,
    PolicyScopeMismatch,
    SelectionBlockedError,
    promote_swing_witness_with_policy_artifact,
    record_dataset_exposure,
)
from trading_system.market_understanding.price_path import (
    DIRECTION_DOWN,
    DIRECTION_UP,
    EXACT,
    MetricResult,
    PublishedOhlcBarFact,
    exact_metric,
    key_axis,
    key_serialization,
    metric_payload,
)
from trading_system.market_understanding.records import (
    ImmutableRecord,
    PublishedRecord,
    freeze_payload,
)
from trading_system.research.information_time import (
    InformationKey,
    InformationKeyError,
    InformationPhase,
)


S5_SCHEMA_IDENTITY = SchemaIdentity("MUF_S5_WAVE_REPRESENTATION", "V1")

# Representation families (D1-6, D1-8)
FAMILY_ALPHA_POLICY_SCALE = "ALPHA_POLICY_SCALE"
FAMILY_BETA_PARAMETER_FREE = "BETA_PARAMETER_FREE"
FAMILY_GAMMA_RESIDUAL = "GAMMA_RESIDUAL"
FAMILY_DELTA_EVENT_CONTAINMENT = "DELTA_EVENT_CONTAINMENT"
LEGAL_REPRESENTATION_FAMILIES = frozenset(
    {
        FAMILY_ALPHA_POLICY_SCALE,
        FAMILY_BETA_PARAMETER_FREE,
        FAMILY_GAMMA_RESIDUAL,
        FAMILY_DELTA_EVENT_CONTAINMENT,
    }
)
FAMILIES_FORBIDDING_INTRINSIC_SCALE = frozenset(
    {
        FAMILY_BETA_PARAMETER_FREE,
        FAMILY_DELTA_EVENT_CONTAINMENT,
    }
)

# Wave lifecycle statuses
WAVE_STATUS_FORMING = "FORMING"
WAVE_STATUS_CONFIRMED = "CONFIRMED"
WAVE_STATUS_SUPERSEDED = "SUPERSEDED"
LEGAL_WAVE_STATUSES = frozenset(
    {
        WAVE_STATUS_FORMING,
        WAVE_STATUS_CONFIRMED,
        WAVE_STATUS_SUPERSEDED,
    }
)

# Record types
S5_WAVE_IDENTITY_RECORD_TYPE = "MUF_S5_WAVE_IDENTITY_RECORD"
S5_RUNNING_WAVE_OBSERVATION_RECORD_TYPE = "MUF_S5_RUNNING_WAVE_OBSERVATION"
S5_FINALIZED_WAVE_GEOMETRY_RECORD_TYPE = "MUF_S5_FINALIZED_WAVE_GEOMETRY"
S5_WAVE_STATUS_EVENT_RECORD_TYPE = "MUF_S5_WAVE_STATUS_EVENT"

# Gate G1 qualification statuses & claim boundary (D2-3, I-SEL-1)
G1_STATUS_ELIGIBLE = "ELIGIBLE"
G1_STATUS_INELIGIBLE = "INELIGIBLE"
LEGAL_G1_STATUSES = frozenset({G1_STATUS_ELIGIBLE, G1_STATUS_INELIGIBLE})
G1_CLAIM_BOUNDARY = "STRUCTURAL_ELIGIBILITY_ONLY_NOT_PREDICTIVE_WINNER"

# Deterministic S5 & G1 error reason codes
S5_INVALID_REPRESENTATION_SPEC = "S5_INVALID_REPRESENTATION_SPEC"
S5_INTRINSIC_SCALE_FORBIDDEN_FOR_FAMILY = "S5_INTRINSIC_SCALE_FORBIDDEN_FOR_FAMILY"
S5_INTRINSIC_SCALE_REQUIRED_FOR_ALPHA = "S5_INTRINSIC_SCALE_REQUIRED_FOR_ALPHA"
S5_IDENTITY_RULE_NOT_CONFIGURED = "S5_IDENTITY_RULE_NOT_CONFIGURED"
S5_POLICY_AUTHORITY_MISSING = "S5_POLICY_AUTHORITY_MISSING"
S5_FINAL_DATASET_FORBIDDEN_IN_CANDIDATE_CONSTRUCTION = (
    "S5_FINAL_DATASET_FORBIDDEN_IN_CANDIDATE_CONSTRUCTION"
)
S5_INVALID_DEVELOPMENT_BAR_STREAM = "S5_INVALID_DEVELOPMENT_BAR_STREAM"
S5_NON_EARLIEST_WAVE_AVAILABILITY = "NON_EARLIEST_AVAILABILITY"
S5_INVALID_WAVE_IDENTITY_RECORD = "S5_INVALID_WAVE_IDENTITY_RECORD"
S5_INVALID_RUNNING_OBSERVATION = "S5_INVALID_RUNNING_OBSERVATION"
S5_INVALID_FINALIZED_GEOMETRY = "S5_INVALID_FINALIZED_GEOMETRY"
S5_INVALID_WAVE_STATUS_EVENT = "S5_INVALID_WAVE_STATUS_EVENT"
S5_INVALID_WAVE_BUNDLE = "S5_INVALID_WAVE_BUNDLE"
G1_BLOCKED_FINAL_DATASET_FORBIDDEN = "G1_BLOCKED_FINAL_DATASET_FORBIDDEN"
G1_WINNER_CLAIM_FORBIDDEN = "G1_WINNER_CLAIM_FORBIDDEN"
G1_INVALID_QUALIFICATION_CRITERIA = "G1_INVALID_QUALIFICATION_CRITERIA"
G1_INVALID_QUALIFICATION_RECORD = "G1_INVALID_QUALIFICATION_RECORD"


REPRESENTATION_SPEC_IDENTITY_SCHEMA = ArtifactIdentitySchema(
    artifact_type="MUF_S5_CANDIDATE_WAVE_REPRESENTATION_SPEC",
    schema_identity=S5_SCHEMA_IDENTITY,
    identity_defining_fields=(
        "representation_id",
        "family_kind",
        "scope_timeline_id",
        "scope_axis",
        "intrinsic_scale_key",
        "identity_rule_ref",
    ),
)

RUNNING_WAVE_OBSERVATION_SCHEMA = ArtifactIdentitySchema(
    artifact_type="MUF_S5_RUNNING_WAVE_OBSERVATION",
    schema_identity=S5_SCHEMA_IDENTITY,
    identity_defining_fields=(
        "wave_process_id",
        "timeline_id",
        "observation_position",
        "observation_key",
    ),
)

FINALIZED_WAVE_GEOMETRY_SCHEMA = ArtifactIdentitySchema(
    artifact_type="MUF_S5_FINALIZED_WAVE_GEOMETRY",
    schema_identity=S5_SCHEMA_IDENTITY,
    identity_defining_fields=(
        "wave_process_id",
        "timeline_id",
        "start_turning_point_id",
        "end_turning_point_id",
        "wave_end_confirmed_key",
    ),
)

WAVE_STATUS_EVENT_SCHEMA = ArtifactIdentitySchema(
    artifact_type="MUF_S5_WAVE_STATUS_EVENT",
    schema_identity=S5_SCHEMA_IDENTITY,
    identity_defining_fields=(
        "wave_process_id",
        "timeline_id",
        "status",
        "status_event_key",
        "trigger_ref",
    ),
)

G1_QUALIFICATION_RECORD_SCHEMA = ArtifactIdentitySchema(
    artifact_type="MUF_G1_STRUCTURAL_QUALIFICATION_RECORD",
    schema_identity=S5_SCHEMA_IDENTITY,
    identity_defining_fields=(
        "qualification_id",
        "representation_spec_hash",
        "authority_policy_hash",
        "dataset_id",
        "dataset_role",
        "evaluation_cutoff_key",
        "qualification_status",
        "ineligibility_reasons",
        "claim_boundary",
    ),
    proof_fields=(
        "wave_identity_count",
        "confirmed_wave_count",
        "prefix_invariance_verified",
    ),
)


def _require_non_empty_str(val: Any, name: str, err_code: str) -> str:
    if not isinstance(val, str) or not val.strip():
        raise SchemaViolation(f"{err_code}: {name} must be a non-empty string")
    return val


def _require_completed_key(
    val: Any, name: str, err_code: str
) -> InformationKey:
    if not isinstance(val, InformationKey):
        raise InformationKeyViolation(
            f"{err_code}: {name} must be an InformationKey"
        )
    if val.information_phase == InformationPhase.BAR_PRE_CLOSE:
        raise IllegalCausalReference(
            f"{err_code}: {name} cannot have BAR_PRE_CLOSE phase"
        )
    return val


def _serialize_seq(items: Sequence[str]) -> Mapping[str, str]:
    return {f"i_{idx}": val for idx, val in enumerate(items)}


def _compute_efficiency_ratio(
    abs_displacement: float, path_length: float
) -> Union[MetricResult, TypedState]:
    """Compute |displacement| / path_length with I-DE-1 zero-denominator guard."""
    if path_length <= 0.0:
        return TypedState.UNDEFINED
    return exact_metric(abs_displacement / path_length)


def _earliest_lawful_wave_key(
    *,
    start_tp_availability_key: InformationKey,
    policy_effective_from_key: InformationKey,
    additional_basis_keys: Sequence[InformationKey] = (),
) -> InformationKey:
    """Compute the earliest lawful InformationKey where all required basis inputs are visible (I-EARLY-1)."""
    earliest = (
        start_tp_availability_key
        if policy_effective_from_key <= start_tp_availability_key
        else policy_effective_from_key
    )
    for k in additional_basis_keys:
        if earliest < k:
            earliest = k
    return earliest


@dataclass(frozen=True)
class CandidateWaveRepresentationSpec(ImmutableRecord):
    """Candidate wave representation specification (D1-6, D1-8, D2-1, D2-2, I-SD-1..4, I-WIB-2)."""

    representation_id: str
    family_kind: str
    scope_timeline_id: str
    scope_axis: InformationAxis
    intrinsic_scale_key: Union[str, TypedState]
    identity_rule_ref: Union[str, TypedState]
    representation_spec_hash: str

    def __post_init__(self) -> None:
        _require_non_empty_str(
            self.representation_id,
            "representation_id",
            S5_INVALID_REPRESENTATION_SPEC,
        )
        if self.family_kind not in LEGAL_REPRESENTATION_FAMILIES:
            raise SchemaViolation(
                f"{S5_INVALID_REPRESENTATION_SPEC}: unknown family_kind {self.family_kind!r}"
            )
        _require_non_empty_str(
            self.scope_timeline_id,
            "scope_timeline_id",
            S5_INVALID_REPRESENTATION_SPEC,
        )
        if not isinstance(self.scope_axis, InformationAxis):
            raise SchemaViolation(
                f"{S5_INVALID_REPRESENTATION_SPEC}: scope_axis must be an InformationAxis"
            )

        # I-SD-4: BETA and DELTA cannot claim an intrinsic_scale_key
        if self.family_kind in FAMILIES_FORBIDDING_INTRINSIC_SCALE:
            if self.intrinsic_scale_key is not TypedState.NOT_APPLICABLE:
                raise SchemaViolation(
                    f"{S5_INTRINSIC_SCALE_FORBIDDEN_FOR_FAMILY}: {self.family_kind} "
                    "must declare intrinsic_scale_key = TypedState.NOT_APPLICABLE (I-SD-4)"
                )
        elif self.family_kind == FAMILY_ALPHA_POLICY_SCALE:
            if not isinstance(self.intrinsic_scale_key, str) or not self.intrinsic_scale_key.strip():
                raise SchemaViolation(
                    f"{S5_INTRINSIC_SCALE_REQUIRED_FOR_ALPHA}: ALPHA_POLICY_SCALE "
                    "requires a non-empty intrinsic_scale_key"
                )
        else:
            if self.intrinsic_scale_key is not TypedState.NOT_APPLICABLE:
                _require_non_empty_str(
                    self.intrinsic_scale_key,
                    "intrinsic_scale_key",
                    S5_INVALID_REPRESENTATION_SPEC,
                )

        if self.identity_rule_ref is not TypedState.NOT_CONFIGURED:
            _require_non_empty_str(
                self.identity_rule_ref,
                "identity_rule_ref",
                S5_INVALID_REPRESENTATION_SPEC,
            )

        expected_hash = canonical_artifact_identity(
            REPRESENTATION_SPEC_IDENTITY_SCHEMA,
            identity_payload={
                "representation_id": self.representation_id,
                "family_kind": self.family_kind,
                "scope_timeline_id": self.scope_timeline_id,
                "scope_axis": self.scope_axis.value,
                "intrinsic_scale_key": self.intrinsic_scale_key,
                "identity_rule_ref": self.identity_rule_ref,
            },
        )
        if self.representation_spec_hash != expected_hash:
            raise SchemaViolation(
                f"{S5_INVALID_REPRESENTATION_SPEC}: representation_spec_hash mismatch"
            )

    @classmethod
    def create(
        cls,
        *,
        representation_id: str,
        family_kind: str,
        scope_timeline_id: str,
        scope_axis: InformationAxis,
        intrinsic_scale_key: Union[str, TypedState] = TypedState.NOT_APPLICABLE,
        identity_rule_ref: Union[str, TypedState] = TypedState.NOT_CONFIGURED,
    ) -> "CandidateWaveRepresentationSpec":
        if not isinstance(scope_axis, InformationAxis):
            raise SchemaViolation(
                f"{S5_INVALID_REPRESENTATION_SPEC}: scope_axis must be an InformationAxis"
            )
        spec_hash = canonical_artifact_identity(
            REPRESENTATION_SPEC_IDENTITY_SCHEMA,
            identity_payload={
                "representation_id": representation_id,
                "family_kind": family_kind,
                "scope_timeline_id": scope_timeline_id,
                "scope_axis": scope_axis.value,
                "intrinsic_scale_key": intrinsic_scale_key,
                "identity_rule_ref": identity_rule_ref,
            },
        )
        return cls(
            representation_id=representation_id,
            family_kind=family_kind,
            scope_timeline_id=scope_timeline_id,
            scope_axis=scope_axis,
            intrinsic_scale_key=intrinsic_scale_key,
            identity_rule_ref=identity_rule_ref,
            representation_spec_hash=spec_hash,
        )


@dataclass(frozen=True)
class WaveIdentityRecord(ImmutableRecord):
    """Origin-anchored causal wave process identity record (D1-5, D2-1, D2-2, Correction-1 §1 & §2)."""

    wave_process_id: str
    timeline_id: str
    identity_basis: WaveProcessIdentityBasis
    identity_proof: WaveIdentityProof
    start_turning_point_id: str
    origin_position: int
    origin_key: InformationKey
    wave_identity_information_key: InformationKey
    wave_direction: str
    published_record: PublishedRecord

    def __post_init__(self) -> None:
        _require_non_empty_str(
            self.wave_process_id,
            "wave_process_id",
            S5_INVALID_WAVE_IDENTITY_RECORD,
        )
        _require_non_empty_str(
            self.timeline_id, "timeline_id", S5_INVALID_WAVE_IDENTITY_RECORD
        )
        if not isinstance(self.identity_basis, WaveProcessIdentityBasis):
            raise SchemaViolation(
                f"{S5_INVALID_WAVE_IDENTITY_RECORD}: identity_basis must be a WaveProcessIdentityBasis"
            )
        if not isinstance(self.identity_proof, WaveIdentityProof):
            raise SchemaViolation(
                f"{S5_INVALID_WAVE_IDENTITY_RECORD}: identity_proof must be a WaveIdentityProof"
            )
        expected_wp_id = wave_process_identity(self.identity_basis)
        if self.wave_process_id != expected_wp_id:
            raise SchemaViolation(
                f"{S5_INVALID_WAVE_IDENTITY_RECORD}: wave_process_id does not match "
                "canonical wave_process_identity(identity_basis)"
            )
        if self.identity_basis.timeline_id != self.timeline_id:
            raise InformationKeyViolation(
                f"{S5_INVALID_WAVE_IDENTITY_RECORD}: identity_basis timeline_id mismatch"
            )
        if (
            self.identity_basis.authoritative_start_turning_point_id.turning_point_identity
            != self.start_turning_point_id
        ):
            raise SchemaViolation(
                f"{S5_INVALID_WAVE_IDENTITY_RECORD}: start_turning_point_id mismatch"
            )
        if (
            isinstance(self.origin_position, bool)
            or not isinstance(self.origin_position, int)
            or self.origin_position < 0
        ):
            raise SchemaViolation(
                f"{S5_INVALID_WAVE_IDENTITY_RECORD}: origin_position must be a non-negative int"
            )
        _require_completed_key(
            self.origin_key, "origin_key", S5_INVALID_WAVE_IDENTITY_RECORD
        )
        _require_completed_key(
            self.wave_identity_information_key,
            "wave_identity_information_key",
            S5_INVALID_WAVE_IDENTITY_RECORD,
        )
        if self.origin_key.timeline_id != self.timeline_id:
            raise InformationKeyViolation(
                f"{S5_INVALID_WAVE_IDENTITY_RECORD}: origin_key timeline mismatch"
            )
        if self.wave_identity_information_key.timeline_id != self.timeline_id:
            raise InformationKeyViolation(
                f"{S5_INVALID_WAVE_IDENTITY_RECORD}: wave_identity_information_key timeline mismatch"
            )
        if (
            self.identity_proof.satisfaction_information_key
            != self.wave_identity_information_key
        ):
            raise SchemaViolation(
                f"{S5_INVALID_WAVE_IDENTITY_RECORD}: identity_proof.satisfaction_information_key "
                "must equal wave_identity_information_key"
            )
        tp_avail = (
            self.identity_basis.authoritative_start_turning_point_id.availability_key
        )
        try:
            origin_before_tp = self.origin_key < tp_avail
            tp_visible = tp_avail <= self.wave_identity_information_key
        except InformationKeyError as exc:
            raise IncomparableInformationKeys(str(exc)) from exc
        if not origin_before_tp or not tp_visible:
            raise PrematureAvailability(
                f"{S5_INVALID_WAVE_IDENTITY_RECORD}: wave_identity_information_key must be "
                ">= start turning point availability_key > origin_key (I-WPI-3)"
            )
        require_visible_at(
            fact_key=tp_avail, at_key=self.wave_identity_information_key
        )
        if self.wave_direction not in (DIRECTION_UP, DIRECTION_DOWN):
            raise SchemaViolation(
                f"{S5_INVALID_WAVE_IDENTITY_RECORD}: wave_direction must be UP or DOWN"
            )
        if not isinstance(self.published_record, PublishedRecord):
            raise SchemaViolation(
                f"{S5_INVALID_WAVE_IDENTITY_RECORD}: published_record must be a PublishedRecord"
            )
        expected_content = {
            "wave_process_id": self.wave_process_id,
            "timeline_id": self.timeline_id,
            "start_turning_point_id": self.start_turning_point_id,
            "origin_position": self.origin_position,
            "origin_key": key_serialization(self.origin_key),
            "wave_identity_information_key": key_serialization(
                self.wave_identity_information_key
            ),
            "wave_direction": self.wave_direction,
            "authority_policy_hash": self.identity_basis.authority_policy_hash,
            "representation_spec_hash": self.identity_basis.representation_spec_hash,
        }
        if (
            self.published_record.record_type != S5_WAVE_IDENTITY_RECORD_TYPE
            or self.published_record.record_identity != self.wave_process_id
            or self.published_record.timeline_id != self.timeline_id
            or self.published_record.availability_key
            != self.wave_identity_information_key
            or self.published_record.content != freeze_payload(expected_content)
        ):
            raise SchemaViolation(
                f"{S5_INVALID_WAVE_IDENTITY_RECORD}: published_record content or identity mismatch"
            )

    @classmethod
    def create(
        cls,
        *,
        representation_spec: CandidateWaveRepresentationSpec,
        policy_artifact: PolicyArtifact,
        start_turning_point: AuthoritativeTurningPointRecord,
        additional_basis_keys: Sequence[InformationKey] = (),
        additional_required_basis_refs: Sequence[str] = (),
        proof_refs: Sequence[str] = (),
        claimed_availability_key: Optional[InformationKey] = None,
    ) -> "WaveIdentityRecord":
        """Construct a WaveIdentityRecord enforcing earliest lawful availability (I-EARLY-1..3) and basis!=proof (I-IDB-1..3)."""
        if not isinstance(representation_spec, CandidateWaveRepresentationSpec):
            raise SchemaViolation("representation_spec must be a CandidateWaveRepresentationSpec")
        if not isinstance(policy_artifact, PolicyArtifact):
            raise SelectionBlockedError(
                f"{S5_POLICY_AUTHORITY_MISSING}: PolicyArtifact required to create WaveIdentityRecord"
            )
        if not isinstance(start_turning_point, AuthoritativeTurningPointRecord):
            raise SelectionBlockedError(
                f"{S5_POLICY_AUTHORITY_MISSING}: AuthoritativeTurningPointRecord required"
            )
        if representation_spec.identity_rule_ref is TypedState.NOT_CONFIGURED:
            raise SelectionBlockedError(
                f"{S5_IDENTITY_RULE_NOT_CONFIGURED}: identity_rule_ref is NOT_CONFIGURED (I-WIB-2)"
            )
        if (
            representation_spec.scope_timeline_id != start_turning_point.timeline_id
            or policy_artifact.scope_timeline_id != start_turning_point.timeline_id
        ):
            raise PolicyScopeMismatch(
                "timeline mismatch between representation_spec, policy_artifact, and start_turning_point"
            )
        if start_turning_point.authority_policy_hash != policy_artifact.policy_hash:
            raise PolicyScopeMismatch(
                "start_turning_point.authority_policy_hash does not match policy_artifact.policy_hash"
            )

        earliest_key = _earliest_lawful_wave_key(
            start_tp_availability_key=start_turning_point.availability_key,
            policy_effective_from_key=policy_artifact.effective_from_key,
            additional_basis_keys=additional_basis_keys,
        )
        target_key = (
            earliest_key
            if claimed_availability_key is None
            else claimed_availability_key
        )
        try:
            is_earlier = target_key < earliest_key
            is_later = earliest_key < target_key
        except InformationKeyError as exc:
            raise IncomparableInformationKeys(str(exc)) from exc
        if is_earlier:
            raise PrematureAvailability(
                "claimed_availability_key precedes earliest lawful availability key (I-WIB-3)"
            )
        if is_later:
            raise NonEarliestAvailability(
                f"{S5_NON_EARLIEST_WAVE_AVAILABILITY}: WaveIdentityRecord delayed past "
                "earliest lawful availability key without new required basis input (I-EARLY-2)"
            )

        basis = WaveProcessIdentityBasis(
            representation_spec_hash=representation_spec.representation_spec_hash,
            authoritative_start_turning_point_id=start_turning_point.to_turning_point_reference(),
            authority_policy_hash=policy_artifact.policy_hash,
            timeline_id=start_turning_point.timeline_id,
            intrinsic_representation_key_or_NOT_APPLICABLE=representation_spec.intrinsic_scale_key,
        )
        wp_id = wave_process_identity(basis)
        req_refs = (
            start_turning_point.turning_point_id,
            policy_artifact.policy_hash,
            representation_spec.representation_spec_hash,
        ) + tuple(additional_required_basis_refs)
        proof = WaveIdentityProof(
            identity_rule_ref=str(representation_spec.identity_rule_ref),
            required_basis_refs=req_refs,
            proof_refs=tuple(proof_refs),
            satisfaction_information_key=target_key,
        )
        w_dir = (
            DIRECTION_UP
            if start_turning_point.extrema_kind == "LOW"
            else DIRECTION_DOWN
        )
        pub_rec = PublishedRecord(
            record_type=S5_WAVE_IDENTITY_RECORD_TYPE,
            record_identity=wp_id,
            schema_identity=S5_SCHEMA_IDENTITY,
            timeline_id=start_turning_point.timeline_id,
            availability_key=target_key,
            content={
                "wave_process_id": wp_id,
                "timeline_id": start_turning_point.timeline_id,
                "start_turning_point_id": start_turning_point.turning_point_id,
                "origin_position": start_turning_point.origin_position,
                "origin_key": key_serialization(start_turning_point.origin_key),
                "wave_identity_information_key": key_serialization(target_key),
                "wave_direction": w_dir,
                "authority_policy_hash": policy_artifact.policy_hash,
                "representation_spec_hash": representation_spec.representation_spec_hash,
            },
        )
        return cls(
            wave_process_id=wp_id,
            timeline_id=start_turning_point.timeline_id,
            identity_basis=basis,
            identity_proof=proof,
            start_turning_point_id=start_turning_point.turning_point_id,
            origin_position=start_turning_point.origin_position,
            origin_key=start_turning_point.origin_key,
            wave_identity_information_key=target_key,
            wave_direction=w_dir,
            published_record=pub_rec,
        )


@dataclass(frozen=True)
class RunningWaveObservationRecord(ImmutableRecord):
    """Append-only running descriptor observation for an active wave process (D1-5, I-WID-1, I-DE-1)."""

    observation_id: str
    wave_process_id: str
    timeline_id: str
    observation_position: int
    observation_key: InformationKey
    running_bar_count: int
    running_displacement: MetricResult
    running_path_length: MetricResult
    running_efficiency_ratio: Union[MetricResult, TypedState]
    running_extreme_price: MetricResult
    published_record: PublishedRecord

    def __post_init__(self) -> None:
        _require_non_empty_str(
            self.observation_id, "observation_id", S5_INVALID_RUNNING_OBSERVATION
        )
        _require_non_empty_str(
            self.wave_process_id,
            "wave_process_id",
            S5_INVALID_RUNNING_OBSERVATION,
        )
        _require_non_empty_str(
            self.timeline_id, "timeline_id", S5_INVALID_RUNNING_OBSERVATION
        )
        if (
            isinstance(self.observation_position, bool)
            or not isinstance(self.observation_position, int)
            or self.observation_position < 0
        ):
            raise SchemaViolation(
                f"{S5_INVALID_RUNNING_OBSERVATION}: observation_position must be a non-negative int"
            )
        _require_completed_key(
            self.observation_key,
            "observation_key",
            S5_INVALID_RUNNING_OBSERVATION,
        )
        if self.observation_key.timeline_id != self.timeline_id:
            raise InformationKeyViolation(
                f"{S5_INVALID_RUNNING_OBSERVATION}: observation_key timeline mismatch"
            )
        if (
            isinstance(self.running_bar_count, bool)
            or not isinstance(self.running_bar_count, int)
            or self.running_bar_count < 1
        ):
            raise SchemaViolation(
                f"{S5_INVALID_RUNNING_OBSERVATION}: running_bar_count must be >= 1"
            )
        for m_name, m_val in (
            ("running_displacement", self.running_displacement),
            ("running_path_length", self.running_path_length),
            ("running_extreme_price", self.running_extreme_price),
        ):
            if (
                not isinstance(m_val, MetricResult)
                or m_val.semantics != EXACT
                or not isinstance(m_val.value, float)
                or not math.isfinite(m_val.value)
            ):
                raise SchemaViolation(
                    f"{S5_INVALID_RUNNING_OBSERVATION}: {m_name} must be finite EXACT MetricResult"
                )
        if self.running_path_length.value <= 0.0:
            if self.running_efficiency_ratio is not TypedState.UNDEFINED:
                raise SchemaViolation(
                    f"{S5_INVALID_RUNNING_OBSERVATION}: zero running_path_length requires "
                    "running_efficiency_ratio = TypedState.UNDEFINED (I-DE-1)"
                )
        else:
            if (
                not isinstance(self.running_efficiency_ratio, MetricResult)
                or self.running_efficiency_ratio.semantics != EXACT
            ):
                raise SchemaViolation(
                    f"{S5_INVALID_RUNNING_OBSERVATION}: positive running_path_length requires "
                    "EXACT running_efficiency_ratio"
                )
        expected_id = canonical_artifact_identity(
            RUNNING_WAVE_OBSERVATION_SCHEMA,
            identity_payload={
                "wave_process_id": self.wave_process_id,
                "timeline_id": self.timeline_id,
                "observation_position": str(self.observation_position),
                "observation_key": self.observation_key,
            },
        )
        if self.observation_id != expected_id:
            raise SchemaViolation(
                f"{S5_INVALID_RUNNING_OBSERVATION}: observation_id mismatch"
            )
        if (
            not isinstance(self.published_record, PublishedRecord)
            or self.published_record.record_type
            != S5_RUNNING_WAVE_OBSERVATION_RECORD_TYPE
            or self.published_record.record_identity != self.observation_id
            or self.published_record.availability_key != self.observation_key
        ):
            raise SchemaViolation(
                f"{S5_INVALID_RUNNING_OBSERVATION}: published_record mismatch"
            )


@dataclass(frozen=True)
class FinalizedWaveGeometryRecord(ImmutableRecord):
    """Separate append-only finalized wave geometry emitted at wave_end_confirmed_key (D1-5, I-WID-2, I-DE-1)."""

    geometry_record_id: str
    wave_process_id: str
    timeline_id: str
    start_turning_point_id: str
    end_turning_point_id: str
    start_origin_position: int
    end_origin_position: int
    start_origin_key: InformationKey
    end_origin_key: InformationKey
    wave_end_confirmed_key: InformationKey
    final_bar_count: int
    final_displacement: MetricResult
    final_path_length: MetricResult
    final_efficiency_ratio: Union[MetricResult, TypedState]
    published_record: PublishedRecord

    def __post_init__(self) -> None:
        _require_non_empty_str(
            self.geometry_record_id,
            "geometry_record_id",
            S5_INVALID_FINALIZED_GEOMETRY,
        )
        _require_non_empty_str(
            self.wave_process_id,
            "wave_process_id",
            S5_INVALID_FINALIZED_GEOMETRY,
        )
        _require_non_empty_str(
            self.timeline_id, "timeline_id", S5_INVALID_FINALIZED_GEOMETRY
        )
        _require_non_empty_str(
            self.start_turning_point_id,
            "start_turning_point_id",
            S5_INVALID_FINALIZED_GEOMETRY,
        )
        _require_non_empty_str(
            self.end_turning_point_id,
            "end_turning_point_id",
            S5_INVALID_FINALIZED_GEOMETRY,
        )
        if self.end_origin_position <= self.start_origin_position:
            raise SchemaViolation(
                f"{S5_INVALID_FINALIZED_GEOMETRY}: end_origin_position must exceed start_origin_position"
            )
        _require_completed_key(
            self.start_origin_key,
            "start_origin_key",
            S5_INVALID_FINALIZED_GEOMETRY,
        )
        _require_completed_key(
            self.end_origin_key,
            "end_origin_key",
            S5_INVALID_FINALIZED_GEOMETRY,
        )
        _require_completed_key(
            self.wave_end_confirmed_key,
            "wave_end_confirmed_key",
            S5_INVALID_FINALIZED_GEOMETRY,
        )
        try:
            valid_chron = (
                self.start_origin_key
                < self.end_origin_key
                < self.wave_end_confirmed_key
            )
        except InformationKeyError as exc:
            raise IncomparableInformationKeys(str(exc)) from exc
        if not valid_chron:
            raise PrematureAvailability(
                f"{S5_INVALID_FINALIZED_GEOMETRY}: require start_origin_key < end_origin_key < wave_end_confirmed_key"
            )
        if self.final_bar_count != (
            self.end_origin_position - self.start_origin_position
        ):
            raise SchemaViolation(
                f"{S5_INVALID_FINALIZED_GEOMETRY}: final_bar_count mismatch"
            )
        for m_name, m_val in (
            ("final_displacement", self.final_displacement),
            ("final_path_length", self.final_path_length),
        ):
            if (
                not isinstance(m_val, MetricResult)
                or m_val.semantics != EXACT
                or not isinstance(m_val.value, float)
                or not math.isfinite(m_val.value)
            ):
                raise SchemaViolation(
                    f"{S5_INVALID_FINALIZED_GEOMETRY}: {m_name} must be finite EXACT MetricResult"
                )
        if self.final_path_length.value <= 0.0:
            if self.final_efficiency_ratio is not TypedState.UNDEFINED:
                raise SchemaViolation(
                    f"{S5_INVALID_FINALIZED_GEOMETRY}: zero final_path_length requires "
                    "final_efficiency_ratio = TypedState.UNDEFINED (I-DE-1)"
                )
        else:
            if (
                not isinstance(self.final_efficiency_ratio, MetricResult)
                or self.final_efficiency_ratio.semantics != EXACT
            ):
                raise SchemaViolation(
                    f"{S5_INVALID_FINALIZED_GEOMETRY}: positive final_path_length requires "
                    "EXACT final_efficiency_ratio"
                )
        expected_id = canonical_artifact_identity(
            FINALIZED_WAVE_GEOMETRY_SCHEMA,
            identity_payload={
                "wave_process_id": self.wave_process_id,
                "timeline_id": self.timeline_id,
                "start_turning_point_id": self.start_turning_point_id,
                "end_turning_point_id": self.end_turning_point_id,
                "wave_end_confirmed_key": self.wave_end_confirmed_key,
            },
        )
        if self.geometry_record_id != expected_id:
            raise SchemaViolation(
                f"{S5_INVALID_FINALIZED_GEOMETRY}: geometry_record_id mismatch"
            )
        if (
            not isinstance(self.published_record, PublishedRecord)
            or self.published_record.record_type
            != S5_FINALIZED_WAVE_GEOMETRY_RECORD_TYPE
            or self.published_record.record_identity != self.geometry_record_id
            or self.published_record.availability_key
            != self.wave_end_confirmed_key
        ):
            raise SchemaViolation(
                f"{S5_INVALID_FINALIZED_GEOMETRY}: published_record mismatch"
            )


@dataclass(frozen=True)
class WaveStatusEventRecord(ImmutableRecord):
    """Append-only wave status transition event (FORMING -> CONFIRMED / SUPERSEDED)."""

    event_id: str
    wave_process_id: str
    timeline_id: str
    status: str
    status_event_key: InformationKey
    trigger_ref: str
    published_record: PublishedRecord

    def __post_init__(self) -> None:
        _require_non_empty_str(
            self.event_id, "event_id", S5_INVALID_WAVE_STATUS_EVENT
        )
        _require_non_empty_str(
            self.wave_process_id,
            "wave_process_id",
            S5_INVALID_WAVE_STATUS_EVENT,
        )
        _require_non_empty_str(
            self.timeline_id, "timeline_id", S5_INVALID_WAVE_STATUS_EVENT
        )
        if self.status not in LEGAL_WAVE_STATUSES:
            raise SchemaViolation(
                f"{S5_INVALID_WAVE_STATUS_EVENT}: invalid status {self.status!r}"
            )
        _require_completed_key(
            self.status_event_key,
            "status_event_key",
            S5_INVALID_WAVE_STATUS_EVENT,
        )
        _require_non_empty_str(
            self.trigger_ref, "trigger_ref", S5_INVALID_WAVE_STATUS_EVENT
        )
        expected_id = canonical_artifact_identity(
            WAVE_STATUS_EVENT_SCHEMA,
            identity_payload={
                "wave_process_id": self.wave_process_id,
                "timeline_id": self.timeline_id,
                "status": self.status,
                "status_event_key": self.status_event_key,
                "trigger_ref": self.trigger_ref,
            },
        )
        if self.event_id != expected_id:
            raise SchemaViolation(
                f"{S5_INVALID_WAVE_STATUS_EVENT}: event_id mismatch"
            )
        if (
            not isinstance(self.published_record, PublishedRecord)
            or self.published_record.record_type
            != S5_WAVE_STATUS_EVENT_RECORD_TYPE
            or self.published_record.record_identity != self.event_id
            or self.published_record.availability_key != self.status_event_key
        ):
            raise SchemaViolation(
                f"{S5_INVALID_WAVE_STATUS_EVENT}: published_record mismatch"
            )


@dataclass(frozen=True)
class WaveRepresentationAsOfView(ImmutableRecord):
    """Causal as-of projection of a candidate wave representation at ``query_key``."""

    timeline_id: str
    axis: InformationAxis
    query_key: InformationKey
    representation_spec_hash: str
    authority_policy_hash: str
    visible_turning_points: Tuple[AuthoritativeTurningPointRecord, ...]
    visible_wave_identities: Tuple[WaveIdentityRecord, ...]
    visible_running_observations: Tuple[RunningWaveObservationRecord, ...]
    visible_finalized_geometries: Tuple[FinalizedWaveGeometryRecord, ...]
    visible_status_events: Tuple[WaveStatusEventRecord, ...]
    forming_wave_process_ids: Tuple[str, ...]
    confirmed_wave_process_ids: Tuple[str, ...]

    def __post_init__(self) -> None:
        _require_completed_key(
            self.query_key, "query_key", S5_INVALID_WAVE_BUNDLE
        )
        for tp in self.visible_turning_points:
            require_visible_at(fact_key=tp.availability_key, at_key=self.query_key)
        for wi in self.visible_wave_identities:
            require_visible_at(
                fact_key=wi.wave_identity_information_key, at_key=self.query_key
            )
        for ro in self.visible_running_observations:
            require_visible_at(fact_key=ro.observation_key, at_key=self.query_key)
        for fg in self.visible_finalized_geometries:
            require_visible_at(
                fact_key=fg.wave_end_confirmed_key, at_key=self.query_key
            )
        for se in self.visible_status_events:
            require_visible_at(fact_key=se.status_event_key, at_key=self.query_key)


@dataclass(frozen=True)
class CandidateWaveRepresentationBundle(ImmutableRecord):
    """Append-only candidate wave representation bundle on a DEVELOPMENT dataset (D1-5, D2-1, D2-2, D2-22)."""

    representation_spec: CandidateWaveRepresentationSpec
    policy_artifact: PolicyArtifact
    dataset_id: str
    dataset_role: str
    timeline_id: str
    axis: InformationAxis
    observation_keys: Tuple[InformationKey, ...]
    authoritative_turning_points: Tuple[AuthoritativeTurningPointRecord, ...]
    wave_identity_records: Tuple[WaveIdentityRecord, ...]
    running_wave_observations: Tuple[RunningWaveObservationRecord, ...]
    finalized_wave_geometries: Tuple[FinalizedWaveGeometryRecord, ...]
    wave_status_events: Tuple[WaveStatusEventRecord, ...]
    updated_dataset_role: DatasetRoleArtifact

    def __post_init__(self) -> None:
        if not isinstance(self.representation_spec, CandidateWaveRepresentationSpec):
            raise SchemaViolation(
                f"{S5_INVALID_WAVE_BUNDLE}: representation_spec must be a CandidateWaveRepresentationSpec"
            )
        if not isinstance(self.policy_artifact, PolicyArtifact):
            raise SelectionBlockedError(
                f"{S5_POLICY_AUTHORITY_MISSING}: policy_artifact must be a PolicyArtifact"
            )
        if self.dataset_role not in (
            DATASET_ROLE_DEVELOPMENT_FIT,
            DATASET_ROLE_DEVELOPMENT_SELECTION,
        ):
            raise SelectionBlockedError(
                f"{S5_FINAL_DATASET_FORBIDDEN_IN_CANDIDATE_CONSTRUCTION}: S5 candidate wave "
                f"construction forbids dataset role {self.dataset_role!r} (I-SEL-3)"
            )
        obs_tuple = tuple(self.observation_keys)
        if len(obs_tuple) == 0:
            raise SchemaViolation(
                f"{S5_INVALID_WAVE_BUNDLE}: observation_keys must be non-empty"
            )
        object.__setattr__(self, "observation_keys", obs_tuple)
        object.__setattr__(
            self,
            "authoritative_turning_points",
            tuple(self.authoritative_turning_points),
        )
        object.__setattr__(
            self, "wave_identity_records", tuple(self.wave_identity_records)
        )
        object.__setattr__(
            self,
            "running_wave_observations",
            tuple(self.running_wave_observations),
        )
        object.__setattr__(
            self,
            "finalized_wave_geometries",
            tuple(self.finalized_wave_geometries),
        )
        object.__setattr__(
            self, "wave_status_events", tuple(self.wave_status_events)
        )


def _create_running_observation(
    *,
    wave_identity: WaveIdentityRecord,
    start_price: float,
    obs_pos: int,
    obs_key: InformationKey,
    bar_high: float,
    bar_low: float,
    bar_close: float,
    running_extreme: float,
    cum_path_from_origin: float,
) -> Tuple[RunningWaveObservationRecord, float]:
    new_extreme = (
        max(running_extreme, bar_high)
        if wave_identity.wave_direction == DIRECTION_UP
        else min(running_extreme, bar_low)
    )
    disp = bar_close - start_price
    bar_cnt = (obs_pos - wave_identity.origin_position) + 1
    eff = _compute_efficiency_ratio(abs(disp), cum_path_from_origin)
    obs_id = canonical_artifact_identity(
        RUNNING_WAVE_OBSERVATION_SCHEMA,
        identity_payload={
            "wave_process_id": wave_identity.wave_process_id,
            "timeline_id": wave_identity.timeline_id,
            "observation_position": str(obs_pos),
            "observation_key": obs_key,
        },
    )
    disp_m = exact_metric(disp)
    path_m = exact_metric(cum_path_from_origin)
    ext_m = exact_metric(new_extreme)
    pub = PublishedRecord(
        record_type=S5_RUNNING_WAVE_OBSERVATION_RECORD_TYPE,
        record_identity=obs_id,
        schema_identity=S5_SCHEMA_IDENTITY,
        timeline_id=wave_identity.timeline_id,
        availability_key=obs_key,
        content={
            "observation_id": obs_id,
            "wave_process_id": wave_identity.wave_process_id,
            "observation_position": obs_pos,
            "running_bar_count": bar_cnt,
            "running_displacement": metric_payload(disp_m),
            "running_path_length": metric_payload(path_m),
            "running_efficiency_ratio": (
                metric_payload(eff)
                if isinstance(eff, MetricResult)
                else eff.value
            ),
            "running_extreme_price": metric_payload(ext_m),
        },
    )
    return (
        RunningWaveObservationRecord(
            observation_id=obs_id,
            wave_process_id=wave_identity.wave_process_id,
            timeline_id=wave_identity.timeline_id,
            observation_position=obs_pos,
            observation_key=obs_key,
            running_bar_count=bar_cnt,
            running_displacement=disp_m,
            running_path_length=path_m,
            running_efficiency_ratio=eff,
            running_extreme_price=ext_m,
            published_record=pub,
        ),
        new_extreme,
    )


def _create_status_event(
    *,
    wave_process_id: str,
    timeline_id: str,
    status: str,
    status_event_key: InformationKey,
    trigger_ref: str,
) -> WaveStatusEventRecord:
    ev_id = canonical_artifact_identity(
        WAVE_STATUS_EVENT_SCHEMA,
        identity_payload={
            "wave_process_id": wave_process_id,
            "timeline_id": timeline_id,
            "status": status,
            "status_event_key": status_event_key,
            "trigger_ref": trigger_ref,
        },
    )
    pub = PublishedRecord(
        record_type=S5_WAVE_STATUS_EVENT_RECORD_TYPE,
        record_identity=ev_id,
        schema_identity=S5_SCHEMA_IDENTITY,
        timeline_id=timeline_id,
        availability_key=status_event_key,
        content={
            "event_id": ev_id,
            "wave_process_id": wave_process_id,
            "status": status,
            "trigger_ref": trigger_ref,
        },
    )
    return WaveStatusEventRecord(
        event_id=ev_id,
        wave_process_id=wave_process_id,
        timeline_id=timeline_id,
        status=status,
        status_event_key=status_event_key,
        trigger_ref=trigger_ref,
        published_record=pub,
    )


def _create_finalized_geometry(
    *,
    wave_identity: WaveIdentityRecord,
    start_tp: AuthoritativeTurningPointRecord,
    end_tp: AuthoritativeTurningPointRecord,
    final_path_len_val: float,
) -> FinalizedWaveGeometryRecord:
    confirmed_key = (
        wave_identity.wave_identity_information_key
        if end_tp.availability_key <= wave_identity.wave_identity_information_key
        else end_tp.availability_key
    )
    disp_val = end_tp.swing_price.value - start_tp.swing_price.value
    bar_cnt = end_tp.origin_position - start_tp.origin_position
    eff = _compute_efficiency_ratio(abs(disp_val), final_path_len_val)
    geom_id = canonical_artifact_identity(
        FINALIZED_WAVE_GEOMETRY_SCHEMA,
        identity_payload={
            "wave_process_id": wave_identity.wave_process_id,
            "timeline_id": wave_identity.timeline_id,
            "start_turning_point_id": start_tp.turning_point_id,
            "end_turning_point_id": end_tp.turning_point_id,
            "wave_end_confirmed_key": confirmed_key,
        },
    )
    disp_m = exact_metric(disp_val)
    path_m = exact_metric(final_path_len_val)
    pub = PublishedRecord(
        record_type=S5_FINALIZED_WAVE_GEOMETRY_RECORD_TYPE,
        record_identity=geom_id,
        schema_identity=S5_SCHEMA_IDENTITY,
        timeline_id=wave_identity.timeline_id,
        availability_key=confirmed_key,
        content={
            "geometry_record_id": geom_id,
            "wave_process_id": wave_identity.wave_process_id,
            "start_turning_point_id": start_tp.turning_point_id,
            "end_turning_point_id": end_tp.turning_point_id,
            "final_bar_count": bar_cnt,
            "final_displacement": metric_payload(disp_m),
            "final_path_length": metric_payload(path_m),
            "final_efficiency_ratio": (
                metric_payload(eff)
                if isinstance(eff, MetricResult)
                else eff.value
            ),
        },
    )
    return FinalizedWaveGeometryRecord(
        geometry_record_id=geom_id,
        wave_process_id=wave_identity.wave_process_id,
        timeline_id=wave_identity.timeline_id,
        start_turning_point_id=start_tp.turning_point_id,
        end_turning_point_id=end_tp.turning_point_id,
        start_origin_position=start_tp.origin_position,
        end_origin_position=end_tp.origin_position,
        start_origin_key=start_tp.origin_key,
        end_origin_key=end_tp.origin_key,
        wave_end_confirmed_key=confirmed_key,
        final_bar_count=bar_cnt,
        final_displacement=disp_m,
        final_path_length=path_m,
        final_efficiency_ratio=eff,
        published_record=pub,
    )


def construct_candidate_wave_representation(
    bars: Sequence[PublishedOhlcBarFact],
    *,
    witness_bundle: DetectorWitnessBundle,
    representation_spec: Any,
    policy_artifact: Any,
    dataset_identity: DatasetIdentityArtifact,
    dataset_role: DatasetRoleArtifact,
) -> CandidateWaveRepresentationBundle:
    """Construct a CandidateWaveRepresentationBundle in a single O(N) pass (O(1) per bar).

    Enforces:
    - Development-only dataset role (rejects FINAL_EVALUATION_LOCKED);
    - Explicit PolicyArtifact & configured identity_rule_ref;
    - Earliest lawful availability (I-EARLY-1..3) and origin-anchored identity (I-WPI-1..5);
    - Four append-only wave tables with zero retroactive mutation.
    """
    if not isinstance(representation_spec, CandidateWaveRepresentationSpec):
        raise SelectionBlockedError(
            f"{S5_INVALID_REPRESENTATION_SPEC}: valid CandidateWaveRepresentationSpec required"
        )
    if not isinstance(policy_artifact, PolicyArtifact):
        raise SelectionBlockedError(
            f"{S5_POLICY_AUTHORITY_MISSING}: valid PolicyArtifact required for S5 wave construction (Attack 2)"
        )
    if representation_spec.identity_rule_ref is TypedState.NOT_CONFIGURED:
        raise SelectionBlockedError(
            f"{S5_IDENTITY_RULE_NOT_CONFIGURED}: identity_rule_ref is NOT_CONFIGURED (Attack 26)"
        )
    if not isinstance(dataset_identity, DatasetIdentityArtifact) or not isinstance(
        dataset_role, DatasetRoleArtifact
    ):
        raise SelectionBlockedError(
            f"{S5_INVALID_DEVELOPMENT_BAR_STREAM}: dataset_identity and dataset_role required"
        )
    if (
        dataset_role.dataset_id != dataset_identity.dataset_id
        or dataset_role.dataset_identity_hash
        != dataset_identity.dataset_identity_hash
    ):
        raise SelectionBlockedError(
            f"{S5_INVALID_DEVELOPMENT_BAR_STREAM}: dataset_role does not match dataset_identity"
        )
    if dataset_role.role not in (
        DATASET_ROLE_DEVELOPMENT_FIT,
        DATASET_ROLE_DEVELOPMENT_SELECTION,
    ):
        raise SelectionBlockedError(
            f"{S5_FINAL_DATASET_FORBIDDEN_IN_CANDIDATE_CONSTRUCTION}: S5 candidate wave "
            f"construction is forbidden on dataset role {dataset_role.role!r} (I-SEL-3, Attack 38)"
        )
    if dataset_role.exposure_state not in (
        EXPOSURE_STATE_UNEXPOSED,
        EXPOSURE_STATE_EXPOSED_DEVELOPMENT,
    ):
        raise SelectionBlockedError(
            f"{S5_INVALID_DEVELOPMENT_BAR_STREAM}: invalid exposure_state {dataset_role.exposure_state!r}"
        )

    if (
        policy_artifact.scope_timeline_id != dataset_identity.timeline_id
        or representation_spec.scope_timeline_id != dataset_identity.timeline_id
    ):
        raise PolicyScopeMismatch(
            "timeline_id mismatch across dataset_identity, policy_artifact, and representation_spec"
        )
    if (
        policy_artifact.scope_axis is not dataset_identity.axis
        or representation_spec.scope_axis is not dataset_identity.axis
    ):
        raise PolicyScopeMismatch(
            "axis mismatch across dataset_identity, policy_artifact, and representation_spec"
        )
    if (
        policy_artifact.scope_representation_id
        != representation_spec.representation_id
    ):
        raise PolicyScopeMismatch(
            "policy_artifact.scope_representation_id does not match representation_spec.representation_id"
        )

    bar_tuple = tuple(bars)
    if len(bar_tuple) == 0:
        raise SchemaViolation(
            f"{S5_INVALID_DEVELOPMENT_BAR_STREAM}: bars must be non-empty"
        )
    if not isinstance(witness_bundle, DetectorWitnessBundle):
        raise SchemaViolation("witness_bundle must be a DetectorWitnessBundle")
    if len(witness_bundle.observation_keys) != len(bar_tuple):
        raise SchemaViolation(
            f"{S5_INVALID_DEVELOPMENT_BAR_STREAM}: witness_bundle length mismatch with bars"
        )

    # Validate bars and build O(1) prefix-sum path-length array
    prefix_path_len: list[float] = [0.0] * len(bar_tuple)
    obs_keys: list[InformationKey] = []
    for idx, bar in enumerate(bar_tuple):
        if not isinstance(bar, PublishedOhlcBarFact):
            raise SchemaViolation(
                f"{S5_INVALID_DEVELOPMENT_BAR_STREAM}: element {idx} is not PublishedOhlcBarFact"
            )
        if bar.dataset_identity != dataset_identity.dataset_id:
            raise SelectionBlockedError(
                f"{S5_FINAL_DATASET_FORBIDDEN_IN_CANDIDATE_CONSTRUCTION}: bar {idx} "
                f"dataset_identity {bar.dataset_identity!r} != {dataset_identity.dataset_id!r}"
            )
        if bar.availability_key != witness_bundle.observation_keys[idx]:
            raise SchemaViolation(
                f"{S5_INVALID_DEVELOPMENT_BAR_STREAM}: bar {idx} availability_key mismatch with witness_bundle"
            )
        if not (
            dataset_identity.start_key
            <= bar.availability_key
            <= dataset_identity.end_key
        ):
            raise PrematureAvailability(
                f"{S5_INVALID_DEVELOPMENT_BAR_STREAM}: bar {idx} outside dataset [start_key, end_key]"
            )
        obs_keys.append(bar.availability_key)
        if idx > 0:
            step_len = abs(
                bar.close_price - bar_tuple[idx - 1].close_price
            ) + (bar.high_price - bar.low_price)
            prefix_path_len[idx] = prefix_path_len[idx - 1] + step_len
        else:
            prefix_path_len[0] = bar.high_price - bar.low_price

    # Index swing witnesses by confirmation_position for O(1) lookup during single-pass scan
    witnesses_by_conf_pos: dict[int, list[SwingEventWitnessRecord]] = {}
    for sw in witness_bundle.swing_event_witnesses:
        # Only promote witnesses that become available at or after policy_artifact.effective_from_key
        if policy_artifact.effective_from_key <= sw.availability_key:
            witnesses_by_conf_pos.setdefault(sw.confirmation_position, []).append(
                sw
            )

    promoted_tps: list[AuthoritativeTurningPointRecord] = []
    wave_identities: list[WaveIdentityRecord] = []
    running_observations: list[RunningWaveObservationRecord] = []
    finalized_geometries: list[FinalizedWaveGeometryRecord] = []
    status_events: list[WaveStatusEventRecord] = []

    active_wave: Optional[WaveIdentityRecord] = None
    active_start_tp: Optional[AuthoritativeTurningPointRecord] = None
    active_running_extreme: float = 0.0

    # Single O(N) causal bar-by-bar pass (O(1) work per bar)
    for pos, bar in enumerate(bar_tuple):
        b_key = bar.availability_key
        new_witnesses = witnesses_by_conf_pos.get(pos, [])
        for sw in new_witnesses:
            tp = promote_swing_witness_with_policy_artifact(
                sw, policy_artifact=policy_artifact
            )
            promoted_tps.append(tp)

            # If an active wave exists and this new TP has a strictly later origin, finalize the active wave
            if (
                active_wave is not None
                and active_start_tp is not None
                and tp.origin_position > active_start_tp.origin_position
                and tp.extrema_kind != active_start_tp.extrema_kind
            ):
                path_seg = (
                    prefix_path_len[tp.origin_position]
                    - prefix_path_len[active_start_tp.origin_position]
                )
                fg = _create_finalized_geometry(
                    wave_identity=active_wave,
                    start_tp=active_start_tp,
                    end_tp=tp,
                    final_path_len_val=path_seg,
                )
                finalized_geometries.append(fg)
                status_events.append(
                    _create_status_event(
                        wave_process_id=active_wave.wave_process_id,
                        timeline_id=active_wave.timeline_id,
                        status=WAVE_STATUS_CONFIRMED,
                        status_event_key=fg.wave_end_confirmed_key,
                        trigger_ref=fg.geometry_record_id,
                    )
                )
                active_wave = None
                active_start_tp = None

            # Start a new origin-anchored wave process from `tp`
            new_wave = WaveIdentityRecord.create(
                representation_spec=representation_spec,
                policy_artifact=policy_artifact,
                start_turning_point=tp,
            )
            wave_identities.append(new_wave)
            status_events.append(
                _create_status_event(
                    wave_process_id=new_wave.wave_process_id,
                    timeline_id=new_wave.timeline_id,
                    status=WAVE_STATUS_FORMING,
                    status_event_key=new_wave.wave_identity_information_key,
                    trigger_ref=tp.turning_point_id,
                )
            )
            active_wave = new_wave
            active_start_tp = tp
            active_running_extreme = tp.swing_price.value

        # Emit O(1) running observation for the currently active wave at bar `pos`
        if (
            active_wave is not None
            and active_start_tp is not None
            and active_wave.wave_identity_information_key <= b_key
        ):
            cum_path = (
                prefix_path_len[pos]
                - prefix_path_len[active_start_tp.origin_position]
            )
            run_obs, active_running_extreme = _create_running_observation(
                wave_identity=active_wave,
                start_price=active_start_tp.swing_price.value,
                obs_pos=pos,
                obs_key=b_key,
                bar_high=bar.high_price,
                bar_low=bar.low_price,
                bar_close=bar.close_price,
                running_extreme=active_running_extreme,
                cum_path_from_origin=cum_path,
            )
            running_observations.append(run_obs)

    updated_role = record_dataset_exposure(
        dataset_role,
        event_id=f"s5_wave_build:{representation_spec.representation_id}:{obs_keys[-1].bar_position}",
        exposure_key=obs_keys[-1],
        exposure_kind="S5_CANDIDATE_WAVE_CONSTRUCTION",
        actor_or_protocol_ref=representation_spec.representation_spec_hash,
    )

    return CandidateWaveRepresentationBundle(
        representation_spec=representation_spec,
        policy_artifact=policy_artifact,
        dataset_id=dataset_identity.dataset_id,
        dataset_role=dataset_role.role,
        timeline_id=dataset_identity.timeline_id,
        axis=dataset_identity.axis,
        observation_keys=tuple(obs_keys),
        authoritative_turning_points=tuple(promoted_tps),
        wave_identity_records=tuple(wave_identities),
        running_wave_observations=tuple(running_observations),
        finalized_wave_geometries=tuple(finalized_geometries),
        wave_status_events=tuple(status_events),
        updated_dataset_role=updated_role,
    )


def query_wave_representation_as_of(
    bundle: CandidateWaveRepresentationBundle,
    *,
    at_key: InformationKey,
) -> WaveRepresentationAsOfView:
    """Project a CandidateWaveRepresentationBundle causally at ``at_key``."""
    if not isinstance(bundle, CandidateWaveRepresentationBundle):
        raise SchemaViolation("bundle must be a CandidateWaveRepresentationBundle")
    _require_completed_key(at_key, "at_key", S5_INVALID_WAVE_BUNDLE)
    if at_key.timeline_id != bundle.timeline_id:
        raise InformationKeyViolation("at_key timeline mismatch with bundle")
    if key_axis(at_key) is not bundle.axis:
        raise IncomparableInformationKeys("at_key axis mismatch with bundle")
    if not (
        bundle.observation_keys[0] <= at_key <= bundle.observation_keys[-1]
    ):
        raise PrematureAvailability(
            "at_key lies outside bundle observation_keys range"
        )

    vis_tps = tuple(
        tp
        for tp in bundle.authoritative_turning_points
        if tp.availability_key <= at_key
    )
    vis_ids = tuple(
        wi
        for wi in bundle.wave_identity_records
        if wi.wave_identity_information_key <= at_key
    )
    vis_obs = tuple(
        ro
        for ro in bundle.running_wave_observations
        if ro.observation_key <= at_key
    )
    vis_geoms = tuple(
        fg
        for fg in bundle.finalized_wave_geometries
        if fg.wave_end_confirmed_key <= at_key
    )
    vis_events = tuple(
        se
        for se in bundle.wave_status_events
        if se.status_event_key <= at_key
    )

    latest_status_by_wp: dict[str, str] = {}
    for se in vis_events:
        latest_status_by_wp[se.wave_process_id] = se.status

    forming_ids = tuple(
        wi.wave_process_id
        for wi in vis_ids
        if latest_status_by_wp.get(wi.wave_process_id) == WAVE_STATUS_FORMING
    )
    confirmed_ids = tuple(
        wi.wave_process_id
        for wi in vis_ids
        if latest_status_by_wp.get(wi.wave_process_id) == WAVE_STATUS_CONFIRMED
    )

    return WaveRepresentationAsOfView(
        timeline_id=bundle.timeline_id,
        axis=bundle.axis,
        query_key=at_key,
        representation_spec_hash=bundle.representation_spec.representation_spec_hash,
        authority_policy_hash=bundle.policy_artifact.policy_hash,
        visible_turning_points=vis_tps,
        visible_wave_identities=vis_ids,
        visible_running_observations=vis_obs,
        visible_finalized_geometries=vis_geoms,
        visible_status_events=vis_events,
        forming_wave_process_ids=forming_ids,
        confirmed_wave_process_ids=confirmed_ids,
    )


def _published_records_equal(left: PublishedRecord, right: PublishedRecord) -> bool:
    return (
        left.record_identity == right.record_identity
        and left.record_type == right.record_type
        and left.schema_identity == right.schema_identity
        and left.timeline_id == right.timeline_id
        and left.availability_key == right.availability_key
        and left.content == right.content
    )


def _record_tuples_equal(left_seq: Sequence[Any], right_seq: Sequence[Any]) -> bool:
    if len(left_seq) != len(right_seq):
        return False
    for left_item, right_item in zip(left_seq, right_seq):
        if not _published_records_equal(
            left_item.published_record, right_item.published_record
        ):
            return False
    return True


def verify_wave_prefix_invariance(
    bars: Sequence[PublishedOhlcBarFact],
    *,
    prefix_length: int,
    full_witness_bundle: DetectorWitnessBundle,
    prefix_witness_bundle: DetectorWitnessBundle,
    representation_spec: CandidateWaveRepresentationSpec,
    policy_artifact: PolicyArtifact,
    dataset_identity: DatasetIdentityArtifact,
    dataset_role: DatasetRoleArtifact,
) -> bool:
    """Verify that appending future bars never mutates wave identities or observations at prefix_cutoff (I-IMM-3)."""
    bar_tuple = tuple(bars)
    if prefix_length < 1 or prefix_length > len(bar_tuple):
        raise SchemaViolation("prefix_length out of range")
    prefix_bars = bar_tuple[:prefix_length]
    cutoff_key = prefix_bars[-1].availability_key

    full_bundle = construct_candidate_wave_representation(
        bar_tuple,
        witness_bundle=full_witness_bundle,
        representation_spec=representation_spec,
        policy_artifact=policy_artifact,
        dataset_identity=dataset_identity,
        dataset_role=dataset_role,
    )
    prefix_bundle = construct_candidate_wave_representation(
        prefix_bars,
        witness_bundle=prefix_witness_bundle,
        representation_spec=representation_spec,
        policy_artifact=policy_artifact,
        dataset_identity=dataset_identity,
        dataset_role=dataset_role,
    )

    view_from_full = query_wave_representation_as_of(
        full_bundle, at_key=cutoff_key
    )
    view_from_prefix = query_wave_representation_as_of(
        prefix_bundle, at_key=cutoff_key
    )
    if (
        view_from_full.forming_wave_process_ids
        != view_from_prefix.forming_wave_process_ids
        or view_from_full.confirmed_wave_process_ids
        != view_from_prefix.confirmed_wave_process_ids
        or not _record_tuples_equal(
            view_from_full.visible_turning_points,
            view_from_prefix.visible_turning_points,
        )
        or not _record_tuples_equal(
            view_from_full.visible_wave_identities,
            view_from_prefix.visible_wave_identities,
        )
        or not _record_tuples_equal(
            view_from_full.visible_running_observations,
            view_from_prefix.visible_running_observations,
        )
        or not _record_tuples_equal(
            view_from_full.visible_finalized_geometries,
            view_from_prefix.visible_finalized_geometries,
        )
        or not _record_tuples_equal(
            view_from_full.visible_status_events,
            view_from_prefix.visible_status_events,
        )
    ):
        raise SchemaViolation(
            "prefix wave invariance violated between prefix bundle and full bundle as-of view"
        )
    return True


@dataclass(frozen=True)
class StructuralQualificationCriteria(ImmutableRecord):
    """Predefined structural non-degeneracy criteria for Gate G1 (D2-3, I-SEL-1)."""

    criteria_id: str
    min_wave_identities: int
    min_confirmed_waves: int
    require_causal_prefix_invariance: bool

    def __post_init__(self) -> None:
        _require_non_empty_str(
            self.criteria_id, "criteria_id", G1_INVALID_QUALIFICATION_CRITERIA
        )
        if (
            isinstance(self.min_wave_identities, bool)
            or not isinstance(self.min_wave_identities, int)
            or self.min_wave_identities < 0
        ):
            raise SchemaViolation(
                f"{G1_INVALID_QUALIFICATION_CRITERIA}: min_wave_identities must be >= 0"
            )
        if (
            isinstance(self.min_confirmed_waves, bool)
            or not isinstance(self.min_confirmed_waves, int)
            or self.min_confirmed_waves < 0
        ):
            raise SchemaViolation(
                f"{G1_INVALID_QUALIFICATION_CRITERIA}: min_confirmed_waves must be >= 0"
            )
        if not isinstance(self.require_causal_prefix_invariance, bool):
            raise SchemaViolation(
                f"{G1_INVALID_QUALIFICATION_CRITERIA}: require_causal_prefix_invariance must be bool"
            )


@dataclass(frozen=True)
class StructuralQualificationRecord(ImmutableRecord):
    """Gate G1 Structural Qualification output: ELIGIBLE or INELIGIBLE only, NEVER a winner (D2-3, I-SEL-1)."""

    qualification_id: str
    representation_spec_hash: str
    authority_policy_hash: str
    dataset_id: str
    dataset_role: str
    evaluation_cutoff_key: InformationKey
    qualification_status: str
    ineligibility_reasons: Tuple[str, ...]
    wave_identity_count: int
    confirmed_wave_count: int
    prefix_invariance_verified: bool
    claim_boundary: str
    qualification_hash: str

    def __post_init__(self) -> None:
        _require_non_empty_str(
            self.qualification_id,
            "qualification_id",
            G1_INVALID_QUALIFICATION_RECORD,
        )
        _require_non_empty_str(
            self.representation_spec_hash,
            "representation_spec_hash",
            G1_INVALID_QUALIFICATION_RECORD,
        )
        _require_non_empty_str(
            self.authority_policy_hash,
            "authority_policy_hash",
            G1_INVALID_QUALIFICATION_RECORD,
        )
        _require_non_empty_str(
            self.dataset_id, "dataset_id", G1_INVALID_QUALIFICATION_RECORD
        )
        if self.dataset_role not in (
            DATASET_ROLE_DEVELOPMENT_FIT,
            DATASET_ROLE_DEVELOPMENT_SELECTION,
        ):
            raise SelectionBlockedError(
                f"{G1_BLOCKED_FINAL_DATASET_FORBIDDEN}: Gate G1 forbids dataset role {self.dataset_role!r}"
            )
        _require_completed_key(
            self.evaluation_cutoff_key,
            "evaluation_cutoff_key",
            G1_INVALID_QUALIFICATION_RECORD,
        )
        if self.qualification_status not in LEGAL_G1_STATUSES:
            raise SchemaViolation(
                f"{G1_INVALID_QUALIFICATION_RECORD}: qualification_status must be ELIGIBLE or INELIGIBLE, "
                f"got {self.qualification_status!r} (no WINNER allowed, I-SEL-1)"
            )
        reasons = tuple(self.ineligibility_reasons)
        object.__setattr__(self, "ineligibility_reasons", reasons)
        if self.qualification_status == G1_STATUS_ELIGIBLE and len(reasons) != 0:
            raise SchemaViolation(
                f"{G1_INVALID_QUALIFICATION_RECORD}: ELIGIBLE record cannot have ineligibility_reasons"
            )
        if (
            self.qualification_status == G1_STATUS_INELIGIBLE
            and len(reasons) == 0
        ):
            raise SchemaViolation(
                f"{G1_INVALID_QUALIFICATION_RECORD}: INELIGIBLE record requires non-empty ineligibility_reasons"
            )
        if self.claim_boundary != G1_CLAIM_BOUNDARY:
            raise SelectionBlockedError(
                f"{G1_WINNER_CLAIM_FORBIDDEN}: claim_boundary must equal {G1_CLAIM_BOUNDARY!r}"
            )

        expected_hash = canonical_artifact_identity(
            G1_QUALIFICATION_RECORD_SCHEMA,
            identity_payload={
                "qualification_id": self.qualification_id,
                "representation_spec_hash": self.representation_spec_hash,
                "authority_policy_hash": self.authority_policy_hash,
                "dataset_id": self.dataset_id,
                "dataset_role": self.dataset_role,
                "evaluation_cutoff_key": self.evaluation_cutoff_key,
                "qualification_status": self.qualification_status,
                "ineligibility_reasons": _serialize_seq(reasons),
                "claim_boundary": self.claim_boundary,
            },
            proof_payload={
                "wave_identity_count": str(self.wave_identity_count),
                "confirmed_wave_count": str(self.confirmed_wave_count),
                "prefix_invariance_verified": str(self.prefix_invariance_verified),
            },
        )
        if self.qualification_hash != expected_hash:
            raise SchemaViolation(
                f"{G1_INVALID_QUALIFICATION_RECORD}: qualification_hash mismatch"
            )


def evaluate_g1_structural_qualification(
    bundle: CandidateWaveRepresentationBundle,
    *,
    qualification_id: str,
    criteria: StructuralQualificationCriteria,
    prefix_invariance_verified: bool = True,
    claim_predictive_winner: bool = False,
) -> StructuralQualificationRecord:
    """Evaluate Gate G1 Structural Qualification (D2-3, D2-17, D2-22, I-SEL-1, Attacks 27 & 38).

    Emits ELIGIBLE or INELIGIBLE(reasons) only. Never declares a predictive winner.
    """
    if claim_predictive_winner:
        raise SelectionBlockedError(
            f"{G1_WINNER_CLAIM_FORBIDDEN}: Gate G1 is structural qualification only "
            "(ELIGIBLE/INELIGIBLE) and cannot claim a predictive winner (I-SEL-1, Attack 27)"
        )
    if not isinstance(bundle, CandidateWaveRepresentationBundle):
        raise SchemaViolation("bundle must be a CandidateWaveRepresentationBundle")
    if not isinstance(criteria, StructuralQualificationCriteria):
        raise SchemaViolation(
            "criteria must be a StructuralQualificationCriteria"
        )
    if bundle.dataset_role not in (
        DATASET_ROLE_DEVELOPMENT_FIT,
        DATASET_ROLE_DEVELOPMENT_SELECTION,
    ):
        raise SelectionBlockedError(
            f"{G1_BLOCKED_FINAL_DATASET_FORBIDDEN}: Gate G1 forbids dataset role {bundle.dataset_role!r}"
        )

    reasons: list[str] = []
    wp_count = len(bundle.wave_identity_records)
    conf_count = len(bundle.finalized_wave_geometries)

    if wp_count < criteria.min_wave_identities:
        reasons.append(
            f"INSUFFICIENT_WAVE_IDENTITIES:{wp_count}<{criteria.min_wave_identities}"
        )
    if conf_count < criteria.min_confirmed_waves:
        reasons.append(
            f"INSUFFICIENT_CONFIRMED_WAVES:{conf_count}<{criteria.min_confirmed_waves}"
        )
    if criteria.require_causal_prefix_invariance and not prefix_invariance_verified:
        reasons.append("CAUSAL_PREFIX_INVARIANCE_NOT_VERIFIED")

    status = G1_STATUS_ELIGIBLE if len(reasons) == 0 else G1_STATUS_INELIGIBLE
    reasons_tuple = tuple(reasons)
    cutoff_key = bundle.observation_keys[-1]

    q_hash = canonical_artifact_identity(
        G1_QUALIFICATION_RECORD_SCHEMA,
        identity_payload={
            "qualification_id": qualification_id,
            "representation_spec_hash": bundle.representation_spec.representation_spec_hash,
            "authority_policy_hash": bundle.policy_artifact.policy_hash,
            "dataset_id": bundle.dataset_id,
            "dataset_role": bundle.dataset_role,
            "evaluation_cutoff_key": cutoff_key,
            "qualification_status": status,
            "ineligibility_reasons": _serialize_seq(reasons_tuple),
            "claim_boundary": G1_CLAIM_BOUNDARY,
        },
        proof_payload={
            "wave_identity_count": str(wp_count),
            "confirmed_wave_count": str(conf_count),
            "prefix_invariance_verified": str(prefix_invariance_verified),
        },
    )
    return StructuralQualificationRecord(
        qualification_id=qualification_id,
        representation_spec_hash=bundle.representation_spec.representation_spec_hash,
        authority_policy_hash=bundle.policy_artifact.policy_hash,
        dataset_id=bundle.dataset_id,
        dataset_role=bundle.dataset_role,
        evaluation_cutoff_key=cutoff_key,
        qualification_status=status,
        ineligibility_reasons=reasons_tuple,
        wave_identity_count=wp_count,
        confirmed_wave_count=conf_count,
        prefix_invariance_verified=prefix_invariance_verified,
        claim_boundary=G1_CLAIM_BOUNDARY,
        qualification_hash=q_hash,
    )


__all__ = [
    "CandidateWaveRepresentationBundle",
    "CandidateWaveRepresentationSpec",
    "FAMILIES_FORBIDDING_INTRINSIC_SCALE",
    "FAMILY_ALPHA_POLICY_SCALE",
    "FAMILY_BETA_PARAMETER_FREE",
    "FAMILY_DELTA_EVENT_CONTAINMENT",
    "FAMILY_GAMMA_RESIDUAL",
    "FINALIZED_WAVE_GEOMETRY_SCHEMA",
    "FinalizedWaveGeometryRecord",
    "G1_BLOCKED_FINAL_DATASET_FORBIDDEN",
    "G1_CLAIM_BOUNDARY",
    "G1_INVALID_QUALIFICATION_CRITERIA",
    "G1_INVALID_QUALIFICATION_RECORD",
    "G1_QUALIFICATION_RECORD_SCHEMA",
    "G1_STATUS_ELIGIBLE",
    "G1_STATUS_INELIGIBLE",
    "G1_WINNER_CLAIM_FORBIDDEN",
    "LEGAL_G1_STATUSES",
    "LEGAL_REPRESENTATION_FAMILIES",
    "LEGAL_WAVE_STATUSES",
    "REPRESENTATION_SPEC_IDENTITY_SCHEMA",
    "RUNNING_WAVE_OBSERVATION_SCHEMA",
    "RunningWaveObservationRecord",
    "S5_FINALIZED_WAVE_GEOMETRY_RECORD_TYPE",
    "S5_FINAL_DATASET_FORBIDDEN_IN_CANDIDATE_CONSTRUCTION",
    "S5_IDENTITY_RULE_NOT_CONFIGURED",
    "S5_INTRINSIC_SCALE_FORBIDDEN_FOR_FAMILY",
    "S5_INTRINSIC_SCALE_REQUIRED_FOR_ALPHA",
    "S5_INVALID_DEVELOPMENT_BAR_STREAM",
    "S5_INVALID_FINALIZED_GEOMETRY",
    "S5_INVALID_REPRESENTATION_SPEC",
    "S5_INVALID_RUNNING_OBSERVATION",
    "S5_INVALID_WAVE_BUNDLE",
    "S5_INVALID_WAVE_IDENTITY_RECORD",
    "S5_INVALID_WAVE_STATUS_EVENT",
    "S5_NON_EARLIEST_WAVE_AVAILABILITY",
    "S5_POLICY_AUTHORITY_MISSING",
    "S5_RUNNING_WAVE_OBSERVATION_RECORD_TYPE",
    "S5_SCHEMA_IDENTITY",
    "S5_WAVE_IDENTITY_RECORD_TYPE",
    "S5_WAVE_STATUS_EVENT_RECORD_TYPE",
    "StructuralQualificationCriteria",
    "StructuralQualificationRecord",
    "WAVE_STATUS_CONFIRMED",
    "WAVE_STATUS_EVENT_SCHEMA",
    "WAVE_STATUS_FORMING",
    "WAVE_STATUS_SUPERSEDED",
    "WaveIdentityRecord",
    "WaveRepresentationAsOfView",
    "WaveStatusEventRecord",
    "construct_candidate_wave_representation",
    "evaluate_g1_structural_qualification",
    "query_wave_representation_as_of",
    "verify_wave_prefix_invariance",
]
