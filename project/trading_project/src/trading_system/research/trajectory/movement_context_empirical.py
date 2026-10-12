"""Offline, exploratory FVG movement-context empirical slice (V1).

This module is deliberately an experiment runner, not a trading signal, FVG
quality score, detector, or reusable market-theory layer. It compares two fixed
ordinary-least-squares specifications against the same two *continuous,
observed* one-hour excursion components. The M1 fields are correlated
price-derived measurements and are treated as one joint block.

The runner uses the official Binance Spot kline adapter, the shared sealed
market timeline, Stage4B2 FVG creation entities, Stage4A volatility facts,
Stage4C completed HTF raw OHLC, and MUF S1 causal bar-path descriptors. It
never reads FVG lifecycle rows as creation-time predictors. It writes an
experiment-specific ordered prefix-chain identity; this is intentionally NOT
the same hash schema as any Stage4 ``project_*_prefix`` function.

No owner data are embedded or loaded at import time. A run on one month is a
within-sample temporal diagnostic only: no independent predictive claim,
confidence interval, p-value, IID assertion, trading interpretation, or PnL
claim is produced.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import hashlib
import heapq
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from trading_system.market_understanding.contracts import SchemaIdentity, TypedState
from trading_system.market_understanding.price_path import (
    CausalObservationStream,
    PRICE_PATH_SCHEMA,
    PublishedOhlcBarFact,
    S1_DESCRIPTOR_SPECS,
    safe_ratio,
)
from trading_system.research.hashing import canonical_sha256
from trading_system.research.information_time import (
    INFORMATION_KEY_VERSION,
    InformationKey,
    InformationPhase,
    TimeIndexedTimelineAdapter,
)
from trading_system.research.trajectory.trajectory_contract import (
    MARKET_TIMELINE_SOURCE_VERSION,
    MarketObservationTimeline,
)
from trading_system.research.trajectory import trajectory_stage4a as s4a
from trading_system.research.trajectory import trajectory_stage4b2 as s4b2
from trading_system.research.trajectory import trajectory_stage4c as s4c
from trading_system.sources import SourceArtifactIdentity, sha256_file
from trading_system.sources.binance_spot_kline_ohlc_source import (
    KlineOhlcSource,
    KLINES_SCHEMA_CONTRACT,
    load_binance_spot_klines,
)


EXPERIMENT_ID = "FVG_CAUSAL_MOVEMENT_CONTEXT_EMPIRICAL_SLICE_V1"
HORIZON_POLICY_ID = "EXACT_UTC_ELAPSED_ONE_HOUR_AFTER_FVG_CREATION_V1"
HORIZON = pd.Timedelta(hours=1)
EXPECTED_STEP = pd.Timedelta(minutes=1)
HTF_SCALE_NAME = "H1"
HTF_SCALE_DURATION = pd.Timedelta(hours=1)
HTF_CADENCE_GRID_EPOCH = pd.Timestamp("1970-01-01T00:00:00Z")
PREFIX_CHAIN_VERSION = "EXPERIMENT_ORDERED_ROW_CHAIN_V1"

# Fixed, preregistered model fields. All other produced fields remain in the
# candidate artifact with typed status but are not silently added to the fit.
M0_FEATURES: tuple[str, ...] = (
    "fvg_is_bullish",
    "fvg_creation_close_price",
    "fvg_midpoint_distance_fraction",
    "fvg_gap_width_fraction",
    "fvg_gap_width_percentile",
    "fvg_gap_width_history_count",
    "fvg_middle_body_fraction",
    "fvg_middle_signed_body_fraction",
)
M1_ADDITIONAL_FEATURES: tuple[str, ...] = (
    "s1_close_step_fraction",
    "s1_close_path_step_fraction",
    "s1_observed_close_path_length_fraction",
    "s1_running_high_distance_fraction",
    "s1_running_low_distance_fraction",
    "s1_sum_close_displacement_fraction",
    "s1_bar_count_observed",
    "stage4a_normalized_true_range",
    "stage4a_true_range_percentile",
    "stage4a_normalized_tr_change",
    "stage4a_expansion_percentile",
    "h1_open_relative_to_creation_close",
    "h1_high_relative_to_creation_close",
    "h1_low_relative_to_creation_close",
    "h1_close_relative_to_creation_close",
)
M1_FEATURES: tuple[str, ...] = M0_FEATURES + M1_ADDITIONAL_FEATURES
TARGETS: tuple[str, ...] = (
    "high_excursion_fraction",
    "low_excursion_fraction",
)
_OUTCOME_COLUMNS: tuple[str, ...] = (
    "candidate_id",
    "decision_position",
    "decision_time_utc",
    "requested_horizon_end_utc",
    "requested_end_bar_position",
    "requested_end_key_state",
    "requested_end_key_timeline_id",
    "requested_end_key_event_time_utc",
    "actual_end_position",
    "actual_end_time_utc",
    "path_start_position_exclusive",
    "path_start_position_inclusive",
    "path_end_position_inclusive",
    "path_row_count",
    "path_status",
    "horizon_completion",
    "censoring_state",
    "coverage_assessment",
    "coverage_issues_json",
    "observed_value_state",
    "observed_max_high",
    "observed_min_low",
    "observed_high_delta_from_creation_close",
    "observed_low_delta_from_creation_close",
    "observed_high_excursion_fraction",
    "observed_low_excursion_fraction",
    "model_target_state",
    "high_excursion_fraction",
    "low_excursion_fraction",
    "max_high_position",
    "min_low_position",
    "source_path_slice_sha256",
    "path_id",
    "outcome_id",
    "horizon_policy_sha256",
    "scoreable_under_frozen_protocol",
    "development_cutoff_utc",
    "model_split_state",
)
_VOLATILITY_COLUMNS: tuple[str, ...] = (
    "true_range",
    "normalized_true_range",
    "true_range_percentile",
    "true_range_history_count",
    "normalized_tr_change",
    "expansion_percentile",
    "expansion_history_count",
)
_HTF_METADATA_FIELDS: tuple[str, ...] = (
    "completed_bucket_end_utc",
    "completed_bucket_open",
    "completed_bucket_high",
    "completed_bucket_low",
    "completed_bucket_close",
    "observed_source_bar_count",
    "expected_grid_bar_count",
    "missing_grid_observation_count",
    "off_grid_observation_count",
    "coverage_status",
    "projectable_asof_position",
    "projectable_asof_time_utc",
    "close_batch_order_unknown",
)
_S1_RAW_DESCRIPTOR_FIELDS: tuple[str, ...] = (
    "observed_close_path_length",
    "grid_contiguous_close_path_length",
    "running_high_so_far",
    "running_low_so_far",
    "bar_count_observed",
    "bar_count_grid",
    "sum_close_displacement",
)
_SOURCE_ADAPTER_ID = (
    "trading_system.sources.binance_spot_kline_ohlc_source.load_binance_spot_klines"
)
_KLINE_SCHEMA_DOMAIN, _KLINE_SCHEMA_VERSION = KLINES_SCHEMA_CONTRACT.rsplit("_", 1)
S1_BAR_SOURCE_IDENTITY = SchemaIdentity(
    _KLINE_SCHEMA_DOMAIN,
    _KLINE_SCHEMA_VERSION,
)
_S1_DESCRIPTOR_CONFIGURATION = tuple(
    {
        "name": spec.name,
        "version": spec.version,
        "descriptor_identity": spec.descriptor_identity,
        "stage": spec.stage,
        "required_inputs": list(spec.required_inputs),
        "availability_rule": spec.availability_rule,
        "boundary_contract": spec.boundary_contract,
        "missingness": spec.missingness,
        "denominator_semantics": (
            spec.denominator_semantics.value
            if isinstance(spec.denominator_semantics, TypedState)
            else spec.denominator_semantics
        ),
        "incremental_state": spec.incremental_state,
        "policy_dependencies": list(spec.policy_dependencies),
    }
    for spec in S1_DESCRIPTOR_SPECS
)
_S1_DESCRIPTOR_CONFIGURATION_SHA256 = canonical_sha256(
    domain="FVG_MOVEMENT_CONTEXT_S1_DESCRIPTOR_CONFIGURATION_V1",
    payload={
        "schema_identity": {
            "schema_domain": PRICE_PATH_SCHEMA.schema_domain,
            "schema_version": PRICE_PATH_SCHEMA.schema_version,
        },
        "descriptor_specs": _S1_DESCRIPTOR_CONFIGURATION,
        "declared_grid": None,
    },
)


class MovementContextExperimentError(ValueError):
    """Fail-closed validation error for this experiment slice."""


def _experiment_htf_cadence_contract() -> s4c.CadenceGridContract:
    return s4c.CadenceGridContract(
        grid_epoch_utc=HTF_CADENCE_GRID_EPOCH,
        period=EXPECTED_STEP,
    )


def _experiment_htf_cadence_hash() -> str:
    return canonical_sha256(
        domain="STAGE4C1_CADENCE_GRID_CONTRACT_V1",
        payload=_experiment_htf_cadence_contract().payload(),
    )


@dataclass(frozen=True)
class ExperimentBundle:
    candidate_context: pd.DataFrame
    excursion_outcomes: pd.DataFrame
    comparison: Mapping[str, Any]
    protocol: Mapping[str, Any]
    summary: Mapping[str, Any]
    timeline: MarketObservationTimeline
    adapter: TimeIndexedTimelineAdapter


def _sha256_text(value: object, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise MovementContextExperimentError(f"{field} must be lowercase SHA-256 hex")
    return value


def _utc_timestamp(value: object, field: str) -> pd.Timestamp:
    try:
        timestamp = pd.Timestamp(value)
    except Exception as exc:
        raise MovementContextExperimentError(f"{field} must be a timestamp") from exc
    if pd.isna(timestamp) or timestamp.tz is None:
        raise MovementContextExperimentError(f"{field} must be timezone-aware")
    return timestamp.tz_convert("UTC")


def _iso_utc(value: object) -> str | None:
    if value is None or value is pd.NaT or (isinstance(value, float) and math.isnan(value)):
        return None
    timestamp = pd.Timestamp(value)
    if pd.isna(timestamp):
        return None
    if timestamp.tz is None:
        raise MovementContextExperimentError("naive timestamps are forbidden in experiment output")
    return timestamp.tz_convert("UTC").isoformat().replace("+00:00", "Z")


def _index_values_ns(index: pd.DatetimeIndex) -> np.ndarray:
    """Return exact UTC instants as nanoseconds across pandas datetime resolutions."""
    return np.fromiter(
        (int(pd.Timestamp(value).value) for value in index),
        dtype=np.int64,
        count=len(index),
    )


def _json_safe(value: Any) -> Any:
    if isinstance(value, TypedState):
        return value.value
    if isinstance(value, pd.Timestamp):
        return _iso_utc(value)
    if isinstance(value, pd.Timedelta):
        return int(value.value)
    if isinstance(value, np.generic):
        return _json_safe(value.item())
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_safe(item) for item in value]
    if value is None or value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, float):
        if math.isnan(value):
            return None
        if not math.isfinite(value):
            raise MovementContextExperimentError("non-finite output value")
        return value
    if isinstance(value, (str, int, bool)):
        return value
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def _number_and_state(value: object, *, missing_state: str = "UNAVAILABLE") -> tuple[float | None, str]:
    if isinstance(value, TypedState):
        return None, value.value
    if value is None or value is pd.NA or value is pd.NaT:
        return None, missing_state
    try:
        if bool(pd.isna(value)):
            return None, missing_state
    except (TypeError, ValueError):
        pass
    if isinstance(value, bool):
        return float(value), "AVAILABLE"
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        return None, "NON_NUMERIC"
    if not math.isfinite(number):
        return None, missing_state
    return number, "AVAILABLE"


def _ratio_and_state(numerator: object, denominator: object, *, offset: float = 0.0) -> tuple[float | None, str]:
    num, num_state = _number_and_state(numerator)
    den, den_state = _number_and_state(denominator)
    if num is None:
        return None, num_state
    if den is None:
        return None, den_state
    ratio = safe_ratio(num, den)
    if isinstance(ratio, TypedState):
        return None, ratio.value
    result = float(ratio) + offset
    if not math.isfinite(result):
        return None, "NONFINITE_DERIVED_VALUE"
    return result, "AVAILABLE"


def _state_name(value: object) -> str:
    if isinstance(value, TypedState):
        return value.value
    if value is None or value is pd.NA or value is pd.NaT:
        return "UNAVAILABLE"
    try:
        if bool(pd.isna(value)):
            return "UNAVAILABLE"
    except (TypeError, ValueError):
        pass
    return "AVAILABLE"


def _source_identity_payload(identity: SourceArtifactIdentity) -> dict[str, str]:
    return {
        "symbol": identity.symbol,
        "market_type": identity.market_type,
        "interval": identity.interval,
        "period_start_utc": identity.period_start_utc,
        "period_end_utc": identity.period_end_utc,
        "timestamp_unit": identity.timestamp_unit,
    }


def _check_market_frame(
    market_history: pd.DataFrame,
    *,
    timeline: MarketObservationTimeline,
    adapter: TimeIndexedTimelineAdapter,
    source_file_sha256: str,
) -> pd.DataFrame:
    _sha256_text(source_file_sha256, "source_file_sha256")
    if not isinstance(market_history, pd.DataFrame) or market_history.empty:
        raise MovementContextExperimentError("market_history must be a nonempty DataFrame")
    if not isinstance(adapter, TimeIndexedTimelineAdapter):
        raise MovementContextExperimentError("the experiment requires a time-indexed adapter")
    if not isinstance(market_history.index, pd.DatetimeIndex) or market_history.index.tz is None:
        raise MovementContextExperimentError("canonical market index must be timezone-aware")
    snapshot = market_history.copy(deep=True)
    snapshot.index = snapshot.index.tz_convert("UTC")
    try:
        timeline.verify(adapter=adapter, market_history=snapshot)
    except Exception as exc:
        raise MovementContextExperimentError(f"canonical timeline verification failed: {exc}") from exc
    return snapshot


def _prefix_chain_for_frame(
    frame: pd.DataFrame,
    *,
    component: str,
    contract_version: str,
    configuration_identity: str,
    expected_index: pd.Index,
) -> tuple[str, ...]:
    """Build an experiment-local O(N) prefix chain over verified public rows.

    This is not a Stage4 prefix hash and is never labeled as one. Its seed
    excludes whole-file/surface hashes so an unchanged prefix remains invariant
    when later rows are appended; source and full-surface identities are bound
    separately in each candidate artifact.
    """
    if not frame.index.equals(expected_index):
        raise MovementContextExperimentError(f"{component} row index differs from canonical timeline")
    seed = canonical_sha256(
        domain="FVG_MOVEMENT_CONTEXT_PREFIX_CHAIN_SEED_V1",
        payload={
            "chain_version": PREFIX_CHAIN_VERSION,
            "component": component,
            "contract_version": contract_version,
            "configuration_identity": configuration_identity,
        },
    )
    current = seed
    prefixes: list[str] = []
    for position in range(len(frame)):
        row_digest = canonical_sha256(
            domain="FVG_MOVEMENT_CONTEXT_PREFIX_CHAIN_ROW_V1",
            payload={"position": position, "row": frame.iloc[[position]]},
        )
        current = canonical_sha256(
            domain="FVG_MOVEMENT_CONTEXT_PREFIX_CHAIN_STEP_V1",
            payload={"previous": current, "position": position, "row_digest": row_digest},
        )
        prefixes.append(current)
    return tuple(prefixes)


def _prefix_chain_for_sparse_records(
    records_by_position: Sequence[Sequence[Mapping[str, Any]]],
    *,
    component: str,
    contract_version: str,
    configuration_identity: str,
    index: pd.Index,
) -> tuple[str, ...]:
    if len(records_by_position) != len(index):
        raise MovementContextExperimentError(f"{component} sparse record count differs from timeline")
    seed = canonical_sha256(
        domain="FVG_MOVEMENT_CONTEXT_PREFIX_CHAIN_SEED_V1",
        payload={
            "chain_version": PREFIX_CHAIN_VERSION,
            "component": component,
            "contract_version": contract_version,
            "configuration_identity": configuration_identity,
        },
    )
    current = seed
    prefixes: list[str] = []
    for position, records in enumerate(records_by_position):
        ordered = sorted(
            (_json_safe(record) for record in records),
            key=lambda record: json.dumps(record, sort_keys=True, separators=(",", ":")),
        )
        row_digest = canonical_sha256(
            domain="FVG_MOVEMENT_CONTEXT_PREFIX_CHAIN_ROW_V1",
            payload={
                "position": position,
                "event_time_utc_ns": int(pd.Timestamp(index[position]).value),
                "records": ordered,
            },
        )
        current = canonical_sha256(
            domain="FVG_MOVEMENT_CONTEXT_PREFIX_CHAIN_STEP_V1",
            payload={"previous": current, "position": position, "row_digest": row_digest},
        )
        prefixes.append(current)
    return tuple(prefixes)


def _s1_path_facts(
    market_history: pd.DataFrame,
    *,
    adapter: TimeIndexedTimelineAdapter,
    source_identity: SourceArtifactIdentity,
    source_file_sha256: str,
) -> tuple[tuple[dict[str, Any], ...], str]:
    dataset_identity = canonical_sha256(
        domain="FVG_MOVEMENT_CONTEXT_S1_DATASET_ID_V1",
        payload={
            "source_identity": _source_identity_payload(source_identity),
            "source_schema_identity": S1_BAR_SOURCE_IDENTITY.as_payload(),
            "source_file_sha256": source_file_sha256,
        },
    )
    s1_source_identity = S1_BAR_SOURCE_IDENTITY
    stream = CausalObservationStream(
        source_identity=s1_source_identity,
        dataset_identity=dataset_identity,
        declared_grid=None,
    )
    facts: list[dict[str, Any]] = []
    for position, (timestamp, row) in enumerate(market_history.iterrows()):
        key = adapter.key_for_position(
            market_history.index,
            position,
            InformationPhase.COMPLETED_ROW_AVAILABLE,
            deterministic_sequence=0,
        )
        fact = PublishedOhlcBarFact(
            open_price=float(row["open"]),
            high_price=float(row["high"]),
            low_price=float(row["low"]),
            close_price=float(row["close"]),
            availability_key=key,
            source_identity=s1_source_identity,
            dataset_identity=dataset_identity,
            published_bar_record_ref=(
                f"SOURCE_ARTIFACT_SHA256:{source_file_sha256}:"
                f"CLOSE_TIME_NS:{int(pd.Timestamp(timestamp).value)}"
            ),
        )
        accepted = stream.accept(fact)
        descriptor_values = {
            str(record.content["descriptor_name"]): record.content["value"]
            for record in accepted.descriptor_records
        }
        displacement = None
        close_path_step = None
        if accepted.displacement_record is not None:
            displacement_payload = accepted.displacement_record.content["close_displacement"]
            step_payload = accepted.displacement_record.content["close_path_step"]
            displacement = displacement_payload["value"]
            close_path_step = step_payload["value"]
        facts.append(
            {
                "key": key,
                "descriptor_values": descriptor_values,
                "close_displacement": displacement,
                "close_path_step": close_path_step,
                "adjacency_kind": (
                    None
                    if accepted.displacement_record is None
                    else accepted.displacement_record.content["adjacency_kind"]
                ),
            }
        )
    return tuple(facts), dataset_identity


def _feature_value(record: dict[str, Any], name: str, value: object) -> None:
    number, state = _number_and_state(value)
    record[name] = number
    record[f"{name}__state"] = state


def _empty_candidate_columns() -> list[str]:
    """Return the same stable candidate schema when Stage4B2 creates no entities."""
    columns = [
        "candidate_id",
        "fvg_id",
        "event_type",
        "direction",
        "origin_position",
        "middle_position",
        "creation_position",
        "creation_time_utc",
        "creation_key_timeline_id",
        "creation_key_bar_position",
        "creation_key_information_phase",
        "creation_key_deterministic_sequence",
        "same_information_batch_order_unknown",
        "fvg_zone_low",
        "fvg_zone_high",
        "fvg_midpoint",
        "fvg_gap_width",
        "fvg_creation_close_price",
        "source_file_sha256",
        "source_adapter",
        "source_schema_contract",
        "source_validation_state",
        "source_origin_authenticated",
        "source_timestamp_unit",
        "source_symbol",
        "source_market_type",
        "source_interval",
        "source_period_start_utc",
        "source_period_end_utc",
        "timeline_id",
        "timeline_hash",
        "timeline_source_version",
        "s1_dataset_identity",
        "s1_source_schema_domain",
        "s1_source_schema_version",
        "s1_schema_domain",
        "s1_schema_version",
        "s1_descriptor_configuration_sha256",
        "s1_declared_grid_state",
        "fvg_full_surface_id",
        "fvg_contract_version",
        "fvg_reconstruction_input_hash",
        "fvg_complete_result_hash",
        "fvg_normalized_entity_hash",
        "fvg_normalized_event_hash",
        "fvg_structure_surface_id",
        "stage4a_surface_id",
        "stage4a_contract_version",
        "stage4a_configuration_binding_hash",
        "stage4a_reconstruction_input_hash",
        "stage4c_surface_id",
        "stage4c_contract_version",
        "stage4c_scale_name",
        "stage4c_scale_duration_ns",
        "stage4c_cadence_contract_hash",
        "stage4c_reconstruction_input_hash",
        "market_prefix_chain_sha256",
        "fvg_creation_prefix_chain_sha256",
        "s1_prefix_chain_sha256",
        "stage4a_prefix_chain_sha256",
        "stage4c_prefix_chain_sha256",
        "s1_observation_adjacency_kind",
        "s1_grid_contiguity_state",
        "s1_bar_count_grid_state",
        "stage4c_h1_context_state",
    ]
    columns.extend(f"s1_{name}" for name in _S1_RAW_DESCRIPTOR_FIELDS)
    for name in _S1_RAW_DESCRIPTOR_FIELDS:
        columns.append(f"s1_{name}__state")
    for name in _VOLATILITY_COLUMNS:
        columns.extend((f"stage4a_{name}", f"stage4a_{name}__state"))
    for name in _HTF_METADATA_FIELDS:
        columns.extend((f"stage4c_h1_{name}", f"stage4c_h1_{name}__state"))
    for feature in M1_FEATURES:
        columns.extend((feature, f"{feature}__state"))
    columns.append("candidate_context_sha256")
    return list(dict.fromkeys(columns))


def _source_metadata(
    *,
    source_identity: SourceArtifactIdentity,
    source_file_sha256: str,
    timeline: MarketObservationTimeline,
    fvg_surface: s4b2.Stage4B2FVGSurface,
    volatility_surface: s4a.Stage4ADomainSurface,
    htf_surface: s4c.Stage4CHtfScaleSurface,
    source_validation: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "source_identity": _source_identity_payload(source_identity),
        "source_file_sha256": source_file_sha256,
        "source_contract": {
            "adapter": _SOURCE_ADAPTER_ID,
            "schema_contract": KLINES_SCHEMA_CONTRACT,
            "canonical_index_semantics": "CLOSE_TIME_UTC_OPEN_TIME_PLUS_ONE_MINUTE",
            "timestamp_unit_in_source_file": source_identity.timestamp_unit,
            "tie_order_contract": "NOT_PROVEN",
            "source_origin_authenticated": False,
        },
        "source_validation": dict(source_validation),
        "timeline_id": timeline.timeline_id,
        "timeline_hash": timeline.timeline_hash,
        "timeline_row_count": timeline.bar_count,
        "timeline_source_version": MARKET_TIMELINE_SOURCE_VERSION,
        "source_semantics": (
            "CALLER_DECLARED_PUBLISHED_BINANCE_SPOT_KLINE_OHLC; source origin is not authenticated"
        ),
        "fvg_surface": {
            "surface_id": fvg_surface.surface_id,
            "contract_version": s4b2.TRAJECTORY_STAGE4B2_CONTRACT_VERSION,
            "reconstruction_input_hash": fvg_surface.reconstruction_input_hash,
            "complete_result_hash": fvg_surface.complete_result_hash,
            "normalized_entity_hash": fvg_surface.normalized_entity_hash,
            "normalized_event_hash": fvg_surface.normalized_event_hash,
            "structure_surface_id": fvg_surface.structure_surface_id,
            "scope": "FULL_INPUT_SURFACE_ID; NOT_AN_ASOF_PREFIX_HASH",
        },
        "stage4a_volatility_surface": {
            "surface_id": volatility_surface.surface_id,
            "domain": volatility_surface.domain,
            "contract_version": volatility_surface.contract_version,
            "configuration_binding_hash": volatility_surface.configuration_binding_hash,
            "reconstruction_input_hash": volatility_surface.reconstruction_input_hash,
            "scope": "FULL_INPUT_SURFACE_ID; NOT_AN_ASOF_PREFIX_HASH",
        },
        "stage4c_h1_surface": {
            "surface_id": htf_surface.surface_id,
            "domain": htf_surface.domain,
            "contract_version": htf_surface.contract_version,
            "scale_name": htf_surface.scale_name,
            "scale_duration_ns": htf_surface.scale_duration_ns,
            "cadence_contract_hash": htf_surface.cadence_contract_hash,
            "cadence_contract_payload": _experiment_htf_cadence_contract().payload(),
            "reconstruction_input_hash": htf_surface.reconstruction_input_hash,
            "scope": "FULL_INPUT_SURFACE_ID; NOT_AN_ASOF_PREFIX_HASH",
        },
        "muf_s1_contract": {
            "schema_identity": {
                "schema_domain": PRICE_PATH_SCHEMA.schema_domain,
                "schema_version": PRICE_PATH_SCHEMA.schema_version,
            },
            "descriptor_configuration_sha256": _S1_DESCRIPTOR_CONFIGURATION_SHA256,
            "descriptor_specs": _S1_DESCRIPTOR_CONFIGURATION,
            "declared_grid": "NONE; GRID-DEPENDENT-DESCRIPTORS-REMAIN-NOT_CONFIGURED",
            "semantic_scope": "CAUSAL_FACTUAL_SCHEMA_FOUNDATIONS_ONLY; NO_EPISODES_OR_NARRATIVES",
        },
        "prefix_chain_version": PREFIX_CHAIN_VERSION,
        "prefix_chain_note": (
            "Experiment-specific ordered row-chain digest; not equal to or represented as a native Stage4 prefix hash."
        ),
    }


def _path_event_records(
    normalized_event_frame: pd.DataFrame,
    *,
    row_count: int,
) -> tuple[tuple[Mapping[str, Any], ...], ...]:
    groups: list[list[Mapping[str, Any]]] = [[] for _ in range(row_count)]
    for _, event in normalized_event_frame.iterrows():
        if str(event["event_type"]) != "FVG_CREATED":
            continue
        position = int(event["event_position"])
        if position < 0 or position >= row_count:
            raise MovementContextExperimentError("FVG creation event position is outside the timeline")
        groups[position].append({str(column): event[column] for column in normalized_event_frame.columns})
    return tuple(tuple(group) for group in groups)


def _coverage_for_slice(index_ns: np.ndarray, decision_position: int, actual_end_position: int | None) -> tuple[str, list[dict[str, int]]]:
    if actual_end_position is None or actual_end_position <= decision_position:
        return "UNASSESSED", []
    issues: list[dict[str, int]] = []
    expected_ns = int(EXPECTED_STEP.value)
    for left in range(decision_position, actual_end_position):
        right = left + 1
        observed_ns = int(index_ns[right] - index_ns[left])
        if observed_ns != expected_ns:
            issues.append(
                {
                    "left_position": left,
                    "right_position": right,
                    "observed_delta_ns": observed_ns,
                    "expected_delta_ns": expected_ns,
                }
            )
    return ("GAPS_OR_CADENCE_DEVIATION" if issues else "CONTIGUOUS_UNDER_DECLARED_STEP", issues)


def _outcome_rows(
    candidate_context: pd.DataFrame,
    market_history: pd.DataFrame,
    *,
    adapter: TimeIndexedTimelineAdapter,
    horizon_policy_hash: str,
) -> pd.DataFrame:
    index_ns = _index_values_ns(market_history.index)
    position_by_time = {int(value): position for position, value in enumerate(index_ns)}
    last_ns = int(index_ns[-1])
    rows: list[dict[str, Any]] = []
    if candidate_context.empty:
        return pd.DataFrame(columns=_OUTCOME_COLUMNS)
    for candidate in candidate_context.to_dict(orient="records"):
        decision_position = int(candidate["creation_position"])
        decision_time = pd.Timestamp(market_history.index[decision_position]).tz_convert("UTC")
        requested_ns = int(decision_time.value + HORIZON.value)
        requested_time = pd.Timestamp(requested_ns, tz="UTC")
        exact_position = position_by_time.get(requested_ns)
        actual_end_position: int | None
        if exact_position is not None:
            actual_end_position = exact_position
            path_status = "HORIZON_BOUNDARY_OBSERVED"
            horizon_completion = "COMPLETE"
            censoring_state = (
                "RIGHT_CENSORED"
                if exact_position == len(market_history) - 1
                else "OBSERVED_TO_REQUESTED_END"
            )
        elif requested_ns > last_ns:
            actual_end_position = len(market_history) - 1 if decision_position < len(market_history) - 1 else None
            path_status = "RIGHT_CENSORED_AT_DATASET_END"
            horizon_completion = "INCOMPLETE"
            censoring_state = "RIGHT_CENSORED"
        else:
            insertion = int(np.searchsorted(index_ns, requested_ns, side="left"))
            actual_end_position = insertion - 1
            if actual_end_position <= decision_position:
                actual_end_position = None
            path_status = "IN_RANGE_BOUNDARY_UNOBSERVED"
            horizon_completion = "NOT_QUERYABLE_WITH_EXACT_TIME_INDEX_KEY"
            censoring_state = "NOT_CLASSIFIED_NO_VALID_HORIZON_REQUEST"

        coverage, coverage_issues = _coverage_for_slice(index_ns, decision_position, actual_end_position)
        first_path_position = decision_position + 1
        if actual_end_position is None or actual_end_position < first_path_position:
            path_positions: tuple[int, ...] = ()
        else:
            path_positions = tuple(range(first_path_position, actual_end_position + 1))
        observed_rows = len(path_positions)
        decision_close = float(market_history["close"].iloc[decision_position])
        path_slice = market_history.iloc[list(path_positions)].loc[:, ["open", "high", "low", "close"]]
        path_slice_hash = canonical_sha256(
            domain="FVG_MOVEMENT_CONTEXT_OBSERVED_PATH_SLICE_V1",
            payload=path_slice,
        )
        requested_key: InformationKey | None = None
        if exact_position is not None:
            requested_key = adapter.key_for_position(
                market_history.index,
                exact_position,
                InformationPhase.COMPLETED_ROW_AVAILABLE,
                deterministic_sequence=0,
            )
        elif requested_ns > last_ns:
            requested_key = InformationKey(
                information_key_version=INFORMATION_KEY_VERSION,
                timeline_id=adapter.timeline_id,
                bar_position=len(market_history),
                event_time_utc=requested_time,
                information_phase=InformationPhase.COMPLETED_ROW_AVAILABLE,
                deterministic_sequence=0,
            )

        max_high = min_low = high_delta = low_delta = None
        max_high_position = min_low_position = None
        observed_high_fraction = observed_low_fraction = None
        observed_value_state = "NO_POST_DECISION_ROWS"
        if observed_rows:
            highs = market_history["high"].to_numpy(dtype="float64")[list(path_positions)]
            lows = market_history["low"].to_numpy(dtype="float64")[list(path_positions)]
            max_offset = int(np.argmax(highs))
            min_offset = int(np.argmin(lows))
            max_high = float(highs[max_offset])
            min_low = float(lows[min_offset])
            max_high_position = path_positions[max_offset]
            min_low_position = path_positions[min_offset]
            high_delta = max_high - decision_close
            low_delta = min_low - decision_close
            observed_high_fraction = high_delta / decision_close
            observed_low_fraction = low_delta / decision_close
            observed_value_state = "AVAILABLE_ON_OBSERVED_PATH_ONLY"

        scoreable = (
            exact_position is not None
            and horizon_completion == "COMPLETE"
            and censoring_state == "OBSERVED_TO_REQUESTED_END"
            and coverage == "CONTIGUOUS_UNDER_DECLARED_STEP"
        )
        if scoreable:
            target_state = "AVAILABLE"
        elif exact_position is not None and coverage != "CONTIGUOUS_UNDER_DECLARED_STEP":
            target_state = "NOT_SCOREABLE_COVERAGE_GAPS_OR_CADENCE_DEVIATION"
        elif exact_position is not None and censoring_state == "RIGHT_CENSORED":
            target_state = "NOT_SCOREABLE_RIGHT_CENSORED_AT_SOURCE_END"
        elif observed_rows == 0:
            target_state = "NO_POST_DECISION_ROWS"
        else:
            target_state = path_status
        high_target = observed_high_fraction if scoreable else None
        low_target = observed_low_fraction if scoreable else None
        actual_end_time = (
            None
            if actual_end_position is None
            else pd.Timestamp(market_history.index[actual_end_position]).tz_convert("UTC")
        )
        path_id = canonical_sha256(
            domain="FVG_MOVEMENT_CONTEXT_PATH_ID_V1",
            payload={
                "candidate_id": candidate["candidate_id"],
                "decision_position": decision_position,
                "decision_time_utc_ns": int(decision_time.value),
                "requested_end_time_utc_ns": requested_ns,
                "actual_end_position": actual_end_position,
                "path_slice_hash": path_slice_hash,
                "horizon_policy_hash": horizon_policy_hash,
            },
        )
        outcome_id = canonical_sha256(
            domain="FVG_MOVEMENT_CONTEXT_OUTCOME_ID_V1",
            payload={
                "path_id": path_id,
                "path_status": path_status,
                "horizon_completion": horizon_completion,
                "censoring_state": censoring_state,
                "coverage_assessment": coverage,
                "observed_high_fraction": observed_high_fraction,
                "observed_low_fraction": observed_low_fraction,
                "target_state": target_state,
            },
        )
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "decision_position": decision_position,
                "decision_time_utc": _iso_utc(decision_time),
                "requested_horizon_end_utc": _iso_utc(requested_time),
                "requested_end_bar_position": (
                    None
                    if requested_key is None
                    else requested_key.bar_position
                ),
                "requested_end_key_state": (
                    "EXACT_OBSERVED_KEY"
                    if exact_position is not None
                    else "EXPLICIT_OUT_OF_RANGE_FUTURE_BOUNDARY"
                    if requested_key is not None
                    else "IN_RANGE_TIMESTAMP_ABSENT_NO_KEY"
                ),
                "requested_end_key_timeline_id": None if requested_key is None else requested_key.timeline_id,
                "requested_end_key_event_time_utc": None if requested_key is None else _iso_utc(requested_key.event_time_utc),
                "actual_end_position": actual_end_position,
                "actual_end_time_utc": _iso_utc(actual_end_time),
                "path_start_position_exclusive": decision_position,
                "path_start_position_inclusive": first_path_position if observed_rows else None,
                "path_end_position_inclusive": actual_end_position,
                "path_row_count": observed_rows,
                "path_status": path_status,
                "horizon_completion": horizon_completion,
                "censoring_state": censoring_state,
                "coverage_assessment": coverage,
                "coverage_issues_json": json.dumps(coverage_issues, sort_keys=True, separators=(",", ":")),
                "observed_value_state": observed_value_state,
                "observed_max_high": max_high,
                "observed_min_low": min_low,
                "observed_high_delta_from_creation_close": high_delta,
                "observed_low_delta_from_creation_close": low_delta,
                "observed_high_excursion_fraction": observed_high_fraction,
                "observed_low_excursion_fraction": observed_low_fraction,
                "model_target_state": target_state,
                "high_excursion_fraction": high_target,
                "low_excursion_fraction": low_target,
                "max_high_position": max_high_position,
                "min_low_position": min_low_position,
                "source_path_slice_sha256": path_slice_hash,
                "path_id": path_id,
                "outcome_id": outcome_id,
                "horizon_policy_sha256": horizon_policy_hash,
                "scoreable_under_frozen_protocol": bool(scoreable),
            }
        )
    return pd.DataFrame(rows)


def _ols_predict(
    train_x: np.ndarray,
    train_y: np.ndarray,
    eval_x: np.ndarray,
) -> tuple[np.ndarray | None, dict[str, Any]]:
    if train_x.ndim != 2 or eval_x.ndim != 2 or train_x.shape[1] != eval_x.shape[1]:
        return None, {"status": "INVALID_DESIGN_MATRIX"}
    if train_x.shape[0] == 0 or eval_x.shape[0] == 0:
        return None, {"status": "NO_TRAIN_OR_EVALUATION_CASES"}
    means = np.mean(train_x, axis=0)
    scales = np.std(train_x, axis=0, ddof=0)
    scales = np.where(scales > 0.0, scales, 1.0)
    train_z = (train_x - means) / scales
    eval_z = (eval_x - means) / scales
    train_design = np.column_stack((np.ones(train_z.shape[0]), train_z))
    eval_design = np.column_stack((np.ones(eval_z.shape[0]), eval_z))
    coefficients, _, rank, singular_values = np.linalg.lstsq(train_design, train_y, rcond=None)
    diagnostics = {
        "status": "FITTED" if rank == train_design.shape[1] and train_design.shape[0] > train_design.shape[1] else "INCONCLUSIVE_RANK_OR_SAMPLE_DEFICIENT",
        "training_rows": int(train_design.shape[0]),
        "evaluation_rows": int(eval_design.shape[0]),
        "feature_count_excluding_intercept": int(train_x.shape[1]),
        "design_rank_including_intercept": int(rank),
        "design_columns_including_intercept": int(train_design.shape[1]),
        "singular_value_condition_ratio": (
            None
            if len(singular_values) == 0 or float(np.min(singular_values)) == 0.0
            else float(np.max(singular_values) / np.min(singular_values))
        ),
        "feature_standardization": "TRAINING_MEAN_AND_POPULATION_STD; ZERO_STD_SCALE_SET_TO_ONE",
        "feature_selection": "NONE",
        "regularization": "NONE",
    }
    if diagnostics["status"] != "FITTED":
        return None, diagnostics
    return eval_design @ coefficients, diagnostics


def _overlap_summary(outcomes: pd.DataFrame, candidate_ids: set[str]) -> dict[str, Any]:
    intervals = []
    for row in outcomes.to_dict(orient="records"):
        candidate_id = str(row["candidate_id"])
        if candidate_id not in candidate_ids:
            continue
        start = int(row["decision_position"])
        end = row["actual_end_position"]
        if end is None or pd.isna(end) or int(end) <= start:
            continue
        intervals.append((start, int(end), candidate_id))
    intervals.sort(key=lambda item: (item[0], item[1], item[2]))
    active_ends: list[int] = []
    pair_count = 0
    max_concurrent = 0
    for start, end, _ in intervals:
        # Path intervals are (decision, actual_end]; if a prior path ends at
        # this candidate's decision row, their observed post-decision rows do
        # not overlap.
        while active_ends and active_ends[0] <= start:
            heapq.heappop(active_ends)
        pair_count += len(active_ends)
        heapq.heappush(active_ends, end)
        max_concurrent = max(max_concurrent, len(active_ends))
    prefix_max_end: list[int] = []
    running = -1
    for _, end, _ in intervals:
        running = max(running, end)
        prefix_max_end.append(running)
    suffix_min_start = [0] * len(intervals)
    running_start = math.inf
    for i in range(len(intervals) - 1, -1, -1):
        running_start = min(running_start, intervals[i][0])
        suffix_min_start[i] = int(running_start)
    candidates_with_overlap: set[str] = set()
    for i, (start, end, candidate_id) in enumerate(intervals):
        overlaps_left = i > 0 and prefix_max_end[i - 1] > start
        overlaps_right = i + 1 < len(intervals) and suffix_min_start[i + 1] < end
        if overlaps_left or overlaps_right:
            candidates_with_overlap.add(candidate_id)
    return {
        "observed_path_interval_count": len(intervals),
        "overlapping_interval_pair_count": int(pair_count),
        "candidate_count_with_any_observed_path_overlap": len(candidates_with_overlap),
        "max_concurrent_observed_path_intervals": int(max_concurrent),
        "independence_claim": "NONE; OVERLAP IS DESCRIPTIVE DEPENDENCE ACCOUNTING ONLY",
        "uncertainty_estimation": "NOT_PRODUCED; RESEARCH-DEBT-024 REMAINS OPEN",
    }


def _fit_comparison(
    candidate_context: pd.DataFrame,
    outcomes: pd.DataFrame,
    *,
    cutoff: pd.Timestamp,
) -> dict[str, Any]:
    joined = candidate_context.merge(outcomes, on="candidate_id", how="left", validate="one_to_one")
    feature_complete = np.ones(len(joined), dtype=bool)
    for feature in M1_FEATURES:
        state_col = f"{feature}__state"
        feature_complete &= joined[state_col].to_numpy(dtype=object) == "AVAILABLE"
    scoreable = joined["scoreable_under_frozen_protocol"].fillna(False).to_numpy(dtype=bool)
    times = pd.to_datetime(joined["creation_time_utc"], utc=True)
    horizon_ends = pd.to_datetime(joined["requested_horizon_end_utc"], utc=True)
    before = (times < cutoff).to_numpy(dtype=bool)
    after_or_at = (times >= cutoff).to_numpy(dtype=bool)
    outcome_before_cutoff = (horizon_ends < cutoff).fillna(False).to_numpy(dtype=bool)
    training_mask = before & outcome_before_cutoff & scoreable & feature_complete
    evaluation_mask = after_or_at & scoreable & feature_complete
    training_indices = np.flatnonzero(training_mask)
    evaluation_indices = np.flatnonzero(evaluation_mask)
    train_ids = sorted(joined.iloc[training_indices]["candidate_id"].astype(str).tolist())
    evaluation_ids = sorted(joined.iloc[evaluation_indices]["candidate_id"].astype(str).tolist())
    same_case_hash = canonical_sha256(
        domain="FVG_MOVEMENT_CONTEXT_COMPARISON_CASE_SET_V1",
        payload={"training_candidate_ids": train_ids, "evaluation_candidate_ids": evaluation_ids},
    )
    overlap = {
        "training": _overlap_summary(outcomes, set(train_ids)),
        "evaluation": _overlap_summary(outcomes, set(evaluation_ids)),
        "all_model_cases": _overlap_summary(outcomes, set(train_ids + evaluation_ids)),
    }
    base: dict[str, Any] = {
        "experiment_id": EXPERIMENT_ID,
        "comparison_role": "WITHIN_DATA_TEMPORAL_DIAGNOSTIC_NOT_INDEPENDENT_EVALUATION",
        "development_cutoff_utc": _iso_utc(cutoff),
        "training_candidate_count": len(train_ids),
        "evaluation_candidate_count": len(evaluation_ids),
        "training_candidate_set_sha256": canonical_sha256(
            domain="FVG_MOVEMENT_CONTEXT_TRAINING_CASE_SET_V1", payload=train_ids
        ),
        "evaluation_candidate_set_sha256": canonical_sha256(
            domain="FVG_MOVEMENT_CONTEXT_EVALUATION_CASE_SET_V1", payload=evaluation_ids
        ),
        "same_m0_m1_case_set": True,
        "comparison_case_set_sha256": same_case_hash,
        "m0_features": list(M0_FEATURES),
        "m1_additional_features": list(M1_ADDITIONAL_FEATURES),
        "m1_features": list(M1_FEATURES),
        "target_comparison": {},
        "overlap": overlap,
        "inference": "NONE; NO STANDARD ERRORS, P_VALUES, OR CONFIDENCE INTERVALS",
        "interpretation_boundary": (
            "Target-specific descriptive RMSE only. One-month temporal split is not independent, "
            "overlapping paths are not IID, and no predictive, causal, or trading claim follows."
        ),
    }
    if not len(training_indices) or not len(evaluation_indices):
        base["status"] = "INCONCLUSIVE_NO_TRAINING_OR_EVALUATION_CASES"
        return base

    train_x_m0 = joined.iloc[training_indices].loc[:, list(M0_FEATURES)].to_numpy(dtype="float64")
    eval_x_m0 = joined.iloc[evaluation_indices].loc[:, list(M0_FEATURES)].to_numpy(dtype="float64")
    train_x_m1 = joined.iloc[training_indices].loc[:, list(M1_FEATURES)].to_numpy(dtype="float64")
    eval_x_m1 = joined.iloc[evaluation_indices].loc[:, list(M1_FEATURES)].to_numpy(dtype="float64")
    base["target_comparison"] = {}
    model_statuses = []
    for target in TARGETS:
        train_y = joined.iloc[training_indices][target].to_numpy(dtype="float64")
        eval_y = joined.iloc[evaluation_indices][target].to_numpy(dtype="float64")
        pred_m0, diagnostic_m0 = _ols_predict(train_x_m0, train_y, eval_x_m0)
        pred_m1, diagnostic_m1 = _ols_predict(train_x_m1, train_y, eval_x_m1)
        target_result: dict[str, Any] = {
            "target": target,
            "M0": diagnostic_m0,
            "M1": diagnostic_m1,
            "M0_RMSE": None,
            "M1_RMSE": None,
            "M1_MINUS_M0_RMSE": None,
            "status": "INCONCLUSIVE_MODEL_FIT",
        }
        if pred_m0 is not None and pred_m1 is not None:
            rmse0 = float(np.sqrt(np.mean(np.square(eval_y - pred_m0))))
            rmse1 = float(np.sqrt(np.mean(np.square(eval_y - pred_m1))))
            target_result.update(
                {
                    "M0_RMSE": rmse0,
                    "M1_RMSE": rmse1,
                    "M1_MINUS_M0_RMSE": rmse1 - rmse0,
                    "status": "DESCRIPTIVE_RMSE_AVAILABLE_NOT_INFERENTIAL",
                }
            )
        model_statuses.append(target_result["status"])
        base["target_comparison"][target] = target_result
    base["status"] = (
        "DESCRIPTIVE_TEMPORAL_COMPARISON_NOT_INDEPENDENT"
        if all(status == "DESCRIPTIVE_RMSE_AVAILABLE_NOT_INFERENTIAL" for status in model_statuses)
        else "INCONCLUSIVE_ONE_OR_MORE_MODEL_DESIGNS"
    )
    return base


def _coverage_counts(index: pd.DatetimeIndex, identity: SourceArtifactIdentity) -> dict[str, Any]:
    start = _utc_timestamp(identity.period_start_utc, "period_start_utc")
    end = _utc_timestamp(identity.period_end_utc, "period_end_utc")
    if end <= start:
        raise MovementContextExperimentError("declared source period end must follow its start")
    if start.value % EXPECTED_STEP.value or end.value % EXPECTED_STEP.value:
        raise MovementContextExperimentError("declared source period boundaries must align to exact UTC minutes")
    opens = index - EXPECTED_STEP
    if (opens < start).any() or (opens >= end).any():
        raise MovementContextExperimentError("source rows fall outside declared open-time period")
    expected_close_times = pd.date_range(
        start=start + EXPECTED_STEP,
        end=end,
        freq=EXPECTED_STEP,
        tz="UTC",
    )
    expected_ns = set(_index_values_ns(expected_close_times))
    observed_ns = set(_index_values_ns(index))
    missing_ns = sorted(expected_ns - observed_ns)
    extra_ns = sorted(observed_ns - expected_ns)
    return {
        "declared_expected_minute_slots": len(expected_ns),
        "observed_rows": len(index),
        "missing_expected_minute_count": len(missing_ns),
        "off_declared_grid_row_count": len(extra_ns),
        "missing_expected_minute_times_utc_first_100": [
            _iso_utc(pd.Timestamp(value, tz="UTC")) for value in missing_ns[:100]
        ],
        "coverage_claim": "OBSERVATIONS_VS_CALLER_DECLARED_UTC_1M_GRID_ONLY; NOT_FEED_OR_MARKET_COMPLETENESS",
    }


def build_experiment_from_surfaces(
    *,
    market_history: pd.DataFrame,
    timeline: MarketObservationTimeline,
    adapter: TimeIndexedTimelineAdapter,
    source_identity: SourceArtifactIdentity,
    source_file_sha256: str,
    fvg_surface: s4b2.Stage4B2FVGSurface,
    volatility_surface: s4a.Stage4ADomainSurface,
    htf_surface: s4c.Stage4CHtfScaleSurface,
    development_cutoff_utc: object,
    source_validation: KlineOhlcSource | None = None,
) -> ExperimentBundle:
    """Build the complete candidate/outcome/comparison bundle from verified surfaces.

    This entrypoint is useful for software tests and independent audits.
    SourceArtifactIdentity and the hash are caller declarations unless the
    optional KlineOhlcSource from the CLI adapter route is supplied. Neither
    path authenticates the provider or proves exchange origin.
    """
    cutoff = _utc_timestamp(development_cutoff_utc, "development_cutoff_utc")
    market = _check_market_frame(
        market_history,
        timeline=timeline,
        adapter=adapter,
        source_file_sha256=source_file_sha256,
    )
    if not isinstance(source_identity, SourceArtifactIdentity):
        raise MovementContextExperimentError("SourceArtifactIdentity is required")
    try:
        s4b2.verify_surface_integrity(fvg_surface)
        s4a.verify_surface_integrity(volatility_surface)
        s4c.verify_surface_integrity(htf_surface)
    except Exception as exc:
        raise MovementContextExperimentError(f"surface integrity verification failed: {exc}") from exc

    if fvg_surface.structure_surface_id is not None:
        raise MovementContextExperimentError("FVG input must be the sealed structure-independent Stage4B2 surface")
    surfaces = (fvg_surface, volatility_surface, htf_surface)
    for surface in surfaces:
        if (
            getattr(surface, "timeline_id", None) != timeline.timeline_id
            or getattr(surface, "timeline_hash", None) != timeline.timeline_hash
        ):
            raise MovementContextExperimentError("surface/timeline identity mismatch")
    if volatility_surface.domain != "VOLATILITY":
        raise MovementContextExperimentError("only the sealed Stage4A VOLATILITY domain is supported")
    if (
        htf_surface.domain != "HTF_SCALE_RAW"
        or htf_surface.scale_name != HTF_SCALE_NAME
        or htf_surface.scale_duration_ns != int(HTF_SCALE_DURATION.value)
        or htf_surface.cadence_contract_hash != _experiment_htf_cadence_hash()
    ):
        raise MovementContextExperimentError(
            "HTF surface must match the frozen completed raw H1 and one-minute cadence contracts"
        )
    if not volatility_surface.surface.index.equals(market.index):
        raise MovementContextExperimentError("Stage4A row index mismatch")
    if not htf_surface.asof_bar_frame.index.equals(market.index):
        raise MovementContextExperimentError("Stage4C row index mismatch")

    source_hash = _sha256_text(source_file_sha256, "source_file_sha256")
    source_validation_metadata = _source_validation_metadata(
        source_validation,
        identity=source_identity,
        source_file_sha256=source_hash,
        timeline=timeline,
        adapter=adapter,
    )
    s1_facts, s1_dataset_identity = _s1_path_facts(
        market,
        adapter=adapter,
        source_identity=source_identity,
        source_file_sha256=source_hash,
    )
    raw_market_for_chain = market.loc[:, list(timeline.required_columns) + list(timeline.optional_columns_present)]
    raw_prefixes = _prefix_chain_for_frame(
        raw_market_for_chain,
        component="CANONICAL_PUBLISHED_KLINE_OHLC_PREFIX",
        contract_version=MARKET_TIMELINE_SOURCE_VERSION,
        configuration_identity=KLINES_SCHEMA_CONTRACT,
        expected_index=market.index,
    )
    s1_rows = []
    for item in s1_facts:
        values = item["descriptor_values"]
        s1_rows.append(
            {
                "observed_close_path_length": values["observed_close_path_length"],
                "grid_contiguous_close_path_length": values["grid_contiguous_close_path_length"],
                "running_high_so_far": values["running_high_so_far"],
                "running_low_so_far": values["running_low_so_far"],
                "bar_count_observed": values["bar_count_observed"],
                "bar_count_grid": values["bar_count_grid"],
                "sum_close_displacement": values["sum_close_displacement"],
                "close_displacement": item["close_displacement"],
                "adjacency_kind": item["adjacency_kind"],
            }
        )
    s1_frame = pd.DataFrame(s1_rows, index=market.index)
    s1_prefixes = _prefix_chain_for_frame(
        s1_frame,
        component="MUF_S1_CAUSAL_OBSERVATION_ADJACENT_PATH_FACTS",
        contract_version=PRICE_PATH_SCHEMA.schema_version,
        configuration_identity=_S1_DESCRIPTOR_CONFIGURATION_SHA256,
        expected_index=market.index,
    )
    vol_output = volatility_surface.surface.loc[:, list(volatility_surface.output_columns)].copy(deep=True)
    vol_prefixes = _prefix_chain_for_frame(
        vol_output,
        component="STAGE4A_VOLATILITY_OUTPUT_ROWS",
        contract_version=volatility_surface.contract_version,
        configuration_identity=volatility_surface.configuration_binding_hash,
        expected_index=market.index,
    )
    htf_prefixes = _prefix_chain_for_frame(
        htf_surface.asof_bar_frame,
        component="STAGE4C_COMPLETED_HTF_ASOF_ROWS",
        contract_version=htf_surface.contract_version,
        configuration_identity=htf_surface.cadence_contract_hash,
        expected_index=market.index,
    )

    normalized_events = fvg_surface.normalized_event_frame
    creation_events = normalized_events.loc[normalized_events["event_type"] == "FVG_CREATED"].copy(deep=True)
    entities = fvg_surface.normalized_entity_frame
    if len(creation_events) != len(entities):
        raise MovementContextExperimentError("FVG_CREATED event/entity coverage mismatch")
    if entities["fvg_id"].duplicated().any() or creation_events["fvg_id"].duplicated().any():
        raise MovementContextExperimentError("FVG IDs must be unique in the creation population")
    event_by_id = {
        str(row["fvg_id"]): row
        for _, row in creation_events.iterrows()
    }
    if set(event_by_id) != set(entities["fvg_id"].astype(str)):
        raise MovementContextExperimentError("FVG creation event/entity identity mismatch")
    fvg_records = _path_event_records(normalized_events, row_count=len(market))
    fvg_prefixes = _prefix_chain_for_sparse_records(
        fvg_records,
        component="STAGE4B2_FVG_CREATED_EVENTS_ONLY",
        contract_version=s4b2.TRAJECTORY_STAGE4B2_CONTRACT_VERSION,
        configuration_identity=canonical_sha256(
            domain="FVG_MOVEMENT_CONTEXT_CREATION_EVENT_SCHEMA_V1",
            payload={
                "normalized_event_columns": list(normalized_events.columns),
                "included_event_types": ["FVG_CREATED"],
            },
        ),
        index=market.index,
    )

    htf_prefix = f"{HTF_SCALE_NAME}__"
    htf_asof = htf_surface.asof_bar_frame
    vol_surface = volatility_surface.surface
    candidates: list[dict[str, Any]] = []
    for _, entity in entities.iterrows():
        candidate_id = str(entity["fvg_id"])
        event = event_by_id[candidate_id]
        position = int(entity["creation_position"])
        if int(event["event_position"]) != position or position != int(entity["creation_position"]):
            raise MovementContextExperimentError("FVG creation key and entity position mismatch")
        if position < 0 or position >= len(market):
            raise MovementContextExperimentError("FVG creation position outside timeline")
        key = adapter.key_for_position(
            market.index,
            position,
            InformationPhase.COMPLETED_ROW_AVAILABLE,
            deterministic_sequence=0,
        )
        close = float(market["close"].iloc[position])
        s1 = s1_facts[position]
        descriptors = s1["descriptor_values"]
        vol_row = vol_surface.iloc[position]
        htf_row = htf_asof.iloc[position]
        direction = str(entity["direction"])
        if not (direction.startswith("BULLISH_FVG_CANDIDATE") or direction.startswith("BEARISH_FVG_CANDIDATE")):
            raise MovementContextExperimentError(f"unsupported FVG direction token {direction!r}")

        row: dict[str, Any] = {
            "candidate_id": candidate_id,
            "fvg_id": candidate_id,
            "event_type": "FVG_CREATED",
            "direction": direction,
            "origin_position": int(entity["origin_position"]),
            "middle_position": int(entity["middle_position"]),
            "creation_position": position,
            "creation_time_utc": _iso_utc(key.event_time_utc),
            "creation_key_timeline_id": key.timeline_id,
            "creation_key_bar_position": key.bar_position,
            "creation_key_information_phase": key.information_phase.value,
            "creation_key_deterministic_sequence": key.deterministic_sequence,
            "same_information_batch_order_unknown": bool(event["same_information_batch_order_unknown"]),
            "fvg_zone_low": float(entity["zone_low"]),
            "fvg_zone_high": float(entity["zone_high"]),
            "fvg_midpoint": float(entity["midpoint"]),
            "fvg_gap_width": float(entity["gap_width"]),
            "fvg_gap_width_fraction": _json_safe(entity["gap_width_fraction"]),
            "fvg_gap_width_percentile": _json_safe(entity["gap_width_percentile"]),
            "fvg_gap_width_history_count": _json_safe(entity["gap_width_history_count"]),
            "fvg_middle_body_fraction": _json_safe(entity["middle_body_fraction"]),
            "fvg_middle_signed_body_fraction": _json_safe(entity["middle_signed_body_fraction"]),
            "fvg_creation_close_price": close,
            "source_file_sha256": source_hash,
            "source_adapter": _SOURCE_ADAPTER_ID,
            "source_schema_contract": KLINES_SCHEMA_CONTRACT,
            "source_validation_state": source_validation_metadata["state"],
            "source_origin_authenticated": False,
            "source_timestamp_unit": source_identity.timestamp_unit,
            "source_symbol": source_identity.symbol,
            "source_market_type": source_identity.market_type,
            "source_interval": source_identity.interval,
            "source_period_start_utc": source_identity.period_start_utc,
            "source_period_end_utc": source_identity.period_end_utc,
            "timeline_id": timeline.timeline_id,
            "timeline_hash": timeline.timeline_hash,
            "timeline_source_version": MARKET_TIMELINE_SOURCE_VERSION,
            "s1_dataset_identity": s1_dataset_identity,
            "s1_source_schema_domain": S1_BAR_SOURCE_IDENTITY.schema_domain,
            "s1_source_schema_version": S1_BAR_SOURCE_IDENTITY.schema_version,
            "s1_schema_domain": PRICE_PATH_SCHEMA.schema_domain,
            "s1_schema_version": PRICE_PATH_SCHEMA.schema_version,
            "s1_descriptor_configuration_sha256": _S1_DESCRIPTOR_CONFIGURATION_SHA256,
            "s1_declared_grid_state": "NOT_CONFIGURED_NO_DECLARED_GRID",
            "fvg_full_surface_id": fvg_surface.surface_id,
            "fvg_contract_version": s4b2.TRAJECTORY_STAGE4B2_CONTRACT_VERSION,
            "fvg_reconstruction_input_hash": fvg_surface.reconstruction_input_hash,
            "fvg_complete_result_hash": fvg_surface.complete_result_hash,
            "fvg_normalized_entity_hash": fvg_surface.normalized_entity_hash,
            "fvg_normalized_event_hash": fvg_surface.normalized_event_hash,
            "fvg_structure_surface_id": fvg_surface.structure_surface_id,
            "stage4a_surface_id": volatility_surface.surface_id,
            "stage4a_contract_version": volatility_surface.contract_version,
            "stage4a_configuration_binding_hash": volatility_surface.configuration_binding_hash,
            "stage4a_reconstruction_input_hash": volatility_surface.reconstruction_input_hash,
            "stage4c_surface_id": htf_surface.surface_id,
            "stage4c_contract_version": htf_surface.contract_version,
            "stage4c_scale_name": htf_surface.scale_name,
            "stage4c_scale_duration_ns": htf_surface.scale_duration_ns,
            "stage4c_cadence_contract_hash": htf_surface.cadence_contract_hash,
            "stage4c_reconstruction_input_hash": htf_surface.reconstruction_input_hash,
            "market_prefix_chain_sha256": raw_prefixes[position],
            "fvg_creation_prefix_chain_sha256": fvg_prefixes[position],
            "s1_prefix_chain_sha256": s1_prefixes[position],
            "stage4a_prefix_chain_sha256": vol_prefixes[position],
            "stage4c_prefix_chain_sha256": htf_prefixes[position],
        }
        # M0: creation-time FVG entity geometry only, with the creation close
        # named explicitly as the reference level. Redundant exact combinations
        # (e.g. midpoint and both zone edges as separate regressors) are retained
        # in the artifact but not all redundantly inserted into the fixed model.
        _feature_value(row, "fvg_is_bullish", direction.startswith("BULLISH_FVG_CANDIDATE"))
        _feature_value(row, "fvg_midpoint_distance_fraction", (float(entity["midpoint"]) - close) / close)
        for feature, source_field in (
            ("fvg_gap_width_fraction", "gap_width_fraction"),
            ("fvg_gap_width_percentile", "gap_width_percentile"),
            ("fvg_gap_width_history_count", "gap_width_history_count"),
            ("fvg_middle_body_fraction", "middle_body_fraction"),
            ("fvg_middle_signed_body_fraction", "middle_signed_body_fraction"),
        ):
            _feature_value(row, feature, entity[source_field])
        _feature_value(row, "fvg_creation_close_price", close)

        # MUF S1 facts are observation-adjacent/completed-row facts only. The
        # grid-specific descriptors remain explicitly NOT_CONFIGURED here.
        for name in _S1_RAW_DESCRIPTOR_FIELDS:
            value = descriptors[name]
            number, state = _number_and_state(value)
            row[f"s1_{name}"] = number
            row[f"s1_{name}__state"] = state
        close_step_state = (
            TypedState.UNAVAILABLE
            if s1["close_displacement"] is None
            else s1["close_displacement"]
        )
        close_path_step_state = (
            TypedState.UNAVAILABLE
            if s1["close_path_step"] is None
            else s1["close_path_step"]
        )
        _feature_value(row, "s1_close_step_fraction", _ratio_and_state(close_step_state, close)[0])
        _feature_value(row, "s1_close_path_step_fraction", _ratio_and_state(close_path_step_state, close)[0])
        _feature_value(row, "s1_observed_close_path_length_fraction", _ratio_and_state(
            descriptors["observed_close_path_length"], close
        )[0])
        _feature_value(row, "s1_running_high_distance_fraction", _ratio_and_state(
            float(descriptors["running_high_so_far"]) - close, close
        )[0])
        _feature_value(row, "s1_running_low_distance_fraction", _ratio_and_state(
            float(descriptors["running_low_so_far"]) - close, close
        )[0])
        _feature_value(row, "s1_sum_close_displacement_fraction", _ratio_and_state(
            descriptors["sum_close_displacement"], close
        )[0])
        _feature_value(row, "s1_bar_count_observed", descriptors["bar_count_observed"])
        if s1["close_displacement"] is None:
            row["s1_close_step_fraction__state"] = "NO_PRIOR_OBSERVATION"
        if s1["close_path_step"] is None:
            row["s1_close_path_step_fraction__state"] = "NO_PRIOR_OBSERVATION"
        row["s1_observation_adjacency_kind"] = s1["adjacency_kind"] or "NO_PRIOR_OBSERVATION"
        row["s1_grid_contiguity_state"] = str(_json_safe(descriptors["grid_contiguous_close_path_length"]))
        row["s1_bar_count_grid_state"] = str(_json_safe(descriptors["bar_count_grid"]))

        # Stage4A: preserve every supported volatility column and its typed
        # missingness. Model uses only the frozen numeric subset below.
        for column in _VOLATILITY_COLUMNS:
            value = vol_row[column]
            number, state = _number_and_state(value)
            row[f"stage4a_{column}"] = number
            row[f"stage4a_{column}__state"] = state
        for feature in (
            "normalized_true_range",
            "true_range_percentile",
            "normalized_tr_change",
            "expansion_percentile",
        ):
            _feature_value(row, f"stage4a_{feature}", vol_row[feature])

        # Stage4C: the last completed raw HTF OHLC bucket as projected at this
        # exact LTF completed-row key. Same-batch order-unknown is metadata, not
        # an inferred before/after relation.
        for field in _HTF_METADATA_FIELDS:
            value = htf_row[f"{htf_prefix}{field}"]
            row[f"stage4c_h1_{field}"] = _json_safe(value)
            row[f"stage4c_h1_{field}__state"] = _state_name(value)
        for field in ("open", "high", "low", "close"):
            htf_value = htf_row[f"{htf_prefix}completed_bucket_{field}"]
            feature = f"h1_{field}_relative_to_creation_close"
            value, state = _ratio_and_state(htf_value, close, offset=-1.0)
            _feature_value(row, feature, value if state == "AVAILABLE" else TypedState.UNAVAILABLE)
            if state != "AVAILABLE":
                row[f"{feature}__state"] = state
        row["stage4c_h1_context_state"] = (
            "AVAILABLE"
            if _state_name(htf_row[f"{htf_prefix}completed_bucket_close"]) == "AVAILABLE"
            else str(htf_row[f"{htf_prefix}coverage_status"])
        )

        context_content = {
            "candidate_id": candidate_id,
            "creation_key": key,
            "m0_features": {name: row[name] for name in M0_FEATURES},
            "m0_states": {name: row[f"{name}__state"] for name in M0_FEATURES},
            "m1_additions": {name: row[name] for name in M1_ADDITIONAL_FEATURES},
            "m1_states": {name: row[f"{name}__state"] for name in M1_ADDITIONAL_FEATURES},
            "prefix_chain_ids": {
                "market": raw_prefixes[position],
                "fvg_created": fvg_prefixes[position],
                "s1": s1_prefixes[position],
                "stage4a": vol_prefixes[position],
                "stage4c": htf_prefixes[position],
            },
        }
        row["candidate_context_sha256"] = canonical_sha256(
            domain="FVG_MOVEMENT_CONTEXT_CANDIDATE_CONTEXT_V1",
            payload=context_content,
        )
        candidates.append(row)

    candidate_frame = pd.DataFrame(candidates)
    candidate_columns = _empty_candidate_columns()
    if candidate_frame.empty:
        candidate_frame = pd.DataFrame(columns=candidate_columns)
    else:
        if set(candidate_frame.columns) != set(candidate_columns):
            raise MovementContextExperimentError("candidate context schema differs from the frozen output schema")
        candidate_frame = candidate_frame.reindex(columns=candidate_columns)
    if len(candidate_frame) != len(entities):
        raise MovementContextExperimentError("candidate universe coverage failure")
    if candidate_frame["candidate_id"].duplicated().any():
        raise MovementContextExperimentError("candidate IDs are not unique")
    horizon_policy_hash = canonical_sha256(
        domain="FVG_MOVEMENT_CONTEXT_HORIZON_POLICY_V1",
        payload={
            "policy_id": HORIZON_POLICY_ID,
            "horizon_ns": int(HORIZON.value),
            "reference": "FVG_CREATION_COMPLETED_ROW_CLOSE",
            "interval": "(DECISION, EXACT_UTC_DECISION_PLUS_ONE_HOUR]",
            "coverage_step_ns": int(EXPECTED_STEP.value),
            "missing_in_range_boundary": "PRESERVE_PARTIAL_OBSERVATIONS; NO_NEAREST_ROW_SUBSTITUTION; NOT_SCOREABLE",
            "censoring": "FOLLOW_TRAJECTORY_QUERY_SOURCE_END_RULE_WHERE_REQUESTABLE",
        },
    )
    outcomes = _outcome_rows(
        candidate_frame,
        market,
        adapter=adapter,
        horizon_policy_hash=horizon_policy_hash,
    )
    outcomes["development_cutoff_utc"] = _iso_utc(cutoff)
    outcomes["model_split_state"] = [
        "CROSSES_DEVELOPMENT_CUTOFF"
        if pd.Timestamp(row["decision_time_utc"]) < cutoff
        and pd.Timestamp(row["requested_horizon_end_utc"]) >= cutoff
        else "PRE_CUTOFF"
        if pd.Timestamp(row["decision_time_utc"]) < cutoff
        else "POST_CUTOFF"
        for row in outcomes.to_dict(orient="records")
    ]
    comparison = _fit_comparison(candidate_frame, outcomes, cutoff=cutoff)
    source_metadata = _source_metadata(
        source_identity=source_identity,
        source_file_sha256=source_hash,
        timeline=timeline,
        fvg_surface=fvg_surface,
        volatility_surface=volatility_surface,
        htf_surface=htf_surface,
        source_validation=source_validation_metadata,
    )
    protocol_payload = {
        "experiment_id": EXPERIMENT_ID,
        "status": "EXPLORATORY_PROTOCOL_NOT_PREREGISTERED_OUTSIDE_THIS_FROZEN_RUN_ARTIFACT",
        "empirical_question": (
            "Within the same complete, contiguous, uncensored one-hour post-creation OHLC windows, "
            "does the fixed M1 joint factual movement-context feature block reduce each separate "
            "excursion-component RMSE relative to M0 FVG creation geometry alone?"
        ),
        "statistical_unit": "ONE_STAGE4B2_FVG_CREATED_ENTITY; ALL_CREATION_ENTITIES_RETAINED",
        "m0_fields": list(M0_FEATURES),
        "m1_additional_fields": list(M1_ADDITIONAL_FEATURES),
        "feature_semantics": {
            "M0": "Stage4B2 FVG creation geometry plus its completed-row creation close; not lifecycle fields",
            "M1": "M0 plus MUF S1 observation-adjacent path facts, causal Stage4A volatility facts, and completed Stage4C H1 raw OHLC",
            "correlated_context": "All price-derived M1 fields are one joint block; no independent-evidence attribution",
            "typed_missingness": "Preserved in candidate_context.csv; no imputation; one complete-case mask shared by M0 and M1",
        },
        "outcome": {
            "contract_reference": "TrajectoryWindow + ExcursionView semantics, batch-extracted and parity-tested",
            "horizon_policy_id": HORIZON_POLICY_ID,
            "horizon_ns": int(HORIZON.value),
            "interval": "(creation completed-row key, exact UTC creation timestamp + 1 hour]",
            "reference": "published creation-row close (MARKET_MARK)",
            "targets": list(TARGETS),
            "no_binary_label": True,
            "same_bar_order": "UNPROVEN; no intrabar chronology reconstructed",
            "missing_in_range_boundary": "No approximate/nearest row; preserve observed pre-boundary path and mark unqueryable/not scoreable",
            "right_censoring": "Use observed rows through dataset end; mark right-censored; not scoreable as a complete one-hour outcome",
            "coverage": "Exact one-minute timestamp deltas; gaps/cadence deviations retained and not scored in the fixed complete-window comparison",
        },
        "estimator": {
            "name": "UNREGULARIZED_ORDINARY_LEAST_SQUARES",
            "implementation": "numpy.linalg.lstsq",
            "intercept": True,
            "feature_standardization": "TRAINING_ONLY_MEAN_AND_POPULATION_STD",
            "feature_selection": "NONE",
            "hyperparameter_search": "NONE",
            "regularization": "NONE",
            "model_outputs": "two target-specific RMSE values; no combined relevance score and no coefficient interpretation",
        },
        "development_evaluation": {
            "fit_rows": "creation before cutoff and exact one-hour outcome ends strictly before cutoff",
            "evaluation_rows": "creation at/after cutoff; exact complete contiguous one-hour outcome required",
            "crossing_rows": "retained in candidate/outcome tables; excluded from both roles because the outcome interval crosses the cutoff",
            "same_month_status": "WITHIN_DATA_TEMPORAL_DIAGNOSTIC_ONLY_NOT_INDEPENDENT_HOLDOUT",
        },
        "overlap": "All candidates retained; report observed-window overlap pairs/concurrency separately for training, evaluation, and combined model cases; no IID inference or uncertainty estimator",
        "interpretation": "Descriptive empirical comparison only; no causal, market-theory, trading, execution, fill, probability, or predictive-validity claim",
        "source_and_surface_identity": source_metadata,
        "cutoff_utc": _iso_utc(cutoff),
    }
    protocol_hash = canonical_sha256(
        domain="FVG_MOVEMENT_CONTEXT_PROTOCOL_V1",
        payload=protocol_payload,
    )
    protocol = dict(protocol_payload)
    protocol["protocol_sha256"] = protocol_hash
    outcome_counts = {
        str(key): int(value)
        for key, value in outcomes["path_status"].value_counts(dropna=False).items()
    }
    summary = {
        "experiment_id": EXPERIMENT_ID,
        "protocol_sha256": protocol_hash,
        "source": source_metadata,
        "declared_grid_coverage": _coverage_counts(market.index, source_identity),
        "candidate_count": len(candidate_frame),
        "all_stage4b2_creation_entities_preserved": len(candidate_frame) == len(entities),
        "outcome_path_status_counts": outcome_counts,
        "scoreable_complete_contiguous_uncensored_outcomes": int(outcomes["scoreable_under_frozen_protocol"].sum()),
        "comparison_status": comparison["status"],
        "comparison": comparison,
        "empirical_claim": (
            "NONE; this descriptive output establishes neither market-theory support nor predictive validity"
        ),
    }
    return ExperimentBundle(
        candidate_context=candidate_frame,
        excursion_outcomes=outcomes,
        comparison=comparison,
        protocol=protocol,
        summary=summary,
        timeline=timeline,
        adapter=adapter,
    )


def build_experiment(
    *,
    market_history: pd.DataFrame,
    source_identity: SourceArtifactIdentity,
    source_file_sha256: str,
    development_cutoff_utc: object,
    timeline_id: str,
    source_validation: KlineOhlcSource | None = None,
) -> ExperimentBundle:
    """Build timeline and shared surfaces, then create the experiment bundle."""
    if not isinstance(market_history.index, pd.DatetimeIndex) or market_history.index.tz is None:
        raise MovementContextExperimentError("the experiment requires a timezone-aware time index")
    market = market_history.copy(deep=True)
    # Public Stage4C V1's timestamp-grid arithmetic is nanosecond based. This
    # changes only the DatetimeIndex storage resolution; every UTC instant is
    # preserved exactly and the normalized index is what gets sealed.
    market.index = market.index.tz_convert("UTC").as_unit("ns")
    adapter = TimeIndexedTimelineAdapter(timeline_id)
    timeline = MarketObservationTimeline.seal(adapter=adapter, market_history=market)
    fvg_surface = s4b2.build_fvg_surface(
        timeline=timeline,
        adapter=adapter,
        market_history=market,
    )
    volatility_surface = s4a.build_volatility_surface(
        timeline=timeline,
        adapter=adapter,
        market_history=market,
    )
    cadence = _experiment_htf_cadence_contract()
    htf_surface = s4c.build_htf_scale_surface(
        timeline=timeline,
        adapter=adapter,
        market_history=market,
        scale_spec=s4c.HtfScaleSpec(HTF_SCALE_NAME, HTF_SCALE_DURATION),
        cadence=cadence,
    )
    return build_experiment_from_surfaces(
        market_history=market,
        timeline=timeline,
        adapter=adapter,
        source_identity=source_identity,
        source_file_sha256=source_file_sha256,
        fvg_surface=fvg_surface,
        volatility_surface=volatility_surface,
        htf_surface=htf_surface,
        development_cutoff_utc=development_cutoff_utc,
        source_validation=source_validation,
    )


def _write_json(path: Path, content: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(_json_safe(content), ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_paths(path: Path, outcomes: pd.DataFrame, market_history: pd.DataFrame) -> None:
    columns = (
        "candidate_id",
        "path_id",
        "bar_position",
        "event_time_utc",
        "open",
        "high",
        "low",
        "close",
        "intrabar_high_low_order",
    )
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        for outcome in outcomes.to_dict(orient="records"):
            start = outcome["path_start_position_inclusive"]
            end = outcome["path_end_position_inclusive"]
            if start is None or end is None or pd.isna(start) or pd.isna(end):
                continue
            for position in range(int(start), int(end) + 1):
                row = market_history.iloc[position]
                writer.writerow(
                    (
                        outcome["candidate_id"],
                        outcome["path_id"],
                        position,
                        _iso_utc(market_history.index[position]),
                        format(float(row["open"]), ".17g"),
                        format(float(row["high"]), ".17g"),
                        format(float(row["low"]), ".17g"),
                        format(float(row["close"]), ".17g"),
                        "UNPROVEN_FROM_PUBLISHED_OHLC",
                    )
                )


def _market_frame_for_bundle(
    bundle: ExperimentBundle,
    market_history: pd.DataFrame,
) -> pd.DataFrame:
    if not isinstance(bundle, ExperimentBundle):
        raise MovementContextExperimentError("write_outputs requires an ExperimentBundle")
    if not isinstance(market_history, pd.DataFrame) or not isinstance(market_history.index, pd.DatetimeIndex):
        raise MovementContextExperimentError("output market_history must have a DatetimeIndex")
    if market_history.index.tz is None:
        raise MovementContextExperimentError("output market index must be timezone-aware")
    target_dtype = bundle.timeline.index_dtype
    try:
        target_unit = target_dtype.split("[", 1)[1].split(",", 1)[0]
        if target_unit not in {"s", "ms", "us", "ns"}:
            raise ValueError("unsupported sealed timestamp resolution")
        snapshot = market_history.copy(deep=True)
        snapshot.index = snapshot.index.tz_convert("UTC").as_unit(target_unit, round_ok=False)
        bundle.timeline.verify(adapter=bundle.adapter, market_history=snapshot)
    except Exception as exc:
        raise MovementContextExperimentError(
            f"output OHLC frame does not match the sealed experiment timeline: {exc}"
        ) from exc
    return snapshot


def write_outputs(
    bundle: ExperimentBundle,
    *,
    market_history: pd.DataFrame,
    output_dir: str | Path,
) -> Path:
    """Write reproducible CSV/JSON artifacts to a new, caller-selected directory."""
    market_snapshot = _market_frame_for_bundle(bundle, market_history)
    destination = Path(output_dir)
    if destination.exists() and any(destination.iterdir()):
        raise MovementContextExperimentError("output directory must be new or empty; refusing to overwrite")
    destination.mkdir(parents=True, exist_ok=True)
    candidate_path = destination / "candidate_context.csv"
    outcome_path = destination / "excursion_outcomes.csv"
    path_path = destination / "observed_paths.csv"
    bundle.candidate_context.to_csv(candidate_path, index=False, na_rep="", float_format="%.17g")
    bundle.excursion_outcomes.to_csv(outcome_path, index=False, na_rep="", float_format="%.17g")
    _write_paths(path_path, bundle.excursion_outcomes, market_snapshot)
    _write_json(destination / "protocol.json", bundle.protocol)
    _write_json(destination / "comparison.json", bundle.comparison)
    _write_json(destination / "summary.json", bundle.summary)
    output_files = (
        candidate_path,
        outcome_path,
        path_path,
        destination / "protocol.json",
        destination / "comparison.json",
        destination / "summary.json",
    )
    manifest_lines = [
        f"{sha256_file(str(file_path))}  {file_path.name}"
        for file_path in output_files
    ]
    (destination / "OUTPUT_MANIFEST.sha256").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    return destination


def _validate_source_period(source, identity: SourceArtifactIdentity) -> dict[str, Any]:
    market = source.canonical_market_frame
    coverage = _coverage_counts(market.index, identity)
    open_us = pd.to_numeric(source.exact_frame["open_time"], errors="raise").to_numpy(dtype="int64")
    start_ns = int(_utc_timestamp(identity.period_start_utc, "period_start_utc").value)
    end_ns = int(_utc_timestamp(identity.period_end_utc, "period_end_utc").value)
    open_ns = open_us * 1000
    if (open_ns < start_ns).any() or (open_ns >= end_ns).any():
        raise MovementContextExperimentError("source file open_time rows fall outside SourceArtifactIdentity period")
    coverage["source_adapter_interior_missing_intervals"] = len(source.missing_minute_intervals)
    coverage["source_adapter_required_full_coverage"] = source.require_full_coverage
    return coverage


def _source_validation_metadata(
    source: KlineOhlcSource | None,
    *,
    identity: SourceArtifactIdentity,
    source_file_sha256: str,
    timeline: MarketObservationTimeline,
    adapter: TimeIndexedTimelineAdapter,
) -> dict[str, Any]:
    """Describe schema/period checks without claiming trusted-source origin."""
    if source is None:
        return {
            "state": "CALLER_SUPPLIED_FRAME_NOT_VERIFIED_BY_BINANCE_ADAPTER",
            "adapter": _SOURCE_ADAPTER_ID,
            "schema_contract_expected_for_cli": KLINES_SCHEMA_CONTRACT,
            "source_origin_authenticated": False,
        }
    if not isinstance(source, KlineOhlcSource):
        raise MovementContextExperimentError("source_validation must be a KlineOhlcSource")
    if source.identity != identity:
        raise MovementContextExperimentError("validated kline source identity mismatch")
    if source.provenance.schema_contract != KLINES_SCHEMA_CONTRACT:
        raise MovementContextExperimentError("validated kline schema contract mismatch")
    if source.provenance.source_file_sha256 != source_file_sha256:
        raise MovementContextExperimentError("validated kline file hash mismatch")
    source_market = source.canonical_market_frame.copy(deep=True)
    try:
        target_unit = timeline.index_dtype.split("[", 1)[1].split(",", 1)[0]
        source_market.index = source_market.index.tz_convert("UTC").as_unit(
            target_unit,
            round_ok=False,
        )
    except Exception as exc:
        raise MovementContextExperimentError(
            f"validated source index cannot match sealed timeline resolution: {exc}"
        ) from exc
    _check_market_frame(
        source_market,
        timeline=timeline,
        adapter=adapter,
        source_file_sha256=source_file_sha256,
    )
    period_coverage = _validate_source_period(source, identity)
    return {
        "state": "BINANCE_KLINE_SCHEMA_AND_DECLARED_PERIOD_VALIDATED_NOT_ORIGIN_AUTHENTICATED",
        "adapter": _SOURCE_ADAPTER_ID,
        "schema_contract": source.provenance.schema_contract,
        "source_rows": source.provenance.source_rows,
        "timestamp_unit": source.provenance.timestamp_unit,
        "numeric_contract": source.provenance.numeric_contract,
        "ohlc_source_label": source.provenance.ohlc_source_label,
        "tie_order_contract": source.provenance.tie_order_contract,
        "published_fact_statement": source.provenance.published_fact_statement,
        "historical_research_contract": source.provenance.historical_research_contract,
        "require_full_coverage": source.require_full_coverage,
        "source_missing_minute_interval_count": len(source.missing_minute_intervals),
        "period_coverage": period_coverage,
        "source_origin_authenticated": False,
    }


def run_from_binance_csv(
    *,
    csv_path: str | Path,
    identity: SourceArtifactIdentity,
    development_cutoff_utc: object,
    output_dir: str | Path,
) -> ExperimentBundle:
    source_path = Path(csv_path)
    source_hash = sha256_file(str(source_path))
    source = load_binance_spot_klines(
        str(source_path),
        identity=identity,
        require_full_coverage=False,
    )
    timeline_id = f"binance-spot-kline-{identity.symbol.lower()}-{source_hash[:20]}"
    bundle = build_experiment(
        market_history=source.canonical_market_frame,
        source_identity=identity,
        source_file_sha256=source_hash,
        development_cutoff_utc=development_cutoff_utc,
        timeline_id=timeline_id,
        source_validation=source,
    )
    write_outputs(bundle, market_history=source.canonical_market_frame, output_dir=output_dir)
    return bundle


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", required=True, help="Official Binance Spot 1m klines CSV (12 headerless columns)")
    parser.add_argument("--symbol", required=True, help="Binance Spot symbol, e.g. BTCUSDT")
    parser.add_argument("--period-start-utc", required=True, help="Declared inclusive kline open-time start, ISO UTC Z")
    parser.add_argument("--period-end-utc", required=True, help="Declared exclusive kline open-time end, ISO UTC Z")
    parser.add_argument("--development-cutoff-utc", required=True, help="Predeclared temporal split boundary, ISO UTC Z")
    parser.add_argument("--output-dir", required=True, help="New external output directory; existing non-empty directories are refused")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    identity = SourceArtifactIdentity(
        symbol=args.symbol,
        market_type="SPOT",
        interval="1m",
        period_start_utc=args.period_start_utc,
        period_end_utc=args.period_end_utc,
    )
    bundle = run_from_binance_csv(
        csv_path=args.csv,
        identity=identity,
        development_cutoff_utc=args.development_cutoff_utc,
        output_dir=args.output_dir,
    )
    print(json.dumps(_json_safe(bundle.summary), ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
