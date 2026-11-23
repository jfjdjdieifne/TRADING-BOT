"""Anti-Chop KER, Volatility Squeeze, Time-of-Day RVOL Anatomy & BTC Regime Filter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np
import pandas as pd

from .perception_engine import compute_atr_series, sigmoid


@dataclass
class RegimeSnapshot:
    ker: float
    ker_score: float
    range_pos: float  # 0.0=range low, 0.5=mid equilibrium, 1.0=range high
    in_mid_chop: bool
    squeeze_ratio: float
    prior_compressed: bool
    squeeze_score: float
    rvol: float
    rvol_score: float
    body_ratio: float
    effort_result_score: float
    absorption_trap_score: float
    btc_regime_score: float


class RegimeFilterEngine:
    """Vectorized regime diagnostics + per-bar causal scoring without lookahead."""

    def __init__(self, ker_period: int = 20, rvol_days: int = 20) -> None:
        self.ker_period = int(ker_period)
        self.rvol_days = int(rvol_days)

    @staticmethod
    def compute_ker_series(close: np.ndarray, period: int = 20) -> np.ndarray:
        n = len(close)
        ker = np.zeros(n, dtype=float)
        if n <= period:
            return ker
        diffs = np.abs(np.diff(close, prepend=close[0]))
        csum = np.cumsum(diffs)
        net = np.abs(close[period:] - close[:-period])
        vol_sum = csum[period:] - csum[:-period]
        valid = vol_sum > 1e-12
        out = np.zeros_like(net)
        out[valid] = net[valid] / vol_sum[valid]
        ker[period:] = np.clip(out, 0.0, 1.0)
        return ker

    @staticmethod
    def compute_squeeze_ratio_series(
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        period: int = 20,
        bb_mult: float = 2.0,
        kc_mult: float = 1.5,
    ) -> np.ndarray:
        s = pd.Series(close)
        mid = s.rolling(period, min_periods=period).mean().to_numpy()
        sd = s.rolling(period, min_periods=period).std(ddof=0).to_numpy()
        atr = compute_atr_series(high, low, close, period=period)
        bb_w = 2.0 * bb_mult * sd
        kc_w = np.maximum(2.0 * kc_mult * atr, 1e-12)
        ratio = np.where(np.isfinite(bb_w), bb_w / kc_w, 1.0)
        return ratio

    @staticmethod
    def compute_tod_rvol_series(df: pd.DataFrame, lookback_slots: int = 20) -> np.ndarray:
        """Vectorized Time-of-Day Normalized RVOL using strictly PRIOR days' same UTC slot."""
        vol = df["Volume"].to_numpy(dtype=float)
        if len(vol) == 0:
            return np.array([], dtype=float)
        idx = df.index
        slot = idx.hour * 60 + idx.minute
        ser = pd.Series(vol, index=df.index)
        # Shift by 1 inside each time-of-day group so current bar never leaks into its own baseline!
        base = ser.groupby(slot).transform(
            lambda g: g.shift(1).rolling(lookback_slots, min_periods=5).median()
        ).to_numpy(dtype=float)
        fallback = ser.shift(1).rolling(lookback_slots * 4, min_periods=10).median().to_numpy(dtype=float)
        denom = np.where(np.isfinite(base) & (base > 0), base, np.where(np.isfinite(fallback) & (fallback > 0), fallback, 1.0))
        return np.where(denom > 0, vol / denom, 1.0)

    def precompute_frame_features(self, df: pd.DataFrame) -> Dict[str, np.ndarray]:
        """Precompute vectorized causal arrays on a closed-bar DataFrame."""
        o = df["Open"].to_numpy(dtype=float)
        h = df["High"].to_numpy(dtype=float)
        l = df["Low"].to_numpy(dtype=float)
        c = df["Close"].to_numpy(dtype=float)
        n = len(c)

        ker = self.compute_ker_series(c, self.ker_period)
        sq = self.compute_squeeze_ratio_series(h, l, c, period=20)
        sq_min_recent = pd.Series(sq).shift(1).rolling(6, min_periods=1).min().fillna(1.0).to_numpy(dtype=float)

        hi_rng = pd.Series(h).rolling(self.ker_period, min_periods=1).max().to_numpy(dtype=float)
        lo_rng = pd.Series(l).rolling(self.ker_period, min_periods=1).min().to_numpy(dtype=float)
        span = np.maximum(hi_rng - lo_rng, 1e-12)
        range_pos = np.clip((c - lo_rng) / span, 0.0, 1.0)

        rvol = self.compute_tod_rvol_series(df, lookback_slots=self.rvol_days)
        rng_bar = np.maximum(h - l, 1e-12)
        body_ratio = np.abs(c - o) / rng_bar

        atr14 = compute_atr_series(h, l, c, period=14)
        return {
            "ker": ker,
            "squeeze_ratio": sq,
            "sq_min_recent": sq_min_recent,
            "range_pos": range_pos,
            "rvol": rvol,
            "body_ratio": body_ratio,
            "atr14": atr14,
            "n": np.array([n]),
        }

    def evaluate_bar(
        self,
        feats: Dict[str, np.ndarray],
        i: int,
        has_boundary_sweep: bool = False,
        btc_regime_score: float = 1.0,
    ) -> RegimeSnapshot:
        """Score bar `i` continuously using precomputed causal arrays."""
        ker = float(feats["ker"][i])
        sq = float(feats["squeeze_ratio"][i])
        sq_min = float(feats["sq_min_recent"][i])
        rpos = float(feats["range_pos"][i])
        rvol = float(feats["rvol"][i])
        br = float(feats["body_ratio"][i])

        in_mid_chop = (ker < 0.25) and (0.25 <= rpos <= 0.75) and (not has_boundary_sweep)
        ker_score = 0.05 if in_mid_chop else float(sigmoid(ker, x0=0.25, k=9.0))
        if has_boundary_sweep and ker < 0.25:
            # Boundary sweeps inside range boundaries are allowed (not penalized as mid-range chop)
            ker_score = max(ker_score, 0.65)

        prior_compressed = sq_min < 0.98
        squeeze_exp = float(sigmoid(sq - sq_min, x0=0.04, k=18.0)) if prior_compressed else 0.45
        squeeze_score = float(np.clip(0.55 * float(sigmoid(1.05 - sq_min, x0=0.05, k=12.0)) + 0.45 * squeeze_exp, 0.0, 1.0))

        rvol_score = float(sigmoid(rvol, x0=1.6, k=2.2))

        # Wyckoff Effort-vs-Result:
        #   - Valid displacement: synchronous high RVOL + Body/Range > 0.65
        #   - Absorption trap: RVOL > 1.8 + tiny body (br < 0.35)
        body_ok = float(sigmoid(br, x0=0.65, k=9.0))
        effort_result = float(np.clip(rvol_score * body_ok + (0.25 if (rvol >= 1.4 and br >= 0.65) else 0.0), 0.0, 1.0))
        trap = float(sigmoid(rvol, x0=1.8, k=3.0) * sigmoid(0.42 - br, x0=0.0, k=10.0))

        return RegimeSnapshot(
            ker=ker,
            ker_score=ker_score,
            range_pos=rpos,
            in_mid_chop=in_mid_chop,
            squeeze_ratio=sq,
            prior_compressed=prior_compressed,
            squeeze_score=squeeze_score,
            rvol=rvol,
            rvol_score=rvol_score,
            body_ratio=br,
            effort_result_score=effort_result,
            absorption_trap_score=trap,
            btc_regime_score=float(np.clip(btc_regime_score, 0.0, 1.0)),
        )

    @staticmethod
    def compute_btc_regime_score(
        trade_side: int,
        btc_4h_trend: int,
        btc_4h_disp: float,
        corr_to_btc: Optional[float] = None,
    ) -> float:
        """Cross-asset BTC veto: block altcoin longs when BTC breaks 4H bearishly with high displacement."""
        c_wt = 1.0 if corr_to_btc is None else float(np.clip(abs(corr_to_btc), 0.3, 1.0))
        if trade_side == 1 and btc_4h_trend == -1 and btc_4h_disp >= 0.65:
            return float(max(0.05, 1.0 - 0.90 * c_wt * btc_4h_disp))
        if trade_side == -1 and btc_4h_trend == 1 and btc_4h_disp >= 0.65:
            return float(max(0.05, 1.0 - 0.90 * c_wt * btc_4h_disp))
        if trade_side == btc_4h_trend:
            return 0.92
        return 0.65
