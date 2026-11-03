#!/usr/bin/env python3
"""Decision-trace runner — does the connected-reading engine actually
COMPARE competing references/FVGs in context? (deliverable task)

Produces, on REAL BTCUSDT 1m mirror data, at a DISCLOSED pause:
  1. a compact human-readable decision trace (context, declared task,
     materially relevant competing candidates with supporting /
     counterevidence / unknowns, criteria + why, conclusion or explicit
     non-resolution, watch-next) with counts BEFORE and AFTER display
     filtering and explicit resource limits — nothing silently removed;
  2. causal stepping showing what happens to THAT SAME decision, with
     old and new ledger records (honest "no change" when nothing
     changes; a conditional watch is not a prediction);
  3. a cadence trace distinguishing a bar's completion time (data) from
     the engine's processing/recording time (wall clock at the task-
     scale boundary).

Nothing here is a trade or recommendation. selection_quality =
NOT_ESTABLISHED.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
PROJECT_SRC = HERE.parents[1] / "project" / "trading_project" / "src"
if not PROJECT_SRC.exists():
    PROJECT_SRC = HERE.parents[2] / "src"
sys.path.insert(0, str(PROJECT_SRC))

from trading_system.research.contextual_selection.monitoring import (  # noqa: E402
    MonitoringLoop,
    ReplayObservationStream,
)
from trading_system.research.contextual_selection.study_links import (  # noqa: E402
    StudyReasoningLayer,
)

sys.path.insert(0, str(HERE))
from run_connected_reading_v1 import (  # noqa: E402
    engine_factory,
    frames_builder,
    load_rows,
)

TASK_LEDGER = {"RT-REF-REVIEW": "T-STUDY-READING"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _pick_task(study, wanted: str | None):
    tasks = study.readings.tasks
    if wanted:
        if wanted in tasks:
            return tasks[wanted]
        hits = [t for k, t in tasks.items() if wanted in k]
        if len(hits) == 1:
            return hits[0]
        raise KeyError(f"task {wanted!r} not found; have {list(tasks)}")
    return max(tasks.values(),
               key=lambda t: (len(t.candidates), len(t.versions)),
               default=None)


def _print_decision_trace(study, tag: str, task_id: str | None) -> None:
    print(f"\n{'=' * 72}\n== DECISION TRACE at {tag} "
          f"(pause disclosed; window chosen for the demo)\n{'=' * 72}",
          flush=True)
    hf = study.hf_context
    print(f"[1] HIGHER-FRAME CONTEXT: trend={hf.get('trend')}", flush=True)
    print(f"    available/established at (data time): "
          f"{hf.get('established_at')}", flush=True)
    print(f"    evidence: {hf.get('evidence')}", flush=True)
    print(f"    source/engineering: the trend is the engine's derived "
          f"direction (ENGINEERING), from completed structure only",
          flush=True)

    task = _pick_task(study, task_id)
    if task is None:
        print("[2] no declared reading task exists at this pause",
              flush=True)
        return
    print(f"\n[2] DECLARED TASK {task.task_id}: {task.question}",
          flush=True)
    rule = task.declared.get("evaluation_rule", {})
    print(f"    evaluation rule: {rule.get('rule')}", flush=True)
    print(f"    rule class: {rule.get('kind')} — {rule.get('source_status')}",
          flush=True)
    print(f"    conflict handling: {rule.get('conflict_handling')}",
          flush=True)
    print("    criteria applied (and why):", flush=True)
    for c in task.declared.get("criteria", []):
        print(f"      - {c['name']} [{c['class']}]: {c['meaning']}",
              flush=True)

    comp = task.comparison or {}
    print(f"\n[3] CANDIDATE COMPARISON (this is a comparison, not a "
          f"collection)", flush=True)
    print(f"    candidates before filtering: "
          f"{comp.get('candidates_before_filtering', len(task.candidates))}",
          flush=True)
    print(f"    by support count (criteria met): "
          f"{comp.get('by_support_count')}", flush=True)
    print(f"    relevance rule (display filter): "
          f"{comp.get('materially_relevant_rule')}", flush=True)
    print(f"    candidates after filtering (shown in detail): "
          f"{comp.get('candidates_after_filtering')}", flush=True)
    print(f"    removed from the record: "
          f"{comp.get('removed_from_record', 0)} (never silently "
          f"removed; all remain in task.candidates)", flush=True)
    print(f"    resource limits: {comp.get('resource_limit')}",
          flush=True)

    def support_n(c):
        return sum(bool(v) for v in c.get("criteria", {}).values())

    # display batching (DISPLAY rule, disclosed — not an analytical
    # threshold; nothing is removed from the record): candidates near
    # satisfying the rule (support >= 2) are shown in full detail,
    # each lower-support group contributes up to 3 disclosed examples,
    # and the rest are reported as counts. Full per-candidate evidence
    # breakdowns remain in the task record.
    example_cap = 3
    near = [c for c in task.candidates if support_n(c) >= 2]
    from collections import Counter, defaultdict
    groups = defaultdict(list)
    for c in task.candidates:
        if support_n(c) < 2:
            groups[support_n(c)].append(c)
    background = []
    detailed = list(near)
    for s in sorted(groups, reverse=True):
        detailed.extend(groups[s][:example_cap])
        background.extend(groups[s][example_cap:])
    print(f"\n    display rule (disclosed; DISPLAY batching only, not an "
          f"analytical threshold): candidates meeting >=2 criteria "
          f"shown in full; each lower-support group contributes up to "
          f"{example_cap} examples; the rest reported as counts; "
          f"removed from record: 0", flush=True)
    print(f"    materially relevant competing candidates "
          f"({len(near)} near-satisfying + "
          f"{len(detailed) - len(near)} examples):", flush=True)
    for c in detailed:
        head = (f"      * {c['candidate_id']} [{c.get('kind')}] "
                f"tf={c.get('timeframe')}")
        if "level" in c and c["level"] == c["level"]:  # not NaN
            head += f" level={c['level']}"
        head += f" available_at={c['availability']}"
        print(head, flush=True)
        rtc = c.get("relation_to_context", {})
        print(f"        relation to context: hf_trend="
              f"{rtc.get('hf_trend')} → {rtc.get('region_vs_context', rtc.get('prior_events'))}",
              flush=True)
        for key, label in (("supporting_evidence", "supporting"),
                           ("counterevidence", "counterevidence"),
                           ("unknowns", "unknowns")):
            for e in c.get(key, []):
                print(f"        {label}: {e}", flush=True)
        if c.get("conflict_note"):
            print(f"        conflict: {c['conflict_note']}", flush=True)
    if background:
        dist = Counter(support_n(c) for c in background)
        print(f"\n    background candidates kept in the record "
              f"({len(background)}; shown as counts, not dumped): "
              f"support distribution {dict(dist)}", flush=True)
        print("    (each keeps its full evidence breakdown in "
              "task.candidates)", flush=True)

    concl = task.conclusion or {}
    print(f"\n[4] CONCLUSION: {concl.get('status')}", flush=True)
    print(f"    preferred: {concl.get('preferred')}", flush=True)
    for r in concl.get("reasons", []):
        print(f"    reason: {r}", flush=True)
    if concl.get("status") == "UNRESOLVED_NO_EDGE":
        print("    why unresolved: the declared evidence does not "
              "single out one candidate (or none qualifies) — no "
              "winner is forced and no permanent abstention is "
              "declared: a later version may prefer", flush=True)
    alts = concl.get("alternatives", [])
    print(f"    alternatives in THIS conclusion version (as recorded "
          f"when the version was written): {len(alts)}", flush=True)
    print(f"    current candidate set (rebuilt each boundary): "
          f"{len(task.candidates)} (all kept; none deleted)", flush=True)
    for a in alts[:6]:
        print(f"      - {a.get('candidate_id')}: "
              f"{a.get('why_not_preferred')} "
              f"[supporting={a.get('supporting')} "
              f"counterevidence={a.get('counterevidence')} "
              f"conflict={a.get('conflict')}]",
              flush=True)
    if len(alts) > 6:
        print(f"      … {len(alts) - 6} more alternatives in the record",
              flush=True)

    print("\n[5] EXACTLY WHAT IS WATCHED NEXT (conditional "
          "observation — NOT a prediction):", flush=True)
    for w in task.watch_next:
        print(f"    observable event: {w.get('observable_event')}",
              flush=True)
        print(f"      would change: {w.get('would_change')}", flush=True)
        print(f"      would weaken/suspend: "
              f"{w.get('would_weaken_or_suspend')}", flush=True)
        print(f"      alternative remains: "
              f"{w.get('alternative_remains')}", flush=True)
        print(f"      cannot establish: {w.get('cannot_establish')}",
              flush=True)
    for i in study.readings.interps.values():
        for w in i.watch:
            print(f"    interpretation {i.interp_id} watches: "
                  f"{w.get('observable_event')}", flush=True)


def _ledger_records(ledger, obj_id: str):
    """Ledger records for one object (task/interpretation), in order."""
    out = []
    if ledger is None:
        return out
    for uid, versions in ledger.versions.items():
        res = versions[0]["result"]
        payload = ledger._payloads.get(uid, {})
        inputs = payload.get("inputs", {})
        rec = inputs.get("task") or inputs.get("interpretation") or {}
        if rec.get("task_id") == obj_id or rec.get("interp_id") == obj_id:
            out.append({
                "uid": uid,
                "revision_of": payload.get("revision_of"),
                "decision_time": str(res.decision_time),
                "notes": list(res.notes),
            })
    out.sort(key=lambda r: r["uid"])
    return out


def _print_ledger(ledger, obj_id: str, label: str) -> None:
    recs = _ledger_records(ledger, obj_id)
    print(f"    ledger records for {obj_id} ({label}): {len(recs)} "
          f"record(s)", flush=True)
    for r in recs[-2:]:
        print(f"      uid={r['uid']} revision_of={r['revision_of']}",
              flush=True)
        print(f"        notes: {r['notes']}", flush=True)
        print(f"        decision_time (PROCESSING wall clock): "
              f"{r['decision_time']}", flush=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mirror-dir", required=True)
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--months", default="8")
    ap.add_argument("--pause-at", required=True)
    ap.add_argument("--step", type=int, default=2,
                    help="completed task-scale bars to step forward")
    ap.add_argument("--task", default=None,
                    help="task id to trace (default: most candidates)")
    ap.add_argument("--cadence", action="store_true",
                    help="print the evaluation-cadence trace")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    rows = load_rows(Path(args.mirror_dir), args.year,
                     [int(m) for m in args.months.split(",")])
    stream = ReplayObservationStream(
        rows.copy(), timeline_id="BTCUSDT_1m_decision_trace",
        dataset_identity="BTCUSDT-mirror@27c9be70")
    study = StudyReasoningLayer(
        run_id="connected-read-v1", k=5, task_scale="4h",
        instrument="BTCUSDT")
    loop = MonitoringLoop(stream=stream, frames_builder=frames_builder,
                          engine_factory=engine_factory,
                          task_scale="4h", study_layer=study)

    pause = pd.Timestamp(args.pause_at)
    if pause.tzinfo is None:
        pause = pause.tz_localize("UTC")

    # run to the pause, recording boundary processing wall-clocks
    cadence_rows = []
    prev_labels = []
    while not loop.stream.exhausted:
        t_before = loop.last_record.as_of_time if loop.last_record \
            else None
        r = loop.step_observation()
        if loop.last_record is not None and \
                loop.last_record.as_of_time != t_before:
            # a task-scale boundary was processed at this moment
            wall = _now()
            frames = loop._prefix_frames()
            f15 = frames.get("15m")
            labels = []
            if f15 is not None:
                labels = [str(x) for x in f15.index
                          if t_before is None or
                          pd.Timestamp(x) > pd.Timestamp(t_before)]
            cadence_rows.append({
                "boundary_as_of": str(loop.last_record.as_of_time),
                "processing_wall_clock": wall,
                "new_15m_completion_labels": labels[:2] + (
                    ["…"] if len(labels) > 4 else []) +
                    labels[-2:] if labels else [],
                "n_new_15m": len(labels),
            })
        if loop.last_record is not None and \
                pd.Timestamp(loop.last_record.as_of_time) >= pause:
            break

    print(f"== paused at {loop.last_record.as_of_time} "
          f"(observations consumed: {stream.position}) ==", flush=True)
    _print_decision_trace(study, str(loop.last_record.as_of_time),
                          args.task)

    task0 = _pick_task(study, args.task)
    tid = task0.task_id if task0 is not None else None
    v_before = len(task0.versions) if task0 else 0
    concl_before = json.dumps(task0.conclusion, sort_keys=True,
                              default=str) if task0 else ""
    if tid:
        _print_ledger(loop.engine.ledger, tid, "at pause")
    else:
        print("    (no task to follow)", flush=True)

    # ---- causal stepping on the SAME decision -----------------------
    for n in range(1, max(1, args.step) + 1):
        if loop.stream.exhausted:
            print("== stream exhausted ==", flush=True)
            break
        t_before = loop.last_record.as_of_time
        wall_before = _now()
        r = loop.step_completed_bar()
        wall_after = _now()
        at = str(loop.last_record.as_of_time)
        print(f"\n{'=' * 72}\n== STEP {n}: task-scale boundary "
              f"{at} (processed at wall clock {wall_after})\n{'=' * 72}",
              flush=True)
        task_now = study.readings.tasks.get(tid) if tid else None
        if task_now is None:
            print("  decision: task does not exist", flush=True)
            continue
        v_now = len(task_now.versions)
        concl_now = json.dumps(task_now.conclusion, sort_keys=True,
                               default=str)
        if concl_now != concl_before:
            v = task_now.versions[-1]
            print(f"  decision {tid}: CHANGED → conclusion "
                  f"v{v['version']} (revision_of={v['revision_of']}) "
                  f"recorded_at={v['recorded_at']} (data time of this "
                  f"boundary)", flush=True)
            print(f"    new status={v['conclusion']['status']} "
                  f"preferred={v['conclusion']['preferred']}", flush=True)
            for rr in v["conclusion"].get("reasons", []):
                print(f"    new reason: {rr}", flush=True)
            if v_now > 1:
                old = task_now.versions[-2]
                print(f"    OLD conclusion v{old['version']} "
                      f"(preserved unchanged): "
                      f"status={old['conclusion']['status']} "
                      f"preferred={old['conclusion']['preferred']}",
                      flush=True)
            _print_ledger(loop.engine.ledger, tid, "old + new")
            concl_before = concl_now
        else:
            print(f"  decision {tid}: NO relevant change — conclusion "
                  f"still v{v_now} "
                  f"({task_now.conclusion.get('status')}); nothing was "
                  f"forced", flush=True)
        # what else changed at this boundary (honest inventory)
        comp = task_now.comparison or {}
        print(f"  candidates: before={comp.get('candidates_before_filtering')} "
              f"after={comp.get('candidates_after_filtering')} "
              f"(removed={comp.get('removed_from_record')})",
              flush=True)
        print(f"  support distribution: "
              f"{comp.get('by_support_count')}", flush=True)
        # other tasks at this boundary (compact one-liners)
        for oid, o in study.readings.tasks.items():
            if oid == tid:
                continue
            oc = o.conclusion or {}
            print(f"  other task {oid}: {oc.get('status')} "
                  f"preferred={oc.get('preferred')} "
                  f"candidates={len(o.candidates)} "
                  f"v{o.versions[-1]['version'] if o.versions else 0}",
                  flush=True)

    # ---- cadence trace ---------------------------------------------
    if args.cadence:
        print(f"\n{'=' * 72}\n== CADENCE TRACE (completion vs "
              f"processing vs recording)\n{'=' * 72}", flush=True)
        print("engine cadence (from monitoring.py, verified code):",
              flush=True)
        print("  - 1m observations stream one by one; a 15m or 1h bar "
              "is PUBLISHED to its frame as soon as its last 1m row "
              "completes (completion-labelled resample)", flush=True)
        print("  - the connected-reading pipeline runs ONLY inside "
              "on_boundary, i.e. when a TASK-SCALE (4h) bar completes",
              flush=True)
        print("  - between 4h boundaries only on_observation runs "
              "(fine-touch evidence); it does not scan FVGs or change "
              "interpretations", flush=True)
        print("  - therefore: a 15m bar closing at T is FIRST CONSUMED "
              "by the connected reading at the next 4h boundary "
              "processing; a recorded interpretation can change only "
              "at that processing point", flush=True)
        for cr in cadence_rows[-6:]:
            print(f"\n  boundary as_of (DATA time of the completing "
                  f"4h bar): {cr['boundary_as_of']}", flush=True)
            print(f"    processing/recording (WALL clock): "
                  f"{cr['processing_wall_clock']}", flush=True)
            print(f"    15m bars consumed at this boundary: "
                  f"{cr['n_new_15m']} (completion labels e.g. "
                  f"{cr['new_15m_completion_labels']})", flush=True)
        print("\n  recorded timestamps: region observability_time / "
              "facts 'at' / conclusion recorded_at = DATA times "
              "(completion labels); ledger result decision_time = "
              "PROCESSING wall clock. Both are stored; they are never "
              "mixed.", flush=True)

    if args.out:
        Path(args.out).write_text(json.dumps(
            {"pause_at": str(loop.last_record.as_of_time),
             "task": tid,
             "conclusion": task0.conclusion if task0 else None,
             "comparison": task0.comparison if task0 else None},
            indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
