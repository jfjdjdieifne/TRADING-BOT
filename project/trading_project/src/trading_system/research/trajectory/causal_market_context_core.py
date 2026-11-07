"""Causal Market Understanding Core V1: integrated chronological factual replay.

This additive research core composes existing source, timeline, MUF S0/S1,
Stage4A, Stage4B1/2, Stage4C-1, and trajectory outcome contracts. It does not
create a market-data truth source, swing/wave definition, universal score,
recommendation, execution path, fill, PnL, or predictive claim.

Every row is replayed at its public COMPLETED_ROW_AVAILABLE InformationKey.
Producer entities/events are registered only at their declared availability
position. Facts in the same information batch are stored as unordered sets;
serialization order is never treated as market chronology. Missing policies,
flow sources, and task authority fail closed with explicit states.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from trading_system.market_understanding.contracts import SchemaIdentity
from trading_system.market_understanding.price_path import CausalObservationStream, PublishedOhlcBarFact
from trading_system.market_understanding.records import (
    AppendOnlyEventLedger,
    EventKind,
    EventRecord,
    PublishedRecord,
    freeze_payload,
)
from trading_system.orderflow.absorption import CausalAbsorptionEvidenceEngine
from trading_system.orderflow.volume_delta import CausalVolumeDeltaEngine, OrderFlowMode
from trading_system.research.hashing import canonical_sha256
from trading_system.research.information_time import InformationKey, InformationPhase, TimeIndexedTimelineAdapter
from trading_system.research.trajectory import trajectory_stage4a as s4a
from trading_system.research.trajectory import trajectory_stage4b1 as s4b1
from trading_system.research.trajectory import trajectory_stage4b2 as s4b2
from trading_system.research.trajectory import trajectory_stage4c as s4c
from trading_system.research.trajectory.trajectory_case_adapter import create_trajectory_decision_case
from trading_system.research.trajectory.trajectory_contract import MarketObservationTimeline
from trading_system.research.trajectory.trajectory_query_views import (
    CoverageContract,
    ExcursionView,
    HorizonRequest,
    build_trajectory_window,
    decision_close_excursion_reference,
    derive_excursion_view,
)
from trading_system.sources import SourceArtifactIdentity, sha256_file
from trading_system.sources.binance_executed_flow_source import ExecutedFlowSource, build_executed_flow_source
from trading_system.sources.binance_spot_kline_ohlc_source import (
    KLINES_SCHEMA_CONTRACT,
    KlineOhlcSource,
    load_binance_spot_klines,
)
from trading_system.sources.binance_spot_minute_facts_source import (
    MinuteFactsExpectedProvenance,
    MinuteFactsProvenance,
    MinuteFactsSource,
    load_minute_facts,
)
from trading_system.structure.swing_detector import EmpiricalConfirmationPolicy

CORE_ID = "CAUSAL_MARKET_UNDERSTANDING_CORE_V1"
CORE_SCHEMA_VERSION = "CAUSAL_MARKET_CONTEXT_RECORDS_V1"
MAX_INPUT_BARS = 250_000
MAX_STRUCTURAL_REPRESENTATIONS = 4
MAX_REGISTERED_ENTITIES_HARD = 500_000
MAX_PRODUCER_EVENTS_HARD = 1_000_000
MAX_MEMORY_MODE_BARS_HARD = 20_000
LEGAL_ASOF_PHASES = frozenset({InformationPhase.COMPLETED_ROW_AVAILABLE, InformationPhase.RESEARCH_SNAPSHOT_AVAILABLE})


class CausalMarketContextCoreError(ValueError):
    """Invalid source, replay, or output contract; the core fails closed."""


def _canonical_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _canonical_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_canonical_value(item) for item in value]
    if isinstance(value, np.ndarray):
        return [_canonical_value(item) for item in value.tolist()]
    return value


def _hash(domain: str, payload: Any) -> str:
    try:
        return canonical_sha256(domain=domain, payload=_canonical_value(payload))
    except Exception as exc:
        raise CausalMarketContextCoreError(f"canonical hash failed ({domain}): {exc}") from exc


def _require_hash(value: object, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise CausalMarketContextCoreError(f"{label} must be lowercase SHA-256 hex")
    return value


def _json(value: Any) -> Any:
    if value is None or value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, InformationKey):
        return {
            "information_key_version": value.information_key_version,
            "timeline_id": value.timeline_id,
            "bar_position": int(value.bar_position),
            "event_time_utc": _json(value.event_time_utc),
            "information_phase": value.information_phase.value,
            "deterministic_sequence": int(value.deterministic_sequence),
        }
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return None
        if value.tz is None:
            raise CausalMarketContextCoreError("naive timestamps cannot be serialized")
        return value.tz_convert("UTC").isoformat().replace("+00:00", "Z")
    if isinstance(value, pd.Timedelta):
        return {"nanoseconds": int(value.value)}
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        number = float(value)
        if math.isnan(number):
            return None
        if not math.isfinite(number):
            raise CausalMarketContextCoreError("infinite facts cannot be serialized")
        return number
    if isinstance(value, str):
        return value
    if hasattr(value, "value") and isinstance(value.value, (str, int, float, bool)):
        return _json(value.value)
    if isinstance(value, Mapping):
        return {str(key): _json(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [_json(item) for item in value]
    if isinstance(value, np.ndarray):
        return [_json(item) for item in value.tolist()]
    if hasattr(value, "__dataclass_fields__"):
        return {name: _json(getattr(value, name)) for name in value.__dataclass_fields__}
    raise CausalMarketContextCoreError(f"unsupported JSON value {type(value).__name__}")


def _frozen(mapping: Mapping[str, Any]):
    try:
        return freeze_payload(_json(mapping), field_name="causal market-context record")
    except Exception as exc:
        raise CausalMarketContextCoreError(f"S0 payload freeze failed: {exc}") from exc


def _string_sequence(values: Sequence[str], label: str) -> tuple[str, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise CausalMarketContextCoreError(f"{label} must be a sequence of nonempty strings")
    result = tuple(values)
    if any(not isinstance(value, str) or not value.strip() for value in result):
        raise CausalMarketContextCoreError(f"{label} must contain only nonempty strings")
    return result


def _market_copy(frame: pd.DataFrame, label: str = "market history") -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame) or frame.empty or frame.columns.has_duplicates:
        raise CausalMarketContextCoreError(f"{label} must be a nonempty DataFrame with unique columns")
    if not isinstance(frame.index, pd.DatetimeIndex) or frame.index.tz is None:
        raise CausalMarketContextCoreError(f"{label} needs a timezone-aware DatetimeIndex")
    result = frame.copy(deep=True)
    index = result.index.tz_convert("UTC")
    try:
        index = index.as_unit("ns")
    except AttributeError:
        index = pd.DatetimeIndex(index.asi8, tz="UTC")
    result.index = index
    if result.index.hasnans or result.index.has_duplicates or not result.index.is_monotonic_increasing:
        raise CausalMarketContextCoreError(f"{label} index must be unique and increasing")
    required = ("open", "high", "low", "close")
    if any(column not in result.columns for column in required):
        raise CausalMarketContextCoreError("market history requires open/high/low/close")
    for column in required:
        series = result[column]
        if not pd.api.types.is_numeric_dtype(series) or not np.isfinite(series.to_numpy(float, na_value=np.nan)).all():
            raise CausalMarketContextCoreError(f"market column {column} must be finite real numeric")
        if (series.to_numpy(float, na_value=np.nan) <= 0).any():
            raise CausalMarketContextCoreError(f"market column {column} must be positive")
    high, low = result["high"].to_numpy(float), result["low"].to_numpy(float)
    open_, close = result["open"].to_numpy(float), result["close"].to_numpy(float)
    if (high < low).any() or ((open_ < low) | (open_ > high) | (close < low) | (close > high)).any():
        raise CausalMarketContextCoreError("market history violates OHLC geometry")
    if "volume" in result.columns:
        volume = result["volume"]
        values = volume.to_numpy(float, na_value=np.nan)
        if not pd.api.types.is_numeric_dtype(volume) or not np.isfinite(values).all() or (values < 0).any():
            raise CausalMarketContextCoreError("volume must be finite and nonnegative")
    return result


def _source_payload(identity: SourceArtifactIdentity) -> dict[str, str]:
    return {field: str(getattr(identity, field)) for field in (
        "symbol", "market_type", "interval", "period_start_utc", "period_end_utc", "timestamp_unit"
    )}


def _timed_fact_copy(frame: pd.DataFrame, label: str) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame) or frame.empty or frame.columns.has_duplicates:
        raise CausalMarketContextCoreError(f"{label} must be a nonempty DataFrame with unique columns")
    if not isinstance(frame.index, pd.DatetimeIndex) or frame.index.tz is None:
        raise CausalMarketContextCoreError(f"{label} requires a timezone-aware DatetimeIndex")
    result = frame.copy(deep=True)
    result.index = result.index.tz_convert("UTC")
    if result.index.has_duplicates or not result.index.is_monotonic_increasing:
        raise CausalMarketContextCoreError(f"{label} index must be unique and increasing")
    for column in result.columns:
        series = result[column]
        if not pd.api.types.is_numeric_dtype(series):
            continue
        values = series.to_numpy(float, na_value=np.nan)
        if np.isinf(values).any():
            raise CausalMarketContextCoreError(f"{label}.{column} contains an infinite numeric fact")
    return result


def _check_source_period(market: pd.DataFrame, identity: SourceArtifactIdentity) -> None:
    start = pd.Timestamp(identity.period_start_utc).tz_convert("UTC")
    end = pd.Timestamp(identity.period_end_utc).tz_convert("UTC")
    open_times = market.index - pd.Timedelta(minutes=1)
    if (open_times < start).any() or (open_times >= end).any():
        raise CausalMarketContextCoreError("market bars fall outside declared source open-time period")


def _row(frame: pd.DataFrame, position: int, columns: Sequence[str] | None = None) -> dict[str, Any]:
    values = frame.iloc[position] if columns is None else frame.iloc[position].loc[list(columns)]
    return {str(name): _json(value) for name, value in values.items()}


def _as_position(value: Any, name: str, *, optional: bool = False) -> int | None:
    if value is None or value is pd.NA or pd.isna(value):
        if optional:
            return None
        raise CausalMarketContextCoreError(f"{name} is missing")
    if isinstance(value, (bool, np.bool_)):
        raise CausalMarketContextCoreError(f"{name} must be an integer position")
    try:
        result = int(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise CausalMarketContextCoreError(f"{name} must be an integer position") from exc
    if result < 0 or float(value) != result:
        raise CausalMarketContextCoreError(f"{name} must be a nonnegative integer position")
    return result


def _number(value: Any, name: str) -> float:
    if value is None or value is pd.NA or pd.isna(value) or isinstance(value, (bool, np.bool_)):
        raise CausalMarketContextCoreError(f"{name} must be a finite producer value")
    result = float(value)
    if not math.isfinite(result):
        raise CausalMarketContextCoreError(f"{name} must be finite")
    return result


def _producer_bool(value: Any, name: str) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if value is None or value is pd.NA or pd.isna(value):
        return False
    raise CausalMarketContextCoreError(f"{name} must be a boolean producer fact")


def _bar_id(timeline_id: str, position: int, timestamp: pd.Timestamp, row: Mapping[str, Any]) -> str:
    return "BAR-" + _hash("CAUSAL_MARKET_CONTEXT_BAR_FACT_V1", {
        "timeline_id": timeline_id, "position": position, "event_time_utc": timestamp, "row": row
    })


@dataclass(frozen=True)
class SwingPolicyConfig:
    """Explicit Stage4B1 policy; there is no core default or invented prior."""
    policy_id: str
    policy: EmpiricalConfirmationPolicy
    artifact_sha256: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.policy_id, str) or not self.policy_id.strip():
            raise CausalMarketContextCoreError("policy_id must be nonempty")
        if not isinstance(self.policy, EmpiricalConfirmationPolicy):
            raise CausalMarketContextCoreError("EmpiricalConfirmationPolicy must be supplied explicitly")
        if self.artifact_sha256 is not None:
            _require_hash(self.artifact_sha256, "policy artifact hash")

    def payload(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "policy_version": "MODULE_2_1A_V1_1",
            "quantile": float(self.policy.quantile),
            "prior_continuation_reversals": list(self.policy.prior_continuation_reversals),
            "prior_confirmed_reversals": list(self.policy.prior_confirmed_reversals),
            "artifact_sha256": self.artifact_sha256,
        }

    @property
    def identity_sha256(self) -> str:
        return _hash("CORE_EXPLICIT_SWING_POLICY_V1", self.payload())

    @property
    def representation_id(self) -> str:
        return "REP-" + _hash("CORE_STRUCTURE_REPRESENTATION_V1", {
            "policy_id": self.policy_id, "policy_sha256": self.identity_sha256
        })


@dataclass(frozen=True)
class StructuralRepresentation:
    config: SwingPolicyConfig
    structure: s4b1.Stage4B1StructureSurface
    liquidity: s4b2.Stage4B2LiquiditySurface
    order_block: s4b2.Stage4B2OrderBlockSurface
    dealing_range: s4b2.Stage4B2DealingRangeSurface


@dataclass(frozen=True)
class CoreBundle:
    market: pd.DataFrame
    timeline: MarketObservationTimeline
    adapter: TimeIndexedTimelineAdapter
    source_identity: SourceArtifactIdentity
    source_hash: str
    source_state: str
    source_semantics: str
    source_metadata: Mapping[str, Any]
    stage4a: tuple[s4a.Stage4ADomainSurface, ...]
    htf: s4c.Stage4CHtfScaleSurface
    fvg: s4b2.Stage4B2FVGSurface
    structures: tuple[StructuralRepresentation, ...]
    executed_source: ExecutedFlowSource | None
    actual_flow: pd.DataFrame | None
    actual_absorption: pd.DataFrame | None
    actual_flow_hash: str | None
    actual_absorption_hash: str | None
    actual_absorption_state: str
    provenance: Mapping[str, Any]
    coverage: tuple[Mapping[str, Any], ...]


@dataclass(frozen=True)
class ReplayLimits:
    """Hard ceilings reject a run or mark relationship coverage partial; nothing is pruned."""
    max_input_bars: int = MAX_INPUT_BARS
    max_structural_representations: int = MAX_STRUCTURAL_REPRESENTATIONS
    max_registered_entities: int = 100_000
    max_producer_events: int = 250_000
    max_memory_mode_bars: int = 10_000
    max_interval_nodes_per_query: int = 20_000
    max_spatial_relations_per_boundary: int = 128
    max_spatial_relations_total: int = 250_000

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise CausalMarketContextCoreError(f"{name} must be a nonnegative integer")
        if self.max_input_bars == 0 or self.max_input_bars > MAX_INPUT_BARS:
            raise CausalMarketContextCoreError(f"max_input_bars must be in [1,{MAX_INPUT_BARS}]")
        if self.max_structural_representations > MAX_STRUCTURAL_REPRESENTATIONS:
            raise CausalMarketContextCoreError(f"max_structural_representations exceeds hard cap {MAX_STRUCTURAL_REPRESENTATIONS}")
        if self.max_registered_entities > MAX_REGISTERED_ENTITIES_HARD:
            raise CausalMarketContextCoreError(f"max_registered_entities exceeds hard cap {MAX_REGISTERED_ENTITIES_HARD}")
        if self.max_producer_events > MAX_PRODUCER_EVENTS_HARD:
            raise CausalMarketContextCoreError(f"max_producer_events exceeds hard cap {MAX_PRODUCER_EVENTS_HARD}")
        if self.max_memory_mode_bars > MAX_MEMORY_MODE_BARS_HARD:
            raise CausalMarketContextCoreError(f"max_memory_mode_bars exceeds hard cap {MAX_MEMORY_MODE_BARS_HARD}")


@dataclass(frozen=True)
class CoreEntity:
    entity_id: str
    source_entity_id: str
    domain: str
    representation_id: str
    availability_key: InformationKey
    origin_positions: tuple[int, ...]
    low: float | None
    high: float | None
    geometry_state: str
    record: PublishedRecord

    def payload(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "source_entity_id": self.source_entity_id,
            "domain": self.domain,
            "representation_id": self.representation_id,
            "availability_key": _json(self.availability_key),
            "origin_positions": list(self.origin_positions),
            "geometry": {"low": self.low, "high": self.high, "state": self.geometry_state},
            "record_identity": self.record.record_identity,
            "schema_identity": self.record.schema_identity.as_payload(),
            "content": _json(self.record.content),
        }


@dataclass(frozen=True)
class ProducerEvent:
    event_id: str
    entity_id: str
    domain: str
    event_type: str
    key: InformationKey
    same_batch_order_unknown: bool
    record: PublishedRecord

    def payload(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "entity_id": self.entity_id,
            "domain": self.domain,
            "event_type": self.event_type,
            "information_key": _json(self.key),
            "same_information_batch_order_unknown": self.same_batch_order_unknown,
            "producer_record_identity": self.record.record_identity,
            "producer_record_type": self.record.record_type,
            "producer_schema_identity": self.record.schema_identity.as_payload(),
            "producer_record": _json(self.record.content),
        }


@dataclass(frozen=True)
class EntityRevision:
    revision_id: str
    entity_id: str
    previous_revision_id: str | None
    revision_number: int
    key: InformationKey
    event_ids: tuple[str, ...]
    event_types_at_key: tuple[str, ...]
    event_types_seen_as_set: tuple[str, ...]
    same_batch_order_unknown: bool
    record: PublishedRecord

    def payload(self) -> dict[str, Any]:
        return {
            "revision_id": self.revision_id,
            "entity_id": self.entity_id,
            "previous_revision_id": self.previous_revision_id,
            "revision_number": self.revision_number,
            "available_key": _json(self.key),
            "event_ids_at_boundary": list(self.event_ids),
            "event_types_at_boundary": list(self.event_types_at_key),
            "event_types_seen_as_set": list(self.event_types_seen_as_set),
            "same_information_batch_order_unknown": self.same_batch_order_unknown,
            "projection_semantics": "SET_OF_PRODUCER_FACTS_NO_WITHIN_BATCH_ORDER",
            "state_claim": "NO_ACTIVE_FILLED_INVALIDATED_OR_DIRECTIONAL_STATE_INFERRED",
            "immutable_record_identity": self.record.record_identity,
            "record_type": self.record.record_type,
            "schema_identity": self.record.schema_identity.as_payload(),
            "record_content": _json(self.record.content),
        }


@dataclass(frozen=True)
class Relation:
    relation_id: str
    relation_type: str
    key: InformationKey
    left_id: str
    right_id: str
    evidence_ids: tuple[str, ...]
    same_batch: bool
    facts: Mapping[str, Any]

    def payload(self) -> dict[str, Any]:
        return {
            "relation_id": self.relation_id,
            "relation_type": self.relation_type,
            "available_key": _json(self.key),
            "left_record_id": self.left_id,
            "right_record_id": self.right_id,
            "endpoint_roles_are_not_chronology": True,
            "evidence_record_ids": list(self.evidence_ids),
            "same_information_batch": self.same_batch,
            "content": _json(self.facts),
        }


@dataclass(frozen=True)
class InterpretationPolicyReference:
    policy_id: str
    policy_version: str
    policy_sha256: str
    authorization_reference: str

    def __post_init__(self) -> None:
        for name in ("policy_id", "policy_version", "authorization_reference"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise CausalMarketContextCoreError(f"{name} must be nonempty")
        _require_hash(self.policy_sha256, "interpretation policy hash")


@dataclass(frozen=True)
class InterpretationRevision:
    revision_id: str
    question_id: str
    revision_number: int
    previous_revision_id: str | None
    key: InformationKey
    status: str
    statement: str | None
    policy_reference: Mapping[str, Any] | None
    supporting_evidence_ids: tuple[str, ...]
    contradicting_evidence_ids: tuple[str, ...]
    assumptions: tuple[str, ...]
    provenance_references: tuple[str, ...]
    evidence_set_sha256: str
    record: PublishedRecord

    def payload(self) -> dict[str, Any]:
        return {
            "revision_id": self.revision_id,
            "question_id": self.question_id,
            "revision_number": self.revision_number,
            "previous_revision_id": self.previous_revision_id,
            "available_key": _json(self.key),
            "status": self.status,
            "statement": self.statement,
            "policy_reference": _json(self.policy_reference),
            "supporting_evidence_ids": list(self.supporting_evidence_ids),
            "contradicting_evidence_ids": list(self.contradicting_evidence_ids),
            "assumptions": list(self.assumptions),
            "provenance_references": list(self.provenance_references),
            "evidence_set_sha256": self.evidence_set_sha256,
            "record_identity": self.record.record_identity,
            "record_type": self.record.record_type,
            "schema_identity": self.record.schema_identity.as_payload(),
            "record_content": _json(self.record.content),
            "immutable_revision": True,
        }


@dataclass(frozen=True)
class TaskEvaluationAuthority:
    task_id: str
    task_contract_version: str
    task_contract_sha256: str
    outcome_contract_id: str
    outcome_contract_version: str
    outcome_contract_sha256: str
    validation_protocol_id: str
    validation_protocol_version: str
    validation_protocol_sha256: str
    authorization_reference: str

    def __post_init__(self) -> None:
        for name in ("task_id", "task_contract_version", "outcome_contract_id", "outcome_contract_version", "validation_protocol_id", "validation_protocol_version", "authorization_reference"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise CausalMarketContextCoreError(f"task authority {name} must be nonempty")
        for name in ("task_contract_sha256", "outcome_contract_sha256", "validation_protocol_sha256"):
            _require_hash(getattr(self, name), name)


@dataclass(frozen=True)
class TaskOutcome:
    authority: TaskEvaluationAuthority
    case_id: str
    path_id: str
    horizon_request_id: str
    coverage_contract_id: str
    excursion: ExcursionView

    def payload(self) -> dict[str, Any]:
        return {"status": "TASK_AUTHORIZED_FACTUAL_EXCURSION_VIEW_AVAILABLE", "authority": _json(self.authority), "case_id": self.case_id, "path_id": self.path_id, "horizon_request_id": self.horizon_request_id, "coverage_contract_id": self.coverage_contract_id, "excursion_view": _json(self.excursion), "authority_is_caller_asserted_not_authenticated": True, "model_score_probability_recommendation_or_execution": False}


@dataclass(frozen=True)
class ReplaySummary:
    run_id: str
    boundary_count: int
    entity_count: int
    producer_event_count: int
    state_revision_count: int
    relationship_count: int
    relationship_counts_by_type: Mapping[str, int]
    interpretation_revision_count: int
    disagreement_count: int
    candidates_by_domain_representation: Mapping[str, int]
    relationship_coverage_state: str
    prefix_chain_sha256: str | None
    output_directory: str | None
    source_validation_state: str

    def payload(self) -> dict[str, Any]:
        return _json(self)


@dataclass(frozen=True)
class EntityStateAsOf:
    entity_id: str
    key: InformationKey
    state: str
    revision: EntityRevision | None


@dataclass(frozen=True)
class ReplayMemoryResult:
    summary: ReplaySummary
    entities: tuple[CoreEntity, ...]
    events: tuple[ProducerEvent, ...]
    revisions: tuple[EntityRevision, ...]
    relationships: tuple[Relation, ...]
    boundaries: tuple[Mapping[str, Any], ...]
    relationship_coverage_rows: tuple[Mapping[str, Any], ...]
    unmapped_flow_observations: tuple[Mapping[str, Any], ...]
    interpretations: tuple[InterpretationRevision, ...]
    disagreements: tuple[Mapping[str, Any], ...]
    entity_availability: Mapping[str, InformationKey]
    run_provenance: Mapping[str, Any]
    domain_coverage: tuple[Mapping[str, Any], ...]
    evaluation_boundary: Mapping[str, Any]

    def entity_state_as_of(self, entity_id: str, key: InformationKey) -> EntityStateAsOf:
        if not isinstance(key, InformationKey) or key.information_phase not in LEGAL_ASOF_PHASES:
            raise CausalMarketContextCoreError("legal completed-row/research-snapshot key required")
        if entity_id not in self.entity_availability:
            raise CausalMarketContextCoreError("unknown entity identity")
        if key.bar_position >= len(self.boundaries):
            raise CausalMarketContextCoreError("as-of key is beyond the replayed boundary range")
        available = self.entity_availability[entity_id]
        if key.timeline_id != available.timeline_id or key < available:
            raise CausalMarketContextCoreError("entity is not visible at requested key")
        matches = [item for item in self.revisions if item.entity_id == entity_id and item.key.bar_position <= key.bar_position]
        if not matches:
            return EntityStateAsOf(entity_id, key, "REGISTERED_NO_PRODUCER_LIFECYCLE_FACTS_AS_OF_KEY", None)
        latest = max(matches, key=lambda item: item.key.bar_position)
        return EntityStateAsOf(entity_id, key, "PRODUCER_EVENT_FACT_SET_AVAILABLE", latest)


@dataclass(frozen=True)
class _Candidate:
    domain: str
    representation_id: str
    producer_contract: str
    source_entity_id: str
    available_position: int
    origins: tuple[int, ...]
    low: float
    high: float
    producer_row: Mapping[str, Any]


@dataclass
class _StateCursor:
    previous_revision_id: str | None = None
    revision_number: int = 0
    event_types_seen: tuple[str, ...] = ()


def _entity_record(bundle: CoreBundle, candidate: _Candidate) -> CoreEntity:
    if not 0 <= candidate.available_position < len(bundle.market):
        raise CausalMarketContextCoreError("candidate availability position is outside timeline")
    for origin in candidate.origins:
        if not 0 <= origin < len(bundle.market):
            raise CausalMarketContextCoreError("producer origin position is outside timeline")
        if origin > candidate.available_position:
            raise CausalMarketContextCoreError("producer entity origin cannot be later than availability")
    if candidate.low > candidate.high:
        raise CausalMarketContextCoreError("producer geometry is inverted")
    entity_id = "ENT-" + _hash("CORE_ENTITY_ID_V1", {
        "domain": candidate.domain,
        "representation_id": candidate.representation_id,
        "producer_contract": candidate.producer_contract,
        "source_entity_id": candidate.source_entity_id,
    })
    key = bundle.adapter.key_for_position(bundle.market.index, candidate.available_position, InformationPhase.COMPLETED_ROW_AVAILABLE, 0)
    content = {
        "entity_id": entity_id,
        "source_entity_id": candidate.source_entity_id,
        "domain": candidate.domain,
        "representation_id": candidate.representation_id,
        "producer_contract": candidate.producer_contract,
        "availability_position": candidate.available_position,
        "availability_semantics": "PRODUCER_DECLARED_ROW_POSITION",
        "origin_positions": list(candidate.origins),
        "origin_semantics": "PRODUCER_METADATA_REFERENCE_ONLY_NOT_HISTORICAL_FEATURE_AVAILABILITY",
        "geometry": {"low": candidate.low, "high": candidate.high, "semantics": "PRODUCER_BOUNDS_CLOSED_INTERVAL_INDEX_ONLY"},
        "producer_row": _json(candidate.producer_row),
    }
    record = PublishedRecord(
        record_identity=entity_id,
        record_type=f"CAUSAL_MARKET_ENTITY::{candidate.domain}",
        schema_identity=SchemaIdentity("CAUSAL_MARKET_ENTITY", CORE_SCHEMA_VERSION),
        timeline_id=bundle.timeline.timeline_id,
        availability_key=key,
        content=_frozen(content),
    )
    return CoreEntity(entity_id, candidate.source_entity_id, candidate.domain, candidate.representation_id, key, candidate.origins, candidate.low, candidate.high, "AVAILABLE_PRODUCER_GEOMETRY", record)


def _candidate_rows(bundle: CoreBundle) -> list[_Candidate]:
    rows: list[_Candidate] = []
    producers: list[tuple[str, object, str]] = [("FVG", bundle.fvg, "REP-STRUCTURE-INDEPENDENT-FVG")]
    for representation in bundle.structures:
        rep = representation.config.representation_id
        producers.extend([
            ("LIQUIDITY", representation.liquidity, rep),
            ("ORDER_BLOCK", representation.order_block, rep),
            ("DEALING_RANGE", representation.dealing_range, rep),
        ])
    for domain, surface, rep in producers:
        s4b2.verify_surface_integrity(surface)
        for _, series in surface.normalized_entity_frame.iterrows():
            row = {str(name): _json(value) for name, value in series.items()}
            if domain == "FVG":
                source_id = str(_json(series["fvg_id"])); available = _as_position(series["creation_position"], "FVG creation_position")
                origins = (_as_position(series["origin_position"], "FVG origin_position"),)
                low, high = _number(series["zone_low"], "FVG zone_low"), _number(series["zone_high"], "FVG zone_high")
            elif domain == "LIQUIDITY":
                source_id = str(_json(series["level_id"])); available = _as_position(series["source_confirmation_position"], "liquidity confirmation")
                origins = (_as_position(series["source_origin_position"], "liquidity origin"),)
                low = high = _number(series["immutable_level_price"], "liquidity price")
            elif domain == "ORDER_BLOCK":
                source_id = str(_json(series["zone_id"])); available = _as_position(series["creation_position"], "OB creation")
                origins = (_as_position(series["origin_position"], "OB origin"),)
                low, high = _number(series["full_zone_low"], "OB low"), _number(series["full_zone_high"], "OB high")
            else:
                source_id = str(_json(series["range_id"])); available = _as_position(series["creation_position"], "range creation")
                origins = tuple(sorted({x for x in (
                    _as_position(series["first_endpoint_origin_position"], "first endpoint origin", optional=True),
                    _as_position(series["second_endpoint_origin_position"], "second endpoint origin", optional=True),
                ) if x is not None}))
                low, high = _number(series["range_low"], "range low"), _number(series["range_high"], "range high")
            rows.append(_Candidate(domain, rep, s4b2.TRAJECTORY_STAGE4B2_CONTRACT_VERSION, source_id, int(available), tuple(int(x) for x in origins), low, high, row))
    for representation in bundle.structures:
        frame = representation.structure.frame
        columns = [column for column in frame.columns if column not in bundle.market.columns]
        for position in range(len(frame)):
            row_series = frame.iloc[position].loc[columns]
            sides = []
            if _producer_bool(row_series.get("swing_high_confirmed", False), "swing_high_confirmed"):
                sides.append("HIGH")
            if _producer_bool(row_series.get("swing_low_confirmed", False), "swing_low_confirmed"):
                sides.append("LOW")
            if not sides:
                continue
            origin = int(_as_position(row_series.get("swing_origin_position"), "swing origin"))
            available = int(_as_position(row_series.get("swing_confirmation_position"), "swing confirmation"))
            if available != position:
                raise CausalMarketContextCoreError("Stage4B1 confirmation position differs from output row")
            price = _number(row_series.get("swing_price"), "swing price")
            for side in sides:
                source_id = f"{side}:{origin}:{available}"
                row = {str(name): _json(value) for name, value in row_series.items()}
                rows.append(_Candidate("STAGE4B1_CONFIRMED_SWING", representation.config.representation_id, s4b1.TRAJECTORY_STAGE4B1_CONTRACT_VERSION, source_id, available, (origin,), price, price, row))
    return rows


def _producer_events(bundle: CoreBundle, entities: Mapping[str, CoreEntity]) -> dict[int, list[ProducerEvent]]:
    source_index: dict[tuple[str, str, str], str] = {}
    for entity in entities.values():
        source_index[(entity.domain, entity.representation_id, entity.source_entity_id)] = entity.entity_id
    result: dict[int, list[ProducerEvent]] = defaultdict(list)
    producers: list[tuple[str, object, str]] = [("FVG", bundle.fvg, "REP-STRUCTURE-INDEPENDENT-FVG")]
    for representation in bundle.structures:
        rep = representation.config.representation_id
        producers.extend([("LIQUIDITY", representation.liquidity, rep), ("ORDER_BLOCK", representation.order_block, rep)])
    for domain, surface, rep in producers:
        s4b2.verify_surface_integrity(surface)
        frame = surface.normalized_event_frame
        entity_col = {"FVG": "fvg_id", "LIQUIDITY": "level_id", "ORDER_BLOCK": "zone_id"}[domain]
        counts = Counter((str(_json(row[entity_col])), int(row["event_position"])) for _, row in frame.iterrows())
        for _, series in frame.iterrows():
            position = int(_as_position(series["event_position"], f"{domain} event position"))
            source_id = str(_json(series[entity_col]))
            entity_id = source_index.get((domain, rep, source_id))
            if entity_id is None:
                raise CausalMarketContextCoreError("producer lifecycle row has no normalized candidate")
            entity = entities[entity_id]
            if position < entity.availability_key.bar_position:
                raise CausalMarketContextCoreError("producer lifecycle event precedes entity availability")
            event_type = str(series["event_type"])
            row = {str(name): _json(value) for name, value in series.items()}
            ambiguous = _producer_bool(row.get("same_information_batch_order_unknown", False), "same_information_batch_order_unknown") or counts[(source_id, position)] > 1
            key = bundle.adapter.key_for_position(bundle.market.index, position, InformationPhase.COMPLETED_ROW_AVAILABLE, 0)
            event_id = "EVT-" + _hash("CORE_PRODUCER_EVENT_ID_V1", {"entity_id": entity_id, "key": key, "event_type": event_type, "producer_row": row})
            record = PublishedRecord(
                record_identity=event_id,
                record_type=f"CAUSAL_MARKET_PRODUCER_EVENT::{domain}",
                schema_identity=SchemaIdentity("CAUSAL_MARKET_PRODUCER_EVENT", CORE_SCHEMA_VERSION),
                timeline_id=key.timeline_id,
                availability_key=key,
                content=_frozen({"event_id": event_id, "entity_id": entity_id, "domain": domain, "event_type": event_type, "producer_row": row, "same_information_batch_order_unknown": ambiguous}),
            )
            result[position].append(ProducerEvent(event_id, entity_id, domain, event_type, key, ambiguous, record))
    for representation in bundle.structures:
        frame = representation.structure.frame
        columns = [column for column in frame.columns if column not in bundle.market.columns]
        rep = representation.config.representation_id
        for position in range(len(frame)):
            row_series = frame.iloc[position].loc[columns]
            high = _producer_bool(row_series.get("swing_high_confirmed", False), "swing_high_confirmed")
            low = _producer_bool(row_series.get("swing_low_confirmed", False), "swing_low_confirmed")
            if not high and not low:
                continue
            origin = int(_as_position(row_series.get("swing_origin_position"), "swing origin"))
            for side in (("HIGH", "LOW") if high and low else ("HIGH",) if high else ("LOW",)):
                entity_id = "ENT-" + _hash("CORE_ENTITY_ID_V1", {"domain": "STAGE4B1_CONFIRMED_SWING", "representation_id": rep, "producer_contract": s4b1.TRAJECTORY_STAGE4B1_CONTRACT_VERSION, "source_entity_id": f"{side}:{origin}:{position}"})
                if entity_id not in entities:
                    raise CausalMarketContextCoreError("Stage4B1 event has no registered swing entity")
                event_type = f"STAGE4B1_SWING_{side}_CONFIRMED"
                key = bundle.adapter.key_for_position(bundle.market.index, position, InformationPhase.COMPLETED_ROW_AVAILABLE, 0)
                row = {str(name): _json(value) for name, value in row_series.items()}
                event_id = "EVT-" + _hash("CORE_STAGE4B1_EVENT_ID_V1", {"entity_id": entity_id, "key": key, "event_type": event_type, "producer_row": row})
                record = PublishedRecord(record_identity=event_id, record_type="CAUSAL_MARKET_PRODUCER_EVENT::STAGE4B1", schema_identity=SchemaIdentity("CAUSAL_MARKET_PRODUCER_EVENT", CORE_SCHEMA_VERSION), timeline_id=key.timeline_id, availability_key=key, content=_frozen({"event_id": event_id, "entity_id": entity_id, "domain": "STAGE4B1_CONFIRMED_SWING", "event_type": event_type, "producer_row": row}))
                result[position].append(ProducerEvent(event_id, entity_id, "STAGE4B1_CONFIRMED_SWING", event_type, key, high and low, record))
    for position in result:
        result[position].sort(key=lambda item: item.event_id)
    return result


def _row_surface(representation: StructuralRepresentation, position: int, market_columns: set[str]) -> dict[str, Any]:
    columns = [column for column in representation.structure.frame.columns if column not in market_columns]
    return _row(representation.structure.frame, position, columns)


def _relation(kind: str, key: InformationKey, left: str, right: str, evidence: Sequence[str], same_batch: bool, facts: Mapping[str, Any]) -> Relation:
    ev = tuple(sorted(set(evidence)))
    ident = "REL-" + _hash("CORE_RELATIONSHIP_ID_V1", {"kind": kind, "key": key, "left": left, "right": right, "evidence": list(ev), "same_batch": same_batch, "facts": _json(facts)})
    return Relation(ident, kind, key, left, right, ev, same_batch, _frozen(facts))


# AVL interval tree with subtree bounds: O(log n) insert; visits/results are budgeted.
@dataclass
class _Node:
    entity: CoreEntity
    left: "_Node | None" = None
    right: "_Node | None" = None
    height: int = 1
    count: int = 1
    min_low: float = 0.0
    max_high: float = 0.0

    def __post_init__(self):
        self.min_low = float(self.entity.low)
        self.max_high = float(self.entity.high)


def _height(node: _Node | None) -> int:
    return 0 if node is None else node.height


def _count(node: _Node | None) -> int:
    return 0 if node is None else node.count


def _refresh(node: _Node) -> None:
    node.height = 1 + max(_height(node.left), _height(node.right))
    node.count = 1 + _count(node.left) + _count(node.right)
    node.min_low = min(float(node.entity.low), node.left.min_low if node.left else float(node.entity.low), node.right.min_low if node.right else float(node.entity.low))
    node.max_high = max(float(node.entity.high), node.left.max_high if node.left else float(node.entity.high), node.right.max_high if node.right else float(node.entity.high))


def _rot_right(root: _Node) -> _Node:
    pivot = root.left
    if pivot is None:
        return root
    root.left = pivot.right
    pivot.right = root
    _refresh(root); _refresh(pivot)
    return pivot


def _rot_left(root: _Node) -> _Node:
    pivot = root.right
    if pivot is None:
        return root
    root.right = pivot.left
    pivot.left = root
    _refresh(root); _refresh(pivot)
    return pivot


@dataclass(frozen=True)
class _Query:
    matches: tuple[CoreEntity, ...]
    eligible: int
    visited: int
    tested: int
    pruned: int
    unexamined: int
    state: str


class _IntervalIndex:
    def __init__(self):
        self.root: _Node | None = None
        self.ids: set[str] = set()

    @property
    def count(self) -> int:
        return _count(self.root)

    def insert(self, entity: CoreEntity) -> None:
        if entity.low is None or entity.high is None or entity.entity_id in self.ids:
            raise CausalMarketContextCoreError("invalid or duplicate interval entity")
        key = (float(entity.low), entity.entity_id)
        def add(node: _Node | None) -> _Node:
            if node is None:
                return _Node(entity)
            current = (float(node.entity.low), node.entity.entity_id)
            if key == current:
                raise CausalMarketContextCoreError("duplicate interval key")
            if key < current:
                node.left = add(node.left)
            else:
                node.right = add(node.right)
            _refresh(node)
            balance = _height(node.left) - _height(node.right)
            if balance > 1:
                assert node.left is not None
                if key > (float(node.left.entity.low), node.left.entity.entity_id):
                    node.left = _rot_left(node.left)
                return _rot_right(node)
            if balance < -1:
                assert node.right is not None
                if key < (float(node.right.entity.low), node.right.entity.entity_id):
                    node.right = _rot_right(node.right)
                return _rot_left(node)
            return node
        self.root = add(self.root)
        self.ids.add(entity.entity_id)

    def query(self, low: float, high: float, max_visits: int, max_results: int) -> _Query:
        eligible = self.count
        if self.root is None:
            return _Query((), 0, 0, 0, 0, 0, "COMPLETE_NO_CANDIDATES")
        stack = [self.root]
        matches: list[CoreEntity] = []
        visited = tested = pruned = 0
        state = "COMPLETE"
        while stack:
            if visited >= max_visits or len(matches) >= max_results:
                state = "PARTIAL_RESOURCE_BUDGET"
                break
            node = stack.pop(); visited += 1
            if node.max_high < low or node.min_low > high:
                pruned += node.count
                continue
            tested += 1
            if float(node.entity.low) <= high and float(node.entity.high) >= low:
                matches.append(node.entity)
            for child in (node.right, node.left):
                if child is None:
                    continue
                if child.max_high < low or child.min_low > high:
                    pruned += child.count
                else:
                    stack.append(child)
        unexamined = max(0, eligible - tested - pruned)
        if state == "COMPLETE" and unexamined:
            raise CausalMarketContextCoreError("interval index coverage accounting failed")
        matches.sort(key=lambda entity: entity.entity_id)
        return _Query(tuple(matches), eligible, visited, tested, pruned, unexamined, state)


class _Sink:
    retain = False
    def write(self, stream: str, row: Mapping[str, Any]) -> None:
        raise NotImplementedError
    def finish(self, summary: Mapping[str, Any], provenance: Mapping[str, Any], coverage: Sequence[Mapping[str, Any]], evaluation: Mapping[str, Any]) -> str | None:
        raise NotImplementedError


STREAMS = ("boundary_records", "entities", "producer_events", "entity_state_revisions", "relationships", "relationship_coverage", "interpretation_revisions", "representation_disagreements", "unmapped_flow_observations")


class MemorySink(_Sink):
    retain = True
    def __init__(self):
        self.rows: dict[str, list[Mapping[str, Any]]] = {name: [] for name in STREAMS}
        self.static: dict[str, Any] = {}
    def write(self, stream: str, row: Mapping[str, Any]) -> None:
        self.rows[stream].append(_json(row))
    def finish(self, summary, provenance, coverage, evaluation):
        self.static = {"summary": _json(summary), "run_provenance": _json(provenance), "domain_coverage": _json(coverage), "evaluation_boundary": _json(evaluation)}
        return None


class DirectorySink(_Sink):
    """JSONL append-only output; incomplete outputs carry a marker and no valid manifest."""
    def __init__(self, output_dir: str | Path):
        self.path = Path(output_dir).expanduser().resolve()
        repo = next((parent for parent in Path(__file__).resolve().parents if (parent / ".git").exists()), None)
        if repo is not None and (self.path == repo or repo in self.path.parents):
            raise CausalMarketContextCoreError("output directory must be outside the Git checkout")
        if self.path.exists() and any(self.path.iterdir()):
            raise CausalMarketContextCoreError("output directory must be new or empty")
        self.path.mkdir(parents=True, exist_ok=True)
        self.marker = self.path / "RUN_INCOMPLETE"
        self.marker.write_text("Replay incomplete; files are not a valid run.\n", encoding="utf-8")
        self.handles = {name: (self.path / f"{name}.jsonl").open("w", encoding="utf-8", newline="\n") for name in STREAMS}
        self.closed = False
    def write(self, stream: str, row: Mapping[str, Any]) -> None:
        if self.closed or stream not in self.handles:
            raise CausalMarketContextCoreError("invalid/closed output stream")
        self.handles[stream].write(json.dumps(_json(row), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
    def _json_file(self, name: str, value: Any) -> None:
        (self.path / name).write_text(json.dumps(_json(value), ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    def finish(self, summary, provenance, coverage, evaluation):
        for handle in self.handles.values():
            handle.flush(); handle.close()
        self.closed = True
        self._json_file("summary.json", summary); self._json_file("run_provenance.json", provenance)
        self._json_file("domain_coverage.json", coverage); self._json_file("evaluation_boundary.json", evaluation)
        manifest_files = []
        for path in sorted(self.path.iterdir(), key=lambda p: p.name):
            if path.is_file() and path.name not in {"hash_manifest.json", "RUN_INCOMPLETE"}:
                manifest_files.append({"path": path.name, "sha256": sha256_file(str(path)), "bytes": path.stat().st_size})
        self._json_file("hash_manifest.json", {"schema_version": "CAUSAL_MARKET_CONTEXT_OUTPUT_HASH_MANIFEST_V1", "self_hash_excluded": True, "files": manifest_files})
        self.marker.unlink(missing_ok=True)
        return str(self.path)
    def abort(self):
        for handle in self.handles.values():
            if not handle.closed:
                handle.close()


class InterpretationRevisionLedger:
    """Append-only mechanism with evidence visibility checks and no default interpretation."""
    def __init__(self, sink: _Sink, question_id: str):
        if not question_id:
            raise CausalMarketContextCoreError("question_id must be nonempty")
        self.sink, self.question_id = sink, question_id
        self.previous: str | None = None
        self.last_key: InformationKey | None = None
        self.count = 0
        self.evidence: dict[str, InformationKey] = {}
        self.retained: list[InterpretationRevision] = []
    def register_evidence(self, record_id: str, key: InformationKey) -> None:
        if not isinstance(record_id, str) or not record_id or not isinstance(key, InformationKey):
            raise CausalMarketContextCoreError("evidence id and information key required")
        old = self.evidence.get(record_id)
        if old is not None and old != key:
            raise CausalMarketContextCoreError("evidence identity rebound to another key")
        self.evidence[record_id] = key
    def append_unestablished(self, key: InformationKey, evidence_ids: Sequence[str], provenance: Sequence[str]) -> InterpretationRevision:
        if not isinstance(key, InformationKey):
            raise CausalMarketContextCoreError("interpretation InformationKey required")
        evidence = tuple(sorted(set(_string_sequence(evidence_ids, "evidence_ids"))))
        prov = tuple(sorted(set(_string_sequence(provenance, "provenance"))))
        for item in evidence:
            fact_key = self.evidence.get(item)
            if fact_key is None or fact_key.timeline_id != key.timeline_id or fact_key > key:
                raise CausalMarketContextCoreError("interpretation evidence unknown, future, or cross-timeline")
        evidence_hash = _hash("CORE_INTERPRETATION_EVIDENCE_V1", {"evidence": list(evidence), "provenance": list(prov)})
        return self._append(key, "INTERPRETATION_NOT_ESTABLISHED", None, None, (), (), (), prov, evidence_hash)
    def append_explicit(self, *, key: InformationKey, statement: str, policy: InterpretationPolicyReference, supporting: Sequence[str], contradicting: Sequence[str], assumptions: Sequence[str], provenance: Sequence[str]) -> InterpretationRevision:
        if not isinstance(key, InformationKey):
            raise CausalMarketContextCoreError("interpretation InformationKey required")
        if not isinstance(policy, InterpretationPolicyReference) or not isinstance(statement, str) or not statement.strip():
            raise CausalMarketContextCoreError("explicit interpretation requires policy and statement")
        support = tuple(sorted(set(_string_sequence(supporting, "supporting evidence"))))
        contra = tuple(sorted(set(_string_sequence(contradicting, "contradicting evidence"))))
        if not support and not contra:
            raise CausalMarketContextCoreError("explicit interpretation must cite evidence")
        for identity in support + contra:
            fact_key = self.evidence.get(identity)
            if fact_key is None or fact_key.timeline_id != key.timeline_id or fact_key > key:
                raise CausalMarketContextCoreError("future/unknown/cross-timeline interpretation evidence")
        assume = _string_sequence(assumptions, "assumptions")
        prov = tuple(sorted(set(_string_sequence(provenance, "provenance"))))
        policy_payload = {"policy_id": policy.policy_id, "policy_version": policy.policy_version, "policy_sha256": policy.policy_sha256, "authorization_reference": policy.authorization_reference, "authentication_state": "CALLER_ASSERTED_NOT_INDEPENDENTLY_AUTHENTICATED"}
        evidence_hash = _hash("CORE_INTERPRETATION_EVIDENCE_V1", {"support": list(support), "contradict": list(contra), "assumptions": list(assume), "provenance": list(prov)})
        return self._append(key, "EXPLICITLY_SUPPLIED_UNVALIDATED_INTERPRETATION", policy_payload, statement.strip(), support, contra, assume, prov, evidence_hash)
    def _append(self, key, status, policy, statement, support, contra, assumptions, provenance, evidence_hash):
        if key.information_phase not in LEGAL_ASOF_PHASES:
            raise CausalMarketContextCoreError("interpretation key must be completed-row or research-snapshot available")
        if self.last_key is not None and (key.timeline_id != self.last_key.timeline_id or not key > self.last_key):
            raise CausalMarketContextCoreError("interpretation revisions must append at strictly later keys")
        number = self.count + 1
        revision_id = "INT-" + _hash("CORE_INTERPRETATION_REVISION_V1", {"question_id": self.question_id, "number": number, "previous": self.previous, "key": key, "status": status, "policy": policy, "statement": statement, "support": list(support), "contradict": list(contra), "assumptions": list(assumptions), "provenance": list(provenance), "evidence_hash": evidence_hash})
        content = {"revision_id": revision_id, "question_id": self.question_id, "revision_number": number, "previous_revision_id": self.previous, "available_key": key, "status": status, "statement": statement, "policy_reference": policy, "supporting_evidence_ids": list(support), "contradicting_evidence_ids": list(contra), "assumptions": list(assumptions), "provenance_references": list(provenance), "evidence_set_sha256": evidence_hash}
        record = PublishedRecord(record_identity=revision_id, record_type="CAUSAL_MARKET_CONTEXT_INTERPRETATION_REVISION", schema_identity=SchemaIdentity("CAUSAL_MARKET_CONTEXT_INTERPRETATION", CORE_SCHEMA_VERSION), timeline_id=key.timeline_id, availability_key=key, content=_frozen(content))
        revision = InterpretationRevision(revision_id, self.question_id, number, self.previous, key, status, statement, None if policy is None else _frozen(policy), tuple(support), tuple(contra), tuple(assumptions), tuple(provenance), evidence_hash, record)
        self.sink.write("interpretation_revisions", revision.payload())
        if self.sink.retain:
            self.retained.append(revision)
        self.previous, self.last_key, self.count = revision_id, key, number
        return revision


@dataclass(frozen=True)
class _Coverage:
    bar_query: Mapping[str, Any]
    entity_queries: tuple[Mapping[str, Any], ...]
    pair_count: int
    pair_checked: int
    pair_unexamined: int
    emitted: int
    global_state: str


class _Replay:
    def __init__(self, bundle: CoreBundle, sink: _Sink, limits: ReplayLimits):
        self.bundle, self.sink, self.limits = bundle, sink, limits
        self.ledger = AppendOnlyEventLedger()
        self.tree = _IntervalIndex()
        self.entities: dict[str, CoreEntity] = {}
        self.availability: dict[str, InformationKey] = {}
        self.state: dict[str, _StateCursor] = {}
        self.relation_count = 0
        self.relation_counts = Counter()
        self.spatial_count = 0
        self.global_partial = False
        self.any_spatial_partial = False
        self.state_revision_total = 0
        self.current_relation_ids: list[str] = []
        self.mem_entities: list[CoreEntity] = []; self.mem_events: list[ProducerEvent] = []
        self.mem_revisions: list[EntityRevision] = []; self.mem_relations: list[Relation] = []
        self.mem_boundaries: list[Mapping[str, Any]] = []; self.mem_coverage: list[Mapping[str, Any]] = []
        self.mem_unmapped_flow: list[Mapping[str, Any]] = []; self.mem_disagreements: list[Mapping[str, Any]] = []
        self.disagreement_count = 0
        self.interpretation = InterpretationRevisionLedger(sink, "MARKET_CONTEXT_INTERPRETATION")
    def _emit_relation(self, relation: Relation) -> None:
        self.sink.write("relationships", relation.payload())
        self.interpretation.register_evidence(relation.relation_id, relation.key)
        self.relation_count += 1; self.relation_counts[relation.relation_type] += 1
        if relation.relation_type in {"ENTITY_GEOMETRY_OVERLAP", "PRICE_BAR_RANGE_OVERLAPS_PREVIOUSLY_AVAILABLE_ENTITY_GEOMETRY"}:
            self.spatial_count += 1
        self.current_relation_ids.append(relation.relation_id)
        if self.sink.retain:
            self.mem_relations.append(relation)
    def _register_entity_links(self, entity: CoreEntity, bar_id: str, key: InformationKey) -> None:
        link = _relation("PRODUCER_ENTITY_AVAILABLE_AT_OBSERVED_BAR", key, entity.entity_id, bar_id, (entity.record.record_identity, bar_id), True, {"availability_position": key.bar_position, "no_intrabar_order_claim": True})
        self._emit_relation(link)
        for origin in entity.origin_positions:
            ref = _bar_id(self.bundle.timeline.timeline_id, origin, self.bundle.market.index[origin], _row(self.bundle.market, origin))
            self._emit_relation(_relation("PRODUCER_ENTITY_REFERENCES_ORIGIN_POSITION", key, entity.entity_id, ref, (entity.record.record_identity, ref), origin == key.bar_position, {"producer_origin_position": origin, "entity_availability_position": key.bar_position, "semantics": "PRODUCER_METADATA_REFERENCE_ONLY_NOT_HISTORICAL_FEATURE_AVAILABILITY"}))
    def _entity_event_link(self, event: ProducerEvent, key: InformationKey) -> None:
        entity = self.entities[event.entity_id]
        self._emit_relation(_relation("PRODUCER_LIFECYCLE_EVENT_REFERENCES_ENTITY", key, event.event_id, entity.entity_id, (event.record.record_identity, entity.record.record_identity), event.key.bar_position == entity.availability_key.bar_position, {"producer_event_type": event.event_type, "same_information_batch_order_unknown": event.same_batch_order_unknown, "semantics": "DIRECT_PRODUCER_ID_REFERENCE_NO_CAUSAL_OR_INTENT_CLAIM"}))
    def _spatial(self, position: int, key: InformationKey, new_entities: Sequence[CoreEntity], bar_id: str) -> _Coverage:
        before = self.tree.count; rel_before = self.spatial_count
        per_boundary_limit = self.limits.max_spatial_relations_per_boundary
        global_left = max(0, self.limits.max_spatial_relations_total - self.spatial_count)
        cap = min(per_boundary_limit, global_left)
        geom_new = [item for item in new_entities if item.low is not None]
        pair_count = len(geom_new) * (len(geom_new) - 1) // 2
        if cap <= 0 or self.global_partial:
            skipped = before > 0 or pair_count > 0
            if global_left == 0 and skipped:
                self.global_partial = True
            self.any_spatial_partial = self.any_spatial_partial or skipped
            bar_q = {"state": "SKIPPED_RELATIONSHIP_BUDGET", "eligible": before, "unexamined": before, "visited": 0}
            entity_q = tuple({"entity_id": item.entity_id, "state": "SKIPPED_RELATIONSHIP_BUDGET", "eligible": before, "unexamined": before, "visited": 0} for item in geom_new)
            state = "PARTIAL_GLOBAL_LIMIT" if skipped and global_left == 0 else "PARTIAL_QUERY_OR_BOUNDARY_LIMIT" if skipped else "COMPLETE_NO_CURRENT_SPATIAL_WORK"
            return _Coverage(bar_q, entity_q, pair_count, 0, pair_count, 0, state)
        bar = self.bundle.market.iloc[position]
        query = self.tree.query(float(bar["low"]), float(bar["high"]), self.limits.max_interval_nodes_per_query, cap)
        bar_q = {"state": query.state, "eligible": query.eligible, "visited": query.visited, "tested": query.tested, "proven_nonoverlap": query.pruned, "unexamined": query.unexamined, "bar_range": {"low": float(bar["low"]), "high": float(bar["high"])}}
        for entity in query.matches:
            if self.spatial_count - rel_before >= per_boundary_limit or self.spatial_count >= self.limits.max_spatial_relations_total:
                break
            facts = {"entity_available_position": entity.availability_key.bar_position, "later_observed_bar_position": position, "entity_geometry": {"low": entity.low, "high": entity.high}, "bar_range": {"low": float(bar["low"]), "high": float(bar["high"])}, "intersection": {"low": max(float(entity.low), float(bar["low"])), "high": min(float(entity.high), float(bar["high"]))}, "claim": "LATER_BAR_RANGE_OVERLAPS_PREVIOUSLY_AVAILABLE_GEOMETRY; NO_INTRABAR_TOUCH_ORDER"}
            self._emit_relation(_relation("PRICE_BAR_RANGE_OVERLAPS_PREVIOUSLY_AVAILABLE_ENTITY_GEOMETRY", key, entity.entity_id, bar_id, (entity.record.record_identity, bar_id), False, facts))
        entity_q = []
        for entity in geom_new:
            left = min(per_boundary_limit - (self.spatial_count - rel_before), self.limits.max_spatial_relations_total - self.spatial_count)
            if left <= 0:
                entity_q.append({"entity_id": entity.entity_id, "state": "SKIPPED_RELATIONSHIP_BUDGET", "eligible": before, "unexamined": before, "visited": 0}); continue
            result = self.tree.query(float(entity.low), float(entity.high), self.limits.max_interval_nodes_per_query, left)
            entity_q.append({"entity_id": entity.entity_id, "state": result.state, "eligible": result.eligible, "visited": result.visited, "tested": result.tested, "proven_nonoverlap": result.pruned, "unexamined": result.unexamined})
            for other in result.matches:
                if self.spatial_count - rel_before >= per_boundary_limit or self.spatial_count >= self.limits.max_spatial_relations_total:
                    break
                overlap = {"left_geometry": {"low": entity.low, "high": entity.high}, "right_geometry": {"low": other.low, "high": other.high}, "intersection": {"low": max(float(entity.low), float(other.low)), "high": min(float(entity.high), float(other.high))}, "claim": "CLOSED_INTERVAL_GEOMETRIC_OVERLAP_ONLY_NO_RELEVANCE_OR_CAUSALITY"}
                self._emit_relation(_relation("ENTITY_GEOMETRY_OVERLAP", key, entity.entity_id, other.entity_id, (entity.record.record_identity, other.record.record_identity), False, overlap))
        checked = 0
        for i, left in enumerate(geom_new):
            for right in geom_new[i + 1:]:
                if self.spatial_count - rel_before >= per_boundary_limit or self.spatial_count >= self.limits.max_spatial_relations_total:
                    break
                checked += 1
                if float(left.low) <= float(right.high) and float(right.low) <= float(left.high):
                    facts = {"left_geometry": {"low": left.low, "high": left.high}, "right_geometry": {"low": right.low, "high": right.high}, "intersection": {"low": max(float(left.low), float(right.low)), "high": min(float(left.high), float(right.high))}, "claim": "SAME_INFORMATION_BATCH_GEOMETRIC_OVERLAP; NO_CREATION_ORDER"}
                    self._emit_relation(_relation("ENTITY_GEOMETRY_OVERLAP", key, left.entity_id, right.entity_id, (left.record.record_identity, right.record.record_identity), True, facts))
            if self.spatial_count - rel_before >= per_boundary_limit or self.spatial_count >= self.limits.max_spatial_relations_total:
                break
        unexamined = max(0, pair_count - checked)
        query_unexamined = int(bar_q.get("unexamined", 0)) + sum(int(row.get("unexamined", 0)) for row in entity_q)
        partial = unexamined > 0 or query_unexamined > 0
        self.any_spatial_partial = self.any_spatial_partial or partial
        if self.spatial_count >= self.limits.max_spatial_relations_total and partial:
            self.global_partial = True
        state = "PARTIAL_GLOBAL_LIMIT" if self.global_partial else "PARTIAL_QUERY_OR_BOUNDARY_LIMIT" if partial else "COMPLETE"
        return _Coverage(bar_q, tuple(entity_q), pair_count, checked, unexamined, self.spatial_count - rel_before, state)

    def run(self) -> ReplayMemoryResult | ReplaySummary:
        bundle, limits = self.bundle, self.limits
        _verify_bundle(bundle)
        if len(bundle.market) > limits.max_input_bars:
            raise CausalMarketContextCoreError("input exceeds max_input_bars; no rows were pruned")
        if self.sink.retain and len(bundle.market) > limits.max_memory_mode_bars:
            raise CausalMarketContextCoreError("in-memory replay row cap exceeded; use an external output_dir instead of pruning")
        if len(bundle.structures) > limits.max_structural_representations:
            raise CausalMarketContextCoreError("explicit representation count exceeds limit; none were pruned")
        expected_entities, expected_events = _candidate_event_totals(bundle)
        if expected_entities > limits.max_registered_entities:
            raise CausalMarketContextCoreError("candidate entity count exceeds configured limit; none were pruned")
        if expected_events > limits.max_producer_events:
            raise CausalMarketContextCoreError("producer event count exceeds configured limit; none were pruned")
        candidates = _candidate_rows(bundle)
        if len(candidates) != expected_entities:
            raise CausalMarketContextCoreError("producer candidate preflight disagrees with normalized entity tables")
        by_position: dict[int, list[CoreEntity]] = defaultdict(list)
        for candidate in candidates:
            entity = _entity_record(bundle, candidate)
            if entity.entity_id in self.entities:
                raise CausalMarketContextCoreError("core entity identity collision")
            self.entities[entity.entity_id] = entity
            self.availability[entity.entity_id] = entity.availability_key
            by_position[entity.availability_key.bar_position].append(entity)
        events_by_position = _producer_events(bundle, self.entities)
        event_count_expected = sum(map(len, events_by_position.values()))
        if event_count_expected != expected_events:
            raise CausalMarketContextCoreError("producer event preflight disagrees with normalized event tables")
        candidate_counts = dict(sorted(Counter(f"{item.domain}:{item.representation_id}" for item in self.entities.values()).items()))
        actual_counts: Counter[str] = Counter()
        source_schema = SchemaIdentity("PUBLISHED_KLINE_OHLC" if bundle.source_state.startswith("BINANCE_") else "CALLER_SUPPLIED_OHLC", KLINES_SCHEMA_CONTRACT if bundle.source_state.startswith("BINANCE_") else "CALLER_FRAME_V1")
        dataset_id = _hash("CORE_S1_DATASET_ID_V1", {"source_identity": _source_payload(bundle.source_identity), "source_hash": bundle.source_hash, "timeline_id": bundle.timeline.timeline_id})
        observation_stream = CausalObservationStream(source_identity=source_schema, dataset_identity=dataset_id)
        prefix = _hash("CORE_ASOF_PREFIX_SEED_V1", {"core": CORE_ID, "schema": CORE_SCHEMA_VERSION, "timeline_id": bundle.timeline.timeline_id, "producer_contracts": bundle.provenance["producer_contracts"], "policy_hashes": [item.config.identity_sha256 for item in bundle.structures]})
        prefix_final = None
        state_cursors: dict[str, _StateCursor] = {}
        retained_disagreement_rows: list[Mapping[str, Any]] = []
        for position in range(len(bundle.market)):
            self.current_relation_ids = []
            key = bundle.adapter.key_for_position(bundle.market.index, position, InformationPhase.COMPLETED_ROW_AVAILABLE, 0)
            bar = bundle.market.iloc[position]
            bar_row = _row(bundle.market, position)
            bar_id = _bar_id(bundle.timeline.timeline_id, position, bundle.market.index[position], bar_row)
            bar_record = PublishedRecord(record_identity=bar_id, record_type="PUBLISHED_OHLC_OBSERVATION_FACT", schema_identity=source_schema, timeline_id=key.timeline_id, availability_key=key, content=_frozen({"ohlcv": bar_row, "source_semantics": bundle.source_semantics, "source_identity": _source_payload(bundle.source_identity), "tie_order_contract": "NOT_PROVEN", "intrabar_path_reconstructed": False}))
            self.interpretation.register_evidence(bar_id, key)
            accepted = observation_stream.accept(PublishedOhlcBarFact(float(bar["open"]), float(bar["high"]), float(bar["low"]), float(bar["close"]), key, source_schema, dataset_id, bar_id))
            s1_content = _price_path_facts(accepted)
            stage4a_rows = {surface.domain: {"contract_version": surface.contract_version, "derived_values": _row(surface.surface, position, surface.output_columns), "semantics": "OHLCV_PROXY" if surface.domain in {"ORDER_FLOW_PROXY", "ABSORPTION_PROXY"} else "EXISTING_STAGE4A_SURFACE"} for surface in bundle.stage4a}
            htf_row = _row(bundle.htf.asof_bar_frame, position)
            structural_rows = {item.config.representation_id: _row_surface(item, position, set(bundle.market.columns)) for item in bundle.structures}
            flow_content = _actual_flow_at(bundle, position)
            actual_absorption = {"state": bundle.actual_absorption_state, "values": None if bundle.actual_absorption is None else _row(bundle.actual_absorption, position)}
            current = sorted(by_position.get(position, []), key=lambda item: item.entity_id)
            for entity in current:
                self.sink.write("entities", entity.payload()); actual_counts[f"{entity.domain}:{entity.representation_id}"] += 1
                self.interpretation.register_evidence(entity.record.record_identity, key)
                if self.sink.retain:
                    self.mem_entities.append(entity)
            batch_events = events_by_position.get(position, [])
            for event in batch_events:
                self.ledger.append(EventRecord(event_identity=event.event_id, event_kind=EventKind.STATUS_EVENT, subject_record_identity=event.entity_id, event_key=key, event_payload={"status": event.event_type, "producer_domain": event.domain, "same_information_batch_order_unknown": event.same_batch_order_unknown, "producer_event_record_identity": event.record.record_identity}))
                self.sink.write("producer_events", event.payload()); self.interpretation.register_evidence(event.record.record_identity, key)
                if self.sink.retain:
                    self.mem_events.append(event)
            grouped: dict[str, list[ProducerEvent]] = defaultdict(list)
            for event in batch_events:
                grouped[event.entity_id].append(event)
            new_revisions = []
            for entity_id in sorted(grouped):
                group = grouped[entity_id]
                previous = state_cursors.get(entity_id, _StateCursor())
                types_at_key = tuple(sorted({item.event_type for item in group}))
                types_seen = tuple(sorted(set(previous.event_types_seen).union(types_at_key)))
                revision_number = previous.revision_number + 1
                event_ids = tuple(sorted(item.event_id for item in group))
                ambiguous = len(group) > 1 or any(item.same_batch_order_unknown for item in group)
                revision_id = "STATE-" + _hash("CORE_ENTITY_STATE_REVISION_V1", {"entity_id": entity_id, "previous": previous.previous_revision_id, "number": revision_number, "key": key, "event_ids": list(event_ids), "types_at_key": list(types_at_key), "types_seen": list(types_seen), "same_batch_order_unknown": ambiguous})
                content = {"revision_id": revision_id, "entity_id": entity_id, "previous_revision_id": previous.previous_revision_id, "revision_number": revision_number, "available_key": key, "event_ids_at_boundary": list(event_ids), "event_types_at_boundary": list(types_at_key), "event_types_seen_as_set": list(types_seen), "same_information_batch_order_unknown": ambiguous, "projection_semantics": "SET_OF_PRODUCER_FACTS_NO_WITHIN_BATCH_ORDER", "no_active_filled_or_invalidated_status_inferred": True}
                record = PublishedRecord(record_identity=revision_id, record_type="CAUSAL_MARKET_ENTITY_STATE_REVISION", schema_identity=SchemaIdentity("CAUSAL_MARKET_ENTITY_STATE", CORE_SCHEMA_VERSION), timeline_id=key.timeline_id, availability_key=key, content=_frozen(content))
                revision = EntityRevision(revision_id, entity_id, previous.previous_revision_id, revision_number, key, event_ids, types_at_key, types_seen, ambiguous, record)
                state_cursors[entity_id] = _StateCursor(revision_id, revision_number, types_seen)
                self.state_revision_total += 1
                new_revisions.append(revision); self.sink.write("entity_state_revisions", revision.payload())
                self.interpretation.register_evidence(revision_id, key)
                if self.sink.retain:
                    self.mem_revisions.append(revision)
            for entity in current:
                self._register_entity_links(entity, bar_id, key)
            for event in batch_events:
                self._entity_event_link(event, key)
            before_tree = self.tree.count
            coverage = self._spatial(position, key, current, bar_id)
            for entity in current:
                self.tree.insert(entity)
            # Record only factual representation differences. A row is compared
            # as a whole; no policy is selected as truth.
            disagreement_ids = []
            if len(bundle.structures) > 1:
                states = []
                for representation in bundle.structures:
                    facts = _row_surface(representation, position, set(bundle.market.columns))
                    states.append({"representation_id": representation.config.representation_id, "policy_sha256": representation.config.identity_sha256, "row_sha256": _hash("CORE_STRUCTURE_ROW_V1", facts), "facts": facts})
                if len({item["row_sha256"] for item in states}) > 1:
                    disagreement = {"information_key": _json(key), "state": "POLICY_OUTPUTS_DIFFER_NO_WINNER_SELECTED", "representations": states, "same_batch_order_unknown": True}
                    disagreement["record_id"] = "DIFF-" + _hash("CORE_STRUCTURE_DISAGREEMENT_V1", {"position": position, "representations": [(item["representation_id"], item["row_sha256"]) for item in states]})
                    self.sink.write("representation_disagreements", disagreement); retained_disagreement_rows.append(disagreement)
                    disagreement_ids.append(disagreement["record_id"]); self.disagreement_count += 1
            context = {
                "information_key": _json(key),
                "published_bar_record": {"record_identity": bar_id, "schema_identity": source_schema.as_payload(), "content": _json(bar_record.content)},
                "muf_s1_price_path": s1_content,
                "stage4a_surfaces": stage4a_rows,
                "stage4c_h1_raw_asof": {"scale": "H1", "duration_ns": bundle.htf.scale_duration_ns, "values": htf_row, "same_batch_semantics_preserved": True},
                "explicit_structural_surface_rows": structural_rows,
                "actual_executed_flow": flow_content,
                "actual_absorption": actual_absorption,
                "new_entity_ids": sorted(item.entity_id for item in current),
                "producer_event_ids": sorted(item.event_id for item in batch_events),
                "state_revision_ids": sorted(item.revision_id for item in new_revisions),
                "relationship_ids": sorted(self.current_relation_ids),
                "representation_disagreement_ids": disagreement_ids,
                "domain_availability_at_this_key": _asof_domain_states(bundle, htf_row, flow_content),
                "same_information_batch_rule": "UNORDERED_FACT_SET_NO_WITHIN_BATCH_ORDERING",
            }
            facts_hash = _hash("CORE_BOUNDARY_FACTS_V1", context)
            boundary_id = "BOUNDARY-" + _hash("CORE_BOUNDARY_RECORD_ID_V1", {"key": key, "facts_hash": facts_hash})
            prefix_prev = prefix
            step = {"position": position, "key": key, "boundary_id": boundary_id, "facts_hash": facts_hash, "entity_ids": sorted(item.entity_id for item in current), "event_ids": sorted(item.event_id for item in batch_events), "revision_ids": sorted(item.revision_id for item in new_revisions), "relation_ids": sorted(self.current_relation_ids), "disagreement_ids": disagreement_ids}
            prefix_next = _hash("CORE_ASOF_PREFIX_STEP_V1", {"previous": prefix, "step": step})
            boundary_record = PublishedRecord(record_identity=boundary_id, record_type="CAUSAL_MARKET_CONTEXT_BOUNDARY", schema_identity=SchemaIdentity("CAUSAL_MARKET_CONTEXT_BOUNDARY", CORE_SCHEMA_VERSION), timeline_id=key.timeline_id, availability_key=key, content=_frozen({"facts_hash": facts_hash, "facts": context, "prefix_chain_previous": prefix_prev, "prefix_chain_current": prefix_next, "prefix_chain_contract": "ASOF_STEP_CHAIN_EXCLUDES_FULL_SOURCE_OR_FUTURE_SURFACE_HASHES"}))
            boundary_payload = {"record_identity": boundary_id, "record_type": boundary_record.record_type, "schema_identity": boundary_record.schema_identity.as_payload(), "information_key": _json(key), "content": _json(boundary_record.content)}
            self.sink.write("boundary_records", boundary_payload); self.interpretation.register_evidence(boundary_id, key)
            if self.sink.retain:
                self.mem_boundaries.append(boundary_payload)
            coverage_row = {
                "information_key": _json(key),
                "registered_candidates_through_boundary": int(sum(actual_counts.values())),
                "new_candidates": len(current),
                "known_geometry_candidates_before_boundary": before_tree,
                "bar_price_query": coverage.bar_query,
                "new_entity_overlap_queries": list(coverage.entity_queries),
                "same_batch_pair_count": coverage.pair_count,
                "same_batch_pairs_examined": coverage.pair_checked,
                "same_batch_pairs_unexamined": coverage.pair_unexamined,
                "spatial_relations_emitted": coverage.emitted,
                "relationship_search_state": coverage.global_state,
                "candidate_universe_pruned": False,
                "all_candidate_registry_rows_written": True,
            }
            self.sink.write("relationship_coverage", coverage_row)
            if self.sink.retain:
                self.mem_coverage.append(coverage_row)
            interp_evidence = [boundary_id, bar_id] + [item.record.record_identity for item in current] + [item.record.record_identity for item in batch_events] + [item.revision_id for item in new_revisions] + self.current_relation_ids
            self.interpretation.append_unestablished(key, interp_evidence, ("PUBLIC_PRODUCER_CONTRACTS", "SOURCE_ROW_FACT:" + bar_id))
            prefix = prefix_next
            prefix_final = prefix
        if dict(sorted(actual_counts.items())) != candidate_counts:
            raise CausalMarketContextCoreError("complete producer-candidate coverage invariant failed")
        if sum(len(items) for items in events_by_position.values()) != len(self.ledger.events()):
            raise CausalMarketContextCoreError("append-only event ledger coverage invariant failed")
        if bundle.actual_flow is not None:
            known = set(map(int, bundle.market.index.asi8))
            for position, timestamp in enumerate(bundle.actual_flow.index):
                if int(timestamp.value) not in known:
                    unmapped = {"timestamp_utc": _json(timestamp), "status": "PRESERVED_NOT_JOINED_NO_NEAREST_ROW_MAPPING", "semantic_label": bundle.executed_source.semantic_label, "volume_unit": bundle.executed_source.volume_unit, "facts": _row(bundle.actual_flow, position)}
                    self.sink.write("unmapped_flow_observations", unmapped)
                    if self.sink.retain:
                        self.mem_unmapped_flow.append(unmapped)
        coverage_state = "PARTIAL_GLOBAL_SPATIAL_RELATIONSHIP_BUDGET" if self.global_partial else "PARTIAL_QUERY_OR_BOUNDARY_LIMIT" if self.any_spatial_partial else "BOUNDED_SEARCH_COMPLETE_FOR_VISITED_BOUNDARIES"
        summary = ReplaySummary(
            _hash("CORE_RUN_ID_V1", {"source_identity": _source_payload(bundle.source_identity), "source_hash": bundle.source_hash, "timeline_hash": bundle.timeline.timeline_hash}),
            len(bundle.market), len(self.entities), len(self.ledger.events()), len(self.mem_revisions) if self.sink.retain else sum(1 for _ in ()),
            self.relation_count, dict(sorted(self.relation_counts.items())), self.interpretation.count, self.disagreement_count,
            candidate_counts, coverage_state, prefix_final, None, bundle.source_state,
        )
        # Directory output has revision counts from the interpreter; state revisions
        # in a streaming sink are tracked separately below.
        state_revision_count = sum(1 for _ in self.mem_revisions) if self.sink.retain else self.state_revision_total
        summary = ReplaySummary(summary.run_id, summary.boundary_count, summary.entity_count, summary.producer_event_count, state_revision_count, summary.relationship_count, summary.relationship_counts_by_type, summary.interpretation_revision_count, summary.disagreement_count, summary.candidates_by_domain_representation, summary.relationship_coverage_state, summary.prefix_chain_sha256, summary.output_directory, summary.source_validation_state)
        provenance = {**_json(bundle.provenance), "candidate_counts_by_domain_representation": candidate_counts, "candidate_universe_complete": True, "producer_event_count": len(self.ledger.events()), "state_revision_count": state_revision_count, "relationship_counts_by_type": dict(self.relation_counts), "interpretation_policy_state": "NOT_CONFIGURED_BY_DEFAULT", "relationship_search_state": coverage_state, "prefix_chain_sha256": prefix_final, "hashes_do_not_authenticate_source_origin": True}
        evaluation = {"state": "NOT_ESTABLISHED_MISSING_TASK_AUTHORITY", "mechanism": "EXPLICIT_TASK_AUTHORITY_PLUS_EXISTING_TRAJECTORY_WINDOW_AND_EXCURSION_VIEW_REQUIRED", "no_default_horizon": True, "no_model_score_probability_or_recommendation": True}
        output_dir = self.sink.finish(summary.payload(), provenance, bundle.coverage, evaluation)
        if not self.sink.retain:
            return ReplaySummary(summary.run_id, summary.boundary_count, summary.entity_count, summary.producer_event_count, summary.state_revision_count, summary.relationship_count, summary.relationship_counts_by_type, summary.interpretation_revision_count, summary.disagreement_count, summary.candidates_by_domain_representation, summary.relationship_coverage_state, summary.prefix_chain_sha256, output_dir, summary.source_validation_state)
        return ReplayMemoryResult(summary, tuple(self.mem_entities), tuple(self.mem_events), tuple(self.mem_revisions), tuple(self.mem_relations), tuple(self.mem_boundaries), tuple(self.mem_coverage), tuple(self.mem_unmapped_flow), tuple(self.interpretation.retained), tuple(retained_disagreement_rows), dict(self.availability), _frozen(provenance), tuple(bundle.coverage), _frozen(evaluation))


def _price_path_facts(accepted: Any) -> dict[str, Any]:
    derivatives, running = accepted.derivatives_record.content, accepted.running_snapshot_record.content
    descriptors = {}
    for record in accepted.descriptor_records:
        content = record.content
        descriptors[str(content["descriptor_name"])] = {"record_id": record.record_identity, "descriptor_version": content["descriptor_version"], "boundary_contract": content["boundary_contract"], "availability_rule": content["availability_rule"], "value": _json(content["value"])}
    displacement = None
    if accepted.displacement_record is not None:
        content = accepted.displacement_record.content
        displacement = {"record_id": accepted.displacement_record.record_identity, "origin_key": _json(content["origin_key"]), "adjacent_key": _json(content["adjacent_key"]), "adjacency_kind": content["adjacency_kind"], "close_displacement": _json(content["close_displacement"]), "close_path_step": _json(content["close_path_step"]), "direction": _json(content["direction"])}
    return {"contract": "MUF_S1_PRICE_PATH_V1", "derivatives_record_id": accepted.derivatives_record.record_identity, "metrics": _json(derivatives["metrics"]), "metric_semantics": _json(derivatives["metric_semantics"]), "running_snapshot_record_id": accepted.running_snapshot_record.record_identity, "running_snapshot": {name: _json(running[name]) for name in ("scope", "running_high_so_far", "running_high_origins", "running_low_so_far", "running_low_origins", "origins_semantics")}, "descriptors": descriptors, "observed_displacement": displacement, "full_dataset_identity_not_used_as_asof_feature": True}


def _actual_flow_at(bundle: CoreBundle, position: int) -> dict[str, Any]:
    if bundle.actual_flow is None:
        return {"state": "UNAVAILABLE_NOT_SUPPLIED", "semantic_label": None, "volume_unit": None, "facts": None}
    timestamp = bundle.market.index[position]
    location = bundle.actual_flow.index.get_indexer([timestamp])
    if not location.size or int(location[0]) < 0:
        return {"state": "NO_FLOW_ROW_AT_EXACT_MARKET_TIMESTAMP", "semantic_label": bundle.executed_source.semantic_label, "volume_unit": bundle.executed_source.volume_unit, "facts": None}
    return {"state": "AVAILABLE_AT_EXACT_SOURCE_TIMESTAMP", "semantic_label": bundle.executed_source.semantic_label, "volume_unit": bundle.executed_source.volume_unit, "mode": OrderFlowMode.ACTUAL_AGGRESSOR.value, "facts": _row(bundle.actual_flow, int(location[0])), "intrabar_order_claimed": False, "tie_order_contract": "NOT_PROVEN"}


def _asof_domain_states(bundle: CoreBundle, htf: Mapping[str, Any], flow: Mapping[str, Any]) -> dict[str, str]:
    htf_key = f"{bundle.htf.scale_name}__completed_bucket_end_utc"
    return {
        "PUBLISHED_OHLC_BAR_FACTS": "AVAILABLE_AT_THIS_KEY",
        "MUF_S1_PRICE_PATH": "AVAILABLE_AT_THIS_KEY",
        "STAGE4A_VOLATILITY": "AVAILABLE_AT_THIS_KEY",
        "STAGE4A_OHLCV_PROXY": "AVAILABLE_AS_PROXY" if any(surface.domain == "ORDER_FLOW_PROXY" for surface in bundle.stage4a) else "UNAVAILABLE_VOLUME_NOT_SUPPLIED",
        "STAGE4C_H1_RAW": "AVAILABLE_ASOF_THIS_KEY" if htf.get(htf_key) is not None else "UNAVAILABLE_NO_COMPLETED_BUCKET_ASOF_THIS_KEY",
        "STAGE4B2_FVG": "AVAILABLE_PRODUCER_DOMAIN",
        "STAGE4B1_STRUCTURE": "AVAILABLE_EXPLICIT_POLICY" if bundle.structures else "UNAVAILABLE_NO_EXPLICIT_SWING_POLICY",
        "STAGE4B2_LIQUIDITY": "AVAILABLE_EXPLICIT_POLICY" if bundle.structures else "UNAVAILABLE_NO_EXPLICIT_SWING_POLICY",
        "STAGE4B2_ORDER_BLOCK": "AVAILABLE_EXPLICIT_POLICY" if bundle.structures else "UNAVAILABLE_NO_EXPLICIT_SWING_POLICY",
        "STAGE4B2_DEALING_RANGE": "AVAILABLE_EXPLICIT_POLICY" if bundle.structures else "UNAVAILABLE_NO_EXPLICIT_SWING_POLICY",
        "STAGE4B1_AND_DEPENDENT_STAGE4B2": "AVAILABLE_EXPLICIT_POLICY" if bundle.structures else "UNAVAILABLE_NO_EXPLICIT_SWING_POLICY",
        "ACTUAL_EXECUTED_FLOW": flow["state"],
        "MARKET_INTERPRETATION": "INTERPRETATION_NOT_ESTABLISHED_NO_JUSTIFIED_POLICY",
    }


def _candidate_event_totals(bundle: CoreBundle) -> tuple[int, int]:
    entities = len(bundle.fvg.normalized_entity_frame)
    events = len(bundle.fvg.normalized_event_frame)
    for representation in bundle.structures:
        for surface in (representation.liquidity, representation.order_block, representation.dealing_range):
            entities += len(surface.normalized_entity_frame)
            if not isinstance(surface, s4b2.Stage4B2DealingRangeSurface):
                events += len(surface.normalized_event_frame)
        structure_frame = representation.structure.frame
        for name in ("swing_high_confirmed", "swing_low_confirmed"):
            if name not in structure_frame.columns:
                raise CausalMarketContextCoreError(f"Stage4B1 missing {name}")
            count = sum(_producer_bool(value, name) for value in structure_frame[name].tolist())
            entities += count; events += count
    return entities, events


def _verify_bundle(bundle: CoreBundle) -> None:
    bundle.timeline.verify(adapter=bundle.adapter, market_history=bundle.market)
    for surface in bundle.stage4a:
        s4a.verify_surface_integrity(surface)
        if not surface.surface.index.equals(bundle.market.index):
            raise CausalMarketContextCoreError("Stage4A index mismatch")
    s4c.verify_surface_integrity(bundle.htf)
    if not bundle.htf.asof_bar_frame.index.equals(bundle.market.index):
        raise CausalMarketContextCoreError("Stage4C H1 index mismatch")
    s4b2.verify_surface_integrity(bundle.fvg)
    if not bundle.fvg.bar_frame.index.equals(bundle.market.index):
        raise CausalMarketContextCoreError("Stage4B2 FVG index mismatch")
    for representation in bundle.structures:
        s4b1.verify_surface_integrity(representation.structure)
        if not representation.structure.frame.index.equals(bundle.market.index):
            raise CausalMarketContextCoreError("Stage4B1 structure index mismatch")
        for surface in (representation.liquidity, representation.order_block, representation.dealing_range):
            s4b2.verify_surface_integrity(surface)
            if not surface.bar_frame.index.equals(bundle.market.index):
                raise CausalMarketContextCoreError("Stage4B2 dependent index mismatch")
    if bundle.actual_flow is not None and _hash("CORE_ACTUAL_FLOW_FRAME_V1", bundle.actual_flow) != bundle.actual_flow_hash:
        raise CausalMarketContextCoreError("actual flow frame changed after validation")
    if bundle.actual_absorption is not None and _hash("CORE_ACTUAL_ABSORPTION_FRAME_V1", bundle.actual_absorption) != bundle.actual_absorption_hash:
        raise CausalMarketContextCoreError("actual absorption frame changed after validation")


def build_causal_market_context_core(
    *,
    market_history: pd.DataFrame,
    source_identity: SourceArtifactIdentity,
    timeline_id: str,
    source_file_sha256: str | None = None,
    source_validation: KlineOhlcSource | None = None,
    minute_facts_source: MinuteFactsSource | None = None,
    swing_policies: Sequence[SwingPolicyConfig] = (),
) -> CoreBundle:
    """Seal one source and build existing shared surfaces; no structure default exists."""
    if not isinstance(source_identity, SourceArtifactIdentity) or not isinstance(timeline_id, str) or not timeline_id.strip():
        raise CausalMarketContextCoreError("SourceArtifactIdentity and timeline_id are required")
    market = _market_copy(market_history)
    if len(market) > MAX_INPUT_BARS:
        raise CausalMarketContextCoreError("input exceeds hard resource ceiling; no bars were pruned")
    _check_source_period(market, source_identity)
    if source_validation is not None and not isinstance(source_validation, KlineOhlcSource):
        raise CausalMarketContextCoreError("source_validation must be a KlineOhlcSource")
    if source_validation is not None:
        if source_validation.identity != source_identity or not _market_copy(source_validation.canonical_market_frame).equals(market):
            raise CausalMarketContextCoreError("validated Kline source identity/content mismatch")
        actual_hash = source_validation.provenance.source_file_sha256
        if source_file_sha256 is not None and _require_hash(source_file_sha256, "source hash") != actual_hash:
            raise CausalMarketContextCoreError("declared source hash differs from Kline source")
        source_hash = actual_hash
        source_state = "BINANCE_KLINE_SCHEMA_VALIDATED_NOT_ORIGIN_AUTHENTICATED"
        source_semantics = "PUBLISHED_KLINE_OHLC; TIE_ORDER_NOT_PROVEN"
        source_metadata = {"schema_contract": source_validation.provenance.schema_contract, "source_file_sha256": actual_hash, "source_rows": source_validation.provenance.source_rows, "tie_order_contract": source_validation.provenance.tie_order_contract, "missing_minute_intervals": _json(source_validation.missing_minute_intervals), "origin_authenticated": False}
    else:
        if source_file_sha256 is None:
            source_hash = _hash("CORE_CALLER_FRAME_HASH_V1", market)
            source_state = "CALLER_FRAME_CANONICAL_HASH_NOT_FILE_AUTHENTICATION"
        else:
            source_hash = _require_hash(source_file_sha256, "source_file_sha256")
            source_state = "CALLER_DECLARED_FILE_HASH_NOT_ORIGIN_AUTHENTICATED"
        source_semantics = "CALLER_SUPPLIED_OHLC; SOURCE_ORIGIN_UNVERIFIED"
        source_metadata = {"source_file_sha256_or_frame_hash": source_hash, "origin_authenticated": False}

    adapter = TimeIndexedTimelineAdapter(timeline_id)
    timeline = MarketObservationTimeline.seal(adapter=adapter, market_history=market)
    timeline.verify(adapter=adapter, market_history=market)
    vol = s4a.build_volatility_surface(timeline=timeline, adapter=adapter, market_history=market)
    stage4a = [vol]
    if "volume" in market.columns:
        flow_proxy = s4a.build_order_flow_proxy_surface(timeline=timeline, adapter=adapter, market_history=market, mode=OrderFlowMode.OHLCV_PROXY)
        absorption_proxy = s4a.build_absorption_proxy_surface(timeline=timeline, adapter=adapter, market_history=market, order_flow_surface=flow_proxy, mode=OrderFlowMode.OHLCV_PROXY)
        stage4a.extend((flow_proxy, absorption_proxy))
    for surface in stage4a:
        s4a.verify_surface_integrity(surface)
    htf = s4c.build_htf_scale_surface(
        timeline=timeline,
        adapter=adapter,
        market_history=market,
        scale_spec=s4c.HtfScaleSpec(name="H1", duration=pd.Timedelta(hours=1)),
        cadence=s4c.CadenceGridContract(pd.Timestamp("1970-01-01T00:00:00Z"), pd.Timedelta(minutes=1)),
    )
    s4c.verify_surface_integrity(htf)
    fvg = s4b2.build_fvg_surface(timeline=timeline, adapter=adapter, market_history=market)
    s4b2.verify_surface_integrity(fvg)
    policies = tuple(swing_policies)
    if len(policies) > MAX_STRUCTURAL_REPRESENTATIONS or any(not isinstance(p, SwingPolicyConfig) for p in policies):
        raise CausalMarketContextCoreError("explicit policy set invalid or exceeds representation limit; none were pruned")
    if len({p.policy_id for p in policies}) != len(policies) or len({p.representation_id for p in policies}) != len(policies):
        raise CausalMarketContextCoreError("swing policy identities must be unique")
    policies = tuple(sorted(policies, key=lambda p: p.representation_id))
    structures = []
    for config in policies:
        structure = s4b1.build_structure_surface(timeline=timeline, adapter=adapter, market_history=market, swing_policy=config.policy)
        s4b1.verify_surface_integrity(structure)
        liq = s4b2.build_liquidity_surface(timeline=timeline, adapter=adapter, market_history=market, structure_surface=structure)
        ob = s4b2.build_order_block_surface(timeline=timeline, adapter=adapter, market_history=market, structure_surface=structure)
        dr = s4b2.build_dealing_range_surface(timeline=timeline, adapter=adapter, market_history=market, structure_surface=structure)
        for item in (liq, ob, dr): s4b2.verify_surface_integrity(item)
        structures.append(StructuralRepresentation(config, structure, liq, ob, dr))
    executed = None; actual_flow = None; actual_abs = None
    actual_abs_state = "UNAVAILABLE_NOT_SUPPLIED"
    flow_hash = abs_hash = None
    if minute_facts_source is not None:
        if not isinstance(minute_facts_source, MinuteFactsSource) or minute_facts_source.identity != source_identity:
            raise CausalMarketContextCoreError("validated minute facts with matching source identity required")
        if not isinstance(minute_facts_source.provenance, MinuteFactsProvenance) or minute_facts_source.provenance.identity != source_identity:
            raise CausalMarketContextCoreError("MinuteFactsProvenance with matching identity is required")
        _require_hash(minute_facts_source.provenance.minute_facts_sha256, "minute-facts source hash")
        if minute_facts_source.provenance.TIE_ORDER_CONTRACT != "NOT_PROVEN":
            raise CausalMarketContextCoreError("minute-facts source must preserve NOT_PROVEN tie-order semantics")
        try:
            executed = build_executed_flow_source(minute_facts_source)
            actual_flow = CausalVolumeDeltaEngine(mode=OrderFlowMode.ACTUAL_AGGRESSOR, reconcile_total_volume=True).analyze(executed.frame)
            actual_flow = _timed_fact_copy(actual_flow, "actual flow")
            flow_hash = _hash("CORE_ACTUAL_FLOW_FRAME_V1", actual_flow)
            if actual_flow.index.equals(market.index):
                with_close = actual_flow.copy(deep=True); with_close["close"] = market["close"].to_numpy(float)
                actual_abs = CausalAbsorptionEvidenceEngine(mode=OrderFlowMode.ACTUAL_AGGRESSOR).analyze(with_close)
                abs_hash = _hash("CORE_ACTUAL_ABSORPTION_FRAME_V1", actual_abs)
                actual_abs_state = "AVAILABLE_ACTUAL_AGGRESSOR_BAR_RESPONSE; INTRABAR_ORDER_UNPROVEN"
            else:
                actual_abs_state = "UNAVAILABLE_PRICE_FLOW_INDEX_MISMATCH_NO_NEAREST_ROW_OR_GAP_BRIDGING"
        except Exception as exc:
            raise CausalMarketContextCoreError(f"actual-flow source rejected input: {exc}") from exc
    stage_ids = {surface.domain: surface.surface_id for surface in stage4a}
    coverage = [
        {"domain": "PUBLISHED_OHLC_BAR_FACTS", "state": "AVAILABLE", "fact_count": len(market), "semantics": source_semantics},
        {"domain": "MUF_S1_PRICE_PATH", "state": "AVAILABLE", "fact_count": len(market), "semantics": "CAUSAL_OBSERVATION_STREAM; OBSERVATION_ADJACENT; NO_INTRABAR_PATH_RECONSTRUCTION"},
        {"domain": "STAGE4A_VOLATILITY", "state": "AVAILABLE", "surface_id": vol.surface_id},
        {"domain": "STAGE4A_ORDER_FLOW_PROXY", "state": "AVAILABLE" if "ORDER_FLOW_PROXY" in stage_ids else "UNAVAILABLE_VOLUME_NOT_SUPPLIED", "semantics": "OHLCV_PROXY_NOT_ACTUAL_AGGRESSOR"},
        {"domain": "STAGE4A_ABSORPTION_PROXY", "state": "AVAILABLE" if "ABSORPTION_PROXY" in stage_ids else "UNAVAILABLE_VOLUME_NOT_SUPPLIED", "semantics": "PROXY_ONLY"},
        {"domain": "STAGE4C_H1_RAW", "state": "AVAILABLE" if len(htf.bucket_frame) else "AVAILABLE_EMPTY_NO_COMPLETED_BUCKET", "completed_bucket_count": len(htf.bucket_frame), "semantics": "RAW_COMPLETED_H1_OHLC_NO_STRUCTURE"},
        {"domain": "STAGE4B2_FVG", "state": "AVAILABLE" if len(fvg.normalized_entity_frame) else "AVAILABLE_EMPTY", "candidate_count": len(fvg.normalized_entity_frame), "producer_event_count": len(fvg.normalized_event_frame)},
        {"domain": "STAGE4B1_STRUCTURE", "state": "AVAILABLE_EXPLICIT_POLICIES" if structures else "UNAVAILABLE_NO_EXPLICIT_SWING_POLICY", "representation_count": len(structures)},
        {"domain": "STAGE4B2_LIQUIDITY", "state": "AVAILABLE_EXPLICIT_POLICIES" if structures else "UNAVAILABLE_NO_EXPLICIT_SWING_POLICY", "candidate_count": sum(len(item.liquidity.normalized_entity_frame) for item in structures), "representation_count": len(structures)},
        {"domain": "STAGE4B2_ORDER_BLOCK", "state": "AVAILABLE_EXPLICIT_POLICIES" if structures else "UNAVAILABLE_NO_EXPLICIT_SWING_POLICY", "candidate_count": sum(len(item.order_block.normalized_entity_frame) for item in structures), "representation_count": len(structures)},
        {"domain": "STAGE4B2_DEALING_RANGE", "state": "AVAILABLE_EXPLICIT_POLICIES" if structures else "UNAVAILABLE_NO_EXPLICIT_SWING_POLICY", "candidate_count": sum(len(item.dealing_range.normalized_entity_frame) for item in structures), "representation_count": len(structures)},
        {"domain": "STAGE4B1_AND_DEPENDENT_STAGE4B2", "state": "AVAILABLE_EXPLICIT_POLICIES" if structures else "UNAVAILABLE_NO_EXPLICIT_SWING_POLICY", "representation_count": len(structures), "dependent_domains": ["LIQUIDITY", "ORDER_BLOCK", "DEALING_RANGE"]},
        {"domain": "ACTUAL_EXECUTED_INITIATED_FLOW", "state": "AVAILABLE" if actual_flow is not None else "UNAVAILABLE_NOT_SUPPLIED", "fact_count": 0 if actual_flow is None else len(actual_flow), "semantic_label": None if executed is None else executed.semantic_label, "volume_unit": None if executed is None else executed.volume_unit},
        {"domain": "ACTUAL_AGGRESSOR_ABSORPTION", "state": actual_abs_state, "fact_count": 0 if actual_abs is None else len(actual_abs)},
        {"domain": "STAGE4C_HTF_STRUCTURE", "state": "UNAVAILABLE_NO_HTF_STRUCTURE_CONTRACT"},
        {"domain": "WAVE_INTERPRETATION", "state": "UNAVAILABLE_NO_CONFIGURED_WAVE_CONTRACT"},
        {"domain": "SESSION_CONTEXT", "state": "UNAVAILABLE_NO_EXPLICIT_SESSION_CONTRACT"},
        {"domain": "MARKET_INTERPRETATION", "state": "INTERPRETATION_NOT_ESTABLISHED_NO_JUSTIFIED_POLICY"},
        {"domain": "TASK_OUTCOME", "state": "NOT_ESTABLISHED_MISSING_TASK_AUTHORITY"},
    ]
    provenance = {
        "core_id": CORE_ID,
        "core_schema_version": CORE_SCHEMA_VERSION,
        "source_identity": _source_payload(source_identity),
        "source_hash": source_hash,
        "source_validation_state": source_state,
        "source_metadata": source_metadata,
        "source_semantics": source_semantics,
        "timeline_id": timeline.timeline_id,
        "timeline_hash": timeline.timeline_hash,
        "producer_contracts": {"stage4a": s4a.TRAJECTORY_STAGE4A_CONTRACT_VERSION, "stage4b1": s4b1.TRAJECTORY_STAGE4B1_CONTRACT_VERSION, "stage4b2": s4b2.TRAJECTORY_STAGE4B2_CONTRACT_VERSION, "stage4c": s4c.TRAJECTORY_STAGE4C_CONTRACT_VERSION, "price_path": "MUF_S1_PRICE_PATH_V1"},
        "stage4a_surface_ids": stage_ids,
        "htf_surface_id": htf.surface_id,
        "fvg_surface_id": fvg.surface_id,
        "structural_policies": [{"representation_id": item.config.representation_id, "policy": item.config.payload(), "policy_sha256": item.config.identity_sha256, "structure_surface_id": item.structure.surface_id, "liquidity_surface_id": item.liquidity.surface_id, "order_block_surface_id": item.order_block.surface_id, "dealing_range_surface_id": item.dealing_range.surface_id} for item in structures],
        "actual_flow": None if executed is None else {"semantic_label": executed.semantic_label, "volume_unit": executed.volume_unit, "statement": executed.statement, "source_minute_facts_sha256": executed.source_minute_facts_sha256, "minute_facts_source_provenance": _json(minute_facts_source.provenance), "minute_facts_missing_intervals": _json(minute_facts_source.missing_minute_intervals), "minute_facts_full_coverage_required": minute_facts_source.require_full_coverage, "tie_order_contract": minute_facts_source.provenance.TIE_ORDER_CONTRACT, "ambiguous_open_minute_count": minute_facts_source.provenance.ambiguous_open_minute_count, "ambiguous_close_minute_count": minute_facts_source.provenance.ambiguous_close_minute_count, "actual_absorption_state": actual_abs_state},
        "authentication_boundary": "HASH_AND_ADAPTER_VALIDATION_DO_NOT_AUTHENTICATE_HISTORICAL_SOURCE_ORIGIN",
    }
    return CoreBundle(market, timeline, adapter, source_identity, source_hash, source_state, source_semantics, _frozen(source_metadata), tuple(stage4a), htf, fvg, tuple(structures), executed, actual_flow, actual_abs, flow_hash, abs_hash, actual_abs_state, _frozen(provenance), tuple(_frozen(item) for item in coverage))


def replay_causal_market_context(bundle: CoreBundle, *, output_dir: str | Path | None = None, sink: _Sink | None = None, limits: ReplayLimits = ReplayLimits()) -> ReplayMemoryResult | ReplaySummary:
    if not isinstance(bundle, CoreBundle) or not isinstance(limits, ReplayLimits):
        raise CausalMarketContextCoreError("CoreBundle and ReplayLimits are required")
    if sink is not None and output_dir is not None:
        raise CausalMarketContextCoreError("provide sink or output_dir, not both")
    sink = sink or (DirectorySink(output_dir) if output_dir is not None else MemorySink())
    replay = _Replay(bundle, sink, limits)
    try:
        return replay.run()
    except Exception:
        if isinstance(sink, DirectorySink):
            sink.abort()
        raise


def evaluate_explicit_task_outcome(*, bundle: CoreBundle, authority: TaskEvaluationAuthority, decision_key: InformationKey, horizon_request: HorizonRequest, coverage_contract: CoverageContract) -> TaskOutcome:
    """Use existing factual trajectory outcome machinery only under explicit task authority."""
    if not isinstance(authority, TaskEvaluationAuthority) or not isinstance(decision_key, InformationKey) or not isinstance(horizon_request, HorizonRequest) or not isinstance(coverage_contract, CoverageContract):
        raise CausalMarketContextCoreError("explicit task authority, key, horizon, and coverage contract are required")
    if decision_key.timeline_id != bundle.timeline.timeline_id or horizon_request.requested_end_key.timeline_id != bundle.timeline.timeline_id:
        raise CausalMarketContextCoreError("task request belongs to another timeline")
    case = create_trajectory_decision_case(timeline=bundle.timeline, adapter=bundle.adapter, market_history=bundle.market, decision_key=decision_key, surfaces=(), parent_snapshot=None)
    window = build_trajectory_window(case=case, timeline=bundle.timeline, adapter=bundle.adapter, market_history=bundle.market, horizon_request=horizon_request, coverage_contract=coverage_contract)
    reference = decision_close_excursion_reference(window)
    excursion = derive_excursion_view(window=window, reference=reference)
    return TaskOutcome(authority, case.case_id, window.reference.path_id, horizon_request.identity_hash, coverage_contract.identity_hash, excursion)


def _verify_output_manifest(root: Path) -> None:
    manifest_path = root / "hash_manifest.json"
    if (root / "RUN_INCOMPLETE").exists() or not manifest_path.is_file():
        raise CausalMarketContextCoreError("replay output is incomplete or has no output manifest")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CausalMarketContextCoreError("output manifest cannot be parsed") from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != "CAUSAL_MARKET_CONTEXT_OUTPUT_HASH_MANIFEST_V1" or manifest.get("self_hash_excluded") is not True or not isinstance(manifest.get("files"), list):
        raise CausalMarketContextCoreError("output manifest schema is invalid")
    listed: set[str] = set()
    for item in manifest["files"]:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise CausalMarketContextCoreError("output manifest file entry is malformed")
        name = item["path"]
        if not name or "/" in name or chr(92) in name or Path(name).name != name or name in {".", "..", "hash_manifest.json", "RUN_INCOMPLETE"} or name in listed:
            raise CausalMarketContextCoreError("output manifest path is unsafe or duplicated")
        listed.add(name)
        digest = _require_hash(item.get("sha256"), "output file hash")
        size = item.get("bytes")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise CausalMarketContextCoreError("output manifest byte count is invalid")
        path = root / name
        if path.resolve().parent != root.resolve() or not path.is_file() or path.stat().st_size != size or sha256_file(str(path)) != digest:
            raise CausalMarketContextCoreError(f"output file differs from manifest: {name}")
    actual = {path.name for path in root.iterdir() if path.is_file() and path.name != "hash_manifest.json"}
    if actual != listed:
        raise CausalMarketContextCoreError("output directory file set differs from manifest")
    if not {"summary.json", "entities.jsonl", "entity_state_revisions.jsonl"}.issubset(listed):
        raise CausalMarketContextCoreError("manifest omits required replay state streams")


def entity_state_as_of_from_directory(*, output_dir: str | Path, entity_id: str, as_of_key: InformationKey) -> Mapping[str, Any]:
    if not isinstance(as_of_key, InformationKey) or as_of_key.information_phase not in LEGAL_ASOF_PHASES:
        raise CausalMarketContextCoreError("legal as-of key required")
    root = Path(output_dir).expanduser().resolve()
    _verify_output_manifest(root)
    entities_path = root / "entities.jsonl"
    revisions_path = root / "entity_state_revisions.jsonl"
    if not entities_path.is_file() or not revisions_path.is_file():
        raise CausalMarketContextCoreError("entity registry or revision stream missing")
    registered = None
    with entities_path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("entity_id") == entity_id:
                registered = row
                break
    if registered is None:
        raise CausalMarketContextCoreError("unknown entity identity")
    available = registered["availability_key"]
    if available["timeline_id"] != as_of_key.timeline_id:
        raise CausalMarketContextCoreError("cross-timeline as-of lookup")
    if int(available["bar_position"]) > as_of_key.bar_position:
        raise CausalMarketContextCoreError("entity is not visible at requested key")
    summary_path = root / "summary.json"
    if summary_path.is_file():
        boundary_count = int(json.loads(summary_path.read_text(encoding="utf-8"))["boundary_count"])
        if as_of_key.bar_position >= boundary_count:
            raise CausalMarketContextCoreError("as-of key is beyond the replayed boundary range")
    latest = None
    with revisions_path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line); key = row["available_key"]
            if row["entity_id"] == entity_id and key["timeline_id"] == as_of_key.timeline_id and int(key["bar_position"]) <= as_of_key.bar_position:
                if latest is None or int(key["bar_position"]) > int(latest["available_key"]["bar_position"]):
                    latest = row
    if latest is None:
        return {"entity_id": entity_id, "as_of_key": _json(as_of_key), "state": "REGISTERED_NO_PRODUCER_LIFECYCLE_FACTS_AS_OF_KEY", "revision": None}
    return {"entity_id": entity_id, "as_of_key": _json(as_of_key), "state": "PRODUCER_EVENT_FACT_SET_AVAILABLE", "revision": latest}


def _policy_file(path: str | Path) -> tuple[SwingPolicyConfig, ...]:
    raw = Path(path).read_bytes(); digest = hashlib.sha256(raw).hexdigest()
    try: document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc: raise CausalMarketContextCoreError(f"invalid swing policy JSON: {exc}") from exc
    if not isinstance(document, dict) or document.get("schema_version") != "EXPLICIT_SWING_POLICY_SET_V1":
        raise CausalMarketContextCoreError("swing policy schema_version must be EXPLICIT_SWING_POLICY_SET_V1")
    entries = document.get("policies")
    if not isinstance(entries, list) or not entries: raise CausalMarketContextCoreError("policies must be a nonempty array")
    result = []
    fields = {"policy_id", "quantile", "prior_continuation_reversals", "prior_confirmed_reversals"}
    for item in entries:
        if not isinstance(item, dict) or set(item) != fields or not isinstance(item["policy_id"], str):
            raise CausalMarketContextCoreError("each policy requires exactly policy_id, quantile, and both explicit prior arrays")
        if not isinstance(item["prior_continuation_reversals"], list) or not isinstance(item["prior_confirmed_reversals"], list):
            raise CausalMarketContextCoreError("prior values must be explicit JSON arrays (use [] for none)")
        policy = EmpiricalConfirmationPolicy(float(item["quantile"]), tuple(item["prior_continuation_reversals"]), tuple(item["prior_confirmed_reversals"]))
        result.append(SwingPolicyConfig(item["policy_id"], policy, digest))
    return tuple(result)


def _args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", required=True, help="existing local Spot 1m klines CSV; no download")
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--period-start-utc", required=True)
    parser.add_argument("--period-end-utc", required=True)
    parser.add_argument("--output-dir", required=True, help="new/empty directory outside the checkout")
    parser.add_argument("--minute-facts-csv", help="optional already-converted minute-facts CSV")
    parser.add_argument("--minute-facts-sidecar", help="sidecar for existing minute-facts CSV; no conversion")
    parser.add_argument("--swing-policy-json", help="optional explicit policy set; omission fails structural domains closed")
    parser.add_argument("--max-registered-entities", type=int, default=100_000)
    parser.add_argument("--max-producer-events", type=int, default=250_000)
    parser.add_argument("--max-interval-nodes", type=int, default=20_000)
    parser.add_argument("--max-spatial-relations-per-boundary", type=int, default=128)
    parser.add_argument("--max-spatial-relations-total", type=int, default=250_000)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _args(argv)
    if bool(args.minute_facts_csv) != bool(args.minute_facts_sidecar):
        raise CausalMarketContextCoreError("both minute-facts file and sidecar must be supplied together")
    identity = SourceArtifactIdentity(args.symbol, "SPOT", "1m", args.period_start_utc, args.period_end_utc)
    kline = load_binance_spot_klines(args.csv, identity=identity, require_full_coverage=False)
    policies = _policy_file(args.swing_policy_json) if args.swing_policy_json else ()
    facts = None
    if args.minute_facts_csv:
        facts = load_minute_facts(args.minute_facts_csv, args.minute_facts_sidecar, identity=identity, expected=MinuteFactsExpectedProvenance(symbol=args.symbol), require_full_coverage=False)
    timeline_id = "binance-spot-kline-" + args.symbol.lower() + "-" + args.period_start_utc.replace(":", "-").replace("T", "-").replace("Z", "") + "-" + args.period_end_utc.replace(":", "-").replace("T", "-").replace("Z", "")
    bundle = build_causal_market_context_core(market_history=kline.canonical_market_frame, source_identity=identity, timeline_id=timeline_id, source_file_sha256=kline.provenance.source_file_sha256, source_validation=kline, minute_facts_source=facts, swing_policies=policies)
    limits = ReplayLimits(max_registered_entities=args.max_registered_entities, max_producer_events=args.max_producer_events, max_interval_nodes_per_query=args.max_interval_nodes, max_spatial_relations_per_boundary=args.max_spatial_relations_per_boundary, max_spatial_relations_total=args.max_spatial_relations_total)
    summary = replay_causal_market_context(bundle, output_dir=args.output_dir, limits=limits)
    print(json.dumps(_json(summary), ensure_ascii=False, sort_keys=True, indent=2))
    return 0


__all__ = [
    "CORE_ID",
    "CausalMarketContextCoreError",
    "CoreBundle",
    "CoreEntity",
    "DirectorySink",
    "EntityRevision",
    "EntityStateAsOf",
    "InterpretationPolicyReference",
    "InterpretationRevision",
    "InterpretationRevisionLedger",
    "MemorySink",
    "ProducerEvent",
    "Relation",
    "ReplayLimits",
    "ReplayMemoryResult",
    "ReplaySummary",
    "StructuralRepresentation",
    "SwingPolicyConfig",
    "TaskEvaluationAuthority",
    "TaskOutcome",
    "build_causal_market_context_core",
    "entity_state_as_of_from_directory",
    "evaluate_explicit_task_outcome",
    "main",
    "replay_causal_market_context",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
