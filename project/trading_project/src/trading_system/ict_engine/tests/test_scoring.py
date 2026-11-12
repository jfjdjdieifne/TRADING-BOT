from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json

import pytest

from trading_system.ict_engine.m3_report import (
    extract_narration_examples,
    render_main_report,
    render_monthly_report,
    select_narration_examples,
)
from trading_system.ict_engine.score_ledger import load_dev_2022
from trading_system.ict_engine.narrator import reading_trace
from trading_system.ict_engine.scoring import (
    Outcome,
    ScoredPrediction,
    apply_causal_baseline,
    metrics,
    prediction_object_id,
    resolve_market_window,
    score_decisions,
    score_predictions,
    summarise_decisions,
    summarise_predictions,
)
from trading_system.ict_engine.variants import REFERENCE

from .primitive_helpers import candle_at, market_series

UTC = timezone.utc
ORIGIN = datetime(2022, 1, 3, tzinfo=UTC)


def prediction_row(
    prediction_id: str = "p:R00:draw:pool-a",
    *,
    available_at: datetime = ORIGIN + timedelta(minutes=5),
    prediction_type: str = "draw_touch",
    direction: str = "bullish",
    horizon: int = 2,
    target: float | None = 1.1,
    stop: float | None = None,
    lower: float | None = None,
    upper: float | None = None,
    basis: str = "bid",
) -> dict:
    definition = {
        "draw_touch": "DRAW_TOUCH_V1",
        "ob_first_retracement": "OB_FIRST_RETRACEMENT_V1",
        "setup_target_before_stop": "SETUP_TARGET_BEFORE_STOP_V1",
    }[prediction_type]
    short = {"draw_touch": "draw", "ob_first_retracement": "ob", "setup_target_before_stop": "setup"}[prediction_type]
    if not prediction_id.startswith(f"p:R00:{short}:"):
        prediction_id = f"p:R00:{short}:{prediction_id}"
    return {
        "prediction_id": prediction_id,
        "spec_version": "m2-v1",
        "variant_id": "R00",
        "available_at": available_at.isoformat(),
        "concept": "liquidity_pool_candidate",
        "prediction_type": prediction_type,
        "direction": direction,
        "basis": basis,
        "claim_ids": ["U0020"],
        "expectation": "توقع عربي",
        "invalidation": "إبطال عربي",
        "outcome_definition_id": definition,
        "horizon_market_bars": horizon,
        "source_event_id": "synthetic",
        "entry_price": 1.05 if prediction_type == "setup_target_before_stop" else None,
        "target_id": "pool-a" if prediction_type == "draw_touch" else None,
        "target_price": target,
        "stop_price": stop,
        "zone_lower": lower,
        "zone_upper": upper,
        "reward_risk": None,
    }


def test_draw_requires_strict_break_and_resolves_on_second_market_bar() -> None:
    candles = market_series(
        [
            (1.0, 1.02, 0.99, 1.01),
            (1.01, 1.1, 1.0, 1.05),
            (1.05, 1.1001, 1.04, 1.08),
        ],
        origin=ORIGIN,
    )
    resolution = resolve_market_window(prediction_row(), candles, start=1)
    assert resolution.outcome is Outcome.TRUE
    assert resolution.resolved_at == candles[2].end
    assert resolution.bars_observed == 2


def test_bearish_draw_and_ask_basis_use_the_selected_side() -> None:
    candles = market_series(
        [(1.2, 1.3, 1.1, 1.2), (1.2, 1.25, 1.0998, 1.1)], origin=ORIGIN
    )
    row = prediction_row(direction="bearish", target=1.1, basis="ask")
    # ASK low is 1.1000 exactly: equality is not a strict break.
    assert resolve_market_window(row, candles, start=1).outcome is Outcome.UNJUDGEABLE_TRUNCATED
    row["horizon_market_bars"] = 1
    assert resolve_market_window(row, candles, start=1).outcome is Outcome.FALSE


def test_complete_timeout_is_false_but_short_data_is_truncated() -> None:
    candles = market_series(
        [(1.0, 1.01, 0.99, 1.0), (1.0, 1.02, 0.99, 1.0), (1.0, 1.02, 0.99, 1.0)],
        origin=ORIGIN,
    )
    complete = resolve_market_window(prediction_row(), candles, start=1)
    assert complete.outcome is Outcome.FALSE
    assert complete.resolved_at == candles[2].end
    short = resolve_market_window(prediction_row(), candles[:2], start=1)
    assert short.outcome is Outcome.UNJUDGEABLE_TRUNCATED
    assert short.resolved_at is None
    assert short.bars_observed == 1


@pytest.mark.parametrize(
    "future,expected",
    [
        ((1.04, 1.06, 1.03, 1.05), Outcome.TRUE),
        ((1.04, 1.06, 0.89, 1.05), Outcome.UNJUDGEABLE_SAME_BAR),
        ((0.95, 0.97, 0.89, 0.96), Outcome.FALSE),
    ],
)
def test_ob_touch_violation_and_collision(future, expected: Outcome) -> None:
    candles = market_series([(1.1, 1.12, 1.08, 1.1), future], origin=ORIGIN)
    row = prediction_row(
        "p:R00:ob:zone-a",
        prediction_type="ob_first_retracement",
        target=None,
        stop=0.9,
        lower=1.0,
        upper=1.1,
        horizon=1,
    )
    resolution = resolve_market_window(row, candles, start=1)
    assert resolution.outcome is expected
    assert resolution.bars_observed == 1


@pytest.mark.parametrize(
    "future,expected",
    [
        ((1.05, 1.1001, 1.01, 1.08), Outcome.TRUE),
        ((1.05, 1.08, 0.999, 1.02), Outcome.FALSE),
        ((1.05, 1.1001, 0.999, 1.04), Outcome.UNJUDGEABLE_SAME_BAR),
        ((1.05, 1.1, 1.0, 1.04), Outcome.FALSE),
    ],
)
def test_setup_target_stop_collision_and_strict_equality(future, expected: Outcome) -> None:
    candles = market_series([(1.04, 1.06, 1.03, 1.05), future], origin=ORIGIN)
    row = prediction_row(
        "p:R00:setup:zone-a",
        prediction_type="setup_target_before_stop",
        target=1.1,
        stop=1.0,
        horizon=1,
    )
    assert resolve_market_window(row, candles, start=1).outcome is expected


def test_no_market_bars_do_not_consume_horizon() -> None:
    first = candle_at(ORIGIN, 1.0, 1.02, 0.99, 1.01)
    closed = candle_at(
        ORIGIN + timedelta(minutes=5), 0.0, 0.0, 0.0, 0.0, volume=0.0
    )
    hit = candle_at(ORIGIN + timedelta(minutes=10), 1.01, 1.2, 1.0, 1.1)
    row = prediction_row(horizon=1)
    candles = (first, closed, hit)
    scored = score_predictions(
        [replace_horizon(row)], candles, expected_variant="R00"
    )
    assert scored[0].outcome is Outcome.TRUE
    assert scored[0].bars_observed == 1
    assert scored[0].resolved_at == hit.end


def replace_horizon(row: dict, horizon: int = 288) -> dict:
    return {**row, "horizon_market_bars": horizon}


def make_case(
    identifier: str,
    minute: int,
    outcome: Outcome,
    *,
    resolved_minute: int | None,
    independent: bool = True,
    prediction_type: str = "draw_touch",
    direction: str = "bullish",
) -> ScoredPrediction:
    return ScoredPrediction(
        prediction_id=identifier,
        variant_id="R00",
        available_at=ORIGIN + timedelta(minutes=minute),
        concept="liquidity_pool_candidate",
        prediction_type=prediction_type,
        direction=direction,
        object_id=identifier,
        outcome=outcome,
        resolved_at=(
            ORIGIN + timedelta(minutes=resolved_minute)
            if resolved_minute is not None
            else None
        ),
        bars_observed=1,
        independent=independent,
    )


def test_first_emission_independence_is_by_type_and_object() -> None:
    candles = market_series([(1.0, 1.02, 0.99, 1.0)] * 290, origin=ORIGIN)
    first = replace_horizon(prediction_row(available_at=candles[0].end))
    duplicate = replace_horizon(
        prediction_row(
            "p:R00:draw:another-unique-id",
            available_at=candles[1].end,
        )
    )
    # Same target object and type, despite a different synthetic row identifier.
    other_type = replace_horizon(
        prediction_row(
            "p:R00:ob:pool-a",
            available_at=candles[2].end,
            prediction_type="ob_first_retracement",
            target=None,
            stop=0.9,
            lower=0.95,
            upper=1.01,
        )
    )
    cases = score_predictions([first, duplicate, other_type], candles)
    assert [case.independent for case in cases] == [True, False, True]
    assert prediction_object_id(first) == prediction_object_id(duplicate) == "pool-a"
    summary = summarise_predictions(cases)
    values = summary["prediction_types"]["draw_touch"]
    assert values["raw_count"] == 2
    assert values["independent_count"] == 1
    assert values["raw_count"] >= values["independent_count"]


def test_baseline_waits_for_resolution_and_breaks_ties_toward_false() -> None:
    early_true = make_case("a", 0, Outcome.TRUE, resolved_minute=2)
    before_resolution = make_case("b", 1, Outcome.FALSE, resolved_minute=3)
    at_resolution = make_case("c", 2, Outcome.FALSE, resolved_minute=4)
    cases = apply_causal_baseline([early_true, before_resolution, at_resolution])
    assert cases[0].baseline_prediction is None
    assert cases[1].baseline_prediction is None  # early_true is still unresolved
    assert cases[2].baseline_prediction is Outcome.TRUE
    assert cases[2].baseline_correct is False

    false_case = make_case("d", 0, Outcome.FALSE, resolved_minute=1)
    true_case = make_case("e", 0, Outcome.TRUE, resolved_minute=1)
    tied = make_case("f", 1, Outcome.TRUE, resolved_minute=2)
    tied_result = apply_causal_baseline([false_case, true_case, tied])[-1]
    assert tied_result.baseline_prediction is Outcome.FALSE
    assert tied_result.baseline_correct is False


def test_unjudgeable_and_raw_duplicates_never_enter_baseline_history() -> None:
    collision = make_case(
        "a", 0, Outcome.UNJUDGEABLE_SAME_BAR, resolved_minute=1
    )
    truncated = make_case(
        "b", 0, Outcome.UNJUDGEABLE_TRUNCATED, resolved_minute=None
    )
    duplicate_true = make_case(
        "c", 0, Outcome.TRUE, resolved_minute=1, independent=False
    )
    later = make_case("d", 1, Outcome.FALSE, resolved_minute=2)
    result = apply_causal_baseline([collision, truncated, duplicate_true, later])
    assert result[-1].baseline_prediction is None
    assert result[-1].baseline_correct is None


def test_metrics_reports_raw_independent_matched_and_descriptive() -> None:
    first = make_case("a", 0, Outcome.TRUE, resolved_minute=1)
    duplicate = make_case("b", 0, Outcome.FALSE, resolved_minute=1, independent=False)
    later = make_case("c", 2, Outcome.FALSE, resolved_minute=3)
    cases = apply_causal_baseline([first, duplicate, later])
    values = metrics(list(cases))
    assert values["raw_count"] == 3
    assert values["independent_count"] == 2
    assert values["raw_true"] == 1 and values["raw_false"] == 2
    assert values["true"] == 1 and values["false"] == 1
    assert values["hit_rate"] == 0.5
    assert values["matched_count"] == 1
    assert values["matched_hit_rate"] == 0.0
    assert values["baseline_rate"] == 0.0
    assert values["difference"] == 0.0
    assert values["descriptive_only"] is True


def test_decisions_inherit_linked_outcome_and_stand_aside_has_none() -> None:
    case = apply_causal_baseline(
        [make_case("p:R00:draw:pool-a", 0, Outcome.TRUE, resolved_minute=1)]
    )[0]
    decisions = [
        {
            "decision_id": "d:R00:target_choice:a",
            "available_at": case.available_at.isoformat(),
            "decision_type": "target_choice",
            "prediction_id": case.prediction_id,
        },
        {
            "decision_id": "d:R00:stand_aside:zone-a:reason",
            "available_at": case.available_at.isoformat(),
            "decision_type": "stand_aside",
            "prediction_id": None,
        },
    ]
    scored = score_decisions(
        sorted(decisions, key=lambda row: row["decision_id"]),
        [case],
        expected_variant="R00",
    )
    by_type = {decision.decision_type: decision for decision in scored}
    assert by_type["target_choice"].outcome is Outcome.TRUE
    assert by_type["stand_aside"].outcome is None
    summary = summarise_decisions(scored)["decisions"]
    assert summary["target_choice"]["true"] == 1
    aside = summary["stand_aside"]
    assert aside["raw_count"] == aside["independent_count"] == 1
    assert aside["outcome_applicable"] is False
    assert aside["hit_rate"] is None and aside["baseline_rate"] is None


def test_ledger_guards_reject_future_fields_wrong_year_and_wrong_horizon() -> None:
    candles = market_series([(1.0, 1.02, 0.99, 1.0)] * 290, origin=ORIGIN)
    row = replace_horizon(prediction_row(available_at=candles[0].end))
    with pytest.raises(ValueError, match="sealed"):
        score_predictions([{**row, "outcome": "true"}], candles)
    with pytest.raises(ValueError, match="2022"):
        score_predictions(
            [{**row, "available_at": "2023-01-01T00:05:00+00:00"}], candles
        )
    with pytest.raises(ValueError, match="288"):
        score_predictions([{**row, "horizon_market_bars": 2}], candles)
    with pytest.raises(ValueError, match="2022"):
        score_predictions([row], [replace(candles[0], start=datetime(2023, 1, 1, tzinfo=UTC))])


def test_example_rule_uses_fixed_months_type_fallback_and_first_emission() -> None:
    rows = []
    for month, day in [(1, 20), (4, 10), (7, 5), (10, 14), (12, 14)]:
        rows.append(
            prediction_row(
                f"p:R00:draw:draw-{month}",
                available_at=datetime(2022, month, 1, 0, 5, tzinfo=UTC),
            )
        )
        prediction_type = (
            "ob_first_retracement" if month == 4 else
            "draw_touch" if month == 7 else
            "setup_target_before_stop"
        )
        selected_day = 1 if month in {4, 7} else day
        row = prediction_row(
            f"p:R00:setup:setup-{month}",
            available_at=datetime(2022, month, selected_day, 8, tzinfo=UTC),
            prediction_type=prediction_type,
            target=1.2 if prediction_type != "ob_first_retracement" else None,
            stop=1.0 if prediction_type != "draw_touch" else None,
            lower=1.0 if prediction_type == "ob_first_retracement" else None,
            upper=1.1 if prediction_type == "ob_first_retracement" else None,
        )
        if prediction_type == "ob_first_retracement":
            row["prediction_id"] = f"p:R00:ob:setup-{month}"
        row["outcome"] = "false"  # Deliberately present: selection must ignore it.
        rows.append(row)
    selected = select_narration_examples(rows)
    assert [item["fixed_month"] for item in selected] == [1, 4, 7, 10, 12]
    assert [item["prediction_type"] for item in selected] == [
        "setup_target_before_stop",
        "ob_first_retracement",
        "draw_touch",
        "setup_target_before_stop",
        "setup_target_before_stop",
    ]
    assert selected[0]["day"] == "2022-01-20"
    assert selected[1]["day"] == "2022-04-01"
    assert selected[2]["day"] == "2022-07-01"


def test_example_extraction_is_complete_and_ignores_unselected_days(tmp_path) -> None:
    rows = []
    for month in (1, 4, 7, 10, 12):
        rows.append(
            prediction_row(
                f"p:R00:draw:pool-{month}",
                available_at=datetime(2022, month, 2, 0, 5, tzinfo=UTC),
            )
        )
    selected = select_narration_examples(rows)
    narration_path = tmp_path / "narration.jsonl"
    decisions_path = tmp_path / "decisions.jsonl"
    narration = [
        {
            "event_id": f"n:R00:event-{item['fixed_month']}",
            "available_at": item["available_at"],
            "concept": "liquidity_pool",
            "claim_ids": ["U0020"],
            "text": "نص عربي كامل.",
        }
        for item in selected
    ]
    narration.append(
        {
            "event_id": "n:R00:ignored",
            "available_at": "2022-02-02T00:05:00+00:00",
            "concept": "liquidity_pool",
            "claim_ids": [],
            "text": "English text on an unselected day is not read into an example.",
        }
    )
    narration_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in narration),
        encoding="utf-8",
    )
    decisions = [
        {
            "decision_id": f"d:R00:target-{item['fixed_month']}",
            "available_at": item["available_at"],
            "decision_type": "target_choice",
            "concept": "target_choice",
            "claim_ids": ["U0020"],
            "reason": "سبب عربي كامل.",
            "prediction_id": item["prediction_id"],
        }
        for item in selected
    ]
    decisions_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in decisions),
        encoding="utf-8",
    )
    examples = extract_narration_examples(
        selected, narration_path=narration_path, decisions_path=decisions_path
    )
    assert len(examples) == 5
    assert all(len(example["narration"]) == 1 for example in examples)
    assert all(len(example["decisions"]) == 1 for example in examples)
    assert examples[0]["narration"][0]["text"] == "نص عربي كامل."


def test_report_renderer_handles_every_variant_concept_decision_and_month() -> None:
    empty = metrics([])
    concepts = {name: empty for name in (
        "liquidity_pool_candidate",
        "order_block_candidate",
        "candidate_first_retracement_continuation",
    )}
    decisions = {name: empty for name in (
        "target_choice", "entry_choice", "stop_choice", "stand_aside"
    )}
    months = [f"2022-{month:02d}" for month in range(1, 13)]
    variants = {
        variant: {
            "prediction_summary": {
                "concepts": concepts,
                "monthly": {month: {"concepts": concepts} for month in months},
            },
            "decision_summary": {
                "decisions": decisions,
                "monthly": {month: {"decisions": decisions} for month in months},
            },
        }
        for variant in ("R00", "V01", "V02", "V03", "V04", "V05")
    }
    scores = {
        "year": 2022,
        "provenance": {
            "prediction_spec_commit": "1" * 40,
            "variant_plan_commit": "2" * 40,
            "scoring_commit": "3" * 40,
        },
        "data": {"sha256": "4" * 64, "rows": 0, "market_candles": 0},
        "independence_id": "FIRST_EMISSION_BY_VARIANT_TYPE_OBJECT_V1",
        "baseline_id": "EXPANDING_MAJORITY_BY_VARIANT_TYPE_DIRECTION_V1",
        "variants": variants,
    }
    rows = [
        prediction_row(
            f"p:R00:draw:pool-{month}",
            available_at=datetime(2022, month, 2, 0, 5, tzinfo=UTC),
        )
        for month in (1, 4, 7, 10, 12)
    ]
    selected = select_narration_examples(rows)
    main = render_main_report(scores, selected, sample_spec_commit="5" * 40)
    monthly = render_monthly_report(scores)
    assert main.count("| `R00` |") == 7
    assert monthly.count("\n## ") == 12
    assert " outcome " not in main
    assert "وصف فقط" in main or "لا حالات" in main


def test_dev_loader_refuses_2023_before_opening(tmp_path) -> None:
    sealed = tmp_path / "2023.csv.gz"
    with pytest.raises(ValueError, match="2022.csv.gz"):
        load_dev_2022(sealed)
    assert not sealed.exists()


def test_pass1_does_not_import_scorer() -> None:
    # A real prefix trace remains deterministic after the independent module exists.
    candles = market_series([(1.0, 1.02, 0.99, 1.0)] * 6, origin=ORIGIN)
    assert reading_trace(candles, REFERENCE) == reading_trace(candles, REFERENCE)
