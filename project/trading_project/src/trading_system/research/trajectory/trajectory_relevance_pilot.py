"""Strategy-neutral, as-of contextual candidate/revision pilot.

This module registers the complete FVG entity universe visible at one declared
historical InformationKey, keeps factual producer context separate from
question-specific declared assessments, and supports append-only revisions
from later newly available lifecycle facts. V1 revision evidence is limited to
candidate-matched normalized FVG lifecycle rows; it does not treat FVG bar
summaries or unbound domains as candidate-specific evidence. It makes no
relevance score, probability, prediction, trade signal, market-performance
label, or claim about institutional intent. Stage 4B2 local verification is not
producer/source authentication.

The pilot does not resolve either existing unsafe blocker:
* S8 COMPETING_BOUNDARY_FIRST_PASSAGE remains blocked; same-bar OHLC touches do
  not establish intrabar order.
* S9 SATISFY_CONSTRAINT remains blocked; constraint selection/satisfaction is
  not evaluated here.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace as dataclass_replace
from decimal import Decimal, InvalidOperation
from enum import Enum
import re
from typing import Iterable

import pandas as pd

from trading_system.research.hashing import canonical_sha256
from trading_system.research.information_time import (
    InformationKey,
    InformationPhase,
    PositionalTimelineAdapter,
    TimeIndexedTimelineAdapter,
)
from trading_system.research.trajectory.trajectory_contract import MarketObservationTimeline
from trading_system.research.trajectory.trajectory_case_adapter import (
    SurfacePrefixBinding,
    TrajectoryCaseError,
    TrajectoryDecisionCase,
    create_trajectory_decision_case,
    verify_case_source_prefix,
)
from trading_system.research.trajectory.trajectory_query_views import (
    AsOfSurfaceView,
    AvailabilityStatus,
    FrozenCell,
    FrozenCellKind,
    FrozenSurfaceTable,
    ObservedEntityLocator,
    TrajectoryQueryError,
    create_asof_surface_view,
    decision_surface_view,
    resolve_observed_entity,
)
from trading_system.research.trajectory import trajectory_stage4b2 as s4b2


PILOT_CONTRACT_VERSION = "CONTEXTUAL_CANDIDATE_RELEVANCE_PILOT_V1"
FVG_ELIGIBILITY_POLICY_ID = "STAGE4B2_FVG_VISIBLE_BY_CREATION_POSITION_V1"
FVG_EVENT_EVIDENCE_KIND = "FVG_NORMALIZED_LIFECYCLE_EVENT"
_FVG_NORMALIZED_EVENT_COLUMNS = (
    "event_position", "fvg_id", "direction", "event_type", "origin_position",
    "middle_position", "creation_position", "zone_low", "zone_high", "midpoint",
    "gap_width", "gap_width_fraction", "gap_width_percentile",
    "gap_width_history_count", "middle_body_fraction", "middle_signed_body_fraction",
    "event_high", "event_low", "event_close", "zone_range_coverage_fraction",
    "fvg_age_bars", "same_information_batch_order_unknown",
)
_SUPPORTED_CONTEXT_DOMAINS = (
    "VOLATILITY", "SESSION", "ORDER_FLOW_PROXY", "ABSORPTION_PROXY",
    "SHARED_STRUCTURE", "LIQUIDITY", "ORDER_BLOCK", "FVG",
    "DEALING_RANGE", "HTF_SCALE_RAW",
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
TimelineAdapter = PositionalTimelineAdapter | TimeIndexedTimelineAdapter

# Deliberately descriptive constants: the pilot does not alter or reinterpret
# either blocker in the closed S8/S9 surfaces.
UNSAFE_BLOCKER_DECLARATIONS = (
    "S8 COMPETING_BOUNDARY_FIRST_PASSAGE: BLOCKED; same-bar OHLC does not establish order.",
    "S9 SATISFY_CONSTRAINT: BLOCKED; constraint selection/satisfaction is not evaluated.",
)


class CandidatePilotError(ValueError):
    """Invalid, incomplete, mutated, or causally unavailable pilot input."""


class AssessmentCategory(Enum):
    FACTUAL_CONTEXT = "FACTUAL_CONTEXT"
    DECLARED_HUMAN_ASSESSMENT = "DECLARED_HUMAN_ASSESSMENT"
    DECLARED_OPERATIONAL_POLICY = "DECLARED_OPERATIONAL_POLICY"
    EMPIRICALLY_VALIDATED_RELEVANCE = "EMPIRICALLY_VALIDATED_RELEVANCE"
    UNKNOWN = "UNKNOWN"


class ProvisionalStatus(Enum):
    PROVISIONAL = "PROVISIONAL"
    DEFERRED = "DEFERRED"
    UNRESOLVED = "UNRESOLVED"
    UNKNOWN = "UNKNOWN"


class CandidateCoverageState(Enum):
    REGISTERED = "REGISTERED"
    ASSESSED = "ASSESSED"
    DEFERRED = "DEFERRED"
    UNRESOLVED = "UNRESOLVED"
    NOT_EVALUATED = "NOT_EVALUATED"


@dataclass(frozen=True)
class ResearchQuestion:
    question_id: str
    version: str
    text: str
    question_sha256: str

    @classmethod
    def declare(cls, *, question_id: str, version: str, text: str) -> "ResearchQuestion":
        digest = canonical_sha256(
            domain="CONTEXTUAL_CANDIDATE_RESEARCH_QUESTION_V1",
            payload={"question_id": question_id, "version": version, "text": text},
        )
        return cls(question_id, version, text, digest)

    def __post_init__(self) -> None:
        _require_text(self.question_id, "question_id")
        _require_text(self.version, "question version")
        _require_text(self.text, "question text")
        _require_hash(self.question_sha256, "question_sha256")
        expected = canonical_sha256(
            domain="CONTEXTUAL_CANDIDATE_RESEARCH_QUESTION_V1",
            payload={"question_id": self.question_id, "version": self.version, "text": self.text},
        )
        if self.question_sha256 != expected:
            raise CandidatePilotError("research question identity/hash mismatch")

    @property
    def identity_hash(self) -> str:
        return self.question_sha256


@dataclass(frozen=True)
class AssessmentProtocolIdentity:
    protocol_id: str
    version: str
    description: str
    protocol_sha256: str

    @classmethod
    def declare(
        cls, *, protocol_id: str, version: str, description: str
    ) -> "AssessmentProtocolIdentity":
        digest = canonical_sha256(
            domain="CONTEXTUAL_CANDIDATE_ASSESSMENT_PROTOCOL_V1",
            payload={"protocol_id": protocol_id, "version": version, "description": description},
        )
        return cls(protocol_id, version, description, digest)

    def __post_init__(self) -> None:
        _require_text(self.protocol_id, "protocol_id")
        _require_text(self.version, "protocol version")
        _require_text(self.description, "protocol description")
        _require_hash(self.protocol_sha256, "protocol_sha256")
        expected = canonical_sha256(
            domain="CONTEXTUAL_CANDIDATE_ASSESSMENT_PROTOCOL_V1",
            payload={"protocol_id": self.protocol_id, "version": self.version, "description": self.description},
        )
        if self.protocol_sha256 != expected:
            raise CandidatePilotError("assessment protocol identity/hash mismatch")


@dataclass(frozen=True)
class ProducerPolicyIdentity:
    """Identity of the fixed Stage4B2 FVG source contract, not a relevance policy."""

    producer_domain: str
    surface_family: str
    contract_version: str
    configuration_identity_hash: str
    policy_id: str
    policy_version: str
    policy_sha256: str
    scope: str = "FIXED_PRODUCER_CONTRACT_ONLY_NOT_A_RELEVANCE_OR_TRADING_POLICY"

    def __post_init__(self) -> None:
        for name in ("producer_domain", "surface_family", "contract_version", "policy_id", "policy_version", "scope"):
            _require_text(getattr(self, name), name)
        _require_hash(self.configuration_identity_hash, "configuration_identity_hash")
        _require_hash(self.policy_sha256, "policy_sha256")
        if self.producer_domain != "FVG" or self.surface_family != "STAGE4B2":
            raise CandidatePilotError("pilot source policy must identify the fixed Stage4B2 FVG surface")

    @property
    def identity_hash(self) -> str:
        return canonical_sha256(
            domain="CONTEXTUAL_CANDIDATE_PRODUCER_POLICY_IDENTITY_V1",
            payload={
                "producer_domain": self.producer_domain,
                "surface_family": self.surface_family,
                "contract_version": self.contract_version,
                "configuration_identity_hash": self.configuration_identity_hash,
                "policy_id": self.policy_id,
                "policy_version": self.policy_version,
                "policy_sha256": self.policy_sha256,
                "scope": self.scope,
            },
        )


@dataclass(frozen=True)
class SourceArtifactProvenance:
    """Full-artifact provenance kept separate from causal prefix identity.

    ``source_surface_id`` and ``source_timeline_hash`` can change after future
    append. They are provenance references only and are excluded from candidate,
    universe, question, and assessment identity hashes.
    """

    source_timeline_id: str
    source_timeline_hash: str
    source_surface_id: str
    reconstruction_input_hash: str
    verification_scope: str | None
    producer_policy_identity: ProducerPolicyIdentity

    def __post_init__(self) -> None:
        _require_text(self.source_timeline_id, "source_timeline_id")
        for name in ("source_timeline_hash", "source_surface_id", "reconstruction_input_hash"):
            _require_hash(getattr(self, name), name)
        if self.verification_scope is not None:
            _require_text(self.verification_scope, "verification_scope")
        if not isinstance(self.producer_policy_identity, ProducerPolicyIdentity):
            raise CandidatePilotError("producer policy identity is required")


@dataclass(frozen=True)
class FactualEvidenceReference:
    """Immutable reference to one source-backed row or explicit missingness fact."""

    reference_id: str
    candidate_id: str
    evidence_kind: str
    producer_domain: str
    source_binding_hash: str | None
    source_prefix_hash: str
    available_at: InformationKey
    row_columns: tuple[str, ...]
    row: tuple[FrozenCell, ...]
    row_sha256: str

    def __post_init__(self) -> None:
        _require_hash(self.reference_id, "evidence reference_id")
        _require_text(self.candidate_id, "evidence candidate_id")
        _require_text(self.evidence_kind, "evidence_kind")
        _require_text(self.producer_domain, "evidence producer_domain")
        if self.source_binding_hash is not None:
            _require_hash(self.source_binding_hash, "evidence source_binding_hash")
        _require_hash(self.source_prefix_hash, "evidence source_prefix_hash")
        if not isinstance(self.available_at, InformationKey):
            raise CandidatePilotError("evidence availability key is required")
        if not isinstance(self.row_columns, tuple) or any(not isinstance(item, str) for item in self.row_columns):
            raise CandidatePilotError("evidence row_columns must be immutable strings")
        if not isinstance(self.row, tuple) or len(self.row) != len(self.row_columns) or any(
            not isinstance(cell, FrozenCell) for cell in self.row
        ):
            raise CandidatePilotError("evidence row must be immutable and schema aligned")
        _require_hash(self.row_sha256, "evidence row_sha256")
        expected_row = canonical_sha256(
            domain="CONTEXTUAL_CANDIDATE_EVIDENCE_ROW_V1",
            payload={
                "columns": list(self.row_columns),
                "row": [cell.canonical_payload() for cell in self.row],
            },
        )
        if self.row_sha256 != expected_row:
            raise CandidatePilotError("evidence row hash mismatch")
        expected_id = _evidence_reference_id(
            candidate_id=self.candidate_id,
            evidence_kind=self.evidence_kind,
            producer_domain=self.producer_domain,
            source_binding_hash=self.source_binding_hash,
            available_at=self.available_at,
            row_sha256=self.row_sha256,
        )
        if self.reference_id != expected_id:
            raise CandidatePilotError("evidence reference identity mismatch")


def _evidence_reference_id(
    *,
    candidate_id: str,
    evidence_kind: str,
    producer_domain: str,
    source_binding_hash: str | None,
    available_at: InformationKey,
    row_sha256: str,
) -> str:
    # Retrieval-prefix hash is deliberately omitted: one immutable event keeps
    # the same reference identity when later prefixes append more rows.
    return canonical_sha256(
        domain="CONTEXTUAL_CANDIDATE_EVIDENCE_REFERENCE_V1",
        payload={
            "candidate_id": candidate_id,
            "evidence_kind": evidence_kind,
            "producer_domain": producer_domain,
            "source_binding_hash": source_binding_hash,
            "available_at": available_at,
            "row_sha256": row_sha256,
        },
    )


def _make_evidence_reference(
    *,
    candidate_id: str,
    evidence_kind: str,
    producer_domain: str,
    source_binding_hash: str | None,
    source_prefix_hash: str,
    available_at: InformationKey,
    row_columns: tuple[str, ...],
    row: tuple[FrozenCell, ...],
) -> FactualEvidenceReference:
    row_hash = canonical_sha256(
        domain="CONTEXTUAL_CANDIDATE_EVIDENCE_ROW_V1",
        payload={"columns": list(row_columns), "row": [cell.canonical_payload() for cell in row]},
    )
    reference_id = _evidence_reference_id(
        candidate_id=candidate_id,
        evidence_kind=evidence_kind,
        producer_domain=producer_domain,
        source_binding_hash=source_binding_hash,
        available_at=available_at,
        row_sha256=row_hash,
    )
    return FactualEvidenceReference(
        reference_id=reference_id,
        candidate_id=candidate_id,
        evidence_kind=evidence_kind,
        producer_domain=producer_domain,
        source_binding_hash=source_binding_hash,
        source_prefix_hash=source_prefix_hash,
        available_at=available_at,
        row_columns=row_columns,
        row=row,
        row_sha256=row_hash,
    )


@dataclass(frozen=True)
class CandidateContext:
    """A decision-time producer record; source attributes are not relevance scores."""

    candidate_id: str
    candidate_identity_hash: str
    decision_key: InformationKey
    origin_positions: tuple[int, ...]
    creation_position: int
    availability_position: int
    availability_key: InformationKey
    factual_attributes: tuple[tuple[str, FrozenCell], ...]
    entity_evidence: FactualEvidenceReference
    visible_lifecycle_events: tuple[FactualEvidenceReference, ...]
    unknown_context_references: tuple[FactualEvidenceReference, ...]
    domain_availability: tuple[tuple[str, str, int], ...]
    source_provenance: SourceArtifactProvenance = field(compare=False)
    decision_market_prefix_hash: str
    decision_surface_binding_hash: str
    decision_surface_prefix_hash: str
    decision_asof_view_hash: str
    context_id: str

    def __post_init__(self) -> None:
        _require_text(self.candidate_id, "candidate_id")
        for name in (
            "candidate_identity_hash", "decision_market_prefix_hash", "decision_surface_binding_hash",
            "decision_surface_prefix_hash", "decision_asof_view_hash",
        ):
            _require_hash(getattr(self, name), name)
        if self.context_id:
            _require_hash(self.context_id, "context_id")
        if not isinstance(self.decision_key, InformationKey) or not isinstance(self.availability_key, InformationKey):
            raise CandidatePilotError("candidate decision/availability keys are required")
        if not isinstance(self.origin_positions, tuple) or any(
            isinstance(position, bool) or not isinstance(position, int) or position < 0
            for position in self.origin_positions
        ):
            raise CandidatePilotError("candidate origin positions must be immutable nonnegative positions")
        for name in ("creation_position", "availability_position"):
            position = getattr(self, name)
            if isinstance(position, bool) or not isinstance(position, int) or position < 0:
                raise CandidatePilotError(f"{name} must be a nonnegative position")
        if self.availability_position > self.decision_key.bar_position:
            raise CandidatePilotError("candidate was not available at its declared decision boundary")
        if self.availability_key.timeline_id != self.decision_key.timeline_id or self.availability_key > self.decision_key:
            raise CandidatePilotError("candidate availability key is outside its decision context")
        if not isinstance(self.factual_attributes, tuple) or any(
            not isinstance(item, tuple) or len(item) != 2 or not isinstance(item[0], str)
            or not isinstance(item[1], FrozenCell)
            for item in self.factual_attributes
        ):
            raise CandidatePilotError("factual attributes must be immutable source cells")
        for name in ("entity_evidence",):
            if not isinstance(getattr(self, name), FactualEvidenceReference):
                raise CandidatePilotError(f"{name} is required")
        for name in ("visible_lifecycle_events", "unknown_context_references"):
            refs = getattr(self, name)
            if not isinstance(refs, tuple) or any(not isinstance(ref, FactualEvidenceReference) for ref in refs):
                raise CandidatePilotError(f"{name} must be immutable evidence references")
        if not isinstance(self.domain_availability, tuple) or any(
            not isinstance(item, tuple) or len(item) != 3 for item in self.domain_availability
        ):
            raise CandidatePilotError("domain availability must be immutable and complete")
        if not isinstance(self.source_provenance, SourceArtifactProvenance):
            raise CandidatePilotError("candidate source provenance is required")
        if self.creation_position != self.availability_position:
            raise CandidatePilotError("FVG creation and Stage4B2 availability positions must agree")
        if (
            self.entity_evidence.candidate_id != self.candidate_id
            or self.entity_evidence.evidence_kind != "FVG_NORMALIZED_SOURCE_ENTITY_ROW"
            or self.entity_evidence.producer_domain != "FVG"
            or self.entity_evidence.source_binding_hash != self.decision_surface_binding_hash
            or self.entity_evidence.source_prefix_hash != self.decision_surface_prefix_hash
            or self.entity_evidence.available_at != self.availability_key
            or tuple(zip(self.entity_evidence.row_columns, self.entity_evidence.row)) != self.factual_attributes
        ):
            raise CandidatePilotError("candidate factual attributes are not bound to their source entity row")
        if tuple(item[0] for item in self.domain_availability) != _SUPPORTED_CONTEXT_DOMAINS:
            raise CandidatePilotError("candidate context availability slots are incomplete or unordered")
        for domain, status, count in self.domain_availability:
            if domain == "FVG":
                if status != AvailabilityStatus.AVAILABLE.value or count != 1:
                    raise CandidatePilotError("the registered FVG source must be explicitly available")
            elif status != AvailabilityStatus.NOT_SUPPLIED.value or count != 0:
                raise CandidatePilotError("unbound context domains must remain explicitly not supplied")
        if any(
            ref.candidate_id != self.candidate_id
            or ref.evidence_kind != FVG_EVENT_EVIDENCE_KIND
            or ref.source_binding_hash != self.decision_surface_binding_hash
            or ref.source_prefix_hash != self.decision_surface_prefix_hash
            or ref.available_at > self.decision_key
            for ref in self.visible_lifecycle_events
        ):
            raise CandidatePilotError("visible lifecycle evidence is not source-backed at the decision boundary")
        if any(
            ref.candidate_id != self.candidate_id
            or ref.source_binding_hash is not None
            or ref.source_prefix_hash != self.decision_surface_prefix_hash
            for ref in self.unknown_context_references
        ):
            raise CandidatePilotError("unknown/missing context references are not explicit or correctly bound")
        expected = _candidate_context_id(self)
        if self.context_id and self.context_id != expected:
            raise CandidatePilotError("candidate contextual identity mismatch")
        if not self.context_id:
            object.__setattr__(self, "context_id", expected)

    @property
    def evidence_references(self) -> tuple[FactualEvidenceReference, ...]:
        return (self.entity_evidence,) + self.visible_lifecycle_events + self.unknown_context_references


def _candidate_context_id(context: CandidateContext) -> str:
    return canonical_sha256(
        domain="CONTEXTUAL_FVG_CANDIDATE_CONTEXT_ID_V1",
        payload={
            "candidate_id": context.candidate_id,
            "candidate_identity_hash": context.candidate_identity_hash,
            "decision_key": context.decision_key,
            "origin_positions": list(context.origin_positions),
            "creation_position": context.creation_position,
            "availability_position": context.availability_position,
            "availability_key": context.availability_key,
            "factual_attributes": [
                {"column": column, "cell": cell.canonical_payload()}
                for column, cell in context.factual_attributes
            ],
            "entity_evidence_reference_id": context.entity_evidence.reference_id,
            "visible_lifecycle_event_reference_ids": [ref.reference_id for ref in context.visible_lifecycle_events],
            "unknown_context_reference_ids": [ref.reference_id for ref in context.unknown_context_references],
            "domain_availability": [list(item) for item in context.domain_availability],
            "producer_policy_identity_hash": context.source_provenance.producer_policy_identity.identity_hash,
            "decision_market_prefix_hash": context.decision_market_prefix_hash,
            "decision_surface_binding_hash": context.decision_surface_binding_hash,
            "decision_surface_prefix_hash": context.decision_surface_prefix_hash,
            "decision_asof_view_hash": context.decision_asof_view_hash,
        },
    )


@dataclass(frozen=True)
class CandidateUniverse:
    """Complete visible FVG universe at one boundary; ``_case`` is verification-only."""

    universe_id: str
    case_id: str
    timeline_id: str
    decision_key: InformationKey
    decision_market_prefix_hash: str
    source_binding_hash: str
    source_prefix_hash: str
    asof_view_hash: str
    eligibility_policy_id: str
    candidates: tuple[CandidateContext, ...]
    _case: TrajectoryDecisionCase = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        for name in (
            "case_id", "decision_market_prefix_hash", "source_binding_hash",
            "source_prefix_hash", "asof_view_hash",
        ):
            _require_hash(getattr(self, name), name)
        if self.universe_id:
            _require_hash(self.universe_id, "universe_id")
        _require_text(self.timeline_id, "universe timeline_id")
        _require_text(self.eligibility_policy_id, "eligibility_policy_id")
        if not isinstance(self.decision_key, InformationKey) or self.decision_key.timeline_id != self.timeline_id:
            raise CandidatePilotError("universe decision key/timeline mismatch")
        if not isinstance(self.candidates, tuple) or any(not isinstance(item, CandidateContext) for item in self.candidates):
            raise CandidatePilotError("candidate universe must be an immutable tuple")
        ids = tuple(candidate.candidate_id for candidate in self.candidates)
        if len(set(ids)) != len(ids):
            raise CandidatePilotError("candidate universe contains duplicate canonical producer IDs")
        if any(
            candidate.decision_key != self.decision_key
            or candidate.decision_market_prefix_hash != self.decision_market_prefix_hash
            or candidate.decision_surface_binding_hash != self.source_binding_hash
            or candidate.decision_surface_prefix_hash != self.source_prefix_hash
            for candidate in self.candidates
        ):
            raise CandidatePilotError("candidate context is not bound to the universe decision prefix")
        if not isinstance(self._case, TrajectoryDecisionCase) or self._case.case_id != self.case_id:
            raise CandidatePilotError("universe verification case is missing or mismatched")
        if tuple(binding.stable_binding_hash for binding in self._case.surface_prefix_bindings) != (self.source_binding_hash,):
            raise CandidatePilotError("universe must bind exactly its one FVG source surface")
        expected = _candidate_universe_id(self)
        if self.universe_id and self.universe_id != expected:
            raise CandidatePilotError("candidate universe identity mismatch")
        if not self.universe_id:
            object.__setattr__(self, "universe_id", expected)

    @property
    def eligible_candidate_ids(self) -> tuple[str, ...]:
        """All and only canonical FVG IDs visible in the decision-time entity table."""
        return tuple(candidate.candidate_id for candidate in self.candidates)

    @property
    def source_visible_entity_count(self) -> int:
        return len(self.candidates)

    def candidate(self, candidate_id: str) -> CandidateContext:
        matches = [item for item in self.candidates if item.candidate_id == candidate_id]
        if len(matches) != 1:
            raise CandidatePilotError("candidate is not registered exactly once")
        return matches[0]


def _candidate_universe_id(universe: CandidateUniverse) -> str:
    return canonical_sha256(
        domain="CONTEXTUAL_FVG_CANDIDATE_UNIVERSE_V1",
        payload={
            "pilot_contract_version": PILOT_CONTRACT_VERSION,
            "case_id": universe.case_id,
            "timeline_id": universe.timeline_id,
            "decision_key": universe.decision_key,
            "decision_market_prefix_hash": universe.decision_market_prefix_hash,
            "source_binding_hash": universe.source_binding_hash,
            "source_prefix_hash": universe.source_prefix_hash,
            "asof_view_hash": universe.asof_view_hash,
            "eligibility_policy_id": universe.eligibility_policy_id,
            "candidate_context_ids_in_source_order": [item.context_id for item in universe.candidates],
        },
    )


def _cell_text(cell: FrozenCell, *, field_name: str) -> str:
    if cell.kind not in (FrozenCellKind.STRING, FrozenCellKind.NUMBER) or not isinstance(cell.value, str):
        raise CandidatePilotError(f"source {field_name} is not a canonical ID/string fact")
    return cell.value


def _cell_position(cell: FrozenCell, *, field_name: str) -> int:
    if cell.kind is not FrozenCellKind.NUMBER or not isinstance(cell.value, str):
        raise CandidatePilotError(f"source {field_name} is not a numeric position fact")
    try:
        number = Decimal(cell.value)
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise CandidatePilotError(f"source {field_name} is not a valid integer position") from exc
    if not number.is_finite() or number != number.to_integral_value() or number < 0:
        raise CandidatePilotError(f"source {field_name} is not a nonnegative integer position")
    return int(number)


def _column_index(table: FrozenSurfaceTable, column: str) -> int:
    matches = [index for index, value in enumerate(table.columns) if value == column]
    if len(matches) != 1:
        raise CandidatePilotError(f"verified FVG source column missing or duplicated: {column}")
    return matches[0]


def _key_at_position(adapter: TimelineAdapter, index: pd.Index, position: int) -> InformationKey:
    try:
        return adapter.key_for_position(
            index,
            position,
            InformationPhase.COMPLETED_ROW_AVAILABLE,
        )
    except Exception as exc:
        raise CandidatePilotError(f"could not construct a source availability key: {exc}") from exc


def _binding_for_case(case: TrajectoryDecisionCase) -> SurfacePrefixBinding:
    matches = [binding for binding in case.surface_prefix_bindings if binding.domain == "FVG"]
    if len(matches) != 1 or len(case.surface_prefix_bindings) != 1:
        raise CandidatePilotError("pilot requires exactly one bound Stage4B2 FVG surface")
    return matches[0]


def _fvg_instance(view: AsOfSurfaceView, binding_hash: str):
    matches = [
        item for item in view.surfaces
        if item.domain == "FVG" and item.surface_family == "STAGE4B2"
        and item.stable_binding_hash == binding_hash
    ]
    if len(matches) != 1 or len(matches[0].tables) != 4:
        raise CandidatePilotError("verified Stage4B2 FVG as-of tables are unavailable or ambiguous")
    instance = matches[0]
    if tuple(table.table_name for table in instance.tables) != (
        "FVG:0", "FVG:1", "FVG:2", "FVG:3"
    ):
        raise CandidatePilotError("verified Stage4B2 FVG tables have unexpected public ordering")
    return instance


def _availability_payload(view: AsOfSurfaceView) -> tuple[tuple[str, str, int], ...]:
    return tuple((item.domain, item.status.value, item.bound_surface_count) for item in view.availability)


def _make_missing_context_reference(
    *,
    candidate_id: str,
    evidence_kind: str,
    producer_domain: str,
    source_prefix_hash: str,
    decision_key: InformationKey,
    row_columns: tuple[str, ...],
    row: tuple[FrozenCell, ...],
) -> FactualEvidenceReference:
    return _make_evidence_reference(
        candidate_id=candidate_id,
        evidence_kind=evidence_kind,
        producer_domain=producer_domain,
        source_binding_hash=None,
        source_prefix_hash=source_prefix_hash,
        available_at=decision_key,
        row_columns=row_columns,
        row=row,
    )


def build_fvg_candidate_universe(
    *,
    timeline: MarketObservationTimeline,
    adapter: TimelineAdapter,
    market_history: pd.DataFrame,
    fvg_surface: s4b2.Stage4B2FVGSurface,
    decision_key: InformationKey,
) -> CandidateUniverse:
    """Enumerate every decision-visible normalized FVG entity, with no cap/filter.

    Only the public Stage4B2 FVG surface and the public trajectory case/query/
    resolution APIs establish source facts. The complete entity table projected
    at ``decision_key`` is the eligible universe; later lifecycle/outcome rows
    are not consulted when choosing candidates.
    """
    if not isinstance(fvg_surface, s4b2.Stage4B2FVGSurface):
        raise CandidatePilotError("fvg_surface must be the public Stage4B2 FVG surface")
    try:
        case = create_trajectory_decision_case(
            timeline=timeline,
            adapter=adapter,
            market_history=market_history,
            decision_key=decision_key,
            surfaces=(fvg_surface,),
            parent_snapshot=None,
        )
        view = decision_surface_view(case=case, surfaces=(fvg_surface,))
    except Exception as exc:
        raise CandidatePilotError(f"could not verify/register historical FVG source: {exc}") from exc

    binding = _binding_for_case(case)
    instance = _fvg_instance(view, binding.stable_binding_hash)
    entity_table = instance.tables[2]
    event_table = instance.tables[3]
    id_column = _column_index(entity_table, "fvg_id")
    event_id_column = _column_index(event_table, "fvg_id")
    event_position_column = _column_index(event_table, "event_position")
    event_type_column = _column_index(event_table, "event_type")

    entity_rows: list[tuple[str, tuple[FrozenCell, ...]]] = []
    for row in entity_table.rows:
        candidate_id = _cell_text(row[id_column], field_name="fvg_id")
        entity_rows.append((candidate_id, row))
    candidate_ids = tuple(candidate_id for candidate_id, _ in entity_rows)
    if len(set(candidate_ids)) != len(candidate_ids):
        raise CandidatePilotError("visible normalized FVG table has duplicate canonical IDs")

    source_policy = ProducerPolicyIdentity(
        producer_domain="FVG",
        surface_family=instance.surface_family,
        contract_version=instance.contract_version,
        configuration_identity_hash=instance.configuration_identity_hash,
        policy_id="STAGE4B2_FVG_PUBLIC_CONTRACT",
        policy_version=instance.contract_version,
        policy_sha256=instance.configuration_identity_hash,
    )
    source_provenance = SourceArtifactProvenance(
        source_timeline_id=timeline.timeline_id,
        source_timeline_hash=binding.source_timeline_hash,
        source_surface_id=binding.source_surface_id,
        reconstruction_input_hash=fvg_surface.reconstruction_input_hash,
        verification_scope=binding.verification_scope,
        producer_policy_identity=source_policy,
    )
    domain_availability = _availability_payload(view)
    candidates: list[CandidateContext] = []

    for candidate_id, row in entity_rows:
        locator = ObservedEntityLocator(
            producer_domain="FVG",
            stable_binding_hash=binding.stable_binding_hash,
            canonical_entity_id=candidate_id,
        )
        try:
            resolved = resolve_observed_entity(
                case=case,
                surfaces=(fvg_surface,),
                locator=locator,
            )
        except Exception as exc:
            raise CandidatePilotError(f"could not resolve source-visible FVG {candidate_id}: {exc}") from exc
        if resolved.row_columns != entity_table.columns or resolved.row != row:
            raise CandidatePilotError("resolved FVG row differs from the complete visible source entity table")
        if resolved.availability_position > decision_key.bar_position:
            raise CandidatePilotError("future-created FVG leaked into the decision-visible entity table")
        if resolved.creation_position is None:
            raise CandidatePilotError("FVG source row lacks a factual creation position")
        availability_key = _key_at_position(adapter, market_history.index, resolved.availability_position)
        if availability_key > decision_key:
            raise CandidatePilotError("FVG creation/availability key is later than the declared decision")

        entity_ref = _make_evidence_reference(
            candidate_id=candidate_id,
            evidence_kind="FVG_NORMALIZED_SOURCE_ENTITY_ROW",
            producer_domain="FVG",
            source_binding_hash=binding.stable_binding_hash,
            source_prefix_hash=instance.prefix_hash,
            available_at=availability_key,
            row_columns=entity_table.columns,
            row=row,
        )
        lifecycle_refs: list[FactualEvidenceReference] = []
        creation_event_found = False
        for event_row in event_table.rows:
            if _cell_text(event_row[event_id_column], field_name="normalized event fvg_id") != candidate_id:
                continue
            event_position = _cell_position(event_row[event_position_column], field_name="event_position")
            event_key = _key_at_position(adapter, market_history.index, event_position)
            if event_key > decision_key:
                raise CandidatePilotError("future lifecycle event leaked into decision-time FVG context")
            event_type = _cell_text(event_row[event_type_column], field_name="event_type")
            if event_type == "FVG_CREATED" and event_position == resolved.availability_position:
                creation_event_found = True
            lifecycle_refs.append(
                _make_evidence_reference(
                    candidate_id=candidate_id,
                    evidence_kind=FVG_EVENT_EVIDENCE_KIND,
                    producer_domain="FVG",
                    source_binding_hash=binding.stable_binding_hash,
                    source_prefix_hash=instance.prefix_hash,
                    available_at=event_key,
                    row_columns=event_table.columns,
                    row=event_row,
                )
            )
        if not creation_event_found:
            raise CandidatePilotError("source-visible FVG lacks its source-backed creation lifecycle event")

        unknown_refs: list[FactualEvidenceReference] = []
        for domain, status, count in domain_availability:
            if status == AvailabilityStatus.NOT_SUPPLIED.value:
                unknown_refs.append(
                    _make_missing_context_reference(
                        candidate_id=candidate_id,
                        evidence_kind="CONTEXT_DOMAIN_NOT_SUPPLIED",
                        producer_domain=domain,
                        source_prefix_hash=instance.prefix_hash,
                        decision_key=decision_key,
                        row_columns=("domain", "availability_status", "bound_surface_count"),
                        row=(
                            FrozenCell(FrozenCellKind.STRING, domain),
                            FrozenCell(FrozenCellKind.STRING, status),
                            FrozenCell(FrozenCellKind.NUMBER, str(count)),
                        ),
                    )
                )
        factual_attributes = tuple(zip(resolved.row_columns, resolved.row))
        for name, cell in factual_attributes:
            if cell.kind is FrozenCellKind.MISSING:
                unknown_refs.append(
                    _make_missing_context_reference(
                        candidate_id=candidate_id,
                        evidence_kind="SOURCE_ATTRIBUTE_MISSING",
                        producer_domain="FVG",
                        source_prefix_hash=instance.prefix_hash,
                        decision_key=decision_key,
                        row_columns=("field", "cell_kind"),
                        row=(
                            FrozenCell(FrozenCellKind.STRING, name),
                            FrozenCell(FrozenCellKind.STRING, cell.kind.value),
                        ),
                    )
                )
        context = CandidateContext(
            candidate_id=candidate_id,
            candidate_identity_hash=resolved.identity_hash,
            decision_key=decision_key,
            origin_positions=resolved.origin_positions,
            creation_position=resolved.creation_position,
            availability_position=resolved.availability_position,
            availability_key=availability_key,
            factual_attributes=factual_attributes,
            entity_evidence=entity_ref,
            visible_lifecycle_events=tuple(lifecycle_refs),
            unknown_context_references=tuple(unknown_refs),
            domain_availability=domain_availability,
            source_provenance=source_provenance,
            decision_market_prefix_hash=case.decision_prefix_hash,
            decision_surface_binding_hash=binding.stable_binding_hash,
            decision_surface_prefix_hash=instance.prefix_hash,
            decision_asof_view_hash=view.view_hash,
            context_id="",
        )
        candidates.append(context)

    universe = CandidateUniverse(
        universe_id="",
        case_id=case.case_id,
        timeline_id=case.timeline_id,
        decision_key=decision_key,
        decision_market_prefix_hash=case.decision_prefix_hash,
        source_binding_hash=binding.stable_binding_hash,
        source_prefix_hash=instance.prefix_hash,
        asof_view_hash=view.view_hash,
        eligibility_policy_id=FVG_ELIGIBILITY_POLICY_ID,
        candidates=tuple(candidates),
        _case=case,
    )
    return universe


@dataclass(frozen=True)
class EvidenceBatch:
    """Immutable retrieval result; public assessment APIs do not accept caller batches."""

    batch_id: str
    case_id: str
    candidate_id: str
    source_binding_hash: str
    start_key: InformationKey
    as_of_key: InformationKey
    source_prefix_hash: str
    asof_view_hash: str
    evidence: tuple[FactualEvidenceReference, ...]

    def __post_init__(self) -> None:
        for name in ("batch_id", "case_id", "source_binding_hash", "source_prefix_hash", "asof_view_hash"):
            _require_hash(getattr(self, name), name)
        _require_text(self.candidate_id, "batch candidate_id")
        if not isinstance(self.start_key, InformationKey) or not isinstance(self.as_of_key, InformationKey):
            raise CandidatePilotError("evidence batch keys are required")
        if self.start_key.timeline_id != self.as_of_key.timeline_id or not self.start_key < self.as_of_key:
            raise CandidatePilotError("evidence batch must advance on one causal timeline")
        if not isinstance(self.evidence, tuple) or any(not isinstance(ref, FactualEvidenceReference) for ref in self.evidence):
            raise CandidatePilotError("evidence batch rows must be immutable references")
        if len({ref.reference_id for ref in self.evidence}) != len(self.evidence):
            raise CandidatePilotError("evidence batch contains duplicate references")
        for ref in self.evidence:
            if ref.available_at.timeline_id != self.start_key.timeline_id:
                raise CandidatePilotError("evidence availability must use the batch causal timeline")
            if (
                ref.candidate_id != self.candidate_id
                or ref.evidence_kind != FVG_EVENT_EVIDENCE_KIND
                or ref.producer_domain != "FVG"
            ):
                raise CandidatePilotError("revision batch may contain only this candidate's FVG lifecycle events")
            if ref.source_binding_hash != self.source_binding_hash:
                raise CandidatePilotError("per-reference source binding differs from the batch binding")
            if ref.source_prefix_hash != self.source_prefix_hash:
                raise CandidatePilotError("per-reference source prefix differs from the batch prefix")
            if ref.row_columns != _FVG_NORMALIZED_EVENT_COLUMNS:
                raise CandidatePilotError("revision reference does not use the exact normalized FVG event schema")
            row = dict(zip(ref.row_columns, ref.row))
            row_candidate_id = _cell_text(row["fvg_id"], field_name="normalized event fvg_id")
            event_position = _cell_position(row["event_position"], field_name="event_position")
            if row_candidate_id != self.candidate_id:
                raise CandidatePilotError("normalized event row belongs to another canonical FVG ID")
            if event_position != ref.available_at.bar_position:
                raise CandidatePilotError("event position and claimed availability position disagree")
            if (
                ref.available_at.information_phase is not InformationPhase.COMPLETED_ROW_AVAILABLE
                or ref.available_at.deterministic_sequence != 0
            ):
                raise CandidatePilotError("FVG lifecycle evidence must use its completed-row availability key")
            if row["same_information_batch_order_unknown"].kind is not FrozenCellKind.BOOLEAN:
                raise CandidatePilotError("same-batch ordering ambiguity must remain an explicit boolean fact")
            if not self.start_key < ref.available_at or ref.available_at > self.as_of_key:
                raise CandidatePilotError("revision batch contains evidence outside its causal interval")
        expected = _evidence_batch_id(
            case_id=self.case_id,
            candidate_id=self.candidate_id,
            source_binding_hash=self.source_binding_hash,
            start_key=self.start_key,
            as_of_key=self.as_of_key,
            source_prefix_hash=self.source_prefix_hash,
            asof_view_hash=self.asof_view_hash,
            reference_ids=tuple(ref.reference_id for ref in self.evidence),
        )
        if self.batch_id != expected:
            raise CandidatePilotError("evidence batch identity mismatch")


def _evidence_batch_id(
    *, case_id: str, candidate_id: str, source_binding_hash: str,
    start_key: InformationKey, as_of_key: InformationKey, source_prefix_hash: str,
    asof_view_hash: str, reference_ids: tuple[str, ...],
) -> str:
    return canonical_sha256(
        domain="CONTEXTUAL_FVG_NEW_EVIDENCE_BATCH_V1",
        payload={
            "case_id": case_id,
            "candidate_id": candidate_id,
            "source_binding_hash": source_binding_hash,
            "start_key": start_key,
            "as_of_key": as_of_key,
            "source_prefix_hash": source_prefix_hash,
            "asof_view_hash": asof_view_hash,
            "new_reference_ids": list(reference_ids),
        },
    )


def retrieve_new_fvg_factual_evidence(
    *,
    universe: CandidateUniverse,
    candidate_id: str,
    timeline: MarketObservationTimeline,
    adapter: TimelineAdapter,
    market_history: pd.DataFrame,
    fvg_surface: s4b2.Stage4B2FVGSurface,
    start_key: InformationKey,
    as_of_key: InformationKey,
) -> EvidenceBatch:
    """Return only candidate-matched normalized FVG event rows in ``(start, as_of]``.

    Per-bar summaries and unbound domains are intentionally outside this V1
    revision evidence contract; an empty batch cannot create a later revision.
    """
    candidate = universe.candidate(candidate_id)
    if not isinstance(fvg_surface, s4b2.Stage4B2FVGSurface):
        raise CandidatePilotError("fvg_surface must be the public Stage4B2 FVG surface")
    if not isinstance(start_key, InformationKey) or not isinstance(as_of_key, InformationKey):
        raise CandidatePilotError("revision interval requires explicit InformationKeys")
    if start_key.timeline_id != universe.timeline_id or as_of_key.timeline_id != universe.timeline_id:
        raise CandidatePilotError("revision keys must belong to the registered timeline")
    if start_key < universe.decision_key or not start_key < as_of_key:
        raise CandidatePilotError("revision interval must advance from the registered historical boundary")
    if start_key.information_phase not in (
        InformationPhase.COMPLETED_ROW_AVAILABLE,
        InformationPhase.RESEARCH_SNAPSHOT_AVAILABLE,
    ):
        raise CandidatePilotError("revision start key is not a completed-row boundary")
    if as_of_key.information_phase not in (
        InformationPhase.COMPLETED_ROW_AVAILABLE,
        InformationPhase.RESEARCH_SNAPSHOT_AVAILABLE,
    ):
        raise CandidatePilotError("revision as-of key is not a completed-row boundary")
    try:
        verify_case_source_prefix(
            case=universe._case,
            timeline=timeline,
            adapter=adapter,
            market_history=market_history,
        )
        adapter.validate_key(start_key, market_history.index)
        adapter.validate_key(as_of_key, market_history.index)
        view = create_asof_surface_view(
            case=universe._case,
            surfaces=(fvg_surface,),
            as_of_key=as_of_key,
        )
    except Exception as exc:
        raise CandidatePilotError(f"later FVG source/as-of verification failed closed: {exc}") from exc
    instance = _fvg_instance(view, universe.source_binding_hash)
    entity_table, event_table = instance.tables[2], instance.tables[3]
    if event_table.columns != _FVG_NORMALIZED_EVENT_COLUMNS:
        raise CandidatePilotError("verified FVG source exposes an unexpected normalized event schema")
    id_column = _column_index(entity_table, "fvg_id")
    entity_rows = [row for row in entity_table.rows if _cell_text(row[id_column], field_name="fvg_id") == candidate_id]
    if len(entity_rows) != 1 or tuple(zip(entity_table.columns, entity_rows[0])) != candidate.factual_attributes:
        raise CandidatePilotError("registered FVG source attributes changed or disappeared at revision time")

    event_id_column = _column_index(event_table, "fvg_id")
    event_position_column = _column_index(event_table, "event_position")
    refs: list[FactualEvidenceReference] = []
    for row in event_table.rows:
        if _cell_text(row[event_id_column], field_name="normalized event fvg_id") != candidate_id:
            continue
        event_position = _cell_position(row[event_position_column], field_name="event_position")
        available_at = _key_at_position(adapter, market_history.index, event_position)
        if start_key < available_at <= as_of_key:
            refs.append(
                _make_evidence_reference(
                    candidate_id=candidate_id,
                    evidence_kind=FVG_EVENT_EVIDENCE_KIND,
                    producer_domain="FVG",
                    source_binding_hash=universe.source_binding_hash,
                    source_prefix_hash=instance.prefix_hash,
                    available_at=available_at,
                    row_columns=event_table.columns,
                    row=row,
                )
            )
    if len({ref.reference_id for ref in refs}) != len(refs):
        raise CandidatePilotError("later FVG lifecycle source contains duplicate evidence identities")
    batch_id = _evidence_batch_id(
        case_id=universe.case_id,
        candidate_id=candidate_id,
        source_binding_hash=universe.source_binding_hash,
        start_key=start_key,
        as_of_key=as_of_key,
        source_prefix_hash=instance.prefix_hash,
        asof_view_hash=view.view_hash,
        reference_ids=tuple(ref.reference_id for ref in refs),
    )
    return EvidenceBatch(
        batch_id=batch_id,
        case_id=universe.case_id,
        candidate_id=candidate_id,
        source_binding_hash=universe.source_binding_hash,
        start_key=start_key,
        as_of_key=as_of_key,
        source_prefix_hash=instance.prefix_hash,
        asof_view_hash=view.view_hash,
        evidence=tuple(refs),
    )


@dataclass(frozen=True)
class CandidateAssessmentRecord:
    assessment_id: str
    candidate_id: str
    candidate_identity_hash: str
    question: ResearchQuestion
    category: AssessmentCategory
    protocol: AssessmentProtocolIdentity
    as_of_key: InformationKey
    evidence_reference_ids: tuple[str, ...]
    supporting_reference_ids: tuple[str, ...]
    conflicting_reference_ids: tuple[str, ...]
    unknown_reference_ids: tuple[str, ...]
    provisional_status: ProvisionalStatus
    reason: str
    declaration_reference: str | None
    previous_assessment_id: str | None
    new_evidence_reference_ids: tuple[str, ...]
    evidence_batch_id: str | None

    def __post_init__(self) -> None:
        if self.assessment_id:
            _require_hash(self.assessment_id, "assessment_id")
        _require_text(self.candidate_id, "assessment candidate_id")
        _require_hash(self.candidate_identity_hash, "assessment candidate_identity_hash")
        if not isinstance(self.question, ResearchQuestion) or not isinstance(self.protocol, AssessmentProtocolIdentity):
            raise CandidatePilotError("assessment question and protocol identities are required")
        if not isinstance(self.category, AssessmentCategory) or not isinstance(self.provisional_status, ProvisionalStatus):
            raise CandidatePilotError("assessment category/status is invalid")
        if self.category is AssessmentCategory.EMPIRICALLY_VALIDATED_RELEVANCE:
            raise CandidatePilotError("empirically validated relevance is reserved and cannot be generated by this pilot")
        if not isinstance(self.as_of_key, InformationKey):
            raise CandidatePilotError("assessment as-of key is required")
        for name in (
            "evidence_reference_ids", "supporting_reference_ids", "conflicting_reference_ids",
            "unknown_reference_ids", "new_evidence_reference_ids",
        ):
            values = getattr(self, name)
            if not isinstance(values, tuple) or any(not _is_hash(item) for item in values):
                raise CandidatePilotError(f"{name} must be an immutable tuple of evidence hashes")
            if len(set(values)) != len(values):
                raise CandidatePilotError(f"{name} contains duplicate evidence references")
        if not self.evidence_reference_ids:
            raise CandidatePilotError("assessment must cite at least one source or explicit-unknown reference")
        evidence = set(self.evidence_reference_ids)
        if any(
            not set(getattr(self, name)).issubset(evidence)
            for name in ("supporting_reference_ids", "conflicting_reference_ids", "unknown_reference_ids", "new_evidence_reference_ids")
        ):
            raise CandidatePilotError("assessment evidence classifications must reference cited evidence")
        _require_text(self.reason, "assessment reason")
        if self.category in (AssessmentCategory.DECLARED_HUMAN_ASSESSMENT, AssessmentCategory.DECLARED_OPERATIONAL_POLICY):
            _require_text(self.declaration_reference, "human/policy declaration reference")
        elif self.declaration_reference is not None:
            _require_text(self.declaration_reference, "declaration_reference")
        if self.previous_assessment_id is not None:
            _require_hash(self.previous_assessment_id, "previous_assessment_id")
        if self.evidence_batch_id is not None:
            _require_hash(self.evidence_batch_id, "evidence_batch_id")
        if bool(self.new_evidence_reference_ids) != (self.evidence_batch_id is not None):
            raise CandidatePilotError("new evidence IDs and evidence batch reference must be supplied together")
        expected = _assessment_id(self)
        if self.assessment_id and self.assessment_id != expected:
            raise CandidatePilotError("assessment identity/hash mismatch")
        if not self.assessment_id:
            object.__setattr__(self, "assessment_id", expected)

    @property
    def key(self) -> tuple[str, str]:
        return (self.candidate_id, self.question.question_id)


def _assessment_id(record: CandidateAssessmentRecord) -> str:
    return canonical_sha256(
        domain="CONTEXTUAL_CANDIDATE_ASSESSMENT_RECORD_V1",
        payload={
            "candidate_id": record.candidate_id,
            "candidate_identity_hash": record.candidate_identity_hash,
            "question_identity_hash": record.question.identity_hash,
            "category": record.category.value,
            "protocol_identity_hash": record.protocol.protocol_sha256,
            "as_of_key": record.as_of_key,
            "evidence_reference_ids": list(record.evidence_reference_ids),
            "supporting_reference_ids": list(record.supporting_reference_ids),
            "conflicting_reference_ids": list(record.conflicting_reference_ids),
            "unknown_reference_ids": list(record.unknown_reference_ids),
            "provisional_status": record.provisional_status.value,
            "reason": record.reason,
            "declaration_reference": record.declaration_reference,
            "previous_assessment_id": record.previous_assessment_id,
            "new_evidence_reference_ids": list(record.new_evidence_reference_ids),
            "evidence_batch_id": record.evidence_batch_id,
        },
    )


def _make_assessment(**values) -> CandidateAssessmentRecord:
    return CandidateAssessmentRecord(assessment_id="", **values)


@dataclass(frozen=True)
class CandidateCoverageRecord:
    coverage_id: str
    candidate_id: str
    question_id: str
    state: CandidateCoverageState
    as_of_key: InformationKey
    reason: str
    assessment_id: str | None
    previous_coverage_id: str | None
    restoration_is_not_utility_evidence: bool = False

    def __post_init__(self) -> None:
        if self.coverage_id:
            _require_hash(self.coverage_id, "coverage_id")
        _require_text(self.candidate_id, "coverage candidate_id")
        _require_text(self.question_id, "coverage question_id")
        if not isinstance(self.state, CandidateCoverageState) or not isinstance(self.as_of_key, InformationKey):
            raise CandidatePilotError("coverage state/as-of key is invalid")
        _require_text(self.reason, "coverage reason")
        if self.assessment_id is not None:
            _require_hash(self.assessment_id, "coverage assessment_id")
        if self.previous_coverage_id is not None:
            _require_hash(self.previous_coverage_id, "previous_coverage_id")
        if not isinstance(self.restoration_is_not_utility_evidence, bool):
            raise CandidatePilotError("restoration flag must be boolean")
        if self.restoration_is_not_utility_evidence and (
            self.state is not CandidateCoverageState.REGISTERED
            or "not evidence of trading utility" not in self.reason.lower()
        ):
            raise CandidatePilotError("restoration must remain an investigation action, not utility evidence")
        if (self.state is CandidateCoverageState.ASSESSED) != (self.assessment_id is not None):
            raise CandidatePilotError("ASSESSED coverage must link an assessment; other states must not")
        expected = _coverage_id(self)
        if self.coverage_id and self.coverage_id != expected:
            raise CandidatePilotError("coverage identity/hash mismatch")
        if not self.coverage_id:
            object.__setattr__(self, "coverage_id", expected)


def _coverage_id(record: CandidateCoverageRecord) -> str:
    return canonical_sha256(
        domain="CONTEXTUAL_CANDIDATE_COVERAGE_RECORD_V1",
        payload={
            "candidate_id": record.candidate_id,
            "question_id": record.question_id,
            "state": record.state.value,
            "as_of_key": record.as_of_key,
            "reason": record.reason,
            "assessment_id": record.assessment_id,
            "previous_coverage_id": record.previous_coverage_id,
            "restoration_is_not_utility_evidence": record.restoration_is_not_utility_evidence,
        },
    )


def _make_coverage(**values) -> CandidateCoverageRecord:
    return CandidateCoverageRecord(coverage_id="", **values)


@dataclass(frozen=True)
class CoverageReconciliation:
    question_id: str
    eligible_candidate_ids: tuple[str, ...]
    accounted_candidate_ids: tuple[str, ...]
    missing_candidate_ids: tuple[str, ...]
    extra_candidate_ids: tuple[str, ...]
    state_counts: tuple[tuple[str, int], ...]

    @property
    def reconciled(self) -> bool:
        return not self.missing_candidate_ids and not self.extra_candidate_ids


@dataclass(frozen=True)
class CandidateResearchLedger:
    """Immutable register and append-only assessment/coverage/evidence history."""

    universe: CandidateUniverse
    questions: tuple[ResearchQuestion, ...]
    assessments: tuple[CandidateAssessmentRecord, ...]
    coverage_history: tuple[CandidateCoverageRecord, ...]
    factual_evidence: tuple[FactualEvidenceReference, ...]
    evidence_batches: tuple[EvidenceBatch, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.universe, CandidateUniverse):
            raise CandidatePilotError("research ledger requires a registered candidate universe")
        if not isinstance(self.questions, tuple) or not self.questions or any(
            not isinstance(item, ResearchQuestion) for item in self.questions
        ):
            raise CandidatePilotError("at least one immutable research question must be registered")
        question_ids = tuple(item.question_id for item in self.questions)
        if len(set(question_ids)) != len(question_ids):
            raise CandidatePilotError("duplicate research question IDs")
        if any(not isinstance(items, tuple) for items in (self.assessments, self.coverage_history, self.factual_evidence, self.evidence_batches)):
            raise CandidatePilotError("ledger histories must be immutable tuples")
        if any(not isinstance(item, CandidateAssessmentRecord) for item in self.assessments):
            raise CandidatePilotError("invalid assessment history record")
        if any(not isinstance(item, CandidateCoverageRecord) for item in self.coverage_history):
            raise CandidatePilotError("invalid coverage history record")
        if any(not isinstance(item, FactualEvidenceReference) for item in self.factual_evidence):
            raise CandidatePilotError("invalid factual evidence history record")
        if any(not isinstance(item, EvidenceBatch) for item in self.evidence_batches):
            raise CandidatePilotError("invalid new-evidence batch history record")
        _validate_ledger(self)

    def assessments_for(self, candidate_id: str, question_id: str) -> tuple[CandidateAssessmentRecord, ...]:
        return tuple(record for record in self.assessments if record.key == (candidate_id, question_id))

    def latest_assessment(self, candidate_id: str, question_id: str) -> CandidateAssessmentRecord | None:
        matches = self.assessments_for(candidate_id, question_id)
        return matches[-1] if matches else None

    def latest_coverage(self, candidate_id: str, question_id: str) -> CandidateCoverageRecord:
        matches = [
            record for record in self.coverage_history
            if (record.candidate_id, record.question_id) == (candidate_id, question_id)
        ]
        if not matches:
            raise CandidatePilotError("coverage record is missing for a registered candidate/question pair")
        return matches[-1]


def _validate_ledger(ledger: CandidateResearchLedger) -> None:
    candidate_by_id = {item.candidate_id: item for item in ledger.universe.candidates}
    question_by_id = {item.question_id: item for item in ledger.questions}
    initial_evidence = tuple(
        evidence
        for candidate in ledger.universe.candidates
        for evidence in candidate.evidence_references
    )
    if ledger.factual_evidence[:len(initial_evidence)] != initial_evidence:
        raise CandidatePilotError("initial factual evidence no longer matches the registered candidate snapshot")
    evidence_by_id: dict[str, FactualEvidenceReference] = {}
    for evidence in ledger.factual_evidence:
        if evidence.candidate_id not in candidate_by_id:
            raise CandidatePilotError("evidence references an unregistered candidate")
        if evidence.reference_id in evidence_by_id:
            raise CandidatePilotError("duplicate evidence reference in append-only ledger")
        evidence_by_id[evidence.reference_id] = evidence
    batch_by_id: dict[str, EvidenceBatch] = {}
    expected_evidence_order = [item.reference_id for item in initial_evidence]
    appended_evidence_ids = set(expected_evidence_order)
    for batch in ledger.evidence_batches:
        if batch.batch_id in batch_by_id:
            raise CandidatePilotError("duplicate evidence batch in append-only ledger")
        if batch.case_id != ledger.universe.case_id or batch.source_binding_hash != ledger.universe.source_binding_hash:
            raise CandidatePilotError("evidence batch is bound to another source/case")
        if batch.candidate_id not in candidate_by_id:
            raise CandidatePilotError("evidence batch references an unregistered candidate")
        for evidence in batch.evidence:
            if evidence.reference_id in appended_evidence_ids:
                raise CandidatePilotError("new evidence was already present before its batch")
            if evidence_by_id.get(evidence.reference_id) != evidence:
                raise CandidatePilotError("evidence batch fact is missing or changed in the append-only evidence history")
            appended_evidence_ids.add(evidence.reference_id)
            expected_evidence_order.append(evidence.reference_id)
        batch_by_id[batch.batch_id] = batch
    if tuple(expected_evidence_order) != tuple(item.reference_id for item in ledger.factual_evidence):
        raise CandidatePilotError("factual evidence history is not append-only aligned with its retrieval batches")

    prior_assessments: dict[tuple[str, str], CandidateAssessmentRecord] = {}
    assessment_ids: set[str] = set()
    for record in ledger.assessments:
        if record.assessment_id in assessment_ids:
            raise CandidatePilotError("duplicate assessment identity")
        assessment_ids.add(record.assessment_id)
        if record.candidate_id not in candidate_by_id or record.question.question_id not in question_by_id:
            raise CandidatePilotError("assessment references an unregistered candidate/question")
        if question_by_id[record.question.question_id] != record.question:
            raise CandidatePilotError("assessment question identity differs from registered question")
        if candidate_by_id[record.candidate_id].candidate_identity_hash != record.candidate_identity_hash:
            raise CandidatePilotError("assessment candidate identity differs from registered source row")
        key = record.key
        previous = prior_assessments.get(key)
        expected_previous_id = None if previous is None else previous.assessment_id
        if record.previous_assessment_id != expected_previous_id:
            raise CandidatePilotError("assessment revision chain does not reference the immediately previous record")
        earliest_key = ledger.universe.decision_key if previous is None else previous.as_of_key
        if record.as_of_key.timeline_id != ledger.universe.timeline_id or record.as_of_key < earliest_key:
            raise CandidatePilotError("assessment key precedes its candidate/question history")
        if not set(record.evidence_reference_ids).issubset(evidence_by_id):
            raise CandidatePilotError("assessment cites evidence not registered in the append-only evidence history")
        for reference_id in record.evidence_reference_ids:
            if evidence_by_id[reference_id].candidate_id != record.candidate_id:
                raise CandidatePilotError("assessment cites another candidate's evidence")
            if evidence_by_id[reference_id].available_at > record.as_of_key:
                raise CandidatePilotError("assessment cites evidence not yet available at its as-of key")
        if record.new_evidence_reference_ids:
            batch = batch_by_id.get(record.evidence_batch_id or "")
            if batch is None:
                raise CandidatePilotError("assessment references a missing new-evidence batch")
            if (
                batch.candidate_id != record.candidate_id
                or batch.as_of_key != record.as_of_key
                or batch.start_key != earliest_key
                or tuple(ref.reference_id for ref in batch.evidence) != record.new_evidence_reference_ids
            ):
                raise CandidatePilotError("assessment does not match its newly available evidence batch")
            if not set(record.new_evidence_reference_ids).issubset(record.evidence_reference_ids):
                raise CandidatePilotError("assessment omits newly retrieved factual evidence")
            classified_new = (
                set(record.supporting_reference_ids)
                | set(record.conflicting_reference_ids)
                | set(record.unknown_reference_ids)
            )
            if not set(record.new_evidence_reference_ids).issubset(classified_new):
                raise CandidatePilotError("every new factual reference must be marked support, conflict, or unknown")
            for reference_id in record.new_evidence_reference_ids:
                ref = evidence_by_id[reference_id]
                if ref.evidence_kind != FVG_EVENT_EVIDENCE_KIND or not earliest_key < ref.available_at:
                    raise CandidatePilotError("revision contains non-new or non-lifecycle evidence")
        elif record.evidence_batch_id is not None:
            raise CandidatePilotError("empty revision evidence must not name a batch")
        if record.as_of_key > earliest_key and not record.new_evidence_reference_ids:
            raise CandidatePilotError("later assessment/revision requires newly available factual evidence")
        prior_assessments[key] = record

    coverage_latest: dict[tuple[str, str], CandidateCoverageRecord] = {}
    coverage_ids: set[str] = set()
    initial_pairs: set[tuple[str, str]] = set()
    for record in ledger.coverage_history:
        if record.coverage_id in coverage_ids:
            raise CandidatePilotError("duplicate coverage identity")
        coverage_ids.add(record.coverage_id)
        pair = (record.candidate_id, record.question_id)
        if record.candidate_id not in candidate_by_id or record.question_id not in question_by_id:
            raise CandidatePilotError("coverage references an unregistered candidate/question")
        previous = coverage_latest.get(pair)
        if previous is None:
            if record.state is not CandidateCoverageState.REGISTERED or record.previous_coverage_id is not None:
                raise CandidatePilotError("each candidate/question coverage history must start REGISTERED")
            if record.as_of_key != ledger.universe.decision_key:
                raise CandidatePilotError("initial registration coverage must use the universe decision key")
            initial_pairs.add(pair)
        else:
            if record.previous_coverage_id != previous.coverage_id:
                raise CandidatePilotError("coverage history is not append-only-linked")
            if record.as_of_key.timeline_id != ledger.universe.timeline_id or record.as_of_key < previous.as_of_key:
                raise CandidatePilotError("coverage key precedes its registered history")
        if record.state is CandidateCoverageState.ASSESSED and record.assessment_id not in assessment_ids:
            raise CandidatePilotError("ASSESSED coverage references a missing assessment")
        if record.restoration_is_not_utility_evidence and (
            previous is None or previous.state is not CandidateCoverageState.DEFERRED
        ):
            raise CandidatePilotError("investigation restoration must follow an explicit DEFERRED state")
        coverage_latest[pair] = record
    expected_pairs = {
        (candidate.candidate_id, question.question_id)
        for candidate in ledger.universe.candidates
        for question in ledger.questions
    }
    if initial_pairs != expected_pairs:
        raise CandidatePilotError("registration coverage does not reconcile with every eligible candidate/question")
    if set(coverage_latest) != expected_pairs:
        raise CandidatePilotError("current coverage does not reconcile with the eligible universe")
    for pair, record in coverage_latest.items():
        if record.state is CandidateCoverageState.ASSESSED and record.assessment_id not in {
            item.assessment_id for item in ledger.assessments if item.key == pair
        }:
            raise CandidatePilotError("current ASSESSED coverage does not reference this candidate/question")


def initialize_candidate_research_ledger(
    *, universe: CandidateUniverse, questions: Iterable[ResearchQuestion]
) -> CandidateResearchLedger:
    """Register every visible candidate for each declared question explicitly."""
    question_tuple = tuple(questions)
    if not question_tuple or any(not isinstance(item, ResearchQuestion) for item in question_tuple):
        raise CandidatePilotError("at least one declared research question is required")
    evidence: list[FactualEvidenceReference] = []
    for candidate in universe.candidates:
        evidence.extend(candidate.evidence_references)
    if len({item.reference_id for item in evidence}) != len(evidence):
        raise CandidatePilotError("initial source context contains duplicate evidence identities")
    coverage = tuple(
        _make_coverage(
            candidate_id=candidate.candidate_id,
            question_id=question.question_id,
            state=CandidateCoverageState.REGISTERED,
            as_of_key=universe.decision_key,
            reason="Registered from the complete decision-visible FVG universe; not yet assessed.",
            assessment_id=None,
            previous_coverage_id=None,
        )
        for question in question_tuple
        for candidate in universe.candidates
    )
    return CandidateResearchLedger(
        universe=universe,
        questions=question_tuple,
        assessments=(),
        coverage_history=coverage,
        factual_evidence=tuple(evidence),
        evidence_batches=(),
    )


def reconcile_candidate_coverage(
    *, ledger: CandidateResearchLedger, question_id: str
) -> CoverageReconciliation:
    if question_id not in {item.question_id for item in ledger.questions}:
        raise CandidatePilotError("coverage reconciliation question is not registered")
    expected = ledger.universe.eligible_candidate_ids
    latest = {
        record.candidate_id: record
        for record in ledger.coverage_history
        if record.question_id == question_id
        and ledger.latest_coverage(record.candidate_id, question_id).coverage_id == record.coverage_id
    }
    accounted = tuple(candidate_id for candidate_id in expected if candidate_id in latest)
    missing = tuple(candidate_id for candidate_id in expected if candidate_id not in latest)
    extras = tuple(candidate_id for candidate_id in latest if candidate_id not in set(expected))
    counts = tuple(
        (state.value, sum(record.state is state for record in latest.values()))
        for state in CandidateCoverageState
    )
    return CoverageReconciliation(question_id, expected, accounted, missing, extras, counts)


def record_candidate_coverage(
    *,
    ledger: CandidateResearchLedger,
    candidate_id: str,
    question_id: str,
    state: CandidateCoverageState,
    as_of_key: InformationKey,
    reason: str,
) -> CandidateResearchLedger:
    if state not in (
        CandidateCoverageState.DEFERRED,
        CandidateCoverageState.UNRESOLVED,
        CandidateCoverageState.NOT_EVALUATED,
    ):
        raise CandidatePilotError("use assessment append or restoration APIs for ASSESSED/REGISTERED states")
    ledger.universe.candidate(candidate_id)
    if question_id not in {item.question_id for item in ledger.questions}:
        raise CandidatePilotError("coverage question is not registered")
    latest = ledger.latest_coverage(candidate_id, question_id)
    if latest.state is CandidateCoverageState.DEFERRED:
        raise CandidatePilotError("deferred candidate must be explicitly restored before further coverage changes")
    if as_of_key.timeline_id != ledger.universe.timeline_id or as_of_key < latest.as_of_key:
        raise CandidatePilotError("coverage key precedes registered coverage history")
    record = _make_coverage(
        candidate_id=candidate_id,
        question_id=question_id,
        state=state,
        as_of_key=as_of_key,
        reason=reason,
        assessment_id=None,
        previous_coverage_id=latest.coverage_id,
    )
    return dataclass_replace(ledger, coverage_history=ledger.coverage_history + (record,))


def restore_deferred_candidate(
    *,
    ledger: CandidateResearchLedger,
    candidate_id: str,
    question_id: str,
    as_of_key: InformationKey,
    reason: str,
) -> CandidateResearchLedger:
    """Restore only for investigation; this action is explicitly not utility evidence."""
    latest = ledger.latest_coverage(candidate_id, question_id)
    if latest.state is not CandidateCoverageState.DEFERRED:
        raise CandidatePilotError("only an explicitly DEFERRED candidate can be restored")
    if as_of_key.timeline_id != ledger.universe.timeline_id or as_of_key < latest.as_of_key:
        raise CandidatePilotError("restoration key precedes deferred coverage")
    _require_text(reason, "restoration reason")
    restored = _make_coverage(
        candidate_id=candidate_id,
        question_id=question_id,
        state=CandidateCoverageState.REGISTERED,
        as_of_key=as_of_key,
        reason=f"Restored for investigation only; not evidence of trading utility. {reason}",
        assessment_id=None,
        previous_coverage_id=latest.coverage_id,
        restoration_is_not_utility_evidence=True,
    )
    return dataclass_replace(ledger, coverage_history=ledger.coverage_history + (restored,))


def _coverage_state_for_assessment(status: ProvisionalStatus) -> CandidateCoverageState:
    if status is ProvisionalStatus.DEFERRED:
        return CandidateCoverageState.DEFERRED
    if status in (ProvisionalStatus.UNRESOLVED, ProvisionalStatus.UNKNOWN):
        return CandidateCoverageState.UNRESOLVED
    return CandidateCoverageState.ASSESSED


def append_candidate_assessment(
    *,
    ledger: CandidateResearchLedger,
    candidate_id: str,
    question_id: str,
    category: AssessmentCategory,
    protocol: AssessmentProtocolIdentity,
    as_of_key: InformationKey,
    evidence_reference_ids: Iterable[str],
    supporting_reference_ids: Iterable[str] = (),
    conflicting_reference_ids: Iterable[str] = (),
    unknown_reference_ids: Iterable[str] = (),
    provisional_status: ProvisionalStatus = ProvisionalStatus.PROVISIONAL,
    reason: str,
    declaration_reference: str | None = None,
) -> CandidateResearchLedger:
    """Append an assessment without accepting caller-authored factual batches.

    Later-key factual revisions must use :func:`revise_candidate_assessment`,
    which retrieves new rows from the verified FVG source itself.
    """
    return _append_candidate_assessment_record(
        ledger=ledger,
        candidate_id=candidate_id,
        question_id=question_id,
        category=category,
        protocol=protocol,
        as_of_key=as_of_key,
        evidence_reference_ids=evidence_reference_ids,
        supporting_reference_ids=supporting_reference_ids,
        conflicting_reference_ids=conflicting_reference_ids,
        unknown_reference_ids=unknown_reference_ids,
        provisional_status=provisional_status,
        reason=reason,
        declaration_reference=declaration_reference,
        evidence_batch=None,
    )


def _append_candidate_assessment_record(
    *,
    ledger: CandidateResearchLedger,
    candidate_id: str,
    question_id: str,
    category: AssessmentCategory,
    protocol: AssessmentProtocolIdentity,
    as_of_key: InformationKey,
    evidence_reference_ids: Iterable[str],
    supporting_reference_ids: Iterable[str] = (),
    conflicting_reference_ids: Iterable[str] = (),
    unknown_reference_ids: Iterable[str] = (),
    provisional_status: ProvisionalStatus = ProvisionalStatus.PROVISIONAL,
    reason: str,
    declaration_reference: str | None = None,
    evidence_batch: EvidenceBatch | None = None,
) -> CandidateResearchLedger:
    """Internal ledger append used after public-input validation/retrieval.

    A later-key record must cite a nonempty batch of newly available FVG
    lifecycle rows. Public assessment APIs do not accept this batch from callers.
    """
    candidate = ledger.universe.candidate(candidate_id)
    question_matches = [item for item in ledger.questions if item.question_id == question_id]
    if len(question_matches) != 1:
        raise CandidatePilotError("assessment question is not registered")
    if category is AssessmentCategory.EMPIRICALLY_VALIDATED_RELEVANCE:
        raise CandidatePilotError("this pilot cannot generate empirically validated relevance")
    if not isinstance(category, AssessmentCategory) or not isinstance(provisional_status, ProvisionalStatus):
        raise CandidatePilotError("assessment category/status is invalid")
    if not isinstance(protocol, AssessmentProtocolIdentity):
        raise CandidatePilotError("assessment protocol identity is required")
    if as_of_key.timeline_id != ledger.universe.timeline_id or as_of_key < ledger.universe.decision_key:
        raise CandidatePilotError("assessment key precedes its registered candidate universe")
    coverage = ledger.latest_coverage(candidate_id, question_id)
    if coverage.state is CandidateCoverageState.DEFERRED:
        raise CandidatePilotError("restore a deferred candidate before appending another assessment")
    previous = ledger.latest_assessment(candidate_id, question_id)
    previous_id = None if previous is None else previous.assessment_id
    comparison_key = ledger.universe.decision_key if previous is None else previous.as_of_key
    if as_of_key < comparison_key:
        raise CandidatePilotError("assessment key precedes the prior question-specific assessment")

    supplied_batch = evidence_batch
    new_refs: tuple[FactualEvidenceReference, ...] = ()
    if as_of_key > comparison_key:
        if supplied_batch is None:
            raise CandidatePilotError("later-key assessment requires a newly retrieved factual evidence batch")
        if (
            supplied_batch.case_id != ledger.universe.case_id
            or supplied_batch.candidate_id != candidate_id
            or supplied_batch.source_binding_hash != ledger.universe.source_binding_hash
            or supplied_batch.start_key != comparison_key
            or supplied_batch.as_of_key != as_of_key
            or not supplied_batch.evidence
        ):
            raise CandidatePilotError("later-key assessment batch is empty or mismatched")
        new_refs = supplied_batch.evidence
    elif supplied_batch is not None:
        raise CandidatePilotError("a same-key assessment cannot claim a later-evidence batch")

    prior_evidence = {item.reference_id: item for item in ledger.factual_evidence}
    batch_ids = {item.batch_id for item in ledger.evidence_batches}
    if supplied_batch is not None:
        if supplied_batch.batch_id in batch_ids:
            raise CandidatePilotError("evidence batch has already been appended")
        if any(item.reference_id in prior_evidence for item in supplied_batch.evidence):
            raise CandidatePilotError("new evidence was already present in the append-only ledger")
    new_evidence_history = ledger.factual_evidence + tuple(new_refs)
    new_batch_history = ledger.evidence_batches + (() if supplied_batch is None else (supplied_batch,))
    evidence_ids = tuple(evidence_reference_ids)
    supporting = tuple(supporting_reference_ids)
    conflicting = tuple(conflicting_reference_ids)
    unknown = tuple(unknown_reference_ids)
    if not set(item.reference_id for item in new_refs).issubset(set(evidence_ids)):
        raise CandidatePilotError("assessment must cite every newly retrieved factual reference")
    assessment = _make_assessment(
        candidate_id=candidate_id,
        candidate_identity_hash=candidate.candidate_identity_hash,
        question=question_matches[0],
        category=category,
        protocol=protocol,
        as_of_key=as_of_key,
        evidence_reference_ids=evidence_ids,
        supporting_reference_ids=supporting,
        conflicting_reference_ids=conflicting,
        unknown_reference_ids=unknown,
        provisional_status=provisional_status,
        reason=reason,
        declaration_reference=declaration_reference,
        previous_assessment_id=previous_id,
        new_evidence_reference_ids=tuple(item.reference_id for item in new_refs),
        evidence_batch_id=None if supplied_batch is None else supplied_batch.batch_id,
    )
    assessments = ledger.assessments + (assessment,)
    state = _coverage_state_for_assessment(provisional_status)
    coverage_record = _make_coverage(
        candidate_id=candidate_id,
        question_id=question_id,
        state=state,
        as_of_key=as_of_key,
        reason=f"Assessment {assessment.assessment_id} appended as {provisional_status.value}.",
        assessment_id=assessment.assessment_id if state is CandidateCoverageState.ASSESSED else None,
        previous_coverage_id=coverage.coverage_id,
    )
    return CandidateResearchLedger(
        universe=ledger.universe,
        questions=ledger.questions,
        assessments=assessments,
        coverage_history=ledger.coverage_history + (coverage_record,),
        factual_evidence=new_evidence_history,
        evidence_batches=new_batch_history,
    )


def revise_candidate_assessment(
    *,
    ledger: CandidateResearchLedger,
    candidate_id: str,
    question_id: str,
    category: AssessmentCategory,
    protocol: AssessmentProtocolIdentity,
    as_of_key: InformationKey,
    timeline: MarketObservationTimeline,
    adapter: TimelineAdapter,
    market_history: pd.DataFrame,
    fvg_surface: s4b2.Stage4B2FVGSurface,
    supporting_reference_ids: Iterable[str] = (),
    conflicting_reference_ids: Iterable[str] = (),
    unknown_reference_ids: Iterable[str] = (),
    provisional_status: ProvisionalStatus = ProvisionalStatus.PROVISIONAL,
    reason: str,
    declaration_reference: str | None = None,
) -> CandidateResearchLedger:
    """Retrieve verified new FVG facts internally and append a later revision.

    Callers supply the new as-of boundary and source inputs, never an
    ``EvidenceBatch`` or factual rows. Retrieval is bound to the registered
    source, candidate, and previous assessment boundary; no eligible rows is a
    fail-closed no-revision result. Earlier records are never edited.
    """
    previous = ledger.latest_assessment(candidate_id, question_id)
    if previous is None:
        raise CandidatePilotError("revision requires an earlier question-specific assessment")
    if not isinstance(as_of_key, InformationKey) or as_of_key.timeline_id != ledger.universe.timeline_id:
        raise CandidatePilotError("revision as-of key must belong to the registered timeline")
    if not previous.as_of_key < as_of_key:
        raise CandidatePilotError("revision as-of key must advance beyond the prior assessment")

    batch = retrieve_new_fvg_factual_evidence(
        universe=ledger.universe,
        candidate_id=candidate_id,
        timeline=timeline,
        adapter=adapter,
        market_history=market_history,
        fvg_surface=fvg_surface,
        start_key=previous.as_of_key,
        as_of_key=as_of_key,
    )
    if not batch.evidence:
        raise CandidatePilotError("no eligible new FVG factual evidence; revision was not appended")

    new_ids = tuple(item.reference_id for item in batch.evidence)
    evidence_ids = tuple(dict.fromkeys((*previous.evidence_reference_ids, *new_ids)))
    supporting = tuple(supporting_reference_ids)
    conflicting = tuple(conflicting_reference_ids)
    unknown = tuple(unknown_reference_ids)
    classified = set(supporting) | set(conflicting) | set(unknown)
    # Unclassified newly retrieved facts remain explicitly unknown; their
    # arrival never implies support, conflict, or an outcome.
    unknown = tuple(dict.fromkeys((*unknown, *(item for item in new_ids if item not in classified))))
    return _append_candidate_assessment_record(
        ledger=ledger,
        candidate_id=candidate_id,
        question_id=question_id,
        category=category,
        protocol=protocol,
        as_of_key=as_of_key,
        evidence_reference_ids=evidence_ids,
        supporting_reference_ids=supporting,
        conflicting_reference_ids=conflicting,
        unknown_reference_ids=unknown,
        provisional_status=provisional_status,
        reason=reason,
        declaration_reference=declaration_reference,
        evidence_batch=batch,
    )


def _require_text(value: object, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise CandidatePilotError(f"{field_name} must be nonempty text")


def _require_hash(value: object, field_name: str) -> None:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise CandidatePilotError(f"{field_name} must be lowercase SHA-256 hex")


def _is_hash(value: object) -> bool:
    return isinstance(value, str) and _SHA256_RE.fullmatch(value) is not None


__all__ = [
    "PILOT_CONTRACT_VERSION",
    "FVG_ELIGIBILITY_POLICY_ID",
    "UNSAFE_BLOCKER_DECLARATIONS",
    "CandidatePilotError",
    "AssessmentCategory",
    "ProvisionalStatus",
    "CandidateCoverageState",
    "ResearchQuestion",
    "AssessmentProtocolIdentity",
    "ProducerPolicyIdentity",
    "SourceArtifactProvenance",
    "FactualEvidenceReference",
    "CandidateContext",
    "CandidateUniverse",
    "EvidenceBatch",
    "CandidateAssessmentRecord",
    "CandidateCoverageRecord",
    "CoverageReconciliation",
    "CandidateResearchLedger",
    "build_fvg_candidate_universe",
    "initialize_candidate_research_ledger",
    "retrieve_new_fvg_factual_evidence",
    "append_candidate_assessment",
    "revise_candidate_assessment",
    "record_candidate_coverage",
    "restore_deferred_candidate",
    "reconcile_candidate_coverage",
]
