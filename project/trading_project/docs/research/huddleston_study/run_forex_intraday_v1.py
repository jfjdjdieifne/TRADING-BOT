#!/usr/bin/env python3
"""End-to-end causally-evaluated FOREX development loop (research/paper).

RESEARCH / PAPER recommendations and their measured outcomes only —
NOT live orders, NOT a claim of trading readiness.
selection_quality = NOT_ESTABLISHED.

Data: EURUSD 5m BID/ASK (Dukascopy via mailztoganesh-civil/forex-data
@ 56d5f04, data/EURUSD/5m_bidask/).  Structure is computed on the MID;
hypothetical fills use the actual BID/ASK rows.

Phases (chronological; the eval period is never used for tuning):
  dev   : fit the existing ContextEventModel on dev episodes ONLY
          (label windows must complete inside dev) and run the loop.
  eval  : freeze the dev model and run the untouched eval period.
  pause : pause-and-step excerpt (disclosed window).

The analytical QUESTION (one): after an old structural reference is
crossed, does subsequently observable lower-frame evidence (connected
readings: FVG comparison) support a short-duration research plan in the
scenario direction — or is the state honestly unresolved?

Plan rules come from the EXISTING plan layer (build_components /
create_plan / observe_plan): research configurations, not a proven
Michael entry.  Costs: actual spread at fill bars (bid/ask).  No
commission data exists in this dataset (reported, never invented).
Same-bar stop/target ambiguity (5m path inside one task bar) is
preserved as AMBIGUOUS — never resolved in favor of the trade.
"""

from __future__ import annotations

import argparse
import gzip
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
from trading_system.research.contextual_selection.csm import (  # noqa: E402
    SharedInformationAxis,
)
from trading_system.research.contextual_selection.decision_layer import (  # noqa: E402
    ContextEventModel,
    EpisodeExtractor,
    decide,
)
from trading_system.research.contextual_selection.monitoring import (  # noqa: E402
    MonitoringLoop,
    ReplayObservationStream,
)
from trading_system.research.contextual_selection.study_links import (  # noqa: E402
    StudyReasoningLayer,
)
from trading_system.research.contextual_selection.trade_plan import (  # noqa: E402
    PLAN_HYPOTHETICAL_ENTRY_MET,
    PLAN_INVALIDATED,
    PLAN_MISSED,
    PLAN_MONITORING,
    PLAN_CONDITION_OBSERVED,
    PLAN_NO_JUSTIFIED_PLAN,
    build_components,
    create_plan,
    evaluate_plans,
    observe_plan,
    resolve_world,
    source_agreement,
)

TASK_SCALE = "1h"
READINGS_SCALE = "15m"
K = 5
RUN_ID = "fx-intraday-v1"
HORIZON_BARS = 12          # label horizon in task-scale bars (12h)


# ---------------------------------------------------------------- data

def load_bidask(bidask_dir: Path, t0: str, t1: str):
    """EURUSD 5m bid/ask rows in [t0, t1).  Declared data-hygiene rule:
    rows where BOTH sides are flat AND both volumes are zero are
    market-closed placeholders (weekends/holidays) and are dropped —
    they are not observable movement.  (Research configuration.)"""
    parts = []
    y0, y1 = int(t0[:4]), int(t1[:4])
    for y in range(y0, y1 + 1):
        p = bidask_dir / f"{y}.csv.gz"
        if p.exists():
            parts.append(pd.read_csv(p, compression="gzip"))
    df = pd.concat(parts, ignore_index=True)
    df["Datetime"] = pd.to_datetime(df["Datetime"], utc=True)
    df = df.set_index("Datetime").sort_index()
    df = df[~df.index.duplicated(keep="first")]
    closed = ((df.BidOpen == df.BidClose) & (df.BidHigh == df.BidLow)
              & (df.AskOpen == df.AskClose) & (df.AskHigh == df.AskLow)
              & (df.BidVolume == 0) & (df.AskVolume == 0))
    df = df[~closed]
    df = df[(df.index >= pd.Timestamp(t0, tz="UTC"))
            & (df.index < pd.Timestamp(t1, tz="UTC"))]
    return df


_FRAMES_CACHE: dict = {"rows": None, "frames": None}
_FRAME_RULES = (("1D", "1D", 1440), ("4h", "4h", 240),
                ("1h", "1h", 60), ("15m", "15min", 15))


def frames_builder(rows: pd.DataFrame):
    """Completion-labelled resample of the 5m mid rows (1D/4h/1h/15m).

    PERFORMANCE (mathematically identical to a from-scratch resample of
    ``rows``): the monitoring loop calls this with GROWING prefixes of
    one series.  A bucket that closed before the prefix frontier
    aggregates exactly the same rows as in the full scan (all of its
    rows lie inside the prefix), so closed buckets are taken from a
    cached full resample and only the frontier bucket is re-aggregated
    from the prefix's own rows."""
    def _empty():
        return {name: pd.DataFrame(columns=["open", "high", "low",
                                            "close", "volume"])
                for name, _, _ in _FRAME_RULES}

    if len(rows) == 0:
        return _empty()
    cache = _FRAMES_CACHE
    prefix_of_cache = (
        cache["frames"] is not None
        and 0 < len(rows) <= len(cache["rows"])
        and rows.index[0] == cache["rows"].index[0]
        and rows.index[-1] == cache["rows"].index[len(rows) - 1])
    if not prefix_of_cache:
        # first call, a longer series, or a different series: full scan
        frames = {}
        for name, rule, minutes in _FRAME_RULES:
            f = rows.resample(rule).agg({"open": "first", "high": "max",
                                         "low": "min", "close": "last",
                                         "volume": "sum"})
            f = f.dropna(subset=["open"])
            f.index = f.index + pd.Timedelta(minutes=minutes)
            frames[name] = f
        cache["rows"] = rows
        cache["frames"] = frames
        return frames
    last = rows.index[-1]
    full_rows = cache["rows"]
    out = {}
    for name, rule, minutes in _FRAME_RULES:
        f = cache["frames"][name]
        width = pd.Timedelta(minutes=minutes)
        frontier_label = pd.Timestamp(last).floor(width) + width
        frontier_start = frontier_label - width
        j = int(f.index.searchsorted(frontier_label, side="left"))
        closed = f.iloc[:j]
        i0 = int(rows.index.searchsorted(frontier_start, side="left"))
        tail = rows.iloc[i0:]
        if len(tail):
            frontier = pd.DataFrame([{
                "open": float(tail["open"].iloc[0]),
                "high": float(tail["high"].max()),
                "low": float(tail["low"].min()),
                "close": float(tail["close"].iloc[-1]),
                "volume": float(tail["volume"].sum())}])
            frontier.index = pd.DatetimeIndex([frontier_label])
            out[name] = pd.concat([closed, frontier])
        else:
            out[name] = closed
    return out


def mid_rows(bidask: pd.DataFrame) -> pd.DataFrame:
    mid = (bidask.BidClose + bidask.AskClose) / 2.0
    return pd.DataFrame({
        "open": (bidask.BidOpen + bidask.AskOpen) / 2.0,
        "high": (bidask.BidHigh + bidask.AskHigh) / 2.0,
        "low": (bidask.BidLow + bidask.AskLow) / 2.0,
        "close": mid,
        "volume": bidask.BidVolume + bidask.AskVolume,
    }, index=bidask.index)


def engine_factory(task_scale=TASK_SCALE):
    def mk(frames):
        return AnalysisEngine(run_id=RUN_ID, frames=frames, k=K,
                              instrument="EURUSD",
                              task_scale=task_scale)
    return mk


# ------------------------------------------------------- outcome harness

def _intended_direction(pid, ctx_dir):
    """Interpretation-direction helper (ported from the Builder branch,
    module level by design).  Map interpretation id + context direction
    to the INTENDED trade direction:
      I-primary / I-scenario -> continuation: same side as the context
      I-alt                  -> reversal: opposite side of the context
      anything unknown       -> None (no determinable intended direction)
    """
    if ctx_dir not in ("up", "down"):
        return None
    if pid in ("I-primary", "I-scenario"):
        return ctx_dir
    if pid == "I-alt":
        return "down" if ctx_dir == "up" else "up"
    return None


def fill_price_next_open(bidask, ts, direction, side="entry"):
    """CAUSAL next_open fill: the fill happens at the OPEN of the NEXT
    5m bar strictly after ``ts`` (gap handling: next available row — a
    bar starting at or before ts is never used).  Both entry AND exit
    use next-open fills:  long entry / short exit use ASK;  short
    entry / long exit use BID.  RESEARCH SIMULATION — not an
    executable fill claim."""
    sub = bidask[bidask.index > ts]
    if sub.empty:
        return None, None
    row = sub.iloc[0]
    if direction == "up":
        px = row.AskOpen if side == "entry" else row.BidOpen
    else:
        px = row.BidOpen if side == "entry" else row.AskOpen
    return float(px), str(sub.index[0])


def fill_price(bidask, ts, direction, side="entry"):
    """EXPLICITLY LABELED NON-CAUSAL COMPARISON MODE (bar_close): a
    hypothetical fill at the CLOSE of the event bar itself, from the
    actual two-sided quote at that bar's last 5m row: a BUY enters at
    ASK and exits at BID; a SELL enters at BID and exits at ASK (the
    spread is actually paid in the simulation).  Kept only for
    comparison against the causal next_open mode; NOT the default.
    RESEARCH SIMULATION — not an executable fill claim."""
    sub = bidask[bidask.index <= ts]
    if sub.empty:
        return None, None
    row = sub.iloc[-1]
    if direction == "up":
        px = row.AskClose if side == "entry" else row.BidClose
    else:
        px = row.BidClose if side == "entry" else row.AskClose
    return float(px), str(sub.index[-1])


def same_bar_ambiguity(bidask, t_entry, t_exit, level_a, level_b):
    """If both an invalidation level and the objective level are
    touched by 5m quotes inside ONE task bar before the close resolved,
    the ordering is unavailable → AMBIGUOUS (never resolved favorably).
    Returns True when such a bar exists between entry and exit."""
    win = bidask[(bidask.index > t_entry) & (bidask.index <= t_exit)]
    if win.empty:
        return False
    bybar = win.groupby(win.index.floor("1h"))
    for _, g in bybar:
        hi = float(g.AskHigh.max())
        lo = float(g.BidLow.min())
        touch_a = (level_a is not None) and (lo <= level_a <= hi)
        touch_b = (level_b is not None) and (lo <= level_b <= hi)
        if touch_a and touch_b:
            return True
    return False


def outcome_for(plan, bidask, direction, fill_mode="next_open"):
    """Measure the hypothetical outcome of an entered plan from the
    5m bid/ask record.  fill_mode="next_open" (DEFAULT, causal): both
    entry and exit fill at the NEXT 5m bar open after their events
    (long entry/short exit at ask; short entry/long exit at bid).
    fill_mode="bar_close": EXPLICITLY LABELED NON-CAUSAL comparison
    mode filling at the event bar's close.  Same-bar stop/target
    double-touch (5m quotes inside one task bar) yields
    AMBIGUOUS_CENSORED — the ordering is never resolved in favour of
    the trade."""
    if fill_mode not in ("next_open", "bar_close"):
        raise ValueError("fill_mode must be 'next_open' or 'bar_close'")
    versions = plan.to_record()["versions"]
    ent = next((v for v in versions
                if v["state"] == PLAN_HYPOTHETICAL_ENTRY_MET), None)
    if ent is None:
        return {"outcome": "no-entry",
                "final_state": plan.current.state}
    t_entry = pd.Timestamp(ent["as_of_time"])
    inval = plan.current.state == PLAN_INVALIDATED
    final = plan.current.state
    exit_v = versions[-1]
    t_exit = pd.Timestamp(exit_v["as_of_time"])
    if fill_mode == "next_open":
        entry_px, t_fill = fill_price_next_open(bidask, t_entry,
                                                direction, side="entry")
        exit_px, _ = fill_price_next_open(bidask, t_exit, direction,
                                          side="exit")
    else:
        entry_px, t_fill = fill_price(bidask, t_entry, direction,
                                      side="entry")
        exit_px, _ = fill_price(bidask, t_exit, direction, side="exit")
    if entry_px is None or exit_px is None:
        return {"outcome": "censored", "final_state": final,
                "reason": "no quote rows at fill/exit time"}
    lvl = plan.current.levels
    inval_level = lvl.get("reference", {}).get("level")
    obj_level = lvl.get("leg_end", {}).get("level")
    amb = same_bar_ambiguity(bidask, t_entry, t_exit, inval_level,
                             obj_level)
    pips = (exit_px - entry_px) * (1 if direction == "up" else -1) * 1e4
    out = {
        "fill_mode": fill_mode,
        "entry_time": str(t_entry), "fill_time": t_fill,
        "entry_fill": entry_px, "exit_time": str(t_exit),
        "exit_fill": exit_px, "pips_gross": round(pips, 2),
        "final_state": final,
        "ambiguity_same_bar_touch": amb,
        "notes": (["causal next_open simulation: both legs fill at "
                   "the next 5m bar open after their events; long "
                   "entry/short exit at ask, short entry/long exit "
                   "at bid (spread actually paid)"]
                  if fill_mode == "next_open" else
                  ["NON-CAUSAL bar_close comparison mode (explicitly "
                   "labeled): both legs fill at the event bar's close "
                   "long entry/short exit at ask, short entry/long "
                   "exit at bid (spread actually paid)"])
                 + ["no commission data exists in this dataset "
                    "(not invented)"],
    }
    if amb:
        out["outcome"] = "AMBIGUOUS_CENSORED"
    elif final == PLAN_MISSED:
        out["outcome"] = "missed"
    elif inval:
        out["outcome"] = "loss"
    elif plan.objective_seen:
        out["outcome"] = "win"
    else:
        out["outcome"] = "open/censored"
    return out


# ------------------------------------------------------------------ run

def run_phase(args, phase: str) -> int:
    t0, t1 = args["from"], args["to"]
    out_dir = Path(args["out_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    bidask = load_bidask(Path(args["bidask_dir"]), t0, t1)
    rows = mid_rows(bidask)
    print(f"== {phase}: {t0} -> {t1}; open-market 5m rows: {len(rows)} "
          f"(market-closed placeholders dropped by declared rule)",
          flush=True)

    stream = ReplayObservationStream(
        rows.copy(), timeline_id="EURUSD_1m_fx_intraday_v1",
        dataset_identity="dukascopy-eurusd-5m-bidask@56d5f04")
    study = StudyReasoningLayer(run_id=RUN_ID, k=K,
                                task_scale=TASK_SCALE,
                                instrument="EURUSD")
    loop = MonitoringLoop(
        stream=stream, frames_builder=frames_builder,
        engine_factory=engine_factory(), task_scale=TASK_SCALE,
        study_layer=study, readings_scale=READINGS_SCALE)

    model = ContextEventModel()
    extractor = EpisodeExtractor(frames=loop._grid_frames, k=K,
                                 task_scale=TASK_SCALE,
                                 horizon_bars=HORIZON_BARS,
                                 axis=None, instrument="EURUSD")
    if phase == "eval":
        frozen = json.loads(Path(args["model"]).read_text())
        model.counts = {tuple(k): dict(v) for k, v in
                        frozen.get("counts", [])}
        model.n_episodes = int(frozen.get("n_episodes", 0))
        model.trained_through = (pd.Timestamp(frozen["trained_through"])
                                 if frozen.get("trained_through")
                                 else None)
        print(f"== frozen dev model loaded from {args['model']} "
              f"(eval NEVER trains; trained_through="
              f"{model.trained_through}) ==", flush=True)

    cases = []
    plans = []
    plan_seq = 0
    decision_seq = 0
    episodes = []
    pending_eps = []
    active_plan = None
    gate_stats = {"decisions": 0, "strict_pref": 0, "gate_pass": 0,
                  "plans_created": 0, "no_plan": 0}
    t_start = time.time()

    def gate_v1(dec, study) -> tuple:
        """V1 connected gate: a strict decision preference AND the
        connected readings do not contradict (research configuration,
        declared; no thresholds, no forced trades)."""
        if dec.primary_is_baseline or dec.state in ("NO_EDGE",
                                                    "UNRESOLVED"):
            return False, ("decision has no strict evidence-supported "
                           "preference: " + dec.state)
        rt = study.readings.tasks.get("RT-REF-REVIEW")
        # categorical connected CONTRADICTION (declared research
        # configuration; ENGINEERING interpretation — no thresholds):
        # hold the attempt while the connected readings hold an
        # EVIDENCE_PREFERRED FVG whose region direction OPPOSES the
        # INTENDED trade direction (interpretation-direction helper:
        # continuation follows the context, reversal opposes it — the
        # legacy gate wrongly compared against the raw context
        # direction and blocked profitable reversals).  This is
        # recorded contradicting evidence — not a prediction and not a
        # rule from the source material.
        ctx_dir = str(dec.context.get("direction"))
        pid = getattr(dec, "primary_interpretation_id", None)
        intended = _intended_direction(pid, ctx_dir)
        if intended is None:
            return False, (
                "decision has no determinable intended direction: "
                "pid=" + str(pid) + " ctx_dir=" + str(ctx_dir))
        for tid2, t2 in study.readings.tasks.items():
            c2 = t2.conclusion or {}
            pref = c2.get("preferred")
            if c2.get("status") == "EVIDENCE_PREFERRED" and pref:
                reg = study.readings.regions.get(pref)
                if reg is not None and intended in ("up", "down"):
                    oppose = ((reg.direction == "downward"
                               and intended == "up")
                              or (reg.direction == "upward"
                                  and intended == "down"))
                    if oppose:
                        return False, (
                            "connected readings hold EVIDENCE_PREFERRED "
                            f"FVG {pref} ({reg.direction}) opposing the "
                            "intended direction (" + intended
                            + " from pid=" + str(pid) + " ctx=" + ctx_dir
                            + ") — recorded contradicting evidence; "
                            "the attempt is held while this holds")
        if rt is not None and rt.conclusion:
            st = rt.conclusion.get("status")
            if st == "UNRESOLVED_NO_EDGE":
                return True, ("connected readings UNRESOLVED: plan "
                              "attempt allowed as PROVISIONAL baseline "
                              "only if the plan-layer definitions "
                              "themselves resolve")
        return True, "connected readings do not contradict"

    def gate_b0(dec, study) -> tuple:
        """BASELINE B0 (explicitly defined simple baseline): act on
        every strict decision preference WITHOUT consulting the
        connected readings.  Same plan definitions, same fills, same
        costs — only the connected gate differs."""
        if dec.primary_is_baseline or dec.state in ("NO_EDGE",
                                                    "UNRESOLVED"):
            return False, ("decision has no strict evidence-supported "
                           "preference: " + dec.state)
        return True, ("B0 baseline: connected readings NOT consulted")

    gate = {"v1": gate_v1, "b0": gate_b0}[args.get("gate", "v1")]

    while not loop.stream.exhausted:
        r = loop.step_completed_bar()
        if r.trigger != "task-boundary" or loop.last_record is None:
            continue
        rec = loop.last_record
        if decision_seq % 500 == 0:
            print(f"  … {decision_seq} task boundaries "
                  f"({rec.as_of_time}) cases={len(cases)} "
                  f"t={time.time() - t_start:.0f}s", flush=True)
        decision_seq += 1
        # dev: training episodes are extracted at EVERY task boundary.
        # CHRONOLOGICAL PROTOCOL (no label-window overlap): at the
        # decision at time T the model contains ONLY episodes whose
        # label windows CLOSED strictly before T.  Labels use future
        # bars and are never features.  ALL decision cases and plan
        # events are recorded at EVERY boundary.  The FK world is
        # computed lazily ONLY where a plan needs it.
        if phase == "dev":
            ep = extractor.extract(rec, run_id=phase, seq=decision_seq)
            episodes.append(ep)
            pending_eps.append(ep)
            t_now = pd.Timestamp(rec.as_of_time)
            ready = [e for e in pending_eps
                     if e.window_end_time is not None
                     and pd.Timestamp(e.window_end_time) < t_now]
            if ready:
                model.fit(ready)
                for e in ready:
                    pending_eps.remove(e)
        dec = decide(record=rec, model=model, decision_seq=decision_seq)
        gate_stats["decisions"] += 1
        strict = not (dec.primary_is_baseline
                      or dec.state in ("NO_EDGE", "UNRESOLVED"))
        gate_stats["strict_pref"] += int(strict)
        ok, gate_reason = gate(dec, study)
        gate_stats["gate_pass"] += int(ok and strict)

        def _world_now():
            fr = loop._prefix_frames()
            return resolve_world(frames=fr, record=rec, k=K,
                                 task_scale=TASK_SCALE,
                                 axis=loop.engine.axis)

        if active_plan is not None and active_plan.active:
            v = observe_plan(plan=active_plan, record=rec,
                             world=_world_now(),
                             frames=loop._prefix_frames(),
                             run_context="historical-replay",
                             decision_id=dec.decision_id,
                             task_scale=TASK_SCALE)
            if not active_plan.active:
                oc = outcome_for(active_plan, bidask,
                                 active_plan.current.direction,
                                 fill_mode=args.get("fill_mode",
                                                    "next_open"))
                case = {"kind": "plan", "plan": active_plan.to_record(),
                        "outcome": oc,
                        "decision_state": dec.state,
                        "gate_reason": active_plan.gate_reason}
                cases.append(case)
                plans.append(active_plan)
                active_plan = None
        elif ok and strict and active_plan is None:
            plan_seq += 1
            plan, reason = create_plan(
                record=rec, decision=dec, world=_world_now(),
                run_id=RUN_ID, seq=plan_seq,
                frames=loop._prefix_frames(),
                run_context="historical-replay",
                task_scale=TASK_SCALE, instrument="EURUSD")
            if plan is None:
                gate_stats["no_plan"] += 1
                cases.append({"kind": "no-plan",
                              "as_of": str(rec.as_of_time),
                              "decision_state": dec.state,
                              "gate_reason": gate_reason,
                              "missing_evidence":
                                  reason.get("missing_evidence")})
            else:
                plan.gate_reason = gate_reason
                gate_stats["plans_created"] += 1
                active_plan = plan
                cases.append({"kind": "plan-opened",
                              "as_of": str(rec.as_of_time),
                              "plan_id": plan.plan_id,
                              "scenario": plan.current.scenario,
                              "direction": plan.current.direction,
                              "gate_reason": gate_reason,
                              "components_origins":
                                  {k: {"definition_origin":
                                       c.definition_origin,
                                       "claim_class": c.claim_class}
                                   for k, c in
                                   build_components(
                                       scenario=plan.current.scenario)
                                   .items()}})
        elif not ok or not strict:
            gate_stats["no_plan"] += 1
            cases.append({"kind": "no-plan",
                          "as_of": str(rec.as_of_time),
                          "decision_state": dec.state,
                          "gate_reason": gate_reason})

    if active_plan is not None:
        oc = outcome_for(active_plan, bidask,
                         active_plan.current.direction,
                         fill_mode=args.get("fill_mode", "next_open"))
        cases.append({"kind": "plan", "plan": active_plan.to_record(),
                      "outcome": oc,
                      "decision_state": "open-at-data-end",
                      "gate_reason": getattr(active_plan, "gate_reason",
                                             "")})
        plans.append(active_plan)

    # ---- dev: fit the model ONLY on episodes whose label windows
    # complete strictly inside the dev period (no overlap with eval) ----
    if phase == "dev":
        dev_end = pd.Timestamp(t1, tz="UTC")
        usable = [e for e in pending_eps
                  if e.label is not None and e.exclusion_reason is None
                  and e.window_end_time is not None
                  and pd.Timestamp(e.window_end_time) <= dev_end]
        censored = [e for e in episodes if e.exclusion_reason]
        model.fit(usable)
        Path(args["model"]).write_text(json.dumps(
            model_state(model), indent=1))
        summary_extra = {
            "episodes_total": len(episodes),
            "episodes_fitted": model.n_episodes,
            "episodes_censored_or_excluded": len(censored),
            "label_windows_inside_dev": True,
            "trained_through": str(model.trained_through),
        }
    else:
        summary_extra = {"episodes_fitted": 0,
                         "note": "eval never trains"}

    ev = evaluate_plans(plans)
    summary = {
        "phase": phase, "window": [t0, t1],
        "gate": args.get("gate", "v1"),
        "fill_mode": args.get("fill_mode", "next_open"),
        "gate_stats": gate_stats,
        "plan_evaluation": ev,
        "cases_total": len(cases),
        "cases_by_kind": {k: sum(1 for c in cases if c["kind"] == k)
                          for k in sorted({c["kind"] for c in cases})},
        "outcomes": {k: sum(1 for c in cases
                            if c.get("outcome", {}).get("outcome") == k)
                     for k in sorted({c.get("outcome", {}).get("outcome")
                                      for c in cases
                                      if c.get("outcome")})},
        **summary_extra,
        "source_agreement": source_agreement(
            {k: c.to_record() for k, c in
             build_components(scenario="continuation").items()}),
        "limitations": [
            "selection_quality = NOT_ESTABLISHED",
            "research/paper record only — no live orders",
            "close-based hypothetical fills at ask/bid of the actual 5m "
            "quotes; commission NOT provided by this dataset (never "
            "invented); slippage not modeled",
            "same-bar level-touch ambiguity preserved as AMBIGUOUS",
        ],
    }
    (out_dir / f"cases_{phase}_{args.get('gate', 'v1')}.jsonl").write_text(
        "\n".join(json.dumps(c, default=str) for c in cases))
    (out_dir / f"summary_{phase}_{args.get('gate', 'v1')}.json").write_text(
        json.dumps(summary, indent=1, default=str))
    print(f"== {phase} done in {time.time() - t_start:.1f}s; "
          f"cases={len(cases)} gate={gate_stats} ==", flush=True)
    print(json.dumps(summary["outcomes"], indent=1), flush=True)
    return 0


def model_state(model):
    """Serialize the ContextEventModel deterministically."""
    return {"kind": "context-event-model-v1",
            "counts": [[list(k), v] for k, v in model.counts.items()],
            "n_episodes": model.n_episodes,
            "trained_through": str(model.trained_through)
            if model.trained_through is not None else None}


def pause_and_step(args) -> int:
    """Pause-and-step excerpt on a DISCLOSED window."""
    t0, t1 = args["from"], args["to"]
    bidask = load_bidask(Path(args["bidask_dir"]), t0, t1)
    rows = mid_rows(bidask)
    stream = ReplayObservationStream(
        rows.copy(), timeline_id="EURUSD_1m_fx_intraday_v1",
        dataset_identity="dukascopy-eurusd-5m-bidask@56d5f04")
    study = StudyReasoningLayer(run_id=RUN_ID, k=K,
                                task_scale=TASK_SCALE,
                                instrument="EURUSD")
    loop = MonitoringLoop(
        stream=stream, frames_builder=frames_builder,
        engine_factory=engine_factory(), task_scale=TASK_SCALE,
        study_layer=study, readings_scale=READINGS_SCALE)
    pause = pd.Timestamp(args["pause_at"], tz="UTC")
    while not loop.stream.exhausted:
        loop.step_observation()
        if loop.last_record is not None and \
                pd.Timestamp(loop.last_record.as_of_time) >= pause:
            break
    print(f"== PAUSE at {loop.last_record.as_of_time} (window "
          f"{t0}->{t1} disclosed; pause demo-chosen) ==", flush=True)
    cr = study.readings
    hf = study.hf_context
    print(f"[context] hf trend={hf.get('trend')} established_at="
          f"{hf.get('established_at')}", flush=True)
    print(f"[references] confirmed refs used by readings: "
          f"{len(study._last_ref_records)}", flush=True)
    print(f"[FVG regions] {len(cr.regions)} "
          f"(by tf: " + str({tf: sum(1 for r in cr.regions.values()
                                     if r.timeframe == tf)
                            for tf in sorted({r.timeframe
                                              for r in cr.regions.values()})})
          + ")", flush=True)
    for tid, t in cr.tasks.items():
        c = t.conclusion or {}
        supp = t.comparison.get("by_support_count") \
            if t.comparison else None
        print(f"[task {tid}] {c.get('status')} preferred="
              f"{c.get('preferred')} candidates={len(t.candidates)} "
              f"comparison={supp}", flush=True)
    print(f"[shift watches] {len(study.shift_watches)}", flush=True)
    for w in study.shift_watches:
        print(f"  {w.watch_id} [{w.status}] crossing={w.crossing}",
              flush=True)
    for n in range(args["step"]):
        if loop.stream.exhausted:
            break
        before = {tid: len(t.versions) for tid, t in cr.tasks.items()}
        r = loop.step_completed_bar()
        print(f"\n-- step {n + 1}: {loop.last_record.as_of_time} "
              f"(trigger={r.trigger}) --", flush=True)
        for tid, t in cr.tasks.items():
            chg = len(t.versions) - before.get(tid, 0)
            if chg:
                v = t.versions[-1]
                print(f"  task {tid} NEW version v{v['version']}: "
                      f"{v['conclusion']['status']} preferred="
                      f"{v['conclusion']['preferred']}", flush=True)
            else:
                print(f"  task {tid}: no change (honest)", flush=True)
        for i in cr.interps.values():
            if i.revision_count:
                print(f"  interpretation {i.interp_id}: "
                      f"{i.revision_count} revision(s); latest: "
                      f"{i.versions[-1]['reason']}", flush=True)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bidask-dir", required=True)
    ap.add_argument("--phase", choices=["dev", "eval", "pause"],
                    required=True)
    ap.add_argument("--from", dest="from", required=True)
    ap.add_argument("--to", dest="to", required=True)
    ap.add_argument("--model", default=None)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--pause-at", default=None)
    ap.add_argument("--step", type=int, default=3)
    ap.add_argument("--gate", choices=["v1", "b0"], default="v1",
                    help="v1 = connected gate; b0 = explicitly defined "
                         "simple baseline (no connected gate)")
    ap.add_argument("--fill-mode", choices=["next_open", "bar_close"],
                    default="next_open",
                    help="next_open (DEFAULT, causal): both legs fill "
                         "at the next 5m bar open after their events; "
                         "bar_close: EXPLICITLY LABELED NON-CAUSAL "
                         "comparison mode (event bar close)")
    args = vars(ap.parse_args(argv))
    if args["phase"] == "pause":
        return pause_and_step(args)
    if args["phase"] == "dev" and not args["model"]:
        args["model"] = str(Path(args["out_dir"]) / "dev_model.json")
    return run_phase(args, args["phase"])


if __name__ == "__main__":
    sys.exit(main())
