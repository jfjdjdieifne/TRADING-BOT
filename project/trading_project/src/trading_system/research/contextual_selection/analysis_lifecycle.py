"""Contextual analysis lifecycle V1 — the end-to-end analytical chain.

This module IS the deliverable "causal trading intelligence" layer the
final report describes: a *bounded analytical lifecycle* over the existing
approved components — observations, structural facts, interpretations,
conditional forecasts, and one next awaited observation.  It is NOT a
trading signal, NOT a rigid signal bot, and never claims proven accuracy.

Design contract (task):
  * every as-of decision goes through the closed information-time contract
    (``SharedInformationAxis`` over the sealed 6.2A-0 module); there is no
    second causal clock;
  * the structural-reference layer is BUILT ON ``task_s1_structural_reference``
    (via the existing ``expert_structural_reference_selection`` pipeline)
    and ``task_s5_falsifier``, F-K swing points and SP-03/SP-04/SP-05;
  * the existing ``InterpretationLedger`` records the engine's task results
    with COMPLETE recomputation payloads — no parallel selection engine and
    no disconnected parallel history;
  * conditional forecasts are recorded BEFORE their conditions when possible
    (``observed_before_record=False``) and revised only by appending new
    immutable versions (prior versions keep their original wording);
  * a condition that already occurred before its record is never presented
    as pre-event prediction (``observed_before_record=True`` + state
    CONDITION_ALREADY_OBSERVED);
  * missing / future / off-grid / unmappable / inconsistent evidence is
    RECORDED as unavailable with an explicit reason and never affects the
    analysis;
  * multi-timeframe material is aligned by availability (completion) times;
    an incomplete higher-timeframe bar is never used (consumed frames are
    truncated to completed rows only);
  * position state is supplied / absent / unknown — never inferred from
    price structure;
  * ``selection_quality`` stays ``NOT_ESTABLISHED``.

Claim classes (every claim in every record carries one):
    directly-stated | paraphrase | engineering-interpretation |
    research-hypothesis | unsupported-or-unavailable

Methodological direction: Michael Huddleston's publicly documented work
(ICT).  Only statements verified against the pinned knowledge register
(``knowledge_foundation``) or against the source transcripts are ever
attributed; a URL or a title is not evidence.  This engine is NOT Michael,
does NOT replicate his private judgment, and has NO proven accuracy.

Life-cycle states (analytical, never a trading signal):
    INSUFFICIENT_CONTEXT | INTERPRETATIONS_FORMING | MONITORING |
    PENDING_CONDITION | CONDITION_ALREADY_OBSERVED |
    SOURCE_DEFINED_CONFIRMATION_ONLY_IF_DEFINED | WEAKENED |
    CONTRADICTED | INVALIDATED | RECONSTRUCTED
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd

from trading_system.research.contextual_selection.csm import (
    KIND_RESEARCH,
    InterpretationLedger,
    PolicyRegistry,
    Representation,
    SharedInformationAxis,
    STATUS_CONFIRMED,
    TIE_FT_EQ_FIRST,
    build_legs,
    fk_turning_points,
    sp03_binding,
    sp05_containment,
    task_s5_falsifier,
)
from trading_system.research.contextual_selection.expert_selection import (
    ContextualRelationships,
    EvidenceItem,
    ExpertSelection,
    EXPERT_KNOWLEDGE_SRS_V1,
    OUTCOME_SELECTED,
    OUTCOME_UNRESOLVED,
    VALID_ROLES,
    expert_structural_reference_selection,
    validate_relationship_stamp,
)

__all__ = [
    "SourceRecord", "StructuralFact", "Interpretation",
    "ForecastCondition", "ForecastVersion", "AnalysisRecord",
    "AnalysisEngine", "SOURCE_REGISTER",
    "CLAIM_DIRECT", "CLAIM_PARAPHRASE", "CLAIM_ENGINEERING",
    "CLAIM_HYPOTHESIS", "CLAIM_UNSUPPORTED",
    "STATE_INSUFFICIENT", "STATE_INTERPRETATIONS", "STATE_MONITORING",
    "STATE_PENDING", "STATE_ALREADY_OBSERVED", "STATE_CONFIRMATION_ONLY",
    "STATE_WEAKENED", "STATE_CONTRADICTED", "STATE_INVALIDATED",
    "STATE_RECONSTRUCTED",
    "MODE_LIVE", "MODE_RECONSTRUCTED",
]

# --------------------------------------------------------------------- #
# claim classification vocabulary (task: exactly these five)             #
# --------------------------------------------------------------------- #
CLAIM_DIRECT = "directly-stated"
CLAIM_PARAPHRASE = "paraphrase"
CLAIM_ENGINEERING = "engineering-interpretation"
CLAIM_HYPOTHESIS = "research-hypothesis"
CLAIM_UNSUPPORTED = "unsupported-or-unavailable"
CLAIM_CLASSES = (CLAIM_DIRECT, CLAIM_PARAPHRASE, CLAIM_ENGINEERING,
                 CLAIM_HYPOTHESIS, CLAIM_UNSUPPORTED)

# --------------------------------------------------------------------- #
# lifecycle states                                                       #
# --------------------------------------------------------------------- #
STATE_INSUFFICIENT = "INSUFFICIENT_CONTEXT"
STATE_INTERPRETATIONS = "INTERPRETATIONS_FORMING"
STATE_MONITORING = "MONITORING"
STATE_PENDING = "PENDING_CONDITION"
STATE_ALREADY_OBSERVED = "CONDITION_ALREADY_OBSERVED"
STATE_CONFIRMATION_ONLY = "SOURCE_DEFINED_CONFIRMATION_ONLY_IF_DEFINED"
STATE_WEAKENED = "WEAKENED"
STATE_CONTRADICTED = "CONTRADICTED"
STATE_INVALIDATED = "INVALIDATED"
STATE_RECONSTRUCTED = "RECONSTRUCTED"
LIFECYCLE_STATES = (STATE_INSUFFICIENT, STATE_INTERPRETATIONS,
                    STATE_MONITORING, STATE_PENDING,
                    STATE_ALREADY_OBSERVED, STATE_CONFIRMATION_ONLY,
                    STATE_WEAKENED, STATE_CONTRADICTED,
                    STATE_INVALIDATED, STATE_RECONSTRUCTED)

MODE_LIVE = "live-observed"
MODE_RECONSTRUCTED = "reconstructed"

_POSITION_ABSENT = "absent"


# --------------------------------------------------------------------- #
# source register: verified claims only                                  #
# --------------------------------------------------------------------- #
@dataclass
class SourceRecord:
    source_id: str
    kind: str
    locator: str
    published: str
    quoted_passage: Optional[str]
    claim_class: str
    verification_status: str
    claims_stated: List[str]
    claims_unavailable: List[str]
    permitted_use: str

    def to_record(self) -> dict:
        return dataclasses.asdict(self)


def _src(source_id, kind, locator, published, quote=None,
         claim_class=CLAIM_UNSUPPORTED, verification="unverified",
         claims_stated=None, claims_unavailable=None, permitted_use=""):
    return SourceRecord(
        source_id=source_id, kind=kind, locator=locator,
        published=published, quoted_passage=quote,
        claim_class=claim_class, verification_status=verification,
        claims_stated=list(claims_stated or []),
        claims_unavailable=list(claims_unavailable or []),
        permitted_use=permitted_use)


_K_REP = ("knowledge_foundation 6c8bf6fd (12_SOURCE_INDEX, "
          "15_CONTEXTUAL_SELECTION_METHOD, 16_SWING_WAVE_SELECTION)")

SOURCE_REGISTER: Tuple[SourceRecord, ...] = (
    _src("SRS-FK", "method-pinned-knowledge", _K_REP, "2026-10",
         claim_class=CLAIM_PARAPHRASE,
         verification="verified against pinned knowledge_foundation",
         claims_stated=[
             "F-K k-bar turning point with causal confirmation: a candidate "
             "is knowable only at the close of the k-th bar after it",
             "SP-13 / SWS-04: occurrence time and confirmation (knowable) "
             "time are preserved separately"],
         permitted_use="operational definition of turning points and their "
                       "knowability (engineering implementation)"),
    _src("SRS-TS5", "method-pinned-knowledge", _K_REP, "2026-10",
         claim_class=CLAIM_PARAPHRASE,
         verification="verified against pinned knowledge_foundation",
         claims_stated=[
             "T-S5 / SP-04: a reference-form claim maps to its falsifier "
             "reference; a claim not written in reference terms is MP",
             "the falsifier's violation weakens/invalidates the "
             "interpretation that rests on it"],
         permitted_use="conditional-forecast semantics (if-event -> "
                       "loses-support)"),
    _src("SRS-SP03", "method-pinned-knowledge", _K_REP, "2026-10",
         claim_class=CLAIM_PARAPHRASE,
         verification="verified against pinned knowledge_foundation",
         claims_stated=[
             "SP-03 close-basis binding: a reference is bound iff the "
             "closing price is beyond its level on the break side",
             "equality is not a crossing (TIE-CROSS-EQUAL-UNBOUND-V1)"],
         permitted_use="operational definition of the violation condition"),
    _src("SRS-SP04", "method-pinned-knowledge", _K_REP, "2026-10",
         claim_class=CLAIM_PARAPHRASE,
         verification="verified against pinned knowledge_foundation",
         claims_stated=[
             "SP-04: reference-form interpretation claims carry falsifier "
             "references; violation changes the interpretation's status"],
         permitted_use="falsifier wiring"),
    _src("SRS-SP05", "method-pinned-knowledge", _K_REP, "2026-10",
         claim_class=CLAIM_PARAPHRASE,
         verification="verified against pinned knowledge_foundation",
         claims_stated=[
             "SP-05 containment: a fine move is contained | escaping | "
             "disjoint relative to a coarse move (verified timestamps)"],
         permitted_use="cross-scale structural facts"),
    _src("SRS-TAKEN", "method-pinned-knowledge", _K_REP, "2026-10",
         claim_class=CLAIM_PARAPHRASE,
         verification="verified against pinned knowledge_foundation",
         claims_stated=[
             "taken-state observations are STATE-only observations; they "
             "establish state, not cause"],
         permitted_use="state observation records; no causal claims"),
    _src("SRS-CLAIM-SEM", "research-task-corpus",
         "final task + pinned knowledge claim-class table", "2026-10",
         claim_class=CLAIM_DIRECT,
         verification="directly stated in the task specification",
         claims_stated=[
             "claim classes: directly-stated | paraphrase | "
             "engineering-interpretation | research-hypothesis | "
             "unsupported-or-unavailable",
             "a URL or a title is not evidence; unverified claims must be "
             "marked and never attributed"],
         permitted_use="claim-classification semantics"),
    _src("SRS-ICT-OB", "public-video-partial-transcript",
         "youtube.com/watch?v=PIYh0CxoY9c (order block)",
         "2024-09-16 (per task)",
         quote="opening lines only (P1 partial transcript)",
         claim_class=CLAIM_UNSUPPORTED,
         verification="partial transcript: opening lines only; the "
                     "operative definitions were not available",
         claims_unavailable=[
             "an exact operational order-block definition",
             "an exact candle count / percentage rule"]),
    _src("SRS-ICT-FVG", "public-video-partial-transcript",
         "youtube.com/watch?v=FgacYSN9QEo (fair value gap)",
         "2024-09-16 (per task)",
         quote="opening lines only (P1 partial transcript)",
         claim_class=CLAIM_UNSUPPORTED,
         verification="partial transcript: opening lines only",
         claims_unavailable=[
             "an exact operational fair-value-gap definition"]),
    _src("SRS-ICT-M22-E3", "public-video-unverified",
         "youtube.com/watch?v=nQfHZ2DEJ8c (2022 mentorship Ep3)",
         "date not verified", claim_class=CLAIM_UNSUPPORTED,
         verification="NOT verified: no transcript/passage available; "
                     "the pinned register does not contain this URL",
         claims_unavailable=["any specific definition or number"]),
    _src("SRS-ICT-M22-E12", "public-video-unverified",
         "youtube.com/watch?v=8GkQfdAXZP0 (2022 mentorship Ep12)",
         "date not verified", claim_class=CLAIM_UNSUPPORTED,
         verification="NOT verified: no transcript/passage available",
         claims_unavailable=["any specific definition or number"]),
    _src("SRS-ICT-FVG-24", "public-video-unverified",
         "youtube.com/watch?v=HhgWGduYQZQ (2024-09-16 FVG)",
         "2024-09-16 (title claim; not independently verified)",
         claim_class=CLAIM_UNSUPPORTED,
         verification="NOT verified: no transcript/passage available",
         claims_unavailable=["any specific definition or number"]),
)
SOURCE_BY_ID = {s.source_id: s for s in SOURCE_REGISTER}


# --------------------------------------------------------------------- #
# records                                                                #
# --------------------------------------------------------------------- #
@dataclass
class StructuralFact:
    fact_id: str
    kind: str
    as_of_time: Optional[pd.Timestamp]
    as_of_bar: Optional[int]
    description: str
    inputs: Dict[str, Any]
    dependencies: List[str]
    basis: str
    claim_class: str
    verification: str

    def to_record(self) -> dict:
        d = dataclasses.asdict(self)
        if self.as_of_time is not None:
            d["as_of_time"] = str(self.as_of_time)
        return d


@dataclass
class Interpretation:
    interpretation_id: str
    version: int
    label: str
    status: str                      # active | alternative-monitoring |
                                     # weakened | contradicted | invalidated
    scope: str
    description: str
    as_of_time: Optional[pd.Timestamp]
    supporting_evidence: List[str]
    opposed_evidence: List[str]
    alternative_explanations: List[str]
    alternative_ids: List[str]
    falsifier_reference: Optional[str]
    would_be_supported_by: List[str]
    would_be_weakened_by: List[str]
    next_discriminating_observation: str
    invalidating_observations: List[str]
    dependencies: List[str]
    unknowns: List[str]
    claim_class: str
    provenance: List[str]
    note: str = ""
    data: Dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> dict:
        d = dataclasses.asdict(self)
        if self.as_of_time is not None:
            d["as_of_time"] = str(self.as_of_time)
        return d


@dataclass
class ForecastCondition:
    detector: str
    executable: bool
    definition: str
    basis: str
    claim_class: str

    def to_record(self) -> dict:
        return dataclasses.asdict(self)


@dataclass
class ForecastVersion:
    forecast_id: str
    version: int
    analysis_ref: str
    asof_time: pd.Timestamp
    asof_bar: int
    task_id: str
    role: str
    condition: ForecastCondition
    if_event: str
    then_effect: str
    interpretation_id: str
    support_description: str
    weaken_description: str
    next_observation: str
    status: str                  # pending | already_observed |
                                 # condition_observed (post-record)
    status_evidence: List[dict]
    observed_before_record: bool
    revises: Optional[str]
    dependencies: List[str]
    provenance: List[str]
    market_state_snapshot: Dict[str, Any]

    def to_record(self) -> dict:
        d = dataclasses.asdict(self)
        d["asof_time"] = str(self.asof_time)
        d["condition"] = self.condition.to_record()
        return d


@dataclass
class AnalysisRecord:
    analysis_id: str
    analysis_version: int
    as_of_time: pd.Timestamp
    as_of_bar: int
    observation_mode: str
    observation_note: str
    task_id: str
    task_name: str
    task_scale: str
    role: str
    role_semantics: str
    policy_id: str
    policy_kind: str
    observed_state: str
    lifecycle_state: str
    prior_state: Optional[str]
    revision_reason: Optional[str]
    structural_facts: List[StructuralFact]
    interpretations: List[Interpretation]
    supporting_evidence: List[dict]
    conflicting_evidence: List[dict]
    reference_status: Dict[str, Any]
    forecasts: List[ForecastVersion]
    next_discriminating_observation: str
    invalidating_observations: List[str]
    position_status: str
    position_note: str
    sources: List[str]
    source_claim_classes: Dict[str, str]
    dependencies: List[str]
    rejected_evidence: List[dict]
    selection_quality: str
    limitations: List[str]
    unresolved: List[str]
    prior: Optional[str]
    revises: Optional[str]
    ledger_uids: List[str]
    csm_payload: Dict[str, Any]
    run_id: str

    def to_record(self) -> dict:
        d = dataclasses.asdict(self)
        d["as_of_time"] = str(self.as_of_time)
        d["structural_facts"] = [f.to_record() for f in
                                self.structural_facts]
        d["interpretations"] = [i.to_record() for i in
                                self.interpretations]
        d["forecasts"] = [f.to_record() for f in self.forecasts]
        return d

    def to_explanation(self) -> str:
        L = [f"### {self.analysis_id} v{self.analysis_version} — "
             f"as of {self.as_of_time} (UTC)  [{self.observation_mode}]"]
        L.append(f"lifecycle: {self.lifecycle_state}"
                 + (f" (was {self.prior_state})" if self.prior_state
                    else ""))
        if self.revision_reason:
            L.append(f"revision reason: {self.revision_reason}")
        L.append(f"observed state: {self.observed_state}")
        for f in self.structural_facts:
            L.append(f"fact [{f.claim_class}] {f.fact_id}: {f.description}")
        for i in self.interpretations:
            L.append(f"interpretation {i.interpretation_id} "
                     f"({i.status}, [{i.claim_class}]): {i.description}")
            for s in i.supporting_evidence[:3]:
                L.append(f"    supports: {s}")
            for o in i.opposed_evidence[:3]:
                L.append(f"    opposed : {o}")
            for a in i.alternative_explanations[:2]:
                L.append(f"    alternative: {a}")
            if i.falsifier_reference:
                L.append(f"    falsifier reference: "
                         f"{i.falsifier_reference}")
            L.append(f"    next discriminating observation: "
                     f"{i.next_discriminating_observation}")
        for fc in self.forecasts:
            v = fc
            L.append(f"forecast {fc.forecast_id} v{fc.version} "
                     f"[{fc.status}"
                     + (", observed_before_record=True"
                        if fc.observed_before_record else "")
                     + (f", revises {fc.revises}" if fc.revises else "")
                     + "]")
            L.append(f"    if: {fc.if_event}  then: {fc.then_effect}")
        L.append("reference: " + json.dumps(self.reference_status,
                                            default=str))
        L.append(f"next awaited observation: "
                 f"{self.next_discriminating_observation}")
        L.append(f"position status: {self.position_status} "
                 f"({self.position_note})")
        L.append(f"selection_quality = {self.selection_quality}")
        for u in self.unresolved:
            L.append(f"unresolved: {u}")
        for r in self.rejected_evidence:
            L.append(f"rejected: {r['item']} — {r['reason']}")
        return "\n".join(L)


# --------------------------------------------------------------------- #
# engine                                                                 #
# --------------------------------------------------------------------- #
class AnalysisEngine:
    """Bounded end-to-end analytical lifecycle over one instrument.

    The engine never decides trades: it produces traceable analysis
    records (observations -> facts -> interpretations -> conditional
    forecasts -> next observation) over the existing approved pipeline.
    """

    TASK_ID = "T-S5"                     # falsifier-following analysis
    TASK_NAME = "contextual-analysis-lifecycle"
    TASK_ROLE = "origin-of-last-confirmed-leg"
    ROLE_SEMANTICS = ("role semantics: origin of the most recent confirmed "
                      "leg (SWS-02; research configuration, never "
                      "owner-approved)")
    POLICY_ID = "P-ORIGIN-RESEARCH"
    VIEW = "C"
    SCALE_LABEL = "coarse"
    POSITION_NOTE = ("no authoritative position feed was supplied; no "
                     "position is inferred from price structure")

    def __init__(
        self,
        *,
        run_id: str,
        frames: Dict[str, pd.DataFrame],
        k: int = 5,
        instrument: str = "BTCUSDT",
        task_scale: str = "4h",
        fine_scale: str = "1h",
        finest_scale: str = "15m",
        ledger: Optional[InterpretationLedger] = None,
    ) -> None:
        if k < 1:
            raise ValueError("k must be a declared positive research value")
        self.run_id = run_id
        self.instrument = instrument
        self.k = k
        self.task_scale = task_scale
        self.fine_scale = fine_scale
        self.finest_scale = finest_scale
        self.frames = frames
        for name, df in frames.items():
            if df.index.tz is None:
                df.index = df.index.tz_localize("UTC")
        # ONE shared information-time axis over the task-scale completion
        # grid (the codebase convention: the scene's bar domain is the
        # axis's coordinate domain).  Every availability decision for
        # points, legs, references and relationship stamps goes through
        # this axis.
        task_index = pd.DatetimeIndex(frames[task_scale].index)
        self.axis = SharedInformationAxis(
            f"{instrument}_{task_scale}_utc_completion", task_index)
        # per-scale axes (the codebase convention: one shared axis per
        # bar domain; cross-scale facts meet on VERIFIED timestamps via
        # SP-05 — never raw cross-domain index arithmetic)
        self._scale_axes = {
            name: SharedInformationAxis(
                f"{instrument}_{name}_utc_completion",
                pd.DatetimeIndex(df.index))
            for name, df in frames.items()}
        self.rep = Representation(family="F-K", view_id=self.VIEW,
                                  scale_label=self.SCALE_LABEL,
                                  params=(("k", float(k)),))
        self.policy = PolicyRegistry()
        self.policy.register(
            self.POLICY_ID, self.ROLE_SEMANTICS, self.TASK_ROLE,
            kind=KIND_RESEARCH)
        self.ledger = ledger if ledger is not None else \
            InterpretationLedger()
        self.records: List[AnalysisRecord] = []
        self.snapshot_path: Optional[str] = None
        self.resumed_from: Optional[str] = None
        self.restored = False
        self._restored_records: List[dict] = []
        self._version_offset = 0
        self._pending_revision_reason: Optional[str] = None

        _id_material = json.dumps({
            "instrument": instrument, "task_scale": task_scale,
            "k": k, "role": self.TASK_ROLE,
            "policy": self.POLICY_ID}, sort_keys=True)
        self.analysis_id = f"AN-{self._hash12(_id_material)}"
        self.forecast_versions: Dict[str, List[ForecastVersion]] = {}
        self._active_forecast_by_ref: Dict[str, str] = {}
        self._forecast_seq = 0

    # ------------------------------------------------------------------ #
    # as-of helpers (ALL causal questions go through the axis)            #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _hash12(s: str) -> str:
        return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]

    def _decision_at(self, as_of: pd.Timestamp) -> Tuple[int, pd.Timestamp]:
        """Verified (task-bar, boundary-time) pair for one as-of instant.

        FAIL CLOSED: an off-grid as-of is INVALID INPUT (ValueError) —
        never an invented coordinate.
        """
        ts = pd.Timestamp(as_of)
        if ts.tzinfo is None:
            ts = ts.tz_localize("UTC")
        key = self.axis.require_key(ts, what="analysis as-of")
        return int(key.bar_position), ts

    def _bars_upto(self, dbar: int) -> pd.DataFrame:
        return self.frames[self.task_scale].iloc[:dbar + 1]

    # ------------------------------------------------------------------ #
    # structural-fact layer (derived, with operational definitions)       #
    # ------------------------------------------------------------------ #
    def _structural_layer(self, *, as_of: pd.Timestamp, dbar: int,
                          world: Dict[str, Any]) -> Tuple[
                              List[StructuralFact], Dict[str, Any]]:
        points: Sequence = world["all_points"]
        legs: Sequence = world["all_legs"]
        clegs = [l for l in legs
                 if l.completed and l.knowable_bar <= dbar]
        facts: List[StructuralFact] = []

        def add(fid, kind, desc, inputs, deps, basis, klass, ver):
            facts.append(StructuralFact(
                fact_id=fid, kind=kind, as_of_time=as_of, as_of_bar=dbar,
                description=desc, inputs=inputs, dependencies=list(deps),
                basis=basis, claim_class=klass, verification=ver))

        last = clegs[-1] if clegs else None
        if last is not None:
            direction = ("up" if last.direction == "up" else "down")
            scale_desc = (f"the last completed {self.k}-confirmation "
                          f"leg on the {self.task_scale} task scale "
                          f"(F-K k={self.k}, scale relative to the "
                          f"declared task)")
            add(f"SF-DIR-{self.run_id}-{dbar}", "derived-movement-direction",
                f"the most recent completed task-scale leg {last.leg_id} "
                f"({last.start_id}->{last.end_id}) moved {direction} "
                f"({scale_desc})",
                {"leg": last.leg_id, "start_id": last.start_id,
                 "end_id": last.end_id, "t0": last.t0, "t1": last.t1,
                 "knowable_bar": last.knowable_bar},
                [last.start_id, last.end_id, last.leg_id],
                "SRS-FK + SRS-CLAIM-SEM", CLAIM_ENGINEERING,
                "derived on the declared task scale; 'movement' is "
                "relative to this scale, never a universal wave size")
        # SP-05 cross-scale containment facts (verified timestamps)
        fine_legs_by_scale: Dict[str, List] = {}
        for scale in (self.fine_scale, self.finest_scale):
            fdf = self._completed_frame(scale, as_of)
            if fdf is None or fdf.empty:
                continue
            fpts = fk_turning_points(
                fdf, self.k, self.rep,
                id_prefix=f"PT-{scale}", allow_short_left=False,
                tie_policy=TIE_FT_EQ_FIRST,
                axis=self._scale_axes[scale])
            fpts = [p for p in fpts if p.status == STATUS_CONFIRMED
                    and p.knowable_time is not None
                    and p.knowable_time <= as_of]
            flegs_amb: List[dict] = []
            flegs = build_legs(fpts, self.rep, completed_only=True,
                               ambiguities=flegs_amb)
            flegs = [l for l in flegs
                     if l.knowable_time is not None
                     and l.knowable_time <= as_of]
            fine_legs_by_scale[scale] = flegs
            add(f"SF-AVL-{scale}-{self.run_id}-{dbar}",
                "derived-frame-availability",
                f"{len(fdf)} completed {scale} bars and "
                f"{len(flegs)} completed {scale} legs are available at "
                f"this boundary (availability = completion time; "
                f"any incomplete higher-timeframe bar is never used)",
                {"scale": scale, "n_completed": int(len(fdf)),
                 "n_legs": int(len(flegs))},
                [f"frame:{scale}"], "SRS-SP05 + SRS-CLAIM-SEM",
                CLAIM_ENGINEERING,
                "counts of completed rows only; no future row is read")
        # SP-05 containment of the latest fine leg inside the task-scale
        # leg (verified timestamps only)
        if last is not None:
            for scale in (self.fine_scale, self.finest_scale):
                fls = fine_legs_by_scale.get(scale) or []
                if not fls:
                    continue
                fl = fls[-1]
                status = sp05_containment(last, fl, tie_inclusive=True)
                add(f"SF-SP05-{scale}-{self.run_id}-{dbar}",
                    "derived-cross-scale-containment",
                    f"the last completed {scale} leg {fl.leg_id} is "
                    f"'{status}' inside the task-scale leg {last.leg_id} "
                    f"(SP-05, verified timestamps; TIE-BOUNDARIES-"
                    f"INCLUSIVE-V1)",
                    {"coarse": last.leg_id, "fine": fl.leg_id,
                     "status": status, "scale": scale},
                    [last.leg_id, fl.leg_id],
                    "SRS-SP05 + SRS-CLAIM-SEM", CLAIM_ENGINEERING,
                    "operational containment state; a state, not a cause")
        return facts, {"last_leg": last}

    def _completed_frame(self, scale: str,
                         as_of: Optional[pd.Timestamp] = None
                         ) -> Optional[pd.DataFrame]:
        """Rows of ``scale`` completed at or before ``as_of`` that carry
        complete OHLC — an incomplete higher-timeframe bar is dropped and
        no future row is ever read."""
        df = self.frames.get(scale)
        if df is None:
            return None
        out = df.dropna(subset=["open", "high", "low", "close"])
        if as_of is not None:
            out = out[out.index <= as_of]
        return out

    # ------------------------------------------------------------------ #
    # reference selection + falsifier layers (existing components)        #
    # ------------------------------------------------------------------ #
    def _select_reference(self, *, as_of: pd.Timestamp, dbar: int,
                          world: Dict[str, Any]) -> ExpertSelection:
        sel = expert_structural_reference_selection(
            points=world["all_points"], legs=world["all_legs"],
            decision_bar=dbar, rep=self.rep, policy=self.policy,
            role=self.TASK_ROLE, policy_id=self.POLICY_ID,
            allow_provisional=False, decision_time=as_of,
            axis=self.axis, relationships=ContextualRelationships(),
            knowledge=EXPERT_KNOWLEDGE_SRS_V1, state_id_prefix="S1A")
        return sel

    def _falsify(self, *, as_of: pd.Timestamp, dbar: int,
                 world: Dict[str, Any], claims: List[dict]):
        return task_s5_falsifier(
            claims, world["all_points"], world["all_legs"],
            decision_bar=dbar, state_id_prefix="S5A",
            decision_time=as_of, axis=self.axis)

    # ------------------------------------------------------------------ #
    # violation events (SP-03 on the task scale)                          #
    # ------------------------------------------------------------------ #
    def _violation_events(self, ref, *, dbar: int,
                          as_of: pd.Timestamp) -> List[dict]:
        """Every SP-03 close-based violation of ``ref`` knowable at or
        before this boundary.  Deterministic; stamps are validated
        against the decision boundary through the approved interface."""
        bars = self._bars_upto(dbar)
        closes = bars["close"].to_numpy()
        if ref is None or not hasattr(ref, "level"):
            return []
        j0 = max(int(ref.knowable_bar), 0)
        # falsifying side for a low reference (supports 'up' claims) = down
        fals_side = "down" if ref.side == "low" else "up"
        out: List[dict] = []
        for j in range(j0, dbar + 1):
            bound = sp03_binding(float(closes[j]), [ref], side=fals_side,
                                 tie_bound=False)
            if not bound:
                continue
            t = pd.Timestamp(bars.index[j])
            t = (t.tz_localize("UTC") if t.tzinfo is None
                 else t.tz_convert("UTC"))
            ok, why = validate_relationship_stamp(
                j, t, decision_bar=dbar, decision_time=as_of,
                axis=self.axis)
            if not ok:
                # recorded as unavailable; never used
                out.append({"bar": j, "time": str(t), "close":
                            float(closes[j]), "unavailable": why})
                continue
            out.append({"bar": j, "time": str(t), "close":
                        float(closes[j]), "side": fals_side,
                        "level": float(ref.level)})
        return out

    # ------------------------------------------------------------------ #
    # forecast layer                                                      #
    # ------------------------------------------------------------------ #
    def _ensure_forecast(self, *, as_of: pd.Timestamp, dbar: int,
                         ref_point, interpretation_id: str,
                         direction: str, violation_events: List[dict],
                         analysis_ref: str) -> ForecastVersion:
        """One forecast per falsifier reference: created ONCE (before its
        condition when possible), then only REVISED by appending a new
        immutable version when the condition's status changes."""
        key = ref_point.candidate_id
        existing_id = self._active_forecast_by_ref.get(key)
        if existing_id:
            prior = self.forecast_versions[existing_id][-1]
            if prior.status == "pending":
                post = [v for v in violation_events
                        if "unavailable" not in v
                        and pd.Timestamp(v["time"]) > prior.asof_time]
                if post:
                    return self.revise_forecast(
                        existing_id, status="condition_observed",
                        status_evidence=[{"kind": "sp03-close-violation",
                                          **v} for v in post[:5]],
                        as_of=as_of, dbar=dbar,
                        analysis_ref=analysis_ref)
            return prior          # status unchanged: NO new version

        self._forecast_seq += 1
        fid = f"FC-{self.run_id}-{self._forecast_seq:04d}"
        viol_side = "down" if ref_point.side == "low" else "up"
        cond = ForecastCondition(
            detector="sp03-close-violation",
            executable=True,
            definition=(
                f"a completed {self.task_scale} bar whose CLOSE is "
                f"strictly beyond the reference level "
                f"{ref_point.level:g} on the {viol_side} side (SP-03 "
                f"close-based binding; equality is not a crossing — "
                f"TIE-CROSS-EQUAL-UNBOUND-V1)"),
            basis="SRS-SP03 + SRS-SP04 + SRS-TS5",
            claim_class=CLAIM_PARAPHRASE)
        before = [v for v in violation_events
                  if "unavailable" not in v
                  and pd.Timestamp(v["time"]) <= as_of]
        already = bool(before)
        fv = ForecastVersion(
            forecast_id=fid, version=1,
            analysis_ref=analysis_ref,
            asof_time=as_of, asof_bar=dbar,
            task_id=self.TASK_ID, role=self.TASK_ROLE,
            condition=cond,
            if_event=(f"close-based violation of "
                      f"{ref_point.candidate_id} (level "
                      f"{ref_point.level:g}) on the {viol_side} side"),
            then_effect=(f"interpretation {interpretation_id} LOSES "
                         f"SUPPORT (SP-04: the falsifier reference is "
                         f"violated; the interpretation's status changes, "
                         f"not its wording)"),
            interpretation_id=interpretation_id,
            support_description=(
                f"no close beyond {ref_point.level:g} on the "
                f"{viol_side} side on subsequent completed bars"),
            weaken_description=(
                f"a completed bar closing {viol_side} of "
                f"{ref_point.level:g} (SP-03)"),
            next_observation=(
                f"the next completed {self.task_scale} bar's CLOSE vs "
                f"{ref_point.level:g}"),
            status=("already_observed" if already else "pending"),
            status_evidence=([{"kind": "sp03-close-violation", **v}
                              for v in before[:5]] if already else []),
            observed_before_record=already,
            revises=None,
            dependencies=[ref_point.candidate_id, interpretation_id],
            provenance=["SRS-SP03", "SRS-SP04", "SRS-TS5",
                        "SRS-CLAIM-SEM"],
            market_state_snapshot={
                "reference": ref_point.candidate_id,
                "level": float(ref_point.level),
                "direction": direction,
                "boundary": str(as_of)})
        self.forecast_versions.setdefault(fid, []).append(fv)
        self._active_forecast_by_ref[key] = fid
        return fv

    def revise_forecast(self, forecast_id: str, *,
                        status: str,
                        status_evidence: List[dict],
                        as_of: pd.Timestamp,
                        dbar: int,
                        analysis_ref: str) -> ForecastVersion:
        """Append a NEW immutable version (the prior version is never
        edited); the revision reason is recorded on the analysis record."""
        prior = self.forecast_versions[forecast_id][-1]
        if status == prior.status:
            return prior
        if status != "condition_observed":
            raise ValueError("forecast status can only move to "
                             "condition_observed here")
        nv = ForecastVersion(
            forecast_id=forecast_id, version=prior.version + 1,
            analysis_ref=analysis_ref, asof_time=as_of, asof_bar=dbar,
            task_id=prior.task_id, role=prior.role,
            condition=prior.condition, if_event=prior.if_event,
            then_effect=prior.then_effect,
            interpretation_id=prior.interpretation_id,
            support_description=prior.support_description,
            weaken_description=prior.weaken_description,
            next_observation=prior.next_observation,
            status=status, status_evidence=list(status_evidence),
            observed_before_record=prior.observed_before_record,
            revises=f"{forecast_id}@v{prior.version}",
            dependencies=list(prior.dependencies),
            provenance=list(prior.provenance),
            market_state_snapshot=dict(prior.market_state_snapshot))
        self.forecast_versions[forecast_id].append(nv)
        self._pending_revision_reason = (
            f"forecast {forecast_id} revised to {status} by post-record "
            f"evidence ({forecast_id}@v{prior.version} preserved)")
        return nv

    def _monitor_forecasts(self, *, as_of: pd.Timestamp, dbar: int,
                           world: Dict[str, Any]) -> List[ForecastVersion]:
        """Check EVERY active forecast's condition against the evidence
        available at this boundary — including forecasts whose reference
        is no longer the current one (their recorded conditions remain
        under observation).  A status change appends a new immutable
        version; the prior version keeps its original wording."""
        by_id = {p.candidate_id: p for p in world["all_points"]}
        touched: List[ForecastVersion] = []
        for cid, fid in list(self._active_forecast_by_ref.items()):
            prior = self.forecast_versions[fid][-1]
            if prior.status != "pending":
                continue
            refp = by_id.get(cid)
            if refp is None:
                continue
            viol = self._violation_events(refp, dbar=dbar, as_of=as_of)
            post = [v for v in viol
                    if "unavailable" not in v
                    and pd.Timestamp(v["time"]) > prior.asof_time]
            if post:
                touched.append(self.revise_forecast(
                    fid, status="condition_observed",
                    status_evidence=[{"kind": "sp03-close-violation",
                                      **v} for v in post[:5]],
                    as_of=as_of, dbar=dbar,
                    analysis_ref=f"{self.analysis_id}@v"
                                 f"{len(self.records) + 1}"))
        return touched

    # ------------------------------------------------------------------ #
    # interpretation layer                                                #
    # ------------------------------------------------------------------ #
    def _interpretations(self, *, as_of: pd.Timestamp, dbar: int,
                         world: Dict[str, Any], sel: ExpertSelection,
                         s5, facts: List[StructuralFact],
                         unavailable: List[dict]) -> Tuple[
                             List[Interpretation], List[ForecastVersion],
                             Dict[str, str], List[str], Dict[str, Any]]:
        interps: List[Interpretation] = []
        forecasts: List[ForecastVersion] = []
        invalidating: List[str] = []
        last = world["completed"]["last_leg"]

        if last is None:
            interps.append(Interpretation(
                interpretation_id="I-insufficient",
                version=len(self.records) + 1, label="insufficient",
                status="insufficient",
                scope=f"{self.instrument} {self.task_scale}",
                description=(
                    "no completed task-scale leg exists yet: the movement "
                    "direction is not established; no interpretation is "
                    "formed and no condition is forecast"),
                as_of_time=as_of,
                supporting_evidence=[], opposed_evidence=[],
                alternative_explanations=[], alternative_ids=[],
                falsifier_reference=None, would_be_supported_by=[
                    "the completion and causal confirmation of the first "
                    f"{self.k}-bar task-scale leg"],
                would_be_weakened_by=[],
                next_discriminating_observation=(
                    "the completion and confirmation of the first "
                    "task-scale leg"),
                invalidating_observations=[],
                dependencies=[],
                unknowns=["movement direction", "reference"],
                claim_class=CLAIM_ENGINEERING,
                provenance=["SRS-FK", "SRS-CLAIM-SEM"]))
            return interps, forecasts, {"status": "insufficient"}, \
                invalidating, {"status": "unresolved",
                               "reason": "no completed task-scale leg",
                               "survivors": [], "role": self.TASK_ROLE}

        direction = "up" if last.direction == "up" else "down"
        opp = "down" if direction == "up" else "up"

        # ---- reference resolution (T-S5 role: origin of the last
        # confirmed leg; direction claim must match the last leg) --------
        claim = {"interpretation": "I-primary", "view": self.VIEW,
                 "role": self.TASK_ROLE, "direction": direction}
        by_id = {p.candidate_id: p for p in world["all_points"]}
        ref_id = sel.candidate_id
        ref_point = by_id.get(ref_id) if ref_id else None
        if ref_point is None and s5.selected_id:
            ref_id = s5.selected_id
            ref_point = by_id.get(ref_id)
        viol: List[dict] = []
        invalidating = []
        if ref_point is not None:
            viol = self._violation_events(ref_point, dbar=dbar,
                                          as_of=as_of)
            invalidating = [
                f"completed {self.task_scale} bar CLOSE {v.get('side')} of "
                f"{v.get('level', ref_point.level):g} (SP-03 close-based "
                f"violation of {ref_id}) at {v.get('time')}"
                for v in viol if "unavailable" not in v][:5]

        # reference status: either precise OR an explicit unresolved
        # reason — never a vague wait
        if ref_id is not None:
            reference = {"status": "selected", "selected": ref_id,
                         "role": self.TASK_ROLE,
                         "selection_task": getattr(sel, "task_id", "T-S1"),
                         "selection_status": sel.outcome,
                         "selection_evidence": [e.to_record() for e in
                                                sel.evidence[:6]]}
        else:
            reason = (getattr(s5, "unresolved", None) and
                      (f"{s5.unresolved.reason_code}: "
                       f"{s5.unresolved.evidence_needed or 'reason recorded'}")
                      ) or "no reference candidate is available at this as-of"
            if sel.reason:
                reason = f"{sel.reason.get('code', '')}: " \
                         f"{sel.reason.get('evidence_needed') or sel.reason.get('detail') or reason}"
            reference = {"status": "unresolved", "reason": reason,
                         "survivors": list(getattr(s5, "survivors", []))
                         or list(sel.surviving_candidate_ids),
                         "role": self.TASK_ROLE}

        # ---- taken-state / cross-scale facts (state only) --------------
        taken_facts: List[str] = []
        for f in facts:
            if f.kind == "derived-frame-availability":
                taken_facts.append(f.fact_id)

        # ---- per-survivor readings when the reference is unresolved ----
        readings: List[str] = []
        if ref_id is None and reference["survivors"]:
            for cid in reference["survivors"][:3]:
                p = by_id.get(cid)
                if p is None:
                    continue
                readings.append(
                    f"if the reference is {cid} (level {p.level:g}, "
                    f"knowable at bar {p.knowable_bar}) the same "
                    f"{direction} claim has its falsifier there")
        ref_label = ref_id or "the reference (unresolved)"

        # ---- primary interpretation (engineering class) ---------------
        if ref_point is not None:
            support = [f.fact_id for f in facts
                       if f.kind == "derived-movement-direction"]
            if not viol:
                support.append(
                    f"no SP-03 close-based violation of {ref_label} is "
                    f"present in the available as-of history")
            support += [f.fact_id for f in facts
                        if f.kind == "derived-frame-availability"][:2]
            opposed = ([f"SP-03 close violation of {ref_label} "
                        f"({len(viol)} event(s))"] if viol else [])
            prim_status = ("invalidated" if viol else "active")
            prim_id = "I-primary"
            interps.append(Interpretation(
                interpretation_id=prim_id,
                version=len(self.records) + 1,
                label="movement-continuation",
                status=prim_status,
                scope=f"{self.instrument} {self.task_scale}",
                description=(
                    f"the completed task-scale leg moved {direction} "
                    f"({last.leg_id}); the current interpretation is that "
                    f"the {self.TASK_ROLE} = {ref_label} continues to "
                    f"define the boundary of that claim at this as-of "
                    f"(research configuration)"),
                as_of_time=as_of,
                supporting_evidence=support, opposed_evidence=opposed,
                alternative_explanations=[
                    f"the {direction} leg is exhausted and a {opp} "
                    f"structure develops (monitored as I-alt)"],
                alternative_ids=["I-alt"],
                falsifier_reference=ref_id,
                would_be_supported_by=[
                    f"continuation without a close-based violation of "
                    f"{ref_label} (SP-03)"],
                would_be_weakened_by=[
                    f"a completed bar closing beyond {ref_label} on the "
                    f"falsifying side (SP-03 close-based binding; "
                    f"SRS-SP03)"],
                next_discriminating_observation=(
                    f"the next completed {self.task_scale} bar's CLOSE "
                    f"relative to {ref_label}"),
                invalidating_observations=invalidating or [
                    f"a completed {self.task_scale} bar closing on the "
                    f"falsifying side of {ref_label}"],
                dependencies=[last.leg_id, last.start_id, last.end_id]
                + ([ref_id] if ref_id else []),
                unknowns=["no expiry is defined (no approved policy "
                          "defines one)", "no probabilities are claimed"],
                claim_class=CLAIM_ENGINEERING,
                provenance=["SRS-TS5", "SRS-SP03", "SRS-SP04",
                            "SRS-FK", "SRS-CLAIM-SEM"],
                data={"direction": direction,
                      "reference_candidate": ref_id,
                      "reference_status": reference["status"],
                      "last_leg": last.leg_id}))
        else:
            prim_id = "I-scenario"
            interps.append(Interpretation(
                interpretation_id=prim_id,
                version=len(self.records) + 1,
                label="movement-scenario",
                status="alternative-monitoring",
                scope=f"{self.instrument} {self.task_scale}",
                description=(
                    f"the completed task-scale leg moved {direction} "
                    f"({last.leg_id}); the falsifier reference is NOT "
                    f"precisely resolved at this as-of — the scenario is "
                    f"monitored over the recorded reference set"),
                as_of_time=as_of,
                supporting_evidence=[f.fact_id for f in facts
                                    if f.kind ==
                                    "derived-movement-direction"],
                opposed_evidence=[],
                alternative_explanations=[
                    f"the {opp} side takes over (monitored as I-alt)"],
                alternative_ids=["I-alt"],
                falsifier_reference=None,
                would_be_supported_by=[
                    f"resolution of the reference and no close-based "
                    f"violation of it (SP-03)"],
                would_be_weakened_by=[
                    f"a completed bar closing on the falsifying side of "
                    f"every candidate in the reference set"],
                next_discriminating_observation=(
                    f"reference resolution ({reference['reason']}) or "
                    f"the next completed {self.task_scale} bar's CLOSE"),
                invalidating_observations=[],
                dependencies=[last.leg_id],
                unknowns=["precise falsifier reference"],
                claim_class=CLAIM_ENGINEERING,
                provenance=["SRS-TS5", "SRS-SP03", "SRS-CLAIM-SEM"],
                data={"direction": direction,
                      "reference_status": "unresolved",
                      "readings": readings,
                      "last_leg": last.leg_id}))

        # ---- alternative (materially different) -----------------------
        interps.append(Interpretation(
            interpretation_id="I-alt",
            version=len(self.records) + 1,
            label="movement-reversal",
            status="alternative-monitoring",
            scope=f"{self.instrument} {self.task_scale}",
            description=(
                f"materially different alternative: the {direction} "
                f"structure is exhausted and price develops an active "
                f"{opp} structure from the current boundary"),
            as_of_time=as_of,
            supporting_evidence=[],
            opposed_evidence=[f.fact_id for f in facts
                              if f.kind == "derived-movement-direction"],
            alternative_explanations=[
                f"continuation of the {direction} structure "
                f"(I-primary)"],
            alternative_ids=["I-primary"],
            falsifier_reference=None,
            would_be_supported_by=[
                f"a new confirmed {opp} leg (F-K k={self.k} completion)",
                f"a completed bar closing beyond {ref_label} on the "
                f"falsifying side (SP-03)"],
            would_be_weakened_by=[
                f"continuation of the {direction} structure without a "
                f"close-based violation"],
            next_discriminating_observation=(
                f"the next completed {self.task_scale} leg's direction"),
            invalidating_observations=[
                f"a new confirmed {direction} leg beyond the previous "
                f"extreme"],
            dependencies=[last.leg_id],
            unknowns=["no probability is attached (not calibrated)"],
            claim_class=CLAIM_HYPOTHESIS,
            provenance=["SRS-CLAIM-SEM"],
            data={"direction": opp}))

        # ---- conditional forecasts (recorded BEFORE the condition) ----
        fc_meta: Dict[str, str] = {}
        fc_targets: List = []
        if ref_point is not None:
            fc_targets.append((ref_point, "I-primary"))
        elif reference["survivors"]:
            for cid in reference["survivors"][:3]:
                p = by_id.get(cid)
                if p is not None:
                    fc_targets.append((p, "I-scenario"))
        for tp, iid in fc_targets:
            fc = self._ensure_forecast(
                as_of=as_of, dbar=dbar, ref_point=tp,
                interpretation_id=iid, direction=direction,
                violation_events=self._violation_events(
                    tp, dbar=dbar, as_of=as_of),
                analysis_ref=f"{self.analysis_id}@v"
                             f"{len(self.records) + 1}")
            forecasts.append(fc)
        if forecasts:
            primary_fc = forecasts[0]
            fc_meta = {"status": primary_fc.status,
                       "revised": (primary_fc.forecast_id
                                   if primary_fc.revises else ""),
                       "revises": primary_fc.revises or ""}
        else:
            fc_meta = {"status": "scenario"}
        return interps, forecasts, fc_meta, invalidating, reference

    # ------------------------------------------------------------------ #
    # one analysis boundary                                               #
    # ------------------------------------------------------------------ #
    def analyze(self, as_of: pd.Timestamp) -> AnalysisRecord:
        """Produce ONE analysis record as of ``as_of``.

        Every new analysis record includes a new as-of key; append-after-T
        invariance is structural (records are append-only and only the
        newest record changes when evidence beyond T arrives).
        """
        dbar, as_of = self._decision_at(as_of)

        # observed state: bar/scale status as of the boundary
        bars = self._bars_upto(dbar)
        if bars.empty:
            raise ValueError("empty task-scale frame at as-of")

        # structural world (FK + legs) — deterministic, from available
        # bars only (occurrence/knowability stamped by the sealed axis)
        task_bars = bars
        points = fk_turning_points(
            task_bars, self.k, self.rep,
            id_prefix="PT", allow_short_left=False,
            tie_policy=TIE_FT_EQ_FIRST, axis=self.axis)
        leg_ambiguities: List[dict] = []
        legs = build_legs(points, self.rep, completed_only=False,
                          ambiguities=leg_ambiguities)
        world = {"all_points": points, "all_legs": legs, "rep": self.rep,
                 "policy": self.policy}

        facts, completed = self._structural_layer(
            as_of=as_of, dbar=dbar, world=world)
        world["completed"] = completed

        # reference selection (kernel T-S1 + existing documented
        # preferences) and falsifier mapping (T-S5 / SP-04)
        sel = self._select_reference(as_of=as_of, dbar=dbar, world=world)
        direction = ("up" if completed["last_leg"] is not None and
                     completed["last_leg"].direction == "up" else "down")
        s5 = self._falsify(
            as_of=as_of, dbar=dbar, world=world,
            claims=[{"interpretation": "I-primary", "view": self.VIEW,
                     "role": self.TASK_ROLE, "direction": direction}])

        # unavailable / rejected evidence (explicit reasons; never used)
        unavailable: List[dict] = []
        rejected: List[dict] = []
        for scale in (self.fine_scale, self.finest_scale):
            df = self.frames.get(scale)
            if df is None or df.empty:
                unavailable.append({
                    "item": f"frame:{scale}",
                    "reason": f"no {scale} frame available",
                    "kind": "missing-frame"})
                continue
            # incomplete bars INSIDE the visible window are recorded and
            # dropped; rows after the boundary are simply not visible
            # (the record must not depend on how many future rows exist)
            visible = df[df.index <= as_of]
            incomplete = visible[visible[["open", "high", "low", "close"]]
                                 .isna().any(axis=1)]
            for t in list(incomplete.index[-3:]):
                rejected.append({
                    "item": f"{scale} bar at {t}",
                    "reason": "incomplete higher-timeframe bar: never "
                              "used (availability = completion)",
                    "kind": "incomplete-bar"})
            # the future class is always unavailable at any as-of —
            # recorded unconditionally so the record cannot depend on
            # how many future rows happen to exist in the frame
            unavailable.append({
                "item": f"frame:{scale} rows after {as_of}",
                "reason": ("future: rows completing after the as-of "
                           "boundary are unavailable by construction "
                           "(availability = completion time)"),
                "kind": "future-evidence"})

        # interpretation + forecast layers
        interps, forecasts, fc_meta, invalidating, reference = \
            self._interpretations(
                as_of=as_of, dbar=dbar, world=world, sel=sel, s5=s5,
                facts=facts, unavailable=unavailable)

        # monitor EVERY active forecast (incl. those whose reference is
        # no longer the current one)
        touched = self._monitor_forecasts(as_of=as_of, dbar=dbar,
                                          world=world)
        if touched and not fc_meta.get("revised"):
            fc_meta["revised"] = touched[0].forecast_id
        active_fvs = [self.forecast_versions[fid][-1]
                      for cid, fid in
                      sorted(self._active_forecast_by_ref.items())
                      if cid in {p.candidate_id
                                 for p in world["all_points"]}]
        forecasts = active_fvs[:8] or forecasts

        # lifecycle state (analytical, never a trading signal)
        if self.records:
            prior_state = self.records[-1].lifecycle_state
        elif self._restored_records:
            prior_state = self._restored_records[-1].get(
                "lifecycle_state")
        else:
            prior_state = None
        fc_status = fc_meta.get("status")
        if fc_status == "insufficient":
            state = STATE_INSUFFICIENT
        elif fc_meta.get("revised"):
            state = STATE_INVALIDATED   # a recorded forecast's condition
            # was observed after its record: the dependent view is
            # invalidated by later available evidence
        elif fc_status == "already_observed":
            state = STATE_ALREADY_OBSERVED
        elif fc_status == "condition_observed":
            state = STATE_ALREADY_OBSERVED
        elif fc_status == "pending":
            state = STATE_PENDING
        elif fc_status == "scenario":
            state = STATE_MONITORING
        else:
            state = STATE_INTERPRETATIONS

        # observation mode (live-observed vs reconstructed)
        if self.records or self.resumed_from:
            mode = MODE_LIVE
            note = ("engine observed the evidence since its previous "
                    "boundary in sequence")
        else:
            mode = MODE_RECONSTRUCTED
            note = ("analysis assembled from historical data available "
                    "through this boundary; no live event stream was "
                    "observed by this engine before it")

        limitations = [
            "selection_quality = NOT_ESTABLISHED (no independent quality "
            "target has been evaluated)",
            "P-ORIGIN-RESEARCH is research configuration, not an "
            "owner-approved analytical policy",
            "no source-defined operational confirmation event applies to "
            "this path's claims (trade-through validation is S-class for "
            "ORDER-BLOCK candidates, out of scope here) — no CONFIRMED "
            "state is ever claimed",
            "no probabilities (not calibrated on a versioned "
            "out-of-sample set); no forecast expiry (no approved policy "
            "defines one)",
            "position status is absent: " + self.POSITION_NOTE,
        ]
        if mode == MODE_RECONSTRUCTED:
            limitations.append(
                "RECONSTRUCTED start: forecasts and analyses before "
                f"{as_of} were not recorded by this engine; earlier "
                "swing/leg live observation times cannot be reconstructed "
                "from this process (facts are computed from available "
                "bars only)")

        # ledger integration: record the actual task results with
        # COMPLETE payloads (real recomputation preserved)
        ledger_uids: List[str] = []
        payload = sel.ledger_payload(
            run_id=self.run_id, points=world["all_points"],
            legs=world["all_legs"], rep=self.rep, policy=self.policy,
            role=self.TASK_ROLE, policy_id=self.POLICY_ID,
            axis=self.axis, relationships=ContextualRelationships(),
            decision_time=as_of, state_id_prefix="S1A")
        uid = self.ledger.record(sel.final_result, payload)
        ledger_uids.append(uid)
        s5_payload = {
            "kind": "task_s5_falsifier",
            "run_id": self.run_id,
            "claims": [{"interpretation": "I-primary",
                        "view": self.VIEW, "role": self.TASK_ROLE,
                        "direction": direction}],
            "points": list(world["all_points"]),
            "legs": list(world["all_legs"]),
            "decision_bar": dbar, "decision_time": str(as_of),
            "dependencies": [uid],
        }
        uid2 = self.ledger.record(s5, s5_payload)
        ledger_uids.append(uid2)

        # next discriminating observation + invalidating observations
        next_obs = ("the next completed task-scale bar's CLOSE relative "
                    "to " + (reference.get("selected") or
                             "the unresolved reference set"))
        for i in interps:
            if i.status in ("active", "alternative-monitoring"):
                next_obs = i.next_discriminating_observation
                break

        analysis_version = len(self.records) + self._version_offset + 1
        revises = f"{self.analysis_id}@v{analysis_version - 1}" \
            if (self.records or self._restored_records) else None
        revision_reason = self._pending_revision_reason
        self._pending_revision_reason = None

        rec = AnalysisRecord(
            analysis_id=self.analysis_id, analysis_version=analysis_version,
            as_of_time=as_of, as_of_bar=dbar,
            observation_mode=mode, observation_note=note,
            task_id=self.TASK_ID, task_name=self.TASK_NAME,
            task_scale=self.task_scale,
            role=self.TASK_ROLE, role_semantics=self.ROLE_SEMANTICS,
            policy_id=self.POLICY_ID, policy_kind=KIND_RESEARCH,
            observed_state=(f"last completed {self.task_scale} bar: "
                            f"{bars.index[-1]} close={bars['close'].iloc[-1]:g}"),
            lifecycle_state=state, prior_state=prior_state,
            revision_reason=revision_reason,
            structural_facts=facts, interpretations=interps,
            supporting_evidence=[e.to_record() for e in sel.evidence[:8]],
            conflicting_evidence=[dict(c) for c in sel.conflicts[:8]],
            reference_status={**reference, "interpretations":
                              [i.interpretation_id for i in interps]},
            forecasts=forecasts,
            next_discriminating_observation=next_obs,
            invalidating_observations=invalidating,
            position_status=_POSITION_ABSENT,
            position_note=self.POSITION_NOTE,
            sources=[s.source_id for s in SOURCE_REGISTER],
            source_claim_classes={s.source_id: s.claim_class
                                  for s in SOURCE_REGISTER},
            dependencies=sorted({d for i in interps
                                 for d in i.dependencies}),
            rejected_evidence=rejected,
            selection_quality="NOT_ESTABLISHED",
            limitations=limitations,
            unresolved=[u for u in (
                ([f"{s5.unresolved.reason_code}: "
                  f"{s5.unresolved.evidence_needed}"]
                 if getattr(s5, "unresolved", None) else [])
                + [f"unavailable evidence: {u['item']} — {u['reason']}"
                   for u in unavailable])],
            prior=revises, revises=revises,
            ledger_uids=ledger_uids,
            csm_payload={
                "task_id": self.TASK_ID,
                "decision_bar": dbar,
                "points": [candidate_id_of(p) for p in
                           world["all_points"]],
                "legs": [l.leg_id for l in world["all_legs"]],
                "policy_snapshots": dict(sel.policy_snapshots),
                "interpretation_ids": [i.interpretation_id
                                       for i in interps],
                "status": sel.outcome,
                "evidence": [e.to_record() for e in sel.evidence[:8]]},
            run_id=self.run_id)
        self.records.append(rec)
        return rec

    # ------------------------------------------------------------------ #
    # snapshot: midstream start / resume                                  #
    # ------------------------------------------------------------------ #
    def snapshot_state(self) -> dict:
        return {
            "kind": "analysis-engine-v1",
            "analysis_id": self.analysis_id,
            "run_id": self.run_id,
            "as_of_time": str(self.records[-1].as_of_time) if
            self.records else None,
            "as_of_bar": self.records[-1].as_of_bar if self.records
            else None,
            "records": [r.to_record() for r in self.records],
            "forecast_versions": {fid: [v.to_record() for v in vs]
                                  for fid, vs in
                                  self.forecast_versions.items()},
            "active_forecast_by_ref": dict(self._active_forecast_by_ref),
            "forecast_seq": self._forecast_seq,
            "policy_values": {
                self.POLICY_ID:
                    self.policy.snapshot_of(self.POLICY_ID)},
            "task_scale": self.task_scale, "k": self.k,
            "instrument": self.instrument,
            "selection_quality": "NOT_ESTABLISHED",
        }

    def _load_snapshot(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as fh:
            snap = json.load(fh)
        if snap.get("kind") != "analysis-engine-v1":
            raise ValueError("not an analysis-engine snapshot")
        self.resumed_from = str(snap.get("as_of_time"))
        self.restored = True
        self._forecast_seq = int(snap.get("forecast_seq", 0))
        self._active_forecast_by_ref = dict(
            snap.get("active_forecast_by_ref", {}))
        for fid, versions in snap.get("forecast_versions", {}).items():
            self.forecast_versions[fid] = [
                _fv_from_record(v) for v in versions]
        self._restored_records = list(snap.get("records", []))
        self._version_offset = len(self._restored_records)

    @property
    def snapshot_boundary(self) -> Optional[str]:
        return self.resumed_from


def candidate_id_of(p) -> str:
    return p.candidate_id


def _fv_from_record(d: dict) -> ForecastVersion:
    cond = ForecastCondition(**d["condition"])
    d2 = dict(d)
    d2["condition"] = cond
    d2["asof_time"] = pd.Timestamp(d2["asof_time"])
    return ForecastVersion(**d2)
