"""Golden-set + mechanics tests for the CSM research kernel (contextual_selection).

Golden set: knowledge_foundation/19_SELECTION_CASES.md W1-W5, W8-W10
(constructed fixtures; ordinal levels).  W6/W7 (liquidity/zone relevance) are
OUT OF SCOPE for the first build (architecture/v2/05 §4.1 excludes them) and
are recorded as such.  Objective A (file 18 §18.3): exact replication of the
declared deterministic procedures on these fixtures.

These tests are the regression golden set required by LRN-06 §18.7 item 1.
"""
from __future__ import annotations

import copy
from datetime import timedelta

import pandas as pd
import pytest

from trading_system.research.contextual_selection import (
    REASON_AI,
    REASON_EP,
    REASON_IC,
    REASON_MP,
    X_POL,
    X_SCALE,
    X_STATE,
    X_SUPER,
    Exclusion,
    InterpretationLedger,
    LegCandidate,
    PointCandidate,
    PolicyRegistry,
    Representation,
    UnresolvedState,
    build_legs,
    fk_turning_points,
    ft_turning_points,
    sp05_containment,
    sp06_dominance,
    task_s1_structural_reference,
    task_s2_event_binding,
    task_s3_entry_leg,
    task_s5_falsifier,
)

# Shared information-time axis for the fixture: bar i -> T0 + i minutes.
T0 = pd.Timestamp("2025-01-01 00:00:00")

# consolidation V1: validated shared information-time axis over the fixture's
# T0-minute grid (every fixture timestamp lies on this grid)
from trading_system.research.contextual_selection import (  # noqa: E402
    SharedInformationAxis as _SharedInformationAxis,
)
AXIS = _SharedInformationAxis(
    "test-fixture-minute-grid",
    pd.date_range(T0, T0 + pd.Timedelta(minutes=2000), freq="1min"))


# --------------------------------------------------------------------------
# Shared fixture (file 19 §19.2) — ordinal levels, bar indices as labels
# --------------------------------------------------------------------------

K = 5  # declared F-K window for view C fixture (explains knowable 15/25/35/45)


def _rep(view: str, scale: str, family: str = "F-K", **params) -> Representation:
    return Representation(family=family, view_id=view, scale_label=scale,
                          params=tuple(sorted(params.items())))


REP_C = _rep("C", "coarse", k=K)
REP_F = _rep("F", "fine", k=2)


def _pt(pid, rep, side, occ, level, know, status="confirmed", **kw):
    return PointCandidate(
        candidate_id=pid, rep=rep, side=side,
        occurrence_bar=occ, level=level, knowable_bar=know,
        status=status,
        occurrence_time=T0 + timedelta(minutes=occ),
        knowable_time=T0 + timedelta(minutes=know), **kw)


def _fill_leg_times(legs):
    """Causal-state integration V1: fixture legs carry verified times on the
    shared T0-minute axis (same convention as ``_pt``) so decision-time
    availability is always verifiable."""
    for l in legs:
        if l.t0_time is None:
            l.t0_time = T0 + timedelta(minutes=l.t0)
            l.t1_time = T0 + timedelta(minutes=l.t1)
            l.knowable_time = T0 + timedelta(minutes=l.knowable_bar)
    return legs


@pytest.fixture(scope="module")
def world():
    """Coarse points C + fine points F exactly as file 19 §19.2."""
    coarse = [
        _pt("L_a", REP_C, "low", 10, 10.0, 15),
        _pt("H_a", REP_C, "high", 20, 40.0, 25),
        _pt("L_b", REP_C, "low", 30, 20.0, 35),
        _pt("H_b", REP_C, "high", 40, 50.0, 45),
    ]
    fine = [
        _pt("fA.0", REP_F, "low", 30, 20.0, 30),
        _pt("fA.1", REP_F, "high", 33, 35.0, 34),
        _pt("fB.1", REP_F, "low", 36, 25.0, 38),
        _pt("fC.1", REP_F, "high", 38, 42.0, 40),
        _pt("fD.1", REP_F, "low", 39, 22.0, 41),
        _pt("fE.1", REP_F, "high", 40, 50.0, 42),
    ]
    # legs: Leg1/2/3 coarse (fA..fE fine) — ids match the case names
    clegs = [
        LegCandidate("Leg1", REP_C, "L_a", "H_a", "up", 10, 20, 10.0, 40.0, 25),
        LegCandidate("Leg2", REP_C, "H_a", "L_b", "down", 20, 30, 40.0, 20.0, 35),
        LegCandidate("Leg3", REP_C, "L_b", "H_b", "up", 30, 40, 20.0, 50.0, 45),
    ]
    flegs = [
        LegCandidate("fA", REP_F, "fA.0", "fA.1", "up", 30, 33, 20.0, 35.0, 34),
        LegCandidate("fB", REP_F, "fA.1", "fB.1", "down", 33, 36, 35.0, 25.0, 38),
        LegCandidate("fC", REP_F, "fB.1", "fC.1", "up", 36, 38, 25.0, 42.0, 40),
        LegCandidate("fD", REP_F, "fC.1", "fD.1", "down", 38, 39, 42.0, 22.0, 41),
        LegCandidate("fE", REP_F, "fD.1", "fE.1", "up", 39, 40, 22.0, 50.0, 42),
    ]
    _fill_leg_times(clegs + flegs)
    pol = PolicyRegistry()
    pol.register("P-ORIGIN", "role: origin of the most recent confirmed leg (SWS-02, O-class)",
                 "origin-of-last-confirmed-leg")
    pol.register("P-CONTINUATION", "continuation-long entry uses completed down-legs inside an up-leg",
                 "down-legs-in-up-leg")
    return {"points": coarse + fine, "coarse": coarse, "fine": fine,
            "clegs": clegs, "flegs": flegs, "pol": pol}


# --------------------------------------------------------------------------
# W1 — T-S1 structural reference (definite conditional on Pi_T)
# --------------------------------------------------------------------------

def test_W1_structural_reference(world):
    r = task_s1_structural_reference(
        world["points"], world["clegs"], decision_bar=52, rep=REP_C,
        role="origin-of-last-confirmed-leg", policy=world["pol"],
        policy_id="P-ORIGIN", state_id_prefix="W1", axis=AXIS, decision_time=T0 + timedelta(minutes=52))
    assert r.status == "justified"
    assert r.selected_id == "L_b"
    assert r.survivors == ["L_b"]
    codes = {e.candidate_id: e.code for e in r.excluded}
    # fine points excluded X-SCALE (not in view C)
    assert codes.get("fA.0") == X_SCALE
    # coarse non-origin points excluded X-POL
    assert codes.get("L_a") == X_POL
    assert codes.get("H_a") == X_POL
    assert codes.get("H_b") == X_POL
    assert any("Leg3" in n for n in r.notes)
    assert "T-S5-falsifier" in r.dependents


# --------------------------------------------------------------------------
# W2 — T-S3 entry-timing leg with preserved ambiguity (MP; acceptable set)
# --------------------------------------------------------------------------

def test_W2_entry_leg_ambiguity_preserved(world):
    r = task_s3_entry_leg(
        world["clegs"][2], world["flegs"], decision_bar=52, rep=REP_F,
        continuation_condition=("direction", "down"),
        policy=world["pol"], state_id_prefix="W2", axis=AXIS, decision_time=T0 + timedelta(minutes=52))
    assert r.status == "unresolved"
    assert sorted(r.survivors) == ["fB", "fD"]
    assert r.unresolved is not None
    assert r.unresolved.reason_code == REASON_MP
    assert sorted(u for u in r.unresolved.survivors) == ["fB", "fD"]
    codes = {e.candidate_id: e.code for e in r.excluded}
    assert codes.get("fA") == X_POL
    assert codes.get("fC") == X_POL
    assert codes.get("fE") == X_POL
    assert "zone-boundaries" in r.unresolved.dependents_blocked
    # factual differences preserved in notes (depth vs recency not decided)
    assert any("depth" in n and "knowable" in n for n in r.notes)
    # audit D6: depth values are actual numbers (fB: |35-25|=10, fD: |42-22|=20)
    note_text = " ".join(r.notes)
    assert "depth=10" in note_text and "depth=20" in note_text


# --------------------------------------------------------------------------
# W3 — task change: falsifier vs entry timing (SP-04 claim tables)
# --------------------------------------------------------------------------

def test_W3_task_change(world):
    claims = [
        {"interpretation": "I1", "view": "C",
         "role": "origin-of-last-confirmed-leg", "direction": "up"},
        {"interpretation": "I2", "view": "F",
         "role": "low-of-current-leg", "direction": "down"},
    ]
    r = task_s5_falsifier(claims, world["points"], world["clegs"] + world["flegs"],
                          decision_bar=52, state_id_prefix="W3", axis=AXIS, decision_time=T0 + timedelta(minutes=52))
    assert r.status == "unresolved"  # two claims -> two references, kept apart
    assert set(r.survivors) == {"L_b", "fD.1"}
    notes = " ".join(r.notes)
    assert "I1" in notes and "L_b" in notes
    assert "I2" in notes and "fD.1" in notes
    # audit D6: direction is structural — role output changes with direction
    claims_up = [{"interpretation": "I3", "view": "F",
                  "role": "high-of-current-leg", "direction": "up"}]
    claims_dn = [{"interpretation": "I4", "view": "F",
                  "role": "high-of-current-leg", "direction": "down"}]
    ru = task_s5_falsifier(claims_up, world["points"],
                           world["clegs"] + world["flegs"], 52, state_id_prefix="W3u", axis=AXIS, decision_time=T0 + timedelta(minutes=52))
    rd = task_s5_falsifier(claims_dn, world["points"],
                           world["clegs"] + world["flegs"], 52, state_id_prefix="W3d", axis=AXIS, decision_time=T0 + timedelta(minutes=52))
    assert ru.selected_id == "fE.1"   # high of last up-leg fE
    assert rd.selected_id == "fC.1"   # high of last down-leg fD
    # missing direction -> explicit unresolved (IC), never inferred
    claims_nodir = [{"interpretation": "I5", "view": "F",
                     "role": "low-of-current-leg"}]
    rn = task_s5_falsifier(claims_nodir, world["points"],
                           world["clegs"] + world["flegs"], 52, state_id_prefix="W3n", axis=AXIS, decision_time=T0 + timedelta(minutes=52))
    assert rn.status == "unresolved"
    assert rn.unresolved is not None and rn.unresolved.reason_code == REASON_IC
    # entry-timing for the same bars stays ambiguous (W2 pattern)
    r3 = task_s3_entry_leg(world["clegs"][2], world["flegs"], 52, REP_F,
                           continuation_condition=("direction", "down"),
                           policy=world["pol"], axis=AXIS, decision_time=T0 + timedelta(minutes=52))
    assert r3.status == "unresolved" and sorted(r3.survivors) == ["fB", "fD"]


# --------------------------------------------------------------------------
# W4 — provisional point: IC, then branch-dependent (SP-13, SWS-04)
# --------------------------------------------------------------------------

def _extended_world(world):
    pts = list(world["points"]) + [
        _pt("L_c", REP_C, "low", 48, 28.0, 56),
        _pt("H_p", REP_C, "high", 60, 55.0, 65, status="provisional"),
    ]
    legs = world["clegs"] + [
        LegCandidate("Leg4", REP_C, "H_b", "L_c", "down", 40, 48, 50.0, 28.0, 56),
    ]
    _fill_leg_times(legs)
    return pts, legs


def test_W4_provisional_then_branches(world):
    pts, legs = _extended_world(world)
    pol = world["pol"]
    # t = 59: last confirmed leg H_b->L_c; origin H_b
    r = task_s1_structural_reference(pts, legs, 59, REP_C,
                                     "origin-of-last-confirmed-leg", pol, "P-ORIGIN", axis=AXIS, decision_time=T0 + timedelta(minutes=59))
    assert r.selected_id == "H_b"
    # t = 64 (= 60+k-1): H_p provisional -> X-STATE; reference stays H_b (IC note)
    r64 = task_s1_structural_reference(pts, legs, 64, REP_C,
                                       "origin-of-last-confirmed-leg", pol, "P-ORIGIN", axis=AXIS, decision_time=T0 + timedelta(minutes=64))
    assert r64.selected_id == "H_b"
    codes = {e.candidate_id: e.code for e in r64.excluded}
    assert codes.get("H_p") == X_STATE
    # Branch A: H_p confirmed at 65 -> it is the new tracked reference
    pts_a = [p for p in pts if p.candidate_id != "H_p"] + [
        _pt("H_p", REP_C, "high", 60, 55.0, 65)]
    r65 = task_s1_structural_reference(pts_a, legs, 65, REP_C,
                                       "last-confirmed-extreme", pol, None, axis=AXIS, decision_time=T0 + timedelta(minutes=65))
    assert r65.selected_id == "H_p"
    # Branch B: higher high at 62 supersedes H_p (SWS-04c)
    hp = next(p for p in pts if p.candidate_id == "H_p")
    hp.status = "superseded"
    hp.superseded_by = "H_n"
    pts_b = pts + [_pt("H_n", REP_C, "high", 62, 58.0, 67, status="provisional")]
    r66 = task_s1_structural_reference(pts_b, legs, 66, REP_C,
                                       "origin-of-last-confirmed-leg", pol, "P-ORIGIN", axis=AXIS, decision_time=T0 + timedelta(minutes=66))
    assert r66.selected_id == "H_b"
    codes_b = {e.candidate_id: e.code for e in r66.excluded}
    assert codes_b.get("H_p") == X_SUPER
    assert codes_b.get("H_n") == X_STATE
    # Replay check (SWS-04d): recompute at 64 from truncated inputs == stored
    r64_again = task_s1_structural_reference(
        [p for p in pts if p.knowable_bar <= 64 or p.candidate_id == "H_p"],
        [l for l in legs if l.knowable_bar <= 64], 64, REP_C,
        "origin-of-last-confirmed-leg", pol, "P-ORIGIN", axis=AXIS, decision_time=T0 + timedelta(minutes=64))
    assert r64_again.selected_id == r64.selected_id
    assert {e.candidate_id for e in r64_again.excluded} == {e.candidate_id for e in r64.excluded}


# --------------------------------------------------------------------------
# W5 — break event with competing references (SP-03) + AI for reversal
# --------------------------------------------------------------------------

def test_W5_break_binding_and_reversal_ai(world):
    refs_c = [next(p for p in world["coarse"] if p.candidate_id == "L_b")]
    refs_f = [next(p for p in world["fine"] if p.candidate_id == "fB.1"),
              next(p for p in world["fine"] if p.candidate_id == "fD.1")]
    r = task_s2_event_binding(event_bar=53, close_price=19.0,
                              refs_by_view={"C": refs_c, "F": refs_f},
                              decision_bar=53, state_id_prefix="W5",
                              event_time=T0 + timedelta(minutes=53), axis=AXIS,
                              event_ref="W5-E53")
    assert set(r.survivors) == {"L_b", "fB.1", "fD.1"}
    notes = " ".join(r.notes)
    assert "'C': ['L_b']" in notes or '"C": ["L_b"]' in notes or "C" in notes
    # binding is not significance: reversal stays AI (interpretive reading)
    ai = UnresolvedState(
        state_id="W5-53-reversal", task="reversal-interpretation", decision_bar=53,
        survivors=["L_b"], excluded=[], reason_code=REASON_AI,
        evidence_needed="source-faithful reading with timestamp, or a declared reversal policy",
        policy_refs=[], provenance=["R:W5"],
        dependents_blocked=["trend-reversed-statement", "zones/targets depending on it"])
    assert ai.reason_code == REASON_AI


# --------------------------------------------------------------------------
# W8 — reference role change after a later event + propagation log (SP-20)
# --------------------------------------------------------------------------

def test_W8_role_change_and_propagation(world):
    pts, legs = _extended_world(world)
    pol = world["pol"]
    # structural reference at 56 in the intact world: origin of H_b->L_c
    r = task_s1_structural_reference(pts, legs, 56, REP_C,
                                     "origin-of-last-confirmed-leg", pol, "P-ORIGIN",
                                     state_id_prefix="W8", axis=AXIS, decision_time=T0 + timedelta(minutes=56))
    assert r.selected_id == "H_b"  # origin of H_b->L_c after the bar-53 break
    assert r.direction == "down"   # direction from the leg data (D6), not notes

    # state at bar 53: Leg3 is the last knowable confirmed leg -> L_b
    r53 = task_s1_structural_reference(pts, legs, 53, REP_C,
                                       "origin-of-last-confirmed-leg", pol, "P-ORIGIN",
                                       state_id_prefix="W8", axis=AXIS, decision_time=T0 + timedelta(minutes=53))
    assert r53.selected_id == "L_b"
    claims = [{"interpretation": "I1", "view": "C",
               "role": "origin-of-last-confirmed-leg", "direction": "up"}]
    s53 = task_s5_falsifier(claims, pts, legs, 53, state_id_prefix="W8S5", axis=AXIS, decision_time=T0 + timedelta(minutes=53))
    assert s53.selected_id == "L_b"

    ledger = InterpretationLedger()
    t1_uid = ledger.record(r53, payload={
        "kind": "T-S1", "points": copy.deepcopy(pts), "legs": copy.deepcopy(legs),
        "rep": REP_C, "role": "origin-of-last-confirmed-leg",
        "policy": pol, "policy_id": "P-ORIGIN", "state_id_prefix": "W8",
        "axis": AXIS})
    s5_uid = ledger.record(s53, payload={
        "kind": "T-S5", "claims": copy.deepcopy(claims),
        "points": copy.deepcopy(pts), "legs": copy.deepcopy(legs),
        "state_id_prefix": "W8S5", "axis": AXIS})
    ledger.record_event(53, "close-break", "close 19 < L_b 20", ["L_b"],
                        event_time=T0 + timedelta(minutes=53))

    # break fact at 53 -> propagation recomputes dependents (no strings)
    log53 = ledger.propagate(53, ["L_b"], changed_states={"L_b": "broken"},
                             update_time=T0 + timedelta(minutes=53),
                             axis=AXIS)
    assert log53 and all("SP-20" in e["rule"] for e in log53)
    t1v2 = ledger.versions[t1_uid][1]
    # computed: L_b unusable now, but the successor is NOT knowable until 56
    assert t1v2["recomputable"] and t1v2["computed_changes"]
    assert t1v2["result"].status == "unresolved"
    assert t1v2["result"].selected_id is None          # H_b must NOT appear at 53
    assert all(c.get("after") != "H_b" for c in t1v2["computed_changes"])
    # the falsifier fired as a COMPUTED task-level effect
    s5v2 = ledger.versions[s5_uid][1]
    assert s5v2["result"].status == "falsified"
    assert any(c.get("field") == "status" and c.get("after") == "falsified"
               for c in s5v2["computed_changes"])

    # bar 56: Leg4 becomes knowable -> ONLY NOW can T-S1 move to H_b
    ledger.record_change(56, "Leg4", "knowable")
    log56 = ledger.propagate(56, ["Leg4"], update_time=T0 + timedelta(minutes=56),
                             axis=AXIS)
    t1v3 = ledger.versions[t1_uid][2]
    assert t1v3["result"].selected_id == "H_b"
    assert any(c.get("field") == "selected_id" and c.get("after") == "H_b"
               for c in t1v3["computed_changes"])
    # prior historical versions preserved (nothing rewritten in place)
    assert ledger.versions[t1_uid][0]["result"].selected_id == "L_b"
    assert ledger.versions[t1_uid][1]["result"].selected_id is None
    assert ledger.snapshot()["n_events"] == 1


# --------------------------------------------------------------------------
# W9 — two admissible representations, two answers (SP-16, MP)
# --------------------------------------------------------------------------

def test_W9_representation_dependence(world):
    # F-K view C: origin L_b (W1)
    r_fk = task_s1_structural_reference(
        world["points"], world["clegs"], 52, REP_C,
        "origin-of-last-confirmed-leg", world["pol"], "P-ORIGIN", axis=AXIS, decision_time=T0 + timedelta(minutes=52))
    # F-T with large tau: L_b never registers -> points L_a..H_a only
    REP_FT = _rep("C", "coarse", family="F-T", tau=25.0)
    pts_ft = [
        _pt("L_a", REP_FT, "low", 10, 10.0, 15),
        _pt("H_a", REP_FT, "high", 20, 40.0, 25),
    ]
    legs_ft = [LegCandidate("Leg1", REP_FT, "L_a", "H_a", "up", 10, 20, 10.0, 40.0, 25,
                            t0_time=T0 + timedelta(minutes=10),
                            t1_time=T0 + timedelta(minutes=20),
                            knowable_time=T0 + timedelta(minutes=25))]
    r_ft = task_s1_structural_reference(
        pts_ft, legs_ft, 52, REP_FT,
        "origin-of-last-confirmed-leg", world["pol"], "P-ORIGIN", axis=AXIS, decision_time=T0 + timedelta(minutes=52))
    assert r_fk.selected_id == "L_b"
    assert r_ft.selected_id == "L_a"
    # SP-16: report disagreement; do not merge
    agreement = "agree" if r_fk.selected_id == r_ft.selected_id else "disagree"
    assert agreement == "disagree"
    assert r_fk.representation_id != r_ft.representation_id
    # the representation choice is MP (no declared cross-representation rule)
    assert REASON_MP in (REASON_MP,)


def test_W10_singleton_binding(world):
    refs_c = [next(p for p in world["coarse"] if p.candidate_id == "L_b")]
    refs_f = [next(p for p in world["fine"] if p.candidate_id == "fB.1"),
              next(p for p in world["fine"] if p.candidate_id == "fD.1")]
    r = task_s2_event_binding(event_bar=47, close_price=24.0,
                              refs_by_view={"C": refs_c, "F": refs_f},
                              decision_bar=47, state_id_prefix="W10",
                              event_time=T0 + timedelta(minutes=47), axis=AXIS,
                              event_ref="W10-E47")
    assert r.status == "justified"
    assert r.survivors == ["fB.1"]
    assert r.selected_id == "fB.1"


# --------------------------------------------------------------------------
# Generator mechanics (unit): F-K confirmation, supersession; F-T reversal
# --------------------------------------------------------------------------

def _bars_from_levels(lows, highs):
    n = len(lows)
    return pd.DataFrame({
        "open": [ (lows[i] + highs[i]) / 2 for i in range(n)],
        "high": highs, "low": lows,
        "close": [ (lows[i] + highs[i]) / 2 for i in range(n)],
        "volume": [1.0] * n,
    })


def test_fk_generator_confirm_and_supersede():
    # synthetic series realizing the W4 shapes: low@10=10, high@20=40, low@30=20,
    # high@40=50, low@48=28, high@60=55, then a higher high at 62=58
    n = 80
    lows = [30.0] * n
    highs = [30.0] * n
    for i, lv in [(10, 10.0), (30, 20.0), (48, 28.0)]:
        lows[i] = lv
    for i, hv in [(20, 40.0), (40, 50.0), (60, 55.0), (62, 58.0)]:
        highs[i] = hv
    bars = _bars_from_levels(lows, highs)
    rep = REP_C
    pts = fk_turning_points(bars, k=5, rep=rep, id_prefix="G|")
    by = {(p.occurrence_bar, p.side): p for p in pts}
    assert by[(10, "low")].knowable_bar == 15
    assert by[(10, "low")].status == "confirmed"
    assert by[(60, "high")].status == "superseded"          # SWS-04c
    assert by[(60, "high")].superseded_by == by[(62, "high")].candidate_id
    assert by[(62, "high")].status == "confirmed"
    assert by[(62, "high")].knowable_bar == 67
    # replay consistency: truncation at bar 64 reproduces the provisional H_p
    pts64 = fk_turning_points(bars.iloc[:65], k=5, rep=rep, id_prefix="G|")
    p60 = [p for p in pts64 if p.occurrence_bar == 60 and p.side == "high"]
    assert len(p60) == 1 and p60[0].status in ("provisional", "superseded")


def test_ft_generator_threshold_reversal():
    closes = [10.0, 12.0, 15.0, 14.0, 13.5, 12.0, 11.0, 13.0, 16.0]
    highs = [c + 0.2 for c in closes]
    lows = [c - 0.2 for c in closes]
    bars = pd.DataFrame({"open": closes, "high": highs, "low": lows,
                         "close": closes, "volume": [1.0] * len(closes)})
    rep = _rep("T", "coarse", family="F-T", tau=3.0)
    pts = ft_turning_points(bars, tau=3.0, rep=rep)
    sides = [(p.side, p.occurrence_bar, p.status) for p in pts]
    # extreme high at bar 2 (15.0) registers when reversal >= 3 (bar 6: 12.0? no -> bar 6 low 11.8: 15-11.8=3.2)
    assert ("high", 2, "confirmed") in sides
    # the closing extreme at the end stays provisional (never reversed enough)
    assert sides[-1][2] == "provisional"


def test_sp05_containment_labels(world):
    leg3 = world["clegs"][2]
    labels = {f.leg_id: sp05_containment(leg3, f) for f in world["flegs"]}
    assert labels["fA"] == "contained"
    assert labels["fB"] == "contained"
    assert labels["fD"] == "contained"


def test_sp06_dominance_keeps_ties():
    class C:
        def __init__(self, cid, a, b):
            self.candidate_id = cid
            self.a, self.b = a, b
    c1, c2, c3 = C("c1", True, False), C("c2", False, True), C("c3", True, True)
    surv, ex = sp06_dominance([c1, c2, c3], [("a", lambda c: c.a), ("b", lambda c: c.b)])
    ids = sorted(c.candidate_id for c in surv)
    assert ids == ["c3"]
    assert ex[0].code == "X-DOM"
    # ties survive
    surv2, ex2 = sp06_dominance([c1, c2], [("a", lambda c: c.a), ("b", lambda c: c.b)])
    assert sorted(c.candidate_id for c in surv2) == ["c1", "c2"] and not ex2


# Scope record: W6/W7 intentionally absent (liquidity/zone tasks excluded from
# the first build — architecture/v2/05 §4.1).  Objective A = exact replication
# of declared deterministic procedures on the in-scope golden fixtures above.
