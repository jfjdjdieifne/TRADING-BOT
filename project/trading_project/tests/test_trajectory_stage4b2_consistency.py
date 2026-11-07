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
    create_asof_surface_view,
    decision_surface_view,
    resolve_observed_entity,
)
from trading_system.research.trajectory.trajectory_stage4b2_consistency import (
    LOCAL_VERIFICATION_SCOPE,
    Stage4B2ConsistencyError,
    _CREATION_ABSENCE_DEFAULTS,
    verify_stage4b2_consistency,
)
from trading_system.structure.swing_detector import EmpiricalConfirmationPolicy


_EXPECTED_CREATION_ABSENCE_DEFAULTS = {
    "LIQUIDITY": {
        "created_level_id": None,
        "created_level_side": "NONE",
        "created_level_price": None,
        "created_level_origin_position": None,
        "created_level_confirmation_position": None,
        "created_level_source_class": "NONE",
        "nearest_prior_same_side_level_id": None,
        "nearest_same_side_distance_fraction": None,
        "nearest_distance_percentile": None,
        "nearest_distance_reference_history_count": 0,
    },
    "ORDER_BLOCK": {
        "created_ob_zone_id": None,
        "created_ob_direction": "NONE",
        "created_ob_origin_position": None,
        "created_ob_creation_position": None,
        "created_ob_full_zone_low": None,
        "created_ob_full_zone_high": None,
        "created_ob_body_low": None,
        "created_ob_body_high": None,
        "created_ob_source_break_event": "NONE",
        "created_ob_origin_prior_use_count": 0,
        "created_ob_displacement_fraction": None,
        "created_ob_displacement_percentile": None,
        "created_ob_displacement_history_count": 0,
        "created_ob_search_boundary_position": None,
        "created_ob_opposite_candle_count_in_leg": 0,
    },
    "FVG": {
        "created_fvg_id": None,
        "created_fvg_direction": "NONE",
        "created_fvg_origin_position": None,
        "created_fvg_middle_position": None,
        "created_fvg_creation_position": None,
        "created_fvg_zone_low": None,
        "created_fvg_zone_high": None,
        "created_fvg_midpoint": None,
        "created_fvg_gap_width": None,
        "created_fvg_gap_width_fraction": None,
        "created_fvg_gap_width_percentile": None,
        "created_fvg_gap_width_history_count": 0,
        "created_fvg_middle_body_fraction": None,
        "created_fvg_middle_signed_body_fraction": None,
    },
    "DEALING_RANGE": {
        "created_range_id": None,
        "created_range_direction": "NONE",
        "created_range_creation_position": None,
        "created_range_low": None,
        "created_range_high": None,
        "created_range_width": None,
        "created_range_midpoint": None,
        "created_range_first_endpoint_side": "NONE",
        "created_range_first_endpoint_origin_position": None,
        "created_range_first_endpoint_confirmation_position": None,
        "created_range_first_endpoint_price": None,
        "created_range_first_endpoint_class": "NONE",
        "created_range_second_endpoint_side": "NONE",
        "created_range_second_endpoint_origin_position": None,
        "created_range_second_endpoint_confirmation_position": None,
        "created_range_second_endpoint_price": None,
        "created_range_second_endpoint_class": "NONE",
    },
}


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
        result = verify_stage4b2_consistency(surface, market_history=market)
        assert result.domain == domain
        assert result.surface_id == surface.surface_id
        assert result.verification_scope == LOCAL_VERIFICATION_SCOPE
        assert "existing_surface_integrity" in result.checks
        assert "captured_market_source_binding" in result.checks
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

    def counted(snapshot, **kwargs):
        verified_surface_ids.append(snapshot.surface_id)
        return real_verify(snapshot, **kwargs)

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


def test_stage4b2_market_passthrough_is_bound_to_the_captured_market_at_all_consumers(_sources):
    market, adapter, _, _, surfaces = _sources
    liquidity = surfaces["LIQUIDITY"]
    assert float(market["high"].iloc[6]) == 115.0
    assert float(liquidity.bar_frame["high"].iloc[6]) == 115.0

    bar = liquidity.bar_frame.copy(deep=True)
    bar.loc[bar.index[6], "high"] = 125.0
    contradictory = _rehash_surface(liquidity, bar_frame=bar)
    _assert_self_integrity_passes(contradictory)
    with pytest.raises(Stage4B2ConsistencyError, match="exact captured market source observation"):
        verify_stage4b2_consistency(contradictory, market_history=market)
    with pytest.raises(TrajectoryCaseError, match="exact captured market source observation"):
        _case(_sources, surfaces=(contradictory,))

    # A previously valid case retains source evidence for as-of and observed-row
    # consumers; neither public route can relabel this rehashed contradiction.
    case, _ = _case(_sources, surfaces=(liquidity,))
    binding = case.surface_prefix_bindings[0]
    with pytest.raises(TrajectoryQueryError, match="captured market source"):
        decision_surface_view(case=case, surfaces=(contradictory,))
    with pytest.raises(TrajectoryQueryError, match="captured market source"):
        create_asof_surface_view(
            case=case,
            surfaces=(contradictory,),
            as_of_key=adapter.key_for_position(
                market.index, 50, InformationPhase.COMPLETED_ROW_AVAILABLE
            ),
        )
    with pytest.raises(TrajectoryQueryError, match="captured market source"):
        resolve_observed_entity(
            case=case,
            surfaces=(contradictory,),
            locator=ObservedEntityLocator("LIQUIDITY", binding.stable_binding_hash, "0"),
        )
    with pytest.raises(Stage4B2ConsistencyError, match="required captured market source evidence"):
        verify_stage4b2_consistency(liquidity)


def test_every_creation_only_field_enforces_the_closed_producer_absence_default(_sources):
    assert _CREATION_ABSENCE_DEFAULTS == _EXPECTED_CREATION_ABSENCE_DEFAULTS
    market, _, _, _, surfaces = _sources
    flag_by_domain = {
        "LIQUIDITY": "liquidity_level_created",
        "ORDER_BLOCK": "ob_candidate_created",
        "FVG": "fvg_candidate_created",
        "DEALING_RANGE": "dealing_range_created",
    }
    for domain, defaults in _EXPECTED_CREATION_ABSENCE_DEFAULTS.items():
        surface = surfaces[domain]
        flag = flag_by_domain[domain]
        source_bar = surface.bar_frame
        position = int(source_bar.index[~source_bar[flag].astype(bool)][0])
        for column, default in defaults.items():
            bar = source_bar.copy(deep=True)
            dtype = bar[column].dtype
            if default is None:
                if pd.api.types.is_integer_dtype(dtype):
                    invalid_value = 999
                elif pd.api.types.is_numeric_dtype(dtype):
                    invalid_value = 999.125
                else:
                    invalid_value = "FORGED"
            elif isinstance(default, str):
                invalid_value = "FORGED"
            else:
                invalid_value = default + 1
            bar.loc[bar.index[position], column] = invalid_value
            mutated = _rehash_surface(surface, bar_frame=bar)
            _assert_self_integrity_passes(mutated)
            with pytest.raises(Stage4B2ConsistencyError, match=column):
                verify_stage4b2_consistency(mutated, market_history=market)


def _touch_qualifies(domain, surface, entity, position):
    if domain == "LIQUIDITY":
        price = float(entity["immutable_level_price"])
        if entity["side"] == "HIGH_SIDE":
            return float(surface.bar_frame["high"].iloc[position]) >= price
        return float(surface.bar_frame["low"].iloc[position]) <= price
    if domain == "ORDER_BLOCK":
        low, high = float(entity["full_zone_low"]), float(entity["full_zone_high"])
    else:
        low, high = float(entity["zone_low"]), float(entity["zone_high"])
    return (
        float(surface.bar_frame["high"].iloc[position]) >= low
        and float(surface.bar_frame["low"].iloc[position]) <= high
    )


def _mutate_first_touch(surface, domain, event_row, entity_row, target_position):
    events = surface.event_frame.copy(deep=True)
    index = event_row.name
    available = int(
        entity_row["source_confirmation_position"]
        if domain == "LIQUIDITY"
        else entity_row["creation_position"]
    )
    events.loc[index, "event_position"] = target_position
    if domain == "LIQUIDITY":
        bar = surface.bar_frame
        events.loc[index, "event_close"] = bar["close"].iloc[target_position]
        events.loc[index, "event_price"] = (
            bar["high"].iloc[target_position]
            if entity_row["side"] == "HIGH_SIDE"
            else bar["low"].iloc[target_position]
        )
        events.loc[index, "level_age_bars"] = target_position - available
    else:
        bar = surface.bar_frame
        events.loc[index, "event_high"] = bar["high"].iloc[target_position]
        events.loc[index, "event_low"] = bar["low"].iloc[target_position]
        events.loc[index, "event_close"] = bar["close"].iloc[target_position]
        age_column = "zone_age_bars" if domain == "ORDER_BLOCK" else "fvg_age_bars"
        events.loc[index, age_column] = target_position - available
        if domain == "FVG":
            low, high = float(entity_row["zone_low"]), float(entity_row["zone_high"])
            if _touch_qualifies(domain, surface, entity_row, target_position):
                events.loc[index, "zone_range_coverage_fraction"] = (
                    min(float(bar["high"].iloc[target_position]), high)
                    - max(float(bar["low"].iloc[target_position]), low)
                ) / (high - low)
            else:
                events.loc[index, "zone_range_coverage_fraction"] = float("nan")
    return _rehash_surface(surface, event_frame=events)


@pytest.mark.parametrize("domain", ("LIQUIDITY", "ORDER_BLOCK", "FVG"))
@pytest.mark.parametrize("mutation", ("false", "later"))
def test_first_touch_must_match_the_exact_producer_predicate_and_earliest_bar(
    _sources, domain, mutation
):
    market, _, _, _, surfaces = _sources
    surface = surfaces[domain]
    id_column = {"LIQUIDITY": "level_id", "ORDER_BLOCK": "zone_id", "FVG": "fvg_id"}[domain]
    touch = surface.event_frame.loc[surface.event_frame["event_type"] == "FIRST_TOUCH"].iloc[0]
    entity = surface.normalized_entity_frame.loc[
        surface.normalized_entity_frame[id_column] == touch[id_column]
    ].iloc[0]
    available = int(
        entity["source_confirmation_position"]
        if domain == "LIQUIDITY"
        else entity["creation_position"]
    )
    actual_position = int(touch["event_position"])
    if mutation == "false":
        target = next(
            position
            for position in range(available + 1, len(surface.bar_frame))
            if not _touch_qualifies(domain, surface, entity, position)
        )
    else:
        target = next(
            position
            for position in range(actual_position + 1, len(surface.bar_frame))
            if _touch_qualifies(domain, surface, entity, position)
        )
    assert target != actual_position
    mutated = _mutate_first_touch(surface, domain, touch, entity, target)
    _assert_self_integrity_passes(mutated)
    with pytest.raises(Stage4B2ConsistencyError, match="FIRST_TOUCH does not match the exact earliest producer predicate"):
        verify_stage4b2_consistency(mutated, market_history=market)


def test_liquidity_aggregate_columns_match_per_bar_events_and_cumulative_known_levels(_sources):
    market, _, _, _, surfaces = _sources
    surface = surfaces["LIQUIDITY"]
    aggregate_columns = (
        "high_side_first_touch_count", "low_side_first_touch_count",
        "high_side_first_wick_breach_count", "low_side_first_wick_breach_count",
        "high_side_first_wick_only_count", "low_side_first_wick_only_count",
        "high_side_first_close_breach_count", "low_side_first_close_breach_count",
        "high_side_first_reclaim_count", "low_side_first_reclaim_count",
        "known_high_side_level_count", "known_low_side_level_count",
    )
    for column in aggregate_columns:
        bar = surface.bar_frame.copy(deep=True)
        current = int(bar[column].iloc[20])
        bar.loc[bar.index[20], column] = current + 1
        mutated = _rehash_surface(surface, bar_frame=bar)
        _assert_self_integrity_passes(mutated)
        message = "cumulative known-level counts" if column.startswith("known_") else column
        with pytest.raises(Stage4B2ConsistencyError, match=message):
            verify_stage4b2_consistency(mutated, market_history=market)


def test_dealing_range_checks_second_origin_order_and_uses_creation_as_availability(_sources):
    market, adapter, _, _, surfaces = _sources
    dealing = surfaces["DEALING_RANGE"]
    events = dealing.event_frame.copy(deep=True)
    bar = dealing.bar_frame.copy(deep=True)
    last = events.iloc[-1]
    range_id = int(last["range_id"])
    second_confirmation = int(last["second_endpoint_confirmation_position"])
    creation = int(last["creation_position"])
    invalid_origin = second_confirmation + 1
    assert invalid_origin < len(bar)
    events.loc[events["range_id"] == range_id, "second_endpoint_origin_position"] = invalid_origin
    bar.loc[bar.index[creation], "created_range_second_endpoint_origin_position"] = invalid_origin
    bar.loc[bar.index[second_confirmation], "swing_origin_position"] = invalid_origin
    mutated = _rehash_surface(dealing, event_frame=events, bar_frame=bar)
    _assert_self_integrity_passes(mutated)
    with pytest.raises(Stage4B2ConsistencyError, match="origin/confirmation availability ordering"):
        verify_stage4b2_consistency(mutated, market_history=market)

    # The first endpoint uses the same independent origin<=confirmation rule.
    events = dealing.event_frame.copy(deep=True)
    bar = dealing.bar_frame.copy(deep=True)
    target_confirmation = int(last["first_endpoint_confirmation_position"])
    invalid_origin = target_confirmation + 1
    assert invalid_origin < len(bar)
    for row in events.to_dict(orient="records"):
        creation_position = int(row["creation_position"])
        if int(row["first_endpoint_confirmation_position"]) == target_confirmation:
            events.loc[events["range_id"] == row["range_id"], "first_endpoint_origin_position"] = invalid_origin
            bar.loc[bar.index[creation_position], "created_range_first_endpoint_origin_position"] = invalid_origin
        if int(row["second_endpoint_confirmation_position"]) == target_confirmation:
            events.loc[events["range_id"] == row["range_id"], "second_endpoint_origin_position"] = invalid_origin
            bar.loc[bar.index[creation_position], "created_range_second_endpoint_origin_position"] = invalid_origin
    bar.loc[bar.index[target_confirmation], "swing_origin_position"] = invalid_origin
    mutated_first = _rehash_surface(dealing, event_frame=events, bar_frame=bar)
    _assert_self_integrity_passes(mutated_first)
    with pytest.raises(Stage4B2ConsistencyError, match="origin/confirmation availability ordering"):
        verify_stage4b2_consistency(mutated_first, market_history=market)

    first = dealing.normalized_entity_frame.iloc[0]
    second_origin = int(first["second_endpoint_origin_position"])
    creation_position = int(first["creation_position"])
    assert second_origin < creation_position
    case, _ = _case(_sources, surfaces=(dealing,), decision_position=second_origin)
    binding = case.surface_prefix_bindings[0]
    with pytest.raises(TrajectoryQueryError, match="canonical producer entity ID"):
        resolve_observed_entity(
            case=case,
            surfaces=(dealing,),
            locator=ObservedEntityLocator(
                "DEALING_RANGE", binding.stable_binding_hash, str(int(first["range_id"]))
            ),
        )


def test_rehashed_adversarial_surfaces_fail_independent_consistency(_sources):
    market = _sources[0]
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
            verify_stage4b2_consistency(mutated, market_history=market)

    # A normalized entity-only change, with its own hash and the surface ID
    # repaired, is also rejected because it is not the event-table projection.
    entity = liquidity.normalized_entity_frame.copy(deep=True)
    entity.loc[0, "immutable_level_price"] += 0.25
    projection_mismatch = _rehash_surface(liquidity, entity_frame=entity, derive_entity=False)
    _assert_self_integrity_passes(projection_mismatch)
    with pytest.raises(Stage4B2ConsistencyError, match="source-table projection"):
        verify_stage4b2_consistency(projection_mismatch, market_history=market)


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
        result = verify_stage4b2_consistency(invalid, market_history=market)
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


def test_case_uses_exact_market_and_surface_snapshots_after_caller_mutates_source(
    _sources, monkeypatch
):
    market, adapter, timeline, _, surfaces = _sources
    market_input = market.copy(deep=True)
    original = replace(
        surfaces["LIQUIDITY"],
        normalized_entity_frame=surfaces["LIQUIDITY"].normalized_entity_frame.copy(deep=True),
    )
    import trading_system.research.trajectory.trajectory_case_adapter as case_adapter
    from trading_system.research.trajectory.trajectory_stage4b2_consistency import (
        capture_stage4b2_market_source_column_hashes,
    )

    expected_source_hashes = capture_stage4b2_market_source_column_hashes(market, (original,))
    capture_market = case_adapter.snapshot_market_history
    capture_surface = case_adapter.snapshot_stage4_surface

    def capture_market_then_mutate(source):
        snapshot = capture_market(source)
        if source is market_input:
            source.loc[source.index[6], "high"] = 125.0
        return snapshot

    def capture_surface_then_mutate(source):
        snapshot = capture_surface(source)
        if source is original:
            source.normalized_entity_frame.loc[0, "immutable_level_price"] += 0.5
        return snapshot

    monkeypatch.setattr(case_adapter, "snapshot_market_history", capture_market_then_mutate)
    monkeypatch.setattr(case_adapter, "snapshot_stage4_surface", capture_surface_then_mutate)
    decision = adapter.key_for_position(
        market.index, 20, InformationPhase.COMPLETED_ROW_AVAILABLE
    )
    case = create_trajectory_decision_case(
        timeline=timeline,
        adapter=adapter,
        market_history=market_input,
        decision_key=decision,
        surfaces=(original,),
        parent_snapshot=None,
    )
    binding = case.surface_prefix_bindings[0]
    assert binding.verification_scope == LOCAL_VERIFICATION_SCOPE
    assert case.source_provenance.surface_versions[0].verification_scope == LOCAL_VERIFICATION_SCOPE
    assert case.source_provenance.market_source_column_hashes == expected_source_hashes
    assert float(market_input["high"].iloc[6]) == 125.0
    # Both caller mutations happened only after their respective private
    # captures; neither can affect the immutable case or verification result.
    with pytest.raises(Stage4B2ConsistencyError):
        verify_stage4b2_consistency(original, market_history=market)
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
    assert {len(hashes) for _, hashes in short_case.source_provenance.market_source_column_hashes} == {70}
    assert {len(hashes) for _, hashes in long_case.source_provenance.market_source_column_hashes} == {90}
    compatible = verify_surface_prefix_compatibility(case=short_case, surface=long_surface)
    assert compatible.stable_binding_hash == short_case.surface_prefix_bindings[0].stable_binding_hash
    assert compatible.verification_scope == LOCAL_VERIFICATION_SCOPE

    # The valid append is usable through source evidence captured by the short
    # case, but a later as-of boundary without captured market evidence fails closed.
    later_key = long_adapter.key_for_position(
        long_market.index, 75, InformationPhase.COMPLETED_ROW_AVAILABLE
    )
    with pytest.raises(TrajectoryQueryError, match="does not reach as-of position 75"):
        create_asof_surface_view(
            case=short_case,
            surfaces=(long_surface,),
            as_of_key=later_key,
        )
