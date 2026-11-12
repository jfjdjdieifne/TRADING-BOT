#!/usr/bin/env python3
"""Turn a run's outputs into SUMMARY.md and the glass-box CASE files.

    python3 report_v1.py --run /tmp/build_v1/real_2021_06

A and B are kept apart on purpose: A contains only what existed at t (it is copied from the decision
record written *before* the outcome was known), B contains everything after t and is labelled as
hindsight.  C re-derives the plan's arithmetic by an independent call and counts matches.  D is one
row and is marked HYPOTHESIS.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import statistics
from pathlib import Path

SEED = 20261109


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ------------------------------------------------------------------ fault locator
def fault_row(plan: dict, decisions_by_index: dict) -> dict:
    """HYPOTHESIS: where the reading failed, from facts recorded during the run."""

    if plan["state"] == "settled_target":
        return {"plan_id": plan["plan_id"], "verdict": "settled_target", "category": "none visible",
                "evidence": "T1 touched before the stop under the conservative rule"}
    if plan["state"] == "expired":
        return {"plan_id": plan["plan_id"], "verdict": plan["state"], "category": "none visible",
                "evidence": plan.get("exit_reason", "")}
    trigger = decisions_by_index.get(plan.get("trigger_index"))
    reason = []
    if plan.get("trigger_index") == plan.get("exit_index"):
        reason.append("the triggering bar spanned the whole zone, so the conservative stop-first "
                      "rule settles it on the entry bar")
        category = "execution assumption / stop"
    else:
        reason.append("the stop was touched before T1")
        category = "stop"
    if trigger and trigger.get("bias", {}).get("daily") is None:
        category = "bias"
        reason.append("no completed daily bucket was available")
    if trigger and trigger.get("range", {}).get("position") in ("undefined", "no_market"):
        category = "structure"
        reason.append("the dealing range was undefined at the trigger")
    return {"plan_id": plan["plan_id"], "verdict": plan["state"], "category": category,
            "evidence": "; ".join(reason)}


def mechanical_recompute(plan: dict) -> dict:
    """C: re-derive the arithmetic from the record's own numbers, count matches."""

    checks = {}
    entry, stop = plan["entry"], plan["stop"]
    risk = abs(entry - stop)
    checks["risk_price"] = abs(plan["risk_price"] - risk) < 1e-12
    if plan["t1"] is not None:
        rr = abs(plan["t1"]["level"] - entry) / risk
        checks["rr_t1_measured"] = abs((plan["rr_t1_measured"] or 0.0) - rr) < 1e-9
    if plan["t2"] is not None:
        rr2 = abs(plan["t2"]["level"] - entry) / risk
        checks["rr_t2_measured"] = abs((plan["rr_t2_measured"] or 0.0) - rr2) < 1e-9
    direction = plan["direction"]
    checks["stop_on_the_far_side"] = (stop < entry) if direction == "bullish" else (stop > entry)
    if plan["t1"] is not None:
        checks["t1_ahead_of_entry"] = ((plan["t1"]["level"] > entry) if direction == "bullish"
                                       else (plan["t1"]["level"] < entry))
    if plan.get("r_measured") is not None and plan.get("exit_price") is not None:
        gross = (plan["exit_price"] - entry) if direction == "bullish" else (entry - plan["exit_price"])
        r = (gross - plan.get("cost_price", 0.0)) / risk
        checks["r_measured_from_prices"] = abs(r - plan["r_measured"]) < 1e-9
    return {"checks": checks, "matched": sum(1 for v in checks.values() if v),
            "mismatched": sum(1 for v in checks.values() if not v)}


# ------------------------------------------------------------------ case file
def case_markdown(plan: dict, decision: dict, bars_after: list[dict], index: int) -> str:
    story = decision.get("story", {})
    lines = []
    lines.append(f"# CASE {index} — EURUSD 5m, decision at {plan['decided_at']} "
                 f"(bar index {plan['decision_index']})")
    lines.append("")
    lines.append("## A. AS OF t — only what existed at t")
    lines.append(f"A.1 context: daily bias `{decision['bias']['daily']}`, weekly bias "
                 f"`{decision['bias']['weekly']}`, resolved `{decision['bias']['resolved']}`"
                 + (", **bias_conflict**" if decision["bias"].get("bias_conflict") else ""))
    rg = decision["range"]
    lines.append(f"A.2 dealing range: low `{rg.get('low')}`, high `{rg.get('high')}`, "
                 f"equilibrium `{rg.get('equilibrium')}`, position `{rg.get('position')}`, "
                 f"ratio `{round(rg.get('position_ratio', 0), 4) if rg.get('position_ratio') is not None else None}` "
                 f"(id `{rg.get('definition_id')}`)")
    untaken = decision.get("untaken", [])
    lines.append("A.3 liquidity map (untaken, newest first):")
    for pool in untaken[:8]:
        lines.append(f"  - `{pool['level']}` {pool['side']} `{pool['kind']}`, formed at bar "
                     f"{pool['formed_index']}, age {pool['age_bars']} bars")
    if not untaken:
        lines.append("  - *(none recorded)*")
    swing = decision.get("swings", [])
    lines.append(f"A.4 concepts at t: swing `{swing or 'none confirmed on this bar'}`, "
                 f"FVG `{decision.get('fvg') or 'none on this bar'}`, "
                 f"displacement `{decision['displacement']['answer']}` "
                 f"(V-D-01, ratio {decision['displacement'].get('ratio')}), "
                 f"sweep high `{decision['sweep']['high']['answer']}`, "
                 f"sweep low `{decision['sweep']['low']['answer']}`, "
                 f"structure shift `{decision['structure_shift']['shift'] or 'none'}`")
    lines.append("A.5 candidate zones, ranked:")
    for zone in decision.get("zones_ranked", []):
        lines.append(f"  - `{zone['zone_id']}` {zone['kind']} [{zone['lower']}, {zone['upper']}] "
                     f"fresh={zone['fresh']} bias_agrees={zone['bias_agrees']} "
                     f"distance_ratio={zone['distance_ratio']}")
    if decision.get("criteria"):
        lines.append(f"  criteria: {json.dumps(decision['criteria'])}")
    lines.append("A.6 competing hypotheses:")
    for hypo in decision.get("hypotheses", []):
        lines.append(f"  - **{hypo['name']}** — for: {'; '.join(hypo['for'])}; "
                     f"against: {'; '.join(hypo['against'])}")
    lines.append(f"A.7 the decision in plain words: a **{plan['direction']}** plan from the "
                 f"`{plan['zone']['kind']}` zone `{plan['zone']['zone_id']}` was armed at "
                 f"{plan['decided_at']}; it is hypothetical and assumes no execution contract.")
    lines.append(f"A.8 the hypothetical plan: entry `{plan['entry']}` "
                 f"({plan['entry_rule']}), stop `{plan['stop']}` ({plan['stop_rule']}), "
                 f"T1 `{plan['t1']['level'] if plan['t1'] else None}`, "
                 f"T2 `{plan['t2']['level'] if plan['t2'] else None}` "
                 f"({plan['t2_note'] or 'two targets existed'}), measured R:R "
                 f"T1 `{round(plan['rr_t1_measured'], 3) if plan['rr_t1_measured'] else None}` / "
                 f"T2 `{round(plan['rr_t2_measured'], 3) if plan['rr_t2_measured'] else None}`, "
                 f"half-spread at decision `{plan['half_spread_at_decision']}`.")
    lines.append(f"   what would change this: {'; '.join(plan['what_would_change'])}")
    lines.append(f"A.9 not looked at: {'; '.join(decision.get('not_looked_at', []))}")
    lines.append("")
    lines.append("## B. HINDSIGHT — everything after t, kept separate")
    if not bars_after:
        lines.append("B.1 no bars after the decision are in this run's output.")
    else:
        lines.append("B.1 bars after the decision, in order:")
        for row in bars_after[:40]:
            lines.append(f"  - {row['at']}  high {row['high']}  low {row['low']}  "
                         f"close {row['close']}  state {row['state']}")
        if len(bars_after) > 40:
            lines.append(f"  - … {len(bars_after) - 40} more bars to the exit")
    lines.append(f"B.3 fill assumption: limit at the zone edge, settled by the conservative "
                 f"stop-first rule; cost = half the spread at entry + half at exit.")
    lines.append(f"   outcome: `{plan['state']}` ({plan.get('exit_reason')}), "
                 f"R = {round(plan['r_measured'], 4) if plan.get('r_measured') is not None else None}, "
                 f"exit price `{plan.get('exit_price')}` at bar {plan.get('exit_index')}.")
    lines.append("B.4 a plan that never triggered is counted as expired, not as resolved.")
    lines.append("")
    recompute = mechanical_recompute(plan)
    lines.append("## C. MECHANICAL RECOMPUTATION — counts only")
    for name, ok in recompute["checks"].items():
        lines.append(f"  - {name}: {'match' if ok else 'MISMATCH'}")
    lines.append(f"C.2 mismatches: {recompute['mismatched']} of {len(recompute['checks'])} checks.")
    lines.append("C.3 the numbers in A come from records already tagged with their source; this "
                 "section only re-derives the arithmetic.")
    lines.append("")
    return "\n".join(lines) + "\n"


def fault_markdown(row: dict) -> str:
    return (f"## D. FAULT LOCATOR — HYPOTHESIS\n"
            f"  - category: `{row['category']}`\n"
            f"  - verdict: `{row['verdict']}`\n"
            f"  - evidence: {row['evidence']}\n")


# ------------------------------------------------------------------ summary
def build(run_dir: Path) -> dict:
    summary = json.loads((run_dir / "run_summary.json").read_text())
    decisions = read_jsonl(run_dir / "decisions.jsonl")
    final = read_jsonl(run_dir / "plans_final.jsonl")
    plans = final if final else summary.get("settled_plans", [])
    by_index = {d["index"]: d for d in decisions}

    settled = [p for p in plans if p["state"].startswith("settled")]
    expired = [p for p in plans if p["state"] == "expired"]
    open_plans = [p for p in plans if p["state"] in ("armed", "triggered")]
    r_values = [p["r_measured"] for p in settled if p.get("r_measured") is not None]

    def drawdown(series: list[float]) -> float:
        peak, worst = 0.0, 0.0
        for value in series:
            peak = max(peak, value)
            worst = min(worst, value - peak)
        return worst

    def longest_negative(series: list[float]) -> int:
        best = run = 0
        for value in series:
            run = run + 1 if value < 0 else 0
            best = max(best, run)
        return best

    ordered = sorted(settled, key=lambda p: p["exit_index"] or 0)
    r_ordered = [p["r_measured"] for p in ordered if p.get("r_measured") is not None]

    faults = [fault_row(p, by_index) for p in ordered]
    categories: dict[str, int] = {}
    for row in faults:
        categories[row["category"]] = categories.get(row["category"], 0) + 1

    cases_dir = run_dir / "cases"
    cases_dir.mkdir(exist_ok=True)
    for i, plan in enumerate(ordered, start=1):
        decision = by_index.get(plan["decision_index"], {})
        text = case_markdown(plan, decision, plan.get("exit_trail", []), i)
        text += fault_markdown(faults[i - 1])
        (cases_dir / f"CASE_{i:03d}.md").write_text(text, encoding="utf-8")

    # non-plan sample: 10 seeded + the 3 closest to becoming plans
    non_plans = [d for d in decisions if d.get("decision") == "NO_PLAN"]
    rng = random.Random(SEED)
    seeded = rng.sample(non_plans, min(10, len(non_plans))) if non_plans else []
    close_calls = sorted(
        [d for d in non_plans if d.get("reason") == "zone_not_touched"],
        key=lambda d: (d.get("gate_detail") or {}).get("distance", 1e9))[:3]

    lines = []
    lines.append(f"# SUMMARY — {run_dir.name}")
    lines.append("")
    lines.append(f"- decisions: **{summary['decisions']}**; plans: **{summary['plans']}**; "
                 f"no-plan: **{summary['no_plan']}**")
    lines.append(f"- window: {summary['window_bars']} bars; bars consumed: {summary['bars_consumed']}; "
                 f"elapsed: {summary['elapsed_seconds']} s")
    lines.append(f"- peak RSS: {summary['memory']['peak_rss_kb']} kB of "
                 f"{summary['memory']['total_kb']} kB; cap {summary['memory']['cap_kb']} kB")
    lines.append(f"- stopped early: {summary['stopped']}")
    lines.append("")
    lines.append("## 1. No-plan reasons")
    lines.append("")
    lines.append("| reason | count | share |")
    lines.append("|---|---|---|")
    total = max(1, summary["decisions"])
    for reason, count in summary["no_plan_reasons"].items():
        lines.append(f"| {reason} | {count} | {count / total:.1%} |")
    lines.append("")
    lines.append("## 2. Per-step statistics (how often each concept was found)")
    lines.append("")
    lines.append("| step | occurrences | per decision |")
    lines.append("|---|---|---|")
    for name, count in summary["concept_hits"].items():
        lines.append(f"| {name} | {count} | {count / total:.3f} |")
    lines.append("")
    lines.append("## 3. R statistics (hypothetical, after half-spread cost)")
    lines.append("")
    if r_values:
        lines.append(f"- settled plans: {len(settled)}; expired: {len(expired)}; "
                     f"still open at the end: {len(open_plans)}")
        lines.append(f"- mean R {statistics.mean(r_values):.3f}; median {statistics.median(r_values):.3f}; "
                     f"sum {sum(r_values):.3f}")
        lines.append(f"- max drawdown in R (cumulative, ordered by exit): {drawdown(r_ordered):.3f}")
        lines.append(f"- longest negative-R streak: {longest_negative(r_ordered)}")
        rr1 = [p["rr_t1_measured"] for p in plans if p.get("rr_t1_measured")]
        rr2 = [p["rr_t2_measured"] for p in plans if p.get("rr_t2_measured")]
        stops = [p["risk_price"] for p in plans if p.get("risk_price")]
        lines.append(f"- measured R:R to T1: min {min(rr1):.2f}, median {statistics.median(rr1):.2f}, "
                     f"max {max(rr1):.2f} (n={len(rr1)})")
        if rr2:
            lines.append(f"- measured R:R to T2: min {min(rr2):.2f}, median {statistics.median(rr2):.2f}, "
                         f"max {max(rr2):.2f} (n={len(rr2)}); plans with only one target: "
                         f"{sum(1 for p in plans if p.get('t2') is None)}")
        lines.append(f"- stop distance (price): min {min(stops):.5f}, median "
                     f"{statistics.median(stops):.5f}, max {max(stops):.5f}")
    else:
        lines.append("_no plan was settled: **zero plans** is a valid result and the no-plan reasons "
                     "above are the finding._")
    lines.append("")
    lines.append("## 4. Fault locator (HYPOTHESIS, one row per settled plan)")
    lines.append("")
    lines.append("| category | plans |")
    lines.append("|---|---|")
    for name, count in sorted(categories.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {name} | {count} |")
    lines.append("")
    lines.append("| plan | verdict | category | evidence |")
    lines.append("|---|---|---|---|")
    for row in faults[:40]:
        lines.append(f"| `{row['plan_id']}` | {row['verdict']} | {row['category']} | "
                     f"{row['evidence']} |")
    lines.append("")
    lines.append("## 5. Ranked: what is missing / what looks wrong")
    lines.append("")
    ranking = []
    outside = summary["no_plan_reasons"].get("outside_session_window", 0)
    if outside:
        ranking.append((outside / total, f"{outside} decisions ({outside / total:.0%}) fall outside "
                                         f"the declared EURO_0200_0500 window; the story state is "
                                         f"mostly idle and the window is doing most of the filtering"))
    if summary["concept_hits"].get("order_block_created", 0) < 5:
        ranking.append((0.9, "almost no order block survives its prerequisite chain "
                             f"({summary['concept_hits'].get('order_block_created', 0)} created)"))
    if categories.get("execution assumption / stop"):
        ranking.append((categories["execution assumption / stop"] / max(1, len(faults)),
                        "the conservative stop-first rule settles plans on their entry bar when a "
                        "bar spans the zone; the entry/stop model, not the reading, may be the cause"))
    ranking.append((0.5, "KNOWLEDGE_GAP: FVG_INVALIDATION — a gap is never 'invalidated', only "
                         "closed through, so zone lifetimes are mechanical rather than doctrinal"))
    ranking.append((0.4, "T2 is a second element of a ranking that was built for one target; "
                         "whether T2 is a real objective is unsettled"))
    for _, text in sorted(ranking, key=lambda kv: -kv[0]):
        lines.append(f"- {text}")
    lines.append("")
    lines.append("## 6. Non-plan sample (seed 20261109)")
    lines.append("")
    lines.append("The ten sampled non-plan decisions:")
    lines.append("")
    lines.append("| at | reason | close | range position | zones | targets |")
    lines.append("|---|---|---|---|---|---|")
    for d in seeded:
        lines.append(f"| {d['decided_at']} | {d.get('reason')} | {d['close']} | "
                     f"{d['range'].get('position')} | {(d.get('gate_detail') or {}).get('zone','')} "
                     f"| {len(d.get('zones_ranked', []))} |")
    lines.append("")
    lines.append("The three closest to becoming a plan (a zone existed and price was nearest to it):")
    lines.append("")
    lines.append("| at | distance to zone edge | zone | reason |")
    lines.append("|---|---|---|---|")
    for d in close_calls:
        detail = d.get("gate_detail") or {}
        lines.append(f"| {d['decided_at']} | {detail.get('distance')} | {detail.get('zone')} | "
                     f"{d.get('reason')} |")
    lines.append("")
    lines.append("## 7. Files and hashes")
    lines.append("")
    lines.append("| file | sha256 |")
    lines.append("|---|---|")
    for path in sorted(run_dir.rglob("*")):
        if path.is_file() and path.suffix in (".json", ".jsonl", ".md") and path.name != "SUMMARY.md":
            lines.append(f"| `{path.relative_to(run_dir)}` | `{digest(path)}` |")
    lines.append("")
    lines.append("## What this does NOT establish")
    lines.append("")
    lines.append("- It does not establish that any reading is correct: a plan is `HYPOTHETICAL_` and "
                 "a settled R is an accounting identity under a stated fill assumption, not a result.")
    lines.append("- The fault locator is a **HYPOTHESIS** derived from stored fields, not a diagnosis.")
    lines.append("- Zero or few plans is not evidence about the market; it is evidence about the "
                 "gate chain and the declared window.")
    lines.append("- The sensitivity of `WINDOW_BARS` is not tested here (DECLARED_CHOICES row 1).")

    text = "\n".join(lines) + "\n"
    (run_dir / "SUMMARY.md").write_text(text, encoding="utf-8")
    return {"cases": len(ordered), "settled": len(settled), "expired": len(expired),
            "r_values": r_values, "categories": categories}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    args = ap.parse_args()
    result = build(Path(args.run))
    print(json.dumps(result, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
