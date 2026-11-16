"""The learning layer: everything here is estimated from data, causally.

Three small online models, all of them walk-forward and all of them decaying so
they track a market that changes:

  EvidenceModel  naive-Bayes log-likelihood-ratio accumulation over the
                 setup's continuous features.  This is the piece that answers
                 "is THIS setup good?" -- and, unlike a hard checklist, it
                 answers with a number and a reason: +0.8 bits from the sweep,
                 -0.3 bits from the clock, etc.

  HazardModel    discrete-time survival: P(still going to win | survived to
                 bar b of the trade).  Used to abandon a trade that has stopped
                 behaving like a winner instead of holding it to a fixed
                 time-of-day.

  ReachModel     online logistic regression: P(price reaches level D before
                 stop level S | context).  Drives target selection and the
                 partial-exit fractions.

  QuantileTracker decayed histogram -> running quantiles with no fixed window.
"""

from __future__ import annotations

import numpy as np


# --------------------------------------------------------------- quantiles
class QuantileTracker:
    """Decayed histogram over a fixed range -> causal running quantiles."""

    def __init__(self, lo: float, hi: float, nbins: int = 100, halflife: float = 400.0):
        self.lo, self.hi, self.nb = lo, hi, nbins
        self.edges = np.linspace(lo, hi, nbins + 1)
        self.hist = np.zeros(nbins)
        self.hl = halflife

    def add(self, x: float) -> None:
        if not np.isfinite(x):
            return
        self.hist *= np.exp(-np.log(2.0) / self.hl)
        i = int(np.clip(np.searchsorted(self.edges, x, side="right") - 1, 0, self.nb - 1))
        self.hist[i] += 1.0

    def quantile(self, q: float) -> float:
        tot = self.hist.sum()
        if tot < 5:
            return float(np.interp(q, [0, 1], [self.lo, self.hi]))
        cs = np.cumsum(self.hist) / tot
        i = int(np.searchsorted(cs, q))
        i = int(np.clip(i, 0, self.nb - 1))
        return float(0.5 * (self.edges[i] + self.edges[i + 1]))

    @property
    def n(self) -> float:
        return float(self.hist.sum())


# ---------------------------------------------------------------- evidence
class EvidenceModel:
    """Decayed naive-Bayes log-likelihood ratio over binned continuous features."""

    def __init__(self, names: list[str], n_bins: int = 6, halflife: float = 300.0,
                 prior: float = 0.0, shrink_n0: float = 60.0, alpha: float = 1.0):
        self.names = list(names)
        self.nb = n_bins
        self.hl = halflife
        self.prior = prior
        self.n0 = shrink_n0
        self.alpha = alpha
        self.win = np.zeros((len(names), n_bins))
        self.los = np.zeros((len(names), n_bins))
        self.n_obs = 0.0
        self.res: list[np.ndarray] = [np.zeros(0) for _ in names]
        self.edges: list[np.ndarray] = [np.linspace(0, 1, n_bins + 1) for _ in names]
        self._pending: list[tuple[np.ndarray, int]] = []

    # ------------------------------------------------------------- binning
    def _rebin(self) -> None:
        for j in range(len(self.names)):
            r = self.res[j]
            if len(r) < 50:
                continue
            qs = np.quantile(r, np.linspace(0, 1, self.nb + 1)[1:-1])
            # enforce strict monotonicity (duplicate quantile values otherwise
            # collapse bins and make the LLR table degenerate)
            qs = np.maximum.accumulate(qs + np.arange(len(qs)) * 1e-12)
            self.edges[j] = np.r_[-np.inf, qs, np.inf]

    def encode(self, x: np.ndarray) -> np.ndarray:
        out = np.zeros(len(self.names), dtype=np.int64)
        for j in range(len(self.names)):
            v = float(x[j])
            if not np.isfinite(v):
                v = 0.0
            out[j] = int(np.clip(np.searchsorted(self.edges[j], v, side="right") - 1, 0, self.nb - 1))
        for j in range(len(self.names)):
            r = self.res[j]
            if len(r) < 4000:
                self.res[j] = np.append(r, x[j])
            else:
                self.res[j][np.random.randint(0, len(r))] = x[j]
        return out

    def maybe_rebin(self) -> None:
        if self.n_obs % 128 == 0:
            self._rebin()

    # -------------------------------------------------------------- predict
    def score(self, x: np.ndarray) -> tuple[float, np.ndarray]:
        """Return (total log-odds contribution, per-feature LLR vector)."""
        b = self.encode(x)
        llr = np.zeros(len(self.names))
        for j in range(len(self.names)):
            w = self.win[j, b[j]] + self.alpha
            l = self.los[j, b[j]] + self.alpha
            nw = self.win[j].sum() + self.alpha * self.nb
            nl = self.los[j].sum() + self.alpha * self.nb
            llr[j] = np.log((w / nw) / (l / nl))
        shrink = self.n_obs / (self.n_obs + self.n0)
        return float(llr.sum() * shrink + self.prior), llr * shrink

    def probability(self, x: np.ndarray) -> float:
        s, _ = self.score(x)
        return float(1.0 / (1.0 + np.exp(-np.clip(s, -30, 30))))

    # --------------------------------------------------------------- update
    def update(self, x: np.ndarray, y: int) -> None:
        b = self.encode(x)
        a = 1.0 - np.exp(-np.log(2.0) / max(self.hl, 1.0))
        self.win *= (1 - a)
        self.los *= (1 - a)
        self.n_obs *= (1 - a)
        self.n_obs += 1.0
        for j in range(len(self.names)):
            if y == 1:
                self.win[j, b[j]] += 1.0
            else:
                self.los[j, b[j]] += 1.0
        self.maybe_rebin()

    def table(self) -> dict:
        out = {}
        for j, nm in enumerate(self.names):
            w = self.win[j] + self.alpha
            l = self.los[j] + self.alpha
            tot = w + l
            out[nm] = {
                "win": self.win[j].copy(),
                "los": self.los[j].copy(),
                "edge": (w / tot).copy(),
            }
        return out


# ------------------------------------------------------------------ hazard
class HazardModel:
    """P(win | still open after `b` bars). No fixed time-of-day exit."""

    def __init__(self, max_bars: int = 288, halflife: float = 300.0, prior: float = 0.45):
        self.mb = max_bars
        self.hl = halflife
        self.surv = np.zeros(max_bars)
        self.winlater = np.zeros(max_bars)
        self.prior = prior

    def start(self) -> None:
        pass

    def observe_open(self, bars_held: int) -> None:
        pass

    def record(self, path: list[int], won: int) -> None:
        """`path` = the bars at which the trade was still open."""
        a = 1.0 - np.exp(-np.log(2.0) / max(self.hl, 1.0))
        self.surv *= (1 - a)
        self.winlater *= (1 - a)
        for b in path:
            if 0 <= b < self.mb:
                self.surv[b] += 1.0
                if won:
                    self.winlater[b] += 1.0

    def p(self, b: int) -> float:
        i = int(np.clip(b, 0, self.mb - 1))
        s = self.surv[i]
        if s < 12:
            return self.prior
        return float((self.winlater[i] + self.prior * 12) / (s + 12))


# ------------------------------------------------------------------- reach
class ReachModel:
    """P(price travels D before it travels S), D and S in sigmas.

    Features: log(D/S), 1/sqrt(D) (diffusion is harder over long distances),
    session intensity, and the direction's agreement with the HTF bias.
    Trained by online logistic regression (SGD) on resolved setups.
    """

    def __init__(self, lr: float = 0.05, l2: float = 1e-4, halflife: float = 500.0):
        self.w = np.array([-1.0, 0.0, 0.0, 0.0, 0.0])
        self.lr = lr
        self.l2 = l2
        self.hl = halflife
        self.n = 0.0

    @staticmethod
    def phi(d_sig: float, s_sig: float, intensity: float, htf: float) -> np.ndarray:
        d = max(d_sig, 1e-6)
        s = max(s_sig, 1e-6)
        return np.array([1.0, np.log(d / s), 1.0 / np.sqrt(d), intensity - 1.0, htf])

    def predict(self, d_sig: float, s_sig: float, intensity: float = 1.0, htf: float = 0.0) -> float:
        z = float(self.w @ self.phi(d_sig, s_sig, intensity, htf))
        return float(1.0 / (1.0 + np.exp(-np.clip(z, -30, 30))))

    def update(self, d_sig: float, s_sig: float, y: int, intensity: float = 1.0, htf: float = 0.0) -> None:
        x = self.phi(d_sig, s_sig, intensity, htf)
        p = 1.0 / (1.0 + np.exp(-np.clip(self.w @ x, -30, 30)))
        g = (y - p) * self.lr
        self.w = self.w * (1 - self.lr * self.l2) + g * x
        self.n += 1.0

    def fit_offline(self, X: np.ndarray, y: np.ndarray) -> None:
        """Closed-form warm start (Newton/IRLS) if enough data exists."""
        if len(y) < 200:
            return
        w = self.w.copy()
        Xb = np.c_[np.ones(len(y)), X]
        for _ in range(60):
            z = Xb @ w
            p = 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))
            W = np.clip(p * (1 - p), 1e-6, None)
            H = Xb.T @ (Xb * W[:, None]) + 1e-6 * np.eye(Xb.shape[1])
            g = Xb.T @ (y - p)
            step = np.linalg.solve(H, g)
            w = w + step
            if np.max(np.abs(step)) < 1e-8:
                break
        self.w = w


# --------------------------------------------------------------- breakeven
class ComebackModel:
    """P(trade returns to entry | it was once `m` sigmas in profit).

    This is what decides when to take the stop to break-even.  Moving to BE
    too early throws away winners that needed room; too late gives back the
    whole open profit.  The market tells us which is which.
    """

    def __init__(self, grid=(0.5, 1.0, 1.5, 2.0, 3.0, 4.0), halflife: float = 250.0):
        self.grid = np.array(grid, float)
        self.back = np.zeros(len(grid))
        self.tot = np.zeros(len(grid))
        self.hl = halflife

    def record(self, max_mfe_sig: float, came_back: int) -> None:
        a = 1.0 - np.exp(-np.log(2.0) / max(self.hl, 1.0))
        self.back *= (1 - a)
        self.tot *= (1 - a)
        k = int(np.searchsorted(self.grid, max_mfe_sig, side="right") - 1)
        for j in range(max(k, 0) + 1):
            self.tot[j] += 1.0
            if came_back:
                self.back[j] += 1.0

    def p(self, m: float) -> float:
        j = int(np.clip(np.searchsorted(self.grid, m, side="right") - 1, 0, len(self.grid) - 1))
        if self.tot[j] < 10:
            return 0.5
        return float(self.back[j] / self.tot[j])
