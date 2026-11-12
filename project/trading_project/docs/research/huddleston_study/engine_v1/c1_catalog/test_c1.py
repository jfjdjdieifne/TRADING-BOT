"""Fixture tests for step C1 (order block, liquidity sweep, displacement).

Run:  python3 test_c1.py

Expectations come from EXPECTED_C1.json, which was committed before this file
existed and is derived only from BUILD_STEP_C1_SPEC.md and the sources the spec
quotes.  No expectation here is chosen to make a result pass, and none was edited
after a run.

No market data is read.  No network.  No pandas.  No import from the old
pipeline.  No result and no performance figure is produced: the fixtures are
hand-made candles, tagged FIXTURE, except the one SOURCE_EXAMPLE that carries the
claim id it comes from.
"""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import displacement as disp  # noqa: E402
import liquidity_sweep as sweep  # noqa: E402
import order_block as ob  # noqa: E402

FIXTURES_PATH = os.path.join(HERE, "EXPECTED_C1.json")
TOLERANCE = 1e-9

FORBIDDEN_WORDS = ("Michael", "\u0645\u0627\u064a\u0643\u0644")
FORBIDDEN_IMPORTS = ("pandas", "numpy", "requests", "urllib", "socket", "http", "information_time")

checks = 0
failures = []


def check(case_id, condition, message):
    global checks
    checks += 1
    if not condition:
        failures.append("%s: %s" % (case_id, message))


def close(actual, expected):
    return isinstance(actual, (int, float)) and not isinstance(actual, bool) and abs(actual - expected) <= TOLERANCE


def load_cases():
    with open(FIXTURES_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)["cases"]


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


def compare(case, record):
    case_id = case["id"]
    expected = case.get("expect", {})

    # invariants of every record
    check(case_id, record.get("tier") == "TIER2", "tier is not TIER2")
    check(case_id, record.get("status") in ("BUILT", "UNDEFINED", "PENDING"),
          "status %r is not one of BUILT / UNDEFINED / PENDING" % (record.get("status"),))
    claim_ids = record.get("claim_ids")
    check(case_id, isinstance(claim_ids, list) and len(claim_ids) > 0, "claim ids are missing")
    check(case_id, claim_ids == sorted(set(claim_ids)), "claim ids are not sorted and unique")
    dumped = json.dumps(record, ensure_ascii=False)
    for word in FORBIDDEN_WORDS:
        check(case_id, word not in dumped, "a forbidden word appears in the record")
    check(case_id, "FLAGGED_FOR_OWNER_OVERRIDE" in record.get("flags", []) or
          case["concept"] != "order_block", "the owner-override flag is missing")

    if "status" in expected:
        check(case_id, record["status"] == expected["status"],
              "status %r != expected %r" % (record["status"], expected["status"]))
    if "verdict" in expected:
        check(case_id, record["verdict"] == expected["verdict"],
              "verdict %r != expected %r" % (record["verdict"], expected["verdict"]))
    if "answer" in expected:
        check(case_id, record["answer"] == expected["answer"],
              "answer %r != expected %r" % (record["answer"], expected["answer"]))
    if "block_index" in expected:
        check(case_id, record["block_index"] == expected["block_index"],
              "block index %r != expected %r" % (record["block_index"], expected["block_index"]))
    if "variant_ids" in expected:
        check(case_id, record["variant_ids"] == expected["variant_ids"],
              "variant ids %r != expected %r" % (record["variant_ids"], expected["variant_ids"]))
    if "variant_id" in expected:
        check(case_id, record["variant_id"] == expected["variant_id"],
              "variant id %r != expected %r" % (record["variant_id"], expected["variant_id"]))
    if "numbers" in expected:
        numbers = record.get("numbers") or {}
        for key, value in expected["numbers"].items():
            check(case_id, key in numbers, "number %r is missing from the record" % key)
            if key in numbers:
                check(case_id, close(numbers[key], value),
                      "number %r = %r != expected %r" % (key, numbers[key], value))
    if "filters" in expected:
        actual = [[item["id"], item["result"]] for item in record.get("filters", [])]
        check(case_id, actual == expected["filters"],
              "filters %r != expected %r" % (actual, expected["filters"]))
    if "invalidation_label" in expected:
        invalidation = record.get("invalidation") or {}
        check(case_id, invalidation.get("label") == expected["invalidation_label"],
              "invalidation label %r != expected %r" % (invalidation.get("label"), expected["invalidation_label"]))
    if "invalidation_index" in expected:
        invalidation = record.get("invalidation") or {}
        check(case_id, invalidation.get("at_index") == expected["invalidation_index"],
              "invalidation index %r != expected %r" % (invalidation.get("at_index"), expected["invalidation_index"]))
    if "gap_ids" in expected:
        actual = [entry["id"] for entry in record.get("gaps", [])]
        check(case_id, actual == expected["gap_ids"],
              "gap ids %r != expected %r" % (actual, expected["gap_ids"]))
        for entry in record.get("gaps", []):
            check(case_id, entry["text"].startswith("KNOWLEDGE_GAP: "),
                  "a gap text does not start with KNOWLEDGE_GAP:")
    if "claim_ids_include" in expected:
        for claim_id in expected["claim_ids_include"]:
            check(case_id, claim_id in record["claim_ids"],
                  "claim id %r is missing from the record" % claim_id)
    if "level_basis" in expected:
        check(case_id, record.get("level_basis") == expected["level_basis"],
              "level basis %r != expected %r" % (record.get("level_basis"), expected["level_basis"]))
    if "swing_index" in expected:
        check(case_id, record.get("swing_index") == expected["swing_index"],
              "swing index %r != expected %r" % (record.get("swing_index"), expected["swing_index"]))


def run_case(case):
    case_id = case["id"]
    if "raises" in case:
        try:
            record = evaluate(case)
        except ValueError as error:
            check(case_id, case["raises"] in str(error),
                  "raised %r, expected a message containing %r" % (str(error), case["raises"]))
        except Exception as error:  # noqa: BLE001 - a wrong exception type is a failure
            check(case_id, False, "raised %r instead of ValueError" % (error,))
        else:
            check(case_id, False, "did not raise, returned status %r" % (record.get("status"),))
        return
    record = evaluate(case)
    compare(case, record)


def scan_sources():
    """The step must not import data or network libraries, and must not name a person."""

    modules = ("common.py", "order_block.py", "liquidity_sweep.py", "displacement.py")
    for name in modules + ("test_c1.py",):
        path = os.path.join(HERE, name)
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
        for module in FORBIDDEN_IMPORTS:
            check("SOURCE-SCAN", ("import %s" % module) not in text,
                  "%s imports %s" % (name, module))
    # The checker itself holds the forbidden tokens as data, so it is not scanned for them.
    for name in modules:
        path = os.path.join(HERE, name)
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
        for word in FORBIDDEN_WORDS:
            check("SOURCE-SCAN", word not in text, "%s contains a forbidden word" % name)


def variant_counts(cases):
    counts = {}
    for case in cases:
        params = case.get("call", {})
        labels = []
        if case["concept"] == "order_block":
            for key in ("boundaries", "mean_threshold_basis", "entry_level", "invalidation"):
                if params.get(key):
                    labels.append(params[key])
        elif "variant" in params:
            labels.append(params["variant"])
        for label in labels:
            counts.setdefault(label, 0)
            counts[label] += 1
    return counts


def main():
    cases = load_cases()
    scan_sources()
    for case in cases:
        run_case(case)

    counts = variant_counts(cases)
    print("cases: %d" % len(cases))
    print("checks: %d" % checks)
    print("failures: %d" % len(failures))
    print("fixtures per coded variant:")
    for label in sorted(counts):
        print("  %-8s %d" % (label, counts[label]))
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
