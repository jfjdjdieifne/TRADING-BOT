"""Scale-Free Topological Perception & Continuous Activation Kernel Engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.signal import find_peaks


@dataclass
class TopologicalSwing:
    idx: int
    confirm_idx: int
    ts_ns: int
    side: int  # +1 = swing high (peak), -1 = swing low (trough)
    price: float
    prominence_atr: float
    clean_air_bars: int
    structural_weight: float
    wick_close: float
    mitigated: bool = False


def sigmoid(x: np.ndarray | float, x0: float = 0.0, k: float = 1.0) -> np.ndarray | float:
    """Smooth continuous activation mapping (-inf, +inf) -> (0, 1)."""
    z = np.clip(-k * (np.asarray(x, dtype=float) - x0), -60.0, 60.0)
    out = 1.0 / (1.0 + np.exp(z))
    return float(out) if np.isscalar(x) else out


def gaussian_rbf(delta: np.ndarray | float, sigma: float = 1.0) -> np.ndarray | float:
    """Gaussian Radial Basis Function kernel exp(-delta^2 / (2 * sigma^2))."""
    s = max(float(sigma), 1e-12)
    d = np.asarray(delta, dtype=float)
    out = np.exp(-0.5 * (d / s) ** 2)
    return float(out) if np.isscalar(delta) else out


def soft_and_log_odds(
    scores: Dict[str, float],
    weights: Dict[str, float],
    veto_floors: Optional[Dict[str, float]] = None,
    eps: float = 1e-4,
) -> float:
    """Compensatory weighted log-odds tensor with optional critical regime veto."""
    if veto_floors:
        for k_veto, floor in veto_floors.items():
            if k_veto in scores and scores[k_veto] < floor:
                # Smooth collapse when a critical regime filter is near zero
                return float(max(0.0, scores[k_veto] / max(floor, eps)) * 0.15)

    num = 0.0
    den = 0.0
    for key, w in weights.items():
        if w <= 0 or key not in scores:
            continue
        p = float(np.clip(scores[key], eps, 1.0 - eps))
        num += float(w) * float(np.log(p / (1.0 - p)))
        den += float(w)
    if den <= 0:
        return 0.0
    return float(sigmoid(num / den, x0=0.0, k=1.0))


def compute_atr_series(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
    """Vectorized Wilder ATR matching pandas ewm(alpha=1/period, adjust=False)."""
    n = len(close)
    if n == 0:
        return np.array([], dtype=float)
    tr = np.empty(n, dtype=float)
    tr[0] = high[0] - low[0]
    if n > 1:
        pc = close[:-1]
        tr[1:] = np.maximum.reduce([high[1:] - low[1:], np.abs(high[1:] - pc), np.abs(low[1:] - pc)])
    alpha = 1.0 / float(period)
    atr = np.empty(n, dtype=float)
    atr[0] = tr[0]
    for i in range(1, n):
        atr[i] = (1.0 - alpha) * atr[i - 1] + alpha * tr[i]
    return atr


class VisualPerceptionEngine:
    """Perceives swings, EQH/EQL clusters, displacement, and FVGs via scale-free continuous kernels."""

    def __init__(
        self,
        min_prominence_atr: float = 0.90,
        zigzag_atr_mult: float = 1.25,
        eq_sigma_valley: float = 0.12,
        eq_sigma_atr: float = 0.35,
    ) -> None:
        self.min_prominence_atr = float(min_prominence_atr)
        self.zigzag_atr_mult = float(zigzag_atr_mult)
        self.eq_sigma_valley = float(eq_sigma_valley)
        self.eq_sigma_atr = float(eq_sigma_atr)

    def detect_causal_swings(
        self,
        ts_ns: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        atr: np.ndarray,
        max_swings: int = 60,
    ) -> List[TopologicalSwing]:
        """Causal scale-free swing detection combining volatility ZigZag & topological prominence.

        Every swing at `idx` receives a strict `confirm_idx > idx` equal to the first future bar
        where price retraces away from the extremum by at least `min_prominence_atr * ATR[idx]`
        (and never peeks past `len(close) - 1`).
        """
        n = len(close)
        if n < 10:
            return []

        # 1) Causal Volatility-Adjusted ZigZag / Perceptually Important Points (PIPs)
        swings: List[TopologicalSwing] = []
        direction = 0  # +1 seeking peak, -1 seeking trough
        piv_idx = 0
        piv_hi = high[0]
        piv_lo = low[0]

        for i in range(1, n):
            a_i = max(float(atr[i]), 1e-12)
            thresh = self.zigzag_atr_mult * a_i
            if direction == 0:
                if high[i] - piv_lo >= thresh:
                    swings.append(
                        TopologicalSwing(
                            idx=piv_idx, confirm_idx=i, ts_ns=int(ts_ns[piv_idx]), side=-1,
                            price=float(piv_lo), prominence_atr=float((high[i] - piv_lo) / a_i),
                            clean_air_bars=i - piv_idx, structural_weight=0.5,
                            wick_close=float(close[piv_idx]),
                        )
                    )
                    direction = 1
                    piv_idx, piv_hi = i, float(high[i])
                elif piv_hi - low[i] >= thresh:
                    swings.append(
                        TopologicalSwing(
                            idx=piv_idx, confirm_idx=i, ts_ns=int(ts_ns[piv_idx]), side=1,
                            price=float(piv_hi), prominence_atr=float((piv_hi - low[i]) / a_i),
                            clean_air_bars=i - piv_idx, structural_weight=0.5,
                            wick_close=float(close[piv_idx]),
                        )
                    )
                    direction = -1
                    piv_idx, piv_lo = i, float(low[i])
                else:
                    if high[i] > piv_hi:
                        piv_hi, piv_idx = float(high[i]), i
                    if low[i] < piv_lo:
                        piv_lo, piv_idx = float(low[i]), i
            elif direction == 1:
                if high[i] >= piv_hi:
                    piv_hi, piv_idx = float(high[i]), i
                elif piv_hi - low[i] >= thresh:
                    prom_atr = (piv_hi - float(np.min(low[piv_idx:i + 1]))) / max(float(atr[piv_idx]), 1e-12)
                    swings.append(
                        TopologicalSwing(
                            idx=piv_idx, confirm_idx=i, ts_ns=int(ts_ns[piv_idx]), side=1,
                            price=float(piv_hi), prominence_atr=float(prom_atr),
                            clean_air_bars=i - piv_idx, structural_weight=0.5,
                            wick_close=float(close[piv_idx]),
                        )
                    )
                    direction = -1
                    piv_idx, piv_lo = i, float(low[i])
            else:
                if low[i] <= piv_lo:
                    piv_lo, piv_idx = float(low[i]), i
                elif high[i] - piv_lo >= thresh:
                    prom_atr = (float(np.max(high[piv_idx:i + 1])) - piv_lo) / max(float(atr[piv_idx]), 1e-12)
                    swings.append(
                        TopologicalSwing(
                            idx=piv_idx, confirm_idx=i, ts_ns=int(ts_ns[piv_idx]), side=-1,
                            price=float(piv_lo), prominence_atr=float(prom_atr),
                            clean_air_bars=i - piv_idx, structural_weight=0.5,
                            wick_close=float(close[piv_idx]),
                        )
                    )
                    direction = 1
                    piv_idx, piv_hi = i, float(high[i])

        # 2) Topological Peak Prominence pass via scipy.signal.find_peaks + strict causal confirm index
        med_atr = float(np.nanmedian(atr[max(0, n - 100):n]))
        min_prom = max(self.min_prominence_atr * med_atr, 1e-12)
        hi_peaks, hi_props = find_peaks(high, prominence=min_prom, distance=2)
        lo_peaks, lo_props = find_peaks(-low, prominence=min_prom, distance=2)

        existing = {(s.idx, s.side) for s in swings}
        for pk, prom in zip(hi_peaks, hi_props["prominences"]):
            if (int(pk), 1) in existing:
                continue
            a_pk = max(float(atr[pk]), 1e-12)
            drop_need = self.min_prominence_atr * a_pk
            later = np.where(low[pk + 1:] <= high[pk] - drop_need)[0]
            if len(later) == 0:
                continue  # Not causally confirmed yet!
            c_idx = int(pk + 1 + later[0])
            swings.append(
                TopologicalSwing(
                    idx=int(pk), confirm_idx=c_idx, ts_ns=int(ts_ns[pk]), side=1,
                    price=float(high[pk]), prominence_atr=float(prom / a_pk),
                    clean_air_bars=c_idx - int(pk), structural_weight=0.5,
                    wick_close=float(close[pk]),
                )
            )

        for pk, prom in zip(lo_peaks, lo_props["prominences"]):
            if (int(pk), -1) in existing:
                continue
            a_pk = max(float(atr[pk]), 1e-12)
            rally_need = self.min_prominence_atr * a_pk
            later = np.where(high[pk + 1:] >= low[pk] + rally_need)[0]
            if len(later) == 0:
                continue  # Not causally confirmed yet!
            c_idx = int(pk + 1 + later[0])
            swings.append(
                TopologicalSwing(
                    idx=int(pk), confirm_idx=c_idx, ts_ns=int(ts_ns[pk]), side=-1,
                    price=float(low[pk]), prominence_atr=float(prom / a_pk),
                    clean_air_bars=c_idx - int(pk), structural_weight=0.5,
                    wick_close=float(close[pk]),
                )
            )

        # 3) Evaluate Clean Air (unmitigated bars) and continuous structural_weight in [0, 1]
        last_idx = n - 1
        out: List[TopologicalSwing] = []
        for s in sorted(swings, key=lambda x: x.confirm_idx):
            fut_h = high[s.idx + 1:]
            fut_l = low[s.idx + 1:]
            if s.side == 1:
                breach = np.where(fut_h > s.price)[0]
            else:
                breach = np.where(fut_l < s.price)[0]
            if len(breach) > 0:
                s.mitigated = True
                s.clean_air_bars = int(breach[0] + 1)
            else:
                s.mitigated = False
                s.clean_air_bars = int(last_idx - s.idx)

            prom_score = float(sigmoid(s.prominence_atr, x0=1.8, k=1.25))
            air_score = float(sigmoid(s.clean_air_bars, x0=6.0, k=0.22))
            s.structural_weight = float(np.clip(0.65 * prom_score + 0.35 * air_score, 0.0, 1.0))
            out.append(s)

        return out[-max_swings:]

    def visual_eqh_eql_score(
        self,
        s1: TopologicalSwing,
        s2: TopologicalSwing,
        valley_extreme: float,
        atr_val: float,
    ) -> float:
        """Continuous Valley-Depth Gaussian RBF score for Equal Highs / Equal Lows.

        Boosts score contextually when s2 sweeps slightly past s1 and closes back inside.
        """
        if s1.side != s2.side or s1.idx >= s2.idx or atr_val <= 0:
            return 0.0
        eps = 1e-12
        if s1.side == 1:
            depth = max(s1.price, s2.price) - valley_extreme
        else:
            depth = valley_extreme - min(s1.price, s2.price)
        diff = abs(s1.price - s2.price)
        d_valley = diff / max(depth, eps)
        d_atr = diff / max(atr_val, eps)
        s_eq = float(gaussian_rbf(d_valley, self.eq_sigma_valley) * gaussian_rbf(d_atr, self.eq_sigma_atr))

        # Contextual Compensation (Liquidity Sweep Wick boost)
        if s1.side == 1 and s2.price > s1.price and s2.wick_close < s1.price:
            wick_pen = (s2.price - s1.price) / max(atr_val, eps)
            s_eq = min(1.0, s_eq * (1.0 + 0.45 * float(gaussian_rbf(wick_pen, 0.5))))
        elif s1.side == -1 and s2.price < s1.price and s2.wick_close > s1.price:
            wick_pen = (s1.price - s2.price) / max(atr_val, eps)
            s_eq = min(1.0, s_eq * (1.0 + 0.45 * float(gaussian_rbf(wick_pen, 0.5))))
        return float(np.clip(s_eq, 0.0, 1.0))

    @staticmethod
    def displacement_score(o: float, h: float, l: float, c: float, atr: float) -> float:
        """Continuous score of displacement candle strength (body/ATR + body/range)."""
        if atr <= 0 or h <= l:
            return 0.0
        body = abs(c - o)
        rng = h - l
        s_atr = float(sigmoid(body / atr, x0=1.2, k=2.2))
        s_anat = float(sigmoid(body / rng, x0=0.60, k=7.0))
        return float(np.clip(0.60 * s_atr + 0.40 * s_anat, 0.0, 1.0))

    @staticmethod
    def rejection_wick_score(o: float, h: float, l: float, c: float, side: int, atr: float) -> float:
        """Continuous score of liquidity absorption wick for `side` (+1 bullish bottom wick, -1 bearish top wick)."""
        if atr <= 0 or h <= l:
            return 0.0
        rng = h - l
        wick = (min(o, c) - l) if side == 1 else (h - max(o, c))
        s_wick_rng = float(sigmoid(wick / rng, x0=0.42, k=8.0))
        s_wick_atr = float(sigmoid(wick / atr, x0=0.55, k=3.5))
        close_pos = ((c - l) / rng) if side == 1 else ((h - c) / rng)
        s_close = float(sigmoid(close_pos, x0=0.55, k=6.0))
        return float(np.clip(0.45 * s_wick_rng + 0.30 * s_wick_atr + 0.25 * s_close, 0.0, 1.0))

    @staticmethod
    def fvg_quality_score(gap_size: float, atr: float) -> float:
        """Continuous score of Fair Value Gap imbalance relative to ATR."""
        if atr <= 0 or gap_size <= 0:
            return 0.0
        return float(sigmoid(gap_size / atr, x0=0.35, k=4.5))
