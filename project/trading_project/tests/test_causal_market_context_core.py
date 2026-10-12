from __future__ import annotations

import json

import pandas as pd
import pytest

from trading_system.research.information_time import InformationPhase
from trading_system.research.trajectory.causal_market_context_core import (
    CausalMarketContextCoreError,
    InterpretationPolicyReference,
    InterpretationRevisionLedger,
    MemorySink,
    ReplayLimits,
    TaskEvaluationAuthority,
    build_causal_market_context_core,
    entity_state_as_of_from_directory,
    evaluate_explicit_task_outcome,
    replay_causal_market_context,
)
from trading_system.research.trajectory.trajectory_query_views import (
    CoverageContract,
    HorizonPolicyIdentity,
    HorizonRequest,
)
from trading_system.sources import SourceArtifactIdentity
from trading_system.sources.binance_spot_minute_facts_source import (
    MinuteFactsProvenance,
    MinuteFactsSource,
)


def _source() -> SourceArtifactIdentity:
    return SourceArtifactIdentity(
        symbol="BTCUSDT",
        market_type="SPOT",
        interval="1m",
        period_start_utc="2026-05-01T00:00:00Z",
        period_end_utc="2026-05-01T01:00:00Z",
    )


def _market(rows: int = 6) -> pd.DataFrame:
    # Synthetic software fixture only; it is not market evidence or a policy prior.
    index = pd.date_range("2026-05-01T00:01:00Z", periods=6, freq="min")[:rows]
    frame = pd.DataFrame(
        {
            "open": [100, 102, 104, 106, 107, 103][:rows],
            "high": [102, 103, 106, 108, 109, 105][:rows],
            "low": [99, 101, 103, 102.5, 101, 100][:rows],
            "close": [101, 102.5, 105, 107, 102, 101][:rows],
            "volume": [100, 120, 110, 90, 95, 80][:rows],
        },
        index=index,
    )
    return frame


def _bundle(frame: pd.DataFrame | None = None):
    return build_causal_market_context_core(
        market_history=_market() if frame is None else frame,
        source_identity=_source(),
        timeline_id="synthetic-causal-context-test",
    )


def _flow_source(frame: pd.DataFrame) -> MinuteFactsSource:
    identity = _source()
    exact = pd.DataFrame(
        {
            "base_volume": ["10.00000000"] * len(frame),
            "buy_initiated_base_volume": ["6.00000000"] * len(frame),
            "sell_initiated_base_volume": ["4.00000000"] * len(frame),
        },
        index=frame.index,
    )
    provenance = MinuteFactsProvenance(
        identity=identity,
        schema_contract="SYNTHETIC_SOFTWARE_TEST_ONLY",
        raw_source_sha256="a" * 64,
        converter_sha256="b" * 64,
        converter_name="synthetic-test-fixture",
        converter_version="test-only",
        minute_facts_sha256="c" * 64,
        sidecar_sha256="d" * 64,
        sidecar_generated_at_utc="2026-05-01T00:00:00Z",
        timestamp_unit="MICROSECONDS",
        numeric_representation="FIXED_DECIMAL_STRINGS_TEST_ONLY",
        source_rows_total=len(frame),
        legal_rows_consumed=len(frame),
        official_invalid_sentinel_count=0,
        tie_timestamp_count=0,
        ambiguous_open_minute_count=0,
        ambiguous_close_minute_count=0,
        TIE_ORDER_CONTRACT="NOT_PROVEN",
        reconciliation={},
        historical_provenance_statement="synthetic software-test fixture; not owner data",
    )
    return MinuteFactsSource(identity, provenance, exact, exact, (), False)


def _key(bundle, position: int):
    return bundle.adapter.key_for_position(
        bundle.market.index,
        position,
        InformationPhase.COMPLETED_ROW_AVAILABLE,
        0,
    )


def test_integrated_replay_registers_fvg_lifecycle_and_fail_closed_domains():
    bundle = _bundle()
    result = replay_causal_market_context(bundle)

    assert len(result.boundaries) == len(bundle.market) == 6
    assert len(result.entities) == len(bundle.fvg.normalized_entity_frame) == 1
    assert len(result.events) == len(bundle.fvg.normalized_event_frame) == 5
    assert len(result.interpretations) == 6
    assert all(row.status == "INTERPRETATION_NOT_ESTABLISHED" for row in result.interpretations)
    assert bundle.structures == ()
    assert result.run_provenance["candidate_universe_complete"] is True
    assert result.summary.candidates_by_domain_representation == {
        "FVG:REP-STRUCTURE-INDEPENDENT-FVG": 1
    }
    coverage = {item["domain"]: item["state"] for item in result.domain_coverage}
    assert coverage["STAGE4B1_AND_DEPENDENT_STAGE4B2"] == "UNAVAILABLE_NO_EXPLICIT_SWING_POLICY"
    assert coverage["STAGE4B1_STRUCTURE"] == "UNAVAILABLE_NO_EXPLICIT_SWING_POLICY"
    assert coverage["STAGE4B2_LIQUIDITY"] == "UNAVAILABLE_NO_EXPLICIT_SWING_POLICY"
    assert coverage["STAGE4B2_ORDER_BLOCK"] == "UNAVAILABLE_NO_EXPLICIT_SWING_POLICY"
    assert coverage["STAGE4B2_DEALING_RANGE"] == "UNAVAILABLE_NO_EXPLICIT_SWING_POLICY"
    assert coverage["ACTUAL_EXECUTED_INITIATED_FLOW"] == "UNAVAILABLE_NOT_SUPPLIED"
    assert coverage["STAGE4C_HTF_STRUCTURE"] == "UNAVAILABLE_NO_HTF_STRUCTURE_CONTRACT"
    assert result.boundaries[0]["content"]["prefix_chain_current"]
    assert all(
        current["content"]["prefix_chain_previous"]
        == previous["content"]["prefix_chain_current"]
        for previous, current in zip(result.boundaries, result.boundaries[1:])
    )
    assert result.boundaries[-1]["content"]["prefix_chain_current"] == result.summary.prefix_chain_sha256


def test_completed_h1_observation_enters_context_only_at_its_asof_boundary():
    index = pd.date_range("2026-05-01T00:01:00Z", periods=61, freq="min")
    close = [100.0 + position * 0.01 for position in range(len(index))]
    frame = pd.DataFrame(
        {
            "open": close,
            "high": [value + 0.1 for value in close],
            "low": [value - 0.1 for value in close],
            "close": close,
            "volume": [1.0] * len(index),
        },
        index=index,
    )
    identity = SourceArtifactIdentity(
        "BTCUSDT", "SPOT", "1m", "2026-05-01T00:00:00Z", "2026-05-01T03:00:00Z"
    )
    bundle = build_causal_market_context_core(
        market_history=frame,
        source_identity=identity,
        timeline_id="synthetic-completed-h1-test",
    )
    result = replay_causal_market_context(bundle)
    end_column = "H1__completed_bucket_end_utc"
    h1_coverage = next(item for item in result.domain_coverage if item["domain"] == "STAGE4C_H1_RAW")
    assert h1_coverage["completed_bucket_count"] == 1
    assert pd.isna(bundle.htf.asof_bar_frame.iloc[58][end_column])
    assert bundle.htf.asof_bar_frame.iloc[59][end_column] == index[59]
    first_visible = result.boundaries[59]["content"]["facts"]["stage4c_h1_raw_asof"]["values"][end_column]
    assert first_visible == index[59].isoformat().replace("+00:00", "Z")
    prior = result.boundaries[58]["content"]["facts"]["stage4c_h1_raw_asof"]["values"][end_column]
    assert prior is None


def test_actual_executed_flow_is_integrated_with_source_labels_not_as_proxy():
    frame = _market()
    bundle = build_causal_market_context_core(
        market_history=frame,
        source_identity=_source(),
        timeline_id="synthetic-actual-flow-test",
        minute_facts_source=_flow_source(frame),
    )
    result = replay_causal_market_context(bundle)

    assert bundle.actual_flow is not None
    assert bundle.actual_absorption is not None
    assert bundle.executed_source.semantic_label == "EXECUTED_INITIATED_FLOW_FROM_BINANCE_SPOT"
    assert bundle.executed_source.volume_unit == "BASE_ASSET"
    for boundary in result.boundaries:
        flow = boundary["content"]["facts"]["actual_executed_flow"]
        assert flow["state"] == "AVAILABLE_AT_EXACT_SOURCE_TIMESTAMP"
        assert flow["mode"] == "ACTUAL_AGGRESSOR"
        assert flow["semantic_label"] == "EXECUTED_INITIATED_FLOW_FROM_BINANCE_SPOT"
        assert flow["tie_order_contract"] == "NOT_PROVEN"
        assert flow["intrabar_order_claimed"] is False
    coverage = {item["domain"]: item["state"] for item in result.domain_coverage}
    assert coverage["ACTUAL_EXECUTED_INITIATED_FLOW"] == "AVAILABLE"
    assert coverage["ACTUAL_AGGRESSOR_ABSORPTION"] == "AVAILABLE_ACTUAL_AGGRESSOR_BAR_RESPONSE; INTRABAR_ORDER_UNPROVEN"


def test_asof_state_retrieval_never_exposes_future_entity_or_lifecycle_events():
    bundle = _bundle()
    result = replay_causal_market_context(bundle)
    entity = result.entities[0]
    before_creation = _key(bundle, 1)
    with pytest.raises(CausalMarketContextCoreError, match="not visible"):
        result.entity_state_as_of(entity.entity_id, before_creation)

    creation = _key(bundle, 2)
    at_creation = result.entity_state_as_of(entity.entity_id, creation)
    assert at_creation.state == "PRODUCER_EVENT_FACT_SET_AVAILABLE"
    assert at_creation.revision is not None
    assert at_creation.revision.event_types_at_key == ("FVG_CREATED",)

    same_batch = result.entity_state_as_of(entity.entity_id, _key(bundle, 4))
    assert same_batch.revision is not None
    assert same_batch.revision.same_batch_order_unknown is True
    assert same_batch.revision.event_types_at_key == (
        "FIRST_FAR_SIDE_WICK_BREACH",
        "FIRST_FULL_RANGE_COVERAGE",
    )
    assert same_batch.revision.record.content["projection_semantics"] == "SET_OF_PRODUCER_FACTS_NO_WITHIN_BATCH_ORDER"


def test_same_prefix_has_identical_historical_boundary_records_when_future_rows_are_added():
    full_bundle = _bundle()
    prefix_bundle = _bundle(_market(4))
    full = replay_causal_market_context(full_bundle)
    prefix = replay_causal_market_context(prefix_bundle)

    assert full.boundaries[:4] == prefix.boundaries
    assert (
        full.boundaries[3]["content"]["prefix_chain_current"]
        == prefix.summary.prefix_chain_sha256
    )
    assert full.summary.prefix_chain_sha256 != prefix.summary.prefix_chain_sha256


def test_verified_overlap_relationships_are_geometric_only_and_candidate_search_is_bounded():
    bundle = _bundle()
    complete = replay_causal_market_context(bundle)
    overlaps = [
        item
        for item in complete.relationships
        if item.relation_type == "PRICE_BAR_RANGE_OVERLAPS_PREVIOUSLY_AVAILABLE_ENTITY_GEOMETRY"
    ]
    assert overlaps
    for relation in overlaps:
        assert relation.same_batch is False
        assert relation.facts["entity_available_position"] < relation.facts["later_observed_bar_position"]
        intersection = relation.facts["intersection"]
        assert intersection["low"] <= intersection["high"]
        assert "NO_INTRABAR_TOUCH_ORDER" in relation.facts["claim"]

    limited = replay_causal_market_context(
        _bundle(),
        limits=ReplayLimits(max_interval_nodes_per_query=0),
    )
    assert limited.summary.entity_count == complete.summary.entity_count
    assert limited.summary.relationship_coverage_state == "PARTIAL_QUERY_OR_BOUNDARY_LIMIT"
    assert any(
        row["relationship_search_state"] == "PARTIAL_QUERY_OR_BOUNDARY_LIMIT"
        for row in limited.relationship_coverage_rows
    )
    # The candidate universe stays complete even when spatial exploration is budgeted.
    assert limited.run_provenance["candidate_universe_complete"] is True


def test_memory_mode_fails_closed_above_cap_without_dropping_rows(tmp_path):
    bundle = _bundle()
    with pytest.raises(CausalMarketContextCoreError, match="use an external output_dir"):
        replay_causal_market_context(bundle, limits=ReplayLimits(max_memory_mode_bars=5))

    output = tmp_path / "bounded-disk-replay"
    summary = replay_causal_market_context(
        bundle,
        output_dir=output,
        limits=ReplayLimits(max_memory_mode_bars=1),
    )
    assert summary.boundary_count == len(bundle.market)
    assert sum(1 for _ in (output / "boundary_records.jsonl").open()) == len(bundle.market)


def test_directory_output_is_retrievable_and_hash_manifest_is_external(tmp_path):
    output = tmp_path / "causal-replay"
    bundle = _bundle()
    summary = replay_causal_market_context(bundle, output_dir=output)

    assert summary.output_directory == str(output.resolve())
    assert not (output / "RUN_INCOMPLETE").exists()
    assert (output / "boundary_records.jsonl").is_file()
    assert (output / "entities.jsonl").is_file()
    manifest = json.loads((output / "hash_manifest.json").read_text(encoding="utf-8"))
    assert manifest["self_hash_excluded"] is True
    assert {item["path"] for item in manifest["files"]} >= {
        "summary.json",
        "run_provenance.json",
        "domain_coverage.json",
        "evaluation_boundary.json",
        "entities.jsonl",
        "producer_events.jsonl",
    }
    entity = next(json.loads(line) for line in (output / "entities.jsonl").read_text().splitlines())
    visible_key = bundle.adapter.key_for_position(
        bundle.market.index, 3, InformationPhase.COMPLETED_ROW_AVAILABLE, 0
    )
    state = entity_state_as_of_from_directory(
        output_dir=output, entity_id=entity["entity_id"], as_of_key=visible_key
    )
    assert state["state"] == "PRODUCER_EVENT_FACT_SET_AVAILABLE"
    assert state["revision"]["available_key"]["bar_position"] == 3
    revisions_path = output / "entity_state_revisions.jsonl"
    revisions_path.write_text(revisions_path.read_text(encoding="utf-8") + "{}" + chr(10), encoding="utf-8")
    with pytest.raises(CausalMarketContextCoreError, match="differs from manifest"):
        entity_state_as_of_from_directory(
            output_dir=output, entity_id=entity["entity_id"], as_of_key=visible_key
        )


def test_task_outcome_requires_explicit_authority_and_reuses_existing_excursion_view():


    bundle = _bundle()
    digest = "a" * 64
    authority = TaskEvaluationAuthority(
        task_id="synthetic-software-contract-test",
        task_contract_version="test-v1",
        task_contract_sha256=digest,
        outcome_contract_id="existing-trajectory-excursion-view",
        outcome_contract_version="v1",
        outcome_contract_sha256=digest,
        validation_protocol_id="explicit-test-protocol",
        validation_protocol_version="v1",
        validation_protocol_sha256=digest,
        authorization_reference="synthetic-test-only",
    )
    horizon = HorizonRequest(
        policy_identity=HorizonPolicyIdentity("explicit-test-horizon", "v1", digest),
        requested_end_key=_key(bundle, 5),
    )
    coverage = CoverageContract("synthetic-test-coverage", "v1", digest, pd.Timedelta(minutes=1))
    outcome = evaluate_explicit_task_outcome(
        bundle=bundle,
        authority=authority,
        decision_key=_key(bundle, 2),
        horizon_request=horizon,
        coverage_contract=coverage,
    )
    assert outcome.payload()["status"] == "TASK_AUTHORIZED_FACTUAL_EXCURSION_VIEW_AVAILABLE"
    assert outcome.payload()["model_score_probability_recommendation_or_execution"] is False
    assert not hasattr(outcome, "fills")
    assert not hasattr(outcome, "pnl")


def test_interpretation_ledger_rejects_future_evidence_and_retains_unestablished_revision():
    bundle = _bundle()
    sink = MemorySink()
    ledger = InterpretationRevisionLedger(sink, "test-question")
    key_1, key_2, key_3 = _key(bundle, 1), _key(bundle, 2), _key(bundle, 3)
    ledger.register_evidence("future-fact", key_3)
    with pytest.raises(CausalMarketContextCoreError, match="future"):
        ledger.append_unestablished(key_1, ("future-fact",), ("test-provenance",))

    ledger.register_evidence("visible-fact", key_1)
    revision = ledger.append_unestablished(key_1, ("visible-fact",), ("test-provenance",))
    assert revision.status == "INTERPRETATION_NOT_ESTABLISHED"
    assert revision.record.record_identity == revision.revision_id
    assert revision.record.content["evidence_set_sha256"] == revision.evidence_set_sha256
    policy = InterpretationPolicyReference("explicit-test-policy", "v1", "b" * 64, "caller-asserted")
    with pytest.raises(CausalMarketContextCoreError, match="future"):
        ledger.append_explicit(
            key=key_2,
            statement="hypothesis only",
            policy=policy,
            supporting=("future-fact",),
            contradicting=(),
            assumptions=("software-test-only",),
            provenance=("test-source",),
        )
