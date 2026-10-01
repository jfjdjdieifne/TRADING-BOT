"""MUF V1 S1 — price_path module gates (tests 1-20; builder self-tests).

Fixture discipline: SYNTHETIC SMALL FIXTURES ONLY (no owner data). Every value
below is fabricated for mathematical validation of the S1 price-path contract.
"""
import pytest

from trading_system.research.information_time import (
    INFORMATION_KEY_VERSION,
    InformationKey,
    InformationKeyError,
    InformationPhase,
)
import pandas as pd

from trading_system.market_understanding.availability import (
    InformationAxis,
    InformationBatchKey,
    SourceBatchIdentity,
)
from trading_system.market_understanding.contracts import (
    ImmutabilityViolation,
    IncomparableInformationKeys,
    InformationKeyViolation,
    PrematureAvailability,
    SchemaIdentity,
    SchemaViolation,
    TypedState,
)
from trading_system.market_understanding.identity import (
    ArtifactIdentitySchema,
    canonical_artifact_identity,
)
from trading_system.market_understanding.price_path import (
    ADJACENCY_GRID_CONTIGUOUS,
    ADJACENCY_OBSERVATION_ADJACENT,
    AMBIGUOUS_INTRABAR_CHRONOLOGY,
    BOUND,
    BOUNDARY_CONTRACTS,
    DESCRIPTOR_STAGES,
    DISCRETE_TV_TRIANGLE_INEQUALITY,
    EXACT,
    PUBLISHED_OHLC_FACT,
    SAME_BATCH_ORDER_UNPROVEN,
    S1_DUPLICATE_OBSERVATION_KEY,
    S1_INVALID_OHLC,
    S1_OUT_OF_ORDER_OBSERVATION,
    UNAVAILABLE,
    UNBOUNDED_REFINEMENT,
    ZERO_DENOMINATOR,
    AcceptedBarFacts,
    CausalObservationStream,
    DeclaredGrid,
    DescriptorSpec,
    PublishedOhlcBarFact,
    RunningExtremeState,
    bar_derivative_metrics,
    canonical_origin_order,
    exact_metric,
    intrabar_path_metrics,
    key_axis,
    key_serialization,
    pair_adjacency_kind,
    pair_direction,
    pair_metrics,
    pair_wall_clock_duration,
    pair_bar_count_duration,
    safe_ratio,
)

SOURCE = SchemaIdentity("BinanceSpotKlinePublishedOhlc", "V1")
DATASET = "BTCUSDT-1m-2026-05"
TIMELINE = "BTCUSDT_1m|1d"


def k(pos, seq=0, ts=None, phase=InformationPhase.COMPLETED_ROW_AVAILABLE, timeline=TIMELINE):
    return InformationKey(
        information_key_version=INFORMATION_KEY_VERSION,
        timeline_id=timeline,
        bar_position=pos,
        event_time_utc=ts,
        information_phase=phase,
        deterministic_sequence=seq,
    )


def batch(pos, ref, status=SourceBatchIdentity.KNOWN_SAME_BATCH, timeline=TIMELINE):
    return InformationBatchKey(
        timeline_id=timeline,
        axis=InformationAxis.POSITIONAL,
        causal_position=pos,
        information_phase=InformationPhase.COMPLETED_ROW_AVAILABLE,
        source_batch_status=status,
        source_batch_ref=ref,
    )


def bar(pos, o=10.0, h=12.0, low=8.0, c=11.0, *, key=None, info_batch=None, source=SOURCE):
    return PublishedOhlcBarFact(
        open_price=o,
        high_price=h,
        low_price=low,
        close_price=c,
        availability_key=key if key is not None else k(pos),
        source_identity=source,
        dataset_identity=DATASET,
        published_bar_record_ref=f"fixture-bar#{pos}",
        information_batch=info_batch,
    )


def stream():
    return CausalObservationStream(source_identity=SOURCE, dataset_identity=DATASET)


# 1 — strict OHLC legality (no clipping, fail closed)
def test_muf_s1_price_path_01_invalid_ohlc_rejected():
    with pytest.raises(SchemaViolation):
        bar(1, o=10.0, h=9.0, low=8.0, c=11.0)  # high below close
    with pytest.raises(SchemaViolation):
        bar(1, o=10.0, h=12.0, low=10.5, c=11.0)  # low above open
    with pytest.raises(SchemaViolation):
        bar(1, o=10.0, h=8.0, low=9.0, c=10.5)  # high below low
    with pytest.raises(SchemaViolation):
        bar(1, o=0.0, h=12.0, low=8.0, c=11.0)  # zero price
    with pytest.raises(SchemaViolation):
        bar(1, o=-1.0, h=12.0, low=8.0, c=11.0)  # negative price
    with pytest.raises(SchemaViolation):
        PublishedOhlcBarFact(
            open_price=float("inf"),
            high_price=12.0,
            low_price=8.0,
            close_price=11.0,
            availability_key=k(1),
            source_identity=SOURCE,
            dataset_identity=DATASET,
            published_bar_record_ref="x",
        )


# 2 — completed-bar facts require COMPLETED_ROW_AVAILABLE phase
def test_muf_s1_price_path_02_completed_row_phase_required():
    with pytest.raises(PrematureAvailability):
        bar(1, key=k(1, phase=InformationPhase.BAR_PRE_CLOSE))


# 3 — intrabar lower bound (discrete triangle inequality fixture)
def test_muf_s1_price_path_03_intrabar_lower_bound_fixture():
    metrics = intrabar_path_metrics(bar(1, o=10.0, h=12.0, low=8.0, c=11.0))
    lower = metrics["intrabar_path_length_lower_bound"]
    assert lower.semantics == BOUND
    assert lower.value == 7.0  # (12-8) + min(3, 5)
    assert lower.bound_basis == DISCRETE_TV_TRIANGLE_INEQUALITY
    exact = metrics["intrabar_path_length_exact"]
    assert exact.semantics == UNAVAILABLE
    assert exact.value is TypedState.UNAVAILABLE
    assert exact.reason == AMBIGUOUS_INTRABAR_CHRONOLOGY
    upper = metrics["intrabar_path_length_upper_bound"]
    assert upper.semantics == UNAVAILABLE
    assert upper.reason == UNBOUNDED_REFINEMENT


# 4 — zero denominators are typed UNDEFINED(ZERO_DENOMINATOR); no epsilon
def test_muf_s1_price_path_04_zero_denominator_typed():
    assert safe_ratio(1, 0) is TypedState.UNDEFINED
    assert safe_ratio(0, 0) is TypedState.UNDEFINED
    assert safe_ratio(3, 2) == 1.5
    assert safe_ratio(1, 5e-324) > 0  # no epsilon floor


# 5 — bar derivative metrics P3-P5 are EXACT facts
def test_muf_s1_price_path_05_bar_derivative_metrics():
    metrics = bar_derivative_metrics(bar(1, o=10.0, h=12.0, low=8.0, c=11.0))
    assert metrics["bar_range"].value == 4.0
    assert metrics["open_close_displacement"].value == 1.0
    assert metrics["upper_wick"].value == 1.0
    assert metrics["lower_wick"].value == 2.0
    for result in metrics.values():
        assert result.semantics == EXACT


# 6 — pair magnitudes P1/P2 are order-free EXACT facts
def test_muf_s1_price_path_06_pair_magnitudes_exact():
    metrics = pair_metrics(bar(1, c=11.0), bar(2, h=13.0, c=12.5))
    assert metrics["close_path_step"].semantics == EXACT
    assert metrics["close_path_step"].value == 1.5


# 7 — signed displacement EXACT when chronology proven (different batches)
def test_muf_s1_price_path_07_signed_displacement_when_chronology_proven():
    left = bar(1, c=11.0, info_batch=batch(1, "2026-05-01|1d"))
    right = bar(2, h=13.0, c=12.5, info_batch=batch(2, "2026-05-02|1d"))
    metrics = pair_metrics(left, right)
    displacement = metrics["close_displacement"]
    assert displacement.semantics == EXACT
    assert displacement.value == 1.5
    assert pair_direction(left, right) == "UP"


# 8 — same-batch chronology unproven: signed facts typed UNDEFINED
def test_muf_s1_price_path_08_same_batch_signed_undefined():
    shared = batch(1, "2026-05-01|1d")
    left = bar(1, c=11.0, info_batch=shared)
    right = bar(2, h=13.0, c=12.5, info_batch=shared)
    metrics = pair_metrics(left, right)
    displacement = metrics["close_displacement"]
    assert displacement.semantics == UNAVAILABLE
    assert displacement.value is TypedState.UNDEFINED
    assert displacement.reason == SAME_BATCH_ORDER_UNPROVEN
    assert metrics["close_path_step"].value == 1.5  # magnitude stays EXACT
    assert pair_direction(left, right) is TypedState.UNDEFINED


# 9 — direction vocabulary: UP / DOWN / FLAT only
def test_muf_s1_price_path_09_direction_vocabulary():
    assert pair_direction(bar(1, c=10.0), bar(2, c=12.0)) == "UP"
    assert pair_direction(bar(1, c=12.0), bar(2, c=10.0)) == "DOWN"
    assert pair_direction(bar(1, c=11.0), bar(2, c=11.0)) == "FLAT"


# 10 — stream strict causal order; out-of-order rejected (fail closed)
def test_muf_s1_price_path_10_stream_strict_order():
    st = stream()
    st.accept(bar(1))
    st.accept(bar(2))
    st.accept(bar(4))
    with pytest.raises(SchemaViolation) as caught:
        st.accept(bar(3, c=11.5))  # unseen but strictly smaller than the last key
    assert S1_OUT_OF_ORDER_OBSERVATION in str(caught.value)
    with pytest.raises(SchemaViolation) as caught:
        st.accept(bar(0))
    assert S1_OUT_OF_ORDER_OBSERVATION in str(caught.value)


# 11 — duplicate observation keys rejected deterministically
def test_muf_s1_price_path_11_stream_duplicate_rejected():
    st = stream()
    st.accept(bar(1))
    with pytest.raises(SchemaViolation) as caught:
        st.accept(bar(1))
    assert S1_DUPLICATE_OBSERVATION_KEY in str(caught.value)


# 12 — no silent sorting: rejected input never changes stream state
def test_muf_s1_price_path_12_stream_never_silently_sorts():
    st = stream()
    st.accept(bar(2))
    with pytest.raises(SchemaViolation):
        st.accept(bar(1))
    assert st.accepted_count == 1
    assert st.last_accepted_key == k(2)
    assert st.accepted_keys == (k(2),)


# 13 — cross-timeline and cross-axis streams forbidden
def test_muf_s1_price_path_13_cross_timeline_and_axis_rejected():
    st = stream()
    st.accept(bar(1))
    with pytest.raises(InformationKeyViolation):
        st.accept(bar(2, key=k(2, timeline="OTHER|1d")))
    st2 = stream()
    positional = bar(1, key=k(1))
    time_indexed = bar(
        2,
        key=k(2, ts=pd.Timestamp("2026-05-02 00:00", tz="UTC")),
    )
    st2.accept(positional)
    with pytest.raises(InformationKeyViolation):
        st2.accept(time_indexed)
    with pytest.raises(IncomparableInformationKeys):
        pair_wall_clock_duration(k(9, timeline="OTHER|1d"), k(2))


# 14 — incomparable keys fail closed (conflicting timestamp provenance)
def test_muf_s1_price_path_14_incomparable_fail_closed():
    left = bar(1, key=k(5, ts=pd.Timestamp("2026-05-01 00:00", tz="UTC")))
    right = bar(2, key=k(5, ts=pd.Timestamp("2026-05-02 00:00", tz="UTC")))
    st = stream()
    st.accept(left)
    with pytest.raises(InformationKeyError):
        st.accept(right)  # same causal coordinate, conflicting timestamps
    assert st.accepted_count == 1


# 15 — running extremes: ties form an unordered semantic set (no winner)
def test_muf_s1_price_path_15_running_extremes_no_winner():
    st = stream()
    st.accept(bar(1, h=12.0, low=8.0))
    st.accept(bar(2, h=12.0, low=8.0))
    st.accept(bar(3, h=12.0, low=8.0))
    high = st.running_high_state
    assert high.value == 12.0
    assert high.origins_unordered == frozenset({k(1), k(2), k(3)})
    assert high.origins == canonical_origin_order((k(1), k(2), k(3)))
    low = st.running_low_state
    assert low.origins_unordered == frozenset({k(1), k(2), k(3)})


# 16 — axis semantics: no invented timestamps; wall-clock TIME_INDEXED only
def test_muf_s1_price_path_16_axis_semantics_and_durations():
    assert key_axis(k(1)) is InformationAxis.POSITIONAL
    assert key_axis(k(1, ts=pd.Timestamp("2026-05-01 00:00", tz="UTC"))) is InformationAxis.TIME_INDEXED
    left = bar(1, key=k(1))
    right = bar(2, key=k(2))
    wall = pair_wall_clock_duration(left.availability_key, right.availability_key)
    assert wall.semantics == UNAVAILABLE
    assert wall.reason == "NOT_TIME_INDEXED"
    count = pair_bar_count_duration(left.availability_key, right.availability_key)
    assert count.value == 1
    timed_left = k(1, ts=pd.Timestamp("2026-05-01 00:00", tz="UTC"))
    timed_right = k(2, ts=pd.Timestamp("2026-05-01 01:00", tz="UTC"))
    wall = pair_wall_clock_duration(timed_left, timed_right)
    assert wall.semantics == EXACT
    assert wall.value == 3600.0


# 17 — DescriptorSpec registry: factual, policy-free, typed denominators
def test_muf_s1_price_path_17_descriptor_specs_policy_free():
    from trading_system.market_understanding.price_path import S1_DESCRIPTOR_SPECS

    assert len(S1_DESCRIPTOR_SPECS) == 7
    identities = set()
    for spec in S1_DESCRIPTOR_SPECS:
        assert spec.stage in DESCRIPTOR_STAGES
        assert spec.boundary_contract in BOUNDARY_CONTRACTS
        assert spec.policy_dependencies == ()
        assert isinstance(spec.denominator_semantics, (str, TypedState))
        identities.add(spec.descriptor_identity)
    assert len(identities) == 7
    with pytest.raises(SchemaViolation):
        DescriptorSpec(
            name="bad",
            version="V1",
            descriptor_identity="x",
            stage="RUNNING_ONLY",
            required_inputs=("CLOSE_PATH_STEP",),
            availability_rule="AT_ACCEPTED_OBSERVATION_KEY",
            boundary_contract="SINCE_GENESIS",
            missingness="NOT_APPLICABLE",
            denominator_semantics=TypedState.NOT_APPLICABLE,
            incremental_state="accumulator",
            policy_dependencies=("risk_policy",),
        )


# 18 — stream emits immutable published records (frozen content)
def test_muf_s1_price_path_18_stream_emits_immutable_records():
    st = stream()
    first = st.accept(bar(1))
    second = st.accept(bar(2))
    assert isinstance(first, AcceptedBarFacts)
    assert first.derivatives_record.record_type == "S1_BAR_FACT_DERIVATIVES"
    assert first.running_snapshot_record.record_type == "S1_RUNNING_EXTREME_SNAPSHOT"
    assert len(first.descriptor_records) == 7
    assert first.displacement_record is None
    assert second.displacement_record is not None
    content = second.derivatives_record.content
    with pytest.raises((ImmutabilityViolation, SchemaViolation, TypeError, AttributeError)):
        content["metrics"] = {}


# 19 — descriptor values: typed missingness without grid; exact accumulators
def test_muf_s1_price_path_19_descriptor_values_typed():
    st = stream()
    first = st.accept(bar(1, c=11.0))
    values = {rec.content["descriptor_name"]: rec.content["value"] for rec in first.descriptor_records}
    assert values["grid_contiguous_close_path_length"] is TypedState.NOT_CONFIGURED
    assert values["bar_count_grid"] is TypedState.NOT_CONFIGURED
    assert values["observed_close_path_length"] == 0.0
    assert values["bar_count_observed"] == 1
    second = st.accept(bar(2, h=13.0, c=12.5))
    values = {rec.content["descriptor_name"]: rec.content["value"] for rec in second.descriptor_records}
    assert values["observed_close_path_length"] == 1.5
    assert values["sum_close_displacement"] == 1.5


# 20 — future append invariance: first t records unchanged by later appends
def test_muf_s1_price_path_20_future_append_invariance():
    def ladder(pos):
        close = 10.0 + pos
        return bar(pos, o=close - 1.0, h=close + 1.0, low=close - 2.0, c=close)

    st1 = stream()
    prefix = [st1.accept(ladder(pos)) for pos in range(1, 4)]
    st2 = stream()
    full = [st2.accept(ladder(pos)) for pos in range(1, 6)]
    for left, right in zip(prefix, full):
        assert left.derivatives_record.record_identity == right.derivatives_record.record_identity
        assert left.derivatives_record.content == right.derivatives_record.content
        assert left.running_snapshot_record.content == right.running_snapshot_record.content
    assert len(prefix) == 3
    assert st2.accepted_count == 5
