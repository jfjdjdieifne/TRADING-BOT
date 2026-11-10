#!/usr/bin/env python3
"""Predeclared paired, day-clustered inference for scalp v1.

The declared family is 20 tests, printed here and in REPORT_SCALP before any inference is read:
5 months x 2 forms x excess-hit and mean R.  Paired controls are grouped per event; bootstrap and
permutation operate on day clusters.  All extra configurations remain descriptive.

What this does NOT establish: these exploratory results are not independent confirmation.
"""
from __future__ import annotations
import json, math, random, statistics
from pathlib import Path

ROOT = Path("/tmp/build_scalp")
OUT = Path(__file__).resolve().parent / "REPORT_SCALP"
MONTHS = ("2021-06", "2021-07", "2021-09", "2021-10", "2021-11")
SEED = 20261109
B = 10000
PERMS = 10000
DECLARED = 20


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def value(row: dict, metric: str) -> float | None:
    return row.get("excess_hit") if metric == "excess_hit" else row.get("r")


def paired_events(plans: list[dict], controls: list[dict], form: int, metric: str) -> list[dict]:
    plan_by_event = {(p.get("s_index"), p.get("h_index")): p
                     for p in plans if p.get("config") == "PRIMARY"}
    cs: dict[tuple, list[dict]] = {}
    for c in controls:
        if c.get("state") != "settled":
            continue
        key = (c.get("for_s_index"), c.get("for_h_index"))
        # The first run records predate `for_form`; its unique PRIMARY event is authoritative.
        event_plan = plan_by_event.get(key)
        control_form = c.get("for_form", event_plan.get("form") if event_plan else None)
        if control_form != form:
            continue
        cs.setdefault(key, []).append(c)
    out = []
    for p in plans:
        if p.get("config") != "PRIMARY" or p.get("form") != form or p.get("state") != "settled":
            continue
        key = (p.get("s_index"), p.get("h_index"))
        matches = cs.get(key, [])
        pv = value(p, metric)
        cvs = [value(c, metric) for c in matches]
        cvs = [x for x in cvs if x is not None]
        if pv is None or not cvs:
            continue
        out.append({"day": p["s_start"][:10], "event": pv,
                    "control": sum(cvs) / len(cvs), "delta": pv - sum(cvs) / len(cvs),
                    "s_index": key[0], "h_index": key[1], "n_control": len(cvs),
                    "rr": p.get("rr"), "hit": p.get("exit_reason") == "target",
                    "bars_to_target": p.get("bars_to_target"), "mae_r": p.get("mae_r"),
                    "reached_half_target": p.get("reached_half_target")})
    return out


def mean(xs: list[float]) -> float | None:
    return sum(xs) / len(xs) if xs else None


def cluster_bootstrap(rows: list[dict], seed: int) -> tuple[float | None, float | None]:
    groups: dict[str, list[float]] = {}
    for row in rows:
        groups.setdefault(row["day"], []).append(row["delta"])
    days = sorted(groups)
    if len(days) < 2:
        return None, None
    rng = random.Random(seed)
    sims = []
    for _ in range(B):
        chosen = [rng.choice(days) for _ in days]
        vals = [v for d in chosen for v in groups[d]]
        sims.append(sum(vals) / len(vals))
    sims.sort()
    return sims[int(.025 * B)], sims[int(.975 * B) - 1]


def cluster_permutation(rows: list[dict], seed: int) -> float:
    groups: dict[str, list[float]] = {}
    for row in rows:
        groups.setdefault(row["day"], []).append(row["delta"])
    days = sorted(groups)
    if not days:
        return 1.0
    observed = mean([r["delta"] for r in rows]) or 0.0
    rng = random.Random(seed)
    extreme = 0
    for _ in range(PERMS):
        vals = []
        for day in days:
            sign = -1 if rng.getrandbits(1) else 1
            vals.extend(sign * v for v in groups[day])
        test = sum(vals) / len(vals)
        if abs(test) >= abs(observed) - 1e-15:
            extreme += 1
    return (extreme + 1) / (PERMS + 1)


def holm(pairs: list[tuple[str, float]]) -> dict[str, float]:
    ranked = sorted(pairs, key=lambda kv: kv[1])
    out, running, m = {}, 0.0, len(ranked)
    for i, (name, p) in enumerate(ranked):
        running = max(running, min(1.0, (m - i) * p))
        out[name] = running
    return out


def main() -> None:
    OUT.mkdir(exist_ok=True)
    by_month = {m: (load(ROOT / m / "plans.jsonl"), load(ROOT / m / "controls.jsonl"),
                    json.loads((ROOT / m / "run_summary.json").read_text())) for m in MONTHS}
    print(f"PRE-RUN DECLARATION: {DECLARED} tests = 5 months x 2 forms x 2 metrics; B={B}; permutations={PERMS}; Holm family={DECLARED}.")
    rows, pvals, paired = [], [], {}
    for month in MONTHS:
        plans, controls, _ = by_month[month]
        for form in (1, 2):
            for metric in ("excess_hit", "mean_r"):
                obs = paired_events(plans, controls, form, metric)
                key = f"{month}|form{form}|{metric}"
                paired[key] = obs
                ci = cluster_bootstrap(obs, SEED + len(rows))
                p = cluster_permutation(obs, SEED + len(rows)) if obs else 1.0
                event_values = [r["event"] for r in obs]
                control_values = [r["control"] for r in obs]
                deltas = [r["delta"] for r in obs]
                days = len({r["day"] for r in obs})
                rows.append({"month": month, "form": form, "metric": metric,
                             "n_events": len(obs), "n_days": days,
                             "event_mean": mean(event_values), "matched_control_mean": mean(control_values),
                             "paired_delta": mean(deltas), "paired_ci95": ci,
                             "mde_ci_halfwidth": ((ci[1] - ci[0]) / 2 if ci[0] is not None else None),
                             "p_cluster_permutation": p})
                pvals.append((key, p))
    adjusted = holm(pvals)
    for row in rows:
        key = f"{row['month']}|form{row['form']}|{row['metric']}"
        row["p_holm"] = adjusted[key]

    decisions = []
    for form in (1, 2):
        for metric in ("excess_hit", "mean_r"):
            candidates = [r for r in rows if r["form"] == form and r["metric"] == metric]
            eligible = []
            for row in candidates:
                lo, hi = row["paired_ci95"]
                sign = 1 if row["paired_delta"] is not None and row["paired_delta"] > 0 else -1
                loo = []
                obs = paired[f"{row['month']}|form{form}|{metric}"]
                for day in sorted({x["day"] for x in obs}):
                    vals = [x["delta"] for x in obs if x["day"] != day]
                    if vals:
                        loo.append(1 if sum(vals) / len(vals) > 0 else -1)
                robust_loo = bool(loo) and all(x == sign for x in loo)
                row["lodo_signs"] = loo
                row["lodo_same_sign"] = robust_loo
                excludes_zero = lo is not None and ((lo > 0) or (hi < 0))
                if excludes_zero and row["p_holm"] < .05 and robust_loo:
                    eligible.append((row["month"], sign))
            pos = sum(1 for _, sign in eligible if sign > 0)
            neg = sum(1 for _, sign in eligible if sign < 0)
            underpowered = (sum(1 for r in candidates if r["n_days"] < 2) >= 2 or
                            (metric == "excess_hit" and bool([r for r in candidates if r["n_events"]]) and
                             all(r["mde_ci_halfwidth"] is None or r["mde_ci_halfwidth"] > 0.10
                                 for r in candidates if r["n_events"])))
            label = "CANDIDATE_FOR_CONFIRMATION" if max(pos, neg) >= 2 else ("UNDERPOWERED" if underpowered else "NO_SIGNAL")
            nonzero = [1 if (r["paired_delta"] or 0) > 0 else -1 for r in candidates if r["n_events"]]
            consistency = (max(nonzero.count(1), nonzero.count(-1)) / len(nonzero)) if nonzero else None
            decisions.append({"form": form, "metric": metric, "label": label,
                              "holm_ci_lodo_months": eligible,
                              "sign_consistency_fraction": consistency,
                              "months_with_data": sum(1 for r in candidates if r["n_events"]),
                              "mde_by_month": {r["month"]: r["mde_ci_halfwidth"] for r in candidates}})

    # descriptive: alternative variants and shorts, plain hit next to event-specific break-even.
    descriptive, excluded, days_sensitivity = {}, {}, {}
    for month, (plans, controls, summary) in by_month.items():
        for config in ("PRIMARY", "window_2", "large_body", "large_loose", "shorts"):
            ev = [p for p in plans if p.get("config") == config and p.get("state") == "settled"]
            if not ev:
                continue
            rrs = [p["rr"] for p in ev if p.get("rr")]
            descriptive[f"{month}|{config}"] = {
                "n": len(ev), "n_days": len({p["s_start"][:10] for p in ev}),
                "hit_count": sum(p.get("exit_reason") == "target" for p in ev),
                "plain_hit_rate": sum(p.get("exit_reason") == "target" for p in ev) / len(ev),
                "breakeven_mean_1_over_1_plus_rr": mean([1 / (1 + x) for x in rrs]),
                "mean_R_net_of_spread": mean([p["r"] for p in ev]),
                "mean_excess_hit": mean([p["excess_hit"] for p in ev if p.get("excess_hit") is not None]),
                "ambiguous_bars": sum(p.get("ambiguous_bars", 0) for p in ev),
                "sub_pip_count": sum(bool(p.get("sub_pip")) for p in ev),
                "expired_count": sum(p.get("exit_reason") == "expired" for p in ev),
                "mean_MAE_r": mean([p["mae_r"] for p in ev if p.get("mae_r") is not None]),
                "median_bars_to_target": statistics.median([p.get("bars_to_target", p.get("bars_held")) for p in ev if p.get("exit_reason") == "target"]) if any(p.get("exit_reason") == "target" for p in ev) else None,
                "share_reaching_half_target_before_stop": mean([1.0 if p.get("reached_half_target") else 0.0 for p in ev]) if any("reached_half_target" in p for p in ev) else None}
        for config in ("PRIMARY", "shorts"):
            ev = [p for p in plans if p.get("config") == config]
            excluded[f"{month}|{config}"] = {"events": len(ev),
                "excluded": sum(p.get("state") == "excluded" for p in ev),
                "target_behind": sum(p.get("excluded") == "TARGET_BEHIND_ENTRY" for p in ev),
                "no_target": sum(p.get("excluded") == "NO_TARGET_SWING" for p in ev),
                "expired": sum(p.get("exit_reason") == "expired" for p in ev),
                "sub_pip": sum(bool(p.get("sub_pip")) for p in ev)}
        for form in (1, 2):
            for metric in ("excess_hit", "mean_r"):
                obs = paired[f"{month}|form{form}|{metric}"]
                first = {}
                for x in obs:
                    first.setdefault(x["day"], x)
                vals = [x["delta"] for x in first.values()]
                days_sensitivity[f"{month}|form{form}|{metric}"] = {
                    "first_event_per_day_n": len(vals), "paired_delta": mean(vals)}

    payload = {"declared_tests": DECLARED, "test_rows": rows, "decisions": decisions,
               "descriptive_runs": descriptive, "excluded_counts": excluded,
               "first_event_per_day": days_sensitivity,
               "run_summaries": {m: {k: by_month[m][2].get(k) for k in
                  ("loaded_from", "loaded_until", "window_end_exclusive", "months_loaded",
                   "reserved_months_loaded", "primary_settled", "primary_hits", "controls", "configs")}
                  for m in MONTHS}}
    (OUT / "STATS_SCALP.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = ["# SCALP v1 — predeclared statistical report", "",
             f"**Declared tests: {DECLARED}; rows: {len(rows)}.** All declared tests were run. "
             f"Day-cluster bootstrap B={B}; paired, day-cluster sign permutation={PERMS}; Holm correction over all {DECLARED} tests.", "",
             "The experimental unit is an event; for each event, its outcome is compared with the mean of that event's same-hour, same-month matched controls. "
             "Confidence intervals and permutation preserve within-day clustering. MDE is reported as the 95% interval half-width, not a claim of detectability at a chosen effect size.", "",
             "## Declared family: all 20 tests", "",
             "| Month | Form | Metric | n events | n days | Event mean | Matched-control mean | Paired difference | 95% paired cluster CI | MDE (half-width) | Perm p | Holm p | LODO signs |",
             "|---|---:|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---|"]
    for r in rows:
        lo, hi = r["paired_ci95"]
        fmt = lambda x: "—" if x is None else f"{x:.4f}"
        lines.append(f"| {r['month']} | {r['form']} | {r['metric']} | {r['n_events']} | {r['n_days']} | {fmt(r['event_mean'])} | {fmt(r['matched_control_mean'])} | {fmt(r['paired_delta'])} | "
                     f"{('—' if lo is None else f'[{lo:.4f}, {hi:.4f}]')} | {fmt(r['mde_ci_halfwidth'])} | {r['p_cluster_permutation']:.4f} | {r['p_holm']:.4f} | {r.get('lodo_signs', [])} |")
    lines += ["", "## Decision labels", "", "| Form | Metric | Label | sign consistency | qualifying months after Holm + CI + LODO |", "|---:|---|---|---|"]
    for d in decisions:
        lines.append(f"| {d['form']} | {d['metric']} | **{d['label']}** | {d['holm_ci_lodo_months']} |")
    lines += ["", "## Descriptive runs (outside the declared family)", "",
              "Plain hit rate is shown next to event-level break-even `1/(1+RR)`. These rows do not enter the declared family.", "",
              "| Month/config | n | hit rate | break-even | mean R net of spread | excess-hit | ambiguous | sub-pip | expired | mean MAE (R) | median bars to T | share reaching half T before stop |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for key, d in descriptive.items():
        f=lambda k: "—" if d.get(k) is None else f"{d[k]:.4f}"
        lines.append(f"| {key} | {d['n']} | {f('plain_hit_rate')} | {f('breakeven_mean_1_over_1_plus_rr')} | {f('mean_R_net_of_spread')} | {f('mean_excess_hit')} | {d['ambiguous_bars']} | {d['sub_pip_count']} | {d['expired_count']} | {f('mean_MAE_r')} | {d['median_bars_to_target']} | {f('share_reaching_half_target_before_stop')} |")
    lines += ["", "## Exclusions and sensitivities", ""]
    for key, d in excluded.items():
        lines.append(f"- {key}: events={d['events']}, excluded={d['excluded']}, TARGET_BEHIND_ENTRY={d['target_behind']}, NO_TARGET_SWING={d['no_target']}, expired={d['expired']}, sub-pip={d['sub_pip']}.")
    lines += ["", "First-event-per-day paired-difference sensitivity:", ""]
    for key, d in days_sensitivity.items():
        lines.append(f"- {key}: n={d['first_event_per_day_n']}, paired difference={d['paired_delta']}.")
    lines += ["", "## Measurement availability and fault locator", "",
              "The five frozen exploratory run bundles predate added MAE / half-target fields, next-bar-open reruns, and the half-body H-level sensitivity. Do not rerun these already-seen months: those measures are unavailable here (bars-to-target is recoverable as bars_held for target hits); they are not silently imputed. The half-body H-level owner sensitivity was omitted from the initial pre-run declarations and is recorded now as not analyzed, not as a valid preregistered result.",
              "The shorts calculation was corrected before the five run bundles were made; its secondary outcomes are included separately, not pooled. The 1B diagnostic implementation now enforces the intervening bullish candle; the earlier 1B records do not reliably establish that condition and are omitted from outcome tables.",
              "The primary family is sparse (many month/form cells have few events or days); MDE intervals are wide and generally do not exclude zero. This is NO_SIGNAL or UNDERPOWERED, not evidence of equivalence.",
              "The detector should be checked against the owner case cards. Any suspected detector issue must be entered in VARIANT_LOG_SCALP.md; no changes or reruns on these seen months are permitted.", "",
              "## What this does NOT establish", "",
              "- It does not establish a working strategy, HYPOTHETICAL_ profitability, or performance outside these exploratory samples.",
              "- The exploratory months are seen; one currency pair and one year are represented.",
              "- CANDIDATE_FOR_CONFIRMATION, if ever assigned, would not mean a working strategy.",
              "- The target buffer is an engineering choice and its intent is a knowledge gap.",
              "- MAE, the half-target-before-stop measure, next-bar-open sensitivity, corrected 1B outcomes, and half-body H-level sensitivity were not generated in the frozen runs; no rerun was made on seen months.",
              "- Cards check whether the owner pattern was read correctly, not HYPOTHETICAL_ profitability.",
              "- 2021-10 is IN_SAMPLE; the v3 round on 2021-12 was waived by owner decision.", ""]
    (OUT / "TABLES_SCALP.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"declared": DECLARED, "rows": len(rows), "decisions": decisions}, indent=2))

if __name__ == "__main__":
    main()

# What this does NOT establish: it does not establish strategy validity or HYPOTHETICAL_ profitability.
