"""Final targeted audit patch — regression tests for the four remaining
reproducible correctness defects (independent re-audit of e90a62f):

  1. F-K tail knowability + T-S2 status gating (prefix/full equivalence)
  2. T-S3 cross-timeframe containment on verified timestamps + decision-time
     availability
  3. T-S5 origin-of-last-confirmed-leg direction validation (all roles)
  4. Same-bar ambiguity propagation to task results (auditor's M1/D4/D5
     pattern) without downgrading unaffected choices
  plus: OHLC-endpoint order evidence (factual) used in ambiguity accounting.
"""
from __future__ import annotations

from datetime import timedelta

import pandas as pd
import pytest

from trading_system.research.contextual_selection import (
    REASON_AI,
    REASON_IC,
    STATUS_BROKEN,
    STATUS_CONFIRMED,
    STATUS_PROVISIONAL,
    STATUS_SUPERSEDED,
    X_KNOW,
    X_STATE,
    X_SUPER,
    LegCandidate,
    PointCandidate,
    PolicyRegistry,
    Representation,
    available_at,
    fk_turning_points,
    task_s1_structural_reference,
    task_s2_event_binding,
    task_s3_entry_leg,
    task_s5_falsifier,
)

T0 = pd.Timestamp("2025-01-01 00:00:00")


def _rep(view: str, family: str = "F-K", **params) -> Representation:
    return Representation(family=family, view_id=view, scale_label=view,
                          params=tuple(sorted(params.items())))


def _pt(pid, rep, side, occ, level, know, status="confirmed", **kw):
    return PointCandidate(
        candidate_id=pid, rep=rep, side=side, occurrence_bar=occ, level=level,
        knowable_bar=know, status=status,
        occurrence_time=T0 + timedelta(minutes=occ),
        knowable_time=T0 + timedelta(minutes=know), **kw)


def _bars(rows):
    """rows: list of (open, high, low, close) with a minute DatetimeIndex."""
    idx = pd.date_range(T0, periods=len(rows), freq="min")
    return pd.DataFrame(
        {"open": [r[0] for r in rows], "high": [r[1] for r in rows],
         "low": [r[2] for r in rows], "close": [r[3] for r in rows],
         "volume": [1.0] * len(rows)}, index=idx)


# --------------------------------------------------------------------------
# 1 — F-K tail knowability (truncated-prefix leak) + T-S2 status gating
# --------------------------------------------------------------------------

def _tail_fixture():
    # k=2; a low at bar 3 that confirms at bar 5
    rows = [(6, 7, 5, 6)] * 8
    rows[3] = (6, 7, 1.0, 6)          # unique low of left window [1..3]
    full = _bars(rows)
    trunc = full.iloc[:5]              # confirmation bar 5 is beyond the data
    rep = _rep("C", k=2)
    return full, trunc, rep


def test_tail_knowable_time_never_claims_last_bar():
    full, trunc, rep = _tail_fixture()
    p_trunc = [p for p in fk_turning_points(trunc, 2, rep) if p.side == "low"][0]
    p_full = [p for p in fk_turning_points(full, 2, rep) if p.side == "low"][0]
    assert p_trunc.knowable_bar == 5 and p_trunc.status == STATUS_PROVISIONAL
    # the truncated candidate must NOT claim the last observed timestamp
    assert p_trunc.knowable_time is None
    assert p_full.knowable_time == pd.Timestamp(full.index[5])
    # auditor's probe at bar 4: both must agree the candidate is NOT available
    t4 = pd.Timestamp(full.index[4])
    assert available_at(p_trunc, as_of_time=t4) is False
    assert available_at(p_full, as_of_time=t4) is False
    # no over-claim at ANY query time: truncated implies full
    for t in full.index:
        tt = pd.Timestamp(t)
        if available_at(p_trunc, as_of_time=tt):
            assert available_at(p_full, as_of_time=tt)


def test_tail_prefix_full_t2_event_binding_equivalence():
    full, trunc, rep = _tail_fixture()
    p_trunc = [p for p in fk_turning_points(trunc, 2, rep) if p.side == "low"][0]
    p_full = [p for p in fk_turning_points(full, 2, rep) if p.side == "low"][0]
    t4 = pd.Timestamp(full.index[4])
    # default contract (no provisional): both empty, no future reference
    r_t = task_s2_event_binding(4, 0.0, {"C": [p_trunc]}, 4, event_time=t4)
    r_f = task_s2_event_binding(4, 0.0, {"C": [p_full]}, 4, event_time=t4)
    assert r_t.survivors == [] and r_f.survivors == []
    assert {e.candidate_id for e in r_t.excluded} == {p_trunc.candidate_id}
    # explicit provisional use is occurrence-gated on BOTH runs (equivalence)
    r_t2 = task_s2_event_binding(4, 0.0, {"C": [p_trunc]}, 4, event_time=t4,
                                 allow_provisional=True)
    r_f2 = task_s2_event_binding(4, 0.0, {"C": [p_full]}, 4, event_time=t4,
                                 allow_provisional=True)
    assert r_t2.survivors == r_f2.survivors == [p_trunc.candidate_id]


def test_t2_status_gating_provisional_superseded_broken():
    rep = _rep("C", k=2)
    prov = _pt("prov", rep, "low", 3, 10.0, 5, status=STATUS_PROVISIONAL)
    sup = _pt("sup", rep, "low", 3, 10.0, 5)
    sup.add_transition(4, STATUS_SUPERSEDED, by="other", note="test")
    brk = _pt("brk", rep, "low", 3, 10.0, 4)   # knowable at the event time
    brk.add_transition(2, STATUS_BROKEN, note="test")   # broken BEFORE the event
    ok = _pt("ok", rep, "low", 3, 10.0, 4)   # knowable at the event time
    t4 = T0 + timedelta(minutes=4)
    r = task_s2_event_binding(4, 0.0, {"C": [prov, sup, brk, ok]}, 4,
                              event_time=t4)
    codes = {e.candidate_id: e.code for e in r.excluded}
    assert codes.get("prov") == X_STATE
    assert codes.get("sup") == X_SUPER
    # knowledge contract (file 16 T-S2): a historically-broken reference is
    # STILL bindable as a separate later factual interaction — never dropped
    assert set(r.survivors) == {"brk", "ok"}
    assert r.binding_kinds["ok"] == "first-break"
    assert r.binding_kinds["brk"] == "later-interaction"
    # explicit provisional contract opens prov only, tagged per SWS-04a
    r2 = task_s2_event_binding(4, 0.0, {"C": [prov]}, 4, event_time=t4,
                               allow_provisional=True)
    assert r2.survivors == ["prov"]
    assert r2.binding_kinds["prov"] == "provisional:first-break"


# --------------------------------------------------------------------------
# 2 — T-S3 / SP-05 cross-timeframe containment + decision-time availability
# --------------------------------------------------------------------------

def _leg(leg_id, t0m, t1m, p0, p1, knowm, view="F", direction="up"):
    rep = _rep(view, k=2)
    return LegCandidate(
        leg_id=leg_id, rep=rep, start_id=f"{leg_id}_s", end_id=f"{leg_id}_e",
        direction=direction, t0=0, t1=1, p_start=p0, p_end=p1,
        knowable_bar=0, completed=True,
        t0_time=T0 + timedelta(minutes=t0m),
        t1_time=T0 + timedelta(minutes=t1m),
        knowable_time=T0 + timedelta(minutes=knowm))


def test_t3_containment_uses_timestamps_not_indices():
    # coarse leg: times 100..200, prices 0..100
    coarse = _leg("coarse", 100, 200, 0.0, 100.0, 200, view="C")
    # fine INSIDE on time axis but its raw indices are outside the coarse
    # pair's indices — the timestamps must govern
    inside = _leg("inside", 120, 180, 20.0, 80.0, 180)
    inside.t0, inside.t1 = 50, 60          # misleading raw indices
    outside = _leg("outside", 210, 260, 20.0, 80.0, 260)
    overlap = _leg("overlap", 150, 230, 20.0, 80.0, 230)
    from trading_system.research.contextual_selection import sp05_containment
    assert sp05_containment(coarse, inside) == "contained"
    assert sp05_containment(coarse, outside) == "disjoint"
    assert sp05_containment(coarse, overlap) == "escaping"


def test_t3_decision_time_availability_check():
    coarse = _leg("coarse", 100, 200, 0.0, 100.0, 200, view="C")
    inside = _leg("inside", 120, 180, 20.0, 80.0, 180)
    late = _leg("late", 120, 180, 30.0, 70.0, 250)   # knowable after decision
    rep = _rep("F", k=2)
    r = task_s3_entry_leg(coarse, [inside, late], 210, rep,
                          decision_time=T0 + timedelta(minutes=210))
    codes = {e.candidate_id: e.code for e in r.excluded}
    assert codes.get("late") == X_KNOW
    assert r.survivors == ["inside"] and r.selected_id == "inside"
    # the coarse leg itself must be knowable at the decision time
    r2 = task_s3_entry_leg(coarse, [inside], 150, rep,
                           decision_time=T0 + timedelta(minutes=150))
    assert r2.status == "unresolved"   # coarse knowable only at 200


def test_t3_mixed_time_index_pair_refused():
    from trading_system.research.contextual_selection import sp05_containment
    coarse = _leg("coarse", 100, 200, 0.0, 100.0, 200, view="C")
    no_times = LegCandidate("bare", _rep("F", k=2), "a", "b", "up", 0, 1,
                            1.0, 2.0, 1)
    with pytest.raises(ValueError, match="timestamps on BOTH legs"):
        sp05_containment(coarse, no_times)


# --------------------------------------------------------------------------
# 3 — T-S5 origin direction validation (all roles)
# --------------------------------------------------------------------------

def _s5_world():
    rep_c = _rep("C", k=2)
    rep_f = _rep("F", k=2)
    pts = [
        _pt("A", rep_c, "low", 10, 10.0, 12),
        _pt("B", rep_c, "high", 20, 40.0, 22),
        _pt("C", rep_c, "low", 30, 20.0, 32),
    ]
    legs = [
        LegCandidate("up1", rep_c, "A", "B", "up", 10, 20, 10.0, 40.0, 22),
        LegCandidate("dn1", rep_c, "B", "C", "down", 20, 30, 40.0, 20.0, 32),
    ]
    return pts, legs


def test_s5_origin_direction_validated():
    pts, legs = _s5_world()
    claim = {"interpretation": "I", "view": "C",
             "role": "origin-of-last-confirmed-leg"}
    # last confirmed leg is dn1 (down): its origin is B
    ok = task_s5_falsifier([{**claim, "direction": "down"}], pts, legs, 40)
    assert ok.status == "justified" and ok.selected_id == "B"
    # missing direction: explicit unresolved (IC) — NOT the same justified result
    miss = task_s5_falsifier([{**claim, "direction": None}], pts, legs, 40)
    assert miss.status == "unresolved"
    assert miss.unresolved is not None and miss.unresolved.reason_code == REASON_IC
    # opposite direction: explicit unresolved (AI) — NOT the same justified result
    opp = task_s5_falsifier([{**claim, "direction": "up"}], pts, legs, 40)
    assert opp.status == "unresolved"
    assert opp.unresolved is not None and opp.unresolved.reason_code == REASON_AI
    assert opp.selected_id is None


def test_s5_all_roles_direction_behavior():
    pts, legs = _s5_world()
    # low-of-current-leg selects per direction (task-specific effect)
    lo_dn = task_s5_falsifier([{"interpretation": "I", "view": "C",
                                "role": "low-of-current-leg",
                                "direction": "down"}], pts, legs, 40)
    lo_up = task_s5_falsifier([{"interpretation": "I", "view": "C",
                                "role": "low-of-current-leg",
                                "direction": "up"}], pts, legs, 40)
    assert lo_dn.selected_id == "C"    # low of last down leg B->C
    assert lo_up.selected_id == "A"    # low of last up leg A->B
    # missing/invalid direction -> explicit IC unresolved
    bad = task_s5_falsifier([{"interpretation": "I", "view": "C",
                              "role": "high-of-current-leg"}], pts, legs, 40)
    assert bad.status == "unresolved"
    assert bad.unresolved.reason_code == REASON_IC
    # last-confirmed-extreme keeps its side-based contract
    ext = task_s5_falsifier([{"interpretation": "I", "view": "C",
                              "role": "last-confirmed-extreme",
                              "side": "low"}], pts, legs, 40)
    assert ext.selected_id == "C"


# --------------------------------------------------------------------------
# 4 — same-bar ambiguity propagation (auditor's M1/D4/D5 pattern)
# --------------------------------------------------------------------------

def _amb_world(evidence=None):
    """M1-shaped: a low origin (same-bar order unresolved) of an up leg."""
    rep = _rep("T", family="F-T", tau=5.0)
    low = _pt("low@1327", rep, "low", 1327, 28.0, 1329,
              same_bar_order="unresolved", same_bar_evidence=evidence)
    high = _pt("high@1329", rep, "high", 1329, 50.0, 1331)
    legs = [LegCandidate("leg1327-1329", rep, "low@1327", "high@1329", "up",
                         1327, 1329, 28.0, 50.0, 1331)]
    return rep, [low, high], legs


def test_same_bar_ambiguity_surfaces_on_t1_selection():
    # auditor's M1/D4/D5 pattern: selected origin has unresolved intrabar
    # order (OHLC endpoints interior) -> must NOT be fully justified
    pol = PolicyRegistry()
    pol.register("P-ORIGIN", "origin role", "origin-of-last-confirmed-leg")
    rep, pts, legs = _amb_world(evidence=None)
    r = task_s1_structural_reference(pts, legs, 1335, rep,
                                     "origin-of-last-confirmed-leg", pol,
                                     "P-ORIGIN")
    assert r.status == "unresolved"
    assert r.selected_id is None
    assert r.survivors == ["low@1327"]
    assert r.unresolved is not None and r.unresolved.reason_code == REASON_AI
    assert "same-bar order unavailable" in " ".join(r.notes)
    # dependents are blocked, not silently fed
    assert "T-S5-falsifier" in r.unresolved.dependents_blocked


def test_same_bar_endpoint_evidence_does_not_downgrade():
    # when OHLC endpoints PROVE the order the choice is unrelated to the
    # ambiguity: stays justified and the factual resolution is noted
    pol = PolicyRegistry()
    pol.register("P-ORIGIN", "origin role", "origin-of-last-confirmed-leg")
    rep, pts, legs = _amb_world(evidence="proven:low-first:open-at-low")
    r = task_s1_structural_reference(pts, legs, 1335, rep,
                                     "origin-of-last-confirmed-leg", pol,
                                     "P-ORIGIN")
    assert r.status == "justified" and r.selected_id == "low@1327"
    assert any("proven by OHLC endpoints" in n for n in r.notes)


def test_same_bar_constrained_evidence_stays_material():
    # close-at-extreme evidence is CONSTRained but not unique: the first-touch
    # order is not proven, so the ambiguity remains material (AI)
    pol = PolicyRegistry()
    pol.register("P-ORIGIN", "origin role", "origin-of-last-confirmed-leg")
    rep, pts, legs = _amb_world(evidence="constrained:close-at-low")
    r = task_s1_structural_reference(pts, legs, 1335, rep,
                                     "origin-of-last-confirmed-leg", pol,
                                     "P-ORIGIN")
    assert r.status == "unresolved"
    assert r.unresolved is not None and r.unresolved.reason_code == REASON_AI
    assert "constrained" in r.unresolved.evidence_needed


def test_same_bar_ambiguity_on_unselected_candidate_is_unrelated():
    # ambiguity on a NON-selected candidate must not downgrade the result
    pol = PolicyRegistry()
    pol.register("P-ORIGIN", "origin role", "origin-of-last-confirmed-leg")
    rep, pts, legs = _amb_world(evidence=None)
    pts[1].same_bar_order = "unresolved"    # the non-origin high is ambiguous
    pts[0].same_bar_order = "resolved"
    r = task_s1_structural_reference(pts, legs, 1335, rep,
                                     "origin-of-last-confirmed-leg", pol,
                                     "P-ORIGIN")
    assert r.status == "justified" and r.selected_id == "low@1327"


def test_same_bar_ambiguity_surfaces_on_t5_falsifier():
    rep, pts, legs = _amb_world(evidence=None)
    r = task_s5_falsifier(
        [{"interpretation": "I", "view": "T",
          "role": "origin-of-last-confirmed-leg", "direction": "up"}],
        pts, legs, 1335)
    assert r.status == "unresolved"
    assert r.unresolved is not None and r.unresolved.reason_code == REASON_AI
    assert "same-bar order unresolved" in " ".join(r.notes)


# --------------------------------------------------------------------------
# OHLC-endpoint order evidence (factual accounting input)
# --------------------------------------------------------------------------

def test_endpoint_order_evidence_from_generator():
    # bar 3 is both the unique left-window high and low; its OPEN is at the
    # high -> the first-touch order is PROVEN high-first on both candidates
    rows = [(5, 6, 4, 5)] * 8
    rows[3] = (9.0, 9.0, 2.0, 5.0)      # open == high -> proven high-first
    bars = _bars(rows)
    rep = _rep("C", k=3)
    pts = [p for p in fk_turning_points(bars, 3, rep) if p.occurrence_bar == 3]
    assert len(pts) == 2
    assert all(p.same_bar_order == "unresolved" for p in pts)
    assert all(p.same_bar_evidence == "proven:high-first:open-at-high"
               for p in pts)
    # close at the high: order CONSTRained but not unique (not proven)
    rows2 = [(5, 6, 4, 5)] * 8
    rows2[3] = (5.0, 9.0, 2.0, 9.0)     # close == high -> constrained
    pts2 = [p for p in fk_turning_points(_bars(rows2), 3, rep)
            if p.occurrence_bar == 3]
    assert all(p.same_bar_evidence == "constrained:close-at-high" for p in pts2)
    # interior endpoints -> ordering unavailable
    rows3 = [(5, 6, 4, 5)] * 8
    rows3[3] = (5.0, 9.0, 2.0, 5.0)
    pts3 = [p for p in fk_turning_points(_bars(rows3), 3, rep)
            if p.occurrence_bar == 3]
    assert all(p.same_bar_evidence is None for p in pts3)
