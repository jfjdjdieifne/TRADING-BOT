"""Audit-remediation regression tests for the contextual-selection V1 audit.

One focused test per confirmed defect category (audit §10):
  D1 cross-timeframe availability + chronological event replay
  D2 F-K confirmation endpoint + full left-context requirement
  D3 historical supersession stability + provisional-state behavior
  D4 same-bar high/low ambiguity + equal-extreme tie handling
  D5 actual dependent recomputation (no caller-supplied before/after)
  D6 direction-sensitive falsifiers + depth values + candidate completeness
  R  reproducible causal outputs (prefix replay determinism)
"""
from __future__ import annotations

from datetime import timedelta

import pandas as pd
import pytest

from trading_system.research.contextual_selection import (
    REASON_IC,
    STATUS_CONFIRMED,
    STATUS_PROVISIONAL,
    STATUS_SUPERSEDED,
    TIE_FT_EQ_FIRST,
    TIE_FT_EQ_LAST,
    X_KNOW,
    X_STATE,
    InterpretationLedger,
    LegCandidate,
    PointCandidate,
    PolicyRegistry,
    Representation,
    available_at,
    build_legs,
    candidate_record,
    fk_turning_points,
    ft_turning_points,
    reference_state_at,
    task_s1_structural_reference,
    task_s2_event_binding,
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


def _bars(lows, highs):
    n = len(lows)
    mid = [(lows[i] + highs[i]) / 2 for i in range(n)]
    return pd.DataFrame({"open": mid, "high": highs, "low": lows,
                         "close": mid, "volume": [1.0] * n},
                        index=pd.date_range(T0, periods=n, freq="min"))


# --------------------------------------------------------------------------
# D1 — cross-timeframe availability (future-reference contamination)
# --------------------------------------------------------------------------

def test_D1_cross_timeframe_unavailable_reference_cannot_bind():
    """A coarse reference whose information time is AFTER the fine event must
    be excluded X-KNOW even when its raw bar index looks small (the auditor's
    future-reference counterexample class)."""
    rep_c = _rep("C", k=5)
    rep_f = _rep("F", k=2)
    # coarse ref occurs "early" in coarse indices (bar 1300) but is knowable
    # at T0+300min — AFTER the fine event at T0+200min.
    late_ref = _pt("C-low", rep_c, "low", 1300, 100.0, 1305)
    late_ref.occurrence_time = T0 + timedelta(minutes=290)
    late_ref.knowable_time = T0 + timedelta(minutes=300)
    fine_ref = _pt("F-low", rep_f, "low", 190, 95.0, 192)
    event_time = T0 + timedelta(minutes=200)
    r = task_s2_event_binding(
        event_bar=200, close_price=90.0,
        refs_by_view={"C": [late_ref], "F": [fine_ref]},
        decision_bar=200, event_time=event_time)
    assert "F-low" in r.survivors
    assert "C-low" not in r.survivors
    codes = {e.candidate_id: e.code for e in r.excluded}
    assert codes.get("C-low") == X_KNOW


def test_D1_cross_view_requires_time_axis():
    """Raw indices from different timeframe domains are never compared: a
    multi-view query without shared timestamps must fail loud, not leak."""
    rep_c = _rep("C", k=5)
    rep_f = _rep("F", k=2)
    a = _pt("c1", rep_c, "low", 35, 20.0, 40)
    b = _pt("f1", rep_f, "low", 38, 25.0, 41)
    with pytest.raises(ValueError, match="information-time"):
        task_s2_event_binding(53, 19.0, {"C": [a], "F": [b]}, 53)


def test_D1_chronological_event_replay_uses_prior_state_only():
    """Events between boundaries t0 and t1 use the reference state knowable at
    t0 — a selection produced at t1 must never apply retroactively."""
    rep = _rep("F", k=2)
    ref_early = _pt("early", rep, "low", 10, 20.0, 12)
    ref_late = _pt("late", rep, "low", 60, 30.0, 62)
    history = [
        (T0 + timedelta(minutes=30), [ref_early]),   # selection at boundary b0
        (T0 + timedelta(minutes=70), [ref_late]),    # selection at boundary b1
    ]
    # an event at t=50 (between b0 and b1) sees only the b0 state
    state = reference_state_at(history, T0 + timedelta(minutes=50))
    assert [p.candidate_id for p in state] == ["early"]
    # an event at t=80 sees the b1 state
    state = reference_state_at(history, T0 + timedelta(minutes=80))
    assert [p.candidate_id for p in state] == ["late"]
    # a selection made at 55 whose reference is only knowable at 62 cannot
    # enter the binding of an event at t=60 (availability filter)
    history2 = [
        (T0 + timedelta(minutes=30), [ref_early]),
        (T0 + timedelta(minutes=55), [ref_late]),
    ]
    state = reference_state_at(history2, T0 + timedelta(minutes=60))
    # knowable only at 62 -> cannot enter the binding of an event at t=60
    assert state == []
    state = reference_state_at(history2, T0 + timedelta(minutes=65))
    assert [p.candidate_id for p in state] == ["late"]   # knowable by 65


# --------------------------------------------------------------------------
# D2 — F-K confirmation endpoint and full left context
# --------------------------------------------------------------------------

def test_D2_fk_confirmation_endpoint_inclusive_supersession():
    """Auditor's k=2 fixture: High 10 at bar 2, higher high 11 at bar 4.
    The earlier high must NOT be confirmed — the more extreme point at the
    confirmation bar itself supersedes first (inclusive window endpoint)."""
    n = 10
    lows = [5.0] * n
    highs = [8.0] * n
    highs[2] = 10.0
    highs[4] = 11.0
    bars = _bars(lows, highs)
    rep = _rep("C", k=2)
    pts = fk_turning_points(bars, k=2, rep=rep)
    p2 = [p for p in pts if p.occurrence_bar == 2 and p.side == "high"]
    p4 = [p for p in pts if p.occurrence_bar == 4 and p.side == "high"]
    assert p2 and p4
    assert p2[0].status == STATUS_SUPERSEDED          # NOT incorrectly confirmed
    assert p2[0].superseded_by == p4[0].candidate_id
    # historical reconstruction agrees: at bar 3 it was provisional
    assert p2[0].status_at(3) == STATUS_PROVISIONAL
    assert p2[0].status_at(4) == STATUS_SUPERSEDED
    assert p4[0].status == STATUS_CONFIRMED


def test_D2_fk_full_left_context_required():
    """Candidates from shortened left-edge windows are not emitted unless the
    explicitly different policy authorizes it."""
    n = 8
    lows = [5.0] * n
    lows[1] = 1.0            # a low inside the short left window (bar 1 < k=3)
    lows[5] = 2.0            # a valid low with full left context
    highs = [8.0] * n
    bars = _bars(lows, highs)
    rep = _rep("C", k=3)
    strict = fk_turning_points(bars, k=3, rep=rep)
    assert all(p.occurrence_bar >= 3 for p in strict)   # full left context only
    assert any(p.occurrence_bar == 5 for p in strict)   # valid candidates exist
    assert not any(p.occurrence_bar == 1 for p in strict)
    # explicit different policy slot may allow short left edges
    loose = fk_turning_points(bars, k=3, rep=rep, allow_short_left=True)
    assert any(p.occurrence_bar == 1 for p in loose)


# --------------------------------------------------------------------------
# D3 — historical status reconstruction
# --------------------------------------------------------------------------

def test_D3_later_supersession_does_not_rewrite_earlier_state():
    n = 30
    lows = [30.0] * n
    highs = [30.0] * n
    highs[10] = 40.0
    highs[12] = 45.0      # supersedes bar-10 high inside its window (k=5)
    bars = _bars(lows, highs)
    rep = _rep("C", k=5)
    pts = fk_turning_points(bars, k=5, rep=rep)
    p10 = next(p for p in pts if p.occurrence_bar == 10 and p.side == "high")
    assert p10.status == STATUS_SUPERSEDED
    # as-of queries reconstruct the status knowable at each boundary
    assert p10.status_at(10) == STATUS_PROVISIONAL
    assert p10.status_at(11) == STATUS_PROVISIONAL
    assert p10.status_at(12) == STATUS_SUPERSEDED   # knowable at the supersede bar
    assert p10.status_at(20) == STATUS_SUPERSEDED


def test_D3_provisional_state_explicit_exclusion():
    """allow_provisional is explicit task-level policy: without it provisional
    references get X-STATE and are never silently treated as confirmed."""
    rep = _rep("C", k=2)
    p_prov = _pt("hp", rep, "high", 10, 50.0, 15, status="provisional")
    pol = PolicyRegistry()
    pol.register("P-ORIGIN", "origin role", "origin-of-last-confirmed-leg")
    leg = LegCandidate("Lg1", rep, "hp", "ok", "down", 10, 20, 50.0, 40.0, 25)
    ok = _pt("ok", rep, "low", 20, 40.0, 25)
    r = task_s1_structural_reference([p_prov, ok], [leg], 14, rep,
                                     "origin-of-last-confirmed-leg", pol,
                                     "P-ORIGIN", allow_provisional=False)
    codes = {e.candidate_id: e.code for e in r.excluded}
    assert codes.get("hp") == X_STATE               # explicit exclusion
    r2 = task_s1_structural_reference([p_prov, ok], [leg], 14, rep,
                                      "origin-of-last-confirmed-leg", pol,
                                      "P-ORIGIN", allow_provisional=True)
    codes2 = {e.candidate_id: e.code for e in r2.excluded}
    assert codes2.get("hp") is None                  # allowed by explicit policy


# --------------------------------------------------------------------------
# D4 — same-bar ambiguity and equal-extreme ties
# --------------------------------------------------------------------------

def test_D4_no_zero_duration_legs_from_same_bar_order():
    rep = _rep("F", k=2)
    h = _pt("h@5", rep, "high", 5, 50.0, 10)
    l = _pt("l@5", rep, "low", 5, 20.0, 10)
    prev = _pt("h@1", rep, "high", 1, 40.0, 6)
    nxt = _pt("l@9", rep, "low", 9, 10.0, 14)
    amb = []
    legs = build_legs([prev, h, l, nxt], rep, ambiguities=amb)
    # no leg between the same-bar pair; the ambiguity is explicit
    assert all({leg.start_id, leg.end_id} != {"h@5", "l@5"} for leg in legs)
    assert any(a["kind"] == "same-bar-order-unresolved" for a in amb)
    assert all(leg.t1 > leg.t0 for leg in legs)     # never zero-duration
    # equal endpoints: direction not established -> no leg, explicit record
    amb2 = []
    eq_a = _pt("x@1", rep, "high", 1, 40.0, 6)
    eq_b = _pt("y@3", rep, "low", 3, 40.0, 8)
    legs2 = build_legs([eq_a, eq_b], rep, ambiguities=amb2)
    assert legs2 == []
    assert any(a["kind"] == "zero-amplitude-leg" for a in amb2)


def test_D4_ft_equal_extreme_tie_policy_explicit():
    """Equal extremes never silently prefer the latest bar: the default
    versioned policy keeps the first; the alternative only when declared."""
    n = 12
    lows = [18.0] * n
    highs = [19.0] * n
    highs[3] = 20.0
    highs[5] = 20.0        # equal extreme — not silently the new extreme
    lows[9] = 13.0         # reversal >= tau below the running high
    bars = _bars(lows, highs)
    rep = _rep("T", family="F-T", tau=4.0)
    amb = []
    pts = ft_turning_points(bars, tau=4.0, rep=rep,
                            tie_policy=TIE_FT_EQ_FIRST, ambiguities=amb)
    highs_reg = [p for p in pts if p.side == "high" and p.level == 20.0]
    assert highs_reg and highs_reg[0].occurrence_bar == 3     # FIRST kept
    # explicit alternative policy is available and identified
    pts_last = ft_turning_points(bars, tau=4.0, rep=rep, tie_policy=TIE_FT_EQ_LAST)
    highs_last = [p for p in pts_last if p.side == "high" and p.level == 20.0]
    assert highs_last and highs_last[0].occurrence_bar == 5   # explicit LAST


def test_D4_ft_same_bar_extreme_and_reversal_unresolved():
    """A bar that both extends the extreme and completes the reversal has an
    unknowable intrabar order — recorded explicitly, not synthesized."""
    n = 8
    lows = [10.0] * n
    highs = [12.0] * n
    highs[3] = 15.0
    lows[4] = 12.0
    highs[4] = 16.0        # update only (reversal 15-12=3 < tau 4)
    lows[5] = 5.0
    highs[5] = 17.0        # both a new high AND a >=tau reversal in one bar
    bars = _bars(lows, highs)
    rep = _rep("T", family="F-T", tau=4.0)
    amb = []
    ft_turning_points(bars, tau=4.0, rep=rep, ambiguities=amb)
    assert any(a["kind"] == "same-bar-extreme-vs-reversal" and a["bar"] == 5
               for a in amb)


# --------------------------------------------------------------------------
# D5 — genuine dependency recomputation
# --------------------------------------------------------------------------

def test_D5_propagate_never_accepts_caller_before_after_strings():
    """A dependent without a stored payload is not recomputable and no
    propagation is claimed for it; with a payload, differences are computed."""
    rep = _rep("C", k=2)
    pol = PolicyRegistry()
    pol.register("P-ORIGIN", "origin role", "origin-of-last-confirmed-leg")
    p1 = _pt("A", rep, "low", 10, 10.0, 12)
    p2 = _pt("B", rep, "high", 20, 40.0, 22)
    leg = LegCandidate("Lg1", rep, "A", "B", "up", 10, 20, 10.0, 40.0, 22)
    r = task_s1_structural_reference([p1, p2], [leg], 25, rep,
                                     "origin-of-last-confirmed-leg", pol,
                                     "P-ORIGIN")
    assert r.selected_id == "A"
    ledger = InterpretationLedger()
    uid = ledger.record(r)                      # NO payload: not recomputable
    log = ledger.propagate(25, ["A"], changed_states={"A": "broken"})
    assert log, "dependent must be visited"
    assert "not recomputable" in log[0].get("note", "")
    assert log[0]["computed_changes"] == []     # nothing claimed without proof
    # with a payload the same change recomputes for real
    ledger2 = InterpretationLedger()
    uid2 = ledger2.record(r, payload={
        "kind": "T-S1", "points": [p1, p2], "legs": [leg], "rep": rep,
        "role": "origin-of-last-confirmed-leg", "policy": pol,
        "policy_id": "P-ORIGIN"})
    log2 = ledger2.propagate(25, ["A"], changed_states={"A": "broken"})
    v2 = ledger2.versions[uid2][1]
    assert v2["computed_changes"]               # computed diff exists
    assert v2["result"].status == "unresolved"  # broken origin, no successor leg


# --------------------------------------------------------------------------
# D6 — direction, depth, candidate-level coverage
# --------------------------------------------------------------------------

def test_D6_direction_sensitive_falsifier_effect():
    rep = _rep("F", k=2)
    pts = [
        _pt("p0", rep, "low", 0, 20.0, 5),
        _pt("p1", rep, "high", 3, 35.0, 8),
        _pt("p2", rep, "low", 6, 25.0, 11),
    ]
    legs = [LegCandidate("up1", rep, "p0", "p1", "up", 0, 3, 20.0, 35.0, 8),
            LegCandidate("dn1", rep, "p1", "p2", "down", 3, 6, 35.0, 25.0, 11)]
    r_low_down = task_s5_falsifier(
        [{"interpretation": "I", "view": "F", "role": "low-of-current-leg",
          "direction": "down"}], pts, legs, 12)
    r_low_up = task_s5_falsifier(
        [{"interpretation": "I", "view": "F", "role": "low-of-current-leg",
          "direction": "up"}], pts, legs, 12)
    assert r_low_down.selected_id == "p2"   # low of the last down leg (p1->p2)
    assert r_low_up.selected_id == "p0"     # low of the last up leg (p0->p1)
    # inconsistent direction value -> explicit unresolved
    r_bad = task_s5_falsifier(
        [{"interpretation": "I", "view": "F", "role": "low-of-current-leg",
          "direction": "sideways"}], pts, legs, 12)
    assert r_bad.status == "unresolved"
    assert r_bad.unresolved is not None and r_bad.unresolved.reason_code == REASON_IC


def test_D6_candidate_ledger_covers_every_candidate():
    """Every claimed coverage statement is verifiable from serialized rows:
    one row per candidate with eligibility, exclusion reason, selection state."""
    rep = _rep("C", k=2)
    pts = [_pt("a", rep, "low", 4, 10.0, 6),
           _pt("b", rep, "high", 8, 40.0, 10),
           _pt("c", rep, "low", 12, 20.0, 14, status="provisional")]
    leg = LegCandidate("Lg1", rep, "a", "b", "up", 4, 8, 10.0, 40.0, 10)
    pol = PolicyRegistry()
    pol.register("P-ORIGIN", "origin role", "origin-of-last-confirmed-leg")
    r = task_s1_structural_reference(pts, [leg], 13, rep,
                                     "origin-of-last-confirmed-leg", pol,
                                     "P-ORIGIN")
    rows = [candidate_record(p, task_id="T-S1", run_id="t", boundary="B",
                             decision_bar=13,
                             eligible=(p.candidate_id in r.survivors),
                             exclusion=next((e for e in r.excluded
                                             if e.candidate_id == p.candidate_id), None),
                             selected=(p.candidate_id == r.selected_id),
                             unresolved_reason=(r.unresolved.reason_code
                                                if r.unresolved else None))
            for p in pts]
    assert {row["candidate_id"] for row in rows} == {"a", "b", "c"}
    by_id = {row["candidate_id"]: row for row in rows}
    assert by_id["a"]["selected"] is True
    assert by_id["a"]["exclusion_code"] is None
    assert by_id["b"]["exclusion_code"] == "X-POL"
    assert by_id["c"]["exclusion_code"] == X_STATE
    # availability + historical status fields present for auditing
    for row in rows:
        assert row["knowable_time"] is not None
        assert row["status_at_decision"] is not None
        assert row["representation_id"] == rep.rep_id


# --------------------------------------------------------------------------
# R — reproducible causal outputs
# --------------------------------------------------------------------------

def test_R_prefix_replay_determinism():
    n = 60
    lows = [30.0] * n
    highs = [30.0] * n
    for i, v in [(10, 10.0), (30, 20.0)]:
        lows[i] = v
    for i, v in [(20, 40.0), (45, 55.0)]:
        highs[i] = v
    bars = _bars(lows, highs)
    rep = _rep("C", k=5)
    full = fk_turning_points(bars, k=5, rep=rep)
    trunc = fk_turning_points(bars.iloc[:35], k=5, rep=rep)
    for p in trunc:
        q = next(x for x in full if x.candidate_id == p.candidate_id)
        assert p.status_at(34) == q.status_at(34)
        assert p.level == q.level
        assert p.knowable_bar == q.knowable_bar
