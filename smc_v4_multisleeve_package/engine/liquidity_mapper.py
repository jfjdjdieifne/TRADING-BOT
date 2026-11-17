"""Institutional Time-Based & Topological Liquidity Pool Mapper."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

from .perception_engine import TopologicalSwing, VisualPerceptionEngine, gaussian_rbf, sigmoid


@dataclass
class LiquidityPool:
    pool_id: str
    tier: int  # 1=PWH/PWL/PDH/PDL, 2=Session H/L, 3=Structural/EQH/EQL
    kind: str  # PWH, PWL, PDH, PDL, ASIA_H, ASIA_L, LONDON_H, LONDON_L, SWING_4H, SWING_1H, EQH, EQL
    side: int  # +1=buy-side liquidity (high), -1=sell-side liquidity (low)
    price: float
    created_bar: int
    weight: float  # Continuous weight in [0, 1]
    status: str = "UNTAPPED"  # UNTAPPED, SWEPT_WITH_REJECTION, BROKEN_WITH_DISPLACEMENT
    event_bar: Optional[int] = None
    sweep_extreme: Optional[float] = None
    sweep_score: float = 0.0


class LiquidityPoolMapper:
    """Maps and tracks institutional liquidity pools with zero lookahead."""

    TIER_BASE_WEIGHT = {1: 0.95, 2: 0.78, 3: 0.65}

    def __init__(self, perception: VisualPerceptionEngine, max_pools: int = 80) -> None:
        self.perception = perception
        self.max_pools = int(max_pools)
        self.pools: Dict[str, LiquidityPool] = {}
        self.bar_count = -1

        # Incremental causal calendar / session accumulators (strictly closed periods only)
        self._cur_week = None
        self._wk_hi = -np.inf
        self._wk_lo = np.inf
        self._cur_day = None
        self._dy_hi = -np.inf
        self._dy_lo = np.inf

        self._asia_day = None
        self._asia_hi = -np.inf
        self._asia_lo = np.inf
        self._asia_emitted = False

        self._lon_day = None
        self._lon_hi = -np.inf
        self._lon_lo = np.inf
        self._lon_emitted = False

    def _upsert(self, pool: LiquidityPool) -> None:
        if pool.pool_id in self.pools:
            return
        self.pools[pool.pool_id] = pool
        if len(self.pools) > self.max_pools:
            # Prune oldest broken/swept pools first, then lowest-weight oldest pools
            ordered = sorted(
                self.pools.values(),
                key=lambda p: (0 if p.status == "UNTAPPED" else 1, -p.weight, -p.created_bar),
            )
            keep = {p.pool_id: p for p in ordered[:self.max_pools]}
            self.pools = keep

    def update_calendar_and_sessions(self, ts_sec: float, h: float, l: float) -> None:
        """Update Tier 1 (PWH/PWL, PDH/PDL) & Tier 2 (Asia/London H/L) strictly on period close."""
        utc_dt = dt.datetime.fromtimestamp(ts_sec, tz=dt.timezone.utc)
        iso_wk = utc_dt.isocalendar()[:2]
        day = utc_dt.date()
        hr = utc_dt.hour

        # Weekly rollover -> emit completed Previous Week High / Low
        if self._cur_week is None:
            self._cur_week = iso_wk
        elif iso_wk != self._cur_week:
            if np.isfinite(self._wk_hi) and np.isfinite(self._wk_lo):
                wk_tag = f"{self._cur_week[0]}W{self._cur_week[1]}"
                self._upsert(LiquidityPool(f"PWH_{wk_tag}", 1, "PWH", 1, float(self._wk_hi), self.bar_count, 0.98))
                self._upsert(LiquidityPool(f"PWL_{wk_tag}", 1, "PWL", -1, float(self._wk_lo), self.bar_count, 0.98))
            self._cur_week = iso_wk
            self._wk_hi, self._wk_lo = -np.inf, np.inf
        self._wk_hi = max(self._wk_hi, h)
        self._wk_lo = min(self._wk_lo, l)

        # Daily rollover -> emit completed Previous Day High / Low
        if self._cur_day is None:
            self._cur_day = day
        elif day != self._cur_day:
            if np.isfinite(self._dy_hi) and np.isfinite(self._dy_lo):
                d_tag = self._cur_day.isoformat()
                self._upsert(LiquidityPool(f"PDH_{d_tag}", 1, "PDH", 1, float(self._dy_hi), self.bar_count, 0.92))
                self._upsert(LiquidityPool(f"PDL_{d_tag}", 1, "PDL", -1, float(self._dy_lo), self.bar_count, 0.92))
            self._cur_day = day
            self._dy_hi, self._dy_lo = -np.inf, np.inf
        self._dy_hi = max(self._dy_hi, h)
        self._dy_lo = min(self._dy_lo, l)

        # Asia session (00:00..07:59 UTC), emitted strictly once hour >= 8
        if self._asia_day != day:
            self._asia_day = day
            self._asia_hi, self._asia_lo = -np.inf, np.inf
            self._asia_emitted = False
        if hr < 8:
            self._asia_hi = max(self._asia_hi, h)
            self._asia_lo = min(self._asia_lo, l)
        elif not self._asia_emitted and np.isfinite(self._asia_hi) and np.isfinite(self._asia_lo):
            d_tag = day.isoformat()
            self._upsert(LiquidityPool(f"ASIA_H_{d_tag}", 2, "ASIA_H", 1, float(self._asia_hi), self.bar_count, 0.80))
            self._upsert(LiquidityPool(f"ASIA_L_{d_tag}", 2, "ASIA_L", -1, float(self._asia_lo), self.bar_count, 0.80))
            self._asia_emitted = True

        # London session (08:00..12:59 UTC), emitted strictly once hour >= 13
        if self._lon_day != day:
            self._lon_day = day
            self._lon_hi, self._lon_lo = -np.inf, np.inf
            self._lon_emitted = False
        if 8 <= hr < 13:
            self._lon_hi = max(self._lon_hi, h)
            self._lon_lo = min(self._lon_lo, l)
        elif hr >= 13 and not self._lon_emitted and np.isfinite(self._lon_hi) and np.isfinite(self._lon_lo):
            d_tag = day.isoformat()
            self._upsert(LiquidityPool(f"LONDON_H_{d_tag}", 2, "LONDON_H", 1, float(self._lon_hi), self.bar_count, 0.78))
            self._upsert(LiquidityPool(f"LONDON_L_{d_tag}", 2, "LONDON_L", -1, float(self._lon_lo), self.bar_count, 0.78))
            self._lon_emitted = True

    def ingest_structural_swings(
        self,
        swings: List[TopologicalSwing],
        low_arr: np.ndarray,
        high_arr: np.ndarray,
        atr_val: float,
        tf_label: str = "4H",
    ) -> None:
        """Ingest confirmed topological swings and detect Valley-Depth EQH/EQL clusters."""
        tf_mult = 0.90 if tf_label == "4H" else 0.72
        for s in swings:
            if s.mitigated:
                continue
            pid = f"SW_{tf_label}_{s.side}_{s.idx}"
            w = float(np.clip(s.structural_weight * tf_mult, 0.15, 0.95))
            self._upsert(LiquidityPool(pid, 3, f"SWING_{tf_label}", s.side, s.price, self.bar_count, w))

        # Topological EQH / EQL cluster detection via Valley-Depth Gaussian Kernel
        for side in (1, -1):
            cands = [s for s in swings[-16:] if s.side == side and not s.mitigated]
            for a_i in range(len(cands)):
                for b_i in range(a_i + 1, len(cands)):
                    s1, s2 = cands[a_i], cands[b_i]
                    if s2.idx - s1.idx < 2:
                        continue
                    lo_slice = low_arr[s1.idx:s2.idx + 1]
                    hi_slice = high_arr[s1.idx:s2.idx + 1]
                    if len(lo_slice) == 0:
                        continue
                    valley = float(np.min(lo_slice)) if side == 1 else float(np.max(hi_slice))
                    eq_score = self.perception.visual_eqh_eql_score(s1, s2, valley, atr_val)
                    if eq_score >= 0.45:
                        kind = "EQH" if side == 1 else "EQL"
                        px = max(s1.price, s2.price) if side == 1 else min(s1.price, s2.price)
                        pid = f"{kind}_{tf_label}_{s1.idx}_{s2.idx}"
                        w = float(np.clip(0.55 + 0.38 * eq_score, 0.45, 0.95))
                        self._upsert(LiquidityPool(pid, 3, kind, side, float(px), self.bar_count, w))

    def step_bar(self, ts_sec: float, o: float, h: float, l: float, c: float, atr: float) -> List[LiquidityPool]:
        """Advance pool state machine for one closed bar and return pools triggered on this bar."""
        self.bar_count += 1
        self.update_calendar_and_sessions(ts_sec, h, l)
        triggered: List[LiquidityPool] = []
        if atr <= 0:
            return triggered

        disp = self.perception.displacement_score(o, h, l, c, atr)
        for p in self.pools.values():
            if p.status != "UNTAPPED":
                continue
            if p.side == 1 and h > p.price:
                if c < p.price:
                    rej = self.perception.rejection_wick_score(o, h, l, c, side=-1, atr=atr)
                    pen = float(gaussian_rbf((h - p.price) / atr, 0.85))
                    p.status = "SWEPT_WITH_REJECTION"
                    p.event_bar = self.bar_count
                    p.sweep_extreme = h
                    p.sweep_score = float(np.clip(p.weight * (0.55 * rej + 0.45 * pen), 0.0, 1.0))
                    triggered.append(p)
                else:
                    close_margin = float(sigmoid((c - p.price) / atr, x0=0.25, k=4.0))
                    if disp * close_margin >= 0.35:
                        p.status = "BROKEN_WITH_DISPLACEMENT"
                        p.event_bar = self.bar_count
                        p.sweep_extreme = h
                        p.sweep_score = float(np.clip(p.weight * disp, 0.0, 1.0))
                        triggered.append(p)
                    else:
                        # Marginal close above -> treat as weak sweep/absorption if next bar rejects, mark broken for safety
                        p.status = "BROKEN_WITH_DISPLACEMENT"
                        p.event_bar = self.bar_count
                        p.sweep_extreme = h
                        p.sweep_score = float(np.clip(p.weight * 0.30, 0.0, 1.0))
            elif p.side == -1 and l < p.price:
                if c > p.price:
                    rej = self.perception.rejection_wick_score(o, h, l, c, side=1, atr=atr)
                    pen = float(gaussian_rbf((p.price - l) / atr, 0.85))
                    p.status = "SWEPT_WITH_REJECTION"
                    p.event_bar = self.bar_count
                    p.sweep_extreme = l
                    p.sweep_score = float(np.clip(p.weight * (0.55 * rej + 0.45 * pen), 0.0, 1.0))
                    triggered.append(p)
                else:
                    close_margin = float(sigmoid((p.price - c) / atr, x0=0.25, k=4.0))
                    if disp * close_margin >= 0.35:
                        p.status = "BROKEN_WITH_DISPLACEMENT"
                        p.event_bar = self.bar_count
                        p.sweep_extreme = l
                        p.sweep_score = float(np.clip(p.weight * disp, 0.0, 1.0))
                        triggered.append(p)
                    else:
                        p.status = "BROKEN_WITH_DISPLACEMENT"
                        p.event_bar = self.bar_count
                        p.sweep_extreme = l
                        p.sweep_score = float(np.clip(p.weight * 0.30, 0.0, 1.0))
        return triggered

    def recent_swept_pools(self, reversal_side: int, max_age_bars: int = 12) -> List[LiquidityPool]:
        """Return pools recently SWEPT_WITH_REJECTION aligned with `reversal_side` (+1 -> swept low, -1 -> swept high)."""
        pool_side = -1 if reversal_side == 1 else 1
        out = [
            p for p in self.pools.values()
            if p.status == "SWEPT_WITH_REJECTION"
            and p.side == pool_side
            and p.event_bar is not None
            and (self.bar_count - p.event_bar) <= max_age_bars
        ]
        return sorted(out, key=lambda x: x.sweep_score, reverse=True)

    def nearest_opposing_pool(
        self,
        price: float,
        trade_side: int,
        min_tier: int = 3,
    ) -> Optional[LiquidityPool]:
        """Find nearest UNTAPPED opposing liquidity pool ahead of `price`."""
        target_side = 1 if trade_side == 1 else -1
        cands = [
            p for p in self.pools.values()
            if p.status == "UNTAPPED"
            and p.side == target_side
            and p.tier <= min_tier
            and ((p.price > price) if trade_side == 1 else (p.price < price))
        ]
        if not cands:
            return None
        return min(cands, key=lambda p: abs(p.price - price))
