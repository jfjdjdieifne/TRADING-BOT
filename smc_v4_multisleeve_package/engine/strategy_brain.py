"""Hybrid Multi-Timeframe Institutional State Machine, Confluence Tensor & Risk-Free Pyramiding."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .exit_manager import (
    AdaptiveExitManager,
    HighVelocityCashflowExitManager,
    IntradayCashflowExitManager,
    ProtectedSwingDetector,
    TradePositionState,
    V10FrontLoadedCashflowExitManager,
    V11SessionEquilibriumExitManager,
)
from .liquidity_mapper import LiquidityPoolMapper
from .perception_engine import (
    BPRZone,
    CompressionVacuumSetup,
    DailySessionLiquidityTracker,
    KinematicMonitor,
    SceneGraphPhysicsDetector,
    SessionSweepSignal,
    TopologicalSwing,
    VisualPerceptionEngine,
    build_causal_topo_events,
    compute_atr_series,
    sigmoid,
    soft_and_log_odds,
)
from .regime_filter import RegimeFilterEngine


@dataclass
class ProsecutorVerdict:
    conviction: float
    thesis_logit: float
    contradiction_penalty: float
    brick_wall_penalty: float
    freight_train_veto: bool
    vol_divergence_penalty: float
    acceptance_status: str
    sweep_decay_score: float
    approved: bool
    reasoning_chain: Dict[str, object]


class AdversarialCrossExaminer:
    """V6 Pillar 3: Bayesian Prosecutor with Temporal Decay, Brick-Wall Clearance & Freight-Train Veto."""

    def __init__(
        self,
        grace_bars: int = 2,
        decay_lambda: float = 0.55,
        alpha_thesis: float = 2.4,
        beta_prosecutor: float = 2.6,
        theta_bias: float = 0.35,
        min_conviction: float = 0.52,
    ) -> None:
        self.grace_bars = int(grace_bars)
        self.decay_lambda = float(decay_lambda)
        self.alpha_thesis = float(alpha_thesis)
        self.beta_prosecutor = float(beta_prosecutor)
        self.theta_bias = float(theta_bias)
        self.min_conviction = float(min_conviction)

    def evaluate_temporal_sweep_decay(
        self,
        s0: float,
        bars_beyond_level: int,
    ) -> Tuple[float, str]:
        """Exponential sweep rejection decay; lingered acceptance beyond level flips to PRICE_ACCEPTANCE."""
        if bars_beyond_level <= 0:
            return float(s0), "FRESH_REJECTION"
        excess = max(0, bars_beyond_level - self.grace_bars)
        decayed = float(s0 * np.exp(-self.decay_lambda * excess))
        if bars_beyond_level > self.grace_bars:
            return decayed, "PRICE_ACCEPTANCE"
        return decayed, "GRACE_WINDOW"

    def cross_examine(
        self,
        side: int,
        entry_px: float,
        risk_dist: float,
        thesis_scores: Dict[str, float],
        thesis_weights: Dict[str, float],
        opposing_htf_walls: List[float],
        ker_4h: float,
        body_ratio_4h: float,
        dir_4h_candle: int,
        htf_trend_1h: int,
        htf_trend_4h: int,
        rvol_entry: float,
        rvol_opp: float,
        sweep_bars_accepted: int = 0,
        is_counter_trend_sweep: bool = False,
        require_1h_bos_against_freight: bool = True,
        min_clearance_r: float = 2.5,
    ) -> ProsecutorVerdict:
        eps = 1e-4
        # 1) Thesis Log-Odds L_Thesis
        num = den = 0.0
        for k, w in thesis_weights.items():
            if w <= 0 or k not in thesis_scores:
                continue
            p = float(np.clip(thesis_scores[k], eps, 1.0 - eps))
            num += float(w) * float(np.log(p / (1.0 - p)))
            den += float(w)
        l_thesis = (num / den) if den > 0 else 0.0

        # 2) Temporal Sweep Acceptance vs Rejection Decay
        s0 = float(thesis_scores.get("sweep", 0.75))
        decayed_sw, acc_status = self.evaluate_temporal_sweep_decay(s0, sweep_bars_accepted)

        # 3) Check A: HTF Brick Wall / Obstacle Clearance (< min_clearance_r ahead of entry)
        bw_pen = 0.0
        nearest_wall_r = 99.0
        if risk_dist > 0 and opposing_htf_walls:
            for wpx in opposing_htf_walls:
                dist = (wpx - entry_px) * side
                if dist > 0:
                    r_room = dist / risk_dist
                    if r_room < nearest_wall_r:
                        nearest_wall_r = r_room
            if nearest_wall_r < min_clearance_r:
                bw_pen = float(np.clip((min_clearance_r - nearest_wall_r) / min_clearance_r, 0.0, 1.0))

        # 4) Check B: HTF Expansion Freight-Train Veto
        freight_veto = False
        freight_pen = 0.0
        opposing_4h_impulse = (dir_4h_candle == -side and body_ratio_4h >= 0.55)
        opposing_macro = (htf_trend_4h == -side)
        if is_counter_trend_sweep:
            if ker_4h > 0.45 and (opposing_4h_impulse or opposing_macro):
                if not require_1h_bos_against_freight or (htf_trend_1h != side):
                    freight_veto = True
                    freight_pen = 1.5
            elif opposing_macro and ker_4h > 0.35:
                freight_pen = 0.65

        # 5) Check C: Volume-Price Divergence (weak breakout RVOL vs strong opposing RVOL)
        vdiv_pen = 0.0
        if rvol_entry < 0.85 and rvol_opp > 1.25:
            vdiv_pen = float(np.clip((1.25 - rvol_entry) * 0.75, 0.0, 1.0))
        elif rvol_entry < 0.85:
            vdiv_pen = 0.25

        acc_pen = 1.6 if acc_status == "PRICE_ACCEPTANCE" else 0.0
        p_contradiction = float(0.85 * bw_pen + freight_pen + 0.55 * vdiv_pen + acc_pen)

        logit = self.alpha_thesis * l_thesis - self.beta_prosecutor * p_contradiction - self.theta_bias
        conviction = float(sigmoid(logit, 0.0, 1.0))
        approved = (not freight_veto) and (acc_status != "PRICE_ACCEPTANCE") and (conviction >= self.min_conviction)

        chain = {
            "thesis_scores": dict(thesis_scores),
            "l_thesis": round(l_thesis, 4),
            "p_contradiction": round(p_contradiction, 4),
            "nearest_wall_r": round(nearest_wall_r, 2),
            "brick_wall_pen": round(bw_pen, 3),
            "freight_train_veto": freight_veto,
            "ker_4h": round(ker_4h, 3),
            "vol_div_pen": round(vdiv_pen, 3),
            "acceptance_status": acc_status,
            "sweep_decay": round(decayed_sw, 3),
            "conviction": round(conviction, 4),
            "approved": approved,
        }
        return ProsecutorVerdict(
            conviction=conviction,
            thesis_logit=l_thesis,
            contradiction_penalty=p_contradiction,
            brick_wall_penalty=bw_pen,
            freight_train_veto=freight_veto,
            vol_divergence_penalty=vdiv_pen,
            acceptance_status=acc_status,
            sweep_decay_score=decayed_sw,
            approved=approved,
            reasoning_chain=chain,
        )


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
        self.kinematics = KinematicMonitor()
        self.prosecutor = AdversarialCrossExaminer()
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


def _summarize_trades(trades: List[dict]) -> Dict[str, object]:
    all_r = [t["net_r"] for t in trades]
    is_r = [t["net_r"] for t in trades if t["entry_time"].year <= 2023]
    oos_r = [t["net_r"] for t in trades if t["entry_time"].year >= 2024]

    def _st(arr: List[float]) -> Dict[str, float]:
        if not arr:
            return {"n": 0, "wr": 0.0, "net": 0.0, "pf": 0.0}
        gp = sum(x for x in arr if x > 0)
        gl = -sum(x for x in arr if x < 0)
        return {
            "n": len(arr),
            "wr": 100.0 * sum(1 for x in arr if x > 0) / len(arr),
            "net": sum(arr),
            "pf": gp / gl if gl > 0 else 99.0,
        }

    cum = np.cumsum(all_r) if all_r else np.array([0.0])
    pk = np.maximum.accumulate(np.insert(cum, 0, 0.0))[1:]
    dd = float(np.max(pk - cum)) if all_r else 0.0

    by_cl: Dict[int, float] = {}
    yr_r: Dict[int, float] = {}
    for t in trades:
        by_cl[t["cluster_id"]] = by_cl.get(t["cluster_id"], 0.0) + t["net_r"]
        yr = int(t["entry_time"].year)
        yr_r[yr] = yr_r.get(yr, 0.0) + t["net_r"]
    cl_vals = list(by_cl.values())
    return {
        "all": _st(all_r),
        "is": _st(is_r),
        "oos": _st(oos_r),
        "max_dd_r": dd,
        "cluster_max_r": max(cl_vals, default=0.0),
        "clusters_ge_10r": sum(1 for v in cl_vals if v >= 10.0),
        "yearly_r": {k: round(v, 1) for k, v in sorted(yr_r.items())},
        "years_green": sum(1 for v in yr_r.values() if v > 0),
        "years_total": len(yr_r),
    }


def run_v6_cognitive_backtest(
    df_5m: pd.DataFrame,
    eval_start: pd.Timestamp,
    eval_end: pd.Timestamp,
    rho_min: float = 1.50,
    rho_max: float = 1.85,
    min_rho_floor: float = 1.50,
    max_rho_cap: float = 2.00,
    use_stage2_pyramid: bool = True,
    use_climax_ratchet: bool = True,
    use_prosecutor: bool = True,
    min_conviction: float = 0.35,
    fee_mult: float = 1.0,
) -> Tuple[List[dict], Dict[str, object]]:
    """V6.0 Cognitive Fractal Engine: Fractal 1H/4H Stop Compression + Kinematics + Prosecutor + 2-Stage Pyramiding."""
    df1h = df_5m.resample("1h").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}).dropna()
    df4h = df_5m.resample("4h").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}).dropna()
    df1d = df_5m.resample("1D").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}).dropna()

    o1, h1, l1, c1, v1 = (df1h[col].to_numpy(float) for col in ("Open", "High", "Low", "Close", "Volume"))
    ts1_ns = df1h.index.as_unit("ns").asi8
    close1_ns = ts1_ns + int(3600 * 1e9)
    atr1 = compute_atr_series(h1, l1, c1, 14)

    o4, h4, l4, c4, v4 = (df4h[col].to_numpy(float) for col in ("Open", "High", "Low", "Close", "Volume"))
    ts4_ns = df4h.index.as_unit("ns").asi8
    ts4_sec = ts4_ns / 1e9
    close4_ns = ts4_ns + int(14400 * 1e9)
    atr4 = compute_atr_series(h4, l4, c4, 14)

    c1d = df1d["Close"].to_numpy(float)
    ts1d_ns = df1d.index.as_unit("ns").asi8
    close1d_ns = ts1d_ns + int(86400 * 1e9)
    e20_1d = pd.Series(c1d).ewm(span=20, adjust=False).mean().to_numpy(float)
    e50_1d = pd.Series(c1d).ewm(span=50, adjust=False).mean().to_numpy(float)

    brain = InstitutionalStrategyBrain(confluence_threshold=0.50)
    brain.prosecutor.min_conviction = float(min_conviction)
    reg_4 = brain.regime.precompute_frame_features(df4h)
    adx4 = brain.compute_adx_series(h4, l4, atr4, 14)

    sw4 = brain.perception.detect_causal_swings(ts4_ns, h4, l4, c4, atr4, max_swings=6000)
    sw4_by_conf: Dict[int, List[TopologicalSwing]] = {}
    for s in sw4:
        sw4_by_conf.setdefault(s.confirm_idx, []).append(s)

    sw1 = brain.perception.detect_causal_swings(ts1_ns, h1, l1, c1, atr1, max_swings=24000)
    sw1_by_conf: Dict[int, List[TopologicalSwing]] = {}
    for s in sw1:
        sw1_by_conf.setdefault(s.confirm_idx, []).append(s)

    hi20 = pd.Series(h4).rolling(20).max().shift(1).to_numpy(float)
    lo20 = pd.Series(l4).rolling(20).min().shift(1).to_numpy(float)

    p1h = 0
    p1d = 0
    vis4: List[TopologicalSwing] = []
    vis1: List[TopologicalSwing] = []
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
        while p1h < len(df1h) and close1_ns[p1h] <= c_ns:
            new_s1 = sw1_by_conf.get(p1h, [])
            if new_s1:
                vis1.extend(new_s1)
                vis1 = vis1[-40:]
            brain.prot_1h.update(p1h, float(c1[p1h]), new_s1)
            p1h += 1

        if i4 in sw4_by_conf:
            vis4.extend(sw4_by_conf[i4])
            vis4 = vis4[-40:]
            brain.liq_mapper.ingest_structural_swings(vis4, l4[:i4 + 1], h4[:i4 + 1], float(atr4[i4]), "4H")
        brain._update_4h_pois(i4, o4, h4, l4, c4, atr4)
        brain.liq_mapper.step_bar(float(ts4_sec[i4]), float(o4[i4]), float(h4[i4]), float(l4[i4]), float(c4[i4]), float(atr4[i4]))

        if p1d < 50 or p1h < 30 or c_ns < eval0_ns:
            continue

        # 1) Manage active positions with V6 Climax Elastic Ratchet & Protected Swings
        still: List[TradePositionState] = []
        cluster_open_r = sum(
            (((float(c4[i4]) - p.entry_price) * p.side) / p.risk_dist) * p.risk_mult
            for p in brain.positions
        ) if brain.positions else 0.0
        rs_now = brain.regime.evaluate_bar(reg_4, i4)

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
                    "pyramid_stage": pos.pyramid_stage,
                    "outcome": "TRAIL_SL" if (pos.cur_sl - pos.entry_price) * pos.side > 0 else "SL",
                    "reasoning_chain": pos.meta.get("reasoning_chain", {}),
                })
                cool = i4 + 1
                continue

            pos.best_px = max(pos.best_px, float(h4[i4])) if pos.side == 1 else min(pos.best_px, float(l4[i4]))
            pos.peak_mfe_r = max(pos.peak_mfe_r, ((pos.best_px - pos.entry_price) * pos.side) / pos.risk_dist)

            # Climax Elastic Ratchet when cluster >= 10R..14R or opposing HTF pool swept with climax volume
            trail_mult = brain.trail_atr_mult
            if use_climax_ratchet:
                opp_htf = brain.liq_mapper.nearest_opposing_pool(float(c4[i4]), pos.side, min_tier=1)
                opp_swept = bool(opp_htf is not None and (
                    (pos.side == 1 and h4[i4] >= opp_htf.price and c4[i4] < opp_htf.price)
                    or (pos.side == -1 and l4[i4] <= opp_htf.price and c4[i4] > opp_htf.price)
                ))
                climax_wick = brain.perception.rejection_wick_score(
                    float(o4[i4]), float(h4[i4]), float(l4[i4]), float(c4[i4]), -pos.side, float(atr4[i4])
                ) >= 0.55
                trail_mult = brain.exit_mgr.climax_ratchet_4h_mult(
                    cluster_open_r, rs_now.rvol, climax_wick, opp_swept, base_mult=brain.trail_atr_mult, ratchet_mult=2.0
                )

            trail_cand = (pos.best_px - trail_mult * float(atr4[i4])) if pos.side == 1 else (pos.best_px + trail_mult * float(atr4[i4]))
            if (pos.side == 1 and trail_cand > pos.cur_sl and trail_cand < c4[i4]) or (
                pos.side == -1 and trail_cand < pos.cur_sl and trail_cand > c4[i4]
            ):
                pos.cur_sl = trail_cand

            # Stage 1 Pyramid Arming (+2.0R MFE -> lock BE+0.35R)
            if (not pos.is_pyramid) and pos.pyramid_stage == 0 and pos.peak_mfe_r >= 2.0:
                lk = pos.entry_price + pos.side * 0.35 * pos.risk_dist
                if (pos.side == 1 and lk > pos.cur_sl and lk < c4[i4]) or (pos.side == -1 and lk < pos.cur_sl and lk > c4[i4]):
                    pos.cur_sl = lk
                pos.be_moved = True
                pos.pyramid_armed = True
            still.append(pos)
        brain.positions = still

        # 2) Risk-Free 2-Stage Pyramiding
        if brain.positions:
            p0 = brain.positions[0]
            # Stage 1: add 0.5x on pullback continuation
            if len(brain.positions) == 1 and p0.pyramid_armed and p0.pyramid_stage == 0:
                pb = (
                    (p0.side == 1 and l4[i4] <= c4[i4 - 1] and c4[i4] > o4[i4] and c4[i4] > p0.entry_price)
                    or (p0.side == -1 and h4[i4] >= c4[i4 - 1] and c4[i4] < o4[i4] and c4[i4] < p0.entry_price)
                )
                if pb:
                    sl_p1 = float(c4[i4]) - p0.side * 1.5 * float(atr4[i4])
                    p0.pyramid_done = True
                    p0.pyramid_stage = 1
                    brain.positions.append(
                        TradePositionState(
                            trade_id=p0.trade_id, side=p0.side, entry_bar=i4,
                            entry_ts=pd.Timestamp(c_ns, tz="UTC"), entry_price=float(c4[i4]),
                            init_sl=sl_p1, cur_sl=sl_p1, risk_dist=abs(float(c4[i4]) - sl_p1),
                            risk_mult=0.50, is_pyramid=True, pyramid_stage=1,
                            meta={"reasoning_chain": p0.meta.get("reasoning_chain", {})},
                        )
                    )
                    continue
            # Stage 2: at +4.2R open cluster profit & strong KER_4H > 0.40, lock prior legs & add 0.35x
            elif use_stage2_pyramid and len(brain.positions) == 2 and p0.pyramid_stage == 1 and cluster_open_r >= 4.2 and rs_now.ker > 0.40:
                pb2 = (
                    (p0.side == 1 and c4[i4] > o4[i4] and c4[i4] > max(c4[i4 - 1], o4[i4 - 1]))
                    or (p0.side == -1 and c4[i4] < o4[i4] and c4[i4] < min(c4[i4 - 1], o4[i4 - 1]))
                )
                ps1 = brain.prot_1h.latest_floor_or_ceiling(p0.side)
                if pb2 and ps1 is not None:
                    lock_px = (ps1.price - 0.25 * float(atr1[p1h - 1])) if p0.side == 1 else (ps1.price + 0.25 * float(atr1[p1h - 1]))
                    min_lock = p0.entry_price + p0.side * 2.0 * p0.risk_dist
                    if p0.side == 1:
                        lock_px = max(lock_px, min_lock)
                    else:
                        lock_px = min(lock_px, min_lock)
                    if (p0.side == 1 and lock_px < c4[i4]) or (p0.side == -1 and lock_px > c4[i4]):
                        for pos_k in brain.positions:
                            if (pos_k.side == 1 and lock_px > pos_k.cur_sl) or (pos_k.side == -1 and lock_px < pos_k.cur_sl):
                                pos_k.cur_sl = lock_px
                        p0.pyramid_stage = 2
                        sl_p2 = float(c4[i4]) - p0.side * 1.4 * float(atr4[i4])
                        brain.positions.append(
                            TradePositionState(
                                trade_id=p0.trade_id, side=p0.side, entry_bar=i4,
                                entry_ts=pd.Timestamp(c_ns, tz="UTC"), entry_price=float(c4[i4]),
                                init_sl=sl_p2, cur_sl=sl_p2, risk_dist=abs(float(c4[i4]) - sl_p2),
                                risk_mult=0.35, is_pyramid=True, pyramid_stage=2,
                                meta={"reasoning_chain": p0.meta.get("reasoning_chain", {})},
                            )
                        )
                        continue

        if brain.positions or i4 < cool or np.isnan(hi20[i4]):
            continue

        # 3) Entry Thesis: 1D Trend + 4H Breakout + Kinematics + Scale-Free Fractal Compression + Prosecutor
        d1_tr = 1 if e20_1d[p1d - 1] > e50_1d[p1d - 1] else -1
        side = 0
        if d1_tr == 1 and c4[i4] > hi20[i4] and c4[i4 - 1] <= hi20[i4 - 1] and adx4[i4] >= 20.0:
            side = 1
        elif d1_tr == -1 and c4[i4] < lo20[i4] and c4[i4 - 1] >= lo20[i4 - 1] and adx4[i4] >= 20.0:
            side = -1
        if side == 0:
            continue

        ep = float(c4[i4])
        # Scale-free fractal 1H structural anchors (no fixed % clamp!)
        recent_1h_anchors = [
            float(s.price) for s in vis1[-10:]
            if s.side == -side and ((side == 1 and s.price < ep) or (side == -1 and s.price > ep))
        ]
        if side == 1:
            recent_1h_anchors.append(float(np.min(l1[max(0, p1h - 12):p1h])))
        else:
            recent_1h_anchors.append(float(np.max(h1[max(0, p1h - 12):p1h])))

        slp, rho_comp, sl_src = brain.kinematics.fractal_stop_compression(
            ep, side, float(atr4[i4]), float(atr1[p1h - 1]), recent_1h_anchors,
            rho_min=rho_min, rho_max=rho_max, min_rho_floor=min_rho_floor, max_rho_cap=max_rho_cap, fallback_mult=2.0,
        )
        rd = abs(ep - slp)
        if rd <= 0 or (rd / ep) > 0.085:
            continue

        # Kinematic Velocity Check on 4H leg
        k_ratio, _, _ = brain.kinematics.compute_kinematic_ratio(o4, h4, l4, c4, atr4, max(0, i4 - 12), i4 - 3, i4)
        disp_sc = brain.perception.displacement_score(float(o4[i4]), float(h4[i4]), float(l4[i4]), float(c4[i4]), float(atr4[i4]))
        adx_sc = float(sigmoid(adx4[i4], x0=18.0, k=0.25))
        kin_sc = float(sigmoid(k_ratio, x0=0.85, k=1.8))

        thesis_scores = {
            "ker": rs_now.ker_score,
            "er": rs_now.effort_result_score,
            "sq": rs_now.squeeze_score,
            "disp": disp_sc,
            "adx": adx_sc,
            "kin": kin_sc,
        }
        thesis_weights = {"ker": 1.0, "er": 1.0, "sq": 0.6, "disp": 1.0, "adx": 1.2, "kin": 0.6}

        opp_walls = [p.price for p in brain.liq_mapper.pools.values() if p.status == "UNTAPPED" and p.tier in (1, 3)]
        dir_4h = 1 if c4[i4] > o4[i4] else -1
        if use_prosecutor:
            verdict = brain.prosecutor.cross_examine(
                side=side,
                entry_px=ep,
                risk_dist=rd,
                thesis_scores=thesis_scores,
                thesis_weights=thesis_weights,
                opposing_htf_walls=opp_walls,
                ker_4h=rs_now.ker,
                body_ratio_4h=rs_now.body_ratio,
                dir_4h_candle=dir_4h,
                htf_trend_1h=d1_tr,
                htf_trend_4h=d1_tr,
                rvol_entry=rs_now.rvol,
                rvol_opp=1.0,
                is_counter_trend_sweep=False,
                min_clearance_r=0.0,
            )
            if not verdict.approved or rs_now.absorption_trap_score >= 0.78:
                continue
            chain = dict(verdict.reasoning_chain)
        else:
            conf = soft_and_log_odds(thesis_scores, thesis_weights, veto_floors={"ker": 0.12})
            if conf < 0.50 or rs_now.absorption_trap_score >= 0.78:
                continue
            chain = {"thesis_scores": thesis_scores, "conviction": round(conf, 4), "approved": True}

        chain.update({"rho_comp": round(rho_comp, 3), "sl_source": sl_src, "kinematic_k": round(k_ratio, 3)})
        cid += 1
        brain.positions.append(
            TradePositionState(
                trade_id=cid, side=side, entry_bar=i4,
                entry_ts=pd.Timestamp(c_ns, tz="UTC"), entry_price=ep,
                init_sl=slp, cur_sl=slp, risk_dist=rd,
                meta={"reasoning_chain": chain},
            )
        )

    return brain.closed_trades, _summarize_trades(brain.closed_trades)


def run_smc_sweep_causal_backtest(
    df_5m: pd.DataFrame,
    eval_start: pd.Timestamp,
    eval_end: pd.Timestamp,
    use_v6_prosecutor: bool = True,
    min_ker4: float = 0.15,
    min_conviction: float = 0.35,
    fee_mult: float = 1.0,
    tp_r: float = 10.0,
) -> Tuple[List[dict], Dict[str, object]]:
    """Strictly causal 5m simulator for SMC_Sweep_10R (`use_v6_prosecutor=False`) vs SMC_Sweep_V6 (`True`)."""
    agg = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    df1h = df_5m.resample("1h").agg(agg).dropna()
    df4h = df_5m.resample("4h").agg(agg).dropna()
    df1d = df_5m.resample("1D").agg(agg).dropna()

    o5, h5, l5, c5, v5 = (df_5m[col].to_numpy(float) for col in ("Open", "High", "Low", "Close", "Volume"))
    ts5_ns = df_5m.index.as_unit("ns").asi8
    close5_ns = ts5_ns + int(300 * 1e9)
    atr5 = compute_atr_series(h5, l5, c5, 14)

    o1, h1, l1, c1, v1 = (df1h[col].to_numpy(float) for col in ("Open", "High", "Low", "Close", "Volume"))
    ts1_ns = df1h.index.as_unit("ns").asi8
    close1_ns = ts1_ns + int(3600 * 1e9)
    atr1 = compute_atr_series(h1, l1, c1, 14)

    o4, h4, l4, c4, v4 = (df4h[col].to_numpy(float) for col in ("Open", "High", "Low", "Close", "Volume"))
    ts4_ns = df4h.index.as_unit("ns").asi8
    close4_ns = ts4_ns + int(14400 * 1e9)
    atr4 = compute_atr_series(h4, l4, c4, 14)

    c1d = df1d["Close"].to_numpy(float)
    close1d_ns = df1d.index.as_unit("ns").asi8 + int(86400 * 1e9)
    e20_1d = pd.Series(c1d).ewm(span=20, adjust=False).mean().to_numpy(float)
    e50_1d = pd.Series(c1d).ewm(span=50, adjust=False).mean().to_numpy(float)

    rf = RegimeFilterEngine()
    reg_4 = rf.precompute_frame_features(df4h)
    reg_5 = rf.precompute_frame_features(df_5m)
    prosecutor = AdversarialCrossExaminer(grace_bars=1, decay_lambda=0.65, min_conviction=float(min_conviction))

    def _step_swing(buf_h, buf_l, k, bar_i, act_hi, act_lo, last_hi, last_lo):
        if len(buf_h) == 2 * k + 1:
            m = k
            ch, cl = buf_h[m], buf_l[m]
            if all(ch >= buf_h[j] for j in range(len(buf_h)) if j != m) and any(ch > buf_h[j] for j in range(len(buf_h)) if j != m):
                last_hi = ch
                act_hi.append([bar_i - k, ch])
                act_hi = act_hi[-25:]
            if all(cl <= buf_l[j] for j in range(len(buf_l)) if j != m) and any(cl < buf_l[j] for j in range(len(buf_l)) if j != m):
                last_lo = cl
                act_lo.append([bar_i - k, cl])
                act_lo = act_lo[-25:]
        return act_hi, act_lo, last_hi, last_lo

    from collections import deque
    b4h, b4l = deque(maxlen=5), deque(maxlen=5)
    act4_hi, act4_lo, l4_hi, l4_lo, tr4 = [], [], None, None, 0
    b1h, b1l = deque(maxlen=5), deque(maxlen=5)
    act1_hi, act1_lo, l1_hi, l1_lo, tr1 = [], [], None, None, 0
    b1k3_h, b1k3_l = deque(maxlen=7), deque(maxlen=7)
    k3_hi, k3_lo = [], []
    b5h, b5l = deque(maxlen=5), deque(maxlen=5)
    l5_hi, l5_lo = None, None

    cands_k3 = []
    p1 = p4 = p1d = cid = 0
    eval0_ns = int(eval_start.as_unit("ns").value)
    eval1_ns = int(eval_end.as_unit("ns").value)
    pos = pend = None
    trades: List[dict] = []

    for i5 in range(80, len(df_5m)):
        c5_ns = int(close5_ns[i5])
        if c5_ns >= eval1_ns:
            break
        while p1d < len(df1d) and close1d_ns[p1d] <= c5_ns:
            p1d += 1
        while p4 < len(df4h) and close4_ns[p4] <= c5_ns:
            b4h.append(h4[p4]); b4l.append(l4[p4])
            act4_hi, act4_lo, l4_hi, l4_lo = _step_swing(b4h, b4l, 2, p4, act4_hi, act4_lo, l4_hi, l4_lo)
            act4_hi = [x for x in act4_hi if h4[p4] <= x[1]]
            act4_lo = [x for x in act4_lo if l4[p4] >= x[1]]
            if l4_hi is not None and c4[p4] > l4_hi:
                tr4 = 1
            elif l4_lo is not None and c4[p4] < l4_lo:
                tr4 = -1
            p4 += 1

        while p1 < len(df1h) and close1_ns[p1] <= c5_ns:
            hh, hl, hc = float(h1[p1]), float(l1[p1]), float(c1[p1])
            upd_cands = []
            for sd, sw_ns, sl_b, b_acc, sw_sc in cands_k3:
                if (c5_ns - sw_ns) <= 5 * 3600 * int(1e9):
                    if (sd == 1 and hc < sl_b) or (sd == -1 and hc > sl_b):
                        b_acc += 1
                    upd_cands.append((sd, sw_ns, sl_b, b_acc, sw_sc))
            cands_k3 = upd_cands[-10:]

            for idx_s, p_lo in list(k3_lo):
                if (p1 - idx_s) >= 4 and hl < p_lo and hc > p_lo:
                    sw_sc = VisualPerceptionEngine.rejection_wick_score(float(o1[p1]), hh, hl, hc, 1, float(atr1[p1]))
                    cands_k3.append((1, int(close1_ns[p1]), hl, 0, sw_sc))
            for idx_s, p_hi in list(k3_hi):
                if (p1 - idx_s) >= 4 and hh > p_hi and hc < p_hi:
                    sw_sc = VisualPerceptionEngine.rejection_wick_score(float(o1[p1]), hh, hl, hc, -1, float(atr1[p1]))
                    cands_k3.append((-1, int(close1_ns[p1]), hh, 0, sw_sc))

            b1h.append(hh); b1l.append(hl)
            act1_hi, act1_lo, l1_hi, l1_lo = _step_swing(b1h, b1l, 2, p1, act1_hi, act1_lo, l1_hi, l1_lo)
            act1_hi = [x for x in act1_hi if hh <= x[1]]
            act1_lo = [x for x in act1_lo if hl >= x[1]]
            if l1_hi is not None and hc > l1_hi:
                tr1 = 1
            elif l1_lo is not None and hc < l1_lo:
                tr1 = -1

            b1k3_h.append(hh); b1k3_l.append(hl)
            k3_hi, k3_lo, _, _ = _step_swing(b1k3_h, b1k3_l, 3, p1, k3_hi, k3_lo, None, None)
            k3_hi = [x for x in k3_hi if hh <= x[1]]
            k3_lo = [x for x in k3_lo if hl >= x[1]]
            p1 += 1

        b5h.append(h5[i5 - 1]); b5l.append(l5[i5 - 1])
        _, _, l5_hi, l5_lo = _step_swing(b5h, b5l, 2, i5 - 1, [], [], l5_hi, l5_lo)

        if c5_ns < eval0_ns or p4 < 30 or p1 < 30 or p1d < 50:
            continue

        if pos is not None:
            sd = pos["side"]
            if (sd == 1 and l5[i5] <= pos["cur_sl"]) or (sd == -1 and h5[i5] >= pos["cur_sl"]):
                gr = ((pos["cur_sl"] - pos["ep"]) * sd) / pos["rd"]
                hrs = max(0.1, (i5 - pos["bar"]) * (5.0 / 60.0))
                cost = fee_mult * ((0.0002 + 0.0007 + 0.0001 * (hrs / 8.0)) / (pos["rd"] / pos["ep"]))
                trades.append({
                    "cluster_id": pos["id"], "entry_time": pos["ts"], "exit_time": pd.Timestamp(c5_ns, tz="UTC"),
                    "side": sd, "entry_price": pos["ep"], "init_sl": pos["sl"], "sl_pct": pos["rd"] / pos["ep"],
                    "gross_r": gr, "net_r": gr - cost, "is_pyramid": False,
                    "outcome": "BE" if pos["be"] else "SL", "reasoning_chain": pos["chain"],
                })
                pos = None
            elif (sd == 1 and h5[i5] >= pos["tp"]) or (sd == -1 and l5[i5] <= pos["tp"]):
                gr = tp_r
                hrs = max(0.1, (i5 - pos["bar"]) * (5.0 / 60.0))
                cost = fee_mult * ((0.0002 + 0.0002 + 0.0001 * (hrs / 8.0)) / (pos["rd"] / pos["ep"]))
                trades.append({
                    "cluster_id": pos["id"], "entry_time": pos["ts"], "exit_time": pd.Timestamp(c5_ns, tz="UTC"),
                    "side": sd, "entry_price": pos["ep"], "init_sl": pos["sl"], "sl_pct": pos["rd"] / pos["ep"],
                    "gross_r": gr, "net_r": gr - cost, "is_pyramid": False,
                    "outcome": "TP", "reasoning_chain": pos["chain"],
                })
                pos = None
            else:
                fav_r = (((h5[i5] if sd == 1 else l5[i5]) - pos["ep"]) * sd) / pos["rd"]
                if not pos["be"] and fav_r >= 3.0:
                    pos["cur_sl"] = pos["ep"] + sd * 1.0 * pos["rd"]
                    pos["be"] = True
            continue

        if pend is not None:
            if i5 > pend["exp"]:
                pend = None
            elif (pend["side"] == 1 and l5[i5] <= pend["ep"]) or (pend["side"] == -1 and h5[i5] >= pend["ep"]):
                cid += 1
                pos = {
                    "id": cid, "side": pend["side"], "ep": pend["ep"], "sl": pend["sl"],
                    "cur_sl": pend["sl"], "tp": pend["tp"], "rd": pend["rd"],
                    "bar": i5, "ts": pd.Timestamp(c5_ns, tz="UTC"), "be": False, "chain": pend["chain"],
                }
                pend = None
                continue

        if pend is not None or not cands_k3:
            continue

        utc_hr = pd.Timestamp(ts5_ns[i5], tz="UTC").hour
        a5 = float(atr5[i5])
        if utc_hr < 9 or a5 <= 0:
            continue

        c2b = abs(c5[i5 - 1] - o5[i5 - 1])
        rs4 = rf.evaluate_bar(reg_4, p4 - 1)
        rs5 = rf.evaluate_bar(reg_5, i5)
        if use_v6_prosecutor and rs4.ker < min_ker4:
            continue
        d1_tr = 1 if e20_1d[p1d - 1] > e50_1d[p1d - 1] else -1

        for side, sw_ns, sl_base, b_acc, sw_sc in reversed(cands_k3):
            if (c5_ns - sw_ns) > 5 * 3600 * int(1e9):
                continue
            ok = False
            if side == 1 and l5[i5] >= sl_base and tr4 == 1 and tr1 == 1 and l5_hi is not None:
                if c5[i5] > l5_hi and (l5[i5] - h5[i5 - 2]) >= 0.25 * a5 and c5[i5 - 1] > o5[i5 - 1] and c2b >= a5:
                    slp = min(sl_base - a5, c5[i5] - max(1.5 * a5, c5[i5] * 0.0020))
                    ok = True
            elif side == -1 and h5[i5] <= sl_base and tr4 == -1 and tr1 == -1 and l5_lo is not None:
                if c5[i5] < l5_lo and (l5[i5 - 2] - h5[i5]) >= 0.25 * a5 and c5[i5 - 1] < o5[i5 - 1] and c2b >= a5:
                    slp = max(sl_base + a5, c5[i5] + max(1.5 * a5, c5[i5] * 0.0020))
                    ok = True
            if not ok:
                continue

            ep = float(c5[i5])
            rd = abs(ep - slp)
            if not (0.0020 <= (rd / ep) <= 0.0180):
                continue

            chain = {}
            if use_v6_prosecutor:
                disp_sc = VisualPerceptionEngine.displacement_score(float(o5[i5 - 1]), float(h5[i5 - 1]), float(l5[i5 - 1]), float(c5[i5 - 1]), a5)
                verdict = prosecutor.cross_examine(
                    side=side,
                    entry_px=ep,
                    risk_dist=rd,
                    thesis_scores={"sweep": max(0.55, sw_sc), "disp": disp_sc, "ker4": rs4.ker_score, "rvol": rs5.rvol_score},
                    thesis_weights={"sweep": 1.2, "disp": 1.3, "ker4": 1.1, "rvol": 0.6},
                    opposing_htf_walls=[],
                    ker_4h=rs4.ker,
                    body_ratio_4h=rs4.body_ratio,
                    dir_4h_candle=(1 if c4[p4 - 1] > o4[p4 - 1] else -1),
                    htf_trend_1h=tr1,
                    htf_trend_4h=d1_tr,
                    rvol_entry=rs5.rvol,
                    rvol_opp=1.0,
                    sweep_bars_accepted=b_acc,
                    is_counter_trend_sweep=(side != d1_tr),
                    require_1h_bos_against_freight=False,
                )
                if not verdict.approved:
                    continue
                chain = dict(verdict.reasoning_chain)

            pend = {
                "side": side, "ep": ep, "sl": slp, "tp": ep + side * tp_r * rd,
                "rd": rd, "exp": i5 + 20, "chain": chain,
            }
            break

    return trades, _summarize_trades(trades)


class SmallAccountCashflowManager:
    """V8.0-V11.0 $100 Conviction-Scaled Ratchet Sizer, 50/50 HWM Profit-Skim & Daily Circuit Breaker.

    V11.0 adds Bug 1 fixes (`fee_inclusive=True`, `strict_aplus_gate=True`, `throttle_mult=0.80`,
    `period_anchor='month'`) via `v11_daily_hunter_100()` and `v11_turbo_sniper_100()`:
      - Fee-Inclusive Exact 1.0R Sizing: `Notional = Risk_USD / (stop_distance_pct + fee_rt_pct)`
        so a full stop-out loss never exceeds `-1.00R` inclusive of fees/slippage.
      - Asymmetric Risk Restricted to Proven `PF > 2.0` A+ Sleeves (`3.8%-4.2%` vs `3.0%`).
      - Smooth DD Throttle: gentle `0.80x` step-down ONLY when active equity DD > `15%` from HWM.
      - Monthly Risk-Anchoring + `sized_r` account R-units (`0/81` monthly `+R = -$` anomalies).
    """

    LEGACY_APLUS_SETUPS = {
        "SMC_Sweep_V6",
        "V7_BPR_Snap",
        "V8_BPR_Snap",
        "V9_LON",
        "V9_1H_K2",
        "V9_15M_NY",
        "V9_BPR_Snap",
        "V10_CompVac",
        "V10_BPR_Snap",
        "V10_BPR_Retest",
        "V10_XAU_VisB",
        "V10_NSX_CompVac",
        "V10_NSX_BPR_Snap",
        "V10_LON",
        "V10_1H_TOPO",
        "V10_15M_TOPO",
        "4H_V6_Cognitive",
    }

    VERIFIED_V11_APLUS_SETUPS = {
        "SMC_Sweep_V6",
        "V10_BPR_Snap",
        "4H_V6_Cognitive",
        "V10_1H_TOPO",
        "V11_SessEq_1H_TOPO",
        "V3_Pro",
        "V3_Pro_Clean",
        "VisB_Pro",
    }

    def __init__(
        self,
        starting_equity: float = 100.0,
        risk_pct: float = 0.025,
        aplus_risk_pct: float = 0.040,
        throttle_risk_pct: float = 0.020,
        throttle_dd_pct: float = 0.10,
        skim_step_usd: float = 25.0,
        skim_frac: float = 0.50,
        max_leverage: float = 15.0,
        daily_dd_cap_r: float = -2.5,
        min_notional_usd: float = 5.0,
        use_conviction_scaling: bool = True,
        max_concurrent_risk_slots: Optional[int] = None,
        slot_recycling: bool = True,
        fee_inclusive: bool = False,
        fee_rt_pct_crypto: float = 0.0010,
        fee_rt_pct_cfd: float = 0.0005,
        throttle_mult: Optional[float] = None,
        strict_aplus_gate: bool = False,
        period_anchor: str = "trade",
    ) -> None:
        self.starting_equity = float(starting_equity)
        self.risk_pct = float(risk_pct)
        self.aplus_risk_pct = float(aplus_risk_pct)
        self.throttle_risk_pct = float(throttle_risk_pct)
        self.throttle_dd_pct = float(throttle_dd_pct)
        self.skim_step_usd = float(skim_step_usd)
        self.skim_frac = float(skim_frac)
        self.max_leverage = float(max_leverage)
        self.daily_dd_cap_r = float(daily_dd_cap_r)
        self.min_notional_usd = float(min_notional_usd)
        self.use_conviction_scaling = bool(use_conviction_scaling)
        self.max_concurrent_risk_slots = max_concurrent_risk_slots
        self.slot_recycling = bool(slot_recycling)
        self.fee_inclusive = bool(fee_inclusive)
        self.fee_rt_pct_crypto = float(fee_rt_pct_crypto)
        self.fee_rt_pct_cfd = float(fee_rt_pct_cfd)
        self.throttle_mult = None if throttle_mult is None else float(throttle_mult)
        self.strict_aplus_gate = bool(strict_aplus_gate)
        self.period_anchor = str(period_anchor).lower()

    @classmethod
    def daily_hunter_100(cls) -> "SmallAccountCashflowManager":
        """V10.0 DAILY_HUNTER_$100: 3.0% std / 4.5% A+, 2.0% DD throttle, 4 risk slots, -2.0R/day CB, $25 50/50 vault skim."""
        return cls(
            starting_equity=100.0,
            risk_pct=0.030,
            aplus_risk_pct=0.045,
            throttle_risk_pct=0.020,
            throttle_dd_pct=0.10,
            skim_step_usd=25.0,
            skim_frac=0.50,
            max_leverage=15.0,
            daily_dd_cap_r=-2.0,
            max_concurrent_risk_slots=4,
            slot_recycling=True,
        )

    @classmethod
    def turbo_sniper_100(cls) -> "SmallAccountCashflowManager":
        """V10.0 TURBO_SNIPER_$100: 4.0% std / 5.5% A+, 2.5% DD throttle, 4 risk slots, -2.5R/day CB, $20 50/50 vault skim."""
        return cls(
            starting_equity=100.0,
            risk_pct=0.040,
            aplus_risk_pct=0.055,
            throttle_risk_pct=0.025,
            throttle_dd_pct=0.10,
            skim_step_usd=20.0,
            skim_frac=0.50,
            max_leverage=15.0,
            daily_dd_cap_r=-2.5,
            max_concurrent_risk_slots=4,
            slot_recycling=True,
        )

    @classmethod
    def v11_daily_hunter_100(cls) -> "SmallAccountCashflowManager":
        """V11.0 DAILY_HUNTER_$100: Fee-inclusive 1.0R sizing, 3.0% std / 3.8% A+ (PF>2.0), 0.80x >15% DD, monthly anchor, $25 50/50 skim."""
        return cls(
            starting_equity=100.0,
            risk_pct=0.030,
            aplus_risk_pct=0.038,
            throttle_risk_pct=0.024,
            throttle_dd_pct=0.15,
            skim_step_usd=25.0,
            skim_frac=0.50,
            max_leverage=15.0,
            daily_dd_cap_r=-2.0,
            max_concurrent_risk_slots=4,
            slot_recycling=True,
            fee_inclusive=True,
            fee_rt_pct_crypto=0.0010,
            fee_rt_pct_cfd=0.0005,
            throttle_mult=0.80,
            strict_aplus_gate=True,
            period_anchor="month",
        )

    @classmethod
    def v11_turbo_sniper_100(cls) -> "SmallAccountCashflowManager":
        """V11.0 TURBO_SNIPER_$100: Fee-inclusive 1.0R sizing, 3.6% std / 4.2% A+ (PF>2.0), 0.80x >15% DD, monthly anchor, $20 50/50 skim."""
        return cls(
            starting_equity=100.0,
            risk_pct=0.036,
            aplus_risk_pct=0.042,
            throttle_risk_pct=0.0288,
            throttle_dd_pct=0.15,
            skim_step_usd=20.0,
            skim_frac=0.50,
            max_leverage=15.0,
            daily_dd_cap_r=-2.5,
            max_concurrent_risk_slots=4,
            slot_recycling=True,
            fee_inclusive=True,
            fee_rt_pct_crypto=0.0010,
            fee_rt_pct_cfd=0.0005,
            throttle_mult=0.80,
            strict_aplus_gate=True,
            period_anchor="month",
        )

    def _fee_rt_for_asset(self, asset: str) -> float:
        a = str(asset).upper()
        if any(k in a for k in ("XAU", "NSX", "NAS", "NDX", "US100", "EUR", "GBP", "SPX")):
            return self.fee_rt_pct_cfd
        return self.fee_rt_pct_crypto

    def resolve_risk_pct(
        self,
        equity: float,
        active_hwm: float,
        trade: Optional[dict] = None,
    ) -> float:
        """Conviction-Based Tiered Risk + Smooth Drawdown Throttle."""
        in_dd = active_hwm > 0 and ((active_hwm - equity) / active_hwm) > self.throttle_dd_pct
        if in_dd and self.throttle_mult is None:
            return self.throttle_risk_pct

        base_rp = self.risk_pct
        if self.use_conviction_scaling and trade is not None:
            setup = str(trade.get("setup", ""))
            conv = float(trade.get("conviction", trade.get("reasoning_chain", {}).get("conviction", 0.0)) or 0.0)
            if self.strict_aplus_gate:
                if setup in self.VERIFIED_V11_APLUS_SETUPS:
                    if setup == "4H_V6_Cognitive":
                        is_aplus = conv >= 0.72 or bool(trade.get("is_aplus", False))
                    else:
                        is_aplus = True
                else:
                    is_aplus = conv >= 0.78 and bool(trade.get("is_aplus", False))
            else:
                is_aplus = bool(
                    trade.get("is_aplus", False)
                    or setup in self.LEGACY_APLUS_SETUPS
                    or conv >= 0.72
                )
            if is_aplus:
                base_rp = self.aplus_risk_pct

        if in_dd and self.throttle_mult is not None:
            return base_rp * self.throttle_mult
        return base_rp

    def compute_position_notional(
        self,
        equity: float,
        stop_distance_pct: float,
        risk_pct_override: Optional[float] = None,
        fee_rt_pct: Optional[float] = None,
    ) -> Tuple[float, float]:
        """Return (effective_risk_usd, notional_usd) capped at safe max_leverage.

        When `fee_inclusive=True` (V11.0), `Notional = Risk_USD / (stop_distance_pct + fee_rt_pct)`
        so a full stop-out loss never exceeds `-1.00R` inclusive of fees and slippage.
        """
        if equity <= 0 or stop_distance_pct <= 0:
            return 0.0, 0.0
        rp = self.risk_pct if risk_pct_override is None else float(risk_pct_override)
        risk_usd = equity * rp
        fee_buf = (self.fee_rt_pct_crypto if fee_rt_pct is None else float(fee_rt_pct)) if self.fee_inclusive else 0.0
        eff_stop_pct = stop_distance_pct + fee_buf
        raw_notional = risk_usd / eff_stop_pct
        max_notional = equity * self.max_leverage
        notional = min(raw_notional, max_notional)
        eff_risk = notional * eff_stop_pct
        if notional < self.min_notional_usd:
            return 0.0, 0.0
        return float(eff_risk), float(notional)

    def simulate_cashflow(
        self,
        trades: List[dict],
        compounded: bool = False,
        basket_mult: float = 1.0,
        mode: Optional[str] = None,
    ) -> Dict[str, object]:
        """Simulate real dollar cashflow with daily circuit breaker & optional V11.0 fee-inclusive 1.0R sizing."""
        mode_norm = str(mode).lower() if mode is not None else ("compounded" if compounded else "fixed_risk_withdrawal")
        is_ratchet = mode_norm.startswith("ratchet")
        is_comp = mode_norm.startswith("comp")

        ordered = sorted(trades, key=lambda t: t["entry_time"])
        eq = self.starting_equity
        peak_eq = eq
        skim_anchor = eq
        withdrawn_vault_usd = 0.0
        max_dd_usd = 0.0
        max_dd_pct = 0.0
        daily_r: Dict[object, float] = {}
        daily_usd: Dict[object, float] = {}
        weekly_usd: Dict[Tuple[int, int], float] = {}
        monthly_usd: Dict[Tuple[int, int], float] = {}
        accepted_r: List[float] = []
        accepted_sized_r: List[float] = []
        accepted_trades: List[dict] = []
        open_risk_slots: List[dict] = []
        skipped_circuit = 0
        skipped_slots = 0
        m1_end = (ordered[0]["entry_time"] + pd.Timedelta(days=30)) if ordered else None
        m1_usd = 0.0
        m1_trades = 0
        cur_period: Optional[Tuple[int, int]] = None
        anchor_eq = eq
        anchor_peak = peak_eq

        for t in ordered:
            et = t["entry_time"]
            day = et.date()
            if daily_r.get(day, 0.0) <= self.daily_dd_cap_r:
                skipped_circuit += 1
                continue
            if self.max_concurrent_risk_slots is not None:
                open_risk_slots = [
                    s for s in open_risk_slots
                    if (s.get("exit_time") is not None and s["exit_time"] > et)
                    and ((not self.slot_recycling) or (s.get("t1_time") is None) or s["t1_time"] > et)
                ]
                if len(open_risk_slots) >= int(self.max_concurrent_risk_slots):
                    skipped_slots += 1
                    continue

            iso = et.isocalendar()
            wk = (int(iso.year), int(iso.week))
            mo = (int(et.year), int(et.month))
            if self.period_anchor == "week":
                if wk != cur_period:
                    cur_period = wk
                    anchor_eq = eq
                    anchor_peak = peak_eq
            elif self.period_anchor == "month":
                if mo != cur_period:
                    cur_period = mo
                    anchor_eq = eq
                    anchor_peak = peak_eq
            else:
                anchor_eq = eq
                anchor_peak = peak_eq

            sl_pct = max(float(t.get("sl_pct", 0.01)), 1e-4)
            base_eq = anchor_eq if (is_comp or is_ratchet) else self.starting_equity
            rp = self.resolve_risk_pct(anchor_eq, anchor_peak, t)
            fee_rt = self._fee_rt_for_asset(str(t.get("asset", "BTCUSD")))
            risk_usd, _ = self.compute_position_notional(
                base_eq, sl_pct, risk_pct_override=rp, fee_rt_pct=fee_rt
            )
            if risk_usd <= 0:
                continue

            raw_r = float(t["net_r"])
            gross_r = float(t.get("gross_r", raw_r))
            if self.fee_inclusive:
                actual_cost_pct = max(fee_rt, max(0.0, gross_r - raw_r) * sl_pct)
                r_val = (sl_pct / (sl_pct + actual_cost_pct)) * raw_r
                if gross_r <= -0.999 and r_val < -1.0:
                    r_val = -1.0
            else:
                r_val = raw_r

            pnl_usd = risk_usd * r_val
            std_unit_usd = max(base_eq * self.risk_pct, 1e-9)
            sized_r = pnl_usd / std_unit_usd if self.fee_inclusive else (r_val * (rp / max(self.risk_pct, 1e-9)))
            accepted_r.append(r_val)
            accepted_sized_r.append(sized_r)

            t1_hrs = t.get("t1_hours")
            t1_ts = t.get("t1_time")
            if t1_ts is None and t1_hrs is not None:
                t1_ts = et + pd.Timedelta(hours=float(t1_hrs))
            open_risk_slots.append({"entry_time": et, "exit_time": t.get("exit_time", et), "t1_time": t1_ts})

            daily_r[day] = daily_r.get(day, 0.0) + r_val
            daily_usd[day] = daily_usd.get(day, 0.0) + pnl_usd
            weekly_usd[wk] = weekly_usd.get(wk, 0.0) + pnl_usd
            monthly_usd[mo] = monthly_usd.get(mo, 0.0) + pnl_usd
            if m1_end is not None and et <= m1_end:
                m1_usd += pnl_usd
                m1_trades += 1

            if is_ratchet:
                eq = max(1.0, eq + pnl_usd)
                peak_eq = max(peak_eq, eq)
                dd_u = peak_eq - eq
                max_dd_usd = max(max_dd_usd, dd_u)
                max_dd_pct = max(max_dd_pct, 100.0 * dd_u / peak_eq)
                if eq >= skim_anchor + self.skim_step_usd:
                    gain = eq - skim_anchor
                    skim = gain * self.skim_frac
                    withdrawn_vault_usd += skim
                    eq -= skim
                    skim_anchor = eq
                    peak_eq = eq
            elif is_comp:
                eq = max(1.0, eq + pnl_usd)
                peak_eq = max(peak_eq, eq)
                dd_u = peak_eq - eq
                max_dd_usd = max(max_dd_usd, dd_u)
                max_dd_pct = max(max_dd_pct, 100.0 * dd_u / peak_eq)
            else:
                eq += pnl_usd
                peak_eq = max(peak_eq, eq)
                dd_u = peak_eq - eq
                max_dd_usd = max(max_dd_usd, dd_u)
                max_dd_pct = max(max_dd_pct, 100.0 * dd_u / max(self.starting_equity, peak_eq))

            ex_ts = t.get("exit_time", et)
            hold_hrs = float(t.get("hold_hours", max(0.0, (ex_ts - et).total_seconds() / 3600.0)))
            accepted_trades.append({
                "entry_time": et,
                "exit_time": ex_ts,
                "asset": t.get("asset", "BTCUSD"),
                "setup": t.get("setup", ""),
                "side": int(t.get("side", 0)),
                "exit_tier": str(t.get("outcome", "")),
                "hold_hours": round(hold_hrs, 2),
                "risk_pct": round(rp * 100.0, 2),
                "risk_usd": round(risk_usd, 2),
                "raw_net_r": round(raw_r, 4),
                "net_r": round(r_val, 4),
                "sized_r": round(sized_r, 4),
                "pnl_usd": round(pnl_usd, 2),
                "equity_after": round(eq, 2),
                "vault_after": round(withdrawn_vault_usd, 2),
                "total_wealth_after": round(eq + withdrawn_vault_usd, 2),
            })

        if not ordered:
            return {"n": 0, "net_usd": 0.0}

        span_days = max(1.0, (ordered[-1]["entry_time"] - ordered[0]["entry_time"]).total_seconds() / 86400.0)
        span_weeks = max(1.0, span_days / 7.0)
        span_months = max(1.0, span_days / 30.4375)
        tot_usd = sum(daily_usd.values())
        gp = sum(r for r in accepted_r if r > 0)
        gl = -sum(r for r in accepted_r if r < 0)
        days_ge_5 = sum(1 for v in daily_usd.values() if v >= 5.0)
        days_ge_10 = sum(1 for v in daily_usd.values() if v >= 10.0)
        days_ge_25 = sum(1 for v in daily_usd.values() if v >= 25.0)
        wks_ge_25 = sum(1 for v in weekly_usd.values() if v >= 25.0)
        mode_lbl = "RATCHET_CASHFLOW" if is_ratchet else ("COMPOUNDED" if is_comp else "FIXED_WITHDRAWAL")

        return {
            "mode": mode_lbl,
            "n": len(accepted_r),
            "skipped_circuit": skipped_circuit,
            "skipped_slots": skipped_slots,
            "trades_per_month": round((len(accepted_r) * basket_mult) / span_months, 2),
            "trades_per_week": round((len(accepted_r) * basket_mult) / span_weeks, 2),
            "wr": round(100.0 * sum(1 for r in accepted_r if r > 0) / max(1, len(accepted_r)), 1),
            "pf": round(gp / gl if gl > 0 else 99.0, 2),
            "net_r": round(sum(accepted_r), 2),
            "sized_r": round(sum(accepted_sized_r), 2),
            "min_net_r": round(min(accepted_r), 4) if accepted_r else 0.0,
            "final_equity_usd": round(eq, 2),
            "withdrawn_vault_usd": round(withdrawn_vault_usd, 2),
            "total_wealth_usd": round(eq + withdrawn_vault_usd, 2),
            "net_usd": round(tot_usd, 2),
            "month1_usd_single": round(m1_usd, 2),
            "month1_usd_basket": round(m1_usd * basket_mult, 2),
            "month1_trades_basket": round(m1_trades * basket_mult, 1),
            "avg_daily_usd_single": round(tot_usd / span_days, 2),
            "avg_weekly_usd_single": round(tot_usd / span_weeks, 2),
            "avg_monthly_usd_single": round(tot_usd / span_months, 2),
            "avg_daily_usd_basket": round((tot_usd * basket_mult) / span_days, 2),
            "avg_weekly_usd_basket": round((tot_usd * basket_mult) / span_weeks, 2),
            "avg_monthly_usd_basket": round((tot_usd * basket_mult) / span_months, 2),
            "days_ge_5usd": days_ge_5,
            "days_ge_10usd": days_ge_10,
            "days_ge_25usd": days_ge_25,
            "weeks_ge_25usd": wks_ge_25,
            "max_dd_usd": round(max_dd_usd, 2),
            "max_dd_pct": round(max_dd_pct, 1),
            "trade_ledger": accepted_trades,
        }

    def simulate_granular_audit(
        self,
        trades: List[dict],
        mode: str = "ratchet_cashflow",
        recent_weeks: int = 52,
        basket_mult: float = 1.0,
    ) -> Dict[str, object]:
        """Run real-asset cashflow audit and produce Day / 52-Week / Month / Rolling-Month-1 ledgers."""
        sim = self.simulate_cashflow(trades, mode=mode, basket_mult=basket_mult)
        ledger = sim.get("trade_ledger", [])
        if not ledger:
            return {"summary": sim, "daily": [], "weekly_52": [], "monthly": [], "rolling_m1": {}}

        df_l = pd.DataFrame(ledger)
        df_l["entry_time"] = pd.to_datetime(df_l["entry_time"], utc=True)
        df_l["date"] = df_l["entry_time"].dt.strftime("%Y-%m-%d")
        df_l["week"] = df_l["entry_time"].dt.strftime("%G-W%V")
        df_l["month"] = df_l["entry_time"].dt.strftime("%Y-%m")

        daily_rows = []
        for dt_str, grp in df_l.groupby("date", sort=True):
            daily_rows.append({
                "date": dt_str,
                "trades": int(len(grp)),
                "wins": int((grp["net_r"] > 0).sum()),
                "net_r": round(float(grp["net_r"].sum()), 2),
                "sized_r": round(float(grp["sized_r"].sum()), 2),
                "pnl_usd": round(float(grp["pnl_usd"].sum()), 2),
                "end_equity": round(float(grp["equity_after"].iloc[-1]), 2),
                "end_vault": round(float(grp["vault_after"].iloc[-1]), 2),
                "total_wealth": round(float(grp["total_wealth_after"].iloc[-1]), 2),
            })

        weekly_rows = []
        for wk_str, grp in df_l.groupby("week", sort=True):
            weekly_rows.append({
                "week": wk_str,
                "trades": int(len(grp)),
                "wins": int((grp["net_r"] > 0).sum()),
                "net_r": round(float(grp["net_r"].sum()), 2),
                "sized_r": round(float(grp["sized_r"].sum()), 2),
                "pnl_usd": round(float(grp["pnl_usd"].sum()), 2),
                "end_equity": round(float(grp["equity_after"].iloc[-1]), 2),
                "end_vault": round(float(grp["vault_after"].iloc[-1]), 2),
                "total_wealth": round(float(grp["total_wealth_after"].iloc[-1]), 2),
            })

        monthly_rows = []
        for mo_str, grp in df_l.groupby("month", sort=True):
            monthly_rows.append({
                "month": mo_str,
                "trades": int(len(grp)),
                "wr": round(100.0 * float((grp["net_r"] > 0).mean()), 1),
                "net_r": round(float(grp["net_r"].sum()), 2),
                "sized_r": round(float(grp["sized_r"].sum()), 2),
                "pnl_usd": round(float(grp["pnl_usd"].sum()), 2),
                "end_equity": round(float(grp["equity_after"].iloc[-1]), 2),
                "end_vault": round(float(grp["vault_after"].iloc[-1]), 2),
                "total_wealth": round(float(grp["total_wealth_after"].iloc[-1]), 2),
            })

        ordered = sorted(trades, key=lambda t: t["entry_time"])
        m1_profits: List[float] = []
        if ordered:
            t_start = ordered[0]["entry_time"].normalize()
            t_end = ordered[-1]["entry_time"] - pd.Timedelta(days=30)
            cur = t_start
            while cur <= t_end:
                nxt = cur + pd.Timedelta(days=30)
                sub = [t for t in ordered if cur <= t["entry_time"] < nxt]
                sub_sim = self.simulate_cashflow(sub, mode=mode, basket_mult=1.0)
                m1_profits.append(float(sub_sim.get("total_wealth_usd", self.starting_equity)) - self.starting_equity)
                cur += pd.DateOffset(months=1)

        rolling_m1 = {
            "windows": len(m1_profits),
            "median_usd": round(float(np.median(m1_profits)), 2) if m1_profits else 0.0,
            "mean_usd": round(float(np.mean(m1_profits)), 2) if m1_profits else 0.0,
            "p75_usd": round(float(np.percentile(m1_profits, 75)), 2) if m1_profits else 0.0,
            "p90_usd": round(float(np.percentile(m1_profits, 90)), 2) if m1_profits else 0.0,
            "pct_green": round(100.0 * sum(1 for x in m1_profits if x > 0) / max(1, len(m1_profits)), 1),
        }

        return {
            "summary": sim,
            "daily": daily_rows,
            "weekly_52": weekly_rows[-recent_weeks:] if recent_weeks > 0 else weekly_rows,
            "monthly": monthly_rows,
            "rolling_m1": rolling_m1,
        }


class IntradayCashflowSniperV7:
    """V7.0/V8.0 Intraday 5m/1H Scene-Graph Physics Coordinator."""

    def __init__(
        self,
        use_setup_a: bool = True,
        use_setup_b: bool = True,
        use_killzones: bool = False,
        bank_r: float = 2.8,
        bank_frac: float = 0.40,
        be_lock_r: float = 0.50,
        bank2_r: float = 5.5,
        bank2_frac: float = 0.40,
        be2_lock_r: float = 2.50,
        runner_tp_r: float = 12.0,
        stagnation_bars: int = 0,
        min_conviction: float = 0.55,
        atr_ratchet_mult: float = 0.0,
    ) -> None:
        self.perception = VisualPerceptionEngine()
        self.physics = SceneGraphPhysicsDetector(max_approach_ker=0.42, min_bpr_k=1.20, min_implied_r=3.0)
        self.liq_mapper = LiquidityPoolMapper(self.perception)
        self.regime = RegimeFilterEngine()
        self.prosecutor = AdversarialCrossExaminer(grace_bars=1, decay_lambda=0.65, min_conviction=min_conviction)
        self.exit_mgr = IntradayCashflowExitManager(
            bank_r=bank_r,
            bank_frac=bank_frac,
            be_lock_r=be_lock_r,
            bank2_r=bank2_r,
            bank2_frac=bank2_frac,
            be2_lock_r=be2_lock_r,
            runner_tp_r=runner_tp_r,
            stagnation_bars=stagnation_bars,
            atr_ratchet_mult=atr_ratchet_mult,
        )
        self.prot_exec = ProtectedSwingDetector()
        self.use_setup_a = bool(use_setup_a)
        self.use_setup_b = bool(use_setup_b)
        self.use_killzones = bool(use_killzones)

    @staticmethod
    def in_intraday_killzone(utc_hour: int, utc_min: int) -> bool:
        """London Open (07:00-11:00), NY Open (12:30-17:00), Asian Close/Sweep (00:00-02:30)."""
        hm = utc_hour * 60 + utc_min
        return (0 <= hm <= 150) or (420 <= hm <= 660) or (750 <= hm <= 1020)


IntradayCashflowSniperV8 = IntradayCashflowSniperV7


def run_v7_intraday_backtest(
    df_5m: pd.DataFrame,
    eval_start: pd.Timestamp,
    eval_end: pd.Timestamp,
    use_setup_a: bool = True,
    use_setup_b: bool = True,
    use_killzones: bool = False,
    bank_r: float = 3.0,
    bank_frac: float = 0.35,
    be_lock_r: float = 0.50,
    runner_tp_r: float = 10.0,
    stagnation_bars: int = 0,
    min_ker4: float = 0.15,
    min_sl_pct: float = 0.0045,
    max_sl_pct: float = 0.0180,
    use_htf_macro_align: bool = True,
    include_smc_sweep: bool = False,
    fee_mult: float = 1.0,
) -> Tuple[List[dict], Dict[str, object]]:
    """Strictly causal 5m/1H/4H V7.0 Intraday Cashflow Sniper backtest (Binance VIP0 fees + funding)."""
    return _run_intraday_sniper_core(
        df_5m=df_5m,
        eval_start=eval_start,
        eval_end=eval_end,
        use_setup_a=use_setup_a,
        use_setup_b=use_setup_b,
        use_killzones=use_killzones,
        bank_r=bank_r,
        bank_frac=bank_frac,
        be_lock_r=be_lock_r,
        bank2_r=5.5,
        bank2_frac=0.0,
        be2_lock_r=2.50,
        runner_tp_r=runner_tp_r,
        stagnation_bars=stagnation_bars,
        min_ker4=min_ker4,
        min_sl_pct=min_sl_pct,
        max_sl_pct=max_sl_pct,
        use_htf_macro_align=use_htf_macro_align,
        use_v8_prosecutor=False,
        min_conviction=0.35,
        min_clearance_r=0.0,
        min_rvol_entry=0.0,
        max_ext4_atr=99.0,
        setup_prefix="V7",
        include_smc_sweep=include_smc_sweep,
        fee_mult=fee_mult,
    )


def run_v8_intraday_backtest(
    df_5m: pd.DataFrame,
    eval_start: pd.Timestamp,
    eval_end: pd.Timestamp,
    use_setup_a: bool = True,
    use_setup_b: bool = True,
    use_killzones: bool = False,
    bank_r: float = 2.8,
    bank_frac: float = 0.40,
    be_lock_r: float = 0.50,
    bank2_r: float = 5.5,
    bank2_frac: float = 0.40,
    be2_lock_r: float = 2.50,
    runner_tp_r: float = 12.0,
    stagnation_bars: int = 0,
    atr_ratchet_mult: float = 0.0,
    min_ker4: float = 0.15,
    min_sl_pct: float = 0.0045,
    max_sl_pct: float = 0.0180,
    use_htf_macro_align: bool = True,
    use_v8_prosecutor: bool = True,
    min_conviction: float = 0.55,
    min_clearance_r: float = 3.0,
    min_rvol_entry: float = 0.90,
    max_ext4_atr: float = 2.50,
    include_smc_sweep: bool = False,
    fee_mult: float = 1.0,
) -> Tuple[List[dict], Dict[str, object]]:
    """Strictly causal 5m/1H/4H V8.0 Intraday Cashflow & Conviction-Ratchet backtest."""
    return _run_intraday_sniper_core(
        df_5m=df_5m,
        eval_start=eval_start,
        eval_end=eval_end,
        use_setup_a=use_setup_a,
        use_setup_b=use_setup_b,
        use_killzones=use_killzones,
        bank_r=bank_r,
        bank_frac=bank_frac,
        be_lock_r=be_lock_r,
        bank2_r=bank2_r,
        bank2_frac=bank2_frac,
        be2_lock_r=be2_lock_r,
        runner_tp_r=runner_tp_r,
        stagnation_bars=stagnation_bars,
        atr_ratchet_mult=atr_ratchet_mult,
        min_ker4=min_ker4,
        min_sl_pct=min_sl_pct,
        max_sl_pct=max_sl_pct,
        use_htf_macro_align=use_htf_macro_align,
        use_v8_prosecutor=use_v8_prosecutor,
        min_conviction=min_conviction,
        min_clearance_r=min_clearance_r,
        min_rvol_entry=min_rvol_entry,
        max_ext4_atr=max_ext4_atr,
        setup_prefix="V8",
        include_smc_sweep=include_smc_sweep,
        fee_mult=fee_mult,
    )


def _run_intraday_sniper_core(
    df_5m: pd.DataFrame,
    eval_start: pd.Timestamp,
    eval_end: pd.Timestamp,
    use_setup_a: bool = True,
    use_setup_b: bool = True,
    use_killzones: bool = False,
    bank_r: float = 2.8,
    bank_frac: float = 0.40,
    be_lock_r: float = 0.50,
    bank2_r: float = 5.5,
    bank2_frac: float = 0.40,
    be2_lock_r: float = 2.50,
    runner_tp_r: float = 12.0,
    stagnation_bars: int = 0,
    atr_ratchet_mult: float = 0.0,
    min_ker4: float = 0.15,
    min_sl_pct: float = 0.0045,
    max_sl_pct: float = 0.0180,
    use_htf_macro_align: bool = True,
    use_v8_prosecutor: bool = True,
    min_conviction: float = 0.55,
    min_clearance_r: float = 3.0,
    min_rvol_entry: float = 0.90,
    max_ext4_atr: float = 2.50,
    setup_prefix: str = "V8",
    include_smc_sweep: bool = False,
    fee_mult: float = 1.0,
) -> Tuple[List[dict], Dict[str, object]]:
    agg = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    df15 = df_5m.resample("15min").agg(agg).dropna()
    df1h = df_5m.resample("1h").agg(agg).dropna()
    df4h = df_5m.resample("4h").agg(agg).dropna()

    o5, h5, l5, c5 = (df_5m[col].to_numpy(float) for col in ("Open", "High", "Low", "Close"))
    ts5_ns = df_5m.index.as_unit("ns").asi8
    ts5_sec = ts5_ns / 1e9
    close5_ns = ts5_ns + int(300 * 1e9)
    atr5 = compute_atr_series(h5, l5, c5, 14)

    _, h15, l15, c15 = (df15[col].to_numpy(float) for col in ("Open", "High", "Low", "Close"))
    ts15_ns = df15.index.as_unit("ns").asi8
    close15_ns = ts15_ns + int(900 * 1e9)
    atr15 = compute_atr_series(h15, l15, c15, 14)

    o1, h1, l1, c1 = (df1h[col].to_numpy(float) for col in ("Open", "High", "Low", "Close"))
    ts1_ns = df1h.index.as_unit("ns").asi8
    close1_ns = ts1_ns + int(3600 * 1e9)
    atr1 = compute_atr_series(h1, l1, c1, 14)

    o4, h4, l4, c4 = (df4h[col].to_numpy(float) for col in ("Open", "High", "Low", "Close"))
    ts4_ns = df4h.index.as_unit("ns").asi8
    close4_ns = ts4_ns + int(14400 * 1e9)
    atr4 = compute_atr_series(h4, l4, c4, 14)
    e20_4h = pd.Series(c4).ewm(span=20, adjust=False).mean().to_numpy(float)

    sniper = IntradayCashflowSniperV8(
        use_setup_a=use_setup_a,
        use_setup_b=use_setup_b,
        use_killzones=use_killzones,
        bank_r=bank_r,
        bank_frac=bank_frac,
        be_lock_r=be_lock_r,
        bank2_r=bank2_r,
        bank2_frac=bank2_frac,
        be2_lock_r=be2_lock_r,
        runner_tp_r=runner_tp_r,
        stagnation_bars=stagnation_bars,
        min_conviction=min_conviction,
        atr_ratchet_mult=atr_ratchet_mult,
    )
    reg_4 = sniper.regime.precompute_frame_features(df4h)
    reg_5 = sniper.regime.precompute_frame_features(df_5m) if use_v8_prosecutor else None

    sw15 = sniper.perception.detect_causal_swings(ts15_ns, h15, l15, c15, atr15, max_swings=40000)
    sw15_by_conf: Dict[int, List[TopologicalSwing]] = {}
    for s in sw15:
        sw15_by_conf.setdefault(s.confirm_idx, []).append(s)

    sw1 = sniper.perception.detect_causal_swings(ts1_ns, h1, l1, c1, atr1, max_swings=24000)
    sw1_by_conf: Dict[int, List[TopologicalSwing]] = {}
    for s in sw1:
        sw1_by_conf.setdefault(s.confirm_idx, []).append(s)

    sw4 = sniper.perception.detect_causal_swings(ts4_ns, h4, l4, c4, atr4, max_swings=6000)
    sw4_by_conf: Dict[int, List[TopologicalSwing]] = {}
    for s in sw4:
        sw4_by_conf.setdefault(s.confirm_idx, []).append(s)

    vis1: List[TopologicalSwing] = []
    cur_hi4 = cur_lo4 = cur_hi1 = cur_lo1 = None
    tr4 = tr1 = 0
    pending_bpr: Optional[BPRZone] = None
    positions: List[TradePositionState] = []
    closed_trades: List[dict] = []
    p15 = p1 = p4 = cid = cool = 0
    eval0_ns = int(eval_start.as_unit("ns").value)
    eval1_ns = int(eval_end.as_unit("ns").value)

    for i5 in range(100, len(df_5m)):
        c_ns = int(close5_ns[i5])
        if c_ns >= eval1_ns:
            break
        while p4 < len(df4h) and close4_ns[p4] <= c_ns:
            for s in sw4_by_conf.get(p4, []):
                if s.side == 1:
                    cur_hi4 = s.price
                else:
                    cur_lo4 = s.price
            if cur_hi4 is not None and c4[p4] > cur_hi4:
                tr4 = 1
            elif cur_lo4 is not None and c4[p4] < cur_lo4:
                tr4 = -1
            p4 += 1

        while p1 < len(df1h) and close1_ns[p1] <= c_ns:
            for s in sw1_by_conf.get(p1, []):
                if s.side == 1:
                    cur_hi1 = s.price
                else:
                    cur_lo1 = s.price
                vis1.append(s)
            vis1 = vis1[-24:]
            if cur_hi1 is not None and c1[p1] > cur_hi1:
                tr1 = 1
            elif cur_lo1 is not None and c1[p1] < cur_lo1:
                tr1 = -1
            if vis1:
                sniper.liq_mapper.ingest_structural_swings(vis1, l1[:p1 + 1], h1[:p1 + 1], float(atr1[p1]), "1H")
            p1 += 1

        while p15 < len(df15) and close15_ns[p15] <= c_ns:
            sniper.prot_exec.update(i5, float(c15[p15]), sw15_by_conf.get(p15, []))
            p15 += 1

        sniper.liq_mapper.step_bar(float(ts5_sec[i5]), float(o5[i5]), float(h5[i5]), float(l5[i5]), float(c5[i5]), float(atr5[i5]))

        if p4 < 30 or p1 < 30 or c_ns < eval0_ns:
            continue

        # 1) Manage active intraday positions
        still: List[TradePositionState] = []
        for pos in positions:
            closed, gross_r, _ = sniper.exit_mgr.step_bar(
                pos, i5, float(h5[i5]), float(l5[i5]), float(c5[i5]), float(atr5[i5]), sniper.prot_exec, pos.meta.get("target_px")
            )
            if closed:
                hrs = max(0.1, (i5 - pos.entry_bar) * (5.0 / 60.0))
                t1_b = pos.meta.get("t1_bar")
                t2_b = pos.meta.get("t2_bar")
                t1_hrs = round((t1_b - pos.entry_bar) * (5.0 / 60.0), 2) if t1_b is not None else None
                t2_hrs = round((t2_b - pos.entry_bar) * (5.0 / 60.0), 2) if t2_b is not None else None
                fee_in = 0.0002
                fee_out = 0.0002 if pos.exit_reason == "VACUUM_TP" else 0.0007
                cost = fee_mult * ((fee_in + fee_out + 0.0001 * (hrs / 8.0)) / (pos.risk_dist / pos.entry_price)) * pos.risk_mult
                rc = dict(pos.meta.get("reasoning_chain", {}))
                closed_trades.append({
                    "cluster_id": pos.trade_id,
                    "entry_time": pos.entry_ts,
                    "exit_time": pd.Timestamp(c_ns, tz="UTC"),
                    "side": pos.side,
                    "entry_price": pos.entry_price,
                    "init_sl": pos.init_sl,
                    "sl_pct": pos.risk_dist / pos.entry_price,
                    "gross_r": gross_r,
                    "net_r": gross_r - cost,
                    "is_pyramid": pos.is_pyramid,
                    "is_aplus": bool(pos.meta.get("is_aplus", False)),
                    "conviction": float(rc.get("conviction", 0.60)),
                    "setup": pos.meta.get("setup", setup_prefix),
                    "outcome": pos.exit_reason,
                    "hold_hours": hrs,
                    "t1_hours": t1_hrs,
                    "t2_hours": t2_hrs,
                    "reasoning_chain": rc,
                })
                cool = i5 + 3
            else:
                still.append(pos)
        positions = still

        if positions or i5 <= cool:
            continue

        rs4 = sniper.regime.evaluate_bar(reg_4, p4 - 1)
        if rs4.ker < min_ker4:
            continue

        if sniper.use_killzones:
            ts_dt = pd.Timestamp(ts5_ns[i5], tz="UTC")
            if not sniper.in_intraday_killzone(ts_dt.hour, ts_dt.minute):
                pending_bpr = None
                continue

        a5 = float(atr5[i5])
        if a5 <= 0:
            continue
        if pending_bpr is None and (h5[i5] - l5[i5]) < 0.70 * a5:
            continue

        # Tier 1/2/3 HTF & Session liquidity barriers (clean 1H pools + 1H structural swings)
        barriers_hi = [
            p.price for p in sniper.liq_mapper.pools.values()
            if p.side == 1 and p.status in ("UNTAPPED", "SWEPT_WITH_REJECTION")
        ] + [s.price for s in vis1[-8:] if s.side == 1]
        barriers_lo = [
            p.price for p in sniper.liq_mapper.pools.values()
            if p.side == -1 and p.status in ("UNTAPPED", "SWEPT_WITH_REJECTION")
        ] + [s.price for s in vis1[-8:] if s.side == -1]

        entry_sig: Optional[Tuple[int, float, float, float, str, float, float, dict]] = None

        # Setup A: Compression Approach + Flat HTF Liquidity Sweep + 4H Trend Snap
        if sniper.use_setup_a:
            ca = sniper.physics.detect_compression_vacuum(o5, h5, l5, c5, atr5, i5, barriers_hi, barriers_lo, lookback=30)
            if ca is not None and ((not use_htf_macro_align) or ca.side == tr4):
                ep = float(c5[i5])
                slp = (ca.sweep_extreme - 1.0 * a5) if ca.side == 1 else (ca.sweep_extreme + 1.0 * a5)
                disp_sc = sniper.perception.displacement_score(o5[i5], h5[i5], l5[i5], c5[i5], a5)
                entry_sig = (
                    ca.side, ep, slp, ca.origin_anchor, f"{setup_prefix}_CompVacuum",
                    float(ca.vacuum_score), float(disp_sc),
                    {"ker4": round(rs4.ker, 2), "vac": round(ca.vacuum_score, 2), "imp_r": round(ca.implied_r, 2)},
                )

        # Setup B: Sweep + BPR / iFVG Polarity Inversion (1H & 4H Trend-Aligned Pullback/Snap)
        if entry_sig is None and sniper.use_setup_b:
            if pending_bpr is not None:
                if (i5 - pending_bpr.created_idx) > 6 or (pending_bpr.side == 1 and l5[i5] < pending_bpr.sweep_extreme) or (pending_bpr.side == -1 and h5[i5] > pending_bpr.sweep_extreme):
                    pending_bpr = None
                else:
                    retest_ok = (
                        (pending_bpr.side == 1 and l5[i5] <= pending_bpr.high and c5[i5] > o5[i5] and c5[i5] >= pending_bpr.mid)
                        or (pending_bpr.side == -1 and h5[i5] >= pending_bpr.low and c5[i5] < o5[i5] and c5[i5] <= pending_bpr.mid)
                    )
                    if retest_ok and ((not use_htf_macro_align) or (pending_bpr.side == tr4 and pending_bpr.side == tr1)):
                        ep = float(c5[i5])
                        slp = (pending_bpr.sweep_extreme - 1.0 * a5) if pending_bpr.side == 1 else (pending_bpr.sweep_extreme + 1.0 * a5)
                        disp_sc = float(sigmoid(pending_bpr.k_velocity, 1.25, 2.0))
                        entry_sig = (
                            pending_bpr.side, ep, slp, ep + pending_bpr.side * runner_tp_r * abs(ep - slp), f"{setup_prefix}_BPR_Retest",
                            float(pending_bpr.vacuum_score), disp_sc,
                            {"ker4": round(rs4.ker, 2), "k_vel": round(pending_bpr.k_velocity, 2), "vac": round(pending_bpr.vacuum_score, 2)},
                        )
                        pending_bpr = None
                    elif retest_ok:
                        pending_bpr = None
            if entry_sig is None:
                bpr = sniper.physics.detect_bpr_ifvg(o5, h5, l5, c5, atr5, i5, barriers_hi, barriers_lo, lookback_manip=10)
                if bpr is not None and ((not use_htf_macro_align) or (bpr.side == tr4 and bpr.side == tr1)):
                    if bpr.vacuum_score >= 0.55 and bpr.k_velocity >= 1.60:
                        ep = float(c5[i5])
                        slp = (bpr.sweep_extreme - 1.0 * a5) if bpr.side == 1 else (bpr.sweep_extreme + 1.0 * a5)
                        disp_sc = float(sigmoid(bpr.k_velocity, 1.25, 2.0))
                        entry_sig = (
                            bpr.side, ep, slp, ep + bpr.side * runner_tp_r * abs(ep - slp), f"{setup_prefix}_BPR_Snap",
                            float(bpr.vacuum_score), disp_sc,
                            {"ker4": round(rs4.ker, 2), "k_vel": round(bpr.k_velocity, 2), "vac": round(bpr.vacuum_score, 2)},
                        )
                    else:
                        pending_bpr = bpr

        if entry_sig is None:
            continue

        side, ep, slp, tgt_px, setup_tag, vac_sc, disp_sc, sc_meta = entry_sig
        rd = abs(ep - slp)
        sl_pct = rd / ep
        if rd <= 0 or not (min_sl_pct <= sl_pct <= max_sl_pct):
            continue

        is_aplus = setup_tag.endswith("BPR_Snap")
        if use_v8_prosecutor:
            rs5 = sniper.regime.evaluate_bar(reg_5, i5)
            if rs5.rvol < min_rvol_entry:
                continue
            ext4 = ((ep - e20_4h[p4 - 1]) * side) / max(float(atr4[p4 - 1]), 1e-12)
            if ext4 > max_ext4_atr:
                continue
            opp_walls = [s.price for s in vis1[-6:] if s.side == side]
            dir4 = 1 if c4[p4 - 1] > o4[p4 - 1] else -1
            verdict = sniper.prosecutor.cross_examine(
                side=side,
                entry_px=ep,
                risk_dist=rd,
                thesis_scores={
                    "sweep": 0.72,
                    "disp": disp_sc,
                    "vac": vac_sc,
                    "ker4": float(sigmoid(rs4.ker, 0.25, 9.0)),
                    "rvol": float(sigmoid(rs5.rvol, 1.3, 2.0)),
                },
                thesis_weights={"sweep": 1.1, "disp": 1.2, "vac": 1.0, "ker4": 1.0, "rvol": 0.7},
                opposing_htf_walls=opp_walls,
                ker_4h=rs4.ker,
                body_ratio_4h=rs4.body_ratio,
                dir_4h_candle=dir4,
                htf_trend_1h=tr1,
                htf_trend_4h=tr4,
                rvol_entry=rs5.rvol,
                rvol_opp=1.0,
                is_counter_trend_sweep=(side != tr4),
                min_clearance_r=min_clearance_r,
            )
            if not verdict.approved:
                continue
            sc_meta["conviction"] = round(verdict.conviction, 3)
            sc_meta["rvol5"] = round(rs5.rvol, 2)
            sc_meta["ext4"] = round(ext4, 2)
            is_aplus = is_aplus or (verdict.conviction >= 0.72)

        cid += 1
        positions.append(
            TradePositionState(
                trade_id=cid, side=side, entry_bar=i5,
                entry_ts=pd.Timestamp(c_ns, tz="UTC"), entry_price=ep,
                init_sl=slp, cur_sl=slp, risk_dist=rd,
                meta={"setup": setup_tag, "target_px": tgt_px, "is_aplus": is_aplus, "reasoning_chain": sc_meta},
            )
        )

    if include_smc_sweep:
        tr_smc, _ = run_smc_sweep_causal_backtest(df_5m, eval_start, eval_end, use_v6_prosecutor=True, fee_mult=fee_mult, tp_r=10.0)
        for _t in tr_smc:
            _t["is_aplus"] = True
        closed_trades = sorted(closed_trades + tr_smc, key=lambda t: t["entry_time"])

    return closed_trades, _summarize_trades(closed_trades)


class DailySessionSniperV9:
    """V9.0 Daily Session & Structural Liquidity Sweep Coordinator + Zero-Risk Slot Recycling."""

    def __init__(
        self,
        bank_r: float = 2.0,
        bank_frac: float = 0.15,
        be_lock_r: float = 0.35,
        bank2_r: float = 4.5,
        bank2_frac: float = 0.20,
        be2_lock_r: float = 2.00,
        runner_tp_r: float = 10.0,
        prot_trail_mfe_r: float = 5.0,
        expiry_hours: float = 5.0,
    ) -> None:
        self.session_tracker = DailySessionLiquidityTracker(expiry_hours=expiry_hours)
        self.regime = RegimeFilterEngine()
        self.exit_mgr = HighVelocityCashflowExitManager(
            bank_r=bank_r,
            bank_frac=bank_frac,
            be_lock_r=be_lock_r,
            bank2_r=bank2_r,
            bank2_frac=bank2_frac,
            be2_lock_r=be2_lock_r,
            runner_tp_r=runner_tp_r,
            prot_trail_mfe_r=prot_trail_mfe_r,
        )
        self.prot_exec = ProtectedSwingDetector()


def _step_causal_fractal_swing(
    buf_h: deque,
    buf_l: deque,
    k: int,
    bar_i: int,
    act_hi: List[List[float]],
    act_lo: List[List[float]],
    last_hi: Optional[float],
    last_lo: Optional[float],
) -> Tuple[List[List[float]], List[List[float]], Optional[float], Optional[float]]:
    """Strictly causal (2k+1)-bar pivot detector confirmed at bar_i for center bar (bar_i - k)."""
    if len(buf_h) == 2 * k + 1:
        m = k
        ch, cl = float(buf_h[m]), float(buf_l[m])
        if all(ch >= buf_h[j] for j in range(len(buf_h)) if j != m) and any(ch > buf_h[j] for j in range(len(buf_h)) if j != m):
            last_hi = ch
            act_hi.append([bar_i - k, ch])
            act_hi = act_hi[-25:]
        if all(cl <= buf_l[j] for j in range(len(buf_l)) if j != m) and any(cl < buf_l[j] for j in range(len(buf_l)) if j != m):
            last_lo = cl
            act_lo.append([bar_i - k, cl])
            act_lo = act_lo[-25:]
    return act_hi, act_lo, last_hi, last_lo


def run_v9_daily_session_backtest(
    df_5m: pd.DataFrame,
    eval_start: pd.Timestamp,
    eval_end: pd.Timestamp,
    asset: str = "BTCUSD",
    use_lon: bool = True,
    use_1h_k2: bool = True,
    use_15m_ny: bool = True,
    include_v8_physics: bool = True,
    include_v6_4h: bool = True,
    htf_align_mode: str = "tr4_eq_tr1",
    bank_r: float = 2.0,
    bank_frac: float = 0.15,
    be_lock_r: float = 0.35,
    bank2_r: float = 4.5,
    bank2_frac: float = 0.20,
    be2_lock_r: float = 2.00,
    runner_tp_r: float = 10.0,
    min_ker4: float = 0.15,
    min_rvol_15m_ny: float = 1.20,
    min_sl_pct: float = 0.0020,
    max_sl_pct: float = 0.0180,
    dedup_same_side_bars: int = 12,
    fee_mult: float = 1.0,
) -> Tuple[List[dict], Dict[str, object]]:
    """Strictly causal V9.0 Daily Session & Multi-TF Liquidity Sweep + V8 Physics + V6 Cognitive backtest.

    Executes causal Session Sweeps (`LON` 07-12 UTC H/L swept >=12 UTC, `1H_K2` 1H k=2 swept >=09 UTC,
    `15M_NY` 15m k=3 swept 12-21 UTC with RVOL>=1.20) confirmed by 5m BOS + 0.25*ATR5 FVG retest,
    managed by `HighVelocityCashflowExitManager` with BE+0.35R Zero-Risk Slot Recycling.
    """
    agg = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    df15 = df_5m.resample("15min").agg(agg).dropna()
    df1h = df_5m.resample("1h").agg(agg).dropna()
    df4h = df_5m.resample("4h").agg(agg).dropna()

    o5, h5, l5, c5 = (df_5m[col].to_numpy(float) for col in ("Open", "High", "Low", "Close"))
    ts5_ns = df_5m.index.as_unit("ns").asi8
    close5_ns = ts5_ns + int(300 * 1e9)
    atr5 = compute_atr_series(h5, l5, c5, 14)

    h15, l15, c15 = (df15[col].to_numpy(float) for col in ("High", "Low", "Close"))
    close15_ns = df15.index.as_unit("ns").asi8 + int(900 * 1e9)
    h1, l1, c1 = (df1h[col].to_numpy(float) for col in ("High", "Low", "Close"))
    close1_ns = df1h.index.as_unit("ns").asi8 + int(3600 * 1e9)
    h4, l4, c4 = (df4h[col].to_numpy(float) for col in ("High", "Low", "Close"))
    close4_ns = df4h.index.as_unit("ns").asi8 + int(14400 * 1e9)
    e20_4h = pd.Series(c4).ewm(span=20, adjust=False).mean().to_numpy(float)

    sniper = DailySessionSniperV9(
        bank_r=bank_r,
        bank_frac=bank_frac,
        be_lock_r=be_lock_r,
        bank2_r=bank2_r,
        bank2_frac=bank2_frac,
        be2_lock_r=be2_lock_r,
        runner_tp_r=runner_tp_r,
    )
    reg4 = sniper.regime.precompute_frame_features(df4h)
    reg5 = sniper.regime.precompute_frame_features(df_5m)
    ker4_arr, rvol5_arr = reg4["ker"], reg5["rvol"]

    b4h, b4l = deque(maxlen=5), deque(maxlen=5)
    l4_hi = l4_lo = None
    tr4 = 0
    b1h, b1l = deque(maxlen=5), deque(maxlen=5)
    k2_hi: List[List[float]] = []
    k2_lo: List[List[float]] = []
    l1_hi = l1_lo = None
    tr1 = 0
    b15_h, b15_l = deque(maxlen=7), deque(maxlen=7)
    k15_hi: List[List[float]] = []
    k15_lo: List[List[float]] = []
    b5h, b5l = deque(maxlen=5), deque(maxlen=5)
    l5_hi = l5_lo = None

    c_k2: List[Tuple[int, int, float]] = []
    c_15: List[Tuple[int, int, float]] = []
    p15 = p1 = p4 = 0
    ts_dt_arr = pd.to_datetime(ts5_ns, utc=True)
    eval0_ns = int(eval_start.as_unit("ns").value)
    eval1_ns = int(eval_end.as_unit("ns").value)

    sleeves = ("LON", "1H_K2", "15M_NY")
    pos_map: Dict[str, Optional[TradePositionState]] = {s: None for s in sleeves}
    pend_map: Dict[str, Optional[dict]] = {s: None for s in sleeves}
    last_side_bar: Dict[int, int] = {1: -999, -1: -999}
    closed_trades: List[dict] = []
    cid = 0

    for i5 in range(80, len(df_5m)):
        c5_ns = int(close5_ns[i5])
        if c5_ns >= eval1_ns:
            break
        dt5 = ts_dt_arr[i5]
        hr5 = int(dt5.hour)
        a5 = float(atr5[i5])

        sniper.session_tracker.step_bar(dt5, c5_ns, float(o5[i5]), float(h5[i5]), float(l5[i5]), float(c5[i5]), a5)

        while p4 < len(df4h) and close4_ns[p4] <= c5_ns:
            b4h.append(h4[p4])
            b4l.append(l4[p4])
            _, _, l4_hi, l4_lo = _step_causal_fractal_swing(b4h, b4l, 2, p4, [], [], l4_hi, l4_lo)
            if l4_hi is not None and c4[p4] > l4_hi:
                tr4 = 1
            elif l4_lo is not None and c4[p4] < l4_lo:
                tr4 = -1
            p4 += 1

        while p1 < len(df1h) and close1_ns[p1] <= c5_ns:
            hh, hl, hc = float(h1[p1]), float(l1[p1]), float(c1[p1])
            c_k2 = [x for x in c_k2 if (c5_ns - x[1]) <= 5 * 3600 * 10**9][-10:]
            for idx_s, p_lo in k2_lo:
                if (p1 - idx_s) >= 3 and hl < p_lo and hc > p_lo:
                    c_k2.append((1, int(close1_ns[p1]), hl))
            for idx_s, p_hi in k2_hi:
                if (p1 - idx_s) >= 3 and hh > p_hi and hc < p_hi:
                    c_k2.append((-1, int(close1_ns[p1]), hh))
            b1h.append(hh)
            b1l.append(hl)
            k2_hi, k2_lo, l1_hi, l1_lo = _step_causal_fractal_swing(b1h, b1l, 2, p1, k2_hi, k2_lo, l1_hi, l1_lo)
            k2_hi = [x for x in k2_hi if hh <= x[1]]
            k2_lo = [x for x in k2_lo if hl >= x[1]]
            if l1_hi is not None and hc > l1_hi:
                tr1 = 1
            elif l1_lo is not None and hc < l1_lo:
                tr1 = -1
            p1 += 1

        while p15 < len(df15) and close15_ns[p15] <= c5_ns:
            hh, hl, hc = float(h15[p15]), float(l15[p15]), float(c15[p15])
            c_15 = [x for x in c_15 if (c5_ns - x[1]) <= 3 * 3600 * 10**9][-10:]
            for idx_s, p_lo in k15_lo:
                if (p15 - idx_s) >= 4 and hl < p_lo and hc > p_lo:
                    c_15.append((1, int(close15_ns[p15]), hl))
            for idx_s, p_hi in k15_hi:
                if (p15 - idx_s) >= 4 and hh > p_hi and hc < p_hi:
                    c_15.append((-1, int(close15_ns[p15]), hh))
            b15_h.append(hh)
            b15_l.append(hl)
            k15_hi, k15_lo, _, _ = _step_causal_fractal_swing(b15_h, b15_l, 3, p15, k15_hi, k15_lo, None, None)
            k15_hi = [x for x in k15_hi if hh <= x[1]]
            k15_lo = [x for x in k15_lo if hl >= x[1]]
            p15 += 1

        b5h.append(h5[i5 - 1])
        b5l.append(l5[i5 - 1])
        _, _, l5_hi, l5_lo = _step_causal_fractal_swing(b5h, b5l, 2, i5 - 1, [], [], l5_hi, l5_lo)

        # 1) Manage active V9 positions via HighVelocityCashflowExitManager
        for slv in sleeves:
            pos = pos_map[slv]
            if pos is None:
                continue
            closed, gross_r, _ = sniper.exit_mgr.step_bar(
                pos, i5, float(h5[i5]), float(l5[i5]), float(c5[i5]), a5, sniper.prot_exec, None
            )
            if closed:
                hrs = max(0.08, (i5 - pos.entry_bar) * (5.0 / 60.0))
                t1_b = pos.meta.get("t1_bar")
                t2_b = pos.meta.get("t2_bar")
                t1_hrs = round((t1_b - pos.entry_bar) * (5.0 / 60.0), 2) if t1_b is not None else None
                t2_hrs = round((t2_b - pos.entry_bar) * (5.0 / 60.0), 2) if t2_b is not None else None
                t1_ts = (pos.entry_ts + pd.Timedelta(hours=t1_hrs)) if t1_hrs is not None else None
                fee_in = 0.0002
                fee_out = 0.0002 if pos.exit_reason == "VACUUM_TP" else 0.0007
                cost = fee_mult * ((fee_in + fee_out + 0.0001 * (hrs / 8.0)) / (pos.risk_dist / pos.entry_price))
                closed_trades.append({
                    "cluster_id": pos.trade_id,
                    "asset": asset,
                    "entry_time": pos.entry_ts,
                    "exit_time": pd.Timestamp(c5_ns, tz="UTC"),
                    "t1_time": t1_ts,
                    "side": pos.side,
                    "entry_price": pos.entry_price,
                    "init_sl": pos.init_sl,
                    "sl_pct": pos.risk_dist / pos.entry_price,
                    "gross_r": gross_r,
                    "net_r": gross_r - cost,
                    "is_pyramid": False,
                    "is_aplus": True,
                    "conviction": 0.78,
                    "setup": f"V9_{slv}",
                    "outcome": pos.exit_reason,
                    "hold_hours": hrs,
                    "t1_hours": t1_hrs,
                    "t2_hours": t2_hrs,
                    "reasoning_chain": dict(pos.meta.get("reasoning_chain", {})),
                })
                pos_map[slv] = None

        if c5_ns < eval0_ns or p4 < 30 or p1 < 30:
            continue

        # 2) Fill pending 5m FVG limit orders (with Zero-Risk Slot Recycling & cross-sleeve same-side dedup)
        for slv in sleeves:
            pend = pend_map[slv]
            if pend is not None and pos_map[slv] is None:
                if i5 > pend["exp"]:
                    pend_map[slv] = None
                elif (pend["sd"] == 1 and l5[i5] <= pend["ep"]) or (pend["sd"] == -1 and h5[i5] >= pend["ep"]):
                    same_unprot = any(
                        p is not None and p.side == pend["sd"] and not HighVelocityCashflowExitManager.is_zero_risk(p)
                        for p in pos_map.values()
                    )
                    if (not same_unprot) and (i5 - last_side_bar[pend["sd"]] >= dedup_same_side_bars):
                        cid += 1
                        last_side_bar[pend["sd"]] = i5
                        pos_map[slv] = TradePositionState(
                            trade_id=cid,
                            side=pend["sd"],
                            entry_bar=i5,
                            entry_ts=pd.Timestamp(c5_ns, tz="UTC"),
                            entry_price=pend["ep"],
                            init_sl=pend["sl"],
                            cur_sl=pend["sl"],
                            risk_dist=pend["rd"],
                            meta={"setup": f"V9_{slv}", "reasoning_chain": pend["meta"]},
                        )
                    pend_map[slv] = None

        if a5 <= 0 or abs(c5[i5 - 1] - o5[i5 - 1]) < 1.0 * a5:
            continue
        k4 = float(ker4_arr[p4 - 1])
        rv5 = float(rvol5_arr[i5])
        if k4 < min_ker4:
            continue
        e4_tr = 1 if c4[p4 - 1] > e20_4h[p4 - 1] else -1

        lon_cand = [(s.side, s.sweep_ns, s.sweep_extreme) for s in sniper.session_tracker.active_lon_sweeps]
        for slv, clist, ok_hr in (
            ("LON", lon_cand, use_lon and hr5 >= 12),
            ("1H_K2", c_k2, use_1h_k2 and hr5 >= 9),
            ("15M_NY", c_15, use_15m_ny and (12 <= hr5 <= 21) and rv5 >= min_rvol_15m_ny),
        ):
            if (not ok_hr) or pos_map[slv] is not None or pend_map[slv] is not None:
                continue
            for sd, _, sl_b in reversed(clist):
                if htf_align_mode == "tr4_eq_tr1" and (sd != tr1 or sd != tr4):
                    continue
                if htf_align_mode == "e4_and_tr1" and (sd != tr1 or sd != e4_tr):
                    continue
                ok = False
                ep = slp = 0.0
                if sd == 1 and l5[i5] >= sl_b and l5_hi is not None:
                    if c5[i5] > l5_hi and (l5[i5] - h5[i5 - 2]) >= 0.25 * a5 and c5[i5 - 1] > o5[i5 - 1]:
                        slp = min(sl_b - a5, c5[i5] - max(1.5 * a5, c5[i5] * 0.0020))
                        ep = float(l5[i5])
                        ok = True
                elif sd == -1 and h5[i5] <= sl_b and l5_lo is not None:
                    if c5[i5] < l5_lo and (l5[i5 - 2] - h5[i5]) >= 0.25 * a5 and c5[i5 - 1] < o5[i5 - 1]:
                        slp = max(sl_b + a5, c5[i5] + max(1.5 * a5, c5[i5] * 0.0020))
                        ep = float(h5[i5])
                        ok = True
                if ok:
                    rd = abs(ep - slp)
                    if ep > 0 and min_sl_pct <= (rd / ep) <= max_sl_pct:
                        pend_map[slv] = {
                            "sd": sd,
                            "ep": ep,
                            "sl": slp,
                            "rd": rd,
                            "exp": i5 + 8,
                            "meta": {"ker4": round(k4, 2), "rvol5": round(rv5, 2), "source": slv},
                        }
                        break

    if include_v8_physics:
        tr_v8, _ = run_v8_intraday_backtest(df_5m, eval_start, eval_end, include_smc_sweep=False, fee_mult=fee_mult)
        for _t in tr_v8:
            _t["asset"] = asset
            _t.setdefault("engine", _t.get("setup", "V8_Physics"))
            if _t.get("t1_hours") is not None and _t.get("t1_time") is None:
                _t["t1_time"] = _t["entry_time"] + pd.Timedelta(hours=float(_t["t1_hours"]))
        closed_trades.extend(tr_v8)

    if include_v6_4h:
        tr_v6, _ = run_v6_cognitive_backtest(df_5m, eval_start, eval_end, fee_mult=fee_mult)
        for _t in tr_v6:
            _t["asset"] = asset
            _t.setdefault("setup", "4H_V6_Cognitive")
            _t.setdefault("engine", "4H_V6_Cognitive")
            if _t.get("t1_time") is None:
                _t["t1_time"] = _t["exit_time"]
        closed_trades.extend(tr_v6)

    closed_trades = sorted(closed_trades, key=lambda t: t["entry_time"])
    return closed_trades, _summarize_trades(closed_trades)


def run_v10_btc_topo_sweeps_backtest(
    df_5m: pd.DataFrame,
    eval_start: pd.Timestamp,
    eval_end: pd.Timestamp,
    *,
    asset: str = "BTCUSD",
    use_lon: bool = True,
    use_1h_topo: bool = True,
    use_15m_topo: bool = True,
    zig_4h: float = 1.25,
    zig_1h: float = 1.15,
    zig_15m: float = 1.15,
    zig_5m: float = 0.50,
    min_prom_atr: float = 1.40,
    min_rvol_entry: float = 1.20,
    min_clearance_r: float = 2.5,
    min_ker4: float = 0.15,
    min_sl_pct: float = 0.0020,
    max_sl_pct: float = 0.0180,
    dedup_same_side_bars: int = 12,
    fee_mult: float = 1.0,
    exit_mgr_override: Optional[HighVelocityCashflowExitManager] = None,
    setup_prefix: str = "V10",
) -> Tuple[List[dict], Dict[str, object]]:
    """V10.0 Topological Liquidity Sweep Engine (ZERO k=2/k=3 fractals + 45/40/15 Front-Loaded Exit).

    Replaces k=2/k=3 fractals with strictly causal ATR-ZigZag TopologicalSwings, validates every
    setup through AdversarialCrossExaminer (RVOL >= 1.20, prominence >= 1.40 ATR, wall clearance >= 2.5R),
    and executes the V10FrontLoadedCashflowExitManager 45/40/15 cascade (2.2R -> +0.35R BE, 4.5R -> +2.0R, 10R runner).
    """
    agg = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    df15 = df_5m.resample("15min").agg(agg).dropna()
    df1h = df_5m.resample("1h").agg(agg).dropna()
    df4h = df_5m.resample("4h").agg(agg).dropna()

    o5, h5, l5, c5 = (df_5m[col].to_numpy(float) for col in ("Open", "High", "Low", "Close"))
    ts5_ns = df_5m.index.as_unit("ns").asi8
    close5_ns = ts5_ns + int(300 * 1e9)
    atr5 = compute_atr_series(h5, l5, c5, 14)

    h15, l15, c15 = (df15[col].to_numpy(float) for col in ("High", "Low", "Close"))
    ts15_ns = df15.index.as_unit("ns").asi8
    close15_ns = ts15_ns + int(900 * 1e9)
    atr15 = compute_atr_series(h15, l15, c15, 14)

    h1, l1, c1 = (df1h[col].to_numpy(float) for col in ("High", "Low", "Close"))
    ts1_ns = df1h.index.as_unit("ns").asi8
    close1_ns = ts1_ns + int(3600 * 1e9)
    atr1 = compute_atr_series(h1, l1, c1, 14)

    o4, h4, l4, c4 = (df4h[col].to_numpy(float) for col in ("Open", "High", "Low", "Close"))
    ts4_ns = df4h.index.as_unit("ns").asi8
    close4_ns = ts4_ns + int(14400 * 1e9)
    atr4 = compute_atr_series(h4, l4, c4, 14)

    rf = RegimeFilterEngine()
    reg4 = rf.precompute_frame_features(df4h)
    reg5 = rf.precompute_frame_features(df_5m)
    ker4_arr = reg4["ker"]
    br4_arr = reg4["body_ratio"]
    rvol5_arr = reg5["rvol"]
    ts_dt_arr = pd.to_datetime(ts5_ns, utc=True)

    sw15_c = build_causal_topo_events(ts15_ns, h15, l15, c15, atr15, zig_mult=zig_15m)
    sw1_c = build_causal_topo_events(ts1_ns, h1, l1, c1, atr1, zig_mult=zig_1h)
    sw4_c = build_causal_topo_events(ts4_ns, h4, l4, c4, atr4, zig_mult=zig_4h)
    sw5_c = build_causal_topo_events(ts5_ns, h5, l5, c5, atr5, zig_mult=zig_5m)

    perc = VisualPerceptionEngine()
    sess = DailySessionLiquidityTracker(expiry_hours=5.0)
    pros = AdversarialCrossExaminer(min_conviction=0.55)
    exit_mgr = exit_mgr_override if exit_mgr_override is not None else V10FrontLoadedCashflowExitManager()
    prot15 = ProtectedSwingDetector()

    p15 = p1 = p4 = 0
    act1_hi: List[TopologicalSwing] = []
    act1_lo: List[TopologicalSwing] = []
    act15_hi: List[TopologicalSwing] = []
    act15_lo: List[TopologicalSwing] = []
    topo4_hi = topo4_lo = topo1_hi = topo1_lo = topo5_hi = topo5_lo = None
    tr4 = tr1 = 0
    c_1h: List[Tuple[int, int, float, float]] = []
    c_15: List[Tuple[int, int, float, float]] = []

    eval0_ns = int(eval_start.as_unit("ns").value)
    eval1_ns = int(eval_end.as_unit("ns").value)
    sleeves = ("LON", "1H_TOPO", "15M_TOPO")
    pos_map: Dict[str, Optional[TradePositionState]] = {s: None for s in sleeves}
    pend_map: Dict[str, Optional[dict]] = {s: None for s in sleeves}
    last_side_bar = {1: -999, -1: -999}
    closed_trades: List[dict] = []
    cid = 0

    for i5 in range(100, len(df_5m)):
        c5_ns = int(close5_ns[i5])
        if c5_ns >= eval1_ns:
            break
        dt5 = ts_dt_arr[i5]
        hr5 = dt5.hour
        a5 = float(atr5[i5])
        sess.step_bar(dt5, c5_ns, float(o5[i5]), float(h5[i5]), float(l5[i5]), float(c5[i5]), a5)

        while p4 < len(df4h) and close4_ns[p4] <= c5_ns:
            for s in sw4_c.get(p4, []):
                if s.side == 1:
                    topo4_hi = s.price
                else:
                    topo4_lo = s.price
            if topo4_hi is not None and c4[p4] > topo4_hi:
                tr4 = 1
            elif topo4_lo is not None and c4[p4] < topo4_lo:
                tr4 = -1
            p4 += 1

        while p1 < len(df1h) and close1_ns[p1] <= c5_ns:
            hh, hl, hc = float(h1[p1]), float(l1[p1]), float(c1[p1])
            c_1h = [x for x in c_1h if (c5_ns - x[1]) <= 5 * 3600 * 10**9][-10:]
            for sw in act1_lo:
                if (p1 - sw.idx) >= 3 and sw.prominence_atr >= min_prom_atr and hl < sw.price and hc > sw.price:
                    c_1h.append((1, int(close1_ns[p1]), hl, sw.structural_weight))
            for sw in act1_hi:
                if (p1 - sw.idx) >= 3 and sw.prominence_atr >= min_prom_atr and hh > sw.price and hc < sw.price:
                    c_1h.append((-1, int(close1_ns[p1]), hh, sw.structural_weight))
            for sw in sw1_c.get(p1, []):
                if sw.side == 1:
                    topo1_hi = sw.price
                    act1_hi.append(sw)
                    act1_hi = act1_hi[-24:]
                else:
                    topo1_lo = sw.price
                    act1_lo.append(sw)
                    act1_lo = act1_lo[-24:]
            act1_hi = [x for x in act1_hi if hh <= x.price]
            act1_lo = [x for x in act1_lo if hl >= x.price]
            if topo1_hi is not None and hc > topo1_hi:
                tr1 = 1
            elif topo1_lo is not None and hc < topo1_lo:
                tr1 = -1
            p1 += 1

        while p15 < len(df15) and close15_ns[p15] <= c5_ns:
            hh, hl, hc = float(h15[p15]), float(l15[p15]), float(c15[p15])
            new15 = sw15_c.get(p15, [])
            prot15.update(i5, hc, new15)
            c_15 = [x for x in c_15 if (c5_ns - x[1]) <= 3 * 3600 * 10**9][-10:]
            for sw in act15_lo:
                if (p15 - sw.idx) >= 4 and sw.prominence_atr >= min_prom_atr and hl < sw.price and hc > sw.price:
                    c_15.append((1, int(close15_ns[p15]), hl, sw.structural_weight))
            for sw in act15_hi:
                if (p15 - sw.idx) >= 4 and sw.prominence_atr >= min_prom_atr and hh > sw.price and hc < sw.price:
                    c_15.append((-1, int(close15_ns[p15]), hh, sw.structural_weight))
            for sw in new15:
                if sw.side == 1:
                    act15_hi.append(sw)
                    act15_hi = act15_hi[-24:]
                else:
                    act15_lo.append(sw)
                    act15_lo = act15_lo[-24:]
            act15_hi = [x for x in act15_hi if hh <= x.price]
            act15_lo = [x for x in act15_lo if hl >= x.price]
            p15 += 1

        for sw in sw5_c.get(i5 - 1, []):
            if sw.side == 1:
                topo5_hi = sw.price
            else:
                topo5_lo = sw.price

        for slv in sleeves:
            pos = pos_map[slv]
            if pos is None:
                continue
            closed, gross_r, _ = exit_mgr.step_bar(pos, i5, float(h5[i5]), float(l5[i5]), float(c5[i5]), a5, prot15, None)
            if closed:
                hrs = max(0.08, (i5 - pos.entry_bar) * (5.0 / 60.0))
                t1_b = pos.meta.get("t1_bar")
                t2_b = pos.meta.get("t2_bar")
                t1_hrs = round((t1_b - pos.entry_bar) * (5.0 / 60.0), 2) if t1_b is not None else None
                t2_hrs = round((t2_b - pos.entry_bar) * (5.0 / 60.0), 2) if t2_b is not None else None
                t1_ts = (pos.entry_ts + pd.Timedelta(hours=t1_hrs)) if t1_hrs is not None else None
                fee_in = 0.0002
                fee_out = 0.0002 if pos.exit_reason == "VACUUM_TP" else 0.0007
                cost = fee_mult * ((fee_in + fee_out + 0.0001 * (hrs / 8.0)) / (pos.risk_dist / pos.entry_price))
                closed_trades.append({
                    "cluster_id": pos.trade_id,
                    "asset": asset,
                    "entry_time": pos.entry_ts,
                    "exit_time": pd.Timestamp(c5_ns, tz="UTC"),
                    "t1_time": t1_ts,
                    "side": pos.side,
                    "entry_price": pos.entry_price,
                    "init_sl": pos.init_sl,
                    "sl_pct": pos.risk_dist / pos.entry_price,
                    "gross_r": gross_r,
                    "net_r": gross_r - cost,
                    "is_pyramid": False,
                    "is_aplus": True,
                    "conviction": float(pos.meta.get("reasoning_chain", {}).get("conviction", 0.78)),
                    "setup": f"{setup_prefix}_{slv}",
                    "engine": f"{setup_prefix}_{slv}",
                    "outcome": pos.exit_reason,
                    "hold_hours": hrs,
                    "t1_hours": t1_hrs,
                    "t2_hours": t2_hrs,
                    "reasoning_chain": dict(pos.meta.get("reasoning_chain", {})),
                })
                pos_map[slv] = None

        if c5_ns < eval0_ns or p4 < 30 or p1 < 30 or a5 <= 0:
            continue

        for slv in sleeves:
            pend = pend_map[slv]
            if pend is not None and pos_map[slv] is None:
                if i5 > pend["exp"]:
                    pend_map[slv] = None
                elif (pend["sd"] == 1 and l5[i5] <= pend["ep"]) or (pend["sd"] == -1 and h5[i5] >= pend["ep"]):
                    same_unprot = any(
                        p is not None and p.side == pend["sd"] and not exit_mgr.is_zero_risk(p)
                        for p in pos_map.values()
                    )
                    if (not same_unprot) and (i5 - last_side_bar[pend["sd"]] >= dedup_same_side_bars):
                        cid += 1
                        last_side_bar[pend["sd"]] = i5
                        pos_map[slv] = TradePositionState(
                            trade_id=cid,
                            side=pend["sd"],
                            entry_bar=i5,
                            entry_ts=pd.Timestamp(c5_ns, tz="UTC"),
                            entry_price=pend["ep"],
                            init_sl=pend["sl"],
                            cur_sl=pend["sl"],
                            risk_dist=pend["rd"],
                            meta={"setup": f"{setup_prefix}_{slv}", "reasoning_chain": pend["meta"]},
                        )
                    pend_map[slv] = None

        k4 = float(ker4_arr[p4 - 1])
        rv5 = float(rvol5_arr[i5])
        if k4 < min_ker4 or rv5 < min_rvol_entry or abs(c5[i5 - 1] - o5[i5 - 1]) < 1.15 * a5:
            continue

        lon_cand = [(s.side, s.sweep_ns, s.sweep_extreme, 0.80) for s in sess.active_lon_sweeps]
        for slv, clist, ok_hr in (
            ("LON", lon_cand, use_lon and hr5 >= 12),
            ("1H_TOPO", c_1h, use_1h_topo and hr5 >= 9),
            ("15M_TOPO", c_15, use_15m_topo and (12 <= hr5 <= 21) and rv5 >= min_rvol_entry),
        ):
            if (not ok_hr) or pos_map[slv] is not None or pend_map[slv] is not None:
                continue
            for sd, _, sl_b, sw_w in reversed(clist):
                if sd != tr1 or sd != tr4:
                    continue
                ok = False
                ep = slp = 0.0
                if sd == 1 and l5[i5] >= sl_b and topo5_hi is not None:
                    if c5[i5] > topo5_hi and (l5[i5] - h5[i5 - 2]) >= 0.30 * a5 and c5[i5 - 1] > o5[i5 - 1]:
                        slp = min(sl_b - a5, c5[i5] - max(1.5 * a5, c5[i5] * 0.0020))
                        ep = float(l5[i5])
                        ok = True
                elif sd == -1 and h5[i5] <= sl_b and topo5_lo is not None:
                    if c5[i5] < topo5_lo and (l5[i5 - 2] - h5[i5]) >= 0.30 * a5 and c5[i5 - 1] < o5[i5 - 1]:
                        slp = max(sl_b + a5, c5[i5] + max(1.5 * a5, c5[i5] * 0.0020))
                        ep = float(h5[i5])
                        ok = True
                if ok:
                    rd = abs(ep - slp)
                    if not (min_sl_pct <= (rd / ep) <= max_sl_pct):
                        continue
                    opp = [x.price for x in (act1_hi if sd == 1 else act1_lo)[-6:]]
                    disp = perc.displacement_score(o5[i5 - 1], h5[i5 - 1], l5[i5 - 1], c5[i5 - 1], a5)
                    verdict = pros.cross_examine(
                        side=sd,
                        entry_px=ep,
                        risk_dist=rd,
                        thesis_scores={
                            "sweep": sw_w,
                            "disp": disp,
                            "vac": 0.72,
                            "ker4": float(sigmoid(k4, 0.25, 9.0)),
                            "rvol": float(sigmoid(rv5, 1.3, 2.0)),
                        },
                        thesis_weights={"sweep": 1.1, "disp": 1.2, "vac": 0.8, "ker4": 1.0, "rvol": 0.8},
                        opposing_htf_walls=opp,
                        ker_4h=k4,
                        body_ratio_4h=float(br4_arr[p4 - 1]),
                        dir_4h_candle=(1 if c4[p4 - 1] > o4[p4 - 1] else -1),
                        htf_trend_1h=tr1,
                        htf_trend_4h=tr4,
                        rvol_entry=rv5,
                        rvol_opp=1.0,
                        sweep_bars_accepted=0,
                        is_counter_trend_sweep=False,
                        min_clearance_r=min_clearance_r,
                    )
                    if not verdict.approved:
                        continue
                    pend_map[slv] = {
                        "sd": sd,
                        "ep": ep,
                        "sl": slp,
                        "rd": rd,
                        "exp": i5 + 8,
                        "meta": dict(verdict.reasoning_chain),
                    }
                    break

    closed_trades = sorted(closed_trades, key=lambda t: t["entry_time"])
    return closed_trades, _summarize_trades(closed_trades)


def run_v10_btc_frontloaded_backtest(
    df_5m: pd.DataFrame,
    eval_start: pd.Timestamp,
    eval_end: pd.Timestamp,
    *,
    asset: str = "BTCUSD",
    include_physics_45: bool = True,
    include_v6_4h: bool = True,
    include_topo_sweeps: bool = False,
    fee_mult: float = 1.0,
) -> Tuple[List[dict], Dict[str, object]]:
    """V10.0 BTCUSD_5m Front-Loaded Cashflow Portfolio (zero k=2/k=3 fractals).

    Combines:
      1) `V10_BTC_Physics` (CompVacuum + BPR/iFVG + AdversarialCrossExaminer + 45/40/15 @ 2.2R/4.5R/10R)
      2) `4H_V6_Cognitive` (VisualPerceptionEngine 4H topological swings + AdversarialCrossExaminer)
      3) Optional `V10_Topo_Sweeps` (`LON` + `1H_TOPO` + `15M_TOPO` + 45/40/15)
    """
    trades: List[dict] = []
    if include_physics_45:
        tr_phys, _ = run_v8_intraday_backtest(
            df_5m,
            eval_start,
            eval_end,
            include_smc_sweep=False,
            fee_mult=fee_mult,
            bank_r=2.2,
            bank_frac=0.45,
            be_lock_r=0.35,
            bank2_r=4.5,
            bank2_frac=0.40,
            be2_lock_r=2.0,
            runner_tp_r=10.0,
        )
        for _t in tr_phys:
            _t["asset"] = asset
            orig_s = str(_t.get("setup", "V8_CompVacuum"))
            new_s = orig_s.replace("V8_", "V10_")
            _t["setup"] = new_s
            _t["engine"] = new_s
            if _t.get("t1_hours") is not None and _t.get("t1_time") is None:
                _t["t1_time"] = _t["entry_time"] + pd.Timedelta(hours=float(_t["t1_hours"]))
            trades.append(_t)

    if include_v6_4h:
        tr_v6, _ = run_v6_cognitive_backtest(df_5m, eval_start, eval_end, fee_mult=fee_mult)
        for _t in tr_v6:
            _t["asset"] = asset
            _t.setdefault("setup", "4H_V6_Cognitive")
            _t.setdefault("engine", "4H_V6_Cognitive")
            if _t.get("t1_time") is None:
                _t["t1_time"] = _t["exit_time"]
            trades.append(_t)

    if include_topo_sweeps:
        tr_topo, _ = run_v10_btc_topo_sweeps_backtest(df_5m, eval_start, eval_end, asset=asset, fee_mult=fee_mult)
        trades.extend(tr_topo)

    trades = sorted(trades, key=lambda t: t["entry_time"])
    return trades, _summarize_trades(trades)


def run_v11_session_equilibrium_scalp(
    df_5m: pd.DataFrame,
    eval_start: pd.Timestamp,
    eval_end: pd.Timestamp,
    *,
    asset: str = "BTCUSD",
    min_prom_atr: float = 1.20,
    min_rvol_entry: float = 1.10,
    fee_mult: float = 1.0,
) -> Tuple[List[dict], Dict[str, object]]:
    """V11.0 High-WR Intraday Session Equilibrium Scalp Engine (50/35/15 @ 1.8R/3.2R/6.5R).

    Prunes noisy 15M_TOPO (PF 1.12) & unpruned LON (PF 1.24), retaining clean 1H Topological
    liquidity sweeps (`min_prom_atr=1.20`, `min_rvol_entry=1.10`) managed by
    `V11SessionEquilibriumExitManager` (50% @ +1.8R -> BE+0.25R, 35% @ +3.2R -> +1.25R, 15% @ +6.5R).
    """
    return run_v10_btc_topo_sweeps_backtest(
        df_5m,
        eval_start,
        eval_end,
        asset=asset,
        use_lon=False,
        use_1h_topo=True,
        use_15m_topo=False,
        min_prom_atr=min_prom_atr,
        min_rvol_entry=min_rvol_entry,
        fee_mult=fee_mult,
        exit_mgr_override=V11SessionEquilibriumExitManager(),
        setup_prefix="V11_SessEq",
    )


def run_v11_btc_portfolio(
    df_5m: pd.DataFrame,
    eval_start: pd.Timestamp,
    eval_end: pd.Timestamp,
    *,
    asset: str = "BTCUSD",
    include_smc_sweep: bool = True,
    include_v6_4h: bool = True,
    include_physics_45: bool = True,
    include_session_eq_1h: bool = True,
    include_v9_lon_pruned: bool = True,
    fee_mult: float = 1.0,
) -> Tuple[List[dict], Dict[str, object]]:
    """V11.0 BTCUSD_5m Institutional Exact-R Portfolio (Bug 2 & Bug 3 Fixed).

    Combines:
      1) `SMC_Sweep_V6` (Restored! 10R BE@3R->+1R + 1D Macro Filter, PF 2.40, 7/7 Green Years)
      2) `4H_V6_Cognitive` (VisualPerceptionEngine 4H topological swings + AdversarialCrossExaminer, PF 2.05)
      3) `V10_BTC_Physics` (CompVacuum + BPR_Snap + 45/40/15 @ 2.2R/4.5R/10R, PF 1.97)
      4) `V11_SessEq_1H_TOPO` (Pruned 1H Topological Sweep + 50/35/15 Session Eq Scalp, PF 1.88, WR 50.9%)
      5) Optional `V9_LON` pruned (`rvol >= 1.15`, PF 1.58)
    """
    trades: List[dict] = []

    if include_smc_sweep:
        tr_smc, _ = run_smc_sweep_causal_backtest(
            df_5m, eval_start, eval_end, use_v6_prosecutor=True, fee_mult=fee_mult, tp_r=10.0
        )
        for _t in tr_smc:
            _t["asset"] = asset
            _t["setup"] = "SMC_Sweep_V6"
            _t["engine"] = "SMC_Sweep_V6"
            _t["is_aplus"] = True
            if _t.get("t1_hours") is not None and _t.get("t1_time") is None:
                _t["t1_time"] = _t["entry_time"] + pd.Timedelta(hours=float(_t["t1_hours"]))
            elif _t.get("t1_time") is None:
                _t["t1_time"] = _t["exit_time"]
            trades.append(_t)

    if include_physics_45 or include_v6_4h:
        tr_v10_core, _ = run_v10_btc_frontloaded_backtest(
            df_5m,
            eval_start,
            eval_end,
            asset=asset,
            include_physics_45=include_physics_45,
            include_v6_4h=include_v6_4h,
            include_topo_sweeps=False,
            fee_mult=fee_mult,
        )
        trades.extend(tr_v10_core)

    if include_session_eq_1h:
        tr_eq, _ = run_v11_session_equilibrium_scalp(
            df_5m, eval_start, eval_end, asset=asset, fee_mult=fee_mult
        )
        trades.extend(tr_eq)

    if include_v9_lon_pruned:
        tr_lon, _ = run_v9_daily_session_backtest(
            df_5m,
            eval_start,
            eval_end,
            asset=asset,
            use_lon=True,
            use_1h_k2=False,
            use_15m_ny=False,
            include_v8_physics=False,
            include_v6_4h=False,
            fee_mult=fee_mult,
        )
        for _t in tr_lon:
            rv = float(_t.get("rvol_entry", _t.get("reasoning_chain", {}).get("rvol5", 0.0)) or 0.0)
            if rv < 1.15:
                continue
            _t["asset"] = asset
            _t["setup"] = "V9_LON"
            _t["engine"] = "V9_LON"
            _t["is_aplus"] = False
            if _t.get("t1_hours") is not None and _t.get("t1_time") is None:
                _t["t1_time"] = _t["entry_time"] + pd.Timedelta(hours=float(_t["t1_hours"]))
            trades.append(_t)

    trades = sorted(trades, key=lambda t: t["entry_time"])
    return trades, _summarize_trades(trades)


# ============================================================================
# SURGICAL MODULE 1: INSTITUTIONAL REFERENCE LEVELS & VALID SWEEP/RECLAIM ENGINE
# Grounded in Empirical Draw-on-Liquidity Research & Valid/Invalid Liquidity Reads
# ============================================================================

@dataclass
class ReferenceLevelSnapshot:
    pdh: float = np.nan
    pdl: float = np.nan
    pwh: float = np.nan
    pwl: float = np.nan
    asia_high: float = np.nan
    asia_low: float = np.nan
    london_high: float = np.nan
    london_low: float = np.nan
    pdh_touches: int = 0
    pdl_touches: int = 0
    pwh_touches: int = 0
    pwl_touches: int = 0


class InstitutionalReferenceAndSwingEngine:
    """
    Implements strict market physics from empirical research & schematic rules:
    1. Reference Levels (PDH/PDL, PWH/PWL, Session H/L) are NEVER used as blind
       standalone magnets. They act ONLY as:
       (a) Confluence Boosters when aligned with confirmed External/Internal Swings.
       (b) Brick-Wall Vetoes when an unmitigated (fresh, touches <= 2) level blocks
           the path to TP1 (+2.2R).
       (c) Touch Decay: Excessive touches (>= 3 without displacement) weaken a level.
    2. Internal vs External Swings & Valid vs Invalid Liquidity Reads:
       - Stepping candle wicks without a confirmed topological pivot != liquidity pool.
       - Wick through + close beyond level = Price Acceptance (Continuation), NOT Reversal.
       - Valid Reversal Read = Confirmed Swing/Pool + Wick Sweep + Body Reclaim back
         inside the level (within max_reclaim_bars=2) + subsequent BOS close.
    """

    @staticmethod
    def compute_causal_reference_levels(
        ts_ns: np.ndarray,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        atr: np.ndarray,
        idx: int,
    ) -> ReferenceLevelSnapshot:
        snap = ReferenceLevelSnapshot()
        if idx < 288:  # Need at least 1 full day of 5m bars (288 bars)
            return snap

        sample_ts = int(ts_ns[idx])
        if 10**14 <= sample_ts < 10**17:  # pandas >= 2.2 / 3.0 microsecond asi8
            ts_ns = ts_ns * 1_000
        elif 10**11 <= sample_ts < 10**14:  # millisecond timestamps
            ts_ns = ts_ns * 1_000_000
        elif sample_ts < 10**11:  # second timestamps
            ts_ns = ts_ns * 1_000_000_000

        sec = int(ts_ns[idx] // 1_000_000_000)
        cur_day = sec // 86400
        cur_day_start_ns = cur_day * 86400 * 1_000_000_000
        prev_day_start_ns = (cur_day - 1) * 86400 * 1_000_000_000

        # Scan backward causally (max 10 days = 2880 5m bars)
        start_scan = max(0, idx - 2880)
        ts_slice = ts_ns[start_scan : idx + 1]
        h_slice = highs[start_scan : idx + 1]
        l_slice = lows[start_scan : idx + 1]

        # 1. Fixed UTC Previous Day High / Low (PDH / PDL)
        pd_mask = (ts_slice >= prev_day_start_ns) & (ts_slice < cur_day_start_ns)
        if np.any(pd_mask):
            snap.pdh = float(np.max(h_slice[pd_mask]))
            snap.pdl = float(np.min(l_slice[pd_mask]))

        # 2. Fixed UTC Previous Week High / Low (PWH / PWL)
        # Unix epoch 1970-01-01 was Thursday (day 4); align to Monday 00:00 UTC
        cur_week = (cur_day + 3) // 7
        cur_week_start_day = cur_week * 7 - 3
        prev_week_start_day = (cur_week - 1) * 7 - 3
        cur_week_start_ns = cur_week_start_day * 86400 * 1_000_000_000
        prev_week_start_ns = prev_week_start_day * 86400 * 1_000_000_000

        pw_mask = (ts_slice >= prev_week_start_ns) & (ts_slice < cur_week_start_ns)
        if np.any(pw_mask):
            snap.pwh = float(np.max(h_slice[pw_mask]))
            snap.pwl = float(np.min(l_slice[pw_mask]))

        # 3. Current Day Completed Session Ranges (Asia: 00:00-07:00 UTC, London: 07:00-12:30 UTC)
        cur_Asia_end_ns = cur_day_start_ns + 7 * 3600 * 1_000_000_000
        cur_Lon_end_ns = cur_day_start_ns + int(12.5 * 3600) * 1_000_000_000

        if ts_ns[idx] >= cur_Asia_end_ns:
            asia_mask = (ts_slice >= cur_day_start_ns) & (ts_slice < cur_Asia_end_ns)
            if np.any(asia_mask):
                snap.asia_high = float(np.max(h_slice[asia_mask]))
                snap.asia_low = float(np.min(l_slice[asia_mask]))

        if ts_ns[idx] >= cur_Lon_end_ns:
            lon_mask = (ts_slice >= cur_Asia_end_ns) & (ts_slice < cur_Lon_end_ns)
            if np.any(lon_mask):
                snap.london_high = float(np.max(h_slice[lon_mask]))
                snap.london_low = float(np.min(l_slice[lon_mask]))

        # 4. Count today's touches on PDH/PDL to model level weakening (Touch Decay)
        today_mask = ts_slice >= cur_day_start_ns
        if np.any(today_mask):
            cur_atr = max(float(atr[idx]), float(closes[idx]) * 0.001)
            tol = 0.20 * cur_atr
            th = h_slice[today_mask]
            tl = l_slice[today_mask]
            if not np.isnan(snap.pdh):
                snap.pdh_touches = int(np.sum(th >= snap.pdh - tol))
            if not np.isnan(snap.pdl):
                snap.pdl_touches = int(np.sum(tl <= snap.pdl + tol))

        return snap

    @staticmethod
    def validate_sweep_and_reclaim(
        side: int,
        pool_level: float,
        is_confirmed_pivot_or_ref: bool,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        atr: np.ndarray,
        sweep_idx: int,
        current_idx: int,
        internal_bos_level: float,
    ) -> Tuple[bool, str, float]:
        """
        Enforces Schematic Image 2 ('INTERNAL LIQUIDITY: VALID vs INVALID READS'):
        - Rule C (WRONG): Stepping candle wicks without a confirmed pivot != pool.
        - Rule D (WRONG): Wick through + close outside level = Price Acceptance.
        - Rules A & B (VALID): Confirmed Swing/Ref Pool -> Wick Sweep -> Reclaim Close
          back inside pool_level (within 2 bars) -> Structure Break Close (BOS) beyond
          internal_bos_level.
        Returns: (is_valid, status_tag, quality_score)
        """
        if not is_confirmed_pivot_or_ref or np.isnan(pool_level) or np.isnan(internal_bos_level):
            return False, "REJECT_NOT_CONFIRMED_POOL", 0.0

        if current_idx < sweep_idx or (current_idx - sweep_idx) > 8:
            return False, "REJECT_STALE_SWEEP", 0.0

        cur_atr = max(float(atr[current_idx]), float(closes[current_idx]) * 0.001)

        if side == 1:  # BULLISH: Sweep below SSL (pool_level), Reclaim > pool_level, BOS > internal_bos_level
            sweep_low = float(lows[sweep_idx])
            if sweep_low >= pool_level:
                return False, "REJECT_NO_SSL_SWEEP", 0.0

            # Check if sweep candle or next candle reclaimed above pool_level
            reclaim_bar = -1
            for k in range(sweep_idx, min(current_idx + 1, sweep_idx + 2)):
                if float(closes[k]) > pool_level:
                    reclaim_bar = k
                    break

            if reclaim_bar == -1:
                # Rule D: Close below pool_level without immediate reclaim = Bearish Price Acceptance!
                return False, "REJECT_BEARISH_PRICE_ACCEPTANCE", 0.0

            # Ensure no subsequent bar closed back below sweep_low (invalidated sweep)
            if np.any(closes[reclaim_bar : current_idx + 1] < pool_level):
                return False, "REJECT_LOST_RECLAIM", 0.0

            # Require BOS close above internal swing high
            if float(closes[current_idx]) <= internal_bos_level:
                return False, "AWAITING_BOS_CLOSE", 0.0

            penetration_atr = (pool_level - sweep_low) / cur_atr
            # Optimal spring penetration is 0.10 to 1.25 ATR
            quality = float(np.exp(-0.5 * ((penetration_atr - 0.45) / 0.45) ** 2))
            return True, "VALID_BULLISH_SWEEP_RECLAIM_BOS", max(0.55, quality)

        else:  # BEARISH: Sweep above BSL (pool_level), Reclaim < pool_level, BOS < internal_bos_level
            sweep_high = float(highs[sweep_idx])
            if sweep_high <= pool_level:
                return False, "REJECT_NO_BSL_SWEEP", 0.0

            reclaim_bar = -1
            for k in range(sweep_idx, min(current_idx + 1, sweep_idx + 2)):
                if float(closes[k]) < pool_level:
                    reclaim_bar = k
                    break

            if reclaim_bar == -1:
                # Rule D: Close above pool_level without immediate reclaim = Bullish Price Acceptance!
                return False, "REJECT_BULLISH_PRICE_ACCEPTANCE", 0.0

            if np.any(closes[reclaim_bar : current_idx + 1] > pool_level):
                return False, "REJECT_LOST_RECLAIM", 0.0

            if float(closes[current_idx]) >= internal_bos_level:
                return False, "AWAITING_BOS_CLOSE", 0.0

            penetration_atr = (sweep_high - pool_level) / cur_atr
            quality = float(np.exp(-0.5 * ((penetration_atr - 0.45) / 0.45) ** 2))
            return True, "VALID_BEARISH_SWEEP_RECLAIM_BOS", max(0.55, quality)


# ============================================================================
# SURGICAL MODULE 2: DRAWDOWN-SAFE EXACT-1.0R SMALL ACCOUNT CASHFLOW MANAGER
# Eliminates the 58% MaxDD 'period_anchor=month' trap via Downward-Safe Anchoring
# ============================================================================

class DrawdownSafeExactRManager:
    """
    1. Exact-1.0R Fee-Inclusive Sizing:
       Notional = Risk_USD / (sl_pct + fee_rt_pct)
       -> Worst-case full stop-out is strictly -1.000R (never -1.25R or -1.65R).
    2. Minimum Structural Stop Clamp (min_sl_pct = 0.0040):
       -> Prevents microscopic noise stops where exchange fees eat >20% of R.
    3. Asymmetric Downward-Safe Equity Anchoring:
       anchor_equity = min(week_start_equity, active_equity)
       -> During a winning streak within a week, Risk_USD stays anchored to
          week_start_equity so a sudden reversal never gives back more dollars
          than earlier wins (+R = -$ paradox eliminated!).
       -> During a losing streak, anchor_equity immediately steps down with
          active_equity so percentage drawdown never snowballs (fixes V11's 58% DD!).
    4. High-Water-Mark 50/50 Vault Skimming:
       -> Skims 50% of net profits above HWM into an untouchable Vault.
    """

    def __init__(
        self,
        initial_equity: float = 100.0,
        base_risk_pct: float = 0.030,        # 3.0% standard risk
        aplus_risk_pct: float = 0.034,       # Tight 3.4% A+ risk (prevents size-skew inversions)
        dd_throttle_threshold: float = 0.12, # Smooth throttle starts at 12% DD
        dd_throttle_mult: float = 0.75,      # 0.75x risk when in >12% DD
        skim_step_usd: float = 25.0,
        skim_fraction: float = 0.50,
        max_leverage: float = 10.0,
        max_margin_fraction: float = 0.85,
        daily_loss_limit_r: float = -2.0,
    ):
        self.initial_equity = float(initial_equity)
        self.base_risk_pct = float(base_risk_pct)
        self.aplus_risk_pct = float(aplus_risk_pct)
        self.dd_throttle_threshold = float(dd_throttle_threshold)
        self.dd_throttle_mult = float(dd_throttle_mult)
        self.skim_step_usd = float(skim_step_usd)
        self.skim_fraction = float(skim_fraction)
        self.max_leverage = float(max_leverage)
        self.max_margin_fraction = float(max_margin_fraction)
        self.daily_loss_limit_r = float(daily_loss_limit_r)

    def resolve_risk_usd(
        self,
        active_equity: float,
        peak_active_equity: float,
        week_start_equity: float,
        is_aplus: bool = False,
    ) -> Tuple[float, float]:
        # Downward-safe anchor: never bet based on vanished equity!
        anchor_eq = min(float(week_start_equity), float(active_equity))
        pct = self.aplus_risk_pct if is_aplus else self.base_risk_pct

        # Smooth drawdown protection relative to peak active equity
        if peak_active_equity > 0:
            dd = max(0.0, (peak_active_equity - active_equity) / peak_active_equity)
            if dd >= self.dd_throttle_threshold:
                pct *= self.dd_throttle_mult

        risk_usd = anchor_eq * pct
        eff_pct = risk_usd / max(active_equity, 1e-9)
        return float(risk_usd), float(eff_pct)

    def compute_exact_1r_notional(
        self,
        risk_usd: float,
        active_equity: float,
        entry_price: float,
        stop_price: float,
        fee_rt_pct: float = 0.0010,
        free_margin_usd: Optional[float] = None,
    ) -> Tuple[float, float]:
        if entry_price <= 0:
            return 0.0, 0.0
        sl_pct = abs(entry_price - stop_price) / entry_price
        if sl_pct <= 1e-6:
            return 0.0, 0.0

        # Fee-inclusive denominator guarantees full stop-out <= -1.000R
        effective_stop_pct = sl_pct + max(0.0, float(fee_rt_pct))
        desired_notional = risk_usd / effective_stop_pct

        avail_margin = active_equity if free_margin_usd is None else min(active_equity, free_margin_usd)
        max_notional = max(0.0, avail_margin * self.max_margin_fraction * self.max_leverage)
        notional = min(desired_notional, max_notional)
        qty = notional / entry_price
        return float(notional), float(qty)

