"""Offline comparison adapter for existing causal market-movement producers.

This module adds no swing detector, wave rule, selection score, signal, or outcome
label. It composes the public S1/S2/S3/S5 contracts with the existing causal
market-context core and its Stage4A/4B/4C producers. All owner-provided policy
values and authorization references are preserved; references are not
cryptographically authenticated by this adapter.

The CLI reads an existing local 1-minute OHLC CSV only. It never downloads,
repairs, sorts, or regenerates market data.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import itertools
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
import sys
import time
import tracemalloc
from typing import Any, Callable, Iterable, Iterator, Mapping, Sequence, TextIO

import numpy as np
import pandas as pd

from trading_system.market_understanding.availability import InformationAxis
from trading_system.market_understanding.contracts import SchemaIdentity, SchemaViolation, TypedState
from trading_system.market_understanding.detector_witness import (
    DetectorPolicyWitnessSpec,
    DetectorWitnessBundle,
    adapt_detector_witness_stream,
    query_witness_surface_as_of,
    verify_prefix_witness_invariance,
)
from trading_system.market_understanding.policy_governance import (
    DATASET_ROLE_DEVELOPMENT_FIT,
    DATASET_ROLE_DEVELOPMENT_SELECTION,
    LEGAL_CALIBRATION_PROVENANCE_KINDS,
    POLICY_AUTHORITY_KIND_MUF,
    PROVENANCE_DEVELOPMENT_FIT,
    DatasetIdentityArtifact,
    DatasetRoleArtifact,
    PolicyArtifact,
    PolicyScopeMismatch,
    SelectionBlockedError,
    verify_policy_artifact_reproduction,
)
from trading_system.market_understanding.price_path import PublishedOhlcBarFact
from trading_system.market_understanding.wave_representation import (
    CandidateWaveRepresentationBundle,
    CandidateWaveRepresentationSpec,
    LEGAL_REPRESENTATION_FAMILIES,
    S5_IDENTITY_RULE_NOT_CONFIGURED,
    S5_POLICY_AUTHORITY_MISSING,
    construct_candidate_wave_representation,
)
from trading_system.research.hashing import canonical_sha256
from trading_system.research.information_time import (
    InformationKey,
    InformationPhase,
    TimeIndexedTimelineAdapter,
)
from trading_system.research.trajectory.causal_market_context_core import (
    CausalMarketContextCoreError,
    CoreBundle,
    ReplayLimits,
    ReplayMemoryResult,
    ReplaySummary,
    SwingPolicyConfig,
    build_causal_market_context_core,
    replay_causal_market_context,
)
from trading_system.sources import SourceArtifactIdentity
from trading_system.sources.binance_spot_kline_ohlc_source import KLINES_SCHEMA_CONTRACT
from trading_system.structure.swing_detector import EmpiricalConfirmationPolicy


REPORT_SCHEMA_VERSION = "MARKET_MOVEMENT_REPRESENTATION_RESEARCH_V1"
SUITABILITY_NOT_ESTABLISHED = "SUITABILITY_NOT_ESTABLISHED"
BLOCKED_MISSING_AUTHORIZED_POLICY = "BLOCKED_MISSING_AUTHORIZED_POLICY"
_AUTH_REF_PRESENT = "REFERENCE_PRESENT_NOT_AUTHENTICATED"
_CALLER_FRAME_SCHEMA = SchemaIdentity("CALLER_SUPPLIED_OHLC", "CALLER_FRAME_V1")


class _ResearchProgress:
    """Low-volume stderr progress with flushed, monotonic wall-clock timings."""

    def __init__(self, stream: TextIO | None = None) -> None:
        self.stream = sys.stderr if stream is None else stream
        self.started_at = time.perf_counter()
        self._finished = False
        self._stream_failed = False

    def emit(self, message: str) -> None:
        if self._stream_failed:
            return
        elapsed = time.perf_counter() - self.started_at
        try:
            print(f"[movement-research +{elapsed:.2f}s] {message}", file=self.stream, flush=True)
        except (OSError, ValueError):
            # A closed/redirection-broken progress stream must not affect research.
            self._stream_failed = True

    def finish(self, status: str, detail: str | None = None) -> None:
        if self._finished:
            return
        suffix = f"; {detail}" if detail else ""
        self.emit(f"run {status}{suffix}")
        self._finished = True

    @contextmanager
    def stage(self, label: str) -> Iterator[Callable[[str], None]]:
        started = time.perf_counter()
        self.emit(f"{label}: started")
        details: list[str] = []

        def complete(detail: str = "") -> None:
            if detail:
                details.append(detail)

        try:
            yield complete
        except BaseException as exc:
            elapsed = time.perf_counter() - started
            state = "interrupted" if isinstance(exc, (KeyboardInterrupt, SystemExit)) else "failed"
            self.emit(f"{label}: {state} after {elapsed:.2f}s ({type(exc).__name__})")
            raise
        else:
            elapsed = time.perf_counter() - started
            suffix = f"; {('; '.join(details))}" if details else ""
            self.emit(f"{label}: completed in {elapsed:.2f}s{suffix}")


@contextmanager
def _progress_stage(
    progress: _ResearchProgress | None,
    label: str,
) -> Iterator[Callable[[str], None]]:
    if progress is None:
        yield lambda _detail="": None
    else:
        with progress.stage(label) as complete:
            yield complete


# These are the current public Stage4B1 result fields. Keeping the partition here
# describes *which output fields differ*; it assigns neither meaning nor score.
_GEOMETRY_FIELDS = (
    "candidate_side",
    "candidate_origin_position",
    "candidate_price",
    "swing_high_confirmed",
    "swing_low_confirmed",
    "swing_origin_position",
    "swing_price",
)
_OPERATIONAL_FIELDS = (
    "structure_event_type",
    "swing_sequence_class",
    "comparison_available",
    "previous_same_type_price",
    "previous_same_type_origin_position",
    "current_structure_swing_price",
    "current_structure_origin_position",
    "current_structure_confirmation_position",
    "structure_state_before",
    "structure_state_after",
    "structural_break_event",
    "high_wick_breach_event",
    "high_close_breach_event",
    "low_wick_breach_event",
    "low_close_breach_event",
    "high_wick_only_breach_event",
    "low_wick_only_breach_event",
)
_AVAILABILITY_FIELDS = (
    "swing_confirmation_position",
    "monitored_high_confirmation_position",
    "monitored_high_first_wick_breach_position",
    "monitored_high_first_close_breach_position",
    "monitored_low_confirmation_position",
    "monitored_low_first_wick_breach_position",
    "monitored_low_first_close_breach_position",
)
_POLICY_EVIDENCE_FIELDS = (
    "candidate_confirmation_threshold",
    "swing_confirmation_threshold",
    "candidate_continuation_history_count",
    "candidate_confirmed_history_count",
    "swing_continuation_history_count",
    "swing_confirmed_history_count",
    "swing_confirmed_history_percentile",
)


@dataclass(frozen=True)
class DeclaredSwingPolicy:
    """An existing CMC swing configuration plus its caller-supplied auth reference."""

    config: SwingPolicyConfig
    owner_authorization_ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.config, SwingPolicyConfig):
            raise TypeError("config must be the existing SwingPolicyConfig")
        if not isinstance(self.owner_authorization_ref, str) or not self.owner_authorization_ref.strip():
            raise ValueError("owner_authorization_ref must be an explicit nonempty reference")


@dataclass(frozen=True)
class S5RepresentationPlan:
    """Exact public S5 inputs; this adapter does not define wave identity or geometry."""

    representation_spec: CandidateWaveRepresentationSpec
    policy_artifact: PolicyArtifact
    confirmation_policy: EmpiricalConfirmationPolicy
    dataset_identity: DatasetIdentityArtifact
    dataset_role: DatasetRoleArtifact
    recomputed_recipe_hash: str

    def __post_init__(self) -> None:
        if not isinstance(self.representation_spec, CandidateWaveRepresentationSpec):
            raise TypeError("representation_spec must be CandidateWaveRepresentationSpec")
        if not isinstance(self.policy_artifact, PolicyArtifact):
            raise TypeError("policy_artifact must be PolicyArtifact")
        if not isinstance(self.confirmation_policy, EmpiricalConfirmationPolicy):
            raise TypeError("confirmation_policy must be an explicit EmpiricalConfirmationPolicy")
        if not isinstance(self.dataset_identity, DatasetIdentityArtifact):
            raise TypeError("dataset_identity must be DatasetIdentityArtifact")
        if not isinstance(self.dataset_role, DatasetRoleArtifact):
            raise TypeError("dataset_role must be DatasetRoleArtifact")
        if not isinstance(self.recomputed_recipe_hash, str) or not self.recomputed_recipe_hash.strip():
            raise ValueError("recomputed_recipe_hash must be an explicit nonempty reference")


@dataclass(frozen=True)
class MovementResearchRun:
    """Run result; memory mode retains records, disk mode points to complete JSONL outputs."""

    report: Mapping[str, Any]
    core_bundle: CoreBundle | None
    replay: ReplayMemoryResult | ReplaySummary | None
    s5_bundles: Mapping[str, CandidateWaveRepresentationBundle]
    witness_bundles: Mapping[str, DetectorWitnessBundle]
    s5_blocked: tuple[Mapping[str, Any], ...]
    turning_point_records: tuple[Mapping[str, Any], ...]
    disagreement_reference_rows: tuple[Mapping[str, Any], ...]
    output_directory: str | None = None
    s5_witness_bundles: Mapping[str, DetectorWitnessBundle] = field(default_factory=dict)


def _jsonable(value: Any) -> Any:
    if value is None or value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, InformationKey):
        return {
            "information_key_version": value.information_key_version,
            "timeline_id": value.timeline_id,
            "bar_position": int(value.bar_position),
            "event_time_utc": _jsonable(value.event_time_utc),
            "information_phase": value.information_phase.value,
            "deterministic_sequence": int(value.deterministic_sequence),
        }
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return None
        if value.tz is None:
            raise ValueError("naive timestamps are not serializable")
        return value.tz_convert("UTC").isoformat().replace("+00:00", "Z")
    if isinstance(value, pd.Timedelta):
        return {"nanoseconds": int(value.value)}
    if isinstance(value, TypedState):
        return value.value
    if isinstance(value, SchemaIdentity):
        return value.as_payload()
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [_jsonable(item) for item in value]
    if isinstance(value, np.ndarray):
        return [_jsonable(item) for item in value.tolist()]
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        result = float(value)
        return result if math.isfinite(result) else None
    if isinstance(value, str):
        return value
    if hasattr(value, "value") and isinstance(value.value, (str, int, float, bool)):
        return _jsonable(value.value)
    if hasattr(value, "__dataclass_fields__"):
        return {name: _jsonable(getattr(value, name)) for name in value.__dataclass_fields__}
    return str(value)


def _canonical_sha256(payload: Any) -> str:
    encoded = json.dumps(_jsonable(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _process_peak_rss_bytes() -> int | None:
    """Return the process high-water RSS when the platform exposes it."""
    try:
        import resource
        peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    except (ImportError, AttributeError, OSError, ValueError):
        return None
    # ru_maxrss units are platform-specific; only convert platforms with a
    # documented convention here rather than claiming bytes elsewhere.
    if sys.platform == "darwin":
        return peak
    if sys.platform.startswith("linux"):
        return peak * 1024
    return None


def _is_missing(value: Any) -> bool:
    try:
        result = pd.isna(value)
    except (TypeError, ValueError):
        return False
    return bool(result) if isinstance(result, (bool, np.bool_)) else False


def _same_value(left: Any, right: Any) -> bool:
    left_missing, right_missing = _is_missing(left), _is_missing(right)
    if left_missing or right_missing:
        return left_missing and right_missing
    if isinstance(left, (float, np.floating)) and isinstance(right, (float, np.floating)):
        return float(left) == float(right)
    try:
        comparison = left == right
        return bool(comparison) if isinstance(comparison, (bool, np.bool_)) else False
    except (TypeError, ValueError):
        return False


def _policy_summary(declaration: DeclaredSwingPolicy) -> dict[str, Any]:
    config = declaration.config
    return {
        "policy_id": config.policy_id,
        "representation_id": config.representation_id,
        "policy_identity_sha256": config.identity_sha256,
        "policy_artifact_sha256": config.artifact_sha256,
        "policy_parameters": config.payload(),
        "owner_authorization_ref": declaration.owner_authorization_ref,
        "authorization_reference_state": _AUTH_REF_PRESENT,
        "scope": "ONE_SHARED_INPUT_TIMELINE; REPRESENTATION_IS_POLICY_IDENTIFIED",
    }


def _expected_source_content_hash(
    market_history: pd.DataFrame,
    *,
    source_file_sha256: str | None,
    source_validation: Any,
) -> str | None:
    if source_file_sha256 is not None:
        return source_file_sha256
    provenance = getattr(source_validation, "provenance", None)
    validated_hash = getattr(provenance, "source_file_sha256", None)
    if isinstance(validated_hash, str) and len(validated_hash) == 64:
        return validated_hash
    if not isinstance(market_history, pd.DataFrame) or not isinstance(market_history.index, pd.DatetimeIndex) or market_history.index.tz is None:
        return None
    normalized = market_history.copy(deep=True)
    index = normalized.index.tz_convert("UTC")
    try:
        index = index.as_unit("ns")
    except AttributeError:
        index = pd.DatetimeIndex(index.asi8, tz="UTC")
    normalized.index = index
    try:
        return canonical_sha256(domain="CORE_CALLER_FRAME_HASH_V1", payload=normalized)
    except Exception:
        return None


def _s5_plan_precheck(
    plan: S5RepresentationPlan,
    *,
    timeline_id: str,
    source_schema: SchemaIdentity,
    first_key: InformationKey,
    last_key: InformationKey,
    expected_content_hash: str | None,
) -> tuple[str | None, str | None]:
    """Return (blocked_status, detail), without attempting to repair a mismatch."""
    spec, policy, dataset, role = (
        plan.representation_spec,
        plan.policy_artifact,
        plan.dataset_identity,
        plan.dataset_role,
    )
    if spec.identity_rule_ref is TypedState.NOT_CONFIGURED:
        return "BLOCKED_IDENTITY_RULE_NOT_CONFIGURED", S5_IDENTITY_RULE_NOT_CONFIGURED
    if policy.detector_policy_witness_ref != DetectorPolicyWitnessSpec.from_policy(plan.confirmation_policy).spec_identity:
        return "BLOCKED_POLICY_MISMATCH", "PolicyArtifact detector witness reference differs from recomputed S2 policy identity"
    try:
        verify_policy_artifact_reproduction(
            policy,
            recomputed_detector_policy_witness_ref=DetectorPolicyWitnessSpec.from_policy(plan.confirmation_policy).spec_identity,
            recomputed_recipe_hash=plan.recomputed_recipe_hash,
        )
    except SchemaViolation as exc:
        return "BLOCKED_POLICY_MISMATCH", str(exc)
    if spec.scope_timeline_id != timeline_id or policy.scope_timeline_id != timeline_id or dataset.timeline_id != timeline_id:
        return "BLOCKED_POLICY_SCOPE_MISMATCH", "timeline scope differs from supplied OHLC timeline"
    if spec.scope_axis is not InformationAxis.TIME_INDEXED or policy.scope_axis is not InformationAxis.TIME_INDEXED or dataset.axis is not InformationAxis.TIME_INDEXED:
        return "BLOCKED_POLICY_SCOPE_MISMATCH", "the supplied OHLC runner requires TIME_INDEXED S5 scope"
    if policy.scope_representation_id != spec.representation_id:
        return "BLOCKED_POLICY_SCOPE_MISMATCH", "PolicyArtifact scope_representation_id differs from CandidateWaveRepresentationSpec"
    if dataset.source_identity != source_schema:
        return "BLOCKED_DATASET_SCOPE_MISMATCH", "DatasetIdentityArtifact source schema differs from the supplied OHLC surface"
    if expected_content_hash is None or dataset.content_hash != expected_content_hash:
        return "BLOCKED_DATASET_SCOPE_MISMATCH", "DatasetIdentityArtifact content hash does not bind the exact supplied OHLC source bytes/frame"
    if dataset.start_key != first_key or dataset.end_key != last_key:
        return "BLOCKED_DATASET_SCOPE_MISMATCH", "DatasetIdentityArtifact interval is not exactly the supplied OHLC interval"
    if role.dataset_id != dataset.dataset_id or role.dataset_identity_hash != dataset.dataset_identity_hash:
        return "BLOCKED_DATASET_ROLE_MISMATCH", "DatasetRoleArtifact does not bind the supplied DatasetIdentityArtifact"
    if role.role not in (DATASET_ROLE_DEVELOPMENT_FIT, DATASET_ROLE_DEVELOPMENT_SELECTION):
        return "BLOCKED_FINAL_EVALUATION_DATASET", f"S5 is development-only; received role {role.role!r}"
    return None, None


def _source_schema_for(bundle: CoreBundle) -> SchemaIdentity:
    if bundle.source_state.startswith("BINANCE_"):
        return SchemaIdentity("PUBLISHED_KLINE_OHLC", KLINES_SCHEMA_CONTRACT)
    return _CALLER_FRAME_SCHEMA


def _bars_for_dataset(
    bundle: CoreBundle,
    dataset_id: str,
    source_schema: SchemaIdentity,
    *,
    progress: _ResearchProgress | None = None,
    progress_label: str = "S2 input preparation",
) -> tuple[PublishedOhlcBarFact, ...]:
    bars = []
    total = len(bundle.market)
    progress_step = max(5_000, (total + 9) // 10)
    for position, (_, row) in enumerate(bundle.market.iterrows()):
        key = bundle.adapter.key_for_position(
            bundle.market.index,
            position,
            InformationPhase.COMPLETED_ROW_AVAILABLE,
            0,
        )
        bars.append(
            PublishedOhlcBarFact(
                open_price=float(row["open"]),
                high_price=float(row["high"]),
                low_price=float(row["low"]),
                close_price=float(row["close"]),
                availability_key=key,
                source_identity=source_schema,
                dataset_identity=dataset_id,
                published_bar_record_ref=f"movement-research-input:{dataset_id}:{position}",
            )
        )
        if progress is not None:
            completed = position + 1
            if completed % progress_step == 0 or completed == total:
                progress.emit(f"{progress_label}: prepared bar facts={completed}/{total}")
    return tuple(bars)


def _confirmed_swing_events(frame: pd.DataFrame) -> tuple[tuple[str, int, float, int], ...]:
    events: list[tuple[str, int, float, int]] = []
    for position in range(len(frame)):
        row = frame.iloc[position]
        sides = []
        if not _is_missing(row.get("swing_high_confirmed")) and bool(row.get("swing_high_confirmed")):
            sides.append("HIGH")
        if not _is_missing(row.get("swing_low_confirmed")) and bool(row.get("swing_low_confirmed")):
            sides.append("LOW")
        if not sides:
            continue
        origin = row.get("swing_origin_position")
        price = row.get("swing_price")
        confirmation = row.get("swing_confirmation_position")
        if _is_missing(origin) or _is_missing(price) or _is_missing(confirmation):
            raise CausalMarketContextCoreError("confirmed Stage4B1 swing is missing its public origin/price/availability fields")
        origin_position, confirmation_position = int(origin), int(confirmation)
        if origin_position >= confirmation_position or confirmation_position != position:
            raise CausalMarketContextCoreError("Stage4B1 confirmed swing violates origin/confirmation timing")
        for side in sides:
            events.append((side, origin_position, float(price), confirmation_position))
    return tuple(events)


def _stage4b1_comparisons(
    bundle: CoreBundle,
    replay: ReplayMemoryResult | ReplaySummary,
    *,
    progress: _ResearchProgress | None = None,
) -> list[dict[str, Any]]:
    representations = sorted(bundle.structures, key=lambda item: item.config.representation_id)
    result: list[dict[str, Any]] = []
    fields = tuple(dict.fromkeys(_GEOMETRY_FIELDS + _OPERATIONAL_FIELDS + _AVAILABILITY_FIELDS + _POLICY_EVIDENCE_FIELDS))
    pair_total = len(representations) * (len(representations) - 1) // 2
    field_pair_total = pair_total * len(fields)
    progress_step = max(1, (field_pair_total + 9) // 10)
    field_pairs_examined = 0
    row_value_comparisons = 0
    for pair_index, (left, right) in enumerate(itertools.combinations(representations, 2), start=1):
        left_frame, right_frame = left.structure.frame, right.structure.frame
        mismatch_counts: Counter[str] = Counter()
        for field_index, name in enumerate(fields, start=1):
            if name in left_frame.columns and name in right_frame.columns:
                for position in range(len(bundle.market)):
                    if not _same_value(left_frame.iloc[position][name], right_frame.iloc[position][name]):
                        mismatch_counts[name] += 1
                if progress is not None:
                    row_value_comparisons += len(bundle.market)
            if progress is not None:
                field_pairs_examined += 1
                if field_pairs_examined % progress_step == 0 or field_pairs_examined == field_pair_total:
                    progress.emit(
                        f"representation comparison: Stage4B1 pair={pair_index}/{pair_total}; "
                        f"fields_examined={field_index}/{len(fields)}; "
                        f"field-pairs={field_pairs_examined}/{field_pair_total}; "
                        f"row-value comparisons={row_value_comparisons}"
                    )
        left_events = _confirmed_swing_events(left_frame)
        right_events = _confirmed_swing_events(right_frame)
        left_geometry = Counter((side, origin, price) for side, origin, price, _ in left_events)
        right_geometry = Counter((side, origin, price) for side, origin, price, _ in right_events)
        left_availability: dict[tuple[str, int, float], Counter[int]] = defaultdict(Counter)
        right_availability: dict[tuple[str, int, float], Counter[int]] = defaultdict(Counter)
        for side, origin, price, available in left_events:
            left_availability[(side, origin, price)][available] += 1
        for side, origin, price, available in right_events:
            right_availability[(side, origin, price)][available] += 1
        availability_differences = []
        for signature in sorted(set(left_availability) & set(right_availability)):
            if left_availability[signature] != right_availability[signature]:
                availability_differences.append({
                    "geometry_signature": list(signature),
                    "left_availability_positions": dict(sorted(left_availability[signature].items())),
                    "right_availability_positions": dict(sorted(right_availability[signature].items())),
                })
        result.append({
            "left_representation_id": left.config.representation_id,
            "right_representation_id": right.config.representation_id,
            "left_policy_identity_sha256": left.config.identity_sha256,
            "right_policy_identity_sha256": right.config.identity_sha256,
            "geometric_disagreement": {
                "left_only_confirmed_event_count": sum((left_geometry - right_geometry).values()),
                "right_only_confirmed_event_count": sum((right_geometry - left_geometry).values()),
                "common_confirmed_event_count": sum((left_geometry & right_geometry).values()),
                "event_signature": ["extrema_kind", "origin_position", "exact_producer_price"],
            },
            "operational_definition_disagreement": {
                "field_mismatch_counts": {name: mismatch_counts[name] for name in _OPERATIONAL_FIELDS if mismatch_counts[name]},
                "same_public_2_1A_to_2_1C_chain": True,
                "identity_rule_interpretation": "NOT_INFERRED_FROM_FIELD_DIFFERENCES",
            },
            "information_availability_disagreement": {
                "field_mismatch_counts": {name: mismatch_counts[name] for name in _AVAILABILITY_FIELDS if mismatch_counts[name]},
                "matched_geometry_with_different_confirmation_positions": availability_differences,
            },
            "policy_evidence_field_mismatch_counts": {name: mismatch_counts[name] for name in _POLICY_EVIDENCE_FIELDS if mismatch_counts[name]},
            "task_relevant_disagreement": "NOT_ASSESSED_MISSING_TASK_AND_OUTCOME_AUTHORITY",
            "no_winner_selected": True,
        })
    return result


def _tp_geometry_signature(record: Any) -> tuple[str, int, float]:
    return (str(record.extrema_kind), int(record.origin_position), float(record.swing_price.value))


def _s5_comparisons(
    bundles: Mapping[str, CandidateWaveRepresentationBundle],
    *,
    progress: _ResearchProgress | None = None,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    values = sorted(bundles.items())
    pair_total = len(values) * (len(values) - 1) // 2
    progress_step = max(1, (pair_total + 9) // 10)
    for pair_index, ((left_id, left), (right_id, right)) in enumerate(itertools.combinations(values, 2), start=1):
        left_tp = {item.turning_point_id: item for item in left.authoritative_turning_points}
        right_tp = {item.turning_point_id: item for item in right.authoritative_turning_points}
        left_geom = Counter(_tp_geometry_signature(item) for item in left.authoritative_turning_points)
        right_geom = Counter(_tp_geometry_signature(item) for item in right.authoritative_turning_points)
        left_availability: dict[tuple[str, int, float], Counter[int]] = defaultdict(Counter)
        right_availability: dict[tuple[str, int, float], Counter[int]] = defaultdict(Counter)
        for item in left.authoritative_turning_points:
            left_availability[_tp_geometry_signature(item)][item.availability_key.bar_position] += 1
        for item in right.authoritative_turning_points:
            right_availability[_tp_geometry_signature(item)][item.availability_key.bar_position] += 1
        availability_differences = [
            {"geometry_signature": list(signature), "left_positions": dict(sorted(left_availability[signature].items())), "right_positions": dict(sorted(right_availability[signature].items()))}
            for signature in sorted(set(left_availability) & set(right_availability))
            if left_availability[signature] != right_availability[signature]
        ]

        def wave_signatures(candidate: CandidateWaveRepresentationBundle, tps: Mapping[str, Any]) -> Counter:
            count: Counter = Counter()
            for geometry in candidate.finalized_wave_geometries:
                start = tps.get(geometry.start_turning_point_id)
                end = tps.get(geometry.end_turning_point_id)
                if start is None or end is None:
                    raise CausalMarketContextCoreError("S5 finalized geometry references an absent authoritative turning point")
                count[(_tp_geometry_signature(start), _tp_geometry_signature(end))] += 1
            return count

        left_waves, right_waves = wave_signatures(left, left_tp), wave_signatures(right, right_tp)
        spec_left, spec_right = left.representation_spec, right.representation_spec
        result.append({
            "left_representation_id": left_id,
            "right_representation_id": right_id,
            "left_family_kind": spec_left.family_kind,
            "right_family_kind": spec_right.family_kind,
            "geometric_disagreement": {
                "left_only_finalized_endpoint_pairs": sum((left_waves - right_waves).values()),
                "right_only_finalized_endpoint_pairs": sum((right_waves - left_waves).values()),
                "common_finalized_endpoint_pairs": sum((left_waves & right_waves).values()),
                "endpoint_signature": "existing_S5_authoritative_turning_point_geometry_not_record_identity",
            },
            "operational_definition_disagreement": {
                "family_kind_differs": spec_left.family_kind != spec_right.family_kind,
                "intrinsic_scale_key_differs": _jsonable(spec_left.intrinsic_scale_key) != _jsonable(spec_right.intrinsic_scale_key),
                "identity_rule_ref_differs": _jsonable(spec_left.identity_rule_ref) != _jsonable(spec_right.identity_rule_ref),
                "policy_artifact_hash_differs": left.policy_artifact.policy_hash != right.policy_artifact.policy_hash,
                "construction_algorithm": "SAME_EXISTING_CONSTRUCT_CANDIDATE_WAVE_REPRESENTATION_INTERFACE",
                "identity_rule_semantics": "REFERENCE_ONLY_NOT_INTERPRETED_BY_RUNNER",
            },
            "information_availability_disagreement": {
                "matched_turning_point_geometry_with_different_availability": availability_differences,
            },
            "task_relevant_disagreement": "NOT_ASSESSED_MISSING_TASK_AND_OUTCOME_AUTHORITY",
            "no_winner_selected": True,
        })
        if progress is not None and (pair_index % progress_step == 0 or pair_index == pair_total):
            progress.emit(f"representation comparison: S5 pairs completed={pair_index}/{pair_total}")
    return result


def _domain_counts(summary: ReplaySummary) -> dict[str, int]:
    return {str(key): int(value) for key, value in sorted(summary.candidates_by_domain_representation.items())}


def _iter_boundaries(replay: ReplayMemoryResult | ReplaySummary) -> Iterable[Mapping[str, Any]]:
    if isinstance(replay, ReplayMemoryResult):
        yield from replay.boundaries
        return
    if not replay.output_directory:
        return
    path = Path(replay.output_directory) / "boundary_records.jsonl"
    if not path.is_file():
        return
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def _affected_disagreement_references(replay: ReplayMemoryResult | ReplaySummary) -> Iterable[dict[str, Any]]:
    for boundary in _iter_boundaries(replay):
        payload = _jsonable(boundary)
        content = payload.get("content", {})
        facts = content.get("facts", {})
        disagreement_ids = facts.get("representation_disagreement_ids", ())
        if not disagreement_ids:
            continue
        yield {
            "boundary_record_identity": payload.get("record_identity"),
            "information_key": payload.get("information_key"),
            "representation_disagreement_ids": list(disagreement_ids),
            "core_entity_ids": list(facts.get("new_entity_ids", ())),
            "producer_event_ids": list(facts.get("producer_event_ids", ())),
            "relationship_ids": list(facts.get("relationship_ids", ())),
            "trace_semantics": "REFERENCES_EMITTED_BY_CAUSAL_MARKET_CONTEXT_CORE; JOIN_TO_ITS_ENTITIES_EVENTS_AND_RELATIONSHIPS_STREAMS",
        }


def _iter_turning_point_records(
    bundle: CoreBundle,
    s5_bundles: Mapping[str, CandidateWaveRepresentationBundle],
    witness_bundles: Mapping[str, DetectorWitnessBundle],
    s5_witness_bundles: Mapping[str, DetectorWitnessBundle],
) -> Iterable[dict[str, Any]]:
    witness_events_by_policy: dict[str, dict[tuple[str, int, int], str]] = {}
    for policy_ref, witness_bundle in witness_bundles.items():
        witness_events_by_policy[policy_ref] = {
            (item.extrema_kind, item.origin_position, item.confirmation_position): item.record_identity
            for item in witness_bundle.swing_event_witnesses
        }
    core_representations_by_policy: dict[str, list[str]] = defaultdict(list)
    for item in bundle.structures:
        policy_ref = DetectorPolicyWitnessSpec.from_policy(item.config.policy).spec_identity
        core_representations_by_policy[policy_ref].append(item.config.representation_id)
    for policy_ref, witness_bundle in sorted(witness_bundles.items()):
        representation_ids = sorted(core_representations_by_policy.get(policy_ref, ()))
        for item in witness_bundle.swing_event_witnesses:
            yield {
                "record_type": "S2_SWING_EVENT_WITNESS_RECORD",
                "record_identity": item.record_identity,
                "consumer_scope": "CMC_STAGE4B1_POLICY_VIEW",
                "representation_ids": representation_ids,
                "dataset_identity": witness_bundle.dataset_identity,
                "policy_witness_ref": item.policy_witness_ref,
                "extrema_kind": item.extrema_kind,
                "origin_position": item.origin_position,
                "origin_key": _jsonable(item.origin_key),
                "confirmation_position": item.confirmation_position,
                "availability_key": _jsonable(item.availability_key),
                "swing_price": _jsonable(item.swing_price),
                "authority_status": item.authority_status,
                "published_record": _jsonable(item.published_record),
                "availability_semantics": "S2_EVENT_VISIBLE_AT_ITS_PUBLISHED_AVAILABILITY_KEY_ONLY",
            }
    for representation_id, witness_bundle in sorted(s5_witness_bundles.items()):
        for item in witness_bundle.swing_event_witnesses:
            yield {
                "record_type": "S2_SWING_EVENT_WITNESS_RECORD",
                "record_identity": item.record_identity,
                "consumer_scope": "S5_REPRESENTATION_PLAN",
                "representation_id": representation_id,
                "dataset_identity": witness_bundle.dataset_identity,
                "policy_witness_ref": item.policy_witness_ref,
                "extrema_kind": item.extrema_kind,
                "origin_position": item.origin_position,
                "origin_key": _jsonable(item.origin_key),
                "confirmation_position": item.confirmation_position,
                "availability_key": _jsonable(item.availability_key),
                "swing_price": _jsonable(item.swing_price),
                "authority_status": item.authority_status,
                "published_record": _jsonable(item.published_record),
                "availability_semantics": "S2_EVENT_VISIBLE_AT_ITS_PUBLISHED_AVAILABILITY_KEY_ONLY",
            }
    for representation in bundle.structures:
        config = representation.config
        spec = DetectorPolicyWitnessSpec.from_policy(config.policy)
        event_refs = witness_events_by_policy.get(spec.spec_identity, {})
        frame = representation.structure.frame
        for side, origin, price, available in _confirmed_swing_events(frame):
            key = bundle.adapter.key_for_position(bundle.market.index, available, InformationPhase.COMPLETED_ROW_AVAILABLE, 0)
            index_value = bundle.market.index[origin]
            yield {
                "record_type": "STAGE4B1_CONFIRMED_SWING_WITNESS_VIEW",
                "view_reference": f"{representation.structure.surface_id}:{side}:{origin}:{available}:{config.identity_sha256}",
                "view_reference_is_producer_record_id": False,
                "representation_id": config.representation_id,
                "representation_kind": "STAGE4B1_POLICY_IDENTIFIED_STRUCTURE",
                "policy_id": config.policy_id,
                "policy_identity_sha256": config.identity_sha256,
                "policy_parameters": config.payload(),
                "s2_policy_witness_ref": spec.spec_identity,
                "s2_swing_event_witness_ref": event_refs.get((side, origin, available)),
                "authority_status": "WITNESS_ONLY_NOT_MUF_AUTHORITATIVE",
                "timeline_id": bundle.timeline.timeline_id,
                "scope_axis": InformationAxis.TIME_INDEXED.value,
                "source_structure_surface_id": representation.structure.surface_id,
                "extrema_kind": side,
                "origin_position": origin,
                "origin_observation_label": _jsonable(index_value),
                "origin_label_semantics": "SOURCE_INDEX_METADATA_ONLY_NOT_INFORMATION_AVAILABILITY",
                "confirmation_position": available,
                "availability_key": _jsonable(key),
                "swing_price": price,
                "availability_semantics": "VISIBLE_AT_CONFIRMATION_KEY_ONLY; NEVER_BACKFILLED_TO_ORIGIN",
                "intrabar_order": "UNPROVEN_FROM_OHLC",
            }
    for representation_id, candidate in sorted(s5_bundles.items()):
        for item in candidate.authoritative_turning_points:
            yield {
                "record_type": "S5_AUTHORITATIVE_TURNING_POINT_RECORD",
                "record_identity": item.turning_point_id,
                "representation_id": representation_id,
                "representation_spec_hash": candidate.representation_spec.representation_spec_hash,
                "family_kind": candidate.representation_spec.family_kind,
                "intrinsic_scale_key": _jsonable(candidate.representation_spec.intrinsic_scale_key),
                "identity_rule_ref": _jsonable(candidate.representation_spec.identity_rule_ref),
                "policy_id": candidate.policy_artifact.policy_id,
                "authority_policy_hash": candidate.policy_artifact.policy_hash,
                "owner_authorization_ref": candidate.policy_artifact.owner_authorization_ref,
                "authorization_reference_state": _AUTH_REF_PRESENT,
                "witness_record_ref": item.witness_record_ref,
                "extrema_kind": item.extrema_kind,
                "origin_position": item.origin_position,
                "origin_key": _jsonable(item.origin_key),
                "confirmation_position": item.confirmation_position,
                "availability_key": _jsonable(item.availability_key),
                "swing_price": _jsonable(item.swing_price),
                "authority_status": "AUTHORITATIVE_UNDER_SUPPLIED_POLICY_ARTIFACT_CONTRACT",
                "intrabar_order": "UNPROVEN_FROM_OHLC",
            }


def _iter_s5_record_payloads(s5_bundles: Mapping[str, CandidateWaveRepresentationBundle]) -> Iterable[dict[str, Any]]:
    for representation_id, candidate in sorted(s5_bundles.items()):
        groups = (
            ("WAVE_IDENTITY", candidate.wave_identity_records),
            ("RUNNING_WAVE_OBSERVATION", candidate.running_wave_observations),
            ("FINALIZED_WAVE_GEOMETRY", candidate.finalized_wave_geometries),
            ("WAVE_STATUS_EVENT", candidate.wave_status_events),
        )
        for record_kind, records in groups:
            for record in records:
                published = getattr(record, "published_record", None)
                yield {
                    "representation_id": representation_id,
                    "family_kind": candidate.representation_spec.family_kind,
                    "record_kind": record_kind,
                    "record_identity": getattr(record, "wave_process_id", None) or getattr(record, "geometry_record_id", None) or getattr(record, "event_id", None) or getattr(record, "observation_id", None),
                    "record_content": None if published is None else _jsonable(published.content),
                    "record_availability_key": None if published is None else _jsonable(published.availability_key),
                    "policy_identity_sha256": candidate.policy_artifact.policy_hash,
                }


def _stage4b1_summary(bundle: CoreBundle) -> list[dict[str, Any]]:
    return [{
        "policy_id": item.config.policy_id,
        "representation_id": item.config.representation_id,
        "policy_identity_sha256": item.config.identity_sha256,
        "structure_surface_id": item.structure.surface_id,
        "liquidity_surface_id": item.liquidity.surface_id,
        "order_block_surface_id": item.order_block.surface_id,
        "dealing_range_surface_id": item.dealing_range.surface_id,
        "confirmed_turning_point_count": len(_confirmed_swing_events(item.structure.frame)),
    } for item in bundle.structures]


def _s5_family_matrix(
    plans: Sequence[S5RepresentationPlan],
    built: Mapping[str, CandidateWaveRepresentationBundle],
    blocked: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for family in sorted(LEGAL_REPRESENTATION_FAMILIES):
        requested = [plan.representation_spec.representation_id for plan in plans if plan.representation_spec.family_kind == family]
        available = [representation_id for representation_id in requested if representation_id in built]
        blocked_rows = [row for row in blocked if row.get("family_kind") == family]
        if available:
            state = "AVAILABLE_CONTRACT_VALID"
        elif blocked_rows:
            state = str(blocked_rows[0].get("status", "BLOCKED_POLICY_CONTRACT"))
        else:
            state = BLOCKED_MISSING_AUTHORIZED_POLICY
        rows.append({
            "family_kind": family,
            "status": state,
            "requested_representation_ids": requested,
            "available_representation_ids": available,
            "blocked_representation_count": len(blocked_rows),
            "authority_boundary": "S5_CONTRACT_OUTPUT_ONLY; NOT_OUTCOME_SUITABILITY",
        })
    return rows


def _base_resource_report(
    *,
    timeline_id: str,
    market_history: pd.DataFrame,
    source_identity: SourceArtifactIdentity,
    declared: Sequence[DeclaredSwingPolicy],
    plans: Sequence[S5RepresentationPlan],
    blocked_policies: Sequence[Mapping[str, Any]],
    blocked_s5: Sequence[Mapping[str, Any]],
    reason: str,
    source_file_sha256: str | None,
) -> dict[str, Any]:
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "run_state": "BLOCKED_RESOURCE_EXHAUSTION",
        "readiness": "INCOMPLETE_NO_PRODUCER_OUTPUTS_EMITTED",
        "source": {
            "source_identity": _jsonable(source_identity),
            "source_file_sha256": source_file_sha256,
            "timeline_id": timeline_id,
            "row_count": len(market_history),
            "source_origin_authenticated": False,
        },
        "policy_candidates": {
            "declared_swing_policy_count": len(declared),
            "s5_representation_plan_count": len(plans),
            "preblocked_swing_candidates": list(_jsonable(blocked_policies)),
            "preblocked_s5_candidates": list(_jsonable(blocked_s5)),
            "candidate_universe_pruned": False,
        },
        "candidate_policy_status": [
            {**_policy_summary(item), "status": "NOT_RUN_RESOURCE_LIMIT"}
            for item in declared
        ],
        "candidate_s5_status": [
            {
                "representation_id": plan.representation_spec.representation_id,
                "family_kind": plan.representation_spec.family_kind,
                "policy_id": plan.policy_artifact.policy_id,
                "status": next((str(row.get("status")) for row in blocked_s5 if row.get("representation_id") == plan.representation_spec.representation_id), "NOT_RUN_RESOURCE_LIMIT"),
            }
            for plan in plans
        ],
        "coverage": {
            "state": "INCOMPLETE_RESOURCE_LIMIT",
            "candidate_universe_complete": False,
            "candidate_universe_pruned": False,
            "detail": reason,
        },
        "suitability": {
            "contract_validity": "NOT_ESTABLISHED_PRODUCER_BUILD_BLOCKED",
            "causal_timing": "NOT_ESTABLISHED_NO_REPLAY",
            "downstream_changes": "NOT_ESTABLISHED_NO_REPLAY",
            "outcome_improvement": "NOT_ESTABLISHED_NO_VALID_OUTCOME_AUTHORITY",
            "overall": SUITABILITY_NOT_ESTABLISHED,
        },
        "limitations": ["Resource ceilings reject or bound work; the runner never drops an eligible policy or producer candidate to fit a budget."],
    }


def _is_resource_exhaustion(exc: CausalMarketContextCoreError) -> bool:
    text = str(exc).lower()
    return any(token in text for token in (
        "exceeds hard resource ceiling",
        "exceeds max_input_bars",
        "exceeds configured limit",
        "exceeds limit",
        "resource ceiling",
        "candidate entity count exceeds",
        "producer event count exceeds",
        "in-memory replay row cap exceeded",
        "explicit representation count exceeds",
    ))


def _merge_swing_policies(
    declared: Sequence[DeclaredSwingPolicy],
    eligible_plans: Sequence[S5RepresentationPlan],
) -> tuple[list[DeclaredSwingPolicy], list[dict[str, Any]]]:
    candidates = list(declared)
    for plan in eligible_plans:
        config = SwingPolicyConfig(plan.policy_artifact.policy_id, plan.confirmation_policy)
        candidates.append(DeclaredSwingPolicy(config, plan.policy_artifact.owner_authorization_ref))
    by_id: dict[str, list[DeclaredSwingPolicy]] = defaultdict(list)
    for item in candidates:
        by_id[item.config.policy_id].append(item)
    merged: list[DeclaredSwingPolicy] = []
    blocked: list[dict[str, Any]] = []
    for policy_id, group in sorted(by_id.items()):
        identities = {item.config.identity_sha256 for item in group}
        if len(identities) > 1:
            blocked.extend({
                "policy_id": item.config.policy_id,
                "representation_id": item.config.representation_id,
                "status": "BLOCKED_POLICY_IDENTITY_CONFLICT",
                "detail": "same policy_id maps to different explicit producer configurations; none selected",
            } for item in group)
            continue
        # The producer identity is exactly the same. Retain all caller references
        # in the report; one physical surface is the public identity, not a prune.
        unique_refs = sorted({item.owner_authorization_ref for item in group})
        chosen = group[0]
        merged.append(DeclaredSwingPolicy(chosen.config, ";".join(unique_refs)))
    representation_ids = [item.config.representation_id for item in merged]
    if len(set(representation_ids)) != len(representation_ids):
        raise CausalMarketContextCoreError("duplicate producer representation identity survived policy preflight")
    return merged, blocked


def _empty_policy_states(
    swing_policies: Sequence[DeclaredSwingPolicy],
    s5_plans: Sequence[S5RepresentationPlan],
    s5_bundles: Mapping[str, CandidateWaveRepresentationBundle],
) -> dict[str, Any]:
    return {
        "stage4b1": [
            {**_policy_summary(item), "status": "AVAILABLE_CONTRACT_VALID"}
            for item in swing_policies
        ],
        "s5_families": _s5_family_matrix(s5_plans, s5_bundles, ()),
    }


def _report_fingerprint(report: Mapping[str, Any]) -> str:
    excluded = {"measurements", "deterministic_fingerprint_sha256", "output_directory", "record_files"}
    payload = {key: value for key, value in report.items() if key not in excluded}
    return _canonical_sha256(payload)


def _prepare_output_root(output_dir: str | Path | None) -> Path | None:
    if output_dir is None:
        return None
    root = Path(output_dir).expanduser().resolve()
    repo = next((parent for parent in Path(__file__).resolve().parents if (parent / ".git").exists()), None)
    if repo is not None and (root == repo or repo in root.parents):
        raise ValueError("offline research output directory must be outside the Git checkout")
    if root.exists() and any(root.iterdir()):
        raise ValueError("offline research output directory must be new or empty")
    root.mkdir(parents=True, exist_ok=True)
    return root


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(_jsonable(payload), ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def _write_jsonl(
    path: Path,
    rows: Iterable[Mapping[str, Any]],
    *,
    progress: _ResearchProgress | None = None,
    progress_label: str = "Output writing",
    expected_total: int | None = None,
) -> int:
    count = 0
    progress_step = max(5_000, ((expected_total or 0) + 9) // 10) if expected_total is not None else 50_000
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(_jsonable(row), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
            count += 1
            if progress is not None and (
                count % progress_step == 0
                or (expected_total is not None and count == expected_total)
            ):
                total = f"/{expected_total}" if expected_total is not None else ""
                progress.emit(f"{progress_label}: written records={count}{total}")
    return count


def _finalize_output(
    run: MovementResearchRun,
    root: Path,
    *,
    progress: _ResearchProgress | None = None,
) -> MovementResearchRun:
    report = dict(run.report)
    if run.replay is None or run.core_bundle is None or report.get("run_state") != "COMPLETED":
        (root / "RUN_INCOMPLETE").write_text("No complete causal market-context replay was produced.\n", encoding="utf-8")
        report["output_directory"] = str(root)
        report["record_files"] = {}
        report["deterministic_fingerprint_sha256"] = _report_fingerprint(report)
        _write_json(root / "movement_representation_report.json", report)
        return MovementResearchRun(report, run.core_bundle, run.replay, run.s5_bundles, run.witness_bundles, run.s5_blocked, run.turning_point_records, run.disagreement_reference_rows, str(root), s5_witness_bundles=run.s5_witness_bundles)

    tp_path = root / "causal_turning_point_records.jsonl"
    tp_rows = run.turning_point_records if run.turning_point_records else _iter_turning_point_records(run.core_bundle, run.s5_bundles, run.witness_bundles, run.s5_witness_bundles)
    tp_total = run.report.get("causal_turning_points", {}).get("record_count")
    tp_count = _write_jsonl(
        tp_path,
        tp_rows,
        progress=progress,
        progress_label="Output writing causal turning-point records",
        expected_total=tp_total if isinstance(tp_total, int) else None,
    )
    s5_path = root / "s5_representation_records.jsonl"
    s5_total = sum(
        len(records)
        for candidate in run.s5_bundles.values()
        for records in (
            candidate.wave_identity_records,
            candidate.running_wave_observations,
            candidate.finalized_wave_geometries,
            candidate.wave_status_events,
        )
    )
    s5_count = _write_jsonl(
        s5_path,
        _iter_s5_record_payloads(run.s5_bundles),
        progress=progress,
        progress_label="Output writing S5 representation records",
        expected_total=s5_total,
    )
    refs_path = root / "disagreement_affected_references.jsonl"
    ref_rows = run.disagreement_reference_rows if run.disagreement_reference_rows else _affected_disagreement_references(run.replay)
    ref_total = len(run.disagreement_reference_rows) if run.disagreement_reference_rows else None
    ref_count = _write_jsonl(
        refs_path,
        ref_rows,
        progress=progress,
        progress_label="Output writing disagreement references",
        expected_total=ref_total,
    )
    report["record_files"] = {
        "causal_turning_point_records": {"path": tp_path.name, "records": tp_count},
        "s5_representation_records": {"path": s5_path.name, "records": s5_count},
        "disagreement_affected_references": {"path": refs_path.name, "records": ref_count},
        "causal_market_context_core_directory": "causal_market_context_core",
    }
    report["output_directory"] = str(root)
    report["deterministic_fingerprint_sha256"] = _report_fingerprint(report)
    _write_json(root / "movement_representation_report.json", report)
    manifest_files = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name in {"movement_research_manifest.json", "RUN_INCOMPLETE"}:
            continue
        manifest_files.append({
            "path": path.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size,
        })
    _write_json(root / "movement_research_manifest.json", {
        "schema_version": "MARKET_MOVEMENT_RESEARCH_OUTPUT_MANIFEST_V1",
        "self_hash_excluded": True,
        "files": manifest_files,
        "hashes_authenticate_output_bytes_not_source_origin_or_owner_authorization": True,
    })
    return MovementResearchRun(report, run.core_bundle, run.replay, run.s5_bundles, run.witness_bundles, run.s5_blocked, run.turning_point_records, run.disagreement_reference_rows, str(root), s5_witness_bundles=run.s5_witness_bundles)


def _run_market_movement_representation_research_impl(
    *,
    market_history: pd.DataFrame,
    source_identity: SourceArtifactIdentity,
    timeline_id: str,
    swing_policies: Sequence[DeclaredSwingPolicy] = (),
    s5_plans: Sequence[S5RepresentationPlan] = (),
    source_file_sha256: str | None = None,
    source_validation: Any = None,
    replay_limits: ReplayLimits = ReplayLimits(),
    output_dir: str | Path | None = None,
    preblocked_policy_candidates: Sequence[Mapping[str, Any]] = (),
    preblocked_s5_candidates: Sequence[Mapping[str, Any]] = (),
    measure_python_allocations: bool = False,
    progress: _ResearchProgress | None = None,
) -> MovementResearchRun:
    """Build and compare available causal representations over one supplied OHLC interval.

    Policy selection and suitability are deliberately absent. Invalid/missing S5
    authorities are reported as blocked; they are never replaced by defaults.
    """
    with _progress_stage(progress, "Runner input and policy declaration validation") as stage_complete:
        if not isinstance(market_history, pd.DataFrame):
            raise TypeError("market_history must be an OHLC pandas DataFrame")
        if not isinstance(source_identity, SourceArtifactIdentity):
            raise TypeError("source_identity must be SourceArtifactIdentity")
        if not isinstance(replay_limits, ReplayLimits):
            raise TypeError("replay_limits must be the existing ReplayLimits contract")
        if not isinstance(measure_python_allocations, bool):
            raise TypeError("measure_python_allocations must be bool")
        if not isinstance(timeline_id, str) or not timeline_id.strip():
            raise ValueError("timeline_id must be a nonempty explicit or content-derived identity")
        declared = tuple(swing_policies)
        plans = tuple(s5_plans)
        if any(not isinstance(item, DeclaredSwingPolicy) for item in declared):
            raise TypeError("swing_policies must contain DeclaredSwingPolicy records")
        if any(not isinstance(item, S5RepresentationPlan) for item in plans):
            raise TypeError("s5_plans must contain S5RepresentationPlan records")
        root = _prepare_output_root(output_dir)
        stage_complete(f"bars={len(market_history)}; declared_swing_policies={len(declared)}; declared_s5_plans={len(plans)}")
    core_output = None if root is None else root / "causal_market_context_core"

    tracing_started_here = measure_python_allocations and not tracemalloc.is_tracing()
    if tracing_started_here:
        tracemalloc.start()
        tracemalloc.reset_peak()
    try:
        source_schema = _CALLER_FRAME_SCHEMA if source_validation is None else SchemaIdentity("PUBLISHED_KLINE_OHLC", KLINES_SCHEMA_CONTRACT)
        adapter = TimeIndexedTimelineAdapter(timeline_id)
        first_key = adapter.key_for_position(market_history.index, 0, InformationPhase.COMPLETED_ROW_AVAILABLE, 0) if isinstance(market_history, pd.DataFrame) and len(market_history) else None
        last_key = adapter.key_for_position(market_history.index, len(market_history) - 1, InformationPhase.COMPLETED_ROW_AVAILABLE, 0) if isinstance(market_history, pd.DataFrame) and len(market_history) else None
        valid_plans: list[S5RepresentationPlan] = []
        blocked_s5: list[dict[str, Any]] = [dict(_jsonable(row)) for row in preblocked_s5_candidates]
        expected_content_hash = _expected_source_content_hash(
            market_history,
            source_file_sha256=source_file_sha256,
            source_validation=source_validation,
        ) if plans else None
        for plan in plans:
            if first_key is None or last_key is None:
                blocked_s5.append({"representation_id": plan.representation_spec.representation_id, "family_kind": plan.representation_spec.family_kind, "status": "BLOCKED_INVALID_OHLC_INTERVAL", "detail": "empty input interval"})
                continue
            status, detail = _s5_plan_precheck(
                plan,
                timeline_id=timeline_id,
                source_schema=source_schema,
                first_key=first_key,
                last_key=last_key,
                expected_content_hash=expected_content_hash,
            )
            if status:
                blocked_s5.append({"representation_id": plan.representation_spec.representation_id, "family_kind": plan.representation_spec.family_kind, "status": status, "detail": detail})
            else:
                valid_plans.append(plan)

        merged_policies, identity_conflicts = _merge_swing_policies(declared, valid_plans)
        blocked_policy_rows = [dict(_jsonable(row)) for row in preblocked_policy_candidates] + identity_conflicts
        if len(merged_policies) > replay_limits.max_structural_representations:
            report = _base_resource_report(
                timeline_id=timeline_id,
                market_history=market_history,
                source_identity=source_identity,
                declared=declared,
                plans=plans,
                blocked_policies=blocked_policy_rows,
                blocked_s5=blocked_s5,
                reason=f"{len(merged_policies)} eligible policy representations exceed the existing Stage4B1/core limit {replay_limits.max_structural_representations}; no policy was selected or pruned",
                source_file_sha256=source_file_sha256,
            )
            return MovementResearchRun(report, None, None, {}, {}, tuple(blocked_s5), (), (), str(root) if root else None)

        try:
            with _progress_stage(
                progress,
                "CMC build (input/source validation, timeline construction, existing producer/surface construction)",
            ) as stage_complete:
                core_bundle = build_causal_market_context_core(
                    market_history=market_history,
                    source_identity=source_identity,
                    timeline_id=timeline_id,
                    source_file_sha256=source_file_sha256,
                    source_validation=source_validation,
                    swing_policies=tuple(item.config for item in merged_policies),
                )
                stage_complete(
                    f"bars={len(core_bundle.market)}; Stage4A_surfaces={len(core_bundle.stage4a)}; "
                    f"Stage4B1_structures={len(core_bundle.structures)}; Stage4B2_FVG_surface=present; "
                    f"Stage4C_HTF_surface=present; CMC API has no internal progress callback"
                )
            with _progress_stage(progress, "Causal market-context replay") as stage_complete:
                replay = replay_causal_market_context(
                    core_bundle,
                    output_dir=core_output,
                    limits=replay_limits,
                )
                replay_summary = replay.summary if isinstance(replay, ReplayMemoryResult) else replay
                stage_complete(
                    f"boundaries={replay_summary.boundary_count}; entities={replay_summary.entity_count}; "
                    f"producer_events={replay_summary.producer_event_count}; relationships={replay_summary.relationship_count}; "
                    f"relationship_coverage={replay_summary.relationship_coverage_state}; replay API has no internal progress callback"
                )
        except CausalMarketContextCoreError as exc:
            if not _is_resource_exhaustion(exc):
                raise
            report = _base_resource_report(
                timeline_id=timeline_id,
                market_history=market_history,
                source_identity=source_identity,
                declared=declared,
                plans=plans,
                blocked_policies=blocked_policy_rows,
                blocked_s5=blocked_s5,
                reason=str(exc),
                source_file_sha256=source_file_sha256,
            )
            report["candidate_policy_status"] = [
                {**_policy_summary(item), "status": "NOT_RUN_RESOURCE_LIMIT"}
                for item in merged_policies
            ]
            report["coverage"]["expected_policy_count"] = len(merged_policies)
            return MovementResearchRun(report, None, None, {}, {}, tuple(blocked_s5), (), (), str(root) if root else None)

        s5_bundles: dict[str, CandidateWaveRepresentationBundle] = {}
        s5_witness_bundles: dict[str, DetectorWitnessBundle] = {}
        s5_blocked = list(blocked_s5)
        for plan in valid_plans:
            representation_id = plan.representation_spec.representation_id
            try:
                with _progress_stage(progress, f"S2 witness extraction for S5 representation {representation_id}") as stage_complete:
                    bars = _bars_for_dataset(
                        core_bundle,
                        plan.dataset_identity.dataset_id,
                        source_schema,
                        progress=progress,
                        progress_label=f"S2 {representation_id}",
                    )
                    witness_bundle = adapt_detector_witness_stream(bars, confirmation_policy=plan.confirmation_policy)
                    # Public S2 binding is checked again at execution time; no synthesized
                    # confirmation is passed through to the S5 promotion API.
                    if witness_bundle.policy_witness_ref != plan.policy_artifact.detector_policy_witness_ref:
                        raise PolicyScopeMismatch("S2 recomputed witness identity differs from PolicyArtifact")
                    stage_complete(
                        f"input_bar_facts={len(bars)}; event_witnesses={len(witness_bundle.swing_event_witnesses)}; "
                        "adaptation is a blocking public call"
                    )
                with _progress_stage(progress, f"S5 construction for {representation_id}") as stage_complete:
                    candidate = construct_candidate_wave_representation(
                        bars,
                        witness_bundle=witness_bundle,
                        representation_spec=plan.representation_spec,
                        policy_artifact=plan.policy_artifact,
                        dataset_identity=plan.dataset_identity,
                        dataset_role=plan.dataset_role,
                    )
                    stage_complete(
                        f"authoritative_turning_points={len(candidate.authoritative_turning_points)}; "
                        f"finalized_geometries={len(candidate.finalized_wave_geometries)}; "
                        "constructor has no internal progress callback"
                    )
                s5_bundles[representation_id] = candidate
                s5_witness_bundles[representation_id] = witness_bundle
            except (SchemaViolation, PolicyScopeMismatch, SelectionBlockedError, ValueError) as exc:
                s5_blocked.append({
                    "representation_id": representation_id,
                    "family_kind": plan.representation_spec.family_kind,
                    "status": "BLOCKED_POLICY_OR_SCOPE_CONTRACT",
                    "detail": str(exc),
                })

        # Build public S2 witness bundles for every actual Stage4B1 policy view.
        witness_bundles: dict[str, DetectorWitnessBundle] = {}
        witness_dataset = "MR-" + _canonical_sha256({"source_identity": _jsonable(source_identity), "timeline_id": timeline_id, "dataset_scope": "CALLER_STABLE_TIMELINE_IDENTITY_NO_FUTURE_CONTENT_HASH_IN_ASOF_WITNESS"})[:32]
        source_schema = _source_schema_for(core_bundle)
        if not merged_policies:
            with _progress_stage(progress, "S2 witness extraction for evidence-only Stage4B1 view") as stage_complete:
                evidence_bars = _bars_for_dataset(
                    core_bundle,
                    witness_dataset,
                    source_schema,
                    progress=progress,
                    progress_label="S2 evidence-only view",
                )
                evidence_bundle = adapt_detector_witness_stream(evidence_bars)
                witness_bundles[str(TypedState.NOT_CONFIGURED)] = evidence_bundle
                stage_complete(
                    f"input_bar_facts={len(evidence_bars)}; event_witnesses={len(evidence_bundle.swing_event_witnesses)}; "
                    "evidence-only; adapter has no internal progress callback"
                )
        else:
            for declaration in merged_policies:
                policy_spec = DetectorPolicyWitnessSpec.from_policy(declaration.config.policy)
                if policy_spec.spec_identity in witness_bundles:
                    continue
                with _progress_stage(progress, f"S2 witness extraction for policy {declaration.config.policy_id}") as stage_complete:
                    bars = _bars_for_dataset(
                        core_bundle,
                        witness_dataset,
                        source_schema,
                        progress=progress,
                        progress_label=f"S2 {declaration.config.policy_id}",
                    )
                    witness_bundles[policy_spec.spec_identity] = adapt_detector_witness_stream(
                        bars,
                        confirmation_policy=declaration.config.policy,
                    )
                    stage_complete(
                        f"input_bar_facts={len(bars)}; "
                        f"event_witnesses={len(witness_bundles[policy_spec.spec_identity].swing_event_witnesses)}; "
                        "adapter has no internal progress callback"
                    )

        s5_turning_point_count = sum(len(candidate.authoritative_turning_points) for candidate in s5_bundles.values())
        stage4b1_turning_point_count = sum(len(_confirmed_swing_events(item.structure.frame)) for item in core_bundle.structures)
        s2_stage4b1_event_count = sum(len(item.swing_event_witnesses) for item in witness_bundles.values())
        s2_s5_event_count = sum(len(item.swing_event_witnesses) for item in s5_witness_bundles.values())
        s2_event_count = s2_stage4b1_event_count + s2_s5_event_count
        turning_count = stage4b1_turning_point_count + s2_event_count + s5_turning_point_count
        disagreement_refs = tuple(_affected_disagreement_references(replay)) if isinstance(replay, ReplayMemoryResult) else ()
        with _progress_stage(progress, "Representation comparison") as stage_complete:
            structural_comparisons = _stage4b1_comparisons(core_bundle, replay, progress=progress)
            wave_comparisons = _s5_comparisons(s5_bundles, progress=progress)
            stage_complete(
                f"Stage4B1_pairs={len(structural_comparisons)}; S5_pairs={len(wave_comparisons)}; "
                "reported counters are completed pairs and actual row-value comparisons"
            )
        summary = replay.summary if isinstance(replay, ReplayMemoryResult) else replay
        domain_coverage = [_jsonable(row) for row in core_bundle.coverage]
        candidate_counts = _domain_counts(summary)
        s1_derivative_count = len(core_bundle.market)
        fvg_count = sum(value for key, value in candidate_counts.items() if key.startswith("FVG:"))
        stage4b2_states = {
            str(item.get("domain")): str(item.get("state"))
            for item in domain_coverage
        }
        all_policy_families = _s5_family_matrix(plans, s5_bundles, s5_blocked)
        s5_view_state = (
            "AVAILABLE_CONTRACT_VALID"
            if s5_bundles
            else str(s5_blocked[0].get("status", BLOCKED_MISSING_AUTHORIZED_POLICY))
            if s5_blocked
            else BLOCKED_MISSING_AUTHORIZED_POLICY
        )
        report: dict[str, Any] = {
            "schema_version": REPORT_SCHEMA_VERSION,
            "run_state": "COMPLETED",
            "readiness": "OFFLINE_RESEARCH_RUN_COMPLETED; EMPIRICAL_SUITABILITY_NOT_ESTABLISHED",
            "source": {
                "source_identity": _jsonable(source_identity),
                "source_validation_state": summary.source_validation_state,
                "source_hash": core_bundle.source_hash,
                "source_file_sha256": source_file_sha256,
                "source_origin_authenticated": False,
                "timeline_id": core_bundle.timeline.timeline_id,
                "timeline_hash": core_bundle.timeline.timeline_hash,
                "bar_count": len(core_bundle.market),
                "interval_first_close_time_utc": _jsonable(core_bundle.market.index[0]),
                "interval_last_close_time_utc": _jsonable(core_bundle.market.index[-1]),
                "bar_timestamp_semantics": "CALLER_INDEXED_OBSERVATION_TIME; SOURCE_CONTRACT_MUST_DEFINE_OPEN/CLOSE_ROLE",
            },
            "policy_candidates": {
                "stage4b1": [{**_policy_summary(item), "status": "AVAILABLE_CONTRACT_VALID"} for item in merged_policies],
                "stage4b1_blocked": blocked_policy_rows,
                "s5_families": all_policy_families,
                "s5_blocked": s5_blocked,
                "s5_representation_specs": [
                    {
                        "representation_id": plan.representation_spec.representation_id,
                        "representation_spec_hash": plan.representation_spec.representation_spec_hash,
                        "family_kind": plan.representation_spec.family_kind,
                        "intrinsic_scale_key": _jsonable(plan.representation_spec.intrinsic_scale_key),
                        "identity_rule_ref": _jsonable(plan.representation_spec.identity_rule_ref),
                        "policy_id": plan.policy_artifact.policy_id,
                        "policy_hash": plan.policy_artifact.policy_hash,
                        "detector_policy_witness_ref": plan.policy_artifact.detector_policy_witness_ref,
                        "scope_timeline_id": plan.policy_artifact.scope_timeline_id,
                        "scope_axis": plan.policy_artifact.scope_axis.value,
                        "effective_from_key": _jsonable(plan.policy_artifact.effective_from_key),
                        "dataset_id": plan.dataset_identity.dataset_id,
                        "dataset_role": plan.dataset_role.role,
                        "owner_authorization_ref": plan.policy_artifact.owner_authorization_ref,
                        "authorization_reference_state": _AUTH_REF_PRESENT,
                    }
                    for plan in plans
                ],
                "owner_authorization_reference_authenticity": "NOT_CRYPTOGRAPHICALLY_VERIFIED_BY_THIS_RUNNER",
            },
            "ambiguity_and_missingness": {
                "intrabar_order": "UNPROVEN_FROM_OHLC",
                "tick_path": "UNAVAILABLE_FROM_OHLC",
                "origin_availability_separation": "ORIGIN_POSITION_IS_METADATA; CONFIRMED_SWING_AVAILABLE_AT_CONFIRMATION_KEY",
                "unconfigured_swing_policy": BLOCKED_MISSING_AUTHORIZED_POLICY if not merged_policies else None,
                "unsupported_actual_flow": "UNAVAILABLE_NOT_SUPPLIED" if core_bundle.executed_source is None else None,
                "domain_states": domain_coverage,
                "source_origin_authentication": "NOT_ESTABLISHED_BY_HASH_OR_SCHEMA_VALIDATION",
            },
            "available_views": {
                "S1_PRICE_PATH": {"state": "AVAILABLE", "accepted_observation_count": s1_derivative_count, "evidence_source": "CAUSAL_MARKET_CONTEXT_CORE_BOUNDARY_RECORDS"},
                "S2_SWING_WITNESS": {"state": "AVAILABLE_POLICY_WITNESS" if merged_policies else "AVAILABLE_EVIDENCE_ONLY_NO_CONFIRMED_SWINGS", "policy_witness_bundle_count": len(witness_bundles), "s5_policy_witness_bundle_count": len(s5_witness_bundles), "stage4b1_event_witness_count": s2_stage4b1_event_count, "s5_event_witness_count": s2_s5_event_count, "turning_point_witness_count": stage4b1_turning_point_count},
                "STAGE4A": {"state": "AVAILABLE", "domains": [str(item.domain) for item in core_bundle.stage4a]},
                "STAGE4B1": {"state": "AVAILABLE" if core_bundle.structures else BLOCKED_MISSING_AUTHORIZED_POLICY, "representation_count": len(core_bundle.structures)},
                "STAGE4B2_FVG": {"state": stage4b2_states.get("STAGE4B2_FVG", "AVAILABLE_SHARED_OHLC_PRODUCER"), "candidate_count": fvg_count, "policy_dependence": "STRUCTURE_INDEPENDENT"},
                "STAGE4B2_LIQUIDITY": {"state": "AVAILABLE" if core_bundle.structures else BLOCKED_MISSING_AUTHORIZED_POLICY, "producer_state": stage4b2_states.get("STAGE4B2_LIQUIDITY", "UNAVAILABLE_NO_EXPLICIT_SWING_POLICY")},
                "STAGE4B2_ORDER_BLOCK": {"state": "AVAILABLE" if core_bundle.structures else BLOCKED_MISSING_AUTHORIZED_POLICY, "producer_state": stage4b2_states.get("STAGE4B2_ORDER_BLOCK", "UNAVAILABLE_NO_EXPLICIT_SWING_POLICY")},
                "STAGE4B2_DEALING_RANGE": {"state": "AVAILABLE" if core_bundle.structures else BLOCKED_MISSING_AUTHORIZED_POLICY, "producer_state": stage4b2_states.get("STAGE4B2_DEALING_RANGE", "UNAVAILABLE_NO_EXPLICIT_SWING_POLICY")},
                "S5_WAVE_REPRESENTATION": {"state": s5_view_state, "representation_count": len(s5_bundles), "authoritative_turning_point_count": s5_turning_point_count},
                "ACTUAL_EXECUTED_FLOW": {"state": "AVAILABLE" if core_bundle.executed_source is not None else "UNAVAILABLE_NOT_SUPPLIED"},
            },
            "coverage": {
                "bar_count": len(core_bundle.market),
                "s1_accepted_observations": s1_derivative_count,
                "s1_running_snapshots": s1_derivative_count,
                "s1_close_displacement_records": max(0, s1_derivative_count - 1),
                "producer_candidate_counts_by_domain_representation": candidate_counts,
                "candidate_universe_complete": bool(summary.candidates_by_domain_representation is not None) and (True if not isinstance(replay, ReplayMemoryResult) else bool(replay.run_provenance.get("candidate_universe_complete", False))),
                "candidate_universe_pruned": False,
                "relationship_search_state": summary.relationship_coverage_state,
                "domain_coverage": domain_coverage,
                "input_candidate_declarations_seen": len(declared) + len(plans) + len(blocked_policy_rows) + len(preblocked_s5_candidates),
                "eligible_swing_policy_count": len(merged_policies),
                "blocked_s5_candidate_count": len(s5_blocked),
                "resource_limits": _jsonable(replay_limits),
            },
            "causal_turning_points": {
                "record_count": turning_count,
                "record_count_scope": "S2_EVENT_WITNESSES_PLUS_STAGE4B1_VIEWS_PLUS_S5_AUTHORITATIVE_UNDER_CONTRACT_RECORDS; DISTINCT_PRODUCER_SCOPES_MAY_REFER_TO_THE_SAME_GEOMETRY",
                "s2_policy_event_witness_count": s2_event_count,
                "s2_stage4b1_policy_event_witness_count": s2_stage4b1_event_count,
                "s2_s5_plan_event_witness_count": s2_s5_event_count,
                "stage4b1_witness_only_count": stage4b1_turning_point_count,
                "s5_authoritative_under_supplied_policy_count": s5_turning_point_count,
                "record_file": "causal_turning_point_records.jsonl" if root is not None else None,
                "availability_contract": "origin_position_is_metadata; turning point is visible only at confirmation/availability key",
                "intrabar_order": "UNPROVEN_FROM_OHLC",
            },
            "disagreements": {
                "geometric": {"stage4b1_policy_pairs": [{"left_representation_id": row["left_representation_id"], "right_representation_id": row["right_representation_id"], **row["geometric_disagreement"]} for row in structural_comparisons], "s5_representation_pairs": [{"left_representation_id": row["left_representation_id"], "right_representation_id": row["right_representation_id"], **row["geometric_disagreement"]} for row in wave_comparisons]},
                "operational_definition": {"stage4b1_policy_pairs": [{"left_representation_id": row["left_representation_id"], "right_representation_id": row["right_representation_id"], **row["operational_definition_disagreement"]} for row in structural_comparisons], "s5_representation_pairs": [{"left_representation_id": row["left_representation_id"], "right_representation_id": row["right_representation_id"], **row["operational_definition_disagreement"]} for row in wave_comparisons]},
                "information_availability": {"stage4b1_policy_pairs": [{"left_representation_id": row["left_representation_id"], "right_representation_id": row["right_representation_id"], **row["information_availability_disagreement"]} for row in structural_comparisons], "s5_representation_pairs": [{"left_representation_id": row["left_representation_id"], "right_representation_id": row["right_representation_id"], **row["information_availability_disagreement"]} for row in wave_comparisons]},
                "task_relevant": {"state": "NOT_ASSESSED_MISSING_TASK_AND_OUTCOME_AUTHORITY", "no_proxy_task_relevance_rule": True},
                "causal_market_context_core_disagreement_record_count": summary.disagreement_count,
                "no_universal_winner_selected": True,
            },
            "affected_downstream_references": {
                "producer_chains": [
                    "CausalAdaptiveSwingDetector -> ConfirmedSwingSequenceEngine -> CausalStructuralBreakEngine -> Stage4B1StructureSurface",
                    "Stage4B1StructureSurface -> Stage4B2LiquiditySurface / Stage4B2OrderBlockSurface / Stage4B2DealingRangeSurface",
                    "Stage4B2FVGSurface -> structure-independent shared FVG candidates and lifecycle",
                ],
                "candidate_counts_by_domain_representation": candidate_counts,
                "core_entities_file": "causal_market_context_core/entities.jsonl" if root is not None else "ReplayMemoryResult.entities",
                "core_producer_events_file": "causal_market_context_core/producer_events.jsonl" if root is not None else "ReplayMemoryResult.events",
                "core_relationships_file": "causal_market_context_core/relationships.jsonl" if root is not None else "ReplayMemoryResult.relationships",
                "disagreement_boundary_reference_file": "disagreement_affected_references.jsonl" if root is not None else None,
                "reference_count_in_memory": len(disagreement_refs),
                "references_are_emitted_producer_record_ids_only": True,
                "fvg_policy_scope": "SHARED_STRUCTURE_INDEPENDENT_NOT_DUPLICATED_PER_SWING_POLICY",
            },
            "suitability": {
                "contract_validity": "PASS_EXISTING_PRODUCER_CONTRACTS_AND_SURFACE_INTEGRITY_VERIFIED",
                "causal_timing": "ASOF_INFORMATION_KEYS_AND_ORIGIN_CONFIRMATION_SEPARATION_ENFORCED; PREFIX_ASOF_INVARIANCE_TESTED_ON_SYNTHETIC_FIXTURES_NOT_VERIFIED_FOR_THIS_OWNER_DATASET",
                "downstream_changes": "OBSERVED_CORE_POLICY_OUTPUT_DIFFERENCES" if summary.disagreement_count else ("NO_STAGE4B1_ROW_DISAGREEMENT_OBSERVED" if structural_comparisons else "NO_COMPETING_REPRESENTATIONS_RUN"),
                "outcome_improvement": "NOT_ESTABLISHED_NO_VALID_TASK_OUTCOME_AUTHORITY_OR_EMPIRICAL_LABELS",
                "overall": SUITABILITY_NOT_ESTABLISHED,
                "selection_authority": None,
                "winner_or_recommendation": None,
                "axes_are_not_collapsed": True,
            },
            "replay": {
                "run_id": summary.run_id,
                "boundary_count": summary.boundary_count,
                "entity_count": summary.entity_count,
                "producer_event_count": summary.producer_event_count,
                "relationship_count": summary.relationship_count,
                "relationship_counts_by_type": _jsonable(summary.relationship_counts_by_type),
                "prefix_chain_sha256": summary.prefix_chain_sha256,
                "evaluation_boundary": _jsonable(replay.evaluation_boundary) if isinstance(replay, ReplayMemoryResult) else "SEE_CAUSAL_MARKET_CONTEXT_CORE_OUTPUT",
                "evaluation_state": "NOT_ESTABLISHED_MISSING_TASK_AUTHORITY",
            },
            "limitations": [
                "Swing-policy authorization references are preserved but not cryptographically authenticated.",
                "Caller-supplied OHLC hashes and schema checks do not authenticate historical source origin.",
                "OHLC does not establish intrabar ordering, tick path, hidden liquidity, intent, fills, PnL, or outcomes.",
                "Stage4B1 swing events are witness-only; authoritative S5 turning points require the supplied S3 PolicyArtifact contract.",
                "S5 identity_rule_ref is retained as a reference and is not interpreted by this runner; S5 families share the existing constructor.",
                "No valid outcome authority or empirical outcome labels are present, so no representation is selected.",
                "Relationship search may be partial under configured query/relationship ceilings even when all candidate rows are preserved.",
            ],
            "output_directory": str(root) if root is not None else None,
        }
        turning_records: tuple[Mapping[str, Any], ...] = ()
        if root is None:
            turning_records = tuple(_iter_turning_point_records(core_bundle, s5_bundles, witness_bundles, s5_witness_bundles))
        report["deterministic_fingerprint_sha256"] = _report_fingerprint(report)
        return MovementResearchRun(
            report,
            core_bundle,
            replay,
            s5_bundles,
            witness_bundles,
            tuple(s5_blocked),
            turning_records,
            disagreement_refs,
            str(root) if root is not None else None,
            s5_witness_bundles=s5_witness_bundles,
        )
    except Exception:
        if root is not None:
            marker = root / "RUN_INCOMPLETE"
            if not marker.exists():
                try:
                    marker.write_text("Run failed before a complete report was finalized.\n", encoding="utf-8")
                except OSError:
                    pass
        raise
    finally:
        if tracing_started_here:
            tracemalloc.stop()


def run_market_movement_representation_research(
    *,
    market_history: pd.DataFrame,
    source_identity: SourceArtifactIdentity,
    timeline_id: str,
    swing_policies: Sequence[DeclaredSwingPolicy] = (),
    s5_plans: Sequence[S5RepresentationPlan] = (),
    source_file_sha256: str | None = None,
    source_validation: Any = None,
    replay_limits: ReplayLimits = ReplayLimits(),
    output_dir: str | Path | None = None,
    preblocked_policy_candidates: Sequence[Mapping[str, Any]] = (),
    preblocked_s5_candidates: Sequence[Mapping[str, Any]] = (),
    measure_python_allocations: bool = False,
    progress: bool = False,
    _progress_reporter: _ResearchProgress | None = None,
    _defer_progress_finish: bool = False,
) -> MovementResearchRun:
    """Measured public entry point; output serialization is outside the run timer.

    ``progress`` is opt-in and writes only to stderr. The private reporter hook
    lets the CLI include CSV loading in the same elapsed-time clock.
    """
    if not isinstance(progress, bool):
        raise TypeError("progress must be bool")
    if not isinstance(_defer_progress_finish, bool):
        raise TypeError("_defer_progress_finish must be bool")
    if _progress_reporter is not None and not progress:
        raise ValueError("_progress_reporter requires progress=True")
    if _defer_progress_finish and _progress_reporter is None:
        raise ValueError("_defer_progress_finish requires an injected CLI progress reporter")
    progress_reporter = _progress_reporter or (_ResearchProgress() if progress else None)
    started = time.perf_counter()
    tracing_was_already_active = tracemalloc.is_tracing()
    tracing_started_here = measure_python_allocations and not tracing_was_already_active
    if tracing_started_here:
        tracemalloc.start()
        tracemalloc.reset_peak()
    try:
        result = _run_market_movement_representation_research_impl(
            market_history=market_history,
            source_identity=source_identity,
            timeline_id=timeline_id,
            swing_policies=swing_policies,
            s5_plans=s5_plans,
            source_file_sha256=source_file_sha256,
            source_validation=source_validation,
            replay_limits=replay_limits,
            output_dir=output_dir,
            preblocked_policy_candidates=preblocked_policy_candidates,
            preblocked_s5_candidates=preblocked_s5_candidates,
            measure_python_allocations=measure_python_allocations,
            progress=progress_reporter,
        )
    except BaseException as exc:
        if progress_reporter is not None:
            status = "interrupted" if isinstance(exc, (KeyboardInterrupt, SystemExit)) else "failed"
            progress_reporter.finish(status, f"error_type={type(exc).__name__}")
        raise
    finally:
        elapsed = time.perf_counter() - started
        if measure_python_allocations and tracemalloc.is_tracing():
            current_bytes, peak_bytes = tracemalloc.get_traced_memory()
        else:
            current_bytes = peak_bytes = None
        if tracing_started_here:
            tracemalloc.stop()
    measurements = {
        "wall_clock_seconds": elapsed,
        "process_peak_rss_bytes": _process_peak_rss_bytes(),
        "process_peak_rss_scope": "PROCESS_HIGH_WATER_MARK_AT_RETURN; NOT_ISOLATED_TO_THIS_RUN",
        "python_tracemalloc_current_bytes_after_core_run": current_bytes,
        "python_tracemalloc_peak_bytes_during_core_run": peak_bytes,
        "python_allocation_tracing_enabled": bool(measure_python_allocations),
        "python_tracemalloc_scope": "THIS_RUN_TRACING_STARTED_BY_RUNNER" if tracing_started_here else ("EXTERNAL_TRACER_INCLUDES_PRIOR_ACTIVITY" if measure_python_allocations and tracing_was_already_active else "DISABLED"),
        "measurement_scope": "RUNTIME_COVERS_BUILDER_AND_REPLAY; RSS_IS_PROCESS_HIGH_WATER_MARK; PYTHON_TRACEMALLOC_IS_OPTIONAL_AND_DOES_NOT_CAPTURE_ALL_NATIVE_ARRAY_MEMORY",
        "runtime_includes": "core_build_and_replay_including_core_stream_output; S5_construction_and_comparison; report_fingerprint",
        "runtime_excludes": "adapter_JSONL_and_report_finalization; output_manifest_hashing; CLI_stdout_JSON_serialization",
    }
    result = _wrap_measurement(result, measurements)
    if result.output_directory is not None:
        try:
            with _progress_stage(progress_reporter, "Output writing and manifest finalization") as stage_complete:
                result = _finalize_output(
                    result,
                    Path(result.output_directory),
                    progress=progress_reporter,
                )
                record_files = result.report.get("record_files", {})
                record_total = sum(
                    int(item.get("records", 0))
                    for item in record_files.values()
                    if isinstance(item, Mapping)
                )
                stage_complete(
                    f"record_files={len(record_files)}; listed_record_rows={record_total}; "
                    f"output_directory={result.output_directory}"
                )
        except BaseException as exc:
            marker = Path(result.output_directory) / "RUN_INCOMPLETE"
            if not marker.exists():
                try:
                    marker.write_text("Run output finalization failed.\n", encoding="utf-8")
                except OSError:
                    pass
            if progress_reporter is not None:
                status = "interrupted" if isinstance(exc, (KeyboardInterrupt, SystemExit)) else "failed"
                progress_reporter.finish(status, f"error_type={type(exc).__name__}")
            raise
    elif progress_reporter is not None:
        progress_reporter.emit("Output writing: skipped (no output_dir configured; records retained in memory)")
    if progress_reporter is not None and not _defer_progress_finish:
        state = str(result.report.get("run_state", "UNKNOWN"))
        status = "completed" if state == "COMPLETED" else "finished"
        progress_reporter.finish(status, f"state={state}; core_wall_clock_seconds={elapsed:.2f}")
    return result


def verify_replay_prefix_invariance(
    *,
    full_bundle: CoreBundle,
    prefix_bundle: CoreBundle,
    replay_limits: ReplayLimits = ReplayLimits(),
) -> bool:
    """Compare public core as-of boundary records for a full run and its exact prefix."""
    if not isinstance(full_bundle, CoreBundle) or not isinstance(prefix_bundle, CoreBundle):
        raise TypeError("full_bundle and prefix_bundle must be CoreBundle instances")
    if full_bundle.timeline.timeline_id != prefix_bundle.timeline.timeline_id:
        raise ValueError("prefix comparison requires the same timeline_id")
    if len(prefix_bundle.market) > len(full_bundle.market):
        raise ValueError("prefix interval is longer than full interval")
    if not full_bundle.market.iloc[: len(prefix_bundle.market)].equals(prefix_bundle.market):
        raise ValueError("prefix market rows differ from the corresponding full-history prefix")
    if tuple(item.config.identity_sha256 for item in full_bundle.structures) != tuple(item.config.identity_sha256 for item in prefix_bundle.structures):
        raise ValueError("prefix comparison requires identical policy identities")
    full = replay_causal_market_context(full_bundle, limits=replay_limits)
    prefix = replay_causal_market_context(prefix_bundle, limits=replay_limits)
    if not isinstance(full, ReplayMemoryResult) or not isinstance(prefix, ReplayMemoryResult):
        raise CausalMarketContextCoreError("prefix invariance verification requires memory replay mode")
    if full.boundaries[: len(prefix.boundaries)] != prefix.boundaries:
        raise CausalMarketContextCoreError("historical boundary records changed after future rows were appended")
    return True


def _wrap_measurement(run: MovementResearchRun, measurements: Mapping[str, Any]) -> MovementResearchRun:
    report = dict(run.report)
    report["measurements"] = dict(measurements)
    report["deterministic_fingerprint_sha256"] = _report_fingerprint(report)
    return MovementResearchRun(report, run.core_bundle, run.replay, run.s5_bundles, run.witness_bundles, run.s5_blocked, run.turning_point_records, run.disagreement_reference_rows, run.output_directory, s5_witness_bundles=run.s5_witness_bundles)


def _read_policy_json(path: str | Path) -> tuple[tuple[DeclaredSwingPolicy, ...], tuple[Mapping[str, Any], ...], str]:
    raw = Path(path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    try:
        doc = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return (), ({"candidate_id": str(path), "status": "BLOCKED_POLICY_FILE_INVALID", "detail": str(exc)},), digest
    if not isinstance(doc, dict) or doc.get("schema_version") != "MOVEMENT_SWING_POLICY_DECLARATIONS_V1" or not isinstance(doc.get("policies"), list):
        return (), ({"candidate_id": str(path), "status": "BLOCKED_POLICY_FILE_SCHEMA_INVALID", "detail": "expected MOVEMENT_SWING_POLICY_DECLARATIONS_V1 with policies array"},), digest
    valid: list[DeclaredSwingPolicy] = []
    blocked: list[Mapping[str, Any]] = []
    allowed = {"policy_id", "quantile", "prior_continuation_reversals", "prior_confirmed_reversals", "owner_authorization_ref"}
    for index, entry in enumerate(doc["policies"]):
        candidate_id = entry.get("policy_id", f"policy-entry-{index}") if isinstance(entry, dict) else f"policy-entry-{index}"
        if isinstance(entry, dict) and ("owner_authorization_ref" not in entry or not isinstance(entry.get("owner_authorization_ref"), str) or not entry.get("owner_authorization_ref", "").strip()):
            blocked.append({"candidate_id": candidate_id, "status": BLOCKED_MISSING_AUTHORIZED_POLICY, "detail": "owner_authorization_ref is absent or empty; candidate not executed"})
            continue
        if not isinstance(entry, dict) or set(entry) != allowed:
            blocked.append({"candidate_id": candidate_id, "status": "BLOCKED_INVALID_POLICY_CONTRACT", "detail": "entry must contain exactly policy_id, quantile, both explicit prior arrays, and owner_authorization_ref"})
            continue
        if not isinstance(entry.get("owner_authorization_ref"), str) or not entry["owner_authorization_ref"].strip():
            blocked.append({"candidate_id": candidate_id, "status": BLOCKED_MISSING_AUTHORIZED_POLICY, "detail": "owner_authorization_ref is absent or empty; candidate not executed"})
            continue
        try:
            if not isinstance(entry["prior_continuation_reversals"], list) or not isinstance(entry["prior_confirmed_reversals"], list):
                raise ValueError("both prior arrays must be explicit JSON arrays; use [] only when that is the declared policy")
            policy = EmpiricalConfirmationPolicy(
                quantile=float(entry["quantile"]),
                prior_continuation_reversals=tuple(entry["prior_continuation_reversals"]),
                prior_confirmed_reversals=tuple(entry["prior_confirmed_reversals"]),
            )
            config = SwingPolicyConfig(str(entry["policy_id"]), policy, digest)
            valid.append(DeclaredSwingPolicy(config, entry["owner_authorization_ref"]))
        except (TypeError, ValueError, CausalMarketContextCoreError) as exc:
            blocked.append({"candidate_id": candidate_id, "status": "BLOCKED_INVALID_POLICY_CONTRACT", "detail": str(exc)})
    return tuple(valid), tuple(blocked), digest


def _create_cli_s5_plans(
    path: str | Path,
    *,
    market_history: pd.DataFrame,
    timeline_id: str,
    source_file_sha256: str,
    policy_declarations: Sequence[DeclaredSwingPolicy],
) -> tuple[tuple[S5RepresentationPlan, ...], tuple[Mapping[str, Any], ...]]:
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return (), ({"candidate_id": str(path), "family_kind": None, "status": "BLOCKED_S5_PLAN_FILE_INVALID", "detail": str(exc)},)
    if not isinstance(doc, dict) or doc.get("schema_version") != "MOVEMENT_S5_AUTHORIZED_PLAN_SET_V1":
        return (), ({"candidate_id": str(path), "family_kind": None, "status": "BLOCKED_S5_PLAN_FILE_SCHEMA_INVALID", "detail": "expected MOVEMENT_S5_AUTHORIZED_PLAN_SET_V1"},)
    dataset_doc = doc.get("dataset")
    plan_docs = doc.get("representations")
    if not isinstance(dataset_doc, dict) or not isinstance(plan_docs, list):
        return (), ({"candidate_id": str(path), "family_kind": None, "status": "BLOCKED_S5_PLAN_FILE_SCHEMA_INVALID", "detail": "dataset object and representations array are required"},)
    blocked: list[Mapping[str, Any]] = []
    valid: list[S5RepresentationPlan] = []
    adapter = TimeIndexedTimelineAdapter(timeline_id)
    if not len(market_history):
        return (), ({"candidate_id": str(path), "family_kind": None, "status": "BLOCKED_INVALID_OHLC_INTERVAL", "detail": "empty OHLC interval"},)
    first_key = adapter.key_for_position(market_history.index, 0, InformationPhase.COMPLETED_ROW_AVAILABLE, 0)
    last_key = adapter.key_for_position(market_history.index, len(market_history) - 1, InformationPhase.COMPLETED_ROW_AVAILABLE, 0)
    source_schema = _CALLER_FRAME_SCHEMA
    required_dataset = {"dataset_id", "role", "role_assignment_position", "permitted_operations", "prohibited_operations", "owner_authorization_ref"}
    if not required_dataset.issubset(dataset_doc):
        for item in plan_docs:
            representation_id = item.get("representation_id", "unknown") if isinstance(item, dict) else "unknown"
            family = item.get("family_kind") if isinstance(item, dict) else None
            blocked.append({"representation_id": representation_id, "family_kind": family, "status": BLOCKED_MISSING_AUTHORIZED_POLICY, "detail": "dataset role and owner authorization metadata are incomplete"})
        return (), tuple(blocked)
    try:
        if not isinstance(dataset_doc.get("owner_authorization_ref"), str) or not dataset_doc["owner_authorization_ref"].strip():
            raise ValueError("dataset owner_authorization_ref must be explicit and nonempty")
        declared_content_hash = dataset_doc.get("content_hash")
        if declared_content_hash is not None and declared_content_hash != source_file_sha256:
            raise ValueError("dataset.content_hash must match the exact local input-file SHA-256")
        dataset_identity = DatasetIdentityArtifact.create(
            dataset_id=str(dataset_doc["dataset_id"]),
            content_hash=source_file_sha256,
            source_identity=source_schema,
            timeline_id=timeline_id,
            start_key=first_key,
            end_key=last_key,
            transformation_spec_hash=_canonical_sha256({"schema": "close_time_utc+OHLC+optional-volume-v1"}),
            parent_dataset_ids=(),
            creation_code_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            semantic_schema_hash=_canonical_sha256({"price_semantics": "PUBLISHED_OHLC_FACT", "columns": ["open", "high", "low", "close"]}),
        )
        role_position = int(dataset_doc["role_assignment_position"])
        if role_position < 0 or role_position >= len(market_history):
            raise ValueError("role_assignment_position is outside supplied interval")
        role_key = adapter.key_for_position(market_history.index, role_position, InformationPhase.COMPLETED_ROW_AVAILABLE, 0)
        role = DatasetRoleArtifact.create(
            dataset_identity=dataset_identity,
            role=str(dataset_doc["role"]),
            role_assignment_key=role_key,
            permitted_operations=tuple(dataset_doc["permitted_operations"]),
            prohibited_operations=tuple(dataset_doc["prohibited_operations"]),
            owner_authorization_ref=str(dataset_doc["owner_authorization_ref"]),
        )
    except (TypeError, ValueError, SchemaViolation, CausalMarketContextCoreError) as exc:
        for item in plan_docs:
            representation_id = item.get("representation_id", "unknown") if isinstance(item, dict) else "unknown"
            family = item.get("family_kind") if isinstance(item, dict) else None
            blocked.append({"representation_id": representation_id, "family_kind": family, "status": "BLOCKED_DATASET_ROLE_OR_IDENTITY", "detail": str(exc)})
        return (), tuple(blocked)

    policy_map = {item.config.policy_id: item.config.policy for item in policy_declarations}
    for index, item in enumerate(plan_docs):
        representation_id = item.get("representation_id", f"s5-plan-{index}") if isinstance(item, dict) else f"s5-plan-{index}"
        family = item.get("family_kind") if isinstance(item, dict) else None
        try:
            if not isinstance(item, dict):
                raise ValueError("representation entry must be an object")
            policy_id = str(item["swing_policy_id"])
            if policy_id not in policy_map:
                raise ValueError("referenced explicit swing_policy_id is not available/authorized")
            if family not in LEGAL_REPRESENTATION_FAMILIES:
                raise ValueError(f"unknown existing S5 family {family!r}")
            scale_raw = item["intrinsic_scale_key"]
            scale = TypedState.NOT_APPLICABLE if scale_raw == "NOT_APPLICABLE" else scale_raw
            rule_raw = item.get("identity_rule_ref", "NOT_CONFIGURED")
            rule = TypedState.NOT_CONFIGURED if rule_raw == "NOT_CONFIGURED" else rule_raw
            spec = CandidateWaveRepresentationSpec.create(
                representation_id=str(representation_id),
                family_kind=str(family),
                scope_timeline_id=timeline_id,
                scope_axis=InformationAxis.TIME_INDEXED,
                intrinsic_scale_key=scale,
                identity_rule_ref=rule,
            )
            policy_doc = item["policy_artifact"]
            if not isinstance(policy_doc, dict):
                raise ValueError("policy_artifact object is required")
            if not isinstance(policy_doc.get("owner_authorization_ref"), str) or not policy_doc["owner_authorization_ref"].strip():
                raise ValueError(BLOCKED_MISSING_AUTHORIZED_POLICY)
            effective_pos = int(policy_doc["effective_from_position"])
            if effective_pos < 0 or effective_pos >= len(market_history):
                raise ValueError("effective_from_position is outside supplied interval")
            effective_key = adapter.key_for_position(market_history.index, effective_pos, InformationPhase.COMPLETED_ROW_AVAILABLE, 0)
            provenance = str(policy_doc["calibration_provenance_kind"])
            fit_fields: dict[str, Any] = {}
            if provenance == PROVENANCE_DEVELOPMENT_FIT:
                for name in ("fit_dataset_id", "objective_artifact_hash", "experiment_id", "fit_dataset_role_hash"):
                    fit_fields[name] = policy_doc[name]
            detector_ref = DetectorPolicyWitnessSpec.from_policy(policy_map[policy_id]).spec_identity
            policy_artifact = PolicyArtifact.create(
                policy_id=str(policy_doc["policy_id"]),
                authority_kind=str(policy_doc.get("authority_kind", POLICY_AUTHORITY_KIND_MUF)),
                detector_policy_witness_ref=detector_ref,
                scope_timeline_id=timeline_id,
                scope_axis=InformationAxis.TIME_INDEXED,
                scope_representation_id=spec.representation_id,
                calibration_provenance_kind=provenance,
                fit_dataset_id=fit_fields.get("fit_dataset_id", TypedState.NOT_APPLICABLE),
                objective_artifact_hash=fit_fields.get("objective_artifact_hash", TypedState.NOT_APPLICABLE),
                experiment_id=fit_fields.get("experiment_id", TypedState.NOT_APPLICABLE),
                fit_dataset_role_hash=fit_fields.get("fit_dataset_role_hash", TypedState.NOT_APPLICABLE),
                reproduction_recipe_hash=str(policy_doc["reproduction_recipe_hash"]),
                effective_from_key=effective_key,
                owner_authorization_ref=str(policy_doc["owner_authorization_ref"]),
            )
            plan = S5RepresentationPlan(
                representation_spec=spec,
                policy_artifact=policy_artifact,
                confirmation_policy=policy_map[policy_id],
                dataset_identity=dataset_identity,
                dataset_role=role,
                recomputed_recipe_hash=str(policy_doc["recomputed_recipe_hash"]),
            )
            valid.append(plan)
        except (KeyError, TypeError, ValueError, SchemaViolation, CausalMarketContextCoreError) as exc:
            blocked.append({"representation_id": representation_id, "family_kind": family, "status": BLOCKED_MISSING_AUTHORIZED_POLICY if str(exc) == BLOCKED_MISSING_AUTHORIZED_POLICY else "BLOCKED_S5_POLICY_OR_SPEC_INPUT", "detail": str(exc)})
    return tuple(valid), tuple(blocked)


def _parse_cli(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", required=True, help="existing local OHLC CSV; no download or conversion")
    parser.add_argument("--timestamp-column", default="close_time_utc", help="timezone-aware bar-observation timestamp; values are not sorted")
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--period-start-utc", required=True)
    parser.add_argument("--period-end-utc", required=True)
    parser.add_argument("--timeline-id", help="optional explicit timeline identity; otherwise derived from local input hash and source scope")
    parser.add_argument("--swing-policy-json", help="optional owner-declared policy file; omission leaves swing-dependent domains blocked")
    parser.add_argument("--s5-plan-json", help="optional explicit S5 policy/representation authorization manifest")
    parser.add_argument("--output-dir", required=True, help="new or empty output directory outside the Git checkout")
    parser.add_argument("--max-registered-entities", type=int, default=100_000)
    parser.add_argument("--max-producer-events", type=int, default=250_000)
    parser.add_argument("--max-interval-nodes", type=int, default=20_000)
    parser.add_argument("--max-spatial-relations-per-boundary", type=int, default=128)
    parser.add_argument("--max-spatial-relations-total", type=int, default=250_000)
    parser.add_argument("--measure-python-allocations", action="store_true", help="opt in to tracemalloc; adds runtime overhead and does not capture all native memory")
    parser.add_argument("--progress", action="store_true", help="opt in to throttled elapsed-time progress on stderr; never changes analytical output")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_cli(argv)
    progress_reporter = _ResearchProgress() if args.progress else None
    try:
        with _progress_stage(progress_reporter, "Input loading, timestamp validation, and policy-manifest parsing") as stage_complete:
            raw_bytes = Path(args.csv).expanduser().read_bytes()
            input_sha = hashlib.sha256(raw_bytes).hexdigest()
            frame = pd.read_csv(args.csv)
            if args.timestamp_column not in frame.columns:
                raise ValueError(f"CSV is missing timestamp column {args.timestamp_column!r}")
            times = pd.to_datetime(frame.pop(args.timestamp_column), utc=True, errors="raise")
            frame.index = pd.DatetimeIndex(times, name=args.timestamp_column)
            identity = SourceArtifactIdentity(args.symbol, "SPOT", "1m", args.period_start_utc, args.period_end_utc)
            timeline_id = args.timeline_id or ("movement-" + _canonical_sha256({"input_sha256": input_sha, "symbol": args.symbol, "period_start_utc": args.period_start_utc, "period_end_utc": args.period_end_utc})[:24])
            policies: tuple[DeclaredSwingPolicy, ...] = ()
            blocked_policies: tuple[Mapping[str, Any], ...] = ()
            if args.swing_policy_json:
                policies, blocked_policies, _ = _read_policy_json(args.swing_policy_json)
            s5_plans: tuple[S5RepresentationPlan, ...] = ()
            blocked_s5: tuple[Mapping[str, Any], ...] = ()
            if args.s5_plan_json:
                s5_plans, blocked_s5 = _create_cli_s5_plans(
                    args.s5_plan_json,
                    market_history=frame,
                    timeline_id=timeline_id,
                    source_file_sha256=input_sha,
                    policy_declarations=policies,
                )
            limits = ReplayLimits(
                max_registered_entities=args.max_registered_entities,
                max_producer_events=args.max_producer_events,
                max_interval_nodes_per_query=args.max_interval_nodes,
                max_spatial_relations_per_boundary=args.max_spatial_relations_per_boundary,
                max_spatial_relations_total=args.max_spatial_relations_total,
            )
            stage_complete(
                f"bars={len(frame)}; owner_csv_sha256={input_sha}; "
                f"swing_policies={len(policies)}; valid_s5_plans={len(s5_plans)}"
            )
        result = run_market_movement_representation_research(
            market_history=frame,
            source_identity=identity,
            timeline_id=timeline_id,
            swing_policies=policies,
            s5_plans=s5_plans,
            source_file_sha256=input_sha,
            replay_limits=limits,
            output_dir=args.output_dir,
            preblocked_policy_candidates=blocked_policies,
            preblocked_s5_candidates=blocked_s5,
            measure_python_allocations=args.measure_python_allocations,
            progress=args.progress,
            _progress_reporter=progress_reporter,
            _defer_progress_finish=progress_reporter is not None,
        )
        print(json.dumps(_jsonable(result.report), ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False))
        if progress_reporter is not None:
            state = str(result.report.get("run_state", "UNKNOWN"))
            status = "completed" if state == "COMPLETED" else "finished"
            measurements = result.report.get("measurements", {})
            core_seconds = measurements.get("wall_clock_seconds") if isinstance(measurements, Mapping) else None
            detail = f"state={state}"
            if isinstance(core_seconds, (int, float)) and not isinstance(core_seconds, bool):
                detail += f"; core_wall_clock_seconds={core_seconds:.2f}"
            progress_reporter.finish(status, detail)
        return 0 if result.report.get("run_state") == "COMPLETED" else 2
    except (OSError, ValueError, TypeError, CausalMarketContextCoreError) as exc:
        if progress_reporter is not None:
            progress_reporter.finish("failed", f"error_type={type(exc).__name__}")
        print(json.dumps({"schema_version": REPORT_SCHEMA_VERSION, "run_state": "FAILED_INPUT_OR_CONTRACT", "error": str(exc)}, ensure_ascii=False, sort_keys=True, indent=2))
        return 2
    except BaseException as exc:
        if progress_reporter is not None:
            state = "interrupted" if isinstance(exc, (KeyboardInterrupt, SystemExit)) else "failed"
            progress_reporter.finish(state, f"error_type={type(exc).__name__}")
        raise


__all__ = [
    "BLOCKED_MISSING_AUTHORIZED_POLICY",
    "DeclaredSwingPolicy",
    "MovementResearchRun",
    "REPORT_SCHEMA_VERSION",
    "S5RepresentationPlan",
    "SUITABILITY_NOT_ESTABLISHED",
    "run_market_movement_representation_research",
    "verify_prefix_replay_invariance",
    "main",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
