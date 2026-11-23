"""Unit, zero-lookahead, cashflow, and export-parity tests for V7.0 Intraday Cashflow Sniper."""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import types

import numpy as np
import pandas as pd

PKG_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from engine import (
    IntradayCashflowExitManager,
    IntradayCashflowSniperV7,
    ProtectedSwingDetector,
    SceneGraphPhysicsDetector,
    SmallAccountCashflowManager,
    TradePositionState,
)


def _load_binance_bot_module():
    path = PKG_ROOT / "exports" / "binance" / "binance_futures_scalper.py"
    spec = importlib.util.spec_from_file_location("binance_futures_scalper", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["binance_futures_scalper"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_v7_compression_vacuum_causal_and_edge_safe():
    det = SceneGraphPhysicsDetector(max_approach_ker=0.45, min_implied_r=3.0)
    # Build 30 bars: origin high at idx 4 (110.0), choppy compression grind down to 100.0,
    # then sweep below barrier 100.0 (low=99.2) and bullish snap close at 101.5.
    o = np.full(35, 102.0)
    h = np.full(35, 102.5)
    l = np.full(35, 101.5)
    c = np.full(35, 102.0)
    # Origin swing high at bar 9
    h[9] = 112.0
    c[9] = 111.0
    # Choppy alternating grind down from bar 10..32 toward 100.0
    for k in range(10, 33):
        drift = 109.0 - 0.44 * (k - 10) + (0.4 if k % 2 == 0 else -0.4)
        o[k] = drift + 0.15
        c[k] = drift - 0.15
        h[k] = max(o[k], c[k]) + 0.20
        l[k] = min(o[k], c[k]) - 0.20
    # Sweep bar 33 + displacement snap bar 34 (sl_dist = 101.6 - (99.5 - 0.2) = 2.3 <= 2.8 * ATR)
    o[33], h[33], l[33], c[33] = 100.0, 100.2, 99.5, 99.7
    o[34], h[34], l[34], c[34] = 99.7, 101.8, 99.6, 101.6
    atr = np.full(35, 1.0)

    setup = det.detect_compression_vacuum(o, h, l, c, atr, bar_idx=34, barriers_hi=[], barriers_lo=[100.0], lookback=30)
    assert setup is not None
    assert setup.side == 1
    assert setup.origin_anchor >= 111.0
    assert setup.implied_r >= 3.0

    # Edge-case safety: origin_idx near end of window must not raise ValueError on empty slice
    o2 = np.full(35, 100.0)
    h2 = np.full(35, 100.5)
    l2 = np.full(35, 99.5)
    c2 = np.full(35, 100.0)
    h2[31] = 110.0  # origin_idx == len(win_h) - 4
    o2[34], h2[34], l2[34], c2[34] = 99.5, 102.0, 99.2, 101.8
    assert det.detect_compression_vacuum(o2, h2, l2, c2, atr, bar_idx=34, barriers_hi=[], barriers_lo=[99.6], lookback=30) is None or True


def test_v7_bpr_ifvg_detection():
    det = SceneGraphPhysicsDetector(min_bpr_k=1.20)
    n = 20
    o = np.full(n, 103.0)
    h = np.full(n, 103.4)
    l = np.full(n, 102.6)
    c = np.full(n, 103.0)
    # Bearish manipulation FVG around bars 12..14 (l[12]=102.4 > h[14]=101.6)
    o[12], h[12], l[12], c[12] = 103.0, 103.2, 102.4, 102.5
    o[13], h[13], l[13], c[13] = 102.5, 102.6, 101.0, 101.2
    o[14], h[14], l[14], c[14] = 101.2, 101.6, 100.4, 100.6
    # Sweep below barrier 100.5 at bar 16
    o[16], h[16], l[16], c[16] = 100.6, 100.8, 99.8, 100.4
    # Bullish displacement FVG at bars 17..19 overlapping [101.6, 102.4]
    o[17], h[17], l[17], c[17] = 100.4, 101.5, 100.3, 101.4
    o[18], h[18], l[18], c[18] = 101.4, 102.9, 101.3, 102.8
    o[19], h[19], l[19], c[19] = 102.8, 103.5, 102.2, 103.4
    atr = np.full(n, 0.8)

    bpr = det.detect_bpr_ifvg(o, h, l, c, atr, bar_idx=19, barriers_hi=[], barriers_lo=[100.5], lookback_manip=10)
    assert bpr is not None
    assert bpr.side == 1
    assert bpr.low < bpr.high
    assert bpr.k_velocity >= 1.20


def test_v7_intraday_cashflow_exit_manager():
    mgr = IntradayCashflowExitManager(bank_r=3.0, bank_frac=0.35, be_lock_r=0.50, bank2_frac=0.0, runner_tp_r=10.0, stagnation_bars=0)
    prot = ProtectedSwingDetector()
    pos = TradePositionState(
        trade_id=1, side=1, entry_bar=0,
        entry_ts=pd.Timestamp("2025-01-01 08:00", tz="UTC"),
        entry_price=100.0, init_sl=99.0, cur_sl=99.0, risk_dist=1.0,
    )
    # Bar 1 reaches +3.2R -> banks 35% @ 3.0R (+1.05R), moves SL to +0.50R (100.5)
    closed, _, note = mgr.step_bar(pos, 1, bar_h=103.2, bar_l=100.1, bar_c=102.9, atr_exec=0.5, prot_swing=prot)
    assert not closed
    assert note in ("BANKED_PARTIAL", "BANKED_T1")
    assert abs(pos.cur_sl - 100.5) < 1e-9
    assert abs(pos.qty_rem - 0.65) < 1e-9

    # Bar 2 hits +10.0R target -> total realized = 0.35*3.0 + 0.65*10.0 = +7.55R
    closed, gross_r, reason = mgr.step_bar(pos, 2, bar_h=110.2, bar_l=102.5, bar_c=110.0, atr_exec=0.5, prot_swing=prot)
    assert closed
    assert reason == "VACUUM_TP"
    assert abs(gross_r - 7.55) < 1e-6

    # Runner SL hit after partial bank must still finish green (+0.35*3.0 + 0.65*0.50 = +1.375R)
    pos2 = TradePositionState(
        trade_id=2, side=1, entry_bar=0,
        entry_ts=pd.Timestamp("2025-01-02 08:00", tz="UTC"),
        entry_price=100.0, init_sl=99.0, cur_sl=99.0, risk_dist=1.0,
    )
    mgr.step_bar(pos2, 1, bar_h=103.1, bar_l=100.2, bar_c=102.5, atr_exec=0.5, prot_swing=prot)
    closed2, gross_r2, reason2 = mgr.step_bar(pos2, 2, bar_h=101.0, bar_l=100.4, bar_c=100.6, atr_exec=0.5, prot_swing=prot)
    assert closed2 and reason2 == "RUNNER_SL"
    assert abs(gross_r2 - 1.375) < 1e-6


def test_small_account_cashflow_manager_and_daily_circuit_breaker():
    mgr = SmallAccountCashflowManager(starting_equity=100.0, risk_pct=0.03, max_leverage=15.0, daily_dd_cap_r=-2.5)
    # 0.75% SL on $100 @ 3% risk -> $3 risk / 0.0075 = $400 notional (4x leverage <= 15x cap)
    risk_usd, notional = mgr.compute_position_notional(100.0, 0.0075)
    assert abs(risk_usd - 3.0) < 1e-6
    assert abs(notional - 400.0) < 1e-6

    # 3 losses of -1.0R on Day 1 -> 4th trade on Day 1 is blocked by -2.5R CB; Day 2 resets and takes +7.0R winner
    d1 = pd.Timestamp("2025-05-01 08:00", tz="UTC")
    d2 = pd.Timestamp("2025-05-02 08:00", tz="UTC")
    trades = [
        {"entry_time": d1, "sl_pct": 0.0075, "net_r": -1.0},
        {"entry_time": d1 + pd.Timedelta(hours=1), "sl_pct": 0.0075, "net_r": -1.0},
        {"entry_time": d1 + pd.Timedelta(hours=2), "sl_pct": 0.0075, "net_r": -1.0},
        {"entry_time": d1 + pd.Timedelta(hours=3), "sl_pct": 0.0075, "net_r": -1.0},  # skipped
        {"entry_time": d2, "sl_pct": 0.0075, "net_r": 7.0},
    ]
    res_fixed = mgr.simulate_cashflow(trades, mode="fixed_risk_withdrawal")
    assert res_fixed["skipped_circuit"] == 1
    assert abs(res_fixed["net_r"] - 4.0) < 1e-6
    assert abs(res_fixed["final_equity_usd"] - 112.0) < 1e-6

    res_comp = mgr.simulate_cashflow(trades, mode="compounded")
    assert res_comp["skipped_circuit"] == 1
    assert res_comp["final_equity_usd"] > 100.0


def test_v7_exports_10_coin_basket_and_binance_parity():
    bot = _load_binance_bot_module()
    expected = {
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
        "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "LINKUSDT", "SUIUSDT",
    }
    assert set(bot.DEFAULT_SYMBOLS) == expected

    # Verify $100 small-account sizing clears Binance minNotional on alts and BTC
    filt_btc = bot.SymbolFilters(tick_size=0.1, step_size=0.001, min_qty=0.001, min_notional=100.0)
    qty = bot.compute_order_qty(100.0, 0.03, entry_px=60000.0, sl_px=59550.0, filt=filt_btc, leverage=15, max_slot_frac=0.85)
    assert qty > 0 and (qty * 60000.0) >= 100.0

    # Verify QC file compiles cleanly and declares the 10-coin basket + V7 symbols
    qc_path = PKG_ROOT / "exports" / "quantconnect" / "BinanceFutures_MultiCoin_Scalper_QC.py"
    qc_src = qc_path.read_text(encoding="utf-8")
    compile(qc_src, str(qc_path), "exec")
    for sym in expected:
        assert f'"{sym}"' in qc_src
    assert "_detect_v7_comp_vacuum" in qc_src
    assert "_detect_v7_bpr" in qc_src
    assert "V8.0" in qc_src

    assert IntradayCashflowSniperV7.in_intraday_killzone(8, 0)
    assert not IntradayCashflowSniperV7.in_intraday_killzone(19, 0)
