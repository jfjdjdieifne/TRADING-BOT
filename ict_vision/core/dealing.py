"""Dealing range, premium/discount, and the Optimal Trade Entry -- learned.

=============================================================================
THE QUESTION THIS FILE ANSWERS
=============================================================================
Every ICT course says: buy in discount, sell in premium, and enter between the
62% and 79% retracement, ideally at 70.5%.  Every programmer asks: *why 62?
why not 58?  and why is "discount" below 50%?*

Our answers, both derived rather than asserted:

DISCOUNT/PREMIUM.  The equilibrium of a range is not its arithmetic midpoint.
It is the centroid of the time the market has actually spent inside it.  We
carry a running time-weighted mean price and use THAT as the equilibrium; the
arithmetic midpoint is only correct if time-at-price is symmetric, which on
this instrument it is not.  The number is printed in every report so you can
see how far it sits from 50%.

OPTIMAL TRADE ENTRY.  We do not pick a Fibonacci level.  We keep, for every
displacement leg the engine has seen, two histograms indexed by *how deep the
retracement went*:

    H_win[d]  : legs that retraced at least to depth d and then delivered
    H_los[d]  : legs that retraced at least to depth d and then failed

from which  p(win | retraced to d)  and  p(price even reaches d)  are both
read off.  The entry depth is then the d that maximises expected value

    EV(d) = p(reach d) * [ p(win|d) * R(d) - (1 - p(win|d)) * 1 ]

with  R(d) = (target - entry) / (entry - stop)  computed from the leg's own
geometry.  Deeper entries pay more *if* they get filled and *if* the leg still
works; shallower entries get filled more often.  The optimum is where those
two forces balance -- and that is a number the data chooses.

The ICT 62-79% band enters as a **Bayesian prior** on p(win|d), peaking at
70.5%, with the weight of 40 pseudo-observations.  It is therefore the
starting point of the model, not a hard-coded rule, and the report shows both
the prior and the posterior so you can see exactly how far the data moved it.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


# --------------------------------------------------------------------- range
def session_range_state(bars, day: np.ndarray) -> dict:
    """Causal session extremes plus the time-weighted equilibrium.

    eq = running mean of the typical price over the bars that formed the range.
    This is the centroid of time-at-price, i.e. the level around which the
    market has actually balanced -- not (high+low)/2.
    """
    n = bars.n
    tp = 0.5 * (bars.h + bars.l)
    sess = np.empty(n, dtype=np.int64)
    prev = None
    cur = -1
    start = np.zeros(n, dtype=np.int64)
    for i, d in enumerate(day):
        if d != prev:
            cur += 1
            prev = d
            start[cur] = i
        sess[i] = cur
    ns = cur + 1
    hi = np.full(n, np.nan)
    lo = np.full(n, np.nan)
    eq = np.full(n, np.nan)
    alive = np.zeros(ns, bool)
    cur_hi = np.full(ns, -np.inf)
    cur_lo = np.full(ns, np.inf)
    cur_sum = np.zeros(ns)
    cur_cnt = np.zeros(ns)
    for i in range(n):
        s = sess[i]
        if not alive[s]:
            alive[s] = True
            cur_hi[s] = -np.inf
            cur_lo[s] = np.inf
            cur_sum[s] = 0.0
            cur_cnt[s] = 0.0
        cur_hi[s] = max(cur_hi[s], bars.h[i])
        cur_lo[s] = min(cur_lo[s], bars.l[i])
        cur_sum[s] += tp[i]
        cur_cnt[s] += 1.0
        hi[i] = cur_hi[s]
        lo[i] = cur_lo[s]
        eq[i] = cur_sum[s] / max(cur_cnt[s], 1.0)
    rng = np.maximum(hi - lo, 1e-12)
    return {
        "hi": hi, "lo": lo, "eq": eq, "range": rng,
        "pd": (bars.c - eq) / (0.5 * rng),        # 0 at equilibrium, +-1 at the extremes
        "pos": (bars.c - lo) / rng,               # 0..1 inside the range
        "sess": sess,
    }


def pd_membership(pd_pos: float, direction: int, width: float = 0.55) -> float:
    """Continuous 'am I in the right half of the range' score.

    A long wants price BELOW equilibrium (discount); a short wants it ABOVE.
    `width` is the range-fraction over which the score decays from 1 to 0 --
    it is a smoothing constant, not a gate: at pd = -0.1 for a long the score
    is 0.83, not 0.
    """
    z = -direction * pd_pos / max(width, 1e-9)
    return float(1.0 / (1.0 + np.exp(-2.2 * z)))


# ------------------------------------------------------------------ the OTE
class RetracementModel:
    """Causal, decaying, Bayesian model of 'how deep do legs retrace'."""

    def __init__(
        self,
        n_bins: int = 60,
        d_max: float = 1.30,
        prior_center: float = 0.705,
        prior_width: float = 0.085,
        prior_amp: float = 0.14,
        prior_base: float = 0.42,
        prior_kappa: float = 20.0,
        halflife: float = 250.0,
    ):
        self.n_bins = n_bins
        self.d_max = d_max
        self.edges = np.linspace(0.0, d_max, n_bins + 1)
        self.centers = 0.5 * (self.edges[:-1] + self.edges[1:])
        self.prior_center = prior_center
        self.prior_width = prior_width
        self.prior_amp = prior_amp
        self.prior_base = prior_base
        self.prior_kappa = prior_kappa
        self.halflife = halflife
        self.win = np.zeros(n_bins)
        self.los = np.zeros(n_bins)
        self.reach = np.zeros(n_bins)
        self.n_legs = 0.0
        self.ext = 1.0          # learned average target extension (multiple of leg)

    # ---------------------------------------------------------------- prior
    def prior_curve(self) -> np.ndarray:
        """ICT's 62-79 / 70.5 encoded as a smooth bump on top of a base rate."""
        d = self.centers
        bump = np.exp(-0.5 * ((d - self.prior_center) / self.prior_width) ** 2)
        return np.clip(self.prior_base + self.prior_amp * bump, 0.01, 0.99)

    # --------------------------------------------------------------- update
    def observe(self, max_depth: float, outcome: int, extension: float | None = None) -> None:
        """Record one resolved leg.

        max_depth : deepest retracement fraction reached before resolution
        outcome   : 1 delivered, 0 failed
        extension : how far past the leg extreme price travelled (in leg units)
        """
        if not np.isfinite(max_depth):
            return
        k = np.searchsorted(self.edges, max_depth, side="right") - 1
        k = int(np.clip(k, 0, self.n_bins - 1))
        a = 1.0 - np.exp(-np.log(2.0) / self.halflife) if self.halflife > 0 else 1.0
        self.win *= (1 - a)
        self.los *= (1 - a)
        self.reach *= (1 - a)
        self.n_legs *= (1 - a)
        self.n_legs += 1.0
        self.reach[: k + 1] += 1.0
        if outcome == 1:
            self.win[: k + 1] += 1.0
        else:
            self.los[: k + 1] += 1.0
        if extension is not None and np.isfinite(extension):
            self.ext += 0.02 * (float(np.clip(extension, -1.0, 6.0)) - self.ext)

    # --------------------------------------------------------------- queries
    def p_win(self) -> np.ndarray:
        w = self.win + self.prior_kappa * self.prior_curve()
        n_ = self.win + self.los + self.prior_kappa
        return w / np.maximum(n_, 1e-9)

    def p_reach(self) -> np.ndarray:
        return np.clip(self.reach / max(self.n_legs, 1e-9), 0.0, 1.0)

    def llr(self) -> np.ndarray:
        p = self.p_win()
        p0 = float(np.clip(p[0], 1e-6, 1 - 1e-6))
        return np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6))) - np.log(p0 / (1 - p0))

    def r_multiple(self, target_ext: float | None = None, buffer_frac: float = 0.08) -> np.ndarray:
        """R(d) = (target - entry) / (entry - stop) for a unit leg.

        leg from origin S=0 to extreme E=1.  entry = 1 - d.  stop = -buffer.
        target = 1 + g.  R is clamped: once the entry is within a few percent
        of the origin the 'risk' is no longer a real stop distance, and an
        unclamped R would run to infinity and drag the optimum to d = 1.
        """
        g = self.ext if target_ext is None else target_ext
        d = self.centers
        entry = 1.0 - d
        stop = -buffer_frac
        risk = entry - stop
        R = (1.0 + g - entry) / np.maximum(risk, 1e-6)
        return np.where(risk > 0.02, np.clip(R, 0.0, 25.0), 0.0)

    def ev(self, target_ext: float | None = None, buffer_frac: float = 0.08) -> np.ndarray:
        p = self.p_win()
        R = self.r_multiple(target_ext, buffer_frac)
        return self.p_reach() * (p * R - (1.0 - p))

    def best_depth(self, target_ext: float | None = None, buffer_frac: float = 0.08,
                   d_lo: float = 0.15, d_hi: float = 0.90, min_reach: float = 0.30):
        """The entry depth that maximises expected value.

        `min_reach` is the fill-probability floor: a depth price almost never
        trades back to is not an entry, it is a wish, and its EV is an
        artefact of a limit order that never fills.
        """
        ev = self.ev(target_ext, buffer_frac)
        sel = (self.centers >= d_lo) & (self.centers <= d_hi) & (self.p_reach() >= min_reach)
        if not sel.any() or self.n_legs < 25:
            return float(np.clip(self.prior_center, d_lo, d_hi)), ev
        i = int(np.argmax(np.where(sel, ev, -np.inf)))
        return float(self.centers[i]), ev

    def hdi(self, mass: float = 0.5) -> tuple[float, float]:
        """Highest-density interval of the EV curve -- the learned 'OTE zone'."""
        ev = self.ev()
        ev = np.clip(ev, 0, None)
        tot = ev.sum()
        if tot <= 0:
            return float(self.prior_center - 0.085), float(self.prior_center + 0.085)
        order = np.argsort(-ev)
        acc = 0.0
        take = []
        for i in order:
            take.append(i)
            acc += ev[i]
            if acc >= mass * tot:
                break
        lo = float(self.centers[min(take)])
        hi = float(self.centers[max(take)])
        return lo, hi

    def snapshot(self) -> dict:
        d, ev = self.best_depth()
        lo, hi = self.hdi()
        return {
            "n_legs_effective": float(self.n_legs),
            "best_depth": d,
            "hdi": (lo, hi),
            "prior_center": self.prior_center,
            "learned_extension": float(self.ext),
            "p_win_at_best": float(np.interp(d, self.centers, self.p_win())),
            "p_reach_at_best": float(np.interp(d, self.centers, self.p_reach())),
            "centers": self.centers.copy(),
            "p_win": self.p_win().copy(),
            "p_reach": self.p_reach().copy(),
            "prior": self.prior_curve().copy(),
            "ev": self.ev().copy(),
        }


def leg_resolution(bars, t: int, direction: int, origin: float, extreme: float,
                   horizon: int = 288, inval_buffer: float = 0.15,
                   ext_target: float = 1.0):
    """Resolve a displacement leg: did it extend, or did it get invalidated?

    Whichever happens FIRST wins.  Also returns the deepest retracement seen
    before resolution, which is what feeds the retracement model.
    """
    n = bars.n
    L = abs(extreme - origin)
    if L <= 0:
        return None
    end = min(n, t + 1 + horizon)
    tgt = extreme + direction * ext_target * L
    inv = origin - direction * inval_buffer * L
    if direction > 0:
        hh = bars.h[t + 1 : end]
        ll = bars.l[t + 1 : end]
        a = np.flatnonzero(hh >= tgt)
        b = np.flatnonzero(ll <= inv)
    else:
        hh = bars.h[t + 1 : end]
        ll = bars.l[t + 1 : end]
        a = np.flatnonzero(ll <= tgt)
        b = np.flatnonzero(hh >= inv)
    ta = int(t + 1 + a[0]) if a.size else -1
    tb = int(t + 1 + b[0]) if b.size else -1
    if ta >= 0 and (tb < 0 or ta < tb):
        outcome, stop_bar = 1, ta
    elif tb >= 0:
        outcome, stop_bar = 0, tb
    else:
        outcome, stop_bar = 0, end - 1
    seg_l = bars.l[t + 1 : stop_bar + 1] if stop_bar > t else np.array([bars.l[t]])
    seg_h = bars.h[t + 1 : stop_bar + 1] if stop_bar > t else np.array([bars.h[t]])
    if direction > 0:
        depth = (extreme - float(seg_l.min())) / L
        ext = (float(seg_h.max()) - extreme) / L
    else:
        depth = (float(seg_h.max()) - extreme) / L
        ext = (extreme - float(seg_l.min())) / L
    return {"outcome": outcome, "depth": float(np.clip(depth, 0.0, 2.0)),
            "ext": float(ext), "bars": int(stop_bar - t)}
