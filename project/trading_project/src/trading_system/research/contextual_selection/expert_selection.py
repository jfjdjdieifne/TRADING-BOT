"""Expert-grounded contextual selection V1 — STRUCTURAL_REFERENCE_SELECTION (T-S1).

CONTROLLED IMPLEMENTATION (no parallel architecture).  This module is the
first runnable expert-grounded JUDGMENT LAYER over the existing CSM kernel
(``contextual_selection.csm``).  It consumes — never reimplements — the
existing candidates (``PointCandidate``/``LegCandidate``), lifecycle/status
history, eligibility gates (``task_s1_structural_reference`` -> SP-01/SP-13/
SP-14/X-SCALE/X-SUPER/same-bar discipline), the shared information-time axis
(``SharedInformationAxis`` over the CLOSED 6.2A-0 contract in
``research.information_time``), policy registry (SP-18) and the
revision/dependency mechanisms (``SelectionResult.dependencies/dependents``,
``UnresolvedState.dependents_blocked``, ``InterpretationLedger`` payloads).

The layer adds exactly one capability the kernel deliberately leaves open:

    "For this analytical task, which candidate is currently the most
     relevant, and WHY?"   ->  SELECTED(candidate_id, evidence)
                          or  UNRESOLVED(reason, surviving_candidate_ids)

by applying DOCUMENTED, SOURCE-GROUNDED conditional preferences (task
classification E / foundation class S) whose applicability requires
observable evidence, and preserving — never silently resolving — conflicts.

Knowledge provenance (task §3; knowledge_foundation jfjdjdieifne/test @
6c8bf6fd files 05/08/12/15/16/17/19 plus the named expert source families):
ICT / Michael J. Huddleston (primary educational source for ICT definitions;
SRC-ICT-* P1 partial transcripts), Grimes, Wyckoff, Livermore, Elder,
Lo-Mamaysky-Wang, Osler, Bulkowski.  Every preference record carries its
exact source, applicable task/context, observable evidence, known exceptions
and conflict status (task §4).  Numeric weights and undocumented precedence
are NEVER invented (task §4, §6).

Classification (task §4) is carried per record as ``kclass``:
    A deterministic fact · B hard eligibility constraint ·
    C declared analytical policy · D task-conditioning information ·
    E source-grounded conditional preference · F unresolved expert hypothesis.
Only A-E influence selection behavior.  F-class records are documentation of
REFUSALS and can never become binding rules (task §4).

Determinism contract (SWS-04d): identical inputs (including relationship
evidence) produce identical output records; recompute-from-truncated-data
reproduces the stored output.  No future information is read: every evidence
item is checked against the decision boundary through the existing axis /
``status_at()`` discipline.

This module contains no market thresholds, no confidence percentages, no
learned scores, no trading recommendation and no future-outcome logic.
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
    KIND_RESEARCH,
    KIND_SOURCE,
    REASON_AI,
    REASON_EP,
    REASON_IC,
    REASON_MP,
    STATUS_CONFIRMED,
    Exclusion,
    LegCandidate,
    PointCandidate,
    PolicyRegistry,
    Representation,
    SelectionResult,
    SharedInformationAxis,
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

#: The task this V1 layer implements (task §5: exactly one selection subject).
SRS_TASK_ID = "T-S1"
SRS_TASK_NAME = "STRUCTURAL_REFERENCE_SELECTION"

#: Role sentinel for a task card that declares no role at all.  The kernel's
#: T-S1 then reports MP with the gated survivor set, which is exactly the
#: state this layer's preference resolution may attempt to reduce.
EXPERT_ROLE_UNDECLARED = "__role-undeclared__"

#: Declared-role semantics (Pi_T, SWS-02) take precedence over E-class
#: conditional preferences when a role policy is registered and applies.
#: This precedence is DOCUMENTED (knowledge_foundation/15 §15.7 item 3:
#: "a survivor chosen by a declared Pi_T"), never invented here.  Any
#: contradicting source-grounded preference is PRESERVED as a tension record
#: (task §7) and reported as the SP-12 main alternative.
PI_T_PRECEDENCE_DOC = "knowledge_foundation/15 §15.7.3 (Pi_T resolution)"


# ---------------------------------------------------------------------------
# Knowledge records
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ExpertPreference:
    """One documented, source-grounded knowledge record (task §4 fields).

    ``observable_evidence`` lists the evidence keys that MUST be observable
    before the record's comparison may be licensed.  Absent evidence makes
    the record inapplicable — it never degrades into a default.
    """

    pref_id: str
    task_id: str
    kclass: str                 # task §4: A..F
    klass: str                  # file 15 §15.3: F/O/S/L/U
    source: str                 # exact citation
    source_family: str          # "ICT" | "Grimes" | "Wyckoff" | ...
    statement: str
    context: str                # applicable context
    observable_evidence: Tuple[str, ...]
    licenses: str               # comparison id this record may license
    exceptions: str
    conflict_status: str
    provenance_refs: Tuple[str, ...]
    binding: bool = False       # only B-class records bind (hard gates)

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


def _kp(**kw) -> ExpertPreference:
    return ExpertPreference(task_id=SRS_TASK_ID, **kw)


# ---------------------------------------------------------------------------
# The documented knowledge base for STRUCTURAL_REFERENCE_SELECTION (V1).
#
# Sources cited exactly as verified (task §3).  Source claims are used as
# PROVISIONAL ANALYTICAL KNOWLEDGE (E/S class), never as empirically
# established market truth (task §3 final paragraph).
# ---------------------------------------------------------------------------

EXPERT_KNOWLEDGE_SRS_V1: Tuple[ExpertPreference, ...] = (
    _kp(
        pref_id="KP-01",
        kclass=KCLASS_D, klass=CLASS_O,
        source=("knowledge_foundation/16 §16.3 (T-S1 task card, SWS-02); "
                "Wyckoff, The Richard D. Wyckoff Method of Trading and "
                "Investing in Stocks (1931 course), five-step approach; "
                "Livermore, How to Trade in Stocks (1940), 'The Pivotal "
                "Point' — the price 'at which the trend is decided'"),
        source_family="knowledge_foundation+Wyckoff+Livermore",
        statement=("the declared analytical role (task card) determines which "
                   "reference is relevant; the 'origin of the most recent "
                   "confirmed leg' rule is an operational definition (SWS-02), "
                   "not a market claim"),
        context="every T-S1 selection (task conditioning)",
        observable_evidence=("declared_role", "policy_ref"),
        licenses="none",
        exceptions=("without a declared role the kernel reports MP and this "
                    "record licenses no comparison"),
        conflict_status="uncontested (O-class operational definition)",
        provenance_refs=("knowledge_foundation/16:SWS-02",
                         "knowledge_foundation/19:W1", "O:P-ORIGIN"),
    ),
    _kp(
        pref_id="KP-02",
        kclass=KCLASS_E, klass=CLASS_S,
        source=("Grimes, The Art & Science of Technical Analysis (Wiley, "
                "2012) — random-lines falsification: untested drawn levels "
                "behave like random lines; Livermore, How to Trade in Stocks "
                "(1940) — a pivotal point is validated by subsequent price "
                "action; Osler, Stop-Loss Orders and Price Cascades in "
                "Currency Markets, FRBNY Staff Report 150 (2002) / JIMF "
                "24(2) 2005 — stop orders cluster at documented levels and "
                "price reacts/cascades at clusters"),
        source_family="Grimes+Livermore+Osler",
        statement=("among role-eligible references, one carrying DOCUMENTED "
                   "prior test evidence (a recorded close-crossing binding or "
                   "an exact price-range touch before the decision) is "
                   "preferred over a prominent but untested one"),
        context=("comparison among survivors of the same declared role where "
                 "exactly one candidate carries test evidence"),
        observable_evidence=("test_history",),
        licenses="tested>untested",
        exceptions=("applies only in the tested-vs-untested comparison shape "
                    "(never as a touch-count ranking — file 15 §15.4 bans "
                    "touch count as sole basis); inapplicable when both or "
                    "neither candidate is tested; a declared Pi_T role policy "
                    "takes documented precedence and any tension is recorded "
                    "as the SP-12 main alternative, never silently applied"),
        conflict_status=("CF-01 (level validity) partial: CONDITIONAL — no "
                         "universal support/resistance claim is made; "
                         "untested-extreme cases are legitimate exceptions"),
        provenance_refs=("knowledge_foundation/15 §15.3,§15.4",
                         "SRC-OSLER-SR150", "SRC-GRIMES-2012",
                         "SRC-LIVERMORE-1940"),
    ),
    _kp(
        pref_id="KP-03",
        kclass=KCLASS_E, klass=CLASS_S,
        source=("ICT / Michael J. Huddleston, ICT Mentorship Core Content "
                "Month 04 lessons (SRC-ICT-OB / SRC-ICT-FVG, P1 partial "
                "transcripts, 2016 content): a support reference is an 'old "
                "low on a higher timeframe' or a reclaimed 'old high' "
                "(REF-OLD-LOW-HTF / REF-OLD-HIGH-RECLAIMED)"),
        source_family="ICT",
        statement=("for a declared support/structural-reference role, "
                   "candidates whose upstream-declared reference kind is "
                   "'old-low-htf' or 'old-high-reclaimed' are the "
                   "source-indicated references over locally drawn ones"),
        context="declared support/structural reference role (any T-S1 role)",
        observable_evidence=("ref_kind",),
        licenses="old-low-htf>other",
        exceptions=("the source does not define how the old reference is "
                    "confirmed or when it expires (file 05 §5.4a P-R open) — "
                    "the preference is provisional; auto-caption wording is "
                    "P1 grade; if a dispute needs the source's exact wording, "
                    "the result must surface AI instead of guessing"),
        conflict_status="uncontested in the foundation (CF-01 concerns the "
                        "order-block definition, not this reference kind)",
        provenance_refs=("knowledge_foundation/05 §5.4a:P-R",
                         "knowledge_foundation/08:CASE observables",
                         "SRC-ICT-OB", "SRC-ICT-FVG"),
    ),
    _kp(
        pref_id="KP-04",
        kclass=KCLASS_B, klass=CLASS_F,
        source=("knowledge_foundation/15 §15.7 AI definition + audit D4 "
                "(same-bar ambiguity surfaced, never sequenced); "
                "Lo, Mamaysky & Wang, Foundations of Technical Analysis, "
                "J. Finance 55(4) 2000 — pattern definitions must control "
                "look-ahead (explicit estimation lag)"),
        source_family="knowledge_foundation+Lo-Mamaysky-Wang",
        statement=("a selected reference whose intrabar high/low order is "
                   "materially unresolved cannot yield a fully justified "
                   "result; it surfaces AI (hard constraint, already enforced "
                   "by the kernel)"),
        context="any selection whose survivor set intersects same-bar "
                "ambiguity records",
        observable_evidence=("same_bar_order", "same_bar_evidence"),
        licenses="none",
        exceptions="endpoint-proven order is factual and is never downgraded",
        conflict_status="uncontested",
        provenance_refs=("knowledge_foundation/15 §15.7",
                         "SRC-LMW-2000"),
        binding=True,
    ),
    _kp(
        pref_id="KP-05",
        kclass=KCLASS_F, klass=CLASS_U,
        source=("Wyckoff (1931 course) effort-vs-result readings require "
                "volume; ICT/community narratives that gaps or blocks define "
                "the operative reference (marketing forms)"),
        source_family="Wyckoff+ICT/community",
        statement=("UNRESOLVED expert hypotheses: volume-based effort/result "
                   "validation of references; narrative claims that FVG/OB "
                   "geometry decides which structural reference matters"),
        context="documented refusal record",
        observable_evidence=("volume",),
        licenses="none",
        exceptions=("volume-dependent readings are unidentifiable on "
                    "OHLC-alone datasets (MO); narrative forms have no "
                    "independent validation in the verified evidence and are "
                    "kept provisional"),
        conflict_status="F-class: never binding (task §4); recorded so the "
                        "refusal is auditable",
        provenance_refs=("knowledge_foundation/10 (open register)",
                         "knowledge_foundation/05 §5.4a"),
    ),
    _kp(
        pref_id="KP-06",
        kclass=KCLASS_E, klass=CLASS_S,
        source=("Osler, Stop-Loss Orders and Price Cascades in Currency "
                "Markets, FRBNY Staff Report 150 (2002) / JIMF 24(2) 2005 — "
                "stop-loss orders cluster near round numbers (dealer-order "
                "evidence) and price moves rapidly through the clusters"),
        source_family="Osler",
        statement=("when an upstream process DECLARES a round-number/stop-"
                   "cluster marker on candidates, a marked reference is "
                   "preferred over an unmarked one in the same role"),
        context="upstream-declared cluster marker present on at least one "
                "survivor",
        observable_evidence=("round_cluster",),
        licenses="cluster>non-cluster",
        exceptions=("the marker must be declared upstream — this layer never "
                    "detects round numbers (no invented market thresholds); "
                    "the evidence is FX dealer-order data and instrument "
                    "transfer is unproven (provisional; OOD caution)"),
        conflict_status="uncontested as evidence; transfer status noted",
        provenance_refs=("SRC-OSLER-SR150",),
    ),
    _kp(
        pref_id="KP-07",
        kclass=KCLASS_D, klass=CLASS_O,
        source=("Elder, Trading for a Living (1993) / triple screen "
                "(Futures, 1985) — decide the higher timeframe first; "
                "Wyckoff (1931) five-step approach — determine position "
                "before acting; knowledge_foundation/16 T-S6 + SP-02/SP-16"),
        source_family="Elder+Wyckoff+knowledge_foundation",
        statement=("the answering scale/view is fixed by the task card "
                   "before T-S1 runs; candidates of other views are excluded "
                   "by X-SCALE (existing kernel gate), never mixed"),
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
# Evidence model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EvidenceItem:
    """One observable fact used in a selection (file 15 §15.3: the class is
    part of the record; a claim without a class is invalid)."""

    name: str
    klass: str            # F/O/S/L/U
    value: object
    source_ref: str       # e.g. "R:SP-01", "R:test-history", "S:REF-OLD-LOW-HTF"
    detail: str = ""

    def __post_init__(self) -> None:
        if self.klass not in (CLASS_F, CLASS_O, CLASS_S, CLASS_U):
            raise ValueError(f"bad evidence class {self.klass!r}")

    def to_record(self) -> dict:
        return {"name": self.name, "class": self.klass, "value": self.value,
                "source_ref": self.source_ref, "detail": self.detail}


@dataclass
class ContextualRelationships:
    """Existing contextual relationship evidence supplied to the layer.

    The layer CONSUMES these facts; it never derives market thresholds.
    Producers: the kernel's own procedures (SP-03 binding via
    ``task_s2_event_binding``/close crossings), exact price-range containment
    (F-class interval arithmetic, same family as SP-05), and upstream
    declarations (S-class markers such as REF-OLD-LOW-HTF).

    All lookups are keyed by candidate id.  A missing key means "not
    observable" — preferences needing it become inapplicable (never default).
    """

    test_history: Dict[str, List[dict]] = field(default_factory=dict)
    ref_kind: Dict[str, str] = field(default_factory=dict)
    round_cluster: Dict[str, bool] = field(default_factory=dict)

    def test_bars(self, cid: str) -> List[dict]:
        return list(self.test_history.get(cid, ()))


# ---------------------------------------------------------------------------
# Licensed comparisons (preference rules).  Each rule is a pure function over
# two evidence maps; it returns True (left preferred), False (right
# preferred) or None (comparison not licensed / evidence missing).
# ---------------------------------------------------------------------------

def _rule_tested(left: dict, right: dict) -> Optional[bool]:
    lt = bool(left.get("test_history"))
    rt = bool(right.get("test_history"))
    if lt == rt:
        return None
    return lt          # tested wins iff exactly one side is tested


def _rule_old_htf(left: dict, right: dict) -> Optional[bool]:
    indicated = {"old-low-htf", "old-high-reclaimed"}
    lk = left.get("ref_kind")
    rk = right.get("ref_kind")
    l_in = lk in indicated
    r_in = rk in indicated
    if l_in == r_in:
        return None
    return l_in


def _rule_cluster(left: dict, right: dict) -> Optional[bool]:
    lc = left.get("round_cluster") is True
    rc = right.get("round_cluster") is True
    if lc == rc:
        return None
    return lc


_LICENSE_RULES: Dict[str, Callable[[dict, dict], Optional[bool]]] = {
    "tested>untested": _rule_tested,
    "old-low-htf>other": _rule_old_htf,
    "cluster>non-cluster": _rule_cluster,
}


# ---------------------------------------------------------------------------
# Output types (task §5 contract)
# ---------------------------------------------------------------------------

OUTCOME_SELECTED = "SELECTED"
OUTCOME_UNRESOLVED = "UNRESOLVED"


@dataclass
class ExpertSelection:
    """SELECTED(candidate_id, evidence) or UNRESOLVED(reason, survivors).

    ``base_result`` is the kernel's own ``SelectionResult`` produced through
    the existing T-S1 path — the carrier of revision dependencies, policy
    snapshots and dependent-conclusion bookkeeping (task §6.10).
    """

    outcome: str
    task_id: str
    task_name: str
    decision_bar: int
    decision_time: Optional[pd.Timestamp]
    representation_id: str
    candidate_id: Optional[str]
    evidence: List[EvidenceItem]
    reason: Optional[dict]             # {"code", "text", "evidence_needed"}
    surviving_candidate_ids: List[str]
    excluded: List[Exclusion]
    activated_preferences: List[dict]
    inactive_preferences: List[dict]
    conflicts: List[dict]
    base_result: SelectionResult
    interpretation: Optional[dict]
    provenance: List[str]
    policy_snapshots: Dict[str, dict]

    # ---- task §5 convenience views ------------------------------------
    @property
    def selected_id(self) -> Optional[str]:
        return self.candidate_id

    @property
    def is_selected(self) -> bool:
        return self.outcome == OUTCOME_SELECTED

    def to_record(self) -> dict:
        """Serializable record (deterministic key order; replay-comparable)."""
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
            "base_status": self.base_result.status,
            "base_selected_id": self.base_result.selected_id,
            "dependencies": list(self.base_result.dependencies),
            "dependents": list(self.base_result.dependents),
            "direction": self.base_result.direction,
            "notes": list(self.base_result.notes),
        }

    def ledger_payload(self, *, run_id: str = "",
                       points: Optional[Sequence[PointCandidate]] = None,
                       legs: Optional[Sequence[LegCandidate]] = None) -> dict:
        """Payload for ``InterpretationLedger.record(base_result, payload)`` —
        real recomputation inputs (task §6.10: revision dependencies through
        EXISTING project mechanisms; audit D5: the payload carries the task
        kind and its actual inputs so ``propagate()`` can recompute)."""
        return {
            "kind": "expert_structural_reference_selection",
            "run_id": run_id,
            "points": list(points or ()),
            "legs": list(legs or ()),
            "expert_outcome": self.outcome,
            "selected_id": self.candidate_id,
            "survivors": list(self.surviving_candidate_ids),
            "activated_preferences": self.activated_preferences,
            "conflicts": self.conflicts,
            "depends_on_results": [],
        }


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------

def _evidence_for(cid: str, c: PointCandidate, legs: Sequence[LegCandidate],
                  decision_bar: int,
                  decision_time: Optional[pd.Timestamp],
                  rel: ContextualRelationships) -> List[EvidenceItem]:
    """Observable evidence per candidate (all F/S class; no derived scores)."""
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
    # leg role (F): which legs this point anchors
    anchored = [l.leg_id for l in legs
                if getattr(l, "start_id", None) == cid
                or getattr(l, "end_id", None) == cid]
    if anchored:
        items.append(EvidenceItem("leg_role", CLASS_F, anchored, "R:SP-14",
                                  "endpoint of these legs"))
    # same-bar ambiguity (F)
    if getattr(c, "same_bar_order", "resolved") != "resolved":
        items.append(EvidenceItem(
            "same_bar_ambiguity", CLASS_F,
            {"order": c.same_bar_order,
             "evidence_class": same_bar_evidence_class(c.same_bar_evidence)},
            "F:endpoints", "audit D4 ambiguity record"))
    # relationship evidence (consumed, never invented here).
    # Contract: an OBSERVED fact is recorded even when its value is empty /
    # False (observed-no-tests ≠ not-observed); a missing key means the fact
    # was never observable for this candidate.
    if cid in rel.test_history:
        items.append(EvidenceItem("test_history", CLASS_F,
                                  list(rel.test_bars(cid)),
                                  "R:test-history",
                                  "prior close-crossing bindings / exact "
                                  "range touches (F-class interval facts); "
                                  "empty list = observed, no tests"))
    rk = rel.ref_kind.get(cid)
    if rk is not None:
        items.append(EvidenceItem("ref_kind", CLASS_S, rk,
                                  "S:REF-OLD-LOW-HTF",
                                  "upstream-declared reference kind (P1)"))
    rc = rel.round_cluster.get(cid)
    if rc is not None:
        items.append(EvidenceItem("round_cluster", CLASS_S, rc,
                                  "S:SRC-OSLER-SR150",
                                  "upstream-declared cluster marker"))
    return items


def _evidence_maps(items_by_id: Dict[str, List[EvidenceItem]]
                   ) -> Dict[str, dict]:
    maps: Dict[str, dict] = {}
    for cid, items in items_by_id.items():
        m: dict = {}
        for it in items:
            if it.name == "test_history":
                m["test_history"] = list(it.value or [])
            elif it.name == "ref_kind":
                m["ref_kind"] = it.value
            elif it.name == "round_cluster":
                m["round_cluster"] = it.value
        maps[cid] = m
    return maps


def apply_expert_preferences(
        survivor_ids: Sequence[str],
        evidence_maps: Dict[str, dict],
        knowledge: Sequence[ExpertPreference] = EXPERT_KNOWLEDGE_SRS_V1,
        *,
        scene: Optional[dict] = None,
) -> Tuple[List[dict], List[dict], List[dict], Optional[str], dict]:
    """Apply documented conditional preferences over the survivor set.

    Returns ``(activated, inactive, conflicts, winner_or_None, diagnostics)``.

    Resolution discipline (task §6.5–§6.7):
      * a comparison is licensed ONLY when its preference's observable
        evidence is present on both sides in the documented shape;
      * contradictory licensed comparisons for one pair are PRESERVED as
        conflicts (task §7) and resolve nothing;
      * a unique candidate is returned only when it wins at least one
        licensed comparison and loses none;
      * otherwise nothing is selected — the caller emits UNRESOLVED.
    """
    scene = scene or {}
    activated: List[dict] = []
    inactive: List[dict] = []
    conflicts: List[dict] = []
    ids = list(survivor_ids)

    for pref in knowledge:
        if pref.kclass == KCLASS_F:
            inactive.append({"pref_id": pref.pref_id,
                             "cause": "F-class: unresolved expert hypothesis "
                                      "— never binding (task §4)"})
            continue
        if pref.licenses == "none":
            inactive.append({"pref_id": pref.pref_id,
                             "cause": "task-conditioning/constraint record: "
                                      "licenses no candidate comparison"})
            continue
        rule = _LICENSE_RULES.get(pref.licenses)
        if rule is None:  # pragma: no cover — registry integrity
            raise ValueError(f"unknown license rule {pref.licenses!r}")
        # observable-evidence presence per survivor: the fact must be
        # OBSERVED (key present) — an observed negative value counts; a
        # missing key means "not observable" and the candidate is left out
        # of this preference's comparisons (never defaulted).
        present = [cid for cid in ids
                   if all(k in evidence_maps.get(cid, {})
                          for k in pref.observable_evidence)]
        if not present:
            inactive.append({
                "pref_id": pref.pref_id,
                "cause": f"observable evidence {pref.observable_evidence} "
                         f"absent on all survivors — preference inapplicable "
                         f"(never a default)"})
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
                         "comparison shape — no comparison licensed"})
            continue
        activated.append({"pref_id": pref.pref_id, "pairs": pref_pairs,
                          "source": pref.source, "klass": pref.klass})

    # ---- conflict preservation (task §7) -------------------------------
    pair_dir: Dict[Tuple[str, str], List[str]] = {}
    for act in activated:
        for pr in act["pairs"]:
            key = tuple(sorted((pr["winner"], pr["loser"])))
            pair_dir.setdefault(key, []).append(pr["pref_id"])
    winners_lose: Dict[str, List[str]] = {cid: [] for cid in ids}
    for act in activated:
        for pr in act["pairs"]:
            winners_lose.setdefault(pr["loser"], []).append(pr["pref_id"])
    # two preferences preferring opposite members of one pair -> conflict
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
    diagnostics = {
        "clean_wins": clean_wins,
        "clean_losses": clean_losses,
        "preferred": preferred,
        "n_conflicts": len(conflicts),
    }
    return activated, inactive, conflicts, winner, diagnostics


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
    """Run expert-grounded STRUCTURAL_REFERENCE_SELECTION on one frozen scene.

    Pipeline (task §6, in order):
      1-2. retrieve candidates + existing eligibility gates  -> kernel T-S1
      3.   identify task-relevant evidence                   -> _evidence_for
      4.   apply documented conditional preferences          -> apply_expert_preferences
      5-6. resolve only evidence-supported comparisons;
            preserve unresolved comparisons / conflicts
      7-8. emit SELECTED or UNRESOLVED with evidence + source provenance
      9.   continue one compatible structural interpretation where supported
      10.  preserve revision dependencies via SelectionResult/ledger payloads

    No largest/nearest/newest/prominence default exists anywhere in this
    function (task §5): with no declared role policy and no applicable
    evidence, the honest output is UNRESOLVED.
    """
    rel = relationships or ContextualRelationships()
    eff_role = role if role is not None else EXPERT_ROLE_UNDECLARED

    # ---- steps 1-2: EXISTING gates + role semantics (kernel T-S1) ------
    base = task_s1_structural_reference(
        points, legs, decision_bar, rep, eff_role, policy,
        policy_id=policy_id, allow_provisional=allow_provisional,
        state_id_prefix=state_id_prefix, decision_time=decision_time,
        axis=axis)

    by_id = {p.candidate_id: p for p in points}
    survivor_objs = [by_id[cid] for cid in base.survivors if cid in by_id]

    # ---- step 3: task-relevant evidence -------------------------------
    items_by_id = {
        p.candidate_id: _evidence_for(p.candidate_id, p, legs, decision_bar,
                                      decision_time, rel)
        for p in survivor_objs}
    maps = _evidence_maps(items_by_id)

    scene = {"task_id": SRS_TASK_ID, "role": role,
             "has_declared_policy": policy_id is not None}
    activated, inactive, conflicts, pref_winner, diag = apply_expert_preferences(
        base.survivors, maps, knowledge, scene=scene)

    prov = list(base.provenance) + [
        "X:expert-selection-v1",
        "F:knowledge=%s" % "+".join(p.pref_id for p in knowledge)]
    psnaps: Dict[str, dict] = dict(base.policy_snapshots)
    psnaps["expert_layer"] = {
        "policy_id": "expert-selection-v1", "version": 1,
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

    # ---- outcome assembly ---------------------------------------------
    if base.is_justified:
        # Declared Pi_T role semantics resolved the task (documented
        # precedence, PI_T_PRECEDENCE_DOC).  Contradicting source-grounded
        # preferences are preserved as tensions — never silently applied.
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
            "view": rep.view_id,
            "reference": cid,
            "role": role,
            "direction": base.direction,
            "state": "reference-active",
            "conditional_on": [PI_T_PRECEDENCE_DOC]
            + [a["pref_id"] for a in activated],
            "dependents": list(base.dependents),
            "revision_dependencies": list(base.dependencies),
        }
        return ExpertSelection(
            outcome=OUTCOME_SELECTED, task_id=SRS_TASK_ID,
            task_name=SRS_TASK_NAME, decision_bar=decision_bar,
            decision_time=decision_time, representation_id=rep.rep_id,
            candidate_id=cid, evidence=_evidence_chain(cid), reason=None,
            surviving_candidate_ids=list(base.survivors),
            excluded=list(base.excluded),
            activated_preferences=activated, inactive_preferences=inactive,
            conflicts=conflicts, base_result=base,
            interpretation=interpretation,
            provenance=prov, policy_snapshots=psnaps)

    # gate-blocked states (IC/AI/...) — preferences never override gates
    if base.unresolved is not None and base.unresolved.reason_code != REASON_MP:
        return ExpertSelection(
            outcome=OUTCOME_UNRESOLVED, task_id=SRS_TASK_ID,
            task_name=SRS_TASK_NAME, decision_bar=decision_bar,
            decision_time=decision_time, representation_id=rep.rep_id,
            candidate_id=None,
            evidence=[e for cid in base.survivors
                      for e in items_by_id.get(cid, ())],
            reason={"code": base.unresolved.reason_code,
                    "text": base.unresolved.evidence_needed,
                    "evidence_needed": base.unresolved.evidence_needed},
            surviving_candidate_ids=list(base.survivors),
            excluded=list(base.excluded),
            activated_preferences=activated, inactive_preferences=inactive,
            conflicts=conflicts, base_result=base, interpretation=None,
            provenance=prov, policy_snapshots=psnaps)

    # MP state with survivors: the expert layer may resolve by documented
    # conditional preferences (task §6.4-7) — or remain unresolved honestly.
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
                                     "between the conflicting preferences "
                                     "(file 18 objective B/C) or a declared "
                                     "Pi_T policy (SP-18)"}
    elif pref_winner is not None:
        cid = pref_winner
        interpretation = {
            "kind": "T-S1-structural-interpretation",
            "view": rep.view_id,
            "reference": cid,
            "role": role,
            "direction": base.direction,
            "state": "reference-active",
            "conditional_on": [a["pref_id"] for a in activated],
            "dependents": list(base.dependents),
            "revision_dependencies": list(base.dependencies),
        }
        prov2 = prov + [
            "R:preference-resolution(%s)"
            % ",".join(a["pref_id"] for a in activated)]
        return ExpertSelection(
            outcome=OUTCOME_SELECTED, task_id=SRS_TASK_ID,
            task_name=SRS_TASK_NAME, decision_bar=decision_bar,
            decision_time=decision_time, representation_id=rep.rep_id,
            candidate_id=cid, evidence=_evidence_chain(cid), reason=None,
            surviving_candidate_ids=survivors, excluded=list(base.excluded),
            activated_preferences=activated, inactive_preferences=inactive,
            conflicts=conflicts, base_result=base,
            interpretation=interpretation, provenance=prov2,
            policy_snapshots=psnaps)
    else:
        if activated and len(diag["preferred"]) != 1:
            code, text = (REASON_EP,
                          "documented preferences apply but do not uniquely "
                          "order the survivors (preferred: %s)"
                          % diag["preferred"])
            needed = ("comparative evidence between the surviving "
                      "candidates (file 18 objective B) or a declared Pi_T "
                      "policy (SP-18)")
        else:
            code, text = (REASON_MP,
                          "no declared role policy and no applicable "
                          "source-grounded preference with observable "
                          "evidence")
            needed = ("declare a Pi_T role policy (SP-18) + SP-12 "
                      "sensitivity, or supply observable relationship "
                      "evidence (test history / declared reference kind / "
                      "declared cluster marker)")
        reason = {"code": code, "text": text, "evidence_needed": needed}

    return ExpertSelection(
        outcome=OUTCOME_UNRESOLVED, task_id=SRS_TASK_ID,
        task_name=SRS_TASK_NAME, decision_bar=decision_bar,
        decision_time=decision_time, representation_id=rep.rep_id,
        candidate_id=None,
        evidence=[e for cid in survivors
                  for e in items_by_id.get(cid, ())],
        reason=reason,
        surviving_candidate_ids=survivors, excluded=list(base.excluded),
        activated_preferences=activated, inactive_preferences=inactive,
        conflicts=conflicts, base_result=base, interpretation=None,
        provenance=prov, policy_snapshots=psnaps)
