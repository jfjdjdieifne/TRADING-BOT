"""The 'golden trade' confluence score.

Each bar gets a direction-agnostic quality score in [0, 1] from a set of
objective, causal conditions. The idea (from the request) is that stacking many
conditions should raise the probability that a setup reaches its target.

IMPORTANT (honest): a high score raises the hit rate only if the conditions are
actually predictive. This module measures that, it does not assume it. See
`run_confluence.py` for the empirical test.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .primitives import displacement
from .sessions import session_name


def setup_quality(df: pd.DataFrame, atr: np.ndarray, htf_trend: np.ndarray):
    """Return (score[n], parts dict). All causal."""
    h = df["High"].to_numpy(float)
    l = df["Low"].to_numpy(float)
    c = df["Close"].to_numpy(float)
    o = df["Open"].to_numpy(float)
    v = df["Volume"].to_numpy(float) if "Volume" in df else np.zeros(len(df))
    n = len(df)
    idx = pd.DatetimeIndex(df.index)

    rng = h - l
    body = np.abs(c - o)
    disp = displacement(c, o, atr, 1.0)

    # volume expansion vs 20-bar mean
    vol_ok = np.zeros(n, dtype=bool)
    if v.sum() > 0:
        for t in range(20, n):
            base = v[t - 20:t].mean()
            if base > 0:
                vol_ok[t] = v[t] >= 1.5 * base

    # close in top/bottom 25% of the bar range
    close_extreme = np.zeros(n, dtype=bool)
    valid = rng > 0
    pos = np.zeros(n)
    pos[valid] = (c[valid] - l[valid]) / rng[valid]
    close_extreme = (pos >= 0.75) | (pos <= 0.25)

    range_ok = rng >= 0.8 * atr
    htf_ok = htf_trend != 0
    sess_ok = np.array([session_name(idx[t]) in ("london", "ny") for t in range(n)])

    # volatility expanding vs 50-bar median
    vol_regime = np.zeros(n, dtype=bool)
    for t in range(50, n):
        med = np.nanmedian(atr[t - 50:t])
        if med > 0:
            vol_regime[t] = atr[t] >= 0.8 * med

    parts = {
        "disp": disp, "vol": vol_ok, "close_extreme": close_extreme,
        "range": range_ok, "htf": htf_ok, "session": sess_ok, "vol_regime": vol_regime,
    }
    score = np.zeros(n)
    for arr in parts.values():
        score += arr.astype(float)
    score /= float(len(parts))
    return score, parts
