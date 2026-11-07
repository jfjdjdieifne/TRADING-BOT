#!/usr/bin/env python
"""Real-market experiment: contextual selection of movement/structural
references on BTCUSDT (research only; no trading recommendations).

Experiment id: CSM-SEL-EXP-V1
Source data: parshant231234-eng/BTCUSDT-Historical-Data @ 27c9be70
  (month files sha256 15d26d23.. (2025-08), e1d5c8f3.. (2025-09)).

Declared operational policy slots (O-class; SP-18; sensitivity grid recorded;
none of these is a market-truth claim):
  P-TF-COARSE = 1h, P-TF-FINE = 5m   (two timeframes, owner not consulted;
                                      recorded as builder-declared O)
  P-ORIGIN    = role "origin-of-last-confirmed-leg" (SWS-02)
  P-CONTINUATION = continuation-long timing uses completed down-legs in an
                                      up-leg (W2 pattern)
  P-FK-COARSE = k in {5, 12}; P-FK-FINE = k in {6}; P-T-FINE = tau in {80}
  P-TF tie rule = close-equality is not a crossing (SP-03 open choice)

Tasks run per frozen boundary: T-S1 (structural reference), T-S2 (event
binding by crossing, close basis), T-S5 (falsifier of the declared
interpretation "view C last-confirmed-leg direction holds").

Every candidate survives in the output with an X-* reason when excluded;
unresolved states carry MO/MP/AI/IC/EP/OOD codes (SP-19).
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

sys.path.insert(0, "/home/user/TRADING-BOT/project/trading_project/src")

from trading_system.research.contextual_selection import (  # noqa: E402
    InterpretationLedger,
    PolicyRegistry,
    Representation,
    build_legs,
    fk_turning_points,
    ft_turning_points,
    sp01_knowability,
    task_s1_structural_reference,
    task_s2_event_binding,
    task_s5_falsifier,
)

MIRROR = Path("/home/user/work/data/btc/mirror")
OUT = Path("/home/user/work/csm_v1")
OUT.mkdir(parents=True, exist_ok=True)

BOUNDARIES = [
    ("D1_2025-09-20", "2025-09-20 00:00:00"),
    ("D2_2025-09-22", "2025-09-22 00:00:00"),
    ("D3_2025-09-24", "2025-09-24 00:00:00"),
    ("B0_midnight_open", "2025-09-25 00:01:00"),   # SXM-005 forward clause
    ("B1_post5", "2025-09-25 06:49:00"),           # SXM-005 created 06:49:22.428Z (v1)
    ("M1_2025-09-25_noon", "2025-09-25 12:00:00"),
    ("B2_post6", "2025-09-25 19:34:00"),           # SXM-006 created 19:34:06.983Z (v3)
    ("D4_2025-09-26", "2025-09-26 12:00:00"),
    ("D5_2025-09-26_end", "2025-09-26 23:00:00"),
]


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_1m() -> pd.DataFrame:
    frames = []
    for name in ("BTCUSDT_1m_2025-08.csv", "BTCUSDT_1m_2025-09.csv"):
        f = pd.read_csv(MIRROR / name, usecols=["datetime_utc", "open", "high", "low", "close", "volume"])
        frames.append(f)
    f = pd.concat(frames, ignore_index=True)
    f["dt"] = pd.to_datetime(f["datetime_utc"])
    f = f[(f["dt"] >= "2025-08-01 00:00:00") & (f["dt"] < "2025-09-27 00:00:00")]
    return f.set_index("dt").sort_index()


def resample_ohlc(f1m: pd.DataFrame, rule: str) -> pd.DataFrame:
    agg = f1m.resample(rule).agg({"open": "first", "high": "max", "low": "min",
                                  "close": "last", "volume": "sum"})
    return agg.dropna(subset=["open"])


def last_completed_pos(index: pd.DatetimeIndex, when: str) -> int:
    """Position of the last bar whose END time is <= `when` (bar = start-labeled,
    completes at start + interval; we use label + rule as close time)."""
    t = pd.Timestamp(when)
    closes = index + pd.Timedelta(minutes=5) if index.name == "5m" else None
    # close time = start + interval; intervals fixed by construction below
    return None  # replaced by caller with explicit close arrays


def make_reps() -> dict:
    return {
        "C_FK5": Representation("F-K", "C", "coarse", (("k", 5.0),)),
        "C_FK12": Representation("F-K", "C", "coarse", (("k", 12.0),)),
        "C_FT250": Representation("F-T", "C", "coarse", (("tau", 250.0),)),
        "F_FK6": Representation("F-K", "F", "fine", (("k", 6.0),)),
        "F_FT80": Representation("F-T", "F", "fine", (("tau", 80.0),)),
    }


def main() -> int:
    f1m = load_1m()
    fC = resample_ohlc(f1m, "1h")
    fF = resample_ohlc(f1m, "5min")
    closeC = fC.index + pd.Timedelta(hours=1)     # bar completion times
    closeF = fF.index + pd.Timedelta(minutes=5)
    print(f"bars: 1m={len(f1m)} 5m={len(fF)} 1h={len(fC)}")

    pol = PolicyRegistry()
    pol.register("P-ORIGIN", "origin of most recent confirmed leg (SWS-02)",
                 "origin-of-last-confirmed-leg")
    pol.register("P-CONTINUATION", "continuation-long uses completed down-legs in up-leg",
                 "down-legs-in-up-leg")
    pol.register("P-TF", "coarse=1h fine=5m (builder-declared; owner not consulted)",
                 "1h/5m")
    pol.register("P-FK-K-COARSE", "F-K window grid on coarse view", [5, 12])
    pol.register("P-FK-K-FINE", "F-K window on fine view", [6])
    pol.register("P-T-TAU-FINE", "F-T reversal amount on fine view (USD)", 80.0)
    pol.register("P-TIE", "close equality is not a crossing (SP-03 open choice)",
                 "not-bound")

    reps = make_reps()
    ledger = InterpretationLedger()
    boundaries_out = []
    events_out = []
    prev_active = {}      # rep_id -> active reference point objects
    prev_t = None
    replay_checks = []

    for bname, when in BOUNDARIES:
        row = {"boundary": bname, "decision_time_utc": when, "tasks": {}}
        # --- per representation: causal truncation, generation, T-S1 ---------
        for rid, rep in reps.items():
            fview = fC if rep.view_id == "C" else fF
            closes = closeC if rep.view_id == "C" else closeF
            cutoff = closes.searchsorted(pd.Timestamp(when), side="right") - 1
            bars_t = fview.iloc[: cutoff + 1]
            if rep.family == "F-K":
                pts = fk_turning_points(bars_t, int(rep.param("k")), rep)
            else:
                pts = ft_turning_points(bars_t, rep.param("tau"), rep)
            legs = build_legs(pts, rep)
            t_bar = cutoff  # decision bar index in this view
            r = task_s1_structural_reference(pts, legs, t_bar, rep,
                                             "origin-of-last-confirmed-leg",
                                             pol, "P-ORIGIN",
                                             state_id_prefix=f"{bname}:{rid}:S1")
            ledger.record(r)
            r_ext = task_s1_structural_reference(
                pts, legs, t_bar, rep, "last-confirmed-extreme", pol, None,
                state_id_prefix=f"{bname}:{rid}:S1x")
            ledger.record(r_ext)
            row["tasks"][rid] = {
                "T-S1_origin": {
                    "status": r.status,
                    "selected": r.selected_id,
                    "survivors": r.survivors,
                    "n_excluded": len(r.excluded),
                    "excluded_codes": dict(Counter(e.code for e in r.excluded)),
                    "notes": r.notes,
                },
                "T-S1_extreme": {"status": r_ext.status, "selected": r_ext.selected_id},
                "n_points": len(pts),
                "n_legs": len(legs),
                "unresolved_codes": [r.unresolved.reason_code] if r.unresolved else [],
            }
            # level lookup for binding
            by_id = {p.candidate_id: p for p in pts}
            prev_active[rid] = (r, by_id, rep)

        # --- T-S2: events since previous boundary on the fine view -----------
        if prev_t is not None:
            fview = fF
            closes = closeF
            lo = closes.searchsorted(pd.Timestamp(prev_t), side="right") - 1
            hi = closes.searchsorted(pd.Timestamp(when), side="right") - 1
            refs_by_view = {}
            for rid, (r1, by_id, rep) in prev_active.items():
                if r1.selected_id and r1.selected_id in by_id:
                    refs_by_view.setdefault(rep.view_id, []).append(by_id[r1.selected_id])
            for j in range(max(lo, 0) + 1, hi + 1):
                c = float(fview.iloc[j]["close"])
                prev_c = float(fview.iloc[j - 1]["close"])
                rb = {v: [p for p in refs if p.knowable_bar <= j] for v, refs in refs_by_view.items()}
                if not any(rb.values()):
                    continue
                ev = task_s2_event_binding(j, c, rb, j, tie_bound=False,
                                           prev_close=prev_c,
                                           state_id_prefix=f"{bname}:E{j}")
                if ev.survivors:
                    ledger.record(ev)
                    ledger.record_event(
                        int(j), "binding",
                        f"close={c} time={closes[j]} notes={ev.notes}",
                        ev.survivors)
                    events_out.append({
                        "boundary": bname, "event_bar": int(j),
                        "close_time": str(closes[j]), "close": c,
                        "bound": ev.survivors, "notes": ev.notes,
                    })
                    # W8-pattern propagation when the active coarse reference is hit
                    for rid, (r1, by_id, rep) in prev_active.items():
                        if rep.view_id == "C" and r1.selected_id in ev.survivors:
                            log = ledger.propagate(j, [
                                (f"status:{r1.selected_id}", "active-structure", f"broken@{j}"),
                                ("T-S1(view C)", r1.selected_id or "-", "recomputed-next-boundary"),
                                ("T-S5(falsifier)", r1.selected_id or "-", "invalid(contradicted)"),
                            ])
                            row.setdefault("propagations", []).extend(log)

        # --- T-S5: declared interpretation falsifier per view C rep ----------
        s5_out = {}
        for rid, (r1, by_id, rep) in prev_active.items():
            if rep.view_id != "C":
                continue
            direction = "up" if "up" in " ".join(r1.notes) else "down"
            legs_all = build_legs(list(by_id.values()), rep)
            claims = [{"interpretation": f"I:{rid}:{bname}", "view": "C",
                       "role": "origin-of-last-confirmed-leg",
                       "direction": direction}]
            r5 = task_s5_falsifier(claims, list(by_id.values()), legs_all,
                                   int(closeC.searchsorted(pd.Timestamp(when), side="right") - 1),
                                   state_id_prefix=f"{bname}:{rid}:S5")
            ledger.record(r5)
            s5_out[rid] = {"status": r5.status, "falsifier": r5.survivors,
                           "notes": r5.notes}
        row["tasks"]["T-S5_by_view_C_rep"] = s5_out

        # --- SP-16 representation-dependence report -------------------------
        origins = {rid: row["tasks"][rid]["T-S1_origin"]["selected"]
                   for rid in ("C_FK5", "C_FK12", "C_FT250")}
        agree = len(set(v.split("|")[1] if v and "|" in v else v for v in origins.values())) <= 1
        row["representation_report_SP16"] = {
            "coarse_origins": origins,
            "agreement": "agree" if agree else "disagree",
            "note": "disagreement is reported, never merged (SWS-01)",
        }
        boundaries_out.append(row)
        prev_t = when
        print(f"[{bname}] " + " ".join(
            f"{rid}={row['tasks'][rid]['T-S1_origin']['selected']}" for rid in reps))

        # --- replay consistency (SWS-04d) on two sample boundaries ----------
        if bname in ("B1_post5", "B2_post6"):
            for rid, rep in (("C_FK5", reps["C_FK5"]), ("F_FK6", reps["F_FK6"])):
                fview = fC if rep.view_id == "C" else fF
                closes = closeC if rep.view_id == "C" else closeF
                cutoff = closes.searchsorted(pd.Timestamp(when), side="right") - 1
                bars_t = fview.iloc[: cutoff + 1]
                pts2 = (fk_turning_points(bars_t, int(rep.param("k")), rep)
                        if rep.family == "F-K" else
                        ft_turning_points(bars_t, rep.param("tau"), rep))
                legs2 = build_legs(pts2, rep)
                r2 = task_s1_structural_reference(pts2, legs2, cutoff, rep,
                                                  "origin-of-last-confirmed-leg",
                                                  pol, "P-ORIGIN")
                same = r2.selected_id == row["tasks"][rid]["T-S1_origin"]["selected"]
                replay_checks.append({"boundary": bname, "rep": rid,
                                      "recomputed": r2.selected_id,
                                      "stored": row["tasks"][rid]["T-S1_origin"]["selected"],
                                      "equal": same})

    # ------------------------------------------------------------------
    summary = {
        "experiment_id": "CSM-SEL-EXP-V1",
        "target_commit": "c96b9a56b3e966432c30cf058c19abda9c02224b",
        "inputs": {
            "1m_2025-08_sha256": sha256_file(MIRROR / "BTCUSDT_1m_2025-08.csv"),
            "1m_2025-09_sha256": sha256_file(MIRROR / "BTCUSDT_1m_2025-09.csv"),
            "window": "2025-08-01 -> 2025-09-27 UTC",
            "semantics": "PUBLISHED_OHLC_FACT; SOURCE_ORIGIN_UNVERIFIED",
        },
        "declared_policies": {pid: e for pid, e in pol.items()},
        "n_boundaries": len(boundaries_out),
        "n_events": len(events_out),
        "ledger": ledger.snapshot(),
        "replay_checks": replay_checks,
        "exclusion_histogram": dict(Counter(
            e.code for r in ledger.results for e in r.excluded)),
        "unresolved_histogram": dict(Counter(
            r.unresolved.reason_code for r in ledger.results if r.unresolved)),
        "sp16_agreement": dict(Counter(
            b["representation_report_SP16"]["agreement"] for b in boundaries_out)),
        "learning_evidence": {
            "objective_A_golden_set": "12/12 exact (tests/test_contextual_selection_csm.py)",
            "objective_B_contextual_coherence": "NOT_ESTABLISHED",
            "objective_B_blocker": "no acceptable-set annotations exist for any "
                                   "real instrument/window; route: annotation "
                                   "protocol (file 03 §2) + seed bindings from "
                                   "source-verified cases (SXM-005/006, ICT-2024-09-16)",
            "objective_C_predictive_usefulness": "NOT_ESTABLISHED (not evaluated in "
                                                 "the selection step by design)",
        },
        "selection_quality": {
            "state": "NOT_ESTABLISHED",
            "blocker": "EP: no annotated acceptable sets for this instrument/window; "
                       "per file 18 objective B requires human annotations with "
                       "inter-annotator agreement before any preference learning",
            "what_was_measured": "deterministic selection behavior, ambiguity "
                                 "preservation, representation dependence, replay "
                                 "equality — not selection quality",
        },
    }
    record = {
        "summary": summary,
        "boundaries": boundaries_out,
        "binding_events": events_out,
        "propagation_log": ledger.revisions,
    }
    out_path = OUT / "experiment_record_v1.json"
    out_path.write_text(json.dumps(record, indent=1, default=str))
    print("record:", out_path)
    print("ledger:", summary["ledger"])
    print("exclusions:", summary["exclusion_histogram"])
    print("unresolved:", summary["unresolved_histogram"])
    print("SP-16:", summary["sp16_agreement"])
    print("replay:", all(c["equal"] for c in replay_checks), replay_checks)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
