"""Comprehensive Zero-Lookahead & Causal Invariance Test Suite for SMC V4 & V5 Portfolios."""

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
    build_causal_swing_events,
    causal_atr14,
    detect_swings_causal,
    in_killzone_utc,
    load_asset_ohlcv,
    load_xauusd_1m,
    resample_causal_tf,
)
from engine.smc_v3_trend_engine import SMCV3Config, run_smc_v3_backtest  # noqa: E402
from engine.smc_v4_portfolio import (  # noqa: E402
    apply_cost_reprice,
    run_engine_ltf_1m,
    run_engine_sniper_htf,
    run_smc_v4_portfolio,
    run_smc_v5_portfolio,
    run_smc_v6_xau_portfolio,
    run_smc_v7_multiasset_portfolio,
    run_smc_v8_multiasset_portfolio,
    simulate_compounded_account,
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
    pd.testing.assert_frame_equal(tf_full.loc[tf_full.index <= cut], tf_pref.loc[tf_pref.index <= cut])


def test_detect_swings_causal_cannot_see_future_bars():
    idx = pd.date_range("2025-10-01 07:15", periods=10, freq="15min", tz="UTC")
    highs = np.array([10, 12, 15, 20, 14, 13, 12, 11, 10, 9], dtype=float)
    lows = np.array([8, 9, 10, 11, 10, 9, 8, 7, 6, 5], dtype=float)
    sw = detect_swings_causal(highs, lows, idx, k=3)
    for idx_early in range(6):
        assert all(sp.candle_idx != 3 for sp in sw.get(idx_early, []))
    assert any(sp.candle_idx == 3 and sp.kind == "high" and sp.price == 20.0 for sp in sw.get(6, []))


def test_causal_atr14_prefix_invariance():
    rng = np.random.default_rng(7)
    n = 100
    c = 4000.0 + np.cumsum(rng.normal(0, 1.5, n))
    h = c + rng.uniform(0.2, 2.0, n)
    l = c - rng.uniform(0.2, 2.0, n)
    np.testing.assert_allclose(causal_atr14(h, l, c)[:60], causal_atr14(h[:60], l[:60], c[:60]), equal_nan=True)


def test_htf_structure_and_1h_swing_events_prefix_invariance():
    df = _make_synthetic_1m(days=10)
    cut = pd.Timestamp("2025-10-06 14:17:00", tz="UTC")
    e4_full, t4_full = build_causal_htf_structure(df, "4h", swing_k=2)
    e4_pref, t4_pref = build_causal_htf_structure(df.loc[:cut], "4h", swing_k=2)
    assert np.array_equal(t4_full[e4_full <= cut], t4_pref[e4_pref <= cut])

    s1_t_full, s1_k_full, s1_p_full = build_causal_swing_events(df, "1h", 2)
    s1_t_pref, s1_k_pref, s1_p_pref = build_causal_swing_events(df.loc[:cut], "1h", 2)
    mask_f = s1_t_full <= cut
    mask_p = s1_t_pref <= cut
    assert list(s1_t_full[mask_f]) == list(s1_t_pref[mask_p])
    assert [k for k, m in zip(s1_k_full, mask_f) if m] == [k for k, m in zip(s1_k_pref, mask_p) if m]
    np.testing.assert_allclose(s1_p_full[mask_f], s1_p_pref[mask_p])


def test_killzone_utc_boundaries():
    assert in_killzone_utc(pd.Timestamp("2025-10-02 07:00", tz="UTC"))
    assert in_killzone_utc(pd.Timestamp("2025-10-02 10:59", tz="UTC"))
    assert not in_killzone_utc(pd.Timestamp("2025-10-02 11:00", tz="UTC"))
    assert in_killzone_utc(pd.Timestamp("2025-10-02 12:00", tz="UTC"))
    assert in_killzone_utc(pd.Timestamp("2025-10-02 16:59", tz="UTC"))
    assert not in_killzone_utc(pd.Timestamp("2025-10-02 17:00", tz="UTC"))


def _assert_prefix_invariant(full_trades: list[dict], pref_trades: list[dict], cut: pd.Timestamp) -> None:
    closed_pref = [t for t in pref_trades if t["outcome"] != "EOD"]
    closed_full = [t for t in full_trades if pd.Timestamp(t["exit_time"]) <= cut and t["outcome"] != "EOD"]
    assert closed_pref == closed_full

    eod_pref = [t for t in pref_trades if t["outcome"] == "EOD"]
    open_at_cut_full = [
        t for t in full_trades
        if pd.Timestamp(t["entry_time"]) <= cut < pd.Timestamp(t["exit_time"])
    ]
    assert len(eod_pref) == len(open_at_cut_full)
    keys = ("engine", "side", "setup_time", "entry_time", "entry_price", "sl_price", "tp_price", "risk_usd")
    for p, f in zip(eod_pref, open_at_cut_full):
        for k in keys:
            assert p[k] == f[k]


def test_smc_v4_and_v5_all_sleeves_prefix_invariance():
    df = _make_synthetic_1m(days=12)
    ev0 = pd.Timestamp("2025-10-05 00:00", tz="UTC")
    ev1 = pd.Timestamp("2025-10-12 23:59", tz="UTC")
    cut = pd.Timestamp("2025-10-09 13:45:00", tz="UTC")

    full_v4 = run_smc_v4_portfolio(df, ev0, ev1, cost=0.25, single_position_lock=False)
    pref_v4 = run_smc_v4_portfolio(df.loc[:cut], ev0, ev1, cost=0.25, single_position_lock=False)
    for sleeve in ("v3_ny", "vis_b", "vis_a", "combined"):
        _assert_prefix_invariant(full_v4[sleeve], pref_v4[sleeve], cut)

    full_v5 = run_smc_v5_portfolio(df, ev0, ev1, cost=0.25, single_position_lock=False)
    pref_v5 = run_smc_v5_portfolio(df.loc[:cut], ev0, ev1, cost=0.25, single_position_lock=False)
    for sleeve in ("v3_pro", "vis_b_pro", "vis_a", "amd_pro", "v5_unlocked"):
        _assert_prefix_invariant(full_v5[sleeve], pref_v5[sleeve], cut)

    full_ltf = run_engine_ltf_1m(df, ev0, ev1, cost=0.25)
    pref_ltf = run_engine_ltf_1m(df.loc[:cut], ev0, ev1, cost=0.25)
    _assert_prefix_invariant(full_ltf, pref_ltf, cut)


def test_real_data_slice_v4_and_v5_prefix_invariance_and_cost_reprice():
    data_dir = PKG_ROOT / "data" / "XAUUSD_1m_histdata"
    if not (data_dir / "2026-03.csv.gz").exists():
        pytest.skip("Real data archive not present")

    df = load_xauusd_1m(data_dir, ["2026-01", "2026-02", "2026-03", "2026-04"])
    ev0 = pd.Timestamp("2026-02-01 00:00", tz="UTC")
    ev1 = pd.Timestamp("2026-05-01 00:00", tz="UTC")
    cut = pd.Timestamp("2026-03-31 14:30:00", tz="UTC")

    full_v4 = run_smc_v4_portfolio(df, ev0, ev1, cost=0.25, single_position_lock=False)
    pref_v4 = run_smc_v4_portfolio(df.loc[:cut], ev0, ev1, cost=0.25, single_position_lock=False)
    for sleeve in ("v3_ny", "vis_b", "vis_a", "combined"):
        _assert_prefix_invariant(full_v4[sleeve], pref_v4[sleeve], cut)
    assert len(pref_v4["combined"]) > 0

    full_v6 = run_smc_v6_xau_portfolio(df, ev0, ev1, cost=0.25, single_position_lock=False)
    pref_v6 = run_smc_v6_xau_portfolio(df.loc[:cut], ev0, ev1, cost=0.25, single_position_lock=False)
    for sleeve in ("v3_pro", "vis_b_pro", "vis_a", "amd_pro", "ltf_1m", "v5_unlocked", "v6_unlocked"):
        _assert_prefix_invariant(full_v6[sleeve], pref_v6[sleeve], cut)
    assert len(pref_v6["ltf_1m"]) > 0
    assert len(pref_v6["v6_unlocked"]) > 0

    # Verify cost reprice matches full re-run at $0.35 identically
    full_v5_035 = run_smc_v5_portfolio(df, ev0, ev1, cost=0.35, single_position_lock=False)["v5_unlocked"]
    repriced_035 = apply_cost_reprice(full_v6["v5_unlocked"], 0.35)
    assert len(full_v5_035) == len(repriced_035)
    for a, b in zip(full_v5_035, repriced_035):
        assert a["entry_time"] == b["entry_time"]
        assert a["net_r"] == pytest.approx(b["net_r"], abs=1e-12)


def test_compounding_simulation_math():
    sample = [{"exit_time": "2025-01-01 12:00+00:00", "net_r": 2.0}, {"exit_time": "2025-01-02 12:00+00:00", "net_r": -1.0}]
    res = simulate_compounded_account(sample, start_capital=100.0, risk_pct=0.10, compound=True)
    # 100 -> +20% = 120 -> -10% of 120 = 108.0; peak=120, dd=12/120=10%
    assert res["final_equity"] == pytest.approx(108.0, abs=1e-6)
    assert res["max_dd_pct"] == pytest.approx(10.0, abs=1e-6)


def test_v7_sniper_and_multiasset_zero_lookahead_prefix_invariance():
    xau_dir = PKG_ROOT / "data" / "XAUUSD_1m_histdata"
    nsx_dir = PKG_ROOT / "data" / "NSXUSD_1m_histdata"
    btc_dir = PKG_ROOT / "data" / "BTCUSD_5m"
    if not ((xau_dir / "2026-03.csv.gz").exists() and (nsx_dir / "2026-03.csv.gz").exists() and (btc_dir / "2026.csv.gz").exists()):
        pytest.skip("Multi-asset archives not present")

    df_xau = load_asset_ohlcv(xau_dir, ["2026-01", "2026-02", "2026-03", "2026-04"])
    df_nsx = load_asset_ohlcv(nsx_dir, ["2026-01", "2026-02", "2026-03", "2026-04"])
    df_btc = load_asset_ohlcv(btc_dir, ["2025", "2026"])
    df_btc = df_btc.loc[df_btc.index <= pd.Timestamp("2026-05-01 00:00", tz="UTC")]

    ev0 = pd.Timestamp("2026-02-01 00:00", tz="UTC")
    ev1 = pd.Timestamp("2026-05-01 00:00", tz="UTC")
    cut = pd.Timestamp("2026-03-31 14:30:00", tz="UTC")

    full_x15 = run_engine_sniper_htf(
        df_xau, ev0, ev1, asset="XAUUSD", sweep_tf="15min", sweep_k=2, min_age=2, htf_mode="dual",
        min_risk_abs=2.0, min_risk_pct=0.0010, fixed_rr=None, trail_1h_after_r=4.0, be_lock_r=1.5,
        use_killzone=True, cost=0.25, engine_label="XAU_15m1m_Tr1H",
    )
    pref_x15 = run_engine_sniper_htf(
        df_xau.loc[:cut], ev0, ev1, asset="XAUUSD", sweep_tf="15min", sweep_k=2, min_age=2, htf_mode="dual",
        min_risk_abs=2.0, min_risk_pct=0.0010, fixed_rr=None, trail_1h_after_r=4.0, be_lock_r=1.5,
        use_killzone=True, cost=0.25, engine_label="XAU_15m1m_Tr1H",
    )
    _assert_prefix_invariant(full_x15, pref_x15, cut)

    full_btc = run_engine_sniper_htf(
        df_btc, ev0, ev1, asset="BTCUSD", sweep_tf="1h", sweep_k=3, min_age=4, htf_mode="dual",
        min_risk_abs=0.0, min_risk_pct=0.0020, fixed_rr=15.0, trail_1h_after_r=None,
        use_killzone=False, cost=0.0, pct_cost=0.0008, engine_label="BTC_1H5m_Dual15R",
    )
    pref_btc = run_engine_sniper_htf(
        df_btc.loc[:cut], ev0, ev1, asset="BTCUSD", sweep_tf="1h", sweep_k=3, min_age=4, htf_mode="dual",
        min_risk_abs=0.0, min_risk_pct=0.0020, fixed_rr=15.0, trail_1h_after_r=None,
        use_killzone=False, cost=0.0, pct_cost=0.0008, engine_label="BTC_1H5m_Dual15R",
    )
    _assert_prefix_invariant(full_btc, pref_btc, cut)

    full_v7 = run_smc_v7_multiasset_portfolio(df_xau, df_nsx, df_btc, ev0, ev1)
    assert len(full_v7["v7_global_1pos"]) > 0
    assert len(full_v7["v7_3asset_1pos_each"]) >= len(full_v7["v7_global_1pos"])
    assert {t["asset"] for t in full_v7["v7_3asset_1pos_each"]}.issubset({"XAUUSD", "NSXUSD", "BTCUSD"})


def test_v8_microscopy_and_ict_ob_zero_lookahead_prefix_invariance():
    xau_dir = PKG_ROOT / "data" / "XAUUSD_1m_histdata"
    nsx_dir = PKG_ROOT / "data" / "NSXUSD_1m_histdata"
    btc_dir = PKG_ROOT / "data" / "BTCUSD_5m"
    if not ((xau_dir / "2026-03.csv.gz").exists() and (nsx_dir / "2026-03.csv.gz").exists() and (btc_dir / "2026.csv.gz").exists()):
        pytest.skip("Multi-asset archives not present")

    df_xau = load_asset_ohlcv(xau_dir, ["2026-01", "2026-02", "2026-03", "2026-04"])
    df_nsx = load_asset_ohlcv(nsx_dir, ["2026-01", "2026-02", "2026-03", "2026-04"])
    df_btc = load_asset_ohlcv(btc_dir, ["2025", "2026"])
    df_btc = df_btc.loc[df_btc.index <= pd.Timestamp("2026-05-01 00:00", tz="UTC")]

    ev0 = pd.Timestamp("2026-02-01 00:00", tz="UTC")
    ev1 = pd.Timestamp("2026-05-01 00:00", tz="UTC")
    cut = pd.Timestamp("2026-03-31 14:30:00", tz="UTC")

    full_ob = run_engine_sniper_htf(
        df_xau, ev0, ev1, asset="XAUUSD", sweep_tf="15min", sweep_k=2, min_age=2, htf_mode="dual",
        min_risk_abs=2.0, min_risk_pct=0.0010, fixed_rr=None, trail_1h_after_r=4.0, be_lock_r=1.5,
        entry_mode="ob_overlap", require_cisd=True, use_killzone=True, cost=0.25, engine_label="XAU_OB",
    )
    pref_ob = run_engine_sniper_htf(
        df_xau.loc[:cut], ev0, ev1, asset="XAUUSD", sweep_tf="15min", sweep_k=2, min_age=2, htf_mode="dual",
        min_risk_abs=2.0, min_risk_pct=0.0010, fixed_rr=None, trail_1h_after_r=4.0, be_lock_r=1.5,
        entry_mode="ob_overlap", require_cisd=True, use_killzone=True, cost=0.25, engine_label="XAU_OB",
    )
    _assert_prefix_invariant(full_ob, pref_ob, cut)

    full_btc_be = run_engine_sniper_htf(
        df_btc, ev0, ev1, asset="BTCUSD", sweep_tf="1h", sweep_k=3, min_age=4, htf_mode="dual",
        min_risk_abs=0.0, min_risk_pct=0.0020, fixed_rr=15.0, trail_1h_after_r=None,
        be_act_r=3.0, be_lock_r=1.0, use_killzone=False, min_hour_utc=9, cost=0.0, pct_cost=0.0008, engine_label="BTC_15R_BE",
    )
    pref_btc_be = run_engine_sniper_htf(
        df_btc.loc[:cut], ev0, ev1, asset="BTCUSD", sweep_tf="1h", sweep_k=3, min_age=4, htf_mode="dual",
        min_risk_abs=0.0, min_risk_pct=0.0020, fixed_rr=15.0, trail_1h_after_r=None,
        be_act_r=3.0, be_lock_r=1.0, use_killzone=False, min_hour_utc=9, cost=0.0, pct_cost=0.0008, engine_label="BTC_15R_BE",
    )
    _assert_prefix_invariant(full_btc_be, pref_btc_be, cut)

    full_v8 = run_smc_v8_multiasset_portfolio(df_xau, df_nsx, df_btc, ev0, ev1)
    assert len(full_v8["v8_global_1pos"]) > 0
    assert len(full_v8["v8_3asset_1pos_each"]) >= len(full_v8["v8_global_1pos"])
    assert all(pd.Timestamp(t["entry_time"]).hour >= 9 for t in full_v8["btc_15r_be"])
    assert all(pd.Timestamp(t["entry_time"]).hour >= 9 for t in full_v8["nsx_1h_10r"])
