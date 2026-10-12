"""As-of surface composition and factual, explicitly bounded path queries.

This module does not retrieve files, choose horizons/samples/candidate levels,
classify all possible paths, or create a decision feature from future rows. A
trajectory window is built only from caller-supplied rows that verify against a
sealed timeline; that operation is ephemeral and is not durable retrieval.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
import math
import re
from typing import Iterable

import numpy as np
import pandas as pd

from trading_system.research.hashing import canonical_sha256
from trading_system.research.information_time import (
    INFORMATION_KEY_VERSION,
    InformationKey,
    InformationPhase,
    PositionalTimelineAdapter,
    TimeIndexedTimelineAdapter,
)
from trading_system.research.trajectory.trajectory_contract import MarketObservationTimeline
from trading_system.research.trajectory.trajectory_timeline_resolver import (
    TimelineArtifactReference,
)
from trading_system.research.trajectory.trajectory_case_adapter import (
    TrajectoryCaseError,
    TrajectoryDecisionCase,
    _verify_case_source_prefix_snapshot,
    _verify_surface_prefix_snapshot,
    snapshot_market_history,
    snapshot_stage4_surface,
)
from trading_system.research.trajectory import trajectory_stage4a as s4a
from trading_system.research.trajectory import trajectory_stage4b1 as s4b1
from trading_system.research.trajectory import trajectory_stage4b2 as s4b2
from trading_system.research.trajectory import trajectory_stage4c as s4c


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_LEGAL_QUERY_PHASES = frozenset(
    {InformationPhase.COMPLETED_ROW_AVAILABLE, InformationPhase.RESEARCH_SNAPSHOT_AVAILABLE}
)
TimelineAdapter = PositionalTimelineAdapter | TimeIndexedTimelineAdapter


class TrajectoryQueryError(ValueError):
    """Invalid as-of view, query identity, or factual path input."""


class AvailabilityStatus(Enum):
    AVAILABLE = "AVAILABLE"
    NOT_SUPPLIED = "NOT_SUPPLIED"


class FrozenCellKind(Enum):
    MISSING = "MISSING"
    NUMBER = "NUMBER"
    BOOLEAN = "BOOLEAN"
    STRING = "STRING"
    TIMESTAMP_UTC_NS = "TIMESTAMP_UTC_NS"
    TIMEDELTA_NS = "TIMEDELTA_NS"


class CensoringState(Enum):
    OBSERVED_TO_REQUESTED_END = "OBSERVED_TO_REQUESTED_END"
    RIGHT_CENSORED = "RIGHT_CENSORED"


class HorizonCompletionState(Enum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"


class QueryResolutionState(Enum):
    RESOLVED = "RESOLVED"


class ExcursionReferenceKind(Enum):
    MARKET_MARK = "MARKET_MARK"


class CoverageAssessment(Enum):
    UNASSESSED = "UNASSESSED"
    CONTIGUOUS = "CONTIGUOUS_UNDER_DECLARED_STEP"
    GAPS_OR_CADENCE_DEVIATION = "GAPS_OR_CADENCE_DEVIATION"


class CallerRowAccessState(Enum):
    CALLER_SUPPLIED_VERIFIED_FRAME = "CALLER_SUPPLIED_VERIFIED_FRAME_NOT_DURABLE"


class InteractionStatus(Enum):
    OBSERVED_TOUCH = "OBSERVED_TOUCH"
    NOT_OBSERVED_COMPLETE_WINDOW = "NOT_OBSERVED_COMPLETE_WINDOW"
    NOT_OBSERVED_RIGHT_CENSORED = "NOT_OBSERVED_RIGHT_CENSORED"
    NOT_OBSERVED_RIGHT_CENSORED_WITH_COVERAGE_GAPS = "NOT_OBSERVED_RIGHT_CENSORED_WITH_COVERAGE_GAPS"
    NOT_OBSERVED_COVERAGE_GAPS = "NOT_OBSERVED_COVERAGE_GAPS"
    NOT_OBSERVED_COVERAGE_UNASSESSED = "NOT_OBSERVED_COVERAGE_UNASSESSED"
    NO_POST_DECISION_ROWS_TO_REQUESTED_END = "NO_POST_DECISION_ROWS_TO_REQUESTED_END"
    RIGHT_CENSORED_NO_POST_DECISION_ROWS = "RIGHT_CENSORED_NO_POST_DECISION_ROWS"
    NO_POST_DECISION_ROWS_COVERAGE_UNASSESSED = "NO_POST_DECISION_ROWS_COVERAGE_UNASSESSED"


class PairOrderStatus(Enum):
    TARGET_OBSERVED_FIRST = "TARGET_OBSERVED_FIRST"
    INVALIDATION_OBSERVED_FIRST = "INVALIDATION_OBSERVED_FIRST"
    BOTH_SAME_BAR_ORDER_UNKNOWN = "BOTH_SAME_BAR_ORDER_UNKNOWN"
    ORDER_UNDETERMINED_COVERAGE = "ORDER_UNDETERMINED_COVERAGE"
    NO_OBSERVED_TOUCH_COMPLETE_WINDOW = "NO_OBSERVED_TOUCH_COMPLETE_WINDOW"
    NO_OBSERVED_TOUCH_RIGHT_CENSORED = "NO_OBSERVED_TOUCH_RIGHT_CENSORED"
    NO_OBSERVED_TOUCH_RIGHT_CENSORED_WITH_COVERAGE_GAPS = "NO_OBSERVED_TOUCH_RIGHT_CENSORED_WITH_COVERAGE_GAPS"
    NO_OBSERVED_TOUCH_COVERAGE_GAPS = "NO_OBSERVED_TOUCH_COVERAGE_GAPS"
    NO_OBSERVED_TOUCH_COVERAGE_UNASSESSED = "NO_OBSERVED_TOUCH_COVERAGE_UNASSESSED"


class DerivedViewStatus(Enum):
    AVAILABLE = "AVAILABLE"
    NO_POST_DECISION_ROWS = "NO_POST_DECISION_ROWS"
    NO_OBSERVED_TOUCH = "NO_OBSERVED_TOUCH"


@dataclass(frozen=True)
class FrozenCell:
    """Immutable tagged scalar; missing values never become neutral numeric values."""

    kind: FrozenCellKind
    value: str | bool | None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, FrozenCellKind):
            raise TrajectoryQueryError("invalid frozen cell kind")
        if self.kind is FrozenCellKind.MISSING:
            if self.value is not None:
                raise TrajectoryQueryError("missing cell must have no value")
        elif self.kind is FrozenCellKind.BOOLEAN:
            if not isinstance(self.value, bool):
                raise TrajectoryQueryError("boolean cell value required")
        elif not isinstance(self.value, str):
            raise TrajectoryQueryError("string-encoded frozen cell value required")

    def canonical_payload(self) -> dict[str, str | bool | None]:
        return {"kind": self.kind.value, "value": self.value}


def _decimal_literal(value: object, *, field: str) -> str:
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, (bool, np.bool_)):
        raise TrajectoryQueryError(f"boolean is not a numeric cell: {field}")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise TrajectoryQueryError(f"unsupported numeric cell: {field}") from exc
    if not number.is_finite():
        raise TrajectoryQueryError(f"non-finite numeric cell: {field}")
    if number == 0:
        return "0"
    return format(number.normalize(), "f")


def _freeze_cell(value: object, *, field: str) -> FrozenCell:
    if value is None or value is pd.NA or value is pd.NaT:
        return FrozenCell(FrozenCellKind.MISSING, None)
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return FrozenCell(FrozenCellKind.MISSING, None)
        if value.tz is None:
            raise TrajectoryQueryError(f"naive timestamp cell is forbidden: {field}")
        return FrozenCell(
            FrozenCellKind.TIMESTAMP_UTC_NS,
            str(int(value.tz_convert("UTC").value)),
        )
    if isinstance(value, pd.Timedelta):
        if pd.isna(value):
            return FrozenCell(FrozenCellKind.MISSING, None)
        return FrozenCell(FrozenCellKind.TIMEDELTA_NS, str(int(value.value)))
    if isinstance(value, np.generic):
        value = value.item()
    try:
        missing = bool(pd.isna(value))
    except (TypeError, ValueError):
        missing = False
    if missing:
        return FrozenCell(FrozenCellKind.MISSING, None)
    if isinstance(value, bool):
        return FrozenCell(FrozenCellKind.BOOLEAN, value)
    if isinstance(value, (int, float, np.number)):
        return FrozenCell(FrozenCellKind.NUMBER, _decimal_literal(value, field=field))
    if isinstance(value, str):
        return FrozenCell(FrozenCellKind.STRING, value)
    raise TrajectoryQueryError(f"unsupported immutable surface cell: {field}:{type(value).__name__}")


@dataclass(frozen=True)
class FrozenSurfaceTable:
    table_name: str
    columns: tuple[str, ...]
    index: tuple[FrozenCell, ...]
    rows: tuple[tuple[FrozenCell, ...], ...]
    content_hash: str

    def __post_init__(self) -> None:
        if not isinstance(self.table_name, str) or not self.table_name:
            raise TrajectoryQueryError("surface table name is required")
        if not isinstance(self.columns, tuple) or any(not isinstance(c, str) for c in self.columns):
            raise TrajectoryQueryError("surface table columns must be an immutable string tuple")
        if not isinstance(self.index, tuple) or any(not isinstance(c, FrozenCell) for c in self.index):
            raise TrajectoryQueryError("surface table index must be immutable")
        if not isinstance(self.rows, tuple) or any(
            not isinstance(row, tuple)
            or len(row) != len(self.columns)
            or any(not isinstance(cell, FrozenCell) for cell in row)
            for row in self.rows
        ):
            raise TrajectoryQueryError("surface table rows must be immutable and schema-aligned")
        if len(self.index) != len(self.rows):
            raise TrajectoryQueryError("surface table index/row count mismatch")
        if not _is_sha256(self.content_hash):
            raise TrajectoryQueryError("surface table content_hash must be SHA-256")
        if self.content_hash != _frozen_table_hash(
            self.table_name, self.columns, self.index, self.rows
        ):
            raise TrajectoryQueryError("surface table content hash mismatch")


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and _SHA256_RE.fullmatch(value) is not None


def _cell_payload(cell: FrozenCell) -> dict[str, str | bool | None]:
    return cell.canonical_payload()


def _frozen_table_hash(
    table_name: str,
    columns: tuple[str, ...],
    index: tuple[FrozenCell, ...],
    rows: tuple[tuple[FrozenCell, ...], ...],
) -> str:
    return canonical_sha256(
        domain="TRAJECTORY_FROZEN_ASOF_SURFACE_TABLE_V1",
        payload={
            "table_name": table_name,
            "columns": list(columns),
            "index": [_cell_payload(cell) for cell in index],
            "rows": [[_cell_payload(cell) for cell in row] for row in rows],
        },
    )


def _freeze_table(table_name: str, frame: pd.DataFrame) -> FrozenSurfaceTable:
    if not isinstance(frame, pd.DataFrame) or frame.columns.has_duplicates:
        raise TrajectoryQueryError(f"{table_name} must be a duplicate-free DataFrame")
    columns = tuple(str(column) for column in frame.columns.tolist())
    if len(set(columns)) != len(columns):
        raise TrajectoryQueryError(f"{table_name} column names are not uniquely representable")
    index = tuple(_freeze_cell(value, field=f"{table_name}.index") for value in frame.index.tolist())
    rows = tuple(
        tuple(_freeze_cell(value, field=f"{table_name}.{column}") for column, value in zip(columns, row))
        for row in frame.itertuples(index=False, name=None)
    )
    digest = _frozen_table_hash(table_name, columns, index, rows)
    return FrozenSurfaceTable(table_name, columns, index, rows, digest)


@dataclass(frozen=True)
class SurfaceDomainAvailability:
    domain: str
    status: AvailabilityStatus
    bound_surface_count: int

    def __post_init__(self) -> None:
        if not isinstance(self.domain, str) or not self.domain:
            raise TrajectoryQueryError("surface availability domain is required")
        if not isinstance(self.status, AvailabilityStatus):
            raise TrajectoryQueryError("invalid surface availability status")
        if (
            isinstance(self.bound_surface_count, bool)
            or not isinstance(self.bound_surface_count, int)
            or self.bound_surface_count < 0
        ):
            raise TrajectoryQueryError("bound_surface_count must be a nonnegative integer")
        if (self.status is AvailabilityStatus.AVAILABLE) != (self.bound_surface_count > 0):
            raise TrajectoryQueryError("surface availability/count contradiction")


@dataclass(frozen=True)
class AsOfSurfaceInstance:
    stable_binding_hash: str
    surface_family: str
    domain: str
    contract_version: str
    configuration_identity_hash: str
    boundary_key: InformationKey
    prefix_hash: str
    tables: tuple[FrozenSurfaceTable, ...]

    def __post_init__(self) -> None:
        for name in (
            "stable_binding_hash",
            "configuration_identity_hash",
            "prefix_hash",
        ):
            if not _is_sha256(getattr(self, name)):
                raise TrajectoryQueryError(f"{name} must be lowercase SHA-256 hex")
        if not all(isinstance(getattr(self, name), str) and getattr(self, name) for name in (
            "surface_family", "domain", "contract_version"
        )):
            raise TrajectoryQueryError("as-of surface identity fields are required")
        if not isinstance(self.boundary_key, InformationKey):
            raise TrajectoryQueryError("as-of surface boundary must be an InformationKey")
        if not isinstance(self.tables, tuple) or any(
            not isinstance(table, FrozenSurfaceTable) for table in self.tables
        ):
            raise TrajectoryQueryError("as-of surface tables must be immutable")
        if not self.tables:
            raise TrajectoryQueryError("available surface must expose at least one table")


_SUPPORTED_DOMAIN_SLOTS = (
    "VOLATILITY",
    "SESSION",
    "ORDER_FLOW_PROXY",
    "ABSORPTION_PROXY",
    "SHARED_STRUCTURE",
    "LIQUIDITY",
    "ORDER_BLOCK",
    "FVG",
    "DEALING_RANGE",
    "HTF_SCALE_RAW",
)


@dataclass(frozen=True)
class AsOfSurfaceView:
    case_id: str
    as_of_key: InformationKey
    surfaces: tuple[AsOfSurfaceInstance, ...]
    availability: tuple[SurfaceDomainAvailability, ...]
    view_hash: str

    def __post_init__(self) -> None:
        if not _is_sha256(self.case_id) or not _is_sha256(self.view_hash):
            raise TrajectoryQueryError("as-of view identity must be SHA-256")
        if not isinstance(self.as_of_key, InformationKey):
            raise TrajectoryQueryError("as-of key required")
        if not isinstance(self.surfaces, tuple) or any(
            not isinstance(surface, AsOfSurfaceInstance) for surface in self.surfaces
        ):
            raise TrajectoryQueryError("as-of surfaces must be immutable")
        if not isinstance(self.availability, tuple) or any(
            not isinstance(entry, SurfaceDomainAvailability) for entry in self.availability
        ):
            raise TrajectoryQueryError("as-of availability must be immutable")
        if tuple(sorted(self.surfaces, key=lambda surface: surface.stable_binding_hash)) != self.surfaces:
            raise TrajectoryQueryError("as-of surfaces must be canonically ordered")
        if any(
            surface.boundary_key != self.as_of_key
            or surface.boundary_key.timeline_id != self.as_of_key.timeline_id
            for surface in self.surfaces
        ):
            raise TrajectoryQueryError("as-of surface boundary does not match view key")
        if tuple(entry.domain for entry in self.availability) != _SUPPORTED_DOMAIN_SLOTS:
            raise TrajectoryQueryError("as-of availability slots are incomplete or unordered")
        for entry in self.availability:
            expected_count = sum(surface.domain == entry.domain for surface in self.surfaces)
            if entry.bound_surface_count != expected_count:
                raise TrajectoryQueryError("as-of availability count does not match supplied surfaces")
        expected = _asof_view_hash(self.case_id, self.as_of_key, self.surfaces, self.availability)
        if self.view_hash != expected:
            raise TrajectoryQueryError("as-of view hash mismatch")


def _surface_tables_at(surface: object, boundary_key: InformationKey) -> tuple[str, tuple[pd.DataFrame, ...]]:
    """Use public Stage 4 prefix projectors, then freeze only visible rows."""
    position = boundary_key.bar_position
    if isinstance(surface, s4a.Stage4ADomainSurface):
        binding = s4a.project_surface_prefix(surface=surface, boundary_key=boundary_key)
        frame = surface.surface.loc[:, list(surface.output_columns)].iloc[: position + 1]
        return binding.prefix_hash, (frame,)
    if isinstance(surface, s4b1.Stage4B1StructureSurface):
        binding = s4b1.project_structure_prefix(surface=surface, boundary_key=boundary_key)
        derived = tuple(surface.derived_2_1a) + tuple(surface.derived_2_1b) + tuple(surface.derived_2_1c)
        frame = surface.frame.loc[:, list(derived)].iloc[: position + 1]
        return binding.prefix_hash, (frame,)
    if isinstance(surface, s4b2.Stage4B2LiquiditySurface):
        binding = s4b2.project_domain_prefix(surface=surface, boundary_key=boundary_key)
        tables = _stage4b2_tables(surface, position, entity_position="source_confirmation_position", event_position="event_position")
        return binding.prefix_hash, tables
    if isinstance(surface, s4b2.Stage4B2OrderBlockSurface):
        binding = s4b2.project_domain_prefix(surface=surface, boundary_key=boundary_key)
        tables = _stage4b2_tables(surface, position, entity_position="creation_position", event_position="event_position")
        return binding.prefix_hash, tables
    if isinstance(surface, s4b2.Stage4B2FVGSurface):
        binding = s4b2.project_domain_prefix(surface=surface, boundary_key=boundary_key)
        tables = _stage4b2_tables(surface, position, entity_position="creation_position", event_position="event_position")
        return binding.prefix_hash, tables
    if isinstance(surface, s4b2.Stage4B2DealingRangeSurface):
        binding = s4b2.project_domain_prefix(surface=surface, boundary_key=boundary_key)
        tables = _stage4b2_tables(surface, position, entity_position="creation_position", event_position="creation_position")
        return binding.prefix_hash, tables
    if isinstance(surface, s4c.Stage4CHtfScaleSurface):
        binding = s4c.project_htf_scale_prefix(surface=surface, boundary_key=boundary_key)
        if "first_observed_asof_position" not in surface.bucket_frame.columns:
            raise TrajectoryQueryError("Stage 4C bucket availability field missing")
        positions = surface.bucket_frame["first_observed_asof_position"]
        if positions.isna().any():
            raise TrajectoryQueryError("Stage 4C bucket availability is unknown")
        bucket_prefix = surface.bucket_frame.loc[positions <= position].reset_index(drop=True)
        asof_prefix = surface.asof_bar_frame.iloc[: position + 1]
        return binding.prefix_hash, (asof_prefix, bucket_prefix)
    raise TrajectoryQueryError(f"unsupported Stage 4 surface type: {type(surface).__name__}")


def _stage4b2_tables(
    surface: object,
    position: int,
    *,
    entity_position: str,
    event_position: str,
) -> tuple[pd.DataFrame, ...]:
    def visible(frame: pd.DataFrame, column: str, label: str) -> pd.DataFrame:
        if column not in frame.columns:
            if len(frame) == 0:
                return frame.iloc[:0].reset_index(drop=True)
            raise TrajectoryQueryError(f"Stage 4B2 {label} availability field missing: {column}")
        if frame[column].isna().any():
            raise TrajectoryQueryError(f"Stage 4B2 {label} availability is unknown")
        return frame.loc[frame[column] <= position].reset_index(drop=True)

    return (
        surface.bar_frame.iloc[: position + 1],
        visible(surface.event_frame, event_position, "event"),
        visible(surface.normalized_entity_frame, entity_position, "entity"),
        visible(surface.normalized_event_frame, event_position, "normalized-event"),
    )


def _asof_view_hash(
    case_id: str,
    as_of_key: InformationKey,
    surfaces: tuple[AsOfSurfaceInstance, ...],
    availability: tuple[SurfaceDomainAvailability, ...],
) -> str:
    return canonical_sha256(
        domain="TRAJECTORY_ASOF_SURFACE_VIEW_V1",
        payload={
            "case_id": case_id,
            "as_of_key": as_of_key,
            "surfaces": [
                {
                    "stable_binding_hash": surface.stable_binding_hash,
                    "surface_family": surface.surface_family,
                    "domain": surface.domain,
                    "contract_version": surface.contract_version,
                    "configuration_identity_hash": surface.configuration_identity_hash,
                    "boundary_key": surface.boundary_key,
                    "prefix_hash": surface.prefix_hash,
                    "tables": [table.content_hash for table in surface.tables],
                }
                for surface in surfaces
            ],
            "availability": [
                {
                    "domain": item.domain,
                    "status": item.status.value,
                    "bound_surface_count": item.bound_surface_count,
                }
                for item in availability
            ],
        },
    )


def create_asof_surface_view(
    *,
    case: TrajectoryDecisionCase,
    surfaces: Iterable[object],
    as_of_key: InformationKey,
) -> AsOfSurfaceView:
    """Build a fresh immutable as-of view; no later rows are copied into it.

    All surface bindings frozen into the case must be supplied and re-verified.
    Missing known domains are returned explicitly as ``NOT_SUPPLIED`` rather
    than silently filled or merged. Full surface/timeline IDs are omitted from
    this view because they can depend on data after ``as_of_key``.
    """
    if not isinstance(case, TrajectoryDecisionCase):
        raise TypeError("case must be a TrajectoryDecisionCase")
    if not isinstance(as_of_key, InformationKey):
        raise TypeError("as_of_key must be an InformationKey")
    if as_of_key.timeline_id != case.timeline_id:
        raise TrajectoryQueryError("as-of key belongs to another timeline")
    if as_of_key.information_phase not in _LEGAL_QUERY_PHASES:
        raise TrajectoryQueryError("as-of surface view requires a completed-row boundary")
    if as_of_key < case.decision_key:
        raise TrajectoryQueryError("a frozen decision case cannot be projected backward before its boundary")
    supplied_inputs = tuple(surfaces)
    # Capture all surfaces before running any public verifier/projector. Every
    # subsequent operation uses only these private snapshots.
    try:
        supplied = tuple(snapshot_stage4_surface(surface) for surface in supplied_inputs)
    except TrajectoryCaseError as exc:
        raise TrajectoryQueryError(f"cannot capture Stage 4 surface snapshot: {exc}") from exc
    if not supplied and as_of_key != case.decision_key:
        raise TrajectoryQueryError("cannot verify a non-decision as-of key without a bound surface")

    case_bindings = {binding.stable_binding_hash: binding for binding in case.surface_prefix_bindings}
    matched: dict[str, tuple[object, SurfacePrefixBinding]] = {}
    for surface in supplied:
        try:
            decision_binding = _verify_surface_prefix_snapshot(
                case=case,
                surface_snapshot=surface,
                source_through_position=as_of_key.bar_position,
            )
        except TrajectoryCaseError as exc:
            raise TrajectoryQueryError(str(exc)) from exc
        stable_hash = decision_binding.stable_binding_hash
        if stable_hash not in case_bindings:
            raise TrajectoryQueryError("unbound surface cannot be added to a frozen case view")
        if stable_hash in matched:
            raise TrajectoryQueryError("duplicate surface supplied to as-of view")
        matched[stable_hash] = (surface, case_bindings[stable_hash])
    if set(matched) != set(case_bindings):
        raise TrajectoryQueryError("one or more case-bound surfaces are unavailable")

    instances = []
    for stable_hash in sorted(matched):
        surface, binding = matched[stable_hash]
        prefix_hash, frames = _surface_tables_at(surface, as_of_key)
        if as_of_key == case.decision_key and prefix_hash != binding.prefix_hash:
            raise TrajectoryQueryError("decision prefix projection changed within captured Stage 4 snapshot")
        frozen_tables = tuple(
            _freeze_table(f"{binding.domain}:{index}", frame)
            for index, frame in enumerate(frames)
        )
        instances.append(
            AsOfSurfaceInstance(
                stable_binding_hash=stable_hash,
                surface_family=binding.surface_family,
                domain=binding.domain,
                contract_version=binding.contract_version,
                configuration_identity_hash=binding.configuration_identity_hash,
                boundary_key=as_of_key,
                prefix_hash=prefix_hash,
                tables=frozen_tables,
            )
        )
    surface_tuple = tuple(instances)
    available_counts = {
        domain: sum(1 for instance in surface_tuple if instance.domain == domain)
        for domain in _SUPPORTED_DOMAIN_SLOTS
    }
    availability = tuple(
        SurfaceDomainAvailability(
            domain=domain,
            status=(
                AvailabilityStatus.AVAILABLE
                if available_counts[domain]
                else AvailabilityStatus.NOT_SUPPLIED
            ),
            bound_surface_count=available_counts[domain],
        )
        for domain in _SUPPORTED_DOMAIN_SLOTS
    )
    view_hash = _asof_view_hash(case.case_id, as_of_key, surface_tuple, availability)
    return AsOfSurfaceView(
        case_id=case.case_id,
        as_of_key=as_of_key,
        surfaces=surface_tuple,
        availability=availability,
        view_hash=view_hash,
    )


def decision_surface_view(
    *, case: TrajectoryDecisionCase, surfaces: Iterable[object]
) -> AsOfSurfaceView:
    """Return exactly the case decision-time surface view (never a path input)."""
    return create_asof_surface_view(
        case=case,
        surfaces=surfaces,
        as_of_key=case.decision_key,
    )


@dataclass(frozen=True)
class HorizonPolicyIdentity:
    policy_id: str
    policy_version: str
    policy_sha256: str

    def __post_init__(self) -> None:
        _require_text(self.policy_id, "horizon policy_id")
        _require_text(self.policy_version, "horizon policy_version")
        _require_hash(self.policy_sha256, "horizon policy_sha256")


@dataclass(frozen=True)
class SamplingPolicyIdentity:
    policy_id: str
    policy_version: str
    policy_sha256: str

    def __post_init__(self) -> None:
        _require_text(self.policy_id, "sampling policy_id")
        _require_text(self.policy_version, "sampling policy_version")
        _require_hash(self.policy_sha256, "sampling policy_sha256")


def _require_text(value: object, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise TrajectoryQueryError(f"{field} must be a nonempty string")


def _require_hash(value: object, field: str) -> None:
    if not _is_sha256(value):
        raise TrajectoryQueryError(f"{field} must be lowercase SHA-256 hex")


def _policy_payload(policy: HorizonPolicyIdentity | SamplingPolicyIdentity) -> dict[str, str]:
    return {
        "policy_id": policy.policy_id,
        "policy_version": policy.policy_version,
        "policy_sha256": policy.policy_sha256,
    }


@dataclass(frozen=True)
class HorizonRequest:
    """An opaque policy identity plus a caller-supplied exact end boundary."""

    policy_identity: HorizonPolicyIdentity
    requested_end_key: InformationKey

    def __post_init__(self) -> None:
        if not isinstance(self.policy_identity, HorizonPolicyIdentity):
            raise TrajectoryQueryError("HorizonPolicyIdentity is required")
        if not isinstance(self.requested_end_key, InformationKey):
            raise TrajectoryQueryError("explicit requested_end_key is required")
        if self.requested_end_key.information_phase not in _LEGAL_QUERY_PHASES:
            raise TrajectoryQueryError("requested horizon end must be a completed-row boundary")

    @property
    def identity_hash(self) -> str:
        return canonical_sha256(
            domain="TRAJECTORY_HORIZON_REQUEST_ID_V1",
            payload={
                "policy_identity": _policy_payload(self.policy_identity),
                "requested_end_key": self.requested_end_key,
            },
        )


@dataclass(frozen=True)
class QueryProtocolIdentity:
    query_contract_type: str
    query_contract_version: str
    protocol_id: str
    protocol_version: str
    protocol_sha256: str
    canonical_parameters: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        for field in (
            "query_contract_type",
            "query_contract_version",
            "protocol_id",
            "protocol_version",
        ):
            _require_text(getattr(self, field), field)
        _require_hash(self.protocol_sha256, "protocol_sha256")
        if not isinstance(self.canonical_parameters, tuple) or any(
            not isinstance(item, tuple)
            or len(item) != 2
            or not isinstance(item[0], str)
            or not item[0]
            or not isinstance(item[1], str)
            for item in self.canonical_parameters
        ):
            raise TrajectoryQueryError("canonical_parameters must be immutable name/value string pairs")
        if tuple(sorted(self.canonical_parameters)) != self.canonical_parameters:
            raise TrajectoryQueryError("canonical_parameters must be sorted by parameter name")
        if len({name for name, _ in self.canonical_parameters}) != len(self.canonical_parameters):
            raise TrajectoryQueryError("canonical_parameters contain duplicate names")

    @property
    def identity_hash(self) -> str:
        return canonical_sha256(
            domain="TRAJECTORY_QUERY_PROTOCOL_ID_V1",
            payload={
                "query_contract_type": self.query_contract_type,
                "query_contract_version": self.query_contract_version,
                "protocol_id": self.protocol_id,
                "protocol_version": self.protocol_version,
                "protocol_sha256": self.protocol_sha256,
                "canonical_parameters": [list(item) for item in self.canonical_parameters],
            },
        )


class SamplingMembershipState(Enum):
    INCLUDED = "INCLUDED"
    EXCLUDED = "EXCLUDED"


@dataclass(frozen=True)
class SamplingAlgorithmIdentity:
    algorithm_id: str
    algorithm_version: str
    algorithm_sha256: str

    def __post_init__(self) -> None:
        _require_text(self.algorithm_id, "sampling algorithm_id")
        _require_text(self.algorithm_version, "sampling algorithm_version")
        _require_hash(self.algorithm_sha256, "sampling algorithm_sha256")


@dataclass(frozen=True)
class SamplingMembershipReference:
    case_id: str
    policy_identity: SamplingPolicyIdentity
    candidate_universe_id: str
    candidate_universe_sha256: str
    selection_run_id: str
    membership_id: str
    membership_role: str
    selection_key: InformationKey
    state: SamplingMembershipState
    rationale_reference: str
    deterministic_seed: str | int | None
    algorithm_identity: SamplingAlgorithmIdentity | None
    paired_control_reference: str | None
    attrition_rejection_reference: str | None
    identity_hash: str

    @property
    def membership_key(self) -> InformationKey:
        """Compatibility spelling for the recorded selection key."""
        return self.selection_key

    def __post_init__(self) -> None:
        _require_hash(self.case_id, "sampling case_id")
        if not isinstance(self.policy_identity, SamplingPolicyIdentity):
            raise TrajectoryQueryError("sampling protocol identity required")
        _require_text(self.candidate_universe_id, "candidate_universe_id")
        _require_hash(self.candidate_universe_sha256, "candidate_universe_sha256")
        _require_text(self.selection_run_id, "selection_run_id")
        _require_text(self.membership_id, "membership_id")
        _require_text(self.membership_role, "membership_role")
        if not isinstance(self.selection_key, InformationKey):
            raise TrajectoryQueryError("selection_key is required")
        if not isinstance(self.state, SamplingMembershipState):
            raise TrajectoryQueryError("sampling membership state is required")
        _require_text(self.rationale_reference, "rationale_reference")
        if isinstance(self.deterministic_seed, bool) or not isinstance(
            self.deterministic_seed, (str, int, type(None))
        ):
            raise TrajectoryQueryError("deterministic_seed must be a string, integer, or None")
        if self.deterministic_seed == "":
            raise TrajectoryQueryError("deterministic_seed must be nonempty when supplied")
        if self.algorithm_identity is not None and not isinstance(
            self.algorithm_identity, SamplingAlgorithmIdentity
        ):
            raise TrajectoryQueryError("algorithm_identity must be SamplingAlgorithmIdentity or None")
        for field in ("paired_control_reference", "attrition_rejection_reference"):
            value = getattr(self, field)
            if value is not None:
                _require_text(value, field)
        _require_hash(self.identity_hash, "sampling membership identity_hash")
        expected = _sampling_membership_hash(
            case_id=self.case_id,
            policy_identity=self.policy_identity,
            candidate_universe_id=self.candidate_universe_id,
            candidate_universe_sha256=self.candidate_universe_sha256,
            selection_run_id=self.selection_run_id,
            membership_id=self.membership_id,
            membership_role=self.membership_role,
            selection_key=self.selection_key,
            state=self.state,
            rationale_reference=self.rationale_reference,
            deterministic_seed=self.deterministic_seed,
            algorithm_identity=self.algorithm_identity,
            paired_control_reference=self.paired_control_reference,
            attrition_rejection_reference=self.attrition_rejection_reference,
        )
        if self.identity_hash != expected:
            raise TrajectoryQueryError("sampling membership identity mismatch")


def _sampling_membership_hash(
    *,
    case_id: str,
    policy_identity: SamplingPolicyIdentity,
    candidate_universe_id: str,
    candidate_universe_sha256: str,
    selection_run_id: str,
    membership_id: str,
    membership_role: str,
    selection_key: InformationKey,
    state: SamplingMembershipState,
    rationale_reference: str,
    deterministic_seed: str | int | None,
    algorithm_identity: SamplingAlgorithmIdentity | None,
    paired_control_reference: str | None,
    attrition_rejection_reference: str | None,
) -> str:
    return canonical_sha256(
        domain="TRAJECTORY_SAMPLING_MEMBERSHIP_REF_V2",
        payload={
            "case_id": case_id,
            "sampling_protocol": _policy_payload(policy_identity),
            "candidate_universe_id": candidate_universe_id,
            "candidate_universe_sha256": candidate_universe_sha256,
            "selection_run_id": selection_run_id,
            "membership_id": membership_id,
            "membership_role": membership_role,
            "selection_key": selection_key,
            "state": state.value,
            "rationale_reference": rationale_reference,
            "deterministic_seed": deterministic_seed,
            "algorithm_identity": (
                None
                if algorithm_identity is None
                else {
                    "algorithm_id": algorithm_identity.algorithm_id,
                    "algorithm_version": algorithm_identity.algorithm_version,
                    "algorithm_sha256": algorithm_identity.algorithm_sha256,
                }
            ),
            "paired_control_reference": paired_control_reference,
            "attrition_rejection_reference": attrition_rejection_reference,
        },
    )


def bind_sampling_membership(
    *,
    case: TrajectoryDecisionCase,
    policy_identity: SamplingPolicyIdentity,
    candidate_universe_id: str,
    candidate_universe_sha256: str,
    selection_run_id: str,
    membership_id: str,
    membership_role: str,
    selection_key: InformationKey,
    state: SamplingMembershipState,
    rationale_reference: str,
    deterministic_seed: str | int | None = None,
    algorithm_identity: SamplingAlgorithmIdentity | None = None,
    paired_control_reference: str | None = None,
    attrition_rejection_reference: str | None = None,
) -> SamplingMembershipReference:
    """Record externally determined membership metadata; no path/outcome is accepted.

    These references support auditing but do not prove future-blind selection or
    absence of selection bias.
    """
    if not isinstance(case, TrajectoryDecisionCase):
        raise TypeError("case must be a TrajectoryDecisionCase")
    if not isinstance(policy_identity, SamplingPolicyIdentity):
        raise TypeError("policy_identity must be a SamplingPolicyIdentity")
    if not isinstance(selection_key, InformationKey):
        raise TypeError("selection_key must be an InformationKey")
    if not isinstance(state, SamplingMembershipState):
        raise TypeError("state must be a SamplingMembershipState")
    if selection_key.timeline_id != case.timeline_id:
        raise TrajectoryQueryError("sampling membership timeline mismatch")
    if selection_key > case.decision_key:
        raise TrajectoryQueryError("sampling membership was not available by the decision key")
    identity_fields = {
        "case_id": case.case_id,
        "policy_identity": policy_identity,
        "candidate_universe_id": candidate_universe_id,
        "candidate_universe_sha256": candidate_universe_sha256,
        "selection_run_id": selection_run_id,
        "membership_id": membership_id,
        "membership_role": membership_role,
        "selection_key": selection_key,
        "state": state,
        "rationale_reference": rationale_reference,
        "deterministic_seed": deterministic_seed,
        "algorithm_identity": algorithm_identity,
        "paired_control_reference": paired_control_reference,
        "attrition_rejection_reference": attrition_rejection_reference,
    }
    identity = _sampling_membership_hash(**identity_fields)
    return SamplingMembershipReference(identity_hash=identity, **identity_fields)


@dataclass(frozen=True)
class ProjectedTargetReference:
    candidate_id: str
    projection_id: str
    projection_sha256: str
    projected_price: float
    available_at: InformationKey

    def __post_init__(self) -> None:
        _require_text(self.candidate_id, "projected target candidate_id")
        _require_text(self.projection_id, "projected target projection_id")
        _require_hash(self.projection_sha256, "projected target projection_sha256")
        object.__setattr__(self, "projected_price", _finite_price(self.projected_price, "projected_price"))
        if not isinstance(self.available_at, InformationKey):
            raise TrajectoryQueryError("projected target availability key required")

    @property
    def identity_hash(self) -> str:
        return canonical_sha256(
            domain="PROJECTED_TARGET_REFERENCE_V1",
            payload={
                "candidate_id": self.candidate_id,
                "projection_id": self.projection_id,
                "projection_sha256": self.projection_sha256,
                "projected_price": self.projected_price,
                "available_at": self.available_at,
            },
        )


@dataclass(frozen=True)
class ProjectedInvalidationReference:
    candidate_id: str
    projection_id: str
    projection_sha256: str
    projected_price: float
    available_at: InformationKey

    def __post_init__(self) -> None:
        _require_text(self.candidate_id, "projected invalidation candidate_id")
        _require_text(self.projection_id, "projected invalidation projection_id")
        _require_hash(self.projection_sha256, "projected invalidation projection_sha256")
        object.__setattr__(self, "projected_price", _finite_price(self.projected_price, "projected_price"))
        if not isinstance(self.available_at, InformationKey):
            raise TrajectoryQueryError("projected invalidation availability key required")

    @property
    def identity_hash(self) -> str:
        return canonical_sha256(
            domain="PROJECTED_INVALIDATION_REFERENCE_V1",
            payload={
                "candidate_id": self.candidate_id,
                "projection_id": self.projection_id,
                "projection_sha256": self.projection_sha256,
                "projected_price": self.projected_price,
                "available_at": self.available_at,
            },
        )


@dataclass(frozen=True)
class ObservedEntityLocator:
    """Caller locator only; all factual attributes are resolved from Stage4B2."""

    producer_domain: str
    stable_binding_hash: str
    canonical_entity_id: str

    def __post_init__(self) -> None:
        _require_text(self.producer_domain, "producer_domain")
        _require_hash(self.stable_binding_hash, "stable_binding_hash")
        _require_text(self.canonical_entity_id, "canonical_entity_id")
        if self.producer_domain == "MARKET_TIMELINE":
            raise TrajectoryQueryError("MARKET_TIMELINE is not an observed producer-entity domain")

    @property
    def identity_hash(self) -> str:
        return canonical_sha256(
            domain="TRAJECTORY_OBSERVED_ENTITY_LOCATOR_V1",
            payload={
                "producer_domain": self.producer_domain,
                "stable_binding_hash": self.stable_binding_hash,
                "canonical_entity_id": self.canonical_entity_id,
            },
        )


# The previous public spelling now names a locator only; it accepts no price or
# availability assertions from the caller.
ObservedTargetReference = ObservedEntityLocator


@dataclass(frozen=True)
class ResolvedProducerEntity:
    locator: ObservedEntityLocator
    contract_version: str
    row_columns: tuple[str, ...]
    row: tuple[FrozenCell, ...]
    canonical_row_sha256: str
    identity_hash: str
    canonical_price: float | None
    lower_bound: float | None
    upper_bound: float | None
    side_or_direction: str
    origin_positions: tuple[int, ...]
    creation_position: int | None
    confirmation_positions: tuple[int, ...]
    availability_position: int

    def __post_init__(self) -> None:
        if not isinstance(self.locator, ObservedEntityLocator):
            raise TrajectoryQueryError("resolved producer entity locator required")
        _require_text(self.contract_version, "resolved entity contract_version")
        _require_hash(self.canonical_row_sha256, "canonical_row_sha256")
        _require_hash(self.identity_hash, "resolved entity identity_hash")
        if not isinstance(self.row_columns, tuple) or any(not isinstance(c, str) for c in self.row_columns):
            raise TrajectoryQueryError("resolved producer row columns must be immutable")
        if not isinstance(self.row, tuple) or len(self.row) != len(self.row_columns) or any(
            not isinstance(cell, FrozenCell) for cell in self.row
        ):
            raise TrajectoryQueryError("resolved producer row must be frozen and schema-aligned")
        _require_text(self.side_or_direction, "side_or_direction")
        if not isinstance(self.origin_positions, tuple) or any(
            isinstance(position, bool) or not isinstance(position, int) or position < 0
            for position in self.origin_positions
        ):
            raise TrajectoryQueryError("origin_positions must be immutable nonnegative positions")
        if not isinstance(self.confirmation_positions, tuple) or any(
            isinstance(position, bool) or not isinstance(position, int) or position < 0
            for position in self.confirmation_positions
        ):
            raise TrajectoryQueryError("confirmation_positions must be immutable nonnegative positions")
        for field in ("creation_position", "availability_position"):
            position = getattr(self, field)
            if field == "creation_position" and position is None:
                continue
            if isinstance(position, bool) or not isinstance(position, int) or position < 0:
                raise TrajectoryQueryError(f"{field} must be a nonnegative position")
        for field in ("canonical_price", "lower_bound", "upper_bound"):
            value = getattr(self, field)
            if value is not None:
                object.__setattr__(self, field, _finite_price(value, field))
        if (self.canonical_price is None) == (self.lower_bound is None or self.upper_bound is None):
            raise TrajectoryQueryError("resolved entity must have exactly a point price or a bounds pair")
        if self.lower_bound is not None and self.upper_bound is not None and self.lower_bound > self.upper_bound:
            raise TrajectoryQueryError("resolved entity bounds are inverted")
        expected_row_hash = canonical_sha256(
            domain="TRAJECTORY_STAGE4B2_RESOLVED_ENTITY_ROW_V1",
            payload={
                "stable_binding_hash": self.locator.stable_binding_hash,
                "producer_domain": self.locator.producer_domain,
                "canonical_entity_id": self.locator.canonical_entity_id,
                "columns": list(self.row_columns),
                "row": [_cell_payload(cell) for cell in self.row],
            },
        )
        if self.canonical_row_sha256 != expected_row_hash:
            raise TrajectoryQueryError("resolved producer row hash mismatch")
        expected_identity = canonical_sha256(
            domain="TRAJECTORY_RESOLVED_PRODUCER_ENTITY_ID_V1",
            payload={
                "stable_binding_hash": self.locator.stable_binding_hash,
                "producer_domain": self.locator.producer_domain,
                "canonical_entity_id": self.locator.canonical_entity_id,
                "canonical_row_sha256": self.canonical_row_sha256,
            },
        )
        if self.identity_hash != expected_identity:
            raise TrajectoryQueryError("resolved producer entity identity mismatch")


def _frozen_cell_number(cell: FrozenCell, *, field: str) -> float:
    if cell.kind is not FrozenCellKind.NUMBER or not isinstance(cell.value, str):
        raise TrajectoryQueryError(f"producer entity {field} is not a numeric fact")
    try:
        value = float(Decimal(cell.value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise TrajectoryQueryError(f"producer entity {field} is not a valid number") from exc
    return _finite_price(value, field)


def _frozen_cell_position(cell: FrozenCell, *, field: str) -> int:
    value = _frozen_cell_number(cell, field=field)
    if not value.is_integer() or value < 0:
        raise TrajectoryQueryError(f"producer entity {field} is not a nonnegative integer position")
    return int(value)


_OBSERVED_ENTITY_CONTRACTS = {
    "LIQUIDITY": {
        "id_column": "level_id",
        "availability_column": "source_confirmation_position",
        "point_price_column": "immutable_level_price",
        "bounds_columns": None,
        "side_column": "side",
        "origin_columns": ("source_origin_position",),
        "creation_column": None,
        "confirmation_columns": ("source_confirmation_position",),
    },
    "ORDER_BLOCK": {
        "id_column": "zone_id",
        "availability_column": "creation_position",
        "point_price_column": None,
        "bounds_columns": ("full_zone_low", "full_zone_high"),
        "side_column": "direction",
        "origin_columns": ("origin_position",),
        "creation_column": "creation_position",
        "confirmation_columns": (),
    },
    "FVG": {
        "id_column": "fvg_id",
        "availability_column": "creation_position",
        "point_price_column": None,
        "bounds_columns": ("zone_low", "zone_high"),
        "side_column": "direction",
        "origin_columns": ("origin_position",),
        "creation_column": "creation_position",
        "confirmation_columns": (),
    },
    "DEALING_RANGE": {
        "id_column": "range_id",
        "availability_column": "creation_position",
        "point_price_column": None,
        "bounds_columns": ("range_low", "range_high"),
        "side_column": "direction",
        "origin_columns": ("first_endpoint_origin_position", "second_endpoint_origin_position"),
        "creation_column": "creation_position",
        "confirmation_columns": (
            "first_endpoint_confirmation_position",
            "second_endpoint_confirmation_position",
        ),
    },
}


SUPPORTED_OBSERVED_PRODUCER_DOMAINS = tuple(_OBSERVED_ENTITY_CONTRACTS)


def resolve_observed_entity(
    *,
    case: TrajectoryDecisionCase,
    surfaces: Iterable[object],
    locator: ObservedEntityLocator,
) -> ResolvedProducerEntity:
    """Resolve only from the frozen, verified Stage4B2 decision-prefix rows."""
    if not isinstance(case, TrajectoryDecisionCase):
        raise TypeError("case must be a TrajectoryDecisionCase")
    if not isinstance(locator, ObservedEntityLocator):
        raise TypeError("ObservedEntityLocator required")
    contract = _OBSERVED_ENTITY_CONTRACTS.get(locator.producer_domain)
    if contract is None:
        raise TrajectoryQueryError(
            f"unsupported observed producer domain: {locator.producer_domain}"
        )
    matching_bindings = [
        binding
        for binding in case.surface_prefix_bindings
        if binding.domain == locator.producer_domain
        and binding.stable_binding_hash == locator.stable_binding_hash
    ]
    if len(matching_bindings) != 1:
        raise TrajectoryQueryError("entity locator is not bound to exactly one case decision prefix")

    # decision_surface_view captures Stage4 inputs before verification and freezes
    # the exact rows used by the public Stage4 prefix projector.
    view = decision_surface_view(case=case, surfaces=surfaces)
    instances = [
        instance
        for instance in view.surfaces
        if instance.domain == locator.producer_domain
        and instance.stable_binding_hash == locator.stable_binding_hash
    ]
    if len(instances) != 1:
        raise TrajectoryQueryError("verified Stage4B2 surface is unavailable or ambiguous")
    instance = instances[0]
    if instance.surface_family != "STAGE4B2" or len(instance.tables) < 3:
        raise TrajectoryQueryError("observed entity source is not a Stage4B2 entity surface")
    entity_table = instance.tables[2]
    if entity_table.table_name != f"{locator.producer_domain}:2":
        raise TrajectoryQueryError("verified Stage4B2 normalized entity table is missing")
    column_index = {name: index for index, name in enumerate(entity_table.columns)}
    required_columns = {
        contract["id_column"],
        contract["availability_column"],
        contract["side_column"],
        *contract["origin_columns"],
        *contract["confirmation_columns"],
    }
    if contract["point_price_column"] is not None:
        required_columns.add(contract["point_price_column"])
    if contract["creation_column"] is not None:
        required_columns.add(contract["creation_column"])
    if contract["bounds_columns"] is not None:
        required_columns.update(contract["bounds_columns"])
    if not required_columns.issubset(column_index):
        raise TrajectoryQueryError("verified producer entity row does not satisfy its fixed domain schema")

    id_index = column_index[contract["id_column"]]
    matches = [
        row
        for row in entity_table.rows
        if row[id_index].kind in (FrozenCellKind.STRING, FrozenCellKind.NUMBER)
        and row[id_index].value == locator.canonical_entity_id
    ]
    if len(matches) != 1:
        raise TrajectoryQueryError(
            "canonical producer entity ID must resolve to exactly one decision-visible row"
        )
    row = matches[0]
    availability_position = _frozen_cell_position(
        row[column_index[contract["availability_column"]]],
        field=contract["availability_column"],
    )
    if availability_position > case.decision_key.bar_position:
        raise TrajectoryQueryError("producer entity was unavailable at the decision boundary")

    side_cell = row[column_index[contract["side_column"]]]
    if side_cell.kind is not FrozenCellKind.STRING or not isinstance(side_cell.value, str):
        raise TrajectoryQueryError("producer side/direction is not a resolved string fact")
    origin_positions = tuple(
        _frozen_cell_position(row[column_index[name]], field=name)
        for name in contract["origin_columns"]
    )
    creation_position = (
        None
        if contract["creation_column"] is None
        else _frozen_cell_position(row[column_index[contract["creation_column"]]], field=contract["creation_column"])
    )
    confirmation_positions = tuple(
        _frozen_cell_position(row[column_index[name]], field=name)
        for name in contract["confirmation_columns"]
    )
    canonical_price = None
    lower_bound = upper_bound = None
    if contract["point_price_column"] is not None:
        canonical_price = _frozen_cell_number(
            row[column_index[contract["point_price_column"]]],
            field=contract["point_price_column"],
        )
    else:
        low_column, high_column = contract["bounds_columns"]
        lower_bound = _frozen_cell_number(row[column_index[low_column]], field=low_column)
        upper_bound = _frozen_cell_number(row[column_index[high_column]], field=high_column)
        if lower_bound > upper_bound:
            raise TrajectoryQueryError("producer entity bounds are inverted")

    row_hash = canonical_sha256(
        domain="TRAJECTORY_STAGE4B2_RESOLVED_ENTITY_ROW_V1",
        payload={
            "stable_binding_hash": locator.stable_binding_hash,
            "producer_domain": locator.producer_domain,
            "canonical_entity_id": locator.canonical_entity_id,
            "columns": list(entity_table.columns),
            "row": [_cell_payload(cell) for cell in row],
        },
    )
    identity_hash = canonical_sha256(
        domain="TRAJECTORY_RESOLVED_PRODUCER_ENTITY_ID_V1",
        payload={
            "stable_binding_hash": locator.stable_binding_hash,
            "producer_domain": locator.producer_domain,
            "canonical_entity_id": locator.canonical_entity_id,
            "canonical_row_sha256": row_hash,
        },
    )
    return ResolvedProducerEntity(
        locator=locator,
        contract_version=instance.contract_version,
        row_columns=entity_table.columns,
        row=row,
        canonical_row_sha256=row_hash,
        identity_hash=identity_hash,
        canonical_price=canonical_price,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        side_or_direction=side_cell.value,
        origin_positions=origin_positions,
        creation_position=creation_position,
        confirmation_positions=confirmation_positions,
        availability_position=availability_position,
    )


def _finite_price(value: object, field: str) -> float:
    if isinstance(value, (bool, np.bool_)):
        raise TrajectoryQueryError(f"{field} must be a finite numeric value")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise TrajectoryQueryError(f"{field} must be a finite numeric value") from exc
    if not math.isfinite(result):
        raise TrajectoryQueryError(f"{field} must be finite")
    return result


@dataclass(frozen=True)
class CandidatePricePair:
    candidate_pair_id: str
    projected_target: ProjectedTargetReference
    projected_invalidation: ProjectedInvalidationReference

    def __post_init__(self) -> None:
        _require_text(self.candidate_pair_id, "candidate_pair_id")
        if not isinstance(self.projected_target, ProjectedTargetReference):
            raise TrajectoryQueryError("projected target reference required")
        if not isinstance(self.projected_invalidation, ProjectedInvalidationReference):
            raise TrajectoryQueryError("projected invalidation reference required")
        if self.projected_target.candidate_id != self.projected_invalidation.candidate_id:
            raise TrajectoryQueryError("candidate pair references must share candidate identity")

    @property
    def identity_hash(self) -> str:
        return canonical_sha256(
            domain="CANDIDATE_PRICE_PAIR_REFERENCE_V1",
            payload={
                "candidate_pair_id": self.candidate_pair_id,
                "projected_target_identity": self.projected_target.identity_hash,
                "projected_invalidation_identity": self.projected_invalidation.identity_hash,
            },
        )


@dataclass(frozen=True)
class TrajectoryQueryReference:
    case_id: str
    protocol_identity: QueryProtocolIdentity
    horizon_request: HorizonRequest
    candidate_pair_identity: str | None
    sampling_membership_identity: str | None
    study_identity: str | None
    observed_entity_identity: str | None
    query_id: str

    def __post_init__(self) -> None:
        _require_hash(self.case_id, "query case_id")
        if not isinstance(self.protocol_identity, QueryProtocolIdentity):
            raise TrajectoryQueryError("explicit QueryProtocolIdentity required")
        if not isinstance(self.horizon_request, HorizonRequest):
            raise TrajectoryQueryError("explicit HorizonRequest required")
        for field in (
            "candidate_pair_identity",
            "sampling_membership_identity",
            "study_identity",
            "observed_entity_identity",
        ):
            value = getattr(self, field)
            if value is not None:
                _require_hash(value, field)
        _require_hash(self.query_id, "query_id")
        expected = _query_id(
            case_id=self.case_id,
            protocol_identity=self.protocol_identity,
            horizon_request=self.horizon_request,
            candidate_pair_identity=self.candidate_pair_identity,
            sampling_membership_identity=self.sampling_membership_identity,
            study_identity=self.study_identity,
            observed_entity_identity=self.observed_entity_identity,
        )
        if self.query_id != expected:
            raise TrajectoryQueryError("query identity mismatch")


def _query_id(
    *,
    case_id: str,
    protocol_identity: QueryProtocolIdentity,
    horizon_request: HorizonRequest,
    candidate_pair_identity: str | None,
    sampling_membership_identity: str | None,
    study_identity: str | None,
    observed_entity_identity: str | None,
) -> str:
    return canonical_sha256(
        domain="TRAJECTORY_QUERY_ID_V2",
        payload={
            "case_id": case_id,
            "query_protocol_identity": protocol_identity.identity_hash,
            "horizon_request_identity": horizon_request.identity_hash,
            "candidate_pair_identity": candidate_pair_identity,
            "sampling_membership_identity": sampling_membership_identity,
            "study_identity": study_identity,
            "observed_entity_identity": observed_entity_identity,
        },
    )


def create_trajectory_query_reference(
    *,
    case: TrajectoryDecisionCase,
    protocol_identity: QueryProtocolIdentity,
    horizon_request: HorizonRequest,
    candidate_pair: CandidatePricePair | None,
    sampling_membership: SamplingMembershipReference | None,
    study_identity: str | None = None,
    observed_entity: ObservedEntityLocator | None = None,
) -> TrajectoryQueryReference:
    """Bind question-defining identities without observing a future answer."""
    if not isinstance(case, TrajectoryDecisionCase):
        raise TypeError("case must be a TrajectoryDecisionCase")
    if not isinstance(protocol_identity, QueryProtocolIdentity):
        raise TypeError("protocol_identity must be a QueryProtocolIdentity")
    if study_identity is not None:
        _require_hash(study_identity, "study_identity")
    if observed_entity is not None:
        if not isinstance(observed_entity, ObservedEntityLocator):
            raise TypeError("observed_entity must be an ObservedEntityLocator or None")
        if not any(
            binding.domain == observed_entity.producer_domain
            and binding.stable_binding_hash == observed_entity.stable_binding_hash
            for binding in case.surface_prefix_bindings
        ):
            raise TrajectoryQueryError("observed entity locator is not bound to this case")
    end_key = horizon_request.requested_end_key
    if end_key.timeline_id != case.timeline_id:
        raise TrajectoryQueryError("horizon end belongs to another timeline")
    if end_key.bar_position <= case.decision_key.bar_position:
        raise TrajectoryQueryError("trajectory interval must be (decision, end]")
    if candidate_pair is not None:
        if not isinstance(candidate_pair, CandidatePricePair):
            raise TypeError("candidate_pair must be a CandidatePricePair or None")
        for key in (
            candidate_pair.projected_target.available_at,
            candidate_pair.projected_invalidation.available_at,
        ):
            if key.timeline_id != case.timeline_id or key > case.decision_key:
                raise TrajectoryQueryError("candidate pair was not available at decision")
    if sampling_membership is not None:
        if not isinstance(sampling_membership, SamplingMembershipReference):
            raise TypeError("sampling_membership must be a SamplingMembershipReference or None")
        if sampling_membership.case_id != case.case_id:
            raise TrajectoryQueryError("sampling membership belongs to another case")
        if sampling_membership.membership_key.timeline_id != case.timeline_id:
            raise TrajectoryQueryError("sampling membership timeline mismatch")
        if sampling_membership.membership_key > case.decision_key:
            raise TrajectoryQueryError("sampling membership was not available by the decision key")
    pair_hash = None if candidate_pair is None else candidate_pair.identity_hash
    membership_hash = None if sampling_membership is None else sampling_membership.identity_hash
    entity_hash = None if observed_entity is None else observed_entity.identity_hash
    query_id = _query_id(
        case_id=case.case_id,
        protocol_identity=protocol_identity,
        horizon_request=horizon_request,
        candidate_pair_identity=pair_hash,
        sampling_membership_identity=membership_hash,
        study_identity=study_identity,
        observed_entity_identity=entity_hash,
    )
    return TrajectoryQueryReference(
        case_id=case.case_id,
        protocol_identity=protocol_identity,
        horizon_request=horizon_request,
        candidate_pair_identity=pair_hash,
        sampling_membership_identity=membership_hash,
        study_identity=study_identity,
        observed_entity_identity=entity_hash,
        query_id=query_id,
    )


@dataclass(frozen=True)
class CoverageContract:
    """Caller-declared coverage expectation; ``None`` means explicitly unassessed."""

    contract_id: str
    contract_version: str
    contract_sha256: str
    expected_step: pd.Timedelta | None

    def __post_init__(self) -> None:
        _require_text(self.contract_id, "coverage contract_id")
        _require_text(self.contract_version, "coverage contract_version")
        _require_hash(self.contract_sha256, "coverage contract_sha256")
        if self.expected_step is not None:
            if not isinstance(self.expected_step, pd.Timedelta) or pd.isna(self.expected_step):
                raise TrajectoryQueryError("expected_step must be an explicit positive Timedelta or None")
            if self.expected_step.value <= 0:
                raise TrajectoryQueryError("expected_step must be positive")

    @property
    def identity_hash(self) -> str:
        return canonical_sha256(
            domain="TRAJECTORY_COVERAGE_CONTRACT_ID_V1",
            payload={
                "contract_id": self.contract_id,
                "contract_version": self.contract_version,
                "contract_sha256": self.contract_sha256,
                "expected_step_ns": (
                    None if self.expected_step is None else int(self.expected_step.value)
                ),
            },
        )


@dataclass(frozen=True)
class CoverageIssue:
    left_position: int
    right_position: int
    observed_delta_ns: int
    expected_delta_ns: int

    def __post_init__(self) -> None:
        if self.left_position < 0 or self.right_position <= self.left_position:
            raise TrajectoryQueryError("coverage issue positions are invalid")
        if self.observed_delta_ns <= 0 or self.expected_delta_ns <= 0:
            raise TrajectoryQueryError("coverage issue deltas must be positive")


@dataclass(frozen=True)
class TrajectoryBar:
    position: int
    event_time_utc: pd.Timestamp | None
    open: float
    high: float
    low: float
    close: float

    def __post_init__(self) -> None:
        if isinstance(self.position, bool) or not isinstance(self.position, int) or self.position < 0:
            raise TrajectoryQueryError("bar position must be a nonnegative integer")
        if self.event_time_utc is not None:
            if not isinstance(self.event_time_utc, pd.Timestamp) or self.event_time_utc.tz is None:
                raise TrajectoryQueryError("bar event time must be timezone-aware")
            object.__setattr__(self, "event_time_utc", self.event_time_utc.tz_convert("UTC"))
        for field in ("open", "high", "low", "close"):
            value = _finite_price(getattr(self, field), field)
            object.__setattr__(self, field, value)
        if self.high < self.low or not (self.low <= self.open <= self.high) or not (
            self.low <= self.close <= self.high
        ):
            raise TrajectoryQueryError("trajectory bar violates OHLC range")


@dataclass(frozen=True)
class DecisionCloseObservation:
    information_key: InformationKey
    value: float
    source_field: str = "close"

    def __post_init__(self) -> None:
        if not isinstance(self.information_key, InformationKey):
            raise TrajectoryQueryError("decision close information key required")
        if self.source_field != "close":
            raise TrajectoryQueryError("decision baseline must be the observed close field")
        object.__setattr__(self, "value", _finite_price(self.value, "decision close"))


@dataclass(frozen=True)
class TrajectoryPathReference:
    path_id: str
    provenance_binding_hash: str
    case_id: str
    timeline_id: str
    decision_key: InformationKey
    decision_source_bindings: tuple[tuple[str, str], ...]
    decision_close_value: float
    horizon_request: HorizonRequest
    actual_end_key: InformationKey | None
    source_timeline_hash: str
    source_artifact_reference: TimelineArtifactReference | None
    row_access_state: CallerRowAccessState
    censoring_state: CensoringState
    coverage_contract: CoverageContract
    coverage_assessment: CoverageAssessment
    coverage_issues: tuple[CoverageIssue, ...]
    observed_row_count: int
    source_slice_hash: str
    bar_snapshot_hash: str
    slice_content_hash: str

    @property
    def requested_end_key(self) -> InformationKey:
        """The explicit, caller-selected horizon boundary (possibly beyond data)."""
        return self.horizon_request.requested_end_key

    def __post_init__(self) -> None:
        for name in (
            "path_id", "provenance_binding_hash", "case_id", "source_timeline_hash",
            "source_slice_hash", "bar_snapshot_hash", "slice_content_hash",
        ):
            _require_hash(getattr(self, name), name)
        _require_text(self.timeline_id, "path timeline_id")
        if not isinstance(self.decision_key, InformationKey):
            raise TrajectoryQueryError("path decision key required")
        if self.decision_key.timeline_id != self.timeline_id:
            raise TrajectoryQueryError("path decision timeline mismatch")
        if not isinstance(self.decision_source_bindings, tuple) or any(
            not isinstance(item, tuple)
            or len(item) != 2
            or not isinstance(item[0], str)
            or not item[0]
            or not _is_sha256(item[1])
            for item in self.decision_source_bindings
        ):
            raise TrajectoryQueryError("decision source bindings must be immutable domain/hash pairs")
        if tuple(sorted(self.decision_source_bindings)) != self.decision_source_bindings:
            raise TrajectoryQueryError("decision source bindings must be canonically ordered")
        if len(set(self.decision_source_bindings)) != len(self.decision_source_bindings):
            raise TrajectoryQueryError("duplicate decision source binding")
        if sum(domain == "MARKET_TIMELINE" for domain, _ in self.decision_source_bindings) != 1:
            raise TrajectoryQueryError("exactly one verified market timeline prefix binding is required")
        object.__setattr__(self, "decision_close_value", _finite_price(self.decision_close_value, "decision_close_value"))
        if not isinstance(self.horizon_request, HorizonRequest):
            raise TrajectoryQueryError("path horizon request required")
        requested_end = self.horizon_request.requested_end_key
        if requested_end.timeline_id != self.timeline_id:
            raise TrajectoryQueryError("path requested end timeline mismatch")
        if requested_end.bar_position <= self.decision_key.bar_position:
            raise TrajectoryQueryError("path interval must be (decision, end]")
        if self.actual_end_key is not None and self.actual_end_key.timeline_id != self.timeline_id:
            raise TrajectoryQueryError("path actual end timeline mismatch")
        if self.actual_end_key is not None and self.actual_end_key.bar_position <= self.decision_key.bar_position:
            raise TrajectoryQueryError("path actual end must follow decision bar")
        if self.actual_end_key is None and self.observed_row_count != 0:
            raise TrajectoryQueryError("observed path rows require an actual end key")
        if self.actual_end_key is not None and self.actual_end_key.bar_position > requested_end.bar_position:
            raise TrajectoryQueryError("actual path end exceeds requested end")
        if (self.decision_key.event_time_utc is None) != (requested_end.event_time_utc is None):
            raise TrajectoryQueryError("positional/time-indexed horizon identity mismatch")
        if self.actual_end_key is not None:
            if (self.decision_key.event_time_utc is None) != (self.actual_end_key.event_time_utc is None):
                raise TrajectoryQueryError("positional/time-indexed actual-end mismatch")
            if self.actual_end_key.information_phase is not InformationPhase.COMPLETED_ROW_AVAILABLE:
                raise TrajectoryQueryError("actual observed end must be a completed-row key")
        if self.censoring_state is CensoringState.OBSERVED_TO_REQUESTED_END:
            if self.actual_end_key is None or self.actual_end_key.bar_position != requested_end.bar_position:
                raise TrajectoryQueryError("complete requested window must reach requested end")
        if self.censoring_state is CensoringState.RIGHT_CENSORED:
            if self.actual_end_key is not None and self.actual_end_key.bar_position > requested_end.bar_position:
                raise TrajectoryQueryError("right-censored actual end exceeds requested end")
        if self.source_artifact_reference is not None:
            if not isinstance(self.source_artifact_reference, TimelineArtifactReference):
                raise TrajectoryQueryError("invalid path source artifact reference")
            if (
                self.source_artifact_reference.timeline_id != self.timeline_id
                or self.source_artifact_reference.timeline_hash != self.source_timeline_hash
            ):
                raise TrajectoryQueryError("path artifact reference/timeline binding mismatch")
        if self.row_access_state is not CallerRowAccessState.CALLER_SUPPLIED_VERIFIED_FRAME:
            raise TrajectoryQueryError("unsupported row access state")
        if not isinstance(self.censoring_state, CensoringState):
            raise TrajectoryQueryError("invalid censoring state")
        if not isinstance(self.coverage_contract, CoverageContract):
            raise TrajectoryQueryError("coverage contract required")
        if not isinstance(self.coverage_assessment, CoverageAssessment):
            raise TrajectoryQueryError("coverage assessment required")
        if not isinstance(self.coverage_issues, tuple) or any(
            not isinstance(issue, CoverageIssue) for issue in self.coverage_issues
        ):
            raise TrajectoryQueryError("coverage issues must be immutable")
        if self.coverage_assessment is CoverageAssessment.UNASSESSED and self.coverage_issues:
            raise TrajectoryQueryError("unassessed coverage cannot carry inferred gap issues")
        if self.coverage_assessment is CoverageAssessment.CONTIGUOUS and self.coverage_issues:
            raise TrajectoryQueryError("contiguous coverage cannot carry gap issues")
        if self.coverage_assessment is CoverageAssessment.GAPS_OR_CADENCE_DEVIATION and not self.coverage_issues:
            raise TrajectoryQueryError("coverage gap assessment requires explicit issues")
        if any(
            issue.left_position < self.decision_key.bar_position
            or self.actual_end_key is None
            or issue.right_position > self.actual_end_key.bar_position
            for issue in self.coverage_issues
        ):
            raise TrajectoryQueryError("coverage issue falls outside observed path")
        if isinstance(self.observed_row_count, bool) or not isinstance(self.observed_row_count, int) or self.observed_row_count < 0:
            raise TrajectoryQueryError("observed row count must be a nonnegative integer")
        if (self.observed_row_count == 0) != (self.actual_end_key is None):
            raise TrajectoryQueryError("actual end key/observed row count mismatch")
        expected_path_id = _path_identity_hash(self)
        if self.path_id != expected_path_id:
            raise TrajectoryQueryError("trajectory path identity mismatch")
        expected_provenance = _path_provenance_hash(
            path_id=self.path_id,
            source_timeline_hash=self.source_timeline_hash,
            source_artifact_reference=self.source_artifact_reference,
        )
        if self.provenance_binding_hash != expected_provenance:
            raise TrajectoryQueryError("trajectory source provenance mismatch")


def _path_identity_payload(reference: TrajectoryPathReference) -> dict:
    return {
        "case_id": reference.case_id,
        "timeline_id": reference.timeline_id,
        "decision_key": reference.decision_key,
        "decision_source_bindings": [list(item) for item in reference.decision_source_bindings],
        "decision_close_value_hex": float(reference.decision_close_value).hex(),
        "horizon_request_identity": reference.horizon_request.identity_hash,
        "actual_end_key": reference.actual_end_key,
        "censoring_state": reference.censoring_state.value,
        "coverage_contract_identity": reference.coverage_contract.identity_hash,
        "coverage_assessment": reference.coverage_assessment.value,
        "coverage_issues": [
            {
                "left_position": issue.left_position,
                "right_position": issue.right_position,
                "observed_delta_ns": issue.observed_delta_ns,
                "expected_delta_ns": issue.expected_delta_ns,
            }
            for issue in reference.coverage_issues
        ],
        "observed_row_count": reference.observed_row_count,
        "source_slice_hash": reference.source_slice_hash,
        "bar_snapshot_hash": reference.bar_snapshot_hash,
        "slice_content_hash": reference.slice_content_hash,
    }


def _path_identity_hash(reference: TrajectoryPathReference) -> str:
    return canonical_sha256(
        domain="TRAJECTORY_EPHEMERAL_PATH_ID_V1",
        payload=_path_identity_payload(reference),
    )


def _path_provenance_hash(
    *,
    path_id: str,
    source_timeline_hash: str,
    source_artifact_reference: TimelineArtifactReference | None,
) -> str:
    artifact = None
    if source_artifact_reference is not None:
        artifact = {
            "reference_id": source_artifact_reference.reference_id,
            "uri": source_artifact_reference.uri,
            "artifact_format": source_artifact_reference.artifact_format,
            "artifact_sha256": source_artifact_reference.artifact_sha256,
            "timeline_id": source_artifact_reference.timeline_id,
            "timeline_hash": source_artifact_reference.timeline_hash,
        }
    return canonical_sha256(
        domain="TRAJECTORY_EPHEMERAL_PATH_PROVENANCE_V1",
        payload={
            "path_id": path_id,
            "source_timeline_hash": source_timeline_hash,
            "source_artifact_reference": artifact,
            "row_access_state": CallerRowAccessState.CALLER_SUPPLIED_VERIFIED_FRAME.value,
        },
    )


def _bar_snapshot_hash(bars: tuple[TrajectoryBar, ...]) -> str:
    return canonical_sha256(
        domain="TRAJECTORY_OHLC_BAR_SNAPSHOT_V1",
        payload=[
            {
                "position": bar.position,
                "event_time_utc_ns": (
                    None if bar.event_time_utc is None else int(bar.event_time_utc.value)
                ),
                "open_hex": float(bar.open).hex(),
                "high_hex": float(bar.high).hex(),
                "low_hex": float(bar.low).hex(),
                "close_hex": float(bar.close).hex(),
            }
            for bar in bars
        ],
    )


@dataclass(frozen=True)
class TrajectoryWindow:
    reference: TrajectoryPathReference
    decision_close_observation: DecisionCloseObservation
    bars: tuple[TrajectoryBar, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.reference, TrajectoryPathReference):
            raise TrajectoryQueryError("trajectory path reference required")
        if not isinstance(self.decision_close_observation, DecisionCloseObservation):
            raise TrajectoryQueryError("decision close observation required")
        if self.decision_close_observation.information_key != self.reference.decision_key:
            raise TrajectoryQueryError("decision close key does not match path decision")
        if self.decision_close_observation.value != self.reference.decision_close_value:
            raise TrajectoryQueryError("decision close observation differs from path identity")
        if not isinstance(self.bars, tuple) or any(not isinstance(bar, TrajectoryBar) for bar in self.bars):
            raise TrajectoryQueryError("trajectory bars must be an immutable tuple")
        if len(self.bars) != self.reference.observed_row_count:
            raise TrajectoryQueryError("trajectory row count mismatch")
        if any(
            right.position <= left.position for left, right in zip(self.bars, self.bars[1:])
        ):
            raise TrajectoryQueryError("trajectory bars must be in strict chronological order")
        expected_end = (
            self.reference.decision_key.bar_position
            if self.reference.actual_end_key is None
            else self.reference.actual_end_key.bar_position
        )
        expected_positions = tuple(
            range(self.reference.decision_key.bar_position + 1, expected_end + 1)
        )
        if tuple(bar.position for bar in self.bars) != expected_positions:
            raise TrajectoryQueryError("trajectory rows must preserve every source position in (decision, end]")
        if self.bars and self.bars[0].position <= self.reference.decision_key.bar_position:
            raise TrajectoryQueryError("decision bar must be excluded from (decision, end]")
        if self.bars and self.reference.actual_end_key is not None:
            if self.bars[-1].position != self.reference.actual_end_key.bar_position:
                raise TrajectoryQueryError("actual end key does not match final observed row")
        if _bar_snapshot_hash(self.bars) != self.reference.bar_snapshot_hash:
            raise TrajectoryQueryError("trajectory bar snapshot was modified")


def _make_bar(index: pd.Index, market_history: pd.DataFrame, position: int, adapter: TimelineAdapter) -> TrajectoryBar:
    timestamp = None
    if isinstance(adapter, TimeIndexedTimelineAdapter):
        timestamp = pd.Timestamp(index[position]).tz_convert("UTC")
    return TrajectoryBar(
        position=position,
        event_time_utc=timestamp,
        open=float(market_history["open"].iloc[position]),
        high=float(market_history["high"].iloc[position]),
        low=float(market_history["low"].iloc[position]),
        close=float(market_history["close"].iloc[position]),
    )


def _coverage_assessment(
    *,
    adapter: TimelineAdapter,
    index: pd.Index,
    decision_position: int,
    stop_position: int,
    contract: CoverageContract,
) -> tuple[CoverageAssessment, tuple[CoverageIssue, ...]]:
    if contract.expected_step is None:
        return CoverageAssessment.UNASSESSED, ()
    if not isinstance(adapter, TimeIndexedTimelineAdapter):
        raise TrajectoryQueryError("fixed-step coverage requires a time-indexed timeline")
    if stop_position <= decision_position:
        return CoverageAssessment.UNASSESSED, ()
    expected_ns = int(contract.expected_step.value)
    issues = []
    for left in range(decision_position, stop_position):
        right = left + 1
        actual_ns = int(pd.Timestamp(index[right]).value - pd.Timestamp(index[left]).value)
        if actual_ns != expected_ns:
            issues.append(
                CoverageIssue(
                    left_position=left,
                    right_position=right,
                    observed_delta_ns=actual_ns,
                    expected_delta_ns=expected_ns,
                )
            )
    return (
        CoverageAssessment.GAPS_OR_CADENCE_DEVIATION if issues else CoverageAssessment.CONTIGUOUS,
        tuple(issues),
    )


def build_trajectory_window(
    *,
    case: TrajectoryDecisionCase,
    timeline: MarketObservationTimeline,
    adapter: TimelineAdapter,
    market_history: pd.DataFrame,
    horizon_request: HorizonRequest,
    coverage_contract: CoverageContract,
) -> TrajectoryWindow:
    """Build an ephemeral ``(decision, requested_end]`` slice from supplied rows.

    This verifies the full supplied timeline and the frozen decision prefix. It
    does not resolve a file/reference, infer a default horizon, interpolate
    gaps, or treat a hash as retrieval.
    """
    if not isinstance(case, TrajectoryDecisionCase):
        raise TypeError("case must be a TrajectoryDecisionCase")
    if not isinstance(horizon_request, HorizonRequest):
        raise TypeError("explicit HorizonRequest required")
    if not isinstance(coverage_contract, CoverageContract):
        raise TypeError("explicit CoverageContract required")
    try:
        market_snapshot = snapshot_market_history(market_history)
    except TrajectoryCaseError as exc:
        raise TrajectoryQueryError(f"cannot capture market snapshot: {exc}") from exc
    # From this point onward the caller's original frame is never read again.
    market_history = market_snapshot
    try:
        _verify_case_source_prefix_snapshot(
            case=case,
            timeline=timeline,
            adapter=adapter,
            market_snapshot=market_snapshot,
        )
    except TrajectoryCaseError as exc:
        raise TrajectoryQueryError(str(exc)) from exc
    requested_end = horizon_request.requested_end_key
    if requested_end.timeline_id != case.timeline_id:
        raise TrajectoryQueryError("requested end belongs to another timeline")
    if requested_end.bar_position <= case.decision_key.bar_position:
        raise TrajectoryQueryError("trajectory interval must be (decision, end]")
    if requested_end.information_phase not in _LEGAL_QUERY_PHASES:
        raise TrajectoryQueryError("requested end is not a completed-row boundary")

    n_rows = len(market_history)
    if requested_end.bar_position < n_rows:
        try:
            adapter.validate_key(requested_end, market_history.index)
        except Exception as exc:
            raise TrajectoryQueryError(f"requested end key is unavailable: {exc}") from exc
        stop_position = requested_end.bar_position
        # Reaching the final available source row is itself a right-censored
        # source boundary, even when the caller's requested endpoint coincides
        # with it. A strictly earlier requested endpoint is complete.
        censoring = (
            CensoringState.RIGHT_CENSORED
            if stop_position == n_rows - 1
            else CensoringState.OBSERVED_TO_REQUESTED_END
        )
    else:
        if isinstance(adapter, PositionalTimelineAdapter):
            if requested_end.event_time_utc is not None:
                raise TrajectoryQueryError("positional future boundary must not carry a timestamp")
        else:
            if requested_end.event_time_utc is None:
                raise TrajectoryQueryError("time-indexed future boundary requires an explicit UTC timestamp")
            final_timestamp = pd.Timestamp(market_history.index[-1]).tz_convert("UTC")
            if requested_end.event_time_utc <= final_timestamp:
                raise TrajectoryQueryError("out-of-range future boundary must follow the last observation")
        stop_position = n_rows - 1
        censoring = CensoringState.RIGHT_CENSORED

    decision_position = case.decision_key.bar_position
    row_positions = tuple(range(decision_position + 1, stop_position + 1))
    bars = tuple(_make_bar(market_history.index, market_history, position, adapter) for position in row_positions)
    actual_end = None
    if bars:
        actual_end = adapter.key_for_position(
            market_history.index,
            bars[-1].position,
            InformationPhase.COMPLETED_ROW_AVAILABLE,
            deterministic_sequence=0,
        )
    sealed_columns = tuple(timeline.required_columns) + tuple(timeline.optional_columns_present)
    source_slice = market_history.iloc[decision_position + 1 : stop_position + 1].loc[:, list(sealed_columns)]
    source_slice_hash = canonical_sha256(
        domain="TRAJECTORY_SOURCE_OHLC_SLICE_V1",
        payload=source_slice,
    )
    bar_snapshot_hash = _bar_snapshot_hash(bars)
    slice_content_hash = canonical_sha256(
        domain="TRAJECTORY_VERIFIED_SLICE_CONTENT_V1",
        payload={
            "source_slice_hash": source_slice_hash,
            "bar_snapshot_hash": bar_snapshot_hash,
        },
    )
    coverage_assessment, coverage_issues = _coverage_assessment(
        adapter=adapter,
        index=market_history.index,
        decision_position=decision_position,
        stop_position=stop_position,
        contract=coverage_contract,
    )
    # Path identity binds the bounded slice; the whole-history timeline hash is
    # retained separately as provenance and may change under future append.
    shell = object.__new__(TrajectoryPathReference)
    values = {
        "path_id": "0" * 64,
        "provenance_binding_hash": "0" * 64,
        "case_id": case.case_id,
        "timeline_id": timeline.timeline_id,
        "decision_key": case.decision_key,
        "decision_source_bindings": tuple(
            sorted(
                [("MARKET_TIMELINE", case.decision_prefix_hash)]
                + [(binding.domain, binding.stable_binding_hash) for binding in case.surface_prefix_bindings]
            )
        ),
        "decision_close_value": float(market_history["close"].iloc[decision_position]),
        "horizon_request": horizon_request,
        "actual_end_key": actual_end,
        "source_timeline_hash": timeline.timeline_hash,
        "source_artifact_reference": None,
        "row_access_state": CallerRowAccessState.CALLER_SUPPLIED_VERIFIED_FRAME,
        "censoring_state": censoring,
        "coverage_contract": coverage_contract,
        "coverage_assessment": coverage_assessment,
        "coverage_issues": coverage_issues,
        "observed_row_count": len(bars),
        "source_slice_hash": source_slice_hash,
        "bar_snapshot_hash": bar_snapshot_hash,
        "slice_content_hash": slice_content_hash,
    }
    for name, value in values.items():
        object.__setattr__(shell, name, value)
    path_id = _path_identity_hash(shell)
    provenance_hash = _path_provenance_hash(
        path_id=path_id,
        source_timeline_hash=timeline.timeline_hash,
        source_artifact_reference=None,
    )
    reference = TrajectoryPathReference(
        path_id=path_id,
        provenance_binding_hash=provenance_hash,
        **{key: value for key, value in values.items() if key not in ("path_id", "provenance_binding_hash")},
    )
    close_observation = DecisionCloseObservation(
        information_key=case.decision_key,
        value=float(market_history["close"].iloc[decision_position]),
    )
    return TrajectoryWindow(reference=reference, decision_close_observation=close_observation, bars=bars)


def verify_trajectory_window_source(
    *,
    window: TrajectoryWindow,
    case: TrajectoryDecisionCase,
    timeline: MarketObservationTimeline,
    adapter: TimelineAdapter,
    market_history: pd.DataFrame,
) -> None:
    """Independently reseal caller rows and verify an ephemeral path reference."""
    if not isinstance(window, TrajectoryWindow):
        raise TypeError("window must be a TrajectoryWindow")
    if window.reference.case_id != case.case_id:
        raise TrajectoryQueryError("trajectory window belongs to another case")
    try:
        market_snapshot = snapshot_market_history(market_history)
    except TrajectoryCaseError as exc:
        raise TrajectoryQueryError(f"cannot capture market snapshot: {exc}") from exc
    market_history = market_snapshot
    try:
        _verify_case_source_prefix_snapshot(
            case=case,
            timeline=timeline,
            adapter=adapter,
            market_snapshot=market_snapshot,
        )
    except TrajectoryCaseError as exc:
        raise TrajectoryQueryError(str(exc)) from exc
    if timeline.timeline_hash != window.reference.source_timeline_hash:
        raise TrajectoryQueryError("trajectory source timeline hash mismatch")
    requested_end = window.reference.requested_end_key
    row_count = len(market_history)
    if requested_end.bar_position < row_count:
        try:
            adapter.validate_key(requested_end, market_history.index)
        except Exception as exc:
            raise TrajectoryQueryError(f"requested end key is unavailable: {exc}") from exc
        expected_stop = requested_end.bar_position
    else:
        expected_stop = row_count - 1
        if isinstance(adapter, PositionalTimelineAdapter):
            if requested_end.event_time_utc is not None:
                raise TrajectoryQueryError("positional future boundary must not carry a timestamp")
        else:
            if requested_end.event_time_utc is None:
                raise TrajectoryQueryError("time-indexed future boundary requires an explicit UTC timestamp")
            final_timestamp = pd.Timestamp(market_history.index[-1]).tz_convert("UTC")
            if requested_end.event_time_utc <= final_timestamp:
                raise TrajectoryQueryError("out-of-range future boundary must follow the last observation")
    decision_position = case.decision_key.bar_position
    if expected_stop < decision_position:
        raise TrajectoryQueryError("verified trajectory end precedes the decision boundary")
    expected_actual_end = (
        None
        if expected_stop == decision_position
        else adapter.key_for_position(
            market_history.index,
            expected_stop,
            InformationPhase.COMPLETED_ROW_AVAILABLE,
            deterministic_sequence=0,
        )
    )
    expected_censoring = (
        CensoringState.RIGHT_CENSORED
        if expected_stop == row_count - 1
        else CensoringState.OBSERVED_TO_REQUESTED_END
    )
    if window.reference.actual_end_key != expected_actual_end:
        raise TrajectoryQueryError("trajectory actual end key does not match requested/source boundary")
    if window.reference.censoring_state is not expected_censoring:
        raise TrajectoryQueryError("trajectory censoring state does not match source boundary")
    expected_coverage, expected_issues = _coverage_assessment(
        adapter=adapter,
        index=market_history.index,
        decision_position=decision_position,
        stop_position=expected_stop,
        contract=window.reference.coverage_contract,
    )
    if (
        window.reference.coverage_assessment is not expected_coverage
        or window.reference.coverage_issues != expected_issues
    ):
        raise TrajectoryQueryError("trajectory coverage reference does not match source index")
    source_decision_close = float(market_history["close"].iloc[decision_position])
    if (
        window.reference.decision_close_value != source_decision_close
        or window.decision_close_observation.value != source_decision_close
    ):
        raise TrajectoryQueryError("decision close observation does not match verified source")
    stop = expected_stop
    columns = tuple(timeline.required_columns) + tuple(timeline.optional_columns_present)
    slice_frame = market_history.iloc[case.decision_key.bar_position + 1 : stop + 1].loc[:, list(columns)]
    source_hash = canonical_sha256(domain="TRAJECTORY_SOURCE_OHLC_SLICE_V1", payload=slice_frame)
    if source_hash != window.reference.source_slice_hash:
        raise TrajectoryQueryError("trajectory source slice hash mismatch")
    bars = tuple(
        _make_bar(market_history.index, market_history, position, adapter)
        for position in range(case.decision_key.bar_position + 1, stop + 1)
    )
    if bars != window.bars or _bar_snapshot_hash(bars) != window.reference.bar_snapshot_hash:
        raise TrajectoryQueryError("trajectory snapshot does not match supplied source rows")
    expected_slice_hash = canonical_sha256(
        domain="TRAJECTORY_VERIFIED_SLICE_CONTENT_V1",
        payload={"source_slice_hash": source_hash, "bar_snapshot_hash": _bar_snapshot_hash(bars)},
    )
    if expected_slice_hash != window.reference.slice_content_hash:
        raise TrajectoryQueryError("trajectory slice content hash mismatch")


def _touch_positions(window: TrajectoryWindow, price: float) -> tuple[int, ...]:
    return tuple(bar.position for bar in window.bars if bar.low <= price <= bar.high)


def _entity_touch_positions(
    window: TrajectoryWindow,
    entity: ResolvedProducerEntity,
) -> tuple[int, ...]:
    if entity.canonical_price is not None:
        return _touch_positions(window, entity.canonical_price)
    if entity.lower_bound is None or entity.upper_bound is None:
        raise TrajectoryQueryError("resolved producer entity has no contact price or bounds")
    return tuple(
        bar.position
        for bar in window.bars
        if bar.low <= entity.upper_bound and bar.high >= entity.lower_bound
    )


def _key_for_bar(window: TrajectoryWindow, position: int) -> InformationKey:
    bar = next(bar for bar in window.bars if bar.position == position)
    return InformationKey(
        information_key_version=INFORMATION_KEY_VERSION,
        timeline_id=window.reference.timeline_id,
        bar_position=bar.position,
        event_time_utc=bar.event_time_utc,
        information_phase=InformationPhase.COMPLETED_ROW_AVAILABLE,
        deterministic_sequence=0,
    )


def _horizon_completion(window: TrajectoryWindow) -> HorizonCompletionState:
    actual = window.reference.actual_end_key
    requested = window.reference.requested_end_key
    return (
        HorizonCompletionState.COMPLETE
        if actual is not None and actual.bar_position == requested.bar_position
        else HorizonCompletionState.INCOMPLETE
    )


def _interaction_status(window: TrajectoryWindow, touched: tuple[int, ...]) -> InteractionStatus:
    if touched:
        return InteractionStatus.OBSERVED_TOUCH
    if not window.bars:
        if window.reference.censoring_state is CensoringState.RIGHT_CENSORED:
            return InteractionStatus.RIGHT_CENSORED_NO_POST_DECISION_ROWS
        if window.reference.coverage_assessment is CoverageAssessment.UNASSESSED:
            return InteractionStatus.NO_POST_DECISION_ROWS_COVERAGE_UNASSESSED
        return InteractionStatus.NO_POST_DECISION_ROWS_TO_REQUESTED_END
    if window.reference.censoring_state is CensoringState.RIGHT_CENSORED:
        if window.reference.coverage_assessment is CoverageAssessment.GAPS_OR_CADENCE_DEVIATION:
            return InteractionStatus.NOT_OBSERVED_RIGHT_CENSORED_WITH_COVERAGE_GAPS
        return InteractionStatus.NOT_OBSERVED_RIGHT_CENSORED
    if window.reference.coverage_assessment is CoverageAssessment.GAPS_OR_CADENCE_DEVIATION:
        return InteractionStatus.NOT_OBSERVED_COVERAGE_GAPS
    if window.reference.coverage_assessment is CoverageAssessment.UNASSESSED:
        return InteractionStatus.NOT_OBSERVED_COVERAGE_UNASSESSED
    return InteractionStatus.NOT_OBSERVED_COMPLETE_WINDOW


def _touch_view_hash(
    *,
    domain: str,
    path_id: str,
    reference_hash: str,
    positions: tuple[int, ...],
    status: InteractionStatus,
    horizon_completion: HorizonCompletionState,
    source_censoring: CensoringState,
    coverage_assessment: CoverageAssessment,
    coverage_issues: tuple[CoverageIssue, ...],
    query_resolution: QueryResolutionState,
) -> str:
    return canonical_sha256(
        domain=domain,
        payload={
            "path_id": path_id,
            "reference_hash": reference_hash,
            "touch_positions": list(positions),
            "status": status.value,
            "horizon_completion": horizon_completion.value,
            "source_censoring": source_censoring.value,
            "coverage_assessment": coverage_assessment.value,
            "coverage_issues": [
                (issue.left_position, issue.right_position, issue.observed_delta_ns, issue.expected_delta_ns)
                for issue in coverage_issues
            ],
            "query_resolution": query_resolution.value,
        },
    )


@dataclass(frozen=True)
class ObservedTargetInteractionView:
    path_id: str
    observed_target_identity: str
    touch_positions: tuple[int, ...]
    first_observed_touch_key: InformationKey | None
    status: InteractionStatus
    horizon_completion: HorizonCompletionState
    source_censoring: CensoringState
    coverage_assessment: CoverageAssessment
    coverage_issues: tuple[CoverageIssue, ...]
    query_resolution: QueryResolutionState
    view_hash: str

    def __post_init__(self) -> None:
        for field in ("path_id", "observed_target_identity", "view_hash"):
            _require_hash(getattr(self, field), field)
        if tuple(sorted(set(self.touch_positions))) != self.touch_positions:
            raise TrajectoryQueryError("observed target positions must be sorted and unique")
        if (not self.touch_positions) != (self.first_observed_touch_key is None):
            raise TrajectoryQueryError("observed target first-touch key mismatch")
        if not isinstance(self.status, InteractionStatus):
            raise TrajectoryQueryError("invalid observed target status")
        if not isinstance(self.horizon_completion, HorizonCompletionState):
            raise TrajectoryQueryError("observed target horizon completion is required")
        if not isinstance(self.source_censoring, CensoringState):
            raise TrajectoryQueryError("observed target source censoring is required")
        if not isinstance(self.coverage_assessment, CoverageAssessment):
            raise TrajectoryQueryError("observed target coverage assessment is required")
        if not isinstance(self.query_resolution, QueryResolutionState):
            raise TrajectoryQueryError("observed target query resolution is required")


@dataclass(frozen=True)
class ProjectedTargetInteractionView:
    path_id: str
    projected_target_identity: str
    touch_positions: tuple[int, ...]
    first_observed_touch_key: InformationKey | None
    status: InteractionStatus
    horizon_completion: HorizonCompletionState
    source_censoring: CensoringState
    coverage_assessment: CoverageAssessment
    coverage_issues: tuple[CoverageIssue, ...]
    query_resolution: QueryResolutionState
    view_hash: str

    def __post_init__(self) -> None:
        for field in ("path_id", "projected_target_identity", "view_hash"):
            _require_hash(getattr(self, field), field)
        if tuple(sorted(set(self.touch_positions))) != self.touch_positions:
            raise TrajectoryQueryError("projected target positions must be sorted and unique")
        if (not self.touch_positions) != (self.first_observed_touch_key is None):
            raise TrajectoryQueryError("projected target first-touch key mismatch")
        if not isinstance(self.status, InteractionStatus):
            raise TrajectoryQueryError("invalid projected target status")
        if not isinstance(self.horizon_completion, HorizonCompletionState):
            raise TrajectoryQueryError("projected target horizon completion is required")
        if not isinstance(self.source_censoring, CensoringState):
            raise TrajectoryQueryError("projected target source censoring is required")
        if not isinstance(self.coverage_assessment, CoverageAssessment):
            raise TrajectoryQueryError("projected target coverage assessment is required")
        if not isinstance(self.query_resolution, QueryResolutionState):
            raise TrajectoryQueryError("projected target query resolution is required")


@dataclass(frozen=True)
class ProjectedInvalidationInteractionView:
    path_id: str
    projected_invalidation_identity: str
    touch_positions: tuple[int, ...]
    first_observed_touch_key: InformationKey | None
    status: InteractionStatus
    horizon_completion: HorizonCompletionState
    source_censoring: CensoringState
    coverage_assessment: CoverageAssessment
    coverage_issues: tuple[CoverageIssue, ...]
    query_resolution: QueryResolutionState
    view_hash: str

    def __post_init__(self) -> None:
        for field in ("path_id", "projected_invalidation_identity", "view_hash"):
            _require_hash(getattr(self, field), field)
        if tuple(sorted(set(self.touch_positions))) != self.touch_positions:
            raise TrajectoryQueryError("projected invalidation positions must be sorted and unique")
        if (not self.touch_positions) != (self.first_observed_touch_key is None):
            raise TrajectoryQueryError("projected invalidation first-touch key mismatch")
        if not isinstance(self.status, InteractionStatus):
            raise TrajectoryQueryError("invalid projected invalidation status")
        if not isinstance(self.horizon_completion, HorizonCompletionState):
            raise TrajectoryQueryError("projected invalidation horizon completion is required")
        if not isinstance(self.source_censoring, CensoringState):
            raise TrajectoryQueryError("projected invalidation source censoring is required")
        if not isinstance(self.coverage_assessment, CoverageAssessment):
            raise TrajectoryQueryError("projected invalidation coverage assessment is required")
        if not isinstance(self.query_resolution, QueryResolutionState):
            raise TrajectoryQueryError("projected invalidation query resolution is required")


def derive_observed_target_interaction(
    *,
    window: TrajectoryWindow,
    case: TrajectoryDecisionCase,
    surfaces: Iterable[object],
    observed_target: ObservedEntityLocator,
) -> ObservedTargetInteractionView:
    """Resolve an observed Stage4B2 entity; caller-supplied prices are impossible."""
    if not isinstance(window, TrajectoryWindow):
        raise TypeError("window must be a TrajectoryWindow")
    if not isinstance(case, TrajectoryDecisionCase):
        raise TypeError("case must be a TrajectoryDecisionCase")
    if not isinstance(observed_target, ObservedEntityLocator):
        raise TypeError("ObservedEntityLocator required; projected targets are a different type")
    if window.reference.case_id != case.case_id:
        raise TrajectoryQueryError("trajectory window belongs to another decision case")
    if (
        observed_target.producer_domain,
        observed_target.stable_binding_hash,
    ) not in window.reference.decision_source_bindings:
        raise TrajectoryQueryError("observed producer entity is not bound to the path decision case")
    resolved = resolve_observed_entity(
        case=case,
        surfaces=surfaces,
        locator=observed_target,
    )
    positions = _entity_touch_positions(window, resolved)
    status = _interaction_status(window, positions)
    first_key = None if not positions else _key_for_bar(window, positions[0])
    completion = _horizon_completion(window)
    censoring = window.reference.censoring_state
    coverage = window.reference.coverage_assessment
    query_resolution = QueryResolutionState.RESOLVED
    digest = _touch_view_hash(
        domain="OBSERVED_TARGET_INTERACTION_VIEW_V2",
        path_id=window.reference.path_id,
        reference_hash=resolved.identity_hash,
        positions=positions,
        status=status,
        horizon_completion=completion,
        source_censoring=censoring,
        coverage_assessment=coverage,
        coverage_issues=window.reference.coverage_issues,
        query_resolution=query_resolution,
    )
    return ObservedTargetInteractionView(
        path_id=window.reference.path_id,
        observed_target_identity=resolved.identity_hash,
        touch_positions=positions,
        first_observed_touch_key=first_key,
        status=status,
        horizon_completion=completion,
        source_censoring=censoring,
        coverage_assessment=coverage,
        coverage_issues=window.reference.coverage_issues,
        query_resolution=query_resolution,
        view_hash=digest,
    )


def derive_projected_target_interaction(
    *, window: TrajectoryWindow, projected_target: ProjectedTargetReference
) -> ProjectedTargetInteractionView:
    if not isinstance(window, TrajectoryWindow):
        raise TypeError("window must be a TrajectoryWindow")
    if not isinstance(projected_target, ProjectedTargetReference):
        raise TypeError("ProjectedTargetReference required; observed targets are a different type")
    if projected_target.available_at.timeline_id != window.reference.timeline_id:
        raise TrajectoryQueryError("projected target timeline mismatch")
    if projected_target.available_at > window.reference.decision_key:
        raise TrajectoryQueryError("projected target was unavailable at decision")
    positions = _touch_positions(window, projected_target.projected_price)
    status = _interaction_status(window, positions)
    first_key = None if not positions else _key_for_bar(window, positions[0])
    completion = _horizon_completion(window)
    censoring = window.reference.censoring_state
    coverage = window.reference.coverage_assessment
    query_resolution = QueryResolutionState.RESOLVED
    digest = _touch_view_hash(
        domain="PROJECTED_TARGET_INTERACTION_VIEW_V2",
        path_id=window.reference.path_id,
        reference_hash=projected_target.identity_hash,
        positions=positions,
        status=status,
        horizon_completion=completion,
        source_censoring=censoring,
        coverage_assessment=coverage,
        coverage_issues=window.reference.coverage_issues,
        query_resolution=query_resolution,
    )
    return ProjectedTargetInteractionView(
        path_id=window.reference.path_id,
        projected_target_identity=projected_target.identity_hash,
        touch_positions=positions,
        first_observed_touch_key=first_key,
        status=status,
        horizon_completion=completion,
        source_censoring=censoring,
        coverage_assessment=coverage,
        coverage_issues=window.reference.coverage_issues,
        query_resolution=query_resolution,
        view_hash=digest,
    )


def derive_projected_invalidation_interaction(
    *, window: TrajectoryWindow, projected_invalidation: ProjectedInvalidationReference
) -> ProjectedInvalidationInteractionView:
    if not isinstance(window, TrajectoryWindow):
        raise TypeError("window must be a TrajectoryWindow")
    if not isinstance(projected_invalidation, ProjectedInvalidationReference):
        raise TypeError("ProjectedInvalidationReference required")
    if projected_invalidation.available_at.timeline_id != window.reference.timeline_id:
        raise TrajectoryQueryError("projected invalidation timeline mismatch")
    if projected_invalidation.available_at > window.reference.decision_key:
        raise TrajectoryQueryError("projected invalidation was unavailable at decision")
    positions = _touch_positions(window, projected_invalidation.projected_price)
    status = _interaction_status(window, positions)
    first_key = None if not positions else _key_for_bar(window, positions[0])
    completion = _horizon_completion(window)
    censoring = window.reference.censoring_state
    coverage = window.reference.coverage_assessment
    query_resolution = QueryResolutionState.RESOLVED
    digest = _touch_view_hash(
        domain="PROJECTED_INVALIDATION_INTERACTION_VIEW_V2",
        path_id=window.reference.path_id,
        reference_hash=projected_invalidation.identity_hash,
        positions=positions,
        status=status,
        horizon_completion=completion,
        source_censoring=censoring,
        coverage_assessment=coverage,
        coverage_issues=window.reference.coverage_issues,
        query_resolution=query_resolution,
    )
    return ProjectedInvalidationInteractionView(
        path_id=window.reference.path_id,
        projected_invalidation_identity=projected_invalidation.identity_hash,
        touch_positions=positions,
        first_observed_touch_key=first_key,
        status=status,
        horizon_completion=completion,
        source_censoring=censoring,
        coverage_assessment=coverage,
        coverage_issues=window.reference.coverage_issues,
        query_resolution=query_resolution,
        view_hash=digest,
    )


def _coverage_complete_through(window: TrajectoryWindow, position: int) -> bool:
    assessment = window.reference.coverage_assessment
    if assessment is CoverageAssessment.UNASSESSED:
        return False
    if assessment is CoverageAssessment.CONTIGUOUS:
        return True
    return not any(issue.right_position <= position for issue in window.reference.coverage_issues)


@dataclass(frozen=True)
class TargetInvalidationInteractionView:
    path_id: str
    candidate_pair_id: str
    candidate_pair_identity: str
    target_touch_positions: tuple[int, ...]
    invalidation_touch_positions: tuple[int, ...]
    ordering: PairOrderStatus
    horizon_completion: HorizonCompletionState
    coverage_assessment: CoverageAssessment
    coverage_issues: tuple[CoverageIssue, ...]
    censoring_state: CensoringState
    query_resolution: QueryResolutionState
    view_hash: str

    def __post_init__(self) -> None:
        for field in ("path_id", "candidate_pair_identity", "view_hash"):
            _require_hash(getattr(self, field), field)
        _require_text(self.candidate_pair_id, "candidate_pair_id")
        if not isinstance(self.ordering, PairOrderStatus):
            raise TrajectoryQueryError("invalid target/invalidation ordering")
        if not isinstance(self.horizon_completion, HorizonCompletionState):
            raise TrajectoryQueryError("horizon completion required")
        if not isinstance(self.coverage_assessment, CoverageAssessment):
            raise TrajectoryQueryError("coverage assessment required")
        if not isinstance(self.coverage_issues, tuple) or any(
            not isinstance(issue, CoverageIssue) for issue in self.coverage_issues
        ):
            raise TrajectoryQueryError("coverage issues must be immutable")
        if not isinstance(self.censoring_state, CensoringState):
            raise TrajectoryQueryError("censoring state required")
        if not isinstance(self.query_resolution, QueryResolutionState):
            raise TrajectoryQueryError("query resolution required")


def derive_target_invalidation_view(
    *, window: TrajectoryWindow, candidate_pair: CandidatePricePair
) -> TargetInvalidationInteractionView:
    """Compare observed OHLC touches only; never infer intrabar order."""
    if not isinstance(window, TrajectoryWindow):
        raise TypeError("window must be a TrajectoryWindow")
    if not isinstance(candidate_pair, CandidatePricePair):
        raise TypeError("candidate_pair must be a CandidatePricePair")
    for key in (
        candidate_pair.projected_target.available_at,
        candidate_pair.projected_invalidation.available_at,
    ):
        if key.timeline_id != window.reference.timeline_id or key > window.reference.decision_key:
            raise TrajectoryQueryError("candidate pair was unavailable at trajectory decision")
    target_positions = _touch_positions(window, candidate_pair.projected_target.projected_price)
    invalidation_positions = _touch_positions(window, candidate_pair.projected_invalidation.projected_price)
    target_first = None if not target_positions else target_positions[0]
    invalidation_first = None if not invalidation_positions else invalidation_positions[0]

    if target_first is not None and invalidation_first is not None and target_first == invalidation_first:
        ordering = PairOrderStatus.BOTH_SAME_BAR_ORDER_UNKNOWN
    elif target_first is None and invalidation_first is None:
        if (
            window.reference.censoring_state is CensoringState.RIGHT_CENSORED
            and window.reference.coverage_assessment is CoverageAssessment.GAPS_OR_CADENCE_DEVIATION
        ):
            ordering = PairOrderStatus.NO_OBSERVED_TOUCH_RIGHT_CENSORED_WITH_COVERAGE_GAPS
        elif window.reference.censoring_state is CensoringState.RIGHT_CENSORED:
            ordering = PairOrderStatus.NO_OBSERVED_TOUCH_RIGHT_CENSORED
        elif window.reference.coverage_assessment is CoverageAssessment.GAPS_OR_CADENCE_DEVIATION:
            ordering = PairOrderStatus.NO_OBSERVED_TOUCH_COVERAGE_GAPS
        elif window.reference.coverage_assessment is CoverageAssessment.UNASSESSED:
            ordering = PairOrderStatus.NO_OBSERVED_TOUCH_COVERAGE_UNASSESSED
        else:
            ordering = PairOrderStatus.NO_OBSERVED_TOUCH_COMPLETE_WINDOW
    else:
        earliest = min(
            position for position in (target_first, invalidation_first) if position is not None
        )
        if not _coverage_complete_through(window, earliest):
            ordering = PairOrderStatus.ORDER_UNDETERMINED_COVERAGE
        elif target_first is not None and (
            invalidation_first is None or target_first < invalidation_first
        ):
            ordering = PairOrderStatus.TARGET_OBSERVED_FIRST
        else:
            ordering = PairOrderStatus.INVALIDATION_OBSERVED_FIRST

    digest = canonical_sha256(
        domain="TARGET_INVALIDATION_INTERACTION_VIEW_V1",
        payload={
            "path_id": window.reference.path_id,
            "candidate_pair_id": candidate_pair.candidate_pair_id,
            "candidate_pair_identity": candidate_pair.identity_hash,
            "target_touch_positions": list(target_positions),
            "invalidation_touch_positions": list(invalidation_positions),
            "ordering": ordering.value,
            "horizon_completion": _horizon_completion(window).value,
            "coverage_assessment": window.reference.coverage_assessment.value,
            "coverage_issues": [
                (issue.left_position, issue.right_position, issue.observed_delta_ns, issue.expected_delta_ns)
                for issue in window.reference.coverage_issues
            ],
            "censoring_state": window.reference.censoring_state.value,
            "query_resolution": QueryResolutionState.RESOLVED.value,
        },
    )
    return TargetInvalidationInteractionView(
        path_id=window.reference.path_id,
        candidate_pair_id=candidate_pair.candidate_pair_id,
        candidate_pair_identity=candidate_pair.identity_hash,
        target_touch_positions=target_positions,
        invalidation_touch_positions=invalidation_positions,
        ordering=ordering,
        horizon_completion=_horizon_completion(window),
        coverage_assessment=window.reference.coverage_assessment,
        coverage_issues=window.reference.coverage_issues,
        censoring_state=window.reference.censoring_state,
        query_resolution=QueryResolutionState.RESOLVED,
        view_hash=digest,
    )


@dataclass(frozen=True)
class ExcursionReference:
    kind: ExcursionReferenceKind
    information_key: InformationKey
    value: float
    source_binding_sha256: str
    source_field: str

    def __post_init__(self) -> None:
        if self.kind is not ExcursionReferenceKind.MARKET_MARK:
            raise TrajectoryQueryError("only a verified MARKET_MARK excursion reference is supported")
        if not isinstance(self.information_key, InformationKey):
            raise TrajectoryQueryError("excursion reference information key required")
        _require_hash(self.source_binding_sha256, "excursion source binding")
        if self.source_field != "close":
            raise TrajectoryQueryError("MARKET_MARK reference must name the captured market close")
        object.__setattr__(self, "value", _finite_price(self.value, "excursion reference value"))

    @property
    def identity_hash(self) -> str:
        return canonical_sha256(
            domain="TRAJECTORY_EXCURSION_REFERENCE_V1",
            payload={
                "kind": self.kind.value,
                "information_key": self.information_key,
                "value_hex": float(self.value).hex(),
                "source_binding_sha256": self.source_binding_sha256,
                "source_field": self.source_field,
            },
        )


def decision_close_excursion_reference(window: TrajectoryWindow) -> ExcursionReference:
    """Name the captured decision close explicitly as a MARKET_MARK reference."""
    if not isinstance(window, TrajectoryWindow):
        raise TypeError("window must be a TrajectoryWindow")
    bindings = [
        binding_hash
        for domain, binding_hash in window.reference.decision_source_bindings
        if domain == "MARKET_TIMELINE"
    ]
    if len(bindings) != 1:
        raise TrajectoryQueryError("path must bind exactly one market prefix for MARKET_MARK")
    return ExcursionReference(
        kind=ExcursionReferenceKind.MARKET_MARK,
        information_key=window.reference.decision_key,
        value=window.decision_close_observation.value,
        source_binding_sha256=bindings[0],
        source_field="close",
    )


@dataclass(frozen=True)
class ExcursionView:
    path_id: str
    reference_identity: str
    reference_kind: ExcursionReferenceKind
    reference_value: float
    status: DerivedViewStatus
    observed_max_high: float | None
    observed_min_low: float | None
    observed_high_delta_from_reference: float | None
    observed_low_delta_from_reference: float | None
    max_high_position: int | None
    min_low_position: int | None
    horizon_completion: HorizonCompletionState
    coverage_assessment: CoverageAssessment
    censoring_state: CensoringState
    query_resolution: QueryResolutionState
    view_hash: str

    def __post_init__(self) -> None:
        _require_hash(self.path_id, "excursion path_id")
        _require_hash(self.reference_identity, "excursion reference_identity")
        _require_hash(self.view_hash, "excursion view_hash")
        if self.reference_kind is not ExcursionReferenceKind.MARKET_MARK:
            raise TrajectoryQueryError("unsupported excursion reference kind")
        if not isinstance(self.status, DerivedViewStatus):
            raise TrajectoryQueryError("excursion status required")
        if not isinstance(self.horizon_completion, HorizonCompletionState):
            raise TrajectoryQueryError("excursion horizon completion required")
        if not isinstance(self.coverage_assessment, CoverageAssessment):
            raise TrajectoryQueryError("excursion coverage assessment required")
        if not isinstance(self.censoring_state, CensoringState):
            raise TrajectoryQueryError("excursion source censoring required")
        if not isinstance(self.query_resolution, QueryResolutionState):
            raise TrajectoryQueryError("excursion query resolution required")
        values = (
            self.observed_max_high,
            self.observed_min_low,
            self.observed_high_delta_from_reference,
            self.observed_low_delta_from_reference,
        )
        if self.status is DerivedViewStatus.NO_POST_DECISION_ROWS:
            if any(value is not None for value in values) or self.max_high_position is not None or self.min_low_position is not None:
                raise TrajectoryQueryError("empty excursion view must preserve unavailable values")
        else:
            if any(value is None for value in values) or self.max_high_position is None or self.min_low_position is None:
                raise TrajectoryQueryError("available excursion view is incomplete")


def derive_excursion_view(
    *,
    window: TrajectoryWindow,
    reference: ExcursionReference,
) -> ExcursionView:
    if not isinstance(window, TrajectoryWindow):
        raise TypeError("window must be a TrajectoryWindow")
    if not isinstance(reference, ExcursionReference):
        raise TypeError("explicit ExcursionReference required")
    market_bindings = [
        binding_hash
        for domain, binding_hash in window.reference.decision_source_bindings
        if domain == "MARKET_TIMELINE"
    ]
    if (
        reference.kind is not ExcursionReferenceKind.MARKET_MARK
        or reference.information_key != window.reference.decision_key
        or reference.source_field != "close"
        or len(market_bindings) != 1
        or reference.source_binding_sha256 != market_bindings[0]
        or reference.value != window.decision_close_observation.value
    ):
        raise TrajectoryQueryError("excursion reference is not the verified decision MARKET_MARK")
    if not window.bars:
        status = DerivedViewStatus.NO_POST_DECISION_ROWS
        maximum = minimum = high_delta = low_delta = None
        max_position = min_position = None
    else:
        status = DerivedViewStatus.AVAILABLE
        maximum_bar = max(window.bars, key=lambda bar: (bar.high, -bar.position))
        minimum_bar = min(window.bars, key=lambda bar: (bar.low, bar.position))
        maximum = maximum_bar.high
        minimum = minimum_bar.low
        high_delta = maximum - reference.value
        low_delta = minimum - reference.value
        max_position = maximum_bar.position
        min_position = minimum_bar.position
    completion = _horizon_completion(window)
    resolution = QueryResolutionState.RESOLVED
    digest = canonical_sha256(
        domain="TRAJECTORY_OBSERVED_EXCURSION_VIEW_V2",
        payload={
            "path_id": window.reference.path_id,
            "reference_identity": reference.identity_hash,
            "status": status.value,
            "observed_max_high": maximum,
            "observed_min_low": minimum,
            "observed_high_delta_from_reference": high_delta,
            "observed_low_delta_from_reference": low_delta,
            "max_high_position": max_position,
            "min_low_position": min_position,
            "horizon_completion": completion.value,
            "coverage_assessment": window.reference.coverage_assessment.value,
            "coverage_issues": [
                (issue.left_position, issue.right_position, issue.observed_delta_ns, issue.expected_delta_ns)
                for issue in window.reference.coverage_issues
            ],
            "censoring_state": window.reference.censoring_state.value,
            "query_resolution": resolution.value,
        },
    )
    return ExcursionView(
        path_id=window.reference.path_id,
        reference_identity=reference.identity_hash,
        reference_kind=reference.kind,
        reference_value=reference.value,
        status=status,
        observed_max_high=maximum,
        observed_min_low=minimum,
        observed_high_delta_from_reference=high_delta,
        observed_low_delta_from_reference=low_delta,
        max_high_position=max_position,
        min_low_position=min_position,
        horizon_completion=completion,
        coverage_assessment=window.reference.coverage_assessment,
        censoring_state=window.reference.censoring_state,
        query_resolution=resolution,
        view_hash=digest,
    )


@dataclass(frozen=True)
class TimingView:
    path_id: str
    reference_identity: str
    interaction_status: InteractionStatus
    first_observed_touch_key: InformationKey | None
    observed_bar_offset: int | None
    elapsed_time_ns: int | None
    horizon_completion: HorizonCompletionState
    source_censoring: CensoringState
    coverage_assessment: CoverageAssessment
    coverage_issues: tuple[CoverageIssue, ...]
    query_resolution: QueryResolutionState
    view_hash: str

    def __post_init__(self) -> None:
        for field in ("path_id", "reference_identity", "view_hash"):
            _require_hash(getattr(self, field), field)
        if not isinstance(self.interaction_status, InteractionStatus):
            raise TrajectoryQueryError("timing view requires explicit interaction status")
        if (self.first_observed_touch_key is None) != (self.observed_bar_offset is None):
            raise TrajectoryQueryError("timing key and observed bar offset mismatch")
        if self.first_observed_touch_key is None and self.elapsed_time_ns is not None:
            raise TrajectoryQueryError("elapsed time cannot exist without an observed touch")
        if self.observed_bar_offset is not None and self.observed_bar_offset <= 0:
            raise TrajectoryQueryError("trajectory timing offset must follow decision bar")
        if self.elapsed_time_ns is not None and self.elapsed_time_ns < 0:
            raise TrajectoryQueryError("elapsed time must not be negative")
        if not isinstance(self.horizon_completion, HorizonCompletionState):
            raise TrajectoryQueryError("timing horizon completion is required")
        if not isinstance(self.source_censoring, CensoringState):
            raise TrajectoryQueryError("timing source censoring is required")
        if not isinstance(self.coverage_assessment, CoverageAssessment):
            raise TrajectoryQueryError("timing coverage assessment is required")
        if not isinstance(self.query_resolution, QueryResolutionState):
            raise TrajectoryQueryError("timing query resolution is required")


def derive_timing_view(
    *,
    window: TrajectoryWindow,
    target_reference: ObservedEntityLocator | ProjectedTargetReference | ProjectedInvalidationReference,
    case: TrajectoryDecisionCase | None = None,
    surfaces: Iterable[object] | None = None,
) -> TimingView:
    if isinstance(target_reference, ObservedEntityLocator):
        if case is None or surfaces is None:
            raise TrajectoryQueryError("observed timing requires a case and verified Stage4B2 surfaces")
        interaction = derive_observed_target_interaction(
            window=window,
            case=case,
            surfaces=surfaces,
            observed_target=target_reference,
        )
        identity = interaction.observed_target_identity
    elif isinstance(target_reference, ProjectedTargetReference):
        interaction = derive_projected_target_interaction(window=window, projected_target=target_reference)
        identity = target_reference.identity_hash
    elif isinstance(target_reference, ProjectedInvalidationReference):
        interaction = derive_projected_invalidation_interaction(
            window=window,
            projected_invalidation=target_reference,
        )
        identity = target_reference.identity_hash
    else:
        raise TypeError(
            "ObservedEntityLocator, ProjectedTargetReference, or ProjectedInvalidationReference required"
        )
    touch_key = interaction.first_observed_touch_key
    offset = None if touch_key is None else touch_key.bar_position - window.reference.decision_key.bar_position
    elapsed = None
    if touch_key is not None and touch_key.event_time_utc is not None:
        decision_time = window.reference.decision_key.event_time_utc
        if decision_time is None:
            raise TrajectoryQueryError("mixed positional/time-indexed timing keys")
        elapsed = int(touch_key.event_time_utc.value - decision_time.value)
    completion = _horizon_completion(window)
    censoring = window.reference.censoring_state
    coverage = window.reference.coverage_assessment
    query_resolution = QueryResolutionState.RESOLVED
    digest = canonical_sha256(
        domain="TRAJECTORY_OBSERVED_TIMING_VIEW_V2",
        payload={
            "path_id": window.reference.path_id,
            "reference_identity": identity,
            "interaction_status": interaction.status.value,
            "first_observed_touch_key": touch_key,
            "observed_bar_offset": offset,
            "elapsed_time_ns": elapsed,
            "horizon_completion": completion.value,
            "source_censoring": censoring.value,
            "coverage_assessment": coverage.value,
            "coverage_issues": [
                (issue.left_position, issue.right_position, issue.observed_delta_ns, issue.expected_delta_ns)
                for issue in window.reference.coverage_issues
            ],
            "query_resolution": query_resolution.value,
        },
    )
    return TimingView(
        path_id=window.reference.path_id,
        reference_identity=identity,
        interaction_status=interaction.status,
        first_observed_touch_key=touch_key,
        observed_bar_offset=offset,
        elapsed_time_ns=elapsed,
        horizon_completion=completion,
        source_censoring=censoring,
        coverage_assessment=coverage,
        coverage_issues=window.reference.coverage_issues,
        query_resolution=query_resolution,
        view_hash=digest,
    )
