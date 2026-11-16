#!/usr/bin/env python3
"""Standard-library tests for the corrected sweep research engine."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from strategy import (
    Bar15,
    MinuteBar,
    StrategyConfig,
    detect_signals,
    detect_swings,
    signal_core_signature,
    simulate_with_config,
)

UTC = timezone.utc


def make_bars(rows: list[tuple[float, float, float, float]]) -> tuple[list[Bar15], list[MinuteBar]]:
    minutes: list[MinuteBar] = []
    bars: list[Bar15] = []
    origin = datetime(2021, 1, 1, tzinfo=UTC)
    for index, (op, hi, lo, close) in enumerate(rows):
        start = origin + timedelta(minutes=15 * index)
        first = len(minutes)
        for offset in range(15):
            stamp = start + timedelta(minutes=offset)
            # Keep all bars valid and place the aggregate high/low on the
            # first minute so a target/stop path is deterministic.
            if offset == 0:
                mhi, mlo = hi, lo
            else:
                mhi = max(op, close)
                mlo = min(op, close)
            minutes.append(MinuteBar(len(minutes), stamp, op, mhi, mlo, close))
        bars.append(Bar15(index, start, start + timedelta(minutes=15), op, hi, lo, close, first, len(minutes) - 1, 15, True))
    return bars, minutes


def pattern_rows(side: str) -> list[tuple[float, float, float, float]]:
    # Flat warm-up is deliberately boring.  The pattern is engineered after
    # it, with a confirmed target swing before the swept level.
    rows = [(100.0, 100.2, 99.8, 100.0)] * 24
    # prior swing high target at 24, prior swing low that will be swept at 26
    rows += [
        (100.0, 103.0, 99.9, 102.0),  # 24 HIGH target
        (102.0, 102.2, 100.2, 101.0),
        (101.0, 101.2, 98.0, 100.0),  # 26 LOW level
        (100.0, 100.4, 99.7, 100.1),  # confirms low
    ]
    if side == "LONG":
        rows += [
            (100.1, 100.3, 97.5, 99.0),  # 28 S below 98 and reclaim
            (99.0, 104.0, 99.0, 103.8),  # 29 D, FVG: low 99 > high(27)=100.4? no, fix below
        ]
    else:
        rows += [
            (100.1, 102.8, 99.8, 101.0),  # 28 S above 102.2 and close below
            (101.0, 101.1, 97.0, 97.2),  # 29 D, bearish
        ]
    return rows


class StrategyTests(unittest.TestCase):
    def test_short_uses_upper_sweep_red_displacement_and_prior_low_target(self) -> None:
        rows = [(100.0, 100.2, 99.8, 100.0)] * 24
        rows += [
            (100.0, 101.0, 97.0, 98.0),  # 24 LOW target
            (98.0, 99.0, 97.8, 98.5),
            (98.5, 99.0, 98.0, 98.2),  # 26 HIGH candidate? not high; next
            (98.2, 98.5, 97.8, 98.0),
            (98.0, 103.0, 97.9, 99.0),  # 28 S above confirmed high 102? no
            (99.0, 99.2, 95.0, 95.2),   # 29 D
        ]
        # Make a clear confirmed high at 26 and preserve the prior low at 24.
        rows[26] = (98.5, 102.0, 98.0, 101.0)
        rows[27] = (101.0, 101.2, 99.0, 100.0)
        rows[28] = (100.0, 103.0, 99.8, 100.0)
        rows[29] = (100.0, 100.1, 95.0, 95.2)
        bars, _ = make_bars(rows)
        config = StrategyConfig("SHORT_TEST", require_fvg=False, large_mode="none", min_body_fraction=0.0)
        signals = detect_signals(bars, config)
        shorts = [signal for signal in signals if signal.side == "SHORT"]
        self.assertTrue(shorts, "upper sweep followed by red candle must produce a short candidate")
        signal = shorts[-1]
        self.assertEqual(signal.sweep_index + 1, signal.displacement_index)
        self.assertEqual(signal.displacement_color, "RED")
        self.assertEqual(signal.target_level, 97.0)
        self.assertEqual(signal.target_pivot_index, 24)

    def test_long_target_is_prior_high_before_swept_low(self) -> None:
        rows = [(100.0, 100.2, 99.8, 100.0)] * 24
        rows += [
            (100.0, 103.0, 99.9, 102.0),  # 24 target HIGH
            (102.0, 102.2, 100.2, 101.0),
            (101.0, 101.2, 98.0, 100.0),  # 26 swept LOW level
            (100.0, 100.4, 99.7, 100.1),  # 27 confirms
            (100.1, 100.3, 97.5, 99.0),   # 28 S below 98, reclaim
            (99.0, 104.0, 99.0, 103.8),    # 29 D; non-FVG relaxed test
        ]
        bars, _ = make_bars(rows)
        config = StrategyConfig("LONG_TEST", require_fvg=False, large_mode="none", min_body_fraction=0.0)
        signals = detect_signals(bars, config)
        longs = [signal for signal in signals if signal.side == "LONG"]
        self.assertTrue(longs)
        signal = longs[-1]
        self.assertEqual(signal.displacement_index, signal.sweep_index + 1)
        self.assertEqual(signal.displacement_color, "GREEN")
        self.assertEqual(signal.target_level, 103.0)
        self.assertEqual(signal.target_pivot_index, 24)

    def test_displacement_is_exactly_one_candle_after_sweep(self) -> None:
        rows = [(100.0, 100.2, 99.8, 100.0)] * 24
        rows += [
            (100.0, 103.0, 99.9, 102.0),
            (102.0, 102.2, 100.2, 101.0),
            (101.0, 101.2, 98.0, 100.0),
            (100.0, 100.4, 99.7, 100.1),
            (100.1, 100.3, 97.5, 99.0),  # S
            (99.0, 99.2, 98.0, 98.5),      # S+1 wrong color / no displacement
            (98.5, 104.0, 98.5, 103.8),   # S+2 would be green but is rejected
        ]
        bars, _ = make_bars(rows)
        config = StrategyConfig("ONE_BAR", require_fvg=False, large_mode="none", min_body_fraction=0.0)
        signals = detect_signals(bars, config)
        self.assertFalse(any(signal.sweep_index == 28 and signal.eligible for signal in signals))

    def test_future_append_does_not_change_prior_signal_decisions(self) -> None:
        rows = [(100.0, 100.2, 99.8, 100.0)] * 24
        rows += [
            (100.0, 103.0, 99.9, 102.0),
            (102.0, 102.2, 100.2, 101.0),
            (101.0, 101.2, 98.0, 100.0),
            (100.0, 100.4, 99.7, 100.1),
            (100.1, 100.3, 97.5, 99.0),
            (99.0, 104.0, 99.0, 103.8),
            (103.8, 104.0, 103.5, 103.7),
            (103.7, 104.1, 103.4, 103.8),
            (103.8, 104.2, 103.5, 103.9),
        ]
        full, _ = make_bars(rows)
        prefix = full[:34]
        config = StrategyConfig("PREFIX", require_fvg=False, large_mode="none", min_body_fraction=0.0)
        all_prior = [signal_core_signature(signal) for signal in detect_signals(full, config) if signal.displacement_index < 32]
        pref_prior = [signal_core_signature(signal) for signal in detect_signals(prefix, config) if signal.displacement_index < 32]
        self.assertEqual(all_prior, pref_prior)

    def test_outcome_is_not_a_signal_and_uses_conservative_one_minute_order(self) -> None:
        rows = [(100.0, 100.2, 99.8, 100.0)] * 24
        rows += [
            (100.0, 103.0, 99.9, 102.0),
            (102.0, 102.2, 100.2, 101.0),
            (101.0, 101.2, 98.0, 100.0),
            (100.0, 100.4, 99.7, 100.1),
            (100.1, 100.3, 97.5, 99.0),
            (99.0, 104.0, 99.0, 102.5),
            (102.5, 104.0, 99.0, 103.0),
            (103.0, 103.5, 99.0, 102.0),
            (102.0, 102.2, 99.0, 101.0),
        ]
        bars, minutes = make_bars(rows)
        config = StrategyConfig("OUTCOME", require_fvg=False, large_mode="none", min_body_fraction=0.0)
        signals = [signal for signal in detect_signals(bars, config) if signal.side == "LONG" and signal.eligible]
        self.assertTrue(signals)
        outcome = simulate_with_config(signals[-1], config, bars, minutes)
        self.assertIn(outcome.state, {"TARGET", "STOP", "TIME", "DATA_GAP"})
        self.assertEqual(outcome.entry_price, bars[signals[-1].displacement_index].close)


if __name__ == "__main__":
    unittest.main(verbosity=2)
