"""Parallel break-even doctrines; management states only, never PnL scoring."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

OBJECTIVE_TRIGGER = Decimal("0.75")


class BreakEvenVariant(str, Enum):
    AFTER_FIRST_PROFIT = "after_first_profit"
    AT_75_PERCENT_OBJECTIVE = "at_75_percent_objective"
    LONDON_ELIGIBILITY_ONLY = "london_eligibility_only"
    HIGHER_TIMEFRAME_RESIST = "higher_timeframe_resist"
    NO_RUSH_TRIGGER_WAITING = "no_rush_trigger_waiting"


class ManagementAction(str, Enum):
    MOVE_TO_BREAK_EVEN = "move_to_break_even"
    DO_NOT_MOVE = "do_not_move"
    ELIGIBLE_BUT_TRIGGER_SEPARATE = "eligible_but_trigger_separate"
    WAITING = "waiting"


@dataclass(frozen=True, slots=True)
class BreakEvenContext:
    first_profit_taken: bool
    objective_progress: Decimal | None
    london_active: bool
    long_term: bool


@dataclass(frozen=True, slots=True)
class BreakEvenState:
    variant: BreakEvenVariant
    action: ManagementAction
    claim_ids: tuple[str, ...]


def objective_progress(entry: float, objective: float, current: float) -> Decimal | None:
    """Exact decimal progress toward either an upward or downward objective."""

    entry_decimal, objective_decimal, current_decimal = (
        Decimal(str(value)) for value in (entry, objective, current)
    )
    if objective_decimal == entry_decimal:
        return None
    return (current_decimal - entry_decimal) / (objective_decimal - entry_decimal)


def break_even_states(context: BreakEvenContext) -> tuple[BreakEvenState, ...]:
    """Return every card alternative; no variant is selected or merged."""

    return (
        BreakEvenState(
            BreakEvenVariant.AFTER_FIRST_PROFIT,
            ManagementAction.MOVE_TO_BREAK_EVEN
            if context.first_profit_taken
            else ManagementAction.DO_NOT_MOVE,
            ("U0115",),
        ),
        BreakEvenState(
            BreakEvenVariant.AT_75_PERCENT_OBJECTIVE,
            ManagementAction.WAITING
            if context.objective_progress is None
            else ManagementAction.MOVE_TO_BREAK_EVEN
            if context.objective_progress >= OBJECTIVE_TRIGGER
            else ManagementAction.DO_NOT_MOVE,
            ("U0116",),
        ),
        BreakEvenState(
            BreakEvenVariant.LONDON_ELIGIBILITY_ONLY,
            ManagementAction.ELIGIBLE_BUT_TRIGGER_SEPARATE
            if context.london_active
            else ManagementAction.DO_NOT_MOVE,
            ("U0117",),
        ),
        BreakEvenState(
            BreakEvenVariant.HIGHER_TIMEFRAME_RESIST,
            ManagementAction.DO_NOT_MOVE
            if context.long_term
            else ManagementAction.WAITING,
            ("U0113", "U0114"),
        ),
        BreakEvenState(
            BreakEvenVariant.NO_RUSH_TRIGGER_WAITING,
            ManagementAction.WAITING,
            ("U0118",),
        ),
    )
