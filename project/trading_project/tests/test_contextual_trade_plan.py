"""Focused tests for the contextual trade-plan layer.

Covers: plan creation only with an evidence-supported preference (or a
NO_JUSTIFIED_PLAN record with the SPECIFIC missing evidence); states
defined by observable events (MONITORING before the condition;
HYPOTHETICAL_ENTRY_MET post-record; CONDITION_OBSERVED at startup never
a pre-event claim; INVALIDATED pre-entry; MISSED = entry+objective first
visible at one boundary); immutable versioned revisions recorded in the
existing InterpretationLedger; append-after-T invariance; plan-is-not-
an-order guards; source-vs-declared component origins.
"""

import json

import pandas as pd

from trading_system.research.contextual_selection.analysis_lifecycle import (
    AnalysisEngine,
)
from trading_system.research.contextual_selection.csm import (
    InterpretationLedger,
    SharedInformationAxis,
)
from trading_system.research.contextual_selection.decision_layer import (
    ContextEventModel,
    Episode,
    EVENT_CONTINUATION,
    EVENT_VIOLATION,
    decide,
    extract_context,
)
from trading_system.research.contextual_selection.trade_plan import (
    PLAN_CONDITION_OBSERVED,
    PLAN_HYPOTHETICAL_ENTRY_MET,
    PLAN_INVALIDATED,
    PLAN_MISSED,
    PLAN_MONITORING,
    PLAN_NO_JUSTIFIED_PLAN,
    PLAN_STATES,
    SOURCE_EXAMPLES,
    build_components,
    create_plan,
    evaluate_plans,
    observe_plan,
    plan_ledger_entries,
    resolve_world,
    source_agreement,
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


# V low (bar 4) -> up leg 4->8 (end level 95, completed at bar 10) ->
# pullback -> rise -> entry bar 14 (close 99 > 95) -> crash bar 15
# (close 52 < ref level 55)
PATH_MAIN = [80, 78, 74, 70, 62, 70, 76, 82, 88, 84, 82, 86, 90, 94,
             99, 52, 54, 56, 58]
# same prefix; early crash: invalidation (close < 55) at bar 13, no entry
PATH_EARLY = PATH_MAIN[:11] + [70, 60, 52, 50, 48]
# same prefix through the entry (bar 14: close 99 > 95); gentle pullback
# confirms the up leg 10->14 (knowable 16) WITHOUT invalidating (closes
# stay above the ref level 55)
PATH_PULL = PATH_MAIN[:15] + [96, 94, 92]
# entry fires at bar 11 (close 96 > end level 95) BEFORE the creation
# boundary at bar 11: the condition is already present at startup
PATH_OBS2 = [80, 78, 74, 70, 62, 70, 76, 82, 88, 84, 82, 96, 90, 88,
             86]

BAR_CREATE = 10


def engine_of(closes, run_id="tp", k=2):
    b4 = mk_bars(closes)
    frames = {"4h": b4, "1h": b4, "15m": b4}
    return (AnalysisEngine(run_id=run_id, frames=frames, k=k),
            frames, b4)


def decision_with_preference(frames, bar, run_id="tpd", prefer="cont"):
    """Real analysis record + a decision whose model evidence supports a
    strict preference (continuation or reversal)."""
    eng = AnalysisEngine(run_id=run_id, frames=frames, k=2)
    rec = eng.analyze(frames["4h"].index[bar])
    ctx = extract_context(rec)
    t = pd.Timestamp("2025-01-05", tz="UTC")
    w = pd.Timestamp("2025-01-09", tz="UTC")

    def ep(label, i):
        return Episode(episode_id=f"EP-p-{i}", as_of_time=t, as_of_bar=0,
                       context=dict(ctx), label=label, label_time=None,
                       label_detail={}, exclusion_reason=None,
                       window_end_bar=24, window_end_time=w)

    labels = ([EVENT_CONTINUATION] * 4 + [EVENT_VIOLATION]) \
        if prefer == "cont" else \
        ([EVENT_VIOLATION] * 4 + [EVENT_CONTINUATION])
    model = ContextEventModel()
    model.fit([ep(l, i) for i, l in enumerate(labels)])
    dec = decide(record=rec, model=model, decision_seq=1)
    return eng, rec, dec


def world_of(eng, frames, rec):
    return resolve_world(frames=frames, record=rec, k=2, axis=eng.axis)


def make_plan(closes, bar=BAR_CREATE, prefer="cont", run_id="tp"):
    eng, frames, b4 = engine_of(closes, run_id=run_id)
    d_eng, rec, dec = decision_with_preference(frames, bar,
                                               run_id=run_id + "d",
                                               prefer=prefer)
    w = world_of(eng, frames, rec)
    plan, reason = create_plan(record=rec, decision=dec, world=w,
                               run_id=run_id, seq=1, frames=frames)
    return eng, frames, b4, rec, dec, w, plan, reason


# --------------------------------------------------------------------- #
# 1: plan only with preference; components labeled source-vs-declared    #
# --------------------------------------------------------------------- #
def test_plan_components_labeled_and_no_invented_numbers():
    eng, frames, b4, rec, dec, w, plan, reason = make_plan(PATH_MAIN)
    assert plan is not None
    v = plan.current
    assert v.state == PLAN_MONITORING
    assert v.position_status == "absent"
    assert v.selection_quality == "NOT_ESTABLISHED"
    for kind in ("entry", "invalidation", "objective"):
        c = v.components[kind]
        assert c["definition_origin"] in (
            "verifiable-source", "declared-research-configuration")
        assert c["claim_class"] in (
            "directly-stated", "paraphrase",
            "engineering-interpretation", "research-hypothesis",
            "unsupported-or-unavailable")
        assert c["basis"] and c["detector"]
    # entry/objective are DECLARED research configuration (identified);
    # the source-reference field records the ICT material honestly
    assert v.components["entry"]["definition_origin"] == \
        "declared-research-configuration"
    assert "NOT implemented" in v.components["entry"]["source_reference"]
    assert v.components["objective"]["definition_origin"] == \
        "declared-research-configuration"
    # no invented numbers in the operative definitions
    defs = " ".join(v.components[k]["definition"] for k in v.components)
    for token in ("%", "ATR", "confidence", "R:R", "risk"):
        assert token.lower() not in defs.lower()


# --------------------------------------------------------------------- #
# 2: NO_JUSTIFIED_PLAN carries the SPECIFIC missing evidence             #
# --------------------------------------------------------------------- #
def test_no_plan_with_specific_missing_evidence():
    eng, frames, b4 = engine_of(PATH_MAIN, run_id="np")
    d_eng, rec, dec = decision_with_preference(frames, BAR_CREATE,
                                               run_id="npd", prefer="cont")
    # no-preference decision (untrained model) -> no justified plan
    weak = decide(record=rec, model=ContextEventModel(), decision_seq=1)
    w = world_of(eng, frames, rec)
    plan, reason = create_plan(record=rec, decision=weak, world=w,
                               run_id="np", seq=1, frames=frames)
    assert plan is None
    assert reason["state"] == PLAN_NO_JUSTIFIED_PLAN
    joined = " ".join(reason["missing_evidence"])
    assert "directional preference" in joined
    assert reason["next_discriminating_observation"]
    for vague in ("wait for confirmation", "see what happens"):
        assert vague not in joined.lower()


# --------------------------------------------------------------------- #
# 3: MONITORING before the condition -> entry met post-record (v2)       #
# --------------------------------------------------------------------- #
def test_monitored_before_condition_then_entry_met():
    eng, frames, b4, rec, dec, w, plan, reason = make_plan(
        PATH_PULL, run_id="em")
    assert plan.current.state == PLAN_MONITORING
    # boundary still before the entry event: still MONITORING (no change)
    rec13 = eng.analyze(b4.index[13])
    v = observe_plan(plan=plan, record=rec13,
                     world=world_of(eng, frames, rec13), frames=frames,
                     run_context="historical-replay", decision_id="d1")
    assert v is None and plan.current.state == PLAN_MONITORING

    # entry event (bar 14: close 99 > end level 95) after the record
    rec14 = eng.analyze(b4.index[14])
    v2 = observe_plan(plan=plan, record=rec14,
                      world=world_of(eng, frames, rec14), frames=frames,
                      run_context="historical-replay", decision_id="d2")
    assert v2 is not None
    assert v2.state == PLAN_HYPOTHETICAL_ENTRY_MET
    assert v2.observed_before_record is False
    assert v2.revises == f"{plan.plan_id}@v1"
    assert "HYPOTHETICAL" in v2.state_detail and "not an order" in \
        v2.state_detail
    # v1 preserved verbatim (immutable history)
    assert plan.versions[0].state == PLAN_MONITORING
    assert plan.versions[0].version == 1

    # objective (leg 10->14, knowable 16) becomes visible at bar 17
    rec17 = eng.analyze(b4.index[17])
    v3 = observe_plan(plan=plan, record=rec17,
                      world=world_of(eng, frames, rec17), frames=frames,
                      run_context="historical-replay", decision_id="d3")
    assert v3 is not None and "objective" in v3.state_detail
    assert plan.objective_seen is True
    ev = evaluate_plans([plan])
    assert ev["hypothetical_outcomes"]["objective_before_invalidation"] == 1


# --------------------------------------------------------------------- #
# 4: pre-entry INVALIDATION (observable invalidation first)              #
# --------------------------------------------------------------------- #
def test_invalidated_before_entry():
    eng, frames, b4, rec, dec, w, plan, reason = make_plan(
        PATH_EARLY, run_id="iv")
    assert plan.current.state == PLAN_MONITORING
    rec13 = eng.analyze(b4.index[13])   # close 52 < ref 55
    v2 = observe_plan(plan=plan, record=rec13,
                      world=world_of(eng, frames, rec13), frames=frames,
                      run_context="historical-replay", decision_id="d2")
    assert v2 is not None and v2.state == PLAN_INVALIDATED
    assert "before any entry" in v2.state_detail
    assert plan.active is False
    ev = evaluate_plans([plan])
    assert ev["hypothetical_outcomes"]["invalidated_before_entry"] == 1


# --------------------------------------------------------------------- #
# 5: MISSED = entry + objective first visible at one boundary            #
# --------------------------------------------------------------------- #
def test_missed_when_entry_and_objective_share_a_boundary():
    eng, frames, b4, rec, dec, w, plan, reason = make_plan(
        PATH_PULL, run_id="ms")
    # only one later boundary: entry (14) and objective (leg 10->14,
    # knowable 16) both first visible at bar 16
    rec16 = eng.analyze(b4.index[16])
    v2 = observe_plan(plan=plan, record=rec16,
                      world=world_of(eng, frames, rec16), frames=frames,
                      run_context="historical-replay", decision_id="d2")
    assert v2 is not None and v2.state == PLAN_MISSED
    assert "same" in v2.state_detail and "no boundary" in v2.state_detail
    ev = evaluate_plans([plan])
    assert ev["hypothetical_outcomes"]["missed"] == 1


# --------------------------------------------------------------------- #
# 6: condition already present at startup is never a pre-event claim     #
# --------------------------------------------------------------------- #
def test_condition_observed_at_startup_not_pre_event():
    # create the plan at a boundary where the entry condition (a close
    # beyond the leg-end level in the leg direction) is ALREADY present
    # in the available history (bar 11 close 96 > 95, created at bar 11):
    # it must be identified as past
    eng, frames, b4, rec, dec, w, plan, reason = make_plan(
        PATH_OBS2, bar=11, run_id="co")
    assert plan.current.state == PLAN_CONDITION_OBSERVED
    assert plan.current.observed_before_record is True
    text = json.dumps(plan.to_record(), default=str).lower()
    assert "not described as a pre-event plan" in text
    for claim in ("we predicted", "predicted before", "pre-event plan is",
                  "successful prediction"):
        assert claim not in text


# --------------------------------------------------------------------- #
# 7: future data cannot alter a past plan record                         #
# --------------------------------------------------------------------- #
def test_append_after_t_invariance():
    b_full = mk_bars(PATH_MAIN)
    b_short = b_full.iloc[:BAR_CREATE + 1]
    outs = []
    for bars in (b_short, b_full):
        frames = {"4h": bars, "1h": bars, "15m": bars}
        eng = AnalysisEngine(run_id="inv", frames=frames, k=2)
        rec = eng.analyze(bars.index[BAR_CREATE])
        d_eng, d_rec, dec = decision_with_preference(
            frames, BAR_CREATE, run_id="invd")
        w = resolve_world(frames=frames, record=rec, k=2, axis=eng.axis)
        plan, _ = create_plan(record=rec, decision=dec, world=w,
                              run_id="inv", seq=1, frames=frames)
        outs.append(json.dumps(plan.to_record(), sort_keys=True,
                               default=str))
    assert outs[0] == outs[1], "future bars changed the past plan record"


# --------------------------------------------------------------------- #
# 8: plan is an analytical record, not an order                          #
# --------------------------------------------------------------------- #
def test_plan_is_not_an_order():
    eng, frames, b4, rec, dec, w, plan, reason = make_plan(PATH_MAIN)
    text = json.dumps(plan.to_record(), default=str).lower()
    assert '"position_status": "absent"' in text
    for orderish in ("quantity", "leverage", "order_id", "buy order",
                     "sell order", "market order", "limit order",
                     "position size", "pnl"):
        assert orderish not in text
    assert any("NOT an order" in l for l in plan.current.limitations)


# --------------------------------------------------------------------- #
# 9: revisions are recorded in the EXISTING InterpretationLedger         #
# --------------------------------------------------------------------- #
def test_ledger_records_versions_with_revision_link():
    eng, frames, b4, rec, dec, w, plan, reason = make_plan(
        PATH_PULL, run_id="lg")
    rec14 = eng.analyze(b4.index[14])
    observe_plan(plan=plan, record=rec14,
                 world=world_of(eng, frames, rec14), frames=frames,
                 run_context="historical-replay", decision_id="d2")
    ledger = InterpretationLedger()
    axis = SharedInformationAxis("lg", frames["4h"].index)
    uids = plan_ledger_entries(ledger=ledger, plan=plan, axis=axis)
    assert len(uids) == 2
    assert plan.versions[0].ledger_uid == uids[0]
    assert plan.versions[1].ledger_uid == uids[1]
    payloads = ledger._payloads
    assert payloads[uids[0]]["revision_of"] is None
    assert payloads[uids[1]]["revision_of"] == uids[0]
    assert payloads[uids[1]]["plan_state"] == PLAN_HYPOTHETICAL_ENTRY_MET
    assert [r.status for r in ledger.results] == ["justified", "justified"]
    assert all(any("plan_state=" in n for n in r.notes)
               for r in ledger.results)
    # prior version never rewritten
    assert plan.versions[0].state == PLAN_MONITORING


# --------------------------------------------------------------------- #
# 10: source register + agreement honesty                                #
# --------------------------------------------------------------------- #
def test_source_examples_and_agreement_honest():
    assert len(SOURCE_EXAMPLES) >= 2
    for ex in SOURCE_EXAMPLES:
        assert ex["location"] and ex["source"]
        for k in ("context_at_decision_time", "reference_selected",
                  "entry_and_invalidation_as_described",
                  "explained_only_after_outcome"):
            assert ex.get(k)
        for cls in ex["claim_classes"].values():
            assert cls in ("directly-stated", "paraphrase",
                           "engineering-interpretation",
                           "research-hypothesis",
                           "unsupported-or-unavailable")
    comps = {k: c.to_record() for k, c in
             build_components(scenario="continuation").items()}
    agree = source_agreement(comps)
    verdicts = [r["verdict"] for r in agree["rows"]]
    assert any("differs" in v for v in verdicts)
    assert any("not stated" in v for v in verdicts)
    assert "NOT a performance" in agree["scope"]
    assert len(PLAN_STATES) == 6
    assert PLAN_NO_JUSTIFIED_PLAN in PLAN_STATES
