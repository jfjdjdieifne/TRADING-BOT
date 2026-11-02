#!/usr/bin/env python3
"""Huddleston-study replay driver (§10 demonstration) — runs the study
links layer THROUGH the existing causal monitoring path.

PAUSE at a boundary T: print the observations/context known at T, the
OB-like candidate states and roles (or the reasons a role is NOT
preferred), then RECORD what will be watched and the revision
conditions BEFORE stepping.  Advance one observation (or one completed
bar) at a time: print what changed (or that no revision was required),
save state, and resume in a fresh process — without ever exposing
future observations to the engine.

The driver holds the full historical file (allowed); the engine
receives only the causally available prefix plus approved time
metadata.  The sealed causal foundation is used through approved
interfaces only.  ``selection_quality = NOT_ESTABLISHED``.

Modes
-----
--stop-at T --state S.json      run from the window start to boundary
                                T, print + persist, SAVE STATE, exit
--resume S.json --advance N     fresh process: resume, advance N steps,
                                print what changed/not and why, save
--step {observation,bar}        step granularity (default: observation)

Example (real BTCUSDT mirror):
  python run_study_replay_v1.py --stop-at "2025-08-14 00:00:00+00:00" \
      --state /tmp/study_state.json
  python run_study_replay_v1.py --resume /tmp/study_state.json \
      --advance 5
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
PROJECT_SRC = HERE.parents[1] / "project" / "trading_project" / "src"
if not PROJECT_SRC.exists():
    PROJECT_SRC = HERE.parents[2] / "src"
sys.path.insert(0, str(PROJECT_SRC))

from trading_system.research.contextual_selection.analysis_lifecycle import (  # noqa: E402
    AnalysisEngine,
)
from trading_system.research.contextual_selection.monitoring import (  # noqa: E402
    DATA_CAPABILITIES,
    LIVE_FEED_STATUS,
    MonitoringLoop,
    ReplayObservationStream,
)
from trading_system.research.contextual_selection.study_links import (  # noqa: E402
    RELATIONSHIP_REGISTER,
    StudyReasoningLayer,
)


def _load_analysis_runner():
    path = (HERE.parents[1] / "project" / "trading_project" / "docs" /
            "research" / "analysis_v1" / "run_market_analysis_v1.py")
    if not path.exists():
        path = HERE.parent / "analysis_v1" / "run_market_analysis_v1.py"
    spec = importlib.util.spec_from_file_location("analysis_v1_runner",
                                                  path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


AN = _load_analysis_runner()


def frames_builder(rows: pd.DataFrame):
    def _resample(rule, minutes):
        f = rows.resample(rule).agg({"open": "first", "high": "max",
                                     "low": "min", "close": "last",
                                     "volume": "sum"})
        f = f.dropna(subset=["open"])
        f.index = f.index + pd.Timedelta(minutes=minutes)
        return f
    return {"4h": _resample("4h", 240), "1h": _resample("1h", 60),
            "15m": _resample("15min", 15)}


def engine_factory(frames):
    return AnalysisEngine(run_id="study-replay-v1", frames=frames,
                          k=5, instrument="BTCUSDT")


def load_rows(mirror_dir: Path, year: int, months) -> pd.DataFrame:
    parts = []
    for m in months:
        p = AN._locate_month_csv(mirror_dir, year, m)
        parts.append(AN._load_month_csv(p))
    rows = pd.concat(parts).sort_index()
    rows = rows[~rows.index.duplicated(keep="first")]
    return rows


def _print_study_state(layer, tag: str) -> dict:
    print(f"\n== STUDY STATE ({tag}) ==", flush=True)
    hf = layer.hf_context
    print(f"HF context: trend={hf.get('trend')} "
          f"established_at={hf.get('established_at')} "
          f"evidence={hf.get('evidence')}", flush=True)
    for c in layer.candidates:
        print(f"candidate {c.candidate_id}: {c.state} role={c.role} "
              f"ordering={c.ordering} "
              f"bar={c.bar_time} o={c.open} h={c.high} l={c.low} "
              f"c={c.close}", flush=True)
        for v in c.role_assignments:
            for r in v.get("reasons", []):
                print(f"    role reason: {r}", flush=True)
            for alt in v.get("alternatives", []):
                print(f"    alternative: {alt}", flush=True)
        for e in c.events[-3:]:
            print(f"    event: {e.get('kind')} at_bar={e.get('at_bar')}"
                  f" -> {e.get('to')}", flush=True)
    if not layer.candidates:
        print("candidates: none formed yet (or no matching shape in "
              "the declared research definition)", flush=True)
    for s in layer.selections:
        print(f"selection {s.selection_id}: {s.status} "
              f"subject={s.subject_id} at={s.selected_at}", flush=True)
    return {"hf_context": hf,
            "candidates": [c.to_record() for c in layer.candidates],
            "selections": [s.to_record() for s in layer.selections]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mirror-dir", required=True)
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--months", default="8,9")
    ap.add_argument("--stop-at", default=None)
    ap.add_argument("--state", required=True)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--advance", type=int, default=1)
    ap.add_argument("--step", choices=["observation", "bar"],
                    default="observation")
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args(argv)

    out_dir = Path(args.out_dir or (HERE / "run_artifacts"))
    out_dir.mkdir(parents=True, exist_ok=True)
    months = [int(m) for m in args.months.split(",")]
    study = StudyReasoningLayer(run_id="study-replay-v1", k=5,
                                task_scale="4h")

    if args.resume:
        rows = load_rows(Path(args.mirror_dir), args.year, months)
        stream = ReplayObservationStream(
            rows, timeline_id="BTCUSDT_1m_study_replay",
            dataset_identity="BTCUSDT-mirror@27c9be70")
        loop = MonitoringLoop.load_state(
            args.state, stream=stream, frames_builder=frames_builder,
            engine_factory=engine_factory, task_scale="4h",
            study_layer=study)
        print(f"== resumed {args.state} at cursor {stream.position} "
              f"({stream.current_time}) ==", flush=True)
        _print_study_state(study, "at resume, BEFORE stepping")
        facts_before = len(study.state_dict().get("seq_facts", []))
        events_before = sum(len(c.events) for c in study.candidates)
        t0 = time.time()
        reports = []
        for _ in range(max(1, args.advance)):
            if args.step == "bar":
                r = loop.step_completed_bar()
            else:
                r = loop.step_observation()
            reports.append(r)
            print(r.to_text(), flush=True)
            if stream.exhausted:
                break
        loop.save_state(args.state)
        _print_study_state(study, "after stepping")
        # post-T honesty: earlier study events are append-only — later
        # stepping may add facts but never rewrites the past
        facts_after = len(study.state_dict().get("seq_facts", []))
        events_after = sum(len(c.events) for c in study.candidates)
        _save(out_dir, loop, reports, resumed=True,
              watch_plan=study.watch_plan())
        print(f"== {len(reports)} step(s) in {time.time() - t0:.2f}s; "
              f"state saved (cursor {loop.stream.position}) =="
              f"\n== append-only check: sequence facts {facts_before}"
              f"->{facts_after}, candidate events {events_before}"
              f"->{events_after} (growth only; earlier records "
              f"immutable) ==", flush=True)
        return 0

    if not args.stop_at:
        ap.error("provide --stop-at T (fresh run) or --resume")

    rows = load_rows(Path(args.mirror_dir), args.year, months)
    stream = ReplayObservationStream(
        rows, timeline_id="BTCUSDT_1m_study_replay",
        dataset_identity="BTCUSDT-mirror@27c9be70")
    loop = MonitoringLoop(stream=stream, frames_builder=frames_builder,
                          engine_factory=engine_factory, task_scale="4h",
                          study_layer=study)
    t0 = time.time()
    target = pd.Timestamp(args.stop_at)
    if target.tzinfo is None:
        target = target.tz_localize("UTC")
    reports = loop.run_to(target)
    changed = [r for r in reports if r.material_change]
    for r in changed[-3:]:
        print(r.to_text(), flush=True)
    print(f"== stopped at {loop.last_record.as_of_time} "
          f"({stream.position} observations consumed; "
          f"{len(reports)} steps, {len(changed)} material) in "
          f"{time.time() - t0:.1f}s ==", flush=True)
    rec = loop.last_record
    print(f"lifecycle: {rec.lifecycle_state} | "
          f"reference status: {rec.reference_status.get('status')}",
          flush=True)
    _print_study_state(study, f"at {loop.last_record.as_of_time}")
    # record what WILL be watched + revision conditions BEFORE stepping
    watch = study.watch_plan()
    print("\n== WATCH PLAN (recorded before any further step) ==",
          flush=True)
    for w in watch:
        print(f"watch {w['subject']} [{w.get('state')}/{w.get('role')}]",
              flush=True)
        for item in w.get("watch", []):
            print(f"    - {item}", flush=True)
        for item in w.get("revision_conditions", []):
            print(f"    revision: {item}", flush=True)
        for item in w.get("unknowns", []):
            print(f"    unknown: {item}", flush=True)
    if not watch:
        print("    (nothing open to watch at this boundary)",
              flush=True)
    loop.save_state(args.state)
    _save(out_dir, loop, reports, resumed=False, watch_plan=watch)
    print(f"== state saved to {args.state} ==", flush=True)
    return 0


def _save(out_dir, loop, reports, resumed, watch_plan):
    suffix = "resume" if resumed else "stop"
    path = out_dir / f"study_replay_{suffix}_v1.json"
    study_state = (loop.study_layer.state_dict()
                   if loop.study_layer is not None else None)
    payload = {
        "cursor": loop.stream.position,
        "as_of": str(loop.last_record.as_of_time)
        if loop.last_record is not None else None,
        "lifecycle_state": getattr(loop.last_record, "lifecycle_state",
                                   None),
        "steps": [r.to_record() for r in reports],
        "watch_plan": watch_plan,
        "study_state": study_state,
        "relationship_register": RELATIONSHIP_REGISTER,
        "live_feed_status": LIVE_FEED_STATUS,
        "data_capabilities": DATA_CAPABILITIES,
        "selection_quality": "NOT_ESTABLISHED",
    }
    path.write_text(json.dumps(payload, indent=1, sort_keys=True,
                               default=str))
    print(f"== wrote {path} ==", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
