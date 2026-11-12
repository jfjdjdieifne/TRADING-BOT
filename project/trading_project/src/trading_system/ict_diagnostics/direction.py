"""Symmetric opposite-side barriers and their two preregistered references."""

from __future__ import annotations

import hashlib
from typing import Any

from trading_system.ict_engine.order_blocks import OrderBlockDirection
from trading_system.ict_engine.price import PriceBasis, ohlc
from trading_system.ict_engine.scoring import MarketBars

from .common import iso
from .context import EntryContext

DIRECTION_SEED = "ICT-2022-OPPOSITE-SIDE-V2-SEED-001"
DIRECTION_GRID = (1, 2, 4, 8)
DIRECTION_HORIZON = 288


def resolve_barriers(
    market: MarketBars,
    *,
    entry_index: int,
    entry: float,
    distance: float,
    direction: OrderBlockDirection,
    basis: PriceBasis,
    horizon: int = DIRECTION_HORIZON,
) -> dict[str, Any]:
    if entry_index < 0 or entry_index >= len(market.candles):
        raise ValueError("Barrier entry index is outside market bars")
    if distance <= 0 or horizon <= 0:
        raise ValueError("Barrier distance and horizon must be positive")
    if direction is OrderBlockDirection.BULLISH:
        favorable = entry + distance
        adverse = entry - distance
    else:
        favorable = entry - distance
        adverse = entry + distance
    start = entry_index + 1
    observed = min(horizon, len(market.candles) - start)
    for offset in range(observed):
        candle = market.candles[start + offset]
        _, high, low, _ = ohlc(candle, basis)
        if direction is OrderBlockDirection.BULLISH:
            favorable_hit = high > favorable
            adverse_hit = low < adverse
        else:
            favorable_hit = low < favorable
            adverse_hit = high > adverse
        outcome = None
        if favorable_hit and adverse_hit:
            outcome = "UNJUDGEABLE_SAME_BAR"
        elif favorable_hit:
            outcome = "DIRECTION_FIRST"
        elif adverse_hit:
            outcome = "OPPOSITE_FIRST"
        if outcome is not None:
            return {
                "outcome": outcome,
                "bars": offset + 1,
                "resolved_at": iso(candle.end),
                "observed_until": iso(candle.end),
                "entry": entry,
                "favorable_barrier": favorable,
                "adverse_barrier": adverse,
                "distance": distance,
                "horizon": horizon,
            }
    truncated = observed < horizon
    observed_until = iso(market.candles[start + observed - 1].end) if observed else iso(market.candles[entry_index].end)
    return {
        "outcome": "TRUNCATED" if truncated else "NO_TOUCH",
        "bars": observed,
        "resolved_at": None,
        "observed_until": observed_until,
        "entry": entry,
        "favorable_barrier": favorable,
        "adverse_barrier": adverse,
        "distance": distance,
        "horizon": horizon,
    }


def mirrored_result(result: dict[str, Any]) -> dict[str, Any]:
    mirrored = dict(result)
    if result["outcome"] == "DIRECTION_FIRST":
        mirrored["outcome"] = "OPPOSITE_FIRST"
    elif result["outcome"] == "OPPOSITE_FIRST":
        mirrored["outcome"] = "DIRECTION_FIRST"
    mirrored["favorable_barrier"], mirrored["adverse_barrier"] = (
        result["adverse_barrier"],
        result["favorable_barrier"],
    )
    return mirrored


def random_entry_index(
    candidates: tuple[int, ...], *, variant_id: str, case_id: str, multiple: int
) -> int | None:
    if not candidates:
        return None
    key = f"{variant_id}:{case_id}:{multiple}".encode("utf-8")
    digest = hashlib.sha256(DIRECTION_SEED.encode("utf-8") + b"\0" + key).digest()
    position = int.from_bytes(digest, "big") % len(candidates)
    return candidates[position]


def direction_rows_for_case(
    context: EntryContext,
    basis: PriceBasis,
    market: MarketBars,
    month_candidate_indices: tuple[int, ...],
) -> list[dict[str, Any]]:
    prediction = context.prediction
    if prediction is None:
        raise ValueError("Direction barriers require an engine setup entry")
    entry_index = market.start_after(prediction.available_at) - 1
    entry = float(prediction.entry_price)
    stop = float(prediction.stop_price)
    risk = entry - stop if context.direction is OrderBlockDirection.BULLISH else stop - entry
    rows: list[dict[str, Any]] = []
    for multiple in DIRECTION_GRID:
        distance = multiple * risk
        actual = resolve_barriers(
            market,
            entry_index=entry_index,
            entry=entry,
            distance=distance,
            direction=context.direction,
            basis=basis,
        )
        random_index = random_entry_index(
            month_candidate_indices,
            variant_id=context.variant_id,
            case_id=prediction.prediction_id,
            multiple=multiple,
        )
        if random_index is None:
            random_result = {"outcome": "UNAVAILABLE", "bars": 0, "resolved_at": None}
            random_at = None
        else:
            random_entry = ohlc(market.candles[random_index], basis)[3]
            random_at = iso(market.candles[random_index].end)
            random_result = resolve_barriers(
                market,
                entry_index=random_index,
                entry=random_entry,
                distance=distance,
                direction=context.direction,
                basis=basis,
            )
        opposite = mirrored_result(actual)
        rows.append(
            {
                "case_id": prediction.prediction_id,
                "variant_id": context.variant_id,
                "available_at": iso(prediction.available_at),
                "month": prediction.available_at.strftime("%Y-%m"),
                "direction": context.direction.value,
                "basis": basis.value,
                "multiple": multiple,
                "distance": distance,
                "engine": actual,
                "random_same_month_same_direction": {
                    **random_result,
                    "random_entry_at": random_at,
                    "same_as_engine_time": random_index == entry_index,
                    "seed": DIRECTION_SEED,
                },
                "opposite_direction_same_time": opposite,
                "paired_engine_random_judgeable": actual["outcome"] in {"DIRECTION_FIRST", "OPPOSITE_FIRST"}
                and random_result["outcome"] in {"DIRECTION_FIRST", "OPPOSITE_FIRST"},
            }
        )
    return rows


def count_barrier_results(rows: list[dict[str, Any]], arm: str) -> dict[str, int]:
    names = ["DIRECTION_FIRST", "OPPOSITE_FIRST", "UNJUDGEABLE_SAME_BAR", "NO_TOUCH", "TRUNCATED", "UNAVAILABLE"]
    return {name: sum(row[arm]["outcome"] == name for row in rows) for name in names}
