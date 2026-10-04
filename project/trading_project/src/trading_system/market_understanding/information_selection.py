"""MUF V1 S9 & Gate G2: Development Information Evaluation and Selection.

Implements D2-3, D2-4, D2-17, D2-22, and AP-1 §4.1..4.4:
1. ``CandidateInformationEvaluationRecord``: evaluates a structurally ELIGIBLE
   candidate representation under a preregistered ``DevelopmentEvaluationProtocol``,
   ``EstimandArtifact``, ``FeatureViewSpec``, and ``ObjectiveArtifact``
   (``OBJECTIVE_KIND_INFORMATION``), computing cluster-weighted empirical
   information scores across non-overlapping episode span clusters while
   preserving explicit right-censoring accounting.
2. ``GateG2InformationSelectionDecision`` & ``run_gate_g2_information_selection``:
   enforces Gate G2 (Stage B Information-Based Development Selection):
   - Requires prior ``ELIGIBLE`` structural qualification (``I-SEL-1``).
   - Blocks evaluation without preregistered ``EstimandArtifact`` / ``FeatureViewSpec``
     / ``DevelopmentEvaluationProtocol`` (``I-SEL-2``, ``I-FVIEW-1``, ``I-SG-1A``).
   - Forbids ``FINAL_EVALUATION_LOCKED`` dataset roles (``I-SEL-3``).
   - Returns ``GATE_G2_NOT_CONFIGURED`` with ``selected_winner_candidate_id = TypedState.NOT_CONFIGURED``
     when the information objective is ``TypedState.NOT_CONFIGURED`` or ``TypedState.UNDEFINED``,
     preserving the structurally ``ELIGIBLE`` candidate set without inventing a winner (``I-SEL-4``, ``D2-17``).
   - Rejects visual/human subjective preference as a tie-breaker (``I-SEL-5``) and
     preserves tied top candidates with ``GATE_G2_TIED_NO_UNIQUE_WINNER``.
   - Permanently records candidate evaluations in ``ExperimentRegistry`` (``I-ER-1..5``).
"""
from dataclasses import dataclass
from typing import Any, Final, Mapping, Sequence, Tuple, Union

from trading_system.market_understanding.contracts import (
    IllegalCausalReference,
    SchemaIdentity,
    SchemaViolation,
    TypedState,
)
from trading_system.market_understanding.dependence_accounting import (
    DependenceAccountingBundle,
    RESEARCH_DEBT_024_STANDING_STATUS,
)
from trading_system.market_understanding.estimand_catalog import (
    CENSORING_STATUS_UNCENSORED,
    DevelopmentEstimandEvaluationBundle,
    DevelopmentEvaluationProtocol,
    EstimandArtifact,
    FeatureViewSpec,
    evaluate_development_estimand_realizations,
)
from trading_system.market_understanding.identity import (
    ArtifactIdentitySchema,
    canonical_artifact_identity,
)
from trading_system.market_understanding.policy_governance import (
    DATASET_ROLE_DEVELOPMENT_FIT,
    DATASET_ROLE_DEVELOPMENT_SELECTION,
    DATASET_ROLE_FINAL_EVALUATION_LOCKED,
    OBJECTIVE_KIND_INFORMATION,
    ExperimentRegistry,
    ObjectiveArtifact,
    SelectionBlockedError,
)
from trading_system.market_understanding.price_path import (
    MetricResult,
    exact_metric,
)
from trading_system.market_understanding.records import ImmutableRecord
from trading_system.market_understanding.wave_representation import (
    G1_STATUS_ELIGIBLE,
    StructuralQualificationRecord,
)
from trading_system.research.information_time import (
    InformationKey,
    InformationPhase,
)


S9_SCHEMA_VERSION: Final[str] = "MUF_S9_INFORMATION_SELECTION_V1"
S9_SCHEMA_IDENTITY: Final[SchemaIdentity] = SchemaIdentity(
    "MUF_S9_INFORMATION_SELECTION", "V1"
)

CANDIDATE_INFORMATION_EVALUATION_SCHEMA: Final[ArtifactIdentitySchema] = (
    ArtifactIdentitySchema(
        artifact_type="MUF_S9_CANDIDATE_INFORMATION_EVALUATION",
        schema_identity=S9_SCHEMA_IDENTITY,
        identity_defining_fields=(
            "evaluation_id",
            "candidate_id",
            "experiment_id",
            "representation_spec_hash",
            "policy_hash",
            "protocol_hash",
            "estimand_hash",
            "feature_view_hash",
            "state_catalog_hash",
            "graph_spec_hash",
            "dependence_contract_hash",
            "objective_hash",
            "dataset_id",
            "dataset_role",
            "structural_eligibility_status",
            "uncensored_realization_count",
            "right_censored_realization_count",
            "non_overlapping_span_cluster_count",
            "cluster_weighted_information_score",
            "evaluation_key",
        ),
    )
)
GATE_G2_SELECTION_DECISION_SCHEMA: Final[ArtifactIdentitySchema] = (
    ArtifactIdentitySchema(
        artifact_type="MUF_S9_GATE_G2_SELECTION_DECISION",
        schema_identity=S9_SCHEMA_IDENTITY,
        identity_defining_fields=(
            "decision_id",
            "gate_status",
            "objective_hash_or_state",
            "eligible_candidate_ids",
            "candidate_evaluation_hashes",
            "selected_winner_candidate_id",
            "tied_top_candidate_ids",
            "decision_key",
            "research_debt_024_status",
        ),
    )
)

# Gate G2 status constants (D2-3, D2-17, I-SEL-1..5)
GATE_G2_SELECTED: Final[str] = "GATE_G2_SELECTED"
GATE_G2_TIED_NO_UNIQUE_WINNER: Final[str] = "GATE_G2_TIED_NO_UNIQUE_WINNER"
GATE_G2_NOT_CONFIGURED: Final[str] = "GATE_G2_NOT_CONFIGURED"

VALID_GATE_G2_STATUSES: Final[Tuple[str, ...]] = (
    GATE_G2_SELECTED,
    GATE_G2_TIED_NO_UNIQUE_WINNER,
    GATE_G2_NOT_CONFIGURED,
)

# Deterministic error codes
S9_INVALID_CANDIDATE_EVALUATION: Final[str] = "S9_INVALID_CANDIDATE_EVALUATION"
S9_INELIGIBLE_CANDIDATE_REJECTED: Final[str] = "S9_INELIGIBLE_CANDIDATE_REJECTED"
S9_FINAL_DATASET_FORBIDDEN_IN_G2: Final[str] = "S9_FINAL_DATASET_FORBIDDEN_IN_G2"
S9_MISSING_INFORMATION_OBJECTIVE: Final[str] = "S9_MISSING_INFORMATION_OBJECTIVE"
S9_VISUAL_TIE_BREAKER_FORBIDDEN: Final[str] = "S9_VISUAL_TIE_BREAKER_FORBIDDEN"
S9_INVALID_GATE_G2_DECISION: Final[str] = "S9_INVALID_GATE_G2_DECISION"
S9_INCONSISTENT_CANDIDATE_COMPARISON: Final[str] = (
    "S9_INCONSISTENT_CANDIDATE_COMPARISON"
)


def _require_non_empty_str(val: Any, field_name: str, code: str) -> str:
    if not isinstance(val, str) or not val.strip():
        raise SchemaViolation(f"{code}: {field_name} must be a non-empty string")
    return val


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
class CandidateInformationEvaluationRecord(ImmutableRecord):
    """Development information evaluation record for one structurally ELIGIBLE candidate."""

    evaluation_id: str
    candidate_id: str
    experiment_id: str
    representation_spec_hash: str
    policy_hash: str
    protocol_hash: str
    estimand_hash: str
    feature_view_hash: str
    state_catalog_hash: str
    graph_spec_hash: str
    dependence_contract_hash: str
    objective_hash: str
    dataset_id: str
    dataset_role: str
    structural_eligibility_status: str
    uncensored_realization_count: int
    right_censored_realization_count: int
    non_overlapping_span_cluster_count: int
    cluster_weighted_information_score: Union[MetricResult, TypedState]
    evaluation_key: InformationKey
    evaluation_record_hash: str

    def __post_init__(self) -> None:
        for f_name, f_val in (
            ("evaluation_id", self.evaluation_id),
            ("candidate_id", self.candidate_id),
            ("experiment_id", self.experiment_id),
            ("representation_spec_hash", self.representation_spec_hash),
            ("policy_hash", self.policy_hash),
            ("protocol_hash", self.protocol_hash),
            ("estimand_hash", self.estimand_hash),
            ("feature_view_hash", self.feature_view_hash),
            ("state_catalog_hash", self.state_catalog_hash),
            ("graph_spec_hash", self.graph_spec_hash),
            ("dependence_contract_hash", self.dependence_contract_hash),
            ("objective_hash", self.objective_hash),
            ("dataset_id", self.dataset_id),
        ):
            _require_non_empty_str(
                f_val, f_name, S9_INVALID_CANDIDATE_EVALUATION
            )

        if self.dataset_role == DATASET_ROLE_FINAL_EVALUATION_LOCKED or self.dataset_role not in (
            DATASET_ROLE_DEVELOPMENT_FIT,
            DATASET_ROLE_DEVELOPMENT_SELECTION,
        ):
            raise SelectionBlockedError(
                f"{S9_FINAL_DATASET_FORBIDDEN_IN_G2}: dataset_role={self.dataset_role!r} forbidden in S9/G2 (I-SEL-3)"
            )
        if self.structural_eligibility_status != G1_STATUS_ELIGIBLE:
            raise SelectionBlockedError(
                f"{S9_INELIGIBLE_CANDIDATE_REJECTED}: candidate {self.candidate_id!r} "
                f"has structural_eligibility_status={self.structural_eligibility_status!r} != ELIGIBLE (I-SEL-1)"
            )

        for c_name, c_val in (
            ("uncensored_realization_count", self.uncensored_realization_count),
            (
                "right_censored_realization_count",
                self.right_censored_realization_count,
            ),
            (
                "non_overlapping_span_cluster_count",
                self.non_overlapping_span_cluster_count,
            ),
        ):
            if (
                not isinstance(c_val, int)
                or isinstance(c_val, bool)
                or c_val < 0
            ):
                raise SchemaViolation(
                    f"{S9_INVALID_CANDIDATE_EVALUATION}: {c_name} must be a non-negative int"
                )

        if not isinstance(
            self.cluster_weighted_information_score, (MetricResult, TypedState)
        ):
            raise SchemaViolation(
                f"{S9_INVALID_CANDIDATE_EVALUATION}: cluster_weighted_information_score must be MetricResult or TypedState"
            )
        _require_completed_key(
            self.evaluation_key,
            "evaluation_key",
            S9_INVALID_CANDIDATE_EVALUATION,
        )

        score_tok = (
            self.cluster_weighted_information_score.value
            if isinstance(self.cluster_weighted_information_score, TypedState)
            else repr(self.cluster_weighted_information_score.value)
        )
        expected_hash = canonical_artifact_identity(
            CANDIDATE_INFORMATION_EVALUATION_SCHEMA,
            identity_payload={
                "evaluation_id": self.evaluation_id,
                "candidate_id": self.candidate_id,
                "experiment_id": self.experiment_id,
                "representation_spec_hash": self.representation_spec_hash,
                "policy_hash": self.policy_hash,
                "protocol_hash": self.protocol_hash,
                "estimand_hash": self.estimand_hash,
                "feature_view_hash": self.feature_view_hash,
                "state_catalog_hash": self.state_catalog_hash,
                "graph_spec_hash": self.graph_spec_hash,
                "dependence_contract_hash": self.dependence_contract_hash,
                "objective_hash": self.objective_hash,
                "dataset_id": self.dataset_id,
                "dataset_role": self.dataset_role,
                "structural_eligibility_status": self.structural_eligibility_status,
                "uncensored_realization_count": str(
                    self.uncensored_realization_count
                ),
                "right_censored_realization_count": str(
                    self.right_censored_realization_count
                ),
                "non_overlapping_span_cluster_count": str(
                    self.non_overlapping_span_cluster_count
                ),
                "cluster_weighted_information_score": score_tok,
                "evaluation_key": self.evaluation_key,
            },
        )
        if self.evaluation_record_hash != expected_hash:
            raise SchemaViolation(
                f"{S9_INVALID_CANDIDATE_EVALUATION}: evaluation_record_hash mismatch"
            )


def evaluate_candidate_information_on_development(
    dependence_bundle: DependenceAccountingBundle,
    *,
    evaluation_id: str,
    candidate_id: str,
    protocol: DevelopmentEvaluationProtocol,
    estimand: Union[EstimandArtifact, TypedState],
    feature_view: Union[FeatureViewSpec, TypedState],
    objective_artifact: Union[ObjectiveArtifact, TypedState],
    experiment_registry: ExperimentRegistry,
    structural_eligibility_status: str = G1_STATUS_ELIGIBLE,
) -> Tuple[CandidateInformationEvaluationRecord, DevelopmentEstimandEvaluationBundle]:
    """Evaluate a structurally ELIGIBLE candidate on development data under S8.5/S9 contracts."""
    if not isinstance(dependence_bundle, DependenceAccountingBundle):
        raise SchemaViolation(
            f"{S9_INVALID_CANDIDATE_EVALUATION}: dependence_bundle must be a DependenceAccountingBundle"
        )
    if isinstance(objective_artifact, TypedState) or not isinstance(
        objective_artifact, ObjectiveArtifact
    ):
        raise SelectionBlockedError(
            f"{S9_MISSING_INFORMATION_OBJECTIVE}: valid ObjectiveArtifact required for candidate information evaluation (I-SEL-2)"
        )
    if objective_artifact.objective_kind != OBJECTIVE_KIND_INFORMATION:
        raise SelectionBlockedError(
            f"{S9_MISSING_INFORMATION_OBJECTIVE}: objective_kind must be {OBJECTIVE_KIND_INFORMATION!r} (D2-3, D2-17)"
        )

    wave_bundle = dependence_bundle.state_graph_bundle.wave_bundle
    elig_status = structural_eligibility_status
    if elig_status != G1_STATUS_ELIGIBLE:
        raise SelectionBlockedError(
            f"{S9_INELIGIBLE_CANDIDATE_REJECTED}: candidate {candidate_id!r} is {elig_status!r}, not ELIGIBLE (I-SEL-1)"
        )

    eval_bundle = evaluate_development_estimand_realizations(
        dependence_bundle,
        protocol=protocol,
        estimand=estimand,
        feature_view=feature_view,
        objective_artifact=objective_artifact,
        experiment_registry=experiment_registry,
    )

    # Group overlapping confirmed wave spans into non-overlapping span clusters
    wp_to_ep: dict[str, str] = {
        anc.anchor_wave_process_id: anc.episode_id
        for anc in dependence_bundle.episode_anchors
    }
    ep_to_cluster: dict[str, int] = {}
    sorted_geoms = sorted(
        wave_bundle.finalized_wave_geometries,
        key=lambda fg: (fg.start_origin_position, fg.end_origin_position),
    )
    curr_cluster = 0
    curr_end = -1
    for fg in sorted_geoms:
        if curr_end < 0:
            curr_cluster = 1
            curr_end = fg.end_origin_position
        elif fg.start_origin_position > curr_end:
            curr_cluster += 1
            curr_end = fg.end_origin_position
        elif fg.end_origin_position > curr_end:
            curr_end = fg.end_origin_position
        ep_id = wp_to_ep.get(fg.wave_process_id, fg.wave_process_id)
        ep_to_cluster[ep_id] = curr_cluster

    cluster_uncensored_values: dict[int, list[float]] = {}
    for real in eval_bundle.realizations:
        if (
            real.censoring_status == CENSORING_STATUS_UNCENSORED
            and isinstance(real.outcome_value, MetricResult)
        ):
            cid = ep_to_cluster.get(real.episode_id, 0)
            cluster_uncensored_values.setdefault(cid, []).append(
                real.outcome_value.value
            )

    if len(cluster_uncensored_values) == 0:
        score: Union[MetricResult, TypedState] = TypedState.UNDEFINED
    else:
        cluster_means = [
            sum(vals) / float(len(vals))
            for vals in cluster_uncensored_values.values()
        ]
        score = exact_metric(sum(cluster_means) / float(len(cluster_means)))

    eval_key = wave_bundle.observation_keys[-1]
    score_tok = (
        score.value if isinstance(score, TypedState) else repr(score.value)
    )
    rec_hash = canonical_artifact_identity(
        CANDIDATE_INFORMATION_EVALUATION_SCHEMA,
        identity_payload={
            "evaluation_id": evaluation_id,
            "candidate_id": candidate_id,
            "experiment_id": protocol.experiment_id,
            "representation_spec_hash": wave_bundle.representation_spec.representation_spec_hash,
            "policy_hash": wave_bundle.policy_artifact.policy_hash,
            "protocol_hash": protocol.protocol_hash,
            "estimand_hash": protocol.estimand_hash,
            "feature_view_hash": protocol.feature_view_hash,
            "state_catalog_hash": protocol.state_catalog_hash,
            "graph_spec_hash": protocol.graph_spec_hash,
            "dependence_contract_hash": protocol.dependence_contract_hash,
            "objective_hash": protocol.objective_hash,
            "dataset_id": protocol.dataset_id,
            "dataset_role": protocol.dataset_role,
            "structural_eligibility_status": elig_status,
            "uncensored_realization_count": str(eval_bundle.uncensored_count),
            "right_censored_realization_count": str(
                eval_bundle.right_censored_count
            ),
            "non_overlapping_span_cluster_count": str(
                eval_bundle.non_overlapping_span_cluster_count
            ),
            "cluster_weighted_information_score": score_tok,
            "evaluation_key": eval_key,
        },
    )
    record = CandidateInformationEvaluationRecord(
        evaluation_id=evaluation_id,
        candidate_id=candidate_id,
        experiment_id=protocol.experiment_id,
        representation_spec_hash=wave_bundle.representation_spec.representation_spec_hash,
        policy_hash=wave_bundle.policy_artifact.policy_hash,
        protocol_hash=protocol.protocol_hash,
        estimand_hash=protocol.estimand_hash,
        feature_view_hash=protocol.feature_view_hash,
        state_catalog_hash=protocol.state_catalog_hash,
        graph_spec_hash=protocol.graph_spec_hash,
        dependence_contract_hash=protocol.dependence_contract_hash,
        objective_hash=protocol.objective_hash,
        dataset_id=protocol.dataset_id,
        dataset_role=protocol.dataset_role,
        structural_eligibility_status=elig_status,
        uncensored_realization_count=eval_bundle.uncensored_count,
        right_censored_realization_count=eval_bundle.right_censored_count,
        non_overlapping_span_cluster_count=eval_bundle.non_overlapping_span_cluster_count,
        cluster_weighted_information_score=score,
        evaluation_key=eval_key,
        evaluation_record_hash=rec_hash,
    )
    return record, eval_bundle


@dataclass(frozen=True)
class GateG2InformationSelectionDecision(ImmutableRecord):
    """Gate G2 decision record (D2-3, D2-17, I-SEL-1..5)."""

    decision_id: str
    gate_status: str
    objective_hash_or_state: Union[str, TypedState]
    eligible_candidate_ids: Tuple[str, ...]
    candidate_evaluation_hashes: Tuple[str, ...]
    selected_winner_candidate_id: Union[str, TypedState]
    tied_top_candidate_ids: Tuple[str, ...]
    decision_key: InformationKey
    research_debt_024_status: str
    decision_hash: str

    def __post_init__(self) -> None:
        _require_non_empty_str(
            self.decision_id, "decision_id", S9_INVALID_GATE_G2_DECISION
        )
        if self.gate_status not in VALID_GATE_G2_STATUSES:
            raise SchemaViolation(
                f"{S9_INVALID_GATE_G2_DECISION}: invalid gate_status {self.gate_status!r}"
            )
        if not isinstance(self.objective_hash_or_state, (str, TypedState)):
            raise SchemaViolation(
                f"{S9_INVALID_GATE_G2_DECISION}: objective_hash_or_state must be str or TypedState"
            )
        if isinstance(self.objective_hash_or_state, str) and not self.objective_hash_or_state.strip():
            raise SchemaViolation(
                f"{S9_INVALID_GATE_G2_DECISION}: objective_hash_or_state string cannot be empty"
            )

        elig_ids = tuple(self.eligible_candidate_ids)
        if len(elig_ids) == 0:
            raise SchemaViolation(
                f"{S9_INVALID_GATE_G2_DECISION}: eligible_candidate_ids must be non-empty"
            )
        eval_hashes = tuple(self.candidate_evaluation_hashes)
        tied_ids = tuple(self.tied_top_candidate_ids)
        object.__setattr__(self, "eligible_candidate_ids", elig_ids)
        object.__setattr__(self, "candidate_evaluation_hashes", eval_hashes)
        object.__setattr__(self, "tied_top_candidate_ids", tied_ids)

        if self.gate_status == GATE_G2_NOT_CONFIGURED:
            if self.selected_winner_candidate_id is not TypedState.NOT_CONFIGURED:
                raise SchemaViolation(
                    f"{S9_INVALID_GATE_G2_DECISION}: GATE_G2_NOT_CONFIGURED requires selected_winner_candidate_id=TypedState.NOT_CONFIGURED (I-SEL-4)"
                )
        elif self.gate_status == GATE_G2_TIED_NO_UNIQUE_WINNER:
            if self.selected_winner_candidate_id is not TypedState.UNDEFINED:
                raise SchemaViolation(
                    f"{S9_INVALID_GATE_G2_DECISION}: GATE_G2_TIED_NO_UNIQUE_WINNER requires selected_winner_candidate_id=TypedState.UNDEFINED (I-SEL-5)"
                )
            if len(tied_ids) <= 1:
                raise SchemaViolation(
                    f"{S9_INVALID_GATE_G2_DECISION}: GATE_G2_TIED_NO_UNIQUE_WINNER requires multiple tied_top_candidate_ids"
                )
        else:
            if (
                not isinstance(self.selected_winner_candidate_id, str)
                or self.selected_winner_candidate_id not in elig_ids
            ):
                raise SchemaViolation(
                    f"{S9_INVALID_GATE_G2_DECISION}: GATE_G2_SELECTED winner must be in eligible_candidate_ids"
                )

        _require_completed_key(
            self.decision_key, "decision_key", S9_INVALID_GATE_G2_DECISION
        )
        if self.research_debt_024_status != RESEARCH_DEBT_024_STANDING_STATUS:
            raise SchemaViolation(
                f"{S9_INVALID_GATE_G2_DECISION}: research_debt_024_status must remain {RESEARCH_DEBT_024_STANDING_STATUS!r}"
            )

        obj_tok = (
            self.objective_hash_or_state.value
            if isinstance(self.objective_hash_or_state, TypedState)
            else self.objective_hash_or_state
        )
        win_tok = (
            self.selected_winner_candidate_id.value
            if isinstance(self.selected_winner_candidate_id, TypedState)
            else self.selected_winner_candidate_id
        )
        expected_hash = canonical_artifact_identity(
            GATE_G2_SELECTION_DECISION_SCHEMA,
            identity_payload={
                "decision_id": self.decision_id,
                "gate_status": self.gate_status,
                "objective_hash_or_state": obj_tok,
                "eligible_candidate_ids": _serialize_seq(elig_ids),
                "candidate_evaluation_hashes": _serialize_seq(eval_hashes),
                "selected_winner_candidate_id": win_tok,
                "tied_top_candidate_ids": _serialize_seq(tied_ids),
                "decision_key": self.decision_key,
                "research_debt_024_status": self.research_debt_024_status,
            },
        )
        if self.decision_hash != expected_hash:
            raise SchemaViolation(
                f"{S9_INVALID_GATE_G2_DECISION}: decision_hash mismatch"
            )


def run_gate_g2_information_selection(
    *,
    decision_id: str,
    eligible_candidate_ids: Sequence[str],
    objective_artifact: Union[ObjectiveArtifact, TypedState],
    candidate_evaluations: Sequence[CandidateInformationEvaluationRecord],
    decision_key: InformationKey,
    visual_preference_candidate_id: Union[str, TypedState] = TypedState.NOT_APPLICABLE,
) -> GateG2InformationSelectionDecision:
    """Execute Gate G2 (Development Information Selection) under D2-3, D2-17, and I-SEL-1..5."""
    if (
        not isinstance(visual_preference_candidate_id, TypedState)
        or visual_preference_candidate_id is not TypedState.NOT_APPLICABLE
    ):
        raise SelectionBlockedError(
            f"{S9_VISUAL_TIE_BREAKER_FORBIDDEN}: visual/subjective preference is forbidden in Gate G2 (I-SEL-5)"
        )
    elig_ids = tuple(eligible_candidate_ids)
    if len(elig_ids) == 0:
        raise SelectionBlockedError(
            f"{S9_INELIGIBLE_CANDIDATE_REJECTED}: at least one structurally ELIGIBLE candidate required"
        )
    _require_completed_key(
        decision_key, "decision_key", S9_INVALID_GATE_G2_DECISION
    )

    # D2-17 / I-SEL-4: When InformationObjective is NOT_CONFIGURED or UNDEFINED,
    # Gate G2 returns GATE_G2_NOT_CONFIGURED and preserves eligible_candidate_ids with no winner.
    if isinstance(objective_artifact, TypedState):
        if objective_artifact not in (
            TypedState.NOT_CONFIGURED,
            TypedState.UNDEFINED,
        ):
            raise SelectionBlockedError(
                f"{S9_MISSING_INFORMATION_OBJECTIVE}: invalid objective_artifact state {objective_artifact!r}"
            )
        dec_hash = canonical_artifact_identity(
            GATE_G2_SELECTION_DECISION_SCHEMA,
            identity_payload={
                "decision_id": decision_id,
                "gate_status": GATE_G2_NOT_CONFIGURED,
                "objective_hash_or_state": TypedState.NOT_CONFIGURED.value,
                "eligible_candidate_ids": _serialize_seq(elig_ids),
                "candidate_evaluation_hashes": _serialize_seq(()),
                "selected_winner_candidate_id": TypedState.NOT_CONFIGURED.value,
                "tied_top_candidate_ids": _serialize_seq(()),
                "decision_key": decision_key,
                "research_debt_024_status": RESEARCH_DEBT_024_STANDING_STATUS,
            },
        )
        return GateG2InformationSelectionDecision(
            decision_id=decision_id,
            gate_status=GATE_G2_NOT_CONFIGURED,
            objective_hash_or_state=TypedState.NOT_CONFIGURED,
            eligible_candidate_ids=elig_ids,
            candidate_evaluation_hashes=(),
            selected_winner_candidate_id=TypedState.NOT_CONFIGURED,
            tied_top_candidate_ids=(),
            decision_key=decision_key,
            research_debt_024_status=RESEARCH_DEBT_024_STANDING_STATUS,
            decision_hash=dec_hash,
        )

    if not isinstance(objective_artifact, ObjectiveArtifact):
        raise SelectionBlockedError(
            f"{S9_MISSING_INFORMATION_OBJECTIVE}: expected ObjectiveArtifact or TypedState"
        )
    if objective_artifact.objective_kind != OBJECTIVE_KIND_INFORMATION:
        raise SelectionBlockedError(
            f"{S9_MISSING_INFORMATION_OBJECTIVE}: Gate G2 requires OBJECTIVE_KIND_INFORMATION"
        )

    evals = tuple(candidate_evaluations)
    if len(evals) == 0:
        raise SelectionBlockedError(
            f"{S9_INVALID_CANDIDATE_EVALUATION}: candidate_evaluations cannot be empty when objective is configured"
        )

    seen_cands: set[str] = set()
    ref_estimand = evals[0].estimand_hash
    ref_dataset = evals[0].dataset_id
    ref_role = evals[0].dataset_role

    scored_pairs: list[Tuple[str, float]] = []
    eval_hashes: list[str] = []

    for ev in evals:
        if not isinstance(ev, CandidateInformationEvaluationRecord):
            raise SchemaViolation(
                f"{S9_INVALID_CANDIDATE_EVALUATION}: expected CandidateInformationEvaluationRecord"
            )
        if ev.candidate_id not in elig_ids:
            raise SelectionBlockedError(
                f"{S9_INELIGIBLE_CANDIDATE_REJECTED}: candidate {ev.candidate_id!r} not in eligible_candidate_ids"
            )
        if ev.candidate_id in seen_cands:
            raise SchemaViolation(
                f"{S9_INVALID_CANDIDATE_EVALUATION}: duplicate evaluation for candidate {ev.candidate_id!r}"
            )
        seen_cands.add(ev.candidate_id)

        if (
            ev.objective_hash != objective_artifact.objective_hash
            or ev.estimand_hash != ref_estimand
            or ev.dataset_id != ref_dataset
            or ev.dataset_role != ref_role
        ):
            raise SelectionBlockedError(
                f"{S9_INCONSISTENT_CANDIDATE_COMPARISON}: all compared candidates must share objective_hash, estimand_hash, dataset_id, and dataset_role"
            )
        if not isinstance(ev.cluster_weighted_information_score, MetricResult):
            raise SelectionBlockedError(
                f"{S9_INVALID_CANDIDATE_EVALUATION}: candidate {ev.candidate_id!r} has non-numeric score {ev.cluster_weighted_information_score!r}"
            )
        scored_pairs.append(
            (ev.candidate_id, ev.cluster_weighted_information_score.value)
        )
        eval_hashes.append(ev.evaluation_record_hash)

    maximize = objective_artifact.comparison_direction == "MAXIMIZE"
    best_val = (
        max(val for _, val in scored_pairs)
        if maximize
        else min(val for _, val in scored_pairs)
    )
    top_cands = tuple(cid for cid, val in scored_pairs if val == best_val)

    if len(top_cands) == 1:
        g_status = GATE_G2_SELECTED
        winner: Union[str, TypedState] = top_cands[0]
        tied_top: Tuple[str, ...] = ()
    else:
        g_status = GATE_G2_TIED_NO_UNIQUE_WINNER
        winner = TypedState.UNDEFINED
        tied_top = top_cands

    win_tok = winner.value if isinstance(winner, TypedState) else winner
    dec_hash = canonical_artifact_identity(
        GATE_G2_SELECTION_DECISION_SCHEMA,
        identity_payload={
            "decision_id": decision_id,
            "gate_status": g_status,
            "objective_hash_or_state": objective_artifact.objective_hash,
            "eligible_candidate_ids": _serialize_seq(elig_ids),
            "candidate_evaluation_hashes": _serialize_seq(eval_hashes),
            "selected_winner_candidate_id": win_tok,
            "tied_top_candidate_ids": _serialize_seq(tied_top),
            "decision_key": decision_key,
            "research_debt_024_status": RESEARCH_DEBT_024_STANDING_STATUS,
        },
    )
    return GateG2InformationSelectionDecision(
        decision_id=decision_id,
        gate_status=g_status,
        objective_hash_or_state=objective_artifact.objective_hash,
        eligible_candidate_ids=elig_ids,
        candidate_evaluation_hashes=tuple(eval_hashes),
        selected_winner_candidate_id=winner,
        tied_top_candidate_ids=tied_top,
        decision_key=decision_key,
        research_debt_024_status=RESEARCH_DEBT_024_STANDING_STATUS,
        decision_hash=dec_hash,
    )


__all__ = [
    "S9_SCHEMA_VERSION",
    "CANDIDATE_INFORMATION_EVALUATION_SCHEMA",
    "GATE_G2_SELECTION_DECISION_SCHEMA",
    "GATE_G2_SELECTED",
    "GATE_G2_TIED_NO_UNIQUE_WINNER",
    "GATE_G2_NOT_CONFIGURED",
    "VALID_GATE_G2_STATUSES",
    "S9_INVALID_CANDIDATE_EVALUATION",
    "S9_INELIGIBLE_CANDIDATE_REJECTED",
    "S9_FINAL_DATASET_FORBIDDEN_IN_G2",
    "S9_MISSING_INFORMATION_OBJECTIVE",
    "S9_VISUAL_TIE_BREAKER_FORBIDDEN",
    "S9_INVALID_GATE_G2_DECISION",
    "S9_INCONSISTENT_CANDIDATE_COMPARISON",
    "CandidateInformationEvaluationRecord",
    "evaluate_candidate_information_on_development",
    "GateG2InformationSelectionDecision",
    "run_gate_g2_information_selection",
]
