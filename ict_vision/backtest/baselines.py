"""Two controls. Without them a backtest is an anecdote.

1. RIGID ICT -- the thing everybody writes first and the thing the brief
   explicitly complains about: three-bar fractals, body ratio > 65%, gap
   bigger than half an ATR, entries only inside the 10:00-11:00 Silver Bullet
   hour, entry at the 50% consequent encroachment, stop five points past the
   wick, fixed 2R target.  Every one of those numbers is asserted.

2. RANDOM CONTROL -- the same number of trades, at random times, with random
   direction, but with the stop/target geometry *drawn from the engine's own
   trades*.  This separates two very different questions: "does the model
   select better than a coin flip?" and "is the geometry+cost structure
   survivable at all?"
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def atr(bars, n: int = 14) -> np.ndarray:
    tr = np.maximum(
        bars.h[1:] - bars.l[1:],
        np.maximum(
            np.abs(bars.h[1:] - bars.c[:-1]),
            np.abs(bars.l[1:] - bars.c[:-1]),
        ),
    )
    tr = np.r_[bars.h[0] - bars.l[0], tr]
    return pd.Series(tr).rolling(n, min_periods=1).mean().to_numpy()


def fractal_swings(bars) -> tuple[np.ndarray, np.ndarray]:
    """The textbook three-bar fractal. No volatility normalisation anywhere."""
    n = bars.n
    hi = np.zeros(n, bool)
    lo = np.zeros(n, bool)
    h, l = bars.h, bars.l
    hi[1:-1] = (h[1:-1] > h[:-2]) & (h[1:-1] > h[2:])
    lo[1:-1] = (l[1:-1] < l[:-2]) & (l[1:-1] < l[2:])
    return hi, lo


def rigid_ict(bars, bars1, m1_a, m1_b, tod, cfg=None, start=4000, one_at_a_time=True):
    n = bars.n
    A = atr(bars, 14)
    fhi, flo = fractal_swings(bars)
    o, h, l, c = bars.o, bars.h, bars.l, bars.c
    body = np.abs(c - o)
    rng = np.maximum(h - l, 1e-12)
    body_ratio = body / rng
    last_hi = np.full(n, np.nan)
    last_lo = np.full(n, np.nan)
    cur_hi = np.nan
    cur_lo = np.nan
    for i in range(1, n - 1):
        if fhi[i]:
            cur_hi = h[i]
        if flo[i]:
            cur_lo = l[i]
        last_hi[i + 1] = cur_hi
        last_lo[i + 1] = cur_lo

    trades = []
    pending = None
    for t in range(start, n):
        # ---- fills
        if pending is not None:
            a, b = int(m1_a[t]), int(m1_b[t])
            oo, hh, ll = bars1.o[a:b], bars1.h[a:b], bars1.l[a:b]
            filled = False
            for j in range(len(oo)):
                d = pending[0]
                if d > 0 and ll[j] <= pending[3]:
                    trades.append(-1.0); pending = None; filled = True; break
                if d < 0 and hh[j] >= pending[3]:
                    trades.append(-1.0); pending = None; filled = True; break
                if ll[j] <= pending[1] <= hh[j]:
                    entry = min(oo[j], pending[1]) if d > 0 else max(oo[j], pending[1])
                    risk = abs(entry - pending[3])
                    tgt = entry + d * 2.0 * risk
                    stop = pending[3]
                    res = None
                    end = min(n, t + 288)
                    for k in range(t, end):
                        if d > 0 and l[k] <= stop:
                            res = -1.0; break
                        if d < 0 and h[k] >= stop:
                            res = -1.0; break
                        if d > 0 and h[k] >= tgt:
                            res = 2.0; break
                        if d < 0 and l[k] <= tgt:
                            res = 2.0; break
                    if res is None:
                        res = (c[end - 1] - entry) * d / max(risk, 1e-9)
                    cost = (2 * 1.0 + 0.5) / max(risk, 1e-9)
                    trades.append(res - cost)
                    pending = None
                    filled = True
                    break
            if pending is not None and t - pending[4] > 6:
                pending = None
        if pending is not None:
            continue
        # ---- signal: inside one of the three canonical killzones
        if not ((2 * 60 <= tod[t] < 5 * 60)
                or (8 * 60 + 30 <= tod[t] < 11 * 60)
                or (13 * 60 + 30 <= tod[t] < 16 * 60)):
            continue
        # displacement candle
        if body_ratio[t] < 0.65 or body[t] < 1.0 * A[t]:
            continue
        d = 1 if c[t] > o[t] else -1
        # a liquidity sweep on the other side within 30 bars
        lvl = last_lo[t - 1] if d > 0 else last_hi[t - 1]
        if not np.isfinite(lvl):
            continue
        swept = False
        sweep_px = lvl
        for k in range(max(0, t - 30), t):
            if d > 0 and l[k] < lvl and c[k] > lvl:
                swept = True
                sweep_px = min(sweep_px, l[k])
            if d < 0 and h[k] > lvl and c[k] < lvl:
                swept = True
                sweep_px = max(sweep_px, h[k])
        if not swept:
            continue
        # fair value gap in the direction, bigger than half an ATR
        if t < 2:
            continue
        gap_top = l[t] if d > 0 else l[t - 2]
        gap_bot = h[t - 2] if d > 0 else h[t]
        if d > 0 and not (l[t] > h[t - 2]):
            continue
        if d < 0 and not (h[t] < l[t - 2]):
            continue
        if (gap_top - gap_bot) < 0.5 * A[t]:
            continue
        entry = 0.5 * (gap_top + gap_bot)
        stop = sweep_px - 5.0 if d > 0 else sweep_px + 5.0
        if abs(entry - stop) <= 0:
            continue
        pending = (d, entry, 0.0, stop, t)
    return np.array(trades, float)


def random_control(bars, m1_a, m1_b, n_trades: int, risk_sig: float = 1.5,
                   rr: float = 2.0, hold: int = 48, start: int = 4000, seed: int = 3):
    """Coin-flip entries with the SAME cost structure and a sane geometry.

    This isolates the two questions that matter: how much does the cost model
    drag, and does the engine's *selection* beat a coin flip.
    """
    rng = np.random.default_rng(seed)
    n = bars.n
    idx = rng.integers(start, n - 200, size=n_trades)
    out = []
    for t in idx:
        t = int(t)
        d = 1 if rng.random() < 0.5 else -1
        sp = risk_sig * float(np.median(np.abs(np.diff(bars.c[max(0, t - 60):t + 1]))) or 1e-9)
        sp = risk_sig * _local_sigma(bars, t)
        entry = bars.c[t]
        stop = entry - d * sp
        tgt = entry + d * sp * rr
        end = min(n - 1, t + hold)
        res = None
        for k in range(t + 1, end + 1):
            if d > 0 and bars.l[k] <= stop:
                res = -1.0; break
            if d < 0 and bars.h[k] >= stop:
                res = -1.0; break
            if d > 0 and bars.h[k] >= tgt:
                res = rr; break
            if d < 0 and bars.l[k] <= tgt:
                res = rr; break
        if res is None:
            res = (bars.c[end] - entry) * d / max(sp, 1e-9)
        out.append(res - (2 * 1.0 + 0.5) / max(sp, 1e-9))
    return np.array(out, float)


def _local_sigma(bars, t: int, win: int = 60) -> float:
    a = max(0, t - win)
    r = np.abs(np.diff(bars.c[a:t + 1]))
    return float(np.median(r)) / 0.7979 if len(r) > 5 else float(max(bars.c[t] * 1e-4, 1e-9))


def time_matched_control(bars, trades, seed: int = 7):
    """The engine's exact entry level and risk distance, COIN-FLIP direction.

    This is the purest test of whether the engine knows which WAY the market is
    going.  Everything is held fixed - the bar, the entry price, the stop
    distance, the 2R objective - and only the sign is randomised.

    We deliberately do NOT mirror the stop about the entry.  An ICT entry sits
    ~90% deep in the leg, so mirroring puts the stop about 0.1 leg away and
    every trade stops out instantly; that is geometry, not evidence.  Instead we
    keep the entry point and the stop DISTANCE and flip only the sign.
    """
    rng = np.random.default_rng(seed)
    out = []
    for tr in trades:
        t = tr.t_signal
        risk = abs(tr.entry - tr.stop0)
        if risk <= 0:
            continue
        d = 1 if rng.random() < 0.5 else -1
        entry = tr.entry
        stop = entry - d * risk
        tgt = entry + d * 2.0 * risk
        end = min(bars.n - 1, t + 288)
        res = None
        for k in range(t + 1, end + 1):
            if d > 0 and bars.l[k] <= stop:
                res = -1.0; break
            if d < 0 and bars.h[k] >= stop:
                res = -1.0; break
            if d > 0 and bars.h[k] >= tgt:
                res = 2.0; break
            if d < 0 and bars.l[k] <= tgt:
                res = 2.0; break
        if res is None:
            res = (bars.c[end] - entry) * d / risk
        out.append(res - (2 * 1.0 + 0.5) / risk)
    return np.array(out, float)


def market_entry_ablation(bars, trades):
    """Same moment, same direction, same risk - but enter at MARKET on the
    signal close instead of waiting for the retracement limit.

    Isolates the value of the OTE entry level itself.  If this beats the
    engine, the whole retracement/OTE apparatus is hurting rather than helping.
    """
    out = []
    for tr in trades:
        t = tr.t_signal
        d = tr.direction
        entry = bars.c[t]
        risk = abs(entry - tr.stop0)
        if risk <= 0:
            continue
        tgt = entry + d * 2.0 * risk
        end = min(bars.n - 1, t + 288)
        res = None
        for k in range(t + 1, end + 1):
            if d > 0 and bars.l[k] <= tr.stop0:
                res = -1.0; break
            if d < 0 and bars.h[k] >= tr.stop0:
                res = -1.0; break
            if d > 0 and bars.h[k] >= tgt:
                res = 2.0; break
            if d < 0 and bars.l[k] <= tgt:
                res = 2.0; break
        if res is None:
            res = (bars.c[end] - entry) * d / risk
        out.append(res - (2 * 1.0 + 0.5) / risk)
    return np.array(out, float)
