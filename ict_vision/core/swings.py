"""Adaptive multi-scale swing structure.

A "swing point" is not `high[i] > high[i-1] and high[i] > high[i+1]`.  That
three-bar fractal is a hard-coded number (why three?) and it fires on noise.

Here a swing is a *reversal of at least k local sigmas*, where k itself is not
chosen by us: we run the detector at several k simultaneously and let the
market tell us, causally, which k's swings behave like real structure.

How the market tells us (`structuality`):

    when price CLOSES beyond a swing of scale k, does it then
      (a) stay beyond it (persistence), and
      (b) travel cleanly (efficiency = |net move| / total path travelled)?

`quality = persistence x efficiency` is dimensionless, in [0,1], and does not
grow with k -- so it compares scales fairly.  A swing size whose breaks are
followed by chop scores ~0.1; a swing size whose breaks are followed by real
delivery scores ~0.5.  We then trust, at each instant, the scales that are
currently scoring well, with exponential-weight smoothing and shrinkage
toward a neutral prior while a scale is still thinly sampled.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Pivots:
    """Swing points.

    idx  : bar where the extreme printed
    conf : bar at which the reversal was CONFIRMED (the pivot is unknowable
           before `conf`; every consumer must use `conf`, never `idx`)
    px   : extreme price
    kind : +1 swing high, -1 swing low
    """

    idx: np.ndarray
    conf: np.ndarray
    px: np.ndarray
    kind: np.ndarray

    def __len__(self) -> int:
        return len(self.px)


def zigzag(h: np.ndarray, l: np.ndarray, thr: np.ndarray, chunk: int = 2048) -> Pivots:
    """Time-varying-threshold zigzag, chunk-vectorised.

    An up-leg ends at the first bar j where  low[j] <= max(h[i..j]) - thr[j];
    the pivot emitted is the running maximum, not j.  Symmetric for down-legs.
    """
    n = len(h)
    if n == 0:
        return Pivots(np.array([], int), np.array([], int), np.array([]), np.array([], np.int8))
    pi: list[int] = []
    pp: list[float] = []
    pk: list[int] = []
    pc: list[int] = []

    i = 0
    ex_i = 0            # index of the running extreme
    ex_p = float(h[0])  # running max on an up-leg, running min on a down-leg
    direction = 1
    while i < n:
        j_end = min(i + chunk, n)
        hh = h[i:j_end]
        ll = l[i:j_end]
        tt = thr[i:j_end]
        if direction == 1:
            cm = np.maximum.accumulate(hh)
            cond = (ll + tt) <= np.maximum(cm, ex_p)
            hit = np.flatnonzero(cond)
            if hit.size:
                j = i + int(hit[0])
                off = j - i + 1
                Mj = float(np.maximum.accumulate(hh[:off])[-1])
                if Mj >= ex_p:
                    k = i + int(np.argmax(hh[:off] == Mj))
                else:
                    k, Mj = ex_i, ex_p
                pi.append(k)
                pp.append(Mj)
                pk.append(1)
                pc.append(j)
                direction = -1
                i = max(i, k + 1)
                ex_i = j
                ex_p = float(l[j])          # down-leg running min starts here
                continue
            if cm[-1] > ex_p:
                k = i + int(np.argmax(hh == cm[-1]))
                ex_p = float(cm[-1])
                ex_i = k
            i = j_end
        else:
            cm = np.minimum.accumulate(ll)
            cond = (hh - tt) >= np.minimum(cm, ex_p)
            hit = np.flatnonzero(cond)
            if hit.size:
                j = i + int(hit[0])
                off = j - i + 1
                Mj = float(np.minimum.accumulate(ll[:off])[-1])
                if Mj <= ex_p:
                    k = i + int(np.argmax(ll[:off] == Mj))
                else:
                    k, Mj = ex_i, ex_p
                pi.append(k)
                pp.append(Mj)
                pk.append(-1)
                pc.append(j)
                direction = 1
                i = max(i, k + 1)
                ex_i = j
                ex_p = float(h[j])
                continue
            if cm[-1] < ex_p:
                k = i + int(np.argmax(ll == cm[-1]))
                ex_p = float(cm[-1])
                ex_i = k
            i = j_end
    return Pivots(
        np.array(pi, dtype=np.int64),
        np.array(pc, dtype=np.int64),
        np.array(pp, dtype=float),
        np.array(pk, dtype=np.int8),
    )


def pivot_state(piv: Pivots, n: int) -> dict:
    """Per-bar state, filled from the CONFIRMATION bar (never earlier)."""
    out = {}
    for name, kind in (("hi", 1), ("lo", -1)):
        sel = piv.kind == kind
        conf = piv.conf[sel]
        px = piv.px[sel]
        idx = piv.idx[sel]
        pos = np.searchsorted(conf, np.arange(n), side="right") - 1
        ok = pos >= 0
        p = np.clip(pos, 0, None)
        out[f"last_{name}"] = np.where(ok, px[p], np.nan)
        out[f"last_{name}_i"] = np.where(ok, idx[p], -1)
    age = np.arange(n)
    out["hi_age"] = np.where(out["last_hi_i"] >= 0, age - out["last_hi_i"], 1e9)
    out["lo_age"] = np.where(out["last_lo_i"] >= 0, age - out["last_lo_i"], 1e9)

    conf = piv.conf
    order = np.argsort(conf, kind="stable")
    conf_s = conf[order]
    pos = np.searchsorted(conf_s, np.arange(n), side="right") - 1
    ok = pos >= 0
    p = np.clip(pos, 0, None)
    out["last_kind"] = np.where(ok, piv.kind[order][p], 0).astype(np.int8)
    out["last_px"] = np.where(ok, piv.px[order][p], np.nan)
    out["last_idx"] = np.where(ok, piv.idx[order][p], -1)
    # a confirmed swing HIGH means the leg that just finished was an up-leg
    out["trend"] = np.where(ok, -out["last_kind"], 0).astype(np.int8)
    return out


def _first_cross(c: np.ndarray, start: int, level: float, up: bool, max_look: int) -> int:
    end = min(len(c), start + max_look)
    if end <= start:
        return -1
    seg = c[start:end]
    hit = np.flatnonzero(seg > level) if up else np.flatnonzero(seg < level)
    return -1 if hit.size == 0 else start + int(hit[0])


def structuality(b, piv: Pivots, look: int = 400, horizon: int = 40, max_events: int = 40000):
    """For every pivot: once it broke, how clean was the delivery afterwards?

    Returns (event_time, quality).  `event_time` is the bar at which the
    measurement became knowable (break bar + horizon); a consumer standing at
    bar t may only use events with event_time <= t.
    """
    c, h, l = b.c, b.h, b.l
    n = len(c)
    step = 1 if len(piv) <= max_events else int(np.ceil(len(piv) / max_events))
    times: list[int] = []
    quals: list[float] = []
    for k in range(0, len(piv), step):
        j = _first_cross(
            c, int(piv.conf[k]) + 1, float(piv.px[k]), up=(piv.kind[k] > 0), max_look=look
        )
        if j < 0 or j + horizon >= n:
            continue
        lvl = float(piv.px[k])
        seg_h = h[j : j + horizon + 1]
        seg_l = l[j : j + horizon + 1]
        seg_c = c[j : j + horizon + 1]
        path = float(np.abs(np.diff(seg_c)).sum())
        if piv.kind[k] > 0:
            net = float(seg_h.max()) - lvl
            beyond = float((seg_c > lvl).mean())
        else:
            net = lvl - float(seg_l.min())
            beyond = float((seg_c < lvl).mean())
        if path <= 0:
            continue
        eff = float(np.clip(net / path, 0.0, 1.0))
        times.append(j + horizon)
        quals.append(beyond * eff)
    if not times:
        return np.array([], int), np.array([], float)
    return np.array(times, int), np.array(quals, float)


def ewma_score_at(
    times: np.ndarray,
    vals: np.ndarray,
    n: int,
    halflife: float,
    prior: float,
    n0: float,
):
    """Causal exponentially-weighted mean with shrinkage to `prior`.

    Returns (score, ess) on the bar grid.  ess = effective sample size, which
    is what lets the caller know how much to trust a scale.
    """
    score = np.full(n, float(prior))
    ess = np.zeros(n)
    if len(times) == 0:
        return score, ess
    order = np.argsort(times, kind="stable")
    times = times[order]
    vals = vals[order].astype(float)
    a = 1.0 - np.exp(-np.log(2.0) / max(halflife, 1.0))
    acc = float(prior)
    w = 0.0
    p = 0
    scale = (2.0 - a) / a
    for t in range(n):
        while p < len(times) and times[p] <= t:
            acc += a * (vals[p] - acc)
            w += a * (1.0 - w)
            p += 1
        e = w * scale
        score[t] = (e * acc + n0 * prior) / (e + n0)
        ess[t] = e
    return score, ess


def run_start(mask: np.ndarray) -> np.ndarray:
    """For each bar, the index at which its current run of equal booleans began."""
    n = len(mask)
    chg = np.r_[0, np.flatnonzero(mask[1:] != mask[:-1]) + 1]
    starts = np.repeat(chg, np.diff(np.r_[chg, n]))
    return np.where(mask, starts, np.arange(n))


def cisd_levels(b) -> dict:
    """Change In State Of Delivery reference levels.

    After a run of down-close candles delivers price into a low, the bullish
    CISD reference is the OPEN of the FIRST candle of that delivery run; a
    body close above it is the earliest mechanical proof that delivery has
    flipped.  (No size filter here -- size gets scored, not thresholded.)
    """
    dn = b.c < b.o
    up = b.c > b.o
    return {"dn_start": run_start(dn), "up_start": run_start(up), "dn": dn, "up": up}
