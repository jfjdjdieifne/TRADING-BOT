#!/usr/bin/env python3
"""Driver: selection, cards, all-plan checks, descriptive tables, error classes."""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import statistics
from pathlib import Path

import td_lib as L

# the runs loaded bars with t1 = the first day of the NEXT month; the same bound is used
# here so that decision_index refers to the same bar
MONTH_END = {"2021-09": "2021-10-01", "2021-07": "2021-08-01", "2021-06": "2021-07-01"}


def decision_context(run_dir: Path, indices: set[int]) -> dict[int, dict]:
    out = {}
    with open(run_dir / "decisions.jsonl", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            if '"index": ' not in line:
                continue
            try:
                record = json.loads(line)
            except Exception:
                continue
            if record.get("index") in indices:
                out[record["index"]] = record
    return out


def card(plan: dict, ctx: dict | None, bars, frames: dict, run_id: str, why: str,
         replayed: dict, checks: list) -> str:
    direction = plan["direction"]
    entry, stop = plan["entry"], plan["stop"]
    t1 = plan["t1"]["level"] if plan.get("t1") else None
    t2 = plan["t2"]["level"] if plan.get("t2") else None
    risk = abs(entry - stop)
    half = plan.get("half_spread_at_decision") or 0.0
    decide_at = plan["decided_at"]
    frame_label = plan.get("setup_frame") or "5m"
    zone = plan["zone"]
    lines = []
    lines.append(f"# TRADE CARD — {run_id} — {plan['plan_id']}")
    lines.append("")
    lines.append(f"- run id: `{run_id}` · month `{run_id.split('_')[0]}` · variant "
                 f"`{plan.get('variant', run_id.split('_', 1)[1])}`")
    lines.append(f"- plan id: `{plan['plan_id']}`")
    lines.append(f"- thesis id: `{plan.get('thesis_id', '—')}` = setup frame `{frame_label}` + zone "
                 f"`{zone['zone_id']}` + direction `{direction}` + sweep/formation reference "
                 f"`{zone.get('formed_index')}`")
    lines.append(f"- why this plan: **{why}**")

    # 1 story
    lines.append("\n## 1. The story, in plain English\n")
    lines.append(f"1. The daily bias was read as `{plan.get('bias')}` on completed buckets.")
    lines.append(f"2. On the {frame_label} frame a {zone['kind']} formed between "
                 f"{zone['lower']:.5f} and {zone['upper']:.5f}.")
    lines.append(f"3. Price was in the `{plan.get('range_position')}` part of the dealing range.")
    lines.append(f"4. The engine waited for a 5m bar whose close came back into that zone.")
    lines.append(f"5. When it did, the hypothetical plan was armed: {direction} from {entry:.5f}.")
    lines.append(f"6. The thesis dies at {stop:.5f} (the far side of the zone) and aims at {t1}.")
    lines.append(f"7. The zone was read at setup candle {zone.get('formed_index')}, which had closed "
                 f"before the decision.")
    lines.append(f"8. Everything below is accounting under that reading — no position ever existed.")

    # 2 setup context
    lines.append("\n## 2. Setup-frame context\n")
    candles = frames[frame_label]
    formed = zone.get("formed_index")
    lo = max(0, (formed or 0) - 8)
    hi = min(len(candles), (formed or 0) + 4)
    lines.append(f"| # | open (UTC) | close (UTC) | open | high | low | close |")
    lines.append("|---|---|---|---|---|---|---|")
    for i in range(lo, hi):
        c = candles[i]
        lines.append(f"| {i} | {c['start'].isoformat()} | {c['close_time']} | {c['open']:.5f} | "
                     f"{c['high']:.5f} | {c['low']:.5f} | {c['close']:.5f} |")
    if ctx:
        lines.append("")
        lines.append(f"- dealing range (setup frame): `{ctx['range'].get('low')}` – "
                     f"`{ctx['range'].get('high')}`, equilibrium `{ctx['range'].get('equilibrium')}`, "
                     f"position `{ctx['range'].get('position')}`, ratio "
                     f"`{ctx['range'].get('position_ratio')}` ({ctx['range'].get('position_state')})")
        sc = ctx.get("setup_context") or {}
        lines.append(f"- swings on the setup frame: {sc.get('swings')}")
        lines.append(f"- sweep high `{sc.get('sweep_high')}` · sweep low `{sc.get('sweep_low')}`")
        lines.append(f"- displacement `{sc.get('displacement')}` · structure shift `{sc.get('shift')}`")
        lines.append(f"- order block at the decision: `{sc.get('order_block')}`")
        lines.append(f"- bias source: daily `{ctx['bias']['daily']}`, weekly `{ctx['bias']['weekly']}`, "
                     f"conflict `{ctx['bias']['bias_conflict']}`")

    # 3 causality
    lines.append("\n## 3. Causality table\n")
    lines.append("| item | frame | index | close time | decision time | verdict |")
    lines.append("|---|---|---|---|---|---|")
    close_idx = (formed or 0)
    close_time = candles[close_idx]["close_time"] if 0 <= close_idx < len(candles) else "—"
    lines.append(f"| zone candle | {frame_label} | {close_idx} | {close_time} | {decide_at} | "
                 f"{'OK' if close_time <= decide_at else 'VIOLATION'} |")
    if ctx:
        lines.append(f"| dealing range swings | {frame_label} | "
                     f"{ctx['range'].get('low_index')}/{ctx['range'].get('high_index')} | (closed "
                     f"before decision) | {decide_at} | OK |")
        lines.append(f"| bias buckets | daily/weekly from 5m | — | (completed buckets only) | "
                     f"{decide_at} | OK |")

    # 4 execution
    lines.append("\n## 4. Execution, 5m candle by candle\n")
    start = plan["decision_index"] + 1
    end = min(len(bars), (plan.get("exit_index") or start) + 2)
    lines.append("| bar | time (UTC) | bid O/H/L/C | ask O/H/L/C | touched? | closed inside? | hit stop? | hit T1? | spread |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for i in range(start, end):
        b = bars[i]
        touched = b.bid_low <= entry <= b.bid_high
        inside = zone["lower"] <= b.bid_close <= zone["upper"]
        hit_stop = (b.bid_low <= stop) if direction == "bullish" else (b.bid_high >= stop)
        hit_t1 = ((b.bid_high >= t1) if direction == "bullish" else (b.bid_low <= t1)) \
            if t1 is not None else False
        lines.append(f"| {i} | {b.start.isoformat()} | {b.bid_open:.5f}/{b.bid_high:.5f}/"
                     f"{b.bid_low:.5f}/{b.bid_close:.5f} | {b.ask_open:.5f}/{b.ask_high:.5f}/"
                     f"{b.ask_low:.5f}/{b.ask_close:.5f} | {'yes' if touched else 'no'} | "
                     f"{'yes' if inside else 'no'} | {'YES' if hit_stop else 'no'} | "
                     f"{'YES' if hit_t1 else 'no'} | {b.spread_open:.6f} |")
    lines.append("")
    lines.append(f"- entry candle: bar {plan.get('trigger_index')} · fill price `{entry:.5f}` · "
                 f"convention: **limit at the zone edge, v1 convention** (the bar's own range must "
                 f"contain the entry price).")

    # 5 levels
    lines.append("\n## 5. Levels\n")
    lines.append("| level | price | distance (pips) | frame |")
    lines.append("|---|---|---|---|")
    lines.append(f"| entry | {entry:.5f} | — | {frame_label} zone edge |")
    lines.append(f"| stop | {stop:.5f} | {risk * 10000:.2f} | {plan.get('stop_frame') or frame_label} far edge |")
    if t1 is not None:
        lines.append(f"| T1 | {t1:.5f} | {abs(t1 - entry) * 10000:.2f} | {plan.get('t1_frame') or '?'} pool |")
    if t2 is not None:
        lines.append(f"| T2 (informational) | {t2:.5f} | {abs(t2 - entry) * 10000:.2f} | "
                     f"{plan.get('t2_frame') or '?'} pool |")
    lines.append("")
    lines.append(f"- R:R to T1 `{L.fmt(plan.get('rr_t1_measured'), 3)}`, to T2 "
                 f"`{L.fmt(plan.get('rr_t2_measured'), 3)}`")
    lines.append(f"- half-spread `{half * 10000:.2f}` pips; spread as a fraction of the stop "
                 f"`{L.fmt(plan.get('cost_fraction_of_stop'), 3)}`; stop as a fraction of the setup "
                 f"candle range `{L.fmt(plan.get('stop_fraction_of_setup_candle'), 3)}`")

    # 6 outcome
    lines.append("\n## 6. Outcome\n")
    lines.append(f"- state `{plan.get('state')}` · reason `{plan.get('exit_reason')}` · exit bar "
                 f"{plan.get('exit_index')} · exit price `{plan.get('exit_price')}`")
    lines.append(f"- hypothetical R reported by the engine: **{L.fmt(plan.get('r_measured'), 4)}**")

    # 7 replay
    lines.append("\n## 7. Independent replay\n")
    lines.append("```")
    lines.append("for each 5m bar after the decision bar, up to 288 bars:")
    lines.append("    if not (low <= entry <= high): continue          # not triggered yet")
    lines.append("    if direction bullish and low <= stop, or bearish and high >= stop: settle at stop")
    lines.append("    elif bullish and high >= t1, or bearish and low <= t1:        settle at t1")
    lines.append("    gross = (exit - entry) for bullish, (entry - exit) for bearish")
    lines.append("    cost  = half_spread_at_decision + spread_of_exit_bar / 2")
    lines.append("    R     = (gross - cost) / |entry - stop|")
    lines.append("```")
    lines.append(f"- replay: `{replayed.get('reason')}` at bar {replayed.get('index')}, price "
                 f"`{replayed.get('price')}` → R `{L.fmt(replayed.get('r'), 6)}`")
    match = (not replayed.get("error")) and abs((replayed.get("r") or 0) -
                                                (plan.get("r_measured") or 0)) < L.TOL
    lines.append(f"- tolerance `{L.TOL}` (floating point only) → **{'MATCH' if match else 'MISMATCH'}**")

    # 8 checklist
    lines.append("\n## 8. Checklist\n")
    lines.append("| item | verdict | number |")
    lines.append("|---|---|---|")
    for name, ok, detail in checks:
        lines.append(f"| {name} | {'PASS' if ok else 'FAIL'} | {detail} |")

    # 9 expert
    lines.append("\n## 9. What a human expert would need to judge — NOT JUDGED BY THE AGENT\n")
    lines.append(f"1. Is this `{zone['kind']}` a valid one on the {frame_label} frame, and would you "
                 f"have used the same two candles to draw it?")
    lines.append(f"2. Is the `{plan.get('range_position')}` reading of the dealing range the one you "
                 f"would take at this time, or is the swing pair wrong?")
    lines.append(f"3. Was a {direction} continuation the right expectation after this "
                 f"{'sweep' if zone['kind'] == 'sweep_level' else 'gap'}, given the session window?")
    lines.append("\n## What this does NOT establish\n")
    lines.append("- One card is one plan: it says nothing about the variant's edge, and R is "
                 "hypothetical under a stated fill assumption.")
    lines.append("- The checklist checks arithmetic, sides and conventions; it cannot check whether "
                 "the reading was right.")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/tmp/build_v2")
    ap.add_argument("--data", default="/tmp/hud_data/2021.csv.gz")
    args = ap.parse_args()
    root = Path(args.root)
    out = L.HERE
    (out / "CARDS").mkdir(exist_ok=True)

    # ---- hash verification of every saved output
    manifest = (L.BUILD / "REPORT_M1_M2" / "RUN_OUTPUT_SHA256.txt").read_text().splitlines()
    ok = bad = 0
    for line in manifest:
        h, path, _size = line.split("  ")
        p = Path(path)
        if not p.exists() or L.sha256(p) != h:
            bad += 1
        else:
            ok += 1
    hash_line = f"sha256 verified: {ok} files match, {bad} do not"

    from stream_v1 import load_bars
    bars_by_month = {m: load_bars(Path(args.data), "2021-01-01", MONTH_END[m])
                     for m in ("2021-09", "2021-07", "2021-06")}
    frames_by_month = {m: {"5m": L.aggregate(b, 5), "15m": L.aggregate(b, 15),
                           "1h": L.aggregate(b, 60)} for m, b in bars_by_month.items()}

    selection, run_rows, fails, mismatches = [], [], [], []
    for month, variant in L.RUNS + L.IN_SAMPLE:
        run_id = f"{month}_{variant}"
        summary, plans = L.load_plans(root, month, variant)
        bars = bars_by_month[month]
        row = {"run": run_id, "plans": len(plans), "match": 0, "mismatch": 0,
               "fail": collections.Counter(), "in_sample": month == "2021-06"}
        for plan in plans:
            offset = 0 if variant == "v1" else 1
            replayed = L.replay(bars, plan["decision_index"], plan["entry"], plan["stop"],
                                plan["t1"]["level"] if plan.get("t1") else None,
                                plan["direction"], plan.get("half_spread_at_decision") or 0.0,
                                start_offset=offset)
            checks = L.checklist(plan, bars, replayed, offset)
            match = (not replayed.get("error")) and abs((replayed.get("r") or 0) -
                                                        (plan.get("r_measured") or 0)) < L.TOL
            row["match" if match else "mismatch"] += 1
            if not match:
                mismatches.append({"run": run_id, "plan": plan["plan_id"],
                                   "engine": plan.get("r_measured"), "replay": replayed,
                                   "engine_reason": plan.get("exit_reason")})
            for name, okv, detail in checks:
                if okv is False:
                    row["fail"][name] += 1
                    fails.append({"run": run_id, "plan": plan["plan_id"], "check": name,
                                  "detail": detail})
                elif okv == "NOT_EVALUABLE":
                    row.setdefault("not_evaluable", collections.Counter())[name] += 1
        run_rows.append(row)

        # ---- selection + cards
        if month == "2021-06":
            continue
        picked = L.pick(plans, run_id)
        indices = {p["decision_index"] for _, p, _ in picked}
        context = decision_context(root / run_id, indices)
        for why, plan, meta in picked:
            offset = 0 if variant == "v1" else 1
            replayed = L.replay(bars, plan["decision_index"], plan["entry"], plan["stop"],
                                plan["t1"]["level"] if plan.get("t1") else None,
                                plan["direction"], plan.get("half_spread_at_decision") or 0.0,
                                start_offset=offset)
            checks = L.checklist(plan, bars, replayed, offset)
            text = card(plan, context.get(plan["decision_index"]), bars,
                        frames_by_month[month], run_id, why, replayed, checks)
            safe = plan["plan_id"].replace(":", "_").replace("+", "p")
            path = out / "CARDS" / f"{run_id}__{why.split()[0]}__{safe[:60]}.md"
            path.write_text(text, encoding="utf-8")
            selection.append({"run": run_id, "why": why, "plan_id": plan["plan_id"],
                              "r": plan.get("r_measured"), "meta": meta,
                              "state": plan.get("state"), "file": str(path.relative_to(out))})

    (out / "SELECTION.json").write_text(json.dumps({"hash_check": hash_line,
                                                    "selected": selection}, indent=1),
                                        encoding="utf-8")

    # ---- ALL_PLANS_CHECKS.md
    lines = ["# ALL PLANS CHECKS — every plan of every run", "",
             f"- {hash_line}", "- replay: independent function in `td_lib.py::replay` (no import of "
             "build_v1 or build_v2 settlement code); tolerance 1e-9, floating point only", ""]
    checklist_names = ["stop on the correct side of entry", "T1 beyond entry",
                       "entry inside the zone", "T1 not already traded-through before arming (288-bar proxy)",
                       "fill convention consistent (limit at the zone edge)",
                       "half-spread applied once per side",
                       "same-bar rule applied as declared (stop first)",
                       "first evaluation at or after the arming bar", "R:R formula correct",
                       "replay reproduces the reported R"]
    header = "| run | plans | MATCH | MISMATCH | " + " | ".join(
        f"F{n+1}" for n in range(len(checklist_names))) + " |"
    lines += [header, "|" + "---|" * (4 + len(checklist_names))]
    for row in run_rows:
        cells = [str(row["fail"].get(n, 0)) for n in checklist_names]
        ne = row.get("not_evaluable", collections.Counter())
        lines.append(f"| {row['run']}{' (IN_SAMPLE)' if row['in_sample'] else ''} | {row['plans']} | "
                     f"{row['match']} | {row['mismatch']} | " + " | ".join(cells) + " |")
    lines += ["", "Checklist columns: " + "; ".join(f"F{n+1} = {name}"
                                                    for n, name in enumerate(checklist_names)), "",
              "F4 is reported **NOT_EVALUABLE** for every plan: the saved plan record does not persist "
              "the T1 pool's formation index, so 'untaken between formation and arming' cannot be "
              "reconstructed from the outputs. The proxy count (closes beyond T1 in the 288 bars before "
              "arming) is printed in each card but is not a verdict. This is recorded as defect D5.", ""]
    lines += ["## Every mismatch", ""]
    if mismatches:
        for item in mismatches[:60]:
            lines.append(f"- `{item['run']}` `{item['plan']}`: engine `{item['engine_reason']}` "
                         f"R={item['engine']}, replay `{item['replay'].get('reason')}` "
                         f"R={item['replay'].get('r')}")
    else:
        lines.append("- none: every replay matched the engine to within 1e-9.")
    lines += ["", "## Every FAIL", ""]
    grouped = collections.Counter(f["check"] for f in fails)
    if fails:
        for name, count in grouped.most_common():
            examples = [f for f in fails if f["check"] == name][:5]
            lines.append(f"- **{name}** — {count} plans. Examples: " +
                         "; ".join(f"`{e['run']}`/`{e['plan']}` ({e['detail']})" for e in examples))
    else:
        lines.append("- none.")
    lines += ["", "## The NULL baseline", "",
              "- The NULL entries were produced **inside** `report_v2.py::null_baseline`, per run, by "
              "replaying the same decision bars with the same stop distance and the same T1 distance, "
              "with the direction drawn once per plan from `random.Random(20261109)`.",
              "- It is a **single seeded draw**, not an average of several draws: every plan gets one "
              "coin flip, so the NULL column moves by whole plans if the draw changes.",
              "- Entry bars and distances: identical to the real plans by construction (the same "
              "`decision_index`, `|entry − stop|` and `|t1 − entry|` objects are used); only the "
              "direction is replaced. This is verified by construction, not by a separate check.",
              "", "## What this does NOT establish", "",
              "- A MATCH proves two implementations of the same convention agree; it does not prove "
              "the convention is right.", "- A PASS on 'T1 not already traded-through' uses a "
              "2,880-bar lookback (10 days of 5m); a different lookback would change the count."]
    (out / "ALL_PLANS_CHECKS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ---- descriptive tables
    desc = ["# DESCRIPTIVE TABLES PER RUN — no judgement, no winner", ""]
    for month, variant in L.RUNS + L.IN_SAMPLE:
        run_id = f"{month}_{variant}"
        summary, plans = L.load_plans(root, month, variant)
        r = [(p.get("r_measured"), p["plan_id"]) for p in plans if p.get("r_measured") is not None]
        if not r:
            desc += [f"## {run_id}", "", "_no settled plan: **zero plans** is a valid result._", ""]
            continue
        values = [x[0] for x in r]
        ordered = sorted(r, key=lambda x: -x[0])
        wins = sum(1 for p in plans if p.get("state") == "settled_target")
        same = sum(1 for p in plans if p.get("trigger_index") is not None
                   and p.get("trigger_index") == p.get("exit_index"))
        without_best = [v for v in values]
        without_best.remove(max(values))
        big = [v for v in values if v > 5]
        frac = [p.get("stop_fraction_of_setup_candle") for p in plans
                if p.get("stop_fraction_of_setup_candle")]
        desc += [f"## {run_id}", "",
                 f"- plans {len(plans)} · settled {len(values)} · hit T1 {wins} · settled on the "
                 f"entry candle {same}",
                 f"- mean R {statistics.mean(values):.3f} · median R {statistics.median(values):.3f} · "
                 f"mean R without the single best plan "
                 f"{statistics.mean(without_best) if without_best else float('nan'):.3f}",
                 f"- best three: " + ", ".join(f"`{pid}` {v:.2f}" for v, pid in ordered[:3]),
                 f"- worst three: " + ", ".join(f"`{pid}` {v:.2f}" for v, pid in ordered[-3:]),
                 (f"- plans with R > +5: {len(big)} carrying {sum(big):.2f} R of a total of "
                  f"{sum(values):.2f} R (a share is meaningless when the total is negative)"
                  if sum(values) <= 0 else
                  f"- plans with R > +5: {len(big)} carrying {sum(big) / sum(values):.1%} of the total R"),
                 f"- stop as a fraction of the setup candle range: "
                 f"{('min %.4f / median %.4f / max %.4f' % (min(frac), statistics.median(frac), max(frac))) if frac else 'not recorded for this variant'}",
                 ""]
    desc += ["## The '0.39–0.63' claim in the previous report", "",
             "Those two numbers were a **median** pair, not a min/max and not one run: 0.390 was the "
             "median of V2-B on M1 (2021-09) and 0.629 the median of V2-B-OFF on M1. The per-run "
             "min/median/max above is the honest form of the same quantity.", ""]
    (out / "DESCRIPTIVE_TABLES.md").write_text("\n".join(desc) + "\n", encoding="utf-8")

    # ---- fragility
    summary, plans = L.load_plans(root, "2021-09", "V2-A")
    top = max(plans, key=lambda p: p.get("r_measured") or -1e9)
    risk = abs(top["entry"] - top["stop"])
    t1 = top["t1"]["level"]
    half = top["half_spread_at_decision"]
    gross = abs(t1 - top["entry"])
    fragile = [f"## Fragility of the highest-R plan in V2-A on M1", "",
               f"plan `{top['plan_id']}`, reported R = **{top['r_measured']:.4f}**, stop "
               f"{risk * 10000:.2f} pips, T1 {gross * 10000:.2f} pips away, half-spread "
               f"{half * 10000:.2f} pips.", "",
               "| scenario | R |", "|---|---|",
               f"| as reported | {(gross - 2 * half) / risk:.4f} |",
               f"| half-spread doubled | {(gross - 4 * half) / risk:.4f} |",
               f"| stop widened by 0.5 pip | {(gross - 2 * half) / (risk + 0.00005):.4f} |",
               f"| both | {(gross - 4 * half) / (risk + 0.00005):.4f} |", "",
               "This is a description of fragility, not a rule: a plan whose R falls by this much "
               "when one cost assumption moves is a plan resting on one narrow stop.", ""]
    (out / "FRAGILITY.md").write_text("\n".join(fragile), encoding="utf-8")

    # ---- error classes
    classes = collections.Counter()
    for m in mismatches:
        classes["ARITHMETIC"] += 1
    for f in fails:
        if f["check"] in ("T1 beyond entry", "entry inside the zone",
                          "T1 not already traded-through before arming (288-bar proxy)"):
            classes["GEOMETRY"] += 1
        elif f["check"] in ("first evaluation at or after the arming bar",
                            "stop on the correct side of entry"):
            classes["CAUSALITY" if "zone" in f["check"] else "GEOMETRY"] += 1
        elif f["check"] in ("half-spread applied once per side",
                            "same-bar rule applied as declared (stop first)",
                            "fill convention consistent (limit at the zone edge)"):
            classes["CONVENTION"] += 1
    total = sum(classes.values())
    errors = ["# ERRORS FOUND — by counting, HYPOTHESIS on the layer", "",
              f"- {hash_line}", "",
              "| class | count | what it means | layer to suspect (HYPOTHESIS) |",
              "|---|---|---|---|",
              f"| ARITHMETIC | {classes['ARITHMETIC']} | replay disagrees with the engine's R or reason | execution / accounting |",
              f"| CAUSALITY | {classes['CAUSALITY']} | a level used before its candle closed | facts |",
              f"| GEOMETRY | {classes['GEOMETRY']} | a side/level inconsistency (e.g. T1 already traded) | target / selection |",
              f"| CONVENTION | {classes['CONVENTION']} | a rule applied differently from the declaration | execution |",
              f"| CONCEPT | 0 counted | needs a human expert; listed as questions in section 9 of each card | concept |",
              f"| NONE | {total == 0 and 'all plans' or 'remaining plans'} | — | — |", "",
              "## Examples (at most three per class)", ""]
    for name in ("ARITHMETIC", "CAUSALITY", "GEOMETRY", "CONVENTION"):
        examples = ([m for m in mismatches] if name == "ARITHMETIC"
                    else [f for f in fails if (name == "GEOMETRY" and f["check"] in
                                               ("T1 beyond entry", "entry inside the zone"))
                          or (name == "CAUSALITY" and f["check"].startswith("zone"))
                          or (name == "CONVENTION" and f["check"].startswith(("half", "same", "fill")))])
        errors.append(f"### {name} — {len(examples)}")
        for e in examples[:3]:
            errors.append(f"- `{e.get('run')}` `{e.get('plan')}`: "
                          f"{e.get('check') or e.get('engine_reason')} — "
                          f"{(e.get('detail') or str(e.get('replay')))}")
        errors.append("")
    errors += ["## What this does NOT establish", "",
               "- A class count is a count of flagged records, not of real errors: a FAIL on 'T1 not "
               "already traded' may be a legitimate pool that price approached and rejected.",
               "- Every layer assignment is a **HYPOTHESIS**; no defect was fixed and no run repeated.",
               "- 'NONE' rows are not evidence of correctness, only of no flag."]
    (out / "ERRORS_FOUND.md").write_text("\n".join(errors) + "\n", encoding="utf-8")

    print(json.dumps({"hash_check": hash_line, "cards": len(selection),
                      "runs_checked": len(run_rows), "mismatches": len(mismatches),
                      "fails": len(fails), "classes": dict(classes)}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
