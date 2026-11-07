from __future__ import annotations

from decimal import Decimal

import pytest

from trading_system.ict_engine.management import (
    BreakEvenContext,
    BreakEvenVariant,
    ManagementAction,
    break_even_states,
    objective_progress,
)
from trading_system.ict_engine.waiting import UNCARDED_CONCEPTS, WAITING_CONCEPTS


def test_every_break_even_variant_is_returned_without_selection() -> None:
    context = BreakEvenContext(True, Decimal("0.75"), True, True)
    states = {state.variant: state for state in break_even_states(context)}
    assert len(states) == 5
    assert states[BreakEvenVariant.AFTER_FIRST_PROFIT].action is ManagementAction.MOVE_TO_BREAK_EVEN
    assert states[BreakEvenVariant.AT_75_PERCENT_OBJECTIVE].action is ManagementAction.MOVE_TO_BREAK_EVEN
    assert states[BreakEvenVariant.LONDON_ELIGIBILITY_ONLY].action is ManagementAction.ELIGIBLE_BUT_TRIGGER_SEPARATE
    assert states[BreakEvenVariant.HIGHER_TIMEFRAME_RESIST].action is ManagementAction.DO_NOT_MOVE
    assert states[BreakEvenVariant.NO_RUSH_TRIGGER_WAITING].action is ManagementAction.WAITING
    assert break_even_states(context) == break_even_states(context)


def test_objective_progress_works_in_both_directions() -> None:
    upward = objective_progress(1.0, 1.2, 1.15)
    downward = objective_progress(1.2, 1.0, 1.05)
    assert upward == downward == Decimal("0.75")
    states = {state.variant: state for state in break_even_states(BreakEvenContext(False, upward, False, False))}
    assert states[BreakEvenVariant.AT_75_PERCENT_OBJECTIVE].action is ManagementAction.MOVE_TO_BREAK_EVEN
    assert objective_progress(1.0, 1.0, 1.1) is None


def test_all_46_exact_name_unmatched_concepts_and_doctrine_gaps_are_waiting() -> None:
    # gaps.md says 45; the mechanical 66-name vs 21-card comparison yields 46
    # because premium_discount is a combined card absent from kept_concepts.tsv.
    assert len(UNCARDED_CONCEPTS) == 46
    assert len(set(UNCARDED_CONCEPTS)) == 46
    waiting = {item.concept: item for item in WAITING_CONCEPTS}
    assert waiting["inversion_fair_value_gap_recognizer"].claim_ids == ("U0042",)
    assert waiting["order_block_full_qualification"].claim_ids == ("U0051",)
    assert waiting["carrying_charge_premium"].claim_ids == ("U0088",)
