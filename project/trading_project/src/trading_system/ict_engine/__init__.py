"""Deterministic, card-grounded ICT reading engine.

The bounded data loader, causal market/filler status, and prefix-invariance
contract are shared infrastructure. Recognizers and narrative output are added
only at their approved milestones.
"""

from .causal import PrefixInvarianceError, assert_prefix_invariance
from .data import (
    ALLOWED_YEARS,
    BAR_WIDTH,
    DATA_CUTOFF,
    Candle,
    CandleBatch,
    DataValidationError,
    load_eurusd_5m,
    parse_eurusd_5m,
)

__all__ = [
    "ALLOWED_YEARS",
    "BAR_WIDTH",
    "DATA_CUTOFF",
    "Candle",
    "CandleBatch",
    "DataValidationError",
    "PrefixInvarianceError",
    "assert_prefix_invariance",
    "load_eurusd_5m",
    "parse_eurusd_5m",
]
