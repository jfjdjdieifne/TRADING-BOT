"""CSM core: model, generators, seed procedures, task cards, ledger.

Claim references (knowledge_foundation, jfjdjdieifne/test @ 6c8bf6fd):
CSM-*, SWS-*, SP-*, LRN-* — see files 15-18.  This module implements the
deterministic, non-learned subset (file 18 §18.9: SP-01..SP-20, unresolved
emission, dependency-aware recomputation are implementable without learning).
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
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

    @property
    def view_id(self) -> str:
        return self.rep.view_id


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
    status: str                       # "justified" | "unresolved" | "empty"
    selected_id: Optional[str]
    survivors: List[str]
    excluded: List[Exclusion]
    unresolved: Optional[UnresolvedState]
    provenance: List[str]
    policy_refs: List[str]
    representation_id: str
    dependents: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

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
    """SP-18: declared policy registry.  Every O-class choice is recorded here."""

    def __init__(self) -> None:
        self._entries: Dict[str, dict] = {}

    def register(self, policy_id: str, description: str, value: object,
                 sensitivity_required: bool = True) -> None:
        self._entries[policy_id] = {
            "policy_id": policy_id,
            "description": description,
            "value": value,
            "class": CLASS_O,
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
# L1 generators (file 16 §16.2) — declared parameters only, causal, replay-safe
# --------------------------------------------------------------------------

def fk_turning_points(bars: pd.DataFrame, k: int, rep: Representation,
                      id_prefix: str = "") -> List[PointCandidate]:
    """F-K k-bar pivot with causal confirmation (SP-13, SWS-04).

    A bar i is a turning-point candidate iff its high/low is the unique
    extreme of the LEFT window [i-k, i] (the right edge is not yet observable
    at i).  The candidate is registered as PROVISIONAL at i; its confirmation
    bar is i+k (SP-13: knowable_bar is the confirmation bar, not the
    occurrence bar).  SWS-04c: a provisional same-side point is SUPERSEDED if
    a strictly more extreme same-side point occurs inside (i, i+k]; it stays
    in the record.  Replay consistency (SWS-04d): a run truncated at bar T
    reproduces every stored output at bars <= T.
    """
    if k < 1:
        raise ValueError("k must be >= 1 (declared policy slot, no default)")
    highs = bars["high"].to_numpy(dtype=float)
    lows = bars["low"].to_numpy(dtype=float)
    n = len(bars)
    out: List[PointCandidate] = []
    pending: List[PointCandidate] = []

    def _flush(upto_bar: int) -> None:
        for p in pending:
            if (p.status == STATUS_PROVISIONAL and p.knowable_bar <= upto_bar):
                p.status = STATUS_CONFIRMED

    for i in range(n):
        _flush(i)
        lo_i = max(0, i - k)
        window_h = highs[lo_i : i + 1]
        window_l = lows[lo_i : i + 1]
        is_high = (highs[i] == window_h.max()
                   and int((window_h == highs[i]).sum()) == 1)
        is_low = (lows[i] == window_l.min()
                  and int((window_l == lows[i]).sum()) == 1)
        for side, flag, level in (("high", is_high, float(highs[i])),
                                  ("low", is_low, float(lows[i]))):
            if not flag:
                continue
            cand = PointCandidate(
                candidate_id=f"{id_prefix}{rep.rep_id}|{side}@{i}",
                rep=rep,
                side=side,
                occurrence_bar=i,
                level=level,
                knowable_bar=i + k,
                status=STATUS_PROVISIONAL,
            )
            # SWS-04c: supersession inside the confirmation window
            for p in pending:
                if (p.side == side and p.status == STATUS_PROVISIONAL
                        and p.occurrence_bar < i < p.knowable_bar):
                    more_extreme = (level > p.level) if side == "high" else (level < p.level)
                    if more_extreme:
                        p.status = STATUS_SUPERSEDED
                        p.superseded_by = cand.candidate_id
            out.append(cand)
            pending.append(cand)
    _flush(n - 1)  # nothing beyond the last observed bar may confirm
    return out


def ft_turning_points(bars: pd.DataFrame, tau: float, rep: Representation,
                      id_prefix: str = "") -> List[PointCandidate]:
    """F-T threshold reversal: a point is registered at the running extreme
    when price reverses from it by the declared amount tau (absolute price
    units; the unit choice is a declared O policy).  knowable_bar = the bar
    where the reversal first reaches tau (SP-13).  Bars never reversing leave
    the running extreme unregistered (it is still a candidate at the end and
    is emitted as provisional).
    """
    if tau <= 0:
        raise ValueError("tau must be > 0 (declared policy slot, no default)")
    closes = bars["close"].to_numpy(dtype=float)
    highs = bars["high"].to_numpy(dtype=float)
    lows = bars["low"].to_numpy(dtype=float)
    n = len(bars)
    out: List[PointCandidate] = []
    ext_side: Optional[str] = None
    ext_i = 0
    ext_level = 0.0
    for i in range(n):
        if ext_side is None:
            ext_side, ext_i, ext_level = "high", i, float(highs[i])
            continue
        if ext_side == "high":
            if highs[i] >= ext_level:
                ext_side, ext_i, ext_level = "high", i, float(highs[i])
            elif ext_level - lows[i] >= tau:
                out.append(PointCandidate(
                    candidate_id=f"{id_prefix}{rep.rep_id}|high@{ext_i}",
                    rep=rep, side="high", occurrence_bar=ext_i,
                    level=ext_level, knowable_bar=i, status=STATUS_CONFIRMED))
                ext_side, ext_i, ext_level = "low", i, float(lows[i])
        else:
            if lows[i] <= ext_level:
                ext_side, ext_i, ext_level = "low", i, float(lows[i])
            elif highs[i] - ext_level >= tau:
                out.append(PointCandidate(
                    candidate_id=f"{id_prefix}{rep.rep_id}|low@{ext_i}",
                    rep=rep, side="low", occurrence_bar=ext_i,
                    level=ext_level, knowable_bar=i, status=STATUS_CONFIRMED))
                ext_side, ext_i, ext_level = "high", i, float(highs[i])
    if ext_side is not None:
        out.append(PointCandidate(
            candidate_id=f"{id_prefix}{rep.rep_id}|{ext_side}@{ext_i}",
            rep=rep, side=ext_side, occurrence_bar=ext_i,
            level=ext_level, knowable_bar=n + 1, status=STATUS_PROVISIONAL))
    return out


def build_legs(points: Sequence[PointCandidate], rep: Representation,
               completed_only: bool = False) -> List[LegCandidate]:
    """SP-14 leg construction: consecutive alternating points."""
    pts = [p for p in points if p.status != STATUS_SUPERSEDED]
    pts = sorted(pts, key=lambda p: p.occurrence_bar)
    legs: List[LegCandidate] = []
    for a, b in zip(pts, pts[1:]):
        if a.side == b.side:
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
        ))
    if completed_only:
        legs = [l for l in legs if l.completed]
    return legs


# --------------------------------------------------------------------------
# Seed procedures (file 17)
# --------------------------------------------------------------------------

def _cid(c: object) -> str:
    return getattr(c, "candidate_id", None) or getattr(c, "leg_id")


def sp01_knowability(candidates: Sequence[object], decision_bar: int,
                     allow_provisional: bool = False
                     ) -> Tuple[List[object], List[Exclusion]]:
    """SP-01: X-KNOW when knowable_bar > t; X-STATE when provisional and the
    declared policy does not allow provisional use."""
    passed, excluded = [], []
    for c in candidates:
        st = getattr(c, "status", STATUS_CONFIRMED)
        if st == STATUS_SUPERSEDED:
            if getattr(c, "occurrence_bar", 0) > decision_bar:
                excluded.append(Exclusion(_cid(c), X_KNOW, "R:SP-01",
                                          f"occurrence {c.occurrence_bar} > t={decision_bar}"))
            else:
                excluded.append(Exclusion(_cid(c), X_SUPER, "R:SP-13/SWS-04c",
                                          "superseded inside confirmation window"))
        elif st == STATUS_PROVISIONAL:
            # a provisional point is visible at its occurrence bar; its confirmed
            # form is not yet knowable (SP-13).  Default policy excludes it with
            # X-STATE (SWS-04a; golden case W4).
            if getattr(c, "occurrence_bar", 0) > decision_bar:
                excluded.append(Exclusion(_cid(c), X_KNOW, "R:SP-01",
                                          f"occurrence {c.occurrence_bar} > t={decision_bar}"))
            elif not allow_provisional:
                excluded.append(Exclusion(_cid(c), X_STATE, "R:SP-01/SWS-04a",
                                          "provisional not allowed by policy"))
            else:
                passed.append(c)
        else:
            if c.knowable_bar > decision_bar:
                excluded.append(Exclusion(_cid(c), X_KNOW, "R:SP-01",
                                          f"knowable_bar={c.knowable_bar} > t={decision_bar}"))
            else:
                passed.append(c)
    return passed, excluded


def sp05_containment(coarse: LegCandidate, fine: LegCandidate,
                     tie_inclusive: bool = True) -> str:
    """SP-05: contained | escaping | disjoint.  Boundary tie rule is a declared
    policy (SWS-06); default here: inclusive spans (recorded by the caller)."""
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
    (default: equality is not a crossing)."""
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
        notes: Optional[List[str]] = None) -> SelectionResult:
    return SelectionResult(
        task_id=task_id, decision_bar=decision_bar, status=status,
        selected_id=selected_id, survivors=survivors, excluded=excluded,
        unresolved=unresolved, provenance=provenance, policy_refs=policy_refs,
        representation_id=rep_id, dependents=dependents or [], notes=notes or [])


def task_s1_structural_reference(points: Sequence[PointCandidate],
                                 legs: Sequence[LegCandidate],
                                 decision_bar: int,
                                 rep: Representation,
                                 role: str,
                                 policy: PolicyRegistry,
                                 policy_id: Optional[str] = None,
                                 allow_provisional: bool = False,
                                 state_id_prefix: str = "S1") -> SelectionResult:
    """T-S1: which confirmed point is the reference for view V's current state.

    Roles (Pi_T, O-class): "origin-of-last-confirmed-leg" (SWS-02) or
    "last-confirmed-extreme".  Without a declared role the output is MP.
    """
    prov = [f"R:SP-01", f"R:SP-13", f"R:SP-14", "F:H_T(confirmed,knowable,in-view)"]
    pregs: List[str] = []
    in_view = [p for p in points if p.rep.view_id == rep.view_id and p.rep.family == rep.family
               and p.rep.params == rep.params]
    others = [p for p in points if p not in in_view]
    excluded: List[Exclusion] = [Exclusion(p.candidate_id, X_SCALE, "R:SP-02",
                                           "not in view V") for p in others]
    passed, ex1 = sp01_knowability(in_view, decision_bar, allow_provisional)
    excluded += ex1
    confirmed = [p for p in passed if p.status == STATUS_CONFIRMED]
    view_legs = [l for l in legs
                 if l.rep.view_id == rep.view_id and l.rep.params == rep.params]
    confirmed_legs = [l for l in view_legs
                      if l.completed and l.knowable_bar <= decision_bar]
    if not confirmed_legs and not confirmed:
        state = UnresolvedState(
            state_id=f"{state_id_prefix}-{decision_bar}", task="T-S1",
            decision_bar=decision_bar, survivors=[], excluded=excluded,
            reason_code=REASON_IC, evidence_needed="more history / confirmation",
            policy_refs=[], provenance=prov,
            dependents_blocked=["T-S5", "T-S4", "zone-context", "liquidity-objective"])
        return _mk("T-S1", decision_bar, "unresolved", None, [], excluded, state,
                   prov, pregs, rep.rep_id)

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
                       prov, pregs, rep.rep_id)
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
                       prov, pregs, rep.rep_id)
        last_leg = max(confirmed_legs, key=lambda l: (l.knowable_bar, l.t1))
        target_id = last_leg.start_id  # origin of the most recent confirmed leg
        target = next(p for p in points if p.candidate_id == target_id)
        for p in confirmed:
            if p.candidate_id != target_id:
                excluded.append(Exclusion(p.candidate_id, X_POL, f"O:{policy_id}",
                                          "not the origin of the last confirmed leg"))
        return _mk("T-S1", decision_bar, "justified", target_id, [target_id],
                   excluded, None, prov, pregs, rep.rep_id,
                   dependents=["T-S5-falsifier", "T-S4-base", "zone-context",
                               "liquidity-objective"],
                   notes=[f"last_confirmed_leg={last_leg.leg_id}",
                          f"role={role} (O-class; SWS-02: not a market claim)"])
    elif role == "last-confirmed-extreme":
        if not confirmed:
            state = UnresolvedState(
                state_id=f"{state_id_prefix}-{decision_bar}", task="T-S1",
                decision_bar=decision_bar, survivors=[], excluded=excluded,
                reason_code=REASON_IC, evidence_needed="no confirmed point yet",
                policy_refs=pregs, provenance=prov)
            return _mk("T-S1", decision_bar, "unresolved", None, [], excluded,
                       state, prov, pregs, rep.rep_id)
        best = max(confirmed, key=lambda p: p.knowable_bar)
        for p in confirmed:
            if p.candidate_id != best.candidate_id:
                excluded.append(Exclusion(p.candidate_id, X_POL, "R:within-class:knowable_bar",
                                          "less recent confirmed point"))
        return _mk("T-S1", decision_bar, "justified", best.candidate_id,
                   [best.candidate_id], excluded, None, prov, pregs, rep.rep_id,
                   notes=["role=last-confirmed-extreme"])
    state = UnresolvedState(
        state_id=f"{state_id_prefix}-{decision_bar}", task="T-S1",
        decision_bar=decision_bar, survivors=[p.candidate_id for p in confirmed],
        excluded=excluded, reason_code=REASON_MP,
        evidence_needed=f"declared role for question (role={role!r} not recognized)",
        policy_refs=[], provenance=prov)
    return _mk("T-S1", decision_bar, "unresolved", None,
               [p.candidate_id for p in confirmed], excluded, state, prov,
               pregs, rep.rep_id)


def task_s2_event_binding(event_bar: int, close_price: float,
                          refs_by_view: Dict[str, Sequence[object]],
                          decision_bar: int,
                          tie_bound: bool = False,
                          require_single_view: Optional[str] = None,
                          prev_close: Optional[float] = None,
                          state_id_prefix: str = "S2") -> SelectionResult:
    """T-S2: which references does a closed-bar event bind to (SP-03)?
    The binding set keeps all members; no ranking (SWS-05).  When
    ``prev_close`` is provided only FRESH crossings count (the previous close
    was not yet beyond the level); without it the bar is the declared single
    event bar (golden cases W5/W10)."""
    prov = ["R:SP-03", "F:close-basis (declared; wick variant open)"]
    bound: List[str] = []
    excluded: List[Exclusion] = []
    per_view: Dict[str, List[str]] = {}

    def _crossed(r: object, px: float) -> bool:
        rside = getattr(r, "side", None)
        if rside == "high":
            return (px > r.level) or (tie_bound and px == r.level)
        if rside == "low":
            return (px < r.level) or (tie_bound and px == r.level)
        return (px != r.level) if not tie_bound else True

    for view, refs in refs_by_view.items():
        knowable = [r for r in refs if r.knowable_bar <= event_bar]
        for r in refs:
            if r.knowable_bar > event_bar:
                excluded.append(Exclusion(r.candidate_id, X_KNOW, "R:SP-01",
                                          f"knowable {r.knowable_bar} > event {event_bar}"))
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
                   [], f"event@{event_bar}", notes=["no event at these scales"])
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
               notes=[f"binding per view: {per_view}"])


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
    surv_ids = [f.leg_id for f in survivors]
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
    if not survivors:
        state = UnresolvedState(
            state_id=f"{state_id_prefix}-{decision_bar}", task="T-S3",
            decision_bar=decision_bar, survivors=[], excluded=excluded,
            reason_code=REASON_IC, evidence_needed="no completed contained fine leg yet",
            policy_refs=pregs, provenance=prov)
        return _mk("T-S3", decision_bar, "unresolved", None, [], excluded, state,
                   prov, pregs, rep.rep_id)
    if len(survivors) == 1:
        return _mk("T-S3", decision_bar, "justified", surv_ids[0], surv_ids,
                   excluded, None, prov, pregs, rep.rep_id,
                   notes=["singleton after H_T + dominance"])
    diffs = []
    for f in survivors:
        diffs.append(f"{f.leg_id}(depth={min(abs(f.p_start - f.p_end), 0):g}"
                     f",knowable={f.knowable_bar})")
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
                      "depth-vs-recency is SWS-07 open (MP/EP), not a fact"])


def task_s5_falsifier(claims: Sequence[dict], points: Sequence[PointCandidate],
                      legs: Sequence[LegCandidate], decision_bar: int,
                      state_id_prefix: str = "S5") -> SelectionResult:
    """T-S5 / SP-04: map each reference-form claim of interpretation I to its
    falsifier reference.  Claims are dicts:
      {"interpretation": "I1", "view": "C", "role": "...", "direction": "up"}
    Supported roles: "origin-of-last-confirmed-leg", "low-of-current-leg",
    "high-of-current-leg", "last-confirmed-extreme".  A claim not written in
    reference terms yields MP (SWS-08).
    """
    prov = ["R:SP-04", "F:given I written in reference terms (SWS-08)"]
    resolved: List[str] = []
    excluded: List[Exclusion] = []
    notes: List[str] = []
    by_id = {p.candidate_id: p for p in points}
    legs_by_view: Dict[str, List[LegCandidate]] = {}
    for l in legs:
        legs_by_view.setdefault(l.view_id, []).append(l)
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
            notes.append(f"{interp}: origin of {last.leg_id} -> {last.start_id}")
        elif role in ("low-of-current-leg", "high-of-current-leg"):
            want_dir = claim.get("direction")
            dlegs = [l for l in vlegs if want_dir is None or l.direction == want_dir]
            if not dlegs:
                excluded.append(Exclusion(f"{interp}:{role}", X_STATE, "R:SP-04",
                                          f"no confirmed {want_dir or ''} leg in view"))
                continue
            last = max(dlegs, key=lambda l: (l.knowable_bar, l.t1))
            pid = last.low_id if role == "low-of-current-leg" else last.high_id
            resolved.append(pid)
            notes.append(f"{interp}: {role} of {last.leg_id} -> {pid}")
        elif role == "last-confirmed-extreme":
            vpts = [p for p in points if p.view_id == view
                    and p.status == STATUS_CONFIRMED and p.knowable_bar <= decision_bar]
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
            notes.append(f"{interp}: last-confirmed-{want} -> {best.candidate_id}")
        else:
            excluded.append(Exclusion(f"{interp}:{role or 'none'}", X_POL, "R:SP-04",
                                      "claim not written in reference terms"))
    if not resolved:
        state = UnresolvedState(
            state_id=f"{state_id_prefix}-{decision_bar}", task="T-S5",
            decision_bar=decision_bar, survivors=[], excluded=excluded,
            reason_code=REASON_MP,
            evidence_needed="write I in reference terms (SWS-08) or declare the reading as O/S-ambiguous",
            policy_refs=[], provenance=prov)
        return _mk("T-S5", decision_bar, "unresolved", None, [], excluded, state,
                   prov, [], "claims", notes=notes)
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
               notes=notes)


# --------------------------------------------------------------------------
# Interpretation ledger & revision propagation (IC-10, IC-11, SP-20)
# --------------------------------------------------------------------------

class InterpretationLedger:
    """Append-only record of selections, events, and propagation steps."""

    def __init__(self) -> None:
        self.results: List[SelectionResult] = []
        self.events: List[dict] = []
        self.revisions: List[dict] = []

    def record(self, result: SelectionResult) -> None:
        self.results.append(result)

    def record_event(self, event_bar: int, kind: str, detail: str,
                     affected_ids: Sequence[str]) -> None:
        self.events.append({"event_bar": event_bar, "kind": kind,
                            "detail": detail, "affected_ids": list(affected_ids)})

    def propagate(self, event_bar: int, changes: Sequence[Tuple[str, str, str]],
                  ) -> List[dict]:
        """SP-20: revision propagation — topological recomputation log.

        changes: list of (subject, before, after) recomputations.  Never an
        in-place patch; each dependent conclusion is recomputed and logged.
        """
        log = []
        for i, (subject, before, after) in enumerate(changes):
            entry = {"event_bar": event_bar, "step": i + 1,
                     "subject": subject, "before": before, "after": after,
                     "rule": "R:SP-20 recomputation, not patch"}
            self.revisions.append(entry)
            log.append(entry)
        return log

    def snapshot(self) -> dict:
        return {
            "n_results": len(self.results),
            "n_events": len(self.events),
            "n_revisions": len(self.revisions),
            "justified": sum(1 for r in self.results if r.status == "justified"),
            "unresolved": sum(1 for r in self.results if r.status == "unresolved"),
            "empty": sum(1 for r in self.results if r.status == "empty"),
        }
