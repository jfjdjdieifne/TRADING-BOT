"""MUF V1 S1 — path_schemas module gates (tests 1-20 + H1 A-G + RC1 + MUT A-O).

Fixture discipline: SYNTHETIC SMALL FIXTURES ONLY (no owner data). H1/RC1
sections pin the adjudicated design; MUT sections are the mutation-proof gates
(each must fail when its targeted fault is injected on an isolated copy).
"""
import inspect
import time

import pandas as pd
import pytest

from trading_system.research.information_time import (
    INFORMATION_KEY_VERSION,
    InformationKey,
    InformationKeyError,
    InformationPhase,
)
from trading_system.research.trajectory import trajectory_stage4c

from trading_system.market_understanding.availability import (
    IllegalCausalReference,
    InformationAxis,
    NonEarliestAvailability,
    InformationBatchKey,
    SourceBatchIdentity,
)
from trading_system.market_understanding.contracts import (
    ImmutabilityViolation,
    IncomparableInformationKeys,
    SchemaIdentity,
    SchemaViolation,
    TypedState,
)
from trading_system.market_understanding.records import EventKind, payload_canonical_view
from trading_system.market_understanding import path_schemas, price_path
from trading_system.market_understanding.price_path import (
    ADJACENCY_GRID_CONTIGUOUS,
    ADJACENCY_OBSERVATION_ADJACENT,
    AMBIGUOUS_INTRABAR_CHRONOLOGY,
    BOUND,
    DISCRETE_TV_TRIANGLE_INEQUALITY,
    EXACT,
    SAME_BATCH_ORDER_UNPROVEN,
    S1_DUPLICATE_OBSERVATION_KEY,
    S1_OUT_OF_ORDER_OBSERVATION,
    UNAVAILABLE,
    ZERO_DENOMINATOR,
    CausalObservationStream,
    DeclaredGrid,
    PublishedOhlcBarFact,
    intrabar_path_metrics,
    key_axis,
    pair_direction,
    pair_metrics,
    pair_wall_clock_duration,
    safe_ratio,
)
from trading_system.market_understanding.path_schemas import (
    COVERAGE_UNAVAILABLE,
    EXPECTED_GRID_KEY_NOT_OBSERVED,
    GRID_OBSERVATIONS_COMPLETE,
    OFF_GRID_OBSERVATIONS_PRESENT,
    S1_ABSENCE_REQUIRES_CLOSED_DOMAIN,
    S1_GRID_CONTIGUITY_UNPROVEN,
    S1_NOT_YET_OBSERVED,
    S1_SCHEMA_IDENTITY,
    S1_SCHEMA_VERSION_MISMATCH,
    S1_TYPED_STATE_UNAVAILABLE,
    STAGE_4C1_AUTHORITY_MODULE,
    ExactSlotCadence,
    ExpectedGridAbsenceWitness,
    StreamCheckpoint,
    absence_pair_tuple,
    bar_provenance,
    cadence_partition,
    capture_checkpoint,
    expected_grid_absence_record,
    normalize_descriptor_inputs,
    observed_grid_keys_record,
    observe_complete_bar_event,
    pair_path_schemas,
    require_s1_schema_version,
    s1_scheduled_slot_coverage,
    verify_checkpoint_continuity,
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


def stream(declared_grid=None):
    return CausalObservationStream(
        source_identity=SOURCE, dataset_identity=DATASET, declared_grid=declared_grid
    )


def witness(token=GRID_OBSERVATIONS_COMPLETE, coverage=COVERAGE_UNAVAILABLE, claim=False, origin=STAGE_4C1_AUTHORITY_MODULE):
    return ExpectedGridAbsenceWitness(
        token_identity=token,
        coverage_status=coverage,
        coverage_requires_expectations_met=claim,
        origin_module=origin,
        witnessed_at_key=k(9),
    )


def grid(*positions):
    return DeclaredGrid("MUF_S1_1d_GRID_V1", tuple(k(pos) for pos in positions))


# ===========================================================================
# Tests 1-20 — schema layer
# ===========================================================================


def test_muf_s1_path_schemas_01_schema_identity_and_version_gate():
    assert S1_SCHEMA_IDENTITY.schema_domain == "MUF_S1_PATH_SCHEMAS"
    require_s1_schema_version(S1_SCHEMA_IDENTITY)  # no raise
    with pytest.raises(SchemaViolation) as caught:
        require_s1_schema_version(SchemaIdentity("MUF_S1_PATH_SCHEMAS", "V2"))
    assert S1_SCHEMA_VERSION_MISMATCH in str(caught.value)


def test_muf_s1_path_schemas_02_canonical_observation_event():
    st = stream()
    facts = observe_complete_bar_event(st, bar(1))
    assert facts.derivatives_record.record_type == "S1_BAR_FACT_DERIVATIVES"
    assert st.accepted_count == 1
    with pytest.raises(SchemaViolation):
        observe_complete_bar_event(object(), bar(2))


def test_muf_s1_path_schemas_03_absence_witness_valid_tokens():
    w = witness()
    assert w.proves_complete_coverage
    assert w.token_identity is GRID_OBSERVATIONS_COMPLETE


def test_muf_s1_path_schemas_04_absence_witness_rejects_unknown_tokens():
    with pytest.raises(SchemaViolation):
        witness(token="SOME_OTHER_TOKEN")
    with pytest.raises(SchemaViolation):
        witness(coverage="SOME_OTHER_COVERAGE")


def test_muf_s1_path_schemas_05_absence_witness_requires_stage_authority():
    with pytest.raises(SchemaViolation):
        witness(origin="trading_system.market_understanding.records")


def test_muf_s1_path_schemas_06_witness_branch_semantics():
    proven = witness(
        token=OFF_GRID_OBSERVATIONS_PRESENT, coverage=COVERAGE_UNAVAILABLE, claim=True
    )
    assert proven.proves_complete_coverage
    unproven = witness(
        token=OFF_GRID_OBSERVATIONS_PRESENT, coverage=COVERAGE_UNAVAILABLE, claim=False
    )
    assert not unproven.proves_complete_coverage


def test_muf_s1_path_schemas_07_absence_pair_tuple_reuse():
    key = k(2)
    assert absence_pair_tuple(key) == (
        EXPECTED_GRID_KEY_NOT_OBSERVED,
        key,
        S1_TYPED_STATE_UNAVAILABLE,
    )


def test_muf_s1_path_schemas_08_absence_record_content():
    g = grid(1, 2)
    rec = expected_grid_absence_record(
        declared_grid=g, availability_key=k(2), grid_key=k(2), witness=witness()
    )
    content = rec.content
    assert content["missing_observation_reason"] == EXPECTED_GRID_KEY_NOT_OBSERVED
    assert content["typed_state"] is TypedState.UNAVAILABLE
    assert content["witness_origin_module"] == STAGE_4C1_AUTHORITY_MODULE
    assert "Stage 4C-1" in content["provenance"]


def test_muf_s1_path_schemas_09_absence_record_never_synthesizes_bars():
    g = grid(1, 2)
    rec = expected_grid_absence_record(
        declared_grid=g, availability_key=k(2), grid_key=k(2), witness=witness()
    )
    for name in ("open_price", "high_price", "low_price", "close_price"):
        assert name not in rec.content


def test_muf_s1_path_schemas_10_cadence_partition_happy_path():
    cadence = ExactSlotCadence("SLOT_TEST", (k(1), k(2), k(3)))
    result = cadence_partition((k(1), k(3)), cadence)
    assert [key.bar_position for key in result["at_expected_slot"]] == [1, 3]
    assert result["received_at_unexpected_slot"] == ()
    assert [key.bar_position for key in result["expected_not_observed"]] == [2]
    assert result["scheduled_slot_status_map"][k(2)] is TypedState.UNAVAILABLE


def test_muf_s1_path_schemas_11_cadence_duplicate_fail_closed():
    cadence = ExactSlotCadence("SLOT_TEST", (k(1), k(2)))
    with pytest.raises(SchemaViolation) as caught:
        cadence_partition((k(1), k(1)), cadence)
    assert S1_DUPLICATE_OBSERVATION_KEY in str(caught.value)


def test_muf_s1_path_schemas_12_cadence_out_of_order_fail_closed():
    cadence = ExactSlotCadence("SLOT_TEST", (k(1), k(2)))
    with pytest.raises(SchemaViolation) as caught:
        cadence_partition((k(2), k(1)), cadence)
    assert S1_OUT_OF_ORDER_OBSERVATION in str(caught.value)


def test_muf_s1_path_schemas_13_cadence_mixed_axes_fail_closed():
    cadence = ExactSlotCadence("SLOT_TEST", (k(1), k(2)))
    mixed = (k(1), k(2, ts=pd.Timestamp("2026-05-02 00:00", tz="UTC")))
    with pytest.raises(SchemaViolation) as caught:
        cadence_partition(mixed, cadence)
    assert S1_GRID_CONTIGUITY_UNPROVEN in str(caught.value)


def test_muf_s1_path_schemas_14_s1_missing_state_vocabulary():
    result = s1_scheduled_slot_coverage((k(1),), (k(1), k(2)))
    assert result[k(1)] == "OBSERVED"
    assert result[k(2)] == S1_NOT_YET_OBSERVED
    assert set(path_schemas.S1_MISSING_STATES) == {
        "S1_NOT_YET_OBSERVED",
        "EXPECTED_GRID_KEY_NOT_OBSERVED",
        "S1_ABSENCE_REQUIRES_CLOSED_DOMAIN",
    }


def test_muf_s1_path_schemas_15_normalize_inputs_zero_denominator_typed():
    spec = price_path.S1_DESCRIPTOR_SPECS[0]
    state = normalize_descriptor_inputs(spec, 3.5)
    assert state.semantics == EXACT
    assert state.value == 3.5
    zero = normalize_descriptor_inputs(spec, 3.5, denominator=0)
    assert zero.denominator_semantics is TypedState.UNDEFINED
    ok = normalize_descriptor_inputs(spec, 3.5, denominator=2)
    assert ok.denominator_semantics == EXACT


def test_muf_s1_path_schemas_16_normalize_inputs_typed_state_value():
    spec = price_path.S1_DESCRIPTOR_SPECS[0]
    state = normalize_descriptor_inputs(spec, TypedState.NOT_CONFIGURED)
    assert state.semantics == UNAVAILABLE
    assert state.value is TypedState.NOT_CONFIGURED
    with pytest.raises(SchemaViolation):
        normalize_descriptor_inputs(spec, "not-a-number")


def test_muf_s1_path_schemas_17_pair_schema_adjacency_kinds():
    g = grid(1, 2, 3, 4)
    contiguous = pair_path_schemas(
        bar(1), bar(2), source_identity=SOURCE, dataset_identity=DATASET, declared_grid=g
    )
    assert contiguous.adjacency_descriptor.content["recorded_kind"] == ADJACENCY_GRID_CONTIGUOUS
    assert contiguous.grid_contiguity_descriptor.content["recorded_kind"] == "GRID_CONTIGUOUS"
    non_grid = pair_path_schemas(
        bar(2), bar(4), source_identity=SOURCE, dataset_identity=DATASET, declared_grid=g
    )
    assert non_grid.adjacency_descriptor.content["recorded_kind"] == ADJACENCY_OBSERVATION_ADJACENT
    assert non_grid.grid_contiguity_descriptor.content["recorded_kind"] == "NOT_PROVEN"


def test_muf_s1_path_schemas_18_pair_records_formulas_and_bundle():
    recs = pair_path_schemas(
        bar(1, c=11.0), bar(2, h=13.0, c=12.5), source_identity=SOURCE, dataset_identity=DATASET
    )
    signed = recs.displacement_with_direction_record.content
    assert "close_displacement :=" in signed["formulas"]
    assert "SAME_BATCH_ORDER_UNPROVEN" in signed["formulas"]
    assert "chronology" in signed["chronology_caveat"]
    bundle = recs.metric_bundle_record.content["metrics"]
    assert set(bundle) == {
        "close_displacement",
        "close_path_step",
        "bar_range",
        "open_close_displacement",
        "upper_wick",
        "lower_wick",
        "bar_count",
        "bar_count_on_grid",
    }
    assert bundle["close_path_step"]["value"] == 1.5


def test_muf_s1_path_schemas_19_checkpoint_continuity():
    st = stream()
    st.accept(bar(1))
    st.accept(bar(2))
    checkpoint = capture_checkpoint(st)
    verify_checkpoint_continuity(st, checkpoint)  # prefix state
    st.accept(bar(3))
    verify_checkpoint_continuity(st, checkpoint)  # still a valid prefix
    bad = StreamCheckpoint(
        accepted_count=3,
        last_accepted_key=k(1),
        observed_close_path_length=0.0,
        grid_contiguous_close_path_length=0.0,
        running_high_so_far=12.0,
        running_low_so_far=8.0,
    )
    with pytest.raises(SchemaViolation):
        verify_checkpoint_continuity(st, bad)


def test_muf_s1_path_schemas_20_provenance_and_deterministic_identities():
    fact = bar(7)
    provenance = bar_provenance(fact)
    assert provenance["price_semantics"] == "PUBLISHED_OHLC_FACT"
    assert provenance["dataset_identity"] == DATASET
    assert provenance["published_bar_record_ref"] == "fixture-bar#7"
    left = pair_path_schemas(bar(1), bar(2), source_identity=SOURCE, dataset_identity=DATASET)
    right = pair_path_schemas(bar(1), bar(2), source_identity=SOURCE, dataset_identity=DATASET)
    assert (
        left.displacement_with_direction_record.record_identity
        == right.displacement_with_direction_record.record_identity
    )


# ===========================================================================
# H1 A-G — adjudicated design gates
# ===========================================================================


def test_muf_s1_h1a_staged_schema_price_is_bar_fact():
    fact = bar(1)
    assert fact.provenance["price_semantics"] == "PUBLISHED_OHLC_FACT"
    bundle = pair_path_schemas(
        bar(1), bar(2), source_identity=SOURCE, dataset_identity=DATASET
    ).metric_bundle_record.content["metrics"]
    for name in (
        "close_displacement",
        "close_path_step",
        "bar_range",
        "open_close_displacement",
        "upper_wick",
        "lower_wick",
        "bar_count",
        "bar_count_on_grid",
    ):
        assert name in bundle


def test_muf_s1_h1b_discrete_intrabar_lower_bound():
    metrics = intrabar_path_metrics(bar(1, o=10.0, h=12.0, low=8.0, c=11.0))
    lower = metrics["intrabar_path_length_lower_bound"]
    assert lower.semantics == BOUND
    assert lower.value == 7.0
    assert lower.bound_basis == DISCRETE_TV_TRIANGLE_INEQUALITY
    assert metrics["intrabar_path_length_exact"].reason == AMBIGUOUS_INTRABAR_CHRONOLOGY
    assert metrics["intrabar_path_length_upper_bound"].semantics == UNAVAILABLE


def test_muf_s1_h1c_batch_semantics_and_span_scaling():
    shared = batch(1, "2026-05-01|1d")
    same = pair_metrics(bar(1, c=11.0, info_batch=shared), bar(2, c=12.0, info_batch=shared))
    assert same["close_displacement"].value is TypedState.UNDEFINED
    assert same["close_displacement"].reason == SAME_BATCH_ORDER_UNPROVEN
    assert same["close_path_step"].value == 1.0
    left = bar(1, o=10.0, h=15.0, low=5.0, c=12.0, info_batch=batch(1, "2026-05-01|1d"))
    right = bar(2, o=12.0, h=16.0, low=6.0, c=15.0, info_batch=batch(2, "2026-05-02|1d"))
    cross = pair_metrics(left, right)
    assert cross["close_displacement"].semantics == EXACT
    assert cross["close_displacement"].value == 3.0
    lb = intrabar_path_metrics(left)["intrabar_path_length_lower_bound"]
    assert lb.value == 18.0  # (15-5) + min(12, 8)


def test_muf_s1_h1d_missingness_composed_with_stage_tokens():
    assert path_schemas.GRID_OBSERVATIONS_COMPLETE is trajectory_stage4c.GRID_OBSERVATIONS_COMPLETE
    assert path_schemas.COVERAGE_UNAVAILABLE is trajectory_stage4c.COVERAGE_UNAVAILABLE
    result = s1_scheduled_slot_coverage((), (k(1),))
    assert result[k(1)] == S1_NOT_YET_OBSERVED
    w = witness()
    assert w.proves_complete_coverage  # token-level composition only


def test_muf_s1_h1e_scaling_incremental_state_no_rescan():
    counter = {"calls": 0}
    original = price_path.pair_metrics

    def counted(left, right):
        counter["calls"] += 1
        return original(left, right)

    price_path.pair_metrics = counted
    try:
        st = stream()
        n = 300
        early = time.perf_counter()
        for pos in range(1, 31):
            st.accept(bar(pos, h=12.0, low=8.0))
        early = time.perf_counter() - early
        late = time.perf_counter()
        for pos in range(31, n + 1):
            st.accept(bar(pos, h=12.0, low=8.0))
        late = time.perf_counter() - late
    finally:
        price_path.pair_metrics = original
    assert counter["calls"] == n - 1  # exactly one fact computation per pair
    assert st.running_high_state.origins_unordered == frozenset(
        k(pos) for pos in range(1, n + 1)
    )  # tie set O(k) retained without truncation
    per_early = early / 30
    per_late = late / (n - 30)
    assert per_late < 20 * max(per_early, 1e-9)  # no history-rescan growth
    extra = bar(n + 1, o=12.0, h=14.0, low=11.0, c=13.0)
    for record in st.accept(extra).descriptor_records:
        for name in ("open_price", "high_price", "low_price", "close_price"):
            assert name not in record.content


def test_muf_s1_h1f_pair_records_separated_no_structural_language():
    g = grid(1, 2, 3)
    st = stream()
    first = [observe_complete_bar_event(st, bar(pos)) for pos in (1, 2)]
    recs = pair_path_schemas(
        bar(1), bar(2), source_identity=SOURCE, dataset_identity=DATASET, declared_grid=g
    )
    types = {
        recs.adjacency_descriptor.record_type,
        recs.grid_contiguity_descriptor.record_type,
        recs.metric_bundle_record.record_type,
        recs.displacement_with_direction_record.record_type,
    }
    assert len(types) == 4
    banned = ("episode", "turning", "wave", "segment", "narrative")

    def walk(value):
        if isinstance(value, str):
            for word in banned:
                assert word not in value.lower()
        elif isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, (tuple, list)):
            for item in value:
                walk(item)

    for rec in (recs.adjacency_descriptor, recs.grid_contiguity_descriptor,
                recs.metric_bundle_record, recs.displacement_with_direction_record):
        walk(rec.content)
    later = stream()
    full = [observe_complete_bar_event(later, bar(pos)) for pos in (1, 2, 3)]
    for early_rec, late_rec in zip(first, full):
        assert (
            early_rec.derivatives_record.record_identity
            == late_rec.derivatives_record.record_identity
        )


def test_muf_s1_h1g_exemplar_aggregation():
    closes = [10.0, 4.0, 8.0, 2.0, 4.0]  # 5 closes -> 4 steps: 6 + 4 + 6 + 2

    def span_bar(pos, previous_close, close):
        return bar(
            pos,
            o=previous_close,
            h=max(previous_close, close) + 1.0,
            low=min(previous_close, close) - 1.0,
            c=close,
            info_batch=batch(pos, f"batch#{pos}"),
        )

    g = grid(1, 2, 3, 4, 5)
    st = stream()
    for pos, close in enumerate(closes, start=1):
        previous_close = closes[pos - 1] if pos > 1 else close
        st.accept(span_bar(pos, previous_close, close))
    assert st.observed_close_path_length == 18.0  # 6 + 4 + 6 + 2
    assert st.accepted_count == 5
    pairs = []
    for pos in range(1, 5):
        left = span_bar(pos, closes[pos - 1], closes[pos - 1])
        right = span_bar(pos + 1, closes[pos - 1], closes[pos])
        pairs.append(
            pair_path_schemas(
                left, right, source_identity=SOURCE, dataset_identity=DATASET, declared_grid=g
            )
        )
    displacement_sum = sum(
        rec.displacement_with_direction_record.content["close_displacement"]["value"]
        for rec in pairs
    )
    assert displacement_sum == -6.0  # 4 - 10
    assert len(pairs) == 4


# ===========================================================================
# RC1 — absence authority corrections
# ===========================================================================


def test_muf_s1_rc1a1_absence_witness_over_reused_stage_tokens():
    assert path_schemas.GRID_OBSERVATIONS_COMPLETE is trajectory_stage4c.GRID_OBSERVATIONS_COMPLETE
    w = witness()
    fields = tuple(ExpectedGridAbsenceWitness.__dataclass_fields__.keys())
    assert fields == (
        "token_identity",
        "coverage_status",
        "coverage_requires_expectations_met",
        "origin_module",
        "witnessed_at_key",
    )  # no timestamp-set input exists: S1 never reimplements the comparison


def test_muf_s1_rc1a2_absence_is_typed_unavailable_with_reason():
    g = grid(1, 2)
    rec = expected_grid_absence_record(
        declared_grid=g, availability_key=k(2), grid_key=k(2), witness=witness()
    )
    assert rec.content["typed_state"] is TypedState.UNAVAILABLE
    assert rec.content["missing_observation_reason"] == "EXPECTED_GRID_KEY_NOT_OBSERVED"


def test_muf_s1_rc1a3_pair_tuple_reuse_exact():
    key = k(2)
    reason, paired_key, state = absence_pair_tuple(key)
    assert reason == "EXPECTED_GRID_KEY_NOT_OBSERVED"
    assert paired_key is key
    assert state is TypedState.UNAVAILABLE


def test_muf_s1_rc1b1_prefix_without_closed_authority_fails_closed():
    g = grid(1, 2)
    with pytest.raises(SchemaViolation) as caught:
        expected_grid_absence_record(
            declared_grid=g, availability_key=k(2), grid_key=k(2), witness=None
        )
    assert S1_ABSENCE_REQUIRES_CLOSED_DOMAIN in str(caught.value)
    unproven = witness(
        token=OFF_GRID_OBSERVATIONS_PRESENT, coverage=COVERAGE_UNAVAILABLE, claim=False
    )
    with pytest.raises(SchemaViolation) as caught:
        expected_grid_absence_record(
            declared_grid=g, availability_key=k(2), grid_key=k(2), witness=unproven
        )
    assert S1_ABSENCE_REQUIRES_CLOSED_DOMAIN in str(caught.value)


def test_muf_s1_rc1b2_witnessed_complete_emits_absence_line_d1():
    g = grid(1, 2, 3)
    rec = expected_grid_absence_record(
        declared_grid=g, availability_key=k(3), grid_key=k(2), witness=witness()
    )
    assert rec.content["missing_observation_reason"] == EXPECTED_GRID_KEY_NOT_OBSERVED
    assert rec.content["witness_token_identity"] == GRID_OBSERVATIONS_COMPLETE


def test_muf_s1_rc1b3_d2_identity_never_merged():
    left = k(5, ts=pd.Timestamp("2026-05-01 00:00", tz="UTC"))
    right = k(5, ts=pd.Timestamp("2026-05-02 00:00", tz="UTC"))
    assert left != right  # distinct identity at one causal coordinate
    with pytest.raises(InformationKeyError):
        ExactSlotCadence("SLOT_TEST", (left, right))  # conflicting provenance fails closed
    g = grid(1, 2)
    rec = expected_grid_absence_record(
        declared_grid=g, availability_key=k(2), grid_key=k(2), witness=witness()
    )
    assert rec.content["grid_key"] != k(3) or True  # identity preserved per key
    assert rec.content["grid_key"] == k(2)


# ===========================================================================
# MUT gates A-O — mutation-proof targets
# ===========================================================================


def test_muf_s1_mut_a_intrabar_lb_min_branch():
    metrics = intrabar_path_metrics(bar(1, o=10.0, h=15.0, low=5.0, c=12.0))
    assert metrics["intrabar_path_length_lower_bound"].value == 18.0


def test_muf_s1_mut_b_same_batch_signed_undefined():
    shared = batch(1, "same")
    result = pair_metrics(bar(1, c=11.0, info_batch=shared), bar(2, c=12.0, info_batch=shared))
    assert result["close_displacement"].value is TypedState.UNDEFINED
    assert result["close_displacement"].reason == SAME_BATCH_ORDER_UNPROVEN


def test_muf_s1_mut_c_out_of_order_rejected():
    st = stream()
    st.accept(bar(2))
    with pytest.raises(SchemaViolation) as caught:
        st.accept(bar(1))
    assert S1_OUT_OF_ORDER_OBSERVATION in str(caught.value)


def test_muf_s1_mut_d_duplicate_rejected():
    st = stream()
    st.accept(bar(1))
    with pytest.raises(SchemaViolation) as caught:
        st.accept(bar(1))
    assert S1_DUPLICATE_OBSERVATION_KEY in str(caught.value)


def test_muf_s1_mut_e_tie_origins_no_winner():
    st = stream()
    for pos in range(1, 6):
        st.accept(bar(pos, h=12.0, low=8.0))
    high = st.running_high_state
    assert high.origins_unordered == frozenset(k(pos) for pos in range(1, 6))
    assert high.value == 12.0


def test_muf_s1_mut_f_ohlc_legality_enforced():
    with pytest.raises(SchemaViolation):
        bar(1, o=10.0, h=9.5, low=8.0, c=11.0)


def test_muf_s1_mut_g_zero_denominator_typed_not_numeric():
    assert safe_ratio(1, 0) is TypedState.UNDEFINED
    assert not isinstance(safe_ratio(1, 0), float)


def test_muf_s1_mut_h_axis_never_invents_timestamps():
    positional = k(1)
    assert positional.event_time_utc is None
    assert key_axis(positional) is InformationAxis.POSITIONAL
    timed = k(2, ts=pd.Timestamp("2026-05-01 00:00", tz="UTC"))
    assert key_axis(timed) is InformationAxis.TIME_INDEXED


def test_muf_s1_mut_i_absence_requires_witness():
    g = grid(1, 2)
    with pytest.raises(SchemaViolation) as caught:
        expected_grid_absence_record(
            declared_grid=g, availability_key=k(2), grid_key=k(2), witness=None
        )
    assert S1_ABSENCE_REQUIRES_CLOSED_DOMAIN in str(caught.value)


def test_muf_s1_mut_j_no_history_rescan_and_tie_memory():
    counter = {"calls": 0}
    original = price_path.pair_metrics

    def counted(left, right):
        counter["calls"] += 1
        return original(left, right)

    price_path.pair_metrics = counted
    try:
        st = stream()
        for pos in range(1, 51):
            st.accept(bar(pos, h=12.0, low=8.0))
    finally:
        price_path.pair_metrics = original
    assert counter["calls"] == 49
    assert len(st.running_high_state.origins_unordered) == 50  # O(k), no truncation


def test_muf_s1_mut_k_grid_contiguity_only_via_declared_grid():
    g = grid(1, 2, 3, 4)
    assert pair_path_schemas(
        bar(1), bar(2), source_identity=SOURCE, dataset_identity=DATASET, declared_grid=g
    ).adjacency_descriptor.content["recorded_kind"] == ADJACENCY_GRID_CONTIGUOUS
    assert pair_path_schemas(
        bar(2), bar(4), source_identity=SOURCE, dataset_identity=DATASET, declared_grid=g
    ).adjacency_descriptor.content["recorded_kind"] == ADJACENCY_OBSERVATION_ADJACENT


def test_muf_s1_mut_l_wall_clock_requires_time_indexed():
    wall = pair_wall_clock_duration(k(1), k(2))
    assert wall.semantics == UNAVAILABLE
    assert wall.reason == "NOT_TIME_INDEXED"


def test_muf_s1_mut_m_no_structural_vocabulary_definitions():
    banned = (
        "swing", "turning", "zigzag", "pivot", "hierarch", "qualif",
        "narrative", "repaint", "real_wave", "fake_wave", "market_model",
    )
    for module in (price_path, path_schemas):
        for name, obj in vars(module).items():
            if callable(obj) or isinstance(obj, type):
                lowered = name.lower()
                for word in banned:
                    assert word not in lowered, (module.__name__, name)


def test_muf_s1_mut_n_grid_path_length_excludes_off_grid_steps():
    g = grid(1, 2, 3)
    st = stream(declared_grid=g)
    st.accept(bar(1, c=10.0))
    st.accept(bar(3, h=14.0, c=13.0))  # pair (1,3): not consecutive on the declared grid
    st.accept(bar(4, h=15.0, c=14.0))  # pair (3,4): 4 is off-grid entirely
    assert st.observed_close_path_length == 4.0
    assert st.grid_contiguous_close_path_length == 0.0
    st2 = stream(declared_grid=grid(1, 2, 3))
    st2.accept(bar(1, c=10.0))
    st2.accept(bar(2, h=14.0, c=13.0))  # grid-contiguous step of 3.0
    st2.accept(bar(3, h=15.0, c=14.0))  # grid-contiguous step of 1.0
    assert st2.grid_contiguous_close_path_length == 4.0
    assert st2.observed_close_path_length == 4.0


def test_muf_s1_mut_o_direction_flat_at_zero_delta():
    assert pair_direction(bar(1, c=11.0), bar(2, c=11.0)) == "FLAT"


# ===========================================================================
# PATCH P1 — MANDATORY SCHEMA-FOUNDATION TESTS (1-12) + LB GATE (13)
# ===========================================================================


def _anchor_episode(**overrides):
    fields = dict(
        schema_identity=path_schemas.S1_SCHEMA_IDENTITY,
        timeline_id=TIMELINE,
        axis=InformationAxis.POSITIONAL,
        anchor_information_key=k(1),
        anchor_rule_version="MUF_ANCHOR_RULE_V1",
        anchor_fact_ref="anchor-fact#1",
        provenance={"source_identity": SOURCE.as_payload(), "dataset_identity": DATASET},
        availability_information_key=k(1),
    )
    fields.update(overrides)
    return path_schemas.CausalEpisodeRecord.create(**fields)


def _membership(episode_id, ref, member_key, membership_key):
    return path_schemas.EpisodeMembershipEvent.create(
        schema_identity=path_schemas.S1_SCHEMA_IDENTITY,
        episode_id=episode_id,
        member_fact_ref=ref,
        member_fact_availability_key=member_key,
        membership_information_key=membership_key,
        provenance={"dataset_identity": DATASET},
    )


def test_muf_s1_patch_p1_01_episode_record_legal_anchor_passes():
    for name in (
        "CausalEpisodeRecord",
        "EpisodeMembershipEvent",
        "MarketStateTransitionRecord",
        "ExplanationRecord",
    ):
        assert hasattr(path_schemas, name)  # the four schema foundations exist
    episode = _anchor_episode()
    assert episode.episode_identity
    assert episode.anchor_rule_version == "MUF_ANCHOR_RULE_V1"
    record = episode.as_record()
    assert record.record_type == path_schemas.CAUSAL_EPISODE_RECORD_TYPE
    assert record.record_identity == episode.episode_identity


def test_muf_s1_patch_p1_02_membership_refs_rejected():
    with pytest.raises(SchemaViolation) as caught:
        path_schemas.CausalEpisodeRecord.create(
            schema_identity=path_schemas.S1_SCHEMA_IDENTITY,
            timeline_id=TIMELINE,
            axis=InformationAxis.POSITIONAL,
            anchor_information_key=k(1),
            anchor_rule_version="MUF_ANCHOR_RULE_V1",
            anchor_fact_ref="anchor-fact#1",
            provenance={"dataset_identity": DATASET},
            availability_information_key=k(1),
            membership_refs=(),
        )
    assert "membership_refs" in str(caught.value)
    episode = _anchor_episode()
    assert "membership_refs" not in episode.as_record().content


def test_muf_s1_patch_p1_03_membership_never_changes_episode_id():
    episode = _anchor_episode()
    before = episode.episode_identity
    first = _membership(before, "member-A", k(2), k(2))
    second = _membership(before, "member-B", k(3), k(3))
    assert episode.episode_identity == before
    assert first.episode_id == second.episode_id == before
    assert first.event_identity != second.event_identity
    assert first.as_event_record().event_kind is EventKind.MEMBERSHIP_EVENT


def test_muf_s1_patch_p1_04_future_membership_cannot_change_history():
    episode = _anchor_episode()
    record_before = episode.as_record()
    identity_before = record_before.record_identity
    view_before = payload_canonical_view(record_before.content)
    _membership(episode.episode_identity, "member-A", k(2), k(2))
    _membership(episode.episode_identity, "member-B", k(3), k(3))
    record_after = episode.as_record()
    assert record_after.record_identity == identity_before
    assert payload_canonical_view(record_after.content) == view_before


def test_muf_s1_patch_p1_05_membership_key_earlier_than_fact_rejected():
    episode = _anchor_episode()
    with pytest.raises(IllegalCausalReference):
        _membership(episode.episode_identity, "member-A", k(5), k(1))  # k(1) < k(5)


def test_muf_s1_patch_p1_06_literal_factual_transition_passes():
    transition = path_schemas.MarketStateTransitionRecord.create(
        schema_identity=path_schemas.S1_SCHEMA_IDENTITY,
        timeline_id=TIMELINE,
        from_state="OBSERVED_CLOSE_DISPLACEMENT_UP",
        to_state="OBSERVED_CLOSE_DISPLACEMENT_DOWN",
        state_kind=path_schemas.STATE_KIND_LITERAL_FACTUAL,
        policy_artifact_ref=path_schemas.POLICY_ARTIFACT_NOT_CONFIGURED,
        availability_information_key=k(2),
        provenance={"dataset_identity": DATASET},
    )
    record = transition.as_record()
    assert record.record_type == path_schemas.MARKET_STATE_TRANSITION_RECORD_TYPE
    delta = path_schemas.MarketStateTransitionRecord.create(
        schema_identity=path_schemas.S1_SCHEMA_IDENTITY,
        timeline_id=TIMELINE,
        from_state="RUNNING_HIGH_SO_FAR",
        to_state="RUNNING_HIGH_SO_FAR",
        state_kind=path_schemas.STATE_KIND_DESCRIPTOR_DELTA,
        descriptor_deltas={"running_high_so_far": 2.5},
        policy_artifact_ref=path_schemas.POLICY_ARTIFACT_NOT_CONFIGURED,
        availability_information_key=k(3),
        provenance={"dataset_identity": DATASET},
    )
    assert delta.as_record().content["descriptor_deltas"]["running_high_so_far"] == 2.5


def test_muf_s1_patch_p1_07_threshold_regime_without_policy_rejected():
    base = dict(
        schema_identity=path_schemas.S1_SCHEMA_IDENTITY,
        timeline_id=TIMELINE,
        from_state="STATE_BEFORE",
        to_state="STATE_AFTER",
        state_kind=path_schemas.STATE_KIND_LITERAL_FACTUAL,
        policy_artifact_ref=path_schemas.POLICY_ARTIFACT_NOT_CONFIGURED,
        availability_information_key=k(2),
        provenance={"dataset_identity": DATASET},
    )
    with pytest.raises(SchemaViolation):
        path_schemas.MarketStateTransitionRecord.create(**base, threshold=0.5)
    with pytest.raises(SchemaViolation):
        path_schemas.MarketStateTransitionRecord.create(**base, regime="risk_on")
    with pytest.raises(SchemaViolation) as caught:
        path_schemas.MarketStateTransitionRecord.create(
            **{**base, "state_kind": "THRESHOLD_REGIME"}
        )
    assert "NOT_CONFIGURED" in str(caught.value)
    with pytest.raises(SchemaViolation):
        path_schemas.MarketStateTransitionRecord.create(
            **{**base, "from_state": "RISK_THRESHOLD_STATE"}
        )
    with pytest.raises(SchemaViolation) as caught:
        path_schemas.MarketStateTransitionRecord.create(
            **{**base, "policy_artifact_ref": "policy-v1"}
        )
    assert "PolicyArtifact" in str(caught.value)


def test_muf_s1_patch_p1_08_explanation_four_legal_states_pass():
    for state in (
        "MONITORING",
        "PATTERN_REQUIREMENTS_SATISFIED",
        "CONTRADICTED",
        "SUPERSEDED",
    ):
        explanation = path_schemas.ExplanationRecord.create(
            schema_identity=path_schemas.S1_SCHEMA_IDENTITY,
            timeline_id=TIMELINE,
            state=state,
            fact_refs=("fixture-bar#1",),
            availability_information_key=k(2),
            provenance={"dataset_identity": DATASET},
        )
        record = explanation.as_record()
        assert record.record_type == path_schemas.EXPLANATION_RECORD_TYPE
        assert record.content["state"] == state


def test_muf_s1_patch_p1_09_forbidden_explanation_states_rejected():
    for state in ("PROBABLE", "LIKELY", "SUPPORTED", "WINNING_EXPLANATION"):
        with pytest.raises(SchemaViolation):
            path_schemas.ExplanationRecord.create(
                schema_identity=path_schemas.S1_SCHEMA_IDENTITY,
                timeline_id=TIMELINE,
                state=state,
                fact_refs=("fixture-bar#1",),
                availability_information_key=k(2),
                provenance={"dataset_identity": DATASET},
            )


def test_muf_s1_patch_p1_10_probability_weight_score_fields_rejected():
    base = dict(
        schema_identity=path_schemas.S1_SCHEMA_IDENTITY,
        timeline_id=TIMELINE,
        state="MONITORING",
        fact_refs=("fixture-bar#1",),
        availability_information_key=k(2),
        provenance={"dataset_identity": DATASET},
    )
    for name in ("probability", "weight", "score"):
        with pytest.raises(SchemaViolation) as caught:
            path_schemas.ExplanationRecord.create(**base, **{name: 0.5})
        assert name in str(caught.value)


def test_muf_s1_patch_p1_11_payload_mutation_impossible():
    episode = _anchor_episode()
    record = episode.as_record()
    with pytest.raises((ImmutabilityViolation, TypeError, AttributeError)):
        record.content["anchor_fact_ref"] = "mutated"
    event = _membership(episode.episode_identity, "member-A", k(2), k(2)).as_event_record()
    with pytest.raises((ImmutabilityViolation, TypeError, AttributeError)):
        event.event_payload["member_fact_ref"] = "mutated"
    with pytest.raises((ImmutabilityViolation, AttributeError, TypeError)):
        episode.episode_identity = "mutated"
    with pytest.raises((ImmutabilityViolation, AttributeError, TypeError)):
        event.event_kind = None


def test_muf_s1_patch_p1_12_ast_no_population_engine():
    import ast as _ast

    banned_stems = ("populate", "engine", "discover", "detect", "infer", "generate")
    for module in (price_path, path_schemas):
        tree = _ast.parse(open(module.__file__).read())
        for node in _ast.walk(tree):
            if isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef, _ast.ClassDef)):
                lowered = node.name.lower()
                for stem in banned_stems:
                    assert stem not in lowered, (module.__name__, node.name)


def test_muf_s1_patch_p1_13_lb_consistency_gate_actuals():
    metrics = intrabar_path_metrics(bar(1, o=10.0, h=12.0, low=8.0, c=11.0))
    assert metrics["intrabar_path_length_lower_bound"].value == 7.0
    metrics = intrabar_path_metrics(bar(1, o=10.0, h=15.0, low=5.0, c=12.0))
    assert metrics["intrabar_path_length_lower_bound"].value == 18.0


# ===========================================================================
# PATCH P2 — MANDATORY TESTS (1-8): membership earliest-lawful availability
# ===========================================================================


def test_muf_s1_patch_p2_01_equal_keys_accepted():
    episode = _anchor_episode()
    member = _membership(episode.episode_identity, "member-A", k(5), k(5))
    assert member.membership_information_key == member.member_fact_availability_key
    record = member.as_event_record()
    assert record.event_kind is EventKind.MEMBERSHIP_EVENT


def test_muf_s1_patch_p2_02_delayed_membership_rejected_non_earliest():
    # exact auditor fixture: same timeline, member_fact bar_position=5,
    # membership bar_position=10 -> T+k must be rejected machine-distinguishably
    episode = _anchor_episode()
    with pytest.raises(NonEarliestAvailability) as caught:
        _membership(episode.episode_identity, "member-A", k(5), k(10))
    assert path_schemas.NON_EARLIEST_AVAILABILITY in str(caught.value)
    assert isinstance(caught.value, NonEarliestAvailability)  # S0 contract class


def test_muf_s1_patch_p2_03_premature_membership_rejected():
    episode = _anchor_episode()
    with pytest.raises(IllegalCausalReference):
        _membership(episode.episode_identity, "member-A", k(5), k(3))  # T-k premature


def test_muf_s1_patch_p2_04_cross_timeline_rejected():
    episode = _anchor_episode()
    with pytest.raises(IllegalCausalReference):
        _membership(
            episode.episode_identity,
            "member-A",
            k(5),
            k(5, timeline="OTHER|1d"),
        )


def test_muf_s1_patch_p2_05_incomparable_timestamp_provenance_fails_closed():
    episode = _anchor_episode()
    left = k(5, ts=pd.Timestamp("2026-05-01 00:00", tz="UTC"))
    right = k(5, ts=pd.Timestamp("2026-05-02 00:00", tz="UTC"))
    with pytest.raises(IncomparableInformationKeys):
        _membership(episode.episode_identity, "member-A", left, right)


def test_muf_s1_patch_p2_06_two_members_distinct_events_same_episode():
    episode = _anchor_episode()
    first = _membership(episode.episode_identity, "member-A", k(2), k(2))
    second = _membership(episode.episode_identity, "member-B", k(3), k(3))
    assert first.episode_id == second.episode_id == episode.episode_identity
    assert first.event_identity != second.event_identity
    # deterministic identity: same member fact + same episode + same key -> same event
    again = _membership(episode.episode_identity, "member-A", k(2), k(2))
    assert again.event_identity == first.event_identity


def test_muf_s1_patch_p2_07_future_member_never_alters_episode():
    episode = _anchor_episode()
    record_before = episode.as_record()
    identity_before = record_before.record_identity
    view_before = payload_canonical_view(record_before.content)
    _membership(episode.episode_identity, "member-A", k(2), k(2))
    _membership(episode.episode_identity, "member-B", k(3), k(3))
    record_after = episode.as_record()
    assert record_after.record_identity == identity_before
    assert payload_canonical_view(record_after.content) == view_before


def test_muf_s1_patch_p2_08_mutation_proof_revert_to_visibility_only(monkeypatch):
    episode = _anchor_episode()
    # baseline: enforcement active -> auditor fixture rejected (test #2 semantics)
    with pytest.raises(NonEarliestAvailability):
        _membership(episode.episode_identity, "member-A", k(5), k(10))
    # mutation: remove equality/earliest enforcement (revert to require_visible_at-only)
    monkeypatch.setattr(
        path_schemas,
        "_require_earliest_lawful_membership_key",
        lambda member_fact_availability_key, membership_information_key: None,
    )
    mutated = _membership(episode.episode_identity, "member-A", k(5), k(10))
    # with enforcement removed the T+k fixture is ACCEPTED => test #2 must fail
    assert mutated.membership_information_key == k(10)
