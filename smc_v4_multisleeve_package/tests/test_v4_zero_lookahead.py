"""Comprehensive Zero-Lookahead & Causal Invariance Test Suite for SMC V4 Multi-Sleeve."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PKG_ROOT = Path(__file__).resolve().parents[1]
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from engine.causal_primitives import (  # noqa: E402
    build_causal_htf_structure,
    causal_atr14,
    detect_swings_causal,
    in_killzone_utc,
    load_xauusd_1m,
    resample_causal_tf,
)
from engine.smc_v3_trend_engine import SMCV3Config, run_smc_v3_backtest  # noqa: E402
from engine.smc_v4_portfolio import (  # noqa: E402
    apply_cost_reprice,
    run_smc_v4_portfolio,
)


def _make_synthetic_1m(days: int = 12) -> pd.DataFrame:
    idx = pd.date_range("2025-10-01 00:00", periods=days * 1440, freq="1min", tz="UTC")
    t_hr = np.arange(len(idx)) / 60.0
    base = 4000.0 + 0.45 * t_hr + 9.0 * np.sin(t_hr / 2.2) + 2.5 * np.cos(t_hr * 1.4)
    return pd.DataFrame(
        {
            "Open": base,
            "High": base + 0.65,
            "Low": base - 0.65,
            "Close": base + 0.12,
            "Volume": np.zeros(len(idx)),
        },
        index=idx,
    )


def test_resample_causal_end_time_and_prefix_invariance():
    df = _make_synthetic_1m(days=2)
    cut = pd.Timestamp("2025-10-01 13:22:00", tz="UTC")
    tf_full = resample_causal_tf(df, "15m")
    tf_pref = resample_causal_tf(df.loc[:cut], "15m")

    # Completed 15m bars ending <= cut must be identical
    closed_full = tf_full.loc[tf_full.index <= cut]
    closed_pref = tf_pref.loc[tf_pref.index <= cut]
    pd.testing.assert_frame_equal(closed_full, closed_pref)


def test_detect_swings_causal_cannot_see_future_bars():
    idx = pd.date_range("2025-10-01 07:15", periods=10, freq="15min", tz="UTC")
    highs = np.array([10, 12, 15, 20, 14, 13, 12, 11, 10, 9], dtype=float)
    lows = np.array([8, 9, 10, 11, 10, 9, 8, 7, 6, 5], dtype=float)
    sw = detect_swings_causal(highs, lows, idx, k=3)
    # Pivot at index 3 (price=20) MUST NOT appear before confirm_idx = 3 + 3 = 6
    for idx_early in range(6):
        assert all(sp.candle_idx != 3 for sp in sw.get(idx_early, []))
    assert any(sp.candle_idx == 3 and sp.kind == "high" and sp.price == 20.0 for sp in sw.get(6, []))


def test_causal_atr14_prefix_invariance():
    rng = np.random.default_rng(7)
    n = 100
    c = 4000.0 + np.cumsum(rng.normal(0, 1.5, n))
    h = c + rng.uniform(0.2, 2.0, n)
    l = c - rng.uniform(0.2, 2.0, n)
    atr_full = causal_atr14(h, l, c)
    atr_pref = causal_atr14(h[:60], l[:60], c[:60])
    np.testing.assert_allclose(atr_full[:60], atr_pref, equal_nan=True)


def test_htf_structure_prefix_invariance():
    df = _make_synthetic_1m(days=10)
    cut = pd.Timestamp("2025-10-06 14:17:00", tz="UTC")
    e4_full, t4_full = build_causal_htf_structure(df, "4h", swing_k=2)
    e4_pref, t4_pref = build_causal_htf_structure(df.loc[:cut], "4h", swing_k=2)
    assert np.array_equal(t4_full[e4_full <= cut], t4_pref[e4_pref <= cut])


def test_killzone_utc_boundaries():
    assert in_killzone_utc(pd.Timestamp("2025-10-02 07:00", tz="UTC"))
    assert in_killzone_utc(pd.Timestamp("2025-10-02 10:59", tz="UTC"))
    assert not in_killzone_utc(pd.Timestamp("2025-10-02 11:00", tz="UTC"))
    assert in_killzone_utc(pd.Timestamp("2025-10-02 12:00", tz="UTC"))
    assert in_killzone_utc(pd.Timestamp("2025-10-02 16:59", tz="UTC"))
    assert not in_killzone_utc(pd.Timestamp("2025-10-02 17:00", tz="UTC"))


def test_smc_v4_all_three_sleeves_prefix_invariance():
    df = _make_synthetic_1m(days=12)
    ev0 = pd.Timestamp("2025-10-05 00:00", tz="UTC")
    ev1 = pd.Timestamp("2025-10-12 23:59", tz="UTC")
    cut = pd.Timestamp("2025-10-09 13:45:00", tz="UTC")

    full = run_smc_v4_portfolio(df, ev0, ev1, cost=0.25, single_position_lock=False)
    pref = run_smc_v4_portfolio(df.loc[:cut], ev0, ev1, cost=0.25, single_position_lock=False)

    for sleeve in ("v3_ny", "vis_b", "vis_a", "combined"):
        full_closed = [t for t in full[sleeve] if pd.Timestamp(t["exit_time"]) <= cut]
        assert pref[sleeve] == full_closed


def test_real_data_slice_prefix_invariance_and_cost_reprice():
    data_dir = PKG_ROOT / "data" / "XAUUSD_1m_histdata"
    if not (data_dir / "2026-03.csv.gz").exists():
        pytest.skip("Real data archive not present")

    df = load_xauusd_1m(data_dir, ["2026-01", "2026-02", "2026-03", "2026-04"])
    ev0 = pd.Timestamp("2026-02-01 00:00", tz="UTC")
    ev1 = pd.Timestamp("2026-05-01 00:00", tz="UTC")
    cut = pd.Timestamp("2026-03-31 14:30:00", tz="UTC")

    full = run_smc_v4_portfolio(df, ev0, ev1, cost=0.25, single_position_lock=False)
    pref = run_smc_v4_portfolio(df.loc[:cut], ev0, ev1, cost=0.25, single_position_lock=False)

    for sleeve in ("v3_ny", "vis_b", "vis_a", "combined"):
        full_closed = [t for t in full[sleeve] if pd.Timestamp(t["exit_time"]) <= cut]
        assert pref[sleeve] == full_closed
    assert len(pref["combined"]) > 0

    # Verify cost reprice matches full re-run at $0.35 and $0.50 identically
    full_035 = run_smc_v4_portfolio(df, ev0, ev1, cost=0.35, single_position_lock=False)["combined"]
    repriced_035 = apply_cost_reprice(full["combined"], 0.35)
    assert len(full_035) == len(repriced_035)
    for a, b in zip(full_035, repriced_035):
        assert a["entry_time"] == b["entry_time"]
        assert a["net_r"] == pytest.approx(b["net_r"], abs=1e-12)
