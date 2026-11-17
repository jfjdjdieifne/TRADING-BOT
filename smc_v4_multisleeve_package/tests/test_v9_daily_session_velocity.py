"""Comprehensive V9.0 Daily Session Velocity, Zero-Risk Slot Recycling & Multi-Asset Tests."""

from __future__ import annotations

import pathlib
import py_compile
import sys

import numpy as np
import pandas as pd

PKG = pathlib.Path(__file__).resolve().parents[1]
if str(PKG) not in sys.path:
    sys.path.insert(0, str(PKG))

from engine import (
    DailySessionLiquidityTracker,
    DailySessionSniperV9,
    HighVelocityCashflowExitManager,
    ProtectedSwingDetector,
    SmallAccountCashflowManager,
    TopologicalSwing,
    TradePositionState,
    load_asset_ohlcv,
    run_v9_daily_session_backtest,
)


def test_daily_session_tracker_zero_lookahead() -> None:
    """Changing future NY bars must not affect Asia/London boundaries or earlier sweep signals."""
    idx = pd.date_range("2025-03-03 00:00", periods=288, freq="5min", tz="UTC")
    rng = np.random.default_rng(7)
    base = 50000.0 + np.cumsum(rng.normal(0.0, 25.0, len(idx)))
    o = base.copy()
    c = base + rng.normal(0.0, 15.0, len(idx))
    h = np.maximum(o, c) + 20.0
    l = np.minimum(o, c) - 20.0

    # Inject a deterministic London low sweep at 12:30 UTC (bar 150)
    lon_lo = float(np.min(l[84:144]))  # 07:00..11:55 UTC
    l[150] = lon_lo - 60.0
    c[150] = lon_lo + 15.0
    h[150] = lon_lo + 25.0

    def _run_prefix(h_arr, l_arr, c_arr, end_bar):
        tr = DailySessionLiquidityTracker(expiry_hours=5.0)
        sigs = []
        for i in range(end_bar):
            sigs.extend(tr.step_bar(idx[i], int(idx[i].as_unit("ns").value + 300 * 10**9), float(o[i]), float(h_arr[i]), float(l_arr[i]), float(c_arr[i]), 40.0))
        return tr, sigs

    tr1, s1 = _run_prefix(h, l, c, 155)
    h_mut, l_mut, c_mut = h.copy(), l.copy(), c.copy()
    h_mut[160:] += 5000.0
    l_mut[160:] -= 5000.0
    c_mut[160:] += 4000.0
    tr2, s2 = _run_prefix(h_mut, l_mut, c_mut, 155)

    assert tr1.lon_hi == tr2.lon_hi
    assert tr1.lon_lo == tr2.lon_lo
    assert [(x.source, x.side, x.sweep_ns, x.sweep_extreme) for x in s1] == [
        (x.source, x.side, x.sweep_ns, x.sweep_extreme) for x in s2
    ]
    assert any(x.source == "LON" and x.side == 1 for x in s1)


def test_high_velocity_exit_manager_and_zero_risk_lock() -> None:
    """Verify HighVelocityCashflowExitManager 45/40/15 & 15/20/65 Tier-1 BE+0.35R and is_zero_risk."""
    mgr = HighVelocityCashflowExitManager(
        bank_r=2.3, bank_frac=0.45, be_lock_r=0.35,
        bank2_r=4.2, bank2_frac=0.40, be2_lock_r=2.00,
        runner_tp_r=10.0, prot_trail_mfe_r=5.0,
    )
    pos = TradePositionState(
        trade_id=1, side=1, entry_bar=10, entry_ts=pd.Timestamp("2025-01-01 12:00", tz="UTC"),
        entry_price=100.0, init_sl=99.0, cur_sl=99.0, risk_dist=1.0,
    )
    assert not HighVelocityCashflowExitManager.is_zero_risk(pos)
    prot = ProtectedSwingDetector()

    # Bar 11 reaches +2.4R -> Tier-1 banks 45%, locks BE + 0.35R, marks zero-risk
    closed, _, note1 = mgr.step_bar(pos, 11, 102.4, 100.2, 102.2, 0.5, prot)
    assert not closed
    assert note1 == "BANKED_T1"
    assert abs(pos.qty_rem - 0.55) < 1e-6
    assert abs(pos.cur_sl - 100.35) < 1e-6
    assert HighVelocityCashflowExitManager.is_zero_risk(pos)

    # Bar 12 reaches +4.3R -> Tier-2 banks 40%, locks +2.0R
    closed, _, note2 = mgr.step_bar(pos, 12, 104.3, 102.1, 104.1, 0.5, prot)
    assert not closed
    assert note2 == "BANKED_T2_ORIGIN"
    assert abs(pos.qty_rem - 0.15) < 1e-6
    assert abs(pos.cur_sl - 102.0) < 1e-6

    # Bar 13 hits +10.0R TP on remaining 15%
    closed, gross_r, note3 = mgr.step_bar(pos, 13, 110.2, 104.0, 110.0, 0.5, prot)
    assert closed
    assert note3 == "VACUUM_TP"
    expected_r = 0.45 * 2.3 + 0.40 * 4.2 + 0.15 * 10.0
    assert abs(gross_r - expected_r) < 1e-5


def test_small_account_zero_risk_slot_recycling_and_granular_audit() -> None:
    """Slot recycling unlocks slots at t1_time (`BE+0.35R`) instead of blocking until exit_time."""
    t0 = pd.Timestamp("2025-01-01 12:00", tz="UTC")
    trades = [
        # Trade 1 enters at 12:00, locks BE+0.35R at 13:00 (`t1_time`), exits at 22:00
        {"entry_time": t0, "t1_time": t0 + pd.Timedelta(hours=1), "exit_time": t0 + pd.Timedelta(hours=10), "sl_pct": 0.01, "net_r": 2.5, "setup": "V9_LON", "side": 1, "asset": "BTCUSD"},
        # Trade 2 enters at 14:00 (after Trade 1 is already zero-risk!)
        {"entry_time": t0 + pd.Timedelta(hours=2), "t1_time": t0 + pd.Timedelta(hours=3), "exit_time": t0 + pd.Timedelta(hours=8), "sl_pct": 0.01, "net_r": 2.0, "setup": "V9_1H_K2", "side": 1, "asset": "XAUUSD"},
    ]

    # With 1 risk slot + slot_recycling=False -> Trade 2 is blocked!
    mgr_no_rec = SmallAccountCashflowManager(
        starting_equity=100.0, risk_pct=0.015, aplus_risk_pct=0.020,
        max_concurrent_risk_slots=1, slot_recycling=False,
    )
    res_no = mgr_no_rec.simulate_cashflow(trades, mode="ratchet_cashflow", basket_mult=1.0)
    assert res_no["n"] == 1
    assert res_no["skipped_slots"] == 1

    # With 1 risk slot + slot_recycling=True -> Trade 2 is accepted!
    mgr_rec = SmallAccountCashflowManager(
        starting_equity=100.0, risk_pct=0.015, aplus_risk_pct=0.020,
        max_concurrent_risk_slots=1, slot_recycling=True,
    )
    audit = mgr_rec.simulate_granular_audit(trades, mode="ratchet_cashflow")
    assert audit["summary"]["n"] == 2
    assert audit["summary"]["skipped_slots"] == 0
    assert len(audit["daily"]) == 1
    assert len(audit["monthly"]) == 1
    assert audit["summary"]["total_wealth_usd"] > 100.0


def test_v9_daily_session_backtest_real_btc_slice() -> None:
    """Verify causal V9.0 backtest on a 2024 BTCUSD_5m real data slice."""
    df_btc = load_asset_ohlcv(PKG / "data" / "BTCUSD_5m", ["2023", "2024"])
    eval_start = pd.Timestamp("2024-01-01", tz="UTC")
    eval_end = pd.Timestamp("2025-01-01", tz="UTC")
    trades, summary = run_v9_daily_session_backtest(
        df_btc,
        eval_start,
        eval_end,
        asset="BTCUSD",
        include_v8_physics=True,
        include_v6_4h=True,
    )
    assert len(trades) >= 70
    assert summary["all"]["pf"] > 1.20
    assert summary["all"]["net"] > 10.0
    for tr in trades:
        assert tr["entry_time"] < tr["exit_time"]
        assert eval_start <= tr["entry_time"] < eval_end
    setups = {t["setup"] for t in trades}
    assert any(s.startswith("V9_") for s in setups)


def test_v9_live_and_qc_exports_compile_and_parity() -> None:
    """Verify QC and Binance V9.0 exports compile cleanly and contain V9 session & slot-recycling hooks."""
    qc_path = PKG / "exports" / "quantconnect" / "BinanceFutures_MultiCoin_Scalper_QC.py"
    bn_path = PKG / "exports" / "binance" / "binance_futures_scalper.py"
    py_compile.compile(str(qc_path), doraise=True)
    py_compile.compile(str(bn_path), doraise=True)
    qc_src = qc_path.read_text(encoding="utf-8")
    bn_src = bn_path.read_text(encoding="utf-8")
    assert "DailySessionTracker" in qc_src and "_is_zero_risk" in qc_src and "V9_LON" in qc_src
    assert "detect_v9_daily_session_sweeps" in bn_src and "--no-v9" in bn_src and "V9_LON" in bn_src
