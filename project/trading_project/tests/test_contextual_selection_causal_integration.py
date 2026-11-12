"""Causal state integration and root-cause remediation V1 — adversarial
regression tests (task §14).

Failure classes covered:
  * cross-timeframe look-ahead (support knowable only after the event)
  * leg availability at the decision boundary (T-S1 and T-S5)
  * broken-state persistence across candidate regeneration
  * pre/post-event binding stability (immutable first binding; later
    interactions preserved and tagged, never dropped)
  * provisional replay-policy retention through propagation
  * incomplete history (truncated windows; missing comparable time)
  * timestamp-only cross-domain comparisons (bar-index veto removed)
  * same-bar endpoint ambiguity (proven / constrained / unavailable)
  * stable candidate identity across overlapping replay windows
  * task-output ambiguity coverage (constrained stays material)
  * dependency recomputation (change-facts vs computed recomputations)
  * shared InformationKey axis (cross-timeline comparison refused)
"""
from __future__ import annotations

import copy
from datetime import timedelta

import pandas as pd
import pytest

from trading_system.research.information_time import InformationKeyError
from trading_system.research.contextual_selection import (
    REASON_AI,
    STATUS_BROKEN,
    STATUS_CONFIRMED,
    STATUS_PROVISIONAL,
    X_KNOW,
    X_STATE,
    X_SUPER,
    InterpretationLedger,
    LegCandidate,
    PointCandidate,
    PolicyRegistry,
    Representation,
    SharedInformationAxis,
    available_at,
    build_legs,
    fk_turning_points,
    material_same_bar_ambiguity,
    same_bar_evidence_class,
    sp05_containment,
    task_s1_structural_reference,
    task_s2_event_binding,
    task_s3_entry_leg,
    task_s5_falsifier,
)

T0 = pd.Timestamp("2025-01-01 00:00:00")

# consolidation V1: validated shared information-time axis over the fixture's
# T0-minute grid (every fixture timestamp lies on this grid)
from trading_system.research.contextual_selection import (  # noqa: E402
    SharedInformationAxis as _SharedInformationAxis,
)
AXIS = _SharedInformationAxis(
    "test-fixture-minute-grid",
    pd.date_range(T0, T0 + pd.Timedelta(minutes=2000), freq="1min"))



def _rep(view: str, family: str = "F-K", **params) -> Representation:
    return Representation(family=family, view_id=view, scale_label=view,
                          params=tuple(sorted(params.items())))


def _pt(pid, rep, side, occ, level, know, status="confirmed", **kw):
    return PointCandidate(
        candidate_id=pid, rep=rep, side=side,
        occurrence_bar=occ, level=level, knowable_bar=know,
        status=status,
        occurrence_time=T0 + timedelta(minutes=occ),
        knowable_time=T0 + timedelta(minutes=know), **kw)


def _lg(lid, rep, s, e, direction, t0, t1, p0, p1, know, **kw):
    return LegCandidate(
        leg_id=lid, rep=rep, start_id=s, end_id=e, direction=direction,
        t0=t0, t1=t1, p_start=p0, p_end=p1, knowable_bar=know,
        t0_time=kw.pop("t0_time", T0 + timedelta(minutes=t0)),
        t1_time=kw.pop("t1_time", T0 + timedelta(minutes=t1)),
        knowable_time=kw.pop("knowable_time", T0 + timedelta(minutes=know)),
        **kw)


def _pol_origin():
    pol = PolicyRegistry()
    pol.register("P-ORIGIN", "origin role", "origin-of-last-confirmed-leg")
    return pol


# --------------------------------------------------------------------------
# 1 — cross-timeframe look-ahead / leg availability (T-S1, T-S5)
# --------------------------------------------------------------------------

def test_t1_leg_support_must_be_available_at_decision():
    # points are available at t=50 but their leg only completes at t=60:
    # no justified T-S1 result at 50 may rest on that leg
    rep = _rep("C", k=2)
    pts = [_pt("lo", rep, "low", 30, 20.0, 35),
           _pt("hi", rep, "high", 40, 50.0, 45)]
    legs = [_lg("up1", rep, "lo", "hi", "up", 30, 40, 20.0, 50.0, 60)]
    pol = _pol_origin()
    r50 = task_s1_structural_reference(pts, legs, 50, rep,
                                       "origin-of-last-confirmed-leg", pol,
                                       "P-ORIGIN",
                                       decision_time=T0 + timedelta(minutes=50), axis=AXIS)
    assert r50.selected_id != "lo"          # leg support not yet knowable
    assert r50.status == "unresolved"
    codes = {e.candidate_id: e.code for e in r50.excluded}
    assert codes.get("up1") == X_KNOW
    r60 = task_s1_structural_reference(pts, legs, 60, rep,
                                       "origin-of-last-confirmed-leg", pol,
                                       "P-ORIGIN",
                                       decision_time=T0 + timedelta(minutes=60), axis=AXIS)
    assert r60.status == "justified" and r60.selected_id == "lo"


def test_t5_leg_support_availability_discipline():
    rep = _rep("C", k=2)
    pts = [_pt("lo", rep, "low", 30, 20.0, 35),
           _pt("hi", rep, "high", 40, 50.0, 45)]
    legs = [_lg("up1", rep, "lo", "hi", "up", 30, 40, 20.0, 50.0, 60)]
    claim = {"interpretation": "I", "view": "C",
             "role": "origin-of-last-confirmed-leg", "direction": "up"}
    r50 = task_s5_falsifier([claim], pts, legs, 50,
                            decision_time=T0 + timedelta(minutes=50), axis=AXIS)
    assert r50.status == "unresolved"      # supporting leg not yet knowable
    r60 = task_s5_falsifier([claim], pts, legs, 60,
                            decision_time=T0 + timedelta(minutes=60), axis=AXIS)
    assert r60.status == "justified" and r60.selected_id == "lo"


def test_status_at_time_axis_governs_over_domain_bar():
    # a transition placeable on the time axis must NOT be vetoed by a
    # domain-local bar index from another timeframe's query
    p = _pt("x", _rep("C", k=2), "high", 500, 10.0, 505)  # 1m-domain bars
    p.add_transition(505, STATUS_BROKEN,
                     info_time=T0 + timedelta(minutes=505), axis=AXIS)
    # query with a 5m-domain bar index (small) but the correct time
    assert p.status_at(100, T0 + timedelta(minutes=600)) == STATUS_BROKEN
    # before the transition time: still confirmed (time governs)
    assert p.status_at(100, T0 + timedelta(minutes=500)) == STATUS_CONFIRMED


# --------------------------------------------------------------------------
# 2 — broken-state persistence / regeneration
# --------------------------------------------------------------------------

def test_regenerated_candidates_restore_recorded_history():
    rep = _rep("C", k=2)
    p = _pt("L", rep, "low", 10, 20.0, 15)
    ledger = InterpretationLedger()
    claims = [{"interpretation": "I", "view": "C",
               "role": "origin-of-last-confirmed-leg", "direction": "up"}]
    legs = [_lg("up1", rep, "L", "H", "up", 10, 20, 20.0, 40.0, 25)]
    s5 = task_s5_falsifier(claims, [p], legs, 30, axis=AXIS, decision_time=T0 + timedelta(minutes=30))
    ledger.record(s5, payload={"kind": "T-S5", "claims": copy.deepcopy(claims),
                               "points": copy.deepcopy([p]),
                               "legs": copy.deepcopy(legs),
                               "state_id_prefix": "R", "axis": AXIS})
    ledger.propagate(30, ["L"], changed_states={"L": STATUS_BROKEN},
                     update_time=T0 + timedelta(minutes=30), axis=AXIS)
    # regeneration: a fresh copy with the same identity starts "clean"...
    fresh = _pt("L", rep, "low", 10, 20.0, 15)
    assert fresh.status_at(30, T0 + timedelta(minutes=30)) == STATUS_CONFIRMED
    # ...but restoring recorded history must bring the broken state back —
    # a historically broken reference never reappears as fresh confirmed
    n = ledger.restore_history([fresh], axis=AXIS)
    assert n >= 1
    assert fresh.status_at(30, T0 + timedelta(minutes=30)) == STATUS_BROKEN


# --------------------------------------------------------------------------
# 3 — pre/post-event binding stability (T-S2)
# --------------------------------------------------------------------------

def test_binding_survives_post_event_break_and_later_interactions_bind():
    rep = _rep("C", k=2)
    ref = _pt("ref", rep, "high", 10, 100.0, 12)
    t_ev1 = T0 + timedelta(minutes=20)
    # event 1: first break-side crossing
    ev1 = task_s2_event_binding(20, 110.0, {"C": [ref]}, 20, event_time=t_ev1, axis=AXIS,
                          event_ref="EV1")
    assert ev1.survivors == ["ref"]
    assert ev1.binding_kinds["ref"] == "first-break"
    # the event's post-state transition is applied AFTER the binding record
    ref.add_transition(20, STATUS_BROKEN, info_time=t_ev1,
                       note="break by event 1", event_ref="EV1", axis=AXIS)
    # the original binding record is immutable (still present, unchanged)
    assert ev1.survivors == ["ref"]
    assert ev1.binding_kinds["ref"] == "first-break"
    # event 2: a later close crossing of the already-broken reference —
    # the knowledge contract keeps it as a SEPARATE event (tagged B), never
    # dropped and never editing the first
    ev2 = task_s2_event_binding(30, 112.0, {"C": [ref]}, 30,
                                prev_close=90.0,
                                event_time=T0 + timedelta(minutes=30), axis=AXIS,
                                event_ref="EV2")
    assert ev2.survivors == ["ref"]
    assert ev2.binding_kinds["ref"] == "later-interaction"


def test_provisional_replay_policy_retained_through_propagation():
    rep = _rep("C", k=2)
    prov = _pt("tail", rep, "low", 3, 10.0, 99, status=STATUS_PROVISIONAL)
    ledger = InterpretationLedger()
    ev = task_s2_event_binding(4, 0.0, {"C": [prov]}, 4, prev_close=20.0,
                               event_time=T0 + timedelta(minutes=4),
                               allow_provisional=True, axis=AXIS,
                               event_ref="EV-PROV")
    assert ev.survivors == ["tail"]
    uid = ledger.record(ev, payload={
        "kind": "T-S2", "event_bar": 4, "close_price": 0.0,
        "refs_by_view": {"C": [copy.deepcopy(prov)]}, "decision_bar": 4,
        "prev_close": 20.0, "state_id_prefix": "P",
        "event_time": T0 + timedelta(minutes=4),
        "allow_provisional": True,          # declared Π_T — must survive
        "tie_policy": "TIE-CROSS-EQUAL-UNBOUND-V1",
        "event_ref": "EV-PROV",             # replay identity (audit F)
        "axis": AXIS})
    # a change fact on a dependency forces recomputation of this dependent
    log = ledger.propagate(6, ["tail"], changed_states={"tail": "knowable"},
                           update_time=T0 + timedelta(minutes=6), axis=AXIS)
    v2 = ledger.versions[uid][-1]
    assert v2["version"] == 2               # recomputed, not rewritten
    # the provisional binding SURVIVES the recompute (policy retained)
    assert v2["result"].survivors == ["tail"]


def test_no_provisional_policy_by_default():
    rep = _rep("C", k=2)
    prov = _pt("tail", rep, "low", 3, 10.0, 99, status=STATUS_PROVISIONAL)
    ev = task_s2_event_binding(4, 0.0, {"C": [prov]}, 4,
                               event_time=T0 + timedelta(minutes=4), axis=AXIS,
                               event_ref="EV-NOPROV")
    assert ev.survivors == []
    assert any(e.code == X_STATE for e in ev.excluded)


# --------------------------------------------------------------------------
# 4 — stable identity across replay windows
# --------------------------------------------------------------------------

def _id_bars():
    rows = [(5, 6, 4, 5)] * 30
    rows[10] = (5, 9.0, 4, 5)     # unique high at bar 10 of the window
    rows[20] = (5, 6, 1.0, 5)     # unique low at bar 20
    idx = pd.date_range(T0, periods=30, freq="min")
    return pd.DataFrame({"open": [r[0] for r in rows], "high": [r[1] for r in rows],
                         "low": [r[2] for r in rows], "close": [r[3] for r in rows],
                         "volume": [1.0] * 30}, index=idx)


def test_candidate_identity_stable_across_replay_windows():
    bars = _id_bars()
    rep = _rep("C", k=3)
    full = {p.side: p for p in fk_turning_points(bars, 3, rep, axis=AXIS)
            if p.occurrence_bar in (10, 20)}
    # a window that STARTS LATER shifts every local bar index (10 -> 5)…
    trunc = bars.iloc[5:]
    rerun = {p.side: p for p in fk_turning_points(trunc, 3, rep, axis=AXIS)
             if p.occurrence_bar in (5, 15)}
    # …but source/time identity is unchanged: the same historical candidate is
    # recognized across overlapping replay windows
    assert full["high"].candidate_id == rerun["high"].candidate_id
    assert full["low"].candidate_id == rerun["low"].candidate_id
    assert "@2025-01-01" in full["high"].candidate_id
    # distinct candidates at the same price stay distinct (identity is not
    # price-based)
    assert full["high"].candidate_id != full["low"].candidate_id


def test_leg_identity_stable_across_replay_windows():
    bars = _id_bars()
    rep = _rep("C", k=3)
    pts_full = fk_turning_points(bars, 3, rep, axis=AXIS)
    legs_full = build_legs(pts_full, rep)
    pts_trunc = fk_turning_points(bars.iloc[5:], 3, rep, axis=AXIS)
    legs_trunc = build_legs(pts_trunc, rep)
    ids_full = {l.leg_id for l in legs_full}
    ids_trunc = {l.leg_id for l in legs_trunc}
    shared = ids_full & ids_trunc
    assert shared, "identical market legs must share identity across windows"


# --------------------------------------------------------------------------
# 5 — same-bar endpoint ambiguity (proven / constrained / unavailable)
# --------------------------------------------------------------------------

def test_endpoint_evidence_three_class_semantics():
    from trading_system.research.contextual_selection.csm import _endpoint_order
    # open at the high: first touch PROVEN
    assert _endpoint_order(9.0, 9.0, 2.0, 5.0) == "proven:high-first:open-at-high"
    # open at the low: first touch PROVEN
    assert _endpoint_order(2.0, 9.0, 2.0, 5.0) == "proven:low-first:open-at-low"
    # close at the high: constrained but NOT unique (first touch unknown)
    assert _endpoint_order(5.0, 9.0, 2.0, 9.0) == "constrained:close-at-high"
    assert _endpoint_order(5.0, 9.0, 2.0, 2.0) == "constrained:close-at-low"
    # interior endpoints / flat bar: unavailable
    assert _endpoint_order(5.0, 9.0, 2.0, 5.0) is None
    assert _endpoint_order(5.0, 5.0, 5.0, 5.0) is None
    # classes: only proven resolves; constrained stays material
    assert same_bar_evidence_class("proven:high-first:open-at-high") == "proven"
    assert same_bar_evidence_class("constrained:close-at-high") == "constrained"
    assert same_bar_evidence_class(None) == "unavailable"
    prov_c = _pt("p", _rep("C", k=2), "high", 1, 1.0, 2,
                 same_bar_order="unresolved",
                 same_bar_evidence="proven:high-first:open-at-high")
    con_c = _pt("c", _rep("C", k=2), "high", 1, 1.0, 2,
                same_bar_order="unresolved",
                same_bar_evidence="constrained:close-at-high")
    non_c = _pt("n", _rep("C", k=2), "high", 1, 1.0, 2,
                same_bar_order="unresolved")
    assert not material_same_bar_ambiguity(prov_c)
    assert material_same_bar_ambiguity(con_c)      # constrained is material
    assert material_same_bar_ambiguity(non_c)


def test_t5_constrained_ambiguity_surfaces_ai():
    rep = _rep("T", family="F-T", tau=5.0)
    low = _pt("lo", rep, "low", 10, 20.0, 12,
              same_bar_order="unresolved",
              same_bar_evidence="constrained:close-at-low")
    high = _pt("hi", rep, "high", 20, 40.0, 22)
    legs = [_lg("up1", rep, "lo", "hi", "up", 10, 20, 20.0, 40.0, 22)]
    r = task_s5_falsifier(
        [{"interpretation": "I", "view": "T",
          "role": "origin-of-last-confirmed-leg", "direction": "up"}],
        [low, high], legs, 30, axis=AXIS, decision_time=T0 + timedelta(minutes=30))
    assert r.status == "unresolved"
    assert r.unresolved is not None and r.unresolved.reason_code == REASON_AI


# --------------------------------------------------------------------------
# 6 — dependency recomputation honesty + coverage
# --------------------------------------------------------------------------

def test_change_facts_and_recomputations_are_separate_streams():
    rep = _rep("C", k=2)
    lo = _pt("lo", rep, "low", 30, 20.0, 35)
    hi = _pt("hi", rep, "high", 40, 50.0, 45)
    legs = [_lg("up1", rep, "lo", "hi", "up", 30, 40, 20.0, 50.0, 45)]
    pol = _pol_origin()
    ledger = InterpretationLedger()
    r = task_s1_structural_reference([lo, hi], legs, 45, rep,
                                     "origin-of-last-confirmed-leg", pol,
                                     "P-ORIGIN",
                                     decision_time=T0 + timedelta(minutes=45), axis=AXIS)
    uid = ledger.record(r, payload={
        "kind": "T-S1", "points": copy.deepcopy([lo, hi]),
        "legs": copy.deepcopy(legs), "rep": rep, "role":
        "origin-of-last-confirmed-leg", "policy": pol, "policy_id": "P-ORIGIN",
        "state_id_prefix": "D", "decision_time": T0 + timedelta(minutes=45),
        "axis": AXIS})
    ledger.propagate(50, ["lo"], changed_states={"lo": STATUS_BROKEN},
                     update_time=T0 + timedelta(minutes=50), axis=AXIS)
    kinds = [x["kind"] for x in ledger.revisions]
    assert "change-fact" in kinds
    # the break fact cites its authorizing event when given
    ledger.record_change(50, "hi", "knowable", event_ref="event@50")
    fact = [x for x in ledger.revisions
            if x.get("kind") == "change-fact" and x.get("event_ref")][0]
    assert fact["event_ref"] == "event@50"
    # recomputation rows carry computed diffs, never caller-supplied ones
    recomp = [x for x in ledger.revisions if "computed_changes" in x]
    assert recomp and all("rule" in x for x in recomp)
    snap = ledger.snapshot()
    assert snap["n_dependents_without_payload"] == 0


def test_incomplete_dependency_coverage_is_tracked():
    rep = _rep("C", k=2)
    p = _pt("p", rep, "high", 1, 10.0, 2)
    ledger = InterpretationLedger()
    r = task_s2_event_binding(3, 11.0, {"C": [p]}, 3,
                              event_time=T0 + timedelta(minutes=3), axis=AXIS,
                              event_ref="EV-INCOMPLETE")
    ledger.record(r)                          # NO payload: non-recomputable
    snap = ledger.snapshot()
    assert snap["n_dependents_without_payload"] == 1


# --------------------------------------------------------------------------
# 7 — shared InformationKey axis
# --------------------------------------------------------------------------

def test_shared_axis_refuses_cross_timeline_and_missing_times():
    idx = pd.date_range("2025-01-01", periods=10, freq="min", tz="UTC")
    ax = SharedInformationAxis("master-1m-UTC", idx)
    k0 = ax.key_for_time(idx[2])
    k1 = ax.key_for_time(idx[7])
    assert k0 < k1
    assert ax.available(idx[2], idx[7]) is True
    assert ax.available(idx[7], idx[2]) is False
    # missing / off-grid times: explicit unavailability, never a claim
    assert ax.available(None, idx[7]) is False
    assert ax.available(idx[2], None) is False
    assert ax.available(pd.Timestamp("2025-01-01 00:00:30"), idx[7]) is False
    # cross-timeline comparison is forbidden by the CLOSED contract
    ax2 = SharedInformationAxis("other-timeline", idx)
    with pytest.raises(InformationKeyError):
        _ = k0 <= ax2.key_for_time(idx[7])


# --------------------------------------------------------------------------
# 8 — timestamp-only containment (mixed pair refused; documented single domain)
# --------------------------------------------------------------------------

def test_containment_mixed_pair_refused_single_domain_allowed():
    coarse = _lg("c", _rep("C", k=2), "a", "b", "up", 0, 1, 0.0, 100.0, 1,
                 t0_time=T0, t1_time=T0 + timedelta(minutes=100))
    fine = _lg("f", _rep("F", k=2), "a", "b", "up", 50, 60, 20.0, 80.0, 60,
               t0_time=T0 + timedelta(minutes=50),
               t1_time=T0 + timedelta(minutes=60))
    assert sp05_containment(coarse, fine) == "contained"
    bare = LegCandidate("bare", _rep("F", k=2), "x", "y", "up", 0, 1,
                        1.0, 2.0, 1)
    with pytest.raises(ValueError, match="timestamps on BOTH legs"):
        sp05_containment(coarse, bare)
    # neither has times: index comparison allowed ONLY inside one declared
    # domain (consolidation V1: bar numbers from different view domains do
    # not establish temporal containment — the audited counterexample)
    same_view_a = LegCandidate("sv_a", _rep("C", k=2), "x", "y", "up", 0, 10,
                               1.0, 2.0, 10)
    same_view_b = LegCandidate("sv_b", _rep("C", k=2), "x", "y", "up", 2, 5,
                               1.2, 1.8, 5)
    assert sp05_containment(same_view_a, same_view_b) == "contained"
    bare2 = LegCandidate("bare2", _rep("C", k=2), "x", "y", "up", 0, 10,
                         1.0, 2.0, 10)
    with pytest.raises(ValueError,
                       match="across views requires verified timestamps"):
        sp05_containment(bare2, bare)   # cross-view, no times: refused
