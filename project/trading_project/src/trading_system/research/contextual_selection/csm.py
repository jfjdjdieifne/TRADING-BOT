"""CSM core: model, generators, seed procedures, task cards, ledger.

Claim references (knowledge_foundation, jfjdjdieifne/test @ 6c8bf6fd):
CSM-*, SWS-*, SP-*, LRN-* — see files 15-18.  This module implements the
deterministic, non-learned subset (file 18 §18.9: SP-01..SP-20, unresolved
emission, dependency-aware recomputation are implementable without learning).

AUDIT REMEDIATION (contextual-selection V1 audit of commit 4e04198) — this
revision patches only the confirmed defects; no new market model, swing
family, learning algorithm, or strategy is introduced:

  D1 cross-timeframe future leakage  -> shared information-time axis
     (occurrence_time/knowable_time; cross-view queries compare timestamps
     only; reference_state_at() serves chronological event replay)
  D2 F-K premature confirmation     -> complete confirmation window with
     inclusive supersession endpoint, full left-context requirement
  D3 mutable status rewrites past   -> StatusTransition history + status_at()
  D4 same-bar / equal-extreme ties  -> explicit same-bar ambiguity records,
     no zero-duration directional legs, versioned tie policies
  D5 fake propagation               -> InterpretationLedger recomputes
     dependents from stored inputs and records computed differences
  D6 direction/depth/coverage       -> structural direction on results,
     fixed T-S3 depth, candidate_record() serializable coverage evidence
  D7 policy & provenance            -> PolicyRegistry kinds (research
     configuration is never owner-approved); run provenance records the
     actual source version (experiment script, not this module).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

# Reuse of the CLOSED 6.2A-0 information-time contract (read-only):
from trading_system.research.information_time import (  # noqa: F401
    InformationKey,
    InformationKeyError,
    InformationPhase,
    TimeIndexedTimelineAdapter,
)

# --------------------------------------------------------------------------
# CSM vocabulary (file 15 §15.3, §15.5, §15.7)
# --------------------------------------------------------------------------

CLASS_F = "F"  # factual
CLASS_O = "O"  # operational policy
CLASS_S = "S"  # source-declared
CLASS_L = "L"  # learned (never produced here)
CLASS_U = "U"  # unknown

# Policy kinds (audit §8: never promote research configuration to owner policy)
KIND_RESEARCH = "research_configuration"
KIND_AUTHORIZED = "authorized_analytical_policy"      # owner-approved (none here)
KIND_FACTUAL = "factual_calculation"
KIND_SOURCE = "ict_source_interpretation"
KIND_PROCEDURE = "source_declared_procedure"          # knowledge-foundation rules
POLICY_KINDS = (KIND_RESEARCH, KIND_AUTHORIZED, KIND_FACTUAL, KIND_SOURCE,
                KIND_PROCEDURE)

REASON_MO = "MO"    # missing market observation
REASON_MP = "MP"    # missing operational policy
REASON_AI = "AI"    # ambiguous ICT interpretation
REASON_IC = "IC"    # insufficient contextual evidence
REASON_EP = "EP"    # empirical preference not yet learned
REASON_OOD = "OOD"  # out of distribution

X_KNOW = "X-KNOW"
X_SCALE = "X-SCALE"
X_SUPER = "X-SUPER"
X_STATE = "X-STATE"
X_GEOM = "X-GEOM"
X_DOM = "X-DOM"
X_POL = "X-POL"
EXCLUSION_CODES = (X_KNOW, X_SCALE, X_SUPER, X_STATE, X_GEOM, X_DOM, X_POL)

STATUS_CONFIRMED = "confirmed"
STATUS_PROVISIONAL = "provisional"
STATUS_SUPERSEDED = "superseded"
STATUS_BROKEN = "broken"          # structural break fact (audit D5/D6)

# Versioned tie policies (audit D4): every tie break must name its policy.
TIE_FT_EQ_FIRST = "TIE-FT-EQ-FIRST-V1"   # keep first equal extreme (default)
TIE_FT_EQ_LAST = "TIE-FT-EQ-LAST-V1"     # explicit alternative (never implicit)
TIE_BOUNDARIES = "TIE-BOUNDARIES-INCLUSIVE-V1"
TIE_CROSS_EQUAL_UNBOUND = "TIE-CROSS-EQUAL-UNBOUND-V1"  # equality not a crossing
TIE_CROSS_EQUAL_BOUND_V1 = "TIE-CROSS-EQUAL-BOUND-V1"    # equality IS a crossing
TIE_CROSS_POLICIES = (TIE_CROSS_EQUAL_UNBOUND, TIE_CROSS_EQUAL_BOUND_V1)

# ---- END-TO-END CONSOLIDATION V1 (independent audit of 312163a) ----------
# Explicit event phases (task §3): a historical binding is evaluated against
# PRE_EVENT_STATE; the event's own transition never rewrites it.
PHASE_PRE_EVENT = "PRE_EVENT_STATE"
PHASE_BINDING = "EVENT_BINDING"
PHASE_POST_EVENT = "POST_EVENT_STATE"


# --------------------------------------------------------------------------
# Core records
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Representation:
    """family + scale + parameters + causal mode (file 15 §15.1)."""

    family: str            # "F-K" | "F-T" | "F-C"
    view_id: str           # e.g. "C" (coarse), "F" (fine)
    scale_label: str       # "coarse" | "fine" | ...
    params: Tuple[Tuple[str, float], ...]  # declared policy slots, frozen

    def __post_init__(self) -> None:
        if self.family not in ("F-K", "F-T", "F-C"):
            raise ValueError(f"unknown family {self.family!r}")

    @property
    def rep_id(self) -> str:
        p = ",".join(f"{k}={v:g}" for k, v in self.params)
        return f"{self.view_id}:{self.family}({p})"

    def param(self, name: str) -> float:
        for k, v in self.params:
            if k == name:
                return v
        raise KeyError(name)


@dataclass
class PropertyRecord:
    """Every property carries its class (file 15 §15.3)."""

    name: str
    klass: str
    value: object
    source_ref: Optional[str] = None  # e.g. "R:SP-01", "P1:OB-transcript", "O:P-ORIGIN"

    def __post_init__(self) -> None:
        if self.klass not in (CLASS_F, CLASS_O, CLASS_S, CLASS_L, CLASS_U):
            raise ValueError(f"bad property class {self.klass!r}")


@dataclass(frozen=True)
class StatusTransition:
    """Append-only status transition with its information time (audit D3).

    A transition becomes knowable at ``info_bar`` / ``info_time``; historical
    queries must use ``status_at()`` and never the mutable final field.
    """

    info_bar: int
    status: str
    info_time: Optional[pd.Timestamp] = None
    by: Optional[str] = None      # e.g. candidate id that superseded this one
    note: str = ""
    # authorizing EVENT reference (consolidation V1): the recorded event this
    # transition implements.  Pre-event state queries exclude the event's own
    # transitions so applying an event never rewrites its own binding.
    event_ref: Optional[str] = None


@dataclass
class PointCandidate:
    """L1 turning-point candidate (file 16 §16.2)."""

    candidate_id: str
    rep: Representation
    side: str                 # "high" | "low"
    occurrence_bar: int
    level: float
    knowable_bar: int
    status: str = STATUS_CONFIRMED
    superseded_by: Optional[str] = None
    properties: List[PropertyRecord] = field(default_factory=list)
    # --- audit D1: shared information-time axis (same domain as the bars) ---
    occurrence_time: Optional[pd.Timestamp] = None
    knowable_time: Optional[pd.Timestamp] = None
    # --- audit D3: status history (append-only; `status` is the final field) ---
    status_transitions: List[StatusTransition] = field(default_factory=list)
    # --- audit D4: "unresolved" when same-bar high/low order is unknowable ---
    same_bar_order: str = "resolved"   # "resolved" | "unresolved"
    # factual (CLASS_F) OHLC-endpoint evidence that DOES determine the
    # intrabar order ("high-first" | "low-first") even when the generator
    # cannot order the bar: e.g. an open at the extreme.  None = no evidence.
    same_bar_evidence: Optional[str] = None
    initial_status: str = ""           # status at construction (D3 history)

    def __post_init__(self) -> None:
        if not self.initial_status:
            self.initial_status = self.status

    @property
    def view_id(self) -> str:
        return self.rep.view_id

    def add_transition(self, info_bar: int, status: str,
                       info_time: Optional[pd.Timestamp] = None,
                       by: Optional[str] = None, note: str = "",
                       event_ref: Optional[str] = None) -> None:
        self.status_transitions.append(
            StatusTransition(info_bar=info_bar, status=status,
                             info_time=info_time, by=by, note=note,
                             event_ref=event_ref))
        self.status = status  # final-field mirror for callers that read it

    def status_at(self, info_bar: Optional[int] = None,
                  info_time: Optional[pd.Timestamp] = None,
                  excluding_event_ref: Optional[str] = None) -> str:
        """Reconstruct the status knowable at the requested boundary (D3).

        END-TO-END CONSOLIDATION V1: a TIME-based query NEVER falls back to a
        bar index — a transition without ``info_time`` is unplaceable on the
        time axis and is not applied (a bar index from another domain must
        not give it meaning).  The bar axis is consulted only for bar-only
        queries (single declared domain).

        ``excluding_event_ref`` reconstructs the PRE_EVENT_STATE: the
        transitions authorized by the excluded event itself are omitted, so
        applying an event's own break never rewrites that event's binding
        (first-break stays first-break on replay).

        Falls back to the final ``status`` field when no transition history
        exists (hand-built candidates); later supersession recorded as a
        transition never rewrites the earlier provisional state.
        """
        if not self.status_transitions:
            return self.status
        applicable = []
        for t in self.status_transitions:
            if excluding_event_ref is not None and t.event_ref == excluding_event_ref:
                continue                          # the event's own transition
            if info_time is not None:
                if t.info_time is not None:
                    if t.info_time > info_time:
                        continue                  # time axis governs
                else:
                    # unplaceable on the time axis: never borrow a foreign
                    # domain's bar index (consolidation V1, audit D4)
                    continue
            elif info_bar is not None:
                if t.info_bar > info_bar:
                    continue                      # single-domain bar axis
            applicable.append(t)
        # queried before the first recorded transition: the constructed state
        return applicable[-1].status if applicable else self.initial_status


@dataclass
class LegCandidate:
    """L2 leg: ordered pair of consecutive alternating points (SP-14)."""

    leg_id: str
    rep: Representation
    start_id: str
    end_id: str
    direction: str            # "up" | "down"
    t0: int
    t1: int
    p_start: float
    p_end: float
    knowable_bar: int
    completed: bool = True
    # --- audit D1: shared information-time axis ---
    t0_time: Optional[pd.Timestamp] = None
    t1_time: Optional[pd.Timestamp] = None
    knowable_time: Optional[pd.Timestamp] = None

    @property
    def view_id(self) -> str:
        return self.rep.view_id

    @property
    def p_lo(self) -> float:
        return min(self.p_start, self.p_end)

    @property
    def p_hi(self) -> float:
        return max(self.p_start, self.p_end)

    @property
    def low_id(self) -> str:
        return self.start_id if self.p_start <= self.p_end else self.end_id

    @property
    def high_id(self) -> str:
        return self.end_id if self.p_start <= self.p_end else self.start_id

    @property
    def depth(self) -> float:
        """Absolute price travel of the leg (audit D6: factual depth)."""
        return abs(self.p_start - self.p_end)


@dataclass
class Exclusion:
    candidate_id: str
    code: str
    rule_ref: str
    detail: str = ""

    def __post_init__(self) -> None:
        if self.code not in EXCLUSION_CODES:
            raise ValueError(f"bad exclusion code {self.code!r}")


@dataclass
class UnresolvedState:
    """Schema of file 19 §19.1."""

    state_id: str
    task: str
    decision_bar: int
    survivors: List[str]
    excluded: List[Exclusion]
    reason_code: str
    evidence_needed: str
    policy_refs: List[str]
    provenance: List[str]
    dependents_blocked: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.reason_code not in (REASON_MO, REASON_MP, REASON_AI, REASON_IC, REASON_EP, REASON_OOD):
            raise ValueError(f"bad reason code {self.reason_code!r}")


@dataclass
class SelectionResult:
    task_id: str
    decision_bar: int
    status: str                       # "justified" | "unresolved" | "empty" | "falsified"
    selected_id: Optional[str]
    survivors: List[str]
    excluded: List[Exclusion]
    unresolved: Optional[UnresolvedState]
    provenance: List[str]
    policy_refs: List[str]
    representation_id: str
    dependents: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    # --- audit D6: structural direction (never mined from note strings) ---
    direction: Optional[str] = None
    # --- audit D5: explicit dependency references for real propagation ---
    dependencies: List[str] = field(default_factory=list)
    # --- audit D1: information time of the decision (optional) ---
    decision_time: Optional[pd.Timestamp] = None
    # --- causal-state integration V1: T-S2 pre-event lifecycle tags ---
    # bound reference -> "first-break" | "later-interaction" (|"provisional:")
    binding_kinds: Dict[str, str] = field(default_factory=dict)
    # --- consolidation V1 (task §3): explicit event phases -------------
    # {PRE_EVENT_STATE: {cid: status}, EVENT_BINDING: {bound, binding_kinds},
    #  POST_EVENT_STATE: {cid: authorized status}}
    event_phase: Optional[dict] = None
    # --- consolidation V1 (task §4): exact policy identity/version/values
    # captured when this result was produced — later registry mutation can
    # never change the historical meaning of this result.
    policy_snapshots: Dict[str, dict] = field(default_factory=dict)

    @property
    def is_justified(self) -> bool:
        return self.status == "justified"


@dataclass(frozen=True)
class TaskCard:
    """File 15 §15.1 / file 16 §16.3."""

    task_id: str
    question: str
    role: str
    hard_requirements: Tuple[str, ...]
    exclusion_rules: Tuple[str, ...]
    comparison_basis: Tuple[str, ...]
    policy_id: Optional[str]      # Pi_T; None means "no declared policy"
    requires_single: bool = False


class PolicyRegistry:
    """SP-18: declared policy registry.  Every O-class choice is recorded here.

    Audit D7 (§8): every entry carries a ``kind``; research configuration is
    never presented as an owner-approved analytical policy.  Entries without
    an explicit kind default to KIND_RESEARCH.

    END-TO-END CONSOLIDATION V1 (task §4): entries are VERSIONED and
    immutable per version.  Re-registering a policy id creates a NEW version
    (v2, v3, ...); earlier results hold ``policy_snapshots`` of the exact
    identity/version/values used at creation, so a registry mutation can
    never silently change their historical meaning.  ``ref()`` names the
    version explicitly.
    """

    def __init__(self) -> None:
        self._entries: Dict[str, dict] = {}

    def register(self, policy_id: str, description: str, value: object,
                 sensitivity_required: bool = True,
                 kind: str = KIND_RESEARCH) -> None:
        if kind not in POLICY_KINDS:
            raise ValueError(f"bad policy kind {kind!r}")
        prev = self._entries.get(policy_id)
        version = 1 if prev is None else prev["version"] + 1
        self._entries[policy_id] = {
            "policy_id": policy_id,
            "version": version,
            "description": description,
            "value": value,
            "class": CLASS_O,
            "kind": kind,
            "sensitivity_required": sensitivity_required,
        }

    def ref(self, policy_id: str) -> str:
        if policy_id not in self._entries:
            raise KeyError(f"policy {policy_id!r} not registered (SP-18)")
        return f"O:{policy_id}@v{self._entries[policy_id]['version']}"

    def get(self, policy_id: str) -> dict:
        return self._entries[policy_id]

    def snapshot_of(self, policy_id: str) -> dict:
        """Exact policy identity/version/effective values at call time
        (consolidation V1: results preserve their own policy meaning)."""
        if policy_id not in self._entries:
            raise KeyError(f"policy {policy_id!r} not registered (SP-18)")
        return dict(self._entries[policy_id])

    def items(self) -> Iterable[Tuple[str, dict]]:
        return self._entries.items()


# --------------------------------------------------------------------------
# Shared information-time axis (audit D1)
# --------------------------------------------------------------------------

def available_at(c: object, *,
                 as_of_bar: Optional[int] = None,
                 as_of_time: Optional[pd.Timestamp] = None,
                 axis: Optional["SharedInformationAxis"] = None) -> bool:
    """Availability of a candidate on a shared axis.

    Timestamps are the only axis allowed to cross view domains; bar indices
    are compared only inside one timeframe domain.  When both sides carry
    times, the time comparison governs (never raw cross-domain indices).
    A candidate with no recorded ``knowable_time`` under a time query is NOT
    available: an unverifiable availability is never claimed (this covers the
    truncated-prefix tail whose confirmation lies beyond the supplied bars).

    END-TO-END CONSOLIDATION V1: when a validated ``axis`` is supplied the
    comparison is KEY-VALIDATED (both times must resolve on the master
    timeline — an off-grid timestamp is explicit unavailability, never a raw
    float comparison).  Public task entry points REQUIRE the axis whenever
    time-bearing evidence is evaluated (``require_validated_asof``).
    """
    k_time = getattr(c, "knowable_time", None)
    if as_of_time is not None:
        if k_time is None:
            return False   # unverifiable on the time axis -> not available
        if axis is not None:
            return axis.available(k_time, as_of_time)
        return bool(k_time <= as_of_time)
    if as_of_bar is not None:
        return bool(getattr(c, "knowable_bar") <= as_of_bar)
    raise ValueError("availability requires a shared axis "
                     "(as_of_time with candidate knowable_time, or as_of_bar)")


def _time_bearing(*objs: object) -> bool:
    """True iff any evaluated object carries information-time evidence."""
    for o in objs:
        if o is None:
            continue
        seq = o if isinstance(o, (list, tuple, dict)) else (o,)
        if isinstance(o, dict):
            seq = [x for v in o.values() for x in (v if isinstance(v, (list, tuple)) else (v,))]
        for x in seq:
            if x is None or not hasattr(x, "__dict__") and not hasattr(x, "candidate_id") \
               and not hasattr(x, "leg_id") and not hasattr(x, "knowable_bar"):
                continue
            if getattr(x, "knowable_time", None) is not None:
                return True
            if getattr(x, "occurrence_time", None) is not None:
                return True
            if getattr(x, "t0_time", None) is not None or getattr(x, "t1_time", None) is not None:
                return True
    return False


def require_validated_asof(task_id: str, *,
                           axis: Optional["SharedInformationAxis"],
                           boundary_time: Optional[pd.Timestamp],
                           time_bearing: bool) -> None:
    """Unified information-time enforcement (consolidation V1, task §1).

    EVERY public task path routes its as-of evaluation through this gate:

    * time-bearing evidence (any input carries timestamps) REQUIRES the
      decision/event boundary on the shared time axis AND a validated axis —
      the call is rejected (ValueError) otherwise: no silent bypass.
    * a time boundary with no axis is likewise rejected.
    * pure bar-domain evidence (no times anywhere) keeps the single-domain
      bar contract unchanged.

    Missing essential evidence fails CLOSED (the call is refused) — never a
    bar-index fallback for time-bearing evidence.
    """
    if boundary_time is None and not time_bearing:
        return                       # pure bar-domain contract (one domain)
    if boundary_time is None:
        raise ValueError(
            f"{task_id}: time-bearing evidence requires the decision/event "
            f"boundary on the shared time axis (decision_time/event_time); "
            f"missing boundary is never replaced by a bar index")
    if axis is None:
        raise ValueError(
            f"{task_id}: validated as-of contract requires a shared "
            f"information-time axis (axis=...); raw timestamp comparison is "
            f"not a verified information-time claim")
    try:
        axis.key_for_time(boundary_time)
    except InformationKeyError as exc:
        raise ValueError(
            f"{task_id}: decision/event boundary {boundary_time} is not a "
            f"verified information time on axis {axis.timeline_id!r}: {exc}"
        ) from exc


def _endpoint_order(open_: float, high: float, low: float,
                    close: float) -> Optional[str]:
    """Factual OHLC-endpoint evidence (CLASS_F) for intrabar high/low order.

    ROOT-CAUSE REPAIR (same-bar ambiguity V1): endpoint evidence is now
    epistemically classified instead of overclaimed —

    * ``proven:…``   — the FIRST-TOUCH order is genuinely established by the
      data.  The open is the first traded price of the bar: an open at an
      extreme (strictly above/below the other extreme) proves that extreme
      was reached first.
    * ``constrained:…`` — the order is constrained but NOT unique.  A close
      at an extreme only proves that extreme's LAST touch is at the bar end;
      its FIRST touch may precede or follow the other extreme.
    * ``None`` — ordering unavailable (interior endpoints or flat bar).

    Only ``proven:`` evidence resolves the ambiguity; ``constrained:`` and
    missing evidence remain material.  This is a factual calculation, not a
    selection rule.
    """
    if not (high > low):
        return None                      # flat/degenerate bar: unavailable
    parts: List[str] = []
    order: Optional[str] = None
    if open_ == high and open_ != low:
        order = "high-first"
        parts.append("open-at-high")     # proven: first trade is the high
    elif open_ == low and open_ != high:
        order = "low-first"
        parts.append("open-at-low")      # proven: first trade is the low
    if close == high and close != low:
        parts.append("close-at-high")    # constrained: high touched last
    elif close == low and close != high:
        parts.append("close-at-low")     # constrained: low touched last
    if order is not None:
        return f"proven:{order}:" + "+".join(parts)
    if parts:
        return "constrained:" + "+".join(parts)
    return None


def same_bar_evidence_class(evidence: Optional[str]) -> str:
    """Epistemic class of same-bar endpoint evidence: 'proven' | 'constrained'
    | 'unavailable' (causal-state integration V1)."""
    if not evidence:
        return "unavailable"
    return "proven" if evidence.startswith("proven:") else "constrained"


def material_same_bar_ambiguity(c: object) -> bool:
    """True iff candidate ``c`` carries an unresolved intrabar order that the
    OHLC endpoints do NOT PROVE — the consequential case that must be
    surfaced on task results (never silently downgraded elsewhere).
    Constrained-but-not-unique evidence stays material; only proven ordering
    resolves the ambiguity."""
    if getattr(c, "same_bar_order", "resolved") != "unresolved":
        return False
    return same_bar_evidence_class(
        getattr(c, "same_bar_evidence", None)) != "proven"


def reference_state_at(selection_history: Sequence[Tuple[object, Sequence[object]]],
                       event_time: pd.Timestamp) -> List[object]:
    """Chronological retrieval for event replay (audit D1).

    ``selection_history`` is an ordered list of
    ``(available_time, reference_candidates)`` — one entry per frozen
    decision boundary, in increasing time order.  Returns the reference set
    of the LATEST state available at ``event_time`` (a selection produced at
    a later boundary can never apply to an earlier event), further filtered
    to references whose own ``knowable_time`` <= ``event_time``.
    """
    state: Sequence[object] = []
    for available_time, refs in selection_history:
        if available_time <= event_time:
            state = refs
        else:
            break
    return [r for r in state
            if getattr(r, "knowable_time", None) is not None
            and r.knowable_time <= event_time]


# --------------------------------------------------------------------------
# L1 generators (file 16 §16.2) — declared parameters only, causal, replay-safe
# --------------------------------------------------------------------------

# ---- causal-state integration V1 (root-cause repair) ----------------------
# Stable source/time identity + one verified shared information-time axis.
# Reuses the CLOSED 6.2A-0 contract (InformationKey / TimeIndexedTimelineAdapter)
# without modifying it.  Cross-timeline comparison is forbidden by that
# contract and raises; CSM therefore compares only keys built on ONE master
# timeline.

def stable_point_id(rep: "Representation", side: str, occurrence_bar: int,
                    occurrence_time: Optional[pd.Timestamp] = None,
                    id_prefix: str = "") -> str:
    """Source/time-based candidate identity (stable across replay windows).

    Local bar indices shift when the historical window changes; the source
    timestamp does not.  Bar indices remain as ``occurrence_bar`` metadata
    (single declared domain) but are never the identity when a time axis
    exists.  Distinct candidates at the same price but different occurrence
    times keep distinct identities.
    """
    if occurrence_time is not None:
        return (f"{id_prefix}{rep.rep_id}|{side}"
                f"@{pd.Timestamp(occurrence_time).isoformat()}")
    return f"{id_prefix}{rep.rep_id}|{side}@b{occurrence_bar}"


def stable_leg_id(rep: "Representation", start_bar: int, end_bar: int,
                  start_time: Optional[pd.Timestamp] = None,
                  end_time: Optional[pd.Timestamp] = None) -> str:
    if start_time is not None and end_time is not None:
        return (f"{rep.rep_id}|leg{pd.Timestamp(start_time).isoformat()}"
                f"-{pd.Timestamp(end_time).isoformat()}")
    return f"{rep.rep_id}|leg{start_bar}-{end_bar}"


_TS_MIN = pd.Timestamp(0)


def leg_recency_key(l: object) -> tuple:
    """Shared-axis recency ordering for legs (causal-state integration V1).

    Verified times govern; domain-local bar indices are only tiebreakers
    inside one declared domain.  Legs without verifiable times rank below
    time-bearing legs (an unverifiable recency is never preferred).
    """
    kt = getattr(l, "knowable_time", None)
    t1t = getattr(l, "t1_time", None)
    return (kt is not None, pd.Timestamp(kt) if kt is not None else _TS_MIN,
            t1t is not None, pd.Timestamp(t1t) if t1t is not None else _TS_MIN,
            getattr(l, "knowable_bar", -1), getattr(l, "t1", -1))


class SharedInformationAxis:
    """Minimal adapter over the CLOSED 6.2A-0 information-time contract.

    One market event gets one information-time identity on ONE master
    timeline (``TimeIndexedTimelineAdapter`` + ``InformationKey``).  Every
    cross-timeframe availability comparison must go through this axis;
    missing or off-grid times yield an explicit unavailability — never an
    invented timestamp and never a future-availability claim.
    """

    def __init__(self, timeline_id: str, master_index: "pd.DatetimeIndex"):
        idx = pd.DatetimeIndex(master_index)
        if idx.tz is None:
            # file convention (BTCUSDT mirror): timestamps are UTC
            idx = idx.tz_localize("UTC")
        self.timeline_id = timeline_id
        self._adapter = TimeIndexedTimelineAdapter(timeline_id)
        self._adapter.validate_index(idx)
        self._index = idx
        self._pos = {ts: i for i, ts in enumerate(idx)}

    @property
    def n_rows(self) -> int:
        return len(self._index)

    def key_for_time(self, t, phase=InformationPhase.COMPLETED_ROW_AVAILABLE,
                     deterministic_sequence: int = 0) -> "InformationKey":
        if t is None:
            raise InformationKeyError("no timestamp: no verified key")
        ts = pd.Timestamp(t)
        ts = ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")
        pos = self._pos.get(ts)
        if pos is None:
            raise InformationKeyError(f"time {ts} not on master timeline")
        return self._adapter.key_for_position(self._index, pos, phase,
                                              deterministic_sequence)

    def available(self, knowable_time, decision_time) -> bool:
        """Verified ``knowable <= decision`` on the shared axis.  False when
        either time is missing or not on the master grid (explicit
        unavailability)."""
        try:
            return (self.key_for_time(knowable_time)
                    <= self.key_for_time(decision_time))
        except InformationKeyError:
            return False


def fk_turning_points(bars: pd.DataFrame, k: int, rep: Representation,
                      id_prefix: str = "",
                      allow_short_left: bool = False,
                      tie_policy: str = TIE_FT_EQ_FIRST) -> List[PointCandidate]:
    """F-K k-bar pivot with causal confirmation (SP-13, SWS-04).

    Audit D2 fixes:
    - full left-side context required: a candidate registers only when the
      left window [i-k, i] is complete (``i >= k``); short left-edge windows
      are rejected unless the explicitly different policy slot
      ``allow_short_left`` is declared (recorded in provenance).
    - the complete confirmation window is checked BEFORE confirming: at bar
      i the SWS-04c supersession pass runs first (inclusive endpoint
      ``occurrence < j <= knowable_bar``), and only then are confirmations
      flushed.  A more extreme same-side point at the confirmation bar
      itself therefore supersedes instead of being beaten by a premature
      confirmation.
    - occurrence time and confirmation/availability time are preserved
      separately (``occurrence_bar``/``knowable_bar`` and, when the frame
      index supplies them, ``occurrence_time``/``knowable_time``).
    """
    if k < 1:
        raise ValueError("k must be >= 1 (declared policy slot, no default)")
    if tie_policy != TIE_FT_EQ_FIRST and not allow_short_left:
        # tie policy currently affects equal-extreme handling in F-T only;
        # accepted here for provenance symmetry without silent defaults.
        pass
    highs = bars["high"].to_numpy(dtype=float)
    lows = bars["low"].to_numpy(dtype=float)
    times = (bars.index.to_pydatetime() if isinstance(bars.index, pd.DatetimeIndex)
             else None)
    n = len(bars)
    out: List[PointCandidate] = []
    pending: List[PointCandidate] = []

    def _flush(upto_bar: int) -> None:
        for p in pending:
            if (p.status == STATUS_PROVISIONAL and p.knowable_bar <= upto_bar):
                p.add_transition(p.knowable_bar, STATUS_CONFIRMED,
                                 info_time=p.knowable_time, note="SWS-04b confirm")

    for i in range(n):
        # (1) registration needs the full left context (audit D2)
        if i < k and not allow_short_left:
            continue
        lo_i = max(0, i - k)
        window_h = highs[lo_i : i + 1]
        window_l = lows[lo_i : i + 1]
        is_high = (highs[i] == window_h.max()
                   and int((window_h == highs[i]).sum()) == 1)
        is_low = (lows[i] == window_l.min()
                  and int((window_l == lows[i]).sum()) == 1)
        new_cands: List[PointCandidate] = []
        for side, flag, level in (("high", is_high, float(highs[i])),
                                  ("low", is_low, float(lows[i]))):
            if not flag:
                continue
            occ_time = (pd.Timestamp(times[i]) if times is not None else None)
            # FINAL AUDIT PATCH (F-K tail knowability): a confirmation that
            # lies beyond the supplied bars gets NO knowable_time — the tail
            # must never claim the last observed timestamp as availability.
            know_time = (pd.Timestamp(times[i + k])
                         if (times is not None and i + k < n) else None)
            ev = None
            if is_high and is_low:
                row = bars.iloc[i]
                ev = _endpoint_order(float(row["open"]), float(row["high"]),
                                     float(row["low"]), float(row["close"]))
            cand = PointCandidate(
                candidate_id=stable_point_id(rep, side, i, occ_time, id_prefix),
                rep=rep,
                side=side,
                occurrence_bar=i,
                level=level,
                knowable_bar=i + k,
                status=STATUS_PROVISIONAL,
                occurrence_time=occ_time,
                knowable_time=know_time,
                same_bar_order="unresolved" if (is_high and is_low) else "resolved",
                same_bar_evidence=ev,
            )
            cand.add_transition(i, STATUS_PROVISIONAL, info_time=occ_time,
                                note="registered (SWS-04a)")
            new_cands.append(cand)
        # (2) SWS-04c supersession INSIDE the confirmation window, endpoint
        #     inclusive: occurrence < j <= knowable_bar (audit D2)
        for cand in new_cands:
            for p in pending:
                if (p.side == cand.side and p.status == STATUS_PROVISIONAL
                        and p.occurrence_bar < cand.occurrence_bar <= p.knowable_bar):
                    more_extreme = ((cand.level > p.level) if cand.side == "high"
                                    else (cand.level < p.level))
                    if more_extreme:
                        p.add_transition(cand.occurrence_bar, STATUS_SUPERSEDED,
                                         info_time=cand.occurrence_time,
                                         by=cand.candidate_id,
                                         note="SWS-04c supersede")
                        p.superseded_by = cand.candidate_id
        out.extend(new_cands)
        pending.extend(new_cands)
        # (3) confirmation flush AFTER supersession at this bar
        _flush(i)
    _flush(n - 1)  # nothing beyond the last observed bar may confirm
    return out


def ft_turning_points(bars: pd.DataFrame, tau: float, rep: Representation,
                      id_prefix: str = "",
                      tie_policy: str = TIE_FT_EQ_FIRST,
                      ambiguities: Optional[List[dict]] = None) -> List[PointCandidate]:
    """F-T threshold reversal (audit D4: ties and same-bar order explicit).

    - Equal-extreme ties never silently prefer the latest extreme: the
      default versioned policy ``TIE-FT-EQ-FIRST-V1`` keeps the first
      occurrence; ``TIE-FT-EQ-LAST-V1`` is available only when explicitly
      declared by the caller and is recorded on every emitted candidate.
    - A bar that would BOTH extend the running extreme AND complete a tau
      reversal from the previous extreme has an unknowable intrabar high/low
      order; no sequencing is synthesized.  The ambiguity is recorded in
      ``ambiguities`` (and the bar keeps the extreme tagged
      ``same_bar_order="unresolved"``).
    """
    if tau <= 0:
        raise ValueError("tau must be > 0 (declared policy slot, no default)")
    if tie_policy not in (TIE_FT_EQ_FIRST, TIE_FT_EQ_LAST):
        raise ValueError(f"unknown tie policy {tie_policy!r}")
    closes = bars["close"].to_numpy(dtype=float)
    highs = bars["high"].to_numpy(dtype=float)
    lows = bars["low"].to_numpy(dtype=float)
    times = (bars.index.to_pydatetime() if isinstance(bars.index, pd.DatetimeIndex)
             else None)
    n = len(bars)
    out: List[PointCandidate] = []
    ext_side: Optional[str] = None
    ext_i = 0
    ext_level = 0.0
    ext_order = "resolved"
    ext_ev: Optional[str] = None

    def _emit(i: int, side: str, occ_i: int, level: float, status: str,
              order: str, ev: Optional[str] = None) -> None:
        occ_time = (pd.Timestamp(times[occ_i]) if times is not None else None)
        know_time = (pd.Timestamp(times[i])
                     if (times is not None and 0 <= i < len(times)) else None)
        cand = PointCandidate(
            candidate_id=stable_point_id(rep, side, occ_i, occ_time, id_prefix),
            rep=rep, side=side, occurrence_bar=occ_i, level=level,
            knowable_bar=i, status=status,
            occurrence_time=occ_time, knowable_time=know_time,
            same_bar_order=order, same_bar_evidence=ev)
        cand.add_transition(occ_i, STATUS_PROVISIONAL, info_time=occ_time,
                            note=f"F-T registered (tie={tie_policy})")
        if status == STATUS_CONFIRMED:
            cand.add_transition(i, STATUS_CONFIRMED, info_time=know_time,
                                note="F-T reversal >= tau")
        out.append(cand)

    def _retire(occ_i: int, side: str, level: float, order: str,
                ev: Optional[str], by_id: str) -> None:
        """END-TO-END CONSOLIDATION V1 (task §6): a provisional running
        extreme displaced by a more extreme bar is RETAINED with its
        lifecycle (superseded, ``superseded_by`` set) — consistent with
        F-K's SWS-04c retention, and never silently discarded.  Retention
        is inventory bookkeeping only: superseded candidates are excluded
        from every selection path (X-SUPER) and from leg construction."""
        occ_time = (pd.Timestamp(times[occ_i]) if times is not None else None)
        cand = PointCandidate(
            candidate_id=stable_point_id(rep, side, occ_i, occ_time, id_prefix),
            rep=rep, side=side, occurrence_bar=occ_i, level=level,
            knowable_bar=occ_i, status=STATUS_SUPERSEDED,
            occurrence_time=occ_time, knowable_time=None,
            same_bar_order=order, same_bar_evidence=ev)
        cand.superseded_by = by_id
        cand.add_transition(occ_i, STATUS_PROVISIONAL, info_time=occ_time,
                            note=f"F-T registered (tie={tie_policy})")
        cand.add_transition(occ_i, STATUS_SUPERSEDED, info_time=occ_time,
                            by=by_id,
                            note="F-T provisional extreme displaced by a "
                                 "more extreme bar (retained)")
        out.append(cand)

    for i in range(n):
        if ext_side is None:
            ext_side, ext_i, ext_level = "high", i, float(highs[i])
            ext_order, ext_ev = "resolved", None
            continue
        if ext_side == "high":
            if tie_policy == TIE_FT_EQ_LAST:
                update = highs[i] >= ext_level
            else:
                update = highs[i] > ext_level  # TIE-FT-EQ-FIRST-V1
            reversal = ext_level - lows[i] >= tau
            if update and reversal:
                # same-bar both-sides: intrabar order unknowable (audit D4);
                # factual OHLC-endpoint evidence recorded when it determines
                row = bars.iloc[i]
                ev = _endpoint_order(float(row["open"]), float(row["high"]),
                                     float(row["low"]), float(row["close"]))
                if ambiguities is not None:
                    ambiguities.append({
                        "rep": rep.rep_id, "bar": i,
                        "kind": "same-bar-extreme-vs-reversal",
                        "side": "high", "prior_extreme_bar": ext_i,
                        "prior_extreme": ext_level, "high": float(highs[i]),
                        "low": float(lows[i]),
                        "open": float(row["open"]), "close": float(row["close"]),
                        "tie_policy": tie_policy,
                        "endpoint_evidence": ev,
                        "note": "OHLC cannot order the intrabar high/low; "
                                "no sequence synthesized",
                    })
                _retire(ext_i, "high", ext_level, ext_order, ext_ev,
                        stable_point_id(rep, "high", i,
                                        pd.Timestamp(times[i]) if times is not None else None,
                                        id_prefix))
                ext_side, ext_i, ext_level = "high", i, float(highs[i])
                ext_order, ext_ev = "unresolved", ev
                continue
            if update:
                _retire(ext_i, "high", ext_level, ext_order, ext_ev,
                        stable_point_id(rep, "high", i,
                                        pd.Timestamp(times[i]) if times is not None else None,
                                        id_prefix))
                ext_side, ext_i, ext_level = "high", i, float(highs[i])
                ext_order, ext_ev = "resolved", None
            elif reversal:
                _emit(i, "high", ext_i, ext_level, STATUS_CONFIRMED,
                      ext_order, ext_ev)
                ext_side, ext_i, ext_level = "low", i, float(lows[i])
                ext_order, ext_ev = "resolved", None
        else:
            if tie_policy == TIE_FT_EQ_LAST:
                update = lows[i] <= ext_level
            else:
                update = lows[i] < ext_level  # TIE-FT-EQ-FIRST-V1
            reversal = highs[i] - ext_level >= tau
            if update and reversal:
                row = bars.iloc[i]
                ev = _endpoint_order(float(row["open"]), float(row["high"]),
                                     float(row["low"]), float(row["close"]))
                if ambiguities is not None:
                    ambiguities.append({
                        "rep": rep.rep_id, "bar": i,
                        "kind": "same-bar-extreme-vs-reversal",
                        "side": "low", "prior_extreme_bar": ext_i,
                        "prior_extreme": ext_level, "high": float(highs[i]),
                        "low": float(lows[i]),
                        "open": float(row["open"]), "close": float(row["close"]),
                        "tie_policy": tie_policy,
                        "endpoint_evidence": ev,
                        "note": "OHLC cannot order the intrabar high/low; "
                                "no sequence synthesized",
                    })
                _retire(ext_i, "low", ext_level, ext_order, ext_ev,
                        stable_point_id(rep, "low", i,
                                        pd.Timestamp(times[i]) if times is not None else None,
                                        id_prefix))
                ext_side, ext_i, ext_level = "low", i, float(lows[i])
                ext_order, ext_ev = "unresolved", ev
                continue
            if update:
                _retire(ext_i, "low", ext_level, ext_order, ext_ev,
                        stable_point_id(rep, "low", i,
                                        pd.Timestamp(times[i]) if times is not None else None,
                                        id_prefix))
                ext_side, ext_i, ext_level = "low", i, float(lows[i])
                ext_order, ext_ev = "resolved", None
            elif reversal:
                _emit(i, "low", ext_i, ext_level, STATUS_CONFIRMED,
                      ext_order, ext_ev)
                ext_side, ext_i, ext_level = "high", i, float(highs[i])
                ext_order, ext_ev = "resolved", None
    if ext_side is not None:
        _emit(n + 1, ext_side, ext_i, ext_level, STATUS_PROVISIONAL,
              ext_order, ext_ev)
    return out


def build_legs(points: Sequence[PointCandidate], rep: Representation,
               completed_only: bool = False,
               ambiguities: Optional[List[dict]] = None) -> List[LegCandidate]:
    """SP-14 leg construction: consecutive alternating points.

    Audit D4: no zero-duration directional legs from invented intrabar
    sequencing — same-bar endpoint pairs (and equal-level pairs, whose
    direction cannot be established) are skipped and recorded as explicit
    same-bar/zero-amplitude ambiguities instead.
    """
    pts = [p for p in points if p.status != STATUS_SUPERSEDED]
    pts = sorted(pts, key=lambda p: (p.occurrence_bar, p.side, p.candidate_id))
    legs: List[LegCandidate] = []
    for a, b in zip(pts, pts[1:]):
        if a.side == b.side:
            continue
        if a.occurrence_bar == b.occurrence_bar:
            if ambiguities is not None:
                ambiguities.append({
                    "rep": rep.rep_id, "bar": a.occurrence_bar,
                    "kind": "same-bar-order-unresolved",
                    "pair": [a.candidate_id, b.candidate_id],
                    "endpoint_evidence": getattr(a, "same_bar_evidence", None),
                    "note": "OHLC cannot order same-bar high/low; no directional "
                            "zero-duration leg synthesized",
                })
            continue
        if a.level == b.level:
            if ambiguities is not None:
                ambiguities.append({
                    "rep": rep.rep_id, "bar": a.occurrence_bar,
                    "kind": "zero-amplitude-leg",
                    "pair": [a.candidate_id, b.candidate_id],
                    "note": "equal endpoints: direction not established",
                })
            continue
        direction = "up" if b.level > a.level else "down"
        # END-TO-END CONSOLIDATION V1 (audit D3): an endpoint without a
        # verifiable knowable_time leaves the leg's availability UNVERIFIABLE
        # — fail closed (knowable_time=None), never claimed from one side.
        kt_a = getattr(a, "knowable_time", None)
        kt_b = getattr(b, "knowable_time", None)
        know_time = (max(kt_a, kt_b)
                     if (kt_a is not None and kt_b is not None) else None)
        legs.append(LegCandidate(
            leg_id=stable_leg_id(rep, a.occurrence_bar, b.occurrence_bar,
                                 a.occurrence_time, b.occurrence_time),
            rep=rep,
            start_id=a.candidate_id, end_id=b.candidate_id,
            direction=direction,
            t0=a.occurrence_bar, t1=b.occurrence_bar,
            p_start=a.level, p_end=b.level,
            knowable_bar=max(a.knowable_bar, b.knowable_bar),
            completed=b.status == STATUS_CONFIRMED,
            t0_time=a.occurrence_time, t1_time=b.occurrence_time,
            knowable_time=know_time,
        ))
    if completed_only:
        legs = [l for l in legs if l.completed]
    return legs


# --------------------------------------------------------------------------
# Seed procedures (file 17)
# --------------------------------------------------------------------------

def _cid(c: object) -> str:
    return getattr(c, "candidate_id", None) or getattr(c, "leg_id")


def sp01_knowability(candidates: Sequence[object], decision_bar: Optional[int],
                     allow_provisional: bool = False,
                     as_of_time: Optional[pd.Timestamp] = None,
                     axis: Optional["SharedInformationAxis"] = None
                     ) -> Tuple[List[object], List[Exclusion]]:
    """SP-01 knowability with historical status reconstruction (audit D3).

    Status is evaluated via ``status_at(decision_bar, as_of_time)`` so a later
    supersession never rewrites the earlier provisional state of an as-of
    query.  ``allow_provisional`` is an explicit task-level policy: when the
    task does not support provisional references they get the explicit
    X-STATE exclusion (never silently treated as confirmed).
    """
    passed, excluded = [], []
    for c in candidates:
        occ_bar = getattr(c, "occurrence_bar", 0)
        occ_time = getattr(c, "occurrence_time", None)
        if as_of_time is not None and occ_time is not None:
            visible = occ_time <= as_of_time
        else:
            visible = (decision_bar is None) or (occ_bar <= decision_bar)
        if not visible:
            excluded.append(Exclusion(_cid(c), X_KNOW, "R:SP-01",
                                      f"occurrence {occ_bar} > t={decision_bar}"))
            continue
        st = c.status_at(decision_bar, as_of_time) if hasattr(c, "status_at") \
            else getattr(c, "status", STATUS_CONFIRMED)
        if st == STATUS_SUPERSEDED:
            excluded.append(Exclusion(_cid(c), X_SUPER, "R:SP-13/SWS-04c",
                                      "superseded inside confirmation window"))
        elif st == STATUS_BROKEN:
            excluded.append(Exclusion(_cid(c), X_STATE, "R:SP-20",
                                      "structural break recorded at/before t"))
        elif st == STATUS_PROVISIONAL:
            # provisional is visible at occurrence but its confirmed form is
            # not yet knowable (SP-13).  Default policy: explicit X-STATE
            # (SWS-04a; golden case W4) — never silently confirmed.
            if not allow_provisional:
                excluded.append(Exclusion(_cid(c), X_STATE, "R:SP-01/SWS-04a",
                                          "provisional not allowed by policy"))
            else:
                passed.append(c)
        else:
            if not available_at(c, as_of_bar=decision_bar,
                                as_of_time=as_of_time, axis=axis):
                excluded.append(Exclusion(_cid(c), X_KNOW, "R:SP-01",
                                          f"knowable_bar={getattr(c, 'knowable_bar', '?')} "
                                          f"> t={decision_bar}"))
            else:
                passed.append(c)
    return passed, excluded


def sp05_containment(coarse: LegCandidate, fine: LegCandidate,
                     tie_inclusive: bool = True) -> str:
    """SP-05: contained | escaping | disjoint.  Boundary tie rule is a declared
    policy (SWS-06; TIE-BOUNDARIES-INCLUSIVE-V1 default): inclusive spans.

    FINAL AUDIT PATCH (T-S3 cross-timeframe containment): time spans are
    compared on VERIFIED TIMESTAMPS whenever both legs carry them — raw bar
    indices from different timeframe domains are never compared.  A mixed
    pair (times on only one leg) raises; index comparison is allowed only
    inside a single declared domain (no times at all).
    """
    c_times = (coarse.t0_time, coarse.t1_time)
    f_times = (fine.t0_time, fine.t1_time)
    have = [t is not None for t in c_times + f_times]
    if all(have):
        ct0, ct1 = sorted(c_times)
        ft0, ft1 = sorted(f_times)
        if ft1 < ct0 or ft0 > ct1:
            return "disjoint"
        if tie_inclusive:
            time_inside = ct0 <= ft0 and ft1 <= ct1
        else:
            time_inside = ct0 < ft0 and ft1 < ct1
    elif any(have):
        raise ValueError(
            "containment requires timestamps on BOTH legs or on neither "
            "(single declared domain); raw cross-domain indices are never "
            "compared (final audit patch)")
    else:
        # END-TO-END CONSOLIDATION V1 (audit D5): numeric bar indices alone
        # establish containment ONLY inside one declared domain.  Cross-view
        # pairs without timestamps are incomparable — refuse, never 'contained'.
        if getattr(coarse, "view_id", None) != getattr(fine, "view_id", None):
            raise ValueError(
                "containment across views requires verified timestamps on "
                "both legs; bar numbers from different view domains do not "
                "establish temporal containment (consolidation V1)")
        ct0, ct1 = sorted((coarse.t0, coarse.t1))
        ft0, ft1 = sorted((fine.t0, fine.t1))
        if ft1 < ct0 or ft0 > ct1:
            return "disjoint"
        if tie_inclusive:
            time_inside = ct0 <= ft0 and ft1 <= ct1
        else:
            time_inside = ct0 < ft0 and ft1 < ct1
    if tie_inclusive:
        price_inside = coarse.p_lo <= fine.p_lo and fine.p_hi <= coarse.p_hi
    else:
        price_inside = coarse.p_lo < fine.p_lo and fine.p_hi < coarse.p_hi
    return "contained" if (time_inside and price_inside) else "escaping"


def sp06_dominance(candidates: Sequence[object],
                   requirements: Sequence[Tuple[str, Callable[[object], bool]]],
                   ) -> Tuple[List[object], List[Exclusion]]:
    """SP-06: exclude B when some A has S(B) strictly contained in S(A)."""
    satisfied: Dict[str, set] = {}
    for c in candidates:
        satisfied[_cid(c)] = {name for name, fn in requirements if fn(c)}
    survivors, excluded = [], []
    for c in candidates:
        sb = satisfied[_cid(c)]
        dominated_by = [cid for cid, sa in satisfied.items()
                        if cid != _cid(c) and sb < sa]
        if dominated_by:
            excluded.append(Exclusion(_cid(c), X_DOM, "R:SP-06",
                                      f"dominated by {dominated_by[0]}"))
        else:
            survivors.append(c)
    return survivors, excluded


def sp03_binding(close_price: float, refs: Sequence[object], side: str,
                 tie_bound: bool = False) -> List[object]:
    """SP-03 close-basis event binding: a reference is bound iff the closing
    price is beyond its level on the break side.  Tie rule is declared
    (TIE-CROSS-EQUAL-UNBOUND-V1 default: equality is not a crossing)."""
    bound = []
    for r in refs:
        if side == "down":
            crossed = (close_price < r.level) or (tie_bound and close_price == r.level)
        else:
            crossed = (close_price > r.level) or (tie_bound and close_price == r.level)
        if crossed:
            bound.append(r)
    return bound


def sp07_consistency(direction: str, current_price: float,
                     target_level: Optional[float],
                     invalidation_level: Optional[float],
                     entry_contained: Optional[bool]) -> Tuple[str, str]:
    """SP-07 logical consistency of a partial combination."""
    if target_level is not None and invalidation_level is not None:
        if direction == "up" and not (invalidation_level < current_price < target_level):
            return "inconsistent", "X-GEOM: invalidation/target not on declared sides"
        if direction == "down" and not (target_level < current_price < invalidation_level):
            return "inconsistent", "X-GEOM: invalidation/target not on declared sides"
    if entry_contained is False:
        return "inconsistent", "X-GEOM: entry leg not contained in its coarse leg (SP-05)"
    if target_level is None or invalidation_level is None:
        return "not-evaluable", "required element missing"
    return "consistent", ""


# --------------------------------------------------------------------------
# Task cards (file 16 §16.3) — deterministic procedures, Pi_T applied last
# --------------------------------------------------------------------------

def _mk(task_id: str, decision_bar: int, status: str,
        selected_id: Optional[str], survivors: List[str],
        excluded: List[Exclusion], unresolved: Optional[UnresolvedState],
        provenance: List[str], policy_refs: List[str], rep_id: str,
        dependents: Optional[List[str]] = None,
        notes: Optional[List[str]] = None,
        direction: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        decision_time: Optional[pd.Timestamp] = None) -> SelectionResult:
    return SelectionResult(
        task_id=task_id, decision_bar=decision_bar, status=status,
        selected_id=selected_id, survivors=survivors, excluded=excluded,
        unresolved=unresolved, provenance=provenance, policy_refs=policy_refs,
        representation_id=rep_id, dependents=dependents or [], notes=notes or [],
        direction=direction, dependencies=dependencies or [],
        decision_time=decision_time)


def task_s1_structural_reference(points: Sequence[PointCandidate],
                                 legs: Sequence[LegCandidate],
                                 decision_bar: int,
                                 rep: Representation,
                                 role: str,
                                 policy: PolicyRegistry,
                                 policy_id: Optional[str] = None,
                                 allow_provisional: bool = False,
                                 state_id_prefix: str = "S1",
                                 decision_time: Optional[pd.Timestamp] = None,
                                 axis: Optional["SharedInformationAxis"] = None
                                 ) -> SelectionResult:
    """T-S1: which confirmed point is the reference for view V's current state.

    Roles (Pi_T, O-class): "origin-of-last-confirmed-leg" (SWS-02) or
    "last-confirmed-extreme".  Without a declared role the output is MP.
    The analytical direction of the resolved reference is derived from the
    supporting leg (audit D6) — never from note strings.

    END-TO-END CONSOLIDATION V1 (task §1): all as-of availability runs
    through the validated shared information-time axis whenever evidence is
    time-bearing (``require_validated_asof``); no silent bar fallback.
    """
    require_validated_asof("T-S1", axis=axis, boundary_time=decision_time,
                           time_bearing=_time_bearing(points, legs))
    prov = ["R:SP-01", "R:SP-13", "R:SP-14", "F:H_T(confirmed,knowable,in-view)"]
    pregs: List[str] = []
    psnaps: Dict[str, dict] = {}
    # consolidation V1 (perf-neutral structural repair): the in-view partition
    # is computed by the DECLARED predicate (O(n)) — the previous membership
    # scan performed O(n^2) full record equality over the entire candidate
    # inventory on every recomputation (hours-long full-context runs)
    def _in_view(p: object) -> bool:
        return (p.rep.view_id == rep.view_id and p.rep.family == rep.family
                and p.rep.params == rep.params)

    in_view = [p for p in points if _in_view(p)]
    others = [p for p in points if not _in_view(p)]
    excluded: List[Exclusion] = [Exclusion(p.candidate_id, X_SCALE, "R:SP-02",
                                           "not in view V") for p in others]
    passed, ex1 = sp01_knowability(in_view, decision_bar, allow_provisional,
                                   as_of_time=decision_time, axis=axis)
    excluded += ex1
    confirmed = [p for p in passed if p.status_at(decision_bar, decision_time)
                 == STATUS_CONFIRMED]
    view_legs = [l for l in legs
                 if l.rep.view_id == rep.view_id and l.rep.params == rep.params]
    # CAUSAL-STATE INTEGRATION V1: legs are filtered by the SAME decision-time
    # availability discipline as points (shared axis; never bar-index-only —
    # a leg whose support becomes knowable only after the event must not
    # justify a result at the event).  Unavailable legs are EXCLUDED with an
    # auditable X-KNOW record, never silently dropped.
    confirmed_legs = []
    for l in view_legs:
        if not l.completed:
            continue
        if available_at(l, as_of_bar=decision_bar, as_of_time=decision_time,
                        axis=axis):
            confirmed_legs.append(l)
        else:
            excluded.append(Exclusion(
                l.leg_id, X_KNOW, "R:SP-01",
                f"leg knowable {getattr(l, 'knowable_time', None) or l.knowable_bar}"
                f" > t={decision_time or decision_bar}"))

    def _deps(*ids: str) -> List[str]:
        return [i for i in ids if i]

    # consolidation V1 (task §4): every result carries the exact policy
    # identity/version/values used when it was produced — including the
    # declared role and any registered policy id for ANY role
    psnaps["role"] = {"policy_id": "role", "version": 1, "value": role,
                      "class": CLASS_O, "kind": KIND_PROCEDURE}
    if policy_id is not None:
        psnaps[policy_id] = policy.snapshot_of(policy_id)

    def _ret(*args, **kwargs) -> SelectionResult:
        r = _mk(*args, **kwargs)
        r.policy_snapshots = dict(psnaps)
        return r

    if not confirmed_legs and not confirmed:
        state = UnresolvedState(
            state_id=f"{state_id_prefix}-{decision_bar}", task="T-S1",
            decision_bar=decision_bar, survivors=[], excluded=excluded,
            reason_code=REASON_IC, evidence_needed="more history / confirmation",
            policy_refs=[], provenance=prov,
            dependents_blocked=["T-S5", "T-S4", "zone-context", "liquidity-objective"])
        return _ret("T-S1", decision_bar, "unresolved", None, [], excluded, state,
                   prov, pregs, rep.rep_id, decision_time=decision_time)

    if role == "origin-of-last-confirmed-leg":
        if policy_id is None:
            state = UnresolvedState(
                state_id=f"{state_id_prefix}-{decision_bar}", task="T-S1",
                decision_bar=decision_bar,
                survivors=[p.candidate_id for p in confirmed], excluded=excluded,
                reason_code=REASON_MP,
                evidence_needed="declare Pi_T role (SP-18) and run SP-12 sensitivity",
                policy_refs=[], provenance=prov,
                dependents_blocked=["T-S5", "T-S4", "zone-context", "liquidity-objective"])
            return _ret("T-S1", decision_bar, "unresolved", None,
                       [p.candidate_id for p in confirmed], excluded, state,
                       prov, pregs, rep.rep_id, decision_time=decision_time)
        pregs.append(policy.ref(policy_id))
        psnaps[policy_id] = policy.snapshot_of(policy_id)
        if not confirmed_legs:
            state = UnresolvedState(
                state_id=f"{state_id_prefix}-{decision_bar}", task="T-S1",
                decision_bar=decision_bar,
                survivors=[p.candidate_id for p in confirmed], excluded=excluded,
                reason_code=REASON_IC, evidence_needed="no confirmed leg in view V yet",
                policy_refs=pregs, provenance=prov,
                dependents_blocked=["T-S5", "T-S4"])
            return _ret("T-S1", decision_bar, "unresolved", None,
                       [p.candidate_id for p in confirmed], excluded, state,
                       prov, pregs, rep.rep_id, decision_time=decision_time)
        last_leg = max(confirmed_legs, key=leg_recency_key)
        target_id = last_leg.start_id  # origin of the most recent confirmed leg
        target = next(p for p in points if p.candidate_id == target_id)
        # audit D5: a broken origin cannot serve as the structural reference;
        # the successor only becomes selectable when its leg is knowable.
        if target.status_at(decision_bar, decision_time) == STATUS_BROKEN:
            state = UnresolvedState(
                state_id=f"{state_id_prefix}-{decision_bar}", task="T-S1",
                decision_bar=decision_bar,
                survivors=[], excluded=excluded,
                reason_code=REASON_IC,
                evidence_needed=("origin of last confirmed leg is broken; "
                                 "successor reference not yet knowable"),
                policy_refs=pregs, provenance=prov,
                dependents_blocked=["T-S5", "T-S4"])
            return _ret("T-S1", decision_bar, "unresolved", None, [],
                       excluded, state, prov, pregs, rep.rep_id,
                       dependencies=_deps(target_id, last_leg.leg_id),
                       direction=last_leg.direction,
                       decision_time=decision_time)
        # CAUSAL-STATE INTEGRATION V1 (same-bar ambiguity): a selected
        # reference whose intrabar high/low order is not PROVEN by OHLC
        # endpoints must not silently produce a fully justified task result —
        # the consequential ambiguity (unavailable OR constrained-but-not-
        # unique) is surfaced to the result and its dependents.  Proven
        # endpoint order is factual: it is noted, never downgraded.
        amb_note = None
        if getattr(target, "same_bar_order", "resolved") == "unresolved":
            ev = getattr(target, "same_bar_evidence", None)
            cls = same_bar_evidence_class(ev)
            if cls != "proven":
                for p in confirmed:
                    if p.candidate_id != target_id:
                        excluded.append(Exclusion(
                            p.candidate_id, X_POL, f"O:{policy_id}",
                            "not the origin of the last confirmed leg"))
                state = UnresolvedState(
                    state_id=f"{state_id_prefix}-{decision_bar}", task="T-S1",
                    decision_bar=decision_bar,
                    survivors=[target_id], excluded=excluded,
                    reason_code=REASON_AI,
                    evidence_needed=(f"intrabar high/low order of the selected "
                                     f"reference is {cls} "
                                     f"(endpoint evidence: {ev or 'none'}); "
                                     "tick data (MO) or a declared ordering "
                                     "policy needed"),
                    policy_refs=pregs, provenance=prov,
                    dependents_blocked=["T-S5-falsifier", "T-S4-base",
                                        "zone-context", "liquidity-objective"])
                return _ret("T-S1", decision_bar, "unresolved", None, [target_id],
                           excluded, state, prov, pregs, rep.rep_id,
                           dependents=["T-S5-falsifier", "T-S4-base",
                                       "zone-context", "liquidity-objective"],
                           notes=[f"last_confirmed_leg={last_leg.leg_id}",
                                  f"role={role} (O-class; SWS-02: not a market claim)",
                                  f"same-bar order {cls}; surfaced (AI)"],
                           direction=last_leg.direction,
                           dependencies=_deps(target_id, last_leg.leg_id,
                                              last_leg.start_id, last_leg.end_id),
                           decision_time=decision_time)
            amb_note = (f"same-bar order proven by OHLC endpoints "
                        f"({ev}); not downgraded")
        for p in confirmed:
            if p.candidate_id != target_id:
                excluded.append(Exclusion(p.candidate_id, X_POL, f"O:{policy_id}",
                                          "not the origin of the last confirmed leg"))
        notes_final = [f"last_confirmed_leg={last_leg.leg_id}",
                       f"role={role} (O-class; SWS-02: not a market claim)"]
        if amb_note:
            notes_final.append(amb_note)
        return _ret("T-S1", decision_bar, "justified", target_id, [target_id],
                   excluded, None, prov, pregs, rep.rep_id,
                   dependents=["T-S5-falsifier", "T-S4-base", "zone-context",
                               "liquidity-objective"],
                   notes=notes_final,
                   direction=last_leg.direction,
                   dependencies=_deps(target_id, last_leg.leg_id,
                                      last_leg.start_id, last_leg.end_id),
                   decision_time=decision_time)
    elif role == "last-confirmed-extreme":
        if not confirmed:
            state = UnresolvedState(
                state_id=f"{state_id_prefix}-{decision_bar}", task="T-S1",
                decision_bar=decision_bar, survivors=[], excluded=excluded,
                reason_code=REASON_IC, evidence_needed="no confirmed point yet",
                policy_refs=pregs, provenance=prov)
            return _ret("T-S1", decision_bar, "unresolved", None, [], excluded,
                       state, prov, pregs, rep.rep_id, decision_time=decision_time)
        best = max(confirmed, key=lambda p: p.knowable_bar)
        for p in confirmed:
            if p.candidate_id != best.candidate_id:
                excluded.append(Exclusion(p.candidate_id, X_POL, "R:within-class:knowable_bar",
                                          "less recent confirmed point"))
        # FINAL AUDIT PATCH (same-bar ambiguity propagation), same gate as the
        # origin branch: a selected reference with materially unresolved
        # intrabar order must surface (AI); endpoint-determined is noted.
        e_notes = ["role=last-confirmed-extreme"]
        if getattr(best, "same_bar_order", "resolved") == "unresolved":
            ev = getattr(best, "same_bar_evidence", None)
            cls = same_bar_evidence_class(ev)
            if cls != "proven":
                state = UnresolvedState(
                    state_id=f"{state_id_prefix}-{decision_bar}", task="T-S1",
                    decision_bar=decision_bar,
                    survivors=[best.candidate_id], excluded=excluded,
                    reason_code=REASON_AI,
                    evidence_needed=(f"intrabar high/low order of the selected "
                                     f"reference is {cls} "
                                     f"(endpoint evidence: {ev or 'none'}); "
                                     "tick data (MO) or a declared ordering "
                                     "policy needed"),
                    policy_refs=pregs, provenance=prov,
                    dependents_blocked=["T-S5-falsifier", "T-S4-base",
                                        "zone-context", "liquidity-objective"])
                return _ret("T-S1", decision_bar, "unresolved", None,
                           [best.candidate_id], excluded, state, prov, pregs,
                           rep.rep_id,
                           notes=e_notes + [f"same-bar order {cls}; surfaced (AI)"],
                           dependencies=_deps(best.candidate_id),
                           decision_time=decision_time)
            e_notes.append(f"same-bar order proven by OHLC endpoints ({ev}); "
                           "not downgraded")
        return _ret("T-S1", decision_bar, "justified", best.candidate_id,
                   [best.candidate_id], excluded, None, prov, pregs, rep.rep_id,
                   notes=e_notes,
                   dependencies=_deps(best.candidate_id),
                   decision_time=decision_time)
    state = UnresolvedState(
        state_id=f"{state_id_prefix}-{decision_bar}", task="T-S1",
        decision_bar=decision_bar, survivors=[p.candidate_id for p in confirmed],
        excluded=excluded, reason_code=REASON_MP,
        evidence_needed=f"declared role for question (role={role!r} not recognized)",
        policy_refs=[], provenance=prov)
    return _ret("T-S1", decision_bar, "unresolved", None,
               [p.candidate_id for p in confirmed], excluded, state, prov,
               pregs, rep.rep_id, decision_time=decision_time)


def task_s2_event_binding(event_bar: int, close_price: float,
                          refs_by_view: Dict[str, Sequence[object]],
                          decision_bar: int,
                          tie_bound: bool = False,
                          require_single_view: Optional[str] = None,
                          prev_close: Optional[float] = None,
                          state_id_prefix: str = "S2",
                          event_time: Optional[pd.Timestamp] = None,
                          tie_policy: str = TIE_CROSS_EQUAL_UNBOUND,
                          allow_provisional: bool = False,
                          event_ref: Optional[str] = None,
                          axis: Optional["SharedInformationAxis"] = None
                          ) -> SelectionResult:
    """T-S2: which references does a closed-bar event bind to (SP-03)?

    The binding set keeps all members; no ranking (SWS-05).  When
    ``prev_close`` is provided only FRESH crossings count (the previous close
    was not yet beyond the level); without it the bar is the declared single
    event bar (golden cases W5/W10).

    Knowledge contract (file 16 T-S2): inputs are **all confirmed references
    knowable ≤ b** in every view in scope; H_T is a close crossing on the
    break side with ``knowable ≤ b``.  The dependent clause states that "a
    later close back across the reference is a separate event, not an edit of
    the first" — therefore NO first-break-only restriction exists in the
    contract: later factual price interactions with a known level bind too
    and are TAGGED, never dropped.  ``binding_kinds`` on the result records,
    per bound reference, the pre-event lifecycle state:

    * ``first-break``            — pre-event state not broken (category A)
    * ``later-interaction``      — pre-event state already broken (category B)
    * ``provisional:…`` prefix   — declared provisional use (SWS-04a tag)

    PRE/POST-EVENT PROTOCOL (causal-state integration V1): this task
    evaluates crossings against the state reconstructed immediately BEFORE
    the event and NEVER mutates candidates; the caller applies the event's
    lifecycle transitions afterwards and recomputes dependents on the
    post-event state.  Recorded bindings are immutable (a later break never
    edits or removes the original binding record).

    Cross-view binding compares only on the shared information-time axis
    (``event_time`` mandatory for multi-view); raw bar indices from different
    timeframe domains are never compared.  Superseded never-confirmed points
    are excluded X-SUPER (SWS-04c); provisional points are excluded X-STATE
    unless ``allow_provisional=True`` declares the SWS-04a policy (gated on
    occurrence visibility, output tagged ``provisional``).
    """
    prov = ["R:SP-03", "F:close-basis (declared; wick variant open)",
            f"tie={tie_policy}"]
    # ---- consolidation V1 (task §4): tie policy vs tie behavior ---------
    # The DECLARED policy governs actual behavior; the boolean and the
    # policy name can never contradict each other.
    if tie_policy not in TIE_CROSS_POLICIES:
        raise ValueError(f"unknown tie policy {tie_policy!r}")
    if tie_bound and tie_policy != TIE_CROSS_EQUAL_BOUND_V1:
        raise ValueError(
            "tie-policy contradiction: tie_bound=True requires "
            f"{TIE_CROSS_EQUAL_BOUND_V1!r} (declared {tie_policy!r}); "
            "declared policy and actual tie behavior must agree")
    if tie_policy == TIE_CROSS_EQUAL_BOUND_V1:
        tie_bound = True      # behavior derived from the declared policy
    all_refs = [r for refs in refs_by_view.values() for r in refs]
    require_validated_asof("T-S2", axis=axis, boundary_time=event_time,
                           time_bearing=_time_bearing(all_refs))
    bound: List[str] = []
    binding_kinds: Dict[str, str] = {}
    excluded: List[Exclusion] = []
    per_view: Dict[str, List[str]] = {}
    pre_all: Dict[str, str] = {}      # PRE_EVENT_STATE (consolidation V1)
    multi_view = len(refs_by_view) > 1
    if multi_view and event_time is None:
        raise ValueError(
            "cross-view binding requires a shared information-time axis "
            "(event_time): raw bar indices from different timeframe domains "
            "are never compared (audit D1)")

    def _crossed(r: object, px: float) -> bool:
        rside = getattr(r, "side", None)
        if rside == "high":
            return (px > r.level) or (tie_bound and px == r.level)
        if rside == "low":
            return (px < r.level) or (tie_bound and px == r.level)
        return (px != r.level) if not tie_bound else True

    for view, refs in refs_by_view.items():
        # status gate BEFORE availability (task contract); st here is the
        # PRE-EVENT lifecycle state (this task never mutates candidates).
        # consolidation V1: excluding_event_ref reconstructs PRE_EVENT_STATE —
        # the event's own recorded transitions never rewrite its binding.
        usable = []
        knowable: List[object] = []
        late: List[object] = []
        for r in refs:
            st = (r.status_at(event_bar, event_time,
                              excluding_event_ref=event_ref)
                  if hasattr(r, "status_at") else getattr(r, "status", STATUS_CONFIRMED))
            pre_all[r.candidate_id] = st
            if st == STATUS_SUPERSEDED:
                excluded.append(Exclusion(r.candidate_id, X_SUPER, "R:SP-13/SWS-04c",
                                          "superseded (never confirmed) not bindable"))
            elif st == STATUS_PROVISIONAL and not allow_provisional:
                excluded.append(Exclusion(r.candidate_id, X_STATE, "R:SP-01/SWS-04a",
                                          "provisional not allowed by task contract"))
            elif st == STATUS_PROVISIONAL:
                # explicit provisional use: gated on OCCURRENCE visibility,
                # never on the projected confirmation time
                occ_t = getattr(r, "occurrence_time", None)
                occ_b = getattr(r, "occurrence_bar", 0)
                if ((event_time is not None and occ_t is not None
                     and occ_t <= event_time)
                        or (event_time is None and occ_b <= event_bar)):
                    knowable.append(r)
                else:
                    excluded.append(Exclusion(r.candidate_id, X_KNOW, "R:SP-01",
                                              "provisional occurrence after event"))
            else:
                # confirmed AND historically-broken references are eligible:
                # the knowledge contract has no first-break-only rule; later
                # factual interactions bind and are TAGGED (A vs B), never
                # dropped
                usable.append(r)
        for r in usable:
            ok = available_at(r, as_of_bar=event_bar, as_of_time=event_time,
                              axis=axis)
            if ok:
                knowable.append(r)
            else:
                late.append(r)
        for r in late:
            excluded.append(Exclusion(
                r.candidate_id, X_KNOW, "R:SP-01",
                f"knowable {getattr(r, 'knowable_time', None) or r.knowable_bar}"
                f" > event {event_time or event_bar}"))
        # SP-03 (close basis): a reference is bound iff the close is beyond its
        # level ON ITS BREAK SIDE — a low is broken downward (close < level),
        # a high upward (close > level).  Tie rule declared (SWS-06).
        hit = [r for r in knowable
               if _crossed(r, close_price)
               and (prev_close is None or not _crossed(r, prev_close))]
        per_view[view] = [r.candidate_id for r in hit]
        bound += per_view[view]
        for r in hit:
            st = pre_all.get(r.candidate_id)
            kind = ("later-interaction" if st == STATUS_BROKEN else "first-break")
            if st == STATUS_PROVISIONAL:
                kind = "provisional:" + kind
            binding_kinds[r.candidate_id] = kind
    # explicit event phases (consolidation V1, task §3)
    post_state = dict(pre_all)
    for cid, kind in binding_kinds.items():
        if kind.endswith("first-break"):
            post_state[cid] = STATUS_BROKEN
    event_phase = {
        PHASE_PRE_EVENT: dict(pre_all),
        PHASE_BINDING: {"bound": list(bound),
                        "binding_kinds": dict(binding_kinds)},
        PHASE_POST_EVENT: post_state,
    }
    task_psnaps = {
        "tie_policy": {"policy_id": "tie_policy", "version": 1,
                       "value": tie_policy, "class": CLASS_O,
                       "kind": KIND_PROCEDURE},
        "allow_provisional": {"policy_id": "allow_provisional", "version": 1,
                              "value": bool(allow_provisional), "class": CLASS_O,
                              "kind": KIND_PROCEDURE},
    }
    if not bound:
        result = _mk("T-S2", event_bar, "empty", None, [], excluded, None, prov,
                     [], f"event@{event_bar}",
                     notes=["no event at these scales",
                            f"binding per view: {per_view}"],
                     dependencies=[r.candidate_id for refs in refs_by_view.values()
                                   for r in refs],
                     decision_time=event_time)
        result.binding_kinds = binding_kinds
        result.event_phase = event_phase
        result.policy_snapshots = task_psnaps
        return result
    unresolved = None
    status = "justified"
    if require_single_view is not None and len(per_view.get(require_single_view, [])) != 1:
        status = "unresolved"
        unresolved = UnresolvedState(
            state_id=f"{state_id_prefix}-{event_bar}", task="T-S2",
            decision_bar=event_bar, survivors=bound, excluded=excluded,
            reason_code=REASON_MP if len(per_view.get(require_single_view, [])) > 1 else REASON_IC,
            evidence_needed="task requires a single view binding; several/none crossed — declare view policy",
            policy_refs=[], provenance=prov)
    kinds_note = ", ".join(f"{cid}={k}" for cid, k in binding_kinds.items())
    result = _mk("T-S2", event_bar, status, bound[0] if len(bound) == 1 else None,
                 bound, excluded, unresolved, prov, [], f"event@{event_bar}",
                 dependents=["view-trend-state", "falsifier-evaluation", "reclaim-check"],
                 notes=[f"binding per view: {per_view}",
                        f"binding kinds (pre-event state): {kinds_note or 'none'}"],
                         dependencies=[r.candidate_id for refs in refs_by_view.values()
                                       for r in refs],
                         decision_time=event_time)
    result.binding_kinds = binding_kinds
    result.event_phase = event_phase
    result.policy_snapshots = task_psnaps
    return result


def task_s3_entry_leg(coarse_leg: LegCandidate, fine_legs: Sequence[LegCandidate],
                      decision_bar: int, rep: Representation,
                      continuation_condition: Optional[Tuple[str, str]] = None,
                      policy: Optional[PolicyRegistry] = None,
                      state_id_prefix: str = "S3",
                      decision_time: Optional[pd.Timestamp] = None,
                      axis: Optional["SharedInformationAxis"] = None) -> SelectionResult:
    """T-S3: which completed fine leg contained in the coarse leg times an entry.

    continuation_condition: optional declared O policy (e.g. ("direction",
    "down") meaning a continuation-long entry uses completed down-legs inside
    an up-leg).  Depth vs recency is never decided here (SWS-07): without a
    declared policy the surviving pair is emitted as MP (or EP when a learned
    preference would be needed).

    FINAL AUDIT PATCH: availability is evaluated on the shared information
    axis (``decision_time`` when given); containment uses verified timestamps
    for cross-timeframe legs (sp05_containment).
    """
    prov = ["R:SP-05", "R:SP-08", "R:SP-01", "R:SP-06"]
    # END-TO-END CONSOLIDATION V1 (task §1): T-S3 is the cross-timeframe task
    # — time-bearing legs REQUIRE the decision boundary and the validated
    # shared axis; a missing decision_time is never accepted (audit D6).
    require_validated_asof("T-S3", axis=axis, boundary_time=decision_time,
                           time_bearing=_time_bearing([coarse_leg], fine_legs))
    pregs: List[str] = []
    psnaps3: Dict[str, dict] = {}
    excluded: List[Exclusion] = []
    survivors: List[LegCandidate] = []
    def _ret(*args, **kwargs) -> SelectionResult:
        kwargs.setdefault("decision_time", decision_time)
        r = _mk(*args, **kwargs)
        r.policy_snapshots = dict(psnaps3)
        return r

    # decision-time availability (shared axis): the coarse leg itself must be
    # knowable at the decision boundary too
    if not available_at(coarse_leg, as_of_bar=decision_bar,
                        as_of_time=decision_time, axis=axis):
        excluded.append(Exclusion(coarse_leg.leg_id, X_KNOW, "R:SP-01",
                                  "coarse leg not knowable at decision time"))
        state = UnresolvedState(
            state_id=f"{state_id_prefix}-{decision_bar}", task="T-S3",
            decision_bar=decision_bar, survivors=[], excluded=excluded,
            reason_code=REASON_IC,
            evidence_needed="coarse basis not knowable at the decision time",
            policy_refs=[], provenance=prov,
            dependents_blocked=["zone-boundaries", "fine-liquidity-below-above"])
        return _ret("T-S3", decision_bar, "unresolved", None, [], excluded,
                   state, prov, pregs, rep.rep_id,
                   dependencies=[coarse_leg.leg_id] + [f.leg_id for f in fine_legs])
    for f in fine_legs:
        if not available_at(f, as_of_bar=decision_bar,
                            as_of_time=decision_time, axis=axis):
            excluded.append(Exclusion(f.leg_id, X_KNOW, "R:SP-01",
                                      f"knowable {getattr(f, 'knowable_time', None) or f.knowable_bar}"
                                      f" > t={decision_time or decision_bar}"))
            continue
        label = sp05_containment(coarse_leg, f)
        if label != "contained":
            excluded.append(Exclusion(f.leg_id, X_GEOM, "R:SP-05", label))
            continue
        if not f.completed:
            excluded.append(Exclusion(f.leg_id, X_STATE, "R:T-S3:H_T", "not completed"))
            continue
        if continuation_condition is not None:
            pregs.append("O:P-CONTINUATION" if policy is None else policy.ref("P-CONTINUATION"))
            if policy is not None:
                psnaps3["P-CONTINUATION"] = policy.snapshot_of("P-CONTINUATION")
            else:
                psnaps3["P-CONTINUATION"] = {
                    "policy_id": "P-CONTINUATION", "version": 1,
                    "value": continuation_condition, "class": CLASS_O,
                    "kind": KIND_PROCEDURE}
            kind, want = continuation_condition
            if kind == "direction" and f.direction != want:
                excluded.append(Exclusion(f.leg_id, X_POL,
                                          "O:P-CONTINUATION",
                                          f"continuation condition wants {want}-legs"))
                continue
        survivors.append(f)
    # SP-06 dominance on the declared H_T facts (completed, contained, direction)
    reqs: List[Tuple[str, Callable[[object], bool]]] = [
        ("completed", lambda f: f.completed),
        ("knowable", lambda f: available_at(f, as_of_bar=decision_bar,
                                            as_of_time=decision_time,
                                            axis=axis)),
    ]
    if continuation_condition is not None:
        reqs.append(("direction-match",
                     lambda f: f.direction == continuation_condition[1]))
    survivors, ex2 = sp06_dominance(survivors, reqs)
    excluded += ex2
    surv_ids = [f.leg_id for f in survivors]
    deps = [coarse_leg.leg_id] + [f.leg_id for f in fine_legs]
    if not survivors:
        state = UnresolvedState(
            state_id=f"{state_id_prefix}-{decision_bar}", task="T-S3",
            decision_bar=decision_bar, survivors=[], excluded=excluded,
            reason_code=REASON_IC, evidence_needed="no completed contained fine leg yet",
            policy_refs=pregs, provenance=prov)
        return _ret("T-S3", decision_bar, "unresolved", None, [], excluded, state,
                   prov, pregs, rep.rep_id, dependencies=deps)
    if len(survivors) == 1:
        return _ret("T-S3", decision_bar, "justified", surv_ids[0], surv_ids,
                   excluded, None, prov, pregs, rep.rep_id,
                   notes=["singleton after H_T + dominance"], dependencies=deps)
    # audit D6: factual depth is the absolute price travel of the leg
    diffs = []
    for f in survivors:
        diffs.append(f"{f.leg_id}(depth={f.depth:g},knowable={f.knowable_bar})")
    state = UnresolvedState(
        state_id=f"{state_id_prefix}-{decision_bar}", task="T-S3",
        decision_bar=decision_bar, survivors=surv_ids, excluded=excluded,
        reason_code=REASON_MP,
        evidence_needed=("declare a recency-vs-depth policy Pi_T (SP-18) with "
                         "sensitivity analysis (SP-12), or annotated preference "
                         "data (file 18, objective B) for an EP resolution"),
        policy_refs=pregs, provenance=prov,
        dependents_blocked=["zone-boundaries", "fine-liquidity-below-above"])
    return _ret("T-S3", decision_bar, "unresolved", None, surv_ids, excluded,
               state, prov, pregs, rep.rep_id,
               notes=["factual differences preserved: " + "; ".join(diffs),
                      "depth-vs-recency is SWS-07 open (MP/EP), not a fact"],
               dependencies=deps)


def task_s5_falsifier(claims: Sequence[dict], points: Sequence[PointCandidate],
                      legs: Sequence[LegCandidate], decision_bar: int,
                      state_id_prefix: str = "S5",
                      decision_time: Optional[pd.Timestamp] = None,
                      axis: Optional["SharedInformationAxis"] = None) -> SelectionResult:
    """T-S5 / SP-04: map each reference-form claim of interpretation I to its
    falsifier reference.  Claims are dicts:
      {"interpretation": "I1", "view": "C", "role": "...", "direction": "up"}
    Supported roles: "origin-of-last-confirmed-leg", "low-of-current-leg",
    "high-of-current-leg", "last-confirmed-extreme".  A claim not written in
    reference terms yields MP (SWS-08).

    CAUSAL-STATE INTEGRATION V1: supporting legs and references are filtered
    by the SAME decision-time availability discipline as T-S1 (shared axis
    via ``decision_time``); a support that becomes knowable only after the
    decision never justifies a result.

    Audit D6: direction is taken from the claim's declared interpretation
    semantics (the movement representation), validated structurally against
    the supporting leg; a missing or inconsistent direction yields an
    explicit unresolved state (never inferred from note strings).  A
    falsifier reference recorded as structurally broken at the decision bar
    FALSIFIES the claim (computed task-level effect).
    """
    prov = ["R:SP-04", "F:given I written in reference terms (SWS-08)"]
    require_validated_asof("T-S5", axis=axis, boundary_time=decision_time,
                           time_bearing=_time_bearing(points, legs))
    resolved: List[str] = []
    excluded: List[Exclusion] = []
    notes: List[str] = []
    deps: List[str] = []
    falsified: List[str] = []
    by_id = {p.candidate_id: p for p in points}
    legs_by_view: Dict[str, List[LegCandidate]] = {}
    for l in legs:
        legs_by_view.setdefault(l.view_id, []).append(l)

    def _broken(pid: str) -> bool:
        p = by_id.get(pid)
        return (p is not None
                and p.status_at(decision_bar, decision_time) == STATUS_BROKEN)

    for claim in claims:
        role = claim.get("role", "")
        view = claim.get("view", "")
        interp = claim.get("interpretation", "?")
        vlegs = [l for l in legs_by_view.get(view, [])
                 if l.completed
                 and available_at(l, as_of_bar=decision_bar,
                                  as_of_time=decision_time, axis=axis)]
        if role == "origin-of-last-confirmed-leg":
            if not vlegs:
                excluded.append(Exclusion(f"{interp}:{role}", X_STATE, "R:SP-04",
                                          "no confirmed leg in view"))
                continue
            last = max(vlegs, key=leg_recency_key)
            # FINAL AUDIT PATCH (T-S5 origin direction validation): the claim's
            # direction is validated against the supporting leg — opposite or
            # missing direction must NOT silently produce the same justified
            # result (previously this branch ignored direction entirely).
            want_dir = claim.get("direction")
            if want_dir not in ("up", "down"):
                state = UnresolvedState(
                    state_id=f"{state_id_prefix}-{decision_bar}", task="T-S5",
                    decision_bar=decision_bar, survivors=resolved, excluded=excluded,
                    reason_code=REASON_IC,
                    evidence_needed=(f"claim {interp} role {role} requires a "
                                     "supported direction (movement "
                                     "representation); none given"),
                    policy_refs=[], provenance=prov)
                return _mk("T-S5", decision_bar, "unresolved", None, resolved,
                           excluded, state, prov, [], "claims",
                           notes=notes, dependencies=deps, decision_time=decision_time)
            if want_dir != last.direction:
                state = UnresolvedState(
                    state_id=f"{state_id_prefix}-{decision_bar}", task="T-S5",
                    decision_bar=decision_bar, survivors=resolved, excluded=excluded,
                    reason_code=REASON_AI,
                    evidence_needed=(f"claim {interp} direction {want_dir!r} "
                                     f"contradicts the supporting leg "
                                     f"{last.leg_id} direction {last.direction!r}; "
                                     "re-read the interpretation"),
                    policy_refs=[], provenance=prov)
                return _mk("T-S5", decision_bar, "unresolved", None, resolved,
                           excluded, state, prov, [], "claims",
                           notes=notes, dependencies=deps,
                           direction=last.direction, decision_time=decision_time)
            resolved.append(last.start_id)
            deps += [last.start_id, last.leg_id]
            notes.append(f"{interp}: origin of {last.leg_id} -> {last.start_id}")
        elif role in ("low-of-current-leg", "high-of-current-leg"):
            want_dir = claim.get("direction")
            # audit D6: direction must come from the interpretation/movement
            # representation; unavailable or invalid -> explicit unresolved
            if want_dir not in ("up", "down"):
                state = UnresolvedState(
                    state_id=f"{state_id_prefix}-{decision_bar}", task="T-S5",
                    decision_bar=decision_bar, survivors=resolved, excluded=excluded,
                    reason_code=REASON_IC,
                    evidence_needed=(f"claim {interp} role {role} requires a "
                                     "supported direction (movement "
                                     "representation); none/inconsistent given"),
                    policy_refs=[], provenance=prov)
                return _mk("T-S5", decision_bar, "unresolved", None, resolved,
                           excluded, state, prov, [], "claims",
                           notes=notes, dependencies=deps, decision_time=decision_time)
            dlegs = [l for l in vlegs if l.direction == want_dir]
            if not dlegs:
                excluded.append(Exclusion(f"{interp}:{role}", X_STATE, "R:SP-04",
                                          f"no confirmed {want_dir} leg in view"))
                continue
            last = max(dlegs, key=lambda l: (l.knowable_bar, l.t1))
            pid = last.low_id if role == "low-of-current-leg" else last.high_id
            resolved.append(pid)
            deps += [pid, last.leg_id]
            notes.append(f"{interp}: {role}[{want_dir}] of {last.leg_id} -> {pid}")
        elif role == "last-confirmed-extreme":
            # END-TO-END CONSOLIDATION V1 (audit D2): time-aware availability
            # governs — a point whose knowable_time is after the decision
            # boundary can NEVER justify a result at that boundary (the old
            # bar-index-only filter admitted late-confirmed references).
            # Late but confirmed points get an auditable X-KNOW exclusion.
            vpts = []
            for p in points:
                if p.view_id != view:
                    continue
                if p.status_at(decision_bar, decision_time) != STATUS_CONFIRMED:
                    continue
                if not available_at(p, as_of_bar=decision_bar,
                                    as_of_time=decision_time, axis=axis):
                    excluded.append(Exclusion(
                        p.candidate_id, X_KNOW, "R:SP-01",
                        f"knowable {getattr(p, 'knowable_time', None) or p.knowable_bar}"
                        f" > t={decision_time or decision_bar}"))
                    continue
                vpts.append(p)
            if not vpts:
                excluded.append(Exclusion(f"{interp}:{role}", X_STATE, "R:SP-04",
                                          "no confirmed point in view"))
                continue
            want = claim.get("side", "low")
            cand = [p for p in vpts if p.side == want]
            if not cand:
                excluded.append(Exclusion(f"{interp}:{role}", X_STATE, "R:SP-04",
                                          f"no confirmed {want} in view"))
                continue
            best = max(cand, key=lambda p: p.knowable_bar)
            resolved.append(best.candidate_id)
            deps.append(best.candidate_id)
            notes.append(f"{interp}: last-confirmed-{want} -> {best.candidate_id}")
        else:
            excluded.append(Exclusion(f"{interp}:{role or 'none'}", X_POL, "R:SP-04",
                                      "claim not written in reference terms"))
    # computed falsification: a broken falsifier reference fires (audit D5/D6)
    for pid in list(resolved):
        if _broken(pid):
            falsified.append(pid)
    if falsified:
        state = UnresolvedState(
            state_id=f"{state_id_prefix}-{decision_bar}", task="T-S5",
            decision_bar=decision_bar, survivors=resolved, excluded=excluded,
            reason_code=REASON_IC,
            evidence_needed=("falsifier reference structurally broken at/before t; "
                             "claim contradicted — re-state interpretation or "
                             "record the revision (SP-20)"),
            policy_refs=[], provenance=prov)
        return _mk("T-S5", decision_bar, "falsified", None, resolved, excluded,
                   state, prov, [], "claims",
                   dependents=["invalidation-levels", "stop-side-reference"],
                   notes=notes + [f"falsified by broken ref {p}" for p in falsified],
                   dependencies=deps, decision_time=decision_time)
    if not resolved:
        state = UnresolvedState(
            state_id=f"{state_id_prefix}-{decision_bar}", task="T-S5",
            decision_bar=decision_bar, survivors=[], excluded=excluded,
            reason_code=REASON_MP,
            evidence_needed="write I in reference terms (SWS-08) or declare the reading as O/S-ambiguous",
            policy_refs=[], provenance=prov)
        return _mk("T-S5", decision_bar, "unresolved", None, [], excluded, state,
                   prov, [], "claims", notes=notes, dependencies=deps, decision_time=decision_time)
    # FINAL AUDIT PATCH (same-bar ambiguity propagation): a resolved falsifier
    # whose intrabar order is materially unresolved must surface that state.
    amb_ids = [pid for pid in resolved if material_same_bar_ambiguity(by_id.get(pid))]
    if amb_ids:
        state = UnresolvedState(
            state_id=f"{state_id_prefix}-{decision_bar}", task="T-S5",
            decision_bar=decision_bar, survivors=resolved, excluded=excluded,
            reason_code=REASON_AI,
            evidence_needed=("falsifier reference has unresolved intrabar "
                             f"high/low order ({amb_ids}); tick data (MO) or a "
                             "declared ordering policy needed"),
            policy_refs=[], provenance=prov,
            dependents_blocked=["invalidation-levels", "stop-side-reference"])
        return _mk("T-S5", decision_bar, "unresolved", None, resolved, excluded,
                   state, prov, [], "claims",
                   dependents=["invalidation-levels", "stop-side-reference"],
                   notes=notes + ["same-bar order unresolved; surfaced (AI)"],
                   dependencies=deps, decision_time=decision_time)
    status = "justified" if len(resolved) == 1 else "unresolved"
    unresolved = None
    if status == "unresolved":
        unresolved = UnresolvedState(
            state_id=f"{state_id_prefix}-{decision_bar}", task="T-S5",
            decision_bar=decision_bar, survivors=resolved, excluded=excluded,
            reason_code=REASON_AI,
            evidence_needed="claim maps to several references; re-read the wording with a timestamp",
            policy_refs=[], provenance=prov)
    return _mk("T-S5", decision_bar, status,
               resolved[0] if len(resolved) == 1 else None, resolved, excluded,
               unresolved, prov, [], "claims",
               dependents=["invalidation-levels", "stop-side-reference"],
               notes=notes, dependencies=deps, decision_time=decision_time)

# --------------------------------------------------------------------------
# Interpretation ledger & REAL revision propagation (IC-10, IC-11, SP-20)
# --------------------------------------------------------------------------

class InterpretationLedger:
    """Append-only record of selections, events, versions, and propagation.

    Audit D5: ``propagate()`` RECOMPUTES dependent results from the stored
    task inputs as of the update boundary and records the computed
    differences.  Caller-supplied before/after strings are never accepted as
    proof of recomputation (``record_change`` stores upstream FACTS such as a
    structural break or a newly knowable leg; propagation derives everything
    else).  Prior versions are preserved; a dependent conclusion changes only
    when the required information is knowable at the update boundary.
    """

    def __init__(self) -> None:
        self.results: List[SelectionResult] = []
        self.events: List[dict] = []
        self.revisions: List[dict] = []
        # uid -> ordered version list: [{"version", "info_bar", "result",
        #                                "computed_changes"}]
        self.versions: Dict[str, List[dict]] = {}
        # uid -> (kind, payload) sufficient to re-run the task
        self._payloads: Dict[str, dict] = {}
        # uid -> every candidate/leg id the task consumed (input dependencies)
        self._payload_ids: Dict[str, set] = {}
        # uid -> registered RESULT uids it depends on (consolidation V1 §5:
        # transitive dependent recomputation along result-dependency edges)
        self._result_deps: Dict[str, set] = {}
        self._uid_seq = 0

    # ---- recording -----------------------------------------------------

    def record(self, result: SelectionResult,
               payload: Optional[dict] = None) -> str:
        """Register a result version.  ``payload`` (audit D5) must contain
        the task kind and its inputs (points/legs/claims/...) to make real
        recomputation possible; without it the result can still be logged but
        is marked non-recomputable (and never claimed as propagated)."""
        self._uid_seq += 1
        uid = f"{result.task_id}#{self._uid_seq}"
        self.results.append(result)
        self.versions[uid] = [{
            "version": 1,
            "info_bar": result.decision_bar,
            "result": result,
            "computed_changes": [],
            "recomputable": payload is not None,
        }]
        if payload is not None:
            self._payloads[uid] = dict(payload, _kind=payload.get("kind"))
            self._payload_ids[uid] = _payload_ids(payload)
        else:
            self._payload_ids[uid] = set()
        # result-level dependency edges (consolidation V1 §5): explicit
        # ``depends_on_results`` and any dependency naming a registered uid
        deps = set(payload.get("depends_on_results", []) if payload else [])
        deps |= {d for d in (result.dependencies or []) if d in self.versions}
        self._result_deps[uid] = deps
        return uid

    def record_event(self, event_bar: int, kind: str, detail: str,
                     affected_ids: Sequence[str],
                     event_time: Optional[pd.Timestamp] = None) -> None:
        self.events.append({"event_bar": event_bar, "kind": kind,
                            "detail": detail, "affected_ids": list(affected_ids),
                            "event_time": event_time})

    def record_change(self, info_bar: int, target_id: str, new_state: str,
                      detail: str = "",
                      info_time: Optional[pd.Timestamp] = None,
                      event_ref: Optional[str] = None) -> None:
        """Upstream FACT (append-only): a structural break ('broken') or a
        newly knowable item ('knowable').  Facts drive propagation; they are
        not themselves claimed as recomputation.  ``event_ref`` names the
        recorded EVENT that authorizes the state change (causal-state
        integration V1: a break fact must cite its binding event)."""
        self.revisions.append({
            "kind": "change-fact", "info_bar": info_bar, "info_time": info_time,
            "target": target_id, "new_state": new_state, "detail": detail,
            "event_ref": event_ref,
            "rule": "R:SP-20 upstream fact (append-only)",
        })

    # ---- real propagation ---------------------------------------------

    def propagate(self, update_bar: int, changed_ids: Sequence[str],
                  changed_states: Optional[Dict[str, str]] = None,
                  update_time: Optional[pd.Timestamp] = None,
                  event_ref: Optional[str] = None) -> List[dict]:
        """SP-20: recompute every dependent of ``changed_ids`` from its
        stored inputs as of ``update_bar`` and append new versions with the
        ACTUAL computed differences.  Returns the propagation entries.

        ``changed_states`` (optional) maps candidate id -> structural state to
        apply as an append-only change fact before recomputation (e.g.
        {"L_b": "broken"}); the state is recorded as a fact (citing
        ``event_ref`` as its authorizing event when given), then every
        dependent is re-evaluated — the logged differences are computed from
        the recomputed results, never supplied by the caller.

        END-TO-END CONSOLIDATION V1 (task §5): TRANSITIVE along registered
        result-dependency edges.  A -> B -> C: when A is reconsidered, B is
        reconsidered too; when B is reconsidered, C is reconsidered with its
        correct updated inputs and information time.  Results outside the
        dependency closure of the change are never recomputed; every result
        is recomputed at most once per call; dependency cycles are detected
        and reported explicitly.
        """
        log: List[dict] = []
        changed = set(changed_ids)
        if changed_states:
            for cid, st in changed_states.items():
                self.record_change(update_bar, cid, st,
                                   info_time=update_time, event_ref=event_ref)
                if st == STATUS_BROKEN:
                    self._mark_broken(cid, update_bar, update_time,
                                      event_ref=event_ref)
        cycle = self._find_dependency_cycle()
        step = 0
        if cycle:
            entry = {
                "kind": "dependency-cycle",
                "event_bar": update_bar, "info_time": update_time,
                "cycle": cycle,
                "note": "cycle in registered result dependencies; each "
                        "result is recomputed at most once and the cyclic "
                        "edge is not followed twice (explicit detection)",
                "rule": "R:SP-20 cycle detection",
            }
            self.revisions.append(entry)
            log.append(entry)
        frontier = set(changed) | set(changed_states or {})
        done: set = set()
        while frontier:
            wave = sorted(uid for uid in self.versions
                          if uid not in done and self._deps_of(uid) & frontier)
            if not wave:
                break
            next_frontier = set()
            for uid in wave:
                done.add(uid)
                versions = self.versions[uid]
                last = versions[-1]
                result: SelectionResult = last["result"]
                payload = self._payloads.get(uid)
                step += 1
                if payload is None:
                    entry = {
                        "kind": "recomputation",
                        "event_bar": update_bar, "info_time": update_time,
                        "step": step, "uid": uid,
                        "subject": result.task_id, "version": last["version"] + 1,
                        "computed_changes": [],
                        "note": "dependent registered without payload; not "
                                "recomputable — no propagation claimed",
                        "rule": "R:SP-20 recomputation, not patch",
                    }
                    self.revisions.append(entry)
                    log.append(entry)
                    continue
                new_result = self._recompute(payload, update_bar, update_time)
                changes = _diff_results(result, new_result)
                new_version = {
                    "version": last["version"] + 1,
                    "info_bar": update_bar,
                    "result": new_result,
                    "computed_changes": changes,
                    "recomputable": True,
                }
                versions.append(new_version)
                self.results.append(new_result)
                entry = {
                    "kind": "recomputation",
                    "event_bar": update_bar, "info_time": update_time,
                    "step": step, "uid": uid, "subject": result.task_id,
                    "version": new_version["version"],
                    "selected_before": result.selected_id,
                    "selected_after": new_result.selected_id,
                    "status_before": result.status,
                    "status_after": new_result.status,
                    "computed_changes": changes,
                    "cascade_from": sorted(frontier & self._deps_of(uid)),
                    "rule": "R:SP-20 recomputation, not patch",
                }
                self.revisions.append(entry)
                log.append(entry)
                # this result's dependents are reconsidered along the
                # registered result-dependency edges (transitive A -> B -> C):
                # a dependent of a recomputed result is never "unaffected"
                next_frontier.add(uid)
            frontier = next_frontier
        return log

    def _deps_of(self, uid: str) -> set:
        versions = self.versions.get(uid)
        last = versions[-1] if versions else None
        result = last["result"] if last else None
        return (set(self._result_deps.get(uid, ()))
                | set(self._payload_ids.get(uid, ()))
                | set((result.dependencies or []) if result else ()))

    def _find_dependency_cycle(self) -> List[str]:
        """Explicit cycle detection over registered result-dependency edges
        (consolidation V1 task §5).  Returns the cycle path, or []."""
        WHITE, GREY, BLACK = 0, 1, 2
        color = {uid: WHITE for uid in self.versions}
        stack: List[str] = []

        def _dfs(uid: str) -> List[str]:
            color[uid] = GREY
            stack.append(uid)
            for dep in sorted(self._result_deps.get(uid, ())):
                if dep not in color:
                    continue                      # unregistered name: not an edge
                if color[dep] == GREY:
                    return stack[stack.index(dep):] + [dep]
                if color[dep] == WHITE:
                    found = _dfs(dep)
                    if found:
                        return found
            stack.pop()
            color[uid] = BLACK
            return []

        for uid in sorted(color):
            if color[uid] == WHITE:
                found = _dfs(uid)
                if found:
                    return found
        return []

    def _mark_broken(self, candidate_id: str, info_bar: int,
                     info_time: Optional[pd.Timestamp],
                     event_ref: Optional[str] = None) -> None:
        """Apply a recorded break fact to the stored world copies so that
        recomputation sees the structural state as of the update boundary.

        END-TO-END CONSOLIDATION V1 (audit F): transitions reach candidates
        referenced through ANY payload shape — ``points``, ``claims_points``,
        and ``refs_by_view`` (T-S2-only recording must persist too).  The
        transition cites its authorizing ``event_ref`` so pre-event state
        queries can exclude the event's own transition.
        """
        seen: set = set()
        for payload in self._payloads.values():
            for p in _payload_points(payload):
                if id(p) in seen:
                    continue
                seen.add(id(p))
                if getattr(p, "candidate_id", None) == candidate_id:
                    # append-only transition; earlier history preserved
                    p.add_transition(info_bar, STATUS_BROKEN,
                                     info_time=info_time,
                                     note="break fact (SP-20)",
                                     event_ref=event_ref)

    def restore_history(self, candidates: Sequence[object]) -> int:
        """CAUSAL-STATE INTEGRATION V1: re-apply every recorded lifecycle
        transition to regenerated candidate copies with matching identity.

        Regenerating candidates must not erase previously observed
        transitions, and a historically broken reference must never come back
        as a fresh confirmed reference without a genuine new event.  Returns
        the number of transitions re-applied.

        END-TO-END CONSOLIDATION V1 (audit F): transition sources cover every
        payload shape (``points``, ``claims_points``, ``refs_by_view``) and
        carry their authorizing ``event_ref`` — lifecycle state is
        recoverable independently of which task payload referenced the
        candidate.
        """
        applied = 0
        # consolidation V1 (perf-neutral): identity index over the regenerated
        # candidates — the previous nested scan was O(payloads x points x
        # candidates) record walks per restore
        targets: Dict[str, List[object]] = {}
        for c in candidates:
            pid = getattr(c, "candidate_id", None)
            if pid:
                targets.setdefault(pid, []).append(c)
        seen_trans: set = set()
        for payload in self._payloads.values():
            for p in _payload_points(payload):
                pid = getattr(p, "candidate_id", None)
                if not pid or pid not in targets:
                    continue
                for t in getattr(p, "status_transitions", []) or []:
                    key = (pid, t.info_bar, t.status, t.info_time, t.event_ref)
                    if key in seen_trans:
                        continue
                    seen_trans.add(key)
                    for c in targets[pid]:
                        have = {(x.info_bar, x.status, x.info_time, x.event_ref)
                                for x in getattr(c, "status_transitions", [])}
                        if (t.info_bar, t.status, t.info_time,
                                t.event_ref) not in have:
                            c.add_transition(t.info_bar, t.status,
                                             info_time=t.info_time,
                                             by=t.by, note=t.note,
                                             event_ref=t.event_ref)
                            applied += 1
        return applied

    def _recompute(self, payload: dict, update_bar: int,
                   update_time: Optional[pd.Timestamp]) -> SelectionResult:
        kind = payload.get("kind")
        if kind == "T-S1":
            return task_s1_structural_reference(
                payload["points"], payload["legs"], update_bar, payload["rep"],
                payload["role"], payload["policy"], payload.get("policy_id"),
                payload.get("allow_provisional", False),
                state_id_prefix=payload.get("state_id_prefix", "S1"),
                decision_time=payload.get("decision_time", update_time),
                axis=payload.get("axis"))
        if kind == "T-S5":
            return task_s5_falsifier(
                payload["claims"], payload["points"], payload["legs"],
                update_bar, state_id_prefix=payload.get("state_id_prefix", "S5"),
                decision_time=payload.get("decision_time", update_time),
                axis=payload.get("axis"))
        if kind == "T-S3":
            return task_s3_entry_leg(
                payload["coarse_leg"], payload["fine_legs"], update_bar,
                payload["rep"], payload.get("continuation_condition"),
                payload.get("policy"),
                state_id_prefix=payload.get("state_id_prefix", "S3"),
                decision_time=payload.get("decision_time", update_time),
                axis=payload.get("axis"))
        if kind == "T-S2":
            # CAUSAL-STATE INTEGRATION V1: replay preserves ALL declared task
            # parameters — provisional eligibility policy and tie policy are
            # part of the recorded task contract and must survive recomputation.
            # consolidation V1: ``event_ref`` reconstructs the PRE_EVENT_STATE
            # on replay — the event's own transition never changes its binding.
            return task_s2_event_binding(
                payload["event_bar"], payload["close_price"],
                payload["refs_by_view"], update_bar,
                tie_bound=payload.get("tie_bound", False),
                prev_close=payload.get("prev_close"),
                state_id_prefix=payload.get("state_id_prefix", "S2"),
                event_time=payload.get("event_time"),
                tie_policy=payload.get("tie_policy", TIE_CROSS_EQUAL_UNBOUND),
                allow_provisional=payload.get("allow_provisional", False),
                event_ref=payload.get("event_ref"),
                axis=payload.get("axis"))
        raise ValueError(f"payload kind {kind!r} not recomputable")

    def snapshot(self) -> dict:
        # CAUSAL-STATE INTEGRATION V1: dependency-coverage tracking — a
        # dependent registered without a recomputation payload is INCOMPLETE
        # COVERAGE and is counted, never silently dropped or claimed.
        missing = [uid for uid, versions in self.versions.items()
                   if not versions[-1].get("recomputable", True)]
        return {
            "n_results": len(self.results),
            "n_events": len(self.events),
            "n_revisions": len(self.revisions),
            "justified": sum(1 for r in self.results if r.status == "justified"),
            "unresolved": sum(1 for r in self.results if r.status == "unresolved"),
            "empty": sum(1 for r in self.results if r.status == "empty"),
            "falsified": sum(1 for r in self.results if r.status == "falsified"),
            "n_result_versions": sum(len(v) for v in self.versions.values()),
            "n_dependents_without_payload": len(missing),
            "incomplete_dependency_coverage": missing[:50],
            "n_result_dependency_edges": sum(
                len(v) for v in self._result_deps.values()),
            "dependency_cycles_detected": sum(
                1 for r in self.revisions if r.get("kind") == "dependency-cycle"),
        }


def _payload_points(payload: dict) -> List[object]:
    """Every point-candidate a stored task references — ANY payload shape
    (``points``, ``claims_points``, ``refs_by_view``): lifecycle transitions
    must persist regardless of which task recorded the candidate
    (consolidation V1, audit F)."""
    pts: List[object] = []
    for key in ("points", "claims_points"):
        pts.extend(payload.get(key) or [])
    for refs in (payload.get("refs_by_view") or {}).values():
        pts.extend(refs or [])
    return pts


def _payload_ids(payload: dict) -> set:
    """Every candidate/leg id a stored task consumed (audit D5 dependency refs)."""
    ids: set = set()
    for p in _payload_points(payload):
        ids.add(getattr(p, "candidate_id", None))
    for key in ("legs", "fine_legs"):
        for l in payload.get(key) or []:
            ids.add(getattr(l, "leg_id", None))
    for key in ("coarse_leg",):
        l = payload.get(key)
        if l is not None:
            ids.add(getattr(l, "leg_id", None))
    return {i for i in ids if i}


def _diff_results(old: SelectionResult, new: SelectionResult) -> List[dict]:
    """Actual computed differences between two result versions (audit D5)."""
    changes: List[dict] = []
    if old.status != new.status:
        changes.append({"field": "status", "before": old.status,
                        "after": new.status})
    if old.selected_id != new.selected_id:
        changes.append({"field": "selected_id", "before": old.selected_id,
                        "after": new.selected_id})
    if set(old.survivors) != set(new.survivors):
        changes.append({"field": "survivors",
                        "before": sorted(old.survivors),
                        "after": sorted(new.survivors)})
    old_codes = {e.candidate_id: e.code for e in old.excluded}
    new_codes = {e.candidate_id: e.code for e in new.excluded}
    if old_codes != new_codes:
        changed_ids = sorted(set(old_codes) | set(new_codes), key=str)
        diffs = [{"candidate_id": cid,
                  "before": old_codes.get(cid), "after": new_codes.get(cid)}
                 for cid in changed_ids if old_codes.get(cid) != new_codes.get(cid)]
        # full candidate-level detail lives in the candidate ledger; the
        # revision keeps a bounded sample plus the exact count (audit D6)
        changes.append({"field": "exclusions", "n_changed": len(diffs),
                        "diffs": diffs[:20]})
    # consolidation V1 (task §3/§4): binding kinds and policy identity are
    # part of the result's meaning and MUST appear in difference accounting
    if old.binding_kinds != new.binding_kinds:
        changes.append({"field": "binding_kinds",
                        "before": dict(old.binding_kinds),
                        "after": dict(new.binding_kinds)})
    if old.policy_refs != new.policy_refs:
        changes.append({"field": "policy_refs",
                        "before": list(old.policy_refs),
                        "after": list(new.policy_refs)})
    if old.policy_snapshots != new.policy_snapshots:
        pv_old = {k: (v.get("version"), v.get("value"))
                  for k, v in old.policy_snapshots.items()}
        pv_new = {k: (v.get("version"), v.get("value"))
                  for k, v in new.policy_snapshots.items()}
        if pv_old != pv_new:
            changes.append({"field": "policy_snapshots",
                            "before": pv_old, "after": pv_new})
    return changes


# --------------------------------------------------------------------------
# Candidate-level serialization (audit D6 / §7 candidate ledger)
# --------------------------------------------------------------------------

def candidate_record(c: object, *, task_id: str = "", run_id: str = "",
                     boundary: str = "", decision_bar: Optional[int] = None,
                     decision_time: Optional[pd.Timestamp] = None,
                     eligible: Optional[bool] = None,
                     exclusion: Optional[Exclusion] = None,
                     selected: bool = False,
                     unresolved_reason: Optional[str] = None) -> dict:
    """Serializable row covering the full coverage-evidence contract:
    candidate identity, representation identity, availability information,
    historical status, task eligibility, exclusion reason, and the
    selected/unresolved state.  Coverage claims are verifiable from these
    rows (one row per candidate per run) — not from aggregate counts."""
    return {
        "run_id": run_id,
        "boundary": boundary,
        "task_id": task_id,
        "decision_bar": decision_bar,
        "decision_time": None if decision_time is None else str(decision_time),
        "candidate_id": _cid(c),
        "start_id": getattr(c, "start_id", None),   # leg support (consolidation V1 §6)
        "end_id": getattr(c, "end_id", None),
        "representation_id": getattr(getattr(c, "rep", None), "rep_id", None),
        "side": getattr(c, "side", None),
        "level": getattr(c, "level", None),
        "occurrence_bar": getattr(c, "occurrence_bar", None),
        "knowable_bar": getattr(c, "knowable_bar", None),
        "occurrence_time": _ts(getattr(c, "occurrence_time", None)),
        "knowable_time": _ts(getattr(c, "knowable_time", None)),
        "status_at_decision": (
            c.status_at(decision_bar, decision_time)
            if hasattr(c, "status_at") else getattr(c, "status", None)),
        "status_final": getattr(c, "status", None),
        "same_bar_order": getattr(c, "same_bar_order", None),
        "same_bar_evidence": getattr(c, "same_bar_evidence", None),
        "leg_direction": getattr(c, "direction", None),
        "leg_depth": getattr(c, "depth", None),
        "leg_t0_time": _ts(getattr(c, "t0_time", None)),
        "leg_t1_time": _ts(getattr(c, "t1_time", None)),
        "eligible": eligible,
        "exclusion_code": None if exclusion is None else exclusion.code,
        "exclusion_detail": None if exclusion is None else exclusion.detail,
        "selected": selected,
        "unresolved_reason": unresolved_reason,
    }


def _ts(v: Optional[pd.Timestamp]) -> Optional[str]:
    return None if v is None else str(v)
