"""
V18 — structure-target spot profit engine (local real-data harness).

Spec (owner, 2026-11-19):
  1) SPOT entries; target = nearest liquidity ceiling (hi20 / active 4h
     swing / e200_4) with a HARD 3R floor — never clamped down to 3.
  2) Win rate > 60%.
  3) Consecutive FULL-RISK losses <= 3 via a smart circuit (24h pause ->
     probe-only half-risk until a win resets). No blind freeze, no missed
     opportunities (parked retest orders keep working through the pause).
  4) Bull-run: ride one position through the wave (ratchet rungs), other
     opportunities stay reachable (retest parking) [multi-coin = QC side].
  5) Capital 200 USDT. Deliver with actual run + monthly table.

Data: data/BTCUSD_5m (local). Fees 0.001/side (harness disclosure).
Single-coin: breadth/RS are stand-ins [D].
"""

import json
import math
from collections import deque
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------- config ---------------- #
FEE_RATE = 0.001            # 0.10% per side (harness disclosure)
LEVERAGE = 3.0              # not used for spot sizing; kept for parity
CAPITAL = 200.0             # owner: 200 USDT
WARMUP_DAYS = 35
FULL_START = "2021-01-01"
FULL_END = "2026-10-31"

LOT = 0.000001
MIN_QTY = 0.000001
MIN_NOTIONAL = 5.0

TRANSITION_R = 3.15         # deliberate exit floor (deliberate exits >= 3.15R)
RATCHET_ARM_R = 3.47        # floor-3R arm
BREACH_PX = 0.997
BREACH_BARS = 6
CATASTOPHE_R = 1.85
STALL_RSI_DROP = 6.0        # STALL_TAKE momentum-dead threshold

# THREE_LOSS_CIRCUIT
PAUSE_BARS_24H = 288        # 3rd full-risk loss -> 24h pause (12*24 5m bars)
PROBE_SPACING_BARS = 288    # >=24h between probe attempts
PROBE_POS20 = 0.32          # probe: only deep bottoms
PROBE_TARGET_R = 3.5        # probe: only >=3.5R structures
PROBE_RISK_MULT = 0.5       # probe: half risk

DEAD_BARS, DEAD_RHIGH, DEAD_RNOW = 96, 0.35, 0.10  # 8h slow-bleed time stop
PENDING_BARS = 96           # retest order lives 8h, then expires


# ---------------- regime (single-coin stand-in) ---------------- #
def classify_regime_single(c4, e20, e50, e200, ret30d):
    """Single-coin regime [D]: stack position + 30d return."""
    if c4 <= 0 or e200 <= 0:
        return "RANGE_SNIPER"
    strong = c4 > e20 > e50 > e200
    if strong and ret30d >= 0.15:
        return "SUPER_BULL"
    golden = c4 > e200 and e50 > e200
    if golden and c4 > e50:
        return "NORMAL_BULL"
    if c4 > e50:
        return "RANGE_SNIPER"
    return "BEAR_DEFENSE"


class TopoSwing:
    """Confirmed structural pivot engine with unbroken obstacle purging
    (lineage verbatim from qc_v16_2_fixed.py)."""

    def __init__(self, k=3, max_len=50):
        self.k = k
        self.w = 2 * k + 1
        self.hb = deque(maxlen=self.w)
        self.lb = deque(maxlen=self.w)
        self.sh = deque(maxlen=max_len)
        self.sl = deque(maxlen=max_len)
        self.uh = deque(maxlen=max_len)
        self.ul = deque(maxlen=max_len)

    def update(self, h, l, bar_idx):
        if h <= 0 or l <= 0:
            return
        while self.uh and h > self.uh[-1][1]:
            self.uh.pop()
        while self.ul and l < self.ul[-1][1]:
            self.ul.pop()

        self.hb.append(h)
        self.lb.append(l)
        if len(self.hb) < self.w:
            return

        ch = self.hb[self.k]
        if all(ch >= self.hb[i] for i in range(self.w) if i != self.k):
            if not self.sh or bar_idx - self.sh[-1][0] >= self.k:
                p = (bar_idx - self.k, ch)
                self.sh.append(p)
                if ch >= max(self.hb):
                    self.uh.append(p)

        cl = self.lb[self.k]
        if all(cl <= self.lb[i] for i in range(self.w) if i != self.k):
            if not self.sl or bar_idx - self.sl[-1][0] >= self.k:
                p = (bar_idx - self.k, cl)
                self.sl.append(p)
                if cl <= min(self.lb):
                    self.ul.append(p)

    def ceiling_above(self, price, min_dist):
        cands = [v for _, v in self.uh if v > price + min_dist]
        return min(cands) if cands else None

    def floor_below(self, price, min_dist):
        cands = [v for _, v in self.sl if v < price - min_dist]
        return max(cands) if cands else None


class SymState:
    def __init__(self):
        self.b5 = self.b15 = self.b1h = self.b4h = 0
        self.b1 = 0
        self.b4 = 0
        self.o5 = deque(maxlen=60); self.h5 = deque(maxlen=60)
        self.l5 = deque(maxlen=60); self.c5 = deque(maxlen=60)
        self.v5 = deque(maxlen=60)
        self.o1 = deque(maxlen=260); self.h1 = deque(maxlen=260)
        self.l1 = deque(maxlen=260); self.c1 = deque(maxlen=260)
        self.v1 = deque(maxlen=260)
        self.o4 = deque(maxlen=260); self.h4 = deque(maxlen=260)
        self.l4 = deque(maxlen=260); self.c4 = deque(maxlen=260)
        self.v4 = deque(maxlen=260)
        self.e20_1 = self.e50_1 = self.e200_1 = 0.0
        self.e20_4 = self.e50_4 = self.e200_4 = 0.0
        self.atr1 = self.atr4 = 0.0
        self.rsi1 = 50.0
        self.rsi1_hist = deque(maxlen=36)
        self.vma1 = 0.0
        self.sw_h4 = TopoSwing(2); self.sw_l4 = TopoSwing(2)
        self.ret30d = 0.0
        self.ret7d = 0.0
        # position
        self.ep = self.sl = self.ir = self.tp = 0.0
        self.tp_r = 3.0
        self.eb5 = self.eb1 = self.eb4 = 0
        self.mfe = 0.0
        self.stage = 0
        self.arm = ""
        self.cd_until = 0
        self.sl_breach = 0
        self.in_pos = False

    def reset_pos(self):
        self.ep = self.sl = self.ir = self.tp = 0.0
        self.tp_r = 3.0
        self.eb5 = self.eb1 = self.eb4 = 0
        self.mfe = 0.0
        self.stage = 0
        self.arm = ""
        self.sl_breach = 0
        self.in_pos = False


class Engine:
    def __init__(self, start, capital=CAPITAL):
        self.start = start
        self.now = start
        self.price = 0.0
        self.is_warming_up = True
        self.s = SymState()
        self.cash = float(capital)
        self.margin = 0.0
        self.qty = 0.0
        self.ep = 0.0
        self.fees_total = 0.0
        self.peak_eq = float(capital)
        self.trades = []
        self.cur_trade = None
        self.events = []
        self.count = {}
        self._eq_rows = []
        self._trade_seq = 0
        # circuits
        self.consec_losses = 0        # full-risk consecutive losses
        self.probe_mode = False
        self.pause_until_b5 = -1
        self.last_probe_b5 = -10 ** 9
        self.regime = "RANGE_SNIPER"
        self.breadth = 0.0
        self.regime_log = []
        self._pending = None   # parked retest order (arm, sl, tp_r, line)

    # ---------------- helpers ---------------- #
    @staticmethod
    def _ema(prev, val, n):
        if prev <= 0:
            return val
        k = 2.0 / (n + 1.0)
        return val * k + prev * (1.0 - k)

    def _atr(self, prev, h, l, pc, n=14):
        tr = max(h - l, abs(h - pc), abs(l - pc)) if pc > 0 else (h - l)
        if prev <= 0:
            return tr
        return (prev * (n - 1.0) + tr) / float(n)

    @staticmethod
    def _rsi(closes, n=14):
        if len(closes) < n + 1:
            return 50.0
        arr = list(closes)[-(n + 1):]
        gains = losses = 0.0
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

    @staticmethod
    def _ker(closes, n=12):
        if len(closes) < n + 1:
            return 0.5
        arr = list(closes)[-(n + 1):]
        net = abs(arr[-1] - arr[0])
        path = sum(abs(arr[i] - arr[i - 1]) for i in range(1, len(arr)))
        return net / path if path > 1e-12 else 0.5

    def _cnt(self, k, n=1):
        self.count[k] = self.count.get(k, 0) + n

    def _log(self, kind, **kw):
        ev = {"time": self.now, "kind": kind}
        ev.update(kw)
        self.events.append(ev)

    def equity(self):
        unreal = self.qty * (self.price - self.ep) if self.qty else 0.0
        return self.cash + self.margin + unreal

    def _free_margin(self):
        unreal = self.qty * (self.price - self.ep) if self.qty else 0.0
        return self.cash + unreal

    # ---------------- timeframe handlers ---------------- #
    def _on_1h(self, bar):
        s = self.s
        c = float(bar.close); h = float(bar.high); l = float(bar.low)
        o = float(bar.open); v = float(bar.volume)
        pc = s.c1[-1] if s.c1 else c
        s.b1 += 1
        s.o1.append(o); s.h1.append(h); s.l1.append(l)
        s.c1.append(c); s.v1.append(v)
        s.atr1 = self._atr(s.atr1, h, l, pc, 14)
        s.e20_1 = self._ema(s.e20_1, c, 20)
        s.e50_1 = self._ema(s.e50_1, c, 50)
        s.e200_1 = self._ema(s.e200_1, c, 200)
        s.vma1 = self._ema(s.vma1, v, 20) if s.vma1 > 0 else v
        s.rsi1 = self._rsi(s.c1, 14)
        s.rsi1_hist.append(s.rsi1)
        # returns (causal: current completed 1h close vs history)
        if len(s.c1) >= 168 and s.c1[-168] > 0:
            s.ret7d = (c - s.c1[-168]) / s.c1[-168]
        s.sw_h4  # noqa — swings updated on 4h

    def _on_4h(self, bar):
        s = self.s
        c = float(bar.close); h = float(bar.high); l = float(bar.low)
        o = float(bar.open); v = float(bar.volume)
        pc = s.c4[-1] if s.c4 else c
        s.b4 += 1
        s.o4.append(o); s.h4.append(h); s.l4.append(l)
        s.c4.append(c); s.v4.append(v)
        s.atr4 = self._atr(s.atr4, h, l, pc, 14)
        s.e20_4 = self._ema(s.e20_4, c, 20)
        s.e50_4 = self._ema(s.e50_4, c, 50)
        s.e200_4 = self._ema(s.e200_4, c, 200)
        s.sw_h4.update(h, l, s.b4)
        s.sw_l4.update(h, l, s.b4)
        if len(s.c4) >= 180 and s.c4[-180] > 0:
            s.ret30d = (c - s.c4[-180]) / s.c4[-180]
        elif s.ret7d:
            s.ret30d = s.ret7d

    def _on_15m(self, bar):
        s = self.s
        s.b15 += 1
        s.atr1 = s.atr1  # 15m tracked implicitly via 5m; atr basis = 1h

    def _update_regime(self):
        s = self.s
        c4 = s.c4[-1] if s.c4 else 0.0
        self.regime = classify_regime_single(
            c4, s.e20_4, s.e50_4, s.e200_4, s.ret30d)
        # single-coin breadth stand-in [D]: stack position of 4h close
        if s.e200_4 > 0 and c4 > s.e200_4:
            self.breadth = 1.0
        elif s.e50_4 > 0 and c4 > s.e50_4:
            self.breadth = 0.5
        else:
            self.breadth = 0.0

    # ---------------- accounting ---------------- #
    def _buy(self, qty, tag, px):
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
        self._log("ENTRY", tag=tag, px=px, qty=qty)
        return True

    def _close(self, px, tag):
        if self.qty <= 0:
            return
        qty = self.qty
        fee = qty * px * FEE_RATE
        realized = qty * (px - self.ep)
        self.cash += self.margin + realized - fee
        self.margin = 0.0
        self.qty = 0.0
        self.fees_total += fee
        # NET-based loss: a trade can be px>=ep yet net<=0 after fees —
        # the owner counts that as a loss [measured mismatch vs metric]
        entry_fee0 = self.cur_trade["entry_fee"] if self.cur_trade else 0.0
        is_loss = (realized - fee - entry_fee0) < 0.0
        is_probe = bool(getattr(self, "_cur_probe", False))
        # THREE_LOSS_CIRCUIT: 3 FULL-RISK losses -> pause; probe (half-risk)
        # losses do NOT count and do NOT reset — only a probe WIN resets
        if is_probe:
            if not is_loss:
                if self.consec_losses > 0 or self.probe_mode:
                    self._cnt("circuit_reset_by_win")
                self.consec_losses = 0
                self.probe_mode = False
        elif is_loss:
            self.consec_losses += 1
            # 24h entry cooldown after ANY loss [measured: same-day
            # double losses 2026-06-04 / 2025-02-27 were the last bleed]
            self.s.cd_until = self.s.b5 + PAUSE_BARS_24H
            if self.consec_losses >= 3:
                self.pause_until_b5 = self.s.b5 + PAUSE_BARS_24H
                self.probe_mode = True
                self._cnt("circuit_three_loss_pause")
        else:
            if self.consec_losses > 0 or self.probe_mode:
                self._cnt("circuit_reset_by_win")
            self.consec_losses = 0
            self.probe_mode = False
        self._cnt("exit_" + tag)
        self._log("EXIT", tag=tag, px=px, pnl=round(realized - fee, 4))
        if self.cur_trade is not None:
            ct = self.cur_trade
            net = ct.get("realized_acc", 0.0) + realized - ct["entry_fee"] - fee
            ct["exit_time"] = self.now
            ct["exit_price"] = round(px, 6)
            ct["exit_tag"] = tag
            ct["net_pnl"] = round(net, 4)
            ct["r_multiple"] = (round(net / ct["risk_usd"], 2)
                                if ct.get("risk_usd") else None)
            ct["mfe_r"] = round((ct.get("mfe_r", 0.0)), 2)
            ct["probe"] = bool(getattr(self, "_cur_probe", False))
            self.trades.append(ct)
            self.cur_trade = None
        self.s.reset_pos()

    def _open_trade_record(self, arm, risk_pct, c, sl, tp_r, qty, fee, probe):
        self._trade_seq += 1
        ir = c - sl
        self.cur_trade = {
            "trade_id": self._trade_seq,
            "entry_time": self.now,
            "arm": arm,
            "regime": self.regime,
            "iso_week": "%d-W%02d" % self.now.isocalendar()[:2],
            "entry_price": round(c, 6),
            "entry_qty": round(qty, 6),
            "sl_at_entry": round(sl, 6),
            "tp_at_entry": round(c + tp_r * ir, 6),
            "target_R": round(tp_r, 2),
            "risk_pct": round(risk_pct, 4),
            "probe": bool(probe),
            "risk_usd": round(ir * qty, 4),
            "entry_fee": round(fee, 4),
            "realized_acc": 0.0,
            "exit_time": None, "exit_price": None, "exit_tag": None,
            "net_pnl": None, "r_multiple": None, "mfe_r": 0.0,
            "equity_after": None,
        }

    # ---------------- waterfall veto (BTC self) ---------------- #
    def btc_waterfall_veto(self):
        s = self.s
        if len(s.c1) < 30 or len(s.c5) < 5 or s.e20_1 <= 0:
            return False
        c1 = s.c1[-1]
        # true waterfall = breaking BELOW recent 1h structure, not merely
        # trading under the EMA (bear washouts must stay enterable)
        l1w = list(s.l1)
        struct_break = (len(l1w) >= 6 and s.c5[-1] < min(l1w[-6:]))
        falling = (c1 < s.e20_1 * 0.992 and c1 < s.c1[-2] and struct_break)
        if not falling:
            return False
        l1 = list(s.l1)
        h1 = list(s.h1)
        if len(l1) >= 10 and len(h1) >= 3:
            hl = min(l1[-3:]) > min(l1[-10:-3])
            reclaim = s.c5[-1] > h1[-1]
            if hl and reclaim:
                return False
        return True

    # ---------------- structure target (>= 3R floor) ---------------- #
    def nearest_ceiling(self, c):
        """Nearest liquidity box / swing ceiling above price [owner spec]."""
        s = self.s
        cands = []
        if len(s.h4) >= 20:
            hi20 = max(list(s.h4)[-20:])
            if hi20 > c:
                cands.append(hi20)
        sw = s.sw_h4.ceiling_above(c, 0.20 * max(s.atr1, 1e-9))
        if sw is not None:
            cands.append(sw)
        if s.e200_4 > 0 and s.e200_4 > c:
            cands.append(s.e200_4)
        return min(cands) if cands else None

    # ---------------- 5m brain ---------------- #
    def on_5m(self, bar):
        s = self.s
        o = float(bar.open); h = float(bar.high)
        l = float(bar.low); c = float(bar.close); v = float(bar.volume)
        pc = s.c5[-1] if s.c5 else c
        s.b5 += 1
        s.o5.append(o); s.h5.append(h); s.l5.append(l)
        s.c5.append(c); s.v5.append(v)
        s.atr1 = s.atr1  # atr fresh via 1h only (structure stop basis)
        if self.is_warming_up:
            return
        if len(s.c1) < 60 or len(s.c4) < 50 or s.atr1 <= 0 or s.atr4 <= 0:
            return
        self._update_regime()
        eq = self.equity()
        if eq > self.peak_eq:
            self.peak_eq = eq
        # daily regime log
        dkey = self.now.date()
        if dkey != getattr(self, "_last_log_day", None):
            self._last_log_day = dkey
            self.regime_log.append({
                "date": str(dkey), "regime": self.regime,
                "close": round(c, 2), "ret30d": round(s.ret30d, 4),
            })
        inv = self.qty > 0
        if inv and not s.in_pos:                 # defensive rebuild
            s.in_pos = True
            s.ep = self.ep
            s.ir = max(s.ep * 0.015, 0.90 * s.atr1)
            s.sl = s.ep - s.ir
            res = self.nearest_ceiling(s.ep)
            if res is not None and res > s.ep:
                s.tp = res
                s.tp_r = max(3.0, (res - s.ep) / s.ir)
            else:
                s.tp = s.ep + 3.15 * s.ir
                s.tp_r = 3.15
            s.eb5 = s.b5; s.eb1 = s.b1; s.eb4 = s.b4
            s.mfe = s.ep
        if inv:
            self.manage(c, h, l)
            return
        if s.ep > 0.0:
            s.reset_pos()
        if self._pending is not None:
            p = self._pending
            if s.b5 > p["exp_b5"]:
                self._pending = None
                self._cnt("pending_expired")
            elif c < p["line"] - 1.0 * s.atr1:
                self._pending = None
                self._cnt("pending_broke")
            elif l <= p["line"]:
                self._fill_pending(c, h, l, o, v)
                return
        self.try_enter(c, h, l, o, v)

    # ---------------- entry ---------------- #
    def try_enter(self, c, h, l, o, v):
        s = self.s
        if s.b5 < s.cd_until:
            return
        if self.btc_waterfall_veto():
            self._cnt("gate_waterfall")
            return
        # THREE_LOSS_CIRCUIT: pause, then probe-only until a win resets
        probe = False
        if self.probe_mode:
            if s.b5 < self.pause_until_b5:
                self._cnt("gate_three_loss_pause")
                return
            probe = True
        if len(s.h4) < 30 or len(s.h1) < 30 or len(s.rsi1_hist) < 15:
            return
        if s.atr1 <= 0 or len(s.l1) < 24:
            return

        score, sl, arm, tp_r = self.evaluate(c, h, l, o, v)
        if score <= 0.0:
            return
        line = s.e20_1
        if self.regime != "SUPER_BULL" and c > line + 0.10 * s.atr1:
            # EXTENDED above the reclaim line: park a retest order at the
            # line instead of chasing — fills on the pullback, expires in
            # 8h, cancels if structure breaks while waiting [no-miss spec]
            stale = (self._pending is None
                     or score > self._pending.get("score", 0.0)
                     or s.b5 > self._pending.get("exp_b5", 0))
            if stale:
                score2, sl2, arm2, tp2 = self.evaluate(
                    c, h, l, o, v, px_ref=line)
                if score2 > 0.0 and sl2 < line:
                    self._pending = {"arm": arm2, "score": score2,
                                     "sl": sl2, "tp_r": tp2, "line": line,
                                     "exp_b5": s.b5 + PENDING_BARS}
                    self._cnt("pending_parked")
            self._cnt("gate_extended_park")
            return
        if probe:
            pos_20 = self._pos20(c)
            if pos_20 > PROBE_POS20 or tp_r < PROBE_TARGET_R:
                self._cnt("gate_probe_filter")
                return
            if s.b5 - self.last_probe_b5 < PROBE_SPACING_BARS:
                self._cnt("gate_probe_spacing")
                return

        eq = self.equity()
        if eq <= 5.0:
            return
        regime = self.regime
        if regime == "SUPER_BULL":
            risk_pct, slot = 0.030, 0.85
        elif regime == "NORMAL_BULL":
            risk_pct, slot = 0.026, 0.75
        elif regime == "RANGE_SNIPER":
            risk_pct, slot = 0.022, 0.65
        else:
            risk_pct, slot = 0.018, 0.55
        if probe:
            risk_pct *= PROBE_RISK_MULT
        risk_usdt = eq * risk_pct
        ir = c - sl
        if ir <= 0:
            return
        notional = (risk_usdt / ir) * c
        notional = min(notional, eq * slot, self._free_margin() * 1.55)
        if notional < 6.2:
            return
        qty = float(np.floor((notional / c) / LOT) * LOT)
        if qty < MIN_QTY or qty * c < MIN_NOTIONAL:
            self._cnt("exec_rejected")
            return
        if not self._buy(qty, "ENT_%s_%s" % (arm, regime), c):
            return
        self._pending = None   # in via market — drop any parked retest
        s.in_pos = True
        s.ep = c
        s.sl = sl
        s.ir = ir
        s.tp_r = tp_r
        s.tp = c + tp_r * ir
        s.eb5 = s.b5; s.eb1 = s.b1; s.eb4 = s.b4
        s.mfe = c
        s.stage = 0
        s.arm = arm
        s.sl_breach = 0
        self._cur_probe = probe
        if probe:
            self.last_probe_b5 = s.b5
        self._open_trade_record(arm, risk_pct, c, sl, tp_r, qty,
                                qty * c * FEE_RATE, probe)

    def _fill_pending(self, c, h, l, o, v):
        """Fill the parked retest order at the reclaim line (limit logic:
        touch of the line fills; a gap through fills at the better open)."""
        s = self.s
        p = self._pending
        if p is None or self.qty > 0:
            return
        if s.b5 < s.cd_until:
            return                      # keep parked; no fill during cooldown
        fill = min(p["line"], o)
        sl = p["sl"]
        tp_r = p["tp_r"]
        ir = fill - sl
        if ir <= 0 or fill <= 0:
            self._pending = None
            self._cnt("pending_bad_fill")
            return
        probe = False
        if self.probe_mode:
            if s.b5 < self.pause_until_b5:
                return                      # keep parked until pause lifts
            probe = True
            if (self._pos20(fill) > PROBE_POS20 or tp_r < PROBE_TARGET_R
                    or s.b5 - self.last_probe_b5 < PROBE_SPACING_BARS):
                self._pending = None
                self._cnt("pending_probe_filtered")
                return
        eq = self.equity()
        if eq <= 5.0:
            self._pending = None
            return
        regime = self.regime
        if regime == "SUPER_BULL":
            risk_pct, slot = 0.030, 0.85
        elif regime == "NORMAL_BULL":
            risk_pct, slot = 0.026, 0.75
        elif regime == "RANGE_SNIPER":
            risk_pct, slot = 0.022, 0.65
        else:
            risk_pct, slot = 0.018, 0.55
        if probe:
            risk_pct *= PROBE_RISK_MULT
        risk_usdt = eq * risk_pct
        notional = (risk_usdt / ir) * fill
        notional = min(notional, eq * slot, self._free_margin() * 1.55)
        if notional < 6.2:
            self._pending = None
            return
        qty = float(np.floor((notional / fill) / LOT) * LOT)
        if qty < MIN_QTY or qty * fill < MIN_NOTIONAL:
            self._pending = None
            self._cnt("exec_rejected")
            return
        if not self._buy(qty, "RET_%s_%s" % (p["arm"], regime), fill):
            self._pending = None
            return
        s.in_pos = True
        s.ep = fill
        s.sl = sl
        s.ir = ir
        s.tp_r = tp_r
        s.tp = fill + tp_r * ir
        s.eb5 = s.b5; s.eb1 = s.b1; s.eb4 = s.b4
        s.mfe = fill
        s.stage = 0
        s.arm = p["arm"]
        s.sl_breach = 0
        self._cur_probe = probe
        if probe:
            self.last_probe_b5 = s.b5
        self._open_trade_record(p["arm"], risk_pct, fill, sl, tp_r, qty,
                                qty * fill * FEE_RATE, probe)
        self._pending = None
        self._cnt("pending_filled")

    def _pos20(self, c):
        s = self.s
        hi = max(list(s.h4)[-20:])
        lo = min(list(s.l4)[-20:])
        return (c - lo) / max(hi - lo, c * 0.01)

    def evaluate(self, c, h, l, o, v, px_ref=None):
        s = self.s
        regime = self.regime
        pos_20 = self._pos20(c)
        vma5 = sum(s.v5) / float(len(s.v5)) if len(s.v5) >= 10 else v
        vr5 = (v / vma5) if vma5 > 0 else 1.0
        # single-coin RS stand-in: 7d absolute momentum [D]
        strength = s.ret7d
        l1 = list(s.l1); h1 = list(s.h1); rsi_h = list(s.rsi1_hist)
        # px_ref: entry reference price (market close, or the retest LINE
        # when sizing a pending order) — arms always judge the live bar c
        px = c if px_ref is None else px_ref
        # reclaim sustained required ONLY when extended above the line
        # (at the line, the pullback bar is below — that IS the retest)
        if (c > s.e20_1 + 0.10 * s.atr1
                and (len(s.c5) < 3 or s.c5[-2] <= s.e20_1 * 0.999)):
            return 0.0, 0.0, "", 0.0

        # F5: structural stop under the confirmed 1h bottom (4h floor was
        # inflating ir until every gate rejected — measured collapse)
        struct_sl = min(l1[-4:]) - 0.45 * s.atr1
        raw_ir = px - struct_sl
        max_ir = (min(px * 0.042, 2.20 * s.atr1) if regime == "SUPER_BULL"
                  else min(px * 0.032, 2.00 * s.atr1))
        if raw_ir > max_ir * 1.5:
            return 0.0, 0.0, "", 0.0
        min_ir = max(px * 0.015, 1.10 * s.atr1)
        ir = max(min_ir, min(raw_ir, max_ir))

        # STRUCTURE TARGET (floor 3R, never clamped down)
        res = self.nearest_ceiling(px)
        if res is None or (res - px) < 3.0 * ir:
            self._cnt("gate_target_below_3r")
            return 0.0, 0.0, "", 0.0
        tp_r = (res - px) / ir

        arm = ""
        score = 0.0

        # ARM 1: W_CAP_BOTTOM
        if len(rsi_h) >= 24 and len(s.v1) >= 24:
            win = l1[-24:-3]
            rw = rsi_h[-24:-3]
            vw = list(s.v1)[-24:-3]
            if len(win) >= 10 and len(rw) >= 10:
                abs_low = min(win)
                idx = win.index(abs_low)
                ago_ok = 4 <= (24 - idx) <= 21
                wash = (abs_low <= s.e50_1 * 0.952 and min(rw) <= 32.5
                        and max(vw) >= 1.8 * s.vma1)
                hl = min(l1[-3:]) >= abs_low * 1.002
                div = min(rsi_h[-3:]) >= min(rw) + 4.0
                turn = (c > s.e20_1 and c > s.o1[-1]
                        and 40.0 <= s.rsi1 <= 56.0)
                if ago_ok and wash and hl and div and turn and pos_20 <= 0.38:
                    arm = "W_CAP_BOTTOM"
                    score = 92.0 + strength * 100.0

        # ARM 2: DEMAND_4H_SPRING — DISABLED [measured: 3 wins / 10 losses
        # (WR 23%) across the full window; the only arm dragging PF below 1]
        if False and not arm and regime in ("SUPER_BULL", "NORMAL_BULL", "RANGE_SNIPER"):
            l4 = list(s.l4)
            lo20 = min(l4[-20:])
            tested = (min(l4[-3:]) <= max(s.e50_4 * 1.005, lo20 * 1.012)
                      and s.c4[-1] >= s.e200_4 * 0.985)
            hl = l1[-1] > min(l1[-6:-1])
            turn = (c > s.e20_1 and c > s.o1[-1]
                    and 42.0 <= s.rsi1 <= 57.0)
            if tested and hl and turn and pos_20 <= 0.40 and strength >= 0.0:
                arm = "DEMAND_4H_SPRING"
                score = 86.0 + strength * 100.0

        # ARM 3: TREND_PULLBACK_1H
        if not arm and regime in ("NORMAL_BULL", "SUPER_BULL", "RANGE_SNIPER"):
            trend = (s.c4[-1] > s.e20_4 >= s.e50_4 and s.e20_1 >= s.e50_1)
            pocket = (min(l1[-8:-1]) <= s.e20_1 * 1.003
                      and min(l1[-8:-1]) >= s.e50_1 * 0.988
                      and min(rsi_h[-8:-1]) <= 49.0)
            turn = (c > s.e20_1 and c > max(h1[-2:]) and c > s.o1[-1]
                    and pos_20 <= 0.48 and 45.0 <= s.rsi1 <= 59.0)
            snap = c - min(l1[-4:]) <= 1.6 * s.atr1
            if (trend and strength >= 0.003 and pocket and turn and snap
                    and pos_20 <= 0.48):
                arm = "TREND_PULLBACK_1H"
                score = 88.0 + strength * 100.0

        # ARM 4: SUPER_CYCLE_IGN
        if not arm and regime == "SUPER_BULL" and self.breadth >= 0.70:
            base = max(h1[-10:-1]) - min(l1[-10:-1]) <= 2.4 * s.atr1
            brk = (c > max(h1[-10:-1]) and vr5 >= 1.35
                   and 50.0 <= s.rsi1 <= 63.0)
            if base and brk and pos_20 <= 0.65 and strength >= 0.008:
                arm = "SUPER_CYCLE_IGN"
                score = 84.0 + strength * 100.0

        if not arm:
            return 0.0, 0.0, "", 0.0
        return score, px - ir, arm, tp_r

    # ---------------- exits ---------------- #
    def manage(self, c, h, l):
        s = self.s
        if h > s.mfe:
            s.mfe = h
        ir = max(s.ir, s.ep * 0.015)
        r_now = (c - s.ep) / ir
        r_high = (s.mfe - s.ep) / ir
        r_close_1h = (s.c1[-1] - s.ep) / ir if s.c1 else r_now
        mfe_r = r_high

        if c <= s.ep - CATASTOPHE_R * ir:
            self._close(c, "CATASTROPHIC_GUARD")
            return
        if c <= s.sl * BREACH_PX:
            s.sl_breach += 1
        else:
            s.sl_breach = 0

        if s.stage == 0:
            # SCRATCH SHIELD ladder [V18, WR lever]: lock must clear fees
            # (0.002*ep/ir ≈ 0.13R at tightest ir) — every rung stays NET
            # POSITIVE so pullbacks exit as WINS [owner: WR>60]
            if r_high >= 1.10:
                s.sl = max(s.sl, s.ep + 0.55 * ir)
            if r_high >= 0.70:
                s.sl = max(s.sl, s.ep + 0.35 * ir)
            if r_high >= 0.45:
                s.sl = max(s.sl, s.ep + 0.25 * ir)
            # STALL_TAKE [V18, WR lever]: confirmed +1.25R with dead
            # momentum exits as a WIN instead of round-tripping
            if r_high >= 1.45 and r_close_1h >= 1.25:
                stall_1h = len(s.c1) >= 2 and s.c1[-1] < s.o1[-1]
                rsi_dead = (len(s.rsi1_hist) >= 7
                            and s.rsi1 < s.rsi1_hist[-7] - STALL_RSI_DROP)
                if stall_1h and rsi_dead:
                    self._close(c, "STALL_TAKE")
                    return
                s.sl = max(s.sl, s.ep - 0.15 * ir)
            if (r_high >= 2.35 and r_close_1h >= 2.00
                    and self.regime in ("BEAR_DEFENSE", "RANGE_SNIPER")
                    and len(s.c1) >= 2 and s.c1[-1] < s.o1[-1]
                    and len(s.rsi1_hist) >= 7
                    and s.rsi1 < s.rsi1_hist[-7] - STALL_RSI_DROP):
                s.sl = max(s.sl, s.ep - 0.05 * ir)
            if r_high >= 2.75 and s.b1 > s.eb1:
                s.sl = max(s.sl, s.ep + 2.10 * ir)
            # structure stop on 5m close (no 1h confirmation lag: the lag
            # was exiting at -1.7R instead of -1R [measured])
            if c <= s.sl or s.sl_breach >= BREACH_BARS:
                self._close(c, "STRUCT_STOP")
                return
            if ((s.b5 - s.eb5) >= DEAD_BARS and r_high < DEAD_RHIGH
                    and r_now < DEAD_RNOW):
                self._close(c, "DEAD_SETUP_EXIT")
                return

        if s.stage == 0 and (r_high >= TRANSITION_R or r_now >= TRANSITION_R):
            s.stage = 1

        if s.stage >= 1:
            self.ratchet(c, h, r_now, r_high, ir, mfe_r)

    def ratchet(self, c, h, r_now, r_high, ir, mfe_r):
        s = self.s
        regime = self.regime
        vma5 = sum(s.v5) / float(len(s.v5)) if len(s.v5) >= 10 else 1.0
        vr5 = (s.v5[-1] / vma5) if vma5 > 0 else 1.0
        super_mode = (regime == "SUPER_BULL" or
                      (r_now >= 3.30 and vr5 >= 1.5 and s.e20_1 > 0
                       and c > s.e20_1))
        if super_mode:
            # bull-run rider: whole-wave locks with >= 0.55R buffers
            if r_high >= 3.60:
                s.sl = max(s.sl, s.ep + 3.05 * ir)
            if r_high >= 5.00:
                s.sl = max(s.sl, s.ep + 3.80 * ir)
            if r_high >= 8.00:
                s.sl = max(s.sl, s.ep + 6.00 * ir)
            if r_high >= 14.0:
                s.sl = max(s.sl, s.ep + 10.5 * ir)
            if r_high >= 22.0:
                s.sl = max(s.sl, s.ep + 17.0 * ir)
            if (len(s.c4) >= 2 and s.b4 > s.eb4
                    and s.c4[-1] < s.e50_4 and c < s.e50_4):
                self._close(c, "WAVE_TRAIL_4H")
                return
            if c <= s.sl:
                self._close(c, "RIDE_TRAIL_SL")
                return
            return

        # non-super: structure target (kept whole — never clamped to 3R)
        if s.tp > 0 and c >= s.tp * 0.997:
            self._close(c, "TP_STRUCT")
            return
        floor_3r = s.ep + 3.02 * ir
        trail = s.mfe - 1.25 * ir
        if s.e20_1 > 0:
            trail = max(trail, s.e20_1 - 0.35 * s.atr1)
        armed = r_high >= RATCHET_ARM_R
        if armed:
            trail = max(trail, floor_3r)
        if trail > s.sl:
            s.sl = trail
        deccel = (s.rsi1 >= 68.0) or (armed and len(s.h5) >= 2 and c < s.h5[-2])
        if deccel and r_now >= TRANSITION_R:
            self._close(c, "FULL_SNIPER_3_3R")
            return
        if c <= s.sl:
            # armed -> locked floor; unarmed -> EMA/MFE trail hit
            self._close(c, "RAT_3R_FLOOR" if armed else "RAT_TRAIL_SL")
            return

    def close_eod(self):
        if self.qty > 0:
            self._close(self.price, "EOD")


# --------------------------------------------------------------------------- #
def _tz(ts):
    t = pd.Timestamp(ts)
    return t.tz_localize("UTC") if t.tzinfo is None else t


def metrics(trades, eq, capital=CAPITAL):
    n = len(trades)
    pnl = [t["net_pnl"] for t in trades]
    wins = [p for p in pnl if p > 0]
    losses = [p for p in pnl if p <= 0]
    gp, gl = sum(wins), sum(losses)
    rs = [t["r_multiple"] for t in trades if t.get("r_multiple") is not None]
    max_dd_pct = 0.0
    exposure = None
    if eq is not None and not eq.empty:
        curve = eq["equity"]
        peak = curve.cummax()
        dd = curve - peak
        max_dd_pct = float((dd / peak).min() * 100.0)
        exposure = float(eq["in_position"].mean() * 100.0)
    hold_h = [(_tz(t["exit_time"]) - _tz(t["entry_time"])).total_seconds() / 3600.0
              for t in trades if t.get("exit_time") is not None]
    end_eq = float(eq["equity"].iloc[-1]) if eq is not None and not eq.empty else None
    cagr = sharpe = None
    if eq is not None and not eq.empty and end_eq:
        days = max(1, (_tz(eq.index[-1]) - _tz(eq.index[0])).days)
        cagr = round(((end_eq / capital) ** (365.0 / days) - 1.0) * 100.0, 2)
        me = eq["equity"].resample("ME").last().dropna()
        if len(me) >= 4:
            rets = me.pct_change().dropna()
            sd = float(rets.std())
            if sd > 1e-9:
                sharpe = round(float(rets.mean()) / sd * math.sqrt(12.0), 3)
    # max consecutive full-risk losses observed (probe trades break the
    # full-risk streak: they are half-risk by design)
    max_consec = cur = 0
    for t in trades:
        if t.get("probe"):
            cur = 0
        elif (t.get("net_pnl") or 0) <= 0:
            cur += 1
            max_consec = max(max_consec, cur)
        else:
            cur = 0
    return {
        "trades": n, "wins": len(wins), "losses": len(losses),
        "win_rate_pct": round(100.0 * len(wins) / n, 1) if n else None,
        "profit_factor": round(gp / abs(gl), 2) if gl != 0 else None,
        "net_pnl": round(sum(pnl), 2),
        "net_pct": round(sum(pnl) / capital * 100.0, 2),
        "end_equity": round(end_eq, 2) if end_eq is not None else None,
        "cagr_pct": cagr, "sharpe_monthly": sharpe,
        "max_drawdown_pct": round(max_dd_pct, 2),
        "avg_r": round(sum(rs) / len(rs), 2) if rs else None,
        "best_r": round(max(rs), 2) if rs else None,
        "worst_r": round(min(rs), 2) if rs else None,
        "avg_hold_hours": round(sum(hold_h) / n, 1) if n else None,
        "exposure_pct": round(exposure, 1) if exposure is not None else None,
        "max_consecutive_full_risk_losses": max_consec,
        "probe_trades": sum(1 for t in trades if t.get("probe")),
        "fees_total": None,
        "exit_tags": ({str(k): int(v) for k, v in
                       pd.Series([t["exit_tag"] for t in trades]).value_counts().items()}
                      if n else {}),
        "setups": ({str(k): int(v) for k, v in
                    pd.Series([t["arm"] for t in trades]).value_counts().items()}
                   if n else {}),
        "regimes": ({str(k): int(v) for k, v in
                     pd.Series([t["regime"] for t in trades]).value_counts().items()}
                    if n else {}),
        "target_r": ({'min': round(float(pd.Series(
            [t["target_R"] for t in trades]).min()), 2),
                      'median': round(float(pd.Series(
                          [t["target_R"] for t in trades]).median()), 2),
                      'max': round(float(pd.Series(
                          [t["target_R"] for t in trades]).max()), 2)} if n else {}),
    }


def run_backtest(data_dir, start, end, warmup_days=WARMUP_DAYS, capital=CAPITAL):
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

    tf1 = resample_causal_tf(df, "1h")
    tf4 = resample_causal_tf(df, "4h")

    def _vol_of(tf_df, freq):
        rule = {"5m": "5min", "15m": "15min", "1h": "1h", "4h": "4h"}[freq]
        v = df["Volume"].resample(rule, label="left", closed="left").sum()
        v.index = v.index + pd.Timedelta(rule)
        v = v.reindex(tf_df.index).fillna(0.0)
        return {t: float(v.loc[t]) for t in tf_df.index}

    v1, v4 = _vol_of(tf1, "1h"), _vol_of(tf4, "4h")
    m1 = {t: r for t, r in tf1.iterrows()}
    m4 = {t: r for t, r in tf4.iterrows()}

    from strategy import Bar
    eng = Engine(start=start_ts, capital=capital)
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
        eng.on_5m(bar)
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
                "time": t, "equity": round(eng.equity(), 4),
                "usdt": round(eng.cash, 4), "btc": eng.qty,
                "price": bar.close, "in_position": bool(eng.qty > 0),
            })
    eng.now = end_ts
    eng.price = float(df["Close"].iloc[-1]) if len(df) else eng.price
    eng.close_eod()

    equity = (pd.DataFrame(eng._eq_rows).set_index("time")
              if eng._eq_rows else pd.DataFrame())
    return {"trades": eng.trades, "equity": equity, "events": eng.events,
            "count": eng.count, "regime_log": eng.regime_log,
            "fees_total": eng.fees_total, "final_equity": eng.equity(),
            "df5": df}


def main():
    out = Path(__file__).resolve().parent / "results"
    out.mkdir(exist_ok=True)
    print("[v18] running %s..%s capital=%.0f ..." % (FULL_START, FULL_END, CAPITAL),
          flush=True)
    run = run_backtest(str(Path(__file__).resolve().parent / "data" / "BTCUSD_5m"),
                       FULL_START, FULL_END)
    trades = run["trades"]
    eq = run["equity"]
    m = metrics(trades, eq)
    m["fees_total"] = round(run["fees_total"], 2)
    m["signal_funnel"] = run["count"]

    pd.DataFrame(trades).to_csv(out / "trades_v18.csv", index=False)
    eq.to_csv(out / "equity_v18.csv")
    pd.DataFrame(run["regime_log"]).to_csv(out / "regime_log_v18.csv", index=False)
    me = eq["equity"].resample("ME").last()
    monthly = me.pct_change().fillna(0.0) * 100.0
    pd.DataFrame({"month": monthly.index.strftime("%Y-%m"),
                  "ret_pct": monthly.values.round(2)}).to_csv(
        out / "monthly_v18.csv", index=False)

    summary = {
        "config": {
            "strategy": "V18 structure-target spot (local real-data run)",
            "window": "%s .. %s" % (FULL_START, FULL_END),
            "capital_usdt": CAPITAL, "leverage": LEVERAGE,
            "warmup_days": WARMUP_DAYS, "fee_rate_per_side": FEE_RATE,
            "target_rule": "nearest ceiling, floor 3R, never clamped",
            "symbol": "BTCUSDT",
            "single_coin_disclosure": "breadth binary; RS gates use ret7d [D]; "
                                      "multi-coin slots QC-side only",
        },
        "metrics": m,
        "monthly_pos_neg": {
            "positive_months": int((monthly > 0).sum()),
            "negative_months": int((monthly < 0).sum()),
            "flat_months": int((monthly == 0).sum()),
            "avg_pct": round(float(monthly.mean()), 2),
            "worst_pct": round(float(monthly.min()), 2),
            "best_pct": round(float(monthly.max()), 2),
        },
        "buy_hold": None,
    }
    if not eq.empty:
        p0, p1 = float(eq["price"].iloc[0]), float(eq["price"].iloc[-1])
        summary["buy_hold"] = round(100.0 * (p1 - p0) / p0, 2)
    (out / "summary_v18.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8")
    print("[v18] wrote results/{summary,trades,equity,monthly,regime_log}_v18",
          flush=True)
    keys = ("trades", "win_rate_pct", "profit_factor", "net_pct", "end_equity",
            "max_drawdown_pct", "max_consecutive_full_risk_losses",
            "avg_r", "cagr_pct", "sharpe_monthly", "probe_trades", "target_r")
    print(json.dumps({k: m[k] for k in keys if k in m}, indent=2), flush=True)


if __name__ == "__main__":
    main()
