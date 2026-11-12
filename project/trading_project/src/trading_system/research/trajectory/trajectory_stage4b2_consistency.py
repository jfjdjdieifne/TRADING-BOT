"""Independent local cross-table checks for captured Stage4B2 surfaces.

This validator consumes an already privately captured public surface snapshot.
It does not replay any producer and does not authenticate producer code, market
sources, or market semantics. A returned LOCAL_VERIFIED_PRODUCER_SURFACE label
means only that this exact local snapshot passed Stage4B2's existing integrity
check and the cross-table/source-witness checks below.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import math
from typing import Any, Iterable

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

# Exact market columns consumed by each CLOSED Stage4B2 producer contract.
_MARKET_SOURCE_COLUMNS_BY_DOMAIN = {
    "LIQUIDITY": ("high", "low", "close"),
    "ORDER_BLOCK": ("open", "high", "low", "close"),
    "FVG": ("open", "high", "low", "close"),
    "DEALING_RANGE": ("close",),
}

# Producer-initialized absence values for fields populated only on a creation
# row. None means a pandas missing value (nullable integer or NaN float); string
# sentinels and zero-valued integer counters remain literal producer defaults.
_CREATION_ABSENCE_DEFAULTS = {
    "LIQUIDITY": {
        "created_level_id": None,
        "created_level_side": "NONE",
        "created_level_price": None,
        "created_level_origin_position": None,
        "created_level_confirmation_position": None,
        "created_level_source_class": "NONE",
        "nearest_prior_same_side_level_id": None,
        "nearest_same_side_distance_fraction": None,
        "nearest_distance_percentile": None,
        "nearest_distance_reference_history_count": 0,
    },
    "ORDER_BLOCK": {
        "created_ob_zone_id": None,
        "created_ob_direction": "NONE",
        "created_ob_origin_position": None,
        "created_ob_creation_position": None,
        "created_ob_full_zone_low": None,
        "created_ob_full_zone_high": None,
        "created_ob_body_low": None,
        "created_ob_body_high": None,
        "created_ob_source_break_event": "NONE",
        "created_ob_origin_prior_use_count": 0,
        "created_ob_displacement_fraction": None,
        "created_ob_displacement_percentile": None,
        "created_ob_displacement_history_count": 0,
        "created_ob_search_boundary_position": None,
        "created_ob_opposite_candle_count_in_leg": 0,
    },
    "FVG": {
        "created_fvg_id": None,
        "created_fvg_direction": "NONE",
        "created_fvg_origin_position": None,
        "created_fvg_middle_position": None,
        "created_fvg_creation_position": None,
        "created_fvg_zone_low": None,
        "created_fvg_zone_high": None,
        "created_fvg_midpoint": None,
        "created_fvg_gap_width": None,
        "created_fvg_gap_width_fraction": None,
        "created_fvg_gap_width_percentile": None,
        "created_fvg_gap_width_history_count": 0,
        "created_fvg_middle_body_fraction": None,
        "created_fvg_middle_signed_body_fraction": None,
    },
    "DEALING_RANGE": {
        "created_range_id": None,
        "created_range_direction": "NONE",
        "created_range_creation_position": None,
        "created_range_low": None,
        "created_range_high": None,
        "created_range_width": None,
        "created_range_midpoint": None,
        "created_range_first_endpoint_side": "NONE",
        "created_range_first_endpoint_origin_position": None,
        "created_range_first_endpoint_confirmation_position": None,
        "created_range_first_endpoint_price": None,
        "created_range_first_endpoint_class": "NONE",
        "created_range_second_endpoint_side": "NONE",
        "created_range_second_endpoint_origin_position": None,
        "created_range_second_endpoint_confirmation_position": None,
        "created_range_second_endpoint_price": None,
        "created_range_second_endpoint_class": "NONE",
    },
}

_LIQUIDITY_EVENT_COUNT_COLUMNS = {
    ("HIGH_SIDE", "FIRST_TOUCH"): "high_side_first_touch_count",
    ("LOW_SIDE", "FIRST_TOUCH"): "low_side_first_touch_count",
    ("HIGH_SIDE", "FIRST_WICK_BREACH"): "high_side_first_wick_breach_count",
    ("LOW_SIDE", "FIRST_WICK_BREACH"): "low_side_first_wick_breach_count",
    ("HIGH_SIDE", "FIRST_WICK_ONLY_EXCURSION"): "high_side_first_wick_only_count",
    ("LOW_SIDE", "FIRST_WICK_ONLY_EXCURSION"): "low_side_first_wick_only_count",
    ("HIGH_SIDE", "FIRST_CLOSE_BREACH"): "high_side_first_close_breach_count",
    ("LOW_SIDE", "FIRST_CLOSE_BREACH"): "low_side_first_close_breach_count",
    ("HIGH_SIDE", "FIRST_RECLAIM_AFTER_CLOSE_BREACH"): "high_side_first_reclaim_count",
    ("LOW_SIDE", "FIRST_RECLAIM_AFTER_CLOSE_BREACH"): "low_side_first_reclaim_count",
}


def required_stage4b2_market_source_columns(domain: str) -> tuple[str, ...]:
    """Return the exact captured-market columns consumed by one producer domain."""
    try:
        return _MARKET_SOURCE_COLUMNS_BY_DOMAIN[domain]
    except (KeyError, TypeError) as exc:
        raise Stage4B2ConsistencyError(f"unsupported Stage4B2 market-source domain: {domain!r}") from exc


def _fail(domain: str, detail: str) -> None:
    raise Stage4B2ConsistencyError(f"{domain} cross-table consistency: {detail}")


def _source_index_token(value: Any) -> dict[str, Any]:
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, pd.Timestamp):
        return {"type": "timestamp", "value": value.isoformat()}
    if isinstance(value, pd.Timedelta):
        return {"type": "timedelta_ns", "value": int(value.value)}
    if isinstance(value, bool):
        return {"type": "bool", "value": value}
    if isinstance(value, int):
        return {"type": "int", "value": value}
    if isinstance(value, float):
        return {"type": "float_hex", "value": value.hex()}
    if isinstance(value, str):
        return {"type": "str", "value": value}
    return {"type": type(value).__qualname__, "value": str(value)}


def _source_number_token(value: Any, *, domain: str, column: str, position: int) -> dict[str, str]:
    if isinstance(value, np.generic):
        value = value.item()
    if _is_missing(value) or isinstance(value, bool):
        _fail(domain, f"market source {column}[{position}] must be a finite numeric observation")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise Stage4B2ConsistencyError(
            f"{domain} cross-table consistency: market source {column}[{position}] is not numeric"
        ) from exc
    if not number.is_finite():
        _fail(domain, f"market source {column}[{position}] must be finite")
    if number == 0:
        try:
            negative = math.copysign(1.0, float(value)) < 0.0
        except (TypeError, ValueError, OverflowError):
            negative = str(value).startswith("-")
        literal = "-0" if negative else "0"
    else:
        literal = format(number.normalize(), "f")
    return {"state": "NUMBER", "value": literal}


def _source_column_row_hashes(
    frame: pd.DataFrame, column: str, *, domain: str
) -> tuple[str, ...]:
    if not isinstance(frame, pd.DataFrame) or frame.columns.has_duplicates or column not in frame.columns:
        _fail(domain, f"required market source column {column!r} is unavailable")
    hashes = []
    for position, (index_value, value) in enumerate(zip(frame.index.tolist(), frame[column].tolist())):
        hashes.append(
            canonical_sha256(
                domain="STAGE4B2_MARKET_SOURCE_COLUMN_ROW_V1",
                payload={
                    "bar_position": position,
                    "index": _source_index_token(index_value),
                    "column": column,
                    "value": _source_number_token(
                        value, domain=domain, column=column, position=position
                    ),
                },
            )
        )
    return tuple(hashes)


def capture_stage4b2_market_source_column_hashes(
    market_history: pd.DataFrame, surfaces: Iterable[object]
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Capture local row hashes of only the source columns used by supplied B2 surfaces.

    This is provenance evidence for later as-of consumers, not a signature,
    producer authentication, or market-feed authenticity claim.
    """
    if not isinstance(market_history, pd.DataFrame) or market_history.columns.has_duplicates:
        _fail("MARKET_SOURCE", "captured market history must be a unique-column DataFrame")
    domains = set()
    for surface in tuple(surfaces):
        domain = next(
            (candidate for surface_class, candidate in _DOMAIN_BY_CLASS.items() if isinstance(surface, surface_class)),
            None,
        )
        if domain is not None:
            domains.add(domain)
    columns = tuple(sorted({
        column
        for domain in domains
        for column in required_stage4b2_market_source_columns(domain)
    }))
    return tuple(
        (column, _source_column_row_hashes(market_history, column, domain="MARKET_SOURCE"))
        for column in columns
    )


def _verify_market_source_snapshot(surface: Any, domain: str, market_history: pd.DataFrame) -> None:
    if not isinstance(market_history, pd.DataFrame) or market_history.columns.has_duplicates:
        _fail(domain, "captured market source must be a unique-column DataFrame")
    bar = surface.bar_frame
    if len(market_history) != len(bar):
        _fail(domain, "captured market source row count differs from the Stage4B2 snapshot")
    if not market_history.index.equals(bar.index):
        _fail(domain, "captured market source index differs from the Stage4B2 snapshot")
    for column in required_stage4b2_market_source_columns(domain):
        expected = _source_column_row_hashes(market_history, column, domain=domain)
        actual = _source_column_row_hashes(bar, column, domain=domain)
        if actual != expected:
            position = next(
                index for index, (left, right) in enumerate(zip(actual, expected)) if left != right
            )
            _fail(
                domain,
                f"bar.{column}[{position}] differs from the exact captured market source observation",
            )


def _verify_market_source_column_hashes(
    surface: Any,
    domain: str,
    *,
    market_source_column_hashes: tuple[tuple[str, tuple[str, ...]], ...],
    source_through_position: int,
) -> None:
    if isinstance(source_through_position, bool) or not isinstance(source_through_position, int) or source_through_position < 0:
        _fail(domain, "source verification boundary must be a nonnegative integer position")
    if not isinstance(market_source_column_hashes, tuple):
        _fail(domain, "captured market source evidence must be an immutable tuple")
    by_column: dict[str, tuple[str, ...]] = {}
    for item in market_source_column_hashes:
        if not isinstance(item, tuple) or len(item) != 2:
            _fail(domain, "captured market source evidence has an invalid column entry")
        column, hashes = item
        if not isinstance(column, str) or not column or column in by_column:
            _fail(domain, "captured market source evidence has duplicate/invalid columns")
        if not isinstance(hashes, tuple) or any(
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
            for digest in hashes
        ):
            _fail(domain, f"captured market source row hashes for {column!r} are invalid")
        by_column[column] = hashes
    if tuple(sorted(by_column)) != tuple(by_column):
        _fail(domain, "captured market source columns are not canonically ordered")
    lengths = {len(hashes) for hashes in by_column.values()}
    if len(lengths) > 1:
        _fail(domain, "captured market source columns have inconsistent row counts")
    row_count = len(surface.bar_frame)
    if source_through_position >= row_count:
        _fail(domain, "as-of source boundary is unavailable in the captured Stage4B2 bar frame")
    for column in required_stage4b2_market_source_columns(domain):
        expected = by_column.get(column)
        if expected is None:
            _fail(domain, f"captured market source evidence is unavailable for required column {column!r}")
        if source_through_position >= len(expected):
            _fail(domain, f"captured market source evidence does not reach as-of position {source_through_position}")
        actual = _source_column_row_hashes(surface.bar_frame, column, domain=domain)
        # Verify the complete historical overlap, not just the projected row.
        # A valid future append may extend past the case's source evidence; such
        # future-only rows are not decision-time features, and an as-of request
        # beyond the evidence still fails closed above.
        compared = min(len(actual), len(expected))
        mismatch = next(
            (index for index in range(compared) if actual[index] != expected[index]),
            None,
        )
        if mismatch is not None:
            _fail(
                domain,
                f"bar.{column}[{mismatch}] differs from the captured market source prefix",
            )


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


def _check_creation_absence_values(surface: Any, *, domain: str, flag_column: str) -> None:
    bar = surface.bar_frame
    defaults = _CREATION_ABSENCE_DEFAULTS[domain]
    _require_columns(bar, tuple(defaults), domain, "bar_frame")
    flags = bar[flag_column].tolist()
    for position, created in enumerate(flags):
        if bool(created):
            continue
        for column, expected in defaults.items():
            actual = _bar_value(surface, column, position, domain)
            if expected is None:
                if not _is_missing(actual):
                    _fail(
                        domain,
                        f"noncreation field {column} must be missing at position {position}",
                    )
            elif isinstance(expected, str):
                if not isinstance(actual, str) or actual != expected:
                    _fail(
                        domain,
                        f"noncreation field {column} must equal producer absence value {expected!r} at position {position}",
                    )
            elif _integer(actual, domain, f"{column}[{position}]") != expected:
                _fail(
                    domain,
                    f"noncreation field {column} must equal producer absence value {expected} at position {position}",
                )


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


def _check_first_touch_semantics(
    surface: Any,
    *,
    domain: str,
    entity_by_id: dict[int, dict[str, Any]],
    events_by_id: dict[int, dict[str, int]],
    id_column: str,
    availability_column: str,
    qualifies,
    verify_fvg_coverage: bool = False,
) -> None:
    """Check only the literal CLOSED FIRST_TOUCH predicate and first occurrence."""
    row_count = len(surface.bar_frame)
    touch_events = {
        _integer(event[id_column], domain, f"event.{id_column}"): event
        for event in surface.event_frame.to_dict(orient="records")
        if event.get("event_type") == "FIRST_TOUCH"
    }
    for identity, entity in entity_by_id.items():
        available = _position(
            entity[availability_column],
            domain=domain,
            detail=availability_column,
            row_count=row_count,
        )
        expected = next(
            (position for position in range(available + 1, row_count) if qualifies(entity, position)),
            None,
        )
        actual = events_by_id[identity].get("FIRST_TOUCH")
        if actual != expected:
            _fail(
                domain,
                f"{id_column}={identity} FIRST_TOUCH does not match the exact earliest producer predicate position (expected {expected}, got {actual})",
            )
        if verify_fvg_coverage and expected is not None:
            event = touch_events.get(identity)
            if event is None:
                _fail(domain, f"fvg_id={identity} FIRST_TOUCH event record is missing")
            low = _number(entity["zone_low"], domain, "zone_low")
            high = _number(entity["zone_high"], domain, "zone_high")
            width = high - low
            event_high = _number(_bar_value(surface, "high", expected, domain), domain, "touch high")
            event_low = _number(_bar_value(surface, "low", expected, domain), domain, "touch low")
            coverage = (min(event_high, high) - max(event_low, low)) / width
            _near(
                domain,
                event.get("zone_range_coverage_fraction"),
                coverage,
                f"fvg_id={identity}.FIRST_TOUCH.zone_range_coverage_fraction",
            )


def _check_liquidity_aggregates(
    surface: Any, *, entity_by_id: dict[int, dict[str, Any]]
) -> None:
    domain = "LIQUIDITY"
    row_count = len(surface.bar_frame)
    counts = {column: [0] * row_count for column in _LIQUIDITY_EVENT_COUNT_COLUMNS.values()}
    for event in surface.event_frame.to_dict(orient="records"):
        if event.get("event_type") == "LEVEL_CREATED":
            continue
        key = (event.get("side"), event.get("event_type"))
        column = _LIQUIDITY_EVENT_COUNT_COLUMNS.get(key)
        if column is None:
            _fail(domain, f"cannot map producer lifecycle event count for {key!r}")
        position = _position(
            event["event_position"],
            domain=domain,
            detail="event_position",
            row_count=row_count,
        )
        counts[column][position] += 1

    for column, expected_by_position in counts.items():
        for position, expected in enumerate(expected_by_position):
            actual = _integer(_bar_value(surface, column, position, domain), domain, f"{column}[{position}]")
            if actual != expected:
                _fail(
                    domain,
                    f"per-bar producer event count {column}[{position}] is {actual}, expected {expected}",
                )

    high_created_at = [0] * row_count
    low_created_at = [0] * row_count
    for row in entity_by_id.values():
        confirmation = _position(
            row["source_confirmation_position"],
            domain=domain,
            detail="source_confirmation_position",
            row_count=row_count,
        )
        if row["side"] == "HIGH_SIDE":
            high_created_at[confirmation] += 1
        else:
            low_created_at[confirmation] += 1
    known_high = known_low = 0
    for position in range(row_count):
        known_high += high_created_at[position]
        known_low += low_created_at[position]
        actual_high = _integer(
            _bar_value(surface, "known_high_side_level_count", position, domain),
            domain,
            f"known_high_side_level_count[{position}]",
        )
        actual_low = _integer(
            _bar_value(surface, "known_low_side_level_count", position, domain),
            domain,
            f"known_low_side_level_count[{position}]",
        )
        if actual_high != known_high or actual_low != known_low:
            _fail(
                domain,
                f"cumulative known-level counts disagree with creation confirmations at position {position}",
            )


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
    _check_creation_absence_values(
        surface, domain=domain, flag_column="liquidity_level_created"
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

    def liquidity_touch_qualifies(entity: dict[str, Any], position: int) -> bool:
        price = _number(entity["immutable_level_price"], domain, "immutable_level_price")
        if entity["side"] == "HIGH_SIDE":
            return _number(_bar_value(surface, "high", position, domain), domain, "high") >= price
        return _number(_bar_value(surface, "low", position, domain), domain, "low") <= price

    _check_first_touch_semantics(
        surface,
        domain=domain,
        entity_by_id=entity_by_id,
        events_by_id=event_positions,
        id_column="level_id",
        availability_column="source_confirmation_position",
        qualifies=liquidity_touch_qualifies,
    )
    _check_liquidity_aggregates(surface, entity_by_id=entity_by_id)
    return (
        "entity_projection", "unique_ids", "creation_bar_mirrors", "creation_absence_defaults",
        "swing_source_witnesses", "lifecycle_references", "stable_lifecycle_attributes",
        "event_bar_ohlc", "event_price_bar_witnesses", "availability_and_age",
        "exact_first_touch_predicate_and_earliest_event", "per_bar_producer_event_counts",
        "cumulative_known_entity_counts",
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
    _check_creation_absence_values(
        surface, domain=domain, flag_column="ob_candidate_created"
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

        # CLOSED producer field: count opposite-colour candles in [search boundary, creation).
        bullish = row["direction"] == "BULLISH_OB_CANDIDATE"
        expected_opposite_count = sum(
            (
                _number(_bar_value(surface, "close", position, domain), domain, "close")
                < _number(_bar_value(surface, "open", position, domain), domain, "open")
            )
            if bullish
            else (
                _number(_bar_value(surface, "close", position, domain), domain, "close")
                > _number(_bar_value(surface, "open", position, domain), domain, "open")
            )
            for position in range(boundary, creation)
        )
        actual_opposite_count = _integer(
            _bar_value(surface, "created_ob_opposite_candle_count_in_leg", creation, domain),
            domain,
            f"created_ob_opposite_candle_count_in_leg[{creation}]",
        )
        if actual_opposite_count != expected_opposite_count:
            _fail(domain, f"zone_id={identity} creation opposite-candle count disagrees with the literal producer predicate")

    _, event_positions = _event_frame_common(
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

    def order_block_touch_qualifies(entity: dict[str, Any], position: int) -> bool:
        zone_low = _number(entity["full_zone_low"], domain, "full_zone_low")
        zone_high = _number(entity["full_zone_high"], domain, "full_zone_high")
        high = _number(_bar_value(surface, "high", position, domain), domain, "high")
        low = _number(_bar_value(surface, "low", position, domain), domain, "low")
        return high >= zone_low and low <= zone_high

    _check_first_touch_semantics(
        surface,
        domain=domain,
        entity_by_id=entity_by_id,
        events_by_id=event_positions,
        id_column="zone_id",
        availability_column="creation_position",
        qualifies=order_block_touch_qualifies,
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
        "entity_projection", "unique_ids", "creation_bar_mirrors", "creation_absence_defaults",
        "source_break_and_positions", "origin_ohlc_bounds", "producer_opposite_candle_count",
        "lifecycle_references", "stable_lifecycle_attributes", "event_bar_ohlc",
        "exact_first_touch_predicate_and_earliest_event",
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
    _check_creation_absence_values(
        surface, domain=domain, flag_column="fvg_candidate_created"
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

    _, event_positions = _event_frame_common(
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

    def fvg_touch_qualifies(entity: dict[str, Any], position: int) -> bool:
        zone_low = _number(entity["zone_low"], domain, "zone_low")
        zone_high = _number(entity["zone_high"], domain, "zone_high")
        high = _number(_bar_value(surface, "high", position, domain), domain, "high")
        low = _number(_bar_value(surface, "low", position, domain), domain, "low")
        return high >= zone_low and low <= zone_high

    _check_first_touch_semantics(
        surface,
        domain=domain,
        entity_by_id=entity_by_id,
        events_by_id=event_positions,
        id_column="fvg_id",
        availability_column="creation_position",
        qualifies=fvg_touch_qualifies,
        verify_fvg_coverage=True,
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
        "entity_projection", "unique_ids", "creation_bar_mirrors", "creation_absence_defaults",
        "source_bar_fvg_geometry", "lifecycle_references", "stable_lifecycle_attributes",
        "event_bar_ohlc", "availability_and_age", "exact_first_touch_predicate_and_earliest_event",
        "producer_touch_coverage_fraction",
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
    _check_creation_absence_values(
        surface, domain=domain, flag_column="dealing_range_created"
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
        if not (
            first_origin <= first_confirmation < second_confirmation == creation
            and second_origin <= second_confirmation
        ):
            _fail(domain, f"range_id={identity} endpoint origin/confirmation availability ordering is invalid")
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
        "range_table_projection", "unique_ids", "creation_bar_mirrors", "creation_absence_defaults",
        "endpoint_swing_witnesses", "endpoint_origin_confirmation_order_and_geometry",
        "current_range_bar_witnesses",
    )


def verify_stage4b2_consistency(
    surface_snapshot: Any,
    *,
    market_history: pd.DataFrame | None = None,
    market_source_column_hashes: tuple[tuple[str, tuple[str, ...]], ...] | None = None,
    source_through_position: int | None = None,
) -> Stage4B2ConsistencyResult:
    """Verify one privately captured public Stage4B2 snapshot; never call producers.

    A success label requires enforceable local source evidence: either the exact
    captured market frame at case creation, or row hashes retained in the case's
    provenance sidecar for later as-of/observed-entity consumers. Row hashes do
    not authenticate producers or assert market-feed authenticity.
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
        if market_history is not None:
            if market_source_column_hashes is not None or source_through_position is not None:
                _fail(domain, "supply either the exact market frame or captured source hashes, not both")
            _verify_market_source_snapshot(surface_snapshot, domain, market_history)
        else:
            if market_source_column_hashes is None or source_through_position is None:
                _fail(domain, "required captured market source evidence is unavailable")
            _verify_market_source_column_hashes(
                surface_snapshot,
                domain,
                market_source_column_hashes=market_source_column_hashes,
                source_through_position=source_through_position,
            )
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
        checks=(
            "existing_surface_integrity",
            "captured_market_source_binding",
            "reconstruction_input_binding",
        ) + checks,
    )
