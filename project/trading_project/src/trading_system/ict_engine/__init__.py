"""Deterministic, card-grounded ICT reading engine.

Stage M0 contains only the bounded EURUSD data loader and causal-test contract.
Recognizers and narrative output deliberately do not exist yet.
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
