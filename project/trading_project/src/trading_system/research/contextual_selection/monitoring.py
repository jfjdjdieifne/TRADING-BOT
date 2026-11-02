"""Continuous monitoring layer V1 — local incremental analysis over a
stream of available observations, plus the causal step-by-step replay
contract.

WHAT THIS REUSES (verified in this repository)
----------------------------------------------
* ``market_understanding.price_path.CausalObservationStream`` — the
  EXISTING strict causal accepted-observation stream: validates every
  observation (OHLC legality, fail closed), enforces strictly increasing
  availability keys (duplicates and out-of-order input rejected, never
  silently sorted), and keeps same-batch chronology UNPROVEN.  This
  layer feeds every consumed observation through it — the stream IS the
  ingestion/validation interface.
* ``market_understanding.price_path.intrabar_path_metrics`` — the
  existing rule that OHLC never reveals whether a high preceded a low
  (``UNAVAILABLE(AMBIGUOUS_INTRABAR_CHRONOLOGY)``).  Same-bar ordering
  stays UNRESOLVED here too: this layer never fabricates an intra-bar
  order.
* ``analysis_lifecycle.AnalysisEngine`` — the deterministic analysis
  recompute at completed task-scale boundaries (the update mechanism).
* ``decision_layer`` / ``trade_plan`` — interpretation decisions and
  research-only plan states, revised through their existing immutable
  version records and the existing ``InterpretationLedger``.

WHAT IS NEW HERE (the missing path)
-----------------------------------
* ``ReplayObservationStream`` — replay a historical file ONE available
  observation at a time; the analysis engine at time T receives only the
  causally available prefix and approved time metadata (the timeline
  grid).  The full file stays in the driver; it is never handed to the
  engine.
* ``MonitoringLoop`` — incremental loop: validate -> advance -> update
  completed-bar facts -> diff -> record WHAT changed, WHY, and WHICH
  evidence caused it; when nothing material changed, preserve the state
  and record that no revision was required.  Step granularity follows
  the data source's actual resolution (``step_observation``) or a
  completed bar (``step_completed_bar``).
* Save / resume state in a FRESH PROCESS without exposing future data.
* ``DATA_CAPABILITIES`` / ``CONCEPT_REGISTER`` — what the available data
  can and cannot establish; per-concept inputs, availability time,
  operational observable event, interpretation, source, limitations,
  alternatives, revision dependencies.

HONESTY BOUNDARIES
------------------
* NO live market feed exists in this repository and none is connected:
  ``LIVE_FEED_STATUS["exists"] is False``.  A replayed stream is
  provided; the missing live adapter is identified (``LiveFeedAdapter``
  protocol is an interface only).  This layer must never be described as
  live-market monitoring.
* Individual trades and order-book data are NOT available in the input
  (reported aggregates only).  Resting orders, their size, participant
  identity and intent are NOT establishable from this data.
* A price crossing is an observable binding event — never automatically
  a 'successful liquidity sweep', 'rejection', 'reversal' or 'entry'.
* No position is ever inferred from price.
* ``selection_quality = NOT_ESTABLISHED``.
"""

from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import pandas as pd

from trading_system.research.information_time import (
    INFORMATION_KEY_VERSION,
    InformationKey,
    InformationPhase,
)

__all__ = [
    "DATA_CAPABILITIES", "CONCEPT_REGISTER", "LIVE_FEED_STATUS",
    "LiveFeedAdapter", "ReplayObservationStream", "MonitoringLoop",
    "StepReport", "CHANGE_ASPECTS",
]

_COMPLETED = InformationPhase.COMPLETED_ROW_AVAILABLE


# --------------------------------------------------------------------- #
# what the available data can and cannot establish                       #
# --------------------------------------------------------------------- #
DATA_CAPABILITIES: Dict[str, Dict[str, Any]] = {
    "ohlc_1m": {
        "status": "available",
        "kind": "direct-observation",
        "detail": "1-minute OHLC bars (timestamp = bucket start, "
                  "datetime_utc column), verified mirror of "
                  "parshant231234-eng/BTCUSDT-Historical-Data@27c9be70",
    },
    "reported_volume": {
        "status": "available",
        "kind": "reported-aggregate",
        "detail": "volume / quote_volume columns: REPORTED aggregates; "
                  "no inference of trade direction or participant",
    },
    "trade_count_taker_aggregates": {
        "status": "available",
        "kind": "reported-aggregate",
        "detail": "trade_count (a COUNT), taker_buy_volume, "
                  "taker_buy_quote_volume: aggregates only",
    },
    "individual_trades": {
        "status": "unavailable",
        "kind": "missing",
        "detail": "no per-trade records in the input; tick paths are not "
                  "reconstructible",
    },
    "order_book": {
        "status": "unavailable",
        "kind": "missing",
        "detail": "no order-book data in the input: resting orders, "
                  "their size, participant identity and intent CANNOT be "
                  "established; a prior high/low is at most a "
                  "source-supported reference for POTENTIAL liquidity",
    },
    "open_position": {
        "status": "absent",
        "kind": "authoritative-source-required",
        "detail": "no authoritative position feed was supplied; no "
                  "position is inferred from price",
    },
    "live_market_feed": {
        "status": "unavailable",
        "kind": "missing-adapter",
        "detail": "no live read-only data adapter exists in this "
                  "repository; only replayed streams are provided",
    },
}

LIVE_FEED_STATUS: Dict[str, Any] = {
    "exists": False,
    "adapter": None,
    "tested": False,
    "missing": "a live read-only market data adapter (exchange/API "
               "client) is NOT present; LiveFeedAdapter below is an "
               "interface contract only — this module never claims "
               "live-market monitoring",
}


class LiveFeedAdapter:
    """INTERFACE ONLY (missing implementation — see LIVE_FEED_STATUS).

    A live read-only adapter would emit the same observation records as
    ``ReplayObservationStream`` from a real-time source.  No such adapter
    exists in this repository; nothing here connects to a live feed.
    """

    def next_observation(self) -> dict:  # pragma: no cover - interface
        raise NotImplementedError(
            "no live read-only market data adapter exists in this "
            "repository (LIVE_FEED_STATUS['exists'] is False)")


# --------------------------------------------------------------------- #
# concept register (implemented concepts only; bounded)                  #
# --------------------------------------------------------------------- #
def _concept(**kw) -> Dict[str, Any]:
    return kw


CONCEPT_REGISTER: List[Dict[str, Any]] = [
    _concept(
        concept_id="C-OBS-COMPLETED-BAR",
        name="completed-bar observation",
        required_inputs="1m OHLC rows (mirror CSVs)",
        availability_time="the bar's completion time (never before)",
        observable_event="a parsed OHLC row whose bucket closed",
        interpretation="a direct observation; no participant or intent "
                       "is implied",
        source="engineering (input schema)",
        limitations="OHLC aggregates only; intra-bar path unknown",
        alternatives="none (the base observation type)",
        revision_dependencies="none (facts depend on it; it is never "
                              "revised)"),
    _concept(
        concept_id="C-DER-FK-SWING",
        name="F-K confirmed turning point / completed leg",
        required_inputs="completed task-scale bars; k (research "
                        "configuration)",
        availability_time="the candidate's knowable bar (k right bars "
                          "after occurrence) — a swing/HTF fact is NOT "
                          "available before its confirmation",
        observable_event="unique extreme in its window with k confirming "
                         "bars (operational: fk_turning_points / "
                         "build_legs, TIE-FT-EQ-FIRST)",
        interpretation="structural reference candidate (research "
                       "configuration; not a universal recipe)",
        source="pinned knowledge SRS-FK (paraphrase); ICT material not "
               "claimed for this detector",
        limitations="equal wicks kill candidates; supersession rules "
                    "apply; no claim that price 'must' react",
        alternatives="other swing families exist (knowledge 16); none "
                     "is authoritative",
        revision_dependencies="leg completion depends on its endpoint "
                              "knowability; a superseded point revises "
                              "legs that referenced it"),
    _concept(
        concept_id="C-DER-FAULTSIFIER-REF",
        name="falsifier reference (origin-of-last-confirmed-leg)",
        required_inputs="completed legs; task role; policy registry",
        availability_time="the reference point's knowable time",
        observable_event="the reference is selected or explicitly "
                         "unresolved (MP-UNRESOLVED) with reasons",
        interpretation="the boundary of the current claim; violation "
                       "loses support (T-S5/SP-04 semantics)",
        source="pinned knowledge SRS-CLAIM-SEM / T-S5 / SP-04 "
               "(paraphrase)",
        limitations="selection is a narrow research role, not the 'most "
                    "important' level; ties stay unresolved",
        alternatives="other references (e.g. OB zones) are NOT "
                     "operationalized here",
        revision_dependencies="interpretations and plans depend on it; "
                              "reference changes create new versions"),
    _concept(
        concept_id="C-EVT-SP03-BINDING",
        name="SP-03 close-based binding event (violation / continuation)",
        required_inputs="a completed bar's CLOSE; a reference level",
        availability_time="the binding bar's completion",
        observable_event="close strictly beyond the level on the "
                         "declared side (equality is NOT a crossing: "
                         "TIE-CROSS-EQUAL-UNBOUND-V1)",
        interpretation="a price crossing is OBSERVABLE; it is never "
                       "automatically a successful sweep, rejection, "
                       "reversal or entry",
        source="pinned knowledge SRS-SP03 (paraphrase)",
        limitations="close-based only; intrabar traversal unknown; "
                    "trade-through variants are a separate policy",
        alternatives="trade-through binding (P-V ambiguity, "
                     "close-based chosen as declared)",
        revision_dependencies="forecast/plan states depend on binding "
                              "events; later bars never rewrite earlier "
                              "observations"),
    _concept(
        concept_id="C-DER-SP05-CONTAINMENT",
        name="cross-scale containment (SP-05)",
        required_inputs="completed legs at two scales",
        availability_time="the later of the two legs' knowable times; "
                          "incomplete HTF bars are never used",
        observable_event="verifiable timestamp set relation "
                         "(contained / escaping / disjoint)",
        interpretation="lower-timeframe evidence relative to the "
                       "available higher-timeframe context",
        source="pinned knowledge SRS-SP05 (paraphrase)",
        limitations="state, not cause (knowledge 15 §15.2-15.4)",
        alternatives="none implemented",
        revision_dependencies="context feature for decisions; revised "
                              "when either scale's leg set changes"),
    _concept(
        concept_id="C-EVT-LIQUIDITY-REFERENCE",
        name="prior high/low as potential-liquidity reference",
        required_inputs="completed bars' extremes",
        availability_time="the extreme's confirmable time",
        observable_event="the level exists and later bars may cross it",
        interpretation="a source-supported reference for POTENTIAL "
                       "liquidity ONLY: OHLC alone does not prove "
                       "resting orders, size, participant identity or "
                       "intent; a crossing is not automatically a sweep",
        source="pinned knowledge 04_LIQUIDITY (directly-stated "
               "limitations; community mechanism unsupported CF-05)",
        limitations="no order-book data; no sweep/rejection labels are "
                    "produced",
        alternatives="multiple candidate readings are retained (04 §77)",
        revision_dependencies="interpretations cite it as evidence; it "
                              "is never promoted to cause"),
    _concept(
        concept_id="C-PLAN-HYPOTHETICAL",
        name="research-only hypothetical trade plan",
        required_inputs="decision preference; frozen reference/leg-end "
                        "levels",
        availability_time="plan record at its as-of; events after it",
        observable_event="entry/invalidation SP-03 bindings; objective = "
                         "completed leg after entry (declared research "
                         "configuration)",
        interpretation="analytical record, NOT an order; the ICT OB "
                       "entry technique is source-stated but NOT "
                       "implemented (G-OB-P not runnable)",
        source="trade_plan.SOURCE_EXAMPLES (claim classes recorded)",
        limitations="no execution, no position, no profitability; "
                    "entry/objective = declared research configuration",
        alternatives="source-grounded OB entry (blocked on owner-"
                     "declared P-N/P-W)",
        revision_dependencies="immutable version append on observed "
                              "events; ledger revision_of links"),
]


# --------------------------------------------------------------------- #
# replay observation stream (no future exposure)                         #
# --------------------------------------------------------------------- #
@dataclass
class _Obs:
    time: pd.Timestamp
    row: Dict[str, float]
    index: int


class ReplayObservationStream:
    """Replay a historical row frame ONE available observation at a
    time.  The driver may hold the full file; consumers only ever see
    ``prefix_rows()`` (rows up to the cursor) and the approved time grid.
    Every consumed observation is validated through the EXISTING
    ``CausalObservationStream`` (OHLC legality + strict key ordering;
    same-batch chronology stays unproven).
    """

    def __init__(self, rows: pd.DataFrame, *, timeline_id: str,
                 source_name: str = "mirror-1m",
                 dataset_identity: str = "BTCUSDT-mirror@27c9be70",
                 key_fn: Optional[Callable[[pd.Timestamp, int],
                                           InformationKey]] = None
                 ) -> None:
        from trading_system.market_understanding.contracts import (
            SchemaIdentity,
        )
        from trading_system.market_understanding.price_path import (
            CausalObservationStream,
            PublishedOhlcBarFact,
        )
        self._rows = rows.copy()
        self._times = pd.DatetimeIndex(self._rows.index)
        self._cursor = -1
        self._timeline_id = timeline_id
        self._dataset_identity = dataset_identity
        self._source = SchemaIdentity(source_name, "V1")
        self._causal = CausalObservationStream(
            source_identity=self._source, dataset_identity=dataset_identity)
        self._fact_cls = PublishedOhlcBarFact
        self._key_fn = key_fn
        self.rejected: List[dict] = []

    # ---- cursor ----
    @property
    def position(self) -> int:
        return self._cursor

    @property
    def current_time(self) -> Optional[pd.Timestamp]:
        if self._cursor < 0:
            return None
        return pd.Timestamp(self._times[self._cursor])

    @property
    def exhausted(self) -> bool:
        return self._cursor >= len(self._times) - 1

    def peek(self) -> Optional[dict]:
        if self.exhausted:
            return None
        return self._row_dict(self._cursor + 1)

    def next_observation(self) -> Optional[dict]:
        if self.exhausted:
            return None
        self._cursor += 1
        rec = self._row_dict(self._cursor)
        self._validate_and_accept(rec)
        return rec

    def prefix_rows(self) -> pd.DataFrame:
        """Rows consumed so far — the ONLY data the engine may see."""
        return self._rows.iloc[: self._cursor + 1].copy()

    def tail_rows(self) -> pd.DataFrame:
        """Rows after the cursor: driver-side ONLY (evaluation after
        they become available).  Never pass this to the engine at the
        current step."""
        return self._rows.iloc[self._cursor + 1:].copy()

    def accepted_count(self) -> int:
        return self._causal.accepted_count

    # ---- internals ----
    def _row_dict(self, i: int) -> dict:
        r = self._rows.iloc[i]
        return {"time": pd.Timestamp(self._times[i]), "index": i,
                "open": float(r["open"]), "high": float(r["high"]),
                "low": float(r["low"]), "close": float(r["close"]),
                "volume": float(r["volume"])
                if "volume" in self._rows.columns else 0.0}

    def _validate_and_accept(self, rec: dict) -> None:
        """Validate through the EXISTING causal observation stream."""
        key = self._key_for(rec)
        fact = self._fact_cls(
            open_price=rec["open"], high_price=rec["high"],
            low_price=rec["low"], close_price=rec["close"],
            availability_key=key, source_identity=self._source,
            dataset_identity=self._dataset_identity,
            published_bar_record_ref=f"mirror-row#{rec['index']}")
        self._causal.accept(fact)

    def _key_for(self, rec: dict) -> InformationKey:
        if self._key_fn is not None:
            return self._key_fn(rec["time"], rec["index"])
        # approved time metadata: the observation's availability key on
        # the declared timeline (strictly increasing positions; the
        # sealed InformationKey is the only key mechanism)
        return InformationKey(
            information_key_version=INFORMATION_KEY_VERSION,
            timeline_id=self._timeline_id,
            bar_position=int(rec["index"]),
            event_time_utc=pd.Timestamp(rec["time"]),
            information_phase=InformationPhase.COMPLETED_ROW_AVAILABLE,
            deterministic_sequence=int(rec["index"]),
        )


def completed_bars_only(df: pd.DataFrame, rows: pd.DataFrame
                        ) -> pd.DataFrame:
    """ONLY completed bars count as completed.  A bucket is kept iff its
    completion label is at or before the last available observation's
    own completion time; incomplete higher-timeframe bars are never
    used (their final high/low/close are not observations)."""
    if len(df) == 0 or len(rows) == 0:
        return df
    idx = pd.DatetimeIndex(rows.index)
    step = pd.Series(idx).diff().median()
    if pd.isna(step) or step is pd.Timedelta(0):
        step = pd.Timedelta(minutes=1)
    last_avail = pd.Timestamp(idx[-1]) + step
    return df[pd.DatetimeIndex(df.index) <= last_avail]


# --------------------------------------------------------------------- #
# step reports (what changed / why / which evidence)                     #
# --------------------------------------------------------------------- #
CHANGE_ASPECTS = ("lifecycle_state", "reference", "interpretation",
                  "forecast", "plan", "structural_facts")

_SAME_BAR_NOTE = ("sequence unresolved: events share one bar; OHLC "
                  "cannot order intra-bar events "
                  "(UNAVAILABLE(AMBIGUOUS_INTRABAR_CHRONOLOGY))")


@dataclass
class StepReport:
    step: int
    trigger: str                    # "observation" | "task-boundary"
    as_of: Optional[str]
    observation_time: Optional[str]
    material_change: bool
    changes: List[dict]
    no_revision_reason: Optional[str]
    sequence_notes: List[str]
    analysis_id: Optional[str]
    analysis_version: Optional[int]
    lifecycle_state: Optional[str]
    accepted_observations: int

    def to_record(self) -> dict:
        return dataclasses.asdict(self)

    def to_text(self) -> str:
        head = (f"[step {self.step}] {self.trigger} "
                f"obs={self.observation_time} as_of={self.as_of}")
        if not self.material_change:
            return (f"{head}\n  no revision required: "
                    f"{self.no_revision_reason}")
        L = [head, f"  MATERIAL CHANGE ({len(self.changes)}):"]
        for c in self.changes:
            L.append(f"   - [{c['aspect']}] {c['before']} -> {c['after']}")
            L.append(f"     why: {c['reason']}")
            L.append(f"     evidence: {c['evidence']}")
        for s in self.sequence_notes:
            L.append(f"   note: {s}")
        return "\n".join(L)


def _diff_records(prev, cur) -> List[dict]:
    """Field-level diff between two analysis records, with causes."""
    changes: List[dict] = []
    if prev is None:
        return changes
    if prev.lifecycle_state != cur.lifecycle_state:
        changes.append({
            "aspect": "lifecycle_state", "before": prev.lifecycle_state,
            "after": cur.lifecycle_state,
            "reason": cur.revision_reason or "state recomputed at the "
                      "new boundary",
            "evidence": [f"as_of {prev.as_of_time} -> {cur.as_of_time}"]})
    prev_ref = prev.reference_status.get("selected")
    cur_ref = cur.reference_status.get("selected")
    if prev.reference_status.get("status") != \
            cur.reference_status.get("status") or prev_ref != cur_ref:
        changes.append({
            "aspect": "reference",
            "before": f"{prev.reference_status.get('status')}:{prev_ref}",
            "after": f"{cur.reference_status.get('status')}:{cur_ref}",
            "reason": cur.reference_status.get("reason") or
                      "reference recomputed",
            "evidence": [str(cur.reference_status)]})
    prev_i = {i.interpretation_id: i for i in prev.interpretations}
    for i in cur.interpretations:
        p = prev_i.get(i.interpretation_id)
        if p is None or (p.status, p.description) != (i.status,
                                                      i.description):
            changes.append({
                "aspect": "interpretation",
                "before": f"{i.interpretation_id}:"
                          f"{p.status if p else '(absent)'}",
                "after": f"{i.interpretation_id}:{i.status}",
                "reason": "status/description recomputed from the "
                          "available evidence at this boundary",
                "evidence": (i.opposed_evidence[:2] if i.status !=
                             (p.status if p else None) else
                             i.supporting_evidence[:2])})
    prev_f = {f.forecast_id: f for f in prev.forecasts}
    for f in cur.forecasts:
        p = prev_f.get(f.forecast_id)
        if p is not None and (p.status, p.version) != (f.status,
                                                       f.version):
            ev = [str(e) for e in (f.status_evidence or [])][:2]
            changes.append({
                "aspect": "forecast",
                "before": f"{f.forecast_id}@v{p.version}:{p.status}",
                "after": f"{f.forecast_id}@v{f.version}:{f.status}",
                "reason": "watched condition observed after the record "
                          "(prior version preserved)",
                "evidence": ev or [f.if_event]})
        elif p is None:
            changes.append({
                "aspect": "forecast", "before": "(absent)",
                "after": f"{f.forecast_id}@v{f.version}:{f.status}",
                "reason": "new conditional forecast recorded",
                "evidence": [f.if_event]})
    prev_ids = {f.fact_id for f in prev.structural_facts}
    new_facts = [f.fact_id for f in cur.structural_facts
                 if f.fact_id not in prev_ids]
    if new_facts:
        changes.append({
            "aspect": "structural_facts", "before": "(subset)",
            "after": f"+{len(new_facts)} fact(s)",
            "reason": "new completed bars/legs became available",
            "evidence": new_facts[:3]})
    return changes


# --------------------------------------------------------------------- #
# the monitoring loop                                                    #
# --------------------------------------------------------------------- #
class MonitoringLoop:
    """Incremental analysis loop over an observation stream.

    Each ``step_observation`` consumes ONE available observation at the
    source's actual resolution.  Completed task-scale bars trigger the
    analysis recompute (the existing engine); observations inside an
    incomplete bar never change completed-bar facts and are reported as
    'no revision required'.  ``step_completed_bar`` advances to the next
    task-scale completion.  Prior records stay immutable (engine ledger
    appends; this loop appends journals only).
    """

    def __init__(self, *, stream: ReplayObservationStream,
                 frames_builder: Callable[[pd.DataFrame],
                                         Dict[str, pd.DataFrame]],
                 engine_factory: Callable[[Dict[str, pd.DataFrame]],
                                          Any],
                 task_scale: str = "4h",
                 grid_frames: Optional[Dict[str, pd.DataFrame]] = None,
                 study_layer: Optional[Any] = None
                 ) -> None:
        self.stream = stream
        self.frames_builder = frames_builder
        self.engine_factory = engine_factory
        self.task_scale = task_scale
        # STUDY LINKS (optional): a StudyReasoningLayer observing the
        # SAME flow — no side channel.  It sees each observation row in
        # the fast path and each analyzed boundary record; its state is
        # saved with the loop state.
        self.study_layer = study_layer
        # APPROVED TIME METADATA: the engine's causal axis is built once
        # from the declared time GRID (labels only — the stream's index).
        # Prices at any step come exclusively from
        # ``frames_builder(prefix_rows())``: ``engine.frames`` is
        # replaced by the prefix before EVERY analysis, so the engine
        # never sees future observations.
        self._grid_frames = (grid_frames if grid_frames is not None
                             else frames_builder(stream._rows))
        self.engine = None
        self.last_record = None
        self.journal: List[dict] = []
        self.step_no = 0
        self.plan = None

    # ---- step primitives ----
    def step_observation(self) -> StepReport:
        self.step_no += 1
        rec = self.stream.next_observation()
        if rec is None:
            return self._report("observation", None, False, [],
                                "stream exhausted", [], None)
        if not self._completes_task_bar(rec) and \
                self.last_record is not None:
            # O(1) fast path: this observation completes no task-scale
            # bar and no analysis is pending -> no completed-bar fact
            # can change (incomplete bars are never used)
            study_changes = []
            if self.study_layer is not None:
                study_changes = self.study_layer.on_observation(rec)
            if study_changes:
                report = self._report(
                    "observation", rec["time"], True, study_changes,
                    "finer observation touched an open study "
                    "candidate: re-evaluated at the actually "
                    "available resolution", [], None)
                self.journal.append(report.to_record())
                return report
            report = self._report(
                "observation", rec["time"], False, [],
                "no completed task-scale bar closed at this "
                "observation: incomplete bars are never used and no "
                "completed-bar fact changed", [], None)
            self.journal.append(report.to_record())
            return report
        frames = self._prefix_frames()
        completed_key = self._new_completion_key(frames)
        if completed_key is None:
            report = self._report(
                "observation", rec["time"], False, [],
                "no completed task-scale bar closed at this "
                "observation: incomplete bars are never used and no "
                "completed-bar fact changed", [], None)
            self.journal.append(report.to_record())
            return report
        if self.study_layer is not None:
            # the completing row is still an observation: let the study
            # layer see EVERY row (fine-touch evidence) before the
            # boundary analysis
            self.study_layer.on_observation(rec)
        return self._run_boundary(frames, completed_key, rec["time"])

    def _completes_task_bar(self, rec: dict) -> bool:
        """An observation completes a task-scale bar iff it is the last
        observation of its task bucket (the next row starts a new
        bucket, or the stream ends)."""
        times = self.stream._times
        i = rec["index"]
        if i >= len(times) - 1:
            return True
        hours = {"4h": 4, "1h": 1, "15m": 0.25}.get(self.task_scale, 4)
        width = pd.Timedelta(hours=hours)
        b_now = pd.Timestamp(times[i]).floor(width)
        b_next = pd.Timestamp(times[i + 1]).floor(width)
        return b_next != b_now

    def step_completed_bar(self) -> StepReport:
        """Advance observations until the next task-scale completion."""
        while True:
            report = self.step_observation()
            if report.trigger == "task-boundary" or self.stream.exhausted:
                return report

    def run_to(self, as_of: pd.Timestamp) -> List[StepReport]:
        """Advance until the task-scale completion at ``as_of`` has been
        processed (then STOP — nothing beyond it is consumed)."""
        target = pd.Timestamp(as_of)
        reports: List[StepReport] = []
        while not self.stream.exhausted:
            r = self.step_observation()
            reports.append(r)
            if (r.trigger == "task-boundary" and r.as_of is not None
                    and pd.Timestamp(r.as_of) >= target):
                break
        return reports

# ---- state save / resume (fresh process) ----
    def state_dict(self) -> dict:
        return {
            "cursor": self.stream.position,
            "step_no": self.step_no,
            "journal": self.journal,
            "engine_snapshot": self.engine_snapshot_state(),
            "last_analysis": (self.last_record.to_record()
                              if self.last_record is not None else None),
            "timeline_id": self.stream._timeline_id,
            "study_state": (self.study_layer.state_dict()
                            if self.study_layer is not None else None),
        }

    def save_state(self, path) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.state_dict(), fh, indent=1, sort_keys=True,
                      default=str)

    @classmethod
    def load_state(cls, path, *, stream, frames_builder, engine_factory,
                   task_scale: str = "4h", grid_frames=None,
                   study_layer: Optional[Any] = None
                   ) -> "MonitoringLoop":
        """Resume in a FRESH process: the stream advances to the saved
        cursor; the engine restores through the EXISTING snapshot
        mechanism; nothing past the saved boundary is ever analyzed."""
        import os
        import tempfile
        with open(path, encoding="utf-8") as fh:
            st = json.load(fh)
        loop = cls(stream=stream, frames_builder=frames_builder,
                   engine_factory=engine_factory, task_scale=task_scale,
                   grid_frames=grid_frames, study_layer=study_layer)
        while loop.stream.position < int(st["cursor"]):
            if loop.stream.next_observation() is None:
                break
        loop.step_no = int(st["step_no"])
        loop.journal = list(st["journal"])
        if st.get("last_analysis"):
            loop.last_record = _shim(st["last_analysis"])
        if st.get("study_state") and loop.study_layer is not None:
            loop.study_layer.load_state_dict(st["study_state"])
        frames = loop._prefix_frames()
        loop.engine = engine_factory(loop._grid_frames)
        loop.engine.frames = frames
        snap = st.get("engine_snapshot")
        if snap:
            fd, tmp = tempfile.mkstemp(suffix=".snapshot.json")
            os.close(fd)
            try:
                with open(tmp, "w", encoding="utf-8") as fh:
                    json.dump(snap, fh, default=str)
                loop.engine._load_snapshot(tmp)   # existing mechanism
            finally:
                os.unlink(tmp)
        return loop

    def engine_snapshot_state(self) -> dict:
        if self.engine is None:
            return {}
        snap = self.engine.snapshot_state()
        # round-trip completeness: the engine keeps restored records
        # separate from new ones; a re-saved snapshot must preserve the
        # FULL history (restored + new), never drop the restored part
        restored = list(getattr(self.engine, "_restored_records", [])
                        or [])
        new = [r.to_record() for r in self.engine.records]
        if restored:
            merged = restored + new
            snap = dict(snap)
            snap["records"] = merged
            if merged:
                snap["as_of_time"] = merged[-1].get("as_of_time")
                snap["as_of_bar"] = merged[-1].get("as_of_bar")
        return snap

    # ---- internals ----
    def _prefix_frames(self) -> Dict[str, pd.DataFrame]:
        rows = self.stream.prefix_rows()
        frames = self.frames_builder(rows)
        # causal rule: incomplete bars are never used as completed bars
        return {k: completed_bars_only(v, rows)
                for k, v in frames.items()}

    def _report(self, trigger, obs_time, material, changes, reason,
                notes, as_of) -> StepReport:
        r = StepReport(
            step=self.step_no, trigger=trigger,
            as_of=str(as_of) if as_of is not None else None,
            observation_time=str(obs_time) if obs_time is not None else
            None,
            material_change=material, changes=changes,
            no_revision_reason=None if material else reason,
            sequence_notes=list(notes),
            analysis_id=(self.last_record.analysis_id
                         if self.last_record is not None else None),
            analysis_version=(self.last_record.analysis_version
                              if self.last_record is not None else None),
            lifecycle_state=(self.last_record.lifecycle_state
                             if self.last_record is not None else None),
            accepted_observations=self.stream.accepted_count())
        return r

    def _new_completion_key(self, frames):
        idx = pd.DatetimeIndex(frames[self.task_scale].index)
        if self.last_record is None:
            # mid-move start: reconstruct from data available at the
            # CURRENT boundary (the latest completed bar), never replay
            # stale earlier boundaries behind the stream cursor
            return idx[-1] if len(idx) else None
        last_time = pd.Timestamp(self.last_record.as_of_time)
        newer = [t for t in idx if pd.Timestamp(t) > last_time]
        return newer[0] if newer else None

    def _last_completion_of(self, frames) -> pd.Timestamp:
        idx = pd.DatetimeIndex(frames[self.task_scale].index)
        return pd.Timestamp(idx[-1]) if len(idx) else pd.Timestamp(0)

    def _next_completion_time(self) -> Optional[pd.Timestamp]:
        frames = self._prefix_frames()
        key = self._new_completion_key(frames)
        return key

    def _run_boundary(self, frames, boundary_time, obs_time) -> StepReport:
        if self.engine is None:
            self.engine = self.engine_factory(
                self._grid_frames if self._grid_frames is not None
                else frames)
        # causal contract: prices come ONLY from the prefix frames
        self.engine.frames = frames
        rec = self.engine.analyze(boundary_time)
        changes = _diff_records(self.last_record, rec)
        if self.study_layer is not None:
            study_changes = self.study_layer.on_boundary(
                rec, frames, getattr(self.engine, "ledger", None))
            if study_changes:
                changes = list(changes) + list(study_changes)
        notes: List[str] = []
        material = bool(changes)
        if not material:
            reason = ("the new completed bar changed no recorded "
                      "interpretation, reference, forecast or fact: "
                      "state preserved; no revision required")
        else:
            reason = None
        # same-bar ordering honesty: any two changed events whose first
        # evidence shares one bar are NOT ordered
        bars = {}
        for c in changes:
            for e in c.get("evidence", []):
                s = str(e)
                for tok in s.replace(",", " ").split():
                    if tok.startswith("bar=") or tok.startswith("'bar'"):
                        pass
                if "'bar': " in s:
                    try:
                        b = int(s.split("'bar': ")[1].split(",")[0]
                                .split("}")[0])
                        bars.setdefault(b, 0)
                        bars[b] += 1
                    except (ValueError, IndexError):
                        pass
        if any(v >= 2 for v in bars.values()):
            notes.append(_SAME_BAR_NOTE)
        self.last_record = rec
        report = self._report("task-boundary", obs_time, material,
                              changes, reason, notes, boundary_time)
        self.journal.append(report.to_record())
        return report


class _Shim:
    """Attribute view over a serialized record dict (resume path)."""

    def __init__(self, d):
        self._d = d

    def __getattr__(self, k):
        v = self._d.get(k)
        return _shim(v)

    def to_record(self):
        return dict(self._d)

    def get(self, k, default=None):
        v = self._d.get(k, default)
        return _shim(v) if v is not None else v


def _shim(v):
    if isinstance(v, dict):
        return _Shim(v)
    if isinstance(v, list):
        return [_shim(x) for x in v]
    return v


