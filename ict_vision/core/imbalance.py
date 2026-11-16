"""Fair value gaps, volume imbalances and order blocks.

A fair value gap is the cleanest object in the whole ICT toolbox because it is
a *geometric* fact, not an opinion: on three consecutive bars the wick of bar
t-2 and the wick of bar t do not overlap, so no trade occurred in between and
the move was delivered by orders on one side only.

What IS an opinion is "how big does a gap have to be before it matters", and
that is exactly the number nobody can justify.  Here the gap is measured in
sigmas and scored against the *causal trailing distribution of gap sizes*:
a gap in the top decile of what this instrument has actually been producing
lately scores ~1, a gap at the median scores ~0.5, a sub-noise gap scores ~0.
Nothing is rejected; small gaps simply carry little evidence.

Consequent Encroachment (50% of the gap) is kept as the reference price, but
note it is used as a *geometric midpoint*, never as a pass/fail gate.

Lifecycle (filled / partially filled / untouched) is computed by scanning the
actual bars forward from creation, so it is always the truth as of that bar.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class FairValueGaps:
    t: np.ndarray        # creation bar (the third candle)
    direction: np.ndarray  # +1 bullish gap (price gapped up), -1 bearish
    top: np.ndarray
    bot: np.ndarray
    size: np.ndarray
    size_sig: np.ndarray  # size / (sigma * price) at creation
    ce: np.ndarray        # consequent encroachment = geometric midpoint
    body_gap: np.ndarray  # 1 if the BODIES also do not overlap (a "volume imbalance")


def detect_fvg(bars, sigma: np.ndarray) -> FairValueGaps:
    h, l, o, c = bars.h, bars.l, bars.o, bars.c
    n = bars.n
    if n < 3:
        z = np.zeros(0)
        return FairValueGaps(z, z, z, z, z, z, z, z)
    t = np.arange(2, n)
    bull = l[2:] > h[:-2]
    bear = h[2:] < l[:-2]
    m = bull | bear
    t = t[m]
    bull = bull[m]
    bear = bear[m]
    direction = np.where(bull, 1, -1).astype(np.int8)
    top = np.where(bull, l[2:][m], l[:-2][m])
    bot = np.where(bull, h[:-2][m], h[2:][m])
    size = top - bot
    sig = sigma[t] * c[t]
    body_top = np.where(bull, np.minimum(o, c)[2:][m], np.maximum(o, c)[:-2][m])
    body_bot = np.where(bull, np.maximum(o, c)[:-2][m], np.minimum(o, c)[2:][m])
    body_gap = (body_top > body_bot).astype(np.int8)
    return FairValueGaps(
        t=t.astype(np.int64),
        direction=direction,
        top=top,
        bot=bot,
        size=size,
        size_sig=size / np.maximum(sig, 1e-12),
        ce=0.5 * (top + bot),
        body_gap=body_gap,
    )


def fvg_lifecycle(bars, fvg: FairValueGaps, idx: int, horizon: int = 576,
                  upto: int | None = None):
    """For gap #idx, scan forward from its creation bar.

    `upto` caps the scan at a given bar so the answer is always 'as of now'.
    Without it the function happily reports whether the gap survives, which is
    the future.

    Returns (touch_t, fill_t, max_fill_fraction) where
      touch_t : first bar that traded INTO the gap (-1 if never)
      fill_t  : first bar that traded all the way THROUGH it
      frac    : deepest penetration reached, 0..1 (1 = fully filled)
    """
    t = int(fvg.t[idx])
    top = float(fvg.top[idx])
    bot = float(fvg.bot[idx])
    span = max(top - bot, 1e-12)
    end = min(bars.n, t + 1 + horizon)
    if upto is not None:
        end = min(end, max(upto + 1, t + 1))
    if end <= t + 1:
        return -1, -1, 0.0
    if fvg.direction[idx] > 0:
        seg = bars.l[t + 1 : end]
        # penetrating downward: enters at < top, fully filled at <= bot
        ent = np.flatnonzero(seg < top)
        ful = np.flatnonzero(seg <= bot)
        deep = (top - seg.min()) / span if len(seg) else 0.0
    else:
        seg = bars.h[t + 1 : end]
        ent = np.flatnonzero(seg > bot)
        ful = np.flatnonzero(seg >= top)
        deep = (seg.max() - bot) / span if len(seg) else 0.0
    touch_t = int(t + 1 + ent[0]) if ent.size else -1
    fill_t = int(t + 1 + ful[0]) if ful.size else -1
    return touch_t, fill_t, float(np.clip(deep, 0.0, 1.0))


def gap_size_quantile(fvg: FairValueGaps, i: int, window: int = 2000) -> float:
    """Where does gap #i sit in the trailing distribution of gap sizes?

    Causal: only gaps created at or before bar fvg.t[i] are used.  Returns a
    value in (0,1).  This is the continuous replacement for
    `if gap > 1.5 * ATR`.
    """
    t = int(fvg.t[i])
    j = np.searchsorted(fvg.t, t, side="right")
    a = max(0, j - window)
    ref = fvg.size_sig[a:j]
    if len(ref) < 30:
        return 0.5
    return float((ref < fvg.size_sig[i]).mean())


def find_order_block(bars, t_start: int, direction: int, max_look: int = 40):
    """The last candle of the OPPOSITE colour before an impulsive move.

    Bullish displacement -> the last down-close candle before it: its range
    (or ICT's "mean threshold", the 50% of its body, which is again a
    geometric midpoint) is the order block.  Returns (index, open, close) or
    None.
    """
    n = bars.n
    a = max(0, t_start - max_look)
    for k in range(t_start, a, -1):
        col = 1 if bars.c[k] > bars.o[k] else (-1 if bars.c[k] < bars.o[k] else 0)
        if col == -direction and col != 0:
            return k, float(bars.o[k]), float(bars.c[k])
    return None


def candle_quality(bars, i: int) -> dict:
    """Body-to-range ratio and close position -- the ICT 'displacement candle'
    descriptors, kept continuous (no 65% cut-off)."""
    rng = max(bars.h[i] - bars.l[i], 1e-12)
    body = abs(bars.c[i] - bars.o[i])
    up = bars.c[i] >= bars.o[i]
    upper = bars.h[i] - max(bars.c[i], bars.o[i])
    lower = min(bars.c[i], bars.o[i]) - bars.l[i]
    return {
        "body_ratio": float(body / rng),
        "close_pos": float((bars.c[i] - bars.l[i]) / rng),
        "upper_wick": float(upper / rng),
        "lower_wick": float(lower / rng),
        "dir": 1 if up else -1,
    }
