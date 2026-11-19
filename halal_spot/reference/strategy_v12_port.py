"""Faithful standalone port of `BinanceFuturesMultiCoinV12` (QuantConnect) to pure Python.

Source of truth (verbatim QC original): reference/qc_binance_futures_multi_coin_v12.py
Port rule: 1-to-1 — every equation, number and condition copied unchanged.

Execution-model notes (environment differences only, no logic changes):
- BTCUSDT only: the project contains candle data for BTCUSD_5m alone; the other
  9 pairs of the QC universe (ETH/SOL/BNB/XRP/DOGE/ADA/AVAX/LINK/SUI) are untested
  (stated in the report). The original `_regime` / `_can` / `_allowed` formulas run
  unchanged over the 1-symbol universe.
- QC base resolution is 1m; here the resting stop_market_order is checked on EVERY
  completed 5m bar: long `low <= sl` fills at `min(open, sl)`, short `high >= sl`
  fills at `max(open, sl)` — precise Stop-Market simulation without lookahead.
- QC `market_order` entries use ImmediateFillModel: they fill at the current security
  price (= the signal 5m close) the moment they are placed inside `_on5m`.
- Exits via `liquidate` fill at the current security price of the callback
  (5m close inside `_m5` / `_exit`, HTF close inside `_trail`).
- Order of processing per 5m bar (documented choice): (1) resting stop check,
  (2) `_on5m`, (3) `_on15m`, (4) `_on1h`, (5) `_on4h`, (6) weekly `on_data` mode
  switch (LEAN consolidators fire in registration order before OnData).
- Futures margin model (harness): initial margin = notional / 10 (set_leverage(10));
  equity = free cash + reserved margin + unrealized PnL; `margin_remaining` modeled
  as equity*10 - margin used. `free_portfolio_value_percentage` enters no equation of
  this algorithm and is not modeled.
- Fees: Binance 0.1% per fill in USDT (session standing rule — matches the code's
  round-trip assumption FEE=0.0020); the QC constant `FEE` inside min_r / stats
  equations is kept verbatim.
- BTCUSDT futures symbol properties: tick 0.01, lot 0.001, min notional 5.5.
- Warmup 35 days (`set_warm_up`); test window fixed by the session standing rule to
  2025-07-01 .. 2026-07-01 (QC `get_parameter` y0/y1 defaults are overridden here).
- Harness-only: EOD flatten (tag EOD) so standalone/cut runs close deterministically
  (QC's on_end_of_algorithm only logs open positions).
- Reporting bookkeeping (trade records, equity rows, veto/engine stats) never feeds
  back into any signal, sizing or risk decision.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import math
from typing import Any, Optional

import pandas as pd

# --- Binance futures symbol properties (BTCUSDT) ----------------------------
TICK = 0.01             # minimum_price_variation
LOT = 0.001             # lot_size (futures stepSize)
MN = 5.5                # max(5.5, minimum_order_size) for BTCUSDT
FEE_RATE = 0.001        # 0.1% per fill in USDT (session standing rule)
FEE = 0.0020            # QC round-trip fee constant inside min_r / stats (verbatim)
LEVERAGE = 10.0         # set_leverage(10)

SYMBOL = "BTCUSDT"


def _sig(x):
    return 1.0 / (1.0 + math.exp(-max(-40.0, min(40.0, x))))


# ---------------------------------------------------------------------------
# Bars
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Bar:
    end_time: pd.Timestamp
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


# ---------------------------------------------------------------------------
# TopoSwing — V12 verbatim
# ---------------------------------------------------------------------------
class TopoSwing:
    def __init__(self, lb=80):
        self.c, self.tr = deque(maxlen=lb), deque(maxlen=lb)
        self.ah, self.al = [], []
        self.idx, self.os, self.cnh, self.cnl = 0, 0, 0, 0
        self.eh, self.hi, self.el, self.li = None, -1, None, -1

    def update(self, h, l, c):
        pc = self.c[-1] if self.c else c
        self.c.append(c)
        self.tr.append(max(h - l, abs(h - pc), abs(l - pc)))
        self.idx += 1
        if len(self.tr) < 10:
            return
        atr = max(sum(self.tr) / len(self.tr), c * 1e-4)
        if self.eh is None or h > self.eh:
            self.eh, self.hi = h, self.idx
        if self.el is None or l < self.el:
            self.el, self.li = l, self.idx
        if self.os != -1 and (self.eh - c) >= 1.25 * atr and (self.idx - self.hi) >= 1:
            self.ah = (self.ah + [(self.hi, self.eh)])[-24:]
            self.cnh += 1
            self.os, self.el, self.li = -1, l, self.idx
        elif self.os != 1 and (c - self.el) >= 1.25 * atr and (self.idx - self.li) >= 1:
            self.al = (self.al + [(self.li, self.el)])[-24:]
            self.cnl += 1
            self.os, self.eh, self.hi = 1, h, self.idx

    def atr(self):
        return max(sum(self.tr) / len(self.tr), 1e-6) if self.tr else 1e-4

    def ker(self, n=12):
        if len(self.c) < n + 1:
            return 0.5
        cl = list(self.c)[-n - 1:]
        v = sum(abs(cl[i] - cl[i - 1]) for i in range(1, len(cl)))
        return abs(cl[-1] - cl[0]) / v if v > 1e-9 else 0.0

    def swp_rec(self, o, h, l, c, lvl, sd, atr):
        if lvl <= 0 or atr <= 0:
            return 0.0
        rng = max(h - l, 1e-8)
        if sd == -1:
            if h <= lvl or c >= lvl:
                return 0.0
            pen, wk, rj = (h - lvl) / atr, (h - max(o, c)) / rng, (lvl - c) / atr
        else:
            if l >= lvl or c <= lvl:
                return 0.0
            pen, wk, rj = (lvl - l) / atr, (min(o, c) - l) / rng, (c - lvl) / atr
        g = math.exp(-((pen - 0.55) ** 2) / (2.0 * 0.65 ** 2))
        return float(max(0.0, min(1.0, _sig(2.5 * (wk - 0.30)) * _sig(2.2 * (rj + 0.15)) * (0.4 + 0.6 * g))))


# ---------------------------------------------------------------------------
# CoinMemory — V12 verbatim
# ---------------------------------------------------------------------------
class CoinMemory:
    def __init__(self):
        self.ath, self.atl = 0.0, 1e18
        self.dh, self.dl = deque(maxlen=90), deque(maxlen=90)
        self.e20 = self.e50 = self.e120 = self.h20 = 0.0

    def on5(self, h, l):
        if h > self.ath:
            self.ath = h
        if 0 < l < self.atl:
            self.atl = l

    def on1h(self, c):
        self.h20 = c if self.h20 == 0.0 else self.h20 + (2.0 / 21.0) * (c - self.h20)

    def on4h(self, c):
        if self.e20 == 0.0:
            self.e20 = self.e50 = self.e120 = c
        else:
            self.e20 += (2.0 / 21.0) * (c - self.e20)
            self.e50 += (2.0 / 51.0) * (c - self.e50)
            self.e120 += (2.0 / 121.0) * (c - self.e120)

    def push(self, h, l):
        if h > 0 and l < 1e17:
            self.dh.append(h)
            self.dl.append(l)

    def hi(self, n=30):
        return max(list(self.dh)[-n:]) if self.dh else self.ath

    def lo(self, n=30):
        return min(list(self.dl)[-n:]) if self.dl else self.atl

    def coiled(self, c, sd):
        if len(self.dh) < 14:
            return False
        dh, dl = list(self.dh), list(self.dl)
        h10, l10, h35, l35 = max(dh[-10:]), min(dl[-10:]), max(dh[-35:]), min(dl[-35:])
        ratio = max(h10 - l10, c * 1e-4) / max(h35 - l35, c * 1e-4)
        if sd == 1:
            return (ratio <= 0.58 and c >= h10 * 0.992) or c >= self.hi(25) * 0.992
        return (ratio <= 0.58 and c <= l10 * 1.008) or c <= self.lo(25) * 1.008


# ---------------------------------------------------------------------------
# SymState — V12 verbatim field set
# ---------------------------------------------------------------------------
class SymState:
    def __init__(self, sym):
        self.sym = sym
        self.mem = CoinMemory()
        self.sw1, self.sw15, self.sw4 = TopoSwing(80), TopoSwing(80), TopoSwing(90)
        self.b5 = self.b15 = self.b1 = self.b4 = 0
        self.q15, self.q1, self.q4 = deque(maxlen=24), deque(maxlen=32), deque(maxlen=96)
        self.v15, self.v1, self.v4 = deque(maxlen=24), deque(maxlen=24), deque(maxlen=24)
        self.pdh = self.pdl = self.pwh = self.pwl = 0.0
        self.cday = self.cwk = -1
        self.dh, self.dl, self.wh, self.wl = 0.0, 1e18, 0.0, 1e18
        self.sd4, self.sh4, self.sl4, self.ker4 = 0, 0.0, 0.0, 0.5
        self.sd1, self.sh1, self.sl1 = 0, 0.0, 0.0
        self.g4 = self.g1 = self.gi = self.gs = None
        self.armed = False
        self.mk = {1: -1, -1: -1}
        self.p0 = 0.0
        self.entk: Optional[dict] = None
        self.sltk: Optional[dict] = None
        self.eng, self.wall, self.story = "", "", ""
        self.sd = self.ph = self.cb = self.e4 = self.eb = 0
        self.en = self.sl = self.tp = self.tpr = self.min_r = 0.0
        self.rd = self.qty = self.mfe = self.peak = self.a1 = self.score = 0.0
        self.pend = self.closing = False
        self.if_bos = self.if_fvg = self.if_vol = 0


# ---------------------------------------------------------------------------
# Engine (QCAlgorithm port — single-symbol BTCUSDT futures)
# ---------------------------------------------------------------------------
class FuturesEngine:
    """Pure-Python execution engine mirroring BinanceFuturesMultiCoinV12 (BTCUSDT)."""

    def __init__(self, start: pd.Timestamp, capital: float = 100.0):
        self.start = start
        self.shorts = True          # get_parameter("shorts") default "1"
        self.rbudget = 0.10         # get_parameter("rbudget") default 0.10
        self.pk = self.wse = capital
        self.lwk, self.maxp, self.mode = -1, 5, "DAILY"
        self.cd: dict = {}
        self.st = {SYMBOL: SymState(SYMBOL)}
        self.s = self.st[SYMBOL]
        self.btc = SYMBOL
        self.vt: dict[str, int] = {}
        self.stats: dict[str, list] = {}
        self.nbad = 0
        self._rt: Any = None
        self._rv: Any = None
        # Futures margin book (harness)
        self.cash = float(capital)
        self.margin = 0.0           # reserved initial margin for the open position
        self.qty_signed = 0.0       # +long / -short (portfolio quantity)
        self.en_pos = 0.0           # position average entry (portfolio side)
        self.fees_total = 0.0
        # Context
        self.now = self.start
        self.price = 0.0
        # Reporting bookkeeping (never feeds decisions)
        self.events: list[dict] = []
        self.count: dict[str, int] = {}
        self.cur_trade: Optional[dict] = None
        self.trades: list[dict] = []
        self._trade_seq = 0
        self._order_seq = 0
        self._orders: dict[int, dict] = {}
        self.pending_meta: dict = {}

    # -- context helpers -----------------------------------------------------
    @property
    def is_warming_up(self) -> bool:
        return self.now < self.start

    def _log(self, typ: str, **kw: Any) -> None:
        self.events.append({"time": self.now, "type": typ, **kw})

    def _cnt(self, key: str, n: int = 1) -> None:
        self.count[key] = self.count.get(key, 0) + n

    def _invested(self) -> bool:
        """portfolio[sym].invested."""
        return self.qty_signed != 0.0

    def equity(self) -> float:
        """total_portfolio_value = cash + reserved margin + unrealized PnL."""
        unreal = self.qty_signed * (self.price - self.en_pos) if self.qty_signed != 0.0 else 0.0
        return self.cash + self.margin + unreal

    # -- QC parity helpers (V12 verbatim) ------------------------------------
    def _v(self, why: str) -> bool:
        """`_v` veto counter."""
        self.count[why] = self.count.get(why, 0) + 1
        return False

    def _ae(self) -> float:
        """`_ae`."""
        return max(5.0, float(self.equity()))

    def _rpx(self, sym, px) -> float:
        """`_rpx` (single-symbol port: BTCUSDT tick = 0.01)."""
        step = TICK if TICK > 0 else 1e-6
        return round(round(float(px) / step) * step, 8)

    def _rq(self, sym, q, px) -> float:
        """`_rq` (single-symbol port: BTCUSDT lot 0.001, mn 5.5)."""
        lot = LOT
        q = math.floor(abs(float(q)) / lot) * lot
        mn = MN
        return round(q, 6) if (q >= lot and q * px >= mn) else 0.0

    def _rpct(self, ap: bool) -> float:
        """`_rpct` (verbatim — updates self.pk peak equity as a side effect)."""
        ae = self._ae()
        self.pk = max(self.pk, ae)
        dd = max(0.0, (self.pk - ae) / self.pk)
        bs = (0.048 if ap else 0.035) if self.mode == "TURBO" else (0.040 if ap else 0.028)
        return bs * (1.0 if dd < 0.12 else max(0.25, (1.0 - dd) ** 2.6))

    def _regime(self):
        """`_regime` (verbatim — single-symbol universe)."""
        if self._rt == self.now:
            return self._rv
        act = bull = bear = 0
        for x in self.st.values():
            if x.b4 < 10 or x.mem.e50 <= 0:
                continue
            px = float(self.price or 0.0)
            if px <= 0:
                continue
            act += 1
            if px > x.mem.e50 and x.mem.e20 >= x.mem.e50 * 0.995:
                bull += 1
            elif px < x.mem.e50 and x.mem.e20 <= x.mem.e50 * 1.005:
                bear += 1
        if act == 0:
            v = ("MIXED", 0.5, 0.5)
        else:
            b, r = bull / act, bear / act
            v = ("BULL_RALLY" if b >= 0.55 else ("BEAR_CASCADE" if r >= 0.60 else "MIXED"), b, r)
        self._rt, self._rv = self.now, v
        return v

    def _allowed(self, s: SymState, sd: int, c: float) -> bool:
        """`_allowed` (verbatim)."""
        reg = self._regime()[0]
        if sd == -1:
            if not self.shorts or reg == "BULL_RALLY":
                return False
            if s.mem.e50 > 0 and c > s.mem.e50:
                return False
            if self.btc is not None:
                bt = self.st[self.btc]
                if bt.sd4 == 1 and bt.ker4 > 0.45:
                    return False
        elif reg == "BEAR_CASCADE" and s.mem.e50 > 0 and c < s.mem.e50 and s.sd4 == -1:
            return False
        return True

    def _can(self, s: SymState, sd: int = 0) -> bool:
        """`_can` (verbatim)."""
        if self._invested() or s.pend:
            return False
        n = ns = 0
        for x in self.st.values():
            if x.pend or (self._invested() and x.ph == 0):
                n += 1
                if sd != 0 and x.sd == sd:
                    ns += 1
        return n < self.maxp and ns < 4

    def _orisk(self) -> float:
        """`_orisk` (verbatim)."""
        t = 0.0
        for x in self.st.values():
            if x.sd != 0 and x.ph == 0 and x.rd > 0:
                t += x.qty * x.rd
        return t / self._ae()

    def _target(self, s: SymState, sd: int, en: float, rd: float, min_r: float):
        """`_target` (verbatim)."""
        m = s.mem
        if sd == 1:
            w = sorted([(p, n) for p, n in ((s.pwh, "PWH"), (s.pdh, "PDH"), (m.hi(30), "H30")) if en + 0.5 * rd < p < 1e17])
        else:
            w = sorted([(p, n) for p, n in ((s.pwl, "PWL"), (s.pdl, "PDL"), (m.lo(30), "L30")) if 0 < p < en - 0.5 * rd], reverse=True)
        if not w:
            return 0.0, 0.0, "OPEN"
        p, n = w[0]
        r = abs(p - en) / rd
        if r < min_r:
            return None, 0.0, n
        r = min(r, 25.0)
        return en + sd * r * rd, r, n

    def _score(self, s: SymState, sd: int, c: float, cf: float, tg: str) -> float:
        """`_score` (verbatim)."""
        reg, b, r = self._regime()
        m = s.mem
        co = 1.0 if m.coiled(c, sd) else 0.3
        al = 1.0 if ((sd == 1 and c > m.e20 >= m.e50) or (sd == -1 and c < m.e20 <= m.e50)) else 0.3
        aw = 0.15 if tg[:4] in ("ARM1", "ARM2") else 0.05
        return min(1.0, 0.30 * (b if sd == 1 else r) + 0.25 * co + 0.25 * al + 0.20 * cf + aw)

    def _gate(self, s: SymState, c: float) -> bool:
        """`_gate` (verbatim)."""
        reg = self._regime()[0]
        m, sd = s.mem, s.sd
        if sd == 1 and reg == "BULL_RALLY" and c > m.e20 >= m.e50:
            return True
        if sd == -1 and reg == "BEAR_CASCADE" and c < m.e20 <= m.e50:
            return True
        inf = 0.18 * min(3, s.if_bos) + 0.15 * min(3, s.if_fvg) + 0.12 * min(2, s.if_vol)
        if m.coiled(c, sd):
            inf += 0.25
        return 0.45 * s.score + 0.55 * inf >= 0.62

    # -- orders (ImmediateFillModel simulation) ------------------------------
    def _live(self, tk) -> bool:
        """`_live`."""
        return tk is not None and tk["status"] not in ("FILLED", "CANCELED", "INVALID")

    def _on_order_event(self, od: dict) -> None:
        """`on_order_event` (statuses are strings; tickets are dicts)."""
        s = self.s
        tag = od.get("tag") or ""
        inv = self._invested()
        st = od["status"]
        if st == "INVALID":
            if self.nbad < 20:
                self.nbad += 1
                self._log("QC_LOG", msg="INVALID %s %s" % (SYMBOL, tag))
            if tag.startswith("EN_"):
                self.cd[SYMBOL] = self.now + pd.Timedelta(hours=1)
                if not inv:
                    self._rst(s)
            elif tag.startswith("SL_") and inv:
                s.sltk = None
                self._exit(s, "SL_INVALID")
            return
        if st == "CANCELED":
            if tag.startswith("EN_") and not inv:
                self._rst(s)
            return
        if st != "FILLED":
            return
        if tag.startswith("EN_") and s.pend:
            s.pend, s.entk = False, None
            s.en = float(od["fill_price"])
            s.qty = abs(float(self.qty_signed))
            s.sd = 1 if od["fill_quantity"] > 0 else -1
            s.rd = abs(s.en - s.sl)
            if s.rd <= 0 or s.qty <= 0:
                self._exit(s, "BAD_FILL")
                return
            s.min_r = 3.0 + 4.0 * FEE * s.en / s.rd
            s.peak, s.e4 = s.en, s.b4
            self._sync_sl(s)
            self._log("QC_LOG", msg=(
                "ENTER %s %s %s px=%.6g stop=%.2f%% tp=%.1fR(%s) minR=%.2f %s" % (
                    SYMBOL, "LONG" if s.sd == 1 else "SHORT", s.eng, s.en,
                    100.0 * s.rd / s.en, s.tpr, s.wall, s.min_r, s.story)))
            # harness: attach risk fields to the trade record created at fill
            if self.cur_trade is not None:
                ct = self.cur_trade
                ct["r_price"] = round(s.rd, 6)
                ct["risk_usd"] = round(s.rd * s.qty, 4)
                ct["sl_at_entry"] = round(s.sl, 6)
                ct["min_r_at_entry"] = round(s.min_r, 6)
            return
        if (tag.startswith("SL_") or tag.startswith("X_")) and not inv:
            self._fin(s, float(od["fill_price"]), tag)

    def _market_fill(self, qty_signed: float, tag: str) -> dict:
        """ImmediateFillModel market order at the current price."""
        fill = self.price
        self._order_seq += 1
        od = {"id": self._order_seq, "tag": tag, "status": "FILLED",
              "fill_price": fill, "fill_quantity": qty_signed}
        self._orders[od["id"]] = od
        if tag.startswith("EN_"):
            absq = abs(qty_signed)
            notional = absq * fill
            fee = notional * FEE_RATE
            margin_req = notional / LEVERAGE
            self.cash -= margin_req + fee
            self.margin = margin_req
            self.qty_signed = qty_signed
            self.en_pos = fill
            self.fees_total += fee
            self._open_trade(self.pending_meta, qty_signed, fill, fee, margin_req)
        else:
            absq = abs(self.qty_signed)
            fee = absq * fill * FEE_RATE
            realized = self.qty_signed * (fill - self.en_pos)
            self.cash += self.margin + realized - fee
            self.margin = 0.0
            self.qty_signed = 0.0
            self.en_pos = 0.0
            self.fees_total += fee
        self._on_order_event(od)
        return od

    def _stop_fill(self, fill_price: float, tag: str) -> dict:
        """Resting stop_market_order fill (portfolio close + SL_ event)."""
        self._order_seq += 1
        absq = abs(self.qty_signed)
        fee = absq * fill_price * FEE_RATE
        realized = self.qty_signed * (fill_price - self.en_pos)
        self.cash += self.margin + realized - fee
        self.margin = 0.0
        self.qty_signed = 0.0
        self.en_pos = 0.0
        self.fees_total += fee
        od = {"id": self._order_seq, "tag": tag, "status": "FILLED",
              "fill_price": fill_price, "fill_quantity": 0.0}
        self._orders[od["id"]] = od
        if self.s.sltk is not None:
            self.s.sltk["status"] = "FILLED"
        self._on_order_event(od)
        return od

    def _place_stop(self, qty: float, slp: float, tag: str) -> dict:
        """`stop_market_order` — resting order (status NEW)."""
        self._order_seq += 1
        od = {"id": self._order_seq, "tag": tag, "status": "NEW",
              "price": slp, "qty": qty}
        self._orders[od["id"]] = od
        return od

    def _cancel_order(self, od: dict) -> None:
        if od is None or od["status"] in ("FILLED", "CANCELED", "INVALID"):
            return
        od["status"] = "CANCELED"
        # reporting counters only (no decision feedback)
        if od["tag"].startswith("EN_"):
            self._cnt("ENT_CANCELLED")
        elif od["tag"].startswith("SL_"):
            self._cnt("SL_CANCELLED")
        self._on_order_event(od)

    def _update_stop_price(self, od: dict, slp: float) -> bool:
        """QC update_stop_price: succeeds in backtesting."""
        od["price"] = slp
        return True

    def _sync_sl(self, s: SymState) -> None:
        """`_sync_sl` (verbatim)."""
        if not self._invested() or s.sd == 0 or s.closing:
            return
        q = abs(float(self.qty_signed))
        px = float(self.price or s.en)
        slp = self._rpx(s.sym, s.sl)
        if s.sd * (px - slp) <= 0:
            self._exit(s, "SL_CROSSED")
            return
        if self._live(s.sltk):
            try:
                r = self._update_stop_price(s.sltk, slp)
                if r:
                    return
            except Exception:
                pass
            self._cancel_order(s.sltk)
        s.sltk = self._place_stop(-q if s.sd == 1 else q, slp, tag="SL_" + s.eng)

    def _raise(self, s: SymState, nsl: float, c: float) -> None:
        """`_raise` (verbatim)."""
        if s.closing or s.sd == 0:
            return
        nsl = self._rpx(s.sym, nsl)
        if s.sd * (nsl - s.sl) <= 0:
            return
        if s.sd * (c - nsl) <= 0:
            self._exit(s, "STOP_CROSSED")
            return
        s.sl = nsl
        self._sync_sl(s)

    def _exit(self, s: SymState, why: str) -> None:
        """`_exit` + liquidate at current price."""
        if s.closing:
            return
        s.closing, s.cb = True, s.b5
        if self._live(s.sltk):
            self._cancel_order(s.sltk)
        s.sltk = None
        if self.qty_signed != 0.0:
            self._market_fill(-self.qty_signed, tag="X_" + why)

    def _rst(self, s: SymState) -> None:
        """`_rst` (verbatim — only sltk is cancelled, as in QC)."""
        if self._live(s.sltk):
            self._cancel_order(s.sltk)
        s.sltk, s.entk = None, None
        s.eng, s.wall, s.story, s.sd, s.ph = "", "", "", 0, 0
        s.en = s.sl = s.tp = s.tpr = s.min_r = s.rd = s.qty = s.mfe = s.peak = s.score = 0.0
        s.pend = s.closing = False
        s.if_bos = s.if_fvg = s.if_vol = 0

    def _fin(self, s: SymState, px: float, tag: str) -> None:
        """`_fin` (verbatim stats/cooldown) + trade-record close (harness)."""
        if s.sd == 0:
            return
        r = s.sd * (px - s.en) / s.rd if s.rd > 0 else 0.0
        net = r - (FEE * s.en / s.rd if s.rd > 0 else 0.0)
        st = self.stats.setdefault(s.eng, [0, 0.0, 0])
        st[0] += 1
        st[1] += net
        st[2] += 1 if net > 0 else 0
        self._log("QC_LOG", msg=(
            "EXIT %s %s %s Rnet=%.2f mfe=%.2f ph=%d t=%s" % (
                SYMBOL, s.eng, tag, net, s.mfe, s.ph, self.now.strftime("%m-%d %H:%M"))))
        if net < 0:
            self.cd[SYMBOL] = self.now + pd.Timedelta(hours=4)
        # ---- trade record close (harness) ----
        rec_tag = tag[2:] if tag.startswith("X_") else tag
        if self.cur_trade is not None:
            ct = self.cur_trade
            exit_fee = s.qty * px * FEE_RATE
            realized = s.sd * s.qty * (px - s.en)
            ct["exit_time"] = self.now
            ct["exit_price"] = round(px, 6)
            ct["exit_qty"] = s.qty
            ct["exit_tag"] = rec_tag
            ct["exit_fee"] = round(exit_fee, 4)
            ct["realized"] = round(realized, 4)
            ct["net_pnl"] = round(realized - ct["entry_fee"] - exit_fee, 4)
            ct["code_rnet"] = round(net, 4)
            ct["mfe_at_exit"] = round(s.mfe, 4)
            ct["ph_at_exit"] = s.ph
            ct["be_locked_at_exit"] = None
            risk = ct.get("risk_usd")
            ct["r_multiple"] = round(ct["net_pnl"] / risk, 2) if risk else None
            if ct.get("r_price"):
                ct["mfe_r"] = round(s.mfe, 2)
                if ct.get("mae_min") is not None:
                    adverse = (ct["mae_min"] - ct["entry_price"]) if s.sd == -1 else (ct["entry_price"] - ct["mae_min"])
                    ct["mae_r"] = round(adverse / ct["r_price"], 2)
                else:
                    ct["mae_r"] = None
            ct["equity_after"] = round(self.equity(), 2)
            self.trades.append(ct)
            self.cur_trade = None
        self._rst(s)

    # -- entry (`_sub` verbatim) ---------------------------------------------
    def _sub(self, s: SymState, sd: int, en0: float, sl: float, tg: str, cf: float) -> bool:
        """`_sub` (verbatim) + ImmediateFillModel market fill + reporting meta."""
        if s.sym in self.cd and self.now < self.cd[s.sym]:
            return self._v("COOLDOWN")
        if not self._can(s, sd):
            return self._v("SLOTS_FULL")
        tx = float(self.price or en0)
        if tx <= 0 or not self._allowed(s, sd, tx):
            return self._v("COUNTER_REGIME")
        need = s.sw4.cnl if sd == 1 else s.sw4.cnh
        if need <= s.mk[sd]:
            return self._v("SAME_WAVE")
        fm = float(self._margin_remaining())
        if fm < 2.0:
            return self._v("NO_MARGIN")
        en, sl = self._rpx(s.sym, tx), self._rpx(s.sym, sl)
        rd = sd * (en - sl)
        if rd <= 0:
            return self._v("BAD_STOP")
        a1, a4 = s.sw1.atr(), s.sw4.atr()
        if rd < a1:
            return self._v("STOP_INSIDE_NOISE")
        if rd > 4.0 * a4:
            return self._v("STOP_TOO_WIDE")
        min_r = 3.0 + 4.0 * FEE * en / rd
        tp, tpr, wall = self._target(s, sd, en, rd, min_r)
        if tp is None:
            return self._v("WALL_UNDER_3R_NET")
        ae = self._ae()
        dd = max(0.0, (self.pk - ae) / self.pk)
        eb = ae if dd < 0.14 else max(ae * 0.50, min(self.wse, ae))
        ap = cf >= 0.78
        sc = self._score(s, sd, en, cf, tg)
        rk = eb * self._rpct(ap) * (0.85 + 0.35 * max(0.0, min(1.0, 0.5 * cf + 0.5 * sc)))
        room = self.rbudget - self._orisk()
        if room <= 0.002:
            return self._v("RISK_BUDGET")
        rk = min(rk, room * ae)
        lev = 3.2 if (ap and dd < 0.10) else (2.4 if ap else 1.8)
        notional = min(rk / (rd / en + 0.0012), eb * lev, fm * 5.8)
        if notional < 5.5:
            return self._v("NOTIONAL_TOO_SMALL")
        q = self._rq(s.sym, notional / en, en)
        if q <= 0:
            return self._v("LOT_SIZE")
        reg, b, r = self._regime()
        s.eng, s.sd, s.sl, s.en, s.rd = tg, sd, sl, en, rd
        s.tp, s.tpr, s.wall, s.min_r, s.a1 = tp, tpr, wall, min_r, a1
        s.qty, s.mfe, s.peak, s.ph, s.closing = q, 0.0, en, 0, False
        s.score, s.if_bos, s.if_fvg, s.if_vol = sc, 0, 0, 0
        s.story = "%s br=%.2f cf=%.2f sc=%.2f" % (reg, b if sd == 1 else r, cf, sc)
        s.pend, s.eb = True, s.b5
        s.mk[sd] = need
        # reporting meta (harness only — built before the order, as in QC state set)
        self.pending_meta = {
            "signal_time": self.now,
            "eng": tg,
            "side": "LONG" if sd == 1 else "SHORT",
            "story": s.story,
            "score": round(sc, 4),
            "cf_at_signal": round(cf, 4),
            "tpr": round(tpr, 4),
            "wall": wall,
            "min_r": round(min_r, 4),
            "a1": round(a1, 6),
            "sl_at_signal": round(sl, 6),
            "en_at_signal": round(en, 6),
            "rd_at_signal": round(rd, 6),
            "tp_at_signal": round(tp, 6),
            "mode_at_entry": self.mode,
            "regime_at_entry": reg,
            "dd_at_signal": round(dd, 4),
            "eb_at_signal": round(eb, 2),
            "rk_at_signal": round(rk, 4),
            "notional_target": round(notional, 2),
            "lev_at_entry": lev,
            "equity_at_signal": round(ae, 2),
        }
        # tk = market_order(...) — ImmediateFillModel -> FILLED at current price
        qty_signed = q if sd == 1 else -q
        tk = self._market_fill(qty_signed, tag="EN_" + tg)
        if tk is None or tk["status"] == "INVALID":
            self._rst(s)
            self.cd[s.sym] = self.now + pd.Timedelta(hours=1)
            return False
        if tk["status"] not in ("FILLED", "CANCELED", "INVALID"):
            s.entk = tk
        self._cnt("entries_placed")
        return True

    def _margin_remaining(self) -> float:
        """portfolio.margin_remaining ≈ equity*10 - initial margin used (LEAN InitialMargin model)."""
        return max(0.0, self.equity() * LEVERAGE - self.margin)

    # -- management (verbatim) ------------------------------------------------
    def _lock(self, s: SymState, c: float, ph: int) -> None:
        s.ph = ph
        self._raise(s, s.en + s.sd * (s.min_r + 0.02) * s.rd, c)

    def _m5(self, s: SymState, h: float, l: float, c: float) -> None:
        """`_m5` (verbatim)."""
        sd = s.sd
        if sd == 0 or s.rd <= 0:
            return
        if s.closing:
            if s.b5 - s.cb > 3:
                s.cb = s.b5
                if self.qty_signed != 0.0:
                    self._market_fill(-self.qty_signed, tag="X_RETRY")
            return
        ext = h if sd == 1 else l
        s.peak = max(s.peak, h) if sd == 1 else min(s.peak, l)
        s.mfe = max(s.mfe, sd * (ext - s.en) / s.rd)
        if not self._live(s.sltk):
            self._sync_sl(s)
            if s.closing:
                return
        if s.ph < 2 and s.tp > 0 and sd * (ext - s.tp) >= 0:
            if self._gate(s, c):
                self._lock(s, c, 2)
            else:
                self._exit(s, "TARGET_%.1fR_%s" % (s.tpr, s.wall))
            return
        if s.ph == 0 and sd * (ext - (s.en + sd * (s.min_r * s.rd + s.a1))) >= 0:
            self._lock(s, c, 2 if self._gate(s, c) else 1)

    def _trail(self, s: SymState, c: float, is4: bool) -> None:
        """`_trail` (verbatim)."""
        if s.ph == 0 or s.closing or s.sd == 0 or s.rd <= 0:
            return
        if is4 and s.ph == 1 and self._gate(s, c):
            s.ph = 2
        if s.ph == 2 and is4:
            m = max(12, min(84, (s.b4 - s.e4) // 3))
            seg, pad = list(s.q4)[-m:], 1.5 * s.sw4.atr()
        elif s.ph == 1 and not is4:
            seg, pad = list(s.q1)[-8:], 0.5 * s.sw1.atr()
        else:
            return
        lvl = (min(x.low for x in seg) - pad) if s.sd == 1 else (max(x.high for x in seg) + pad)
        self._raise(s, lvl, c)

    # -- 5m resting-stop check (base resolution) ------------------------------
    def check_stop_5m(self, bar: Bar) -> None:
        """Resting stop_market_order checked on EVERY completed 5m bar.

        Long: `low <= sl` fills at `min(open, sl)`.
        Short: `high >= sl` fills at `max(open, sl)`.
        """
        if self.is_warming_up:
            return
        s = self.s
        if s.sd == 0 or s.rd <= 0 or not self._invested() or s.closing:
            return
        slp = self._rpx(s.sym, s.sl)
        fill = None
        if s.sd == 1 and bar.low <= slp:
            fill = min(bar.open, slp)
        elif s.sd == -1 and bar.high >= slp:
            fill = max(bar.open, slp)
        if fill is None:
            return
        tag = s.sltk["tag"] if self._live(s.sltk) else ("SL_" + s.eng)
        self._log("STOP_5M", tag=tag, sl=slp, fill=fill)
        self._stop_fill(fill, tag)

    # -- tracking (harness) ---------------------------------------------------
    def _track_extremes(self, bar: Bar) -> None:
        t = self.cur_trade
        if t is None:
            return
        # side-aware: mfe_max = most favorable price reached, mae_min = most adverse
        if self.s.sd == -1:
            if bar.low < t["mfe_max"]:
                t["mfe_max"] = bar.low
            if bar.high > t["mae_min"]:
                t["mae_min"] = bar.high
        else:
            if bar.high > t["mfe_max"]:
                t["mfe_max"] = bar.high
            if bar.low < t["mae_min"]:
                t["mae_min"] = bar.low

    def _open_trade(self, meta: dict, qty_signed: float, fill: float,
                    fee: float, margin_req: float) -> None:
        if self.cur_trade is not None:
            self._fin(self.s, fill, "SUPERSEDED")
        self._trade_seq += 1
        absq = abs(qty_signed)
        cost = absq * fill
        self.cur_trade = {
            "trade_id": self._trade_seq,
            "symbol": SYMBOL,
            **meta,
            "entry_time": self.now,
            "entry_price": round(fill, 6),
            "entry_qty": absq,
            "entry_notional": round(cost, 2),
            "entry_fee": round(fee, 4),
            "margin_used": round(margin_req, 4),
            "r_price": None,
            "risk_usd": None,
            "sl_at_entry": None,
            "min_r_at_entry": None,
            "equity_at_entry": round(self.equity(), 2),
            "exit_time": None,
            "exit_price": None,
            "exit_qty": None,
            "exit_tag": None,
            "exit_fee": None,
            "realized": None,
            "net_pnl": None,
            "code_rnet": None,
            "r_multiple": None,
            "mfe_at_exit": None,
            "ph_at_exit": None,
            "mfe_r": None,
            "mae_r": None,
            "equity_after": None,
            "mfe_max": fill,
            "mae_min": fill,
        }

    # -- 4H callback (V12 verbatim) -------------------------------------------
    def _on_4h(self, bar: Bar) -> None:
        s = self.s
        s.b4 += 1
        s.q4.append(bar)
        s.v4.append(float(bar.volume))
        h, l, c, o = float(bar.high), float(bar.low), float(bar.close), float(bar.open)
        s.mem.on4h(c)
        s.sw4.update(h, l, c)
        s.ker4 = s.sw4.ker(10)
        if len(s.q4) < 16:
            return
        atr = s.sw4.atr()
        psh, psl = s.sh4, s.sl4
        if s.sh4 == 0.0:
            s.sh4, s.sl4 = max(x.high for x in s.q4), min(x.low for x in s.q4)
        if s.sw4.ah:
            s.sh4 = s.sw4.ah[-1][1]
        if s.sw4.al:
            s.sl4 = s.sw4.al[-1][1]
        fb = 0
        if psh > 0 and c > psh:
            s.sd4, s.sh4, fb = 1, h, 1
        elif psl > 0 and c < psl:
            s.sd4, s.sl4, fb = -1, l, -1
        rv = float(bar.volume) / max(sum(s.v4) / len(s.v4), 1e-8)
        if self._invested():
            if fb == s.sd:
                s.if_bos += 1
            if rv >= 1.25 and ((s.sd == 1 and c > o) or (s.sd == -1 and c < o)):
                s.if_vol += 1
            if not self.is_warming_up:
                self._trail(s, c, True)
            return
        if self.is_warming_up:
            return
        if fb != 0 and ((fb == 1 and c > o) or (fb == -1 and c < o)) and self._allowed(s, fb, c):
            n5 = list(s.q4)[-5:]
            sl = (min(x.low for x in n5) - 0.45 * atr) if fb == 1 else (max(x.high for x in n5) + 0.45 * atr)
            cf = min(0.95, 0.62 + (0.15 if s.ker4 > 0.36 else 0.0) + (0.12 if rv > 1.10 else 0.0))
            s.g4 = (fb, sl, cf, s.b4)

    # -- 1H callback (V12 verbatim) --------------------------------------------
    def _on_1h(self, bar: Bar) -> None:
        s = self.s
        s.b1 += 1
        s.q1.append(bar)
        s.v1.append(float(bar.volume))
        h, l, c, o = float(bar.high), float(bar.low), float(bar.close), float(bar.open)
        s.mem.on1h(c)
        s.sw1.update(h, l, c)
        if len(s.q1) < 16:
            return
        a1 = s.sw1.atr()
        psh, psl = s.sh1, s.sl1
        if s.sw1.ah:
            s.sh1 = s.sw1.ah[-1][1]
        if s.sw1.al:
            s.sl1 = s.sw1.al[-1][1]
        fb = 0
        if psh > 0 and c > psh:
            s.sd1, fb = 1, 1
        elif psl > 0 and c < psl:
            s.sd1, fb = -1, -1
        if self._invested():
            if fb == s.sd:
                s.if_bos += 1
            if not self.is_warming_up:
                self._trail(s, c, False)
            return
        if s.sd4 == 1 and l <= max(s.mem.h20 * 1.008, s.sl1 * 1.015):
            s.armed = True
        elif s.sd4 == -1 and h >= min(s.mem.h20 * 0.992, s.sh1 * 0.985 if s.sh1 > 0 else 1e18):
            s.armed = True
        if self.is_warming_up:
            return
        pb = s.q1[-2]
        sd = s.sd4
        if (s.armed or fb != 0) and sd != 0 and self._allowed(s, sd, c):
            up = sd == 1 and c > o and c > float(pb.high) and c > s.mem.h20
            dn = sd == -1 and c < o and c < float(pb.low) and c < s.mem.h20
            if up or dn:
                s.armed = False
                q8 = list(s.q1)[-8:]
                sl = (min(x.low for x in q8) - 0.55 * a1) if sd == 1 else (max(x.high for x in q8) + 0.55 * a1)
                s.g1 = (sd, sl, min(0.94, 0.68 + 0.20 * s.sw1.ker(10)), s.b1)

    # -- 15M callback (V12 verbatim) --------------------------------------------
    def _on_15m(self, bar: Bar) -> None:
        s = self.s
        s.b15 += 1
        s.q15.append(bar)
        s.v15.append(float(bar.volume))
        h, l, c, o = float(bar.high), float(bar.low), float(bar.close), float(bar.open)
        s.sw15.update(h, l, c)
        if len(s.q15) < 8:
            return
        a15 = s.sw15.atr()
        a1 = max(s.sw1.atr(), a15 * 1.8)
        rv = float(bar.volume) / max(sum(s.v15) / len(s.v15), 1e-8)
        b0, b2 = s.q15[-1], s.q15[-3]
        fu = b0.low > b2.high and (b0.low - b2.high) > 0.15 * a15
        fd = b0.high < b2.low and (b2.low - b0.high) > 0.15 * a15
        if self._invested():
            if (s.sd == 1 and fu) or (s.sd == -1 and fd):
                s.if_fvg += 1
            return
        if self.is_warming_up:
            return
        k = s.sw15.ker(8)
        for lvl, sd in ((s.pdl, 1), (s.pwl, 1), (s.sl1, 1), (s.pdh, -1), (s.pwh, -1), (s.sh1, -1)):
            if lvl <= 0 or lvl >= 1e17:
                continue
            if self._allowed(s, sd, c):
                sc = s.sw15.swp_rec(o, h, l, c, lvl, sd, a15)
                if sc > 0.48:
                    qb = list(s.q1)[-6:] if len(s.q1) >= 6 else list(s.q15)[-12:]
                    sl = (min(l, min(x.low for x in qb)) - 0.5 * a1) if sd == 1 else (max(h, max(x.high for x in qb)) + 0.5 * a1)
                    s.gs = (sd, sl, min(0.94, 0.62 + 0.30 * sc), s.b15)
                    break
            bd = -sd
            if k > 0.48 and rv > 1.25 and self._allowed(s, bd, c):
                qb = list(s.q1)[-5:] if len(s.q1) >= 5 else list(s.q15)[-10:]
                if bd == 1 and o <= lvl and c > lvl + 0.2 * a15 and (c - o) > 0.5 * (h - l):
                    s.gi = (1, min(l, min(x.low for x in qb)) - 0.45 * a1, min(0.95, 0.68 + 0.22 * k), s.b15)
                    break
                if bd == -1 and o >= lvl and c < lvl - 0.2 * a15 and (o - c) > 0.5 * (h - l):
                    s.gi = (-1, max(h, max(x.high for x in qb)) + 0.45 * a1, min(0.95, 0.68 + 0.22 * k), s.b15)
                    break

    # -- 5M callback (V12 verbatim) ---------------------------------------------
    def _on_5m(self, bar: Bar) -> None:
        s = self.s
        s.b5 += 1
        h, l, c, o = float(bar.high), float(bar.low), float(bar.close), float(bar.open)
        s.mem.on5(h, l)
        dt = bar.end_time
        if dt.day != s.cday:
            if s.cday != -1:
                s.pdh, s.pdl = s.dh, s.dl
                s.mem.push(s.dh, s.dl)
            s.cday, s.dh, s.dl = dt.day, h, l
        else:
            s.dh, s.dl = max(s.dh, h), min(s.dl, l)
        wk = dt.isocalendar()[1]
        if wk != s.cwk:
            if s.cwk != -1:
                s.pwh, s.pwl = s.wh, s.wl
            s.cwk, s.wh, s.wl = wk, h, l
        else:
            s.wh, s.wl = max(s.wh, h), min(s.wl, l)
        if self.is_warming_up:
            return
        if s.p0 == 0.0:
            s.p0 = c
        inv = self._invested()
        if s.pend and s.b5 - s.eb > 6:
            if self._live(s.entk):
                self._cancel_order(s.entk)
            self._cnt("ENT_TIMEOUT")
            s.pend, s.entk = False, None
            if not inv:
                self._rst(s)
        if inv:
            self._track_extremes(bar)
            self._m5(s, h, l, c)
            return
        if s.sd != 0 and not s.pend:
            self._fin(s, c, "SYNC")
        if not self._can(s):
            return
        for at, tg, cn, mx in (("g4", "ARM1_4H", "b4", 1), ("g1", "ARM2_1H", "b1", 1),
                               ("gi", "ARM3_IGN", "b15", 2), ("gs", "ARM4_SWP", "b15", 2)):
            sg = getattr(s, at)
            if sg is None:
                continue
            setattr(s, at, None)
            sd, sl, cf, bid = sg
            if getattr(s, cn) - bid > mx:
                continue
            if at == "gs" and not ((sd == 1 and c > o) or (sd == -1 and c < o)):
                self._v("SWP_NO_CONFIRM")
                continue
            if self._sub(s, sd, c, sl, tg, cf):
                return

    # -- weekly mode switch (on_data verbatim) ---------------------------------
    def on_data_weekly(self) -> None:
        """QC `on_data`: weekly TURBO/DAILY mode switch (runs last per bar)."""
        if self.is_warming_up:
            return
        wk = self.now.isocalendar()[1]
        if wk != self.lwk:
            ae = self._ae()
            if self.lwk != -1:
                self.mode = "TURBO" if (ae - self.wse) / max(self.wse, 1.0) >= 0.04 else "DAILY"
            self.wse, self.lwk = ae, wk

    # -- end of data ------------------------------------------------------------
    def close_eod(self) -> None:
        """Harness: flatten any open position at the final price (tag EOD)."""
        s = self.s
        if s.pend:
            if self._live(s.entk):
                self._cancel_order(s.entk)
            s.pend, s.entk = False, None
            if not self._invested():
                self._rst(s)
        if s.sd != 0 and self._invested():
            self._exit(s, "EOD")

    def end_of_algorithm(self) -> dict:
        """`on_end_of_algorithm` summary (harness: structured instead of log lines)."""
        eng_stats = {
            k: {"n": v[0], "avgRnet": round(v[1] / max(1, v[0]), 4),
                "win_pct": round(100.0 * v[2] / max(1, v[0]), 1)}
            for k, v in sorted(self.stats.items())
        }
        s = self.s
        bh = []
        px = float(self.price or 0.0)
        if s.p0 > 0 and px > 0:
            bh.append(px / s.p0 - 1.0)
        out = {
            "vetoes": dict(sorted(self.count.items())),
            "engines": eng_stats,
            "bh_ew_pct": round(100.0 * sum(bh) / len(bh), 2) if bh else None,
            "fees_total": round(self.fees_total, 4),
            "equity": round(self.equity(), 2),
            "mode_final": self.mode,
        }
        self._log("QC_LOG", msg="VETOES " + " ".join("%s=%d" % kv for kv in sorted(self.vt.items())) if self.vt else "VETOES")
        return out


# ---------------------------------------------------------------------------
# Backtest runner (zero-lookahead: causal resample + 5m stop/entry rules)
# ---------------------------------------------------------------------------
def run_backtest(
    data_dir: str,
    start: str,
    end: str,
    warmup_days: int = 35,
    capital: float = 100.0,
) -> dict:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from engine.causal_primitives import load_asset_ohlcv, resample_causal_tf

    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)          # inclusive upper bound on bar END times
    if start_ts.tzinfo is None:
        start_ts = start_ts.tz_localize("UTC")
    if end_ts.tzinfo is None:
        end_ts = end_ts.tz_localize("UTC")
    warm_start = start_ts - pd.Timedelta(days=warmup_days)

    stems = [str(y) for y in range(warm_start.year, end_ts.year + 1)]
    df = load_asset_ohlcv(Path(data_dir), include_stems=stems)
    df = df[(df.index >= warm_start) & (df.index <= end_ts)]
    if df.empty:
        raise RuntimeError("no data in window")

    tf15 = resample_causal_tf(df, "15m")
    tf1 = resample_causal_tf(df, "1h")
    tf4 = resample_causal_tf(df, "4h")

    def _vol_of(tf_df: pd.DataFrame, freq: str) -> dict:
        """Causal volume sums on the exact same left-closed bins as resample_causal_tf."""
        # same freq normalization as the engine's norm_map ("15m" -> "15min")
        rule = {"5m": "5min", "15m": "15min", "30m": "30min"}.get(freq, freq)
        v = df["Volume"].resample(rule, label="left", closed="left").sum()
        v.index = v.index + pd.Timedelta(rule)
        v = v.reindex(tf_df.index).fillna(0.0)
        return {t: float(v.loc[t]) for t in tf_df.index}

    v15, v1, v4 = _vol_of(tf15, "15m"), _vol_of(tf1, "1h"), _vol_of(tf4, "4h")
    m15 = {t: r for t, r in tf15.iterrows()}
    m1 = {t: r for t, r in tf1.iterrows()}
    m4 = {t: r for t, r in tf4.iterrows()}

    eng = FuturesEngine(start=start_ts, capital=capital)

    idx5 = df.index
    n = len(idx5)
    for i in range(n):
        st = idx5[i]
        t = st + pd.Timedelta(minutes=5)          # 5m bar end_time
        if t > end_ts:
            break
        row = df.iloc[i]
        bar = Bar(end_time=t, open=float(row.Open), high=float(row.High),
                  low=float(row.Low), close=float(row.Close), volume=float(row.Volume))
        eng.now = t
        eng.price = bar.close

        # (1) resting stop_market_order check (base-resolution analog)
        eng.check_stop_5m(bar)

        # (2) 5m consolidator (entries, management)
        eng._on_5m(bar)

        # (3..5) HTF consolidators in registration order
        r15 = m15.get(t)
        if r15 is not None:
            eng._on_15m(Bar(t, float(r15.Open), float(r15.High), float(r15.Low),
                            float(r15.Close), v15.get(t, 0.0)))
        r1 = m1.get(t)
        if r1 is not None:
            eng._on_1h(Bar(t, float(r1.Open), float(r1.High), float(r1.Low),
                           float(r1.Close), v1.get(t, 0.0)))
        r4 = m4.get(t)
        if r4 is not None:
            eng._on_4h(Bar(t, float(r4.Open), float(r4.High), float(r4.Low),
                           float(r4.Close), v4.get(t, 0.0)))

        # (6) weekly mode switch (QC on_data) — after consolidators (LEAN slice order)
        eng.on_data_weekly()

        # equity curve (trading period only)
        if t >= start_ts:
            eng._eq_rows = getattr(eng, "_eq_rows", [])
            eng._eq_rows.append({
                "time": t,
                "equity": round(eng.equity(), 4),
                "usdt": round(eng.cash, 4),
                "btc": eng.qty_signed,
                "price": bar.close,
                "in_position": bool(eng._invested() or eng.s.pend),
            })

    eng.now = end_ts
    eng.close_eod()
    if eng.cur_trade is not None:                 # safety net
        eng._fin(eng.s, eng.price, "EOD")
    end_log = eng.end_of_algorithm()

    equity = pd.DataFrame(getattr(eng, "_eq_rows", [])).set_index("time") if getattr(eng, "_eq_rows", None) else pd.DataFrame()
    return {
        "trades": eng.trades,
        "equity": equity,
        "events": eng.events,
        "count": eng.count,
        "end_log": end_log,
        "final_equity": eng.equity(),
        "final_usdt": eng.cash,
        "final_margin": eng.margin,
        "fees_total": round(eng.fees_total, 4),
        "start": start_ts,
        "end": end_ts,
        "capital": capital,
    }
