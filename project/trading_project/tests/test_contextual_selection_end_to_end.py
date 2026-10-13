"""END-TO-END CONSOLIDATION V1 — adversarial regression gate.

Reproduces every blocking counterexample from the independent audit of
commit 312163a and asserts ACTUAL behavior (state transitions, bound sets,
computed versions), not merely returned status names.  Selection quality is
NOT_ESTABLISHED throughout; this file tests causal correctness only.

Required cases (task §8):
  1 off-grid time acceptance            8 pre/post-event binding stability
  2 late-confirmed T-S5 extreme         9 tie-policy contradiction
  3 missing endpoint availability      10 policy mutation after result creation
  4 cross-domain transition fallback   11 missing T-S3 decision boundary
  5 cross-view containment without time 12 provisional policy replay
  6 candidate lifecycle reset at B2    13 A->B->C transitive propagation
  7 T-S2-only transition persistence  14 terminal provisional retention
"""
from datetime import timedelta

import pandas as pd
import pytest

from trading_system.research.contextual_selection import (
    PHASE_BINDING,
    PHASE_POST_EVENT,
    PHASE_PRE_EVENT,
    PointCandidate,
    LegCandidate,
    PolicyRegistry,
    Representation,
    SharedInformationAxis,
    STATUS_BROKEN,
    STATUS_CONFIRMED,
    STATUS_PROVISIONAL,
    STATUS_SUPERSEDED,
    TIE_CROSS_EQUAL_BOUND_V1,
    TIE_CROSS_EQUAL_UNBOUND,
    InterpretationLedger,
    available_at,
    build_legs,
    fk_turning_points,
    ft_turning_points,
    sp05_containment,
    task_s1_structural_reference,
    task_s2_event_binding,
    task_s3_entry_leg,
    task_s5_falsifier,
)

T0 = pd.Timestamp("2025-01-01 00:00:00")
# validated axis: the fixture's minute grid (bar i <-> T0 + i minutes)
AXIS = SharedInformationAxis(
    "test-fixture-minute-grid",
    pd.date_range(T0, T0 + pd.Timedelta(minutes=3000), freq="1min"))
OFF_GRID = T0 + pd.Timedelta(seconds=30)      # NOT on the minute grid


def _rep(view="C", family="F-K", **params):
    return Representation(family=family, view_id=view, scale_label="s",
                          params=tuple(sorted(params.items())))


def _pt(pid, rep, side, occ, level, know, status=STATUS_CONFIRMED, **kw):
    kw.setdefault("occurrence_time", T0 + timedelta(minutes=occ))
    if know is not None:
        kw.setdefault("knowable_time", T0 + timedelta(minutes=know))
    return PointCandidate(candidate_id=pid, rep=rep, side=side,
                          occurrence_bar=occ, level=level,
                          knowable_bar=know if know is not None else occ + 99,
                          status=status, **kw)


def _lg(leg_id, rep, s, e, direction, t0, t1, p0, p1, know,
        times=True, **kw):
    if times:
        kw.setdefault("t0_time", T0 + timedelta(minutes=t0))
        kw.setdefault("t1_time", T0 + timedelta(minutes=t1))
        kw.setdefault("knowable_time", T0 + timedelta(minutes=know))
    return LegCandidate(leg_id=leg_id, rep=rep, start_id=s, end_id=e,
                        direction=direction, t0=t0, t1=t1, p_start=p0,
                        p_end=p1, knowable_bar=know, **kw)


def _pol():
    pol = PolicyRegistry()
    pol.register("P-ORIGIN", "origin role", "origin-of-last-confirmed-leg")
    return pol


# ---------------------------------------------------------------- 1
def test_off_grid_knowable_time_is_not_a_verified_claim():
    """An off-grid knowable time must NOT bind through raw comparison: with
    the validated axis it is explicit unavailability; without an axis the
    time-bearing call is rejected outright (no silent bypass)."""
    rep = _rep("C", k=2)
    ref = _pt("off", rep, "low", 3, 10.0, 3)
    ref.knowable_time = OFF_GRID                 # 00:00:30 — off the grid
    ev_t = T0 + timedelta(minutes=5)             # 00:05:00 — on the grid
    r = task_s2_event_binding(5, 0.0, {"C": [ref]}, 5, event_time=ev_t,
                              axis=AXIS, state_id_prefix="off")
    assert r.survivors == []                     # never bound
    codes = {e.candidate_id: e.code for e in r.excluded}
    assert codes.get("off") == "X-KNOW"          # explicit, auditable
    # the OLD counterexample path (direct comparison, no axis) is REJECTED:
    with pytest.raises(ValueError, match="axis"):
        task_s2_event_binding(5, 0.0, {"C": [ref]}, 5, event_time=ev_t)


# ---------------------------------------------------------------- 2
def test_late_confirmed_extreme_never_justifies_at_decision_time():
    """T-S5 last-confirmed-extreme: a point whose knowable_time is AFTER the
    decision boundary must not be selected even when its knowable_bar fits
    (the audited bar-index trap)."""
    rep = _rep("C", k=2)
    late = _pt("late", rep, "low", 10, 20.0, 10)      # knowable_bar 10 <= 31
    late.knowable_time = T0 + timedelta(minutes=32)   # but the TIME is late
    r = task_s5_falsifier(
        [{"interpretation": "I", "view": "C", "role": "last-confirmed-extreme",
          "side": "low"}], [late], [], 31,
        decision_time=T0 + timedelta(minutes=31), axis=AXIS)
    assert r.selected_id is None
    assert r.survivors == []
    assert r.status == "unresolved"
    assert any(e.candidate_id == "late" and e.code == "X-KNOW"
               for e in r.excluded)
    # the SAME point justifies once its information time has come
    r2 = task_s5_falsifier(
        [{"interpretation": "I", "view": "C", "role": "last-confirmed-extreme",
          "side": "low"}], [late], [], 31,
        decision_time=T0 + timedelta(minutes=33), axis=AXIS)
    assert r2.selected_id == "late"


# ---------------------------------------------------------------- 3
def test_missing_endpoint_time_makes_leg_availability_fail_closed():
    """A leg must not borrow availability from one endpoint when the other
    has no verifiable knowable time."""
    rep = _rep("C", k=2)
    a = _pt("a", rep, "low", 10, 10.0, 12)
    b = _pt("b", rep, "high", 20, 40.0, None)    # endpoint time MISSING
    b.knowable_time = None
    legs = build_legs([a, b], rep)
    assert len(legs) == 1
    assert legs[0].knowable_time is None         # unverifiable, not invented
    assert not available_at(legs[0], as_of_time=T0 + timedelta(minutes=25))
    # a fully supported sibling leg is available at the LATER endpoint time
    c = _pt("c", rep, "low", 30, 20.0, 32)
    legs2 = build_legs([b2 := _pt("b2", rep, "high", 20, 40.0, 22), c], rep)
    assert legs2[0].knowable_time == T0 + timedelta(minutes=32)   # max(22, 32)
    assert not available_at(legs2[0], as_of_time=T0 + timedelta(minutes=25))
    assert available_at(legs2[0], as_of_time=T0 + timedelta(minutes=35))


# ---------------------------------------------------------------- 4
def test_time_query_never_borrows_a_foreign_domain_bar_index():
    """A transition with no info_time is unplaceable on the time axis and is
    NOT applied by a time-based status query — its bar index (possibly from
    another domain) gives it no meaning."""
    rep = _rep("C", k=2)
    p = _pt("p", rep, "low", 10, 10.0, 12)
    p.add_transition(7, STATUS_BROKEN, note="bar-only row (foreign domain)")
    p.add_transition(15, STATUS_SUPERSEDED, info_time=T0 + timedelta(minutes=15),
                     note="placeable")
    # time query at T0+12: the unplaceable break must NOT apply
    assert p.status_at(99, T0 + timedelta(minutes=12)) == STATUS_CONFIRMED
    # the placeable transition DOES apply at its own time
    assert p.status_at(99, T0 + timedelta(minutes=16)) == STATUS_SUPERSEDED
    # bar-only query (single declared domain) may still use the bar index
    assert p.status_at(8, None) == STATUS_BROKEN


# ---------------------------------------------------------------- 5
def test_cross_view_containment_without_times_is_refused():
    coarse = _lg("c", _rep("C", k=2), "a", "b", "up", 0, 1, 0.0, 100.0, 1,
                 times=False)
    fine = _lg("f", _rep("F", k=2), "x", "y", "up", 0, 1, 1.0, 2.0, 1,
               times=False)
    with pytest.raises(ValueError,
                       match="across views requires verified timestamps"):
        sp05_containment(coarse, fine)
    # same declared domain: index comparison stays legal
    fine2 = _lg("f2", _rep("C", k=2), "x", "y", "up", 0, 1, 1.0, 2.0, 1,
                times=False)
    assert sp05_containment(coarse, fine2) == "contained"


# ---------------------------------------------------------------- 6
def test_lifecycle_reset_at_b2_is_prevented_by_restore_history():
    """The audited B2 pattern: a reference broken before B2 must NOT come
    back as a fresh confirmed candidate when the world is regenerated."""
    rep = _rep("C", k=2)
    pol = _pol()
    pts = [_pt("L", rep, "low", 10, 10.0, 12),
           _pt("H", rep, "high", 20, 40.0, 22)]
    legs = [_lg("up", rep, "L", "H", "up", 10, 20, 10.0, 40.0, 22)]
    r = task_s1_structural_reference(pts, legs, 25, rep,
                                     "origin-of-last-confirmed-leg", pol,
                                     "P-ORIGIN",
                                     decision_time=T0 + timedelta(minutes=25),
                                     axis=AXIS)
    assert r.selected_id == "L"
    led = InterpretationLedger()
    led.record(r, payload={"kind": "T-S1", "points": pts, "legs": legs,
                           "rep": rep, "role": "origin-of-last-confirmed-leg",
                           "policy": pol, "policy_id": "P-ORIGIN",
                           "decision_time": T0 + timedelta(minutes=25),
                           "axis": AXIS})
    # an event breaks L at 30 (first break), then B2 at 50 regenerates the
    # world from scratch — the same identities reappear FRESH
    led.propagate(30, ["L"], changed_states={"L": STATUS_BROKEN},
                  update_time=T0 + timedelta(minutes=30), event_ref="E30")
    pts_b2 = [_pt("L", rep, "low", 10, 10.0, 12),
              _pt("H", rep, "high", 20, 40.0, 22)]
    legs_b2 = [_lg("up", rep, "L", "H", "up", 10, 20, 10.0, 40.0, 22)]
    # WITHOUT restore_history the regenerated row is fresh confirmed (the
    # audited reset); with it, the recorded lifecycle is recovered
    assert pts_b2[0].status_at(50, T0 + timedelta(minutes=50)) == STATUS_CONFIRMED
    n = led.restore_history(pts_b2)
    assert n >= 1
    assert pts_b2[0].status_at(50, T0 + timedelta(minutes=50)) == STATUS_BROKEN
    r_b2 = task_s1_structural_reference(pts_b2, legs_b2, 50, rep,
                                        "origin-of-last-confirmed-leg", pol,
                                        "P-ORIGIN",
                                        decision_time=T0 + timedelta(minutes=50),
                                        axis=AXIS)
    # the historically broken reference can NOT be re-selected as fresh
    assert r_b2.selected_id != "L"
    assert r_b2.status == "unresolved"


# ---------------------------------------------------------------- 7
def test_t2_only_recording_persists_broken_transition():
    """Lifecycle transitions must persist even when the ONLY payload that
    referenced the candidate is a T-S2 refs_by_view record (no points list)."""
    rep = _rep("C", k=2)
    ref = _pt("L", rep, "low", 10, 10.0, 12)
    ev = task_s2_event_binding(20, 0.0, {"C": [ref]}, 20,
                               event_time=T0 + timedelta(minutes=20),
                               axis=AXIS, event_ref="E20")
    assert ev.binding_kinds == {"L": "first-break"}
    led = InterpretationLedger()
    led.record(ev, payload={"kind": "T-S2", "event_bar": 20, "close_price": 0.0,
                            "refs_by_view": {"C": [ref]},
                            "event_time": T0 + timedelta(minutes=20),
                            "event_ref": "E20", "axis": AXIS,
                            "tie_policy": TIE_CROSS_EQUAL_UNBOUND})
    led.propagate(20, ["L"], changed_states={"L": STATUS_BROKEN},
                  update_time=T0 + timedelta(minutes=20), event_ref="E20")
    # the transition reached the referenced point (refs_by_view shape)
    assert ref.status_at(20, T0 + timedelta(minutes=20),
                         excluding_event_ref="E20") != STATUS_BROKEN
    assert ref.status_at(21, T0 + timedelta(minutes=21)) == STATUS_BROKEN
    # and the recomputed T-S2 result keeps its recorded binding kind
    v2 = led.versions[ev.task_id + "#1"][1]["result"]
    assert v2.binding_kinds == {"L": "first-break"}


# ---------------------------------------------------------------- 8
def test_pre_event_binding_survives_the_events_own_transition():
    """PRE/EVENT/POST phases are explicit; replaying an event after its own
    same-time broken transition was applied must not flip first-break into
    later-interaction; binding_kinds appear in difference accounting."""
    rep = _rep("C", k=2)
    ref = _pt("L", rep, "low", 10, 10.0, 12)
    t_ev = T0 + timedelta(minutes=20)
    ev = task_s2_event_binding(20, 0.0, {"C": [ref]}, 20, event_time=t_ev,
                               axis=AXIS, event_ref="E20")
    assert ev.event_phase is not None
    assert ev.event_phase[PHASE_PRE_EVENT] == {"L": STATUS_CONFIRMED}
    assert ev.event_phase[PHASE_BINDING]["binding_kinds"] == {"L": "first-break"}
    assert ev.event_phase[PHASE_POST_EVENT]["L"] == STATUS_BROKEN
    # apply the event's own transition at the SAME timestamp…
    ref.add_transition(20, STATUS_BROKEN, info_time=t_ev, event_ref="E20",
                       note="the event's own break")
    # …and replay: the binding kind must be STABLE
    ev2 = task_s2_event_binding(20, 0.0, {"C": [ref]}, 20, event_time=t_ev,
                                axis=AXIS, event_ref="E20")
    assert ev2.binding_kinds == {"L": "first-break"}
    # without the event's transition the later state is visible (append-only)
    ev3 = task_s2_event_binding(20, 0.0, {"C": [ref]}, 20, event_time=t_ev,
                                axis=AXIS)
    assert ev3.binding_kinds == {"L": "later-interaction"}
    # difference accounting reports binding-kind changes: a replay WITHOUT
    # the event-ref exclusion sees the applied break and the computed diff
    # names the binding_kinds field (never a silent rewrite)
    led = InterpretationLedger()
    led.record(ev, payload={"kind": "T-S2", "event_bar": 20, "close_price": 0.0,
                            "refs_by_view": {"C": [ref]}, "event_time": t_ev,
                            "axis": AXIS,
                            "tie_policy": TIE_CROSS_EQUAL_UNBOUND})
    led.propagate(20, ["L"], changed_states={"L": STATUS_BROKEN},
                  update_time=t_ev)
    diffs = led.versions["T-S2#1"][1]["computed_changes"]
    kinds_diff = [d for d in diffs if d.get("field") == "binding_kinds"]
    assert kinds_diff, f"binding_kinds missing from difference accounting: {diffs}"
    assert kinds_diff[0]["before"] == {"L": "first-break"}
    assert kinds_diff[0]["after"] == {"L": "later-interaction"}


# ---------------------------------------------------------------- 9
def test_tie_policy_and_tie_behavior_cannot_contradict():
    rep = _rep("C", k=2)
    ref = _pt("L", rep, "low", 10, 10.0, 12)
    # the audited contradiction: boolean says bound, policy says unbound
    with pytest.raises(ValueError, match="tie-policy contradiction"):
        task_s2_event_binding(20, 10.0, {"C": [ref]}, 20, tie_bound=True,
                              event_time=T0 + timedelta(minutes=20), axis=AXIS)
    # the declared policy governs actual behavior: UNBOUND → equality no bind
    r = task_s2_event_binding(20, 10.0, {"C": [ref]}, 20,
                              event_time=T0 + timedelta(minutes=20), axis=AXIS,
                              tie_policy=TIE_CROSS_EQUAL_UNBOUND)
    assert r.survivors == []
    # the BOUND policy makes equality a crossing — declared AND effective
    r2 = task_s2_event_binding(20, 10.0, {"C": [ref]}, 20,
                               event_time=T0 + timedelta(minutes=20), axis=AXIS,
                               tie_policy=TIE_CROSS_EQUAL_BOUND_V1)
    assert r2.survivors == ["L"]
    assert r2.policy_snapshots["tie_policy"]["value"] == TIE_CROSS_EQUAL_BOUND_V1


# ---------------------------------------------------------------- 10
def test_policy_mutation_after_result_creation_is_never_silent():
    pol = PolicyRegistry()
    pol.register("P-ORIGIN", "v1 description", "origin-of-last-confirmed-leg")
    rep = _rep("C", k=2)
    pts = [_pt("L", rep, "low", 10, 10.0, 12)]
    legs = []
    r = task_s1_structural_reference(pts, legs, 14, rep,
                                     "last-confirmed-extreme", pol, "P-ORIGIN",
                                     decision_time=T0 + timedelta(minutes=14),
                                     axis=AXIS)
    snap = r.policy_snapshots["P-ORIGIN"]
    assert snap["version"] == 1 and snap["value"] == "origin-of-last-confirmed-leg"
    ref_v1 = pol.ref("P-ORIGIN")
    # mutate the registry entry after the result exists
    pol.register("P-ORIGIN", "v2 MUTATED", "something-else")
    assert pol.ref("P-ORIGIN") != ref_v1              # versioned identity
    # the historical result still carries its own exact policy meaning
    assert r.policy_snapshots["P-ORIGIN"]["version"] == 1
    assert r.policy_snapshots["P-ORIGIN"]["value"] == "origin-of-last-confirmed-leg"
    # a recomputation at the later registry state reports the policy change
    led = InterpretationLedger()
    led.record(r, payload={"kind": "T-S1", "points": pts, "legs": legs,
                           "rep": rep, "role": "last-confirmed-extreme",
                           "policy": pol, "policy_id": "P-ORIGIN",
                           "decision_time": T0 + timedelta(minutes=14),
                           "axis": AXIS})
    led.propagate(15, ["L"], update_time=T0 + timedelta(minutes=15))
    diffs = led.versions["T-S1#1"][1]["computed_changes"]
    assert any(d.get("field") in ("policy_refs", "policy_snapshots")
               for d in diffs)


# ---------------------------------------------------------------- 11
def test_t3_requires_decision_boundary_for_time_bearing_legs():
    coarse = _lg("c", _rep("C", k=2), "a", "b", "up", 0, 10, 0.0, 100.0, 10)
    fine = _lg("f", _rep("F", k=2), "x", "y", "up", 1, 2, 1.0, 2.0, 2)
    with pytest.raises(ValueError, match="boundary"):
        task_s3_entry_leg(coarse, [fine], 100, _rep("F", k=2), decision_time=None)
    # with the boundary the task runs and the result RECORDS it
    r = task_s3_entry_leg(coarse, [fine], 100, _rep("F", k=2),
                          decision_time=T0 + timedelta(minutes=100), axis=AXIS)
    assert r.decision_time == T0 + timedelta(minutes=100)
    assert r.selected_id == "f"


# ---------------------------------------------------------------- 12
def test_provisional_policy_survives_replay_with_exact_declared_values():
    rep = _rep("C", k=2)
    prov = _pt("P", rep, "low", 3, 10.0, 5, status=STATUS_PROVISIONAL)
    t4 = T0 + timedelta(minutes=4)
    ev = task_s2_event_binding(4, 0.0, {"C": [prov]}, 4, event_time=t4,
                               axis=AXIS, allow_provisional=True)
    assert ev.survivors == ["P"]
    assert ev.binding_kinds["P"] == "provisional:first-break"
    assert ev.policy_snapshots["allow_provisional"]["value"] is True
    led = InterpretationLedger()
    led.record(ev, payload={"kind": "T-S2", "event_bar": 4, "close_price": 0.0,
                            "refs_by_view": {"C": [prov]}, "event_time": t4,
                            "allow_provisional": True, "axis": AXIS,
                            "event_ref": "E4",
                            "tie_policy": TIE_CROSS_EQUAL_UNBOUND})
    led.propagate(4, ["P"], changed_states={"P": STATUS_BROKEN},
                  update_time=t4, event_ref="E4")
    replay = led.versions["T-S2#1"][1]["result"]
    # replay preserves the declared provisional policy AND the pre-event kind
    assert replay.policy_snapshots["allow_provisional"]["value"] is True
    assert replay.binding_kinds["P"] == "provisional:first-break"
    assert replay.event_phase[PHASE_BINDING]["binding_kinds"] == {
        "P": "provisional:first-break"}
    # the event's own transition never rewrites its binding: NO computed diff
    assert led.versions["T-S2#1"][1]["computed_changes"] == []
    # without the flag the csm default excludes provisional references
    r2 = task_s2_event_binding(4, 0.0, {"C": [prov]}, 4, event_time=t4,
                               axis=AXIS)
    assert r2.survivors == []


# ---------------------------------------------------------------- 13
def test_transitive_dependency_recomputation_a_b_c():
    """A -> B -> C: changing A recomputes B; when B materially changes, C is
    reconsidered too.  Unaffected results stay at version 1.  Cycles are
    detected explicitly."""
    rep = _rep("C", k=2)
    pol = _pol()
    a_pts = [_pt("A_root", rep, "low", 10, 10.0, 12),
             _pt("A_alt", rep, "high", 20, 40.0, 22)]
    a_legs = [_lg("A_leg", rep, "A_root", "A_alt", "up", 10, 20, 10.0, 40.0, 22)]
    rA = task_s1_structural_reference(a_pts, a_legs, 25, rep,
                                      "origin-of-last-confirmed-leg", pol,
                                      "P-ORIGIN",
                                      decision_time=T0 + timedelta(minutes=25),
                                      axis=AXIS)
    assert rA.selected_id == "A_root"

    b_pts = [_pt("B_root", rep, "low", 10, 10.0, 12),
             _pt("B_alt", rep, "high", 20, 40.0, 22)]
    b_legs = [_lg("B_leg", rep, "B_root", "B_alt", "up", 10, 20, 10.0, 40.0, 22)]
    rB = task_s1_structural_reference(b_pts, b_legs, 25, rep,
                                      "last-confirmed-extreme", pol, None,
                                      decision_time=T0 + timedelta(minutes=25),
                                      axis=AXIS)
    c_pts = [_pt("C_root", rep, "low", 10, 10.0, 12),
             _pt("C_alt", rep, "high", 20, 40.0, 22)]
    rC = task_s5_falsifier(
        [{"interpretation": "I", "view": "C", "role": "last-confirmed-extreme",
          "side": "low"}], c_pts, [], 25,
        decision_time=T0 + timedelta(minutes=25), axis=AXIS)
    rD = task_s1_structural_reference(
        [_pt("D_root", rep, "low", 10, 10.0, 12)], [], 25, rep,
        "last-confirmed-extreme", pol, None,
        decision_time=T0 + timedelta(minutes=25), axis=AXIS)

    led = InterpretationLedger()
    uid_a = led.record(rA, payload={"kind": "T-S1", "points": a_pts,
                                    "legs": a_legs, "rep": rep,
                                    "role": "origin-of-last-confirmed-leg",
                                    "policy": pol, "policy_id": "P-ORIGIN",
                                    "decision_time": T0 + timedelta(minutes=25),
                                    "axis": AXIS})
    uid_b = led.record(rB, payload={"kind": "T-S1", "points": b_pts,
                                    "legs": b_legs, "rep": rep,
                                    "role": "last-confirmed-extreme",
                                    "policy": pol, "policy_id": None,
                                    "decision_time": T0 + timedelta(minutes=25),
                                    "axis": AXIS},
                       )
    led._result_deps[uid_b] = {uid_a}          # B depends on result A
    uid_c = led.record(rC, payload={"kind": "T-S5",
                                    "claims": [{"interpretation": "I",
                                                "view": "C",
                                                "role": "last-confirmed-extreme",
                                                "side": "low"}],
                                    "points": c_pts, "legs": [],
                                    "decision_time": T0 + timedelta(minutes=25),
                                    "axis": AXIS})
    led._result_deps[uid_c] = {uid_b}          # C depends on result B
    uid_d = led.record(rD, payload={"kind": "T-S1", "points": [
        _pt("D_root", rep, "low", 10, 10.0, 12)], "legs": [], "rep": rep,
        "role": "last-confirmed-extreme", "policy": pol, "policy_id": None,
        "decision_time": T0 + timedelta(minutes=25), "axis": AXIS})
    led._result_deps[uid_d] = set()            # D is independent

    # break A_root: A is reconsidered; the registered edges A->B->C are
    # followed TRANSITIVELY (B and C must leave version 1); unrelated D stays
    led.propagate(30, ["A_root"],
                  changed_states={"A_root": STATUS_BROKEN},
                  update_time=T0 + timedelta(minutes=30))
    v = {uid: len(led.versions[uid]) for uid in (uid_a, uid_b, uid_c, uid_d)}
    assert v[uid_a] == 2                       # A recomputed
    assert v[uid_b] == 2                       # B reconsidered (A->B)
    assert v[uid_c] == 2                       # C reconsidered (B->C, transitive)
    assert v[uid_d] == 1                       # unrelated D untouched
    # every step records its computed differences / cascade source
    steps = [e for e in led.revisions if e.get("kind") == "recomputation"]
    assert len(steps) == 3
    assert any(e.get("cascade_from") for e in steps)
    # cycle detection: a cyclic edge is reported explicitly and cannot loop
    led._result_deps[uid_a] = {uid_c}          # close the cycle C -> A
    led.propagate(32, ["B_alt"], update_time=T0 + timedelta(minutes=32))
    assert any(r.get("kind") == "dependency-cycle" for r in led.revisions)


# ---------------------------------------------------------------- 14
def test_terminal_provisional_candidates_retained_across_prefixes():
    """Terminal provisional F-T candidates observable in truncated prefixes
    must not silently vanish from a longer-history inventory: they persist
    with their lifecycle (confirmed, or superseded-but-retained)."""
    n = 60
    closes = pd.Series(100.0, index=pd.date_range(T0, periods=n, freq="1min"))
    highs = closes + 5.0
    lows = closes - 5.0
    # a long up-run with an extreme at bar 20, later displaced at bar 40
    highs.iloc[20] = 120.0
    highs.iloc[40] = 130.0
    lows.iloc[50] = 90.0                    # reversal >= tau at the end
    bars = pd.DataFrame({"open": closes, "high": highs, "low": lows,
                         "close": closes}, index=closes.index)
    rep = _rep("T", family="F-T", tau=10.0)
    prefix_ids = set()
    for cut in (25, 35, 45):
        pts_p = ft_turning_points(bars.iloc[:cut], tau=10.0, rep=rep)
        prefix_ids |= {p.candidate_id for p in pts_p}
    pts_full = ft_turning_points(bars, tau=10.0, rep=rep)
    full_ids = {p.candidate_id for p in pts_full}
    missing = prefix_ids - full_ids
    assert not missing, f"prefix candidates silently discarded: {sorted(missing)[:5]}"
    # every retired candidate carries its lifecycle (superseded + by id)
    for p in pts_full:
        if p.status == STATUS_SUPERSEDED:
            assert p.superseded_by is not None
    # and superseded retention never leaks into selection
    legs = build_legs(pts_full, rep)
    assert all(l.start_id != p.candidate_id or p.status != STATUS_SUPERSEDED
               for l in legs for p in pts_full
               if p.candidate_id in (l.start_id, l.end_id))
