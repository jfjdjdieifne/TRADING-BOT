"""Strategy-neutral decision-case identities over verified trajectory inputs.

The case identity commits only to facts/bindings available at its decision key.
Full-history timeline/surface IDs are retained in a provenance sidecar, never in
``case_id``/``case_hash``; those whole-artifact hashes can change when future
bars are appended. Stage 4 engines are reused only through their public
integrity and prefix-projection APIs.
"""
from __future__ import annotations

from dataclasses import dataclass, fields, replace
from decimal import Decimal, InvalidOperation
from enum import Enum
import re
from typing import Iterable

import numpy as np
import pandas as pd

from trading_system.research.hashing import canonical_sha256
from trading_system.research.information_time import (
    InformationKey,
    InformationPhase,
    PositionalTimelineAdapter,
    TimeIndexedTimelineAdapter,
)
from trading_system.research.trajectory.trajectory_contract import (
    MarketObservationTimeline,
    TIMELINE_ADAPTER_KIND,
    TIMELINE_CAPABILITY,
)
from trading_system.research.trajectory.trajectory_timeline_resolver import (
    TimelineArtifactReference,
)
from trading_system.research.trajectory import trajectory_stage4a as s4a
from trading_system.research.trajectory import trajectory_stage4b1 as s4b1
from trading_system.research.trajectory import trajectory_stage4b2 as s4b2
from trading_system.research.trajectory.trajectory_stage4b2_consistency import (
    LOCAL_VERIFICATION_SCOPE,
    Stage4B2ConsistencyError,
    capture_stage4b2_market_source_column_hashes,
    required_stage4b2_market_source_columns,
    verify_stage4b2_consistency,
)
from trading_system.research.trajectory import trajectory_stage4c as s4c


TRAJECTORY_CASE_CONTRACT_VERSION = "STRATEGY_NEUTRAL_TRAJECTORY_CASE_V1"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_LEGAL_DECISION_PHASES = frozenset(
    {InformationPhase.COMPLETED_ROW_AVAILABLE, InformationPhase.RESEARCH_SNAPSHOT_AVAILABLE}
)
TimelineAdapter = PositionalTimelineAdapter | TimeIndexedTimelineAdapter


class TrajectoryCaseError(ValueError):
    """Invalid case binding or as-of identity."""


def _require_nonempty(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise TrajectoryCaseError(f"{field} must be a nonempty string")


def _require_sha256(value: str, field: str) -> None:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise TrajectoryCaseError(f"{field} must be lowercase SHA-256 hex")


def _assert_immutable_snapshot_value(value: object, *, field: str) -> None:
    """Reject mutable object cells/metadata before a captured source is verified.

    ``DataFrame.copy(deep=True)`` does not recursively copy Python objects inside
    object-dtype cells. The trajectory adapter therefore accepts only scalar or
    recursively immutable tuple values in a source snapshot.
    """
    if value is None or value is pd.NA or value is pd.NaT:
        return
    if isinstance(value, np.generic):
        scalar = value.item()
        if scalar is value:
            raise TrajectoryCaseError(f"unsupported mutable snapshot value: {field}")
        _assert_immutable_snapshot_value(scalar, field=field)
        return
    if isinstance(value, tuple):
        for index, item in enumerate(value):
            _assert_immutable_snapshot_value(item, field=f"{field}[{index}]")
        return
    if isinstance(
        value,
        (str, bytes, bool, int, float, Decimal, pd.Timestamp, pd.Timedelta, Enum),
    ):
        return
    raise TrajectoryCaseError(
        f"unsupported mutable or non-scalar snapshot value: {field}:{type(value).__name__}"
    )


def _snapshot_frame(frame: pd.DataFrame, *, field: str) -> pd.DataFrame:
    """Capture an owned DataFrame and reject cells that cannot be frozen safely."""
    if not isinstance(frame, pd.DataFrame):
        raise TrajectoryCaseError(f"{field} must be a DataFrame")
    snapshot = frame.copy(deep=True)
    snapshot.index = frame.index.copy(deep=True)
    snapshot.columns = frame.columns.copy(deep=True)
    for value in snapshot.index.tolist():
        _assert_immutable_snapshot_value(value, field=f"{field}.index")
    for value in snapshot.columns.tolist():
        _assert_immutable_snapshot_value(value, field=f"{field}.column")
    for row in snapshot.itertuples(index=False, name=None):
        for column, value in zip(snapshot.columns.tolist(), row):
            _assert_immutable_snapshot_value(value, field=f"{field}.{column}")
    return snapshot


def snapshot_market_history(market_history: pd.DataFrame) -> pd.DataFrame:
    """Capture the only market frame to be verified and used by a trajectory call."""
    return _snapshot_frame(market_history, field="market_history")


def snapshot_stage4_surface(surface: object) -> object:
    """Capture every mutable frame in one supported public Stage 4 surface.

    Returned surface objects are private to the calling trajectory operation;
    integrity verification, prefix projection and row extraction must all use
    this same object.
    """
    supported = (
        s4a.Stage4ADomainSurface,
        s4b1.Stage4B1StructureSurface,
        s4b2.Stage4B2LiquiditySurface,
        s4b2.Stage4B2OrderBlockSurface,
        s4b2.Stage4B2FVGSurface,
        s4b2.Stage4B2DealingRangeSurface,
        s4c.Stage4CHtfScaleSurface,
    )
    if not isinstance(surface, supported):
        raise TrajectoryCaseError(f"unsupported Stage 4 surface type: {type(surface).__name__}")
    updates = {}
    for descriptor in fields(surface):
        value = getattr(surface, descriptor.name)
        if isinstance(value, pd.DataFrame):
            updates[descriptor.name] = _snapshot_frame(
                value, field=f"{type(surface).__name__}.{descriptor.name}"
            )
        else:
            _assert_immutable_snapshot_value(value, field=f"{type(surface).__name__}.{descriptor.name}")
    try:
        return replace(surface, **updates)
    except Exception as exc:
        raise TrajectoryCaseError(f"could not capture Stage 4 surface snapshot: {exc}") from exc


def _number_token(value: object, *, field: str) -> dict[str, str]:
    """Canonical numeric token independent of whole-frame dtype promotion.

    This makes an unchanged historical prefix keep its identity if appending a
    future row causes pandas to widen an integer column to float. Missing
    optional values stay explicit; missing OHLC is rejected by timeline.verify.
    """
    if isinstance(value, np.generic):
        value = value.item()
    try:
        missing = bool(pd.isna(value))
    except (TypeError, ValueError):
        missing = False
    if missing:
        return {"state": "MISSING"}
    if isinstance(value, (bool, np.bool_)):
        raise TrajectoryCaseError(f"boolean market value is not numeric evidence: {field}")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise TrajectoryCaseError(f"non-numeric sealed market value: {field}") from exc
    if not number.is_finite():
        raise TrajectoryCaseError(f"non-finite sealed market value: {field}")
    if number == 0:
        literal = "0"
    else:
        literal = format(number.normalize(), "f")
    return {"state": "NUMBER", "value": literal}


def _decision_prefix_hash(
    *,
    timeline: MarketObservationTimeline,
    adapter: TimelineAdapter,
    market_history: pd.DataFrame,
    decision_position: int,
) -> str:
    columns = tuple(timeline.required_columns) + tuple(timeline.optional_columns_present)
    if not columns or any(column not in market_history.columns for column in columns):
        raise TrajectoryCaseError("sealed market columns are not present in caller frame")
    rows = []
    for position in range(decision_position + 1):
        row = {
            "bar_position": position,
            "values": tuple(
                (column, _number_token(market_history[column].iloc[position], field=column))
                for column in columns
            ),
        }
        if isinstance(adapter, TimeIndexedTimelineAdapter):
            row["event_time_utc_ns"] = int(
                pd.Timestamp(market_history.index[position]).tz_convert("UTC").value
            )
        rows.append(row)
    return canonical_sha256(
        domain="TRAJECTORY_DECISION_TIMELINE_PREFIX_V1",
        payload={
            "timeline_id": timeline.timeline_id,
            "adapter_kind": timeline.adapter_kind,
            "adapter_version": timeline.adapter_version,
            "source_capability": timeline.source_capability,
            "required_columns": list(timeline.required_columns),
            "optional_columns_present": list(timeline.optional_columns_present),
            "rows_through_decision": rows,
        },
    )


def _surface_prefix_identity_hash(
    *,
    surface_family: str,
    domain: str,
    contract_version: str,
    configuration_identity_hash: str,
    timeline_id: str,
    adapter_kind: TIMELINE_ADAPTER_KIND,
    boundary_key: InformationKey,
    prefix_hash: str,
    prefix_row_count: int,
) -> str:
    return canonical_sha256(
        domain="TRAJECTORY_SURFACE_PREFIX_BINDING_V1",
        payload={
            "surface_family": surface_family,
            "domain": domain,
            "contract_version": contract_version,
            "configuration_identity_hash": configuration_identity_hash,
            "timeline_id": timeline_id,
            "adapter_kind": adapter_kind,
            "boundary_key": boundary_key,
            "prefix_hash": prefix_hash,
            "prefix_row_count": prefix_row_count,
        },
    )


@dataclass(frozen=True)
class ParentDecisionSnapshotReference:
    """Optional neutral reference to a snapshot available no later than decision."""

    snapshot_id: str
    schema_version: str
    content_sha256: str
    available_at: InformationKey

    def __post_init__(self) -> None:
        _require_nonempty(self.snapshot_id, "snapshot_id")
        _require_nonempty(self.schema_version, "schema_version")
        _require_sha256(self.content_sha256, "content_sha256")
        if not isinstance(self.available_at, InformationKey):
            raise TrajectoryCaseError("available_at must be an InformationKey")


@dataclass(frozen=True)
class SurfacePrefixBinding:
    """Stable decision-prefix binding plus explicitly non-identity source refs.

    ``stable_binding_hash`` excludes ``source_surface_id`` and
    ``source_timeline_hash``. The latter are provenance for the supplied
    whole-history artifacts and may change under future append; prefix facts do
    not. ``source_*`` fields are never copied to an as-of feature view.
    """

    surface_family: str
    domain: str
    contract_version: str
    configuration_identity_hash: str
    timeline_id: str
    adapter_kind: TIMELINE_ADAPTER_KIND
    boundary_key: InformationKey
    prefix_hash: str
    prefix_row_count: int
    stable_binding_hash: str
    source_surface_id: str
    source_timeline_hash: str
    verification_scope: str | None = None

    def __post_init__(self) -> None:
        for name in ("surface_family", "domain", "contract_version", "timeline_id"):
            _require_nonempty(getattr(self, name), name)
        for name in (
            "configuration_identity_hash",
            "prefix_hash",
            "stable_binding_hash",
            "source_surface_id",
            "source_timeline_hash",
        ):
            _require_sha256(getattr(self, name), name)
        if self.surface_family == "STAGE4B2":
            if self.verification_scope != LOCAL_VERIFICATION_SCOPE:
                raise TrajectoryCaseError("Stage4B2 binding lacks successful local consistency verification")
        elif self.verification_scope is not None:
            raise TrajectoryCaseError("local Stage4B2 verification scope is invalid for this surface family")
        if not isinstance(self.adapter_kind, TIMELINE_ADAPTER_KIND):
            raise TrajectoryCaseError("invalid surface adapter_kind")
        if not isinstance(self.boundary_key, InformationKey):
            raise TrajectoryCaseError("surface boundary_key must be an InformationKey")
        if self.boundary_key.timeline_id != self.timeline_id:
            raise TrajectoryCaseError("surface boundary timeline mismatch")
        if isinstance(self.prefix_row_count, bool) or not isinstance(self.prefix_row_count, int):
            raise TrajectoryCaseError("prefix_row_count must be an integer")
        if self.prefix_row_count != self.boundary_key.bar_position + 1:
            raise TrajectoryCaseError("surface prefix row count does not match boundary")
        expected = _surface_prefix_identity_hash(
            surface_family=self.surface_family,
            domain=self.domain,
            contract_version=self.contract_version,
            configuration_identity_hash=self.configuration_identity_hash,
            timeline_id=self.timeline_id,
            adapter_kind=self.adapter_kind,
            boundary_key=self.boundary_key,
            prefix_hash=self.prefix_hash,
            prefix_row_count=self.prefix_row_count,
        )
        if self.stable_binding_hash != expected:
            raise TrajectoryCaseError("surface stable prefix binding hash mismatch")


@dataclass(frozen=True)
class SurfaceVersionReference:
    """Non-decision provenance for one concrete full surface artifact version."""

    stable_binding_hash: str
    source_surface_id: str
    source_timeline_hash: str
    verification_scope: str | None = None

    def __post_init__(self) -> None:
        _require_sha256(self.stable_binding_hash, "stable_binding_hash")
        _require_sha256(self.source_surface_id, "source_surface_id")
        _require_sha256(self.source_timeline_hash, "source_timeline_hash")
        if self.verification_scope not in (None, LOCAL_VERIFICATION_SCOPE):
            raise TrajectoryCaseError("invalid local surface verification scope")


@dataclass(frozen=True)
class CaseSourceProvenance:
    """Whole-artifact context kept outside case identity and decision features."""

    timeline_hash: str
    source_artifact_reference: TimelineArtifactReference | None
    surface_versions: tuple[SurfaceVersionReference, ...]
    provenance_binding_hash: str
    market_source_column_hashes: tuple[tuple[str, tuple[str, ...]], ...] = ()

    def __post_init__(self) -> None:
        _require_sha256(self.timeline_hash, "timeline_hash")
        if self.source_artifact_reference is not None and not isinstance(
            self.source_artifact_reference, TimelineArtifactReference
        ):
            raise TrajectoryCaseError("invalid source_artifact_reference")
        if not isinstance(self.surface_versions, tuple) or any(
            not isinstance(item, SurfaceVersionReference) for item in self.surface_versions
        ):
            raise TrajectoryCaseError("surface_versions must be an immutable tuple")
        if tuple(sorted(self.surface_versions, key=lambda item: item.stable_binding_hash)) != self.surface_versions:
            raise TrajectoryCaseError("surface_versions must be canonically ordered")
        if len({item.stable_binding_hash for item in self.surface_versions}) != len(self.surface_versions):
            raise TrajectoryCaseError("duplicate source surface version reference")
        if any(item.source_timeline_hash != self.timeline_hash for item in self.surface_versions):
            raise TrajectoryCaseError("surface source timeline hash differs from provenance timeline")
        if not isinstance(self.market_source_column_hashes, tuple) or any(
            not isinstance(item, tuple)
            or len(item) != 2
            or not isinstance(item[0], str)
            or not item[0]
            or not isinstance(item[1], tuple)
            or any(
                not isinstance(digest, str)
                or _SHA256_RE.fullmatch(digest) is None
                for digest in item[1]
            )
            for item in self.market_source_column_hashes
        ):
            raise TrajectoryCaseError("market source column hashes must be immutable column/hash tuples")
        source_columns = tuple(column for column, _ in self.market_source_column_hashes)
        if tuple(sorted(set(source_columns))) != source_columns:
            raise TrajectoryCaseError("market source columns must be unique and canonically ordered")
        if len({len(hashes) for _, hashes in self.market_source_column_hashes}) > 1:
            raise TrajectoryCaseError("market source columns have inconsistent captured row counts")
        _require_sha256(self.provenance_binding_hash, "provenance_binding_hash")
        expected = _provenance_hash(
            timeline_hash=self.timeline_hash,
            source_artifact_reference=self.source_artifact_reference,
            surface_versions=self.surface_versions,
            market_source_column_hashes=self.market_source_column_hashes,
        )
        if self.provenance_binding_hash != expected:
            raise TrajectoryCaseError("source provenance binding hash mismatch")


def _surface_version_payload(item: SurfaceVersionReference) -> dict:
    payload = {
        "stable_binding_hash": item.stable_binding_hash,
        "source_surface_id": item.source_surface_id,
        "source_timeline_hash": item.source_timeline_hash,
    }
    if item.verification_scope is not None:
        payload["verification_scope"] = item.verification_scope
    return payload


def _provenance_hash(
    *,
    timeline_hash: str,
    source_artifact_reference: TimelineArtifactReference | None,
    surface_versions: tuple[SurfaceVersionReference, ...],
    market_source_column_hashes: tuple[tuple[str, tuple[str, ...]], ...] = (),
) -> str:
    reference = None
    if source_artifact_reference is not None:
        reference = {
            "reference_id": source_artifact_reference.reference_id,
            "uri": source_artifact_reference.uri,
            "artifact_format": source_artifact_reference.artifact_format,
            "artifact_sha256": source_artifact_reference.artifact_sha256,
            "timeline_id": source_artifact_reference.timeline_id,
            "timeline_hash": source_artifact_reference.timeline_hash,
        }
    payload = {
        "timeline_hash": timeline_hash,
        "source_artifact_reference": reference,
        "surface_versions": [_surface_version_payload(item) for item in surface_versions],
    }
    if market_source_column_hashes:
        payload["market_source_column_hashes"] = [
            {"column": column, "row_hashes": list(hashes)}
            for column, hashes in market_source_column_hashes
        ]
    return canonical_sha256(
        domain="TRAJECTORY_CASE_SOURCE_PROVENANCE_V1",
        payload=payload,
    )


def _case_identity_payload(
    *,
    timeline_id: str,
    adapter_kind: TIMELINE_ADAPTER_KIND,
    adapter_version: str,
    source_capability: TIMELINE_CAPABILITY,
    required_columns: tuple[str, ...],
    optional_columns_present: tuple[str, ...],
    decision_key: InformationKey,
    decision_prefix_hash: str,
    surface_prefix_bindings: tuple[SurfacePrefixBinding, ...],
    parent_snapshot: ParentDecisionSnapshotReference | None,
) -> dict:
    if parent_snapshot is not None:
        raise TrajectoryCaseError("parent snapshot attachment is disabled in V1")
    return {
        "contract_version": TRAJECTORY_CASE_CONTRACT_VERSION,
        "timeline_id": timeline_id,
        "adapter_kind": adapter_kind,
        "adapter_version": adapter_version,
        "source_capability": source_capability,
        "required_columns": list(required_columns),
        "optional_columns_present": list(optional_columns_present),
        "decision_key": decision_key,
        "decision_prefix_hash": decision_prefix_hash,
        "surface_prefix_binding_hashes": sorted(
            binding.stable_binding_hash for binding in surface_prefix_bindings
        ),
        "parent_snapshot": None,
    }


@dataclass(frozen=True)
class TrajectoryDecisionCase:
    """Immutable neutral case identity frozen at one explicit decision boundary."""

    contract_version: str
    case_id: str
    case_hash: str
    timeline_id: str
    adapter_kind: TIMELINE_ADAPTER_KIND
    adapter_version: str
    source_capability: TIMELINE_CAPABILITY
    required_columns: tuple[str, ...]
    optional_columns_present: tuple[str, ...]
    decision_key: InformationKey
    decision_prefix_hash: str
    surface_prefix_bindings: tuple[SurfacePrefixBinding, ...]
    parent_snapshot: ParentDecisionSnapshotReference | None
    source_provenance: CaseSourceProvenance

    def __post_init__(self) -> None:
        if self.contract_version != TRAJECTORY_CASE_CONTRACT_VERSION:
            raise TrajectoryCaseError("trajectory case contract version mismatch")
        _require_nonempty(self.timeline_id, "timeline_id")
        _require_nonempty(self.adapter_version, "adapter_version")
        _require_sha256(self.decision_prefix_hash, "decision_prefix_hash")
        _require_sha256(self.case_id, "case_id")
        _require_sha256(self.case_hash, "case_hash")
        if not isinstance(self.adapter_kind, TIMELINE_ADAPTER_KIND):
            raise TrajectoryCaseError("invalid case adapter_kind")
        if not isinstance(self.source_capability, TIMELINE_CAPABILITY):
            raise TrajectoryCaseError("invalid case source_capability")
        if not isinstance(self.required_columns, tuple) or any(
            not isinstance(column, str) or not column for column in self.required_columns
        ):
            raise TrajectoryCaseError("required_columns must be an immutable string tuple")
        if not isinstance(self.optional_columns_present, tuple) or any(
            not isinstance(column, str) or not column for column in self.optional_columns_present
        ):
            raise TrajectoryCaseError("optional_columns_present must be an immutable string tuple")
        if self.decision_key.timeline_id != self.timeline_id:
            raise TrajectoryCaseError("decision key timeline mismatch")
        if self.decision_key.information_phase not in _LEGAL_DECISION_PHASES:
            raise TrajectoryCaseError("decision key phase is not a completed-row boundary")
        if not isinstance(self.surface_prefix_bindings, tuple) or any(
            not isinstance(binding, SurfacePrefixBinding)
            for binding in self.surface_prefix_bindings
        ):
            raise TrajectoryCaseError("surface_prefix_bindings must be an immutable tuple")
        if tuple(sorted(self.surface_prefix_bindings, key=lambda b: b.stable_binding_hash)) != self.surface_prefix_bindings:
            raise TrajectoryCaseError("surface_prefix_bindings must be canonically ordered")
        if len({b.stable_binding_hash for b in self.surface_prefix_bindings}) != len(
            self.surface_prefix_bindings
        ):
            raise TrajectoryCaseError("duplicate stable surface prefix binding")
        if any(
            b.timeline_id != self.timeline_id or b.boundary_key != self.decision_key
            for b in self.surface_prefix_bindings
        ):
            raise TrajectoryCaseError("surface prefix binding is not frozen at this decision")
        if self.parent_snapshot is not None:
            raise TrajectoryCaseError("parent snapshot attachment is disabled in V1")
        if not isinstance(self.source_provenance, CaseSourceProvenance):
            raise TrajectoryCaseError("source_provenance is required")
        b2_domains = {
            binding.domain
            for binding in self.surface_prefix_bindings
            if binding.surface_family == "STAGE4B2"
        }
        source_hash_columns = {
            column for column, _ in self.source_provenance.market_source_column_hashes
        }
        if b2_domains:
            try:
                required_source_columns = {
                    column
                    for domain in b2_domains
                    for column in required_stage4b2_market_source_columns(domain)
                }
            except Stage4B2ConsistencyError as exc:
                raise TrajectoryCaseError(str(exc)) from exc
            if not required_source_columns.issubset(source_hash_columns):
                missing = sorted(required_source_columns - source_hash_columns)
                raise TrajectoryCaseError(f"Stage4B2 case lacks market source evidence for {missing}")
            if any(
                len(hashes) <= self.decision_key.bar_position
                for _, hashes in self.source_provenance.market_source_column_hashes
            ):
                raise TrajectoryCaseError("Stage4B2 market source evidence does not reach the decision boundary")
        elif self.source_provenance.market_source_column_hashes:
            raise TrajectoryCaseError("market source hashes require a Stage4B2 surface binding")
        artifact_reference = self.source_provenance.source_artifact_reference
        if artifact_reference is not None:
            if artifact_reference.timeline_id != self.timeline_id:
                raise TrajectoryCaseError("source artifact reference timeline mismatch")
            if artifact_reference.timeline_hash != self.source_provenance.timeline_hash:
                raise TrajectoryCaseError("source artifact reference timeline hash mismatch")
        if tuple(
            sorted(
                (
                    SurfaceVersionReference(
                        b.stable_binding_hash,
                        b.source_surface_id,
                        b.source_timeline_hash,
                        b.verification_scope,
                    )
                    for b in self.surface_prefix_bindings
                ),
                key=lambda item: item.stable_binding_hash,
            )
        ) != self.source_provenance.surface_versions:
            raise TrajectoryCaseError("surface provenance does not match prefix bindings")

        identity = _case_identity_payload(
            timeline_id=self.timeline_id,
            adapter_kind=self.adapter_kind,
            adapter_version=self.adapter_version,
            source_capability=self.source_capability,
            required_columns=self.required_columns,
            optional_columns_present=self.optional_columns_present,
            decision_key=self.decision_key,
            decision_prefix_hash=self.decision_prefix_hash,
            surface_prefix_bindings=self.surface_prefix_bindings,
            parent_snapshot=self.parent_snapshot,
        )
        expected_id = canonical_sha256(domain="TRAJECTORY_DECISION_CASE_ID_V1", payload=identity)
        expected_hash = canonical_sha256(
            domain="TRAJECTORY_DECISION_CASE_HASH_V1",
            payload={"case_id": expected_id, "identity": identity},
        )
        if self.case_id != expected_id or self.case_hash != expected_hash:
            raise TrajectoryCaseError("trajectory case identity/hash mismatch")


def _make_surface_prefix_binding(
    surface: object,
    boundary_key: InformationKey,
    *,
    market_history: pd.DataFrame | None = None,
    market_source_column_hashes: tuple[tuple[str, tuple[str, ...]], ...] | None = None,
    source_through_position: int | None = None,
) -> SurfacePrefixBinding:
    """Verify and bind one supported public Stage 4 surface prefix."""
    verification_scope = None
    if isinstance(surface, s4a.Stage4ADomainSurface):
        binding = s4a.project_surface_prefix(surface=surface, boundary_key=boundary_key)
        family = "STAGE4A"
        domain = surface.domain
        contract = surface.contract_version
        config_hash = surface.configuration_binding_hash
        source_surface_id = surface.surface_id
        source_timeline_hash = surface.timeline_hash
        adapter_kind = surface.adapter_kind
        timeline_id = surface.timeline_id
    elif isinstance(surface, s4b1.Stage4B1StructureSurface):
        binding = s4b1.project_structure_prefix(surface=surface, boundary_key=boundary_key)
        family = "STAGE4B1"
        domain = surface.domain
        contract = surface.contract_version
        config_hash = canonical_sha256(
            domain="TRAJECTORY_STAGE4B1_CONFIG_BINDING_V1",
            payload={
                "high_col": surface.high_col,
                "low_col": surface.low_col,
                "swing_policy_hash": surface.swing_policy_hash,
            },
        )
        source_surface_id = surface.surface_id
        source_timeline_hash = surface.timeline_hash
        adapter_kind = surface.adapter_kind
        timeline_id = surface.timeline_id
    elif isinstance(
        surface,
        (
            s4b2.Stage4B2LiquiditySurface,
            s4b2.Stage4B2OrderBlockSurface,
            s4b2.Stage4B2FVGSurface,
            s4b2.Stage4B2DealingRangeSurface,
        ),
    ):
        try:
            consistency = verify_stage4b2_consistency(
                surface,
                market_history=market_history,
                market_source_column_hashes=market_source_column_hashes,
                source_through_position=source_through_position,
            )
        except Stage4B2ConsistencyError as exc:
            raise TrajectoryCaseError(str(exc)) from exc
        verification_scope = consistency.verification_scope
        # The private snapshot is checked before the decision-prefix projector;
        # the projector may repeat its existing integrity check, not the new cross-table pass.
        binding = s4b2.project_domain_prefix(surface=surface, boundary_key=boundary_key)
        family = "STAGE4B2"
        domain = binding.domain
        contract = {
            "LIQUIDITY": s4b2.CONTRACT_LIQUIDITY,
            "ORDER_BLOCK": s4b2.CONTRACT_ORDER_BLOCK,
            "FVG": s4b2.CONTRACT_FVG,
            "DEALING_RANGE": s4b2.CONTRACT_DEALING_RANGE,
        }[domain]
        config_hash = canonical_sha256(
            domain="TRAJECTORY_STAGE4B2_CONFIG_BINDING_V1",
            payload={"domain": domain, "contract_version": contract},
        )
        source_surface_id = surface.surface_id
        source_timeline_hash = surface.timeline_hash
        adapter_kind = surface.adapter_kind
        timeline_id = surface.timeline_id
    elif isinstance(surface, s4c.Stage4CHtfScaleSurface):
        binding = s4c.project_htf_scale_prefix(surface=surface, boundary_key=boundary_key)
        family = "STAGE4C"
        domain = surface.domain
        contract = surface.contract_version
        config_hash = canonical_sha256(
            domain="TRAJECTORY_STAGE4C_CONFIG_BINDING_V1",
            payload={
                "scale_name": surface.scale_name,
                "scale_duration_ns": surface.scale_duration_ns,
                "cadence_contract_hash": surface.cadence_contract_hash,
            },
        )
        source_surface_id = surface.surface_id
        source_timeline_hash = surface.timeline_hash
        adapter_kind = surface.adapter_kind
        timeline_id = surface.timeline_id
    else:
        raise TrajectoryCaseError(f"unsupported Stage 4 surface type: {type(surface).__name__}")

    if binding.boundary_key != boundary_key:
        raise TrajectoryCaseError("public surface prefix boundary mismatch")
    stable_hash = _surface_prefix_identity_hash(
        surface_family=family,
        domain=domain,
        contract_version=contract,
        configuration_identity_hash=config_hash,
        timeline_id=timeline_id,
        adapter_kind=adapter_kind,
        boundary_key=boundary_key,
        prefix_hash=binding.prefix_hash,
        prefix_row_count=binding.prefix_row_count,
    )
    return SurfacePrefixBinding(
        surface_family=family,
        domain=domain,
        contract_version=contract,
        configuration_identity_hash=config_hash,
        timeline_id=timeline_id,
        adapter_kind=adapter_kind,
        boundary_key=boundary_key,
        prefix_hash=binding.prefix_hash,
        prefix_row_count=binding.prefix_row_count,
        stable_binding_hash=stable_hash,
        source_surface_id=source_surface_id,
        source_timeline_hash=source_timeline_hash,
        verification_scope=verification_scope,
    )


def _verify_case_source_prefix_snapshot(
    *,
    case: TrajectoryDecisionCase,
    timeline: MarketObservationTimeline,
    adapter: TimelineAdapter,
    market_snapshot: pd.DataFrame,
) -> None:
    """Verify the exact private market snapshot used by the caller."""
    if not isinstance(case, TrajectoryDecisionCase):
        raise TypeError("case must be a TrajectoryDecisionCase")
    if not isinstance(timeline, MarketObservationTimeline):
        raise TypeError("timeline must be a MarketObservationTimeline")
    if not isinstance(adapter, (PositionalTimelineAdapter, TimeIndexedTimelineAdapter)):
        raise TypeError("a supported TimelineAdapter is required")
    if timeline.timeline_id != case.timeline_id or adapter.timeline_id != case.timeline_id:
        raise TrajectoryCaseError("case/timeline/adapter identity mismatch")
    if (
        timeline.adapter_kind != case.adapter_kind
        or timeline.adapter_version != case.adapter_version
        or timeline.source_capability != case.source_capability
        or tuple(timeline.required_columns) != case.required_columns
        or tuple(timeline.optional_columns_present) != case.optional_columns_present
    ):
        raise TrajectoryCaseError("case source contract changed")
    timeline.verify(adapter=adapter, market_history=market_snapshot)
    try:
        adapter.validate_key(case.decision_key, market_snapshot.index)
    except Exception as exc:
        raise TrajectoryCaseError(f"case decision key is unavailable: {exc}") from exc
    current_prefix_hash = _decision_prefix_hash(
        timeline=timeline,
        adapter=adapter,
        market_history=market_snapshot,
        decision_position=case.decision_key.bar_position,
    )
    if current_prefix_hash != case.decision_prefix_hash:
        raise TrajectoryCaseError("supplied history changed the frozen decision prefix")


def verify_case_source_prefix(
    *,
    case: TrajectoryDecisionCase,
    timeline: MarketObservationTimeline,
    adapter: TimelineAdapter,
    market_history: pd.DataFrame,
) -> None:
    """Capture then verify supplied rows; hashes do not imply durable retrieval."""
    market_snapshot = snapshot_market_history(market_history)
    _verify_case_source_prefix_snapshot(
        case=case,
        timeline=timeline,
        adapter=adapter,
        market_snapshot=market_snapshot,
    )


def _verify_surface_prefix_snapshot(
    *,
    case: TrajectoryDecisionCase,
    surface_snapshot: object,
    source_through_position: int | None = None,
) -> SurfacePrefixBinding:
    if not isinstance(case, TrajectoryDecisionCase):
        raise TypeError("case must be a TrajectoryDecisionCase")
    checked_through = (
        case.decision_key.bar_position
        if source_through_position is None
        else source_through_position
    )
    binding = _make_surface_prefix_binding(
        surface_snapshot,
        case.decision_key,
        market_source_column_hashes=case.source_provenance.market_source_column_hashes,
        source_through_position=checked_through,
    )
    matches = [
        prior
        for prior in case.surface_prefix_bindings
        if prior.stable_binding_hash == binding.stable_binding_hash
    ]
    if len(matches) != 1:
        raise TrajectoryCaseError("surface is not bound to this decision case")
    return binding


def verify_surface_prefix_compatibility(
    *,
    case: TrajectoryDecisionCase,
    surface: object,
) -> SurfacePrefixBinding:
    """Capture first, then verify one supplied surface against the frozen case.

    A newer whole-history surface may be used after future append. Its full
    timeline/surface IDs can differ, but its public prefix binding at the case
    decision must match exactly.
    """
    surface_snapshot = snapshot_stage4_surface(surface)
    return _verify_surface_prefix_snapshot(case=case, surface_snapshot=surface_snapshot)


def create_trajectory_decision_case(
    *,
    timeline: MarketObservationTimeline,
    adapter: TimelineAdapter,
    market_history: pd.DataFrame,
    decision_key: InformationKey,
    surfaces: Iterable[object],
    parent_snapshot: ParentDecisionSnapshotReference | None,
) -> TrajectoryDecisionCase:
    """Create an immutable case from sealed rows and verified visible prefixes.

    ``surfaces`` and ``parent_snapshot`` are required keyword arguments so an
    absent surface/parent is explicit. No horizon, sampling, candidate pair,
    future path, outcome, or strategy field participates in case construction.
    """
    if parent_snapshot is not None:
        raise TrajectoryCaseError("parent snapshot attachment is disabled in V1")
    if not isinstance(timeline, MarketObservationTimeline):
        raise TypeError("timeline must be a MarketObservationTimeline")
    if not isinstance(adapter, (PositionalTimelineAdapter, TimeIndexedTimelineAdapter)):
        raise TypeError("a supported TimelineAdapter is required")
    if not isinstance(market_history, pd.DataFrame):
        raise TypeError("market_history must be a caller-supplied DataFrame")
    if not isinstance(decision_key, InformationKey):
        raise TypeError("decision_key must be an InformationKey")

    try:
        raw_surface_inputs = tuple(surfaces)
    except TypeError as exc:
        raise TrajectoryCaseError("surfaces must be an iterable of public Stage 4 surfaces") from exc
    # Capture every mutable input before any integrity/prefix verification.
    market_snapshot = snapshot_market_history(market_history)
    surface_inputs = tuple(snapshot_stage4_surface(surface) for surface in raw_surface_inputs)

    if decision_key.information_phase not in _LEGAL_DECISION_PHASES:
        raise TrajectoryCaseError("decision key must be completed-row or research-snapshot available")
    if decision_key.timeline_id != timeline.timeline_id or adapter.timeline_id != timeline.timeline_id:
        raise TrajectoryCaseError("decision/timeline/adapter identity mismatch")

    # Verify and derive only from the exact private market snapshot captured above.
    timeline.verify(adapter=adapter, market_history=market_snapshot)
    try:
        adapter.validate_key(decision_key, market_snapshot.index)
    except Exception as exc:
        raise TrajectoryCaseError(f"decision key is unavailable on supplied timeline: {exc}") from exc

    try:
        market_source_column_hashes = capture_stage4b2_market_source_column_hashes(
            market_snapshot, surface_inputs
        )
    except Stage4B2ConsistencyError as exc:
        raise TrajectoryCaseError(str(exc)) from exc

    decision_prefix_hash = _decision_prefix_hash(
        timeline=timeline,
        adapter=adapter,
        market_history=market_snapshot,
        decision_position=decision_key.bar_position,
    )

    if any(
        getattr(surface, "timeline_id", None) != timeline.timeline_id
        or getattr(surface, "timeline_hash", None) != timeline.timeline_hash
        or getattr(surface, "adapter_kind", None) != timeline.adapter_kind
        for surface in surface_inputs
    ):
        raise TrajectoryCaseError("surface full-history binding does not match supplied timeline")

    bindings = tuple(
        sorted(
            (
                _make_surface_prefix_binding(
                    surface, decision_key, market_history=market_snapshot
                )
                for surface in surface_inputs
            ),
            key=lambda item: item.stable_binding_hash,
        )
    )
    if len({binding.stable_binding_hash for binding in bindings}) != len(bindings):
        raise TrajectoryCaseError("duplicate Stage 4 prefix binding")

    surface_versions = tuple(
        SurfaceVersionReference(
            stable_binding_hash=binding.stable_binding_hash,
            source_surface_id=binding.source_surface_id,
            source_timeline_hash=binding.source_timeline_hash,
            verification_scope=binding.verification_scope,
        )
        for binding in bindings
    )
    artifact_reference = None  # no durable timeline/artifact resolver exists in this repository
    provenance_hash = _provenance_hash(
        timeline_hash=timeline.timeline_hash,
        source_artifact_reference=artifact_reference,
        surface_versions=surface_versions,
        market_source_column_hashes=market_source_column_hashes,
    )
    provenance = CaseSourceProvenance(
        timeline_hash=timeline.timeline_hash,
        source_artifact_reference=artifact_reference,
        surface_versions=surface_versions,
        provenance_binding_hash=provenance_hash,
        market_source_column_hashes=market_source_column_hashes,
    )

    identity = _case_identity_payload(
        timeline_id=timeline.timeline_id,
        adapter_kind=timeline.adapter_kind,
        adapter_version=timeline.adapter_version,
        source_capability=timeline.source_capability,
        required_columns=tuple(timeline.required_columns),
        optional_columns_present=tuple(timeline.optional_columns_present),
        decision_key=decision_key,
        decision_prefix_hash=decision_prefix_hash,
        surface_prefix_bindings=bindings,
        parent_snapshot=parent_snapshot,
    )
    case_id = canonical_sha256(domain="TRAJECTORY_DECISION_CASE_ID_V1", payload=identity)
    case_hash = canonical_sha256(
        domain="TRAJECTORY_DECISION_CASE_HASH_V1",
        payload={"case_id": case_id, "identity": identity},
    )
    return TrajectoryDecisionCase(
        contract_version=TRAJECTORY_CASE_CONTRACT_VERSION,
        case_id=case_id,
        case_hash=case_hash,
        timeline_id=timeline.timeline_id,
        adapter_kind=timeline.adapter_kind,
        adapter_version=timeline.adapter_version,
        source_capability=timeline.source_capability,
        required_columns=tuple(timeline.required_columns),
        optional_columns_present=tuple(timeline.optional_columns_present),
        decision_key=decision_key,
        decision_prefix_hash=decision_prefix_hash,
        surface_prefix_bindings=bindings,
        parent_snapshot=parent_snapshot,
        source_provenance=provenance,
    )
