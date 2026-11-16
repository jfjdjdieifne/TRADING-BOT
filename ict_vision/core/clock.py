"""Time: the killzones are discovered, not asserted.

ICT gives fixed clock windows: London 02:00-05:00 ET, NY AM 08:30-11:00, the
Silver Bullet hours 03:00-04:00 / 10:00-11:00 / 14:00-15:00, plus eight
20-minute "macro" windows.  A programmer is entitled to ask: why 10:00?  Why
does a window end at 11:00 and not 11:20?  Where do the 8 macros come from?

We take the ICT windows seriously -- as a HYPOTHESIS.  This module measures,
causally and continuously, what the clock actually does to this instrument:

    for every bar, look H bars ahead and record
        delivery   = |net move| / (sigma * sqrt(H))      -- did it MOVE?
        efficiency = |net move| / total path travelled   -- was it CLEAN?

Both are dimensionless.  Both are only knowable at t+H, so they are stamped
into the time-of-day bucket of bar t at time t+H and consumed from then on --
never before.  Each bucket carries an exponentially weighted average, so the
profile tracks the market as its schedule drifts (it does: the profile for
2021 is not the profile for 2026).

`discover_windows()` then segments the live profile into contiguous high
delivery regions with no fixed number of hours, no fixed start minute, and no
fixed count of windows.  The report prints them next to ICT's list so you can
see how much of the folklore survives contact with the data.

Two design points that matter:

 * the profile is a FEATURE, never a gate.  A setup at a quiet hour is not
   rejected; it simply carries less evidence, and the engine says so.
 * the day-of-week dimension is kept separate, because the weekend gap
   genuinely changes the accumulation profile.
"""

from __future__ import annotations

import numpy as np


class DeliveryClock:
    """Causal, adaptive time-of-day delivery profile."""

    def __init__(self, n_buckets: int = 96, halflife_days: float = 120.0, horizon: int = 12):
        self.nb = n_buckets
        self.bucket_min = 24 * 60 / n_buckets
        self.horizon = horizon
        self.hl = halflife_days
        self.deliv = np.full(n_buckets, 1.0)
        self.effic = np.full(n_buckets, 0.25)
        self.n = np.zeros(n_buckets)
        self.dow_deliv = np.full((7, n_buckets), 1.0)
        self.dow_n = np.zeros((7, n_buckets))

    def bucket_of(self, minute_of_day: int) -> int:
        return int(minute_of_day // self.bucket_min) % self.nb

    def feed(self, minute_of_day: np.ndarray, dow: np.ndarray, c: np.ndarray,
             sigma: np.ndarray, t0: int, t1: int) -> None:
        """Advance the profile using measurements made at t and known at t+H."""
        H = self.horizon
        a = 1.0 - np.exp(-np.log(2.0) / max(self.hl, 1.0))
        for t in range(t0, t1):
            if t + H >= len(c):
                break
            d = c[t + H] - c[t]
            path = float(np.abs(np.diff(c[t : t + H + 1])).sum())
            base = max(sigma[t] * np.sqrt(H) * c[t], 1e-12)
            deliv = abs(d) / base
            eff = abs(d) / max(path, 1e-12)
            b = self.bucket_of(int(minute_of_day[t]))
            w = dow[t] if dow[t] >= 0 else 0
            self.deliv[b] += a * (deliv - self.deliv[b])
            self.effic[b] += a * (eff - self.effic[b])
            self.n[b] += a * (1 - self.n[b]) if False else 0.0
            self.n[b] += 1.0
            self.dow_deliv[w, b] += a * (deliv - self.dow_deliv[w, b])
            self.dow_n[w, b] += 1.0

    def profile(self) -> np.ndarray:
        """Combined delivery score, normalised to mean 1 across the day."""
        s = self.deliv * self.effic
        m = s.mean()
        return s / max(m, 1e-12)

    def intensity(self, minute_of_day: int, dow: int = -1) -> float:
        b = self.bucket_of(minute_of_day)
        base = self.profile()[b]
        if 0 <= dow < 7 and self.dow_n[dow, b] > 30:
            md = self.dow_deliv[dow].mean()
            if md > 0:
                base *= float(np.clip(self.dow_deliv[dow, b] / md, 0.4, 2.0))
        return float(base)

    def zscore(self, minute_of_day: int) -> float:
        p = self.profile()
        b = self.bucket_of(minute_of_day)
        mad = np.median(np.abs(p - np.median(p))) * 1.4826
        return float((p[b] - np.median(p)) / max(mad, 1e-9))

    def discover_windows(self, top_frac: float = 0.25, min_buckets: int = 2) -> list[dict]:
        """Contiguous runs of high-delivery buckets. No fixed hours, no fixed count."""
        p = self.profile()
        thr = np.quantile(p, 1.0 - top_frac)
        hot = p >= thr
        out: list[dict] = []
        i = 0
        nb = self.nb
        while i < nb:
            if hot[i]:
                j = i
                while j + 1 < nb and hot[j + 1]:
                    j += 1
                if j - i + 1 >= min_buckets:
                    out.append({
                        "start_min": int(i * self.bucket_min),
                        "end_min": int((j + 1) * self.bucket_min),
                        "peak_min": int((i + int(np.argmax(p[i : j + 1]))) * self.bucket_min),
                        "score": float(p[i : j + 1].max()),
                        "buckets": int(j - i + 1),
                    })
                i = j + 1
            else:
                i += 1
        # merge across midnight
        if len(out) > 1 and out[0]["start_min"] == 0 and out[-1]["end_min"] == 24 * 60:
            a = out.pop(-1)
            out[0]["start_min"] = a["start_min"] - 24 * 60
            out[0]["score"] = max(out[0]["score"], a["score"])
        return sorted(out, key=lambda w: -w["score"])


ICT_WINDOWS = [
    ("London Open KZ", 2 * 60, 5 * 60),
    ("NY AM KZ", 8 * 60 + 30, 11 * 60),
    ("NY PM KZ", 13 * 60 + 30, 16 * 60),
    ("Silver Bullet AM", 3 * 60, 4 * 60),
    ("Silver Bullet NY", 10 * 60, 11 * 60),
    ("Silver Bullet PM", 14 * 60, 15 * 60),
    ("Macro 02:33", 2 * 60 + 33, 3 * 60),
    ("Macro 04:03", 4 * 60 + 3, 4 * 60 + 30),
    ("Macro 08:50", 8 * 60 + 50, 9 * 60 + 10),
    ("Macro 09:50", 9 * 60 + 50, 10 * 60 + 10),
    ("Macro 10:50", 10 * 60 + 50, 11 * 60 + 10),
    ("Macro 11:50", 11 * 60 + 50, 12 * 60 + 10),
    ("Macro 13:10", 13 * 60 + 10, 13 * 60 + 40),
    ("Macro 15:15", 15 * 60 + 15, 15 * 60 + 45),
]


def score_ict_windows(clock: DeliveryClock) -> list[dict]:
    """How does each canonical ICT window actually score on this instrument?"""
    p = clock.profile()
    bm = clock.bucket_min
    rows = []
    for name, a, b in ICT_WINDOWS:
        i0 = int(a // bm)
        i1 = int(np.ceil(b / bm))
        idx = [(i) % clock.nb for i in range(i0, i1)] or [i0 % clock.nb]
        v = float(np.mean([p[i] for i in idx]))
        rows.append({"window": name, "start": a, "end": b, "score": v})
    rows.sort(key=lambda r: -r["score"])
    return rows


def session_phase(minute_of_day: int) -> str:
    if minute_of_day >= 18 * 60 or minute_of_day < 2 * 60:
        return "asia"
    if minute_of_day < 8 * 60:
        return "london"
    if minute_of_day < 12 * 60:
        return "ny_am"
    if minute_of_day < 16 * 60 + 15:
        return "ny_pm"
    return "closed"


PHASES = ("asia", "london", "ny_am", "ny_pm", "closed")
