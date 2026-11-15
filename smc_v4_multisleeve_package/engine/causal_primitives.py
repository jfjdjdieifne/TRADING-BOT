"""Strictly Zero-Lookahead Causal Primitives for Multi-Timeframe XAUUSD SMC Research.

Every primitive enforces strict causal information-time availability:
1. Bar resampling uses left-closed/left-labeled bins indexed by `end_time = bin_start + period`.
   An incomplete bar is never merged into future bars before `end_time`.
2. Swing High/Low pivots with parameter `k` at bar index `c` become visible ONLY at
   bar `c + k` (after `k` subsequent bars have closed).
3. Wilder ATR(14) at bar `i` uses only True Range values from bars `<= i`.
4. Higher-timeframe (4H / 1H / 15m) BOS/CHoCH trend updates only when `htf_end_time <= ltf_end_time`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SwingPoint:
    candle_idx: int
    confirm_idx: int
    confirm_time: pd.Timestamp
    price: float
    kind: str  # "high" or "low"


def load_xauusd_1m(data_dir: Path, months: list[str] | None = None) -> pd.DataFrame:
    """Load sorted UTC 1m OHLC CSV.GZ archives with strict monotonicity & sanity checks."""
    files = sorted(data_dir.glob("*.csv.gz"))
    if months is not None:
        wanted = {f"{m}.csv.gz" for m in months}
        files = [f for f in files if f.name in wanted]
    if not files:
        raise FileNotFoundError(f"No .csv.gz files found in {data_dir}")

    parts = []
    for f in files:
        df = pd.read_csv(f)
        df["Datetime"] = pd.to_datetime(df["Datetime"], utc=True)
        parts.append(df)

    out = pd.concat(parts, ignore_index=True)
    out = out.sort_values("Datetime").drop_duplicates(subset=["Datetime"], keep="first")
    out = out.set_index("Datetime")
    for col in ("Open", "High", "Low", "Close"):
        out[col] = out[col].astype(np.float64)
    if "Volume" in out.columns:
        out["Volume"] = out["Volume"].astype(np.float64)
    return out


def resample_causal_tf(df_1m: pd.DataFrame, freq: str) -> pd.DataFrame:
    """Resample 1m OHLC into completed `freq` bars indexed by exact bar `end_time`.

    Example: `freq='15min'`, 08:00..08:14 1m bars -> `start_time=08:00`, `index=08:15`.
    Also records `first_1m_pos` and `last_1m_pos` (integer positions into `df_1m`)
    for exact intra-bar 1m execution without scanning the entire dataframe.
    """
    norm_map = {"5m": "5min", "15m": "15min", "30m": "30min", "1h": "1h", "4h": "4h"}
    rule = norm_map.get(freq, freq)
    delta = pd.Timedelta(rule)

    tmp = df_1m[["Open", "High", "Low", "Close"]].copy()
    tmp["_pos"] = np.arange(len(tmp), dtype=np.int64)
    agg = (
        tmp.resample(rule, label="left", closed="left")
        .agg(
            Open=("Open", "first"),
            High=("High", "max"),
            Low=("Low", "min"),
            Close=("Close", "last"),
            first_1m_pos=("_pos", "min"),
            last_1m_pos=("_pos", "max"),
        )
        .dropna()
    )
    agg["start_time"] = agg.index
    agg.index = agg.index + delta
    agg.index.name = "end_time"
    agg["first_1m_pos"] = agg["first_1m_pos"].astype(np.int64)
    agg["last_1m_pos"] = agg["last_1m_pos"].astype(np.int64)
    return agg


def detect_swings_causal(
    highs: np.ndarray,
    lows: np.ndarray,
    end_times: pd.DatetimeIndex,
    k: int,
) -> dict[int, list[SwingPoint]]:
    """Map `confirm_idx -> list[SwingPoint]` where `confirm_idx = pivot_idx + k`.

    Zero-lookahead guarantee: a pivot at `c` is strictly confirmed only at `c + k`
    using bars `[c - k, c + k]`.
    """
    n = len(highs)
    out: dict[int, list[SwingPoint]] = {}
    if k < 1 or n < 2 * k + 1:
        return out

    for c in range(k, n - k):
        confirm_idx = c + k
        hi_c = float(highs[c])
        lo_c = float(lows[c])
        left_hi = highs[c - k : c]
        right_hi = highs[c + 1 : c + k + 1]
        left_lo = lows[c - k : c]
        right_lo = lows[c + 1 : c + k + 1]

        if hi_c > float(np.max(left_hi)) and hi_c >= float(np.max(right_hi)):
            out.setdefault(confirm_idx, []).append(
                SwingPoint(
                    candle_idx=c,
                    confirm_idx=confirm_idx,
                    confirm_time=end_times[confirm_idx],
                    price=hi_c,
                    kind="high",
                )
            )
        if lo_c < float(np.min(left_lo)) and lo_c <= float(np.min(right_lo)):
            out.setdefault(confirm_idx, []).append(
                SwingPoint(
                    candle_idx=c,
                    confirm_idx=confirm_idx,
                    confirm_time=end_times[confirm_idx],
                    price=lo_c,
                    kind="low",
                )
            )
    return out


def in_killzone_utc(ts: pd.Timestamp) -> bool:
    """London (07:00-11:00 UTC) and New York (12:00-17:00 UTC) killzones."""
    h = ts.hour
    return (7 <= h < 11) or (12 <= h < 17)


def causal_atr14(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> np.ndarray:
    """Causal Wilder ATR(14) computed sequentially without any future dependence."""
    n = len(highs)
    atr = np.full(n, np.nan, dtype=np.float64)
    if n < period + 1:
        return atr
    tr = np.empty(n, dtype=np.float64)
    tr[0] = float(highs[0] - lows[0])
    for i in range(1, n):
        tr[i] = max(
            float(highs[i] - lows[i]),
            abs(float(highs[i] - closes[i - 1])),
            abs(float(lows[i] - closes[i - 1])),
        )
    atr[period - 1] = float(np.mean(tr[:period]))
    alpha = 1.0 / period
    for i in range(period, n):
        atr[i] = (1.0 - alpha) * atr[i - 1] + alpha * tr[i]
    return atr


def build_causal_htf_structure(
    df_1m: pd.DataFrame,
    freq: str,
    swing_k: int = 2,
) -> tuple[pd.DatetimeIndex, np.ndarray]:
    """Causal BOS/CHoCH market structure state (+1 bullish, -1 bearish, 0 neutral)
    computed on completed `freq` bars (`end_time = bin_start + freq`)."""
    tf = resample_causal_tf(df_1m, freq)
    h = tf["High"].to_numpy()
    l = tf["Low"].to_numpy()
    c = tf["Close"].to_numpy()
    sw = detect_swings_causal(h, l, tf.index, swing_k)

    trend = np.zeros(len(tf), dtype=np.int8)
    last_sh: float | None = None
    last_sl: float | None = None
    cur = 0
    for i in range(len(tf)):
        for sp in sw.get(i, []):
            if sp.kind == "high":
                last_sh = sp.price
            else:
                last_sl = sp.price
        if last_sh is not None and c[i] > last_sh:
            cur = 1
        elif last_sl is not None and c[i] < last_sl:
            cur = -1
        trend[i] = cur
    return tf.index, trend


def build_causal_swing_events(
    df_1m: pd.DataFrame,
    freq: str = "1h",
    k: int = 2,
) -> tuple[pd.DatetimeIndex, list[str], np.ndarray]:
    """Return chronologically ordered confirmed swing events `(confirm_times, kinds, prices)`.

    Every event at `confirm_times[idx]` is strictly confirmed after `k` completed `freq` bars
    following the pivot bar, guaranteeing zero future leakage for live trailing stops.
    """
    tf = resample_causal_tf(df_1m, freq)
    sw = detect_swings_causal(tf["High"].to_numpy(), tf["Low"].to_numpy(), tf.index, k)
    ev_t: list[pd.Timestamp] = []
    ev_k: list[str] = []
    ev_p: list[float] = []
    for i in range(len(tf)):
        for sp in sw.get(i, []):
            ev_t.append(tf.index[i])
            ev_k.append(sp.kind)
            ev_p.append(sp.price)
    return pd.DatetimeIndex(ev_t), ev_k, np.array(ev_p, dtype=np.float64)

