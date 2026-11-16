"""Liquidity: where the resting orders actually are, and when they are taken.

ICT says stops rest above obvious highs and below obvious lows and that price
is delivered to them.  Most implementations look for "equal highs within N
pips" -- N being a number somebody made up.

Here a pool is a *cluster in log-price at the market's own resolution*: two
swing points belong to the same pool when they are within `r` of each other,
where `r = POOL_RADIUS_SIGMA * local_sigma * price`.  Nothing is denominated
in pips or points, so the same code behaves identically on NDX at 8,000 in
2020 and on NDX at 29,000 in 2026.

Pool strength is an exponentially decaying sum of the evidence that the market
has treated the level as a reference (swing weight, touches, recency), and a
pool DIES the instant it is swept -- its orders have been consumed, which is
the entire point of the concept.

Sweep detection is deliberately not `high > level`:
    pierce   : price trades beyond the level by more than SWEEP_EPS sigma
    confirm  : a later bar CLOSEs back on the near side
    consumed : the pool is then retired from the book
and the sweep's quality is a continuous function of the overshoot (in sigmas),
of how quickly price rejected, and of how much of the move was wick.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

POOL_RADIUS_SIGMA = 0.35
SWEEP_EPS_SIGMA = 0.12
MAX_PIERCE_BARS = 36
POOL_TAU_BARS = 576.0
SCALE_WEIGHT = {2.0: 0.6, 4.0: 1.0, 8.0: 1.3, 16.0: 1.0}
BUCKET_SIGMA = 0.35


@dataclass
class SweepEvent:
    t: int
    pierce_t: int
    kind: int          # +1 buy-side taken (a high was raided), -1 sell-side
    level: float
    overshoot_sig: float
    extreme: float
    bars: int
    strength: float
    pool_id: int
    wick_ratio: float = 0.0


class LiquidityBook:
    """Pool store with an O(1) bucket index in price space."""

    def __init__(
        self,
        bucket: float,
        radius_sigma: float = POOL_RADIUS_SIGMA,
        tau: float = POOL_TAU_BARS,
        cap: int = 4096,
    ):
        self.bs = max(bucket, 1e-9)
        self.radius_sigma = radius_sigma
        self.tau = tau
        self.cap = cap
        self.n = 0
        self.px = np.zeros(cap)
        self.kind = np.zeros(cap, np.int8)
        self.w = np.zeros(cap)
        self.birth = np.zeros(cap, np.int64)
        self.last = np.zeros(cap, np.int64)
        self.touches = np.zeros(cap)
        self.alive = np.zeros(cap, bool)
        self.pierced = np.zeros(cap, bool)
        self.pierce_t = np.zeros(cap, np.int64)
        self.pierce_ext = np.zeros(cap)
        self.src = np.zeros(cap, np.int8)
        self.buckets: dict[int, list[int]] = {}

    def _grow(self):
        c = self.cap * 2
        for f in ("px", "kind", "w", "birth", "last", "touches", "alive",
                  "pierced", "pierce_t", "pierce_ext", "src"):
            a = getattr(self, f)
            na = np.zeros(c, dtype=a.dtype) if a.dtype != bool else np.zeros(c, bool)
            na[: self.n] = a
            setattr(self, f, na)
        self.cap = c

    def _bk(self, px: float) -> int:
        return int(math.floor(px / self.bs))

    def add(self, px: float, kind: int, w: float, t: int, src: int = 0) -> int:
        if self.n >= self.cap:
            self._grow()
        i = self.n
        self.px[i] = px
        self.kind[i] = kind
        self.w[i] = w
        self.birth[i] = t
        self.last[i] = t
        self.touches[i] = 1.0
        self.alive[i] = True
        self.pierced[i] = False
        self.pierce_t[i] = -1
        self.pierce_ext[i] = px
        self.src[i] = src
        self.n += 1
        self.buckets.setdefault(self._bk(px), []).append(i)
        return i

    def merge_into(self, i: int, px: float, w: float, t: int) -> None:
        tot = self.w[i] + w
        newpx = (self.px[i] * self.w[i] + px * w) / tot
        self.px[i] = newpx
        self.w[i] = tot
        self.last[i] = t
        self.touches[i] += 1.0

    def candidates(self, lo: float, hi: float, span_buckets: int = 3) -> np.ndarray:
        b0 = self._bk(lo)
        b1 = self._bk(hi)
        # A wide price window spans many buckets; that is normal when we are
        # asking for "every pool within 12 sigmas".  The only guard needed is
        # against a pathological range.
        if b1 - b0 > 20000:
            return np.zeros(0, np.int64)
        ids: list[int] = []
        for b in range(b0, b1 + 1):
            ids.extend(self.buckets.get(b, ()))
        if not ids:
            return np.zeros(0, np.int64)
        return np.array(ids, dtype=np.int64)

    def retire(self, i: int) -> None:
        self.alive[i] = False

    def strength(self, i: int, t: int) -> float:
        age = max(t - self.last[i], 0)
        return float(self.w[i] * np.exp(-age / self.tau) * (1.0 + 0.35 * np.log1p(self.touches[i])))

    def compaction(self) -> None:
        keep = np.flatnonzero(self.alive[: self.n])
        if len(keep) == self.n:
            return
        for f in ("px", "kind", "w", "birth", "last", "touches", "alive",
                  "pierced", "pierce_t", "pierce_ext", "src"):
            a = getattr(self, f)
            na = np.zeros(a.shape[0], dtype=a.dtype)      # keep the capacity
            na[: len(keep)] = a[keep]
            setattr(self, f, na)
        self.n = len(keep)
        self.buckets = {}
        for i in range(self.n):
            self.buckets.setdefault(self._bk(self.px[i]), []).append(i)

    def live_levels(self, t: int, lo: float, hi: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        ids = self.candidates(lo, hi)
        if len(ids) == 0:
            return np.zeros(0, int), np.zeros(0), np.zeros(0)
        ids = ids[self.alive[ids]]
        if len(ids) == 0:
            return np.zeros(0, int), np.zeros(0), np.zeros(0)
        return ids, self.px[ids], np.array([self.strength(int(i), t) for i in ids])



def build_pools(bars, pivots_by_scale: dict, sigma: np.ndarray, t_end: int | None = None,
                min_scale: float = 2.0, bucket_sigma: float = BUCKET_SIGMA) -> LiquidityBook:
    """Cluster swing points into pools, walking in causal (confirmation) order."""
    n = bars.n if t_end is None else t_end
    bs = float(np.median(sigma[:n] * bars.c[:n]) * bucket_sigma)
    book = LiquidityBook(bucket=bs)
    recs = []
    for k, piv in pivots_by_scale.items():
        if float(k) < min_scale:
            continue
        w0 = SCALE_WEIGHT.get(float(k), 1.0)
        conf = piv.conf
        for i in range(len(piv)):
            c0 = int(conf[i])
            if c0 >= n:
                continue
            recs.append((c0, float(piv.px[i]), int(piv.kind[i]), w0))
    recs.sort(key=lambda r: r[0])
    span = max(1, int(np.ceil(2.0 / bucket_sigma)) + 1)
    for t, px, kind, w0 in recs:
        r = POOL_RADIUS_SIGMA * sigma[t] * bars.c[t]
        ids = book.candidates(px - r, px + r, span_buckets=span)
        if len(ids):
            ids = ids[(book.kind[ids] == kind) & book.alive[ids]]
        if len(ids):
            wts = np.array([book.strength(int(i), t) for i in ids])
            book.merge_into(int(ids[int(np.argmax(wts))]), px, w0, t)
        else:
            book.add(px, kind, w0, t, src=0)
    return book


def session_levels(bars, day: np.ndarray) -> dict:
    """Previous-day / Asian / London / overnight reference levels, CAUSAL.

    These are the levels ICT explicitly teaches to mark.  Each one is only
    published from the bar at which it becomes knowable: the Asian range is
    knowable at 02:00 ET, the London range at 08:00 ET, the overnight range at
    the cash open, and the previous day's range at the start of the next
    trading day.
    """
    n = bars.n
    out = {k: np.full(n, np.nan) for k in ("pdh", "pdl", "pdc", "ash", "asl", "lonh", "lonl", "onh", "onl")}
    h, l, c = bars.h, bars.l, bars.c
    tod = (bars.idx.hour * 60 + bars.idx.minute).astype(np.int64)
    uniq = {}
    didx = np.empty(n, dtype=np.int64)
    for i, d in enumerate(day):
        if d not in uniq:
            uniq[d] = len(uniq)
        didx[i] = uniq[d]
    nd = len(uniq)
    dh = np.full(nd, np.nan); dl = np.full(nd, np.nan); dc = np.full(nd, np.nan)
    cur = -1
    day_h = day_l = day_c = np.nan
    ah = al = lnh = lnl = onh_ = onl_ = np.nan
    for i in range(n):
        d = int(didx[i])
        if d != cur:
            if cur >= 0:
                dh[cur] = day_h; dl[cur] = day_l; dc[cur] = day_c
            cur = d
            day_h = h[i]; day_l = l[i]; day_c = c[i]
            ah = al = lnh = lnl = onh_ = onl_ = np.nan
        day_h = max(day_h, h[i]); day_l = min(day_l, l[i]); day_c = c[i]
        m = int(tod[i])
        if m >= 18 * 60 or m < 2 * 60:
            ah = h[i] if not np.isfinite(ah) else max(ah, h[i])
            al = l[i] if not np.isfinite(al) else min(al, l[i])
        if 2 * 60 <= m < 8 * 60:
            lnh = h[i] if not np.isfinite(lnh) else max(lnh, h[i])
            lnl = l[i] if not np.isfinite(lnl) else min(lnl, l[i])
        if m >= 18 * 60 or m < 9 * 60 + 30:
            onh_ = h[i] if not np.isfinite(onh_) else max(onh_, h[i])
            onl_ = l[i] if not np.isfinite(onl_) else min(onl_, l[i])
        if m == 2 * 60:
            out["ash"][i] = ah; out["asl"][i] = al
        if m == 8 * 60:
            out["lonh"][i] = lnh; out["lonl"][i] = lnl
        if m == 9 * 60 + 30:
            out["onh"][i] = onh_; out["onl"][i] = onl_
        if d > 0:
            out["pdh"][i] = dh[d - 1]
            out["pdl"][i] = dl[d - 1]
            out["pdc"][i] = dc[d - 1]
    return out


def add_session_pools(book: LiquidityBook, bars, levels: dict, t0: int, w0: float = 1.4):
    """Publish PDH/PDL / Asian / London / overnight levels into the SAME book.

    They enter with a modest prior weight: they are widely watched, so they
    genuinely carry resting orders, but the prior is only a starting belief and
    the book's decay makes a stale level stop mattering after a couple of days.
    """
    n = bars.n
    keys = ("pdh", "pdl", "ash", "asl", "lonh", "lonl", "onh", "onl")
    prev = {k: np.nan for k in keys}
    for t in range(t0, n):
        for k in keys:
            v = levels[k][t]
            if np.isfinite(v) and not (np.isfinite(prev[k]) and abs(v - prev[k]) < 1e-12):
                kind = 1 if k.endswith("h") else -1
                book.add(float(v), kind, w0, t, src=1)
            prev[k] = v


def run_book(bars, book: LiquidityBook, sigma: np.ndarray, t0: int = 0,
             t1: int | None = None, compact_every: int = 20000) -> list[SweepEvent]:
    """Walk bars, maintain the book, emit confirmed sweeps (no look-ahead)."""
    n = bars.n if t1 is None else t1
    h, l, c = bars.h, bars.l, bars.c
    out: list[SweepEvent] = []
    span = max(2, int(np.ceil(2.0 / BUCKET_SIGMA)) + 2)
    for t in range(t0, n):
        r = SWEEP_EPS_SIGMA * sigma[t] * c[t]
        lo = min(l[t], c[t]) - 4.0 * r
        hi = max(h[t], c[t]) + 4.0 * r
        ids = book.candidates(lo, hi, span_buckets=span)
        if len(ids) == 0:
            continue
        ids = ids[book.alive[ids]]
        if len(ids) == 0:
            continue
        px = book.px[ids]
        knd = book.kind[ids]
        hh = h[t]
        ll = l[t]
        cc = c[t]
        for j in range(len(ids)):
            pid = int(ids[j])
            kind = int(knd[j])
            P = float(px[j])
            if kind > 0:
                if not book.pierced[pid]:
                    if hh > P + r:
                        book.pierced[pid] = True
                        book.pierce_t[pid] = t
                        book.pierce_ext[pid] = hh
                    elif ll <= P + r and ll >= P - r:
                        book.last[pid] = t
                        book.touches[pid] += 0.5
                else:
                    if hh > book.pierce_ext[pid]:
                        book.pierce_ext[pid] = hh
                    if cc < P:
                        ext = float(book.pierce_ext[pid])
                        rng = max(hh - ll, 1e-12)
                        wick = float((ext - max(cc, ll)) / rng)
                        out.append(SweepEvent(
                            t=t, pierce_t=int(book.pierce_t[pid]), kind=1, level=P,
                            overshoot_sig=float((ext - P) / (sigma[t] * c[t])),
                            extreme=ext, bars=int(t - book.pierce_t[pid]),
                            strength=book.strength(pid, t), pool_id=pid,
                            wick_ratio=float(np.clip(wick, 0, 1))))
                        book.retire(pid)
                    elif t - book.pierce_t[pid] > MAX_PIERCE_BARS:
                        book.retire(pid)
            else:
                if not book.pierced[pid]:
                    if ll < P - r:
                        book.pierced[pid] = True
                        book.pierce_t[pid] = t
                        book.pierce_ext[pid] = ll
                    elif hh >= P - r and hh <= P + r:
                        book.last[pid] = t
                        book.touches[pid] += 0.5
                else:
                    if ll < book.pierce_ext[pid]:
                        book.pierce_ext[pid] = ll
                    if cc > P:
                        ext = float(book.pierce_ext[pid])
                        rng = max(hh - ll, 1e-12)
                        wick = float((min(cc, hh) - ext) / rng)
                        out.append(SweepEvent(
                            t=t, pierce_t=int(book.pierce_t[pid]), kind=-1, level=P,
                            overshoot_sig=float((P - ext) / (sigma[t] * c[t])),
                            extreme=ext, bars=int(t - book.pierce_t[pid]),
                            strength=book.strength(pid, t), pool_id=pid,
                            wick_ratio=float(np.clip(wick, 0, 1))))
                        book.retire(pid)
                    elif t - book.pierce_t[pid] > MAX_PIERCE_BARS:
                        book.retire(pid)
        if compact_every and (t - t0) % compact_every == compact_every - 1:
            book.compaction()
    return out
