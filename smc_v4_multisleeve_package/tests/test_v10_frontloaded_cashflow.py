"""Comprehensive V10.0 Front-Loaded Cashflow, Topological Swings & Export Parity Tests."""

from __future__ import annotations

import importlib.util
import pathlib
import py_compile
import sys

import numpy as np
import pandas as pd

PKG = pathlib.Path(__file__).resolve().parents[1]
if str(PKG) not in sys.path:
    sys.path.insert(0, str(PKG))

from engine import (
    ProtectedSwingDetector,
    SmallAccountCashflowManager,
    TradePositionState,
    V10FrontLoadedCashflowExitManager,
    build_causal_topo_events,
    build_causal_topo_swing_dict,
    compute_atr_series,
    run_v10_btc_topo_sweeps_backtest,
    run_v10_multiasset_portfolio,
    run_v10_nsx_topo_backtest,
    run_v10_xau_topo_backtest,
)


def _make_synthetic_ohlcv(periods: int, freq: str, start: str = "2024-01-01", seed: int = 11) -> pd.DataFrame:
    idx = pd.date_range(start, periods=periods, freq=freq, tz="UTC")
    rng = np.random.default_rng(seed)
    rets = rng.normal(0.0001, 0.0020, size=periods)
    close = 50000.0 * np.exp(np.cumsum(rets))
    open_px = np.concatenate([[close[0]], close[:-1]])
    spread = np.abs(rng.normal(0.0012, 0.0006, size=periods)) * close
    high = np.maximum(open_px, close) + spread
    low = np.minimum(open_px, close) - spread
    vol = rng.uniform(50.0, 250.0, size=periods)
    return pd.DataFrame(
        {"Open": open_px, "High": high, "Low": low, "Close": close, "Volume": vol},
        index=idx,
    )


def test_causal_topo_swings_prefix_invariance() -> None:
    """Topological ATR-ZigZag swings (zero k=2/k=3) must be strictly causal under future bar mutation."""
    df = _make_synthetic_ohlcv(600, "1h", seed=42)
    cutoff = 300
    df_pre = df.iloc[:cutoff].copy()

    df_mut = df.copy()
    df_mut.iloc[cutoff:, df_mut.columns.get_loc("High")] += 15000.0
    df_mut.iloc[cutoff:, df_mut.columns.get_loc("Low")] -= 15000.0
    df_mut.iloc[cutoff:, df_mut.columns.get_loc("Close")] += 10000.0

    ev_pre = build_causal_topo_events(
        df_pre.index.as_unit("ns").asi8,
        df_pre["High"].to_numpy(float),
        df_pre["Low"].to_numpy(float),
        df_pre["Close"].to_numpy(float),
        compute_atr_series(df_pre["High"].to_numpy(float), df_pre["Low"].to_numpy(float), df_pre["Close"].to_numpy(float), 14),
        zig_mult=1.15,
    )
    ev_mut = build_causal_topo_events(
        df_mut.index.as_unit("ns").asi8,
        df_mut["High"].to_numpy(float),
        df_mut["Low"].to_numpy(float),
        df_mut["Close"].to_numpy(float),
        compute_atr_series(df_mut["High"].to_numpy(float), df_mut["Low"].to_numpy(float), df_mut["Close"].to_numpy(float), 14),
        zig_mult=1.15,
    )

    pre_flat = [(k, s.idx, s.side, round(s.price, 6)) for k, vs in sorted(ev_pre.items()) for s in vs]
    mut_flat = [(k, s.idx, s.side, round(s.price, 6)) for k, vs in sorted(ev_mut.items()) if k < cutoff for s in vs]
    assert len(pre_flat) > 5
    assert pre_flat == mut_flat

    sd_pre = build_causal_topo_swing_dict(df_pre, zig_mult=1.15)
    assert len(sd_pre) == len(ev_pre)


def test_v10_frontloaded_45_40_15_cascade_and_origin_anchor() -> None:
    """Verify V10FrontLoadedCashflowExitManager 45% @ 2.2R -> +0.35R, 40% @ 4.5R -> +2.0R, 15% @ 10R."""
    mgr = V10FrontLoadedCashflowExitManager()
    assert mgr.bank_r == 2.2 and mgr.bank_frac == 0.45 and mgr.be_lock_r == 0.35
    assert mgr.bank2_r == 4.5 and mgr.bank2_frac == 0.40 and mgr.be2_lock_r == 2.00
    assert mgr.runner_tp_r == 10.0

    pos = TradePositionState(
        trade_id=101,
        side=1,
        entry_bar=10,
        entry_ts=pd.Timestamp("2025-05-01 12:00", tz="UTC"),
        entry_price=100.0,
        init_sl=99.0,
        cur_sl=99.0,
        risk_dist=1.0,
    )
    prot = ProtectedSwingDetector()
    assert not mgr.is_zero_risk(pos)

    # Tier 1 hit at +2.25R -> banks 45%, moves SL to 100.35, frees risk slot
    closed, _, note1 = mgr.step_bar(pos, 11, 102.25, 100.1, 102.0, 0.4, prot)
    assert not closed and note1 == "BANKED_T1"
    assert abs(pos.qty_rem - 0.55) < 1e-6
    assert abs(pos.cur_sl - 100.35) < 1e-6
    assert mgr.is_zero_risk(pos)

    # Tier 2 hit at Origin_Anchor (+4.3R < 4.5R) -> banks 40%, moves SL to +2.0R
    closed, _, note2 = mgr.step_bar(pos, 12, 104.35, 101.8, 104.1, 0.4, prot, target_px=104.3)
    assert not closed and note2 == "BANKED_T2_ORIGIN"
    assert abs(pos.qty_rem - 0.15) < 1e-6
    assert abs(pos.cur_sl - 102.0) < 1e-6

    # Tier 3 hits +10.0R moonbag TP
    closed, gross_r, note3 = mgr.step_bar(pos, 13, 110.1, 104.0, 110.0, 0.4, prot, target_px=104.3)
    assert closed and note3 == "VACUUM_TP"
    expected = 0.45 * 2.2 + 0.40 * 4.3 + 0.15 * 10.0
    assert abs(gross_r - expected) < 1e-5


def test_v10_daily_hunter_and_turbo_sniper_profiles() -> None:
    """Verify DAILY_HUNTER_$100 (3.0%/4.5%, -2.0R CB, $25 skim) & TURBO_SNIPER_$100 (4.0%/5.5%, -2.5R CB, $20 skim)."""
    dh = SmallAccountCashflowManager.daily_hunter_100()
    ts = SmallAccountCashflowManager.turbo_sniper_100()

    assert dh.risk_pct == 0.030 and dh.aplus_risk_pct == 0.045 and dh.throttle_risk_pct == 0.020
    assert dh.max_concurrent_risk_slots == 4 and dh.daily_dd_cap_r == -2.0 and dh.skim_step_usd == 25.0
    assert ts.risk_pct == 0.040 and ts.aplus_risk_pct == 0.055 and ts.throttle_risk_pct == 0.025
    assert ts.max_concurrent_risk_slots == 4 and ts.daily_dd_cap_r == -2.5 and ts.skim_step_usd == 20.0

    t0 = pd.Timestamp("2025-06-01 08:00", tz="UTC")
    trades = [
        {"entry_time": t0, "t1_time": t0 + pd.Timedelta(hours=1), "exit_time": t0 + pd.Timedelta(hours=4), "sl_pct": 0.01, "net_r": 4.0, "setup": "V10_XAU_VisB", "side": 1, "asset": "XAUUSD"},
        {"entry_time": t0 + pd.Timedelta(hours=6), "t1_time": t0 + pd.Timedelta(hours=7), "exit_time": t0 + pd.Timedelta(hours=9), "sl_pct": 0.01, "net_r": 4.0, "setup": "V10_CompVac", "side": 1, "asset": "BTCUSD"},
        # Next day: two -1.0R losses hit -2.0R DAILY_HUNTER CB and block 3rd same-day trade
        {"entry_time": t0 + pd.Timedelta(days=1), "exit_time": t0 + pd.Timedelta(days=1, hours=1), "sl_pct": 0.01, "net_r": -1.0, "setup": "V10_LON", "side": -1, "asset": "BTCUSD"},
        {"entry_time": t0 + pd.Timedelta(days=1, hours=2), "exit_time": t0 + pd.Timedelta(days=1, hours=3), "sl_pct": 0.01, "net_r": -1.0, "setup": "V10_1H_TOPO", "side": -1, "asset": "BTCUSD"},
        {"entry_time": t0 + pd.Timedelta(days=1, hours=4), "exit_time": t0 + pd.Timedelta(days=1, hours=5), "sl_pct": 0.01, "net_r": -1.0, "setup": "V10_15M_TOPO", "side": -1, "asset": "BTCUSD"},
    ]
    res_dh = dh.simulate_cashflow(trades, mode="ratchet_cashflow", basket_mult=1.0)
    assert res_dh["skipped_circuit"] == 1
    assert res_dh["withdrawn_vault_usd"] > 0.0

    res_ts = ts.simulate_cashflow(trades, mode="ratchet_cashflow", basket_mult=1.0)
    assert res_ts["skipped_circuit"] == 0  # -2.5R CB lets 3rd -1.0R run before tripping
    assert res_ts["withdrawn_vault_usd"] > res_dh["withdrawn_vault_usd"]


def test_v10_engines_and_exports_smoke() -> None:
    """Smoke-test all V10 backtest runners and verify zero-dep & QuantConnect export compilation + tracker."""
    df_btc = _make_synthetic_ohlcv(4000, "5min", start="2024-01-01", seed=9)
    df_xau = _make_synthetic_ohlcv(8000, "1min", start="2024-01-01", seed=13)
    df_nsx = _make_synthetic_ohlcv(2500, "5min", start="2024-01-01", seed=17)
    t0 = pd.Timestamp("2024-01-05", tz="UTC")
    t1 = pd.Timestamp("2024-01-20", tz="UTC")

    tr_sw, sm_sw = run_v10_btc_topo_sweeps_backtest(df_btc, t0, t1)
    assert isinstance(tr_sw, list) and "all" in sm_sw

    tr_xau, sm_xau = run_v10_xau_topo_backtest(df_xau, t0, t1)
    assert isinstance(tr_xau, list) and "all" in sm_xau

    tr_nsx, sm_nsx = run_v10_nsx_topo_backtest(df_nsx, t0, t1)
    assert isinstance(tr_nsx, list) and "all" in sm_nsx

    port = run_v10_multiasset_portfolio(df_btc, df_xau, df_nsx, t0, t1)
    assert "real_multiasset_summary" in port and "btc_summary" in port

    qc_path = PKG / "exports" / "quantconnect" / "BinanceFutures_MultiCoin_Scalper_QC.py"
    bn_path = PKG / "exports" / "binance" / "binance_futures_scalper.py"
    py_compile.compile(str(qc_path), doraise=True)
    py_compile.compile(str(bn_path), doraise=True)

    spec = importlib.util.spec_from_file_location("binance_futures_scalper_v10", str(bn_path))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    tr = mod.CausalTopoSwingTracker(1.15)
    for i in range(30):
        px = 100.0 + (i % 6) * 2.0
        tr.update(px + 1.0, px - 1.0, px, 1.0)
    assert tr.bar_idx == 29
