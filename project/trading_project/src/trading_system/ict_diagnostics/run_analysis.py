"""Run the frozen post-stop and v2 diagnostics on pinned 2022 data only."""

from __future__ import annotations

import argparse
import gzip
import io
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from trading_system.ict_engine.pass1_emit import _write_auxiliary
from trading_system.ict_engine.predictions import (
    read_prediction_ledger,
    write_prediction_ledger,
)
from trading_system.ict_engine.score_ledger import _write_outcomes, load_dev_2022
from trading_system.ict_engine.scoring import MarketBars, score_predictions
from trading_system.ict_engine.variants import VARIANT_BY_ID

from .common import sha256_file, write_json, write_jsonl
from .context import build_variant_context
from .direction import count_barrier_results, direction_rows_for_case
from .post_stop import analyze_post_stop_case, summarise_post_stop
from .prediction_v2 import (
    entry_pair_rows,
    entry_pair_summary,
    liquidity_choice_rows,
    liquidity_summary,
    stand_aside_rows,
    stand_aside_summary,
)

EXPECTED_LEGACY = {
    "R00": (
        "cc778c815782297fab205c279c0c92872a326c96bb9e03d9c6dc04ff73f02fcb",
        "6dfc164cd92b8ccbbe857b602bdef3c53c4a17f2d50fe657d886bbb9b1571bae",
        "09b3f49256cce652245e1e75382e6bf25e501e94e59d76486027eadb5393890b",
    ),
    "V01": (
        "7cbe8736b879cbf861522243b8976fa4f2e50abed23914fcb9419d3be02f21b7",
        "b9fe8ebb9256f33fc7d792f394b602b9aaa4186c4b822bef173f16fec7bc03b1",
        "80cbc91c8e0c13d1127170fbe7cb31b8d9b7e7f5066345922a4095351212abf1",
    ),
    "V02": (
        "577ec498ab39edde391ecdddaef4683f717775e69c14aef89c6024c1c038a180",
        "dcd9f0167d30ec2c2f08e0d10ea4521568b62b3d0c7cf84bdc66dc6dee65a64c",
        "c426a48b4cb7794bb947be92f2838de91eaa26e932068a559282ba7c205250da",
    ),
    "V03": (
        "2e297c09b696f09e104ac0588420f3eceaf93332498735bc853de4129112e184",
        "49317478d4a2553a3541411a45141bf813af4cd1a75fbbc7e190a261be976dc8",
        "6f891c904f27216306eac4c311b84f290176f3eb3694c20f5c4dcc309ffeb6a1",
    ),
    "V04": (
        "4c8f9cf1f5af9c51e65d314e10a05aa672b196d07085723738f2cbb37c950762",
        "6f5576174b6d72e17138cddd3e07aabd8400aaa76659eb21f3c9da872cbc07a6",
        "a849d650edc056dc9cc2e78bc86ed42d8c120056ddbf85eca2a799b79de943d1",
    ),
    "V05": (
        "2292d46fa4e045075a3c749a1cf0788c48fbfa4beeb70e116a0fa4ea1382dfeb",
        "5e55122b297b9fcc95e2a5b806b3ec3d19ccb5998dd48d8fb77b8e1313eca5e2",
        "286bd4b3e17b0d79d80ec4183fdb5100f31452b9c553acf6f4085ed31063de96",
    ),
}


def _gzip_text_writer(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = path.open("wb")
    compressed = gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0)
    text = io.TextIOWrapper(compressed, encoding="utf-8", newline="\n")
    return raw, compressed, text


def _write_candle_rows(handle, rows: list[dict[str, Any]]) -> None:
    for row in rows:
        handle.write(
            json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        )
        handle.write("\n")


def _direction_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {"rows": len(rows), "arms": {}}
    for arm in ["engine", "random_same_month_same_direction", "opposite_direction_same_time"]:
        counts = count_barrier_results(rows, arm)
        judgeable = counts["DIRECTION_FIRST"] + counts["OPPOSITE_FIRST"]
        result["arms"][arm] = {
            **counts,
            "judgeable": judgeable,
            "direction_first_rate": counts["DIRECTION_FIRST"] / judgeable if judgeable else None,
        }
    paired = [row for row in rows if row["paired_engine_random_judgeable"]]
    engine_hits = sum(row["engine"]["outcome"] == "DIRECTION_FIRST" for row in paired)
    random_hits = sum(row["random_same_month_same_direction"]["outcome"] == "DIRECTION_FIRST" for row in paired)
    result["paired_engine_random"] = {
        "count": len(paired),
        "engine_direction_first": engine_hits,
        "random_direction_first": random_hits,
        "difference": (engine_hits - random_hits) / len(paired) if paired else None,
    }
    return result


def run_variant(
    candles,
    variant_id: str,
    output_root: Path,
) -> dict[str, Any]:
    variant = VARIANT_BY_ID[variant_id]
    print(f"بدأت مقدمة {variant_id}...", flush=True)
    context = build_variant_context(candles, variant)
    ledger_root = output_root / "ledgers"
    ledger_root.mkdir(parents=True, exist_ok=True)
    prediction_path = ledger_root / f"m2_{variant_id}_predictions.jsonl"
    decision_path = ledger_root / f"m2_{variant_id}_decisions.jsonl"
    outcome_path = ledger_root / f"m3_{variant_id}_outcomes.jsonl"
    predictions = tuple(
        prediction for reading in context.readings for prediction in reading.predictions
    )
    decisions = tuple(
        decision for reading in context.readings for decision in reading.decisions
    )
    write_prediction_ledger(prediction_path, predictions)
    _write_auxiliary(decision_path, decisions)
    rows = list(read_prediction_ledger(prediction_path))
    scored = score_predictions(rows, candles, expected_variant=variant_id)
    _write_outcomes(outcome_path, scored)
    actual_hashes = tuple(sha256_file(path) for path in [prediction_path, decision_path, outcome_path])
    if actual_hashes != EXPECTED_LEGACY[variant_id]:
        raise ValueError(f"Legacy ledger hash mismatch for {variant_id}: {actual_hashes}")
    print(f"طابقت بصمات {variant_id} القديمة؛ بدأ التحليل.", flush=True)

    market = MarketBars.from_candles(candles)
    destination = output_root / "diagnostics" / variant_id
    destination.mkdir(parents=True, exist_ok=True)
    scored_by_id = {case.prediction_id: case for case in scored}
    setups = [entry for entry in context.entries if entry.prediction is not None]
    month_indices: dict[str, list[int]] = defaultdict(list)
    for index, candle in enumerate(market.candles):
        month_indices[candle.end.strftime("%Y-%m")].append(index)

    cases: list[dict[str, Any]] = []
    direction_rows: list[dict[str, Any]] = []
    candle_path = destination / "post_stop_candles.jsonl.gz"
    raw, compressed, text = _gzip_text_writer(candle_path)
    candle_count = 0
    try:
        for entry in setups:
            case, candle_rows = analyze_post_stop_case(entry, variant, market)
            old = scored_by_id[case["case_id"]]
            if (
                case["original"]["engine_outcome"] != old.outcome.value
                or case["original"]["resolved_at"] != (old.resolved_at.isoformat() if old.resolved_at else None)
                or case["original"]["bars_from_entry"] != old.bars_observed
            ):
                raise ValueError(f"Original resolution mismatch: {case['case_id']}")
            _write_candle_rows(text, candle_rows)
            candle_count += len(candle_rows)
            cases.append(case)
            month = case["month"]
            entry_index = market.start_after(entry.available_at) - 1
            candidates = tuple(index for index in month_indices[month] if index != entry_index)
            direction_rows.extend(direction_rows_for_case(entry, variant.basis, market, candidates))
        text.flush()
        compressed.flush()
    finally:
        text.close()
        compressed.close()
        raw.close()

    case_path = destination / "post_stop_cases.jsonl"
    direction_path = destination / "direction_rows.jsonl"
    write_jsonl(case_path, cases)
    write_jsonl(direction_path, direction_rows)

    liquidity = liquidity_choice_rows(context.entries, variant, market)
    pairs, pair_exclusions = entry_pair_rows(context.entries, variant, market)
    aside = stand_aside_rows(context.entries, variant, market)
    liquidity_path = destination / "v2_liquidity.jsonl"
    pairs_path = destination / "v2_entry_pairs.jsonl"
    aside_path = destination / "v2_stand_aside.jsonl"
    write_jsonl(liquidity_path, liquidity)
    write_jsonl(pairs_path, pairs)
    write_jsonl(aside_path, aside)
    write_json(destination / "v2_entry_pair_exclusions.json", pair_exclusions)

    monthly_post: dict[str, Any] = {}
    for month in sorted({case["month"] for case in cases}):
        monthly_post[month] = summarise_post_stop([case for case in cases if case["month"] == month])
    monthly_direction: dict[str, Any] = {}
    for month in sorted({row["month"] for row in direction_rows}):
        monthly_direction[month] = _direction_summary([row for row in direction_rows if row["month"] == month])
    monthly_v2: dict[str, Any] = {}
    for month in sorted({entry.available_at.strftime("%Y-%m") for entry in context.entries}):
        monthly_v2[month] = {
            "liquidity": liquidity_summary([row for row in liquidity if row["month"] == month]),
            "entry_pairs": entry_pair_summary([row for row in pairs if row["month"] == month]),
            "stand_aside": stand_aside_summary([row for row in aside if row["month"] == month]),
        }

    summary = {
        "variant_id": variant_id,
        "post_stop": summarise_post_stop(cases),
        "monthly_post_stop": monthly_post,
        "direction": _direction_summary(direction_rows),
        "monthly_direction": monthly_direction,
        "v2_liquidity": liquidity_summary(liquidity),
        "v2_entry_pairs": entry_pair_summary(pairs),
        "v2_entry_pair_exclusions": dict(Counter(item["reason"] for item in pair_exclusions)),
        "v2_stand_aside": stand_aside_summary(aside),
        "monthly_v2": monthly_v2,
        "target_rule_consequences": dict(Counter(case["target_audit"]["rule_consequence"] for case in cases)),
        "legacy": {
            "predictions": {"path": str(prediction_path), "rows": len(rows), "sha256": actual_hashes[0]},
            "decisions": {"path": str(decision_path), "rows": len(decisions), "sha256": actual_hashes[1]},
            "outcomes": {"path": str(outcome_path), "rows": len(scored), "sha256": actual_hashes[2]},
        },
        "artifacts": {},
    }
    for path in [case_path, candle_path, direction_path, liquidity_path, pairs_path, aside_path]:
        summary["artifacts"][path.name] = {
            "path": str(path),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    summary["candle_rows"] = candle_count
    write_json(destination / "summary.json", summary)
    print(
        f"اكتمل {variant_id}: حالات {len(cases)}، شموع {candle_count}، "
        f"سيولة {len(liquidity)}، أزواج {len(pairs)}، امتناع {len(aside)}.",
        flush=True,
    )
    return summary


def run_all(
    *,
    data_path: str | Path,
    output_root: str | Path,
    variants: list[str],
    implementation_commit: str,
) -> dict[str, Any]:
    if not re.fullmatch(r"[0-9a-f]{40}", implementation_commit):
        raise ValueError("A full implementation commit is required")
    batch = load_dev_2022(data_path)
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {
        "year": 2022,
        "spec_commit": "f7a4fd4ff2f617193b1859f9a768d9c437c0b96c",
        "implementation_commit": implementation_commit,
        "data": {"path": str(data_path), "sha256": sha256_file(data_path), "candles": len(batch.candles)},
        "variants": {},
    }
    for variant_id in variants:
        result["variants"][variant_id] = run_variant(batch.candles, variant_id, root)
    combined_path = root / "combined_results.json"
    write_json(combined_path, result)
    result["combined_output"] = {"path": str(combined_path), "sha256": sha256_file(combined_path)}
    return result


def _parser():
    parser = argparse.ArgumentParser(description="تشخيص 2022 المستقل دون تعديل المحرك")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--variants", nargs="+", choices=list(VARIANT_BY_ID), default=list(VARIANT_BY_ID))
    parser.add_argument("--implementation-commit", required=True)
    return parser


def main() -> None:
    arguments = _parser().parse_args()
    result = run_all(
        data_path=arguments.input,
        output_root=arguments.output_root,
        variants=arguments.variants,
        implementation_commit=arguments.implementation_commit,
    )
    print(json.dumps(result["combined_output"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
