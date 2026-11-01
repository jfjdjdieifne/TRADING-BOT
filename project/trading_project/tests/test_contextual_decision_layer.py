"""Focused tests for the contextual decision layer (task-required):

  T1  different causal contexts can lead to different working
      interpretations;
  T2  a valid snapshot produces a specific working decision (not an
      empty candidate list);
  T3  unresolved evidence produces an explicit NO_EDGE decision with a
      named next discriminator (never a vague abstention), and UNRESOLVED
      is reserved for invalid/insufficient required input;
  T4  future data cannot alter an earlier analysis/decision (and no
      label window leaks into the fitting set at decision time);
  T5  later evidence revises the analysis without rewriting the earlier
      record;
  T6  a condition already present at startup is not described as a
      pre-event prediction;
  T7  out-of-sample evaluation uses chronological separation and no
      trade-profit labels.
"""

import json

import pandas as pd
import pytest

from trading_system.research.contextual_selection.analysis_lifecycle import (
    AnalysisEngine,
    STATE_INSUFFICIENT,
)
from trading_system.research.contextual_selection.decision_layer import (
    EVENT_AMBIGUOUS,
    EVENT_CONTINUATION,
    EVENT_DEFINITIONS,
    EVENT_NONE,
    EVENTS,
    EVENT_VIOLATION,
    EPISODE_HORIZON_BARS,
    STATE_AWAITING_EVENT,
    STATE_EVENT_OCCURRED,
    STATE_NO_EDGE,
    STATE_SCENARIO_DEVELOPING,
    STATE_UNRESOLVED,
    DECISION_STATES,
    ContextEventModel,
    Episode,
    EpisodeExtractor,
    chronological_split,
    decide,
    evaluate_model,
    extract_context,
    summarize_decisions,
)


# --------------------------------------------------------------------- #
# synthetic scenes                                                       #
# --------------------------------------------------------------------- #
def mk_bars(closes):
    idx = pd.date_range("2025-01-01 04:00", periods=len(closes), freq="4h",
                        tz="UTC")
    opens = [closes[0]] + closes[:-1]
    hi = [max(o, c) + 5 + (i % 3)
          for i, (o, c) in enumerate(zip(opens, closes))]
    lo = [min(o, c) - 5 - ((i + 1) % 3)
          for i, (o, c) in enumerate(zip(opens, closes))]
    return pd.DataFrame({"open": opens, "high": hi, "low": lo,
                         "close": closes, "volume": 1.0}, index=idx)


# V low (bar 4) -> up leg (4->8, completed at bar 10) -> pullback ->
# down leg (8->10, completed at bar 12) -> rise -> crash (bar 15)
PATH_UP = [100, 92, 84, 78, 70, 78, 84, 88, 92, 88, 86, 90, 94, 98,
           102, 60, 62, 64, 66]

BAR_T1 = 10          # last completed leg = UP (4->8)
BAR_T1B = 12         # last completed leg = DOWN (8->10)
BAR_T2 = 15          # crash: close 60 violates the low reference


def engine_of(closes, run_id="d", k=2):
    b4 = mk_bars(closes)
    frames = {"4h": b4, "1h": b4, "15m": b4}
    return AnalysisEngine(run_id=run_id, frames=frames, k=k), b4


def record_at(closes, bar, run_id="d", engine=None):
    eng = engine or engine_of(closes, run_id=run_id)[0]
    return eng, eng.analyze(mk_bars(closes).index[bar])


def hand_episode(ctx, label, seq, as_of, window_end_time):
    return Episode(
        episode_id=f"EP-h-{seq:04d}", as_of_time=as_of,
        as_of_bar=0, context=dict(ctx), label=label,
        label_time=None, label_detail={},
        exclusion_reason=None, window_end_bar=24,
        window_end_time=window_end_time)


def model_with(pairs):
    m = ContextEventModel()
    m.fit(pairs)
    return m


# --------------------------------------------------------------------- #
# T1: different causal contexts -> different working interpretations     #
# --------------------------------------------------------------------- #
def test_different_contexts_different_working_interpretations():
    # two snapshots of the same scene with DIFFERENT causal contexts:
    # bar 10 -> last completed leg is UP; bar 12 -> DOWN
    _, rec_up = record_at(PATH_UP, BAR_T1, run_id="t1a")
    _, rec_down = record_at(PATH_UP, BAR_T1B, run_id="t1b")
    ctx_up = extract_context(rec_up)
    ctx_down = extract_context(rec_down)
    assert ctx_up != ctx_down, "the two snapshots must form different contexts"
    assert ctx_up["direction"] == "up" and ctx_down["direction"] == "down"

    t = pd.Timestamp("2025-01-05", tz="UTC")
    w = pd.Timestamp("2025-01-09", tz="UTC")
    eps = ([hand_episode(ctx_up, EVENT_CONTINUATION, i, t, w)
            for i in range(4)] +
           [hand_episode(ctx_up, EVENT_VIOLATION, 4, t, w)] +
           [hand_episode(ctx_down, EVENT_VIOLATION, 10 + i, t, w)
            for i in range(4)] +
           [hand_episode(ctx_down, EVENT_CONTINUATION, 14, t, w)])
    model = model_with(eps)

    d_up = decide(record=rec_up, model=model, decision_seq=1)
    d_down = decide(record=rec_down, model=model, decision_seq=2)

    # the model ranks the two contexts differently...
    assert d_up.model_support["continuation"] > \
        d_up.model_support["violation"]
    assert d_down.model_support["violation"] > \
        d_down.model_support["continuation"]
    # ...and the WORKING INTERPRETATIONS differ
    assert d_up.primary_interpretation_id != \
        d_down.primary_interpretation_id
    assert d_up.primary_is_baseline is False
    assert d_down.primary_is_baseline is False
    assert d_up.state in (STATE_SCENARIO_DEVELOPING, STATE_AWAITING_EVENT)
    assert d_down.state in (STATE_SCENARIO_DEVELOPING, STATE_AWAITING_EVENT)


# --------------------------------------------------------------------- #
# T2: valid snapshot -> specific working decision                        #
# --------------------------------------------------------------------- #
def test_valid_snapshot_specific_decision():
    eng, rec = record_at(PATH_UP, BAR_T1, run_id="t2")
    model = ContextEventModel()          # even untrained: must decide
    d = decide(record=rec, model=model, decision_seq=1)

    assert d.state in DECISION_STATES
    assert d.state != STATE_UNRESOLVED
    assert d.primary_interpretation_id is not None
    assert d.primary_working_view and len(d.primary_working_view) > 10
    assert d.named_event and len(d.named_event) > 5
    assert d.next_discriminating_observation
    assert d.explanation["why"] and d.explanation["would_change"]
    assert d.position_status == "absent"
    assert d.selection_quality == "NOT_ESTABLISHED"
    rec_json = json.dumps(d.to_record(), default=str)
    assert "provisional" in rec_json.lower() or \
        d.model_status == "provisional-unvalidated"
    # alternatives stay visible but a choice was made
    assert d.alternative_interpretation_ids
    assert any(i != d.primary_interpretation_id
               for i in d.alternative_interpretation_ids)


# --------------------------------------------------------------------- #
# T3: NO_EDGE with a named discriminator; UNRESOLVED only if input bad    #
# --------------------------------------------------------------------- #
def test_no_edge_with_named_discriminator_not_vague_abstention():
    _, rec = record_at(PATH_UP, BAR_T1, run_id="t3")
    # context the model has never seen -> evidence does not distinguish
    model = ContextEventModel()
    d = decide(record=rec, model=model, decision_seq=1)
    assert d.state == STATE_NO_EDGE
    assert d.state != STATE_UNRESOLVED
    assert d.primary_interpretation_id is not None   # baseline chosen
    assert d.primary_is_baseline is True
    # named next discriminator: BOTH operational events, not a vague wait
    disc = d.next_discriminating_observation + " " + d.named_event
    assert EVENT_VIOLATION in disc and EVENT_CONTINUATION in disc
    for vague in ("wait for confirmation", "watch the market",
                  "be careful", "see what happens"):
        assert vague not in disc.lower()

    # TIED training evidence -> NO_EDGE as well (explicit tie, no
    # arbitrary tie-breaker)
    ctx = extract_context(rec)
    t = pd.Timestamp("2025-01-05", tz="UTC")
    w = pd.Timestamp("2025-01-09", tz="UTC")
    tied = model_with([hand_episode(ctx, EVENT_CONTINUATION, 0, t, w),
                       hand_episode(ctx, EVENT_VIOLATION, 1, t, w)])
    d2 = decide(record=rec, model=tied, decision_seq=2)
    assert d2.state == STATE_NO_EDGE

    # UNRESOLVED appears ONLY for insufficient required input
    eng = engine_of(PATH_UP, run_id="t3b")[0]
    rec_ins = eng.analyze(mk_bars(PATH_UP).index[2])   # no completed leg
    assert rec_ins.lifecycle_state == STATE_INSUFFICIENT
    d3 = decide(record=rec_ins, model=tied, decision_seq=3)
    assert d3.state == STATE_UNRESOLVED
    assert "insufficient" in " ".join(d3.explanation["why"]).lower()
    assert d3.named_event

    # an UNRESOLVED REFERENCE with a completed leg is NOT insufficient
    # input: the explicit decision is NO_EDGE with a named discriminator
    import dataclasses as _dc
    scenario_interp = _dc.replace(
        rec.interpretations[0], interpretation_id="I-scenario",
        data={**rec.interpretations[0].data,
              "reference_status": "unresolved"})
    rec_unref = _dc.replace(
        rec,
        reference_status={"status": "unresolved",
                          "reason": "MP-UNRESOLVED: two equal-knowable "
                                    "candidates (SP-18 tie policy "
                                    "undeclared)",
                          "survivors": ["PTC:a", "PTC:b"],
                          "role": "origin-of-last-confirmed-leg"},
        interpretations=[scenario_interp] + rec.interpretations[1:])
    d4 = decide(record=rec_unref, model=tied, decision_seq=4)
    assert d4.state == STATE_NO_EDGE
    assert d4.state != STATE_UNRESOLVED
    assert d4.primary_interpretation_id is not None
    disc4 = d4.next_discriminating_observation + " " + d4.named_event
    assert EVENT_VIOLATION in disc4 and EVENT_CONTINUATION in disc4


# --------------------------------------------------------------------- #
# T4: future data cannot alter an earlier analysis/decision               #
# --------------------------------------------------------------------- #
def test_future_data_cannot_alter_earlier_analysis():
    b_full = mk_bars(PATH_UP)
    b_short = b_full.iloc[:BAR_T1 + 1]

    def run(bars):
        frames = {"4h": bars, "1h": bars, "15m": bars}
        eng = AnalysisEngine(run_id="t4", frames=frames, k=2)
        return eng.analyze(bars.index[BAR_T1])

    rec_short, rec_full = run(b_short), run(b_full)
    js = json.dumps(rec_short.to_record(), sort_keys=True, default=str)
    jf = json.dumps(rec_full.to_record(), sort_keys=True, default=str)
    assert js == jf, "future bars changed the earlier analysis record"

    model = ContextEventModel()
    d_s = decide(record=rec_short, model=model, decision_seq=1)
    d_f = decide(record=rec_full, model=model, decision_seq=1)
    assert json.dumps(d_s.to_record(), sort_keys=True, default=str) == \
        json.dumps(d_f.to_record(), sort_keys=True, default=str)

    # model fitting at decision time excludes every label window that
    # has not closed strictly before the decision
    ex = EpisodeExtractor(frames={"4h": b_full, "1h": b_full,
                                  "15m": b_full}, k=2, horizon_bars=4)
    eps = [ex.extract(rec_full, run_id="t4", seq=i) for i in range(1)]
    m2 = ContextEventModel()
    cutoff = pd.Timestamp(rec_full.as_of_time)
    m2.fit_before(eps, cutoff)
    for key in m2.counts:
        pass
    # (rec_full's own window ends after its as_of -> must not be fitted)
    assert m2.n_episodes == 0 or all(
        e.window_end_time < cutoff for e in eps if e.usable)


# --------------------------------------------------------------------- #
# T5: later evidence revises without rewriting the earlier record        #
# --------------------------------------------------------------------- #
def test_later_evidence_revises_without_rewriting():
    eng, b4 = engine_of(PATH_UP, run_id="t5")
    r1 = eng.analyze(b4.index[BAR_T1])
    d1 = decide(record=r1, model=ContextEventModel(), decision_seq=1)
    d1_json = json.dumps(d1.to_record(), sort_keys=True, default=str)

    r2 = eng.analyze(b4.index[BAR_T2])      # the crash violates the ref
    model = ContextEventModel()
    d2 = decide(record=r2, model=model, decision_seq=2)

    assert d2.state == STATE_EVENT_OCCURRED
    assert r2.revision_reason
    # the earlier decision record is untouched
    d1_again = decide(record=r1, model=ContextEventModel(),
                      decision_seq=1)
    assert json.dumps(d1_again.to_record(), sort_keys=True,
                      default=str) == d1_json
    # the revision is visible as a NEW analysis version with prior link
    assert r2.analysis_version == 2 and r2.revises
    # the earlier forecast version is preserved, not rewritten
    fid = r1.forecasts[0].forecast_id
    v1, v2 = eng.forecast_versions[fid]
    assert v1.status == "pending" and v2.status == "condition_observed"
    assert v2.revises == f"{fid}@v1"


# --------------------------------------------------------------------- #
# T6: already-observed at startup is not a pre-event prediction           #
# --------------------------------------------------------------------- #
def test_condition_already_present_not_predicted():
    eng, b4 = engine_of(PATH_UP, run_id="t6")
    # FIRST analysis happens only AFTER the violation (bar 15)
    r = eng.analyze(b4.index[BAR_T2])
    d = decide(record=r, model=ContextEventModel(), decision_seq=1)

    assert d.state in (STATE_EVENT_OCCURRED, STATE_NO_EDGE,
                       STATE_SCENARIO_DEVELOPING, STATE_AWAITING_EVENT)
    assert d.already_observed_conditions, \
        "the pre-existing condition must be visible"
    for c in d.already_observed_conditions:
        assert c["observed_before_record"] is True
    text = json.dumps(d.to_record(), default=str).lower()
    assert "pre-event prediction" in text or \
        "not described as a pre-event prediction" in \
        " ".join(d.explanation["would_change"]).lower()
    for claim in ("we predicted", "predicted before the",
                  "successful prediction", "foresaw"):
        assert claim not in text


# --------------------------------------------------------------------- #
# T7: chronological evaluation; no trade-profit labels                   #
# --------------------------------------------------------------------- #
def test_eval_chronological_no_profit_labels():
    eng, b4 = engine_of(PATH_UP, run_id="t7")
    frames = {"4h": b4, "1h": b4, "15m": b4}
    ex = EpisodeExtractor(frames=frames, k=2, horizon_bars=4)
    recs = [eng.analyze(b4.index[bar]) for bar in (10, 11, 12, 13, 15, 16)]
    eps = [ex.extract(r, run_id="t7", seq=i) for i, r in enumerate(recs)]
    usable = [e for e in eps if e.usable]
    assert usable, "synthetic scenes must yield labeled episodes"

    train, ev = chronological_split(usable, train_fraction=0.5)
    assert train and ev
    assert max(e.as_of_time for e in train) < \
        min(e.as_of_time for e in ev), "chronological separation"

    model = ContextEventModel()
    model.fit(train)
    rep = evaluate_model(model, ev)
    assert rep["n_eval_episodes"] == len(ev)
    assert set(rep["label_distribution"]) <= set(EVENTS)

    # labels are structural event identities only — never trade p/l
    for e in usable:
        assert e.label in EVENTS
        assert set(e.label_detail) <= {"bar", "side", "note"}
    label_text = json.dumps(
        {"labels": [e.label for e in usable],
         "details": [e.label_detail for e in usable],
         "confusion": rep["confusion_predicted_rows_realized_cols"]},
        default=str).lower()
    for token in ("profit", "pnl", "drawdown", "win rate",
                  "take profit", "stop loss", "risk"):
        assert token not in label_text
    assert "never" in rep["labels_note"].lower()

    # decision summary reports NO_EDGE frequency and never calls it win
    decisions = [decide(record=r, model=ContextEventModel(),
                        decision_seq=i) for i, r in enumerate(recs)]
    summary = summarize_decisions(decisions)
    assert summary["no_edge_count"] == sum(
        1 for d in decisions if d.state == STATE_NO_EDGE)
    assert "never" in summary["no_edge_note"].lower()


# --------------------------------------------------------------------- #
# extra: event definitions are operational and sourced                   #
# --------------------------------------------------------------------- #
def test_event_definitions_operational_and_sourced():
    for e in EVENTS:
        d = EVENT_DEFINITIONS[e]
        assert d["detector"] and d["definition"]
        assert d["basis"] and "SRS-" in d["basis"]
        assert d["claim_class"] in ("directly-stated", "paraphrase",
                                    "engineering-interpretation",
                                    "research-hypothesis",
                                    "unsupported-or-unavailable")
        assert d["scenario_support"] in ("primary", "alternative",
                                         "neutral")
    assert EVENT_DEFINITIONS[EVENT_VIOLATION]["scenario_support"] == \
        "alternative"
    assert EVENT_DEFINITIONS[EVENT_CONTINUATION]["scenario_support"] == \
        "primary"
    assert EPISODE_HORIZON_BARS > 0
