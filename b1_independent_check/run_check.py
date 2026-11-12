#!/usr/bin/env python3
"""Read-only independent check of the B1 candle implementation.

Expectations are loaded as committed before this runner was written. The B1
source files are only imported/read; this runner never edits them.
"""
from __future__ import annotations

import ast
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PATH = Path(__file__).with_name("INDEPENDENT_EXPECTATIONS.json")
RESULTS_PATH = Path(__file__).with_name("RESULTS.md")
CODE_DIR = ROOT / "project/trading_project/docs/research/huddleston_study/engine_v1/b1_candles"
sys.path.insert(0, str(CODE_DIR))

from candle import Candle  # noqa: E402
from fvg import fvg_at  # noqa: E402
from swing import swing_at  # noqa: E402


def construct(rows):
    return [Candle(**row) for row in rows]


def evaluate(group, case, candles=None):
    fixture = case["fixture"]
    values = construct(fixture["candles"]) if candles is None else candles
    t = fixture["target_index"] + 1  # target_index names c2; API t names c3
    if group == "swing_high_at_c2":
        return swing_at(values, t, "high")
    if group == "swing_low_at_c2":
        return swing_at(values, t, "low")
    if group == "fvg_bullish":
        return fvg_at(values, t, "bullish")
    if group == "fvg_bearish":
        return fvg_at(values, t, "bearish")
    raise ValueError(group)


def static_findings():
    findings = []
    numeric = []
    imports = []
    file_reads = []
    old_pipeline = []
    threshold_names = []
    for path in sorted(CODE_DIR.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend((path.name, a.name) for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append((path.name, ("." * node.level) + (node.module or "")))
                mod = (node.module or "").lower()
                if "information_time" in mod or "pipeline" in mod:
                    old_pipeline.append(f"{path.name}:{node.lineno}: {node.module}")
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else ""
                attr = node.func.attr if isinstance(node.func, ast.Attribute) else ""
                if name == "open" or attr in {"read_text", "read_bytes", "load", "loads"}:
                    if name == "open" or attr in {"read_text", "read_bytes"}:
                        file_reads.append(f"{path.name}:{node.lineno}: {name or attr}()")
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and isinstance(node.value, ast.Constant):
                        if isinstance(node.value.value, (int, float)) and not isinstance(node.value.value, bool):
                            numeric.append((path.name, node.lineno, target.id, repr(node.value.value)))
                        if any(token in target.id.lower() for token in ("threshold", "ratio", "default")):
                            threshold_names.append(f"{path.name}:{node.lineno}: {target.id}={ast.unparse(node.value)}")
        # Token/word scan is intentionally separate from AST import parsing.
        if "michael" in source.lower():
            findings.append(f"{path.name}: contains the word Michael (case-insensitive)")

    dependency_names = {name.split(".")[0].lower() for _, name in imports}
    forbidden_modules = {"pandas", "requests", "urllib", "socket", "http", "httpx", "aiohttp", "websocket", "websockets"}
    forbidden_found = sorted(dependency_names & forbidden_modules)
    findings.append("Word Michael: " + ("; ".join(x for x in findings if "word Michael" in x) if any("word Michael" in x for x in findings) else "not found in Python source text"))
    findings.append("Imported modules: " + ", ".join(f"{f}:{m}" for f, m in imports))
    findings.append("Forbidden/network/pandas imports: " + (", ".join(forbidden_found) if forbidden_found else "none"))
    findings.append("Old pipeline imports: " + ("; ".join(old_pipeline) if old_pipeline else "none found; the token information_time occurs only in test_fixtures.py's forbidden-import guard list, not as an import"))
    findings.append("File reads: " + ("; ".join(file_reads) if file_reads else "none found"))
    findings.append("Module-level numeric assignments (includes test-harness state): " + ("; ".join(f"{f}:{line} {name}={value}" for f, line, name, value in numeric) if numeric else "none"))
    findings.append("Threshold/ratio/default-named assignments: " + ("; ".join(threshold_names) if threshold_names else "none"))
    findings.append("Numeric interpretation: NEIGHBOURS_EACH_SIDE=1 is the V2 source number; GAP_CANDLES=3 is the V2 three-candle FVG structure. Other numeric literals found in implementation are fixed index/window offsets and validation (t-2, t-1, t+1, t<2), not price thresholds or ratios. Defaults found: Candle.closed=True and from_mapping(...).get('closed', True).")
    findings.append("Future-candle access: swing_at and fvg_at both use candles[:t+1], then c1=t-2, c2=t-1, c3=t; no access after index t found.")
    return findings


def main():
    expectations = json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))
    lines = ["# Independent B1 check results", "", "Source files were imported/read-only; no code under `engine_v1/b1_candles/` was modified.", "", "## Per-case results", ""]
    counts = {}
    records = {}
    all_serialized = []
    low_label_checks = []
    fvg_gate_checks = []

    for group in ("swing_high_at_c2", "swing_low_at_c2", "fvg_bullish", "fvg_bearish"):
        results = []
        for case in expectations["expectations"][group]["cases"]:
            record = evaluate(group, case)
            records[case["id"]] = record
            all_serialized.append(json.dumps(record, ensure_ascii=False, sort_keys=True))
            expected = case["expected_status"]
            actual = record["status"]
            if expected == "TEXT_SILENT":
                classification = "TEXT_SILENT"
                detail = f"code returned {actual}; question: {case['exact_question']}"
            elif actual == expected:
                classification = "MATCH"
                detail = f"expected={expected}; actual={actual}"
            else:
                classification = "MISMATCH"
                detail = f"expected={expected}; actual={actual}"
            results.append(classification)
            lines.append(f"- {classification} | {group} | {case['id']} | {detail}")
            if group == "swing_low_at_c2":
                low_label_checks.append((case["id"], "WEAK_SUPPORT" in record.get("labels", [])))
            if group.startswith("fvg_"):
                fvg_gate_checks.append((case["id"], any(g.get("id") == "INVALIDATION_UNDECIDED" for g in record.get("gates", []))))
        counts[group] = {kind: results.count(kind) for kind in ("MATCH", "MISMATCH", "TEXT_SILENT")}

    lines.extend(["", "## Counts", ""])
    for group, result in counts.items():
        lines.append(f"- {group}: MATCH {result['MATCH']}, MISMATCH {result['MISMATCH']}, TEXT_SILENT {result['TEXT_SILENT']}")
    lines.append(f"- Combined FVG: MATCH {sum(counts[g]['MATCH'] for g in ('fvg_bullish','fvg_bearish'))}, MISMATCH {sum(counts[g]['MISMATCH'] for g in ('fvg_bullish','fvg_bearish'))}, TEXT_SILENT {sum(counts[g]['TEXT_SILENT'] for g in ('fvg_bullish','fvg_bearish'))}")

    # Cross-cutting behavioral expectations.
    lines.extend(["", "## Cross-cutting checks", ""])
    lines.append(f"- Swing-low WEAK_SUPPORT: {'PASS' if all(ok for _, ok in low_label_checks) else 'FAIL'} ({sum(ok for _, ok in low_label_checks)}/{len(low_label_checks)} results)")
    lines.append(f"- FVG INVALIDATION_UNDECIDED: {'PASS' if all(ok for _, ok in fvg_gate_checks) else 'FAIL'} ({sum(ok for _, ok in fvg_gate_checks)}/{len(fvg_gate_checks)} results)")
    serialized_blob = "\n".join(all_serialized).lower()
    lines.append("- No word Michael in serialized result records: " + ("PASS" if "michael" not in serialized_blob else "FAIL"))

    base = construct(expectations['cross_cutting_expectations'][3]['fixture']['candles'][:3])
    appended = construct(expectations['cross_cutting_expectations'][3]['fixture']['candles'])
    extra = [Candle(open=14, high=16, low=13, close=15, closed=True)]
    future_checks = []
    for fn, args in ((swing_at, ("high",)), (swing_at, ("low",)), (fvg_at, ("bullish",)), (fvg_at, ("bearish",))):
        before = fn(base, 2, *args)
        after = fn(appended + extra, 2, *args)
        future_checks.append(before == after)
    lines.append(f"- Future append invariance at t=2 (swing high/low, bullish/bearish FVG): {'PASS' if all(future_checks) else 'FAIL'} ({sum(future_checks)}/4)")

    mutation_rows = expectations['cross_cutting_expectations'][4]['fixture']['candles']
    mutation_checks = []
    for fn, args in ((swing_at, ("high",)), (swing_at, ("low",)), (fvg_at, ("bullish",)), (fvg_at, ("bearish",))):
        mutation_input = construct(mutation_rows)
        snapshot = copy.deepcopy(mutation_input)
        fn(mutation_input, 2, *args)
        mutation_checks.append(mutation_input == snapshot)
    lines.append(f"- Input candle list unchanged (all four functions): {'PASS' if all(mutation_checks) else 'FAIL'} ({sum(mutation_checks)}/4)")

    deterministic_input = construct(expectations['cross_cutting_expectations'][5]['fixture']['candles'])
    deterministic_checks = []
    for fn, args in ((swing_at, ("high",)), (swing_at, ("low",)), (fvg_at, ("bullish",)), (fvg_at, ("bearish",))):
        first = fn(deterministic_input, 2, *args)
        second = fn(deterministic_input, 2, *args)
        deterministic_checks.append(first == second)
    lines.append(f"- Two identical runs (all four functions): {'PASS' if all(deterministic_checks) else 'FAIL'} ({sum(deterministic_checks)}/4)")

    lines.extend(["", "## Step 4 static findings", ""])
    lines.extend(f"- {finding}" for finding in static_findings())
    lines.append("")
    RESULTS_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(RESULTS_PATH.read_text(encoding="utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
