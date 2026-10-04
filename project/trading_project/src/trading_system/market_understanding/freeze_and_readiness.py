"""MUF V1 S10, S11, S12 & Gate G3: Frozen Bundle, Evaluation Protocol, Pre-Final Readiness, Comparability & Equivalence.

Implements D1-18, D1-19, D1-20, D2-5, D2-6, D2-13, D2-14, D2-15, D2-19, D2-22,
Correction-1 §3, §4, Δ3, Δ5, and AP-1 §4.2, §4.3:
1. ``FrozenRepresentationBundle`` (S10, D2-15, I-FREEZE-1..4, I-SG-1B):
   freezes the exact closed bundle identity of all S2–S9 components, including
   state catalog, generic state graph spec, feature views, descriptors,
   dependence contracts, estimands, policies, objective, and experiment registry root.
2. ``EvaluationProtocolArtifact`` & ``EvaluationProtocolEventLedger`` (S11, D2-5,
   D2-6, Correction-1 §3, I-EVP-1..3, I-EVAL-1..6, I-RES-1..2, I-SG-1B):
   - ``EvaluationProtocolArtifact`` is strictly immutable and contains NO mutable
     post-open fields (``opened_at_or_null`` and ``exposure_log_root`` are excluded);
     ``protocol_hash`` stays byte-identical before and after ``OPENED`` (``I-EVP-2``).
   - Verifies ``I-SG-1B``: all referenced estimand/state/feature/graph/dependence
     dependencies must reside inside ``FrozenRepresentationBundle`` closure.
   - Hash-linked ``EvaluationProtocolEvent`` chain separates ``RESERVED`` (no exposure)
     from ``OPENED`` (irreversible exposure).
3. ``PreFinalReadinessRecord`` & ``evaluate_gate_g3_open_final_authorization``
   (S12 & Gate G3, D2-19, I-PFR-1..3, Correction-1 Δ5):
   - Verifies pre-final readiness without accessing protected final outcomes.
   - Blocks Gate G3 if readiness failed, dependency closure is incomplete, or
     owner opening authorization is missing.
4. ``EquivalenceClaimArtifact`` (D2-13, I-EQ-1..4) and ``ComparabilitySnapshotSpec``
   / ``evaluate_snapshot_comparability`` (D1-18, D1-19, D2-14, I-CMP-1..2, I-CMPL-1..3, I-MSN-1).
"""
from dataclasses import dataclass
from typing import Any, Final, Mapping, Optional, Sequence, Tuple, Union

from trading_system.market_understanding.contracts import (
    IllegalCausalReference,
    ImmutabilityViolation,
    SchemaIdentity,
    SchemaViolation,
    TypedState,
)
from trading_system.market_understanding.identity import (
    ArtifactIdentitySchema,
    canonical_artifact_identity,
)
from trading_system.market_understanding.policy_governance import (
    SelectionBlockedError,
)
from trading_system.market_understanding.records import ImmutableRecord
from trading_system.research.information_time import (
    InformationKey,
    InformationPhase,
)


S10_S12_SCHEMA_VERSION: Final[str] = "MUF_S10_S12_FREEZE_AND_READINESS_V1"
S10_S12_SCHEMA_IDENTITY: Final[SchemaIdentity] = SchemaIdentity(
    "MUF_S10_S12_FREEZE_AND_READINESS", "V1"
)

FROZEN_REPRESENTATION_BUNDLE_SCHEMA: Final[ArtifactIdentitySchema] = (
    ArtifactIdentitySchema(
        artifact_type="MUF_S10_FROZEN_REPRESENTATION_BUNDLE",
        schema_identity=S10_S12_SCHEMA_IDENTITY,
        identity_defining_fields=(
            "bundle_name",
            "artifact_lineage_id",
            "representation_spec_hash",
            "policy_artifact_hashes",
            "objective_artifact_hash_or_state",
            "state_catalog_hash",
            "graph_spec_hash",
            "feature_view_hashes",
            "descriptor_contract_hashes",
            "dependence_contract_hashes",
            "estimand_hashes",
            "fit_protocol_hash_or_state",
            "selection_protocol_hash_or_state",
            "dataset_role_artifact_hashes",
            "fold_protocol_hash_or_state",
            "code_artifact_hashes",
            "experiment_registry_root",
            "schema_contract_hashes",
            "freeze_information_key",
            "owner_freeze_authorization_ref",
        ),
    )
)

EVALUATION_PROTOCOL_ARTIFACT_SCHEMA: Final[ArtifactIdentitySchema] = (
    ArtifactIdentitySchema(
        artifact_type="MUF_S11_EVALUATION_PROTOCOL_ARTIFACT",
        schema_identity=S10_S12_SCHEMA_IDENTITY,
        identity_defining_fields=(
            "evaluation_protocol_id",
            "frozen_bundle_id",
            "artifact_lineage_id",
            "objective_artifact_hash",
            "estimand_hashes",
            "state_catalog_hash",
            "graph_spec_hash",
            "feature_view_hashes",
            "dataset_identity",
            "dataset_ancestry_root",
            "allowed_outputs",
            "prohibited_outputs",
            "opening_authorization_ref_or_state",
            "reservation_time_key",
            "schema_version",
        ),
    )
)

EVALUATION_PROTOCOL_EVENT_SCHEMA: Final[ArtifactIdentitySchema] = (
    ArtifactIdentitySchema(
        artifact_type="MUF_S11_EVALUATION_PROTOCOL_EVENT",
        schema_identity=S10_S12_SCHEMA_IDENTITY,
        identity_defining_fields=(
            "protocol_id",
            "event_type",
            "event_information_key",
            "payload_ref",
            "previous_event_hash",
        ),
    )
)

PRE_FINAL_READINESS_RECORD_SCHEMA: Final[ArtifactIdentitySchema] = (
    ArtifactIdentitySchema(
        artifact_type="MUF_S12_PRE_FINAL_READINESS_RECORD",
        schema_identity=S10_S12_SCHEMA_IDENTITY,
        identity_defining_fields=(
            "readiness_id",
            "bundle_id",
            "evaluation_protocol_id",
            "schema_valid",
            "artifact_identity_valid",
            "dependency_closure_valid",
            "synthetic_dry_run_valid",
            "protected_final_outcomes_accessed",
            "readiness_result",
            "proof_refs",
            "readiness_key",
        ),
    )
)

GATE_G3_AUTHORIZATION_SCHEMA: Final[ArtifactIdentitySchema] = (
    ArtifactIdentitySchema(
        artifact_type="MUF_GATE_G3_OPEN_FINAL_DECISION",
        schema_identity=S10_S12_SCHEMA_IDENTITY,
        identity_defining_fields=(
            "decision_id",
            "bundle_id",
            "evaluation_protocol_id",
            "readiness_hash",
            "owner_opening_authorization_ref",
            "gate_g3_status",
            "decision_key",
        ),
    )
)

EQUIVALENCE_CLAIM_ARTIFACT_SCHEMA: Final[ArtifactIdentitySchema] = (
    ArtifactIdentitySchema(
        artifact_type="MUF_S10_EQUIVALENCE_CLAIM_ARTIFACT",
        schema_identity=S10_S12_SCHEMA_IDENTITY,
        identity_defining_fields=(
            "claim_id",
            "old_bundle_id",
            "new_bundle_id",
            "evaluation_claim_scope",
            "required_equivalence_dimensions",
            "proven_equivalence_dimensions",
            "proof_refs",
            "equivalence_result",
        ),
    )
)

# EvaluationProtocolEvent types (Correction-1 §3)
PROTOCOL_EVENT_RESERVED: Final[str] = "RESERVED"
PROTOCOL_EVENT_OPEN_AUTHORIZED: Final[str] = "OPEN_AUTHORIZED"
PROTOCOL_EVENT_OPENED: Final[str] = "OPENED"
PROTOCOL_EVENT_OUTPUT_EMITTED: Final[str] = "OUTPUT_EMITTED"
PROTOCOL_EVENT_EXPLORATORY_OUTPUT_REQUESTED: Final[str] = (
    "EXPLORATORY_OUTPUT_REQUESTED"
)
PROTOCOL_EVENT_INVALIDATED: Final[str] = "INVALIDATED"

VALID_PROTOCOL_EVENT_TYPES: Final[Tuple[str, ...]] = (
    PROTOCOL_EVENT_RESERVED,
    PROTOCOL_EVENT_OPEN_AUTHORIZED,
    PROTOCOL_EVENT_OPENED,
    PROTOCOL_EVENT_OUTPUT_EMITTED,
    PROTOCOL_EVENT_EXPLORATORY_OUTPUT_REQUESTED,
    PROTOCOL_EVENT_INVALIDATED,
)

# Pre-final readiness & Gate G3 statuses (D2-19)
READINESS_RESULT_READY: Final[str] = "READY"
READINESS_RESULT_FAILED: Final[str] = "FAILED"
GATE_G3_AUTHORIZED_TO_OPEN: Final[str] = "GATE_G3_AUTHORIZED_TO_OPEN"

# Equivalence dimensions & results (D2-13, I-EQ-1..4)
EQ_DIM_SEMANTIC_OUTPUT: Final[str] = "SEMANTIC_OUTPUT_EQUIVALENCE"
EQ_DIM_CAUSAL_VISIBILITY: Final[str] = "CAUSAL_VISIBILITY_EQUIVALENCE"
EQ_DIM_PROVENANCE: Final[str] = "PROVENANCE_EQUIVALENCE"
EQ_DIM_SELECTION_PROCESS: Final[str] = "SELECTION_PROCESS_EQUIVALENCE"
EQ_DIM_SCHEMA: Final[str] = "SCHEMA_EQUIVALENCE"
EQ_DIM_EVALUATION_OUTPUT: Final[str] = "EVALUATION_OUTPUT_EQUIVALENCE"

EQUIVALENCE_RESULT_CERTIFIED: Final[str] = "EQUIVALENCE_CERTIFIED"
EQUIVALENCE_RESULT_REJECTED: Final[str] = "EQUIVALENCE_REJECTED_NEW_LINEAGE_REQUIRED"

# Comparability levels (D1-18, D1-19, D2-14, I-CMPL-1..3)
COMPARABILITY_IDENTICAL_CONTRACT: Final[str] = "IDENTICAL_CONTRACT_COMPARABLE"
COMPARABILITY_MAPPED: Final[str] = "MAPPED_COMPARABLE"
COMPARABILITY_NOT_COMPARABLE: Final[str] = "NOT_COMPARABLE"

# Deterministic error codes
S10_INVALID_FROZEN_BUNDLE: Final[str] = "S10_INVALID_FROZEN_BUNDLE"
S11_INVALID_EVALUATION_PROTOCOL: Final[str] = "S11_INVALID_EVALUATION_PROTOCOL"
S11_BUNDLE_DEPENDENCY_CLOSURE_MISSING: Final[str] = (
    "S11_BUNDLE_DEPENDENCY_CLOSURE_MISSING"
)
S11_INVALID_PROTOCOL_EVENT: Final[str] = "S11_INVALID_PROTOCOL_EVENT"
S11_PROTOCOL_ALREADY_OPENED_FOR_LINEAGE: Final[str] = (
    "S11_PROTOCOL_ALREADY_OPENED_FOR_LINEAGE"
)
S12_INVALID_READINESS_RECORD: Final[str] = "S12_INVALID_READINESS_RECORD"
S12_PROTECTED_FINAL_DATA_USED_IN_READINESS: Final[str] = (
    "S12_PROTECTED_FINAL_DATA_USED_IN_READINESS"
)
G3_OPEN_FINAL_BLOCKED: Final[str] = "G3_OPEN_FINAL_BLOCKED"
S10_INVALID_EQUIVALENCE_CLAIM: Final[str] = "S10_INVALID_EQUIVALENCE_CLAIM"
S10_NOT_COMPARABLE_DISTANCE_FORBIDDEN: Final[str] = (
    "S10_NOT_COMPARABLE_DISTANCE_FORBIDDEN"
)


def _require_non_empty_str(val: Any, field_name: str, code: str) -> str:
    if not isinstance(val, str) or not val.strip():
        raise SchemaViolation(f"{code}: {field_name} must be a non-empty string")
    return val


def _require_str_tuple(
    vals: Any, field_name: str, code: str, *, allow_empty: bool = False
) -> Tuple[str, ...]:
    if not isinstance(vals, (tuple, list)):
        raise SchemaViolation(
            f"{code}: {field_name} must be a sequence of strings"
        )
    res: list[str] = []
    for idx, item in enumerate(vals):
        res.append(_require_non_empty_str(item, f"{field_name}[{idx}]", code))
    if not allow_empty and len(res) == 0:
        raise SchemaViolation(f"{code}: {field_name} must be non-empty")
    return tuple(res)


def _require_completed_key(
    key: Any, field_name: str, code: str
) -> InformationKey:
    if not isinstance(key, InformationKey):
        raise SchemaViolation(
            f"{code}: {field_name} must be an InformationKey"
        )
    if key.information_phase != InformationPhase.COMPLETED_ROW_AVAILABLE:
        raise IllegalCausalReference(
            f"{code}: {field_name} requires COMPLETED_ROW_AVAILABLE"
        )
    return key


def _serialize_seq(items: Sequence[str]) -> Mapping[str, str]:
    return {str(idx): item for idx, item in enumerate(items)}


def _tok_or_str(val: Union[str, TypedState], field_name: str, code: str) -> str:
    if isinstance(val, TypedState):
        return val.value
    return _require_non_empty_str(val, field_name, code)


@dataclass(frozen=True)
class FrozenRepresentationBundle(ImmutableRecord):
    """Frozen, immutable representation bundle (S10, D2-15, I-FREEZE-1..4, I-SG-1B)."""

    bundle_name: str
    artifact_lineage_id: str
    representation_spec_hash: str
    policy_artifact_hashes: Tuple[str, ...]
    objective_artifact_hash_or_state: Union[str, TypedState]
    state_catalog_hash: str
    graph_spec_hash: str
    feature_view_hashes: Tuple[str, ...]
    descriptor_contract_hashes: Tuple[str, ...]
    dependence_contract_hashes: Tuple[str, ...]
    estimand_hashes: Tuple[str, ...]
    fit_protocol_hash_or_state: Union[str, TypedState]
    selection_protocol_hash_or_state: Union[str, TypedState]
    dataset_role_artifact_hashes: Tuple[str, ...]
    fold_protocol_hash_or_state: Union[str, TypedState]
    code_artifact_hashes: Tuple[str, ...]
    experiment_registry_root: str
    schema_contract_hashes: Tuple[str, ...]
    freeze_information_key: InformationKey
    owner_freeze_authorization_ref: str
    bundle_id: str

    def __post_init__(self) -> None:
        for f_name, f_val in (
            ("bundle_name", self.bundle_name),
            ("artifact_lineage_id", self.artifact_lineage_id),
            ("representation_spec_hash", self.representation_spec_hash),
            ("state_catalog_hash", self.state_catalog_hash),
            ("graph_spec_hash", self.graph_spec_hash),
            ("experiment_registry_root", self.experiment_registry_root),
            (
                "owner_freeze_authorization_ref",
                self.owner_freeze_authorization_ref,
            ),
        ):
            _require_non_empty_str(f_val, f_name, S10_INVALID_FROZEN_BUNDLE)

        pol_h = _require_str_tuple(
            self.policy_artifact_hashes,
            "policy_artifact_hashes",
            S10_INVALID_FROZEN_BUNDLE,
        )
        fv_h = _require_str_tuple(
            self.feature_view_hashes,
            "feature_view_hashes",
            S10_INVALID_FROZEN_BUNDLE,
        )
        desc_h = _require_str_tuple(
            self.descriptor_contract_hashes,
            "descriptor_contract_hashes",
            S10_INVALID_FROZEN_BUNDLE,
        )
        dep_h = _require_str_tuple(
            self.dependence_contract_hashes,
            "dependence_contract_hashes",
            S10_INVALID_FROZEN_BUNDLE,
        )
        est_h = _require_str_tuple(
            self.estimand_hashes,
            "estimand_hashes",
            S10_INVALID_FROZEN_BUNDLE,
        )
        ds_role_h = _require_str_tuple(
            self.dataset_role_artifact_hashes,
            "dataset_role_artifact_hashes",
            S10_INVALID_FROZEN_BUNDLE,
        )
        code_h = _require_str_tuple(
            self.code_artifact_hashes,
            "code_artifact_hashes",
            S10_INVALID_FROZEN_BUNDLE,
        )
        schema_h = _require_str_tuple(
            self.schema_contract_hashes,
            "schema_contract_hashes",
            S10_INVALID_FROZEN_BUNDLE,
        )

        object.__setattr__(self, "policy_artifact_hashes", pol_h)
        object.__setattr__(self, "feature_view_hashes", fv_h)
        object.__setattr__(self, "descriptor_contract_hashes", desc_h)
        object.__setattr__(self, "dependence_contract_hashes", dep_h)
        object.__setattr__(self, "estimand_hashes", est_h)
        object.__setattr__(self, "dataset_role_artifact_hashes", ds_role_h)
        object.__setattr__(self, "code_artifact_hashes", code_h)
        object.__setattr__(self, "schema_contract_hashes", schema_h)

        obj_tok = _tok_or_str(
            self.objective_artifact_hash_or_state,
            "objective_artifact_hash_or_state",
            S10_INVALID_FROZEN_BUNDLE,
        )
        fit_tok = _tok_or_str(
            self.fit_protocol_hash_or_state,
            "fit_protocol_hash_or_state",
            S10_INVALID_FROZEN_BUNDLE,
        )
        sel_tok = _tok_or_str(
            self.selection_protocol_hash_or_state,
            "selection_protocol_hash_or_state",
            S10_INVALID_FROZEN_BUNDLE,
        )
        fold_tok = _tok_or_str(
            self.fold_protocol_hash_or_state,
            "fold_protocol_hash_or_state",
            S10_INVALID_FROZEN_BUNDLE,
        )
        _require_completed_key(
            self.freeze_information_key,
            "freeze_information_key",
            S10_INVALID_FROZEN_BUNDLE,
        )

        expected_id = canonical_artifact_identity(
            FROZEN_REPRESENTATION_BUNDLE_SCHEMA,
            identity_payload={
                "bundle_name": self.bundle_name,
                "artifact_lineage_id": self.artifact_lineage_id,
                "representation_spec_hash": self.representation_spec_hash,
                "policy_artifact_hashes": _serialize_seq(pol_h),
                "objective_artifact_hash_or_state": obj_tok,
                "state_catalog_hash": self.state_catalog_hash,
                "graph_spec_hash": self.graph_spec_hash,
                "feature_view_hashes": _serialize_seq(fv_h),
                "descriptor_contract_hashes": _serialize_seq(desc_h),
                "dependence_contract_hashes": _serialize_seq(dep_h),
                "estimand_hashes": _serialize_seq(est_h),
                "fit_protocol_hash_or_state": fit_tok,
                "selection_protocol_hash_or_state": sel_tok,
                "dataset_role_artifact_hashes": _serialize_seq(ds_role_h),
                "fold_protocol_hash_or_state": fold_tok,
                "code_artifact_hashes": _serialize_seq(code_h),
                "experiment_registry_root": self.experiment_registry_root,
                "schema_contract_hashes": _serialize_seq(schema_h),
                "freeze_information_key": self.freeze_information_key,
                "owner_freeze_authorization_ref": self.owner_freeze_authorization_ref,
            },
        )
        if self.bundle_id != expected_id:
            raise SchemaViolation(
                f"{S10_INVALID_FROZEN_BUNDLE}: bundle_id mismatch (I-FREEZE-1)"
            )

    @classmethod
    def create(
        cls,
        *,
        bundle_name: str,
        artifact_lineage_id: str,
        representation_spec_hash: str,
        policy_artifact_hashes: Sequence[str],
        objective_artifact_hash_or_state: Union[str, TypedState],
        state_catalog_hash: str,
        graph_spec_hash: str,
        feature_view_hashes: Sequence[str],
        descriptor_contract_hashes: Sequence[str],
        dependence_contract_hashes: Sequence[str],
        estimand_hashes: Sequence[str],
        fit_protocol_hash_or_state: Union[str, TypedState],
        selection_protocol_hash_or_state: Union[str, TypedState],
        dataset_role_artifact_hashes: Sequence[str],
        fold_protocol_hash_or_state: Union[str, TypedState] = TypedState.NOT_CONFIGURED,
        code_artifact_hashes: Sequence[str],
        experiment_registry_root: str,
        schema_contract_hashes: Sequence[str],
        freeze_information_key: InformationKey,
        owner_freeze_authorization_ref: str,
    ) -> "FrozenRepresentationBundle":
        pol_h = _require_str_tuple(
            policy_artifact_hashes,
            "policy_artifact_hashes",
            S10_INVALID_FROZEN_BUNDLE,
        )
        fv_h = _require_str_tuple(
            feature_view_hashes,
            "feature_view_hashes",
            S10_INVALID_FROZEN_BUNDLE,
        )
        desc_h = _require_str_tuple(
            descriptor_contract_hashes,
            "descriptor_contract_hashes",
            S10_INVALID_FROZEN_BUNDLE,
        )
        dep_h = _require_str_tuple(
            dependence_contract_hashes,
            "dependence_contract_hashes",
            S10_INVALID_FROZEN_BUNDLE,
        )
        est_h = _require_str_tuple(
            estimand_hashes,
            "estimand_hashes",
            S10_INVALID_FROZEN_BUNDLE,
        )
        ds_role_h = _require_str_tuple(
            dataset_role_artifact_hashes,
            "dataset_role_artifact_hashes",
            S10_INVALID_FROZEN_BUNDLE,
        )
        code_h = _require_str_tuple(
            code_artifact_hashes,
            "code_artifact_hashes",
            S10_INVALID_FROZEN_BUNDLE,
        )
        schema_h = _require_str_tuple(
            schema_contract_hashes,
            "schema_contract_hashes",
            S10_INVALID_FROZEN_BUNDLE,
        )
        obj_tok = _tok_or_str(
            objective_artifact_hash_or_state,
            "objective_artifact_hash_or_state",
            S10_INVALID_FROZEN_BUNDLE,
        )
        fit_tok = _tok_or_str(
            fit_protocol_hash_or_state,
            "fit_protocol_hash_or_state",
            S10_INVALID_FROZEN_BUNDLE,
        )
        sel_tok = _tok_or_str(
            selection_protocol_hash_or_state,
            "selection_protocol_hash_or_state",
            S10_INVALID_FROZEN_BUNDLE,
        )
        fold_tok = _tok_or_str(
            fold_protocol_hash_or_state,
            "fold_protocol_hash_or_state",
            S10_INVALID_FROZEN_BUNDLE,
        )
        b_id = canonical_artifact_identity(
            FROZEN_REPRESENTATION_BUNDLE_SCHEMA,
            identity_payload={
                "bundle_name": bundle_name,
                "artifact_lineage_id": artifact_lineage_id,
                "representation_spec_hash": representation_spec_hash,
                "policy_artifact_hashes": _serialize_seq(pol_h),
                "objective_artifact_hash_or_state": obj_tok,
                "state_catalog_hash": state_catalog_hash,
                "graph_spec_hash": graph_spec_hash,
                "feature_view_hashes": _serialize_seq(fv_h),
                "descriptor_contract_hashes": _serialize_seq(desc_h),
                "dependence_contract_hashes": _serialize_seq(dep_h),
                "estimand_hashes": _serialize_seq(est_h),
                "fit_protocol_hash_or_state": fit_tok,
                "selection_protocol_hash_or_state": sel_tok,
                "dataset_role_artifact_hashes": _serialize_seq(ds_role_h),
                "fold_protocol_hash_or_state": fold_tok,
                "code_artifact_hashes": _serialize_seq(code_h),
                "experiment_registry_root": experiment_registry_root,
                "schema_contract_hashes": _serialize_seq(schema_h),
                "freeze_information_key": freeze_information_key,
                "owner_freeze_authorization_ref": owner_freeze_authorization_ref,
            },
        )
        return cls(
            bundle_name=bundle_name,
            artifact_lineage_id=artifact_lineage_id,
            representation_spec_hash=representation_spec_hash,
            policy_artifact_hashes=pol_h,
            objective_artifact_hash_or_state=objective_artifact_hash_or_state,
            state_catalog_hash=state_catalog_hash,
            graph_spec_hash=graph_spec_hash,
            feature_view_hashes=fv_h,
            descriptor_contract_hashes=desc_h,
            dependence_contract_hashes=dep_h,
            estimand_hashes=est_h,
            fit_protocol_hash_or_state=fit_protocol_hash_or_state,
            selection_protocol_hash_or_state=selection_protocol_hash_or_state,
            dataset_role_artifact_hashes=ds_role_h,
            fold_protocol_hash_or_state=fold_protocol_hash_or_state,
            code_artifact_hashes=code_h,
            experiment_registry_root=experiment_registry_root,
            schema_contract_hashes=schema_h,
            freeze_information_key=freeze_information_key,
            owner_freeze_authorization_ref=owner_freeze_authorization_ref,
            bundle_id=b_id,
        )


@dataclass(frozen=True)
class EvaluationProtocolArtifact(ImmutableRecord):
    """Immutable EvaluationProtocolArtifact (S11, D2-5, Correction-1 §3, I-EVP-1..3, I-SG-1B).

    Excludes mutable post-open fields (no ``opened_at_or_null``, no ``exposure_log_root``);
    ``protocol_hash`` stays byte-identical before and after ``OPENED``.
    """

    evaluation_protocol_id: str
    frozen_bundle_id: str
    artifact_lineage_id: str
    objective_artifact_hash: str
    estimand_hashes: Tuple[str, ...]
    state_catalog_hash: str
    graph_spec_hash: str
    feature_view_hashes: Tuple[str, ...]
    dataset_identity: str
    dataset_ancestry_root: str
    allowed_outputs: Tuple[str, ...]
    prohibited_outputs: Tuple[str, ...]
    opening_authorization_ref_or_state: Union[str, TypedState]
    reservation_time_key: InformationKey
    schema_version: str
    protocol_hash: str

    def __post_init__(self) -> None:
        for f_name, f_val in (
            ("evaluation_protocol_id", self.evaluation_protocol_id),
            ("frozen_bundle_id", self.frozen_bundle_id),
            ("artifact_lineage_id", self.artifact_lineage_id),
            ("objective_artifact_hash", self.objective_artifact_hash),
            ("state_catalog_hash", self.state_catalog_hash),
            ("graph_spec_hash", self.graph_spec_hash),
            ("dataset_identity", self.dataset_identity),
            ("dataset_ancestry_root", self.dataset_ancestry_root),
            ("schema_version", self.schema_version),
        ):
            _require_non_empty_str(
                f_val, f_name, S11_INVALID_EVALUATION_PROTOCOL
            )

        est_h = _require_str_tuple(
            self.estimand_hashes,
            "estimand_hashes",
            S11_INVALID_EVALUATION_PROTOCOL,
        )
        fv_h = _require_str_tuple(
            self.feature_view_hashes,
            "feature_view_hashes",
            S11_INVALID_EVALUATION_PROTOCOL,
        )
        allowed = _require_str_tuple(
            self.allowed_outputs,
            "allowed_outputs",
            S11_INVALID_EVALUATION_PROTOCOL,
        )
        prohibited = _require_str_tuple(
            self.prohibited_outputs,
            "prohibited_outputs",
            S11_INVALID_EVALUATION_PROTOCOL,
            allow_empty=True,
        )
        if set(allowed) & set(prohibited):
            raise SchemaViolation(
                f"{S11_INVALID_EVALUATION_PROTOCOL}: allowed_outputs and prohibited_outputs cannot overlap"
            )
        object.__setattr__(self, "estimand_hashes", est_h)
        object.__setattr__(self, "feature_view_hashes", fv_h)
        object.__setattr__(self, "allowed_outputs", allowed)
        object.__setattr__(self, "prohibited_outputs", prohibited)

        open_tok = _tok_or_str(
            self.opening_authorization_ref_or_state,
            "opening_authorization_ref_or_state",
            S11_INVALID_EVALUATION_PROTOCOL,
        )
        _require_completed_key(
            self.reservation_time_key,
            "reservation_time_key",
            S11_INVALID_EVALUATION_PROTOCOL,
        )

        expected_hash = canonical_artifact_identity(
            EVALUATION_PROTOCOL_ARTIFACT_SCHEMA,
            identity_payload={
                "evaluation_protocol_id": self.evaluation_protocol_id,
                "frozen_bundle_id": self.frozen_bundle_id,
                "artifact_lineage_id": self.artifact_lineage_id,
                "objective_artifact_hash": self.objective_artifact_hash,
                "estimand_hashes": _serialize_seq(est_h),
                "state_catalog_hash": self.state_catalog_hash,
                "graph_spec_hash": self.graph_spec_hash,
                "feature_view_hashes": _serialize_seq(fv_h),
                "dataset_identity": self.dataset_identity,
                "dataset_ancestry_root": self.dataset_ancestry_root,
                "allowed_outputs": _serialize_seq(allowed),
                "prohibited_outputs": _serialize_seq(prohibited),
                "opening_authorization_ref_or_state": open_tok,
                "reservation_time_key": self.reservation_time_key,
                "schema_version": self.schema_version,
            },
        )
        if self.protocol_hash != expected_hash:
            raise SchemaViolation(
                f"{S11_INVALID_EVALUATION_PROTOCOL}: protocol_hash mismatch (I-EVP-2)"
            )

    @classmethod
    def create(
        cls,
        *,
        evaluation_protocol_id: str,
        frozen_bundle: FrozenRepresentationBundle,
        objective_artifact_hash: str,
        estimand_hashes: Sequence[str],
        state_catalog_hash: str,
        graph_spec_hash: str,
        feature_view_hashes: Sequence[str],
        dataset_identity: str,
        dataset_ancestry_root: str,
        allowed_outputs: Sequence[str],
        prohibited_outputs: Sequence[str] = (),
        opening_authorization_ref_or_state: Union[
            str, TypedState
        ] = TypedState.NOT_CONFIGURED,
        reservation_time_key: InformationKey,
        schema_version: str = S10_S12_SCHEMA_VERSION,
    ) -> "EvaluationProtocolArtifact":
        if not isinstance(frozen_bundle, FrozenRepresentationBundle):
            raise SchemaViolation(
                f"{S11_INVALID_EVALUATION_PROTOCOL}: frozen_bundle must be a FrozenRepresentationBundle"
            )
        est_h = _require_str_tuple(
            estimand_hashes,
            "estimand_hashes",
            S11_INVALID_EVALUATION_PROTOCOL,
        )
        fv_h = _require_str_tuple(
            feature_view_hashes,
            "feature_view_hashes",
            S11_INVALID_EVALUATION_PROTOCOL,
        )
        # Verify I-SG-1B: all dependencies must be in FrozenRepresentationBundle closure
        if (
            state_catalog_hash != frozen_bundle.state_catalog_hash
            or graph_spec_hash != frozen_bundle.graph_spec_hash
            or not set(est_h).issubset(set(frozen_bundle.estimand_hashes))
            or not set(fv_h).issubset(set(frozen_bundle.feature_view_hashes))
        ):
            raise SelectionBlockedError(
                f"{S11_BUNDLE_DEPENDENCY_CLOSURE_MISSING}: EvaluationProtocol references state/feature/estimand "
                "dependency absent from FrozenRepresentationBundle closure (I-SG-1B)"
            )

        allowed = _require_str_tuple(
            allowed_outputs,
            "allowed_outputs",
            S11_INVALID_EVALUATION_PROTOCOL,
        )
        prohibited = _require_str_tuple(
            prohibited_outputs,
            "prohibited_outputs",
            S11_INVALID_EVALUATION_PROTOCOL,
            allow_empty=True,
        )
        open_tok = _tok_or_str(
            opening_authorization_ref_or_state,
            "opening_authorization_ref_or_state",
            S11_INVALID_EVALUATION_PROTOCOL,
        )
        p_hash = canonical_artifact_identity(
            EVALUATION_PROTOCOL_ARTIFACT_SCHEMA,
            identity_payload={
                "evaluation_protocol_id": evaluation_protocol_id,
                "frozen_bundle_id": frozen_bundle.bundle_id,
                "artifact_lineage_id": frozen_bundle.artifact_lineage_id,
                "objective_artifact_hash": objective_artifact_hash,
                "estimand_hashes": _serialize_seq(est_h),
                "state_catalog_hash": state_catalog_hash,
                "graph_spec_hash": graph_spec_hash,
                "feature_view_hashes": _serialize_seq(fv_h),
                "dataset_identity": dataset_identity,
                "dataset_ancestry_root": dataset_ancestry_root,
                "allowed_outputs": _serialize_seq(allowed),
                "prohibited_outputs": _serialize_seq(prohibited),
                "opening_authorization_ref_or_state": open_tok,
                "reservation_time_key": reservation_time_key,
                "schema_version": schema_version,
            },
        )
        return cls(
            evaluation_protocol_id=evaluation_protocol_id,
            frozen_bundle_id=frozen_bundle.bundle_id,
            artifact_lineage_id=frozen_bundle.artifact_lineage_id,
            objective_artifact_hash=objective_artifact_hash,
            estimand_hashes=est_h,
            state_catalog_hash=state_catalog_hash,
            graph_spec_hash=graph_spec_hash,
            feature_view_hashes=fv_h,
            dataset_identity=dataset_identity,
            dataset_ancestry_root=dataset_ancestry_root,
            allowed_outputs=allowed,
            prohibited_outputs=prohibited,
            opening_authorization_ref_or_state=opening_authorization_ref_or_state,
            reservation_time_key=reservation_time_key,
            schema_version=schema_version,
            protocol_hash=p_hash,
        )


def verify_final_protocol_bundle_closure(
    protocol: EvaluationProtocolArtifact,
    *,
    frozen_bundle: FrozenRepresentationBundle,
) -> bool:
    """Verify I-SG-1B: all protocol dependencies exist inside FrozenRepresentationBundle."""
    if not isinstance(protocol, EvaluationProtocolArtifact) or not isinstance(
        frozen_bundle, FrozenRepresentationBundle
    ):
        raise SelectionBlockedError(
            f"{S11_BUNDLE_DEPENDENCY_CLOSURE_MISSING}: valid EvaluationProtocolArtifact and FrozenRepresentationBundle required"
        )
    if (
        protocol.frozen_bundle_id != frozen_bundle.bundle_id
        or protocol.artifact_lineage_id != frozen_bundle.artifact_lineage_id
        or protocol.state_catalog_hash != frozen_bundle.state_catalog_hash
        or protocol.graph_spec_hash != frozen_bundle.graph_spec_hash
        or not set(protocol.estimand_hashes).issubset(
            set(frozen_bundle.estimand_hashes)
        )
        or not set(protocol.feature_view_hashes).issubset(
            set(frozen_bundle.feature_view_hashes)
        )
    ):
        raise SelectionBlockedError(
            f"{S11_BUNDLE_DEPENDENCY_CLOSURE_MISSING}: protocol dependency outside FrozenRepresentationBundle closure (I-SG-1B)"
        )
    return True


@dataclass(frozen=True)
class EvaluationProtocolEvent(ImmutableRecord):
    """Append-only hash-linked EvaluationProtocolEvent (Correction-1 §3, I-EVP-1..3)."""

    protocol_id: str
    event_type: str
    event_information_key: InformationKey
    payload_ref: str
    previous_event_hash: str
    event_hash: str

    def __post_init__(self) -> None:
        _require_non_empty_str(
            self.protocol_id, "protocol_id", S11_INVALID_PROTOCOL_EVENT
        )
        if self.event_type not in VALID_PROTOCOL_EVENT_TYPES:
            raise SchemaViolation(
                f"{S11_INVALID_PROTOCOL_EVENT}: invalid event_type {self.event_type!r}"
            )
        _require_completed_key(
            self.event_information_key,
            "event_information_key",
            S11_INVALID_PROTOCOL_EVENT,
        )
        _require_non_empty_str(
            self.payload_ref, "payload_ref", S11_INVALID_PROTOCOL_EVENT
        )
        _require_non_empty_str(
            self.previous_event_hash,
            "previous_event_hash",
            S11_INVALID_PROTOCOL_EVENT,
        )
        expected_hash = canonical_artifact_identity(
            EVALUATION_PROTOCOL_EVENT_SCHEMA,
            identity_payload={
                "protocol_id": self.protocol_id,
                "event_type": self.event_type,
                "event_information_key": self.event_information_key,
                "payload_ref": self.payload_ref,
                "previous_event_hash": self.previous_event_hash,
            },
        )
        if self.event_hash != expected_hash:
            raise SchemaViolation(
                f"{S11_INVALID_PROTOCOL_EVENT}: event_hash mismatch"
            )


class EvaluationProtocolEventLedger:
    """Append-only hash-linked event ledger projecting EvaluationProtocolArtifact state (Correction-1 §3, I-EVP-1..3)."""

    def __init__(self) -> None:
        self.__protocols: dict[str, EvaluationProtocolArtifact] = {}
        self.__events_by_protocol: dict[
            str, list[EvaluationProtocolEvent]
        ] = {}
        self.__opened_protocol_lineages: set[Tuple[str, str]] = set()

    def register_reserved_protocol(
        self, protocol: EvaluationProtocolArtifact
    ) -> EvaluationProtocolEvent:
        if not isinstance(protocol, EvaluationProtocolArtifact):
            raise SchemaViolation(
                f"{S11_INVALID_EVALUATION_PROTOCOL}: expected EvaluationProtocolArtifact"
            )
        protos = object.__getattribute__(
            self, "_EvaluationProtocolEventLedger__protocols"
        )
        if protocol.evaluation_protocol_id in protos:
            raise ImmutabilityViolation(
                f"{S11_INVALID_EVALUATION_PROTOCOL}: protocol {protocol.evaluation_protocol_id!r} already registered"
            )
        protos[protocol.evaluation_protocol_id] = protocol
        ev_map = object.__getattribute__(
            self, "_EvaluationProtocolEventLedger__events_by_protocol"
        )
        ev_map[protocol.evaluation_protocol_id] = []
        return self.append_event(
            protocol_id=protocol.evaluation_protocol_id,
            event_type=PROTOCOL_EVENT_RESERVED,
            event_information_key=protocol.reservation_time_key,
            payload_ref=f"reserved:{protocol.protocol_hash}",
        )

    def append_event(
        self,
        *,
        protocol_id: str,
        event_type: str,
        event_information_key: InformationKey,
        payload_ref: str,
    ) -> EvaluationProtocolEvent:
        protos = object.__getattribute__(
            self, "_EvaluationProtocolEventLedger__protocols"
        )
        if protocol_id not in protos:
            raise SchemaViolation(
                f"{S11_INVALID_PROTOCOL_EVENT}: unknown protocol_id {protocol_id!r}"
            )
        proto = protos[protocol_id]
        ev_map = object.__getattribute__(
            self, "_EvaluationProtocolEventLedger__events_by_protocol"
        )
        chain = ev_map[protocol_id]
        prev_hash = "GENESIS" if len(chain) == 0 else chain[-1].event_hash

        if event_type == PROTOCOL_EVENT_OPENED:
            opened_set = object.__getattribute__(
                self, "_EvaluationProtocolEventLedger__opened_protocol_lineages"
            )
            lineage_pair = (proto.evaluation_protocol_id, proto.artifact_lineage_id)
            if lineage_pair in opened_set:
                raise SelectionBlockedError(
                    f"{S11_PROTOCOL_ALREADY_OPENED_FOR_LINEAGE}: protocol {protocol_id!r} "
                    f"already OPENED for lineage {proto.artifact_lineage_id!r} (I-EVAL-1)"
                )
            opened_set.add(lineage_pair)

        ev_hash = canonical_artifact_identity(
            EVALUATION_PROTOCOL_EVENT_SCHEMA,
            identity_payload={
                "protocol_id": protocol_id,
                "event_type": event_type,
                "event_information_key": event_information_key,
                "payload_ref": payload_ref,
                "previous_event_hash": prev_hash,
            },
        )
        ev = EvaluationProtocolEvent(
            protocol_id=protocol_id,
            event_type=event_type,
            event_information_key=event_information_key,
            payload_ref=payload_ref,
            previous_event_hash=prev_hash,
            event_hash=ev_hash,
        )
        chain.append(ev)
        return ev

    def protocol(self, protocol_id: str) -> EvaluationProtocolArtifact:
        protos = object.__getattribute__(
            self, "_EvaluationProtocolEventLedger__protocols"
        )
        if protocol_id not in protos:
            raise SchemaViolation(
                f"{S11_INVALID_PROTOCOL_EVENT}: unknown protocol_id {protocol_id!r}"
            )
        return protos[protocol_id]

    def events(self, protocol_id: str) -> Tuple[EvaluationProtocolEvent, ...]:
        ev_map = object.__getattribute__(
            self, "_EvaluationProtocolEventLedger__events_by_protocol"
        )
        if protocol_id not in ev_map:
            raise SchemaViolation(
                f"{S11_INVALID_PROTOCOL_EVENT}: unknown protocol_id {protocol_id!r}"
            )
        return tuple(ev_map[protocol_id])

    def is_exposed(self, protocol_id: str) -> bool:
        """Reservation is NOT exposure (I-RES-1); only OPENED triggers exposure (I-EVAL-2)."""
        return any(
            ev.event_type == PROTOCOL_EVENT_OPENED
            for ev in self.events(protocol_id)
        )


@dataclass(frozen=True)
class PreFinalReadinessRecord(ImmutableRecord):
    """Pre-Final Readiness Record without protected final outcomes (S12, D2-19, I-PFR-1..3)."""

    readiness_id: str
    bundle_id: str
    evaluation_protocol_id: str
    schema_valid: bool
    artifact_identity_valid: bool
    dependency_closure_valid: bool
    synthetic_dry_run_valid: bool
    protected_final_outcomes_accessed: bool
    readiness_result: str
    proof_refs: Tuple[str, ...]
    readiness_key: InformationKey
    readiness_hash: str

    def __post_init__(self) -> None:
        for f_name, f_val in (
            ("readiness_id", self.readiness_id),
            ("bundle_id", self.bundle_id),
            ("evaluation_protocol_id", self.evaluation_protocol_id),
        ):
            _require_non_empty_str(f_val, f_name, S12_INVALID_READINESS_RECORD)

        for b_name, b_val in (
            ("schema_valid", self.schema_valid),
            ("artifact_identity_valid", self.artifact_identity_valid),
            ("dependency_closure_valid", self.dependency_closure_valid),
            ("synthetic_dry_run_valid", self.synthetic_dry_run_valid),
            (
                "protected_final_outcomes_accessed",
                self.protected_final_outcomes_accessed,
            ),
        ):
            if not isinstance(b_val, bool):
                raise SchemaViolation(
                    f"{S12_INVALID_READINESS_RECORD}: {b_name} must be bool"
                )

        if self.protected_final_outcomes_accessed:
            raise SelectionBlockedError(
                f"{S12_PROTECTED_FINAL_DATA_USED_IN_READINESS}: Pre-Final Readiness must not access protected final outcomes (I-PFR-2, I-PFR-3)"
            )
        if self.readiness_result not in (
            READINESS_RESULT_READY,
            READINESS_RESULT_FAILED,
        ):
            raise SchemaViolation(
                f"{S12_INVALID_READINESS_RECORD}: invalid readiness_result {self.readiness_result!r}"
            )
        all_passed = (
            self.schema_valid
            and self.artifact_identity_valid
            and self.dependency_closure_valid
            and self.synthetic_dry_run_valid
            and not self.protected_final_outcomes_accessed
        )
        if self.readiness_result == READINESS_RESULT_READY and not all_passed:
            raise SchemaViolation(
                f"{S12_INVALID_READINESS_RECORD}: readiness_result cannot be READY when a check failed"
            )

        p_refs = _require_str_tuple(
            self.proof_refs, "proof_refs", S12_INVALID_READINESS_RECORD
        )
        object.__setattr__(self, "proof_refs", p_refs)
        _require_completed_key(
            self.readiness_key, "readiness_key", S12_INVALID_READINESS_RECORD
        )

        expected_hash = canonical_artifact_identity(
            PRE_FINAL_READINESS_RECORD_SCHEMA,
            identity_payload={
                "readiness_id": self.readiness_id,
                "bundle_id": self.bundle_id,
                "evaluation_protocol_id": self.evaluation_protocol_id,
                "schema_valid": str(self.schema_valid),
                "artifact_identity_valid": str(self.artifact_identity_valid),
                "dependency_closure_valid": str(self.dependency_closure_valid),
                "synthetic_dry_run_valid": str(self.synthetic_dry_run_valid),
                "protected_final_outcomes_accessed": str(
                    self.protected_final_outcomes_accessed
                ),
                "readiness_result": self.readiness_result,
                "proof_refs": _serialize_seq(p_refs),
                "readiness_key": self.readiness_key,
            },
        )
        if self.readiness_hash != expected_hash:
            raise SchemaViolation(
                f"{S12_INVALID_READINESS_RECORD}: readiness_hash mismatch"
            )

    @classmethod
    def create(
        cls,
        *,
        readiness_id: str,
        frozen_bundle: FrozenRepresentationBundle,
        protocol: EvaluationProtocolArtifact,
        schema_valid: bool = True,
        artifact_identity_valid: bool = True,
        synthetic_dry_run_valid: bool = True,
        protected_final_outcomes_accessed: bool = False,
        proof_refs: Sequence[str] = ("SYNTHETIC_DRY_RUN_PROOF_V1",),
        readiness_key: InformationKey,
    ) -> "PreFinalReadinessRecord":
        closure_ok = verify_final_protocol_bundle_closure(
            protocol, frozen_bundle=frozen_bundle
        )
        all_ok = (
            schema_valid
            and artifact_identity_valid
            and closure_ok
            and synthetic_dry_run_valid
            and not protected_final_outcomes_accessed
        )
        res_str = (
            READINESS_RESULT_READY if all_ok else READINESS_RESULT_FAILED
        )
        p_refs = _require_str_tuple(
            proof_refs, "proof_refs", S12_INVALID_READINESS_RECORD
        )
        r_hash = canonical_artifact_identity(
            PRE_FINAL_READINESS_RECORD_SCHEMA,
            identity_payload={
                "readiness_id": readiness_id,
                "bundle_id": frozen_bundle.bundle_id,
                "evaluation_protocol_id": protocol.evaluation_protocol_id,
                "schema_valid": str(schema_valid),
                "artifact_identity_valid": str(artifact_identity_valid),
                "dependency_closure_valid": str(closure_ok),
                "synthetic_dry_run_valid": str(synthetic_dry_run_valid),
                "protected_final_outcomes_accessed": str(
                    protected_final_outcomes_accessed
                ),
                "readiness_result": res_str,
                "proof_refs": _serialize_seq(p_refs),
                "readiness_key": readiness_key,
            },
        )
        return cls(
            readiness_id=readiness_id,
            bundle_id=frozen_bundle.bundle_id,
            evaluation_protocol_id=protocol.evaluation_protocol_id,
            schema_valid=schema_valid,
            artifact_identity_valid=artifact_identity_valid,
            dependency_closure_valid=closure_ok,
            synthetic_dry_run_valid=synthetic_dry_run_valid,
            protected_final_outcomes_accessed=protected_final_outcomes_accessed,
            readiness_result=res_str,
            proof_refs=p_refs,
            readiness_key=readiness_key,
            readiness_hash=r_hash,
        )


@dataclass(frozen=True)
class GateG3OpenFinalAuthorizationDecision(ImmutableRecord):
    """Gate G3 authorization record to open FINAL evaluation (D2-19, D2-22, Correction-1 Δ5, I-PFR-1)."""

    decision_id: str
    bundle_id: str
    evaluation_protocol_id: str
    readiness_hash: str
    owner_opening_authorization_ref: str
    gate_g3_status: str
    decision_key: InformationKey
    decision_hash: str

    def __post_init__(self) -> None:
        for f_name, f_val in (
            ("decision_id", self.decision_id),
            ("bundle_id", self.bundle_id),
            ("evaluation_protocol_id", self.evaluation_protocol_id),
            ("readiness_hash", self.readiness_hash),
            (
                "owner_opening_authorization_ref",
                self.owner_opening_authorization_ref,
            ),
        ):
            _require_non_empty_str(f_val, f_name, G3_OPEN_FINAL_BLOCKED)
        if self.gate_g3_status != GATE_G3_AUTHORIZED_TO_OPEN:
            raise SchemaViolation(
                f"{G3_OPEN_FINAL_BLOCKED}: invalid gate_g3_status {self.gate_g3_status!r}"
            )
        _require_completed_key(
            self.decision_key, "decision_key", G3_OPEN_FINAL_BLOCKED
        )
        expected_hash = canonical_artifact_identity(
            GATE_G3_AUTHORIZATION_SCHEMA,
            identity_payload={
                "decision_id": self.decision_id,
                "bundle_id": self.bundle_id,
                "evaluation_protocol_id": self.evaluation_protocol_id,
                "readiness_hash": self.readiness_hash,
                "owner_opening_authorization_ref": self.owner_opening_authorization_ref,
                "gate_g3_status": self.gate_g3_status,
                "decision_key": self.decision_key,
            },
        )
        if self.decision_hash != expected_hash:
            raise SchemaViolation(
                f"{G3_OPEN_FINAL_BLOCKED}: decision_hash mismatch"
            )


def evaluate_gate_g3_open_final_authorization(
    *,
    decision_id: str,
    frozen_bundle: FrozenRepresentationBundle,
    protocol: EvaluationProtocolArtifact,
    readiness_record: PreFinalReadinessRecord,
    owner_opening_authorization_ref: Union[str, TypedState],
    event_ledger: EvaluationProtocolEventLedger,
    decision_key: InformationKey,
) -> GateG3OpenFinalAuthorizationDecision:
    """Enforce Gate G3 before opening FINAL evaluation (D2-19, Correction-1 Δ5, I-PFR-1)."""
    if (
        isinstance(owner_opening_authorization_ref, TypedState)
        or not isinstance(owner_opening_authorization_ref, str)
        or not owner_opening_authorization_ref.strip()
    ):
        raise SelectionBlockedError(
            f"{G3_OPEN_FINAL_BLOCKED}: explicit owner_opening_authorization_ref required at Gate G3"
        )
    if not isinstance(readiness_record, PreFinalReadinessRecord):
        raise SelectionBlockedError(
            f"{G3_OPEN_FINAL_BLOCKED}: valid PreFinalReadinessRecord required (I-PFR-1)"
        )
    if readiness_record.readiness_result != READINESS_RESULT_READY:
        raise SelectionBlockedError(
            f"{G3_OPEN_FINAL_BLOCKED}: PreFinalReadinessRecord result is {readiness_record.readiness_result!r}, not READY (Attack 44, I-PFR-1)"
        )
    if (
        readiness_record.bundle_id != frozen_bundle.bundle_id
        or readiness_record.evaluation_protocol_id
        != protocol.evaluation_protocol_id
    ):
        raise SelectionBlockedError(
            f"{G3_OPEN_FINAL_BLOCKED}: readiness_record bundle_id or protocol_id mismatch"
        )
    verify_final_protocol_bundle_closure(
        protocol, frozen_bundle=frozen_bundle
    )
    event_ledger.append_event(
        protocol_id=protocol.evaluation_protocol_id,
        event_type=PROTOCOL_EVENT_OPEN_AUTHORIZED,
        event_information_key=decision_key,
        payload_ref=owner_opening_authorization_ref,
    )
    d_hash = canonical_artifact_identity(
        GATE_G3_AUTHORIZATION_SCHEMA,
        identity_payload={
            "decision_id": decision_id,
            "bundle_id": frozen_bundle.bundle_id,
            "evaluation_protocol_id": protocol.evaluation_protocol_id,
            "readiness_hash": readiness_record.readiness_hash,
            "owner_opening_authorization_ref": owner_opening_authorization_ref,
            "gate_g3_status": GATE_G3_AUTHORIZED_TO_OPEN,
            "decision_key": decision_key,
        },
    )
    return GateG3OpenFinalAuthorizationDecision(
        decision_id=decision_id,
        bundle_id=frozen_bundle.bundle_id,
        evaluation_protocol_id=protocol.evaluation_protocol_id,
        readiness_hash=readiness_record.readiness_hash,
        owner_opening_authorization_ref=owner_opening_authorization_ref,
        gate_g3_status=GATE_G3_AUTHORIZED_TO_OPEN,
        decision_key=decision_key,
        decision_hash=d_hash,
    )


@dataclass(frozen=True)
class EquivalenceClaimArtifact(ImmutableRecord):
    """Claim-scoped EquivalenceClaimArtifact (D2-13, I-EQ-1..4)."""

    claim_id: str
    old_bundle_id: str
    new_bundle_id: str
    evaluation_claim_scope: str
    required_equivalence_dimensions: Tuple[str, ...]
    proven_equivalence_dimensions: Tuple[str, ...]
    proof_refs: Tuple[str, ...]
    equivalence_result: str
    claim_hash: str

    def __post_init__(self) -> None:
        for f_name, f_val in (
            ("claim_id", self.claim_id),
            ("old_bundle_id", self.old_bundle_id),
            ("new_bundle_id", self.new_bundle_id),
            ("evaluation_claim_scope", self.evaluation_claim_scope),
        ):
            _require_non_empty_str(f_val, f_name, S10_INVALID_EQUIVALENCE_CLAIM)

        req_dims = _require_str_tuple(
            self.required_equivalence_dimensions,
            "required_equivalence_dimensions",
            S10_INVALID_EQUIVALENCE_CLAIM,
        )
        prov_dims = _require_str_tuple(
            self.proven_equivalence_dimensions,
            "proven_equivalence_dimensions",
            S10_INVALID_EQUIVALENCE_CLAIM,
            allow_empty=True,
        )
        # I-EQ-1: numeric output equality alone is never sufficient by itself
        if req_dims == (EQ_DIM_SEMANTIC_OUTPUT,):
            raise SchemaViolation(
                f"{S10_INVALID_EQUIVALENCE_CLAIM}: numeric/semantic output equality alone is insufficient (Attack 41, I-EQ-1)"
            )
        p_refs = _require_str_tuple(
            self.proof_refs, "proof_refs", S10_INVALID_EQUIVALENCE_CLAIM
        )
        object.__setattr__(self, "required_equivalence_dimensions", req_dims)
        object.__setattr__(self, "proven_equivalence_dimensions", prov_dims)
        object.__setattr__(self, "proof_refs", p_refs)

        all_proven = set(req_dims).issubset(set(prov_dims))
        if (
            self.equivalence_result == EQUIVALENCE_RESULT_CERTIFIED
            and not all_proven
        ):
            raise SchemaViolation(
                f"{S10_INVALID_EQUIVALENCE_CLAIM}: cannot certify equivalence when required dimensions are unproven (I-EQ-3)"
            )
        if self.equivalence_result not in (
            EQUIVALENCE_RESULT_CERTIFIED,
            EQUIVALENCE_RESULT_REJECTED,
        ):
            raise SchemaViolation(
                f"{S10_INVALID_EQUIVALENCE_CLAIM}: invalid equivalence_result {self.equivalence_result!r}"
            )

        expected_hash = canonical_artifact_identity(
            EQUIVALENCE_CLAIM_ARTIFACT_SCHEMA,
            identity_payload={
                "claim_id": self.claim_id,
                "old_bundle_id": self.old_bundle_id,
                "new_bundle_id": self.new_bundle_id,
                "evaluation_claim_scope": self.evaluation_claim_scope,
                "required_equivalence_dimensions": _serialize_seq(req_dims),
                "proven_equivalence_dimensions": _serialize_seq(prov_dims),
                "proof_refs": _serialize_seq(p_refs),
                "equivalence_result": self.equivalence_result,
            },
        )
        if self.claim_hash != expected_hash:
            raise SchemaViolation(
                f"{S10_INVALID_EQUIVALENCE_CLAIM}: claim_hash mismatch"
            )

    @classmethod
    def create(
        cls,
        *,
        claim_id: str,
        old_bundle_id: str,
        new_bundle_id: str,
        evaluation_claim_scope: str,
        required_equivalence_dimensions: Sequence[str],
        proven_equivalence_dimensions: Sequence[str],
        proof_refs: Sequence[str],
    ) -> "EquivalenceClaimArtifact":
        req_dims = _require_str_tuple(
            required_equivalence_dimensions,
            "required_equivalence_dimensions",
            S10_INVALID_EQUIVALENCE_CLAIM,
        )
        prov_dims = _require_str_tuple(
            proven_equivalence_dimensions,
            "proven_equivalence_dimensions",
            S10_INVALID_EQUIVALENCE_CLAIM,
            allow_empty=True,
        )
        p_refs = _require_str_tuple(
            proof_refs, "proof_refs", S10_INVALID_EQUIVALENCE_CLAIM
        )
        all_proven = set(req_dims).issubset(set(prov_dims))
        res_str = (
            EQUIVALENCE_RESULT_CERTIFIED
            if all_proven
            else EQUIVALENCE_RESULT_REJECTED
        )
        c_hash = canonical_artifact_identity(
            EQUIVALENCE_CLAIM_ARTIFACT_SCHEMA,
            identity_payload={
                "claim_id": claim_id,
                "old_bundle_id": old_bundle_id,
                "new_bundle_id": new_bundle_id,
                "evaluation_claim_scope": evaluation_claim_scope,
                "required_equivalence_dimensions": _serialize_seq(req_dims),
                "proven_equivalence_dimensions": _serialize_seq(prov_dims),
                "proof_refs": _serialize_seq(p_refs),
                "equivalence_result": res_str,
            },
        )
        return cls(
            claim_id=claim_id,
            old_bundle_id=old_bundle_id,
            new_bundle_id=new_bundle_id,
            evaluation_claim_scope=evaluation_claim_scope,
            required_equivalence_dimensions=req_dims,
            proven_equivalence_dimensions=prov_dims,
            proof_refs=p_refs,
            equivalence_result=res_str,
            claim_hash=c_hash,
        )


@dataclass(frozen=True)
class ComparabilitySnapshotSpec(ImmutableRecord):
    """Snapshot comparability envelope (D1-18, D1-19, D2-14, I-CMP-1..2, I-CMPL-1..3, I-MSN-1)."""

    snapshot_id: str
    representation_spec_hash: str
    policy_hash_lineage: str
    descriptor_set_hash: str
    information_key_version: str
    history_boundary_kind: str
    source_semantic_identities: Tuple[str, ...]
    actual_proxy_availability_mask: Tuple[str, ...]
    schema_version: str


@dataclass(frozen=True)
class ComparabilityCheckResult(ImmutableRecord):
    """Three-level comparability verdict (D2-14, I-CMPL-1..3)."""

    comparability_level: str
    reasons: Tuple[str, ...]


def evaluate_snapshot_comparability(
    left: ComparabilitySnapshotSpec,
    right: ComparabilitySnapshotSpec,
    *,
    compatibility_artifact_state: TypedState = TypedState.NOT_CONFIGURED,
) -> ComparabilityCheckResult:
    """Evaluate three-level comparability between two snapshots (D1-18, D1-19, D2-14)."""
    reasons: list[str] = []
    if left.representation_spec_hash != right.representation_spec_hash:
        reasons.append("REPRESENTATION_SPEC_HASH_DIFFERS")
    if left.policy_hash_lineage != right.policy_hash_lineage:
        reasons.append("POLICY_HASH_LINEAGE_DIFFERS")
    if left.descriptor_set_hash != right.descriptor_set_hash:
        reasons.append("DESCRIPTOR_SET_HASH_DIFFERS")
    if left.information_key_version != right.information_key_version:
        reasons.append("INFORMATION_KEY_VERSION_DIFFERS")
    if left.history_boundary_kind != right.history_boundary_kind:
        reasons.append("HISTORY_BOUNDARY_KIND_DIFFERS")
    if tuple(left.source_semantic_identities) != tuple(
        right.source_semantic_identities
    ):
        reasons.append("SOURCE_SEMANTIC_IDENTITIES_DIFFER")
    if tuple(left.actual_proxy_availability_mask) != tuple(
        right.actual_proxy_availability_mask
    ):
        reasons.append("AVAILABILITY_MASK_DIFFERS")
    if left.schema_version != right.schema_version:
        reasons.append("SCHEMA_VERSION_DIFFERS")

    if len(reasons) == 0:
        return ComparabilityCheckResult(
            comparability_level=COMPARABILITY_IDENTICAL_CONTRACT,
            reasons=(),
        )
    # D2-14 / I-CMPL-1: CompatibilityArtifact is NOT IMPLEMENTED; without it, no MAPPED_COMPARABLE
    _ = compatibility_artifact_state
    return ComparabilityCheckResult(
        comparability_level=COMPARABILITY_NOT_COMPARABLE,
        reasons=tuple(reasons),
    )


def compute_comparable_snapshot_distance(
    left: ComparabilitySnapshotSpec,
    right: ComparabilitySnapshotSpec,
    *,
    left_values: Sequence[float],
    right_values: Sequence[float],
) -> float:
    """Compute L1 distance only when snapshots are IDENTICAL_CONTRACT_COMPARABLE (I-CMP-1)."""
    verdict = evaluate_snapshot_comparability(left, right)
    if verdict.comparability_level != COMPARABILITY_IDENTICAL_CONTRACT:
        raise SelectionBlockedError(
            f"{S10_NOT_COMPARABLE_DISTANCE_FORBIDDEN}: distance/similarity forbidden when "
            f"{verdict.comparability_level} ({','.join(verdict.reasons)}) (I-CMP-1)"
        )
    if len(left_values) != len(right_values) or len(left_values) == 0:
        raise SchemaViolation(
            "left_values and right_values must have equal non-zero length"
        )
    return sum(abs(a - b) for a, b in zip(left_values, right_values))


__all__ = [
    "S10_S12_SCHEMA_VERSION",
    "S10_S12_SCHEMA_IDENTITY",
    "FROZEN_REPRESENTATION_BUNDLE_SCHEMA",
    "EVALUATION_PROTOCOL_ARTIFACT_SCHEMA",
    "EVALUATION_PROTOCOL_EVENT_SCHEMA",
    "PRE_FINAL_READINESS_RECORD_SCHEMA",
    "GATE_G3_AUTHORIZATION_SCHEMA",
    "EQUIVALENCE_CLAIM_ARTIFACT_SCHEMA",
    "PROTOCOL_EVENT_RESERVED",
    "PROTOCOL_EVENT_OPEN_AUTHORIZED",
    "PROTOCOL_EVENT_OPENED",
    "PROTOCOL_EVENT_OUTPUT_EMITTED",
    "PROTOCOL_EVENT_EXPLORATORY_OUTPUT_REQUESTED",
    "PROTOCOL_EVENT_INVALIDATED",
    "VALID_PROTOCOL_EVENT_TYPES",
    "READINESS_RESULT_READY",
    "READINESS_RESULT_FAILED",
    "GATE_G3_AUTHORIZED_TO_OPEN",
    "EQ_DIM_SEMANTIC_OUTPUT",
    "EQ_DIM_CAUSAL_VISIBILITY",
    "EQ_DIM_PROVENANCE",
    "EQ_DIM_SELECTION_PROCESS",
    "EQ_DIM_SCHEMA",
    "EQ_DIM_EVALUATION_OUTPUT",
    "EQUIVALENCE_RESULT_CERTIFIED",
    "EQUIVALENCE_RESULT_REJECTED",
    "COMPARABILITY_IDENTICAL_CONTRACT",
    "COMPARABILITY_MAPPED",
    "COMPARABILITY_NOT_COMPARABLE",
    "S10_INVALID_FROZEN_BUNDLE",
    "S11_INVALID_EVALUATION_PROTOCOL",
    "S11_BUNDLE_DEPENDENCY_CLOSURE_MISSING",
    "S11_INVALID_PROTOCOL_EVENT",
    "S11_PROTOCOL_ALREADY_OPENED_FOR_LINEAGE",
    "S12_INVALID_READINESS_RECORD",
    "S12_PROTECTED_FINAL_DATA_USED_IN_READINESS",
    "G3_OPEN_FINAL_BLOCKED",
    "S10_INVALID_EQUIVALENCE_CLAIM",
    "S10_NOT_COMPARABLE_DISTANCE_FORBIDDEN",
    "FrozenRepresentationBundle",
    "EvaluationProtocolArtifact",
    "verify_final_protocol_bundle_closure",
    "EvaluationProtocolEvent",
    "EvaluationProtocolEventLedger",
    "PreFinalReadinessRecord",
    "GateG3OpenFinalAuthorizationDecision",
    "evaluate_gate_g3_open_final_authorization",
    "EquivalenceClaimArtifact",
    "ComparabilitySnapshotSpec",
    "ComparabilityCheckResult",
    "evaluate_snapshot_comparability",
    "compute_comparable_snapshot_distance",
]
