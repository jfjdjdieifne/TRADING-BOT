"""Hybrid Multi-Timeframe Institutional State Machine, Confluence Tensor & Risk-Free Pyramiding."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .exit_manager import (
    AdaptiveExitManager,
    ProtectedSwingDetector,
    TradePositionState,
)
from .liquidity_mapper import LiquidityPoolMapper
from .perception_engine import (
    TopologicalSwing,
    VisualPerceptionEngine,
    compute_atr_series,
    sigmoid,
    soft_and_log_odds,
)
from .regime_filter import RegimeFilterEngine


@dataclass
class POIZone:
    poi_id: str
    side: int
    low: float
    high: float
    mid: float
    created_bar: int
    weight: float
    mitigated: bool = False


@dataclass
class PendingLTFOrder:
    side: int
    entry_px: float
    sl_px: float
    risk_dist: float
    created_bar: int
    expires_bar: int
    confluence_score: float
    is_pyramid: bool = False
    tag: str = ""


@dataclass
class LTFMonitorContext:
    side: int
    started_bar: int
    expires_bar: int
    sweep_extreme: float
    sweep_score: float
    htf_bias_score: float
    source_tag: str


class InstitutionalStrategyBrain:
    """State-machine coordinator: Visual Perception + Liquidity + Regime Tensor + Risk-Free Pyramiding."""

    def __init__(
        self,
        confluence_threshold: float = 0.50,
        sl_min_pct: float = 0.0050,
        sl_max_pct: float = 0.0800,
        pyramid_arm_r: float = 2.0,
        trail_atr_mult: float = 3.5,
    ) -> None:
        self.perception = VisualPerceptionEngine()
        self.liq_mapper = LiquidityPoolMapper(self.perception)
        self.regime = RegimeFilterEngine()
        self.exit_mgr = AdaptiveExitManager()
        self.prot_1h = ProtectedSwingDetector()
        self.prot_15m = ProtectedSwingDetector()

        self.confluence_threshold = float(confluence_threshold)
        self.sl_min_pct = float(sl_min_pct)
        self.sl_max_pct = float(sl_max_pct)
        self.pyramid_arm_r = float(pyramid_arm_r)
        self.trail_atr_mult = float(trail_atr_mult)

        self.state = "SCANNING_4H"
        self.monitor_ctx: Optional[LTFMonitorContext] = None
        self.pending_order: Optional[PendingLTFOrder] = None
        self.positions: List[TradePositionState] = []
        self.closed_trades: List[dict] = []
        self.pois_4h: List[POIZone] = []
        self._next_trade_id = 1

    @staticmethod
    def compute_adx_series(high: np.ndarray, low: np.ndarray, atr: np.ndarray, period: int = 14) -> np.ndarray:
        up = np.diff(high, prepend=high[0])
        dn = -np.diff(low, prepend=low[0])
        pdm = np.where((up > dn) & (up > 0), up, 0.0)
        mdm = np.where((dn > up) & (dn > 0), dn, 0.0)
        atr_s = np.maximum(atr, 1e-12)
        pdi = 100.0 * pd.Series(pdm).ewm(alpha=1.0 / period, adjust=False).mean().to_numpy(float) / atr_s
        mdi = 100.0 * pd.Series(mdm).ewm(alpha=1.0 / period, adjust=False).mean().to_numpy(float) / atr_s
        dx = 100.0 * np.abs(pdi - mdi) / np.maximum(pdi + mdi, 1e-12)
        return pd.Series(dx).ewm(alpha=1.0 / period, adjust=False).mean().fillna(0.0).to_numpy(float)

    @staticmethod
    def _htf_bias_score(
        swings_4h: List[TopologicalSwing],
        ema20_1d: float,
        ema50_1d: float,
        atr_4h: float,
        side: int,
    ) -> float:
        """Continuous HTF directional bias score in [0, 1] combining 1D macro EMA + 4H topological swings."""
        s_macro = float(sigmoid(((ema20_1d - ema50_1d) / max(atr_4h, 1e-12)) * side, x0=0.0, k=0.8))
        hi_sw = [s for s in swings_4h if s.side == 1][-2:]
        lo_sw = [s for s in swings_4h if s.side == -1][-2:]
        s_struct = 0.5
        if len(hi_sw) == 2 and len(lo_sw) == 2:
            hh = hi_sw[-1].price > hi_sw[-2].price
            hl = lo_sw[-1].price > lo_sw[-2].price
            lh = hi_sw[-1].price < hi_sw[-2].price
            ll = lo_sw[-1].price < lo_sw[-2].price
            if side == 1:
                s_struct = 0.90 if (hh and hl) else (0.65 if (hh or hl) else 0.20)
            else:
                s_struct = 0.90 if (lh and ll) else (0.65 if (lh or ll) else 0.20)
        return float(np.clip(0.55 * s_macro + 0.45 * s_struct, 0.0, 1.0))

    def _update_4h_pois(self, b_idx: int, o: np.ndarray, h: np.ndarray, l: np.ndarray, c: np.ndarray, atr: np.ndarray) -> None:
        if b_idx < 3:
            return
        a = max(float(atr[b_idx - 1]), 1e-12)
        if l[b_idx] > h[b_idx - 2] and c[b_idx - 1] > o[b_idx - 1]:
            gap = float(l[b_idx] - h[b_idx - 2])
            w = self.perception.fvg_quality_score(gap, a)
            if w >= 0.35:
                zlo, zhi = min(float(h[b_idx - 2]), float(l[b_idx - 1])), float(l[b_idx])
                self.pois_4h.append(POIZone(f"POI4H_B_{b_idx}", 1, zlo, zhi, 0.5 * (zlo + zhi), b_idx, w))
        if h[b_idx] < l[b_idx - 2] and c[b_idx - 1] < o[b_idx - 1]:
            gap = float(l[b_idx - 2] - h[b_idx])
            w = self.perception.fvg_quality_score(gap, a)
            if w >= 0.35:
                zlo, zhi = float(h[b_idx]), max(float(l[b_idx - 2]), float(h[b_idx - 1]))
                self.pois_4h.append(POIZone(f"POI4H_S_{b_idx}", -1, zlo, zhi, 0.5 * (zlo + zhi), b_idx, w))
        cur_l, cur_h = float(l[b_idx]), float(h[b_idx])
        self.pois_4h = [
            pz for pz in self.pois_4h[-24:]
            if (b_idx - pz.created_bar) <= 60 and not ((pz.side == 1 and cur_l < pz.low) or (pz.side == -1 and cur_h > pz.high))
        ]


def run_v5_causal_backtest(
    df_5m: pd.DataFrame,
    eval_start: pd.Timestamp,
    eval_end: pd.Timestamp,
    mode: str = "4h_hybrid",
    confluence_threshold: Optional[float] = None,
    use_pyramid: bool = True,
    fee_mult: float = 1.0,
) -> Tuple[List[dict], Dict[str, float]]:
    """Run strictly causal V5 backtest (`4h_hybrid` or `4h_topological`) with zero lookahead bias."""
    if mode not in ("4h_hybrid", "4h_topological"):
        raise ValueError(f"Unsupported V5 mode: {mode}")

    thr = float(confluence_threshold if confluence_threshold is not None else (0.50 if mode == "4h_hybrid" else 0.55))

    df4h = df_5m.resample("4h").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}).dropna()
    df1d = df_5m.resample("1D").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}).dropna()

    o4, h4, l4, c4 = (df4h[col].to_numpy(float) for col in ("Open", "High", "Low", "Close"))
    ts4_ns = df4h.index.as_unit("ns").asi8
    ts4_sec = ts4_ns / 1e9
    close4_ns = ts4_ns + int(14400 * 1e9)
    atr4 = compute_atr_series(h4, l4, c4, 14)

    c1d = df1d["Close"].to_numpy(float)
    ts1d_ns = df1d.index.as_unit("ns").asi8
    close1d_ns = ts1d_ns + int(86400 * 1e9)
    e20_1d = pd.Series(c1d).ewm(span=20, adjust=False).mean().to_numpy(float)
    e50_1d = pd.Series(c1d).ewm(span=50, adjust=False).mean().to_numpy(float)

    brain = InstitutionalStrategyBrain(confluence_threshold=thr)
    reg_4 = brain.regime.precompute_frame_features(df4h)
    adx4 = brain.compute_adx_series(h4, l4, atr4, 14)

    sw4 = brain.perception.detect_causal_swings(ts4_ns, h4, l4, c4, atr4, max_swings=6000)
    sw4_by_conf: Dict[int, List[TopologicalSwing]] = {}
    for s in sw4:
        sw4_by_conf.setdefault(s.confirm_idx, []).append(s)

    hi20 = pd.Series(h4).rolling(20).max().shift(1).to_numpy(float)
    lo20 = pd.Series(l4).rolling(20).min().shift(1).to_numpy(float)

    p1d = 0
    vis4: List[TopologicalSwing] = []
    cur_top_hi: Optional[float] = None
    cur_top_lo: Optional[float] = None
    cool = 0
    cid = 0
    eval0_ns = int(eval_start.as_unit("ns").value)
    eval1_ns = int(eval_end.as_unit("ns").value)

    for i4 in range(60, len(df4h)):
        c_ns = int(close4_ns[i4])
        if c_ns >= eval1_ns:
            break
        while p1d < len(df1d) and close1d_ns[p1d] <= c_ns:
            p1d += 1
        if i4 in sw4_by_conf:
            for s in sw4_by_conf[i4]:
                vis4.append(s)
                if s.side == 1:
                    cur_top_hi = s.price
                else:
                    cur_top_lo = s.price
            vis4 = vis4[-40:]
            brain.liq_mapper.ingest_structural_swings(vis4, l4[:i4 + 1], h4[:i4 + 1], float(atr4[i4]), "4H")
        brain._update_4h_pois(i4, o4, h4, l4, c4, atr4)
        brain.liq_mapper.step_bar(float(ts4_sec[i4]), float(o4[i4]), float(h4[i4]), float(l4[i4]), float(c4[i4]), float(atr4[i4]))

        if p1d < 50 or c_ns < eval0_ns:
            continue

        # 1) Manage active positions (Chandelier 3.5*ATR4 + Risk-Free Pyramid Arming)
        still: List[TradePositionState] = []
        for pos in brain.positions:
            if (pos.side == 1 and l4[i4] <= pos.cur_sl) or (pos.side == -1 and h4[i4] >= pos.cur_sl):
                gr = (((pos.cur_sl - pos.entry_price) * pos.side) / pos.risk_dist) * pos.risk_mult
                hrs = max(4.0, (i4 - pos.entry_bar) * 4.0)
                cost = fee_mult * ((0.0005 + 0.0008 + 0.0001 * (hrs / 8.0)) / (pos.risk_dist / pos.entry_price)) * pos.risk_mult
                brain.closed_trades.append({
                    "cluster_id": pos.trade_id,
                    "entry_time": pos.entry_ts,
                    "exit_time": pd.Timestamp(c_ns, tz="UTC"),
                    "side": pos.side,
                    "entry_price": pos.entry_price,
                    "init_sl": pos.init_sl,
                    "sl_pct": pos.risk_dist / pos.entry_price,
                    "gross_r": gr,
                    "net_r": gr - cost,
                    "is_pyramid": pos.is_pyramid,
                    "outcome": "TRAIL_SL" if (pos.cur_sl - pos.entry_price) * pos.side > 0 else "SL",
                })
                cool = i4 + 1
                continue

            pos.best_px = max(pos.best_px, float(h4[i4])) if pos.side == 1 else min(pos.best_px, float(l4[i4]))
            pos.peak_mfe_r = max(pos.peak_mfe_r, ((pos.best_px - pos.entry_price) * pos.side) / pos.risk_dist)
            trail_cand = (pos.best_px - brain.trail_atr_mult * float(atr4[i4])) if pos.side == 1 else (pos.best_px + brain.trail_atr_mult * float(atr4[i4]))
            if (pos.side == 1 and trail_cand > pos.cur_sl) or (pos.side == -1 and trail_cand < pos.cur_sl):
                pos.cur_sl = trail_cand

            if use_pyramid and (not pos.is_pyramid) and (not pos.pyramid_done) and pos.peak_mfe_r >= brain.pyramid_arm_r:
                lk = pos.entry_price + pos.side * 0.25 * pos.risk_dist
                if (pos.side == 1 and lk > pos.cur_sl) or (pos.side == -1 and lk < pos.cur_sl):
                    pos.cur_sl = lk
                pos.be_moved = True
                pos.pyramid_armed = True
            still.append(pos)
        brain.positions = still

        # 2) Risk-Free Pyramid Scale-In on pullback continuation
        if use_pyramid and len(brain.positions) == 1 and brain.positions[0].pyramid_armed and not brain.positions[0].pyramid_done:
            p0 = brain.positions[0]
            pb = (
                (p0.side == 1 and l4[i4] <= c4[i4 - 1] and c4[i4] > o4[i4] and c4[i4] > p0.entry_price)
                or (p0.side == -1 and h4[i4] >= c4[i4 - 1] and c4[i4] < o4[i4] and c4[i4] < p0.entry_price)
            )
            if pb:
                sl_p = float(c4[i4]) - p0.side * 1.5 * float(atr4[i4])
                p0.pyramid_done = True
                brain.positions.append(
                    TradePositionState(
                        trade_id=p0.trade_id, side=p0.side, entry_bar=i4,
                        entry_ts=pd.Timestamp(c_ns, tz="UTC"), entry_price=float(c4[i4]),
                        init_sl=sl_p, cur_sl=sl_p, risk_dist=abs(float(c4[i4]) - sl_p),
                        risk_mult=0.5, is_pyramid=True,
                    )
                )
                continue

        if brain.positions or i4 < cool:
            continue

        # 3) Entry Signal: 4H Macro + Breakout/Topological BOS + Compensatory Confluence Tensor
        d1_tr = 1 if e20_1d[p1d - 1] > e50_1d[p1d - 1] else -1
        side = 0
        if mode == "4h_hybrid" and not np.isnan(hi20[i4]):
            if d1_tr == 1 and c4[i4] > hi20[i4] and c4[i4 - 1] <= hi20[i4 - 1] and adx4[i4] >= 20.0:
                side = 1
            elif d1_tr == -1 and c4[i4] < lo20[i4] and c4[i4 - 1] >= lo20[i4 - 1] and adx4[i4] >= 20.0:
                side = -1
        elif mode == "4h_topological":
            if d1_tr == 1 and cur_top_hi is not None and c4[i4] > cur_top_hi and c4[i4 - 1] <= cur_top_hi:
                side = 1
            elif d1_tr == -1 and cur_top_lo is not None and c4[i4] < cur_top_lo and c4[i4 - 1] >= cur_top_lo:
                side = -1
        if side == 0:
            continue

        rs = brain.regime.evaluate_bar(reg_4, i4)
        disp_sc = brain.perception.displacement_score(float(o4[i4]), float(h4[i4]), float(l4[i4]), float(c4[i4]), float(atr4[i4]))
        adx_sc = float(sigmoid(adx4[i4], x0=18.0, k=0.25))
        conf = soft_and_log_odds(
            {"ker": rs.ker_score, "er": rs.effort_result_score, "sq": rs.squeeze_score, "disp": disp_sc, "adx": adx_sc},
            {"ker": 1.0, "er": 1.0, "sq": 0.6, "disp": 1.0, "adx": 1.2},
            veto_floors={"ker": 0.12},
        )
        if conf < thr or rs.absorption_trap_score >= 0.78:
            continue

        ep = float(c4[i4])
        slp = ep - side * 2.0 * float(atr4[i4])
        rd = abs(ep - slp)
        if not (brain.sl_min_pct <= (rd / ep) <= brain.sl_max_pct):
            continue
        cid += 1
        brain.positions.append(
            TradePositionState(
                trade_id=cid, side=side, entry_bar=i4,
                entry_ts=pd.Timestamp(c_ns, tz="UTC"), entry_price=ep,
                init_sl=slp, cur_sl=slp, risk_dist=rd,
            )
        )

    all_r = [t["net_r"] for t in brain.closed_trades]
    is_r = [t["net_r"] for t in brain.closed_trades if t["entry_time"].year <= 2023]
    oos_r = [t["net_r"] for t in brain.closed_trades if t["entry_time"].year >= 2024]
    def _stats(arr: List[float]) -> Dict[str, float]:
        if not arr:
            return {"n": 0, "wr": 0.0, "net": 0.0, "pf": 0.0}
        gp = sum(x for x in arr if x > 0)
        gl = -sum(x for x in arr if x < 0)
        return {"n": len(arr), "wr": 100.0 * sum(1 for x in arr if x > 0) / len(arr), "net": sum(arr), "pf": gp / gl if gl > 0 else 99.0}

    cum = np.cumsum(all_r) if all_r else np.array([0.0])
    pk = np.maximum.accumulate(np.insert(cum, 0, 0.0))[1:]
    dd = float(np.max(pk - cum)) if all_r else 0.0
    by_cl: Dict[int, float] = {}
    for t in brain.closed_trades:
        by_cl[t["cluster_id"]] = by_cl.get(t["cluster_id"], 0.0) + t["net_r"]
    cl_vals = list(by_cl.values())
    summary = {
        "all": _stats(all_r),
        "is": _stats(is_r),
        "oos": _stats(oos_r),
        "max_dd_r": dd,
        "cluster_max_r": max(cl_vals, default=0.0),
        "clusters_ge_10r": sum(1 for v in cl_vals if v >= 10.0),
    }
    return brain.closed_trades, summary
