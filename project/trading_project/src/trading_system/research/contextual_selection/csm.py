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
    initial_status: str = ""           # status at construction (D3 history)

    def __post_init__(self) -> None:
        if not self.initial_status:
            self.initial_status = self.status

    @property
    def view_id(self) -> str:
        return self.rep.view_id

    def add_transition(self, info_bar: int, status: str,
                       info_time: Optional[pd.Timestamp] = None,
                       by: Optional[str] = None, note: str = "") -> None:
        self.status_transitions.append(
            StatusTransition(info_bar=info_bar, status=status,
                             info_time=info_time, by=by, note=note))
        self.status = status  # final-field mirror for callers that read it

    def status_at(self, info_bar: Optional[int] = None,
                  info_time: Optional[pd.Timestamp] = None) -> str:
        """Reconstruct the status knowable at the requested boundary (D3).

        Falls back to the final ``status`` field when no transition history
        exists (hand-built candidates); later supersession recorded as a
        transition never rewrites the earlier provisional state.
        """
        if not self.status_transitions:
            return self.status
        applicable = []
        for t in self.status_transitions:
            if info_bar is not None and t.info_bar > info_bar:
                continue
            if (info_time is not None and t.info_time is not None
                    and t.info_time > info_time):
                continue
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
    """

    def __init__(self) -> None:
        self._entries: Dict[str, dict] = {}

    def register(self, policy_id: str, description: str, value: object,
                 sensitivity_required: bool = True,
                 kind: str = KIND_RESEARCH) -> None:
        if kind not in POLICY_KINDS:
            raise ValueError(f"bad policy kind {kind!r}")
        self._entries[policy_id] = {
            "policy_id": policy_id,
            "description": description,
            "value": value,
            "class": CLASS_O,
            "kind": kind,
            "sensitivity_required": sensitivity_required,
        }

    def ref(self, policy_id: str) -> str:
        if policy_id not in self._entries:
            raise KeyError(f"policy {policy_id!r} not registered (SP-18)")
        return f"O:{policy_id}"

    def get(self, policy_id: str) -> dict:
        return self._entries[policy_id]

    def items(self) -> Iterable[Tuple[str, dict]]:
        return self._entries.items()


# --------------------------------------------------------------------------
# Shared information-time axis (audit D1)
# --------------------------------------------------------------------------

def available_at(c: object, *,
                 as_of_bar: Optional[int] = None,
                 as_of_time: Optional[pd.Timestamp] = None) -> bool:
    """Availability of a candidate on a shared axis.

    Timestamps are the only axis allowed to cross view domains; bar indices
    are compared only inside one timeframe domain.  When both sides carry
    times, the time comparison governs (never raw cross-domain indices).
    """
    k_time = getattr(c, "knowable_time", None)
    if as_of_time is not None:
        if k_time is None:
            raise ValueError(
                "candidate lacks knowable_time; availability cannot be "
                "evaluated on the shared information-time axis (audit D1)")
        return bool(k_time <= as_of_time)
    if as_of_bar is not None:
        return bool(getattr(c, "knowable_bar") <= as_of_bar)
    raise ValueError("availability requires a shared axis "
                     "(as_of_time with candidate knowable_time, or as_of_bar)")


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
            know_time = (pd.Timestamp(times[min(i + k, n - 1)]) if times is not None
                         else None)
            cand = PointCandidate(
                candidate_id=f"{id_prefix}{rep.rep_id}|{side}@{i}",
                rep=rep,
                side=side,
                occurrence_bar=i,
                level=level,
                knowable_bar=i + k,
                status=STATUS_PROVISIONAL,
                occurrence_time=occ_time,
                knowable_time=know_time,
                same_bar_order="unresolved" if (is_high and is_low) else "resolved",
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

    def _emit(i: int, side: str, occ_i: int, level: float, status: str,
              order: str) -> None:
        occ_time = (pd.Timestamp(times[occ_i]) if times is not None else None)
        know_time = (pd.Timestamp(times[i])
                     if (times is not None and 0 <= i < len(times)) else None)
        cand = PointCandidate(
            candidate_id=f"{id_prefix}{rep.rep_id}|{side}@{occ_i}",
            rep=rep, side=side, occurrence_bar=occ_i, level=level,
            knowable_bar=i, status=status,
            occurrence_time=occ_time, knowable_time=know_time,
            same_bar_order=order)
        cand.add_transition(occ_i, STATUS_PROVISIONAL, info_time=occ_time,
                            note=f"F-T registered (tie={tie_policy})")
        if status == STATUS_CONFIRMED:
            cand.add_transition(i, STATUS_CONFIRMED, info_time=know_time,
                                note="F-T reversal >= tau")
        out.append(cand)

    for i in range(n):
        if ext_side is None:
            ext_side, ext_i, ext_level = "high", i, float(highs[i])
            ext_order = "resolved"
            continue
        if ext_side == "high":
            if tie_policy == TIE_FT_EQ_LAST:
                update = highs[i] >= ext_level
            else:
                update = highs[i] > ext_level  # TIE-FT-EQ-FIRST-V1
            reversal = ext_level - lows[i] >= tau
            if update and reversal:
                # same-bar both-sides: intrabar order unknowable (audit D4)
                if ambiguities is not None:
                    ambiguities.append({
                        "bar": i, "kind": "same-bar-extreme-vs-reversal",
                        "side": "high", "prior_extreme_bar": ext_i,
                        "prior_extreme": ext_level, "high": float(highs[i]),
                        "low": float(lows[i]), "tie_policy": tie_policy,
                        "note": "OHLC cannot order the intrabar high/low; "
                                "no sequence synthesized",
                    })
                ext_side, ext_i, ext_level = "high", i, float(highs[i])
                ext_order = "unresolved"
                continue
            if update:
                ext_side, ext_i, ext_level = "high", i, float(highs[i])
                ext_order = "resolved"
            elif reversal:
                _emit(i, "high", ext_i, ext_level, STATUS_CONFIRMED, ext_order)
                ext_side, ext_i, ext_level = "low", i, float(lows[i])
                ext_order = "resolved" if highs[i] <= ext_level or True else "resolved"
        else:
            if tie_policy == TIE_FT_EQ_LAST:
                update = lows[i] <= ext_level
            else:
                update = lows[i] < ext_level  # TIE-FT-EQ-FIRST-V1
            reversal = highs[i] - ext_level >= tau
            if update and reversal:
                if ambiguities is not None:
                    ambiguities.append({
                        "bar": i, "kind": "same-bar-extreme-vs-reversal",
                        "side": "low", "prior_extreme_bar": ext_i,
                        "prior_extreme": ext_level, "high": float(highs[i]),
                        "low": float(lows[i]), "tie_policy": tie_policy,
                        "note": "OHLC cannot order the intrabar high/low; "
                                "no sequence synthesized",
                    })
                ext_side, ext_i, ext_level = "low", i, float(lows[i])
                ext_order = "unresolved"
                continue
            if update:
                ext_side, ext_i, ext_level = "low", i, float(lows[i])
                ext_order = "resolved"
            elif reversal:
                _emit(i, "low", ext_i, ext_level, STATUS_CONFIRMED, ext_order)
                ext_side, ext_i, ext_level = "high", i, float(highs[i])
                ext_order = "resolved"
    if ext_side is not None:
        _emit(n + 1, ext_side, ext_i, ext_level, STATUS_PROVISIONAL, ext_order)
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
                    "bar": a.occurrence_bar, "kind": "same-bar-order-unresolved",
                    "pair": [a.candidate_id, b.candidate_id],
                    "note": "OHLC cannot order same-bar high/low; no directional "
                            "zero-duration leg synthesized",
                })
            continue
        if a.level == b.level:
            if ambiguities is not None:
                ambiguities.append({
                    "bar": a.occurrence_bar, "kind": "zero-amplitude-leg",
                    "pair": [a.candidate_id, b.candidate_id],
                    "note": "equal endpoints: direction not established",
                })
            continue
        direction = "up" if b.level > a.level else "down"
        legs.append(LegCandidate(
            leg_id=f"{rep.rep_id}|leg{a.occurrence_bar}-{b.occurrence_bar}",
            rep=rep,
            start_id=a.candidate_id, end_id=b.candidate_id,
            direction=direction,
            t0=a.occurrence_bar, t1=b.occurrence_bar,
            p_start=a.level, p_end=b.level,
            knowable_bar=max(a.knowable_bar, b.knowable_bar),
            completed=b.status == STATUS_CONFIRMED,
            t0_time=a.occurrence_time, t1_time=b.occurrence_time,
            knowable_time=max([t for t in (a.knowable_time, b.knowable_time)
                               if t is not None], default=None),
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
                     as_of_time: Optional[pd.Timestamp] = None
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
            if not available_at(c, as_of_bar=decision_bar, as_of_time=as_of_time):
                excluded.append(Exclusion(_cid(c), X_KNOW, "R:SP-01",
                                          f"knowable_bar={getattr(c, 'knowable_bar', '?')} "
                                          f"> t={decision_bar}"))
            else:
                passed.append(c)
    return passed, excluded


def sp05_containment(coarse: LegCandidate, fine: LegCandidate,
                     tie_inclusive: bool = True) -> str:
    """SP-05: contained | escaping | disjoint.  Boundary tie rule is a declared
    policy (SWS-06; TIE-BOUNDARIES-INCLUSIVE-V1 default): inclusive spans."""
    if fine.t1 < coarse.t0 or fine.t0 > coarse.t1:
        return "disjoint"
    if tie_inclusive:
        time_inside = coarse.t0 <= fine.t0 and fine.t1 <= coarse.t1
        price_inside = coarse.p_lo <= fine.p_lo and fine.p_hi <= coarse.p_hi
    else:
        time_inside = coarse.t0 < fine.t0 and fine.t1 < coarse.t1
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
                                 decision_time: Optional[pd.Timestamp] = None
                                 ) -> SelectionResult:
    """T-S1: which confirmed point is the reference for view V's current state.

    Roles (Pi_T, O-class): "origin-of-last-confirmed-leg" (SWS-02) or
    "last-confirmed-extreme".  Without a declared role the output is MP.
    The analytical direction of the resolved reference is derived from the
    supporting leg (audit D6) — never from note strings.
    """
    prov = ["R:SP-01", "R:SP-13", "R:SP-14", "F:H_T(confirmed,knowable,in-view)"]
    pregs: List[str] = []
    in_view = [p for p in points if p.rep.view_id == rep.view_id and p.rep.family == rep.family
               and p.rep.params == rep.params]
    others = [p for p in points if p not in in_view]
    excluded: List[Exclusion] = [Exclusion(p.candidate_id, X_SCALE, "R:SP-02",
                                           "not in view V") for p in others]
    passed, ex1 = sp01_knowability(in_view, decision_bar, allow_provisional,
                                   as_of_time=decision_time)
    excluded += ex1
    confirmed = [p for p in passed if p.status_at(decision_bar, decision_time)
                 == STATUS_CONFIRMED]
    view_legs = [l for l in legs
                 if l.rep.view_id == rep.view_id and l.rep.params == rep.params]
    confirmed_legs = [l for l in view_legs
                      if l.completed and l.knowable_bar <= decision_bar]

    def _deps(*ids: str) -> List[str]:
        return [i for i in ids if i]

    if not confirmed_legs and not confirmed:
        state = UnresolvedState(
            state_id=f"{state_id_prefix}-{decision_bar}", task="T-S1",
            decision_bar=decision_bar, survivors=[], excluded=excluded,
            reason_code=REASON_IC, evidence_needed="more history / confirmation",
            policy_refs=[], provenance=prov,
            dependents_blocked=["T-S5", "T-S4", "zone-context", "liquidity-objective"])
        return _mk("T-S1", decision_bar, "unresolved", None, [], excluded, state,
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
            return _mk("T-S1", decision_bar, "unresolved", None,
                       [p.candidate_id for p in confirmed], excluded, state,
                       prov, pregs, rep.rep_id, decision_time=decision_time)
        pregs.append(policy.ref(policy_id))
        if not confirmed_legs:
            state = UnresolvedState(
                state_id=f"{state_id_prefix}-{decision_bar}", task="T-S1",
                decision_bar=decision_bar,
                survivors=[p.candidate_id for p in confirmed], excluded=excluded,
                reason_code=REASON_IC, evidence_needed="no confirmed leg in view V yet",
                policy_refs=pregs, provenance=prov,
                dependents_blocked=["T-S5", "T-S4"])
            return _mk("T-S1", decision_bar, "unresolved", None,
                       [p.candidate_id for p in confirmed], excluded, state,
                       prov, pregs, rep.rep_id, decision_time=decision_time)
        last_leg = max(confirmed_legs, key=lambda l: (l.knowable_bar, l.t1))
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
            return _mk("T-S1", decision_bar, "unresolved", None, [],
                       excluded, state, prov, pregs, rep.rep_id,
                       dependencies=_deps(target_id, last_leg.leg_id),
                       direction=last_leg.direction,
                       decision_time=decision_time)
        for p in confirmed:
            if p.candidate_id != target_id:
                excluded.append(Exclusion(p.candidate_id, X_POL, f"O:{policy_id}",
                                          "not the origin of the last confirmed leg"))
        return _mk("T-S1", decision_bar, "justified", target_id, [target_id],
                   excluded, None, prov, pregs, rep.rep_id,
                   dependents=["T-S5-falsifier", "T-S4-base", "zone-context",
                               "liquidity-objective"],
                   notes=[f"last_confirmed_leg={last_leg.leg_id}",
                          f"role={role} (O-class; SWS-02: not a market claim)"],
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
            return _mk("T-S1", decision_bar, "unresolved", None, [], excluded,
                       state, prov, pregs, rep.rep_id, decision_time=decision_time)
        best = max(confirmed, key=lambda p: p.knowable_bar)
        for p in confirmed:
            if p.candidate_id != best.candidate_id:
                excluded.append(Exclusion(p.candidate_id, X_POL, "R:within-class:knowable_bar",
                                          "less recent confirmed point"))
        return _mk("T-S1", decision_bar, "justified", best.candidate_id,
                   [best.candidate_id], excluded, None, prov, pregs, rep.rep_id,
                   notes=["role=last-confirmed-extreme"],
                   dependencies=_deps(best.candidate_id),
                   decision_time=decision_time)
    state = UnresolvedState(
        state_id=f"{state_id_prefix}-{decision_bar}", task="T-S1",
        decision_bar=decision_bar, survivors=[p.candidate_id for p in confirmed],
        excluded=excluded, reason_code=REASON_MP,
        evidence_needed=f"declared role for question (role={role!r} not recognized)",
        policy_refs=[], provenance=prov)
    return _mk("T-S1", decision_bar, "unresolved", None,
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
                          tie_policy: str = TIE_CROSS_EQUAL_UNBOUND) -> SelectionResult:
    """T-S2: which references does a closed-bar event bind to (SP-03)?

    The binding set keeps all members; no ranking (SWS-05).  When
    ``prev_close`` is provided only FRESH crossings count (the previous close
    was not yet beyond the level); without it the bar is the declared single
    event bar (golden cases W5/W10).

    Audit D1: references from MULTIPLE views are compared on the shared
    information-time axis only — ``event_time`` is then mandatory and every
    reference must carry ``knowable_time``.  Raw bar indices from different
    timeframe domains are never compared; an unavailable reference is
    excluded X-KNOW and can never enter an earlier event's binding.
    """
    prov = ["R:SP-03", "F:close-basis (declared; wick variant open)",
            f"tie={tie_policy}"]
    bound: List[str] = []
    excluded: List[Exclusion] = []
    per_view: Dict[str, List[str]] = {}
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
        knowable, late = [], []
        for r in refs:
            ok = available_at(r, as_of_bar=event_bar, as_of_time=event_time)
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
    if not bound:
        return _mk("T-S2", decision_bar, "empty", None, [], excluded, None, prov,
                   [], f"event@{event_bar}",
                   notes=["no event at these scales",
                          f"binding per view: {per_view}"],
                   dependencies=[r.candidate_id for refs in refs_by_view.values()
                                 for r in refs],
                   decision_time=event_time)
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
    return _mk("T-S2", decision_bar, status, bound[0] if len(bound) == 1 else None,
               bound, excluded, unresolved, prov, [], f"event@{event_bar}",
               dependents=["view-trend-state", "falsifier-evaluation", "reclaim-check"],
               notes=[f"binding per view: {per_view}"],
               dependencies=[r.candidate_id for refs in refs_by_view.values()
                             for r in refs],
               decision_time=event_time)


def task_s3_entry_leg(coarse_leg: LegCandidate, fine_legs: Sequence[LegCandidate],
                      decision_bar: int, rep: Representation,
                      continuation_condition: Optional[Tuple[str, str]] = None,
                      policy: Optional[PolicyRegistry] = None,
                      state_id_prefix: str = "S3") -> SelectionResult:
    """T-S3: which completed fine leg contained in the coarse leg times an entry.

    continuation_condition: optional declared O policy (e.g. ("direction",
    "down") meaning a continuation-long entry uses completed down-legs inside
    an up-leg).  Depth vs recency is never decided here (SWS-07): without a
    declared policy the surviving pair is emitted as MP (or EP when a learned
    preference would be needed).
    """
    prov = ["R:SP-05", "R:SP-08", "R:SP-01", "R:SP-06"]
    pregs: List[str] = []
    excluded: List[Exclusion] = []
    survivors: List[LegCandidate] = []
    for f in fine_legs:
        if f.knowable_bar > decision_bar:
            excluded.append(Exclusion(f.leg_id, X_KNOW, "R:SP-01",
                                      f"knowable {f.knowable_bar} > t={decision_bar}"))
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
        ("knowable", lambda f: f.knowable_bar <= decision_bar),
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
        return _mk("T-S3", decision_bar, "unresolved", None, [], excluded, state,
                   prov, pregs, rep.rep_id, dependencies=deps)
    if len(survivors) == 1:
        return _mk("T-S3", decision_bar, "justified", surv_ids[0], surv_ids,
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
    return _mk("T-S3", decision_bar, "unresolved", None, surv_ids, excluded,
               state, prov, pregs, rep.rep_id,
               notes=["factual differences preserved: " + "; ".join(diffs),
                      "depth-vs-recency is SWS-07 open (MP/EP), not a fact"],
               dependencies=deps)


def task_s5_falsifier(claims: Sequence[dict], points: Sequence[PointCandidate],
                      legs: Sequence[LegCandidate], decision_bar: int,
                      state_id_prefix: str = "S5") -> SelectionResult:
    """T-S5 / SP-04: map each reference-form claim of interpretation I to its
    falsifier reference.  Claims are dicts:
      {"interpretation": "I1", "view": "C", "role": "...", "direction": "up"}
    Supported roles: "origin-of-last-confirmed-leg", "low-of-current-leg",
    "high-of-current-leg", "last-confirmed-extreme".  A claim not written in
    reference terms yields MP (SWS-08).

    Audit D6: direction is taken from the claim's declared interpretation
    semantics (the movement representation), validated structurally against
    the supporting leg; a missing or inconsistent direction yields an
    explicit unresolved state (never inferred from note strings).  A
    falsifier reference recorded as structurally broken at the decision bar
    FALSIFIES the claim (computed task-level effect).
    """
    prov = ["R:SP-04", "F:given I written in reference terms (SWS-08)"]
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
                and p.status_at(decision_bar) == STATUS_BROKEN)

    for claim in claims:
        role = claim.get("role", "")
        view = claim.get("view", "")
        interp = claim.get("interpretation", "?")
        vlegs = [l for l in legs_by_view.get(view, [])
                 if l.completed and l.knowable_bar <= decision_bar]
        if role == "origin-of-last-confirmed-leg":
            if not vlegs:
                excluded.append(Exclusion(f"{interp}:{role}", X_STATE, "R:SP-04",
                                          "no confirmed leg in view"))
                continue
            last = max(vlegs, key=lambda l: (l.knowable_bar, l.t1))
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
                           notes=notes, dependencies=deps)
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
            vpts = [p for p in points if p.view_id == view
                    and p.status_at(decision_bar) == STATUS_CONFIRMED
                    and p.knowable_bar <= decision_bar]
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
                   dependencies=deps)
    if not resolved:
        state = UnresolvedState(
            state_id=f"{state_id_prefix}-{decision_bar}", task="T-S5",
            decision_bar=decision_bar, survivors=[], excluded=excluded,
            reason_code=REASON_MP,
            evidence_needed="write I in reference terms (SWS-08) or declare the reading as O/S-ambiguous",
            policy_refs=[], provenance=prov)
        return _mk("T-S5", decision_bar, "unresolved", None, [], excluded, state,
                   prov, [], "claims", notes=notes, dependencies=deps)
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
               notes=notes, dependencies=deps)


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
        return uid

    def record_event(self, event_bar: int, kind: str, detail: str,
                     affected_ids: Sequence[str],
                     event_time: Optional[pd.Timestamp] = None) -> None:
        self.events.append({"event_bar": event_bar, "kind": kind,
                            "detail": detail, "affected_ids": list(affected_ids),
                            "event_time": event_time})

    def record_change(self, info_bar: int, target_id: str, new_state: str,
                      detail: str = "",
                      info_time: Optional[pd.Timestamp] = None) -> None:
        """Upstream FACT (append-only): a structural break ('broken') or a
        newly knowable item ('knowable').  Facts drive propagation; they are
        not themselves claimed as recomputation."""
        self.revisions.append({
            "kind": "change-fact", "info_bar": info_bar, "info_time": info_time,
            "target": target_id, "new_state": new_state, "detail": detail,
            "rule": "R:SP-20 upstream fact (append-only)",
        })

    # ---- real propagation ---------------------------------------------

    def propagate(self, update_bar: int, changed_ids: Sequence[str],
                  changed_states: Optional[Dict[str, str]] = None,
                  update_time: Optional[pd.Timestamp] = None) -> List[dict]:
        """SP-20: recompute every dependent of ``changed_ids`` from its
        stored inputs as of ``update_bar`` and append new versions with the
        ACTUAL computed differences.  Returns the propagation entries.

        ``changed_states`` (optional) maps candidate id -> structural state to
        apply as an append-only change fact before recomputation (e.g.
        {"L_b": "broken"}); the state is recorded as a fact, then every
        dependent is re-evaluated — the logged differences are computed from
        the recomputed results, never supplied by the caller.
        """
        log: List[dict] = []
        changed = set(changed_ids)
        if changed_states:
            for cid, st in changed_states.items():
                self.record_change(update_bar, cid, st,
                                   info_time=update_time)
                if st == STATUS_BROKEN:
                    self._mark_broken(cid, update_bar, update_time)
        step = 0
        for uid, versions in self.versions.items():
            last = versions[-1]
            result: SelectionResult = last["result"]
            input_ids = self._payload_ids.get(uid, set())
            if not changed.intersection(set(result.dependencies or []) | input_ids):
                continue
            payload = self._payloads.get(uid)
            if payload is None:
                step += 1
                entry = {
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
            step += 1
            entry = {
                "event_bar": update_bar, "info_time": update_time,
                "step": step, "uid": uid, "subject": result.task_id,
                "version": new_version["version"],
                "selected_before": result.selected_id,
                "selected_after": new_result.selected_id,
                "status_before": result.status,
                "status_after": new_result.status,
                "computed_changes": changes,
                "rule": "R:SP-20 recomputation, not patch",
            }
            self.revisions.append(entry)
            log.append(entry)
        return log

    def _mark_broken(self, candidate_id: str, info_bar: int,
                     info_time: Optional[pd.Timestamp]) -> None:
        """Apply a recorded break fact to the stored world copies so that
        recomputation sees the structural state as of the update boundary."""
        for payload in self._payloads.values():
            for key in ("points", "claims_points"):
                for p in payload.get(key) or []:
                    if getattr(p, "candidate_id", None) == candidate_id:
                        # append-only transition; earlier history preserved
                        p.add_transition(info_bar, STATUS_BROKEN,
                                         info_time=info_time,
                                         note="break fact (SP-20)")

    def _recompute(self, payload: dict, update_bar: int,
                   update_time: Optional[pd.Timestamp]) -> SelectionResult:
        kind = payload.get("kind")
        if kind == "T-S1":
            return task_s1_structural_reference(
                payload["points"], payload["legs"], update_bar, payload["rep"],
                payload["role"], payload["policy"], payload.get("policy_id"),
                payload.get("allow_provisional", False),
                state_id_prefix=payload.get("state_id_prefix", "S1"),
                decision_time=update_time)
        if kind == "T-S5":
            return task_s5_falsifier(
                payload["claims"], payload["points"], payload["legs"],
                update_bar, state_id_prefix=payload.get("state_id_prefix", "S5"))
        if kind == "T-S3":
            return task_s3_entry_leg(
                payload["coarse_leg"], payload["fine_legs"], update_bar,
                payload["rep"], payload.get("continuation_condition"),
                payload.get("policy"),
                state_id_prefix=payload.get("state_id_prefix", "S3"))
        if kind == "T-S2":
            return task_s2_event_binding(
                payload["event_bar"], payload["close_price"],
                payload["refs_by_view"], update_bar,
                tie_bound=payload.get("tie_bound", False),
                prev_close=payload.get("prev_close"),
                state_id_prefix=payload.get("state_id_prefix", "S2"),
                event_time=payload.get("event_time"))
        raise ValueError(f"payload kind {kind!r} not recomputable")

    def snapshot(self) -> dict:
        return {
            "n_results": len(self.results),
            "n_events": len(self.events),
            "n_revisions": len(self.revisions),
            "justified": sum(1 for r in self.results if r.status == "justified"),
            "unresolved": sum(1 for r in self.results if r.status == "unresolved"),
            "empty": sum(1 for r in self.results if r.status == "empty"),
            "falsified": sum(1 for r in self.results if r.status == "falsified"),
            "n_result_versions": sum(len(v) for v in self.versions.values()),
        }


def _payload_ids(payload: dict) -> set:
    """Every candidate/leg id a stored task consumed (audit D5 dependency refs)."""
    ids: set = set()
    for key in ("points", "claims_points"):
        for p in payload.get(key) or []:
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
        "representation_id": getattr(getattr(c, "rep", None), "rep_id", None),
        "side": getattr(c, "side", None),
        "occurrence_bar": getattr(c, "occurrence_bar", None),
        "knowable_bar": getattr(c, "knowable_bar", None),
        "occurrence_time": _ts(getattr(c, "occurrence_time", None)),
        "knowable_time": _ts(getattr(c, "knowable_time", None)),
        "status_at_decision": (
            c.status_at(decision_bar, decision_time)
            if hasattr(c, "status_at") else getattr(c, "status", None)),
        "status_final": getattr(c, "status", None),
        "same_bar_order": getattr(c, "same_bar_order", None),
        "eligible": eligible,
        "exclusion_code": None if exclusion is None else exclusion.code,
        "exclusion_detail": None if exclusion is None else exclusion.detail,
        "selected": selected,
        "unresolved_reason": unresolved_reason,
    }


def _ts(v: Optional[pd.Timestamp]) -> Optional[str]:
    return None if v is None else str(v)
