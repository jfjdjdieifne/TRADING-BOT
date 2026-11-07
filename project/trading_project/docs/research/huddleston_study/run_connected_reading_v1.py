#!/usr/bin/env python3
"""Runnable pause-and-step example — connected readings (deliverable
task §13) on REAL BTCUSDT 1m mirror data.

Demonstrates the connected reading path inside the existing causal
monitoring loop (no second engine, no side channel):
  higher-frame context -> structural references -> reference interaction
  -> lower-frame evidence and three-candle FVG geometry -> comparison of
  competing interpretations -> working conclusion OR explicit non-
  resolution -> conditional watch items -> revision on new evidence.

Modes:
  fresh run + pause + stepping:
    python run_connected_reading_v1.py --mirror-dir DIR \\
        --stop-at 2025-08-07T00:00 --state st.json \\
        --step-advance 3
  resume in a NEW process and step further:
    python run_connected_reading_v1.py --mirror-dir DIR \\
        --state st.json --resume --advance 3
  save/resume equality check (continuous vs new-process resume):
    python run_connected_reading_v1.py --mirror-dir DIR \\
        --state st.json --verify-resume \\
        --stop-at 2025-08-07T00:00 --until 2025-08-09T00:00

Everything printed is what the recorded data establishes.  Nothing
here is a trade, a recommendation, a prediction, or a fill/order
claim.  selection_quality = NOT_ESTABLISHED.
"""

from __future__ import annotations

import argparse
import json
import subprocess
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
    MonitoringLoop,
    ReplayObservationStream,
)
from trading_system.research.contextual_selection.study_links import (  # noqa: E402
    StudyReasoningLayer,
)
from trading_system.research.contextual_selection.connected_readings import (  # noqa: E402
    FVG_UNKNOWNS,
)

import importlib.util  # noqa: E402


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
    return {"1D": _resample("1D", 1440), "4h": _resample("4h", 240),
            "1h": _resample("1h", 60), "15m": _resample("15min", 15)}


def engine_factory(frames):
    return AnalysisEngine(run_id="connected-read-v1", frames=frames,
                          k=5, instrument="BTCUSDT")


def load_rows(mirror_dir: Path, year: int, months) -> pd.DataFrame:
    parts = []
    for m in months:
        p = AN._locate_month_csv(mirror_dir, year, m)
        parts.append(AN._load_month_csv(p))
    rows = pd.concat(parts).sort_index()
    rows = rows[~rows.index.duplicated(keep="first")]
    return rows


# ---------------------------------------------------------------- printing

def _print_pause_view(study, tag: str) -> None:
    print(f"\n== PAUSED VIEW ({tag}) ==", flush=True)
    hf = study.hf_context
    print(f"[context] higher-frame trend={hf.get('trend')} "
          f"established_at={hf.get('established_at')}", flush=True)
    print(f"[context] evidence={hf.get('evidence')}", flush=True)
    cr = study.readings
    print(f"[references] structural refs on task frame: "
          f"{len(getattr(study, 'candidates', []))} candidate(s) "
          f"(see study candidates below)", flush=True)
    for c in study.candidates:
        print(f"  ref {c.candidate_id}: {c.state} role={c.role} "
              f"bar={c.bar_time} "
              f"level_relation={c.to_record().get('level_relation')}",
              flush=True)
    print(f"[FVG regions] {len(cr.regions)} observable region(s):",
          flush=True)
    for rid, r in sorted(cr.regions.items()):
        print(f"  {rid} {r.direction} [{r.lower_bound:.2f}, "
              f"{r.upper_bound:.2f}] @{r.timeframe} observable_at="
              f"{r.observability_time} ce_midpoint={r.ce_midpoint:.2f} "
              f"interactions={len(r.interactions)}", flush=True)
    print(f"[cross-timeframe links] {len(cr.links)} link(s), each a "
          f"relation, never an identity claim:", flush=True)
    for l in cr.links:
        print(f"  {l.link_id}: {l.subject_id} ({l.subject_frame}) "
              f"--{l.relation}-- {l.other_id} ({l.other_frame})",
              flush=True)
    print(f"[shift watches] {len(study.shift_watches)}:", flush=True)
    for w in study.shift_watches:
        print(f"  {w.watch_id} [{w.status}] crossing={w.crossing}",
              flush=True)
    print(f"[reading tasks] {len(cr.tasks)}:", flush=True)
    for t in cr.tasks.values():
        concl = t.conclusion or {}
        print(f"  {t.task_id}: {concl.get('status')} "
              f"preferred={concl.get('preferred')}", flush=True)
        for r in concl.get("reasons", []):
            print(f"    reason: {r}", flush=True)
        for a in concl.get("alternatives", []):
            print(f"    alternative: {a.get('candidate_id')} — "
                  f"{a.get('why_not_preferred')}", flush=True)
    print(f"[working interpretations] {len(cr.interps)}:", flush=True)
    for i in cr.interps.values():
        print(f"  {i.interp_id} [{i.status}] v{i.versions[-1]['version']}"
              f" ({i.revision_count} revision(s))", flush=True)
        print(f"    statement: {i.statement}", flush=True)
        for a in i.alternatives:
            print(f"    alternative: {a.get('statement')} — "
                  f"{a.get('class')}", flush=True)
        for w in i.watch:
            print(f"    watch next: {w.get('observable_event')}",
                  flush=True)
            print(f"      would change: {w.get('would_change')}",
                  flush=True)
            print(f"      cannot establish: "
                  f"{w.get('cannot_establish')}", flush=True)
    print("[unknowns] what the data cannot establish:", flush=True)
    for u in FVG_UNKNOWNS:
        print(f"  - {u}", flush=True)


def _readings_counts(study) -> dict:
    cr = study.readings
    return {
        "regions": len(cr.regions),
        "links": len(cr.links),
        "task_versions": sum(len(t.versions) for t in cr.tasks.values()),
        "interp_versions": sum(len(i.versions)
                               for i in cr.interps.values()),
        "facts": len(cr.seq_facts),
    }


def _print_step_delta(before: dict, study, tag: str) -> None:
    after = _readings_counts(study)
    changed = {k: (before[k], after[k]) for k in after
               if before[k] != after[k]}
    if changed:
        print(f"\n[step {tag}] NEW OBSERVED/RECORDED:", flush=True)
        for k, (b, a) in sorted(changed.items()):
            print(f"  {k}: {b} -> {a}", flush=True)
        cr = study.readings
        for t in cr.tasks.values():
            if t.versions and str(t.versions[-1].get("recorded_at")) \
                    >= tag[:10]:
                v = t.versions[-1]
                print(f"  task {t.task_id} conclusion v"
                      f"{v['version']}: {v['conclusion']['status']}",
                      flush=True)
        for i in cr.interps.values():
            if len(i.versions) > 1 and \
                    str(i.versions[-1].get("recorded_at")) >= tag[:10]:
                v = i.versions[-1]
                print(f"  interpretation {i.interp_id} REVISED to v"
                      f"{v['version']}: {v['reason']}", flush=True)
    else:
        print(f"\n[step {tag}] no change — nothing was forced; the "
              f"recorded state is honestly unchanged", flush=True)


# ------------------------------------------------------------------- main

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mirror-dir", required=True)
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--months", default="8,9")
    ap.add_argument("--stop-at", default=None)
    ap.add_argument("--until", default=None,
                    help="verify-resume: continue target")
    ap.add_argument("--state", required=True)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--advance", type=int, default=1)
    ap.add_argument("--step-advance", type=int, default=0,
                    help="after the pause, step this many 4h boundaries "
                         "printing each delta")
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--verify-resume", action="store_true")
    args = ap.parse_args(argv)

    out_dir = Path(args.out_dir or (HERE / "run_artifacts"))
    out_dir.mkdir(parents=True, exist_ok=True)
    months = [int(m) for m in args.months.split(",")]
    rows = load_rows(Path(args.mirror_dir), args.year, months)

    def mk_loop():
        stream = ReplayObservationStream(
            rows.copy(), timeline_id="BTCUSDT_1m_connected_read_v1",
            dataset_identity="BTCUSDT-mirror@27c9be70")
        study = StudyReasoningLayer(run_id="connected-read-v1", k=5,
                                    task_scale="4h",
                                    instrument="BTCUSDT")
        loop = MonitoringLoop(stream=stream, frames_builder=frames_builder,
                              engine_factory=engine_factory,
                              task_scale="4h", study_layer=study)
        return loop, stream, study

    # ---- save/resume equality (continuous vs NEW-process resume) ----
    if args.verify_resume:
        if not (args.stop_at and args.until):
            ap.error("--verify-resume needs --stop-at and --until")
        t1 = pd.Timestamp(args.stop_at)
        t2 = pd.Timestamp(args.until)
        if t1.tzinfo is None:
            t1 = t1.tz_localize("UTC")
        if t2.tzinfo is None:
            t2 = t2.tz_localize("UTC")
        loop, stream, study = mk_loop()
        loop.run_to(t1)
        loop.save_state(args.state)
        at_t1 = json.dumps(loop.state_dict()["study_state"],
                           sort_keys=True, default=str)
        loop.run_to(t2)
        cont = json.dumps(loop.state_dict()["study_state"],
                          sort_keys=True, default=str)
        cmd = [sys.executable, str(Path(__file__).resolve()),
               "--mirror-dir", args.mirror_dir, "--state", args.state,
               "--resume", "--until", args.until,
               "--out-dir", str(out_dir)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            print(proc.stdout[-2000:], proc.stderr[-2000:],
                  flush=True)
            return proc.returncode
        resumed = json.loads(
            (out_dir / "verify_resumed.json").read_text())["study_state"]
        resumed = json.dumps(resumed, sort_keys=True, default=str)
        ok1 = (at_t1 == json.dumps(
            json.loads(at_t1), sort_keys=True, default=str))
        ok_resume_matches_cont = (resumed == cont)
        print(f"== study_state at T1 saved ({len(at_t1)} chars) ==",
              flush=True)
        print(f"== NEW-process resume == continuous run: "
              f"{'PASS' if ok_resume_matches_cont else 'FAIL'} ==",
              flush=True)
        (out_dir / "verify_result.json").write_text(json.dumps({
            "resume_equals_continuous": ok_resume_matches_cont}, indent=1))
        return 0 if ok_resume_matches_cont else 1

    # ---- resume mode -------------------------------------------------
    if args.resume:
        stream = ReplayObservationStream(
            rows.copy(), timeline_id="BTCUSDT_1m_connected_read_v1",
            dataset_identity="BTCUSDT-mirror@27c9be70")
        study = StudyReasoningLayer(run_id="connected-read-v1", k=5,
                                    task_scale="4h",
                                    instrument="BTCUSDT")
        loop = MonitoringLoop.load_state(
            args.state, stream=stream, frames_builder=frames_builder,
            engine_factory=engine_factory, task_scale="4h",
            study_layer=study)
        print(f"== resumed {args.state} at cursor {stream.position} "
              f"({stream.current_time}) ==", flush=True)
        _print_pause_view(study, "at resume, BEFORE stepping")
        if getattr(args, "until", None):
            t_until = pd.Timestamp(args.until)
            if t_until.tzinfo is None:
                t_until = t_until.tz_localize("UTC")
            loop.run_to(t_until)
            out = {"study_state": loop.state_dict()["study_state"]}
            (out_dir / "verify_resumed.json").write_text(
                json.dumps(out, default=str))
            print("== resumed run to "
                  f"{args.until}; study_state written ==", flush=True)
            return 0
        before = _readings_counts(study)
        for _ in range(max(1, args.advance)):
            if loop.stream.exhausted:
                break
            r = loop.step_completed_bar()
            print(r.to_text(), flush=True)
        loop.save_state(args.state)
        _print_pause_view(study, "after stepping")
        _print_step_delta(before, study, str(loop.last_record.as_of_time))
        print(f"== state saved (cursor {loop.stream.position}) =="
              "\n== append-only: earlier task/interpretation versions "
              "and ledger records are preserved unchanged ==",
              flush=True)
        return 0

    # ---- fresh run + pause + optional stepping -----------------------
    if not args.stop_at:
        ap.error("provide --stop-at T (fresh run) or --resume")
    loop, stream, study = mk_loop()
    t0 = time.time()
    target = pd.Timestamp(args.stop_at)
    if target.tzinfo is None:
        target = target.tz_localize("UTC")
    reports = loop.run_to(target)
    changed = [r for r in reports if r.material_change]
    print(f"== stopped at {loop.last_record.as_of_time} "
          f"({stream.position} observations; {len(reports)} steps, "
          f"{len(changed)} material) in {time.time() - t0:.1f}s ==",
          flush=True)
    _print_pause_view(study, f"at {loop.last_record.as_of_time}")
    loop.save_state(args.state)
    print(f"== state saved to {args.state} ==", flush=True)

    before = _readings_counts(study)
    for n in range(max(0, args.step_advance)):
        if loop.stream.exhausted:
            break
        r = loop.step_completed_bar()
        tag = str(loop.last_record.as_of_time)
        _print_step_delta(before, study, tag)
        before = _readings_counts(study)
    if args.step_advance:
        loop.save_state(args.state)
        _print_pause_view(study, f"after {args.step_advance} step(s)")
        print(f"== final state saved (cursor {stream.position}) =="
              "\n== resuming this state in a NEW process reproduces the "
              "continuous run (see --verify-resume) ==", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
