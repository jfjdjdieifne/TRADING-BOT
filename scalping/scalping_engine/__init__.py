"""scalping_engine - causal 1m/5m SMC scalping engine (order blocks, liquidity
sweeps, FVG, displacement, VWAP, candlestick confirmation).

Strictly zero-lookahead: every value used to decide at bar `t` is derived only
from bars `<= t` (closed). See README.md for the honesty section.
"""

from .primitives import (
    wilder_atr,
    swing_points,
    SwingState,
    order_blocks,
    fair_value_gaps,
    displacement,
    candle_patterns,
    session_vwap,
    sweep_events,
)
from .engine import ScalpingEngine, Trade, EngineConfig
from .metrics import compute_metrics

__all__ = [
    "wilder_atr",
    "swing_points",
    "SwingState",
    "order_blocks",
    "fair_value_gaps",
    "displacement",
    "candle_patterns",
    "session_vwap",
    "sweep_events",
    "ScalpingEngine",
    "Trade",
    "EngineConfig",
    "compute_metrics",
]
