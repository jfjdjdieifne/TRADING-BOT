"""SAFE INTEGRATION V1 — behavioral regressions for the independent audit
(CSM V1 audit REVISE on 34a2c7a, section F probes).

One regression per REPRODUCED counterexample — each test drives the public
path and asserts ACTUAL behavior (eligibility, labels, revisions, files),
never a returned status name alone:

F1  axis enforcement for time-bearing inputs (T-S2 provisional occurrence,
    T-S3 leg endpoints, status-transition times)
F2  same-time event ordering (EVENT_ORDER_V1), chronological transition
    handling, replay identity, event-phase-only computed changes
F3  immutable effective policy snapshots; structured policy contradictions
F4  incomplete dependency coverage marks transitive descendants stale
F5  candidate rows carry durable lifecycle evidence
F6  atomic artifact writing; refusal to mix stale/seeded outputs
+   complete-path future-data invariance
"""
from __future__ import annotations

import gzip
import json
from datetime import timedelta

import pandas as pd
import pytest

from trading_system.research.contextual_selection import (
    STATUS_BROKEN,
    STATUS_CONFIRMED,
    STATUS_PROVISIONAL,
    STATUS_SUPERSEDED,
    X_GEOM,
    X_KNOW,
    InterpretationLedger,
    LegCandidate,
    PointCandidate,
    PolicyRegistry,
    Representation,
    SharedInformationAxis,
    candidate_record,
    fk_turning_points,
    build_legs,
    task_s1_structural_reference,
    task_s2_event_binding,
    task_s3_entry_leg,
    task_s5_falsifier,
)
from trading_system.research.contextual_selection.artifacts import (
    ArtifactWriteError,
    require_clean_out_dir,
    write_run_artifacts,
)

T0 = pd.Timestamp("2025-01-01 00:00:00")
AXIS = SharedInformationAxis(
    "repair-fixture-minute-grid",
    pd.date_range(T0, T0 + pd.Timedelta(minutes=2000), freq="1min"))
OFF_GRID = T0 + pd.Timedelta(seconds=30)     # 00:00:30 — never on the grid


def _rep(view="C", family="F-K", **params):
    return Representation(family=family, view_id=view, scale_label=view,
                          params=tuple(sorted(params.items())))


def _pt(pid, rep, side, occ, level, know, status=STATUS_CONFIRMED):
    return PointCandidate(
        candidate_id=pid, rep=rep, side=side, occurrence_bar=occ, level=level,
        knowable_bar=know, status=status,
        occurrence_time=T0 + timedelta(minutes=occ),
        knowable_time=(T0 + timedelta(minutes=know)) if know is not None else None)


def _lg(leg_id, rep, s, e, direction, b0, b1, p0, p1, know):
    return LegCandidate(leg_id, rep, s, e, direction, b0, b1, p0, p1, know,
                        t0_time=T0 + timedelta(minutes=b0),
                        t1_time=T0 + timedelta(minutes=b1),
                        knowable_time=T0 + timedelta(minutes=know))


# =========================================================================
# F1 — axis enforcement for time-bearing inputs
# =========================================================================

def test_f1_t2_off_grid_provisional_occurrence_never_eligible():
    """Audit F: a direct T-S2 call ACCEPTED an off-grid provisional
    occurrence time (raw comparison).  Now the occurrence-visibility claim
    is unverifiable: the provisional is excluded X-KNOW and never eligible —
    the off-grid value is never USED in a comparison."""
    rep = _rep()
    prov = _pt("prov", rep, "low", 3, 10.0, 5, status=STATUS_PROVISIONAL)
    prov.occurrence_time = OFF_GRID          # off the shared axis
    ev_t = T0 + timedelta(minutes=5)
    r = task_s2_event_binding(5, 0.0, {"C": [prov]}, 5, event_time=ev_t,
                              axis=AXIS, allow_provisional=True,
                              event_ref="F1a-E5")
    assert r.survivors == []
    assert r.selected_id is None
    codes = {e.candidate_id: e.code for e in r.excluded}
    assert codes.get("prov") == X_KNOW
    details = " ".join(e.detail for e in r.excluded)
    assert "verified information time" in details
    # the same candidate with a VERIFIED occurrence is eligible (control)
    prov2 = _pt("prov2", rep, "low", 3, 10.0, 5, status=STATUS_PROVISIONAL)
    r2 = task_s2_event_binding(5, 0.0, {"C": [prov2]}, 5, event_time=ev_t,
                               axis=AXIS, allow_provisional=True,
                               event_ref="F1a-E5b")
    assert r2.survivors == ["prov2"]


def test_f1_t3_off_grid_leg_endpoints_never_used_for_geometry():
    """Audit F: a direct T-S3 call USED off-grid leg endpoints.  Now an
    unverifiable endpoint is unverifiable GEOMETRY: containment is never
    computed from it (fine -> X-GEOM; coarse -> unresolved IC)."""
    rep_c, rep_f = _rep("C"), _rep("F")
    coarse = _lg("cg", rep_c, "a", "b", "up", 0, 10, 0.0, 100.0, 10)
    fine = _lg("fg", rep_f, "x", "y", "down", 2, 4, 80.0, 20.0, 4)
    fine.t1_time = OFF_GRID                  # endpoint off the shared axis
    r = task_s3_entry_leg(coarse, [fine], 20, rep_f,
                          decision_time=T0 + timedelta(minutes=20), axis=AXIS)
    assert r.selected_id != "fg"
    codes = {e.candidate_id: e.code for e in r.excluded}
    assert codes.get("fg") == X_GEOM
    # coarse endpoints unverifiable -> the containment BASIS fails closed
    coarse2 = _lg("cg2", rep_c, "a", "b", "up", 0, 10, 0.0, 100.0, 10)
    coarse2.t0_time = OFF_GRID
    fine2 = _lg("fg2", rep_f, "x", "y", "down", 2, 4, 80.0, 20.0, 4)
    r2 = task_s3_entry_leg(coarse2, [fine2], 20, rep_f,
                           decision_time=T0 + timedelta(minutes=20), axis=AXIS)
    assert r2.status == "unresolved"
    assert r2.survivors == []


def test_f1_off_grid_status_transition_time_never_applied():
    """Audit F: an off-grid status-transition time was APPLIED.  Now a
    time-bearing transition requires the validated axis AND a verified key —
    an off-grid transition time is rejected, never recorded."""
    rep = _rep()
    p = _pt("x", rep, "low", 1, 5.0, 2)
    with pytest.raises(ValueError, match="verified information time"):
        p.add_transition(30, STATUS_BROKEN, info_time=OFF_GRID, axis=AXIS)
    assert p.status_transitions == []        # nothing applied
    # without any axis a time-bearing transition is likewise refused
    with pytest.raises(ValueError, match="axis"):
        p.add_transition(30, STATUS_BROKEN,
                         info_time=T0 + timedelta(minutes=30))
    assert p.status_transitions == []
    # and a verified on-grid transition applies normally (control)
    p.add_transition(30, STATUS_BROKEN,
                     info_time=T0 + timedelta(minutes=30), axis=AXIS)
    assert len(p.status_transitions) == 1


# =========================================================================
# F2 — ordering, chronological transitions, replay identity
# =========================================================================

def test_f2_same_time_event_labels_are_order_independent():
    """Audit F: processing two same-time events A then B made A first-break
    and B later-interaction; reversing the order reversed the labels.  Now
    EVENT_ORDER_V1 governs: same-time events order by event identity, the
    pre-event state respects that order, and out-of-order APPLICATION is
    rejected outright."""
    rep = _rep()
    ref = _pt("R", rep, "high", 1, 100.0, 2)
    t_ev = T0 + timedelta(minutes=10)
    # canonical order: E1 < E2 at the same information time
    ev1 = task_s2_event_binding(10, 110.0, {"C": [ref]}, 10, event_time=t_ev,
                                axis=AXIS, event_ref="E1")
    assert ev1.binding_kinds == {"R": "first-break"}
    ref.add_transition(10, STATUS_BROKEN, info_time=t_ev, event_ref="E1",
                       axis=AXIS)
    ev2 = task_s2_event_binding(10, 112.0, {"C": [ref]}, 10, event_time=t_ev,
                                axis=AXIS, event_ref="E2")
    assert ev2.binding_kinds == {"R": "later-interaction"}
    # REVERSED application order is rejected (never a silent relabel):
    ref2 = _pt("R2", rep, "high", 1, 100.0, 2)
    ref2.add_transition(10, STATUS_BROKEN, info_time=t_ev, event_ref="E2",
                        axis=AXIS)          # out-of-order application
    with pytest.raises(ValueError, match="EVENT_ORDER_V1"):
        task_s2_event_binding(10, 110.0, {"C": [ref2]}, 10, event_time=t_ev,
                              axis=AXIS, event_ref="E1")
    # with BOTH transitions applied, the reconstructed labels are canonical
    # regardless of which transition was inserted first
    ref2.add_transition(10, STATUS_BROKEN, info_time=t_ev, event_ref="E1",
                        axis=AXIS)
    # (status reconstruction is chronological + EVENT_ORDER_V1)
    assert ref2.status_at(10, t_ev, excluding_event_ref="E1") == STATUS_CONFIRMED
    assert ref2.status_at(10, t_ev, excluding_event_ref="E2") == STATUS_BROKEN


def test_f2_status_at_chronological_not_insertion_order():
    """Audit F: an out-of-order transition sequence made status_at(35)
    return superseded despite the chronologically later transition being
    broken.  Reconstruction is chronological — insertion order never wins."""
    rep = _rep()
    p = _pt("S", rep, "low", 1, 5.0, 2)
    # inserted OUT of chronological order: broken@40 BEFORE superseded@20
    p.add_transition(40, STATUS_BROKEN)
    p.add_transition(20, STATUS_SUPERSEDED)
    assert p.status_at(35) == STATUS_SUPERSEDED    # only @20 applies at 35
    assert p.status_at(50) == STATUS_BROKEN        # @40 is chronologically last
    # a third earlier transition inserted LAST must still sort first
    p.add_transition(5, STATUS_PROVISIONAL)
    assert p.status_at(10) == STATUS_PROVISIONAL
    assert p.status_at(35) == STATUS_SUPERSEDED
    assert p.status_at(50) == STATUS_BROKEN


def test_f2_replay_identity_is_mandatory_and_stable():
    """Audit F: replaying an event after its own transition was applied
    required the caller to supply event_ref — omitting it silently changed
    first-break into later-interaction.  Now identity-less time-based calls
    are REJECTED and an identity-bearing replay is stable."""
    rep = _rep()
    ref = _pt("R", rep, "high", 1, 100.0, 2)
    t_ev = T0 + timedelta(minutes=10)
    ev = task_s2_event_binding(10, 110.0, {"C": [ref]}, 10, event_time=t_ev,
                               axis=AXIS, event_ref="E7")
    assert ev.binding_kinds == {"R": "first-break"}
    ref.add_transition(10, STATUS_BROKEN, info_time=t_ev, event_ref="E7",
                       axis=AXIS)
    replay = task_s2_event_binding(10, 110.0, {"C": [ref]}, 10,
                                   event_time=t_ev, axis=AXIS, event_ref="E7")
    assert replay.binding_kinds == {"R": "first-break"}   # stable
    with pytest.raises(ValueError, match="identity"):
        task_s2_event_binding(10, 110.0, {"C": [ref]}, 10, event_time=t_ev,
                              axis=AXIS)                  # no identity


def test_f2_event_phase_only_change_is_a_computed_change():
    """Audit F: an event-phase-only change produced an EMPTY
    computed_changes list.  Every recomputation whose event_phase moved
    records that move explicitly."""
    rep = _rep()
    crossed = _pt("R1", rep, "high", 1, 100.0, 2)
    far = _pt("R2", rep, "high", 1, 999.0, 2)      # never crossed
    t_ev = T0 + timedelta(minutes=10)
    ev = task_s2_event_binding(10, 110.0, {"C": [crossed, far]}, 10,
                               event_time=t_ev, axis=AXIS, event_ref="E1")
    led = InterpretationLedger()
    uid = led.record(ev, payload={
        "kind": "T-S2", "event_bar": 10, "close_price": 110.0,
        "refs_by_view": {"C": [crossed, far]}, "event_time": t_ev,
        "event_ref": "E1", "axis": AXIS})
    # an INDEPENDENT earlier event breaks the far (uncrossed) ref: the
    # binding set is unchanged, but the PRE/EVENT/POST phase map moves
    far.add_transition(4, STATUS_BROKEN,
                       info_time=T0 + timedelta(minutes=4),
                       event_ref="E0", axis=AXIS)
    led.propagate(10, ["R2"], update_time=t_ev, axis=AXIS)
    v2 = led.versions[uid][-1]
    assert v2["version"] == 2
    diffs = v2["computed_changes"]
    assert any(d.get("field") == "event_phase" for d in diffs), diffs
    # the phase diff is explicit and bounded
    ph = [d for d in diffs if d.get("field") == "event_phase"][0]
    assert ph["n_changed"] >= 1


# =========================================================================
# F3 — policy provenance
# =========================================================================

def test_f3_policy_snapshots_immutable_to_nested_mutation():
    """Audit F: mutating a nested value changed an already-recorded policy
    snapshot without a version change.  Registry values and snapshots are
    DEEP copies: nested mutation of a returned object changes nothing."""
    pol = PolicyRegistry()
    pol.register("P-NEST", "nested", {"want": "down", "opts": [1, 2]})
    snap = pol.snapshot_of("P-NEST")
    got = pol.get("P-NEST")
    snap["value"]["want"] = "MUTATED"
    snap["value"]["opts"].append(99)
    got["value"]["want"] = "MUTATED2"
    live = pol.snapshot_of("P-NEST")
    assert live["value"] == {"want": "down", "opts": [1, 2]}
    assert live["version"] == 1
    # a result recorded BEFORE the mutation keeps its own exact meaning
    rep = _rep()
    p = _pt("L", rep, "low", 1, 5.0, 2)
    lg = _lg("g", rep, "L", "H", "up", 1, 3, 5.0, 9.0, 3)
    pol.register("P-ORIGIN", "origin", {"role": "origin-of-last-confirmed-leg"})
    r = task_s1_structural_reference([p], [lg], 5, rep,
                                     "origin-of-last-confirmed-leg", pol,
                                     "P-ORIGIN",
                                     decision_time=T0 + timedelta(minutes=5),
                                     axis=AXIS)
    r.policy_snapshots["P-ORIGIN"]["value"]["role"] = "MUTATED3"
    assert pol.snapshot_of("P-ORIGIN")["value"] == {
        "role": "origin-of-last-confirmed-leg"}


def test_f3_t3_effective_policy_contradiction_and_snapshot():
    """Audit F: a T-S3 call used a direction condition that disagreed with
    its stored policy snapshot.  Structured contradictions are REJECTED;
    the snapshot records the EFFECTIVE condition AND the registered form."""
    rep_c, rep_f = _rep("C"), _rep("F")
    pol = PolicyRegistry()
    pol.register("P-CONTINUATION", "cont", ("direction", "up"))
    coarse = _lg("cg", rep_c, "a", "b", "up", 0, 10, 0.0, 100.0, 10)
    fine = _lg("fg", rep_f, "x", "y", "down", 2, 4, 80.0, 20.0, 4)
    with pytest.raises(ValueError, match="contradiction"):
        task_s3_entry_leg(coarse, [fine], 20, rep_f,
                          continuation_condition=("direction", "down"),
                          policy=pol,
                          decision_time=T0 + timedelta(minutes=20), axis=AXIS)
    # agreeing structured policy: the snapshot shows the EFFECTIVE value
    pol.register("P-CONTINUATION", "cont", ("direction", "down"))
    r = task_s3_entry_leg(coarse, [fine], 20, rep_f,
                          continuation_condition=("direction", "down"),
                          policy=pol,
                          decision_time=T0 + timedelta(minutes=20), axis=AXIS)
    snap = r.policy_snapshots["P-CONTINUATION"]
    assert snap["value"] == ("direction", "down")       # effective
    assert snap["registered_value"] == ("direction", "down")
    assert snap["version"] == 2
    # descriptive registered form: both forms preserved in the snapshot
    pol.register("P-CONTINUATION", "cont", "down-legs-in-up-leg")
    r2 = task_s3_entry_leg(coarse, [fine], 20, rep_f,
                           continuation_condition=("direction", "down"),
                           policy=pol,
                           decision_time=T0 + timedelta(minutes=20), axis=AXIS)
    snap2 = r2.policy_snapshots["P-CONTINUATION"]
    assert snap2["value"] == ("direction", "down")      # effective governs
    assert snap2["registered_value"] == "down-legs-in-up-leg"


# =========================================================================
# F4 — dependency coverage reaches descendants
# =========================================================================

def test_f4_unrecomputable_intermediate_marks_descendants_stale():
    """Audit F: A->B->C with B non-recomputable left B and C at version 1
    and identified only B.  Now C is marked STALE/BLOCKED downstream of B —
    a dependent is never silently kept as current against a stale upstream."""
    rep = _rep()
    pol = PolicyRegistry()
    pol.register("P-ORIGIN", "origin", "origin-of-last-confirmed-leg")
    a_pts = [_pt("A_root", rep, "low", 10, 10.0, 12),
             _pt("A_alt", rep, "high", 20, 40.0, 22)]
    a_legs = [_lg("A_leg", rep, "A_root", "A_alt", "up", 10, 20, 10.0, 40.0, 22)]
    rA = task_s1_structural_reference(a_pts, a_legs, 25, rep,
                                      "origin-of-last-confirmed-leg", pol,
                                      "P-ORIGIN",
                                      decision_time=T0 + timedelta(minutes=25),
                                      axis=AXIS)
    b_pts = [_pt("B_root", rep, "low", 10, 10.0, 12)]
    rB = task_s1_structural_reference(b_pts, [], 25, rep,
                                      "last-confirmed-extreme", pol, None,
                                      decision_time=T0 + timedelta(minutes=25),
                                      axis=AXIS)
    rC = task_s5_falsifier(
        [{"interpretation": "I", "view": "C", "role": "last-confirmed-extreme",
          "side": "low"}], b_pts, [], 25,
        decision_time=T0 + timedelta(minutes=25), axis=AXIS)
    led = InterpretationLedger()
    uid_a = led.record(rA, payload={"kind": "T-S1", "points": a_pts,
                                    "legs": a_legs, "rep": rep,
                                    "role": "origin-of-last-confirmed-leg",
                                    "policy": pol, "policy_id": "P-ORIGIN",
                                    "decision_time": T0 + timedelta(minutes=25),
                                    "axis": AXIS})
    uid_b = led.record(rB)        # NO payload: B cannot be recomputed
    led._result_deps[uid_b] = {uid_a}
    uid_c = led.record(rC, payload={"kind": "T-S5",
                                    "claims": [{"interpretation": "I",
                                                "view": "C",
                                                "role": "last-confirmed-extreme",
                                                "side": "low"}],
                                    "points": b_pts, "legs": [],
                                    "decision_time": T0 + timedelta(minutes=25),
                                    "axis": AXIS})
    led._result_deps[uid_c] = {uid_b}      # C depends on B
    led.propagate(30, ["A_root"],
                  changed_states={"A_root": STATUS_BROKEN},
                  update_time=T0 + timedelta(minutes=30), axis=AXIS)
    kinds = {(e.get("uid"), e.get("kind")) for e in led.revisions}
    # B: explicitly marked stale (not silently left current)
    b_entries = [e for e in led.revisions
                 if e.get("uid") == uid_b and e.get("kind") == "recomputation"]
    assert b_entries and b_entries[-1].get("stale") is True
    # C: explicitly marked as a STALE DESCENDANT of B
    c_entries = [e for e in led.revisions
                 if e.get("uid") == uid_c and e.get("kind") == "stale-descendant"]
    assert c_entries, f"C not marked stale: {led.revisions}"
    assert uid_b in c_entries[-1]["stale_from"]
    snap = led.snapshot()
    assert snap["n_stale_results"] == 2
    assert uid_b in snap["stale_results"] and uid_c in snap["stale_results"]


# =========================================================================
# F5 — candidate rows carry durable lifecycle evidence
# =========================================================================

def test_f5_candidate_record_lifecycle_and_supersession():
    """Audit F: candidate rows lacked the transition sequence and an
    explicit superseded_by relation.  Every row now carries both."""
    rep = _rep()
    p = _pt("P", rep, "high", 5, 50.0, 10, status=STATUS_SUPERSEDED)
    p.superseded_by = "Q"
    p.add_transition(5, STATUS_PROVISIONAL,
                     info_time=T0 + timedelta(minutes=5), axis=AXIS)
    p.add_transition(8, STATUS_SUPERSEDED, info_time=T0 + timedelta(minutes=8),
                     by="Q", axis=AXIS)
    row = candidate_record(p, task_id="T-S1_origin", run_id="r", boundary="B",
                           decision_bar=10, decision_time=T0 + timedelta(minutes=10),
                           eligible=False, selected=False,
                           task_detail={"binding_kind": "first-break"})
    assert row["superseded_by"] == "Q"
    assert [t["status"] for t in row["status_transitions"]] == [
        STATUS_PROVISIONAL, STATUS_SUPERSEDED]
    assert row["status_transitions"][1]["by"] == "Q"
    assert row["status_transitions"][0]["info_time"] is not None
    assert row["task_detail"] == {"binding_kind": "first-break"}
    assert row["initial_status"] == STATUS_SUPERSEDED


# =========================================================================
# F6 — atomic artifacts / clean output directory
# =========================================================================

def test_f6_atomic_write_failure_leaves_no_artifacts(tmp_path):
    """Audit F: a serialization failure left a truncated gzip beside seeded
    stale files.  Now the failure leaves NO target and NO temp residue."""
    targets = {"experiment_record_v2.json": {"ok": 1},
               "candidate_ledger_v1.jsonl.gz": ("jsonl.gz", [{"a": 1}]),
               "propagation_log_v1.jsonl": ("jsonl", [{"b": 2}]),
               "experiment_manifest_v1.json": {"m": 1},
               "REPRODUCE.md": "# repro"}
    class _Boom:
        def __str__(self):
            raise RuntimeError("serialization boom")

    bad = dict(targets)
    bad["experiment_record_v2.json"] = {"boom": _Boom()}   # fails to serialize
    with pytest.raises(RuntimeError, match="boom"):
        write_run_artifacts(tmp_path, bad)
    for name in targets:
        assert not (tmp_path / name).exists(), f"{name} left behind"
    assert list(tmp_path.iterdir()) == [], "temp residue left behind"


def test_f6_refuses_stale_output_dir_and_commits_cleanly(tmp_path):
    """A run never mixes its outputs with seeded/stale files; the clean
    commit writes every listed target completely (gzip is readable)."""
    targets = {"experiment_record_v2.json": {"ok": 1},
               "candidate_ledger_v1.jsonl.gz": ("jsonl.gz", [{"a": 1}, {"a": 2}]),
               "propagation_log_v1.jsonl": ("jsonl", [{"b": 2}]),
               "experiment_manifest_v1.json": {"m": 1},
               "REPRODUCE.md": "# repro"}
    (tmp_path / "experiment_record_v2.json").write_text("SEEDED STALE")
    with pytest.raises(ArtifactWriteError, match="stale"):
        write_run_artifacts(tmp_path, targets)
    assert (tmp_path / "experiment_record_v2.json").read_text() == "SEEDED STALE"
    clean = tmp_path / "clean"
    hashes = write_run_artifacts(clean, targets)
    assert set(hashes) == set(targets)
    with gzip.open(clean / "candidate_ledger_v1.jsonl.gz", "rt") as fh:
        rows = [json.loads(l) for l in fh]
    assert rows == [{"a": 1}, {"a": 2}]                    # complete gzip
    assert (clean / "propagation_log_v1.jsonl").read_text().splitlines() == [
        json.dumps({"b": 2})]
    assert not list(clean.glob("*.tmp"))
    # require_clean_out_dir is the explicit gate behind the refusal
    with pytest.raises(ArtifactWriteError):
        require_clean_out_dir(clean, targets.keys())


# =========================================================================
# complete path — observations -> ... -> persisted result; future invariance
# =========================================================================

def test_complete_path_future_data_invariance():
    """Market observations -> candidates -> historical state -> task
    selection -> event binding -> dependency update -> persisted result;
    adding FUTURE data must not change any earlier output."""
    n = 40
    closes = pd.Series(100.0, index=pd.date_range(T0, periods=n, freq="1min"))
    highs = closes + 2.0
    lows = closes - 2.0
    highs.iloc[10] = 110.0
    lows.iloc[20] = 90.0
    bars = pd.DataFrame({"open": closes, "high": highs, "low": lows,
                         "close": closes}, index=closes.index)
    cutoff = 30

    def _pipeline(bars_df):
        pts = fk_turning_points(bars_df.iloc[:cutoff + 1], 2, _rep(),
                                axis=AXIS)
        legs = build_legs(pts, _rep())
        pol = PolicyRegistry()
        pol.register("P-ORIGIN", "origin", "origin-of-last-confirmed-leg")
        r1 = task_s1_structural_reference(
            pts, legs, cutoff, _rep(), "origin-of-last-confirmed-leg", pol,
            "P-ORIGIN", decision_time=T0 + timedelta(minutes=cutoff),
            axis=AXIS)
        led = InterpretationLedger()
        led.record(r1, payload={"kind": "T-S1", "points": pts, "legs": legs,
                                "rep": _rep(),
                                "role": "origin-of-last-confirmed-leg",
                                "policy": pol, "policy_id": "P-ORIGIN",
                                "decision_time": T0 + timedelta(minutes=cutoff),
                                "axis": AXIS})
        ref = next((p for p in pts if p.candidate_id == r1.selected_id), None)
        if ref is not None:
            t_ev = T0 + timedelta(minutes=28)
            ev = task_s2_event_binding(
                28, 115.0, {"C": [ref]}, 28, event_time=t_ev, axis=AXIS,
                event_ref="E28")
            led.record_event(28, "binding", "close 115", ev.survivors,
                             event_time=t_ev, event_ref="E28")
            led.propagate(28, [ref.candidate_id],
                          changed_states={ref.candidate_id: STATUS_BROKEN},
                          update_time=t_ev, event_ref="E28", axis=AXIS)
        rows = [candidate_record(p, task_id="T-S1_origin", run_id="P",
                                 boundary="B", decision_bar=cutoff,
                                 decision_time=T0 + timedelta(minutes=cutoff),
                                 eligible=(p.candidate_id in r1.survivors),
                                 selected=(p.candidate_id == r1.selected_id))
                for p in pts]
        return {
            "selected": r1.selected_id,
            "status": r1.status,
            "rows": rows,
            "revisions": [
                {k: v for k, v in e.items() if k != "info_time"}
                for e in led.revisions],
            "versions": {u: [(vv["version"], vv.get("computed_changes"))
                             for vv in led.versions[u]] for u in led.versions},
        }

    early = _pipeline(bars)
    later = _pipeline(bars)          # same prefix: identical
    assert early == later
    # extend with FUTURE bars beyond the cutoff: earlier outputs unchanged
    bars2 = bars.copy()
    bars2.iloc[35:, bars2.columns.get_loc("high")] = 140.0
    bars2.iloc[35:, bars2.columns.get_loc("low")] = 60.0
    future = _pipeline(bars2)
    assert future == early
