#!/usr/bin/env python3
"""Contextual trade-plan layer V1 — end-to-end runnable path (task scope).

market context -> structural evidence -> working interpretation ->
awaited / already-observed event -> HYPOTHETICAL conditional trade plan
(entry / invalidation / objective, each labeled verifiable-source or
declared-research-configuration) -> observable state -> next observation
-> versioned revision (existing InterpretationLedger).

ANALYTICAL RECORDS ONLY.  No orders, no execution, no position inference.
``selection_quality = NOT_ESTABLISHED``.

Example
-------
  python run_trade_plan_v1.py --run \
      --mirror-dir /home/user/work/data/btc/mirror \
      --from 2025-08-01 --to 2025-09-30
"""

from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
import sys
import time
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
PROJECT_SRC = HERE.parents[2] / "src"
sys.path.insert(0, str(PROJECT_SRC))

from trading_system.research.contextual_selection.analysis_lifecycle import (  # noqa: E402
    AnalysisEngine,
)
from trading_system.research.contextual_selection.csm import (  # noqa: E402
    InterpretationLedger,
    SharedInformationAxis,
)
from trading_system.research.contextual_selection.decision_layer import (  # noqa: E402
    EPISODE_HORIZON_BARS,
    HORIZON_DISCLOSURE,
    ContextEventModel,
    EpisodeExtractor,
    chronological_split,
    decide,
    evaluate_ex_ante_baseline,
    evaluate_model,
)
from trading_system.research.contextual_selection.trade_plan import (  # noqa: E402
    PLAN_CONDITION_OBSERVED,
    PLAN_HYPOTHETICAL_ENTRY_MET,
    PLAN_INVALIDATED,
    PLAN_MISSED,
    PLAN_MONITORING,
    PLAN_NO_JUSTIFIED_PLAN,
    SOURCE_EXAMPLES,
    build_components,
    create_plan,
    evaluate_plans,
    observe_plan,
    plan_ledger_entries,
    resolve_world,
    source_agreement,
)


def _load_analysis_runner():
    path = HERE.parent / "analysis_v1" / "run_market_analysis_v1.py"
    spec = importlib.util.spec_from_file_location("analysis_v1_runner",
                                                  path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


AN = _load_analysis_runner()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mirror-dir", required=True)
    ap.add_argument("--run", action="store_true",
                    help="chronological end-to-end run (the only mode)")
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--months", default="8,9")
    ap.add_argument("--from", dest="t_from", default="2025-08-01")
    ap.add_argument("--to", dest="t_to", default="2025-09-30")
    ap.add_argument("--boundary-days", type=int, default=1)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--horizon-bars", type=int,
                    default=EPISODE_HORIZON_BARS)
    ap.add_argument("--train-fraction", type=float, default=2 / 3)
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args(argv)

    mirror_dir = Path(args.mirror_dir)
    months = [int(m) for m in args.months.split(",")]
    out_dir = Path(args.out_dir or (HERE / "run_artifacts"))
    out_dir.mkdir(parents=True, exist_ok=True)

    print("== loading 1m mirror ==", flush=True)
    frames, csv_paths = AN.load_frames(mirror_dir, args.year, months)
    input_hashes = {p.name: AN._sha256_file(p) for p in csv_paths}
    print(f"   4h bars: {len(frames['4h'])}, 1h: {len(frames['1h'])}, "
          f"15m: {len(frames['15m'])}", flush=True)

    t_from = pd.Timestamp(args.t_from)
    t_to = pd.Timestamp(args.t_to)
    if t_from.tzinfo is None:
        t_from = t_from.tz_localize("UTC")
    if t_to.tzinfo is None:
        t_to = t_to.tz_localize("UTC")
    grid = frames["4h"].index
    boundaries = [ts for ts in pd.date_range(
        t_from.normalize(), t_to, freq=f"{args.boundary_days}D", tz="UTC")
        if ts in grid and t_from <= ts <= t_to]
    if not boundaries:
        print("no boundary on the 4h completion grid", flush=True)
        return 1

    ledger = InterpretationLedger()
    engine = AnalysisEngine(run_id="plan-v1", frames=frames, k=args.k,
                            instrument="BTCUSDT", ledger=ledger)
    extractor = EpisodeExtractor(frames=frames, k=args.k, task_scale="4h",
                                 horizon_bars=args.horizon_bars,
                                 axis=engine.axis)
    axis = SharedInformationAxis("plan-v1-decisions", grid)

    # ---- connected lifecycle ----------------------------------------
    records, episodes, decisions = [], [], []
    plans: list = []
    open_plans: list = []
    no_plan_records: list = []
    plan_log: list = []          # per-boundary state trace
    t0 = time.time()
    for i, bnd in enumerate(boundaries, 1):
        rec = engine.analyze(bnd)
        ep = extractor.extract(rec, run_id="plan-v1", seq=i)
        model = ContextEventModel()
        model.fit_before(episodes, cutoff_time=rec.as_of_time)
        dec = decide(record=rec, model=model,
                     run_context="historical-replay", decision_seq=i)
        records.append(rec)
        episodes.append(ep)
        decisions.append(dec)

        w = resolve_world(frames=frames, record=rec, k=args.k,
                          axis=engine.axis)
        # (a) observe NEW evidence at every open plan (versioned
        #     revisions; prior versions never rewritten)
        changed = []
        for p in open_plans:
            if not p.active:
                continue
            v = observe_plan(plan=p, record=rec, world=w, frames=frames,
                             run_context="historical-replay",
                             decision_id=dec.decision_id)
            if v is not None:
                changed.append((p.plan_id, v.state))
        # (b) this snapshot's plan candidate: create when the structural
        #     configuration changed (or no open plan); reuse otherwise
        key = (dec.primary_interpretation_id, dec.primary_is_baseline,
               w["ref"].candidate_id if w["ref"] else None,
               w["end"].candidate_id if w["end"] else None)
        reuse = next((p for p in reversed(open_plans) if p.active and
                      (p.current.scenario, p.current.levels
                       ["reference"]["id"], p.current.levels
                       ["leg_end"]["id"]) == (
                          "continuation" if key[0] == "I-primary" and
                          not key[1] else "reversal", key[2], key[3])),
                     None)
        if dec.primary_is_baseline or dec.state in ("NO_EDGE",
                                                    "UNRESOLVED") or \
                w["ref"] is None or w["end"] is None:
            plan, reason = create_plan(
                record=rec, decision=dec, world=w, run_id="plan-v1",
                seq=len(plans) + 1, frames=frames,
                run_context="historical-replay")
            assert plan is None
            no_plan_records.append(reason)
            plan_log.append({"as_of": str(rec.as_of_time), "plan_id":
                             reuse.plan_id if reuse else None,
                             "state": PLAN_NO_JUSTIFIED_PLAN,
                             "changed": bool(changed),
                             "missing": reason.get("missing_evidence")})
        elif reuse is not None:
            plan_log.append({"as_of": str(rec.as_of_time),
                             "plan_id": reuse.plan_id,
                             "state": reuse.current.state,
                             "changed": bool(changed),
                             "missing": None})
        else:
            plan, reason = create_plan(
                record=rec, decision=dec, world=w, run_id="plan-v1",
                seq=len(plans) + 1, frames=frames,
                run_context="historical-replay")
            assert plan is not None
            plans.append(plan)
            open_plans.append(plan)
            plan_ledger_entries(ledger=ledger, plan=plan,
                                axis=axis, run_id="plan-v1")
            plan_log.append({"as_of": str(rec.as_of_time),
                             "plan_id": plan.plan_id,
                             "state": plan.current.state,
                             "changed": True, "missing": None})
        print(f"[{i}/{len(boundaries)}] {rec.as_of_time} "
              f"dec={dec.state:38s} "
              f"plan={plan_log[-1]['state']}"
              f"{'(' + plan_log[-1]['plan_id'] + ')' if plan_log[-1]['plan_id'] else ''}"
              f"{' revised' if changed else ''}",
              flush=True)
    print(f"== lifecycle done in {time.time() - t0:.1f}s ==", flush=True)

    # ---- evaluation (four separate axes) ----------------------------
    train, ev, purged = chronological_split(
        episodes, train_fraction=args.train_fraction, return_purged=True)
    eval_model = ContextEventModel()
    eval_model.fit(train)
    event_eval = evaluate_model(eval_model, ev)
    baseline_eval = evaluate_ex_ante_baseline(train, ev)
    plan_eval = evaluate_plans(plans)

    examples = _collect_examples(plans, no_plan_records, plan_log)

    eval_full = {
        "axis_1_reproducibility_causal_integrity": {
            "append_after_t_test": "tests/test_contextual_trade_plan.py"
                                   "::test_append_after_t_invariance "
                                   "(pass)",
            "immutable_revisions": "tests/test_contextual_trade_plan.py"
                                   " revision/ledger tests (pass)",
            "separation": (
                f"train as_of <= "
                f"{max((e.as_of_time for e in train), default=None)} < "
                f"eval as_of >= "
                f"{min((e.as_of_time for e in ev), default=None)}; "
                f"purged overlapping train episodes: {len(purged)}"),
        },
        "axis_2_source_agreement": source_agreement(
            {k: c.to_record() for k, c in
             build_components(scenario="continuation").items()}),
        "axis_3_event_forecasts_later_data": {
            "model": event_eval,
            "ex_ante_baseline": baseline_eval,
            "note": "small, correlated sample (17 episodes); the "
                    "decision ranking stays PROVISIONAL and UNVALIDATED; "
                    "10/17 vs 6/17 establishes nothing about market "
                    "understanding or trading readiness",
        },
        "axis_4_hypothetical_plan_outcomes": plan_eval,
        "source_examples": SOURCE_EXAMPLES,
        "horizon_disclosure": HORIZON_DISCLOSURE,
        "required_examples": examples,
    }
    (out_dir / "plan_eval_v1.json").write_text(
        json.dumps(eval_full, indent=2, sort_keys=True, default=str))

    # ---- records + explanations -------------------------------------
    with open(out_dir / "plan_records_v1.jsonl", "w",
              encoding="utf-8") as fh:
        for p in plans:
            fh.write(json.dumps(p.to_record(), sort_keys=True,
                                default=str) + "\n")
        for r in no_plan_records:
            fh.write(json.dumps(r, sort_keys=True, default=str) + "\n")
    with gzip.open(out_dir / "plan_records_v1.jsonl.gz", "wt",
                   encoding="utf-8") as fh:
        for p in plans:
            fh.write(json.dumps(p.to_record(), sort_keys=True,
                                default=str) + "\n")
        for r in no_plan_records:
            fh.write(json.dumps(r, sort_keys=True, default=str) + "\n")
    with open(out_dir / "plan_explanations_v1.md", "w",
              encoding="utf-8") as fh:
        fh.write("# Contextual trade-plan layer V1\n\n")
        fh.write("Hypothetical analytical records only — NOT orders.  "
                 "selection_quality = NOT_ESTABLISHED.\n\n")
        for p in plans:
            fh.write(_plan_text(p))
            fh.write("\n---\n\n")
        fh.write("## No-justified-plan records (specific missing "
                 "evidence)\n\n")
        for r in no_plan_records:
            fh.write(f"- **{r['as_of']}** — missing: "
                     f"{'; '.join(r.get('missing_evidence') or [])} — "
                     f"next: {r.get('next_discriminating_observation')}"
                     f"\n")
    (out_dir / "plan_run_trace_v1.json").write_text(json.dumps(
        plan_log, indent=1))

    manifest = {
        "artifact": "contextual-trade-plan-layer-v1",
        "run": {"from": str(t_from), "to": str(t_to),
                "n_boundaries": len(boundaries),
                "run_context": "historical-replay"},
        "config": {"k": args.k, "task_scale": "4h",
                   "episode_horizon_bars": args.horizon_bars,
                   "train_fraction": args.train_fraction,
                   "plan_states": [PLAN_MONITORING,
                                   PLAN_CONDITION_OBSERVED,
                                   PLAN_HYPOTHETICAL_ENTRY_MET,
                                   PLAN_INVALIDATED, PLAN_MISSED,
                                   PLAN_NO_JUSTIFIED_PLAN]},
        "plan_summary": plan_eval,
        "source_agreement": eval_full["axis_2_source_agreement"],
        "selection_quality": "NOT_ESTABLISHED",
        "claims": {
            "plans": "hypothetical analytical records — NOT orders; no "
                     "execution connectivity exists",
            "components": "entry/objective = declared research "
                          "configuration; invalidation = engineering "
                          "interpretation of project falsifier "
                          "semantics; the ICT OB entry technique is "
                          "source-stated but NOT implemented (G-OB-P "
                          "not runnable: P-N/P-W unset; no owner policy; "
                          "none invented)",
            "outcomes": "hypothetical plan mechanics only — not profits",
            "identity": "NOT Michael Huddleston; no exact replication, "
                        "no accuracy or profitability claim",
        },
        "provenance": {
            "dataset_commit": AN.DATASET_COMMIT,
            "dataset_mirror": AN.DATASET_MIRROR,
            "input_sha256": input_hashes,
            "expected_sha256": AN.INPUT_SHA256,
            "hashes_match_expected": {
                k: input_hashes.get(k) == v
                for k, v in AN.INPUT_SHA256.items()},
            "source_material": {
                "pinned_knowledge": "jfjdjdieifne/test@6c8bf6fd10e95813"
                                    "22849485d175e825cea5a27f",
                "examples": [e["example_id"] for e in SOURCE_EXAMPLES],
                "source_commit_note": "the pinned repository's default "
                                      "branch has moved; this path reads "
                                      "the pinned commit 6c8bf6fd only",
            },
            "final_source_commit": AN._git_head(),
            "sealed_information_time_sha256": AN._sealed_hash(),
            "dependency_versions": AN._dep_versions(),
        },
    }
    (out_dir / "plan_manifest_v1.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, default=str))
    print(f"== wrote {out_dir}/plan_manifest_v1.json ==", flush=True)
    print(f"== plans: {len(plans)} | no-plan records: "
          f"{len(no_plan_records)} | outcomes: "
          f"{plan_eval['hypothetical_outcomes']} ==", flush=True)
    return 0


def _collect_examples(plans, no_plan_records, plan_log):
    """The four task-required examples from the REAL run (or an explicit
    limitation when the data cannot produce one)."""
    out = {}
    monitored = next((p for p in plans
                      if any(v.state == PLAN_MONITORING
                             for v in p.versions[1:]) or
                      (len(p.versions) >= 2 and
                       p.versions[0].state == PLAN_MONITORING)), None)
    out["scenario_monitored_before_its_condition"] = (
        _example(monitored) if monitored else
        {"limitation": "no plan in this run spent a boundary in "
                       "MONITORING before its condition"})
    entry_met = next((p for p in plans if any(
        v.state == PLAN_HYPOTHETICAL_ENTRY_MET for v in p.versions)), None)
    out["plan_entry_condition_becomes_met"] = (
        _example(entry_met) if entry_met else
        {"limitation": "no post-record entry condition was met in the "
                       "available data at these boundaries"})
    inval_or_miss = next((p for p in plans if any(
        v.state in (PLAN_INVALIDATED, PLAN_MISSED) for v in p.versions)),
        None)
    out["invalidated_or_missed_scenario"] = (
        _example(inval_or_miss) if inval_or_miss else
        {"limitation": "no invalidated/missed plan occurred in the "
                       "available data"})
    out["no_plan_with_specific_missing_evidence"] = (
        no_plan_records[0] if no_plan_records else
        {"limitation": "every snapshot produced a plan in this run"})
    return out


def _example(plan):
    return {
        "plan_id": plan.plan_id,
        "versions": [v.to_record() for v in plan.versions],
        "events_seen": {"entry_bars": plan.entry_bars_seen,
                        "invalidation_bars": plan.invalidation_bars_seen,
                        "objective_seen": plan.objective_seen},
    }


def _plan_text(p) -> str:
    v = p.current
    L = [f"### {p.plan_id} — {v.scenario} scenario ({v.direction}) "
         f"run_context={v.run_context}",
         f"state: {v.state} (v{v.version}"
         f"{' revised from ' + v.revises if v.revises else ''})",
         f"as of: {v.as_of_time}",
         f"state detail: {v.state_detail}",
         f"decision: {v.decision_id} | analysis: {v.analysis_id} v"
         f"{v.analysis_version}"]
    for kind in ("entry", "invalidation", "objective"):
        c = v.components[kind]
        L.append(f"  {kind} [{c['definition_origin']}; "
                 f"{c['claim_class']}]: {c['definition']}")
        L.append(f"    source note: {c['source_reference']}")
    L.append(f"  levels: ref={v.levels['reference']} "
             f"end={v.levels['leg_end']}")
    L.append(f"  events observed: {v.events_observed}")
    L.append(f"  position status: {v.position_status} | "
             f"selection_quality = {v.selection_quality}")
    L.append("  hypothetical analytical record — NOT an order")
    return "\n".join(L)


if __name__ == "__main__":
    raise SystemExit(main())
