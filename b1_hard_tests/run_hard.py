#!/usr/bin/env python3
"""Offline, text-derived B1 red-team tests; frozen expectations are read-only.

Run from any directory: python3 b1_hard_tests/run_hard.py
All valid FIXTURE prices are integer ticks. The detailed JSONL audit is written
outside the checkout. No market data, external packages, or network are used.
"""
from __future__ import annotations

import copy
import hashlib
import itertools
import json
import os
from collections import Counter
from pathlib import Path
import random
import sys
from types import SimpleNamespace

# Importing the read-only target must not create __pycache__ inside its directory.
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ENGINE = ROOT / "project/trading_project/docs/research/huddleston_study/engine_v1/b1_candles"
sys.path.insert(0, str(ENGINE))
from candle import Candle  # noqa: E402
from fvg import fvg_at  # noqa: E402
from swing import swing_at  # noqa: E402

with (HERE / "hard_expectations.json").open(encoding="utf-8") as f:
    PLAN = json.load(f)

KINDS = ("swing_high", "swing_low", "bullish_fvg", "bearish_fvg")
PRIORITY_QUESTIONS = {"Q_MIXED", "Q_OPEN_FAIL", "Q_OPEN_EQUAL", "Q_OPEN_MIXED"}
FAMILIES = ("A", "B", "C", "D", "E", "F", "PRECEDENCE_CHOICE")
LOG_DIR = Path(os.environ.get("B1_HARD_LOG_DIR", str(Path.home() / "b1_hard_test_logs"))).resolve()
if LOG_DIR == ROOT or ROOT in LOG_DIR.parents:
    raise ValueError("B1_HARD_LOG_DIR must be outside the repository")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = LOG_DIR / "hard_observations.jsonl"
RESULTS_PATH = HERE / "HARD_RESULTS.md"


def stable_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def one_line(value):
    return stable_json(value).replace("|", "\\|")


def make_candle(low, high, opened=None, closed_price=None, closed=True):
    return Candle(open=low if opened is None else opened, high=high, low=low,
                  close=high if closed_price is None else closed_price, closed=closed)


def valid_candles(rows):
    """Construct from integer-valued fixtures without float conversion."""
    out = []
    for row in rows:
        for field in ("open", "high", "low", "close"):
            if type(row[field]) is not int:
                raise AssertionError("valid FIXTURE prices must be integer ticks")
        if type(row["closed"]) is not bool:
            raise AssertionError("valid FIXTURE closed must be a boolean")
        out.append(Candle(**row))
    return out


def raw_observation(candles, i, kind):
    """Invoke the actual event-time interface at C3=i+1, preserving errors."""
    try:
        if kind == "swing_high":
            value = swing_at(candles, i + 1, "high")
        elif kind == "swing_low":
            value = swing_at(candles, i + 1, "low")
        elif kind == "bullish_fvg":
            value = fvg_at(candles, i + 1, "bullish")
        elif kind == "bearish_fvg":
            value = fvg_at(candles, i + 1, "bearish")
        else:
            raise AssertionError("unknown direction")
        return {"type": "return", "value": value}
    except Exception as exc:  # Invalid-input observations must be retained.
        return {"type": "error", "error": type(exc).__name__, "message": str(exc)}


def short_outcome(outcome):
    if outcome["type"] == "error":
        return {"raised": outcome["error"], "message": outcome["message"]}
    v = outcome["value"]
    if not isinstance(v, dict):
        return {"returned_nonrecord": repr(v)}
    return {"status": v.get("status"), "bounds": bounds_of(v),
            "indices": v.get("candle_indices")}


def bounds_of(record):
    if not isinstance(record, dict) or record.get("bounds") is None:
        return None
    try:
        return [record["bounds"]["lower_bound"]["value"],
                record["bounds"]["upper_bound"]["value"]]
    except (KeyError, TypeError):
        return {"malformed_bounds": record.get("bounds")}


def result_value(outcome):
    return outcome.get("value") if outcome["type"] == "return" else None


def status_of(outcome):
    value = result_value(outcome)
    return value.get("status") if isinstance(value, dict) else None


class Reporter:
    def __init__(self, log):
        self.log = log
        self.counts = {family: Counter() for family in FAMILIES}
        self.details = {family: [] for family in FAMILIES}
        self.rule_checks = Counter()
        self.metrics = Counter()
        self.priority_specs = {p["id"]: p for p in PLAN["PRECEDENCE_CHOICE"]}
        self.priority_returns = {p["id"]: Counter() for p in PLAN["PRECEDENCE_CHOICE"]}
        self.priority_origins = {p["id"]: Counter() for p in PLAN["PRECEDENCE_CHOICE"]}
        self.priority_examples = {p["id"]: {} for p in PLAN["PRECEDENCE_CHOICE"]}

    def write_log(self, item):
        self.log.write(stable_json(item) + "\n")

    def case(self, family, case_id, verdict, expected, actual, question=None, **extra):
        assert verdict in ("PASS", "FAIL", "TEXT_SILENT")
        item = {"family": family, "case": case_id, "verdict": verdict,
                "expected": expected, "actual": actual, "fixture_label": "FIXTURE"}
        if question:
            item["exact_question"] = question
        item.update(extra)
        self.counts[family][verdict] += 1
        if verdict != "PASS":
            self.details[family].append(item)
        self.write_log(item)

    def output_contract(self, record, kind, case_id, run_number, unchanged, identical):
        """One F case per actual detector result, including repeat calls."""
        violations = {}
        rules = PLAN["F_output_rules"]
        self.rule_checks["input_unchanged"] += 1
        self.rule_checks["two_runs_identical"] += 1
        if not unchanged:
            violations["input_unchanged"] = False
        if not identical:
            violations["two_runs_identical"] = False
        if not isinstance(record, dict):
            violations["record"] = repr(record)
        else:
            self.rule_checks["tier"] += 1
            if record.get("tier") != rules["tier"]:
                violations["tier"] = record.get("tier")
            self.rule_checks["source_ids"] += 1
            found = record.get("source_ids")
            required = rules["source_ids"][kind]
            if not isinstance(found, list) or not set(required).issubset(set(found)):
                violations["source_ids"] = {"required": required, "actual": found}
            self.rule_checks["forbidden_name"] += 1
            try:
                serialized = stable_json(record).casefold()
            except (TypeError, ValueError):
                serialized = repr(record).casefold()
            if rules["forbidden_name"].casefold() in serialized or "مايكل" in serialized:
                violations["forbidden_name"] = "present"
            if kind == "swing_low":
                self.rule_checks["weak_support"] += 1
                if rules["swing_low_support"] not in record.get("labels", []):
                    violations["weak_support"] = record.get("labels")
            if kind in ("bullish_fvg", "bearish_fvg"):
                self.rule_checks["invalidation"] += 1
                gates = record.get("gates", [])
                gate_ids = [x.get("id") for x in gates if isinstance(x, dict)]
                if rules["fvg_invalidation"] not in gate_ids:
                    violations["invalidation"] = gates
        self.metrics["F_detector_records"] += 1
        if violations:
            self.case("F", f"{case_id}/repeat-{run_number}", "FAIL",
                      "all applicable output, mutation and repeatability rules", violations)
        else:
            # Passing F records are counted individually; logging all of them
            # would duplicate every already logged status/property observation.
            self.counts["F"]["PASS"] += 1

    def call(self, candles, i, kind, case_id):
        """Run twice on independent copies; audit both results and both inputs."""
        first_input = copy.deepcopy(candles)
        second_input = copy.deepcopy(candles)
        first = raw_observation(first_input, i, kind)
        first_unchanged = first_input == candles
        second = raw_observation(second_input, i, kind)
        second_unchanged = second_input == candles
        identical = first == second
        self.metrics["detector_call_pairs"] += 1
        for n, outcome, unchanged in ((1, first, first_unchanged), (2, second, second_unchanged)):
            if outcome["type"] == "return":
                self.output_contract(outcome["value"], kind, case_id, n, unchanged, identical)
            else:
                self.metrics["exception_execution_audits"] += 1
                if not unchanged or not identical:
                    self.case("F", f"{case_id}/error-repeat-{n}", "FAIL",
                              "exception leaves input unchanged and repeats identically",
                              {"input_unchanged": unchanged, "identical": identical,
                               "outcome": short_outcome(outcome)})
        return first

    def priority(self, candles, i, kind, outcome, origin, case_id):
        a, b, c = candles[i - 1:i + 2]
        field = "high" if kind == "swing_high" else "low"
        sign = 1 if field == "high" else -1
        def relation(neighbour):
            delta = sign * (getattr(b, field) - getattr(neighbour, field))
            return "F" if delta > 0 else "E" if delta == 0 else "X"
        left, right = relation(a), relation(c)
        group = ("SH" if kind == "swing_high" else "SL") + "-" + left + "-" + right + "-" + ("C" if c.closed else "O")
        if group not in self.priority_specs:
            raise AssertionError("unexpected priority case: " + group)
        actual = short_outcome(outcome)
        if outcome["type"] == "return" and isinstance(outcome["value"], dict):
            summary = "status=" + str(outcome["value"].get("status"))
        else:
            summary = stable_json(actual)
        self.priority_returns[group][summary] += 1
        self.priority_origins[group][origin] += 1
        self.priority_examples[group].setdefault(summary, {"case": case_id, "actual": actual})
        self.write_log({"family": "PRECEDENCE_CHOICE", "observation": case_id,
                        "group": group, "origin": origin, "expected": "TEXT_SILENT",
                        "exact_question": self.priority_specs[group]["exact_question"],
                        "actual": actual, "fixture_label": "FIXTURE",
                        "window": candle_window(candles, i)})
        self.metrics["priority_observations"] += 1
        self.metrics["priority_" + origin] += 1

    def finish_priority(self):
        for case_id, spec in self.priority_specs.items():
            actual = {"return_counts": dict(self.priority_returns[case_id]),
                      "observations": sum(self.priority_returns[case_id].values()),
                      "origins": dict(self.priority_origins[case_id]),
                      "examples": self.priority_examples[case_id]}
            self.case("PRECEDENCE_CHOICE", case_id, "TEXT_SILENT", "TEXT_SILENT", actual,
                      spec["exact_question"], relations=spec["relations"])


def candle_window(candles, i):
    if candles is None or i < 1 or i + 1 >= len(candles):
        return None
    rows = []
    for c in candles[i - 1:i + 2]:
        if c is None:
            rows.append(None)
        else:
            rows.append({k: getattr(c, k, "<missing>") for k in ("open", "high", "low", "close", "closed")})
    return rows


def text_oracle(candles, i, kind):
    """Independent reference from V2 §4.3/§4.5 and §5.3/§5.5.

    It never ranks competing NO/UNDECIDED/PENDING conditions. That silence
    is returned explicitly so no implementation choice is smuggled into D.
    """
    if i < 1:
        return {"status": "TEXT_SILENT", "question_id": "Q_EDGE_LEFT",
                "exact_question": PLAN["questions"]["Q_EDGE_LEFT"]}
    if i + 1 >= len(candles):
        return {"status": "TEXT_SILENT", "question_id": "Q_EDGE_RIGHT",
                "exact_question": PLAN["questions"]["Q_EDGE_RIGHT"]}
    left, middle, right = candles[i - 1], candles[i], candles[i + 1]
    if kind in ("swing_high", "swing_low"):
        field = "high" if kind == "swing_high" else "low"
        m = getattr(middle, field)
        # Positive means the middle is strictly more extreme, for either side.
        orientation = 1 if field == "high" else -1
        comparisons = [orientation * (m - getattr(neighbour, field)) for neighbour in (left, right)]
        has_tie = any(value == 0 for value in comparisons)
        has_failure = any(value < 0 for value in comparisons)
        if not right.closed and (has_tie or has_failure):
            q = "Q_OPEN_MIXED" if has_tie and has_failure else "Q_OPEN_FAIL" if has_failure else "Q_OPEN_EQUAL"
            return {"status": "TEXT_SILENT", "question_id": q, "exact_question": PLAN["questions"][q]}
        if has_tie and has_failure:
            return {"status": "TEXT_SILENT", "question_id": "Q_MIXED", "exact_question": PLAN["questions"]["Q_MIXED"]}
        if has_tie:
            return {"status": "UNDECIDED"}
        if has_failure:
            return {"status": "NO"}
        return {"status": "YES" if right.closed else "PENDING"}
    # C2 body/colour/size and later candles are deliberately not consulted.
    delta = right.low - left.high if kind == "bullish_fvg" else left.low - right.high
    return {"status": "YES" if delta > 0 else "UNDECIDED" if delta == 0 else "NO"}


def expected_bounds(candles, i, kind):
    if kind == "bullish_fvg":
        return [candles[i - 1].high, candles[i + 1].low]
    if kind == "bearish_fvg":
        return [candles[i + 1].high, candles[i - 1].low]
    return None


def status_case(rep, family, case_id, candles, i, kind, expected, origin=None):
    outcome = rep.call(candles, i, kind, case_id)
    expected_status = expected["status"]
    if expected_status == "TEXT_SILENT":
        if expected.get("question_id") in PRIORITY_QUESTIONS:
            rep.priority(candles, i, kind, outcome, origin or family, case_id)
        else:
            rep.case(family, case_id, "TEXT_SILENT", "TEXT_SILENT", short_outcome(outcome),
                     expected["exact_question"])
        return outcome
    want = {"status": expected_status, "indices": {"c1": i - 1, "c2": i, "c3": i + 1}}
    actual = short_outcome(outcome)
    passed = (outcome["type"] == "return" and isinstance(outcome["value"], dict)
              and status_of(outcome) == expected_status
              and outcome["value"].get("candle_indices") == want["indices"])
    if kind in ("bullish_fvg", "bearish_fvg") and expected_status == "YES":
        want["bounds"] = expected_bounds(candles, i, kind)
        passed = passed and bounds_of(result_value(outcome)) == want["bounds"]
    rep.case(family, case_id, "PASS" if passed else "FAIL", want, actual,
             window=candle_window(candles, i))
    return outcome


def run_a(rep):
    for series in PLAN["A_series"]:
        candles = valid_candles([row["candle"] for row in series["rows"]])
        for row in series["rows"]:
            for kind in KINDS:
                status_case(rep, "A", f"{series['id']}/{row['index']:02}/{kind}",
                            candles, row["index"], kind, row["expected"][kind])


def has_invalidation(record):
    return isinstance(record, dict) and any(
        isinstance(gate, dict) and gate.get("id") == "INVALIDATION_UNDECIDED"
        for gate in record.get("gates", []))


def run_b(rep):
    for shape in PLAN["B_shape_fixtures"]:
        candles = valid_candles(shape["candles"])
        observed = {}
        for row in shape["targets"]:
            i = row["index"]
            for kind in KINDS:
                cid = f"{shape['id']}/{i:02}/{kind}"
                observed[(i, kind)] = status_case(rep, "B", cid, candles, i, kind, row["expected"][kind])
        for i, j in shape.get("overlapping_pairs", []):
            left = result_value(observed[(i, "bullish_fvg")])
            right = result_value(observed[(j, "bullish_fvg")])
            actual_bounds = [bounds_of(left), bounds_of(right)]
            wanted = [shape["yes_bounds"][str(i)]["bullish_fvg"], shape["yes_bounds"][str(j)]["bullish_fvg"]]
            overlap = (all(isinstance(x, list) and len(x) == 2 for x in actual_bounds)
                       and max(actual_bounds[0][0], actual_bounds[1][0]) < min(actual_bounds[0][1], actual_bounds[1][1]))
            ok = actual_bounds == wanted and overlap
            rep.case("B", f"{shape['id']}/overlap-{i}-{j}", "PASS" if ok else "FAIL",
                     {"bounds": wanted, "overlap": True}, {"bounds": actual_bounds, "overlap": overlap})
        if "later_prefix_lengths" in shape:
            kind = "bullish_fvg" if "BULL" in shape["id"] else "bearish_fvg"
            wanted_bounds = shape["yes_bounds"]["1"][kind]
            baseline = None
            for length in shape["later_prefix_lengths"]:
                cid = f"{shape['id']}/prefix-{length}/{kind}"
                outcome = rep.call(candles[:length], 1, kind, cid)
                record = result_value(outcome)
                if baseline is None:
                    baseline = record
                actual = {"status": status_of(outcome), "bounds": bounds_of(record),
                          "invalidation": has_invalidation(record), "same_as_original": record == baseline}
                wanted = {"status": "YES", "bounds": wanted_bounds,
                          "invalidation": True, "same_as_original": True}
                rep.case("B", cid, "PASS" if actual == wanted else "FAIL", wanted, actual)


def shift(c, amount):
    return Candle(open=c.open + amount, high=c.high + amount, low=c.low + amount,
                  close=c.close + amount, closed=c.closed)


def scale(c, factor):
    return Candle(open=c.open * factor, high=c.high * factor, low=c.low * factor,
                  close=c.close * factor, closed=c.closed)


def mirror(c, k):
    return Candle(open=k - c.open, high=k - c.low, low=k - c.high,
                  close=k - c.close, closed=c.closed)


def metamorphic_case(rep, cid, before_candles, after_candles, i, after_i, before_kind, after_kind,
                     transform, argument=0, require_full=False):
    before = rep.call(before_candles, i, before_kind, cid + "/before")
    after = rep.call(after_candles, after_i, after_kind, cid + "/after")
    b, a = result_value(before), result_value(after)
    if not isinstance(b, dict) or not isinstance(a, dict):
        rep.case("C", cid, "FAIL", "two returned records with the prescribed relation",
                 {"before": short_outcome(before), "after": short_outcome(after)})
        return
    shift_by = after_i - i
    before_indices = b.get("candle_indices", {})
    expected_indices = {name: value + shift_by for name, value in before_indices.items()}
    expected = {"status": b.get("status"), "indices": expected_indices}
    actual = {"status": a.get("status"), "indices": a.get("candle_indices")}
    if before_kind in ("bullish_fvg", "bearish_fvg"):
        old_bounds = bounds_of(b)
        if isinstance(old_bounds, list):
            if transform == "translate":
                new_bounds = [v + argument for v in old_bounds]
            elif transform == "scale":
                new_bounds = [v * argument for v in old_bounds]
            elif transform == "mirror":
                new_bounds = [argument - old_bounds[1], argument - old_bounds[0]]
            else:
                new_bounds = old_bounds
        else:
            new_bounds = old_bounds
        expected["bounds"] = new_bounds
        actual["bounds"] = bounds_of(a)
    if require_full:
        expected["entire_record_unchanged"] = True
        actual["entire_record_unchanged"] = (a == b)
    rep.case("C", cid, "PASS" if actual == expected else "FAIL", expected, actual)


def run_c(rep):
    params = PLAN["C_metamorphic"]
    fixtures = [(s["id"], [row["candle"] for row in s["rows"]]) for s in PLAN["A_series"]]
    fixtures += [(s["id"], s["candles"]) for s in PLAN["B_shape_fixtures"]]
    mirrored_kind = {"swing_high": "swing_low", "swing_low": "swing_high",
                     "bullish_fvg": "bearish_fvg", "bearish_fvg": "bullish_fvg"}
    prefix = valid_candles(params["prepend"])
    suffix = valid_candles(params["append"])
    for fixture_id, rows in fixtures:
        base = valid_candles(rows)
        variants = {
            "translate": ([shift(c, params["translate"]) for c in base], 0, params["translate"]),
            "scale": ([scale(c, params["positive_multiplier"]) for c in base], 0, params["positive_multiplier"]),
            "mirror": ([mirror(c, params["mirror_K"]) for c in base], 0, params["mirror_K"]),
            "prepend": (prefix + base, len(prefix), 0),
            "append": (base + suffix, 0, 0),
        }
        for transformation, (variant, offset, argument) in variants.items():
            for i in range(1, len(base) - 1):
                for kind in KINDS:
                    other = mirrored_kind[kind] if transformation == "mirror" else kind
                    cid = f"C-{transformation}/{fixture_id}/{i:02}/{kind}"
                    metamorphic_case(rep, cid, base, variant, i, i + offset, kind, other,
                                     transformation, argument, require_full=(transformation == "append"))
    pending = params["pending_resolution_fixture"]
    base = valid_candles(pending["candles"])
    appended = base + valid_candles([pending["append"]])
    explicitly_closed = [copy.deepcopy(c) for c in base]
    old = explicitly_closed[2]
    explicitly_closed[2] = Candle(open=old.open, high=old.high, low=old.low, close=old.close, closed=True)
    explicitly_closed += valid_candles([pending["append"]])
    for kind in ("swing_high", "swing_low"):
        cid = "C-pending-resolution/" + kind
        one = rep.call(base, 1, kind, cid + "/open")
        two = rep.call(appended, 1, kind, cid + "/append-only")
        three = rep.call(explicitly_closed, 1, kind, cid + "/closed-and-append")
        actual = {"statuses": [status_of(one), status_of(two), status_of(three)],
                  "append_only_unchanged": result_value(one) == result_value(two)}
        expected = {"statuses": ["PENDING", "PENDING", "YES"], "append_only_unchanged": True}
        rep.case("C", cid, "PASS" if actual == expected else "FAIL", expected, actual)
    rng = random.Random(params["lookahead_seed"])
    for series in PLAN["A_series"]:
        base = valid_candles([row["candle"] for row in series["rows"]])
        for trial in range(params["lookahead_trials_per_series"]):
            t = rng.randint(1, len(base) - 3)
            altered = list(base)
            for j in range(t + 2, len(base)):
                low = rng.randint(-30, 60)
                high = rng.randint(low, low + 12)
                opened = rng.randint(low, high)
                close = rng.randint(low, high)
                closed = rng.choice([True, False])
                altered[j] = make_candle(low, high, opened, close, closed)
            # At least one replacement exists, and every position in the suffix
            # was freshly generated (including when its value coincides by chance).
            rep.metrics["C_lookahead_trials"] += 1
            rep.metrics["C_replaced_candles"] += len(base) - (t + 2)
            for i in range(1, t + 1):
                for kind in KINDS:
                    cid = f"C-no-lookahead/{series['id']}/trial-{trial:02}/t-{t:02}/i-{i:02}/{kind}"
                    metamorphic_case(rep, cid, base, altered, i, i, kind, kind, "no-lookahead", require_full=True)


def run_priority_representatives(rep):
    for spec in PLAN["PRECEDENCE_CHOICE"]:
        candles = valid_candles(spec["candles"])
        outcome = rep.call(candles, spec["index"], spec["direction"], "P-REP/" + spec["id"])
        rep.priority(candles, spec["index"], spec["direction"], outcome, "REP", "P-REP/" + spec["id"])


def run_d(rep):
    p = PLAN["D_brute_force"]
    possible = [(lo, hi, closed)
                for lo in range(p["low_high_min"], p["low_high_max"] + 1)
                for hi in range(lo, p["low_high_max"] + 1)
                for closed in p["closure_states"]]
    assert len(possible) == 20
    for serial, triple in enumerate(itertools.product(possible, repeat=3)):
        candles = [make_candle(lo, hi, closed=closed) for lo, hi, closed in triple]
        rep.metrics["D_exhaustive_windows"] += 1
        for kind in KINDS:
            cid = f"D-exhaustive/{serial:04}/{kind}"
            status_case(rep, "D", cid, candles, 1, kind, text_oracle(candles, 1, kind), origin="D-exhaustive")
    assert rep.metrics["D_exhaustive_windows"] == p["exhaustive_windows"]
    rng = random.Random(p["random_seed"])
    for serial in range(p["random_series"]):
        length = rng.randint(5, 40)
        candles = []
        for _ in range(length):
            low = rng.randint(1, 40)
            high = rng.randint(low, low + 12)
            opened = rng.randint(low, high)
            close = rng.randint(low, high)
            closed = rng.choice([True, False])
            candles.append(make_candle(low, high, opened, close, closed))
        rep.metrics["D_random_series"] += 1
        rep.metrics["D_random_windows"] += length - 2
        for i in range(1, length - 1):
            for kind in KINDS:
                cid = f"D-random/{serial:04}/{i:02}/{kind}"
                status_case(rep, "D", cid, candles, i, kind, text_oracle(candles, i, kind), origin="D-random")
    assert rep.metrics["D_random_series"] == p["random_series"]


def constructor_attempt(rows):
    try:
        built = [Candle(**row) for row in rows]
        return {"type": "accepted", "closed_values": [c.closed for c in built]}
    except Exception as exc:
        return {"type": "error", "error": type(exc).__name__, "message": str(exc)}


def duck_rows(rows):
    if rows is None:
        return None
    return [None if row is None else SimpleNamespace(**row) for row in rows]


def invalid_outcome(outcome):
    if outcome["type"] == "error":
        return {"classification": "raised error", "error": outcome["error"], "message": outcome["message"]}
    record = result_value(outcome)
    if isinstance(record, dict) and "status" in record:
        return {"classification": "returned status / silently accepted probe", "status": record["status"]}
    return {"classification": "returned non-status / silently accepted probe", "value": repr(record)}


def run_e(rep):
    for probe in PLAN["E_invalid_probes"]:
        original = copy.deepcopy(probe["candles"])
        first_rows = copy.deepcopy(original)
        second_rows = copy.deepcopy(original)
        constructed1 = constructor_attempt(first_rows)
        constructed2 = constructor_attempt(second_rows)
        construction_unchanged = first_rows == original and second_rows == original
        construction_identical = constructed1 == constructed2
        rep.metrics["constructor_repeat_pairs"] += 1
        if not construction_unchanged or not construction_identical:
            rep.case("F", probe["id"] + "/constructor", "FAIL",
                     "constructor leaves input unchanged and repeats identically",
                     {"input_unchanged": construction_unchanged, "identical": construction_identical,
                      "first": constructed1, "second": constructed2})
        duck = duck_rows(original)
        outcomes = {}
        for kind in KINDS:
            outcome = rep.call(duck, probe["index"], kind, probe["id"] + "/" + kind)
            outcomes[kind] = invalid_outcome(outcome)
        actual = {"constructor": constructed1, "direct_duck_typed_interface": outcomes}
        rep.case("E", probe["id"], "TEXT_SILENT", "TEXT_SILENT", actual, probe["exact_question"])


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def report_line(item):
    question = " | question=" + item["exact_question"] if item.get("exact_question") else ""
    return (f"- {item['verdict']} | {item['case']} | expected={one_line(item['expected'])}"
            f" | actual={one_line(item['actual'])}{question}")


def write_results(rep, log_sha):
    lines = [
        "# B1 hard test results",
        "",
        "The plan and expected fixtures were committed before implementation inspection. "
        "The runner imports the B1 implementation read-only, uses integer-tick FIXTURE prices, "
        "and uses only the Python standard library. The implementation exposes event-time "
        "`swing_at` and `fvg_at`; C2 index `i` is evaluated at C3 index `t=i+1`.",
        "",
        "## Counts",
        "",
        "| Family | Cases | PASS | FAIL | TEXT_SILENT |",
        "|---|---:|---:|---:|---:|",
    ]
    for family in FAMILIES:
        c = rep.counts[family]
        total = c["PASS"] + c["FAIL"] + c["TEXT_SILENT"]
        lines.append(f"| {family} | {total} | {c['PASS']} | {c['FAIL']} | {c['TEXT_SILENT']} |")
    lines += [
        "",
        "Counting: A/B/D count single direction/index assertions, excluding all priority-dependent "
        "status observations. C counts independent relations. E counts malformed-input probes, "
        "each of which is tried with all four detector directions. F counts every returned detector "
        "record, including both repeated invocations; exceptions are audited but are not records. "
        "PRECEDENCE_CHOICE counts 20 relation/closure equivalence-group cases; the actual number "
        "of individual observations routed into them is reported below and each is logged.",
        "",
        "## Coverage and audit",
        "",
        f"- Exhaustive D: {rep.metrics['D_exhaustive_windows']} windows, "
        f"{rep.metrics['D_exhaustive_windows'] * 4} direction observations; all independent closure combinations.",
        f"- Random D: seed 12345, {rep.metrics['D_random_series']} series, "
        f"{rep.metrics['D_random_windows']} complete windows, {rep.metrics['D_random_windows'] * 4} direction observations.",
        f"- D text-decided comparisons: {rep.counts['D']['PASS'] + rep.counts['D']['FAIL']}; "
        f"mismatches: {rep.counts['D']['FAIL']}; priority-dependent D observations: "
        f"{rep.metrics['priority_D-exhaustive'] + rep.metrics['priority_D-random']} "
        "(not asserted as matches or mismatches).",
        f"- Oracle agreement: {'YES on every text-decided observation' if rep.counts['D']['FAIL'] == 0 else 'NO; see every D failure below'}. "
        "There is no V2 oracle answer for the separately counted priority-dependent observations.",
        f"- PRECEDENCE_CHOICE: {rep.metrics['priority_observations']} individual observations, "
        f"origins={one_line({k.removeprefix('priority_'): v for k, v in rep.metrics.items() if k.startswith('priority_') and k != 'priority_observations'})}; "
        "return distributions and exact questions for all 20 groups are listed below.",
        f"- C no-lookahead: {rep.metrics['C_lookahead_trials']} seeded suffix replacements, "
        f"{rep.metrics['C_replaced_candles']} freshly generated later candles; every complete index up to t was compared.",
        f"- F: {rep.metrics['F_detector_records']} returned records from {rep.metrics['detector_call_pairs']} "
        f"paired detector invocations; {rep.metrics['exception_execution_audits']} exception executions "
        f"also audited for unchanged input and repeatability. Constructor probes repeated: {rep.metrics['constructor_repeat_pairs']}.",
        f"- F individual rule-applicability counts: {one_line(dict(rep.rule_checks))}.",
        "- The implementation contains an asserted decision order, but V2 does not state that "
        "priority. Its outcomes are observations in PRECEDENCE_CHOICE, not V2-backed passes or failures.",
        "- No network, external libraries, market data, or code changes were used for the run. "
        "No original fixture is edited. The malformed probes deliberately violate the input schema. "
        "E distinguishes the validating Candle constructor from direct duck-typed detector calls, "
        "which intentionally bypass that constructor; it does not claim V2 requires either behaviour.",
        f"- Detailed per-observation JSONL (outside repository): `{LOG_PATH}`; SHA-256: `{log_sha}`.",
        "",
    ]
    for family in FAMILIES:
        c = rep.counts[family]
        lines += [f"## {family}", "", f"PASS {c['PASS']} / FAIL {c['FAIL']} / TEXT_SILENT {c['TEXT_SILENT']}.", ""]
        details = rep.details[family]
        if details:
            lines.extend(report_line(item) for item in details)
        else:
            lines.append("No FAIL or TEXT_SILENT cases in this family.")
        lines.append("")
    RESULTS_PATH.write_text("\n".join(lines), encoding="utf-8")


def main():
    with LOG_PATH.open("w", encoding="utf-8", buffering=1024 * 1024) as log:
        rep = Reporter(log)
        run_a(rep)
        run_b(rep)
        run_c(rep)
        run_priority_representatives(rep)
        run_d(rep)
        run_e(rep)
        rep.finish_priority()
    sha = file_sha256(LOG_PATH)
    write_results(rep, sha)
    print("Detailed log:", LOG_PATH)
    print("Detailed log SHA-256:", sha)
    for family in FAMILIES:
        c = rep.counts[family]
        print(f"{family}: cases={c['PASS'] + c['FAIL'] + c['TEXT_SILENT']} "
              f"PASS={c['PASS']} FAIL={c['FAIL']} TEXT_SILENT={c['TEXT_SILENT']}")
    print("Priority individual observations:", rep.metrics["priority_observations"])
    print("D exhaustive windows:", rep.metrics["D_exhaustive_windows"],
          "random series:", rep.metrics["D_random_series"], "random windows:", rep.metrics["D_random_windows"])
    return 1 if any(rep.counts[f]["FAIL"] for f in FAMILIES) else 0


if __name__ == "__main__":
    raise SystemExit(main())
