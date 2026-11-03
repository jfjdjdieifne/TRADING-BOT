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
      existence.  Role assignment is EVIDENCE-EVALUATED for a declared
      task: a role is assigned only when positive evidence supports it.
      Opposition to the higher-frame direction never by itself assigns
      (or establishes) a reaction/pause role; alignment never by itself
      assigns a trend role.  Where the evidence does not support a role
      the verdict is UNDETERMINED with the discriminating evidence that
      would settle it.  No shape is ever auto-rejected.
    * sequence separation: HF context established -> candidate formed ->
      later confirmation (or absence) -> possible revisit -> revision;
      confirmation is NEVER back-filled into the formation moment; if
      two events may share one bar and OHLC cannot order them, ordering
      is recorded UNKNOWN and the engine refuses to pick the flattering
      order.  An ambiguous bar is scoped to THAT bar only: a resolution
      (by finer data) or an unresolved ordering never freezes the
      candidate — later independent bars may still confirm (recorded at
      their own evidence bars).

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
    more information — suspension semantics, never an automatic flip to
    the opposite hypothesis.

CANDIDATE–CONTEXT RELATION (no invented distance): the candidate is the
"lowest down close candle" (order statistic, source wording) whose
reported range CONTAINS the contextual reference level
(``low <= level <= high``).  This is a precise range-position relation:
a bar entirely BELOW the level also satisfies ``low <= level`` and is
deliberately EXCLUDED, as is a bar entirely ABOVE it.  Range
containment establishes ONLY that the level lies within the bar's
reported range — it does NOT establish the intrabar direction, the
intrabar sequence, or any orders at the level, and it is NOT called
"traded at or through".  NO percentage, NO candle count, NO hidden
threshold exists anywhere in this module.  The source's "near support"
wording is NOT operationally resolved by this relation (the corpus
marks it ``UNSUPPORTED_OR_UNAVAILABLE``/ambiguous); that gap is
recorded in every candidate's ``unknowns``.  The region for "lowest" is
taken as the bars since the reference's own occurrence bar (an
engine-available fact) — an ENGINEERING choice, not a source claim.

LAYERS: every record separates DIRECT OBSERVATION / DERIVATION under a
declared definition / CONTEXTUAL INTERPRETATION / UNKNOWN-UNSUPPORTED
(resting stops, participant intent, causes, intra-bar order, trading
centres, validated trades, "any chart in the world" — all unsupported).

SOURCE QUOTE PROVENANCE: corpus ``short_quotes`` attributions mark which
wording is visually checked slide text (only OB16-A 01:52) versus
approximate local ASR wording that was NOT audited by ear (all other
quotes).  ASR wording is cited here as approximate attributed wording,
never as verified verbatim quotation.

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
from trading_system.research.contextual_selection.connected_readings import (
    ConnectedReadingsEngine,
)

__all__ = [
    "CORPUS_PATH", "load_corpus", "RELATIONSHIP_REGISTER",
    "SessionClockConvention", "US_INDEX_FIRST_GAP_SESSION_CLOCK",
    "STATE_CANDIDATE", "STATE_AWAITING_CONFIRMATION", "STATE_CONFIRMED",
    "STATE_INVALIDATED", "STATE_INSUFFICIENT", "CANDIDATE_STATES",
    "ROLE_TREND", "ROLE_REACTION_PAUSE", "ROLE_UNDETERMINED",
    "OBLikeCandidate", "HigherFrameHypothesis",
    "TimeProvenanceSelection", "StudyReasoningLayer",
    "ShiftWatch", "SHIFT_QUESTIONS", "SHIFT_STATUSES",
    "assign_role", "UNKNOWN_ORDERING",
    "LAYER_OBSERVATION", "LAYER_DERIVATION",
    "LAYER_INTERPRETATION", "LAYER_UNKNOWN",
]

HERE = Path(__file__).resolve()
CORPUS_PATH = (HERE.parents[4] / "docs" / "research" /
               "huddleston_study" / "corpus_full_pass.json")

# --------------------------------------------------------------------- #
# There is deliberately NO proximity threshold in this module.          #
# A former research-config distance fraction (1%) was removed: an        #
# invented percentage must not decide market meaning and must not        #
# resolve the source's open "near support" wording.  Nothing here        #
# substitutes another percentage, candle count, or hidden threshold —    #
# the candidate-context relation is the exact-level trade relation plus  #
# the "lowest down close candle" order statistic (see module            #
# docstring).                                                           #
# --------------------------------------------------------------------- #

UNKNOWN_ORDERING = "UNKNOWN"

LAYER_OBSERVATION = "DIRECT_OBSERVATION"
LAYER_DERIVATION = "DERIVATION"
LAYER_INTERPRETATION = "CONTEXTUAL_INTERPRETATION"
LAYER_UNKNOWN = "UNKNOWN_UNSUPPORTED"

# quote provenance labels (corpus attributions)
Q_SLIDE = ("slide text, visually checked (on-screen 01:52; ellipsis for "
           "omitted words)")
Q_ASR = ("approximate attributed ASR wording, NOT audited by ear "
         "(local faster-whisper; timings approximate)")


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
            "OB16-A short_quotes (" + Q_SLIDE + "): 'when the high of "
            "the lowest down close candle ... is traded through'",
            "OB16-A short_quotes (" + Q_ASR + ", ~03:21): 'We don't "
            "know that yet until at a later time' — approximate "
            "attributed wording, not verbatim",
            "OB16-A change (DIRECT_STATEMENT): bearish-looking block is "
            "NOT a sell cue under bullish higher-frame context",
        ],
        "engine_interpretation": [
            "state machine CANDIDATE/AWAITING_CONFIRMATION/CONFIRMED/"
            "INVALIDATED/INSUFFICIENT_INFORMATION with ledger-recorded "
            "transitions",
            "role assignment is evidence-evaluated for a declared task; "
            "a role is recorded only when positive evidence supports "
            "it; opposition alone never establishes a reaction role and "
            "alignment alone never establishes a trend role",
            "sequence separation with UNKNOWN ordering on unresolvable "
            "same-bar events; ambiguity is scoped to its own bar and "
            "never permanently freezes the candidate",
        ],
        "not_established": [
            "'near support' operational definition (source leaves "
            "open; NO distance/percentage/candle-count rule is used or "
            "claimed — the exact-level trade relation is an "
            "ENGINEERING choice, not Michael's definition)",
            "the region scope of 'the lowest down close candle' (taken "
            "as since the reference occurrence — engineering choice)",
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
            "FVG24-A short_quotes (" + Q_ASR + ", ~75:02/75:12): "
            "'You can't be on your 9.30 candle...'; 'I was incorrect by "
            "saying all that stuff' — approximate attributed wording, "
            "not verbatim",
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
            "E12-A short_quotes (" + Q_ASR + ", ~11:31/11:39): 'if it "
            "goes above that then I'm probably wrong in my analysis'; "
            "'I demand more information' — approximate attributed "
            "wording, not verbatim",
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
    note="DIRECT_STATEMENT FVG24-A (~75:02 approximate ASR wording, "
         "not ear-audited); session-specific first-gap qualification "
         "only")


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
    ordering: Optional[str] = None   # ordering of the LATEST ambiguous
                                     # bar; UNKNOWN until finer data
    ambiguous_bar: Optional[int] = None
    ambiguity_interval: Optional[Tuple[str, str]] = None
    fine_touches: Dict[str, Optional[pd.Timestamp]] = field(
        default_factory=dict)
    scan_floor: int = -1             # highest bar already adjudicated

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
                                 "(a later bar's reported high exceeds "
                                 "the candidate extreme — the source's "
                                 "'is traded through' wording; "
                                 "intrabar sequence not established); "
                                 "recorded at the evidence bar, never "
                                 "back-filled")

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
                        "more information (source semantics, E12-A — "
                        "approximate ASR wording); no automatic "
                        "opposite hypothesis is generated",
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
# evidence-evaluated role assignment (R1)                                #
# --------------------------------------------------------------------- #
def assign_role(*, candidate_direction: str, hf_trend: str,
                task: str,
                evidence: Optional[Dict[str, Any]] = None
                ) -> Dict[str, Any]:
    """Role is evaluated FOR A DECLARED TASK against the available
    EVIDENCE — never inferred automatically from direction alignment or
    opposition alone.

    Evidence flags (each recorded with its reference when known):
      * ``hf_established``   — a higher-frame context established from
        completed structure before this evaluation;
      * ``confirmation_event`` — the candidate's declared later-evidence
        event (a bar trading through its extreme) is observed;
      * ``reaction_observed`` — an observed return/interaction at the
        candidate area (a recorded revisit event).

    Rules:
      * TREND_CONTINUATION_REFERENCE is supported only with
        hf_established AND direction consistency AND the confirmation
        event (source caution: 'We don't know that yet until at a later
        time' — approximate ASR wording).  Alignment alone supports
        nothing.
      * REACTION_PAUSE_REFERENCE is supported only with
        hf_established AND an observed reaction.  Opposition to the
        higher-frame direction alone NEVER establishes it (the source's
        25:00-25:43 point is that the trend/sell-cue role is NOT
        supported — not that a reaction role becomes fact).
      * Otherwise the verdict is UNDETERMINED with the discriminating
        evidence that would settle it.  Nothing is forced; nothing is
        permanently abstained — new evidence re-opens the evaluation.
    """
    ev = {"hf_established": False, "confirmation_event": False,
          "reaction_observed": False}
    refs: Dict[str, Any] = {}
    if evidence:
        for k in ev:
            if k in evidence:
                ev[k] = bool(evidence[k])
        refs = dict(evidence.get("refs", {}))
    out: Dict[str, Any] = {
        "task": task, "hf_trend": hf_trend,
        "candidate_direction": candidate_direction,
        "evidence_used": {k: {"value": v, "ref": refs.get(k)}
                          for k, v in ev.items()},
        "alternatives": [], "would_change": [],
        "supported": False,
    }
    aligned = (candidate_direction == "bullish" and hf_trend == "up") or \
              (candidate_direction == "bearish" and hf_trend == "down")

    if not ev["hf_established"]:
        out.update(
            role=ROLE_UNDETERMINED,
            reasons=["no established higher-frame context at this "
                     "as-of: the evidence does not support any role"],
            discriminating_evidence_needed=[
                "an established higher-frame context (completed "
                "structure) before this evaluation",
                "the candidate's declared confirmation event (a later "
                "bar trading through its extreme)",
                "an observed reaction at the candidate area, if a "
                "reaction/pause role is proposed"])
        return out

    trend_supported = aligned and ev["confirmation_event"]
    trend_excluded = not aligned
    reaction_supported = ev["reaction_observed"]

    if task == "trend-continuation":
        if trend_supported:
            out.update(role=ROLE_TREND, supported=True,
                       reasons=["trend role SUPPORTED by evidence: the "
                                "candidate direction agrees with the "
                                "established higher-frame context AND "
                                "its declared confirmation event is "
                                "observed"])
            if reaction_supported:
                out["alternatives"].append(
                    f"{ROLE_REACTION_PAUSE}: also supported (an "
                    f"reaction at the area is observed); not preferred "
                    f"for the trend-continuation task")
            else:
                out["alternatives"].append(
                    f"{ROLE_REACTION_PAUSE}: possible but NOT "
                    f"established (no reaction observed at the area)")
            out["would_change"].append(
                "a higher-frame structure change or a role-relevant "
                "event revision re-opens the evaluation")
            return out
        if trend_excluded:
            # source-supported negative only: the trend role is not
            # supported under the opposing context
            reasons = ["trend role NOT supported: the candidate "
                       "direction opposes the established higher-frame "
                       "context (OB16-A 25:00-25:43) — this does NOT "
                       "reject the candidate itself"]
            if reaction_supported:
                out.update(role=ROLE_REACTION_PAUSE, supported=True,
                           reasons=reasons + [
                               "reaction/pause role SUPPORTED by "
                               "evidence: a reaction at the candidate "
                               "area is observed (not inferred from "
                               "opposition)"])
                out["alternatives"].append(
                    f"{ROLE_TREND}: excluded for this task by the "
                    f"higher-frame context")
            else:
                out.update(role=ROLE_UNDETERMINED, supported=False,
                           reasons=reasons + [
                               "reaction/pause role NOT established: "
                               "opposition alone does not make it fact "
                               "— no reaction at the area is observed"],
                           discriminating_evidence_needed=[
                               "an observed reaction/revisit at the "
                               "candidate area (would support a "
                               "reaction/pause role)",
                               "a higher-frame structure change (would "
                               "re-open the trend role)"])
                out["alternatives"].append(
                    f"{ROLE_REACTION_PAUSE}: possible but not fact")
            out["would_change"].append(
                "a higher-frame structure change re-opens the trend "
                "role; an observed reaction settles the reaction role")
            return out
        # aligned but no confirmation event yet
        out.update(role=ROLE_UNDETERMINED, supported=False,
                   reasons=["trend role NOT yet supported: direction "
                            "agrees with the higher-frame context but "
                            "the declared confirmation event is not "
                            "observed ('we don't know that yet until "
                            "at a later time' — approximate ASR "
                            "wording)"],
                   discriminating_evidence_needed=[
                       "the declared confirmation event: a later bar "
                       "trading through the candidate extreme"])
        if reaction_supported:
            out["alternatives"].append(
                f"{ROLE_REACTION_PAUSE}: supported by an observed "
                f"reaction; possible alternative role")
        out["would_change"].append(
            "the confirmation event (or its documented absence) "
            "settles the trend role")
        return out

    # task == reaction-pause
    if reaction_supported:
        out.update(role=ROLE_REACTION_PAUSE, supported=True,
                   reasons=["reaction/pause role SUPPORTED by "
                            "evidence: a reaction at the candidate "
                            "area is observed"])
    else:
        out.update(role=ROLE_UNDETERMINED, supported=False,
                   reasons=["reaction/pause role NOT established: no "
                            "reaction at the candidate area is "
                            "observed"],
                   discriminating_evidence_needed=[
                       "an observed reaction/revisit at the candidate "
                       "area"])
    out["would_change"].append(
        "an observed reaction (or its documented absence) settles the "
        "reaction/pause role")
    return out


# --------------------------------------------------------------------- #
# next relationship slice (E03-A/B) — reference-crossing shift-watch     #
# --------------------------------------------------------------------- #
# SOURCE (E03-A, DIRECT/PARAPHRASE): "Crossing an old low/high is a
# context for WATCHING a possible shift, not proof of one"; a crossing
# "changes the questions to watch on a smaller timeframe, without
# creating an automatic reversal/trade signal."
# SOURCE (E03-B, PARAPHRASE): "monitor next closed-bar
# displacement/non-overlap as evidence"; the sequence is older-reference
# crossing -> subsequent local-swing crossing; "do not assume a buy
# after a low raid; observe whether market supplies evidence."
#
# ENGINEERING (declared): a crossing is the engine's existing
# close-through relation at BAR granularity — a close-to-close
# transition across the level between two consecutive completed bars
# (the intrabar path is NOT established).  A crossing OPENS a watch
# whose status is WATCHING / EVIDENCE_NOTED only — there is NO
# "shift confirmed" state and NO reversal/trade signal anywhere.

SHIFT_STATUS_WATCHING = "WATCHING"
SHIFT_STATUS_EVIDENCE = "EVIDENCE_NOTED"
SHIFT_STATUSES = (SHIFT_STATUS_WATCHING, SHIFT_STATUS_EVIDENCE)

SHIFT_QUESTIONS = [
    "watch the next closed bars for displacement/non-overlap in the "
    "crossing direction (E03-B: 'monitor next closed-bar "
    "displacement/non-overlap as evidence')",
    "watch for a subsequent crossing of the local swing formed before "
    "the older reference (E03-B sequence: older-reference crossing -> "
    "local-swing crossing)",
    "do NOT assume a reversal or a trade after a raid — observe "
    "whether the market supplies evidence (E03-B)",
]


@dataclass
class ShiftWatch:
    watch_id: str
    opened_at: pd.Timestamp
    crossing: Dict[str, Any]      # ref, level, side, bar, close,
                                  # direction, transition evidence
    local_ref_id: Optional[str] = None
    local_ref_level: Optional[float] = None
    questions: List[str] = field(
        default_factory=lambda: list(SHIFT_QUESTIONS))
    evidence: List[dict] = field(default_factory=list)
    status: str = SHIFT_STATUS_WATCHING
    scan_floor: int = -1

    def note_evidence(self, *, kind, at, at_bar, detail) -> dict:
        ev = {"kind": kind, "at": pd.Timestamp(at),
              "at_bar": int(at_bar), "detail": detail,
              "note": "evidence item only — NOT proof of a shift; no "
                      "reversal or trade signal is generated",
              "layer": LAYER_OBSERVATION}
        self.evidence.append(ev)
        self.status = SHIFT_STATUS_EVIDENCE
        return ev

    def to_record(self) -> dict:
        return _jsonable(dataclasses.asdict(self))


# --------------------------------------------------------------------- #
# the reasoning layer (flows through the existing monitoring path)       #
# --------------------------------------------------------------------- #
def _bars_interval(bars, j: int) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Rows of task bar j lie in [index[j-1], index[j]) under the
    completion-label convention used by the approved frames builder."""
    end = pd.Timestamp(bars.index[j])
    if j > 0:
        start = pd.Timestamp(bars.index[j - 1])
    else:
        start = end - pd.Timedelta(hours=4)
    return start, end


class _RefRecordView:
    """Read-only view over a serialized reference record (readings
    boundaries + resume path).  The readings pipeline reads only
    candidate_id/level/side/status/knowable_bar/occurrence_* /kind."""

    def __init__(self, d: dict) -> None:
        self._d = dict(d)

    def __getattr__(self, k):
        try:
            return self._d[k]
        except KeyError:
            raise AttributeError(k)


def _ref_records(world: dict) -> List[dict]:
    out = []
    for p in world.get("by_id", {}).values():
        out.append({k: getattr(p, k, None) for k in (
            "candidate_id", "level", "side", "status", "kind",
            "knowable_bar", "occurrence_bar", "occurrence_time")})
    return out


class StudyReasoningLayer:
    """Detects OB-like candidates against the causal world of the
    current boundary, maintains their state machine and evidence-based
    roles, runs hypothesis reviews and revocable selections, and records
    every transition in the EXISTING InterpretationLedger.
    """

    def __init__(self, *, run_id: str = "study-v1", k: int = 2,
                 task_scale: str = "4h",
                 task: str = "trend-continuation",
                 instrument: str = "UNKNOWN",
                 session_clock: Optional[SessionClockConvention] = None
                 ) -> None:
        self.run_id = run_id
        self.k = k
        self.task_scale = task_scale
        self.task = task
        self.instrument = instrument
        self.session_clock = session_clock
        self.candidates: List[OBLikeCandidate] = []
        self.hypotheses: List[HigherFrameHypothesis] = []
        self.selections: List[TimeProvenanceSelection] = []
        self.seq_facts: List[dict] = []
        self.hf_context: Dict[str, Any] = {"trend": "unknown",
                                           "evidence": []}
        self._scan_upto = -1
        self._ledger_uids: Dict[str, str] = {}
        self._ledger_sigs: Dict[str, tuple] = {}
        self._cand_seq = 0
        self._row_buffer: List[dict] = []
        # E03 slice: reference-crossing shift-watches
        self.shift_watches: List[ShiftWatch] = []
        self._cross_scan_upto = -1
        self._crossed_keys: set = set()
        self._watch_seq = 0
        # connected readings (multi-timeframe context + FVG + tasks)
        self.readings = ConnectedReadingsEngine(
            run_id=f"{run_id}-cr", instrument=instrument,
            timezone="UTC")
        self._last_ref_records: List[dict] = []

    # ---- main hooks (called by the EXISTING MonitoringLoop) ----------
    def on_boundary(self, record, frames: Dict[str, pd.DataFrame],
                    ledger=None) -> List[dict]:
        changes: List[dict] = []
        bars = frames[self.task_scale]
        axis = SharedInformationAxis(f"{self.run_id}_study",
                                     pd.DatetimeIndex(bars.index))
        world = self._world(bars, record, axis)
        changes += self._update_hf_context(record)
        changes += self._scan_for_candidates(record, bars, world)
        changes += self._update_candidates(record, bars)
        changes += self._update_roles(record)
        changes += self._scan_reference_crossings(record, bars, world)
        changes += self._update_shift_watches(record, bars, world)
        # ---- connected readings (FVG + cross-frame links + tasks) ----
        as_of = pd.Timestamp(record.as_of_time)
        self._last_ref_records = _ref_records(world)
        changes += self._run_readings(as_of, frames, world, ledger)
        # drop buffer rows older than this boundary's bar interval
        keep_from = _bars_interval(bars, int(record.as_of_bar))[0]
        self._row_buffer = [r for r in self._row_buffer
                            if pd.Timestamp(r["time"]) >= keep_from]
        return changes

    def _run_readings(self, as_of, frames, world, ledger) -> List[dict]:
        """Connected-readings pipeline (FVG scan, interactions, links,
        reading tasks, working interpretations, ledger sync).  Runs at
        task-scale boundaries AND at readings-scale boundaries (when a
        genuinely available lower-timeframe bar completes) — evidence
        is never held back until the next task boundary."""
        changes: List[dict] = []
        changes += self.readings.scan_fvgs(frames)
        changes += self.readings.update_interactions(
            frames, as_of_time=as_of)
        changes += self.readings.link_regions(
            refs=list(world["by_id"].values()), as_of_time=as_of)
        interacted = set()
        for w in self.shift_watches:
            interacted.add(str(w.crossing.get("ref_id")))
        for c in self.candidates:
            if any(e.get("kind") in ("revisit_event",
                                     "state_transition")
                   for e in c.events[1:]):
                interacted.add(c.context_ref_id)
        self.readings.task_reference_for_review(
            refs=[p for p in world["by_id"].values()
                  if getattr(p, "status", "") == "confirmed"],
            as_of_time=as_of, interacted=sorted(interacted),
            hf_trend=str(self.hf_context.get("trend")))
        for w in self.shift_watches:
            self.readings.task_fvg_relevance_for_watch(
                watch=w.to_record(), as_of_time=as_of,
                hf_trend=str(self.hf_context.get("trend")))
        # working interpretations (context + open watches)
        hf_trend = str(self.hf_context.get("trend"))
        if hf_trend != "unknown":
            self.readings.interpretation_for_hf(
                as_of_time=as_of, trend=hf_trend,
                evidence=self.hf_context.get("evidence", []),
                derived_at=self.hf_context.get("established_at"))
        for w in self.shift_watches:
            self.readings.interpretation_for_watch(
                watch=w.to_record(), as_of_time=as_of)
        if ledger is not None:
            for c in self.candidates:
                self._ledger_sync(c, ledger)
            for w in self.shift_watches:
                self._ledger_sync_watch(w, ledger)
            self.readings.sync_ledger(ledger)
        return changes

    def on_readings_boundary(self, record, frames: Dict[str, pd.DataFrame],
                             ledger=None, boundary_time=None
                             ) -> List[dict]:
        """Relevant connected re-evaluation when a lower-timeframe
        (readings-scale) bar completes BETWEEN task-scale boundaries.

        Causality: ``boundary_time`` is the completion label of the
        just-completed lower-frame bar; only frames prefix data is
        consumed; references are the ones confirmed at the last
        completed TASK-scale boundary (never later data).  Processing
        and recording happen at this call (see ledger decision_time);
        the recorded facts carry the DATA times."""
        as_of = pd.Timestamp(boundary_time if boundary_time is not None
                             else record.as_of_time)
        world = {"by_id": {r["candidate_id"]: _RefRecordView(r)
                           for r in self._last_ref_records}}
        return self._run_readings(as_of, frames, world, ledger)

    def on_observation(self, row: dict) -> List[dict]:
        """Finer-grained re-evaluation on actually available data (the
        1m observation).  Touches are scoped to the ambiguous bar's own
        interval: rows outside it can never resolve its ordering (they
        are later events).  The resolution is recorded APPEND-ONLY when
        the second touch's information becomes available."""
        changes: List[dict] = []
        t = pd.Timestamp(row["time"])
        h, l = float(row["high"]), float(row["low"])
        self._row_buffer.append({"time": t, "high": h, "low": l})
        if len(self._row_buffer) > 4000:
            self._row_buffer = self._row_buffer[-2000:]
        for c in self.candidates:
            if c.ambiguous_bar is None or \
                    c.ordering != UNKNOWN_ORDERING:
                continue
            if c.ambiguity_interval is None:
                continue
            start = pd.Timestamp(c.ambiguity_interval[0])
            end = pd.Timestamp(c.ambiguity_interval[1])
            if not (start <= t < end):
                # outside the ambiguous bar: later events cannot
                # resolve its intra-bar ordering (OBC-0006 defect fix)
                continue
            if c.direction == "bullish":
                conf_touch, rev_touch = h > c.high, l <= c.low
            else:
                conf_touch, rev_touch = l < c.low, h >= c.high
            if conf_touch and c.fine_touches.get("confirm") is None:
                c.fine_touches["confirm"] = t
            if rev_touch and c.fine_touches.get("revisit") is None:
                c.fine_touches["revisit"] = t
            changes += self._resolve_ambiguity_if_possible(c)
        return changes

    # ---- ambiguity handling (scoped, append-only, non-freezing) ------
    def _resolve_ambiguity_if_possible(self, c: OBLikeCandidate,
                                       recorded_at=None
                                       ) -> List[dict]:
        cf = c.fine_touches.get("confirm")
        rv = c.fine_touches.get("revisit")
        if cf is None or rv is None:
            return []
        resolved_at = max(cf, rv)   # info complete at the later touch
        if cf == rv:
            # one fine bar contains both: ordering stays UNKNOWN
            return []
        order = "confirmation-first" if cf < rv else "revisit-first"
        c.ordering = order
        ev = {"kind": "ordering_resolved_by_finer_data",
              "at": pd.Timestamp(resolved_at),
              "recorded_at": pd.Timestamp(recorded_at or resolved_at),
              "ambiguous_bar": c.ambiguous_bar,
              "order": order, "confirm_touch": str(cf),
              "revisit_touch": str(rv),
              "note": "'at' = when the resolving information became "
                      "available (the later touch); 'recorded_at' = "
                      "when the engine learned it; the earlier "
                      "ordering_unresolved record is preserved "
                      "(append-only; nothing is rewritten)",
              "layer": LAYER_OBSERVATION}
        c.events.append(ev)
        changes = [{"aspect": "candidate_ordering",
                    "before": UNKNOWN_ORDERING, "after": order,
                    "reason": "finer observations within the ambiguous "
                              "bar resolved its intra-bar ordering",
                    "evidence": [c.candidate_id, str(cf), str(rv)]}]
        if order == "confirmation-first":
            c.to_confirmed(at_bar=c.ambiguous_bar, at_time=cf,
                           evidence={"fine_bar": str(cf),
                                     "order": order,
                                     "revisit_touch": str(rv)})
            changes.append({"aspect": "candidate", "before":
                            STATE_AWAITING_CONFIRMATION,
                            "after": STATE_CONFIRMED,
                            "reason": "confirmation-first ordering "
                                      "resolved by finer data",
                            "evidence": [c.candidate_id, str(cf)]})
        else:
            # revisit-first: ONLY the proposed sequence is rejected —
            # this bar offers no confirmation event; the candidate is
            # NOT invalidated and later bars may still confirm (the
            # source establishes no permanent invalidation here)
            c.events.append({
                "kind": "sequence_rejected", "at": pd.Timestamp(rv),
                "ambiguous_bar": c.ambiguous_bar,
                "note": "the proposed sequence (trade-through before "
                        "the return within this bar) is rejected; this "
                        "bar supplies NO confirmation event; the "
                        "candidate remains open to later confirmation "
                        "bars (no permanent invalidation is "
                        "established by the source)",
                "layer": LAYER_DERIVATION})
            changes.append({"aspect": "candidate",
                            "before": STATE_AWAITING_CONFIRMATION,
                            "after": STATE_AWAITING_CONFIRMATION,
                            "reason": "revisit-first: this bar's "
                                      "proposed sequence rejected; "
                                      "candidate remains open",
                            "evidence": [c.candidate_id, str(rv)]})
        return changes

    def _try_buffer_resolution(self, c: OBLikeCandidate, start, end):
        """Use already-available fine rows inside the ambiguous bar
        (they streamed BEFORE this boundary) to resolve its ordering at
        detection time."""
        conf = rev = None
        for r in self._row_buffer:
            t = pd.Timestamp(r["time"])
            if not (start <= t < end):
                continue
            if c.direction == "bullish":
                conf_touch, rev_touch = (r["high"] > c.high,
                                         r["low"] <= c.low)
            else:
                conf_touch, rev_touch = (r["low"] < c.low,
                                         r["high"] >= c.high)
            if conf_touch and conf is None:
                conf = t
            if rev_touch and rev is None:
                rev = t
        if conf is not None and rev is not None and conf != rev:
            return conf, rev
        return None

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
                if not (int(r.occurrence_bar) < j):
                    continue
                lvl = float(r.level)
                # PRECISE range relation (Q2): the reference level lies
                # WITHIN the bar's reported range: low <= level <= high.
                # This is NOT "traded at or through": a bar entirely
                # below the level also satisfies low <= level and is
                # EXCLUDED here, as is a bar entirely above it.  Range
                # containment establishes only that the level lies in
                # the reported range — NOT the intrabar direction, NOT
                # the intrabar sequence, NOT any orders at the level.
                contains = (l <= lvl <= h)
                # order statistic over the SAME candle family since the
                # reference's occurrence bar (engine-available fact; no
                # distance/percentage/candle count)
                family_extremes = []
                for m in range(int(r.occurrence_bar) + 1, j):
                    mo = float(bars["open"].iloc[m])
                    ml = float(bars["low"].iloc[m])
                    mh = float(bars["high"].iloc[m])
                    if r.side == "low" and float(
                            bars["close"].iloc[m]) < mo:
                        family_extremes.append(ml)
                    if r.side == "high" and float(
                            bars["close"].iloc[m]) > mo:
                        family_extremes.append(mh)
                if r.side == "low" and c < o and contains:
                    if not family_extremes or l < min(family_extremes):
                        self._add_candidate(
                            direction="bullish", j=j, t=t,
                            ohlc=(o, h, l, c), ref=r, changes=changes,
                            bars=bars)
                if r.side == "high" and c > o and contains:
                    if not family_extremes or h > max(family_extremes):
                        self._add_candidate(
                            direction="bearish", j=j, t=t,
                            ohlc=(o, h, l, c), ref=r, changes=changes,
                            bars=bars)
        self._scan_upto = max(self._scan_upto, upto)
        return changes

    def _add_candidate(self, *, direction, j, t, ohlc, ref, changes,
                       bars=None):
        o, h, l, c = ohlc
        self._cand_seq += 1
        lvl = float(ref.level)
        # range-position facts (DIRECT derivations from published bars)
        prev_contains = None
        if bars is not None and j > 0:
            pl = float(bars["low"].iloc[j - 1])
            ph = float(bars["high"].iloc[j - 1])
            prev_contains = (pl <= lvl <= ph)
        close_side = "closed_below_level" if c < lvl else \
            "closed_at_or_above_level"
        cand = OBLikeCandidate(
            candidate_id=f"OBC-{self.run_id}-{self._cand_seq:04d}",
            direction=direction, bar_index=int(j), bar_time=t,
            open=o, high=h, low=l, close=c,
            context_ref_id=ref.candidate_id,
            context_ref_level=lvl,
            timeframe=self.task_scale,
            eligibility={
                "definition": "declared research definition "
                              "(ENGINEERING_INTERPRETATION, NOT "
                              "Michael's definition): a "
                              f"{'down' if direction == 'bullish' else 'up'}"
                              "-close bar that is the extreme "
                              f"{'low' if direction == 'bullish' else 'high'}"
                              " among its family since the contextual "
                              "reference's occurrence bar AND whose "
                              "reported range CONTAINS the reference "
                              "level (low <= level <= high). NO "
                              "percentage, NO candle count, NO hidden "
                              "threshold.",
                "level_relation": {
                    "kind": "range_contains_level",
                    "establishes": "the reference level lies within "
                                   "this bar's reported range",
                    "does_not_establish": [
                        "the intrabar direction of the touch",
                        "the intrabar sequence of events",
                        "any orders/liquidity at the level",
                    ],
                    "level_entered_range_at_this_bar":
                        (None if prev_contains is None
                         else (not prev_contains)),
                    "previous_bar_range_contains_level": prev_contains,
                    "close_side_of_level": close_side,
                },
                "known_at_selection": [
                    f"context ref {ref.candidate_id} confirmed at its "
                    f"knowable bar (before this bar)",
                    f"bar OHLC at {t}",
                ],
                "source_caveat": "'near support' is NOT operationally "
                                 "resolved (corpus marks the wording "
                                 "ambiguous); this relation does not "
                                 "claim to be the speaker's definition "
                                 "and is not called 'traded through'",
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
            "reason": "declared research definition matched (exact-"
                      "level relation + order statistic; no invented "
                      "distance); awaiting the later-evidence event "
                      "(never confirmed at formation)",
            "evidence": [cand.candidate_id, ref.candidate_id]})

    # ---- candidate updates (confirmation / revisit / ordering) ------
    def _update_candidates(self, record, bars) -> List[dict]:
        changes: List[dict] = []
        upto = int(record.as_of_bar)
        for c in self.candidates:
            if c.state not in (STATE_CANDIDATE,
                               STATE_AWAITING_CONFIRMATION):
                continue
            if c.state == STATE_CANDIDATE:
                c.to_awaiting(at_bar=c.bar_index, at_time=c.bar_time,
                              evidence={"bar": c.bar_index})
            start = max(c.bar_index + 1, c.scan_floor + 1)
            for j in range(start, upto + 1):
                o = float(bars["open"].iloc[j])
                h = float(bars["high"].iloc[j])
                l = float(bars["low"].iloc[j])
                cl = float(bars["close"].iloc[j])
                t = pd.Timestamp(bars.index[j])
                if c.direction == "bullish":
                    conf, rev = h > c.high, l <= c.low
                else:
                    conf, rev = l < c.low, h >= c.high
                if conf and rev:
                    # both events possible inside one bar
                    iv = _bars_interval(bars, j)
                    res = self._try_buffer_resolution(c, *iv)
                    if res is not None:
                        cf, rv = res
                        c.ambiguous_bar = j
                        c.ambiguity_interval = (str(iv[0]), str(iv[1]))
                        c.fine_touches = {"confirm": cf,
                                          "revisit": rv}
                        c.ordering = UNKNOWN_ORDERING
                        c.events.append({
                            "kind": "ordering_unresolved", "at": t,
                            "bar": int(j),
                            "note": "confirmation and revisit could "
                                    "both have occurred inside this "
                                    "bar; fine rows were checked at "
                                    "detection",
                            "layer": LAYER_UNKNOWN})
                        c.scan_floor = j
                        changes += self._resolve_ambiguity_if_possible(
                            c, recorded_at=pd.Timestamp(
                                bars.index[int(record.as_of_bar)]))
                        continue
                    c.ambiguous_bar = j
                    c.ambiguity_interval = (str(iv[0]), str(iv[1]))
                    c.ordering = UNKNOWN_ORDERING
                    c.fine_touches = {}
                    c.events.append({
                        "kind": "ordering_unresolved", "at": t,
                        "bar": int(j),
                        "note": "confirmation and revisit could both "
                                "have occurred inside this bar; OHLC "
                                "cannot order them; state stays "
                                "UNDECIDED and the flattering order is "
                                "refused (scoped to THIS bar only)",
                        "layer": LAYER_UNKNOWN})
                    c.scan_floor = j
                    changes.append({
                        "aspect": "candidate", "before": c.state,
                        "after": c.state + " (ordering UNKNOWN)",
                        "reason": "same-bar confirm/revisit: ordering "
                                  "unresolvable from OHLC",
                        "evidence": [c.candidate_id, str(j)]})
                    continue
                if conf:
                    ev = c.to_confirmed(
                        at_bar=j, at_time=t,
                        evidence={"bar": int(j), "close": cl,
                                  "rule": "a bar traded through the "
                                          "candidate extreme "
                                          "(declared)",
                                  "prior_open_ambiguity":
                                      c.ambiguous_bar})
                    c.scan_floor = j
                    self.seq_facts.append({
                        "kind": "CONFIRMATION_EVENT", "at": t,
                        "candidate_id": c.candidate_id, "bar": int(j),
                        "layer": LAYER_OBSERVATION})
                    changes.append({
                        "aspect": "candidate",
                        "before": STATE_AWAITING_CONFIRMATION,
                        "after": STATE_CONFIRMED,
                        "reason": ev["reason"],
                        "evidence": ev["evidence"]})
                    break
                if rev:
                    c.events.append({
                        "kind": "revisit_event", "at": t, "bar": int(j),
                        "note": "return to the candidate area's far "
                                "boundary observed",
                        "layer": LAYER_OBSERVATION})
                c.scan_floor = j
        return changes

    # ---- evidence-evaluated roles ------------------------------------
    def _update_roles(self, record) -> List[dict]:
        changes: List[dict] = []
        hf_ok = self.hf_context.get("trend") not in ("unknown", None)
        for c in self.candidates:
            evidence = {
                "hf_established": hf_ok,
                "confirmation_event": c.state == STATE_CONFIRMED,
                "reaction_observed": any(
                    e.get("kind") == "revisit_event" for e in c.events),
                "refs": {
                    "hf_established":
                        self.hf_context.get("established_at"),
                    "confirmation_event": next(
                        (str(e.get("at")) for e in c.events
                         if e.get("kind") == "state_transition"
                         and e.get("to") == STATE_CONFIRMED), None),
                    "reaction_observed": next(
                        (str(e.get("at")) for e in c.events
                         if e.get("kind") == "revisit_event"), None),
                },
            }
            verdict = assign_role(candidate_direction=c.direction,
                                  hf_trend=str(self.hf_context.get(
                                      "trend")),
                                  task=self.task, evidence=evidence)
            key = (verdict["role"], verdict["supported"],
                   verdict["evidence_used"]["confirmation_event"]
                   ["value"],
                   verdict["evidence_used"]["reaction_observed"]
                   ["value"],
                   verdict["evidence_used"]["hf_established"]["value"])
            last = c.role_assignments[-1] if c.role_assignments else None
            last_key = None
            if last is not None:
                last_key = (
                    last["role"], last.get("supported"),
                    last["evidence_used"]["confirmation_event"]["value"],
                    last["evidence_used"]["reaction_observed"]["value"],
                    last["evidence_used"]["hf_established"]["value"])
            if key == last_key:
                continue
            c.role_assignments.append(verdict)
            c.role = verdict["role"]
            self.seq_facts.append({
                "kind": "ROLE_EVALUATED", "at":
                    pd.Timestamp(record.as_of_time),
                "candidate_id": c.candidate_id, "role": c.role,
                "supported": verdict["supported"],
                "layer": LAYER_INTERPRETATION})
            changes.append({
                "aspect": "candidate_role", "before":
                    (last["role"] if last else ROLE_UNDETERMINED),
                "after": c.role,
                "reason": verdict["reasons"][0],
                "evidence": [c.candidate_id] +
                            list(verdict.get("alternatives", []))})
        return changes

    # ---- E03 slice: reference crossings -> shift-watches -------------
    def _scan_reference_crossings(self, record, bars, world
                                  ) -> List[dict]:
        """A crossing = a close-to-close transition across a confirmed
        reference level between two consecutive completed bars (the
        engine's close-through relation at bar granularity).  It OPENS
        a shift-watch — it is NOT proof of a shift."""
        changes: List[dict] = []
        upto = int(record.as_of_bar)
        refs = [p for p in world["by_id"].values()
                if getattr(p, "status", "") == "confirmed"]
        from_j = max(1, self._cross_scan_upto + 1)
        for j in range(from_j, upto + 1):
            close = float(bars["close"].iloc[j])
            prev_close = float(bars["close"].iloc[j - 1])
            t = pd.Timestamp(bars.index[j])
            for r in refs:
                if not (int(r.occurrence_bar) < j - 1):
                    continue
                lvl = float(r.level)
                down = prev_close > lvl and close <= lvl
                up = prev_close < lvl and close >= lvl
                if not (down or up):
                    continue
                direction = "downward" if down else "upward"
                key = (r.candidate_id, direction)
                if key in self._crossed_keys:
                    continue
                self._crossed_keys.add(key)
                # the local swing of the opposite side formed before
                # the crossing (E03-B sequence element)
                local = None
                for p in refs:
                    if p.side != r.side and \
                            int(p.occurrence_bar) < j - 1:
                        if local is None or int(p.occurrence_bar) > \
                                int(local.occurrence_bar):
                            local = p
                self._watch_seq += 1
                watch = ShiftWatch(
                    watch_id=f"SW-{self.run_id}-{self._watch_seq:04d}",
                    opened_at=t,
                    crossing={
                        "ref_id": r.candidate_id,
                        "ref_side": r.side, "ref_level": lvl,
                        "bar": int(j), "bar_time": str(t),
                        "previous_close": prev_close,
                        "close": close, "direction": direction,
                        "transition": "close-to-close transition "
                                      "across the level between two "
                                      "completed bars (intrabar path "
                                      "NOT established)",
                    },
                    local_ref_id=(local.candidate_id
                                  if local is not None else None),
                    local_ref_level=(float(local.level)
                                     if local is not None else None),
                    scan_floor=int(j))
                self.shift_watches.append(watch)
                self.seq_facts.append({
                    "kind": "REFERENCE_CROSSING", "at": t,
                    "ref_id": r.candidate_id, "level": lvl,
                    "direction": direction, "bar": int(j),
                    "layer": LAYER_OBSERVATION})
                self.seq_facts.append({
                    "kind": "SHIFT_WATCH_OPENED", "at": t,
                    "watch_id": watch.watch_id,
                    "note": "crossing an old reference is a context "
                            "for WATCHING a possible shift, NOT proof "
                            "of one (E03-A); no reversal/trade signal",
                    "layer": LAYER_INTERPRETATION})
                changes.append({
                    "aspect": "shift_watch", "before": "(none)",
                    "after": f"{watch.watch_id} {watch.status}",
                    "reason": "a close-to-close transition across a "
                              "confirmed reference level opened a "
                              "shift-watch (context for watching, not "
                              "proof of a shift)",
                    "evidence": [watch.watch_id, r.candidate_id,
                                 str(t)]})
        self._cross_scan_upto = max(self._cross_scan_upto, upto)
        return changes

    def _update_shift_watches(self, record, bars, world) -> List[dict]:
        changes: List[dict] = []
        upto = int(record.as_of_bar)
        for w in self.shift_watches:
            start = max(0, w.scan_floor + 1)
            cr = w.crossing
            ch_bar = int(cr["bar"])
            for j in range(start, upto + 1):
                o = float(bars["open"].iloc[j])
                h = float(bars["high"].iloc[j])
                l = float(bars["low"].iloc[j])
                c = float(bars["close"].iloc[j])
                t = pd.Timestamp(bars.index[j])
                # closed-bar non-overlap in the crossing direction
                # (E03-B 'displacement/non-overlap'); exact relation
                ch_h = float(bars["high"].iloc[ch_bar])
                ch_l = float(bars["low"].iloc[ch_bar])
                displaced = (l > ch_h) if cr["direction"] == "upward" \
                    else (h < ch_l)
                if displaced:
                    ev = w.note_evidence(
                        kind="displacement_non_overlap", at=t,
                        at_bar=j,
                        detail={"bar": int(j),
                                "relation": "closed bar does not "
                                            "overlap the crossing "
                                            "bar's range"})
                    self.seq_facts.append({
                        "kind": "SHIFT_EVIDENCE_NOTED", "at": t,
                        "watch_id": w.watch_id,
                        "evidence_kind": ev["kind"], "bar": int(j),
                        "layer": LAYER_OBSERVATION})
                    changes.append({
                        "aspect": "shift_watch", "before":
                            SHIFT_STATUS_WATCHING,
                        "after": w.status,
                        "reason": "closed-bar non-overlap observed in "
                                  "the crossing direction (evidence "
                                  "only; not proof of a shift)",
                        "evidence": [w.watch_id, str(t)]})
                # local-swing crossing (E03-B sequence element)
                if w.local_ref_level is not None and j > 0:
                    pc = float(bars["close"].iloc[j - 1])
                    lvl = float(w.local_ref_level)
                    crossed = (pc < lvl <= c) or (pc > lvl >= c)
                    if crossed:
                        ev = w.note_evidence(
                            kind="local_swing_crossing", at=t,
                            at_bar=j,
                            detail={"bar": int(j), "level": lvl,
                                    "local_ref": w.local_ref_id,
                                    "relation": "close-to-close "
                                                "transition across "
                                                "the local swing "
                                                "level"})
                        self.seq_facts.append({
                            "kind": "SHIFT_EVIDENCE_NOTED", "at": t,
                            "watch_id": w.watch_id,
                            "evidence_kind": ev["kind"], "bar": int(j),
                            "layer": LAYER_OBSERVATION})
                        changes.append({
                            "aspect": "shift_watch", "before":
                                SHIFT_STATUS_WATCHING,
                            "after": w.status,
                            "reason": "local-swing crossing observed "
                                      "(E03-B sequence evidence; "
                                      "still not proof of a shift)",
                            "evidence": [w.watch_id, str(t)]})
                w.scan_floor = j
        return changes

    def _ledger_sync_watch(self, watch: ShiftWatch, ledger) -> None:
        sig = (watch.status, len(watch.evidence))
        if self._ledger_sigs.get(watch.watch_id) == sig:
            return
        res = SelectionResult(
            task_id="T-STUDY-SHIFT-WATCH",
            decision_bar=int(watch.crossing["bar"]),
            status="unresolved",
            selected_id=watch.watch_id,
            survivors=[], excluded=[], unresolved=None,
            provenance=["E03-A", "E03-B"],
            policy_refs=["RESEARCH_CONFIG_ONLY"],
            representation_id="study-links-v1",
            notes=[f"status={watch.status}",
                   f"evidence={len(watch.evidence)}",
                   f"direction={watch.crossing['direction']}"],
            decision_time=pd.Timestamp(watch.opened_at),
            direction=watch.crossing["direction"])
        payload = {
            "kind": "study_shift_watch",
            "run_id": self.run_id,
            "inputs": {"crossing": _jsonable(watch.crossing),
                       "evidence": _jsonable(watch.evidence),
                       "questions": list(watch.questions)},
            "definitions": {"statuses": list(SHIFT_STATUSES),
                            "semantics": "crossing is a context for "
                                         "watching a possible shift, "
                                         "NOT proof of one; no "
                                         "reversal/trade signal"},
            "revision_of": self._ledger_uids.get(watch.watch_id),
            "stale": False, "stale_reason": None,
            "recompute_supported": False, "recompute": None,
            "recorded_event_times": [str(e.get("at"))
                                     for e in watch.evidence],
            "ledger_version_before": len(ledger.results),
            "ledger_version_after": None,
            "depends_on_results": [],
        }
        uid = ledger.record(res, payload)
        payload["ledger_version_after"] = len(ledger.results)
        self._ledger_uids[watch.watch_id] = uid
        self._ledger_sigs[watch.watch_id] = sig

    # ---- ledger integration (existing InterpretationLedger) ----------
    def _ledger_sync(self, cand: OBLikeCandidate, ledger) -> None:
        # record a NEW version only when something actually changed
        # (genuine revision); the dedupe compares an evidence signature,
        # never the ledger uid string
        sig = (len(cand.events), cand.state, str(cand.ordering),
               cand.role)
        if self._ledger_sigs.get(cand.candidate_id) == sig:
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
        self._ledger_sigs[cand.candidate_id] = sig

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
                    f"the candidate extreme {confirm_level}: a later "
                    f"completed bar whose reported high exceeds it "
                    f"(source wording 'is traded through'; intrabar "
                    f"sequence not established) -> CONFIRMED at the "
                    f"evidence bar",
                    f"return to {revisit_level} -> revisit event "
                    f"(same-bar with confirmation -> ordering UNKNOWN "
                    f"for THAT bar only; the candidate stays open)",
                    f"context reference {c.context_ref_id} at "
                    f"{c.context_ref_level}: a completed close through "
                    f"it before confirmation -> role premise failed",
                ],
                "revision_conditions": [
                    "higher-frame structure change re-opens role "
                    "evaluation",
                    "finer rows within an ambiguous bar may resolve "
                    "its ordering (either direction) — recorded when "
                    "available; later bars may still confirm",
                ],
                "unknowns": [
                    "no resting-order data: participant positions/"
                    "intent, resting stops and available liquidity "
                    "CANNOT be established",
                    "the source's 'near support' wording is "
                    "operationally unresolved; the exact-level "
                    "relation used here is an ENGINEERING choice "
                    "(no distance/percentage/candle-count rule exists "
                    "or is claimed)",
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
        for w in self.shift_watches:
            plan.append({
                "subject": w.watch_id,
                "kind": "shift-watch (E03-A/B slice)",
                "state": w.status,
                "time_provenance": {
                    "opened_at": str(w.opened_at),
                    "crossing_bar": w.crossing.get("bar")},
                "watch": list(w.questions),
                "revision_conditions": [
                    "observed evidence is recorded append-only "
                    "(displacement/non-overlap; local-swing crossing); "
                    "there is NO 'shift confirmed' state and NO "
                    "reversal/trade signal",
                ],
                "unknowns": [
                    "a crossing is context for watching a possible "
                    "shift, NOT proof of one (E03-A)",
                    "intrabar path across the level is not "
                    "established by completed bars",
                ],
            })
        for t in self.readings.tasks.values():
            plan.append({
                "subject": t.task_id,
                "kind": "reading task (connected readings)",
                "state": t.conclusion.get("status"),
                "watch": [w.get("observable_event", "")
                          for w in t.watch_next],
                "revision_conditions": [
                    "a new candidate or interaction that changes the "
                    "declared-evidence comparison appends a new "
                    "conclusion version (old versions preserved)",
                ],
                "unknowns": [
                    "preference is task-scoped evidence, not a "
                    "prediction",
                ],
            })
        for i in self.readings.interps.values():
            plan.append({
                "subject": i.interp_id,
                "kind": "working interpretation",
                "state": i.status,
                "watch": [w.get("observable_event", "")
                          for w in i.watch],
                "revision_conditions": [
                    "relevant new evidence appends a linked version; "
                    "the prior version is preserved; a weakening "
                    "hypothesis never flips automatically",
                ],
                "unknowns": ["no trade/entry meaning is implied"],
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
            "readings": self.readings.state_dict(),
            "last_ref_records": [dict(r) for r in self._last_ref_records],
            "shift_watches": [w.to_record() for w in self.shift_watches],
            "cross_scan_upto": self._cross_scan_upto,
            "crossed_keys": sorted(f"{k[0]}|{k[1]}"
                                   for k in self._crossed_keys),
            "watch_seq": self._watch_seq,
            "ledger_uids": dict(self._ledger_uids),
            "ledger_sigs": {k: list(v) for k, v in
                            self._ledger_sigs.items()},
            "row_buffer": _jsonable(self._row_buffer[-2000:]),
            "selection_quality": "NOT_ESTABLISHED",
        }

    def load_state_dict(self, st: dict) -> None:
        self._scan_upto = int(st.get("scan_upto", -1))
        self._cand_seq = int(st.get("cand_seq", 0))
        if st.get("readings"):
            self.readings = ConnectedReadingsEngine(
                run_id=f"{self.run_id}-cr", instrument=self.instrument,
                timezone="UTC")
            self.readings.load_state_dict(st["readings"])
        self._last_ref_records = [dict(r) for r in
                                  st.get("last_ref_records", [])]
        self._cross_scan_upto = int(st.get("cross_scan_upto", -1))
        self._watch_seq = int(st.get("watch_seq", 0))
        self._crossed_keys = set()
        for s in st.get("crossed_keys", []):
            rid, _, d = s.partition("|")
            self._crossed_keys.add((rid, d))
        self.shift_watches = []
        for d in st.get("shift_watches", []):
            w = ShiftWatch(
                watch_id=d["watch_id"],
                opened_at=pd.Timestamp(d["opened_at"]),
                crossing=dict(d["crossing"]),
                local_ref_id=d.get("local_ref_id"),
                local_ref_level=d.get("local_ref_level"),
                questions=d.get("questions", list(SHIFT_QUESTIONS)),
                evidence=d.get("evidence", []),
                status=d.get("status", SHIFT_STATUS_WATCHING),
                scan_floor=int(d.get("scan_floor", -1)))
            self.shift_watches.append(w)
        self.hf_context = dict(st.get("hf_context", {}))
        self._ledger_uids = dict(st.get("ledger_uids", {}))
        self._ledger_sigs = {k: tuple(v) for k, v in
                             st.get("ledger_sigs", {}).items()}
        self.seq_facts = list(st.get("seq_facts", []))
        self._row_buffer = list(st.get("row_buffer", []))
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
                ambiguity_interval=(
                    tuple(d["ambiguity_interval"])
                    if d.get("ambiguity_interval") else None),
                fine_touches={k: (pd.Timestamp(v) if v else None)
                              for k, v in
                              d.get("fine_touches", {}).items()},
                scan_floor=int(d.get("scan_floor", -1)))
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
