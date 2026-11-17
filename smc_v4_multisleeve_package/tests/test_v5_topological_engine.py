"""Zero-lookahead, mathematical kernel, and live parity tests for V5 Topological Engine."""

from __future__ import annotations

import datetime as dt
import importlib.util
import pathlib
import sys
import types

import numpy as np
import pandas as pd

PKG_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from engine.exit_manager import AdaptiveExitManager, ProtectedSwingDetector, TradePositionState
from engine.liquidity_mapper import LiquidityPoolMapper
from engine.perception_engine import (
    TopologicalSwing,
    VisualPerceptionEngine,
    compute_atr_series,
    soft_and_log_odds,
)
from engine.regime_filter import RegimeFilterEngine


def test_causal_swings_zero_lookahead():
    rng = np.random.default_rng(123)
    n = 200
    t0 = int(dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc).timestamp() * 1e9)
    ts = np.array([t0 + i * int(14400 * 1e9) for i in range(n)], dtype=np.int64)
    c = 100.0 + np.cumsum(rng.normal(0.0, 1.8, size=n))
    h = c + np.abs(rng.normal(0.8, 0.5, size=n))
    l = c - np.abs(rng.normal(0.8, 0.5, size=n))
    atr = compute_atr_series(h, l, c, 14)

    perc = VisualPerceptionEngine()
    cutoff = 120
    sw_prefix = perc.detect_causal_swings(ts[:cutoff + 1], h[:cutoff + 1], l[:cutoff + 1], c[:cutoff + 1], atr[:cutoff + 1])

    # Mutate future bars strictly after cutoff
    h2, l2, c2 = h.copy(), l.copy(), c.copy()
    h2[cutoff + 1:] += 50.0
    l2[cutoff + 1:] -= 50.0
    c2[cutoff + 1:] += 30.0
    atr2 = compute_atr_series(h2, l2, c2, 14)
    sw_mut = [s for s in perc.detect_causal_swings(ts, h2, l2, c2, atr2) if s.confirm_idx <= cutoff]

    assert [(s.idx, s.confirm_idx, s.side, round(s.price, 6)) for s in sw_prefix] == [
        (s.idx, s.confirm_idx, s.side, round(s.price, 6)) for s in sw_mut
    ]
    assert all(s.confirm_idx > s.idx for s in sw_prefix)


def test_valley_depth_eqh_and_sweep_boost():
    perc = VisualPerceptionEngine()
    s1 = TopologicalSwing(10, 12, 0, 1, 100.0, 2.0, 5, 0.8, 99.5)
    # Exact equal high with deep valley (90.0)
    s2_eq = TopologicalSwing(25, 27, 0, 1, 100.05, 2.0, 3, 0.8, 99.4)
    # Slight sweep above s1 closing BELOW s1 (contextual boost)
    s2_swp = TopologicalSwing(25, 27, 0, 1, 100.35, 2.0, 3, 0.8, 99.6)
    # Same discrepancy WITHOUT sweep close (closed above s1)
    s2_brk = TopologicalSwing(25, 27, 0, 1, 100.35, 2.0, 3, 0.8, 100.30)

    sc_eq = perc.visual_eqh_eql_score(s1, s2_eq, valley_extreme=90.0, atr_val=1.5)
    sc_swp = perc.visual_eqh_eql_score(s1, s2_swp, valley_extreme=90.0, atr_val=1.5)
    sc_brk = perc.visual_eqh_eql_score(s1, s2_brk, valley_extreme=90.0, atr_val=1.5)
    assert sc_eq > 0.90
    assert sc_swp > sc_brk


def test_soft_and_log_odds_compensatory_and_veto():
    weights = {"sweep": 1.5, "disp": 1.2, "sec": 0.6, "ker": 1.0}
    comp = soft_and_log_odds({"sweep": 0.95, "disp": 0.90, "sec": 0.40, "ker": 0.70}, weights, {"ker": 0.15})
    assert comp > 0.75
    vetoed = soft_and_log_odds({"sweep": 0.95, "disp": 0.90, "sec": 0.80, "ker": 0.05}, weights, {"ker": 0.15})
    assert vetoed < 0.10


def test_liquidity_mapper_strictly_causal_sessions():
    perc = VisualPerceptionEngine()
    lm = LiquidityPoolMapper(perc)
    t0 = dt.datetime(2025, 3, 10, 0, 0, tzinfo=dt.timezone.utc)
    # Feed 00:00..07:00 UTC -> Asia session NOT closed yet
    for hr in range(8):
        ts = (t0 + dt.timedelta(hours=hr)).timestamp()
        lm.step_bar(ts, 100.0, 102.0 + hr * 0.1, 99.0, 101.0, 1.0)
    assert not any(p.kind == "ASIA_H" for p in lm.pools.values())
    # Feed 08:00 UTC -> Asia session NOW closed and emitted
    lm.step_bar((t0 + dt.timedelta(hours=8)).timestamp(), 101.0, 101.5, 100.5, 101.2, 1.0)
    asia_hi = [p for p in lm.pools.values() if p.kind == "ASIA_H"]
    assert len(asia_hi) == 1 and abs(asia_hi[0].price - 102.7) < 1e-6


def test_regime_filter_tod_rvol_and_ker():
    idx = pd.date_range("2025-01-01", periods=40, freq="4h", tz="UTC")
    closes = np.array([100.0 + (1.0 if i % 2 == 0 else -1.0) for i in range(40)])
    closes[35] = 100.0  # Place bar 35 strictly inside middle 50% equilibrium
    df = pd.DataFrame({
        "Open": closes - 0.1, "High": closes + 0.5, "Low": closes - 0.5, "Close": closes,
        "Volume": np.full(40, 100.0),
    }, index=idx)
    rf = RegimeFilterEngine()
    feats = rf.precompute_frame_features(df)
    snap = rf.evaluate_bar(feats, 35, has_boundary_sweep=False)
    assert snap.ker < 0.25 and snap.in_mid_chop and snap.ker_score < 0.15


def test_protected_swing_and_adaptive_exit_phases():
    det = ProtectedSwingDetector()
    s_hi1 = TopologicalSwing(5, 7, 0, 1, 105.0, 2.0, 3, 0.8, 104.0)
    s_lo1 = TopologicalSwing(9, 11, 0, -1, 101.0, 2.0, 3, 0.8, 101.5)
    det.update(11, 103.0, [s_hi1, s_lo1])
    assert len(det.protected_lows) == 0  # No BOS close > 105.0 yet
    det.update(12, 105.8, [])
    assert len(det.protected_lows) == 1 and det.protected_lows[0].price == 101.0

    mgr = AdaptiveExitManager()
    pos = TradePositionState(1, 1, 1, None, 100.0, 99.0, 99.0, 1.0, entry_bos_count_1h=1)
    # Hit opposing 1H liquidity at +4.5R -> triggers BE + Partial + Pyramid Arm
    closed, _, _ = mgr.step_position(pos, 104.8, 103.0, 104.5, 0.8, 2.0, det, det, 104.5, 110.0)
    assert not closed and pos.be_moved and pos.partial_taken and pos.pyramid_armed


def test_binance_bot_and_qc_v5_parity():
    bfs_path = PKG_ROOT / "exports" / "binance" / "binance_futures_scalper.py"
    spec_b = importlib.util.spec_from_file_location("bfs_v5", bfs_path)
    bfs = importlib.util.module_from_spec(spec_b)
    sys.modules["bfs_v5"] = bfs
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
    assert sig is not None and sig.engine == "4H_V5_Trend" and sig.side == 1

    # Mock AlgorithmImports for QC V5
    mod = types.ModuleType("AlgorithmImports")
    class OrderStatus:
        NEW = "NEW"; SUBMITTED = "SUBMITTED"; PARTIALLY_FILLED = "PF"; FILLED = "FILLED"; CANCELED = "CANCELED"; INVALID = "INVALID"
    class Resolution: MINUTE = 1
    class Market: BINANCE = "Binance"
    class TimeZones: UTC = dt.timezone.utc
    class BrokerageName: BINANCE_FUTURES = "BinanceFutures"
    class AccountType: MARGIN = "Margin"
    class Symbol:
        def __init__(self, v): self.value = v
        def __hash__(self): return hash(self.value)
        def __eq__(self, o): return isinstance(o, Symbol) and self.value == o.value
    class OrderEvent:
        def __init__(self, sym, oid, st, fq=0.0, fp=0.0):
            self.symbol, self.order_id, self.status, self.fill_quantity, self.fill_price = sym, oid, st, fq, fp
    class Ticket:
        def __init__(self, oid, st="SUBMITTED"): self.order_id, self.status = oid, st
        def cancel(self): self.status = OrderStatus.CANCELED
    class Slice: pass
    class PortDict(dict):
        def __init__(self):
            super().__init__(); self.total_portfolio_value = 10000.0; self.margin_remaining = 10000.0
    class QCAlgorithm:
        def __init__(self):
            self.utc_time = dt.datetime(2025, 1, 10, 12, 0, tzinfo=dt.timezone.utc); self.is_warming_up = False
            self.securities = {}; self.portfolio = PortDict()
            self.transactions = types.SimpleNamespace(cancel_open_orders=lambda s: None)
            self._consolidators = []; self._oid = 0; self.orders = []; self._params = {}
        def set_time_zone(self, *a): pass
        def set_start_date(self, *a): pass
        def set_end_date(self, *a): pass
        def set_account_currency(self, *a): pass
        def set_warm_up(self, *a): pass
        def set_brokerage_model(self, *a): pass
        def get_parameter(self, k): return self._params.get(k)
        def add_crypto_future(self, tk, *a, **kw):
            sym = Symbol(tk)
            self.securities[sym] = types.SimpleNamespace(symbol=sym, price=115.0, symbol_properties=types.SimpleNamespace(lot_size=0.001, minimum_order_size=0.001, minimum_price_variation=0.01))
            self.portfolio[sym] = types.SimpleNamespace(invested=False)
            return self.securities[sym]
        def consolidate(self, sym, td, fn): self._consolidators.append((sym, td, fn))
        def market_order(self, sym, qty, tag=""):
            self._oid += 1; t = Ticket(self._oid); self.orders.append(("MKT", sym.value, qty, tag)); return t
        def limit_order(self, sym, qty, px, tag=""):
            self._oid += 1; t = Ticket(self._oid); self.orders.append(("LMT", sym.value, qty, px, tag)); return t
        def stop_market_order(self, sym, qty, px, tag=""):
            self._oid += 1; t = Ticket(self._oid); self.orders.append(("STP", sym.value, qty, px, tag)); return t
        def liquidate(self, sym, tag=""): self.orders.append(("LIQ", sym.value, tag))
        def log(self, msg): pass

    for k, v in [("OrderStatus", OrderStatus), ("Resolution", Resolution), ("Market", Market), ("TimeZones", TimeZones),
                 ("BrokerageName", BrokerageName), ("AccountType", AccountType), ("Symbol", Symbol), ("OrderEvent", OrderEvent),
                 ("Slice", Slice), ("QCAlgorithm", QCAlgorithm), ("timedelta", dt.timedelta)]:
        setattr(mod, k, v)
    sys.modules["AlgorithmImports"] = mod

    qc_path = PKG_ROOT / "exports" / "quantconnect" / "BinanceFutures_MultiCoin_Scalper_QC.py"
    spec_q = importlib.util.spec_from_file_location("qc_v5", qc_path)
    qc_mod = importlib.util.module_from_spec(spec_q)
    spec_q.loader.exec_module(qc_mod)

    algo = qc_mod.BinanceFuturesMultiCoinScalper()
    algo.initialize()
    assert len(algo.coins) == 15 and len(algo._consolidators) == 75
    btc_sym = next(s for s in algo.coins if s.value == "BTCUSDT")
    st = algo.coins[btc_sym]
    BarObj = lambda o, h, l, c, v=1e3: types.SimpleNamespace(Open=o, High=h, Low=l, Close=c, Volume=v)
    for i in range(60):
        algo.on_1d(st, BarObj(100 + i * 0.5, 101 + i * 0.5, 99 + i * 0.5, 100.5 + i * 0.5))
    for i in range(69):
        algo.on_4h(st, BarObj(100 + i * 0.2, 101 + i * 0.2, 99 + i * 0.2, 100.5 + i * 0.2))
    algo.securities[btc_sym].price = prev_hi + 2.5
    algo.on_4h(st, BarObj(prev_hi - 0.5, prev_hi + 3.0, prev_hi - 0.5, prev_hi + 2.5, 5e3))
    assert any(o[0] == "MKT" and o[3] == "4H_V5_Trend" for o in algo.orders)
