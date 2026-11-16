"""Data loading: HistData-style 1-minute CSVs -> tz-correct bar frames.

Timezone note (established empirically, see scripts/probe_timezone.py):
the repository's NSXUSD_1m_histdata files are stamped in **Europe/London**
(GMT/BST).  Proof: after converting to America/New_York the trading session
runs 18:00 -> 16:14 ET every day of the year, the London cash open bumps at
03:00 ET, and the single largest one-minute volatility bucket of the whole
6.8-year sample is 09:30-09:45 ET (the US cash open).  No other fixed offset
reproduces all three facts simultaneously.
"""

from __future__ import annotations

import glob as _glob
import os
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd


@dataclass
class Bars:
    """A bar series. Index is tz-aware (America/New_York by default)."""

    idx: pd.DatetimeIndex
    o: np.ndarray
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray

    def __len__(self) -> int:
        return len(self.c)

    @property
    def n(self) -> int:
        return len(self.c)

    def slice(self, a: int, b: int) -> "Bars":
        return Bars(self.idx[a:b], self.o[a:b], self.h[a:b], self.l[a:b], self.c[a:b])

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            {"o": self.o, "h": self.h, "l": self.l, "c": self.c}, index=self.idx
        )


SRC_TZ = "Europe/London"
OUT_TZ = "America/New_York"


def load_histdata_dir(
    directory: str,
    pattern: str = "*.csv.gz",
    src_tz: str = SRC_TZ,
    out_tz: str = OUT_TZ,
) -> pd.DataFrame:
    """Read every monthly file, sort, de-duplicate, convert timezone."""
    files = sorted(_glob.glob(os.path.join(directory, pattern)))
    if not files:
        raise FileNotFoundError(f"no files in {directory} matching {pattern}")
    frames = []
    for f in files:
        d = pd.read_csv(f)
        col = [c for c in d.columns if c.lower() in ("datetime", "time", "timestamp", "date")]
        if not col:
            raise ValueError(f"{f}: no datetime column (cols={list(d.columns)})")
        d[col[0]] = pd.to_datetime(d[col[0]])
        d = d.rename(columns={col[0]: "dt"})
        keep = {}
        for want in ("open", "high", "low", "close"):
            for c in d.columns:
                if c.lower() == want:
                    keep[want[0]] = d[c]
        frames.append(pd.DataFrame(keep).assign(dt=d["dt"].values))
    df = pd.concat(frames, ignore_index=True)
    df = df.dropna(subset=["o", "h", "l", "c"])
    df = df.sort_values("dt").drop_duplicates("dt").reset_index(drop=True)

    idx = pd.DatetimeIndex(df["dt"].values)
    if idx.tz is None:
        idx = idx.tz_localize(src_tz, ambiguous="NaT", nonexistent="shift_forward")
    idx = idx.tz_convert(out_tz)
    df = df.drop(columns=["dt"])
    df.index = idx
    df.index.name = "dt"
    bad = (df.h < df.l) | (df.c > df.h) | (df.c < df.l) | (df.o > df.h) | (df.o < df.l)
    if bad.any():
        df = df[~bad.values]
    return df


def resample(df: pd.DataFrame, minutes: int) -> pd.DataFrame:
    """Time-based aggregation. Empty (market-closed) buckets are dropped.

    Bars therefore stay aligned to real trading minutes; the recipient can
    still detect a session break from the timestamp gap.
    """
    rule = f"{minutes}min"
    agg = df.resample(rule).agg(
        {"o": "first", "h": "max", "l": "min", "c": "last"}
    )
    agg = agg.dropna()
    return agg


def to_bars(df: pd.DataFrame) -> Bars:
    return Bars(
        df.index,
        df["o"].to_numpy(float),
        df["h"].to_numpy(float),
        df["l"].to_numpy(float),
        df["c"].to_numpy(float),
    )


def gap_minutes(idx: pd.DatetimeIndex) -> np.ndarray:
    g = np.empty(len(idx), dtype=float)
    g[0] = 1e9
    g[1:] = np.diff(idx.values).astype("timedelta64[m]").astype(float)
    return g


def session_ids(idx: pd.DatetimeIndex, break_minutes: float = 30.0) -> np.ndarray:
    """Increment whenever the market re-opens after a gap."""
    g = gap_minutes(idx)
    return np.cumsum(g > break_minutes).astype(np.int64)


def trading_day(idx: pd.DatetimeIndex) -> np.ndarray:
    """ICT trading day: the 18:00 ET open belongs to the *previous* calendar date.

    Shifting by -6h maps 18:00 ET (day D) -> 12:00 (day D) and 09:30 ET
    (day D+1) -> 03:30 (day D).  So one ICT day == one futures session.
    """
    shifted = idx.tz_convert("UTC").tz_localize(None) - pd.Timedelta(hours=6)
    return np.array([d.date() for d in shifted], dtype=object)


def minutes_of_day(idx: pd.DatetimeIndex) -> np.ndarray:
    return (idx.hour * 60 + idx.minute).astype(np.int64)


def load_all(
    directory: str,
    minutes: int = 5,
    src_tz: str = SRC_TZ,
    out_tz: str = OUT_TZ,
    cache: Optional[str] = None,
) -> Bars:
    """Convenience: load 1m files, cache the 1m frame, return `minutes` bars."""
    if cache and os.path.exists(cache):
        d1 = pd.read_pickle(cache)
    else:
        d1 = load_histdata_dir(directory, src_tz=src_tz, out_tz=out_tz)
        if cache:
            os.makedirs(os.path.dirname(cache) or ".", exist_ok=True)
            d1.to_pickle(cache)
    if minutes == 1:
        return to_bars(d1)
    return to_bars(resample(d1, minutes))
