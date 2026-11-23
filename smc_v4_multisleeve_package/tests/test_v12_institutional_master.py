from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PKG = Path(__file__).resolve().parents[1]
if str(PKG) not in sys.path:
    sys.path.insert(0, str(PKG))

from engine import (
    AdversarialCrossExaminer,
    InstitutionalReferenceAndSwingEngine,
    ReferenceLevelSnapshot,
    SceneGraphPhysicsDetector,
    SmallAccountCashflowManager,
    run_v12_btc_portfolio,
    run_v12_multiasset_portfolio,
)


def _load_binance_bot():
    bot_path = PKG / "exports" / "binance" / "binance_futures_scalper.py"
    spec = importlib.util.spec_from_file_location("bn_scalper_v12", str(bot_path))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_v12_ref_snap_prosecutor_brick_wall_and_touch_decay():
    ex = AdversarialCrossExaminer(min_conviction=0.55)
    scores = {"sweep": 0.72, "disp": 0.75, "vac": 0.72, "ker4": 0.65, "rvol": 0.65}
    weights = {"sweep": 1.1, "disp": 1.2, "vac": 1.0, "ker4": 1.0, "rvol": 0.7}

    # Fresh PDH (touches=1) at 1.5R blocks Setup A (hard_veto_ref_brick=True)
    snap_fresh = ReferenceLevelSnapshot(pdh=101.5, pdh_touches=1, pwh=108.0)
    v_veto = ex.cross_examine(
        side=1, entry_px=100.0, risk_dist=1.0,
        thesis_scores=scores, thesis_weights=weights, opposing_htf_walls=[],
        ker_4h=0.35, body_ratio_4h=0.6, dir_4h_candle=1,
        htf_trend_1h=1, htf_trend_4h=1, rvol_entry=1.2, rvol_opp=1.0,
        is_counter_trend_sweep=False,
        ref_snap=snap_fresh, min_tp1_clearance_r=2.2, hard_veto_ref_brick=True,
    )
    assert (not v_veto.approved) and v_veto.reasoning_chain["nearest_wall_r"] == 1.5

    # Decayed PDH (touches=3) is ignored as brick wall, and PWH at 8.0R >= 2.2R passes
    snap_decayed = ReferenceLevelSnapshot(pdh=101.5, pdh_touches=3, pwh=108.0)
    v_decayed = ex.cross_examine(
        side=1, entry_px=100.0, risk_dist=1.0,
        thesis_scores=scores, thesis_weights=weights, opposing_htf_walls=[],
        ker_4h=0.35, body_ratio_4h=0.6, dir_4h_candle=1,
        htf_trend_1h=1, htf_trend_4h=1, rvol_entry=1.2, rvol_opp=1.0,
        is_counter_trend_sweep=False,
        ref_snap=snap_decayed, min_tp1_clearance_r=2.2, hard_veto_ref_brick=True,
    )
    assert v_decayed.approved and v_decayed.conviction >= 0.55

    # Trend-aligned BPR (hard_veto_ref_brick=False) applies soft penalty instead of hard veto
    v_bpr = ex.cross_examine(
        side=1, entry_px=100.0, risk_dist=1.0,
        thesis_scores=scores, thesis_weights=weights, opposing_htf_walls=[],
        ker_4h=0.35, body_ratio_4h=0.6, dir_4h_candle=1,
        htf_trend_1h=1, htf_trend_4h=1, rvol_entry=1.2, rvol_opp=1.0,
        is_counter_trend_sweep=False,
        ref_snap=snap_fresh, min_tp1_clearance_r=2.2, hard_veto_ref_brick=False,
    )
    assert v_bpr.conviction < v_decayed.conviction


def test_v12_compression_vacuum_valid_barrier_and_reclaim_parity():
    det = SceneGraphPhysicsDetector()
    n = 30
    o = np.full(n, 102.0, dtype=float)
    h = np.full(n, 102.4, dtype=float)
    l = np.full(n, 101.6, dtype=float)
    c = np.full(n, 101.9, dtype=float)
    a = np.full(n, 1.0, dtype=float)
    # High origin early in window (bar 5) at 112.0 -> imp_r >= 3.2 toward 100.0 floor
    h[5] = 112.0
    o[5], c[5], l[5] = 111.5, 108.5, 108.0
    for i in range(6, 28):
        px = 102.5 - (i - 6) * 0.08 + (0.35 if i % 2 == 0 else -0.35)
        o[i], c[i], h[i], l[i] = px - 0.1, px + 0.1, px + 0.65, px - 0.65
    # Bar 28 sweeps below 100.0 and reclaims (>= 100.0), Bar 29 displaces UP > snap_lvl
    o[28], h[28], l[28], c[28] = 100.3, 100.4, 99.8, 100.2
    o[29], h[29], l[29], c[29] = 100.3, 102.3, 100.2, 102.2

    # Explicit empty valid_lo -> skipped even though raw barriers_lo=[100.0]
    sig_empty = det.detect_compression_vacuum(
        o, h, l, c, a, 29, [109.5], [100.0], valid_hi=[], valid_lo=[],
    )
    assert sig_empty is None

    # Valid barrier + reclaim validator passes
    sig_ok = det.detect_setup_a_waterfall(
        o, h, l, c, a, 29, [109.5], [100.0], valid_hi=[], valid_lo=[100.0],
        reclaim_validator=InstitutionalReferenceAndSwingEngine.validate_sweep_and_reclaim,
    )
    assert sig_ok is not None and sig_ok.side == 1

    # Price acceptance (bar 27 sweeps < 100.0 and bar 27..28 close < 100.0 without reclaim)
    l_acc, c_acc = l.copy(), c.copy()
    l_acc[27], c_acc[27], c_acc[28] = 99.6, 99.7, 99.8
    ok_acc, reason_acc, _ = InstitutionalReferenceAndSwingEngine.validate_sweep_and_reclaim(
        side=1, pool_level=100.0, is_confirmed_pivot_or_ref=True,
        highs=h, lows=l_acc, closes=c_acc, atr=a,
        sweep_idx=27, current_idx=29, internal_bos_level=101.0,
    )
    assert (not ok_acc) and "ACCEPTANCE" in reason_acc


def test_v12_cashflow_week_downward_safe_and_dual_dd_brake():
    dh = SmallAccountCashflowManager.v12_daily_hunter_100()
    ts = SmallAccountCashflowManager.v12_turbo_sniper_100()
    assert dh.period_anchor == "week_downward_safe" and ts.period_anchor == "week_downward_safe"
    assert abs(dh.risk_pct - 0.030) < 1e-9 and abs(dh.aplus_risk_pct - 0.034) < 1e-9
    assert abs(ts.risk_pct - 0.035) < 1e-9 and abs(ts.aplus_risk_pct - 0.040) < 1e-9
    assert abs(dh.throttle_dd_pct - 0.12) < 1e-9 and abs(dh.throttle_mult - 0.75) < 1e-9
    assert abs(dh.throttle2_dd_pct - 0.20) < 1e-9 and abs(dh.throttle2_mult - 0.60) < 1e-9

    t0 = pd.Timestamp("2025-01-06 08:00", tz="UTC")
    trades = [
        {"entry_time": t0, "exit_time": t0 + pd.Timedelta(hours=2), "asset": "BTCUSD", "setup": "SMC_Sweep_V6", "sl_pct": 0.008, "net_r": 4.0, "is_aplus": True},
        {"entry_time": t0 + pd.Timedelta(days=1), "exit_time": t0 + pd.Timedelta(days=1, hours=2), "asset": "BTCUSD", "setup": "V9_LON", "sl_pct": 0.008, "net_r": -1.0, "is_aplus": False},
        {"entry_time": t0 + pd.Timedelta(days=7), "exit_time": t0 + pd.Timedelta(days=7, hours=2), "asset": "BTCUSD", "setup": "V9_LON", "sl_pct": 0.008, "net_r": -1.0, "is_aplus": False},
        {"entry_time": t0 + pd.Timedelta(days=8), "exit_time": t0 + pd.Timedelta(days=8, hours=2), "asset": "BTCUSD", "setup": "SMC_Sweep_V6", "sl_pct": 0.008, "net_r": -1.0, "is_aplus": True},
        {"entry_time": t0 + pd.Timedelta(days=14), "exit_time": t0 + pd.Timedelta(days=14, hours=2), "asset": "BTCUSD", "setup": "SMC_Sweep_V6", "sl_pct": 0.008, "net_r": 3.5, "is_aplus": True},
    ]
    audit = dh.simulate_granular_audit(trades, mode="ratchet_cashflow", basket_mult=1.0)
    assert audit["summary"]["min_net_r"] >= -1.0
    assert audit["sign_inversions"]["weekly_sized_r"] == 0


def test_v12_binance_and_qc_parity_and_compact_export_bounds():
    bot = _load_binance_bot()
    base_ts = int(pd.Timestamp("2026-01-01 00:00", tz="UTC").timestamp() * 1000)
    bars = []
    for i in range(400):
        px = 100.0 + (2.0 if i < 288 else 0.5)
        bars.append((base_ts + i * 300_000, px, px + 0.4, px - 0.4, px + 0.1, 10.0))
    ref = bot.compute_causal_ref_levels_bars(bars, 0.5)
    assert ref["pdh"] is not None and ref["pdl"] is not None

    bars_ok = [
        (0, 100.5, 100.8, 100.2, 100.4, 10.0),
        (1, 100.4, 100.7, 100.1, 100.3, 10.0),
        (2, 100.3, 100.6, 100.1, 100.3, 10.0),
        (3, 100.3, 100.5, 100.1, 100.2, 10.0),
        (4, 100.5, 100.6, 99.6, 100.2, 10.0),
        (5, 100.2, 101.2, 100.1, 101.0, 12.0),
    ]
    assert bot.validate_sweep_reclaim_bars(bars_ok, 1, 100.0, 0.5)
    bars_acc = [
        (0, 100.5, 100.8, 100.2, 100.4, 10.0),
        (1, 100.4, 100.7, 100.1, 100.3, 10.0),
        (2, 100.3, 100.6, 100.1, 100.3, 10.0),
        (3, 100.3, 100.5, 100.1, 100.2, 10.0),
        (4, 100.2, 100.3, 99.4, 99.5, 10.0),
        (5, 99.5, 99.8, 99.3, 99.6, 10.0),
    ]
    assert not bot.validate_sweep_reclaim_bars(bars_acc, 1, 100.0, 0.5)

    btc_4h_up = [(i * 14_400_000, 100.0 + i, 101.1 + i, 99.9 + i, 101.0 + i, 100.0) for i in range(40)]
    assert bot._btc_regime_score_from_4h(btc_4h_up, side=-1) <= 0.20

    qc_full = PKG / "exports" / "quantconnect" / "BinanceFutures_MultiCoin_Scalper_QC.py"
    qc_compact = PKG / "exports" / "quantconnect" / "QC_BinanceFutures_V12_Compact.py"
    full_src = qc_full.read_text(encoding="utf-8")
    comp_src = qc_compact.read_text(encoding="utf-8")
    compile(full_src, str(qc_full), "exec")
    compile(comp_src, str(qc_compact), "exec")

    comp_lines = comp_src.splitlines()
    assert len(comp_lines) <= 380, f"Compact export too many lines: {len(comp_lines)}"
    assert len(comp_src) <= 22_000, f"Compact export too many chars: {len(comp_src)}"
    for token in (
        "4H_V6_Cognitive",
        "V10_CompVacuum",
        "V10_BPR_Snap",
        "V11_SessEq_1H_TOPO",
        "V9_LON",
        "SMC_Sweep_V6",
        "RefTracker",
        "TopoSwing",
        "SwingK3",
        "BANK40_T1",
        "BANK40_T2",
        "_btc_ok",
        "_anceq",
    ):
        assert token in comp_src, f"Missing {token} in QC_BinanceFutures_V12_Compact.py"


def test_v12_exports_available():
    assert callable(run_v12_btc_portfolio)
    assert callable(run_v12_multiasset_portfolio)
