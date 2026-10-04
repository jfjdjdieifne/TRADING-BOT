"""MUF V1 S6: Descriptor Registry, StateCatalogArtifact, and GenericFactualStateGraphSpec.

Implements the causal, Estimand-free factual state-graph and descriptor layer
(D1-6..13, D2-8, D2-9, D2-10, D2-16, D2-22, Correction-1 §4, AP-1 §1, §2, §4):
- ``DescriptorSpec`` & ``DescriptorRegistry`` (D2-16, I-DESC-1..3, I-DE-1)
- ``StateVariableSpec`` & ``StateCatalogArtifact`` (AP-1 §2, I-SCAT-1..3)
- ``GenericFactualStateGraphSpec`` (AP-1 §1, I-GSG-1..4)
- ``WaveRelationRecord`` & relation contracts (D2-9, D2-10, I-DELTA-1..4, I-IKA-1)
- ``FactualStateGraphNodeRecord``, ``CycleSafeGraphClosureRecord``, and
  ``compute_cycle_safe_graph_closure`` (D2-8, I-CLOS-1..3)
- ``CausalDescriptorObservationRecord``, ``CausalStateVariableObservationRecord``,
  ``GenericFactualStateGraphBundle``, ``build_generic_factual_state_graph``, and
  ``query_state_graph_as_of`` (O(N) construction, O(1) per observation)

S6 describes ONLY factual causal market state. It never references Estimand,
InformationObjective, future observables, horizons, or evaluation outcomes.
"""
from dataclasses import dataclass
import math
from typing import Any, Mapping, Optional, Sequence, Tuple, Union

from trading_system.market_understanding.availability import (
    BatchRelation,
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
from trading_system.market_understanding.identity import (
    ArtifactIdentitySchema,
    canonical_artifact_identity,
)
from trading_system.market_understanding.policy_governance import (
    DATASET_ROLE_DEVELOPMENT_FIT,
    DATASET_ROLE_DEVELOPMENT_SELECTION,
    SelectionBlockedError,
)
from trading_system.market_understanding.price_path import (
    EXACT,
    MetricResult,
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
from trading_system.market_understanding.wave_representation import (
    CandidateWaveRepresentationBundle,
    FAMILY_DELTA_EVENT_CONTAINMENT,
    FinalizedWaveGeometryRecord,
)
from trading_system.research.information_time import (
    InformationKey,
    InformationKeyError,
    InformationPhase,
)


S6_SCHEMA_IDENTITY = SchemaIdentity("MUF_S6_STATE_GRAPH", "V1")
S6_SCHEMA_VERSION = "MUF_S6_STATE_GRAPH_V1"

# Descriptor stages (D2-16)
DESCRIPTOR_STAGE_RUNNING_ONLY = "RUNNING_ONLY"
DESCRIPTOR_STAGE_FINAL_ONLY = "FINAL_ONLY"
DESCRIPTOR_STAGE_BOTH_SEPARATE_FORMULAE = "BOTH_SEPARATE_FORMULAE"
LEGAL_DESCRIPTOR_STAGES = frozenset(
    {
        DESCRIPTOR_STAGE_RUNNING_ONLY,
        DESCRIPTOR_STAGE_FINAL_ONLY,
        DESCRIPTOR_STAGE_BOTH_SEPARATE_FORMULAE,
    }
)

# Forbidden future/end tokens inside RUNNING descriptor required_input_refs (D2-16, I-DESC-1..2)
FORBIDDEN_RUNNING_INPUT_SUBSTRINGS = (
    "final_",
    "end_turning_point",
    "wave_end",
    "eventual_",
    "future_",
)

# Forbidden forward-looking / estimand tokens inside S6 generic specs (AP-1 §1, I-GSG-2, I-DESC-3)
FORBIDDEN_GENERIC_GRAPH_SUBSTRINGS = (
    "estimand",
    "information_objective",
    "future_observable",
    "evaluation_result",
    "final_outcome",
)

# Relation types (D2-9, I-DELTA-1..4)
RELATION_ADJACENT_TO = "ADJACENT_TO"
RELATION_ALTERNATES_WITH = "ALTERNATES_WITH"
RELATION_CONTAINS = "CONTAINS"
RELATION_GEOMETRICALLY_COINCIDENT = "GEOMETRICALLY_COINCIDENT"
RELATION_PARTIAL_OVERLAP = "PARTIAL_OVERLAP"
RELATION_GENERAL_REFERENCE = "GENERAL_REFERENCE"
LEGAL_RELATION_TYPES = frozenset(
    {
        RELATION_ADJACENT_TO,
        RELATION_ALTERNATES_WITH,
        RELATION_CONTAINS,
        RELATION_GEOMETRICALLY_COINCIDENT,
        RELATION_PARTIAL_OVERLAP,
        RELATION_GENERAL_REFERENCE,
    }
)

# Delta family standing contracts (D2-9, I-DELTA-3..4)
NON_ALTERNATING_MERGE_RULE_DEFAULT = TypedState.NOT_CONFIGURED
DELTA_CONTAINMENT_HIERARCHY_STANDING_STATUS = (
    "EVENT_ANCHORED_CONTAINMENT_HIERARCHY_CONTRACT_ONLY_NOT_CONFIGURED"
)

# Record types
S6_DESCRIPTOR_OBSERVATION_RECORD_TYPE = "MUF_S6_DESCRIPTOR_OBSERVATION"
S6_STATE_VARIABLE_OBSERVATION_RECORD_TYPE = "MUF_S6_STATE_VARIABLE_OBSERVATION"
S6_WAVE_RELATION_RECORD_TYPE = "MUF_S6_WAVE_RELATION"

# Deterministic S6 error codes
S6_INVALID_DESCRIPTOR_SPEC = "S6_INVALID_DESCRIPTOR_SPEC"
S6_FUTURE_FACT_IN_RUNNING_DESCRIPTOR = "S6_FUTURE_FACT_IN_RUNNING_DESCRIPTOR"
S6_SEPARATE_FORMULAE_REQUIRED = "S6_SEPARATE_FORMULAE_REQUIRED"
S6_DUPLICATE_DESCRIPTOR_REGISTRATION = "S6_DUPLICATE_DESCRIPTOR_REGISTRATION"
S6_UNKNOWN_DESCRIPTOR_REF = "S6_UNKNOWN_DESCRIPTOR_REF"
S6_ESTIMAND_OR_OBJECTIVE_FORBIDDEN_IN_GENERIC_STATE_GRAPH = (
    "S6_ESTIMAND_OR_OBJECTIVE_FORBIDDEN_IN_GENERIC_STATE_GRAPH"
)
S6_INVALID_STATE_VARIABLE_SPEC = "S6_INVALID_STATE_VARIABLE_SPEC"
S6_INVALID_STATE_CATALOG = "S6_INVALID_STATE_CATALOG"
S6_UNDECLARED_CATALOG_REFERENCE = "S6_UNDECLARED_CATALOG_REFERENCE"
S6_INVALID_GENERIC_STATE_GRAPH_SPEC = "S6_INVALID_GENERIC_STATE_GRAPH_SPEC"
S6_INVALID_WAVE_RELATION = "S6_INVALID_WAVE_RELATION"
S6_ALTERNATES_WITH_NOT_ADJACENCY = "S6_ALTERNATES_WITH_NOT_ADJACENCY"
S6_UNPROVEN_CHRONOLOGY_FOR_ADJACENT_TO = (
    "S6_UNPROVEN_CHRONOLOGY_FOR_ADJACENT_TO"
)
S6_DELTA_POPULATED_HIERARCHY_NOT_CONFIGURED = (
    "S6_DELTA_POPULATED_HIERARCHY_NOT_CONFIGURED"
)
S6_ILLEGAL_WAVE_CONTAINMENT_CYCLE = "S6_ILLEGAL_WAVE_CONTAINMENT_CYCLE"
S6_SCALE_DEPTH_COLLAPSE_FORBIDDEN = "S6_SCALE_DEPTH_COLLAPSE_FORBIDDEN"
S6_INVALID_CLOSURE_RECORD = "S6_INVALID_CLOSURE_RECORD"
S6_FINAL_DATASET_FORBIDDEN = "S6_FINAL_DATASET_FORBIDDEN"


DESCRIPTOR_SPEC_SCHEMA = ArtifactIdentitySchema(
    artifact_type="MUF_S6_DESCRIPTOR_SPEC",
    schema_identity=S6_SCHEMA_IDENTITY,
    identity_defining_fields=(
        "descriptor_id",
        "semantic_definition",
        "stage",
        "required_input_refs",
        "availability_rule_ref",
        "denominator_contract",
        "boundary_contract",
        "policy_dependencies",
        "missingness_contract",
        "running_formula_hash",
        "final_formula_hash",
    ),
)

STATE_VARIABLE_SPEC_SCHEMA = ArtifactIdentitySchema(
    artifact_type="MUF_S6_STATE_VARIABLE_SPEC",
    schema_identity=S6_SCHEMA_IDENTITY,
    identity_defining_fields=(
        "variable_id",
        "semantic_definition",
        "value_domain_kind",
        "source_descriptor_refs",
        "source_relation_refs",
        "availability_rule_ref",
        "missingness_semantics_ref",
    ),
)

STATE_CATALOG_SCHEMA = ArtifactIdentitySchema(
    artifact_type="MUF_S6_STATE_CATALOG_ARTIFACT",
    schema_identity=S6_SCHEMA_IDENTITY,
    identity_defining_fields=(
        "state_catalog_id",
        "variable_hashes",
        "descriptor_refs",
        "relation_refs",
        "availability_missingness_semantics",
        "schema_version",
    ),
)

GENERIC_STATE_GRAPH_SPEC_SCHEMA = ArtifactIdentitySchema(
    artifact_type="MUF_S6_GENERIC_FACTUAL_STATE_GRAPH_SPEC",
    schema_identity=S6_SCHEMA_IDENTITY,
    identity_defining_fields=(
        "graph_spec_id",
        "state_catalog_hash",
        "source_contract_hashes",
        "representation_contract_hashes",
        "descriptor_contract_hashes",
        "relation_contract_hashes",
        "missingness_contract_hash",
        "information_key_contract_hash",
        "schema_version",
    ),
)

WAVE_RELATION_SCHEMA = ArtifactIdentitySchema(
    artifact_type="MUF_S6_WAVE_RELATION_RECORD",
    schema_identity=S6_SCHEMA_IDENTITY,
    identity_defining_fields=(
        "relation_type",
        "source_wave_process_id",
        "target_wave_process_id",
        "timeline_id",
        "relation_information_key",
    ),
)

CLOSURE_RECORD_SCHEMA = ArtifactIdentitySchema(
    artifact_type="MUF_S6_CYCLE_SAFE_GRAPH_CLOSURE",
    schema_identity=S6_SCHEMA_IDENTITY,
    identity_defining_fields=(
        "timeline_id",
        "closure_cutoff_key",
        "reachable_node_ids",
        "reachable_relation_ids",
        "general_reference_cycle_detected",
    ),
)


def _require_non_empty_str(val: Any, name: str, err_code: str) -> str:
    if not isinstance(val, str) or not val.strip():
        raise SchemaViolation(f"{err_code}: {name} must be a non-empty string")
    return val


def _require_str_tuple(
    seq: Any, name: str, err_code: str
) -> Tuple[str, ...]:
    if isinstance(seq, (str, bytes)) or not isinstance(seq, Sequence):
        raise SchemaViolation(
            f"{err_code}: {name} must be a sequence of non-empty strings"
        )
    out: list[str] = []
    for idx, item in enumerate(seq):
        out.append(_require_non_empty_str(item, f"{name}[{idx}]", err_code))
    return tuple(out)


def _serialize_seq(items: Sequence[str]) -> Mapping[str, str]:
    return {f"i_{idx}": val for idx, val in enumerate(items)}


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


def _reject_estimand_or_objective_tokens(
    text: str, field_name: str
) -> None:
    lowered = text.lower()
    for bad in FORBIDDEN_GENERIC_GRAPH_SUBSTRINGS:
        if bad in lowered:
            raise SchemaViolation(
                f"{S6_ESTIMAND_OR_OBJECTIVE_FORBIDDEN_IN_GENERIC_STATE_GRAPH}: "
                f"{field_name} references forbidden forward/estimand token {bad!r} (I-GSG-2, I-DESC-3)"
            )


@dataclass(frozen=True)
class DescriptorSpec(ImmutableRecord):
    """Causal wave/path descriptor specification (D2-16, I-DESC-1..3, I-DE-1)."""

    descriptor_id: str
    semantic_definition: str
    stage: str
    required_input_refs: Tuple[str, ...]
    availability_rule_ref: str
    denominator_contract: str
    boundary_contract: str
    policy_dependencies: Tuple[str, ...]
    missingness_contract: str
    running_formula_hash: Union[str, TypedState]
    final_formula_hash: Union[str, TypedState]
    descriptor_hash: str

    def __post_init__(self) -> None:
        _require_non_empty_str(
            self.descriptor_id, "descriptor_id", S6_INVALID_DESCRIPTOR_SPEC
        )
        _require_non_empty_str(
            self.semantic_definition,
            "semantic_definition",
            S6_INVALID_DESCRIPTOR_SPEC,
        )
        _reject_estimand_or_objective_tokens(
            self.descriptor_id, "descriptor_id"
        )
        _reject_estimand_or_objective_tokens(
            self.semantic_definition, "semantic_definition"
        )
        if self.stage not in LEGAL_DESCRIPTOR_STAGES:
            raise SchemaViolation(
                f"{S6_INVALID_DESCRIPTOR_SPEC}: invalid stage {self.stage!r}"
            )
        req_inputs = _require_str_tuple(
            self.required_input_refs,
            "required_input_refs",
            S6_INVALID_DESCRIPTOR_SPEC,
        )
        if len(req_inputs) == 0:
            raise SchemaViolation(
                f"{S6_INVALID_DESCRIPTOR_SPEC}: required_input_refs must be non-empty"
            )
        for inp in req_inputs:
            _reject_estimand_or_objective_tokens(inp, "required_input_refs")
            if self.stage == DESCRIPTOR_STAGE_RUNNING_ONLY:
                low_inp = inp.lower()
                for bad_run in FORBIDDEN_RUNNING_INPUT_SUBSTRINGS:
                    if bad_run in low_inp:
                        raise IllegalCausalReference(
                            f"{S6_FUTURE_FACT_IN_RUNNING_DESCRIPTOR}: RUNNING_ONLY descriptor "
                            f"{self.descriptor_id!r} cannot reference end/final input {inp!r} (I-DESC-1..2)"
                        )
        object.__setattr__(self, "required_input_refs", req_inputs)

        _require_non_empty_str(
            self.availability_rule_ref,
            "availability_rule_ref",
            S6_INVALID_DESCRIPTOR_SPEC,
        )
        _require_non_empty_str(
            self.denominator_contract,
            "denominator_contract",
            S6_INVALID_DESCRIPTOR_SPEC,
        )
        _require_non_empty_str(
            self.boundary_contract,
            "boundary_contract",
            S6_INVALID_DESCRIPTOR_SPEC,
        )
        pol_deps = _require_str_tuple(
            self.policy_dependencies,
            "policy_dependencies",
            S6_INVALID_DESCRIPTOR_SPEC,
        )
        object.__setattr__(self, "policy_dependencies", pol_deps)
        _require_non_empty_str(
            self.missingness_contract,
            "missingness_contract",
            S6_INVALID_DESCRIPTOR_SPEC,
        )

        # Stage formula contract (D2-16)
        if self.stage == DESCRIPTOR_STAGE_RUNNING_ONLY:
            _require_non_empty_str(
                self.running_formula_hash,
                "running_formula_hash",
                S6_INVALID_DESCRIPTOR_SPEC,
            )
            if self.final_formula_hash is not TypedState.NOT_APPLICABLE:
                raise SchemaViolation(
                    f"{S6_INVALID_DESCRIPTOR_SPEC}: RUNNING_ONLY requires "
                    "final_formula_hash = TypedState.NOT_APPLICABLE"
                )
        elif self.stage == DESCRIPTOR_STAGE_FINAL_ONLY:
            if self.running_formula_hash is not TypedState.NOT_APPLICABLE:
                raise SchemaViolation(
                    f"{S6_INVALID_DESCRIPTOR_SPEC}: FINAL_ONLY requires "
                    "running_formula_hash = TypedState.NOT_APPLICABLE"
                )
            _require_non_empty_str(
                self.final_formula_hash,
                "final_formula_hash",
                S6_INVALID_DESCRIPTOR_SPEC,
            )
        else:
            # BOTH_SEPARATE_FORMULAE requires two distinct explicit formula hashes (D2-16)
            r_hash = _require_non_empty_str(
                self.running_formula_hash,
                "running_formula_hash",
                S6_SEPARATE_FORMULAE_REQUIRED,
            )
            f_hash = _require_non_empty_str(
                self.final_formula_hash,
                "final_formula_hash",
                S6_SEPARATE_FORMULAE_REQUIRED,
            )
            if r_hash == f_hash:
                raise SchemaViolation(
                    f"{S6_SEPARATE_FORMULAE_REQUIRED}: BOTH_SEPARATE_FORMULAE requires "
                    "distinct running_formula_hash and final_formula_hash (D2-16)"
                )

        expected_hash = canonical_artifact_identity(
            DESCRIPTOR_SPEC_SCHEMA,
            identity_payload={
                "descriptor_id": self.descriptor_id,
                "semantic_definition": self.semantic_definition,
                "stage": self.stage,
                "required_input_refs": _serialize_seq(req_inputs),
                "availability_rule_ref": self.availability_rule_ref,
                "denominator_contract": self.denominator_contract,
                "boundary_contract": self.boundary_contract,
                "policy_dependencies": _serialize_seq(pol_deps),
                "missingness_contract": self.missingness_contract,
                "running_formula_hash": self.running_formula_hash,
                "final_formula_hash": self.final_formula_hash,
            },
        )
        if self.descriptor_hash != expected_hash:
            raise SchemaViolation(
                f"{S6_INVALID_DESCRIPTOR_SPEC}: descriptor_hash mismatch"
            )

    @classmethod
    def create(
        cls,
        *,
        descriptor_id: str,
        semantic_definition: str,
        stage: str,
        required_input_refs: Sequence[str],
        availability_rule_ref: str,
        denominator_contract: str = "ZERO_DENOMINATOR_RETURNS_UNDEFINED",
        boundary_contract: str = "CLOSED_BAR_CAUSAL_VISIBILITY",
        policy_dependencies: Sequence[str] = (),
        missingness_contract: str = "EXPLICIT_TYPED_STATE",
        running_formula_hash: Union[str, TypedState] = TypedState.NOT_APPLICABLE,
        final_formula_hash: Union[str, TypedState] = TypedState.NOT_APPLICABLE,
    ) -> "DescriptorSpec":
        req_inputs = _require_str_tuple(
            required_input_refs,
            "required_input_refs",
            S6_INVALID_DESCRIPTOR_SPEC,
        )
        pol_deps = _require_str_tuple(
            policy_dependencies,
            "policy_dependencies",
            S6_INVALID_DESCRIPTOR_SPEC,
        )
        d_hash = canonical_artifact_identity(
            DESCRIPTOR_SPEC_SCHEMA,
            identity_payload={
                "descriptor_id": descriptor_id,
                "semantic_definition": semantic_definition,
                "stage": stage,
                "required_input_refs": _serialize_seq(req_inputs),
                "availability_rule_ref": availability_rule_ref,
                "denominator_contract": denominator_contract,
                "boundary_contract": boundary_contract,
                "policy_dependencies": _serialize_seq(pol_deps),
                "missingness_contract": missingness_contract,
                "running_formula_hash": running_formula_hash,
                "final_formula_hash": final_formula_hash,
            },
        )
        return cls(
            descriptor_id=descriptor_id,
            semantic_definition=semantic_definition,
            stage=stage,
            required_input_refs=req_inputs,
            availability_rule_ref=availability_rule_ref,
            denominator_contract=denominator_contract,
            boundary_contract=boundary_contract,
            policy_dependencies=pol_deps,
            missingness_contract=missingness_contract,
            running_formula_hash=running_formula_hash,
            final_formula_hash=final_formula_hash,
            descriptor_hash=d_hash,
        )


class DescriptorRegistry:
    """Append-only registry of causal wave/path DescriptorSpecs (D2-16)."""

    def __init__(self) -> None:
        self.__specs_by_id: dict[str, DescriptorSpec] = {}

    def register(self, spec: DescriptorSpec) -> DescriptorSpec:
        if not isinstance(spec, DescriptorSpec):
            raise SchemaViolation(
                f"{S6_INVALID_DESCRIPTOR_SPEC}: expected DescriptorSpec"
            )
        specs = object.__getattribute__(
            self, "_DescriptorRegistry__specs_by_id"
        )
        if spec.descriptor_id in specs:
            raise ImmutabilityViolation(
                f"{S6_DUPLICATE_DESCRIPTOR_REGISTRATION}: descriptor {spec.descriptor_id!r} already registered"
            )
        specs[spec.descriptor_id] = spec
        return spec

    def get(self, descriptor_id: str) -> DescriptorSpec:
        specs = object.__getattribute__(
            self, "_DescriptorRegistry__specs_by_id"
        )
        if descriptor_id not in specs:
            raise SchemaViolation(
                f"{S6_UNKNOWN_DESCRIPTOR_REF}: unknown descriptor {descriptor_id!r}"
            )
        return specs[descriptor_id]

    def all_specs(self) -> Tuple[DescriptorSpec, ...]:
        specs = object.__getattribute__(
            self, "_DescriptorRegistry__specs_by_id"
        )
        return tuple(specs.values())


@dataclass(frozen=True)
class StateVariableSpec(ImmutableRecord):
    """Factual state-variable specification inside StateCatalogArtifact (AP-1 §2, I-SCAT-1..3)."""

    variable_id: str
    semantic_definition: str
    value_domain_kind: str
    source_descriptor_refs: Tuple[str, ...]
    source_relation_refs: Tuple[str, ...]
    availability_rule_ref: str
    missingness_semantics_ref: str
    variable_hash: str

    def __post_init__(self) -> None:
        _require_non_empty_str(
            self.variable_id, "variable_id", S6_INVALID_STATE_VARIABLE_SPEC
        )
        _require_non_empty_str(
            self.semantic_definition,
            "semantic_definition",
            S6_INVALID_STATE_VARIABLE_SPEC,
        )
        _reject_estimand_or_objective_tokens(self.variable_id, "variable_id")
        _reject_estimand_or_objective_tokens(
            self.semantic_definition, "semantic_definition"
        )
        _require_non_empty_str(
            self.value_domain_kind,
            "value_domain_kind",
            S6_INVALID_STATE_VARIABLE_SPEC,
        )
        d_refs = _require_str_tuple(
            self.source_descriptor_refs,
            "source_descriptor_refs",
            S6_INVALID_STATE_VARIABLE_SPEC,
        )
        r_refs = _require_str_tuple(
            self.source_relation_refs,
            "source_relation_refs",
            S6_INVALID_STATE_VARIABLE_SPEC,
        )
        if len(d_refs) == 0 and len(r_refs) == 0:
            raise SchemaViolation(
                f"{S6_INVALID_STATE_VARIABLE_SPEC}: require at least one source_descriptor_ref or source_relation_ref"
            )
        object.__setattr__(self, "source_descriptor_refs", d_refs)
        object.__setattr__(self, "source_relation_refs", r_refs)
        _require_non_empty_str(
            self.availability_rule_ref,
            "availability_rule_ref",
            S6_INVALID_STATE_VARIABLE_SPEC,
        )
        _require_non_empty_str(
            self.missingness_semantics_ref,
            "missingness_semantics_ref",
            S6_INVALID_STATE_VARIABLE_SPEC,
        )

        expected_hash = canonical_artifact_identity(
            STATE_VARIABLE_SPEC_SCHEMA,
            identity_payload={
                "variable_id": self.variable_id,
                "semantic_definition": self.semantic_definition,
                "value_domain_kind": self.value_domain_kind,
                "source_descriptor_refs": _serialize_seq(d_refs),
                "source_relation_refs": _serialize_seq(r_refs),
                "availability_rule_ref": self.availability_rule_ref,
                "missingness_semantics_ref": self.missingness_semantics_ref,
            },
        )
        if self.variable_hash != expected_hash:
            raise SchemaViolation(
                f"{S6_INVALID_STATE_VARIABLE_SPEC}: variable_hash mismatch"
            )

    @classmethod
    def create(
        cls,
        *,
        variable_id: str,
        semantic_definition: str,
        value_domain_kind: str,
        source_descriptor_refs: Sequence[str] = (),
        source_relation_refs: Sequence[str] = (),
        availability_rule_ref: str = "EARLIEST_LAWFUL_DESCRIPTOR_VISIBILITY",
        missingness_semantics_ref: str = "EXPLICIT_TYPED_STATE",
    ) -> "StateVariableSpec":
        d_refs = _require_str_tuple(
            source_descriptor_refs,
            "source_descriptor_refs",
            S6_INVALID_STATE_VARIABLE_SPEC,
        )
        r_refs = _require_str_tuple(
            source_relation_refs,
            "source_relation_refs",
            S6_INVALID_STATE_VARIABLE_SPEC,
        )
        v_hash = canonical_artifact_identity(
            STATE_VARIABLE_SPEC_SCHEMA,
            identity_payload={
                "variable_id": variable_id,
                "semantic_definition": semantic_definition,
                "value_domain_kind": value_domain_kind,
                "source_descriptor_refs": _serialize_seq(d_refs),
                "source_relation_refs": _serialize_seq(r_refs),
                "availability_rule_ref": availability_rule_ref,
                "missingness_semantics_ref": missingness_semantics_ref,
            },
        )
        return cls(
            variable_id=variable_id,
            semantic_definition=semantic_definition,
            value_domain_kind=value_domain_kind,
            source_descriptor_refs=d_refs,
            source_relation_refs=r_refs,
            availability_rule_ref=availability_rule_ref,
            missingness_semantics_ref=missingness_semantics_ref,
            variable_hash=v_hash,
        )


@dataclass(frozen=True)
class StateCatalogArtifact(ImmutableRecord):
    """Generic factual StateCatalogArtifact preceding any Estimand (AP-1 §2, I-SCAT-1..3)."""

    state_catalog_id: str
    variable_specs: Tuple[StateVariableSpec, ...]
    descriptor_refs: Tuple[str, ...]
    relation_refs: Tuple[str, ...]
    availability_missingness_semantics: str
    schema_version: str
    state_catalog_hash: str

    def __post_init__(self) -> None:
        _require_non_empty_str(
            self.state_catalog_id, "state_catalog_id", S6_INVALID_STATE_CATALOG
        )
        _reject_estimand_or_objective_tokens(
            self.state_catalog_id, "state_catalog_id"
        )
        if not isinstance(self.variable_specs, Sequence) or len(self.variable_specs) == 0:
            raise SchemaViolation(
                f"{S6_INVALID_STATE_CATALOG}: variable_specs must be non-empty"
            )
        var_tuple = tuple(self.variable_specs)
        object.__setattr__(self, "variable_specs", var_tuple)

        d_refs = _require_str_tuple(
            self.descriptor_refs, "descriptor_refs", S6_INVALID_STATE_CATALOG
        )
        r_refs = _require_str_tuple(
            self.relation_refs, "relation_refs", S6_INVALID_STATE_CATALOG
        )
        object.__setattr__(self, "descriptor_refs", d_refs)
        object.__setattr__(self, "relation_refs", r_refs)

        d_set = set(d_refs)
        r_set = set(r_refs)
        seen_vars: set[str] = set()
        var_hashes: list[str] = []
        for vs in var_tuple:
            if not isinstance(vs, StateVariableSpec):
                raise SchemaViolation(
                    f"{S6_INVALID_STATE_CATALOG}: variable_specs must contain StateVariableSpec"
                )
            if vs.variable_id in seen_vars:
                raise SchemaViolation(
                    f"{S6_INVALID_STATE_CATALOG}: duplicate variable_id {vs.variable_id!r}"
                )
            seen_vars.add(vs.variable_id)
            for dr in vs.source_descriptor_refs:
                if dr not in d_set:
                    raise SchemaViolation(
                        f"{S6_UNDECLARED_CATALOG_REFERENCE}: variable {vs.variable_id!r} references "
                        f"undeclared descriptor_ref {dr!r} (I-SCAT-1)"
                    )
            for rr in vs.source_relation_refs:
                if rr not in r_set:
                    raise SchemaViolation(
                        f"{S6_UNDECLARED_CATALOG_REFERENCE}: variable {vs.variable_id!r} references "
                        f"undeclared relation_ref {rr!r} (I-SCAT-1)"
                    )
            var_hashes.append(vs.variable_hash)

        _require_non_empty_str(
            self.availability_missingness_semantics,
            "availability_missingness_semantics",
            S6_INVALID_STATE_CATALOG,
        )
        _require_non_empty_str(
            self.schema_version, "schema_version", S6_INVALID_STATE_CATALOG
        )

        expected_hash = canonical_artifact_identity(
            STATE_CATALOG_SCHEMA,
            identity_payload={
                "state_catalog_id": self.state_catalog_id,
                "variable_hashes": _serialize_seq(var_hashes),
                "descriptor_refs": _serialize_seq(d_refs),
                "relation_refs": _serialize_seq(r_refs),
                "availability_missingness_semantics": self.availability_missingness_semantics,
                "schema_version": self.schema_version,
            },
        )
        if self.state_catalog_hash != expected_hash:
            raise SchemaViolation(
                f"{S6_INVALID_STATE_CATALOG}: state_catalog_hash mismatch"
            )

    @classmethod
    def create(
        cls,
        *,
        state_catalog_id: str,
        variable_specs: Sequence[StateVariableSpec],
        descriptor_refs: Sequence[str],
        relation_refs: Sequence[str],
        availability_missingness_semantics: str = "EXPLICIT_TYPED_STATE_NO_SILENT_DROP",
        schema_version: str = S6_SCHEMA_VERSION,
    ) -> "StateCatalogArtifact":
        var_tuple = tuple(variable_specs)
        d_refs = _require_str_tuple(
            descriptor_refs, "descriptor_refs", S6_INVALID_STATE_CATALOG
        )
        r_refs = _require_str_tuple(
            relation_refs, "relation_refs", S6_INVALID_STATE_CATALOG
        )
        var_hashes = [
            vs.variable_hash
            for vs in var_tuple
            if isinstance(vs, StateVariableSpec)
        ]
        c_hash = canonical_artifact_identity(
            STATE_CATALOG_SCHEMA,
            identity_payload={
                "state_catalog_id": state_catalog_id,
                "variable_hashes": _serialize_seq(var_hashes),
                "descriptor_refs": _serialize_seq(d_refs),
                "relation_refs": _serialize_seq(r_refs),
                "availability_missingness_semantics": availability_missingness_semantics,
                "schema_version": schema_version,
            },
        )
        return cls(
            state_catalog_id=state_catalog_id,
            variable_specs=var_tuple,
            descriptor_refs=d_refs,
            relation_refs=r_refs,
            availability_missingness_semantics=availability_missingness_semantics,
            schema_version=schema_version,
            state_catalog_hash=c_hash,
        )


@dataclass(frozen=True)
class GenericFactualStateGraphSpec(ImmutableRecord):
    """Generic Factual State Graph Specification (AP-1 §1, I-GSG-1..4)."""

    graph_spec_id: str
    state_catalog_hash: str
    source_contract_hashes: Tuple[str, ...]
    representation_contract_hashes: Tuple[str, ...]
    descriptor_contract_hashes: Tuple[str, ...]
    relation_contract_hashes: Tuple[str, ...]
    missingness_contract_hash: str
    information_key_contract_hash: str
    schema_version: str
    graph_spec_hash: str

    def __post_init__(self) -> None:
        _require_non_empty_str(
            self.graph_spec_id,
            "graph_spec_id",
            S6_INVALID_GENERIC_STATE_GRAPH_SPEC,
        )
        _reject_estimand_or_objective_tokens(
            self.graph_spec_id, "graph_spec_id"
        )
        _require_non_empty_str(
            self.state_catalog_hash,
            "state_catalog_hash",
            S6_INVALID_GENERIC_STATE_GRAPH_SPEC,
        )
        src_h = _require_str_tuple(
            self.source_contract_hashes,
            "source_contract_hashes",
            S6_INVALID_GENERIC_STATE_GRAPH_SPEC,
        )
        rep_h = _require_str_tuple(
            self.representation_contract_hashes,
            "representation_contract_hashes",
            S6_INVALID_GENERIC_STATE_GRAPH_SPEC,
        )
        desc_h = _require_str_tuple(
            self.descriptor_contract_hashes,
            "descriptor_contract_hashes",
            S6_INVALID_GENERIC_STATE_GRAPH_SPEC,
        )
        rel_h = _require_str_tuple(
            self.relation_contract_hashes,
            "relation_contract_hashes",
            S6_INVALID_GENERIC_STATE_GRAPH_SPEC,
        )
        if len(rep_h) == 0 or len(desc_h) == 0:
            raise SchemaViolation(
                f"{S6_INVALID_GENERIC_STATE_GRAPH_SPEC}: representation and descriptor contract hashes must be non-empty"
            )
        for seq_name, seq_vals in (
            ("source_contract_hashes", src_h),
            ("representation_contract_hashes", rep_h),
            ("descriptor_contract_hashes", desc_h),
            ("relation_contract_hashes", rel_h),
        ):
            for item in seq_vals:
                _reject_estimand_or_objective_tokens(item, seq_name)
        object.__setattr__(self, "source_contract_hashes", src_h)
        object.__setattr__(self, "representation_contract_hashes", rep_h)
        object.__setattr__(self, "descriptor_contract_hashes", desc_h)
        object.__setattr__(self, "relation_contract_hashes", rel_h)

        _require_non_empty_str(
            self.missingness_contract_hash,
            "missingness_contract_hash",
            S6_INVALID_GENERIC_STATE_GRAPH_SPEC,
        )
        _require_non_empty_str(
            self.information_key_contract_hash,
            "information_key_contract_hash",
            S6_INVALID_GENERIC_STATE_GRAPH_SPEC,
        )
        _require_non_empty_str(
            self.schema_version,
            "schema_version",
            S6_INVALID_GENERIC_STATE_GRAPH_SPEC,
        )

        expected_hash = canonical_artifact_identity(
            GENERIC_STATE_GRAPH_SPEC_SCHEMA,
            identity_payload={
                "graph_spec_id": self.graph_spec_id,
                "state_catalog_hash": self.state_catalog_hash,
                "source_contract_hashes": _serialize_seq(src_h),
                "representation_contract_hashes": _serialize_seq(rep_h),
                "descriptor_contract_hashes": _serialize_seq(desc_h),
                "relation_contract_hashes": _serialize_seq(rel_h),
                "missingness_contract_hash": self.missingness_contract_hash,
                "information_key_contract_hash": self.information_key_contract_hash,
                "schema_version": self.schema_version,
            },
        )
        if self.graph_spec_hash != expected_hash:
            raise SchemaViolation(
                f"{S6_INVALID_GENERIC_STATE_GRAPH_SPEC}: graph_spec_hash mismatch"
            )

    @classmethod
    def create(
        cls,
        *,
        graph_spec_id: str,
        state_catalog: StateCatalogArtifact,
        source_contract_hashes: Sequence[str],
        representation_contract_hashes: Sequence[str],
        descriptor_contract_hashes: Sequence[str],
        relation_contract_hashes: Sequence[str],
        missingness_contract_hash: str = "MISSINGNESS_EXPLICIT_TYPED_STATE_V1",
        information_key_contract_hash: str = "INFORMATION_KEY_CAUSAL_V1",
        schema_version: str = S6_SCHEMA_VERSION,
    ) -> "GenericFactualStateGraphSpec":
        if not isinstance(state_catalog, StateCatalogArtifact):
            raise SchemaViolation(
                f"{S6_INVALID_GENERIC_STATE_GRAPH_SPEC}: state_catalog must be a StateCatalogArtifact"
            )
        src_h = _require_str_tuple(
            source_contract_hashes,
            "source_contract_hashes",
            S6_INVALID_GENERIC_STATE_GRAPH_SPEC,
        )
        rep_h = _require_str_tuple(
            representation_contract_hashes,
            "representation_contract_hashes",
            S6_INVALID_GENERIC_STATE_GRAPH_SPEC,
        )
        desc_h = _require_str_tuple(
            descriptor_contract_hashes,
            "descriptor_contract_hashes",
            S6_INVALID_GENERIC_STATE_GRAPH_SPEC,
        )
        rel_h = _require_str_tuple(
            relation_contract_hashes,
            "relation_contract_hashes",
            S6_INVALID_GENERIC_STATE_GRAPH_SPEC,
        )
        g_hash = canonical_artifact_identity(
            GENERIC_STATE_GRAPH_SPEC_SCHEMA,
            identity_payload={
                "graph_spec_id": graph_spec_id,
                "state_catalog_hash": state_catalog.state_catalog_hash,
                "source_contract_hashes": _serialize_seq(src_h),
                "representation_contract_hashes": _serialize_seq(rep_h),
                "descriptor_contract_hashes": _serialize_seq(desc_h),
                "relation_contract_hashes": _serialize_seq(rel_h),
                "missingness_contract_hash": missingness_contract_hash,
                "information_key_contract_hash": information_key_contract_hash,
                "schema_version": schema_version,
            },
        )
        return cls(
            graph_spec_id=graph_spec_id,
            state_catalog_hash=state_catalog.state_catalog_hash,
            source_contract_hashes=src_h,
            representation_contract_hashes=rep_h,
            descriptor_contract_hashes=desc_h,
            relation_contract_hashes=rel_h,
            missingness_contract_hash=missingness_contract_hash,
            information_key_contract_hash=information_key_contract_hash,
            schema_version=schema_version,
            graph_spec_hash=g_hash,
        )


@dataclass(frozen=True)
class FactualStateGraphNodeRecord(ImmutableRecord):
    """Factual node in the generic state graph enforcing Scale != Depth (D1-6, I-SD-1..4)."""

    node_id: str
    timeline_id: str
    node_availability_key: InformationKey
    intrinsic_scale_key: Union[str, TypedState]
    containment_depth: Union[int, TypedState]

    def __post_init__(self) -> None:
        _require_non_empty_str(self.node_id, "node_id", S6_INVALID_WAVE_RELATION)
        _require_non_empty_str(
            self.timeline_id, "timeline_id", S6_INVALID_WAVE_RELATION
        )
        _require_completed_key(
            self.node_availability_key,
            "node_availability_key",
            S6_INVALID_WAVE_RELATION,
        )
        if self.node_availability_key.timeline_id != self.timeline_id:
            raise InformationKeyViolation(
                f"{S6_INVALID_WAVE_RELATION}: node_availability_key timeline mismatch"
            )
        if self.intrinsic_scale_key is not TypedState.NOT_APPLICABLE:
            _require_non_empty_str(
                self.intrinsic_scale_key,
                "intrinsic_scale_key",
                S6_INVALID_WAVE_RELATION,
            )
        if self.containment_depth is not TypedState.NOT_APPLICABLE:
            if (
                isinstance(self.containment_depth, bool)
                or not isinstance(self.containment_depth, int)
                or self.containment_depth < 0
            ):
                raise SchemaViolation(
                    f"{S6_SCALE_DEPTH_COLLAPSE_FORBIDDEN}: containment_depth must be non-negative int or NOT_APPLICABLE (I-SD-1)"
                )


@dataclass(frozen=True)
class WaveRelationRecord(ImmutableRecord):
    """Causal relation edge between two wave/state nodes (D2-9, D2-10, I-DELTA-1..4, I-IKA-1)."""

    relation_id: str
    relation_type: str
    source_wave_process_id: str
    target_wave_process_id: str
    timeline_id: str
    source_availability_key: InformationKey
    target_availability_key: InformationKey
    relation_information_key: InformationKey
    batch_relation: BatchRelation
    used_for_adjacency_or_parent: bool
    published_record: PublishedRecord

    def __post_init__(self) -> None:
        _require_non_empty_str(
            self.relation_id, "relation_id", S6_INVALID_WAVE_RELATION
        )
        if self.relation_type not in LEGAL_RELATION_TYPES:
            raise SchemaViolation(
                f"{S6_INVALID_WAVE_RELATION}: invalid relation_type {self.relation_type!r}"
            )
        _require_non_empty_str(
            self.source_wave_process_id,
            "source_wave_process_id",
            S6_INVALID_WAVE_RELATION,
        )
        _require_non_empty_str(
            self.target_wave_process_id,
            "target_wave_process_id",
            S6_INVALID_WAVE_RELATION,
        )
        _require_non_empty_str(
            self.timeline_id, "timeline_id", S6_INVALID_WAVE_RELATION
        )
        _require_completed_key(
            self.source_availability_key,
            "source_availability_key",
            S6_INVALID_WAVE_RELATION,
        )
        _require_completed_key(
            self.target_availability_key,
            "target_availability_key",
            S6_INVALID_WAVE_RELATION,
        )
        _require_completed_key(
            self.relation_information_key,
            "relation_information_key",
            S6_INVALID_WAVE_RELATION,
        )
        if (
            self.source_availability_key.timeline_id != self.timeline_id
            or self.target_availability_key.timeline_id != self.timeline_id
            or self.relation_information_key.timeline_id != self.timeline_id
        ):
            raise InformationKeyViolation(
                f"{S6_INVALID_WAVE_RELATION}: timeline mismatch on WaveRelationRecord"
            )
        require_visible_at(
            fact_key=self.source_availability_key,
            at_key=self.relation_information_key,
        )
        require_visible_at(
            fact_key=self.target_availability_key,
            at_key=self.relation_information_key,
        )
        if not isinstance(self.batch_relation, BatchRelation):
            raise SchemaViolation(
                f"{S6_INVALID_WAVE_RELATION}: batch_relation must be a BatchRelation"
            )

        # I-DELTA-1: ALTERNATES_WITH is never adjacency or parent containment
        if (
            self.relation_type == RELATION_ALTERNATES_WITH
            and self.used_for_adjacency_or_parent
        ):
            raise SchemaViolation(
                f"{S6_ALTERNATES_WITH_NOT_ADJACENCY}: ALTERNATES_WITH cannot be used "
                "as adjacency or parent containment (D2-9, I-DELTA-1)"
            )

        # I-DELTA-2: ADJACENT_TO requires proven different batch chronology (source < target)
        if self.relation_type == RELATION_ADJACENT_TO:
            if self.batch_relation is not BatchRelation.DIFFERENT_BATCH:
                raise SchemaViolation(
                    f"{S6_UNPROVEN_CHRONOLOGY_FOR_ADJACENT_TO}: directed ADJACENT_TO "
                    f"forbidden under batch_relation={self.batch_relation.value!r} (D2-9, I-DELTA-2)"
                )

        if (
            self.relation_type == RELATION_CONTAINS
            and self.source_wave_process_id == self.target_wave_process_id
        ):
            raise SchemaViolation(
                f"{S6_ILLEGAL_WAVE_CONTAINMENT_CYCLE}: self-containment forbidden"
            )

        expected_id = canonical_artifact_identity(
            WAVE_RELATION_SCHEMA,
            identity_payload={
                "relation_type": self.relation_type,
                "source_wave_process_id": self.source_wave_process_id,
                "target_wave_process_id": self.target_wave_process_id,
                "timeline_id": self.timeline_id,
                "relation_information_key": self.relation_information_key,
            },
        )
        if self.relation_id != expected_id:
            raise SchemaViolation(
                f"{S6_INVALID_WAVE_RELATION}: relation_id mismatch"
            )
        if (
            not isinstance(self.published_record, PublishedRecord)
            or self.published_record.record_type != S6_WAVE_RELATION_RECORD_TYPE
            or self.published_record.record_identity != self.relation_id
            or self.published_record.availability_key
            != self.relation_information_key
        ):
            raise SchemaViolation(
                f"{S6_INVALID_WAVE_RELATION}: published_record mismatch"
            )

    @classmethod
    def create(
        cls,
        *,
        relation_type: str,
        source_wave_process_id: str,
        target_wave_process_id: str,
        timeline_id: str,
        source_availability_key: InformationKey,
        target_availability_key: InformationKey,
        batch_relation: BatchRelation = BatchRelation.DIFFERENT_BATCH,
        used_for_adjacency_or_parent: bool = False,
    ) -> "WaveRelationRecord":
        rel_key = (
            source_availability_key
            if target_availability_key <= source_availability_key
            else target_availability_key
        )
        rel_id = canonical_artifact_identity(
            WAVE_RELATION_SCHEMA,
            identity_payload={
                "relation_type": relation_type,
                "source_wave_process_id": source_wave_process_id,
                "target_wave_process_id": target_wave_process_id,
                "timeline_id": timeline_id,
                "relation_information_key": rel_key,
            },
        )
        pub = PublishedRecord(
            record_type=S6_WAVE_RELATION_RECORD_TYPE,
            record_identity=rel_id,
            schema_identity=S6_SCHEMA_IDENTITY,
            timeline_id=timeline_id,
            availability_key=rel_key,
            content={
                "relation_id": rel_id,
                "relation_type": relation_type,
                "source_wave_process_id": source_wave_process_id,
                "target_wave_process_id": target_wave_process_id,
            },
        )
        return cls(
            relation_id=rel_id,
            relation_type=relation_type,
            source_wave_process_id=source_wave_process_id,
            target_wave_process_id=target_wave_process_id,
            timeline_id=timeline_id,
            source_availability_key=source_availability_key,
            target_availability_key=target_availability_key,
            relation_information_key=rel_key,
            batch_relation=batch_relation,
            used_for_adjacency_or_parent=used_for_adjacency_or_parent,
            published_record=pub,
        )


@dataclass(frozen=True)
class CycleSafeGraphClosureRecord(ImmutableRecord):
    """Deterministic cycle-safe causal snapshot closure (D2-8, I-CLOS-1..3)."""

    timeline_id: str
    closure_cutoff_key: InformationKey
    reachable_node_ids: Tuple[str, ...]
    reachable_relation_ids: Tuple[str, ...]
    general_reference_cycle_detected: bool
    closure_hash: str

    def __post_init__(self) -> None:
        _require_non_empty_str(
            self.timeline_id, "timeline_id", S6_INVALID_CLOSURE_RECORD
        )
        _require_completed_key(
            self.closure_cutoff_key,
            "closure_cutoff_key",
            S6_INVALID_CLOSURE_RECORD,
        )
        nodes = _require_str_tuple(
            self.reachable_node_ids,
            "reachable_node_ids",
            S6_INVALID_CLOSURE_RECORD,
        )
        rels = _require_str_tuple(
            self.reachable_relation_ids,
            "reachable_relation_ids",
            S6_INVALID_CLOSURE_RECORD,
        )
        object.__setattr__(self, "reachable_node_ids", nodes)
        object.__setattr__(self, "reachable_relation_ids", rels)

        expected_hash = canonical_artifact_identity(
            CLOSURE_RECORD_SCHEMA,
            identity_payload={
                "timeline_id": self.timeline_id,
                "closure_cutoff_key": self.closure_cutoff_key,
                "reachable_node_ids": _serialize_seq(nodes),
                "reachable_relation_ids": _serialize_seq(rels),
                "general_reference_cycle_detected": str(
                    self.general_reference_cycle_detected
                ),
            },
        )
        if self.closure_hash != expected_hash:
            raise SchemaViolation(
                f"{S6_INVALID_CLOSURE_RECORD}: closure_hash mismatch"
            )


def compute_cycle_safe_graph_closure(
    nodes: Sequence[FactualStateGraphNodeRecord],
    relations: Sequence[WaveRelationRecord],
    *,
    seed_node_ids: Sequence[str],
    at_key: InformationKey,
) -> CycleSafeGraphClosureRecord:
    """Compute deterministic cycle-safe snapshot closure at ``at_key`` (D2-8, I-CLOS-1..3).

    - Rejects any CONTAINS cycle with ``S6_ILLEGAL_WAVE_CONTAINMENT_CYCLE``.
    - Traverses GENERAL_REFERENCE cycles safely once per node without infinite recursion (I-CLOS-1).
    - Validates ``availability_key <= at_key`` for every reachable node and relation (I-CLOS-2).
    - Produces canonical ``closure_hash`` independent of input insertion order (I-CLOS-3).
    """
    _require_completed_key(at_key, "at_key", S6_INVALID_CLOSURE_RECORD)
    node_map: dict[str, FactualStateGraphNodeRecord] = {}
    for n in nodes:
        if not isinstance(n, FactualStateGraphNodeRecord):
            raise SchemaViolation("nodes must contain FactualStateGraphNodeRecord")
        if n.timeline_id != at_key.timeline_id:
            raise InformationKeyViolation("node timeline mismatch with at_key")
        node_map[n.node_id] = n

    # Check CONTAINS relations for cycles via deterministic DFS
    contains_adj: dict[str, list[str]] = {}
    outgoing_by_node: dict[str, list[WaveRelationRecord]] = {}
    for rel in relations:
        if not isinstance(rel, WaveRelationRecord):
            raise SchemaViolation("relations must contain WaveRelationRecord")
        if rel.timeline_id != at_key.timeline_id:
            raise InformationKeyViolation("relation timeline mismatch with at_key")
        outgoing_by_node.setdefault(rel.source_wave_process_id, []).append(rel)
        if rel.relation_type == RELATION_CONTAINS:
            contains_adj.setdefault(rel.source_wave_process_id, []).append(
                rel.target_wave_process_id
            )

    # Sort adjacency lists for canonical traversal (I-CLOS-3)
    for k_id in contains_adj:
        contains_adj[k_id].sort()
    for k_id in outgoing_by_node:
        outgoing_by_node[k_id].sort(key=lambda r: r.relation_id)

    visit_state: dict[str, int] = {}
    for start_id in sorted(contains_adj.keys()):
        if visit_state.get(start_id, 0) != 0:
            continue
        stack: list[Tuple[str, int]] = [(start_id, 0)]
        visit_state[start_id] = 1
        while len(stack) > 0:
            curr_id, child_idx = stack[-1]
            children = contains_adj.get(curr_id, [])
            if child_idx < len(children):
                stack[-1] = (curr_id, child_idx + 1)
                nxt = children[child_idx]
                st = visit_state.get(nxt, 0)
                if st == 1:
                    raise SchemaViolation(
                        f"{S6_ILLEGAL_WAVE_CONTAINMENT_CYCLE}: cycle detected in CONTAINS graph at {nxt!r} (D2-8)"
                    )
                if st == 0:
                    visit_state[nxt] = 1
                    stack.append((nxt, 0))
            else:
                visit_state[curr_id] = -1
                stack.pop()

    # Deterministic BFS/DFS reachability from sorted seed_node_ids with cycle detection
    visited_nodes: set[str] = set()
    active_path: set[str] = set()
    reachable_rels: set[str] = set()
    gen_cycle_found = False

    def _dfs(u_id: str) -> None:
        nonlocal gen_cycle_found
        if u_id not in node_map:
            raise SchemaViolation(f"unknown node_id {u_id!r} in graph closure")
        u_node = node_map[u_id]
        # I-CLOS-2: cycle never bypasses availability validation
        require_visible_at(fact_key=u_node.node_availability_key, at_key=at_key)
        visited_nodes.add(u_id)
        active_path.add(u_id)
        for rel in outgoing_by_node.get(u_id, []):
            require_visible_at(
                fact_key=rel.relation_information_key, at_key=at_key
            )
            reachable_rels.add(rel.relation_id)
            v_id = rel.target_wave_process_id
            if v_id in active_path:
                gen_cycle_found = True
            elif v_id not in visited_nodes:
                _dfs(v_id)
            else:
                # Ensure target node availability is validated
                require_visible_at(
                    fact_key=node_map[v_id].node_availability_key, at_key=at_key
                )
        active_path.remove(u_id)

    for s_id in sorted(set(seed_node_ids)):
        if s_id not in visited_nodes:
            _dfs(s_id)

    sorted_nodes = tuple(sorted(visited_nodes))
    sorted_rels = tuple(sorted(reachable_rels))
    c_hash = canonical_artifact_identity(
        CLOSURE_RECORD_SCHEMA,
        identity_payload={
            "timeline_id": at_key.timeline_id,
            "closure_cutoff_key": at_key,
            "reachable_node_ids": _serialize_seq(sorted_nodes),
            "reachable_relation_ids": _serialize_seq(sorted_rels),
            "general_reference_cycle_detected": str(gen_cycle_found),
        },
    )
    return CycleSafeGraphClosureRecord(
        timeline_id=at_key.timeline_id,
        closure_cutoff_key=at_key,
        reachable_node_ids=sorted_nodes,
        reachable_relation_ids=sorted_rels,
        general_reference_cycle_detected=gen_cycle_found,
        closure_hash=c_hash,
    )


@dataclass(frozen=True)
class CausalDescriptorObservationRecord(ImmutableRecord):
    """Causal wave descriptor observation emitted at ``observation_key`` (D2-16, I-DESC-1..3, I-DE-1)."""

    observation_id: str
    wave_process_id: str
    descriptor_id: str
    descriptor_hash: str
    stage: str
    timeline_id: str
    observation_key: InformationKey
    value: Union[MetricResult, TypedState]
    published_record: PublishedRecord

    def __post_init__(self) -> None:
        _require_non_empty_str(
            self.observation_id, "observation_id", S6_INVALID_DESCRIPTOR_SPEC
        )
        _require_non_empty_str(
            self.wave_process_id, "wave_process_id", S6_INVALID_DESCRIPTOR_SPEC
        )
        _require_non_empty_str(
            self.descriptor_id, "descriptor_id", S6_INVALID_DESCRIPTOR_SPEC
        )
        _require_non_empty_str(
            self.descriptor_hash, "descriptor_hash", S6_INVALID_DESCRIPTOR_SPEC
        )
        if self.stage not in (
            DESCRIPTOR_STAGE_RUNNING_ONLY,
            DESCRIPTOR_STAGE_FINAL_ONLY,
        ):
            raise SchemaViolation(
                f"{S6_INVALID_DESCRIPTOR_SPEC}: observation stage must be RUNNING_ONLY or FINAL_ONLY"
            )
        _require_completed_key(
            self.observation_key, "observation_key", S6_INVALID_DESCRIPTOR_SPEC
        )
        if not isinstance(self.value, (MetricResult, TypedState)):
            raise SchemaViolation(
                f"{S6_INVALID_DESCRIPTOR_SPEC}: value must be MetricResult or TypedState"
            )


@dataclass(frozen=True)
class CausalStateVariableObservationRecord(ImmutableRecord):
    """Causal state-variable observation bound to a StateCatalogArtifact variable (AP-1 §2)."""

    state_observation_id: str
    wave_process_id: str
    variable_id: str
    variable_hash: str
    state_catalog_hash: str
    timeline_id: str
    observation_key: InformationKey
    state_value: Union[MetricResult, TypedState, str]


@dataclass(frozen=True)
class GenericFactualStateGraphAsOfView(ImmutableRecord):
    """Causal as-of projection of a GenericFactualStateGraphBundle at ``query_key``."""

    timeline_id: str
    query_key: InformationKey
    graph_spec_hash: str
    state_catalog_hash: str
    visible_nodes: Tuple[FactualStateGraphNodeRecord, ...]
    visible_relations: Tuple[WaveRelationRecord, ...]
    visible_descriptor_observations: Tuple[
        CausalDescriptorObservationRecord, ...
    ]
    visible_state_observations: Tuple[
        CausalStateVariableObservationRecord, ...
    ]
    closure_record: CycleSafeGraphClosureRecord


@dataclass(frozen=True)
class GenericFactualStateGraphBundle(ImmutableRecord):
    """Complete S6 Generic Factual State Graph Bundle over an S5 CandidateWaveRepresentationBundle."""

    graph_spec: GenericFactualStateGraphSpec
    state_catalog: StateCatalogArtifact
    wave_bundle: CandidateWaveRepresentationBundle
    nodes: Tuple[FactualStateGraphNodeRecord, ...]
    relations: Tuple[WaveRelationRecord, ...]
    descriptor_observations: Tuple[CausalDescriptorObservationRecord, ...]
    state_observations: Tuple[CausalStateVariableObservationRecord, ...]
    delta_hierarchy_standing_status: Union[str, TypedState]


def create_standard_wave_descriptor_registry() -> DescriptorRegistry:
    """Create the standard S6 mathematical wave DescriptorRegistry (zero magic constants)."""
    reg = DescriptorRegistry()
    reg.register(
        DescriptorSpec.create(
            descriptor_id="RUNNING_EFFICIENCY_RATIO",
            semantic_definition="Causal |running_displacement| / running_path_length at bar t",
            stage=DESCRIPTOR_STAGE_RUNNING_ONLY,
            required_input_refs=(
                "running_displacement",
                "running_path_length",
            ),
            availability_rule_ref="VISIBLE_AT_RUNNING_OBSERVATION_KEY",
            running_formula_hash="FORMULA_RUN_EFF_V1",
        )
    )
    reg.register(
        DescriptorSpec.create(
            descriptor_id="RUNNING_AMPLITUDE_VS_PRIOR_WAVE",
            semantic_definition="Causal |running_displacement| / |prior_confirmed_wave_displacement|",
            stage=DESCRIPTOR_STAGE_RUNNING_ONLY,
            required_input_refs=(
                "running_displacement",
                "prior_confirmed_wave_displacement",
            ),
            availability_rule_ref="VISIBLE_AT_RUNNING_OBSERVATION_KEY",
            running_formula_hash="FORMULA_RUN_AMP_RATIO_V1",
        )
    )
    reg.register(
        DescriptorSpec.create(
            descriptor_id="FINAL_EFFICIENCY_RATIO",
            semantic_definition="Finalized |final_displacement| / final_path_length at wave_end_confirmed_key",
            stage=DESCRIPTOR_STAGE_FINAL_ONLY,
            required_input_refs=("final_displacement", "final_path_length"),
            availability_rule_ref="VISIBLE_AT_WAVE_END_CONFIRMED_KEY",
            final_formula_hash="FORMULA_FINAL_EFF_V1",
        )
    )
    reg.register(
        DescriptorSpec.create(
            descriptor_id="FINAL_RETRACTION_OR_EXTENSION_RATIO",
            semantic_definition="Finalized |final_displacement| / |prior_confirmed_wave_displacement|",
            stage=DESCRIPTOR_STAGE_FINAL_ONLY,
            required_input_refs=(
                "final_displacement",
                "prior_confirmed_wave_displacement",
            ),
            availability_rule_ref="VISIBLE_AT_WAVE_END_CONFIRMED_KEY",
            final_formula_hash="FORMULA_FINAL_RET_EXT_V1",
        )
    )
    reg.register(
        DescriptorSpec.create(
            descriptor_id="FINAL_CAUSAL_EFFICIENCY_RANK",
            semantic_definition="Causal empirical rank of final_efficiency_ratio over prior confirmed waves <= wave_end_confirmed_key",
            stage=DESCRIPTOR_STAGE_FINAL_ONLY,
            required_input_refs=(
                "final_efficiency_ratio",
                "prior_confirmed_efficiency_history",
            ),
            availability_rule_ref="VISIBLE_AT_WAVE_END_CONFIRMED_KEY",
            final_formula_hash="FORMULA_FINAL_CAUSAL_EFF_RANK_V1",
        )
    )
    return reg


def build_generic_factual_state_graph(
    wave_bundle: CandidateWaveRepresentationBundle,
    *,
    descriptor_registry: DescriptorRegistry,
    state_catalog: StateCatalogArtifact,
    graph_spec: GenericFactualStateGraphSpec,
    request_populated_delta_hierarchy: bool = False,
) -> GenericFactualStateGraphBundle:
    """Build a GenericFactualStateGraphBundle in O(N) over a CandidateWaveRepresentationBundle (D2-8..16, AP-1 §1..2)."""
    if not isinstance(wave_bundle, CandidateWaveRepresentationBundle):
        raise SchemaViolation(
            "wave_bundle must be a CandidateWaveRepresentationBundle"
        )
    if wave_bundle.dataset_role not in (
        DATASET_ROLE_DEVELOPMENT_FIT,
        DATASET_ROLE_DEVELOPMENT_SELECTION,
    ):
        raise SelectionBlockedError(
            f"{S6_FINAL_DATASET_FORBIDDEN}: S6 state graph construction on {wave_bundle.dataset_role!r} forbidden"
        )
    if not isinstance(descriptor_registry, DescriptorRegistry):
        raise SchemaViolation("descriptor_registry must be a DescriptorRegistry")
    if not isinstance(state_catalog, StateCatalogArtifact):
        raise SchemaViolation("state_catalog must be a StateCatalogArtifact")
    if not isinstance(graph_spec, GenericFactualStateGraphSpec):
        raise SchemaViolation(
            "graph_spec must be a GenericFactualStateGraphSpec"
        )
    if graph_spec.state_catalog_hash != state_catalog.state_catalog_hash:
        raise SchemaViolation(
            f"{S6_INVALID_GENERIC_STATE_GRAPH_SPEC}: graph_spec.state_catalog_hash != state_catalog.state_catalog_hash"
        )

    # I-DELTA-4: Delta family populated containment hierarchy is contract-only unless merge/adjacency configured
    delta_status: Union[str, TypedState] = TypedState.NOT_APPLICABLE
    if (
        wave_bundle.representation_spec.family_kind
        == FAMILY_DELTA_EVENT_CONTAINMENT
    ):
        if request_populated_delta_hierarchy:
            raise SelectionBlockedError(
                f"{S6_DELTA_POPULATED_HIERARCHY_NOT_CONFIGURED}: "
                f"{DELTA_CONTAINMENT_HIERARCHY_STANDING_STATUS} (D2-9, I-DELTA-3..4)"
            )
        delta_status = DELTA_CONTAINMENT_HIERARCHY_STANDING_STATUS

    # Build FactualStateGraphNodeRecord per WaveIdentityRecord (Scale != Depth, I-SD-1..4)
    nodes: list[FactualStateGraphNodeRecord] = []
    for wi in wave_bundle.wave_identity_records:
        nodes.append(
            FactualStateGraphNodeRecord(
                node_id=wi.wave_process_id,
                timeline_id=wi.timeline_id,
                node_availability_key=wi.wave_identity_information_key,
                intrinsic_scale_key=wave_bundle.representation_spec.intrinsic_scale_key,
                containment_depth=TypedState.NOT_APPLICABLE,
            )
        )

    # Build causal ADJACENT_TO relations between consecutive waves (D2-9, D2-10)
    relations: list[WaveRelationRecord] = []
    for idx in range(1, len(wave_bundle.wave_identity_records)):
        prev_wi = wave_bundle.wave_identity_records[idx - 1]
        curr_wi = wave_bundle.wave_identity_records[idx]
        batch_rel = (
            BatchRelation.DIFFERENT_BATCH
            if prev_wi.wave_identity_information_key
            < curr_wi.wave_identity_information_key
            else BatchRelation.KNOWN_SAME_BATCH
        )
        if batch_rel is BatchRelation.DIFFERENT_BATCH:
            relations.append(
                WaveRelationRecord.create(
                    relation_type=RELATION_ADJACENT_TO,
                    source_wave_process_id=prev_wi.wave_process_id,
                    target_wave_process_id=curr_wi.wave_process_id,
                    timeline_id=curr_wi.timeline_id,
                    source_availability_key=prev_wi.wave_identity_information_key,
                    target_availability_key=curr_wi.wave_identity_information_key,
                    batch_relation=batch_rel,
                    used_for_adjacency_or_parent=True,
                )
            )

    # Index finalized geometries by wave_end_confirmed_key for causal prior-wave lookup
    geoms_sorted = sorted(
        wave_bundle.finalized_wave_geometries,
        key=lambda g: g.wave_end_confirmed_key,
    )

    desc_obs: list[CausalDescriptorObservationRecord] = []
    state_obs: list[CausalStateVariableObservationRecord] = []

    # Map registered descriptor specs
    reg_specs = {s.descriptor_id: s for s in descriptor_registry.all_specs()}

    # 1. Running descriptor observations
    geom_ptr = 0
    latest_prior_geom: Optional[FinalizedWaveGeometryRecord] = None
    for ro in wave_bundle.running_wave_observations:
        while (
            geom_ptr < len(geoms_sorted)
            and geoms_sorted[geom_ptr].wave_end_confirmed_key
            <= ro.observation_key
        ):
            if geoms_sorted[geom_ptr].wave_process_id != ro.wave_process_id:
                latest_prior_geom = geoms_sorted[geom_ptr]
            geom_ptr += 1

        if "RUNNING_EFFICIENCY_RATIO" in reg_specs:
            sp = reg_specs["RUNNING_EFFICIENCY_RATIO"]
            obs_id = f"dobs:{sp.descriptor_id}:{ro.observation_id}"
            pub = PublishedRecord(
                record_type=S6_DESCRIPTOR_OBSERVATION_RECORD_TYPE,
                record_identity=obs_id,
                schema_identity=S6_SCHEMA_IDENTITY,
                timeline_id=ro.timeline_id,
                availability_key=ro.observation_key,
                content={
                    "observation_id": obs_id,
                    "descriptor_id": sp.descriptor_id,
                    "wave_process_id": ro.wave_process_id,
                },
            )
            desc_obs.append(
                CausalDescriptorObservationRecord(
                    observation_id=obs_id,
                    wave_process_id=ro.wave_process_id,
                    descriptor_id=sp.descriptor_id,
                    descriptor_hash=sp.descriptor_hash,
                    stage=DESCRIPTOR_STAGE_RUNNING_ONLY,
                    timeline_id=ro.timeline_id,
                    observation_key=ro.observation_key,
                    value=ro.running_efficiency_ratio,
                    published_record=pub,
                )
            )

        if "RUNNING_AMPLITUDE_VS_PRIOR_WAVE" in reg_specs:
            sp = reg_specs["RUNNING_AMPLITUDE_VS_PRIOR_WAVE"]
            if (
                latest_prior_geom is None
                or abs(latest_prior_geom.final_displacement.value) <= 0.0
            ):
                amp_val: Union[MetricResult, TypedState] = TypedState.UNDEFINED
            else:
                amp_val = exact_metric(
                    abs(ro.running_displacement.value)
                    / abs(latest_prior_geom.final_displacement.value)
                )
            obs_id = f"dobs:{sp.descriptor_id}:{ro.observation_id}"
            pub = PublishedRecord(
                record_type=S6_DESCRIPTOR_OBSERVATION_RECORD_TYPE,
                record_identity=obs_id,
                schema_identity=S6_SCHEMA_IDENTITY,
                timeline_id=ro.timeline_id,
                availability_key=ro.observation_key,
                content={
                    "observation_id": obs_id,
                    "descriptor_id": sp.descriptor_id,
                    "wave_process_id": ro.wave_process_id,
                },
            )
            desc_obs.append(
                CausalDescriptorObservationRecord(
                    observation_id=obs_id,
                    wave_process_id=ro.wave_process_id,
                    descriptor_id=sp.descriptor_id,
                    descriptor_hash=sp.descriptor_hash,
                    stage=DESCRIPTOR_STAGE_RUNNING_ONLY,
                    timeline_id=ro.timeline_id,
                    observation_key=ro.observation_key,
                    value=amp_val,
                    published_record=pub,
                )
            )

    # 2. Finalized descriptor observations & state-variable observations
    prior_eff_values: list[float] = []
    prev_fg: Optional[FinalizedWaveGeometryRecord] = None
    for fg in geoms_sorted:
        if "FINAL_EFFICIENCY_RATIO" in reg_specs:
            sp = reg_specs["FINAL_EFFICIENCY_RATIO"]
            obs_id = f"dobs:{sp.descriptor_id}:{fg.geometry_record_id}"
            pub = PublishedRecord(
                record_type=S6_DESCRIPTOR_OBSERVATION_RECORD_TYPE,
                record_identity=obs_id,
                schema_identity=S6_SCHEMA_IDENTITY,
                timeline_id=fg.timeline_id,
                availability_key=fg.wave_end_confirmed_key,
                content={
                    "observation_id": obs_id,
                    "descriptor_id": sp.descriptor_id,
                    "wave_process_id": fg.wave_process_id,
                },
            )
            desc_obs.append(
                CausalDescriptorObservationRecord(
                    observation_id=obs_id,
                    wave_process_id=fg.wave_process_id,
                    descriptor_id=sp.descriptor_id,
                    descriptor_hash=sp.descriptor_hash,
                    stage=DESCRIPTOR_STAGE_FINAL_ONLY,
                    timeline_id=fg.timeline_id,
                    observation_key=fg.wave_end_confirmed_key,
                    value=fg.final_efficiency_ratio,
                    published_record=pub,
                )
            )

        if "FINAL_RETRACTION_OR_EXTENSION_RATIO" in reg_specs:
            sp = reg_specs["FINAL_RETRACTION_OR_EXTENSION_RATIO"]
            if prev_fg is None or abs(prev_fg.final_displacement.value) <= 0.0:
                ret_val: Union[MetricResult, TypedState] = TypedState.UNDEFINED
            else:
                ret_val = exact_metric(
                    abs(fg.final_displacement.value)
                    / abs(prev_fg.final_displacement.value)
                )
            obs_id = f"dobs:{sp.descriptor_id}:{fg.geometry_record_id}"
            pub = PublishedRecord(
                record_type=S6_DESCRIPTOR_OBSERVATION_RECORD_TYPE,
                record_identity=obs_id,
                schema_identity=S6_SCHEMA_IDENTITY,
                timeline_id=fg.timeline_id,
                availability_key=fg.wave_end_confirmed_key,
                content={
                    "observation_id": obs_id,
                    "descriptor_id": sp.descriptor_id,
                    "wave_process_id": fg.wave_process_id,
                },
            )
            desc_obs.append(
                CausalDescriptorObservationRecord(
                    observation_id=obs_id,
                    wave_process_id=fg.wave_process_id,
                    descriptor_id=sp.descriptor_id,
                    descriptor_hash=sp.descriptor_hash,
                    stage=DESCRIPTOR_STAGE_FINAL_ONLY,
                    timeline_id=fg.timeline_id,
                    observation_key=fg.wave_end_confirmed_key,
                    value=ret_val,
                    published_record=pub,
                )
            )

        if "FINAL_CAUSAL_EFFICIENCY_RANK" in reg_specs:
            sp = reg_specs["FINAL_CAUSAL_EFFICIENCY_RANK"]
            if (
                not isinstance(fg.final_efficiency_ratio, MetricResult)
                or len(prior_eff_values) == 0
            ):
                rank_val: Union[MetricResult, TypedState] = (
                    TypedState.UNDEFINED
                )
            else:
                le_cnt = sum(
                    1
                    for v in prior_eff_values
                    if v <= fg.final_efficiency_ratio.value
                )
                rank_val = exact_metric(
                    float(le_cnt) / float(len(prior_eff_values))
                )
            obs_id = f"dobs:{sp.descriptor_id}:{fg.geometry_record_id}"
            pub = PublishedRecord(
                record_type=S6_DESCRIPTOR_OBSERVATION_RECORD_TYPE,
                record_identity=obs_id,
                schema_identity=S6_SCHEMA_IDENTITY,
                timeline_id=fg.timeline_id,
                availability_key=fg.wave_end_confirmed_key,
                content={
                    "observation_id": obs_id,
                    "descriptor_id": sp.descriptor_id,
                    "wave_process_id": fg.wave_process_id,
                },
            )
            desc_obs.append(
                CausalDescriptorObservationRecord(
                    observation_id=obs_id,
                    wave_process_id=fg.wave_process_id,
                    descriptor_id=sp.descriptor_id,
                    descriptor_hash=sp.descriptor_hash,
                    stage=DESCRIPTOR_STAGE_FINAL_ONLY,
                    timeline_id=fg.timeline_id,
                    observation_key=fg.wave_end_confirmed_key,
                    value=rank_val,
                    published_record=pub,
                )
            )

        if isinstance(fg.final_efficiency_ratio, MetricResult):
            prior_eff_values.append(fg.final_efficiency_ratio.value)
        prev_fg = fg

        for vs in state_catalog.variable_specs:
            state_obs.append(
                CausalStateVariableObservationRecord(
                    state_observation_id=f"sobs:{vs.variable_id}:{fg.geometry_record_id}",
                    wave_process_id=fg.wave_process_id,
                    variable_id=vs.variable_id,
                    variable_hash=vs.variable_hash,
                    state_catalog_hash=state_catalog.state_catalog_hash,
                    timeline_id=fg.timeline_id,
                    observation_key=fg.wave_end_confirmed_key,
                    state_value=fg.final_efficiency_ratio,
                )
            )

    return GenericFactualStateGraphBundle(
        graph_spec=graph_spec,
        state_catalog=state_catalog,
        wave_bundle=wave_bundle,
        nodes=tuple(nodes),
        relations=tuple(relations),
        descriptor_observations=tuple(desc_obs),
        state_observations=tuple(state_obs),
        delta_hierarchy_standing_status=delta_status,
    )


def query_state_graph_as_of(
    bundle: GenericFactualStateGraphBundle,
    *,
    at_key: InformationKey,
) -> GenericFactualStateGraphAsOfView:
    """Project a GenericFactualStateGraphBundle causally at ``at_key`` with cycle-safe closure."""
    if not isinstance(bundle, GenericFactualStateGraphBundle):
        raise SchemaViolation("bundle must be a GenericFactualStateGraphBundle")
    _require_completed_key(at_key, "at_key", S6_INVALID_CLOSURE_RECORD)
    if at_key.timeline_id != bundle.wave_bundle.timeline_id:
        raise InformationKeyViolation("at_key timeline mismatch with bundle")
    if not (
        bundle.wave_bundle.observation_keys[0]
        <= at_key
        <= bundle.wave_bundle.observation_keys[-1]
    ):
        raise PrematureAvailability("at_key outside bundle observation_keys")

    vis_nodes = tuple(
        n for n in bundle.nodes if n.node_availability_key <= at_key
    )
    vis_rels = tuple(
        r for r in bundle.relations if r.relation_information_key <= at_key
    )
    vis_dobs = tuple(
        d for d in bundle.descriptor_observations if d.observation_key <= at_key
    )
    vis_sobs = tuple(
        s for s in bundle.state_observations if s.observation_key <= at_key
    )
    closure = compute_cycle_safe_graph_closure(
        vis_nodes,
        vis_rels,
        seed_node_ids=tuple(n.node_id for n in vis_nodes),
        at_key=at_key,
    )
    return GenericFactualStateGraphAsOfView(
        timeline_id=bundle.wave_bundle.timeline_id,
        query_key=at_key,
        graph_spec_hash=bundle.graph_spec.graph_spec_hash,
        state_catalog_hash=bundle.state_catalog.state_catalog_hash,
        visible_nodes=vis_nodes,
        visible_relations=vis_rels,
        visible_descriptor_observations=vis_dobs,
        visible_state_observations=vis_sobs,
        closure_record=closure,
    )


__all__ = [
    "CLOSURE_RECORD_SCHEMA",
    "CausalDescriptorObservationRecord",
    "CausalStateVariableObservationRecord",
    "CycleSafeGraphClosureRecord",
    "DELTA_CONTAINMENT_HIERARCHY_STANDING_STATUS",
    "DESCRIPTOR_SPEC_SCHEMA",
    "DESCRIPTOR_STAGE_BOTH_SEPARATE_FORMULAE",
    "DESCRIPTOR_STAGE_FINAL_ONLY",
    "DESCRIPTOR_STAGE_RUNNING_ONLY",
    "DescriptorRegistry",
    "DescriptorSpec",
    "FORBIDDEN_GENERIC_GRAPH_SUBSTRINGS",
    "FORBIDDEN_RUNNING_INPUT_SUBSTRINGS",
    "FactualStateGraphNodeRecord",
    "GENERIC_STATE_GRAPH_SPEC_SCHEMA",
    "GenericFactualStateGraphAsOfView",
    "GenericFactualStateGraphBundle",
    "GenericFactualStateGraphSpec",
    "LEGAL_DESCRIPTOR_STAGES",
    "LEGAL_RELATION_TYPES",
    "NON_ALTERNATING_MERGE_RULE_DEFAULT",
    "RELATION_ADJACENT_TO",
    "RELATION_ALTERNATES_WITH",
    "RELATION_CONTAINS",
    "RELATION_GENERAL_REFERENCE",
    "RELATION_GEOMETRICALLY_COINCIDENT",
    "RELATION_PARTIAL_OVERLAP",
    "S6_ALTERNATES_WITH_NOT_ADJACENCY",
    "S6_DELTA_POPULATED_HIERARCHY_NOT_CONFIGURED",
    "S6_DESCRIPTOR_OBSERVATION_RECORD_TYPE",
    "S6_DUPLICATE_DESCRIPTOR_REGISTRATION",
    "S6_ESTIMAND_OR_OBJECTIVE_FORBIDDEN_IN_GENERIC_STATE_GRAPH",
    "S6_FINAL_DATASET_FORBIDDEN",
    "S6_FUTURE_FACT_IN_RUNNING_DESCRIPTOR",
    "S6_ILLEGAL_WAVE_CONTAINMENT_CYCLE",
    "S6_INVALID_CLOSURE_RECORD",
    "S6_INVALID_DESCRIPTOR_SPEC",
    "S6_INVALID_GENERIC_STATE_GRAPH_SPEC",
    "S6_INVALID_STATE_CATALOG",
    "S6_INVALID_STATE_VARIABLE_SPEC",
    "S6_INVALID_WAVE_RELATION",
    "S6_SCALE_DEPTH_COLLAPSE_FORBIDDEN",
    "S6_SCHEMA_IDENTITY",
    "S6_SCHEMA_VERSION",
    "S6_SEPARATE_FORMULAE_REQUIRED",
    "S6_STATE_VARIABLE_OBSERVATION_RECORD_TYPE",
    "S6_UNDECLARED_CATALOG_REFERENCE",
    "S6_UNKNOWN_DESCRIPTOR_REF",
    "S6_UNPROVEN_CHRONOLOGY_FOR_ADJACENT_TO",
    "S6_WAVE_RELATION_RECORD_TYPE",
    "STATE_CATALOG_SCHEMA",
    "STATE_VARIABLE_SPEC_SCHEMA",
    "StateCatalogArtifact",
    "StateVariableSpec",
    "WAVE_RELATION_SCHEMA",
    "WaveRelationRecord",
    "build_generic_factual_state_graph",
    "compute_cycle_safe_graph_closure",
    "create_standard_wave_descriptor_registry",
    "query_state_graph_as_of",
]
