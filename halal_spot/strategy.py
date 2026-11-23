"""V13 — Regime-Aware Multi-Arm Sniper (يُفهم السياق، لا يُطبَّق أرقام ميتة).

Design charter (user mandate):
- Classify the market REGIME first, then choose which ARM may act:
    EXPLOSIVE_UP -> RIDE (ride the rally end-to-end, structure trail, no fixed TP)
    TREND_UP     -> ACCUM (investment-style pullback entries) + RIDE
    RANGE        -> SNIP  (sweep-reclaim scalps, target = opposite edge, only >= 3R)
    TREND_DOWN   -> FALL  (trend shorts into 1h-structure retests)
                  -> DIP   (counter-trend longs on 15m capitulation sweeps)
    EXPLOSIVE_DOWN -> FALL + DIP
- Every trade must carry a structural objective >= 3R (user mandate).
- Few consecutive losses: self-calibrating quality bar (percentile of the market's
  own candidate stream) + loss-streak circuit breaker (raise bar, then stand down).
- NO absolute price/percent constants. Provenance classes:
  [M] user mandate | [X] exchange facts | [L] lineage (tested ancestor code)
  [D] derived per-bar from trailing distributions | [C] single calibration constant
- Context vetoes: regime/arm mismatch, stale regime (late), arm loss-cooldown,
  same-wave repeat, stop noise/width in ATR units, objective wall < 3R.

Lineage reused verbatim (proven in the V12 harness): TopoSwing structure engine,
futures margin accounting (10x, 0.1%/side), stop-first 5m resting-stop checks,
ImmediateFillModel entries at the signal close, EOD flatten, zero-lookahead
causal resampling (engine/causal_primitives.py copied; Volume summed separately).
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import math
from typing import Optional

import pandas as pd

# --- Binance futures symbol properties (BTCUSDT) --- [X]
TICK = 0.01
LOT = 0.001
MN = 5.5
FEE_RATE = 0.001
FEE = 0.0020            # [L] lineage round-trip fee constant (their min_r formula)
LEVERAGE = 10.0

SYMBOL = "BTCUSDT"

PRI = {"IGN": 1, "DIP": 2, "SNIP": 3, "RIDE": 4, "FALL": 5, "ACCUM": 6}   # [C] arm priority [L chain]
ARM_MODES = {
    "IGN": frozenset({"EXPLOSIVE_UP", "TREND_UP", "RANGE", "TREND_DOWN", "EXPLOSIVE_DOWN"}),
    "RIDE": frozenset({"EXPLOSIVE_UP", "TREND_UP"}),
    "ACCUM": frozenset({"TREND_UP"}),
    "FALL": frozenset({"TREND_DOWN", "EXPLOSIVE_DOWN"}),
    "DIP": frozenset({"TREND_DOWN", "EXPLOSIVE_DOWN"}),
    "SNIP": frozenset({"RANGE"}),
}
IGN_KER, IGN_RV = 0.46, 1.20      # [L] V10_IGN gates (their newest code, verbatim)
# [D] TESTED & REJECTED on BTC data: 40/42 IGN entries hit the stop in our run,
# and the owner's OWN trade log shows V10_IGN losses (XRP -6.73, AVAX -3.21).
# The 5,382% was never made by ignition entries — it was 3 bug-stuck moonbags.
IGN_ENABLED = False
BULL_MODES = frozenset({"EXPLOSIVE_UP", "TREND_UP"})
BEAR_MODES = frozenset({"TREND_DOWN", "EXPLOSIVE_DOWN"})

Q_MIN_HISTORY = 30          # [C] candidates before the adaptive bar is trusted
Q_FALLBACK = 0.50           # [C] fallback bar before history exists
PEND_MAX_5M = 6             # [L] armed-setup lifetime (lineage entk timeout)
P_Q60, P_Q75, P_Q80 = 0.60, 0.75, 0.80   # [C] quantiles of the candidate stream [D]
STREAK_LOSS_BAR = 2         # [M] raise the bar after 2 consecutive losses
STREAK_HALT = 4             # [M] stand down after 4 until the regime story changes
SWEEP_MIN = 0.44            # [L] sweep-recognition floor (their newest code)
WALL_MIN_R = 3.0            # [M] every trade: structural objective >= 3R


def _sig(x):
    return 1.0 / (1.0 + math.exp(-max(-40.0, min(40.0, x))))


def _q(sorted_vals, p):
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return float(sorted_vals[0])
    i = p * (len(sorted_vals) - 1)
    lo = int(math.floor(i))
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = i - lo
    return float(sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac)


def _pctl(dist, x):
    n = len(dist)
    if n == 0:
        return 0.5
    lt = sum(1 for v in dist if v < x)
    eq = sum(1 for v in dist if v == x)
    return (lt + 0.5 * eq) / n


# ---------------------------------------------------------------------------
# Bar
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
# TopoSwing — lineage verbatim (structure engine, incl. swp_rec)
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

    def eq_pool(self, is_h=True):
        """Equal-high/low pool (lineage verbatim) — the liquidity magnet levels."""
        arr = self.ah if is_h else self.al
        if len(arr) < 2:
            return 0.0, 0.0, 1
        atr = self.atr()
        p1, p2 = arr[-1][1], arr[-2][1]
        if abs(p1 - p2) > 0.55 * atr:
            return p1, 0.45, 1
        k = math.exp(-((p1 - p2) ** 2) / (2.0 * ((0.28 * atr) ** 2)))
        tc = sum(1 for x in arr[-6:] if abs(x[1] - p1) <= 0.45 * atr)   # (idx, px) shape here
        return (p1 + p2) * 0.5, min(0.98, 0.55 + 0.35 * k + 0.05 * tc), tc

    def swp_rec(self, o, h, l, c, lvl, sd, atr):
        """Sweep recognition quality in [0,1] (lineage verbatim)."""
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
# CoinMemory — lineage (trend anchors)
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


# ---------------------------------------------------------------------------
# Position state
# ---------------------------------------------------------------------------
class SymState:
    def __init__(self, sym):
        self.sym = sym
        self.mem = CoinMemory()
        self.sw5, self.sw15, self.sw1, self.sw4 = TopoSwing(90), TopoSwing(80), TopoSwing(80), TopoSwing(90)
        self.b15 = self.b1 = self.b4 = 0
        self.q15, self.q1, self.q4 = deque(maxlen=40), deque(maxlen=40), deque(maxlen=40)
        self.v15 = deque(maxlen=24)                 # [L] 15m volume mean for rv15
        self.pdh = self.pdl = self.pwh = self.pwl = 0.0
        self.ash = 0.0
        self.asl = 1e18                             # [L] Asia-session (00-07h) high/low
        self.cday = self.cwk = -1
        self.dh, self.dl, self.wh, self.wl = 0.0, 1e18, 0.0, 1e18
        self.sd4, self.sh4, self.sl4 = 0, 0.0, 0.0
        self.sd1, self.sh1, self.sl1 = 0, 0.0, 0.0
        self.ign = None                             # [L] V10_IGN armed ignition
        # position
        self.arm, self.sd = "", 0
        self.en = self.sl = self.tp = self.rd = self.qty = 0.0
        self.init_q = 0.0
        self.mfe = 0.0
        self.exit_design = "TRAIL"
        self.sltk: Optional[dict] = None
        self.tptk: Optional[dict] = None
        self.tp1tk: Optional[dict] = None
        self.tp1_done = False
        self.closing = False
        self.b1_at_entry = 0
        self.b4_at_entry = 0
        self.mark: dict = {}
        self.flip_streak = 0
        # [L] lineage runner-machine state (their _manage_runner)
        self.sllk = False
        self.p1d = False
        self.ms_lk = 0


# ---------------------------------------------------------------------------
# V13 engine
# ---------------------------------------------------------------------------
class RegimeEngine:
    def __init__(self, start: pd.Timestamp, capital: float = 100.0):
        self.start = start
        self.shorts = True                   # [M] shorts allowed
        self.rbudget = 0.10                  # [L] lineage risk budget
        self.pk = self.wse = capital
        self.s = SymState(SYMBOL)
        self.cd: dict = {}                   # arm cooldowns after losses [L] 4h
        # trailing distributions [D]
        self.d_e1 = deque(maxlen=600)        # 1h efficiency ker(12)
        self.d_rng10 = deque(maxlen=600)     # 10x15m range / ATR15 (compression) [D]
        self._rng10 = float("nan")
        self.d_x15 = deque(maxlen=600)       # 15m vol-expansion ratio
        self.d_v1 = deque(maxlen=600)        # 1h ATR% level
        self.d_a15 = deque(maxlen=40)        # recent 15m ATR (expansion base)
        self.d_vol5 = deque(maxlen=1440)     # 5m volume
        self.cand_q: list = []               # candidate qualities (cap 400) [D] — global stream:
        # one market-wide grading basis for every arm (per-arm bars tested and
        # rejected: they let no-edge arms in at their own median)
        # regime machine
        self.mode = "RANGE"
        self.mode_score = 0.5
        self._mcand, self._mcnt = "", 0
        self._mode_age = 0
        self._mode_durations = deque(maxlen=120)
        self.d_flipgap = deque(maxlen=120)      # 4h-bar gaps between structure flips [D]
        self._last_flip_b4 = 0
        # streak circuit [M]
        self.loss_streak = 0
        self.halt = False
        # pending armed setup
        self.pending: Optional[dict] = None
        self.pending_meta: dict = {}
        # stats / reporting
        self.count: dict = {}
        self.now = self.start
        self.price = 0.0
        self._last5h = self._last5l = 0.0
        self._close_en_pos: Optional[float] = None
        self.b5 = 0
        self._last_vol = 0.0
        self._wk = -1
        # futures margin book (proven harness) [L]
        self.cash = float(capital)
        self.margin = 0.0
        self.qty_signed = 0.0
        self.en_pos = 0.0
        self.fees_total = 0.0
        # reporting
        self.trades: list = []
        self.cur_trade: Optional[dict] = None
        self.events: list = []
        self._trade_seq = 0
        self._order_seq = 0

    # -- context helpers -----------------------------------------------------
    @property
    def is_warming_up(self) -> bool:
        return self.now < self.start

    def _log(self, typ: str, **kw) -> None:
        self.events.append({"time": self.now, "type": typ, **kw})

    def _cnt(self, key: str, n: int = 1) -> None:
        self.count[key] = self.count.get(key, 0) + n

    def _veto(self, why: str, dry: bool) -> bool:
        if not dry:
            self._cnt(why)
        return False

    def _invested(self) -> bool:
        return self.qty_signed != 0.0

    def equity(self) -> float:
        unreal = self.qty_signed * (self.price - self.en_pos) if self.qty_signed != 0.0 else 0.0
        return self.cash + self.margin + unreal

    def _ae(self) -> float:
        return max(5.0, float(self.equity()))

    def _margin_remaining(self) -> float:
        return max(0.0, self.equity() * LEVERAGE - self.margin)

    # -- lineage rounding / sizing --------------------------------------------
    def _rpx(self, px) -> float:
        return round(round(float(px) / TICK) * TICK, 8)

    def _rq(self, q, px) -> float:
        q = math.floor(abs(float(q)) / LOT) * LOT
        return round(q, 6) if (q >= LOT and q * px >= MN) else 0.0

    def _rpct(self, ap: bool) -> float:
        """[L] lineage dd-scaled base risk (their curve, verbatim shape)."""
        ae = self._ae()
        self.pk = max(self.pk, ae)
        dd = max(0.0, (self.pk - ae) / self.pk)
        bs = 0.044 if ap else 0.032
        return bs * (1.0 if dd < 0.09 else max(0.22, (1.0 - dd) ** 3.2))

    def _quant(self, arr, p) -> float:
        return _q(sorted(arr), p)

    # -- regime machine --------------------------------------------------------
    def _update_mode(self) -> None:
        """Every completed 15m close. All evidences are percentiles of own history [D]."""
        s = self.s
        px = float(self.price or 0.0)
        if s.b15 < 10 or px <= 0:
            return
        e1 = s.sw1.ker(12)
        self.d_e1.append(e1)
        a15 = s.sw15.atr()
        prior = list(self.d_a15)
        exp_ratio = (a15 / (sum(prior[-20:]) / len(prior[-20:]))) if len(prior) >= 10 else 1.0
        self.d_a15.append(a15)
        self.d_x15.append(exp_ratio)
        self.d_v1.append(s.sw1.atr() / max(px, 1e-9))

        e1p = _pctl(self.d_e1, e1)
        x15p = _pctl(self.d_x15, exp_ratio)
        volp = _pctl(self.d_v1, s.sw1.atr() / max(px, 1e-9)) if len(self.d_v1) > 20 else 0.5
        xq = _q(sorted(self.d_x15), 0.75) if len(self.d_x15) >= 30 else float("inf")
        eq = _q(sorted(self.d_e1), 0.60) if len(self.d_e1) >= 30 else 0.0
        explosive = exp_ratio >= xq and e1p >= eq

        diru = 1.0 if s.sd4 == 1 else 0.0
        dird = 1.0 if s.sd4 == -1 else 0.0
        above = 1.0 if (s.mem.e50 > 0 and px > s.mem.e50) else 0.0
        # stale structure: no fresh 4h break for longer than q75 of past gaps [D]
        # (a lingering sd4 with no new breaks IS range behaviour -> SNIP gets a life)
        stale = (len(self.d_flipgap) >= 10
                 and (s.b4 - self._last_flip_b4) > _q(sorted(self.d_flipgap), 0.75))

        if diru and explosive:
            cand, sc = "EXPLOSIVE_UP", (diru + e1p + x15p) / 3.0
        elif dird and explosive:
            cand, sc = "EXPLOSIVE_DOWN", (dird + e1p + x15p) / 3.0
        elif stale:
            cand, sc = "RANGE", ((1.0 - max(diru, dird)) + (1.0 - e1p) + (1.0 - volp)) / 3.0
        elif diru:
            cand, sc = "TREND_UP", (diru + e1p + above) / 3.0
        elif dird:
            cand, sc = "TREND_DOWN", (dird + e1p + (1.0 - above)) / 3.0
        else:
            cand, sc = "RANGE", ((1.0 - max(diru, dird)) + (1.0 - e1p) + (1.0 - volp)) / 3.0

        # hysteresis: two consecutive 15m closes agree before the story changes
        if cand == self._mcand:
            self._mcnt += 1
        else:
            self._mcand, self._mcnt = cand, 1
        if self._mcnt >= 2 and cand != self.mode:
            if self._mode_age > 0:
                self._mode_durations.append(self._mode_age)
            self.mode, self._mode_age, self.halt = cand, 0, False
            self.s.flip_streak = 0
            self._log("REGIME", mode=cand)
        else:
            self._mode_age += 1
        self.mode_score = sc
    def _mode_late(self) -> bool:
        """Regime older than q75 of past regimes -> late in the story [D]."""
        if len(self._mode_durations) < 10:
            return False
        return self._mode_age > _q(sorted(self._mode_durations), 0.75)

    # -- wall / objective: nearest structural target ------------------------------
    def _wall(self, en: float, sd: int, design: str) -> float:
        """TRAIL arms aim at MAJOR structure only (daily highs reform every day and
        would fake a 'near wall' mid-trend); TARGET arms may aim at daily/range
        destinations too (real take-profit levels)."""
        s = self.s
        if sd == 1:
            pool = [p for p in (s.pwh, s.mem.hi(30), *[x[1] for x in s.sw4.ah])
                    if p and 0 < p < 1e17 and p > en]
            if design == "TARGET":
                pool += [p for p in (s.pdh,) if p and 0 < p < 1e17 and p > en]
            return min(pool) if pool else 0.0
        pool = [p for p in (s.pwl, s.mem.lo(30), *[x[1] for x in s.sw4.al])
                if p and 0 < p < 1e17 and p < en]
        if design == "TARGET":
            pool += [p for p in (s.pdl,) if p and 0 < p < 1e17 and p < en]
        return max(pool) if pool else 0.0

    # -- order simulation (proven harness) -------------------------------------
    def _live(self, tk) -> bool:
        return tk is not None and tk["status"] not in ("FILLED", "CANCELED", "INVALID")

    def _market_fill(self, qty_signed: float, tag: str) -> dict:
        fill = self.price
        self._order_seq += 1
        od = {"id": self._order_seq, "tag": tag, "status": "FILLED",
              "fill_price": fill, "fill_quantity": qty_signed}
        if tag.startswith("EN_"):
            absq = abs(qty_signed)
            fee = absq * fill * FEE_RATE
            margin_req = absq * fill / LEVERAGE
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
            self._close_en_pos = self.en_pos      # avg entry snapshot for _fin (pyramid-aware)
            self.margin = 0.0
            self.qty_signed = 0.0
            self.en_pos = 0.0
            self.fees_total += fee
        self._on_fill(od)
        return od

    def _stop_fill(self, fill_price: float, tag: str) -> dict:
        absq = abs(self.qty_signed)
        fee = absq * fill_price * FEE_RATE
        realized = self.qty_signed * (fill_price - self.en_pos)
        self.cash += self.margin + realized - fee
        self._close_en_pos = self.en_pos          # avg entry snapshot for _fin
        self.margin = 0.0
        self.qty_signed = 0.0
        self.en_pos = 0.0
        self.fees_total += fee
        self._order_seq += 1
        od = {"id": self._order_seq, "tag": tag, "status": "FILLED",
              "fill_price": fill_price, "fill_quantity": 0.0}
        if self.s.sltk is not None:
            self.s.sltk["status"] = "FILLED"
        self._on_fill(od)
        return od

    def _pyramid(self, qty_signed: float, px: float) -> bool:
        """[L] pyramid add to the OPEN position: margin increases, average entry
        shifts, R-unit stays the original rd (their accounting: pyramid profit
        counts against the INITIAL risk — '12R becomes 14R')."""
        s = self.s
        if not self._invested() or s.closing or s.sd == 0 or self.qty_signed == 0:
            return False
        absq = abs(qty_signed)
        new_q = self.qty_signed + qty_signed
        if new_q == 0 or (new_q > 0) != (self.qty_signed > 0):
            return False
        fee = absq * px * FEE_RATE
        margin_add = absq * px / LEVERAGE
        if self.cash < margin_add + fee:
            return False
        self.en_pos = (abs(self.qty_signed) * self.en_pos + absq * px) / abs(new_q)
        self.cash -= margin_add + fee
        self.margin += margin_add
        self.qty_signed = new_q
        self.fees_total += fee
        s.qty = abs(new_q)
        if self.cur_trade is not None:
            # fold the pyramid fee into the trade's cash-flow ledger (test 8 identity)
            self.cur_trade["realized_acc"] = self.cur_trade.get("realized_acc", 0.0) - fee
            self.cur_trade["pyramid_qty"] = round(self.cur_trade.get("pyramid_qty", 0.0) + absq, 6)
        self._cnt("pyramid_filled")
        self._log("PYR", q=absq, px=px, en_pos=round(self.en_pos, 6))
        return True

    def _place_order(self, px: float, tag: str, qty: float = 0.0) -> dict:
        self._order_seq += 1
        return {"id": self._order_seq, "tag": tag, "status": "NEW", "price": px, "qty": qty}

    def _cancel(self, od: dict) -> None:
        if od is None or od["status"] in ("FILLED", "CANCELED", "INVALID"):
            return
        od["status"] = "CANCELED"
        if od["tag"].startswith("SL_"):
            self._cnt("SL_CANCELLED")
        elif od["tag"].startswith("TP_"):
            self._cnt("TP_CANCELLED")

    def _on_fill(self, od: dict) -> None:
        tag = od["tag"]
        if tag.startswith("EN_"):
            s = self.s
            s.en = float(od["fill_price"])
            s.qty = abs(float(self.qty_signed))
            s.init_q = s.qty
            s.sd = 1 if od["fill_quantity"] > 0 else -1
            s.rd = abs(s.en - s.sl)
            s.b1_at_entry, s.b4_at_entry = s.b1, s.b4
            if s.rd <= 0 or s.qty <= 0:
                self._exit("BAD_FILL")
                return
            if self.cur_trade is not None:
                ct = self.cur_trade
                ct["r_price"] = round(s.rd, 6)
                ct["risk_usd"] = round(s.rd * s.qty, 4)
                ct["sl_at_entry"] = round(s.sl, 6)
            self._cnt("entries_filled")
            self._log("ENTRY", arm=s.arm, side=s.sd, px=s.en, sl=s.sl, tp=s.tp,
                      design=s.exit_design, q=self.pending_meta.get("quality"))
            return
        # any closing fill finalizes the trade record
        self._fin(float(od["fill_price"]), tag)

    def _sync_sl(self) -> None:
        s = self.s
        if not self._invested() or s.sd == 0 or s.closing:
            return
        slp = self._rpx(s.sl)
        if s.sd * (self.price - slp) <= 0:
            self._exit("SL_CROSSED")
            return
        if self._live(s.sltk):
            s.sltk["price"] = slp
            return
        if s.sltk is not None and s.sltk["status"] == "FILLED":
            return
        s.sltk = self._place_order(slp, tag="SL_" + s.arm)

    def _raise(self, nsl: float, c: float) -> None:
        s = self.s
        if s.closing or s.sd == 0 or s.exit_design != "TRAIL":
            return
        nsl = self._rpx(nsl)
        if s.sd * (nsl - s.sl) <= 0:
            return
        if s.sd * (c - nsl) <= 0:
            self._exit("STOP_CROSSED")
            return
        s.sl = nsl
        self._sync_sl()

    def _exit(self, why: str) -> None:
        s = self.s
        if s.closing:
            return
        s.closing = True
        self._cancel(s.sltk)
        self._cancel(s.tptk)
        self._cancel(s.tp1tk)
        s.sltk = s.tptk = s.tp1tk = None
        if self.qty_signed != 0.0:
            self._market_fill(-self.qty_signed, tag="X_" + why)
        else:
            s.closing = False

    def _partial_tp1(self, px: float) -> None:
        """[L] lineage TP1: bank 30% at 1.9R, then lock stop at +0.35R (their _arm_tp
        + on_order_event numbers verbatim: tr1 = (1.9, 0.30, 0.35))."""
        s = self.s
        tk = s.tp1tk
        if tk is None or tk["status"] != "NEW":
            return
        q = float(tk.get("qty") or 0.0)
        q = min(q, abs(self.qty_signed))
        if q <= 0:
            return
        sd = s.sd
        fee = q * px * FEE_RATE
        realized = sd * q * (px - self.en_pos)
        remaining = abs(self.qty_signed - sd * q)
        margin_new = remaining * self.en_pos / LEVERAGE
        self.cash += (self.margin - margin_new) + realized - fee
        self.margin = margin_new
        self.qty_signed = self.qty_signed - sd * q
        self.fees_total += fee
        tk["status"] = "FILLED"
        s.tp1_done = True
        self._cnt("tp1_filled")
        ct = self.cur_trade
        if ct is not None:
            ct["tp1_time"] = self.now
            ct["tp1_price"] = round(px, 6)
            ct["tp1_qty"] = round(q, 6)
            ct["tp1_net"] = round(realized - fee, 4)
            ct["realized_acc"] = ct.get("realized_acc", 0.0) + realized - fee
        # lineage lock: remaining stop -> entry + 0.35R (only if it improves)
        nsl = self._rpx(s.en + sd * 0.35 * s.rd)
        if (sd == 1 and nsl > s.sl) or (sd == -1 and nsl < s.sl):
            s.sl = nsl
            if self._live(s.sltk):
                s.sltk["price"] = nsl
            else:
                s.sltk = self._place_order(nsl, tag="SL_" + s.arm)
        self._log("TP1", px=px, qty=q, lock=s.sl)

    def _manage_runner(self, h: float, l: float, c: float, is_4h: bool = False) -> None:
        """[L] lineage runner machine (their _manage_runner, verbatim numbers):
        mfe>=1.15 -> lock +0.30R; mfe>=2.0 & ker15>0.42 -> lock +1.05R (pyramid
        component omitted — sizing already uses leverage); milestones 4.2/8/14R ->
        +2.4/+5.2/+10R; chandelier from recent 10 bars (mult 2.45, or 1.85 when
        mfe>=6.5). Raise-only via _raise (crossed -> exit)."""
        s = self.s
        if s.sd == 0 or s.rd <= 0 or s.closing or self.is_warming_up or not self._invested():
            return
        r = s.rd
        nsl = s.sl
        if s.mfe >= 1.15 and not s.sllk:
            nsl = s.en + s.sd * 0.30 * r
            s.sllk = True
        if s.sllk and not s.p1d and s.mfe >= 2.0 and s.sw15.ker(10) > 0.42:
            # [L] their risk-free pyramid: +45% of init_q funded by open profit,
            # combined stop to entry + 1.05R (numbers verbatim from _manage_runner)
            pq = self._rq(abs(s.init_q) * 0.45, c)
            if pq > 0 and pq * c >= 6.0 and self.cash >= pq * c / LEVERAGE + pq * c * FEE_RATE:
                if self._pyramid(pq if s.sd == 1 else -pq, c):
                    nsl = (max(nsl, s.en + s.sd * 1.05 * r) if s.sd == 1
                           else min(nsl, s.en + s.sd * 1.05 * r))
                    s.p1d = True
        for mt, ml, idx in ((4.2, 2.4, 1), (8.0, 5.2, 2), (14.0, 10.0, 3)):
            if s.mfe >= mt and s.ms_lk < idx:
                cand = s.en + s.sd * ml * r
                nsl = (max(nsl, cand) if s.sd == 1 else min(nsl, cand))
                s.ms_lk = idx
        if s.mfe >= 2.5:
            mult = 1.85 if s.mfe >= 6.5 else 2.45
            qb = list(s.q4)[-10:] if is_4h else list(s.q15)[-10:]
            at = s.sw4.atr() if is_4h else s.sw15.atr()
            if qb:
                if s.sd == 1:
                    ch = max(x.high for x in qb) - mult * at
                    if ch > nsl and ch < c:
                        nsl = ch
                else:
                    ch = min(x.low for x in qb) + mult * at
                    if ch < nsl and ch > c:
                        nsl = ch
        if nsl != s.sl:
            self._raise(nsl, c)

    def _fin(self, px: float, tag: str) -> None:
        s = self.s
        if s.sd == 0:
            return
        avg = self._close_en_pos if getattr(self, "_close_en_pos", None) else s.en
        self._close_en_pos = None                 # one-shot snapshot (supersede falls back to s.en)
        r = s.sd * (px - avg) / s.rd if s.rd > 0 else 0.0
        rec_tag = tag[2:] if tag.startswith("X_") else tag
        if self.cur_trade is not None:
            ct = self.cur_trade
            exit_fee = s.qty * px * FEE_RATE
            realized = s.sd * s.qty * (px - avg)
            net = ct.get("realized_acc", 0.0) + realized - ct["entry_fee"] - exit_fee
            if ct.get("risk_usd"):
                r = net / ct["risk_usd"]          # streak follows NET R (fees + pyramid)
            ct["exit_time"] = self.now
            ct["exit_price"] = round(px, 6)
            ct["exit_qty"] = s.qty
            ct["exit_tag"] = rec_tag
            ct["exit_fee"] = round(exit_fee, 4)
            ct["realized"] = round(realized, 4)
            ct["net_pnl"] = round(net, 4)
            ct["r_multiple"] = round(net / ct["risk_usd"], 2) if ct.get("risk_usd") else None
            ct["mfe_r"] = round(s.mfe, 2)
            if ct.get("r_price") and ct.get("mae_min") is not None:
                adverse = (ct["mae_min"] - ct["entry_price"]) if s.sd == -1 else (ct["entry_price"] - ct["mae_min"])
                ct["mae_r"] = round(adverse / ct["r_price"], 2)
            else:
                ct["mae_r"] = None
            ct["equity_after"] = round(self.equity(), 2)
            self.trades.append(ct)
            self.cur_trade = None
        # streak circuit [M]
        if r > 0:
            self.loss_streak = 0
        else:
            self.loss_streak += 1
            self.cd[s.arm] = self.now + pd.Timedelta(hours=4)   # [L] 4h arm cooldown
            if self.loss_streak >= STREAK_HALT:
                self.halt = True
            self._log("STREAK", n=self.loss_streak, halt=self.halt)
        self._log("EXIT", arm=s.arm, tag=rec_tag, r=round(r, 2))
        s.arm, s.sd = "", 0
        s.en = s.sl = s.tp = s.rd = s.qty = s.mfe = 0.0
        s.init_q = 0.0
        s.sltk = s.tptk = s.tp1tk = None
        s.tp1_done = False
        s.closing = False
        s.flip_streak = 0
        s.sllk = s.p1d = False
        s.ms_lk = 0
        s.exit_design = "TRAIL"

    # -- quality bar (self-calibrating from own candidates) ---------------------
    def _quality_bar(self, streak: int) -> float:
        if len(self.cand_q) < Q_MIN_HISTORY:
            return Q_FALLBACK
        p = P_Q75 if streak >= STREAK_LOSS_BAR else P_Q60
        return _q(sorted(self.cand_q), p)

    # -- the gate: context -> objective -> quality -> size -----------------------
    def _consider(self, arm: str, sd: int, stop_px: float, extra: float, wave,
                  tpx: Optional[float], dry: bool) -> bool:
        s = self.s
        if arm not in ARM_MODES or self.mode not in ARM_MODES[arm]:
            return self._veto("v_regime", dry)
        # ignition must AGREE with the regime story [D]: long only in bull/range,
        # short only in bear/range — context vetoes the counter-side explosion
        if arm == "IGN" and ((sd == 1 and self.mode in BEAR_MODES) or
                             (sd == -1 and self.mode in BULL_MODES)):
            return self._veto("v_regime", dry)
        if self.halt:
            return self._veto("v_streak", dry)
        if not dry:
            if arm in self.cd and self.now < self.cd[arm]:
                return self._veto("v_cd", dry)
            if self._invested():
                return self._veto("v_slots", dry)
        en = self._rpx(self.price)
        if en <= 0:
            return self._veto("v_price", dry)
        sl = self._rpx(stop_px)
        rd = sd * (en - sl)
        a15 = s.sw15.atr()
        a4 = s.sw4.atr()
        if rd <= 0:
            return self._veto("v_stop", dry)
        if rd < a15:                        # [L] inside 15m noise (ATR units)
            return self._veto("v_noise", dry)
        if rd > 4.0 * a4:                   # [L] wider than 4x 4h ATR
            return self._veto("v_wide", dry)
        # [L] their _xexam: a major level sitting between entry and 1.5R ahead is
        # blocking structure — downweight; stacked blockers (pdh+pwh) reject.
        # IGN skips it: for ignition the broken level IS the gateway, not a wall.
        xp = 1.0
        if arm != "IGN":
            for bl, w in ((s.pdh, 0.60), (s.pdl, 0.60), (s.pwh, 0.50), (s.pwl, 0.50)):
                if bl <= 0 or bl >= 1e17:
                    continue
                if (sd == 1 and en < bl < en + 1.5 * rd) or (sd == -1 and en - 1.5 * rd < bl < en):
                    xp *= w
            if xp < 0.32:
                return self._veto("v_level", dry)
        # objective: explicit target (SNIP opposite edge) or nearest structure wall
        design = s.exit_design
        obj = tpx if tpx else self._wall(en, sd, design)
        if obj <= 0:
            return self._veto("v_wall", dry)
        wall_r = sd * (obj - en) / rd
        # [M]+[L] user mandate: objective >= 3R NET of the fee drag; lineage formula
        # min_r = 3.0 + 4.0*FEE*en/rd (their exact construction, FEE=0.0020)
        min_r = WALL_MIN_R + 4.0 * FEE * en / rd
        if wall_r < min_r:
            return self._veto("v_wall", dry)
        if wave is not None and s.mark.get((arm, sd), -1) >= wave:
            return self._veto("v_wave", dry)
        # quality evidence: equal weights, all percentile/structure based [D]
        e1p = _pctl(self.d_e1, s.sw1.ker(12))
        volp5 = _pctl(self.d_vol5, self._last_vol)
        wallq = min(1.0, wall_r / 6.0)      # [C] saturation at 6R
        terms = [self.mode_score, wallq, volp5, extra, e1p]
        if self._mode_late():
            terms = [t * 0.85 for t in terms]   # [D] late in the regime story
        q = sum(terms) / len(terms)
        # the market grades its own candidate stream (one global basis)
        if len(self.cand_q) < 400:
            self.cand_q.append(q)
        if dry:
            return False
        bar = self._quality_bar(self.loss_streak)
        if q < bar:
            return self._veto("v_quality", dry)
        # sizing [L] lineage formulas, quality-driven confidence
        ae = self._ae()
        dd = max(0.0, (self.pk - ae) / self.pk)
        ap = (q >= self._quant(self.cand_q, P_Q80)) if len(self.cand_q) >= Q_MIN_HISTORY else (q >= 0.70)
        eb = ae if dd < 0.10 else max(ae * 0.40, min(self.wse, ae))
        rk = eb * self._rpct(ap) * (0.85 + 0.40 * max(0.0, min(1.0, q * xp)))   # [L] cf x xexam
        sl_p = rd / en
        lev_cap = 3.6 if (ap and dd < 0.09) else (2.6 if ap else 1.9)
        notional = min((rk / (sl_p + 0.0012)) * (1.30 if (ap and q > 0.80) else 1.0),
                       eb * lev_cap, self._margin_remaining() * 5.8)
        if notional < 5.5:
            return self._veto("v_size", dry)
        qty = self._rq(notional / en, en)
        if qty <= 0:
            return self._veto("v_lot", dry)
        # accept
        if wave is not None:
            s.mark[(arm, sd)] = wave
        self.pending_meta = {
            "signal_time": self.now,
            "arm": arm,
            "side": "LONG" if sd == 1 else "SHORT",
            "regime": self.mode,
            "regime_score": round(self.mode_score, 4),
            "quality": round(q, 4),
            "q_threshold": round(bar, 4),
            "eff_p": round(e1p, 4),
            "vol_p": round(volp5, 4),
            "wall": round(obj, 6),
            "wall_R": round(wall_r, 4),
            "sl_at_signal": round(sl, 6),
            "en_at_signal": round(en, 6),
            "rd_at_signal": round(rd, 6),
            "tp_at_signal": round(obj, 6),
            "exit_design": s.exit_design,
            "dd_at_signal": round(dd, 4),
            "eb_at_signal": round(eb, 2),
            "rk_at_signal": round(rk, 4),
            "notional_target": round(notional, 2),
            "lev_at_entry": lev_cap,
            "equity_at_signal": round(ae, 2),
        }
        s.arm, s.sd = arm, sd
        s.sl, s.tp = sl, obj
        s.sltk = self._place_order(sl, tag="SL_" + arm)
        if s.exit_design == "TARGET":
            s.tptk = self._place_order(obj, tag="TP_" + arm)
        else:
            # [L] lineage TP3: the runner is capped only at +28R (their p3) —
            # no low ceiling on TRAIL arms; the 3R mandate lives in tp_at_signal
            s.tptk = self._place_order(self._rpx(en + sd * 28.0 * rd), tag="TP3_" + arm)
        qty_signed = qty if sd == 1 else -qty
        tk = self._market_fill(qty_signed, tag="EN_" + arm)
        if tk["status"] != "FILLED":
            self._cancel(s.sltk)
            self._cancel(s.tptk)
            s.arm, s.sd, s.sltk, s.tptk = "", 0, None, None
            self.cd[arm] = self.now + pd.Timedelta(hours=1)
            return False
        # lineage TP1: bank 30% at 1.9R (their tr1 = (1.9, 0.30, 0.35) verbatim)
        if tk["status"] == "FILLED":
            q1 = self._rq(abs(s.qty) * 0.30, s.en)
            if 0 < q1 < abs(s.qty):
                s.tp1tk = self._place_order(
                    self._rpx(s.en + s.sd * 1.9 * s.rd), tag="TP1_" + arm, qty=q1)
        self._cnt("entries_placed")
        return True

    # -- 5m resting orders: stop FIRST, then target ------------------------------
    def check_orders_5m(self, bar: Bar) -> None:
        if self.is_warming_up or not self._invested() or self.s.closing:
            return
        s = self.s
        slp = self._rpx(s.sl)
        fill = None
        tag = s.sltk["tag"] if self._live(s.sltk) else ("SL_" + s.arm)
        if s.sd == 1 and bar.low <= slp:
            fill = min(bar.open, slp)
        elif s.sd == -1 and bar.high >= slp:
            fill = max(bar.open, slp)
        if fill is not None:
            self._log("STOP_5M", tag=tag, sl=slp, fill=fill)
            self._stop_fill(fill, tag)
            return
        # lineage TP1 partial: 30% at 1.9R (checked every 5m like every resting order)
        if self._live(s.tp1tk):
            p1 = float(s.tp1tk["price"])
            f1 = None
            if s.sd == 1 and bar.high >= p1:
                f1 = max(bar.open, p1)
            elif s.sd == -1 and bar.low <= p1:
                f1 = min(bar.open, p1)
            if f1 is not None:
                self._partial_tp1(f1)
        if self._live(s.tptk):                  # TARGET wall OR TRAIL 28R runner cap
            tpp = float(s.tptk["price"])
            tfill = None
            if s.sd == 1 and bar.high >= tpp:
                tfill = max(bar.open, tpp)
            elif s.sd == -1 and bar.low <= tpp:
                tfill = min(bar.open, tpp)
            if tfill is not None:
                s.tptk["status"] = "FILLED"
                self._log("TARGET_5M", tag=s.tptk["tag"], tp=tpp, fill=tfill)
                self._market_fill(-self.qty_signed, tag="X_" + s.tptk["tag"])

    # -- 5m state + MFE/MAE --------------------------------------------------------
    def _on_5m_state(self, bar: Bar) -> None:
        s = self.s
        h, l = float(bar.high), float(bar.low)
        s.mem.on5(h, l)
        s.sw5.update(h, l, float(bar.close))        # [L] 5m topology (IGN stop uses atr5)
        self._last_vol = float(bar.volume)
        self.d_vol5.append(float(bar.volume))
        self._last5h, self._last5l = h, l           # current 5m bar for ignition stops
        dt = bar.end_time
        if dt.day != s.cday:
            if s.cday != -1:
                s.pdh, s.pdl = s.dh, s.dl
                s.mem.push(s.dh, s.dl)
            s.cday, s.dh, s.dl = dt.day, h, l
            s.ash, s.asl = h, l                     # [L] session anchors reset at day start
        else:
            s.dh, s.dl = max(s.dh, h), min(s.dl, l)
        if 0 <= dt.hour < 7:                        # [L] Asia session 00-07h
            s.ash = max(s.ash, h)
            s.asl = min(s.asl, l)
        wk = dt.isocalendar()[1]
        if wk != s.cwk:
            if s.cwk != -1:
                s.pwh, s.pwl = s.wh, s.wl
            s.cwk, s.wh, s.wl = wk, h, l
        else:
            s.wh, s.wl = max(s.wh, h), min(s.wl, l)
        # weekly start-equity anchor [L] (lineage wse)
        if wk != self._wk:
            if self._wk != -1:
                self.wse = self._ae()
            self._wk = wk
        # MFE/MAE tracking (side-aware, reporting only)
        if self.cur_trade is not None:
            t = self.cur_trade
            if s.sd == -1:
                if bar.low < t["mfe_max"]:
                    t["mfe_max"] = bar.low
                if bar.high > t["mae_min"]:
                    t["mae_min"] = bar.high
                if s.sd and s.rd > 0:
                    s.mfe = max(s.mfe, (s.en - bar.low) / s.rd)
            else:
                if bar.high > t["mfe_max"]:
                    t["mfe_max"] = bar.high
                if bar.low < t["mae_min"]:
                    t["mae_min"] = bar.low
                if s.sd and s.rd > 0:
                    s.mfe = max(s.mfe, (bar.high - s.en) / s.rd)
        # [L] lineage runner machine on every 5m close (their _on5m hook)
        self._manage_runner(h, l, float(bar.close))

    # -- detectors (15m closes) -----------------------------------------------------
    def _compressed(self) -> bool:
        """Breakout launched from compression: current 10x15m range in the bottom
        40% of its own rolling distribution [D] — hypothesis 'compression -> expansion'.
        Warmup (short history / NaN): gate open (detector dry-runs anyway)."""
        if len(self.d_rng10) < 200 or self._rng10 != self._rng10:
            return True
        return _pctl(self.d_rng10, self._rng10) < 0.40

    def _arm_pending(self, arm: str, sd: int, stop: float, design: str,
                     extra: float, wave, lvl: float, tpx: Optional[float] = None) -> bool:
        pr = PRI[arm]
        if self.pending is not None and self.pending["pri"] <= pr:
            return False
        self.pending = {"arm": arm, "sd": sd, "stop": stop, "design": design,
                        "extra": extra, "wave": wave, "pri": pr,
                        "born5": self.b5, "lvl": lvl, "tpx": tpx}
        self._cnt("cand_" + arm)
        return True

    def _on_15m(self, bar: Bar) -> None:
        s = self.s
        s.b15 += 1
        s.q15.append(bar)
        s.v15.append(float(bar.volume))
        h, l, c, o = float(bar.high), float(bar.low), float(bar.close), float(bar.open)
        s.sw15.update(h, l, c)
        if len(s.q15) < 8:
            return
        self._update_mode()
        # regime-aware exit: two closes against the position's story -> out [D]
        # ONLY for TRAIL (trend-riding) designs: counter-trend TARGET arms (DIP/SNIP)
        # are bounded by stop+target; their thesis never was 'regime stays this way'.
        if self._invested() and not s.closing and s.exit_design == "TRAIL":
            against = (s.sd == 1 and self.mode in BEAR_MODES) or (s.sd == -1 and self.mode in BULL_MODES)
            s.flip_streak = s.flip_streak + 1 if against else 0
            if s.flip_streak >= 2:
                self._exit("FLIP_" + s.arm)
        a15 = s.sw15.atr()
        prev = list(s.q15)[:-1]
        # compression ratio of the last 10 x 15m bars (range / ATR15) [D] —
        # hypothesis 'compression -> expansion': breakouts launch from compression
        self._rng10 = float("nan")
        if len(prev) >= 10 and a15 > 0:
            w = prev[-10:]
            self._rng10 = (max(x.high for x in w) - min(x.low for x in w)) / a15
            self.d_rng10.append(self._rng10)
        # V10_IGN: failed-sweep ignition — a level is swept, then price ACCEPTS
        # through it with force (high KER + high RVOL + wide body) [L verbatim
        # from their newest code: ker15>0.46, rv15>1.20, body>0.45 of range]
        if s.ign is not None and (s.b15 - s.ign[3]) > 4:
            s.ign = None
        if s.ign is None and IGN_ENABLED:
            eh, _, th = s.sw15.eq_pool(True)
            el, _, tl = s.sw15.eq_pool(False)
            v15m = max(sum(s.v15) / len(s.v15), 1e-8) if s.v15 else 1.0
            rv15 = float(bar.volume) / v15m
            ker15 = s.sw15.ker(8)
            if ker15 > IGN_KER and rv15 > IGN_RV:
                lvls = ((eh, -1, th), (el, 1, tl), (s.ash, -1, 2), (s.asl, 1, 2),
                        (s.pdh, -1, 3), (s.pdl, 1, 3), (s.pwh, -1, 3), (s.pwl, 1, 3))
                for lvl, sd_l, tc in lvls:
                    if lvl <= 0 or lvl >= 1e17:
                        continue
                    cf = min(0.96, 0.65 + 0.20 * ker15 + 0.08 * tc)
                    if cf < 0.78:
                        continue
                    if sd_l == -1 and o <= lvl and c > lvl + 0.18 * a15 and (c - o) > 0.45 * (h - l):
                        s.ign = (1, lvl, cf, s.b15, min(l, lvl - 0.35 * a15))
                        break
                    if sd_l == 1 and o >= lvl and c < lvl - 0.18 * a15 and (o - c) > 0.45 * (h - l):
                        s.ign = (-1, lvl, cf, s.b15, max(h, lvl + 0.35 * a15))
                        break
        if len(prev) >= 20:
            hi20 = max(x.high for x in prev[-20:])
            lo20 = min(x.low for x in prev[-20:])
            # SNIP: sweep of the range edge + reclaim back inside (RANGE)
            # target = OPPOSITE edge of the range (the classic mean-revert objective)
            if self.mode == "RANGE":
                if h > hi20 and c < hi20:
                    sc = s.sw15.swp_rec(o, h, l, c, hi20, -1, a15)
                    if sc > SWEEP_MIN:
                        self._arm_pending("SNIP", -1, h + 0.35 * a15, "TARGET", sc, None, hi20, tpx=lo20)
                elif l < lo20 and c > lo20:
                    sc = s.sw15.swp_rec(o, h, l, c, lo20, 1, a15)
                    if sc > SWEEP_MIN:
                        self._arm_pending("SNIP", 1, l - 0.35 * a15, "TARGET", sc, None, lo20, tpx=hi20)
            # DIP: 15m capitulation sweep + same-bar reclaim (bear modes)
            if self.mode in BEAR_MODES and s.sw15.al:
                li, lvl = s.sw15.al[-1]
                if li <= s.b15 - 1 and l < lvl and c > lvl and (c - o) > 0:
                    sc = s.sw15.swp_rec(o, h, l, c, lvl, 1, a15)
                    if sc > SWEEP_MIN:
                        self._arm_pending("DIP", 1, l - 0.35 * a15, "TARGET", sc, None, lvl)
            # FALL: retest of broken 1h swing low from below (bear modes) —
            # only from compression [D] (hypothesis: compression -> expansion)
            if self.mode in BEAR_MODES and s.sl1 > 0 and self._compressed():
                sc = s.sw15.swp_rec(o, h, l, c, s.sl1, -1, a15)
                if sc > SWEEP_MIN:
                    self._arm_pending("FALL", -1, max(h, s.sl1) + 0.35 * a15, "TRAIL", sc, s.b15, s.sl1)
            # RIDE: 15m breakout of the last 10-bar high (up modes) — only from
            # compression [D] (hypothesis: compression -> expansion)
            if self.mode in BULL_MODES and len(prev) >= 10 and self._compressed():
                h10 = max(x.high for x in prev[-10:])
                if c > h10 and (c - o) > 0:
                    stop = min(l, min(x.low for x in prev[-6:])) - 0.5 * a15
                    extra = _pctl(self.d_x15, list(self.d_x15)[-1]) if self.d_x15 else 0.5
                    self._arm_pending("RIDE", 1, stop, "TRAIL", extra, s.b15, 0.0)
            # ACCUM: pullback into prior 15m swing high + reclaim (TREND_UP)
            if self.mode == "TREND_UP" and s.sw15.ah:
                li, h_lvl = s.sw15.ah[-1]
                if li <= s.b15 - 1 and l <= h_lvl + 0.15 * a15 and c > h_lvl and (c - o) > 0:
                    stop = min(l, h_lvl - 0.5 * a15)
                    extra = 1.0 - (_pctl(self.d_x15, list(self.d_x15)[-1]) if self.d_x15 else 0.5)
                    self._arm_pending("ACCUM", 1, stop, "TRAIL", extra, s.b15, h_lvl)

    # -- 1h structure + trails -------------------------------------------------------
    def _on_1h(self, bar: Bar) -> None:
        s = self.s
        s.b1 += 1
        s.q1.append(bar)
        h, l, c = float(bar.high), float(bar.low), float(bar.close)
        s.mem.on1h(c)
        s.sw1.update(h, l, c)
        if s.sw1.ah:
            s.sh1 = s.sw1.ah[-1][1]
        if s.sw1.al:
            s.sl1 = s.sw1.al[-1][1]
        if s.sh1 > 0 and c > s.sh1:
            s.sd1 = 1
        elif s.sl1 > 0 and c < s.sl1:
            s.sd1 = -1
        if self.is_warming_up or not self._invested() or s.closing:
            return
        if s.exit_design == "TRAIL" and s.sd == 1 and s.sw1.al:
            for li, lvl in reversed(s.sw1.al):
                if li > s.b1_at_entry:
                    self._raise(lvl - 0.5 * s.sw1.atr(), c)   # [L] pad 0.5xATR1
                    break
        elif s.exit_design == "TRAIL" and s.sd == -1 and s.sw1.ah:
            for hi, lvl in reversed(s.sw1.ah):
                if hi > s.b1_at_entry:
                    self._raise(lvl + 0.5 * s.sw1.atr(), c)
                    break

    # -- 4h structure + trails -------------------------------------------------------
    def _on_4h(self, bar: Bar) -> None:
        s = self.s
        s.b4 += 1
        s.q4.append(bar)
        h, l, c = float(bar.high), float(bar.low), float(bar.close)
        s.mem.on4h(c)
        s.sw4.update(h, l, c)
        if len(s.q4) < 16:
            return
        if s.sh4 == 0.0:
            s.sh4, s.sl4 = max(x.high for x in s.q4), min(x.low for x in s.q4)
        if s.sw4.ah:
            s.sh4 = s.sw4.ah[-1][1]
        if s.sw4.al:
            s.sl4 = s.sw4.al[-1][1]
        prev_sd = s.sd4
        if c > s.sh4:
            s.sd4, s.sh4 = 1, h
        elif c < s.sl4:
            s.sd4, s.sl4 = -1, l
        if prev_sd != 0 and s.sd4 != prev_sd:
            if self._last_flip_b4 > 0:
                self.d_flipgap.append(s.b4 - self._last_flip_b4)
            self._last_flip_b4 = s.b4
        if self.is_warming_up or not self._invested() or s.closing:
            return
        if s.exit_design == "TRAIL" and s.sd == 1 and s.sw4.al:
            for li, lvl in reversed(s.sw4.al):
                if li > s.b4_at_entry:
                    self._raise(lvl - 1.5 * s.sw4.atr(), c)   # [L] pad 1.5xATR4
                    break
        elif s.exit_design == "TRAIL" and s.sd == -1 and s.sw4.ah:
            for hi, lvl in reversed(s.sw4.ah):
                if hi > s.b4_at_entry:
                    self._raise(lvl + 1.5 * s.sw4.atr(), c)
                    break

    # -- consume armed setups on 5m ---------------------------------------------------
    def _on_5m_consume(self) -> None:
        s = self.s
        # V10_IGN has chain priority [L]: enter when the 5m CLOSE holds beyond the
        # broken level; stop = sweep extreme - 0.25*ATR5 (their formula verbatim)
        if s.ign is not None and IGN_ENABLED:
            sd, lvl, cf_, _born, sl_px = s.ign
            ok = (self.price > lvl) if sd == 1 else (self.price < lvl)
            if ok:
                a5 = s.sw5.atr()
                if sd == 1:
                    stop = min(self._last5l, sl_px) - 0.25 * a5
                else:
                    stop = max(self._last5h, sl_px) + 0.25 * a5
                self.s.exit_design = "TRAIL"
                self._cnt("cand_IGN")
                if self._consider("IGN", sd, stop, cf_, None, None, dry=self.is_warming_up):
                    s.ign = None
                    return
        pend = self.pending
        if pend is None:
            return
        if self.b5 - pend["born5"] > PEND_MAX_5M:
            self._veto("exp_pending", dry=False)
            self.pending = None
            return
        if self._invested():
            return
        arm, sd, lvl = pend["arm"], pend["sd"], pend.get("lvl", 0.0)
        ok = True
        if arm == "DIP" and lvl > 0:   # reclaim must hold on the 5m close [M: causal]
            ok = (self.price > lvl) if sd == 1 else (self.price < lvl)
        if arm == "SNIP" and lvl > 0:  # still inside the range at consume
            ok = (self.price < lvl) if sd == -1 else (self.price > lvl)
        if not ok:
            return
        self.pending = None
        self.s.exit_design = pend["design"]
        self._consider(arm, sd, pend["stop"], pend["extra"], pend["wave"],
                       pend.get("tpx"), dry=self.is_warming_up)

    # -- reporting ---------------------------------------------------------------------
    def close_eod(self) -> None:
        s = self.s
        if self.pending is not None:
            self._cnt("exp_eod")
            self.pending = None
        if s.sd != 0 and self._invested():
            self._exit("EOD")
        if self.cur_trade is not None:
            self._fin(self.price, "X_EOD")

    def end_of_algorithm(self) -> dict:
        return {
            "vetoes": dict(sorted(self.count.items())),
            "fees_total": round(self.fees_total, 4),
            "equity": round(self.equity(), 2),
            "mode_final": self.mode,
            "loss_streak": self.loss_streak,
        }

    # -- trade records (reporting only) -------------------------------------------------
    def _open_trade(self, meta: dict, qty_signed: float, fill: float,
                    fee: float, margin_req: float) -> None:
        if self.cur_trade is not None:
            self._fin(fill, "SUPERSEDED")
        self._trade_seq += 1
        absq = abs(qty_signed)
        self.cur_trade = {
            "trade_id": self._trade_seq,
            "symbol": SYMBOL,
            **meta,
            "entry_time": self.now,
            "entry_price": round(fill, 6),
            "entry_qty": absq,
            "entry_notional": round(absq * fill, 2),
            "entry_fee": round(fee, 4),
            "margin_used": round(margin_req, 4),
            "r_price": None,
            "risk_usd": None,
            "sl_at_entry": None,
            "equity_at_entry": round(self.equity(), 2),
            "exit_time": None,
            "exit_price": None,
            "exit_qty": None,
            "exit_tag": None,
            "exit_fee": None,
            "realized": None,
            "net_pnl": None,
            "r_multiple": None,
            "mfe_r": None,
            "mae_r": None,
            "equity_after": None,
            "tp1_time": None,
            "tp1_price": None,
            "tp1_qty": None,
            "tp1_net": None,
            "realized_acc": 0.0,
            "mfe_max": fill,
            "mae_min": fill,
        }


# ---------------------------------------------------------------------------
# Backtest runner (zero-lookahead: causal resample + stop-first 5m rules)
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
        """Causal volume sums on the exact same left-closed bins (engine drops Volume)."""
        rule = {"5m": "5min", "15m": "15min", "30m": "30min"}.get(freq, freq)
        v = df["Volume"].resample(rule, label="left", closed="left").sum()
        v.index = v.index + pd.Timedelta(rule)
        v = v.reindex(tf_df.index).fillna(0.0)
        return {t: float(v.loc[t]) for t in tf_df.index}

    v15, v1, v4 = _vol_of(tf15, "15m"), _vol_of(tf1, "1h"), _vol_of(tf4, "4h")
    m15 = {t: r for t, r in tf15.iterrows()}
    m1 = {t: r for t, r in tf1.iterrows()}
    m4 = {t: r for t, r in tf4.iterrows()}

    eng = RegimeEngine(start=start_ts, capital=capital)

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
        eng.b5 += 1

        eng._on_5m_state(bar)        # day/week/anchor/MFE bookkeeping
        eng.check_orders_5m(bar)     # (1) resting stop FIRST, then target
        eng._on_5m_consume()         # (2) consume armed setup (immediate fill)

        r15 = m15.get(t)             # (3) 15m: mode machine + detectors
        if r15 is not None:
            eng._on_15m(Bar(t, float(r15.Open), float(r15.High), float(r15.Low),
                            float(r15.Close), v15.get(t, 0.0)))
        r1 = m1.get(t)               # (4) 1h: structure + trails
        if r1 is not None:
            eng._on_1h(Bar(t, float(r1.Open), float(r1.High), float(r1.Low),
                           float(r1.Close), v1.get(t, 0.0)))
        r4 = m4.get(t)               # (5) 4h: structure + trails
        if r4 is not None:
            eng._on_4h(Bar(t, float(r4.Open), float(r4.High), float(r4.Low),
                           float(r4.Close), v4.get(t, 0.0)))

        if t >= start_ts:            # equity curve (trading period only)
            eng.events  # noqa: B018 (touch to keep attribute alive)
            rows = getattr(eng, "_eq_rows", None)
            if rows is None:
                rows = []
                eng._eq_rows = rows
            rows.append({
                "time": t,
                "equity": round(eng.equity(), 4),
                "usdt": round(eng.cash, 4),
                "btc": eng.qty_signed,
                "price": bar.close,
                "in_position": bool(eng._invested() or eng.pending is not None),
            })

    eng.now = end_ts
    eng.close_eod()
    end_log = eng.end_of_algorithm()

    equity = (pd.DataFrame(getattr(eng, "_eq_rows", [])).set_index("time")
              if getattr(eng, "_eq_rows", None) else pd.DataFrame())
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
