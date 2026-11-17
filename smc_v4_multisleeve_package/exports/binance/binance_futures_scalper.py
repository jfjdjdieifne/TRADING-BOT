#!/usr/bin/env python3
"""
Binance USDT-M Futures Multi-Coin V7.0 Intraday Cashflow Sniper + 4H Cognitive
- Zero third-party dependencies (pure Python 3 stdlib).
- 3-Sleeve Causal Portfolio across the 10-Coin High-Liquidity Basket (zero HTF lookahead, real Binance VIP0 fees+slip+funding):
    1) V7 Intraday Scene-Graph Physics (--no-v7 to disable): V7_CompVacuum + V7_BPR_Snap/Retest
       - 5m Compression-Vacuum Snap & Sweep+BPR/iFVG on 1H Liquidity Pools + 4H KER>=0.15
       - Cashflow Exit: 35% Partial Bank @ +3.0R -> BE+0.50R Lock -> +10R Vacuum Runner
       - N=183, WR=33.9%, Net=+80.1R, PF=1.58, DD=17.3R | IS=+64.1R(1.87) | OOS=+16.0R(1.25)
    2) Secondary 1H->5m Engine (--no-smc to disable): SMC_Sweep_V6
       - Bayesian Prosecutor: Temporal Sweep Decay + KER4>=0.15 + HTF Freight-Train Veto
       - N=87, WR=36.8%, Net=+88.9R, PF=2.40, DD=9.0R, 7/7 yrs green | OOS PF=3.10
    3) Primary 4H Engine (--no-4h-trend to disable): 4H_V6_Cognitive
       - Fractal 1H/4H Structural Stop Compression + 2-Stage Risk-Free Pyramiding + Climax Ratchet
       - N=240, WR=40.8%, Net=+109.1R, PF=2.05, DD=8.2R, 7/7 yrs green | OOS PF=1.94
    Combined 3-Sleeve BTC Single-Asset: N=510, WR=37.6%, Net=+278.1R, PF=1.91, DD=18.7R, 7/7 yrs green
- Small-Account Cashflow Engine (--small-account): $100+ equity, 2.5%-3.0% risk, <=15x leverage, -2.5R daily circuit breaker.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import hmac
import json
import math
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from typing import Dict, List, Optional, Tuple


DEFAULT_SYMBOLS = (
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
    "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "LINKUSDT", "SUIUSDT",
)

LIVE_BASE = "https://fapi.binance.com"
TESTNET_BASE = "https://testnet.binancefuture.com"

Bar = Tuple[int, float, float, float, float, float]


# -------------------- Pure Causal V6/V7 Topological, Kernel, Scene-Graph Physics & Prosecutor Math --------------------

def sigmoid(x: float, x0: float = 0.0, k: float = 1.0) -> float:
    z = max(-60.0, min(60.0, -k * (x - x0)))
    return 1.0 / (1.0 + math.exp(z))


def _ker_slice(closes: List[float]) -> float:
    if len(closes) < 3:
        return 0.0
    den = sum(abs(closes[i] - closes[i - 1]) for i in range(1, len(closes)))
    return abs(closes[-1] - closes[0]) / den if den > 1e-12 else 0.0


def detect_v7_comp_vacuum(
    bars_5m: List[Bar],
    atr5: float,
    barriers_hi: List[float],
    barriers_lo: List[float],
    trend_4h: int,
    max_approach_ker: float = 0.42,
    min_implied_r: float = 3.0,
) -> Optional[Tuple[int, float, float]]:
    """V7 Setup A: Compression grind into 1H liquidity barrier + sweep & 4H-aligned snap."""
    if atr5 <= 0 or len(bars_5m) < 30 or trend_4h == 0:
        return None
    _, o0, h0, l0, c0, _ = bars_5m[-1]
    rng0 = h0 - l0
    body0 = abs(c0 - o0)
    if rng0 <= 0 or body0 < 0.45 * rng0 or rng0 < 0.90 * atr5:
        return None
    win = bars_5m[-30:]
    win_h = [b[2] for b in win]
    win_l = [b[3] for b in win]
    win_c = [b[4] for b in win]

    if trend_4h == 1 and c0 > o0 and barriers_lo:
        if (body0 / atr5) < 1.05:
            return None
        origin_idx = max(range(len(win_h) - 5), key=lambda k: win_h[k])
        origin_px = win_h[origin_idx]
        mid_pt = min(len(win_l) - 3, max(origin_idx + 1, len(win_l) - 6))
        app_c = win_c[origin_idx:mid_pt + 1]
        if len(app_c) >= 4 and _ker_slice(app_c) <= max_approach_ker:
            seg_l = win_l[mid_pt:-1]
            sweep_low = min(l0, min(seg_l) if seg_l else l0)
            sl_dist = abs(c0 - (sweep_low - atr5))
            if sl_dist > 0 and (origin_px - c0) / sl_dist >= min_implied_r:
                for lv in barriers_lo:
                    if sweep_low < lv and c0 > lv and (lv - sweep_low) <= 2.2 * atr5:
                        return (1, sweep_low, origin_px)

    if trend_4h == -1 and c0 < o0 and barriers_hi:
        if (body0 / atr5) < 1.05:
            return None
        origin_idx = min(range(len(win_l) - 5), key=lambda k: win_l[k])
        origin_px = win_l[origin_idx]
        mid_pt = min(len(win_h) - 3, max(origin_idx + 1, len(win_h) - 6))
        app_c = win_c[origin_idx:mid_pt + 1]
        if len(app_c) >= 4 and _ker_slice(app_c) <= max_approach_ker:
            seg_h = win_h[mid_pt:-1]
            sweep_high = max(h0, max(seg_h) if seg_h else h0)
            sl_dist = abs((sweep_high + atr5) - c0)
            if sl_dist > 0 and (c0 - origin_px) / sl_dist >= min_implied_r:
                for lv in barriers_hi:
                    if sweep_high > lv and c0 < lv and (sweep_high - lv) <= 2.2 * atr5:
                        return (-1, sweep_high, origin_px)
    return None


def _bpr_at_bar(
    bars: List[Bar],
    idx: int,
    atr5: float,
    barriers_hi: List[float],
    barriers_lo: List[float],
    trend_4h: int,
    trend_1h: int,
    min_bpr_k: float = 1.20,
) -> Optional[dict]:
    if atr5 <= 0 or idx < 15 or trend_4h == 0 or trend_4h != trend_1h:
        return None
    _, _, h2, l2, _, _ = bars[idx - 2]
    _, o_d, _, _, c_d, _ = bars[idx - 1]
    _, _, h0, l0, c0, _ = bars[idx]
    disp_body = abs(c_d - o_d)
    k_vel = disp_body / atr5
    if k_vel < min_bpr_k:
        return None
    sub = bars[max(0, idx - 11):idx + 1]
    sub_h = [b[2] for b in sub]
    sub_l = [b[3] for b in sub]

    if trend_4h == 1 and c_d > o_d and c0 > h2 and (l0 - h2) >= 0.12 * atr5 and barriers_lo:
        d_lo, d_hi = h2, l0
        sweep_low = min(sub_l)
        if any(sweep_low < lv and c_d > lv and (lv - sweep_low) <= 2.5 * atr5 for lv in barriers_lo):
            for m in range(max(1, idx - 9), idx - 2):
                if bars[m - 1][3] - bars[m + 1][2] >= 0.10 * atr5 and bars[m][4] < bars[m][1]:
                    ov_lo = max(d_lo, bars[m + 1][2])
                    ov_hi = min(d_hi, bars[m - 1][3])
                    if ov_hi > ov_lo:
                        vac = min(1.0, (k_vel - 1.0) * 0.45 + 0.35)
                        return {"side": 1, "low": ov_lo, "high": ov_hi, "mid": 0.5 * (ov_lo + ov_hi), "sweep": sweep_low, "k": k_vel, "vac": vac}
    if trend_4h == -1 and c_d < o_d and c0 < l2 and (l2 - h0) >= 0.12 * atr5 and barriers_hi:
        d_lo, d_hi = h0, l2
        sweep_high = max(sub_h)
        if any(sweep_high > lv and c_d < lv and (sweep_high - lv) <= 2.5 * atr5 for lv in barriers_hi):
            for m in range(max(1, idx - 9), idx - 2):
                if bars[m + 1][3] - bars[m - 1][2] >= 0.10 * atr5 and bars[m][4] > bars[m][1]:
                    ov_lo = max(d_lo, bars[m - 1][2])
                    ov_hi = min(d_hi, bars[m + 1][3])
                    if ov_hi > ov_lo:
                        vac = min(1.0, (k_vel - 1.0) * 0.45 + 0.35)
                        return {"side": -1, "low": ov_lo, "high": ov_hi, "mid": 0.5 * (ov_lo + ov_hi), "sweep": sweep_high, "k": k_vel, "vac": vac}
    return None


def detect_v7_bpr_signal(
    bars_5m: List[Bar],
    atr5: float,
    barriers_hi: List[float],
    barriers_lo: List[float],
    trend_4h: int,
    trend_1h: int,
) -> Optional[Tuple[str, int, float]]:
    """Stateless causal check at bars_5m[-1]: immediate high-velocity BPR snap OR 6-bar causal retest."""
    n = len(bars_5m)
    bpr_now = _bpr_at_bar(bars_5m, n - 1, atr5, barriers_hi, barriers_lo, trend_4h, trend_1h)
    if bpr_now is not None and bpr_now["vac"] >= 0.55 and bpr_now["k"] >= 1.60:
        slp = (bpr_now["sweep"] - atr5) if bpr_now["side"] == 1 else (bpr_now["sweep"] + atr5)
        return ("V7_BPR_Snap", bpr_now["side"], slp)

    _, o, h, l, c, _ = bars_5m[-1]
    for back in range(1, min(7, n - 16)):
        c_idx = (n - 1) - back
        bpr = _bpr_at_bar(bars_5m, c_idx, atr5, barriers_hi, barriers_lo, trend_4h, trend_1h)
        if bpr is None or (bpr["vac"] >= 0.55 and bpr["k"] >= 1.60):
            continue
        intervening = bars_5m[c_idx + 1:n - 1]
        if bpr["side"] == 1:
            if any(b[3] < bpr["sweep"] for b in intervening) or l < bpr["sweep"]:
                continue
            if l <= bpr["high"] and c > o and c >= bpr["mid"]:
                return ("V7_BPR_Retest", 1, bpr["sweep"] - atr5)
        else:
            if any(b[2] > bpr["sweep"] for b in intervening) or h > bpr["sweep"]:
                continue
            if h >= bpr["low"] and c < o and c <= bpr["mid"]:
                return ("V7_BPR_Retest", -1, bpr["sweep"] + atr5)
    return None


def soft_and_log_odds(
    scores: Dict[str, float],
    weights: Dict[str, float],
    veto_floors: Optional[Dict[str, float]] = None,
) -> float:
    eps = 1e-4
    if veto_floors:
        for k_v, fl in veto_floors.items():
            if k_v in scores and scores[k_v] < fl:
                return max(0.0, scores[k_v] / max(fl, eps)) * 0.15
    num = den = 0.0
    for k_w, w in weights.items():
        if w <= 0 or k_w not in scores:
            continue
        p = max(eps, min(1.0 - eps, scores[k_w]))
        num += w * math.log(p / (1.0 - p))
        den += w
    return sigmoid(num / den, 0.0, 1.0) if den > 0 else 0.0


def prosecutor_cross_examine(
    side: int,
    thesis_scores: Dict[str, float],
    thesis_weights: Dict[str, float],
    ker_4h: float,
    body_ratio_4h: float,
    dir_4h_candle: int,
    htf_trend_1h: int,
    htf_trend_4h: int,
    rvol_entry: float,
    sweep_bars_accepted: int = 0,
    is_counter_trend_sweep: bool = False,
    min_conviction: float = 0.35,
) -> Tuple[bool, float]:
    """V6 Bayesian Prosecutor: Temporal Sweep Decay + HTF Freight-Train Veto + Volume Divergence."""
    if sweep_bars_accepted > 1:
        return False, 0.0
    if is_counter_trend_sweep and ker_4h > 0.45 and ((dir_4h_candle == -side and body_ratio_4h >= 0.55) or htf_trend_4h == -side):
        return False, 0.0
    eps = 1e-4
    num = den = 0.0
    for k_w, w in thesis_weights.items():
        if w <= 0 or k_w not in thesis_scores:
            continue
        p = max(eps, min(1.0 - eps, thesis_scores[k_w]))
        num += w * math.log(p / (1.0 - p))
        den += w
    l_thesis = (num / den) if den > 0 else 0.0
    freight_pen = 0.65 if (is_counter_trend_sweep and htf_trend_4h == -side and ker_4h > 0.35) else 0.0
    vdiv_pen = 0.25 if rvol_entry < 0.85 else 0.0
    p_contra = freight_pen + 0.55 * vdiv_pen
    conv = sigmoid(2.4 * l_thesis - 2.6 * p_contra - 0.35, 0.0, 1.0)
    return (conv >= min_conviction), conv


class CausalSwingTracker:
    def __init__(self, k: int = 2, max_active: int = 25) -> None:
        self.k = k
        self.max_active = max_active
        self.win: deque = deque(maxlen=2 * k + 1)
        self.bar_idx = -1
        self.last_high: Optional[float] = None
        self.last_low: Optional[float] = None
        self.trend = 0
        self.act_hi: List[Tuple[int, float]] = []
        self.act_lo: List[Tuple[int, float]] = []

    def update(self, h: float, l: float, c: float) -> None:
        self.bar_idx += 1
        self.win.append((h, l))
        if len(self.win) == 2 * self.k + 1:
            m = self.k
            ch, cl = self.win[m]
            if all(ch >= self.win[i][0] for i in range(len(self.win)) if i != m) and any(
                ch > self.win[i][0] for i in range(len(self.win)) if i != m
            ):
                self.last_high = ch
                self.act_hi.append((self.bar_idx - self.k, ch))
                self.act_hi = self.act_hi[-self.max_active:]
            if all(cl <= self.win[i][1] for i in range(len(self.win)) if i != m) and any(
                cl < self.win[i][1] for i in range(len(self.win)) if i != m
            ):
                self.last_low = cl
                self.act_lo.append((self.bar_idx - self.k, cl))
                self.act_lo = self.act_lo[-self.max_active:]
        self.act_hi = [x for x in self.act_hi if h <= x[1]]
        self.act_lo = [x for x in self.act_lo if l >= x[1]]
        if self.last_high is not None and c > self.last_high:
            self.trend = 1
        elif self.last_low is not None and c < self.last_low:
            self.trend = -1


def compute_topological_swings(bars: List[Bar], atr_series: List[float], atr_mult: float = 1.25) -> Tuple[Optional[float], Optional[float], int]:
    if len(bars) < 5 or len(atr_series) != len(bars):
        return None, None, 0
    direction = 0
    piv_hi, piv_lo = bars[0][2], bars[0][3]
    last_hi = last_lo = prev_hi = prev_lo = None
    for i in range(1, len(bars)):
        h, l = bars[i][2], bars[i][3]
        th = atr_mult * max(atr_series[i], 1e-12)
        if direction == 0:
            if h - piv_lo >= th:
                prev_lo, last_lo = last_lo, piv_lo
                direction, piv_hi = 1, h
            elif piv_hi - l >= th:
                prev_hi, last_hi = last_hi, piv_hi
                direction, piv_lo = -1, l
            else:
                piv_hi, piv_lo = max(piv_hi, h), min(piv_lo, l)
        elif direction == 1:
            if h >= piv_hi:
                piv_hi = h
            elif piv_hi - l >= th:
                prev_hi, last_hi = last_hi, piv_hi
                direction, piv_lo = -1, l
        else:
            if l <= piv_lo:
                piv_lo = l
            elif h - piv_lo >= th:
                prev_lo, last_lo = last_lo, piv_lo
                direction, piv_hi = 1, h
    tr = 0
    if last_hi is not None and prev_hi is not None and last_lo is not None and prev_lo is not None:
        if last_hi > prev_hi and last_lo > prev_lo:
            tr = 1
        elif last_hi < prev_hi and last_lo < prev_lo:
            tr = -1
    return last_hi, last_lo, tr


def compute_ema_series(closes: List[float], span: int) -> List[float]:
    k = 2.0 / (span + 1.0)
    out: List[float] = []
    for c in closes:
        out.append(c if not out else (c * k + out[-1] * (1.0 - k)))
    return out


def compute_wilder_atr_series(bars: List[Bar], period: int = 14) -> List[float]:
    out: List[float] = []
    val = 0.0
    prev_c: Optional[float] = None
    alpha = 1.0 / period
    for i, (_, _, h, l, c, _) in enumerate(bars):
        tr = (h - l) if prev_c is None else max(h - l, abs(h - prev_c), abs(l - prev_c))
        prev_c = c
        val = tr if i == 0 else ((1.0 - alpha) * val + alpha * tr)
        out.append(val)
    return out


def compute_wilder_atr(bars: List[Bar], period: int = 14) -> float:
    ser = compute_wilder_atr_series(bars, period)
    return ser[-1] if ser else 0.0


def compute_wilder_adx(bars: List[Bar], period: int = 14) -> float:
    if len(bars) < 2:
        return 0.0
    alpha = 1.0 / period
    prev_h, prev_l, prev_c = bars[0][2], bars[0][3], bars[0][4]
    atr = max(prev_h - prev_l, 1e-12)
    pdm = mdm = adx = 0.0
    dx_init = False
    for _, _, h, l, c, _ in bars[1:]:
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        up, dn = h - prev_h, prev_l - l
        p = up if (up > dn and up > 0) else 0.0
        m = dn if (dn > up and dn > 0) else 0.0
        prev_h, prev_l, prev_c = h, l, c
        atr = (1.0 - alpha) * atr + alpha * tr
        pdm = (1.0 - alpha) * pdm + alpha * p
        mdm = (1.0 - alpha) * mdm + alpha * m
        if atr <= 1e-12:
            continue
        pdi = 100.0 * pdm / atr
        mdi = 100.0 * mdm / atr
        den = pdi + mdi
        dx = (100.0 * abs(pdi - mdi) / den) if den > 1e-12 else 0.0
        adx = dx if not dx_init else ((1.0 - alpha) * adx + alpha * dx)
        dx_init = True
    return adx


def compute_wilder_rsi(closes: List[float], period: int = 14) -> float:
    if len(closes) < 2:
        return 50.0
    gains: List[float] = []
    losses: List[float] = []
    ag = al = 0.0
    for i in range(1, len(closes)):
        d = closes[i] - closes[i - 1]
        g, l = (d, 0.0) if d > 0 else (0.0, -d)
        if len(gains) < period:
            gains.append(g)
            losses.append(l)
            ag = sum(gains) / len(gains)
            al = sum(losses) / len(losses)
        else:
            ag = (ag * (period - 1) + g) / period
            al = (al * (period - 1) + l) / period
    return 100.0 if al <= 1e-12 else (100.0 - 100.0 / (1.0 + ag / al))


def compute_macd_hist(closes: List[float]) -> float:
    e12 = compute_ema_series(closes, 12)
    e26 = compute_ema_series(closes, 26)
    macd = [a - b for a, b in zip(e12, e26)]
    sig = compute_ema_series(macd, 9)
    return macd[-1] - sig[-1]


def compute_ker(closes: List[float], period: int = 20) -> float:
    if len(closes) <= period:
        return 0.0
    arr = closes[-(period + 1):]
    den = sum(abs(arr[i] - arr[i - 1]) for i in range(1, len(arr)))
    return abs(arr[-1] - arr[0]) / den if den > 1e-12 else 0.0


def compute_er14(closes: List[float]) -> float:
    return compute_ker(closes, period=14)


def compute_4h_v6_confluence(
    bars_4h: List[Bar],
    atr_ser: List[float],
    adx4: float,
    btc_regime_score: float = 1.0,
) -> Tuple[float, float, float, float, int]:
    """Return (confluence, trap_score, ker_4h, body_ratio_4h, dir_4h)."""
    ts_ms, o, h, l, c, vol = bars_4h[-1]
    a4 = max(atr_ser[-1], 1e-12)
    closes = [b[4] for b in bars_4h]
    ker = compute_ker(closes, 20)
    hi_r = max(b[2] for b in bars_4h[-20:])
    lo_r = min(b[3] for b in bars_4h[-20:])
    rpos = (c - lo_r) / max(hi_r - lo_r, 1e-12)
    in_mid_chop = (ker < 0.25) and (0.25 <= rpos <= 0.75)
    ker_sc = 0.05 if in_mid_chop else sigmoid(ker, 0.25, 9.0)

    sq_vals: List[float] = []
    for k in range(max(20, len(bars_4h) - 6), len(bars_4h) + 1):
        sub = closes[k - 20:k]
        mu = sum(sub) / 20.0
        sd = math.sqrt(sum((x - mu) ** 2 for x in sub) / 20.0)
        sq_vals.append((4.0 * sd) / max(3.0 * atr_ser[k - 1], 1e-12))
    sq_now = sq_vals[-1]
    sq_min = min(sq_vals[:-1]) if len(sq_vals) > 1 else 1.0
    prior_comp = sq_min < 0.98
    sq_exp = sigmoid(sq_now - sq_min, 0.04, 18.0) if prior_comp else 0.45
    sq_sc = max(0.0, min(1.0, 0.55 * sigmoid(1.05 - sq_min, 0.05, 12.0) + 0.45 * sq_exp))

    cur_hr = dt.datetime.fromtimestamp(ts_ms / 1000.0, tz=dt.timezone.utc).hour
    same_slot = [b[5] for b in bars_4h[:-1] if dt.datetime.fromtimestamp(b[0] / 1000.0, tz=dt.timezone.utc).hour == cur_hr][-20:]
    pool_v = same_slot if len(same_slot) >= 5 else [b[5] for b in bars_4h[:-1][-40:]]
    if pool_v:
        sp = sorted(pool_v)
        med_v = sp[len(sp) // 2]
        rvol = (vol / med_v) if med_v > 0 else 1.0
    else:
        rvol = 1.0
    rvol_sc = sigmoid(rvol, 1.6, 2.2)
    br = abs(c - o) / max(h - l, 1e-12)
    er_sc = min(1.0, rvol_sc * sigmoid(br, 0.65, 9.0) + (0.25 if (rvol >= 1.4 and br >= 0.65) else 0.0))
    trap_sc = sigmoid(rvol, 1.8, 3.0) * sigmoid(0.42 - br, 0.0, 10.0)

    disp_sc = min(1.0, 0.60 * sigmoid(abs(c - o) / a4, 1.2, 2.2) + 0.40 * sigmoid(br, 0.60, 7.0))
    adx_sc = sigmoid(adx4, 18.0, 0.25)

    conf = soft_and_log_odds(
        {"ker": ker_sc, "er": er_sc, "sq": sq_sc, "disp": disp_sc, "adx": adx_sc, "btc": btc_regime_score},
        {"ker": 1.0, "er": 1.0, "sq": 0.6, "disp": 1.0, "adx": 1.2, "btc": 1.1},
        veto_floors={"ker": 0.12, "btc": 0.20},
    )
    return conf, trap_sc, ker, br, (1 if c > o else -1)


def fractal_stop_compression_4h(
    ep: float,
    side: int,
    atr_4h: float,
    bars_1h: List[Bar],
) -> float:
    """Scale-free volatility-normalized stop selection bounded in [1.50, 2.00] * ATR_4H."""
    a4 = max(atr_4h, 1e-12)
    a1 = max(compute_wilder_atr(bars_1h, 14), 1e-12)
    buf = 0.20 * a1
    anchors: List[float] = []
    if len(bars_1h) >= 12:
        anchors.append(min(b[3] for b in bars_1h[-12:]) if side == 1 else max(b[2] for b in bars_1h[-12:]))
    sw1 = CausalSwingTracker(2)
    for _, _, hh, hl, hc, _ in bars_1h:
        sw1.update(hh, hl, hc)
    if side == 1 and sw1.last_low is not None:
        anchors.append(sw1.last_low)
    elif side == -1 and sw1.last_high is not None:
        anchors.append(sw1.last_high)

    best_rho, best_sc = 2.0, -1e9
    for anc in anchors:
        sl_c = (anc - buf) if side == 1 else (anc + buf)
        d = (ep - sl_c) if side == 1 else (sl_c - ep)
        if d <= 0:
            continue
        rho = d / a4
        if 1.50 <= rho <= 2.00:
            sc = 2.0 - abs(rho - 1.68)
            if sc > best_sc:
                best_sc, best_rho = sc, rho
    return ep - side * best_rho * a4


def compute_daily_utc_vwap(bars_5m: List[Bar]) -> Optional[float]:
    if not bars_5m:
        return None
    latest_day = dt.datetime.fromtimestamp(bars_5m[-1][0] / 1000.0, tz=dt.timezone.utc).date()
    pv = vv = 0.0
    for ts_ms, _, h, l, c, v in bars_5m:
        if dt.datetime.fromtimestamp(ts_ms / 1000.0, tz=dt.timezone.utc).date() == latest_day:
            pv += ((h + l + c) / 3.0) * v
            vv += v
    return (pv / vv) if vv > 0 else None


@dataclasses.dataclass
class SignalCandidate:
    symbol: str
    engine: str
    side: int
    entry_px: float
    sl_px: float
    tp_px: Optional[float]
    risk_dist: float
    step_locks: Tuple[Tuple[float, float], ...]
    expire_sec: int
    is_market: bool = False
    trail_atr_mult: Optional[float] = None
    risk_mult: float = 1.0
    bank_r: float = 0.0
    bank_frac: float = 0.0
    be_lock_r: float = 0.50


def evaluate_symbol_bars(
    symbol: str,
    bars_5m: List[Bar],
    bars_15m: List[Bar],
    bars_1h: List[Bar],
    bars_4h: List[Bar],
    bars_1d: Optional[List[Bar]] = None,
    use_v7: bool = True,
    v7_risk_mult: float = 1.0,
    use_4h_trend: bool = True,
    v6_mode: str = "hybrid",
    donch_lb: int = 20,
    trail_atr_mult: float = 3.5,
    conf_threshold: Optional[float] = None,
    btc_regime_fn=None,
    use_smc: bool = True,
    smc_risk_mult: float = 0.50,
    sweep_tp_r: float = 10.0,
    enable_fast_scalp: bool = False,
) -> Optional[SignalCandidate]:
    """Evaluate strictly CLOSED candles using 100% causal V7.0 Intraday Physics + V6.0 Cognitive + Prosecutor rules."""
    if len(bars_5m) < 80 or len(bars_15m) < 40 or len(bars_1h) < 60 or len(bars_4h) < max(60, donch_lb + 3):
        return None

    c4 = [b[4] for b in bars_4h]
    atr_ser4 = compute_wilder_atr_series(bars_4h, 14)
    atr_4h = atr_ser4[-1]
    adx_4h = compute_wilder_adx(bars_4h, 14)
    btc_sc_1 = btc_regime_fn(1) if btc_regime_fn is not None else 1.0
    conf_0, trap_sc, ker_4h, br_4h, dir_4h = compute_4h_v6_confluence(bars_4h, atr_ser4, adx_4h, btc_sc_1)

    d1_tr = 0
    if bars_1d and len(bars_1d) >= 50:
        c1d = [b[4] for b in bars_1d]
        e20_1d = compute_ema_series(c1d, 20)[-1]
        e50_1d = compute_ema_series(c1d, 50)[-1]
        d1_tr = 1 if e20_1d > e50_1d else -1

    # 1) Primary 4H Engine: 4H_V6_Cognitive (N=239, WR=40.6%, Net=+112.4R, PF=2.05, DD=9.4R)
    if use_4h_trend and d1_tr != 0 and atr_4h > 0:
        c_now, c_prev = c4[-1], c4[-2]
        side = 0
        if v6_mode == "topological":
            top_hi, top_lo, _ = compute_topological_swings(bars_4h[:-1], atr_ser4[:-1], 1.25)
            if d1_tr == 1 and top_hi is not None and c_now > top_hi and c_prev <= top_hi:
                side = 1
            elif d1_tr == -1 and top_lo is not None and c_now < top_lo and c_prev >= top_lo:
                side = -1
        else:
            if adx_4h >= 20.0:
                hi_cur = max(b[2] for b in bars_4h[-(donch_lb + 1):-1])
                lo_cur = min(b[3] for b in bars_4h[-(donch_lb + 1):-1])
                hi_prev = max(b[2] for b in bars_4h[-(donch_lb + 2):-2])
                lo_prev = min(b[3] for b in bars_4h[-(donch_lb + 2):-2])
                if d1_tr == 1 and c_now > hi_cur and c_prev <= hi_prev:
                    side = 1
                elif d1_tr == -1 and c_now < lo_cur and c_prev >= lo_prev:
                    side = -1

        if side != 0:
            btc_sc = btc_regime_fn(side) if btc_regime_fn is not None else 1.0
            conf, trap_sc, _, _, _ = compute_4h_v6_confluence(bars_4h, atr_ser4, adx_4h, btc_sc)
            thr = conf_threshold if conf_threshold is not None else (0.50 if v6_mode == "hybrid" else 0.55)
            if conf >= thr and trap_sc < 0.78:
                slp = fractal_stop_compression_4h(c_now, side, atr_4h, bars_1h)
                rd = abs(c_now - slp)
                if 0.005 <= (rd / c_now) <= 0.085:
                    return SignalCandidate(
                        symbol, "4H_V6_Cognitive", side, c_now, slp, None, rd,
                        (), 300, is_market=True, trail_atr_mult=trail_atr_mult, risk_mult=1.0,
                    )

    c1 = [b[4] for b in bars_1h]
    c15 = [b[4] for b in bars_15m]
    c5 = [b[4] for b in bars_5m]
    e20_4h, e50_4h = compute_ema_series(c4, 20)[-1], compute_ema_series(c4, 50)[-1]
    e20_1h, e50_1h = compute_ema_series(c1, 20)[-1], compute_ema_series(c1, 50)[-1]
    tr_up = e20_4h > e50_4h and e20_1h > e50_1h
    tr_dn = e20_4h < e50_4h and e20_1h < e50_1h
    er_4h, er_1h, er_15 = compute_er14(c4), compute_er14(c1), compute_er14(c15)
    rsi_1h = compute_wilder_rsi(c1, 14)

    e9_5, e20_5, e50_5 = compute_ema_series(c5, 9)[-1], compute_ema_series(c5, 20)[-1], compute_ema_series(c5, 50)[-1]
    macd_hist = compute_macd_hist(c5)
    atr_15, atr_5 = compute_wilder_atr(bars_15m, 14), compute_wilder_atr(bars_5m, 14)
    atr_1h = compute_wilder_atr(bars_1h, 14)
    rsi_5 = compute_wilder_rsi(c5, 14)
    vwap = compute_daily_utc_vwap(bars_5m)

    vols_20 = [b[5] for b in bars_5m[-20:]]
    vavg_20 = sum(vols_20) / len(vols_20) if vols_20 else 0.0
    v_last = bars_5m[-1][5]

    sw4, sw1, sw1_k3, sw5 = CausalSwingTracker(2), CausalSwingTracker(2), CausalSwingTracker(3), CausalSwingTracker(2)
    for _, _, h, l, c, _ in bars_4h:
        sw4.update(h, l, c)
    cands_k3 = []
    start_scan = max(0, len(bars_1h) - 5)
    for b_idx, (ts_1h, ho, hh, hl, hc, _) in enumerate(bars_1h):
        upd = []
        for sd, sw_t, sl_b, b_acc, sw_sc in cands_k3:
            if (sd == 1 and hc < sl_b) or (sd == -1 and hc > sl_b):
                b_acc += 1
            upd.append((sd, sw_t, sl_b, b_acc, sw_sc))
        cands_k3 = upd
        if b_idx >= start_scan:
            for idx_s, p_lo in list(sw1_k3.act_lo):
                if (sw1_k3.bar_idx + 1 - idx_s) >= 4 and hl < p_lo and hc > p_lo:
                    sc = sigmoid((min(ho, hc) - hl) / max(atr_1h, 1e-12), 0.45, 3.5)
                    cands_k3.append((1, ts_1h, hl, 0, sc))
            for idx_s, p_hi in list(sw1_k3.act_hi):
                if (sw1_k3.bar_idx + 1 - idx_s) >= 4 and hh > p_hi and hc < p_hi:
                    sc = sigmoid((hh - max(ho, hc)) / max(atr_1h, 1e-12), 0.45, 3.5)
                    cands_k3.append((-1, ts_1h, hh, 0, sc))
        sw1.update(hh, hl, hc)
        sw1_k3.update(hh, hl, hc)

    for _, _, h, l, c, _ in bars_5m[:-1]:
        sw5.update(h, l, c)

    ts_5m, o, h, l, c, _ = bars_5m[-1]
    _, o2, _, _, c2, _ = bars_5m[-2]
    _, _, h1, l1, _, _ = bars_5m[-3]
    utc_dt = dt.datetime.fromtimestamp(ts_5m / 1000.0, tz=dt.timezone.utc)

    # 2) V7.0 Intraday Scene-Graph Physics (5m Compression-Vacuum Snap + Sweep BPR/iFVG)
    if use_v7 and atr_5 > 0 and ker_4h >= 0.15:
        b_hi = [x[1] for x in sw1.act_hi[-8:]]
        b_lo = [x[1] for x in sw1.act_lo[-8:]]
        v7_sig: Optional[Tuple[str, int, float]] = None
        ca = detect_v7_comp_vacuum(bars_5m, atr_5, b_hi, b_lo, sw4.trend)
        if ca is not None:
            sd_v7, sw_ex, _ = ca
            slp_v7 = (sw_ex - atr_5) if sd_v7 == 1 else (sw_ex + atr_5)
            v7_sig = ("V7_CompVacuum", sd_v7, slp_v7)
        if v7_sig is None:
            v7_sig = detect_v7_bpr_signal(bars_5m, atr_5, b_hi, b_lo, sw4.trend, sw1.trend)
        if v7_sig is not None:
            eng_v7, sd_v7, slp_v7 = v7_sig
            rd_v7 = abs(c - slp_v7)
            if 0.0045 <= (rd_v7 / c) <= 0.0180:
                return SignalCandidate(
                    symbol, eng_v7, sd_v7, c, slp_v7, c + sd_v7 * sweep_tp_r * rd_v7,
                    rd_v7, (), 40 * 60, is_market=False, risk_mult=v7_risk_mult,
                    bank_r=3.0, bank_frac=0.35, be_lock_r=0.50,
                )

    # 3) Secondary 1H->5m Engine: SMC_Sweep_V6 (PF=2.40, OOS PF=3.10, DD=9.0R, 7/7 yrs green)
    if use_smc and utc_dt.hour >= 9 and atr_5 > 0 and cands_k3 and ker_4h >= 0.15:
        c2b = abs(c2 - o2)
        rvol5 = (v_last / vavg_20) if vavg_20 > 0 else 1.0
        for side, sw_ts, sl_base, b_acc, sw_sc in reversed(cands_k3):
            if (ts_5m - sw_ts) > 5 * 3600 * 1000:
                continue
            slp = None
            if side == 1 and l >= sl_base and sw4.trend == 1 and sw1.trend == 1 and sw5.last_high is not None:
                if c > sw5.last_high and (l - h1) >= 0.25 * atr_5 and c2 > o2 and c2b >= atr_5:
                    slp = min(sl_base - atr_5, c - max(1.5 * atr_5, c * 0.0020))
            elif side == -1 and h <= sl_base and sw4.trend == -1 and sw1.trend == -1 and sw5.last_low is not None:
                if c < sw5.last_low and (l1 - h) >= 0.25 * atr_5 and c2 < o2 and c2b >= atr_5:
                    slp = max(sl_base + atr_5, c + max(1.5 * atr_5, c * 0.0020))
            if slp is None:
                continue
            rd = abs(c - slp)
            if not (0.0020 <= rd / c <= 0.0180):
                continue
            disp_sc = sigmoid(c2b / atr_5, 1.2, 2.2)
            ok_p, _ = prosecutor_cross_examine(
                side=side,
                thesis_scores={"sweep": max(0.55, sw_sc), "disp": disp_sc, "ker4": sigmoid(ker_4h, 0.25, 9.0), "rvol": sigmoid(rvol5, 1.6, 2.2)},
                thesis_weights={"sweep": 1.2, "disp": 1.3, "ker4": 1.1, "rvol": 0.6},
                ker_4h=ker_4h,
                body_ratio_4h=br_4h,
                dir_4h_candle=dir_4h,
                htf_trend_1h=sw1.trend,
                htf_trend_4h=d1_tr if d1_tr != 0 else sw4.trend,
                rvol_entry=rvol5,
                sweep_bars_accepted=b_acc,
                is_counter_trend_sweep=(d1_tr != 0 and side != d1_tr),
                min_conviction=0.35,
            )
            if ok_p:
                return SignalCandidate(
                    symbol, "SMC_Sweep_V6", side, c, slp, c + side * sweep_tp_r * rd,
                    rd, ((3.0, 1.0),), 100 * 60, is_market=False, risk_mult=smc_risk_mult,
                )

    if not enable_fast_scalp or utc_dt.weekday() >= 5:
        return None

    if vwap is not None and (7 <= utc_dt.hour <= 20) and er_1h >= 0.25 and atr_15 > 0 and atr_5 > 0:
        if tr_up and rsi_1h >= 58.0 and l <= vwap < c and c > o and rsi_5 <= 48.0:
            slp = min(l, vwap - 0.5 * atr_15) - 0.4 * atr_5
            rd = c - slp
            if 0.0040 <= rd / c <= 0.0095:
                return SignalCandidate(symbol, "VWAP_Sniper", 1, c, slp, c + 1.3 * rd, rd, ((0.7, 0.1),), 30 * 60)
        if tr_dn and (100.0 - rsi_1h) >= 58.0 and h >= vwap > c and c < o and rsi_5 >= 52.0:
            slp = max(h, vwap + 0.5 * atr_15) + 0.4 * atr_5
            rd = slp - c
            if 0.0040 <= rd / c <= 0.0095:
                return SignalCandidate(symbol, "VWAP_Sniper", -1, c, slp, c - 1.3 * rd, rd, ((0.7, 0.1),), 30 * 60)

    if er_1h >= 0.30 and er_4h >= 0.22 and er_15 >= 0.30 and vavg_20 > 0 and v_last >= 1.8 * vavg_20 and atr_5 > 0:
        if tr_up and rsi_1h >= 68.0 and macd_hist > 0 and e9_5 > e20_5 > e50_5 and l <= e9_5 < c and c > o:
            slp = min(l, e20_5) - 0.5 * atr_5
            rd = c - slp
            if 0.0040 <= rd / c <= 0.0180:
                return SignalCandidate(symbol, "Mom9_Sniper", 1, c, slp, c + 1.8 * rd, rd, ((0.9, 0.1),), 30 * 60)
        if tr_dn and (100.0 - rsi_1h) >= 68.0 and macd_hist < 0 and e9_5 < e20_5 < e50_5 and h >= e9_5 > c and c < o:
            slp = max(h, e20_5) + 0.5 * atr_5
            rd = slp - c
            if 0.0040 <= rd / c <= 0.0180:
                return SignalCandidate(symbol, "Mom9_Sniper", -1, c, slp, c - 1.8 * rd, rd, ((0.9, 0.1),), 30 * 60)

    return None


# -------------------- Binance USDT-M Futures REST Client --------------------

@dataclasses.dataclass
class SymbolFilters:
    tick_size: float
    step_size: float
    min_qty: float
    min_notional: float


def round_step(val: float, step: float, floor_mode: bool = True) -> float:
    if step <= 0:
        return val
    dec = max(0, int(round(-math.log10(step)))) if step < 1.0 else 0
    fn = (lambda x: math.floor(x + 1e-9)) if floor_mode else round
    return round(fn(val / step) * step, dec)


class BinanceFuturesClient:
    def __init__(self, base_url: str, api_key: str = "", api_secret: str = "") -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.api_secret = api_secret.encode("utf-8")

    def _req(self, method: str, path: str, params: Optional[dict] = None, signed: bool = False) -> dict:
        params = dict(params or {})
        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params.setdefault("recvWindow", 5000)
            qs = urllib.parse.urlencode(params)
            sig = hmac.new(self.api_secret, qs.encode("utf-8"), hashlib.sha256).hexdigest()
            qs = f"{qs}&signature={sig}"
        else:
            qs = urllib.parse.urlencode(params)
        url = f"{self.base_url}{path}" + (f"?{qs}" if qs and method in ("GET", "DELETE") else "")
        data = qs.encode("utf-8") if qs and method == "POST" else None
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        if self.api_key:
            headers["X-MBX-APIKEY"] = self.api_key
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def load_filters(self, symbols: Tuple[str, ...]) -> Dict[str, SymbolFilters]:
        info = self._req("GET", "/fapi/v1/exchangeInfo")
        out: Dict[str, SymbolFilters] = {}
        wanted = set(symbols)
        for s in info.get("symbols", []):
            sym = s.get("symbol")
            if sym not in wanted or s.get("status") != "TRADING":
                continue
            tick = step = min_qty = 0.001
            min_notional = 5.0
            for f in s.get("filters", []):
                ft = f.get("filterType")
                if ft == "PRICE_FILTER":
                    tick = float(f["tickSize"])
                elif ft == "LOT_SIZE":
                    step = float(f["stepSize"])
                    min_qty = float(f["minQty"])
                elif ft == "MIN_NOTIONAL":
                    min_notional = float(f.get("notional", 5.0))
            out[sym] = SymbolFilters(tick, step, min_qty, min_notional)
        return out

    def get_klines(self, symbol: str, interval: str, limit: int = 120) -> List[Bar]:
        raw = self._req("GET", "/fapi/v1/klines", {"symbol": symbol, "interval": interval, "limit": limit})
        return [(int(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5])) for r in raw[:-1]]

    def get_usdt_balance(self) -> float:
        acc = self._req("GET", "/fapi/v2/account", signed=True)
        return float(acc.get("totalMarginBalance", 0.0))

    def get_positions(self) -> Dict[str, float]:
        pos = self._req("GET", "/fapi/v2/positionRisk", signed=True)
        return {p["symbol"]: float(p["positionAmt"]) for p in pos if abs(float(p["positionAmt"])) > 0}

    def set_leverage(self, symbol: str, leverage: int = 10) -> None:
        self._req("POST", "/fapi/v1/leverage", {"symbol": symbol, "leverage": leverage}, signed=True)

    def place_market(self, symbol: str, side: str, qty: float, reduce_only: bool = False) -> dict:
        params = {"symbol": symbol, "side": side, "type": "MARKET", "quantity": f"{qty}"}
        if reduce_only:
            params["reduceOnly"] = "true"
        return self._req("POST", "/fapi/v1/order", params, signed=True)

    def place_maker_limit(self, symbol: str, side: str, qty: float, price: float) -> dict:
        return self._req("POST", "/fapi/v1/order", {
            "symbol": symbol, "side": side, "type": "LIMIT", "timeInForce": "GTX",
            "quantity": f"{qty}", "price": f"{price}",
        }, signed=True)

    def place_stop_market(self, symbol: str, side: str, qty: float, stop_price: float) -> dict:
        return self._req("POST", "/fapi/v1/order", {
            "symbol": symbol, "side": side, "type": "STOP_MARKET",
            "quantity": f"{qty}", "stopPrice": f"{stop_price}", "reduceOnly": "true",
        }, signed=True)

    def place_tp_limit(self, symbol: str, side: str, qty: float, price: float) -> dict:
        return self._req("POST", "/fapi/v1/order", {
            "symbol": symbol, "side": side, "type": "LIMIT", "timeInForce": "GTC",
            "quantity": f"{qty}", "price": f"{price}", "reduceOnly": "true",
        }, signed=True)

    def cancel_all(self, symbol: str) -> None:
        self._req("DELETE", "/fapi/v1/allOpenOrders", {"symbol": symbol}, signed=True)


# -------------------- Position Sizing & Live Loop --------------------

def compute_order_qty(
    equity_usdt: float,
    risk_pct: float,
    entry_px: float,
    sl_px: float,
    filt: SymbolFilters,
    leverage: int = 10,
    max_slot_frac: float = 0.30,
) -> float:
    risk_dist = abs(entry_px - sl_px)
    if risk_dist <= 0 or entry_px <= 0 or equity_usdt <= 0:
        return 0.0
    raw_qty = (equity_usdt * risk_pct) / risk_dist
    max_notional = equity_usdt * leverage * max_slot_frac
    qty = min(raw_qty, max_notional / entry_px)
    qty = round_step(qty, filt.step_size, floor_mode=True)
    if qty < filt.min_qty or (qty * entry_px) < filt.min_notional:
        return 0.0
    return qty


def _btc_regime_score_from_4h(btc_4h: List[Bar], side: int) -> float:
    if len(btc_4h) < 30:
        return 1.0
    atr_s = compute_wilder_atr_series(btc_4h, 14)
    _, _, btc_tr = compute_topological_swings(btc_4h, atr_s, 1.25)
    _, o, h, l, c, _ = btc_4h[-1]
    a4 = max(atr_s[-1], 1e-12)
    disp = min(1.0, 0.60 * sigmoid(abs(c - o) / a4, 1.2, 2.2) + 0.40 * sigmoid(abs(c - o) / max(h - l, 1e-12), 0.60, 7.0))
    if side == 1 and btc_tr == -1 and c < o and disp >= 0.65:
        return max(0.05, 1.0 - 0.90 * disp)
    if side == -1 and btc_tr == 1 and c > o and disp >= 0.65:
        return max(0.05, 1.0 - 0.90 * disp)
    return 0.92 if side == btc_tr else 0.70


def run_bot(
    mode: str,
    symbols: Tuple[str, ...],
    leverage: int,
    max_open_pos: int,
    paper_equity: float,
    use_v7: bool = True,
    v7_risk_mult: float = 1.0,
    use_4h_trend: bool = True,
    v6_mode: str = "hybrid",
    use_pyramid: bool = True,
    use_stage2_pyramid: bool = True,
    donch_lb: int = 20,
    trail_atr_mult: float = 3.5,
    use_smc: bool = True,
    smc_risk_mult: float = 0.50,
    sweep_tp_r: float = 10.0,
    enable_fast_scalp: bool = False,
    small_account: bool = False,
    risk_pct: float = 0.015,
    daily_dd_cap_r: float = -2.5,
) -> None:
    base_url = TESTNET_BASE if mode == "testnet" else LIVE_BASE
    api_key = os.environ.get("BINANCE_API_KEY", "")
    api_secret = os.environ.get("BINANCE_API_SECRET", "")
    if mode in ("testnet", "live") and (not api_key or not api_secret):
        raise SystemExit("ERROR: Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables first.")

    client = BinanceFuturesClient(base_url, api_key, api_secret)
    filters = client.load_filters(symbols)
    slot_frac = 0.85 if small_account else 0.30
    print(
        f"[INIT] V7.0 mode={mode} syms={len(filters)}/{len(symbols)} v7={use_v7}({v7_risk_mult:.2f}x) "
        f"4H={use_4h_trend}({v6_mode}) smc={use_smc}({smc_risk_mult:.2f}x) small_acct={small_account} "
        f"risk={risk_pct*100:.2f}% lev={leverage}x daily_cb={daily_dd_cap_r:.1f}R"
    )

    if mode in ("testnet", "live"):
        for sym in filters:
            try:
                client.set_leverage(sym, leverage)
            except Exception as exc:
                print(f"[WARN] leverage failed for {sym}: {exc}")

    hwm_equity = paper_equity
    active_meta: Dict[str, dict] = {}
    daily_r_day = dt.datetime.now(dt.timezone.utc).date()
    daily_r_pnl = 0.0
    while True:
        try:
            now_day = dt.datetime.now(dt.timezone.utc).date()
            if now_day != daily_r_day:
                daily_r_day = now_day
                daily_r_pnl = 0.0
            equity = paper_equity if mode == "paper" else client.get_usdt_balance()
            hwm_equity = max(hwm_equity, equity)
            dd = (hwm_equity - equity) / hwm_equity if hwm_equity > 0 else 0.0
            dd_brake = 0.50 if dd >= 0.12 else (0.70 if dd >= 0.08 else 1.0)
            open_pos = {} if mode == "paper" else client.get_positions()

            btc_4h_cache = client.get_klines("BTCUSDT", "4h", 120) if "BTCUSDT" in filters else []

            for sym, meta in list(active_meta.items()):
                if mode != "paper" and meta["state"] == "PENDING":
                    if sym in open_pos:
                        exit_side = "SELL" if meta["side"] == 1 else "BUY"
                        qty_abs = abs(open_pos[sym])
                        client.place_stop_market(sym, exit_side, qty_abs, meta["sl"])
                        if meta["tp"] is not None:
                            client.place_tp_limit(sym, exit_side, qty_abs, meta["tp"])
                        meta["state"] = "OPEN"
                        print(f"[FILLED->BRACKET] {sym} SL={meta['sl']} TP={meta['tp']}")
                    elif time.time() > meta["expires_at"]:
                        client.cancel_all(sym)
                        active_meta.pop(sym, None)
                        print(f"[EXPIRED] {sym} pending order canceled")
                    continue
                if mode != "paper" and meta["state"] == "OPEN" and sym not in open_pos:
                    client.cancel_all(sym)
                    b5_close = client.get_klines(sym, "5m", 2)
                    if b5_close and meta.get("risk", 0.0) > 0:
                        c_last = b5_close[-1][4]
                        rem_f = (1.0 - meta.get("bank_frac", 0.0)) if meta.get("partial_taken") else 1.0
                        daily_r_pnl += rem_f * (((c_last - meta["entry"]) * meta["side"]) / meta["risk"])
                    active_meta.pop(sym, None)
                    print(f"[CLOSE] {sym} position closed -> open orders cleaned | daily_r={daily_r_pnl:+.2f}R")
                    continue
                if meta["state"] == "OPEN" and sym in open_pos:
                    exit_side = "SELL" if meta["side"] == 1 else "BUY"
                    qty_abs = abs(open_pos[sym])
                    if meta.get("trail_mult"):
                        b4 = client.get_klines(sym, "4h", 120)
                        if len(b4) >= 2:
                            ts4, o4, h4, l4, c4, _ = b4[-1]
                            if ts4 != meta.get("last_4h_ts"):
                                meta["last_4h_ts"] = ts4
                                atr4 = compute_wilder_atr(b4, 14)
                                ker4 = compute_ker([b[4] for b in b4], 20)
                                meta["best_px"] = max(meta["best_px"], h4) if meta["side"] == 1 else min(meta["best_px"], l4)
                                mfe_r = ((meta["best_px"] - meta["entry"]) * meta["side"]) / max(meta["risk"], 1e-12)
                                open_r = ((c4 - meta["entry"]) * meta["side"]) / max(meta["risk"], 1e-12)

                                if use_pyramid and meta.get("pyr_stage", 0) == 0 and mfe_r >= 2.0:
                                    meta["pyramid_armed"] = True
                                    lk_sl = round_step(meta["entry"] + meta["side"] * 0.35 * meta["risk"], filters[sym].tick_size, False)
                                    if (meta["side"] == 1 and lk_sl > meta["sl"] and lk_sl < c4) or (meta["side"] == -1 and lk_sl < meta["sl"] and lk_sl > c4):
                                        client.cancel_all(sym)
                                        client.place_stop_market(sym, exit_side, qty_abs, lk_sl)
                                        meta["sl"] = lk_sl
                                        print(f"[PYR1 ARMED BE+0.35R] {sym} SL->{lk_sl}")

                                tmult = meta["trail_mult"]
                                if open_r >= 14.0:
                                    tmult = 2.0
                                elif open_r >= 10.0:
                                    tmult = meta["trail_mult"] - ((open_r - 10.0) / 4.0) * (meta["trail_mult"] - 2.0)

                                raw_sl = meta["best_px"] + (-1 if meta["side"] == 1 else 1) * tmult * atr4
                                new_sl = round_step(raw_sl, filters[sym].tick_size, False)
                                crossed = (new_sl >= c4) if meta["side"] == 1 else (new_sl <= c4)
                                if crossed:
                                    client.cancel_all(sym)
                                    client.place_market(sym, exit_side, qty_abs, reduce_only=True)
                                    active_meta.pop(sym, None)
                                    print(f"[TRAIL EXIT MKT] {sym} @ ~{c4}")
                                    continue
                                better = (new_sl > meta["sl"]) if meta["side"] == 1 else (new_sl < meta["sl"])
                                if better:
                                    client.cancel_all(sym)
                                    client.place_stop_market(sym, exit_side, qty_abs, new_sl)
                                    meta["sl"] = new_sl
                                    print(f"[TRAIL SL] {sym} -> {new_sl}")

                                prev_o4, prev_c4 = b4[-2][1], b4[-2][4]
                                pb1 = (
                                    (meta["side"] == 1 and l4 <= prev_c4 and c4 > o4 and c4 > meta["entry"])
                                    or (meta["side"] == -1 and h4 >= prev_c4 and c4 < o4 and c4 < meta["entry"])
                                )
                                if use_pyramid and meta.get("pyramid_armed") and meta.get("pyr_stage", 0) == 0 and pb1:
                                    sl_p1 = round_step(c4 - meta["side"] * 1.5 * atr4, filters[sym].tick_size, False)
                                    qty_p1 = compute_order_qty(equity, 0.50 * risk_pct * dd_brake, c4, sl_p1, filters[sym], leverage=leverage, max_slot_frac=slot_frac)
                                    if qty_p1 > 0:
                                        side_str = "BUY" if meta["side"] == 1 else "SELL"
                                        client.place_market(sym, side_str, qty_p1)
                                        tot_qty = round_step(qty_abs + qty_p1, filters[sym].step_size, True)
                                        comb_sl = max(meta["sl"], sl_p1) if meta["side"] == 1 else min(meta["sl"], sl_p1)
                                        client.cancel_all(sym)
                                        client.place_stop_market(sym, exit_side, tot_qty, comb_sl)
                                        meta["sl"] = comb_sl
                                        meta["pyr_stage"] = 1
                                        print(f"[PYRAMID ST1 +0.5x] {sym} {side_str} +{qty_p1} SL->{comb_sl}")
                                elif use_pyramid and use_stage2_pyramid and meta.get("pyr_stage", 0) == 1 and open_r >= 4.2 and ker4 > 0.40:
                                    pb2 = (
                                        (meta["side"] == 1 and c4 > o4 and c4 > max(prev_c4, prev_o4))
                                        or (meta["side"] == -1 and c4 < o4 and c4 < min(prev_c4, prev_o4))
                                    )
                                    if pb2:
                                        sl_p2 = round_step(c4 - meta["side"] * 1.4 * atr4, filters[sym].tick_size, False)
                                        qty_p2 = compute_order_qty(equity, 0.35 * risk_pct * dd_brake, c4, sl_p2, filters[sym], leverage=leverage, max_slot_frac=slot_frac)
                                        if qty_p2 > 0:
                                            side_str = "BUY" if meta["side"] == 1 else "SELL"
                                            client.place_market(sym, side_str, qty_p2)
                                            tot_qty = round_step(qty_abs + qty_p2, filters[sym].step_size, True)
                                            lock2 = round_step(meta["entry"] + meta["side"] * 2.0 * meta["risk"], filters[sym].tick_size, False)
                                            comb_sl = max(meta["sl"], sl_p2, lock2) if meta["side"] == 1 else min(meta["sl"], sl_p2, lock2)
                                            client.cancel_all(sym)
                                            client.place_stop_market(sym, exit_side, tot_qty, comb_sl)
                                            meta["sl"] = comb_sl
                                            meta["pyr_stage"] = 2
                                            print(f"[PYRAMID ST2 +0.35x] {sym} {side_str} +{qty_p2} SL->{comb_sl}")
                    elif meta.get("bank_frac", 0.0) > 0 or meta["step_locks"]:
                        b5 = client.get_klines(sym, "5m", 3)
                        if b5:
                            _, _, h, l, c, _ = b5[-1]
                            meta["best_px"] = max(meta["best_px"], h) if meta["side"] == 1 else min(meta["best_px"], l)
                            mfe_r = ((meta["best_px"] - meta["entry"]) * meta["side"]) / max(meta["risk"], 1e-12)
                            if meta.get("bank_frac", 0.0) > 0 and (not meta.get("partial_taken")) and mfe_r >= meta.get("bank_r", 3.0):
                                part_qty = round_step(qty_abs * meta["bank_frac"], filters[sym].step_size, True)
                                rem_qty = round_step(qty_abs - part_qty, filters[sym].step_size, True)
                                if part_qty >= filters[sym].min_qty and rem_qty >= filters[sym].min_qty:
                                    client.cancel_all(sym)
                                    client.place_market(sym, exit_side, part_qty, reduce_only=True)
                                    lk_sl = round_step(meta["entry"] + meta["side"] * meta.get("be_lock_r", 0.50) * meta["risk"], filters[sym].tick_size, False)
                                    if (meta["side"] == 1 and lk_sl > meta["sl"] and lk_sl < c) or (meta["side"] == -1 and lk_sl < meta["sl"] and lk_sl > c):
                                        meta["sl"] = lk_sl
                                    client.place_stop_market(sym, exit_side, rem_qty, meta["sl"])
                                    if meta["tp"] is not None:
                                        client.place_tp_limit(sym, exit_side, rem_qty, meta["tp"])
                                    meta["partial_taken"] = True
                                    daily_r_pnl += meta["bank_frac"] * meta.get("bank_r", 3.0)
                                    qty_abs = rem_qty
                                    print(f"[V7 BANK35] {sym} banked {part_qty} @ >=+{meta.get('bank_r', 3.0):.1f}R, SL->{meta['sl']}")
                            for act_r, lk_r in meta["step_locks"]:
                                hit = (h >= meta["entry"] + act_r * meta["risk"]) if meta["side"] == 1 else (l <= meta["entry"] - act_r * meta["risk"])
                                new_sl = round_step(meta["entry"] + meta["side"] * lk_r * meta["risk"], filters[sym].tick_size, False)
                                better = (new_sl > meta["sl"] and new_sl < c) if meta["side"] == 1 else (new_sl < meta["sl"] and new_sl > c)
                                if hit and better:
                                    client.cancel_all(sym)
                                    client.place_stop_market(sym, exit_side, qty_abs, new_sl)
                                    if meta["tp"] is not None:
                                        client.place_tp_limit(sym, exit_side, qty_abs, meta["tp"])
                                    meta["sl"] = new_sl
                                    print(f"[LOCK] {sym} SL moved -> {new_sl}")

            if daily_r_pnl <= daily_dd_cap_r:
                time.sleep(30)
                continue

            for sym, filt in filters.items():
                if sym in open_pos or sym in active_meta or (len(open_pos) + len(active_meta)) >= max_open_pos:
                    continue
                b5 = client.get_klines(sym, "5m", 290)
                b15 = client.get_klines(sym, "15m", 80)
                b1h = client.get_klines(sym, "1h", 120)
                b4h = btc_4h_cache if sym == "BTCUSDT" and btc_4h_cache else client.get_klines(sym, "4h", 120)
                b1d = client.get_klines(sym, "1d", 80)
                btc_fn = None if sym == "BTCUSDT" else (lambda sd: _btc_regime_score_from_4h(btc_4h_cache, sd))
                sig = evaluate_symbol_bars(
                    sym, b5, b15, b1h, b4h, b1d,
                    use_v7=use_v7, v7_risk_mult=v7_risk_mult,
                    use_4h_trend=use_4h_trend, v6_mode=v6_mode, donch_lb=donch_lb,
                    trail_atr_mult=trail_atr_mult, btc_regime_fn=btc_fn,
                    use_smc=use_smc, smc_risk_mult=smc_risk_mult,
                    sweep_tp_r=sweep_tp_r, enable_fast_scalp=enable_fast_scalp,
                )
                if sig is None:
                    continue
                ep = round_step(sig.entry_px, filt.tick_size, False)
                sl = round_step(sig.sl_px, filt.tick_size, False)
                tp = round_step(sig.tp_px, filt.tick_size, False) if sig.tp_px is not None else None
                qty = compute_order_qty(equity, risk_pct * sig.risk_mult * dd_brake, ep, sl, filt, leverage=leverage, max_slot_frac=slot_frac)
                if qty <= 0:
                    print(f"[SKIP] {sym} qty=0 (minNotional={filt.min_notional} equity={equity:.2f})")
                    continue
                side_str = "BUY" if sig.side == 1 else "SELL"
                print(f"[SIGNAL] {sym} {sig.engine} {side_str} qty={qty} ep={ep} sl={sl} tp={tp}")
                if mode in ("testnet", "live"):
                    if sig.is_market:
                        client.place_market(sym, side_str, qty)
                    else:
                        client.place_maker_limit(sym, side_str, qty, ep)
                    active_meta[sym] = {
                        "state": "PENDING", "side": sig.side, "entry": ep, "best_px": ep,
                        "sl": sl, "tp": tp, "risk": abs(ep - sl), "step_locks": sig.step_locks,
                        "trail_mult": sig.trail_atr_mult, "last_4h_ts": b4h[-1][0] if b4h else 0,
                        "pyramid_armed": False, "pyr_stage": 0,
                        "bank_r": sig.bank_r, "bank_frac": sig.bank_frac, "be_lock_r": sig.be_lock_r,
                        "partial_taken": False,
                        "expires_at": time.time() + sig.expire_sec,
                    }
        except urllib.error.URLError as exc:
            print(f"[NET ERR] {exc}")
        except Exception as exc:
            print(f"[ERR] {exc}")
        time.sleep(30)


def main() -> None:
    ap = argparse.ArgumentParser(description="Binance Futures Multi-Coin V7.0 Intraday Cashflow + 4H Cognitive Bot")
    ap.add_argument("--mode", choices=("paper", "testnet", "live"), default="paper")
    ap.add_argument("--leverage", type=int, default=10)
    ap.add_argument("--max-pos", type=int, default=3)
    ap.add_argument("--paper-equity", type=float, default=500.0)
    ap.add_argument("--small-account", action="store_true", help="Enable $100 small-account mode (3.0% risk, 15x lev, -2.5R daily CB)")
    ap.add_argument("--risk-pct", type=float, default=None, help="Override base risk per trade (e.g. 0.025 or 0.03)")
    ap.add_argument("--daily-stop-r", type=float, default=-2.5, help="Daily realized R circuit breaker (default -2.5R)")
    ap.add_argument("--no-v7", action="store_true", help="Disable V7.0 Intraday Scene-Graph Physics engine")
    ap.add_argument("--v7-risk-mult", type=float, default=1.0, help="Risk multiplier for V7 Intraday Physics")
    ap.add_argument("--no-4h-trend", action="store_true", help="Disable primary 4H_V6_Cognitive engine")
    ap.add_argument("--v6-mode", "--v5-mode", dest="v6_mode", choices=("hybrid", "topological"), default="hybrid")
    ap.add_argument("--no-pyramid", action="store_true", help="Disable risk-free 2-stage pyramiding")
    ap.add_argument("--no-stage2-pyramid", action="store_true", help="Disable Stage-2 0.35x pyramid")
    ap.add_argument("--donch-lb", type=int, default=20)
    ap.add_argument("--trail-atr-mult", type=float, default=3.5)
    ap.add_argument("--no-smc", action="store_true", help="Disable secondary SMC_Sweep_V6 engine")
    ap.add_argument("--smc-risk-mult", type=float, default=0.50, help="Risk multiplier for SMC_Sweep_V6 (0.50 -> DD<12R, 1.00 -> max R)")
    ap.add_argument("--sweep-tp-r", type=float, default=10.0, help="TP multiple in R for V7 & SMC_Sweep")
    ap.add_argument("--enable-fast-scalp", action="store_true", help="Enable experimental fast scalp sleeves")
    ap.add_argument("--symbols", type=str, default=",".join(DEFAULT_SYMBOLS))
    args = ap.parse_args()
    syms = tuple(s.strip().upper() for s in args.symbols.split(",") if s.strip())
    lev = 15 if (args.small_account and args.leverage == 10) else args.leverage
    risk_pct = args.risk_pct if args.risk_pct is not None else (0.03 if args.small_account else 0.015)
    smc_mult = 1.0 if (args.small_account and args.smc_risk_mult == 0.50) else args.smc_risk_mult
    run_bot(
        args.mode, syms, lev, args.max_pos, args.paper_equity,
        use_v7=not args.no_v7, v7_risk_mult=args.v7_risk_mult,
        use_4h_trend=not args.no_4h_trend, v6_mode=args.v6_mode, use_pyramid=not args.no_pyramid,
        use_stage2_pyramid=not args.no_stage2_pyramid, donch_lb=args.donch_lb,
        trail_atr_mult=args.trail_atr_mult, use_smc=not args.no_smc,
        smc_risk_mult=smc_mult, sweep_tp_r=args.sweep_tp_r, enable_fast_scalp=args.enable_fast_scalp,
        small_account=args.small_account, risk_pct=risk_pct, daily_dd_cap_r=args.daily_stop_r,
    )


if __name__ == "__main__":
    main()
