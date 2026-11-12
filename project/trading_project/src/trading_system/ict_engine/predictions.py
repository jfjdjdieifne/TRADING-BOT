"""Prefix-only prediction values and deterministic JSONL emission.

This module deliberately contains no outcome resolver or scoring import.  The
later scorer consumes these records in a separate process.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from .order_blocks import OrderBlockDirection
from .price import PriceBasis

PREDICTION_SPEC_VERSION = "m2-v1"
PREDICTION_HORIZON_MARKET_BARS = 288


class PredictionType(str, Enum):
    DRAW_TOUCH = "draw_touch"
    OB_FIRST_RETRACEMENT = "ob_first_retracement"
    SETUP_TARGET_BEFORE_STOP = "setup_target_before_stop"


OUTCOME_DEFINITION_IDS = {
    PredictionType.DRAW_TOUCH: "DRAW_TOUCH_V1",
    PredictionType.OB_FIRST_RETRACEMENT: "OB_FIRST_RETRACEMENT_V1",
    PredictionType.SETUP_TARGET_BEFORE_STOP: "SETUP_TARGET_BEFORE_STOP_V1",
}


@dataclass(frozen=True, slots=True)
class Prediction:
    prediction_id: str
    available_at: datetime
    variant_id: str
    concept: str
    prediction_type: PredictionType
    direction: OrderBlockDirection
    basis: PriceBasis
    claim_ids: tuple[str, ...]
    expectation: str
    invalidation: str
    source_event_id: str
    entry_price: float | None = None
    target_id: str | None = None
    target_price: float | None = None
    stop_price: float | None = None
    zone_lower: float | None = None
    zone_upper: float | None = None
    reward_risk: str | None = None
    spec_version: str = PREDICTION_SPEC_VERSION
    horizon_market_bars: int = PREDICTION_HORIZON_MARKET_BARS

    @property
    def outcome_definition_id(self) -> str:
        return OUTCOME_DEFINITION_IDS[self.prediction_type]


def prediction_to_dict(prediction: Prediction) -> dict[str, Any]:
    """Explicit schema: no outcome, resolution time, or future candle data."""

    return {
        "prediction_id": prediction.prediction_id,
        "spec_version": prediction.spec_version,
        "variant_id": prediction.variant_id,
        "available_at": prediction.available_at.isoformat(),
        "concept": prediction.concept,
        "prediction_type": prediction.prediction_type.value,
        "direction": prediction.direction.value,
        "basis": prediction.basis.value,
        "claim_ids": list(prediction.claim_ids),
        "expectation": prediction.expectation,
        "invalidation": prediction.invalidation,
        "outcome_definition_id": prediction.outcome_definition_id,
        "horizon_market_bars": prediction.horizon_market_bars,
        "source_event_id": prediction.source_event_id,
        "entry_price": prediction.entry_price,
        "target_id": prediction.target_id,
        "target_price": prediction.target_price,
        "stop_price": prediction.stop_price,
        "zone_lower": prediction.zone_lower,
        "zone_upper": prediction.zone_upper,
        "reward_risk": prediction.reward_risk,
    }


def prediction_json(prediction: Prediction) -> str:
    return json.dumps(
        prediction_to_dict(prediction),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def write_prediction_ledger(
    path: str | Path, predictions: Iterable[Prediction]
) -> int:
    """Atomically write a stable, sorted UTF-8 ledger and return its row count."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(
        predictions, key=lambda item: (item.available_at, item.prediction_id)
    )
    identifiers = [item.prediction_id for item in rows]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("Prediction identifiers must be unique within a ledger")
    temporary = destination.with_name(destination.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        for prediction in rows:
            handle.write(prediction_json(prediction))
            handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, destination)
    return len(rows)


def read_prediction_ledger(path: str | Path) -> tuple[Mapping[str, Any], ...]:
    """Read pass-1 records without resolving them; useful for audit tooling."""

    with Path(path).open(encoding="utf-8") as handle:
        return tuple(json.loads(line) for line in handle if line.strip())
