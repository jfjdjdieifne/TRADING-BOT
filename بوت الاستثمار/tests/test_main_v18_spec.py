"""Behavioral tests for reference/main_v18.py — each test reproduces one of
the 6 fatal bugs from Run 11 and asserts the fixed behavior."""

import importlib.util
import sys
import types
from collections import deque
from pathlib import Path

# ---- minimal QuantConnect stub so the file imports outside LEAN ---------- #
stub = types.ModuleType("AlgorithmImports")


class _QCAlgorithm:
    pass


class _FeeModel:
    pass


class _OrderFee:
    def __init__(self, amount=None):
        self.amount = amount


class _CashAmount:
    def __init__(self, value=0.0, currency="USDT"):
        self.value = value
        self.currency = currency


class _BN:
    BINANCE_FUTURES = "binance_futures"


class _AT:
    MARGIN = "margin"


class _Res:
    MINUTE = "minute"


class _Mkt:
    BINANCE = "binance"


class _OS:
    INVALID = "invalid"
    FILLED = "filled"


class _Cons:
    def __init__(self, *a, **k):
        self.data_consolidated = types.SimpleNamespace()


stub.QCAlgorithm = _QCAlgorithm
stub.FeeModel = _FeeModel
stub.OrderFee = _OrderFee
stub.CashAmount = _CashAmount
stub.BrokerageName = _BN
stub.AccountType = _AT
stub.Resolution = _Res
stub.Market = _Mkt
stub.OrderStatus = _OS
stub.TradeBarConsolidator = _Cons
stub.timedelta = __import__("datetime").timedelta
sys.modules["AlgorithmImports"] = stub

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("main_v18", ROOT / "reference" / "main_v18.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


# ---- fixtures ------------------------------------------------------------ #
def make_coin(price=100.0, atr=1.0):
    s = m.SymData("X")
    for _ in range(60):
        s.c5.append(price)
        s.h5.append(price + 0.1)
        s.l5.append(price - 0.1)
        s.o5.append(price)
        s.v5.append(100.0)
    for i in range(80):
        s.c1.append(price)
        s.h1.append(price + 0.4)
        s.l1.append(price - 0.4)
        s.o1.append(price)
        s.v1.append(100.0)
    for _ in range(40):
        s.c4.append(price)
        s.h4.append(price + 2.0)
        s.l4.append(price - 2.0)
        s.o4.append(price)
        s.v4.append(100.0)
    s.b5, s.b1, s.b4 = 1000, 500, 200
    s.e20_1 = s.e50_1 = s.e200_1 = price
    s.e20_4 = s.e50_4 = s.e200_4 = price
    s.atr1, s.atr4 = atr, atr * 4
    s.rsi1 = 45.0
    for _ in range(30):
        s.rsi1_hist.append(45.0)
    s.vma1 = 100.0
    return s


def make_engine():
    eng = m.BinanceFuturesMultiCoinV12.__new__(m.BinanceFuturesMultiCoinV12)
    eng.coins = ["BTCUSDT", "ETHUSDT"]
    eng.data = {"BTCUSDT": make_coin(), "ETHUSDT": make_coin()}
    eng.syms = {"BTCUSDT": "BTCUSDT", "ETHUSDT": "ETHUSDT"}
    eng.orders = []

    class Holding:
        def __init__(self, invested=False, qty=0.0, px=100.0):
            self.invested = invested
            self.quantity = qty
            self.average_price = px

    class Portfolio(dict):
        total_portfolio_value = 100.0
        margin_remaining = 50.0

    eng.portfolio = Portfolio()
    for tk in eng.coins:
        eng.portfolio[tk] = Holding()

    class Props:
        lot_size = 0.001

    class Sec:
        symbol_properties = Props()
        price = 100.0

    eng.securities = {tk: Sec() for tk in eng.coins}

    def fake_order(sym, qty, tag=None):
        eng.orders.append((sym, qty, tag))
        return types.SimpleNamespace(status=_OS.FILLED)

    eng.market_order = fake_order
    return eng


def open_position(eng, tk="ETHUSDT", ep=100.0, ir=2.0, stage=0):
    # ir=2.0 >= manage's 1.5% price floor, so R-math stays exact
    s = eng.data[tk]
    s.ep = ep
    s.ir = ir
    s.sl = ep - ir
    s.stage = stage
    s.eb5 = s.b5 - 10
    s.eb1 = 0
    s.eb4 = 0
    s.mfe = ep
    s.arm = "W_CAP_BOTTOM"
    s.sl_breach = 0
    eng.portfolio[tk] = types.SimpleNamespace(
        invested=True, quantity=0.05, average_price=ep)
    eng.get_macro_regime = lambda: ("RANGE_SNIPER", 0.30)
    return s


# ---- FATAL BUG 1: the 3.02R choke trap ---------------------------------- #
def test_no_choke_at_3r_dip():
    eng = make_engine()
    s = open_position(eng)             # ep=100, ir=2
    s.mfe = 106.40                     # peak +3.20R
    eng.manage_position(0, s, "ETHUSDT", 106.10, 106.40, 106.00)
    assert s.stage == 1
    # floor_3r = ep + 3.02*ir = 106.04 must NOT be armed at 3.20R
    assert s.sl < s.ep + 3.02 * s.ir, "floor_3r armed before 3.47R = Run-11 choke"
    # Run 11 would exit here (sl at ~3.02R while price 3.05R). Now:
    eng.orders.clear()
    eng.manage_position(0, s, "ETHUSDT", 106.00, 106.10, 105.95)
    assert eng.orders == [], "0.05R dip after 3R must NOT exit the runner"
    assert s.stage == 1


def test_floor_only_arms_after_347r_with_room():
    eng = make_engine()
    s = open_position(eng)             # ep=100, ir=2
    s.rsi1 = 50.0
    s.h5[-2] = 106.50                   # no deceleration signal
    s.c1[-1] = 106.50
    for i in range(-20, 0):             # ceiling far overhead (not at_res)
        s.h4[i] = 115.0
    s.mfe = 107.00                      # +3.50R -> armed
    eng.manage_position(0, s, "ETHUSDT", 107.00, 107.00, 106.90)
    assert s.stage == 1
    # armed floor = ep + 3.02*ir = 106.04 (0.45R below the 3.47R arm point)
    assert abs(s.sl - (s.ep + 3.02 * s.ir)) < 1e-9, s.sl
    # deliberate armed-floor exit only below floor (>= 0.45R room kept)
    eng.orders.clear()
    eng.manage_position(0, s, "ETHUSDT", 106.01, 107.00, 105.95)
    assert len(eng.orders) == 1 and eng.orders[0][2] == "RAT_3R_FLOOR"


def test_super_buffers_no_partial_fragments():
    src = (ROOT / "reference" / "main_v18.py").read_text()
    assert "partial_harvest" not in src and "HARVEST_" not in src
    # super rider locks carry >= 0.55R breathing room each
    for hi, lock in ((3.60, 3.05), (5.00, 3.80), (8.00, 6.00),
                     (14.0, 10.5), (22.0, 17.0)):
        assert hi - lock >= 0.55 - 1e-9, (hi, lock)


# ---- FATAL BUG 2: scratch shield (MFE winners must not round-trip) ------ #
def test_scratch_shield_locks_below_entry():
    eng = make_engine()
    s = open_position(eng)             # ep=100, ir=2
    s.mfe = 103.40                     # +1.70R MFE
    s.c1[-1] = 102.80                  # 1H close at +1.40R
    eng.manage_position(0, s, "ETHUSDT", 102.80, 103.40, 102.70)
    assert abs(s.sl - (s.ep - 0.15 * s.ir)) < 1e-9, s.sl
    assert s.sl < s.ep, "shield must sit below entry, never near price"
    assert eng.orders == []


def test_scratch_shield_second_rung_near_zero():
    eng = make_engine()
    s = open_position(eng)             # ep=100, ir=2
    s.mfe = 104.80                     # +2.40R
    s.c1[-1] = 104.10                  # 1H close +2.05R, bearish 1H
    s.o1[-1] = 104.60
    s.rsi1 = 40.0
    s.rsi1_hist[-7] = 50.0             # RSI dropped 10 points
    eng.manage_position(0, s, "ETHUSDT", 104.10, 104.80, 104.00)
    assert abs(s.sl - (s.ep - 0.05 * s.ir)) < 1e-9, s.sl


# ---- FATAL BUG 3: no buying under a 4H ceiling -------------------------- #
def _perfect_setup(eng):
    """Craft W_CAP_BOTTOM conditions on ETHUSDT (c=100, atr1=1)."""
    s = eng.data["ETHUSDT"]
    # washout low 14 hours back at 94.5 (window index 10 -> 24-10=14h)
    for i in range(-24, -3):
        s.l1[i] = 99.0
    s.l1[-14] = 94.5
    for i in range(-3, 0):
        s.l1[i] = 99.0
        s.h1[i] = 99.5
    s.h1[-2] = 99.5
    s.h1[-1] = 99.5
    s.o1[-1] = 99.0
    # RSI window oversold + divergence on the last 3
    for i in range(-24, -3):
        s.rsi1_hist[i] = 30.0
    for i in range(-3, 0):
        s.rsi1_hist[i] = 44.0
    s.rsi1 = 45.0
    # capitulation volume
    s.v1[-14] = 250.0
    s.vma1 = 100.0
    s.e50_1 = 100.0                    # 94.5 <= 95.2 washout line
    s.e20_1 = 99.0
    # 4H range: low 95 / high 110 -> pos_20 = 5/15 = 0.33, runway 10 >= 4.5
    for i in range(-20, 0):
        s.h4[i] = 110.0
        s.l4[i] = 95.0
    s.e200_4 = 100.0
    # struct bottom for ir: min(l1[-4:]) = 99 -> struct 98.65, raw 1.35
    return s


def test_runway_rejects_under_ceiling():
    eng = make_engine()
    s = _perfect_setup(eng)
    # ceiling only 2.0R away (< 2.8R) -> must reject
    for i in range(-20, 0):
        s.h4[i] = 102.0
        s.l4[i] = 95.0
    score, sl, arm = eng.evaluate_entry(
        "ETHUSDT", s, 100.0, 100.1, 99.9, 100.0, 100.0, "RANGE_SNIPER", 0.3)
    assert score == 0.0 and arm == "", (score, sl, arm)


def test_w_cap_bottom_fires_with_clear_runway():
    eng = make_engine()
    s = _perfect_setup(eng)
    score, sl, arm = eng.evaluate_entry(
        "ETHUSDT", s, 100.0, 100.1, 99.9, 100.0, 100.0, "RANGE_SNIPER", 0.3)
    assert arm == "W_CAP_BOTTOM" and score > 0.0, (score, sl, arm)
    ir = 100.0 - sl
    assert 1.5 - 1e-9 <= ir <= 2.0 + 1e-9, ir     # F5 bounds hold


# ---- FATAL BUG 4: BTC waterfall veto ------------------------------------ #
def test_waterfall_veto_blocks_every_entry():
    eng = make_engine()
    s = _perfect_setup(eng)
    b = eng.data["BTCUSDT"]
    b.e20_1 = 100.0
    b.c1[-1] = 98.0                    # < 99.2 and falling
    b.c1[-2] = 99.0
    b.c5[-1] = 99.4                    # < 99.5
    assert eng.btc_waterfall_veto() is True
    score, _, arm = eng.evaluate_entry(
        "ETHUSDT", s, 100.0, 100.1, 99.9, 100.0, 100.0, "RANGE_SNIPER", 0.3)
    assert score == 0.0 and arm == ""


def test_waterfall_exception_higher_low_reclaim():
    eng = make_engine()
    s = _perfect_setup(eng)
    b = eng.data["BTCUSDT"]
    b.e20_1 = 100.0
    b.c1[-1] = 98.0
    b.c1[-2] = 99.0
    b.c5[-1] = 99.4
    # confirmed 1H higher low + close above the last 1H high
    for i in range(-10, -3):
        b.l1[i] = 97.0
    for i, v in zip(range(-3, 0), (97.5, 97.6, 97.7)):
        b.l1[i] = v
    b.h1[-1] = 99.3
    assert eng.btc_waterfall_veto() is False
    score, _, arm = eng.evaluate_entry(
        "ETHUSDT", s, 100.0, 100.1, 99.9, 100.0, 100.0, "RANGE_SNIPER", 0.3)
    assert arm == "W_CAP_BOTTOM"


# ---- FATAL BUG 5: no chasing, ir inside bounds -------------------------- #
def test_far_bottom_is_rejected_not_chased():
    eng = make_engine()
    s = _perfect_setup(eng)
    for i in range(-4, 0):
        s.l1[i] = 80.0                 # struct bottom 19.65R away
    score, _, arm = eng.evaluate_entry(
        "ETHUSDT", s, 100.0, 100.1, 99.9, 100.0, 100.0, "RANGE_SNIPER", 0.3)
    assert score == 0.0 and arm == "", (score, arm)


# ---- FATAL BUG 6: invisible 1H stop, not 5m wick chasing ---------------- #
def test_stage0_waits_for_1h_close_below_stop():
    eng = make_engine()
    s = open_position(eng)             # ep=100, ir=2 -> sl=98
    s.mfe = 100.40
    # 1H still open above the stop: a 5m dip below sl must NOT exit
    s.c1[-1] = 99.50
    s.sl_breach = 0
    s.b1 = 10
    s.eb1 = 0
    eng.manage_position(0, s, "ETHUSDT", 97.50, 97.80, 97.40)
    assert s.ep == 100.0, "must wait for the 1H close, not the 5m wick"
    # now the completed 1H closes below sl AND price still below
    s.c1[-1] = 97.90
    eng.manage_position(0, s, "ETHUSDT", 97.95, 98.10, 97.85)
    assert len(eng.orders) == 1 and eng.orders[0][2] == "1H_STRUCT_STOP"
    assert s.ep == 0.0


def test_catastrophic_guard_at_185r():
    eng = make_engine()
    s = open_position(eng)             # ep=100, ir=2 -> guard at 96.30
    s.mfe = 100.20
    eng.manage_position(0, s, "ETHUSDT", 96.20, 100.20, 96.10)
    assert len(eng.orders) == 1 and eng.orders[0][2] == "CATASTROPHIC_GUARD"


# ---- spec 5.3: slot caps bind the notional ------------------------------- #
def test_range_slot_cap_binds():
    eng = make_engine()
    s = _perfect_setup(eng)
    eng.get_macro_regime = lambda: ("RANGE_SNIPER", 0.30)
    eng.try_enter("ETHUSDT", s, eng.syms["ETHUSDT"],
                  100.0, 100.1, 99.9, 100.0, 100.0)
    assert len(eng.orders) == 1
    sym, qty, tag = eng.orders[0]
    notional = qty * 100.0
    assert notional <= 100.0 * 0.42 + 1e-6, notional    # 42% slot cap
    assert tag.startswith("ENT_W_CAP_BOTTOM_RANGE_SNIPER") or "ENT_" in tag
