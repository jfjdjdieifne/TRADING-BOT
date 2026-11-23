"""V14 — faithful BTC-only port of the owner's pasted 6-arm code (2026-11-18).

Provenance: logic copied verbatim from the paste —
  TopoSwing k-window pivots (k=3/2, min separation, active break tracking),
  EMA/RSI/KER helpers, macro breadth (50/200 EMA across the basket), RS ranking,
  arms V8_4H / V11_1H / V10_IGN (squeeze) / V6_SWP / V9_LON / V12_CAP,
  _build_structural_sl clamps [2.6%-9.5%], min_rr = 3.50, sizing
  (base_risk 0.032 x conf x rs_boost x streak_mult, notional cap eb*0.34),
  management: BE@2.25R, TP@3.5R full-cash OR rally conversion (wave candidate),
  VC harvest stages 4.2/10/22R (35/25/25%), zigzag/macro-box trail,
  stagnant-capital cap, daily loss circuit (3/day), loss-streak sizing.

Harness adaptations (all disclosed in report §12):
  - SINGLE SYMBOL: only BTC candles exist in this project, so macro breadth and
    RS ranking degenerate to BTC-only (rs_rank always 1; macro_bull/bear are
    BTC's own 4h EMA state). The 9 other pairs stay untested (no data).
  - Fill model: market orders fill at the CLOSE of the completed 5m bar that
    triggered them (same instant QC consolidate handlers would fire) — causal.
  - Report ledger: 0.1%/side fees (identical to V13/V12/V5/V1 for comparison);
    the engine's internal realized_eq / streak ledger keeps their verbatim
    0.0008 single-side fee.
  - Leverage 3.0 and warmup 15 days are the pasted code's own settings.
  - One hardening: margin is validated BEFORE the position state is written
    (their on_order_event ordering could desync state on an order rejection).
"""

from __future__ import annotations

import json
import math
import os
import sys
from collections import deque
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

FEE_RATE = 0.001          # report ledger, per side (comparability with V13/V12/V5/V1)
INTERNAL_FEE = 0.0008     # their realized_eq / streak ledger, verbatim
LEVERAGE = 3.0            # their set: set_leverage(3.0)
LOT = 0.001
MIN_NOTIONAL = 5.5
MIN_QTY = 0.001

FULL_START, FULL_END = "2025-07-01", "2026-07-01"
H2_START, H2_END = "2025-07-01", "2026-01-01"
H1_START, H1_END = "2026-01-01", "2026-07-01"
CAPITAL = 100.0


# --------------------------------------------------------------------------- #
# TopoSwing — verbatim from the paste
# --------------------------------------------------------------------------- #
class TopoSwing:
    def __init__(self, k=3):
        self.k = k
        self.w = 2 * k + 1
        self.h = deque(maxlen=self.w)
        self.l = deque(maxlen=self.w)
        self.v = deque(maxlen=self.w)
        self.b = deque(maxlen=self.w)
        self.sh = deque(maxlen=40)
        self.sl = deque(maxlen=40)

    def update(self, hi, lo, vol, bar_idx, atr):
        self.h.append(hi)
        self.l.append(lo)
        self.v.append(vol)
        self.b.append(bar_idx)
        if len(self.h) < self.w:
            return
        c = self.k
        ch = self.h[c]
        cl = self.l[c]
        cb = self.b[c]
        cv = self.v[c]
        for x in self.sh:
            if not x["br"] and hi > x["p"]:
                x["br"] = True
        for x in self.sl:
            if not x["br"] and lo < x["p"]:
                x["br"] = True
        ih = all(ch >= self.h[i] for i in range(self.w) if i != c) and any(
            ch > self.h[i] for i in range(self.w) if i != c)
        il = all(cl <= self.l[i] for i in range(self.w) if i != c) and any(
            cl < self.l[i] for i in range(self.w) if i != c)
        min_d = max(atr * 0.35, ch * 0.002)
        if ih:
            if not self.sh or abs(ch - self.sh[-1]["p"]) >= min_d or (
                    cb - self.sh[-1]["b"]) >= self.k * 2:
                self.sh.append({"p": ch, "b": cb, "v": cv, "br": False})
        if il:
            if not self.sl or abs(cl - self.sl[-1]["p"]) >= min_d or (
                    cb - self.sl[-1]["b"]) >= self.k * 2:
                self.sl.append({"p": cl, "b": cb, "v": cv, "br": False})

    def active_highs(self, b, max_age=280):
        return [x for x in self.sh if not x["br"] and (b - x["b"]) <= max_age]

    def active_lows(self, b, max_age=280):
        return [x for x in self.sl if not x["br"] and (b - x["b"]) <= max_age]


# --------------------------------------------------------------------------- #
# SymState — verbatim + report-only bookkeeping
# --------------------------------------------------------------------------- #
class SymState:
    def __init__(self, sym):
        self.sym = sym
        self.b5 = 0
        self.b15 = 0
        self.b1h = 0
        self.b4h = 0
        self.o5 = deque(maxlen=120)
        self.h5 = deque(maxlen=120)
        self.l5 = deque(maxlen=120)
        self.c5 = deque(maxlen=120)
        self.v5 = deque(maxlen=120)
        self.h15 = deque(maxlen=80)
        self.l15 = deque(maxlen=80)
        self.c15 = deque(maxlen=80)
        self.v15 = deque(maxlen=80)
        self.o1h = deque(maxlen=140)
        self.h1h = deque(maxlen=140)
        self.l1h = deque(maxlen=140)
        self.c1h = deque(maxlen=140)
        self.v1h = deque(maxlen=140)
        self.o4h = deque(maxlen=240)
        self.h4h = deque(maxlen=240)
        self.l4h = deque(maxlen=240)
        self.c4h = deque(maxlen=240)
        self.v4h = deque(maxlen=240)
        self.topo5 = TopoSwing(k=3)
        self.topo15 = TopoSwing(k=3)
        self.topo1h = TopoSwing(k=2)
        self.topo4h = TopoSwing(k=2)
        self.atr5 = 0.0
        self.atr15 = 0.0
        self.atr1h = 0.0
        self.atr4h = 0.0
        self.ema20_5 = 0.0
        self.ema50_5 = 0.0
        self.ema20_1h = 0.0
        self.ema50_1h = 0.0
        self.ema200_1h = 0.0
        self.ema20_4h = 0.0
        self.ema50_4h = 0.0
        self.ema200_4h = 0.0
        self.rsi1h = 50.0
        self.rsi4h = 50.0
        self.ker5 = 0.5
        self.ker1h = 0.5
        self.rs_score = 0.0
        self.rs_rank = 5
        self.sd = 0
        self.arm = ""
        self.ep = 0.0
        self.sl = 0.0
        self.tp = 0.0
        self.ir = 0.0
        self.eb = 0
        self.mfe = 0.0
        self.mae = 0.0            # report-only: max adverse price excursion
        self.be = False
        self.rally = False
        self.vc_stage = 0
        self.zig_hl = 0.0
        self.cd_until = -1

    def reset_pos(self):
        self.sd = 0
        self.arm = ""
        self.ep = 0.0
        self.sl = 0.0
        self.tp = 0.0
        self.ir = 0.0
        self.eb = 0
        self.mfe = 0.0
        self.mae = 0.0
        self.be = False
        self.rally = False
        self.vc_stage = 0
        self.zig_hl = 0.0


# --------------------------------------------------------------------------- #
# Engine — the pasted QCAlgorithm, adapted to the causal harness
# --------------------------------------------------------------------------- #
class Engine:
    def __init__(self, start: pd.Timestamp, capital: float = CAPITAL,
                 cap_fix: bool = False):
        self.start = start
        self.cap_fix = cap_fix
        self.now = start
        self.price = 0.0
        self.is_warming_up = True
        self.st: dict[str, SymState] = {"BTC": SymState("BTC")}
        self.s = self.st["BTC"]
        self.maxp = 4
        self.base_risk = 0.032
        self.min_rr = 3.50
        self.realized_eq = capital
        self.peak_eq = capital
        self.macro_breadth = 0.50
        self.macro_bull = False
        self.macro_bear = False
        self.loss_streak = 0
        self.daily_losses = 0
        self.last_day = -1
        # harness ledger (report)
        self.cash = float(capital)
        self.margin = 0.0
        self.qty = 0.0
        self.ep = 0.0
        self.fees_total = 0.0
        self.trades: list[dict] = []
        self.cur_trade: dict | None = None
        self.events: list[dict] = []
        self.count: dict[str, int] = {}
        self._eq_rows: list[dict] = []
        self._trade_seq = 0

    # ---------------- helpers (verbatim math) ---------------- #
    def _ema(self, prev, val, n):
        if prev <= 0:
            return val
        k = 2.0 / (n + 1.0)
        return val * k + prev * (1.0 - k)

    def _atr(self, prev, h, l, pc, n=14):
        tr = max(h - l, abs(h - pc), abs(l - pc)) if pc > 0 else (h - l)
        if prev <= 0:
            return tr
        return (prev * (n - 1.0) + tr) / float(n)

    def _rsi(self, closes, n=14):
        if len(closes) < n + 1:
            return 50.0
        arr = list(closes)[-(n + 1):]
        gains = 0.0
        losses = 0.0
        for i in range(1, len(arr)):
            d = arr[i] - arr[i - 1]
            if d > 0:
                gains += d
            else:
                losses -= d
        if losses <= 1e-12:
            return 100.0
        rs = (gains / n) / (losses / n)
        return 100.0 - (100.0 / (1.0 + rs))

    def _ker(self, closes, n=12):
        if len(closes) < n + 1:
            return 0.5
        arr = list(closes)[-(n + 1):]
        net = abs(arr[-1] - arr[0])
        path = sum(abs(arr[i] - arr[i - 1]) for i in range(1, len(arr)))
        return net / path if path > 1e-12 else 0.5

    def _cnt(self, k: str, n: int = 1) -> None:
        self.count[k] = self.count.get(k, 0) + n

    def _log(self, kind: str, **kw) -> None:
        ev = {"time": self.now, "kind": kind}
        ev.update(kw)
        self.events.append(ev)

    def equity(self) -> float:
        unreal = self.qty * (self.price - self.ep) if self.qty else 0.0
        return self.cash + self.margin + unreal

    def _free_margin(self) -> float:
        unreal = self.qty * (self.price - self.ep) if self.qty else 0.0
        return self.cash + unreal

    # ---------------- timeframe handlers (verbatim) ---------------- #
    def _on_15m(self, bar):
        s = self.s
        pc = s.c15[-1] if s.c15 else bar.close
        s.b15 += 1
        s.h15.append(float(bar.high))
        s.l15.append(float(bar.low))
        s.c15.append(float(bar.close))
        s.v15.append(float(bar.volume))
        s.atr15 = self._atr(s.atr15, float(bar.high), float(bar.low), pc, 14)
        s.topo15.update(float(bar.high), float(bar.low), float(bar.volume), s.b15, s.atr15)

    def _on_1h(self, bar):
        s = self.s
        c = float(bar.close)
        h = float(bar.high)
        l = float(bar.low)
        pc = s.c1h[-1] if s.c1h else c
        s.b1h += 1
        s.o1h.append(float(bar.open))
        s.h1h.append(h)
        s.l1h.append(l)
        s.c1h.append(c)
        s.v1h.append(float(bar.volume))
        s.atr1h = self._atr(s.atr1h, h, l, pc, 14)
        s.ema20_1h = self._ema(s.ema20_1h, c, 20)
        s.ema50_1h = self._ema(s.ema50_1h, c, 50)
        s.ema200_1h = self._ema(s.ema200_1h, c, 200)
        s.rsi1h = self._rsi(s.c1h, 14)
        s.ker1h = self._ker(s.c1h, 12)
        s.topo1h.update(h, l, float(bar.volume), s.b1h, s.atr1h)

    def _on_4h(self, bar):
        s = self.s
        c = float(bar.close)
        h = float(bar.high)
        l = float(bar.low)
        pc = s.c4h[-1] if s.c4h else c
        s.b4h += 1
        s.o4h.append(float(bar.open))
        s.h4h.append(h)
        s.l4h.append(l)
        s.c4h.append(c)
        s.v4h.append(float(bar.volume))
        s.atr4h = self._atr(s.atr4h, h, l, pc, 14)
        s.ema20_4h = self._ema(s.ema20_4h, c, 20)
        s.ema50_4h = self._ema(s.ema50_4h, c, 50)
        s.ema200_4h = self._ema(s.ema200_4h, c, 200)
        s.rsi4h = self._rsi(s.c4h, 14)
        s.topo4h.update(h, l, float(bar.volume), s.b4h, s.atr4h)
        if s.rally and len(s.l4h) >= 6:
            lows_4h = s.topo4h.active_lows(s.b4h, 180)
            if lows_4h and c > s.ema20_4h:
                cand_hl = lows_4h[-1]["p"] - 1.8 * s.atr4h
                if cand_hl > s.zig_hl and cand_hl < c * 0.94:
                    s.zig_hl = cand_hl
        self._update_macro_and_rs()

    def _update_macro_and_rs(self):
        ready = [x for x in self.st.values() if len(x.c4h) >= 25 and x.atr4h > 0]
        if not ready:
            return
        above50 = sum(1 for x in ready if x.c4h[-1] > x.ema50_4h)
        above200 = sum(1 for x in ready if x.c4h[-1] > x.ema200_4h)
        n = float(len(ready))
        b50 = above50 / n
        b200 = above200 / n
        self.macro_breadth = 0.55 * b50 + 0.45 * b200
        self.macro_bull = (b50 >= 0.50 and b200 >= 0.50)
        self.macro_bear = (b50 <= 0.25 and b200 <= 0.30)
        for x in ready:
            c = x.c4h[-1]
            c12 = x.c4h[-12] if len(x.c4h) >= 12 else x.c4h[0]
            c42 = x.c4h[-42] if len(x.c4h) >= 42 else x.c4h[0]
            at = max(x.atr4h, c * 0.01)
            r_short = (c - c12) / at
            r_med = (c - c42) / at
            v_arr = list(x.v4h)[-20:]
            v_ratio = x.v4h[-1] / (float(np.mean(v_arr)) + 1e-9)
            v_mult = min(1.8, max(0.7, v_ratio))
            x.rs_score = (0.55 * r_short + 0.45 * r_med) * (0.7 + 0.6 * x.ker1h) * v_mult
        ranked = sorted(ready, key=lambda z: z.rs_score, reverse=True)
        for idx, x in enumerate(ranked):
            x.rs_rank = idx + 1

    # ---------------- ledger primitives ---------------- #
    def _buy(self, qty: float, tag: str, px: float) -> bool:
        fee = qty * px * FEE_RATE
        margin_add = qty * px / LEVERAGE
        if self.cash < margin_add + fee:
            self._cnt("exec_no_margin")
            return False
        self.cash -= margin_add + fee
        self.margin += margin_add
        self.qty = qty
        self.ep = px
        self.fees_total += fee
        self._cnt("entries")
        self._log("ENTRY", tag=tag, px=px, qty=qty, fee=round(fee, 4))
        return True

    def _partial(self, frac: float, px: float, tag: str) -> bool:
        """Sell `frac` of the position at px (VC harvest)."""
        cur_q = self.qty
        if cur_q <= 0:
            return False
        sell_q = math.floor(cur_q * frac / LOT) * LOT
        rem_q = cur_q - sell_q
        if not (sell_q >= MIN_QTY and rem_q >= MIN_QTY and sell_q * px >= MIN_NOTIONAL):
            return False
        fee = sell_q * px * FEE_RATE
        realized = sell_q * (px - self.ep)
        margin_release = sell_q * self.ep / LEVERAGE
        self.cash += margin_release + realized - fee
        self.margin -= margin_release
        self.qty = rem_q
        self.fees_total += fee
        # their internal ledger (verbatim): realized_eq + streak bookkeeping
        int_pnl = (px - self.ep) * sell_q - px * sell_q * INTERNAL_FEE
        self.realized_eq = max(10.0, self.realized_eq + int_pnl)
        ct = self.cur_trade
        if ct is not None:
            ct["realized_acc"] = ct.get("realized_acc", 0.0) + realized - fee
            ct.setdefault("partials", []).append(
                {"time": self.now, "price": round(px, 6), "qty": round(sell_q, 6),
                 "pnl": round(realized - fee, 4), "tag": tag})
        self._cnt("partial_" + tag)
        self._log("PARTIAL", tag=tag, px=px, qty=sell_q)
        return True

    def _close(self, px: float, tag: str) -> None:
        if self.qty <= 0:
            return
        qty = self.qty
        fee = qty * px * FEE_RATE
        realized = qty * (px - self.ep)
        self.cash += self.margin + realized - fee
        self.margin = 0.0
        self.qty = 0.0
        self.fees_total += fee
        # their internal ledger (verbatim)
        int_pnl = (px - self.ep) * qty - px * qty * INTERNAL_FEE
        self.realized_eq = max(10.0, self.realized_eq + int_pnl)
        if int_pnl < 0:
            self.loss_streak += 1
            self.daily_losses += 1
        else:
            self.loss_streak = 0
        self._cnt("exit_" + tag)
        self._log("EXIT", tag=tag, px=px, qty=qty, int_pnl=round(int_pnl, 4))
        # finalize the trade record (report ledger)
        if self.cur_trade is not None:
            ct = self.cur_trade
            net = ct.get("realized_acc", 0.0) + realized - ct["entry_fee"] - fee
            ct["exit_time"] = self.now
            ct["exit_price"] = round(px, 6)
            ct["exit_tag"] = tag
            ct["exit_fee"] = round(fee, 4)
            ct["net_pnl"] = round(net, 4)
            ct["r_multiple"] = (round(net / ct["risk_usd"], 2)
                                if ct.get("risk_usd") else None)
            ct["mfe_r"] = round(self.s.mfe, 2)
            # mae from tracked price excursion (price basis / entry risk unit)
            ct["mae_r"] = round((ct["entry_price"] - self.s.mae) / ct["ir"], 2) \
                if self.s.mae > 0 and ct.get("ir") else None
            ct["equity_after"] = round(self.equity(), 2)
            ct["partials"] = ct.get("partials", [])
            self.trades.append(ct)
            self.cur_trade = None
        self.s.reset_pos()

    def _open_trade_record(self, arm: str, conf: float, c: float, sl: float,
                           tp: float, qty: float, fee: float) -> None:
        self._trade_seq += 1
        ir = c - sl
        self.cur_trade = {
            "trade_id": self._trade_seq,
            "signal_time": self.now,
            "entry_time": self.now,
            "arm": arm,
            "side": "LONG",
            "regime": ("MACRO_BULL" if self.macro_bull else
                       "MACRO_BEAR" if self.macro_bear else "MACRO_NEUTRAL"),
            "macro_breadth": round(self.macro_breadth, 4),
            "rs_rank": int(self.s.rs_rank),
            "conf": round(conf, 4),
            "entry_price": round(c, 6),
            "entry_qty": round(qty, 6),
            "margin_used": round(qty * c / LEVERAGE, 4),
            "sl_at_entry": round(sl, 6),
            "tp_at_entry": round(tp, 6),
            "target_R": round((tp - c) / ir, 2) if ir > 0 else None,
            "ir": round(ir, 6),
            "risk_usd": round(ir * qty, 4),
            "entry_fee": round(fee, 4),
            "realized_acc": 0.0,
            "partials": [],
            "exit_time": None,
            "exit_price": None,
            "exit_tag": None,
            "exit_fee": None,
            "net_pnl": None,
            "r_multiple": None,
            "mfe_r": None,
            "mae_r": None,
            "equity_after": None,
        }

    # ---------------- 5m brain (verbatim flow) ---------------- #
    def on_5m(self, bar) -> None:
        s = self.s
        o = float(bar.open)
        h = float(bar.high)
        l = float(bar.low)
        c = float(bar.close)
        v = float(bar.volume)
        pc = s.c5[-1] if s.c5 else c
        s.b5 += 1
        s.o5.append(o)
        s.h5.append(h)
        s.l5.append(l)
        s.c5.append(c)
        s.v5.append(v)
        s.atr5 = self._atr(s.atr5, h, l, pc, 14)
        s.ema20_5 = self._ema(s.ema20_5, c, 20)
        s.ema50_5 = self._ema(s.ema50_5, c, 50)
        s.ker5 = self._ker(s.c5, 12)
        s.topo5.update(h, l, v, s.b5, s.atr5)
        if self.is_warming_up:
            return
        day = self.now.timetuple().tm_yday
        if day != self.last_day:
            self.last_day = day
            self.daily_losses = 0
        eq = self.equity()
        if eq > self.peak_eq:
            self.peak_eq = eq
        inv = self.qty > 0
        if inv and s.sd == 0:                     # defensive rebuild (their branch)
            s.sd = 1
            s.ep = self.ep
            s.ir = max(s.atr1h * 2.2, s.ep * 0.04)
            s.sl = s.ep - s.ir
            s.tp = s.ep + self.min_rr * s.ir
            s.eb = s.b5
        elif not inv and s.sd != 0 and (s.b5 - s.eb) >= 2:
            s.reset_pos()
        if inv:
            self._manage_open_position(s, o, h, l, c)
            return
        if not self._can_open_new(s):
            return
        sig = self._evaluate_signals(s, o, h, l, c, v)
        if sig:
            arm_name, sl_price, tp_price, conf = sig
            self._execute_entry(s, c, sl_price, tp_price, arm_name, conf)

    def _can_open_new(self, s) -> bool:
        if s.b5 < s.cd_until or len(s.c1h) < 35 or len(s.c4h) < 15:
            return False
        if self.daily_losses >= 3:
            return False
        active_cnt = sum(1 for x in self.st.values() if self.qty > 0)
        if active_cnt >= self.maxp:
            return False
        fm = self._free_margin()
        eq = self.equity()
        if fm < max(4.0, eq * 0.12):
            return False
        used = self.margin
        if used >= self.realized_eq * 0.90:
            return False
        return True

    def _is_wave_candidate(self, s, c) -> bool:
        if s.arm == "V12_CAP" or self.macro_bear:
            return False
        t_4h = (c > s.ema50_4h and s.ema20_4h >= s.ema50_4h * 0.985)
        t_1h = (c > s.ema50_1h and s.ema20_1h >= s.ema50_1h * 0.99)
        strong_rs = (s.rs_rank <= 4 or self.macro_bull)
        return (t_4h or t_1h) and strong_rs

    def _round_qty(self, raw_qty: float) -> float:
        q = float(np.floor(raw_qty / LOT) * LOT)
        return round(q, 3)

    def _harvest_partial(self, s, frac, c) -> bool:
        return self._partial(frac, c, f"VC_HARVEST_{s.vc_stage + 1}")

    def _manage_open_position(self, s, o, h, l, c) -> None:
        r = max(s.ir, s.ep * 0.005)
        cur_r = (h - s.ep) / r
        close_r = (c - s.ep) / r
        if cur_r > s.mfe:
            s.mfe = cur_r
        # report-only adverse excursion (price basis)
        if s.mae == 0.0 or l < s.mae:
            s.mae = l
        held_bars = s.b5 - s.eb
        if not s.rally:
            if s.mfe >= 2.25 and not s.be:
                s.be = True
                s.sl = max(s.sl, s.ep + 0.25 * r)
            if h >= s.tp:
                if self._is_wave_candidate(s, c):
                    s.rally = True
                    s.be = True
                    s.sl = max(s.sl, s.ep + 2.20 * r)
                    s.zig_hl = s.sl
                else:
                    self._close(c, "TP_3_5R_FULL_CASH")
                    s.cd_until = s.b5 + 6
                    return
            if held_bars >= 864 and s.mfe < 1.60 and close_r < 0.65 and c < s.ema50_1h:
                self._close(c, "FREE_STAGNANT_CAPITAL")
                s.cd_until = s.b5 + 12
                return
            if held_bars >= 3:
                c1h_closed_below = (len(s.c1h) >= 1 and s.c1h[-1] <= s.sl and c <= s.sl)
                hard_break = (c <= s.sl * 0.991)
                if c1h_closed_below or hard_break:
                    self._close(c, "STRUCTURAL_SL")
                    s.cd_until = s.b5 + 14
                    return
        else:
            if s.vc_stage == 0 and s.mfe >= 4.20 and close_r >= 3.80:
                if self._harvest_partial(s, 0.35, c):
                    s.vc_stage = 1
                    s.sl = max(s.sl, s.ep + 2.85 * r)
                else:
                    s.vc_stage = 1
                    s.sl = max(s.sl, s.ep + 3.15 * r)
            elif s.vc_stage == 1 and s.mfe >= 10.0 and close_r >= 8.80:
                self._harvest_partial(s, 0.25, c)
                s.vc_stage = 2
                s.sl = max(s.sl, s.ep + 4.50 * r)
            elif s.vc_stage == 2 and s.mfe >= 22.0 and close_r >= 19.50:
                self._harvest_partial(s, 0.25, c)
                s.vc_stage = 3
                s.sl = max(s.sl, s.ep + 9.00 * r)
            if s.zig_hl > s.sl and s.zig_hl < c * 0.94:
                s.sl = s.zig_hl
            if len(s.l4h) >= 40 and s.atr4h > 0:
                macro_box_low = min(list(s.l4h)[-150:]) - 1.8 * s.atr4h
                if macro_box_low > s.sl and macro_box_low < c * 0.92:
                    s.sl = macro_box_low
            c4_break = (len(s.c4h) >= 1 and s.c4h[-1] <= s.sl and c <= s.sl)
            macro_collapse = (
                self.macro_bear
                and len(s.c4h) >= 2
                and c < s.ema200_4h * 0.95
                and s.ema20_4h < s.ema50_4h
                and close_r >= 3.10
            )
            if c4_break or c <= s.sl * 0.975 or macro_collapse:
                self._close(c, "ZIGZAG_WAVE_HARVEST")
                s.cd_until = s.b5 + 16
                return

    def _build_structural_sl(self, s, c, raw_low, min_pct=0.026, max_pct=0.095) -> float:
        at1 = s.atr1h if s.atr1h > 0 else s.atr5 * 3.5
        at4 = s.atr4h if s.atr4h > 0 else at1 * 2.0
        lows_1h = s.topo1h.active_lows(s.b1h, 120)
        lows_4h = s.topo4h.active_lows(s.b4h, 120)
        cands = [raw_low - 0.6 * at1]
        if lows_1h:
            cands.append(lows_1h[-1]["p"] - 0.5 * at1)
        if lows_4h:
            cands.append(lows_4h[-1]["p"] - 0.35 * at4)
        if len(s.l1h) >= 12:
            cands.append(min(list(s.l1h)[-12:]) - 0.4 * at1)
        struct_low = min(cands)
        dist = c - struct_low
        min_d = max(c * min_pct, 1.5 * at1)
        max_d = min(c * max_pct, 3.6 * at4) if at4 > 0 else c * max_pct
        if max_d < min_d:
            max_d = min_d * 1.35
        dist = max(min_d, min(dist, max_d))
        return c - dist

    def _evaluate_signals(self, s, o, h, l, c, v):
        if len(s.v5) < 25 or s.atr5 <= 0 or s.atr1h <= 0:
            return None
        vma5 = float(np.mean(list(s.v5)[-20:])) + 1e-9
        vma1h = float(np.mean(list(s.v1h)[-20:])) + 1e-9
        vr5 = v / vma5
        vr1h = s.v1h[-1] / vma1h if s.v1h else 1.0
        bull_bar = (c > o and (c - l) >= 0.58 * max(h - l, 1e-9))

        # ARM 6: V12_CAP — Bear Market & Flash-Crash Capitulation Sniper
        if (s.rsi4h < 25.0 or (s.rsi1h < 21.0 and s.rsi4h < 33.0)) and c < s.ema50_4h * 0.90:
            lower_wick = min(o, c) - l
            rng = max(h - l, 1e-9)
            if c > o and (lower_wick >= 0.38 * rng or c > s.h5[-2]) and vr5 >= 1.65:
                sl = self._build_structural_sl(s, c, l, min_pct=0.030, max_pct=0.080)
                r = c - sl
                return ("V12_CAP", sl, c + self.min_rr * r, 0.92)

        # In deep Bear Market, block normal breakout arms
        if self.macro_bear and s.rs_rank > 1:
            return None

        # Relative Strength leader filter
        if s.rs_rank > 5 and vr5 < 2.4 and vr1h < 2.0:
            return None

        trend_4h = (c >= s.ema50_4h * 0.985 and s.ema20_4h >= s.ema50_4h * 0.98)
        trend_1h = (c >= s.ema50_1h * 0.99 and s.ema20_1h >= s.ema50_1h * 0.985)

        # ARM 1: V8_4H
        if trend_4h and bull_bar and s.rsi4h < 74.0:
            near_val = (l <= s.ema20_1h * 1.012 or l <= s.ema20_4h * 1.018)
            if near_val and c > s.ema20_5 and (vr5 >= 1.15 or vr1h >= 1.15):
                sl = self._build_structural_sl(s, c, l, min_pct=0.028, max_pct=0.090)
                r = c - sl
                return ("V8_4H", sl, c + self.min_rr * r, 0.90)

        # ARM 2: V11_1H
        if (trend_1h or trend_4h) and bull_bar and s.ker1h >= 0.28:
            rec_h1 = max(list(s.h1h)[-10:-1]) if len(s.h1h) >= 12 else h
            if (c >= rec_h1 * 0.997 or (c > s.ema20_1h and l <= s.ema20_1h * 1.006)) and (
                    vr5 >= 1.20 or vr1h >= 1.20):
                sl = self._build_structural_sl(s, c, l, min_pct=0.026, max_pct=0.092)
                r = c - sl
                return ("V11_1H", sl, c + self.min_rr * r, 0.88)

        # ARM 3: V10_IGN — Volatility Squeeze Ignition
        if len(s.h15) >= 20 and bull_bar:
            rng_recent = max(list(s.h15)[-14:-1]) - min(list(s.l15)[-14:-1])
            squeeze = (rng_recent <= 3.6 * s.atr15)
            brk = (c > max(list(s.h15)[-10:-1]) and vr5 >= 1.55
                   and c > s.ema50_1h * 0.98)
            if squeeze and brk:
                sl = self._build_structural_sl(s, c, min(list(s.l15)[-8:]),
                                               min_pct=0.025, max_pct=0.085)
                r = c - sl
                return ("V10_IGN", sl, c + self.min_rr * r, 0.86)

        # ARM 4: V6_SWP — TopoSwing liquidity sweep & reclaim
        lows_15 = s.topo15.active_lows(s.b15, 90)
        if lows_15 and bull_bar and (trend_4h or trend_1h or self.macro_breadth >= 0.45):
            ref_l = lows_15[-1]["p"]
            if l <= ref_l * 1.003 and c > ref_l and c > s.ema20_5 and vr5 >= 1.15:
                sl = self._build_structural_sl(s, c, min(l, ref_l),
                                               min_pct=0.025, max_pct=0.080)
                r = c - sl
                return ("V6_SWP", sl, c + self.min_rr * r, 0.84)

        # ARM 5: V9_LON — session high-volume breakout
        hr = self.now.hour
        if (7 <= hr <= 21) and (trend_1h or trend_4h) and bull_bar and vr5 >= 1.45:
            box_hi = max(list(s.h5)[-18:-1])
            if c > box_hi and s.ker5 >= 0.32:
                sl = self._build_structural_sl(s, c, min(list(s.l5)[-12:]),
                                               min_pct=0.025, max_pct=0.080)
                r = c - sl
                return ("V9_LON", sl, c + self.min_rr * r, 0.82)

        return None

    def _execute_entry(self, s, c, sl_price, tp_price, arm_name, conf) -> None:
        risk_dist = c - sl_price
        if risk_dist <= c * 0.004:
            return
        self._cnt("sig_" + arm_name)
        eq = self.equity()
        fm = self._free_margin()
        eb = max(12.0, min(eq, self.realized_eq))
        rs_boost = 1.12 if s.rs_rank <= 2 else (1.0 if s.rs_rank <= 4 else 0.85)
        streak_mult = max(0.65, 1.0 - 0.10 * max(0, self.loss_streak - 1))
        risk_pct = self.base_risk * conf * rs_boost * streak_mult
        risk_usd = eb * risk_pct
        raw_qty = risk_usd / risk_dist
        # DIAGNOSTIC (V14_CAP_FIX): their eb*0.34 cap (~$34) sits below the
        # exchange minimum lot (0.001 ~= $95 @100k) — every signal dies at
        # sizing. The fix raises the cap ONLY enough to permit min lot.
        cap = eb * 0.34
        if self.cap_fix:
            cap = max(cap, MIN_QTY * c * 1.05)
        max_notional = min(cap, fm * 1.55)
        if raw_qty * c > max_notional:
            raw_qty = max_notional / c
        qty = self._round_qty(raw_qty)
        if qty < MIN_QTY or qty * c < MIN_NOTIONAL:
            self._cnt("exec_rejected")
            return
        # hardening (disclosed): validate margin BEFORE writing state
        if self.cash < qty * c / LEVERAGE + qty * c * FEE_RATE:
            self._cnt("exec_no_margin")
            return
        s.sd = 1
        s.arm = arm_name
        s.ep = c
        s.sl = sl_price
        s.tp = tp_price
        s.ir = risk_dist
        s.eb = s.b5
        s.mfe = 0.0
        s.mae = c
        s.be = False
        s.rally = False
        s.vc_stage = 0
        s.zig_hl = sl_price
        if not self._buy(qty, f"BUY_{arm_name}_RS{s.rs_rank}", c):
            s.reset_pos()
            return
        # on_order_event BUY branch (verbatim): ep = fill, sl/tp from fill & ir
        old_r = max(s.ir, c * 0.025)
        s.ep = c
        s.sl = c - old_r
        s.tp = c + self.min_rr * old_r
        s.ir = old_r
        self._open_trade_record(arm_name, conf, c, s.sl, s.tp, qty,
                                qty * c * FEE_RATE)

    # ---------------- end of run ---------------- #
    def close_eod(self) -> None:
        if self.qty > 0:
            self._close(self.price, "EOD")


# --------------------------------------------------------------------------- #
# reporting helpers (copied from backtest.py — no import cycle)
# --------------------------------------------------------------------------- #
def _tz(ts) -> pd.Timestamp:
    t = pd.Timestamp(ts)
    return t.tz_localize("UTC") if t.tzinfo is None else t


def metrics(trades: list[dict], eq: pd.DataFrame, capital: float = CAPITAL) -> dict:
    n = len(trades)
    pnl = [t["net_pnl"] for t in trades]
    wins = [p for p in pnl if p > 0]
    losses = [p for p in pnl if p <= 0]
    gp, gl = sum(wins), sum(losses)
    rs = [t["r_multiple"] for t in trades if t.get("r_multiple") is not None]

    max_dd_pct, max_dd_usd = 0.0, 0.0
    exposure = None
    if eq is not None and not eq.empty:
        curve = eq["equity"]
        peak = curve.cummax()
        dd = curve - peak
        max_dd_usd = float(-dd.min())
        max_dd_pct = float((dd / peak).min() * 100.0)
        exposure = float(eq["in_position"].mean() * 100.0)

    hold_h = [
        (_tz(t["exit_time"]) - _tz(t["entry_time"])).total_seconds() / 3600.0
        for t in trades if t.get("exit_time") is not None
    ]
    end_eq = float(eq["equity"].iloc[-1]) if eq is not None and not eq.empty else None
    return {
        "trades": n,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": round(100.0 * len(wins) / n, 1) if n else None,
        "gross_profit": round(gp, 2),
        "gross_loss": round(gl, 2),
        "profit_factor": round(gp / abs(gl), 2) if gl != 0 else None,
        "net_pnl": round(sum(pnl), 2),
        "net_pct": round(sum(pnl) / capital * 100.0, 2),
        "start_equity": capital,
        "end_equity": round(end_eq, 2) if end_eq is not None else None,
        "max_drawdown_pct": round(max_dd_pct, 2),
        "max_drawdown_usd": round(max_dd_usd, 2),
        "avg_r": round(sum(rs) / len(rs), 2) if rs else None,
        "best_r": round(max(rs), 2) if rs else None,
        "worst_r": round(min(rs), 2) if rs else None,
        "avg_hold_hours": round(sum(hold_h) / n, 1) if n else None,
        "exposure_pct": round(exposure, 1) if exposure is not None else None,
        "exit_tags": ({str(k): int(v) for k, v in
                       pd.Series([t["exit_tag"] for t in trades]).value_counts().items()}
                      if n else {}),
        "setups": ({str(k): int(v) for k, v in
                    pd.Series([t["arm"] for t in trades]).value_counts().items()}
                   if n else {}),
        "sides": ({str(k): int(v) for k, v in
                   pd.Series([t["side"] for t in trades]).value_counts().items()}
                  if n else {}),
        "exits": ({str(k): int(v) for k, v in
                   pd.Series([str(t["exit_tag"]).split("_")[0]
                              for t in trades]).value_counts().items()}
                  if n else {}),
        "targets_R": ({str(k): int(v) for k, v in
                       pd.Series([t.get("target_R") for t in trades
                                  if t.get("target_R") is not None]).value_counts().items()}
                      if n else {}),
    }


# --------------------------------------------------------------------------- #
# zero-lookahead runner (same causal pattern as strategy.run_backtest)
# --------------------------------------------------------------------------- #
def run_backtest(data_dir: str, start: str, end: str,
                 warmup_days: int = 15, capital: float = CAPITAL,
                 cap_fix: bool = False) -> dict:
    from engine.causal_primitives import load_asset_ohlcv, resample_causal_tf

    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
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
        rule = {"5m": "5min", "15m": "15min", "30m": "30min"}.get(freq, freq)
        v = df["Volume"].resample(rule, label="left", closed="left").sum()
        v.index = v.index + pd.Timedelta(rule)
        v = v.reindex(tf_df.index).fillna(0.0)
        return {t: float(v.loc[t]) for t in tf_df.index}

    v15, v1, v4 = _vol_of(tf15, "15m"), _vol_of(tf1, "1h"), _vol_of(tf4, "4h")
    m15 = {t: r for t, r in tf15.iterrows()}
    m1 = {t: r for t, r in tf1.iterrows()}
    m4 = {t: r for t, r in tf4.iterrows()}

    from strategy import Bar  # shared causal bar type
    eng = Engine(start=start_ts, capital=capital, cap_fix=cap_fix)

    idx5 = df.index
    for i in range(len(idx5)):
        st = idx5[i]
        t = st + pd.Timedelta(minutes=5)
        if t > end_ts:
            break
        row = df.iloc[i]
        bar = Bar(end_time=t, open=float(row.Open), high=float(row.High),
                  low=float(row.Low), close=float(row.Close), volume=float(row.Volume))
        eng.now = t
        eng.price = bar.close
        eng.is_warming_up = t < start_ts

        # QC consolidate firing order (registration order): 5m, 15m, 1h, 4h
        eng.on_5m(bar)
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

        if t >= start_ts:
            eng._eq_rows.append({
                "time": t,
                "equity": round(eng.equity(), 4),
                "usdt": round(eng.cash, 4),
                "btc": eng.qty,
                "price": bar.close,
                "in_position": bool(eng.qty > 0),
            })

    eng.now = end_ts
    eng.price = float(df["Close"].iloc[-1]) if len(df) else eng.price
    eng.close_eod()

    equity = (pd.DataFrame(eng._eq_rows).set_index("time")
              if eng._eq_rows else pd.DataFrame())
    return {
        "trades": eng.trades,
        "equity": equity,
        "events": eng.events,
        "count": eng.count,
        "end_log": {"equity": round(eng.equity(), 2),
                    "realized_eq_book": round(eng.realized_eq, 2),
                    "loss_streak": eng.loss_streak,
                    "daily_losses": eng.daily_losses,
                    "macro_final": ("BULL" if eng.macro_bull else
                                    "BEAR" if eng.macro_bear else "NEUTRAL")},
        "final_equity": eng.equity(),
        "final_usdt": eng.cash,
        "fees_total": eng.fees_total,
    }


def _buy_hold(run) -> float | None:
    eq = run.get("equity")
    if eq is None or eq.empty or eq["price"].iloc[0] <= 0:
        return None
    return round(100.0 * float(eq["price"].iloc[-1]) / float(eq["price"].iloc[0]), 2)


def main() -> None:
    root = Path(__file__).resolve().parent
    data = root / "data" / "BTCUSD_5m"
    out = root / "results"
    out.mkdir(exist_ok=True)
    cap_fix = os.environ.get("V14_CAP_FIX", "") == "1"
    suffix = "_capfix" if cap_fix else ""

    runs = [
        ("full", FULL_START, FULL_END, 35),
        ("h2", H2_START, H2_END, 35),
        ("h1", H1_START, H1_END, 35),
        ("2021first2m", "2021-01-01", "2021-03-01", 15),
    ]
    results = {}
    for label, a, b, warm in runs:
        print(f"[v14{suffix}] {label}: {a} -> {b} ...", flush=True)
        r = run_backtest(str(data), a, b, warmup_days=warm, capital=CAPITAL,
                         cap_fix=cap_fix)
        results[label] = r
        pd.DataFrame(r["trades"]).to_csv(
            out / f"trades_v14_{label}{suffix}.csv", index=False)
        r["equity"].to_csv(out / f"equity_v14_{label}{suffix}.csv")
        m = metrics(r["trades"], r["equity"])
        print(f"    trades={m['trades']} net={m['net_pnl']} pf={m['profit_factor']} "
              f"end={m['end_equity']} bh={_buy_hold(r)}", flush=True)

    summary = {
        "config": {
            "strategy": "V14 — owner's pasted 6-arm code (BTC-only port)",
            "variant": ("cap_fix diagnostic (notional cap raised only enough to "
                        "permit exchange min lot)" if cap_fix else
                        "faithful as-pasted (eb*0.34 notional cap intact)"),
            "window": f"{FULL_START} .. {FULL_END}",
            "capital_usdt": CAPITAL,
            "leverage": LEVERAGE,
            "min_rr": 3.50,
            "fee_rate_report_ledger": FEE_RATE,
            "internal_fee_verbatim": INTERNAL_FEE,
            "warmup_days_main": 35,
            "warmup_days_2021": 15,
            "symbol": "BTCUSDT",
            "not_tested_pairs": ["ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
                                 "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "LINKUSDT",
                                 "SUIUSDT"],
            "not_tested_reason": "no candle data (BTC only); macro breadth / RS rank "
                                 "degenerate to BTC-only in this port",
        },
        "continuous_12m": metrics(results["full"]["trades"], results["full"]["equity"]),
        "standalone_h2_2025": metrics(results["h2"]["trades"], results["h2"]["equity"]),
        "standalone_h1_2026": metrics(results["h1"]["trades"], results["h1"]["equity"]),
        "buy_hold_12m": _buy_hold(results["full"]),
        "window_2021first2m": metrics(results["2021first2m"]["trades"],
                                      results["2021first2m"]["equity"]),
        "buy_hold_2021first2m": _buy_hold(results["2021first2m"]),
        "signal_funnel": results["full"]["count"],
        "end_log": results["full"]["end_log"],
        "fees_total": results["full"]["fees_total"],
    }
    (out / f"summary_v14{suffix}.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8")
    print(f"[v14] wrote results/summary_v14{suffix}.json", flush=True)


if __name__ == "__main__":
    main()
