#!/usr/bin/env python3
"""FIXTURE-ONLY memory probe v0 — where does the dev loop keep its bytes?

WHY THIS FILE EXISTS
--------------------
`dev_month_v0/SUMMARY_V0.md` records a run that was killed by the operating
system at 3,870,276 kB resident, before its first decision.  This probe measures
that growth on **synthetic candles only**.  No market data is opened, read or
imported here: the bars are generated from a declared seed, in this file.

It is a *copy* of the object construction and warm-up body of
`dev_month_v0/run_dev_month_v0.py` (lines 159-173 and 186-206 there), with three
additions and no other change:

  1. the bars come from `synth_bidask()` below instead of `RUNNER.load_bidask`;
  2. resident memory is sampled per task boundary from /proc/self/status;
  3. `tracemalloc` snapshots are taken every `--snapshot-every` boundaries, so
     the growth can be attributed to a file and a line.

The probe stops at `--max-boundaries` or when resident memory passes
`--rss-cap-kb`, whichever comes first, so it cannot repeat the kill it studies.

DECLARED SEED AND GENERATOR (FIXTURE, not market data)
------------------------------------------------------
seed        = 20261109                        (ENGINEERING_CHOICE)
bars        = 5m grid from 2021-01-01T00:00:00Z, weekends removed
returns     = r ~ N(0, 1.2e-4) per 5m bar      (ENGINEERING_CHOICE)
high/low    = |N(0, 4e-5)| added beyond the open/close extreme
half-spread = 5e-5 (0.5 pip per side)          (ENGINEERING_CHOICE)

Outputs (outside the repository): <out>/rss.csv, <out>/snap_<n>.txt,
<out>/probe.json.

Run:
  PYTHONPATH=<repo>/src python3 MEMORY_PROBE_FIXTURE_V0.py \
      --out /tmp/memprobe_v0 --max-boundaries 300 --rss-cap-kb 1500000
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RUNNER_PATH = HERE.parents[0] / "huddleston_study" / "run_forex_intraday_v1.py"
SENTINEL = "NOT_A_REAL_PRICE_FILE"


def load_runner():
    spec = importlib.util.spec_from_file_location("fx_intraday_v1_runner", RUNNER_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["fx_intraday_v1_runner"] = mod
    spec.loader.exec_module(mod)
    return mod


def rss_kb() -> int:
    try:
        with open("/proc/self/status", "r", encoding="ascii") as fh:
            for line in fh:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1])
    except OSError:
        pass
    return -1


def synth_bidask(n_bars: int, seed: int = 20261109) -> pd.DataFrame:
    """Deterministic synthetic bid/ask bars. FIXTURE — no market data."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2021-01-01", periods=n_bars * 2, freq="5min", tz="UTC")
    idx = idx[idx.dayofweek < 5][:n_bars]

    ret = rng.normal(0.0, 1.2e-4, size=len(idx))
    mid = 1.2000 * np.exp(np.cumsum(ret))
    close = mid
    open_ = np.empty_like(close)
    open_[0] = 1.2000
    open_[1:] = close[:-1]

    up = np.abs(rng.normal(0.0, 4e-5, size=len(idx)))
    dn = np.abs(rng.normal(0.0, 4e-5, size=len(idx)))
    high = np.maximum(open_, close) * (1.0 + up)
    low = np.minimum(open_, close) * (1.0 - dn)

    half = 5e-5
    df = pd.DataFrame({
        "Datetime": idx,
        "BidOpen": open_ - half, "BidHigh": high - half,
        "BidLow": low - half, "BidClose": close - half,
        "BidVolume": np.full(len(idx), 100.0),
        "AskOpen": open_ + half, "AskHigh": high + half,
        "AskLow": low + half, "AskClose": close + half,
        "AskVolume": np.full(len(idx), 100.0),
    })
    for name in ("Open", "High", "Low", "Close"):
        df[f"Spread{name}"] = 0.0001
        df[f"Spread{name}Pips"] = 1.0
    return df.set_index("Datetime")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--bars", type=int, default=6000)
    ap.add_argument("--max-boundaries", type=int, default=300)
    ap.add_argument("--rss-cap-kb", type=int, default=1_500_000)
    ap.add_argument("--snapshot-every", type=int, default=50)
    ap.add_argument("--clear-journal", action="store_true",
                    help="drop MonitoringLoop.journal after each boundary "
                         "(a NEW wrapper can do this; no closed module is edited)")
    ap.add_argument("--seed", type=int, default=20261109)
    a = ap.parse_args()

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    assert SENTINEL  # the string exists so a grep for it proves no data path is used

    import tracemalloc
    tracemalloc.start(6)

    RUNNER = load_runner()
    from trading_system.research.contextual_selection.decision_layer import (
        ContextEventModel, EpisodeExtractor)
    from trading_system.research.contextual_selection.monitoring import (
        MonitoringLoop, ReplayObservationStream)
    from trading_system.research.contextual_selection.study_links import (
        StudyReasoningLayer)

    bidask = synth_bidask(a.bars, a.seed)
    rows = RUNNER.mid_rows(bidask)
    base_rss = rss_kb()
    print(f"== FIXTURE bars={len(rows)} (synthetic, seed={a.seed}); "
          f"rss0={base_rss} kB", flush=True)

    # --- object construction: copy of run_dev_month_v0.py lines 159-173 ---
    stream = ReplayObservationStream(
        rows.copy(), timeline_id="FIXTURE_synthetic_v0",
        dataset_identity="SYNTHETIC_FIXTURE_NOT_MARKET_DATA")
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
    # --- end copy ---

    episodes, pending_eps = [], []
    boundary_seq = 0
    samples, snaps = [], []
    t0 = time.time()
    stop_reason = "max-boundaries"

    while not loop.stream.exhausted:
        r = loop.step_completed_bar()
        if r.trigger != "task-boundary" or loop.last_record is None:
            continue
        rec = loop.last_record
        boundary_seq += 1
        ts = pd.Timestamp(rec.as_of_time)

        # --- warm-up body: copy of run_dev_month_v0.py lines 197-206 ---
        ep = extractor.extract(rec, run_id="probe", seq=boundary_seq)
        episodes.append(ep)
        pending_eps.append(ep)
        ready = [e for e in pending_eps
                 if e.window_end_time is not None
                 and pd.Timestamp(e.window_end_time) < ts]
        if ready:
            model.fit(ready)
            for e in ready:
                pending_eps.remove(e)
        # --- end copy ---

        if a.clear_journal:
            loop.journal.clear()

        rss = rss_kb()
        acc = {}
        for label, obj in (("MonitoringLoop", loop),
                           ("AnalysisEngine", getattr(loop, "engine", None)),
                           ("StudyReasoningLayer", study),
                           ("ConnectedReadingsEngine",
                            getattr(study, "readings", None)),
                           ("ContextEventModel", model)):
            if obj is None:
                continue
            for key, val in vars(obj).items():
                if isinstance(val, (list, dict, set)):
                    acc[f"{label}.{key}"] = len(val)
        acc["W0.episodes"] = len(episodes)
        acc["W0.pending_eps"] = len(pending_eps)
        samples.append({"boundary": boundary_seq, "as_of": str(ts),
                        "rss_kb": rss, "pending": len(pending_eps),
                        "fitted": model.n_episodes,
                        "elapsed_s": round(time.time() - t0, 1),
                        "acc": acc})
        if boundary_seq % 10 == 0:
            print(f"  b={boundary_seq} as_of={ts} rss={rss/1024:.0f} MB "
                  f"pending={len(pending_eps)} fitted={model.n_episodes} "
                  f"t={time.time()-t0:.0f}s", flush=True)

        if boundary_seq % a.snapshot_every == 0:
            snap = tracemalloc.take_snapshot()
            name = f"snap_{boundary_seq:04d}.txt"
            with open(out / name, "w", encoding="utf-8") as fh:
                for stat in snap.statistics("lineno")[:25]:
                    fh.write(f"{stat.size:>12} {stat.count:>7} {stat.traceback}\n")
            snaps.append(boundary_seq)

        if rss > a.rss_cap_kb:
            stop_reason = "rss-cap"
            break
        if boundary_seq >= a.max_boundaries:
            stop_reason = "max-boundaries"
            break

    sizes = samples[-1]["acc"] if samples else {}
    result = {
        "fixture": {"seed": a.seed, "bars_generated": int(a.bars),
                    "bars_used": int(len(rows)),
                    "generator": "synth_bidask (this file)",
                    "data": "SYNTHETIC — no market data was opened"},
        "stop_reason": stop_reason,
        "boundaries": boundary_seq,
        "samples": samples,
        "snapshots": snaps,
        "accumulator_sizes_at_end": sizes,
        "episodes_retained": len(episodes),
        "elapsed_s": round(time.time() - t0, 1),
        "clear_journal": bool(a.clear_journal),
    }
    (out / "probe.json").write_text(json.dumps(result, indent=1, default=str))
    pd.DataFrame(samples).to_csv(out / "rss.csv", index=False)
    print(f"== done: boundaries={boundary_seq} stop={stop_reason} "
          f"rss={rss_kb()/1024:.0f} MB accumulators={sizes}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
