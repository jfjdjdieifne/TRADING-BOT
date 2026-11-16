"""The measuring tape.

Nothing in this package is measured in points or pips: everything is measured
in units of the market's own volatility, `sigma`, estimated causally.

Two ideas:

  sigma_local   per-bar volatility, half-life ~ 2h   -> "how big is a normal bar"
  sigma_slow    per-bar volatility, half-life ~ 3d   -> "what regime are we in"

Their ratio is a dimensionless, instrument-free, level-free read on whether the
market is currently excited or asleep.  A 40 point move on NDX at 8,000 (2020)
and at 29,000 (2026) are the same *number* of sigmas only if you divide by a
local estimate -- this is the first thing that kills the "hard-coded number"
failure mode.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# E|X| for X~N(0,s) is s*sqrt(2/pi).  We use the median-ish robust version:
# MAD of a normal -> sigma = MAD / 0.6745.  Using the mean of |r| and dividing
# by 0.7979 is the estimator; both are scale-correct, neither is a threshold.
_K_ABS = np.sqrt(2.0 / np.pi)


def ewma(x: np.ndarray, halflife: float, init: float | None = None) -> np.ndarray:
    """Causal exponentially weighted mean. halflife in samples."""
    x = np.asarray(x, float)
    if halflife <= 0:
        return x.copy()
    a = 1.0 - np.exp(-np.log(2.0) / halflife)
    out = np.empty_like(x)
    acc = x[0] if init is None else float(init)
    a_arr = a
    for i in range(len(x)):
        acc += a_arr * (x[i] - acc)
        out[i] = acc
    return out


def ewma_np(x: np.ndarray, halflife: float) -> np.ndarray:
    """Same thing, pandas' C implementation (faster, identical maths)."""
    a = 1.0 - np.exp(-np.log(2.0) / halflife)
    return pd.Series(x).ewm(alpha=a, adjust=False).mean().to_numpy()


def logret(c: np.ndarray) -> np.ndarray:
    r = np.empty_like(c)
    r[0] = 0.0
    r[1:] = np.diff(np.log(c))
    return r


def abs_sigma(c: np.ndarray, halflife: float) -> np.ndarray:
    """Robust causal per-bar sigma from |log return|, winsorised at 8 sigma."""
    r = np.abs(logret(c))
    # one winsorising pass: clamp single-bar shocks so one news spike cannot
    # inflate the tape for the next hour.
    s0 = ewma_np(r, halflife)
    hi = 8.0 * s0 / _K_ABS
    r = np.minimum(r, hi)
    return ewma_np(r, halflife) / _K_ABS


def sigma_field(c: np.ndarray, hl_fast: float = 24.0, hl_slow: float = 288.0) -> dict:
    """Return {'fast','slow','ratio'} arrays of the same length as c.

    halflives are expressed in bars of whatever timeframe is passed in.
    For 5-minute bars: 24 bars = 2h, 288 bars = 24h.
    """
    fast = abs_sigma(c, hl_fast)
    slow = abs_sigma(c, hl_slow)
    ratio = fast / np.maximum(slow, 1e-12)
    return {"fast": fast, "slow": slow, "ratio": ratio}


def ewma_vol_percentile(ratio: np.ndarray, halflife: float = 2000.0) -> np.ndarray:
    """Where does the current fast/slow ratio sit inside its own recent
    distribution?  Computed causally by comparing the live value against an
    EWMA of squared deviations from the EWMA mean (i.e. an EW variance), then
    mapping through the normal CDF.  Returns a value in (0,1).

    This is a *regime* coordinate, not a threshold: it is used to condition
    the learned parameters, never to gate on.
    """
    m = ewma_np(ratio, halflife)
    d2 = ewma_np((ratio - m) ** 2, halflife)
    sd = np.sqrt(np.maximum(d2, 1e-18))
    z = (ratio - m) / sd
    from scipy.stats import norm

    return norm.cdf(np.clip(z, -8, 8))


def forward_range_ratio(
    h: np.ndarray, l: np.ndarray, sigma: np.ndarray, horizon: int
) -> np.ndarray:
    """Causal empirical scaling law: how many sigmas wide is the next `horizon`
    bar range, expressed as a multiple of sqrt(horizon)*sigma?

    Returns a single scalar ratio (estimated on the sample given).  Used to
    convert "distance to target in sigma" into "expected bars to get there".
    sqrt-time is the null; the fitted ratio says how far reality departs from
    it (trending markets overshoot, choppy markets undershoot).
    """
    n = len(h)
    if n <= horizon + 10:
        return 1.0
    hh = pd.Series(h).rolling(horizon).max().shift(-(horizon - 1)).to_numpy()
    ll = pd.Series(l).rolling(horizon).min().shift(-(horizon - 1)).to_numpy()
    ok = ~np.isnan(hh) & ~np.isnan(ll)
    rng = (hh - ll)[ok]
    base = (np.sqrt(horizon) * sigma)[ok]
    good = base > 0
    if good.sum() < 50:
        return 1.0
    return float(np.median(rng[good] / base[good]))


def rolling_quantile_causal(x: np.ndarray, window: int, q: float) -> np.ndarray:
    """Trailing quantile using only data up to and including each bar.

    pandas' rolling quantile is a causal (backward-looking) C implementation;
    `min_periods=1` just means the first bars use a shorter window, which is
    still causal.  No centring, no shifting.
    """
    return (
        pd.Series(x).rolling(window, min_periods=1).quantile(q).to_numpy()
    )


def forward_min(a: np.ndarray, window: int) -> np.ndarray:
    """min over [i, i+window-1], aligned at i (causal to consume at i+window)."""
    return pd.Series(a).rolling(window, min_periods=1).min().shift(-(window - 1)).to_numpy()


def forward_max(a: np.ndarray, window: int) -> np.ndarray:
    """max over [i, i+window-1], aligned at i."""
    return pd.Series(a).rolling(window, min_periods=1).max().shift(-(window - 1)).to_numpy()
