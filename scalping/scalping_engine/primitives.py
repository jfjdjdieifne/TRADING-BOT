"""Strictly causal (zero-lookahead) primitives for the scalping engine.

Conventions
-----------
* Input arrays are aligned to *closed* bars, index ``t`` = bar that just closed.
* A pivot at bar ``i`` is only *known* at bar ``i + k`` (k confirming bars).
  ``swing_state`` therefore exposes, for every ``t``, the latest pivot whose
  confirmation time is ``<= t``.
* Nothing here reads a future bar. The backtest and the live bot share these
  functions, so a signal that is causal here is causal everywhere.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


# --------------------------------------------------------------------------- #
# ATR
# --------------------------------------------------------------------------- #
def wilder_atr(high, low, close, n: int = 14) -> np.ndarray:
    """Wilder-smoothed ATR. ``atr[t]`` uses only true ranges from bars <= t."""
    h = np.asarray(high, dtype=np.float64)
    l = np.asarray(low, dtype=np.float64)
    c = np.asarray(close, dtype=np.float64)
    m = len(c)
    atr = np.full(m, np.nan, dtype=np.float64)
    if m == 0:
        return atr
    tr = np.empty(m, dtype=np.float64)
    tr[0] = h[0] - l[0]
    for i in range(1, m):
        tr[i] = max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
    if m >= n:
        atr[n - 1] = tr[:n].mean()
        for i in range(n, m):
            atr[i] = (atr[i - 1] * (n - 1) + tr[i]) / n
    return atr


# --------------------------------------------------------------------------- #
# Swings (causal)
# --------------------------------------------------------------------------- #
def swing_points(high, low, k: int = 2):
    """Return (pivot_high_price, pivot_low_price) arrays indexed at pivot bar.

    A pivot at ``i`` is a strict local extremum over ``[i-k, i+k]``.
    """
    h = np.asarray(high, dtype=np.float64)
    l = np.asarray(low, dtype=np.float64)
    m = len(h)
    phi = np.full(m, np.nan, dtype=np.float64)
    plo = np.full(m, np.nan, dtype=np.float64)
    for i in range(k, m - k):
        wh = h[i - k:i + k + 1]
        wl = l[i - k:i + k + 1]
        if h[i] >= wh.max() and (wh == h[i]).sum() == 1:
            phi[i] = h[i]
        if l[i] <= wl.min() and (wl == l[i]).sum() == 1:
            plo[i] = l[i]
    return phi, plo


@dataclass
class SwingState:
    """Latest confirmed swing high/low known at each bar index ``t``."""

    high: np.ndarray  # price of latest confirmed swing high at t (nan if none)
    low: np.ndarray
    high_idx: np.ndarray  # pivot bar index (-1 if none)
    low_idx: np.ndarray

    @classmethod
    def build(cls, high, low, k: int = 2) -> "SwingState":
        h = np.asarray(high, dtype=np.float64)
        l = np.asarray(low, dtype=np.float64)
        m = len(h)
        phi, plo = swing_points(h, l, k)
        out_hi = np.full(m, np.nan)
        out_lo = np.full(m, np.nan)
        idx_hi = np.full(m, -1, dtype=np.int64)
        idx_lo = np.full(m, -1, dtype=np.int64)
        last_hi = np.nan
        last_lo = np.nan
        last_hi_i = -1
        last_lo_i = -1
        # pivot at i is confirmed at i+k -> becomes visible at t = i+k
        for t in range(m):
            p = t - k
            if p >= 0:
                if not np.isnan(phi[p]):
                    last_hi, last_hi_i = phi[p], p
                if not np.isnan(plo[p]):
                    last_lo, last_lo_i = plo[p], p
            out_hi[t] = last_hi
            out_lo[t] = last_lo
            idx_hi[t] = last_hi_i
            idx_lo[t] = last_lo_i
        return cls(out_hi, out_lo, idx_hi, idx_lo)


# --------------------------------------------------------------------------- #
# Order blocks
# --------------------------------------------------------------------------- #
@dataclass
class OrderBlock:
    side: int          # +1 bullish (buy zone), -1 bearish (sell zone)
    top: float
    bottom: float
    formed_idx: int    # bar that created the block
    impulse_idx: int   # displacement bar that caused it
    mitigated: bool = False


def order_blocks(open_, high, low, close, atr, lookback: int = 8,
                 disp_mult: float = 1.0, atr_norm: float = 14.0) -> list:
    """Detect SMC order blocks causally.

    A bullish OB is the last *down* candle immediately preceding a strong
    bullish displacement candle; the zone is that candle's [min(oc), max(oc)].
    Mirror for bearish. Blocks become known at the displacement bar.
    """
    o = np.asarray(open_, dtype=np.float64)
    h = np.asarray(high, dtype=np.float64)
    l = np.asarray(low, dtype=np.float64)
    c = np.asarray(close, dtype=np.float64)
    a = np.asarray(atr, dtype=np.float64)
    m = len(c)
    blocks: list[OrderBlock] = []
    for i in range(1, m):
        if np.isnan(a[i]) or a[i] <= 0:
            continue
        body = c[i] - o[i]
        rng = h[i] - l[i]
        if rng <= 0:
            continue
        # displacement: body dominates the candle and exceeds mult * ATR
        if abs(body) >= disp_mult * a[i] and abs(body) >= 0.6 * rng:
            if body > 0:
                # prior window: find last down candle
                for j in range(i - 1, max(-1, i - 1 - lookback), -1):
                    if c[j] < o[j]:
                        blocks.append(OrderBlock(
                            side=1,
                            top=max(o[j], c[j]),
                            bottom=min(o[j], c[j]),
                            formed_idx=j,
                            impulse_idx=i,
                        ))
                        break
            else:
                for j in range(i - 1, max(-1, i - 1 - lookback), -1):
                    if c[j] > o[j]:
                        blocks.append(OrderBlock(
                            side=-1,
                            top=max(o[j], c[j]),
                            bottom=min(o[j], c[j]),
                            formed_idx=j,
                            impulse_idx=i,
                        ))
                        break
    return blocks


# --------------------------------------------------------------------------- #
# Fair value gaps
# --------------------------------------------------------------------------- #
@dataclass
class FVG:
    side: int      # +1 bullish gap, -1 bearish gap
    top: float
    bottom: float
    idx: int


def fair_value_gaps(high, low) -> list:
    """Three-candle imbalance. Bullish: low[i] > high[i-2]."""
    h = np.asarray(high, dtype=np.float64)
    l = np.asarray(low, dtype=np.float64)
    m = len(h)
    out: list[FVG] = []
    for i in range(2, m):
        if l[i] > h[i - 2]:
            out.append(FVG(1, l[i], h[i - 2], i))
        elif h[i] < l[i - 2]:
            out.append(FVG(-1, l[i - 2], h[i], i))
    return out


# --------------------------------------------------------------------------- #
# Displacement / sweeps / candles
# --------------------------------------------------------------------------- #
def displacement(close, open_, atr, mult: float = 1.0) -> np.ndarray:
    """Boolean array: candle body >= mult * ATR."""
    c = np.asarray(close, dtype=np.float64)
    o = np.asarray(open_, dtype=np.float64)
    a = np.asarray(atr, dtype=np.float64)
    out = np.zeros(len(c), dtype=bool)
    valid = ~np.isnan(a) & (a > 0)
    out[valid] = np.abs(c[valid] - o[valid]) >= mult * a[valid]
    return out


def sweep_events(high, low, close, swing: SwingState):
    """Liquidity sweeps known at each bar.

    A buy-side sweep at bar t: ``high[t] > last_confirmed_swing_high`` but
    ``close[t] <`` that level (takeout then rejection). Returns two boolean
    arrays (bullish_sweep, bearish_sweep).
    """
    h = np.asarray(high, dtype=np.float64)
    l = np.asarray(low, dtype=np.float64)
    c = np.asarray(close, dtype=np.float64)
    m = len(c)
    bull = np.zeros(m, dtype=bool)
    bear = np.zeros(m, dtype=bool)
    for t in range(1, m):
        sh = swing.high[t - 1]   # last confirmed swing high BEFORE bar t
        sl = swing.low[t - 1]
        if not np.isnan(sh) and h[t] > sh and c[t] < sh:
            bull[t] = True
        if not np.isnan(sl) and l[t] < sl and c[t] > sl:
            bear[t] = True
    return bull, bear


def candle_patterns(open_, high, low, close):
    """Engulfing + pin-bar confirmation, causal (uses t-1 and t)."""
    o = np.asarray(open_, dtype=np.float64)
    h = np.asarray(high, dtype=np.float64)
    l = np.asarray(low, dtype=np.float64)
    c = np.asarray(close, dtype=np.float64)
    m = len(c)
    bull = np.zeros(m, dtype=bool)
    bear = np.zeros(m, dtype=bool)
    for t in range(1, m):
        body = c[t] - o[t]
        pbody = c[t - 1] - o[t - 1]
        rng = h[t] - l[t]
        # engulfing
        if body > 0 and pbody < 0 and c[t] > o[t - 1] and o[t] < c[t - 1]:
            bull[t] = True
        if body < 0 and pbody > 0 and c[t] < o[t - 1] and o[t] > c[t - 1]:
            bear[t] = True
        # pin bar: long wick, small body
        if rng > 0:
            up_wick = h[t] - max(o[t], c[t])
            dn_wick = min(o[t], c[t]) - l[t]
            ab = abs(body)
            if up_wick >= 2.0 * ab and up_wick >= 0.6 * rng:
                bear[t] = True
            if dn_wick >= 2.0 * ab and dn_wick >= 0.6 * rng:
                bull[t] = True
    return bull, bear


def session_vwap(high, low, close, volume, index) -> np.ndarray:
    """Session-anchored VWAP (resets each UTC day)."""
    h = np.asarray(high, dtype=np.float64)
    l = np.asarray(low, dtype=np.float64)
    c = np.asarray(close, dtype=np.float64)
    v = np.asarray(volume, dtype=np.float64)
    typical = (h + l + c) / 3.0
    pv = typical * v
    out = np.full(len(c), np.nan, dtype=np.float64)
    idx = pd.DatetimeIndex(index)
    cum_pv = np.zeros(len(c))
    cum_v = np.zeros(len(c))
    day = idx.date
    last_day = None
    for t in range(len(c)):
        if day[t] != last_day:
            cum_pv[t] = pv[t]
            cum_v[t] = v[t]
            last_day = day[t]
        else:
            cum_pv[t] = cum_pv[t - 1] + pv[t]
            cum_v[t] = cum_v[t - 1] + v[t]
        out[t] = cum_pv[t] / cum_v[t] if cum_v[t] > 0 else typical[t]
    return out
