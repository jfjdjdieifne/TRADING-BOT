"""Fixture tests for step B1 (swing high, swing low, fair value gap).

Run:  python3 test_fixtures.py

Expectations come from EXPECTED_FIXTURES.json, which was committed before this
file existed and is derived only from BUILD_STEP_B1_DESIGN_V2.md and
CORRECTIONS_R3. No expectation here is chosen to make a result pass.

No market data is read. No network. No pandas. No import from the old pipeline.
"""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from candle import build_candles  # noqa: E402
from fvg import fvg_at  # noqa: E402
from swing import swing_at  # noqa: E402

FIXTURES_PATH = os.path.join(HERE, "EXPECTED_FIXTURES.json")

FORBIDDEN_WORDS = ("Michael", "مايكل")
FORBIDDEN_IMPORTS = ("pandas", "numpy", "requests", "urllib", "socket", "http", "information_time")

failures = []
checks = 0


def _check(case_id, condition, message):
    global checks
    checks += 1
    if not condition:
        failures.append("%s: %s" % (case_id, message))


def _load_cases():
    with open(FIXTURES_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)["cases"]


def _evaluate(case, candles):
    concept = case["concept"]
    t = case["evaluate_at"]
    if concept == "swing_high":
        return swing_at(candles, t, "high")
    if concept == "swing_low":
        return swing_at(candles, t, "low")
    if concept == "fvg_bullish":
        return fvg_at(candles, t, "bullish")
    if concept == "fvg_bearish":
        return fvg_at(candles, t, "bearish")
    raise ValueError("unknown concept in fixtures: %s" % concept)


def _gap_ids(record):
    return [gap["id"] for gap in record.get("open_gaps", [])]


def _gate_ids(record):
    return [gate["id"] for gate in record.get("gates", [])]


def compare_case(case, record):
    case_id = case["id"]
    expected = case["expected"]

    _check(case_id, record["status"] == expected["status"],
           "status %s != expected %s" % (record["status"], expected["status"]))
    _check(case_id, record["candle_indices"] == expected["candle_indices"],
           "candle indices differ")
    _check(case_id, record["version"] == expected["version"],
           "version %s != expected %s" % (record["version"], expected["version"]))
    _check(case_id, record["tier"] == expected["tier"], "tier differs")
    _check(case_id, record["source_ids"] == expected["source_ids"],
           "source ids %s != expected %s" % (record["source_ids"], expected["source_ids"]))
    _check(case_id, record["labels"] == expected["labels"],
           "labels %s != expected %s" % (record["labels"], expected["labels"]))
    _check(case_id, _gap_ids(record) == expected["gap_ids"],
           "gap ids %s != expected %s" % (_gap_ids(record), expected["gap_ids"]))

    if "gates" in expected:
        _check(case_id, _gate_ids(record) == expected["gates"],
               "gate ids %s != expected %s" % (_gate_ids(record), expected["gates"]))

    if "bounds" in expected:
        if expected["bounds"] is None:
            _check(case_id, record["bounds"] is None, "bounds should be null")
        else:
            for key, want in expected["bounds"].items():
                got = (record["bounds"] or {}).get(key)
                _check(case_id, got == want, "bound %s is %s, expected %s" % (key, got, want))


def test_fixture_cases():
    for case in _load_cases():
        candles = build_candles(case["candles"])
        record = _evaluate(case, candles)
        compare_case(case, record)


def test_no_lookahead():
    case = [c for c in _load_cases() if c["id"] == "T-NL-1"][0]
    base = build_candles(case["candles"])
    extended = base + build_candles(case["appended_candles"])

    before = swing_at(base, case["evaluate_at"], "high")
    after = swing_at(extended, case["evaluate_at"], "high")

    _check("T-NL-1", before == after,
           "record at index %d changed after appending future candles" % case["evaluate_at"])
    _check("T-NL-1", after["status"] == case["expected"]["status"],
           "status %s != expected %s" % (after["status"], case["expected"]["status"]))
    _check("T-NL-1", len(extended) > len(base), "no future candles were appended")


def test_determinism():
    def snapshot():
        rows = []
        for case in _load_cases():
            candles = build_candles(case["candles"])
            rows.append([case["id"], _evaluate(case, candles)])
        return json.dumps(rows, ensure_ascii=False, sort_keys=True)

    first = snapshot()
    second = snapshot()
    _check("determinism", first == second, "two identical runs produced different output")


def test_no_attribution():
    blob = []
    for case in _load_cases():
        candles = build_candles(case["candles"])
        blob.append(json.dumps(_evaluate(case, candles), ensure_ascii=False))
    text = "\n".join(blob)
    for word in FORBIDDEN_WORDS:
        _check("attribution", word.lower() not in text.lower(),
               "printed record contains a forbidden attribution token")


def _imported_modules(path):
    """Real import statements only, never words inside comments or docstrings."""
    import ast

    with open(path, "r", encoding="utf-8") as handle:
        tree = ast.parse(handle.read(), filename=path)

    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name.split(".")[0].lower())
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                found.add(node.module.split(".")[0].lower())
            if node.level:  # relative import
                found.add("<relative>")
    return found


def test_module_constraints():
    for name in ("candle.py", "swing.py", "fvg.py"):
        imported = _imported_modules(os.path.join(HERE, name))
        for token in FORBIDDEN_IMPORTS:
            _check("imports/%s" % name, token not in imported,
                   "module imports a forbidden dependency: %s" % token)


def main():
    for test in (
        test_fixture_cases,
        test_no_lookahead,
        test_determinism,
        test_no_attribution,
        test_module_constraints,
    ):
        test()

    for line in failures:
        print("FAIL " + line)
    print("checks=%d failed=%d" % (checks, len(failures)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
