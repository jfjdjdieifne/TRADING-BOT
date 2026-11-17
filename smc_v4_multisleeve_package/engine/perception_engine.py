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


class KinematicMonitor:
    """V6 Pillar 1 & 2: Pullback Velocity Ratio (K), Falling-Knife Veto, Causal Rejection & Fractal Compression."""

    def __init__(self, min_k_ratio: float = 0.85) -> None:
        self.min_k_ratio = float(min_k_ratio)

    @staticmethod
    def compute_kinematic_ratio(
        o: np.ndarray,
        h: np.ndarray,
        l: np.ndarray,
        c: np.ndarray,
        atr: np.ndarray,
        imp_start: int,
        imp_end: int,
        pb_end: int,
    ) -> Tuple[float, float, float]:
        """Compute K = V_impulse / max(V_pullback, eps), body-weighted per bar normalized by ATR.

        Returns (k_ratio, v_impulse, v_pullback). Strictly causal up to `pb_end`.
        """
        n = len(c)
        if imp_start < 0 or imp_end <= imp_start or pb_end <= imp_end or pb_end >= n:
            return 1.0, 0.0, 0.0
        a_imp = max(float(np.nanmean(atr[imp_start:imp_end + 1])), 1e-12)
        n_imp = max(1, imp_end - imp_start)
        rng_imp = np.maximum(h[imp_start:imp_end + 1] - l[imp_start:imp_end + 1], 1e-12)
        br_imp = float(np.mean(np.abs(c[imp_start:imp_end + 1] - o[imp_start:imp_end + 1]) / rng_imp))
        dp_imp = abs(float(c[imp_end]) - float(c[imp_start]))
        v_imp = (dp_imp / (n_imp * a_imp)) * max(0.30, br_imp)

        a_pb = max(float(np.nanmean(atr[imp_end:pb_end + 1])), 1e-12)
        n_pb = max(1, pb_end - imp_end)
        rng_pb = np.maximum(h[imp_end + 1:pb_end + 1] - l[imp_end + 1:pb_end + 1], 1e-12)
        br_pb = float(np.mean(np.abs(c[imp_end + 1:pb_end + 1] - o[imp_end + 1:pb_end + 1]) / rng_pb)) if len(rng_pb) > 0 else 0.5
        dp_pb = abs(float(c[pb_end]) - float(c[imp_end]))
        v_pb = (dp_pb / (n_pb * a_pb)) * max(0.25, br_pb)

        k_ratio = v_imp / max(v_pb, 1e-6)
        return float(k_ratio), float(v_imp), float(v_pb)

    def falling_knife_veto(self, k_ratio: float) -> bool:
        """True when pullback velocity overwhelms creating impulse (K < min_k_ratio)."""
        return k_ratio < self.min_k_ratio

    @staticmethod
    def causal_reaction_confirmed(
        o: np.ndarray,
        h: np.ndarray,
        l: np.ndarray,
        c: np.ndarray,
        v: np.ndarray,
        idx: int,
        side: int,
        atr_val: float,
    ) -> Tuple[bool, float]:
        """Causal turnaround / rejection confirmation on closed bar `idx`."""
        if idx < 2 or atr_val <= 0:
            return False, 0.0
        rng = max(float(h[idx] - l[idx]), 1e-12)
        wick = (min(float(o[idx]), float(c[idx])) - float(l[idx])) if side == 1 else (float(h[idx]) - max(float(o[idx]), float(c[idx])))
        wick_ratio = wick / rng
        close_in_dir = (c[idx] > o[idx]) if side == 1 else (c[idx] < o[idx])
        momentum_shift = (c[idx] > h[idx - 1] * 0.5 + l[idx - 1] * 0.5) if side == 1 else (c[idx] < h[idx - 1] * 0.5 + l[idx - 1] * 0.5)
        vol_declining_opp = (v[idx] <= v[idx - 1] * 1.15) if ((c[idx - 1] < o[idx - 1] and side == 1) or (c[idx - 1] > o[idx - 1] and side == -1)) else True

        rej_sc = VisualPerceptionEngine.rejection_wick_score(float(o[idx]), float(h[idx]), float(l[idx]), float(c[idx]), side, atr_val)
        confirmed = bool((close_in_dir and momentum_shift) or (wick_ratio >= 0.40 and rej_sc >= 0.45 and vol_declining_opp))
        return confirmed, float(rej_sc)

    @staticmethod
    def fractal_stop_compression(
        entry_px: float,
        side: int,
        atr_4h: float,
        atr_1h: float,
        candidate_anchors: List[float],
        rho_min: float = 0.35,
        rho_max: float = 0.70,
        min_rho_floor: float = 0.25,
        max_rho_cap: float = 2.40,
        fallback_mult: float = 1.85,
    ) -> Tuple[float, float, str]:
        """Scale-free volatility-normalized stop selection relative to ATR_4H (no fixed % clamp).

        Selects a confirmed structural swing anchor whose risk distance rho_comp = delta_SL / ATR_4H
        lies cleanly inside or nearest to [rho_min, rho_max] while maintaining a 0.20 * ATR_1H
        noise buffer behind the actual structural wick and honoring [min_rho_floor, max_rho_cap].
        """
        a4 = max(float(atr_4h), 1e-12)
        a1 = max(float(atr_1h), 1e-12)
        buf = 0.20 * a1
        best_sl: Optional[float] = None
        best_rho: float = fallback_mult
        best_score = -1e9
        src = "ATR4H_FALLBACK"

        for anc in candidate_anchors:
            sl_cand = (anc - buf) if side == 1 else (anc + buf)
            delta = (entry_px - sl_cand) if side == 1 else (sl_cand - entry_px)
            if delta <= 0:
                continue
            rho = delta / a4
            if rho < min_rho_floor or rho > max_rho_cap:
                continue
            in_golden = rho_min <= rho <= rho_max
            target_mid = 0.5 * (rho_min + rho_max)
            score = (2.0 if in_golden else 0.5) - abs(rho - target_mid)
            if score > best_score:
                best_score = score
                best_sl = sl_cand
                best_rho = rho
                src = "FRACTAL_GOLDEN" if in_golden else "FRACTAL_1H_STRUCT"

        if best_sl is None:
            best_rho = float(np.clip(fallback_mult, min_rho_floor, max_rho_cap))
            best_sl = (entry_px - best_rho * a4) if side == 1 else (entry_px + best_rho * a4)
        return float(best_sl), float(best_rho), src


@dataclass
class BPRZone:
    side: int  # +1=bullish inversion (short FVG inverted upward), -1=bearish inversion
    low: float
    high: float
    mid: float
    sweep_extreme: float
    created_idx: int
    k_velocity: float
    vacuum_score: float


@dataclass
class CompressionVacuumSetup:
    side: int  # +1=long reversal (floor swept + snapped up), -1=short reversal (ceiling swept + snapped down)
    barrier_px: float
    sweep_extreme: float
    snap_level: float
    origin_anchor: float
    approach_ker: float
    vacuum_score: float
    implied_r: float
    trigger_idx: int


class SceneGraphPhysicsDetector:
    """V7.0 Intraday 15m/5m Visual Scene-Graph Physics (Compression-Vacuum Snap & BPR/iFVG Polarity Inversion)."""

    def __init__(
        self,
        max_approach_ker: float = 0.42,
        min_bpr_k: float = 1.25,
        min_implied_r: float = 3.2,
    ) -> None:
        self.max_approach_ker = float(max_approach_ker)
        self.min_bpr_k = float(min_bpr_k)
        self.min_implied_r = float(min_implied_r)

    @staticmethod
    def _compute_overlap_ratio(h: np.ndarray, l: np.ndarray) -> float:
        if len(h) < 3:
            return 0.0
        overlaps = np.maximum(0.0, np.minimum(h[1:], h[:-1]) - np.maximum(l[1:], l[:-1]))
        spans = np.maximum(h[1:] - l[1:], 1e-12)
        return float(np.mean(np.clip(overlaps / spans, 0.0, 1.0)))

    def detect_compression_vacuum(
        self,
        o: np.ndarray,
        h: np.ndarray,
        l: np.ndarray,
        c: np.ndarray,
        atr: np.ndarray,
        bar_idx: int,
        barriers_hi: List[float],
        barriers_lo: List[float],
        lookback: int = 24,
    ) -> Optional[CompressionVacuumSetup]:
        """Setup Physics A: Flat Liquidity Barrier + Slow Overlapping Compression Approach + Vacuum Snap."""
        if bar_idx < lookback + 3 or atr[bar_idx] <= 0:
            return None
        a_now = max(float(atr[bar_idx]), 1e-12)
        win_o = o[bar_idx - lookback:bar_idx + 1]
        win_h = h[bar_idx - lookback:bar_idx + 1]
        win_l = l[bar_idx - lookback:bar_idx + 1]
        win_c = c[bar_idx - lookback:bar_idx + 1]

        # Check bearish waterfall (ceiling barrier swept at bar_idx or bar_idx-1, snap down)
        if c[bar_idx] < o[bar_idx] and abs(c[bar_idx] - o[bar_idx]) >= 0.65 * a_now:
            sw_hi = max(float(h[bar_idx]), float(h[bar_idx - 1]))
            hit_barriers = [b for b in barriers_hi if sw_hi > b and float(c[bar_idx]) < b]
            if hit_barriers:
                barrier = min(hit_barriers, key=lambda b: abs(b - sw_hi))
                # Compression approach in prior 5..lookback-1 bars: rising lows & high overlap / low KER
                app_c = win_c[:-2]
                den = float(np.sum(np.abs(np.diff(app_c))))
                app_ker = abs(float(app_c[-1] - app_c[0])) / den if den > 1e-12 else 0.0
                overlap = self._compute_overlap_ratio(win_h[:-2], win_l[:-2])
                origin_idx = int(np.argmin(win_l[:-4]))
                origin_px = float(win_l[origin_idx])
                # Rising lows check: second half lows higher than origin
                mid_pt = min(len(win_l) - 3, max(origin_idx + 1, len(win_l) - 6))
                seg_l = win_l[mid_pt:-2]
                rising_lows = len(seg_l) > 0 and float(np.min(seg_l)) > origin_px + 0.4 * a_now
                # Nearest internal compression low to snap below
                snap_lvl = float(np.min(win_l[-6:-1]))
                if (app_ker <= self.max_approach_ker or overlap >= 0.36) and rising_lows and c[bar_idx] < snap_lvl:
                    sl_dist = (sw_hi + 0.20 * a_now) - float(c[bar_idx])
                    tgt_dist = float(c[bar_idx]) - origin_px
                    imp_r = tgt_dist / max(sl_dist, 1e-12)
                    vac_sc = float(np.clip(0.55 * overlap + 0.45 * (1.0 - min(app_ker, 1.0)), 0.0, 1.0))
                    if imp_r >= self.min_implied_r and 0.35 * a_now <= sl_dist <= 2.8 * a_now:
                        return CompressionVacuumSetup(
                            side=-1, barrier_px=float(barrier), sweep_extreme=sw_hi,
                            snap_level=snap_lvl, origin_anchor=origin_px,
                            approach_ker=app_ker, vacuum_score=vac_sc,
                            implied_r=imp_r, trigger_idx=bar_idx,
                        )

        # Check bullish waterfall (floor barrier swept at bar_idx or bar_idx-1, snap up)
        if c[bar_idx] > o[bar_idx] and abs(c[bar_idx] - o[bar_idx]) >= 0.65 * a_now:
            sw_lo = min(float(l[bar_idx]), float(l[bar_idx - 1]))
            hit_barriers = [b for b in barriers_lo if sw_lo < b and float(c[bar_idx]) > b]
            if hit_barriers:
                barrier = min(hit_barriers, key=lambda b: abs(b - sw_lo))
                app_c = win_c[:-2]
                den = float(np.sum(np.abs(np.diff(app_c))))
                app_ker = abs(float(app_c[-1] - app_c[0])) / den if den > 1e-12 else 0.0
                overlap = self._compute_overlap_ratio(win_h[:-2], win_l[:-2])
                origin_idx = int(np.argmax(win_h[:-4]))
                origin_px = float(win_h[origin_idx])
                mid_pt = min(len(win_h) - 3, max(origin_idx + 1, len(win_h) - 6))
                seg_h = win_h[mid_pt:-2]
                falling_highs = len(seg_h) > 0 and float(np.max(seg_h)) < origin_px - 0.4 * a_now
                snap_lvl = float(np.max(win_h[-6:-1]))
                if (app_ker <= self.max_approach_ker or overlap >= 0.36) and falling_highs and c[bar_idx] > snap_lvl:
                    sl_dist = float(c[bar_idx]) - (sw_lo - 0.20 * a_now)
                    tgt_dist = origin_px - float(c[bar_idx])
                    imp_r = tgt_dist / max(sl_dist, 1e-12)
                    vac_sc = float(np.clip(0.55 * overlap + 0.45 * (1.0 - min(app_ker, 1.0)), 0.0, 1.0))
                    if imp_r >= self.min_implied_r and 0.35 * a_now <= sl_dist <= 2.8 * a_now:
                        return CompressionVacuumSetup(
                            side=1, barrier_px=float(barrier), sweep_extreme=sw_lo,
                            snap_level=snap_lvl, origin_anchor=origin_px,
                            approach_ker=app_ker, vacuum_score=vac_sc,
                            implied_r=imp_r, trigger_idx=bar_idx,
                        )
        return None

    def detect_bpr_ifvg(
        self,
        o: np.ndarray,
        h: np.ndarray,
        l: np.ndarray,
        c: np.ndarray,
        atr: np.ndarray,
        bar_idx: int,
        barriers_hi: List[float],
        barriers_lo: List[float],
        lookback_manip: int = 8,
    ) -> Optional[BPRZone]:
        """Setup Physics B: Liquidity Sweep + Manipulation FVG inverted by high-K reversal FVG (BPR/iFVG)."""
        if bar_idx < lookback_manip + 4 or atr[bar_idx] <= 0:
            return None
        a_now = max(float(atr[bar_idx]), 1e-12)

        # Check bullish reversal FVG at bar_idx (l[bar_idx] > h[bar_idx-2]) inverting a recent bearish FVG into a floor sweep
        if l[bar_idx] > h[bar_idx - 2] and (l[bar_idx] - h[bar_idx - 2]) >= 0.20 * a_now and c[bar_idx - 1] > o[bar_idx - 1]:
            rev_lo, rev_hi = float(h[bar_idx - 2]), float(l[bar_idx])
            win_lo = float(np.min(l[bar_idx - lookback_manip:bar_idx]))
            if any(win_lo < b for b in barriers_lo):
                # Search prior manipulation bearish FVG in [bar_idx - lookback_manip .. bar_idx - 2]
                for m in range(bar_idx - 2, max(2, bar_idx - lookback_manip), -1):
                    if h[m] < l[m - 2] and (l[m - 2] - h[m]) >= 0.15 * a_now:
                        man_lo, man_hi = float(h[m]), float(l[m - 2])
                        bpr_lo, bpr_hi = max(rev_lo, man_lo), min(rev_hi, man_hi)
                        if bpr_hi > bpr_lo:
                            k_vel, _, _ = KinematicMonitor.compute_kinematic_ratio(o, h, l, c, atr, m - 2, m, bar_idx)
                            # Reversal velocity vs manipulation velocity
                            v_rev = abs(float(c[bar_idx]) - win_lo) / max(1, bar_idx - m)
                            v_man = abs(float(c[m]) - float(o[m - 2])) / 2.0
                            k_inv = v_rev / max(v_man, 1e-12)
                            if k_inv >= self.min_bpr_k or k_vel >= self.min_bpr_k:
                                vac = float(np.clip((bpr_hi - bpr_lo) / a_now, 0.0, 1.0))
                                return BPRZone(1, bpr_lo, bpr_hi, 0.5 * (bpr_lo + bpr_hi), win_lo, bar_idx, max(k_inv, k_vel), vac)

        # Check bearish reversal FVG at bar_idx (h[bar_idx] < l[bar_idx-2]) inverting a recent bullish FVG into a ceiling sweep
        if h[bar_idx] < l[bar_idx - 2] and (l[bar_idx - 2] - h[bar_idx]) >= 0.20 * a_now and c[bar_idx - 1] < o[bar_idx - 1]:
            rev_lo, rev_hi = float(h[bar_idx]), float(l[bar_idx - 2])
            win_hi = float(np.max(h[bar_idx - lookback_manip:bar_idx]))
            if any(win_hi > b for b in barriers_hi):
                for m in range(bar_idx - 2, max(2, bar_idx - lookback_manip), -1):
                    if l[m] > h[m - 2] and (l[m] - h[m - 2]) >= 0.15 * a_now:
                        man_lo, man_hi = float(h[m - 2]), float(l[m])
                        bpr_lo, bpr_hi = max(rev_lo, man_lo), min(rev_hi, man_hi)
                        if bpr_hi > bpr_lo:
                            v_rev = abs(win_hi - float(c[bar_idx])) / max(1, bar_idx - m)
                            v_man = abs(float(c[m]) - float(o[m - 2])) / 2.0
                            k_inv = v_rev / max(v_man, 1e-12)
                            if k_inv >= self.min_bpr_k:
                                vac = float(np.clip((bpr_hi - bpr_lo) / a_now, 0.0, 1.0))
                                return BPRZone(-1, bpr_lo, bpr_hi, 0.5 * (bpr_lo + bpr_hi), win_hi, bar_idx, k_inv, vac)
        return None


