"""M3 pass-2 CLI: score six frozen 2022 ledgers without pass-1 imports."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

from .data import load_eurusd_5m
from .scoring import (
    BASELINE_ID,
    INDEPENDENCE_ID,
    SCORING_SPEC_VERSION,
    MarketBars,
    score_decisions,
    score_predictions,
    scored_prediction_dict,
    summarise_decisions,
    summarise_predictions,
)
from .variants import VARIANT_BY_ID

_FULL_COMMIT = re.compile(r"[0-9a-f]{40}\Z")


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_jsonl(path: str | Path) -> tuple[dict[str, Any], ...]:
    with Path(path).open(encoding="utf-8") as handle:
        return tuple(json.loads(line) for line in handle if line.strip())


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _write_outcomes(path: Path, cases) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        for case in cases:
            handle.write(
                json.dumps(
                    scored_prediction_dict(case),
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


def load_dev_2022(path: str | Path):
    source = Path(path)
    if source.name != "2022.csv.gz":
        raise ValueError("M3 refuses every development input not named 2022.csv.gz")
    batch = load_eurusd_5m(source)
    if batch.source_year != 2022 or any(
        candle.start.year != 2022 for candle in batch.candles
    ):
        raise ValueError("M3 DEV scoring is restricted to 2022")
    return batch


def score_all(
    *,
    data_path: str | Path,
    ledger_root: str | Path,
    output_dir: str | Path,
    scoring_commit: str,
    prediction_spec_commit: str,
    variant_plan_commit: str,
) -> dict[str, Any]:
    for label, commit in {
        "scoring": scoring_commit,
        "prediction specification": prediction_spec_commit,
        "variant plan": variant_plan_commit,
    }.items():
        if not _FULL_COMMIT.fullmatch(commit):
            raise ValueError(f"{label} provenance requires a full lowercase Git commit")

    batch = load_dev_2022(data_path)
    root = Path(ledger_root)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    market = MarketBars.from_candles(batch.candles)
    result: dict[str, Any] = {
        "scoring_spec_version": SCORING_SPEC_VERSION,
        "year": 2022,
        "horizon_market_bars": 288,
        "independence_id": INDEPENDENCE_ID,
        "baseline_id": BASELINE_ID,
        "provenance": {
            "scoring_commit": scoring_commit,
            "prediction_spec_commit": prediction_spec_commit,
            "variant_plan_commit": variant_plan_commit,
        },
        "data": {
            "path": str(Path(data_path)),
            "sha256": sha256_file(data_path),
            "rows": batch.rows_seen,
            "candles": len(batch.candles),
            "market_candles": len(market.candles),
        },
        "variants": {},
    }

    for variant_id in VARIANT_BY_ID:
        prediction_path = root / f"m2_{variant_id}_predictions.jsonl"
        decision_path = root / f"m2_{variant_id}_decisions.jsonl"
        predictions = read_jsonl(prediction_path)
        cases = score_predictions(
            predictions, batch.candles, expected_variant=variant_id
        )
        outcome_path = destination / f"m3_{variant_id}_outcomes.jsonl"
        _write_outcomes(outcome_path, cases)
        prediction_summary = summarise_predictions(cases)
        decisions = read_jsonl(decision_path)
        decision_scores = score_decisions(
            decisions, cases, expected_variant=variant_id
        )
        decision_summary = summarise_decisions(decision_scores)
        result["variants"][variant_id] = {
            "inputs": {
                "predictions": {
                    "path": str(prediction_path),
                    "rows": len(predictions),
                    "sha256": sha256_file(prediction_path),
                },
                "decisions": {
                    "path": str(decision_path),
                    "rows": len(decisions),
                    "sha256": sha256_file(decision_path),
                },
            },
            "outcomes": {
                "path": str(outcome_path),
                "rows": len(cases),
                "sha256": sha256_file(outcome_path),
            },
            "prediction_summary": prediction_summary,
            "decision_summary": decision_summary,
        }
        del decisions, decision_scores, cases, predictions

    summary_path = destination / "m3_scores.json"
    _write_json(summary_path, result)
    result["summary_output"] = {
        "path": str(summary_path),
        "sha256": sha256_file(summary_path),
    }
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="تسجيل مستقل لسجلات 2022 الستة بأفق 288 شمعة سوق."
    )
    parser.add_argument("--input", required=True, help="ملف 2022 المثبت وحده")
    parser.add_argument("--ledger-root", required=True, help="مجلد سجلات المرحلة الثانية")
    parser.add_argument("--output-dir", required=True, help="مجلد مخرجات كبير خارج المستودع")
    parser.add_argument("--scoring-commit", required=True)
    parser.add_argument("--prediction-spec-commit", required=True)
    parser.add_argument("--variant-plan-commit", required=True)
    return parser


def main() -> None:
    arguments = _parser().parse_args()
    result = score_all(
        data_path=arguments.input,
        ledger_root=arguments.ledger_root,
        output_dir=arguments.output_dir,
        scoring_commit=arguments.scoring_commit,
        prediction_spec_commit=arguments.prediction_spec_commit,
        variant_plan_commit=arguments.variant_plan_commit,
    )
    print("اكتمل تسجيل 2022 للمتغيرات الستة، من دون قراءة 2023 أو لاحقة.")
    for variant_id, variant in result["variants"].items():
        types = variant["prediction_summary"]["prediction_types"]
        counts = "؛ ".join(
            f"{name}: خام {values['raw_count']}، مستقل {values['independent_count']}، "
            f"إصابة {values['true']}، إخفاق {values['false']}، "
            f"لا حكم {values['unjudgeable']}"
            for name, values in types.items()
        )
        print(f"{variant_id}: {counts}")
    print(f"ملخص النتائج: {result['summary_output']['path']}")
    print(f"بصمة الملخص: {result['summary_output']['sha256']}")


if __name__ == "__main__":
    main()
