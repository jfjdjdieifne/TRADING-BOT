"""Behavioral tests — EXPERT-GROUNDED CONTEXTUAL SELECTION V1 (T-S1).

Covers the 12 required test categories (task §9), exercising the ACTUAL
existing interfaces (kernel ``task_s1_structural_reference`` gates, SP-01/13/14,
``SharedInformationAxis`` over the CLOSED information-time contract,
``add_transition`` lifecycle, ``InterpretationLedger`` revision retention):

  1  same scene, different analytical task
  2  multiple eligible structural references
  3  prominent but task-irrelevant candidate
  4  source-grounded conditional preference
  5  conflicting expert preferences (preserved, never auto-resolved)
  6  no applicable preference -> UNRESOLVED
  7  temporally unavailable candidate
  8  replay determinism (SWS-04d; future data cannot change a past decision)
  9  frozen historical selection
 10  revision after changed evidence (W8; append-only history + versions)
 11  sealed foundation integrity (information_time.py hash)
 12  runtime performance

Fixtures follow knowledge_foundation/19_SELECTION_CASES.md §19.2 (W-world:
ordinal levels, bar labels) — the same golden fixture used by the kernel
test suite.  No test uses future outcomes; no test invents market thresholds.
"""
from __future__ import annotations

import copy
import hashlib
import json
import time
from datetime import timedelta
from pathlib import Path

import pandas as pd
import pytest

from trading_system.research.contextual_selection import (
    OUTCOME_SELECTED,
    OUTCOME_UNRESOLVED,
    REASON_EP,
    REASON_IC,
    REASON_MP,
    STATUS_BROKEN,
    ContextualRelationships,
    ExpertPreference,
    ExpertSelection,
    InterpretationLedger,
    LegCandidate,
    PointCandidate,
    PolicyRegistry,
    Representation,
    SharedInformationAxis,
    apply_expert_preferences,
    expert_structural_reference_selection,
    fk_turning_points,
    build_legs,
)

# Shared information-time axis for the fixture: bar i -> T0 + i minutes
# (identical convention to test_contextual_selection_csm).
T0 = pd.Timestamp("2025-01-01 00:00:00")
AXIS = SharedInformationAxis(
    "expert-fixture-minute-grid",
    pd.date_range(T0, T0 + pd.Timedelta(minutes=2000), freq="1min"))

K = 5  # declared F-K window for view C (file 19 §19.2)


def _rep(view: str, scale: str, family: str = "F-K", **params) -> Representation:
    return Representation(family=family, view_id=view, scale_label=scale,
                          params=tuple(sorted(params.items())))


REP_C = _rep("C", "coarse", k=K)


def _pt(pid, rep, side, occ, level, know, status="confirmed", **kw):
    return PointCandidate(
        candidate_id=pid, rep=rep, side=side,
        occurrence_bar=occ, level=level, knowable_bar=know,
        status=status,
        occurrence_time=T0 + timedelta(minutes=occ),
        knowable_time=T0 + timedelta(minutes=know), **kw)


def _leg(leg_id, rep, start_id, end_id, direction, t0, t1, p0, p1, know):
    return LegCandidate(
        leg_id, rep, start_id, end_id, direction, t0, t1, p0, p1, know,
        t0_time=T0 + timedelta(minutes=t0),
        t1_time=T0 + timedelta(minutes=t1),
        knowable_time=T0 + timedelta(minutes=know))


def make_world() -> dict:
    """Fresh W-world (file 19 §19.2) per test — never shared/mutated."""
    coarse = [
        _pt("L_a", REP_C, "low", 10, 10.0, 15),
        _pt("H_a", REP_C, "high", 20, 40.0, 25),
        _pt("L_b", REP_C, "low", 30, 20.0, 35),
        _pt("H_b", REP_C, "high", 40, 50.0, 45),
    ]
    fine = [
        _pt("fA.0", _rep("F", "fine", k=2), "low", 30, 20.0, 30),
        _pt("fA.1", _rep("F", "fine", k=2), "high", 33, 35.0, 34),
    ]
    clegs = [
        _leg("Leg1", REP_C, "L_a", "H_a", "up", 10, 20, 10.0, 40.0, 25),
        _leg("Leg2", REP_C, "H_a", "L_b", "down", 20, 30, 40.0, 20.0, 35),
        _leg("Leg3", REP_C, "L_b", "H_b", "up", 30, 40, 20.0, 50.0, 45),
    ]
    pol = PolicyRegistry()
    pol.register("P-ORIGIN",
                 "role: origin of the most recent confirmed leg (SWS-02)",
                 "origin-of-last-confirmed-leg")
    return {"points": coarse + fine, "coarse": coarse, "fine": fine,
            "clegs": clegs, "pol": pol}


def _sel(world, *, role=None, policy_id=None, rel=None, bar=52, **kw):
    return expert_structural_reference_selection(
        points=world["points"], legs=world["clegs"], decision_bar=bar,
        rep=REP_C, policy=world["pol"], role=role, policy_id=policy_id,
        decision_time=T0 + timedelta(minutes=bar), axis=AXIS,
        relationships=rel, **kw)


# --------------------------------------------------------------------------
# 1 — same scene, different analytical task
# --------------------------------------------------------------------------
def test_01_same_scene_different_task():
    w = make_world()
    s_origin = _sel(w, role="origin-of-last-confirmed-leg",
                    policy_id="P-ORIGIN")
    s_extreme = _sel(w, role="last-confirmed-extreme")
    s_none = _sel(w, role=None)
    # different declared tasks -> different answers on the SAME scene
    assert s_origin.outcome == OUTCOME_SELECTED and s_origin.candidate_id == "L_b"
    assert s_extreme.outcome == OUTCOME_SELECTED and s_extreme.candidate_id == "H_b"
    assert s_origin.candidate_id != s_extreme.candidate_id
    # with no declared task role the honest answer is not a pick
    assert s_none.outcome == OUTCOME_UNRESOLVED and s_none.candidate_id is None
    # interpretation continuation is task-tagged, one per selection
    assert s_origin.interpretation["reference"] == "L_b"
    assert s_extreme.interpretation["reference"] == "H_b"
    assert s_origin.interpretation["conditional_on"]


# --------------------------------------------------------------------------
# 2 — multiple eligible structural references (nothing silently dropped)
# --------------------------------------------------------------------------
def test_02_multiple_eligible_references():
    w = make_world()
    s = _sel(w, role=None)
    assert sorted(s.surviving_candidate_ids) == ["H_a", "H_b", "L_a", "L_b"]
    # every non-survivor carries an exclusion record (X-SCALE for fine views)
    codes = {x.candidate_id: x.code for x in s.excluded}
    assert set(codes) == {"fA.0", "fA.1"}
    assert all(c == "X-SCALE" for c in codes.values())
    assert len(s.surviving_candidate_ids) + len(s.excluded) == len(w["points"])


# --------------------------------------------------------------------------
# 3 — prominent but task-irrelevant candidate
# --------------------------------------------------------------------------
def test_03_prominent_but_task_irrelevant():
    w = make_world()
    # H_b (level 50 — the most prominent extreme) is NOT the origin answer
    s = _sel(w, role="origin-of-last-confirmed-leg", policy_id="P-ORIGIN")
    assert s.candidate_id == "L_b" and "H_b" != s.candidate_id
    # and without a declared role and without evidence, prominence never
    # selects anything (no largest/nearest/newest default anywhere)
    s2 = _sel(w, role=None)
    assert s2.outcome == OUTCOME_UNRESOLVED and s2.candidate_id is None
    assert "H_b" in s2.surviving_candidate_ids  # kept, not chosen


# --------------------------------------------------------------------------
# 4 — source-grounded conditional preference (KP-02 tested > untested)
# --------------------------------------------------------------------------
def test_04_source_grounded_conditional_preference():
    w = make_world()
    rel = ContextualRelationships(test_history={
        "L_b": [{"bar": 33, "kind": "close-cross-binding", "ref": "R:SP-03"}],
        "L_a": [], "H_a": [], "H_b": [],      # observed: no tests
    })
    s = _sel(w, role="origin-of-last-confirmed-leg", policy_id=None, rel=rel)
    assert s.outcome == OUTCOME_SELECTED and s.candidate_id == "L_b"
    kp02 = [a for a in s.activated_preferences if a["pref_id"] == "KP-02"]
    assert kp02 and kp02[0]["pairs"]
    # evidence chain carries the preference with its EXACT source (task §4)
    pref_items = [e for e in s.evidence if e.name == "preference:KP-02"]
    assert pref_items and pref_items[0].klass == "S"
    assert "Grimes" in pref_items[0].value or "Grimes" in pref_items[0].detail \
        or "tested>untested" == pref_items[0].value
    assert any("Grimes" in a["source"] for a in kp02)
    assert any("Osler" in a["source"] for a in kp02)
    assert any("Livermore" in a["source"] for a in kp02)
    # provenance names the preference resolution
    assert any(p.startswith("R:preference-resolution") for p in s.provenance)


# --------------------------------------------------------------------------
# 5 — conflicting expert preferences preserved (task §7)
# --------------------------------------------------------------------------
def test_05_conflicting_preferences_preserved():
    w = make_world()
    rel = ContextualRelationships(
        test_history={
            "L_b": [{"bar": 33, "kind": "close-cross-binding"}],
            "H_b": [], "L_a": [],              # observed: no tests
        },
        round_cluster={"L_b": False, "H_b": True})  # Osler marker on H_b
    s = _sel(w, role="origin-of-last-confirmed-leg", policy_id=None, rel=rel)
    # KP-02 prefers L_b (tested) over H_b; KP-06 prefers H_b (cluster) over
    # L_b -> the pair is contested by two source-grounded preferences
    assert s.outcome == OUTCOME_UNRESOLVED and s.candidate_id is None
    assert s.reason["code"] == REASON_EP
    kinds = {c["kind"] for c in s.conflicts}
    assert "preference-vs-preference" in kinds
    contested = [c for c in s.conflicts
                 if c["kind"] == "preference-vs-preference"]
    assert any(set(c["pref_ids"]) == {"KP-02", "KP-06"} for c in contested)
    # no winner is hidden through candidate-id ordering: nothing selected
    assert s.candidate_id is None
    assert set(s.surviving_candidate_ids) == {"L_a", "H_a", "L_b", "H_b"}


# --------------------------------------------------------------------------
# 6 — no applicable preference -> UNRESOLVED (never a default pick)
# --------------------------------------------------------------------------
def test_06_no_applicable_preference_unresolved():
    w = make_world()
    s = _sel(w, role=None, rel=ContextualRelationships())
    assert s.outcome == OUTCOME_UNRESOLVED
    assert s.reason["code"] == REASON_MP
    assert "Pi_T" in s.reason["evidence_needed"]
    inactive_ids = {i["pref_id"] for i in s.inactive_preferences}
    assert {"KP-02", "KP-03", "KP-05", "KP-06"} <= inactive_ids
    # KP-05 (F-class) is a documented refusal, never a rule
    kp05 = [i for i in s.inactive_preferences if i["pref_id"] == "KP-05"][0]
    assert "never binding" in kp05["cause"]


# --------------------------------------------------------------------------
# 7 — temporally unavailable candidate
# --------------------------------------------------------------------------
def test_07_temporally_unavailable_candidate():
    w = make_world()
    late = _pt("H_late", REP_C, "high", 60, 99.0, 70)   # knowable AFTER 52
    w["points"].append(late)
    s = _sel(w, role=None)
    assert "H_late" not in s.surviving_candidate_ids
    excl = {x.candidate_id: x.code for x in s.excluded}
    assert excl.get("H_late") == "X-KNOW"

    # contract (audit F): a PRESENT but off-grid candidate time yields
    # EXPLICIT UNAVAILABILITY — never used in a comparison, never supports a
    # positive claim (excluded), and never silently compared
    bad = _pt("H_bad", REP_C, "high", 21, 41.0, 26)
    bad.knowable_time = T0 + timedelta(minutes=26, seconds=30)  # off-grid
    w2 = make_world()
    w2["points"].append(bad)
    s2 = _sel(w2, role=None)
    assert "H_bad" not in s2.surviving_candidate_ids
    excl2 = {x.candidate_id: x.code for x in s2.excluded}
    assert excl2.get("H_bad") == "X-KNOW"

    # fail-closed write path: an off-grid STATUS-TRANSITION time is INVALID
    # INPUT and is rejected (never applied)
    p = w["coarse"][0]
    with pytest.raises(ValueError):
        p.add_transition(53, STATUS_BROKEN,
                         info_time=T0 + timedelta(minutes=53, seconds=30),
                         axis=AXIS)


# --------------------------------------------------------------------------
# 8 — replay determinism (SWS-04d) + future-data isolation
# --------------------------------------------------------------------------
def test_08_replay_determinism():
    w1, w2 = make_world(), make_world()
    r1 = _sel(w1, role=None).to_record()
    r2 = _sel(w2, role=None).to_record()
    assert json.dumps(r1, sort_keys=True) == json.dumps(r2, sort_keys=True)

    # future-EVENT isolation (the real leak vector): the SAME candidate
    # inventory, decided at bar 52, with and without a post-53 status
    # transition on L_b — the frozen past decision must be identical
    w4 = make_world()
    w4["points"].append(_pt("L_c", REP_C, "low", 48, 28.0, 56))
    r4 = _sel(w4, role=None, bar=52).to_record()
    w5 = copy.deepcopy(w4)
    w5["coarse"][2].add_transition(53, STATUS_BROKEN,
                                   info_time=T0 + timedelta(minutes=53),
                                   by="E:break", note="close below 20",
                                   event_ref="E:break@53", axis=AXIS)
    r5 = _sel(w5, role=None, bar=52).to_record()
    assert json.dumps(r5, sort_keys=True) == json.dumps(r4, sort_keys=True)
    # the extra late candidate never leaks into the past selection either
    assert r5["outcome"] == r1["outcome"]
    # and the SAME changed evidence DOES change the decision at bar 56
    # (revision channel is live: the broken origin is surfaced, not hidden)
    s56 = _sel(w5, role="origin-of-last-confirmed-leg", policy_id="P-ORIGIN",
               bar=56)
    assert s56.outcome == OUTCOME_UNRESOLVED
    assert s56.reason["code"] == REASON_IC


# --------------------------------------------------------------------------
# 9 — frozen historical selection
# --------------------------------------------------------------------------
def test_09_frozen_historical_selection():
    w = make_world()
    s = _sel(w, role="origin-of-last-confirmed-leg", policy_id="P-ORIGIN")
    rec = s.to_record()
    frozen = json.dumps(rec, sort_keys=True)
    assert json.loads(frozen) == rec
    # policy snapshots are carried on the frozen record (consolidation V1)
    assert s.base_result.policy_snapshots.get("role", {}).get("value") == \
        "origin-of-last-confirmed-leg"
    assert "P-ORIGIN" in s.policy_snapshots
    # historical status is append-only: later events never rewrite the past
    lb = w["coarse"][2]
    lb.add_transition(53, STATUS_BROKEN, info_time=T0 + timedelta(minutes=53),
                      event_ref="E:break@53", axis=AXIS)
    assert lb.status_at(52) == "confirmed"       # frozen past
    assert lb.status_at(56) == STATUS_BROKEN     # later state


# --------------------------------------------------------------------------
# 10 — revision after changed evidence (W8) with existing mechanisms
# --------------------------------------------------------------------------
def test_10_revision_after_changed_evidence():
    w = make_world()
    ledger = InterpretationLedger()
    s1 = _sel(w, role="origin-of-last-confirmed-leg", policy_id="P-ORIGIN",
              bar=52)
    uid1 = ledger.record(s1.base_result,
                         s1.ledger_payload(run_id="t10",
                                           points=w["points"],
                                           legs=w["clegs"]))
    assert s1.candidate_id == "L_b"

    # changed evidence: break at 53 (append-only) + a new confirmed leg
    w["coarse"][2].add_transition(53, STATUS_BROKEN,
                                  info_time=T0 + timedelta(minutes=53),
                                  by="E:break@53", note="close below level",
                                  event_ref="E:break@53", axis=AXIS)
    lc = _pt("L_c", REP_C, "low", 48, 28.0, 56)
    w["points"].append(lc)
    w["clegs"].append(_leg("Leg4", REP_C, "H_b", "L_c", "down", 40, 48,
                           50.0, 28.0, 56))
    s2 = _sel(w, role="origin-of-last-confirmed-leg", policy_id="P-ORIGIN",
              bar=56)
    uid2 = ledger.record(s2.base_result,
                         s2.ledger_payload(run_id="t10",
                                           points=w["points"],
                                           legs=w["clegs"]))

    # revision: the reference moved L_b -> H_b (origin of the new leg)
    assert s2.candidate_id == "H_b"
    assert s2.base_result.direction == "down"
    # revision dependencies preserved through existing project mechanisms
    assert "H_b" in s2.base_result.dependencies
    assert "Leg4" in s2.base_result.dependencies
    # the old selection is RETAINED as a version (never edited in place)
    assert uid1 != uid2
    assert ledger.versions[uid1][0]["result"].selected_id == "L_b"
    assert ledger.versions[uid2][0]["result"].selected_id == "H_b"
    # the interpretation carries revision dependencies (task §6.9-6.10)
    assert s2.interpretation["revision_dependencies"] == \
        s2.base_result.dependencies


# --------------------------------------------------------------------------
# 11 — sealed foundation integrity
# --------------------------------------------------------------------------
def test_11_sealed_foundation_integrity():
    info_time = Path(__file__).resolve().parents[1] / "src" / "trading_system" \
        / "research" / "information_time.py"
    digest = hashlib.sha256(info_time.read_bytes()).hexdigest()
    assert digest == ("72b03ca6d2333080e0df6dc18b1928147e877b41175f132c7bf08"
                      "eb4e4d74ace"), \
        "sealed information_time.py changed — STOP (task §2)"


# --------------------------------------------------------------------------
# 12 — runtime performance
# --------------------------------------------------------------------------
def _bars_wave(n: int) -> pd.DataFrame:
    import math
    lows, highs = [], []
    for i in range(n):
        base = 100.0 + 0.01 * i
        swing = 10.0 * math.sin(i / 25.0)
        lows.append(base + swing - 1.0)
        highs.append(base + swing + 1.0)
    return pd.DataFrame({
        "open": [(lows[i] + highs[i]) / 2 for i in range(n)],
        "high": highs, "low": lows,
        "close": [(lows[i] + highs[i]) / 2 for i in range(n)],
        "volume": [1.0] * n,
    })


def test_12_runtime_performance():
    bars = _bars_wave(2000)
    pts = fk_turning_points(bars, k=5, rep=REP_C, id_prefix="P|")
    legs = build_legs(pts, REP_C)
    assert len(pts) >= 100, "fixture must exercise a real candidate set"
    pol = PolicyRegistry()
    pol.register("P-ORIGIN", "role", "origin-of-last-confirmed-leg")
    t0 = time.perf_counter()
    for bar in (400, 800, 1200, 1600):
        s = expert_structural_reference_selection(
            points=pts, legs=legs, decision_bar=bar, rep=REP_C, policy=pol,
            role=None,  # worst case: full preference evaluation over survivors
            relationships=ContextualRelationships())
        assert s.outcome in (OUTCOME_SELECTED, OUTCOME_UNRESOLVED)
    elapsed = time.perf_counter() - t0
    assert elapsed < 5.0, f"4 selections over {len(pts)} candidates took {elapsed:.2f}s"


# --------------------------------------------------------------------------
# Bonus contract checks (task §4/§7 discipline)
# --------------------------------------------------------------------------
def test_f_class_never_binds():
    with pytest.raises(ValueError):
        ExpertPreference(
            pref_id="BAD", task_id="T-S1", kclass="F", klass="U",
            source="x", source_family="x", statement="x", context="x",
            observable_evidence=(), licenses="none", exceptions="",
            conflict_status="", provenance_refs=(), binding=True)


def test_preference_resolution_is_pure_and_replayable():
    ids = ["a", "b", "c"]
    maps = {"a": {"test_history": [{"bar": 1}]},
            "b": {"test_history": []},
            "c": {"test_history": []}}
    r1 = apply_expert_preferences(ids, maps)
    r2 = apply_expert_preferences(ids, maps)
    assert json.dumps(r1, sort_keys=True, default=str) == \
        json.dumps(r2, sort_keys=True, default=str)
    act, inact, conf, winner, diag = r1
    assert winner == "a" and not conf
    assert diag["preferred"] == ["a"]
