#!/usr/bin/env python3
"""Contextual market-analysis engine V1 — local runner (task scope).

Runs the end-to-end ANALYTICAL lifecycle (observations -> structural
facts -> interpretations -> conditional forecasts -> next awaited
observation) over real BTCUSDT data through the existing approved
components.  It produces analysis records — never trading signals, never
orders, never probabilities.

Modes
-----
--at ISO         one analysis as of a single time -> JSON + explanation
--replay         chronological boundaries (daily default) -> JSONL +
                 Markdown explanation + provenance manifest (+ optional
                 snapshot)

Both modes record selection_quality = NOT_ESTABLISHED.  The engine is
NOT Michael Huddleston, does NOT replicate his private judgment, and has
NO proven accuracy.

Examples
--------
  python run_market_analysis_v1.py --at "2025-08-14 00:00:00+00:00"
  python run_market_analysis_v1.py --replay \
      --from 2025-08-01 --to 2025-08-03

Evidence provenance (recorded in the manifest):
  dataset commit 27c9be705ac9280248672c895082c057b979ebff
  BTCUSDT_1m_2025-08.csv  sha256
      15d26d2374bce8804e25012ff76e5fad976633a2fde843ffb0f487e1c90a0cf4
  BTCUSDT_1m_2025-09.csv  sha256
      e1d5c8f350d83df866ff36c3b4d74f7e5b383db07cde7bca0ee1f200d7a48979
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
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
)

DATASET_COMMIT = "27c9be705ac9280248672c895082c057b979ebff"
INPUT_SHA256 = {
    "BTCUSDT_1m_2025-08.csv":
        "15d26d2374bce8804e25012ff76e5fad976633a2fde843ffb0f487e1c90a0cf4",
    "BTCUSDT_1m_2025-09.csv":
        "e1d5c8f350d83df866ff36c3b4d74f7e5b383db07cde7bca0ee1f200d7a48979",
}
DATASET_MIRROR = ("parshant231234-eng/BTCUSDT-Historical-Data "
                  "@27c9be705ac9280248672c895082c057b979ebff")


# --------------------------------------------------------------------- #
# data loading (same conventions as the expert-selection runner)         #
# --------------------------------------------------------------------- #
def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _locate_month_csv(mirror_dir: Path, year: int, month: int) -> Path:
    name = f"BTCUSDT_1m_{year:04d}-{month:02d}.csv"
    direct = mirror_dir / name
    if direct.is_file():
        return direct
    hits = sorted(mirror_dir.rglob(name))
    if not hits:
        raise FileNotFoundError(f"{name} not found under {mirror_dir}")
    return hits[0]


def _load_month_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, compression="infer", low_memory=False)
    time_col = next(c for c in ("timestamp", "open_time")
                    if c in df.columns)
    ts = pd.to_numeric(df[time_col], errors="raise")
    raw = ts.astype("int64")
    mx = int(raw.max())
    if mx > 10 ** 14:            # microseconds
        secs = raw // 10 ** 6
    elif mx > 10 ** 11:          # milliseconds (Binance convention)
        secs = raw // 10 ** 3
    else:                        # seconds
        secs = raw
    out = df.assign(_ts=pd.to_datetime(secs, unit="s", utc=True)) \
        .set_index("_ts").sort_index()
    out.index.name = "timestamp"
    out = out.rename(columns={"open": "open", "high": "high",
                              "low": "low", "close": "close",
                              "volume": "volume"})
    return out[["open", "high", "low", "close", "volume"]].astype(float)


def resample_ohlc(f1m: pd.DataFrame, rule: str,
                  interval: pd.Timedelta) -> pd.DataFrame:
    """D1 convention: index = bar COMPLETION times (availability = end)."""
    agg = f1m.resample(rule).agg({"open": "first", "high": "max",
                                  "low": "min", "close": "last",
                                  "volume": "sum"})
    agg = agg.dropna(subset=["open"])
    agg.index = agg.index + interval
    return agg


def load_frames(mirror_dir: Path, year: int, months):
    paths = [_locate_month_csv(mirror_dir, year, m) for m in months]
    f1m = pd.concat([_load_month_csv(p) for p in paths]).sort_index()
    f1m = f1m[~f1m.index.duplicated(keep="first")]
    frames = {
        "4h": resample_ohlc(f1m, "4h", pd.Timedelta(hours=4)),
        "1h": resample_ohlc(f1m, "1h", pd.Timedelta(hours=1)),
        "15m": resample_ohlc(f1m, "15min", pd.Timedelta(minutes=15)),
    }
    return frames, paths


def _dep_versions() -> dict:
    out = {"python": sys.version.split()[0]}
    for pkg in ("numpy", "pandas", "pytest", "tzdata"):
        try:
            out[pkg] = importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError:
            out[pkg] = "not-installed"
    return out


def _git_head() -> str:
    try:
        import subprocess
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(HERE),
                           capture_output=True, text=True)
        return r.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def _sealed_hash() -> str:
    p = PROJECT_SRC / "trading_system" / "research" / "information_time.py"
    return _sha256_file(p) if p.is_file() else "not-found"


# --------------------------------------------------------------------- #
# modes                                                                  #
# --------------------------------------------------------------------- #
def run_at(engine: AnalysisEngine, as_of: pd.Timestamp,
           out_dir: Path) -> dict:
    rec = engine.analyze(as_of)
    payload = rec.to_record()
    (out_dir / "analysis_single_v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str))
    explanation = rec.to_explanation()
    (out_dir / "analysis_single_explanation_v1.txt").write_text(
        explanation)
    return {"record": payload, "explanation": explanation}


def run_replay(engine: AnalysisEngine, boundaries, out_dir: Path,
               snapshot_path: Path, do_snapshot: bool) -> dict:
    jl = out_dir / "analysis_results_v1.jsonl"
    md = out_dir / "analysis_explanation_v1.md"
    states: dict = {}
    t0 = time.time()
    with open(jl, "w", encoding="utf-8") as jf, \
            open(md, "w", encoding="utf-8") as mf:
        mf.write("# Contextual market-analysis engine V1 — replay\n\n")
        mf.write("Analytical lifecycle records only.  selection_quality = "
                 "NOT_ESTABLISHED.  Not trading signals; no probabilities; "
                 "no accuracy claim.\n\n")
        for i, bnd in enumerate(boundaries, 1):
            rec = engine.analyze(bnd)
            row = rec.to_record()
            jf.write(json.dumps(row, sort_keys=True, default=str) + "\n")
            mf.write(rec.to_explanation() + "\n\n---\n\n")
            st = rec.lifecycle_state
            states[st] = states.get(st, 0) + 1
            mode = "R" if rec.observation_mode == "reconstructed" else "L"
            n_fc = len(rec.forecasts)
            ref = rec.reference_status.get("selected") or \
                rec.reference_status.get("status", "?")
            print(f"[{i}/{len(boundaries)}] {rec.as_of_time} [{mode}] "
                  f"{st:32s} forecasts={n_fc} ref={ref}",
                  flush=True)
    elapsed = time.time() - t0
    if do_snapshot:
        snapshot_path.write_text(
            json.dumps(engine.snapshot_state(), indent=2, default=str))
    return {"boundaries": len(boundaries), "states": states,
            "elapsed_s": round(elapsed, 1),
            "snapshot": str(snapshot_path) if do_snapshot else None}


# --------------------------------------------------------------------- #
# main                                                                   #
# --------------------------------------------------------------------- #
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mirror-dir", required=True)
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--months", default="8,9")
    ap.add_argument("--at", default=None,
                    help="single as-of (ISO 8601, UTC)")
    ap.add_argument("--replay", action="store_true")
    ap.add_argument("--from", dest="t_from", default=None)
    ap.add_argument("--to", dest="t_to", default=None)
    ap.add_argument("--boundary-days", type=int, default=1)
    ap.add_argument("--k", type=int, default=5,
                    help="F-K confirmation parameter (research config)")
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--snapshot-out", default=None)
    ap.add_argument("--snapshot-in", default=None)
    args = ap.parse_args(argv)

    if not args.at and not args.replay:
        ap.error("choose --at or --replay")

    mirror_dir = Path(args.mirror_dir)
    months = [int(m) for m in args.months.split(",")]
    out_dir = Path(args.out_dir or (HERE / "run_artifacts"))
    out_dir.mkdir(parents=True, exist_ok=True)

    print("== loading 1m mirror ==", flush=True)
    frames, csv_paths = load_frames(mirror_dir, args.year, months)
    input_hashes = {p.name: _sha256_file(p) for p in csv_paths}
    print(f"   4h bars: {len(frames['4h'])}, "
          f"1h: {len(frames['1h'])}, 15m: {len(frames['15m'])}",
          flush=True)

    ledger = InterpretationLedger()
    engine = AnalysisEngine(
        run_id="analysis-v1", frames=frames, k=args.k,
        instrument="BTCUSDT", ledger=ledger)
    if args.snapshot_in:
        engine._load_snapshot(args.snapshot_in)
        print(f"== resumed from snapshot {args.snapshot_in} "
              f"(boundary {engine.snapshot_boundary}) ==", flush=True)

    if args.at:
        as_of = pd.Timestamp(args.at)
        if as_of.tzinfo is None:
            as_of = as_of.tz_localize("UTC")
        result = run_at(engine, as_of, out_dir)
        print(result["explanation"], flush=True)
        meta = {"mode": "at", "as_of": str(as_of)}
    else:
        if not args.t_from or not args.t_to:
            ap.error("--replay needs --from and --to")
        t_from = pd.Timestamp(args.t_from)
        t_to = pd.Timestamp(args.t_to)
        if t_from.tzinfo is None:
            t_from = t_from.tz_localize("UTC")
        if t_to.tzinfo is None:
            t_to = t_to.tz_localize("UTC")
        grid = frames["4h"].index
        boundaries = [ts for ts in pd.date_range(
            t_from.normalize(), t_to, freq=f"{args.boundary_days}D",
            tz="UTC") if ts in grid and t_from <= ts <= t_to]
        if not boundaries:
            print("no boundary on the 4h completion grid in range",
                  flush=True)
            return 1
        print(f"== replay: {len(boundaries)} boundaries "
              f"{boundaries[0]} .. {boundaries[-1]} ==", flush=True)
        result = run_replay(engine, boundaries, out_dir,
                            out_dir / "analysis_snapshot_v1.json",
                            args.snapshot_out is not None or True)
        meta = {"mode": "replay", "from": str(t_from),
                "to": str(t_to), **result}

    manifest = {
        "artifact": "contextual-market-analysis-v1",
        "run": meta,
        "config": {
            "k": args.k, "task_scale": "4h", "fine_scale": "1h",
            "finest_scale": "15m", "instrument": "BTCUSDT",
            "role": AnalysisEngine.TASK_ROLE,
            "policy_id": AnalysisEngine.POLICY_ID,
            "policy_kind": "research_configuration (NOT owner-approved)",
        },
        "selection_quality": "NOT_ESTABLISHED",
        "claims": {
            "engine_identity": "analytical lifecycle over existing "
                               "approved components; NOT Michael "
                               "Huddleston; no accuracy claim",
            "methodological_direction": "Michael Huddleston's publicly "
                                        "documented work; only verified "
                                        "material is attributed",
        },
        "provenance": {
            "dataset_commit": DATASET_COMMIT,
            "dataset_mirror": DATASET_MIRROR,
            "input_sha256": input_hashes,
            "expected_sha256": INPUT_SHA256,
            "hashes_match_expected": {
                k: input_hashes.get(k) == v
                for k, v in INPUT_SHA256.items()},
            "final_source_commit": _git_head(),
            "sealed_information_time_sha256": _sealed_hash(),
            "dependency_versions": _dep_versions(),
        },
    }
    (out_dir / "analysis_manifest_v1.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, default=str))
    print(f"== wrote {out_dir}/analysis_manifest_v1.json ==", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
