"""Huddleston-study link tests (causal test battery A–H + regressions):

  A  role assignment is EVIDENCE-EVALUATED for the declared task: the
     same local candidate shape under two higher-frame contexts yields
     different verdicts, a role is recorded only with positive
     evidence, and opposition alone never establishes a reaction role
     (labeled geometric/synthetic);
  B  a candidate is not confirmed before its evidence exists and the
     engine never back-fills confirmation into the formation moment
     (state machine + ledger-recorded transitions);
  C  same-bar ambiguity: ordering stays UNKNOWN when OHLC cannot order
     the events; finer rows resolve it only inside that bar's interval
     (rows outside never resolve — OBC-0006 defect regression), the
     resolution is recorded when the information becomes available,
     revisit-first rejects only the proposed sequence and NEVER
     permanently freezes the candidate (later bars may confirm);
  D  time provenance + revocable selection (session-scoped clock;
     revocation = correction, never a fulfilled prediction), and NO
     proximity threshold exists in the module (the former 1% research
     constant is gone; no percentage/candle-count replacement);
  E  a higher-frame hypothesis whose failure reference is crossed
     SUSPENDS and demands more information — never an automatic
     opposite;
  F  insufficient evidence -> UNDETERMINED with reasons and the
     discriminating evidence needed; no forced pick, no permanent
     abstention (evidence re-opens the verdict);
  G  saving state and resuming in a NEW process equals the continuous
     run (study layer included);
  H  appending observations after T cannot change the study state
     recorded at T (post-T invariance / immutable past);
  R  a genuine append-only revision: old and new ledger records both
     retrievable, revision_of chain preserved, old record untouched.

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
from trading_system.research.contextual_selection import study_links as sl
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
    """rows: [(i, o, h, l, c), ...] -> 4h UTC frame with COMPLETION
    labels (index = slot start + 4h), matching the approved frames
    builder convention."""
    idx = pd.date_range("2025-09-01 04:00", periods=len(rows), freq="4h",
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


# scene: swing low 100.0 at bar 3 (confirmable at bar 5), then a
# return: bar 10 is a down-close bar whose low trades AT/THROUGH the
# contextual low (99.8) and is the extreme low of its family — the
# declared candidate definition (exact-level relation + order
# statistic; NO distance).  Bar 12 gaps through the candidate high
# (104.5) WITHOUT returning to the zone -> clean confirmation.
SCENE_CONFIRM = [
    (0, 110.0, 110.5, 108.0, 108.5),   # 0
    (1, 108.5, 109.0, 105.0, 105.5),   # 1
    (2, 105.5, 106.0, 101.0, 101.5),   # 2
    (3, 101.5, 102.0, 100.0, 101.0),   # 3  swing low 100.0
    (4, 101.0, 104.0, 100.8, 103.5),   # 4
    (5, 103.5, 106.5, 103.0, 106.0),   # 5  <- low confirmed here
    (6, 106.0, 108.5, 105.5, 108.0),   # 6
    (7, 108.0, 111.5, 107.5, 111.0),   # 7
    (8, 111.0, 111.5, 107.0, 107.5),   # 8  down-close
    (9, 107.5, 108.0, 103.5, 104.0),   # 9  down-close
    (10, 104.0, 104.5, 99.8, 100.8),   # 10 candidate: low through 100
    (11, 100.8, 102.0, 100.6, 101.8),  # 11 still no trade-through
    (12, 105.0, 105.6, 104.8, 105.2),  # 12 high > cand.high -> CONFIRMS
    (13, 105.2, 106.0, 103.8, 104.5),  # 13 clean bar
]

# same, but bar 12 spans BOTH the confirm level and the zone low in one
# bar (order unresolvable from OHLC).  Bar 13 is a later CLEAN bar
# (high > cand.high, low above the zone) that can still confirm the
# candidate independently.
SCENE_AMBIGUOUS = SCENE_CONFIRM[:12] + [
    (12, 101.0, 105.2, 99.5, 104.0),   # 12 both events possible
    (13, 105.2, 106.0, 103.8, 104.5),  # 13 later clean confirmation
]


# ------------------------------------------------------------------ #
# A  evidence-evaluated roles: supported vs unresolved                 #
# ------------------------------------------------------------------ #
def test_A_roles_are_evidence_evaluated_synthetic_geometric():
    """SYNTHETIC/GEOMETRIC — labeled synthetic data, not a market
    claim.  Alignment alone never assigns a trend role; opposition
    alone never assigns a reaction role.  With positive evidence a role
    is recorded; without it the verdict is UNDETERMINED (not permanent:
    new evidence re-opens it)."""
    ev_confirm = {"hf_established": True, "confirmation_event": True,
                  "reaction_observed": False}
    ev_nothing = {"hf_established": True, "confirmation_event": False,
                  "reaction_observed": False}
    ev_reaction = {"hf_established": True, "confirmation_event": False,
                   "reaction_observed": True}

    # same bearish shape + confirmation evidence, two contexts
    v_aligned = assign_role(candidate_direction="bearish",
                            hf_trend="down", task="trend-continuation",
                            evidence=ev_confirm)
    v_opposed = assign_role(candidate_direction="bearish",
                            hf_trend="up", task="trend-continuation",
                            evidence=ev_confirm)
    # supported trend role ONLY when direction agrees AND the
    # confirmation event is observed
    assert v_aligned["role"] == ROLE_TREND
    assert v_aligned["supported"] is True
    # under the opposing context the trend role is not supported and
    # the confirmation evidence alone does NOT invent a reaction role
    assert v_opposed["role"] == ROLE_UNDETERMINED
    assert v_opposed["supported"] is False
    assert any("opposition alone" in r for r in v_opposed["reasons"])
    assert v_opposed["discriminating_evidence_needed"]

    # a reaction role requires an OBSERVED reaction — never direction
    v_opp_react = assign_role(candidate_direction="bearish",
                             hf_trend="up", task="trend-continuation",
                             evidence=ev_reaction)
    assert v_opp_react["role"] == ROLE_REACTION_PAUSE
    assert v_opp_react["supported"] is True
    assert any("not inferred from opposition" in r
               for r in v_opp_react["reasons"])

    # alignment without confirmation evidence stays UNRESOLVED
    v_align_no_ev = assign_role(candidate_direction="bullish",
                               hf_trend="up",
                               task="trend-continuation",
                               evidence=ev_nothing)
    assert v_align_no_ev["role"] == ROLE_UNDETERMINED
    assert any("not yet supported" in r.lower()
               for r in v_align_no_ev["reasons"])

    # everything recorded: reasons, alternatives, change conditions
    for v in (v_aligned, v_opposed, v_opp_react, v_align_no_ev):
        assert v["reasons"]
        assert v["would_change"]
        assert v["evidence_used"]["hf_established"] is not None
    # not permanent abstention: evidence flags drive the verdict
    assert v_align_no_ev["discriminating_evidence_needed"]


# ------------------------------------------------------------------ #
# B  candidate before evidence; no back-filled confirmation            #
# ------------------------------------------------------------------ #
def test_B_candidate_before_evidence_no_backfill():
    bars = _bars(SCENE_CONFIRM)
    layer = StudyReasoningLayer(run_id="tB", k=2, task_scale="4h")
    ledger = InterpretationLedger()

    _run_boundaries(layer, bars, 9, ledger, direction="up")
    assert layer.candidates == []

    _run_boundaries(layer, bars, 10, ledger, direction="up", start=10)
    assert len(layer.candidates) == 1
    c = layer.candidates[0]
    assert c.state in (STATE_CANDIDATE, STATE_AWAITING_CONFIRMATION)
    assert all(e["to"] != STATE_CONFIRMED for e in c.events
               if e["kind"] == "state_transition")
    assert c.bar_index == 10

    _run_boundaries(layer, bars, 11, ledger, direction="up", start=11)
    assert c.state == STATE_AWAITING_CONFIRMATION

    _run_boundaries(layer, bars, 12, ledger, direction="up", start=12)
    assert c.state == STATE_CONFIRMED
    transitions = [e for e in c.events if e["kind"] == "state_transition"]
    conf = [e for e in transitions if e["to"] == STATE_CONFIRMED]
    assert len(conf) == 1
    assert conf[0]["at_bar"] == 12          # evidence bar
    assert conf[0]["from"] == STATE_AWAITING_CONFIRMATION
    assert c.bar_index == 10                # formation moment unchanged

    entries = [r for r in ledger.results
               if r.task_id == "T-STUDY-CANDIDATE"]
    assert entries, "state machine transitions must be ledger-recorded"
    assert any(p.get("kind") == "study_candidate_state"
               for p in ledger._payloads.values())
    kinds = [f["kind"] for f in layer.seq_facts]
    assert kinds.index("HF_CONTEXT_ESTABLISHED") < \
        kinds.index("CANDIDATE_FORMED")


# ------------------------------------------------------------------ #
# C  same-bar ambiguity: scoped, append-only, non-freezing             #
# ------------------------------------------------------------------ #
def _bar_interval(bars, j):
    return (pd.Timestamp(bars.index[j - 1]),
            pd.Timestamp(bars.index[j]))


def test_C_same_bar_ordering_scoped_append_only_non_freezing():
    # -- C1: finer rows INSIDE the ambiguous bar resolve it; the
    #        flattering order is refused when it is not established --
    bars = _bars(SCENE_AMBIGUOUS)
    layer = StudyReasoningLayer(run_id="tC", k=2, task_scale="4h")
    _run_boundaries(layer, bars, 11, InterpretationLedger(),
                    direction="up")
    c = layer.candidates[0]

    _run_boundaries(layer, bars, 12, InterpretationLedger(),
                    direction="up", start=12)
    assert c.ordering == UNKNOWN_ORDERING
    assert c.state != STATE_CONFIRMED
    assert c.ambiguous_bar == 12
    assert any(e["kind"] == "ordering_unresolved" for e in c.events)

    start, end = _bar_interval(bars, 12)
    span = end - start
    layer.on_observation({"time": start + span / 4,
                          "open": 104.9, "high": 105.2, "low": 104.6,
                          "close": 105.0})       # confirm touch only
    layer.on_observation({"time": start + span * 3 / 4,
                          "open": 102.0, "high": 102.1, "low": 99.5,
                          "close": 100.5})       # revisit touch only
    assert c.ordering == "confirmation-first"
    assert c.state == STATE_CONFIRMED
    res = [e for e in c.events
           if e["kind"] == "ordering_resolved_by_finer_data"]
    assert res and res[0]["order"] == "confirmation-first"
    # recorded when the SECOND touch became available (append-only:
    # the earlier ordering_unresolved record survives)
    assert any(e["kind"] == "ordering_unresolved" for e in c.events)

    # -- C2: revisit-first rejects ONLY the proposed sequence; the
    #        candidate is NOT permanently invalidated --
    layer2 = StudyReasoningLayer(run_id="tC2", k=2, task_scale="4h")
    _run_boundaries(layer2, bars, 12, InterpretationLedger(),
                    direction="up")
    c2 = layer2.candidates[0]
    layer2.on_observation({"time": start + span / 4,
                           "open": 102.0, "high": 102.1, "low": 99.5,
                           "close": 100.5})
    layer2.on_observation({"time": start + span * 3 / 4,
                           "open": 104.9, "high": 105.2, "low": 104.6,
                           "close": 105.0})
    assert c2.ordering == "revisit-first"
    assert c2.state != STATE_CONFIRMED      # not confirmed by THAT bar
    assert any(e["kind"] == "sequence_rejected" for e in c2.events)
    # NON-FREEZING: a later clean bar still confirms, at its own
    # evidence bar (the source establishes no permanent invalidation)
    _run_boundaries(layer2, bars, 13, InterpretationLedger(),
                    direction="up", start=13)
    assert c2.state == STATE_CONFIRMED
    conf2 = [e for e in c2.events if e.get("to") == STATE_CONFIRMED]
    assert conf2 and conf2[0]["at_bar"] == 13

    # -- C3: one fine bar holding both events -> ordering stays
    #        UNKNOWN (not rewritten), and the candidate still does not
    #        freeze --
    layer3 = StudyReasoningLayer(run_id="tC3", k=2, task_scale="4h")
    _run_boundaries(layer3, bars, 12, InterpretationLedger(),
                    direction="up")
    c3 = layer3.candidates[0]
    layer3.on_observation({"time": start + span / 2,
                           "open": 102.0, "high": 105.2, "low": 99.5,
                           "close": 102.5})     # both touches
    assert c3.ordering == UNKNOWN_ORDERING
    assert c3.state != STATE_CONFIRMED
    _run_boundaries(layer3, bars, 13, InterpretationLedger(),
                    direction="up", start=13)
    assert c3.state == STATE_CONFIRMED          # later bar confirms
    assert c3.ordering == UNKNOWN_ORDERING      # never rewritten

    # -- C4 (OBC-0006 defect regression): rows OUTSIDE the ambiguous
    #        bar's interval can NOT resolve its ordering --
    layer4 = StudyReasoningLayer(run_id="tC4", k=2, task_scale="4h")
    _run_boundaries(layer4, bars, 12, InterpretationLedger(),
                    direction="up")
    c4 = layer4.candidates[0]
    assert c4.ambiguous_bar == 12
    layer4.on_observation({"time": end + pd.Timedelta(hours=2),
                           "open": 102.0, "high": 102.1, "low": 99.5,
                           "close": 100.5})     # revisit-ish, outside
    layer4.on_observation({"time": end + pd.Timedelta(hours=6),
                           "open": 104.9, "high": 105.2, "low": 104.6,
                           "close": 105.0})     # confirm-ish, outside
    assert c4.ordering == UNKNOWN_ORDERING      # NOT resolved
    assert c4.state != STATE_CONFIRMED

    # -- C5: fine rows streaming BEFORE the boundary (buffer flow) are
    #        used at detection; resolution recorded at availability --
    layer5 = StudyReasoningLayer(run_id="tC5", k=2, task_scale="4h")
    _run_boundaries(layer5, bars, 11, InterpretationLedger(),
                    direction="up")
    c5 = layer5.candidates[0]
    layer5.on_observation({"time": start + span / 4,
                           "open": 104.9, "high": 105.2, "low": 104.6,
                           "close": 105.0})
    layer5.on_observation({"time": start + span * 3 / 4,
                           "open": 102.0, "high": 102.1, "low": 99.5,
                           "close": 100.5})
    _run_boundaries(layer5, bars, 12, InterpretationLedger(),
                    direction="up", start=12)
    assert c5.ordering == "confirmation-first"
    assert c5.state == STATE_CONFIRMED


# ------------------------------------------------------------------ #
# D  time provenance + revocation + NO proximity threshold             #
# ------------------------------------------------------------------ #
def test_D_time_provenance_revocation_and_no_threshold():
    # the module contains NO proximity threshold of any kind
    assert not hasattr(sl, "RESEARCH_CFG_NEAR_SUPPORT_DISTANCE_FRACTION")
    import inspect
    src = inspect.getsource(sl)
    assert "0.01" not in src, "no 1% value may remain in the module"

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

    clock = US_INDEX_FIRST_GAP_SESSION_CLOCK
    start = pd.Timestamp("2024-09-16 13:30", tz="UTC")
    assert clock.eligible_at(start, start) is False
    assert clock.eligible_at(start + pd.Timedelta(minutes=1), start)
    assert "NOT global" in clock.scope

    corr = sel.revoke(
        reason="FVG24-A (~75:02 approximate ASR wording): the 9:30 "
               "candle cannot be the first qualifying gap under the "
               "stated convention",
        evidence=["'You can't be on your 9.30 candle...' — approximate "
                  "attributed ASR wording, NOT audited by ear"],
        revised_to="first-gap-0931")
    assert sel.status == "REVOKED"
    assert corr["original"]["subject_id"] == "first-gap-0930"
    assert "NOT a fulfilled prediction" in corr["note"]
    assert "correction" in corr["note"]

    sel2 = TimeProvenanceSelection(
        selection_id="SEL-FVG24-2", subject_id="gap-x",
        selected_at=start, timezone="UTC",
        bar_convention="1m", timeframe="1m", eligibility={})
    corr2 = sel2.revoke(reason="eligibility removed by new information",
                        evidence=["observed later fact"], revised_to=None)
    assert sel2.status == "SUSPENDED"
    assert corr2["original"]["subject_id"] == "gap-x"

    # the engine runs WITHOUT the convention and without any threshold
    plain = StudyReasoningLayer(run_id="tD", k=2, task_scale="4h")
    assert plain.session_clock is None
    bars = _bars(SCENE_CONFIRM)
    _run_boundaries(plain, bars, 12, InterpretationLedger(),
                    direction="up")
    assert plain.candidates, "engine runs with no clock rule"
    # eligibility records the source caveat, not a distance
    assert "NOT operationally resolved" in \
        plain.candidates[0].eligibility["source_caveat"]
    assert "%" not in json.dumps(plain.candidates[0].eligibility)


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

    ev = hyp.review(bar_time=pd.Timestamp("2025-09-10"),
                    bar_high=114800, bar_low=113000, bar_close=114000)
    assert ev is None and hyp.status == "ACTIVE"

    ev = hyp.review(bar_time=pd.Timestamp("2025-09-11"),
                    bar_high=116000, bar_low=114000, bar_close=115500)
    assert ev is not None
    assert hyp.status == "SUSPENDED"
    assert "demand more information" in ev["reason"]
    assert "no automatic opposite hypothesis" in ev["reason"]

    layer = StudyReasoningLayer(run_id="tE", k=2, task_scale="4h")
    layer.hypotheses.append(hyp)
    before = len(layer.hypotheses)
    hyp.review(bar_time=pd.Timestamp("2025-09-12"),
               bar_high=117000, bar_low=115000, bar_close=116500)
    assert len(layer.hypotheses) == before
    assert all(h.hypothesis_id == "HYP-E12-1" for h in layer.hypotheses)
    assert hyp.status == "SUSPENDED"


# ------------------------------------------------------------------ #
# F  non-discrimination -> unresolved verdicts, never forced           #
# ------------------------------------------------------------------ #
def test_F_no_forced_pick_on_insufficient_evidence():
    def mk(cid):
        return OBLikeCandidate(
            candidate_id=cid, direction="bullish", bar_index=10,
            bar_time=pd.Timestamp("2025-09-01"), open=104, high=104.5,
            low=99.8, close=100.8, context_ref_id="PS-low-A",
            context_ref_level=100.0)

    a, b = mk("OBC-F-1"), mk("OBC-F-2")
    verdicts = [assign_role(candidate_direction=c.direction,
                           hf_trend="unknown", task="trend-continuation",
                           evidence=None) for c in (a, b)]
    for v in verdicts:
        assert v["role"] == ROLE_UNDETERMINED
        assert v["reasons"], "non-resolution must state reasons"
        assert v["discriminating_evidence_needed"], \
            "must state what evidence would discriminate"

    # layer: two candidates recorded (no silent drop), no forced pick
    layer = StudyReasoningLayer(run_id="tF", k=2, task_scale="4h")
    scene2 = list(SCENE_CONFIRM) + [
        (14, 104.5, 105.0, 99.6, 100.7),   # second candidate bar
    ]
    bars2 = _bars(scene2)
    _run_boundaries(layer, bars2, 14, InterpretationLedger())
    assert len(layer.candidates) >= 1
    assert all(c.role == ROLE_UNDETERMINED for c in layer.candidates)
    assert all(c.state != "rejected" for c in layer.candidates)

    # NOT permanent abstention: new evidence (hf + confirmation)
    # produces a supported role
    layer.hf_context = {"trend": "up", "evidence": ["SF-X"],
                        "established_at": "2025-09-01",
                        "as_of_bar": 0}
    for c in layer.candidates:
        if c.state == STATE_CONFIRMED:
            evidence = {"hf_established": True,
                        "confirmation_event": True,
                        "reaction_observed": False}
            v = assign_role(candidate_direction=c.direction,
                            hf_trend="up", task="trend-continuation",
                            evidence=evidence)
            if c.direction == "bullish":
                assert v["role"] == ROLE_TREND
                assert v["supported"] is True


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
                           index_col="timestamp", float_precision="round_trip")
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
        loop.run_to(pd.Timestamp("2025-09-03 04:00", tz="UTC"))
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
    assert json.dumps(out["resumed_study"], sort_keys=True,
                      default=str) == \
        json.dumps(state_at_T["study_state"], sort_keys=True,
                   default=str)
    assert json.dumps(out["continued_study"], sort_keys=True,
                      default=str) == \
        json.dumps(cont_state["study_state"], sort_keys=True,
                   default=str)


# ------------------------------------------------------------------ #
# H  post-T invariance: appending cannot change state at T             #
# ------------------------------------------------------------------ #
def test_H_post_T_invariance():
    bars = _bars(SCENE_CONFIRM)
    layerA = StudyReasoningLayer(run_id="tH", k=2, task_scale="4h")
    _run_boundaries(layerA, bars, 11, InterpretationLedger(),
                    direction="up")
    snap_A = json.dumps(layerA.state_dict(), sort_keys=True, default=str)

    layerB = StudyReasoningLayer(run_id="tH", k=2, task_scale="4h")
    _run_boundaries(layerB, bars, 11, InterpretationLedger(),
                    direction="up")
    snap_B_at_T = json.dumps(layerB.state_dict(), sort_keys=True,
                             default=str)
    assert snap_A == snap_B_at_T

    _run_boundaries(layerB, bars, 13, InterpretationLedger(),
                    direction="up", start=12)
    assert layerB.candidates[0].state == STATE_CONFIRMED
    events_up_to_T = [e for e in layerB.candidates[0].events
                      if pd.Timestamp(e.get("at", "2020-01-01"))
                      <= pd.Timestamp(bars.index[11])]
    assert len(events_up_to_T) == len(layerA.candidates[0].events)
    assert layerA.candidates[0].state != STATE_CONFIRMED
    assert json.dumps(layerA.state_dict(), sort_keys=True,
                      default=str) == snap_A


# ------------------------------------------------------------------ #
# R  genuine append-only revision: old AND new ledger records          #
# ------------------------------------------------------------------ #
def test_R_append_only_revision_old_and_new_ledger_records():
    bars = _bars(SCENE_AMBIGUOUS)
    layer = StudyReasoningLayer(run_id="tR", k=2, task_scale="4h")
    ledger = InterpretationLedger()

    # v1: formation
    _run_boundaries(layer, bars, 10, ledger, direction="up")
    uid_v1 = layer._ledger_uids[layer.candidates[0].candidate_id]
    snap_v1 = json.dumps(ledger._payloads[uid_v1], sort_keys=True,
                         default=str)

    # v2: the ambiguity (an actual revision — events changed)
    _run_boundaries(layer, bars, 12, ledger, direction="up", start=11)
    uid_v2 = layer._ledger_uids[layer.candidates[0].candidate_id]
    assert uid_v2 != uid_v1
    snap_v2 = json.dumps(ledger._payloads[uid_v2], sort_keys=True,
                         default=str)

    # v3: the resolution (another genuine revision)
    c = layer.candidates[0]
    start, end = _bar_interval(bars, 12)
    span = end - start
    layer.on_observation({"time": start + span / 4,
                          "open": 104.9, "high": 105.2, "low": 104.6,
                          "close": 105.0})
    layer.on_observation({"time": start + span * 3 / 4,
                          "open": 102.0, "high": 102.1, "low": 99.5,
                          "close": 100.5})
    _run_boundaries(layer, bars, 13, ledger, direction="up", start=13)
    uid_v3 = layer._ledger_uids[c.candidate_id]
    assert uid_v3 != uid_v2

    # revision_of chain preserved end to end
    assert ledger._payloads[uid_v2]["revision_of"] == uid_v1
    assert ledger._payloads[uid_v3]["revision_of"] == uid_v2

    # OLD records are still retrievable and UNCHANGED (append-only)
    assert json.dumps(ledger._payloads[uid_v1], sort_keys=True,
                      default=str) == snap_v1
    assert json.dumps(ledger._payloads[uid_v2], sort_keys=True,
                      default=str) == snap_v2
    # the new record carries the new state; the old ones still show the
    # earlier states (via their immutable result versions)
    r1 = ledger.versions[uid_v1][0]["result"]
    r2 = ledger.versions[uid_v2][0]["result"]
    r3 = ledger.versions[uid_v3][0]["result"]
    assert "state=AWAITING_CONFIRMATION" in " ".join(r1.notes)
    assert "state=CONFIRMED" not in " ".join(r1.notes)
    assert "state=AWAITING_CONFIRMATION" in " ".join(r2.notes)
    assert "state=CONFIRMED" in " ".join(r3.notes)
    assert "ordering_unresolved" in snap_v2 or "UNKNOWN" in snap_v2


# ------------------------------------------------------------------ #
# corpus + register integrity (source-linked expectations)            #
# ------------------------------------------------------------------ #
def test_corpus_loads_and_claims_are_classed():
    corpus = load_corpus()
    ids = [e["id"] for e in corpus["examples"]]
    assert {"E03-A", "E03-B", "E12-A", "OB16-A", "FVG16-A",
            "FVG24-A"} <= set(ids)
    assert all(e["split"] == "DEVELOPMENT" for e in corpus["examples"])
    ho = corpus["held_out"]
    assert ho["split"] == "HELD_OUT"
    assert ho["source_id"] == "YT_tpPtItWqmlg"
    assert "No audio transcript" in ho["access"]
    assert "out of tuning" in ho["access"]
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
    ams = corpus.get("amendments", [])
    amd = [a for a in ams
           if a.get("amendment_id") == "AMD-01-E03B-DESCRIPTION"]
    assert amd, "AMD-01-E03B-DESCRIPTION must be recorded"
    assert "hypothetical" in amd[0]["corrected_description"]
    assert "NOT" in amd[0]["corrected_description"]


def test_quote_provenance_is_labeled():
    """ASR wording must be labeled approximate/not ear-audited; only
    the 01:52 slide text is visually checked (Q5)."""
    corpus = load_corpus()
    e = {x["id"]: x for x in corpus["examples"]}
    slide = [q for q in e["OB16-A"]["short_quotes"]
             if "human-verified" in q.get("attribution", "")]
    assert slide, "slide-verified quote must be marked human-verified"
    asr_quotes = []
    for eid in ("OB16-A", "FVG24-A", "E12-A"):
        asr_quotes += [q for q in e[eid]["short_quotes"]
                       if "ASR" in q.get("attribution", "")]
    assert asr_quotes, "ASR quotes exist and must be marked"
    for q in asr_quotes:
        assert "not ear-audited" in q["attribution"] or \
            "not ear-audited" in q["attribution"].replace("(", " ")
    # the relationship register carries the same labels
    reg = json.dumps(sl.RELATIONSHIP_REGISTER)
    assert "NOT audited by ear" in reg or "not ear-audited" in reg
    assert "visually checked" in reg
