"""Causal tests for the V9 dynamic-profile research layer."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

PKG_ROOT = Path(__file__).resolve().parents[1]
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from engine.dynamic_profile import (  # noqa: E402
    Bar,
    Direction,
    DynamicProfileConfig,
    DynamicProfileEngine,
    FlowStatus,
    FundingStatus,
    LiquiditySweep,
    Profile,
    ProfileDecision,
    StrategyInputError,
    WaveMetrics,
    adaptive_displacement_index,
    choose_profile,
    protected_momentum_stop,
    spot_cvd_delta_from_binance_kline,
    tighten_stop,
    volume_zscore,
)


def _bar(i: int, o: float, h: float, l: float, c: float, v: float = 1.0, cvd: float | None = 1.0) -> Bar:
    return Bar(i, o, h, l, c, v, timestamp=i, spot_cvd_delta=cvd)


def _bullish_break_bars(current_volume: float = 10.0, current_cvd: float | None = 1.0) -> list[Bar]:
    # With k=1, the high at 1 is confirmed on 2 and the low at 3 is confirmed
    # on 4.  Bar 5 then closes with its whole body above the confirmed high.
    return [
        _bar(0, 10.0, 10.3, 9.9, 10.1),
        _bar(1, 12.0, 12.3, 11.9, 12.2),
        _bar(2, 11.0, 11.4, 10.8, 11.1),
        _bar(3, 8.1, 8.3, 7.9, 8.1),
        _bar(4, 8.3, 8.5, 8.1, 8.4),
        _bar(5, 49.0, 50.0, 48.5, 50.0, current_volume, current_cvd),
    ]


def test_zscore_is_read_before_push_and_uses_only_prior_history():
    prior = [1.0] * 100
    assert volume_zscore(1.0, prior) == 0.0
    assert math.isinf(volume_zscore(10.0, prior))
    # Including the current spike in the reference window would hide the
    # anomaly; this test prevents that regression.
    included_current = volume_zscore(10.0, prior + [10.0])
    assert included_current is not None and included_current < volume_zscore(10.0, prior)
    assert volume_zscore(10.0, prior, lookback=101, minimum_history=101) is None


def test_adi_and_protected_stop_follow_the_declared_formulas():
    assert adaptive_displacement_index(98.0, 102.0, 2, 1.0, Direction.LONG) == pytest.approx(2.0)
    assert adaptive_displacement_index(102.0, 98.0, 2, 1.0, Direction.SHORT) == pytest.approx(2.0)
    assert adaptive_displacement_index(98.0, 97.0, 2, 1.0, Direction.LONG) == 0.0
    assert adaptive_displacement_index(98.0, 102.0, 2, 0.0, Direction.LONG) is None

    impulse = _bar(0, 100.0, 105.0, 98.1, 104.0)
    assert protected_momentum_stop(Direction.LONG, impulse, 0.01) == pytest.approx(98.09)
    assert protected_momentum_stop(Direction.SHORT, impulse, 0.01) == pytest.approx(105.01)


def test_profile_switch_is_hard_gated_by_spot_flow_and_divergence():
    cfg = DynamicProfileConfig()
    metrics = WaveMetrics(98.0, 112.0, 4, 1.0, 3.8, 3.5)

    good = choose_profile(metrics=metrics, flow_status=FlowStatus.VALID, config=cfg)
    assert good.profile is Profile.AGGRESSIVE
    assert good.allow_shallow_fvg

    unknown = choose_profile(metrics=metrics, flow_status=FlowStatus.UNKNOWN, config=cfg)
    assert unknown.profile is Profile.DEFENSIVE
    assert not unknown.allow_shallow_fvg

    divergent = choose_profile(metrics=metrics, flow_status=FlowStatus.DIVERGENT, config=cfg)
    assert divergent.profile is Profile.DEFENSIVE
    assert "DIVERGENCE" in divergent.reason

    hot = choose_profile(
        metrics=metrics,
        flow_status=FlowStatus.VALID,
        config=DynamicProfileConfig(require_cool_funding=True),
        funding_status=FundingStatus.HOT,
    )
    assert hot.profile is Profile.DEFENSIVE
    assert hot.funding_status is FundingStatus.HOT
    assert "FUNDING" in hot.reason


def test_binance_spot_delta_is_executed_flow_not_ohlcv_price_proxy():
    assert spot_cvd_delta_from_binance_kline(100.0, 60.0) == pytest.approx(20.0)
    assert spot_cvd_delta_from_binance_kline(100.0, 40.0) == pytest.approx(-20.0)
    with pytest.raises(StrategyInputError):
        spot_cvd_delta_from_binance_kline(10.0, 11.0)


def test_scanner_confirms_body_break_and_aggressive_profile_without_future_data():
    cfg = DynamicProfileConfig(volume_lookback=3, minimum_volume_history=3, atr_period=2, swing_k=1, cvd_lookback=3)
    full = DynamicProfileEngine(cfg)
    evaluations = full.scan(_bullish_break_bars())
    last = evaluations[-1]

    assert last.structure.event == "BOS_UP"
    assert last.structure.direction is Direction.LONG
    assert last.fvg is not None
    assert last.fvg.direction is Direction.LONG
    assert last.fvg.low == pytest.approx(8.3)
    assert last.fvg.high == pytest.approx(48.5)
    assert last.decision.profile is Profile.AGGRESSIVE
    assert last.decision.flow_status is FlowStatus.VALID
    assert last.decision.allow_shallow_fvg
    assert last.wave.adi is not None and last.wave.adi > cfg.adi_threshold
    assert last.volume_z is not None and last.volume_z > cfg.volume_z_threshold

    # A prefix run cannot acquire information from the bars after its cut.
    prefix = DynamicProfileEngine(cfg).scan(_bullish_break_bars()[:-1])
    assert len(prefix) == len(evaluations) - 1
    for a, b in zip(prefix, evaluations[:-1]):
        assert (a.structure.event, a.decision.profile, a.volume_z) == (b.structure.event, b.decision.profile, b.volume_z)
        assert a.wave.adi == b.wave.adi


def test_negative_cvd_divergence_cancels_aggressive_attack():
    cfg = DynamicProfileConfig(volume_lookback=3, minimum_volume_history=3, atr_period=2, swing_k=1, cvd_lookback=3)
    evaluations = DynamicProfileEngine(cfg).scan(_bullish_break_bars(current_cvd=-10.0))
    last = evaluations[-1]
    assert last.structure.event == "BOS_UP"
    assert last.decision.flow_status is FlowStatus.DIVERGENT
    assert last.decision.profile is Profile.DEFENSIVE
    assert not last.decision.allow_shallow_fvg
    assert last.plan is None


def test_countertrend_choch_requires_explicit_sweep_flow_speed_and_distance():
    cfg = DynamicProfileConfig(
        volume_lookback=3,
        minimum_volume_history=3,
        atr_period=2,
        swing_k=1,
        cvd_lookback=3,
        speed_lookback_bars=6,
    )
    engine = DynamicProfileEngine(cfg)
    bars = [
        _bar(0, 9.5, 10.0, 9.0, 9.4),
        _bar(1, 11.5, 12.0, 11.0, 11.8),
        _bar(2, 11.0, 11.5, 10.5, 11.1),
        _bar(3, 10.0, 10.8, 9.5, 9.7),
        _bar(4, 8.5, 10.0, 8.0, 8.6),
        _bar(5, 8.2, 9.0, 8.2, 8.7),
        _bar(6, 7.8, 8.0, 6.8, 7.5),  # BOS_DOWN below the confirmed low
    ]
    first = engine.scan(bars)
    assert first[-1].structure.event == "BOS_DOWN"
    engine.register_htf_sweep(LiquiditySweep(6, Direction.LONG, swept_level=8.0, extreme=6.8))

    engine.update(_bar(7, 7.3, 8.5, 7.2, 7.9, 1.0, 1.0))
    engine.update(_bar(8, 7.8, 8.4, 7.0, 8.3, 1.0, 1.0))
    choch = engine.update(_bar(9, 9.0, 11.5, 9.0, 11.0, 10.0, 1.0))

    assert choch.structure.event == "CHOCH_UP"
    assert choch.choch is not None
    assert choch.choch.valid
    assert choch.choch.flow_status is FlowStatus.VALID
    assert choch.choch.speed_ratio is not None and choch.choch.speed_ratio >= 2.0
    assert choch.choch.distance_atr is not None and choch.choch.distance_atr > 1.0


def test_trailing_stop_is_monotonic_and_never_crosses_market():
    assert tighten_stop(Direction.LONG, 98.0, 99.0, 100.0) == 99.0
    assert tighten_stop(Direction.LONG, 99.0, 98.0, 100.0) == 99.0
    assert tighten_stop(Direction.LONG, 99.0, 105.0, 100.0) == 100.0
    assert tighten_stop(Direction.SHORT, 102.0, 101.0, 100.0) == 101.0
    assert tighten_stop(Direction.SHORT, 101.0, 102.0, 100.0) == 101.0
    assert tighten_stop(Direction.SHORT, 101.0, 95.0, 100.0) == 100.0
