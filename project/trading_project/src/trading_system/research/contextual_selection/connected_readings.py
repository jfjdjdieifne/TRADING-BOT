"""Connected readings V1 — multi-timeframe context, FVG geometry,
structural references, shift-watches and decision-making on ONE
analytical path.

This module connects the existing pieces (``study_links`` candidate /
shift-watch machinery, the causal frames, the InterpretationLedger)
into the flow::

    higher-timeframe context
            ↓
    relevant movement and structural references
            ↓
    interaction with a reference
            ↓
    lower-timeframe evidence and FVGs
            ↓
    comparison of competing interpretations
            ↓
    working conclusion or explicit non-resolution
            ↓
    conditional observations to watch
            ↓
    revision when new evidence becomes available

It is an ENGINEERING INTERPRETATION inspired by the supplied research
(corpus: E03-A/B, E12-A, OB16-A, FVG16-A, FVG24-A) and by TRUSTED
PUBLIC REFERENCES describing Michael Huddleston's ICT definitions.
It is NOT a claim that Michael Huddleston's complete reasoning or
trading decisions are reproduced.  NO fixed recipe exists here
(``reference crossing + FVG = reversal`` and similar are deliberately
absent).

FVG GEOMETRY (declared definition)
---------------------------------
Three CONSECUTIVE COMPLETED bars ``b1, b2, b3`` on a declared
timeframe/chart construction:

* upward region (external references call it BISI / bullish FVG):
  ``b3.low > b1.high`` — the non-overlap interval is
  ``[b1.high, b3.low]``;
* downward region (SIBI / bearish FVG): ``b3.high < b1.low`` —
  the interval is ``[b3.high, b1.low]``.

The region becomes observable ONLY when ``b3`` completes (its
completion label is the region's ``observability_time``).  It is never
reported before that moment.  Each region records: the three bars,
timeframe + bar construction (completion-labelled resample of the 1m
source), price bounds, direction, observability time, instrument,
timezone, session convention, the 50% midpoint (external term
"Consequent Encroachment" — kept as a LEVEL, not a rule), subsequent
interactions seen strictly from data available at the analysis time,
and what CANNOT be inferred from bar resolution (intrabar path, order
flow, resting orders, participant intent, inevitability of any fill,
identical geometry on another timeframe).

Separations kept everywhere: observed/derived geometry vs contextual
interpretation of relevance vs subsequent interaction vs unknowns.

SOURCE BASE
-----------
* corpus ``corpus_full_pass.json`` (user-provided, primary):
  FVG16-A DIRECT_STATEMENT — "the exposed price interval a fair value
  gap on the chart timeframe; lower timeframe may display a
  multi-candle liquidity void rather than identical three-candle
  geometry"; FVG16-A ENGINEERING_INTERPRETATION — "store gap geometry
  with its originating timeframe and relate it to other previously
  available references; allow finer-frame representation to differ
  without promoting a gap to inevitable fill"; E03-B PARAPHRASE —
  "assess whether the later candles leave a fair value gap".
* trusted public references describing ICT definitions (external
  SECONDARY sources — not audited speech, not the corpus):
  michaeljhuddleston.org "SIBI and BISI … Fair Value Gap" notes
  (three-candle formation; gap between the first candle's wick and
  the third candle's wick), tradingstrategyguides.com "Complete Guide
  To ICT Fair Value Gaps" (BISI = candle1.high–candle3.low; SIBI =
  candle1.low–candle3.high; Consequent Encroachment = 50% midpoint),
  writofinance.com ICT overview (same three-candle wick non-overlap).
  Trade-execution parts of those references (entries, stops, targets)
  are explicitly NOT implemented.

``selection_quality = NOT_ESTABLISHED``.  No orders, no
recommendations, no live-monitoring claim.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from trading_system.research.contextual_selection.csm import (
    SelectionResult,
)

__all__ = [
    "FVGRegion", "FrameLink", "ReadingTask", "WorkingInterpretation",
    "ConnectedReadingsEngine",
    "CONCLUSION_EVIDENCE_PREFERRED", "CONCLUSION_PROVISIONAL",
    "CONCLUSION_UNRESOLVED",
    "INTERP_WORKING", "INTERP_REVISED", "INTERP_SUSPENDED",
    "INTERP_UNRESOLVED",
    "FVG_GEOMETRY_DEFINITION", "FVG_EXTERNAL_SOURCES",
    "FVG_UNKNOWNS",
]

# --------------------------------------------------------------------- #
# declared definitions and source labels                                 #
# --------------------------------------------------------------------- #
FVG_GEOMETRY_DEFINITION = (
    "three CONSECUTIVE COMPLETED bars (b1, b2, b3) on the declared "
    "timeframe and bar construction (completion-labelled resample of "
    "the 1m source): an UPWARD region exists when b3.low > b1.high "
    "(interval [b1.high, b3.low]); a DOWNWARD region when b3.high < "
    "b1.low (interval [b3.high, b1.low]). The 50% midpoint of the "
    "interval (external term 'Consequent Encroachment') is stored "
    "as a reference LEVEL only — never as a rule or a trigger. "
    "The region is observable "
    "ONLY when b3 completes. (S) corpus FVG16-A + external trusted "
    "references describing ICT's three-candle wick non-overlap; "
    "(E) exact bounds/availability handling is engineering."
)

FVG_EXTERNAL_SOURCES = [
    "https://michaeljhuddleston.org/notes/"
    "sibi-and-bisi-in-ict-master-fair-value-gap-trading/ "
    "(notes site; external secondary reference)",
    "https://tradingstrategyguides.com/the-complete-guide-to-ict-"
    "fair-value-gaps-in-forex/ (external secondary reference; "
    "BISI/SIBI bounds and Consequent Encroachment midpoint)",
    "https://writofinance.com/inner-circle-trader-ict-michael/ "
    "(external secondary reference)",
]

FVG_UNKNOWNS = [
    "the intrabar path inside any bar (not established by completed "
    "OHLC)",
    "order flow, resting orders, participant positions or intent",
    "that a gap will be filled ('rebalanced') — a revisit is an "
    "observed relation, not a guarantee",
    "that a region has the same origin, significance, or geometry on "
    "another timeframe (FVG16-A: a finer frame may show a multi-candle "
    "liquidity void rather than identical three-candle geometry)",
    "any entry, target, stop, reversal or continuation signal from the "
    "geometry alone",
]

CONCLUSION_EVIDENCE_PREFERRED = "EVIDENCE_PREFERRED"
CONCLUSION_PROVISIONAL = "PROVISIONAL_WORKING_BASELINE"
CONCLUSION_UNRESOLVED = "UNRESOLVED_NO_EDGE"

INTERP_WORKING = "WORKING"
INTERP_REVISED = "REVISED"
INTERP_SUSPENDED = "SUSPENDED"
INTERP_UNRESOLVED = "UNRESOLVED"
INTERP_STATUSES = (INTERP_WORKING, INTERP_REVISED, INTERP_SUSPENDED,
                   INTERP_UNRESOLVED)


def _jsonable(obj):
    if isinstance(obj, pd.Timestamp):
        return str(obj)
    if isinstance(obj, dict):
        return {k: _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    return obj


# --------------------------------------------------------------------- #
# FVG region: observable geometry + interactions + unknowns              #
# --------------------------------------------------------------------- #
@dataclass
class FVGRegion:
    region_id: str
    timeframe: str
    direction: str                    # "upward" | "downward"
    bar1: Dict[str, Any]              # {index, time, high, low, ...}
    bar2: Dict[str, Any]
    bar3: Dict[str, Any]
    lower_bound: float
    upper_bound: float
    observability_time: pd.Timestamp  # completion label of bar3
    instrument: str = "UNKNOWN"
    timezone: str = "UTC"
    session_convention: str = ("24h crypto market; the US-index "
                               "first-gap session clock does NOT apply")
    bar_convention: str = ("completion-labelled resample of the 1m "
                           "source; closed bars only")
    ce_midpoint: float = 0.0          # 50% level (external term
                                      # 'Consequent Encroachment');
                                      # a LEVEL, not a rule
    interactions: List[dict] = field(default_factory=list)
    interpretation_notes: List[dict] = field(default_factory=list)
    scan_floor: int = -1              # highest bar index already
                                      # checked for interactions

    def __post_init__(self):
        self.ce_midpoint = (self.lower_bound + self.upper_bound) / 2.0

    def availability(self, as_of) -> str:
        """Explicit causal-availability label at ``as_of``: observable
        ONLY from bar3's completion label onward; never before."""
        t = pd.Timestamp(as_of)
        if t < pd.Timestamp(self.observability_time):
            return ("not_yet_observable at this as_of_time: the region "
                    "requires bar3 (" + str(self.observability_time) +
                    ") to complete")
        return ("observable since " + str(self.observability_time) +
                " (bar3 completion label; the bar covers that "
                "interval and may be INCOMPLETE before the label)")

    def note_interaction(self, *, kind, at, at_bar, detail) -> dict:
        rec = {"kind": kind, "at": pd.Timestamp(at),
               "at_bar": int(at_bar), "detail": detail,
               "layer": "DIRECT_OBSERVATION",
               "note": "observed relation between published bar "
                       "ranges/levels only — NOT proof of orders, "
                       "fills, or intent"}
        self.interactions.append(rec)
        return rec

    def to_record(self) -> dict:
        d = dataclasses.asdict(self)
        d["observability_time"] = str(self.observability_time)
        d["availability_note"] = self.availability(self.observability_time)
        d["source_note"] = ("FVG geometry per external secondary "
                            "references + corpus FVG16-A (S); exact "
                            "bounds/availability handling is "
                            "engineering (E)")
        d["unknowns"] = list(FVG_UNKNOWNS)
        d["hidden_assumptions"] = [
            "bars are what the declared completion-labelled resample "
            "publishes (S/E boundary): intrabar paths are unknown",
            "an observed range relation is NOT evidence of orders, "
            "fills, or participant intent",
            "no relationship here is a trade signal",
        ]
        return _jsonable(d)


# --------------------------------------------------------------------- #
# cross-timeframe links (never equivalence)                              #
# --------------------------------------------------------------------- #
@dataclass
class FrameLink:
    link_id: str
    subject_id: str
    subject_frame: str
    other_id: str
    other_frame: str
    relation: str          # "interval_contains_level" |
                           # "intervals_overlap" |
                           # "intervals_disjoint" |
                           # "level_equals_ce_of_interval"
    established_at: pd.Timestamp
    note: str = ("cross-frame relation between observable regions/"
                 "levels — NOT an identity claim: different "
                 "timeframes keep different representations (FVG16-A)")
    evidence: Dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> dict:
        d = dataclasses.asdict(self)
        d["established_at"] = str(self.established_at)
        return _jsonable(d)


# --------------------------------------------------------------------- #
# reading task: compare candidates for a declared question               #
# --------------------------------------------------------------------- #
@dataclass
class ReadingTask:
    task_id: str
    question: str
    declared: Dict[str, Any]          # task scope/inputs (frame, watch,
                                      # purpose) — declared, not hidden
    candidates: List[dict] = field(default_factory=list)
    conclusion: Dict[str, Any] = field(default_factory=dict)
    watch_next: List[dict] = field(default_factory=list)
    versions: List[dict] = field(default_factory=list)
    comparison: Dict[str, Any] = field(default_factory=dict)

    def conclude(self, *, status, preferred, reasons,
                 discriminating_evidence, alternatives,
                 revision_of=None, recorded_at=None) -> dict:
        ver = {
            "version": len(self.versions) + 1,
            "revision_of": revision_of,
            "conclusion": {
                "status": status, "preferred": preferred,
                "reasons": list(reasons),
                "discriminating_evidence": list(discriminating_evidence),
            },
            "alternatives": list(alternatives),
            "recorded_at": str(pd.Timestamp(
                recorded_at if recorded_at is not None
                else "1970-01-01")),
        }
        self.versions.append(ver)
        self.conclusion = dict(ver["conclusion"],
                               alternatives=list(alternatives))
        return ver

    def to_record(self) -> dict:
        return _jsonable(dataclasses.asdict(self))


# --------------------------------------------------------------------- #
# working interpretation: statement + alternatives + watch + versions    #
# --------------------------------------------------------------------- #
@dataclass
class WorkingInterpretation:
    interp_id: str
    question: str
    statement: str
    basis: List[Dict[str, Any]]       # evidence items (id + class)
    alternatives: List[dict]
    status: str = INTERP_WORKING
    watch: List[dict] = field(default_factory=list)
    versions: List[dict] = field(default_factory=list)
    revision_count: int = 0
    current_trend: Optional[str] = None

    def __post_init__(self):
        if not self.versions:
            self.versions.append({
                "version": 1, "revision_of": None,
                "statement": self.statement,
                "reason": "initial interpretation at creation",
                "evidence": _jsonable(list(self.basis)),
                "status": self.status,
                "recorded_at": "1970-01-01",
            })

    def revise(self, *, statement, reason, evidence, status=None,
               watch=None, recorded_at=None) -> dict:
        """Append a NEW linked version; the previous one is preserved
        unchanged.  A weakening hypothesis NEVER automatically flips
        to its opposite."""
        self.revision_count += 1
        ver = {
            "version": len(self.versions) + 1,
            "revision_of": (self.versions[-1]["version"]
                            if self.versions else None),
            "statement": statement,
            "reason": reason,
            "evidence": _jsonable(list(evidence)),
            "status": status or INTERP_REVISED,
            "recorded_at": str(pd.Timestamp(
                recorded_at if recorded_at is not None
                else "1970-01-01")),
            "note": "append-only revision; the prior version is "
                    "preserved; no automatic opposite conclusion is "
                    "generated",
        }
        self.versions.append(ver)
        self.statement = statement
        self.status = ver["status"]
        if watch is not None:
            self.watch = list(watch)
        return ver

    def to_record(self) -> dict:
        return _jsonable(dataclasses.asdict(self))


# --------------------------------------------------------------------- #
# the connected engine                                                   #
# --------------------------------------------------------------------- #
class ConnectedReadingsEngine:
    """Detects FVG regions per timeframe, links them to structural
    references and across frames, relates them to open shift-watches,
    runs declared reading tasks (evidence-preferred / provisional /
    unresolved), maintains working interpretations with conditional
    watches, and records everything in the existing ledger."""

    def __init__(self, *, run_id: str = "cr-v1",
                 instrument: str = "UNKNOWN",
                 timezone: str = "UTC") -> None:
        self.run_id = run_id
        self.instrument = instrument
        self.timezone = timezone
        self.regions: Dict[str, FVGRegion] = {}
        self.links: List[FrameLink] = []
        self.tasks: Dict[str, ReadingTask] = {}
        self.interps: Dict[str, WorkingInterpretation] = {}
        self.seq_facts: List[dict] = []
        self._frame_cursors: Dict[str, int] = {}
        self._region_seq = 0
        self._link_seq = 0
        self._ledger_uids: Dict[str, str] = {}
        self._ledger_sigs: Dict[str, tuple] = {}
        self._seen_links: set = set()
        self._linked_region_ids: set = set()
        self._linked_ref_ids: set = set()

    # ---- FVG scanning (completed bars only; never before b3 closes) --
    def scan_fvgs(self, frames: Dict[str, pd.DataFrame]
                  ) -> List[dict]:
        changes: List[dict] = []
        for tf, bars in frames.items():
            n = len(bars)
            start = max(0, self._frame_cursors.get(tf, 0) - 2)
            for j in range(start, n - 2):
                b1 = self._bar(bars, j)
                b2 = self._bar(bars, j + 1)
                b3 = self._bar(bars, j + 2)
                if b1 is None or b2 is None or b3 is None:
                    continue
                direction = None
                lo, hi = None, None
                if b3["low"] > b1["high"]:
                    direction = "upward"
                    lo, hi = b1["high"], b3["low"]
                elif b3["high"] < b1["low"]:
                    direction = "downward"
                    lo, hi = b3["high"], b1["low"]
                if direction is None:
                    continue
                rid = f"FVG-{self.run_id}-{tf}-{j + 2}"
                if rid in self.regions:
                    continue
                self._region_seq += 1
                region = FVGRegion(
                    region_id=rid, timeframe=tf, direction=direction,
                    bar1=b1, bar2=b2, bar3=b3,
                    lower_bound=float(lo), upper_bound=float(hi),
                    observability_time=pd.Timestamp(b3["time"]),
                    instrument=self.instrument,
                    timezone=self.timezone)
                self.regions[rid] = region
                region.interpretation_notes.extend([
                    {"layer": "DIRECT_OBSERVATION",
                     "note": "b1.high=" + str(b1["high"]) + " and b3.low="
                     + str(b3["low"]) + " do not overlap on the "
                     "published completed bars"},
                    {"layer": "DERIVATION",
                     "note": "interval [" + str(float(lo)) + ", "
                     + str(float(hi)) + "]; midpoint "
                     + str(region.ce_midpoint) + " (external term "
                     "'Consequent Encroachment' — a LEVEL, not a rule)"},
                    {"layer": "CONTEXTUAL_INTERPRETATION",
                     "note": "any relation of this interval to other "
                     "references is interpretation, recorded with "
                     "timeframe and availability"},
                    {"layer": "UNKNOWN_UNSUPPORTED",
                     "note": "fill inevitability, order flow, "
                     "cross-timeframe identity and trade signals are "
                     "NOT established (FVG_UNKNOWNS)"},
                ])
                self.seq_facts.append({
                    "kind": "FVG_OBSERVABLE", "at": region.observability_time,
                    "region_id": rid, "timeframe": tf,
                    "direction": direction,
                    "interval": [float(lo), float(hi)],
                    "note": "observable only after bar3 completed",
                    "layer": "DERIVATION"})
                changes.append({
                    "aspect": "fvg_region", "before": "(none)",
                    "after": f"{rid} {direction} [{lo}, {hi}] @{tf}",
                    "reason": "three-candle non-overlap completed; "
                              "geometry observable at bar3 completion "
                              "only",
                    "evidence": [rid, str(region.observability_time)]})
            self._frame_cursors[tf] = max(self._frame_cursors.get(tf, 0),
                                          n)
        return changes

    @staticmethod
    def _bar(bars: pd.DataFrame, j: int) -> Optional[dict]:
        if j < 0 or j >= len(bars):
            return None
        return {
            "index": int(j),
            "time": pd.Timestamp(bars.index[j]),
            "open": float(bars["open"].iloc[j]),
            "high": float(bars["high"].iloc[j]),
            "low": float(bars["low"].iloc[j]),
            "close": float(bars["close"].iloc[j]),
        }

    # ---- subsequent interactions (data <= analysis time only) --------
    def update_interactions(self, frames: Dict[str, pd.DataFrame],
                            as_of_time: Optional[pd.Timestamp] = None
                            ) -> List[dict]:
        """Append interactions of SUBSEQUENT completed bars (bars after
        the region's own b1..b3 never predate its observability).  Bars
        with a completion label after ``as_of_time`` are never used
        (future-data invariance)."""
        changes: List[dict] = []
        for rid, region in self.regions.items():
            bars = frames.get(region.timeframe)
            if bars is None:
                continue
            start = max(int(region.bar3["index"]) + 1,
                        region.scan_floor + 1)
            for j in range(start, len(bars)):
                b = self._bar(bars, j)
                if b is None:
                    continue
                if (as_of_time is not None and
                        pd.Timestamp(b["time"]) > pd.Timestamp(as_of_time)):
                    continue
                lo, hi = region.lower_bound, region.upper_bound
                overlaps = b["low"] <= hi and b["high"] >= lo
                covers = b["low"] <= lo and b["high"] >= hi
                ce_hit = b["low"] <= region.ce_midpoint <= b["high"]
                if overlaps:
                    region.note_interaction(
                        kind=("range_covers_interval" if covers
                              else "range_overlaps_interval"),
                        at=b["time"], at_bar=j,
                        detail={"bar": j, "high": b["high"],
                                "low": b["low"]})
                if ce_hit and not covers:
                    region.note_interaction(
                        kind="ce_midpoint_in_range", at=b["time"],
                        at_bar=j,
                        detail={"bar": j, "ce": region.ce_midpoint})
                region.scan_floor = j
            if region.interactions and not region.interpretation_notes:
                region.interpretation_notes.append({
                    "note": "a revisit/coverage is an OBSERVED relation "
                            "between reported ranges — it does not "
                            "prove a fill, orders, or that the gap "
                            "'had to' be revisited",
                    "layer": "CONTEXTUAL_INTERPRETATION"})
        return changes

    # ---- links: FVG ↔ references, FVG ↔ FVG across frames -----------
    def link_regions(self, *, refs: List[Any], as_of_time: pd.Timestamp,
                     compare_pairs: Optional[List[tuple]] = None
                     ) -> List[dict]:
        """Cross-timeframe LINKS (relations only, never identity).

        Recorded links: ``interval_contains_level`` (region contains a
        structural reference level), ``level_equals_ce_of_interval``,
        ``intervals_overlap`` (cross-frame regions whose intervals
        overlap).  ``intervals_disjoint`` is a STATED non-relationship
        recorded only for pairs explicitly passed in ``compare_pairs``
        (e.g. a task's competing candidates) — trivial disjointness
        between unrelated pairs is not noise-worthy.

        Incremental pairing (performance; identical link set): a NEW
        region is paired against every existing region and reference; a
        NEW reference against every existing region; already-linked
        pairs are never re-walked."""
        changes: List[dict] = []
        new_regions = [rid for rid in sorted(self.regions)
                       if rid not in self._linked_region_ids]
        new_refs = [ref for ref in refs
                    if str(getattr(ref, "candidate_id", ref))
                    not in self._linked_ref_ids]
        # (a) NEW regions vs every existing ref and region
        for rid in new_regions:
            region = self.regions[rid]
            for ref in refs:
                lvl = float(getattr(ref, "level", -1))
                if not (region.lower_bound <= lvl <= region.upper_bound):
                    continue
                key = (rid, str(getattr(ref, "candidate_id", ref)),
                       "level_in_interval")
                if self._link_seen(key):
                    continue
                self._link_seq += 1
                link = FrameLink(
                    link_id=f"FL-{self.run_id}-{self._link_seq:04d}",
                    subject_id=rid, subject_frame=region.timeframe,
                    other_id=str(getattr(ref, "candidate_id", ref)),
                    other_frame="task-frame reference (F-K points)",
                    relation="interval_contains_level",
                    established_at=pd.Timestamp(as_of_time),
                    evidence={"level": lvl,
                              "interval": [region.lower_bound,
                                           region.upper_bound]})
                self.links.append(link)
                self._mark_link(key)
                self.seq_facts.append({
                    "kind": "CROSS_FRAME_LINK", "at":
                        pd.Timestamp(as_of_time),
                    "link_id": link.link_id, "relation": link.relation,
                    "layer": "DERIVATION"})
                changes.append({
                    "aspect": "frame_link", "before": "(none)",
                    "after": link.link_id,
                    "reason": "the region's interval contains the "
                              "reference level (exact relation; no "
                              "origin/significance equivalence)",
                    "evidence": [link.link_id, str(lvl)]})
            for oid in sorted(self.regions):
                if oid == rid:
                    continue
                changes += self._pair_regions(rid, oid, as_of_time,
                                              set())
            self._linked_region_ids.add(rid)
        # (b) NEW refs vs every existing region
        for ref in new_refs:
            rid_key = str(getattr(ref, "candidate_id", ref))
            lvl = float(getattr(ref, "level", -1))
            for rid, region in sorted(self.regions.items()):
                if not (region.lower_bound <= lvl <= region.upper_bound):
                    continue
                key = (rid, rid_key, "level_in_interval")
                if self._link_seen(key):
                    continue
                self._link_seq += 1
                link = FrameLink(
                    link_id=f"FL-{self.run_id}-{self._link_seq:04d}",
                    subject_id=rid, subject_frame=region.timeframe,
                    other_id=rid_key,
                    other_frame="task-frame reference (F-K points)",
                    relation="interval_contains_level",
                    established_at=pd.Timestamp(as_of_time),
                    evidence={"level": lvl,
                              "interval": [region.lower_bound,
                                           region.upper_bound]})
                self.links.append(link)
                self._mark_link(key)
                self.seq_facts.append({
                    "kind": "CROSS_FRAME_LINK", "at":
                        pd.Timestamp(as_of_time),
                    "link_id": link.link_id, "relation": link.relation,
                    "layer": "DERIVATION"})
                changes.append({
                    "aspect": "frame_link", "before": "(none)",
                    "after": link.link_id,
                    "reason": "the region's interval contains the "
                              "reference level (exact relation; no "
                              "origin/significance equivalence)",
                    "evidence": [link.link_id, str(lvl)]})
            self._linked_ref_ids.add(rid_key)
        # (c) explicitly compared pairs (may state non-relationship)
        explicit = {frozenset(p) for p in (compare_pairs or [])}
        for pair in explicit:
            if len(pair) != 2:
                continue
            a, b = sorted(pair)
            if a in self.regions and b in self.regions:
                changes += self._pair_regions(a, b, as_of_time, explicit)
        return changes

    def _pair_regions(self, a: str, b: str, as_of_time,
                      explicit: set) -> List[dict]:
        changes: List[dict] = []
        ra, rb = self.regions[a], self.regions[b]
        if ra.timeframe == rb.timeframe:
            return changes
        overlap = (ra.lower_bound <= rb.upper_bound and
                   rb.lower_bound <= ra.upper_bound)
        lo_id, hi_id = (a, b) if a <= b else (b, a)
        rel = ("intervals_overlap" if overlap else "intervals_disjoint")
        if not overlap and frozenset((a, b)) not in explicit:
            return changes
        key = (lo_id, hi_id, rel)
        if self._link_seen(key):
            return changes
        self._link_seq += 1
        link = FrameLink(
            link_id=f"FL-{self.run_id}-{self._link_seq:04d}",
            subject_id=a, subject_frame=ra.timeframe,
            other_id=b, other_frame=rb.timeframe,
            relation=rel,
            established_at=pd.Timestamp(as_of_time),
            note="different timeframes keep different "
                 "representations (FVG16-A): overlap or "
                 "disjointness is recorded; the regions are "
                 "NOT the same object and share no assumed "
                 "origin, significance, or future",
            evidence={"a": [ra.lower_bound, ra.upper_bound],
                      "b": [rb.lower_bound, rb.upper_bound]})
        self.links.append(link)
        self._mark_link(key)
        changes.append({
            "aspect": "frame_link", "before": "(none)",
            "after": link.link_id,
            "reason": f"{ra.timeframe} vs {rb.timeframe}: "
                      f"{link.relation} (not an equivalence)",
            "evidence": [link.link_id]})
        return changes

    _seen_links: set = set()   # per-instance; reset in __init__

    def _link_seen(self, key) -> bool:
        return key in self._seen_links

    def _mark_link(self, key) -> None:
        self._seen_links.add(key)

    # ---- reading tasks ------------------------------------------------
    def task_fvg_relevance_for_watch(self, *, watch: Dict[str, Any],
                                     as_of_time: pd.Timestamp,
                                     hf_trend: Optional[str] = None
                                     ) -> Optional[ReadingTask]:
        """Declared task: which completed FVG region (if any) is the
        displacement/non-overlap evidence to attach to an open
        shift-watch (E03-B)?  The evaluation rule below is an
        ENGINEERING choice of this engine (a conjunction of declared
        criteria), NOT a source statement and NOT presented as anyone's
        universal method; conflicting evidence is recorded per
        candidate (supporting vs counterevidence) and partial-support
        candidates are never deleted."""
        tid = f"RT-WATCH-{watch.get('watch_id')}"
        crossing = dict(watch.get("crossing", {}))
        cross_dir = crossing.get("direction")
        cross_level = crossing.get("ref_level")
        cross_time = crossing.get("bar_time")
        declared = {
            "question": "which FVG region is the displacement/"
                        "non-overlap evidence for this shift-watch",
            "watch": watch.get("watch_id"),
            "frame_scope": sorted({r.timeframe
                                   for r in self.regions.values()}),
            "criteria": [
                {"name": "observable_after_crossing",
                 "meaning": "region observability_time is later than "
                            "the crossing bar's time (chronology "
                            "actually established)",
                 "class": "ENGINEERING_INTERPRETATION"},
                {"name": "direction_consistent",
                 "meaning": "region direction matches the crossing "
                            "direction (E03-B displacement reading)",
                 "class": "ENGINEERING_INTERPRETATION"},
                {"name": "interval_contains_crossed_level",
                 "meaning": "the interval contains the crossed "
                            "reference level (exact relation)",
                 "class": "ENGINEERING_INTERPRETATION"},
            ],
            "evaluation_rule": {
                "kind": "ENGINEERING_INTERPRETATION",
                "rule": "all declared criteria must hold "
                        "(conjunction) for a single-candidate "
                        "preference",
                "source_status": "NOT a source statement; the source "
                                 "material does not specify this "
                                 "evaluation, and other evaluation "
                                 "rules remain possible",
                "conflict_handling": "criteria not met are recorded "
                                     "as counterevidence with the "
                                     "observed facts; partial-support "
                                     "candidates remain in the "
                                     "candidate list and in the "
                                     "alternatives; no numerical "
                                     "score, ranking, or confidence "
                                     "percentage is used",
            },
        }
        task = self.tasks.get(tid) or ReadingTask(
            task_id=tid, question=declared["question"],
            declared=declared)
        task.declared = declared
        # PERFORMANCE (identical content): per-region candidates are
        # recomputed ONLY when that region's own inputs change (new
        # region, new interactions on it, or a changed crossing/trend
        # context).  Each candidate dict is a deterministic function of
        # those inputs, so incremental updates produce byte-identical
        # records to a full rebuild (save/resume tests verify).
        ctx_key = (str(hf_trend), str(cross_time), str(cross_dir),
                   str(cross_level))
        if getattr(task, "_ctx_key", None) != ctx_key:
            task._cand_map = {}
        task._ctx_key = ctx_key
        if not hasattr(task, "_cand_map") or task._cand_map is None:
            task._cand_map = {}
        any_changed = False
        for rid, region in sorted(self.regions.items()):
            n_inter = len(region.interactions)
            prev = task._cand_map.get(rid)
            if prev is not None and prev[0] == n_inter:
                continue                     # unchanged: keep candidate
            any_changed = True
            crit = {
                "observable_after_crossing":
                    (str(region.observability_time) > str(cross_time))
                    if cross_time else False,
                "direction_consistent":
                    (region.direction == ("upward" if cross_dir ==
                                          "upward" else "downward")),
                "interval_contains_crossed_level":
                    (cross_level is not None and
                     region.lower_bound <= float(cross_level) <=
                     region.upper_bound),
            }
            # chronology actually established (never guessed)
            if not cross_time:
                chronology = "crossing_time_unknown"
            elif str(region.observability_time) > str(cross_time):
                chronology = "crossing_before_fvg_observable"
            elif str(region.observability_time) == str(cross_time):
                chronology = ("unorderable_at_boundary: the crossing "
                              "bar labels the same completion boundary "
                              "as the FVG's observability")
            else:
                chronology = "fvg_observable_before_crossing"
            # evidence breakdown: what supports, what contradicts, what
            # cannot be evaluated yet (recorded, never guessed)
            supporting = []
            counterevidence = []
            unknowns = []
            if not cross_time:
                unknowns.append("crossing time unknown: "
                                "observable_after_crossing cannot be "
                                "evaluated")
            elif crit["observable_after_crossing"]:
                supporting.append(
                    "observable_after_crossing: region observable at "
                    + str(region.observability_time) + " is later than "
                    "the crossing at " + str(cross_time))
            else:
                counterevidence.append(
                    "observable_after_crossing: region observable at "
                    + str(region.observability_time) + " vs crossing at "
                    + str(cross_time) + " — chronology: " + chronology)
            if crit["direction_consistent"]:
                supporting.append(
                    "direction_consistent: region direction "
                    + str(region.direction) + " matches the crossing "
                    "direction (" + str(cross_dir) + ")")
            else:
                counterevidence.append(
                    "direction_consistent: region direction "
                    + str(region.direction) + " vs crossing direction "
                    + str(cross_dir) + " — mismatch observed")
            if cross_level is None:
                unknowns.append("crossed level unknown: "
                                "interval_contains_crossed_level "
                                "cannot be evaluated")
            elif crit["interval_contains_crossed_level"]:
                supporting.append(
                    "interval_contains_crossed_level: ["
                    + str(region.lower_bound) + ", "
                    + str(region.upper_bound) + "] contains "
                    + str(cross_level))
            else:
                counterevidence.append(
                    "interval_contains_crossed_level: ["
                    + str(region.lower_bound) + ", "
                    + str(region.upper_bound) + "] does not contain "
                    + str(cross_level))
            relation_to_context = {
                "hf_trend": hf_trend,
                "region_vs_context":
                    ("unknown (no higher-frame context established)"
                     if not hf_trend or hf_trend == "unknown" else
                     ("aligned" if
                      (region.direction == "upward") ==
                      (hf_trend == "up") else "counter")),
                "prior_events": {
                    "crossing": {"ref_id": crossing.get("ref_id"),
                                 "bar_time": cross_time,
                                 "direction": cross_dir},
                    "chronology": chronology,
                    "interactions_observed": len(region.interactions),
                },
            }
            conflict_note = None
            if supporting and counterevidence:
                conflict_note = ("conflicting evidence: partial "
                                 "support only; the declared "
                                 "conjunction is not satisfied; this "
                                 "candidate remains recorded as an "
                                 "alternative (never deleted)")
            _cand = {
                "candidate_id": rid, "kind": "FVG region",
                "timeframe": region.timeframe,
                "availability": str(region.observability_time),
                "chronology": chronology,
                "role_options": ["relevant_evidence",
                                 "competing_reference", "monitor",
                                 "irrelevant", "unresolved"],
                "criteria": crit,
                "supporting_evidence": supporting,
                "counterevidence": counterevidence,
                "unknowns": unknowns,
                "relation_to_context": relation_to_context,
                "conflict_note": conflict_note,
                "all_criteria_met": all(crit.values())}
            task._cand_map[rid] = (n_inter, _cand)
        if any_changed:
            task.candidates = [task._cand_map[rid][1]
                               for rid in sorted(task._cand_map)]
            # relevance accounting: counts BEFORE and AFTER display
            # filtering; nothing is removed from the record
            n_total = len(task.candidates)
            by_support = {0: 0, 1: 0, 2: 0, 3: 0}
            for c in task.candidates:
                by_support[sum(bool(v) for v in
                               c["criteria"].values())] += 1
            material = [c for c in task.candidates
                        if sum(bool(v) for v in
                               c["criteria"].values()) >= 1
                        or c.get("conflict_note")]
            task.comparison = {
                "rule": "candidates are COMPARED by the declared "
                        "criteria and the recorded evidence breakdown "
                        "above",
                "candidates_before_filtering": n_total,
                "by_support_count": by_support,
                "materially_relevant_rule": "at least one declared "
                                            "criterion met OR "
                                            "conflicting evidence "
                                            "recorded (categorical — no "
                                            "numerical threshold)",
                "candidates_after_filtering": len(material),
                "removed_from_record": 0,
                "resource_limit": "none enforced; every observable "
                                  "region is evaluated (counts "
                                  "reported above)",
            }
        met = [c for c in task.candidates if c["all_criteria_met"]]
        prev_uid = self._ledger_uids.get(tid)
        if len(met) == 1:
            new_status, new_pref = (CONCLUSION_EVIDENCE_PREFERRED,
                                    met[0]["candidate_id"])
        elif len(met) > 1:
            new_status, new_pref = (CONCLUSION_UNRESOLVED, None)
        else:
            new_status, new_pref = (CONCLUSION_UNRESOLVED, None)
        # re-version ONLY when the conclusion actually changes
        old = task.conclusion or {}
        if old.get("status") == new_status and \
                old.get("preferred") == new_pref and task.versions:
            self.tasks[tid] = task
            return task
        alts = [{"candidate_id": c["candidate_id"],
                 "why_not_preferred":
                     "declared criteria not all met: " +
                     ", ".join(k for k, v in c["criteria"].items()
                               if not v),
                 "supporting": len(c["supporting_evidence"]),
                 "counterevidence": len(c["counterevidence"]),
                 "conflict": bool(c.get("conflict_note"))}
                for c in task.candidates if not c["all_criteria_met"]]
        if len(met) == 1:
            task.conclude(
                status=CONCLUSION_EVIDENCE_PREFERRED,
                preferred=met[0]["candidate_id"],
                reasons=["the declared discriminating criteria are "
                         "all met by this candidate and by no other "
                         "(evidence distinguishes it for THIS task); "
                         "the sequence " +
                         str(met[0].get("chronology")) +
                         " is recorded as established; the region is "
                         "relevant evidence only — NOT proof of a "
                         "shift (E03-A/B) and never a trade signal"],
                discriminating_evidence=[c["name"] for c in
                                         declared["criteria"]],
                alternatives=alts, revision_of=prev_uid, recorded_at=as_of_time)
        elif len(met) > 1:
            task.conclude(
                status=CONCLUSION_UNRESOLVED,
                preferred=None,
                reasons=["multiple candidates meet the declared "
                         "criteria equally; the evidence does not "
                         "discriminate — no input-order tie-break is "
                         "used"],
                discriminating_evidence=[c["name"] for c in
                                         declared["criteria"]],
                alternatives=[{"candidate_id": c["candidate_id"],
                               "why_not_preferred":
                                   "equal with the others"}
                              for c in met],
                revision_of=prev_uid, recorded_at=as_of_time)
        else:
            task.conclude(
                status=CONCLUSION_UNRESOLVED, preferred=None,
                reasons=["no candidate meets the declared "
                         "discriminating criteria; no preference is "
                         "forced"],
                discriminating_evidence=[c["name"] for c in
                                         declared["criteria"]],
                alternatives=alts, revision_of=prev_uid, recorded_at=as_of_time)
        task.watch_next = [
            {"observable_event": "a further completed region on a "
                                 "watched frame whose geometry meets "
                                 "the declared criteria",
             "would_change": "re-open the comparison as a new "
                             "version",
             "would_weaken_or_suspend": "if the watch itself is "
                                        "closed without evidence",
             "alternative_remains": "every non-preferred candidate",
             "cannot_establish": "which region (if any) represents "
                                 "actual institutional activity"}]
        self.tasks[tid] = task
        self.seq_facts.append({
            "kind": "READING_TASK_CONCLUDED", "at":
                pd.Timestamp(as_of_time),
            "task_id": tid, "status": task.conclusion["status"],
            "layer": "CONTEXTUAL_INTERPRETATION"})
        return task

    def task_reference_for_review(self, *, refs: List[Any],
                                  as_of_time: pd.Timestamp,
                                  interacted: List[str],
                                  hf_trend: Optional[str] = None
                                  ) -> ReadingTask:
        """Declared task: which structural reference matters for
        reviewing the current higher-frame interpretation?  Evidence:
        an interaction (close-to-close transition / range relation) has
        actually been observed at that reference before as_of.  The
        evaluation rule is ENGINEERING (not a source statement)."""
        tid = "RT-REF-REVIEW"
        declared = {
            "question": "which reference's interaction matters for "
                        "reviewing the current higher-frame reading",
            "criteria": [
                {"name": "interaction_observed",
                 "meaning": "an interaction with the reference is "
                            "recorded at or before the analysis time",
                 "class": "ENGINEERING_INTERPRETATION"},
            ],
            "no_automatic_selection": "largest/nearest/newest/"
                                      "most-obvious references are "
                                      "NOT auto-selected",
            "evaluation_rule": {
                "kind": "ENGINEERING_INTERPRETATION",
                "rule": "exactly one candidate with an observed "
                        "interaction is required for a preference; "
                        "equal or absent evidence stays UNRESOLVED",
                "source_status": "NOT a source statement; an "
                                 "evaluation choice of this engine",
                "conflict_handling": "absence of an observed "
                                     "interaction is recorded as "
                                     "'not observed' (an absence, NOT "
                                     "proof that no interaction "
                                     "exists); every candidate stays "
                                     "in the record",
            },
        }
        task = self.tasks.get(tid) or ReadingTask(
            task_id=tid, question=declared["question"],
            declared=declared)
        task.declared = declared
        task.candidates = []
        seen_inter = set(interacted)
        for ref in refs:
            rid = str(getattr(ref, "candidate_id", ref))
            observed = rid in seen_inter
            task.candidates.append({
                "candidate_id": rid,
                "kind": "structural reference (F-K point)",
                "timeframe": "task frame",
                "level": float(getattr(ref, "level", float("nan"))),
                "availability": str(getattr(ref, "knowable_bar", "")),
                "criteria": {"interaction_observed": observed},
                "supporting_evidence":
                    (["an interaction with this reference is "
                      "recorded at or before " + str(as_of_time)]
                     if observed else []),
                "counterevidence": [],
                "unknowns":
                    (["no interaction with this reference has been "
                      "OBSERVED yet as of " + str(as_of_time) +
                      " — an absence of observation, not proof that "
                      "no interaction exists"] if not observed else []),
                "relation_to_context": {
                    "hf_trend": hf_trend,
                    "prior_events":
                        ("interaction recorded before " +
                         str(as_of_time)) if observed else
                        ("no interaction recorded before " +
                         str(as_of_time)),
                },
                "alternatives_note": "other references remain "
                                     "possible until their own "
                                     "interaction is observed"})
        n_total = len(task.candidates)
        task.comparison = {
            "rule": "candidates are COMPARED by observed interaction "
                    "(single declared criterion; engineering choice)",
            "candidates_before_filtering": n_total,
            "by_support_count":
                {"1": sum(1 for c in task.candidates
                          if c["criteria"]["interaction_observed"]),
                 "0": sum(1 for c in task.candidates
                          if not c["criteria"]["interaction_observed"])},
            "materially_relevant_rule": "an interaction is recorded "
                                        "(categorical — no numerical "
                                        "threshold)",
            "candidates_after_filtering":
                sum(1 for c in task.candidates
                    if c["criteria"]["interaction_observed"]),
            "removed_from_record": 0,
            "resource_limit": "none enforced; every confirmed "
                              "reference is evaluated",
        }
        obs = [c for c in task.candidates
               if c["criteria"]["interaction_observed"]]
        prev_uid = self._ledger_uids.get(tid)
        if len(obs) == 1:
            new_status, new_pref = (CONCLUSION_EVIDENCE_PREFERRED,
                                    obs[0]["candidate_id"])
        else:
            new_status, new_pref = (CONCLUSION_UNRESOLVED, None)
        old = task.conclusion or {}
        if old.get("status") == new_status and \
                old.get("preferred") == new_pref and task.versions:
            return task
        if len(obs) == 1:
            task.conclude(
                status=CONCLUSION_EVIDENCE_PREFERRED,
                preferred=obs[0]["candidate_id"],
                reasons=["an interaction is actually observed at "
                         "this reference and at no other (for the "
                         "declared review task)"],
                discriminating_evidence=["interaction_observed"],
                alternatives=[{"candidate_id": c["candidate_id"],
                               "why_not_preferred":
                                   "no interaction observed yet "
                                   "(still monitored)"}
                              for c in task.candidates
                              if c not in obs],
                revision_of=prev_uid, recorded_at=as_of_time)
        elif len(obs) > 1:
            task.conclude(
                status=CONCLUSION_UNRESOLVED, preferred=None,
                reasons=["interactions observed at several "
                         "references; the declared evidence does not "
                         "discriminate for this task"],
                discriminating_evidence=["interaction_observed"],
                alternatives=[{"candidate_id": c["candidate_id"],
                               "why_not_preferred": "equal evidence"}
                              for c in obs],
                revision_of=prev_uid, recorded_at=as_of_time)
        else:
            task.conclude(
                status=CONCLUSION_UNRESOLVED, preferred=None,
                reasons=["no interaction observed yet at any "
                         "reference; nothing justifies a preference"],
                discriminating_evidence=["interaction_observed"],
                alternatives=[{"candidate_id": c["candidate_id"],
                               "why_not_preferred":
                                   "no interaction observed"}
                              for c in task.candidates],
                revision_of=prev_uid, recorded_at=as_of_time)
        self.tasks[tid] = task
        return task

    # ---- working interpretations ---------------------------------------
    def interpretation_for_hf(self, *, as_of_time, trend, evidence,
                              derived_at) -> WorkingInterpretation:
        iid = "INT-HF-CONTEXT"
        interp = self.interps.get(iid)
        if interp is not None and interp.current_trend != str(trend):
            # the higher-frame context CHANGED → a linked revision
            # (old version preserved side-by-side), never silent replace
            old_trend = interp.current_trend
            interp.revise(
                statement=f"higher-frame context: {trend} (derived "
                          f"from completed structure; available at "
                          f"{derived_at})",
                reason="higher-frame context changed from "
                       f"{old_trend} to {trend} on new completed "
                       "structure",
                evidence=[{"id": f"trend_change:{old_trend}->{trend}",
                           "class": "DERIVATION"}],
                recorded_at=as_of_time)
            interp.current_trend = str(trend)
            self.seq_facts.append({
                "kind": "INTERPRETATION_REVISED", "at":
                    pd.Timestamp(as_of_time),
                "interp_id": iid, "revision": interp.revision_count,
                "layer": "CONTEXTUAL_INTERPRETATION"})
        elif interp is not None:
            return interp
        if interp is None:
            interp = WorkingInterpretation(
                interp_id=iid,
                question="what higher-frame context is currently "
                         "being used for the declared task",
                statement=f"higher-frame context: {trend} (derived "
                          f"from completed structure; available at "
                          f"{derived_at})",
                current_trend=str(trend),
                basis=[{"id": str(e), "class": "DERIVATION"}
                       for e in evidence],
                alternatives=[
                    {"statement": "the context may revise when "
                                  "completed structure changes",
                     "class": "ENGINEERING_INTERPRETATION"},
                    {"statement": "no context is source-established "
                                  "beyond the engine's derivation",
                     "class": "UNKNOWN_UNSUPPORTED"}],
                watch=[
                    {"observable_event":
                        "a completed structural change on the "
                        "higher frame (the engine's I-primary "
                        "direction revision)",
                     "would_change":
                         "the context statement is revised to a new "
                         "linked version",
                     "would_weaken_or_suspend":
                         "conflicting completed structure",
                     "alternative_remains":
                         "the previous context remains preserved as "
                         "history",
                     "cannot_establish":
                         "that the context predicts future prices"}])
            self.interps[iid] = interp
        return interp

    def interpretation_for_watch(self, *, watch: Dict[str, Any],
                                 as_of_time) -> WorkingInterpretation:
        iid = f"INT-WATCH-{watch.get('watch_id')}"
        interp = self.interps.get(iid)
        if interp is None:
            interp = WorkingInterpretation(
                interp_id=iid,
                question="what does the evidence so far support about "
                         "the watched possible shift",
                statement=("a possible shift is being WATCHED after "
                           "the recorded reference interaction — no "
                           "shift is established"),
                basis=[{"id": str(watch.get("watch_id")),
                        "class": "ENGINEERING_INTERPRETATION"}],
                alternatives=[
                    {"statement": "a shift occurred",
                     "class": "UNSUPPORTED_OR_UNAVAILABLE",
                     "why": "crossing/FVG items are contexts and "
                            "evidence, not proof (E03-A)"},
                    {"statement": "no shift is developing",
                     "class": "UNSUPPORTED_OR_UNAVAILABLE",
                     "why": "absence of evidence is not evidence of "
                            "absence"}],
                status=INTERP_UNRESOLVED,
                watch=[
                    {"observable_event":
                        "the declared watch questions' observables "
                        "(displacement/non-overlap bars; local-swing "
                        "crossing; a completed FVG meeting the task "
                        "criteria)",
                     "would_change":
                         "evidence items are appended; a declared "
                         "task may reach an evidence-preferred "
                         "conclusion",
                     "would_weaken_or_suspend":
                         "the watch's failure conditions recorded in "
                         "the shift-watch itself",
                     "alternative_remains":
                         "both 'shift' and 'no shift' remain open",
                     "cannot_establish":
                         "institutional intent, resting orders, or a "
                         "tradeable edge"}])
            self.interps[iid] = interp
        return interp

    # ---- ledger --------------------------------------------------------
    def _ledger_sync(self, obj_id: str, kind: str, result_task: str,
                     decision_bar: int, notes: List[str],
                     payload_inputs: Dict[str, Any],
                     definitions: Dict[str, Any], ledger,
                     provenance: List[str]) -> None:
        sig = tuple(notes)
        if self._ledger_sigs.get(obj_id) == sig:
            return
        res = SelectionResult(
            task_id=result_task, decision_bar=decision_bar,
            status="unresolved", selected_id=obj_id,
            survivors=[], excluded=[], unresolved=None,
            provenance=provenance,
            policy_refs=["RESEARCH_CONFIG_ONLY"],
            representation_id="connected-readings-v1",
            notes=list(notes), decision_time=pd.Timestamp.utcnow(),
            direction=None)
        payload = {
            "kind": kind, "run_id": self.run_id,
            "inputs": _jsonable(payload_inputs),
            "definitions": _jsonable(definitions),
            "revision_of": self._ledger_uids.get(obj_id),
            "stale": False, "stale_reason": None,
            "recompute_supported": False, "recompute": None,
            "recorded_event_times": [],
            "ledger_version_before": len(ledger.results),
            "ledger_version_after": None,
            "depends_on_results": [],
        }
        uid = ledger.record(res, payload)
        payload["ledger_version_after"] = len(ledger.results)
        self._ledger_uids[obj_id] = uid
        self._ledger_sigs[obj_id] = sig

    def sync_ledger(self, ledger) -> None:
        for tid, task in self.tasks.items():
            notes = [f"status={task.conclusion.get('status')}",
                     f"preferred={task.conclusion.get('preferred')}"]
            # PERFORMANCE (identical semantics): the sig check inside
            # _ledger_sync would still EVALUATE the payload argument
            # (a full task.to_record() asdict) on every boundary — the
            # dominant quadratic cost.  Skip BEFORE building payloads.
            if self._ledger_sigs.get(tid) == tuple(notes):
                continue
            self._ledger_sync(
                tid, "study_reading_task", "T-STUDY-READING",
                int(task.declared.get("decision_bar", 0)) if
                isinstance(task.declared.get("decision_bar"), int)
                else 0,
                notes,
                {"task": task.to_record()},
                {"conclusions": [CONCLUSION_EVIDENCE_PREFERRED,
                                 CONCLUSION_PROVISIONAL,
                                 CONCLUSION_UNRESOLVED],
                 "semantics": "preference requires declared "
                              "discriminating evidence; equal "
                              "candidates stay unresolved"},
                ledger, ["E03-A", "E03-B", "FVG16-A"])
        for iid, interp in self.interps.items():
            notes = [f"status={interp.status}",
                     f"versions={len(interp.versions)}",
                     interp.statement[:60]]
            if self._ledger_sigs.get(iid) == tuple(notes):
                continue
            self._ledger_sync(
                iid, "study_interpretation", "T-STUDY-INTERPRETATION",
                0, notes,
                {"interpretation": interp.to_record()},
                {"statuses": list(INTERP_STATUSES),
                 "semantics": "append-only versions; no automatic "
                              "opposite conclusion"},
                ledger, ["E03-A", "E12-A", "FVG16-A"])

    # ---- state ---------------------------------------------------------
    def state_dict(self) -> dict:
        return {
            "run_id": self.run_id, "instrument": self.instrument,
            "regions": {k: v.to_record()
                        for k, v in self.regions.items()},
            "links": [l.to_record() for l in self.links],
            "tasks": {k: v.to_record() for k, v in self.tasks.items()},
            "interps": {k: v.to_record()
                        for k, v in self.interps.items()},
            "seq_facts": _jsonable(self.seq_facts),
            "frame_cursors": dict(self._frame_cursors),
            "region_seq": self._region_seq,
            "link_seq": self._link_seq,
            "ledger_uids": dict(self._ledger_uids),
            "ledger_sigs": {k: list(v) for k, v in
                            self._ledger_sigs.items()},
            "seen_links": [list(k) for k in sorted(self._seen_links)],
            "linked_region_ids": sorted(self._linked_region_ids),
            "linked_ref_ids": sorted(self._linked_ref_ids),
            "selection_quality": "NOT_ESTABLISHED",
        }

    def load_state_dict(self, st: dict) -> None:
        self.run_id = st.get("run_id", self.run_id)
        self.instrument = st.get("instrument", self.instrument)
        self._frame_cursors = dict(st.get("frame_cursors", {}))
        self._region_seq = int(st.get("region_seq", 0))
        self._link_seq = int(st.get("link_seq", 0))
        self._ledger_uids = dict(st.get("ledger_uids", {}))
        self._ledger_sigs = {k: tuple(v) for k, v in
                             st.get("ledger_sigs", {}).items()}
        self._seen_links = set()
        for s in st.get("seen_links", []):
            if isinstance(s, (list, tuple)):
                self._seen_links.add(tuple(str(x) for x in s))
            else:                      # legacy pipe-joined string
                self._seen_links.add(tuple(str(s).split("|")))
        self._linked_region_ids = set(st.get("linked_region_ids", []))
        self._linked_ref_ids = set(st.get("linked_ref_ids", []))
        self.seq_facts = list(st.get("seq_facts", []))
        self.regions = {}
        for rid, d in st.get("regions", {}).items():
            self.regions[rid] = FVGRegion(
                region_id=d["region_id"], timeframe=d["timeframe"],
                direction=d["direction"], bar1=d["bar1"],
                bar2=d["bar2"], bar3=d["bar3"],
                lower_bound=d["lower_bound"],
                upper_bound=d["upper_bound"],
                observability_time=pd.Timestamp(
                    d["observability_time"]),
                instrument=d.get("instrument", "UNKNOWN"),
                timezone=d.get("timezone", "UTC"),
                session_convention=d.get("session_convention", ""),
                bar_convention=d.get("bar_convention", ""),
                interactions=d.get("interactions", []),
                interpretation_notes=d.get("interpretation_notes", []),
                scan_floor=int(d.get("scan_floor", -1)))
        self.links = []
        for d in st.get("links", []):
            self.links.append(FrameLink(
                link_id=d["link_id"], subject_id=d["subject_id"],
                subject_frame=d["subject_frame"],
                other_id=d["other_id"], other_frame=d["other_frame"],
                relation=d["relation"],
                established_at=pd.Timestamp(d["established_at"]),
                note=d.get("note", ""), evidence=d.get("evidence", {})))
        self.tasks = {}
        for tid, d in st.get("tasks", {}).items():
            t = ReadingTask(task_id=d["task_id"],
                            question=d["question"],
                            declared=d["declared"],
                            candidates=d.get("candidates", []),
                            conclusion=d.get("conclusion", {}),
                            watch_next=d.get("watch_next", []),
                            versions=d.get("versions", []),
                            comparison=d.get("comparison", {}))
            self.tasks[tid] = t
        self.interps = {}
        for iid, d in st.get("interps", {}).items():
            w = WorkingInterpretation(
                interp_id=d["interp_id"], question=d["question"],
                statement=d["statement"], basis=d.get("basis", []),
                alternatives=d.get("alternatives", []),
                status=d.get("status", INTERP_WORKING),
                watch=d.get("watch", []),
                versions=d.get("versions", []),
                revision_count=int(d.get("revision_count", 0)),
                current_trend=d.get("current_trend"))
            self.interps[iid] = w
