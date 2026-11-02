"""Huddleston-study link tests (causal test battery A–H):

  A  the same local candidate shape under two different higher-frame
     contexts produces different ROLE conclusions (trend vs
     reaction/pause) — labeled geometric/synthetic;
  B  a candidate is not confirmed before its evidence exists and the
     engine never back-fills confirmation into the formation moment
     (state machine + ledger-recorded transitions);
  C  when two events could both have occurred inside one bar and OHLC
     cannot order them, the state remains undecided and the flattering
     order is refused until finer data resolves it (and unresolved it
     stays UNKNOWN);
  D  time provenance + revocable selection: the session-scoped 9:30/9:31
     first-gap convention revokes the 9:30 selection as a CORRECTION
     (original preserved, never a fulfilled prediction) and the engine
     runs without the convention;
  E  a higher-frame hypothesis whose failure reference is crossed
     SUSPENDS and demands more information — it is NOT flipped into an
     automatic opposite hypothesis;
  F  when two structural candidates cannot be discriminated by the
     available evidence the engine reports the non-resolution, reasons,
     and the discriminating evidence needed — and forces no pick;
  G  saving state and resuming in a NEW process equals the continuous
     run (study layer included);
  H  appending observations after T cannot change the study state
     recorded at T (post-T invariance / immutable past).

All scenes are labeled SYNTHETIC/GEOMETRIC (handcrafted OHLC).  Test
success is NOT market truth: ``selection_quality = NOT_ESTABLISHED``.
"""

import json
import os
import subprocess
import sys
import textwrap

import pandas as pd
import pytest

from trading_system.research.contextual_selection.csm import (
    InterpretationLedger,
)
from trading_system.research.contextual_selection.monitoring import (
    MonitoringLoop,
    ReplayObservationStream,
)
from trading_system.research.contextual_selection.analysis_lifecycle import (
    AnalysisEngine,
)
from trading_system.research.contextual_selection.study_links import (
    ROLE_REACTION_PAUSE,
    ROLE_TREND,
    ROLE_UNDETERMINED,
    STATE_AWAITING_CONFIRMATION,
    STATE_CANDIDATE,
    STATE_CONFIRMED,
    UNKNOWN_ORDERING,
    US_INDEX_FIRST_GAP_SESSION_CLOCK,
    HigherFrameHypothesis,
    OBLikeCandidate,
    StudyReasoningLayer,
    TimeProvenanceSelection,
    assign_role,
    load_corpus,
)


# ------------------------------------------------------------------ #
# synthetic scene helpers (SYNTHETIC/GEOMETRIC — not market claims)   #
# ------------------------------------------------------------------ #
def _bars(rows):
    """rows: [(day, o, h, l, c), ...] -> 4h UTC frame."""
    idx = pd.date_range("2025-09-01", periods=len(rows), freq="4h",
                        tz="UTC")
    return pd.DataFrame(
        [{"open": o, "high": h, "low": lo, "close": c, "volume": 1.0}
         for (_, o, h, lo, c) in rows], index=idx)


class _Interp:
    def __init__(self, direction):
        self.interpretation_id = "I-primary"
        self.data = {"direction": direction}
        self.state = "PLAUSIBLE"


class _Rec:
    """Minimal analysis-record shim for the study layer."""

    def __init__(self, as_of_bar, as_of_time, direction=None):
        self.as_of_bar = as_of_bar
        self.as_of_time = as_of_time
        self.interpretations = ([_Interp(direction)]
                                if direction else [])
        self.structural_facts = []


def _run_boundaries(layer, bars, upto, ledger=None, direction=None,
                    start=0):
    out = []
    for j in range(start, upto + 1):
        rec = _Rec(j, pd.Timestamp(bars.index[j]), direction)
        out.extend(layer.on_boundary(rec, {"4h": bars}, ledger))
    return out


# scene: swing low 100 at bar 3 (confirmable at bar 5), then a return:
# bar 10 is a down-close bar near 100 (candidate), bar 12 gaps through
# the candidate high WITHOUT returning to the zone (clean confirmation).
SCENE_CONFIRM = [
    (0, 110.0, 110.5, 108.0, 108.5),   # 0
    (1, 108.5, 109.0, 105.0, 105.5),   # 1
    (2, 105.5, 106.0, 101.0, 101.5),   # 2
    (3, 101.5, 102.0, 100.0, 101.0),   # 3  swing low 100
    (4, 101.0, 104.0, 100.8, 103.5),   # 4
    (5, 103.5, 106.5, 103.0, 106.0),   # 5  <- low confirmed here
    (6, 106.0, 108.5, 105.5, 108.0),   # 6
    (7, 108.0, 111.5, 107.5, 111.0),   # 7
    (8, 111.0, 111.5, 107.0, 107.5),   # 8
    (9, 107.5, 108.0, 103.5, 104.0),   # 9
    (10, 104.0, 104.5, 100.4, 100.8),  # 10 candidate: down-close near 100
    (11, 100.8, 102.0, 100.6, 101.8),  # 11 still no trade-through
    (12, 105.0, 105.6, 104.8, 105.2),  # 12 high > cand.high -> CONFIRMS
    (13, 105.2, 106.0, 103.8, 104.5),  # 13
]

# same, but bar 12 spans BOTH the confirm level and the zone low in one
# bar (order unresolvable from OHLC).
SCENE_AMBIGUOUS = SCENE_CONFIRM[:12] + [
    (12, 101.0, 105.2, 100.0, 104.0),  # 12 both events possible
    (13, 105.2, 106.0, 103.8, 104.5),  # 13
]


# ------------------------------------------------------------------ #
# A  same shape, two higher-frame contexts -> different roles          #
# ------------------------------------------------------------------ #
def test_A_same_shape_two_contexts_roles_differ_synthetic_geometric():
    """SYNTHETIC/GEOMETRIC — labeled synthetic data, not a market
    claim.  A bearish-looking candidate (up-close near resistance)
    under a bullish higher-frame context is NOT a trend sell reference
    but remains a legitimate reaction/pause reference; under a bearish
    context it may be the trend reference.  Never auto-rejected."""
    shape = dict(candidate_id="OBC-X-1", direction="bearish",
                 bar_index=10, bar_time=pd.Timestamp("2025-09-01"),
                 open=101.0, high=102.0, low=100.9, close=101.8,
                 context_ref_id="PS-high-1", context_ref_level=102.0)
    cand_up = OBLikeCandidate(**shape)
    cand_dn = OBLikeCandidate(**shape)

    v_up = assign_role(candidate_direction="bearish", hf_trend="up",
                       task="trend-continuation")
    v_dn = assign_role(candidate_direction="bearish", hf_trend="down",
                       task="trend-continuation")

    # different contexts -> different roles (evidence-supported)
    assert v_up["role"] == ROLE_REACTION_PAUSE
    assert v_dn["role"] == ROLE_TREND
    # OB16-A 25:00-25:43: context rejection is about the SELL-CUE role,
    # not about destroying the reference — it stays monitored
    assert "NOT assigned" in v_up["reasons"][0]
    assert any("reaction/pause" in r for r in v_up["reasons"])
    # explicit non-rejection invariant
    assert v_up["role"] in (ROLE_TREND, ROLE_REACTION_PAUSE,
                            ROLE_UNDETERMINED)
    # alternatives and change conditions are recorded, not hidden
    assert v_up["alternatives"] and v_dn["alternatives"]
    assert v_up["would_change"] and v_dn["would_change"]

    # the same conclusions attach to the candidate record itself
    cand_up.role_assignments.append(v_up)
    cand_dn.role_assignments.append(v_dn)
    assert cand_up.role_assignments[0]["task"] == \
        cand_dn.role_assignments[0]["task"] == "trend-continuation"
    assert cand_up.role_assignments[0]["reasons"] != \
        cand_dn.role_assignments[0]["reasons"]


# ------------------------------------------------------------------ #
# B  candidate before evidence; no back-filled confirmation            #
# ------------------------------------------------------------------ #
def test_B_candidate_before_evidence_no_backfill():
    bars = _bars(SCENE_CONFIRM)
    layer = StudyReasoningLayer(run_id="tB", k=2, task_scale="4h")
    ledger = InterpretationLedger()

    # through bar 9: no candidate yet (the swing is confirmed, but no
    # candidate-shaped bar has appeared)
    _run_boundaries(layer, bars, 9, ledger, direction="up")
    assert layer.candidates == []

    # bar 10: candidate forms -> AWAITING, never confirmed at formation
    _run_boundaries(layer, bars, 10, ledger, direction="up", start=10)
    assert len(layer.candidates) == 1
    c = layer.candidates[0]
    assert c.state in (STATE_CANDIDATE, STATE_AWAITING_CONFIRMATION)
    assert all(e["to"] != STATE_CONFIRMED for e in c.events
               if e["kind"] == "state_transition")
    assert c.bar_index == 10

    # bar 11: still no confirmation evidence
    _run_boundaries(layer, bars, 11, ledger, direction="up", start=11)
    assert c.state == STATE_AWAITING_CONFIRMATION

    # bar 12 trades through -> CONFIRMED, with the transition recorded
    # AT the evidence bar (bar 12), NOT at formation (bar 10)
    _run_boundaries(layer, bars, 12, ledger, direction="up", start=12)
    assert c.state == STATE_CONFIRMED
    transitions = [e for e in c.events if e["kind"] == "state_transition"]
    conf = [e for e in transitions if e["to"] == STATE_CONFIRMED]
    assert len(conf) == 1
    assert conf[0]["at_bar"] == 12          # evidence bar
    assert conf[0]["from"] == STATE_AWAITING_CONFIRMATION
    assert conf[0]["evidence"]["bar"] == 12
    assert c.bar_index == 10                # formation moment unchanged
    assert all(e["at_bar"] <= 12 for e in transitions)

    # the transitions reached the EXISTING ledger with a revision chain
    entries = [r for r in ledger.results
               if r.task_id == "T-STUDY-CANDIDATE"]
    assert entries, "state machine transitions must be ledger-recorded"
    assert any(p.get("kind") == "study_candidate_state"
               for p in ledger._payloads.values())
    # sequence separation: candidate formed AFTER hf context
    kinds = [f["kind"] for f in layer.seq_facts]
    assert kinds.index("HF_CONTEXT_ESTABLISHED") < \
        kinds.index("CANDIDATE_FORMED")


# ------------------------------------------------------------------ #
# C  same-bar ambiguity -> undecided; finer data may resolve           #
# ------------------------------------------------------------------ #
def test_C_same_bar_ordering_unknown_until_finer_data():
    bars = _bars(SCENE_AMBIGUOUS)
    layer = StudyReasoningLayer(run_id="tC", k=2, task_scale="4h")
    ledger = InterpretationLedger()
    _run_boundaries(layer, bars, 11, ledger, direction="up")
    c = layer.candidates[0]

    # bar 12 contains both possible events -> ordering UNKNOWN, no
    # confirmation granted (the flattering order is refused)
    _run_boundaries(layer, bars, 12, ledger, direction="up", start=12)
    assert c.ordering == UNKNOWN_ORDERING
    assert c.state != STATE_CONFIRMED
    assert c.ambiguous_bar == 12
    assert any(e["kind"] == "ordering_unresolved" for e in c.events)

    # finer 1m data resolves: confirm touch happens FIRST
    t0 = pd.Timestamp(bars.index[12])
    layer.on_observation({"time": t0 + pd.Timedelta(minutes=5),
                          "open": 104.9, "high": 105.2, "low": 104.6,
                          "close": 105.0})
    layer.on_observation({"time": t0 + pd.Timedelta(minutes=40),
                          "open": 102.0, "high": 102.1, "low": 99.9,
                          "close": 100.5})
    assert c.ordering == "confirmation-first"
    assert c.state == STATE_CONFIRMED
    assert any(e["kind"] == "ordering_resolved_by_finer_data"
               for e in c.events)

    # second scene: the reverse order must NOT confirm
    bars2 = _bars(SCENE_AMBIGUOUS)
    layer2 = StudyReasoningLayer(run_id="tC2", k=2, task_scale="4h")
    _run_boundaries(layer2, bars2, 12, InterpretationLedger(),
                    direction="up")
    c2 = layer2.candidates[0]
    assert c2.ordering == UNKNOWN_ORDERING
    layer2.on_observation({"time": t0 + pd.Timedelta(minutes=5),
                           "open": 102.0, "high": 102.1, "low": 99.9,
                           "close": 100.5})
    layer2.on_observation({"time": t0 + pd.Timedelta(minutes=40),
                           "open": 104.9, "high": 105.2, "low": 104.6,
                           "close": 105.0})
    assert c2.ordering == "revisit-first"
    assert c2.state != STATE_CONFIRMED     # never the flattering order

    # if even the fine bar cannot order both events, ordering stays
    # UNKNOWN and no confirmation is granted
    bars3 = _bars(SCENE_AMBIGUOUS)
    layer3 = StudyReasoningLayer(run_id="tC3", k=2, task_scale="4h")
    _run_boundaries(layer3, bars3, 12, InterpretationLedger(),
                    direction="up")
    c3 = layer3.candidates[0]
    layer3.on_observation({"time": t0 + pd.Timedelta(minutes=30),
                           "open": 102.0, "high": 105.2, "low": 99.9,
                           "close": 102.5})
    assert c3.ordering == UNKNOWN_ORDERING
    assert c3.state != STATE_CONFIRMED


# ------------------------------------------------------------------ #
# D  time provenance + revocable selection (session-scoped clock)      #
# ------------------------------------------------------------------ #
def test_D_time_provenance_revocation_is_correction_not_prediction():
    # full time provenance is carried on the selection itself
    sel = TimeProvenanceSelection(
        selection_id="SEL-FVG24-1", subject_id="first-gap-0930",
        selected_at=pd.Timestamp("2024-09-16 13:30", tz="UTC"),
        timezone="UTC (platform display UTC-5)",
        bar_convention="1-minute chart as displayed",
        timeframe="1m",
        eligibility={"window": "F1", "reason": "first gap after open",
                     "known_at": "2024-09-16 13:30 UTC"})
    rec = sel.to_record()
    for key in ("selected_at", "timezone", "bar_convention", "timeframe",
                "eligibility"):
        assert rec[key] is not None

    # the session-scoped convention (9:30 excluded, 9:31+ eligible)
    clock = US_INDEX_FIRST_GAP_SESSION_CLOCK
    start = pd.Timestamp("2024-09-16 13:30", tz="UTC")
    assert clock.eligible_at(start, start) is False
    assert clock.eligible_at(start + pd.Timedelta(minutes=1), start)
    assert "session" in clock.scope.lower() or "NOT global" in clock.scope

    # revocation: correction semantics, original preserved
    corr = sel.revoke(
        reason="FVG24-A ~75:02: the 9:30 candle cannot be the first "
               "qualifying gap under the stated convention",
        evidence=["'You can't be on your 9.30 candle, it can only "
                  "appear at 9.31 or after' (FVG24-A, DIRECT_STATEMENT)"],
        revised_to="first-gap-0931")
    assert sel.status == "REVOKED"
    assert corr["original"]["subject_id"] == "first-gap-0930"
    assert "NOT a fulfilled prediction" in corr["note"]
    assert "correction" in corr["note"]
    assert corr["revised_to"] == "first-gap-0931"

    # a suspension-style revocation keeps the original as well
    sel2 = TimeProvenanceSelection(
        selection_id="SEL-FVG24-2", subject_id="gap-x",
        selected_at=start, timezone="UTC",
        bar_convention="1m", timeframe="1m", eligibility={})
    corr2 = sel2.revoke(reason="eligibility removed by new information",
                        evidence=["observed later fact"], revised_to=None)
    assert sel2.status == "SUSPENDED"
    assert corr2["original"]["subject_id"] == "gap-x"

    # the engine runs WITHOUT the convention: it is optional
    plain = StudyReasoningLayer(run_id="tD", k=2, task_scale="4h")
    assert plain.session_clock is None
    bars = _bars(SCENE_CONFIRM)
    _run_boundaries(plain, bars, 12, InterpretationLedger(),
                    direction="up")
    assert plain.candidates, "engine runs fine with no clock rule"


# ------------------------------------------------------------------ #
# E  hypothesis suspension — never an automatic opposite               #
# ------------------------------------------------------------------ #
def test_E_hypothesis_suspends_never_flips():
    hyp = HigherFrameHypothesis(
        hypothesis_id="HYP-E12-1",
        statement="the reference high is expected to hold",
        failure_reference_level=115000.0,
        failure_reference_id="PS-high-ref",
        failure_side="up")

    # below the failure reference: still active
    ev = hyp.review(bar_time=pd.Timestamp("2025-09-10"),
                    bar_high=114800, bar_low=113000, bar_close=114000)
    assert ev is None and hyp.status == "ACTIVE"

    # crossing the failure reference -> SUSPENDED + demand more info
    ev = hyp.review(bar_time=pd.Timestamp("2025-09-11"),
                    bar_high=116000, bar_low=114000, bar_close=115500)
    assert ev is not None
    assert hyp.status == "SUSPENDED"
    assert "demand more information" in ev["reason"]
    assert "no automatic opposite hypothesis" in ev["reason"]

    # E12-A semantics: suspension is not reversal — no opposite
    # hypothesis is ever generated by the review path
    layer = StudyReasoningLayer(run_id="tE", k=2, task_scale="4h")
    layer.hypotheses.append(hyp)
    before = len(layer.hypotheses)
    hyp.review(bar_time=pd.Timestamp("2025-09-12"),
               bar_high=117000, bar_low=115000, bar_close=116500)
    assert len(layer.hypotheses) == before
    assert all(h.hypothesis_id == "HYP-E12-1" for h in layer.hypotheses)
    assert hyp.status == "SUSPENDED"      # no second activation


# ------------------------------------------------------------------ #
# F  non-discrimination -> no forced pick, reasons recorded            #
# ------------------------------------------------------------------ #
def test_F_no_forced_pick_on_insufficient_evidence():
    # two candidates of identical shape; no established hf context:
    # the evidence does not justify preferring one
    def mk(cid):
        return OBLikeCandidate(
            candidate_id=cid, direction="bullish", bar_index=10,
            bar_time=pd.Timestamp("2025-09-01"), open=104, high=104.5,
            low=100.4, close=100.8, context_ref_id="PS-low-A",
            context_ref_level=100.0)

    a, b = mk("OBC-F-1"), mk("OBC-F-2")
    verdicts = [assign_role(candidate_direction=c.direction,
                           hf_trend="unknown", task="trend-continuation")
                for c in (a, b)]
    for v in verdicts:
        assert v["role"] == ROLE_UNDETERMINED
        assert v["reasons"], "non-resolution must state reasons"
        assert v["discriminating_evidence_needed"], \
            "must state what evidence would discriminate"

    # the layer records both candidates (no silent drop) and forces no
    # selection between them
    layer = StudyReasoningLayer(run_id="tF", k=2, task_scale="4h")
    bars = _bars(SCENE_CONFIRM)
    # two swing lows so two candidates can form — use the shared scene
    # but inject both candidates through the scan path by appending a
    # second identical candidate bar
    scene2 = list(SCENE_CONFIRM) + [
        (14, 104.5, 105.0, 100.3, 100.7),  # second candidate bar
    ]
    bars2 = _bars(scene2)
    _run_boundaries(layer, bars2, 14, InterpretationLedger())
    # without hf context: every role stays UNDETERMINED, all candidates
    # remain recorded
    assert layer.candidates, "candidates must be recorded"
    assert all(c.role == ROLE_UNDETERMINED for c in layer.candidates)
    assert all(c.state != "rejected" for c in layer.candidates)
    # no auto-selection concept exists: nothing marks one candidate as
    # chosen over the other
    assert not any("selected" == c.state for c in layer.candidates)


# ------------------------------------------------------------------ #
# G  save/resume in a NEW process == continuous run                    #
# ------------------------------------------------------------------ #
def _frames_builder(rows):
    r4 = rows.resample("4h").agg({"open": "first", "high": "max",
                                  "low": "min", "close": "last",
                                  "volume": "sum"}).dropna(
        subset=["open"])
    r4.index = r4.index + pd.Timedelta(hours=4)
    return {"4h": r4, "1h": rows, "15m": rows}


def _stream(rows):
    return ReplayObservationStream(rows, timeline_id="TEST_STUDY",
                                   dataset_identity="synthetic-study")


def test_G_save_resume_new_process_equals_continuous(tmp_path):
    # SYNTHETIC 1m rows feeding the real MonitoringLoop + study layer
    import math
    idx = pd.date_range("2025-09-01 00:00", periods=13 * 240,
                        freq="1min", tz="UTC")

    def px(i):
        return 100.0 + 2.0 * math.sin(i / 500.0)

    rows = pd.DataFrame(
        [{"timestamp": t, "open": px(i), "high": px(i) + 0.4,
          "low": px(i) - 0.4, "close": px(i) + 0.1,
          "volume": 1.0} for i, t in enumerate(idx)])
    rows = rows.set_index("timestamp")
    rows_path = tmp_path / "rows.csv"
    rows.to_csv(rows_path)

    def factory(frames):
        return AnalysisEngine(run_id="g", frames=frames, k=2)

    # continuous in this process: stop at T, save, then continue
    cont = MonitoringLoop(
        stream=_stream(rows.copy()), frames_builder=_frames_builder,
        engine_factory=factory, task_scale="4h",
        study_layer=StudyReasoningLayer(run_id="g", k=2))
    cont.run_to(pd.Timestamp("2025-09-02 04:00", tz="UTC"))
    state_path = tmp_path / "state.json"
    cont.save_state(str(state_path))
    state_at_T = json.loads(json.dumps(cont.state_dict(), default=str))
    cont.run_to(pd.Timestamp("2025-09-03 04:00", tz="UTC"))
    cont_state = json.loads(json.dumps(cont.state_dict(), default=str))
    assert cont_state["study_state"] is not None

    # fresh process: resume and continue one more step
    out_path = tmp_path / "out.json"
    script = textwrap.dedent(f"""
        import json, sys
        sys.path.insert(0, {str(sys.path[0])!r})
        import pandas as pd
        from trading_system.research.contextual_selection.monitoring import (
            MonitoringLoop, ReplayObservationStream)
        from trading_system.research.contextual_selection.analysis_lifecycle import (
            AnalysisEngine)
        from trading_system.research.contextual_selection.study_links import (
            StudyReasoningLayer)

        def frames_builder(rows):
            r4 = rows.resample("4h").agg({{"open": "first", "high": "max",
                                 "low": "min", "close": "last",
                                 "volume": "sum"}}).dropna(subset=["open"])
            r4.index = r4.index + pd.Timedelta(hours=4)
            return {{"4h": r4, "1h": rows, "15m": rows}}

        def engine_factory(frames):
            return AnalysisEngine(run_id="g", frames=frames, k=2)

        rows = pd.read_csv({str(rows_path)!r}, parse_dates=["timestamp"],
                           index_col="timestamp")
        if rows.index.tz is None:
            rows.index = rows.index.tz_localize("UTC")
        stream = ReplayObservationStream(rows, timeline_id="TEST_STUDY",
                                         dataset_identity="synthetic-study")
        loop = MonitoringLoop.load_state(
            {str(state_path)!r}, stream=stream,
            frames_builder=frames_builder, engine_factory=engine_factory,
            task_scale="4h",
            study_layer=StudyReasoningLayer(run_id="g", k=2))
        resumed_study = loop.state_dict()["study_state"]
        loop.run_to(pd.Timestamp("2025-09-04 04:00", tz="UTC"))
        with open({str(out_path)!r}, "w") as fh:
            json.dump({{"resumed_study": resumed_study,
                       "continued_study": loop.state_dict()["study_state"]}},
                      fh, default=str)
    """)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = dict(os.environ,
               PYTHONPATH=os.pathsep.join([os.path.join(root, "src"),
                                           root]))
    proc = subprocess.run([sys.executable, "-c", script],
                          capture_output=True, text=True, env=env,
                          cwd=root)
    assert proc.returncode == 0, proc.stderr
    out = json.loads(out_path.read_text())
    # the fresh process resumed the SAME study state at T...
    assert json.dumps(out["resumed_study"], sort_keys=True,
                      default=str) == \
        json.dumps(state_at_T["study_state"], sort_keys=True,
                   default=str)
    # ...and its continuation equals the continuous run's study state
    assert json.dumps(out["continued_study"], sort_keys=True,
                      default=str) == \
        json.dumps(cont_state["study_state"], sort_keys=True,
                   default=str)


# ------------------------------------------------------------------ #
# H  post-T invariance: appending cannot change state at T             #
# ------------------------------------------------------------------ #
def test_H_post_T_invariance():
    bars = _bars(SCENE_CONFIRM)
    # run A: stops at T=11
    layerA = StudyReasoningLayer(run_id="tH", k=2, task_scale="4h")
    _run_boundaries(layerA, bars, 11, InterpretationLedger(),
                    direction="up")
    snap_A = json.dumps(layerA.state_dict(), sort_keys=True, default=str)

    # run B: identical up to T, then keeps going
    layerB = StudyReasoningLayer(run_id="tH", k=2, task_scale="4h")
    _run_boundaries(layerB, bars, 11, InterpretationLedger(),
                    direction="up")
    snap_B_at_T = json.dumps(layerB.state_dict(), sort_keys=True,
                             default=str)
    assert snap_A == snap_B_at_T

    _run_boundaries(layerB, bars, 13, InterpretationLedger(),
                    direction="up", start=12)
    # later state evolved (candidate confirmed)...
    assert layerB.candidates[0].state == STATE_CONFIRMED
    # ...but the events recorded AT OR BEFORE T are unchanged, and the
    # run that stopped at T still shows exactly its own T-time state
    events_up_to_T = [e for e in layerB.candidates[0].events
                      if pd.Timestamp(e.get("at", e.get(
                          "bar_time", "2020-01-01")))
                      <= pd.Timestamp(bars.index[11])]
    assert len(events_up_to_T) == len(layerA.candidates[0].events)
    assert layerA.candidates[0].state != STATE_CONFIRMED  # frozen at T
    # the T-time snapshot is recoverable and untouched by later steps
    assert json.dumps(layerA.state_dict(), sort_keys=True,
                      default=str) == snap_A


# ------------------------------------------------------------------ #
# corpus + register integrity (source-linked expectations)            #
# ------------------------------------------------------------------ #
def test_corpus_loads_and_claims_are_classed():
    corpus = load_corpus()
    ids = [e["id"] for e in corpus["examples"]]
    assert {"E03-A", "E03-B", "E12-A", "OB16-A", "FVG16-A",
            "FVG24-A"} <= set(ids)
    # all six examples are DEVELOPMENT material
    assert all(e["split"] == "DEVELOPMENT" for e in corpus["examples"])
    # the held-out episode was never inspected / transcribed / used
    ho = corpus["held_out"]
    assert ho["split"] == "HELD_OUT"
    assert ho["source_id"] == "YT_tpPtItWqmlg"
    assert "No audio transcript" in ho["access"]
    assert "out of tuning" in ho["access"]
    # every classed claim carries a class from the declared vocabulary
    allowed = set(corpus["claim_classes"])
    assert allowed == {"DIRECT_STATEMENT", "PARAPHRASE",
                       "ENGINEERING_INTERPRETATION",
                       "RESEARCH_HYPOTHESIS",
                       "UNSUPPORTED_OR_UNAVAILABLE"}

    def walk(obj):
        if isinstance(obj, dict):
            if "class" in obj and isinstance(obj.get("text"), str):
                assert obj["class"] in allowed, obj
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)

    for e in corpus["examples"]:
        walk(e)
    # the amendment is recorded (E03-B general application NOT settled)
    ams = corpus.get("amendments", [])
    amd = [a for a in ams
           if a.get("amendment_id") == "AMD-01-E03B-DESCRIPTION"]
    assert amd, "AMD-01-E03B-DESCRIPTION must be recorded"
    assert "hypothetical" in amd[0]["corrected_description"]
    assert "NOT" in amd[0]["corrected_description"]
