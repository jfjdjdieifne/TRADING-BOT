from __future__ import annotations

from dataclasses import fields, FrozenInstanceError

import pandas as pd
import pytest

from trading_system.research.hashing import canonical_sha256
from trading_system.research.information_time import (
    InformationPhase,
    PositionalTimelineAdapter,
)
from trading_system.research.trajectory.trajectory_case_adapter import (
    ParentDecisionSnapshotReference,
    TrajectoryCaseError,
    create_trajectory_decision_case,
)
from trading_system.research.trajectory.trajectory_contract import MarketObservationTimeline
from trading_system.research.trajectory import trajectory_stage4a as s4a


def _market(n: int = 12) -> pd.DataFrame:
    close = [100.0 + float(i) for i in range(n)]
    open_ = [value - 0.25 for value in close]
    return pd.DataFrame(
        {
            "open": open_,
            "high": [value + 1.0 for value in close],
            "low": [value - 1.0 for value in close],
            "close": close,
            "volume": [10.0 + i for i in range(n)],
        },
        index=pd.RangeIndex(n),
    )


def _build_case(market: pd.DataFrame, *, timeline_id: str = "case-test", decision_position: int = 4,
                parent: ParentDecisionSnapshotReference | None = None):
    adapter = PositionalTimelineAdapter(timeline_id)
    timeline = MarketObservationTimeline.seal(adapter=adapter, market_history=market)
    key = adapter.key_for_position(
        market.index,
        decision_position,
        InformationPhase.COMPLETED_ROW_AVAILABLE,
    )
    surface = s4a.build_volatility_surface(
        timeline=timeline,
        adapter=adapter,
        market_history=market,
    )
    case = create_trajectory_decision_case(
        timeline=timeline,
        adapter=adapter,
        market_history=market,
        decision_key=key,
        surfaces=(surface,),
        parent_snapshot=parent,
    )
    return case, timeline, adapter, surface, key


def test_case_is_frozen_neutral_and_records_no_source_retrieval_claim():
    market = _market()
    case, _, _, _, _ = _build_case(market)

    names = {field.name for field in fields(case)}
    assert not names.intersection(
        {"direction", "entry", "entry_price", "target", "stop", "hypothesis", "buy", "sell"}
    )
    assert case.parent_snapshot is None
    assert case.source_provenance.source_artifact_reference is None
    assert case.source_provenance.timeline_hash
    assert case.case_id != case.case_hash  # distinct hash domains; both are stable case identities


def test_case_identity_is_invariant_to_future_append_and_future_values():
    short = _market(9)
    long = _market(14)
    # Past rows are exact; future data are deliberately changed.
    long.loc[9:, "close"] = [150.0, 91.0, 177.0, 88.0, 199.0]
    long.loc[9:, "open"] = long.loc[9:, "close"] - 0.5
    long.loc[9:, "high"] = long.loc[9:, "close"] + 2.0
    long.loc[9:, "low"] = long.loc[9:, "close"] - 2.0

    short_case, short_timeline, _, short_surface, _ = _build_case(short, decision_position=4)
    long_case, long_timeline, _, long_surface, _ = _build_case(long, decision_position=4)

    assert short_timeline.timeline_hash != long_timeline.timeline_hash
    assert short_surface.surface_id != long_surface.surface_id
    assert short_case.case_id == long_case.case_id
    assert short_case.case_hash == long_case.case_hash
    assert short_case.decision_prefix_hash == long_case.decision_prefix_hash
    assert (
        short_case.surface_prefix_bindings[0].stable_binding_hash
        == long_case.surface_prefix_bindings[0].stable_binding_hash
    )
    assert (
        short_case.source_provenance.provenance_binding_hash
        != long_case.source_provenance.provenance_binding_hash
    )


def test_case_identity_changes_when_decision_facts_or_exact_key_change():
    base = _market()
    changed_prefix = base.copy(deep=True)
    changed_prefix.loc[2, "close"] += 0.125
    changed_prefix.loc[2, "high"] += 0.125

    base_case, _, _, _, _ = _build_case(base, decision_position=4)
    changed_case, _, _, _, _ = _build_case(changed_prefix, decision_position=4)
    later_case, _, _, _, _ = _build_case(base, decision_position=5)

    assert base_case.case_id != changed_case.case_id
    assert base_case.case_hash != changed_case.case_hash
    assert base_case.case_id != later_case.case_id
    assert base_case.decision_prefix_hash != changed_case.decision_prefix_hash


def test_parent_snapshot_must_be_available_at_decision_and_is_identity_binding():
    market = _market()
    adapter = PositionalTimelineAdapter("parent-case")
    timeline = MarketObservationTimeline.seal(adapter=adapter, market_history=market)
    decision_key = adapter.key_for_position(market.index, 4, InformationPhase.COMPLETED_ROW_AVAILABLE)
    available_key = adapter.key_for_position(market.index, 3, InformationPhase.RESEARCH_SNAPSHOT_AVAILABLE)
    later_key = adapter.key_for_position(market.index, 5, InformationPhase.COMPLETED_ROW_AVAILABLE)
    surface = s4a.build_volatility_surface(timeline=timeline, adapter=adapter, market_history=market)

    parent = ParentDecisionSnapshotReference(
        snapshot_id="parent-snapshot-1",
        schema_version="NEUTRAL_PARENT_V1",
        content_sha256="a" * 64,
        available_at=available_key,
    )
    parent_case = create_trajectory_decision_case(
        timeline=timeline,
        adapter=adapter,
        market_history=market,
        decision_key=decision_key,
        surfaces=(surface,),
        parent_snapshot=parent,
    )
    no_parent_case = create_trajectory_decision_case(
        timeline=timeline,
        adapter=adapter,
        market_history=market,
        decision_key=decision_key,
        surfaces=(surface,),
        parent_snapshot=None,
    )
    assert parent_case.case_id != no_parent_case.case_id

    unavailable = ParentDecisionSnapshotReference(
        snapshot_id="later-snapshot",
        schema_version="NEUTRAL_PARENT_V1",
        content_sha256="b" * 64,
        available_at=later_key,
    )
    with pytest.raises(TrajectoryCaseError, match="not available at decision"):
        create_trajectory_decision_case(
            timeline=timeline,
            adapter=adapter,
            market_history=market,
            decision_key=decision_key,
            surfaces=(surface,),
            parent_snapshot=unavailable,
        )


def test_case_rejects_preclose_decision_boundary_and_tampered_surface():
    market = _market()
    adapter = PositionalTimelineAdapter("tamper-case")
    timeline = MarketObservationTimeline.seal(adapter=adapter, market_history=market)
    preclose = adapter.key_for_position(market.index, 4, InformationPhase.BAR_PRE_CLOSE)
    surface = s4a.build_volatility_surface(timeline=timeline, adapter=adapter, market_history=market)

    with pytest.raises(TrajectoryCaseError, match="completed-row"):
        create_trajectory_decision_case(
            timeline=timeline,
            adapter=adapter,
            market_history=market,
            decision_key=preclose,
            surfaces=(surface,),
            parent_snapshot=None,
        )

    damaged = s4a.build_volatility_surface(timeline=timeline, adapter=adapter, market_history=market)
    first_output = damaged.output_columns[0]
    damaged.surface.loc[market.index[0], first_output] = float(damaged.surface.loc[market.index[0], first_output]) + 0.5
    with pytest.raises(Exception, match="self-integrity|hash|identity"):
        create_trajectory_decision_case(
            timeline=timeline,
            adapter=adapter,
            market_history=market,
            decision_key=adapter.key_for_position(
                market.index, 4, InformationPhase.COMPLETED_ROW_AVAILABLE
            ),
            surfaces=(damaged,),
            parent_snapshot=None,
        )


def test_case_is_deeply_immutable_and_does_not_hash_full_history_into_identity():
    case, _, _, _, _ = _build_case(_market())
    with pytest.raises(FrozenInstanceError):
        case.decision_prefix_hash = "0" * 64
    with pytest.raises(FrozenInstanceError):
        case.surface_prefix_bindings[0].prefix_hash = "0" * 64
    assert isinstance(case.surface_prefix_bindings, tuple)
