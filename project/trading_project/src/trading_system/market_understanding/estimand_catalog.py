"""MUF V1 S8 & S8.5: Estimand Catalog, FeatureViewSpec, and DevelopmentEvaluationProtocol.

Implements the preregistered Estimand Catalog, Estimand-Specific FeatureViewSpec,
DevelopmentEvaluationProtocol dependency-closure pinning, and causal competing-risk /
wave-continuation realization engine on DEVELOPMENT datasets (D1-17, D2-3, D2-4,
D2-15, D2-22, AP-1 §2, §3, §4):
- ``EstimandArtifact`` & ``EstimandCatalog`` (D1-17, I-EST-1, I-SCAT-1..3, I-GSG-4)
- ``FeatureViewSpec`` (AP-1 §3.1..3.4, I-FVIEW-1..5)
- ``DevelopmentEvaluationProtocol`` & ``verify_development_protocol_dependency_closure``
  (AP-1 §3.3 & §4.3, I-SG-1A)
- ``EstimandRealizationRecord``, ``DevelopmentEstimandEvaluationBundle``, and
  ``evaluate_development_estimand_realizations`` (O(N) causal realization with
  explicit right-censoring at dataset boundary)
"""
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence, Tuple, Union

from trading_system.market_understanding.availability import require_visible_at
from trading_system.market_understanding.contracts import (
    IllegalCausalReference,
    ImmutabilityViolation,
    InformationKeyViolation,
    PrematureAvailability,
    SchemaIdentity,
    SchemaViolation,
    TypedState,
)
from trading_system.market_understanding.dependence_accounting import (
    DependenceAccountingBundle,
    DependenceAccountingContract,
)
from trading_system.market_understanding.identity import (
    ArtifactIdentitySchema,
    canonical_artifact_identity,
)
from trading_system.market_understanding.policy_governance import (
    DATASET_ROLE_DEVELOPMENT_FIT,
    DATASET_ROLE_DEVELOPMENT_SELECTION,
    DATASET_ROLE_FINAL_EVALUATION_LOCKED,
    ExperimentRegistry,
    ObjectiveArtifact,
    SelectionBlockedError,
)
from trading_system.market_understanding.price_path import (
    EXACT,
    MetricResult,
    exact_metric,
)
from trading_system.market_understanding.records import (
    ImmutableRecord,
    PublishedRecord,
)
from trading_system.market_understanding.state_graph import (
    GenericFactualStateGraphSpec,
    StateCatalogArtifact,
)
from trading_system.research.information_time import (
    InformationKey,
    InformationPhase,
)


S8_SCHEMA_IDENTITY = SchemaIdentity("MUF_S8_ESTIMAND_CATALOG", "V1")
S8_SCHEMA_VERSION = "MUF_S8_ESTIMAND_CATALOG_V1"

# Future observable kinds (D1-17)
OBSERVABLE_SUBSEQUENT_WAVE_DISPLACEMENT_RATIO = (
    "SUBSEQUENT_WAVE_DISPLACEMENT_RATIO"
)
OBSERVABLE_SUBSEQUENT_WAVE_EFFICIENCY = "SUBSEQUENT_WAVE_EFFICIENCY"
OBSERVABLE_COMPETING_BOUNDARY_FIRST_PASSAGE = (
    "COMPETING_BOUNDARY_FIRST_PASSAGE"
)
LEGAL_FUTURE_OBSERVABLE_KINDS = frozenset(
    {
        OBSERVABLE_SUBSEQUENT_WAVE_DISPLACEMENT_RATIO,
        OBSERVABLE_SUBSEQUENT_WAVE_EFFICIENCY,
        OBSERVABLE_COMPETING_BOUNDARY_FIRST_PASSAGE,
    }
)

# Censoring statuses
CENSORING_STATUS_UNCENSORED = "UNCENSORED"
CENSORING_STATUS_RIGHT_CENSORED = "RIGHT_CENSORED_AT_DATASET_END"
LEGAL_CENSORING_STATUSES = frozenset(
    {
        CENSORING_STATUS_UNCENSORED,
        CENSORING_STATUS_RIGHT_CENSORED,
    }
)

# Deterministic S8 & S8.5 error codes
S8_INVALID_ESTIMAND_ARTIFACT = "S8_INVALID_ESTIMAND_ARTIFACT"
S8_UNDEFINED_STATE_VARIABLE_IN_ESTIMAND = (
    "S8_UNDEFINED_STATE_VARIABLE_IN_ESTIMAND"
)
S8_DUPLICATE_ESTIMAND_REGISTRATION = "S8_DUPLICATE_ESTIMAND_REGISTRATION"
S8_UNKNOWN_ESTIMAND_REF = "S8_UNKNOWN_ESTIMAND_REF"
S8_EVALUATION_WITHOUT_PREREGISTERED_ESTIMAND = (
    "S8_EVALUATION_WITHOUT_PREREGISTERED_ESTIMAND"
)
S8_INVALID_FEATURE_VIEW_SPEC = "S8_INVALID_FEATURE_VIEW_SPEC"
S8_FEATURE_VIEW_UNDECLARED_VARIABLE = "S8_FEATURE_VIEW_UNDECLARED_VARIABLE"
S8_FEATURE_VIEW_CATALOG_OR_ESTIMAND_MISMATCH = (
    "S8_FEATURE_VIEW_CATALOG_OR_ESTIMAND_MISMATCH"
)
S8_INVALID_DEVELOPMENT_EVALUATION_PROTOCOL = (
    "S8_INVALID_DEVELOPMENT_EVALUATION_PROTOCOL"
)
S8_PROTOCOL_DEPENDENCY_CLOSURE_MISMATCH = (
    "S8_PROTOCOL_DEPENDENCY_CLOSURE_MISMATCH"
)
S8_FINAL_DATASET_FORBIDDEN_IN_DEVELOPMENT_PROTOCOL = (
    "S8_FINAL_DATASET_FORBIDDEN_IN_DEVELOPMENT_PROTOCOL"
)


ESTIMAND_ARTIFACT_SCHEMA = ArtifactIdentitySchema(
    artifact_type="MUF_S8_ESTIMAND_ARTIFACT",
    schema_identity=S8_SCHEMA_IDENTITY,
    identity_defining_fields=(
        "estimand_id",
        "state_catalog_hash",
        "population_variable_refs",
        "conditioning_variable_refs",
        "future_observable_kind",
        "boundary_span_contract",
        "censoring_contract",
        "missingness_contract",
        "aggregation_contract",
        "permitted_dataset_roles",
        "preregistration_key",
        "code_hash",
    ),
)

FEATURE_VIEW_SPEC_SCHEMA = ArtifactIdentitySchema(
    artifact_type="MUF_S8_5_FEATURE_VIEW_SPEC",
    schema_identity=S8_SCHEMA_IDENTITY,
    identity_defining_fields=(
        "feature_view_id",
        "state_catalog_hash",
        "selected_state_variable_refs",
        "transformation_refs",
        "missingness_handling_ref",
        "availability_rule_ref",
        "estimand_hash",
        "schema_version",
    ),
)

DEVELOPMENT_EVALUATION_PROTOCOL_SCHEMA = ArtifactIdentitySchema(
    artifact_type="MUF_S8_5_DEVELOPMENT_EVALUATION_PROTOCOL",
    schema_identity=S8_SCHEMA_IDENTITY,
    identity_defining_fields=(
        "protocol_id",
        "estimand_hash",
        "feature_view_hash",
        "state_catalog_hash",
        "graph_spec_hash",
        "dependence_contract_hash",
        "objective_hash",
        "dataset_id",
        "dataset_role",
        "experiment_id",
        "preregistration_key",
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


@dataclass(frozen=True)
class EstimandArtifact(ImmutableRecord):
    """Preregistered EstimandArtifact bound to a StateCatalogArtifact (D1-17, AP-1 §2, I-EST-1, I-SCAT-1..3)."""

    estimand_id: str
    state_catalog_hash: str
    population_variable_refs: Tuple[str, ...]
    conditioning_variable_refs: Tuple[str, ...]
    future_observable_kind: str
    boundary_span_contract: str
    censoring_contract: str
    missingness_contract: str
    aggregation_contract: str
    permitted_dataset_roles: Tuple[str, ...]
    preregistration_key: InformationKey
    code_hash: str
    estimand_hash: str

    def __post_init__(self) -> None:
        _require_non_empty_str(
            self.estimand_id, "estimand_id", S8_INVALID_ESTIMAND_ARTIFACT
        )
        _require_non_empty_str(
            self.state_catalog_hash,
            "state_catalog_hash",
            S8_INVALID_ESTIMAND_ARTIFACT,
        )
        pop_refs = _require_str_tuple(
            self.population_variable_refs,
            "population_variable_refs",
            S8_INVALID_ESTIMAND_ARTIFACT,
        )
        cond_refs = _require_str_tuple(
            self.conditioning_variable_refs,
            "conditioning_variable_refs",
            S8_INVALID_ESTIMAND_ARTIFACT,
        )
        if len(pop_refs) == 0:
            raise SchemaViolation(
                f"{S8_INVALID_ESTIMAND_ARTIFACT}: population_variable_refs must be non-empty"
            )
        object.__setattr__(self, "population_variable_refs", pop_refs)
        object.__setattr__(self, "conditioning_variable_refs", cond_refs)

        if self.future_observable_kind not in LEGAL_FUTURE_OBSERVABLE_KINDS:
            raise SchemaViolation(
                f"{S8_INVALID_ESTIMAND_ARTIFACT}: invalid future_observable_kind {self.future_observable_kind!r}"
            )
        _require_non_empty_str(
            self.boundary_span_contract,
            "boundary_span_contract",
            S8_INVALID_ESTIMAND_ARTIFACT,
        )
        _require_non_empty_str(
            self.censoring_contract,
            "censoring_contract",
            S8_INVALID_ESTIMAND_ARTIFACT,
        )
        _require_non_empty_str(
            self.missingness_contract,
            "missingness_contract",
            S8_INVALID_ESTIMAND_ARTIFACT,
        )
        _require_non_empty_str(
            self.aggregation_contract,
            "aggregation_contract",
            S8_INVALID_ESTIMAND_ARTIFACT,
        )
        roles = _require_str_tuple(
            self.permitted_dataset_roles,
            "permitted_dataset_roles",
            S8_INVALID_ESTIMAND_ARTIFACT,
        )
        if len(roles) == 0:
            raise SchemaViolation(
                f"{S8_INVALID_ESTIMAND_ARTIFACT}: permitted_dataset_roles must be non-empty"
            )
        object.__setattr__(self, "permitted_dataset_roles", roles)
        _require_completed_key(
            self.preregistration_key,
            "preregistration_key",
            S8_INVALID_ESTIMAND_ARTIFACT,
        )
        _require_non_empty_str(
            self.code_hash, "code_hash", S8_INVALID_ESTIMAND_ARTIFACT
        )

        expected_hash = canonical_artifact_identity(
            ESTIMAND_ARTIFACT_SCHEMA,
            identity_payload={
                "estimand_id": self.estimand_id,
                "state_catalog_hash": self.state_catalog_hash,
                "population_variable_refs": _serialize_seq(pop_refs),
                "conditioning_variable_refs": _serialize_seq(cond_refs),
                "future_observable_kind": self.future_observable_kind,
                "boundary_span_contract": self.boundary_span_contract,
                "censoring_contract": self.censoring_contract,
                "missingness_contract": self.missingness_contract,
                "aggregation_contract": self.aggregation_contract,
                "permitted_dataset_roles": _serialize_seq(roles),
                "preregistration_key": self.preregistration_key,
                "code_hash": self.code_hash,
            },
        )
        if self.estimand_hash != expected_hash:
            raise SchemaViolation(
                f"{S8_INVALID_ESTIMAND_ARTIFACT}: estimand_hash mismatch"
            )

    @classmethod
    def create(
        cls,
        *,
        estimand_id: str,
        state_catalog: StateCatalogArtifact,
        population_variable_refs: Sequence[str],
        conditioning_variable_refs: Sequence[str] = (),
        future_observable_kind: str = OBSERVABLE_SUBSEQUENT_WAVE_DISPLACEMENT_RATIO,
        boundary_span_contract: str = "NEXT_CONFIRMED_OPPOSITE_WAVE_END",
        censoring_contract: str = "EXPLICIT_RIGHT_CENSORED_AT_DATASET_END",
        missingness_contract: str = "EXPLICIT_TYPED_STATE_NO_SILENT_DROP",
        aggregation_contract: str = "EPISODE_CLUSTER_WEIGHTED_MEAN",
        permitted_dataset_roles: Sequence[str] = (
            DATASET_ROLE_DEVELOPMENT_FIT,
            DATASET_ROLE_DEVELOPMENT_SELECTION,
        ),
        preregistration_key: InformationKey,
        code_hash: str = "muf_s8_estimand_v1",
    ) -> "EstimandArtifact":
        if not isinstance(state_catalog, StateCatalogArtifact):
            raise SchemaViolation(
                f"{S8_INVALID_ESTIMAND_ARTIFACT}: state_catalog must be a StateCatalogArtifact"
            )
        pop_refs = _require_str_tuple(
            population_variable_refs,
            "population_variable_refs",
            S8_INVALID_ESTIMAND_ARTIFACT,
        )
        cond_refs = _require_str_tuple(
            conditioning_variable_refs,
            "conditioning_variable_refs",
            S8_INVALID_ESTIMAND_ARTIFACT,
        )
        catalog_var_ids = {vs.variable_id for vs in state_catalog.variable_specs}
        # I-SCAT-1 / I-SCAT-2: No EstimandArtifact may reference an undefined state variable
        for v_ref in pop_refs + cond_refs:
            if v_ref not in catalog_var_ids:
                raise SchemaViolation(
                    f"{S8_UNDEFINED_STATE_VARIABLE_IN_ESTIMAND}: state variable {v_ref!r} "
                    f"is not defined in StateCatalogArtifact {state_catalog.state_catalog_id!r} (I-SCAT-1)"
                )
        roles = _require_str_tuple(
            permitted_dataset_roles,
            "permitted_dataset_roles",
            S8_INVALID_ESTIMAND_ARTIFACT,
        )
        e_hash = canonical_artifact_identity(
            ESTIMAND_ARTIFACT_SCHEMA,
            identity_payload={
                "estimand_id": estimand_id,
                "state_catalog_hash": state_catalog.state_catalog_hash,
                "population_variable_refs": _serialize_seq(pop_refs),
                "conditioning_variable_refs": _serialize_seq(cond_refs),
                "future_observable_kind": future_observable_kind,
                "boundary_span_contract": boundary_span_contract,
                "censoring_contract": censoring_contract,
                "missingness_contract": missingness_contract,
                "aggregation_contract": aggregation_contract,
                "permitted_dataset_roles": _serialize_seq(roles),
                "preregistration_key": preregistration_key,
                "code_hash": code_hash,
            },
        )
        return cls(
            estimand_id=estimand_id,
            state_catalog_hash=state_catalog.state_catalog_hash,
            population_variable_refs=pop_refs,
            conditioning_variable_refs=cond_refs,
            future_observable_kind=future_observable_kind,
            boundary_span_contract=boundary_span_contract,
            censoring_contract=censoring_contract,
            missingness_contract=missingness_contract,
            aggregation_contract=aggregation_contract,
            permitted_dataset_roles=roles,
            preregistration_key=preregistration_key,
            code_hash=code_hash,
            estimand_hash=e_hash,
        )


class EstimandCatalog:
    """Append-only catalog of preregistered EstimandArtifacts (D1-17, I-EST-1)."""

    def __init__(self) -> None:
        self.__by_id: dict[str, EstimandArtifact] = {}

    def register(
        self,
        estimand: EstimandArtifact,
        *,
        state_catalog: StateCatalogArtifact,
    ) -> EstimandArtifact:
        if not isinstance(estimand, EstimandArtifact):
            raise SchemaViolation(
                f"{S8_INVALID_ESTIMAND_ARTIFACT}: expected EstimandArtifact"
            )
        if not isinstance(state_catalog, StateCatalogArtifact):
            raise SchemaViolation(
                f"{S8_INVALID_ESTIMAND_ARTIFACT}: expected StateCatalogArtifact"
            )
        if estimand.state_catalog_hash != state_catalog.state_catalog_hash:
            raise SchemaViolation(
                f"{S8_UNDEFINED_STATE_VARIABLE_IN_ESTIMAND}: estimand state_catalog_hash mismatch"
            )
        cat_vars = {vs.variable_id for vs in state_catalog.variable_specs}
        for vr in (
            estimand.population_variable_refs
            + estimand.conditioning_variable_refs
        ):
            if vr not in cat_vars:
                raise SchemaViolation(
                    f"{S8_UNDEFINED_STATE_VARIABLE_IN_ESTIMAND}: unknown state variable {vr!r} (I-SCAT-1)"
                )
        by_id = object.__getattribute__(self, "_EstimandCatalog__by_id")
        if estimand.estimand_id in by_id:
            raise ImmutabilityViolation(
                f"{S8_DUPLICATE_ESTIMAND_REGISTRATION}: estimand {estimand.estimand_id!r} already registered"
            )
        by_id[estimand.estimand_id] = estimand
        return estimand

    def get(self, estimand_id: str) -> EstimandArtifact:
        by_id = object.__getattribute__(self, "_EstimandCatalog__by_id")
        if estimand_id not in by_id:
            raise SelectionBlockedError(
                f"{S8_UNKNOWN_ESTIMAND_REF}: unknown estimand {estimand_id!r}"
            )
        return by_id[estimand_id]

    def all_estimands(self) -> Tuple[EstimandArtifact, ...]:
        by_id = object.__getattribute__(self, "_EstimandCatalog__by_id")
        return tuple(by_id.values())


@dataclass(frozen=True)
class FeatureViewSpec(ImmutableRecord):
    """Estimand-specific FeatureViewSpec (AP-1 §3.1..3.4, I-FVIEW-1..5)."""

    feature_view_id: str
    state_catalog_hash: str
    selected_state_variable_refs: Tuple[str, ...]
    transformation_refs: Tuple[str, ...]
    missingness_handling_ref: str
    availability_rule_ref: str
    estimand_hash: str
    schema_version: str
    feature_view_hash: str

    def __post_init__(self) -> None:
        _require_non_empty_str(
            self.feature_view_id,
            "feature_view_id",
            S8_INVALID_FEATURE_VIEW_SPEC,
        )
        _require_non_empty_str(
            self.state_catalog_hash,
            "state_catalog_hash",
            S8_INVALID_FEATURE_VIEW_SPEC,
        )
        sel_vars = _require_str_tuple(
            self.selected_state_variable_refs,
            "selected_state_variable_refs",
            S8_INVALID_FEATURE_VIEW_SPEC,
        )
        if len(sel_vars) == 0:
            raise SchemaViolation(
                f"{S8_INVALID_FEATURE_VIEW_SPEC}: selected_state_variable_refs must be non-empty"
            )
        trans_refs = _require_str_tuple(
            self.transformation_refs,
            "transformation_refs",
            S8_INVALID_FEATURE_VIEW_SPEC,
        )
        object.__setattr__(self, "selected_state_variable_refs", sel_vars)
        object.__setattr__(self, "transformation_refs", trans_refs)

        _require_non_empty_str(
            self.missingness_handling_ref,
            "missingness_handling_ref",
            S8_INVALID_FEATURE_VIEW_SPEC,
        )
        _require_non_empty_str(
            self.availability_rule_ref,
            "availability_rule_ref",
            S8_INVALID_FEATURE_VIEW_SPEC,
        )
        _require_non_empty_str(
            self.estimand_hash, "estimand_hash", S8_INVALID_FEATURE_VIEW_SPEC
        )
        _require_non_empty_str(
            self.schema_version, "schema_version", S8_INVALID_FEATURE_VIEW_SPEC
        )

        expected_hash = canonical_artifact_identity(
            FEATURE_VIEW_SPEC_SCHEMA,
            identity_payload={
                "feature_view_id": self.feature_view_id,
                "state_catalog_hash": self.state_catalog_hash,
                "selected_state_variable_refs": _serialize_seq(sel_vars),
                "transformation_refs": _serialize_seq(trans_refs),
                "missingness_handling_ref": self.missingness_handling_ref,
                "availability_rule_ref": self.availability_rule_ref,
                "estimand_hash": self.estimand_hash,
                "schema_version": self.schema_version,
            },
        )
        if self.feature_view_hash != expected_hash:
            raise SchemaViolation(
                f"{S8_INVALID_FEATURE_VIEW_SPEC}: feature_view_hash mismatch"
            )

    @classmethod
    def create(
        cls,
        *,
        feature_view_id: str,
        state_catalog: StateCatalogArtifact,
        estimand: EstimandArtifact,
        selected_state_variable_refs: Sequence[str],
        transformation_refs: Sequence[str] = ("IDENTITY_PROJECTION_V1",),
        missingness_handling_ref: str = "PRESERVE_TYPED_STATE_V1",
        availability_rule_ref: str = "VISIBLE_AT_EVALUATION_KEY_V1",
        schema_version: str = S8_SCHEMA_VERSION,
    ) -> "FeatureViewSpec":
        if not isinstance(state_catalog, StateCatalogArtifact):
            raise SchemaViolation(
                f"{S8_INVALID_FEATURE_VIEW_SPEC}: state_catalog must be a StateCatalogArtifact"
            )
        if not isinstance(estimand, EstimandArtifact):
            raise SchemaViolation(
                f"{S8_INVALID_FEATURE_VIEW_SPEC}: estimand must be an EstimandArtifact"
            )
        if estimand.state_catalog_hash != state_catalog.state_catalog_hash:
            raise SchemaViolation(
                f"{S8_FEATURE_VIEW_CATALOG_OR_ESTIMAND_MISMATCH}: estimand.state_catalog_hash mismatch"
            )
        sel_vars = _require_str_tuple(
            selected_state_variable_refs,
            "selected_state_variable_refs",
            S8_INVALID_FEATURE_VIEW_SPEC,
        )
        cat_vars = {vs.variable_id for vs in state_catalog.variable_specs}
        for vr in sel_vars:
            if vr not in cat_vars:
                raise SchemaViolation(
                    f"{S8_FEATURE_VIEW_UNDECLARED_VARIABLE}: selected variable {vr!r} "
                    "not in StateCatalogArtifact (I-FVIEW-1, I-SCAT-1)"
                )
        trans_refs = _require_str_tuple(
            transformation_refs,
            "transformation_refs",
            S8_INVALID_FEATURE_VIEW_SPEC,
        )
        fv_hash = canonical_artifact_identity(
            FEATURE_VIEW_SPEC_SCHEMA,
            identity_payload={
                "feature_view_id": feature_view_id,
                "state_catalog_hash": state_catalog.state_catalog_hash,
                "selected_state_variable_refs": _serialize_seq(sel_vars),
                "transformation_refs": _serialize_seq(trans_refs),
                "missingness_handling_ref": missingness_handling_ref,
                "availability_rule_ref": availability_rule_ref,
                "estimand_hash": estimand.estimand_hash,
                "schema_version": schema_version,
            },
        )
        return cls(
            feature_view_id=feature_view_id,
            state_catalog_hash=state_catalog.state_catalog_hash,
            selected_state_variable_refs=sel_vars,
            transformation_refs=trans_refs,
            missingness_handling_ref=missingness_handling_ref,
            availability_rule_ref=availability_rule_ref,
            estimand_hash=estimand.estimand_hash,
            schema_version=schema_version,
            feature_view_hash=fv_hash,
        )


@dataclass(frozen=True)
class DevelopmentEvaluationProtocol(ImmutableRecord):
    """Preregistered DevelopmentEvaluationProtocol pinning full S6/S7/S8 closure (AP-1 §3.3 & §4.3, I-SG-1A)."""

    protocol_id: str
    estimand_hash: str
    feature_view_hash: str
    state_catalog_hash: str
    graph_spec_hash: str
    dependence_contract_hash: str
    objective_hash: str
    dataset_id: str
    dataset_role: str
    experiment_id: str
    preregistration_key: InformationKey
    protocol_hash: str

    def __post_init__(self) -> None:
        for f_name, f_val in (
            ("protocol_id", self.protocol_id),
            ("estimand_hash", self.estimand_hash),
            ("feature_view_hash", self.feature_view_hash),
            ("state_catalog_hash", self.state_catalog_hash),
            ("graph_spec_hash", self.graph_spec_hash),
            ("dependence_contract_hash", self.dependence_contract_hash),
            ("objective_hash", self.objective_hash),
            ("dataset_id", self.dataset_id),
            ("experiment_id", self.experiment_id),
        ):
            _require_non_empty_str(
                f_val, f_name, S8_INVALID_DEVELOPMENT_EVALUATION_PROTOCOL
            )
        if self.dataset_role not in (
            DATASET_ROLE_DEVELOPMENT_FIT,
            DATASET_ROLE_DEVELOPMENT_SELECTION,
        ):
            raise SelectionBlockedError(
                f"{S8_FINAL_DATASET_FORBIDDEN_IN_DEVELOPMENT_PROTOCOL}: "
                f"DevelopmentEvaluationProtocol forbids dataset_role={self.dataset_role!r} (I-SEL-3)"
            )
        _require_completed_key(
            self.preregistration_key,
            "preregistration_key",
            S8_INVALID_DEVELOPMENT_EVALUATION_PROTOCOL,
        )

        expected_hash = canonical_artifact_identity(
            DEVELOPMENT_EVALUATION_PROTOCOL_SCHEMA,
            identity_payload={
                "protocol_id": self.protocol_id,
                "estimand_hash": self.estimand_hash,
                "feature_view_hash": self.feature_view_hash,
                "state_catalog_hash": self.state_catalog_hash,
                "graph_spec_hash": self.graph_spec_hash,
                "dependence_contract_hash": self.dependence_contract_hash,
                "objective_hash": self.objective_hash,
                "dataset_id": self.dataset_id,
                "dataset_role": self.dataset_role,
                "experiment_id": self.experiment_id,
                "preregistration_key": self.preregistration_key,
            },
        )
        if self.protocol_hash != expected_hash:
            raise SchemaViolation(
                f"{S8_INVALID_DEVELOPMENT_EVALUATION_PROTOCOL}: protocol_hash mismatch"
            )

    @classmethod
    def create(
        cls,
        *,
        protocol_id: str,
        estimand: EstimandArtifact,
        feature_view: FeatureViewSpec,
        state_catalog: StateCatalogArtifact,
        graph_spec: GenericFactualStateGraphSpec,
        dependence_contract: DependenceAccountingContract,
        objective_artifact: ObjectiveArtifact,
        dataset_id: str,
        dataset_role: str,
        experiment_id: str,
        preregistration_key: InformationKey,
    ) -> "DevelopmentEvaluationProtocol":
        if (
            estimand.state_catalog_hash != state_catalog.state_catalog_hash
            or feature_view.state_catalog_hash
            != state_catalog.state_catalog_hash
            or graph_spec.state_catalog_hash
            != state_catalog.state_catalog_hash
            or feature_view.estimand_hash != estimand.estimand_hash
        ):
            raise SchemaViolation(
                f"{S8_PROTOCOL_DEPENDENCY_CLOSURE_MISMATCH}: inconsistent state_catalog_hash or estimand_hash across protocol components (I-SG-1A)"
            )
        p_hash = canonical_artifact_identity(
            DEVELOPMENT_EVALUATION_PROTOCOL_SCHEMA,
            identity_payload={
                "protocol_id": protocol_id,
                "estimand_hash": estimand.estimand_hash,
                "feature_view_hash": feature_view.feature_view_hash,
                "state_catalog_hash": state_catalog.state_catalog_hash,
                "graph_spec_hash": graph_spec.graph_spec_hash,
                "dependence_contract_hash": dependence_contract.contract_hash,
                "objective_hash": objective_artifact.objective_hash,
                "dataset_id": dataset_id,
                "dataset_role": dataset_role,
                "experiment_id": experiment_id,
                "preregistration_key": preregistration_key,
            },
        )
        return cls(
            protocol_id=protocol_id,
            estimand_hash=estimand.estimand_hash,
            feature_view_hash=feature_view.feature_view_hash,
            state_catalog_hash=state_catalog.state_catalog_hash,
            graph_spec_hash=graph_spec.graph_spec_hash,
            dependence_contract_hash=dependence_contract.contract_hash,
            objective_hash=objective_artifact.objective_hash,
            dataset_id=dataset_id,
            dataset_role=dataset_role,
            experiment_id=experiment_id,
            preregistration_key=preregistration_key,
            protocol_hash=p_hash,
        )


def verify_development_protocol_dependency_closure(
    protocol: DevelopmentEvaluationProtocol,
    *,
    estimand: EstimandArtifact,
    feature_view: FeatureViewSpec,
    state_catalog: StateCatalogArtifact,
    graph_spec: GenericFactualStateGraphSpec,
    dependence_contract: DependenceAccountingContract,
    objective_artifact: ObjectiveArtifact,
    experiment_registry: ExperimentRegistry,
) -> bool:
    """Verify full dependency closure of a DevelopmentEvaluationProtocol (AP-1 §4.3, I-SG-1A)."""
    if not isinstance(protocol, DevelopmentEvaluationProtocol):
        raise SelectionBlockedError(
            f"{S8_EVALUATION_WITHOUT_PREREGISTERED_ESTIMAND}: valid DevelopmentEvaluationProtocol required"
        )
    if (
        protocol.estimand_hash != estimand.estimand_hash
        or protocol.feature_view_hash != feature_view.feature_view_hash
        or protocol.state_catalog_hash != state_catalog.state_catalog_hash
        or protocol.graph_spec_hash != graph_spec.graph_spec_hash
        or protocol.dependence_contract_hash
        != dependence_contract.contract_hash
        or protocol.objective_hash != objective_artifact.objective_hash
    ):
        raise SelectionBlockedError(
            f"{S8_PROTOCOL_DEPENDENCY_CLOSURE_MISMATCH}: protocol component hash mismatch (I-SG-1A)"
        )
    exp_rec = experiment_registry.get(protocol.experiment_id)
    if exp_rec.objective_artifact_hash != objective_artifact.objective_hash:
        raise SelectionBlockedError(
            f"{S8_PROTOCOL_DEPENDENCY_CLOSURE_MISMATCH}: experiment objective_artifact_hash mismatch"
        )
    return True


@dataclass(frozen=True)
class EstimandRealizationRecord(ImmutableRecord):
    """Causal realization of a preregistered Estimand for a confirmed wave episode."""

    realization_id: str
    protocol_hash: str
    estimand_hash: str
    feature_view_hash: str
    episode_id: str
    wave_process_id: str
    decision_key: InformationKey
    outcome_resolution_key: InformationKey
    feature_values: Mapping[str, Union[MetricResult, TypedState, str]]
    censoring_status: str
    outcome_value: Union[MetricResult, TypedState]
    favorable_structural_continuation: Union[bool, TypedState]


@dataclass(frozen=True)
class DevelopmentEstimandEvaluationBundle(ImmutableRecord):
    """Complete S8/S8.5 Development Estimand Evaluation Bundle."""

    protocol: DevelopmentEvaluationProtocol
    estimand: EstimandArtifact
    feature_view: FeatureViewSpec
    realizations: Tuple[EstimandRealizationRecord, ...]
    uncensored_count: int
    right_censored_count: int
    non_overlapping_span_cluster_count: int


def evaluate_development_estimand_realizations(
    dependence_bundle: DependenceAccountingBundle,
    *,
    protocol: Any,
    estimand: Any,
    feature_view: Any,
    objective_artifact: ObjectiveArtifact,
    experiment_registry: ExperimentRegistry,
) -> DevelopmentEstimandEvaluationBundle:
    """Evaluate preregistered Estimand & FeatureView realizations over DEVELOPMENT data (D1-17, AP-1 §3..4)."""
    if not isinstance(estimand, EstimandArtifact):
        raise SelectionBlockedError(
            f"{S8_EVALUATION_WITHOUT_PREREGISTERED_ESTIMAND}: preregistered EstimandArtifact required (I-EST-1)"
        )
    if not isinstance(feature_view, FeatureViewSpec):
        raise SelectionBlockedError(
            f"{S8_INVALID_FEATURE_VIEW_SPEC}: frozen FeatureViewSpec required (I-FVIEW-1)"
        )
    if not isinstance(dependence_bundle, DependenceAccountingBundle):
        raise SchemaViolation(
            "dependence_bundle must be a DependenceAccountingBundle"
        )

    sg_bundle = dependence_bundle.state_graph_bundle
    wb = sg_bundle.wave_bundle

    verify_development_protocol_dependency_closure(
        protocol,
        estimand=estimand,
        feature_view=feature_view,
        state_catalog=sg_bundle.state_catalog,
        graph_spec=sg_bundle.graph_spec,
        dependence_contract=dependence_bundle.contract,
        objective_artifact=objective_artifact,
        experiment_registry=experiment_registry,
    )

    if wb.dataset_id != protocol.dataset_id or wb.dataset_role != protocol.dataset_role:
        raise SelectionBlockedError(
            f"{S8_PROTOCOL_DEPENDENCY_CLOSURE_MISMATCH}: wave_bundle dataset mismatch with protocol"
        )
    if wb.dataset_role not in estimand.permitted_dataset_roles:
        raise SelectionBlockedError(
            f"{S8_FINAL_DATASET_FORBIDDEN_IN_DEVELOPMENT_PROTOCOL}: dataset_role {wb.dataset_role!r} not permitted by estimand"
        )

    # Map episode_id by wave_process_id
    ep_by_wp = {
        anc.anchor_wave_process_id: anc.episode_id
        for anc in dependence_bundle.episode_anchors
    }

    # Index state observations by (wave_process_id, variable_id)
    state_obs_by_wp_var: dict[Tuple[str, str], Any] = {}
    for sobs in sg_bundle.state_observations:
        state_obs_by_wp_var[(sobs.wave_process_id, sobs.variable_id)] = sobs

    geoms = wb.finalized_wave_geometries
    dataset_end_key = wb.observation_keys[-1]

    realizations: list[EstimandRealizationRecord] = []
    uncensored_cnt = 0
    censored_cnt = 0

    for idx, fg in enumerate(geoms):
        decision_key = fg.wave_end_confirmed_key
        feat_map: dict[str, Union[MetricResult, TypedState, str]] = {}
        for var_id in feature_view.selected_state_variable_refs:
            sobs = state_obs_by_wp_var.get((fg.wave_process_id, var_id))
            if sobs is None:
                feat_map[var_id] = TypedState.MISSING
            else:
                # I-FVIEW-3: FeatureView cannot access state/fact unavailable at evaluation key
                require_visible_at(
                    fact_key=sobs.observation_key, at_key=decision_key
                )
                feat_map[var_id] = sobs.state_value

        ep_id = ep_by_wp[fg.wave_process_id]
        # Check if a subsequent confirmed wave exists within the dataset
        if idx + 1 < len(geoms):
            next_fg = geoms[idx + 1]
            res_key = next_fg.wave_end_confirmed_key
            c_status = CENSORING_STATUS_UNCENSORED
            uncensored_cnt += 1

            if (
                estimand.future_observable_kind
                == OBSERVABLE_SUBSEQUENT_WAVE_EFFICIENCY
            ):
                out_val = next_fg.final_efficiency_ratio
                fav: Union[bool, TypedState] = (
                    isinstance(next_fg.final_efficiency_ratio, MetricResult)
                    and isinstance(fg.final_efficiency_ratio, MetricResult)
                    and next_fg.final_efficiency_ratio.value
                    >= fg.final_efficiency_ratio.value
                )
            else:
                if abs(fg.final_displacement.value) <= 0.0:
                    out_val = TypedState.UNDEFINED
                    fav = TypedState.UNDEFINED
                else:
                    ratio = abs(next_fg.final_displacement.value) / abs(
                        fg.final_displacement.value
                    )
                    out_val = exact_metric(ratio)
                    fav = ratio >= 1.0
        else:
            res_key = dataset_end_key
            c_status = CENSORING_STATUS_RIGHT_CENSORED
            out_val = TypedState.UNAVAILABLE
            fav = TypedState.UNAVAILABLE
            censored_cnt += 1

        realizations.append(
            EstimandRealizationRecord(
                realization_id=f"real:{protocol.protocol_id}:{fg.wave_process_id}",
                protocol_hash=protocol.protocol_hash,
                estimand_hash=estimand.estimand_hash,
                feature_view_hash=feature_view.feature_view_hash,
                episode_id=ep_id,
                wave_process_id=fg.wave_process_id,
                decision_key=decision_key,
                outcome_resolution_key=res_key,
                feature_values=feat_map,
                censoring_status=c_status,
                outcome_value=out_val,
                favorable_structural_continuation=fav,
            )
        )

    return DevelopmentEstimandEvaluationBundle(
        protocol=protocol,
        estimand=estimand,
        feature_view=feature_view,
        realizations=tuple(realizations),
        uncensored_count=uncensored_cnt,
        right_censored_count=censored_cnt,
        non_overlapping_span_cluster_count=dependence_bundle.non_overlapping_span_cluster_count,
    )


__all__ = [
    "CENSORING_STATUS_RIGHT_CENSORED",
    "CENSORING_STATUS_UNCENSORED",
    "DEVELOPMENT_EVALUATION_PROTOCOL_SCHEMA",
    "DevelopmentEstimandEvaluationBundle",
    "DevelopmentEvaluationProtocol",
    "ESTIMAND_ARTIFACT_SCHEMA",
    "EstimandArtifact",
    "EstimandCatalog",
    "EstimandRealizationRecord",
    "FEATURE_VIEW_SPEC_SCHEMA",
    "FeatureViewSpec",
    "LEGAL_CENSORING_STATUSES",
    "LEGAL_FUTURE_OBSERVABLE_KINDS",
    "OBSERVABLE_COMPETING_BOUNDARY_FIRST_PASSAGE",
    "OBSERVABLE_SUBSEQUENT_WAVE_DISPLACEMENT_RATIO",
    "OBSERVABLE_SUBSEQUENT_WAVE_EFFICIENCY",
    "S8_DUPLICATE_ESTIMAND_REGISTRATION",
    "S8_EVALUATION_WITHOUT_PREREGISTERED_ESTIMAND",
    "S8_FEATURE_VIEW_CATALOG_OR_ESTIMAND_MISMATCH",
    "S8_FEATURE_VIEW_UNDECLARED_VARIABLE",
    "S8_FINAL_DATASET_FORBIDDEN_IN_DEVELOPMENT_PROTOCOL",
    "S8_INVALID_DEVELOPMENT_EVALUATION_PROTOCOL",
    "S8_INVALID_ESTIMAND_ARTIFACT",
    "S8_INVALID_FEATURE_VIEW_SPEC",
    "S8_PROTOCOL_DEPENDENCY_CLOSURE_MISMATCH",
    "S8_SCHEMA_IDENTITY",
    "S8_SCHEMA_VERSION",
    "S8_UNDEFINED_STATE_VARIABLE_IN_ESTIMAND",
    "S8_UNKNOWN_ESTIMAND_REF",
    "evaluate_development_estimand_realizations",
    "verify_development_protocol_dependency_closure",
]
