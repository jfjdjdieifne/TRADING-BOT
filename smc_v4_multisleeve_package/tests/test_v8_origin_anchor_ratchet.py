"""Unit, cashflow-ratchet, Prosecutor, and export-parity tests for V8.0 Intraday Cashflow & Conviction-Ratchet."""

from __future__ import annotations

import importlib.util
import pathlib
import sys

import pandas as pd

PKG_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from engine import (
    AdversarialCrossExaminer,
    IntradayCashflowExitManager,
    IntradayCashflowSniperV8,
    ProtectedSwingDetector,
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


def test_v8_three_tier_origin_anchor_exit_manager():
    mgr = IntradayCashflowExitManager()  # defaults: 40%@2.8R -> BE+0.5R, 40%@min(orig,5.5R)->+2.5R, 20%@12R
    prot = ProtectedSwingDetector()

    # Case A: Origin_Anchor at +4.8R (< +5.5R) -> Tier 2 banks 40% at +4.8R, locks SL at +2.50R, runner hits +12R
    pos = TradePositionState(
        trade_id=1, side=1, entry_bar=0,
        entry_ts=pd.Timestamp("2026-01-05 09:00", tz="UTC"),
        entry_price=100.0, init_sl=99.0, cur_sl=99.0, risk_dist=1.0,
    )
    closed, _, note1 = mgr.step_bar(pos, 1, bar_h=103.0, bar_l=100.1, bar_c=102.7, atr_exec=0.4, prot_swing=prot, target_px=104.8)
    assert not closed and note1 == "BANKED_T1"
    assert abs(pos.qty_rem - 0.60) < 1e-9
    assert abs(pos.cur_sl - 100.5) < 1e-9

    closed, _, note2 = mgr.step_bar(pos, 2, bar_h=105.0, bar_l=102.6, bar_c=104.7, atr_exec=0.4, prot_swing=prot, target_px=104.8)
    assert not closed and note2 == "BANKED_T2_ORIGIN"
    assert abs(pos.qty_rem - 0.20) < 1e-9
    assert abs(pos.cur_sl - 102.5) < 1e-9

    closed, gross_r, reason = mgr.step_bar(pos, 3, bar_h=112.2, bar_l=104.5, bar_c=112.0, atr_exec=0.4, prot_swing=prot, target_px=104.8)
    assert closed and reason == "VACUUM_TP"
    expected_r = 0.40 * 2.8 + 0.40 * 4.8 + 0.20 * 12.0
    assert abs(gross_r - expected_r) < 1e-6

    # Case B: Runner pulled back after Tier 2 (+5.5R capped) must exit at >= +2.50R lock
    pos2 = TradePositionState(
        trade_id=2, side=1, entry_bar=0,
        entry_ts=pd.Timestamp("2026-01-06 09:00", tz="UTC"),
        entry_price=100.0, init_sl=99.0, cur_sl=99.0, risk_dist=1.0,
    )
    mgr.step_bar(pos2, 1, bar_h=103.0, bar_l=100.1, bar_c=102.8, atr_exec=0.4, prot_swing=prot, target_px=109.0)
    mgr.step_bar(pos2, 2, bar_h=105.6, bar_l=102.8, bar_c=105.4, atr_exec=0.4, prot_swing=prot, target_px=109.0)
    closed2, gross_r2, reason2 = mgr.step_bar(pos2, 3, bar_h=104.0, bar_l=102.4, bar_c=102.6, atr_exec=0.4, prot_swing=prot, target_px=109.0)
    assert closed2 and reason2 == "RUNNER_SL"
    expected_r2 = 0.40 * 2.8 + 0.40 * 5.5 + 0.20 * 2.5
    assert abs(gross_r2 - expected_r2) < 1e-6


def test_v8_prosecutor_brick_wall_and_conviction_gate():
    pros = AdversarialCrossExaminer(grace_bars=1, decay_lambda=0.65, min_conviction=0.55)
    # Borderline thesis into a tight opposing HTF Brick Wall (0.6R < min_clearance_r=3.0) is vetoed by Bayesian conviction
    v_wall = pros.cross_examine(
        side=1, entry_px=100.0, risk_dist=1.0,
        thesis_scores={"sweep": 0.65, "disp": 0.65, "vac": 0.62, "ker4": 0.65, "rvol": 0.60},
        thesis_weights={"sweep": 1.1, "disp": 1.2, "vac": 1.0, "ker4": 1.0, "rvol": 0.7},
        opposing_htf_walls=[100.6],
        ker_4h=0.35, body_ratio_4h=0.60, dir_4h_candle=1, htf_trend_1h=1, htf_trend_4h=1,
        rvol_entry=1.0, rvol_opp=1.0, is_counter_trend_sweep=False, min_clearance_r=3.0,
    )
    assert v_wall.brick_wall_penalty > 0.75
    assert not v_wall.approved

    # Clean institutional clearance (>= 3.0R) -> approved with zero brick-wall penalty
    v_ok = pros.cross_examine(
        side=1, entry_px=100.0, risk_dist=1.0,
        thesis_scores={"sweep": 0.78, "disp": 0.80, "vac": 0.72, "ker4": 0.75, "rvol": 0.65},
        thesis_weights={"sweep": 1.1, "disp": 1.2, "vac": 1.0, "ker4": 1.0, "rvol": 0.7},
        opposing_htf_walls=[104.5],
        ker_4h=0.35, body_ratio_4h=0.60, dir_4h_candle=1, htf_trend_1h=1, htf_trend_4h=1,
        rvol_entry=1.2, rvol_opp=1.0, is_counter_trend_sweep=False, min_clearance_r=3.0,
    )
    assert v_ok.brick_wall_penalty == 0.0
    assert v_ok.approved and v_ok.conviction >= 0.55


def test_v8_conviction_ratchet_cashflow_and_dd_throttle():
    mgr = SmallAccountCashflowManager(
        starting_equity=100.0,
        risk_pct=0.025,
        aplus_risk_pct=0.040,
        throttle_risk_pct=0.020,
        throttle_dd_pct=0.10,
        skim_step_usd=25.0,
        skim_frac=0.50,
    )
    # Tiered conviction risk resolution
    assert abs(mgr.resolve_risk_pct(100.0, 100.0, {"setup": "V8_CompVacuum"}) - 0.025) < 1e-9
    assert abs(mgr.resolve_risk_pct(100.0, 100.0, {"setup": "V8_BPR_Snap"}) - 0.040) < 1e-9
    assert abs(mgr.resolve_risk_pct(100.0, 100.0, {"setup": "SMC_Sweep_V6"}) - 0.040) < 1e-9
    # >10% drawdown from HWM triggers 2.0% throttle
    assert abs(mgr.resolve_risk_pct(88.0, 100.0, {"setup": "SMC_Sweep_V6"}) - 0.020) < 1e-9

    # 50/50 HWM skim: A+ trade wins +8R on $100 @ 4% ($4 risk -> +$32 => $132).
    # Gain above $100 anchor is +$32 >= $25 -> $16 locked permanently into vault, $116 active equity!
    t0 = pd.Timestamp("2026-01-01 08:00", tz="UTC")
    trades = [
        {"entry_time": t0, "sl_pct": 0.0075, "net_r": 8.0, "setup": "SMC_Sweep_V6", "is_aplus": True},
        {"entry_time": t0 + pd.Timedelta(days=1), "sl_pct": 0.0075, "net_r": -1.0, "setup": "V8_CompVacuum", "is_aplus": False},
    ]
    res = mgr.simulate_cashflow(trades, mode="ratchet_cashflow")
    assert res["mode"] == "RATCHET_CASHFLOW"
    assert abs(res["withdrawn_vault_usd"] - 16.0) < 1e-6
    # Day 2 risk is 2.5% of $116 = $2.90 -> -1R loss reduces active eq to $113.10; vault stays $16.00!
    assert abs(res["final_equity_usd"] - 113.10) < 1e-6
    assert abs(res["total_wealth_usd"] - 129.10) < 1e-6


def test_v8_exports_parity_and_compile():
    bot = _load_binance_bot_module()
    assert hasattr(bot, "detect_v8_bpr_signal")

    qc_path = PKG_ROOT / "exports" / "quantconnect" / "BinanceFutures_MultiCoin_Scalper_QC.py"
    qc_src = qc_path.read_text(encoding="utf-8")
    compile(qc_src, str(qc_path), "exec")
    assert "BANK40_T1" in qc_src and "BANK40_T2" in qc_src
    assert "withdrawn_vault_usd" in qc_src
    assert "min_clearance_r=3.0" in qc_src

    bot_src = (PKG_ROOT / "exports" / "binance" / "binance_futures_scalper.py").read_text(encoding="utf-8")
    compile(bot_src, "binance_futures_scalper.py", "exec")
    assert "BANK40_T1" in bot_src and "BANK40_T2" in bot_src
    assert "withdrawn_vault_usd" in bot_src
    assert "min_clearance_r=3.0" in bot_src
    assert IntradayCashflowSniperV8.in_intraday_killzone(13, 0)
