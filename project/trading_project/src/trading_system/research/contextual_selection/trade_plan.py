"""Contextual trade-plan layer V1 — an ICT-grounded CONDITIONAL trade plan
on top of the analysis lifecycle and the contextual decision layer.

The path is ANALYTICAL ONLY.  A plan is a recorded conditional hypothesis,
never an order.  No live order execution exists anywhere in this code.
``selection_quality`` stays ``NOT_ESTABLISHED``.

WHAT THIS LAYER ADDS (task contract)
------------------------------------
For a declared instrument/task, one connected lifecycle:

  market context -> structural evidence -> working interpretation ->
  awaited / already-observed event -> HYPOTHETICAL trade-plan candidate
  (only when entry, invalidation and objective are each definable) ->
  observable state -> next observation -> versioned revision.

PLAN STATES are defined ONLY by observable events:

  MONITORING                neither the entry event nor the invalidation
                            event is observed after the plan record;
  CONDITION_OBSERVED        the entry event was already observed at or
                            before the plan record (past; NEVER claimed
                            as a pre-event plan);
  HYPOTHETICAL_ENTRY_MET    the entry event is observed after the plan
                            record, before any invalidation;
  INVALIDATED               the invalidation event is observed before
                            the objective (pre-entry or post-entry is
                            recorded in the version detail);
  MISSED                    the entry event and the objective first
                            become visible at the SAME decision boundary
                            (no boundary observed entry-before-objective;
                            no hypothetical entry could be staged);
  NO_JUSTIFIED_PLAN         no plan record was created at this snapshot;
                            the version carries the SPECIFIC missing
                            evidence (never a guessed number and never a
                            generic "confirmation").

PLAN COMPONENTS and their origins (requirement: identify which is which):

  entry        the scenario's discriminating observable event
               (SP-03 close-based binding of the last leg's end extreme
               in the leg's direction for the continuation scenario, or
               of the falsifier reference on its falsifying side for the
               reversal scenario).  ORIGIN: declared research
               configuration (this project's operational machinery).
               The ICT-published entry technique ("when price trades
               higher away from the bullish order block and then returns
               to the bullish order block candle or price bar high",
               P1 quote) is SOURCE-STATED but NOT implemented here:
               its order-block candidate generator (G-OB-P) is recorded
               NOT RUNNABLE in the pinned foundation until the owner
               declares the unset P-N ("near support") and P-W ("the
               move" window) slots; no values are invented in this path.
  invalidation SP-03 close-based violation of the falsifier reference on
               its falsifying side.  ORIGIN: engineering interpretation
               of the project's falsifier semantics (pinned knowledge
               paraphrase: T-S5/SP-04 "loses support"), with the SOURCE
               concept present ("the low of the bullish order block is
               the location of a relatively safe stop loss placement",
               P1 quote) — but ICT-primary invalidation-by-close is
               recorded NOT in the primary text read (P-K); the
               close-through rule is community (S1), kept separate.
  objective    one completed, causally confirmed task-scale F-K leg in
               the scenario direction whose knowable time is after the
               entry bar.  ORIGIN: declared research configuration.
               No target definition exists in the verified primary text
               read; the pinned liquidity material explicitly refuses to
               select "the" liquidity target without a task and a stated
               objective and records no verified predictive mechanism.

SOURCE REGISTER (concrete, verifiable published examples; pinned
knowledge ``jfjdjdieifne/test@6c8bf6fd``, file/section locations exact):
see ``SOURCE_EXAMPLES`` below.  Each example records the reconstructible
sequence fields (context at decision time / reference / awaited-or-present
event / entry-and-invalidation as explicitly described / what was only
explained later) with claim classes.  A retrospective lesson teaches
methodology only; a later outcome NEVER enters a historical decision
snapshot.

CAUSALITY
---------
Plan records are immutable as-of records; revisions APPEND versions
(``revises`` links + revision reason) and are recorded in the existing
``InterpretationLedger`` (no parallel history).  Every event time in a
plan version is bounded by that version's as-of key.  Appending or
changing future data must not change a past plan record (tested).
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd

from trading_system.research.contextual_selection.csm import (
    Representation,
    SelectionResult,
    SharedInformationAxis,
    TIE_FT_EQ_FIRST,
    build_legs,
    fk_turning_points,
    sp03_binding,
)
from trading_system.research.contextual_selection.decision_layer import (
    EVENT_CONTINUATION,
    EVENT_VIOLATION,
)

__all__ = [
    "PLAN_MONITORING", "PLAN_CONDITION_OBSERVED",
    "PLAN_HYPOTHETICAL_ENTRY_MET", "PLAN_INVALIDATED", "PLAN_MISSED",
    "PLAN_NO_JUSTIFIED_PLAN", "PLAN_STATES",
    "PlanComponent", "PlanVersion", "TradePlan",
    "SOURCE_EXAMPLES", "build_components", "create_plan", "observe_plan",
    "evaluate_plans", "source_agreement", "resolve_world",
    "plan_ledger_entries", "PLAN_TASK_ID",
]

PLAN_TASK_ID = "T-PLAN-V1"

PLAN_MONITORING = "MONITORING"
PLAN_CONDITION_OBSERVED = "CONDITION_OBSERVED"
PLAN_HYPOTHETICAL_ENTRY_MET = "HYPOTHETICAL_ENTRY_MET"
PLAN_INVALIDATED = "INVALIDATED"
PLAN_MISSED = "MISSED"
PLAN_NO_JUSTIFIED_PLAN = "NO_JUSTIFIED_PLAN"
PLAN_STATES = (PLAN_MONITORING, PLAN_CONDITION_OBSERVED,
               PLAN_HYPOTHETICAL_ENTRY_MET, PLAN_INVALIDATED,
               PLAN_MISSED, PLAN_NO_JUSTIFIED_PLAN)
_TERMINAL = {PLAN_INVALIDATED, PLAN_MISSED}

_CLAIM_DIRECT = "directly-stated"
_CLAIM_PARA = "paraphrase"
_CLAIM_ENG = "engineering-interpretation"
_CLAIM_UNSUP = "unsupported-or-unavailable"

_ORIGIN_SOURCE = "verifiable-source"
_ORIGIN_DECLARED = "declared-research-configuration"


# --------------------------------------------------------------------- #
# SOURCE EXAMPLES — verifiable published material, exact locations       #
# (pinned knowledge foundation jfjdjdieifne/test@6c8bf6fd10e95813)      #
# --------------------------------------------------------------------- #
SOURCE_EXAMPLES: List[Dict[str, Any]] = [
    {
        "example_id": "SRC-EX-01-OB-ENTRY-STOP",
        "source": "ICT Mentorship Core Content – Month 04 – Orderblocks "
                  "(YouTube PIYh0CxoY9c; Dec-2016 content; uploader "
                  "The Inner Circle Trader)",
        "location": "knowledge_foundation/05_FVG_ORDER_BLOCKS_ZONES.md "
                    "§5.4 and §5.4a (P1 quotes) + "
                    "08_APPLIED_CHART_CASES.md CASE-02",
        "grade": "P1 partial transcript (opening section; no timestamps; "
                 "auto-caption artifacts; provenance caveats recorded)",
        "context_at_decision_time": (
            "\"the lowest candle or price bar with a down close that has "
            "the most range between open to close and is near a support "
            "level\" — 'near support' is UNDEFINED (P-N) and 'the move' "
            "window is UNDEFINED (P-W)", ),
        "reference_selected": (
            "the order-block candle itself: its HIGH is the validation/"
            "entry level, its LOW is the stop level"),
        "awaited_or_present_event": (
            "validation: \"the high of the lowest down candle or price "
            "bar is traded through by a later formed candle or price bar\""),
        "entry_and_invalidation_as_described": (
            "entry: \"when price trades higher away from the bullish "
            "order block and then returns to the bullish order block "
            "candle or price bar high\";  stop: \"the low of the bullish "
            "order block is the location of a relatively safe stop loss "
            "placement\";  stop management: \"just below the 50 percent "
            "of the order block total range\" (AMBIGUOUS UN-11)"),
        "explained_only_after_outcome": (
            "not applicable: the lesson is procedural "
            "(\"candles, validation, entries, stops\"), not a statistical "
            "result (05 §5.7); no outcome-based case is used as evidence "
            "(08 §8.3)"),
        "claim_classes": {
            "definition": _CLAIM_DIRECT, "validation": _CLAIM_DIRECT,
            "entry": _CLAIM_DIRECT, "stop": _CLAIM_DIRECT,
            "stop_management": _CLAIM_PARA,
            "operationalization": _CLAIM_UNSUP,
        },
    },
    {
        "example_id": "SRC-EX-02-INVALIDATION-GAP",
        "source": "same lesson set + community pages (S1)",
        "location": "knowledge_foundation/05_FVG_ORDER_BLOCKS_ZONES.md "
                    "§5.4a parameter P-K and §5.8",
        "grade": "P1 for the primary-text gap; S1 snippets for the "
                 "community rule",
        "context_at_decision_time": ("zone status transitions each "
                                     "require a bar and a knowability "
                                     "time (§5.8)"),
        "reference_selected": ("zone boundaries of the candidate"),
        "awaited_or_present_event": ("trade-through validation of the "
                                     "block's high (P1 wording)"),
        "entry_and_invalidation_as_described": (
            "entry described (SRC-EX-01); INVALIDATION: 'Not in primary "
            "text read' (P-K) — the community close-through "
            "mitigation/invalidation concept is a separate S1 rule and "
            "is NOT merged with the primary definition"),
        "explained_only_after_outcome": ("n/a"),
        "claim_classes": {"primary_invalidation": _CLAIM_UNSUP,
                          "community_close_through": _CLAIM_PARA},
    },
    {
        "example_id": "SRC-EX-03-NO-TARGET-IN-VERIFIED-TEXT",
        "source": "pinned liquidity/method material",
        "location": "knowledge_foundation/04_LIQUIDITY.md (lines 21, 73, "
                    "77, 87-88, 100) + 02_SWINGS_AND_WAVES.md line 57",
        "grade": "foundation synthesis with explicit gap markers",
        "context_at_decision_time": ("liquidity candidates exist "
                                     "(untaken old highs/lows)"),
        "reference_selected": ("NOT selectable: \"The available "
                               "information does not select one as 'the' "
                               "liquidity target without a task and a "
                               "stated objective\""),
        "awaited_or_present_event": ("n/a"),
        "entry_and_invalidation_as_described": (
            "no target/objective definition in the verified primary text "
            "read; the stop-cluster mechanism is asserted in community "
            "sources with NO verified empirical confirmation (CF-05)"),
        "explained_only_after_outcome": ("n/a"),
        "claim_classes": {"target_refusal": _CLAIM_DIRECT,
                          "mechanism": _CLAIM_UNSUP},
    },
]


def source_agreement(plan_definitions: Dict[str, Any]) -> Dict[str, Any]:
    """Agreement matrix: the plan layer's component definitions vs each
    explicit source statement.  Cells are honest: 'agrees', 'differs',
    or 'not stated in verified material'.  This compares DEFINITIONS
    only — it is not a performance claim."""
    return {
        "scope": "definition-level agreement only; NOT a performance or "
                 "accuracy claim",
        "rows": [
            {"component": "entry",
             "source_position": "SRC-EX-01: ICT entry technique = trade "
                                "away from the OB then return to its "
                                "high (directly-stated)",
             "plan_position": plan_definitions.get("entry", {}).get(
                 "definition", ""),
             "verdict": "differs (engine uses the scenario's "
                        "discriminating binding; the OB-return technique "
                        "is NOT implemented — G-OB-P not runnable: "
                        "P-N/P-W unset in the foundation and no owner "
                        "policy exists)"},
            {"component": "invalidation",
             "source_position": "SRC-EX-01 stop at the OB low "
                                "(directly-stated); SRC-EX-02: ICT-"
                                "primary invalidation-by-close NOT in "
                                "primary text (P-K)",
             "plan_position": plan_definitions.get(
                 "invalidation", {}).get("definition", ""),
             "verdict": "partially aligned (stop-at-structural-extreme "
                        "concept present in source; the close-based "
                        "falsifier operationalization is engineering/"
                        "community-influenced, not ICT-primary)"},
            {"component": "objective",
             "source_position": "SRC-EX-03: no target definition in "
                                "verified primary text; liquidity "
                                "target explicitly not selectable",
             "plan_position": plan_definitions.get(
                 "objective", {}).get("definition", ""),
             "verdict": "not stated in verified material (declared "
                        "research configuration used; identified as "
                        "such)"},
        ],
    }


# --------------------------------------------------------------------- #
# plan components                                                        #
# --------------------------------------------------------------------- #
@dataclass
class PlanComponent:
    kind: str                # entry | invalidation | objective
    definition: str
    detector: str
    basis: str
    claim_class: str
    definition_origin: str   # verifiable-source | declared-research-
                             # configuration (or a MIXED label)
    source_reference: Optional[str] = None

    def to_record(self) -> dict:
        return dataclasses.asdict(self)


def build_components(*, scenario: str) -> Dict[str, PlanComponent]:
    """scenario = 'continuation' (primary) or 'reversal' (alternative)."""
    if scenario == "continuation":
        entry_txt = ("the first completed task-scale bar whose CLOSE is "
                     "strictly beyond the last confirmed leg's END "
                     "extreme in the leg's direction (SP-03 close "
                     "binding of the leg-end reference)")
        inval_txt = ("the first completed task-scale bar whose CLOSE is "
                     "strictly beyond the falsifier reference level on "
                     "its falsifying side (SP-03 close violation)")
    else:
        entry_txt = ("the first completed task-scale bar whose CLOSE is "
                     "strictly beyond the falsifier reference level on "
                     "its falsifying side (SP-03 close violation — the "
                     "event that supports the reversal scenario)")
        inval_txt = ("the first completed task-scale bar whose CLOSE is "
                     "strictly beyond the last confirmed leg's END "
                     "extreme in the leg's direction (SP-03 close "
                     "binding — the event that supports the continuation "
                     "scenario and voids the reversal plan)")
    return {
        "entry": PlanComponent(
            kind="entry", definition=entry_txt,
            detector="sp03-close-binding", basis="SRS-SP03 + SRS-FK",
            claim_class=_CLAIM_ENG,
            definition_origin=_ORIGIN_DECLARED,
            source_reference="ICT entry technique exists (SRC-EX-01) "
                             "but is NOT implemented: G-OB-P not "
                             "runnable (P-N/P-W unset; owner policy "
                             "required; none invented)"),
        "invalidation": PlanComponent(
            kind="invalidation", definition=inval_txt,
            detector="sp03-close-violation",
            basis="SRS-SP03 + SRS-SP04 + SRS-TS5 (falsifier semantics)",
            claim_class=_CLAIM_ENG,
            definition_origin=_ORIGIN_DECLARED,
            source_reference="SRC-EX-01 stop concept (directly-stated) "
                             "+ SRC-EX-02: ICT-primary invalidation-by-"
                             "close NOT in primary text (P-K)"),
        "objective": PlanComponent(
            kind="objective",
            definition=("one completed, causally confirmed task-scale "
                        "F-K leg in the scenario direction whose "
                        "knowable time is after the entry bar"),
            detector="fk-leg-completion", basis="SRS-FK",
            claim_class=_CLAIM_ENG,
            definition_origin=_ORIGIN_DECLARED,
            source_reference="SRC-EX-03: no target definition in the "
                             "verified primary text read"),
    }


# --------------------------------------------------------------------- #
# world resolution (deterministic; approved components only)             #
# --------------------------------------------------------------------- #
def resolve_world(*, frames: Dict[str, pd.DataFrame], record, k: int,
                  task_scale: str = "4h",
                  axis: Optional[SharedInformationAxis] = None
                  ) -> Dict[str, Any]:
    """FK world at the record's as-of; returns the falsifier reference
    and the leg-end point with their levels/sides (frozen into the plan)."""
    bars = frames[task_scale].iloc[:record.as_of_bar + 1]
    rep = Representation(family="F-K", view_id="C", scale_label="coarse",
                         params=(("k", float(k)),))
    points = fk_turning_points(bars, k, rep, id_prefix="PT",
                               allow_short_left=False,
                               tie_policy=TIE_FT_EQ_FIRST, axis=axis)
    by_id = {p.candidate_id: p for p in points}
    legs = build_legs(points, rep, completed_only=True, ambiguities=[])
    ref_id = record.reference_status.get("selected")
    end_id = None
    direction = None
    for f in record.structural_facts:
        if f.kind == "derived-movement-direction":
            end_id = f.inputs.get("end_id")
            direction = f.inputs.get("direction") or (
                "up" if "moved up" in f.description else "down")
            break
    ref = by_id.get(ref_id) if ref_id else None
    end = by_id.get(end_id) if end_id else None
    return {"ref": ref, "end": end, "legs": legs,
            "direction": direction, "by_id": by_id,
            "ref_bar": getattr(ref, "occurrence_bar", None),
            "end_bar": getattr(end, "occurrence_bar", None)}


# --------------------------------------------------------------------- #
# plan records (immutable versions; revisions append)                    #
# --------------------------------------------------------------------- #
@dataclass
class PlanVersion:
    version: int
    revises: Optional[str]
    as_of_time: pd.Timestamp
    as_of_bar: int
    state: str
    state_detail: str
    scenario: str                 # continuation | reversal
    direction: str                # up | down
    components: Dict[str, dict]
    levels: Dict[str, Any]        # frozen refs: ids/levels/sides
    events_observed: Dict[str, Any]
    observed_before_record: bool
    revision_reason: Optional[str]
    decision_id: str
    analysis_id: str
    analysis_version: int
    run_context: str
    missing_evidence: List[str]
    position_status: str
    selection_quality: str
    limitations: List[str]
    ledger_uid: Optional[str] = None

    def to_record(self) -> dict:
        d = dataclasses.asdict(self)
        d["as_of_time"] = str(self.as_of_time)
        return d


@dataclass
class TradePlan:
    plan_id: str
    run_id: str
    instrument: str
    task_scale: str
    versions: List[PlanVersion] = field(default_factory=list)
    no_plan_reasons: List[dict] = field(default_factory=list)
    entry_bars_seen: List[int] = field(default_factory=list)
    invalidation_bars_seen: List[int] = field(default_factory=list)
    objective_seen: bool = False
    scanned_through_bar: int = -1

    @property
    def current(self) -> PlanVersion:
        return self.versions[-1]

    @property
    def active(self) -> bool:
        v = self.current
        if v.state in _TERMINAL:
            return False
        if v.state == PLAN_HYPOTHETICAL_ENTRY_MET and self.objective_seen:
            return False
        return v.state in (PLAN_MONITORING, PLAN_CONDITION_OBSERVED,
                           PLAN_HYPOTHETICAL_ENTRY_MET)

    def to_record(self) -> dict:
        return {"plan_id": self.plan_id, "run_id": self.run_id,
                "instrument": self.instrument,
                "task_scale": self.task_scale,
                "versions": [v.to_record() for v in self.versions],
                "no_plan_reasons": self.no_plan_reasons,
                "events_seen": {
                    "entry_bars": self.entry_bars_seen,
                    "invalidation_bars": self.invalidation_bars_seen,
                    "objective_seen": self.objective_seen}}


def _limitations(run_context: str) -> List[str]:
    return [
        "selection_quality = NOT_ESTABLISHED",
        "hypothetical analytical record — NOT an order; no execution "
        "connectivity exists",
        "no position is inferred from chart data; position_status is "
        "always 'absent'",
        "the decision layer's ranking is PROVISIONAL and UNVALIDATED "
        "(10/17 vs 6/17 on 17 correlated episodes is a small sample and "
        "establishes nothing about market understanding or readiness)",
        "run context: " + run_context + " (a historical replay is never "
        "an actual live market observation)",
        "no probabilities, no candle counts, no percentages, no ATR "
        "multiples and no confidence values are used or implied",
        "not Michael Huddleston; no exact-replication, accuracy or "
        "profitability claim",
    ]


def create_plan(*, record, decision, world: Dict[str, Any],
                run_id: str, seq: int, frames: Dict[str, pd.DataFrame],
                run_context: str = "historical-replay",
                ) -> Tuple[Optional["TradePlan"], dict]:
    """Create a plan record from a decision with an evidence-supported
    preference — or return NO_JUSTIFIED_PLAN with the SPECIFIC missing
    evidence.  Never fabricates a direction or a component value."""
    missing: List[str] = []
    if decision.primary_is_baseline or decision.state in (
            "NO_EDGE", "UNRESOLVED"):
        missing.append(
            "evidence-supported directional preference (the decision is "
            + decision.state + ": " +
            "model does not strictly distinguish the scenarios / input "
            "insufficient)")
    ref, end = world.get("ref"), world.get("end")
    if ref is None:
        missing.append("precise falsifier reference (reference_status="
                       + str(record.reference_status.get("status")))
    if end is None or not world.get("direction"):
        missing.append("completed task-scale leg with a resolved end "
                       "extreme")
    reason = {
        "as_of": str(record.as_of_time),
        "decision_id": decision.decision_id,
        "state": PLAN_NO_JUSTIFIED_PLAN,
        "missing_evidence": missing or None,
        "next_discriminating_observation":
            decision.next_discriminating_observation}
    if missing:
        reason["missing_evidence"] = missing
        return None, reason

    scenario = ("continuation"
                if decision.primary_interpretation_id == "I-primary"
                else "reversal")
    direction = world["direction"] if scenario == "continuation" else (
        "down" if world["direction"] == "up" else "up")
    comps = build_components(scenario=scenario)
    fals_side = "down" if ref.side == "low" else "up"
    cont_side = "up" if world["direction"] == "up" else "down"
    levels = {
        "reference": {"id": ref.candidate_id, "level": ref.level,
                      "side": ref.side, "falsifying_side": fals_side,
                      "bar": int(world.get("ref_bar")
                                 or ref.occurrence_bar or 0)},
        "leg_end": {"id": end.candidate_id, "level": end.level,
                    "side": end.side, "continuation_side": cont_side,
                    "bar": int(world.get("end_bar")
                               or end.occurrence_bar or 0)},
        "leg_direction": world["direction"],
        "plan_direction": direction}

    # entry already observed in the as-of history? (never a pre-event plan)
    bars = frames["4h"]
    hist_entry, hist_inval = _scan_bindings(
        bars, 0, int(record.as_of_bar), levels, scenario)
    observed_before = bool(hist_entry)
    entry_bar = hist_entry[0] if hist_entry else None
    inval_bar = hist_inval[0] if hist_inval else None

    if observed_before and (inval_bar is None or (entry_bar is not None
                                                  and entry_bar <=
                                                  inval_bar)):
        state = PLAN_CONDITION_OBSERVED
        detail = ("the entry condition was already observed in the "
                  "available history before this record "
                  "(observed_before_record=True) — it is NOT described "
                  "as a pre-event plan and no hypothetical entry is "
                  "claimed")
    elif inval_bar is not None and (entry_bar is None or inval_bar <
                                    entry_bar):
        state = PLAN_INVALIDATED
        detail = ("the invalidation condition is already present in the "
                  "as-of history before any entry (past event)")
    else:
        state = PLAN_MONITORING
        detail = ("awaiting the entry condition: " +
                  comps["entry"].definition)

    plan = TradePlan(plan_id=f"PLAN-{run_id}-{seq:04d}", run_id=run_id,
                     instrument="BTCUSDT", task_scale="4h")
    v = PlanVersion(
        version=1, revises=None, as_of_time=pd.Timestamp(record.as_of_time),
        as_of_bar=int(record.as_of_bar), state=state,
        state_detail=detail, scenario=scenario, direction=direction,
        components={k: c.to_record() for k, c in comps.items()},
        levels=levels,
        events_observed={"entry_bars": list(hist_entry or []),
                         "invalidation_bars": list(hist_inval or [])},
        observed_before_record=observed_before, revision_reason=None,
        decision_id=decision.decision_id, analysis_id=record.analysis_id,
        analysis_version=record.analysis_version,
        run_context=run_context, missing_evidence=[],
        position_status="absent", selection_quality="NOT_ESTABLISHED",
        limitations=_limitations(run_context))
    plan.versions.append(v)
    plan.entry_bars_seen = list(hist_entry or [])
    plan.invalidation_bars_seen = list(hist_inval or [])
    plan.scanned_through_bar = int(record.as_of_bar)
    if entry_bar is not None:
        plan.objective_seen = _objective_exists(
            world.get("legs", []), direction, entry_bar,
            int(record.as_of_bar))
    return plan, {"as_of": str(record.as_of_time),
                  "state": state, "plan_id": plan.plan_id}


def _scan_bindings(bars: pd.DataFrame, j_from: int, j_to: int,
                   levels: Dict[str, Any], scenario: str
                   ) -> Tuple[List[int], List[int]]:
    """entry/invalidation binding bars in [j_from, j_to] for the plan's
    frozen levels.  Both are SP-03 close-based bindings of the two
    reference points; which one is entry vs invalidation depends on the
    scenario.  A binding is only meaningful AFTER the referenced point
    exists: each scan starts at its point's occurrence bar + 1 (the same
    rule the analysis layer uses for forecast conditions) — ancient bars
    never 'violate' a level that did not yet exist."""
    ref_pt = _Point(levels["reference"]["level"],
                    levels["reference"]["side"])
    end_pt = _Point(levels["leg_end"]["level"], levels["leg_end"]["side"])
    fals_side = levels["reference"]["falsifying_side"]
    cont_side = levels["leg_end"]["continuation_side"]
    ref_start = int(levels["reference"].get("bar", 0)) + 1
    end_start = int(levels["leg_end"].get("bar", 0)) + 1
    viol: List[int] = []
    cont: List[int] = []
    for j in range(max(0, j_from), min(j_to, len(bars) - 1) + 1):
        close = float(bars["close"].iloc[j])
        if not viol and j >= ref_start and sp03_binding(
                close, [ref_pt], side=fals_side, tie_bound=False):
            viol.append(j)
        if not cont and j >= end_start and sp03_binding(
                close, [end_pt], side=cont_side, tie_bound=False):
            cont.append(j)
        if viol and cont:
            break
    if scenario == "continuation":
        return cont, viol
    return viol, cont


class _Point:
    """Minimal SP-03-compatible point stand-in (level/side only)."""

    def __init__(self, level, side):
        self.level = float(level)
        self.side = side


def _objective_exists(legs: Sequence[Any], direction: str,
                      entry_bar: int, upto_bar: int) -> bool:
    for lg in legs:
        if not getattr(lg, "completed", True):
            continue
        if lg.direction != direction:
            continue
        if lg.knowable_bar is not None and lg.knowable_bar > entry_bar \
                and lg.knowable_bar <= upto_bar:
            return True
    return False


def observe_plan(*, plan: TradePlan, record, world: Dict[str, Any],
                 frames: Dict[str, pd.DataFrame], run_context: str,
                 decision_id: str) -> Optional[PlanVersion]:
    """Observe new evidence at a decision boundary; append an immutable
    version when the observable state changes.  Returns the new version
    (or None when nothing changed)."""
    if not plan.versions:
        return None
    cur = plan.current
    if cur.state in _TERMINAL:
        return None
    bars = frames["4h"]
    creation_bar = int(plan.versions[0].as_of_bar)
    j0 = plan.scanned_through_bar + 1
    j1 = int(record.as_of_bar)
    new_entry, new_inval = _scan_bindings(bars, j0, j1, plan.current.levels,
                                          plan.current.scenario)
    plan.entry_bars_seen.extend(new_entry)
    plan.invalidation_bars_seen.extend(new_inval)
    plan.scanned_through_bar = max(plan.scanned_through_bar, j1)

    direction = plan.current.direction
    # ONLY post-record events drive revisions: a pre-record event is
    # already classified at creation (observed_before_record) and is
    # NEVER re-reported as a post-record observation
    post_entry = sorted(b for b in plan.entry_bars_seen
                        if b > creation_bar)
    post_inval = sorted(b for b in plan.invalidation_bars_seen
                        if b > creation_bar)
    first_entry = post_entry[0] if post_entry else None
    first_inval = post_inval[0] if post_inval else None
    hist_entry = min((b for b in plan.entry_bars_seen
                      if b <= creation_bar), default=None)

    objective_now = False
    if first_entry is not None:
        # objective must become knowable AFTER the entry bar AND after
        # the plan record (a leg completed before the record never
        # counts as a plan outcome)
        objective_now = _objective_exists(
            world.get("legs", []), direction, first_entry, j1)
        if objective_now:
            plan.objective_seen = True

    new_state: Optional[str] = None
    detail = ""
    entry_first_seen_now = first_entry is not None and \
        first_entry in new_entry
    inval_after_entry = first_inval is not None and first_entry is \
        not None and first_inval > first_entry
    # precedence (declared, deterministic): invalidation-before-entry >
    # post-entry invalidation > missed (entry+objective first visible at
    # one boundary, with no post-entry invalidation) > entry >
    # objective-after-entry note
    if first_inval is not None and (first_entry is None or
                                    first_inval < first_entry):
        new_state = PLAN_INVALIDATED
        prior = (f" after the already-observed entry (bar {hist_entry}, "
                 "observed_before_record=True)"
                 if hist_entry is not None else " before any entry")
        detail = (f"the invalidation condition was observed at bar "
                  f"{first_inval}{prior} (pre-record events are never "
                  f"re-reported as post-record)")
    elif first_entry is not None and cur.state == \
            PLAN_HYPOTHETICAL_ENTRY_MET and inval_after_entry:
        new_state = PLAN_INVALIDATED
        detail = (f"the invalidation condition was observed at bar "
                  f"{first_inval} after the hypothetical entry (bar "
                  f"{first_entry}) and before the objective")
    elif first_entry is not None and cur.state == PLAN_MONITORING:
        if objective_now and entry_first_seen_now and not inval_after_entry:
            new_state = PLAN_MISSED
            detail = (f"the entry event (bar {first_entry}) and the "
                      f"objective first became visible at the same "
                      f"boundary {record.as_of_time}: no boundary "
                      f"observed entry-before-objective, so no "
                      f"hypothetical entry could be staged")
        else:
            new_state = PLAN_HYPOTHETICAL_ENTRY_MET
            detail = (f"the entry condition was observed at bar "
                      f"{first_entry} after the plan record "
                      "(observed_before_record=False) — a HYPOTHETICAL "
                      "entry, not an order")
    elif first_entry is not None and objective_now and cur.state == \
            PLAN_HYPOTHETICAL_ENTRY_MET and entry_first_seen_now is False:
        # objective reached after a staged entry: outcome noted, state
        # name unchanged (the task's state vocabulary has no
        # 'objective-met' state; the outcome is evaluated separately)
        detail = ("the objective event (one completed confirmed leg in "
                  f"the {direction} direction after the entry bar) is "
                  "now visible; hypothetical outcome recorded for "
                  "evaluation (not a profit claim)")
    else:
        return None

    v = PlanVersion(
        version=cur.version + 1, revises=f"{plan.plan_id}@v{cur.version}",
        as_of_time=pd.Timestamp(record.as_of_time),
        as_of_bar=j1, state=new_state or cur.state, state_detail=detail,
        scenario=cur.scenario, direction=direction,
        components=cur.components, levels=cur.levels,
        events_observed={
            "entry_bars": list(plan.entry_bars_seen),
            "invalidation_bars": list(plan.invalidation_bars_seen),
            "objective_seen": plan.objective_seen,
            "new_entry_bars": new_entry,
            "new_invalidation_bars": new_inval},
        observed_before_record=cur.observed_before_record,
        revision_reason=(f"plan {plan.plan_id} revised to "
                         f"{new_state or cur.state} by post-record "
                         f"evidence ({plan.plan_id}@v{cur.version} "
                         "preserved)"),
        decision_id=decision_id, analysis_id=record.analysis_id,
        analysis_version=record.analysis_version,
        run_context=run_context, missing_evidence=[],
        position_status="absent", selection_quality="NOT_ESTABLISHED",
        limitations=_limitations(run_context))
    plan.versions.append(v)
    return v


# --------------------------------------------------------------------- #
# ledger integration (existing InterpretationLedger; no parallel history) #
# --------------------------------------------------------------------- #
def plan_ledger_entries(*, ledger, plan: "TradePlan",
                        axis: SharedInformationAxis,
                        run_id: str = "") -> List[str]:
    """Record every plan version in the EXISTING InterpretationLedger.
    Revisions are expressed with ``revision_of`` (immutable append; prior
    versions are never rewritten).  Returns the ledger uids."""
    uids: List[str] = []
    prev_uid: Optional[str] = None
    status_map = {
        PLAN_INVALIDATED: "falsified",
        PLAN_NO_JUSTIFIED_PLAN: "empty",
        PLAN_MISSED: "unresolved",
    }
    for v in plan.versions:
        key = axis.require_key(v.as_of_time, what="plan version as-of")
        result = SelectionResult(
            task_id="T-PLAN-V1",
            decision_bar=v.as_of_bar,
            status=status_map.get(v.state, "justified"),
            selected_id=f"{plan.plan_id}@v{v.version}",
            survivors=[], excluded=[], unresolved=None,
            provenance=["SRS-SP03", "SRS-FK", "SRS-SP04", "SRS-TS5",
                        "SRC-EX-01", "SRC-EX-02", "SRC-EX-03"],
            policy_refs=["P-ORIGIN-RESEARCH"],
            representation_id="F-K/C/coarse",
            dependencies=[v.decision_id, v.analysis_id],
            direction=v.direction,
            decision_time=pd.Timestamp(v.as_of_time),
            notes=[f"plan_state={v.state}", v.state_detail],
        )
        payload = {
            "kind": "trade_plan_version",
            "run_id": run_id or plan.run_id,
            "inputs": {"analysis_id": v.analysis_id,
                       "decision_id": v.decision_id,
                       "levels": v.levels,
                       "events_observed": v.events_observed},
            "definitions": v.components,
            "revision_of": prev_uid,
            "plan_state": v.state,
            "stale": False, "stale_reason": None,
            "recompute_supported": False, "recompute": None,
            "recorded_event_times": [str(v.as_of_time)],
            "ledger_version_before": len(ledger.results),
            "ledger_version_after": None,
            "depends_on_results": [],
        }
        uid = ledger.record(result, payload)
        payload["ledger_version_after"] = len(ledger.results)
        v.ledger_uid = uid
        uids.append(uid)
        prev_uid = uid
    return uids


# --------------------------------------------------------------------- #
# evaluation (four separate axes; no profitability claim)                #
# --------------------------------------------------------------------- #
def evaluate_plans(plans: Sequence[TradePlan]) -> Dict[str, Any]:
    """Hypothetical plan outcomes (mechanics only — NEVER profits)."""
    states: Dict[str, int] = {}
    outcomes = {"objective_before_invalidation": 0,
                "invalidated_after_entry": 0,
                "invalidated_before_entry": 0,
                "missed": 0, "open_at_run_end": 0}
    for p in plans:
        st = p.current.state
        states[st] = states.get(st, 0) + 1
        inval_pre = any(
            v.state == PLAN_INVALIDATED and "before any entry" in
            v.state_detail for v in p.versions)
        if inval_pre:
            outcomes["invalidated_before_entry"] += 1
        elif p.current.state == PLAN_INVALIDATED:
            outcomes["invalidated_after_entry"] += 1
        elif p.current.state == PLAN_MISSED:
            outcomes["missed"] += 1
        elif p.objective_seen and any(
                v.state == PLAN_HYPOTHETICAL_ENTRY_MET for v in p.versions):
            outcomes["objective_before_invalidation"] += 1
        elif p.active:
            outcomes["open_at_run_end"] += 1
    n = len(plans) or 1
    return {
        "n_plans": len(plans),
        "final_states": states,
        "hypothetical_outcomes": outcomes,
        "note": "hypothetical plan MECHANICS only: 'objective' means one "
                "completed confirmed structural leg — NOT a profit, NOT "
                "a return; losses, misses, invalidations and open cases "
                "are all reported; nothing here is trained on wins",
    }
