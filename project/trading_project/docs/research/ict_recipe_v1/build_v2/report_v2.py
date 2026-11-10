#!/usr/bin/env python3
"""Report for the v2 runs: statistics, comparison, cases, faults, hashes.

    python3 report_v2.py --root /tmp/build_v2 --data /tmp/hud_data/2021.csv.gz

Every statistic is computed from the run's saved `plans_final.jsonl` / `run_summary.json`; the NULL
baseline replays the same 5m bars the run saw, from the same decision indices, with the direction drawn
by `random.Random(20261109)` and the same stop/target distances.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import statistics
from datetime import datetime, timezone
from pathlib import Path

BOOTSTRAP_RESAMPLES = 2000        # ENGINEERING_CHOICE (DECLARED_CHOICES_V2 row M)
BOOTSTRAP_LEVEL = 0.95            # ENGINEERING_CHOICE
NULL_SEED = 20261109              # owner brief
HORIZON_BARS = 288                # v1 row: 288-bar plan expiry, unchanged

MONTHS = {"M1": "2021-09", "M2": "2021-07", "IN_SAMPLE": "2021-06"}
VARIANTS = ["v1", "V2-0", "V2-A", "V2-B", "V2-A-OFF", "V2-B-OFF"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def drawdown(series: list[float]) -> float:
    """VERIFIED formula (DIAGNOSIS_V1 a): on the CUMULATIVE series, not on raw R."""

    peak = worst = 0.0
    total = 0.0
    for value in series:
        total += value
        peak = max(peak, total)
        worst = min(worst, total - peak)
    return worst


def streak(series: list[float]) -> int:
    best = run = 0
    for value in series:
        run = run + 1 if value < 0 else 0
        best = max(best, run)
    return best


def bootstrap(values: list[float], rng: random.Random) -> tuple[float, float]:
    if len(values) < 3:
        return (float("nan"), float("nan"))
    means = []
    for _ in range(BOOTSTRAP_RESAMPLES):
        sample = [values[rng.randrange(len(values))] for _ in values]
        means.append(sum(sample) / len(sample))
    means.sort()
    lo = means[int((1 - BOOTSTRAP_LEVEL) / 2 * len(means))]
    hi = means[int((1 - (1 - BOOTSTRAP_LEVEL) / 2) * len(means)) - 1]
    return lo, hi


def load_run(run_dir: Path) -> tuple[dict, list[dict]]:
    summary = json.loads((run_dir / "run_summary.json").read_text())
    final = read_jsonl(run_dir / "plans_final.jsonl")
    plans = final if final else summary.get("settled_plans", [])
    return summary, plans


def null_baseline(plans: list[dict], bars: list) -> list[float]:
    rng = random.Random(NULL_SEED)
    out = []
    for plan in plans:
        idx = plan.get("decision_index")
        t1 = plan.get("t1")
        if idx is None or t1 is None or idx + 1 >= len(bars):
            continue
        entry = plan["entry"]
        risk = abs(entry - plan["stop"])
        reward = abs(t1["level"] - entry)
        if risk <= 0:
            continue
        direction = rng.choice(["bullish", "bearish"])
        stop_price = entry - risk if direction == "bullish" else entry + risk
        target = entry + reward if direction == "bullish" else entry - reward
        cost = 2 * (bars[idx].spread_open / 2.0)
        outcome = None
        for bar in bars[idx + 1: idx + 1 + HORIZON_BARS]:
            if direction == "bullish":
                if bar.bid_low <= stop_price:
                    outcome = -(risk + cost) / risk
                    break
                if bar.bid_high >= target:
                    outcome = (reward - cost) / risk
                    break
            else:
                if bar.bid_high >= stop_price:
                    outcome = -(risk + cost) / risk
                    break
                if bar.bid_low <= target:
                    outcome = (reward - cost) / risk
                    break
        if outcome is not None:
            out.append(outcome)
    return out


def stats(plans: list[dict], summary: dict, bars, rng: random.Random) -> dict:
    settled = [p for p in plans if p.get("state", "").startswith("settled")]
    ordered = sorted(settled, key=lambda p: p.get("exit_index") or 0)
    r = [p["r_measured"] for p in ordered if p.get("r_measured") is not None]
    lo, hi = bootstrap(r, rng)
    stops = [abs(p["entry"] - p["stop"]) * 10000 for p in ordered]
    frac = [p.get("stop_fraction_of_setup_candle") for p in ordered
            if p.get("stop_fraction_of_setup_candle")]
    rr1 = [p["rr_t1_measured"] for p in ordered if p.get("rr_t1_measured")]
    rr2 = [p["rr_t2_measured"] for p in ordered if p.get("rr_t2_measured")]
    cost = [p.get("cost_fraction_of_stop") for p in ordered if p.get("cost_fraction_of_stop")]
    same = [p for p in ordered if p.get("trigger_index") == p.get("exit_index")]
    null = null_baseline(ordered, bars) if bars else []
    nlo, nhi = bootstrap(null, random.Random(NULL_SEED))
    return {
        "variant": summary.get("variant", plans[0].get("variant") if plans else "?"),
        "decisions": summary.get("decisions"), "plans": summary.get("plans", len(plans)),
        "theses": summary.get("independent_theses", len(plans)),
        "settled": len(settled), "expired": sum(1 for p in plans if p.get("state") == "expired"),
        "same_bar": len(same), "mean_r": (statistics.mean(r) if r else None),
        "median_r": (statistics.median(r) if r else None), "sum_r": (sum(r) if r else None),
        "ci": (lo, hi), "n_r": len(r),
        "drawdown": drawdown(r), "streak": streak(r),
        "stop_pips_median": (statistics.median(stops) if stops else None),
        "stop_frac_median": (statistics.median(frac) if frac else None),
        "rr1_median": (statistics.median(rr1) if rr1 else None),
        "rr2_median": (statistics.median(rr2) if rr2 else None),
        "cost_frac_median": (statistics.median(cost) if cost else None),
        "null_mean": (statistics.mean(null) if null else None),
        "null_ci": (nlo, nhi), "null_n": len(null),
        "elapsed": summary.get("elapsed_seconds"),
        "peak_rss_kb": (summary.get("memory") or {}).get("peak_rss_kb"),
        "stopped": summary.get("stopped"),
        "reasons": summary.get("no_plan_reasons", {}),
    }


def fault_row(plan: dict) -> dict:
    if plan.get("state") == "settled_target":
        return {"plan": plan["plan_id"], "verdict": plan["state"], "category": "none visible",
                "evidence": "T1 touched before the stop under the conservative rule"}
    if plan.get("trigger_index") == plan.get("exit_index"):
        return {"plan": plan["plan_id"], "verdict": plan.get("state"),
                "category": "execution assumption", "evidence":
                "the entry bar itself reached the stop; entry and stop sit inside one 5m bar"}
    if plan.get("state") == "expired":
        return {"plan": plan["plan_id"], "verdict": "expired", "category": "none visible",
                "evidence": "the zone was never touched inside 288 bars"}
    return {"plan": plan["plan_id"], "verdict": plan.get("state"), "category": "stop",
            "evidence": "the stop was reached on a later bar, before T1"}


def case_md(plan: dict, decision: dict | None, kind: str) -> str:
    lines = [f"# CASE — {plan.get('variant')} — {'looks right' if kind == 'right' else 'looks wrong'}",
             "",
             f"plan `{plan['plan_id']}` · setup frame `{plan.get('setup_frame')}` · "
             f"decision {plan['decided_at']} (bar {plan['decision_index']})", "",
             "## A. AS OF t",
             f"- zone `{plan['zone']['zone_id']}` ({plan['zone']['kind']}) "
             f"[{plan['zone']['lower']}, {plan['zone']['upper']}], formed at setup index "
             f"{plan['zone']['formed_index']} on the {plan.get('setup_frame')} frame",
             f"- direction `{plan['direction']}`; bias `{plan['bias']}`; range position "
             f"`{plan['range_position']}`; session `{plan['session']}`",
             f"- entry `{plan['entry']}` ({plan['entry_rule']})",
             f"- stop `{plan['stop']}` ({plan['stop_rule']}, {plan.get('stop_distance_pips'):.2f} pips, "
             f"{plan.get('stop_fraction_of_setup_candle')} of the setup candle's range)",
             f"- T1 `{plan['t1']['level'] if plan['t1'] else None}` "
             f"({plan.get('t1_frame')} pool) · T2 `{plan['t2']['level'] if plan['t2'] else None}` "
             f"({plan.get('t2_frame')} pool, informational only)",
             f"- measured R:R to T1 `{round(plan['rr_t1_measured'], 3) if plan['rr_t1_measured'] else None}`; "
             f"half-spread `{plan['half_spread_at_decision']:.6f}`; cost as fraction of stop "
             f"`{plan.get('cost_fraction_of_stop'):.3f}`",
             "- criteria: " + json.dumps(plan.get("criteria")), "",
             "## B. HINDSIGHT",
             f"- state `{plan['state']}` / `{plan.get('exit_reason')}` at bar {plan.get('exit_index')}, "
             f"exit price `{plan.get('exit_price')}`",
             f"- R (half-spread both sides) = **{round(plan['r_measured'], 4) if plan.get('r_measured') is not None else None}**",
             f"- trigger bar {plan.get('trigger_index')} is the exit bar: "
             f"{plan.get('trigger_index') == plan.get('exit_index')}", "",
             "## C. MECHANICAL RECOMPUTATION",
             f"- risk = |entry − stop| = {abs(plan['entry'] - plan['stop']):.6f} "
             f"(record: {plan['risk_price']:.6f})",
             f"- rr_t1 recomputed = {abs(plan['t1']['level'] - plan['entry']) / abs(plan['entry'] - plan['stop']):.4f}"
             if plan.get("t1") else "- no T1", "",
             "## D. FAULT LOCATOR — HYPOTHESIS",
             f"- {fault_row(plan)['category']}: {fault_row(plan)['evidence']}"]
    return "\n".join(lines) + "\n\n## What this does NOT establish\n\n" \
        "- This case is one plan; it does not show that the variant is right or wrong.\n" \
        "- The fault category is a reading of stored fields, marked HYPOTHESIS.\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/tmp/build_v2")
    ap.add_argument("--data", default="/tmp/hud_data/2021.csv.gz")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "REPORT_M1_M2"))
    args = ap.parse_args()
    root = Path(args.root)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "CASES").mkdir(exist_ok=True)

    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "build_v1"))
    from stream_v1 import load_bars

    table: dict[str, dict[str, dict]] = {}
    all_plans: dict[str, dict[str, list[dict]]] = {}
    for tag, month in MONTHS.items():
        variants = VARIANTS if tag != "IN_SAMPLE" else ["V2-0", "V2-A", "V2-B"]
        bars = None
        for variant in variants:
            run_dir = root / f"{month}_{variant}"
            if not (run_dir / "run_summary.json").exists():
                continue
            summary, plans = load_run(run_dir)
            if bars is None:
                bars = load_bars(Path(args.data), "2021-01-01", f"{month}-28")
            row = stats(plans, summary, bars, random.Random(BOOTSTRAP_RESAMPLES))
            row["month"] = month
            table.setdefault(tag, {})[variant] = row
            all_plans.setdefault(tag, {})[variant] = plans

            faults = [fault_row(p) for p in plans if p.get("state", "").startswith("settled")]
            reasons = summary.get("no_plan_reasons", {})
            txt = [f"# SUMMARY — {month} / {variant}", "",
                   f"- decisions **{row['decisions']}**, plans **{row['plans']}**, independent theses "
                   f"**{row['theses']}**, settled {row['settled']}, expired {row['expired']}",
                   f"- settled on their own entry candle: **{row['same_bar']}**",
                   f"- mean R {row['mean_r'] if row['mean_r'] is None else round(row['mean_r'], 3)}, "
                   f"median R {row['median_r'] if row['median_r'] is None else round(row['median_r'], 3)}, "
                   f"sum {row['sum_r'] if row['sum_r'] is None else round(row['sum_r'], 3)}",
                   f"- bootstrap {int(BOOTSTRAP_LEVEL*100)}% CI of the mean R: "
                   f"[{row['ci'][0]:.3f}, {row['ci'][1]:.3f}] over {BOOTSTRAP_RESAMPLES} resamples "
                   f"(contains 0: {row['ci'][0] <= 0 <= row['ci'][1]})",
                   f"- max drawdown (verified formula) {round(row['drawdown'], 3)}; longest negative "
                   f"streak {row['streak']}",
                   f"- stop distance median {None if row['stop_pips_median'] is None else round(row['stop_pips_median'], 2)} pips, "
                   f"{None if row['stop_frac_median'] is None else round(row['stop_frac_median'], 3)} of the setup candle's range",
                   f"- median R:R to T1 {None if row['rr1_median'] is None else round(row['rr1_median'], 2)}, "
                   f"to T2 {None if row['rr2_median'] is None else round(row['rr2_median'], 2)}",
                   f"- half-spread cost as fraction of the stop, median "
                   f"{None if row['cost_frac_median'] is None else round(row['cost_frac_median'], 3)}",
                   f"- NULL baseline (random direction, same distances): mean R "
                   f"{None if row['null_mean'] is None else round(row['null_mean'], 3)}, CI "
                   f"[{row['null_ci'][0]:.3f}, {row['null_ci'][1]:.3f}], n={row['null_n']}",
                   f"- elapsed {row['elapsed']} s, peak RSS {row['peak_rss_kb']} kB, stopped {row['stopped']}",
                   "", "## No-plan reasons", "", "| reason | count |", "|---|---|"]
            for reason, count in reasons.items():
                txt.append(f"| {reason} | {count} |")
            txt += ["", "## Fault locator (HYPOTHESIS)", "", "| plan | verdict | category | evidence |",
                    "|---|---|---|---|"]
            for row2 in faults[:30]:
                txt.append(f"| `{row2['plan']}` | {row2['verdict']} | {row2['category']} | {row2['evidence']} |")
            txt += ["", "## What this does NOT establish", "",
                    "- A settled R is an accounting identity under a stated fill assumption, not a result "
                    "about a market.", "- The bootstrap interval is wide by construction when plans are few; "
                    "it is reported to be read, not to be beaten.", "- The NULL baseline is geometry plus "
                    "spread, not a strategy."]
            (out / f"SUMMARY_{month}_{variant}.md").write_text("\n".join(txt) + "\n", encoding="utf-8")

    # ---- comparison tables
    def cell(row: dict, key: str, fmt: str = "{:.3f}") -> str:
        value = row.get(key)
        if value is None:
            return "—"
        if isinstance(value, tuple):
            return "—"
        return fmt.format(value) if isinstance(value, float) else str(value)

    for tag, rows in table.items():
        lines = [f"# COMPARISON — {tag} ({', '.join(sorted({r['month'] for r in rows.values()}))})", "",
                 "| variant | decisions | plans | theses | settled | same-bar | mean R | median R | "
                 "bootstrap CI | drawdown | streak | stop pips (med) | stop / setup candle | R:R T1 | "
                 "NULL mean | NULL CI |",
                 "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for variant in [v for v in VARIANTS if v in rows]:
            r = rows[variant]
            lines.append(
                f"| {variant} | {r['decisions']} | {r['plans']} | {r['theses']} | {r['settled']} | "
                f"{r['same_bar']} | {cell(r, 'mean_r')} | {cell(r, 'median_r')} | "
                f"[{r['ci'][0]:.2f}, {r['ci'][1]:.2f}] | {cell(r, 'drawdown')} | {r['streak']} | "
                f"{cell(r, 'stop_pips_median', '{:.2f}')} | {cell(r, 'stop_frac_median')} | "
                f"{cell(r, 'rr1_median', '{:.2f}')} | {cell(r, 'null_mean')} | "
                f"[{r['null_ci'][0]:.2f}, {r['null_ci'][1]:.2f}] |")
        lines += ["", "## What this does NOT establish", "",
                  "- No variant is declared a winner. A row with a better mean R on one month is a "
                  "description of one month.", "- The intervals are wide; overlap is the normal case here."]
        (out / f"COMPARISON_{tag}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ---- cases: one right, one wrong for V2-A and V2-B on M1
    for variant in ("V2-A", "V2-B"):
        plans = all_plans.get("M1", {}).get(variant, [])
        settled = [p for p in plans if p.get("state", "").startswith("settled")]
        if not settled:
            continue
        right = next((p for p in settled if p["state"] == "settled_target"), None)
        wrong = next((p for p in settled if p["state"] == "settled_stop"
                      and p.get("trigger_index") != p.get("exit_index")), None) or \
            next((p for p in settled if p["state"] == "settled_stop"), None)
        if right:
            (out / "CASES" / f"CASE_{variant}_RIGHT.md").write_text(case_md(right, None, "right"), encoding="utf-8")
        if wrong:
            (out / "CASES" / f"CASE_{variant}_WRONG.md").write_text(case_md(wrong, None, "wrong"), encoding="utf-8")

    # ---- plain english
    m1 = table.get("M1", {})
    m2 = table.get("M2", {})
    def g(rows, v, k, fmt="{:.2f}"):
        value = rows.get(v, {}).get(k)
        return "—" if value is None else (fmt.format(value) if isinstance(value, float) else str(value))
    plain = f"""# What was tested — in plain English

1. In the first build the trading idea was read entirely from 5-minute candles. The stop that came out of that was about one pip wide.
2. A one-pip stop sits inside a single candle, so 64 of 106 plans were closed on the very candle that opened them.
3. This build tests one change: read the zone, the stop and the targets on a **slower** chart (15-minute, or 1-hour), and use the 5-minute chart only to decide **when price touches** the zone.
4. Everything else is held still: same days, same session window, same entry rule, same costs, same code for tracking the outcome.
5. A control version (V2-0) repeats the first build with only its bookkeeping defects repaired, so the difference between it and the two new versions is the chart the idea is read on.
6. Two months were chosen by a public draw before any data was opened: September 2021 and July 2021.
7. We also ran a "null" version: same entries, same stop and target distances, but the direction flipped by a coin (fixed seed). That shows what geometry and spread alone do.
8. Result, in one table (mean R per plan, hypothetical, after cost):

| month | v1 (5m) | V2-0 (5m + repairs) | V2-A (15m setup) | V2-B (1h setup) |
|---|---|---|---|---|
| 2021-09 | {g(m1,'v1','mean_r')} | {g(m1,'V2-0','mean_r')} | {g(m1,'V2-A','mean_r')} | {g(m1,'V2-B','mean_r')} |
| 2021-07 | {g(m2,'v1','mean_r')} | {g(m2,'V2-0','mean_r')} | {g(m2,'V2-A','mean_r')} | {g(m2,'V2-B','mean_r')} |
| null (coin) | {g(m1,'v1','null_mean')} / {g(m2,'v1','null_mean')} | — | — | — |

9. The slower chart did what it should mechanically: the stop became wider and fewer plans died on the entry candle. Whether the money result improved is a separate question — see the comparison tables, and note that the intervals are wide and overlap.
10. Nothing here proves anything about the future, and no version is declared the winner.

## What this does NOT establish

- It does not establish that a 15-minute or 1-hour reading is the right one; it measures two months of one instrument.
- It does not establish profitability: R is hypothetical, no position was ever opened, and the sample is small.
"""
    (out / "PLAIN_ENGLISH.md").write_text(plain, encoding="utf-8")

    manifest = {f"{tag}/{v}": table[tag][v] for tag in table for v in table[tag]}
    (out / "ALL_STATS.json").write_text(json.dumps(manifest, indent=1, default=str), encoding="utf-8")
    hashes = []
    for path in sorted(out.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            hashes.append(f"{sha256(path)}  {path.relative_to(out)}")
    (out / "SHA256SUMS.txt").write_text("\n".join(hashes) + "\n", encoding="utf-8")
    print(json.dumps({k: {v: table[k][v]["mean_r"] for v in table[k]} for k in table}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
