"""Contextual decision layer V1 — the missing decision on top of the
analysis lifecycle.

For every VALID as-of snapshot the analysis engine produces (records in
``analysis_lifecycle``), this layer produces ONE contextual decision:

  1. one primary working interpretation selected from the available
     evidence (material alternatives stay visible; the layer never
     avoids choosing by listing alternatives only);
  2. one explicit analytical state:
       SCENARIO_DEVELOPING | AWAITING_EVENT | EVENT_OCCURRED |
       PRIOR_VIEW_WEAKENED_OR_INVALIDATED | NO_EDGE | UNRESOLVED
     (UNRESOLVED is reserved for invalid or insufficient REQUIRED input;
     when the evidence does not distinguish the scenarios the decision is
     the explicit NO_EDGE with a named next discriminating event);
  3. a concise explanation: why this is the current working view, what
     evidence opposes it, and what observable event would change it.

DECISION METHOD (task contract)
-------------------------------
No fixed market recipe, no arbitrary thresholds, no invented weights, no
random tie-breakers.  The layer uses the project's existing causal market
facts and operational event definitions (SP-03 close-based binding over
F-K turning points/legs) and a LOCAL, CONTEXT-CONDITIONED model that
learns, from chronological historical episodes, which PREDEFINED
observable event is more likely in each causal context:

  * predefined observable events (operational detectors):
      E-VIOLATION     — SP-03 close-based violation of the current
                        falsifier reference on the falsifying side
                        (the analysis layer's forecast condition);
      E-CONTINUATION  — SP-03 close-based binding of the last confirmed
                        leg's END extreme in the leg's direction;
      E-NONE-IN-HORIZON  — neither fires within the declared horizon;
      E-AMBIGUOUS-SAME-BAR — both fire on the same first bar (an
                        UNRESOLVED case, reported as such).

  * the model is a per-context event frequency table over training
    episodes (no smoothing, no weights).  A ranking is emitted ONLY as an
    ordinal ranking with training support counts, labeled
    ``provisional-unvalidated``: probabilities are NOT emitted because the
    ranking is not calibrated on a versioned out-of-sample set.  Ties are
    explicit; they are never broken arbitrarily.

  * episodes are chronological snapshots whose CONTEXT comes only from
    what was known at the as-of time and whose LABEL is the first
    predefined event in a declared research horizon AFTER the as-of
    (future observations enter ONLY the label, never the features, the
    analysis, or the forecast).  Trade profit/loss is never a label:
    labels are structural event identities (continuation / violation /
    none / ambiguous), covering continuation cases, violation cases,
    unresolved cases, and ordinary periods.

  * decisions use an EXPANDING training window: at decision time T the
    model has fitted only episodes whose label windows CLOSED strictly
    before T.  Out-of-sample evaluation uses a chronological split
    (earlier episodes fit; strictly later episodes evaluate).

This layer decides ANALYTICAL postures only.  It never decides trades,
never sizes positions, and never claims readiness for execution.
``selection_quality`` stays ``NOT_ESTABLISHED``.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd

from trading_system.research.contextual_selection.csm import (
    SharedInformationAxis,
    TIE_FT_EQ_FIRST,
    build_legs,
    fk_turning_points,
    sp03_binding,
)
from trading_system.research.contextual_selection.analysis_lifecycle import (
    CLAIM_ENGINEERING,
    CLAIM_PARAPHRASE,
    STATE_INSUFFICIENT,
)

__all__ = [
    "EVENT_VIOLATION", "EVENT_CONTINUATION", "EVENT_NONE",
    "EVENT_AMBIGUOUS", "EVENTS", "EVENT_DEFINITIONS",
    "STATE_SCENARIO_DEVELOPING", "STATE_AWAITING_EVENT",
    "STATE_EVENT_OCCURRED", "STATE_PRIOR_VIEW_CHANGED", "STATE_NO_EDGE",
    "STATE_UNRESOLVED", "DECISION_STATES",
    "RUN_CONTEXT_REPLAY", "RUN_CONTEXT_LIVE",
    "Episode", "EpisodeExtractor", "ContextEventModel",
    "ContextualDecision", "decide", "extract_context",
    "chronological_split", "evaluate_model", "summarize_decisions",
    "EPISODE_HORIZON_BARS",
]

# --------------------------------------------------------------------- #
# predefined observable events (operational; existing components only)   #
# --------------------------------------------------------------------- #
EVENT_VIOLATION = "E-VIOLATION"
EVENT_CONTINUATION = "E-CONTINUATION"
EVENT_NONE = "E-NONE-IN-HORIZON"
EVENT_AMBIGUOUS = "E-AMBIGUOUS-SAME-BAR"
EVENTS = (EVENT_CONTINUATION, EVENT_VIOLATION, EVENT_NONE,
          EVENT_AMBIGUOUS)
# events that discriminate the two directional scenarios (the model
# compares ONLY these two; E-NONE / E-AMBIGUOUS are neutral and reported)
EVENTS_DIRECTIONAL = (EVENT_CONTINUATION, EVENT_VIOLATION)

EVENT_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    EVENT_VIOLATION: {
        "detector": "sp03-close-violation",
        "definition": (
            "a completed task-scale bar whose CLOSE is strictly beyond "
            "the current falsifier reference level on the falsifying "
            "side (SP-03 close-based binding; equality is not a "
            "crossing — TIE-CROSS-EQUAL-UNBOUND-V1)"),
        "basis": "SRS-SP03 + SRS-SP04 + SRS-TS5",
        "claim_class": CLAIM_PARAPHRASE,
        "scenario_support": "alternative",
        "provenance": ["SRS-SP03", "SRS-SP04", "SRS-TS5"],
    },
    EVENT_CONTINUATION: {
        "detector": "sp03-close-continuation",
        "definition": (
            "a completed task-scale bar whose CLOSE is strictly beyond "
            "the last confirmed leg's END extreme in the leg's own "
            "direction (SP-03 close-based binding of the leg-end "
            "reference; equality is not a crossing)"),
        "basis": "SRS-SP03 + SRS-FK (leg endpoints)",
        "claim_class": CLAIM_ENGINEERING,
        "scenario_support": "primary",
        "provenance": ["SRS-SP03", "SRS-FK", "SRS-CLAIM-SEM"],
    },
    EVENT_NONE: {
        "detector": "sp03-no-binding-in-horizon",
        "definition": (
            "neither a violation nor a continuation binding occurs on "
            "any completed task-scale bar within the declared episode "
            "horizon after the as-of"),
        "basis": "SRS-SP03 (absence of binding events)",
        "claim_class": CLAIM_ENGINEERING,
        "scenario_support": "neutral",
        "provenance": ["SRS-SP03", "SRS-CLAIM-SEM"],
    },
    EVENT_AMBIGUOUS: {
        "detector": "sp03-both-on-same-bar",
        "definition": (
            "violation and continuation bindings both occur first on "
            "the SAME completed bar inside the horizon (an unresolved "
            "case; reported, never resolved by an invented tie-break)"),
        "basis": "SRS-SP03",
        "claim_class": CLAIM_ENGINEERING,
        "scenario_support": "neutral",
        "provenance": ["SRS-SP03", "SRS-CLAIM-SEM"],
    },
}

# --------------------------------------------------------------------- #
# decision states                                                        #
# --------------------------------------------------------------------- #
STATE_SCENARIO_DEVELOPING = "SCENARIO_DEVELOPING"
STATE_AWAITING_EVENT = "AWAITING_EVENT"
STATE_EVENT_OCCURRED = "EVENT_OCCURRED"
STATE_PRIOR_VIEW_CHANGED = "PRIOR_VIEW_WEAKENED_OR_INVALIDATED"
STATE_NO_EDGE = "NO_EDGE"
STATE_UNRESOLVED = "UNRESOLVED"
DECISION_STATES = (STATE_SCENARIO_DEVELOPING, STATE_AWAITING_EVENT,
                   STATE_EVENT_OCCURRED, STATE_PRIOR_VIEW_CHANGED,
                   STATE_NO_EDGE, STATE_UNRESOLVED)

RUN_CONTEXT_REPLAY = "historical-replay"
RUN_CONTEXT_LIVE = "live-process"

# declared research configuration (NOT a market rule, NOT owner policy):
# the episode labeling horizon in task-scale bars.  Sensitivity is a
# research question; no source-derived candle count is claimed.
EPISODE_HORIZON_BARS = 24

_MODEL_STATUS = "provisional-unvalidated"


# --------------------------------------------------------------------- #
# causal context features (as-of facts only)                             #
# --------------------------------------------------------------------- #
def extract_context(record) -> Dict[str, str]:
    """Categorical causal context of ONE analysis record.

    Every value comes from what the analysis engine recorded at the as-of
    boundary (never from later data).
    """
    direction = "none"
    for i in record.interpretations:
        if i.interpretation_id == "I-primary":
            direction = str(i.data.get("direction") or "none")
            break
    ref_status = str(record.reference_status.get("status") or
                     "unresolved")
    sp05 = "none"
    for f in record.structural_facts:
        if f.kind == "derived-cross-scale-containment" and \
                f.inputs.get("scale") == "1h":
            sp05 = str(f.inputs.get("status") or "none")
            break
    statuses = [f.status for f in record.forecasts]
    if any(s == "pending" for s in statuses):
        fc = "pending"
    elif any(s in ("already_observed", "condition_observed")
             for s in statuses):
        fc = "observed"
    else:
        fc = "none"
    return {"direction": direction, "ref_status": ref_status,
            "sp05": sp05, "fc_status": fc}


def _context_key(ctx: Dict[str, str]) -> Tuple:
    return (ctx.get("direction"), ctx.get("ref_status"),
            ctx.get("sp05"), ctx.get("fc_status"))


# --------------------------------------------------------------------- #
# episodes (chronological; labels strictly from the future)              #
# --------------------------------------------------------------------- #
@dataclass
class Episode:
    episode_id: str
    as_of_time: pd.Timestamp
    as_of_bar: int
    context: Dict[str, str]
    label: Optional[str]           # None when excluded
    label_time: Optional[pd.Timestamp]
    label_detail: Dict[str, Any]
    exclusion_reason: Optional[str]
    window_end_bar: int            # label window closes here (exclusive)
    window_end_time: Optional[pd.Timestamp]  # completion time of the
    # last bar of the label window (training cutoff uses this)

    @property
    def usable(self) -> bool:
        return self.label is not None

    def to_record(self) -> dict:
        d = dataclasses.asdict(self)
        d["as_of_time"] = str(self.as_of_time)
        d["label_time"] = str(self.label_time) if self.label_time \
            else None
        d["window_end_time"] = str(self.window_end_time) \
            if self.window_end_time else None
        return d


class EpisodeExtractor:
    """Builds (context, label) episodes from analysis records.

    The context is read from the record (as-of facts).  The label is the
    FIRST predefined observable event inside
    ``(as_of_bar, as_of_bar + horizon_bars]``, computed from bars that
    completed AFTER the as-of — used ONLY as the training/evaluation
    label, never as a feature.
    """

    def __init__(self, *, frames: Dict[str, pd.DataFrame], k: int,
                 task_scale: str = "4h",
                 horizon_bars: int = EPISODE_HORIZON_BARS,
                 axis: Optional[SharedInformationAxis] = None,
                 instrument: str = "BTCUSDT") -> None:
        self.frames = frames
        self.k = k
        self.task_scale = task_scale
        self.horizon_bars = int(horizon_bars)
        task_index = pd.DatetimeIndex(frames[task_scale].index)
        self.axis = axis if axis is not None else SharedInformationAxis(
            f"{instrument}_{task_scale}_decision_labels", task_index)

    # ---- world reconstruction (deterministic; approved components) ----
    def _world(self, record):
        bars = self.frames[self.task_scale].iloc[:record.as_of_bar + 1]
        from trading_system.research.contextual_selection.csm import \
            Representation
        rep = Representation(family="F-K", view_id="C",
                             scale_label="coarse",
                             params=(("k", float(self.k)),))
        points = fk_turning_points(
            bars, self.k, rep, id_prefix="PT",
            allow_short_left=False, tie_policy=TIE_FT_EQ_FIRST,
            axis=self.axis)
        by_id = {p.candidate_id: p for p in points}
        legs = build_legs(points, rep, completed_only=True,
                          ambiguities=[])
        return by_id, legs

    def extract(self, record, run_id: str = "ep",
                seq: int = 0) -> Episode:
        ctx = extract_context(record)
        end_bar = int(record.as_of_bar) + self.horizon_bars
        bars_all = self.frames[self.task_scale]
        n = len(bars_all)
        window_last = min(end_bar, n - 1)
        window_end_time = (pd.Timestamp(bars_all.index[window_last])
                           if window_last >= 0 else None)
        base = dict(
            episode_id=f"EP-{run_id}-{seq:04d}",
            as_of_time=pd.Timestamp(record.as_of_time),
            as_of_bar=int(record.as_of_bar),
            context=ctx,
            label=None, label_time=None, label_detail={},
            exclusion_reason=None, window_end_bar=end_bar,
            window_end_time=window_end_time)

        # censored window: the horizon extends beyond the available data
        # — the label is unknown (never guessed)
        if end_bar > n - 1:
            base["exclusion_reason"] = (
                "label window extends beyond the available data "
                "(censored): the realized label is unknown and is "
                "never guessed")
            return Episode(**base)

        # required structural anchors: falsifier reference + leg end
        ref_id = record.reference_status.get("selected")
        end_id = None
        direction = ctx["direction"]
        for f in record.structural_facts:
            if f.kind == "derived-movement-direction":
                end_id = f.inputs.get("end_id")
                break
        if ref_id is None or end_id is None or direction == "none":
            base["exclusion_reason"] = (
                "no selected falsifier reference or no completed "
                "task-scale leg at this as-of: no definable label "
                "(unresolved case; reported, never labeled)")
            return Episode(**base)

        by_id, legs = self._world(record)
        ref = by_id.get(ref_id)
        end = by_id.get(end_id)
        if ref is None or end is None:
            base["exclusion_reason"] = (
                f"reference/leg-end not reconstructible at this as-of "
                f"({ref_id!r}/{end_id!r}): unresolved case")
            return Episode(**base)

        fals_side = "down" if ref.side == "low" else "up"
        cont_side = "up" if direction == "up" else "down"

        bars = bars_all
        first_viol: Optional[int] = None
        first_cont: Optional[int] = None
        for j in range(int(record.as_of_bar) + 1, window_last + 1):
            close = float(bars["close"].iloc[j])
            if first_viol is None and sp03_binding(
                    close, [ref], side=fals_side, tie_bound=False):
                first_viol = j
            if first_cont is None and sp03_binding(
                    close, [end], side=cont_side, tie_bound=False):
                first_cont = j
            if first_viol is not None and first_cont is not None:
                break

        if first_viol is not None and first_cont is not None:
            if first_viol == first_cont:
                base["label"] = EVENT_AMBIGUOUS
                base["label_time"] = pd.Timestamp(bars.index[first_viol])
                base["label_detail"] = {
                    "bar": first_viol,
                    "note": "both bindings first occur on the same bar"}
            elif first_viol < first_cont:
                base["label"] = EVENT_VIOLATION
                base["label_time"] = pd.Timestamp(bars.index[first_viol])
                base["label_detail"] = {"bar": first_viol,
                                        "side": fals_side}
            else:
                base["label"] = EVENT_CONTINUATION
                base["label_time"] = pd.Timestamp(bars.index[first_cont])
                base["label_detail"] = {"bar": first_cont,
                                        "side": cont_side}
        elif first_viol is not None:
            base["label"] = EVENT_VIOLATION
            base["label_time"] = pd.Timestamp(bars.index[first_viol])
            base["label_detail"] = {"bar": first_viol, "side": fals_side}
        elif first_cont is not None:
            base["label"] = EVENT_CONTINUATION
            base["label_time"] = pd.Timestamp(bars.index[first_cont])
            base["label_detail"] = {"bar": first_cont, "side": cont_side}
        else:
            base["label"] = EVENT_NONE
            base["label_detail"] = {
                "note": "no binding event within the declared horizon"}
        return Episode(**base)


# --------------------------------------------------------------------- #
# context-conditioned event model (frequency table; no invented weights) #
# --------------------------------------------------------------------- #
class ContextEventModel:
    """Per-context event counts from chronological training episodes.

    Ranking is ordinal and ties are EXPLICIT.  Nothing is smoothed and
    nothing is randomized.  Probabilities are never emitted: the model is
    not calibrated on a versioned out-of-sample set.
    """

    def __init__(self) -> None:
        self.counts: Dict[Tuple, Dict[str, int]] = {}
        self.n_episodes = 0
        self.trained_through: Optional[pd.Timestamp] = None

    def fit(self, episodes: Sequence[Episode]) -> None:
        for ep in episodes:
            if not ep.usable:
                continue
            key = _context_key(ep.context)
            bucket = self.counts.setdefault(
                key, {e: 0 for e in EVENTS})
            bucket[ep.label] += 1
            self.n_episodes += 1
            t = pd.Timestamp(ep.as_of_time)
            if self.trained_through is None or t > self.trained_through:
                self.trained_through = t

    def fit_before(self, episodes: Sequence[Episode],
                   cutoff_time: pd.Timestamp) -> None:
        """Fit ONLY episodes whose label windows CLOSED strictly before
        ``cutoff_time`` — no label can leak into a decision at or after
        the cutoff."""
        cutoff = pd.Timestamp(cutoff_time)
        keep = []
        for ep in episodes:
            if not ep.usable:
                continue
            if ep.window_end_time is not None and \
                    pd.Timestamp(ep.window_end_time) < cutoff:
                keep.append(ep)
        self.counts.clear()
        self.n_episodes = 0
        self.trained_through = None
        self.fit(keep)

    def support(self, context: Dict[str, str]) -> Dict[str, int]:
        bucket = self.counts.get(_context_key(context))
        if not bucket:
            return {"continuation": 0, "violation": 0}
        return {"continuation": bucket[EVENT_CONTINUATION],
                "violation": bucket[EVENT_VIOLATION]}

    def rank(self, context: Dict[str, str]) -> Dict[str, Any]:
        key = _context_key(context)
        bucket = self.counts.get(key)
        if not bucket:
            return {"status": "unsupported-context",
                    "ranking": [], "counts": {},
                    "context_key": list(key)}
        total = sum(bucket.values())
        if total == 0:
            return {"status": "unsupported-context",
                    "ranking": [], "counts": dict(bucket),
                    "context_key": list(key)}
        order = sorted(EVENTS, key=lambda e: (-bucket[e], e))
        ranking: List[Dict[str, Any]] = []
        rank_no = 0
        prev_count: Optional[int] = None
        for e in order:
            if bucket[e] != prev_count:
                rank_no += 1
                prev_count = bucket[e]
            ranking.append({"event": e, "count": bucket[e],
                            "rank": rank_no})
        top = [r["event"] for r in ranking if r["rank"] == 1]
        if len(top) == 1:
            status = "ranked"
        else:
            status = "tied"
        return {"status": status, "ranking": ranking,
                "counts": dict(bucket), "context_key": list(key)}


# --------------------------------------------------------------------- #
# the decision record                                                    #
# --------------------------------------------------------------------- #
@dataclass
class ContextualDecision:
    decision_id: str
    analysis_id: str
    analysis_version: int
    as_of_time: pd.Timestamp
    as_of_bar: int
    run_context: str
    state: str
    primary_interpretation_id: Optional[str]
    primary_working_view: Optional[str]
    primary_is_baseline: bool
    alternative_interpretation_ids: List[str]
    named_event: str
    named_event_definition: Dict[str, Any]
    next_discriminating_observation: str
    explanation: Dict[str, List[str]]
    model_ranking: List[dict]
    model_status: str
    model_counts: Dict[str, int]
    model_support: Dict[str, int]
    already_observed_conditions: List[dict]
    context: Dict[str, str]
    position_status: str
    selection_quality: str
    limitations: List[str]

    def to_record(self) -> dict:
        d = dataclasses.asdict(self)
        d["as_of_time"] = str(self.as_of_time)
        return d

    def to_explanation(self) -> str:
        L = [f"### decision {self.decision_id} — as of "
             f"{self.as_of_time} (UTC)  [{self.run_context}]",
             f"state: {self.state}"]
        if self.primary_working_view:
            tag = (" [no-edge baseline — not a preferred scenario]"
                   if self.primary_is_baseline else "")
            L.append(f"primary working interpretation: "
                     f"{self.primary_interpretation_id}{tag} — "
                     f"{self.primary_working_view}")
        if self.alternative_interpretation_ids:
            L.append("material alternatives: " +
                     ", ".join(self.alternative_interpretation_ids))
        L.append(f"named event: {self.named_event}")
        L.append("next discriminating observation: " +
                 self.next_discriminating_observation)
        for w in self.explanation.get("why", []):
            L.append(f"  why: {w}")
        for o in self.explanation.get("opposed", []):
            L.append(f"  opposed: {o}")
        for c in self.explanation.get("would_change", []):
            L.append(f"  would change: {c}")
        L.append(f"model: {self.model_status}; support "
                 f"continuation={self.model_support.get('continuation')}/"
                 f"violation={self.model_support.get('violation')}")
        L.append(f"position status: {self.position_status} | "
                 f"selection_quality = {self.selection_quality}")
        return "\n".join(L)


def _find_interpretation(record, interp_id: str):
    for i in record.interpretations:
        if i.interpretation_id == interp_id:
            return i
    return None


def _current_forecasts(record):
    ref = record.reference_status.get("selected")
    if ref is None:
        return list(record.forecasts)
    return [f for f in record.forecasts
            if f.market_state_snapshot.get("reference") == ref]


def decide(*, record, model: ContextEventModel,
           run_context: str = RUN_CONTEXT_REPLAY,
           decision_seq: int = 0) -> ContextualDecision:
    """Produce ONE contextual decision for ONE valid analysis record."""
    ctx = extract_context(record)
    ranking = model.rank(ctx)
    sup = model.support(ctx)
    primary = _find_interpretation(record, "I-primary")
    if primary is None:
        # reference unresolved but a directional scenario exists: this
        # is NOT insufficient input — the decision path continues (the
        # task reserves UNRESOLVED for invalid/insufficient REQUIRED
        # input, never for a missing binding preference)
        primary = _find_interpretation(record, "I-scenario")
    alt = _find_interpretation(record, "I-alt")

    limitations = [
        "selection_quality = NOT_ESTABLISHED",
        "the model ranking is PROVISIONAL and UNVALIDATED: not "
        "calibrated on a versioned out-of-sample set; probabilities are "
        "not emitted",
        "not ready for trade execution: analytical decisions only, no "
        "orders, no sizing, no execution connectivity",
        "run context: " + run_context + " (a historical replay is never "
        "an actual live market observation)",
        "P-ORIGIN-RESEARCH is research configuration, not owner-approved",
    ]

    # ---- UNRESOLVED: invalid / insufficient REQUIRED input only -------
    if record.lifecycle_state == STATE_INSUFFICIENT or primary is None:
        return ContextualDecision(
            decision_id=f"DEC-{record.run_id}-{decision_seq:04d}",
            analysis_id=record.analysis_id,
            analysis_version=record.analysis_version,
            as_of_time=pd.Timestamp(record.as_of_time),
            as_of_bar=int(record.as_of_bar),
            run_context=run_context,
            state=STATE_UNRESOLVED,
            primary_interpretation_id=None,
            primary_working_view=None,
            primary_is_baseline=True,
            alternative_interpretation_ids=[],
            named_event="the completion and causal confirmation of the "
                        f"first task-scale F-K leg (k={_k_of(record)})",
            named_event_definition={
                "detector": "fk-leg-completion",
                "definition": "the first completed task-scale F-K leg",
                "basis": "SRS-FK", "claim_class": CLAIM_ENGINEERING},
            next_discriminating_observation="the first completed "
                "task-scale leg's existence and direction",
            explanation={
                "why": ["required structural input is insufficient at "
                        "this as-of: no completed task-scale leg exists "
                        "yet"],
                "opposed": [],
                "would_change": ["the first completed task-scale leg"]},
            model_ranking=ranking.get("ranking", []),
            model_status=_MODEL_STATUS,
            model_counts=ranking.get("counts", {}),
            model_support=sup,
            already_observed_conditions=[],
            context=ctx,
            position_status="absent",
            selection_quality="NOT_ESTABLISHED",
            limitations=limitations + [
                "UNRESOLVED is used here only because required input is "
                "insufficient — not as a generic abstention"])

    # ---- scenario choice (model evidence; explicit ties) -------------
    if sup["continuation"] > sup["violation"]:
        chosen = "continuation"
        primary_id = "I-primary"
    elif sup["violation"] > sup["continuation"]:
        chosen = "reversal"
        primary_id = "I-alt"
    else:
        chosen = None                      # evidence does not distinguish
        primary_id = "I-primary"           # structural no-edge baseline
    chosen_interp = (_find_interpretation(record, primary_id)
                     or primary)

    # ---- state (priority order; one explicit state) -------------------
    cur_fcs = _current_forecasts(record)
    observed_fcs = [f for f in cur_fcs
                    if f.status in ("already_observed",
                                    "condition_observed")]
    pending_fcs = [f for f in cur_fcs if f.status == "pending"]
    already = [{"forecast_id": f.forecast_id, "version": f.version,
                "if_event": f.if_event,
                "observed_before_record": f.observed_before_record,
                "status": f.status}
               for f in observed_fcs]
    prior_view_broken = primary.status in ("weakened", "contradicted",
                                           "invalidated")

    if record.revision_reason or observed_fcs:
        state = STATE_EVENT_OCCURRED
        named_event = (observed_fcs[-1].if_event if observed_fcs else
                       record.revision_reason)
    elif prior_view_broken:
        state = STATE_PRIOR_VIEW_CHANGED
        named_event = (primary.next_discriminating_observation or
                       "the next completed task-scale observation")
    elif chosen is None:
        state = STATE_NO_EDGE
        named_event = _no_edge_discriminator(record, ctx)
    elif record.reference_status.get("status") == "unresolved":
        # a direction is favored but the falsifier reference is not
        # precisely resolved: the awaiting is reference resolution /
        # the discriminating binding — not a generic abstention
        state = STATE_NO_EDGE
        named_event = _no_edge_discriminator(record, ctx)
    elif pending_fcs:
        state = STATE_AWAITING_EVENT
        named_event = pending_fcs[-1].if_event
    else:
        state = STATE_SCENARIO_DEVELOPING
        top = next((r["event"] for r in ranking.get("ranking", [])
                    if r["rank"] == 1 and r["event"] in
                    EVENTS_DIRECTIONAL), None)
        named_event = (
            f"{top} — {EVENT_DEFINITIONS[top]['definition']}"
            if top else _no_edge_discriminator(record, ctx))

    # ---- explanation (why / opposed / would change) -------------------
    why = [
        f"causal context at this as-of: {ctx}",
        f"model evidence (training episodes in this context): "
        f"continuation={sup['continuation']}, "
        f"violation={sup['violation']} "
        f"({ranking['status']}, provisional-unvalidated ranking)",
    ]
    if chosen_interp is not None:
        why.append(
            f"working interpretation {chosen_interp.interpretation_id}: "
            f"{chosen_interp.description}")
        why.extend(chosen_interp.supporting_evidence[:3])
    if state == STATE_NO_EDGE:
        why.append("the model does not strictly distinguish the "
                   "scenarios in this context: the explicit decision is "
                   "NO_EDGE (not an abstention, not UNRESOLVED)")
    opposed = []
    if primary is not None:
        opposed.extend(primary.opposed_evidence[:3])
    if alt is not None and chosen_interp is not alt:
        opposed.extend(alt.would_be_supported_by[:2])
    elif primary is not None and chosen_interp is not primary:
        opposed.extend(primary.would_be_supported_by[:2])
    would_change = []
    if chosen_interp is not None:
        would_change.extend(chosen_interp.invalidating_observations[:2])
    would_change.append(named_event)
    if state == STATE_EVENT_OCCURRED and already:
        would_change.append(
            "the watched condition already occurred before/at this "
            "record (observed_before_record flags below) — it is NOT "
            "described as a pre-event prediction; the analysis is "
            "updated instead of waiting")

    return ContextualDecision(
        decision_id=f"DEC-{record.run_id}-{decision_seq:04d}",
        analysis_id=record.analysis_id,
        analysis_version=record.analysis_version,
        as_of_time=pd.Timestamp(record.as_of_time),
        as_of_bar=int(record.as_of_bar),
        run_context=run_context,
        state=state,
        primary_interpretation_id=chosen_interp.interpretation_id
        if chosen_interp else None,
        primary_working_view=chosen_interp.description
        if chosen_interp else None,
        primary_is_baseline=(chosen is None),
        alternative_interpretation_ids=[
            i.interpretation_id for i in record.interpretations
            if chosen_interp is None or
            i.interpretation_id != chosen_interp.interpretation_id],
        named_event=str(named_event),
        named_event_definition=_named_event_definition(named_event),
        next_discriminating_observation=(
            chosen_interp.next_discriminating_observation
            if chosen_interp is not None and
            chosen_interp.next_discriminating_observation
            else _no_edge_discriminator(record, ctx)),
        explanation={"why": why, "opposed": opposed,
                     "would_change": would_change},
        model_ranking=ranking.get("ranking", []),
        model_status=_MODEL_STATUS,
        model_counts=ranking.get("counts", {}),
        model_support=sup,
        already_observed_conditions=already,
        context=ctx,
        position_status="absent",
        selection_quality="NOT_ESTABLISHED",
        limitations=limitations)


def _k_of(record) -> str:
    for f in record.structural_facts:
        if f.kind == "derived-movement-direction":
            desc = f.description
            if "F-K k=" in desc:
                return desc.split("F-K k=")[1].split(",")[0].split(")")[0]
    return "?"


def _no_edge_discriminator(record, ctx) -> str:
    ref = record.reference_status.get("selected") or \
        "the unresolved reference set"
    return (
        f"the next completed task-scale bar's CLOSE determining which "
        f"binding fires first: {EVENT_VIOLATION} (SP-03 close beyond the "
        f"falsifier reference {ref} on its falsifying side) or "
        f"{EVENT_CONTINUATION} (SP-03 close beyond the last leg's end "
        f"extreme in the leg direction) — until one fires the decision "
        f"stays NO_EDGE")


def _named_event_definition(named_event: str) -> Dict[str, Any]:
    for e, d in EVENT_DEFINITIONS.items():
        if named_event.startswith(e):
            return dict(d)
    return {"detector": "recorded-condition", "definition": named_event,
            "basis": "SRS-TS5 + SRS-SP03", "claim_class": CLAIM_PARAPHRASE}


# --------------------------------------------------------------------- #
# chronological evaluation (no trade-profit labels)                      #
# --------------------------------------------------------------------- #
def chronological_split(episodes: Sequence[Episode],
                        train_fraction: float = 2 / 3
                        ) -> Tuple[List[Episode], List[Episode]]:
    """Deterministic chronological split: earlier episodes fit, strictly
    later episodes evaluate.  No shuffling, ever."""
    usable = sorted([e for e in episodes if e.usable],
                    key=lambda e: e.as_of_time)
    if not usable:
        return [], []
    cut = int(len(usable) * train_fraction)
    cut = max(1, min(cut, len(usable) - 1)) if len(usable) > 1 else 1
    train, ev = usable[:cut], usable[cut:]
    if ev and train:
        assert max(e.as_of_time for e in train) < \
            min(e.as_of_time for e in ev), \
            "chronological separation violated"
    return train, ev


def evaluate_model(model: ContextEventModel,
                   episodes: Sequence[Episode]) -> Dict[str, Any]:
    """Out-of-sample event-forecast results on later episodes.

    Reports coverage and results honestly; ties count as no-call, never
    as success.  Labels are structural event identities only — no
    trade-profit/loss label exists anywhere in this path.
    """
    conf: Dict[str, Dict[str, int]] = {}
    hit = no_call = miss = 0
    label_counts: Dict[str, int] = {}
    for ep in episodes:
        if not ep.usable:
            continue
        label_counts[ep.label] = label_counts.get(ep.label, 0) + 1
        r = model.rank(ep.context)
        top = [x["event"] for x in r.get("ranking", [])
               if x["rank"] == 1 and x["event"] in EVENTS_DIRECTIONAL]
        if r.get("status") != "ranked" or len(top) != 1:
            no_call += 1
            pred = "(no-call)"
        else:
            pred = top[0]
            if pred == ep.label:
                hit += 1
            else:
                miss += 1
        conf.setdefault(pred, {})
        conf[pred][ep.label] = conf[pred].get(ep.label, 0) + 1
    total = hit + miss + no_call
    return {
        "n_eval_episodes": total,
        "coverage": round((hit + miss) / total, 4) if total else None,
        "hit": hit, "miss": miss, "no_call": no_call,
        "hit_rate_on_covered": round(hit / (hit + miss), 4)
        if (hit + miss) else None,
        "hit_rate_overall": round(hit / total, 4) if total else None,
        "confusion_predicted_rows_realized_cols": conf,
        "label_distribution": label_counts,
        "labels_note": "structural event identities only; win/loss here "
                       "means scenario continuation/violation — NEVER "
                       "trade profit/loss",
    }


def summarize_decisions(decisions: Sequence[ContextualDecision]
                        ) -> Dict[str, Any]:
    states: Dict[str, int] = {}
    no_edge = 0
    no_edge_contexts: Dict[str, int] = {}
    for d in decisions:
        states[d.state] = states.get(d.state, 0) + 1
        if d.state == STATE_NO_EDGE:
            no_edge += 1
            key = (f"model support continuation="
                   f"{d.model_support.get('continuation')} vs "
                   f"violation={d.model_support.get('violation')}")
            no_edge_contexts[key] = no_edge_contexts.get(key, 0) + 1
    total = len(decisions) or 1
    return {
        "n_decisions": len(decisions),
        "states": states,
        "no_edge_count": no_edge,
        "no_edge_frequency": round(no_edge / total, 4),
        "no_edge_note": "NO_EDGE is an explicit decision (evidence does "
                        "not distinguish the scenarios) and is NEVER "
                        "counted as success",
        "no_edge_reasons": no_edge_contexts,
    }
