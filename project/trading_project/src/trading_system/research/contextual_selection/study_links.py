"""Study links V1 — connect the documented Huddleston study
(``docs/research/huddleston_study/corpus_full_pass.json`` + the extended
five-video study) to the EXISTING causal path: ``AnalysisEngine`` ->
``InterpretationLedger`` -> ``MonitoringLoop``.

This module encodes THREE documented relationships (not a recipe; no
``BOS + FVG + SWEEP = BUY`` exists anywhere here):

R1  OB16-A — candidate order-block-like reference:
    * an explicit candidate state machine: CANDIDATE (shape matched a
      declared research definition) -> AWAITING_CONFIRMATION ->
      CONFIRMED (declared later-evidence event occurred) / INVALIDATED
      (a declared condition of the candidate's role failed) /
      INSUFFICIENT_INFORMATION (needed data unavailable).  Transitions
      carry evidence and are recorded in the ledger — not only comments.
    * higher-frame context changes the candidate's ROLE, not its
      existence: a visually bearish candidate under a bullish
      higher-frame context is NOT a bearish trend reference (source:
      25:00-25:43) but MAY remain a legitimate reaction/pause
      reference.  The rule is NOT "higher frame bullish => reject
      bearish"; when the evidence does not justify a preference the
      engine records UNDETERMINED and does not force a pick.
    * sequence separation: HF context established -> candidate formed ->
      later confirmation (or absence) -> possible revisit -> revision;
      confirmation is NEVER back-filled into the formation moment; if
      two events may share one bar and OHLC cannot order them, ordering
      is recorded UNKNOWN and the engine refuses to pick the flattering
      order (finer available data may resolve it later).

R2  FVG24-A — time provenance and revocable selection:
    every candidate carries timestamp, session/timezone, bar
    construction convention and timeframe, plus the eligibility
    information known at selection time; when new information removes
    eligibility, the selection is REVOKED (or SUSPENDED) with the
    original preserved and the revision recorded as a CORRECTION — never
    as a fulfilled prediction.  The 9:30/9:31 first-gap clock convention
    is SESSION-SCOPED (``SessionClockConvention``); the engine runs
    without it.

R3  E12-A — higher-frame hypothesis with explicit failure reference:
    crossing the failure reference SUSPENDS the hypothesis and demands
    more information ("if it goes above that then I'm probably wrong in
    my analysis / I demand more information") — suspension semantics,
    never an automatic flip to the opposite hypothesis.

LAYERS: every record separates DIRECT OBSERVATION / DERIVATION under a
declared definition / CONTEXTUAL INTERPRETATION / UNKNOWN-UNSUPPORTED
(resting stops, participant intent, causes, intra-bar order, trading
centres, validated trades, "any chart in the world" — all unsupported).

Research configuration constants below are NAMED and declared as such:
they are NOT source claims, NOT market truths, and NOT owner policy.
``selection_quality = NOT_ESTABLISHED``.
"""

from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass, field
from pathlib import Path
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

__all__ = [
    "CORPUS_PATH", "load_corpus", "RELATIONSHIP_REGISTER",
    "RESEARCH_CFG_NEAR_SUPPORT_DISTANCE_FRACTION",
    "SessionClockConvention", "US_INDEX_FIRST_GAP_SESSION_CLOCK",
    "STATE_CANDIDATE", "STATE_AWAITING_CONFIRMATION", "STATE_CONFIRMED",
    "STATE_INVALIDATED", "STATE_INSUFFICIENT", "CANDIDATE_STATES",
    "ROLE_TREND", "ROLE_REACTION_PAUSE", "ROLE_UNDETERMINED",
    "OBLikeCandidate", "HigherFrameHypothesis",
    "TimeProvenanceSelection", "StudyReasoningLayer",
    "UNKNOWN_ORDERING", "LAYER_OBSERVATION", "LAYER_DERIVATION",
    "LAYER_INTERPRETATION", "LAYER_UNKNOWN",
]

HERE = Path(__file__).resolve()
CORPUS_PATH = (HERE.parents[4] / "docs" / "research" /
               "huddleston_study" / "corpus_full_pass.json")

# --------------------------------------------------------------------- #
# research configuration — NOT source claims, NOT market truths          #
# --------------------------------------------------------------------- #
# The source explicitly leaves "near support" operationally undefined
# (OB16-A ambiguities).  This fraction exists ONLY to exercise the
# candidate path and tests.  It is a declared research configuration,
# not a source claim, not a market truth, and not owner policy.
RESEARCH_CFG_NEAR_SUPPORT_DISTANCE_FRACTION = 0.01

UNKNOWN_ORDERING = "UNKNOWN"

LAYER_OBSERVATION = "DIRECT_OBSERVATION"
LAYER_DERIVATION = "DERIVATION"
LAYER_INTERPRETATION = "CONTEXTUAL_INTERPRETATION"
LAYER_UNKNOWN = "UNKNOWN_UNSUPPORTED"


# --------------------------------------------------------------------- #
# source register                                                        #
# --------------------------------------------------------------------- #
def load_corpus() -> dict:
    with open(CORPUS_PATH, encoding="utf-8") as fh:
        return json.load(fh)


RELATIONSHIP_REGISTER: List[Dict[str, Any]] = [
    {
        "relationship_id": "R1-OB-CANDIDATE-LIFECYCLE",
        "source_examples": ["OB16-A"],
        "claim_class": "ENGINEERING_INTERPRETATION",
        "source_support": [
            "OB16-A explicit_identification (DIRECT_STATEMENT): slide "
            "specifies bullish candidate down-close bar near support, "
            "validation by a later bar trading through its high, "
            "possible return",
            "OB16-A short_quotes (DIRECT_STATEMENT, slide 01:52): "
            "'when the high of the lowest down close candle ... is "
            "traded through'; 'We don't know that yet until at a later "
            "time'",
            "OB16-A change (DIRECT_STATEMENT): bearish-looking block is "
            "NOT a sell cue under bullish higher-frame context",
        ],
        "engine_interpretation": [
            "state machine CANDIDATE/AWAITING_CONFIRMATION/CONFIRMED/"
            "INVALIDATED/INSUFFICIENT_INFORMATION with ledger-recorded "
            "transitions",
            "role assignment under a declared task (trend-continuation "
            "vs reaction/pause) with alternatives and change conditions",
            "sequence separation with UNKNOWN ordering on unresolvable "
            "same-bar events",
        ],
        "not_established": [
            "'near support' operational definition (source leaves open; "
            "RESEARCH_CFG constant exists only to exercise tests)",
            "any universal entry, stop, target, or profitability",
        ],
    },
    {
        "relationship_id": "R2-TIME-PROVENANCE-REVOCABLE-SELECTION",
        "source_examples": ["FVG24-A"],
        "claim_class": "ENGINEERING_INTERPRETATION",
        "source_support": [
            "FVG24-A explicit_identification (DIRECT_STATEMENT): the "
            "9:30 candle cannot be the first qualifying gap under his "
            "stated convention; first candidate 9:31+",
            "FVG24-A short_quotes (DIRECT_STATEMENT ~75:02/75:12): "
            "'You can't be on your 9.30 candle...'; 'I was incorrect by "
            "saying all that stuff'",
        ],
        "engine_interpretation": [
            "time provenance on every candidate (timestamp, "
            "session/timezone, bar convention, timeframe)",
            "revocation recorded as a CORRECTION with the original "
            "selection preserved, never as a fulfilled prediction",
        ],
        "not_established": [
            "the 9:30/9:31 convention beyond its session scope "
            "(engine runs without it)",
        ],
    },
    {
        "relationship_id": "R3-HYPOTHESIS-SUSPENSION",
        "source_examples": ["E12-A"],
        "claim_class": "ENGINEERING_INTERPRETATION",
        "source_support": [
            "E12-A short_quotes (DIRECT_STATEMENT ~11:31/11:39): 'if it "
            "goes above that then I'm probably wrong in my analysis'; "
            "'I demand more information'",
            "E12-A change (PARAPHRASE): pause/reassess rather than "
            "mechanically reverse",
        ],
        "engine_interpretation": [
            "failure-reference crossing SUSPENDS the hypothesis and "
            "requests more information; no automatic opposite hypothesis "
            "is generated",
        ],
        "not_established": [
            "that the speaker's earlier forecast was independently "
            "pre-registered (speaker assertion)",
        ],
    },
]


# --------------------------------------------------------------------- #
# session-scoped clock convention (R2) — optional; engine runs without   #
# --------------------------------------------------------------------- #
@dataclass(frozen=True)
class SessionClockConvention:
    name: str
    scope: str                       # e.g. "US-index session 2024-09-16"
    timezone: str
    bar_convention: str
    first_eligible_minute: int       # minutes after session start
    note: str

    def eligible_at(self, t: pd.Timestamp, session_start: pd.Timestamp
                    ) -> bool:
        return (pd.Timestamp(t) - pd.Timestamp(session_start)) >= \
            pd.Timedelta(minutes=self.first_eligible_minute)


# FVG24-A's stated convention, SESSION-SCOPED (9:30 candle excluded,
# first candidate 9:31+).  NOT a market-wide law.  Passing None disables
# it entirely.
US_INDEX_FIRST_GAP_SESSION_CLOCK = SessionClockConvention(
    name="US-index-first-gap-9-31",
    scope="the single 2024-09-16 intraday lesson session (NOT global)",
    timezone="America/New_York (platform display, UTC-5)",
    bar_convention="1-minute chart as displayed",
    first_eligible_minute=1,
    note="DIRECT_STATEMENT FVG24-A ~75:02; session-specific first-gap "
         "qualification only")


# --------------------------------------------------------------------- #
# candidate state machine (R1)                                           #
# --------------------------------------------------------------------- #
STATE_CANDIDATE = "CANDIDATE"
STATE_AWAITING_CONFIRMATION = "AWAITING_CONFIRMATION"
STATE_CONFIRMED = "CONFIRMED"
STATE_INVALIDATED = "INVALIDATED"
STATE_INSUFFICIENT = "INSUFFICIENT_INFORMATION"
CANDIDATE_STATES = (STATE_CANDIDATE, STATE_AWAITING_CONFIRMATION,
                    STATE_CONFIRMED, STATE_INVALIDATED, STATE_INSUFFICIENT)

ROLE_TREND = "TREND_CONTINUATION_REFERENCE"
ROLE_REACTION_PAUSE = "REACTION_PAUSE_REFERENCE"
ROLE_UNDETERMINED = "UNDETERMINED"


@dataclass
class OBLikeCandidate:
    candidate_id: str
    direction: str                   # "bullish" | "bearish"
    bar_index: int
    bar_time: pd.Timestamp
    open: float
    high: float
    low: float
    close: float
    context_ref_id: str              # the contextual support/resistance
    context_ref_level: float
    # --- time provenance (R2) ---
    timezone: str = "UTC"
    bar_convention: str = ("closed bars only; source rows resampled to "
                           "the task scale (completion-labelled)")
    timeframe: str = "task-scale"
    eligibility: Dict[str, Any] = field(default_factory=dict)
    # --- state machine ---
    state: str = STATE_CANDIDATE
    role: str = ROLE_UNDETERMINED
    role_assignments: List[dict] = field(default_factory=list)
    events: List[dict] = field(default_factory=list)   # ordered facts
    ordering: Optional[str] = None   # UNKNOWN when same-bar order is
                                     # not inferable from OHLC
    ambiguous_bar: Optional[int] = None
    fine_touches: Dict[str, Optional[pd.Timestamp]] = field(
        default_factory=dict)

    def to_record(self) -> dict:
        d = dataclasses.asdict(self)
        d["bar_time"] = str(self.bar_time)
        return _jsonable(d)

    # ---- transitions (append-only; each carries evidence) ----
    def _step(self, new_state: str, *, at_bar: int,
              at_time: pd.Timestamp, evidence: Any, reason: str,
              layer: str = LAYER_DERIVATION) -> dict:
        ev = {"kind": "state_transition", "from": self.state,
              "to": new_state, "at_bar": int(at_bar),
              "at": pd.Timestamp(at_time), "evidence": evidence,
              "reason": reason, "layer": layer}
        self.events.append(ev)
        self.state = new_state
        return ev

    def to_awaiting(self, *, at_bar, at_time, evidence) -> dict:
        return self._step(STATE_AWAITING_CONFIRMATION, at_bar=at_bar,
                          at_time=at_time, evidence=evidence,
                          reason="shape matched the declared research "
                                 "definition; later-evidence event not "
                                 "yet observed")

    def to_confirmed(self, *, at_bar, at_time, evidence) -> dict:
        return self._step(STATE_CONFIRMED, at_bar=at_bar,
                          at_time=at_time, evidence=evidence,
                          reason="declared confirmation event observed "
                                 "(later bar traded through the "
                                 "candidate extreme); recorded at the "
                                 "evidence bar, never back-filled")

    def to_invalidated(self, *, at_bar, at_time, evidence, reason) -> dict:
        return self._step(STATE_INVALIDATED, at_bar=at_bar,
                          at_time=at_time, evidence=evidence,
                          reason=reason)

    def to_insufficient(self, *, at_bar, at_time, reason) -> dict:
        return self._step(STATE_INSUFFICIENT, at_bar=at_bar,
                          at_time=at_time, evidence=None,
                          reason=reason,
                          layer=LAYER_UNKNOWN)


# --------------------------------------------------------------------- #
# higher-frame hypothesis with failure reference (R3)                    #
# --------------------------------------------------------------------- #
@dataclass
class HigherFrameHypothesis:
    hypothesis_id: str
    statement: str
    failure_reference_level: float
    failure_reference_id: str
    failure_side: str                # side whose crossing fails it
    status: str = "ACTIVE"
    events: List[dict] = field(default_factory=list)

    def review(self, *, bar_time: pd.Timestamp, bar_high: float,
               bar_low: float, bar_close: float) -> Optional[dict]:
        """Crossing the failure reference SUSPENDS (never reverses)."""
        if self.status != "ACTIVE":
            return None
        crossed = (self.failure_side == "up" and
                   bar_close > self.failure_reference_level) or \
                  (self.failure_side == "down" and
                   bar_close < self.failure_reference_level)
        if not crossed:
            return None
        ev = {"kind": "hypothesis_suspension", "at": pd.Timestamp(bar_time),
              "evidence": f"close {bar_close} beyond failure reference "
                          f"{self.failure_reference_level} "
                          f"(side {self.failure_side})",
              "reason": "failure reference crossed: SUSPEND and demand "
                        "more information (source semantics, E12-A); "
                        "no automatic opposite hypothesis is generated",
              "layer": LAYER_INTERPRETATION}
        self.events.append(ev)
        self.status = "SUSPENDED"
        return ev

    def to_record(self) -> dict:
        return _jsonable(dataclasses.asdict(self))


# --------------------------------------------------------------------- #
# revocable selection with time provenance (R2)                          #
# --------------------------------------------------------------------- #
@dataclass
class TimeProvenanceSelection:
    selection_id: str
    subject_id: str
    selected_at: pd.Timestamp
    timezone: str
    bar_convention: str
    timeframe: str
    eligibility: Dict[str, Any]
    status: str = "SELECTED"
    revisions: List[dict] = field(default_factory=list)

    def revoke(self, *, reason: str, evidence: Any,
               revised_to: Optional[str]) -> dict:
        """A revocation is a CORRECTION — never a fulfilled prediction.
        The original selection is preserved in ``revisions``."""
        rec = {"kind": "selection_correction", "action": "REVOKE",
               "original": dataclasses.asdict(self),
               "reason": reason, "evidence": evidence,
               "revised_to": revised_to or "SUSPENDED",
               "note": "correction of temporal/eligibility "
                       "classification; NOT a fulfilled prediction",
               "layer": LAYER_INTERPRETATION}
        self.revisions.append(rec)
        self.status = "REVOKED" if revised_to else "SUSPENDED"
        return rec

    def to_record(self) -> dict:
        d = dataclasses.asdict(self)
        d["selected_at"] = str(self.selected_at)
        return _jsonable(d)


# --------------------------------------------------------------------- #
# the reasoning layer (flows through the existing monitoring path)       #
# --------------------------------------------------------------------- #
def assign_role(*, candidate_direction: str, hf_trend: str,
                task: str) -> Dict[str, Any]:
    """Role is evaluated FOR A DECLARED TASK against the higher-frame
    context — never an automatic accept/reject of a shape.

    * direction agrees with hf_trend -> TREND_CONTINUATION_REFERENCE is
      preferred (with the alternative recorded).
    * direction opposes hf_trend -> the trend role is NOT assigned, but
      the candidate remains eligible as REACTION_PAUSE_REFERENCE
      (source: OB16-A 25:00-25:43 / 34:00-35:15) — this is NOT
      "higher frame bullish => reject bearish".
    * no established hf context (or evidence does not discriminate) ->
      UNDETERMINED with reasons and the discriminating evidence needed.
    """
    aligned = (candidate_direction == "bullish" and hf_trend == "up") or \
              (candidate_direction == "bearish" and hf_trend == "down")
    opposed = (candidate_direction == "bullish" and hf_trend == "down") or \
              (candidate_direction == "bearish" and hf_trend == "up")
    out: Dict[str, Any] = {"task": task,
                           "hf_trend": hf_trend,
                           "candidate_direction": candidate_direction,
                           "alternatives": [], "would_change": []}
    if hf_trend in ("none", "unknown"):
        out.update(role=ROLE_UNDETERMINED,
                   reasons=["no established higher-frame context at "
                            "this as-of; the evidence does not "
                            "discriminate roles"],
                   discriminating_evidence_needed=[
                       "an established higher-frame context (completed "
                       "structure) before the candidate's evaluation",
                       "a declared task the reference is evaluated for"])
        return out
    if task == "trend-continuation":
        if aligned:
            out.update(role=ROLE_TREND,
                       reasons=["candidate direction agrees with the "
                                "established higher-frame context for "
                                "the declared trend-continuation task"],
                       preferred=True)
            out["alternatives"].append(
                f"{ROLE_REACTION_PAUSE}: also possible as a "
                f"reaction/pause reference; not preferred for this task")
        else:
            # source-guided: NOT a trend reference, BUT still a
            # legitimate reaction/pause reference — never rejected
            out.update(role=ROLE_REACTION_PAUSE,
                       reasons=["candidate direction opposes the "
                                "established higher-frame context; the "
                                "trend-continuation role is NOT "
                                "assigned (OB16-A 25:00-25:43) while "
                                "the candidate remains a legitimate "
                                "reaction/pause reference (34:00-35:15)"],
                       preferred=True)
            out["alternatives"].append(
                f"{ROLE_TREND}: excluded FOR THIS TASK by the "
                f"higher-frame context — the candidate itself is NOT "
                f"rejected")
        out["would_change"].append(
            "a higher-frame structure change would re-open the trend "
            "role evaluation")
    else:   # reaction-pause task
        out.update(role=ROLE_REACTION_PAUSE,
                   reasons=["declared reaction/pause task: the "
                            "candidate is monitored as a possible "
                            "reaction/pause reference"],
                   preferred=True)
        trend_note = "eligible" if aligned else "not assigned for this task"
        out["alternatives"].append(f"{ROLE_TREND}: {trend_note}")
    return out


class StudyReasoningLayer:
    """Detects OB-like candidates against the causal world of the
    current boundary, maintains their state machine and roles, runs
    hypothesis reviews and revocable selections, and records every
    transition in the EXISTING InterpretationLedger.
    """

    def __init__(self, *, run_id: str = "study-v1", k: int = 2,
                 task_scale: str = "4h",
                 task: str = "trend-continuation",
                 session_clock: Optional[SessionClockConvention] = None
                 ) -> None:
        self.run_id = run_id
        self.k = k
        self.task_scale = task_scale
        self.task = task
        self.session_clock = session_clock
        self.candidates: List[OBLikeCandidate] = []
        self.hypotheses: List[HigherFrameHypothesis] = []
        self.selections: List[TimeProvenanceSelection] = []
        self.seq_facts: List[dict] = []
        self.hf_context: Dict[str, Any] = {"trend": "unknown",
                                           "evidence": []}
        self._scan_upto = -1
        self._ledger_uids: Dict[str, str] = {}
        self._cand_seq = 0

    # ---- main hooks (called by the EXISTING MonitoringLoop) ----------
    def on_boundary(self, record, frames: Dict[str, pd.DataFrame],
                    ledger=None) -> List[dict]:
        changes: List[dict] = []
        bars = frames[self.task_scale]
        axis = SharedInformationAxis(f"{self.run_id}_study",
                                     pd.DatetimeIndex(bars.index))
        world = self._world(bars, record, axis)
        # (1) higher-frame context (sequence fact #1)
        changes += self._update_hf_context(record)
        # (2..) candidates: detect new, update existing
        changes += self._scan_for_candidates(record, bars, world)
        changes += self._update_candidates(record, bars, world)
        # role evaluation under the established hf context (declared
        # task; non-forced — records alternatives and change conditions)
        for c in self.candidates:
            if c.role_assignments or \
                    self.hf_context.get("trend") in ("unknown", None):
                continue
            verdict = assign_role(candidate_direction=c.direction,
                                  hf_trend=self.hf_context["trend"],
                                  task=self.task)
            c.role = verdict["role"]
            c.role_assignments.append(verdict)
            self.seq_facts.append({
                "kind": "ROLE_EVALUATED", "at":
                    pd.Timestamp(record.as_of_time),
                "candidate_id": c.candidate_id, "role": c.role,
                "layer": LAYER_INTERPRETATION})
            changes.append({
                "aspect": "candidate_role", "before": ROLE_UNDETERMINED,
                "after": c.role,
                "reason": verdict["reasons"][0],
                "evidence": [c.candidate_id] +
                            list(verdict.get("alternatives", []))})
        # hypothesis reviews + selections are event-driven via helpers
        if ledger is not None:
            for c in self.candidates:
                self._ledger_sync(c, ledger)
        return changes

    def on_observation(self, row: dict) -> List[dict]:
        """Finer-grained re-evaluation on actually available data (the
        1m observation): resolves same-bar ordering for an ambiguous
        candidate and confirms on the finer bar when it can."""
        changes: List[dict] = []
        t = pd.Timestamp(row["time"])
        for c in self.candidates:
            if c.ambiguous_bar is None or c.state != \
                    STATE_AWAITING_CONFIRMATION:
                continue
            if c.ordering != UNKNOWN_ORDERING and \
                    c.ordering is not None:
                continue
            # record first fine touches of the confirm level and of the
            # revisit boundary; ordering becomes known only if the
            # touches land on DIFFERENT fine bars
            if c.direction == "bullish":
                conf_touch = float(row["high"]) > c.high
                rev_touch = float(row["low"]) <= c.low
            else:
                conf_touch = float(row["low"]) < c.low
                rev_touch = float(row["high"]) >= c.high
            if conf_touch and c.fine_touches.get("confirm") is None:
                c.fine_touches["confirm"] = t
            if rev_touch and c.fine_touches.get("revisit") is None:
                c.fine_touches["revisit"] = t
            cf, rv = c.fine_touches.get("confirm"), \
                c.fine_touches.get("revisit")
            if cf is not None and rv is not None:
                if cf == rv:
                    c.ordering = UNKNOWN_ORDERING
                    changes.append({
                        "aspect": "candidate_ordering",
                        "before": "UNKNOWN", "after": "UNKNOWN",
                        "reason": "both events share one fine bar: "
                                  "ordering stays UNKNOWN",
                        "evidence": [c.candidate_id, str(cf)]})
                else:
                    order = "confirmation-first" if cf < rv else \
                        "revisit-first"
                    c.ordering = order
                    c.events.append({
                        "kind": "ordering_resolved_by_finer_data",
                        "at": t, "order": order,
                        "confirm_touch": str(cf),
                        "revisit_touch": str(rv),
                        "layer": LAYER_OBSERVATION})
                    if order == "confirmation-first":
                        c.to_confirmed(at_bar=c.ambiguous_bar, at_time=t,
                                       evidence={"fine_bar": str(cf),
                                                 "order": order})
                    changes.append({
                        "aspect": "candidate_ordering",
                        "before": UNKNOWN_ORDERING,
                        "after": order,
                        "reason": "finer observations resolved the "
                                  "same-bar ordering",
                        "evidence": [c.candidate_id, str(cf), str(rv)]})
        return changes

    # ---- hf context (sequence separation #1) -------------------------
    def _update_hf_context(self, record) -> List[dict]:
        trend = "unknown"
        evidence = []
        for i in record.interpretations:
            if i.interpretation_id in ("I-primary", "I-scenario"):
                trend = str(i.data.get("direction") or "unknown")
                evidence = [f.fact_id for f in record.structural_facts
                            if f.kind == "derived-movement-direction"]
        if trend != self.hf_context.get("trend") and trend != "unknown":
            self.hf_context = {"trend": trend, "evidence": evidence,
                               "established_at":
                                   str(record.as_of_time),
                               "as_of_bar": int(record.as_of_bar)}
            self.seq_facts.append({
                "kind": "HF_CONTEXT_ESTABLISHED",
                "at": pd.Timestamp(record.as_of_time),
                "trend": trend, "evidence": evidence,
                "layer": LAYER_INTERPRETATION})
            return [{"aspect": "hf_context",
                     "before": "unknown", "after": trend,
                     "reason": "higher-frame context established from "
                               "completed structure",
                     "evidence": evidence}]
        return []

    # ---- candidate detection (declared research definition) ----------
    def _scan_for_candidates(self, record, bars, world) -> List[dict]:
        changes: List[dict] = []
        upto = int(record.as_of_bar)
        frac = RESEARCH_CFG_NEAR_SUPPORT_DISTANCE_FRACTION
        refs = [p for p in world["by_id"].values()
                if getattr(p, "status", "") == "confirmed"]
        from_j = max(0, self._scan_upto + 1)
        for j in range(from_j, upto + 1):
            o, h, l, c = (float(bars["open"].iloc[j]),
                          float(bars["high"].iloc[j]),
                          float(bars["low"].iloc[j]),
                          float(bars["close"].iloc[j]))
            t = pd.Timestamp(bars.index[j])
            for r in refs:
                near = abs(l - r.level) / max(abs(r.level), 1e-9) <= frac \
                    if r.side == "low" else \
                    abs(h - r.level) / max(abs(r.level), 1e-9) <= frac
                if r.side == "low" and c < o and near:
                    self._add_candidate(
                        direction="bullish", j=j, t=t, ohlc=(o, h, l, c),
                        ref=r, changes=changes)
                if r.side == "high" and c > o and near:
                    self._add_candidate(
                        direction="bearish", j=j, t=t, ohlc=(o, h, l, c),
                        ref=r, changes=changes)
        self._scan_upto = max(self._scan_upto, upto)
        return changes

    def _add_candidate(self, *, direction, j, t, ohlc, ref, changes):
        o, h, l, c = ohlc
        self._cand_seq += 1
        cand = OBLikeCandidate(
            candidate_id=f"OBC-{self.run_id}-{self._cand_seq:04d}",
            direction=direction, bar_index=int(j), bar_time=t,
            open=o, high=h, low=l, close=c,
            context_ref_id=ref.candidate_id,
            context_ref_level=float(ref.level),
            timeframe=self.task_scale,
            eligibility={
                "definition": "declared research configuration: "
                              f"{'down' if direction == 'bullish' else 'up'}"
                              "-close bar whose "
                              f"{'low' if direction == 'bullish' else 'high'}"
                              f" is within {frac_pct()} of the "
                              "contextual swing "
                              f"{ref.side} level (source leaves 'near "
                              "support' open; this constant is NOT a "
                              "source claim and NOT a market truth)",
                "known_at_selection": [
                    f"context ref {ref.candidate_id} confirmed at its "
                    f"knowable bar (before this bar)",
                    f"bar OHLC at {t}",
                ],
            })
        cand.to_awaiting(at_bar=j, at_time=t,
                         evidence={"bar": int(j), "ohlc": [o, h, l, c]})
        self.seq_facts.append({
            "kind": "CANDIDATE_FORMED", "at": t,
            "candidate_id": cand.candidate_id,
            "after_hf_context": self.hf_context.get("established_at"),
            "layer": LAYER_DERIVATION})
        self.candidates.append(cand)
        changes.append({
            "aspect": "candidate", "before": "(none)",
            "after": f"{cand.candidate_id} {cand.state}",
            "reason": "declared research definition matched; awaiting "
                      "the later-evidence event (never confirmed at "
                      "formation)",
            "evidence": [cand.candidate_id, ref.candidate_id]})

    # ---- candidate updates (confirmation / revisit / ordering) ------
    def _update_candidates(self, record, bars, world) -> List[dict]:
        changes: List[dict] = []
        upto = int(record.as_of_bar)
        for c in self.candidates:
            if c.state not in (STATE_CANDIDATE,
                               STATE_AWAITING_CONFIRMATION):
                continue
            if c.ordering is not None:
                # ambiguous (UNKNOWN) or already resolved by finer
                # data: never re-derive or overwrite at this resolution
                continue
            if c.state == STATE_CANDIDATE:
                c.to_awaiting(at_bar=c.bar_index, at_time=c.bar_time,
                              evidence={"bar": c.bar_index})
            first_confirm = first_revisit = None
            for j in range(c.bar_index + 1, upto + 1):
                h = float(bars["high"].iloc[j])
                l = float(bars["low"].iloc[j])
                cl = float(bars["close"].iloc[j])
                t = pd.Timestamp(bars.index[j])
                conf = h > c.high if c.direction == "bullish" \
                    else l < c.low
                # revisit = RETURN to the candidate area's far boundary
                # (declared definition; both confirm+revisit inside one
                # bar cannot be ordered from OHLC)
                rev = (l <= c.low) if c.direction == "bullish" \
                    else (h >= c.high)
                if conf and first_confirm is None:
                    first_confirm = (j, t, cl)
                if rev and first_revisit is None:
                    first_revisit = (j, t, cl)
                if first_confirm and first_revisit:
                    break
            if first_confirm is None:
                continue
            jf, tf, clf = first_confirm
            jr = first_revisit[0] if first_revisit else None
            if jr is not None and jf == jr:
                # same bar: OHLC cannot order confirm vs revisit
                c.ambiguous_bar = jf
                c.ordering = UNKNOWN_ORDERING
                c.events.append({
                    "kind": "ordering_unresolved",
                    "at": tf, "bar": int(jf),
                    "note": "confirmation and revisit could both have "
                            "occurred inside this bar; OHLC cannot "
                            "order them; state stays UNDECIDED and the "
                            "flattering order is refused",
                    "layer": LAYER_UNKNOWN})
                changes.append({
                    "aspect": "candidate", "before": c.state,
                    "after": c.state + " (ordering UNKNOWN)",
                    "reason": "same-bar confirm/revisit: ordering "
                              "unresolvable from OHLC",
                    "evidence": [c.candidate_id, str(jf)]})
                continue
            ev = c.to_confirmed(
                at_bar=jf, at_time=tf,
                evidence={"bar": int(jf), "close": clf,
                          "rule": "later bar traded through the "
                                  "candidate extreme (declared)",
                          "revisit_bar": jr})
            self.seq_facts.append({
                "kind": "CONFIRMATION_EVENT", "at": tf,
                "candidate_id": c.candidate_id, "bar": int(jf),
                "layer": LAYER_OBSERVATION})
            changes.append({
                "aspect": "candidate", "before": STATE_AWAITING_CONFIRMATION,
                "after": STATE_CONFIRMED,
                "reason": ev["reason"], "evidence": ev["evidence"]})
        return changes

    # ---- ledger integration (existing InterpretationLedger) ----------
    def _ledger_sync(self, cand: OBLikeCandidate, ledger) -> None:
        key = f"{cand.candidate_id}#{len(cand.events)}"
        if self._ledger_uids.get(cand.candidate_id) == key:
            return
        status_map = {STATE_CANDIDATE: "justified",
                      STATE_AWAITING_CONFIRMATION: "justified",
                      STATE_CONFIRMED: "justified",
                      STATE_INVALIDATED: "falsified",
                      STATE_INSUFFICIENT: "unresolved"}
        res = SelectionResult(
            task_id="T-STUDY-CANDIDATE", decision_bar=cand.bar_index,
            status=status_map.get(cand.state, "unresolved"),
            selected_id=cand.candidate_id,
            survivors=[], excluded=[], unresolved=None,
            provenance=["OB16-A", "FVG24-A"],
            policy_refs=["RESEARCH_CONFIG_ONLY"],
            representation_id="study-links-v1",
            notes=[f"state={cand.state}", f"role={cand.role}",
                   f"ordering={cand.ordering}"],
            decision_time=pd.Timestamp(cand.bar_time),
            direction=cand.direction)
        payload = {
            "kind": "study_candidate_state",
            "run_id": self.run_id,
            "inputs": {"events": [str(e) for e in cand.events],
                       "eligibility": cand.eligibility,
                       "context_ref": cand.context_ref_id},
            "definitions": {"state_machine": list(CANDIDATE_STATES),
                            "roles": [ROLE_TREND, ROLE_REACTION_PAUSE,
                                      ROLE_UNDETERMINED]},
            "revision_of": self._ledger_uids.get(cand.candidate_id),
            "stale": False, "stale_reason": None,
            "recompute_supported": False, "recompute": None,
            "recorded_event_times": [str(e.get("at"))
                                     for e in cand.events
                                     if e.get("at") is not None],
            "ledger_version_before": len(ledger.results),
            "ledger_version_after": None,
            "depends_on_results": [],
        }
        uid = ledger.record(res, payload)
        payload["ledger_version_after"] = len(ledger.results)
        self._ledger_uids[cand.candidate_id] = uid

    # ---- world reconstruction (approved components) ------------------
    def _world(self, bars, record, axis):
        sub = bars.iloc[:record.as_of_bar + 1]
        rep = Representation(family="F-K", view_id="C",
                             scale_label="coarse",
                             params=(("k", float(self.k)),))
        points = fk_turning_points(sub, self.k, rep, id_prefix="PS",
                                   allow_short_left=False,
                                   tie_policy=TIE_FT_EQ_FIRST,
                                   axis=axis)
        by_id = {p.candidate_id: p for p in points}
        legs = build_legs(points, rep, completed_only=True,
                          ambiguities=[])
        return {"by_id": by_id, "legs": legs}

    # ---- watch plan (recorded BEFORE stepping — §10) ----------------
    def watch_plan(self) -> List[dict]:
        """What the engine will watch going forward, and the declared
        revision conditions for each open item.  Recorded BEFORE any
        further stepping so a later change cannot be read as a prior
        prediction."""
        plan: List[dict] = []
        for c in self.candidates:
            if c.state in (STATE_INVALIDATED, STATE_INSUFFICIENT):
                continue
            confirm_level = c.high if c.direction == "bullish" else c.low
            revisit_level = c.low if c.direction == "bullish" else c.high
            plan.append({
                "subject": c.candidate_id,
                "kind": "OB-like candidate (R1)",
                "state": c.state, "role": c.role,
                "ordering": c.ordering,
                "time_provenance": {
                    "bar_time": str(c.bar_time), "timezone": c.timezone,
                    "bar_convention": c.bar_convention,
                    "timeframe": c.timeframe},
                "watch": [
                    f"trade-through of {confirm_level} on a later "
                    f"completed bar -> CONFIRMED (recorded at the "
                    f"evidence bar)",
                    f"return to {revisit_level} -> revisit event "
                    f"(same-bar with confirmation -> ordering UNKNOWN)",
                    f"context reference {c.context_ref_id} at "
                    f"{c.context_ref_level}: a completed close through "
                    f"it before confirmation -> role premise failed",
                ],
                "revision_conditions": [
                    "higher-frame structure change re-opens role "
                    "evaluation",
                    "finer data may resolve a same-bar ordering "
                    "(either direction)",
                ],
                "unknowns": [
                    "no resting-order data: participant positions/"
                    "intent, resting stops and available liquidity "
                    "CANNOT be established",
                    "'near support' has no source definition "
                    "(research-config constant only)",
                ],
            })
        for h in self.hypotheses:
            if h.status != "ACTIVE":
                continue
            plan.append({
                "subject": h.hypothesis_id,
                "kind": "higher-frame hypothesis (R3)",
                "state": h.status,
                "watch": [f"failure reference {h.failure_reference_id} "
                          f"at {h.failure_reference_level} "
                          f"(side {h.failure_side})"],
                "revision_conditions": [
                    "a completed close through the failure reference "
                    "-> SUSPEND + demand more information (never an "
                    "automatic opposite hypothesis)",
                ],
                "unknowns": ["corpus evidence is teaching material, "
                             "not an independently pre-registered "
                             "forecast record"],
            })
        return plan

    # ---- save / resume ----------------------------------------------
    def state_dict(self) -> dict:
        return {
            "run_id": self.run_id, "k": self.k,
            "task_scale": self.task_scale, "task": self.task,
            "candidates": [c.to_record() for c in self.candidates],
            "hypotheses": [h.to_record() for h in self.hypotheses],
            "selections": [s.to_record() for s in self.selections],
            "seq_facts": [{**e, "at": str(e.get("at"))}
                          for e in self.seq_facts],
            "hf_context": self.hf_context,
            "scan_upto": self._scan_upto,
            "cand_seq": self._cand_seq,
            "ledger_uids": dict(self._ledger_uids),
            "selection_quality": "NOT_ESTABLISHED",
        }

    def load_state_dict(self, st: dict) -> None:
        self._scan_upto = int(st.get("scan_upto", -1))
        self._cand_seq = int(st.get("cand_seq", 0))
        self.hf_context = dict(st.get("hf_context", {}))
        self._ledger_uids = dict(st.get("ledger_uids", {}))
        self.seq_facts = list(st.get("seq_facts", []))
        self.candidates = []
        for d in st.get("candidates", []):
            c = OBLikeCandidate(
                candidate_id=d["candidate_id"],
                direction=d["direction"], bar_index=d["bar_index"],
                bar_time=pd.Timestamp(d["bar_time"]),
                open=d["open"], high=d["high"], low=d["low"],
                close=d["close"], context_ref_id=d["context_ref_id"],
                context_ref_level=d["context_ref_level"],
                timezone=d.get("timezone", "UTC"),
                bar_convention=d.get("bar_convention", ""),
                timeframe=d.get("timeframe", self.task_scale),
                eligibility=d.get("eligibility", {}),
                state=d.get("state", STATE_CANDIDATE),
                role=d.get("role", ROLE_UNDETERMINED),
                role_assignments=d.get("role_assignments", []),
                events=d.get("events", []),
                ordering=d.get("ordering"),
                ambiguous_bar=d.get("ambiguous_bar"),
                fine_touches={k: (pd.Timestamp(v) if v else None)
                              for k, v in
                              d.get("fine_touches", {}).items()})
            self.candidates.append(c)
        self.hypotheses = []
        for d in st.get("hypotheses", []):
            h = HigherFrameHypothesis(
                hypothesis_id=d["hypothesis_id"],
                statement=d["statement"],
                failure_reference_level=d["failure_reference_level"],
                failure_reference_id=d["failure_reference_id"],
                failure_side=d["failure_side"], status=d["status"],
                events=d.get("events", []))
            self.hypotheses.append(h)
        self.selections = []
        for d in st.get("selections", []):
            s = TimeProvenanceSelection(
                selection_id=d["selection_id"],
                subject_id=d["subject_id"],
                selected_at=pd.Timestamp(d["selected_at"]),
                timezone=d.get("timezone", "UTC"),
                bar_convention=d.get("bar_convention", ""),
                timeframe=d.get("timeframe", ""),
                eligibility=d.get("eligibility", {}),
                status=d.get("status", "SELECTED"),
                revisions=d.get("revisions", []))
            self.selections.append(s)


def frac_pct() -> str:
    return f"{RESEARCH_CFG_NEAR_SUPPORT_DISTANCE_FRACTION:.2%}"


def _jsonable(obj):
    """Recursively convert Timestamps and dataclasses to JSON-safe
    values (used by every to_record/state_dict)."""
    if isinstance(obj, pd.Timestamp):
        return str(obj)
    if isinstance(obj, dict):
        return {k: _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    return obj
