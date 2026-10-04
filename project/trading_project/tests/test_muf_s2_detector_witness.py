"""MUF V1 S2 — Detector Witness Adapter comprehensive & adversarial test suite.

Fixture discipline: SYNTHETIC SMALL FIXTURES ONLY (no owner data).
Verifies Closed Module 2.1A witness adaptation, Origin != Availability,
WITNESS_ONLY_NOT_MUF_AUTHORITATIVE separation, fail-closed promotion blocking
(I-PAUTH-1..4), dynamic schema/passthrough verification, prefix append
invariance (I-IMM-3), proof-noise identity invariance (I-IDB-1/2), deep
immutability, and S0 AST guard compliance.
"""
from dataclasses import replace
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from trading_system.market_understanding.availability import InformationAxis
from trading_system.market_understanding.contracts import (
    IllegalCausalReference,
    ImmutabilityViolation,
    IncomparableInformationKeys,
    InformationKeyViolation,
    PrematureAvailability,
    SchemaIdentity,
    SchemaViolation,
    TypedState,
    scan_market_shape_implementations,
    scan_private_imports,
    scan_prohibited_implementations,
)
from trading_system.market_understanding.detector_witness import (
    AUTHORITY_STATUS_WITNESS_ONLY,
    CANDIDATE_SIDE_HIGH,
    CANDIDATE_SIDE_LOW,
    CANDIDATE_SIDE_UNDECIDED,
    CandidateWitnessRecord,
    DetectorPolicyWitnessSpec,
    DetectorWitnessAsOfView,
    DetectorWitnessBundle,
    REASON_CANDIDATE_UNASSESSED,
    REASON_CANDIDATE_UNDECIDED,
    REASON_POLICY_GATE_INACTIVE,
    S2_ADAPTER_ENGINE_IDENTITY,
    S2_AUTHORITY_MISSING_NO_PROMOTION,
    S2_AXIS_MISMATCH,
    S2_CANDIDATE_WITNESS_RECORD_TYPE,
    S2_CONFIRMATION_POSITION_MISMATCH,
    S2_CONTRADICTORY_SWING_CONFIRMATION,
    S2_DATASET_MISMATCH,
    S2_DETECTOR_SCHEMA_MISMATCH,
    S2_DUPLICATE_OBSERVATION_KEY,
    S2_EMPTY_OBSERVATION_SEQUENCE,
    S2_EXPECTED_ANALYZE_COLUMNS,
    S2_FROZEN_2_1A_COLUMNS,
    S2_ILLEGAL_CANDIDATE_ORIGIN_TIMING,
    S2_ILLEGAL_SWING_ORIGIN_TIMING,
    S2_INVALID_BAR_FACT,
    S2_INVALID_CANDIDATE_PRICE_STATE,
    S2_INVALID_CANDIDATE_SIDE,
    S2_INVALID_WITNESS_POLICY,
    S2_NONFINITE_CONFIRMED_SWING_METRIC,
    S2_OUT_OF_ORDER_OBSERVATION,
    S2_PASSTHROUGH_TAMPERED,
    S2_SCHEMA_IDENTITY,
    S2_SOURCE_MISMATCH,
    S2_SWING_EVENT_WITNESS_RECORD_TYPE,
    S2_TIMELINE_MISMATCH,
    S2_UNCONFIRMED_ROW_CARRIES_SWING_POSITIONS,
    S2_UNEXPECTED_CONFIRMATION_WITHOUT_POLICY,
    SwingEventWitnessRecord,
    WITNESS_MODE_EVIDENCE_ONLY,
    WITNESS_MODE_EXTERNAL_POLICY,
    adapt_detector_witness_stream,
    promote_witness_to_authoritative_turning_point,
    query_authoritative_turning_points_as_of,
    query_witness_surface_as_of,
    verify_prefix_witness_invariance,
)
import trading_system.market_understanding.detector_witness as detector_witness_mod
from trading_system.market_understanding.identity import (
    AuthoritativeTurningPointReference,
    WaveProcessIdentityBasis,
)
from trading_system.market_understanding.price_path import (
    EXACT,
    UNAVAILABLE,
    PublishedOhlcBarFact,
    exact_metric,
)
from trading_system.research.information_time import (
    INFORMATION_KEY_VERSION,
    InformationKey,
    InformationPhase,
)
from trading_system.structure.swing_detector import (
    CausalAdaptiveSwingDetector,
    ConfirmationAssessment,
    ConfirmedEpisodeDiagnostic,
    EmpiricalConfirmationPolicy,
    SwingConfirmationRuntime,
)


SOURCE = SchemaIdentity("BinanceSpotKlinePublishedOhlc", "V1")
DATASET = "SYNTHETIC-S2-FIXTURE"
TIMELINE = "SYNTH_1m|1d"


def k(
    pos: int,
    *,
    seq: int = 0,
    ts=None,
    phase: InformationPhase = InformationPhase.COMPLETED_ROW_AVAILABLE,
    timeline: str = TIMELINE,
) -> InformationKey:
    return InformationKey(
        information_key_version=INFORMATION_KEY_VERSION,
        timeline_id=timeline,
        bar_position=pos,
        event_time_utc=ts,
        information_phase=phase,
        deterministic_sequence=seq,
    )


def mk_bar(
    pos: int,
    high: float,
    low: float,
    *,
    open_price: float | None = None,
    close_price: float | None = None,
    key: InformationKey | None = None,
    source: SchemaIdentity = SOURCE,
    dataset: str = DATASET,
    ref: str | None = None,
) -> PublishedOhlcBarFact:
    mid = (high + low) / 2.0
    return PublishedOhlcBarFact(
        open_price=mid if open_price is None else open_price,
        high_price=high,
        low_price=low,
        close_price=mid if close_price is None else close_price,
        availability_key=k(pos) if key is None else key,
        source_identity=source,
        dataset_identity=dataset,
        published_bar_record_ref=f"fixture-bar#{pos}" if ref is None else ref,
    )


def sample_bars() -> list[PublishedOhlcBarFact]:
    return [
        mk_bar(1, 10.0, 9.0),
        mk_bar(2, 11.0, 10.0),
        mk_bar(3, 10.8, 10.5),
        mk_bar(4, 10.6, 10.0),
        mk_bar(5, 11.2, 10.2),
    ]


def sample_policy() -> EmpiricalConfirmationPolicy:
    return EmpiricalConfirmationPolicy(
        quantile=0.5,
        prior_continuation_reversals=(0.01, 0.02),
    )


# 1 — Evidence-only mode (confirmation_policy=None) preserves continuous candidate witness
def test_muf_s2_01_evidence_only_mode_continuous_witness():
    bars = sample_bars()
    bundle = adapt_detector_witness_stream(bars)
    assert bundle.witness_mode == WITNESS_MODE_EVIDENCE_ONLY
    assert bundle.policy_witness_spec is TypedState.NOT_CONFIGURED
    assert bundle.policy_witness_ref is TypedState.NOT_CONFIGURED
    assert len(bundle.candidate_witnesses) == 5
    assert bundle.swing_event_witnesses == ()

    c0 = bundle.candidate_witnesses[0]
    assert c0.candidate_side == CANDIDATE_SIDE_UNDECIDED
    assert c0.candidate_origin_position is TypedState.NOT_APPLICABLE
    assert c0.candidate_origin_key is TypedState.NOT_APPLICABLE
    assert c0.candidate_price.semantics == UNAVAILABLE
    assert c0.candidate_price.reason == REASON_CANDIDATE_UNDECIDED
    assert c0.authority_status == AUTHORITY_STATUS_WITNESS_ONLY
    assert c0.muf_authority_policy_ref is TypedState.NOT_CONFIGURED

    c1 = bundle.candidate_witnesses[1]
    assert c1.candidate_side == CANDIDATE_SIDE_HIGH
    assert c1.candidate_origin_position == 1
    assert c1.candidate_origin_key == bars[1].availability_key
    assert c1.candidate_price.semantics == EXACT
    assert c1.candidate_price.value == 11.0
    assert c1.candidate_reversal_distance.semantics == UNAVAILABLE
    assert c1.candidate_reversal_distance.reason == REASON_CANDIDATE_UNASSESSED

    c2 = bundle.candidate_witnesses[2]
    assert c2.candidate_side == CANDIDATE_SIDE_HIGH
    assert c2.candidate_origin_position == 1
    assert c2.candidate_origin_key == bars[1].availability_key
    assert c2.candidate_reversal_distance.semantics == EXACT
    assert pytest.approx(c2.candidate_reversal_distance.value) == 0.5
    assert c2.candidate_reversal_fraction.semantics == EXACT
    assert pytest.approx(c2.candidate_reversal_fraction.value) == 0.5 / 11.0
    assert c2.candidate_policy_gate_value.semantics == UNAVAILABLE
    assert c2.candidate_policy_gate_value.reason == REASON_POLICY_GATE_INACTIVE


# 2 — External witness policy mode emits candidate & swing event witnesses as WITNESS_ONLY
def test_muf_s2_02_external_policy_mode_witness_only():
    bars = sample_bars()
    pol = sample_policy()
    bundle = adapt_detector_witness_stream(bars, confirmation_policy=pol)
    assert bundle.witness_mode == WITNESS_MODE_EXTERNAL_POLICY
    assert isinstance(bundle.policy_witness_spec, DetectorPolicyWitnessSpec)
    assert bundle.policy_witness_ref == bundle.policy_witness_spec.spec_identity
    assert len(bundle.candidate_witnesses) == 5
    assert len(bundle.swing_event_witnesses) == 2

    ev0, ev1 = bundle.swing_event_witnesses
    assert ev0.extrema_kind == CANDIDATE_SIDE_HIGH
    assert ev0.origin_position == 1
    assert ev0.confirmation_position == 2
    assert ev0.origin_key == bars[1].availability_key
    assert ev0.availability_key == bars[2].availability_key
    assert ev0.swing_price.value == 11.0
    assert ev0.swing_confirmation_price.value == 10.5
    assert ev0.authority_status == AUTHORITY_STATUS_WITNESS_ONLY
    assert ev0.muf_authority_policy_ref is TypedState.NOT_CONFIGURED

    assert ev1.extrema_kind == CANDIDATE_SIDE_LOW
    assert ev1.origin_position == 3
    assert ev1.confirmation_position == 4
    assert ev1.origin_key == bars[3].availability_key
    assert ev1.availability_key == bars[4].availability_key
    assert ev1.swing_price.value == 10.0
    assert ev1.swing_confirmation_price.value == 11.2
    assert ev1.authority_status == AUTHORITY_STATUS_WITNESS_ONLY
    assert ev1.muf_authority_policy_ref is TypedState.NOT_CONFIGURED

    # On confirmation bar 2, candidate witness reflects newly initialized opposite LOW candidate
    # while preserving confirmed_event_on_bar=True and swing_high_reversal_evidence.
    c2 = bundle.candidate_witnesses[2]
    assert c2.confirmed_event_on_bar is True
    assert c2.candidate_side == CANDIDATE_SIDE_LOW
    assert c2.candidate_origin_position == 2
    assert c2.swing_high_reversal_evidence.semantics == EXACT
    assert c2.swing_low_reversal_evidence.semantics == UNAVAILABLE


# 3 — Origin != Availability: swing event witness invisible at origin_key, visible at availability_key
def test_muf_s2_03_origin_not_equal_availability_no_backfill():
    bars = sample_bars()
    bundle = adapt_detector_witness_stream(bars, confirmation_policy=sample_policy())

    # At bar 2 (index 1, where HIGH extreme originated), confirmation has NOT happened yet!
    view_at_origin = query_witness_surface_as_of(bundle, at_key=bars[1].availability_key)
    assert len(view_at_origin.candidate_witnesses) == 2
    assert view_at_origin.swing_event_witnesses == ()

    # At bar 3 (index 2, where HIGH swing confirmed), first event becomes visible!
    view_at_conf = query_witness_surface_as_of(bundle, at_key=bars[2].availability_key)
    assert len(view_at_conf.candidate_witnesses) == 3
    assert len(view_at_conf.swing_event_witnesses) == 1
    assert view_at_conf.swing_event_witnesses[0].origin_key == bars[1].availability_key
    assert view_at_conf.swing_event_witnesses[0].availability_key == bars[2].availability_key


# 4 — D1 Annex D Attack 1 & 2: zero authoritative turning points & promotion fails closed
def test_muf_s2_04_no_authority_laundering_promotion_blocked():
    bars = sample_bars()
    bundle = adapt_detector_witness_stream(bars, confirmation_policy=sample_policy())
    ev = bundle.swing_event_witnesses[0]
    cand = bundle.candidate_witnesses[2]

    # Factual turning point query returns empty tuple at every bar
    for b in bars:
        assert query_authoritative_turning_points_as_of(bundle, at_key=b.availability_key) == ()

    # Promotion fails closed under NOT_CONFIGURED, None, DetectorPolicyWitnessSpec, or forged dict
    for attempt_policy in (
        TypedState.NOT_CONFIGURED,
        None,
        bundle.policy_witness_spec,
        {"forged_policy_artifact": "v1"},
    ):
        with pytest.raises(SchemaViolation) as exc_info:
            promote_witness_to_authoritative_turning_point(
                ev, muf_policy_artifact=attempt_policy
            )
        assert S2_AUTHORITY_MISSING_NO_PROMOTION in str(exc_info.value)

        with pytest.raises(SchemaViolation) as exc_info2:
            promote_witness_to_authoritative_turning_point(
                cand, muf_policy_artifact=attempt_policy
            )
        assert S2_AUTHORITY_MISSING_NO_PROMOTION in str(exc_info2.value)

    # S0 AuthoritativeTurningPointReference rejects S2 witness record_type
    with pytest.raises(SchemaViolation):
        AuthoritativeTurningPointReference(
            turning_point_identity=ev.record_identity,
            record_type=ev.as_record().record_type,
            schema_identity=S2_SCHEMA_IDENTITY,
            timeline_id=TIMELINE,
            availability_key=ev.availability_key,
        )


# 5 — Prefix truncation / future append invariance (I-IMM-3)
def test_muf_s2_05_prefix_truncation_and_append_invariance():
    extended_bars = sample_bars() + [
        mk_bar(6, 11.8, 10.9),
        mk_bar(7, 10.4, 9.5),
        mk_bar(8, 12.0, 10.1),
    ]
    pol = sample_policy()
    full_bundle = adapt_detector_witness_stream(extended_bars, confirmation_policy=pol)

    for prefix_len in range(1, len(extended_bars) + 1):
        prefix_bars = extended_bars[:prefix_len]
        prefix_bundle = adapt_detector_witness_stream(prefix_bars, confirmation_policy=pol)
        cutoff_key = prefix_bars[-1].availability_key
        assert verify_prefix_witness_invariance(
            prefix_bundle, full_bundle, at_key=cutoff_key
        )


# 6 — Policy witness spec determinism, parameter sensitivity, and proof-noise independence
def test_muf_s2_06_policy_witness_spec_determinism_and_proof_noise():
    bars = sample_bars()
    pol_a1 = EmpiricalConfirmationPolicy(
        quantile=0.5, prior_continuation_reversals=(0.01, 0.02)
    )
    pol_a2 = EmpiricalConfirmationPolicy(
        quantile=0.5, prior_continuation_reversals=(0.01, 0.02)
    )
    pol_b = EmpiricalConfirmationPolicy(
        quantile=0.75, prior_continuation_reversals=(0.01, 0.02)
    )

    spec_a1 = DetectorPolicyWitnessSpec.from_policy(pol_a1, caller_note="note-1")
    spec_a2 = DetectorPolicyWitnessSpec.from_policy(pol_a2, caller_note="note-2")
    spec_b = DetectorPolicyWitnessSpec.from_policy(pol_b, caller_note="note-1")

    # Proof-only caller_note never changes spec_identity (I-IDB-1/2)
    assert spec_a1.spec_identity == spec_a2.spec_identity
    # Different quantile changes spec_identity
    assert spec_a1.spec_identity != spec_b.spec_identity

    bundle_a1 = adapt_detector_witness_stream(
        bars, confirmation_policy=pol_a1, policy_caller_note="alpha"
    )
    bundle_a2 = adapt_detector_witness_stream(
        bars, confirmation_policy=pol_a2, policy_caller_note="beta"
    )
    bundle_b = adapt_detector_witness_stream(bars, confirmation_policy=pol_b)

    assert (
        bundle_a1.candidate_witnesses[2].record_identity
        == bundle_a2.candidate_witnesses[2].record_identity
    )
    assert (
        bundle_a1.swing_event_witnesses[0].record_identity
        == bundle_a2.swing_event_witnesses[0].record_identity
    )
    assert (
        bundle_a1.candidate_witnesses[2].record_identity
        != bundle_b.candidate_witnesses[2].record_identity
    )


# 7 — Provenance noise (dataset_identity, source_identity, bar_record_ref) excluded from record_identity
def test_muf_s2_07_provenance_noise_excluded_from_record_identity():
    pol = sample_policy()
    bars_1 = [
        mk_bar(i + 1, b.high_price, b.low_price, dataset="DS-1", ref=f"r1#{i}")
        for i, b in enumerate(sample_bars())
    ]
    alt_source = SchemaIdentity("AltSourceOhlc", "V9")
    bars_2 = [
        mk_bar(
            i + 1,
            b.high_price,
            b.low_price,
            source=alt_source,
            dataset="DS-2",
            ref=f"r2#{i}",
        )
        for i, b in enumerate(sample_bars())
    ]
    b1 = adapt_detector_witness_stream(bars_1, confirmation_policy=pol)
    b2 = adapt_detector_witness_stream(bars_2, confirmation_policy=pol)

    for c1, c2 in zip(b1.candidate_witnesses, b2.candidate_witnesses):
        assert c1.record_identity == c2.record_identity
    for e1, e2 in zip(b1.swing_event_witnesses, b2.swing_event_witnesses):
        assert e1.record_identity == e2.record_identity


# 8 — Input sequence validation: empty, non-sequence, duplicate, out-of-order, cross-timeline/axis/source/dataset
def test_muf_s2_08_input_sequence_fail_closed_gates():
    with pytest.raises(SchemaViolation) as exc_empty:
        adapt_detector_witness_stream(())
    assert S2_EMPTY_OBSERVATION_SEQUENCE in str(exc_empty.value)

    with pytest.raises(SchemaViolation) as exc_str:
        adapt_detector_witness_stream("not-a-bar-sequence")  # type: ignore[arg-type]
    assert S2_INVALID_BAR_FACT in str(exc_str.value)

    with pytest.raises(SchemaViolation) as exc_elem:
        adapt_detector_witness_stream(["not-a-bar"])  # type: ignore[list-item]
    assert S2_INVALID_BAR_FACT in str(exc_elem.value)

    # Duplicate key & out-of-order key rejected BEFORE detector.analyze is ever called
    class NeverCalledDetector(CausalAdaptiveSwingDetector):
        def analyze(self, df, *, high_col="high", low_col="low"):
            raise AssertionError("detector.analyze must not be called on invalid bar sequence")

    b1 = mk_bar(1, 10.0, 9.0)
    b1_dup = mk_bar(1, 11.0, 9.5)
    with pytest.raises(InformationKeyViolation) as exc_dup:
        adapt_detector_witness_stream(
            [b1, b1_dup], detector_instance=NeverCalledDetector()
        )
    assert S2_DUPLICATE_OBSERVATION_KEY in str(exc_dup.value)

    # Out-of-order key (no silent sorting, rejected before detector.analyze)
    b2 = mk_bar(2, 11.0, 9.5)
    with pytest.raises(PrematureAvailability) as exc_ooo:
        adapt_detector_witness_stream(
            [b2, b1], detector_instance=NeverCalledDetector()
        )
    assert S2_OUT_OF_ORDER_OBSERVATION in str(exc_ooo.value)

    # Cross-timeline
    b_other_tl = mk_bar(2, 11.0, 9.5, key=k(2, timeline="OTHER_TL"))
    with pytest.raises(InformationKeyViolation) as exc_tl:
        adapt_detector_witness_stream([b1, b_other_tl])
    assert S2_TIMELINE_MISMATCH in str(exc_tl.value)

    # Cross-axis (POSITIONAL vs TIME_INDEXED)
    b_timed = mk_bar(
        2, 11.0, 9.5, key=k(2, ts=pd.Timestamp("2026-05-01 00:02", tz="UTC"))
    )
    with pytest.raises(IncomparableInformationKeys) as exc_ax:
        adapt_detector_witness_stream([b1, b_timed])
    assert S2_AXIS_MISMATCH in str(exc_ax.value)

    # Cross-source
    b_other_src = mk_bar(2, 11.0, 9.5, source=SchemaIdentity("OtherSrc", "V1"))
    with pytest.raises(SchemaViolation) as exc_src:
        adapt_detector_witness_stream([b1, b_other_src])
    assert S2_SOURCE_MISMATCH in str(exc_src.value)

    # Cross-dataset
    b_other_ds = mk_bar(2, 11.0, 9.5, dataset="OTHER-DATASET")
    with pytest.raises(SchemaViolation) as exc_ds:
        adapt_detector_witness_stream([b1, b_other_ds])
    assert S2_DATASET_MISMATCH in str(exc_ds.value)


# 9 — Query validation: BAR_PRE_CLOSE, cross-timeline, cross-axis, incomparable keys
def test_muf_s2_09_query_surface_fail_closed_gates():
    bars = sample_bars()
    bundle = adapt_detector_witness_stream(bars, confirmation_policy=sample_policy())

    # BAR_PRE_CLOSE query rejected
    pre_close_key = k(2, phase=InformationPhase.BAR_PRE_CLOSE)
    with pytest.raises(IllegalCausalReference):
        query_witness_surface_as_of(bundle, at_key=pre_close_key)
    with pytest.raises(IllegalCausalReference):
        query_authoritative_turning_points_as_of(bundle, at_key=pre_close_key)

    # Cross-timeline query rejected
    other_tl_key = k(2, timeline="OTHER_TL")
    with pytest.raises(InformationKeyViolation):
        query_witness_surface_as_of(bundle, at_key=other_tl_key)
    with pytest.raises(InformationKeyViolation):
        query_authoritative_turning_points_as_of(bundle, at_key=other_tl_key)

    # Cross-axis query rejected
    timed_key = k(2, ts=pd.Timestamp("2026-05-01 00:02", tz="UTC"))
    with pytest.raises(IncomparableInformationKeys):
        query_witness_surface_as_of(bundle, at_key=timed_key)
    with pytest.raises(IncomparableInformationKeys):
        query_authoritative_turning_points_as_of(bundle, at_key=timed_key)


# 10 — TIME_INDEXED stream support & conflicting timestamp rejection
def test_muf_s2_10_time_indexed_stream_and_incomparable_query():
    t0 = pd.Timestamp("2026-05-01 00:00", tz="UTC")
    timed_bars = [
        mk_bar(
            i + 1,
            b.high_price,
            b.low_price,
            key=k(i + 1, ts=t0 + pd.Timedelta(minutes=i)),
        )
        for i, b in enumerate(sample_bars())
    ]
    bundle = adapt_detector_witness_stream(
        timed_bars, confirmation_policy=sample_policy()
    )
    assert bundle.axis is InformationAxis.TIME_INDEXED
    assert len(bundle.swing_event_witnesses) == 2

    # Conflicting timestamp at same bar_position fails closed with IncomparableInformationKeys
    conflicting_key = k(3, ts=t0 + pd.Timedelta(minutes=99))
    with pytest.raises(IncomparableInformationKeys):
        query_witness_surface_as_of(bundle, at_key=conflicting_key)
    with pytest.raises(IncomparableInformationKeys):
        query_authoritative_turning_points_as_of(bundle, at_key=conflicting_key)


# 11 — Outside bar & equal highs/lows behavior in Module 2.1A witness
def test_muf_s2_11_outside_bar_and_equal_extremes_witness():
    # Bar 1: [9, 10] -> UNDECIDED
    # Bar 2: [8, 11] (outside bar: extends both high and low) -> stays UNDECIDED!
    # Bar 3: [9, 12] -> breaks high -> HIGH with origin at index 2 (bar 3)
    # Bar 4: [9.5, 12] (equal high 12.0) -> retains origin at index 2, assesses 12.0 - 9.5 = 2.5
    bars = [
        mk_bar(1, 10.0, 9.0),
        mk_bar(2, 11.0, 8.0),
        mk_bar(3, 12.0, 9.0),
        mk_bar(4, 12.0, 9.5),
    ]
    bundle = adapt_detector_witness_stream(bars)
    assert bundle.candidate_witnesses[0].candidate_side == CANDIDATE_SIDE_UNDECIDED
    assert bundle.candidate_witnesses[1].candidate_side == CANDIDATE_SIDE_UNDECIDED
    assert bundle.candidate_witnesses[2].candidate_side == CANDIDATE_SIDE_HIGH
    assert bundle.candidate_witnesses[2].candidate_origin_position == 2
    assert bundle.candidate_witnesses[3].candidate_side == CANDIDATE_SIDE_HIGH
    # Equal high does NOT reset origin to index 3; retains earlier origin 2
    assert bundle.candidate_witnesses[3].candidate_origin_position == 2
    assert bundle.candidate_witnesses[3].candidate_origin_key == bars[2].availability_key
    assert pytest.approx(bundle.candidate_witnesses[3].candidate_reversal_distance.value) == 2.5


# 12 — Dynamic schema mirror gate & passthrough tamper gate
def test_muf_s2_12_rogue_detector_schema_and_passthrough_gates():
    bars = sample_bars()

    class ExtraColumnDetector(CausalAdaptiveSwingDetector):
        def analyze(self, df, *, high_col="high", low_col="low"):
            out = super().analyze(df, high_col=high_col, low_col=low_col)
            out["rogue_col"] = 0
            return out

    with pytest.raises(SchemaViolation) as exc_col:
        adapt_detector_witness_stream(bars, detector_instance=ExtraColumnDetector())
    assert S2_DETECTOR_SCHEMA_MISMATCH in str(exc_col.value)

    class ReorderedColumnDetector(CausalAdaptiveSwingDetector):
        def analyze(self, df, *, high_col="high", low_col="low"):
            out = super().analyze(df, high_col=high_col, low_col=low_col)
            cols = list(out.columns)
            cols[0], cols[1] = cols[1], cols[0]
            return out[cols]

    with pytest.raises(SchemaViolation) as exc_ord:
        adapt_detector_witness_stream(bars, detector_instance=ReorderedColumnDetector())
    assert S2_DETECTOR_SCHEMA_MISMATCH in str(exc_ord.value)

    class HighTamperDetector(CausalAdaptiveSwingDetector):
        def analyze(self, df, *, high_col="high", low_col="low"):
            out = super().analyze(df, high_col=high_col, low_col=low_col)
            out["high"] = out["high"] + 1.0
            return out

    with pytest.raises(SchemaViolation) as exc_high:
        adapt_detector_witness_stream(bars, detector_instance=HighTamperDetector())
    assert S2_PASSTHROUGH_TAMPERED in str(exc_high.value)

    class LowTamperDetector(CausalAdaptiveSwingDetector):
        def analyze(self, df, *, high_col="high", low_col="low"):
            out = super().analyze(df, high_col=high_col, low_col=low_col)
            out["low"] = out["low"] - 1.0
            return out

    with pytest.raises(SchemaViolation) as exc_low:
        adapt_detector_witness_stream(bars, detector_instance=LowTamperDetector())
    assert S2_PASSTHROUGH_TAMPERED in str(exc_low.value)


# 13 — Policy spoofing & rogue confirmation / timing gates
def test_muf_s2_13_policy_spoofing_and_rogue_confirmation_gates():
    bars = sample_bars()
    pol = sample_policy()

    # Detector initialized with policy, but caller claims confirmation_policy=None
    with pytest.raises(SchemaViolation) as exc_spoof:
        adapt_detector_witness_stream(
            bars,
            confirmation_policy=None,
            detector_instance=CausalAdaptiveSwingDetector(pol),
        )
    assert S2_INVALID_WITNESS_POLICY in str(exc_spoof.value)

    # Rogue detector confirming in evidence-only mode
    class RogueUnconfiguredConfirmDetector(CausalAdaptiveSwingDetector):
        def analyze(self, df, *, high_col="high", low_col="low"):
            out = super().analyze(df, high_col=high_col, low_col=low_col)
            out.loc[2, "swing_high_confirmed"] = True
            out.loc[2, "swing_origin_position"] = 1
            out.loc[2, "swing_confirmation_position"] = 2
            return out

    with pytest.raises(SchemaViolation) as exc_unexp:
        adapt_detector_witness_stream(
            bars, detector_instance=RogueUnconfiguredConfirmDetector()
        )
    assert S2_UNEXPECTED_CONFIRMATION_WITHOUT_POLICY in str(exc_unexp.value)

    # Rogue detector setting both swing_high_confirmed and swing_low_confirmed True
    class ContradictoryConfirmDetector(CausalAdaptiveSwingDetector):
        def analyze(self, df, *, high_col="high", low_col="low"):
            out = super().analyze(df, high_col=high_col, low_col=low_col)
            out.loc[2, "swing_high_confirmed"] = True
            out.loc[2, "swing_low_confirmed"] = True
            return out

    with pytest.raises(SchemaViolation) as exc_contra:
        adapt_detector_witness_stream(
            bars,
            confirmation_policy=pol,
            detector_instance=ContradictoryConfirmDetector(pol),
        )
    assert S2_CONTRADICTORY_SWING_CONFIRMATION in str(exc_contra.value)

    # Rogue detector setting swing_origin_position >= swing_confirmation_position
    class IllegalOriginTimingDetector(CausalAdaptiveSwingDetector):
        def analyze(self, df, *, high_col="high", low_col="low"):
            out = super().analyze(df, high_col=high_col, low_col=low_col)
            out.loc[2, "swing_origin_position"] = 2
            return out

    with pytest.raises(SchemaViolation) as exc_orig:
        adapt_detector_witness_stream(
            bars,
            confirmation_policy=pol,
            detector_instance=IllegalOriginTimingDetector(pol),
        )
    assert S2_ILLEGAL_SWING_ORIGIN_TIMING in str(exc_orig.value)

    # Rogue detector with swing_confirmation_position != row index
    class BadConfPosDetector(CausalAdaptiveSwingDetector):
        def analyze(self, df, *, high_col="high", low_col="low"):
            out = super().analyze(df, high_col=high_col, low_col=low_col)
            out.loc[2, "swing_confirmation_position"] = 1
            return out

    with pytest.raises(SchemaViolation) as exc_cpos:
        adapt_detector_witness_stream(
            bars,
            confirmation_policy=pol,
            detector_instance=BadConfPosDetector(pol),
        )
    assert S2_CONFIRMATION_POSITION_MISMATCH in str(exc_cpos.value)

    # Rogue detector leaving swing positions on unconfirmed row
    class UnconfirmedPosCarryDetector(CausalAdaptiveSwingDetector):
        def analyze(self, df, *, high_col="high", low_col="low"):
            out = super().analyze(df, high_col=high_col, low_col=low_col)
            out.loc[0, "swing_origin_position"] = 0
            return out

    with pytest.raises(SchemaViolation) as exc_carry:
        adapt_detector_witness_stream(
            bars, detector_instance=UnconfirmedPosCarryDetector()
        )
    assert S2_UNCONFIRMED_ROW_CARRIES_SWING_POSITIONS in str(exc_carry.value)


# 14 — Rogue candidate state / origin / price gates
def test_muf_s2_14_rogue_candidate_state_gates():
    bars = sample_bars()

    class BadCandidateSideDetector(CausalAdaptiveSwingDetector):
        def analyze(self, df, *, high_col="high", low_col="low"):
            out = super().analyze(df, high_col=high_col, low_col=low_col)
            out.loc[1, "candidate_side"] = "BOGUS"
            return out

    with pytest.raises(SchemaViolation) as exc_side:
        adapt_detector_witness_stream(
            bars, detector_instance=BadCandidateSideDetector()
        )
    assert S2_INVALID_CANDIDATE_SIDE in str(exc_side.value)

    class FutureCandidateOriginDetector(CausalAdaptiveSwingDetector):
        def analyze(self, df, *, high_col="high", low_col="low"):
            out = super().analyze(df, high_col=high_col, low_col=low_col)
            out.loc[1, "candidate_origin_position"] = 3
            return out

    with pytest.raises(SchemaViolation) as exc_fut:
        adapt_detector_witness_stream(
            bars, detector_instance=FutureCandidateOriginDetector()
        )
    assert S2_ILLEGAL_CANDIDATE_ORIGIN_TIMING in str(exc_fut.value)

    class UndecidedWithPriceDetector(CausalAdaptiveSwingDetector):
        def analyze(self, df, *, high_col="high", low_col="low"):
            out = super().analyze(df, high_col=high_col, low_col=low_col)
            out.loc[0, "candidate_price"] = 10.0
            return out

    with pytest.raises(SchemaViolation) as exc_price:
        adapt_detector_witness_stream(
            bars, detector_instance=UndecidedWithPriceDetector()
        )
    assert S2_INVALID_CANDIDATE_PRICE_STATE in str(exc_price.value)


# 15 — Custom SwingConfirmationPolicy subclass support & validation
def test_muf_s2_15_custom_confirmation_policy_witness_spec():
    class CustomPolicy:
        def __init__(self, min_frac: float) -> None:
            self.min_frac = min_frac

        def create_runtime(self) -> SwingConfirmationRuntime:
            min_f = self.min_frac

            class _Runtime:
                continuation_history_count = 0
                confirmed_history_count = 0

                def assess(self, reversal_fraction: float) -> ConfirmationAssessment:
                    ok = bool(reversal_fraction >= min_f)
                    return ConfirmationAssessment(
                        confirmed=ok,
                        reversal_evidence=0.5,
                        continuation_history_count=0,
                        threshold=min_f,
                    )

                def finalize_continuation_episode(self, maximum_reversal_fraction):
                    return False

                def record_confirmed_episode(self, maximum_reversal_fraction):
                    return ConfirmedEpisodeDiagnostic(
                        percentile=float("nan"),
                        prior_confirmed_history_count=0,
                    )

            return _Runtime()

    bars = sample_bars()
    custom_pol = CustomPolicy(0.02)

    # Missing custom_policy_parameters rejected fail-closed
    with pytest.raises(SchemaViolation) as exc_missing:
        adapt_detector_witness_stream(bars, confirmation_policy=custom_pol)
    assert S2_INVALID_WITNESS_POLICY in str(exc_missing.value)

    # With explicit custom_policy_parameters succeeds and hashes deterministically
    bundle = adapt_detector_witness_stream(
        bars,
        confirmation_policy=custom_pol,
        custom_policy_parameters={"min_frac": 0.02},
    )
    assert bundle.witness_mode == WITNESS_MODE_EXTERNAL_POLICY
    assert len(bundle.swing_event_witnesses) >= 1


# 16 — Deep immutability & direct constructor tamper resistance
def test_muf_s2_16_deep_immutability_and_constructor_tamper_resistance():
    bars = sample_bars()
    bundle = adapt_detector_witness_stream(bars, confirmation_policy=sample_policy())
    cand = bundle.candidate_witnesses[2]
    ev = bundle.swing_event_witnesses[0]

    # Direct attribute mutation blocked
    with pytest.raises((ImmutabilityViolation, TypeError, AttributeError)):
        cand.candidate_side = "HIGH"  # type: ignore[misc]
    with pytest.raises((ImmutabilityViolation, TypeError, AttributeError)):
        ev.swing_price = exact_metric(999.0)  # type: ignore[misc]
    with pytest.raises((ImmutabilityViolation, TypeError, AttributeError)):
        cand.as_record().content["candidate_side"] = "HIGH"
    with pytest.raises((ImmutabilityViolation, TypeError, AttributeError)):
        ev.as_record().content["swing_price"] = {}

    # Direct constructor tamper: mismatch between wrapper attribute and published_record.content
    with pytest.raises(SchemaViolation):
        replace(cand, candidate_price=exact_metric(999.0))
    with pytest.raises(SchemaViolation):
        replace(ev, swing_price=exact_metric(999.0))
    with pytest.raises(SchemaViolation):
        replace(ev, authority_status="MUF_AUTHORITATIVE")
    with pytest.raises(SchemaViolation):
        replace(
            bundle,
            candidate_witnesses=bundle.candidate_witnesses[:-1],
        )

    # DetectorWitnessAsOfView rejects lookahead record in direct construction
    with pytest.raises((PrematureAvailability, IllegalCausalReference, SchemaViolation)):
        DetectorWitnessAsOfView(
            timeline_id=TIMELINE,
            query_key=bars[1].availability_key,
            witness_mode=bundle.witness_mode,
            policy_witness_ref=bundle.policy_witness_ref,
            candidate_witnesses=bundle.candidate_witnesses[:2],
            swing_event_witnesses=(ev,),  # ev availability_key is bars[2] > bars[1]!
            authoritative_turning_points=(),
        )


# 17 — S0 AST guards on detector_witness.py and frozen 2.1A column mirror check
def test_muf_s2_17_ast_guards_and_dynamic_2_1a_mirror():
    source_text = Path(detector_witness_mod.__file__).read_text(encoding="utf-8")
    assert scan_private_imports(source_text) == ()
    assert scan_prohibited_implementations(source_text) == ()
    assert scan_market_shape_implementations(source_text) == ()

    # Dynamic runtime verification against live CausalAdaptiveSwingDetector output
    probe_df = pd.DataFrame({"high": [10.0, 11.0], "low": [9.0, 10.0]})
    live_out = CausalAdaptiveSwingDetector().analyze(probe_df)
    assert tuple(live_out.columns) == S2_EXPECTED_ANALYZE_COLUMNS
    assert tuple(live_out.columns)[2:] == S2_FROZEN_2_1A_COLUMNS


# 18 — DetectorPolicyWitnessSpec validation & tamper resistance
def test_muf_s2_18_policy_witness_spec_validation_gates():
    pol = sample_policy()
    spec = DetectorPolicyWitnessSpec.from_policy(pol, caller_note="ok")

    with pytest.raises(SchemaViolation) as exc_bad_type:
        DetectorPolicyWitnessSpec.from_policy("not-a-policy")  # type: ignore[arg-type]
    assert S2_INVALID_WITNESS_POLICY in str(exc_bad_type.value)

    with pytest.raises(SchemaViolation) as exc_extra_custom:
        DetectorPolicyWitnessSpec.from_policy(
            pol, custom_parameters={"unexpected": 1}
        )
    assert S2_INVALID_WITNESS_POLICY in str(exc_extra_custom.value)

    with pytest.raises(SchemaViolation) as exc_unconf_custom:
        adapt_detector_witness_stream(
            sample_bars(),
            confirmation_policy=None,
            custom_policy_parameters={"unexpected": 1},
        )
    assert S2_INVALID_WITNESS_POLICY in str(exc_unconf_custom.value)

    with pytest.raises(SchemaViolation):
        replace(spec, authority_scope="MUF_POLICY_ARTIFACT")
    with pytest.raises(SchemaViolation):
        replace(spec, muf_policy_artifact_ref= TypedState.UNAVAILABLE)
    with pytest.raises(SchemaViolation):
        replace(spec, spec_identity="0" * 64)


# 19 — Non-finite confirmed swing metrics & negative history counts rejected
def test_muf_s2_19_nonfinite_confirmed_metrics_and_negative_counts_rejected():
    bars = sample_bars()
    pol = sample_policy()

    class NanConfirmedPriceDetector(CausalAdaptiveSwingDetector):
        def analyze(self, df, *, high_col="high", low_col="low"):
            out = super().analyze(df, high_col=high_col, low_col=low_col)
            out.loc[2, "swing_price"] = float("nan")
            return out

    with pytest.raises(SchemaViolation) as exc_nan:
        adapt_detector_witness_stream(
            bars,
            confirmation_policy=pol,
            detector_instance=NanConfirmedPriceDetector(pol),
        )
    assert S2_NONFINITE_CONFIRMED_SWING_METRIC in str(exc_nan.value)

    class InfReversalDistanceDetector(CausalAdaptiveSwingDetector):
        def analyze(self, df, *, high_col="high", low_col="low"):
            out = super().analyze(df, high_col=high_col, low_col=low_col)
            out.loc[2, "candidate_reversal_distance"] = float("inf")
            return out

    with pytest.raises(SchemaViolation) as exc_inf:
        adapt_detector_witness_stream(
            bars, detector_instance=InfReversalDistanceDetector()
        )
    assert S2_NONFINITE_CONFIRMED_SWING_METRIC in str(exc_inf.value)

    class NegativeHistoryCountDetector(CausalAdaptiveSwingDetector):
        def analyze(self, df, *, high_col="high", low_col="low"):
            out = super().analyze(df, high_col=high_col, low_col=low_col)
            out.loc[1, "candidate_continuation_history_count"] = -1
            return out

    with pytest.raises(SchemaViolation):
        adapt_detector_witness_stream(
            bars, detector_instance=NegativeHistoryCountDetector()
        )


# 20 — Confirmed episode diagnostic percentile transitions from UNAVAILABLE to EXACT
def test_muf_s2_20_confirmed_history_percentile_progression():
    bars = sample_bars()
    pol = sample_policy()
    bundle = adapt_detector_witness_stream(bars, confirmation_policy=pol)
    assert len(bundle.swing_event_witnesses) == 2

    first_ev, second_ev = bundle.swing_event_witnesses
    # First confirmed swing has 0 prior confirmed swings -> percentile is UNAVAILABLE
    assert first_ev.swing_confirmed_history_count == 0
    assert first_ev.swing_confirmed_history_percentile.semantics == UNAVAILABLE
    # Second confirmed swing has 1 prior confirmed swing -> percentile is EXACT in [0, 1]
    assert second_ev.swing_confirmed_history_count == 1
    assert second_ev.swing_confirmed_history_percentile.semantics == EXACT
    assert 0.0 <= second_ev.swing_confirmed_history_percentile.value <= 1.0


# 21 — verify_prefix_witness_invariance negative proof (detects divergence)
def test_muf_s2_21_verify_prefix_witness_invariance_detects_divergence():
    bars_a = sample_bars()
    bars_b = [
        mk_bar(1, 10.0, 9.0),
        mk_bar(2, 12.5, 10.0),  # altered bar 2 high
        mk_bar(3, 10.8, 10.5),
        mk_bar(4, 10.6, 10.0),
        mk_bar(5, 11.2, 10.2),
    ]
    pol = sample_policy()
    bundle_a = adapt_detector_witness_stream(bars_a[:3], confirmation_policy=pol)
    bundle_b = adapt_detector_witness_stream(bars_b, confirmation_policy=pol)

    with pytest.raises(SchemaViolation):
        verify_prefix_witness_invariance(
            bundle_a, bundle_b, at_key=bars_a[2].availability_key
        )

    # Also detects policy witness divergence between evidence-only and external policy
    bundle_ev = adapt_detector_witness_stream(bars_a[:3], confirmation_policy=None)
    bundle_pol = adapt_detector_witness_stream(bars_a, confirmation_policy=pol)
    with pytest.raises(SchemaViolation):
        verify_prefix_witness_invariance(
            bundle_ev, bundle_pol, at_key=bars_a[2].availability_key
        )


# 22 — DetectorWitnessBundle direct constructor invariant enforcement
def test_muf_s2_22_bundle_direct_constructor_invariant_gates():
    bars = sample_bars()
    pol = sample_policy()
    bundle = adapt_detector_witness_stream(bars, confirmation_policy=pol)
    ev_bundle = adapt_detector_witness_stream(bars, confirmation_policy=None)

    # Empty observation_keys rejected
    with pytest.raises(SchemaViolation):
        replace(bundle, observation_keys=(), candidate_witnesses=())

    # EVIDENCE_ONLY bundle with swing_event_witnesses rejected
    with pytest.raises(SchemaViolation):
        replace(ev_bundle, swing_event_witnesses=bundle.swing_event_witnesses)

    # EXTERNAL_POLICY bundle with NOT_CONFIGURED spec rejected
    with pytest.raises(SchemaViolation):
        replace(bundle, policy_witness_spec=TypedState.NOT_CONFIGURED)

    # Mismatched confirmed_event_on_bar vs swing_event_witnesses rejected
    with pytest.raises(SchemaViolation):
        replace(bundle, swing_event_witnesses=bundle.swing_event_witnesses[:1])


# 23 — Integration with S1 CausalObservationStream
def test_muf_s2_23_s1_causal_observation_stream_integration():
    from trading_system.market_understanding.price_path import CausalObservationStream

    bars = sample_bars()
    s1_stream = CausalObservationStream(
        source_identity=SOURCE, dataset_identity=DATASET
    )
    for b in bars:
        s1_stream.accept(b)

    bundle = adapt_detector_witness_stream(bars, confirmation_policy=sample_policy())
    assert bundle.observation_keys == s1_stream.accepted_keys
    assert bundle.dataset_identity == s1_stream.dataset_identity
    assert bundle.source_identity == SOURCE


# 24 — SwingDetectorError translated fail-closed to SchemaViolation
def test_muf_s2_24_swing_detector_error_translated_to_schema_violation():
    from trading_system.structure.swing_detector import SwingDataError

    class FailingDetector(CausalAdaptiveSwingDetector):
        def analyze(self, df, *, high_col="high", low_col="low"):
            raise SwingDataError("synthetic 2.1A failure")

    with pytest.raises(SchemaViolation) as exc_info:
        adapt_detector_witness_stream(
            sample_bars(), detector_instance=FailingDetector()
        )
    assert "Module 2.1A execution error" in str(exc_info.value)


# 25 — Flat / zero-excursion bar sequence produces clean typed metrics without raw NaN
def test_muf_s2_25_flat_bars_zero_excursion_clean_metrics():
    flat_bars = [mk_bar(i, 10.0, 10.0) for i in range(1, 6)]
    bundle = adapt_detector_witness_stream(flat_bars)
    assert len(bundle.candidate_witnesses) == 5
    for cand in bundle.candidate_witnesses:
        assert cand.candidate_side == CANDIDATE_SIDE_UNDECIDED
        assert cand.candidate_price.semantics == UNAVAILABLE
        assert cand.candidate_origin_key is TypedState.NOT_APPLICABLE


# 26 — Signed-zero (-0.0 vs 0.0), list-vs-tuple canonical equivalence, and NaN/Inf rejection in policy spec
def test_muf_s2_26_signed_zero_and_container_canonical_equivalence_in_policy_spec():
    pol_pos_zero = EmpiricalConfirmationPolicy(
        quantile=0.0, prior_continuation_reversals=(0.0, 0.02)
    )
    pol_neg_zero = EmpiricalConfirmationPolicy(
        quantile=-0.0, prior_continuation_reversals=(-0.0, 0.02)
    )
    spec_pos = DetectorPolicyWitnessSpec.from_policy(pol_pos_zero)
    spec_neg = DetectorPolicyWitnessSpec.from_policy(pol_neg_zero)
    assert spec_pos.spec_identity == spec_neg.spec_identity
    assert spec_pos.policy_parameters == spec_neg.policy_parameters
    assert repr(spec_pos.policy_parameters) == repr(spec_neg.policy_parameters)

    class DummyCustomPolicy:
        def create_runtime(self) -> SwingConfirmationRuntime:
            raise NotImplementedError

    c_list = DetectorPolicyWitnessSpec.from_policy(
        DummyCustomPolicy(),
        custom_parameters={"priors": [0.01, -0.0], "flag": True},
    )
    c_tuple = DetectorPolicyWitnessSpec.from_policy(
        DummyCustomPolicy(),
        custom_parameters={"flag": True, "priors": (0.01, 0.0)},
    )
    assert c_list.spec_identity == c_tuple.spec_identity

    for bad_val in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(SchemaViolation) as exc_bad:
            DetectorPolicyWitnessSpec.from_policy(
                DummyCustomPolicy(),
                custom_parameters={"bad": bad_val},
            )
        assert S2_INVALID_WITNESS_POLICY in str(exc_bad.value)


# 27 — WaveProcessIdentityBasis cannot be constructed from S2 witness records
def test_muf_s2_27_wave_process_identity_basis_rejects_s2_witness():
    bars = sample_bars()
    bundle = adapt_detector_witness_stream(bars, confirmation_policy=sample_policy())
    ev0, ev1 = bundle.swing_event_witnesses

    with pytest.raises(SchemaViolation):
        tp_ref = AuthoritativeTurningPointReference(
            turning_point_identity=ev0.record_identity,
            record_type=ev0.as_record().record_type,
            schema_identity=S2_SCHEMA_IDENTITY,
            timeline_id=TIMELINE,
            availability_key=ev0.availability_key,
        )
        WaveProcessIdentityBasis(
            representation_spec_hash="a" * 64,
            authority_policy_hash=bundle.policy_witness_spec.spec_identity,
            timeline_id=TIMELINE,
            start_turning_point=tp_ref,
            direction="UP",
        )


# 28 — Linear-scaling complexity gate (I-P-1) over 500 synthetic bars
def test_muf_s2_28_linear_scaling_500_bars():
    n = 500
    bars = []
    for i in range(1, n + 1):
        wave = 5.0 * np.sin(i * 0.25)
        mid = 100.0 + wave
        bars.append(mk_bar(i, mid + 1.0, mid - 1.0))

    bundle = adapt_detector_witness_stream(bars, confirmation_policy=sample_policy())
    assert len(bundle.candidate_witnesses) == n
    assert len(bundle.swing_event_witnesses) > 10
    for ev in bundle.swing_event_witnesses:
        assert 0 <= ev.origin_position < ev.confirmation_position < n
        assert ev.origin_key < ev.availability_key


# 29 — Load-bearing guard proof via isolated monkeypatch
def test_muf_s2_29_load_bearing_guard_proof(monkeypatch):
    bars = sample_bars()

    class TamperingDetector(CausalAdaptiveSwingDetector):
        def analyze(self, df, *, high_col="high", low_col="low"):
            out = super().analyze(df, high_col=high_col, low_col=low_col)
            out["high"] = out["high"] + 100.0
            return out

    # With real _verify_detector_output_frame, tampering is caught
    with pytest.raises(SchemaViolation) as exc_info:
        adapt_detector_witness_stream(bars, detector_instance=TamperingDetector())
    assert S2_PASSTHROUGH_TAMPERED in str(exc_info.value)

    # If _verify_detector_output_frame were bypassed, tampered frame would pass through
    monkeypatch.setattr(
        detector_witness_mod,
        "_verify_detector_output_frame",
        lambda out, *, expected_high, expected_low: out,
    )
    bypassed_bundle = adapt_detector_witness_stream(
        bars, detector_instance=TamperingDetector()
    )
    assert len(bypassed_bundle.candidate_witnesses) == len(bars)


# 30 — Sealed S0 and S1 certificates remain byte-identical
def test_muf_s2_30_sealed_s0_and_s1_certificates_untouched():
    import hashlib

    root = Path(__file__).resolve().parent.parent
    for cert_rel in (
        "docs/releases/MODULE_MUF_V1_S0_ACCEPTED_SRC_TESTS.sha256",
        "docs/releases/MODULE_MUF_V1_S1_ACCEPTED_SRC_TESTS.sha256",
    ):
        cert_path = root / cert_rel
        lines = [
            ln.strip()
            for ln in cert_path.read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
        assert len(lines) > 0
        for line in lines:
            expected_sha, rel_file = line.split(None, 1)
            actual_sha = hashlib.sha256((root / rel_file).read_bytes()).hexdigest()
            assert actual_sha == expected_sha, (cert_rel, rel_file)


