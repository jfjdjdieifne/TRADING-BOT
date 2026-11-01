#!/usr/bin/env python3
"""Contextual decision layer V1 — local runner (task scope).

Produces ONE contextual decision per valid as-of snapshot over real
BTCUSDT data: a primary working interpretation, one explicit analytical
state (SCENARIO_DEVELOPING | AWAITING_EVENT | EVENT_OCCURRED |
PRIOR_VIEW_WEAKENED_OR_INVALIDATED | NO_EDGE | UNRESOLVED), and a concise
explanation (why / opposed / what would change it).

Decision method: a local context-conditioned event-frequency model over
chronological historical episodes (predefined observable events with
operational SP-03 detectors).  Labels come only from the future (training
and evaluation); they never enter features, analysis, or forecasts at the
earlier as-of.  No trade-profit/loss labels exist in this path.  The
ranking is PROVISIONAL and UNVALIDATED (probabilities are not emitted —
not calibrated); the output is NOT ready for trade execution.

  selection_quality = NOT_ESTABLISHED

Modes
-----
--at ISO     one decision as of a single time -> JSON + explanation
--run        chronological run: decisions JSONL + explanations +
             out-of-sample evaluation + provenance manifest

Example
-------
  python run_contextual_decision_v1.py --run \
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
)
from trading_system.research.contextual_selection.decision_layer import (  # noqa: E402
    DECISION_STATES,
    EPISODE_HORIZON_BARS,
    EVENT_DEFINITIONS,
    EVENTS,
    RUN_CONTEXT_REPLAY,
    ContextEventModel,
    EpisodeExtractor,
    chronological_split,
    decide,
    evaluate_model,
    summarize_decisions,
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
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--months", default="8,9")
    ap.add_argument("--at", default=None)
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--from", dest="t_from", default="2025-08-01")
    ap.add_argument("--to", dest="t_to", default="2025-09-30")
    ap.add_argument("--boundary-days", type=int, default=1)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--horizon-bars", type=int,
                    default=EPISODE_HORIZON_BARS)
    ap.add_argument("--train-fraction", type=float, default=2 / 3)
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args(argv)

    if not args.at and not args.run:
        ap.error("choose --at or --run")

    mirror_dir = Path(args.mirror_dir)
    months = [int(m) for m in args.months.split(",")]
    out_dir = Path(args.out_dir or (HERE / "run_artifacts"))
    out_dir.mkdir(parents=True, exist_ok=True)

    print("== loading 1m mirror ==", flush=True)
    frames, csv_paths = AN.load_frames(mirror_dir, args.year, months)
    input_hashes = {p.name: AN._sha256_file(p) for p in csv_paths}
    print(f"   4h bars: {len(frames['4h'])}, 1h: {len(frames['1h'])}, "
          f"15m: {len(frames['15m'])}", flush=True)

    # boundaries on the 4h completion grid
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
    if args.at:
        at = pd.Timestamp(args.at)
        if at.tzinfo is None:
            at = at.tz_localize("UTC")
        boundaries = [b for b in boundaries if b < at] + [at]
    if not boundaries:
        print("no boundary on the 4h completion grid in range", flush=True)
        return 1

    # ---- analysis records (the existing lifecycle; unchanged) --------
    ledger = InterpretationLedger()
    engine = AnalysisEngine(run_id="decision-v1", frames=frames,
                            k=args.k, instrument="BTCUSDT",
                            ledger=ledger)
    extractor = EpisodeExtractor(frames=frames, k=args.k,
                                 task_scale="4h",
                                 horizon_bars=args.horizon_bars,
                                 axis=engine.axis)
    records, episodes = [], []
    t0 = time.time()
    for i, bnd in enumerate(boundaries, 1):
        rec = engine.analyze(bnd)
        ep = extractor.extract(rec, run_id="decision-v1", seq=i)
        records.append(rec)
        episodes.append(ep)
        if args.run:
            print(f"[analyze {i}/{len(boundaries)}] {rec.as_of_time} "
                  f"{rec.lifecycle_state:32s} "
                  f"episode={'labeled:' + ep.label if ep.usable else 'excluded'}",
                  flush=True)
    print(f"== {len(records)} analysis records in "
          f"{time.time() - t0:.1f}s ==", flush=True)

    # ---- decisions (expanding training window: no label ever leaks) --
    decisions = []
    for i, rec in enumerate(records):
        model = ContextEventModel()
        model.fit_before(episodes, cutoff_time=rec.as_of_time)
        d = decide(record=rec, model=model,
                   run_context=RUN_CONTEXT_REPLAY, decision_seq=i + 1)
        decisions.append(d)
    summary = summarize_decisions(decisions)

    # ---- out-of-sample evaluation (chronological; later data only) ---
    train, ev = chronological_split(episodes,
                                    train_fraction=args.train_fraction)
    eval_model = ContextEventModel()
    eval_model.fit(train)
    eval_report = evaluate_model(eval_model, ev)
    excluded = [e for e in episodes if not e.usable]

    if args.at:
        d = decisions[-1]
        (out_dir / "decision_single_v1.json").write_text(
            json.dumps(d.to_record(), indent=2, sort_keys=True,
                       default=str))
        (out_dir / "decision_single_explanation_v1.txt").write_text(
            d.to_explanation())
        print(d.to_explanation(), flush=True)
    else:
        jl = out_dir / "decisions_v1.jsonl"
        with open(jl, "w", encoding="utf-8") as fh:
            for d in decisions:
                fh.write(json.dumps(d.to_record(), sort_keys=True,
                                    default=str) + "\n")
        with open(out_dir / "decision_explanations_v1.md", "w",
                  encoding="utf-8") as fh:
            fh.write("# Contextual decision layer V1 — decisions\n\n")
            fh.write("Analytical decisions only.  selection_quality = "
                     "NOT_ESTABLISHED.  Not trading signals; no orders; "
                     "ranking provisional and unvalidated.\n\n")
            for d in decisions:
                fh.write(d.to_explanation() + "\n\n---\n\n")
        with gzip.open(out_dir / "decisions_v1.jsonl.gz", "wt",
                       encoding="utf-8") as fh:
            for d in decisions:
                fh.write(json.dumps(d.to_record(), sort_keys=True,
                                    default=str) + "\n")
        for d in decisions:
            print(f"[decide] {d.as_of_time} {d.state:38s} "
                  f"primary={d.primary_interpretation_id}"
                  f"{' (baseline)' if d.primary_is_baseline else ''}",
                  flush=True)

    eval_full = {
        "train_episodes": [e.to_record() for e in train],
        "eval_episodes": [e.to_record() for e in ev],
        "excluded_episodes": [
            {"episode_id": e.episode_id, "as_of": str(e.as_of_time),
             "reason": e.exclusion_reason} for e in excluded],
        "chronological_separation": (
            f"train as_of <= {max((e.as_of_time for e in train), default=None)}"
            f" < eval as_of >= {min((e.as_of_time for e in ev), default=None)}"),
        "evaluation": eval_report,
        "decision_summary": summary,
        "label_vocabulary": {e: EVENT_DEFINITIONS[e] for e in EVENTS},
    }
    (out_dir / "decision_eval_v1.json").write_text(
        json.dumps(eval_full, indent=2, sort_keys=True, default=str))

    manifest = {
        "artifact": "contextual-decision-layer-v1",
        "run": {"mode": "at" if args.at else "run",
                "from": str(t_from), "to": str(t_to),
                "n_boundaries": len(boundaries),
                "run_context": RUN_CONTEXT_REPLAY},
        "config": {
            "k": args.k, "task_scale": "4h",
            "episode_horizon_bars": args.horizon_bars,
            "horizon_note": "declared research configuration for bounded "
                            "episode labeling; NOT a market rule and "
                            "NOT owner-approved",
            "train_fraction": args.train_fraction,
            "model": "context-conditioned event frequency table; no "
                     "smoothing; ties explicit; ordinal ranking only",
            "events": list(EVENTS),
            "decision_states": list(DECISION_STATES),
        },
        "decision_summary": summary,
        "evaluation": eval_report,
        "selection_quality": "NOT_ESTABLISHED",
        "claims": {
            "ranking": "PROVISIONAL and UNVALIDATED (not calibrated); "
                       "probabilities are NOT emitted",
            "readiness": "NOT ready for trade execution: analytical "
                         "decisions only",
            "labels": "structural event identities only; never trade "
                      "profit/loss",
            "identity": "NOT Michael Huddleston; no replication claim; "
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
            "final_source_commit": AN._git_head(),
            "sealed_information_time_sha256": AN._sealed_hash(),
            "dependency_versions": AN._dep_versions(),
        },
    }
    (out_dir / "decision_manifest_v1.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, default=str))
    print(f"== wrote {out_dir}/decision_manifest_v1.json ==", flush=True)
    print(f"== states: {summary['states']} | NO_EDGE frequency: "
          f"{summary['no_edge_frequency']} (never counted as success) ==",
          flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
