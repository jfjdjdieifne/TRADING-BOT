"""The engine: walks the chart once, bar by bar, and trades what it understands.

Order of operations at every bar (this ordering is what makes the whole thing
causal -- each step only ever touches bars <= t):

    1. fills          : play the 1-minute bars that make up this bar through
                        any live order / open position
    2. publish        : swing points confirmed at t enter the liquidity book;
                        session levels that become knowable at t are published
    3. clock          : the delivery measurement taken at t-H is now knowable
    4. liquidity      : update pool state; any pool whose sweep just confirmed
                        emits a sweep event
    5. resolve        : displacement legs that have reached their resolution
                        horizon are resolved and fed to the retracement model
    6. manage         : break-even, structural trail, hazard-based abandonment
    7. decide         : is there a displacement at t that follows a sweep and
                        shifts structure?  If so, score it and maybe place a
                        limit order at the EV-optimal retracement depth

Nothing looks forward.  The engine is also the only place that knows about
time: every other module is a pure function or an online estimator.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from ..core import clock as _clock
from ..core.dealing import RetracementModel, leg_resolution, pd_membership, session_range_state
from ..core.imbalance import candle_quality, detect_fvg, find_order_block, gap_size_quantile
from ..core.liquidity import (
    LiquidityBook,
    add_session_pools,
    session_levels,
)
from ..core.scale import sigma_field
from ..core.swings import cisd_levels, pivot_state, zigzag
from ..data.loader import minutes_of_day, trading_day
from .models import ComebackModel, EvidenceModel, HazardModel, QuantileTracker, ReachModel

FEATURES = [
    "sweep_quality",     # how convincing was the liquidity raid
    "sweep_overshoot",   # how far beyond the pool, in sigmas
    "displacement_z",    # leg size in diffusion units
    "displacement_eff",  # |net| / path  (clean delivery vs chop)
    "struct_break_sig",  # how far past the broken swing, in sigmas
    "struct_scales",     # how many swing scales confirm
    "pd_membership",     # right side of the *learned* equilibrium?
    "ote_llr",           # evidence carried by the retracement depth
    "pd_array_q",        # size x freshness of the gap/order block
    "clock_intensity",   # learned time-of-day delivery
    "htf_agreement",     # daily-bias agreement
    "rr_geometry",       # reward:risk at the chosen entry
]

SCALES = (2.0, 4.0, 8.0, 16.0)


@dataclass
class Cfg:
    bar_minutes: int = 5
    disp_lookback: int = 12
    disp_quantile: float = 0.97      # candidates are the top X% of displacement
    disp_local_max: int = 3          # ...and a local maximum within +-N bars
    sweep_lookback: int = 30
    leg_horizon: int = 288
    leg_ext_target: float = 1.0      # 'delivered' = one measured move past the leg
    leg_inval_buffer: float = 0.15   # 'failed' = back through the origin by this much
    entry_min_bars: int = 1
    entry_valid_bars: int = 24
    risk_pct: float = 0.007
    max_risk_pct: float = 0.015
    min_prob: float = 0.53
    bootstrap_trades: int = 80      # exploration sample that seeds the models
    kelly_cap: float = 0.35
    half_spread: float = 1.0
    stop_slip: float = 0.5
    commission_bp: float = 0.0
    be_comeback_max: float = 0.35
    trail_scale: float = 4.0
    max_hold_bars: int = 576
    min_risk_sigma: float = 0.60     # a stop tighter than this is inside the noise
    min_reach: float = 0.55          # do not quote a level price never trades back to
    warmup_bars: int = 4000
    min_confirm_pools: float = 0.25


@dataclass
class Trade:
    t_signal: int
    t_entry: int = -1
    t_exit: int = -1
    direction: int = 0
    entry: float = np.nan
    stop0: float = np.nan
    t1: float = np.nan
    t2: float = np.nan
    f1: float = 0.5
    exit_px: float = np.nan
    entry_eff: float = np.nan
    risk_cash: float = np.nan
    r_mult: float = np.nan
    pnl_r: float = np.nan
    pnl_cash: float = np.nan
    size: float = 0.0
    prob: float = np.nan
    reason: str = ""
    narrative: str = ""
    features: np.ndarray | None = None
    llr: np.ndarray | None = None
    mfe_r: float = 0.0
    mae_r: float = 0.0
    bars_held: int = 0
    exit_kind: str = ""
    bootstrap: bool = False
    partials: list = field(default_factory=list)


class ChartReader:
    def __init__(self, bars5, bars1, cfg: Cfg | None = None, verbose: bool = False):
        self.b = bars5
        self.m1 = bars1
        self.cfg = cfg or Cfg()
        self.verbose = verbose
        self._prep()

    # ------------------------------------------------------------------ prep
    def _prep(self):
        b = self.b
        n = b.n
        self.n = n
        self.sig = sigma_field(b.c, 24.0, 288.0)
        self.sigma = np.maximum(self.sig["fast"], 1e-9)
        self.vol_pct = np.clip(self.sig["ratio"], 0, 5) / 2.0

        self.pivots = {}
        self.pstate = {}
        for k in SCALES:
            thr = k * self.sigma * b.c
            pv = zigzag(b.h, b.l, thr)
            self.pivots[k] = pv
            self.pstate[k] = pivot_state(pv, n)

        self.fvg = detect_fvg(b, self.sigma)
        self.fvg_pos = np.searchsorted(self.fvg.t, np.arange(n), side="right")

        self.day = trading_day(b.idx)
        self.tod = minutes_of_day(b.idx)
        self.dow = np.array([d.weekday() for d in b.idx.date], dtype=np.int64)
        self.levels = session_levels(b, self.day)
        self.dr = session_range_state(b, self.day)
        self.cisd = cisd_levels(b)

        # HTF bias: the 5-day slope of the daily close, in daily sigmas.
        self.htf = self._htf_bias()

        # 1m index mapping for 5m bars
        idx1 = self.m1.idx
        self.m1_a = np.searchsorted(idx1, b.idx, side="left")
        nxt = np.searchsorted(idx1, b.idx + np.timedelta64(self.cfg.bar_minutes, "m"), side="left")
        self.m1_b = np.maximum(nxt, self.m1_a + 1)

        # displacement score, vectorised, with a CAUSAL trailing quantile
        self.disp = self._displacement()
        import pandas as pd

        self.disp_thr = pd.Series(self.disp["score"]).rolling(3000, min_periods=500).quantile(
            self.cfg.disp_quantile
        ).to_numpy()

        # pooled pivot records in confirmation order
        recs = []
        for k in SCALES:
            pv = self.pivots[k]
            for i in range(len(pv)):
                recs.append((int(pv.conf[i]), float(pv.px[i]), int(pv.kind[i]), float(k)))
        recs.sort(key=lambda r: r[0])
        self._recs = recs
        self._rp = 0

        bs = float(np.median(self.sigma[:n] * b.c[:n]) * 0.35)
        self.book = LiquidityBook(bucket=bs)
        self.clock = _clock.DeliveryClock(halflife_days=120.0, horizon=12)
        self.ret_model = RetracementModel()
        self.evid = EvidenceModel(FEATURES, n_bins=5, halflife=250.0, shrink_n0=60.0)
        self.hazard = HazardModel()
        self.reach = ReachModel()
        self.comeback = ComebackModel()
        self.fill_time = QuantileTracker(0.0, 60.0, 60, halflife=200.0)
        self.sweep_overshoot = QuantileTracker(0.0, 8.0, 80, halflife=400.0)
        self.leg_ext = QuantileTracker(-0.5, 5.0, 60, halflife=300.0)

        self.trades: list[Trade] = []
        self.pending: Trade | None = None
        self.pos: Trade | None = None
        self.open_legs: list[dict] = []
        self.recent_sweeps: list = []
        self.equity = 100000.0
        self.equity_curve = []
        self.diagnostics = {"rejected": 0, "no_sweep": 0, "low_prob": 0}
        self.n_taken = 0
        self.n_cand = 0
        self.setup_log: list[dict] = []

    def _htf_bias(self) -> np.ndarray:
        """Daily-bias proxy: 5-day slope of the daily close in daily sigmas,
        published one trading day late so it is knowable at the bar."""
        b = self.b
        n = b.n
        day = self.day
        uniq = {}
        for d in day:
            if d not in uniq:
                uniq[d] = len(uniq)
        nd = len(uniq)
        didx = np.array([uniq[d] for d in day])
        close = np.full(nd, np.nan)
        hi = np.full(nd, np.nan)
        lo = np.full(nd, np.nan)
        for i in range(n):
            d = didx[i]
            close[d] = b.c[i]
            hi[d] = b.h[i] if not np.isfinite(hi[d]) else max(hi[d], b.h[i])
            lo[d] = b.l[i] if not np.isfinite(lo[d]) else min(lo[d], b.l[i])
        tr = np.maximum(hi - lo, 1e-9)
        sig_d = np.full(nd, np.nan)
        for d in range(1, nd):
            sig_d[d] = np.nanmedian(tr[max(0, d - 10) : d + 1]) if d >= 3 else tr[d]
        slope = np.full(nd, np.nan)
        for d in range(5, nd):
            if not np.isfinite(sig_d[d]) or sig_d[d] <= 0:
                continue
            slope[d] = (close[d] - close[d - 5]) / sig_d[d]
        out = np.full(n, np.nan)
        for i in range(n):
            d = int(didx[i])
            if d >= 1 and np.isfinite(slope[d - 1]):
                out[i] = slope[d - 1]
        return np.nan_to_num(out, nan=0.0)

    def _displacement(self) -> dict:
        b = self.b
        n = b.n
        L = self.cfg.disp_lookback
        h = np.lib.stride_tricks.sliding_window_view(b.h, L + 1)
        lo = np.lib.stride_tricks.sliding_window_view(b.l, L + 1)
        cc = np.lib.stride_tricks.sliding_window_view(b.c, L + 1)
        up_move = b.c[L:] - lo.min(axis=1)
        dn_move = h.max(axis=1) - b.c[L:]
        path = np.abs(np.diff(cc, axis=1)).sum(axis=1)
        path = np.maximum(path, 1e-12)
        unit = np.maximum(self.sigma[L:] * np.sqrt(L) * b.c[L:], 1e-12)
        up_z = up_move / unit
        dn_z = dn_move / unit
        dirn = np.where(up_move >= dn_move, 1, -1)
        move = np.maximum(up_move, dn_move)
        z = np.maximum(up_z, dn_z)
        eff = np.clip(move / path, 0.0, 1.0)
        score = np.zeros(n)
        score[L:] = z * eff
        return {"score": score, "z": np.r_[np.zeros(L), z], "eff": np.r_[np.zeros(L), eff],
                "dir": np.r_[np.zeros(L, int), dirn], "move": np.r_[np.zeros(L), move]}

    # ------------------------------------------------------------- utilities
    def _t(self, i: int) -> str:
        return str(self.b.idx[i])[:16]

    def _sig_px(self, i: int) -> float:
        return float(self.sigma[i] * self.b.c[i])

    def _pools_ahead(self, t: int, direction: int, price: float, k: int = 3):
        """Opposing pools the trade would be *delivered to*."""
        lo, hi = price, price + 12.0 * self._sig_px(t) * (1 if direction > 0 else 1)
        if direction < 0:
            lo, hi = price - 12.0 * self._sig_px(t), price
        ids, px, st = self.book.live_levels(t, lo, hi)
        if len(ids) == 0:
            return []
        want = 1 if direction > 0 else -1
        m = (self.book.kind[ids] == want)
        if direction > 0:
            m &= px > price + 0.15 * self._sig_px(t)
        else:
            m &= px < price - 0.15 * self._sig_px(t)
        ids, px, st = ids[m], px[m], st[m]
        if len(ids) == 0:
            return []
        order = np.argsort(np.abs(px - price))[:k]
        return [(float(px[i]), float(st[i])) for i in order]

    # --------------------------------------------------------- order / fills
    def _scan_pending(self, t: int):
        """Play this bar's 1m bars against a pending limit order."""
        tr = self.pending
        if tr is None:
            return
        a, bnd = int(self.m1_a[t]), int(self.m1_b[t])
        if tr.t_signal >= t:
            return
        if t - tr.t_signal > self.cfg.entry_valid_bars:
            self.pending = None
            self.diagnostics["rejected"] += 1
            return
        o = self.m1.o[a:bnd]
        hh = self.m1.h[a:bnd]
        ll = self.m1.l[a:bnd]
        L = tr.entry
        S = tr.stop0
        for j in range(len(o)):
            # invalidate: price ran through the stop level before we were filled
            if tr.direction > 0 and ll[j] <= S:
                self.pending = None
                return
            if tr.direction < 0 and hh[j] >= S:
                self.pending = None
                return
            if ll[j] <= L <= hh[j]:
                # if the minute opened through our limit we get the better price
                fill = min(o[j], L) if tr.direction > 0 else max(o[j], L)
                tr.t_entry = t
                tr.entry = float(fill)
                tr.entry_eff = float(fill + tr.direction * self.cfg.half_spread)
                tr.risk_cash = float(tr.size * abs(tr.entry_eff - tr.stop0))
                tr.exit_kind = "open"
                self.pos = tr
                self.pending = None
                self.fill_time.add(float(t - tr.t_signal))
                return

    def _scan_position(self, t: int):
        tr = self.pos
        if tr is None:
            return
        a, bnd = int(self.m1_a[t]), int(self.m1_b[t])
        o = self.m1.o[a:bnd]
        hh = self.m1.h[a:bnd]
        ll = self.m1.l[a:bnd]
        d = tr.direction
        for j in range(len(o)):
            # ---- stop first (pessimistic intra-bar ordering)
            if d > 0 and ll[j] <= tr.stop0:
                px = min(o[j], tr.stop0) - self.cfg.stop_slip
                self._close(t, px, "stop")
                return
            if d < 0 and hh[j] >= tr.stop0:
                px = max(o[j], tr.stop0) + self.cfg.stop_slip
                self._close(t, px, "stop")
                return
            # ---- targets
            if not np.isnan(tr.t1) and tr.f1 > 0:
                hit1 = (hh[j] >= tr.t1) if d > 0 else (ll[j] <= tr.t1)
                if hit1:
                    px = tr.t1
                    self._partial(t, px, tr.f1)
                    tr.t1 = np.nan
            if not np.isnan(tr.t2):
                hit2 = (hh[j] >= tr.t2) if d > 0 else (ll[j] <= tr.t2)
                if hit2:
                    self._close(t, tr.t2, "target2")
                    return
            # ---- running extremes in R
            r = self._r_of(tr, hh[j] if d > 0 else ll[j])
            tr.mfe_r = max(tr.mfe_r, r)
            tr.mae_r = min(tr.mae_r, self._r_of(tr, ll[j] if d > 0 else hh[j]))

    def _r_of(self, tr: Trade, px: float) -> float:
        risk = abs(tr.entry - tr.stop0)
        if risk <= 0:
            return 0.0
        return float((px - tr.entry) * tr.direction / risk)

    def _partial(self, t: int, px: float, frac: float):
        tr = self.pos
        if tr is None:
            return
        r = self._r_of(tr, px)
        cost = self.cfg.half_spread
        cash = frac * tr.size * ((px - tr.entry_eff - cost) * tr.direction)
        self.equity += cash
        tr.partials.append((t, float(px), float(frac), float(r), float(cash)))
        tr.size *= (1.0 - frac)
        if tr.size <= 1e-12:
            self._close(t, px, "target1", cash_already=True)
        else:
            # first scale-out locks the trade: stop goes to break-even + cost
            be = tr.entry + tr.direction * self.cfg.half_spread
            if tr.direction > 0:
                tr.stop0 = max(tr.stop0, be)
            else:
                tr.stop0 = min(tr.stop0, be)

    def _close(self, t: int, px: float, kind: str, cash_already: bool = False):
        tr = self.pos
        if tr is None:
            return
        cost = self.cfg.half_spread
        cash = 0.0 if cash_already else tr.size * ((px - tr.entry_eff - cost) * tr.direction)
        self.equity += cash
        tot = cash + sum(p[4] for p in tr.partials)
        tr.t_exit = t
        tr.exit_px = px
        tr.exit_kind = kind
        tr.pnl_cash = float(tot)
        tr.r_mult = float(tot / max(tr.risk_cash, 1e-9))
        tr.bars_held = int(t - tr.t_signal)
        self.pos = None
        self.trades.append(tr)
        y = 1 if tot > 0 else 0
        if tr.features is not None:
            self.evid.update(tr.features, y)
        self.hazard.record(list(range(0, min(tr.bars_held, self.hazard.mb))), y)
        self.comeback.record(tr.mfe_r, 1 if (tr.mfe_r > 0.25 and tr.r_mult < 0.05) else 0)

    # --------------------------------------------------------------- decide
    def _maybe_enter(self, t: int):
        if self.pos is not None or self.pending is not None:
            return
        cfg = self.cfg
        d = self.disp
        if d["score"][t] < (self.disp_thr[t] if np.isfinite(self.disp_thr[t]) else 1e9):
            return
        # CAUSAL local maximum: the window looks BACKWARD only.  Using bars
        # after t here is the single most seductive look-ahead bug in this
        # whole design -- it manufactures a spectacular fake edge (see
        # scripts/probe_lookahead.py).
        w = self.cfg.disp_local_max
        a = max(0, t - w)
        if w and d["score"][t] < d["score"][a:t].max() - 1e-12:
            return                      # only the peak of each displacement burst
        direction = int(d["dir"][t])
        if direction == 0:
            return
        L = cfg.disp_lookback
        seg_h = self.b.h[max(0, t - L) : t + 1]
        seg_l = self.b.l[max(0, t - L) : t + 1]
        extreme = float(seg_h.max()) if direction > 0 else float(seg_l.min())
        origin = float(seg_l.min()) if direction > 0 else float(seg_h.max())
        leg = abs(extreme - origin)
        sp = self._sig_px(t)
        if leg < 0.6 * sp:
            return

        # --- 1. was there a liquidity sweep on the OTHER side just before this?
        # The raid must actually BE the origin of the leg we are about to
        # trade, not some unrelated pool that happened to be run over in the
        # same hour.  ICT's story is "liquidity raid THERE, delivery from
        # THERE" -- if the raid is nowhere near the leg's origin it is a
        # different story and we are not in it.
        tol = max(0.45 * leg, 0.6 * sp)
        best = None
        for s in self.recent_sweeps:
            if t - s.t > cfg.sweep_lookback:
                continue
            if s.kind != -direction:
                continue
            if abs(s.extreme - origin) > tol:
                continue
            q = self._sweep_quality(s, t)
            if best is None or q > best[0]:
                best = (q, s)
        if best is None:
            self.diagnostics["no_sweep"] += 1
            return
        sweep_q, sweep = best
        if direction > 0:
            origin = min(origin, float(sweep.extreme))
        else:
            origin = max(origin, float(sweep.extreme))
        leg = abs(extreme - origin)
        if leg <= 0:
            return

        # --- 2. structure: did we close past the opposite swing at any scale?
        brk_sig = -9.0
        n_conf = 0
        for k in SCALES:
            st = self.pstate[k]
            lvl = st["last_hi"][t - 1] if direction > 0 else st["last_lo"][t - 1]
            if not np.isfinite(lvl):
                continue
            gap = (self.b.c[t] - lvl) if direction > 0 else (lvl - self.b.c[t])
            z = gap / sp
            if z > 0:
                n_conf += 1
                brk_sig = max(brk_sig, z)
        if brk_sig < -8:
            return

        # --- 3. the PD array this displacement left behind
        fvg_i = self._entry_fvg(t, direction)
        pd_q, fresh, fvg_ce = 0.5, 0.0, np.nan
        if fvg_i is not None:
            from ..core.imbalance import fvg_lifecycle

            # `upto=t`: how much of the gap has been filled AS OF NOW.  Scanning
            # past t would tell us whether the gap survives, which is exactly
            # the information we are trying to predict.
            touch_t, fill_t, frac = fvg_lifecycle(self.b, self.fvg, fvg_i, upto=t)
            pd_q = gap_size_quantile(self.fvg, fvg_i)
            fresh = 1.0 - frac
            fvg_ce = float(self.fvg.ce[fvg_i])

        # --- 4. where to enter: EV-optimal retracement depth.
        # The depth is capped so the stop stays outside the noise floor: a stop
        # you can set 0.05 sigma away is not a stop, it is a donation.  The
        # floor is cost-based (a multiple of the spread) and volatility-based.
        min_risk = max(self.cfg.min_risk_sigma * sp, 4.0 * self.cfg.half_spread)
        d_cap = float(np.clip(1.0 - min_risk / max(leg, 1e-9), 0.10, 0.90))
        # The stop buffer is a real fraction of the leg, and R(d) depends on it.
        # Feed the ACTUAL fraction (learned overshoot quantile / this leg) into
        # the EV calculation instead of a nominal constant.
        buf_frac = float(np.clip(self.sweep_overshoot.quantile(0.70) * sp / max(leg, 1e-9),
                                 0.02, 0.60))
        d_star, _ = self.ret_model.best_depth(d_hi=d_cap, min_reach=self.cfg.min_reach,
                                              buffer_frac=buf_frac)
        entry_px = extreme - direction * d_star * leg
        if fvg_i is not None and np.isfinite(fvg_ce):
            # never pay worse than the near edge of the gap we are trading
            if direction > 0:
                entry_px = min(entry_px, float(self.fvg.top[fvg_i]))
            else:
                entry_px = max(entry_px, float(self.fvg.bot[fvg_i]))
        if direction > 0 and entry_px <= origin:
            return
        if direction < 0 and entry_px >= origin:
            return

        # --- 5. stop: beyond the sweep wick by a LEARNED buffer
        buf_sig = self.sweep_overshoot.quantile(0.70)
        buf = max(buf_sig, 0.12) * sp
        stop = (origin - buf) if direction > 0 else (origin + buf)
        risk = abs(entry_px - stop)
        if risk <= 0:
            return

        # --- 6. targets: the pools this move should be delivered to
        pools = self._pools_ahead(t, direction, float(self.b.c[t]))
        ext = max(self.ret_model.ext, 0.5)
        measured = extreme + direction * ext * leg
        if pools:
            t1 = pools[0][0]
            t2 = pools[1][0] if len(pools) > 1 else measured
        else:
            t1, t2 = measured, measured
        if direction > 0:
            t2 = max(t2, measured)
        else:
            t2 = min(t2, measured)
        d1_sig = abs(t1 - entry_px) / sp
        p1 = self.reach.predict(d1_sig, risk / sp, self.clock.intensity(int(self.tod[t])), np.sign(self.htf[t]) * direction)
        p1 = float(np.clip(p1, 0.05, 0.95))
        f1 = self._scale_fraction(p1, self._r_of_px(entry_px, t1, stop, direction))

        # --- 7. features -> evidence -> probability
        pd_pos = float(self.dr["pd"][t])
        llr_at = float(np.interp(d_star, self.ret_model.centers, self.ret_model.llr()))
        inten = self.clock.intensity(int(self.tod[t]), int(self.dow[t]))
        htf = float(np.clip(self.htf[t] * direction / 2.0, -1, 1))
        rr = self._r_of_px(entry_px, t1, stop, direction)
        x = np.array([
            float(np.clip(sweep_q, 0, 3)),
            float(np.log1p(max(sweep.overshoot_sig, 0.0))),
            float(np.clip(d["z"][t], 0, 12)),
            float(np.clip(d["eff"][t], 0, 1)),
            float(np.clip(brk_sig, -2, 12)),
            float(n_conf) / float(len(SCALES)),
            float(pd_membership(pd_pos, direction)),
            float(np.clip(llr_at, -3, 3)),
            float(np.clip(pd_q * (0.4 + 0.6 * fresh), 0, 1)),
            float(np.log(max(inten, 1e-3))),
            htf,
            float(np.log(max(rr, 1e-3))),
        ])
        prob = self.evid.probability(x)
        # ---- cold start: the first BOOTSTRAP_TRADES setups are taken as an
        # exploration sample so the evidence model has something to learn from.
        # They are flagged and reported separately, never mixed into the
        # headline figures.
        self.n_cand += 1
        bootstrap = self.n_cand <= cfg.bootstrap_trades
        if (not bootstrap) and prob < cfg.min_prob:
            self.diagnostics["low_prob"] += 1
            return

        # --- 8. size it
        frac = 0.5 if bootstrap else self._kelly(prob, rr)
        risk_cash = self.equity * cfg.risk_pct * frac
        size = risk_cash / risk
        tr = Trade(
            t_signal=t, direction=direction, entry=float(entry_px), stop0=float(stop),
            t1=float(t1), t2=float(t2), f1=float(f1), size=float(size), prob=float(prob),
            features=x, llr=self.evid.score(x)[1], bootstrap=bool(bootstrap),
        )
        self.n_taken += 1
        if len(self.setup_log) < 4000:
            self.setup_log.append({
                "t": t, "time": self._t(t), "dir": direction, "close": float(self.b.c[t]),
                "origin": float(origin), "extreme": float(extreme), "leg": float(leg),
                "leg_sig": float(leg / sp), "sweep_t": int(sweep.t), "sweep_level": float(sweep.level),
                "sweep_extreme": float(sweep.extreme), "sweep_kind": int(sweep.kind),
                "sweep_overshoot": float(sweep.overshoot_sig), "sweep_strength": float(sweep.strength),
                "brk_sig": float(brk_sig), "n_conf": int(n_conf), "d_star": float(d_star),
                "entry": float(entry_px), "stop": float(stop), "t1": float(t1), "t2": float(t2),
                "n_pools": len(pools), "pool0": float(pools[0][0]) if pools else np.nan,
                "rr": float(rr), "prob": float(prob), "bootstrap": bool(bootstrap),
                "disp_z": float(d["z"][t]), "eff": float(d["eff"][t]),
            })
        tr.narrative = self._narrate(t, direction, sweep, sweep_q, d, brk_sig, n_conf,
                                     fvg_i, pd_q, fresh, d_star, entry_px, stop, t1, t2,
                                     prob, size, inten, htf, rr, pools, x)
        self.pending = tr

        # --- 9. every qualifying displacement (traded or not) is scored later,
        # so the retracement model learns from ALL legs, not just the ones we
        # happened to take.  This is what lets the OTE level move off the prior.
        self.open_legs.append({"t": t, "dir": direction, "origin": origin,
                               "extreme": extreme, "horizon": cfg.leg_horizon})

    def _r_of_px(self, entry, target, stop, direction) -> float:
        risk = abs(entry - stop)
        if risk <= 0:
            return 0.0
        return float(abs(target - entry) / risk)

    def _sweep_quality(self, s, t: int) -> float:
        """Continuous quality of a liquidity raid.

        Three things make a raid convincing, all measured, none thresholded:
        how far past the pool price went (in sigmas), how quickly it rejected,
        and how much of the piercing bar was wick rather than body.
        """
        base = float(np.clip(s.strength, 0.0, 6.0))
        far = 1.0 - np.exp(-max(s.overshoot_sig, 0.0) / 0.8)
        fast = 1.0 / (1.0 + max(s.bars - 1, 0) / 3.0)
        return float(base * (0.35 + 0.45 * far + 0.20 * fast) * (0.5 + 0.5 * s.wick_ratio))

    def _entry_fvg(self, t: int, direction: int):
        """The gap left by THIS displacement: created in the last 3 bars, same
        direction, largest relative to the market's own volatility."""
        j = int(np.searchsorted(self.fvg.t, t, side="right")) - 1
        best = None
        while j >= 0 and self.fvg.t[j] >= t - 2:
            if self.fvg.direction[j] == direction:
                sc = float(self.fvg.size_sig[j])
                if best is None or sc > best[1]:
                    best = (j, sc)
            j -= 1
        return best[0] if best else None

    def _scale_fraction(self, p1: float, rr: float) -> float:
        """How much to take at T1: coarse expected-log-wealth maximisation.

        Wealth after T1 = 1 + f*rr (the scaled-out part) and the remainder runs
        on; if the stop is hit instead we lose the un-scaled part only.
        """
        best_f, best_u = 0.5, -9e9
        for f in np.linspace(0.0, 0.95, 20):
            u_hit = np.log(1.0 + f * rr + (1 - f) * 0.6 * rr)
            u_miss = np.log(max(f, 1e-3))
            u = p1 * u_hit + (1 - p1) * u_miss
            if u > best_u:
                best_u, best_f = u, float(f)
        return float(np.clip(best_f, 0.0, 0.95))

    def _kelly(self, p: float, rr: float) -> float:
        b = max(rr, 1e-6)
        f = (p * (b + 1) - 1) / b
        return float(np.clip(f, 0.0, self.cfg.kelly_cap))

    # -------------------------------------------------------------- manage
    def _manage(self, t: int):
        tr = self.pos
        if tr is None:
            return
        sp = self._sig_px(t)
        d = tr.direction
        # break-even once the measured comeback risk is low enough
        mfe_sig = tr.mfe_r * abs(tr.entry - tr.stop0) / sp
        be = tr.entry + d * self.cfg.half_spread
        if d > 0 and tr.stop0 < be and self.comeback.p(mfe_sig) < self.cfg.be_comeback_max:
            tr.stop0 = be
        if d < 0 and tr.stop0 > be and self.comeback.p(mfe_sig) < self.cfg.be_comeback_max:
            tr.stop0 = be
        # structural trail: the last protected swing of the working scale
        st = self.pstate[self.cfg.trail_scale]
        lvl = st["last_lo"][t] if d > 0 else st["last_hi"][t]
        if np.isfinite(lvl):
            cand = lvl - 0.25 * sp if d > 0 else lvl + 0.25 * sp
            if d > 0 and cand > tr.stop0 and cand < self.b.c[t]:
                tr.stop0 = cand
            if d < 0 and cand < tr.stop0 and cand > self.b.c[t]:
                tr.stop0 = cand
        # hazard: leave when the remaining bet has gone EV-negative
        ph = self.hazard.p(t - tr.t_entry)
        rr_rem = abs(tr.t2 - self.b.c[t]) / max(abs(self.b.c[t] - tr.stop0), 1e-9)
        if ph * rr_rem < (1 - ph):
            self._close(t, float(self.b.c[t]), "hazard")
            return
        if t - tr.t_entry > self.cfg.max_hold_bars:
            self._close(t, float(self.b.c[t]), "time")

    # ---------------------------------------------------------------- loop
    def run(self, t_start: int | None = None, t_end: int | None = None):
        cfg = self.cfg
        t0 = t_start if t_start is not None else cfg.warmup_bars
        t1 = t_end if t_end is not None else self.n
        H = self.clock.horizon
        import pandas as pd

        for t in range(t0, t1):
            # 1. fills from the 1m bars of this bar
            self._scan_pending(t)
            self._scan_position(t)
            if self.pos is not None:
                self.pos.bars_held = t - self.pos.t_entry
            # 2. publish newly confirmed swings into the liquidity book
            while self._rp < len(self._recs) and self._recs[self._rp][0] <= t:
                _, px, kind, k = self._recs[self._rp]
                self._pool_add(px, kind, float(k), t)
                self._rp += 1
            self._publish_session(t)
            # 3. clock: the measurement taken H bars ago is now knowable
            if t - H >= 0:
                c = self.b.c
                d = c[t] - c[t - H]
                path = float(np.abs(np.diff(c[t - H : t + 1])).sum())
                base = max(self.sigma[t - H] * np.sqrt(H) * c[t - H], 1e-12)
                b_ = self.clock.bucket_of(int(self.tod[t - H]))
                w = int(self.dow[t - H])
                a = 1 - np.exp(-np.log(2) / self.clock.hl)
                self.clock.deliv[b_] += a * (abs(d) / base - self.clock.deliv[b_])
                self.clock.effic[b_] += a * (abs(d) / max(path, 1e-12) - self.clock.effic[b_])
                self.clock.n[b_] += 1.0
                self.clock.dow_deliv[w, b_] += a * (abs(d) / base - self.clock.dow_deliv[w, b_])
            # 4. liquidity book update
            self.recent_sweeps.extend(self._book_step(t))
            if len(self.recent_sweeps) > 400:
                self.recent_sweeps = self.recent_sweeps[-200:]
            self.recent_sweeps = [s for s in self.recent_sweeps if t - s.t <= cfg.sweep_lookback + 5]
            # 5. resolve matured legs
            self._resolve_legs(t)
            # 6-7. manage, then decide
            self._manage(t)
            self._maybe_enter(t)
            self.equity_curve.append(self.equity)
        # close anything still open
        if self.pos is not None:
            self._close(t1 - 1, float(self.b.c[t1 - 1]), "eod")
        return self.trades

    # ------------------------------------------------------------- helpers
    def _pool_add(self, px: float, kind: int, k: float, t: int):
        w0 = {2.0: 0.6, 4.0: 1.0, 8.0: 1.3, 16.0: 1.0}.get(float(k), 1.0)
        r = 0.35 * self._sig_px(t)
        ids = self.book.candidates(px - r, px + r, span_buckets=8)
        if len(ids):
            ids = ids[(self.book.kind[ids] == kind) & self.book.alive[ids]]
        if len(ids):
            ws = np.array([self.book.strength(int(i), t) for i in ids])
            self.book.merge_into(int(ids[int(np.argmax(ws))]), px, w0, t)
        else:
            self.book.add(px, kind, w0, t, src=0)

    def _publish_session(self, t: int):
        for k in ("pdh", "pdl", "ash", "asl", "lonh", "lonl", "onh", "onl"):
            v = self.levels[k][t]
            if not np.isfinite(v):
                continue
            prev = self.levels[k][t - 1] if t > 0 else np.nan
            if np.isfinite(prev) and abs(v - prev) < 1e-12:
                continue
            self.book.add(float(v), 1 if k.endswith("h") else -1, 1.4, t, src=1)

    def _book_step(self, t: int):
        from ..core.liquidity import SWEEP_EPS_SIGMA

        out = []
        r = SWEEP_EPS_SIGMA * self._sig_px(t)
        lo = min(self.b.l[t], self.b.c[t]) - 4 * r
        hi = max(self.b.h[t], self.b.c[t]) + 4 * r
        ids = self.book.candidates(lo, hi, span_buckets=10)
        if len(ids) == 0:
            return out
        ids = ids[self.book.alive[ids]]
        hh, ll, cc = self.b.h[t], self.b.l[t], self.b.c[t]
        for pid in ids:
            pid = int(pid)
            P = float(self.book.px[pid])
            kind = int(self.book.kind[pid])
            if kind > 0:
                if not self.book.pierced[pid]:
                    if hh > P + r:
                        self.book.pierced[pid] = True
                        self.book.pierce_t[pid] = t
                        self.book.pierce_ext[pid] = hh
                    elif P - r <= ll <= P + r:
                        self.book.last[pid] = t
                        self.book.touches[pid] += 0.5
                else:
                    self.book.pierce_ext[pid] = max(self.book.pierce_ext[pid], hh)
                    if cc < P:
                        ext = float(self.book.pierce_ext[pid])
                        out.append(self._mk_sweep(t, pid, P, 1, ext, r))
                        self.book.retire(pid)
                    elif t - self.book.pierce_t[pid] > 36:
                        self.book.retire(pid)
            else:
                if not self.book.pierced[pid]:
                    if ll < P - r:
                        self.book.pierced[pid] = True
                        self.book.pierce_t[pid] = t
                        self.book.pierce_ext[pid] = ll
                    elif P - r <= hh <= P + r:
                        self.book.last[pid] = t
                        self.book.touches[pid] += 0.5
                else:
                    self.book.pierce_ext[pid] = min(self.book.pierce_ext[pid], ll)
                    if cc > P:
                        ext = float(self.book.pierce_ext[pid])
                        out.append(self._mk_sweep(t, pid, P, -1, ext, r))
                        self.book.retire(pid)
                    elif t - self.book.pierce_t[pid] > 36:
                        self.book.retire(pid)
        if (t % 20000) == 0:
            self.book.compaction()
        return out

    def _mk_sweep(self, t, pid, P, kind, ext, r):
        from ..core.liquidity import SweepEvent

        rng = max(self.b.h[t] - self.b.l[t], 1e-12)
        if kind > 0:
            wick = float(np.clip((ext - max(self.b.c[t], self.b.l[t])) / rng, 0, 1))
            over = (ext - P) / self._sig_px(t)
        else:
            wick = float(np.clip((min(self.b.c[t], self.b.h[t]) - ext) / rng, 0, 1))
            over = (P - ext) / self._sig_px(t)
        self.sweep_overshoot.add(float(over))
        return SweepEvent(t=t, pierce_t=int(self.book.pierce_t[pid]), kind=kind, level=float(P),
                          overshoot_sig=float(over), extreme=float(ext), bars=int(t - self.book.pierce_t[pid]),
                          strength=float(self.book.strength(pid, t)), pool_id=pid, wick_ratio=wick)

    def _resolve_legs(self, t: int):
        still = []
        for leg in self.open_legs:
            if t < leg["t"] + leg["horizon"]:
                still.append(leg)
                continue
            res = leg_resolution(self.b, leg["t"], leg["dir"], leg["origin"], leg["extreme"],
                                 horizon=leg["horizon"], ext_target=self.cfg.leg_ext_target,
                                 inval_buffer=self.cfg.leg_inval_buffer)
            if res is not None:
                self.ret_model.observe(res["depth"], res["outcome"], res["ext"])
                self.leg_ext.add(float(res["ext"]))
        self.open_legs = still

    # ------------------------------------------------------------ narrative
    def _narrate(self, t, direction, sweep, sweep_q, d, brk_sig, n_conf, fvg_i, pd_q,
                 fresh, d_star, entry_px, stop, t1, t2, prob, size, inten, htf, rr,
                 pools, x) -> str:
        side = "LONG" if direction > 0 else "SHORT"
        pool_kind = "buy-side" if sweep.kind > 0 else "sell-side"
        L = []
        L.append(f"[{self._t(t)}] {side} setup. ")
        L.append(
            f"Liquidity: a {pool_kind} pool at {sweep.level:,.2f} "
            f"(strength {sweep.strength:.2f}, {sweep.bars} bar raid) was run to "
            f"{sweep.extreme:,.2f} — {sweep.overshoot_sig:.2f} sigma beyond it — and price "
            f"closed back inside. Raid quality {sweep_q:.2f}. "
        )
        L.append(
            f"Displacement: {d['z'][t]:.2f} diffusion-units of move over "
            f"{self.cfg.disp_lookback} bars with {d['eff'][t]*100:.0f}% efficiency "
            f"({'clean delivery' if d['eff'][t] > 0.45 else 'some chop'}). "
        )
        L.append(
            f"Structure: close is {brk_sig:.2f} sigma past the last opposite swing; "
            f"{n_conf}/{len(SCALES)} swing scales confirm the shift. "
        )
        if fvg_i is not None:
            L.append(
                f"PD array: a {'bullish' if direction > 0 else 'bearish'} fair value gap "
                f"{self.fvg.bot[fvg_i]:,.2f}-{self.fvg.top[fvg_i]:,.2f} "
                f"({self.fvg.size_sig[fvg_i]:.2f} sigma wide, size in the top "
                f"{(1-pd_q)*100:.0f}% of recent gaps, {fresh*100:.0f}% unfilled). "
            )
        L.append(
            f"Entry: the retracement model, which started at ICT's 62-79% prior and has "
            f"now seen {self.ret_model.n_legs:.0f} legs, puts the EV-optimal depth at "
            f"{d_star*100:.1f}% of the leg — entry {entry_px:,.2f}. "
        )
        L.append(
            f"Risk: stop {stop:,.2f}, beyond the raid wick by a buffer learned from "
            f"how far past swept pools this instrument actually travels. "
        )
        if pools:
            L.append(
                f"Targets: nearest opposing pool at {t1:,.2f} (strength {pools[0][1]:.2f})"
                + (f", then {t2:,.2f}." if len(pools) > 1 else f", then the measured move {t2:,.2f}.")
            )
        L.append(
            f"Clock: this 15-minute bucket is scoring {inten:.2f}x the day's average delivery. "
        )
        L.append(
            f"Bias: HTF agreement {htf:+.2f}. Verdict: evidence {self.evid.score(x)[0]:+.2f} bits "
            f"-> p(win) {prob:.2f} -> {self._kelly(prob, rr)*self.cfg.risk_pct*100:.2f}% of equity at risk "
            f"({size:.4f} units, R:R {rr:.2f})."
        )
        return "".join(L)
