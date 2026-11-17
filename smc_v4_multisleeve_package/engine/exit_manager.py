"""Adaptive 3-Phase Hybrid Exit Engine & Confirmed Protected Swing Detector."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

from .perception_engine import TopologicalSwing, sigmoid


@dataclass
class ProtectedSwing:
    idx: int
    bos_idx: int
    side: int  # -1=protected low (trail floor for Longs), +1=protected high (trail ceiling for Shorts)
    price: float


class ProtectedSwingDetector:
    """Identifies causal Protected Swings: swings validated by a subsequent candle-close BOS."""

    def __init__(self) -> None:
        self.last_confirmed_hi: Optional[TopologicalSwing] = None
        self.last_confirmed_lo: Optional[TopologicalSwing] = None
        self.pending_low_candidate: Optional[TopologicalSwing] = None
        self.pending_high_candidate: Optional[TopologicalSwing] = None
        self.protected_lows: List[ProtectedSwing] = []
        self.protected_highs: List[ProtectedSwing] = []

    def update(self, bar_idx: int, close_px: float, new_swings: List[TopologicalSwing]) -> None:
        """Register confirmed swings and promote to Protected only upon candle-close BOS."""
        for sw in new_swings:
            if sw.side == 1:
                self.last_confirmed_hi = sw
                if self.pending_high_candidate is None or sw.price >= self.pending_high_candidate.price:
                    self.pending_high_candidate = sw
            else:
                self.last_confirmed_lo = sw
                if self.pending_low_candidate is None or sw.price <= self.pending_low_candidate.price:
                    self.pending_low_candidate = sw

        # Bullish BOS (candle close > prior confirmed swing high) protects the origin swing low
        if (
            self.last_confirmed_hi is not None
            and self.pending_low_candidate is not None
            and close_px > self.last_confirmed_hi.price
            and self.pending_low_candidate.idx > self.last_confirmed_hi.idx - 25
        ):
            ps = ProtectedSwing(
                idx=self.pending_low_candidate.idx,
                bos_idx=bar_idx,
                side=-1,
                price=self.pending_low_candidate.price,
            )
            if not self.protected_lows or ps.idx > self.protected_lows[-1].idx:
                self.protected_lows.append(ps)
                self.protected_lows = self.protected_lows[-20:]
            self.pending_low_candidate = None

        # Bearish BOS (candle close < prior confirmed swing low) protects the origin swing high
        if (
            self.last_confirmed_lo is not None
            and self.pending_high_candidate is not None
            and close_px < self.last_confirmed_lo.price
            and self.pending_high_candidate.idx > self.last_confirmed_lo.idx - 25
        ):
            ps = ProtectedSwing(
                idx=self.pending_high_candidate.idx,
                bos_idx=bar_idx,
                side=1,
                price=self.pending_high_candidate.price,
            )
            if not self.protected_highs or ps.idx > self.protected_highs[-1].idx:
                self.protected_highs.append(ps)
                self.protected_highs = self.protected_highs[-20:]
            self.pending_high_candidate = None

    def latest_floor_or_ceiling(self, trade_side: int) -> Optional[ProtectedSwing]:
        if trade_side == 1:
            return self.protected_lows[-1] if self.protected_lows else None
        return self.protected_highs[-1] if self.protected_highs else None


@dataclass
class TradePositionState:
    trade_id: int
    side: int  # +1=Long, -1=Short
    entry_bar: int
    entry_ts: object
    entry_price: float
    init_sl: float
    cur_sl: float
    risk_dist: float
    qty_rem: float = 1.0  # Normalized remaining fraction (1.0 -> 0.72 after partial)
    risk_mult: float = 1.0  # 1.0 for primary trade, 0.5 for pyramid add-on
    is_pyramid: bool = False
    best_px: float = 0.0
    partial_taken: bool = False
    be_moved: bool = False
    phase3_active: bool = False
    realized_r: float = 0.0
    peak_mfe_r: float = 0.0
    entry_bos_count_1h: int = 0
    pyramid_armed: bool = False
    pyramid_done: bool = False
    pyramid_stage: int = 0  # 0=base, 1=stage1_0.5x, 2=stage2_0.35x
    exit_reason: str = ""
    meta: Dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.best_px == 0.0:
            self.best_px = self.entry_price


class AdaptiveExitManager:
    """3-Phase Hybrid Exit Manager + V6 2-Stage Pyramiding & Climax Elastic Ratchet."""

    def __init__(
        self,
        be_trigger_r: float = 3.0,
        partial_frac: float = 0.28,
        partial_min_r: float = 4.0,
        partial_max_r: float = 6.0,
        ratchet_r: float = 8.0,
        climax_ratchet_r: float = 10.0,
        htf_prox_atr4h: float = 0.50,
    ) -> None:
        self.be_trigger_r = float(be_trigger_r)
        self.partial_frac = float(partial_frac)
        self.partial_min_r = float(partial_min_r)
        self.partial_max_r = float(partial_max_r)
        self.ratchet_r = float(ratchet_r)
        self.climax_ratchet_r = float(climax_ratchet_r)
        self.htf_prox_atr4h = float(htf_prox_atr4h)

    @staticmethod
    def elastic_atr_mult(rvol_1h: float, rsi_divergence: bool, base_mult: float = 3.0, min_mult: float = 1.2) -> float:
        """Smoothly decay chandelier multiplier from base_mult down to min_mult as climax volume/divergence builds."""
        climax = float(sigmoid(rvol_1h, x0=2.0, k=2.5))
        div_boost = 0.45 if rsi_divergence else 0.0
        exhaustion = float(np.clip(0.65 * climax + div_boost, 0.0, 1.0))
        return float(base_mult - (base_mult - min_mult) * exhaustion)

    @staticmethod
    def climax_ratchet_4h_mult(
        cluster_open_r: float,
        rvol_4h: float,
        has_climax_wick: bool,
        opposing_htf_swept: bool,
        base_mult: float = 3.5,
        ratchet_mult: float = 2.0,
    ) -> float:
        """Pillar 4 Climax Elastic Ratchet: tighten 4H Chandelier 3.5 -> 2.0*ATR at >=14R or climax pool sweep."""
        if cluster_open_r >= 14.0 or (opposing_htf_swept and rvol_4h >= 2.5 and has_climax_wick):
            return float(ratchet_mult)
        if cluster_open_r >= 10.0:
            t = (cluster_open_r - 10.0) / 4.0
            return float(base_mult - t * (base_mult - ratchet_mult))
        return float(base_mult)

    def step_position(
        self,
        pos: TradePositionState,
        bar_h: float,
        bar_l: float,
        bar_c: float,
        atr_1h: float,
        atr_4h: float,
        prot_1h: ProtectedSwingDetector,
        prot_15m: ProtectedSwingDetector,
        opposing_1h_liq_px: Optional[float],
        opposing_4h_liq_px: Optional[float],
        rvol_1h: float = 1.0,
        rsi_divergence: bool = False,
    ) -> Tuple[bool, float, str]:
        """Update one closed 5m/15m bar for `pos`. Returns (closed, realized_r_contrib, event_note)."""
        rd = pos.risk_dist
        if rd <= 0:
            return True, 0.0, "INVALID_RD"

        # 1) Check stop-loss hit first (conservative intrabar SL-first ordering)
        if pos.side == 1 and bar_l <= pos.cur_sl:
            r_rem = pos.qty_rem * ((pos.cur_sl - pos.entry_price) / rd)
            pos.realized_r += r_rem
            pos.qty_rem = 0.0
            pos.exit_reason = "TRAIL_SL" if pos.cur_sl > pos.entry_price else ("BE" if pos.be_moved else "SL")
            return True, pos.realized_r * pos.risk_mult, pos.exit_reason

        if pos.side == -1 and bar_h >= pos.cur_sl:
            r_rem = pos.qty_rem * ((pos.entry_price - pos.cur_sl) / rd)
            pos.realized_r += r_rem
            pos.qty_rem = 0.0
            pos.exit_reason = "TRAIL_SL" if pos.cur_sl < pos.entry_price else ("BE" if pos.be_moved else "SL")
            return True, pos.realized_r * pos.risk_mult, pos.exit_reason

        # Update MFE & best price
        fav_px = bar_h if pos.side == 1 else bar_l
        pos.best_px = max(pos.best_px, bar_h) if pos.side == 1 else min(pos.best_px, bar_l)
        cur_mfe_r = ((pos.best_px - pos.entry_price) / rd) if pos.side == 1 else ((pos.entry_price - pos.best_px) / rd)
        pos.peak_mfe_r = max(pos.peak_mfe_r, cur_mfe_r)
        cur_close_r = ((bar_c - pos.entry_price) / rd) if pos.side == 1 else ((pos.entry_price - bar_c) / rd)

        note = ""
        # 2) Phase 1: Break-Even upon +3R OR first new 1H BOS in our favor
        new_1h_bos = len(prot_1h.protected_lows if pos.side == 1 else prot_1h.protected_highs) > pos.entry_bos_count_1h
        if not pos.be_moved and (pos.peak_mfe_r >= self.be_trigger_r or (new_1h_bos and cur_close_r >= 1.2)):
            be_px = pos.entry_price + pos.side * 0.08 * rd
            if (pos.side == 1 and be_px > pos.cur_sl and be_px < bar_c) or (
                pos.side == -1 and be_px < pos.cur_sl and be_px > bar_c
            ):
                pos.cur_sl = be_px
                pos.be_moved = True
                note = "BE_LOCKED"

        # 3) Phase 1 Partial (25-30% at first major opposing 1H/Session Liquidity Pool in +4R..+6R zone)
        if not pos.partial_taken and pos.qty_rem > self.partial_frac:
            liq_hit = False
            liq_r = cur_mfe_r
            if opposing_1h_liq_px is not None:
                if (pos.side == 1 and bar_h >= opposing_1h_liq_px) or (pos.side == -1 and bar_l <= opposing_1h_liq_px):
                    opp_r = ((opposing_1h_liq_px - pos.entry_price) * pos.side) / rd
                    if opp_r >= self.partial_min_r:
                        liq_hit = True
                        liq_r = min(opp_r, self.partial_max_r)
            if not liq_hit and cur_mfe_r >= self.partial_max_r:
                liq_hit = True
                liq_r = self.partial_max_r
            if liq_hit:
                pos.realized_r += self.partial_frac * liq_r
                pos.qty_rem -= self.partial_frac
                pos.partial_taken = True
                note = f"PARTIAL_{liq_r:.1f}R"

        # 4) Phase 3 Activation check: >= +8R OR within 0.5*ATR_4H of opposing 4H/Daily pool
        near_htf = False
        if opposing_4h_liq_px is not None and atr_4h > 0:
            dist_htf = (opposing_4h_liq_px - bar_c) * pos.side
            if 0 <= dist_htf <= self.htf_prox_atr4h * atr_4h:
                near_htf = True
        if pos.peak_mfe_r >= self.ratchet_r or (near_htf and pos.peak_mfe_r >= 3.5):
            pos.phase3_active = True

        # 5) Phase 2 (1H Protected Swing Trail) & Phase 3 (15m Protected Swing + Elastic Chandelier)
        ps_1h = prot_1h.latest_floor_or_ceiling(pos.side)
        if ps_1h is not None and ps_1h.bos_idx > pos.entry_bar:
            buf = 0.15 * max(atr_1h, 0.0)
            cand = (ps_1h.price - buf) if pos.side == 1 else (ps_1h.price + buf)
            if (pos.side == 1 and cand > pos.cur_sl and cand < bar_c) or (
                pos.side == -1 and cand < pos.cur_sl and cand > bar_c
            ):
                pos.cur_sl = cand

        if pos.phase3_active:
            ps_15 = prot_15m.latest_floor_or_ceiling(pos.side)
            if ps_15 is not None and ps_15.bos_idx > pos.entry_bar:
                buf15 = 0.08 * max(atr_1h, 0.0)
                cand15 = (ps_15.price - buf15) if pos.side == 1 else (ps_15.price + buf15)
                if (pos.side == 1 and cand15 > pos.cur_sl and cand15 < bar_c) or (
                    pos.side == -1 and cand15 < pos.cur_sl and cand15 > bar_c
                ):
                    pos.cur_sl = cand15

            if atr_1h > 0:
                k_mult = self.elastic_atr_mult(rvol_1h, rsi_divergence)
                cand_el = (pos.best_px - k_mult * atr_1h) if pos.side == 1 else (pos.best_px + k_mult * atr_1h)
                if (pos.side == 1 and cand_el > pos.cur_sl and cand_el < bar_c) or (
                    pos.side == -1 and cand_el < pos.cur_sl and cand_el > bar_c
                ):
                    pos.cur_sl = cand_el

        # 6) Check Risk-Free Pyramiding Arming (+2.5R + confirmed 15m/1H protected swing)
        if (not pos.is_pyramid) and (not pos.pyramid_done) and (not pos.pyramid_armed) and pos.peak_mfe_r >= 2.5:
            ps_any = prot_15m.latest_floor_or_ceiling(pos.side) or prot_1h.latest_floor_or_ceiling(pos.side)
            if ps_any is not None and ps_any.bos_idx > pos.entry_bar:
                lock_px = pos.entry_price + pos.side * 0.20 * rd
                if (pos.side == 1 and lock_px > pos.cur_sl and lock_px < bar_c) or (
                    pos.side == -1 and lock_px < pos.cur_sl and lock_px > bar_c
                ):
                    pos.cur_sl = lock_px
                    pos.be_moved = True
                pos.pyramid_armed = True
                note = "PYRAMID_ARMED"

        return False, 0.0, note
