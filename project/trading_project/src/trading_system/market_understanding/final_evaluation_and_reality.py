"""MUF V1 S13, S14, S15: Final Evaluation Run, Exposure Ledger, and Reality / Causal Market Understanding Surface.

Implements D1-3, D1-15, D1-20, D2-5, D2-6, D2-10, D2-22, Correction-1 §3, §4, and AP-1 §4:
1. S13 (``open_and_run_final_evaluation_once``, ``request_post_open_protocol_output``):
   - Requires a valid ``GateG3OpenFinalAuthorizationDecision`` (``GATE_G3_AUTHORIZED_TO_OPEN``),
     ``FrozenRepresentationBundle``, ``EvaluationProtocolArtifact``, and ``EvaluationProtocolEventLedger``.
   - Enforces ``I-SG-1B`` (bundle dependency closure), ``I-EVAL-1..6`` (once per protocol+lineage,
     ``allowed_outputs`` enforcement, post-open unpermitted outputs logged as ``EXPLORATORY_OUTPUT_REQUESTED``),
     and ``I-EVP-2`` (``protocol_hash`` byte-identical before and after ``OPENED``).
2. S14 (``FinalEvaluationOutcomeRecord`` & ``FinalEvaluationExposureRegistry``):
   - Irreversibly records final evaluation outcomes (including negative outcomes, ``I-FE-2``, Attack 49)
     and marks ``dataset_ancestry_root`` as ``EXPOSED_FINAL``.
   - Enforces ``D1-20`` & ``I-FE-1`` (Attacks 22 & 49): reusing an exposed ``dataset_ancestry_root``
     for a modified lineage fails closed with ``EXPOSED_INVALID_FOR_FINAL_SELECTION`` unless a
     certified ``EquivalenceClaimArtifact`` (``EQUIVALENCE_RESULT_CERTIFIED``) proves claim equivalence.
3. S15 (``ExplanationStateRecord``, ``RealityAuditSurfaceRecord``, ``CausalMarketUnderstandingDiagnosticReport``,
   and ``analyze_causal_market_state_as_of``):
   - Enforces ``D1-15`` & ``I-EXPL-1`` (Attack 24): explanation states are strictly limited to
     ``{MONITORING, PATTERN_REQUIREMENTS_SATISFIED, CONTRADICTED, SUPERSEDED}``; forbidden states
     (``PROBABLE``, ``LIKELY``, ``SUPPORTED``, ``WINNING_EXPLANATION``, ``FACTUALLY_ESTABLISHED_WHERE_POSSIBLE``)
     and numerical probability/weight claims fail closed.
   - Enforces ``D1-3``, ``I-HR-1..2``, ``I-DR-3``, ``Correction-1 §4`` (Attack 12): Reality audit on
     ``FINAL_EVALUATION_LOCKED`` data that requests design changes triggers ``EXPOSED_INVALID_FOR_FINAL_SELECTION``.
   - Provides ``analyze_causal_market_state_as_of``: ultra-fast real-time causal market understanding
     diagnostics at any ``query_key: InformationKey``.
"""
from dataclasses import dataclass
from typing import Any, Final, Mapping, Optional, Sequence, Tuple, Union

from trading_system.market_understanding.availability import require_visible_at
from trading_system.market_understanding.contracts import (
    IllegalCausalReference,
    ImmutabilityViolation,
    SchemaIdentity,
    SchemaViolation,
    TypedState,
)
from trading_system.market_understanding.dependence_accounting import (
    DependenceAccountingBundle,
    RESEARCH_DEBT_024_STANDING_STATUS,
    STATISTICAL_INDEPENDENCE_STANDING_CLAIM,
    query_dependence_accounting_as_of,
)
from trading_system.market_understanding.freeze_and_readiness import (
    EQUIVALENCE_RESULT_CERTIFIED,
    GATE_G3_AUTHORIZED_TO_OPEN,
    PROTOCOL_EVENT_EXPLORATORY_OUTPUT_REQUESTED,
    PROTOCOL_EVENT_OPENED,
    PROTOCOL_EVENT_OUTPUT_EMITTED,
    EquivalenceClaimArtifact,
    EvaluationProtocolArtifact,
    EvaluationProtocolEvent,
    EvaluationProtocolEventLedger,
    FrozenRepresentationBundle,
    GateG3OpenFinalAuthorizationDecision,
    verify_final_protocol_bundle_closure,
)
from trading_system.market_understanding.identity import (
    ArtifactIdentitySchema,
    canonical_artifact_identity,
)
from trading_system.market_understanding.policy_governance import (
    DATASET_ROLE_DEVELOPMENT_FIT,
    DATASET_ROLE_DEVELOPMENT_SELECTION,
    DATASET_ROLE_FINAL_EVALUATION_LOCKED,
    EXPOSURE_STATE_EXPOSED_INVALID_FOR_FINAL,
    SelectionBlockedError,
)
from trading_system.market_understanding.price_path import (
    MetricResult,
    exact_metric,
)
from trading_system.market_understanding.records import ImmutableRecord
from trading_system.market_understanding.state_graph import (
    query_state_graph_as_of,
)
from trading_system.market_understanding.wave_representation import (
    query_wave_representation_as_of,
)
from trading_system.research.information_time import (
    InformationKey,
    InformationPhase,
)


S13_S15_SCHEMA_VERSION: Final[str] = "MUF_S13_S15_FINAL_EVAL_AND_REALITY_V1"
S13_S15_SCHEMA_IDENTITY: Final[SchemaIdentity] = SchemaIdentity(
    "MUF_S13_S15_FINAL_EVAL_AND_REALITY", "V1"
)

FINAL_EVALUATION_OUTCOME_SCHEMA: Final[ArtifactIdentitySchema] = (
    ArtifactIdentitySchema(
        artifact_type="MUF_S13_S14_FINAL_EVALUATION_OUTCOME",
        schema_identity=S13_S15_SCHEMA_IDENTITY,
        identity_defining_fields=(
            "outcome_record_id",
            "evaluation_protocol_id",
            "protocol_hash",
            "frozen_bundle_id",
            "artifact_lineage_id",
            "dataset_identity",
            "dataset_ancestry_root",
            "emitted_allowed_outputs",
            "primary_outcome_metric",
            "outcome_polarity",
            "opened_at_key",
            "exposure_status",
        ),
    )
)

EXPLANATION_STATE_RECORD_SCHEMA: Final[ArtifactIdentitySchema] = (
    ArtifactIdentitySchema(
        artifact_type="MUF_S15_EXPLANATION_STATE_RECORD",
        schema_identity=S13_S15_SCHEMA_IDENTITY,
        identity_defining_fields=(
            "explanation_id",
            "pattern_contract_ref",
            "explanation_state",
            "required_fact_refs",
            "contradicting_fact_refs",
            "same_information_batch_order_unknown",
            "explanation_information_key",
        ),
    )
)

REALITY_AUDIT_SURFACE_SCHEMA: Final[ArtifactIdentitySchema] = (
    ArtifactIdentitySchema(
        artifact_type="MUF_S15_REALITY_AUDIT_SURFACE_RECORD",
        schema_identity=S13_S15_SCHEMA_IDENTITY,
        identity_defining_fields=(
            "audit_record_id",
            "dataset_identity",
            "dataset_ancestry_root",
            "dataset_role",
            "artifact_lineage_id",
            "requested_design_changes",
            "resulting_exposure_status",
            "requires_new_lineage",
            "audit_information_key",
        ),
    )
)

# Explanation state whitelist & forbidden terms (D1-15, I-EXPL-1, Attack 24)
EXPLANATION_STATE_MONITORING: Final[str] = "MONITORING"
EXPLANATION_STATE_PATTERN_SATISFIED: Final[str] = (
    "PATTERN_REQUIREMENTS_SATISFIED"
)
EXPLANATION_STATE_CONTRADICTED: Final[str] = "CONTRADICTED"
EXPLANATION_STATE_SUPERSEDED: Final[str] = "SUPERSEDED"

VALID_EXPLANATION_STATES: Final[Tuple[str, ...]] = (
    EXPLANATION_STATE_MONITORING,
    EXPLANATION_STATE_PATTERN_SATISFIED,
    EXPLANATION_STATE_CONTRADICTED,
    EXPLANATION_STATE_SUPERSEDED,
)

FORBIDDEN_EXPLANATION_STATES: Final[Tuple[str, ...]] = (
    "PROBABLE",
    "LIKELY",
    "SUPPORTED",
    "WINNING_EXPLANATION",
    "FACTUALLY_ESTABLISHED_WHERE_POSSIBLE",
)

# Exposure statuses
EXPOSURE_STATUS_EXPOSED_FINAL: Final[str] = "EXPOSED_FINAL"
EXPOSURE_STATUS_DEVELOPMENT_ONLY: Final[str] = "EXPOSED_DEVELOPMENT_ONLY"

# Outcome polarities (I-FE-2: both POSITIVE and NEGATIVE outcomes are permanently recorded)
OUTCOME_POLARITY_FAVORABLE: Final[str] = "FAVORABLE"
OUTCOME_POLARITY_UNFAVORABLE: Final[str] = "UNFAVORABLE"
OUTCOME_POLARITY_NEUTRAL: Final[str] = "NEUTRAL"

# Deterministic error codes
S13_INVALID_FINAL_EVALUATION: Final[str] = "S13_INVALID_FINAL_EVALUATION"
S13_UNPERMITTED_FINAL_OUTPUT_REQUESTED: Final[str] = (
    "S13_UNPERMITTED_FINAL_OUTPUT_REQUESTED"
)
S14_EXPOSED_DATASET_LINEAGE_REUSE_BLOCKED: Final[str] = (
    "EXPOSED_INVALID_FOR_FINAL_SELECTION"
)
S14_NEGATIVE_RESULT_DELETION_FORBIDDEN: Final[str] = (
    "S14_NEGATIVE_RESULT_DELETION_FORBIDDEN"
)
S15_FORBIDDEN_EXPLANATION_STATE_OR_WEIGHT: Final[str] = (
    "S15_FORBIDDEN_EXPLANATION_STATE_OR_WEIGHT"
)
S15_INVALID_REALITY_AUDIT_RECORD: Final[str] = (
    "S15_INVALID_REALITY_AUDIT_RECORD"
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


@dataclass(frozen=True)
class FinalEvaluationOutcomeRecord(ImmutableRecord):
    """Irreversible S13/S14 final evaluation outcome record (D1-20, D2-5, I-EVAL-1..6, I-FE-1..2)."""

    outcome_record_id: str
    evaluation_protocol_id: str
    protocol_hash: str
    frozen_bundle_id: str
    artifact_lineage_id: str
    dataset_identity: str
    dataset_ancestry_root: str
    emitted_allowed_outputs: Tuple[str, ...]
    primary_outcome_metric: MetricResult
    outcome_polarity: str
    opened_at_key: InformationKey
    exposure_status: str
    outcome_record_hash: str

    def __post_init__(self) -> None:
        for f_name, f_val in (
            ("outcome_record_id", self.outcome_record_id),
            ("evaluation_protocol_id", self.evaluation_protocol_id),
            ("protocol_hash", self.protocol_hash),
            ("frozen_bundle_id", self.frozen_bundle_id),
            ("artifact_lineage_id", self.artifact_lineage_id),
            ("dataset_identity", self.dataset_identity),
            ("dataset_ancestry_root", self.dataset_ancestry_root),
        ):
            _require_non_empty_str(f_val, f_name, S13_INVALID_FINAL_EVALUATION)

        emitted = _require_str_tuple(
            self.emitted_allowed_outputs,
            "emitted_allowed_outputs",
            S13_INVALID_FINAL_EVALUATION,
        )
        object.__setattr__(self, "emitted_allowed_outputs", emitted)

        if not isinstance(self.primary_outcome_metric, MetricResult):
            raise SchemaViolation(
                f"{S13_INVALID_FINAL_EVALUATION}: primary_outcome_metric must be a MetricResult"
            )
        if self.outcome_polarity not in (
            OUTCOME_POLARITY_FAVORABLE,
            OUTCOME_POLARITY_UNFAVORABLE,
            OUTCOME_POLARITY_NEUTRAL,
        ):
            raise SchemaViolation(
                f"{S13_INVALID_FINAL_EVALUATION}: invalid outcome_polarity {self.outcome_polarity!r}"
            )
        _require_completed_key(
            self.opened_at_key, "opened_at_key", S13_INVALID_FINAL_EVALUATION
        )
        if self.exposure_status != EXPOSURE_STATUS_EXPOSED_FINAL:
            raise SchemaViolation(
                f"{S13_INVALID_FINAL_EVALUATION}: exposure_status must be {EXPOSURE_STATUS_EXPOSED_FINAL!r}"
            )

        expected_hash = canonical_artifact_identity(
            FINAL_EVALUATION_OUTCOME_SCHEMA,
            identity_payload={
                "outcome_record_id": self.outcome_record_id,
                "evaluation_protocol_id": self.evaluation_protocol_id,
                "protocol_hash": self.protocol_hash,
                "frozen_bundle_id": self.frozen_bundle_id,
                "artifact_lineage_id": self.artifact_lineage_id,
                "dataset_identity": self.dataset_identity,
                "dataset_ancestry_root": self.dataset_ancestry_root,
                "emitted_allowed_outputs": _serialize_seq(emitted),
                "primary_outcome_metric": repr(
                    self.primary_outcome_metric.value
                ),
                "outcome_polarity": self.outcome_polarity,
                "opened_at_key": self.opened_at_key,
                "exposure_status": self.exposure_status,
            },
        )
        if self.outcome_record_hash != expected_hash:
            raise SchemaViolation(
                f"{S13_INVALID_FINAL_EVALUATION}: outcome_record_hash mismatch"
            )


class FinalEvaluationExposureRegistry:
    """Append-only S14 registry of final evaluation outcomes and exposed dataset ancestry roots (D1-20, I-FE-1..2)."""

    def __init__(self) -> None:
        self.__outcomes_by_id: dict[str, FinalEvaluationOutcomeRecord] = {}
        self.__outcomes_by_ancestry: dict[
            str, list[FinalEvaluationOutcomeRecord]
        ] = {}
        self.__invalidated_ancestry_roots: set[str] = set()

    def record_outcome(
        self, outcome: FinalEvaluationOutcomeRecord
    ) -> FinalEvaluationOutcomeRecord:
        if not isinstance(outcome, FinalEvaluationOutcomeRecord):
            raise SchemaViolation(
                f"{S13_INVALID_FINAL_EVALUATION}: expected FinalEvaluationOutcomeRecord"
            )
        by_id = object.__getattribute__(
            self, "_FinalEvaluationExposureRegistry__outcomes_by_id"
        )
        if outcome.outcome_record_id in by_id:
            raise ImmutabilityViolation(
                f"{S13_INVALID_FINAL_EVALUATION}: outcome {outcome.outcome_record_id!r} already recorded"
            )
        by_id[outcome.outcome_record_id] = outcome
        by_anc = object.__getattribute__(
            self, "_FinalEvaluationExposureRegistry__outcomes_by_ancestry"
        )
        by_anc.setdefault(outcome.dataset_ancestry_root, []).append(outcome)
        return outcome

    def delete_outcome(self, outcome_record_id: str) -> None:
        """Deleting or hiding any final evaluation outcome (positive or negative) is strictly forbidden (I-FE-2, Attack 49)."""
        raise ImmutabilityViolation(
            f"{S14_NEGATIVE_RESULT_DELETION_FORBIDDEN}: final evaluation outcome {outcome_record_id!r} cannot be deleted (I-FE-2)"
        )

    def mark_ancestry_invalid_for_final_selection(
        self, dataset_ancestry_root: str
    ) -> None:
        inv = object.__getattribute__(
            self, "_FinalEvaluationExposureRegistry__invalidated_ancestry_roots"
        )
        inv.add(dataset_ancestry_root)

    def all_outcomes_for_ancestry(
        self, dataset_ancestry_root: str
    ) -> Tuple[FinalEvaluationOutcomeRecord, ...]:
        by_anc = object.__getattribute__(
            self, "_FinalEvaluationExposureRegistry__outcomes_by_ancestry"
        )
        return tuple(by_anc.get(dataset_ancestry_root, ()))

    def all_outcomes(self) -> Tuple[FinalEvaluationOutcomeRecord, ...]:
        by_id = object.__getattribute__(
            self, "_FinalEvaluationExposureRegistry__outcomes_by_id"
        )
        return tuple(by_id.values())

    def verify_ancestry_eligible_for_lineage(
        self,
        *,
        dataset_ancestry_root: str,
        artifact_lineage_id: str,
        equivalence_claim: Optional[EquivalenceClaimArtifact] = None,
    ) -> bool:
        """Enforce D1-20 & I-FE-1 (Attacks 22 & 49): exposed final dataset cannot be reused by a modified lineage unless certified equivalent."""
        inv = object.__getattribute__(
            self, "_FinalEvaluationExposureRegistry__invalidated_ancestry_roots"
        )
        if dataset_ancestry_root in inv:
            raise SelectionBlockedError(
                f"{S14_EXPOSED_DATASET_LINEAGE_REUSE_BLOCKED}: dataset_ancestry_root {dataset_ancestry_root!r} "
                "is invalidated for final selection (Attack 12 / Attack 22)"
            )
        prior_outcomes = self.all_outcomes_for_ancestry(dataset_ancestry_root)
        if len(prior_outcomes) == 0:
            return True

        # Dataset ancestry root was already exposed in a prior final evaluation!
        if (
            equivalence_claim is not None
            and isinstance(equivalence_claim, EquivalenceClaimArtifact)
            and equivalence_claim.equivalence_result
            == EQUIVALENCE_RESULT_CERTIFIED
        ):
            return True

        raise SelectionBlockedError(
            f"{S14_EXPOSED_DATASET_LINEAGE_REUSE_BLOCKED}: dataset_ancestry_root {dataset_ancestry_root!r} "
            f"was already exposed under lineage {prior_outcomes[0].artifact_lineage_id!r} and cannot be "
            f"reused as independent final evidence for lineage {artifact_lineage_id!r} (D1-20, I-FE-1, Attack 22/49)"
        )


def open_and_run_final_evaluation_once(
    *,
    outcome_record_id: str,
    gate_g3_decision: GateG3OpenFinalAuthorizationDecision,
    frozen_bundle: FrozenRepresentationBundle,
    protocol: EvaluationProtocolArtifact,
    event_ledger: EvaluationProtocolEventLedger,
    exposure_registry: FinalEvaluationExposureRegistry,
    requested_outputs: Sequence[str],
    primary_outcome_metric: MetricResult,
    outcome_polarity: str,
    open_key: InformationKey,
    equivalence_claim: Optional[EquivalenceClaimArtifact] = None,
) -> FinalEvaluationOutcomeRecord:
    """Execute S13 Final Evaluation once under Gate G3 and record S14 irreversible exposure (D1-20, D2-5, I-EVAL-1..6)."""
    if (
        not isinstance(gate_g3_decision, GateG3OpenFinalAuthorizationDecision)
        or gate_g3_decision.gate_g3_status != GATE_G3_AUTHORIZED_TO_OPEN
    ):
        raise SelectionBlockedError(
            f"{S13_INVALID_FINAL_EVALUATION}: valid GateG3OpenFinalAuthorizationDecision required"
        )
    if (
        gate_g3_decision.bundle_id != frozen_bundle.bundle_id
        or gate_g3_decision.evaluation_protocol_id
        != protocol.evaluation_protocol_id
    ):
        raise SelectionBlockedError(
            f"{S13_INVALID_FINAL_EVALUATION}: Gate G3 decision does not match bundle_id or protocol_id"
        )
    verify_final_protocol_bundle_closure(
        protocol, frozen_bundle=frozen_bundle
    )
    exposure_registry.verify_ancestry_eligible_for_lineage(
        dataset_ancestry_root=protocol.dataset_ancestry_root,
        artifact_lineage_id=frozen_bundle.artifact_lineage_id,
        equivalence_claim=equivalence_claim,
    )

    req_out = _require_str_tuple(
        requested_outputs, "requested_outputs", S13_INVALID_FINAL_EVALUATION
    )
    allowed_set = set(protocol.allowed_outputs)
    for out_name in req_out:
        if out_name not in allowed_set:
            raise SelectionBlockedError(
                f"{S13_UNPERMITTED_FINAL_OUTPUT_REQUESTED}: requested output {out_name!r} "
                "is not in protocol.allowed_outputs (I-EVAL-5, Attack 30/48)"
            )

    hash_before = protocol.protocol_hash
    event_ledger.append_event(
        protocol_id=protocol.evaluation_protocol_id,
        event_type=PROTOCOL_EVENT_OPENED,
        event_information_key=open_key,
        payload_ref=f"open:{outcome_record_id}",
    )
    event_ledger.append_event(
        protocol_id=protocol.evaluation_protocol_id,
        event_type=PROTOCOL_EVENT_OUTPUT_EMITTED,
        event_information_key=open_key,
        payload_ref=",".join(req_out),
    )
    assert protocol.protocol_hash == hash_before

    out_hash = canonical_artifact_identity(
        FINAL_EVALUATION_OUTCOME_SCHEMA,
        identity_payload={
            "outcome_record_id": outcome_record_id,
            "evaluation_protocol_id": protocol.evaluation_protocol_id,
            "protocol_hash": protocol.protocol_hash,
            "frozen_bundle_id": frozen_bundle.bundle_id,
            "artifact_lineage_id": frozen_bundle.artifact_lineage_id,
            "dataset_identity": protocol.dataset_identity,
            "dataset_ancestry_root": protocol.dataset_ancestry_root,
            "emitted_allowed_outputs": _serialize_seq(req_out),
            "primary_outcome_metric": repr(primary_outcome_metric.value),
            "outcome_polarity": outcome_polarity,
            "opened_at_key": open_key,
            "exposure_status": EXPOSURE_STATUS_EXPOSED_FINAL,
        },
    )
    record = FinalEvaluationOutcomeRecord(
        outcome_record_id=outcome_record_id,
        evaluation_protocol_id=protocol.evaluation_protocol_id,
        protocol_hash=protocol.protocol_hash,
        frozen_bundle_id=frozen_bundle.bundle_id,
        artifact_lineage_id=frozen_bundle.artifact_lineage_id,
        dataset_identity=protocol.dataset_identity,
        dataset_ancestry_root=protocol.dataset_ancestry_root,
        emitted_allowed_outputs=req_out,
        primary_outcome_metric=primary_outcome_metric,
        outcome_polarity=outcome_polarity,
        opened_at_key=open_key,
        exposure_status=EXPOSURE_STATUS_EXPOSED_FINAL,
        outcome_record_hash=out_hash,
    )
    exposure_registry.record_outcome(record)
    return record


def request_post_open_protocol_output(
    *,
    protocol: EvaluationProtocolArtifact,
    event_ledger: EvaluationProtocolEventLedger,
    requested_output_name: str,
    request_key: InformationKey,
) -> EvaluationProtocolEvent:
    """Handle post-open output request: non-preregistered outputs are logged as EXPLORATORY_OUTPUT_REQUESTED only (I-EVAL-5, I-EVAL-6, Attack 30)."""
    _require_non_empty_str(
        requested_output_name,
        "requested_output_name",
        S13_INVALID_FINAL_EVALUATION,
    )
    return event_ledger.append_event(
        protocol_id=protocol.evaluation_protocol_id,
        event_type=PROTOCOL_EVENT_EXPLORATORY_OUTPUT_REQUESTED,
        event_information_key=request_key,
        payload_ref=f"exploratory_only_excluded_from_claim:{requested_output_name}",
    )


@dataclass(frozen=True)
class ExplanationStateRecord(ImmutableRecord):
    """Descriptive ExplanationStateRecord (D1-15, D2-10, I-EXPL-1, I-IKA-1, I-IB-1, Attack 10 & 24).

    Strictly limited to {MONITORING, PATTERN_REQUIREMENTS_SATISFIED, CONTRADICTED, SUPERSEDED}.
    Probability/likelihood/support claims or numerical weights fail closed.
    """

    explanation_id: str
    pattern_contract_ref: str
    explanation_state: str
    required_fact_refs: Tuple[str, ...]
    contradicting_fact_refs: Tuple[str, ...]
    same_information_batch_order_unknown: bool
    explanation_information_key: InformationKey
    probability_or_support_weight: TypedState
    explanation_hash: str

    def __post_init__(self) -> None:
        _require_non_empty_str(
            self.explanation_id,
            "explanation_id",
            S15_FORBIDDEN_EXPLANATION_STATE_OR_WEIGHT,
        )
        _require_non_empty_str(
            self.pattern_contract_ref,
            "pattern_contract_ref",
            S15_FORBIDDEN_EXPLANATION_STATE_OR_WEIGHT,
        )
        if (
            self.explanation_state in FORBIDDEN_EXPLANATION_STATES
            or self.explanation_state not in VALID_EXPLANATION_STATES
        ):
            raise SchemaViolation(
                f"{S15_FORBIDDEN_EXPLANATION_STATE_OR_WEIGHT}: explanation_state {self.explanation_state!r} "
                f"is forbidden; must be in {VALID_EXPLANATION_STATES} (D1-15, I-EXPL-1, Attack 24)"
            )
        if self.probability_or_support_weight is not TypedState.NOT_APPLICABLE:
            raise SchemaViolation(
                f"{S15_FORBIDDEN_EXPLANATION_STATE_OR_WEIGHT}: probability/support weights are forbidden "
                "on ExplanationStateRecord (I-EXPL-1, Attack 24)"
            )
        req_refs = _require_str_tuple(
            self.required_fact_refs,
            "required_fact_refs",
            S15_FORBIDDEN_EXPLANATION_STATE_OR_WEIGHT,
        )
        contra_refs = _require_str_tuple(
            self.contradicting_fact_refs,
            "contradicting_fact_refs",
            S15_FORBIDDEN_EXPLANATION_STATE_OR_WEIGHT,
            allow_empty=True,
        )
        object.__setattr__(self, "required_fact_refs", req_refs)
        object.__setattr__(self, "contradicting_fact_refs", contra_refs)

        if not isinstance(self.same_information_batch_order_unknown, bool):
            raise SchemaViolation(
                f"{S15_FORBIDDEN_EXPLANATION_STATE_OR_WEIGHT}: same_information_batch_order_unknown must be bool"
            )
        _require_completed_key(
            self.explanation_information_key,
            "explanation_information_key",
            S15_FORBIDDEN_EXPLANATION_STATE_OR_WEIGHT,
        )

        expected_hash = canonical_artifact_identity(
            EXPLANATION_STATE_RECORD_SCHEMA,
            identity_payload={
                "explanation_id": self.explanation_id,
                "pattern_contract_ref": self.pattern_contract_ref,
                "explanation_state": self.explanation_state,
                "required_fact_refs": _serialize_seq(req_refs),
                "contradicting_fact_refs": _serialize_seq(contra_refs),
                "same_information_batch_order_unknown": str(
                    self.same_information_batch_order_unknown
                ),
                "explanation_information_key": self.explanation_information_key,
            },
        )
        if self.explanation_hash != expected_hash:
            raise SchemaViolation(
                f"{S15_FORBIDDEN_EXPLANATION_STATE_OR_WEIGHT}: explanation_hash mismatch"
            )

    @classmethod
    def create(
        cls,
        *,
        explanation_id: str,
        pattern_contract_ref: str,
        explanation_state: str,
        required_fact_refs: Sequence[str],
        contradicting_fact_refs: Sequence[str] = (),
        same_information_batch_order_unknown: bool = False,
        explanation_information_key: InformationKey,
        probability_or_support_weight: Any = TypedState.NOT_APPLICABLE,
    ) -> "ExplanationStateRecord":
        req_refs = _require_str_tuple(
            required_fact_refs,
            "required_fact_refs",
            S15_FORBIDDEN_EXPLANATION_STATE_OR_WEIGHT,
        )
        contra_refs = _require_str_tuple(
            contradicting_fact_refs,
            "contradicting_fact_refs",
            S15_FORBIDDEN_EXPLANATION_STATE_OR_WEIGHT,
            allow_empty=True,
        )
        e_hash = canonical_artifact_identity(
            EXPLANATION_STATE_RECORD_SCHEMA,
            identity_payload={
                "explanation_id": explanation_id,
                "pattern_contract_ref": pattern_contract_ref,
                "explanation_state": explanation_state,
                "required_fact_refs": _serialize_seq(req_refs),
                "contradicting_fact_refs": _serialize_seq(contra_refs),
                "same_information_batch_order_unknown": str(
                    same_information_batch_order_unknown
                ),
                "explanation_information_key": explanation_information_key,
            },
        )
        return cls(
            explanation_id=explanation_id,
            pattern_contract_ref=pattern_contract_ref,
            explanation_state=explanation_state,
            required_fact_refs=req_refs,
            contradicting_fact_refs=contra_refs,
            same_information_batch_order_unknown=same_information_batch_order_unknown,
            explanation_information_key=explanation_information_key,
            probability_or_support_weight=probability_or_support_weight,
            explanation_hash=e_hash,
        )


@dataclass(frozen=True)
class RealityAuditSurfaceRecord(ImmutableRecord):
    """Role-gated S15 Reality Audit Surface record (D1-3, Correction-1 §4, I-HR-1..2, I-DR-3, Attack 12)."""

    audit_record_id: str
    dataset_identity: str
    dataset_ancestry_root: str
    dataset_role: str
    artifact_lineage_id: str
    requested_design_changes: Tuple[str, ...]
    resulting_exposure_status: str
    requires_new_lineage: bool
    audit_information_key: InformationKey
    audit_record_hash: str

    def __post_init__(self) -> None:
        for f_name, f_val in (
            ("audit_record_id", self.audit_record_id),
            ("dataset_identity", self.dataset_identity),
            ("dataset_ancestry_root", self.dataset_ancestry_root),
            ("dataset_role", self.dataset_role),
            ("artifact_lineage_id", self.artifact_lineage_id),
            ("resulting_exposure_status", self.resulting_exposure_status),
        ):
            _require_non_empty_str(
                f_val, f_name, S15_INVALID_REALITY_AUDIT_RECORD
            )
        req_changes = _require_str_tuple(
            self.requested_design_changes,
            "requested_design_changes",
            S15_INVALID_REALITY_AUDIT_RECORD,
            allow_empty=True,
        )
        object.__setattr__(self, "requested_design_changes", req_changes)
        if not isinstance(self.requires_new_lineage, bool):
            raise SchemaViolation(
                f"{S15_INVALID_REALITY_AUDIT_RECORD}: requires_new_lineage must be bool"
            )
        _require_completed_key(
            self.audit_information_key,
            "audit_information_key",
            S15_INVALID_REALITY_AUDIT_RECORD,
        )
        expected_hash = canonical_artifact_identity(
            REALITY_AUDIT_SURFACE_SCHEMA,
            identity_payload={
                "audit_record_id": self.audit_record_id,
                "dataset_identity": self.dataset_identity,
                "dataset_ancestry_root": self.dataset_ancestry_root,
                "dataset_role": self.dataset_role,
                "artifact_lineage_id": self.artifact_lineage_id,
                "requested_design_changes": _serialize_seq(req_changes),
                "resulting_exposure_status": self.resulting_exposure_status,
                "requires_new_lineage": str(self.requires_new_lineage),
                "audit_information_key": self.audit_information_key,
            },
        )
        if self.audit_record_hash != expected_hash:
            raise SchemaViolation(
                f"{S15_INVALID_REALITY_AUDIT_RECORD}: audit_record_hash mismatch"
            )

    @classmethod
    def create(
        cls,
        *,
        audit_record_id: str,
        dataset_identity: str,
        dataset_ancestry_root: str,
        dataset_role: str,
        artifact_lineage_id: str,
        requested_design_changes: Sequence[str] = (),
        audit_information_key: InformationKey,
        exposure_registry: Optional[FinalEvaluationExposureRegistry] = None,
    ) -> "RealityAuditSurfaceRecord":
        req_changes = _require_str_tuple(
            requested_design_changes,
            "requested_design_changes",
            S15_INVALID_REALITY_AUDIT_RECORD,
            allow_empty=True,
        )
        if dataset_role == DATASET_ROLE_FINAL_EVALUATION_LOCKED and len(
            req_changes
        ) > 0:
            exp_status = EXPOSURE_STATE_EXPOSED_INVALID_FOR_FINAL
            req_new_lin = True
            if exposure_registry is not None:
                exposure_registry.mark_ancestry_invalid_for_final_selection(
                    dataset_ancestry_root
                )
        elif dataset_role == DATASET_ROLE_FINAL_EVALUATION_LOCKED:
            exp_status = EXPOSURE_STATUS_EXPOSED_FINAL
            req_new_lin = False
        else:
            exp_status = EXPOSURE_STATUS_DEVELOPMENT_ONLY
            req_new_lin = False

        a_hash = canonical_artifact_identity(
            REALITY_AUDIT_SURFACE_SCHEMA,
            identity_payload={
                "audit_record_id": audit_record_id,
                "dataset_identity": dataset_identity,
                "dataset_ancestry_root": dataset_ancestry_root,
                "dataset_role": dataset_role,
                "artifact_lineage_id": artifact_lineage_id,
                "requested_design_changes": _serialize_seq(req_changes),
                "resulting_exposure_status": exp_status,
                "requires_new_lineage": str(req_new_lin),
                "audit_information_key": audit_information_key,
            },
        )
        return cls(
            audit_record_id=audit_record_id,
            dataset_identity=dataset_identity,
            dataset_ancestry_root=dataset_ancestry_root,
            dataset_role=dataset_role,
            artifact_lineage_id=artifact_lineage_id,
            requested_design_changes=req_changes,
            resulting_exposure_status=exp_status,
            requires_new_lineage=req_new_lin,
            audit_information_key=audit_information_key,
            audit_record_hash=a_hash,
        )


@dataclass(frozen=True)
class CausalMarketUnderstandingDiagnosticReport(ImmutableRecord):
    """Real-time as-of causal market understanding diagnostic report (S15)."""

    timeline_id: str
    query_key: InformationKey
    representation_spec_hash: str
    authority_policy_hash: str
    state_catalog_hash: str
    graph_spec_hash: str
    forming_wave_process_ids: Tuple[str, ...]
    confirmed_wave_process_ids: Tuple[str, ...]
    active_running_efficiency_ratio: Union[MetricResult, TypedState]
    latest_confirmed_wave_efficiency_ratio: Union[MetricResult, TypedState]
    latest_confirmed_relative_amplitude_ratio: Union[MetricResult, TypedState]
    visible_episode_count: int
    non_overlapping_span_cluster_count: int
    historical_uncensored_continuation_count: int
    historical_right_censored_count: int
    empirical_continuation_rate: Union[MetricResult, TypedState]
    explanation_record: ExplanationStateRecord
    statistical_independence_claim: str
    research_debt_024_status: str


def analyze_causal_market_state_as_of(
    dependence_bundle: DependenceAccountingBundle,
    *,
    query_key: InformationKey,
    pattern_contract_ref: str = "CAUSAL_WAVE_STATE_CONTINUATION_PATTERN_V1",
) -> CausalMarketUnderstandingDiagnosticReport:
    """Produce a real-time, strictly causal Market Understanding diagnostic report as of ``query_key``."""
    if not isinstance(dependence_bundle, DependenceAccountingBundle):
        raise SchemaViolation(
            "dependence_bundle must be a DependenceAccountingBundle"
        )
    _require_completed_key(
        query_key, "query_key", S15_INVALID_REALITY_AUDIT_RECORD
    )

    sg_bundle = dependence_bundle.state_graph_bundle
    wave_bundle = sg_bundle.wave_bundle

    wave_view = query_wave_representation_as_of(wave_bundle, at_key=query_key)
    sg_view = query_state_graph_as_of(sg_bundle, at_key=query_key)
    dep_view = query_dependence_accounting_as_of(
        dependence_bundle, at_key=query_key
    )

    if len(wave_view.visible_running_observations) > 0:
        active_run_eff = wave_view.visible_running_observations[
            -1
        ].running_efficiency_ratio
    else:
        active_run_eff = TypedState.UNAVAILABLE

    vis_geoms = wave_view.visible_finalized_geometries
    if len(vis_geoms) > 0:
        latest_conf_eff = vis_geoms[-1].final_efficiency_ratio
    else:
        latest_conf_eff = TypedState.UNAVAILABLE

    if len(vis_geoms) > 1:
        prev_amp = abs(vis_geoms[-1 - 1].final_displacement.value)
        curr_amp = abs(vis_geoms[-1].final_displacement.value)
        if prev_amp > 0.0:
            latest_rel_amp: Union[MetricResult, TypedState] = exact_metric(
                curr_amp / prev_amp
            )
        else:
            latest_rel_amp = TypedState.UNDEFINED
    else:
        latest_rel_amp = TypedState.UNAVAILABLE

    # Compute strictly causal empirical continuation distribution over visible confirmed wave pairs
    uncensored_pairs = 0
    favorable_continuations = 0
    for idx in range(len(vis_geoms) - 1):
        g_curr = vis_geoms[idx]
        g_next = vis_geoms[idx + 1]
        require_visible_at(
            fact_key=g_next.wave_end_confirmed_key, at_key=query_key
        )
        uncensored_pairs += 1
        if abs(g_curr.final_displacement.value) > 0.0:
            if (
                abs(g_next.final_displacement.value)
                >= abs(g_curr.final_displacement.value)
            ):
                favorable_continuations += 1

    right_censored_cnt = 1 if len(vis_geoms) > 0 else 0
    if uncensored_pairs > 0:
        emp_rate: Union[MetricResult, TypedState] = exact_metric(
            float(favorable_continuations) / float(uncensored_pairs)
        )
    else:
        emp_rate = TypedState.UNAVAILABLE

    if len(vis_geoms) > 0 and len(sg_view.visible_descriptor_observations) > 0:
        exp_state = EXPLANATION_STATE_PATTERN_SATISFIED
        req_refs: Tuple[str, ...] = (vis_geoms[-1].wave_process_id,)
    else:
        exp_state = EXPLANATION_STATE_MONITORING
        req_refs = ("AWAITING_CONFIRMED_WAVE_FACT",)

    exp_rec = ExplanationStateRecord.create(
        explanation_id=f"expl:{wave_bundle.timeline_id}:{query_key.bar_position}",
        pattern_contract_ref=pattern_contract_ref,
        explanation_state=exp_state,
        required_fact_refs=req_refs,
        explanation_information_key=query_key,
    )

    return CausalMarketUnderstandingDiagnosticReport(
        timeline_id=wave_bundle.timeline_id,
        query_key=query_key,
        representation_spec_hash=wave_bundle.representation_spec.representation_spec_hash,
        authority_policy_hash=wave_bundle.policy_artifact.policy_hash,
        state_catalog_hash=sg_bundle.state_catalog.state_catalog_hash,
        graph_spec_hash=sg_bundle.graph_spec.graph_spec_hash,
        forming_wave_process_ids=wave_view.forming_wave_process_ids,
        confirmed_wave_process_ids=wave_view.confirmed_wave_process_ids,
        active_running_efficiency_ratio=active_run_eff,
        latest_confirmed_wave_efficiency_ratio=latest_conf_eff,
        latest_confirmed_relative_amplitude_ratio=latest_rel_amp,
        visible_episode_count=dep_view.distinct_episode_count,
        non_overlapping_span_cluster_count=dep_view.non_overlapping_span_cluster_count,
        historical_uncensored_continuation_count=uncensored_pairs,
        historical_right_censored_count=right_censored_cnt,
        empirical_continuation_rate=emp_rate,
        explanation_record=exp_rec,
        statistical_independence_claim=STATISTICAL_INDEPENDENCE_STANDING_CLAIM,
        research_debt_024_status=RESEARCH_DEBT_024_STANDING_STATUS,
    )


__all__ = [
    "S13_S15_SCHEMA_VERSION",
    "S13_S15_SCHEMA_IDENTITY",
    "FINAL_EVALUATION_OUTCOME_SCHEMA",
    "EXPLANATION_STATE_RECORD_SCHEMA",
    "REALITY_AUDIT_SURFACE_SCHEMA",
    "EXPLANATION_STATE_MONITORING",
    "EXPLANATION_STATE_PATTERN_SATISFIED",
    "EXPLANATION_STATE_CONTRADICTED",
    "EXPLANATION_STATE_SUPERSEDED",
    "VALID_EXPLANATION_STATES",
    "FORBIDDEN_EXPLANATION_STATES",
    "EXPOSURE_STATUS_EXPOSED_FINAL",
    "EXPOSURE_STATUS_DEVELOPMENT_ONLY",
    "OUTCOME_POLARITY_FAVORABLE",
    "OUTCOME_POLARITY_UNFAVORABLE",
    "OUTCOME_POLARITY_NEUTRAL",
    "S13_INVALID_FINAL_EVALUATION",
    "S13_UNPERMITTED_FINAL_OUTPUT_REQUESTED",
    "S14_EXPOSED_DATASET_LINEAGE_REUSE_BLOCKED",
    "S14_NEGATIVE_RESULT_DELETION_FORBIDDEN",
    "S15_FORBIDDEN_EXPLANATION_STATE_OR_WEIGHT",
    "S15_INVALID_REALITY_AUDIT_RECORD",
    "FinalEvaluationOutcomeRecord",
    "FinalEvaluationExposureRegistry",
    "open_and_run_final_evaluation_once",
    "request_post_open_protocol_output",
    "ExplanationStateRecord",
    "RealityAuditSurfaceRecord",
    "CausalMarketUnderstandingDiagnosticReport",
    "analyze_causal_market_state_as_of",
]
