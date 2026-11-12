#!/usr/bin/env python3
"""Causal step-by-step historical replay driver (task scope).

PAUSE at a decision boundary, produce and persist the analysis using
only information available at that boundary, then ADVANCE one available
observation (or one completed bar) at a time, show what changed (or that
no revision was required), pause again, and resume in a fresh process —
without ever exposing future observations to the engine.

The driver holds the full historical file (allowed); the engine receives
only the causally available prefix plus approved time metadata (the
declared timeline grid).  The sealed causal foundation is used through
approved interfaces only.

Modes
-----
--stop-at T --state S.json      run from the window start to the task
                                boundary T, print step reports and the
                                stopped analysis, SAVE STATE, exit
--resume S.json --advance N     fresh process: resume, advance N steps
                                (observation or completed-bar), print
                                what changed, save state, exit
--step {observation,bar}        step granularity (default: observation,
                                the data source's actual resolution)

Example (real BTCUSDT mirror):
  python run_step_replay_v1.py --stop-at "2025-08-14 00:00:00+00:00" \\
      --state /tmp/replay_state.json
  python run_step_replay_v1.py --resume /tmp/replay_state.json \\
      --advance 1 --step bar
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


def _load_analysis_runner():
    path = HERE.parent / "analysis_v1" / "run_market_analysis_v1.py"
    spec = importlib.util.spec_from_file_location("analysis_v1_runner",
                                                  path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


AN = _load_analysis_runner()


def frames_builder(rows: pd.DataFrame):
    """Prefix frames with the verified completion-label convention
    (same rules as the analysis runner's loader)."""
    def _resample(rule, minutes):
        f = rows.resample(rule).agg({"open": "first", "high": "max",
                                     "low": "min", "close": "last",
                                     "volume": "sum"})
        f = f.dropna(subset=["open"])
        f.index = f.index + pd.Timedelta(minutes=minutes)
        return f
    r15 = _resample("15min", 15)
    r1h = _resample("1h", 60)
    r4h = _resample("4h", 240)
    return {"4h": r4h, "1h": r1h, "15m": r15}


def engine_factory(frames):
    return AnalysisEngine(run_id="replay-step-v1", frames=frames,
                          k=5, instrument="BTCUSDT")


def load_rows(mirror_dir: Path, year: int, months) -> pd.DataFrame:
    parts = []
    for m in months:
        p = AN._locate_month_csv(mirror_dir, year, m)
        parts.append(AN._load_month_csv(p))
    rows = pd.concat(parts).sort_index()
    rows = rows[~rows.index.duplicated(keep="first")]
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mirror-dir", required=True)
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--months", default="8,9")
    ap.add_argument("--from", dest="t_from", default="2025-08-01")
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

    if args.resume:
        # fresh process: rebuild the stream (driver-side file) and
        # resume the saved state (engine sees only the prefix)
        rows = load_rows(Path(args.mirror_dir), args.year, months)
        stream = ReplayObservationStream(
            rows, timeline_id="BTCUSDT_1m_replay_step",
            dataset_identity="BTCUSDT-mirror@27c9be70")
        loop = MonitoringLoop.load_state(
            args.state, stream=stream, frames_builder=frames_builder,
            engine_factory=engine_factory, task_scale="4h")
        print(f"== resumed {args.state} at cursor {stream.position} "
              f"({stream.current_time}) ==", flush=True)
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
        _save(out_dir, loop, reports, resumed=True)
        print(f"== {len(reports)} step(s) in {time.time() - t0:.2f}s; "
              f"state saved (cursor {loop.stream.position}) ==",
              flush=True)
        return 0

    if not args.stop_at:
        ap.error("provide --stop-at T (fresh run) or --resume")

    rows = load_rows(Path(args.mirror_dir), args.year, months)
    stream = ReplayObservationStream(
        rows, timeline_id="BTCUSDT_1m_replay_step",
        dataset_identity="BTCUSDT-mirror@27c9be70")
    loop = MonitoringLoop(stream=stream, frames_builder=frames_builder,
                          engine_factory=engine_factory, task_scale="4h")
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
          f"state: {rec.reference_status.get('status')}", flush=True)
    for f in rec.forecasts:
        print(f"forecast {f.forecast_id} v{f.version}: {f.status} "
              f"(observed_before_record={f.observed_before_record})",
              flush=True)
    loop.save_state(args.state)
    _save(out_dir, loop, reports, resumed=False)
    print(f"== state saved to {args.state} ==", flush=True)
    return 0


def _save(out_dir, loop, reports, resumed):
    suffix = "resume" if resumed else "stop"
    path = out_dir / f"step_replay_{suffix}_v1.json"
    payload = {
        "cursor": loop.stream.position,
        "as_of": str(loop.last_record.as_of_time)
        if loop.last_record is not None else None,
        "lifecycle_state": getattr(loop.last_record, "lifecycle_state",
                                   None),
        "steps": [r.to_record() for r in reports],
        "live_feed_status": LIVE_FEED_STATUS,
        "data_capabilities": DATA_CAPABILITIES,
        "selection_quality": "NOT_ESTABLISHED",
    }
    path.write_text(json.dumps(payload, indent=1, sort_keys=True,
                               default=str))
    print(f"== wrote {path} ==", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
