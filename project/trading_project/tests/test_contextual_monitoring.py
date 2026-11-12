"""Focused tests for the continuous monitoring layer and the causal
step-by-step replay (task-required coverage):

  T1  appending/changing future data cannot change the saved analysis
      at T;
  T2  step-by-step replay does not expose future observations to the
      engine;
  T3  a new observation revises an interpretation without rewriting the
      previous version;
  T4  an observation that changes no dependencies creates no fabricated
      market change;
  T5  a condition already observed at startup is not called a prior
      prediction;
  T6  a saved state resumes in a FRESH PROCESS with the same causal
      result;
  T7  same-bar ordering remains unresolved when OHLC cannot determine
      it;
  T8  a swing/higher-timeframe fact is not available before its actual
      confirmation/completion;
  T9  the same local shape in different broader contexts can lead to
      different interpretations when the evidence supports it;
  T10 changed absolute price scale or irrelevant candle-shape details do
      not alone determine the interpretation;
  T11 missing order-book, position, or source information is reported
      honestly;
  T12 real ledger propagation updates actual dependencies.
"""

import json
import os
import subprocess
import sys
import textwrap

import pandas as pd
import pytest

from trading_system.research.contextual_selection.analysis_lifecycle import (
    AnalysisEngine,
)
from trading_system.research.contextual_selection.csm import (
    InterpretationLedger,
    Representation,
)
from trading_system.research.contextual_selection.monitoring import (
    CONCEPT_REGISTER,
    DATA_CAPABILITIES,
    LIVE_FEED_STATUS,
    LiveFeedAdapter,
    MonitoringLoop,
    ReplayObservationStream,
)
from trading_system.research.information_time import (
    INFORMATION_KEY_VERSION,
    InformationKey,
    InformationPhase,
)


# --------------------------------------------------------------------- #
# synthetic source rows: 4 one-hour rows per 4h scene bar                #
# --------------------------------------------------------------------- #
def synth_rows(closes, wick=5.0):
    """Expand a 4h close path into 1h source rows whose 4h aggregation
    reproduces the verified scene structure (open/high/low/close)."""
    rows = []
    t0 = pd.Timestamp("2025-01-01 00:00", tz="UTC")
    for i, c in enumerate(closes):
        o = closes[i - 1] if i else c
        scale = wick / 5.0
        hi = max(o, c) + wick + (i % 3) * scale
        lo = min(o, c) - wick - ((i + 1) % 3) * scale
        for s in range(4):
            f0, f1 = s / 4, (s + 1) / 4
            ro = o + (c - o) * f0
            rc = o + (c - o) * f1
            rh = max(ro, rc)
            rl = min(ro, rc)
            if s == 1:
                rh = hi
            if s == 2:
                rl = lo
            rows.append({"timestamp": t0 + pd.Timedelta(hours=4 * i + s),
                         "open": ro, "high": rh, "low": rl, "close": rc,
                         "volume": 1.0})
    df = pd.DataFrame(rows).set_index("timestamp")
    return df


def frames_builder(rows):
    r4 = rows.resample("4h").agg({"open": "first", "high": "max",
                                 "low": "min", "close": "last",
                                 "volume": "sum"}).dropna(
        subset=["open"])
    r4.index = r4.index + pd.Timedelta(hours=4)   # completion labels
    return {"4h": r4, "1h": rows, "15m": rows}


def engine_factory(frames):
    return AnalysisEngine(run_id="mon", frames=frames, k=2)


def make_loop(closes, **kw):
    rows = synth_rows(closes)
    stream = ReplayObservationStream(rows, timeline_id="TEST_1h",
                                     dataset_identity="test-synth")
    grid = frames_builder(rows)   # time GRID metadata only
    return MonitoringLoop(stream=stream, frames_builder=frames_builder,
                          engine_factory=engine_factory, task_scale="4h",
                          grid_frames=grid, **kw), rows


# V low (bar 4) -> up leg 4->8 -> pullback -> rise -> entry (bar 14
# close 99 > 95) -> crash (bar 15 close 52 < ref 55)
PATH = [80, 78, 74, 70, 62, 70, 76, 82, 88, 84, 82, 86, 90, 94,
        99, 52, 54, 56, 58]


# --------------------------------------------------------------------- #
# T1: future data cannot change the saved analysis at T                  #
# --------------------------------------------------------------------- #
def test_future_data_cannot_change_saved_analysis(tmp_path):
    loop_full, rows_full = make_loop(PATH)
    loop_full.run_to(pd.Timestamp("2025-01-05 00:00", tz="UTC"))
    state_path = tmp_path / "state.json"
    loop_full.save_state(str(state_path))
    snap_a = json.dumps(loop_full.state_dict()["engine_snapshot"],
                        sort_keys=True, default=str)

    # a SHORTER file that ends exactly at T
    cut = loop_full.stream.position + 1
    rows_short = rows_full.iloc[:cut]
    stream_s = ReplayObservationStream(rows_short, timeline_id="TEST_1h",
                                       dataset_identity="test-synth")
    loop_short = MonitoringLoop(stream=stream_s,
                                frames_builder=frames_builder,
                                engine_factory=engine_factory,
                                task_scale="4h")
    loop_short.run_to(pd.Timestamp("2025-01-05 00:00", tz="UTC"))
    snap_b = json.dumps(loop_short.state_dict()["engine_snapshot"],
                        sort_keys=True, default=str)
    assert snap_a == snap_b, "future rows changed the saved analysis at T"


# --------------------------------------------------------------------- #
# T2: the engine never sees future observations                          #
# --------------------------------------------------------------------- #
def test_step_replay_never_exposes_future():
    loop, rows = make_loop(PATH)
    seen_max = []
    while not loop.stream.exhausted:
        loop.step_observation()
        pref = loop.stream.prefix_rows()
        tail = loop.stream.tail_rows()
        seen_max.append(pd.Timestamp(pref.index[-1]))
        # the prefix contains nothing after the cursor and the tail
        # (future) is never part of it
        assert pd.Timestamp(pref.index[-1]) == loop.stream.current_time
        if len(tail):
            assert pd.Timestamp(tail.index[0]) > loop.stream.current_time
    # strictly increasing exposure
    assert all(b >= a for a, b in zip(seen_max, seen_max[1:]))
    # the boundary record equals a batch analysis built WITHOUT future
    # rows (same causal prefix)
    rec_stream = loop.last_record
    rows_short = rows.iloc[: loop.stream.position + 1]
    stream_s = ReplayObservationStream(rows_short, timeline_id="TEST_1h",
                                       dataset_identity="test-synth")
    loop2 = MonitoringLoop(stream=stream_s, frames_builder=frames_builder,
                           engine_factory=engine_factory, task_scale="4h")
    while not loop2.stream.exhausted:
        loop2.step_observation()
    assert json.dumps(rec_stream.to_record(), sort_keys=True,
                      default=str) == json.dumps(
        loop2.last_record.to_record(), sort_keys=True, default=str)


# --------------------------------------------------------------------- #
# T3: revision without rewriting the previous version                   #
# --------------------------------------------------------------------- #
def test_new_observation_revises_without_rewriting():
    loop, rows = make_loop(PATH)
    loop.run_to(pd.Timestamp("2025-01-05 00:00", tz="UTC"))  # boundary 10
    r1 = loop.last_record
    v1 = loop.engine.forecast_versions[r1.forecasts[0].forecast_id][0]
    assert v1.status == "pending"
    v1_json = json.dumps(v1.to_record(), sort_keys=True, default=str)

    reports = loop.run_to(pd.Timestamp("2025-01-07 00:00", tz="UTC"))
    r2 = loop.last_record
    fid = r1.forecasts[0].forecast_id
    versions = loop.engine.forecast_versions[fid]
    assert versions[-1].status == "condition_observed"
    assert versions[-1].revises == f"{fid}@v1"
    # prior version untouched
    assert json.dumps(versions[0].to_record(), sort_keys=True,
                      default=str) == v1_json
    # the journal recorded WHAT changed, WHY, and WHICH evidence
    forecast_changes = [c for r in loop.journal for c in r["changes"]
                        if c["aspect"] == "forecast"]
    assert forecast_changes
    assert any("watched condition" in c["reason"] for c in
               forecast_changes)


# --------------------------------------------------------------------- #
# T4: no-change observations create no fabricated market change          #
# --------------------------------------------------------------------- #
def test_no_change_observation_creates_no_fabricated_change():
    loop, rows = make_loop(PATH)
    # first three observations live INSIDE the first (incomplete) 4h bar
    n_records_before = 0
    r = loop.step_observation()
    assert r.material_change is False
    assert "incomplete bars are never used" in r.no_revision_reason
    assert loop.engine is None            # no analysis ran at all
    r = loop.step_observation()
    assert r.material_change is False
    r = loop.step_observation()
    assert r.material_change is False
    assert loop.engine is None
    # the fourth observation completes the first 4h bar -> analysis runs
    r = loop.step_observation()
    assert r.trigger == "task-boundary"
    assert loop.engine is not None
    # and the boundary ALSO reports honestly when nothing interpretive
    # changed at a later boundary with no state movement
    loop.run_to(pd.Timestamp("2025-01-03 00:00", tz="UTC"))
    n = len(loop.engine.records)
    r = loop.step_observation()   # inside the next bar
    assert r.material_change is False
    assert len(loop.engine.records) == n   # no new record fabricated


# --------------------------------------------------------------------- #
# T5: already-observed at startup is not a prior prediction               #
# --------------------------------------------------------------------- #
def test_condition_already_observed_at_startup_not_predicted():
    # mid-move start: observations are available from the beginning, but
    # the loop's FIRST analysis happens only AFTER the watched condition
    # (the crash at scene bar 15, close 52) has already occurred
    rows = synth_rows(PATH)
    stream = ReplayObservationStream(rows, timeline_id="TEST_1h",
                                     dataset_identity="test-synth")
    loop = MonitoringLoop(stream=stream, frames_builder=frames_builder,
                          engine_factory=engine_factory, task_scale="4h")
    # consume WITHOUT analysis until the crash bar is fully observed
    target = pd.Timestamp("2025-01-03 16:00", tz="UTC")
    while True:
        rec = stream.next_observation()
        if rec is None or pd.Timestamp(rec["time"]) >= target:
            break
    r = loop.step_observation()          # first analyzed boundary
    rec = loop.last_record
    text = json.dumps(rec.to_record(), default=str).lower()
    # the pre-existing condition is identified as past
    assert ("already_observed" in text or "already observed" in text or
            r.lifecycle_state == "CONDITION_ALREADY_OBSERVED")
    for claim in ("we predicted", "predicted before", "pre-event "
                  "prediction was", "successful prediction"):
        assert claim not in text


# --------------------------------------------------------------------- #
# T6: fresh-process resume with the same causal result                   #
# --------------------------------------------------------------------- #
def test_saved_state_resumes_in_fresh_process(tmp_path):
    loop, rows = make_loop(PATH)
    loop.run_to(pd.Timestamp("2025-01-03 00:00", tz="UTC"))
    state_path = tmp_path / "state.json"
    rows_path = tmp_path / "rows.csv"
    loop.save_state(str(state_path))
    out_path = tmp_path / "resume_out.json"

    script = textwrap.dedent(f"""
        import json, sys
        sys.path.insert(0, {str(sys.path[0])!r})
        import pandas as pd
        from trading_system.research.contextual_selection.monitoring import (
            MonitoringLoop, ReplayObservationStream)
        from trading_system.research.contextual_selection.analysis_lifecycle import (
            AnalysisEngine)

        def frames_builder(rows):
            r4 = rows.resample("4h").agg({{"open": "first", "high": "max",
                                 "low": "min", "close": "last",
                                 "volume": "sum"}}).dropna(subset=["open"])
            r4.index = r4.index + pd.Timedelta(hours=4)
            return {{"4h": r4, "1h": rows, "15m": rows}}

        def engine_factory(frames):
            return AnalysisEngine(run_id="mon", frames=frames, k=2)

        rows = pd.read_csv({str(rows_path)!r}, parse_dates=["timestamp"],
                           index_col="timestamp")
        if rows.index.tz is None:
            rows.index = rows.index.tz_localize("UTC")
        stream = ReplayObservationStream(rows, timeline_id="TEST_1h",
                                         dataset_identity="test-synth")
        loop = MonitoringLoop.load_state(
            {str(state_path)!r}, stream=stream,
            frames_builder=frames_builder, engine_factory=engine_factory,
            task_scale="4h")
        before = json.dumps(loop.state_dict()["engine_snapshot"],
                            sort_keys=True, default=str)
        r = loop.step_completed_bar()
        with open({str(out_path)!r}, "w") as fh:
            json.dump({{"snapshot_at_resume": before,
                       "next_boundary": r.as_of,
                       "next_state": r.lifecycle_state,
                       "next_material": r.material_change}}, fh)
    """)
    rows.to_csv(rows_path)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = dict(os.environ,
               PYTHONPATH=os.pathsep.join([os.path.join(root, "src"),
                                           root]))
    proc = subprocess.run([sys.executable, "-c", script],
                          capture_output=True, text=True, env=env,
                          cwd=root)
    assert proc.returncode == 0, proc.stderr
    out = json.loads(out_path.read_text())
    # the fresh process restored the same snapshot...
    assert out["snapshot_at_resume"] == json.dumps(
        loop.state_dict()["engine_snapshot"], sort_keys=True, default=str)
    # ...and produced the same causal continuation as an in-process step
    r2 = loop.step_completed_bar()
    assert out["next_boundary"] == r2.as_of
    assert out["next_state"] == r2.lifecycle_state
    assert out["next_material"] == r2.material_change


# --------------------------------------------------------------------- #
# T7: same-bar ordering stays unresolved                                 #
# --------------------------------------------------------------------- #
def test_same_bar_ordering_unresolved():
    from trading_system.market_understanding.price_path import (
        PublishedOhlcBarFact,
        intrabar_path_metrics,
    )
    from trading_system.market_understanding.contracts import SchemaIdentity

    key = InformationKey(
        information_key_version=INFORMATION_KEY_VERSION,
        timeline_id="TEST_1h", bar_position=1,
        event_time_utc=pd.Timestamp("2025-01-01 01:00", tz="UTC"),
        information_phase=InformationPhase.COMPLETED_ROW_AVAILABLE,
        deterministic_sequence=1)
    fact = PublishedOhlcBarFact(
        open_price=10.0, high_price=12.0, low_price=8.0, close_price=11.0,
        availability_key=key, source_identity=SchemaIdentity("T", "V1"),
        dataset_identity="test", published_bar_record_ref="b1")
    metrics = intrabar_path_metrics(fact)
    # OHLC never reveals whether the high preceded the low
    vals = json.dumps({k: str(v) for k, v in metrics.items()})
    assert "AMBIGUOUS_INTRABAR_CHRONOLOGY" in vals or \
        "UNAVAILABLE" in vals

    # the stream never silently orders same-time input: a duplicate key
    # is rejected (fail closed), never sorted in
    rows = synth_rows(PATH)
    stream = ReplayObservationStream(rows, timeline_id="TEST_1h",
                                     dataset_identity="test-synth")
    stream.next_observation()
    rec = stream._row_dict(0)
    with pytest.raises(Exception):
        stream._validate_and_accept(rec)   # duplicate observation key


# --------------------------------------------------------------------- #
# T8: swing/HTF facts unavailable before confirmation/completion         #
# --------------------------------------------------------------------- #
def test_swing_and_htf_facts_not_available_before_confirmation():
    loop, rows = make_loop(PATH)
    # advance to the boundary at bar 2 (well before the bar-4 low and
    # bar-8 high are confirmable)
    loop.run_to(pd.Timestamp("2025-01-02 00:00", tz="UTC"))
    rec = loop.last_record
    ids = " ".join(f.fact_id for f in rec.structural_facts)
    # no leg spanning bar 4..8 may exist yet (its endpoints are not
    # confirmable with only 2 right bars)
    assert "2025-01-02T12:00" not in ids
    # a completed-bar availability fact is only reported for COMPLETED
    # bars: the count never exceeds the bars that have closed
    avail = [f for f in rec.structural_facts
             if f.kind == "derived-frame-availability"
             and f.inputs.get("scale") == "1h"]
    for f in avail:
        # exactly the completed source rows at that boundary (6 task
        # bars * 4 one-hour rows) — never more than available
        assert f.inputs["n_completed"] == 24


# --------------------------------------------------------------------- #
# T9: same local shape, different broader context                        #
# --------------------------------------------------------------------- #
def test_same_local_shape_different_context():
    # IDENTICAL local shape (the shared 3-bar tail) in different
    # broader contexts (different prefixes)
    tail = [90, 94, 99]
    scene_a = [80, 78, 74, 70, 62, 70, 76, 82, 88, 84, 82] + tail
    scene_b = [60, 58, 62, 66, 74, 82, 88, 84, 82, 78, 76] + tail
    assert scene_a[-3:] == scene_b[-3:]        # same local shape
    outs = []
    for scene in (scene_a, scene_b):
        loop, _ = make_loop(scene)
        loop.run_to(pd.Timestamp("2025-01-03 00:00", tz="UTC"))
        r = loop.last_record
        outs.append(json.dumps({
            "ref": r.reference_status.get("selected"),
            "state": r.lifecycle_state,
            "interp": [i.description for i in r.interpretations],
            "reason": r.reference_status.get("reason"),
        }, default=str, sort_keys=True))
    # the broader evidence supports a distinction and the interpretation
    # differs (nothing forces equality)
    assert outs[0] != outs[1]


# --------------------------------------------------------------------- #
# T10: scale / irrelevant shape details do not alone decide              #
# --------------------------------------------------------------------- #
def test_scale_and_irrelevant_shape_do_not_decide():
    def summary(closes, wick=5.0):
        rows = synth_rows(closes, wick=wick)
        stream = ReplayObservationStream(rows, timeline_id="TEST_1h",
                                         dataset_identity="test-synth")
        loop = MonitoringLoop(stream=stream, frames_builder=frames_builder,
                              engine_factory=engine_factory,
                              task_scale="4h")
        loop.run_to(pd.Timestamp("2025-01-08 00:00", tz="UTC"))
        states = [rec.lifecycle_state for rec in loop.engine.records]
        fc = [f.status for fid, vs in loop.engine.forecast_versions.items()
              for f in vs]
        dirs = [i.data.get("direction") for rec in loop.engine.records
                for i in rec.interpretations
                if i.interpretation_id == "I-primary"]
        return states, fc, dirs

    states_a, fc_a, dirs_a = summary(PATH)
    # consistent absolute-scale change (everything scaled)
    states_b, fc_b, dirs_b = summary([c * 10.0 for c in PATH], wick=50.0)
    # irrelevant candle-shape detail change (tiny wick jitter)
    states_c, fc_c, dirs_c = summary(PATH, wick=5.01)
    assert states_a == states_b == states_c
    assert fc_a == fc_b == fc_c
    assert dirs_a == dirs_b == dirs_c


# --------------------------------------------------------------------- #
# T11: missing order-book / position / source info reported honestly     #
# --------------------------------------------------------------------- #
def test_missing_information_reported_honestly():
    caps = DATA_CAPABILITIES
    assert caps["order_book"]["status"] == "unavailable"
    assert "resting orders" in caps["order_book"]["detail"]
    assert caps["individual_trades"]["status"] == "unavailable"
    assert caps["open_position"]["status"] == "absent"
    assert caps["live_market_feed"]["status"] == "unavailable"
    assert LIVE_FEED_STATUS["exists"] is False
    with pytest.raises(NotImplementedError):
        LiveFeedAdapter().next_observation()
    for c in CONCEPT_REGISTER:
        assert c["limitations"] and c["availability_time"]
        assert c["revision_dependencies"] is not None
    # volume is explicitly only a reported aggregate
    assert caps["reported_volume"]["kind"] == "reported-aggregate"


# --------------------------------------------------------------------- #
# T12: real ledger propagation updates actual dependencies               #
# --------------------------------------------------------------------- #
def test_ledger_propagation_updates_actual_dependencies():
    """Real SP-20 propagation: a dependent expert task is RECOMPUTED
    from its stored payload when the evidence it consumed changes."""
    from trading_system.research.contextual_selection.csm import (
        InterpretationLedger, PolicyRegistry, SharedInformationAxis,
        Representation, build_legs, fk_turning_points, TIE_FT_EQ_FIRST)
    from trading_system.research.contextual_selection import (
        expert_selection as es)

    rows = synth_rows(PATH)
    frames = frames_builder(rows)
    b4 = frames["4h"]
    axis = SharedInformationAxis("t12", b4.index)
    rep = Representation(family="F-K", view_id="C",
                         scale_label="coarse", params=(("k", 2.0),))
    points = fk_turning_points(b4, 2, rep, id_prefix="P12",
                               allow_short_left=False,
                               tie_policy=TIE_FT_EQ_FIRST, axis=axis)
    legs = build_legs(points, rep, completed_only=True, ambiguities=[])
    pid = "P-ORIGIN-RESEARCH"
    policy = PolicyRegistry()
    policy.register(pid, "origin role (research)",
                    "origin-of-last-confirmed-leg", False,
                    "research_configuration")

    def task(bar, prefix):
        return es.expert_structural_reference_selection(
            points=points, legs=legs, decision_bar=bar, rep=rep,
            policy=policy, role="origin-of-last-confirmed-leg",
            policy_id=pid, allow_provisional=False,
            decision_time=b4.index[bar], axis=axis, relationships=None,
            state_id_prefix=prefix)

    e_a, e_b = task(8, "TA"), task(10, "TB")
    ledger = InterpretationLedger()

    def payload(e, bar, prefix):
        return e.ledger_payload(
            run_id="t12", points=points, legs=legs, rep=rep, policy=policy,
            role="origin-of-last-confirmed-leg", policy_id=pid,
            allow_provisional=False, axis=axis, relationships=None,
            decision_time=b4.index[bar], state_id_prefix=prefix)

    uid_a = ledger.record(e_a.final_result, payload(e_a, 8, "TA"))
    uid_b = ledger.record(e_b.final_result, payload(e_b, 10, "TB"))
    cid = e_b.final_result.selected_id or points[0].candidate_id

    ledger.record_change(12, cid, "superseded",
                         detail="upstream structural fact changed")
    entries = ledger.propagate(12, [cid],
                               changed_states={cid: "superseded"},
                               axis=axis)
    recomputed = [e for e in entries if e.get("kind") == "recomputation"
                  and e.get("uid") == uid_b and not e.get("stale")]
    assert recomputed, entries                      # REAL dependency update
    assert len(ledger.versions[uid_b]) >= 2         # new version appended
    assert ledger.versions[uid_b][0]["version"] == 1  # prior preserved
    assert any(e.get("uid") == uid_a for e in entries)  # transitive edge
