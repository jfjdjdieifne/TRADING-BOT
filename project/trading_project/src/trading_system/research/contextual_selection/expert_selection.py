"""Expert-grounded contextual selection V1.1 — STRUCTURAL_REFERENCE (T-S1).

CONTROLLED IMPLEMENTATION (no parallel architecture).  Judgment layer over
the existing CSM kernel (``contextual_selection.csm``): it consumes — never
reimplements — the candidates, lifecycle/status history, eligibility gates
(``task_s1_structural_reference`` -> SP-01/SP-13/SP-14/X-SCALE/X-SUPER/
same-bar discipline), the shared information-time axis over the CLOSED
6.2A-0 contract (``research.information_time`` — sealed, untouched), policy
registry (SP-18) and the revision/dependency mechanisms
(``SelectionResult``/``UnresolvedState``/``InterpretationLedger``).

V1.1 = remediation of the expert-selection V1 audit (findings 1-6):

  F1  EVERY relationship fact (test events, ref_kind, round_cluster) must
      carry a knowability stamp and is validated against the decision
      boundary through the approved axis interfaces; missing, future,
      off-grid or unmappable evidence is UNAVAILABLE and never influences a
      selection (dropped evidence is logged, not hidden).
  F2  a valid declared task AND role are required; a missing policy never
      bypasses task/role eligibility; comparisons run only over gate-eligible
      candidates; missing evidence / incomparable candidates yield
      UNRESOLVED with explicit reasons; candidates are never silently
      omitted (kernel-silent drops are surfaced as X-STATE/X-SUPER).
  F3  nonempty test_history is NOT binding evidence.  Wick/range touches and
      close-throughs are distinct observations kept apart; neither implies
      rejection, validation or successful reaction (file 15 §15.4: taken
      status "establishes state, not cause").  "tested > untested" and
      "cluster > non-cluster" are NONBINDING research hypotheses (task
      classification F) — the pinned knowledge repository substantiates
      neither as a selection comparison.  The only source-substantiated
      conditional comparison is KP-03 (REF-OLD-LOW-HTF family; file 05
      §5.4a P-R + file 15 §15.3 H).
  F4  equal knowable-time ties are UNRESOLVED in the kernel (task_s1) and
      independently guarded here; no selection is ever order-resolved.
  F5  real ``InterpretationLedger`` recomputation: complete serialized
      inputs in the payload + a registered recompute handler; empty or
      incomplete payloads fail closed (stale), never a silent success.
  F6  the replay manifest records dataset/input/source/dataset versions.

Output contract (task §5): SELECTED(candidate_id, evidence) or
UNRESOLVED(reason, surviving_candidate_ids).  No largest/nearest/newest/
prominence default exists.  No market thresholds, no confidence percentages,
no learned scores, no trading recommendation, no future-outcome logic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import pandas as pd

from trading_system.research.contextual_selection.csm import (  # noqa: F401
    CLASS_F,
    CLASS_O,
    CLASS_S,
    CLASS_U,
    KIND_PROCEDURE,
    REASON_AI,
    REASON_EP,
    REASON_IC,
    REASON_MP,
    STATUS_SUPERSEDED,
    Exclusion,
    LegCandidate,
    PointCandidate,
    PolicyRegistry,
    Representation,
    SelectionResult,
    SharedInformationAxis,
    UnresolvedState,
    X_STATE,
    X_SUPER,
    candidate_record,
    leg_recency_key,
    register_recompute_handler,
    same_bar_evidence_class,
    task_s1_structural_reference,
)

# Task classification (task §4) — dual label beside file 15's F/O/S/L/U.
KCLASS_A = "A"  # deterministic fact
KCLASS_B = "B"  # hard eligibility constraint
KCLASS_C = "C"  # declared analytical policy
KCLASS_D = "D"  # task-conditioning information
KCLASS_E = "E"  # source-grounded conditional preference
KCLASS_F = "F"  # unresolved expert hypothesis (NEVER binding)

SRS_TASK_ID = "T-S1"
SRS_TASK_NAME = "STRUCTURAL_REFERENCE_SELECTION"

#: Valid declared roles for this task (file 16 §16.3).  Anything else is an
#: invalid task instance: UNRESOLVED with an explicit reason (finding F2).
VALID_ROLES: Tuple[str, ...] = ("origin-of-last-confirmed-leg",
                                "last-confirmed-extreme")

#: Role sentinel that routes the kernel to its explicit MP fallthrough (the
#: gated survivor set) WITHOUT pretending a role was declared.
EXPERT_ROLE_UNDECLARED = "__role-undeclared__"

#: Documented precedence: a declared Pi_T role policy resolves the task
#: (knowledge_foundation/15 §15.7.3).  Contradicting source-grounded
#: preferences are preserved as recorded tensions (SP-12 main alternative),
#: never silently applied.
PI_T_PRECEDENCE_DOC = "knowledge_foundation/15 §15.7.3 (Pi_T resolution)"

#: Canonical relationship event kinds (finding F3).  They are kept DISTINCT:
#: a wick/range touch and a close-through are different observations and
#: neither is a validation/rejection/reaction claim.
EVENT_WICK_TOUCH = "wick-range-touch"
EVENT_CLOSE_THROUGH = "close-through"
EVENT_KINDS: Tuple[str, ...] = (EVENT_WICK_TOUCH, EVENT_CLOSE_THROUGH)


# ---------------------------------------------------------------------------
# Knowledge records (finding F3 reclassification applied)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ExpertPreference:
    """One documented knowledge record (task §4 fields).

    ``observable_evidence`` lists the evidence keys that MUST be observable
    (validated against the decision boundary) before the record's comparison
    may be licensed.  Absent/invalid evidence makes the record inapplicable.
    F-class records (``kclass == "F"``) are REFUSAL documentation and never
    bind (enforced in code and by ``__post_init__``).
    """

    pref_id: str
    task_id: str
    kclass: str                 # task §4: A..F
    klass: str                  # file 15 §15.3: F/O/S/L/U
    source: str
    source_family: str
    statement: str
    context: str
    observable_evidence: Tuple[str, ...]
    licenses: str               # comparison id this record may license
    exceptions: str
    conflict_status: str
    provenance_refs: Tuple[str, ...]
    binding: bool = False       # only A/B-class records may bind

    def __post_init__(self) -> None:
        if self.kclass not in (KCLASS_A, KCLASS_B, KCLASS_C, KCLASS_D,
                               KCLASS_E, KCLASS_F):
            raise ValueError(f"bad kclass {self.kclass!r}")
        if self.klass not in (CLASS_F, CLASS_O, CLASS_S, CLASS_U):
            raise ValueError(f"bad klass {self.klass!r}")
        if self.kclass == KCLASS_F and self.binding:
            raise ValueError("F-class (unresolved hypothesis) can never bind")
        if self.binding and self.kclass not in (KCLASS_A, KCLASS_B):
            raise ValueError("only A/B-class records may bind")
        if self.kclass == KCLASS_F and self.licenses != "none":
            raise ValueError("F-class records can never license a comparison")


def _kp(**kw) -> ExpertPreference:
    return ExpertPreference(task_id=SRS_TASK_ID, **kw)


EXPERT_KNOWLEDGE_SRS_V1: Tuple[ExpertPreference, ...] = (
    _kp(
        pref_id="KP-01",
        kclass=KCLASS_D, klass=CLASS_O,
        source=("knowledge_foundation/16 §16.3 (T-S1 task card, SWS-02); "
                "Wyckoff, The Richard D. Wyckoff Method of Trading and "
                "Investing in Stocks (1931 course), five-step approach; "
                "Livermore, How to Trade in Stocks (1940), 'The Pivotal "
                "Point'"),
        source_family="knowledge_foundation+Wyckoff+Livermore",
        statement=("the declared analytical role (task card) determines which "
                   "reference is relevant; the role rule is an operational "
                   "definition (SWS-02), not a market claim"),
        context="every T-S1 selection (task conditioning)",
        observable_evidence=("declared_role", "policy_ref"),
        licenses="none",
        exceptions=("without a valid declared role the task instance is "
                    "invalid and the output is UNRESOLVED (finding F2)"),
        conflict_status="uncontested (O-class operational definition)",
        provenance_refs=("knowledge_foundation/16:SWS-02",
                         "knowledge_foundation/19:W1", "O:P-ORIGIN"),
    ),
    _kp(
        pref_id="KP-02",
        kclass=KCLASS_F, klass=CLASS_S,
        source=("Grimes, The Art & Science of Technical Analysis (Wiley, "
                "2012) — random-lines falsification; Livermore, How to Trade "
                "in Stocks (1940) — pivotal points validated by subsequent "
                "action; Osler, FRBNY Staff Report 150 (2002) / JIMF 24(2) "
                "2005 — stop orders cluster at documented levels"),
        source_family="Grimes+Livermore+Osler",
        statement=(
            "NONBINDING research hypothesis (finding F3): levels with prior "
            "wick-range touches or close-throughs may behave differently "
            "from untouched ones.  Per knowledge_foundation/15 §15.4 taken "
            "status 'establishes state, not cause' and touch count cannot "
            "establish relevance alone — no rejection, validation or "
            "successful reaction is inferred from any event type"),
        context="documented refusal record (never a selection comparison)",
        observable_evidence=("test_events",),
        licenses="none",
        exceptions=("wick-range touches and close-throughs are kept as "
                    "DISTINCT observations and are never merged into a "
                    "'tested' verdict; the exact comparison 'tested > "
                    "untested' is NOT substantiated by the pinned knowledge "
                    "repository (jfjdjdieifne/test @ 6c8bf6fd) and is "
                    "therefore classified F (nonbinding)"),
        conflict_status=("knowledge_foundation/15 §15.4 contradicts any "
                         "binding use; hypothesis only"),
        provenance_refs=("knowledge_foundation/15 §15.4",
                         "SRC-GRIMES-2012", "SRC-LIVERMORE-1940",
                         "SRC-OSLER-SR150"),
    ),
    _kp(
        pref_id="KP-03",
        kclass=KCLASS_E, klass=CLASS_S,
        source=("ICT / Michael J. Huddleston, ICT Mentorship Core Content "
                "Month 04 lessons (SRC-ICT-OB / SRC-ICT-FVG, P1 partial "
                "transcripts): a support reference is an 'old low on a "
                "higher timeframe' or a reclaimed 'old high' "
                "(REF-OLD-LOW-HTF / REF-OLD-HIGH-RECLAIMED)"),
        source_family="ICT",
        statement=("for a declared support/structural-reference role, "
                   "candidates whose upstream-declared reference kind is "
                   "'old-low-htf' or 'old-high-reclaimed' are the "
                   "source-indicated references over locally drawn ones "
                   "(the exact S-class distinction of file 15 §15.3 H)"),
        context="declared support/structural reference role (any valid "
                "T-S1 role)",
        observable_evidence=("ref_kind",),
        licenses="old-low-htf>other",
        exceptions=("the source does not define how the old reference is "
                    "confirmed or when it expires (file 05 §5.4a P-R open) — "
                    "the preference is provisional; auto-caption wording is "
                    "P1 grade; a dispute needing the source's exact wording "
                    "surfaces AI instead of guessing; the declaration must "
                    "carry a knowability stamp or it is unavailable"),
        conflict_status="uncontested in the pinned repository (CF-01 "
                        "concerns the order-block definition, not this)",
        provenance_refs=("knowledge_foundation/05 §5.4a:P-R",
                         "knowledge_foundation/15 §15.3",
                         "knowledge_foundation/08:CASE observables",
                         "SRC-ICT-OB", "SRC-ICT-FVG"),
    ),
    _kp(
        pref_id="KP-04",
        kclass=KCLASS_B, klass=CLASS_F,
        source=("knowledge_foundation/15 §15.7 AI definition + audit D4; "
                "Lo, Mamaysky & Wang, J. Finance 55(4) 2000 — pattern "
                "definitions must control look-ahead"),
        source_family="knowledge_foundation+Lo-Mamaysky-Wang",
        statement=("a selected reference whose intrabar high/low order is "
                   "materially unresolved cannot yield a fully justified "
                   "result; it surfaces AI (hard constraint, kernel-"
                   "enforced)"),
        context="any selection whose survivor set intersects same-bar "
                "ambiguity records",
        observable_evidence=("same_bar_order", "same_bar_evidence"),
        licenses="none",
        exceptions="endpoint-proven order is factual, never downgraded",
        conflict_status="uncontested",
        provenance_refs=("knowledge_foundation/15 §15.7", "SRC-LMW-2000"),
        binding=True,
    ),
    _kp(
        pref_id="KP-05",
        kclass=KCLASS_F, klass=CLASS_U,
        source=("Wyckoff (1931) effort-vs-result readings require volume; "
                "ICT/community narratives that gaps or blocks define the "
                "operative reference"),
        source_family="Wyckoff+ICT/community",
        statement=("UNRESOLVED expert hypotheses: volume-based "
                   "effort/result validation of references; narrative claims "
                   "that FVG/OB geometry decides which structural reference "
                   "matters"),
        context="documented refusal record",
        observable_evidence=("volume",),
        licenses="none",
        exceptions=("volume-dependent readings are unidentifiable on "
                    "OHLC-alone datasets (MO); narrative forms have no "
                    "independent validation in the pinned repository"),
        conflict_status="F-class: never binding (task §4)",
        provenance_refs=("knowledge_foundation/10 (open register)",
                         "knowledge_foundation/05 §5.4a"),
    ),
    _kp(
        pref_id="KP-06",
        kclass=KCLASS_F, klass=CLASS_S,
        source=("Osler, FRBNY Staff Report 150 (2002) / JIMF 24(2) 2005 — "
                "stop-loss orders cluster near round numbers (FX dealer-"
                "order evidence)"),
        source_family="Osler",
        statement=(
            "NONBINDING research hypothesis (finding F3): upstream-declared "
            "round-number/stop-cluster markers may mark relevant levels.  "
            "The exact comparison 'cluster > non-cluster' is NOT "
            "substantiated by the pinned knowledge repository — "
            "knowledge_foundation/04 records the stop-cluster reading as a "
            "COMMUNITY interpretation (S1), and file 15 §15.3's S-class "
            "list does not include it"),
        context="documented refusal record (never a selection comparison)",
        observable_evidence=("round_cluster",),
        licenses="none",
        exceptions=("the marker must be declared upstream with a knowability "
                    "stamp — this layer never detects round numbers (no "
                    "invented market thresholds); instrument transfer is "
                    "unproven"),
        conflict_status="hypothesis only (F-class)",
        provenance_refs=("knowledge_foundation/04 §4.7",
                         "knowledge_foundation/15 §15.3",
                         "SRC-OSLER-SR150"),
    ),
    _kp(
        pref_id="KP-07",
        kclass=KCLASS_D, klass=CLASS_O,
        source=("Elder, Trading for a Living (1993) / triple screen "
                "(Futures, 1985); Wyckoff (1931); "
                "knowledge_foundation/16 T-S6 + SP-02/SP-16"),
        source_family="Elder+Wyckoff+knowledge_foundation",
        statement=("the answering scale/view is fixed by the task card "
                   "before T-S1 runs; candidates of other views are "
                   "excluded by X-SCALE (existing kernel gate), never mixed"),
        context="every T-S1 selection (task conditioning)",
        observable_evidence=("declared_view",),
        licenses="none",
        exceptions="cross-view raw comparisons are structurally rejected",
        conflict_status="uncontested",
        provenance_refs=("knowledge_foundation/16 §16.3 T-S6",
                         "SRC-ELDER-1993"),
    ),
)

KNOWLEDGE_BY_ID: Dict[str, ExpertPreference] = {
    p.pref_id: p for p in EXPERT_KNOWLEDGE_SRS_V1
}


# ---------------------------------------------------------------------------
# Relationship evidence with decision-boundary validation (finding F1)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EvidenceItem:
    """One observable fact (file 15 §15.3: the class is part of the record)."""

    name: str
    klass: str
    value: object
    source_ref: str
    detail: str = ""

    def __post_init__(self) -> None:
        if self.klass not in (CLASS_F, CLASS_O, CLASS_S, CLASS_U):
            raise ValueError(f"bad evidence class {self.klass!r}")

    def to_record(self) -> dict:
        return {"name": self.name, "class": self.klass, "value": self.value,
                "source_ref": self.source_ref, "detail": self.detail}


def _stamp_of(value: object) -> Tuple[Optional[int], Optional[pd.Timestamp]]:
    """Knowability stamp of a declaration value (``{"value", "known_bar",
    "known_time"}``) or a relationship event dict (``{"bar"/"time"}``)."""
    if isinstance(value, dict):
        bar = value.get("known_bar", value.get("bar"))
        t = value.get("known_time", value.get("time"))
        return bar, (None if t is None else pd.Timestamp(t))
    return None, None          # plain value: NO knowability stamp (unmappable)


def validate_relationship_stamp(
        known_bar: Optional[int], known_time: Optional[pd.Timestamp],
        *, decision_bar: int,
        decision_time: Optional[pd.Timestamp],
        axis: Optional[SharedInformationAxis]) -> Tuple[bool, str]:
    """Finding F1: validate one relationship fact against the decision.

    Uses ONLY the approved interfaces over the sealed 6.2A-0 contract
    (``SharedInformationAxis.is_on_grid`` / ``available``).  Missing,
    future, off-grid or unmappable evidence is UNAVAILABLE
    ``(False, reason)`` and must never influence selection.
    """
    if known_bar is None and known_time is None:
        return False, "unmappable: no knowability stamp"
    if known_time is not None:
        if axis is None:
            return False, ("time-bearing relationship evidence requires the "
                           "validated shared information-time axis")
        if not axis.is_on_grid(known_time):
            return False, "off-grid information time"
        if decision_time is None:
            return False, ("time-bearing relationship evidence requires the "
                           "decision boundary time")
        if not axis.available(known_time, decision_time):
            return False, "not available at the decision boundary"
    if known_bar is not None:
        if not isinstance(known_bar, int) or isinstance(known_bar, bool):
            return False, "unmappable: bar stamp is not an integer"
        if known_bar > decision_bar:
            return False, "future: knowable bar after the decision bar"
    return True, ""


@dataclass
class ContextualRelationships:
    """Existing contextual relationship evidence supplied to the layer.

    Contract (finding F1): every fact carries a knowability stamp.

    * ``test_history[cid]``: list of event dicts, each with ``bar`` and/or
      ``time`` and ``kind`` in ``EVENT_KINDS`` (wick-range touch vs
      close-through — kept distinct; state only, never a validation or
      reaction claim).
    * ``ref_kind[cid]`` / ``round_cluster[cid]``: declaration dicts
      ``{"value": ..., "known_bar": ..., "known_time": ...}``.  A PLAIN
      value has no stamp and is UNMAPPABLE — unavailable, never used.

    ``validated()`` returns a decision-boundary-valid copy plus the dropped
    records (unavailable evidence is logged, not hidden).
    """

    test_history: Dict[str, List[dict]] = field(default_factory=dict)
    ref_kind: Dict[str, object] = field(default_factory=dict)
    round_cluster: Dict[str, object] = field(default_factory=dict)

    def validated(self, *, decision_bar: int,
                  decision_time: Optional[pd.Timestamp] = None,
                  axis: Optional[SharedInformationAxis] = None
                  ) -> Tuple["ContextualRelationships", List[dict]]:
        out = ContextualRelationships()
        dropped: List[dict] = []

        def _drop(cid: str, field_name: str, value: object,
                  reason: str) -> None:
            dropped.append({"candidate_id": cid, "field": field_name,
                            "value": repr(value)[:160], "reason": reason})

        for cid, events in self.test_history.items():
            keep: List[dict] = []
            for ev in events or ():
                if not isinstance(ev, dict):
                    _drop(cid, "test_history", ev, "unmappable: not a record")
                    continue
                kind = ev.get("kind")
                if kind not in EVENT_KINDS:
                    _drop(cid, "test_history", ev,
                          f"unmappable: event kind {kind!r} not in "
                          f"{EVENT_KINDS} (wick touch and close-through are "
                          f"distinct; unknown kinds are never merged)")
                    continue
                bar, t = _stamp_of(ev)
                ok, why = validate_relationship_stamp(
                    bar, t, decision_bar=decision_bar,
                    decision_time=decision_time, axis=axis)
                if not ok:
                    _drop(cid, "test_history", ev, why)
                    continue
                keep.append(dict(ev))
            out.test_history[cid] = keep

        for field_name, src in (("ref_kind", self.ref_kind),
                                ("round_cluster", self.round_cluster)):
            dst = out.ref_kind if field_name == "ref_kind" \
                else out.round_cluster
            for cid, raw in src.items():
                if not isinstance(raw, dict) or "value" not in raw:
                    _drop(cid, field_name, raw,
                          "unmappable: declaration without a knowability "
                          "stamp (use {'value', 'known_bar'/'known_time'})")
                    continue
                bar, t = _stamp_of(raw)
                ok, why = validate_relationship_stamp(
                    bar, t, decision_bar=decision_bar,
                    decision_time=decision_time, axis=axis)
                if not ok:
                    _drop(cid, field_name, raw, why)
                    continue
                dst[cid] = raw
        return out, dropped


# ---------------------------------------------------------------------------
# Licensed comparisons — ONLY source-substantiated conditional preferences
# (finding F3).  F-class hypotheses never appear here.
# ---------------------------------------------------------------------------

def _rule_old_htf(left: dict, right: dict) -> Optional[bool]:
    indicated = {"old-low-htf", "old-high-reclaimed"}
    lk = left.get("ref_kind")
    rk = right.get("ref_kind")
    l_in = lk in indicated
    r_in = rk in indicated
    if l_in == r_in:
        return None
    return l_in


_LICENSE_RULES: Dict[str, Callable[[dict, dict], Optional[bool]]] = {
    "old-low-htf>other": _rule_old_htf,
}


# ---------------------------------------------------------------------------
# Output types (task §5 contract)
# ---------------------------------------------------------------------------

OUTCOME_SELECTED = "SELECTED"
OUTCOME_UNRESOLVED = "UNRESOLVED"


@dataclass
class ExpertSelection:
    """SELECTED(candidate_id, evidence) or UNRESOLVED(reason, survivors).

    ``base_result`` : the untouched kernel T-S1 record (audit trail).
    ``final_result`` : SelectionResult mirroring the EXPERT outcome — the
    object registered in ``InterpretationLedger`` for real recomputation.
    """

    outcome: str
    task_id: str
    task_name: str
    decision_bar: int
    decision_time: Optional[pd.Timestamp]
    representation_id: str
    candidate_id: Optional[str]
    evidence: List[EvidenceItem]
    reason: Optional[dict]
    surviving_candidate_ids: List[str]
    excluded: List[Exclusion]
    activated_preferences: List[dict]
    inactive_preferences: List[dict]
    conflicts: List[dict]
    base_result: SelectionResult
    final_result: SelectionResult
    interpretation: Optional[dict]
    provenance: List[str]
    policy_snapshots: Dict[str, dict]
    dropped_evidence: List[dict] = field(default_factory=list)

    @property
    def selected_id(self) -> Optional[str]:
        return self.candidate_id

    @property
    def is_selected(self) -> bool:
        return self.outcome == OUTCOME_SELECTED

    def to_record(self) -> dict:
        return {
            "outcome": self.outcome,
            "task_id": self.task_id,
            "task_name": self.task_name,
            "decision_bar": self.decision_bar,
            "decision_time": None if self.decision_time is None
            else str(self.decision_time),
            "representation_id": self.representation_id,
            "candidate_id": self.candidate_id,
            "evidence": [e.to_record() for e in self.evidence],
            "reason": self.reason,
            "surviving_candidate_ids": list(self.surviving_candidate_ids),
            "excluded": [
                {"candidate_id": x.candidate_id, "code": x.code,
                 "rule_ref": x.rule_ref, "detail": x.detail}
                for x in self.excluded],
            "activated_preferences": self.activated_preferences,
            "inactive_preferences": self.inactive_preferences,
            "conflicts": self.conflicts,
            "interpretation": self.interpretation,
            "provenance": list(self.provenance),
            "policy_snapshots": self.policy_snapshots,
            "dropped_evidence": self.dropped_evidence,
            "base_status": self.base_result.status,
            "base_selected_id": self.base_result.selected_id,
            "final_status": self.final_result.status,
            "dependencies": list(self.final_result.dependencies),
            "dependents": list(self.final_result.dependents),
            "direction": self.final_result.direction,
            "notes": list(self.final_result.notes),
        }

    def ledger_payload(self, *, run_id: str = "",
                       points: Optional[Sequence[PointCandidate]] = None,
                       legs: Optional[Sequence[LegCandidate]] = None,
                       rep: Optional[Representation] = None,
                       policy: Optional[PolicyRegistry] = None,
                       role: Optional[str] = None,
                       policy_id: Optional[str] = None,
                       allow_provisional: bool = False,
                       axis: Optional[SharedInformationAxis] = None,
                       relationships: Optional[ContextualRelationships] = None,
                       decision_time: Optional[pd.Timestamp] = None,
                       state_id_prefix: str = "S1X"
                       ) -> dict:
        """COMPLETE recomputation payload (finding F5): live inputs for real
        recomputation (audit D5) AND their serializable records, so the
        stored task can be re-run and audited independently."""
        pts = list(points or ())
        lgs = list(legs or ())
        return {
            "kind": "expert_structural_reference_selection",
            "run_id": run_id,
            # ---- complete inputs ------------------------------------
            "points": pts,
            "legs": lgs,
            "rep": rep,
            "policy": policy,
            "role": role,
            "policy_id": policy_id,
            "allow_provisional": allow_provisional,
            "axis": axis,
            "relationships": relationships,
            "decision_time": decision_time,
            "state_id_prefix": state_id_prefix,
            "knowledge_ids": list(self.policy_snapshots.get(
                "expert_layer", {}).get("value", {}).get("knowledge_ids", [])),
            # ---- serialized input records (audit) --------------------
            "input_records": {
                "points": [candidate_record(p) for p in pts],
                "legs": [{"leg_id": l.leg_id, "start_id": l.start_id,
                          "end_id": l.end_id, "direction": l.direction,
                          "t0": l.t0, "t1": l.t1,
                          "knowable_bar": l.knowable_bar}
                         for l in lgs],
                "relationships": {
                    "test_history": {k: [dict(e) for e in v]
                                     for k, v in
                                     (relationships.test_history or {}).items()
                                     } if relationships else {},
                    "ref_kind": dict(relationships.ref_kind)
                    if relationships else {},
                    "round_cluster": dict(relationships.round_cluster)
                    if relationships else {},
                },
            },
            # ---- recorded outcome (audit) ---------------------------
            "expert_outcome": self.outcome,
            "selected_id": self.candidate_id,
            "survivors": list(self.surviving_candidate_ids),
            "activated_preferences": self.activated_preferences,
            "conflicts": self.conflicts,
            "depends_on_results": [],
        }


# ---------------------------------------------------------------------------
# Preference application (unchanged discipline; only substantiated rules)
# ---------------------------------------------------------------------------

def apply_expert_preferences(
        survivor_ids: Sequence[str],
        evidence_maps: Dict[str, dict],
        knowledge: Sequence[ExpertPreference] = EXPERT_KNOWLEDGE_SRS_V1,
        *,
        scene: Optional[dict] = None,
        license_rules: Optional[Dict[str, Callable[[dict, dict],
                                                   Optional[bool]]]] = None,
) -> Tuple[List[dict], List[dict], List[dict], Optional[str], dict]:
    """Apply documented conditional preferences over the ELIGIBLE survivor
    set.  Returns (activated, inactive, conflicts, winner_or_None,
    diagnostics).  F-class records never license anything (finding F3);
    contradictory licensed comparisons are PRESERVED (task §7) and resolve
    nothing; a unique candidate is returned only when it wins at least one
    licensed comparison and loses none.  ``license_rules`` may substitute
    the rule registry (test seam for conflict preservation)."""
    scene = scene or {}
    rules = _LICENSE_RULES if license_rules is None else license_rules
    activated: List[dict] = []
    inactive: List[dict] = []
    conflicts: List[dict] = []
    ids = list(survivor_ids)

    for pref in knowledge:
        if pref.kclass == KCLASS_F:
            inactive.append({"pref_id": pref.pref_id,
                             "cause": "F-class: nonbinding research "
                                      "hypothesis — never licenses a "
                                      "comparison (task §4; finding F3)"})
            continue
        if pref.licenses == "none":
            inactive.append({"pref_id": pref.pref_id,
                             "cause": "task-conditioning/constraint record: "
                                      "licenses no candidate comparison"})
            continue
        rule = rules.get(pref.licenses)
        if rule is None:  # pragma: no cover — registry integrity
            raise ValueError(f"unknown license rule {pref.licenses!r}")
        present = [cid for cid in ids
                   if all(k in evidence_maps.get(cid, {})
                          for k in pref.observable_evidence)]
        if not present:
            inactive.append({
                "pref_id": pref.pref_id,
                "cause": f"observable evidence {pref.observable_evidence} "
                         f"absent/unavailable on all survivors — preference "
                         f"inapplicable (never a default)"})
            continue
        pref_pairs: List[dict] = []
        for i, a in enumerate(present):
            for b in present[i + 1:]:
                verdict = rule(evidence_maps[a], evidence_maps[b])
                if verdict is None:
                    continue
                winner, loser = (a, b) if verdict else (b, a)
                pref_pairs.append({"pref_id": pref.pref_id,
                                   "winner": winner, "loser": loser,
                                   "basis": pref.licenses})
        if not pref_pairs:
            inactive.append({
                "pref_id": pref.pref_id,
                "cause": "evidence present but not in the documented "
                         "comparison shape — no comparison licensed "
                         "(incomplete comparisons never resolve)"})
            continue
        activated.append({"pref_id": pref.pref_id, "pairs": pref_pairs,
                          "source": pref.source, "klass": pref.klass})

    for act in activated:
        for pr in act["pairs"]:
            w, l = pr["winner"], pr["loser"]
            for other in activated:
                for pr2 in other["pairs"]:
                    if pr2["winner"] == l and pr2["loser"] == w:
                        conflicts.append({
                            "kind": "preference-vs-preference",
                            "pair": [w, l],
                            "pref_ids": sorted({pr["pref_id"],
                                                pr2["pref_id"]}),
                            "resolution": "none — conflict preserved (task "
                                          "§7); comparison resolves nothing"})

    conflict_pairs = {tuple(sorted(c["pair"])) for c in conflicts}
    clean_wins: Dict[str, int] = {cid: 0 for cid in ids}
    clean_losses: Dict[str, int] = {cid: 0 for cid in ids}
    for act in activated:
        for pr in act["pairs"]:
            key = tuple(sorted((pr["winner"], pr["loser"])))
            if key in conflict_pairs:
                continue
            clean_wins[pr["winner"]] += 1
            clean_losses[pr["loser"]] += 1

    preferred = [cid for cid in ids
                 if clean_wins[cid] > 0 and clean_losses[cid] == 0]
    winner = preferred[0] if len(preferred) == 1 else None
    diagnostics = {"clean_wins": clean_wins, "clean_losses": clean_losses,
                   "preferred": preferred, "n_conflicts": len(conflicts)}
    return activated, inactive, conflicts, winner, diagnostics


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _know_stamp(p: object) -> tuple:
    kt = getattr(p, "knowable_time", None)
    return (kt is not None,
            pd.Timestamp(kt) if kt is not None else pd.Timestamp(0),
            p.knowable_bar)


def _evidence_for(cid: str, c: PointCandidate, legs: Sequence[LegCandidate],
                  decision_bar: int,
                  decision_time: Optional[pd.Timestamp],
                  rel: ContextualRelationships) -> List[EvidenceItem]:
    """Observable evidence per candidate.  Relationship facts arrive ALREADY
    validated (finding F1).  Test events are reported as two DISTINCT
    observations (finding F3): state only — no rejection, validation or
    successful reaction is inferred from either."""
    items = [
        EvidenceItem("side", CLASS_F, c.side, "F:candidate",
                     "turning-point side"),
        EvidenceItem("level", CLASS_F, c.level, "F:candidate",
                     "declared representation level"),
        EvidenceItem("knowable", CLASS_F,
                     {"knowable_bar": c.knowable_bar,
                      "knowable_time": None if c.knowable_time is None
                      else str(c.knowable_time)},
                     "R:SP-01", "knowable at or before the decision"),
        EvidenceItem("status_at_decision", CLASS_F,
                     c.status_at(decision_bar, decision_time),
                     "R:SP-13", "append-only status history (audit D3)"),
    ]
    anchored = [l.leg_id for l in legs
                if getattr(l, "start_id", None) == cid
                or getattr(l, "end_id", None) == cid]
    if anchored:
        items.append(EvidenceItem("leg_role", CLASS_F, anchored, "R:SP-14",
                                  "endpoint of these legs"))
    if getattr(c, "same_bar_order", "resolved") != "resolved":
        items.append(EvidenceItem(
            "same_bar_ambiguity", CLASS_F,
            {"order": c.same_bar_order,
             "evidence_class": same_bar_evidence_class(c.same_bar_evidence)},
            "F:endpoints", "audit D4 ambiguity record"))
    if cid in rel.test_history:
        events = rel.test_history[cid]
        wicks = [e for e in events if e.get("kind") == EVENT_WICK_TOUCH]
        throughs = [e for e in events if e.get("kind") == EVENT_CLOSE_THROUGH]
        state_note = ("state observation only (file 15 §15.4: taken status "
                      "establishes state, not cause) — no rejection, "
                      "validation or successful reaction inferred")
        items.append(EvidenceItem("wick_range_touches", CLASS_F, wicks,
                                  "F:interval-containment", state_note))
        items.append(EvidenceItem("close_throughs", CLASS_F, throughs,
                                  "R:SP-03", state_note))
    rk = rel.ref_kind.get(cid)
    if rk is not None:
        items.append(EvidenceItem("ref_kind", CLASS_S, rk["value"],
                                  "S:REF-OLD-LOW-HTF",
                                  "upstream-declared reference kind (P1); "
                                  f"knowability stamp "
                                  f"bar={rk.get('known_bar')} "
                                  f"time={rk.get('known_time')}"))
    rc = rel.round_cluster.get(cid)
    if rc is not None:
        items.append(EvidenceItem("round_cluster", CLASS_S, rc["value"],
                                  "S:SRC-OSLER-SR150",
                                  "upstream-declared cluster marker "
                                  "(nonbinding hypothesis KP-06)"))
    return items


def _evidence_maps(items_by_id: Dict[str, List[EvidenceItem]]
                   ) -> Dict[str, dict]:
    maps: Dict[str, dict] = {}
    for cid, items in items_by_id.items():
        m: dict = {}
        for it in items:
            if it.name == "ref_kind":
                m["ref_kind"] = it.value
            elif it.name == "round_cluster":
                m["round_cluster"] = it.value
        maps[cid] = m
    return maps


def _account_all_candidates(points: Sequence[PointCandidate],
                            survivors: Sequence[str],
                            excluded: Sequence[Exclusion],
                            decision_bar: int,
                            decision_time: Optional[pd.Timestamp]
                            ) -> List[Exclusion]:
    """Finding F2: candidates are NEVER silently omitted.  Any input
    candidate in neither the survivor set nor the exclusion set is surfaced
    with an explicit lifecycle-based exclusion record."""
    known = set(survivors) | {x.candidate_id for x in excluded}
    extra: List[Exclusion] = []
    for p in points:
        if p.candidate_id in known:
            continue
        st = p.status_at(decision_bar, decision_time)
        code = X_SUPER if st == STATUS_SUPERSEDED else X_STATE
        extra.append(Exclusion(
            p.candidate_id, code, "R:SP-13",
            f"not eligible at the decision (status_at={st!r}); surfaced, "
            f"never silently omitted"))
    return extra


def _mk_final(*, outcome: str, decision_bar: int,
              decision_time: Optional[pd.Timestamp], rep_id: str,
              candidate_id: Optional[str], survivors: List[str],
              excluded: List[Exclusion], reason: Optional[dict],
              provenance: List[str], policy_refs: List[str],
              psnaps: Dict[str, dict], dependents: List[str],
              dependencies: List[str], direction: Optional[str],
              notes: List[str]) -> SelectionResult:
    unresolved = None
    if outcome == OUTCOME_UNRESOLVED:
        unresolved = UnresolvedState(
            state_id=f"S1X-{decision_bar}", task=SRS_TASK_ID,
            decision_bar=decision_bar, survivors=list(survivors),
            excluded=list(excluded),
            reason_code=(reason or {}).get("code", REASON_MP),
            evidence_needed=(reason or {}).get("evidence_needed", ""),
            policy_refs=list(policy_refs), provenance=list(provenance),
            dependents_blocked=list(dependents))
    status = ("justified" if outcome == OUTCOME_SELECTED
              else ("unresolved" if survivors else "empty"))
    return SelectionResult(
        task_id=SRS_TASK_ID, decision_bar=decision_bar, status=status,
        selected_id=candidate_id, survivors=list(survivors),
        excluded=list(excluded), unresolved=unresolved,
        provenance=list(provenance), policy_refs=list(policy_refs),
        representation_id=rep_id, dependents=list(dependents),
        notes=list(notes), direction=direction,
        dependencies=list(dependencies), decision_time=decision_time,
        policy_snapshots=dict(psnaps))


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------

def expert_structural_reference_selection(
        *,
        points: Sequence[PointCandidate],
        legs: Sequence[LegCandidate],
        decision_bar: int,
        rep: Representation,
        policy: PolicyRegistry,
        role: Optional[str] = None,
        policy_id: Optional[str] = None,
        allow_provisional: bool = False,
        decision_time: Optional[pd.Timestamp] = None,
        axis: Optional[SharedInformationAxis] = None,
        relationships: Optional[ContextualRelationships] = None,
        knowledge: Sequence[ExpertPreference] = EXPERT_KNOWLEDGE_SRS_V1,
        state_id_prefix: str = "S1X",
) -> ExpertSelection:
    """Expert-grounded STRUCTURAL_REFERENCE_SELECTION on one frozen scene.

    Pipeline (task §6 + audit findings):
      1  validate the declared task/role (F2) and every relationship fact
         against the decision boundary (F1);
      2  retrieve candidates + existing eligibility gates (kernel T-S1);
      3  surface every candidate (no silent omission, F2);
      4  identify task-relevant evidence (F3: state-only observations);
      5  apply documented conditional preferences over ELIGIBLE survivors
         (only source-substantiated comparisons);
      6  preserve conflicts / incomparability as UNRESOLVED with reasons;
      7  equal knowable-time ties are UNRESOLVED (F4, defense in depth);
      8  emit SELECTED or UNRESOLVED with evidence + source provenance;
      9  continue one compatible structural interpretation where supported;
     10  preserve revision dependencies (SelectionResult + ledger payloads).
    """
    # ---- F1: validate every relationship fact against the decision --------
    rel_raw = relationships or ContextualRelationships()
    rel, dropped = rel_raw.validated(decision_bar=decision_bar,
                                     decision_time=decision_time, axis=axis)

    # ---- F2: a valid declared role is required --------------------------
    role_missing = role is None
    role_valid = role in VALID_ROLES
    eff_role = role if role_valid else EXPERT_ROLE_UNDECLARED

    # ---- steps 1-2: EXISTING gates + role semantics (kernel T-S1) -------
    base = task_s1_structural_reference(
        points, legs, decision_bar, rep, eff_role, policy,
        policy_id=policy_id, allow_provisional=allow_provisional,
        state_id_prefix=state_id_prefix, decision_time=decision_time,
        axis=axis)

    by_id = {p.candidate_id: p for p in points}

    # ---- F2: gate-eligible candidates = survivors + role-policy-removed -
    # (X-POL removal is the Pi_T ROLE decision, not an eligibility gate;
    # those candidates stay ELIGIBLE and must be comparable (finding F2:
    # "compare only eligible candidates")).  X-STATE/X-SUPER/X-KNOW/X-SCALE
    # removals are eligibility exclusions and stay out.
    eligible_ids: List[str] = []
    for cid in list(base.survivors) + [
            x.candidate_id for x in base.excluded if x.code == "X-POL"]:
        if cid not in eligible_ids and cid in by_id:
            eligible_ids.append(cid)
    eligible_objs = [by_id[cid] for cid in eligible_ids]

    # ---- F2: never silently omit a candidate ---------------------------
    accounting = _account_all_candidates(points, base.survivors,
                                         base.excluded, decision_bar,
                                         decision_time)
    all_excluded = list(base.excluded) + accounting

    # ---- step 3: task-relevant evidence (validated facts only) ----------
    items_by_id = {
        p.candidate_id: _evidence_for(p.candidate_id, p, legs, decision_bar,
                                      decision_time, rel)
        for p in eligible_objs}
    maps = _evidence_maps(items_by_id)

    scene = {"task_id": SRS_TASK_ID, "role": role,
             "has_declared_policy": policy_id is not None}
    activated, inactive, conflicts, pref_winner, diag = apply_expert_preferences(
        eligible_ids, maps, knowledge, scene=scene)

    prov = list(base.provenance) + [
        "X:expert-selection-v1.1",
        "F:knowledge=%s" % "+".join(p.pref_id for p in knowledge)]
    if dropped:
        prov.append(f"F:relationship-evidence-dropped={len(dropped)}")
    pregs = list(base.policy_refs)
    psnaps: Dict[str, dict] = dict(base.policy_snapshots)
    psnaps["expert_layer"] = {
        "policy_id": "expert-selection-v1.1", "version": 1,
        "value": {"knowledge_ids": [p.pref_id for p in knowledge],
                  "task": SRS_TASK_NAME},
        "class": CLASS_O, "kind": KIND_PROCEDURE}

    def _evidence_chain(cid: str) -> List[EvidenceItem]:
        chain = list(items_by_id.get(cid, ()))
        chain.append(EvidenceItem(
            "gate_facts", CLASS_F,
            {"confirmed": True, "knowable_at_decision": True,
             "in_view": True},
            "R:SP-01/R:SP-13/R:SP-02",
            "survived the kernel's existing eligibility gates"))
        for act in activated:
            for pr in act["pairs"]:
                if pr["winner"] == cid:
                    pref = KNOWLEDGE_BY_ID.get(pr["pref_id"])
                    chain.append(EvidenceItem(
                        f"preference:{pr['pref_id']}", CLASS_S,
                        pr["basis"],
                        f"S:{pr['pref_id']}",
                        (pref.source[:160] if pref else "")))
        return chain

    def _finish(outcome: str, candidate_id: Optional[str],
                reason: Optional[dict], interpretation: Optional[dict],
                extra_prov: Sequence[str] = ()) -> ExpertSelection:
        survivors = list(base.survivors)
        final = _mk_final(
            outcome=outcome, decision_bar=decision_bar,
            decision_time=decision_time, rep_id=rep.rep_id,
            candidate_id=candidate_id, survivors=survivors,
            excluded=all_excluded, reason=reason,
            provenance=list(prov) + list(extra_prov), policy_refs=pregs,
            psnaps=psnaps, dependents=list(base.dependents),
            dependencies=list(base.dependencies),
            direction=base.direction, notes=list(base.notes))
        if outcome == OUTCOME_SELECTED and candidate_id is not None:
            ev = _evidence_chain(candidate_id)
        else:
            ev = [e for cid in survivors for e in items_by_id.get(cid, ())]
        return ExpertSelection(
            outcome=outcome, task_id=SRS_TASK_ID, task_name=SRS_TASK_NAME,
            decision_bar=decision_bar, decision_time=decision_time,
            representation_id=rep.rep_id, candidate_id=candidate_id,
            evidence=ev, reason=reason,
            surviving_candidate_ids=survivors, excluded=all_excluded,
            activated_preferences=activated, inactive_preferences=inactive,
            conflicts=conflicts, base_result=base, final_result=final,
            interpretation=interpretation,
            provenance=list(prov) + list(extra_prov),
            policy_snapshots=psnaps, dropped_evidence=dropped)

    # ---- F2: invalid task instance (missing/unknown role) ---------------
    if not role_valid:
        why = ("missing" if role_missing else f"not recognized ({role!r})")
        reason = {
            "code": REASON_MP,
            "text": (f"no valid declared role for {SRS_TASK_NAME}: role "
                     f"{why}; declare one of {VALID_ROLES} (a valid task "
                     f"instance requires task AND role)"),
            "evidence_needed": ("declare a valid role (file 16 §16.3); a "
                                "missing/unknown role never falls through "
                                "to preference selection (finding F2)"),
        }
        return _finish(OUTCOME_UNRESOLVED, None, reason, None)

    # ---- F4: equal knowable-time tie guard (defense in depth) -----------
    if base.is_justified and base.selected_id is not None:
        sel_p = by_id.get(base.selected_id)
        tied_ids: List[str] = []
        if role == "last-confirmed-extreme" and sel_p is not None:
            key = _know_stamp(sel_p)
            tied_ids = [cid for cid in base.survivors
                        if cid != base.selected_id and cid in by_id
                        and _know_stamp(by_id[cid]) == key]
        elif role == "origin-of-last-confirmed-leg":
            sel_legs = [l for l in legs
                        if getattr(l, "start_id", None) == base.selected_id]
            if sel_legs:
                key = max(_leg_key(l) for l in sel_legs)
                for l in legs:
                    if (getattr(l, "start_id", None) != base.selected_id
                            and _leg_key(l) == key):
                        tied_ids.append(l.start_id)
        if tied_ids:
            survivors = sorted(set(base.survivors) | set(tied_ids))
            reason = {
                "code": REASON_MP,
                "text": ("equal knowable-time/recency tie between "
                         f"{sorted(set(tied_ids) | {base.selected_id})} — "
                         "never order-resolved (finding F4)"),
                "evidence_needed": "declare a tie policy (SP-18)",
            }
            return _finish(OUTCOME_UNRESOLVED, None, reason, None)

    # ---- step 7a: declared Pi_T role policy resolved the task -----------
    if base.is_justified:
        cid = base.selected_id
        for act in activated:
            for pr in act["pairs"]:
                if pr["loser"] == cid:
                    conflicts.append({
                        "kind": "policy-vs-preference",
                        "pair": [pr["winner"], cid],
                        "pref_ids": [pr["pref_id"]],
                        "resolution": (
                            "Pi_T role policy retained (documented "
                            "precedence); preference preserved as the "
                            "SP-12 main alternative — tension recorded, "
                            "not silently applied")})
        interpretation = {
            "kind": "T-S1-structural-interpretation",
            "view": rep.view_id, "reference": cid, "role": role,
            "direction": base.direction, "state": "reference-active",
            "conditional_on": [PI_T_PRECEDENCE_DOC]
            + [a["pref_id"] for a in activated],
            "dependents": list(base.dependents),
            "revision_dependencies": list(base.dependencies),
        }
        return _finish(OUTCOME_SELECTED, cid, None, interpretation)

    # ---- gate-blocked states (IC/AI/...): preferences never override ----
    if base.unresolved is not None and base.unresolved.reason_code != REASON_MP:
        reason = {"code": base.unresolved.reason_code,
                  "text": base.unresolved.evidence_needed,
                  "evidence_needed": base.unresolved.evidence_needed}
        return _finish(OUTCOME_UNRESOLVED, None, reason, None)

    # ---- MP state with survivors: documented conditional preferences ----
    survivors = list(base.survivors)
    if not survivors:
        reason = {"code": REASON_IC, "text": "no eligible candidates",
                  "evidence_needed": "more history / confirmation"}
    elif conflicts:
        reason = {"code": REASON_EP,
                  "text": "conflicting source-grounded preferences: "
                          + "; ".join(
                              f"{c['pair']} <- {c['pref_ids']}"
                              for c in conflicts),
                  "evidence_needed": "pre-registered comparative evaluation "
                                     "(file 18 objective B/C) or a declared "
                                     "Pi_T policy (SP-18)"}
    elif pref_winner is not None:
        cid = pref_winner
        interpretation = {
            "kind": "T-S1-structural-interpretation",
            "view": rep.view_id, "reference": cid, "role": role,
            "direction": base.direction, "state": "reference-active",
            "conditional_on": [a["pref_id"] for a in activated],
            "dependents": list(base.dependents),
            "revision_dependencies": list(base.dependencies),
        }
        return _finish(OUTCOME_SELECTED, cid, None, interpretation,
                       extra_prov=["R:preference-resolution(%s)"
                                   % ",".join(a["pref_id"]
                                              for a in activated)])
    else:
        if activated and len(diag["preferred"]) != 1:
            code, text = (REASON_EP,
                          "documented preferences apply but do not uniquely "
                          "order the eligible survivors (preferred: %s; "
                          "incomplete comparisons never resolve)"
                          % diag["preferred"])
            needed = ("comparative evidence between the surviving "
                      "candidates (file 18 objective B) or a declared Pi_T "
                      "policy (SP-18)")
        else:
            code, text = (REASON_MP,
                          "no declared role policy resolution and no "
                          "applicable source-grounded preference with "
                          "validated observable evidence")
            needed = ("declare a Pi_T role policy (SP-18) + SP-12 "
                      "sensitivity, or supply VALIDATED relationship "
                      "evidence (knowability-stamped declarations; "
                      "finding F1)")
        reason = {"code": code, "text": text, "evidence_needed": needed}

    return _finish(OUTCOME_UNRESOLVED, None, reason, None)


def _leg_key(l: object) -> tuple:
    return leg_recency_key(l)


# ---------------------------------------------------------------------------
# Real InterpretationLedger recomputation (finding F5)
# ---------------------------------------------------------------------------

def _recompute_expert_selection(payload: dict, update_bar: int,
                                update_time: Optional[pd.Timestamp]
                                ) -> SelectionResult:
    """Recompute the expert selection from its stored COMPLETE inputs as of
    the update boundary.  An incomplete or empty payload raises — the ledger
    marks the result STALE, and stale/empty recomputation is NEVER a
    success (fail closed)."""
    required = ("points", "legs", "rep", "policy", "role")
    missing = [k for k in required if payload.get(k) is None]
    if missing:
        raise ValueError(
            f"expert-selection recompute: incomplete payload, missing "
            f"{missing} — stale, never success")
    if not payload.get("points"):
        raise ValueError(
            "expert-selection recompute: empty candidate input — stale, "
            "never success")
    k_ids = payload.get("knowledge_ids") or [
        p.pref_id for p in EXPERT_KNOWLEDGE_SRS_V1]
    try:
        knowledge = tuple(KNOWLEDGE_BY_ID[i] for i in k_ids)
    except KeyError as exc:
        raise ValueError(
            f"expert-selection recompute: unknown knowledge id {exc}") from exc
    sel = expert_structural_reference_selection(
        points=payload["points"], legs=payload["legs"],
        decision_bar=update_bar, rep=payload["rep"],
        policy=payload["policy"], role=payload["role"],
        policy_id=payload.get("policy_id"),
        allow_provisional=payload.get("allow_provisional", False),
        decision_time=(update_time if update_time is not None
                       else payload.get("decision_time")),
        axis=payload.get("axis"),
        relationships=payload.get("relationships"),
        knowledge=knowledge,
        state_id_prefix=payload.get("state_id_prefix", "S1X"))
    return sel.final_result


register_recompute_handler("expert_structural_reference_selection",
                           _recompute_expert_selection)
