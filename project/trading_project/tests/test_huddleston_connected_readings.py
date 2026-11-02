"""Connected-readings test battery A–J (deliverable task §11).

Scope: three-candle FVG geometry + availability, cross-timeframe
linking (relation only, never identity), reference selection with
competing candidates, shift-watch + FVG sequence classification,
append-only interpretation revisions, save/resume, future-data
invariance, and source/engineering/unknowns separation.

This is a SEPARATE deterministic file so the study battery in
test_huddleston_study_links.py stays untouched.  All conventions
match the existing suite (float_precision="round_trip", case-
insensitive reason asserts, no provenance claims).
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import tempfile

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from trading_system.research.contextual_selection.csm import (  # noqa: E402
    InterpretationLedger,
)
from trading_system.research.contextual_selection.connected_readings import (  # noqa: E402
    CONCLUSION_EVIDENCE_PREFERRED,
    CONCLUSION_UNRESOLVED,
    FVG_GEOMETRY_DEFINITION,
    FVG_EXTERNAL_SOURCES,
    FVG_UNKNOWNS,
    ConnectedReadingsEngine,
    FVGRegion,
)


# ---------------------------------------------------------------- helpers

def _frame(index, highs, lows):
    return pd.DataFrame({
        "open": [h - 0.2 for h in highs],
        "high": highs,
        "low": lows,
        "close": [(h + l) / 2 for h, l in zip(highs, lows)],
    }, index=pd.DatetimeIndex(index, name="ts"))


class _Ref:
    """Minimal reference point compatible with link_regions/refs."""
    def __init__(self, cid, level, kind, t, side="low",
                 role="UNDETERMINED", status="confirmed"):
        self.candidate_id = cid
        self.level = float(level)
        self.kind = kind
        self.side = side
        self.role = role
        self.status = status
        self.occurrence_time = pd.Timestamp(t)


def _up_fvg_frame():
    """b1 high=100, b2 anywhere, b3 low=101 → upward FVG [100, 101]."""
    idx = pd.date_range("2025-09-10 00:00", periods=5, freq="4h", tz="UTC")
    return _frame(idx,
                  highs=[100.0, 100.8, 101.6, 101.4, 101.2],
                  lows=[99.0, 100.0, 101.0, 100.6, 100.4])


def _down_fvg_frame():
    """b1 low=100, b3 high=99 → downward FVG [99, 100]."""
    idx = pd.date_range("2025-09-10 00:00", periods=5, freq="4h", tz="UTC")
    return _frame(idx,
                  highs=[101.0, 100.4, 99.0, 99.6, 99.8],
                  lows=[100.0, 99.4, 98.2, 98.4, 98.6])


# ------------------------------------------------------------------- A

def test_A_fvg_observability_never_before_third_bar_and_bounds():
    eng = ConnectedReadingsEngine(run_id="tA", instrument="TEST",
                                  timezone="UTC")
    f = _up_fvg_frame()
    f2 = f.iloc[:2]                     # only b1, b2 visible
    assert eng.scan_fvgs({"4h": f2}) == []
    changes = eng.scan_fvgs({"4h": f})
    assert any("fvg_region" in str(c.get("aspect", "")) for c in changes)
    (reg,) = eng.regions.values()
    assert reg.direction == "upward"
    assert reg.timeframe == "4h"
    assert reg.lower_bound == 100.0 and reg.upper_bound == 101.0
    assert reg.ce_midpoint == 100.5
    # availability: never observable before bar3's completion label
    assert "not_yet_observable" in reg.availability(
        pd.Timestamp("2025-09-10 04:00", tz="UTC"))
    assert "observable since" in reg.availability(
        pd.Timestamp("2025-09-10 08:00", tz="UTC"))
    assert "INCOMPLETE" in reg.availability(
        pd.Timestamp("2025-09-10 08:00", tz="UTC"))
    assert str(reg.observability_time) == "2025-09-10 08:00:00+00:00"
    # downward definition symmetric
    eng2 = ConnectedReadingsEngine(run_id="tA2", instrument="TEST",
                                   timezone="UTC")
    eng2.scan_fvgs({"4h": _down_fvg_frame()})
    (reg2,) = eng2.regions.values()
    assert reg2.direction == "downward"
    assert (reg2.lower_bound, reg2.upper_bound) == (99.0, 100.0)
    # no non-overlap → no FVG
    eng3 = ConnectedReadingsEngine(run_id="tA3", instrument="TEST",
                                   timezone="UTC")
    f3 = _frame(pd.date_range("2025-09-10 00:00", periods=5, freq="4h",
                              tz="UTC"),
                highs=[100.0, 100.5, 100.4, 100.6, 100.5],
                lows=[99.0, 99.5, 99.4, 99.6, 99.5])
    assert eng3.scan_fvgs({"4h": f3}) == []
    # hidden assumptions surface
    rec = reg.to_record()
    assert rec["hidden_assumptions"]


# ------------------------------------------------------------------- B

def test_B_different_timeframes_never_identical_representation():
    eng = ConnectedReadingsEngine(run_id="tB", instrument="TEST",
                                  timezone="UTC")
    idx4 = pd.date_range("2025-09-10 00:00", periods=4, freq="4h", tz="UTC")
    f4 = _frame(idx4,
                highs=[100.0, 100.4, 100.6, 100.8],
                lows=[99.0, 99.4, 99.6, 99.8])       # NO 4h FVG
    idx15 = pd.date_range("2025-09-10 00:00", periods=16, freq="15min",
                          tz="UTC")
    h15 = [100.0, 100.2, 100.4, 100.3] + [100.5] * 12
    l15 = [99.0, 99.2, 100.1, 100.0] + [99.6] * 12   # 15min FVG at bar3
    f15 = _frame(idx15, highs=h15, lows=l15)
    eng.scan_fvgs({"4h": f4, "15min": f15})
    tfs = {r.timeframe for r in eng.regions.values()}
    assert "4h" not in tfs and "15min" in tfs      # observable bars differ
    # cross-frame link is a RELATION, never an identity/equivalence claim
    ref = _Ref("R1", 100.05, "swing_low",
               pd.Timestamp("2025-09-10 00:00", tz="UTC"))
    links = eng.link_regions(refs=[ref], as_of_time=pd.Timestamp(
        "2025-09-10 06:00", tz="UTC"))
    for link in eng.links:
        assert link.relation in ("interval_contains_level",
                                 "intervals_overlap", "intervals_disjoint")
        assert "NOT an identity claim" in link.note
        assert "cross-timeframe" in link.note or link.other_frame
        rel = link.to_record()["relation"]
        assert "same" not in rel and "equal" not in rel
    assert isinstance(links, list)


# ------------------------------------------------------------------- C

def test_C_same_fvg_two_contexts_classified_differently_with_alternatives():
    eng = ConnectedReadingsEngine(run_id="tC", instrument="TEST",
                                  timezone="UTC")
    eng.scan_fvgs({"4h": _up_fvg_frame()})
    (reg,) = eng.regions.values()
    as_of = pd.Timestamp("2025-09-10 12:00", tz="UTC")
    i1 = eng.interpretation_for_hf(
        as_of_time=as_of, trend="up",
        evidence=["hf displacement 1D up"],
        derived_at=pd.Timestamp("2025-09-10 00:00", tz="UTC"))
    s1 = i1.statement                       # capture BEFORE the change
    v1 = json.loads(json.dumps(i1.versions[-1]))
    assert i1.alternatives                 # classification keeps alternatives
    i2 = eng.interpretation_for_hf(
        as_of_time=as_of, trend="down",
        evidence=["hf displacement 1D down"],
        derived_at=pd.Timestamp("2025-09-10 00:00", tz="UTC"))
    s2 = i2.statement
    assert s1 != s2                     # classification differs by context
    # old and new interpretations preserved side by side (linked versions)
    assert i2.versions[0] == v1
    assert i2.versions[-1]["revision_of"] == 1
    for t in (i1, i2):
        rec = json.dumps(t.to_record()).lower()
        assert "alternative" in rec
        assert "valid" not in rec.split("alternatives")[0] or \
            "not" in rec.split("alternatives")[0]
        # no direction ⇒ valid rule
        assert "buy" not in rec and "sell" not in rec
        assert "entry" not in rec and "target" not in rec
        # ---- test C: same FVG under two watches (crossing before vs
    # after its observability) is classified differently; each
    # conclusion keeps declared criteria evidence + alternatives -------
    eng.update_interactions({"4h": _up_fvg_frame()})
    w_early = {
        "watch_id": "W-early",
        "crossing": {"ref_id": "R1", "ref_level": 100.05,
                     "bar": 4,
                     "bar_time": str(pd.Timestamp(
                         "2025-09-10 12:00", tz="UTC")),
                     "direction": "upward"},
        "evidence": [],
    }
    w_late = {
        "watch_id": "W-late",
        "crossing": {"ref_id": "R1", "ref_level": 100.05,
                     "bar": 2,
                     "bar_time": str(pd.Timestamp(
                         "2025-09-10 04:00", tz="UTC")),
                     "direction": "upward"},
        "evidence": [],
    }
    t1 = eng.task_fvg_relevance_for_watch(watch=w_early, as_of_time=as_of)
    t2 = eng.task_fvg_relevance_for_watch(watch=w_late, as_of_time=as_of)
    assert t1.conclusion["status"] != t2.conclusion["status"] or \
        t1.conclusion["preferred"] != t2.conclusion["preferred"]
    for t in (t1, t2):
        assert isinstance(t.conclusion["alternatives"], list)
        assert t.candidates            # no silent deletion


# ------------------------------------------------------------------- D

def test_D_competing_references_preference_and_unresolved_no_tiebreak():
    def refs():
        return [
            _Ref("R-A", 100.05, "swing_low",
                 pd.Timestamp("2025-09-10 00:00", tz="UTC"), role="REACTION"),
            _Ref("R-B", 100.02, "swing_low",
                 pd.Timestamp("2025-09-10 04:00", tz="UTC")),
        ]

    as_of = pd.Timestamp("2025-09-10 12:00", tz="UTC")
    eng = ConnectedReadingsEngine(run_id="tD", instrument="TEST",
                                  timezone="UTC")
    eng.scan_fvgs({"4h": _up_fvg_frame()})
    # (a) exactly one interacted → justified preference naming evidence
    t = eng.task_reference_for_review(refs=refs(), as_of_time=as_of,
                                      interacted=["R-A"])
    assert t.conclusion["status"] == CONCLUSION_EVIDENCE_PREFERRED
    assert t.conclusion["preferred"] == "R-A"
    assert any("observed" in r.lower() for r in t.conclusion["reasons"])
    assert {a["candidate_id"] for a in t.conclusion["alternatives"]} == \
        {"R-B"}                        # non-preferred kept as alternative
    assert {c["candidate_id"] for c in t.candidates} == {"R-A", "R-B"}
    #                                 nothing silently deleted
    # input order must NOT decide: shuffle → same conclusion
    eng2 = ConnectedReadingsEngine(run_id="tD2", instrument="TEST",
                                   timezone="UTC")
    eng2.scan_fvgs({"4h": _up_fvg_frame()})
    r2 = list(reversed(refs()))
    t2 = eng2.task_reference_for_review(refs=r2, as_of_time=as_of,
                                        interacted=["R-A"])
    assert (t2.conclusion["status"], t2.conclusion["preferred"]) == \
        (t.conclusion["status"], t.conclusion["preferred"])
    # (b) equally interacted → UNRESOLVED (no confidence %, no tie-break)
    eng3 = ConnectedReadingsEngine(run_id="tD3", instrument="TEST",
                                   timezone="UTC")
    eng3.scan_fvgs({"4h": _up_fvg_frame()})
    t3 = eng3.task_reference_for_review(
        refs=refs(), as_of_time=as_of,
        interacted=["R-A", "R-B"])
    assert t3.conclusion["status"] == CONCLUSION_UNRESOLVED
    assert t3.conclusion["preferred"] is None
    assert len(t3.candidates) == 2
    # (c) nothing interacted → also unresolved
    eng4 = ConnectedReadingsEngine(run_id="tD4", instrument="TEST",
                                   timezone="UTC")
    eng4.scan_fvgs({"4h": _up_fvg_frame()})
    t4 = eng4.task_reference_for_review(refs=refs(), as_of_time=as_of,
                                        interacted=[])
    assert t4.conclusion["status"] == CONCLUSION_UNRESOLVED


# ------------------------------------------------------------------- E

def test_E_shift_watch_sequence_classification_and_unorderable_case():
    eng = ConnectedReadingsEngine(run_id="tE", instrument="TEST",
                                  timezone="UTC")
    eng.scan_fvgs({"4h": _up_fvg_frame()})
    as_of = pd.Timestamp("2025-09-10 12:00", tz="UTC")
    # crossing BEFORE the FVG's observability → orderable sequence
    w = {
        "watch_id": "W-1",
        "crossing": {"ref_id": "R-1", "ref_level": 100.05,
                     "bar": 2, "bar_time": str(pd.Timestamp(
                         "2025-09-10 04:00", tz="UTC")),
                     "direction": "upward"},
        "evidence": [],
    }
    t = eng.task_fvg_relevance_for_watch(watch=w, as_of_time=as_of)
    c = t.conclusion
    assert c["status"] == CONCLUSION_EVIDENCE_PREFERRED
    cand = t.candidates[0]
    assert cand["chronology"] == "crossing_before_fvg_observable"
    # the sequence is recorded and the FVG is NOT proof of a shift
    alltxt = json.dumps(t.to_record()).lower()
    assert "crossing_before_fvg_observable" in alltxt
    assert "not proof" in alltxt
    for banned in ("shift confirmed", "guarantee", "must fill",
                   "buy", "sell", "entry", "target"):
        assert banned not in alltxt
    # unorderable case: crossing at the SAME completion boundary as the
    # FVG's observability → the ordering uncertainty is RECORDED, not guessed
    eng2 = ConnectedReadingsEngine(run_id="tE2", instrument="TEST",
                                   timezone="UTC")
    eng2.scan_fvgs({"4h": _up_fvg_frame()})
    w2 = {
        "watch_id": "W-2",
        "crossing": {"ref_id": "R-1", "ref_level": 100.05,
                     "bar": 3, "bar_time": str(pd.Timestamp(
                         "2025-09-10 08:00", tz="UTC")),
                     "direction": "upward"},
        "evidence": [],
    }
    t2 = eng2.task_fvg_relevance_for_watch(watch=w2, as_of_time=as_of)
    assert "unorderable" in t2.candidates[0]["chronology"]
    assert t2.conclusion["status"] == CONCLUSION_UNRESOLVED
    # and the case FVG-observable-before-crossing is recorded as such
    eng3 = ConnectedReadingsEngine(run_id="tE3", instrument="TEST",
                                   timezone="UTC")
    eng3.scan_fvgs({"4h": _up_fvg_frame()})
    w3 = {
        "watch_id": "W-3",
        "crossing": {"ref_id": "R-1", "ref_level": 100.05,
                     "bar": 4, "bar_time": str(pd.Timestamp(
                         "2025-09-10 12:00", tz="UTC")),
                     "direction": "upward"},
        "evidence": [],
    }
    t3 = eng3.task_fvg_relevance_for_watch(watch=w3, as_of_time=as_of)
    assert t3.candidates[0]["chronology"] == \
        "fvg_observable_before_crossing"


# ------------------------------------------------------------------- F

def test_F_revision_appends_linked_version_old_unchanged():
    eng = ConnectedReadingsEngine(run_id="tF", instrument="TEST",
                                  timezone="UTC")
    eng.scan_fvgs({"4h": _up_fvg_frame()})
    as_of = pd.Timestamp("2025-09-10 12:00", tz="UTC")
    w = {
        "watch_id": "W-1",
        "crossing": {"ref_id": "R-1", "ref_level": 100.05,
                     "bar": 4, "bar_time": str(pd.Timestamp(
                         "2025-09-10 12:00", tz="UTC")),
                     "direction": "down"},
        "evidence": [],
    }
    i = eng.interpretation_for_watch(watch=w, as_of_time=as_of)
    old = json.loads(json.dumps(i.versions[-1]))
    i.revise(statement="the crossing is re-observed against level 100.5",
             reason="candidate set changed (new reference R-2 recorded)",
             evidence=[{"kind": "new_reference", "id": "R-2",
                        "at": str(as_of)}],
             recorded_at=as_of)
    assert len(i.versions) == 2
    assert i.versions[-1]["revision_of"] == 1
    assert i.versions[0] == old          # old version preserved unchanged
    assert i.versions[0]["version"] == 1
    # a weakening hypothesis never flips automatically to its opposite:
    # status is "REVISED" — the hypothesis was NOT silently inverted
    assert i.versions[-1]["status"] == "REVISED"
    assert i.versions[-1]["statement"] != old["statement"]
    assert i.revision_count == 1
    # a second revision chains from version 2
    i.revise(statement="still monitoring", reason="no new evidence",
             evidence=[], recorded_at=as_of)
    assert i.versions[-1]["revision_of"] == 2


# ------------------------------------------------------------------- G

def test_G_no_change_observation_never_invents_change():
    eng = ConnectedReadingsEngine(run_id="tG", instrument="TEST",
                                  timezone="UTC")
    eng.scan_fvgs({"4h": _up_fvg_frame()})
    eng.update_interactions({"4h": _up_fvg_frame()})
    as_of = pd.Timestamp("2025-09-10 12:00", tz="UTC")
    i = eng.interpretation_for_hf(as_of_time=as_of, trend="up",
                                  evidence=["e1"], derived_at=as_of)
    assert len(i.versions) == 1
    # same context re-observed → no new version, no new interpretation
    i2 = eng.interpretation_for_hf(as_of_time=as_of, trend="up",
                                   evidence=["e1"], derived_at=as_of)
    assert i2 is i and len(i2.versions) == 1
    # task re-conclusion with identical state → no new version
    w = {
        "watch_id": "W-1",
        "crossing": {"ref_id": "R-1", "ref_level": 100.05,
                     "bar": 2, "bar_time": str(pd.Timestamp(
                         "2025-09-10 04:00", tz="UTC")),
                     "direction": "upward"},
        "evidence": [],
    }
    t = eng.task_fvg_relevance_for_watch(watch=w, as_of_time=as_of)
    n = len(t.versions)
    t2 = eng.task_fvg_relevance_for_watch(watch=w, as_of_time=as_of)
    assert t2 is t and len(t2.versions) == n
    # evidence unchanged → facts unchanged
    facts = [json.dumps(f, sort_keys=True, default=str)
             for f in eng.seq_facts]
    eng.update_interactions({"4h": _up_fvg_frame()})
    facts2 = [json.dumps(f, sort_keys=True, default=str)
              for f in eng.seq_facts]
    assert facts == facts2


# ------------------------------------------------------------------- H

def test_H_save_resume_preserves_fvg_links_alternatives_watch_ledger():
    eng = ConnectedReadingsEngine(run_id="tH", instrument="TEST",
                                  timezone="UTC")
    eng.scan_fvgs({"4h": _up_fvg_frame()})
    as_of = pd.Timestamp("2025-09-10 12:00", tz="UTC")
    ref = _Ref("R-A", 100.05, "swing_low",
               pd.Timestamp("2025-09-10 00:00", tz="UTC"))
    eng.link_regions(refs=[ref], as_of_time=as_of)
    w = {
        "watch_id": "W-1",
        "crossing": {"ref_id": "R-A", "ref_level": 100.05,
                     "bar": 4, "bar_time": str(pd.Timestamp(
                         "2025-09-10 12:00", tz="UTC")),
                     "direction": "down"},
        "evidence": [],
    }
    eng.task_fvg_relevance_for_watch(watch=w, as_of_time=as_of)
    eng.task_reference_for_review(refs=[ref], as_of_time=as_of,
                                  interacted=["R-A"])
    eng.interpretation_for_hf(as_of_time=as_of, trend="up",
                              evidence=["e"], derived_at=as_of)
    ledger = InterpretationLedger()
    eng.sync_ledger(ledger)
    st = json.loads(json.dumps(eng.state_dict(), default=str))
    # fresh engine restores EVERYTHING
    eng2 = ConnectedReadingsEngine(run_id="tH", instrument="TEST",
                                   timezone="UTC")
    eng2.load_state_dict(st)
    st2 = json.loads(json.dumps(eng2.state_dict(), default=str))
    assert st2 == st                    # incl. FVGs, links, alternatives,
    #                                 watch conditions, ledger refs
    assert eng2.regions and eng2.links and eng2.tasks and eng2.interps
    # ledger state round-trips exactly (revisions preserved)
    lst = ledger.to_state()
    led2 = InterpretationLedger()
    led2.load_state(json.loads(json.dumps(lst, default=str)))
    assert json.dumps(led2.to_state(), sort_keys=True, default=str) == \
        json.dumps(json.loads(json.dumps(lst, default=str)),
                   sort_keys=True)
    # revisions continue after resume (version numbering preserved)
    i = list(eng2.interps.values())[0]
    before = len(i.versions)
    i.revise(statement="post-resume revision", reason="new evidence",
             evidence=[{"kind": "e"}], recorded_at=as_of)
    assert i.versions[-1]["version"] == before + 1


# ------------------------------------------------------------------- I

def test_I_future_data_invariance():
    """State computed as-of T is byte-identical whether or not later
    data exists in the frames the engine is later shown."""
    f = _up_fvg_frame()
    t_cut = pd.Timestamp("2025-09-10 08:00", tz="UTC")
    eng1 = ConnectedReadingsEngine(run_id="tI", instrument="TEST",
                                   timezone="UTC")
    eng1.scan_fvgs({"4h": f.iloc[:3]})
    eng1.update_interactions({"4h": f.iloc[:3]}, as_of_time=t_cut)
    ref = _Ref("R-A", 100.05, "swing_low",
               pd.Timestamp("2025-09-10 00:00", tz="UTC"))
    eng1.link_regions(refs=[ref], as_of_time=t_cut)
    w = {
        "watch_id": "W-1",
        "crossing": {"ref_id": "R-A", "ref_level": 100.05,
                     "bar": 3, "bar_time": str(t_cut),
                     "direction": "down"},
        "evidence": [],
    }
    eng1.task_fvg_relevance_for_watch(watch=w, as_of_time=t_cut)
    st1 = json.loads(json.dumps(eng1.state_dict(), default=str))
    # engine that SAW the future (all 5 bars), but as-of the same T
    eng2 = ConnectedReadingsEngine(run_id="tI2", instrument="TEST",
                                   timezone="UTC")
    eng2.scan_fvgs({"4h": f})
    eng2.update_interactions({"4h": f}, as_of_time=t_cut)
    eng2.link_regions(refs=[ref], as_of_time=t_cut)
    eng2.task_fvg_relevance_for_watch(watch=w, as_of_time=t_cut)
    # as-of the cut: only the same regions/links/facts may be ACTED on —
    # identical conclusion for the same as-of
    t1 = list(eng1.tasks.values())[0]
    t2 = list(eng2.tasks.values())[0]
    # conclusions identical modulo run-scoped region ids
    c1 = json.dumps(t1.conclusion, sort_keys=True, default=str)
    c2 = json.dumps(t2.conclusion, sort_keys=True, default=str) \
        .replace("FVG-tI2-", "FVG-tI-")
    assert c1 == c2
    # the future bars must NOT change past conclusions
    for reg in eng1.regions.values():
        assert reg.observability_time <= t_cut
    # and the recorded facts of eng1 are all ≤ as_of
    for fact in eng1.seq_facts:
        if fact.get("fact", "").startswith("FVG_OBSERVABLE"):
            assert pd.Timestamp(fact["at"]) <= t_cut


# ------------------------------------------------------------------- J

def test_J_source_engineering_unknowns_distinguishable():
    # source material is labelled as external SECONDARY references
    assert FVG_EXTERNAL_SOURCES
    for s in FVG_EXTERNAL_SOURCES:
        assert "external" in s.lower()
        assert "http" in s
    # unknowns explicitly enumerate what cannot be inferred
    blob = " ".join(FVG_UNKNOWNS).lower()
    for must in ("fill", "orders", "intent", "signal",
                 "identical", "path"):
        assert must in blob
    # geometry definition declares completed-bar semantics
    assert "completed" in FVG_GEOMETRY_DEFINITION.lower()
    assert "midpoint" in FVG_GEOMETRY_DEFINITION.lower()
    # records separate layers: observations vs interpretation notes
    eng = ConnectedReadingsEngine(run_id="tJ", instrument="TEST",
                                  timezone="UTC")
    eng.scan_fvgs({"4h": _up_fvg_frame()})
    (reg,) = eng.regions.values()
    layers = {n.get("layer") for n in reg.interpretation_notes}
    assert {"DIRECT_OBSERVATION", "CONTEXTUAL_INTERPRETATION"} <= layers
    # every note distinguishes observed facts from derived/unknowns
    for n in reg.interpretation_notes:
        assert n["layer"] in ("DIRECT_OBSERVATION", "DERIVATION",
                              "CONTEXTUAL_INTERPRETATION",
                              "UNKNOWN_UNSUPPORTED")
    rec = reg.to_record()
    assert rec["source_note"].startswith("FVG geometry per external")
    assert rec["unknowns"] == list(FVG_UNKNOWNS)
