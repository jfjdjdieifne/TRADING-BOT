#!/usr/bin/env python
"""Market run V1 — expert-grounded contextual selection on real BTCUSDT data.

CONTROLLED IMPLEMENTATION (task §10).  Chronological information-time replay
of STRUCTURAL_REFERENCE_SELECTION over real historical OHLC, consuming the
EXISTING CSM kernel (fk_turning_points/build_legs generators, SP-01/SP-13
gates, SP-03 bindings, SharedInformationAxis over the CLOSED 6.2A-0
information-time contract) and the expert judgment layer
(``contextual_selection.expert_selection``).

Research only.  No trading recommendation.  No live execution.  Selection
counts do NOT prove selection correctness; zero temporal violations does NOT
prove contextual selection quality (task §10 closing prohibitions).

Input: the BTCUSDT 1m mirror used by the prior definitive run
(parshant231234-eng/BTCUSDT-Historical-Data @ 27c9be70), resampled to 1h
coarse bars with COMPLETION-time indices (the D1 convention of
experiment_contextual_selection_v2).  Window defaults to the prior run's
window (2025-08-01 .. 2025-09-27) so universes are comparable.

Two task modes per boundary (task §5-§7):
  M1 role-declared : role policy Pi_T registered (KIND_RESEARCH) — the
                     documented SWS-02 operational definition;
  M2 preference    : same role without Pi_T (kernel reports MP) — the expert
                     layer attempts resolution by documented conditional
                     preferences, else stays UNRESOLVED.

Outputs (out-dir):
  run_report_v1.json        — §10 metrics and provenance
  selection_records_v1.jsonl — every selection record (both modes)
  candidate_rows_v1.jsonl.gz — coverage-evidence rows (one per candidate
                               per boundary, candidate_record contract)

Usage:
  python run_expert_selection_market_v1.py \
      --mirror-dir /home/user/work/data/btc/mirror \
      --out-dir <this dir>/run_artifacts
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

import pandas as pd

DEFAULT_SRC = str(Path(__file__).resolve().parents[3] / "src")
if DEFAULT_SRC not in sys.path:
    sys.path.insert(0, DEFAULT_SRC)

from trading_system.research.contextual_selection import (  # noqa: E402
    KIND_RESEARCH,
    ContextualRelationships,
    PolicyRegistry,
    Representation,
    SharedInformationAxis,
    build_legs,
    candidate_record,
    expert_structural_reference_selection,
    fk_turning_points,
    sp03_binding,
)


def _sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _git_head() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"],
                             capture_output=True, text=True, timeout=30,
                             cwd=str(Path(__file__).resolve().parents[5]))
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def load_1m(mirror: Path, months: str, start: str, end: str) -> pd.DataFrame:
    frames = []
    for m in months.split(","):
        f = pd.read_csv(mirror / f"BTCUSDT_1m_{m.strip()}.csv",
                        usecols=["datetime_utc", "open", "high", "low",
                                 "close", "volume"])
        frames.append(f)
    f = pd.concat(frames, ignore_index=True)
    f["dt"] = pd.to_datetime(f["datetime_utc"])
    f = f[(f["dt"] >= start) & (f["dt"] < end)]
    return f.set_index("dt").sort_index()


def resample_ohlc(f1m: pd.DataFrame, rule: str,
                  interval: pd.Timedelta) -> pd.DataFrame:
    agg = f1m.resample(rule).agg({"open": "first", "high": "max",
                                  "low": "min", "close": "last",
                                  "volume": "sum"})
    agg = agg.dropna(subset=["open"])
    # D1: index = bar COMPLETION times (availability = bar end)
    agg.index = agg.index + interval
    return agg


def derive_test_history(pts, bars: pd.DataFrame, decision_bar: int
                        ) -> ContextualRelationships:
    """F-class relationship evidence over exact bar arithmetic.

    For every candidate knowable at the decision, scan the bars in
    [knowable_bar, decision_bar] (its own future must not pre-date its
    knowability):
      * wick-range touch : level inside [low, high] (exact interval
        containment — no tolerance, no invented threshold);
      * close crossing   : the EXISTING SP-03 procedure (sp03_binding) on the
        break side (side='high' -> upward close; 'low' -> downward close).

    An OBSERVED empty list means "observed, no tests"; a missing key means
    "not observable".  Every candidate known at the decision is observed.
    """
    rel = ContextualRelationships()
    n = decision_bar + 1
    lows = bars["low"].to_numpy()
    highs = bars["high"].to_numpy()
    closes = bars["close"].to_numpy()
    for p in pts:
        if p.knowable_bar > decision_bar:
            continue                      # not knowable: not observable yet
        events = []
        j0 = max(p.knowable_bar, 0)
        for j in range(j0, n):
            if lows[j] <= p.level <= highs[j]:
                events.append({"bar": int(j), "kind": "wick-range-touch",
                               "ref": "F:interval-containment"})
            side = "up" if p.side == "high" else "down"
            if sp03_binding(float(closes[j]), [p], side):
                events.append({"bar": int(j), "kind": "close-crossing",
                               "ref": "R:SP-03"})
        rel.test_history[p.candidate_id] = events
    return rel


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mirror-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--months", default="2025-08,2025-09")
    ap.add_argument("--start", default="2025-08-01 00:00:00")
    ap.add_argument("--end", default="2025-09-27 00:00:00")
    ap.add_argument("--k", type=int, default=5)
    args = ap.parse_args()

    mirror = Path(args.mirror_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    t_start = time.perf_counter()

    print("[1/6] loading 1m mirror ...", flush=True)
    f1m = load_1m(mirror, args.months, args.start, args.end)
    bars = resample_ohlc(f1m, "1h", pd.Timedelta(hours=1))
    print(f"      1m rows={len(f1m)} -> 1h bars={len(bars)} "
          f"({bars.index[0]} .. {bars.index[-1]})", flush=True)

    rep = Representation(family="F-K", view_id="C", scale_label="coarse",
                         params=(("k", float(args.k)),))
    axis = SharedInformationAxis("BTCUSDT_1h_utc_completion", bars.index)
    pol = PolicyRegistry()
    pol.register("P-ORIGIN-RESEARCH",
                 "role semantics: origin of the most recent confirmed leg "
                 "(SWS-02; research configuration, never owner-approved)",
                 "origin-of-last-confirmed-leg", kind=KIND_RESEARCH)

    # daily boundaries on the completion grid, from the first full day
    boundaries = [ts for ts in pd.date_range(bars.index[0].normalize(),
                                             bars.index[-1],
                                             freq="1D")
                  if ts in set(bars.index) and ts > bars.index[args.k + 2]]
    print(f"[2/6] axis rows={axis.n_rows} rep={rep.rep_id} "
          f"boundaries={len(boundaries)}", flush=True)

    run_id = "EXPERT-SEL-MARKET-V1"
    sel_records = []
    candidate_rows = []
    reason_hist: Counter = Counter()
    pref_hist: Counter = Counter()
    inactive_hist: Counter = Counter()
    source_hist: Counter = Counter()
    conflict_hist: Counter = Counter()
    temporal_violations = []
    revision_events = []
    replay_checks = []
    per_boundary_ms = []
    prev_selected = None
    n_status_transitions = 0

    print("[3/6] chronological information-time replay ...", flush=True)
    for bi, B in enumerate(boundaries):
        t0 = time.perf_counter()
        decision_bar = int(bars.index.get_loc(B))          # last completed bar
        bars_t = bars.iloc[: decision_bar + 1]
        pts = fk_turning_points(bars_t, args.k, rep, id_prefix="",
                                axis=axis)
        amb: list = []
        legs = build_legs(pts, rep, ambiguities=amb)
        for p in pts:
            n_status_transitions += len(p.status_transitions)

        rel = derive_test_history(pts, bars_t, decision_bar)

        modes = {
            "M1_role": dict(role="origin-of-last-confirmed-leg",
                            policy_id="P-ORIGIN-RESEARCH"),
            "M2_preference": dict(role="origin-of-last-confirmed-leg",
                                  policy_id=None),
        }
        expert_selections = {}
        for mode, kw in modes.items():
            sel = expert_structural_reference_selection(
                points=pts, legs=legs, decision_bar=decision_bar, rep=rep,
                policy=pol, decision_time=B, axis=axis, relationships=rel,
                **kw)
            expert_selections[mode] = sel
            rec = sel.to_record()
            rec["mode"] = mode
            rec["boundary"] = str(B)
            sel_records.append(rec)
            if sel.reason is not None:
                reason_hist[f"{mode}:{sel.reason['code']}"] += 1
            for a in sel.activated_preferences:
                pref_hist[f"{mode}:{a['pref_id']}"] += 1
            for i in sel.inactive_preferences:
                inactive_hist[i["pref_id"]] += 1
            for c in sel.conflicts:
                conflict_hist[f"{mode}:{c['kind']}"] += 1
            for e in sel.evidence:
                source_hist[e.source_ref.split(":")[0]] += 1
            # independent temporal check (report item: temporal violations)
            if sel.candidate_id is not None:
                cand = next(p for p in pts
                            if p.candidate_id == sel.candidate_id)
                ok_bar = cand.knowable_bar <= decision_bar
                ok_time = (cand.knowable_time is None
                           or axis.available(cand.knowable_time, B))
                if not (ok_bar and ok_time):
                    temporal_violations.append(
                        {"boundary": str(B), "mode": mode,
                         "candidate": sel.candidate_id})
            if mode == "M1_role":
                if prev_selected is not None and \
                        sel.candidate_id != prev_selected:
                    revision_events.append(
                        {"boundary": str(B), "from": prev_selected,
                         "to": sel.candidate_id})
                prev_selected = sel.candidate_id

        # coverage-evidence rows (M2: the expert run)
        sel_m2 = expert_selections["M2_preference"]
        surv = set(sel_m2.base_result.survivors)
        excl = {x.candidate_id: x for x in sel_m2.excluded}
        for p in pts:
            ex = excl.get(p.candidate_id)
            candidate_rows.append(candidate_record(
                p, task_id="T-S1", run_id=run_id, boundary=str(B),
                decision_bar=decision_bar, decision_time=B,
                eligible=p.candidate_id in surv, exclusion=ex,
                selected=(sel_m2.candidate_id == p.candidate_id),
                unresolved_reason=(sel_m2.reason or {}).get("code"),
                task_detail={"mode": "M2_preference",
                             "test_events": len(
                                 rel.test_history.get(p.candidate_id, ()))}))

        ms = (time.perf_counter() - t0) * 1000.0
        per_boundary_ms.append(ms)
        if (bi + 1) % 10 == 0:
            print(f"      boundary {bi + 1}/{len(boundaries)} "
                  f"({B}) {ms:.0f} ms", flush=True)

    print("[4/6] replay-determinism checks ...", flush=True)
    for B in boundaries[:: max(1, len(boundaries) // 3)][:3]:
        decision_bar = int(bars.index.get_loc(B))
        bars_t = bars.iloc[: decision_bar + 1]
        runs = []
        for _ in range(2):
            pts = fk_turning_points(bars_t, args.k, rep, id_prefix="",
                                    axis=axis)
            legs = build_legs(pts, rep)
            rel = derive_test_history(pts, bars_t, decision_bar)
            sel = expert_structural_reference_selection(
                points=pts, legs=legs, decision_bar=decision_bar, rep=rep,
                policy=pol, decision_time=B, axis=axis, relationships=rel,
                role="origin-of-last-confirmed-leg", policy_id=None)
            runs.append(json.dumps(sel.to_record(), sort_keys=True,
                                   default=str))
        replay_checks.append({"boundary": str(B), "identical":
                              runs[0] == runs[1]})

    print("[5/6] writing artifacts ...", flush=True)
    selections_path = out_dir / "selection_records_v1.jsonl.gz"
    with gzip.open(selections_path, "wt") as fh:
        for rec in sel_records:
            fh.write(json.dumps(rec, default=str) + "\n")
    rows_path = out_dir / "candidate_rows_v1.jsonl.gz"
    with gzip.open(rows_path, "wt") as fh:
        for row in candidate_rows:
            fh.write(json.dumps(row, default=str) + "\n")

    total_ms = (time.perf_counter() - t_start) * 1000.0
    n_m1_sel = sum(1 for r in sel_records
                   if r["mode"] == "M1_role" and r["outcome"] == "SELECTED")
    n_m2_sel = sum(1 for r in sel_records
                   if r["mode"] == "M2_preference"
                   and r["outcome"] == "SELECTED")
    report = {
        "experiment_id": run_id,
        "supersedes": None,
        "research_only": ("selection counts do not prove selection "
                          "correctness; zero temporal violations does not "
                          "prove contextual selection quality"),
        "source_version": {
            "git_head": _git_head(),
            "information_time_sha256": _sha256_file(
                Path(DEFAULT_SRC) / "trading_system" / "research"
                / "information_time.py"),
            "expert_selection_sha256": _sha256_file(
                Path(DEFAULT_SRC) / "trading_system" / "research"
                / "contextual_selection" / "expert_selection.py"),
            "csm_sha256": _sha256_file(
                Path(DEFAULT_SRC) / "trading_system" / "research"
                / "contextual_selection" / "csm.py"),
        },
        "inputs": {
            "mirror": f"parshant231234-eng/BTCUSDT-Historical-Data@27c9be70",
            "mirror_dir": str(mirror),
            "months": args.months,
            "window": [args.start, args.end],
            "resample": "1h (completion-time index, D1 convention)",
            "n_1m_rows": int(len(f1m)),
            "n_1h_bars": int(len(bars)),
        },
        "representation": rep.rep_id,
        "knowledge_ids": ["KP-01", "KP-02", "KP-03", "KP-04", "KP-05",
                          "KP-06", "KP-07"],
        "policy_registry": {pid: pol.get(pid) for pid, _ in
                            [(p, None) for p in ("P-ORIGIN-RESEARCH",)]},
        "summary": {
            "n_boundaries": len(boundaries),
            "total_selection_opportunities": len(sel_records),
            "n_candidate_rows": len(candidate_rows),
            "n_candidates_per_boundary_avg": (
                len(candidate_rows) / max(1, len(boundaries))),
            "actual_selections": {"M1_role": n_m1_sel,
                                  "M2_preference": n_m2_sel},
            "unresolved": dict(reason_hist),
            "preference_rules_activated": dict(pref_hist),
            "preference_inactive_reasons": dict(inactive_hist),
            "conflicts": dict(conflict_hist),
            "source_provenance_evidence_counts": dict(source_hist),
            "temporal_violations": {
                "n": len(temporal_violations),
                "cases": temporal_violations[:20]},
            "revision_behavior": {
                "n_status_transitions_generated": n_status_transitions,
                "n_reference_changes_M1": len(revision_events),
                "events": revision_events[:40]},
            "replay_determinism": replay_checks,
            "runtime": {
                "per_boundary_ms_avg": sum(per_boundary_ms)
                / max(1, len(per_boundary_ms)),
                "per_boundary_ms_max": max(per_boundary_ms or [0.0]),
                "total_s": total_ms / 1000.0},
            "same_bar_ambiguities": len(amb),
        },
        "limitations": [
            "research configuration (P-ORIGIN-RESEARCH) is never an "
            "owner-approved analytical policy (kind=research_configuration)",
            "one coarse view (1h F-K k=5) and one representation family in "
            "this run; representation dependence (W9) reported by the test "
            "suite, not re-run here",
            "fine view / cross-scale selection omitted (single selection "
            "task scope)",
            "test-history evidence derived by exact interval containment + "
            "SP-03 close crossings; no tolerance thresholds were invented",
            "no outcome evaluation: selection quality remains "
            "NOT_ESTABLISHED (objective C quarantine)",
            "cluster/round-number markers (KP-06) not observable in this "
            "generator output — preference inactive by contract",
        ],
    }
    with open(out_dir / "run_report_v1.json", "w") as fh:
        json.dump(report, fh, indent=2, default=str)

    print("[6/6] summary", flush=True)
    print(json.dumps(report["summary"], indent=2, default=str))
    print(f"total runtime {total_ms/1000.0:.1f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
