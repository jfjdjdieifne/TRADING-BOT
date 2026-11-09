"""Fixture tests for step C1b — the corrections on top of C1, and nothing new.

Run:  python3 test_c1b.py

Expectations come from EXPECTED_C1b.json, which was committed before any C1b code
change existed and is derived only from BUILD_STEP_C1b_SPEC.md and OWNER_DECISIONS_D2.md.
No expectation here is chosen to make a result pass, and none is edited after a run:
a mismatch is printed and counted.

No market data is read.  No network.  No pandas.  No result and no performance figure
is produced: every candle is a hand-made FIXTURE.

What is checked:
  * the gap catalog: every id of C1b spec §4, its exact text, and its print status;
  * the module-level corrections: no reference variant, honest status labels;
  * V-D-C above / below / equal to 1.5 x ATR, a short window, an unclosed candle,
    malformed input and an unknown variant id;
  * reference_variant = NONE_PER_OWNER_D2 in every displacement result;
  * the new sweep indices level_candle_index / confirm_candle_index and the kept
    swing_index;
  * the cluster notice of V-OB-3 with two and with three adjacent opposing candles;
  * the CALLER_INPUT basis of V-OB-13 / 14 / 15 and the UNDEFINED of V-D-04 / V-E-EQH.
"""

from __future__ import annotations

import importlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import common  # noqa: E402
import displacement as disp  # noqa: E402
import liquidity_sweep as sweep  # noqa: E402
import order_block as ob  # noqa: E402

FIXTURES_PATH = os.path.join(HERE, "EXPECTED_C1b.json")
TOLERANCE = 1e-9

checks = 0
failures = []


def check(case_id, condition, message):
    global checks
    checks += 1
    if not condition:
        failures.append("%s: %s" % (case_id, message))


def close(actual, expected):
    return (
        isinstance(actual, (int, float))
        and not isinstance(actual, bool)
        and abs(actual - expected) <= TOLERANCE
    )


def load_document():
    with open(FIXTURES_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


# ---------------------------------------------------------------- calls


def call_order_block(case):
    params = case["call"]
    return ob.order_block_at(
        case["candles"],
        displacement_start_index=params["displacement_start_index"],
        direction=params["direction"],
        boundaries=params.get("boundaries"),
        mean_threshold_basis=params.get("mean_threshold_basis"),
        entry_level=params.get("entry_level"),
        invalidation=params.get("invalidation"),
        prerequisites=params.get("prerequisites"),
    )


def call_sweep(case):
    params = case["call"]
    if params.get("mode") == "swing_level":
        return sweep.sweep_at_swing_level(
            case["candles"], params["t"], params["side"], params["variant"]
        )
    return sweep.sweep_at(
        case["candles"], params["t"], params["side"], params["level"], params["variant"]
    )


def call_displacement(case):
    params = case["call"]
    return disp.displacement_at(
        case["candles"], params["t"], params["variant"], params.get("previous_window")
    )


def evaluate(case):
    if case["concept"] == "order_block":
        return call_order_block(case)
    if case["concept"] == "liquidity_sweep":
        return call_sweep(case)
    if case["concept"] == "displacement":
        return call_displacement(case)
    raise ValueError("unknown concept in fixtures: %s" % case["concept"])


# ---------------------------------------------------------------- comparisons


def compare(case, record):
    case_id = case["id"]
    expected = case.get("expect", {})

    # invariants of every record
    check(case_id, record.get("tier") == "TIER2", "tier is not TIER2")
    check(
        case_id,
        record.get("status") in ("BUILT", "UNDEFINED", "PENDING"),
        "status %r is not one of BUILT / UNDEFINED / PENDING" % (record.get("status"),),
    )
    dimension_entries = record.get("dimension_gaps")
    check(case_id, isinstance(dimension_entries, list), "dimension_gaps is missing")
    for entry in dimension_entries or []:
        check(
            case_id,
            entry.get("text", "").startswith("KNOWLEDGE_GAP: "),
            "a dimension gap text does not start with KNOWLEDGE_GAP:",
        )
        check(
            case_id,
            entry.get("print_status")
            in (
                common.PRINTED_PER_RESULT,
                common.PRINTED_IN_DIMENSION_GAPS,
                common.NOT_PRINTABLE,
            ),
            "unknown dimension gap print status %r" % (entry.get("print_status"),),
        )

    if "status" in expected:
        check(
            case_id,
            record["status"] == expected["status"],
            "status %r != expected %r" % (record["status"], expected["status"]),
        )
    if "answer" in expected:
        check(
            case_id,
            record.get("answer") == expected["answer"],
            "answer %r != expected %r" % (record.get("answer"), expected["answer"]),
        )
    if "verdict" in expected:
        check(
            case_id,
            record.get("verdict") == expected["verdict"],
            "verdict %r != expected %r" % (record.get("verdict"), expected["verdict"]),
        )
    if "variant_id" in expected:
        check(
            case_id,
            record.get("variant_id") == expected["variant_id"],
            "variant id %r != expected %r" % (record.get("variant_id"), expected["variant_id"]),
        )
    if "variant_ids" in expected:
        check(
            case_id,
            record.get("variant_ids") == expected["variant_ids"],
            "variant ids %r != expected %r" % (record.get("variant_ids"), expected["variant_ids"]),
        )
    if "block_index" in expected:
        check(
            case_id,
            record.get("block_index") == expected["block_index"],
            "block index %r != expected %r" % (record.get("block_index"), expected["block_index"]),
        )
    if "numbers_is_null" in expected:
        expected_null = expected["numbers_is_null"]
        check(
            case_id,
            (record.get("numbers") is None) == expected_null,
            "numbers is %r, expected null = %r" % (record.get("numbers"), expected_null),
        )
    if "numbers" in expected:
        numbers = record.get("numbers") or {}
        for key, value in expected["numbers"].items():
            check(case_id, key in numbers, "number %r is missing from the record" % key)
            if key in numbers:
                check(
                    case_id,
                    close(numbers[key], value),
                    "number %r = %r != expected %r" % (key, numbers[key], value),
                )
    if "gap_ids" in expected:
        actual = [entry["id"] for entry in record.get("gaps", [])]
        check(
            case_id,
            actual == expected["gap_ids"],
            "gap ids %r != expected %r" % (actual, expected["gap_ids"]),
        )
    if "dimension_gap_ids" in expected:
        actual = [entry["id"] for entry in record.get("dimension_gaps", [])]
        check(
            case_id,
            actual == expected["dimension_gap_ids"],
            "dimension gap ids %r != expected %r" % (actual, expected["dimension_gap_ids"]),
        )
    if "dimension_gap_status" in expected:
        actual = {
            entry["id"]: entry["print_status"] for entry in record.get("dimension_gaps", [])
        }
        for gap_id, status in expected["dimension_gap_status"].items():
            check(
                case_id,
                actual.get(gap_id) == status,
                "dimension gap %r status %r != expected %r"
                % (gap_id, actual.get(gap_id), status),
            )
    if "reference_variant" in expected:
        check(
            case_id,
            record.get("reference_variant") == expected["reference_variant"],
            "reference_variant %r != expected %r"
            % (record.get("reference_variant"), expected["reference_variant"]),
        )
    if "flags" in expected:
        check(
            case_id,
            record.get("flags") == expected["flags"],
            "flags %r != expected %r" % (record.get("flags"), expected["flags"]),
        )
    if "cluster_notice" in expected:
        actual = record.get("cluster_notice") or {}
        for key, value in expected["cluster_notice"].items():
            check(
                case_id,
                actual.get(key) == value,
                "cluster notice %r = %r != expected %r" % (key, actual.get(key), value),
            )
    for key in ("level_candle_index", "confirm_candle_index", "swing_index"):
        if key in expected:
            check(
                case_id,
                record.get(key) == expected[key],
                "%s %r != expected %r" % (key, record.get(key), expected[key]),
            )
    if "level_basis" in expected:
        check(
            case_id,
            record.get("level_basis") == expected["level_basis"],
            "level basis %r != expected %r" % (record.get("level_basis"), expected["level_basis"]),
        )
    if "filters" in expected:
        actual = [[entry["id"], entry["result"]] for entry in record.get("filters", [])]
        check(
            case_id,
            actual == expected["filters"],
            "filters %r != expected %r" % (actual, expected["filters"]),
        )
    if "filter_bases" in expected:
        actual = {entry["id"]: entry["basis"] for entry in record.get("filters", [])}
        for filter_id, basis in expected["filter_bases"].items():
            check(
                case_id,
                actual.get(filter_id) == basis,
                "filter %r basis %r != expected %r" % (filter_id, actual.get(filter_id), basis),
            )
    if "source_number_names" in expected:
        actual = [entry["name"] for entry in record.get("source_numbers", [])]
        check(
            case_id,
            actual == expected["source_number_names"],
            "source number names %r != expected %r" % (actual, expected["source_number_names"]),
        )
    if "claim_ids_include" in expected:
        for claim_id in expected["claim_ids_include"]:
            check(
                case_id,
                claim_id in record.get("claim_ids", []),
                "claim id %r is missing from the record" % claim_id,
            )


def run_case(case):
    case_id = case["id"]
    if "raises" in case:
        try:
            record = evaluate(case)
        except ValueError as error:
            check(
                case_id,
                case["raises"] in str(error),
                "raised %r, expected a message containing %r" % (str(error), case["raises"]),
            )
        except Exception as error:  # noqa: BLE001 - a wrong exception type is a failure
            check(case_id, False, "raised %r instead of ValueError" % (error,))
        else:
            check(
                case_id,
                False,
                "did not raise, returned status %r" % (record.get("status"),),
            )
        return
    compare(case, evaluate(case))


# ---------------------------------------------------------------- catalog and modules


def check_catalog(catalog):
    expected_ids = catalog["gap_ids"]
    check("CATALOG-COUNT", len(common.GAPS) == catalog["gap_count"],
          "GAPS holds %d ids, expected %d" % (len(common.GAPS), catalog["gap_count"]))
    check("CATALOG-COUNT", len(expected_ids) == catalog["gap_count"],
          "the expectation lists %d ids, expected %d" % (len(expected_ids), catalog["gap_count"]))
    check("CATALOG-SET", set(common.GAPS) == set(expected_ids),
          "GAPS ids %r != expected ids %r" % (sorted(common.GAPS), sorted(expected_ids)))
    check("CATALOG-PROMISE-SET", set(common.GAP_PROMISE) == set(common.GAPS),
          "GAP_PROMISE does not cover exactly the catalog ids")
    for gap_id in expected_ids:
        text = common.GAPS.get(gap_id)
        check("CATALOG-%s" % gap_id, text is not None, "the gap id is missing from GAPS")
        if text is not None:
            check("CATALOG-%s" % gap_id, text.startswith(catalog["text_prefix"]),
                  "the gap text does not start with %r" % catalog["text_prefix"])
            check("CATALOG-%s" % gap_id, common.gap(gap_id)["text"] == text,
                  "gap() does not return the catalog text")
        promise = common.GAP_PROMISE.get(gap_id) or {}
        check("CATALOG-%s" % gap_id,
              promise.get("print_status") == catalog["print_status"][gap_id],
              "print status %r != expected %r"
              % (promise.get("print_status"), catalog["print_status"][gap_id]))
        check("CATALOG-%s" % gap_id,
              isinstance(promise.get("dimension"), str) and promise.get("dimension"),
              "the gap does not name the dimension that promises it")
    counts = {}
    for promise in common.GAP_PROMISE.values():
        counts[promise["print_status"]] = counts.get(promise["print_status"], 0) + 1
    for status, expected_count in catalog["print_status_counts"].items():
        check("CATALOG-COUNT-%s" % status,
              counts.get(status) == expected_count,
              "print status %r holds %r ids, expected %r"
              % (status, counts.get(status), expected_count))
    check("CATALOG-CONSTANTS",
          common.PRINTED_PER_RESULT == "PRINTED_PER_RESULT"
          and common.PRINTED_IN_DIMENSION_GAPS == "PRINTED_IN_DIMENSION_GAPS"
          and common.NOT_PRINTABLE == "NOT_PRINTABLE",
          "the print status constants changed")
    for concept in ("order_block", "displacement", "liquidity_sweep"):
        entries = common.dimension_gaps(concept)
        check("CATALOG-DIM-%s" % concept, len(entries) == len(common.gap_ids_of(concept)),
              "dimension_gaps(%r) length mismatch" % concept)


def check_modules(module_checks):
    for entry in module_checks:
        case_id = entry["id"]
        module = importlib.import_module(entry["module"])
        for name in entry.get("absent", []):
            check(case_id, not hasattr(module, name), "%s still defines %s" % (entry["module"], name))
        for name in entry.get("present", []):
            check(case_id, hasattr(module, name), "%s does not define %s" % (entry["module"], name))
        for name, value in entry.get("equals", {}).items():
            actual = getattr(module, name, "<missing>")
            check(case_id, actual == value,
                  "%s.%s = %r != expected %r" % (entry["module"], name, actual, value))
        for fragment in entry.get("source_absent", []):
            path = os.path.join(HERE, module.__name__ + ".py")
            with open(path, "r", encoding="utf-8") as handle:
                text = handle.read()
            check(case_id, fragment not in text,
                  "%s.py still contains %r" % (module.__name__, fragment))


# ---------------------------------------------------------------- main


def main():
    document = load_document()
    check_catalog(document["catalog"])
    check_modules(document["module_checks"])
    cases = document["cases"]
    for case in cases:
        run_case(case)

    print("cases: %d" % len(cases))
    print("module checks: %d" % len(document["module_checks"]))
    print("catalog gap ids: %d" % len(document["catalog"]["gap_ids"]))
    print("checks: %d" % checks)
    print("failures: %d" % len(failures))
    if failures:
        print("")
        print("MISMATCHES (expectations were not edited):")
        for failure in failures:
            print("  - %s" % failure)
        return 1
    print("")
    print("ALL EXPECTATIONS MET")
    return 0


if __name__ == "__main__":
    sys.exit(main())
