"""Independent M3 outcome resolution on closed 2022 market bars only."""

from __future__ import annotations

import heapq
from bisect import bisect_left
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from .data import Candle
from .market_status import MarketStatus, market_status
from .order_blocks import OrderBlockDirection
from .predictions import (
    OUTCOME_DEFINITION_IDS,
    PREDICTION_HORIZON_MARKET_BARS,
    PREDICTION_SPEC_VERSION,
    PredictionType,
)
from .price import PriceBasis, ohlc

UTC = timezone.utc
SCORING_SPEC_VERSION = "m3-v1"
BASELINE_ID = "EXPANDING_MAJORITY_BY_VARIANT_TYPE_DIRECTION_V1"
INDEPENDENCE_ID = "FIRST_EMISSION_BY_VARIANT_TYPE_OBJECT_V1"


class Outcome(str, Enum):
    TRUE = "true"
    FALSE = "false"
    UNJUDGEABLE_SAME_BAR = "unjudgeable_same_bar"
    UNJUDGEABLE_TRUNCATED = "unjudgeable_truncated"

    @property
    def judgeable(self) -> bool:
        return self in {Outcome.TRUE, Outcome.FALSE}


@dataclass(frozen=True, slots=True)
class Resolution:
    outcome: Outcome
    resolved_at: datetime | None
    bars_observed: int


@dataclass(frozen=True, slots=True)
class MarketBars:
    candles: tuple[Candle, ...]
    ends: tuple[datetime, ...]

    @classmethod
    def from_candles(cls, candles: Iterable[Candle]) -> MarketBars:
        selected = tuple(
            candle for candle in candles if market_status(candle) is MarketStatus.MARKET
        )
        ends = tuple(candle.end for candle in selected)
        if any(later <= earlier for earlier, later in zip(ends, ends[1:])):
            raise ValueError("Market bars must have strictly increasing end times")
        return cls(selected, ends)

    def start_after(self, available_at: datetime) -> int:
        index = bisect_left(self.ends, available_at)
        if index == len(self.ends) or self.ends[index] != available_at:
            raise ValueError(
                f"Prediction time {available_at.isoformat()} is not a closed market bar"
            )
        return index + 1


@dataclass(frozen=True, slots=True)
class ScoredPrediction:
    prediction_id: str
    variant_id: str
    available_at: datetime
    concept: str
    prediction_type: str
    direction: str
    object_id: str
    outcome: Outcome
    resolved_at: datetime | None
    bars_observed: int
    independent: bool
    baseline_prediction: Outcome | None = None
    baseline_correct: bool | None = None

    @property
    def month(self) -> str:
        return self.available_at.strftime("%Y-%m")


@dataclass(frozen=True, slots=True)
class DecisionScore:
    decision_id: str
    prediction_id: str | None
    available_at: datetime
    decision_type: str
    object_id: str
    outcome: Outcome | None
    independent: bool
    baseline_prediction: Outcome | None
    baseline_correct: bool | None

    @property
    def month(self) -> str:
        return self.available_at.strftime("%Y-%m")


def _timestamp(value: Any) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Prediction and decision times must be timezone-aware")
    return parsed.astimezone(UTC)


def _required_float(prediction: Mapping[str, Any], field: str) -> float:
    value = prediction.get(field)
    if value is None:
        raise ValueError(f"{prediction.get('prediction_id')}: missing {field}")
    return float(value)


def resolve_market_window(
    prediction: Mapping[str, Any],
    market_candles: Sequence[Candle],
    *,
    start: int = 0,
) -> Resolution:
    """Resolve one prediction against future MARKET bars, never its issue bar."""

    prediction_type = PredictionType(prediction["prediction_type"])
    direction = OrderBlockDirection(prediction["direction"])
    basis = PriceBasis(prediction["basis"])
    horizon = int(prediction["horizon_market_bars"])
    if horizon <= 0:
        raise ValueError("Outcome horizon must be positive")
    if start < 0 or start > len(market_candles):
        raise ValueError("Future market-bar start is outside the input")

    observed = min(horizon, len(market_candles) - start)
    for index in range(start, start + observed):
        candle = market_candles[index]
        _, high, low, _ = ohlc(candle, basis)
        if prediction_type is PredictionType.DRAW_TOUCH:
            target = _required_float(prediction, "target_price")
            touched = high > target if direction is OrderBlockDirection.BULLISH else low < target
            if touched:
                return Resolution(Outcome.TRUE, candle.end, index - start + 1)
            continue

        if prediction_type is PredictionType.OB_FIRST_RETRACEMENT:
            lower = _required_float(prediction, "zone_lower")
            upper = _required_float(prediction, "zone_upper")
            stop = _required_float(prediction, "stop_price")
            touched = high > lower and low < upper
            violated = low < stop if direction is OrderBlockDirection.BULLISH else high > stop
            if touched and violated:
                return Resolution(
                    Outcome.UNJUDGEABLE_SAME_BAR, candle.end, index - start + 1
                )
            if touched:
                return Resolution(Outcome.TRUE, candle.end, index - start + 1)
            if violated:
                return Resolution(Outcome.FALSE, candle.end, index - start + 1)
            continue

        target = _required_float(prediction, "target_price")
        stop = _required_float(prediction, "stop_price")
        target_hit = high > target if direction is OrderBlockDirection.BULLISH else low < target
        stop_hit = low < stop if direction is OrderBlockDirection.BULLISH else high > stop
        if target_hit and stop_hit:
            return Resolution(
                Outcome.UNJUDGEABLE_SAME_BAR, candle.end, index - start + 1
            )
        if target_hit:
            return Resolution(Outcome.TRUE, candle.end, index - start + 1)
        if stop_hit:
            return Resolution(Outcome.FALSE, candle.end, index - start + 1)

    if observed < horizon:
        return Resolution(Outcome.UNJUDGEABLE_TRUNCATED, None, observed)
    return Resolution(Outcome.FALSE, market_candles[start + observed - 1].end, observed)


def prediction_object_id(prediction: Mapping[str, Any]) -> str:
    prediction_type = PredictionType(prediction["prediction_type"])
    variant = str(prediction["variant_id"])
    prediction_id = str(prediction["prediction_id"])
    if prediction_type is PredictionType.DRAW_TOUCH:
        object_id = prediction.get("target_id")
        if not object_id:
            raise ValueError(f"{prediction_id}: DRAW requires a target object")
        return str(object_id)
    short = "ob" if prediction_type is PredictionType.OB_FIRST_RETRACEMENT else "setup"
    prefix = f"p:{variant}:{short}:"
    if not prediction_id.startswith(prefix) or len(prediction_id) == len(prefix):
        raise ValueError(f"{prediction_id}: cannot derive its zone object")
    return prediction_id[len(prefix) :]


def _validate_prediction(
    prediction: Mapping[str, Any], *, expected_variant: str | None
) -> datetime:
    forbidden = {"outcome", "resolved_at", "baseline_prediction", "future_candles"}
    leaked = forbidden.intersection(prediction)
    if leaked:
        raise ValueError(f"Pass-1 row contains sealed fields: {sorted(leaked)}")
    if prediction.get("spec_version") != PREDICTION_SPEC_VERSION:
        raise ValueError("Prediction specification version differs from the frozen contract")
    if prediction.get("horizon_market_bars") != PREDICTION_HORIZON_MARKET_BARS:
        raise ValueError("Prediction horizon differs from 288 market bars")
    prediction_type = PredictionType(prediction["prediction_type"])
    if prediction.get("outcome_definition_id") != OUTCOME_DEFINITION_IDS[prediction_type]:
        raise ValueError("Outcome definition differs from the frozen prediction type")
    variant = str(prediction["variant_id"])
    if expected_variant is not None and variant != expected_variant:
        raise ValueError("Prediction ledger mixes or mislabels variants")
    available_at = _timestamp(prediction["available_at"])
    if available_at.year != 2022:
        raise ValueError("M3 DEV scoring permits prediction timestamps from 2022 only")
    PriceBasis(prediction["basis"])
    OrderBlockDirection(prediction["direction"])
    prediction_object_id(prediction)
    return available_at


def score_predictions(
    predictions: Sequence[Mapping[str, Any]],
    candles: Sequence[Candle],
    *,
    expected_variant: str | None = None,
) -> tuple[ScoredPrediction, ...]:
    if any(candle.start.year != 2022 for candle in candles):
        raise ValueError("M3 DEV scoring permits candles from 2022 only")
    market = MarketBars.from_candles(candles)
    identifiers: set[str] = set()
    seen_objects: set[tuple[str, str]] = set()
    scored: list[ScoredPrediction] = []
    previous_key: tuple[datetime, str] | None = None

    for prediction in predictions:
        available_at = _validate_prediction(prediction, expected_variant=expected_variant)
        prediction_id = str(prediction["prediction_id"])
        if prediction_id in identifiers:
            raise ValueError(f"Duplicate prediction identifier: {prediction_id}")
        identifiers.add(prediction_id)
        order_key = (available_at, prediction_id)
        if previous_key is not None and order_key < previous_key:
            raise ValueError("Prediction ledger must be sorted by time then identifier")
        previous_key = order_key
        object_id = prediction_object_id(prediction)
        independence_key = (str(prediction["prediction_type"]), object_id)
        independent = independence_key not in seen_objects
        seen_objects.add(independence_key)
        start = market.start_after(available_at)
        resolution = resolve_market_window(prediction, market.candles, start=start)
        scored.append(
            ScoredPrediction(
                prediction_id=prediction_id,
                variant_id=str(prediction["variant_id"]),
                available_at=available_at,
                concept=str(prediction["concept"]),
                prediction_type=str(prediction["prediction_type"]),
                direction=str(prediction["direction"]),
                object_id=object_id,
                outcome=resolution.outcome,
                resolved_at=resolution.resolved_at,
                bars_observed=resolution.bars_observed,
                independent=independent,
            )
        )
    return apply_causal_baseline(scored)


def apply_causal_baseline(
    cases: Iterable[ScoredPrediction],
) -> tuple[ScoredPrediction, ...]:
    """Attach a past-resolution-only majority forecast to independent cases."""

    counts: dict[tuple[str, str, str], list[int]] = defaultdict(lambda: [0, 0])
    pending: list[
        tuple[datetime, str, Outcome, tuple[str, str, str]]
    ] = []
    result: list[ScoredPrediction] = []
    previous_key: tuple[datetime, str] | None = None

    for case in cases:
        order_key = (case.available_at, case.prediction_id)
        if previous_key is not None and order_key < previous_key:
            raise ValueError("Baseline input must be sorted by time then identifier")
        previous_key = order_key
        if not case.independent:
            result.append(case)
            continue

        while pending and pending[0][0] <= case.available_at:
            _, _, outcome, key = heapq.heappop(pending)
            counts[key][0 if outcome is Outcome.TRUE else 1] += 1
        key = (case.variant_id, case.prediction_type, case.direction)
        true_count, false_count = counts[key]
        baseline = None
        if true_count + false_count:
            baseline = Outcome.TRUE if true_count > false_count else Outcome.FALSE
        correct = (
            baseline is case.outcome
            if baseline is not None and case.outcome.judgeable
            else None
        )
        updated = replace(
            case, baseline_prediction=baseline, baseline_correct=correct
        )
        result.append(updated)
        if case.outcome.judgeable:
            if case.resolved_at is None:
                raise ValueError("A judgeable outcome requires a resolution time")
            heapq.heappush(
                pending, (case.resolved_at, case.prediction_id, case.outcome, key)
            )
    return tuple(result)


def score_decisions(
    decisions: Sequence[Mapping[str, Any]],
    cases: Sequence[ScoredPrediction],
    *,
    expected_variant: str,
) -> tuple[DecisionScore, ...]:
    by_prediction = {case.prediction_id: case for case in cases}
    identifiers: set[str] = set()
    independent_objects: set[tuple[str, ...]] = set()
    result: list[DecisionScore] = []
    previous_key: tuple[datetime, str] | None = None
    permitted_without_prediction = {"stand_aside", "management"}

    for decision in decisions:
        decision_id = str(decision["decision_id"])
        if decision_id in identifiers:
            raise ValueError(f"Duplicate decision identifier: {decision_id}")
        identifiers.add(decision_id)
        available_at = _timestamp(decision["available_at"])
        if available_at.year != 2022:
            raise ValueError("M3 DEV decisions must be issued in 2022")
        order_key = (available_at, decision_id)
        if previous_key is not None and order_key < previous_key:
            raise ValueError("Decision ledger must be sorted by time then identifier")
        previous_key = order_key
        decision_type = str(decision["decision_type"])
        prediction_id = decision.get("prediction_id")
        if prediction_id is None:
            if decision_type not in permitted_without_prediction:
                raise ValueError(f"{decision_id}: decision requires a prediction")
            object_id = decision_id
            key = (decision_type, object_id)
            outcome = None
            baseline = None
            correct = None
            linked_independent = True
        else:
            case = by_prediction.get(str(prediction_id))
            if case is None or case.variant_id != expected_variant:
                raise ValueError(f"{decision_id}: unknown or cross-variant prediction")
            if case.available_at != available_at:
                raise ValueError(f"{decision_id}: decision and prediction times differ")
            object_id = case.object_id
            key = (decision_type, case.prediction_type, object_id)
            outcome = case.outcome
            baseline = case.baseline_prediction
            correct = case.baseline_correct
            linked_independent = case.independent
        independent = linked_independent and key not in independent_objects
        independent_objects.add(key)
        result.append(
            DecisionScore(
                decision_id=decision_id,
                prediction_id=str(prediction_id) if prediction_id is not None else None,
                available_at=available_at,
                decision_type=decision_type,
                object_id=object_id,
                outcome=outcome,
                independent=independent,
                baseline_prediction=baseline,
                baseline_correct=correct,
            )
        )
    return tuple(result)


def metrics(items: Sequence[ScoredPrediction | DecisionScore]) -> dict[str, Any]:
    independent = [item for item in items if item.independent]
    judgeable = [item for item in independent if item.outcome is not None and item.outcome.judgeable]
    matched = [item for item in judgeable if item.baseline_prediction is not None]
    true_count = sum(item.outcome is Outcome.TRUE for item in independent)
    false_count = sum(item.outcome is Outcome.FALSE for item in independent)
    same_bar = sum(item.outcome is Outcome.UNJUDGEABLE_SAME_BAR for item in independent)
    truncated = sum(item.outcome is Outcome.UNJUDGEABLE_TRUNCATED for item in independent)
    applicable = any(item.outcome is not None for item in items)
    hit_rate = true_count / len(judgeable) if judgeable else None
    matched_true = sum(item.outcome is Outcome.TRUE for item in matched)
    baseline_correct = sum(item.baseline_correct is True for item in matched)
    matched_hit_rate = matched_true / len(matched) if matched else None
    baseline_rate = baseline_correct / len(matched) if matched else None
    difference = (
        matched_hit_rate - baseline_rate
        if matched_hit_rate is not None and baseline_rate is not None
        else None
    )
    return {
        "raw_count": len(items),
        "independent_count": len(independent),
        "raw_true": sum(item.outcome is Outcome.TRUE for item in items),
        "raw_false": sum(item.outcome is Outcome.FALSE for item in items),
        "raw_unjudgeable_same_bar": sum(
            item.outcome is Outcome.UNJUDGEABLE_SAME_BAR for item in items
        ),
        "raw_unjudgeable_truncated": sum(
            item.outcome is Outcome.UNJUDGEABLE_TRUNCATED for item in items
        ),
        "true": true_count,
        "false": false_count,
        "unjudgeable": same_bar + truncated,
        "unjudgeable_same_bar": same_bar,
        "unjudgeable_truncated": truncated,
        "hit_rate": hit_rate,
        "matched_count": len(matched),
        "matched_hit_rate": matched_hit_rate,
        "baseline_rate": baseline_rate,
        "difference": difference,
        "baseline_unavailable": len(judgeable) - len(matched),
        "wrong_rate": false_count / len(judgeable) if judgeable else None,
        "descriptive_only": applicable and len(independent) < 30,
        "outcome_applicable": applicable,
        "baseline_id": BASELINE_ID if applicable else None,
        "independence_id": INDEPENDENCE_ID if applicable else None,
    }


def _group_metrics(
    items: Sequence[ScoredPrediction | DecisionScore],
    key: Callable[[ScoredPrediction | DecisionScore], str],
) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[ScoredPrediction | DecisionScore]] = defaultdict(list)
    for item in items:
        groups[key(item)].append(item)
    return {name: metrics(groups[name]) for name in sorted(groups)}


def summarise_predictions(cases: Sequence[ScoredPrediction]) -> dict[str, Any]:
    annual_concepts = _group_metrics(cases, lambda item: item.concept)
    annual_types = _group_metrics(cases, lambda item: item.prediction_type)
    monthly: dict[str, Any] = {}
    for month_number in range(1, 13):
        month = f"2022-{month_number:02d}"
        selected = [case for case in cases if case.month == month]
        concepts = _group_metrics(selected, lambda item: item.concept)
        types = _group_metrics(selected, lambda item: item.prediction_type)
        monthly[month] = {
            "concepts": {
                name: concepts.get(name, metrics([])) for name in annual_concepts
            },
            "prediction_types": {
                name: types.get(name, metrics([])) for name in annual_types
            },
        }
    return {
        "concepts": annual_concepts,
        "prediction_types": annual_types,
        "monthly": monthly,
    }


def summarise_decisions(decisions: Sequence[DecisionScore]) -> dict[str, Any]:
    annual = _group_metrics(decisions, lambda item: item.decision_type)
    monthly: dict[str, Any] = {}
    for month_number in range(1, 13):
        month = f"2022-{month_number:02d}"
        selected = [decision for decision in decisions if decision.month == month]
        groups = _group_metrics(selected, lambda item: item.decision_type)
        monthly[month] = {
            "decisions": {name: groups.get(name, metrics([])) for name in annual}
        }
    return {"decisions": annual, "monthly": monthly}


def scored_prediction_dict(case: ScoredPrediction) -> dict[str, Any]:
    return {
        "scoring_spec_version": SCORING_SPEC_VERSION,
        "prediction_id": case.prediction_id,
        "variant_id": case.variant_id,
        "available_at": case.available_at.isoformat(),
        "month": case.month,
        "concept": case.concept,
        "prediction_type": case.prediction_type,
        "direction": case.direction,
        "object_id": case.object_id,
        "independent": case.independent,
        "independence_id": INDEPENDENCE_ID,
        "outcome": case.outcome.value,
        "resolved_at": case.resolved_at.isoformat() if case.resolved_at else None,
        "bars_observed": case.bars_observed,
        "baseline_id": BASELINE_ID if case.independent else None,
        "baseline_prediction": (
            case.baseline_prediction.value if case.baseline_prediction else None
        ),
        "baseline_correct": case.baseline_correct,
    }
