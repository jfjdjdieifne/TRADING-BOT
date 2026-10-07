from __future__ import annotations

from dataclasses import replace

import pandas as pd
import pytest

from trading_system.research.hashing import canonical_sha256
from trading_system.research.information_time import InformationPhase, PositionalTimelineAdapter
from trading_system.research.trajectory import trajectory_stage4b1 as s4b1
from trading_system.research.trajectory import trajectory_stage4b2 as s4b2
from trading_system.research.trajectory.trajectory_case_adapter import (
    TrajectoryCaseError,
    create_trajectory_decision_case,
    verify_surface_prefix_compatibility,
)
from trading_system.research.trajectory.trajectory_contract import MarketObservationTimeline
from trading_system.research.trajectory.trajectory_query_views import (
    ObservedEntityLocator,
    TrajectoryQueryError,
    decision_surface_view,
    resolve_observed_entity,
)
from trading_system.research.trajectory.trajectory_stage4b2_consistency import (
    LOCAL_VERIFICATION_SCOPE,
    Stage4B2ConsistencyError,
    verify_stage4b2_consistency,
)
from trading_system.structure.swing_detector import EmpiricalConfirmationPolicy


def _market(n: int = 90) -> pd.DataFrame:
    open_values, high_values, low_values, close_values = [], [], [], []
    level = 100.0
    for position in range(n):
        if position < 65:
            if position % 7 < 4:
                open_values.append(level)
                close_values.append(level + 5.0)
                level = close_values[-1]
            else:
                open_values.append(level)
                close_values.append(level - 3.0)
                level = close_values[-1]
        else:
            open_values.append(level)
            close_values.append(level - 6.0)
            level = close_values[-1]
        high_values.append(max(open_values[-1], close_values[-1]) + 1.0)
        low_values.append(min(open_values[-1], close_values[-1]) - 1.0)
    return pd.DataFrame(
        {"open": open_values, "high": high_values, "low": low_values, "close": close_values},
        index=pd.RangeIndex(n),
        dtype=float,
    )


def _policy() -> EmpiricalConfirmationPolicy:
    return EmpiricalConfirmationPolicy(
        quantile=0.1,
        prior_continuation_reversals=tuple(0.01 * index for index in range(1, 50)),
    )


@pytest.fixture(scope="module")
def _sources():
    market = _market()
    adapter = PositionalTimelineAdapter("stage4b2-consistency-tests")
    timeline = MarketObservationTimeline.seal(adapter=adapter, market_history=market)
    structure = s4b1.build_structure_surface(
        timeline=timeline,
        adapter=adapter,
        market_history=market,
        swing_policy=_policy(),
    )
    surfaces = {
        "LIQUIDITY": s4b2.build_liquidity_surface(
            timeline=timeline,
            adapter=adapter,
            market_history=market,
            structure_surface=structure,
        ),
        "ORDER_BLOCK": s4b2.build_order_block_surface(
            timeline=timeline,
            adapter=adapter,
            market_history=market,
            structure_surface=structure,
        ),
        "FVG": s4b2.build_fvg_surface(
            timeline=timeline,
            adapter=adapter,
            market_history=market,
        ),
        "DEALING_RANGE": s4b2.build_dealing_range_surface(
            timeline=timeline,
            adapter=adapter,
            market_history=market,
            structure_surface=structure,
        ),
    }
    return market, adapter, timeline, structure, surfaces


def _case(sources, *, surfaces=None, decision_position: int = 20):
    market, adapter, timeline, _, producer_surfaces = sources
    decision = adapter.key_for_position(
        market.index,
        decision_position,
        InformationPhase.COMPLETED_ROW_AVAILABLE,
    )
    case = create_trajectory_decision_case(
        timeline=timeline,
        adapter=adapter,
        market_history=market,
        decision_key=decision,
        surfaces=tuple(producer_surfaces.values()) if surfaces is None else tuple(surfaces),
        parent_snapshot=None,
    )
    return case, decision


def _rehash_surface(
    surface,
    *,
    bar_frame: pd.DataFrame | None = None,
    event_frame: pd.DataFrame | None = None,
    entity_frame: pd.DataFrame | None = None,
    derive_entity: bool = True,
):
    """Recompute every mutable table hash and surface ID available to a caller."""
    bar = surface.bar_frame.copy(deep=True) if bar_frame is None else bar_frame.copy(deep=True)
    event = surface.event_frame.copy(deep=True) if event_frame is None else event_frame.copy(deep=True)
    domain, contract, bar_schema, _, entity_schema, _, _ = s4b2._contract_for(surface)
    if derive_entity:
        if domain == "DEALING_RANGE":
            entity = event.loc[:, list(entity_schema)].copy(deep=True)
        else:
            creation_type = {
                "LIQUIDITY": "LEVEL_CREATED",
                "ORDER_BLOCK": "ZONE_CREATED",
                "FVG": "FVG_CREATED",
            }[domain]
            entity = event.loc[event["event_type"] == creation_type, list(entity_schema)].reset_index(drop=True)
    else:
        entity = (
            surface.normalized_entity_frame.copy(deep=True)
            if entity_frame is None
            else entity_frame.copy(deep=True)
        )
    normalized_event = event.copy(deep=True)
    if "event_position" in event.columns:
        normalized_event["same_information_batch_order_unknown"] = event["event_position"].duplicated(keep=False)
    else:
        normalized_event["same_information_batch_order_unknown"] = False
    complete_hash = canonical_sha256(
        domain="STAGE4B2_COMPLETE_RESULT_V1",
        payload={"bar": bar.iloc[:, -len(bar_schema):], "event": event},
    )
    entity_hash = canonical_sha256(domain="STAGE4B2_NORMALIZED_ENTITY_V1", payload=entity)
    normalized_event_hash = canonical_sha256(
        domain="STAGE4B2_NORMALIZED_EVENT_V1", payload=normalized_event
    )
    surface_id = canonical_sha256(
        domain="STAGE4B2_SURFACE_IDENTITY_V1",
        payload={
            "surface_class": surface.__class__.__name__,
            "domain": domain,
            "contract_version": contract,
            "timeline_id": surface.timeline_id,
            "timeline_hash": surface.timeline_hash,
            "adapter_kind": surface.adapter_kind,
            "structure_surface_id": surface.structure_surface_id,
            "reconstruction_input_hash": surface.reconstruction_input_hash,
            "complete_result_hash": complete_hash,
            "normalized_entity_hash": entity_hash,
            "normalized_event_hash": normalized_event_hash,
        },
    )
    return replace(
        surface,
        bar_frame=bar,
        event_frame=event,
        normalized_entity_frame=entity,
        normalized_event_frame=normalized_event,
        complete_result_hash=complete_hash,
        normalized_entity_hash=entity_hash,
        normalized_event_hash=normalized_event_hash,
        surface_id=surface_id,
    )


def _assert_self_integrity_passes(surface) -> None:
    # The attack cases below deliberately repair all accessible Stage4B2 hashes.
    s4b2.verify_surface_integrity(surface)


def test_all_four_producer_surfaces_pass_and_consumer_reuses_each_captured_check(
    _sources, monkeypatch
):
    market, adapter, timeline, _, surfaces = _sources
    for domain, surface in surfaces.items():
        result = verify_stage4b2_consistency(surface)
        assert result.domain == domain
        assert result.surface_id == surface.surface_id
        assert result.verification_scope == LOCAL_VERIFICATION_SCOPE
        assert "existing_surface_integrity" in result.checks
        assert len(surface.normalized_entity_frame) > 0

    # No verifier or consumer should replay a Stage4B2 producer.
    def forbidden(*args, **kwargs):
        raise AssertionError("Stage4B2 producer replay is forbidden during verification/consumption")

    for engine in (
        s4b2.CausalLiquidityMapEngine,
        s4b2.CausalOrderBlockEngine,
        s4b2.CausalFVGEngine,
        s4b2.CausalDealingRangeEngine,
    ):
        monkeypatch.setattr(engine, "analyze", forbidden)

    import trading_system.research.trajectory.trajectory_case_adapter as case_adapter

    real_verify = case_adapter.verify_stage4b2_consistency
    verified_surface_ids: list[str] = []

    def counted(snapshot):
        verified_surface_ids.append(snapshot.surface_id)
        return real_verify(snapshot)

    monkeypatch.setattr(case_adapter, "verify_stage4b2_consistency", counted)
    case, _ = _case(_sources)
    assert len(verified_surface_ids) == 4
    assert all(binding.verification_scope == LOCAL_VERIFICATION_SCOPE for binding in case.surface_prefix_bindings)
    assert all(
        version.verification_scope == LOCAL_VERIFICATION_SCOPE
        for version in case.source_provenance.surface_versions
    )

    view = decision_surface_view(case=case, surfaces=tuple(surfaces.values()))
    assert {instance.domain for instance in view.surfaces} == set(surfaces)
    # Prefix projection uses the same already-validated private snapshots; it
    # reruns only the existing public integrity/projector, not the new checker.
    assert len(verified_surface_ids) == 8

    liquidity_binding = next(item for item in case.surface_prefix_bindings if item.domain == "LIQUIDITY")
    resolved = resolve_observed_entity(
        case=case,
        surfaces=tuple(surfaces.values()),
        locator=ObservedEntityLocator("LIQUIDITY", liquidity_binding.stable_binding_hash, "0"),
    )
    assert resolved.locator.canonical_entity_id == "0"
    assert len(verified_surface_ids) == 12
    assert set(verified_surface_ids[:4]) == {surface.surface_id for surface in surfaces.values()}


def test_rehashed_adversarial_surfaces_fail_independent_consistency(_sources):
    surfaces = _sources[4]
    liquidity = surfaces["LIQUIDITY"]
    events = liquidity.event_frame.copy(deep=True)
    bar = liquidity.bar_frame.copy(deep=True)
    first_id, second_id = [int(value) for value in liquidity.normalized_entity_frame["level_id"].iloc[:2]]
    second_created = liquidity.normalized_entity_frame[
        liquidity.normalized_entity_frame["level_id"] == second_id
    ].iloc[0]
    second_position = int(second_created["source_confirmation_position"])
    events.loc[events["level_id"] == second_id, "level_id"] = first_id
    bar.loc[bar.index[second_position], "created_level_id"] = first_id
    duplicate_id = _rehash_surface(liquidity, event_frame=events, bar_frame=bar)

    events = liquidity.event_frame.copy(deep=True)
    creation_index = events.index[events["event_type"] == "LEVEL_CREATED"][0]
    events.loc[creation_index, "immutable_level_price"] += 0.25
    creation_mirror = _rehash_surface(liquidity, event_frame=events)

    events = liquidity.event_frame.copy(deep=True)
    events.loc[events["level_id"] == first_id, "source_confirmation_position"] += 1
    wrong_availability = _rehash_surface(liquidity, event_frame=events)

    events = liquidity.event_frame.copy(deep=True)
    lifecycle_index = events.index[events["event_type"] != "LEVEL_CREATED"][0]
    events.loc[lifecycle_index, "level_id"] = 999999
    unknown_reference = _rehash_surface(liquidity, event_frame=events)

    events = liquidity.event_frame.copy(deep=True)
    lifecycle_index = events.index[events["event_type"] != "LEVEL_CREATED"][0]
    events.loc[lifecycle_index, "event_close"] += 0.125
    event_ohlc = _rehash_surface(liquidity, event_frame=events)

    events = liquidity.event_frame.copy(deep=True)
    lifecycle_index = events.index[events["event_type"] != "LEVEL_CREATED"][0]
    events.loc[lifecycle_index, "event_price"] += 0.125
    event_price = _rehash_surface(liquidity, event_frame=events)

    fvg = surfaces["FVG"]
    events = fvg.event_frame.copy(deep=True)
    bar = fvg.bar_frame.copy(deep=True)
    fvg_id = int(fvg.normalized_entity_frame.iloc[0]["fvg_id"])
    create_event = events.loc[events["fvg_id"] == fvg_id].iloc[0]
    creation_position = int(create_event["creation_position"])
    changed_low = float(create_event["zone_low"]) + 0.25
    events.loc[events["fvg_id"] == fvg_id, "zone_low"] = changed_low
    bar.loc[bar.index[creation_position], "created_fvg_zone_low"] = changed_low
    fvg_geometry = _rehash_surface(fvg, event_frame=events, bar_frame=bar)

    order_block = surfaces["ORDER_BLOCK"]
    events = order_block.event_frame.copy(deep=True)
    bar = order_block.bar_frame.copy(deep=True)
    zone_id = int(order_block.normalized_entity_frame.iloc[0]["zone_id"])
    create_event = events.loc[events["zone_id"] == zone_id].iloc[0]
    creation_position = int(create_event["creation_position"])
    events.loc[events["zone_id"] == zone_id, "full_zone_low"] += 0.25
    bar.loc[bar.index[creation_position], "created_ob_full_zone_low"] += 0.25
    ob_source_bounds = _rehash_surface(order_block, event_frame=events, bar_frame=bar)

    dealing = surfaces["DEALING_RANGE"]
    events = dealing.event_frame.copy(deep=True)
    bar = dealing.bar_frame.copy(deep=True)
    range_id = int(dealing.normalized_entity_frame.iloc[0]["range_id"])
    creation_position = int(
        dealing.normalized_entity_frame.loc[
            dealing.normalized_entity_frame["range_id"] == range_id, "creation_position"
        ].iloc[0]
    )
    events.loc[events["range_id"] == range_id, "first_endpoint_price"] += 0.25
    bar.loc[bar.index[creation_position], "created_range_first_endpoint_price"] += 0.25
    dealing_endpoint = _rehash_surface(dealing, event_frame=events, bar_frame=bar)

    adversarial = (
        (duplicate_id, "duplicate level_id"),
        (creation_mirror, "created_level_price"),
        (wrong_availability, "liquidity_level_created rows"),
        (unknown_reference, "unknown level_id"),
        (event_ohlc, "event.event_close"),
        (event_price, "event.event_price"),
        (fvg_geometry, "source bars"),
        (ob_source_bounds, "origin bar"),
        (dealing_endpoint, "source swing price"),
    )
    for mutated, message in adversarial:
        _assert_self_integrity_passes(mutated)
        with pytest.raises(Stage4B2ConsistencyError, match=message):
            verify_stage4b2_consistency(mutated)

    # A normalized entity-only change, with its own hash and the surface ID
    # repaired, is also rejected because it is not the event-table projection.
    entity = liquidity.normalized_entity_frame.copy(deep=True)
    entity.loc[0, "immutable_level_price"] += 0.25
    projection_mismatch = _rehash_surface(liquidity, entity_frame=entity, derive_entity=False)
    _assert_self_integrity_passes(projection_mismatch)
    with pytest.raises(Stage4B2ConsistencyError, match="source-table projection"):
        verify_stage4b2_consistency(projection_mismatch)


def test_failed_validation_emits_no_scope_and_case_creation_fails_closed(_sources):
    market, adapter, timeline, _, surfaces = _sources
    source = surfaces["LIQUIDITY"]
    events = source.event_frame.copy(deep=True)
    lifecycle_index = events.index[events["event_type"] != "LEVEL_CREATED"][0]
    events.loc[lifecycle_index, "level_id"] = 999999
    invalid = _rehash_surface(source, event_frame=events)
    _assert_self_integrity_passes(invalid)

    result = None
    with pytest.raises(Stage4B2ConsistencyError):
        result = verify_stage4b2_consistency(invalid)
    assert result is None
    with pytest.raises(TrajectoryCaseError, match="unknown level_id"):
        _case(_sources, surfaces=(invalid,))

    valid_case, _ = _case(_sources)
    invalid_surfaces = (invalid,) + tuple(
        surface for domain, surface in surfaces.items() if domain != "LIQUIDITY"
    )
    with pytest.raises(TrajectoryQueryError, match="unknown level_id"):
        decision_surface_view(case=valid_case, surfaces=invalid_surfaces)
    binding = next(item for item in valid_case.surface_prefix_bindings if item.domain == "LIQUIDITY")
    with pytest.raises(TrajectoryQueryError, match="unknown level_id"):
        resolve_observed_entity(
            case=valid_case,
            surfaces=invalid_surfaces,
            locator=ObservedEntityLocator("LIQUIDITY", binding.stable_binding_hash, "0"),
        )


def test_case_uses_exact_surface_snapshot_after_caller_mutates_source(_sources, monkeypatch):
    market, adapter, timeline, _, surfaces = _sources
    original = surfaces["LIQUIDITY"]
    import trading_system.research.trajectory.trajectory_case_adapter as case_adapter

    capture = case_adapter.snapshot_stage4_surface

    def capture_then_mutate(source):
        snapshot = capture(source)
        if source is original:
            source.normalized_entity_frame.loc[0, "immutable_level_price"] += 0.5
        return snapshot

    monkeypatch.setattr(case_adapter, "snapshot_stage4_surface", capture_then_mutate)
    case, _ = _case(_sources, surfaces=(original,))
    binding = case.surface_prefix_bindings[0]
    assert binding.verification_scope == LOCAL_VERIFICATION_SCOPE
    assert case.source_provenance.surface_versions[0].verification_scope == LOCAL_VERIFICATION_SCOPE
    # The caller's post-capture mutation cannot affect the case made from the
    # private snapshot; the now-mutated original is rejected independently.
    with pytest.raises(Stage4B2ConsistencyError):
        verify_stage4b2_consistency(original)
    assert case.timeline_id == timeline.timeline_id
    assert adapter.timeline_id == timeline.timeline_id


def test_append_only_extension_preserves_stage4b2_prefix_case_identity():
    short_market = _market(70)
    long_market = _market(90)
    short_adapter = PositionalTimelineAdapter("stage4b2-append-prefix")
    long_adapter = PositionalTimelineAdapter("stage4b2-append-prefix")
    short_timeline = MarketObservationTimeline.seal(adapter=short_adapter, market_history=short_market)
    long_timeline = MarketObservationTimeline.seal(adapter=long_adapter, market_history=long_market)
    short_structure = s4b1.build_structure_surface(
        timeline=short_timeline,
        adapter=short_adapter,
        market_history=short_market,
        swing_policy=_policy(),
    )
    long_structure = s4b1.build_structure_surface(
        timeline=long_timeline,
        adapter=long_adapter,
        market_history=long_market,
        swing_policy=_policy(),
    )
    short_surface = s4b2.build_liquidity_surface(
        timeline=short_timeline,
        adapter=short_adapter,
        market_history=short_market,
        structure_surface=short_structure,
    )
    long_surface = s4b2.build_liquidity_surface(
        timeline=long_timeline,
        adapter=long_adapter,
        market_history=long_market,
        structure_surface=long_structure,
    )
    short_decision = short_adapter.key_for_position(
        short_market.index, 20, InformationPhase.COMPLETED_ROW_AVAILABLE
    )
    long_decision = long_adapter.key_for_position(
        long_market.index, 20, InformationPhase.COMPLETED_ROW_AVAILABLE
    )
    short_case = create_trajectory_decision_case(
        timeline=short_timeline,
        adapter=short_adapter,
        market_history=short_market,
        decision_key=short_decision,
        surfaces=(short_surface,),
        parent_snapshot=None,
    )
    long_case = create_trajectory_decision_case(
        timeline=long_timeline,
        adapter=long_adapter,
        market_history=long_market,
        decision_key=long_decision,
        surfaces=(long_surface,),
        parent_snapshot=None,
    )
    assert short_surface.surface_id != long_surface.surface_id
    assert short_case.case_id == long_case.case_id
    assert short_case.case_hash == long_case.case_hash
    assert short_case.surface_prefix_bindings[0].stable_binding_hash == (
        long_case.surface_prefix_bindings[0].stable_binding_hash
    )
    assert short_case.source_provenance.provenance_binding_hash != (
        long_case.source_provenance.provenance_binding_hash
    )
    compatible = verify_surface_prefix_compatibility(case=short_case, surface=long_surface)
    assert compatible.stable_binding_hash == short_case.surface_prefix_bindings[0].stable_binding_hash
    assert compatible.verification_scope == LOCAL_VERIFICATION_SCOPE
