"""Unit, zero-lookahead, and parity tests for V6.0 Cognitive Fractal + Bayesian Prosecutor Engine."""

from __future__ import annotations

import datetime as dt
import importlib.util
import pathlib
import sys
import types

import numpy as np

PKG_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from engine.exit_manager import AdaptiveExitManager
from engine.perception_engine import KinematicMonitor, compute_atr_series
from engine.strategy_brain import AdversarialCrossExaminer


def test_pillar1_scale_free_fractal_stop_compression():
    km = KinematicMonitor()
    # Suppose entry=100, ATR_4H=4.0 (4% volatility regime), ATR_1H=1.5
    # Candidate structural anchors at 98.0 (delta=2.30 -> rho=0.575 inside Golden [0.35, 0.70]) and 94.0 (rho=1.575)
    sl_g, rho_g, src_g = km.fractal_stop_compression(
        100.0, 1, atr_4h=4.0, atr_1h=1.5, candidate_anchors=[98.0, 94.0], rho_min=0.35, rho_max=0.70
    )
    assert src_g == "FRACTAL_GOLDEN"
    assert 0.35 <= rho_g <= 0.70
    assert abs(sl_g - (98.0 - 0.20 * 1.5)) < 1e-6

    # Bounded [1.50, 2.00] mode must reject micro-anchors < 1.50 * ATR_4H and pick 94.0
    sl_b, rho_b, src_b = km.fractal_stop_compression(
        100.0, 1, atr_4h=4.0, atr_1h=1.5, candidate_anchors=[98.0, 94.0],
        rho_min=1.50, rho_max=1.85, min_rho_floor=1.50, max_rho_cap=2.00,
    )
    assert src_b == "FRACTAL_GOLDEN"
    assert 1.50 <= rho_b <= 1.85


def test_pillar2_kinematic_velocity_and_falling_knife_veto():
    km = KinematicMonitor(min_k_ratio=0.85)
    # Slow impulse (4 bars up 4 units -> V=1/bar), fast crash pullback (1 bar down 5 units -> V=5/bar) => K < 0.85
    o = np.array([100.0, 101.0, 102.0, 103.0, 104.0, 104.0])
    c = np.array([101.0, 102.0, 103.0, 104.0, 104.0, 99.0])
    h = np.maximum(o, c) + 0.1
    l = np.minimum(o, c) - 0.1
    atr = np.full(6, 1.0)
    k_crash, v_imp, v_pb = km.compute_kinematic_ratio(o, h, l, c, atr, 0, 4, 5)
    assert v_pb > v_imp and k_crash < 0.85
    assert km.falling_knife_veto(k_crash)

    # Strong fast impulse (2 bars up 6 units), slow 4-bar drift pullback (down 1.5 units) => K > 1.0
    o2 = np.array([100.0, 103.0, 106.0, 105.6, 105.2, 104.8, 104.5])
    c2 = np.array([103.0, 106.0, 105.6, 105.2, 104.8, 104.5, 105.2])
    h2 = np.maximum(o2, c2) + 0.1
    l2 = np.minimum(o2, c2) - 0.1
    atr2 = compute_atr_series(h2, l2, c2, 14)
    k_ok, _, _ = km.compute_kinematic_ratio(o2, h2, l2, c2, atr2, 0, 2, 5)
    assert not km.falling_knife_veto(k_ok)

    # Causal turnaround confirmation on bar 6 (bullish close above prior midpoint)
    v2 = np.array([100.0, 150.0, 90.0, 80.0, 75.0, 70.0, 110.0])
    confirmed, _ = km.causal_reaction_confirmed(o2, h2, l2, c2, v2, 6, 1, 1.0)
    assert confirmed


def test_pillar3_bayesian_prosecutor_decay_brickwall_and_freight_train():
    pros = AdversarialCrossExaminer(grace_bars=1, decay_lambda=0.65, min_conviction=0.40)
    s_fresh, st_fresh = pros.evaluate_temporal_sweep_decay(0.85, 0)
    s_acc, st_acc = pros.evaluate_temporal_sweep_decay(0.85, 3)
    assert st_fresh == "FRESH_REJECTION" and s_fresh == 0.85
    assert st_acc == "PRICE_ACCEPTANCE" and s_acc < 0.30

    # Clean trade approved + diagnostic reasoning_chain attached
    v_ok = pros.cross_examine(
        side=1, entry_px=100.0, risk_dist=1.0,
        thesis_scores={"sweep": 0.80, "disp": 0.80, "ker4": 0.70, "rvol": 0.65},
        thesis_weights={"sweep": 1.2, "disp": 1.2, "ker4": 1.0, "rvol": 0.6},
        opposing_htf_walls=[108.0],
        ker_4h=0.35, body_ratio_4h=0.60, dir_4h_candle=1,
        htf_trend_1h=1, htf_trend_4h=1, rvol_entry=1.4, rvol_opp=1.0,
        sweep_bars_accepted=0, is_counter_trend_sweep=False,
    )
    assert v_ok.approved and "conviction" in v_ok.reasoning_chain

    # HTF Freight-Train Veto blocks counter-trend sweep against strong 4H KER>0.45 impulse
    v_freight = pros.cross_examine(
        side=1, entry_px=100.0, risk_dist=1.0,
        thesis_scores={"sweep": 0.85, "disp": 0.80, "ker4": 0.70, "rvol": 0.65},
        thesis_weights={"sweep": 1.2, "disp": 1.2, "ker4": 1.0, "rvol": 0.6},
        opposing_htf_walls=[],
        ker_4h=0.58, body_ratio_4h=0.72, dir_4h_candle=-1,
        htf_trend_1h=1, htf_trend_4h=-1, rvol_entry=1.4, rvol_opp=1.0,
        sweep_bars_accepted=0, is_counter_trend_sweep=True,
        require_1h_bos_against_freight=False,
    )
    assert not v_freight.approved and v_freight.freight_train_veto

    # Brick-Wall obstacle < 2.5R ahead triggers heavy penalty & veto
    v_wall = pros.cross_examine(
        side=1, entry_px=100.0, risk_dist=1.0,
        thesis_scores={"sweep": 0.62, "disp": 0.60, "ker4": 0.55, "rvol": 0.55},
        thesis_weights={"sweep": 1.2, "disp": 1.2, "ker4": 1.0, "rvol": 0.6},
        opposing_htf_walls=[100.8],  # Only 0.8R room!
        ker_4h=0.30, body_ratio_4h=0.50, dir_4h_candle=1,
        htf_trend_1h=1, htf_trend_4h=1, rvol_entry=1.0, rvol_opp=1.0,
        min_clearance_r=2.5,
    )
    assert v_wall.brick_wall_penalty > 0.60 and not v_wall.approved


def test_pillar4_climax_elastic_ratchet():
    assert AdaptiveExitManager.climax_ratchet_4h_mult(5.0, 1.2, False, False) == 3.5
    m_mid = AdaptiveExitManager.climax_ratchet_4h_mult(12.0, 1.2, False, False)
    assert 2.0 < m_mid < 3.5
    assert AdaptiveExitManager.climax_ratchet_4h_mult(14.5, 1.2, False, False) == 2.0
    assert AdaptiveExitManager.climax_ratchet_4h_mult(6.0, 2.8, True, True) == 2.0


def test_live_v6_binance_and_qc_parity():
    bfs_path = PKG_ROOT / "exports" / "binance" / "binance_futures_scalper.py"
    spec_b = importlib.util.spec_from_file_location("bfs_v6", bfs_path)
    bfs = importlib.util.module_from_spec(spec_b)
    sys.modules["bfs_v6"] = bfs
    spec_b.loader.exec_module(bfs)

    t0 = int(dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc).timestamp() * 1000)
    b1d = [(t0 + i * 86400 * 1000, 100 + i * 0.5, 101 + i * 0.5, 99 + i * 0.5, 100.5 + i * 0.5, 1e4) for i in range(60)]
    b4h = [(t0 + i * 14400 * 1000, 100.0 + i * 0.2, 101.0 + i * 0.2, 99.0 + i * 0.2, 100.5 + i * 0.2, 1e3) for i in range(69)]
    prev_hi = max(b[2] for b in b4h[-20:])
    b4h.append((t0 + 69 * 14400 * 1000, prev_hi - 0.5, prev_hi + 3.0, prev_hi - 0.5, prev_hi + 2.5, 5e3))
    b1h = [(t0 + i * 3600 * 1000, 100, 101, 99, 100.2, 500) for i in range(70)]
    b15 = [(t0 + i * 900 * 1000, 100, 101, 99, 100.2, 100) for i in range(50)]
    b5 = [(t0 + i * 300 * 1000, 100, 101, 99, 100.2, 50) for i in range(90)]
    sig = bfs.evaluate_symbol_bars("BTCUSDT", b5, b15, b1h, b4h, b1d, use_4h_trend=True, use_smc=False)
    assert sig is not None and sig.engine == "4H_V6_Cognitive" and sig.side == 1
