#!/usr/bin/env python3
"""Stage 6 statistics.  Reads only the saved V3 run directories in /tmp/build_v3.

Everything is declared in DECLARED_CHOICES_V3 E/F.  The bootstrap and the permutation test are
written here (no scipy); the seed is 20261109 for both.
"""

from __future__ import annotations

import json
import math
import random
import statistics
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path("/tmp/build_v3")
OUT = HERE / "REPORT_V3"
SEED = 20261109
B = 10000
PERMS = 10000
MONTHS = ("2021-11", "2021-10")
FRAMES = ("15m", "1h")
SWITCHES = ("V3-S1", "V3-S2", "V3-L", "V3-E", "V3-R", "V3-T", "V3-FULL")


def load(run_dir: Path) -> list[dict]:
    path = run_dir / "plans_final.jsonl"
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def summary(run_dir: Path) -> dict:
    path = run_dir / "run_summary.json"
    return json.loads(path.read_text()) if path.exists() else {}


def settled(plans: list[dict]) -> list[dict]:
    return [p for p in plans if p.get("state") == "settled" and p.get("r_measured") is not None]


def hit_of(plan: dict) -> int:
    return 1 if plan.get("exit_reason") == "t1_touched" else 0


def p_star(plan: dict) -> float | None:
    rr = plan.get("rr_t1")
    if rr is None or rr <= 0:
        return None
    return 1.0 / (1.0 + rr)


def excess(plan: dict) -> float | None:
    p = p_star(plan)
    return None if p is None else hit_of(plan) - p


def wilson(hits: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    z = 1.959963984540054
    p = hits / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (centre - half, centre + half)


def day_bootstrap(values_by_day: dict[str, list[float]], seed: int = SEED) -> tuple[float, float]:
    days = sorted(values_by_day)
    if not days:
        return (float("nan"), float("nan"))
    rng = random.Random(seed)
    means = []
    for _ in range(B):
        pick = [rng.choice(days) for _ in range(len(days))]
        vals = [v for d in pick for v in values_by_day[d]]
        if vals:
            means.append(sum(vals) / len(vals))
    means.sort()
    lo = means[int(0.025 * len(means))]
    hi = means[int(0.975 * len(means)) - 1]
    return (lo, hi)


def group_by_day(plans: list[dict], metric) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}
    for plan in plans:
        value = metric(plan)
        if value is None:
            continue
        day = plan["decided_at"][:10]
        out.setdefault(day, []).append(value)
    return out


def mean(values):
    return sum(values) / len(values) if values else None


def table_61() -> dict:
    rows = {}
    for month in MONTHS:
        for frame in FRAMES:
            for variant in ("V3-0",) + SWITCHES + ("WIDE", "NULL"):
                plans = load(ROOT / f"{month}_{variant}_{frame}")
                if not plans:
                    continue
                s = settled(plans)
                hits = sum(hit_of(p) for p in s)
                ex = [e for e in (excess(p) for p in s) if e is not None]
                ex_days = group_by_day(s, excess)
                lo, hi = day_bootstrap(ex_days) if ex else (float("nan"), float("nan"))
                pips = [p["stop_pips"] for p in plans if p.get("stop_pips")]
                rows[f"{month}|{frame}|{variant}"] = {
                    "plans": len(plans), "cancelled": sum(1 for p in plans if p.get("state") == "cancelled"),
                    "expired": sum(1 for p in plans if p.get("state") == "expired"),
                    "settled": len(s), "hits": hits,
                    "hit_rate": hits / len(s) if s else None,
                    "hit_ci": wilson(hits, len(s)),
                    "mean_r": mean([p["r_measured"] for p in s]),
                    "median_r": statistics.median([p["r_measured"] for p in s]) if s else None,
                    "mean_excess": mean(ex), "excess_ci": (lo, hi),
                    "settled_on_fill_bar": sum(1 for p in s if p.get("exit_index") == p.get("fill_index")),
                    "stop_pips": {"min": min(pips) if pips else None,
                                  "median": statistics.median(pips) if pips else None,
                                  "max": max(pips) if pips else None},
                    "days": len({p["decided_at"][:10] for p in plans}),
                }
    return rows


def paired(month: str, frame: str, variant: str) -> dict:
    base = {p["thesis_id"]: p for p in load(ROOT / f"{month}_V3-0_{frame}")}
    other = {p["thesis_id"]: p for p in load(ROOT / f"{month}_{variant}_{frame}")}
    common = sorted(set(base) & set(other))
    deltas = []
    per_day: dict[str, list[float]] = {}
    for key in common:
        a, b = excess(base[key]), excess(other[key])
        if a is None or b is None:
            continue
        if base[key].get("state") != "settled" or other[key].get("state") != "settled":
            continue
        d = b - a
        deltas.append(d)
        per_day.setdefault(base[key]["decided_at"][:10], []).append(d)
    ci = day_bootstrap(per_day) if deltas else (float("nan"), float("nan"))
    # leave-one-day-out sign stability
    signs = []
    for day in sorted(per_day):
        rest = [v for d, vals in per_day.items() if d != day for v in vals]
        if rest:
            signs.append(1 if mean(rest) > 0 else -1 if mean(rest) < 0 else 0)
    # permutation: subset (deltas) versus random subsets of the same size drawn from the pooled
    # settled plans of both variants (paired-free, declared as such)
    pooled = [p for p in list(base.values()) + list(other.values())
              if p.get("state") == "settled" and excess(p) is not None]
    rng = random.Random(SEED)
    observed = mean(deltas) if deltas else 0.0
    hits = 0
    for _ in range(PERMS):
        rng.shuffle(pooled)
        half = len(pooled) // 2
        a = [excess(p) for p in pooled[:half]]
        b = [excess(p) for p in pooled[half:half + len(deltas)]]
        if observed >= 0:
            if mean(b) - mean(a) >= observed:
                hits += 1
        else:
            if mean(b) - mean(a) <= observed:
                hits += 1
    return {"month": month, "frame": frame, "variant": variant, "common": len(common),
            "added": len(set(other) - set(base)), "removed": len(set(base) - set(other)),
            "n_pairs": len(deltas), "delta_mean": observed, "delta_ci": ci,
            "loo_signs": signs, "loo_stable": len(signs) > 0 and all(s == (1 if observed > 0 else -1)
                                                                     for s in signs),
            "p_perm": (hits + 1) / (PERMS + 1)}


def holm(pvalues: list[tuple[str, float]]) -> dict[str, float]:
    ordered = sorted(pvalues, key=lambda kv: kv[1])
    m = len(ordered)
    adjusted = {}
    running = 0.0
    for i, (name, p) in enumerate(ordered):
        adj = min(1.0, (m - i) * p)
        running = max(running, adj)
        adjusted[name] = running
    return adjusted


def main() -> None:
    OUT.mkdir(exist_ok=True)
    rows = table_61()
    tests = []
    pairs = {}
    for month in MONTHS:
        for frame in FRAMES:
            for variant in SWITCHES:
                result = paired(month, frame, variant)
                pairs[f"{month}|{frame}|{variant}"] = result
                tests.append((f"{month}|{frame}|{variant}", result["p_perm"]))
    adjusted = holm(tests)
    for key, value in adjusted.items():
        pairs[key]["p_holm"] = value
    # declared label rule (F)
    labels = {}
    for frame in FRAMES:
        for variant in SWITCHES:
            a = pairs.get(f"2021-11|{frame}|{variant}")
            b = pairs.get(f"2021-10|{frame}|{variant}")
            if not a or not b:
                continue
            ok = (a["delta_ci"][0] > 0 and b["delta_ci"][0] > 0 and a["loo_stable"] and b["loo_stable"]) or \
                 (a["delta_ci"][1] < 0 and b["delta_ci"][1] < 0 and a["loo_stable"] and b["loo_stable"])
            if ok:
                label = "CANDIDATE_FOR_CONFIRMATION"
            elif (a["delta_mean"] or 0) * (b["delta_mean"] or 0) > 0 and abs(a["delta_mean"] or 0) > 1e-9:
                label = "INCONCLUSIVE"
            else:
                label = "NO_SIGNAL"
            labels[f"{frame}|{variant}"] = {"label": label,
                                            "delta_n1": a["delta_mean"], "ci_n1": a["delta_ci"],
                                            "delta_n2": b["delta_mean"], "ci_n2": b["delta_ci"]}
    payload = {"rows": rows, "pairs": pairs, "labels": labels,
               "declared_tests": len(tests)}
    (OUT / "STATS_V3.json").write_text(json.dumps(payload, indent=1, default=str), encoding="utf-8")

    lines = ["# V3 statistics tables (generated)", "",
             "Seed 20261109, B=10,000 day-cluster bootstrap, 10,000 permutations, "
             f"{len(tests)} declared tests, Holm over that count.", ""]
    lines.append("## 6.1 per run")
    lines.append("```")
    lines.append(f"{'run':34s} {'plans':>5s} {'cxl':>4s} {'exp':>4s} {'set':>4s} {'hit':>4s} "
                 f"{'hit_ci':>15s} {'meanR':>7s} {'medR':>7s} {'excess':>7s} {'excess_ci':>17s} {'pips_med':>8s}")
    for key, r in rows.items():
        lines.append(f"{key:34s} {r['plans']:5d} {r['cancelled']:4d} {r['expired']:4d} "
                     f"{r['settled']:4d} {r['hits']:4d} [{r['hit_ci'][0]:.2f},{r['hit_ci'][1]:.2f}]  "
                     f"{0 if r['mean_r'] is None else r['mean_r']:7.3f} "
                     f"{0 if r['median_r'] is None else r['median_r']:7.3f} "
                     f"{0 if r['mean_excess'] is None else r['mean_excess']:7.4f} "
                     f"[{r['excess_ci'][0]:.3f},{r['excess_ci'][1]:.3f}] "
                     f"{0 if r['stop_pips']['median'] is None else r['stop_pips']['median']:8.2f}")
    lines.append("```")
    lines.append("## 6.2 paired deltas versus V3-0 (primary metric = excess-hit)")
    lines.append("```")
    lines.append(f"{'test':26s} {'common':>6s} {'add':>4s} {'rem':>4s} {'delta':>8s} {'ci':>18s} "
                 f"{'p':>7s} {'p_holm':>7s} {'loo_stable':>10s}")
    for key, r in pairs.items():
        lines.append(f"{key:26s} {r['common']:6d} {r['added']:4d} {r['removed']:4d} "
                     f"{r['delta_mean']:8.4f} [{r['delta_ci'][0]:.3f},{r['delta_ci'][1]:.3f}] "
                     f"{r['p_perm']:7.4f} {r['p_holm']:7.4f} {str(r['loo_stable']):>10s}")
    lines.append("```")
    lines.append("## 6.2b labels per the declared rule F")
    lines.append("```")
    for key, value in labels.items():
        lines.append(f"{key:16s} {value['label']:28s} N1 {value['delta_n1'] if value['delta_n1'] is not None else 0:8.4f} "
                     f"N2 {value['delta_n2'] if value['delta_n2'] is not None else 0:8.4f}")
    lines.append("```")
    (OUT / "TABLES_6_1_6_2.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"runs": len(rows), "tests": len(tests)}, indent=1))


if __name__ == "__main__":
    main()
