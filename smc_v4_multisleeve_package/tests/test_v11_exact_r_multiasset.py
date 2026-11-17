"""Comprehensive V11.0 Institutional Exact-R Sizing, Session Equilibrium Scalp, & Multi-Asset Tests."""

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
    DrawdownSafeExactRManager,
    InstitutionalReferenceAndSwingEngine,
    ProtectedSwingDetector,
    ReferenceLevelSnapshot,
    SmallAccountCashflowManager,
    TradePositionState,
    V11SessionEquilibriumExitManager,
    run_v11_btc_portfolio,
    run_v11_multiasset_portfolio,
    run_v11_session_equilibrium_scalp,
)


def _make_synthetic_ohlcv(periods: int, freq: str, start: str = "2024-01-01", seed: int = 21) -> pd.DataFrame:
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


def test_v11_fee_inclusive_exact_1r_sizing_and_strict_aplus_gate() -> None:
    """Bug 1 fix: Notional = Risk_USD / (sl_pct + fee_rt_pct) guarantees stop-out loss <= -1.00R."""
    dh = SmallAccountCashflowManager.v11_daily_hunter_100()
    ts = SmallAccountCashflowManager.v11_turbo_sniper_100()

    assert dh.fee_inclusive and dh.strict_aplus_gate and dh.period_anchor == "month"
    assert dh.risk_pct == 0.030 and dh.aplus_risk_pct == 0.038 and dh.throttle_mult == 0.80
    assert dh.throttle_dd_pct == 0.15 and dh.daily_dd_cap_r == -2.0 and dh.skim_step_usd == 25.0
    assert ts.risk_pct == 0.036 and ts.aplus_risk_pct == 0.042 and ts.throttle_mult == 0.80

    # 1) Exact 1.0R fee-inclusive notional check: sl=0.40%, fee_rt=0.10% -> eff_stop=0.50%
    eff_risk_usd, notional = dh.compute_position_notional(100.0, 0.0040, risk_pct_override=0.030, fee_rt_pct=0.0010)
    assert abs(notional - (3.0 / 0.0050)) < 1e-6
    assert abs(eff_risk_usd - 3.0) < 1e-6
    # A full -1.0R stop + 0.10% round-trip fee costs: notional * (0.0040 + 0.0010) = $3.00 = -1.00R exact!
    dollar_loss_at_sl = notional * (0.0040 + 0.0010)
    assert abs(dollar_loss_at_sl - 3.0) < 1e-6

    # 2) Strict A+ gate: PF>2.0 sleeves get 3.8%, standard sleeves (V10_CompVac, V9_LON, NSX_AMD_1D) get 3.0%
    assert abs(dh.resolve_risk_pct(100.0, 100.0, {"setup": "SMC_Sweep_V6"}) - 0.038) < 1e-9
    assert abs(dh.resolve_risk_pct(100.0, 100.0, {"setup": "V11_SessEq_1H_TOPO"}) - 0.038) < 1e-9
    assert abs(dh.resolve_risk_pct(100.0, 100.0, {"setup": "V3_Pro_Clean"}) - 0.038) < 1e-9
    assert abs(dh.resolve_risk_pct(100.0, 100.0, {"setup": "V10_CompVac"}) - 0.030) < 1e-9
    assert abs(dh.resolve_risk_pct(100.0, 100.0, {"setup": "V9_LON"}) - 0.030) < 1e-9
    assert abs(dh.resolve_risk_pct(100.0, 100.0, {"setup": "NSX_AMD_1D"}) - 0.030) < 1e-9

    # 3) Smooth 0.80x throttle ONLY when DD > 15% from HWM (no abrupt collapse at 10%)
    assert abs(dh.resolve_risk_pct(88.0, 100.0, {"setup": "SMC_Sweep_V6"}) - 0.038) < 1e-9
    assert abs(dh.resolve_risk_pct(84.0, 100.0, {"setup": "SMC_Sweep_V6"}) - (0.038 * 0.80)) < 1e-9
    assert abs(dh.resolve_risk_pct(84.0, 100.0, {"setup": "V9_LON"}) - (0.030 * 0.80)) < 1e-9


def test_v11_zero_positive_r_negative_dollar_paradox() -> None:
    """Verify full stop-out hits never exceed -1.00R and monthly sized_r <=> pnl_usd has zero sign inversions."""
    dh = SmallAccountCashflowManager.v11_daily_hunter_100()
    t0 = pd.Timestamp("2025-03-01 08:00", tz="UTC")
    # Simulate tight-SL trades where unbuffered V10 would produce net_r = -1.25R..-1.50R
    trades = [
        {"entry_time": t0, "exit_time": t0 + pd.Timedelta(hours=1), "sl_pct": 0.0020, "gross_r": -1.0, "net_r": -1.50, "setup": "SMC_Sweep_V6", "side": 1, "asset": "BTCUSD"},
        {"entry_time": t0 + pd.Timedelta(days=1), "exit_time": t0 + pd.Timedelta(days=1, hours=2), "sl_pct": 0.0020, "gross_r": 2.1, "net_r": 1.60, "setup": "V9_LON", "side": 1, "asset": "BTCUSD"},
        {"entry_time": t0 + pd.Timedelta(days=32), "exit_time": t0 + pd.Timedelta(days=32, hours=1), "sl_pct": 0.0025, "gross_r": -1.0, "net_r": -1.40, "setup": "V10_CompVac", "side": -1, "asset": "BTCUSD"},
        {"entry_time": t0 + pd.Timedelta(days=33), "exit_time": t0 + pd.Timedelta(days=33, hours=3), "sl_pct": 0.0025, "gross_r": 3.5, "net_r": 3.10, "setup": "V11_SessEq_1H_TOPO", "side": 1, "asset": "BTCUSD"},
    ]
    audit = dh.simulate_granular_audit(trades, mode="ratchet_cashflow")
    s = audit["summary"]
    assert s["min_net_r"] >= -1.0001
    for m in audit["monthly"]:
        if m["sized_r"] > 0.01:
            assert m["pnl_usd"] > 0.0
        elif m["sized_r"] < -0.01:
            assert m["pnl_usd"] < 0.0


def test_v11_session_equilibrium_50_35_15_cascade() -> None:
    """Verify V11SessionEquilibriumExitManager 50% @ +1.8R -> BE+0.25R, 35% @ +3.2R -> +1.25R, 15% @ +6.5R."""
    mgr = V11SessionEquilibriumExitManager()
    assert mgr.bank_r == 1.8 and mgr.bank_frac == 0.50 and mgr.be_lock_r == 0.25
    assert mgr.bank2_r == 3.2 and mgr.bank2_frac == 0.35 and mgr.be2_lock_r == 1.25
    assert mgr.runner_tp_r == 6.5

    pos = TradePositionState(
        trade_id=202,
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

    closed, _, note1 = mgr.step_bar(pos, 11, 101.85, 99.8, 101.7, 0.4, prot)
    assert not closed and note1 == "BANKED_T1"
    assert abs(pos.qty_rem - 0.50) < 1e-6
    assert abs(pos.cur_sl - 100.25) < 1e-6
    assert mgr.is_zero_risk(pos)

    closed, _, note2 = mgr.step_bar(pos, 12, 103.25, 101.0, 103.1, 0.4, prot)
    assert not closed and note2 == "BANKED_T2_ORIGIN"
    assert abs(pos.qty_rem - 0.15) < 1e-6
    assert abs(pos.cur_sl - 101.25) < 1e-6

    closed, gross_r, note3 = mgr.step_bar(pos, 13, 106.6, 103.0, 106.5, 0.4, prot)
    assert closed and note3 == "VACUUM_TP"
    expected = 0.50 * 1.8 + 0.35 * 3.2 + 0.15 * 6.5
    assert abs(gross_r - expected) < 1e-5


def test_v11_engines_and_exports_parity() -> None:
    """Smoke-test V11 engines and verify live Binance + QuantConnect exports compile with V11 parameters."""
    df_btc = _make_synthetic_ohlcv(4000, "5min", start="2024-01-01", seed=9)
    df_xau = _make_synthetic_ohlcv(8000, "1min", start="2024-01-01", seed=13)
    df_nsx = _make_synthetic_ohlcv(8000, "1min", start="2024-01-01", seed=17)
    t0 = pd.Timestamp("2024-01-05", tz="UTC")
    t1 = pd.Timestamp("2024-01-20", tz="UTC")

    tr_eq, sm_eq = run_v11_session_equilibrium_scalp(df_btc, t0, t1)
    assert isinstance(tr_eq, list) and "all" in sm_eq

    tr_btc, sm_btc = run_v11_btc_portfolio(df_btc, t0, t1)
    assert isinstance(tr_btc, list) and "all" in sm_btc

    port = run_v11_multiasset_portfolio(df_btc, df_xau, df_nsx, t0, t1)
    assert "real_multiasset_summary" in port and "btc_summary" in port

    qc_path = PKG / "exports" / "quantconnect" / "BinanceFutures_MultiCoin_Scalper_QC.py"
    bn_path = PKG / "exports" / "binance" / "binance_futures_scalper.py"
    py_compile.compile(str(qc_path), doraise=True)
    py_compile.compile(str(bn_path), doraise=True)

    qc_src = qc_path.read_text(encoding="utf-8")
    assert "V11_SessEq_1H_TOPO" in qc_src
    assert "self.fee_rt_pct" in qc_src
    assert ("0.034" in qc_src or "0.038" in qc_src) and ("0.75" in qc_src or "0.80" in qc_src)

    spec = importlib.util.spec_from_file_location("binance_futures_scalper_v11", str(bn_path))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    qty = mod.compute_order_qty(
        equity_usdt=100.0,
        risk_pct=0.030,
        entry_px=100.0,
        sl_px=99.6,  # 0.40% SL
        filt=mod.SymbolFilters(tick_size=0.01, step_size=0.001, min_qty=0.001, min_notional=5.0),
        leverage=15,
        max_slot_frac=0.85,
        fee_rt_pct=0.0010,
    )
    # Notional = 3.0 / (0.004 + 0.001) = $600 -> 6.0 units (not $750 = 7.5 units)
    assert abs(qty - 6.0) < 1e-6


def test_surgical_modules_reference_levels_dd_safe_and_v12_exits() -> None:
    """Verify Surgical Modules 1, 2, and 3 (Reference Levels/Reclaim, Downward-Safe Exact-1R, QC/Binance V12 Exits)."""
    # Module 1: Causal Reference Levels (PDH/PDL, PWH/PWL, Asia/London) + Sweep/Reclaim/BOS
    df = _make_synthetic_ohlcv(2500, "5min", start="2025-01-01", seed=42)
    ts_ns = df.index.asi8
    highs = df["High"].to_numpy(dtype=float)
    lows = df["Low"].to_numpy(dtype=float)
    closes = df["Close"].to_numpy(dtype=float)
    atr = np.full(len(df), 25.0, dtype=float)
    snap = InstitutionalReferenceAndSwingEngine.compute_causal_reference_levels(
        ts_ns, highs, lows, closes, atr, idx=2300
    )
    assert isinstance(snap, ReferenceLevelSnapshot)
    assert not np.isnan(snap.pdh) and not np.isnan(snap.pdl)

    # Valid bullish sweep below pool_level=100, reclaim above 100, BOS close above 103
    h_arr = np.array([102.0, 101.0, 102.0, 105.0])
    l_arr = np.array([100.5, 98.5, 100.2, 101.0])
    c_arr = np.array([101.0, 100.4, 101.5, 104.0])
    a_arr = np.array([3.0, 3.0, 3.0, 3.0])
    ok, tag, q = InstitutionalReferenceAndSwingEngine.validate_sweep_and_reclaim(
        side=1, pool_level=100.0, is_confirmed_pivot_or_ref=True,
        highs=h_arr, lows=l_arr, closes=c_arr, atr=a_arr,
        sweep_idx=1, current_idx=3, internal_bos_level=103.0,
    )
    assert ok and tag == "VALID_BULLISH_SWEEP_RECLAIM_BOS" and q >= 0.55

    # Invalid Rule D: Price Acceptance below level (closes stay < 100.0)
    c_acc = np.array([101.0, 99.0, 98.8, 99.2])
    ok_bad, tag_bad, q_bad = InstitutionalReferenceAndSwingEngine.validate_sweep_and_reclaim(
        side=1, pool_level=100.0, is_confirmed_pivot_or_ref=True,
        highs=h_arr, lows=l_arr, closes=c_acc, atr=a_arr,
        sweep_idx=1, current_idx=3, internal_bos_level=103.0,
    )
    assert (not ok_bad) and tag_bad == "REJECT_BEARISH_PRICE_ACCEPTANCE" and q_bad == 0.0

    # Module 2: Downward-Safe Exact-1.0R Manager
    mgr = DrawdownSafeExactRManager()
    # Winning week: active=120, week_start=100 -> anchor=100 -> risk_usd=3.0 (3.0% of 100)
    r_win, _ = mgr.resolve_risk_usd(active_equity=120.0, peak_active_equity=120.0, week_start_equity=100.0, is_aplus=False)
    assert abs(r_win - 3.0) < 1e-6
    # Losing week (15% DD >= 12%): active=85, peak=100, week_start=100 -> anchor=85 * 3.4% * 0.75 = 2.1675
    r_dd, _ = mgr.resolve_risk_usd(active_equity=85.0, peak_active_equity=100.0, week_start_equity=100.0, is_aplus=True)
    assert abs(r_dd - (85.0 * 0.034 * 0.75)) < 1e-6
    notional, qty_1r = mgr.compute_exact_1r_notional(r_win, 100.0, 100.0, 99.6, fee_rt_pct=0.0010)
    assert abs(notional - (3.0 / 0.0050)) < 1e-6 and abs(qty_1r - 6.0) < 1e-6

    # Module 3: QC & Binance V12 surgical 3-tier + 15m protected trail presence & compile
    qc_src = (PKG / "exports" / "quantconnect" / "BinanceFutures_MultiCoin_Scalper_QC.py").read_text(encoding="utf-8")
    bn_src = (PKG / "exports" / "binance" / "binance_futures_scalper.py").read_text(encoding="utf-8")
    assert "_manage_active_positions_v12_surgical" in qc_src
    assert "_replace_stop_loss_order" in qc_src
    assert "15M_TRAIL" in qc_src and "15M_TRAIL" in bn_src

