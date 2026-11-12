from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from trading_system.ict_engine.m2_waiting import K2_THIN_CONCEPTS, M2_WAITING_CONCEPTS
from trading_system.ict_engine.pass1_emit import emit_pass1
from trading_system.ict_engine.predictions import (
    OUTCOME_DEFINITION_IDS,
    PREDICTION_HORIZON_MARKET_BARS,
    PredictionType,
    prediction_to_dict,
    read_prediction_ledger,
    write_prediction_ledger,
)
from trading_system.ict_engine.variants import REFERENCE

from .test_narrator import setup_candles

ENGINE = Path(__file__).resolve().parents[1]


def _predictions(candles=setup_candles()):
    from trading_system.ict_engine.narrator import reading_trace

    return tuple(
        prediction
        for reading in reading_trace(candles, REFERENCE)
        for prediction in reading.predictions
    )


def test_every_prediction_has_required_causal_schema_and_real_claims() -> None:
    predictions = _predictions()
    assert {item.prediction_type for item in predictions} == set(PredictionType)
    for prediction in predictions:
        row = prediction_to_dict(prediction)
        assert row["prediction_id"]
        assert row["available_at"] == prediction.available_at.isoformat()
        assert row["concept"]
        assert row["claim_ids"]
        assert all(claim.startswith(("U", "K2C-")) for claim in row["claim_ids"])
        assert row["expectation"]
        assert row["invalidation"]
        assert row["outcome_definition_id"] == OUTCOME_DEFINITION_IDS[prediction.prediction_type]
        assert row["horizon_market_bars"] == PREDICTION_HORIZON_MARKET_BARS == 288
        assert row["source_event_id"]
        if prediction.prediction_type is PredictionType.OB_FIRST_RETRACEMENT:
            assert row["zone_lower"] < row["zone_upper"]
            assert row["zone_lower"] <= row["stop_price"] <= row["zone_upper"]
        if prediction.prediction_type is PredictionType.DRAW_TOUCH:
            assert row["target_price"] is not None
        if prediction.prediction_type is PredictionType.SETUP_TARGET_BEFORE_STOP:
            assert row["entry_price"] is not None
            assert row["target_price"] is not None
            assert row["stop_price"] is not None
        assert not {
            "outcome",
            "resolved_at",
            "resolution_time",
            "hit",
            "score",
            "future_candles",
        } & set(row)


def test_pass1_two_runs_are_byte_identical_including_audit_ledgers(tmp_path) -> None:
    candles = setup_candles()
    first = emit_pass1(
        candles,
        variant_id="R00",
        prediction_output=tmp_path / "a.jsonl",
        narration_output=tmp_path / "a_narration.jsonl",
        decisions_output=tmp_path / "a_decisions.jsonl",
    )
    second = emit_pass1(
        candles,
        variant_id="R00",
        prediction_output=tmp_path / "b.jsonl",
        narration_output=tmp_path / "b_narration.jsonl",
        decisions_output=tmp_path / "b_decisions.jsonl",
    )
    assert first == second
    for left, right in (
        ("a.jsonl", "b.jsonl"),
        ("a_narration.jsonl", "b_narration.jsonl"),
        ("a_decisions.jsonl", "b_decisions.jsonl"),
    ):
        assert (tmp_path / left).read_bytes() == (tmp_path / right).read_bytes()
    records = read_prediction_ledger(tmp_path / "a.jsonl")
    assert len(records) == first.prediction_count
    assert all(record["variant_id"] == "R00" for record in records)
    assert len({record["prediction_id"] for record in records}) == len(records)


def test_duplicate_prediction_ids_are_rejected_before_writing(tmp_path) -> None:
    predictions = _predictions()
    duplicate = predictions[0]
    with pytest.raises(ValueError, match="identifiers must be unique"):
        write_prediction_ledger(tmp_path / "duplicate.jsonl", (duplicate, duplicate))
    assert not (tmp_path / "duplicate.jsonl").exists()


def test_pass1_modules_never_import_an_outcome_scorer() -> None:
    names = ("pass1_emit.py", "narrator.py", "predictions.py", "variants.py")
    forbidden = {"scoring", "score_ledger", "outcomes", "outcome_resolver"}
    for name in names:
        tree = ast.parse((ENGINE / name).read_text(encoding="utf-8"), filename=name)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = {alias.name for alias in node.names}
            elif isinstance(node, ast.ImportFrom):
                imported = {node.module or ""}
            else:
                continue
            assert not any(
                module.split(".")[-1] in forbidden for module in imported
            ), (name, imported)


def test_all_23_thin_k2_cards_remain_waiting() -> None:
    assert len(K2_THIN_CONCEPTS) == 23
    waiting_names = {item.concept for item in M2_WAITING_CONCEPTS}
    assert {f"k2_thin:{name}" for name in K2_THIN_CONCEPTS} <= waiting_names
    assert "breaker_swing_point_entry" in waiting_names
    assert "mean_threshold_stop_boundary" in waiting_names
    assert "liquidity_run_10_20_pips" in waiting_names


def test_ledger_is_utf8_stable_json_with_no_nonfinite_numbers(tmp_path) -> None:
    output = tmp_path / "predictions.jsonl"
    emit_pass1(setup_candles(), variant_id="R00", prediction_output=output)
    raw = output.read_text(encoding="utf-8")
    assert "NaN" not in raw and "Infinity" not in raw
    for line in raw.splitlines():
        parsed = json.loads(line)
        assert parsed["spec_version"] == "m2-v1"
        assert isinstance(parsed["expectation"], str)
        assert isinstance(parsed["invalidation"], str)
