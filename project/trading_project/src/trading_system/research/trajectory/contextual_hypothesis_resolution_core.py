"""Contextual Hypothesis Resolution Core V1.

A contract-driven, append-only mechanism layered over
``causal_market_context_core``. This module contains no market narrative
catalogue or default hypothesis generator. An authorized caller-supplied
policy must generate hypotheses; a caller-supplied discriminator contract
must define observations and outcomes. Every resolution is explicitly
mechanical and contract-relative, never market truth or empirical proof.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from itertools import combinations
import math
from typing import Any, Protocol

import numpy as np
import pandas as pd

from trading_system.market_understanding.contracts import SchemaIdentity
from trading_system.market_understanding.records import (
    AppendOnlyEventLedger,
    EventKind,
    EventRecord,
    PublishedRecord,
    freeze_payload,
)
from trading_system.research.hashing import canonical_sha256
from trading_system.research.information_time import InformationKey, InformationPhase
from trading_system.research.trajectory.causal_market_context_core import (
    CORE_ID as CAUSAL_CORE_ID,
    CORE_SCHEMA_VERSION as CAUSAL_CORE_SCHEMA_VERSION,
    LEGAL_ASOF_PHASES,
    CausalMarketContextCoreError,
    CoreEntity,
    EntityRevision,
    ProducerEvent,
    Relation,
    ReplayMemoryResult,
)

CORE_ID = "CONTEXTUAL_HYPOTHESIS_RESOLUTION_CORE_V1"
CORE_SCHEMA_VERSION = "CONTEXTUAL_HYPOTHESIS_RESOLUTION_RECORDS_V1"
SUPPORTED_RESOLUTION_RULE = "UNIQUE_SUPPORTED_AGAINST_EACH_DECLARED_ALTERNATIVE_V1"
HYPOTHESIS_SCHEMA = SchemaIdentity("CONTEXTUAL_HYPOTHESIS", CORE_SCHEMA_VERSION)
HYPOTHESIS_SET_SCHEMA = SchemaIdentity("CONTEXTUAL_HYPOTHESIS_SET", CORE_SCHEMA_VERSION)
PAIR_ASSESSMENT_SCHEMA = SchemaIdentity("CONTEXTUAL_HYPOTHESIS_PAIR_ASSESSMENT", CORE_SCHEMA_VERSION)
ANALYSIS_CYCLE_SCHEMA = SchemaIdentity("CONTEXTUAL_HYPOTHESIS_ANALYSIS_CYCLE", CORE_SCHEMA_VERSION)


class HypothesisResolutionError(ValueError):
    """Invalid policy, context, discriminator, or append-only assessment."""


class AuthorizationScope(str, Enum):
    OPERATIONAL_INTERPRETATION = "OPERATIONAL_INTERPRETATION"
    SOFTWARE_TEST_ONLY = "SOFTWARE_TEST_ONLY"


class AnalysisMode(str, Enum):
    OPERATIONAL = "OPERATIONAL"
    SOFTWARE_TEST_ONLY = "SOFTWARE_TEST_ONLY"


class TerminationStatus(str, Enum):
    RESOLVED_UNDER_DECLARED_POLICY = "RESOLVED_UNDER_DECLARED_POLICY"
    UNRESOLVED_WAITING_FOR_SPECIFIC_EVIDENCE = "UNRESOLVED_WAITING_FOR_SPECIFIC_EVIDENCE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    INVALID_FOUNDATION = "INVALID_FOUNDATION"
    NO_AUTHORIZED_HYPOTHESES = "NO_AUTHORIZED_HYPOTHESES"
    INCOMPLETE_COVERAGE = "INCOMPLETE_COVERAGE"


class HypothesisDisposition(str, Enum):
    SUPPORTED_BY_DECLARED_EVIDENCE = "SUPPORTED_BY_DECLARED_EVIDENCE"
    CONTRADICTED_BY_DECLARED_EVIDENCE = "CONTRADICTED_BY_DECLARED_EVIDENCE"
    REMAINS_UNRESOLVED = "REMAINS_UNRESOLVED"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"
    INVALIDATED_BY_FOUNDATION_CHANGE = "INVALIDATED_BY_FOUNDATION_CHANGE"
    DISCRIMINATOR_NOT_ESTABLISHED = "DISCRIMINATOR_NOT_ESTABLISHED"


class ReassessmentCause(str, Enum):
    INITIAL_ANALYSIS = "INITIAL_ANALYSIS"
    EVIDENCE_ARRIVED = "EVIDENCE_ARRIVED"
    NO_NEW_RELEVANT_EVIDENCE = "NO_NEW_RELEVANT_EVIDENCE"
    INTERPRETATION_POLICY_CHANGE = "INTERPRETATION_POLICY_CHANGE"
    DISCRIMINATOR_POLICY_CHANGE = "DISCRIMINATOR_POLICY_CHANGE"
    REPRESENTATION_POLICY_CHANGE = "REPRESENTATION_POLICY_CHANGE"
    CORRECTED_INPUT = "CORRECTED_INPUT"
    CORE_CONTRACT_CHANGE = "CORE_CONTRACT_CHANGE"
    RESOURCE_LIMIT_INCOMPLETE = "RESOURCE_LIMIT_INCOMPLETE"


@dataclass(frozen=True)
class ResolutionLimits:
    """Resource budgets; crossing a budget rejects or marks coverage partial.

    These are operational resource ceilings, not hypothesis-count semantics.
    No hypothesis or competing pair is silently dropped.
    """

    max_visible_evidence_records: int = 100_000
    max_policy_outputs: int = 10_000
    max_discriminator_contracts: int = 50_000
    max_pair_evaluations: int = 50_000
    max_discriminator_evidence_checks: int = 1_000_000

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise HypothesisResolutionError(f"{name} must be a nonnegative integer")
        if any(getattr(self, name) == 0 for name in self.__dataclass_fields__):
            raise HypothesisResolutionError("resolution resource budgets must be positive")


@dataclass(frozen=True)
class RepresentationPolicyIdentity:
    representation_id: str
    state: str
    policy_id: str | None
    policy_version: str | None
    policy_sha256: str | None
    surface_ids: tuple[str, ...]

    def payload(self) -> dict[str, Any]:
        return {
            "representation_id": self.representation_id,
            "state": self.state,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "policy_sha256": self.policy_sha256,
            "surface_ids": list(self.surface_ids),
        }


@dataclass(frozen=True)
class PolicyRepresentationIdentity:
    """Representation identity visible to a policy; full-run surface hashes stay private."""

    representation_id: str
    state: str
    policy_id: str | None
    policy_version: str | None
    policy_sha256: str | None


@dataclass(frozen=True)
class ContextEvidence:
    """One core-produced immutable/as-of evidence reference."""

    evidence_id: str
    record_type: str
    information_key: InformationKey
    schema_identity: Mapping[str, Any]
    payload: Mapping[str, Any]
    source_identity_sha256: str
    representation_id: str | None
    representation_policy_sha256: str | None
    dependency_record_ids: tuple[str, ...]
    payload_sha256: str

    def payload_record(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "record_type": self.record_type,
            "information_key": _key_payload(self.information_key),
            "schema_identity": _plain(self.schema_identity),
            "payload": _plain(self.payload),
            "source_identity_sha256": self.source_identity_sha256,
            "representation_id": self.representation_id,
            "representation_policy_sha256": self.representation_policy_sha256,
            "dependency_record_ids": list(self.dependency_record_ids),
            "payload_sha256": self.payload_sha256,
        }


_CONTEXT_SEAL = object()


@dataclass(frozen=True, init=False)
class VerifiedAsOfContext:
    """Verified prefix of a ``ReplayMemoryResult``; no later rows are exposed."""

    as_of_key: InformationKey
    snapshot_id: str
    core_run_id: str
    core_id: str
    core_schema_version: str
    source_identity: Mapping[str, Any]
    source_identity_sha256: str
    source_file_sha256: str
    source_validation_state: str
    source_semantics: str
    timeline_id: str
    prefix_chain_sha256: str
    prefix_chain_by_position: tuple[tuple[int, str], ...]
    producer_contracts: Mapping[str, Any]
    representation_policies: tuple[RepresentationPolicyIdentity, ...]
    domain_availability: Mapping[str, Any]
    relationship_coverage: Mapping[str, Any]
    evidence: tuple[ContextEvidence, ...]
    _verification_seal: object = field(repr=False, compare=False)

    def __init__(self, *, _seal: object, **values: Any) -> None:
        if _seal is not _CONTEXT_SEAL:
            raise HypothesisResolutionError("VerifiedAsOfContext must be built from verified causal-core output")
        for name, value in values.items():
            object.__setattr__(self, name, value)
        object.__setattr__(self, "_verification_seal", _seal)

    def prefix_at(self, position: int) -> str | None:
        for index, digest in self.prefix_chain_by_position:
            if index == position:
                return digest
        return None

    @property
    def evidence_by_id(self) -> Mapping[str, ContextEvidence]:
        return {item.evidence_id: item for item in self.evidence}

    def provenance_payload(self) -> dict[str, Any]:
        return {
            "core_run_id": self.core_run_id,
            "core_id": self.core_id,
            "core_schema_version": self.core_schema_version,
            "source_identity": _plain(self.source_identity),
            "source_identity_sha256": self.source_identity_sha256,
            "source_file_sha256": self.source_file_sha256,
            "source_validation_state": self.source_validation_state,
            "source_semantics": self.source_semantics,
            "timeline_id": self.timeline_id,
            "as_of_key": _key_payload(self.as_of_key),
            "prefix_chain_sha256": self.prefix_chain_sha256,
            "relationship_coverage_at_key": _plain(self.relationship_coverage),
            "relationship_coverage_row_used_as_hypothesis_feature": False,
            "representation_policies": [item.payload() for item in self.representation_policies],
            "representation_surface_ids_are_full_run_provenance_only": True,
            "source_origin_authenticated": False,
        }


@dataclass(frozen=True)
class PolicyInput:
    """As-of view with artifact-source metadata withheld from policy features."""

    as_of_key: InformationKey
    context_snapshot_id: str
    source_identity_reference: str
    evidence: tuple[ContextEvidence, ...]
    domain_availability: Mapping[str, Any]
    representation_policies: tuple[PolicyRepresentationIdentity, ...]

    @property
    def evidence_by_id(self) -> Mapping[str, ContextEvidence]:
        return {item.evidence_id: item for item in self.evidence}


@dataclass(frozen=True)
class PolicyIdentity:
    policy_id: str
    policy_version: str
    policy_sha256: str
    implementation_sha256: str
    authorization_reference: str
    authorization_scope: AuthorizationScope
    authorization_status: str
    resolution_rule_id: str
    resolution_rule_sha256: str

    def __post_init__(self) -> None:
        for name in (
            "policy_id",
            "policy_version",
            "authorization_reference",
            "authorization_status",
            "resolution_rule_id",
        ):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise HypothesisResolutionError(f"policy {name} must be a nonempty string")
        for name in ("policy_sha256", "implementation_sha256", "resolution_rule_sha256"):
            _require_hash(getattr(self, name), name)
        if not isinstance(self.authorization_scope, AuthorizationScope):
            raise HypothesisResolutionError("explicit policy authorization scope required")

    def payload(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "policy_sha256": self.policy_sha256,
            "implementation_sha256": self.implementation_sha256,
            "authorization_reference": self.authorization_reference,
            "authorization_scope": self.authorization_scope.value,
            "authorization_status": self.authorization_status,
            "resolution_rule_id": self.resolution_rule_id,
            "resolution_rule_sha256": self.resolution_rule_sha256,
            "authorization_is_caller_asserted_not_authenticated": True,
        }

    @property
    def identity_sha256(self) -> str:
        return _digest("CONTEXTUAL_HYPOTHESIS_POLICY_IDENTITY_V1", self.payload())


class HypothesisProducer(Protocol):
    def generate(self, context: PolicyInput) -> Iterable["HypothesisDraft"]: ...


@dataclass(frozen=True)
class AuthorizedHypothesisPolicy:
    identity: PolicyIdentity
    producer: HypothesisProducer = field(compare=False, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.identity, PolicyIdentity):
            raise HypothesisResolutionError("PolicyIdentity required")
        if not callable(getattr(self.producer, "generate", None)):
            raise HypothesisResolutionError("policy producer must expose generate(context)")


@dataclass(frozen=True)
class HypothesisDraft:
    hypothesis_id: str
    alternative_group_id: str
    statement: str
    evidence_ids: tuple[str, ...]
    dependency_record_ids: tuple[str, ...]
    assumptions: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("hypothesis_id", "alternative_group_id", "statement"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise HypothesisResolutionError(f"hypothesis {name} must be nonempty")
        for name in ("evidence_ids", "dependency_record_ids"):
            values = getattr(self, name)
            if not isinstance(values, tuple) or any(not isinstance(x, str) or not x.strip() for x in values):
                raise HypothesisResolutionError(f"{name} must be a tuple of nonempty record identities")
            if len(set(values)) != len(values):
                raise HypothesisResolutionError(f"{name} must not contain duplicate identities")
        if not self.evidence_ids:
            raise HypothesisResolutionError("hypothesis must cite at least one visible evidence record")
        if not set(self.evidence_ids).issubset(set(self.dependency_record_ids)):
            raise HypothesisResolutionError("hypothesis evidence must be included in its dependency identities")
        if not isinstance(self.assumptions, tuple) or any(not isinstance(x, str) or not x.strip() for x in self.assumptions):
            raise HypothesisResolutionError("assumptions must be a tuple of explicit nonempty strings")


@dataclass(frozen=True)
class ExactValueDiscriminatorContract:
    """Declared exact-value discriminator; no operator or outcome is inferred.

    The contract supplies the observed record type/path, two competing
    hypothesis identities and their expected scalar values. ``closed_world``
    explicitly controls whether a match for one alternative contradicts the
    other. Only ``FIRST_MATCHING_INFORMATION_BATCH`` is implemented; any
    different selection semantics require a different registered evaluator.
    """

    contract_id: str
    contract_version: str
    policy_sha256: str
    authorization_reference: str
    alternative_group_id: str
    hypothesis_ids: tuple[str, str]
    evidence_record_type: str
    field_path: tuple[str, ...]
    expected_values_by_hypothesis: tuple[tuple[str, Any], tuple[str, Any]]
    require_evidence_after_generation: bool
    closed_world: bool
    selection_rule_id: str
    contract_sha256: str = ""

    def __post_init__(self) -> None:
        for name in (
            "contract_id",
            "contract_version",
            "authorization_reference",
            "alternative_group_id",
            "evidence_record_type",
            "selection_rule_id",
        ):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise HypothesisResolutionError(f"discriminator {name} must be nonempty")
        _require_hash(self.policy_sha256, "discriminator policy_sha256")
        if not isinstance(self.hypothesis_ids, tuple) or len(self.hypothesis_ids) != 2:
            raise HypothesisResolutionError("an exact-value discriminator must declare one competing pair")
        if len(set(self.hypothesis_ids)) != 2 or any(not isinstance(x, str) or not x for x in self.hypothesis_ids):
            raise HypothesisResolutionError("discriminator hypothesis ids must be distinct nonempty strings")
        if not isinstance(self.field_path, tuple) or not self.field_path or any(not isinstance(x, str) or not x for x in self.field_path):
            raise HypothesisResolutionError("discriminator field_path must be a nonempty tuple of field names")
        if self.selection_rule_id != "FIRST_MATCHING_INFORMATION_BATCH":
            raise HypothesisResolutionError("unsupported evidence-selection rule; no substitute is inferred")
        if not isinstance(self.require_evidence_after_generation, bool) or not isinstance(self.closed_world, bool):
            raise HypothesisResolutionError("discriminator temporal and closed-world declarations must be boolean")
        pairs = self.expected_values_by_hypothesis
        if not isinstance(pairs, tuple) or len(pairs) != 2:
            raise HypothesisResolutionError("two expected values, one per competing hypothesis, are required")
        ids = tuple(item[0] for item in pairs)
        if set(ids) != set(self.hypothesis_ids) or len(set(ids)) != 2:
            raise HypothesisResolutionError("expected values must bind exactly the declared hypotheses")
        values = [item[1] for item in pairs]
        normalized_values = [_plain(value) for value in values]
        if any(value is not None and not isinstance(value, (str, bool, int, float)) for value in normalized_values):
            raise HypothesisResolutionError("exact-value discriminator outcomes must be scalar values")
        hashes = [_digest("CONTEXTUAL_HYPOTHESIS_EXPECTED_VALUE_V1", value) for value in normalized_values]
        if hashes[0] == hashes[1]:
            raise HypothesisResolutionError("declared discriminator outcomes must differ to distinguish the pair")
        payload = self._identity_payload()
        expected_hash = _digest("CONTEXTUAL_HYPOTHESIS_DISCRIMINATOR_CONTRACT_V1", payload)
        if self.contract_sha256:
            _require_hash(self.contract_sha256, "discriminator contract hash")
            if self.contract_sha256 != expected_hash:
                raise HypothesisResolutionError("discriminator contract hash does not match its declaration")
        else:
            object.__setattr__(self, "contract_sha256", expected_hash)

    def _identity_payload(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "contract_version": self.contract_version,
            "policy_sha256": self.policy_sha256,
            "authorization_reference": self.authorization_reference,
            "alternative_group_id": self.alternative_group_id,
            "hypothesis_ids": list(self.hypothesis_ids),
            "evidence_record_type": self.evidence_record_type,
            "field_path": list(self.field_path),
            "expected_values_by_hypothesis": [[key, _plain(value)] for key, value in self.expected_values_by_hypothesis],
            "require_evidence_after_generation": self.require_evidence_after_generation,
            "closed_world": self.closed_world,
            "selection_rule_id": self.selection_rule_id,
        }

    def payload(self) -> dict[str, Any]:
        return {**self._identity_payload(), "contract_sha256": self.contract_sha256, "authorization_is_caller_asserted_not_authenticated": True}

    @property
    def pair_key(self) -> tuple[str, str]:
        return tuple(sorted(self.hypothesis_ids))

    @property
    def expected_values(self) -> Mapping[str, Any]:
        return {key: value for key, value in self.expected_values_by_hypothesis}


@dataclass(frozen=True)
class HypothesisRecord:
    hypothesis_id: str
    alternative_group_id: str
    statement: str
    created_key: InformationKey
    alternative_hypothesis_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    dependency_record_ids: tuple[str, ...]
    assumptions: tuple[str, ...]
    policy_identity: Mapping[str, Any]
    context_snapshot_id: str
    source_identity_sha256: str
    source_file_sha256: str
    representation_policy_sha256s: tuple[str, ...]
    record: PublishedRecord

    def payload(self) -> dict[str, Any]:
        return _plain(self.record.content)


@dataclass(frozen=True)
class PairAssessment:
    pair_id: str
    assessment_id: str
    hypothesis_ids: tuple[str, str]
    discriminator_contract_id: str | None
    discriminator_contract_sha256: str | None
    pair_status: str
    dispositions: tuple[tuple[str, str], tuple[str, str]]
    evidence_ids: tuple[str, ...]
    observed_value: Any
    required_evidence: Mapping[str, Any]
    supersedes_assessment_id: str | None
    reassessment_cause: str
    record: PublishedRecord

    def payload(self) -> dict[str, Any]:
        return _plain(self.record.content)


@dataclass(frozen=True)
class AnalysisCycle:
    cycle_id: str
    cycle_ordinal: int
    generation_id: str | None
    context_snapshot_id: str
    as_of_key: InformationKey
    termination_status: TerminationStatus
    hypothesis_generation_state: str
    reassessment_cause: str
    hypothesis_ids: tuple[str, ...]
    pair_assessment_ids: tuple[str, ...]
    affected_pair_ids: tuple[str, ...]
    unaffected_pair_ids: tuple[str, ...]
    total_competing_pairs: int
    evaluated_pair_count: int
    unexamined_pair_count: int
    coverage_state: str
    details: Mapping[str, Any]
    record: PublishedRecord

    def payload(self) -> dict[str, Any]:
        return _plain(self.record.content)


@dataclass(frozen=True)
class ResolutionResult:
    cycle: AnalysisCycle
    hypotheses: tuple[HypothesisRecord, ...]
    pair_assessments: tuple[PairAssessment, ...]
    records_added: tuple[PublishedRecord, ...]
    events_added: tuple[EventRecord, ...]

    def payload(self) -> dict[str, Any]:
        return {
            "core_id": CORE_ID,
            "termination_status": self.cycle.termination_status.value,
            "hypothesis_generation_state": self.cycle.hypothesis_generation_state,
            "reassessment_cause": self.cycle.reassessment_cause,
            "cycle": self.cycle.payload(),
            "hypotheses": [item.payload() for item in self.hypotheses],
            "pair_assessments": [item.payload() for item in self.pair_assessments],
            "records_added": [_plain(item.content) for item in self.records_added],
            "events_added": [_plain(event.event_payload) for event in self.events_added],
            "mechanical_resolution_is_not_market_truth": True,
            "empirical_proof_probability_relevance_score_and_recommendation_emitted": False,
        }


@dataclass(frozen=True)
class HypothesisSetState:
    generation_id: str
    policy: AuthorizedHypothesisPolicy
    contracts: tuple[ExactValueDiscriminatorContract, ...]
    hypotheses: tuple[HypothesisRecord, ...]
    pairs: tuple[tuple[str, str, str, str], ...]
    assessments_by_pair: Mapping[str, PairAssessment]
    created_context: VerifiedAsOfContext
    latest_context: VerifiedAsOfContext
    latest_termination: TerminationStatus
    invalidated: bool = False


class HypothesisResolutionLedger:
    """Append-only S0 record/event adapter; never replaces old assessments."""

    def __init__(self) -> None:
        self._event_ledger = AppendOnlyEventLedger()
        self._records: list[PublishedRecord] = []
        self._events: list[EventRecord] = []
        self._record_ids: set[str] = set()
        self._last_event_identity: str | None = None
        self._last_key: InformationKey | None = None

    @property
    def records(self) -> tuple[PublishedRecord, ...]:
        return tuple(self._records)

    @property
    def events(self) -> tuple[EventRecord, ...]:
        return self._event_ledger.events()

    def append(self, record: PublishedRecord, *, status: str, event_payload: Mapping[str, Any]) -> EventRecord:
        if not isinstance(record, PublishedRecord):
            raise HypothesisResolutionError("only immutable PublishedRecord instances may enter the resolution ledger")
        if record.record_identity in self._record_ids:
            raise HypothesisResolutionError("duplicate published identity; prior assessments are immutable")
        if not isinstance(status, str) or not status.strip() or not isinstance(event_payload, Mapping):
            raise HypothesisResolutionError("append status and event payload are required")
        if self._last_key is not None:
            if record.timeline_id == self._last_key.timeline_id:
                try:
                    if record.availability_key < self._last_key:
                        raise HypothesisResolutionError("ledger information keys cannot move backwards")
                except Exception as exc:
                    if isinstance(exc, HypothesisResolutionError):
                        raise
                    raise HypothesisResolutionError("incomparable resolution ledger keys") from exc
            elif "FOUNDATION" not in status and "INVALID" not in status:
                raise HypothesisResolutionError("cross-timeline ledger append requires an explicit invalidation event")
        ordinal = len(self._events)
        event_identity = "HREV-" + _digest("CONTEXTUAL_HYPOTHESIS_LEDGER_EVENT_ID_V1", {
            "ordinal": ordinal,
            "previous_event_identity": self._last_event_identity,
            "record_identity": record.record_identity,
            "information_key": record.availability_key,
            "status": status,
            "event_payload": _plain(event_payload),
        })
        payload = {
            "status": status,
            "published_record_identity": record.record_identity,
            "published_record_type": record.record_type,
            "ledger_append_ordinal": ordinal,
            "previous_ledger_event_identity": self._last_event_identity,
            "event_payload": _plain(event_payload),
            "ledger_storage_order_is_not_information_order": True,
        }
        event = EventRecord(
            event_identity=event_identity,
            event_kind=EventKind.STATUS_EVENT,
            subject_record_identity=record.record_identity,
            event_key=record.availability_key,
            event_payload=payload,
        )
        self._event_ledger.append(event)
        self._records.append(record)
        self._events.append(event)
        self._record_ids.add(record.record_identity)
        self._last_event_identity = event_identity
        self._last_key = record.availability_key
        return event

    def status_of(self, record_identity: str) -> str | Any:
        return self._event_ledger.project_status(record_identity)


def _plain(value: Any) -> Any:
    if value is None or value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, InformationKey):
        return _key_payload(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, pd.Timestamp):
        if value.tz is None:
            raise HypothesisResolutionError("naive timestamp in resolution payload")
        return value.tz_convert("UTC").isoformat().replace("+00:00", "Z")
    if isinstance(value, pd.Timedelta):
        return {"nanoseconds": int(value.value)}
    if isinstance(value, np.ndarray):
        return [_plain(item) for item in value.tolist()]
    if isinstance(value, np.generic):
        return _plain(value.item())
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    if isinstance(value, (set, frozenset)):
        raise HypothesisResolutionError("unordered values are forbidden in canonical resolution payloads")
    if isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise HypothesisResolutionError("nonfinite resolution payload value")
        return value
    if hasattr(value, "as_payload") and callable(value.as_payload):
        return _plain(value.as_payload())
    if hasattr(value, "__dataclass_fields__"):
        return {name: _plain(getattr(value, name)) for name in value.__dataclass_fields__ if not name.startswith("_")}
    raise HypothesisResolutionError(f"unsupported resolution payload type: {type(value).__name__}")


def _digest(domain: str, payload: Any) -> str:
    try:
        return canonical_sha256(domain=domain, payload=_plain(payload))
    except Exception as exc:
        raise HypothesisResolutionError(f"canonical hash rejected {domain}: {exc}") from exc


def _require_hash(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise HypothesisResolutionError(f"{label} must be lowercase SHA-256 hex")
    return value


def _key_payload(key: InformationKey) -> dict[str, Any]:
    if not isinstance(key, InformationKey):
        raise HypothesisResolutionError("InformationKey required")
    return {
        "information_key_version": key.information_key_version,
        "timeline_id": key.timeline_id,
        "bar_position": key.bar_position,
        "event_time_utc": None if key.event_time_utc is None else _plain(key.event_time_utc),
        "information_phase": key.information_phase.value,
        "deterministic_sequence": key.deterministic_sequence,
    }


def _parse_key(payload: Mapping[str, Any]) -> InformationKey:
    try:
        timestamp = payload.get("event_time_utc")
        return InformationKey(
            information_key_version=str(payload["information_key_version"]),
            timeline_id=str(payload["timeline_id"]),
            bar_position=int(payload["bar_position"]),
            event_time_utc=None if timestamp is None else pd.Timestamp(timestamp),
            information_phase=InformationPhase(str(payload["information_phase"])),
            deterministic_sequence=int(payload["deterministic_sequence"]),
        )
    except Exception as exc:
        raise HypothesisResolutionError(f"invalid causal-core InformationKey payload: {exc}") from exc


def _core_hash(domain: str, payload: Any) -> str:
    """Match causal-core `_hash`: mappings/lists normalized, typed keys retained."""
    def normalize(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {str(key): normalize(item) for key, item in value.items()}
        if isinstance(value, (tuple, list)):
            return [normalize(item) for item in value]
        if isinstance(value, np.ndarray):
            return [normalize(item) for item in value.tolist()]
        return value
    try:
        return canonical_sha256(domain=domain, payload=normalize(payload))
    except Exception as exc:
        raise HypothesisResolutionError(f"causal-core prefix hash verification failed: {exc}") from exc


def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    try:
        return freeze_payload(_plain(value), field_name="contextual hypothesis immutable record")
    except Exception as exc:
        raise HypothesisResolutionError(f"immutable S0 payload rejected: {exc}") from exc


def _record_evidence(
    *,
    evidence_id: str,
    record_type: str,
    key: InformationKey,
    schema_identity: Mapping[str, Any],
    payload: Mapping[str, Any],
    source_identity_sha256: str,
    representation_id: str | None,
    representation_policy_sha256: str | None,
    dependencies: Sequence[str] = (),
) -> ContextEvidence:
    _require_hash(source_identity_sha256, "source identity hash")
    plain_payload = _plain(payload)
    schema = _plain(schema_identity)
    digest = _digest("CONTEXTUAL_HYPOTHESIS_CONTEXT_EVIDENCE_V1", {
        "evidence_id": evidence_id,
        "record_type": record_type,
        "information_key": key,
        "schema_identity": schema,
        "payload": plain_payload,
        "source_identity_sha256": source_identity_sha256,
        "representation_id": representation_id,
        "representation_policy_sha256": representation_policy_sha256,
        "dependency_record_ids": list(dependencies),
    })
    return ContextEvidence(
        evidence_id=evidence_id,
        record_type=record_type,
        information_key=key,
        schema_identity=_freeze(schema),
        payload=_freeze(plain_payload),
        source_identity_sha256=source_identity_sha256,
        representation_id=representation_id,
        representation_policy_sha256=representation_policy_sha256,
        dependency_record_ids=tuple(dependencies),
        payload_sha256=digest,
    )


def _core_prefix(result: ReplayMemoryResult, final_position: int) -> tuple[tuple[tuple[int, str], ...], tuple[Mapping[str, Any], ...]]:
    provenance = _plain(result.run_provenance)
    if provenance.get("core_id") != CAUSAL_CORE_ID or provenance.get("core_schema_version") != CAUSAL_CORE_SCHEMA_VERSION:
        raise HypothesisResolutionError("context was not produced by the declared causal market context core")
    timeline_id = provenance.get("timeline_id")
    producer_contracts = provenance.get("producer_contracts")
    structural_policies = provenance.get("structural_policies")
    if not isinstance(timeline_id, str) or not isinstance(producer_contracts, Mapping) or not isinstance(structural_policies, (tuple, list)):
        raise HypothesisResolutionError("causal-core run provenance is incomplete")
    policy_hashes: list[str] = []
    for item in structural_policies:
        if not isinstance(item, Mapping):
            raise HypothesisResolutionError("malformed structural policy identity in causal-core provenance")
        policy_hashes.append(_require_hash(item.get("policy_sha256"), "causal structural policy hash"))
    prefix = _core_hash("CORE_ASOF_PREFIX_SEED_V1", {
        "core": CAUSAL_CORE_ID,
        "schema": CAUSAL_CORE_SCHEMA_VERSION,
        "timeline_id": timeline_id,
        "producer_contracts": producer_contracts,
        "policy_hashes": policy_hashes,
    })
    prefixes: list[tuple[int, str]] = []
    visible_boundaries: list[Mapping[str, Any]] = []
    if len(result.boundaries) != result.summary.boundary_count or final_position >= len(result.boundaries):
        raise HypothesisResolutionError("causal-core boundary stream does not cover the requested as-of position")
    for position in range(final_position + 1):
        outer = result.boundaries[position]
        if not isinstance(outer, Mapping):
            raise HypothesisResolutionError("malformed causal-core boundary record")
        key_payload = outer.get("information_key")
        content = _plain(outer.get("content"))
        if not isinstance(key_payload, Mapping) or not isinstance(content, Mapping):
            raise HypothesisResolutionError("boundary key/content is missing")
        key = _parse_key(key_payload)
        if key.timeline_id != timeline_id or key.bar_position != position or key.information_phase is not InformationPhase.COMPLETED_ROW_AVAILABLE:
            raise HypothesisResolutionError("boundary ordering or information-time identity is inconsistent")
        schema = outer.get("schema_identity")
        if not isinstance(schema, Mapping) or schema.get("schema_domain") != "CAUSAL_MARKET_CONTEXT_BOUNDARY" or schema.get("schema_version") != CAUSAL_CORE_SCHEMA_VERSION:
            raise HypothesisResolutionError("boundary immutable schema identity mismatch")
        facts = content.get("facts")
        if not isinstance(facts, Mapping):
            raise HypothesisResolutionError("boundary facts are missing")
        if _parse_key(facts.get("information_key", {})) != key:
            raise HypothesisResolutionError("boundary fact key differs from immutable record key")
        facts_hash = _core_hash("CORE_BOUNDARY_FACTS_V1", facts)
        if content.get("facts_hash") != facts_hash:
            raise HypothesisResolutionError("boundary facts hash mismatch")
        expected_id = "BOUNDARY-" + _core_hash("CORE_BOUNDARY_RECORD_ID_V1", {"key": key, "facts_hash": facts_hash})
        if outer.get("record_identity") != expected_id or outer.get("record_type") != "CAUSAL_MARKET_CONTEXT_BOUNDARY":
            raise HypothesisResolutionError("boundary immutable record identity mismatch")
        if content.get("prefix_chain_previous") != prefix:
            raise HypothesisResolutionError("causal-core prefix predecessor mismatch")
        step = {
            "position": position,
            "key": key,
            "boundary_id": expected_id,
            "facts_hash": facts_hash,
            "entity_ids": sorted(_string_tuple(facts.get("new_entity_ids", ()), "boundary entity ids")),
            "event_ids": sorted(_string_tuple(facts.get("producer_event_ids", ()), "boundary event ids")),
            "revision_ids": sorted(_string_tuple(facts.get("state_revision_ids", ()), "boundary revision ids")),
            "relation_ids": sorted(_string_tuple(facts.get("relationship_ids", ()), "boundary relation ids")),
            "disagreement_ids": sorted(_string_tuple(facts.get("representation_disagreement_ids", ()), "boundary disagreement ids")),
        }
        prefix = _core_hash("CORE_ASOF_PREFIX_STEP_V1", {"previous": prefix, "step": step})
        if content.get("prefix_chain_current") != prefix:
            raise HypothesisResolutionError("causal-core prefix step mismatch")
        prefixes.append((position, prefix))
        visible_boundaries.append({"outer": _plain(outer), "key": key, "content": content, "facts": _plain(facts)})
    return tuple(prefixes), tuple(visible_boundaries)


def _string_tuple(values: Any, label: str) -> tuple[str, ...]:
    if isinstance(values, str) or not isinstance(values, (tuple, list)):
        raise HypothesisResolutionError(f"{label} must be an ordered sequence of record identities")
    items = tuple(values)
    if any(not isinstance(item, str) or not item for item in items) or len(set(items)) != len(items):
        raise HypothesisResolutionError(f"{label} contains invalid or duplicate identities")
    return items


def _verify_core_record(
    record: PublishedRecord,
    *,
    identity: str,
    record_type: str,
    schema_domain: str,
    key: InformationKey,
    label: str,
) -> None:
    if not isinstance(record, PublishedRecord):
        raise HypothesisResolutionError(f"{label} lacks a causal-core PublishedRecord")
    if record.record_identity != identity or record.record_type != record_type:
        raise HypothesisResolutionError(f"{label} immutable record identity/type mismatch")
    if record.schema_identity.schema_domain != schema_domain or record.schema_identity.schema_version != CAUSAL_CORE_SCHEMA_VERSION:
        raise HypothesisResolutionError(f"{label} immutable schema identity mismatch")
    if record.timeline_id != key.timeline_id or record.availability_key != key:
        raise HypothesisResolutionError(f"{label} PublishedRecord information-time identity mismatch")


def _verify_core_entity(entity: CoreEntity) -> None:
    if not isinstance(entity, CoreEntity):
        raise HypothesisResolutionError("causal-core entity stream contains a non-CoreEntity value")
    payload = _plain(entity.record.content)
    if not isinstance(payload, Mapping):
        raise HypothesisResolutionError("causal-core entity payload is malformed")
    producer_contract = payload.get("producer_contract")
    expected_identity = "ENT-" + _core_hash("CORE_ENTITY_ID_V1", {
        "domain": entity.domain,
        "representation_id": entity.representation_id,
        "producer_contract": producer_contract,
        "source_entity_id": entity.source_entity_id,
    })
    expected_type = f"CAUSAL_MARKET_ENTITY::{entity.domain}"
    _verify_core_record(
        entity.record,
        identity=expected_identity,
        record_type=expected_type,
        schema_domain="CAUSAL_MARKET_ENTITY",
        key=entity.availability_key,
        label="causal-core entity",
    )
    geometry = payload.get("geometry")
    if (
        payload.get("entity_id") != entity.entity_id
        or payload.get("source_entity_id") != entity.source_entity_id
        or payload.get("domain") != entity.domain
        or payload.get("representation_id") != entity.representation_id
        or payload.get("availability_position") != entity.availability_key.bar_position
        or payload.get("availability_semantics") != "PRODUCER_DECLARED_ROW_POSITION"
        or payload.get("origin_positions") != list(entity.origin_positions)
        or payload.get("origin_semantics") != "PRODUCER_METADATA_REFERENCE_ONLY_NOT_HISTORICAL_FEATURE_AVAILABILITY"
        or entity.geometry_state != "AVAILABLE_PRODUCER_GEOMETRY"
        or not isinstance(producer_contract, str)
        or not isinstance(payload.get("producer_row"), Mapping)
        or not isinstance(geometry, Mapping)
        or geometry.get("semantics") != "PRODUCER_BOUNDS_CLOSED_INTERVAL_INDEX_ONLY"
        or geometry.get("low") != entity.low
        or geometry.get("high") != entity.high
        or not isinstance(entity.low, (int, float))
        or isinstance(entity.low, bool)
        or not math.isfinite(float(entity.low))
        or not isinstance(entity.high, (int, float))
        or isinstance(entity.high, bool)
        or not math.isfinite(float(entity.high))
        or entity.low > entity.high
    ):
        raise HypothesisResolutionError("causal-core entity payload differs from its immutable typed fields")


def _verify_core_event(event: ProducerEvent) -> None:
    if not isinstance(event, ProducerEvent):
        raise HypothesisResolutionError("causal-core producer-event stream contains a non-ProducerEvent value")
    payload = _plain(event.record.content)
    if not isinstance(payload, Mapping):
        raise HypothesisResolutionError("causal-core producer-event payload is malformed")
    producer_row = payload.get("producer_row")
    if not isinstance(producer_row, Mapping) or not isinstance(event.same_batch_order_unknown, bool):
        raise HypothesisResolutionError("causal-core producer-event row/ordering metadata is malformed")
    if event.domain == "STAGE4B1_CONFIRMED_SWING":
        expected_id = "EVT-" + _core_hash("CORE_STAGE4B1_EVENT_ID_V1", {
            "entity_id": event.entity_id,
            "key": event.key,
            "event_type": event.event_type,
            "producer_row": producer_row,
        })
        expected_record_type = "CAUSAL_MARKET_PRODUCER_EVENT::STAGE4B1"
    else:
        expected_id = "EVT-" + _core_hash("CORE_PRODUCER_EVENT_ID_V1", {
            "entity_id": event.entity_id,
            "key": event.key,
            "event_type": event.event_type,
            "producer_row": producer_row,
        })
        expected_record_type = f"CAUSAL_MARKET_PRODUCER_EVENT::{event.domain}"
    _verify_core_record(
        event.record,
        identity=expected_id,
        record_type=expected_record_type,
        schema_domain="CAUSAL_MARKET_PRODUCER_EVENT",
        key=event.key,
        label="causal-core producer event",
    )
    if (
        event.event_id != expected_id
        or payload.get("event_id") != event.event_id
        or payload.get("entity_id") != event.entity_id
        or payload.get("domain") != event.domain
        or payload.get("event_type") != event.event_type
        or ("same_information_batch_order_unknown" in payload and payload["same_information_batch_order_unknown"] != event.same_batch_order_unknown)
    ):
        raise HypothesisResolutionError("causal-core producer-event payload differs from its immutable typed fields")


def _verify_core_relation(relation: Relation) -> None:
    if not isinstance(relation, Relation):
        raise HypothesisResolutionError("causal-core relationship stream contains a non-Relation value")
    evidence = tuple(sorted(set(relation.evidence_ids)))
    if evidence != relation.evidence_ids or not isinstance(relation.same_batch, bool):
        raise HypothesisResolutionError("causal-core relationship evidence/order metadata is malformed")
    expected_id = "REL-" + _core_hash("CORE_RELATIONSHIP_ID_V1", {
        "kind": relation.relation_type,
        "key": relation.key,
        "left": relation.left_id,
        "right": relation.right_id,
        "evidence": list(evidence),
        "same_batch": relation.same_batch,
        "facts": _plain(relation.facts),
    })
    if expected_id != relation.relation_id:
        raise HypothesisResolutionError("causal-core relationship identity/content mismatch")


def _verify_memory_result_envelope(replay: ReplayMemoryResult, provenance: Mapping[str, Any]) -> None:
    summary = replay.summary
    actual_counts = (
        len(replay.boundaries),
        len(replay.entities),
        len(replay.events),
        len(replay.revisions),
        len(replay.relationships),
        len(replay.interpretations),
        len(replay.disagreements),
        len(replay.relationship_coverage_rows),
    )
    declared_counts = (
        summary.boundary_count,
        summary.entity_count,
        summary.producer_event_count,
        summary.state_revision_count,
        summary.relationship_count,
        summary.interpretation_revision_count,
        summary.disagreement_count,
        summary.boundary_count,
    )
    if actual_counts != declared_counts:
        raise HypothesisResolutionError("causal-core memory stream counts differ from the immutable replay summary")
    relation_counts = dict(sorted(Counter(item.relation_type for item in replay.relationships).items()))
    if dict(summary.relationship_counts_by_type) != relation_counts or _plain(provenance.get("relationship_counts_by_type")) != relation_counts:
        raise HypothesisResolutionError("causal-core relationship type counts differ from replay streams")
    candidate_counts = dict(sorted(Counter(f"{item.domain}:{item.representation_id}" for item in replay.entities).items()))
    if dict(summary.candidates_by_domain_representation) != candidate_counts or _plain(provenance.get("candidate_counts_by_domain_representation")) != candidate_counts:
        raise HypothesisResolutionError("causal-core candidate counts differ from the registered entity stream")
    if summary.source_validation_state != provenance.get("source_validation_state"):
        raise HypothesisResolutionError("causal-core source-validation state differs between run provenance and summary")
    if summary.relationship_coverage_state != provenance.get("relationship_search_state"):
        raise HypothesisResolutionError("causal-core relationship-search coverage differs between summary and provenance")
    if summary.prefix_chain_sha256 != provenance.get("prefix_chain_sha256"):
        raise HypothesisResolutionError("causal-core final prefix identity differs between summary and provenance")
    source_identity = provenance.get("source_identity")
    if not isinstance(source_identity, Mapping):
        raise HypothesisResolutionError("causal-core run provenance lacks source identity")
    source_hash = _require_hash(provenance.get("source_hash"), "causal-core source hash")
    timeline_hash = _require_hash(provenance.get("timeline_hash"), "causal-core timeline hash")
    expected_run_id = _core_hash("CORE_RUN_ID_V1", {
        "source_identity": source_identity,
        "source_hash": source_hash,
        "timeline_hash": timeline_hash,
    })
    if summary.run_id != expected_run_id:
        raise HypothesisResolutionError("causal-core run identity does not match source/timeline provenance")


def verify_asof_context(
    replay: ReplayMemoryResult,
    as_of_key: InformationKey,
    *,
    limits: ResolutionLimits = ResolutionLimits(),
) -> VerifiedAsOfContext:
    """Verify and freeze a causal-core memory replay prefix through ``as_of_key``.

    It recomputes the causal-core boundary facts/prefix chain only through the
    requested position, then verifies candidate/event/revision/relation
    coverage and every visible dependency. Later rows are not returned to the
    hypothesis policy.
    """
    if not isinstance(replay, ReplayMemoryResult):
        raise HypothesisResolutionError("ReplayMemoryResult from the causal context core is required")
    if not isinstance(as_of_key, InformationKey) or as_of_key.information_phase not in LEGAL_ASOF_PHASES:
        raise HypothesisResolutionError("legal completed-row or research-snapshot as-of key required")
    provenance = _plain(replay.run_provenance)
    _verify_memory_result_envelope(replay, provenance)
    timeline_id = provenance.get("timeline_id")
    if as_of_key.timeline_id != timeline_id:
        raise HypothesisResolutionError("as-of key timeline does not match causal-core source")
    if as_of_key.bar_position >= replay.summary.boundary_count:
        raise HypothesisResolutionError("as-of key is outside the verified causal-core boundary range")
    prefixes, boundaries = _core_prefix(replay, as_of_key.bar_position)
    boundary = boundaries[-1]
    boundary_key = boundary["key"]
    if as_of_key.event_time_utc != boundary_key.event_time_utc:
        raise HypothesisResolutionError("as-of key timestamp differs from the causal-core boundary")
    if as_of_key.information_phase is InformationPhase.COMPLETED_ROW_AVAILABLE:
        if as_of_key != boundary_key:
            raise HypothesisResolutionError("completed-row key must exactly match its core boundary")
    elif as_of_key <= boundary_key:
        raise HypothesisResolutionError("research snapshot must be strictly after its completed-row boundary")

    source_identity = provenance.get("source_identity")
    if not isinstance(source_identity, Mapping) or not source_identity:
        raise HypothesisResolutionError("causal-core source identity missing")
    source_identity_sha256 = _digest("CONTEXTUAL_HYPOTHESIS_SOURCE_IDENTITY_V1", source_identity)
    source_file_sha256 = _require_hash(provenance.get("source_hash"), "causal-core source hash")
    source_validation_state = replay.summary.source_validation_state
    source_semantics = provenance.get("source_semantics")
    if not isinstance(source_validation_state, str) or not source_validation_state or not isinstance(source_semantics, str) or not source_semantics:
        raise HypothesisResolutionError("source validation state/semantics missing")
    if provenance.get("candidate_universe_complete") is not True:
        raise HypothesisResolutionError("causal-core candidate universe is not certified complete")

    structural_rows = provenance.get("structural_policies", ())
    representation_policies: list[RepresentationPolicyIdentity] = []
    policy_by_representation: dict[str, str] = {}
    for item in structural_rows:
        item = _plain(item)
        representation_id = item.get("representation_id")
        if not isinstance(representation_id, str) or representation_id in policy_by_representation:
            raise HypothesisResolutionError("duplicate/malformed structural representation identity")
        digest = _require_hash(item.get("policy_sha256"), "structural policy identity")
        policy_by_representation[representation_id] = digest
        representation_policies.append(RepresentationPolicyIdentity(
            representation_id=representation_id,
            state="EXPLICIT_POLICY_CONFIGURED",
            policy_id=item.get("policy", {}).get("policy_id"),
            policy_version=item.get("policy", {}).get("policy_version"),
            policy_sha256=digest,
            surface_ids=tuple(str(item[name]) for name in (
                "structure_surface_id", "liquidity_surface_id", "order_block_surface_id", "dealing_range_surface_id"
            ) if item.get(name) is not None),
        ))
    representation_policies.append(RepresentationPolicyIdentity(
        representation_id="REP-STRUCTURE-INDEPENDENT-FVG",
        state="PRODUCER_DEFINED_NO_ADDITIONAL_INTERPRETATION_POLICY",
        policy_id=None,
        policy_version=None,
        policy_sha256=None,
        surface_ids=(str(provenance.get("fvg_surface_id")),),
    ))
    representation_policies.sort(key=lambda item: item.representation_id)

    position = as_of_key.bar_position
    bar_ids_by_position: dict[int, str] = {}
    evidence: list[ContextEvidence] = []
    expected_by_stream: dict[str, set[str]] = {name: set() for name in ("entities", "events", "revisions", "relationships", "disagreements")}
    stream_ids_by_position: dict[str, dict[int, set[str]]] = {
        name: defaultdict(set) for name in expected_by_stream
    }

    for item in boundaries:
        key, facts = item["key"], item["facts"]
        expected_by_stream["entities"].update(_string_tuple(facts.get("new_entity_ids", ()), "entity ids"))
        expected_by_stream["events"].update(_string_tuple(facts.get("producer_event_ids", ()), "event ids"))
        expected_by_stream["revisions"].update(_string_tuple(facts.get("state_revision_ids", ()), "revision ids"))
        expected_by_stream["relationships"].update(_string_tuple(facts.get("relationship_ids", ()), "relationship ids"))
        expected_by_stream["disagreements"].update(_string_tuple(facts.get("representation_disagreement_ids", ()), "disagreement ids"))
        bar = facts.get("published_bar_record")
        if not isinstance(bar, Mapping) or not isinstance(bar.get("record_identity"), str):
            raise HypothesisResolutionError("published bar evidence is missing from a causal boundary")
        bar_id = bar["record_identity"]
        content = bar.get("content")
        if not isinstance(content, Mapping) or not isinstance(content.get("ohlcv"), Mapping):
            raise HypothesisResolutionError("published bar payload is malformed")
        row = _plain(content["ohlcv"])
        expected_bar_id = "BAR-" + _core_hash("CAUSAL_MARKET_CONTEXT_BAR_FACT_V1", {
            "timeline_id": key.timeline_id,
            "position": key.bar_position,
            "event_time_utc": key.event_time_utc,
            "row": row,
        })
        if expected_bar_id != bar_id:
            raise HypothesisResolutionError("published bar identity does not match its source facts")
        bar_ids_by_position[key.bar_position] = bar_id
        evidence.append(_record_evidence(
            evidence_id=bar_id,
            record_type="PUBLISHED_OHLC_OBSERVATION_FACT",
            key=key,
            schema_identity=bar.get("schema_identity", {}),
            payload=content,
            source_identity_sha256=source_identity_sha256,
            representation_id=None,
            representation_policy_sha256=None,
        ))

    visible_count = len(boundaries) + len(bar_ids_by_position)
    if visible_count > limits.max_visible_evidence_records:
        raise HypothesisResolutionError(
            f"visible evidence limit exceeded ({visible_count}>{limits.max_visible_evidence_records}); no evidence was pruned"
        )
    for rows, key_for in (
        (replay.entities, lambda item: item.availability_key),
        (replay.events, lambda item: item.key),
        (replay.revisions, lambda item: item.key),
        (replay.relationships, lambda item: item.key),
    ):
        for row in rows:
            if key_for(row).bar_position <= position:
                visible_count += 1
                if visible_count > limits.max_visible_evidence_records:
                    raise HypothesisResolutionError(
                        f"visible evidence limit exceeded ({visible_count}>{limits.max_visible_evidence_records}); no evidence was pruned"
                    )
    visible_disagreements_list: list[Mapping[str, Any]] = []
    for raw_disagreement in replay.disagreements:
        if not isinstance(raw_disagreement, Mapping) or not isinstance(raw_disagreement.get("information_key"), Mapping):
            raise HypothesisResolutionError("malformed causal-core representation disagreement")
        disagreement_key = _parse_key(raw_disagreement["information_key"])
        if disagreement_key.timeline_id != timeline_id:
            raise HypothesisResolutionError("representation disagreement has a foreign timeline")
        if disagreement_key.bar_position <= position:
            visible_count += 1
            if visible_count > limits.max_visible_evidence_records:
                raise HypothesisResolutionError(
                    f"visible evidence limit exceeded ({visible_count}>{limits.max_visible_evidence_records}); no evidence was pruned"
                )
            visible_disagreements_list.append(_plain(raw_disagreement))
    visible_entities = tuple(item for item in replay.entities if item.availability_key.bar_position <= position)
    visible_events = tuple(item for item in replay.events if item.key.bar_position <= position)
    visible_revisions = tuple(item for item in replay.revisions if item.key.bar_position <= position)
    visible_relationships = tuple(item for item in replay.relationships if item.key.bar_position <= position)
    visible_disagreements = tuple(visible_disagreements_list)

    entity_by_id: dict[str, CoreEntity] = {}
    for entity in visible_entities:
        _verify_core_entity(entity)
        key = entity.availability_key
        if key.timeline_id != timeline_id or entity.record.timeline_id != timeline_id or entity.record.availability_key != key:
            raise HypothesisResolutionError("entity source/availability identity mismatch")
        if replay.entity_availability.get(entity.entity_id) != key:
            raise HypothesisResolutionError("causal-core entity availability index differs from immutable entity records")
        if entity.entity_id in entity_by_id:
            raise HypothesisResolutionError("duplicate causal-core entity identity")
        if entity.representation_id != "REP-STRUCTURE-INDEPENDENT-FVG" and entity.representation_id not in policy_by_representation:
            raise HypothesisResolutionError("entity representation has no preserved policy identity")
        origin_dependencies = []
        for origin in entity.origin_positions:
            if origin > key.bar_position or origin not in bar_ids_by_position:
                raise HypothesisResolutionError("entity depends on a future or unavailable origin bar")
            origin_dependencies.append(bar_ids_by_position[origin])
        entity_by_id[entity.entity_id] = entity
        stream_ids_by_position["entities"][key.bar_position].add(entity.entity_id)
        evidence.append(_record_evidence(
            evidence_id=entity.record.record_identity,
            record_type=entity.record.record_type,
            key=key,
            schema_identity=entity.record.schema_identity.as_payload(),
            payload=entity.record.content,
            source_identity_sha256=source_identity_sha256,
            representation_id=entity.representation_id,
            representation_policy_sha256=policy_by_representation.get(entity.representation_id),
            dependencies=origin_dependencies,
        ))
    if {item.entity_id for item in visible_entities} != expected_by_stream["entities"]:
        raise HypothesisResolutionError("as-of entity registry differs from causal boundary candidate coverage")

    event_by_id: dict[str, ProducerEvent] = {}
    for event in visible_events:
        _verify_core_event(event)
        if event.key.timeline_id != timeline_id or event.record.timeline_id != timeline_id or event.record.availability_key != event.key:
            raise HypothesisResolutionError("producer-event source/availability identity mismatch")
        entity = entity_by_id.get(event.entity_id)
        if entity is None or entity.availability_key > event.key:
            raise HypothesisResolutionError("producer event references an unknown/future entity")
        if event.event_id in event_by_id:
            raise HypothesisResolutionError("duplicate producer-event identity")
        event_by_id[event.event_id] = event
        stream_ids_by_position["events"][event.key.bar_position].add(event.event_id)
        evidence.append(_record_evidence(
            evidence_id=event.record.record_identity,
            record_type=event.record.record_type,
            key=event.key,
            schema_identity=event.record.schema_identity.as_payload(),
            payload=event.record.content,
            source_identity_sha256=source_identity_sha256,
            representation_id=entity.representation_id,
            representation_policy_sha256=policy_by_representation.get(entity.representation_id),
            dependencies=(entity.record.record_identity,),
        ))
    if set(event_by_id) != expected_by_stream["events"]:
        raise HypothesisResolutionError("as-of producer-event stream differs from causal boundary event coverage")

    revision_ids: set[str] = set()
    revision_state: dict[str, tuple[str | None, int, set[str]]] = {}
    revision_positions: set[tuple[str, int]] = set()
    for revision in sorted(visible_revisions, key=lambda item: (item.key.bar_position, item.entity_id, item.revision_id)):
        if not isinstance(revision, EntityRevision):
            raise HypothesisResolutionError("causal-core state-revision stream contains a non-EntityRevision value")
        if revision.key.timeline_id != timeline_id:
            raise HypothesisResolutionError("entity revision timeline identity mismatch")
        entity = entity_by_id.get(revision.entity_id)
        if entity is None or entity.availability_key > revision.key:
            raise HypothesisResolutionError("entity revision references unknown/future entity")
        if (revision.entity_id, revision.key.bar_position) in revision_positions:
            raise HypothesisResolutionError("multiple state revisions for one entity at the same boundary")
        revision_positions.add((revision.entity_id, revision.key.bar_position))
        if revision.event_ids != tuple(sorted(set(revision.event_ids))):
            raise HypothesisResolutionError("entity revision event references are unordered or duplicated")
        event_rows: list[ProducerEvent] = []
        for event_id in revision.event_ids:
            event = event_by_id.get(event_id)
            if event is None or event.entity_id != revision.entity_id or event.key != revision.key:
                raise HypothesisResolutionError("entity revision references an unknown/mismatched producer event")
            event_rows.append(event)
        if not event_rows:
            raise HypothesisResolutionError("entity state revision has no producer events")
        previous_id, previous_number, previous_types = revision_state.get(revision.entity_id, (None, 0, set()))
        types_at_key = tuple(sorted({item.event_type for item in event_rows}))
        types_seen = tuple(sorted(previous_types.union(types_at_key)))
        expected_ambiguous = len(event_rows) > 1 or any(item.same_batch_order_unknown for item in event_rows)
        expected_revision_id = "STATE-" + _core_hash("CORE_ENTITY_STATE_REVISION_V1", {
            "entity_id": revision.entity_id,
            "previous": previous_id,
            "number": previous_number + 1,
            "key": revision.key,
            "event_ids": list(revision.event_ids),
            "types_at_key": list(types_at_key),
            "types_seen": list(types_seen),
            "same_batch_order_unknown": expected_ambiguous,
        })
        _verify_core_record(
            revision.record,
            identity=expected_revision_id,
            record_type="CAUSAL_MARKET_ENTITY_STATE_REVISION",
            schema_domain="CAUSAL_MARKET_ENTITY_STATE",
            key=revision.key,
            label="causal-core entity state revision",
        )
        revision_payload = _plain(revision.record.content)
        if (
            revision.revision_id != expected_revision_id
            or revision.previous_revision_id != previous_id
            or revision.revision_number != previous_number + 1
            or revision.event_types_at_key != types_at_key
            or revision.event_types_seen_as_set != types_seen
            or revision.same_batch_order_unknown is not expected_ambiguous
            or revision_payload.get("revision_id") != expected_revision_id
            or revision_payload.get("entity_id") != revision.entity_id
            or revision_payload.get("previous_revision_id") != previous_id
            or revision_payload.get("revision_number") != previous_number + 1
            or _parse_key(revision_payload.get("available_key", {})) != revision.key
            or revision_payload.get("event_ids_at_boundary") != list(revision.event_ids)
            or revision_payload.get("event_types_at_boundary") != list(types_at_key)
            or revision_payload.get("event_types_seen_as_set") != list(types_seen)
            or revision_payload.get("same_information_batch_order_unknown") is not expected_ambiguous
            or revision_payload.get("projection_semantics") != "SET_OF_PRODUCER_FACTS_NO_WITHIN_BATCH_ORDER"
            or revision_payload.get("no_active_filled_or_invalidated_status_inferred") is not True
        ):
            raise HypothesisResolutionError("entity state revision identity/content differs from its declared event facts")
        revision_state[revision.entity_id] = (expected_revision_id, previous_number + 1, set(types_seen))
        if revision.revision_id in revision_ids:
            raise HypothesisResolutionError("duplicate entity state revision identity")
        revision_ids.add(revision.revision_id)
        stream_ids_by_position["revisions"][revision.key.bar_position].add(revision.revision_id)
        evidence.append(_record_evidence(
            evidence_id=revision.record.record_identity,
            record_type=revision.record.record_type,
            key=revision.key,
            schema_identity=revision.record.schema_identity.as_payload(),
            payload=revision.record.content,
            source_identity_sha256=source_identity_sha256,
            representation_id=entity.representation_id,
            representation_policy_sha256=policy_by_representation.get(entity.representation_id),
            dependencies=(entity.record.record_identity,) + tuple(revision.event_ids),
        ))
    if revision_ids != expected_by_stream["revisions"]:
        raise HypothesisResolutionError("as-of entity-state revision stream differs from boundary coverage")

    known_record_keys: dict[str, InformationKey] = {}
    for item in evidence:
        if item.evidence_id in known_record_keys:
            raise HypothesisResolutionError("causal-core evidence record identity collision")
        known_record_keys[item.evidence_id] = item.information_key
    for entity in visible_entities:
        known_record_keys[entity.entity_id] = entity.availability_key
    for event in visible_events:
        known_record_keys[event.event_id] = event.key
    for revision in visible_revisions:
        known_record_keys[revision.revision_id] = revision.key

    relation_ids: set[str] = set()
    for relation in visible_relationships:
        _verify_core_relation(relation)
        if relation.key.timeline_id != timeline_id or relation.key > as_of_key:
            raise HypothesisResolutionError("relationship is cross-timeline or future-derived")
        if relation.relation_id in relation_ids:
            raise HypothesisResolutionError("duplicate relationship identity")
        for evidence_id in relation.evidence_ids:
            evidence_key = known_record_keys.get(evidence_id)
            if evidence_key is None or evidence_key > relation.key:
                raise HypothesisResolutionError("relationship cites unknown/future evidence")
        for endpoint in (relation.left_id, relation.right_id):
            endpoint_key = known_record_keys.get(endpoint)
            if endpoint_key is None or endpoint_key > relation.key:
                raise HypothesisResolutionError("relationship endpoint is unknown or future-derived")
        relation_ids.add(relation.relation_id)
        stream_ids_by_position["relationships"][relation.key.bar_position].add(relation.relation_id)
        evidence.append(_record_evidence(
            evidence_id=relation.relation_id,
            record_type=relation.relation_type,
            key=relation.key,
            schema_identity={"schema_domain": "CAUSAL_MARKET_CONTEXT_RELATION", "schema_version": CAUSAL_CORE_SCHEMA_VERSION},
            payload=relation.payload(),
            source_identity_sha256=source_identity_sha256,
            representation_id=None,
            representation_policy_sha256=None,
            dependencies=relation.evidence_ids,
        ))
    if relation_ids != expected_by_stream["relationships"]:
        raise HypothesisResolutionError("as-of relationship stream differs from boundary relation coverage")

    disagreement_ids: set[str] = set()
    for item in visible_disagreements:
        key = _parse_key(item["information_key"])
        if key.timeline_id != timeline_id or key > as_of_key:
            raise HypothesisResolutionError("representation disagreement is future or cross-timeline")
        record_id = item.get("record_id")
        states = item.get("representations")
        if not isinstance(record_id, str) or record_id in disagreement_ids or item.get("state") != "POLICY_OUTPUTS_DIFFER_NO_WINNER_SELECTED" or item.get("same_batch_order_unknown") is not True:
            raise HypothesisResolutionError("invalid/duplicate disagreement record identity or semantics")
        if not isinstance(states, (tuple, list)) or len(states) < 2:
            raise HypothesisResolutionError("representation disagreement lacks competing policy rows")
        state_identities: list[tuple[str, str]] = []
        seen_representations: set[str] = set()
        for state in states:
            if not isinstance(state, Mapping):
                raise HypothesisResolutionError("malformed representation disagreement row")
            representation_id = state.get("representation_id")
            facts = state.get("facts")
            if not isinstance(representation_id, str) or representation_id in seen_representations or representation_id not in policy_by_representation or not isinstance(facts, Mapping):
                raise HypothesisResolutionError("representation disagreement row lacks a declared policy identity")
            if state.get("policy_sha256") != policy_by_representation[representation_id]:
                raise HypothesisResolutionError("representation disagreement policy identity mismatch")
            row_sha256 = _core_hash("CORE_STRUCTURE_ROW_V1", facts)
            if state.get("row_sha256") != row_sha256:
                raise HypothesisResolutionError("representation disagreement row hash mismatch")
            seen_representations.add(representation_id)
            state_identities.append((representation_id, row_sha256))
        expected_record_id = "DIFF-" + _core_hash("CORE_STRUCTURE_DISAGREEMENT_V1", {
            "position": key.bar_position,
            "representations": state_identities,
        })
        if len({item[1] for item in state_identities}) < 2 or record_id != expected_record_id:
            raise HypothesisResolutionError("representation disagreement record identity/content mismatch")
        disagreement_ids.add(record_id)
        stream_ids_by_position["disagreements"][key.bar_position].add(record_id)
        evidence.append(_record_evidence(
            evidence_id=record_id,
            record_type="CAUSAL_MARKET_CONTEXT_REPRESENTATION_DISAGREEMENT",
            key=key,
            schema_identity={"schema_domain": "CAUSAL_MARKET_CONTEXT_REPRESENTATION_DISAGREEMENT", "schema_version": CAUSAL_CORE_SCHEMA_VERSION},
            payload=item,
            source_identity_sha256=source_identity_sha256,
            representation_id=None,
            representation_policy_sha256=None,
            dependencies=(),
        ))
    if disagreement_ids != expected_by_stream["disagreements"]:
        raise HypothesisResolutionError("as-of representation disagreements differ from boundary coverage")

    boundary_fields = {
        "entities": "new_entity_ids",
        "events": "producer_event_ids",
        "revisions": "state_revision_ids",
        "relationships": "relationship_ids",
        "disagreements": "representation_disagreement_ids",
    }
    for boundary_item in boundaries:
        boundary_position = boundary_item["key"].bar_position
        facts = boundary_item["facts"]
        for stream_name, field_name in boundary_fields.items():
            expected_ids = set(_string_tuple(facts.get(field_name, ()), f"{stream_name} at boundary {boundary_position}"))
            actual_ids = stream_ids_by_position[stream_name].get(boundary_position, set())
            if actual_ids != expected_ids:
                raise HypothesisResolutionError(f"as-of {stream_name} at boundary {boundary_position} differ from core candidate coverage")

    boundary_evidence: list[ContextEvidence] = []
    for item in boundaries:
        facts = item["facts"]
        key = item["key"]
        dependencies = [facts["published_bar_record"]["record_identity"]]
        for field_name in ("new_entity_ids", "producer_event_ids", "state_revision_ids", "relationship_ids", "representation_disagreement_ids"):
            dependencies.extend(facts.get(field_name, ()))
        outer = item["outer"]
        boundary_evidence.append(_record_evidence(
            evidence_id=outer["record_identity"],
            record_type=outer["record_type"],
            key=key,
            schema_identity=outer.get("schema_identity", {}),
            payload=item["content"],
            source_identity_sha256=source_identity_sha256,
            representation_id=None,
            representation_policy_sha256=None,
            dependencies=dependencies,
        ))
    evidence.extend(boundary_evidence)

    # Register all identifiers, including non-record entity/event ids, then
    # enforce that every dependency resolves no later than its consumer.
    evidence_by_id: dict[str, ContextEvidence] = {}
    for item in evidence:
        if item.evidence_id in evidence_by_id:
            raise HypothesisResolutionError("duplicate context evidence identity")
        evidence_by_id[item.evidence_id] = item
    for item in evidence:
        for dependency_id in item.dependency_record_ids:
            dependency = evidence_by_id.get(dependency_id)
            dep_key = known_record_keys.get(dependency_id) if dependency is None else dependency.information_key
            if dep_key is None or dep_key.timeline_id != item.information_key.timeline_id or dep_key > item.information_key:
                raise HypothesisResolutionError("context evidence has an unresolved or future-derived dependency")

    if replay.entity_availability:
        for entity_id, available_key in replay.entity_availability.items():
            if available_key.bar_position <= position:
                try:
                    replay.entity_state_as_of(entity_id, as_of_key)
                except CausalMarketContextCoreError as exc:
                    raise HypothesisResolutionError(f"causal-core as-of entity-state validation failed: {exc}") from exc

    coverage = replay.relationship_coverage_rows[position]
    if not isinstance(coverage, Mapping):
        raise HypothesisResolutionError("relationship coverage row is missing at requested boundary")
    if _parse_key(coverage["information_key"]) != boundary_key:
        raise HypothesisResolutionError("relationship coverage key does not match boundary")
    facts = boundary["facts"]
    domain_availability = facts.get("domain_availability_at_this_key")
    if not isinstance(domain_availability, Mapping):
        raise HypothesisResolutionError("as-of domain availability facts are missing")
    context_identity_payload = {
        "core_id": CAUSAL_CORE_ID,
        "core_schema_version": CAUSAL_CORE_SCHEMA_VERSION,
        "source_identity_sha256": source_identity_sha256,
        "timeline_id": timeline_id,
        "as_of_key": as_of_key,
        "prefix_chain_sha256": prefixes[-1][1],
        "evidence_ids": sorted(item.evidence_id for item in evidence),
        "evidence_hashes": sorted(item.payload_sha256 for item in evidence),
    }
    snapshot_id = "CTX-" + _digest("CONTEXTUAL_HYPOTHESIS_VERIFIED_ASOF_CONTEXT_V1", context_identity_payload)
    return VerifiedAsOfContext(
        _seal=_CONTEXT_SEAL,
        as_of_key=as_of_key,
        snapshot_id=snapshot_id,
        core_run_id=str(replay.summary.run_id),
        core_id=CAUSAL_CORE_ID,
        core_schema_version=CAUSAL_CORE_SCHEMA_VERSION,
        source_identity=_freeze(source_identity),
        source_identity_sha256=source_identity_sha256,
        source_file_sha256=source_file_sha256,
        source_validation_state=source_validation_state,
        source_semantics=source_semantics,
        timeline_id=timeline_id,
        prefix_chain_sha256=prefixes[-1][1],
        prefix_chain_by_position=prefixes,
        producer_contracts=_freeze(provenance["producer_contracts"]),
        representation_policies=tuple(representation_policies),
        domain_availability=_freeze(domain_availability),
        relationship_coverage=_freeze(_plain(coverage)),
        evidence=tuple(sorted(evidence, key=lambda item: (item.information_key.bar_position, item.record_type, item.evidence_id))),
    )


def _policy_safe_payload(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _policy_safe_payload(item)
            for key, item in value.items()
            if str(key) not in {"source_identity", "source_hash", "source_file_sha256", "timeline_hash"}
        }
    if isinstance(value, (tuple, list)):
        return tuple(_policy_safe_payload(item) for item in value)
    return value


def _policy_view(context: VerifiedAsOfContext) -> PolicyInput:
    if context._verification_seal is not _CONTEXT_SEAL:
        raise HypothesisResolutionError("unverified context object")
    policy_evidence = tuple(
        ContextEvidence(
            evidence_id=item.evidence_id,
            record_type=item.record_type,
            information_key=item.information_key,
            schema_identity=item.schema_identity,
            payload=_freeze(_policy_safe_payload(item.payload)),
            source_identity_sha256=item.source_identity_sha256,
            representation_id=item.representation_id,
            representation_policy_sha256=item.representation_policy_sha256,
            dependency_record_ids=item.dependency_record_ids,
            payload_sha256=item.payload_sha256,
        )
        for item in context.evidence
    )
    return PolicyInput(
        as_of_key=context.as_of_key,
        context_snapshot_id=context.snapshot_id,
        source_identity_reference=context.source_identity_sha256,
        evidence=policy_evidence,
        domain_availability=context.domain_availability,
        representation_policies=tuple(
            PolicyRepresentationIdentity(
                representation_id=item.representation_id,
                state=item.state,
                policy_id=item.policy_id,
                policy_version=item.policy_version,
                policy_sha256=item.policy_sha256,
            )
            for item in context.representation_policies
        ),
    )


def _get_path(payload: Mapping[str, Any], path: Sequence[str]) -> tuple[bool, Any]:
    current: Any = payload
    for name in path:
        if not isinstance(current, Mapping) or name not in current:
            return False, None
        current = current[name]
    if isinstance(current, (Mapping, tuple, list)):
        return False, None
    return True, current


def _pair_identity(group_id: str, left: str, right: str) -> tuple[str, tuple[str, str]]:
    ids = tuple(sorted((left, right)))
    return "PAIR-" + _digest("CONTEXTUAL_HYPOTHESIS_ALTERNATIVE_PAIR_V1", {"group_id": group_id, "hypothesis_ids": list(ids)}), ids


def _contract_hashes(contracts: Sequence[ExactValueDiscriminatorContract]) -> tuple[str, ...]:
    return tuple(sorted(item.contract_sha256 for item in contracts))


def _authorization_allowed(policy: AuthorizedHypothesisPolicy | None, mode: AnalysisMode) -> bool:
    if policy is None or not isinstance(policy, AuthorizedHypothesisPolicy):
        return False
    identity = policy.identity
    if identity.authorization_status != "AUTHORIZED":
        return False
    if mode is AnalysisMode.OPERATIONAL:
        return identity.authorization_scope is AuthorizationScope.OPERATIONAL_INTERPRETATION
    return identity.authorization_scope in {AuthorizationScope.SOFTWARE_TEST_ONLY, AuthorizationScope.OPERATIONAL_INTERPRETATION}


class HypothesisResolutionSession:
    """One append-only hypothesis generation with evidence-driven reassessment."""

    def __init__(self, *, limits: ResolutionLimits = ResolutionLimits()) -> None:
        self.limits = limits
        self.ledger = HypothesisResolutionLedger()
        self._generation: HypothesisSetState | None = None
        self._latest_context: VerifiedAsOfContext | None = None
        self._cycle_ordinal = 0
        self._latest_cycle: AnalysisCycle | None = None
        self._mode = AnalysisMode.OPERATIONAL

    @property
    def generation(self) -> HypothesisSetState | None:
        return self._generation

    def analyze(
        self,
        context: VerifiedAsOfContext,
        *,
        policy: AuthorizedHypothesisPolicy | None = None,
        discriminators: Sequence[ExactValueDiscriminatorContract] = (),
        mode: AnalysisMode = AnalysisMode.OPERATIONAL,
    ) -> ResolutionResult:
        if self._generation is not None or self._latest_context is not None:
            raise HypothesisResolutionError("session already started; use reassess to preserve history")
        if not isinstance(context, VerifiedAsOfContext) or context._verification_seal is not _CONTEXT_SEAL:
            raise HypothesisResolutionError("verified as-of causal-core context required")
        if not isinstance(mode, AnalysisMode):
            raise HypothesisResolutionError("explicit analysis mode required")
        self._mode = mode
        self._latest_context = context
        return self._new_generation(
            context,
            policy=policy,
            discriminators=discriminators,
            mode=mode,
            cause=ReassessmentCause.INITIAL_ANALYSIS,
        )

    def reassess(
        self,
        context: VerifiedAsOfContext,
        *,
        policy: AuthorizedHypothesisPolicy | None = None,
        discriminators: Sequence[ExactValueDiscriminatorContract] | None = None,
        mode: AnalysisMode | None = None,
    ) -> ResolutionResult:
        if not isinstance(context, VerifiedAsOfContext) or context._verification_seal is not _CONTEXT_SEAL:
            raise HypothesisResolutionError("verified as-of causal-core context required")
        mode = self._mode if mode is None else mode
        if not isinstance(mode, AnalysisMode):
            raise HypothesisResolutionError("explicit analysis mode required")
        self._mode = mode
        previous_context = self._latest_context
        if previous_context is None:
            return self.analyze(context, policy=policy, discriminators=() if discriminators is None else discriminators, mode=mode)
        generation = self._generation
        if generation is None:
            # A newly authorized policy may be attached after a no-policy cycle.
            self._latest_context = context
            return self._new_generation(
                context,
                policy=policy,
                discriminators=() if discriminators is None else discriminators,
                mode=mode,
                cause=ReassessmentCause.INTERPRETATION_POLICY_CHANGE,
            )
        if context.timeline_id != previous_context.timeline_id or context.as_of_key.bar_position < previous_context.as_of_key.bar_position:
            return self._invalidate_foundation(context, ReassessmentCause.CORRECTED_INPUT, "timeline or information position changed")
        if _plain(context.producer_contracts) != _plain(previous_context.producer_contracts):
            return self._invalidate_foundation(context, ReassessmentCause.CORE_CONTRACT_CHANGE, "causal producer contracts changed")
        policy_scope = lambda rows: tuple((item.representation_id, item.state, item.policy_id, item.policy_version, item.policy_sha256) for item in rows)
        if policy_scope(context.representation_policies) != policy_scope(previous_context.representation_policies):
            return self._invalidate_foundation(context, ReassessmentCause.REPRESENTATION_POLICY_CHANGE, "structural representation policy changed")
        if context.source_identity_sha256 != previous_context.source_identity_sha256:
            return self._invalidate_foundation(context, ReassessmentCause.CORRECTED_INPUT, "source artifact identity changed")
        prior_prefix = context.prefix_at(previous_context.as_of_key.bar_position)
        if prior_prefix != previous_context.prefix_chain_sha256:
            return self._invalidate_foundation(context, ReassessmentCause.CORRECTED_INPUT, "previous as-of prefix changed")

        next_policy = generation.policy if policy is None else policy
        if not _authorization_allowed(next_policy, mode):
            # A policy downgrade is not evidence; keep old assessments immutable
            # and record an explicit new cycle under the unauthorized state.
            self._latest_context = context
            return self._terminal_cycle(
                context,
                status=TerminationStatus.NO_AUTHORIZED_HYPOTHESES,
                generation_state="HYPOTHESIS_GENERATION_NOT_AUTHORIZED",
                cause=ReassessmentCause.INTERPRETATION_POLICY_CHANGE,
                details={"previous_generation_preserved": True, "authorization_is_caller_asserted_not_authenticated": True},
            )
        policy_changed = next_policy.identity.identity_sha256 != generation.policy.identity.identity_sha256
        if discriminators is None:
            next_contracts = generation.contracts
        else:
            if isinstance(discriminators, (str, bytes)) or not isinstance(discriminators, Sequence):
                raise HypothesisResolutionError("discriminators must be a finite sequence of declared contracts")
            if len(discriminators) > self.limits.max_discriminator_contracts:
                self._latest_context = context
                cause = ReassessmentCause.INTERPRETATION_POLICY_CHANGE if policy_changed else ReassessmentCause.DISCRIMINATOR_POLICY_CHANGE
                return self._new_generation(context, policy=next_policy, discriminators=discriminators, mode=mode, cause=cause)
            next_contracts = tuple(discriminators)
        contracts_changed = _contract_hashes(next_contracts) != _contract_hashes(generation.contracts)
        if policy_changed or contracts_changed:
            self._latest_context = context
            self._generation = None
            cause = ReassessmentCause.INTERPRETATION_POLICY_CHANGE if policy_changed else ReassessmentCause.DISCRIMINATOR_POLICY_CHANGE
            return self._new_generation(context, policy=next_policy, discriminators=next_contracts, mode=mode, cause=cause)

        if generation.invalidated:
            self._latest_context = context
            return self._terminal_cycle(
                context,
                status=TerminationStatus.INVALID_FOUNDATION,
                generation_state="HYPOTHESES_INVALIDATED_BY_FOUNDATION_CHANGE",
                cause=ReassessmentCause.CORRECTED_INPUT,
                details={"prior_generation_id": generation.generation_id, "new_evidence_used": False},
            )
        if context.as_of_key < previous_context.as_of_key:
            return self._invalidate_foundation(context, ReassessmentCause.CORRECTED_INPUT, "as-of key moved backward")

        old_ids = {item.evidence_id for item in previous_context.evidence}
        new_ids = {item.evidence_id for item in context.evidence}
        if not old_ids.issubset(new_ids):
            return self._invalidate_foundation(context, ReassessmentCause.CORRECTED_INPUT, "previous visible evidence disappeared")
        policy_context = _policy_view(context)
        newly_visible = tuple(item for item in policy_context.evidence if item.evidence_id not in old_ids)
        if context.as_of_key == previous_context.as_of_key and newly_visible:
            return self._invalidate_foundation(context, ReassessmentCause.CORRECTED_INPUT, "new records appeared without an information-time advance")

        if len(generation.assessments_by_pair) < len(generation.pairs):
            self._latest_context = context
            self._generation = HypothesisSetState(
                generation.generation_id,
                generation.policy,
                generation.contracts,
                generation.hypotheses,
                generation.pairs,
                generation.assessments_by_pair,
                generation.created_context,
                context,
                TerminationStatus.INCOMPLETE_COVERAGE,
                False,
            )
            pending = tuple(sorted(set(item[0] for item in generation.pairs) - set(generation.assessments_by_pair)))
            cycle = self._append_cycle(
                context,
                generation_id=generation.generation_id,
                status=TerminationStatus.INCOMPLETE_COVERAGE,
                generation_state="PRIOR_PAIR_COVERAGE_REMAINS_INCOMPLETE",
                cause=ReassessmentCause.RESOURCE_LIMIT_INCOMPLETE,
                hypothesis_ids=tuple(item.hypothesis_id for item in generation.hypotheses),
                pair_assessment_ids=tuple(item.assessment_id for item in generation.assessments_by_pair.values()),
                affected_pair_ids=(),
                unaffected_pair_ids=(),
                total_pairs=len(generation.pairs),
                evaluated_pairs=len(generation.assessments_by_pair),
                unexamined_pairs=len(pending),
                coverage_state="INCOMPLETE_PAIR_COVERAGE_CARRIED_FORWARD_WITHOUT_CLAIM",
                details={
                    "pending_pair_ids": list(pending),
                    "new_visible_evidence_ids": sorted(item.evidence_id for item in newly_visible),
                    "evidence_used_to_fill_prior_coverage_gap": False,
                },
            )
            return ResolutionResult(cycle, generation.hypotheses, tuple(generation.assessments_by_pair.values()), tuple(self.ledger.records[-1:]), tuple(self.ledger.events[-1:]))

        pair_specs = {pair_id: (group_id, left, right) for pair_id, group_id, left, right in generation.pairs}
        contract_index = self._contract_index(generation.contracts)
        candidate_pairs: dict[str, ExactValueDiscriminatorContract] = {}
        for pair_id, (group_id, left, right) in pair_specs.items():
            contract = self._contract_for_pair(contract_index, (left, right), generation.policy.identity.policy_sha256, group_id)
            previous_assessment = generation.assessments_by_pair.get(pair_id)
            if contract is None or previous_assessment is None:
                continue
            if previous_assessment.pair_status != "UNRESOLVED_WAITING_FOR_SPECIFIC_EVIDENCE" or previous_assessment.evidence_ids:
                continue
            candidate_pairs[pair_id] = contract
        evidence_match_checks = len(candidate_pairs) * len(newly_visible)
        if evidence_match_checks > self.limits.max_discriminator_evidence_checks:
            return self._append_resource_limited_reassessment(
                context,
                generation,
                pair_specs,
                potentially_affected=tuple(candidate_pairs),
                known_affected=(),
                estimated_checks=evidence_match_checks,
                newly_visible=newly_visible,
                affected_set_unknown=True,
            )
        affected: set[str] = set()
        hypotheses_by_id = {item.hypothesis_id: item for item in generation.hypotheses}
        for pair_id, contract in candidate_pairs.items():
            baseline = max(hypotheses_by_id[identity].created_key for identity in contract.hypothesis_ids)
            if any(self._matches_requirement(item, contract, baseline) for item in newly_visible):
                affected.add(pair_id)

        reassessment_checks = len(affected) * len(policy_context.evidence)
        total_evidence_checks = evidence_match_checks + reassessment_checks
        if total_evidence_checks > self.limits.max_discriminator_evidence_checks:
            return self._append_resource_limited_reassessment(
                context,
                generation,
                pair_specs,
                potentially_affected=tuple(sorted(candidate_pairs)),
                known_affected=tuple(sorted(affected)),
                estimated_checks=total_evidence_checks,
                newly_visible=newly_visible,
                affected_set_unknown=False,
            )

        self._latest_context = context
        if not affected:
            latest_status = generation.latest_termination
            cycle = self._append_cycle(
                context,
                generation_id=generation.generation_id,
                status=latest_status,
                generation_state="AUTHORIZED_HYPOTHESES_RETAINED",
                cause=ReassessmentCause.NO_NEW_RELEVANT_EVIDENCE,
                hypothesis_ids=tuple(item.hypothesis_id for item in generation.hypotheses),
                pair_assessment_ids=tuple(item.assessment_id for item in generation.assessments_by_pair.values()),
                affected_pair_ids=(),
                unaffected_pair_ids=tuple(sorted(pair_specs)),
                total_pairs=len(pair_specs),
                evaluated_pairs=0,
                unexamined_pairs=0,
                coverage_state="NO_AFFECTED_HYPOTHESES_NO_NEW_RELEVANT_EVIDENCE",
                details={"new_visible_evidence_ids": sorted(item.evidence_id for item in newly_visible), "old_assessments_rewritten": False},
            )
            return ResolutionResult(cycle, generation.hypotheses, tuple(generation.assessments_by_pair.values()), tuple(self.ledger.records[-1:]), tuple(self.ledger.events[-1:]))

        if len(affected) > self.limits.max_pair_evaluations:
            return self._append_incomplete_reassessment(context, generation, affected, pair_specs, newly_visible)
        new_assessments: dict[str, PairAssessment] = {}
        by_id = {item.hypothesis_id: item for item in generation.hypotheses}
        for pair_id in sorted(affected):
            group_id, left_id, right_id = pair_specs[pair_id]
            contract = self._contract_for_pair(contract_index, (left_id, right_id), generation.policy.identity.policy_sha256, group_id)
            previous = generation.assessments_by_pair.get(pair_id)
            new_assessments[pair_id] = self._assess_pair(
                context,
                generation,
                pair_id,
                group_id,
                by_id[left_id],
                by_id[right_id],
                contract,
                previous=previous,
                cause=ReassessmentCause.EVIDENCE_ARRIVED,
                policy_evidence=policy_context.evidence,
            )
        updated = dict(generation.assessments_by_pair)
        updated.update(new_assessments)
        termination = self._termination_for(generation, updated)
        generation = HypothesisSetState(
            generation_id=generation.generation_id,
            policy=generation.policy,
            contracts=generation.contracts,
            hypotheses=generation.hypotheses,
            pairs=generation.pairs,
            assessments_by_pair=updated,
            created_context=generation.created_context,
            latest_context=context,
            latest_termination=termination,
            invalidated=False,
        )
        self._generation = generation
        cycle = self._append_cycle(
            context,
            generation_id=generation.generation_id,
            status=termination,
            generation_state="AUTHORIZED_HYPOTHESES_REASSESSED",
            cause=ReassessmentCause.EVIDENCE_ARRIVED,
            hypothesis_ids=tuple(item.hypothesis_id for item in generation.hypotheses),
            pair_assessment_ids=tuple(item.assessment_id for item in updated.values()),
            affected_pair_ids=tuple(sorted(affected)),
            unaffected_pair_ids=tuple(sorted(set(pair_specs) - affected)),
            total_pairs=len(pair_specs),
            evaluated_pairs=len(affected),
            unexamined_pairs=0,
            coverage_state="COMPLETE_FOR_AFFECTED_PAIRS",
            details={"new_visible_evidence_ids": sorted(item.evidence_id for item in newly_visible), "old_assessments_rewritten": False},
        )
        return ResolutionResult(cycle, generation.hypotheses, tuple(new_assessments.values()), tuple(self.ledger.records[-len(new_assessments) - 1:]), tuple(self.ledger.events[-len(new_assessments) - 1:]))

    def _new_generation(
        self,
        context: VerifiedAsOfContext,
        *,
        policy: AuthorizedHypothesisPolicy | None,
        discriminators: Sequence[ExactValueDiscriminatorContract],
        mode: AnalysisMode,
        cause: ReassessmentCause,
    ) -> ResolutionResult:
        start_record_count, start_event_count = len(self.ledger.records), len(self.ledger.events)
        if not _authorization_allowed(policy, mode):
            self._generation = None
            result = self._terminal_cycle(
                context,
                status=TerminationStatus.NO_AUTHORIZED_HYPOTHESES,
                generation_state="HYPOTHESIS_GENERATION_NOT_AUTHORIZED",
                cause=cause,
                details={
                    "policy_supplied": policy is not None,
                    "authorized_scope_required": AuthorizationScope.OPERATIONAL_INTERPRETATION.value if mode is AnalysisMode.OPERATIONAL else AuthorizationScope.SOFTWARE_TEST_ONLY.value,
                    "hypotheses_generated": False,
                    "authorization_is_caller_asserted_not_authenticated": True,
                },
            )
            return ResolutionResult(result.cycle, (), (), tuple(self.ledger.records[start_record_count:]), tuple(self.ledger.events[start_event_count:]))

        assert policy is not None
        if isinstance(discriminators, (str, bytes)) or not isinstance(discriminators, Sequence):
            return self._terminal_generation_error(context, policy, cause, "DISCRIMINATOR_INPUT_MUST_BE_A_FINITE_SEQUENCE", start_record_count, start_event_count)
        if len(discriminators) > self.limits.max_discriminator_contracts:
            self._generation, self._latest_context = None, context
            cycle = self._append_cycle(
                context,
                generation_id=None,
                status=TerminationStatus.INCOMPLETE_COVERAGE,
                generation_state="DISCRIMINATOR_DECLARATION_RESOURCE_LIMIT",
                cause=ReassessmentCause.RESOURCE_LIMIT_INCOMPLETE,
                hypothesis_ids=(),
                pair_assessment_ids=(),
                affected_pair_ids=(),
                unaffected_pair_ids=(),
                total_pairs=0,
                evaluated_pairs=0,
                unexamined_pairs=0,
                coverage_state="POLICY_NOT_INVOKED_DISCRIMINATOR_DECLARATIONS_NOT_TRUNCATED",
                details={
                    "provided_discriminator_contract_count": len(discriminators),
                    "max_discriminator_contracts": self.limits.max_discriminator_contracts,
                    "policy_invoked": False,
                    "contracts_truncated": False,
                },
            )
            return ResolutionResult(cycle, (), (), tuple(self.ledger.records[start_record_count:]), tuple(self.ledger.events[start_event_count:]))
        contracts = tuple(discriminators)
        if any(not isinstance(item, ExactValueDiscriminatorContract) for item in contracts):
            return self._terminal_generation_error(context, policy, cause, "INVALID_DISCRIMINATOR_DECLARATION", start_record_count, start_event_count)
        contract_index = self._contract_index(contracts)
        policy_input = _policy_view(context)
        try:
            raw = policy.producer.generate(policy_input)
            if not isinstance(raw, Iterable):
                raise HypothesisResolutionError("authorized policy must return an iterable of HypothesisDraft")
            drafts: list[HypothesisDraft] = []
            iterator = iter(raw)
            for _ in range(self.limits.max_policy_outputs + 1):
                try:
                    item = next(iterator)
                except StopIteration:
                    break
                if len(drafts) >= self.limits.max_policy_outputs:
                    self._latest_context = context
                    cycle = self._terminal_cycle(
                        context,
                        status=TerminationStatus.INCOMPLETE_COVERAGE,
                        generation_state="PARTIAL_POLICY_OUTPUT_RESOURCE_LIMIT",
                        cause=cause,
                        details={"policy_outputs_observed_at_least": len(drafts) + 1, "max_policy_outputs": self.limits.max_policy_outputs, "hypotheses_pruned": False},
                    )
                    return ResolutionResult(cycle.cycle, (), (), tuple(self.ledger.records[start_record_count:]), tuple(self.ledger.events[start_event_count:]))
                if not isinstance(item, HypothesisDraft):
                    raise HypothesisResolutionError("policy output contains a non-HypothesisDraft value")
                drafts.append(item)
            self._validate_drafts(drafts, context)
        except Exception as exc:
            self._latest_context = context
            return self._terminal_generation_error(context, policy, cause, f"POLICY_OUTPUT_REJECTED:{type(exc).__name__}:{exc}", start_record_count, start_event_count)

        if not drafts:
            self._latest_context = context
            cycle = self._terminal_cycle(
                context,
                status=TerminationStatus.NO_AUTHORIZED_HYPOTHESES,
                generation_state="AUTHORIZED_POLICY_EMITTED_NO_HYPOTHESES",
                cause=cause,
                details={"policy_identity": policy.identity.payload(), "hypothesis_count": 0},
            )
            return ResolutionResult(cycle.cycle, (), (), tuple(self.ledger.records[start_record_count:]), tuple(self.ledger.events[start_event_count:]))

        groups: dict[str, list[HypothesisDraft]] = defaultdict(list)
        seen: set[str] = set()
        for draft in drafts:
            if draft.hypothesis_id in seen:
                self._latest_context = context
                return self._terminal_generation_error(context, policy, cause, "DUPLICATE_HYPOTHESIS_ID", start_record_count, start_event_count)
            seen.add(draft.hypothesis_id)
            groups[draft.alternative_group_id].append(draft)
        hypothesis_set_id = "HSET-" + _digest("CONTEXTUAL_HYPOTHESIS_SET_ID_V1", {
            "context_snapshot_id": context.snapshot_id,
            "policy_identity_sha256": policy.identity.identity_sha256,
            "hypothesis_ids": sorted(seen),
            "groups": {name: sorted(item.hypothesis_id for item in values) for name, values in sorted(groups.items())},
        })
        set_payload = {
            "hypothesis_set_id": hypothesis_set_id,
            "context_snapshot_id": context.snapshot_id,
            "as_of_key": _key_payload(context.as_of_key),
            "policy_identity": policy.identity.payload(),
            "hypothesis_ids": sorted(seen),
            "alternatives_by_group": {name: sorted(item.hypothesis_id for item in values) for name, values in sorted(groups.items())},
            "candidate_universe_complete": True,
            "policy_output_count": len(drafts),
            "policy_output_truncated": False,
            "no_probability_or_general_importance_score": True,
        }
        set_record = self._publish(
            "CONTEXTUAL_HYPOTHESIS_SET",
            HYPOTHESIS_SET_SCHEMA,
            context.as_of_key,
            set_payload,
            status="AUTHORIZED_HYPOTHESIS_SET_DECLARED",
            event_payload={"hypothesis_set_id": hypothesis_set_id, "reassessment_cause": cause.value},
        )
        alternatives_by_group = {name: tuple(sorted(item.hypothesis_id for item in values)) for name, values in groups.items()}
        hypotheses: list[HypothesisRecord] = []
        for draft in drafts:
            payload = {
                "hypothesis_id": draft.hypothesis_id,
                "hypothesis_set_id": hypothesis_set_id,
                "alternative_group_id": draft.alternative_group_id,
                "statement": draft.statement,
                "created_key": _key_payload(context.as_of_key),
                "alternative_hypothesis_ids": list(alternatives_by_group[draft.alternative_group_id]),
                "evidence_ids": list(draft.evidence_ids),
                "dependency_record_ids": list(draft.dependency_record_ids),
                "assumptions": list(draft.assumptions),
                "policy_identity": policy.identity.payload(),
                "policy_identity_sha256": policy.identity.identity_sha256,
                "context_snapshot_id": context.snapshot_id,
                "source_identity_sha256": context.source_identity_sha256,
                "source_file_sha256_provenance_only": context.source_file_sha256,
                "representation_policy_sha256s": sorted({
                    context.evidence_by_id[evidence_id].representation_policy_sha256
                    for evidence_id in draft.dependency_record_ids
                    if evidence_id in context.evidence_by_id and context.evidence_by_id[evidence_id].representation_policy_sha256 is not None
                }),
                "assertion_boundary": "POLICY_GENERATED_HYPOTHESIS_NOT_EMPIRICAL_PROOF",
                "authorization_is_caller_asserted_not_authenticated": True,
            }
            record = self._publish(
                "CONTEXTUAL_HYPOTHESIS",
                HYPOTHESIS_SCHEMA,
                context.as_of_key,
                payload,
                status="HYPOTHESIS_DECLARED_UNDER_AUTHORIZED_POLICY",
                event_payload={"hypothesis_id": draft.hypothesis_id, "alternative_group_id": draft.alternative_group_id, "hypothesis_set_id": hypothesis_set_id},
            )
            hypotheses.append(HypothesisRecord(
                hypothesis_id=draft.hypothesis_id,
                alternative_group_id=draft.alternative_group_id,
                statement=draft.statement,
                created_key=context.as_of_key,
                alternative_hypothesis_ids=alternatives_by_group[draft.alternative_group_id],
                evidence_ids=draft.evidence_ids,
                dependency_record_ids=draft.dependency_record_ids,
                assumptions=draft.assumptions,
                policy_identity=_freeze(policy.identity.payload()),
                context_snapshot_id=context.snapshot_id,
                source_identity_sha256=context.source_identity_sha256,
                source_file_sha256=context.source_file_sha256,
                representation_policy_sha256s=tuple(payload["representation_policy_sha256s"]),
                record=record,
            ))

        total_pairs = sum(len(items) * (len(items) - 1) // 2 for items in groups.values())
        if total_pairs > self.limits.max_pair_evaluations:
            cycle = self._append_cycle(
                context,
                generation_id=hypothesis_set_id,
                status=TerminationStatus.INCOMPLETE_COVERAGE,
                generation_state="AUTHORIZED_HYPOTHESES_GENERATED_PAIR_BUDGET_EXCEEDED",
                cause=cause,
                hypothesis_ids=tuple(item.hypothesis_id for item in hypotheses),
                pair_assessment_ids=(),
                affected_pair_ids=(),
                unaffected_pair_ids=(),
                total_pairs=total_pairs,
                evaluated_pairs=0,
                unexamined_pairs=total_pairs,
                coverage_state="PARTIAL_PAIR_EVALUATION_BUDGET",
                details={"hypothesis_count": len(hypotheses), "pair_budget": self.limits.max_pair_evaluations, "hypotheses_pruned": False, "pair_ids_omitted_to_bound_output": True},
            )
            state = HypothesisSetState(hypothesis_set_id, policy, contracts, tuple(hypotheses), (), {}, context, context, TerminationStatus.INCOMPLETE_COVERAGE, False)
            self._generation, self._latest_context = state, context
            return ResolutionResult(cycle, tuple(hypotheses), (), tuple(self.ledger.records[start_record_count:]), tuple(self.ledger.events[start_event_count:]))

        pairs: list[tuple[str, str, str, str]] = []
        for group_id, items in sorted(groups.items()):
            ids = sorted(item.hypothesis_id for item in items)
            for left, right in combinations(ids, 2):
                pair_id, _ = _pair_identity(group_id, left, right)
                pairs.append((pair_id, group_id, left, right))

        pair_contracts = {
            pair_id: self._contract_for_pair(contract_index, (left_id, right_id), policy.identity.policy_sha256, group_id)
            for pair_id, group_id, left_id, right_id in pairs
        }
        contracted_pair_count = sum(contract is not None for contract in pair_contracts.values())
        required_evidence_checks = contracted_pair_count * len(policy_input.evidence)
        by_id = {item.hypothesis_id: item for item in hypotheses}
        assessments: dict[str, PairAssessment] = {}
        if required_evidence_checks > self.limits.max_discriminator_evidence_checks:
            for pair_id, group_id, left_id, right_id in pairs:
                contract = pair_contracts[pair_id]
                if contract is not None:
                    continue
                assessments[pair_id] = self._assess_pair(
                    context,
                    HypothesisSetState(hypothesis_set_id, policy, contracts, tuple(hypotheses), tuple(pairs), {}, context, context, TerminationStatus.INCOMPLETE_COVERAGE, False),
                    pair_id,
                    group_id,
                    by_id[left_id],
                    by_id[right_id],
                    None,
                    previous=None,
                    cause=cause,
                    policy_evidence=policy_input.evidence,
                )
            state = HypothesisSetState(
                hypothesis_set_id,
                policy,
                contracts,
                tuple(hypotheses),
                tuple(pairs),
                assessments,
                context,
                context,
                TerminationStatus.INCOMPLETE_COVERAGE,
                False,
            )
            self._generation, self._latest_context = state, context
            cycle = self._append_cycle(
                context,
                generation_id=hypothesis_set_id,
                status=TerminationStatus.INCOMPLETE_COVERAGE,
                generation_state="AUTHORIZED_HYPOTHESES_GENERATED_EVIDENCE_SCAN_BUDGET_EXCEEDED",
                cause=cause,
                hypothesis_ids=tuple(item.hypothesis_id for item in hypotheses),
                pair_assessment_ids=tuple(item.assessment_id for item in assessments.values()),
                affected_pair_ids=tuple(sorted(assessments)),
                unaffected_pair_ids=(),
                total_pairs=total_pairs,
                evaluated_pairs=len(assessments),
                unexamined_pairs=total_pairs - len(assessments),
                coverage_state="PARTIAL_DISCRIMINATOR_EVIDENCE_SCAN_BUDGET",
                details={
                    "estimated_evidence_checks": required_evidence_checks,
                    "max_discriminator_evidence_checks": self.limits.max_discriminator_evidence_checks,
                    "contracted_pair_count": contracted_pair_count,
                    "unexamined_pair_count": total_pairs - len(assessments),
                    "hypotheses_pruned": False,
                    "pair_ids_pruned": False,
                },
            )
            return ResolutionResult(cycle, tuple(hypotheses), tuple(assessments.values()), tuple(self.ledger.records[start_record_count:]), tuple(self.ledger.events[start_event_count:]))

        for pair_id, group_id, left_id, right_id in pairs:
            assessments[pair_id] = self._assess_pair(
                context,
                HypothesisSetState(hypothesis_set_id, policy, contracts, tuple(hypotheses), tuple(pairs), {}, context, context, TerminationStatus.INSUFFICIENT_EVIDENCE, False),
                pair_id,
                group_id,
                by_id[left_id],
                by_id[right_id],
                pair_contracts[pair_id],
                previous=None,
                cause=cause,
                policy_evidence=policy_input.evidence,
            )
        provisional = HypothesisSetState(
            hypothesis_set_id,
            policy,
            contracts,
            tuple(hypotheses),
            tuple(pairs),
            assessments,
            context,
            context,
            TerminationStatus.INSUFFICIENT_EVIDENCE,
            False,
        )
        termination = self._termination_for(provisional, assessments)
        state = HypothesisSetState(
            provisional.generation_id,
            provisional.policy,
            provisional.contracts,
            provisional.hypotheses,
            provisional.pairs,
            provisional.assessments_by_pair,
            provisional.created_context,
            context,
            termination,
            False,
        )
        self._generation, self._latest_context = state, context
        cycle = self._append_cycle(
            context,
            generation_id=hypothesis_set_id,
            status=termination,
            generation_state="AUTHORIZED_HYPOTHESES_GENERATED",
            cause=cause,
            hypothesis_ids=tuple(item.hypothesis_id for item in hypotheses),
            pair_assessment_ids=tuple(item.assessment_id for item in assessments.values()),
            affected_pair_ids=tuple(assessments),
            unaffected_pair_ids=(),
            total_pairs=total_pairs,
            evaluated_pairs=len(assessments),
            unexamined_pairs=0,
            coverage_state="COMPLETE_FOR_GENERATED_COMPETING_PAIRS",
            details={"hypothesis_set_record_identity": set_record.record_identity, "alternatives_preserved": True, "resolution_rule_id": policy.identity.resolution_rule_id},
        )
        added_records = tuple(self.ledger.records[start_record_count:])
        added_events = tuple(self.ledger.events[start_event_count:])
        return ResolutionResult(cycle, tuple(hypotheses), tuple(assessments.values()), added_records, added_events)

    def _validate_drafts(self, drafts: Sequence[HypothesisDraft], context: VerifiedAsOfContext) -> None:
        evidence = context.evidence_by_id
        for draft in drafts:
            for identity in set(draft.evidence_ids + draft.dependency_record_ids):
                item = evidence.get(identity)
                if item is None:
                    raise HypothesisResolutionError(f"policy cited unknown/future evidence identity: {identity}")
                if item.information_key.timeline_id != context.timeline_id or item.information_key > context.as_of_key:
                    raise HypothesisResolutionError(f"policy cited evidence beyond as-of key: {identity}")
    @staticmethod
    def _contract_index(
        contracts: Sequence[ExactValueDiscriminatorContract],
    ) -> Mapping[tuple[str, str], tuple[ExactValueDiscriminatorContract, ...]]:
        indexed: dict[tuple[str, str], list[ExactValueDiscriminatorContract]] = defaultdict(list)
        for contract in contracts:
            indexed[contract.pair_key].append(contract)
        return {pair: tuple(items) for pair, items in indexed.items()}

    def _contract_for_pair(
        self,
        contract_index: Mapping[tuple[str, str], tuple[ExactValueDiscriminatorContract, ...]],
        hypothesis_ids: tuple[str, str],
        policy_sha256: str,
        group_id: str,
    ) -> ExactValueDiscriminatorContract | None:
        pair = tuple(sorted(hypothesis_ids))
        matches = contract_index.get(pair, ())
        if len(matches) != 1:
            return None
        contract = matches[0]
        if contract.policy_sha256 != policy_sha256 or contract.alternative_group_id != group_id:
            return None
        return contract

    def _matches_requirement(
        self,
        item: ContextEvidence,
        contract: ExactValueDiscriminatorContract,
        baseline: InformationKey,
    ) -> bool:
        if item.record_type != contract.evidence_record_type:
            return False
        found, _ = _get_path(item.payload, contract.field_path)
        if not found:
            return False
        return not contract.require_evidence_after_generation or item.information_key > baseline

    def _assess_pair(
        self,
        context: VerifiedAsOfContext,
        generation: HypothesisSetState,
        pair_id: str,
        group_id: str,
        left: HypothesisRecord,
        right: HypothesisRecord,
        contract: ExactValueDiscriminatorContract | None,
        *,
        previous: PairAssessment | None,
        cause: ReassessmentCause,
        policy_evidence: Sequence[ContextEvidence] | None = None,
    ) -> PairAssessment:
        hypothesis_ids = tuple(sorted((left.hypothesis_id, right.hypothesis_id)))
        if contract is None:
            return self._make_pair_assessment(
                context, pair_id, hypothesis_ids, None,
                "DISCRIMINATOR_NOT_ESTABLISHED",
                ((hypothesis_ids[0], HypothesisDisposition.DISCRIMINATOR_NOT_ESTABLISHED.value), (hypothesis_ids[1], HypothesisDisposition.DISCRIMINATOR_NOT_ESTABLISHED.value)),
                (), None,
                {"state": "DISCRIMINATOR_NOT_ESTABLISHED", "required_contract": "caller-supplied pair-specific discriminator"},
                previous, cause,
            )
        self._validate_contract(contract, generation.policy.identity, group_id, hypothesis_ids)
        baseline = max(left.created_key, right.created_key)
        available_before = []
        visible_policy_evidence = _policy_view(context).evidence if policy_evidence is None else policy_evidence
        eligible: list[ContextEvidence] = []
        for item in visible_policy_evidence:
            if item.record_type != contract.evidence_record_type:
                continue
            found, _ = _get_path(item.payload, contract.field_path)
            if not found:
                continue
            if contract.require_evidence_after_generation and item.information_key <= baseline:
                available_before.append(item.evidence_id)
            else:
                eligible.append(item)
        if not eligible:
            return self._make_pair_assessment(
                context, pair_id, hypothesis_ids, contract,
                "UNRESOLVED_WAITING_FOR_SPECIFIC_EVIDENCE",
                ((hypothesis_ids[0], HypothesisDisposition.REMAINS_UNRESOLVED.value), (hypothesis_ids[1], HypothesisDisposition.REMAINS_UNRESOLVED.value)),
                (), None,
                {
                    "state": "FUTURE_OBSERVATION_NEEDED",
                    "required_record_type": contract.evidence_record_type,
                    "field_path": list(contract.field_path),
                    "strictly_after_key": _key_payload(baseline) if contract.require_evidence_after_generation else None,
                    "already_available_but_not_eligible_evidence_ids": sorted(available_before),
                    "future_time_or_outcome_inferred": False,
                    "selection_rule_id": contract.selection_rule_id,
                },
                previous, cause,
            )
        earliest_key = min(item.information_key for item in eligible)
        first_batch = [item for item in eligible if item.information_key == earliest_key]
        if len(first_batch) != 1:
            return self._make_pair_assessment(
                context, pair_id, hypothesis_ids, contract,
                "INSUFFICIENT_INFORMATION",
                ((hypothesis_ids[0], HypothesisDisposition.INSUFFICIENT_INFORMATION.value), (hypothesis_ids[1], HypothesisDisposition.INSUFFICIENT_INFORMATION.value)),
                tuple(sorted(item.evidence_id for item in first_batch)), None,
                {
                    "state": "AMBIGUOUS_FIRST_INFORMATION_BATCH",
                    "required_record_type": contract.evidence_record_type,
                    "field_path": list(contract.field_path),
                    "matching_record_ids": sorted(item.evidence_id for item in first_batch),
                    "same_information_batch_order_claimed": False,
                    "selection_rule_id": contract.selection_rule_id,
                },
                previous, cause,
            )
        observation = first_batch[0]
        found, value = _get_path(observation.payload, contract.field_path)
        if not found:
            raise HypothesisResolutionError("selected discriminator evidence lost its declared field")
        observed_digest = _digest("CONTEXTUAL_HYPOTHESIS_EXPECTED_VALUE_V1", value)
        matches = [hypothesis_id for hypothesis_id, expected in contract.expected_values_by_hypothesis if _digest("CONTEXTUAL_HYPOTHESIS_EXPECTED_VALUE_V1", expected) == observed_digest]
        if len(matches) != 1:
            return self._make_pair_assessment(
                context, pair_id, hypothesis_ids, contract,
                "UNRESOLVED",
                ((hypothesis_ids[0], HypothesisDisposition.REMAINS_UNRESOLVED.value), (hypothesis_ids[1], HypothesisDisposition.REMAINS_UNRESOLVED.value)),
                (observation.evidence_id,), value,
                {
                    "state": "OBSERVATION_NOT_MAPPED_TO_A_DECLARED_ALTERNATIVE",
                    "field_path": list(contract.field_path),
                    "observed_value_sha256": observed_digest,
                    "closed_world": contract.closed_world,
                },
                previous, cause,
            )
        winner = matches[0]
        loser = next(identity for identity in hypothesis_ids if identity != winner)
        dispositions = {
            winner: HypothesisDisposition.SUPPORTED_BY_DECLARED_EVIDENCE.value,
            loser: HypothesisDisposition.CONTRADICTED_BY_DECLARED_EVIDENCE.value if contract.closed_world else HypothesisDisposition.REMAINS_UNRESOLVED.value,
        }
        return self._make_pair_assessment(
            context, pair_id, hypothesis_ids, contract,
            "PAIR_RESOLVED_BY_DECLARED_EXACT_VALUE_DISCRIMINATOR" if contract.closed_world else "ONE_ALTERNATIVE_SUPPORTED_OTHER_UNRESOLVED",
            ((hypothesis_ids[0], dispositions[hypothesis_ids[0]]), (hypothesis_ids[1], dispositions[hypothesis_ids[1]])),
            (observation.evidence_id,), value,
            {
                "state": "DECLARED_OBSERVATION_MATCHED_ONE_EXPECTED_VALUE",
                "field_path": list(contract.field_path),
                "observed_value_sha256": observed_digest,
                "expected_value_sha256_by_hypothesis": {
                    identity: _digest("CONTEXTUAL_HYPOTHESIS_EXPECTED_VALUE_V1", expected)
                    for identity, expected in contract.expected_values_by_hypothesis
                },
                "closed_world": contract.closed_world,
                "contract_sha256": contract.contract_sha256,
                "support_is_not_empirical_proof": True,
            },
            previous, cause,
        )

    def _validate_contract(
        self,
        contract: ExactValueDiscriminatorContract,
        policy: PolicyIdentity,
        group_id: str,
        pair: tuple[str, str],
    ) -> None:
        if contract.pair_key != pair or contract.alternative_group_id != group_id:
            raise HypothesisResolutionError("discriminator does not bind the exact competing pair")
        if contract.policy_sha256 != policy.policy_sha256:
            raise HypothesisResolutionError("discriminator policy identity differs from hypothesis policy")
        if not contract.authorization_reference.strip():
            raise HypothesisResolutionError("discriminator authorization reference missing")
        expected = _digest("CONTEXTUAL_HYPOTHESIS_DISCRIMINATOR_CONTRACT_V1", contract._identity_payload())
        if expected != contract.contract_sha256:
            raise HypothesisResolutionError("discriminator contract identity was altered")

    def _make_pair_assessment(
        self,
        context: VerifiedAsOfContext,
        pair_id: str,
        hypothesis_ids: tuple[str, str],
        contract: ExactValueDiscriminatorContract | None,
        status: str,
        dispositions: tuple[tuple[str, str], tuple[str, str]],
        evidence_ids: tuple[str, ...],
        observed_value: Any,
        required: Mapping[str, Any],
        previous: PairAssessment | None,
        cause: ReassessmentCause,
    ) -> PairAssessment:
        assessment_sequence = sum(1 for item in self.ledger.records if item.record_type == "CONTEXTUAL_HYPOTHESIS_PAIR_ASSESSMENT")
        content = {
            "assessment_id": "",
            "pair_id": pair_id,
            "hypothesis_ids": list(hypothesis_ids),
            "discriminator_contract_id": None if contract is None else contract.contract_id,
            "discriminator_contract_sha256": None if contract is None else contract.contract_sha256,
            "pair_status": status,
            "dispositions": [{"hypothesis_id": key, "disposition": value} for key, value in dispositions],
            "evidence_ids": list(evidence_ids),
            "observed_value": _plain(observed_value),
            "required_evidence": _plain(required),
            "supersedes_assessment_id": None if previous is None else previous.assessment_id,
            "reassessment_cause": cause.value,
            "context_snapshot_id": context.snapshot_id,
            "source_identity_sha256": context.source_identity_sha256,
            "source_file_sha256_provenance_only": context.source_file_sha256,
            "as_of_key": _key_payload(context.as_of_key),
            "assessment_ordinal": assessment_sequence,
            "resolution_semantics": "CONTRACT_RELATIVE_MECHANICAL_RESULT_NOT_MARKET_TRUTH",
            "probability_relevance_score_and_empirical_proof_emitted": False,
        }
        assessment_id = "ASSESS-" + _digest("CONTEXTUAL_HYPOTHESIS_PAIR_ASSESSMENT_V1", content)
        content["assessment_id"] = assessment_id
        record = self._publish(
            "CONTEXTUAL_HYPOTHESIS_PAIR_ASSESSMENT",
            PAIR_ASSESSMENT_SCHEMA,
            context.as_of_key,
            content,
            status=status,
            event_payload={"assessment_id": assessment_id, "pair_id": pair_id, "supersedes_assessment_id": content["supersedes_assessment_id"], "reassessment_cause": cause.value},
        )
        return PairAssessment(
            pair_id=pair_id,
            assessment_id=assessment_id,
            hypothesis_ids=hypothesis_ids,
            discriminator_contract_id=None if contract is None else contract.contract_id,
            discriminator_contract_sha256=None if contract is None else contract.contract_sha256,
            pair_status=status,
            dispositions=dispositions,
            evidence_ids=evidence_ids,
            observed_value=_plain(observed_value),
            required_evidence=_freeze(required),
            supersedes_assessment_id=content["supersedes_assessment_id"],
            reassessment_cause=cause.value,
            record=record,
        )

    def _termination_for(
        self,
        generation: HypothesisSetState,
        assessments: Mapping[str, PairAssessment],
    ) -> TerminationStatus:
        if generation.invalidated:
            return TerminationStatus.INVALID_FOUNDATION
        if not generation.pairs:
            return TerminationStatus.INSUFFICIENT_EVIDENCE
        if len(assessments) < len(generation.pairs):
            return TerminationStatus.INCOMPLETE_COVERAGE
        if any(item.pair_status == "UNRESOLVED_WAITING_FOR_SPECIFIC_EVIDENCE" for item in assessments.values()):
            return TerminationStatus.UNRESOLVED_WAITING_FOR_SPECIFIC_EVIDENCE
        policy = generation.policy.identity
        if policy.resolution_rule_id != SUPPORTED_RESOLUTION_RULE:
            return TerminationStatus.INSUFFICIENT_EVIDENCE
        if policy.resolution_rule_sha256 != _digest("CONTEXTUAL_HYPOTHESIS_RESOLUTION_RULE_V1", {"rule_id": SUPPORTED_RESOLUTION_RULE, "semantics": "one hypothesis supported and every declared alternative contradicted under pair-specific declared contracts"}):
            return TerminationStatus.INSUFFICIENT_EVIDENCE
        groups: dict[str, list[HypothesisRecord]] = defaultdict(list)
        for item in generation.hypotheses:
            groups[item.alternative_group_id].append(item)
        any_competing = False
        for group_id, hypotheses in groups.items():
            if len(hypotheses) < 2:
                continue
            any_competing = True
            ids = {item.hypothesis_id for item in hypotheses}
            group_assessments = [assessment for assessment in assessments.values() if set(assessment.hypothesis_ids).issubset(ids)]
            if len(group_assessments) != len(hypotheses) * (len(hypotheses) - 1) // 2:
                return TerminationStatus.INSUFFICIENT_EVIDENCE
            winners = []
            for hypothesis in hypotheses:
                dispositions = []
                for assessment in group_assessments:
                    dispositions.extend(value for identity, value in assessment.dispositions if identity == hypothesis.hypothesis_id)
                if len(dispositions) == len(hypotheses) - 1 and all(value == HypothesisDisposition.SUPPORTED_BY_DECLARED_EVIDENCE.value for value in dispositions):
                    winners.append(hypothesis.hypothesis_id)
            if len(winners) != 1:
                return TerminationStatus.INSUFFICIENT_EVIDENCE
        return TerminationStatus.RESOLVED_UNDER_DECLARED_POLICY if any_competing else TerminationStatus.INSUFFICIENT_EVIDENCE

    def _publish(
        self,
        record_type: str,
        schema: SchemaIdentity,
        key: InformationKey,
        content: Mapping[str, Any],
        *,
        status: str,
        event_payload: Mapping[str, Any],
    ) -> PublishedRecord:
        plain_content = _plain(content)
        record_id = "HREC-" + _digest("CONTEXTUAL_HYPOTHESIS_PUBLISHED_RECORD_ID_V1", {
            "record_type": record_type,
            "schema_identity": schema.as_payload(),
            "timeline_id": key.timeline_id,
            "availability_key": key,
            "content": plain_content,
            "append_ordinal": len(self.ledger.records),
        })
        record = PublishedRecord(
            record_identity=record_id,
            record_type=record_type,
            schema_identity=schema,
            timeline_id=key.timeline_id,
            availability_key=key,
            content=_freeze(plain_content),
        )
        self.ledger.append(record, status=status, event_payload=event_payload)
        return record

    def _append_cycle(
        self,
        context: VerifiedAsOfContext,
        *,
        generation_id: str | None,
        status: TerminationStatus,
        generation_state: str,
        cause: ReassessmentCause,
        hypothesis_ids: tuple[str, ...],
        pair_assessment_ids: tuple[str, ...],
        affected_pair_ids: tuple[str, ...],
        unaffected_pair_ids: tuple[str, ...],
        total_pairs: int,
        evaluated_pairs: int,
        unexamined_pairs: int,
        coverage_state: str,
        details: Mapping[str, Any],
    ) -> AnalysisCycle:
        ordinal = self._cycle_ordinal
        cycle_id = "CYCLE-" + _digest("CONTEXTUAL_HYPOTHESIS_ANALYSIS_CYCLE_ID_V1", {
            "ordinal": ordinal,
            "generation_id": generation_id,
            "context_snapshot_id": context.snapshot_id,
            "as_of_key": context.as_of_key,
            "termination_status": status.value,
            "cause": cause.value,
        })
        content = {
            "cycle_id": cycle_id,
            "cycle_ordinal": ordinal,
            "generation_id": generation_id,
            "context_snapshot_id": context.snapshot_id,
            "as_of_key": _key_payload(context.as_of_key),
            "termination_status": status.value,
            "hypothesis_generation_state": generation_state,
            "reassessment_cause": cause.value,
            "hypothesis_ids": list(hypothesis_ids),
            "pair_assessment_ids": list(pair_assessment_ids),
            "affected_pair_ids": list(affected_pair_ids),
            "unaffected_pair_ids": list(unaffected_pair_ids),
            "total_competing_pairs": total_pairs,
            "evaluated_pair_count": evaluated_pairs,
            "unexamined_pair_count": unexamined_pairs,
            "coverage_state": coverage_state,
            "details": _plain(details),
            "source_identity_sha256": context.source_identity_sha256,
            "source_file_sha256_provenance_only": context.source_file_sha256,
            "prefix_chain_sha256": context.prefix_chain_sha256,
            "mechanical_resolution_is_not_market_truth": True,
            "probability_relevance_score_and_recommendation_emitted": False,
        }
        record = self._publish(
            "CONTEXTUAL_HYPOTHESIS_ANALYSIS_CYCLE",
            ANALYSIS_CYCLE_SCHEMA,
            context.as_of_key,
            content,
            status=status.value,
            event_payload={"cycle_id": cycle_id, "termination_status": status.value, "reassessment_cause": cause.value, "coverage_state": coverage_state},
        )
        cycle = AnalysisCycle(
            cycle_id=cycle_id,
            cycle_ordinal=ordinal,
            generation_id=generation_id,
            context_snapshot_id=context.snapshot_id,
            as_of_key=context.as_of_key,
            termination_status=status,
            hypothesis_generation_state=generation_state,
            reassessment_cause=cause.value,
            hypothesis_ids=hypothesis_ids,
            pair_assessment_ids=pair_assessment_ids,
            affected_pair_ids=affected_pair_ids,
            unaffected_pair_ids=unaffected_pair_ids,
            total_competing_pairs=total_pairs,
            evaluated_pair_count=evaluated_pairs,
            unexamined_pair_count=unexamined_pairs,
            coverage_state=coverage_state,
            details=_freeze(details),
            record=record,
        )
        self._latest_cycle = cycle
        self._cycle_ordinal += 1
        return cycle

    def _terminal_cycle(
        self,
        context: VerifiedAsOfContext,
        *,
        status: TerminationStatus,
        generation_state: str,
        cause: ReassessmentCause,
        details: Mapping[str, Any],
    ) -> ResolutionResult:
        cycle = self._append_cycle(
            context,
            generation_id=None if self._generation is None else self._generation.generation_id,
            status=status,
            generation_state=generation_state,
            cause=cause,
            hypothesis_ids=() if self._generation is None else tuple(item.hypothesis_id for item in self._generation.hypotheses),
            pair_assessment_ids=() if self._generation is None else tuple(item.assessment_id for item in self._generation.assessments_by_pair.values()),
            affected_pair_ids=(),
            unaffected_pair_ids=(),
            total_pairs=0 if self._generation is None else len(self._generation.pairs),
            evaluated_pairs=0,
            unexamined_pairs=0,
            coverage_state="TERMINAL_NO_NEW_ASSESSMENTS",
            details=details,
        )
        return ResolutionResult(cycle, () if self._generation is None else self._generation.hypotheses, (), tuple(self.ledger.records[-1:]), tuple(self.ledger.events[-1:]))

    def _terminal_generation_error(
        self,
        context: VerifiedAsOfContext,
        policy: AuthorizedHypothesisPolicy,
        cause: ReassessmentCause,
        diagnostic: str,
        start_record_count: int,
        start_event_count: int,
    ) -> ResolutionResult:
        self._latest_context = context
        cycle = self._append_cycle(
            context,
            generation_id=None,
            status=TerminationStatus.INVALID_FOUNDATION,
            generation_state="AUTHORIZED_POLICY_OUTPUT_REJECTED",
            cause=cause,
            hypothesis_ids=(),
            pair_assessment_ids=(),
            affected_pair_ids=(),
            unaffected_pair_ids=(),
            total_pairs=0,
            evaluated_pairs=0,
            unexamined_pairs=0,
            coverage_state="POLICY_OUTPUT_REJECTED_NO_HYPOTHESES_ADMITTED",
            details={"diagnostic": diagnostic, "policy_identity": policy.identity.payload(), "no_partial_hypothesis_set_admitted": True},
        )
        return ResolutionResult(cycle, (), (), tuple(self.ledger.records[start_record_count:]), tuple(self.ledger.events[start_event_count:]))

    def _invalidate_foundation(
        self,
        context: VerifiedAsOfContext,
        cause: ReassessmentCause,
        diagnostic: str,
    ) -> ResolutionResult:
        generation = self._generation
        if generation is None:
            self._latest_context = context
            return self._terminal_cycle(
                context,
                status=TerminationStatus.INVALID_FOUNDATION,
                generation_state="INVALID_FOUNDATION_NO_ACTIVE_GENERATION",
                cause=cause,
                details={"diagnostic": diagnostic},
            )
        before_records, before_events = len(self.ledger.records), len(self.ledger.events)
        invalidated: dict[str, PairAssessment] = {}
        for pair_id, group_id, left_id, right_id in generation.pairs:
            previous = generation.assessments_by_pair.get(pair_id)
            ids = tuple(sorted((left_id, right_id)))
            invalidated[pair_id] = self._make_pair_assessment(
                context,
                pair_id,
                ids,
                None,
                "INVALID_FOUNDATION",
                ((ids[0], HypothesisDisposition.INVALIDATED_BY_FOUNDATION_CHANGE.value), (ids[1], HypothesisDisposition.INVALIDATED_BY_FOUNDATION_CHANGE.value)),
                (), None,
                {"state": "INVALIDATED_BY_FOUNDATIONAL_CHANGE", "diagnostic": diagnostic, "cause": cause.value},
                previous,
                cause,
            )
        self._generation = HypothesisSetState(
            generation.generation_id,
            generation.policy,
            generation.contracts,
            generation.hypotheses,
            generation.pairs,
            {**generation.assessments_by_pair, **invalidated},
            generation.created_context,
            context,
            TerminationStatus.INVALID_FOUNDATION,
            True,
        )
        self._latest_context = context
        cycle = self._append_cycle(
            context,
            generation_id=generation.generation_id,
            status=TerminationStatus.INVALID_FOUNDATION,
            generation_state="PRIOR_HYPOTHESES_INVALIDATED_NO_REWRITE",
            cause=cause,
            hypothesis_ids=tuple(item.hypothesis_id for item in generation.hypotheses),
            pair_assessment_ids=tuple(item.assessment_id for item in invalidated.values()),
            affected_pair_ids=tuple(sorted(invalidated)),
            unaffected_pair_ids=(),
            total_pairs=len(generation.pairs),
            evaluated_pairs=len(invalidated),
            unexamined_pairs=0,
            coverage_state="FOUNDATION_CHANGED; PRIOR_ASSESSMENTS_PRESERVED_AND_INVALIDATED_BY_NEW_RECORDS",
            details={"diagnostic": diagnostic, "previous_context_snapshot_id": generation.latest_context.snapshot_id, "new_context_snapshot_id": context.snapshot_id, "old_assessments_rewritten": False},
        )
        return ResolutionResult(cycle, generation.hypotheses, tuple(invalidated.values()), tuple(self.ledger.records[before_records:]), tuple(self.ledger.events[before_events:]))

    def _append_resource_limited_reassessment(
        self,
        context: VerifiedAsOfContext,
        generation: HypothesisSetState,
        pair_specs: Mapping[str, tuple[str, str, str]],
        *,
        potentially_affected: Sequence[str],
        known_affected: Sequence[str],
        estimated_checks: int,
        newly_visible: Sequence[ContextEvidence],
        affected_set_unknown: bool,
    ) -> ResolutionResult:
        self._latest_context = context
        self._generation = HypothesisSetState(
            generation.generation_id,
            generation.policy,
            generation.contracts,
            generation.hypotheses,
            generation.pairs,
            generation.assessments_by_pair,
            generation.created_context,
            context,
            TerminationStatus.INCOMPLETE_COVERAGE,
            False,
        )
        affected = () if affected_set_unknown else tuple(sorted(set(known_affected)))
        unaffected = () if affected_set_unknown else tuple(sorted(set(pair_specs) - set(affected)))
        unexamined = len(potentially_affected) if affected_set_unknown else len(affected)
        cycle = self._append_cycle(
            context,
            generation_id=generation.generation_id,
            status=TerminationStatus.INCOMPLETE_COVERAGE,
            generation_state="AUTHORIZED_HYPOTHESES_RETAINED_EVIDENCE_SCAN_BUDGET_EXCEEDED",
            cause=ReassessmentCause.RESOURCE_LIMIT_INCOMPLETE,
            hypothesis_ids=tuple(item.hypothesis_id for item in generation.hypotheses),
            pair_assessment_ids=tuple(item.assessment_id for item in generation.assessments_by_pair.values()),
            affected_pair_ids=affected,
            unaffected_pair_ids=unaffected,
            total_pairs=len(pair_specs),
            evaluated_pairs=0,
            unexamined_pairs=unexamined,
            coverage_state="PARTIAL_DISCRIMINATOR_EVIDENCE_SCAN_BUDGET",
            details={
                "estimated_evidence_checks": estimated_checks,
                "max_discriminator_evidence_checks": self.limits.max_discriminator_evidence_checks,
                "potentially_affected_pair_ids": sorted(potentially_affected),
                "affected_set_unknown": affected_set_unknown,
                "new_visible_evidence_ids": sorted(item.evidence_id for item in newly_visible),
                "prior_assessments_rewritten": False,
            },
        )
        return ResolutionResult(cycle, generation.hypotheses, (), tuple(self.ledger.records[-1:]), tuple(self.ledger.events[-1:]))

    def _append_incomplete_reassessment(
        self,
        context: VerifiedAsOfContext,
        generation: HypothesisSetState,
        affected: set[str],
        pair_specs: Mapping[str, tuple[str, str, str]],
        newly_visible: Sequence[ContextEvidence],
    ) -> ResolutionResult:
        self._latest_context = context
        cycle = self._append_cycle(
            context,
            generation_id=generation.generation_id,
            status=TerminationStatus.INCOMPLETE_COVERAGE,
            generation_state="AUTHORIZED_HYPOTHESES_RETAINED_PAIR_BUDGET_EXCEEDED",
            cause=ReassessmentCause.EVIDENCE_ARRIVED,
            hypothesis_ids=tuple(item.hypothesis_id for item in generation.hypotheses),
            pair_assessment_ids=tuple(item.assessment_id for item in generation.assessments_by_pair.values()),
            affected_pair_ids=tuple(sorted(affected)),
            unaffected_pair_ids=tuple(sorted(set(pair_specs) - affected)),
            total_pairs=len(pair_specs),
            evaluated_pairs=0,
            unexamined_pairs=len(affected),
            coverage_state="PARTIAL_PAIR_REASSESSMENT_BUDGET; NO_AFFECTED_PAIR_DROPPED",
            details={"max_pair_evaluations": self.limits.max_pair_evaluations, "new_visible_evidence_ids": sorted(item.evidence_id for item in newly_visible), "affected_pair_count": len(affected)},
        )
        return ResolutionResult(cycle, generation.hypotheses, (), tuple(self.ledger.records[-1:]), tuple(self.ledger.events[-1:]))


def verify_and_analyze(
    replay: ReplayMemoryResult,
    as_of_key: InformationKey,
    *,
    policy: AuthorizedHypothesisPolicy | None = None,
    discriminators: Sequence[ExactValueDiscriminatorContract] | None = None,
    mode: AnalysisMode = AnalysisMode.OPERATIONAL,
    limits: ResolutionLimits = ResolutionLimits(),
    session: HypothesisResolutionSession | None = None,
) -> tuple[VerifiedAsOfContext, HypothesisResolutionSession, ResolutionResult]:
    """Convenience entry point from causal-core memory replay to a cycle."""
    active = HypothesisResolutionSession(limits=limits) if session is None else session
    context = verify_asof_context(replay, as_of_key, limits=active.limits)
    result = active.reassess(context, policy=policy, discriminators=discriminators, mode=mode)
    return context, active, result


SUPPORTED_RESOLUTION_RULE_SHA256 = _digest(
    "CONTEXTUAL_HYPOTHESIS_RESOLUTION_RULE_V1",
    {
        "rule_id": SUPPORTED_RESOLUTION_RULE,
        "semantics": "one hypothesis supported and every declared alternative contradicted under pair-specific declared contracts",
    },
)


def supported_resolution_rule_identity() -> tuple[str, str]:
    """Return the only currently implemented, explicitly declarable rule."""
    return SUPPORTED_RESOLUTION_RULE, SUPPORTED_RESOLUTION_RULE_SHA256


__all__ = [
    "AnalysisCycle",
    "AnalysisMode",
    "AuthorizationScope",
    "AuthorizedHypothesisPolicy",
    "ContextEvidence",
    "ExactValueDiscriminatorContract",
    "HypothesisDisposition",
    "HypothesisDraft",
    "HypothesisResolutionError",
    "HypothesisResolutionLedger",
    "HypothesisResolutionSession",
    "HypothesisRecord",
    "PairAssessment",
    "PolicyIdentity",
    "PolicyInput",
    "PolicyRepresentationIdentity",
    "ReassessmentCause",
    "RepresentationPolicyIdentity",
    "ResolutionLimits",
    "ResolutionResult",
    "TerminationStatus",
    "VerifiedAsOfContext",
    "SUPPORTED_RESOLUTION_RULE",
    "SUPPORTED_RESOLUTION_RULE_SHA256",
    "supported_resolution_rule_identity",
    "verify_and_analyze",
    "verify_asof_context",
]
