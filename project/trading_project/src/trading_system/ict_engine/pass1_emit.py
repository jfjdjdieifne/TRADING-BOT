"""Pass 1: load closed candles and emit prefix-only reading ledgers.

No outcome resolver is imported or called here.  Run as a module with an annual
input path, a prediction output path, and one pre-registered variant identifier.
"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from .data import Candle, load_eurusd_5m
from .narrator import DecisionRecord, NarrationEvent, reading_trace
from .predictions import write_prediction_ledger
from .variants import VARIANT_BY_ID


@dataclass(frozen=True, slots=True)
class EmissionSummary:
    variant_id: str
    candle_count: int
    prediction_count: int
    narration_count: int
    decision_count: int
    prediction_counts: tuple[tuple[str, int], ...]
    decision_counts: tuple[tuple[str, int], ...]


def _json_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    return value


def _record_dict(record: NarrationEvent | DecisionRecord) -> dict[str, Any]:
    if isinstance(record, NarrationEvent):
        return {
            "event_id": record.event_id,
            "available_at": record.available_at.isoformat(),
            "concept": record.concept,
            "claim_ids": list(record.claim_ids),
            "text": record.text,
        }
    return {
        "decision_id": record.decision_id,
        "available_at": record.available_at.isoformat(),
        "decision_type": record.decision_type.value,
        "concept": record.concept,
        "claim_ids": list(record.claim_ids),
        "reason": record.reason,
        "prediction_id": record.prediction_id,
    }


def _write_auxiliary(
    path: Path, records: Iterable[NarrationEvent | DecisionRecord]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    ordered = sorted(
        records,
        key=lambda record: (
            record.available_at,
            record.event_id if isinstance(record, NarrationEvent) else record.decision_id,
        ),
    )
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        for record in ordered:
            handle.write(
                json.dumps(
                    _record_dict(record),
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                    allow_nan=False,
                )
            )
            handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def emit_pass1(
    candles: tuple[Candle, ...],
    *,
    variant_id: str,
    prediction_output: str | Path,
    narration_output: str | Path | None = None,
    decisions_output: str | Path | None = None,
) -> EmissionSummary:
    variant = VARIANT_BY_ID[variant_id]
    readings = reading_trace(candles, variant)
    predictions = tuple(
        prediction for reading in readings for prediction in reading.predictions
    )
    narration = tuple(
        event for reading in readings for event in reading.narration
    )
    decisions = tuple(
        decision for reading in readings for decision in reading.decisions
    )
    write_prediction_ledger(prediction_output, predictions)
    if narration_output is not None:
        _write_auxiliary(Path(narration_output), narration)
    if decisions_output is not None:
        _write_auxiliary(Path(decisions_output), decisions)
    prediction_counts = Counter(
        prediction.prediction_type.value for prediction in predictions
    )
    decision_counts = Counter(
        decision.decision_type.value for decision in decisions
    )
    return EmissionSummary(
        variant_id=variant_id,
        candle_count=len(candles),
        prediction_count=len(predictions),
        narration_count=len(narration),
        decision_count=len(decisions),
        prediction_counts=tuple(sorted(prediction_counts.items())),
        decision_counts=tuple(sorted(decision_counts.items())),
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="كتابة تنبؤات المقدمة فقط من دون قراءة النتائج اللاحقة."
    )
    parser.add_argument("--input", required=True, help="ملف سنوي مضغوط بالمخطط المثبت")
    parser.add_argument("--predictions", required=True, help="مسار سجل التنبؤات")
    parser.add_argument("--narration", help="مسار اختياري لسجل السرد")
    parser.add_argument("--decisions", help="مسار اختياري لسجل القرارات")
    parser.add_argument("--variant", required=True, choices=sorted(VARIANT_BY_ID))
    return parser


def main() -> None:
    arguments = _parser().parse_args()
    batch = load_eurusd_5m(arguments.input)
    summary = emit_pass1(
        batch.candles,
        variant_id=arguments.variant,
        prediction_output=arguments.predictions,
        narration_output=arguments.narration,
        decisions_output=arguments.decisions,
    )
    print(f"اكتمل إصدار المقدمة للمتغير {summary.variant_id}.")
    print(f"عدد الشموع: {summary.candle_count}؛ عدد التنبؤات: {summary.prediction_count}.")
    print(f"عدد أحداث السرد: {summary.narration_count}؛ عدد القرارات: {summary.decision_count}.")
    for name, count in summary.prediction_counts:
        print(f"نوع التنبؤ {name}: {count}.")
    for name, count in summary.decision_counts:
        print(f"نوع القرار {name}: {count}.")
    print("لم تُقرأ نتيجة لاحقة ولم يُحسب خط أساس أو معدل إصابة.")


if __name__ == "__main__":
    main()
