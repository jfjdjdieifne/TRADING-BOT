"""MUF V1 S3: Research-Governance Infrastructure & Authority Gate G0.

Implements the S3 governance contracts and Gate G0 required before any S4
development policy calibration or S5 wave representation construction:
- ``ObjectiveArtifact`` (D1-1, D2-3, I-OA-1..5)
- ``DatasetIdentityArtifact``, ``DatasetRoleArtifact``, and exposure/ancestry
  firewalls (D1-2, D2-6, D2-7, I-DR-1..5, I-DATA-1..5, I-RES-1..2)
- ``FoldProtocolArtifact`` and walk-forward vs final-data firewall
  (D1-2, D2-18, I-WF-1..3)
- ``HumanReviewRecord`` and automatic final-data contamination tripwire
  (D1-3, D2-10, I-HR-1..2)
- ``RepresentationExperimentRecord`` and append-only ``ExperimentRegistry``
  (D1-16, I-ER-1..5)
- ``PolicyArtifact`` infrastructure, reproduction verification, and
  ``AuthoritativeTurningPointRecord`` promotion from S2 ``SwingEventWitnessRecord``
  (D1-4, D2-1, I-PAUTH-1..4)
- ``evaluate_g0_calibration_gate`` (D1-21, D2-22, Gate G0)

S3 performs ZERO parameter fitting, invents ZERO market thresholds/windows/
quantiles/horizons, and defines QualificationObjective as
``TypedState.UNDEFINED`` unless explicitly supplied by an authorized
``ObjectiveArtifact``.
"""
from dataclasses import dataclass
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
    MufS0ContractError,
    PrematureAvailability,
    SchemaIdentity,
    SchemaViolation,
    TypedState,
)
from trading_system.market_understanding.detector_witness import (
    S2_ADAPTER_ENGINE_IDENTITY,
    SwingEventWitnessRecord,
)
from trading_system.market_understanding.identity import (
    TURNING_POINT_RECORD_TYPE,
    ArtifactIdentitySchema,
    AuthoritativeTurningPointReference,
    canonical_artifact_identity,
)
from trading_system.market_understanding.price_path import (
    EXACT,
    MetricResult,
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


S3_SCHEMA_IDENTITY = SchemaIdentity("MUF_S3_POLICY_GOVERNANCE", "V1")

# QualificationObjective standing state in S3 (I-OA-5)
QUALIFICATION_OBJECTIVE_DEFAULT = TypedState.UNDEFINED
FOLD_PROTOCOL_DEFAULT = TypedState.NOT_CONFIGURED

# Objective kinds (D1-1)
OBJECTIVE_KIND_DETECTION_VALIDITY = "DETECTION_VALIDITY"
OBJECTIVE_KIND_REPRESENTATION_DIAGNOSTIC = "REPRESENTATION_DIAGNOSTIC"
OBJECTIVE_KIND_INFORMATION = "INFORMATION_OBJECTIVE"
OBJECTIVE_KIND_ECONOMIC_FORBIDDEN = "ECONOMIC_OBJECTIVE"
LEGAL_OBJECTIVE_KINDS = frozenset(
    {
        OBJECTIVE_KIND_DETECTION_VALIDITY,
        OBJECTIVE_KIND_REPRESENTATION_DIAGNOSTIC,
        OBJECTIVE_KIND_INFORMATION,
    }
)

# Dataset roles & exposure states (D1-2, D2-6)
DATASET_ROLE_DEVELOPMENT_FIT = "DEVELOPMENT_FIT"
DATASET_ROLE_DEVELOPMENT_SELECTION = "DEVELOPMENT_SELECTION"
DATASET_ROLE_FINAL_EVALUATION_LOCKED = "FINAL_EVALUATION_LOCKED"
LEGAL_DATASET_ROLES = frozenset(
    {
        DATASET_ROLE_DEVELOPMENT_FIT,
        DATASET_ROLE_DEVELOPMENT_SELECTION,
        DATASET_ROLE_FINAL_EVALUATION_LOCKED,
    }
)

EXPOSURE_STATE_UNEXPOSED = "UNEXPOSED"
EXPOSURE_STATE_EXPOSED_DEVELOPMENT = "EXPOSED_DEVELOPMENT"
EXPOSURE_STATE_EXPOSED_FINAL = "EXPOSED_FINAL"
EXPOSURE_STATE_EXPOSED_INVALID_FOR_FINAL = "EXPOSED_INVALID_FOR_FINAL_SELECTION"
LEGAL_EXPOSURE_STATES = frozenset(
    {
        EXPOSURE_STATE_UNEXPOSED,
        EXPOSURE_STATE_EXPOSED_DEVELOPMENT,
        EXPOSURE_STATE_EXPOSED_FINAL,
        EXPOSURE_STATE_EXPOSED_INVALID_FOR_FINAL,
    }
)

RESERVATION_STATUS_NOT_APPLICABLE = "NOT_APPLICABLE_DEVELOPMENT_ROLE"
RESERVATION_STATUS_FINAL_RESERVED = "FINAL_DATA_RESERVED"
RESERVATION_STATUS_FINAL_OPENED = "FINAL_EVALUATION_OPENED"
RESERVATION_STATUS_FINAL_INVALIDATED = "FINAL_EVALUATION_INVALIDATED"
LEGAL_RESERVATION_STATUSES = frozenset(
    {
        RESERVATION_STATUS_NOT_APPLICABLE,
        RESERVATION_STATUS_FINAL_RESERVED,
        RESERVATION_STATUS_FINAL_OPENED,
        RESERVATION_STATUS_FINAL_INVALIDATED,
    }
)

# Human review constants (D1-3)
REVIEW_KIND_DEVELOPMENT_AUDIT = "DEVELOPMENT_REALITY_AUDIT"
REVIEW_KIND_FINAL_AUDIT = "FINAL_EVALUATION_REALITY_AUDIT"
LEGAL_REVIEW_KINDS = frozenset(
    {
        REVIEW_KIND_DEVELOPMENT_AUDIT,
        REVIEW_KIND_FINAL_AUDIT,
    }
)

INFLUENCE_NONE = "NONE"
INFLUENCE_DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"
INFLUENCE_DESIGN_INFLUENCING = "DESIGN_INFLUENCING"
LEGAL_CHANGE_INFLUENCES = frozenset(
    {
        INFLUENCE_NONE,
        INFLUENCE_DIAGNOSTIC_ONLY,
        INFLUENCE_DESIGN_INFLUENCING,
    }
)

# Experiment registry constants (D1-16)
EXPERIMENT_STATUS_PREREGISTERED = "PREREGISTERED"
EXPERIMENT_STATUS_RUNNING = "RUNNING"
EXPERIMENT_STATUS_COMPLETED = "COMPLETED"
EXPERIMENT_STATUS_FAILED = "FAILED"
EXPERIMENT_STATUS_SUPERSEDED = "SUPERSEDED"
LEGAL_EXPERIMENT_STATUSES = frozenset(
    {
        EXPERIMENT_STATUS_PREREGISTERED,
        EXPERIMENT_STATUS_RUNNING,
        EXPERIMENT_STATUS_COMPLETED,
        EXPERIMENT_STATUS_FAILED,
        EXPERIMENT_STATUS_SUPERSEDED,
    }
)

# Policy authority & provenance constants (D1-4)
POLICY_AUTHORITY_KIND_MUF = "MUF_POLICY_ARTIFACT"
POLICY_AUTHORITY_KIND_PREDEFINED = "PREDEFINED_EQUIVALENT_CONTRACT"
LEGAL_POLICY_AUTHORITY_KINDS = frozenset(
    {
        POLICY_AUTHORITY_KIND_MUF,
        POLICY_AUTHORITY_KIND_PREDEFINED,
    }
)

PROVENANCE_PREDEFINED_CONTRACT = "PREDEFINED_DECLARED_CONTRACT"
PROVENANCE_DEVELOPMENT_FIT = "DEVELOPMENT_FIT_CALIBRATED"
LEGAL_CALIBRATION_PROVENANCE_KINDS = frozenset(
    {
        PROVENANCE_PREDEFINED_CONTRACT,
        PROVENANCE_DEVELOPMENT_FIT,
    }
)

# Deterministic S3 & G0 error reason codes
S3_ECONOMIC_OBJECTIVE_OUT_OF_SCOPE = "S3_ECONOMIC_OBJECTIVE_OUT_OF_SCOPE"
S3_INVALID_OBJECTIVE_ARTIFACT = "S3_INVALID_OBJECTIVE_ARTIFACT"
S3_INFORMATION_OBJECTIVE_REQUIRES_ESTIMAND = "S3_INFORMATION_OBJECTIVE_REQUIRES_ESTIMAND"
S3_NON_INFORMATION_OBJECTIVE_FORBIDS_ESTIMAND = (
    "S3_NON_INFORMATION_OBJECTIVE_FORBIDS_ESTIMAND"
)
S3_INVALID_DATASET_IDENTITY = "S3_INVALID_DATASET_IDENTITY"
S3_UNDECLARED_SHARED_CONTENT_ANCESTRY = "S3_UNDECLARED_SHARED_CONTENT_ANCESTRY"
S3_TEMPORAL_OVERLAP_NOT_INDEPENDENT = "S3_TEMPORAL_OVERLAP_NOT_INDEPENDENT"
S3_EXPOSED_ANCESTRY_CONTAMINATION = "S3_EXPOSED_ANCESTRY_CONTAMINATION"
S3_INVALID_DATASET_ROLE = "S3_INVALID_DATASET_ROLE"
S3_ROLE_REASSIGNMENT_AFTER_EXPOSURE = "S3_ROLE_REASSIGNMENT_AFTER_EXPOSURE"
S3_ILLEGAL_FINAL_DATA_OPERATION = "S3_ILLEGAL_FINAL_DATA_OPERATION"
S3_PREMATURE_FINAL_INSPECTION = "S3_PREMATURE_FINAL_INSPECTION"
S3_FINAL_DATA_LEAKED_INTO_WALK_FORWARD = "S3_FINAL_DATA_LEAKED_INTO_WALK_FORWARD"
S3_INVALID_FOLD_PROTOCOL = "S3_INVALID_FOLD_PROTOCOL"
S3_INVALID_HUMAN_REVIEW = "S3_INVALID_HUMAN_REVIEW"
S3_CONTRADICTORY_REVIEW_INFLUENCE = "S3_CONTRADICTORY_REVIEW_INFLUENCE"
S3_FINAL_DATASET_CONTAMINATED_BY_REVIEW = "S3_FINAL_DATASET_CONTAMINATED_BY_REVIEW"
S3_INVALID_EXPERIMENT_RECORD = "S3_INVALID_EXPERIMENT_RECORD"
S3_EXPERIMENT_IDENTITY_COLLISION = "S3_EXPERIMENT_IDENTITY_COLLISION"
S3_EXPERIMENT_DELETION_FORBIDDEN = "S3_EXPERIMENT_DELETION_FORBIDDEN"
S3_UNREGISTERED_EXPERIMENT = "S3_UNREGISTERED_EXPERIMENT"
S3_INVALID_POLICY_ARTIFACT = "S3_INVALID_POLICY_ARTIFACT"
S3_POLICY_REPRODUCTION_MISMATCH = "S3_POLICY_REPRODUCTION_MISMATCH"
S3_POLICY_SCOPE_MISMATCH = "S3_POLICY_SCOPE_MISMATCH"
S3_INVALID_TURNING_POINT_PROMOTION = "S3_INVALID_TURNING_POINT_PROMOTION"

G0_BLOCKED_OBJECTIVE_UNDEFINED = "G0_BLOCKED_OBJECTIVE_UNDEFINED"
G0_BLOCKED_INVALID_DATASET_ROLE = "G0_BLOCKED_INVALID_DATASET_ROLE"
G0_BLOCKED_FINAL_DATA_LEAKAGE = "G0_BLOCKED_FINAL_DATA_LEAKAGE"
G0_BLOCKED_UNREGISTERED_EXPERIMENT = "G0_BLOCKED_UNREGISTERED_EXPERIMENT"
G0_BLOCKED_MISSING_OWNER_AUTHORIZATION = "G0_BLOCKED_MISSING_OWNER_AUTHORIZATION"


class SelectionBlockedError(MufS0ContractError):
    """Raised when calibration or selection is attempted without required S3/G0 authority."""


class PolicyScopeMismatch(MufS0ContractError):
    """Raised when a PolicyArtifact is applied outside its declared timeline/axis/witness scope."""


# Canonical identity schemas (D2-12)
OBJECTIVE_IDENTITY_SCHEMA = ArtifactIdentitySchema(
    artifact_type="MUF_S3_OBJECTIVE_ARTIFACT",
    schema_identity=S3_SCHEMA_IDENTITY,
    identity_defining_fields=(
        "objective_id",
        "objective_kind",
        "semantic_definition",
        "estimand_refs",
        "dataset_role_permissions",
        "aggregation_contract",
        "missingness_contract",
        "tie_contract",
        "comparison_direction",
        "creation_key",
        "code_hash",
        "owner_authorization_ref",
    ),
)

DATASET_IDENTITY_SCHEMA = ArtifactIdentitySchema(
    artifact_type="MUF_S3_DATASET_IDENTITY_ARTIFACT",
    schema_identity=S3_SCHEMA_IDENTITY,
    identity_defining_fields=(
        "dataset_id",
        "content_hash",
        "source_identity",
        "timeline_id",
        "axis",
        "start_key",
        "end_key",
        "transformation_spec_hash",
        "parent_dataset_ids",
        "creation_code_hash",
        "semantic_schema_hash",
    ),
)

DATASET_ROLE_IDENTITY_SCHEMA = ArtifactIdentitySchema(
    artifact_type="MUF_S3_DATASET_ROLE_ARTIFACT",
    schema_identity=S3_SCHEMA_IDENTITY,
    identity_defining_fields=(
        "dataset_id",
        "dataset_identity_hash",
        "role",
        "role_assignment_key",
        "permitted_operations",
        "prohibited_operations",
        "owner_authorization_ref",
    ),
    proof_fields=(
        "exposure_state",
        "reservation_status",
    ),
)

FOLD_PROTOCOL_IDENTITY_SCHEMA = ArtifactIdentitySchema(
    artifact_type="MUF_S3_FOLD_PROTOCOL_ARTIFACT",
    schema_identity=S3_SCHEMA_IDENTITY,
    identity_defining_fields=(
        "protocol_id",
        "timeline_id",
        "folds",
        "owner_authorization_ref",
    ),
)

HUMAN_REVIEW_IDENTITY_SCHEMA = ArtifactIdentitySchema(
    artifact_type="MUF_S3_HUMAN_REVIEW_RECORD",
    schema_identity=S3_SCHEMA_IDENTITY,
    identity_defining_fields=(
        "review_id",
        "dataset_id",
        "dataset_role",
        "review_kind",
        "review_key",
        "reviewer",
        "artifacts_viewed",
        "charts_viewed",
        "observations",
        "requested_changes",
        "change_influence",
    ),
)

EXPERIMENT_IDENTITY_SCHEMA = ArtifactIdentitySchema(
    artifact_type="MUF_S3_REPRESENTATION_EXPERIMENT",
    schema_identity=S3_SCHEMA_IDENTITY,
    identity_defining_fields=(
        "experiment_id",
        "preregistration_key",
        "representation_spec_hash",
        "policy_artifact_hashes",
        "objective_artifact_hash",
        "dataset_identities_by_role",
        "code_hash",
        "fit_protocol_hash",
        "selection_protocol_hash",
    ),
    proof_fields=(
        "status",
        "result_refs",
        "failure_refs",
        "supersedes_experiment_id",
    ),
)

POLICY_ARTIFACT_IDENTITY_SCHEMA = ArtifactIdentitySchema(
    artifact_type="MUF_S3_POLICY_ARTIFACT",
    schema_identity=S3_SCHEMA_IDENTITY,
    identity_defining_fields=(
        "policy_id",
        "authority_kind",
        "target_engine_identity",
        "detector_policy_witness_ref",
        "scope_timeline_id",
        "scope_axis",
        "scope_representation_id",
        "calibration_provenance_kind",
        "fit_dataset_id",
        "objective_artifact_hash",
        "experiment_id",
        "fit_dataset_role_hash",
        "reproduction_recipe_hash",
        "effective_from_key",
        "owner_authorization_ref",
    ),
)

AUTHORITATIVE_TP_IDENTITY_SCHEMA = ArtifactIdentitySchema(
    artifact_type="MUF_S3_AUTHORITATIVE_TURNING_POINT",
    schema_identity=S3_SCHEMA_IDENTITY,
    identity_defining_fields=(
        "timeline_id",
        "origin_key",
        "availability_key",
        "extrema_kind",
        "authority_policy_hash",
        "witness_record_ref",
    ),
)


def _require_non_empty_str(val: Any, name: str, err_code: str) -> str:
    if not isinstance(val, str) or not val.strip():
        raise SchemaViolation(f"{err_code}: {name} must be a non-empty string")
    return val


def _require_str_tuple(val: Any, name: str, err_code: str) -> Tuple[str, ...]:
    if not isinstance(val, (tuple, list)) or isinstance(val, (str, bytes)):
        raise SchemaViolation(f"{err_code}: {name} must be a sequence of strings")
    items = tuple(val)
    for idx, item in enumerate(items):
        if not isinstance(item, str) or not item.strip():
            raise SchemaViolation(
                f"{err_code}: {name}[{idx}] must be a non-empty string"
            )
    return items


def _require_completed_key(val: Any, name: str, err_code: str) -> InformationKey:
    if not isinstance(val, InformationKey):
        raise InformationKeyViolation(f"{err_code}: {name} must be an InformationKey")
    if val.information_phase != InformationPhase.COMPLETED_ROW_AVAILABLE:
        raise IllegalCausalReference(
            f"{err_code}: {name} must have COMPLETED_ROW_AVAILABLE phase"
        )
    return val


def _serialize_seq(items: Sequence[str]) -> Mapping[str, str]:
    return {f"i_{idx}": val for idx, val in enumerate(items)}


@dataclass(frozen=True)
class ObjectiveArtifact(ImmutableRecord):
    """Typed objective contract required before any calibration or selection (D1-1, D2-3)."""

    objective_id: str
    objective_kind: str
    semantic_definition: str
    estimand_refs: Tuple[str, ...]
    dataset_role_permissions: Tuple[str, ...]
    aggregation_contract: str
    missingness_contract: str
    tie_contract: str
    comparison_direction: Union[str, TypedState]
    creation_key: InformationKey
    code_hash: str
    owner_authorization_ref: str
    objective_hash: str

    def __post_init__(self) -> None:
        _require_non_empty_str(
            self.objective_id, "objective_id", S3_INVALID_OBJECTIVE_ARTIFACT
        )
        if self.objective_kind == OBJECTIVE_KIND_ECONOMIC_FORBIDDEN:
            raise SchemaViolation(
                f"{S3_ECONOMIC_OBJECTIVE_OUT_OF_SCOPE}: ECONOMIC_OBJECTIVE is out of scope in MUF"
            )
        if self.objective_kind not in LEGAL_OBJECTIVE_KINDS:
            raise SchemaViolation(
                f"{S3_INVALID_OBJECTIVE_ARTIFACT}: illegal objective_kind {self.objective_kind!r}"
            )
        _require_non_empty_str(
            self.semantic_definition,
            "semantic_definition",
            S3_INVALID_OBJECTIVE_ARTIFACT,
        )
        est_tuple = _require_str_tuple(
            self.estimand_refs, "estimand_refs", S3_INVALID_OBJECTIVE_ARTIFACT
        )
        object.__setattr__(self, "estimand_refs", est_tuple)
        if self.objective_kind == OBJECTIVE_KIND_INFORMATION:
            if len(est_tuple) == 0:
                raise SchemaViolation(
                    f"{S3_INFORMATION_OBJECTIVE_REQUIRES_ESTIMAND}: INFORMATION_OBJECTIVE "
                    "requires at least one preregistered EstimandArtifact reference"
                )
        else:
            if len(est_tuple) != 0:
                raise SchemaViolation(
                    f"{S3_NON_INFORMATION_OBJECTIVE_FORBIDS_ESTIMAND}: {self.objective_kind} "
                    "must have empty estimand_refs"
                )

        role_perms = _require_str_tuple(
            self.dataset_role_permissions,
            "dataset_role_permissions",
            S3_INVALID_OBJECTIVE_ARTIFACT,
        )
        if len(role_perms) == 0:
            raise SchemaViolation(
                f"{S3_INVALID_OBJECTIVE_ARTIFACT}: dataset_role_permissions must be non-empty"
            )
        for r in role_perms:
            if r not in LEGAL_DATASET_ROLES:
                raise SchemaViolation(
                    f"{S3_INVALID_OBJECTIVE_ARTIFACT}: unknown dataset role {r!r}"
                )
        object.__setattr__(self, "dataset_role_permissions", role_perms)

        _require_non_empty_str(
            self.aggregation_contract,
            "aggregation_contract",
            S3_INVALID_OBJECTIVE_ARTIFACT,
        )
        _require_non_empty_str(
            self.missingness_contract,
            "missingness_contract",
            S3_INVALID_OBJECTIVE_ARTIFACT,
        )
        _require_non_empty_str(
            self.tie_contract, "tie_contract", S3_INVALID_OBJECTIVE_ARTIFACT
        )
        if self.comparison_direction is not TypedState.NOT_APPLICABLE:
            if self.comparison_direction not in (
                "MAXIMIZE",
                "MINIMIZE",
                "SATISFY_CONSTRAINT",
            ):
                raise SchemaViolation(
                    f"{S3_INVALID_OBJECTIVE_ARTIFACT}: invalid comparison_direction "
                    f"{self.comparison_direction!r}"
                )
        _require_completed_key(
            self.creation_key, "creation_key", S3_INVALID_OBJECTIVE_ARTIFACT
        )
        _require_non_empty_str(
            self.code_hash, "code_hash", S3_INVALID_OBJECTIVE_ARTIFACT
        )
        _require_non_empty_str(
            self.owner_authorization_ref,
            "owner_authorization_ref",
            S3_INVALID_OBJECTIVE_ARTIFACT,
        )

        expected_hash = canonical_artifact_identity(
            OBJECTIVE_IDENTITY_SCHEMA,
            identity_payload={
                "objective_id": self.objective_id,
                "objective_kind": self.objective_kind,
                "semantic_definition": self.semantic_definition,
                "estimand_refs": _serialize_seq(est_tuple),
                "dataset_role_permissions": _serialize_seq(role_perms),
                "aggregation_contract": self.aggregation_contract,
                "missingness_contract": self.missingness_contract,
                "tie_contract": self.tie_contract,
                "comparison_direction": self.comparison_direction,
                "creation_key": self.creation_key,
                "code_hash": self.code_hash,
                "owner_authorization_ref": self.owner_authorization_ref,
            },
        )
        if self.objective_hash != expected_hash:
            raise SchemaViolation(
                f"{S3_INVALID_OBJECTIVE_ARTIFACT}: objective_hash mismatch"
            )

    @classmethod
    def create(
        cls,
        *,
        objective_id: str,
        objective_kind: str,
        semantic_definition: str,
        estimand_refs: Sequence[str] = (),
        dataset_role_permissions: Sequence[str],
        aggregation_contract: str,
        missingness_contract: str,
        tie_contract: str,
        comparison_direction: Union[str, TypedState] = TypedState.NOT_APPLICABLE,
        creation_key: InformationKey,
        code_hash: str,
        owner_authorization_ref: str,
    ) -> "ObjectiveArtifact":
        est_tuple = _require_str_tuple(
            estimand_refs, "estimand_refs", S3_INVALID_OBJECTIVE_ARTIFACT
        )
        role_perms = _require_str_tuple(
            dataset_role_permissions,
            "dataset_role_permissions",
            S3_INVALID_OBJECTIVE_ARTIFACT,
        )
        obj_hash = canonical_artifact_identity(
            OBJECTIVE_IDENTITY_SCHEMA,
            identity_payload={
                "objective_id": objective_id,
                "objective_kind": objective_kind,
                "semantic_definition": semantic_definition,
                "estimand_refs": _serialize_seq(est_tuple),
                "dataset_role_permissions": _serialize_seq(role_perms),
                "aggregation_contract": aggregation_contract,
                "missingness_contract": missingness_contract,
                "tie_contract": tie_contract,
                "comparison_direction": comparison_direction,
                "creation_key": creation_key,
                "code_hash": code_hash,
                "owner_authorization_ref": owner_authorization_ref,
            },
        )
        return cls(
            objective_id=objective_id,
            objective_kind=objective_kind,
            semantic_definition=semantic_definition,
            estimand_refs=est_tuple,
            dataset_role_permissions=role_perms,
            aggregation_contract=aggregation_contract,
            missingness_contract=missingness_contract,
            tie_contract=tie_contract,
            comparison_direction=comparison_direction,
            creation_key=creation_key,
            code_hash=code_hash,
            owner_authorization_ref=owner_authorization_ref,
            objective_hash=obj_hash,
        )


@dataclass(frozen=True)
class DatasetIdentityArtifact(ImmutableRecord):
    """Canonical dataset identity with explicit lineage and causal extent (D2-7, I-DATA-1..5)."""

    dataset_id: str
    content_hash: str
    source_identity: SchemaIdentity
    timeline_id: str
    axis: InformationAxis
    start_key: InformationKey
    end_key: InformationKey
    transformation_spec_hash: str
    parent_dataset_ids: Tuple[str, ...]
    creation_code_hash: str
    semantic_schema_hash: str
    dataset_identity_hash: str

    def __post_init__(self) -> None:
        _require_non_empty_str(
            self.dataset_id, "dataset_id", S3_INVALID_DATASET_IDENTITY
        )
        _require_non_empty_str(
            self.content_hash, "content_hash", S3_INVALID_DATASET_IDENTITY
        )
        if not isinstance(self.source_identity, SchemaIdentity):
            raise SchemaViolation(
                f"{S3_INVALID_DATASET_IDENTITY}: source_identity must be a SchemaIdentity"
            )
        _require_non_empty_str(
            self.timeline_id, "timeline_id", S3_INVALID_DATASET_IDENTITY
        )
        if not isinstance(self.axis, InformationAxis):
            raise SchemaViolation(
                f"{S3_INVALID_DATASET_IDENTITY}: axis must be an InformationAxis"
            )
        _require_completed_key(
            self.start_key, "start_key", S3_INVALID_DATASET_IDENTITY
        )
        _require_completed_key(self.end_key, "end_key", S3_INVALID_DATASET_IDENTITY)
        if (
            self.start_key.timeline_id != self.timeline_id
            or self.end_key.timeline_id != self.timeline_id
        ):
            raise InformationKeyViolation(
                f"{S3_INVALID_DATASET_IDENTITY}: start_key/end_key timeline mismatch"
            )
        if key_axis(self.start_key) is not self.axis or key_axis(self.end_key) is not self.axis:
            raise IncomparableInformationKeys(
                f"{S3_INVALID_DATASET_IDENTITY}: start_key/end_key axis mismatch"
            )
        try:
            valid_span = self.start_key <= self.end_key
        except InformationKeyError as exc:
            raise IncomparableInformationKeys(str(exc)) from exc
        if not valid_span:
            raise SchemaViolation(
                f"{S3_INVALID_DATASET_IDENTITY}: start_key must be <= end_key"
            )
        _require_non_empty_str(
            self.transformation_spec_hash,
            "transformation_spec_hash",
            S3_INVALID_DATASET_IDENTITY,
        )
        parents = _require_str_tuple(
            self.parent_dataset_ids,
            "parent_dataset_ids",
            S3_INVALID_DATASET_IDENTITY,
        )
        if self.dataset_id in parents:
            raise SchemaViolation(
                f"{S3_INVALID_DATASET_IDENTITY}: dataset cannot be its own parent"
            )
        object.__setattr__(self, "parent_dataset_ids", parents)
        _require_non_empty_str(
            self.creation_code_hash,
            "creation_code_hash",
            S3_INVALID_DATASET_IDENTITY,
        )
        _require_non_empty_str(
            self.semantic_schema_hash,
            "semantic_schema_hash",
            S3_INVALID_DATASET_IDENTITY,
        )

        expected_hash = canonical_artifact_identity(
            DATASET_IDENTITY_SCHEMA,
            identity_payload={
                "dataset_id": self.dataset_id,
                "content_hash": self.content_hash,
                "source_identity": self.source_identity,
                "timeline_id": self.timeline_id,
                "axis": self.axis.value,
                "start_key": self.start_key,
                "end_key": self.end_key,
                "transformation_spec_hash": self.transformation_spec_hash,
                "parent_dataset_ids": _serialize_seq(parents),
                "creation_code_hash": self.creation_code_hash,
                "semantic_schema_hash": self.semantic_schema_hash,
            },
        )
        if self.dataset_identity_hash != expected_hash:
            raise SchemaViolation(
                f"{S3_INVALID_DATASET_IDENTITY}: dataset_identity_hash mismatch"
            )

    @classmethod
    def create(
        cls,
        *,
        dataset_id: str,
        content_hash: str,
        source_identity: SchemaIdentity,
        timeline_id: str,
        start_key: InformationKey,
        end_key: InformationKey,
        transformation_spec_hash: str,
        parent_dataset_ids: Sequence[str] = (),
        creation_code_hash: str,
        semantic_schema_hash: str,
    ) -> "DatasetIdentityArtifact":
        parents = _require_str_tuple(
            parent_dataset_ids, "parent_dataset_ids", S3_INVALID_DATASET_IDENTITY
        )
        axis = key_axis(start_key)
        ds_hash = canonical_artifact_identity(
            DATASET_IDENTITY_SCHEMA,
            identity_payload={
                "dataset_id": dataset_id,
                "content_hash": content_hash,
                "source_identity": source_identity,
                "timeline_id": timeline_id,
                "axis": axis.value,
                "start_key": start_key,
                "end_key": end_key,
                "transformation_spec_hash": transformation_spec_hash,
                "parent_dataset_ids": _serialize_seq(parents),
                "creation_code_hash": creation_code_hash,
                "semantic_schema_hash": semantic_schema_hash,
            },
        )
        return cls(
            dataset_id=dataset_id,
            content_hash=content_hash,
            source_identity=source_identity,
            timeline_id=timeline_id,
            axis=axis,
            start_key=start_key,
            end_key=end_key,
            transformation_spec_hash=transformation_spec_hash,
            parent_dataset_ids=parents,
            creation_code_hash=creation_code_hash,
            semantic_schema_hash=semantic_schema_hash,
            dataset_identity_hash=ds_hash,
        )


@dataclass(frozen=True)
class DatasetExposureEvent(ImmutableRecord):
    """Immutable exposure event logged against a DatasetRoleArtifact (D1-2, D2-6)."""

    event_id: str
    dataset_id: str
    exposure_key: InformationKey
    exposure_kind: str
    resulting_exposure_state: str
    actor_or_protocol_ref: str

    def __post_init__(self) -> None:
        _require_non_empty_str(self.event_id, "event_id", S3_INVALID_DATASET_ROLE)
        _require_non_empty_str(self.dataset_id, "dataset_id", S3_INVALID_DATASET_ROLE)
        _require_completed_key(
            self.exposure_key, "exposure_key", S3_INVALID_DATASET_ROLE
        )
        _require_non_empty_str(
            self.exposure_kind, "exposure_kind", S3_INVALID_DATASET_ROLE
        )
        if self.resulting_exposure_state not in LEGAL_EXPOSURE_STATES:
            raise SchemaViolation(
                f"{S3_INVALID_DATASET_ROLE}: invalid resulting_exposure_state "
                f"{self.resulting_exposure_state!r}"
            )
        _require_non_empty_str(
            self.actor_or_protocol_ref,
            "actor_or_protocol_ref",
            S3_INVALID_DATASET_ROLE,
        )


@dataclass(frozen=True)
class DatasetRoleArtifact(ImmutableRecord):
    """Dataset role & exposure firewall contract (D1-2, D2-6, I-DR-1..5, I-RES-1..2)."""

    dataset_id: str
    dataset_identity_hash: str
    role: str
    role_assignment_key: InformationKey
    permitted_operations: Tuple[str, ...]
    prohibited_operations: Tuple[str, ...]
    exposure_state: str
    reservation_status: str
    exposure_events: Tuple[DatasetExposureEvent, ...]
    owner_authorization_ref: str
    role_artifact_hash: str

    def __post_init__(self) -> None:
        _require_non_empty_str(self.dataset_id, "dataset_id", S3_INVALID_DATASET_ROLE)
        _require_non_empty_str(
            self.dataset_identity_hash,
            "dataset_identity_hash",
            S3_INVALID_DATASET_ROLE,
        )
        if self.role not in LEGAL_DATASET_ROLES:
            raise SchemaViolation(
                f"{S3_INVALID_DATASET_ROLE}: unknown role {self.role!r}"
            )
        _require_completed_key(
            self.role_assignment_key,
            "role_assignment_key",
            S3_INVALID_DATASET_ROLE,
        )
        perm_ops = _require_str_tuple(
            self.permitted_operations,
            "permitted_operations",
            S3_INVALID_DATASET_ROLE,
        )
        proh_ops = _require_str_tuple(
            self.prohibited_operations,
            "prohibited_operations",
            S3_INVALID_DATASET_ROLE,
        )
        if len(perm_ops) == 0 or len(proh_ops) == 0:
            raise SchemaViolation(
                f"{S3_INVALID_DATASET_ROLE}: permitted and prohibited operations must be non-empty"
            )
        if set(perm_ops) & set(proh_ops):
            raise SchemaViolation(
                f"{S3_INVALID_DATASET_ROLE}: overlap between permitted and prohibited operations"
            )
        if self.role == DATASET_ROLE_FINAL_EVALUATION_LOCKED:
            forbidden_on_final = {
                "DEVELOPMENT_FIT",
                "PARAMETER_CALIBRATION",
                "REPRESENTATION_SELECTION",
                "ARCHITECTURE_TUNING",
                "VISUAL_TUNING",
            }
            if set(perm_ops) & forbidden_on_final:
                raise SchemaViolation(
                    f"{S3_ILLEGAL_FINAL_DATA_OPERATION}: FINAL_EVALUATION_LOCKED cannot permit "
                    f"{sorted(set(perm_ops) & forbidden_on_final)}"
                )
            if self.reservation_status == RESERVATION_STATUS_NOT_APPLICABLE:
                raise SchemaViolation(
                    f"{S3_INVALID_DATASET_ROLE}: FINAL_EVALUATION_LOCKED requires a final reservation_status"
                )
        else:
            if self.reservation_status != RESERVATION_STATUS_NOT_APPLICABLE:
                raise SchemaViolation(
                    f"{S3_INVALID_DATASET_ROLE}: development role must have "
                    f"reservation_status={RESERVATION_STATUS_NOT_APPLICABLE!r}"
                )

        if self.exposure_state not in LEGAL_EXPOSURE_STATES:
            raise SchemaViolation(
                f"{S3_INVALID_DATASET_ROLE}: invalid exposure_state {self.exposure_state!r}"
            )
        if self.reservation_status not in LEGAL_RESERVATION_STATUSES:
            raise SchemaViolation(
                f"{S3_INVALID_DATASET_ROLE}: invalid reservation_status {self.reservation_status!r}"
            )
        object.__setattr__(self, "permitted_operations", perm_ops)
        object.__setattr__(self, "prohibited_operations", proh_ops)

        ev_tuple = tuple(self.exposure_events)
        prev_exp_key: Optional[InformationKey] = None
        for ev in ev_tuple:
            if not isinstance(ev, DatasetExposureEvent):
                raise SchemaViolation(
                    f"{S3_INVALID_DATASET_ROLE}: exposure_events must contain DatasetExposureEvent"
                )
            if ev.dataset_id != self.dataset_id:
                raise SchemaViolation(
                    f"{S3_INVALID_DATASET_ROLE}: exposure event dataset_id mismatch"
                )
            # I-DR-1: role_assignment_key must be <= every exposure event key
            try:
                assigned_before = self.role_assignment_key <= ev.exposure_key
                monotonic_exp = (
                    True if prev_exp_key is None else (prev_exp_key <= ev.exposure_key)
                )
            except InformationKeyError as exc:
                raise IncomparableInformationKeys(str(exc)) from exc
            if not assigned_before:
                raise SchemaViolation(
                    f"{S3_ROLE_REASSIGNMENT_AFTER_EXPOSURE}: role_assignment_key "
                    "cannot be later than an existing exposure event (I-DR-1)"
                )
            if not monotonic_exp:
                raise PrematureAvailability(
                    f"{S3_INVALID_DATASET_ROLE}: exposure_events must be in causal order"
                )
            prev_exp_key = ev.exposure_key
        object.__setattr__(self, "exposure_events", ev_tuple)

        if len(ev_tuple) == 0 and self.exposure_state != EXPOSURE_STATE_UNEXPOSED:
            raise SchemaViolation(
                f"{S3_INVALID_DATASET_ROLE}: non-UNEXPOSED state requires at least one exposure event"
            )
        if len(ev_tuple) > 0 and ev_tuple[-1].resulting_exposure_state != self.exposure_state:
            raise SchemaViolation(
                f"{S3_INVALID_DATASET_ROLE}: exposure_state must match latest exposure event"
            )

        _require_non_empty_str(
            self.owner_authorization_ref,
            "owner_authorization_ref",
            S3_INVALID_DATASET_ROLE,
        )
        expected_hash = canonical_artifact_identity(
            DATASET_ROLE_IDENTITY_SCHEMA,
            identity_payload={
                "dataset_id": self.dataset_id,
                "dataset_identity_hash": self.dataset_identity_hash,
                "role": self.role,
                "role_assignment_key": self.role_assignment_key,
                "permitted_operations": _serialize_seq(perm_ops),
                "prohibited_operations": _serialize_seq(proh_ops),
                "owner_authorization_ref": self.owner_authorization_ref,
            },
            proof_payload={
                "exposure_state": self.exposure_state,
                "reservation_status": self.reservation_status,
            },
        )
        if self.role_artifact_hash != expected_hash:
            raise SchemaViolation(
                f"{S3_INVALID_DATASET_ROLE}: role_artifact_hash mismatch"
            )

    @classmethod
    def create(
        cls,
        *,
        dataset_identity: DatasetIdentityArtifact,
        role: str,
        role_assignment_key: InformationKey,
        permitted_operations: Sequence[str],
        prohibited_operations: Sequence[str],
        owner_authorization_ref: str,
    ) -> "DatasetRoleArtifact":
        if not isinstance(dataset_identity, DatasetIdentityArtifact):
            raise SchemaViolation(
                f"{S3_INVALID_DATASET_ROLE}: dataset_identity must be a DatasetIdentityArtifact"
            )
        perm_ops = _require_str_tuple(
            permitted_operations, "permitted_operations", S3_INVALID_DATASET_ROLE
        )
        proh_ops = _require_str_tuple(
            prohibited_operations, "prohibited_operations", S3_INVALID_DATASET_ROLE
        )
        res_status = (
            RESERVATION_STATUS_FINAL_RESERVED
            if role == DATASET_ROLE_FINAL_EVALUATION_LOCKED
            else RESERVATION_STATUS_NOT_APPLICABLE
        )
        role_hash = canonical_artifact_identity(
            DATASET_ROLE_IDENTITY_SCHEMA,
            identity_payload={
                "dataset_id": dataset_identity.dataset_id,
                "dataset_identity_hash": dataset_identity.dataset_identity_hash,
                "role": role,
                "role_assignment_key": role_assignment_key,
                "permitted_operations": _serialize_seq(perm_ops),
                "prohibited_operations": _serialize_seq(proh_ops),
                "owner_authorization_ref": owner_authorization_ref,
            },
            proof_payload={
                "exposure_state": EXPOSURE_STATE_UNEXPOSED,
                "reservation_status": res_status,
            },
        )
        return cls(
            dataset_id=dataset_identity.dataset_id,
            dataset_identity_hash=dataset_identity.dataset_identity_hash,
            role=role,
            role_assignment_key=role_assignment_key,
            permitted_operations=perm_ops,
            prohibited_operations=proh_ops,
            exposure_state=EXPOSURE_STATE_UNEXPOSED,
            reservation_status=res_status,
            exposure_events=(),
            owner_authorization_ref=owner_authorization_ref,
            role_artifact_hash=role_hash,
        )


def record_dataset_exposure(
    role_artifact: DatasetRoleArtifact,
    *,
    event_id: str,
    exposure_key: InformationKey,
    exposure_kind: str,
    actor_or_protocol_ref: str,
    authorized_final_open: bool = False,
    design_influencing: bool = False,
) -> DatasetRoleArtifact:
    """Append an exposure event to a DatasetRoleArtifact (D1-2, D2-6, I-DR-1..4, I-RES-1..2)."""
    if not isinstance(role_artifact, DatasetRoleArtifact):
        raise SchemaViolation("role_artifact must be a DatasetRoleArtifact")
    if role_artifact.role == DATASET_ROLE_FINAL_EVALUATION_LOCKED:
        if (
            design_influencing
            or not authorized_final_open
            or role_artifact.exposure_state != EXPOSURE_STATE_UNEXPOSED
        ):
            new_state = EXPOSURE_STATE_EXPOSED_INVALID_FOR_FINAL
            new_res = RESERVATION_STATUS_FINAL_INVALIDATED
        else:
            new_state = EXPOSURE_STATE_EXPOSED_FINAL
            new_res = RESERVATION_STATUS_FINAL_OPENED
    else:
        new_state = EXPOSURE_STATE_EXPOSED_DEVELOPMENT
        new_res = RESERVATION_STATUS_NOT_APPLICABLE

    ev = DatasetExposureEvent(
        event_id=event_id,
        dataset_id=role_artifact.dataset_id,
        exposure_key=exposure_key,
        exposure_kind=exposure_kind,
        resulting_exposure_state=new_state,
        actor_or_protocol_ref=actor_or_protocol_ref,
    )
    return DatasetRoleArtifact(
        dataset_id=role_artifact.dataset_id,
        dataset_identity_hash=role_artifact.dataset_identity_hash,
        role=role_artifact.role,
        role_assignment_key=role_artifact.role_assignment_key,
        permitted_operations=role_artifact.permitted_operations,
        prohibited_operations=role_artifact.prohibited_operations,
        exposure_state=new_state,
        reservation_status=new_res,
        exposure_events=role_artifact.exposure_events + (ev,),
        owner_authorization_ref=role_artifact.owner_authorization_ref,
        role_artifact_hash=role_artifact.role_artifact_hash,
    )


def reassign_dataset_role(
    role_artifact: DatasetRoleArtifact,
    *,
    dataset_identity: DatasetIdentityArtifact,
    new_role: str,
    reassignment_key: InformationKey,
    permitted_operations: Sequence[str],
    prohibited_operations: Sequence[str],
    owner_authorization_ref: str,
) -> DatasetRoleArtifact:
    """Attempt to reassign a dataset's role; fails closed if already exposed (I-DR-1, I-WF-1, Attack 46)."""
    if not isinstance(role_artifact, DatasetRoleArtifact):
        raise SchemaViolation("role_artifact must be a DatasetRoleArtifact")
    if (
        role_artifact.exposure_state != EXPOSURE_STATE_UNEXPOSED
        or len(role_artifact.exposure_events) > 0
    ):
        raise SchemaViolation(
            f"{S3_ROLE_REASSIGNMENT_AFTER_EXPOSURE}: cannot reassign dataset "
            f"{role_artifact.dataset_id!r} to {new_role!r} after exposure "
            f"({role_artifact.exposure_state})"
        )
    return DatasetRoleArtifact.create(
        dataset_identity=dataset_identity,
        role=new_role,
        role_assignment_key=reassignment_key,
        permitted_operations=permitted_operations,
        prohibited_operations=prohibited_operations,
        owner_authorization_ref=owner_authorization_ref,
    )


def _datasets_temporally_overlap(
    left: DatasetIdentityArtifact,
    right: DatasetIdentityArtifact,
) -> bool:
    if left.source_identity != right.source_identity:
        return False
    if left.timeline_id != right.timeline_id:
        return False
    if left.axis is not right.axis:
        return False
    return bool(left.start_key <= right.end_key and right.start_key <= left.end_key)


def verify_dataset_independence_and_ancestry(
    candidate_identity: DatasetIdentityArtifact,
    *,
    known_identities: Sequence[DatasetIdentityArtifact],
    known_roles: Mapping[str, DatasetRoleArtifact],
    require_unexposed_final_eligibility: bool = False,
) -> bool:
    """Verify dataset ancestry, content-hash uniqueness, and temporal/exposure isolation (D2-7, Attacks 31-33)."""
    if not isinstance(candidate_identity, DatasetIdentityArtifact):
        raise SchemaViolation("candidate_identity must be a DatasetIdentityArtifact")
    id_map: dict[str, DatasetIdentityArtifact] = {
        d.dataset_id: d for d in known_identities
    }
    id_map[candidate_identity.dataset_id] = candidate_identity

    # 1. Check undeclared shared content hash (Attack 32)
    for other in known_identities:
        if other.dataset_id == candidate_identity.dataset_id:
            continue
        if other.content_hash == candidate_identity.content_hash:
            if (
                other.dataset_id not in candidate_identity.parent_dataset_ids
                and candidate_identity.dataset_id not in other.parent_dataset_ids
            ):
                raise SchemaViolation(
                    f"{S3_UNDECLARED_SHARED_CONTENT_ANCESTRY}: dataset "
                    f"{candidate_identity.dataset_id!r} shares content_hash with "
                    f"{other.dataset_id!r} without declared parent_dataset_ids"
                )

    # 2. Traverse ancestor chain (cycle-safe) to collect all ancestors
    ancestors: set[str] = set()
    queue: list[str] = list(candidate_identity.parent_dataset_ids)
    while len(queue) > 0:
        curr_id = queue.pop(0)
        if curr_id == candidate_identity.dataset_id:
            raise SchemaViolation(
                f"{S3_INVALID_DATASET_IDENTITY}: cycle in dataset parent ancestry"
            )
        if curr_id in ancestors:
            continue
        ancestors.add(curr_id)
        if curr_id in id_map:
            queue.extend(id_map[curr_id].parent_dataset_ids)

    # 3. Check temporal overlap with non-ancestor datasets on same source/timeline (Attack 33)
    for other in known_identities:
        if other.dataset_id == candidate_identity.dataset_id:
            continue
        if (
            other.dataset_id not in ancestors
            and candidate_identity.dataset_id not in other.parent_dataset_ids
        ):
            if _datasets_temporally_overlap(candidate_identity, other):
                raise SchemaViolation(
                    f"{S3_TEMPORAL_OVERLAP_NOT_INDEPENDENT}: dataset "
                    f"{candidate_identity.dataset_id!r} temporally overlaps "
                    f"{other.dataset_id!r} on timeline {candidate_identity.timeline_id!r}"
                )

    # 4. If checking fresh final eligibility, reject any ancestor that has been exposed (Attack 31)
    if require_unexposed_final_eligibility:
        for anc_id in ancestors:
            if anc_id in known_roles:
                anc_role = known_roles[anc_id]
                if anc_role.exposure_state != EXPOSURE_STATE_UNEXPOSED:
                    raise SchemaViolation(
                        f"{S3_EXPOSED_ANCESTRY_CONTAMINATION}: dataset "
                        f"{candidate_identity.dataset_id!r} derives from exposed "
                        f"ancestor {anc_id!r} ({anc_role.exposure_state})"
                    )

    return True


@dataclass(frozen=True)
class FoldPairSpec(ImmutableRecord):
    """One walk-forward development fold pair (DEVELOPMENT_FIT -> DEVELOPMENT_SELECTION)."""

    fold_index: int
    fit_dataset_id: str
    selection_dataset_id: str

    def __post_init__(self) -> None:
        if isinstance(self.fold_index, bool) or not isinstance(self.fold_index, int) or self.fold_index < 0:
            raise SchemaViolation(f"{S3_INVALID_FOLD_PROTOCOL}: fold_index must be >= 0")
        _require_non_empty_str(
            self.fit_dataset_id, "fit_dataset_id", S3_INVALID_FOLD_PROTOCOL
        )
        _require_non_empty_str(
            self.selection_dataset_id,
            "selection_dataset_id",
            S3_INVALID_FOLD_PROTOCOL,
        )
        if self.fit_dataset_id == self.selection_dataset_id:
            raise SchemaViolation(
                f"{S3_INVALID_FOLD_PROTOCOL}: fit_dataset_id and selection_dataset_id must be distinct"
            )


@dataclass(frozen=True)
class FoldProtocolArtifact(ImmutableRecord):
    """Walk-forward fold protocol contract with final-data firewall (D1-2, D2-18, I-WF-1..3)."""

    protocol_id: str
    timeline_id: str
    folds: Tuple[FoldPairSpec, ...]
    owner_authorization_ref: str
    protocol_hash: str

    def __post_init__(self) -> None:
        _require_non_empty_str(
            self.protocol_id, "protocol_id", S3_INVALID_FOLD_PROTOCOL
        )
        _require_non_empty_str(
            self.timeline_id, "timeline_id", S3_INVALID_FOLD_PROTOCOL
        )
        fold_tuple = tuple(self.folds)
        if len(fold_tuple) == 0:
            raise SchemaViolation(
                f"{S3_INVALID_FOLD_PROTOCOL}: folds must be non-empty"
            )
        for idx, f in enumerate(fold_tuple):
            if not isinstance(f, FoldPairSpec) or f.fold_index != idx:
                raise SchemaViolation(
                    f"{S3_INVALID_FOLD_PROTOCOL}: fold at index {idx} must be FoldPairSpec with fold_index={idx}"
                )
        object.__setattr__(self, "folds", fold_tuple)
        _require_non_empty_str(
            self.owner_authorization_ref,
            "owner_authorization_ref",
            S3_INVALID_FOLD_PROTOCOL,
        )

        folds_ser = {
            f"fold_{f.fold_index}": {
                "fit": f.fit_dataset_id,
                "sel": f.selection_dataset_id,
            }
            for f in fold_tuple
        }
        expected_hash = canonical_artifact_identity(
            FOLD_PROTOCOL_IDENTITY_SCHEMA,
            identity_payload={
                "protocol_id": self.protocol_id,
                "timeline_id": self.timeline_id,
                "folds": folds_ser,
                "owner_authorization_ref": self.owner_authorization_ref,
            },
        )
        if self.protocol_hash != expected_hash:
            raise SchemaViolation(
                f"{S3_INVALID_FOLD_PROTOCOL}: protocol_hash mismatch"
            )

    @classmethod
    def create(
        cls,
        *,
        protocol_id: str,
        timeline_id: str,
        folds: Sequence[FoldPairSpec],
        dataset_identities: Mapping[str, DatasetIdentityArtifact],
        dataset_roles: Mapping[str, DatasetRoleArtifact],
        owner_authorization_ref: str,
    ) -> "FoldProtocolArtifact":
        fold_tuple = tuple(folds)
        if len(fold_tuple) == 0:
            raise SchemaViolation(
                f"{S3_INVALID_FOLD_PROTOCOL}: folds must be non-empty"
            )

        # Collect all FINAL_EVALUATION_LOCKED datasets to enforce walk-forward firewall (Attack 47)
        final_datasets = [
            dataset_identities[ds_id]
            for ds_id, r in dataset_roles.items()
            if r.role == DATASET_ROLE_FINAL_EVALUATION_LOCKED and ds_id in dataset_identities
        ]

        prev_sel_start: Optional[InformationKey] = None
        for idx, f in enumerate(fold_tuple):
            if not isinstance(f, FoldPairSpec) or f.fold_index != idx:
                raise SchemaViolation(
                    f"{S3_INVALID_FOLD_PROTOCOL}: invalid FoldPairSpec at index {idx}"
                )
            if f.fit_dataset_id not in dataset_roles or f.selection_dataset_id not in dataset_roles:
                raise SchemaViolation(
                    f"{S3_INVALID_FOLD_PROTOCOL}: fold {idx} datasets must have assigned roles"
                )
            if f.fit_dataset_id not in dataset_identities or f.selection_dataset_id not in dataset_identities:
                raise SchemaViolation(
                    f"{S3_INVALID_FOLD_PROTOCOL}: fold {idx} datasets must have DatasetIdentityArtifact"
                )
            fit_role = dataset_roles[f.fit_dataset_id]
            sel_role = dataset_roles[f.selection_dataset_id]
            if fit_role.role == DATASET_ROLE_FINAL_EVALUATION_LOCKED or sel_role.role == DATASET_ROLE_FINAL_EVALUATION_LOCKED:
                raise SchemaViolation(
                    f"{S3_FINAL_DATA_LEAKED_INTO_WALK_FORWARD}: fold {idx} references FINAL_EVALUATION_LOCKED data"
                )
            if fit_role.role != DATASET_ROLE_DEVELOPMENT_FIT:
                raise SchemaViolation(
                    f"{S3_INVALID_FOLD_PROTOCOL}: fit_dataset_id must have DEVELOPMENT_FIT role"
                )
            if sel_role.role != DATASET_ROLE_DEVELOPMENT_SELECTION:
                raise SchemaViolation(
                    f"{S3_INVALID_FOLD_PROTOCOL}: selection_dataset_id must have DEVELOPMENT_SELECTION role"
                )
            fit_id = dataset_identities[f.fit_dataset_id]
            sel_id = dataset_identities[f.selection_dataset_id]
            if fit_id.timeline_id != timeline_id or sel_id.timeline_id != timeline_id:
                raise InformationKeyViolation(
                    f"{S3_INVALID_FOLD_PROTOCOL}: fold {idx} dataset timeline mismatch"
                )
            if not (fit_id.end_key < sel_id.start_key):
                raise PrematureAvailability(
                    f"{S3_INVALID_FOLD_PROTOCOL}: fold {idx} fit_dataset end_key must precede selection_dataset start_key"
                )
            if prev_sel_start is not None and not (prev_sel_start <= sel_id.start_key):
                raise PrematureAvailability(
                    f"{S3_INVALID_FOLD_PROTOCOL}: fold {idx} selection window cannot precede earlier fold selection window"
                )
            prev_sel_start = sel_id.start_key
            for final_ds in final_datasets:
                if _datasets_temporally_overlap(fit_id, final_ds) or _datasets_temporally_overlap(sel_id, final_ds):
                    raise SchemaViolation(
                        f"{S3_FINAL_DATA_LEAKED_INTO_WALK_FORWARD}: fold {idx} overlaps reserved final dataset {final_ds.dataset_id!r}"
                    )

        folds_ser = {
            f"fold_{f.fold_index}": {
                "fit": f.fit_dataset_id,
                "sel": f.selection_dataset_id,
            }
            for f in fold_tuple
        }
        prot_hash = canonical_artifact_identity(
            FOLD_PROTOCOL_IDENTITY_SCHEMA,
            identity_payload={
                "protocol_id": protocol_id,
                "timeline_id": timeline_id,
                "folds": folds_ser,
                "owner_authorization_ref": owner_authorization_ref,
            },
        )
        return cls(
            protocol_id=protocol_id,
            timeline_id=timeline_id,
            folds=fold_tuple,
            owner_authorization_ref=owner_authorization_ref,
            protocol_hash=prot_hash,
        )


@dataclass(frozen=True)
class HumanReviewRecord(ImmutableRecord):
    """Human/Reality audit record with automatic final-data contamination enforcement (D1-3, I-HR-1..2)."""

    review_id: str
    dataset_id: str
    dataset_role: str
    review_kind: str
    review_key: InformationKey
    reviewer: str
    artifacts_viewed: Tuple[str, ...]
    charts_viewed: Tuple[str, ...]
    observations: Tuple[str, ...]
    requested_changes: Tuple[str, ...]
    change_influence: str
    review_hash: str

    def __post_init__(self) -> None:
        _require_non_empty_str(self.review_id, "review_id", S3_INVALID_HUMAN_REVIEW)
        _require_non_empty_str(self.dataset_id, "dataset_id", S3_INVALID_HUMAN_REVIEW)
        if self.dataset_role not in LEGAL_DATASET_ROLES:
            raise SchemaViolation(
                f"{S3_INVALID_HUMAN_REVIEW}: invalid dataset_role {self.dataset_role!r}"
            )
        if self.review_kind not in LEGAL_REVIEW_KINDS:
            raise SchemaViolation(
                f"{S3_INVALID_HUMAN_REVIEW}: invalid review_kind {self.review_kind!r}"
            )
        if (
            self.dataset_role == DATASET_ROLE_FINAL_EVALUATION_LOCKED
            and self.review_kind != REVIEW_KIND_FINAL_AUDIT
        ):
            raise SchemaViolation(
                f"{S3_INVALID_HUMAN_REVIEW}: FINAL_EVALUATION_LOCKED requires FINAL_EVALUATION_REALITY_AUDIT"
            )
        _require_completed_key(self.review_key, "review_key", S3_INVALID_HUMAN_REVIEW)
        _require_non_empty_str(self.reviewer, "reviewer", S3_INVALID_HUMAN_REVIEW)

        art_v = _require_str_tuple(
            self.artifacts_viewed, "artifacts_viewed", S3_INVALID_HUMAN_REVIEW
        )
        cht_v = _require_str_tuple(
            self.charts_viewed, "charts_viewed", S3_INVALID_HUMAN_REVIEW
        )
        if len(art_v) == 0 and len(cht_v) == 0:
            raise SchemaViolation(
                f"{S3_INVALID_HUMAN_REVIEW}: review must list at least one viewed artifact or chart"
            )
        obs = _require_str_tuple(
            self.observations, "observations", S3_INVALID_HUMAN_REVIEW
        )
        req_chg = _require_str_tuple(
            self.requested_changes, "requested_changes", S3_INVALID_HUMAN_REVIEW
        )
        object.__setattr__(self, "artifacts_viewed", art_v)
        object.__setattr__(self, "charts_viewed", cht_v)
        object.__setattr__(self, "observations", obs)
        object.__setattr__(self, "requested_changes", req_chg)

        if self.change_influence not in LEGAL_CHANGE_INFLUENCES:
            raise SchemaViolation(
                f"{S3_INVALID_HUMAN_REVIEW}: invalid change_influence {self.change_influence!r}"
            )
        if len(req_chg) > 0 and self.change_influence != INFLUENCE_DESIGN_INFLUENCING:
            raise SchemaViolation(
                f"{S3_CONTRADICTORY_REVIEW_INFLUENCE}: non-empty requested_changes requires "
                "change_influence = DESIGN_INFLUENCING"
            )

        expected_hash = canonical_artifact_identity(
            HUMAN_REVIEW_IDENTITY_SCHEMA,
            identity_payload={
                "review_id": self.review_id,
                "dataset_id": self.dataset_id,
                "dataset_role": self.dataset_role,
                "review_kind": self.review_kind,
                "review_key": self.review_key,
                "reviewer": self.reviewer,
                "artifacts_viewed": _serialize_seq(art_v),
                "charts_viewed": _serialize_seq(cht_v),
                "observations": _serialize_seq(obs),
                "requested_changes": _serialize_seq(req_chg),
                "change_influence": self.change_influence,
            },
        )
        if self.review_hash != expected_hash:
            raise SchemaViolation(f"{S3_INVALID_HUMAN_REVIEW}: review_hash mismatch")

    @classmethod
    def create_and_apply(
        cls,
        *,
        review_id: str,
        role_artifact: DatasetRoleArtifact,
        review_kind: str,
        review_key: InformationKey,
        reviewer: str,
        artifacts_viewed: Sequence[str] = (),
        charts_viewed: Sequence[str] = (),
        observations: Sequence[str] = (),
        requested_changes: Sequence[str] = (),
        change_influence: str,
    ) -> Tuple["HumanReviewRecord", DatasetRoleArtifact]:
        """Create a HumanReviewRecord and update DatasetRoleArtifact exposure state (I-HR-1..2, Attack 12)."""
        if not isinstance(role_artifact, DatasetRoleArtifact):
            raise SchemaViolation("role_artifact must be a DatasetRoleArtifact")
        art_v = _require_str_tuple(
            artifacts_viewed, "artifacts_viewed", S3_INVALID_HUMAN_REVIEW
        )
        cht_v = _require_str_tuple(
            charts_viewed, "charts_viewed", S3_INVALID_HUMAN_REVIEW
        )
        obs = _require_str_tuple(
            observations, "observations", S3_INVALID_HUMAN_REVIEW
        )
        req_chg = _require_str_tuple(
            requested_changes, "requested_changes", S3_INVALID_HUMAN_REVIEW
        )
        rev_hash = canonical_artifact_identity(
            HUMAN_REVIEW_IDENTITY_SCHEMA,
            identity_payload={
                "review_id": review_id,
                "dataset_id": role_artifact.dataset_id,
                "dataset_role": role_artifact.role,
                "review_kind": review_kind,
                "review_key": review_key,
                "reviewer": reviewer,
                "artifacts_viewed": _serialize_seq(art_v),
                "charts_viewed": _serialize_seq(cht_v),
                "observations": _serialize_seq(obs),
                "requested_changes": _serialize_seq(req_chg),
                "change_influence": change_influence,
            },
        )
        review_rec = cls(
            review_id=review_id,
            dataset_id=role_artifact.dataset_id,
            dataset_role=role_artifact.role,
            review_kind=review_kind,
            review_key=review_key,
            reviewer=reviewer,
            artifacts_viewed=art_v,
            charts_viewed=cht_v,
            observations=obs,
            requested_changes=req_chg,
            change_influence=change_influence,
            review_hash=rev_hash,
        )
        is_design_influencing = (
            change_influence == INFLUENCE_DESIGN_INFLUENCING or len(req_chg) > 0
        )
        updated_role = record_dataset_exposure(
            role_artifact,
            event_id=f"review:{review_id}",
            exposure_key=review_key,
            exposure_kind=review_kind,
            actor_or_protocol_ref=reviewer,
            authorized_final_open=not is_design_influencing,
            design_influencing=is_design_influencing,
        )
        return review_rec, updated_role


@dataclass(frozen=True)
class RepresentationExperimentRecord(ImmutableRecord):
    """Preregistered experiment record in the S3 Experiment Registry (D1-16, I-ER-1..5)."""

    experiment_id: str
    preregistration_key: InformationKey
    representation_spec_hash: str
    policy_artifact_hashes: Tuple[str, ...]
    objective_artifact_hash: str
    dataset_identities_by_role: Any
    code_hash: str
    fit_protocol_hash: str
    selection_protocol_hash: Union[str, TypedState]
    status: str
    result_refs: Tuple[str, ...]
    failure_refs: Tuple[str, ...]
    supersedes_experiment_id: Union[str, TypedState]
    last_transition_key: InformationKey
    experiment_hash: str

    def __post_init__(self) -> None:
        _require_non_empty_str(
            self.experiment_id, "experiment_id", S3_INVALID_EXPERIMENT_RECORD
        )
        _require_completed_key(
            self.preregistration_key,
            "preregistration_key",
            S3_INVALID_EXPERIMENT_RECORD,
        )
        _require_completed_key(
            self.last_transition_key,
            "last_transition_key",
            S3_INVALID_EXPERIMENT_RECORD,
        )
        try:
            valid_time = self.preregistration_key <= self.last_transition_key
        except InformationKeyError as exc:
            raise IncomparableInformationKeys(str(exc)) from exc
        if not valid_time:
            raise PrematureAvailability(
                f"{S3_INVALID_EXPERIMENT_RECORD}: last_transition_key cannot precede preregistration_key"
            )
        _require_non_empty_str(
            self.representation_spec_hash,
            "representation_spec_hash",
            S3_INVALID_EXPERIMENT_RECORD,
        )
        pol_hashes = _require_str_tuple(
            self.policy_artifact_hashes,
            "policy_artifact_hashes",
            S3_INVALID_EXPERIMENT_RECORD,
        )
        if len(pol_hashes) == 0:
            raise SchemaViolation(
                f"{S3_INVALID_EXPERIMENT_RECORD}: policy_artifact_hashes must be non-empty"
            )
        object.__setattr__(self, "policy_artifact_hashes", pol_hashes)
        _require_non_empty_str(
            self.objective_artifact_hash,
            "objective_artifact_hash",
            S3_INVALID_EXPERIMENT_RECORD,
        )
        if not isinstance(self.dataset_identities_by_role, Mapping) or len(self.dataset_identities_by_role) == 0:
            raise SchemaViolation(
                f"{S3_INVALID_EXPERIMENT_RECORD}: dataset_identities_by_role must be a non-empty mapping"
            )
        role_map_clean: dict[str, str] = {}
        for r_key, ds_val in self.dataset_identities_by_role.items():
            if r_key not in LEGAL_DATASET_ROLES:
                raise SchemaViolation(
                    f"{S3_INVALID_EXPERIMENT_RECORD}: invalid role {r_key!r} in dataset_identities_by_role"
                )
            role_map_clean[r_key] = _require_non_empty_str(
                ds_val, f"dataset_identities_by_role[{r_key!r}]", S3_INVALID_EXPERIMENT_RECORD
            )
        frozen_role_map = freeze_payload(role_map_clean)
        object.__setattr__(self, "dataset_identities_by_role", frozen_role_map)

        _require_non_empty_str(
            self.code_hash, "code_hash", S3_INVALID_EXPERIMENT_RECORD
        )
        _require_non_empty_str(
            self.fit_protocol_hash,
            "fit_protocol_hash",
            S3_INVALID_EXPERIMENT_RECORD,
        )
        if self.selection_protocol_hash is not TypedState.NOT_CONFIGURED:
            _require_non_empty_str(
                self.selection_protocol_hash,
                "selection_protocol_hash",
                S3_INVALID_EXPERIMENT_RECORD,
            )
        if self.status not in LEGAL_EXPERIMENT_STATUSES:
            raise SchemaViolation(
                f"{S3_INVALID_EXPERIMENT_RECORD}: invalid status {self.status!r}"
            )
        res_refs = _require_str_tuple(
            self.result_refs, "result_refs", S3_INVALID_EXPERIMENT_RECORD
        )
        fail_refs = _require_str_tuple(
            self.failure_refs, "failure_refs", S3_INVALID_EXPERIMENT_RECORD
        )
        object.__setattr__(self, "result_refs", res_refs)
        object.__setattr__(self, "failure_refs", fail_refs)
        if self.status == EXPERIMENT_STATUS_FAILED and len(fail_refs) == 0:
            raise SchemaViolation(
                f"{S3_INVALID_EXPERIMENT_RECORD}: FAILED experiment requires non-empty failure_refs"
            )
        if self.status == EXPERIMENT_STATUS_COMPLETED and len(res_refs) == 0:
            raise SchemaViolation(
                f"{S3_INVALID_EXPERIMENT_RECORD}: COMPLETED experiment requires non-empty result_refs"
            )
        if self.supersedes_experiment_id is not TypedState.NOT_APPLICABLE:
            _require_non_empty_str(
                self.supersedes_experiment_id,
                "supersedes_experiment_id",
                S3_INVALID_EXPERIMENT_RECORD,
            )

        expected_hash = canonical_artifact_identity(
            EXPERIMENT_IDENTITY_SCHEMA,
            identity_payload={
                "experiment_id": self.experiment_id,
                "preregistration_key": self.preregistration_key,
                "representation_spec_hash": self.representation_spec_hash,
                "policy_artifact_hashes": _serialize_seq(pol_hashes),
                "objective_artifact_hash": self.objective_artifact_hash,
                "dataset_identities_by_role": role_map_clean,
                "code_hash": self.code_hash,
                "fit_protocol_hash": self.fit_protocol_hash,
                "selection_protocol_hash": self.selection_protocol_hash,
            },
            proof_payload={
                "status": self.status,
                "result_refs": _serialize_seq(res_refs),
                "failure_refs": _serialize_seq(fail_refs),
                "supersedes_experiment_id": self.supersedes_experiment_id,
            },
        )
        if self.experiment_hash != expected_hash:
            raise SchemaViolation(
                f"{S3_INVALID_EXPERIMENT_RECORD}: experiment_hash mismatch"
            )


class ExperimentRegistry:
    """Append-only registry of preregistered experiments and their lifecycle transitions (D1-16, I-ER-1..5).

    Failed trials and superseded experiments can NEVER be deleted or overwritten
    (Attacks 13 & 14). Changing any identity-defining field (objective_artifact_hash,
    representation_spec_hash, policy_artifact_hashes, dataset_identities_by_role)
    requires registering a new experiment_id.
    """

    __slots__ = ("__entries_by_id", "__history")

    def __init__(self) -> None:
        object.__setattr__(self, "_ExperimentRegistry__entries_by_id", {})
        object.__setattr__(self, "_ExperimentRegistry__history", [])

    def __setattr__(self, name: str, value: Any) -> None:
        raise ImmutabilityViolation("ExperimentRegistry attributes cannot be rebound")

    def __delattr__(self, name: str) -> None:
        raise ImmutabilityViolation("ExperimentRegistry attributes cannot be deleted")

    def preregister(
        self,
        *,
        experiment_id: str,
        preregistration_key: InformationKey,
        representation_spec_hash: str,
        policy_artifact_hashes: Sequence[str],
        objective_artifact_hash: str,
        dataset_identities_by_role: Mapping[str, str],
        code_hash: str,
        fit_protocol_hash: str,
        selection_protocol_hash: Union[str, TypedState] = TypedState.NOT_CONFIGURED,
        supersedes_experiment_id: Union[str, TypedState] = TypedState.NOT_APPLICABLE,
    ) -> RepresentationExperimentRecord:
        entries: dict[str, RepresentationExperimentRecord] = object.__getattribute__(
            self, "_ExperimentRegistry__entries_by_id"
        )
        history: list[RepresentationExperimentRecord] = object.__getattribute__(
            self, "_ExperimentRegistry__history"
        )
        if supersedes_experiment_id is not TypedState.NOT_APPLICABLE:
            if supersedes_experiment_id not in entries:
                raise SchemaViolation(
                    f"{S3_UNREGISTERED_EXPERIMENT}: supersedes_experiment_id "
                    f"{supersedes_experiment_id!r} does not exist in registry"
                )
        pol_tuple = _require_str_tuple(
            policy_artifact_hashes,
            "policy_artifact_hashes",
            S3_INVALID_EXPERIMENT_RECORD,
        )
        role_map_clean = {str(k): str(v) for k, v in dataset_identities_by_role.items()}
        exp_hash = canonical_artifact_identity(
            EXPERIMENT_IDENTITY_SCHEMA,
            identity_payload={
                "experiment_id": experiment_id,
                "preregistration_key": preregistration_key,
                "representation_spec_hash": representation_spec_hash,
                "policy_artifact_hashes": _serialize_seq(pol_tuple),
                "objective_artifact_hash": objective_artifact_hash,
                "dataset_identities_by_role": role_map_clean,
                "code_hash": code_hash,
                "fit_protocol_hash": fit_protocol_hash,
                "selection_protocol_hash": selection_protocol_hash,
            },
            proof_payload={
                "status": EXPERIMENT_STATUS_PREREGISTERED,
                "result_refs": {},
                "failure_refs": {},
                "supersedes_experiment_id": supersedes_experiment_id,
            },
        )
        rec = RepresentationExperimentRecord(
            experiment_id=experiment_id,
            preregistration_key=preregistration_key,
            representation_spec_hash=representation_spec_hash,
            policy_artifact_hashes=pol_tuple,
            objective_artifact_hash=objective_artifact_hash,
            dataset_identities_by_role=role_map_clean,
            code_hash=code_hash,
            fit_protocol_hash=fit_protocol_hash,
            selection_protocol_hash=selection_protocol_hash,
            status=EXPERIMENT_STATUS_PREREGISTERED,
            result_refs=(),
            failure_refs=(),
            supersedes_experiment_id=supersedes_experiment_id,
            last_transition_key=preregistration_key,
            experiment_hash=exp_hash,
        )
        if experiment_id in entries:
            existing = entries[experiment_id]
            if existing == rec:
                return existing
            raise SchemaViolation(
                f"{S3_EXPERIMENT_IDENTITY_COLLISION}: experiment_id {experiment_id!r} "
                "is already registered; parameter/objective changes require a new experiment_id (I-ER-3)"
            )
        entries[experiment_id] = rec
        history.append(rec)
        return rec

    def record_transition(
        self,
        *,
        experiment_id: str,
        new_status: str,
        transition_key: InformationKey,
        result_refs: Sequence[str] = (),
        failure_refs: Sequence[str] = (),
    ) -> RepresentationExperimentRecord:
        entries: dict[str, RepresentationExperimentRecord] = object.__getattribute__(
            self, "_ExperimentRegistry__entries_by_id"
        )
        history: list[RepresentationExperimentRecord] = object.__getattribute__(
            self, "_ExperimentRegistry__history"
        )
        if experiment_id not in entries:
            raise SchemaViolation(
                f"{S3_UNREGISTERED_EXPERIMENT}: cannot transition unregistered "
                f"experiment {experiment_id!r} (I-ER-1)"
            )
        current = entries[experiment_id]
        if new_status == EXPERIMENT_STATUS_PREREGISTERED:
            raise SchemaViolation(
                f"{S3_INVALID_EXPERIMENT_RECORD}: cannot transition back to PREREGISTERED"
            )
        if current.status == EXPERIMENT_STATUS_SUPERSEDED:
            raise SchemaViolation(
                f"{S3_EXPERIMENT_DELETION_FORBIDDEN}: SUPERSEDED experiment {experiment_id!r} "
                "is in a terminal state and cannot transition further"
            )
        if (
            current.status in (EXPERIMENT_STATUS_FAILED, EXPERIMENT_STATUS_COMPLETED)
            and new_status != EXPERIMENT_STATUS_SUPERSEDED
        ):
            raise SchemaViolation(
                f"{S3_EXPERIMENT_DELETION_FORBIDDEN}: {current.status} experiment {experiment_id!r} "
                "cannot be overwritten; only transition to SUPERSEDED is permitted (I-ER-2)"
            )
        try:
            valid_order = current.last_transition_key <= transition_key
        except InformationKeyError as exc:
            raise IncomparableInformationKeys(str(exc)) from exc
        if not valid_order:
            raise PrematureAvailability(
                f"{S3_INVALID_EXPERIMENT_RECORD}: transition_key precedes prior transition"
            )

        merged_results = current.result_refs + _require_str_tuple(
            result_refs, "result_refs", S3_INVALID_EXPERIMENT_RECORD
        )
        merged_failures = current.failure_refs + _require_str_tuple(
            failure_refs, "failure_refs", S3_INVALID_EXPERIMENT_RECORD
        )
        updated = RepresentationExperimentRecord(
            experiment_id=current.experiment_id,
            preregistration_key=current.preregistration_key,
            representation_spec_hash=current.representation_spec_hash,
            policy_artifact_hashes=current.policy_artifact_hashes,
            objective_artifact_hash=current.objective_artifact_hash,
            dataset_identities_by_role=current.dataset_identities_by_role,
            code_hash=current.code_hash,
            fit_protocol_hash=current.fit_protocol_hash,
            selection_protocol_hash=current.selection_protocol_hash,
            status=new_status,
            result_refs=merged_results,
            failure_refs=merged_failures,
            supersedes_experiment_id=current.supersedes_experiment_id,
            last_transition_key=transition_key,
            experiment_hash=current.experiment_hash,
        )
        entries[experiment_id] = updated
        history.append(updated)
        return updated

    def delete_experiment(self, experiment_id: str) -> None:
        """Deleting any experiment or failed trial is strictly forbidden (I-ER-2/4, Attack 13)."""
        raise ImmutabilityViolation(
            f"{S3_EXPERIMENT_DELETION_FORBIDDEN}: ExperimentRegistry is append-only; "
            f"cannot delete experiment {experiment_id!r}"
        )

    def get(self, experiment_id: str) -> RepresentationExperimentRecord:
        entries: dict[str, RepresentationExperimentRecord] = object.__getattribute__(
            self, "_ExperimentRegistry__entries_by_id"
        )
        if experiment_id not in entries:
            raise SchemaViolation(
                f"{S3_UNREGISTERED_EXPERIMENT}: unknown experiment {experiment_id!r}"
            )
        return entries[experiment_id]

    def history(self) -> Tuple[RepresentationExperimentRecord, ...]:
        history: list[RepresentationExperimentRecord] = object.__getattribute__(
            self, "_ExperimentRegistry__history"
        )
        return tuple(history)


@dataclass(frozen=True)
class PolicyArtifact(ImmutableRecord):
    """MUF PolicyArtifact infrastructure contract (D1-4, D2-1, I-PAUTH-1..4; no fit in S3)."""

    policy_id: str
    authority_kind: str
    target_engine_identity: SchemaIdentity
    detector_policy_witness_ref: str
    scope_timeline_id: str
    scope_axis: InformationAxis
    scope_representation_id: str
    calibration_provenance_kind: str
    fit_dataset_id: Union[str, TypedState]
    objective_artifact_hash: Union[str, TypedState]
    experiment_id: Union[str, TypedState]
    fit_dataset_role_hash: Union[str, TypedState]
    reproduction_recipe_hash: str
    effective_from_key: InformationKey
    owner_authorization_ref: str
    policy_hash: str

    def __post_init__(self) -> None:
        _require_non_empty_str(self.policy_id, "policy_id", S3_INVALID_POLICY_ARTIFACT)
        if self.authority_kind not in LEGAL_POLICY_AUTHORITY_KINDS:
            raise SchemaViolation(
                f"{S3_INVALID_POLICY_ARTIFACT}: invalid authority_kind {self.authority_kind!r}"
            )
        if not isinstance(self.target_engine_identity, SchemaIdentity):
            raise SchemaViolation(
                f"{S3_INVALID_POLICY_ARTIFACT}: target_engine_identity must be a SchemaIdentity"
            )
        _require_non_empty_str(
            self.detector_policy_witness_ref,
            "detector_policy_witness_ref",
            S3_INVALID_POLICY_ARTIFACT,
        )
        _require_non_empty_str(
            self.scope_timeline_id,
            "scope_timeline_id",
            S3_INVALID_POLICY_ARTIFACT,
        )
        if not isinstance(self.scope_axis, InformationAxis):
            raise SchemaViolation(
                f"{S3_INVALID_POLICY_ARTIFACT}: scope_axis must be an InformationAxis"
            )
        _require_non_empty_str(
            self.scope_representation_id,
            "scope_representation_id",
            S3_INVALID_POLICY_ARTIFACT,
        )
        if self.calibration_provenance_kind not in LEGAL_CALIBRATION_PROVENANCE_KINDS:
            raise SchemaViolation(
                f"{S3_INVALID_POLICY_ARTIFACT}: invalid calibration_provenance_kind "
                f"{self.calibration_provenance_kind!r}"
            )
        if self.calibration_provenance_kind == PROVENANCE_DEVELOPMENT_FIT:
            _require_non_empty_str(
                self.fit_dataset_id,
                "fit_dataset_id",
                S3_INVALID_POLICY_ARTIFACT,
            )
            _require_non_empty_str(
                self.objective_artifact_hash,
                "objective_artifact_hash",
                S3_INVALID_POLICY_ARTIFACT,
            )
            _require_non_empty_str(
                self.experiment_id,
                "experiment_id",
                S3_INVALID_POLICY_ARTIFACT,
            )
            if self.fit_dataset_role_hash is not TypedState.NOT_APPLICABLE:
                _require_non_empty_str(
                    self.fit_dataset_role_hash,
                    "fit_dataset_role_hash",
                    S3_INVALID_POLICY_ARTIFACT,
                )
        else:
            if (
                self.fit_dataset_id is not TypedState.NOT_APPLICABLE
                or self.objective_artifact_hash is not TypedState.NOT_APPLICABLE
                or self.experiment_id is not TypedState.NOT_APPLICABLE
                or self.fit_dataset_role_hash is not TypedState.NOT_APPLICABLE
            ):
                raise SchemaViolation(
                    f"{S3_INVALID_POLICY_ARTIFACT}: {self.calibration_provenance_kind} "
                    "requires fit_dataset_id, objective_artifact_hash, experiment_id, and "
                    "fit_dataset_role_hash to be TypedState.NOT_APPLICABLE"
                )
        _require_non_empty_str(
            self.reproduction_recipe_hash,
            "reproduction_recipe_hash",
            S3_INVALID_POLICY_ARTIFACT,
        )
        _require_completed_key(
            self.effective_from_key,
            "effective_from_key",
            S3_INVALID_POLICY_ARTIFACT,
        )
        if self.effective_from_key.timeline_id != self.scope_timeline_id:
            raise InformationKeyViolation(
                f"{S3_POLICY_SCOPE_MISMATCH}: effective_from_key timeline mismatch"
            )
        if key_axis(self.effective_from_key) is not self.scope_axis:
            raise IncomparableInformationKeys(
                f"{S3_POLICY_SCOPE_MISMATCH}: effective_from_key axis mismatch"
            )
        _require_non_empty_str(
            self.owner_authorization_ref,
            "owner_authorization_ref",
            S3_INVALID_POLICY_ARTIFACT,
        )

        expected_hash = canonical_artifact_identity(
            POLICY_ARTIFACT_IDENTITY_SCHEMA,
            identity_payload={
                "policy_id": self.policy_id,
                "authority_kind": self.authority_kind,
                "target_engine_identity": self.target_engine_identity,
                "detector_policy_witness_ref": self.detector_policy_witness_ref,
                "scope_timeline_id": self.scope_timeline_id,
                "scope_axis": self.scope_axis.value,
                "scope_representation_id": self.scope_representation_id,
                "calibration_provenance_kind": self.calibration_provenance_kind,
                "fit_dataset_id": self.fit_dataset_id,
                "objective_artifact_hash": self.objective_artifact_hash,
                "experiment_id": self.experiment_id,
                "fit_dataset_role_hash": self.fit_dataset_role_hash,
                "reproduction_recipe_hash": self.reproduction_recipe_hash,
                "effective_from_key": self.effective_from_key,
                "owner_authorization_ref": self.owner_authorization_ref,
            },
        )
        if self.policy_hash != expected_hash:
            raise SchemaViolation(
                f"{S3_INVALID_POLICY_ARTIFACT}: policy_hash mismatch"
            )

    @classmethod
    def create(
        cls,
        *,
        policy_id: str,
        authority_kind: str = POLICY_AUTHORITY_KIND_MUF,
        target_engine_identity: SchemaIdentity = S2_ADAPTER_ENGINE_IDENTITY,
        detector_policy_witness_ref: str,
        scope_timeline_id: str,
        scope_axis: InformationAxis,
        scope_representation_id: str,
        calibration_provenance_kind: str,
        fit_dataset_id: Union[str, TypedState] = TypedState.NOT_APPLICABLE,
        objective_artifact_hash: Union[str, TypedState] = TypedState.NOT_APPLICABLE,
        experiment_id: Union[str, TypedState] = TypedState.NOT_APPLICABLE,
        fit_dataset_role_hash: Union[str, TypedState] = TypedState.NOT_APPLICABLE,
        reproduction_recipe_hash: str,
        effective_from_key: InformationKey,
        owner_authorization_ref: str,
    ) -> "PolicyArtifact":
        p_hash = canonical_artifact_identity(
            POLICY_ARTIFACT_IDENTITY_SCHEMA,
            identity_payload={
                "policy_id": policy_id,
                "authority_kind": authority_kind,
                "target_engine_identity": target_engine_identity,
                "detector_policy_witness_ref": detector_policy_witness_ref,
                "scope_timeline_id": scope_timeline_id,
                "scope_axis": scope_axis.value,
                "scope_representation_id": scope_representation_id,
                "calibration_provenance_kind": calibration_provenance_kind,
                "fit_dataset_id": fit_dataset_id,
                "objective_artifact_hash": objective_artifact_hash,
                "experiment_id": experiment_id,
                "fit_dataset_role_hash": fit_dataset_role_hash,
                "reproduction_recipe_hash": reproduction_recipe_hash,
                "effective_from_key": effective_from_key,
                "owner_authorization_ref": owner_authorization_ref,
            },
        )
        return cls(
            policy_id=policy_id,
            authority_kind=authority_kind,
            target_engine_identity=target_engine_identity,
            detector_policy_witness_ref=detector_policy_witness_ref,
            scope_timeline_id=scope_timeline_id,
            scope_axis=scope_axis,
            scope_representation_id=scope_representation_id,
            calibration_provenance_kind=calibration_provenance_kind,
            fit_dataset_id=fit_dataset_id,
            objective_artifact_hash=objective_artifact_hash,
            experiment_id=experiment_id,
            fit_dataset_role_hash=fit_dataset_role_hash,
            reproduction_recipe_hash=reproduction_recipe_hash,
            effective_from_key=effective_from_key,
            owner_authorization_ref=owner_authorization_ref,
            policy_hash=p_hash,
        )


def verify_policy_artifact_reproduction(
    policy_artifact: PolicyArtifact,
    *,
    recomputed_detector_policy_witness_ref: str,
    recomputed_recipe_hash: str,
) -> bool:
    """Verify deterministic reproduction of a PolicyArtifact's bound witness spec & recipe."""
    if not isinstance(policy_artifact, PolicyArtifact):
        raise SchemaViolation(
            f"{S3_INVALID_POLICY_ARTIFACT}: expected PolicyArtifact"
        )
    if policy_artifact.detector_policy_witness_ref != recomputed_detector_policy_witness_ref:
        raise SchemaViolation(
            f"{S3_POLICY_REPRODUCTION_MISMATCH}: detector_policy_witness_ref mismatch"
        )
    if policy_artifact.reproduction_recipe_hash != recomputed_recipe_hash:
        raise SchemaViolation(
            f"{S3_POLICY_REPRODUCTION_MISMATCH}: reproduction_recipe_hash mismatch"
        )
    return True


@dataclass(frozen=True)
class AuthoritativeTurningPointRecord(ImmutableRecord):
    """Authoritative MUF turning point promoted from an S2 SwingEventWitnessRecord under a PolicyArtifact (D1-4, D2-1)."""

    turning_point_id: str
    timeline_id: str
    extrema_kind: str
    origin_position: int
    confirmation_position: int
    origin_key: InformationKey
    availability_key: InformationKey
    swing_price: MetricResult
    swing_confirmation_price: MetricResult
    authority_kind: str
    authority_policy_hash: str
    witness_record_ref: str
    published_record: PublishedRecord

    def __post_init__(self) -> None:
        _require_non_empty_str(
            self.turning_point_id,
            "turning_point_id",
            S3_INVALID_TURNING_POINT_PROMOTION,
        )
        _require_non_empty_str(
            self.timeline_id, "timeline_id", S3_INVALID_TURNING_POINT_PROMOTION
        )
        if self.extrema_kind not in ("HIGH", "LOW"):
            raise SchemaViolation(
                f"{S3_INVALID_TURNING_POINT_PROMOTION}: invalid extrema_kind {self.extrema_kind!r}"
            )
        if self.origin_position < 0 or self.origin_position >= self.confirmation_position:
            raise SchemaViolation(
                f"{S3_INVALID_TURNING_POINT_PROMOTION}: require 0 <= origin_position < confirmation_position"
            )
        require_visible_at(fact_key=self.origin_key, at_key=self.availability_key)
        if not (self.origin_key < self.availability_key):
            raise SchemaViolation(
                f"{S3_INVALID_TURNING_POINT_PROMOTION}: origin_key must be strictly < availability_key"
            )
        if not isinstance(self.swing_price, MetricResult) or self.swing_price.semantics != EXACT:
            raise SchemaViolation(
                f"{S3_INVALID_TURNING_POINT_PROMOTION}: swing_price must be EXACT MetricResult"
            )
        if (
            not isinstance(self.swing_confirmation_price, MetricResult)
            or self.swing_confirmation_price.semantics != EXACT
        ):
            raise SchemaViolation(
                f"{S3_INVALID_TURNING_POINT_PROMOTION}: swing_confirmation_price must be EXACT MetricResult"
            )
        if self.authority_kind not in LEGAL_POLICY_AUTHORITY_KINDS:
            raise SchemaViolation(
                f"{S3_INVALID_TURNING_POINT_PROMOTION}: invalid authority_kind {self.authority_kind!r}"
            )
        _require_non_empty_str(
            self.authority_policy_hash,
            "authority_policy_hash",
            S3_INVALID_TURNING_POINT_PROMOTION,
        )
        _require_non_empty_str(
            self.witness_record_ref,
            "witness_record_ref",
            S3_INVALID_TURNING_POINT_PROMOTION,
        )
        if not isinstance(self.published_record, PublishedRecord):
            raise SchemaViolation("published_record must be a PublishedRecord")
        if self.published_record.record_type != TURNING_POINT_RECORD_TYPE:
            raise SchemaViolation(
                f"published_record.record_type must be {TURNING_POINT_RECORD_TYPE!r}"
            )
        if self.published_record.availability_key != self.availability_key:
            raise SchemaViolation(
                "published_record.availability_key must equal availability_key"
            )

        expected_id = canonical_artifact_identity(
            AUTHORITATIVE_TP_IDENTITY_SCHEMA,
            identity_payload={
                "timeline_id": self.timeline_id,
                "origin_key": "|".join(key_serialization(self.origin_key)),
                "availability_key": "|".join(key_serialization(self.availability_key)),
                "extrema_kind": self.extrema_kind,
                "authority_policy_hash": self.authority_policy_hash,
                "witness_record_ref": self.witness_record_ref,
            },
        )
        if self.turning_point_id != expected_id or self.published_record.record_identity != expected_id:
            raise SchemaViolation(
                f"{S3_INVALID_TURNING_POINT_PROMOTION}: turning_point_id mismatch"
            )
        rec_c = self.published_record.content
        if (
            rec_c["timeline_id"] != self.timeline_id
            or rec_c["extrema_kind"] != self.extrema_kind
            or rec_c["origin_position"] != self.origin_position
            or rec_c["confirmation_position"] != self.confirmation_position
            or rec_c["origin_key"] != self.origin_key
            or rec_c["availability_key"] != self.availability_key
            or rec_c["swing_price"] != freeze_payload(metric_payload(self.swing_price))
            or rec_c["swing_confirmation_price"]
            != freeze_payload(metric_payload(self.swing_confirmation_price))
            or rec_c["authority_kind"] != self.authority_kind
            or rec_c["authority_policy_hash"] != self.authority_policy_hash
            or rec_c["witness_record_ref"] != self.witness_record_ref
        ):
            raise SchemaViolation(
                "published_record.content mismatch with AuthoritativeTurningPointRecord"
            )

    def as_record(self) -> PublishedRecord:
        return self.published_record

    def to_turning_point_reference(self) -> AuthoritativeTurningPointReference:
        return AuthoritativeTurningPointReference(
            turning_point_identity=self.turning_point_id,
            record_type=TURNING_POINT_RECORD_TYPE,
            schema_identity=S3_SCHEMA_IDENTITY,
            timeline_id=self.timeline_id,
            availability_key=self.availability_key,
        )


def promote_swing_witness_with_policy_artifact(
    witness_record: SwingEventWitnessRecord,
    *,
    policy_artifact: PolicyArtifact,
) -> AuthoritativeTurningPointRecord:
    """Promote an S2 SwingEventWitnessRecord to an AuthoritativeTurningPointRecord under a PolicyArtifact (D1-4, I-PAUTH-1..4).

    Creates a new immutable ``AuthoritativeTurningPointRecord`` without mutating
    the underlying ``SwingEventWitnessRecord``. Fails closed with
    ``PolicyScopeMismatch`` if timeline, axis, or ``detector_policy_witness_ref``
    do not match, or ``PrematureAvailability`` if the policy's ``effective_from_key``
    is later than the witness's ``availability_key``.
    """
    if not isinstance(witness_record, SwingEventWitnessRecord):
        raise SchemaViolation(
            f"{S3_INVALID_TURNING_POINT_PROMOTION}: witness_record must be a SwingEventWitnessRecord"
        )
    if not isinstance(policy_artifact, PolicyArtifact):
        raise SchemaViolation(
            f"{S3_INVALID_POLICY_ARTIFACT}: policy_artifact must be a PolicyArtifact"
        )
    if witness_record.timeline_id != policy_artifact.scope_timeline_id:
        raise PolicyScopeMismatch(
            f"{S3_POLICY_SCOPE_MISMATCH}: witness timeline {witness_record.timeline_id!r} "
            f"!= policy scope_timeline_id {policy_artifact.scope_timeline_id!r}"
        )
    if key_axis(witness_record.availability_key) is not policy_artifact.scope_axis:
        raise PolicyScopeMismatch(
            f"{S3_POLICY_SCOPE_MISMATCH}: witness axis != policy scope_axis"
        )
    if witness_record.policy_witness_ref != policy_artifact.detector_policy_witness_ref:
        raise PolicyScopeMismatch(
            f"{S3_POLICY_SCOPE_MISMATCH}: witness policy_witness_ref "
            f"{witness_record.policy_witness_ref!r} != policy detector_policy_witness_ref "
            f"{policy_artifact.detector_policy_witness_ref!r}"
        )
    try:
        is_effective = policy_artifact.effective_from_key <= witness_record.availability_key
    except InformationKeyError as exc:
        raise IncomparableInformationKeys(str(exc)) from exc
    if not is_effective:
        raise PrematureAvailability(
            f"{S3_POLICY_SCOPE_MISMATCH}: policy effective_from_key is after witness availability_key"
        )
    require_visible_at(
        fact_key=policy_artifact.effective_from_key,
        at_key=witness_record.availability_key,
    )

    tp_id = canonical_artifact_identity(
        AUTHORITATIVE_TP_IDENTITY_SCHEMA,
        identity_payload={
            "timeline_id": witness_record.timeline_id,
            "origin_key": "|".join(key_serialization(witness_record.origin_key)),
            "availability_key": "|".join(
                key_serialization(witness_record.availability_key)
            ),
            "extrema_kind": witness_record.extrema_kind,
            "authority_policy_hash": policy_artifact.policy_hash,
            "witness_record_ref": witness_record.record_identity,
        },
    )
    content = {
        "timeline_id": witness_record.timeline_id,
        "extrema_kind": witness_record.extrema_kind,
        "origin_position": witness_record.origin_position,
        "confirmation_position": witness_record.confirmation_position,
        "origin_key": witness_record.origin_key,
        "availability_key": witness_record.availability_key,
        "swing_price": metric_payload(witness_record.swing_price),
        "swing_confirmation_price": metric_payload(
            witness_record.swing_confirmation_price
        ),
        "authority_kind": policy_artifact.authority_kind,
        "authority_policy_hash": policy_artifact.policy_hash,
        "witness_record_ref": witness_record.record_identity,
    }
    pub_rec = PublishedRecord(
        record_identity=tp_id,
        record_type=TURNING_POINT_RECORD_TYPE,
        schema_identity=S3_SCHEMA_IDENTITY,
        timeline_id=witness_record.timeline_id,
        availability_key=witness_record.availability_key,
        content=content,
    )
    return AuthoritativeTurningPointRecord(
        turning_point_id=tp_id,
        timeline_id=witness_record.timeline_id,
        extrema_kind=witness_record.extrema_kind,
        origin_position=witness_record.origin_position,
        confirmation_position=witness_record.confirmation_position,
        origin_key=witness_record.origin_key,
        availability_key=witness_record.availability_key,
        swing_price=witness_record.swing_price,
        swing_confirmation_price=witness_record.swing_confirmation_price,
        authority_kind=policy_artifact.authority_kind,
        authority_policy_hash=policy_artifact.policy_hash,
        witness_record_ref=witness_record.record_identity,
        published_record=pub_rec,
    )


def query_promoted_turning_points_as_of(
    turning_points: Sequence[AuthoritativeTurningPointRecord],
    *,
    timeline_id: str,
    axis: InformationAxis,
    at_key: InformationKey,
) -> Tuple[AuthoritativeTurningPointRecord, ...]:
    """Return authoritative turning points visible at ``at_key`` (``availability_key <= at_key``).

    Strictly enforces ``Origin != Availability`` (turning points whose
    ``origin_key <= at_key < availability_key`` are excluded) and rejects any
    unpromoted witness record in ``turning_points`` (I-PAUTH-1).
    """
    if not isinstance(at_key, InformationKey):
        raise InformationKeyViolation("at_key must be an InformationKey")
    if at_key.timeline_id != timeline_id:
        raise InformationKeyViolation("at_key timeline mismatch")
    if at_key.information_phase == InformationPhase.BAR_PRE_CLOSE:
        raise IllegalCausalReference(
            "BAR_PRE_CLOSE query cannot access completed-row turning points"
        )
    if key_axis(at_key) is not axis:
        raise IncomparableInformationKeys("at_key axis mismatch")

    visible: list[AuthoritativeTurningPointRecord] = []
    for tp in turning_points:
        if not isinstance(tp, AuthoritativeTurningPointRecord):
            raise SchemaViolation(
                f"{S3_INVALID_TURNING_POINT_PROMOTION}: factual turning point query "
                f"rejects non-authoritative record {type(tp).__name__} (I-PAUTH-1)"
            )
        if tp.timeline_id != timeline_id:
            raise InformationKeyViolation("turning point timeline mismatch")
        if key_axis(tp.availability_key) is not axis:
            raise IncomparableInformationKeys("turning point axis mismatch")
        try:
            is_vis = tp.availability_key <= at_key
        except InformationKeyError as exc:
            raise IncomparableInformationKeys(str(exc)) from exc
        if is_vis:
            require_visible_at(fact_key=tp.availability_key, at_key=at_key)
            visible.append(tp)
    return tuple(visible)


@dataclass(frozen=True)
class G0CalibrationGateCertificate(ImmutableRecord):
    """Certificate emitted by Gate G0 when all S3 prerequisites for S4 calibration are satisfied."""

    objective_artifact_hash: str
    fit_dataset_id: str
    fit_dataset_identity_hash: str
    fit_dataset_role_hash: str
    experiment_id: str
    experiment_hash: str
    owner_fit_authorization_ref: str
    gate_passed: bool

    def __post_init__(self) -> None:
        if self.gate_passed is not True:
            raise SelectionBlockedError("G0CalibrationGateCertificate requires gate_passed=True")
        _require_non_empty_str(
            self.objective_artifact_hash,
            "objective_artifact_hash",
            G0_BLOCKED_OBJECTIVE_UNDEFINED,
        )
        _require_non_empty_str(
            self.fit_dataset_id, "fit_dataset_id", G0_BLOCKED_INVALID_DATASET_ROLE
        )
        _require_non_empty_str(
            self.fit_dataset_identity_hash,
            "fit_dataset_identity_hash",
            G0_BLOCKED_INVALID_DATASET_ROLE,
        )
        _require_non_empty_str(
            self.fit_dataset_role_hash,
            "fit_dataset_role_hash",
            G0_BLOCKED_INVALID_DATASET_ROLE,
        )
        _require_non_empty_str(
            self.experiment_id, "experiment_id", G0_BLOCKED_UNREGISTERED_EXPERIMENT
        )
        _require_non_empty_str(
            self.experiment_hash, "experiment_hash", G0_BLOCKED_UNREGISTERED_EXPERIMENT
        )
        _require_non_empty_str(
            self.owner_fit_authorization_ref,
            "owner_fit_authorization_ref",
            G0_BLOCKED_MISSING_OWNER_AUTHORIZATION,
        )


def evaluate_g0_calibration_gate(
    *,
    objective_artifact: Any = QUALIFICATION_OBJECTIVE_DEFAULT,
    fit_dataset_identity: Any = TypedState.NOT_CONFIGURED,
    fit_dataset_role: Any = TypedState.NOT_CONFIGURED,
    known_dataset_identities: Sequence[DatasetIdentityArtifact] = (),
    known_dataset_roles: Optional[Mapping[str, DatasetRoleArtifact]] = None,
    experiment_registry: Optional[ExperimentRegistry] = None,
    experiment_id: Union[str, TypedState] = TypedState.NOT_CONFIGURED,
    owner_fit_authorization_ref: Union[str, TypedState] = TypedState.NOT_CONFIGURED,
) -> G0CalibrationGateCertificate:
    """Evaluate Authority Gate G0 before S4 development policy fit (D1-21, D2-22).

    Raises ``SelectionBlockedError`` if any prerequisite is missing, undefined,
    contaminated, or unauthorized.
    """
    if not isinstance(objective_artifact, ObjectiveArtifact):
        raise SelectionBlockedError(
            f"{G0_BLOCKED_OBJECTIVE_UNDEFINED}: valid ObjectiveArtifact required before calibration"
        )
    if DATASET_ROLE_DEVELOPMENT_FIT not in objective_artifact.dataset_role_permissions:
        raise SelectionBlockedError(
            f"{G0_BLOCKED_OBJECTIVE_UNDEFINED}: ObjectiveArtifact does not permit DEVELOPMENT_FIT"
        )
    if not isinstance(fit_dataset_identity, DatasetIdentityArtifact) or not isinstance(
        fit_dataset_role, DatasetRoleArtifact
    ):
        raise SelectionBlockedError(
            f"{G0_BLOCKED_INVALID_DATASET_ROLE}: fit_dataset_identity and fit_dataset_role required"
        )
    if (
        fit_dataset_role.dataset_id != fit_dataset_identity.dataset_id
        or fit_dataset_role.dataset_identity_hash != fit_dataset_identity.dataset_identity_hash
    ):
        raise SelectionBlockedError(
            f"{G0_BLOCKED_INVALID_DATASET_ROLE}: fit_dataset_role does not match fit_dataset_identity"
        )
    if fit_dataset_role.role != DATASET_ROLE_DEVELOPMENT_FIT:
        raise SelectionBlockedError(
            f"{G0_BLOCKED_INVALID_DATASET_ROLE}: calibration requires DEVELOPMENT_FIT role, "
            f"got {fit_dataset_role.role!r}"
        )
    if fit_dataset_role.exposure_state not in (
        EXPOSURE_STATE_UNEXPOSED,
        EXPOSURE_STATE_EXPOSED_DEVELOPMENT,
    ):
        raise SelectionBlockedError(
            f"{G0_BLOCKED_INVALID_DATASET_ROLE}: illegal fit dataset exposure_state "
            f"{fit_dataset_role.exposure_state!r}"
        )

    roles_map: dict[str, DatasetRoleArtifact] = (
        dict(known_dataset_roles) if known_dataset_roles is not None else {}
    )
    roles_map[fit_dataset_role.dataset_id] = fit_dataset_role

    try:
        verify_dataset_independence_and_ancestry(
            fit_dataset_identity,
            known_identities=known_dataset_identities,
            known_roles=roles_map,
            require_unexposed_final_eligibility=False,
        )
    except SchemaViolation as exc:
        raise SelectionBlockedError(
            f"{G0_BLOCKED_FINAL_DATA_LEAKAGE}: {exc}"
        ) from exc

    # Verify fit dataset does not derive from or overlap any FINAL_EVALUATION_LOCKED dataset (Attack 47)
    id_map = {d.dataset_id: d for d in known_dataset_identities}
    id_map[fit_dataset_identity.dataset_id] = fit_dataset_identity
    ancestors: set[str] = set()
    queue = list(fit_dataset_identity.parent_dataset_ids)
    while len(queue) > 0:
        curr = queue.pop(0)
        if curr not in ancestors:
            ancestors.add(curr)
            if curr in id_map:
                queue.extend(id_map[curr].parent_dataset_ids)

    for ds_id, r_art in roles_map.items():
        if r_art.role == DATASET_ROLE_FINAL_EVALUATION_LOCKED:
            if ds_id in ancestors:
                raise SelectionBlockedError(
                    f"{G0_BLOCKED_FINAL_DATA_LEAKAGE}: DEVELOPMENT_FIT dataset "
                    f"{fit_dataset_identity.dataset_id!r} derives from FINAL_EVALUATION_LOCKED "
                    f"dataset {ds_id!r}"
                )
            if ds_id in id_map and _datasets_temporally_overlap(fit_dataset_identity, id_map[ds_id]):
                raise SelectionBlockedError(
                    f"{G0_BLOCKED_FINAL_DATA_LEAKAGE}: DEVELOPMENT_FIT dataset "
                    f"{fit_dataset_identity.dataset_id!r} overlaps FINAL_EVALUATION_LOCKED "
                    f"dataset {ds_id!r}"
                )

    if not isinstance(experiment_registry, ExperimentRegistry) or not isinstance(
        experiment_id, str
    ) or not experiment_id.strip():
        raise SelectionBlockedError(
            f"{G0_BLOCKED_UNREGISTERED_EXPERIMENT}: preregistered experiment required in ExperimentRegistry"
        )
    try:
        exp_rec = experiment_registry.get(experiment_id)
    except SchemaViolation as exc:
        raise SelectionBlockedError(
            f"{G0_BLOCKED_UNREGISTERED_EXPERIMENT}: {exc}"
        ) from exc

    if exp_rec.status not in (
        EXPERIMENT_STATUS_PREREGISTERED,
        EXPERIMENT_STATUS_RUNNING,
    ):
        raise SelectionBlockedError(
            f"{G0_BLOCKED_UNREGISTERED_EXPERIMENT}: experiment {experiment_id!r} has status "
            f"{exp_rec.status!r}; calibration requires PREREGISTERED or RUNNING experiment"
        )
    if exp_rec.objective_artifact_hash != objective_artifact.objective_hash:
        raise SelectionBlockedError(
            f"{G0_BLOCKED_UNREGISTERED_EXPERIMENT}: experiment objective_artifact_hash mismatch"
        )
    if (
        DATASET_ROLE_DEVELOPMENT_FIT not in exp_rec.dataset_identities_by_role
        or exp_rec.dataset_identities_by_role[DATASET_ROLE_DEVELOPMENT_FIT]
        != fit_dataset_identity.dataset_id
    ):
        raise SelectionBlockedError(
            f"{G0_BLOCKED_UNREGISTERED_EXPERIMENT}: experiment DEVELOPMENT_FIT dataset mismatch"
        )

    if not isinstance(owner_fit_authorization_ref, str) or not owner_fit_authorization_ref.strip():
        raise SelectionBlockedError(
            f"{G0_BLOCKED_MISSING_OWNER_AUTHORIZATION}: owner_fit_authorization_ref required"
        )

    return G0CalibrationGateCertificate(
        objective_artifact_hash=objective_artifact.objective_hash,
        fit_dataset_id=fit_dataset_identity.dataset_id,
        fit_dataset_identity_hash=fit_dataset_identity.dataset_identity_hash,
        fit_dataset_role_hash=fit_dataset_role.role_artifact_hash,
        experiment_id=exp_rec.experiment_id,
        experiment_hash=exp_rec.experiment_hash,
        owner_fit_authorization_ref=owner_fit_authorization_ref,
        gate_passed=True,
    )


__all__ = [
    "AUTHORITATIVE_TP_IDENTITY_SCHEMA",
    "AuthoritativeTurningPointRecord",
    "DATASET_IDENTITY_SCHEMA",
    "DATASET_ROLE_DEVELOPMENT_FIT",
    "DATASET_ROLE_DEVELOPMENT_SELECTION",
    "DATASET_ROLE_FINAL_EVALUATION_LOCKED",
    "DATASET_ROLE_IDENTITY_SCHEMA",
    "DatasetExposureEvent",
    "DatasetIdentityArtifact",
    "DatasetRoleArtifact",
    "EXPERIMENT_IDENTITY_SCHEMA",
    "EXPERIMENT_STATUS_COMPLETED",
    "EXPERIMENT_STATUS_FAILED",
    "EXPERIMENT_STATUS_PREREGISTERED",
    "EXPERIMENT_STATUS_RUNNING",
    "EXPERIMENT_STATUS_SUPERSEDED",
    "EXPOSURE_STATE_EXPOSED_DEVELOPMENT",
    "EXPOSURE_STATE_EXPOSED_FINAL",
    "EXPOSURE_STATE_EXPOSED_INVALID_FOR_FINAL",
    "EXPOSURE_STATE_UNEXPOSED",
    "ExperimentRegistry",
    "FOLD_PROTOCOL_DEFAULT",
    "FOLD_PROTOCOL_IDENTITY_SCHEMA",
    "FoldPairSpec",
    "FoldProtocolArtifact",
    "G0CalibrationGateCertificate",
    "G0_BLOCKED_FINAL_DATA_LEAKAGE",
    "G0_BLOCKED_INVALID_DATASET_ROLE",
    "G0_BLOCKED_MISSING_OWNER_AUTHORIZATION",
    "G0_BLOCKED_OBJECTIVE_UNDEFINED",
    "G0_BLOCKED_UNREGISTERED_EXPERIMENT",
    "HUMAN_REVIEW_IDENTITY_SCHEMA",
    "HumanReviewRecord",
    "INFLUENCE_DESIGN_INFLUENCING",
    "INFLUENCE_DIAGNOSTIC_ONLY",
    "INFLUENCE_NONE",
    "LEGAL_CALIBRATION_PROVENANCE_KINDS",
    "LEGAL_CHANGE_INFLUENCES",
    "LEGAL_DATASET_ROLES",
    "LEGAL_EXPERIMENT_STATUSES",
    "LEGAL_EXPOSURE_STATES",
    "LEGAL_OBJECTIVE_KINDS",
    "LEGAL_POLICY_AUTHORITY_KINDS",
    "LEGAL_RESERVATION_STATUSES",
    "LEGAL_REVIEW_KINDS",
    "OBJECTIVE_IDENTITY_SCHEMA",
    "OBJECTIVE_KIND_DETECTION_VALIDITY",
    "OBJECTIVE_KIND_ECONOMIC_FORBIDDEN",
    "OBJECTIVE_KIND_INFORMATION",
    "OBJECTIVE_KIND_REPRESENTATION_DIAGNOSTIC",
    "ObjectiveArtifact",
    "POLICY_ARTIFACT_IDENTITY_SCHEMA",
    "POLICY_AUTHORITY_KIND_MUF",
    "POLICY_AUTHORITY_KIND_PREDEFINED",
    "PROVENANCE_DEVELOPMENT_FIT",
    "PROVENANCE_PREDEFINED_CONTRACT",
    "PolicyArtifact",
    "PolicyScopeMismatch",
    "QUALIFICATION_OBJECTIVE_DEFAULT",
    "RESERVATION_STATUS_FINAL_INVALIDATED",
    "RESERVATION_STATUS_FINAL_OPENED",
    "RESERVATION_STATUS_FINAL_RESERVED",
    "RESERVATION_STATUS_NOT_APPLICABLE",
    "REVIEW_KIND_DEVELOPMENT_AUDIT",
    "REVIEW_KIND_FINAL_AUDIT",
    "RepresentationExperimentRecord",
    "S3_CONTRADICTORY_REVIEW_INFLUENCE",
    "S3_ECONOMIC_OBJECTIVE_OUT_OF_SCOPE",
    "S3_EXPERIMENT_DELETION_FORBIDDEN",
    "S3_EXPERIMENT_IDENTITY_COLLISION",
    "S3_EXPOSED_ANCESTRY_CONTAMINATION",
    "S3_FINAL_DATASET_CONTAMINATED_BY_REVIEW",
    "S3_FINAL_DATA_LEAKED_INTO_WALK_FORWARD",
    "S3_ILLEGAL_FINAL_DATA_OPERATION",
    "S3_INFORMATION_OBJECTIVE_REQUIRES_ESTIMAND",
    "S3_INVALID_DATASET_IDENTITY",
    "S3_INVALID_DATASET_ROLE",
    "S3_INVALID_EXPERIMENT_RECORD",
    "S3_INVALID_FOLD_PROTOCOL",
    "S3_INVALID_HUMAN_REVIEW",
    "S3_INVALID_OBJECTIVE_ARTIFACT",
    "S3_INVALID_POLICY_ARTIFACT",
    "S3_INVALID_TURNING_POINT_PROMOTION",
    "S3_NON_INFORMATION_OBJECTIVE_FORBIDS_ESTIMAND",
    "S3_POLICY_REPRODUCTION_MISMATCH",
    "S3_POLICY_SCOPE_MISMATCH",
    "S3_PREMATURE_FINAL_INSPECTION",
    "S3_ROLE_REASSIGNMENT_AFTER_EXPOSURE",
    "S3_SCHEMA_IDENTITY",
    "S3_TEMPORAL_OVERLAP_NOT_INDEPENDENT",
    "S3_UNDECLARED_SHARED_CONTENT_ANCESTRY",
    "S3_UNREGISTERED_EXPERIMENT",
    "SelectionBlockedError",
    "evaluate_g0_calibration_gate",
    "promote_swing_witness_with_policy_artifact",
    "query_promoted_turning_points_as_of",
    "reassign_dataset_role",
    "record_dataset_exposure",
    "verify_dataset_independence_and_ancestry",
    "verify_policy_artifact_reproduction",
]
