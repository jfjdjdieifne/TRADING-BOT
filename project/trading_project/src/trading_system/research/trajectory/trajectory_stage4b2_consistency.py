"""Independent local cross-table checks for captured Stage4B2 surfaces.

This validator consumes an already privately captured public surface snapshot.
It does not replay any producer and does not authenticate producer code, market
sources, or market semantics. A returned LOCAL_VERIFIED_PRODUCER_SURFACE label
means only that this exact local snapshot passed Stage4B2's existing integrity
check and the cross-table/source-witness checks below.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

import numpy as np
import pandas as pd

from trading_system.research.hashing import canonical_sha256
from trading_system.research.trajectory import trajectory_stage4b2 as s4b2


LOCAL_VERIFICATION_SCOPE = "LOCAL_VERIFIED_PRODUCER_SURFACE"


class Stage4B2ConsistencyError(ValueError):
    """A captured Stage4B2 surface failed integrity or factual consistency."""


@dataclass(frozen=True)
class Stage4B2ConsistencyResult:
    """Success-only local verification result for one concrete surface snapshot."""

    domain: str
    surface_id: str
    verification_scope: str
    checks: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.domain not in {"LIQUIDITY", "ORDER_BLOCK", "FVG", "DEALING_RANGE"}:
            raise Stage4B2ConsistencyError("invalid Stage4B2 result domain")
        if not isinstance(self.surface_id, str) or not self.surface_id:
            raise Stage4B2ConsistencyError("surface_id must be nonempty")
        if self.verification_scope != LOCAL_VERIFICATION_SCOPE:
            raise Stage4B2ConsistencyError("invalid local verification scope")
        if not isinstance(self.checks, tuple) or not self.checks:
            raise Stage4B2ConsistencyError("successful verification must name its checks")


_DOMAIN_BY_CLASS = {
    s4b2.Stage4B2LiquiditySurface: "LIQUIDITY",
    s4b2.Stage4B2OrderBlockSurface: "ORDER_BLOCK",
    s4b2.Stage4B2FVGSurface: "FVG",
    s4b2.Stage4B2DealingRangeSurface: "DEALING_RANGE",
}
_CONTRACT_BY_DOMAIN = {
    "LIQUIDITY": s4b2.CONTRACT_LIQUIDITY,
    "ORDER_BLOCK": s4b2.CONTRACT_ORDER_BLOCK,
    "FVG": s4b2.CONTRACT_FVG,
    "DEALING_RANGE": s4b2.CONTRACT_DEALING_RANGE,
}
_CREATION_EVENT = {
    "LIQUIDITY": "LEVEL_CREATED",
    "ORDER_BLOCK": "ZONE_CREATED",
    "FVG": "FVG_CREATED",
}


def _fail(domain: str, detail: str) -> None:
    raise Stage4B2ConsistencyError(f"{domain} cross-table consistency: {detail}")


def _is_missing(value: Any) -> bool:
    try:
        missing = pd.isna(value)
        return bool(missing) if np.isscalar(missing) else False
    except (TypeError, ValueError):
        return False


def _same(left: Any, right: Any) -> bool:
    """Scalar equality that treats matching pandas missing sentinels as equal."""
    left_missing = _is_missing(left)
    right_missing = _is_missing(right)
    if left_missing or right_missing:
        return left_missing and right_missing
    try:
        result = left == right
        return bool(result) if np.isscalar(result) else False
    except (TypeError, ValueError):
        return False


def _same_or_fail(domain: str, left: Any, right: Any, detail: str) -> None:
    if not _same(left, right):
        _fail(domain, detail)


def _number(value: Any, domain: str, detail: str) -> float:
    if _is_missing(value) or isinstance(value, (bool, np.bool_)):
        _fail(domain, f"{detail} must be a finite number")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        _fail(domain, f"{detail} must be a finite number")
    if not math.isfinite(result):
        _fail(domain, f"{detail} must be a finite number")
    return result


def _integer(value: Any, domain: str, detail: str) -> int:
    number = _number(value, domain, detail)
    integer = int(number)
    if float(integer) != number:
        _fail(domain, f"{detail} must be an integer")
    return integer


def _position(value: Any, *, domain: str, detail: str, row_count: int) -> int:
    position = _integer(value, domain, detail)
    if position < 0 or position >= row_count:
        _fail(domain, f"{detail}={position} is outside the captured bar frame")
    return position


def _near(domain: str, actual: Any, expected: float, detail: str) -> None:
    actual_number = _number(actual, domain, detail)
    if not math.isclose(actual_number, expected, rel_tol=1e-12, abs_tol=1e-12):
        _fail(domain, f"{detail} does not match its source-bar derivation")


def _require_columns(frame: pd.DataFrame, columns: tuple[str, ...], domain: str, label: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        _fail(domain, f"{label} is missing source columns: {missing}")


def _bar_value(surface: Any, column: str, position: int, domain: str) -> Any:
    if column not in surface.bar_frame.columns:
        _fail(domain, f"bar_frame is missing required source column {column!r}")
    return surface.bar_frame[column].iloc[position]


def _row_position(row: dict[str, Any], column: str, *, domain: str, row_count: int) -> int:
    if column not in row:
        _fail(domain, f"row is missing availability/position column {column!r}")
    return _position(row[column], domain=domain, detail=column, row_count=row_count)


def _rows_and_unique_ids(
    frame: pd.DataFrame, id_column: str, *, domain: str, label: str
) -> tuple[list[dict[str, Any]], dict[int, dict[str, Any]]]:
    if id_column not in frame.columns:
        _fail(domain, f"{label} is missing ID column {id_column!r}")
    rows = frame.to_dict(orient="records")
    by_id: dict[int, dict[str, Any]] = {}
    for row in rows:
        identity = _integer(row[id_column], domain, f"{label}.{id_column}")
        if identity in by_id:
            _fail(domain, f"{label} contains duplicate {id_column}={identity}")
        by_id[identity] = row
    return rows, by_id


def _expected_normalized_tables(surface: Any, domain: str) -> None:
    event = surface.event_frame
    if domain == "DEALING_RANGE":
        expected_entity = event.loc[:, list(surface.normalized_entity_frame.columns)].copy(deep=True)
    else:
        creation_type = _CREATION_EVENT[domain]
        if "event_type" not in event.columns:
            _fail(domain, "event_frame is missing event_type")
        expected_entity = event.loc[
            event["event_type"] == creation_type,
            list(surface.normalized_entity_frame.columns),
        ].reset_index(drop=True)
    if not surface.normalized_entity_frame.equals(expected_entity):
        _fail(domain, "normalized entity rows are not the declared source-table projection")

    expected_event = event.copy(deep=True)
    if "event_position" in expected_event.columns:
        expected_event["same_information_batch_order_unknown"] = (
            expected_event["event_position"].duplicated(keep=False)
        )
    else:
        expected_event["same_information_batch_order_unknown"] = False
    if not surface.normalized_event_frame.equals(expected_event):
        _fail(domain, "normalized event rows or same-batch ambiguity flags disagree with event_frame")


def _check_reconstruction_binding(surface: Any, domain: str) -> None:
    payload = {
        "domain": domain,
        "contract_version": _CONTRACT_BY_DOMAIN[domain],
        "timeline_id": surface.timeline_id,
        "timeline_hash": surface.timeline_hash,
        "structure_surface_id": surface.structure_surface_id,
    }
    expected = canonical_sha256(
        domain="STAGE4B2_RECONSTRUCTION_INPUT_BINDING_V1",
        payload=payload,
    )
    if surface.reconstruction_input_hash != expected:
        _fail(domain, "reconstruction-input binding does not match its declared local inputs")


def _creation_bar_mirrors(
    surface: Any,
    *,
    rows: list[dict[str, Any]],
    id_column: str,
    position_column: str,
    flag_column: str,
    mirrors: tuple[tuple[str, str], ...],
    domain: str,
) -> dict[int, dict[str, Any]]:
    bar = surface.bar_frame
    row_count = len(bar)
    if row_count == 0:
        _fail(domain, "bar_frame must contain at least one row")
    _require_columns(bar, (flag_column,) + tuple(bar_column for _, bar_column in mirrors), domain, "bar_frame")
    expected_by_position: dict[int, dict[str, Any]] = {}
    for row in rows:
        position = _row_position(row, position_column, domain=domain, row_count=row_count)
        if position in expected_by_position:
            _fail(domain, f"multiple entities claim one creation row at position {position}")
        expected_by_position[position] = row

    actual_positions: set[int] = set()
    for position, value in enumerate(bar[flag_column].tolist()):
        if _is_missing(value) or not isinstance(value, (bool, np.bool_)):
            _fail(domain, f"{flag_column} must be non-missing boolean evidence")
        if bool(value):
            actual_positions.add(position)
    if actual_positions != set(expected_by_position):
        _fail(domain, f"{flag_column} rows do not mirror entity availability positions")
    id_bar_column = mirrors[0][1]
    for position in set(range(row_count)) - actual_positions:
        if not _is_missing(_bar_value(surface, id_bar_column, position, domain)):
            _fail(domain, f"{id_bar_column} is populated without a creation flag at position {position}")

    by_position: dict[int, dict[str, Any]] = {}
    for position, row in expected_by_position.items():
        for entity_column, bar_column in mirrors:
            _same_or_fail(
                domain,
                _bar_value(surface, bar_column, position, domain),
                row[entity_column],
                f"bar.{bar_column} differs from entity.{entity_column} at position {position}",
            )
        by_position[position] = row
    # Ensure each created ID is also a valid unique table ID, including the bar witness.
    for row in rows:
        position = _row_position(row, position_column, domain=domain, row_count=row_count)
        _same_or_fail(
            domain,
            _bar_value(surface, mirrors[0][1], position, domain),
            row[id_column],
            f"bar creation ID does not mirror {id_column} at position {position}",
        )
    return by_position


def _event_frame_common(
    surface: Any,
    *,
    domain: str,
    entity_by_id: dict[int, dict[str, Any]],
    id_column: str,
    event_id_column: str,
    event_position_column: str,
    availability_column: str,
    creation_event: str,
    allowed_events: frozenset[str],
    stable_columns: tuple[str, ...],
    ohlc_columns: tuple[tuple[str, str], ...],
) -> tuple[dict[int, dict[str, Any]], dict[int, dict[str, int]]]:
    row_count = len(surface.bar_frame)
    events_by_id: dict[int, dict[str, int]] = {identity: {} for identity in entity_by_id}
    creation_rows: dict[int, dict[str, Any]] = {}
    for event in surface.event_frame.to_dict(orient="records"):
        identity = _integer(event[event_id_column], domain, f"event.{event_id_column}")
        if identity not in entity_by_id:
            _fail(domain, f"lifecycle event references unknown {id_column}={identity}")
        event_type = event.get("event_type")
        if not isinstance(event_type, str) or event_type not in allowed_events:
            _fail(domain, f"unsupported lifecycle event type {event_type!r}")
        event_position = _position(
            event[event_position_column],
            domain=domain,
            detail=event_position_column,
            row_count=row_count,
        )
        availability = _position(
            entity_by_id[identity][availability_column],
            domain=domain,
            detail=availability_column,
            row_count=row_count,
        )
        if event_type == creation_event:
            if identity in creation_rows:
                _fail(domain, f"{id_column}={identity} has more than one creation event")
            if event_position != availability:
                _fail(domain, f"{id_column}={identity} creation event disagrees with availability")
            creation_rows[identity] = event
        elif event_position <= availability:
            _fail(domain, f"{id_column}={identity} lifecycle event is not after creation/availability")
        position_history = events_by_id[identity]
        if event_type in position_history:
            _fail(domain, f"{id_column}={identity} repeats lifecycle event {event_type}")
        position_history[event_type] = event_position

        entity = entity_by_id[identity]
        for column in stable_columns:
            _same_or_fail(
                domain,
                event[column],
                entity[column],
                f"{id_column}={identity} lifecycle attribute {column} changed",
            )
        age_column = {
            "LIQUIDITY": "level_age_bars",
            "ORDER_BLOCK": "zone_age_bars",
            "FVG": "fvg_age_bars",
        }[domain]
        if _integer(event[age_column], domain, age_column) != event_position - availability:
            _fail(domain, f"{id_column}={identity} lifecycle age disagrees with availability")

        for event_column, bar_column in ohlc_columns:
            source_value = _bar_value(surface, bar_column, event_position, domain)
            _number(source_value, domain, f"bar.{bar_column}[{event_position}]")
            _same_or_fail(
                domain,
                event[event_column],
                source_value,
                f"event.{event_column} disagrees with bar.{bar_column} at position {event_position}",
            )

    if set(creation_rows) != set(entity_by_id):
        _fail(domain, "entity IDs and creation-event IDs do not match exactly")
    return creation_rows, events_by_id


def _check_liquidity(surface: Any) -> tuple[str, ...]:
    domain = "LIQUIDITY"
    bar = surface.bar_frame
    _require_columns(
        bar,
        (
            "open", "high", "low", "close", "swing_high_confirmed", "swing_low_confirmed",
            "swing_origin_position", "swing_confirmation_position", "swing_price",
            "swing_sequence_class",
        ),
        domain,
        "bar_frame",
    )
    rows, entity_by_id = _rows_and_unique_ids(
        surface.normalized_entity_frame, "level_id", domain=domain, label="entity_frame"
    )
    by_creation_position = _creation_bar_mirrors(
        surface,
        rows=rows,
        id_column="level_id",
        position_column="source_confirmation_position",
        flag_column="liquidity_level_created",
        mirrors=(
            ("level_id", "created_level_id"),
            ("side", "created_level_side"),
            ("immutable_level_price", "created_level_price"),
            ("source_origin_position", "created_level_origin_position"),
            ("source_confirmation_position", "created_level_confirmation_position"),
            ("source_class", "created_level_source_class"),
        ),
        domain=domain,
    )
    for identity, row in entity_by_id.items():
        position = _row_position(row, "source_confirmation_position", domain=domain, row_count=len(bar))
        origin = _position(row["source_origin_position"], domain=domain, detail="source_origin_position", row_count=len(bar))
        if origin > position:
            _fail(domain, f"level_id={identity} origin follows confirmation")
        side = row["side"]
        expected_high = side == "HIGH_SIDE"
        expected_low = side == "LOW_SIDE"
        if not (expected_high or expected_low):
            _fail(domain, f"level_id={identity} has unsupported side {side!r}")
        _same_or_fail(domain, _bar_value(surface, "swing_confirmation_position", position, domain), position,
                      f"level_id={identity} source confirmation-position witness disagrees")
        _same_or_fail(domain, _bar_value(surface, "swing_origin_position", position, domain), origin,
                      f"level_id={identity} source origin-position witness disagrees")
        _same_or_fail(domain, _bar_value(surface, "swing_price", position, domain), row["immutable_level_price"],
                      f"level_id={identity} source swing price disagrees")
        _same_or_fail(domain, _bar_value(surface, "swing_sequence_class", position, domain), row["source_class"],
                      f"level_id={identity} source swing class disagrees")
        high_flag = _bar_value(surface, "swing_high_confirmed", position, domain)
        low_flag = _bar_value(surface, "swing_low_confirmed", position, domain)
        if not isinstance(high_flag, (bool, np.bool_)) or not isinstance(low_flag, (bool, np.bool_)):
            _fail(domain, f"level_id={identity} source swing flags must be booleans")
        if bool(high_flag) != expected_high or bool(low_flag) != expected_low:
            _fail(domain, f"level_id={identity} side disagrees with source swing flags")
        _number(row["immutable_level_price"], domain, f"level_id={identity}.immutable_level_price")

    stable = (
        "side", "source_origin_position", "source_confirmation_position", "source_class",
        "immutable_level_price",
    )
    creation_rows, event_positions = _event_frame_common(
        surface,
        domain=domain,
        entity_by_id=entity_by_id,
        id_column="level_id",
        event_id_column="level_id",
        event_position_column="event_position",
        availability_column="source_confirmation_position",
        creation_event="LEVEL_CREATED",
        allowed_events=frozenset({
            "LEVEL_CREATED", "FIRST_TOUCH", "FIRST_WICK_BREACH", "FIRST_WICK_ONLY_EXCURSION",
            "FIRST_CLOSE_BREACH", "FIRST_RECLAIM_AFTER_CLOSE_BREACH",
        }),
        stable_columns=stable,
        ohlc_columns=(("event_close", "close"),),
    )
    for event in surface.event_frame.to_dict(orient="records"):
        position = _position(event["event_position"], domain=domain, detail="event_position", row_count=len(bar))
        event_type = event["event_type"]
        if event_type == "LEVEL_CREATED":
            for event_column, bar_column in (
                ("nearest_prior_same_side_level_id", "nearest_prior_same_side_level_id"),
                ("nearest_same_side_distance_fraction", "nearest_same_side_distance_fraction"),
                ("nearest_distance_percentile", "nearest_distance_percentile"),
                ("nearest_distance_reference_history_count", "nearest_distance_reference_history_count"),
            ):
                _same_or_fail(
                    domain,
                    event[event_column],
                    _bar_value(surface, bar_column, position, domain),
                    f"creation event.{event_column} disagrees with bar.{bar_column} at position {position}",
                )
            source_column = "swing_price"
        elif event_type in {"FIRST_TOUCH", "FIRST_WICK_BREACH", "FIRST_WICK_ONLY_EXCURSION"}:
            source_column = "high" if event["side"] == "HIGH_SIDE" else "low"
        else:
            source_column = "close"
        _same_or_fail(
            domain,
            event["event_price"],
            _bar_value(surface, source_column, position, domain),
            f"event.event_price disagrees with bar.{source_column} at position {position}",
        )
    for identity, history in event_positions.items():
        close = history.get("FIRST_CLOSE_BREACH")
        reclaim = history.get("FIRST_RECLAIM_AFTER_CLOSE_BREACH")
        wick_only = history.get("FIRST_WICK_ONLY_EXCURSION")
        if reclaim is not None and (close is None or reclaim <= close):
            _fail(domain, f"level_id={identity} reclaim lacks a preceding close breach")
        if close is not None and wick_only is not None and wick_only >= close:
            _fail(domain, f"level_id={identity} wick-only event is not before close breach")
        created = creation_rows[identity]
        prior_id = created.get("nearest_prior_same_side_level_id")
        if not _is_missing(prior_id):
            prior = entity_by_id.get(_integer(prior_id, domain, "nearest_prior_same_side_level_id"))
            if prior is None:
                _fail(domain, f"level_id={identity} nearest-prior reference is unknown")
            if prior["side"] != entity_by_id[identity]["side"]:
                _fail(domain, f"level_id={identity} nearest-prior reference changes side")
            if _integer(prior["source_confirmation_position"], domain, "prior confirmation") >= _integer(
                entity_by_id[identity]["source_confirmation_position"], domain, "level confirmation"
            ):
                _fail(domain, f"level_id={identity} nearest-prior reference is not prior")
    return (
        "entity_projection", "unique_ids", "creation_bar_mirrors", "swing_source_witnesses",
        "lifecycle_references", "stable_lifecycle_attributes", "event_bar_ohlc", "event_price_bar_witnesses",
        "availability_and_age",
    )


def _check_order_block(surface: Any) -> tuple[str, ...]:
    domain = "ORDER_BLOCK"
    bar = surface.bar_frame
    _require_columns(
        bar,
        (
            "open", "high", "low", "close", "structural_break_event",
            "swing_high_confirmed", "swing_low_confirmed", "swing_origin_position",
        ),
        domain,
        "bar_frame",
    )
    rows, entity_by_id = _rows_and_unique_ids(
        surface.normalized_entity_frame, "zone_id", domain=domain, label="entity_frame"
    )
    _creation_bar_mirrors(
        surface,
        rows=rows,
        id_column="zone_id",
        position_column="creation_position",
        flag_column="ob_candidate_created",
        mirrors=(
            ("zone_id", "created_ob_zone_id"), ("direction", "created_ob_direction"),
            ("origin_position", "created_ob_origin_position"),
            ("creation_position", "created_ob_creation_position"),
            ("full_zone_low", "created_ob_full_zone_low"),
            ("full_zone_high", "created_ob_full_zone_high"),
            ("body_low", "created_ob_body_low"), ("body_high", "created_ob_body_high"),
            ("source_break_event", "created_ob_source_break_event"),
            ("origin_prior_use_count", "created_ob_origin_prior_use_count"),
            ("displacement_fraction", "created_ob_displacement_fraction"),
            ("displacement_percentile", "created_ob_displacement_percentile"),
            ("displacement_history_count", "created_ob_displacement_history_count"),
            ("search_boundary_position", "created_ob_search_boundary_position"),
        ),
        domain=domain,
    )
    for identity, row in entity_by_id.items():
        creation = _row_position(row, "creation_position", domain=domain, row_count=len(bar))
        origin = _position(row["origin_position"], domain=domain, detail="origin_position", row_count=len(bar))
        boundary = _position(row["search_boundary_position"], domain=domain, detail="search_boundary_position", row_count=len(bar))
        if not boundary <= origin < creation:
            _fail(domain, f"zone_id={identity} origin/boundary/creation order is invalid")
        source = row["source_break_event"]
        expected_direction = {
            "BOS_UP": "BULLISH_OB_CANDIDATE", "CHOCH_UP": "BULLISH_OB_CANDIDATE",
            "BOS_DOWN": "BEARISH_OB_CANDIDATE", "CHOCH_DOWN": "BEARISH_OB_CANDIDATE",
        }.get(source)
        if expected_direction is None or row["direction"] != expected_direction:
            _fail(domain, f"zone_id={identity} direction disagrees with source break event")
        _same_or_fail(domain, _bar_value(surface, "structural_break_event", creation, domain), source,
                      f"zone_id={identity} source break event disagrees with creation bar")
        origin_open = _number(_bar_value(surface, "open", origin, domain), domain, f"origin open for zone {identity}")
        origin_close = _number(_bar_value(surface, "close", origin, domain), domain, f"origin close for zone {identity}")
        origin_high = _number(_bar_value(surface, "high", origin, domain), domain, f"origin high for zone {identity}")
        origin_low = _number(_bar_value(surface, "low", origin, domain), domain, f"origin low for zone {identity}")
        _same_or_fail(domain, row["full_zone_low"], origin_low, f"zone_id={identity} full-zone low differs from origin bar")
        _same_or_fail(domain, row["full_zone_high"], origin_high, f"zone_id={identity} full-zone high differs from origin bar")
        _same_or_fail(domain, row["body_low"], min(origin_open, origin_close), f"zone_id={identity} body low differs from origin bar")
        _same_or_fail(domain, row["body_high"], max(origin_open, origin_close), f"zone_id={identity} body high differs from origin bar")
        if not origin_low <= _number(row["full_zone_low"], domain, "full_zone_low") <= _number(row["full_zone_high"], domain, "full_zone_high") <= origin_high:
            _fail(domain, f"zone_id={identity} zone bounds are invalid")

    _event_frame_common(
        surface,
        domain=domain,
        entity_by_id=entity_by_id,
        id_column="zone_id",
        event_id_column="zone_id",
        event_position_column="event_position",
        availability_column="creation_position",
        creation_event="ZONE_CREATED",
        allowed_events=frozenset({
            "ZONE_CREATED", "FIRST_TOUCH", "FIRST_FAR_SIDE_WICK_BREACH",
            "FIRST_FAR_SIDE_CLOSE_BREACH", "FIRST_CLOSE_RECLAIM_OF_FAR_SIDE",
        }),
        stable_columns=tuple(column for column in surface.normalized_entity_frame.columns if column != "zone_id"),
        ohlc_columns=(("event_high", "high"), ("event_low", "low"), ("event_close", "close")),
    )
    events_by_id: dict[int, dict[str, int]] = {}
    for event in surface.event_frame.to_dict(orient="records"):
        identity = _integer(event["zone_id"], domain, "event.zone_id")
        event_type = event["event_type"]
        position = _integer(event["event_position"], domain, "event_position")
        events_by_id.setdefault(identity, {})[event_type] = position
    for identity, history in events_by_id.items():
        close = history.get("FIRST_FAR_SIDE_CLOSE_BREACH")
        reclaim = history.get("FIRST_CLOSE_RECLAIM_OF_FAR_SIDE")
        if reclaim is not None and (close is None or reclaim <= close):
            _fail(domain, f"zone_id={identity} reclaim lacks a preceding close breach")
    return (
        "entity_projection", "unique_ids", "creation_bar_mirrors", "source_break_and_positions",
        "origin_ohlc_bounds", "lifecycle_references", "stable_lifecycle_attributes", "event_bar_ohlc",
    )


def _check_fvg(surface: Any) -> tuple[str, ...]:
    domain = "FVG"
    bar = surface.bar_frame
    _require_columns(bar, ("open", "high", "low", "close"), domain, "bar_frame")
    rows, entity_by_id = _rows_and_unique_ids(
        surface.normalized_entity_frame, "fvg_id", domain=domain, label="entity_frame"
    )
    _creation_bar_mirrors(
        surface,
        rows=rows,
        id_column="fvg_id",
        position_column="creation_position",
        flag_column="fvg_candidate_created",
        mirrors=(
            ("fvg_id", "created_fvg_id"), ("direction", "created_fvg_direction"),
            ("origin_position", "created_fvg_origin_position"),
            ("middle_position", "created_fvg_middle_position"),
            ("creation_position", "created_fvg_creation_position"),
            ("zone_low", "created_fvg_zone_low"), ("zone_high", "created_fvg_zone_high"),
            ("midpoint", "created_fvg_midpoint"), ("gap_width", "created_fvg_gap_width"),
            ("gap_width_fraction", "created_fvg_gap_width_fraction"),
            ("gap_width_percentile", "created_fvg_gap_width_percentile"),
            ("gap_width_history_count", "created_fvg_gap_width_history_count"),
            ("middle_body_fraction", "created_fvg_middle_body_fraction"),
            ("middle_signed_body_fraction", "created_fvg_middle_signed_body_fraction"),
        ),
        domain=domain,
    )
    for identity, row in entity_by_id.items():
        creation = _row_position(row, "creation_position", domain=domain, row_count=len(bar))
        origin = _position(row["origin_position"], domain=domain, detail="origin_position", row_count=len(bar))
        middle = _position(row["middle_position"], domain=domain, detail="middle_position", row_count=len(bar))
        if not origin < middle < creation or creation - origin != 2 or middle != origin + 1:
            _fail(domain, f"fvg_id={identity} source-bar positions are invalid")
        source_high_before = _number(_bar_value(surface, "high", origin, domain), domain, "FVG origin high")
        source_low_before = _number(_bar_value(surface, "low", origin, domain), domain, "FVG origin low")
        source_high_after = _number(_bar_value(surface, "high", creation, domain), domain, "FVG creation high")
        source_low_after = _number(_bar_value(surface, "low", creation, domain), domain, "FVG creation low")
        if row["direction"] == "BULLISH_FVG_CANDIDATE":
            if not source_low_after > source_high_before:
                _fail(domain, f"fvg_id={identity} bullish source bars do not contain a gap")
            expected_low, expected_high = source_high_before, source_low_after
        elif row["direction"] == "BEARISH_FVG_CANDIDATE":
            if not source_high_after < source_low_before:
                _fail(domain, f"fvg_id={identity} bearish source bars do not contain a gap")
            expected_low, expected_high = source_high_after, source_low_before
        else:
            _fail(domain, f"fvg_id={identity} has unsupported direction {row['direction']!r}")
        _same_or_fail(domain, row["zone_low"], expected_low, f"fvg_id={identity} zone_low disagrees with source bars")
        _same_or_fail(domain, row["zone_high"], expected_high, f"fvg_id={identity} zone_high disagrees with source bars")
        width = expected_high - expected_low
        if not math.isfinite(width) or width <= 0:
            _fail(domain, f"fvg_id={identity} source gap width is invalid")
        _near(domain, row["gap_width"], width, f"fvg_id={identity}.gap_width")
        _near(domain, row["midpoint"], expected_low + width / 2.0, f"fvg_id={identity}.midpoint")
        denominator = max(abs(expected_low), abs(expected_high))
        if denominator > 0:
            _near(domain, row["gap_width_fraction"], width / denominator, f"fvg_id={identity}.gap_width_fraction")
        else:
            if not _is_missing(row["gap_width_fraction"]):
                _fail(domain, f"fvg_id={identity} zero-denominator width fraction must be missing")
        middle_open = _number(_bar_value(surface, "open", middle, domain), domain, "FVG middle open")
        middle_close = _number(_bar_value(surface, "close", middle, domain), domain, "FVG middle close")
        middle_high = _number(_bar_value(surface, "high", middle, domain), domain, "FVG middle high")
        middle_low = _number(_bar_value(surface, "low", middle, domain), domain, "FVG middle low")
        middle_range = middle_high - middle_low
        if middle_range < 0:
            _fail(domain, f"fvg_id={identity} middle source-bar range is invalid")
        if middle_range == 0:
            if not _is_missing(row["middle_body_fraction"]) or not _is_missing(row["middle_signed_body_fraction"]):
                _fail(domain, f"fvg_id={identity} zero-range body fractions must be missing")
        else:
            _near(domain, row["middle_body_fraction"], abs(middle_close - middle_open) / middle_range,
                  f"fvg_id={identity}.middle_body_fraction")
            _near(domain, row["middle_signed_body_fraction"], (middle_close - middle_open) / middle_range,
                  f"fvg_id={identity}.middle_signed_body_fraction")

    _event_frame_common(
        surface,
        domain=domain,
        entity_by_id=entity_by_id,
        id_column="fvg_id",
        event_id_column="fvg_id",
        event_position_column="event_position",
        availability_column="creation_position",
        creation_event="FVG_CREATED",
        allowed_events=frozenset({
            "FVG_CREATED", "FIRST_TOUCH", "FIRST_FULL_RANGE_COVERAGE",
            "FIRST_FAR_SIDE_WICK_BREACH", "FIRST_FAR_SIDE_CLOSE_BREACH",
            "FIRST_CLOSE_RECLAIM_OF_FAR_SIDE",
        }),
        stable_columns=tuple(column for column in surface.normalized_entity_frame.columns if column != "fvg_id"),
        ohlc_columns=(("event_high", "high"), ("event_low", "low"), ("event_close", "close")),
    )
    events_by_id: dict[int, dict[str, int]] = {}
    for event in surface.event_frame.to_dict(orient="records"):
        identity = _integer(event["fvg_id"], domain, "event.fvg_id")
        event_type = event["event_type"]
        position = _integer(event["event_position"], domain, "event_position")
        events_by_id.setdefault(identity, {})[event_type] = position
    for identity, history in events_by_id.items():
        close = history.get("FIRST_FAR_SIDE_CLOSE_BREACH")
        reclaim = history.get("FIRST_CLOSE_RECLAIM_OF_FAR_SIDE")
        if reclaim is not None and (close is None or reclaim <= close):
            _fail(domain, f"fvg_id={identity} reclaim lacks a preceding close breach")
    return (
        "entity_projection", "unique_ids", "creation_bar_mirrors", "source_bar_fvg_geometry",
        "lifecycle_references", "stable_lifecycle_attributes", "event_bar_ohlc", "availability_and_age",
    )


def _check_source_swing(
    surface: Any,
    *,
    domain: str,
    position: int,
    origin: Any,
    price: Any,
    source_class: Any,
    side: str,
) -> None:
    expected_high = side in {"HIGH", "HIGH_SIDE"}
    expected_low = side in {"LOW", "LOW_SIDE"}
    if not (expected_high or expected_low):
        _fail(domain, f"unsupported endpoint/swing side {side!r}")
    flags = (
        _bar_value(surface, "swing_high_confirmed", position, domain),
        _bar_value(surface, "swing_low_confirmed", position, domain),
    )
    if any(not isinstance(value, (bool, np.bool_)) for value in flags):
        _fail(domain, f"source swing flags at {position} must be booleans")
    if bool(flags[0]) != expected_high or bool(flags[1]) != expected_low:
        _fail(domain, f"endpoint side at {position} disagrees with source swing flags")
    _same_or_fail(domain, _bar_value(surface, "swing_confirmation_position", position, domain), position,
                  f"source swing confirmation position at {position} disagrees")
    _same_or_fail(domain, _bar_value(surface, "swing_origin_position", position, domain), origin,
                  f"source swing origin at {position} disagrees")
    _same_or_fail(domain, _bar_value(surface, "swing_price", position, domain), price,
                  f"source swing price at {position} disagrees")
    _same_or_fail(domain, _bar_value(surface, "swing_sequence_class", position, domain), source_class,
                  f"source swing class at {position} disagrees")


def _check_dealing_range(surface: Any) -> tuple[str, ...]:
    domain = "DEALING_RANGE"
    bar = surface.bar_frame
    _require_columns(
        bar,
        (
            "open", "high", "low", "close", "swing_high_confirmed", "swing_low_confirmed",
            "swing_origin_position", "swing_confirmation_position", "swing_price", "swing_sequence_class",
        ),
        domain,
        "bar_frame",
    )
    rows, range_by_id = _rows_and_unique_ids(
        surface.normalized_entity_frame, "range_id", domain=domain, label="range_table"
    )
    by_creation_position = _creation_bar_mirrors(
        surface,
        rows=rows,
        id_column="range_id",
        position_column="creation_position",
        flag_column="dealing_range_created",
        mirrors=(
            ("range_id", "created_range_id"), ("creation_position", "created_range_creation_position"),
            ("direction", "created_range_direction"), ("range_low", "created_range_low"),
            ("range_high", "created_range_high"), ("range_width", "created_range_width"),
            ("midpoint", "created_range_midpoint"),
            ("first_endpoint_side", "created_range_first_endpoint_side"),
            ("first_endpoint_origin_position", "created_range_first_endpoint_origin_position"),
            ("first_endpoint_confirmation_position", "created_range_first_endpoint_confirmation_position"),
            ("first_endpoint_price", "created_range_first_endpoint_price"),
            ("first_endpoint_class", "created_range_first_endpoint_class"),
            ("second_endpoint_side", "created_range_second_endpoint_side"),
            ("second_endpoint_origin_position", "created_range_second_endpoint_origin_position"),
            ("second_endpoint_confirmation_position", "created_range_second_endpoint_confirmation_position"),
            ("second_endpoint_price", "created_range_second_endpoint_price"),
            ("second_endpoint_class", "created_range_second_endpoint_class"),
        ),
        domain=domain,
    )
    ordered_ranges = sorted(rows, key=lambda row: _integer(row["creation_position"], domain, "creation_position"))
    previous_creation = -1
    for identity, row in range_by_id.items():
        creation = _row_position(row, "creation_position", domain=domain, row_count=len(bar))
        if creation <= previous_creation:
            _fail(domain, "range creation positions are not strictly increasing")
        previous_creation = creation
        first_confirmation = _position(
            row["first_endpoint_confirmation_position"], domain=domain,
            detail="first_endpoint_confirmation_position", row_count=len(bar),
        )
        second_confirmation = _position(
            row["second_endpoint_confirmation_position"], domain=domain,
            detail="second_endpoint_confirmation_position", row_count=len(bar),
        )
        first_origin = _position(row["first_endpoint_origin_position"], domain=domain,
                                 detail="first_endpoint_origin_position", row_count=len(bar))
        second_origin = _position(row["second_endpoint_origin_position"], domain=domain,
                                  detail="second_endpoint_origin_position", row_count=len(bar))
        if not first_origin <= first_confirmation < second_confirmation == creation:
            _fail(domain, f"range_id={identity} endpoint availability/position ordering is invalid")
        first_side, second_side = row["first_endpoint_side"], row["second_endpoint_side"]
        if first_side == second_side or {first_side, second_side} != {"HIGH", "LOW"}:
            _fail(domain, f"range_id={identity} endpoints are not opposite swing sides")
        _check_source_swing(
            surface, domain=domain, position=first_confirmation, origin=first_origin,
            price=row["first_endpoint_price"], source_class=row["first_endpoint_class"], side=first_side,
        )
        _check_source_swing(
            surface, domain=domain, position=second_confirmation, origin=second_origin,
            price=row["second_endpoint_price"], source_class=row["second_endpoint_class"], side=second_side,
        )
        first_price = _number(row["first_endpoint_price"], domain, f"range_id={identity}.first_endpoint_price")
        second_price = _number(row["second_endpoint_price"], domain, f"range_id={identity}.second_endpoint_price")
        expected_low, expected_high = min(first_price, second_price), max(first_price, second_price)
        _same_or_fail(domain, row["range_low"], expected_low, f"range_id={identity} low differs from endpoints")
        _same_or_fail(domain, row["range_high"], expected_high, f"range_id={identity} high differs from endpoints")
        width = expected_high - expected_low
        if not math.isfinite(width) or width <= 0:
            _fail(domain, f"range_id={identity} endpoint geometry has nonpositive width")
        _near(domain, row["range_width"], width, f"range_id={identity}.range_width")
        _near(domain, row["midpoint"], expected_low + width / 2.0, f"range_id={identity}.midpoint")
        expected_direction = (
            "ASCENDING_DEALING_RANGE_CANDIDATE" if first_side == "LOW"
            else "DESCENDING_DEALING_RANGE_CANDIDATE"
        )
        if row["direction"] != expected_direction:
            _fail(domain, f"range_id={identity} direction disagrees with first endpoint")

    # Dealing Range has a range table, not lifecycle events. Check that its
    # public current-range bar witness always points to the latest available row.
    current_columns = (
        "current_range_id", "current_range_direction", "current_range_creation_position",
        "current_range_low", "current_range_high", "current_range_width", "current_range_midpoint",
        "current_range_position_raw", "current_midpoint_displacement",
        "current_discount_depth", "current_premium_depth",
    )
    _require_columns(bar, current_columns, domain, "bar_frame")
    latest: dict[str, Any] | None = None
    range_rows_by_position = {
        _integer(row["creation_position"], domain, "creation_position"): row for row in ordered_ranges
    }
    for position in range(len(bar)):
        if position in range_rows_by_position:
            latest = range_rows_by_position[position]
        current_id = _bar_value(surface, "current_range_id", position, domain)
        if latest is None:
            if not _is_missing(current_id):
                _fail(domain, f"current range is available before any range creation at {position}")
            continue
        identity = _integer(latest["range_id"], domain, "latest range_id")
        _same_or_fail(domain, current_id, identity, f"current range ID is not latest at {position}")
        mirrors = (
            ("current_range_direction", "direction"),
            ("current_range_creation_position", "creation_position"),
            ("current_range_low", "range_low"), ("current_range_high", "range_high"),
            ("current_range_width", "range_width"), ("current_range_midpoint", "midpoint"),
        )
        for bar_column, range_column in mirrors:
            _same_or_fail(
                domain, _bar_value(surface, bar_column, position, domain), latest[range_column],
                f"{bar_column} disagrees with latest range at position {position}",
            )
        close = _number(_bar_value(surface, "close", position, domain), domain, f"close[{position}]")
        low = _number(latest["range_low"], domain, "current range low")
        width = _number(latest["range_width"], domain, "current range width")
        raw_position = (close - low) / width
        displacement = 2.0 * raw_position - 1.0
        _near(domain, _bar_value(surface, "current_range_position_raw", position, domain), raw_position,
              f"current_range_position_raw[{position}]")
        _near(domain, _bar_value(surface, "current_midpoint_displacement", position, domain), displacement,
              f"current_midpoint_displacement[{position}]")
        _near(domain, _bar_value(surface, "current_discount_depth", position, domain), max(-displacement, 0.0),
              f"current_discount_depth[{position}]")
        _near(domain, _bar_value(surface, "current_premium_depth", position, domain), max(displacement, 0.0),
              f"current_premium_depth[{position}]")
    return (
        "range_table_projection", "unique_ids", "creation_bar_mirrors", "endpoint_swing_witnesses",
        "endpoint_availability_and_geometry", "current_range_bar_witnesses",
    )


def verify_stage4b2_consistency(surface_snapshot: Any) -> Stage4B2ConsistencyResult:
    """Verify one privately captured public Stage4B2 snapshot; never call producers.

    Consumers must first capture the surface using their existing trusted-local
    snapshot path. This function runs Stage4B2's existing integrity verifier,
    then independent consistency checks, and returns a local-only verification
    label only after every check has passed.
    """
    surface_class = next(
        (candidate for candidate in _DOMAIN_BY_CLASS if isinstance(surface_snapshot, candidate)),
        None,
    )
    if surface_class is None:
        raise Stage4B2ConsistencyError(
            f"unsupported Stage4B2 surface type: {type(surface_snapshot).__name__}"
        )
    domain = _DOMAIN_BY_CLASS[surface_class]
    try:
        s4b2.verify_surface_integrity(surface_snapshot)
    except Exception as exc:
        raise Stage4B2ConsistencyError(f"{domain} existing integrity check failed: {exc}") from exc

    try:
        _check_reconstruction_binding(surface_snapshot, domain)
        _expected_normalized_tables(surface_snapshot, domain)
        if domain == "LIQUIDITY":
            checks = _check_liquidity(surface_snapshot)
        elif domain == "ORDER_BLOCK":
            checks = _check_order_block(surface_snapshot)
        elif domain == "FVG":
            checks = _check_fvg(surface_snapshot)
        else:
            checks = _check_dealing_range(surface_snapshot)
    except Stage4B2ConsistencyError:
        raise
    except Exception as exc:
        raise Stage4B2ConsistencyError(
            f"{domain} consistency check failed closed: {type(exc).__name__}: {exc}"
        ) from exc
    return Stage4B2ConsistencyResult(
        domain=domain,
        surface_id=surface_snapshot.surface_id,
        verification_scope=LOCAL_VERIFICATION_SCOPE,
        checks=("existing_surface_integrity", "reconstruction_input_binding") + checks,
    )
