#!/usr/bin/env python3
"""DEV-MONTH wrapper v0 — 2021 history, March-2021 decisions only.

WHY THIS FILE EXISTS (Phase 3e of the task block)
-------------------------------------------------
The existing runner ``docs/research/huddleston_study/run_forex_intraday_v1.py``
produces a decision at EVERY task boundary inside ``--from .. --to``.  The owner
authorisation for this run permits history bars from 2021-01-01 but decisions
and plans only inside 2021-03-01 .. 2021-03-31.  The runner has no flag that
separates "history window" from "decision window", and its decision loop lives
inside ``run_phase`` — editing it would modify an existing file, which this task
forbids.  This wrapper therefore drives the SAME loop with the SAME objects and
copies the runner's two gate functions verbatim, adding exactly one thing: a
decision window gate.

NOTHING IS RE-TUNED HERE.  Every constant is imported from the runner or from the
engine modules; none is redefined.  The only new parameter is the decision window,
which comes from the owner authorisation, not from a measurement.

Copied verbatim from ``run_forex_intraday_v1.py`` (recorded so a later reader can
diff): ``gate_v1`` and ``gate_b0`` (inside ``run_phase``), and the loop body's
ordering (episode extraction -> model fit -> decide -> gate -> observe/create).
If the runner changes, this copy must be re-checked; it is a copy, not a call.

Run:
  python3 run_dev_month_v0.py --bidask-dir DIR --history-from 2021-01-01 \
      --decide-from 2021-03-01 --decide-to 2021-04-01 --to 2021-04-01 \
      --out-dir DIR [--gate v1|b0] [--fill-mode next_open|bar_close]
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RUNNER_PATH = HERE.parents[0] / "huddleston_study" / "run_forex_intraday_v1.py"
SRC = HERE.parents[2] / "src"


def _load_runner():
    spec = importlib.util.spec_from_file_location("fx_intraday_v1_runner", RUNNER_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["fx_intraday_v1_runner"] = mod
    spec.loader.exec_module(mod)
    return mod


RUNNER = _load_runner()

from trading_system.research.contextual_selection.csm import SharedInformationAxis  # noqa: E402,F401
from trading_system.research.contextual_selection.decision_layer import (  # noqa: E402
    ContextEventModel,
    EpisodeExtractor,
    decide,
)
from trading_system.research.contextual_selection.monitoring import (  # noqa: E402
    MonitoringLoop,
    ReplayObservationStream,
)
from trading_system.research.contextual_selection.study_links import (  # noqa: E402
    StudyReasoningLayer,
)
from trading_system.research.contextual_selection.trade_plan import (  # noqa: E402
    build_components,
    create_plan,
    evaluate_plans,
    observe_plan,
    resolve_world,
    source_agreement,
)


def _intended_direction(pid, ctx_dir):
    return RUNNER._intended_direction(pid, ctx_dir)


def gate_v1(dec, study) -> tuple:
    """Copied verbatim from run_forex_intraday_v1.run_phase.gate_v1."""
    if dec.primary_is_baseline or dec.state in ("NO_EDGE", "UNRESOLVED"):
        return False, ("decision has no strict evidence-supported "
                       "preference: " + dec.state)
    rt = study.readings.tasks.get("RT-REF-REVIEW")
    ctx_dir = str(dec.context.get("direction"))
    pid = getattr(dec, "primary_interpretation_id", None)
    intended = _intended_direction(pid, ctx_dir)
    if intended is None:
        return False, ("decision has no determinable intended direction: "
                       "pid=" + str(pid) + " ctx_dir=" + str(ctx_dir))
    for tid2, t2 in study.readings.tasks.items():
        c2 = t2.conclusion or {}
        pref = c2.get("preferred")
        if c2.get("status") == "EVIDENCE_PREFERRED" and pref:
            reg = study.readings.regions.get(pref)
            if reg is not None and intended in ("up", "down"):
                oppose = ((reg.direction == "downward" and intended == "up")
                          or (reg.direction == "upward" and intended == "down"))
                if oppose:
                    return False, ("connected readings hold EVIDENCE_PREFERRED "
                                   f"FVG {pref} ({reg.direction}) opposing the "
                                   "intended direction (" + intended
                                   + " from pid=" + str(pid) + " ctx=" + ctx_dir
                                   + ") — recorded contradicting evidence; "
                                   "the attempt is held while this holds")
    if rt is not None and rt.conclusion:
        st = rt.conclusion.get("status")
        if st == "UNRESOLVED_NO_EDGE":
            return True, ("connected readings UNRESOLVED: plan attempt "
                          "allowed as PROVISIONAL baseline only if the "
                          "plan-layer definitions themselves resolve")
    return True, "connected readings do not contradict"


def gate_b0(dec, study) -> tuple:
    """Copied verbatim from run_forex_intraday_v1.run_phase.gate_b0."""
    if dec.primary_is_baseline or dec.state in ("NO_EDGE", "UNRESOLVED"):
        return False, ("decision has no strict evidence-supported "
                       "preference: " + dec.state)
    return True, ("B0 baseline: connected readings NOT consulted")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bidask-dir", required=True)
    ap.add_argument("--history-from", required=True,
                    help="first bar loaded (causal history / warm-up)")
    ap.add_argument("--decide-from", required=True,
                    help="first decision instant produced")
    ap.add_argument("--decide-to", required=True,
                    help="exclusive end of the decision window")
    ap.add_argument("--to", required=True, help="exclusive end of loaded bars")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--model", default=None)
    ap.add_argument("--gate", choices=["v1", "b0"], default="v1")
    ap.add_argument("--fill-mode", choices=["next_open", "bar_close"],
                    default="next_open")
    a = vars(ap.parse_args(argv))

    out_dir = Path(a["out_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    if not a["model"]:
        a["model"] = str(out_dir / "dev_model.json")

    t0, t1 = a["history_from"], a["to"]
    d0 = pd.Timestamp(a["decide_from"], tz="UTC")
    d1 = pd.Timestamp(a["decide_to"], tz="UTC")

    bidask = RUNNER.load_bidask(Path(a["bidask_dir"]), t0, t1)
    rows = RUNNER.mid_rows(bidask)
    print(f"== loaded {t0} -> {t1}: open-market 5m rows {len(rows)}; "
          f"decisions {a['decide_from']} -> {a['decide_to']}", flush=True)

    stream = ReplayObservationStream(
        rows.copy(), timeline_id="EURUSD_1m_fx_intraday_v1",
        dataset_identity="dukascopy-eurusd-5m-bidask@56d5f04")
    study = StudyReasoningLayer(run_id=RUNNER.RUN_ID, k=RUNNER.K,
                                task_scale=RUNNER.TASK_SCALE,
                                instrument="EURUSD")
    loop = MonitoringLoop(
        stream=stream, frames_builder=RUNNER.frames_builder,
        engine_factory=RUNNER.engine_factory(), task_scale=RUNNER.TASK_SCALE,
        study_layer=study, readings_scale=RUNNER.READINGS_SCALE)
    model = ContextEventModel()
    extractor = EpisodeExtractor(frames=loop._grid_frames, k=RUNNER.K,
                                 task_scale=RUNNER.TASK_SCALE,
                                 horizon_bars=RUNNER.HORIZON_BARS,
                                 axis=None, instrument="EURUSD")
    gate = {"v1": gate_v1, "b0": gate_b0}[a["gate"]]

    cases, plans, episodes, pending_eps = [], [], [], []
    active_plan = None
    plan_seq = 0
    boundary_seq = 0
    decision_seq = 0
    stats = {"boundaries_total": 0, "boundaries_before_window": 0,
             "boundaries_after_window": 0, "decisions": 0, "strict_pref": 0,
             "gate_pass": 0, "plans_created": 0, "no_plan": 0}
    t_start = time.time()

    while not loop.stream.exhausted:
        r = loop.step_completed_bar()
        if r.trigger != "task-boundary" or loop.last_record is None:
            continue
        rec = loop.last_record
        boundary_seq += 1
        stats["boundaries_total"] += 1
        ts = pd.Timestamp(rec.as_of_time)

        # warm-up: episodes are extracted and the model fitted (internal
        # state, causal: only episodes whose label window closed before ts)
        ep = extractor.extract(rec, run_id="dev", seq=boundary_seq)
        episodes.append(ep)
        pending_eps.append(ep)
        ready = [e for e in pending_eps
                 if e.window_end_time is not None
                 and pd.Timestamp(e.window_end_time) < ts]
        if ready:
            model.fit(ready)
            for e in ready:
                pending_eps.remove(e)

        if ts < d0:
            stats["boundaries_before_window"] += 1
            continue
        if ts >= d1:
            stats["boundaries_after_window"] += 1
            continue

        decision_seq += 1
        stats["decisions"] += 1
        if decision_seq % 100 == 0:
            print(f"  … {decision_seq} decisions ({ts}) cases={len(cases)} "
                  f"t={time.time() - t_start:.0f}s", flush=True)

        dec = decide(record=rec, model=model, decision_seq=decision_seq)
        strict = not (dec.primary_is_baseline
                      or dec.state in ("NO_EDGE", "UNRESOLVED"))
        stats["strict_pref"] += int(strict)
        ok, gate_reason = gate(dec, study)
        stats["gate_pass"] += int(ok and strict)

        def _world_now():
            fr = loop._prefix_frames()
            return resolve_world(frames=fr, record=rec, k=RUNNER.K,
                                 task_scale=RUNNER.TASK_SCALE,
                                 axis=loop.engine.axis)

        if active_plan is not None and active_plan.active:
            observe_plan(plan=active_plan, record=rec, world=_world_now(),
                         frames=loop._prefix_frames(),
                         run_context="historical-replay",
                         decision_id=dec.decision_id,
                         task_scale=RUNNER.TASK_SCALE)
            if not active_plan.active:
                oc = RUNNER.outcome_for(active_plan, bidask,
                                        active_plan.current.direction,
                                        fill_mode=a["fill_mode"])
                cases.append({"kind": "plan",
                              "plan": active_plan.to_record(),
                              "outcome": oc,
                              "decision": dec.to_record()
                              if hasattr(dec, "to_record") else None,
                              "decision_state": dec.state,
                              "gate_reason": active_plan.gate_reason})
                plans.append(active_plan)
                active_plan = None
        elif ok and strict and active_plan is None:
            plan_seq += 1
            plan, reason = create_plan(
                record=rec, decision=dec, world=_world_now(),
                run_id=RUNNER.RUN_ID, seq=plan_seq,
                frames=loop._prefix_frames(),
                run_context="historical-replay",
                task_scale=RUNNER.TASK_SCALE, instrument="EURUSD")
            if plan is None:
                stats["no_plan"] += 1
                cases.append({"kind": "no-plan", "as_of": str(rec.as_of_time),
                              "decision_state": dec.state,
                              "gate_reason": gate_reason,
                              "missing_evidence": reason.get("missing_evidence"),
                              "decision": dec.to_record()
                              if hasattr(dec, "to_record") else None})
            else:
                plan.gate_reason = gate_reason
                stats["plans_created"] += 1
                active_plan = plan
                cases.append({"kind": "plan-opened",
                              "as_of": str(rec.as_of_time),
                              "plan_id": plan.plan_id,
                              "scenario": plan.current.scenario,
                              "direction": plan.current.direction,
                              "gate_reason": gate_reason,
                              "decision": dec.to_record()
                              if hasattr(dec, "to_record") else None,
                              "components_origins":
                                  {k: {"definition_origin":
                                       c.definition_origin,
                                       "claim_class": c.claim_class}
                                   for k, c in
                                   build_components(
                                       scenario=plan.current.scenario).items()}})
        elif not ok or not strict:
            stats["no_plan"] += 1
            cases.append({"kind": "no-plan", "as_of": str(rec.as_of_time),
                          "decision_state": dec.state,
                          "gate_reason": gate_reason,
                          "decision": dec.to_record()
                          if hasattr(dec, "to_record") else None})

    if active_plan is not None:
        oc = RUNNER.outcome_for(active_plan, bidask,
                                active_plan.current.direction,
                                fill_mode=a["fill_mode"])
        cases.append({"kind": "plan", "plan": active_plan.to_record(),
                      "outcome": oc,
                      "decision_state": "open-at-data-end",
                      "gate_reason": getattr(active_plan, "gate_reason", "")})
        plans.append(active_plan)

    dev_end = pd.Timestamp(t1, tz="UTC")
    usable = [e for e in pending_eps
              if e.label is not None and e.exclusion_reason is None
              and e.window_end_time is not None
              and pd.Timestamp(e.window_end_time) <= dev_end]
    model.fit(usable)
    Path(a["model"]).write_text(json.dumps(RUNNER.model_state(model), indent=1))

    ev = evaluate_plans(plans)
    summary = {
        "phase": "dev-month-v0", "history_window": [t0, t1],
        "decision_window": [a["decide_from"], a["decide_to"]],
        "gate": a["gate"], "fill_mode": a["fill_mode"],
        "gate_stats": stats,
        "plan_evaluation": ev,
        "cases_total": len(cases),
        "cases_by_kind": {k: sum(1 for c in cases if c["kind"] == k)
                          for k in sorted({c["kind"] for c in cases})},
        "outcomes": {k: sum(1 for c in cases
                            if c.get("outcome", {}).get("outcome") == k)
                     for k in sorted({c.get("outcome", {}).get("outcome")
                                      for c in cases if c.get("outcome")})},
        "episodes_total": len(episodes),
        "episodes_fitted": model.n_episodes,
        "trained_through": str(model.trained_through),
        "source_agreement": source_agreement(
            {k: c.to_record() for k, c in
             build_components(scenario="continuation").items()}),
        "warmup_note": ("episodes extracted and model fitted from the first "
                        "boundary (causal: label windows close before t); "
                        "decide()/create_plan() called only inside the "
                        "decision window"),
        "limitations": [
            "selection_quality = NOT_ESTABLISHED",
            "research/paper record only — no live orders",
            "commission NOT provided by this dataset (never invented)",
            "slippage not modelled",
            "same-bar level-touch ambiguity preserved as AMBIGUOUS",
        ],
    }
    (out_dir / f"cases_{a['gate']}.jsonl").write_text(
        "\n".join(json.dumps(c, default=str) for c in cases))
    (out_dir / f"summary_{a['gate']}.json").write_text(
        json.dumps(summary, indent=1, default=str))
    print(f"== done in {time.time() - t_start:.1f}s; cases={len(cases)} "
          f"stats={stats} ==", flush=True)
    print(json.dumps(summary["outcomes"], indent=1), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
