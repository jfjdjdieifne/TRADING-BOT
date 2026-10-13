#!/usr/bin/env python
"""Real-market experiment v2: contextual selection of movement/structural
references on BTCUSDT — AUDIT-REMEDIATED rerun (research only; no trading
recommendations; no live execution).

Experiment id: CSM-SEL-EXP-V2 (repaired causal reproduction of CSM-SEL-EXP-V1)

Audit fixes exercised here:
  D1 shared information-time axis; chronological event replay — events in
     (b_{i-1}, b_i] use ONLY the reference state selected at b_{i-1}, each
     reference further filtered by its own availability time.  No raw
     cross-domain index comparison anywhere.
  D2 F-K full left context + inclusive supersession endpoint.
  D3 historical status via status_at() at every boundary/event.
  D4 same-bar/zero-amplitude ambiguities recorded, never sequenced;
     explicit versioned tie policies.
  D5 InterpretationLedger.propagate recomputes dependents from stored
     payloads at event/boundary times and records COMPUTED differences.
  D6 T-S5 direction from structural leg data (SelectionResult.direction);
     candidate-level coverage ledger serialized (not aggregate counts).
  D7/§8 policy kinds distinguished (research configuration is never
     owner-approved); record carries the ACTUAL source version used for the
     run (git head + file hashes); input/output paths configurable.

Usage (paths configurable; defaults target this builder's mirror layout):
  python experiment_contextual_selection_v2.py \\
      --mirror-dir /home/user/work/data/btc/mirror \\
      --out-dir /home/user/work/csm_v2 \\
      --old-record .../experiment_record_v1.json   # optional comparison
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

DEFAULT_SRC = str(Path(__file__).resolve().parents[3] / "src")


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


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="CSM-SEL-EXP-V2 (audit remediation)")
    ap.add_argument("--mirror-dir", type=Path,
                    default=Path("/home/user/work/data/btc/mirror"),
                    help="directory holding BTCUSDT_1m_YYYY-MM.csv month files")
    ap.add_argument("--months", default="2025-08,2025-09",
                    help="comma list of YYYY-MM month files to load")
    ap.add_argument("--start", default="2025-08-01 00:00:00")
    ap.add_argument("--end", default="2025-09-27 00:00:00")
    ap.add_argument("--out-dir", type=Path,
                    default=Path("/home/user/work/csm_v2"))
    ap.add_argument("--old-record", type=Path, default=None,
                    help="optional V1 record for old-vs-new comparison")
    ap.add_argument("--src", default=DEFAULT_SRC,
                    help="trading_project src path for the CSM kernel import")
    return ap.parse_args()


BOUNDARIES = [
    ("D1_2025-09-20", "2025-09-20 00:00:00"),
    ("D2_2025-09-22", "2025-09-22 00:00:00"),
    ("D3_2025-09-24", "2025-09-24 00:00:00"),
    ("B0_midnight_open", "2025-09-25 00:01:00"),   # SXM-005 forward clause (ICT-source)
    ("B1_post5", "2025-09-25 06:49:00"),           # SXM-005 created 06:49:22.428Z (v1)
    ("M1_2025-09-25_noon", "2025-09-25 12:00:00"),
    ("B2_post6", "2025-09-25 19:34:00"),           # SXM-006 created 19:34:06.983Z (v3)
    ("D4_2025-09-26", "2025-09-26 12:00:00"),
    ("D5_2025-09-26_end", "2025-09-26 23:00:00"),
]


def load_1m(mirror: Path, months: str, start: str, end: str) -> pd.DataFrame:
    frames = []
    for m in months.split(","):
        f = pd.read_csv(mirror / f"BTCUSDT_1m_{m.strip()}.csv",
                        usecols=["datetime_utc", "open", "high", "low", "close", "volume"])
        frames.append(f)
    f = pd.concat(frames, ignore_index=True)
    f["dt"] = pd.to_datetime(f["datetime_utc"])
    f = f[(f["dt"] >= start) & (f["dt"] < end)]
    return f.set_index("dt").sort_index()


def resample_ohlc(f1m: pd.DataFrame, rule: str, interval: pd.Timedelta) -> pd.DataFrame:
    agg = f1m.resample(rule).agg({"open": "first", "high": "max", "low": "min",
                                  "close": "last", "volume": "sum"})
    agg = agg.dropna(subset=["open"])
    # D1: shift the index to bar COMPLETION times — the shared information
    # time axis for all views (availability = bar end, never bar start).
    agg.index = agg.index + interval
    return agg


def main() -> int:
    args = parse_args()
    sys.path.insert(0, args.src)
    from trading_system.research.contextual_selection import (  # noqa: E402
        KIND_PROCEDURE, KIND_RESEARCH, KIND_SOURCE,
        InterpretationLedger, PolicyRegistry, Representation,
        SharedInformationAxis, TIE_CROSS_EQUAL_UNBOUND, TIE_FT_EQ_FIRST,
        available_at,
        build_legs, candidate_record, fk_turning_points, ft_turning_points,
        reference_state_at, same_bar_evidence_class,
        task_s1_structural_reference,
        task_s2_event_binding, task_s5_falsifier,
    )
    from trading_system.research.contextual_selection.artifacts import (  # noqa: E402
        write_run_artifacts,
    )

    out_dir: Path = args.out_dir
    # SAFE INTEGRATION V1 (audit F §"Output failure"): the run writes ONLY
    # into a clean output directory — seeded/stale artifacts are never mixed
    # with (or mistaken for) this run's outputs.
    TARGET_ARTIFACTS = ("experiment_record_v2.json",
                        "candidate_ledger_v1.jsonl.gz",
                        "propagation_log_v1.jsonl",
                        "experiment_manifest_v1.json", "REPRODUCE.md")
    out_dir.mkdir(parents=True, exist_ok=True)
    stale = [n for n in TARGET_ARTIFACTS if (out_dir / n).exists()]
    if stale:
        print(f"REFUSING: output directory {out_dir} already contains "
              f"{stale} — use a clean output directory", flush=True)
        return 2

    f1m = load_1m(args.mirror_dir, args.months, args.start, args.end)
    fC = resample_ohlc(f1m, "1h", pd.Timedelta(hours=1))
    fF = resample_ohlc(f1m, "5min", pd.Timedelta(minutes=5))
    print(f"bars: 1m={len(f1m)} 5m={len(fF)} 1h={len(fC)}", flush=True)

    # ---- shared information-time axis (CLOSED 6.2A-0 contract) ----------
    # ALL cross-timeframe comparisons are verified on ONE master timeline;
    # left context starts 2025-08-01, the evaluated event window is
    # 2025-09-20..2025-09-27 (context is never confused with evaluation).
    # consolidation V1: the axis carries TRUE bar-completion times (bar end,
    # never bar start) — matching its D1 contract and the D1..D5 boundary
    # keys (a boundary at 00:00 is the completion of the previous minute bar)
    axis = SharedInformationAxis("BTCUSDT_1m_utc_completion",
                                 f1m.index + pd.Timedelta(minutes=1))
    print(f"shared axis: {axis.timeline_id} rows={axis.n_rows}", flush=True)

    # ---- policy/provenance classification (audit §8) ---------------------
    pol = PolicyRegistry()
    pol.register("P-TF", "coarse=1h fine=5m timeframes", "1h/5m",
                 kind=KIND_RESEARCH)                    # builder research config
    pol.register("P-ORIGIN", "origin of most recent confirmed leg (SWS-02)",
                 "origin-of-last-confirmed-leg", kind=KIND_PROCEDURE)
    pol.register("P-FK-K-COARSE", "F-K window grid on coarse view", [5, 12],
                 kind=KIND_RESEARCH)
    pol.register("P-FK-K-FINE", "F-K window on fine view", [6], kind=KIND_RESEARCH)
    pol.register("P-T-TAU-FINE", "F-T reversal amount, fine view (USD)", 80.0,
                 kind=KIND_RESEARCH)
    pol.register("P-T-TAU-COARSE", "F-T reversal amount, coarse view (USD)", 250.0,
                 kind=KIND_RESEARCH)
    pol.register("P-TIE-CROSS", "close equality is not a crossing",
                 TIE_CROSS_EQUAL_UNBOUND, kind=KIND_PROCEDURE)
    pol.register("P-TIE-FT", "equal-extreme tie policy", TIE_FT_EQ_FIRST,
                 kind=KIND_RESEARCH)
    pol.register("P-SXM-TIMES", "decision boundaries B0/B1/B2 from SXM journals",
                 ["2025-09-25 00:01:00", "2025-09-25 06:49:00",
                  "2025-09-25 19:34:00"], kind=KIND_SOURCE)

    reps = {
        "C_FK5": Representation("F-K", "C", "coarse", (("k", 5.0),)),
        "C_FK12": Representation("F-K", "C", "coarse", (("k", 12.0),)),
        "C_FT250": Representation("F-T", "C", "coarse", (("tau", 250.0),)),
        "F_FK6": Representation("F-K", "F", "fine", (("k", 6.0),)),
        "F_FT80": Representation("F-T", "F", "fine", (("tau", 80.0),)),
    }

    ledger = InterpretationLedger()
    boundaries_out = []
    events_out = []
    coverage_rows = []          # candidate-level rows (audit D6/§7)
    prefix_inventory: dict = {}   # rep -> ids seen in truncated prefixes (§6)
    ambiguities_out = []
    t2_exclusions = Counter()   # final audit patch: T-S2 gate accounting
    binding_kind_counts = Counter()  # first-break vs later-interaction (A/B)
    selection_history = []      # (available_time, reference candidates) per boundary
    registered = {}             # rid -> (uid_t1, uid_s5) active payload registrations
    replay_checks = []
    prev_t = None
    prev_bname = None
    old_selections = {}         # for old-vs-new comparison

    for bname, when in BOUNDARIES:
        b_time = pd.Timestamp(when)
        row = {"boundary": bname, "decision_time_utc": when, "tasks": {}}
        fresh_refs = []          # references selected at THIS boundary (for later events)
        # versions ACTIVE during (prev boundary, this boundary]: registered
        # before this boundary's results are computed (audit D5/D1)
        registered_active = dict(registered)

        # ---- chronological event replay (D1): events since the PREVIOUS
        # boundary use the PREVIOUS boundary's selection state only ---------
        if prev_t is not None:
            fview = fF
            lo = int(fview.index.searchsorted(pd.Timestamp(prev_t), side="right") - 1)
            hi = int(fview.index.searchsorted(b_time, side="right") - 1)
            for j in range(max(lo, 0) + 1, hi + 1):
                event_time = pd.Timestamp(fview.index[j])   # 5m completion time
                c = float(fview.iloc[j]["close"])
                prev_c = float(fview.iloc[j - 1]["close"])
                refs_now = reference_state_at(selection_history, event_time)
                if not refs_now:
                    continue
                refs_by_view = {}
                for p in refs_now:
                    refs_by_view.setdefault(p.view_id, []).append(p)
                event_ref = f"{prev_bname}->{bname}:E{j}"
                ev = task_s2_event_binding(
                    j, c, refs_by_view, j, tie_bound=False, prev_close=prev_c,
                    state_id_prefix=f"{prev_bname}->{bname}:E{j}",
                    event_time=event_time,
                    # FINAL AUDIT PATCH: provisional references are admitted
                    # ONLY by this explicit contract (occurrence-visible);
                    # the csm default excludes them.  Statuses are recorded.
                    allow_provisional=True,
                    # consolidation V1: validated as-of axis + the event's
                    # own reference (PRE_EVENT_STATE reconstruction)
                    event_ref=event_ref, axis=axis)
                t2_exclusions.update(
                    f"{e.code}|{e.detail[:28]}" for e in ev.excluded)
                for _k in ev.binding_kinds.values():
                    binding_kind_counts[_k] += 1
                if ev.survivors:
                    ledger.record(ev, payload={
                        "kind": "T-S2", "event_bar": j, "close_price": c,
                        "refs_by_view": refs_by_view, "prev_close": prev_c,
                        "event_time": event_time,
                        "state_id_prefix": f"{prev_bname}->{bname}:E{j}",
                        # replay preserves ALL declared task parameters
                        # (causal-state integration V1)
                        "allow_provisional": True,
                        "tie_policy": TIE_CROSS_EQUAL_UNBOUND,
                        "event_ref": event_ref, "axis": axis})
                    ledger.record_event(
                        int(j), "binding",
                        f"close={c} time={event_time} notes={ev.notes}",
                        ev.survivors, event_time=event_time,
                        event_ref=event_ref)
                    events_out.append({
                        "boundary_interval": f"{prev_bname}->{bname}",
                        "event_bar": int(j), "event_time": str(event_time),
                        "close": c, "bound": ev.survivors,
                        "binding_kinds": dict(ev.binding_kinds),
                        # consolidation V1 (task §3): explicit event phases
                        "event_phase": ev.event_phase,
                        "notes": ev.notes,
                    })
                    # SAFE INTEGRATION V1 (audit F §"Candidate ledger"): the
                    # T-S2 event-binding candidates get their own per-task
                    # lifecycle rows (with the pre-event binding kind)
                    ex2_by_id = {}
                    for e in ev.excluded:
                        ex2_by_id.setdefault(e.candidate_id, e)
                    for p_ref in refs_now:
                        coverage_rows.append(candidate_record(
                            p_ref, task_id="T-S2",
                            run_id=f"{prev_bname}->{bname}:E{j}",
                            boundary=f"{prev_bname}->{bname}",
                            decision_bar=int(j), decision_time=event_time,
                            eligible=(p_ref.candidate_id in ev.survivors),
                            exclusion=ex2_by_id.get(p_ref.candidate_id),
                            selected=(p_ref.candidate_id == ev.selected_id),
                            task_detail={
                                "event_ref": event_ref,
                                "binding_kind": ev.binding_kinds.get(
                                    p_ref.candidate_id)}))
                    # W8-pattern REAL propagation on breaks of active refs
                    for rid, (uid, uid5) in registered_active.items():
                        # break of the ACTIVE reference (selected at prev boundary)
                        prev_sel = None
                        for p in refs_now:
                            if p.rep.rep_id == reps[rid].rep_id:
                                prev_sel = p.candidate_id
                        if prev_sel and prev_sel in ev.survivors:
                            log = ledger.propagate(
                                int(j), [prev_sel],
                                changed_states={prev_sel: "broken"},
                                update_time=event_time,
                                event_ref=event_ref, axis=axis)
                            row.setdefault("propagations", []).extend(log)


        # ---- T-S1 per representation at this boundary (D1: time axis) ----
        for rid, rep in reps.items():
            fview = fC if rep.view_id == "C" else fF
            closes = fview.index  # completion times == the index (D1 shift)
            cutoff = int(closes.searchsorted(b_time, side="right") - 1)
            bars_t = fview.iloc[: cutoff + 1]
            amb = []
            if rep.family == "F-K":
                pts = fk_turning_points(bars_t, int(rep.param("k")), rep,
                                        axis=axis)
            else:
                pts = ft_turning_points(bars_t, rep.param("tau"), rep,
                                        tie_policy=TIE_FT_EQ_FIRST,
                                        ambiguities=amb, axis=axis)
            legs = build_legs(pts, rep, ambiguities=amb)
            # consolidation V1 (task §2): regenerating candidates must NEVER
            # reset recorded lifecycle events (the audited B2 pattern) — the
            # ledger's recorded transitions are re-applied before the tasks
            led_restore = ledger.restore_history(pts, axis=axis)
            prefix_inventory.setdefault(rid, set()).update(
                p.candidate_id for p in pts)
            ambiguities_out += [{"boundary": bname, "rep": rid, **a} for a in amb]
            r = task_s1_structural_reference(
                pts, legs, cutoff, rep, "origin-of-last-confirmed-leg",
                pol, "P-ORIGIN", state_id_prefix=f"{bname}:{rid}:S1",
                decision_time=b_time, axis=axis)
            uid = ledger.record(r, payload={
                "kind": "T-S1", "points": pts, "legs": legs, "rep": rep,
                "role": "origin-of-last-confirmed-leg", "policy": pol,
                "policy_id": "P-ORIGIN", "state_id_prefix": f"{bname}:{rid}:S1",
                "decision_time": b_time, "axis": axis})
            r_ext = task_s1_structural_reference(
                pts, legs, cutoff, rep, "last-confirmed-extreme", pol, None,
                state_id_prefix=f"{bname}:{rid}:S1x", decision_time=b_time,
                axis=axis)
            uid_ext = ledger.record(r_ext, payload={
                "kind": "T-S1", "points": pts, "legs": legs, "rep": rep,
                "role": "last-confirmed-extreme", "policy": pol,
                "policy_id": None, "state_id_prefix": f"{bname}:{rid}:S1x",
                "decision_time": b_time, "axis": axis})
            by_id = {p.candidate_id: p for p in pts}
            row["tasks"][rid] = {
                "T-S1_origin": {
                    "status": r.status,
                    "selected": r.selected_id,
                    "direction": r.direction,
                    "survivors": r.survivors,
                    "n_excluded": len(r.excluded),
                    "excluded_codes": dict(Counter(e.code for e in r.excluded)),
                    "notes": r.notes,
                    "policy_refs": list(r.policy_refs),
                    "unresolved": (None if r.unresolved is None else {
                        "reason_code": r.unresolved.reason_code,
                        "evidence_needed": r.unresolved.evidence_needed}),
                },
                # consolidation V1 (task §6): survivors + reasons serialized
                # for EVERY task variant (not just status/selected)
                "T-S1_extreme": {
                    "status": r_ext.status,
                    "selected": r_ext.selected_id,
                    "survivors": r_ext.survivors,
                    "reason": (r_ext.unresolved.reason_code
                               if r_ext.unresolved else None),
                    "evidence_needed": (r_ext.unresolved.evidence_needed
                                        if r_ext.unresolved else None),
                    "notes": r_ext.notes,
                    "policy_refs": list(r_ext.policy_refs),
                },
                "n_points": len(pts),
                "n_legs": len(legs),
                "restored_transitions": led_restore,
                "unresolved_codes": [r.unresolved.reason_code] if r.unresolved else [],
            }
            old_selections.setdefault(bname, {})[rid] = r.selected_id

            # ---- T-S5 falsifier (D6: direction from structural data) ------
            direction = r.direction
            claims = [{"interpretation": f"I:{rid}:{bname}", "view": rep.view_id,
                       "role": "origin-of-last-confirmed-leg",
                       "direction": direction}]
            r5 = task_s5_falsifier(claims, pts, legs, cutoff,
                                   state_id_prefix=f"{bname}:{rid}:S5",
                                   decision_time=b_time, axis=axis)
            uid5 = ledger.record(r5, payload={
                "kind": "T-S5", "claims": claims, "points": pts, "legs": legs,
                "state_id_prefix": f"{bname}:{rid}:S5",
                "decision_time": b_time, "axis": axis})
            row["tasks"][rid]["T-S5"] = {
                "status": r5.status,
                "falsifier": r5.survivors,
                "survivors": r5.survivors,
                "direction_used": direction,
                "reason": (r5.unresolved.reason_code if r5.unresolved else None),
                "evidence_needed": (r5.unresolved.evidence_needed
                                    if r5.unresolved else None),
                "notes": r5.notes,
                "policy_refs": list(r5.policy_refs),
            }
            registered[rid] = (uid, uid5)

            # ---- candidate-level coverage rows (D6/§7) --------------------
            # SAFE INTEGRATION V1 (audit F §"Candidate ledger"): one row per
            # candidate PER TASK VARIANT — T-S1 origin AND T-S1 extreme,
            # T-S2 event-binding refs (in the event loop), and T-S5 support
            # legs with LEG-level classification (a leg id is NEVER compared
            # against T-S5 point survivor ids).
            def _rows_for(task, objs, res, b_bar, b_t):
                ex_by = {}
                for e in res.excluded:
                    ex_by.setdefault(e.candidate_id, e)
                for o in objs:
                    oid = getattr(o, "candidate_id", None) or o.leg_id
                    coverage_rows.append(candidate_record(
                        o, task_id=task, run_id=f"{bname}:{rid}",
                        boundary=bname, decision_bar=b_bar, decision_time=b_t,
                        eligible=(oid in res.survivors),
                        exclusion=ex_by.get(oid),
                        selected=(oid == res.selected_id),
                        unresolved_reason=(res.unresolved.reason_code
                                           if res.unresolved else None)))
            _rows_for("T-S1_origin", pts, r, cutoff, b_time)
            _rows_for("T-S1_extreme", pts, r_ext, cutoff, b_time)
            ex5_by_id = {}
            for e in r5.excluded:
                ex5_by_id.setdefault(e.candidate_id, e)
            support = set(r5.dependencies)   # resolved supports (pts + legs)
            for l in legs:
                # LEG-level eligibility: evaluated support iff completed and
                # decision-time-available; r5.survivors are POINT ids and
                # never define leg eligibility (audit F)
                leg_eval = l.completed and available_at(
                    l, as_of_bar=cutoff, as_of_time=b_time, axis=axis)
                ex = ex5_by_id.get(l.leg_id)
                coverage_rows.append(candidate_record(
                    l, task_id="T-S5_support", run_id=f"{bname}:{rid}",
                    boundary=bname, decision_bar=cutoff, decision_time=b_time,
                    eligible=(leg_eval and ex is None),
                    exclusion=ex,
                    selected=(l.leg_id in support),
                    unresolved_reason=(r5.unresolved.reason_code
                                       if r5.unresolved else None),
                    task_detail={"support_of_falsifier": l.leg_id in support,
                                 "evaluated_support": leg_eval}))
            if r.selected_id and r.selected_id in by_id:
                fresh_refs.append(by_id[r.selected_id])

        # ---- boundary-time propagation (D5): dependents registered at
        # earlier boundaries recompute with the information knowable at THIS
        # boundary; computed differences are recorded by the ledger ---------
        for rid, (uid, uid5) in registered.items():
            rep = reps[rid]
            fview = fC if rep.view_id == "C" else fF
            cutoff_b = int(fview.index.searchsorted(b_time, side="right") - 1)
            sel_id = row["tasks"][rid]["T-S1_origin"]["selected"]
            changed_ids = [x for x in (sel_id,) if x]
            if changed_ids:
                log = ledger.propagate(cutoff_b, changed_ids,
                                       update_time=b_time, axis=axis)
                row.setdefault("boundary_propagations", []).extend(log)

        # ---- SP-16 representation-dependence report ----------------------
        origins = {rid: row["tasks"][rid]["T-S1_origin"]["selected"]
                   for rid in ("C_FK5", "C_FK12", "C_FT250")}
        agree = len(set(v.split("|")[1] if v and "|" in v else v
                        for v in origins.values())) <= 1
        row["representation_report_SP16"] = {
            "coarse_origins": origins,
            "agreement": "agree" if agree else "disagree",
            "note": "disagreement is reported, never merged (SWS-01)",
        }
        boundaries_out.append(row)

        # selection history for later events (D1 chronological replay):
        # the state produced at THIS boundary becomes available AT this time
        selection_history.append((b_time, list(fresh_refs)))

        # ---- replay consistency (SWS-04d) on two sample boundaries ------
        if bname in ("B1_post5", "B2_post6"):
            for rid in ("C_FK5", "F_FK6"):
                rep = reps[rid]
                fview = fC if rep.view_id == "C" else fF
                cutoff2 = int(fview.index.searchsorted(b_time, side="right") - 1)
                bars_t = fview.iloc[: cutoff2 + 1]
                pts2 = (fk_turning_points(bars_t, int(rep.param("k")), rep,
                                          axis=axis)
                        if rep.family == "F-K" else
                        ft_turning_points(bars_t, rep.param("tau"), rep,
                                          axis=axis))
                legs2 = build_legs(pts2, rep)
                ledger.restore_history(pts2, axis=axis)   # replay keeps recorded lifecycle
                r2 = task_s1_structural_reference(
                    pts2, legs2, cutoff2, rep, "origin-of-last-confirmed-leg",
                    pol, "P-ORIGIN", decision_time=b_time, axis=axis)
                same = r2.selected_id == row["tasks"][rid]["T-S1_origin"]["selected"]
                replay_checks.append({
                    "boundary": bname, "rep": rid, "recomputed": r2.selected_id,
                    "stored": row["tasks"][rid]["T-S1_origin"]["selected"],
                    "equal": same})

        prev_t = when
        prev_bname = bname
        print(f"[{bname}] " + " ".join(
            f"{rid}={row['tasks'][rid]['T-S1_origin']['selected']}"
            for rid in reps), flush=True)

    # ---- candidate ledger (D6/§7) ---------------------------------------
    # SAFE INTEGRATION V1: serialization is STAGED and committed atomically
    # at the end (write_run_artifacts) — a failure never leaves a truncated
    # gzip beside stale files.
    print(f"candidate ledger rows: {len(coverage_rows)} (staged)", flush=True)

    # ---- old-vs-new comparison (§9) -------------------------------------
    comparison = None
    # new-run self-check ALWAYS runs (acceptance criterion 1): zero tolerated
    # future-reference use — every binding verified on the shared axis
    knowable_by_id = {rrow["candidate_id"]: rrow["knowable_time"]
                      for rrow in coverage_rows if rrow["knowable_time"]}
    new_violations = []
    axis_verified = 0
    for e in events_out:
        et = pd.Timestamp(e["event_time"])
        for cid in e.get("bound", []):
            kt = knowable_by_id.get(cid)
            # CAUSAL-STATE INTEGRATION V1: the availability claim is
            # verified on the shared InformationKey axis (one market
            # event = one information-time identity)
            if axis.available(kt, et):
                axis_verified += 1
            else:
                new_violations.append({"event_time": str(et), "bound": cid,
                                       "knowable": str(kt)})
    if args.old_record and args.old_record.exists():
        old = json.load(open(args.old_record))
        old_events = old.get("binding_events", [])
        old_revs = old.get("propagation_log", [])
        # reproduce the auditor's future-reference counterexamples on the
        # OLD events with the NEW availability axis: rebuild id -> knowable
        # time from the regenerated candidates (id scheme is stable).
        contaminated, contam_events = [], set()
        unmatched_old_ids = 0
        for e in old_events:
            et = pd.Timestamp(e.get("close_time") or e.get("event_time"))
            for cid in e.get("bound", []):
                kt = knowable_by_id.get(cid)
                if kt is None:
                    unmatched_old_ids += 1
                if kt is not None and pd.Timestamp(kt) > et:
                    contaminated.append({
                        "old_event_time": str(et), "bound": cid,
                        "knowable_time": kt,
                        "finding": "reference unavailable at event time (D1)"})
                    contam_events.add(str(et))
        # later-boundary-selection contamination (root cause #2): old events
        # were scanned with the selection computed at the CURRENT (later)
        # boundary.  Key the selections by the rep id embedded in each
        # selected candidate id.
        sel_map = {}
        for b in old.get("boundaries", []):
            m = {}
            for rid, v in b.get("tasks", {}).items():
                if isinstance(v, dict) and "T-S1_origin" in v:
                    s = v["T-S1_origin"].get("selected")
                    if s:
                        m[s.split("|")[0]] = s
            sel_map[b["boundary"]] = m
        border = [b["boundary"] for b in old.get("boundaries", [])]
        later_sel, later_events = [], set()
        for e in old_events:
            cur = e.get("boundary")
            if cur is None and e.get("boundary_interval"):
                cur = e["boundary_interval"].split("->")[-1]
            if cur not in border:
                continue
            i = border.index(cur)
            prev_b = border[i - 1] if i else None
            for cid in e.get("bound", []):
                rep_of = cid.split("|")[0]
                if (sel_map.get(cur, {}).get(rep_of) == cid
                        and sel_map.get(prev_b, {}).get(rep_of) != cid):
                    later_sel.append({
                        "old_event_time": (e.get("close_time")
                                           or e.get("event_time")),
                        "bound": cid,
                        "used_from_boundary": cur, "not_in_boundary": prev_b,
                        "finding": "later-boundary selection applied to "
                                   "earlier event (D1)"})
                    later_events.add(str(e.get("close_time")
                                         or e.get("event_time")))
        # new-run self-check moved outside (always runs)
        comparison = {
            "old_record": str(args.old_record),
            "old_n_events": len(old_events),
            "old_n_revisions": len(old_revs),
            "old_causal_evidence_accepted": False,
            "note": ("old event bindings / propagation entries are NOT "
                     "accepted causal evidence and are not success targets"),
            "reproduced_future_reference_counterexamples": {
                "audit_reported": "36 of 59 event records contain references "
                                  "unavailable at event time",
                "id_scheme_note": (
                    "the old record used bar-index candidate ids; the stable "
                    "source/time id scheme cannot resolve knowable times for "
                    f"{unmatched_old_ids} old bound ids — those rows are "
                    "unverifiable, not cleared"),
                "unmatched_old_bound_ids": unmatched_old_ids,
                "unavailable_at_event_time_bindings": len(contaminated),
                "unavailable_at_event_time_distinct_events": len(contam_events),
                "later_boundary_selection_retroactive_bindings": len(later_sel),
                "later_boundary_selection_retroactive_distinct_events":
                    len(later_events),
                "examples": contaminated[:10] + later_sel[:10],
            },
            "new_run_future_reference_violations": len(new_violations),
            "new_run_information_key_axis_verified_bindings": axis_verified,
            "new_n_events": len(events_out),
            "new_propagation": ledger.snapshot(),
        }

    # ---- final audit patch (item 5): propagation + ambiguity accounting ----
    # NOTE on semantics: propagation_revisions rows are CUMULATIVE per-boundary
    # records of one replay stream — never "independent market events".
    revs = ledger.revisions
    change_facts = [r for r in revs if r.get("kind") == "change-fact"]
    recomputations = [r for r in revs if r.get("kind") != "change-fact"]
    with_diffs = [r for r in recomputations if r.get("computed_changes")]
    no_ops = [r for r in recomputations if not r.get("computed_changes")]
    propagation_summary = {
        "note": ("rows are cumulative per-boundary records of one replay "
                 "stream (distinct idem rep-bar events per boundary), not "
                 "independent market events"),
        "total_rows": len(revs),
        "change_facts": len(change_facts),
        "recomputations": len(recomputations),
        "recomputations_with_computed_diffs": len(with_diffs),
        "recomputations_no_op": len(no_ops),
    }

    def _rid(cid: str) -> str:
        return cid.split("|")[0]

    # Cumulative ambiguity RECORDS = per-boundary generator ambiguity entries
    # (ambiguities_out), cross-referenced with candidate-level endpoint
    # evidence from the final candidate inventory.
    kind_map = {"same-bar-extreme-vs-reversal": "F-T",
                "same-bar-order-unresolved": "F-K"}
    amb_records = [a for a in ambiguities_out
                   if a.get("kind") in kind_map]
    ev_by_id = {r["candidate_id"]: r.get("same_bar_evidence")
                for r in coverage_rows}

    def _rec_ev(a):
        if a.get("endpoint_evidence"):
            return a["endpoint_evidence"]
        for pid in a.get("pair", []):
            e = ev_by_id.get(pid)
            if e:
                return e
        return None

    fam_counts = Counter(kind_map[a["kind"]] for a in amb_records)
    distinct_events = sorted({(a.get("rep"), a.get("bar"))
                              for a in amb_records})
    recur_counts = Counter((a.get("rep"), a.get("bar")) for a in amb_records)
    recur_all = sum(1 for ev, n in recur_counts.items()
                    if n == len(boundaries_out))
    # endpoint evidence classes (causal-state integration V1): only PROVEN
    # ordering resolves; constrained-but-not-unique stays material
    ev_class = Counter(same_bar_evidence_class(_rec_ev(a)) for a in amb_records)
    resolved_recs = [a for a in amb_records
                     if same_bar_evidence_class(_rec_ev(a)) == "proven"]
    constrained_recs = [a for a in amb_records
                        if same_bar_evidence_class(_rec_ev(a)) == "constrained"]
    unresolved_recs = [a for a in amb_records
                       if same_bar_evidence_class(_rec_ev(a)) == "unavailable"]
    side_counts = Counter(_rec_ev(a) for a in
                          resolved_recs + constrained_recs)
    amb_by_id = {r["candidate_id"]: r for r in coverage_rows
                 if r.get("same_bar_order") == "unresolved"}
    affecting = []
    for b in boundaries_out:
        for rep_name, tdict in b["tasks"].items():
            if not isinstance(tdict, dict):
                continue
            for tname, trow in tdict.items():
                if not isinstance(trow, dict):
                    continue
                sel = trow.get("selected") or trow.get("selected_id")
                scanned = ([sel] if sel else []) + list(trow.get("survivors") or [])
                for cid in scanned:
                    r = amb_by_id.get(cid)
                    if r:
                        affecting.append({
                            "boundary": b["boundary"], "rep": rep_name,
                            "task": tname, "candidate_id": cid,
                            "same_bar_evidence": r.get("same_bar_evidence"),
                            "material": (same_bar_evidence_class(
                                r.get("same_bar_evidence")) != "proven"),
                            "task_status": trow.get("status"),
                            "selected": sel == cid,
                        })
    ambiguity_accounting = {
        "note": ("cumulative ambiguity RECORDS across boundary/rep runs "
                 "(repeated observations of the same bar event recur across "
                 "prefixes) — distinct rep-bar events are the market-event "
                 "scale; records are never independent market events"),
        "total_records": len(amb_records),
        "by_family": dict(fam_counts),
        "distinct_rep_bar_events": len(distinct_events),
        "events_recurring_in_all_boundaries": recur_all,
        "max_records_per_event": max(recur_counts.values()) if recur_counts else 0,
        "recurrence_distribution": {str(k): v for k, v in
                                   sorted(Counter(recur_counts.values()).items())},
        "endpoint_resolved_records": len(resolved_recs),
        "endpoint_resolution_side": dict(side_counts),
        "evidence_class_counts": dict(ev_class),
        "constrained_not_unique_records": len(constrained_recs),
        "genuinely_unresolved_records": len(unresolved_recs),
        "genuinely_unresolved_events": len({(a.get("rep"), a.get("bar"))
                                           for a in unresolved_recs}),
        "affecting_actual_selections": affecting,
    }
    binding_accounting = {
        "note": ("T-S2 binding kinds from pre-event lifecycle state "
                 "(knowledge contract file 16): first-break = structural "
                 "break eligibility (A); later-interaction = subsequent "
                 "factual price interaction with a known level (B), "
                 "preserved as separate events and never dropped"),
        "by_kind": dict(binding_kind_counts),
        "factual_later_interactions": sum(
            v for k, v in binding_kind_counts.items()
            if "later-interaction" in k),
        "first_break_bindings": sum(
            v for k, v in binding_kind_counts.items()
            if k.endswith("first-break") and "later" not in k),
    }

    # ---- stable identity recognition across overlapping replay windows (§11)
    rep_ck5 = reps["C_FK5"]
    fC_eval = fC[(fC.index >= pd.Timestamp(args.start))
                 & (fC.index < pd.Timestamp(args.end))]
    ids_full = {p.candidate_id
                for p in fk_turning_points(fC, int(rep_ck5.param("k")), rep_ck5,
                                           axis=axis)}
    ids_eval = {p.candidate_id
                for p in fk_turning_points(fC_eval, int(rep_ck5.param("k")),
                                           rep_ck5, axis=axis)}
    identity_recognition = {
        "rep": "C_FK5",
        "note": ("source/time identity: candidates regenerated on the "
                 "evaluation-only window (local bar indices shifted) are "
                 "recognized in the full left-context run by identity"),
        "n_eval_window_candidates": len(ids_eval),
        "recognized_in_full_context": len(ids_eval & ids_full),
        "unrecognized_examples": sorted(ids_eval - ids_full)[:5],
    }

    # ---- terminal provisional candidate retention (consolidation V1 §6) ---
    # every candidate observable in a truncated prefix must persist in the
    # one-shot full-history inventory (confirmed, or superseded-but-retained)
    retention = {}
    for rid, rep in reps.items():
        fview = fC if rep.view_id == "C" else fF
        if rep.family == "F-K":
            full_pts = fk_turning_points(fview, int(rep.param("k")), rep,
                                         axis=axis)
        else:
            full_pts = ft_turning_points(fview, rep.param("tau"), rep,
                                         axis=axis)
        full_ids = {p.candidate_id for p in full_pts}
        prefix_ids = prefix_inventory.get(rid, set())
        missing = prefix_ids - full_ids
        retention[rid] = {
            "n_full_history_inventory": len(full_ids),
            "n_prefix_inventory_union": len(prefix_ids),
            "n_prefix_only_ids": len(missing),
            "prefix_only_examples": sorted(missing)[:5],
            "n_retained_superseded_in_full": sum(
                1 for p in full_pts if p.status == "superseded"),
        }
    print("propagation summary:", propagation_summary, flush=True)
    print("ambiguity accounting:", {k: v for k, v in ambiguity_accounting.items()
                                    if k != "affecting_actual_selections"},
          flush=True)
    print("ambiguity affecting selections (material only):",
          [a for a in affecting if a["material"]], flush=True)
    print("t2 exclusions:", dict(t2_exclusions), flush=True)
    print("binding accounting:", binding_accounting, flush=True)
    print("identity recognition:", identity_recognition, flush=True)

    # ---- record (provenance: ACTUAL source version used for the run) ----
    csm_path = Path(args.src) / "trading_system/research/contextual_selection/csm.py"
    summary = {
        "experiment_id": "CSM-SEL-EXP-V2",
        "supersedes": "CSM-SEL-EXP-V1 (commit 4e04198) — old record retained "
                      "for comparison only, never as corrected evidence",
        "source_version": {
            "git_head_at_run": _git_head(),
            "csm_py_sha256": _sha256_file(csm_path),
            "experiment_py_sha256": _sha256_file(Path(__file__).resolve()),
        },
        "inputs": {
            "months": args.months,
            "window": f"{args.start} -> {args.end} UTC",
            "left_context_start": "2025-08-01 (context only)",
            "evaluation_event_window": "2025-09-20 .. 2025-09-27 UTC",
            "shared_information_axis": {
                "timeline_id": axis.timeline_id,
                "n_rows": axis.n_rows,
                "contract": "INFORMATION_KEY_V1_2 (CLOSED 6.2A-0, reused)",
            },
            "files": {f"BTCUSDT_1m_{m.strip()}.csv":
                      _sha256_file(args.mirror_dir / f"BTCUSDT_1m_{m.strip()}.csv")
                      for m in args.months.split(",")},
            "semantics": "PUBLISHED_OHLC_FACT; SOURCE_ORIGIN_UNVERIFIED",
        },
        "policy_classification": {pid: {k: v for k, v in e.items()}
                                  for pid, e in pol.items()},
        "tie_policies_in_effect": {
            "crossing": TIE_CROSS_EQUAL_UNBOUND,
            "ft_equal_extreme": TIE_FT_EQ_FIRST,
        },
        "t2_provisional_contract": (
            "T-S2 admits provisional references ONLY via explicit "
            "allow_provisional=True (occurrence-visible); the csm default "
            "excludes provisional/superseded/broken candidates"),
        "n_boundaries": len(boundaries_out),
        "n_events": len(events_out),
        "n_candidate_rows": len(coverage_rows),
        "n_ambiguities": len(ambiguities_out),
        "ledger": ledger.snapshot(),
        "replay_checks": replay_checks,
        "exclusion_histogram": dict(Counter(
            e.code for r in ledger.results for e in r.excluded)),
        "t2_exclusion_histogram": dict(t2_exclusions),
        "unresolved_histogram": dict(Counter(
            r.unresolved.reason_code for r in ledger.results if r.unresolved)),
        "sp16_agreement": dict(Counter(
            b["representation_report_SP16"]["agreement"] for b in boundaries_out)),
        # consolidation V1 (task §6/§8): retention probe + ALWAYS-ON self-check
        "candidate_retention": retention,
        "self_check": {
            "axis_verified_bindings": axis_verified,
            "future_reference_violations": len(new_violations),
            "violation_examples": new_violations[:10],
            "rule": "every binding must be verified on the shared axis at "
                    "its event time; zero violations tolerated",
        },
        "selection_quality": {
            "state": "NOT_ESTABLISHED",
            "blocker": "EP: no acceptable-set annotations exist for this "
                       "instrument/window (unchanged by this remediation)",
            "what_was_measured": "causal integrity, candidate coverage, "
                                 "computed dependency recomputation — NOT "
                                 "selection quality",
        },
    }
    record = {"summary": summary, "boundaries": boundaries_out,
              "binding_events": events_out,
              "ambiguities": ambiguities_out[:200],
              "comparison_v1_vs_v2": comparison,
              "propagation_summary": propagation_summary,
              "ambiguity_accounting": ambiguity_accounting,
              "binding_accounting": binding_accounting,
              "identity_recognition": identity_recognition,
              "propagation_revisions": ledger.revisions}
    out_path = out_dir / "experiment_record_v2.json"
    # SAFE INTEGRATION V1: the record is STAGED with the other artifacts and
    # committed atomically below.

    # ---- inspectable manifest (task §7): durable identities + reproduction --
    info_time_path = (Path(args.src) / "trading_system/research/information_time.py")
    manifest = {
        "experiment_id": "CSM-SEL-EXP-V2-CONSOLIDATION",
        "source": {
            "git_head_at_run": _git_head(),
            "csm_py_sha256": _sha256_file(csm_path),
            "experiment_py_sha256": _sha256_file(Path(__file__).resolve()),
            "information_time_py_sha256": (_sha256_file(info_time_path)
                                           if info_time_path.exists() else None),
        },
        "inputs": summary["inputs"],
        "policy_registry": summary["policy_classification"],
        "evaluation_window": "2025-09-20 .. 2025-09-27 UTC",
        "left_context_start": "2025-08-01 UTC",
        "counts": {
            "boundaries": len(boundaries_out),
            "event_bindings": len(events_out),
            "binding_kinds": binding_accounting.get("by_kind"),
            "candidate_rows": len(coverage_rows),
            "historical_transitions_reapplied": sum(
                (b["tasks"][rid].get("restored_transitions") or 0)
                for b in boundaries_out for rid in b["tasks"]),
            "dependency_updates": len(ledger.revisions),
            "ambiguity_records": ambiguity_accounting.get("total_records"),
            "incomplete_dependency_coverage": summary["ledger"].get(
                "incomplete_dependency_coverage"),
        },
        "self_check": summary["self_check"],
        "candidate_retention": retention,
        "reproduction": {
            "python": "3.11",
            "pandas": "2.2.3",
            "numpy": "2.2.6",
            "command": (
                "PYTHONPATH=src python "
                "docs/research/contextual_selection_v1/"
                "experiment_contextual_selection_v2.py "
                "--mirror-dir <mirror> --out-dir <out> "
                "--months 2025-08,2025-09 "
                "--start 2025-08-01 --end 2025-09-28 "
                "--old-record docs/research/contextual_selection_v1/"
                "experiment_record_v2.json --src src"),
            "inputs": "CSV sha256 identities above (btc-usdt-1m mirror)",
            "outputs": ["experiment_record_v2.json",
                        "candidate_ledger_v1.jsonl.gz",
                        "propagation_log_v1.jsonl",
                        "experiment_manifest_v1.json", "REPRODUCE.md"],
        },
    }
    repro_text = f"""# CSM V1 safe-integration run — reproduction

Authoritative full-run output of the CLOSED-FOUNDATION PRESERVATION AND
SAFE INTEGRATION build (audit REVISE remediation).
Selection quality: NOT_ESTABLISHED (EP blocker, unchanged).

## Source
- git head at run: `{manifest['source']['git_head_at_run']}`
- csm.py sha256: `{manifest['source']['csm_py_sha256']}`
- experiment sha256: `{manifest['source']['experiment_py_sha256']}`
- information_time.py sha256 (CLOSED, byte-identical): `{manifest['source']['information_time_py_sha256']}`

## Environment
Python 3.11, pandas==2.2.3, numpy==2.2.6 (pinned; pandas 3.x breaks the tests)

## Inputs
BTCUSDT 1m CSVs (PUBLISHED_OHLC_FACT; SOURCE_ORIGIN_UNVERIFIED), identities:

{json.dumps(manifest['inputs']['files'], indent=1)}

Mirror source: parshant231234-eng/BTCUSDT-Historical-Data @ 27c9be70
(nested 1m/2025/MM/), fetched with Accept: application/vnd.github.raw.

## Window
- context (market observations only): 2025-08-01 .. 2025-09-20 UTC
- evaluation/event window: 2025-09-20 .. 2025-09-27 UTC

## Command
```
{manifest['reproduction']['command']}
```
`--old-record` names a DISTINCT historical input (the tracked
pre-consolidation record kept for comparison) — never this run's output.

## Outputs
- experiment_record_v2.json — full run record (boundaries, events, revisions)
- candidate_ledger_v1.jsonl.gz — per-candidate coverage rows: T-S1 origin,
  T-S1 extreme, T-S2 event refs (with binding kinds) and T-S5 support legs
  (leg-level classification); every row carries its status-transition
  sequence and explicit superseded_by
- propagation_log_v1.jsonl — change-fact / recomputation / stale-descendant
  rows (emitted artifact; matches the record's propagation_revisions)
- experiment_manifest_v1.json — this manifest (machine-readable)
- historical note: the tracked `experiment_record_v2.json` of the
  pre-consolidation build (source head e90a62f, short window) is retained
  for historical comparison ONLY and is not the output of this build.
"""
    # ---- atomic commit of every artifact (audit F §9) --------------------
    # All payloads serialize to staged temps first; a failure removes every
    # temp and leaves no target partially written (no truncated gzip, no
    # stale mixtures).  Targets are committed only into the clean out dir.
    artifact_hashes = write_run_artifacts(out_dir, {
        "experiment_record_v2.json": record,
        "candidate_ledger_v1.jsonl.gz": ("jsonl.gz", coverage_rows),
        "propagation_log_v1.jsonl": ("jsonl", ledger.revisions),
        "experiment_manifest_v1.json": manifest,
        "REPRODUCE.md": repro_text,
    })
    print("manifest:", out_dir / "experiment_manifest_v1.json", flush=True)
    print("reproduce:", out_dir / "REPRODUCE.md", flush=True)
    print("artifact sha256:", json.dumps(artifact_hashes, indent=1), flush=True)
    print("ledger:", summary["ledger"], flush=True)
    print("exclusions:", summary["exclusion_histogram"], flush=True)
    print("unresolved:", summary["unresolved_histogram"], flush=True)
    print("SP-16:", summary["sp16_agreement"], flush=True)
    print("replay:", all(c["equal"] for c in replay_checks), replay_checks, flush=True)
    if comparison:
        print("comparison:", json.dumps(
            comparison["reproduced_future_reference_counterexamples"],
            indent=1)[:1500], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
