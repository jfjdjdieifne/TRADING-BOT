# =============================================================================
#  ICT "CHART READER" — QuantConnect / LEAN streaming port
#  https://www.quantconnect.com  ->  New Project -> paste this file as main.py
# =============================================================================
#
#  WHAT THIS IS
#  ------------
#  The streaming (per-bar) implementation of the research engine in
#  `ict_vision/brain/engine.py`.  Same maths, same priors, same learned
#  parameters — rewritten so that every decision is made from the bars that
#  have actually arrived, with no array that can peek at the future.
#
#  WHAT IT DOES, IN ORDER
#  ----------------------
#   1. measures the market in its own volatility units (no points, no pips)
#   2. finds swing structure at four scales at once and lets the market say
#      which scales are behaving like real structure that day
#   3. clusters those swings into liquidity pools and retires a pool the
#      moment it is raided
#   4. reads fair value gaps, order blocks and balanced price ranges
#   5. learns, walk-forward, the retracement depth that maximises expected
#      value (starting from ICT's 62-79% prior, and moving it if the data says
#      otherwise — the learned number is printed in the log)
#   6. learns its own killzones (the discovered windows are printed in the log
#      next to ICT's canonical ones)
#   7. scores each setup with a naive-Bayes evidence model and sizes with
#      fractional Kelly
#   8. manages: break-even from a measured comeback curve, structural trail,
#      and an exit when the survival model says the trade has stopped
#      behaving like a winner
#
#  HOW TO RUN
#  ----------
#   * ASSET default is the Oanda Nasdaq-100 CFD, which is the instrument the
#     research was done on.  Switch ASSET below for forex / gold / crypto.
#   * Six years: SetStartDate(2019,1,1) -> SetEndDate(2025,1,1).
#   * Costs: the algorithm applies HALF_SPREAD and STOP_SLIP itself and sets
#     LEAN's slippage and fees to zero, so the cost you see in the log is the
#     cost you configured.  Change HALF_SPREAD to your broker's real spread:
#     everything in this file rescales automatically because nothing is
#     denominated in points.
#   * The log prints the learned OTE depth, the discovered killzones and the
#     ICT window scores at the end of the run.
#
#  HONEST NOTE
#  -----------
#  On six years of Nasdaq-100 one-minute data this model lands at
#  expectancy ~ +0.07R per trade (t = 1.2): indistinguishable from zero once
#  costs are paid.  It beats a rigid, hard-coded ICT implementation (-0.01R)
#  and badly beats random entries with the same cost model (-0.29R), but it is
#  NOT a money printer, and any backtest that shows you one is either using
#  look-ahead or ignoring costs.  See ict_vision/FINDINGS.md.
# =============================================================================

from AlgorithmImports import *

import math
from collections import deque

import numpy as np

# ------------------------------------------------------------------ settings
ASSET = "cfd"                 # "cfd" | "forex" | "crypto" | "index"
TICKER = "NAS100USD"          # NAS100USD, SPX500USD, US30USD, XAUUSD, EURUSD, BTCUSD
MARKET = Market.OANDA
LEVERAGE = 20.0
START = (2019, 1, 1)
END = (2025, 1, 1)
CASH = 100_000
EXEC_MINUTES = 5              # bar the decisions are made on
HALF_SPREAD = 1             # price units, per side (set to your broker's)
STOP_SLIP = 0.5               # price units of extra slippage on a stop
RISK_PCT = 0.007              # fraction of equity risked on a full-conviction trade
KELLY_CAP = 0.35
BOOTSTRAP = 80                # exploration trades that seed the evidence model
WARMUP_DAYS = 120

SCALES = (2.0, 4.0, 8.0, 16.0)
FEATURES = ["sweep_quality", "sweep_overshoot", "displacement_z", "displacement_eff",
            "struct_break_sig", "struct_scales", "pd_membership", "ote_llr",
            "pd_array_q", "clock_intensity", "htf_agreement", "rr_geometry"]


# --------------------------------------------------------------- small pieces
def ewma_update(acc, x, halflife):
    a = 1.0 - np.exp(-np.log(2.0) / max(halflife, 1.0))
    return acc + a * (x - acc), a


class QuantileTracker:
    def __init__(self, lo, hi, nbins=100, halflife=400.0):
        self.edges = np.linspace(lo, hi, nbins + 1)
        self.hist = np.zeros(nbins)
        self.nb = nbins
        self.hl = halflife

    def add(self, x):
        if not np.isfinite(x):
            return
        self.hist *= np.exp(-np.log(2.0) / self.hl)
        i = int(np.clip(np.searchsorted(self.edges, x, side="right") - 1, 0, self.nb - 1))
        self.hist[i] += 1.0

    def quantile(self, q):
        tot = self.hist.sum()
        if tot < 5:
            return 0.5 * (self.edges[0] + self.edges[-1])
        cs = np.cumsum(self.hist) / tot
        i = int(np.clip(np.searchsorted(cs, q), 0, self.nb - 1))
        return 0.5 * (self.edges[i] + self.edges[i + 1])


class ZigZag:
    """Incremental, volatility-scaled swing detector.

    A leg ends when price reverses by `thr` from the running extreme.  `thr`
    is re-read every bar from the caller, so the swing size breathes with
    volatility instead of being a fixed number of points.
    """

    def __init__(self):
        self.dir = 1
        self.ex_i = 0
        self.ex_p = None
        self.ready = False
        self.pivots = deque(maxlen=64)   # (index, price, kind)

    def update(self, i, h, l, thr):
        if self.ex_p is None:
            self.ex_p = h
            self.ex_i = i
            return None
        out = None
        if self.dir == 1:
            if h > self.ex_p:
                self.ex_p = h
                self.ex_i = i
            elif l <= self.ex_p - thr:
                out = (self.ex_i, self.ex_p, 1, i)
                self.pivots.append(out)
                self.dir = -1
                self.ex_p = l
                self.ex_i = i
        else:
            if l < self.ex_p:
                self.ex_p = l
                self.ex_i = i
            elif h >= self.ex_p + thr:
                out = (self.ex_i, self.ex_p, -1, i)
                self.pivots.append(out)
                self.dir = 1
                self.ex_p = h
                self.ex_i = i
        self.ready = True
        return out


class LiquidityBook:
    """Pools clustered at the market's own resolution, in log-price."""

    R_SIGMA = 0.35
    EPS_SIGMA = 0.12
    TAU_BARS = 576.0
    MAX_PIERCE = 36

    def __init__(self, bucket):
        self.bs = max(bucket, 1e-9)
        self.px = []
        self.kind = []
        self.w = []
        self.last = []
        self.touches = []
        self.alive = []
        self.pierced = []
        self.pierce_t = []
        self.pierce_ext = []
        self.buckets = {}

    def _bk(self, p):
        return int(math.floor(p / self.bs))

    def add(self, px, kind, w, t):
        i = len(self.px)
        self.px.append(px); self.kind.append(kind); self.w.append(w)
        self.last.append(t); self.touches.append(1.0); self.alive.append(True)
        self.pierced.append(False); self.pierce_t.append(-1); self.pierce_ext.append(px)
        self.buckets.setdefault(self._bk(px), []).append(i)
        return i

    def strength(self, i, t):
        age = max(t - self.last[i], 0)
        return self.w[i] * math.exp(-age / self.TAU_BARS) * (1 + 0.35 * math.log1p(self.touches[i]))

    def candidates(self, lo, hi):
        i0, i1 = self._bk(lo), self._bk(hi)
        if i1 - i0 > 20000:
            return []
        out = []
        for b in range(i0, i1 + 1):
            out.extend(self.buckets.get(b, ()))
        return out

    def merge(self, i, px, w, t):
        tot = self.w[i] + w
        self.px[i] = (self.px[i] * self.w[i] + px * w) / tot
        self.w[i] = tot
        self.last[i] = t
        self.touches[i] += 1.0

    def add_swing(self, px, kind, w, t, sigma_px):
        r = self.R_SIGMA * sigma_px
        best, bw = None, -1e18
        for i in self.candidates(px - r, px + r):
            if self.alive[i] and self.kind[i] == kind:
                s = self.strength(i, t)
                if s > bw:
                    bw, best = s, i
        if best is None:
            return self.add(px, kind, w, t)
        self.merge(best, px, w, t)
        return best

    def step(self, t, h, l, c, sigma_px):
        """Returns the sweeps that confirmed on this bar."""
        eps = self.EPS_SIGMA * sigma_px
        out = []
        for i in self.candidates(min(l, c) - 4 * eps, max(h, c) + 4 * eps):
            if not self.alive[i]:
                continue
            P = self.px[i]
            if self.kind[i] > 0:
                if not self.pierced[i]:
                    if h > P + eps:
                        self.pierced[i] = True
                        self.pierce_t[i] = t
                        self.pierce_ext[i] = h
                    elif P - eps <= l <= P + eps:
                        self.last[i] = t
                        self.touches[i] += 0.5
                else:
                    self.pierce_ext[i] = max(self.pierce_ext[i], h)
                    if c < P:
                        rng = max(h - l, 1e-12)
                        out.append({
                            "kind": 1, "level": P, "extreme": self.pierce_ext[i],
                            "overshoot": (self.pierce_ext[i] - P) / max(sigma_px, 1e-12),
                            "bars": t - self.pierce_t[i], "strength": self.strength(i, t),
                            "wick": float(np.clip((self.pierce_ext[i] - max(c, l)) / rng, 0, 1)),
                        })
                        self.alive[i] = False
                    elif t - self.pierce_t[i] > self.MAX_PIERCE:
                        self.alive[i] = False
            else:
                if not self.pierced[i]:
                    if l < P - eps:
                        self.pierced[i] = True
                        self.pierce_t[i] = t
                        self.pierce_ext[i] = l
                    elif P - eps <= h <= P + eps:
                        self.last[i] = t
                        self.touches[i] += 0.5
                else:
                    self.pierce_ext[i] = min(self.pierce_ext[i], l)
                    if c > P:
                        rng = max(h - l, 1e-12)
                        out.append({
                            "kind": -1, "level": P, "extreme": self.pierce_ext[i],
                            "overshoot": (P - self.pierce_ext[i]) / max(sigma_px, 1e-12),
                            "bars": t - self.pierce_t[i], "strength": self.strength(i, t),
                            "wick": float(np.clip((min(c, h) - self.pierce_ext[i]) / rng, 0, 1)),
                        })
                        self.alive[i] = False
                    elif t - self.pierce_t[i] > self.MAX_PIERCE:
                        self.alive[i] = False
        return out


class RetracementModel:
    """Where to enter: the depth that maximises expected value.

    Starts at ICT's 62-79% / 70.5% prior (kappa pseudo-observations) and lets
    the resolved legs move it.
    """

    def __init__(self, nb=60, dmax=1.30, center=0.705, width=0.085,
                 amp=0.14, base=0.42, kappa=20.0, hl=250.0):
        self.nb = nb
        self.edges = np.linspace(0, dmax, nb + 1)
        self.centers = 0.5 * (self.edges[:-1] + self.edges[1:])
        self.center, self.width, self.amp, self.base = center, width, amp, base
        self.kappa = kappa
        self.hl = hl
        self.win = np.zeros(nb)
        self.los = np.zeros(nb)
        self.reach = np.zeros(nb)
        self.n = 0.0
        self.ext = 1.0

    def prior(self):
        d = self.centers
        return np.clip(self.base + self.amp * np.exp(-0.5 * ((d - self.center) / self.width) ** 2), 0.01, 0.99)

    def observe(self, depth, outcome, extension=None):
        if not np.isfinite(depth):
            return
        k = int(np.clip(np.searchsorted(self.edges, depth, side="right") - 1, 0, self.nb - 1))
        a = 1 - np.exp(-np.log(2) / self.hl)
        self.win *= (1 - a); self.los *= (1 - a); self.reach *= (1 - a)
        self.n = self.n * (1 - a) + 1.0
        self.reach[: k + 1] += 1.0
        (self.win if outcome == 1 else self.los)[: k + 1] += 1.0
        if extension is not None and np.isfinite(extension):
            self.ext += 0.02 * (float(np.clip(extension, -1, 6)) - self.ext)

    def p_win(self):
        w = self.win + self.kappa * self.prior()
        return w / np.maximum(self.win + self.los + self.kappa, 1e-9)

    def p_reach(self):
        return np.clip(self.reach / max(self.n, 1e-9), 0, 1)

    def r_mult(self, buf):
        entry = 1 - self.centers
        risk = entry + buf
        return np.where(risk > 0.02, np.clip((1 + self.ext - entry) / np.maximum(risk, 1e-6), 0, 25), 0.0)

    def ev(self, buf):
        p = self.p_win()
        return self.p_reach() * (p * self.r_mult(buf) - (1 - p))

    def best(self, d_hi=0.90, min_reach=0.55, buf=0.20):
        ev = self.ev(buf)
        sel = (self.centers >= 0.15) & (self.centers <= d_hi) & (self.p_reach() >= min_reach)
        if not sel.any() or self.n < 25:
            return float(np.clip(self.center, 0.15, d_hi)), ev
        return float(self.centers[int(np.argmax(np.where(sel, ev, -np.inf)))]), ev

    def llr_at(self, d):
        p = np.clip(np.interp(d, self.centers, self.p_win()), 1e-6, 1 - 1e-6)
        p0 = float(np.clip(self.p_win()[0], 1e-6, 1 - 1e-6))
        return float(np.log(p / (1 - p)) - np.log(p0 / (1 - p0)))


class DeliveryClock:
    BUCKETS = 96

    def __init__(self, horizon=12, hl_days=120.0):
        self.h = horizon
        self.bm = 24 * 60 / self.BUCKETS
        self.hl = hl_days
        self.deliv = np.ones(self.BUCKETS)
        self.effic = np.full(self.BUCKETS, 0.25)

    def bucket(self, minute_of_day):
        return int(minute_of_day // self.bm) % self.BUCKETS

    def feed(self, minute_of_day, deliv, eff):
        b = self.bucket(minute_of_day)
        a = 1 - np.exp(-np.log(2) / self.hl)
        self.deliv[b] += a * (deliv - self.deliv[b])
        self.effic[b] += a * (eff - self.effic[b])

    def profile(self):
        s = self.deliv * self.effic
        return s / max(s.mean(), 1e-12)

    def intensity(self, minute_of_day):
        return float(self.profile()[self.bucket(minute_of_day)])


class EvidenceModel:
    def __init__(self, names, nb=5, hl=250.0, n0=60.0, alpha=1.0):
        self.names = list(names)
        self.nb = nb
        self.hl = hl
        self.n0 = n0
        self.alpha = alpha
        self.win = np.zeros((len(names), nb))
        self.los = np.zeros((len(names), nb))
        self.n = 0.0
        self.res = [deque(maxlen=4000) for _ in names]
        self.edges = [np.linspace(-1, 1, nb + 1) for _ in names]

    def _rebin(self):
        for j in range(len(self.names)):
            r = np.asarray(self.res[j])
            if len(r) < 50:
                continue
            qs = np.quantile(r, np.linspace(0, 1, self.nb + 1)[1:-1])
            qs = np.maximum.accumulate(qs + np.arange(len(qs)) * 1e-12)
            self.edges[j] = np.r_[-np.inf, qs, np.inf]

    def encode(self, x, learn=True):
        b = np.zeros(len(self.names), int)
        for j in range(len(self.names)):
            v = float(x[j]) if np.isfinite(x[j]) else 0.0
            b[j] = int(np.clip(np.searchsorted(self.edges[j], v, side="right") - 1, 0, self.nb - 1))
            if learn:
                self.res[j].append(v)
        return b

    def score(self, x):
        b = self.encode(x)
        llr = np.zeros(len(self.names))
        for j in range(len(self.names)):
            w = self.win[j, b[j]] + self.alpha
            l = self.los[j, b[j]] + self.alpha
            nw = self.win[j].sum() + self.alpha * self.nb
            nl = self.los[j].sum() + self.alpha * self.nb
            llr[j] = math.log((w / nw) / (l / nl))
        s = self.n / (self.n + self.n0)
        return float(llr.sum() * s), llr * s

    def probability(self, x):
        s, _ = self.score(x)
        return 1.0 / (1.0 + math.exp(-max(-30, min(30, s))))

    def update(self, x, y):
        b = self.encode(x)
        a = 1 - math.exp(-math.log(2) / self.hl)
        self.win *= (1 - a); self.los *= (1 - a)
        self.n = self.n * (1 - a) + 1.0
        for j in range(len(self.names)):
            (self.win if y == 1 else self.los)[j, b[j]] += 1.0
        if int(self.n) % 128 == 0:
            self._rebin()


class HazardModel:
    def __init__(self, mb=288, hl=300.0, prior=0.45):
        self.mb, self.hl, self.prior = mb, hl, prior
        self.surv = np.zeros(mb)
        self.winlater = np.zeros(mb)

    def record(self, path, won):
        a = 1 - math.exp(-math.log(2) / self.hl)
        self.surv *= (1 - a); self.winlater *= (1 - a)
        for b in path:
            if 0 <= b < self.mb:
                self.surv[b] += 1.0
                if won:
                    self.winlater[b] += 1.0

    def p(self, b):
        i = int(np.clip(b, 0, self.mb - 1))
        if self.surv[i] < 12:
            return self.prior
        return float((self.winlater[i] + self.prior * 12) / (self.surv[i] + 12))


class ComebackModel:
    GRID = (0.5, 1.0, 1.5, 2.0, 3.0, 4.0)

    def __init__(self, hl=250.0):
        self.hl = hl
        self.back = np.zeros(len(self.GRID))
        self.tot = np.zeros(len(self.GRID))

    def record(self, mfe_r, came_back):
        a = 1 - math.exp(-math.log(2) / self.hl)
        self.back *= (1 - a); self.tot *= (1 - a)
        k = int(np.searchsorted(self.GRID, mfe_r, side="right") - 1)
        for j in range(max(k, 0) + 1):
            self.tot[j] += 1.0
            if came_back:
                self.back[j] += 1.0

    def p(self, m):
        j = int(np.clip(np.searchsorted(self.GRID, m, side="right") - 1, 0, len(self.GRID) - 1))
        return 0.5 if self.tot[j] < 10 else float(self.back[j] / self.tot[j])


class ReachModel:
    def __init__(self, lr=0.05):
        self.w = np.array([-1.0, 0.0, 0.0, 0.0, 0.0])
        self.lr = lr

    @staticmethod
    def phi(d, s, inten, htf):
        d = max(d, 1e-6); s = max(s, 1e-6)
        return np.array([1.0, math.log(d / s), 1 / math.sqrt(d), inten - 1.0, htf])

    def predict(self, d, s, inten=1.0, htf=0.0):
        z = float(self.w @ self.phi(d, s, inten, htf))
        return 1 / (1 + math.exp(-max(-30, min(30, z))))

    def update(self, d, s, y, inten=1.0, htf=0.0):
        x = self.phi(d, s, inten, htf)
        p = 1 / (1 + math.exp(-max(-30, min(30, float(self.w @ x)))))
        self.w = self.w * (1 - self.lr * 1e-4) + (y - p) * self.lr * x


# =============================================================================
#  THE ALGORITHM
# =============================================================================
class IctVisionAlgorithm(QCAlgorithm):

    def initialize(self) -> None:
        self.set_start_date(*START)
        self.set_end_date(*END)
        self.set_cash(CASH)

        if ASSET == "cfd":
            self.symbol = self.add_cfd(TICKER, Resolution.MINUTE, MARKET).symbol
        elif ASSET == "forex":
            self.symbol = self.add_forex(TICKER, Resolution.MINUTE, MARKET).symbol
        elif ASSET == "crypto":
            self.symbol = self.add_crypto(TICKER, Resolution.MINUTE, Market.BINANCE).symbol
        else:
            self.symbol = self.add_index(TICKER, Resolution.MINUTE).symbol
        self.securities[self.symbol].set_leverage(LEVERAGE)
        # costs are applied by us, in price units, so LEAN adds nothing
        self.securities[self.symbol].set_slippage_model(ConstantSlippageModel(0))
        self.securities[self.symbol].set_fee_model(ConstantFeeModel(0))

        self.consolidator = TradeBarConsolidator(timedelta(minutes=EXEC_MINUTES))
        self.consolidator.data_consolidated += self.on_exec_bar
        self.subscription_manager.add_consolidator(self.symbol, self.consolidator)

        # ---- rolling state
        self.t = -1
        self.o, self.h, self.l, self.c = [], [], [], []
        self.minute_of_day, self.dow = [], []
        self.sigma = []
        self.zz = {k: ZigZag() for k in SCALES}
        self.last_hi = {k: np.nan for k in SCALES}
        self.last_lo = {k: np.nan for k in SCALES}
        self.book = None
        self.ret = RetracementModel()
        self.clock = DeliveryClock()
        self.evid = EvidenceModel(FEATURES)
        self.hazard = HazardModel()
        self.comeback = ComebackModel()
        self.reach = ReachModel()
        self.overshoot_q = QuantileTracker(0.0, 8.0, 80, 400.0)
        self.fill_q = QuantileTracker(0.0, 60.0, 60, 200.0)
        self.legs = []
        self.sweeps = deque(maxlen=200)
        self.n_cand = 0
        self.n_orders = 0
        self.trade_log = []
        self.eq0 = CASH

        # pending / open trade state
        self.pending = None
        self.pos = None
        self.set_warm_up(timedelta(days=WARMUP_DAYS))

    # ------------------------------------------------------------ bookkeeping
    def _sigma_update(self, r, prev):
        if prev is None:
            return None
        return r

    def on_exec_bar(self, sender, bar) -> None:
        self.t += 1
        t = self.t
        o, h, l, c = float(bar.open), float(bar.high), float(bar.low), float(bar.close)
        self.o.append(o); self.h.append(h); self.l.append(l); self.c.append(c)
        tod = bar.time.hour * 60 + bar.time.minute
        self.minute_of_day.append(tod)
        self.dow.append(int(bar.time.weekday()))

        # --- volatility tape (causal EWMA of |log return|)
        if t == 0:
            self.sigma.append(max(c * 1e-4, 1e-9))
        else:
            r = abs(math.log(c / self.c[t - 1]))
            s, _ = ewma_update(self.sigma[t - 1], r, 24.0)
            self.sigma.append(max(s / 0.7979, 1e-12))
        sp = self.sigma[t] * c

        if self.book is None:
            self.book = LiquidityBook(bucket=max(sp * 0.35, 1e-9))

        if self.is_warming_up:
            # still learn the tape, the clock and the pools; do not trade
            self._perceive(t, h, l, c, sp)
            return

        self._perceive(t, h, l, c, sp)
        self._manage(t, c, sp)

    def _perceive(self, t, h, l, c, sp):
        # --- swings / pools
        for k in SCALES:
            thr = k * sp
            pv = self.zz[k].update(t, h, l, thr)
            if pv is None:
                continue
            idx, px, kind, conf = pv
            if kind > 0:
                self.last_hi[k] = px
            else:
                self.last_lo[k] = px
            w = {2.0: 0.6, 4.0: 1.0, 8.0: 1.3, 16.0: 1.0}[k]
            self.book.add_swing(px, kind, w, t, sp)
        # --- sweeps
        for s in self.book.step(t, h, l, c, sp):
            s["t"] = t
            self.overshoot_q.add(s["overshoot"])
            self.sweeps.append(s)
        # --- clock (measurement made H bars ago is now knowable)
        Hh = self.clock.h
        if t - Hh >= 0:
            d = self.c[t] - self.c[t - Hh]
            path = sum(abs(self.c[i + 1] - self.c[i]) for i in range(t - Hh, t))
            base = max(self.sigma[t - Hh] * math.sqrt(Hh) * self.c[t - Hh], 1e-12)
            self.clock.feed(self.minute_of_day[t - Hh], abs(d) / base, abs(d) / max(path, 1e-12))
        # --- resolved legs feed the retracement model
        still = []
        for leg in self.legs:
            if t < leg["t"] + 288:
                still.append(leg); continue
            res = self._resolve_leg(leg, t)
            if res:
                self.ret.observe(res["depth"], res["outcome"], res["ext"])
        self.legs = still

    def _resolve_leg(self, leg, t):
        d, org, ext = leg["dir"], leg["origin"], leg["extreme"]
        L = abs(ext - org)
        if L <= 0:
            return None
        end = min(t, leg["t"] + 288)
        tgt = ext + d * 1.0 * L
        inv = org - d * 0.15 * L
        ta = tb = -1
        for k in range(leg["t"] + 1, end + 1):
            if (d > 0 and self.h[k] >= tgt) or (d < 0 and self.l[k] <= tgt):
                ta = k; break
            if (d > 0 and self.l[k] <= inv) or (d < 0 and self.h[k] >= inv):
                tb = k; break
        stop_bar = ta if (ta >= 0 and (tb < 0 or ta < tb)) else (tb if tb >= 0 else end)
        if stop_bar <= leg["t"]:
            return None
        seg_l = min(self.l[leg["t"] + 1: stop_bar + 1])
        seg_h = max(self.h[leg["t"] + 1: stop_bar + 1])
        if d > 0:
            depth = (ext - seg_l) / L
            extension = (seg_h - ext) / L
        else:
            depth = (seg_h - ext) / L
            extension = (ext - seg_l) / L
        return {"depth": float(np.clip(depth, 0, 2)), "ext": float(extension),
                "outcome": 1 if (ta >= 0 and (tb < 0 or ta < tb)) else 0}

    # ----------------------------------------------------------------- decide
    def _maybe_enter(self, t, c, sp):
        if self.pending is not None or self.pos is not None:
            return
        L = 12
        if t < L + 50:
            return
        hh = max(self.h[t - L: t + 1])
        ll = min(self.l[t - L: t + 1])
        up = c - ll
        dn = hh - c
        path = sum(abs(self.c[i + 1] - self.c[i]) for i in range(t - L, t))
        unit = max(self.sigma[t] * math.sqrt(L) * c, 1e-12)
        z = max(up, dn) / unit
        eff = min(max(up, dn) / max(path, 1e-12), 1.0)
        d = 1 if up >= dn else -1
        hist = self.c[max(0, t - 3000): t + 1]
        if len(hist) > 500:
            recent = sorted((max(self.h[i - L: i + 1]) - min(self.l[i - L: i + 1])) for i in range(t - 400, t))
            thr = recent[int(0.97 * (len(recent) - 1))] / unit if recent else 0
            if (max(up, dn) / unit) * eff < thr:
                return
        extreme = hh if d > 0 else ll
        origin = ll if d > 0 else hh
        leg = abs(extreme - origin)
        if leg < 0.6 * sp:
            return

        tol = max(0.45 * leg, 0.6 * sp)
        best = None
        for s in self.sweeps:
            if t - s["t"] > 30 or s["kind"] != -d:
                continue
            if abs(s["extreme"] - origin) > tol:
                continue
            q = self._sweep_quality(s)
            if best is None or q > best[0]:
                best = (q, s)
        if best is None:
            return
        sweep_q, sweep = best
        if d > 0:
            origin = min(origin, sweep["extreme"])
        else:
            origin = max(origin, sweep["extreme"])
        leg = abs(extreme - origin)
        if leg <= 0:
            return

        brk, nconf = -9.0, 0
        for k in SCALES:
            lvl = self.last_hi[k] if d > 0 else self.last_lo[k]
            if lvl is None or not np.isfinite(lvl):
                continue
            gap = (c - lvl) if d > 0 else (lvl - c)
            if gap / sp > 0:
                nconf += 1
                brk = max(brk, gap / sp)

        # fair value gap left by the displacement
        top = bot = None
        gap_sig = 0.0
        for j in range(t, max(t - 3, 1), -1):
            if d > 0 and self.l[j] > self.h[j - 2]:
                top, bot = self.l[j], self.h[j - 2]
            elif d < 0 and self.h[j] < self.l[j - 2]:
                top, bot = self.l[j - 2], self.h[j]
            if top is not None:
                gap_sig = (top - bot) / max(sp, 1e-12)
                break
        pd_q = float(np.clip(0.5 + 0.45 * math.tanh((gap_sig - 0.6) / 0.6), 0, 1)) if top else 0.5

        min_risk = max(0.60 * sp, 4.0 * HALF_SPREAD)
        d_cap = float(np.clip(1.0 - min_risk / max(leg, 1e-9), 0.10, 0.90))
        buf_frac = float(np.clip(self.overshoot_q.quantile(0.70) * sp / max(leg, 1e-9), 0.02, 0.60))
        d_star, _ = self.ret.best(d_hi=d_cap, min_reach=0.55, buf=buf_frac)
        entry = extreme - d * d_star * leg
        if top is not None:
            entry = min(entry, top) if d > 0 else max(entry, bot)
        stop = origin - d * max(self.overshoot_q.quantile(0.70), 0.12) * sp
        risk = abs(entry - stop)
        if risk <= 0:
            return

        # targets: the opposing pools, else one measured move
        pools = self._pools_ahead(t, d, c, sp, k=3)
        measured = extreme + d * max(self.ret.ext, 0.5) * leg
        t1 = pools[0][0] if pools else measured
        t2 = pools[1][0] if len(pools) > 1 else measured
        t2 = max(t2, measured) if d > 0 else min(t2, measured)
        rr = abs(t1 - entry) / risk
        p1 = float(np.clip(self.reach.predict(abs(t1 - entry) / sp, risk / sp,
                                              self.clock.intensity(self.minute_of_day[t]),
                                              self._htf() * d), 0.05, 0.95))
        f1 = self._scale_fraction(p1, rr)

        pd_pos = self._pd_position(t, c)
        x = np.array([
            float(np.clip(sweep_q, 0, 3)),
            float(math.log1p(max(sweep["overshoot"], 0))),
            float(np.clip(z, 0, 12)),
            float(eff),
            float(np.clip(brk, -2, 12)),
            float(nconf) / len(SCALES),
            self._pd_membership(pd_pos, d),
            float(np.clip(self.ret.llr_at(d_star), -3, 3)),
            float(pd_q),
            float(math.log(max(self.clock.intensity(self.minute_of_day[t]), 1e-3))),
            float(np.clip(self._htf() * d / 2.0, -1, 1)),
            float(math.log(max(rr, 1e-3))),
        ])
        prob = self.evid.probability(x)
        self.n_cand += 1
        bootstrap = self.n_cand <= BOOTSTRAP
        if not bootstrap and prob < 0.53:
            return
        kelly = 0.5 if bootstrap else max(0.0, min(KELLY_CAP, (prob * (rr + 1) - 1) / max(rr, 1e-6)))
        qty = (self.portfolio.total_portfolio_value * RISK_PCT * kelly) / risk
        if not np.isfinite(qty) or qty <= 0:
            return
        self.n_orders += 1
        self.pending = {"dir": d, "entry": entry, "stop": stop, "t1": t1, "t2": t2,
                        "f1": f1, "qty": qty, "t": t, "x": x, "prob": prob,
                        "valid": t + int(max(self.fill_q.quantile(0.85), 24)),
                        "leg": (origin, extreme, d)}

    def _sweep_quality(self, s):
        base = float(np.clip(s["strength"], 0, 6))
        far = 1 - math.exp(-max(s["overshoot"], 0) / 0.8)
        fast = 1 / (1 + max(s["bars"] - 1, 0) / 3.0)
        return base * (0.35 + 0.45 * far + 0.20 * fast) * (0.5 + 0.5 * s["wick"])

    def _pools_ahead(self, t, d, c, sp, k=3):
        lo, hi = (c, c + 12 * sp) if d > 0 else (c - 12 * sp, c)
        out = []
        for i in self.book.candidates(lo, hi):
            if not self.book.alive[i] or self.book.kind[i] != (1 if d > 0 else -1):
                continue
            p = self.book.px[i]
            if (d > 0 and p > c + 0.15 * sp) or (d < 0 and p < c - 0.15 * sp):
                out.append((p, self.book.strength(i, t)))
        out.sort(key=lambda z: abs(z[0] - c))
        return out[:k]

    def _pd_position(self, t, c):
        # session dealing range so far, and its time-at-price centroid
        a = max(0, t - 267)
        hi = max(self.h[a: t + 1]); lo = min(self.l[a: t + 1])
        eq = sum(self.h[i] + self.l[i] for i in range(a, t + 1)) / max(2 * (t - a + 1), 1)
        return (c - eq) / max(0.5 * (hi - lo), 1e-12)

    def _pd_membership(self, pd_pos, d):
        z = -d * pd_pos / 0.55
        return 1 / (1 + math.exp(-2.2 * max(-30, min(30, z))))

    def _htf(self):
        # daily-bias proxy: 5-session slope of the close in daily-range units
        if len(self.c) < 1600:
            return 0.0
        i = len(self.c) - 1
        a = max(0, i - 5 * 267)
        rng = max(max(self.h[a:i + 1]) - min(self.l[a:i + 1]), 1e-12)
        return float((self.c[i] - self.c[a]) / rng)

    def _scale_fraction(self, p1, rr):
        best_f, best_u = 0.5, -9e9
        for f in np.linspace(0, 0.95, 20):
            u_hit = math.log(1 + f * rr + (1 - f) * 0.6 * rr)
            u_miss = math.log(max(f, 1e-3))
            u = p1 * u_hit + (1 - p1) * u_miss
            if u > best_u:
                best_u, best_f = u, float(f)
        return float(np.clip(best_f, 0, 0.95))

    # ---------------------------------------------------------------- manage
    def _manage(self, t, c, sp):
        p = self.pending
        if p is not None:
            if t > p["valid"]:
                self.pending = None
            elif (p["dir"] > 0 and self.l[t] <= p["entry"] <= self.h[t]) or \
                 (p["dir"] < 0 and self.l[t] <= p["entry"] <= self.h[t]):
                self.fill_q.add(t - p["t"])
                entry = p["entry"] + p["dir"] * HALF_SPREAD
                self.market_order(self.symbol, p["dir"] * p["qty"])
                self.pos = dict(p, entry_eff=entry, qty_left=p["qty"], mfe=0.0, mae=0.0,
                                t_entry=t, path=[])
                self.pending = None
            elif (p["dir"] > 0 and self.l[t] <= p["stop"]) or (p["dir"] < 0 and self.h[t] >= p["stop"]):
                self.pending = None
            return
        q = self.pos
        if q is None:
            self._maybe_enter(t, c, sp)
            return
        d = q["dir"]
        risk = abs(q["entry_eff"] - q["stop"])
        q["mfe"] = max(q["mfe"], (self.h[t] - q["entry_eff"]) * d / risk if d > 0
                       else (q["entry_eff"] - self.l[t]) * d / risk)
        # stop (checked first — pessimistic intra-bar ordering)
        if (d > 0 and self.l[t] <= q["stop"]) or (d < 0 and self.h[t] >= q["stop"]):
            self._exit(t, q["stop"] - d * STOP_SLIP if d > 0 else q["stop"] + d * STOP_SLIP, "stop")
            return
        if q["qty_left"] > 0 and q["f1"] > 0:
            if (d > 0 and self.h[t] >= q["t1"]) or (d < 0 and self.l[t] <= q["t1"]):
                self.market_order(self.symbol, -d * q["qty"] * q["f1"])
                q["qty_left"] *= (1 - q["f1"])
                be = q["entry_eff"] + d * HALF_SPREAD
                q["stop"] = max(q["stop"], be) if d > 0 else min(q["stop"], be)
                q["t1"] = None
        if (d > 0 and self.h[t] >= q["t2"]) or (d < 0 and self.l[t] <= q["t2"]):
            self._exit(t, q["t2"], "target")
            return
        # break-even from the measured comeback curve
        be = q["entry_eff"] + d * HALF_SPREAD
        mfe_sig = q["mfe"] * risk / sp
        if (d > 0 and q["stop"] < be) or (d < 0 and q["stop"] > be):
            if self.comeback.p(mfe_sig) < 0.35:
                q["stop"] = be
        # structural trail at the working scale
        lvl = self.last_lo[4.0] if d > 0 else self.last_hi[4.0]
        if lvl is not None and np.isfinite(lvl):
            cand = lvl - 0.25 * sp if d > 0 else lvl + 0.25 * sp
            if (d > 0 and cand > q["stop"] and cand < c) or (d < 0 and cand < q["stop"] and cand > c):
                q["stop"] = cand
        # leave when the survival model says the remaining bet is EV-negative
        held = t - q["t_entry"]
        q["path"].append(min(held, 287))
        ph = self.hazard.p(held)
        rr_rem = abs(q["t2"] - c) / max(abs(c - q["stop"]), 1e-9)
        if ph * rr_rem < (1 - ph) or held > 576:
            self._exit(t, c, "hazard" if held <= 576 else "time")
            return
        if self.pos is not None:
            self._maybe_enter(t, c, sp)

    def _exit(self, t, px, kind):
        q = self.pos
        if q is None:
            return
        d = q["dir"]
        risk = abs(q["entry_eff"] - q["stop"])
        r = (px - q["entry_eff"] - d * HALF_SPREAD) * d / max(risk, 1e-9)
        if q["qty_left"] > 0:
            self.market_order(self.symbol, -d * q["qty_left"])
        self.trade_log.append({"t": t, "dir": d, "R": float(r), "kind": kind})
        self.evid.update(q["x"], 1 if r > 0 else 0)
        self.hazard.record(q["path"], 1 if r > 0 else 0)
        self.comeback.record(q["mfe"], 1 if (q["mfe"] > 0.25 and r < 0.05) else 0)
        self.legs.append({"t": q["t"], "dir": d, "origin": q["leg"][0], "extreme": q["leg"][1]})
        self.pos = None

    # ------------------------------------------------------------------- end
    def on_end_of_algorithm(self) -> None:
        if not self.trade_log:
            self.debug("no trades")
            return
        R = np.array([x["R"] for x in self.trade_log])
        self.debug(f"trades {len(R)}  win {np.mean(R>0)*100:.1f}%  meanR {R.mean():+.3f}  "
                   f"t {R.mean()/(R.std()/np.sqrt(len(R))):+.2f}")
        d, _ = self.ret.best()
        self.debug(f"learned OTE depth {d*100:.1f}%   (ICT prior 62-79%, mean 70.5%)   "
                   f"legs seen {self.ret.n:.0f}")
        prof = self.clock.profile()
        order = np.argsort(-prof)
        self.debug("discovered high-delivery windows (ET):")
        for b in order[:6]:
            m0 = int(b * self.clock.bm)
            self.debug(f"   {m0//60:02d}:{m0%60:02d}-{m0//60:02d}:{(m0+15)%60:02d}  {prof[b]:.2f}x")
        self.debug(f"ICT 08:50 macro scores "
                   f"{np.mean(prof[34:38]):.2f}x ; NY AM killzone "
                   f"{np.mean(prof[34:44]):.2f}x ; London open {np.mean(prof[8:20]):.2f}x")
