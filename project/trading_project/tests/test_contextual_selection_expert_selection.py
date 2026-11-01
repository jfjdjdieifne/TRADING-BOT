"""Behavioral + adversarial tests — EXPERT-GROUNDED SELECTION V1.1 (T-S1).

Covers the 12 required categories (task §9) PLUS the audit-remediation
acceptance list (findings F1-F5):

  1  same scene, different analytical task
  2  multiple eligible structural references (no silent omission)
  3  prominent but task-irrelevant candidate
  4  source-grounded conditional preference (KP-03; KP-02 is nonbinding)
  5  conflicting expert preferences preserved (never auto-resolved)
  6  no applicable preference -> UNRESOLVED
  7  temporally unavailable candidates AND relationship evidence
  8  replay determinism + input-permutation invariance
  9  frozen historical selection
 10  revision after changed evidence / REAL ledger propagation
 11  sealed foundation integrity
 12  runtime performance

Adversarial (audit acceptance): future/off-grid/unmappable relationship
evidence, missing/mismatched roles, incomplete comparisons, KP-02 event
types (wick touch vs close-through; nonbinding proof), equal-knowable ties
in kernel + expert layer + permutations, real InterpretationLedger
recomputation through a dependent conclusion, stale/empty recompute never
counted as success.

All tests exercise the actual interfaces (kernel T-S1 gates, SP-01/13/14,
SharedInformationAxis over the sealed 6.2A-0 contract, add_transition,
InterpretationLedger).  No future outcomes; no invented market thresholds.
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
    EVENT_CLOSE_THROUGH,
    EVENT_WICK_TOUCH,
    KNOWLEDGE_BY_ID,
    OUTCOME_SELECTED,
    OUTCOME_UNRESOLVED,
    REASON_EP,
    REASON_IC,
    REASON_MP,
    STATUS_BROKEN,
    ContextualRelationships,
    ExpertPreference,
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
    task_s1_structural_reference,
)

T0 = pd.Timestamp("2025-01-01 00:00:00")
AXIS = SharedInformationAxis(
    "expert-fixture-minute-grid",
    pd.date_range(T0, T0 + pd.Timedelta(minutes=2000), freq="1min"))

K = 5


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
    """Fresh W-world (knowledge_foundation/19 §19.2) per test."""
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
    assert s_origin.outcome == OUTCOME_SELECTED
    assert s_origin.candidate_id == "L_b"
    assert s_extreme.outcome == OUTCOME_SELECTED
    assert s_extreme.candidate_id == "H_b"
    assert s_origin.candidate_id != s_extreme.candidate_id
    # missing role = invalid task instance: explicit UNRESOLVED (finding F2)
    assert s_none.outcome == OUTCOME_UNRESOLVED and s_none.candidate_id is None
    assert s_none.reason["code"] == REASON_MP
    assert "no valid declared role" in s_none.reason["text"]
    assert s_origin.interpretation["reference"] == "L_b"
    assert s_extreme.interpretation["reference"] == "H_b"


# --------------------------------------------------------------------------
# 2 — multiple eligible references; nothing silently omitted (F2)
# --------------------------------------------------------------------------
def test_02_multiple_eligible_references_no_silent_omission():
    w = make_world()
    # a broken candidate that the kernel filters WITHOUT a record: the layer
    # must surface it (audit: do not silently omit candidates)
    broken = _pt("H_br", REP_C, "high", 25, 45.0, 30)
    broken.add_transition(40, STATUS_BROKEN,
                          info_time=T0 + timedelta(minutes=40),
                          event_ref="E:br", axis=AXIS)
    w["points"].append(broken)
    s = _sel(w, role="last-confirmed-extreme")
    # justified extreme role: the kernel keeps the winner as the survivor and
    # records X-POL for the rest — the BROKEN candidate is the silent gap and
    # must be surfaced by the layer (finding F2)
    assert s.surviving_candidate_ids == ["H_b"]
    codes = {x.candidate_id: x.code for x in s.excluded}
    assert codes.get("H_br") == "X-STATE"          # surfaced, not omitted
    assert codes.get("fA.0") == "X-SCALE"
    assert codes.get("L_a") == "X-POL"
    assert len(s.surviving_candidate_ids) + len(s.excluded) == len(w["points"])


# --------------------------------------------------------------------------
# 3 — prominent but task-irrelevant candidate
# --------------------------------------------------------------------------
def test_03_prominent_but_task_irrelevant():
    w = make_world()
    s = _sel(w, role="origin-of-last-confirmed-leg", policy_id="P-ORIGIN")
    assert s.candidate_id == "L_b" and s.candidate_id != "H_b"
    # without a valid role nothing is selected — prominence never decides
    s2 = _sel(w, role=None)
    assert s2.outcome == OUTCOME_UNRESOLVED and s2.candidate_id is None
    assert "H_b" in s2.surviving_candidate_ids


# --------------------------------------------------------------------------
# 4 — source-grounded conditional preference MECHANISM + KP-03 disposition
# --------------------------------------------------------------------------
def _injected_htf_record(pref_id="T-HTF", task_id="T-S1"):
    """A test-local documented comparison record over the real license rule."""
    return ExpertPreference(
        pref_id=pref_id, task_id=task_id, kclass="E", klass="S",
        source="test-source (documented comparison)", source_family="t",
        statement="indicated reference kinds are preferred (test record)",
        context="test", observable_evidence=("ref_kind",),
        licenses="old-low-htf>other", exceptions="",
        conflict_status="", provenance_refs=())


def test_04_source_grounded_conditional_preference_mechanism():
    w = make_world()
    rel = ContextualRelationships(ref_kind={
        "L_b": {"value": "old-low-htf", "known_bar": 35,
                "known_time": T0 + timedelta(minutes=35)},
        "L_a": {"value": "local", "known_bar": 15,
                "known_time": T0 + timedelta(minutes=15)},
        "H_a": {"value": "local", "known_bar": 25,
                "known_time": T0 + timedelta(minutes=25)},
        "H_b": {"value": "local", "known_bar": 45,
                "known_time": T0 + timedelta(minutes=45)},
    })
    s = _sel(w, role="origin-of-last-confirmed-leg", policy_id=None, rel=rel,
             knowledge=(_injected_htf_record(),))
    assert s.outcome == OUTCOME_SELECTED and s.candidate_id == "L_b"
    act = [a for a in s.activated_preferences if a["pref_id"] == "T-HTF"]
    assert act and act[0]["pairs"]
    pref_items = [e for e in s.evidence if e.name == "preference:T-HTF"]
    assert pref_items and pref_items[0].klass == "S"
    assert any(p.startswith("R:preference-resolution")
               for p in s.provenance)


def test_04b_finding3_kp03_nonbinding_unsupported_contexts():
    """Finding 3: the pinned source does not establish the old-low/HTF
    comparison for T-S1 role selection — KP-03 is nonbinding research-only
    and NO unsupported context can produce a selection through it alone."""
    w = make_world()
    rel = ContextualRelationships(ref_kind={
        "L_b": {"value": "old-low-htf", "known_bar": 35},
        "L_a": {"value": "old-high-reclaimed", "known_bar": 15},
        "H_a": {"value": "local", "known_bar": 25},
        "H_b": {"value": "local", "known_bar": 45},
    })
    # origin role without policy: nothing can resolve — KP-03 cannot select
    s1 = _sel(w, role="origin-of-last-confirmed-leg", policy_id=None, rel=rel)
    assert s1.outcome == OUTCOME_UNRESOLVED and s1.candidate_id is None
    assert not s1.activated_preferences
    # extreme role resolves only by its OPERATIONAL role definition
    # (SWS-02, 'not an ICT-source claim') — never THROUGH KP-03
    s2 = _sel(w, role="last-confirmed-extreme", policy_id=None, rel=rel)
    assert not s2.activated_preferences
    assert all(not e.name.startswith("preference:") for e in s2.evidence)
    for s in (s1, s2):
        kp03 = [i for i in s.inactive_preferences if i["pref_id"] == "KP-03"]
        assert kp03 and ("nonbinding" in kp03[0]["cause"]
                         or "never licenses" in kp03[0]["cause"])
    # the record documents the exact source boundary; it never licenses
    kp03_rec = KNOWLEDGE_BY_ID["KP-03"]
    assert kp03_rec.kclass == "F" and kp03_rec.licenses == "none"
    assert "not an ICT-source claim" in kp03_rec.statement
    assert "knowledge_foundation/16 §16.3" in kp03_rec.statement


# --------------------------------------------------------------------------
# 5 — conflicting preferences preserved (task §7; F2/F3 compatible)
# --------------------------------------------------------------------------
def test_05a_policy_vs_preference_tension_preserved():
    w = make_world()
    # the injected documented comparison prefers L_a (old-low-htf) but the
    # Pi_T role policy selects L_b
    rel = ContextualRelationships(ref_kind={
        "L_a": {"value": "old-low-htf", "known_bar": 15,
                "known_time": T0 + timedelta(minutes=15)},
        "L_b": {"value": "local", "known_bar": 35,
                "known_time": T0 + timedelta(minutes=35)},
        "H_a": {"value": "local", "known_bar": 25,
                "known_time": T0 + timedelta(minutes=25)},
        "H_b": {"value": "local", "known_bar": 45,
                "known_time": T0 + timedelta(minutes=45)},
    })
    s = _sel(w, role="origin-of-last-confirmed-leg", policy_id="P-ORIGIN",
             rel=rel, knowledge=(_injected_htf_record(),))
    # documented precedence: Pi_T resolves; the tension is PRESERVED
    assert s.outcome == OUTCOME_SELECTED and s.candidate_id == "L_b"
    kinds = {c["kind"] for c in s.conflicts}
    assert "policy-vs-preference" in kinds
    tension = [c for c in s.conflicts if c["kind"] == "policy-vs-preference"]
    assert any(c["pref_ids"] == ["T-HTF"] for c in tension)
    assert any("SP-12" in c["resolution"] for c in tension)


def test_05b_preference_vs_preference_conflict_preserved():
    ids = ["a", "b"]
    maps = {"a": {"ref_kind": "old-low-htf", "rank": 1},
            "b": {"ref_kind": "local", "rank": 2}}

    def rule_htf(l, r):
        ind = {"old-low-htf", "old-high-reclaimed"}
        li, ri = l.get("ref_kind") in ind, r.get("ref_kind") in ind
        return None if li == ri else li

    def rule_rank(l, r):
        if "rank" not in l or "rank" not in r:
            return None
        return None if l["rank"] == r["rank"] else l["rank"] > r["rank"]

    kb = (
        ExpertPreference(pref_id="T-1", task_id="T-S1", kclass="E",
                         klass="S", source="test-source-1",
                         source_family="t", statement="s", context="c",
                         observable_evidence=("ref_kind",),
                         licenses="lic-htf", exceptions="", conflict_status="",
                         provenance_refs=()),
        ExpertPreference(pref_id="T-2", task_id="T-S1", kclass="E",
                         klass="S", source="test-source-2",
                         source_family="t", statement="s", context="c",
                         observable_evidence=("rank",),
                         licenses="lic-rank", exceptions="",
                         conflict_status="", provenance_refs=()),
    )
    act, inact, conf, winner, diag = apply_expert_preferences(
        ids, maps, kb,
        license_rules={"lic-htf": rule_htf, "lic-rank": rule_rank})
    # T-1 prefers a; T-2 prefers b -> conflict preserved, NO winner
    assert winner is None
    assert conf and any(set(c["pref_ids"]) == {"T-1", "T-2"} for c in conf)
    assert diag["preferred"] == []


# --------------------------------------------------------------------------
# 6 — no applicable preference -> UNRESOLVED (never a default)
# --------------------------------------------------------------------------
def test_06_no_applicable_preference_unresolved():
    w = make_world()
    s = _sel(w, role="origin-of-last-confirmed-leg", policy_id=None,
             rel=ContextualRelationships())
    assert s.outcome == OUTCOME_UNRESOLVED
    assert s.reason["code"] == REASON_MP
    assert "Pi_T" in s.reason["evidence_needed"]
    inactive_ids = {i["pref_id"] for i in s.inactive_preferences}
    assert {"KP-02", "KP-03", "KP-05", "KP-06"} <= inactive_ids
    kp02 = [i for i in s.inactive_preferences if i["pref_id"] == "KP-02"][0]
    assert "never licenses" in kp02["cause"] or "nonbinding" in kp02["cause"]
    kp05 = [i for i in s.inactive_preferences if i["pref_id"] == "KP-05"][0]
    assert "never licenses" in kp05["cause"] or "nonbinding" in kp05["cause"]


# --------------------------------------------------------------------------
# 7 — temporally unavailable candidates AND relationship evidence (F1)
# --------------------------------------------------------------------------
def test_07_temporally_unavailable_candidate():
    w = make_world()
    w["points"].append(_pt("H_late", REP_C, "high", 60, 99.0, 70))
    s = _sel(w, role="last-confirmed-extreme")
    assert "H_late" not in s.surviving_candidate_ids
    excl = {x.candidate_id: x.code for x in s.excluded}
    assert excl.get("H_late") == "X-KNOW"

    bad = _pt("H_bad", REP_C, "high", 21, 41.0, 26)
    bad.knowable_time = T0 + timedelta(minutes=26, seconds=30)  # off-grid
    w2 = make_world()
    w2["points"].append(bad)
    s2 = _sel(w2, role="last-confirmed-extreme")
    assert "H_bad" not in s2.surviving_candidate_ids
    excl2 = {x.candidate_id: x.code for x in s2.excluded}
    assert excl2.get("H_bad") == "X-KNOW"

    p = w["coarse"][0]
    with pytest.raises(ValueError):
        p.add_transition(53, STATUS_BROKEN,
                         info_time=T0 + timedelta(minutes=53, seconds=30),
                         axis=AXIS)


def test_07b_adv_future_relationship_evidence_unavailable():
    w = make_world()
    rel_future = ContextualRelationships(test_history={
        "L_a": [{"bar": 60, "kind": EVENT_WICK_TOUCH}],   # FUTURE (> 52)
        "L_b": [{"bar": 40, "kind": EVENT_CLOSE_THROUGH}],
    })
    rel_none = ContextualRelationships()
    s_f = _sel(w, role="origin-of-last-confirmed-leg", policy_id=None,
               rel=rel_future)
    s_n = _sel(w, role="origin-of-last-confirmed-leg", policy_id=None,
               rel=rel_none)
    # the future event must be unavailable and must NOT influence selection
    assert s_f.to_record()["outcome"] == s_n.to_record()["outcome"]
    assert s_f.candidate_id == s_n.candidate_id
    assert any("future" in d["reason"] for d in s_f.dropped_evidence)


def test_07c_adv_offgrid_and_unmappable_relationship_evidence():
    w = make_world()
    rel = ContextualRelationships(
        test_history={
            "L_a": [{"bar": 30, "time": T0 + timedelta(minutes=30, seconds=30),
                     "kind": EVENT_WICK_TOUCH}],            # off-grid time
            "L_b": [{"kind": EVENT_WICK_TOUCH}],            # no stamp
            "H_a": [{"bar": 30, "kind": "some-other-kind"}],  # unknown kind
        },
        ref_kind={"H_b": "old-low-htf"},      # plain value: no stamp
    )
    s = _sel(w, role="origin-of-last-confirmed-leg", policy_id=None, rel=rel)
    reasons = " | ".join(d["reason"] for d in s.dropped_evidence)
    assert "off-grid" in reasons
    assert "unmappable" in reasons
    # every dropped fact is unavailable: no preference activated, no pick
    assert s.outcome == OUTCOME_UNRESOLVED
    assert not s.activated_preferences
    # and the plain ref_kind value never reaches evidence
    assert not any(e.name == "ref_kind" for e in s.evidence)


def test_07d_adv_future_declaration_unavailable():
    w = make_world()
    rel = ContextualRelationships(ref_kind={
        "L_a": {"value": "old-low-htf", "known_bar": 60},   # future (> 52)
        "L_b": {"value": "local", "known_bar": 35},
    })
    s = _sel(w, role="origin-of-last-confirmed-leg", policy_id=None, rel=rel)
    # KP-03 cannot compare: only one side has a valid declaration
    assert s.outcome == OUTCOME_UNRESOLVED
    assert not s.activated_preferences
    assert any("future" in d["reason"] for d in s.dropped_evidence)


# --------------------------------------------------------------------------
# 8 — replay determinism + input-permutation invariance (F4)
# --------------------------------------------------------------------------
def test_08_replay_determinism():
    w1, w2 = make_world(), make_world()
    r1 = _sel(w1, role="last-confirmed-extreme").to_record()
    r2 = _sel(w2, role="last-confirmed-extreme").to_record()
    assert json.dumps(r1, sort_keys=True) == json.dumps(r2, sort_keys=True)

    w4 = make_world()
    w4["points"].append(_pt("L_c", REP_C, "low", 48, 28.0, 56))
    r4 = _sel(w4, role="origin-of-last-confirmed-leg", policy_id="P-ORIGIN",
              bar=52).to_record()
    w5 = copy.deepcopy(w4)
    w5["coarse"][2].add_transition(53, STATUS_BROKEN,
                                   info_time=T0 + timedelta(minutes=53),
                                   by="E:break", note="close below 20",
                                   event_ref="E:break@53", axis=AXIS)
    r5 = _sel(w5, role="origin-of-last-confirmed-leg", policy_id="P-ORIGIN",
              bar=52).to_record()
    assert json.dumps(r5, sort_keys=True) == json.dumps(r4, sort_keys=True)


def test_08b_input_permutation_invariance():
    w = make_world()
    s_fwd = _sel(w, role="last-confirmed-extreme")
    w_rev = make_world()
    w_rev["points"] = list(reversed(w_rev["points"]))
    w_rev["clegs"] = list(reversed(w_rev["clegs"]))
    s_rev = _sel(w_rev, role="last-confirmed-extreme")
    assert s_fwd.outcome == s_rev.outcome
    assert s_fwd.candidate_id == s_rev.candidate_id
    assert sorted(s_fwd.surviving_candidate_ids) == \
        sorted(s_rev.surviving_candidate_ids)
    assert {x.candidate_id: x.code for x in s_fwd.excluded} == \
        {x.candidate_id: x.code for x in s_rev.excluded}
    # preference path is likewise permutation-invariant
    s_fwd2 = _sel(w, role="origin-of-last-confirmed-leg", policy_id=None)
    s_rev2 = _sel(w_rev, role="origin-of-last-confirmed-leg", policy_id=None)
    assert s_fwd2.outcome == s_rev2.outcome
    assert s_fwd2.reason["code"] == s_rev2.reason["code"]
    assert sorted(s_fwd2.surviving_candidate_ids) == \
        sorted(s_rev2.surviving_candidate_ids)


# --------------------------------------------------------------------------
# 9 — frozen historical selection
# --------------------------------------------------------------------------
def test_09_frozen_historical_selection():
    w = make_world()
    s = _sel(w, role="origin-of-last-confirmed-leg", policy_id="P-ORIGIN")
    rec = s.to_record()
    frozen = json.dumps(rec, sort_keys=True)
    assert json.loads(frozen) == rec
    assert s.base_result.policy_snapshots.get("role", {}).get("value") == \
        "origin-of-last-confirmed-leg"
    lb = w["coarse"][2]
    lb.add_transition(53, STATUS_BROKEN, info_time=T0 + timedelta(minutes=53),
                      event_ref="E:break@53", axis=AXIS)
    assert lb.status_at(52) == "confirmed"       # frozen past
    assert lb.status_at(56) == STATUS_BROKEN


# --------------------------------------------------------------------------
# 10 — REAL InterpretationLedger recomputation (finding F5)
# --------------------------------------------------------------------------
def test_10_real_ledger_propagation_through_dependent_conclusion():
    w = make_world()
    # the evolving world is part of the RECORDED inputs (candidate set is
    # captured at record time; lifecycle facts apply to the shared objects):
    # L_c/Leg4 exist but are NOT YET KNOWABLE at the 52 decision
    w["points"].append(_pt("L_c", REP_C, "low", 48, 28.0, 56))
    w["clegs"].append(_leg("Leg4", REP_C, "H_b", "L_c", "down", 40, 48,
                           50.0, 28.0, 56))
    ledger = InterpretationLedger()
    rel = ContextualRelationships()
    s1 = _sel(w, role="origin-of-last-confirmed-leg", policy_id="P-ORIGIN",
              bar=52, rel=rel)
    payload1 = s1.ledger_payload(
        run_id="t10", points=w["points"], legs=w["clegs"], rep=REP_C,
        policy=w["pol"], role="origin-of-last-confirmed-leg",
        policy_id="P-ORIGIN", axis=AXIS, relationships=rel,
        decision_time=T0 + timedelta(minutes=52), state_id_prefix="S1X")
    # complete serialized inputs (finding F5)
    assert payload1["input_records"]["points"], "serialized inputs required"
    assert payload1["input_records"]["relationships"] is not None
    uid1 = ledger.record(s1.final_result, payload1)
    assert s1.candidate_id == "L_b"

    # actual dependent conclusion: the T-S5 falsifier of interpretation I1
    from trading_system.research.contextual_selection import task_s5_falsifier
    claims = [{"interpretation": "I1", "view": "C",
               "role": "origin-of-last-confirmed-leg", "direction": "up"}]
    r5 = task_s5_falsifier(claims, w["points"], w["clegs"], 52,
                           state_id_prefix="S5X", axis=AXIS,
                           decision_time=T0 + timedelta(minutes=52))
    assert r5.selected_id == "L_b"      # falsifier follows the reference
    # NOTE: no "decision_time" key — the kernel T-S5 recompute then uses the
    # UPDATE boundary (as-of-update recomputation, SP-20)
    uid2 = ledger.record(r5, {"kind": "T-S5", "claims": claims,
                              "points": w["points"], "legs": w["clegs"],
                              "depends_on_results": [uid1],
                              "state_id_prefix": "S5X",
                              "axis": AXIS})

    # changed evidence: a recorded break fact at the update boundary
    log = ledger.propagate(
        update_bar=56, changed_ids=["L_b"],
        changed_states={"L_b": "broken"},
        update_time=T0 + timedelta(minutes=56), event_ref="E:break@53",
        axis=AXIS)

    # expert selection: a NEW result version with ACTUAL computed changes
    v1 = ledger.versions[uid1]
    assert len(v1) == 2 and v1[-1]["version"] == 2
    assert v1[-1]["recomputable"] is True and not v1[-1].get("stale", False)
    change_fields = {c["field"] for c in v1[-1]["computed_changes"]}
    assert "selected_id" in change_fields
    assert v1[-1]["result"].selected_id == "H_b"
    # updated dependencies (L_b/Leg3 replaced by H_b/Leg4)
    deps = set(v1[-1]["result"].dependencies)
    assert "Leg4" in deps and "H_b" in deps and "Leg3" not in deps

    # dependent conclusion T-S5 also recomputed (transitive SP-20): per the
    # documented W8 semantics the falsifier being VIOLATED changes the
    # interpretation's status — the recomputed dependent conclusion is
    # honestly unresolved (never patched, never kept as stale-current)
    v2 = ledger.versions[uid2]
    assert len(v2) == 2 and v2[-1]["version"] == 2
    assert v2[-1]["recomputable"] is True and not v2[-1].get("stale", False)
    assert v2[-1]["result"].status in ("unresolved", "falsified")
    assert v2[-1]["result"].selected_id != "L_b"
    assert any(c["field"] in ("selected_id", "status")
               for c in v2[-1]["computed_changes"])
    # finding 5: the DOWNSTREAM early-UNRESOLVED result preserves the
    # dependencies actually evaluated — H_b and Leg4 were consumed by the
    # supporting-leg evaluation and must appear (result may stay unresolved)
    deps2 = set(v2[-1]["result"].dependencies)
    assert "H_b" in deps2 and "Leg4" in deps2
    assert any(c["field"] == "dependencies"
               for c in v2[-1]["computed_changes"])
    assert any(e.get("kind") == "recomputation" and not e.get("stale")
               for e in log)


def test_10b_stale_or_empty_recompute_is_never_success():
    w = make_world()
    ledger = InterpretationLedger()
    s1 = _sel(w, role="origin-of-last-confirmed-leg", policy_id="P-ORIGIN")
    # one dependent WITHOUT payload, one with an EMPTY expert payload
    uid_nopay = ledger.record(s1.final_result, None)
    uid_empty = ledger.record(
        s1.final_result,
        {"kind": "expert_structural_reference_selection"})   # empty inputs
    log = ledger.propagate(update_bar=53, changed_ids=["L_b"],
                           changed_states={"L_b": "broken"},
                           update_time=T0 + timedelta(minutes=53),
                           axis=AXIS)
    stale_entries = [e for e in log if e.get("stale")]
    assert stale_entries, "stale recomputation must be recorded as stale"
    # NOT success: no new recomputable version was appended
    assert len(ledger.versions[uid_nopay]) == 1
    assert len(ledger.versions[uid_empty]) == 1
    assert ledger.versions[uid_nopay][-1].get("stale") is True
    assert ledger.versions[uid_empty][-1].get("stale") is True
    reasons = " ".join(str(e.get("stale_reason", "")) for e in stale_entries)
    assert "payload" in reasons or "incomplete" in reasons or "empty" in reasons
    snap = ledger.snapshot()
    assert snap["n_stale_results"] >= 2


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
    assert len(pts) >= 100
    pol = PolicyRegistry()
    pol.register("P-ORIGIN", "role", "origin-of-last-confirmed-leg")
    t0 = time.perf_counter()
    for bar in (400, 800, 1200, 1600):
        s = expert_structural_reference_selection(
            points=pts, legs=legs, decision_bar=bar, rep=REP_C, policy=pol,
            role="origin-of-last-confirmed-leg", policy_id=None,
            relationships=ContextualRelationships())
        assert s.outcome in (OUTCOME_SELECTED, OUTCOME_UNRESOLVED)
    elapsed = time.perf_counter() - t0
    assert elapsed < 5.0, f"4 selections took {elapsed:.2f}s"


# --------------------------------------------------------------------------
# Audit acceptance: roles, ties, KP-02 event types, comparisons
# --------------------------------------------------------------------------
def test_adv_missing_and_mismatched_roles():
    w = make_world()
    for bad_role in (None, "", "origin-of-last-leg", "T-S1", 123):
        s = _sel(w, role=bad_role)
        assert s.outcome == OUTCOME_UNRESOLVED and s.candidate_id is None
        assert s.reason["code"] == REASON_MP
        assert "no valid declared role" in s.reason["text"]
        # invalid role never activates preferences (no bypass)
        assert not s.activated_preferences


def test_adv_incomplete_comparison_unresolved():
    w = make_world()
    # both candidates carry the indicated reference kind -> no licensed pair
    rel = ContextualRelationships(ref_kind={
        "L_a": {"value": "old-low-htf", "known_bar": 15},
        "L_b": {"value": "old-high-reclaimed", "known_bar": 35},
    })
    s = _sel(w, role="origin-of-last-confirmed-leg", policy_id=None, rel=rel)
    assert s.outcome == OUTCOME_UNRESOLVED
    assert not s.activated_preferences
    # one-sided evidence: the comparison cannot be made -> unresolved, and
    # the candidate lacking evidence is NOT silently omitted
    rel2 = ContextualRelationships(ref_kind={
        "L_b": {"value": "old-low-htf", "known_bar": 35}})
    s2 = _sel(w, role="origin-of-last-confirmed-leg", policy_id=None,
              rel=rel2)
    assert s2.outcome == OUTCOME_UNRESOLVED
    assert set(s2.surviving_candidate_ids) == {"L_a", "H_a", "L_b", "H_b"}


def test_adv_kp02_event_types_distinct_and_nonbinding():
    w = make_world()
    rel_rich = ContextualRelationships(test_history={
        "L_b": [{"bar": 33, "kind": EVENT_WICK_TOUCH},
                {"bar": 34, "kind": EVENT_CLOSE_THROUGH}],
        "L_a": [{"bar": 20, "kind": EVENT_WICK_TOUCH}],
        "H_a": [], "H_b": [],
    })
    rel_empty = ContextualRelationships(test_history={
        "L_b": [], "L_a": [], "H_a": [], "H_b": []})
    s_rich = _sel(w, role="origin-of-last-confirmed-leg", policy_id=None,
                  rel=rel_rich)
    s_empty = _sel(w, role="origin-of-last-confirmed-leg", policy_id=None,
                   rel=rel_empty)
    # nonbinding proof: test_history presence/value NEVER changes the output
    assert s_rich.outcome == s_empty.outcome
    assert s_rich.candidate_id == s_empty.candidate_id
    assert not s_rich.activated_preferences
    assert not s_empty.activated_preferences
    # event types are DISTINCT observations (state only)
    wick_items = [e for e in s_rich.evidence if e.name == "wick_range_touches"]
    thru_items = [e for e in s_rich.evidence if e.name == "close_throughs"]
    assert wick_items and thru_items
    assert all(e.value for e in wick_items) or any(
        e.value for e in wick_items)
    assert "state" in wick_items[0].detail
    assert "state" in thru_items[0].detail
    for e in s_rich.evidence:
        detail = (e.detail or "").lower()
        for forbidden in ("validated", "rejected", "successful reaction"):
            assert forbidden not in detail or "no rejection" in detail, \
                f"inference leaked into evidence: {e.name}"
    # KP-02 is documented as a nonbinding hypothesis
    kp02 = [i for i in s_rich.inactive_preferences if i["pref_id"] == "KP-02"]
    assert kp02 and "nonbinding" in kp02[0]["cause"]


def test_adv_equal_knowable_tie_unresolved_kernel_and_layer():
    # two confirmed points with IDENTICAL knowable stamps
    tie_world = {
        "points": [
            _pt("X_1", REP_C, "low", 30, 20.0, 35),
            _pt("X_2", REP_C, "high", 31, 40.0, 35),
        ],
        "clegs": [],
        "pol": PolicyRegistry(),
    }
    # kernel (delegated) itself: UNRESOLVED, never order-picked
    k1 = task_s1_structural_reference(
        tie_world["points"], [], 52, REP_C, "last-confirmed-extreme",
        tie_world["pol"], decision_time=T0 + timedelta(minutes=52), axis=AXIS)
    assert k1.status == "unresolved" and k1.selected_id is None
    assert set(k1.survivors) == {"X_1", "X_2"}
    assert k1.unresolved.reason_code == REASON_MP
    assert "tie" in k1.unresolved.evidence_needed
    # expert layer: same — UNRESOLVED regardless of input order
    for order in ([0, 1], [1, 0]):
        w = {"points": [tie_world["points"][i] for i in order],
             "clegs": [], "pol": PolicyRegistry()}
        s = _sel(w, role="last-confirmed-extreme")
        assert s.outcome == OUTCOME_UNRESOLVED and s.candidate_id is None
        assert set(s.surviving_candidate_ids) == {"X_1", "X_2"}


def test_adv_equal_leg_recency_tie_unresolved():
    # two legs with identical recency stamps but distinct origins
    pts = [
        _pt("A_1", REP_C, "low", 10, 10.0, 15),
        _pt("A_2", REP_C, "high", 20, 40.0, 25),
        _pt("B_1", REP_C, "low", 30, 20.0, 35),
        _pt("B_2", REP_C, "high", 40, 50.0, 45),
    ]
    leg1 = _leg("T1", REP_C, "A_1", "A_2", "up", 10, 20, 10.0, 40.0, 45)
    leg2 = _leg("T2", REP_C, "B_1", "B_2", "up", 30, 40, 20.0, 50.0, 45)
    # identical (knowable_time, t1_time, knowable_bar, t1) stamps:
    leg2.t1_time = leg1.t1_time
    leg2.knowable_time = leg1.knowable_time
    leg2.t1 = leg1.t1
    pol = PolicyRegistry()
    pol.register("P-ORIGIN", "role", "origin-of-last-confirmed-leg")
    k = task_s1_structural_reference(
        pts, [leg1, leg2], 52, REP_C, "origin-of-last-confirmed-leg", pol,
        policy_id="P-ORIGIN", decision_time=T0 + timedelta(minutes=52),
        axis=AXIS)
    assert k.status == "unresolved" and k.selected_id is None
    assert set(k.survivors) == {"A_1", "B_1"}
    assert "tie" in k.unresolved.evidence_needed
    # permutation invariance of the tie outcome
    k2 = task_s1_structural_reference(
        list(reversed(pts)), [leg2, leg1], 52, REP_C,
        "origin-of-last-confirmed-leg", pol, policy_id="P-ORIGIN",
        decision_time=T0 + timedelta(minutes=52), axis=AXIS)
    assert k2.status == "unresolved" and k2.selected_id is None
    assert set(k2.survivors) == {"A_1", "B_1"}


# --------------------------------------------------------------------------
# Contract checks
# --------------------------------------------------------------------------
def test_f_class_never_binds_or_licenses():
    with pytest.raises(ValueError):
        ExpertPreference(
            pref_id="BAD", task_id="T-S1", kclass="F", klass="U",
            source="x", source_family="x", statement="x", context="x",
            observable_evidence=(), licenses="none", exceptions="",
            conflict_status="", provenance_refs=(), binding=True)
    with pytest.raises(ValueError):
        ExpertPreference(
            pref_id="BAD2", task_id="T-S1", kclass="F", klass="U",
            source="x", source_family="x", statement="x", context="x",
            observable_evidence=(), licenses="tested>untested",
            exceptions="", conflict_status="", provenance_refs=())


def test_preference_resolution_is_pure_and_replayable():
    ids = ["a", "b", "c"]
    maps = {"a": {"ref_kind": "old-low-htf"},
            "b": {"ref_kind": "local"},
            "c": {"ref_kind": "local"}}
    kb = (_injected_htf_record(),)
    r1 = apply_expert_preferences(ids, maps, kb)
    r2 = apply_expert_preferences(ids, maps, kb)
    assert json.dumps(r1, sort_keys=True, default=str) == \
        json.dumps(r2, sort_keys=True, default=str)
    act, inact, conf, winner, diag = r1
    assert winner == "a" and not conf
    assert diag["preferred"] == ["a"]
    # default knowledge (all F-class) can never produce a winner
    r3 = apply_expert_preferences(ids, maps)
    assert r3[3] is None and not r3[0]


# --------------------------------------------------------------------------
# Audit acceptance (findings 1-4): stamp integrity, task/role/comparison
# completeness, nonbinding KP-03 contexts, tie guard vs preferences
# --------------------------------------------------------------------------
def test_adv_finding1_negative_known_bar_rejected():
    w = make_world()
    rel = ContextualRelationships(ref_kind={
        "L_a": {"value": "old-low-htf", "known_bar": -5},
    })
    s = _sel(w, role="origin-of-last-confirmed-leg", policy_id=None, rel=rel)
    assert any("negative" in d["reason"] for d in s.dropped_evidence)
    assert not any(e.name == "ref_kind" for e in s.evidence)
    assert s.outcome == OUTCOME_UNRESOLVED and not s.activated_preferences
    # events carry the same discipline
    rel2 = ContextualRelationships(test_history={
        "L_b": [{"bar": -3, "kind": EVENT_WICK_TOUCH}]})
    s2 = _sel(w, role="origin-of-last-confirmed-leg", policy_id=None,
              rel=rel2)
    assert any("negative" in d["reason"] for d in s2.dropped_evidence)


def test_adv_finding1_out_of_axis_known_bar_rejected():
    w = make_world()
    assert AXIS.n_rows == 2001
    rel = ContextualRelationships(ref_kind={
        "L_a": {"value": "old-low-htf", "known_bar": 100000},
    })
    s = _sel(w, role="origin-of-last-confirmed-leg", policy_id=None, rel=rel)
    assert any("out-of-axis" in d["reason"] for d in s.dropped_evidence)
    assert not any(e.name == "ref_kind" for e in s.evidence)
    assert s.outcome == OUTCOME_UNRESOLVED


def test_adv_finding1_inconsistent_bar_time_pair_rejected():
    w = make_world()
    # bar says coordinate 35, time says coordinate 40 — different axis
    # coordinates: REJECTED (and the consistent pair passes)
    rel_bad = ContextualRelationships(ref_kind={
        "L_b": {"value": "old-low-htf", "known_bar": 35,
                "known_time": T0 + timedelta(minutes=40)},
    })
    s_bad = _sel(w, role="origin-of-last-confirmed-leg", policy_id=None,
                 rel=rel_bad)
    assert any("inconsistent stamps" in d["reason"]
               for d in s_bad.dropped_evidence)
    assert not any(e.name == "ref_kind" for e in s_bad.evidence)
    rel_ok = ContextualRelationships(ref_kind={
        "L_b": {"value": "old-low-htf", "known_bar": 35,
                "known_time": T0 + timedelta(minutes=35)},
    })
    s_ok = _sel(w, role="origin-of-last-confirmed-leg", policy_id=None,
                rel=rel_ok)
    assert not any("inconsistent" in d["reason"]
                   for d in s_ok.dropped_evidence)
    assert any(e.name == "ref_kind" for e in s_ok.evidence)
    # rejected evidence never influences selection
    assert s_bad.outcome == OUTCOME_UNRESOLVED


def test_adv_finding2_task_id_mismatch_never_applies():
    w = make_world()
    rel = ContextualRelationships(ref_kind={
        "L_b": {"value": "old-low-htf", "known_bar": 35},
        "L_a": {"value": "local", "known_bar": 15},
        "H_a": {"value": "local", "known_bar": 25},
        "H_b": {"value": "local", "known_bar": 45},
    })
    foreign = _injected_htf_record(pref_id="T-FOREIGN", task_id="T-S9")
    s = _sel(w, role="origin-of-last-confirmed-leg", policy_id=None, rel=rel,
             knowledge=(foreign,))
    assert s.outcome == OUTCOME_UNRESOLVED and s.candidate_id is None
    assert not s.activated_preferences
    causes = {i["pref_id"]: i["cause"] for i in s.inactive_preferences}
    assert "task mismatch" in causes.get("T-FOREIGN", "")
    # the same record DOES apply when its task matches (control)
    ok = _sel(w, role="origin-of-last-confirmed-leg", policy_id=None, rel=rel,
              knowledge=(_injected_htf_record(),))
    assert ok.outcome == OUTCOME_SELECTED and ok.candidate_id == "L_b"


def test_adv_finding2_policy_role_mismatch_unresolved():
    w = make_world()
    pol = PolicyRegistry()
    pol.register("P-EXTREME", "role", "last-confirmed-extreme")
    w2 = dict(w, pol=pol)
    s = _sel(w2, role="origin-of-last-confirmed-leg", policy_id="P-EXTREME")
    assert s.outcome == OUTCOME_UNRESOLVED and s.candidate_id is None
    assert s.reason["code"] == REASON_MP
    assert "policy-role mismatch" in s.reason["text"]
    # the reversed mismatch is equally rejected
    pol2 = PolicyRegistry()
    pol2.register("P-ORIGIN2", "role", "origin-of-last-confirmed-leg")
    w3 = dict(w, pol=pol2)
    s2 = _sel(w3, role="last-confirmed-extreme", policy_id="P-ORIGIN2")
    assert s2.outcome == OUTCOME_UNRESOLVED
    assert "policy-role mismatch" in s2.reason["text"]
    # matching semantics proceed normally (control)
    s3 = _sel(w, role="origin-of-last-confirmed-leg", policy_id="P-ORIGIN")
    assert s3.outcome == OUTCOME_SELECTED and s3.candidate_id == "L_b"


def test_adv_finding2_partial_evidence_across_eligible_unresolved():
    w = make_world()
    # evidence on 3 of 4 eligible survivors; the 3 alone would pick L_b
    rel = ContextualRelationships(ref_kind={
        "L_b": {"value": "old-low-htf", "known_bar": 35},
        "L_a": {"value": "local", "known_bar": 15},
        "H_a": {"value": "local", "known_bar": 25},
    })
    s = _sel(w, role="origin-of-last-confirmed-leg", policy_id=None, rel=rel,
             knowledge=(_injected_htf_record(),))
    assert s.outcome == OUTCOME_UNRESOLVED and s.candidate_id is None
    assert not s.activated_preferences          # NO subset comparison
    assert s.reason["code"] == REASON_IC
    assert "H_b" in s.reason["text"]            # gap named explicitly
    assert set(s.surviving_candidate_ids) == {"L_a", "H_a", "L_b", "H_b"}


def test_adv_finding2_unknown_ref_kind_incomparable_not_other():
    w = make_world()
    # "mystery-kind" is OUTSIDE the declared vocabulary: incomparable —
    # never an ordinary "other" that would lose to old-low-htf
    rel = ContextualRelationships(ref_kind={
        "L_b": {"value": "old-low-htf", "known_bar": 35},
        "L_a": {"value": "local", "known_bar": 15},
        "H_a": {"value": "mystery-kind", "known_bar": 25},
        "H_b": {"value": "local", "known_bar": 45},
    })
    s = _sel(w, role="origin-of-last-confirmed-leg", policy_id=None, rel=rel,
             knowledge=(_injected_htf_record(),))
    assert s.outcome == OUTCOME_UNRESOLVED and s.candidate_id is None
    assert not s.activated_preferences          # no pair was licensed
    assert s.reason["code"] == REASON_EP        # empirical not learned
    assert "mystery-kind" in s.reason["text"] and "H_a" in s.reason["text"]
    assert "ordinary" in s.reason["evidence_needed"] or "other" in \
        s.reason["evidence_needed"]


def _tie_world_extreme():
    return {"points": [
        _pt("X_1", REP_C, "low", 30, 20.0, 35),
        _pt("X_2", REP_C, "high", 31, 40.0, 35),
    ], "clegs": [], "pol": PolicyRegistry()}


def test_adv_finding4_tie_not_overridden_by_preference_extreme():
    # valid preference evidence for BOTH tied candidates; the preference
    # WOULD pick X_1 — the tie guard must return UNRESOLVED anyway
    rel = ContextualRelationships(ref_kind={
        "X_1": {"value": "old-low-htf", "known_bar": 35},
        "X_2": {"value": "local", "known_bar": 35},
    })
    for order in ([0, 1], [1, 0]):
        w = _tie_world_extreme()
        w["points"] = [w["points"][i] for i in order]
        s = _sel(w, role="last-confirmed-extreme", rel=rel,
                 knowledge=(_injected_htf_record(),))
        assert s.outcome == OUTCOME_UNRESOLVED and s.candidate_id is None
        assert set(s.surviving_candidate_ids) == {"X_1", "X_2"}
        assert "tie" in s.reason["text"]
        assert not s.activated_preferences      # before applying preferences


def test_adv_finding4_tie_not_overridden_by_preference_origin():
    pts = [
        _pt("A_1", REP_C, "low", 10, 10.0, 15),
        _pt("A_2", REP_C, "high", 20, 40.0, 25),
        _pt("B_1", REP_C, "low", 30, 20.0, 35),
        _pt("B_2", REP_C, "high", 40, 50.0, 45),
    ]
    leg1 = _leg("T1", REP_C, "A_1", "A_2", "up", 10, 20, 10.0, 40.0, 45)
    leg2 = _leg("T2", REP_C, "B_1", "B_2", "up", 30, 40, 20.0, 50.0, 45)
    leg2.t1_time = leg1.t1_time
    leg2.knowable_time = leg1.knowable_time
    leg2.t1 = leg1.t1
    rel = ContextualRelationships(ref_kind={
        "A_1": {"value": "old-low-htf", "known_bar": 15},
        "B_1": {"value": "local", "known_bar": 35},
    })
    for order in ([0, 1], [1, 0]):
        w = {"points": [pts[i] for i in order],
             "clegs": [leg1, leg2] if order == [0, 1] else [leg2, leg1],
             "pol": PolicyRegistry()}
        s = _sel(w, role="origin-of-last-confirmed-leg", policy_id=None,
                 rel=rel, knowledge=(_injected_htf_record(),))
        assert s.outcome == OUTCOME_UNRESOLVED and s.candidate_id is None
        assert set(s.surviving_candidate_ids) == {"A_1", "B_1"}
        assert "tie" in s.reason["text"]
        assert not s.activated_preferences
