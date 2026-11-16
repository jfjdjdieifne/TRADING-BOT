"""Session definitions and opening-range (ORB) levels — strictly causal.

Sessions are UTC windows (crypto trades 24/7, FX/CFD follows the cash clock).
The opening range is the first ``or_min`` minutes after a session start; the
breakout window is the following ``window_min`` minutes. A bar at time ``t`` may
only use a range whose end ``<= t`` (no lookahead).

Evidence for these windows (see math_notes.md):
  * the opening ~30 min of the cash session ~= 32% of the daily range (ES);
  * ~67% of daily extremes form in the opening/closing windows;
  * London/NY opens are the most volatile, most liquid windows (NBER/Örebro).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Session:
    name: str
    start_hour: int          # UTC
    or_min: int = 15         # opening-range length
    window_min: int = 180    # breakout window after the range
    strength: float = 1.0    # empirical quality weight


SESSIONS = {
    "london": Session("london", 7, 15, 180, 1.0),
    "ny": Session("ny", 13, 15, 180, 1.0),
    "overlap": Session("overlap", 13, 30, 120, 0.9),
    "asia": Session("asia", 0, 30, 180, 0.5),
}


def session_name(ts) -> str:
    h = ts.hour
    if 7 <= h < 13:
        return "london"
    if 13 <= h < 17:
        return "ny"
    if 0 <= h < 7:
        return "asia"
    return "other"


def opening_range_arrays(df: pd.DataFrame, session: Session):
    """Causal ORB arrays.

    Returns ``(or_high, or_low, break_hi, break_lo, in_window)`` where
    ``or_high[t]``/``or_low[t]`` are the opening-range levels once the range has
    completed (NaN before), ``in_window[t]`` marks the breakout window, and
    ``break_hi``/``break_lo`` mark a close beyond the level known at ``t-1``.
    """
    idx = pd.DatetimeIndex(df.index)
    h = df["High"].to_numpy(float)
    l = df["Low"].to_numpy(float)
    c = df["Close"].to_numpy(float)
    n = len(df)
    or_high = np.full(n, np.nan)
    or_low = np.full(n, np.nan)
    in_window = np.zeros(n, dtype=bool)
    span = session.or_min + session.window_min
    for t in range(n):
        ts = idx[t]
        start = ts.normalize() + pd.Timedelta(hours=session.start_hour)
        if start > ts:
            start -= pd.Timedelta(days=1)
        mins = (ts - start).total_seconds() / 60.0
        if mins < 0 or mins >= span:
            continue
        lo = idx.searchsorted(start, side="left")
        hi = idx.searchsorted(start + pd.Timedelta(minutes=session.or_min),
                              side="left")
        if mins >= session.or_min and hi > lo:
            or_high[t] = h[lo:hi].max()
            or_low[t] = l[lo:hi].min()
            in_window[t] = True
    break_hi = np.zeros(n, dtype=bool)
    break_lo = np.zeros(n, dtype=bool)
    for t in range(1, n):
        if not np.isnan(or_high[t - 1]):
            if c[t] > or_high[t - 1]:
                break_hi[t] = True
            if c[t] < or_low[t - 1]:
                break_lo[t] = True
    return or_high, or_low, break_hi, break_lo, in_window


def all_session_arrays(df: pd.DataFrame):
    return {name: opening_range_arrays(df, s) for name, s in SESSIONS.items()}
