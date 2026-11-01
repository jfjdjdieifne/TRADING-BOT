"""Lifecycle tests for the contextual market-analysis engine.

Covers the task's required behaviors:
  T1  append-after-T invariance (evidence appended after T must not
      change the analysis produced at T);
  T2  a forecast recorded before its condition + a later observation
      updates it WITHOUT rewriting the prior record;
  T3  a condition already observed at startup is never claimed as a
      pre-event prediction;
  T4  snapshot resume without leaking data past the saved boundary;
  T5  midstream start = reconstructed mode with missing-history limits;
  T6  position absent is preserved (never inferred);
  T7  competing interpretations remain distinct;
  T8  unresolved references carry an explicit reason (precise reference
      OR a specific unresolved reason — never a vague wait);
  T9  machine-detectable conditions carry operational and source/policy
      definitions;
  T10 provenance survives recomputation; stale recomputes are never
      counted as success;
  T11 off-grid as-of is invalid input (fail closed).
"""

import json

import pandas as pd
import pytest

from trading_system.research.contextual_selection.analysis_lifecycle import (
    AnalysisEngine,
    CLAIM_CLASSES,
    CLAIM_DIRECT,
    CLAIM_ENGINEERING,
    CLAIM_HYPOTHESIS,
    CLAIM_PARAPHRASE,
    CLAIM_UNSUPPORTED,
    MODE_LIVE,
    MODE_RECONSTRUCTED,
    STATE_ALREADY_OBSERVED,
    STATE_INSUFFICIENT,
    STATE_INVALIDATED,
    STATE_PENDING,
    SOURCE_REGISTER,
)
from trading_system.research.contextual_selection.csm import (
    InterpretationLedger,
)


# --------------------------------------------------------------------- #
# synthetic scenes (deterministic; no market claim)                      #
# --------------------------------------------------------------------- #
def mk_bars(closes):
    """4h bars with distinct wicks (FK uniqueness holds)."""
    idx = pd.date_range("2025-01-01 04:00", periods=len(closes), freq="4h",
                        tz="UTC")
    opens = [closes[0]] + closes[:-1]
    hi = [max(o, c) + 5 + (i % 3)
          for i, (o, c) in enumerate(zip(opens, closes))]
    lo = [min(o, c) - 5 - ((i + 1) % 3)
          for i, (o, c) in enumerate(zip(opens, closes))]
    return pd.DataFrame({"open": opens, "high": hi, "low": lo,
                         "close": closes, "volume": 1.0}, index=idx)


# fall to a V low (bar 4), rise to H (bar 8), pull back (bars 9-10),
# rise again (11-14), crash (bar 15 closes below the V low), settle.
PATH_VIOLATION = [100, 92, 84, 78, 70,
                  78, 84, 88, 92,
                  88, 86, 90, 94, 98, 102,
                  60, 62, 64, 66]


def frames_of(closes, run_frames=None):
    b4 = mk_bars(closes)
    frames = {"4h": b4, "1h": b4, "15m": b4}
    return frames, b4


def engine_of(closes, run_id="t", ledger=None):
    frames, b4 = frames_of(closes)
    eng = AnalysisEngine(run_id=run_id, frames=frames, k=2,
                         ledger=ledger)
    return eng, b4


# bars used in the scene (indices into PATH_VIOLATION):
#   T1 = bar 10  -> reference = the V low, forecast PENDING
#   T2 = bar 15  -> crash closes below the V low -> condition observed
BAR_T1 = 10
BAR_T2 = 15


# --------------------------------------------------------------------- #
# T1: append-after-T invariance                                          #
# --------------------------------------------------------------------- #
def test_append_after_t_invariance():
    eng_a, b4a = engine_of(PATH_VIOLATION[:BAR_T1 + 1], run_id="inv")
    rec_a = eng_a.analyze(b4a.index[BAR_T1])

    eng_b, b4b = engine_of(PATH_VIOLATION, run_id="inv")
    rec_b = eng_b.analyze(b4b.index[BAR_T1])

    ja = json.dumps(rec_a.to_record(), sort_keys=True, default=str)
    jb = json.dumps(rec_b.to_record(), sort_keys=True, default=str)
    assert ja == jb, ("evidence appended after T changed the analysis "
                      "produced at T")


# --------------------------------------------------------------------- #
# T2: forecast BEFORE its condition; revision never rewrites history     #
# --------------------------------------------------------------------- #
def test_forecast_recorded_before_condition_then_immutable_revision():
    eng, b4 = engine_of(PATH_VIOLATION, run_id="fc")
    r1 = eng.analyze(b4.index[BAR_T1])

    # recorded BEFORE the condition
    assert r1.lifecycle_state == STATE_PENDING
    assert len(r1.forecasts) == 1
    f1 = r1.forecasts[0]
    assert f1.status == "pending"
    assert f1.observed_before_record is False
    v1 = eng.forecast_versions[f1.forecast_id][0]
    v1_json = json.dumps(v1.to_record(), sort_keys=True, default=str)

    # later observation (crash) updates it
    r2 = eng.analyze(b4.index[BAR_T2])
    assert r2.lifecycle_state == STATE_INVALIDATED
    assert r2.revision_reason and f1.forecast_id in r2.revision_reason

    versions = eng.forecast_versions[f1.forecast_id]
    assert len(versions) == 2
    assert versions[-1].status == "condition_observed"
    assert versions[-1].revises == f"{f1.forecast_id}@v1"
    # the prior version is NOT rewritten
    v1_after = json.dumps(versions[0].to_record(), sort_keys=True,
                          default=str)
    assert v1_after == v1_json
    assert versions[0].status == "pending"


# --------------------------------------------------------------------- #
# T3: already-observed at startup is not a pre-event prediction          #
# --------------------------------------------------------------------- #
def test_condition_already_observed_at_startup_not_predicted():
    eng, b4 = engine_of(PATH_VIOLATION, run_id="ao")
    # FIRST analysis happens only AFTER the violation (bar 15 close 60)
    r = eng.analyze(b4.index[BAR_T2])
    assert r.observation_mode == MODE_RECONSTRUCTED

    observed = [f for f in r.forecasts
                if f.status in ("already_observed", "condition_observed")]
    assert observed, "the pre-existing condition must be visible"
    for f in observed:
        # never claimed as a pre-event prediction
        assert f.observed_before_record is True
        assert f.status != "pending"
        rec = f.to_record()
        assert rec["observed_before_record"] is True
    assert r.lifecycle_state in (STATE_ALREADY_OBSERVED,
                                 STATE_INVALIDATED)


# --------------------------------------------------------------------- #
# T4: snapshot resume without leakage past the saved boundary            #
# --------------------------------------------------------------------- #
def test_snapshot_resume_no_leakage(tmp_path):
    eng, b4 = engine_of(PATH_VIOLATION, run_id="snap")
    r1 = eng.analyze(b4.index[BAR_T1])
    snap = eng.snapshot_state()
    snap_path = tmp_path / "snap.json"
    snap_path.write_text(json.dumps(snap, default=str))

    # fresh process: resumes from the snapshot only
    eng2, _ = engine_of(PATH_VIOLATION, run_id="snap")
    eng2._load_snapshot(str(snap_path))
    assert eng2.snapshot_boundary == str(r1.as_of_time)
    # restored state contains nothing past the saved boundary
    for versions in eng2.forecast_versions.values():
        for v in versions:
            assert pd.Timestamp(v.asof_time) <= r1.as_of_time
    assert all(pd.Timestamp(rd["as_of_time"]) <= r1.as_of_time
               for rd in eng2._restored_records)

    # revising with NEW causal evidence keeps the prior version intact
    r2 = eng2.analyze(b4.index[BAR_T2])
    fid = r1.forecasts[0].forecast_id
    versions = eng2.forecast_versions[fid]
    assert versions[0].status == "pending"
    assert versions[-1].status == "condition_observed"
    assert versions[-1].revises == f"{fid}@v1"
    # the analysis version continues the restored history
    assert r2.analysis_version == 2
    assert r2.revises == f"{r2.analysis_id}@v1"
    assert r2.revision_reason


# --------------------------------------------------------------------- #
# T5: midstream start is reconstructed with missing-history limits       #
# --------------------------------------------------------------------- #
def test_midstream_reconstructed_records_limits():
    eng, b4 = engine_of(PATH_VIOLATION, run_id="mid")
    r1 = eng.analyze(b4.index[BAR_T1])
    assert r1.observation_mode == MODE_RECONSTRUCTED
    assert any("not recorded by this engine" in lim or
               "RECONSTRUCTED" in lim for lim in r1.limitations)
    r2 = eng.analyze(b4.index[BAR_T2])
    assert r2.observation_mode == MODE_LIVE


# --------------------------------------------------------------------- #
# T6: position absent is preserved (never inferred)                      #
# --------------------------------------------------------------------- #
def test_position_absent_never_inferred():
    eng, b4 = engine_of(PATH_VIOLATION, run_id="pos")
    for bar in (BAR_T1, BAR_T2):
        r = eng.analyze(b4.index[bar])
        assert r.position_status == "absent"
        assert "inferred from price structure" in r.position_note
        rec = r.to_record()
        pos_keys = [k for k in rec if "position" in k]
        assert set(pos_keys) <= {"position_status", "position_note"}


# --------------------------------------------------------------------- #
# T7: competing interpretations remain distinct                          #
# --------------------------------------------------------------------- #
def test_competing_interpretations_distinct():
    eng, b4 = engine_of(PATH_VIOLATION, run_id="comp")
    r = eng.analyze(b4.index[BAR_T1])
    by_id = {i.interpretation_id: i for i in r.interpretations}
    assert "I-primary" in by_id and "I-alt" in by_id
    a, b = by_id["I-primary"], by_id["I-alt"]
    assert a.description != b.description
    assert a.would_be_supported_by != b.would_be_supported_by
    assert "I-alt" in a.alternative_ids
    assert "I-primary" in b.alternative_ids
    assert a.claim_class == CLAIM_ENGINEERING
    assert b.claim_class == CLAIM_HYPOTHESIS


# --------------------------------------------------------------------- #
# T8: precise reference OR an explicit unresolved reason                 #
# --------------------------------------------------------------------- #
def test_unresolved_reference_has_specific_reason():
    # scene with no completed task-scale leg yet (too little history)
    eng, b4 = engine_of(PATH_VIOLATION, run_id="unres")
    r = eng.analyze(b4.index[2])     # before any leg completes
    assert r.lifecycle_state == STATE_INSUFFICIENT
    ref = r.reference_status
    assert ref["status"] == "unresolved"
    assert ref["reason"] and "leg" in ref["reason"]
    assert "wait" not in ref["reason"].lower() or "awaited" not in \
        ref["reason"].lower()
    # precise-reference case: a selected reference is an exact id
    r2 = eng.analyze(b4.index[BAR_T1])
    ref2 = r2.reference_status
    assert ref2["status"] == "selected"
    assert ref2["selected"] and ref2["selected"].startswith("PTC:")


# --------------------------------------------------------------------- #
# T9: machine-detectable conditions carry operational + source defs      #
# --------------------------------------------------------------------- #
def test_condition_definitions_operational_and_sourced():
    eng, b4 = engine_of(PATH_VIOLATION, run_id="cond")
    r = eng.analyze(b4.index[BAR_T1])
    for f in r.forecasts:
        c = f.condition
        assert c.executable is True
        assert c.detector == "sp03-close-violation"
        assert "CLOSE" in c.definition and "SP-03" in c.definition
        assert c.basis and "SRS-" in c.basis
        assert c.claim_class in CLAIM_CLASSES
        assert f.if_event and f.then_effect
        assert f.next_observation
        assert f.status in ("pending", "already_observed",
                            "condition_observed")
        for p in f.provenance:
            assert p.startswith("SRS-")
    # source register: unverified material is marked and never attributed
    for s in SOURCE_REGISTER:
        assert s.claim_class in CLAIM_CLASSES
        if s.claim_class == CLAIM_UNSUPPORTED:
            assert ("NOT verified" in s.verification_status or
                    "partial" in s.verification_status or
                    "not available" in s.verification_status)
    classes = {s.source_id: s.claim_class for s in SOURCE_REGISTER}
    assert classes["SRS-CLAIM-SEM"] == CLAIM_DIRECT
    assert classes["SRS-FK"] == CLAIM_PARAPHRASE
    assert classes["SRS-ICT-M22-E3"] == CLAIM_UNSUPPORTED


# --------------------------------------------------------------------- #
# T10: provenance survives recomputation; stale never success            #
# --------------------------------------------------------------------- #
def test_provenance_survives_recomputation_and_stale_never_success():
    ledger = InterpretationLedger()
    eng, b4 = engine_of(PATH_VIOLATION, run_id="rec", ledger=ledger)
    r = eng.analyze(b4.index[BAR_T1])

    uid1, uid2 = r.ledger_uids
    res1 = ledger.results[0]
    dep = next((d for d in res1.dependencies
                if d.startswith("PTC") or d.startswith("C:")), None)
    assert dep, "the recorded result must carry real dependencies"

    log = ledger.propagate(
        update_bar=r.as_of_bar + 1, changed_ids=[dep],
        update_time=b4.index[r.as_of_bar + 1], axis=eng.axis)
    by_uid = {}
    for e in log:
        by_uid.setdefault(e.get("uid"), []).append(e)

    # the expert reference selection REALLY recomputes (handler exists)
    entries = by_uid.get(uid1, [])
    assert entries, "no propagation reached the dependent result"
    ok = [e for e in entries if e.get("kind") == "recomputation"
          and not e.get("stale")]
    assert ok, f"expected real recomputation, got {entries}"
    # provenance survives
    new_version = ledger.versions[uid1][-1]
    new_res = new_version["result"]
    assert list(new_res.provenance) == list(res1.provenance)
    assert new_version["version"] >= 2

    # the falsifier result has NO recompute handler: any dependent
    # recompute of it is stale and never counted as success
    s5_entries = by_uid.get(uid2, [])
    for e in s5_entries:
        if e.get("kind") == "recomputation":
            assert e.get("stale") is not True or \
                e.get("stale_reason"), \
                "a stale recompute must never look successful"


# --------------------------------------------------------------------- #
# T11: off-grid as-of is invalid input (fail closed)                     #
# --------------------------------------------------------------------- #
def test_offgrid_asof_rejected():
    eng, b4 = engine_of(PATH_VIOLATION, run_id="off")
    with pytest.raises(ValueError):
        eng.analyze(pd.Timestamp("2025-01-02 05:13:00", tz="UTC"))


# --------------------------------------------------------------------- #
# extra guards (claims / forbidden outputs)                              #
# --------------------------------------------------------------------- #
def test_no_probabilities_no_expiry_no_signal():
    eng, b4 = engine_of(PATH_VIOLATION, run_id="guard")
    r = eng.analyze(b4.index[BAR_T1])
    rec = json.dumps(r.to_record(), default=str).lower()
    for token in ("buy signal", "sell signal", "confidence",
                  "win rate", "profit"):
        assert token not in rec
    assert r.selection_quality == "NOT_ESTABLISHED"
    assert "no probabilities" in " ".join(r.limitations).lower()
