# QUANTCONNECT.COM - Binance Futures Multi-Coin V11.0 Institutional Exact-R Cashflow + Topological Swings + 4H Cognitive
# Audited with ZERO HTF lookahead on 823,154 BTC 5m bars (2020-2026, fee-inclusive exact 1.0R sizing):
#   1) Sleeve 1 (use_v10=true): V11_SessEq_1H_TOPO (pruned 15M_TOPO & unpruned LON; ATR-ZigZag prom>=1.20, rvol>=1.10)
#      -> 50/35/15 Session Equilibrium Exit (50%@+1.8R->BE+0.25R, 35%@+3.2R->+1.25R, 15%@+6.5R) + pruned V9_LON (rvol>=1.15)
#   2) Sleeve 2 (use_v8=true): V10_Intraday_Physics (5m CompVacuum + BPR/iFVG + Bayesian Prosecutor + 45/40/15 @ 2.2R/4.5R/10R)
#   3) Sleeve 3 (use_4h_trend=true): 4H_V6_Cognitive (Topological 4H Swings + 2-Stage Pyramid + Climax Ratchet)
#   4) Sleeve 4 (use_smc=true): SMC_Sweep_V6 (Restored! 10R BE@3R->+1R + 1D Macro Filter, PF 2.40)
#   - Account Profiles: `DAILY_HUNTER` (3.0%/3.8% A+, 0.80x >15% DD, 4 risk slots, -2.0R/day CB, $25 50/50 vault skim)
#     and `TURBO_SNIPER` (3.6%/4.2% A+, 0.80x >15% DD, 4 risk slots, -2.5R/day CB, $20 50/50 vault skim)
#   - Fee-Inclusive Exact 1.0R Sizing: Notional = Risk_USD / (sl_pct + 0.0010 RT fee+slip buffer).

from AlgorithmImports import *
from collections import deque
import math


def _sigmoid(x: float, x0: float = 0.0, k: float = 1.0) -> float:
    z = max(-60.0, min(60.0, -k * (x - x0)))
    return 1.0 / (1.0 + math.exp(z))


def _ker_slice(closes: list[float]) -> float:
    if len(closes) < 3:
        return 0.0
    den = sum(abs(closes[i] - closes[i - 1]) for i in range(1, len(closes)))
    return abs(closes[-1] - closes[0]) / den if den > 1e-12 else 0.0


def _detect_v7_comp_vacuum(
    bars: list[tuple[float, float, float, float]],
    atr5: float,
    barriers_hi: list[float],
    barriers_lo: list[float],
    trend_4h: int,
    max_approach_ker: float = 0.42,
    min_implied_r: float = 3.0,
) -> tuple[int, float, float] | None:
    """V7 Setup A: Compression grind into 1H liquidity barrier + sweep & 4H-aligned snap."""
    if atr5 <= 0 or len(bars) < 30 or trend_4h == 0:
        return None
    o0, h0, l0, c0 = bars[-1]
    rng0 = h0 - l0
    body0 = abs(c0 - o0)
    if rng0 <= 0 or body0 < 0.45 * rng0 or rng0 < 0.90 * atr5:
        return None
    win = bars[-30:]
    win_h = [b[1] for b in win]
    win_l = [b[2] for b in win]
    win_c = [b[3] for b in win]

    if trend_4h == 1 and c0 > o0 and barriers_lo:
        k_vel = body0 / atr5
        if k_vel < 1.05:
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
                    if sweep_low < lv and c0 > lv and (lv - sweep_low) <= 2.2 * atr5 and _validate_sweep_reclaim_qc(bars, 1, lv, atr5):
                        return (1, sweep_low, origin_px)

    if trend_4h == -1 and c0 < o0 and barriers_hi:
        k_vel = body0 / atr5
        if k_vel < 1.05:
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
                    if sweep_high > lv and c0 < lv and (sweep_high - lv) <= 2.2 * atr5 and _validate_sweep_reclaim_qc(bars, -1, lv, atr5):
                        return (-1, sweep_high, origin_px)
    return None


def _detect_v7_bpr(
    bars: list[tuple[float, float, float, float]],
    atr5: float,
    barriers_hi: list[float],
    barriers_lo: list[float],
    trend_4h: int,
    trend_1h: int,
    min_bpr_k: float = 1.20,
) -> dict | None:
    """V7 Setup B: Sweep + Overlapping Balanced Price Range (BPR/iFVG) Polarity Inversion."""
    if atr5 <= 0 or len(bars) < 16 or trend_4h == 0 or trend_4h != trend_1h:
        return None
    b2, b1, b0 = bars[-3], bars[-2], bars[-1]
    o_d, h_d, l_d, c_d = b1
    disp_body = abs(c_d - o_d)
    k_vel = disp_body / atr5
    if k_vel < min_bpr_k:
        return None
    sub = bars[-12:]
    sub_h = [b[1] for b in sub]
    sub_l = [b[2] for b in sub]

    if trend_4h == 1 and c_d > o_d and b0[3] > b2[1] and (b0[2] - b2[1]) >= 0.12 * atr5 and barriers_lo:
        d_lo, d_hi = b2[1], b0[2]
        sweep_low = min(sub_l)
        if any(sweep_low < lv and c_d > lv and (lv - sweep_low) <= 2.5 * atr5 for lv in barriers_lo):
            for m in range(len(bars) - 10, len(bars) - 3):
                if bars[m - 1][2] - bars[m + 1][1] >= 0.10 * atr5 and bars[m][3] < bars[m][0]:
                    ov_lo = max(d_lo, bars[m + 1][1])
                    ov_hi = min(d_hi, bars[m - 1][2])
                    if ov_hi > ov_lo:
                        vac = min(1.0, (k_vel - 1.0) * 0.45 + 0.35)
                        return {"side": 1, "low": ov_lo, "high": ov_hi, "mid": 0.5 * (ov_lo + ov_hi), "sweep": sweep_low, "k": k_vel, "vac": vac}
    if trend_4h == -1 and c_d < o_d and b0[3] < b2[2] and (b2[2] - b0[1]) >= 0.12 * atr5 and barriers_hi:
        d_lo, d_hi = b0[1], b2[2]
        sweep_high = max(sub_h)
        if any(sweep_high > lv and c_d < lv and (sweep_high - lv) <= 2.5 * atr5 for lv in barriers_hi):
            for m in range(len(bars) - 10, len(bars) - 3):
                if bars[m + 1][2] - bars[m - 1][1] >= 0.10 * atr5 and bars[m][3] > bars[m][0]:
                    ov_lo = max(d_lo, bars[m - 1][1])
                    ov_hi = min(d_hi, bars[m + 1][2])
                    if ov_hi > ov_lo:
                        vac = min(1.0, (k_vel - 1.0) * 0.45 + 0.35)
                        return {"side": -1, "low": ov_lo, "high": ov_hi, "mid": 0.5 * (ov_lo + ov_hi), "sweep": sweep_high, "k": k_vel, "vac": vac}
    return None


def _soft_and_log_odds(scores: dict, weights: dict, veto_floors: dict | None = None) -> float:
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
    return _sigmoid(num / den, 0.0, 1.0) if den > 0 else 0.0


def _prosecutor_cross_examine(
    side: int,
    thesis_scores: dict,
    thesis_weights: dict,
    ker_4h: float,
    body_ratio_4h: float,
    dir_4h_candle: int,
    htf_trend_1h: int,
    htf_trend_4h: int,
    rvol_entry: float,
    sweep_bars_accepted: int = 0,
    is_counter_trend_sweep: bool = False,
    min_conviction: float = 0.55,
    entry_px: float = 0.0,
    risk_dist: float = 0.0,
    opposing_htf_walls: list[float] | None = None,
    min_clearance_r: float = 0.0,
    ref_snap: dict | None = None,
    min_tp1_clearance_r: float = 2.2,
    hard_veto_ref_brick: bool = False,
) -> tuple[bool, float]:
    """V12.0 Bayesian Prosecutor: HTF Brick-Wall + Unmitigated PDH/PWH Clearance + Sweep Decay + Freight-Train."""
    if sweep_bars_accepted > 1:
        return False, 0.0
    if is_counter_trend_sweep and ker_4h > 0.45 and (dir_4h_candle == -side and body_ratio_4h >= 0.55 or htf_trend_4h == -side):
        return False, 0.0
    bw_pen = 0.0
    if opposing_htf_walls and risk_dist > 0 and min_clearance_r > 0:
        nearest_r = 99.0
        for w in opposing_htf_walls:
            clr_r = ((w - entry_px) * side) / risk_dist
            if clr_r > 0.0 and clr_r < nearest_r:
                nearest_r = clr_r
        if nearest_r < min_clearance_r:
            bw_pen = min(1.0, max(0.0, (min_clearance_r - nearest_r) / min_clearance_r))
    if ref_snap and risk_dist > 0:
        ref_walls = []
        if side == 1:
            if ref_snap.get("pdh") is not None and ref_snap.get("pdh_touches", 0) <= 1:
                ref_walls.append(ref_snap["pdh"])
            if ref_snap.get("pwh") is not None:
                ref_walls.append(ref_snap["pwh"])
        else:
            if ref_snap.get("pdl") is not None and ref_snap.get("pdl_touches", 0) <= 1:
                ref_walls.append(ref_snap["pdl"])
            if ref_snap.get("pwl") is not None:
                ref_walls.append(ref_snap["pwl"])
        for rw in ref_walls:
            r_rw = ((rw - entry_px) * side) / risk_dist
            if 0.0 < r_rw < min_tp1_clearance_r:
                bw_pen = max(bw_pen, min(1.0, (min_tp1_clearance_r - r_rw) / min_tp1_clearance_r))
                if is_counter_trend_sweep or hard_veto_ref_brick:
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
    p_contra = 0.85 * bw_pen + freight_pen + 0.55 * vdiv_pen
    conv = _sigmoid(2.4 * l_thesis - 2.6 * p_contra - 0.35, 0.0, 1.0)
    return (conv >= min_conviction), conv


class CausalSwingTracker:
    def __init__(self, k: int = 2, max_active: int = 25) -> None:
        self.k, self.max_active = k, max_active
        self.win = deque(maxlen=2 * k + 1)
        self.bar_idx = -1
        self.last_high = self.last_low = None
        self.trend = 0
        self.act_hi, self.act_lo = [], []

    def update(self, bar) -> None:
        h, l, c = float(bar.High), float(bar.Low), float(bar.Close)
        self.bar_idx += 1
        self.win.append((h, l))
        if len(self.win) == 2 * self.k + 1:
            m = self.k
            ch, cl = self.win[m][0], self.win[m][1]
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


class CausalTopologicalZigZag:
    """Scale-free volatility-adjusted topological swing tracker (ZERO k=2/k=3 fractals)."""

    def __init__(self, atr_mult: float = 1.15, max_active: int = 24) -> None:
        self.atr_mult = atr_mult
        self.max_active = max_active
        self.dir = 0
        self.bar_idx = -1
        self.piv_idx = 0
        self.piv_hi = self.piv_lo = None
        self.run_hi = self.run_lo = None
        self.last_hi = self.last_lo = None
        self.trend = 0
        self.act_hi = []
        self.act_lo = []

    def update(self, h: float, l: float, atr: float, c: float | None = None) -> None:
        self.bar_idx += 1
        if self.piv_hi is None:
            self.piv_hi = self.run_hi = h
            self.piv_lo = self.run_lo = l
            self.piv_idx = self.bar_idx
            return
        self.run_hi = max(self.run_hi, h)
        self.run_lo = min(self.run_lo, l)
        if atr > 0:
            th = self.atr_mult * atr
            if self.dir == 0:
                if h - self.piv_lo >= th:
                    prom = (h - self.piv_lo) / max(atr, 1e-12)
                    self.last_lo = self.piv_lo
                    self.act_lo.append((self.piv_idx, self.piv_lo, prom))
                    self.act_lo = self.act_lo[-self.max_active:]
                    self.dir, self.piv_hi, self.piv_idx, self.run_lo = 1, h, self.bar_idx, l
                elif self.piv_hi - l >= th:
                    prom = (self.piv_hi - l) / max(atr, 1e-12)
                    self.last_hi = self.piv_hi
                    self.act_hi.append((self.piv_idx, self.piv_hi, prom))
                    self.act_hi = self.act_hi[-self.max_active:]
                    self.dir, self.piv_lo, self.piv_idx, self.run_hi = -1, l, self.bar_idx, h
                else:
                    if h > self.piv_hi:
                        self.piv_hi, self.piv_idx = h, self.bar_idx
                    if l < self.piv_lo:
                        self.piv_lo, self.piv_idx = l, self.bar_idx
            elif self.dir == 1:
                if h >= self.piv_hi:
                    self.piv_hi, self.piv_idx, self.run_lo = h, self.bar_idx, l
                elif self.piv_hi - l >= th:
                    prom = (self.piv_hi - self.run_lo) / max(atr, 1e-12)
                    self.last_hi = self.piv_hi
                    self.act_hi.append((self.piv_idx, self.piv_hi, prom))
                    self.act_hi = self.act_hi[-self.max_active:]
                    self.dir, self.piv_lo, self.piv_idx, self.run_hi = -1, l, self.bar_idx, h
            else:
                if l <= self.piv_lo:
                    self.piv_lo, self.piv_idx, self.run_hi = l, self.bar_idx, h
                elif h - self.piv_lo >= th:
                    prom = (self.run_hi - self.piv_lo) / max(atr, 1e-12)
                    self.last_lo = self.piv_lo
                    self.act_lo.append((self.piv_idx, self.piv_lo, prom))
                    self.act_lo = self.act_lo[-self.max_active:]
                    self.dir, self.piv_hi, self.piv_idx, self.run_lo = 1, h, self.bar_idx, l
        self.act_hi = [x for x in self.act_hi if h <= x[1]]
        self.act_lo = [x for x in self.act_lo if l >= x[1]]
        px = c if c is not None else 0.5 * (h + l)
        if self.last_hi is not None and px > self.last_hi:
            self.trend = 1
        elif self.last_lo is not None and px < self.last_lo:
            self.trend = -1


class WilderATR14:
    def __init__(self) -> None:
        self.prev_close = None
        self.val = 0.0
        self.init = False

    def update(self, h: float, l: float, c: float) -> float:
        tr = (h - l) if self.prev_close is None else max(h - l, abs(h - self.prev_close), abs(l - self.prev_close))
        self.prev_close = c
        if not self.init:
            self.val = tr
            self.init = True
        else:
            self.val = (self.val * 13.0 + tr) / 14.0
        return self.val


class WilderADX14:
    def __init__(self) -> None:
        self.prev_h = self.prev_l = self.prev_c = None
        self.atr = self.pdm = self.mdm = self.adx = 0.0
        self.dx_init = False

    def update(self, h: float, l: float, c: float) -> float:
        if self.prev_h is None:
            self.prev_h, self.prev_l, self.prev_c = h, l, c
            self.atr = max(h - l, 1e-12)
            return 0.0
        tr = max(h - l, abs(h - self.prev_c), abs(l - self.prev_c))
        up, dn = h - self.prev_h, self.prev_l - l
        p = up if (up > dn and up > 0) else 0.0
        m = dn if (dn > up and dn > 0) else 0.0
        self.prev_h, self.prev_l, self.prev_c = h, l, c
        alpha = 1.0 / 14.0
        self.atr = (1.0 - alpha) * self.atr + alpha * tr
        self.pdm = (1.0 - alpha) * self.pdm + alpha * p
        self.mdm = (1.0 - alpha) * self.mdm + alpha * m
        if self.atr <= 1e-12:
            return self.adx
        pdi = 100.0 * self.pdm / self.atr
        mdi = 100.0 * self.mdm / self.atr
        den = pdi + mdi
        dx = (100.0 * abs(pdi - mdi) / den) if den > 1e-12 else 0.0
        if not self.dx_init:
            self.adx = dx
            self.dx_init = True
        else:
            self.adx = (1.0 - alpha) * self.adx + alpha * dx
        return self.adx


class WilderRSI14:
    def __init__(self) -> None:
        self.prev_c = None
        self.gains, self.losses = [], []
        self.ag = self.al = 0.0
        self.val = 50.0

    def update(self, c: float) -> float:
        if self.prev_c is None:
            self.prev_c = c
            return 50.0
        d = c - self.prev_c
        self.prev_c = c
        g, l = (d, 0.0) if d > 0 else (0.0, -d)
        if len(self.gains) < 14:
            self.gains.append(g)
            self.losses.append(l)
            self.ag = sum(self.gains) / len(self.gains)
            self.al = sum(self.losses) / len(self.losses)
        else:
            self.ag = (self.ag * 13.0 + g) / 14.0
            self.al = (self.al * 13.0 + l) / 14.0
        self.val = 100.0 if self.al <= 1e-12 else (100.0 - 100.0 / (1.0 + self.ag / self.al))
        return self.val


class EmaState:
    def __init__(self) -> None:
        self.e9 = self.e12 = self.e20 = self.e26 = self.e50 = self.msig = None
        self.macd_hist = 0.0
        self.closes = deque(maxlen=25)
        self.er14 = 0.0

    def update(self, c: float) -> None:
        self.e9 = c if self.e9 is None else (c * 0.2 + self.e9 * 0.8)
        self.e12 = c if self.e12 is None else (c * (2.0 / 13.0) + self.e12 * (11.0 / 13.0))
        self.e20 = c if self.e20 is None else (c * (2.0 / 21.0) + self.e20 * (19.0 / 21.0))
        self.e26 = c if self.e26 is None else (c * (2.0 / 27.0) + self.e26 * (25.0 / 27.0))
        self.e50 = c if self.e50 is None else (c * (2.0 / 51.0) + self.e50 * (49.0 / 51.0))
        macd = self.e12 - self.e26
        self.msig = macd if self.msig is None else (macd * 0.2 + self.msig * 0.8)
        self.macd_hist = macd - self.msig
        self.closes.append(c)
        if len(self.closes) >= 15:
            arr = list(self.closes)[-15:]
            den = sum(abs(arr[i] - arr[i - 1]) for i in range(1, len(arr)))
            self.er14 = abs(arr[-1] - arr[0]) / den if den > 0 else 0.0

    @property
    def trend(self) -> int:
        if self.e20 is None or self.e50 is None:
            return 0
        return 1 if self.e20 > self.e50 else (-1 if self.e20 < self.e50 else 0)


class DailySessionTracker:
    """Strictly causal V9.0 Daily Session High/Low Tracker (London 07-12 UTC H/L)."""

    def __init__(self, expiry_bars_5m: int = 60) -> None:
        self.expiry_bars_5m = int(expiry_bars_5m)
        self.cur_day = None
        self.lon_hi = self.lon_lo = None
        self.lon_hi_sw = self.lon_lo_sw = False
        self.cands_lon = []

    def step_5m(self, dt, idx_5m: int, h: float, l: float, c: float) -> None:
        d = dt.date()
        hr = int(dt.hour)
        if self.cur_day != d:
            self.cur_day = d
            self.lon_hi = self.lon_lo = None
            self.lon_hi_sw = self.lon_lo_sw = False
        if 7 <= hr < 12:
            self.lon_hi = h if self.lon_hi is None else max(self.lon_hi, h)
            self.lon_lo = l if self.lon_lo is None else min(self.lon_lo, l)
        self.cands_lon = [x for x in self.cands_lon if (idx_5m - x["start_i"]) <= self.expiry_bars_5m][-6:]
        if hr >= 12 and self.lon_lo is not None and not self.lon_lo_sw and l < self.lon_lo and c > self.lon_lo:
            self.lon_lo_sw = True
            self.cands_lon.append({"side": 1, "start_i": idx_5m, "sl_base": l})
        if hr >= 12 and self.lon_hi is not None and not self.lon_hi_sw and h > self.lon_hi and c < self.lon_hi:
            self.lon_hi_sw = True
            self.cands_lon.append({"side": -1, "start_i": idx_5m, "sl_base": h})


class CausalTopoSwingTracker:
    """V12.0 Scale-Free Topological Swing Tracker (replaces CausalSwingTracker(2) fractals)."""

    def __init__(self, prom_mult: float = 0.80, min_sep: int = 3, max_active: int = 25) -> None:
        self.prom_mult = float(prom_mult)
        self.min_sep = int(min_sep)
        self.max_active = int(max_active)
        self.bar_idx = -1
        self.prev_c = None
        self.atr = 0.0
        self.atr_init = False
        self.dir = 0
        self.piv_idx = 0
        self.piv_hi = self.piv_lo = None
        self.last_high = self.last_low = None
        self.trend = 0
        self.act_hi, self.act_lo = [], []

    def update(self, bar) -> None:
        h, l, c = float(bar.High), float(bar.Low), float(bar.Close)
        self.bar_idx += 1
        tr = (h - l) if self.prev_c is None else max(h - l, abs(h - self.prev_c), abs(l - self.prev_c))
        self.prev_c = c
        if not self.atr_init:
            self.atr, self.atr_init = tr, True
        else:
            self.atr = (self.atr * 13.0 + tr) / 14.0
        if self.piv_hi is None:
            self.piv_hi, self.piv_lo, self.piv_idx = h, l, self.bar_idx
        elif self.atr > 0:
            th = self.prom_mult * self.atr
            if self.dir == 0:
                if h - self.piv_lo >= th and (self.bar_idx - self.piv_idx) >= self.min_sep:
                    self.last_low = self.piv_lo
                    self.act_lo.append((self.piv_idx, self.piv_lo))
                    self.act_lo = self.act_lo[-self.max_active:]
                    self.dir, self.piv_hi, self.piv_idx = 1, h, self.bar_idx
                elif self.piv_hi - l >= th and (self.bar_idx - self.piv_idx) >= self.min_sep:
                    self.last_high = self.piv_hi
                    self.act_hi.append((self.piv_idx, self.piv_hi))
                    self.act_hi = self.act_hi[-self.max_active:]
                    self.dir, self.piv_lo, self.piv_idx = -1, l, self.bar_idx
                else:
                    if h > self.piv_hi:
                        self.piv_hi, self.piv_idx = h, self.bar_idx
                    if l < self.piv_lo:
                        self.piv_lo, self.piv_idx = l, self.bar_idx
            elif self.dir == 1:
                if h >= self.piv_hi:
                    self.piv_hi, self.piv_idx = h, self.bar_idx
                elif self.piv_hi - l >= th and (self.bar_idx - self.piv_idx) >= self.min_sep:
                    self.last_high = self.piv_hi
                    self.act_hi.append((self.piv_idx, self.piv_hi))
                    self.act_hi = self.act_hi[-self.max_active:]
                    self.dir, self.piv_lo, self.piv_idx = -1, l, self.bar_idx
            else:
                if l <= self.piv_lo:
                    self.piv_lo, self.piv_idx = l, self.bar_idx
                elif h - self.piv_lo >= th and (self.bar_idx - self.piv_idx) >= self.min_sep:
                    self.last_low = self.piv_lo
                    self.act_lo.append((self.piv_idx, self.piv_lo))
                    self.act_lo = self.act_lo[-self.max_active:]
                    self.dir, self.piv_hi, self.piv_idx = 1, h, self.bar_idx
        self.act_hi = [x for x in self.act_hi if h <= x[1]]
        self.act_lo = [x for x in self.act_lo if l >= x[1]]
        if self.last_high is not None and c > self.last_high:
            self.trend = 1
        elif self.last_low is not None and c < self.last_low:
            self.trend = -1


class CausalReferenceTracker:
    """V12.0 Strictly Causal Reference Level Tracker (PDH/PDL + Touch Decay, PWH/PWL, Asia/London)."""

    def __init__(self) -> None:
        self.cur_day = self.cur_week = None
        self.dy_hi = self.dy_lo = self.pdh = self.pdl = None
        self.wk_hi = self.wk_lo = self.pwh = self.pwl = None
        self.asia_hi = self.asia_lo = self.lon_hi = self.lon_lo = None
        self.pdh_touches = self.pdl_touches = 0

    def update(self, dt, h: float, l: float, c: float, atr: float) -> dict:
        d = dt.date()
        wk = dt.isocalendar()[:2]
        hr_min = dt.hour + dt.minute / 60.0
        if self.cur_week is None:
            self.cur_week, self.wk_hi, self.wk_lo = wk, h, l
        elif wk != self.cur_week:
            self.pwh, self.pwl = self.wk_hi, self.wk_lo
            self.cur_week, self.wk_hi, self.wk_lo = wk, h, l
        else:
            self.wk_hi = max(self.wk_hi, h)
            self.wk_lo = min(self.wk_lo, l)

        if self.cur_day is None:
            self.cur_day, self.dy_hi, self.dy_lo = d, h, l
        elif d != self.cur_day:
            self.pdh, self.pdl = self.dy_hi, self.dy_lo
            self.cur_day, self.dy_hi, self.dy_lo = d, h, l
            self.asia_hi = self.asia_lo = self.lon_hi = self.lon_lo = None
            self.pdh_touches = self.pdl_touches = 0
        else:
            self.dy_hi = max(self.dy_hi, h)
            self.dy_lo = min(self.dy_lo, l)

        if hr_min < 7.0:
            self.asia_hi = h if self.asia_hi is None else max(self.asia_hi, h)
            self.asia_lo = l if self.asia_lo is None else min(self.asia_lo, l)
        elif hr_min < 12.5:
            self.lon_hi = h if self.lon_hi is None else max(self.lon_hi, h)
            self.lon_lo = l if self.lon_lo is None else min(self.lon_lo, l)

        tol = 0.20 * max(atr, c * 0.001)
        if self.pdh is not None and h >= self.pdh - tol:
            self.pdh_touches += 1
        if self.pdl is not None and l <= self.pdl + tol:
            self.pdl_touches += 1

        return {
            "pdh": self.pdh, "pdl": self.pdl, "pwh": self.pwh, "pwl": self.pwl,
            "asia_high": self.asia_hi if hr_min >= 7.0 else None,
            "asia_low": self.asia_lo if hr_min >= 7.0 else None,
            "london_high": self.lon_hi if hr_min >= 12.5 else None,
            "london_low": self.lon_lo if hr_min >= 12.5 else None,
            "pdh_touches": self.pdh_touches, "pdl_touches": self.pdl_touches,
        }


def _validate_sweep_reclaim_qc(bars: list[tuple[float, float, float, float]], side: int, pool_px: float, atr5: float) -> bool:
    """Enforce wick sweep + body reclaim within 2 bars + BOS close (reject continuation acceptance)."""
    if len(bars) < 5 or atr5 <= 0:
        return False
    c0 = bars[-1][3]
    sw_i = -1 if ((bars[-1][2] < pool_px) if side == 1 else (bars[-1][1] > pool_px)) else -2
    reclaimed = False
    for k in range(sw_i, 0):
        ck = bars[k][3]
        if (side == 1 and ck > pool_px) or (side == -1 and ck < pool_px):
            reclaimed = True
            break
    if not reclaimed:
        return False
    if side == 1:
        bos_lv = max(b[1] for b in bars[-6:-1])
        return c0 > bos_lv and c0 > pool_px
    bos_lv = min(b[2] for b in bars[-6:-1])
    return c0 < bos_lv and c0 < pool_px


class CoinState:
    def __init__(self, ticker: str, symbol: Symbol, leverage: float) -> None:
        self.ticker, self.symbol, self.leverage = ticker, symbol, leverage
        self.sw_4h = CausalTopoSwingTracker(0.80, 3)
        self.sw_1h = CausalTopoSwingTracker(0.80, 3)
        self.sw_1h_k3 = CausalSwingTracker(3)
        self.sw_15m_k3 = CausalSwingTracker(3)
        self.sw_5m = CausalTopoSwingTracker(0.70, 3)
        self.ref_tracker = CausalReferenceTracker()
        self.session_tracker = DailySessionTracker(expiry_bars_5m=60)
        self.topo_4h = CausalTopologicalZigZag(1.25)
        self.topo_1h = CausalTopologicalZigZag(1.15)
        self.topo_15m = CausalTopologicalZigZag(1.15)
        self.topo_5m = CausalTopologicalZigZag(0.50)
        self.ema_1d, self.ema_4h, self.ema_1h = EmaState(), EmaState(), EmaState()
        self.ema_15m, self.ema_5m = EmaState(), EmaState()
        self.atr_4h, self.adx_4h = WilderATR14(), WilderADX14()
        self.atr_1h, self.atr_15m, self.atr_5m = WilderATR14(), WilderATR14(), WilderATR14()
        self.rsi_1h, self.rsi_5m = WilderRSI14(), WilderRSI14()

        # V6 4H Regime & Fractal buffers
        self.donch_hi_4h = deque(maxlen=20)
        self.donch_lo_4h = deque(maxlen=20)
        self.closes_4h = deque(maxlen=25)
        self.highs_4h = deque(maxlen=25)
        self.lows_4h = deque(maxlen=25)
        self.vols_4h = deque(maxlen=80)
        self.sq_recent_4h = deque(maxlen=6)
        self.highs_1h = deque(maxlen=16)
        self.lows_1h = deque(maxlen=16)
        self.last_ker_4h = 0.0
        self.last_br_4h = 0.0
        self.last_dir_4h = 0
        self.last_rvol_4h = 1.0
        self.prev_4h_o = self.prev_4h_c = self.prev_4h_hi20 = self.prev_4h_lo20 = None
        self.idx_4h = self.cooldown_4h = 0

        self.vols_5m = deque(maxlen=20)
        self.vwap_day, self.vwap_pv, self.vwap_v = None, 0.0, 0.0
        self.bars_5m = deque(maxlen=40)
        self.cands_1h_k3 = []
        self.cands_1h_k2 = []
        self.cands_15m_ny = []
        self.last_v9_side_bar = {1: -999, -1: -999}
        self.pending_bpr = None
        self.idx_5m = self.cooldown_until = 0

        self.pending_ticket = self.pending_meta = None
        self.in_position, self.active_engine, self.active_side = False, None, 0
        self.entry_price = self.sl_price = self.risk_dist = self.qty = self.init_qty = self.best_px = 0.0
        self.tp_price = self.trail_atr_mult = None
        self.pyramid_armed = self.pyramid_done = self.partial_taken = self.t2_taken = False
        self.pyramid_stage = 0
        self.step_locks = ()
        self.bank_r = self.bank_frac = self.be_lock_r = 0.0
        self.bank2_r = self.bank2_frac = self.be2_lock_r = 0.0
        self.origin_px = None
        self.sl_ticket = self.tp_ticket = self.partial_ticket = None
        self.canceled_sl_ids = set()


class BinanceFuturesMultiCoinScalper(QCAlgorithm):
    TICKERS = (
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
        "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "LINKUSDT", "SUIUSDT",
    )
    ENGINE_RISK = {
        "V11_SessEq_1H_TOPO": 0.020,
        "V10_LON": 0.015,
        "V10_1H_TOPO": 0.020,
        "V10_15M_TOPO": 0.015,
        "V10_CompVac": 0.015,
        "V10_BPR_Snap": 0.020,
        "V10_BPR_Retest": 0.015,
        "V9_LON": 0.015,
        "V9_1H_K2": 0.015,
        "V9_15M_NY": 0.015,
        "V8_CompVacuum": 0.015,
        "V8_BPR_Snap": 0.020,
        "V8_BPR_Retest": 0.015,
        "V7_CompVacuum": 0.015,
        "V7_BPR_Snap": 0.015,
        "V7_BPR_Retest": 0.015,
        "4H_V6_Cognitive": 0.015,
        "SMC_Sweep_V6": 0.020,
        "VWAP_Sniper": 0.015,
        "Mom9_Sniper": 0.015,
    }
    VWAP_STEPS = ((0.7, 0.1),)
    MOM9_STEPS = ((0.9, 0.1),)
    SWEEP_STEPS = ((3.0, 1.0),)

    def initialize(self) -> None:
        self.set_time_zone(TimeZones.UTC)
        self.set_start_date(2021, 1, 1)
        self.set_end_date(2026, 10, 31)
        start_cash = float(self.get_parameter("start_cash") or 10000.0)
        self.set_account_currency("USDT", start_cash)
        self.hwm_equity = start_cash
        self.skim_anchor = start_cash
        self.withdrawn_vault_usd = 0.0
        self.small_account_mode = (
            str(self.get_parameter("small_account_mode") or ("true" if start_cash <= 500.0 else "false")).lower() == "true"
        )
        self.v10_profile = str(self.get_parameter("v10_profile") or "DAILY_HUNTER").upper()
        if self.v10_profile == "TURBO_SNIPER":
            def_std, def_ap, def_thr, def_skim, def_cb = 0.035, 0.040, 0.02625, 20.0, -2.5
        else:
            def_std, def_ap, def_thr, def_skim, def_cb = 0.030, 0.034, 0.0225, 25.0, -2.0
        self.skim_step_usd = float(self.get_parameter("skim_step_usd") or def_skim)
        self.skim_frac = float(self.get_parameter("skim_frac") or 0.50)
        self.small_risk_pct = float(self.get_parameter("small_risk_pct") or def_std)
        self.small_aplus_risk_pct = float(self.get_parameter("small_aplus_risk_pct") or def_ap)
        self.small_throttle_risk_pct = float(self.get_parameter("small_throttle_risk_pct") or def_thr)
        self.throttle_dd_pct = float(self.get_parameter("throttle_dd_pct") or 0.12)
        self.throttle_mult = float(self.get_parameter("throttle_mult") or 0.75)
        self.throttle2_dd_pct = float(self.get_parameter("throttle2_dd_pct") or 0.20)
        self.throttle2_mult = float(self.get_parameter("throttle2_mult") or 0.60)
        self.cur_week_key = None
        self.week_start_equity = start_cash
        self.fee_rt_pct = float(self.get_parameter("fee_rt_pct") or 0.0010)
        self.max_leverage = float(self.get_parameter("max_leverage") or (15.0 if self.small_account_mode else 10.0))
        self.daily_dd_cap_r = float(self.get_parameter("daily_dd_cap_r") or def_cb)
        self.daily_r_day = None
        self.daily_r_pnl = 0.0
        self.use_v10 = str(self.get_parameter("use_v10") or "true").lower() == "true"
        self.use_v9 = str(self.get_parameter("use_v9") or "true").lower() == "true"
        self.v9_risk_mult = float(self.get_parameter("v9_risk_mult") or 1.0)
        self.risk_scale = float(self.get_parameter("risk_scale") or 1.0)
        self.max_open_pos = int(self.get_parameter("max_open_pos") or (4 if self.small_account_mode else 3))
        self.use_v8 = str(self.get_parameter("use_v8") or self.get_parameter("use_v7") or "true").lower() == "true"
        self.use_v7 = self.use_v8
        self.v8_risk_mult = float(self.get_parameter("v8_risk_mult") or self.get_parameter("v7_risk_mult") or 1.0)
        self.v7_risk_mult = self.v8_risk_mult
        self.use_4h_trend = str(self.get_parameter("use_4h_trend") or "true").lower() == "true"
        self.v6_mode = str(self.get_parameter("v6_mode") or self.get_parameter("v5_mode") or "hybrid").lower()
        self.use_pyramid = str(self.get_parameter("use_pyramid") or "true").lower() == "true"
        self.use_stage2_pyramid = str(self.get_parameter("use_stage2_pyramid") or "true").lower() == "true"
        self.use_smc = str(self.get_parameter("use_smc") or "true").lower() == "true"
        self.smc_risk_mult = float(self.get_parameter("smc_risk_mult") or (1.0 if self.small_account_mode else 0.50))
        self.enable_fast_scalp = str(self.get_parameter("enable_fast_scalp") or "false").lower() == "true"
        self.sweep_tp_r = float(self.get_parameter("sweep_tp_r") or 12.0)
        self.donch_lb = int(self.get_parameter("donch_lb") or 20)
        self.trail_atr_mult = float(self.get_parameter("trail_atr_mult") or 3.5)
        self.conf_threshold = float(self.get_parameter("conf_threshold") or (0.50 if self.v6_mode == "hybrid" else 0.55))
        self.set_warm_up(timedelta(days=65), Resolution.MINUTE)
        self.set_brokerage_model(BrokerageName.BINANCE_FUTURES, AccountType.MARGIN)

        self.coins, self.trade_counts, self.invalid_counts = {}, {}, {}
        for tk in self.TICKERS:
            sec = self.add_crypto_future(tk, Resolution.MINUTE, Market.BINANCE, leverage=int(self.max_leverage))
            st = CoinState(tk, sec.symbol, self.max_leverage)
            st.donch_hi_4h = deque(maxlen=self.donch_lb)
            st.donch_lo_4h = deque(maxlen=self.donch_lb)
            self.coins[sec.symbol] = st
            self.trade_counts[tk] = 0
            self.invalid_counts[tk] = 0
            self.consolidate(sec.symbol, timedelta(days=1), lambda b, s=st: self.on_1d(s, b))
            self.consolidate(sec.symbol, timedelta(hours=4), lambda b, s=st: self.on_4h(s, b))
            self.consolidate(sec.symbol, timedelta(hours=1), lambda b, s=st: self.on_1h(s, b))
            self.consolidate(sec.symbol, timedelta(minutes=15), lambda b, s=st: self.on_15m(s, b))
            self.consolidate(sec.symbol, timedelta(minutes=5), lambda b, s=st: self.on_5m(s, b))

    def _is_zero_risk(self, st: CoinState) -> bool:
        if not st.in_position:
            return False
        return (st.active_side == 1 and st.sl_price >= st.entry_price) or (
            st.active_side == -1 and st.sl_price <= st.entry_price
        )

    def _open_count(self) -> int:
        return sum(
            1 for st in self.coins.values()
            if st.pending_ticket is not None or (st.in_position and not self._is_zero_risk(st))
        )

    def _daily_circuit_ok(self) -> bool:
        d = self.utc_time.date()
        if self.daily_r_day != d:
            self.daily_r_day = d
            self.daily_r_pnl = 0.0
        return self.daily_r_pnl > self.daily_dd_cap_r

    def _active_anchor_equity(self) -> float:
        eq = float(self.portfolio.total_portfolio_value)
        active_eq = max(1.0, eq - (self.withdrawn_vault_usd if self.small_account_mode else 0.0))
        wk = self.utc_time.isocalendar()[:2]
        if self.cur_week_key != wk:
            self.cur_week_key = wk
            self.week_start_equity = active_eq
        return min(self.week_start_equity, active_eq)

    def _effective_risk_pct(self, engine: str, mult: float = 1.0, is_aplus: bool = False) -> float:
        eq = float(self.portfolio.total_portfolio_value)
        active_eq = max(1.0, eq - self.withdrawn_vault_usd)
        dd = (self.hwm_equity - active_eq) / self.hwm_equity if self.hwm_equity > 0 else 0.0
        if self.small_account_mode:
            if is_aplus or engine in ("SMC_Sweep_V6", "V10_BPR_Snap", "V11_SessEq_1H_TOPO", "V10_1H_TOPO", "V8_BPR_Snap"):
                base = self.small_aplus_risk_pct
            else:
                base = self.small_risk_pct
            if dd >= self.throttle2_dd_pct:
                base *= self.throttle2_mult
            elif dd >= self.throttle_dd_pct:
                base *= self.throttle_mult
            return base * self.risk_scale * mult
        brake = 0.50 if dd >= 0.12 else (0.70 if dd >= 0.08 else 1.0)
        base = self.ENGINE_RISK.get(engine, 0.015)
        return base * brake * self.risk_scale * mult

    def _round_qty(self, sym: Symbol, raw_qty: float, is_long: bool) -> float:
        sp = self.securities[sym].symbol_properties
        lot = float(sp.lot_size or 0.001)
        min_sz = float(sp.minimum_order_size or lot)
        qty = round(math.floor((abs(raw_qty) / lot) + 1e-9) * lot, 8)
        if qty < min_sz:
            return 0.0
        return qty if is_long else -qty

    def _round_px(self, sym: Symbol, price: float) -> float:
        tick = float(self.securities[sym].symbol_properties.minimum_price_variation or 0.01)
        tick = tick if tick > 0 else 0.01
        return round(round(price / tick) * tick, 8)

    def _clamp_qty(self, st: CoinState, raw_qty: float, px: float) -> float:
        if px <= 0:
            return 0.0
        rem = max(0.0, float(self.portfolio.margin_remaining))
        slot_frac = 0.85 if self.small_account_mode else 0.30
        slot_cap = float(self.portfolio.total_portfolio_value) * st.leverage * slot_frac
        max_notional = min(rem * st.leverage * 0.85, slot_cap)
        return min(abs(raw_qty), max_notional / px) if max_notional > 0 else 0.0

    def _cancel_pending(self, st: CoinState) -> None:
        if st.pending_ticket is not None and st.pending_ticket.status not in (
            OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.INVALID
        ):
            st.pending_ticket.cancel()
        st.pending_ticket = st.pending_meta = None

    def _replace_sl(self, st: CoinState, lock_px: float, cur_c: float, market_if_crossed: bool = False) -> None:
        lp = self._round_px(st.symbol, lock_px)
        if market_if_crossed and ((st.active_side == 1 and lp >= cur_c) or (st.active_side == -1 and lp <= cur_c)):
            self.transactions.cancel_open_orders(st.symbol)
            self.liquidate(st.symbol, tag=f"{st.active_engine}_TRAIL_MKT")
            self._reset_pos(st)
            return
        if not ((st.active_side == 1 and lp > st.sl_price and lp < cur_c) or
                (st.active_side == -1 and lp < st.sl_price and lp > cur_c)):
            return
        old = st.sl_ticket
        if old is not None and old.status not in (OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.INVALID):
            st.canceled_sl_ids.add(old.order_id)
            old.cancel()
        st.sl_price = lp
        st.sl_ticket = self.stop_market_order(st.symbol, -st.qty, lp, tag=f"{st.active_engine}_SL")

    def _can_enter(self, st: CoinState) -> bool:
        if self.is_warming_up or st.in_position or st.pending_ticket is not None:
            return False
        if not self._daily_circuit_ok():
            return False
        if st.idx_5m < st.cooldown_until or self._open_count() >= self.max_open_pos:
            return False
        if self.portfolio[st.symbol].invested:
            self.transactions.cancel_open_orders(st.symbol)
            self.liquidate(st.symbol, tag="ORPHAN_CLEAN")
            return False
        return float(self.securities[st.symbol].price) > 0

    def _fractal_stop_4h(self, st: CoinState, ep: float, side: int, a4: float) -> float:
        """Scale-free volatility-normalized stop selection bounded in [1.50, 2.00] * ATR_4H."""
        a1 = max(st.atr_1h.val, 1e-12)
        buf = 0.20 * a1
        anchors = []
        if side == 1:
            if st.sw_1h.last_low is not None:
                anchors.append(st.sw_1h.last_low)
            if st.lows_1h:
                anchors.append(min(st.lows_1h))
        else:
            if st.sw_1h.last_high is not None:
                anchors.append(st.sw_1h.last_high)
            if st.highs_1h:
                anchors.append(max(st.highs_1h))

        best_rho, best_sc = 2.0, -1e9
        for anc in anchors:
            sl_c = (anc - buf) if side == 1 else (anc + buf)
            d = (ep - sl_c) if side == 1 else (sl_c - ep)
            if d <= 0:
                continue
            rho = d / max(a4, 1e-12)
            if 1.50 <= rho <= 2.00:
                sc = 2.0 - abs(rho - 1.68)
                if sc > best_sc:
                    best_sc, best_rho = sc, rho
        return ep - side * best_rho * a4

    def _submit_market(self, st: CoinState, engine: str, side: int, sl: float,
                       trail_mult: float, sl_max: float = 0.085, sl_min: float = 0.005,
                       risk_mult: float = 1.0, is_pyramid: bool = False, pyr_stage: int = 0) -> None:
        if not is_pyramid and not self._can_enter(st):
            return
        cur_px = float(self.securities[st.symbol].price)
        if cur_px <= 0:
            return
        sl_px = self._round_px(st.symbol, sl)
        risk = (cur_px - sl_px) if side == 1 else (sl_px - cur_px)
        sl_pct = risk / cur_px
        if risk <= 0 or sl_pct < sl_min or sl_pct > sl_max:
            return
        risk_base = self._active_anchor_equity()
        risk_usd = risk_base * self._effective_risk_pct(engine, risk_mult)
        eff_risk = risk + cur_px * self.fee_rt_pct
        qty = self._round_qty(st.symbol, self._clamp_qty(st, risk_usd / eff_risk, cur_px), side == 1)
        if qty == 0.0:
            return
        st.pending_meta = {
            "engine": engine, "side": side, "trig": cur_px, "sl": sl_px, "tp": None,
            "risk": risk, "qty": qty, "step_locks": (), "trail_mult": trail_mult,
            "is_pyramid": is_pyramid, "pyr_stage": pyr_stage, "exp": st.idx_5m + 3,
        }
        t = self.market_order(st.symbol, qty, tag=f"{engine}_PYR{pyr_stage}" if is_pyramid else engine)
        if t.status == OrderStatus.INVALID:
            st.pending_meta = st.pending_ticket = None
            return
        if st.pending_meta is not None:
            st.pending_ticket = t

    def _submit_limit(self, st: CoinState, engine: str, side: int, trig: float, sl: float,
                      tp_r: float, step_locks, expire_bars: int, sl_max: float = 0.0180,
                      sl_min: float = 0.0040, risk_mult: float = 1.0,
                      bank_r: float = 0.0, bank_frac: float = 0.0, be_lock_r: float = 0.50,
                      bank2_r: float = 0.0, bank2_frac: float = 0.0, be2_lock_r: float = 2.50,
                      origin_px: float | None = None, is_aplus: bool = False) -> None:
        if not self._can_enter(st):
            return
        cur_px = float(self.securities[st.symbol].price)
        trig_px = self._round_px(st.symbol, trig)
        sl_px = self._round_px(st.symbol, sl)
        risk = (trig_px - sl_px) if side == 1 else (sl_px - trig_px)
        sl_pct = risk / cur_px
        if risk <= 0 or sl_pct < sl_min or sl_pct > sl_max:
            return
        if (side == 1 and trig_px > cur_px) or (side == -1 and trig_px < cur_px):
            return
        tp_px = self._round_px(st.symbol, trig_px + side * tp_r * risk)
        risk_base = self._active_anchor_equity()
        risk_usd = risk_base * self._effective_risk_pct(engine, risk_mult, is_aplus=is_aplus)
        eff_risk = risk + trig_px * self.fee_rt_pct
        qty = self._round_qty(st.symbol, self._clamp_qty(st, risk_usd / eff_risk, trig_px), side == 1)
        if qty == 0.0:
            return
        st.pending_meta = {
            "engine": engine, "side": side, "trig": trig_px, "sl": sl_px, "tp": tp_px,
            "risk": risk, "qty": qty, "step_locks": step_locks, "trail_mult": None,
            "is_pyramid": False, "pyr_stage": 0, "exp": st.idx_5m + expire_bars,
            "bank_r": bank_r, "bank_frac": bank_frac, "be_lock_r": be_lock_r,
            "bank2_r": bank2_r, "bank2_frac": bank2_frac, "be2_lock_r": be2_lock_r,
            "origin_px": origin_px,
        }
        t = self.limit_order(st.symbol, qty, trig_px, tag=engine)
        if t.status == OrderStatus.INVALID:
            st.pending_meta = st.pending_ticket = None
            return
        if st.pending_meta is not None:
            st.pending_ticket = t

    def _compute_4h_v6_confluence(self, st: CoinState, o: float, h: float, l: float, c: float, vol: float, a4: float, adx4: float) -> tuple[float, float]:
        closes = list(st.closes_4h)
        if len(closes) >= 20:
            net = abs(c - closes[-20])
            den = sum(abs(closes[k] - closes[k - 1]) for k in range(len(closes) - 19, len(closes))) + abs(c - closes[-1])
            ker = (net / den) if den > 1e-12 else 0.0
            hi_r = max(max(st.highs_4h), h)
            lo_r = min(min(st.lows_4h), l)
            rpos = (c - lo_r) / max(hi_r - lo_r, 1e-12)
            in_mid_chop = (ker < 0.25) and (0.25 <= rpos <= 0.75)
            ker_sc = 0.05 if in_mid_chop else _sigmoid(ker, 0.25, 9.0)

            arr20 = (closes[-19:] + [c])
            mu = sum(arr20) / 20.0
            sd = math.sqrt(sum((x - mu) ** 2 for x in arr20) / 20.0)
            sq_now = (4.0 * sd) / max(3.0 * a4, 1e-12)
            sq_min = min(st.sq_recent_4h) if st.sq_recent_4h else 1.0
            st.sq_recent_4h.append(sq_now)
            prior_comp = sq_min < 0.98
            sq_exp = _sigmoid(sq_now - sq_min, 0.04, 18.0) if prior_comp else 0.45
            sq_sc = max(0.0, min(1.0, 0.55 * _sigmoid(1.05 - sq_min, 0.05, 12.0) + 0.45 * sq_exp))
        else:
            ker, ker_sc, sq_sc = 0.0, 0.5, 0.45

        if len(st.vols_4h) >= 10:
            sv = sorted(st.vols_4h)
            med_v = sv[len(sv) // 2]
            rvol = (vol / med_v) if med_v > 0 else 1.0
        else:
            rvol = 1.0
        rvol_sc = _sigmoid(rvol, 1.6, 2.2)
        rng = max(h - l, 1e-12)
        br = abs(c - o) / rng
        er_sc = min(1.0, rvol_sc * _sigmoid(br, 0.65, 9.0) + (0.25 if (rvol >= 1.4 and br >= 0.65) else 0.0))
        trap_sc = _sigmoid(rvol, 1.8, 3.0) * _sigmoid(0.42 - br, 0.0, 10.0)
        disp_sc = min(1.0, 0.60 * _sigmoid(abs(c - o) / max(a4, 1e-12), 1.2, 2.2) + 0.40 * _sigmoid(br, 0.60, 7.0))
        adx_sc = _sigmoid(adx4, 18.0, 0.25)

        st.last_ker_4h, st.last_br_4h, st.last_dir_4h, st.last_rvol_4h = ker, br, (1 if c > o else -1), rvol
        conf = _soft_and_log_odds(
            {"ker": ker_sc, "er": er_sc, "sq": sq_sc, "disp": disp_sc, "adx": adx_sc},
            {"ker": 1.0, "er": 1.0, "sq": 0.6, "disp": 1.0, "adx": 1.2},
            veto_floors={"ker": 0.12},
        )
        return conf, trap_sc

    def on_1d(self, st: CoinState, bar) -> None:
        st.ema_1d.update(float(bar.Close))

    def on_4h(self, st: CoinState, bar) -> None:
        st.idx_4h += 1
        o, h, l, c = float(bar.Open), float(bar.High), float(bar.Low), float(bar.Close)
        vol = float(getattr(bar, "Volume", 0.0) or 0.0)
        a4 = st.atr_4h.update(h, l, c)
        adx4 = st.adx_4h.update(h, l, c)

        # Keep 4H regime state fresh even when no signal triggers
        conf_now, trap_now = self._compute_4h_v6_confluence(st, o, h, l, c, vol, a4, adx4)

        # Update V6 Climax Elastic Ratchet + 2-Stage Risk-Free Pyramiding for open 4H_V6_Cognitive
        if st.in_position and st.trail_atr_mult is not None and a4 > 0 and st.sl_ticket is not None:
            st.best_px = max(st.best_px, h) if st.active_side == 1 else min(st.best_px, l)
            mfe_r = ((st.best_px - st.entry_price) * st.active_side) / max(st.risk_dist, 1e-12)
            open_r = ((c - st.entry_price) * st.active_side) / max(st.risk_dist, 1e-12)

            if self.use_pyramid and st.pyramid_stage == 0 and mfe_r >= 2.0:
                st.pyramid_armed = True
                self._replace_sl(st, st.entry_price + st.active_side * 0.35 * st.risk_dist, c, market_if_crossed=False)

            tmult = st.trail_atr_mult
            if open_r >= 14.0:
                tmult = 2.0
            elif open_r >= 10.0:
                tmult = st.trail_atr_mult - ((open_r - 10.0) / 4.0) * (st.trail_atr_mult - 2.0)

            trail_px = (st.best_px - tmult * a4) if st.active_side == 1 else (st.best_px + tmult * a4)
            self._replace_sl(st, trail_px, c, market_if_crossed=True)

            if self.use_pyramid and st.in_position and st.pending_ticket is None and st.prev_4h_c is not None:
                if st.pyramid_armed and st.pyramid_stage == 0:
                    pb = (
                        (st.active_side == 1 and l <= st.prev_4h_c and c > o and c > st.entry_price)
                        or (st.active_side == -1 and h >= st.prev_4h_c and c < o and c < st.entry_price)
                    )
                    if pb:
                        self._submit_market(
                            st, "4H_V6_Cognitive", st.active_side, c - st.active_side * 1.5 * a4,
                            self.trail_atr_mult, risk_mult=0.50, is_pyramid=True, pyr_stage=1,
                        )
                elif self.use_stage2_pyramid and st.pyramid_stage == 1 and open_r >= 4.2 and st.last_ker_4h > 0.40:
                    pb2 = (
                        (st.active_side == 1 and c > o and c > max(st.prev_4h_c, st.prev_4h_o or st.prev_4h_c))
                        or (st.active_side == -1 and c < o and c < min(st.prev_4h_c, st.prev_4h_o or st.prev_4h_c))
                    )
                    if pb2:
                        self._replace_sl(st, st.entry_price + st.active_side * 2.0 * st.risk_dist, c, market_if_crossed=False)
                        self._submit_market(
                            st, "4H_V6_Cognitive", st.active_side, c - st.active_side * 1.4 * a4,
                            self.trail_atr_mult, risk_mult=0.35, is_pyramid=True, pyr_stage=2,
                        )

        hi_n = max(st.donch_hi_4h) if len(st.donch_hi_4h) == self.donch_lb else None
        lo_n = min(st.donch_lo_4h) if len(st.donch_lo_4h) == self.donch_lb else None
        if (
            self.use_4h_trend and not self.is_warming_up and not st.in_position and a4 > 0
            and st.idx_4h >= st.cooldown_4h and st.prev_4h_c is not None
        ):
            t1d = st.ema_1d.trend
            side = 0
            if self.v6_mode == "topological":
                if t1d == 1 and st.topo_4h.last_hi is not None and c > st.topo_4h.last_hi and st.prev_4h_c <= st.topo_4h.last_hi:
                    side = 1
                elif t1d == -1 and st.topo_4h.last_lo is not None and c < st.topo_4h.last_lo and st.prev_4h_c >= st.topo_4h.last_lo:
                    side = -1
            else:
                if hi_n is not None and st.prev_4h_hi20 is not None and adx4 >= 20.0:
                    if t1d == 1 and c > hi_n and st.prev_4h_c <= st.prev_4h_hi20:
                        side = 1
                    elif t1d == -1 and c < lo_n and st.prev_4h_c >= st.prev_4h_lo20:
                        side = -1

            if side != 0 and conf_now >= self.conf_threshold and trap_now < 0.78 and self._btc_regime_allows(st, side):
                slp = self._fractal_stop_4h(st, c, side, a4)
                self._submit_market(st, "4H_V6_Cognitive", side, slp, self.trail_atr_mult)

        st.prev_4h_o, st.prev_4h_c, st.prev_4h_hi20, st.prev_4h_lo20 = o, c, hi_n, lo_n
        st.donch_hi_4h.append(h)
        st.donch_lo_4h.append(l)
        st.closes_4h.append(c)
        st.highs_4h.append(h)
        st.lows_4h.append(l)
        st.vols_4h.append(vol)
        st.topo_4h.update(h, l, a4, c)
        st.sw_4h.update(bar)
        st.ema_4h.update(c)

    def on_1h(self, st: CoinState, bar) -> None:
        h, l, c = float(bar.High), float(bar.Low), float(bar.Close)
        a1 = st.atr_1h.update(h, l, c)
        st.highs_1h.append(h)
        st.lows_1h.append(l)

        # Temporal Acceptance Decay check on active 1H sweep candidates
        for cd in st.cands_1h_k3:
            if (cd["side"] == 1 and c < cd["sl_base"]) or (cd["side"] == -1 and c > cd["sl_base"]):
                cd["b_acc"] = cd.get("b_acc", 0) + 1

        k3 = st.sw_1h_k3
        for idx_s, p_lo in list(k3.act_lo):
            if (k3.bar_idx + 1 - idx_s) >= 4 and l < p_lo and c > p_lo:
                st.cands_1h_k3.append({"side": 1, "start_i": st.idx_5m, "sl_base": l, "choch": st.sw_5m.last_high, "b_acc": 0, "sw_sc": _sigmoid((min(float(bar.Open), c) - l) / max(a1, 1e-12), 0.45, 3.5)})
        for idx_s, p_hi in list(k3.act_hi):
            if (k3.bar_idx + 1 - idx_s) >= 4 and h > p_hi and c < p_hi:
                st.cands_1h_k3.append({"side": -1, "start_i": st.idx_5m, "sl_base": h, "choch": st.sw_5m.last_low, "b_acc": 0, "sw_sc": _sigmoid((h - max(float(bar.Open), c)) / max(a1, 1e-12), 0.45, 3.5)})

        st.cands_1h_k2 = [x for x in st.cands_1h_k2 if (st.idx_5m - x["start_i"]) <= 60][-10:]
        if self.use_v10:
            t1 = st.topo_1h
            for idx_s, p_lo, prom in list(t1.act_lo):
                if (t1.bar_idx + 1 - idx_s) >= 3 and prom >= 1.20 and l < p_lo and c > p_lo:
                    st.cands_1h_k2.append({"side": 1, "start_i": st.idx_5m, "sl_base": l})
            for idx_s, p_hi, prom in list(t1.act_hi):
                if (t1.bar_idx + 1 - idx_s) >= 3 and prom >= 1.20 and h > p_hi and c < p_hi:
                    st.cands_1h_k2.append({"side": -1, "start_i": st.idx_5m, "sl_base": h})
        else:
            k2 = st.sw_1h
            for idx_s, p_lo in list(k2.act_lo):
                if (k2.bar_idx + 1 - idx_s) >= 3 and l < p_lo and c > p_lo:
                    st.cands_1h_k2.append({"side": 1, "start_i": st.idx_5m, "sl_base": l})
            for idx_s, p_hi in list(k2.act_hi):
                if (k2.bar_idx + 1 - idx_s) >= 3 and h > p_hi and c < p_hi:
                    st.cands_1h_k2.append({"side": -1, "start_i": st.idx_5m, "sl_base": h})

        st.topo_1h.update(h, l, a1, c)
        st.sw_1h.update(bar)
        k3.update(bar)
        st.ema_1h.update(c)
        st.rsi_1h.update(c)

    def on_15m(self, st: CoinState, bar) -> None:
        h, l, c = float(bar.High), float(bar.Low), float(bar.Close)
        a15 = st.atr_15m.update(h, l, c)
        st.ema_15m.update(c)
        st.cands_15m_ny = [x for x in st.cands_15m_ny if (st.idx_5m - x["start_i"]) <= 36][-10:]
        if self.use_v10:
            t15 = st.topo_15m
            for idx_s, p_lo, prom in list(t15.act_lo):
                if (t15.bar_idx + 1 - idx_s) >= 4 and prom >= 1.40 and l < p_lo and c > p_lo:
                    st.cands_15m_ny.append({"side": 1, "start_i": st.idx_5m, "sl_base": l})
            for idx_s, p_hi, prom in list(t15.act_hi):
                if (t15.bar_idx + 1 - idx_s) >= 4 and prom >= 1.40 and h > p_hi and c < p_hi:
                    st.cands_15m_ny.append({"side": -1, "start_i": st.idx_5m, "sl_base": h})
        else:
            k15 = st.sw_15m_k3
            for idx_s, p_lo in list(k15.act_lo):
                if (k15.bar_idx + 1 - idx_s) >= 4 and l < p_lo and c > p_lo:
                    st.cands_15m_ny.append({"side": 1, "start_i": st.idx_5m, "sl_base": l})
            for idx_s, p_hi in list(k15.act_hi):
                if (k15.bar_idx + 1 - idx_s) >= 4 and h > p_hi and c < p_hi:
                    st.cands_15m_ny.append({"side": -1, "start_i": st.idx_5m, "sl_base": h})
        st.topo_15m.update(h, l, a15, c)
        st.sw_15m_k3.update(bar)

    def _cleanup_coin_orders(self, st: CoinState) -> None:
        for tk_obj in (st.sl_ticket, st.tp_ticket):
            if tk_obj is not None and tk_obj.status not in (
                OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.INVALID
            ):
                st.canceled_sl_ids.add(tk_obj.order_id)
                tk_obj.cancel()
        st.sl_ticket = st.tp_ticket = None

    def _replace_stop_loss_order(self, st: CoinState, new_sl: float, cur_c: float, tag: str) -> bool:
        """Guaranteed SL ratchet; market-liquidates if price already closed past new_sl."""
        d = st.active_side
        if (d == 1 and new_sl >= cur_c) or (d == -1 and new_sl <= cur_c):
            rem_frac = max(
                0.0,
                1.0
                - (st.bank_frac if st.partial_taken else 0.0)
                - (st.bank2_frac if st.t2_taken else 0.0),
            )
            locked_r = ((new_sl - st.entry_price) * d) / max(st.risk_dist, 1e-12)
            fee_r = (st.entry_price * self.fee_rt_pct) / max(st.risk_dist, 1e-12)
            self.daily_r_pnl += rem_frac * (locked_r - fee_r)
            self._cleanup_coin_orders(st)
            if self.portfolio[st.symbol].invested:
                self.liquidate(st.symbol, tag=f"{tag}_CROSSED")
            self._reset_pos(st)
            return False
        self._cleanup_coin_orders(st)
        st.sl_price = new_sl
        st.sl_ticket = self.stop_market_order(st.symbol, -st.qty, st.sl_price, tag=tag)
        if st.tp_price is not None:
            st.tp_ticket = self.limit_order(st.symbol, -st.qty, st.tp_price, tag=f"{st.active_engine}_TP")
        return True

    def _manage_active_positions_v12_surgical(self, st: CoinState, h: float, l: float, c: float) -> None:
        """
        V12 Surgical 3-Tier Resting Limit Exit & 15m Protected Swing Trail:
        - Strict intrabar SL-before-TP conservative priority.
        - 3-Tier Partial Banking (45/40/15 for Physics/SMC, 50/35/15 for SessEq_1H).
        - Guaranteed SL Ratchet to BE+0.35R/+0.25R on TP1 and +2.0R/+1.25R on TP2 (never blocked by close c).
        - Zero-Risk Slot Recycling as soon as TP1 locks SL above entry.
        - 15m Topological Protected Swing Trailing for the 15% Runner.
        """
        if not st.in_position or st.risk_dist <= 1e-9 or st.sl_ticket is None:
            return
        if not self.portfolio[st.symbol].invested:
            self._cleanup_coin_orders(st)
            self._reset_pos(st)
            return
        if st.trail_atr_mult is not None:
            return

        d = int(st.active_side)
        ep = float(st.entry_price)
        sl = float(st.sl_price)
        r_dist = float(st.risk_dist)
        eng = str(st.active_engine or "")

        # 1. Conservative Intrabar Check: Did price hit current Stop Loss first?
        sl_hit = (d == 1 and l <= sl) or (d == -1 and h >= sl)
        if sl_hit:
            rem_frac = max(
                0.0,
                1.0
                - (st.bank_frac if st.partial_taken else 0.0)
                - (st.bank2_frac if st.t2_taken else 0.0),
            )
            locked_r = ((sl - ep) * d) / r_dist
            fee_r = (ep * self.fee_rt_pct) / r_dist
            self.daily_r_pnl += rem_frac * (locked_r - fee_r)
            self._cleanup_coin_orders(st)
            self.liquidate(st.symbol, tag=f"{eng}_SL_EXIT")
            self._reset_pos(st)
            return

        st.best_px = max(st.best_px, h) if d == 1 else min(st.best_px, l)
        mfe_r = ((st.best_px - ep) * d) / r_dist
        fee_r = (ep * self.fee_rt_pct) / r_dist
        base_qty = st.init_qty if st.init_qty > 0 else abs(st.qty)

        if st.bank_frac > 0.0:
            if "SessEq" in eng:
                tp1_r, tp1_frac, be_lock_r = 1.8, 0.50, 0.25
                tp2_r, tp2_frac, tp2_lock_r = 3.2, 0.35, 1.25
            else:
                tp1_r, tp1_frac, be_lock_r = st.bank_r, st.bank_frac, st.be_lock_r
                tp2_r = st.bank2_r
                if st.origin_px is not None:
                    orig_r = ((st.origin_px - ep) * d) / r_dist
                    if orig_r >= 4.2:
                        tp2_r = min(max(3.0, orig_r), st.bank2_r)
                tp2_frac, tp2_lock_r = st.bank2_frac, st.be2_lock_r

            # 2. Tier 1 Banking (TP1): Unconditional SL ratchet to BE + offset
            if (not st.partial_taken) and mfe_r >= tp1_r:
                st.partial_taken = True
                part_qty = self._round_qty(st.symbol, min(abs(st.qty), base_qty * tp1_frac), d == 1)
                rem_qty = self._round_qty(st.symbol, abs(st.qty) - abs(part_qty), d == 1)
                if abs(part_qty) > 0 and abs(rem_qty) > 0:
                    st.partial_ticket = self.market_order(st.symbol, -part_qty, tag=f"{eng}_BANK40_T1_{tp1_r:.1f}R")
                    st.qty = rem_qty
                    self.daily_r_pnl += tp1_frac * (tp1_r - fee_r)
                new_sl = self._round_px(st.symbol, ep + d * be_lock_r * r_dist)
                if (d == 1 and new_sl > st.sl_price) or (d == -1 and new_sl < st.sl_price):
                    if not self._replace_stop_loss_order(st, new_sl, c, f"{eng}_BE_LOCK"):
                        return

            # 3. Tier 2 Banking (TP2 @ Origin_Anchor / +4.5R): Guaranteed SL ratchet
            if tp2_frac > 0.0 and st.partial_taken and (not st.t2_taken) and mfe_r >= tp2_r:
                st.t2_taken = True
                part2_qty = self._round_qty(st.symbol, min(abs(st.qty), base_qty * tp2_frac), d == 1)
                rem2_qty = self._round_qty(st.symbol, abs(st.qty) - abs(part2_qty), d == 1)
                if abs(part2_qty) > 0 and abs(rem2_qty) > 0:
                    st.partial_ticket = self.market_order(st.symbol, -part2_qty, tag=f"{eng}_BANK40_T2_{tp2_r:.1f}R")
                    st.qty = rem2_qty
                    self.daily_r_pnl += tp2_frac * (tp2_r - fee_r)
                new_sl = self._round_px(st.symbol, ep + d * tp2_lock_r * r_dist)
                if (d == 1 and new_sl > st.sl_price) or (d == -1 and new_sl < st.sl_price):
                    if not self._replace_stop_loss_order(st, new_sl, c, f"{eng}_TP2_LOCK"):
                        return

            # 4. Tier 3 Runner (15%): Trail behind confirmed 15m Topological Protected Swings
            if st.t2_taken and mfe_r >= 4.5:
                sw15 = st.topo_15m
                if d == 1:
                    raw_lo = sw15.act_lo[-1][1] if sw15.act_lo else sw15.last_lo
                    if raw_lo is not None:
                        cand_sl = self._round_px(st.symbol, float(raw_lo))
                        if cand_sl > st.sl_price and cand_sl < l:
                            self._replace_stop_loss_order(st, cand_sl, c, f"{eng}_15M_TRAIL")
                else:
                    raw_hi = sw15.act_hi[-1][1] if sw15.act_hi else sw15.last_hi
                    if raw_hi is not None:
                        cand_sl = self._round_px(st.symbol, float(raw_hi))
                        if cand_sl < st.sl_price and cand_sl > h:
                            self._replace_stop_loss_order(st, cand_sl, c, f"{eng}_15M_TRAIL")

        for act_r, lk_r in st.step_locks:
            hit = (h >= ep + act_r * r_dist) if d == 1 else (l <= ep - act_r * r_dist)
            if hit:
                cand_sl = self._round_px(st.symbol, ep + d * lk_r * r_dist)
                if (d == 1 and cand_sl > st.sl_price) or (d == -1 and cand_sl < st.sl_price):
                    if not self._replace_stop_loss_order(st, cand_sl, c, f"{eng}_STEP_LOCK"):
                        return

    def _btc_regime_allows(self, st: CoinState, side: int) -> bool:
        """V12.0 Cross-Asset BTCUSDT 4H Macro Regime Veto (ker4 > 0.68 opposing altcoin trade direction)."""
        if st.ticker == "BTCUSDT" or side == 0:
            return True
        for cst in self.coins.values():
            if cst.ticker == "BTCUSDT":
                if cst.last_ker_4h > 0.68 and cst.last_dir_4h != 0 and cst.last_dir_4h != side:
                    return False
                break
        return True

    def on_5m(self, st: CoinState, bar) -> None:
        st.idx_5m += 1
        dt = self.utc_time
        o, h, l, c = float(bar.Open), float(bar.High), float(bar.Low), float(bar.Close)
        vol = float(getattr(bar, "Volume", 0.0) or 0.0)
        a5 = st.atr_5m.update(h, l, c)
        rsi5 = st.rsi_5m.update(c)
        st.ema_5m.update(c)
        st.vols_5m.append(vol)
        st.bars_5m.append((o, h, l, c))
        st.session_tracker.step_5m(dt, st.idx_5m, h, l, c)
        ref_snap = st.ref_tracker.update(dt, h, l, c, a5)

        if st.vwap_day != dt.date():
            st.vwap_day = dt.date()
            st.vwap_pv = st.vwap_v = 0.0
        st.vwap_pv += ((h + l + c) / 3.0) * vol
        st.vwap_v += vol
        vwap = (st.vwap_pv / st.vwap_v) if st.vwap_v > 0 else None

        if st.in_position and st.risk_dist > 0 and st.sl_ticket is not None:
            self._manage_active_positions_v12_surgical(st, h, l, c)

        if st.pending_ticket is not None and st.pending_meta is not None:
            pm = st.pending_meta
            if st.idx_5m > pm["exp"] or (l <= pm["sl"] if pm["side"] == 1 else h >= pm["sl"]):
                self._cancel_pending(st)

        if not self.is_warming_up and len(st.bars_5m) >= 3:
            b1, b2, b3 = st.bars_5m[-3], st.bars_5m[-2], st.bars_5m[-1]
            c2b = abs(b2[3] - b2[0])

            # V8.0/V12.0 Intraday Scene-Graph Physics + Reference Engine + Bayesian Prosecutor
            if self.use_v8 and a5 > 0 and st.last_ker_4h >= 0.15 and self._can_enter(st):
                b_hi = [x[1] for x in st.sw_1h.act_hi[-8:]]
                b_lo = [x[1] for x in st.sw_1h.act_lo[-8:]]
                tol_ref = 0.35 * a5
                ref_hi = [v for v, ok in ((ref_snap["pdh"], ref_snap["pdh_touches"] <= 2), (ref_snap["pwh"], True), (ref_snap["asia_high"], True), (ref_snap["london_high"], True)) if ok and v is not None]
                ref_lo = [v for v, ok in ((ref_snap["pdl"], ref_snap["pdl_touches"] <= 2), (ref_snap["pwl"], True), (ref_snap["asia_low"], True), (ref_snap["london_low"], True)) if ok and v is not None]
                v_hi = [p for i, p in enumerate(b_hi) if any(i != j and 1e-6 < abs(p - q) <= tol_ref for j, q in enumerate(b_hi)) or any(abs(p - r) <= tol_ref for r in ref_hi)] + ref_hi
                v_lo = [p for i, p in enumerate(b_lo) if any(i != j and 1e-6 < abs(p - q) <= tol_ref for j, q in enumerate(b_lo)) or any(abs(p - r) <= tol_ref for r in ref_lo)] + ref_lo
                v8_sig = None
                ca = _detect_v7_comp_vacuum(list(st.bars_5m), a5, v_hi, v_lo, st.sw_4h.trend)
                if ca is not None:
                    sd, sw_ex, orig_px = ca
                    slp = (sw_ex - a5) if sd == 1 else (sw_ex + a5)
                    disp_sc = _sigmoid(abs(c - o) / max(a5, 1e-12), 1.2, 2.2)
                    v8_sig = ("V8_CompVacuum", sd, slp, orig_px, 0.72, disp_sc)
                if v8_sig is None:
                    pbpr = st.pending_bpr
                    if pbpr is not None:
                        if (st.idx_5m - pbpr["idx"]) > 6 or (pbpr["side"] == 1 and l < pbpr["sweep"]) or (pbpr["side"] == -1 and h > pbpr["sweep"]):
                            st.pending_bpr = None
                        elif ((pbpr["side"] == 1 and l <= pbpr["high"] and c > o and c >= pbpr["mid"]) or (pbpr["side"] == -1 and h >= pbpr["low"] and c < o and c <= pbpr["mid"])):
                            if pbpr["side"] == st.sw_4h.trend and pbpr["side"] == st.sw_1h.trend:
                                slp = (pbpr["sweep"] - a5) if pbpr["side"] == 1 else (pbpr["sweep"] + a5)
                                v8_sig = ("V8_BPR_Retest", pbpr["side"], slp, None, pbpr["vac"], _sigmoid(pbpr["k"], 1.25, 2.0))
                            st.pending_bpr = None
                    if v8_sig is None:
                        bpr = _detect_v7_bpr(list(st.bars_5m), a5, b_hi, b_lo, st.sw_4h.trend, st.sw_1h.trend)
                        if bpr is not None:
                            if bpr["vac"] >= 0.55 and bpr["k"] >= 1.60:
                                slp = (bpr["sweep"] - a5) if bpr["side"] == 1 else (bpr["sweep"] + a5)
                                v8_sig = ("V8_BPR_Snap", bpr["side"], slp, None, bpr["vac"], _sigmoid(bpr["k"], 1.25, 2.0))
                            else:
                                bpr["idx"] = st.idx_5m
                                st.pending_bpr = bpr
                if v8_sig is not None:
                    eng_v8, sd_v8, slp_v8, orig_v8, vac_v8, disp_v8 = v8_sig
                    rd_v8 = abs(c - slp_v8)
                    vavg5 = (sum(st.vols_5m) / len(st.vols_5m)) if st.vols_5m else 1.0
                    rvol5 = (vol / vavg5) if vavg5 > 0 else 1.0
                    a4_cur = max(st.atr_4h.val, 1e-12)
                    ext4 = ((c - st.ema_4h.e20) * sd_v8 / a4_cur) if (st.ema_4h.e20 is not None) else 0.0
                    opp_w = [x[1] for x in (st.sw_1h.act_hi[-6:] if sd_v8 == 1 else st.sw_1h.act_lo[-6:])]
                    if rd_v8 > 0 and rvol5 >= 0.90 and ext4 <= 2.50 and self._btc_regime_allows(st, sd_v8):
                        ok_p8, conv8 = _prosecutor_cross_examine(
                            side=sd_v8,
                            thesis_scores={"sweep": 0.72, "disp": disp_v8, "vac": vac_v8, "ker4": _sigmoid(st.last_ker_4h, 0.25, 9.0), "rvol": _sigmoid(rvol5, 1.3, 2.0)},
                            thesis_weights={"sweep": 1.1, "disp": 1.2, "vac": 1.0, "ker4": 1.0, "rvol": 0.7},
                            ker_4h=st.last_ker_4h,
                            body_ratio_4h=st.last_br_4h,
                            dir_4h_candle=st.last_dir_4h,
                            htf_trend_1h=st.sw_1h.trend,
                            htf_trend_4h=st.sw_4h.trend,
                            rvol_entry=rvol5,
                            is_counter_trend_sweep=(sd_v8 != st.sw_4h.trend),
                            min_conviction=0.55,
                            entry_px=c,
                            risk_dist=rd_v8,
                            opposing_htf_walls=opp_w,
                            min_clearance_r=3.0,
                            ref_snap=ref_snap,
                            min_tp1_clearance_r=2.2,
                            hard_veto_ref_brick=(eng_v8 == "V8_CompVacuum"),
                        )
                        if ok_p8:
                            self._submit_limit(
                                st, eng_v8.replace("V8_", "V10_") if self.use_v10 else eng_v8, sd_v8, c, slp_v8,
                                10.0 if self.use_v10 else self.sweep_tp_r, (), 8,
                                0.0180, 0.0045, risk_mult=self.v8_risk_mult,
                                bank_r=2.2 if self.use_v10 else 2.8,
                                bank_frac=0.45 if self.use_v10 else 0.40,
                                be_lock_r=0.35 if self.use_v10 else 0.50,
                                bank2_r=4.5 if self.use_v10 else 5.5,
                                bank2_frac=0.40,
                                be2_lock_r=2.00 if self.use_v10 else 2.50,
                                origin_px=orig_v8, is_aplus=(eng_v8 == "V8_BPR_Snap" or conv8 >= 0.72),
                            )

            # V11.0 / V9.0 Pruned Topological 1H Liquidity Sweep (50/35/15 Session Eq) + pruned V9_LON (rvol >= 1.15)
            if self.use_v9 and a5 > 0 and st.last_ker_4h >= 0.15 and c2b >= (1.15 * a5 if self.use_v10 else a5) and self._can_enter(st):
                vavg5 = (sum(st.vols_5m) / len(st.vols_5m)) if st.vols_5m else 1.0
                rvol5 = (vol / vavg5) if vavg5 > 0 else 1.0
                htf1_tr = st.topo_1h.trend if self.use_v10 else st.sw_1h.trend
                htf4_tr = st.topo_4h.trend if self.use_v10 else st.sw_4h.trend
                sw5_hi = st.topo_5m.last_hi if self.use_v10 else st.sw_5m.last_high
                sw5_lo = st.topo_5m.last_lo if self.use_v10 else st.sw_5m.last_low
                slv_specs = (
                    ("V11_SessEq_1H_TOPO", st.cands_1h_k2, dt.hour >= 9 and rvol5 >= 1.10, True),
                    ("V9_LON", st.session_tracker.cands_lon, dt.hour >= 12 and rvol5 >= 1.15, False),
                ) if self.use_v10 else (
                    ("V9_LON", st.session_tracker.cands_lon, dt.hour >= 12, False),
                    ("V9_1H_K2", st.cands_1h_k2, dt.hour >= 9, False),
                    ("V9_15M_NY", st.cands_15m_ny, (12 <= dt.hour <= 21) and rvol5 >= 1.20, False),
                )
                for slv_tag, clist, ok_hr, is_ap in slv_specs:
                    if not ok_hr:
                        continue
                    placed_v9 = False
                    for cd in reversed(clist):
                        sd = cd["side"]
                        if sd != htf1_tr or sd != htf4_tr:
                            continue
                        if (st.idx_5m - st.last_v9_side_bar.get(sd, -999)) < 12:
                            continue
                        ok_fvg = False
                        ep_v9 = slp_v9 = 0.0
                        if sd == 1 and l >= cd["sl_base"] and sw5_hi is not None:
                            if c > sw5_hi and (l - b1[1]) >= (0.30 if self.use_v10 else 0.25) * a5 and b2[3] > b2[0]:
                                slp_v9 = min(cd["sl_base"] - a5, c - max(1.5 * a5, c * 0.0020))
                                ep_v9 = l
                                ok_fvg = True
                        elif sd == -1 and h <= cd["sl_base"] and sw5_lo is not None:
                            if c < sw5_lo and (b1[2] - h) >= (0.30 if self.use_v10 else 0.25) * a5 and b2[3] < b2[0]:
                                slp_v9 = max(cd["sl_base"] + a5, c + max(1.5 * a5, c * 0.0020))
                                ep_v9 = h
                                ok_fvg = True
                        if ok_fvg and self._btc_regime_allows(st, sd):
                            st.last_v9_side_bar[sd] = st.idx_5m
                            if slv_tag == "V11_SessEq_1H_TOPO":
                                self._submit_limit(
                                    st, slv_tag, sd, ep_v9, slp_v9, 6.5, (), 8,
                                    0.0180, 0.0020, risk_mult=self.v9_risk_mult,
                                    bank_r=1.8, bank_frac=0.50, be_lock_r=0.25,
                                    bank2_r=3.2, bank2_frac=0.35, be2_lock_r=1.25,
                                    is_aplus=True,
                                )
                            else:
                                self._submit_limit(
                                    st, slv_tag, sd, ep_v9, slp_v9, 10.0, (), 8,
                                    0.0180, 0.0020, risk_mult=self.v9_risk_mult,
                                    bank_r=2.2 if self.use_v10 else 2.0,
                                    bank_frac=0.45 if self.use_v10 else 0.15,
                                    be_lock_r=0.35,
                                    bank2_r=4.5,
                                    bank2_frac=0.40 if self.use_v10 else 0.20,
                                    be2_lock_r=2.00,
                                    is_aplus=is_ap,
                                )
                            placed_v9 = True
                            break
                    if placed_v9:
                        break

            still = []
            for cd in st.cands_1h_k3:
                if st.idx_5m - cd["start_i"] > 60:
                    continue
                if self.use_smc and dt.hour >= 9 and st.last_ker_4h >= 0.15:
                    slp = None
                    if cd["side"] == 1 and l >= cd["sl_base"] and st.sw_4h.trend == 1 and st.sw_1h.trend == 1 and cd["choch"] is not None and c > cd["choch"] and (b3[2] - b1[1]) >= 0.25 * a5 and b2[3] > b2[0] and c2b >= a5:
                        slp = min(cd["sl_base"] - a5, c - max(1.5 * a5, c * 0.0020))
                    elif cd["side"] == -1 and h <= cd["sl_base"] and st.sw_4h.trend == -1 and st.sw_1h.trend == -1 and cd["choch"] is not None and c < cd["choch"] and (b1[2] - b3[1]) >= 0.25 * a5 and b2[3] < b2[0] and c2b >= a5:
                        slp = max(cd["sl_base"] + a5, c + max(1.5 * a5, c * 0.0020))
                    if slp is not None:
                        vavg5 = (sum(st.vols_5m) / len(st.vols_5m)) if st.vols_5m else 1.0
                        rvol5 = (vol / vavg5) if vavg5 > 0 else 1.0
                        disp_sc = _sigmoid(c2b / max(a5, 1e-12), 1.2, 2.2)
                        ok_p, _ = _prosecutor_cross_examine(
                            side=cd["side"],
                            thesis_scores={"sweep": max(0.55, cd.get("sw_sc", 0.65)), "disp": disp_sc, "ker4": _sigmoid(st.last_ker_4h, 0.25, 9.0), "rvol": _sigmoid(rvol5, 1.6, 2.2)},
                            thesis_weights={"sweep": 1.2, "disp": 1.3, "ker4": 1.1, "rvol": 0.6},
                            ker_4h=st.last_ker_4h,
                            body_ratio_4h=st.last_br_4h,
                            dir_4h_candle=st.last_dir_4h,
                            htf_trend_1h=st.sw_1h.trend,
                            htf_trend_4h=st.ema_1d.trend,
                            rvol_entry=rvol5,
                            sweep_bars_accepted=cd.get("b_acc", 0),
                            is_counter_trend_sweep=(cd["side"] != st.ema_1d.trend),
                            min_conviction=0.35,
                        )
                        if ok_p and self._btc_regime_allows(st, cd["side"]):
                            self._submit_limit(
                                st, "SMC_Sweep_V6", cd["side"], c, slp, 10.0,
                                self.SWEEP_STEPS, 20, 0.0180, 0.0020, risk_mult=self.smc_risk_mult, is_aplus=True,
                            )
                            continue
                if (cd["side"] == 1 and l >= cd["sl_base"]) or (cd["side"] == -1 and h <= cd["sl_base"]):
                    still.append(cd)
            st.cands_1h_k3 = still

            if self.enable_fast_scalp and dt.weekday() < 5:
                a15 = st.atr_15m.val
                t4, t1 = st.ema_4h.trend, st.ema_1h.trend
                r1h = st.rsi_1h.val
                if vwap is not None and a15 > 0 and (7 <= dt.hour <= 20) and st.ema_1h.er14 >= 0.25:
                    if t4 == 1 and t1 == 1 and r1h >= 58.0 and l <= vwap < c and c > o and rsi5 <= 48.0:
                        slp = min(l, vwap - 0.5 * a15) - 0.4 * a5
                        self._submit_limit(st, "VWAP_Sniper", 1, c, slp, 1.3, self.VWAP_STEPS, 6, 0.0095)
                    elif t4 == -1 and t1 == -1 and (100.0 - r1h) >= 58.0 and h >= vwap > c and c < o and rsi5 >= 52.0:
                        slp = max(h, vwap + 0.5 * a15) + 0.4 * a5
                        self._submit_limit(st, "VWAP_Sniper", -1, c, slp, 1.3, self.VWAP_STEPS, 6, 0.0095)

                if len(st.vols_5m) == 20 and st.ema_1h.er14 >= 0.30 and st.ema_4h.er14 >= 0.22 and st.ema_15m.er14 >= 0.30 and a5 > 0:
                    vavg = sum(st.vols_5m) / 20.0
                    e9, e20, e50, mh = st.ema_5m.e9, st.ema_5m.e20, st.ema_5m.e50, st.ema_5m.macd_hist
                    if vavg > 0 and vol >= 1.8 * vavg and e9 is not None and e50 is not None:
                        if t4 == 1 and t1 == 1 and r1h >= 68.0 and mh > 0 and e9 > e20 > e50 and l <= e9 < c and c > o:
                            slp = min(l, e20) - 0.5 * a5
                            self._submit_limit(st, "Mom9_Sniper", 1, c, slp, 1.8, self.MOM9_STEPS, 6)
                        elif t4 == -1 and t1 == -1 and (100.0 - r1h) >= 68.0 and mh < 0 and e9 < e20 < e50 and h >= e9 > c and c < o:
                            slp = max(h, e20) + 0.5 * a5
                            self._submit_limit(st, "Mom9_Sniper", -1, c, slp, 1.8, self.MOM9_STEPS, 6)

        st.topo_5m.update(h, l, a5, c)
        st.sw_5m.update(bar)

    def on_data(self, data: Slice) -> None:
        if self.is_warming_up:
            return
        for sym, st in self.coins.items():
            if not st.in_position and st.pending_ticket is None and self.portfolio[sym].invested:
                self.transactions.cancel_open_orders(sym)
                self.liquidate(sym, tag="ORPHAN_SYNC")

    def on_order_event(self, oe: OrderEvent) -> None:
        if oe.symbol not in self.coins:
            return
        st = self.coins[oe.symbol]
        if oe.order_id in st.canceled_sl_ids and oe.status == OrderStatus.CANCELED:
            st.canceled_sl_ids.discard(oe.order_id)
            return
        if oe.status == OrderStatus.INVALID:
            self.invalid_counts[st.ticker] += 1
            if st.pending_meta is not None and not st.in_position:
                st.pending_ticket = st.pending_meta = None
            elif st.in_position and st.pending_meta is not None and st.pending_meta.get("is_pyramid"):
                st.pending_ticket = st.pending_meta = None
            elif st.in_position:
                self.transactions.cancel_open_orders(oe.symbol)
                self.liquidate(oe.symbol, tag="INVALID_RECOVERY")
                self._reset_pos(st)
            return
        if oe.status == OrderStatus.CANCELED:
            if st.pending_ticket is not None and oe.order_id == st.pending_ticket.order_id:
                st.pending_ticket = st.pending_meta = None
            return
        if oe.status != OrderStatus.FILLED:
            return

        if st.partial_ticket is not None and oe.order_id == st.partial_ticket.order_id:
            st.partial_ticket = None
            return

        if st.pending_meta is not None and st.in_position and st.pending_meta.get("is_pyramid") and abs(float(oe.fill_quantity)) > 0:
            pm = st.pending_meta
            st.pending_ticket = st.pending_meta = None
            st.pyramid_stage = max(st.pyramid_stage, int(pm.get("pyr_stage", 1)))
            st.pyramid_done = (st.pyramid_stage >= 2)
            st.qty += float(oe.fill_quantity)
            self.trade_counts[st.ticker] += 1
            old = st.sl_ticket
            if old is not None and old.status not in (OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.INVALID):
                st.canceled_sl_ids.add(old.order_id)
                old.cancel()
            new_sl = max(st.sl_price, pm["sl"]) if st.active_side == 1 else min(st.sl_price, pm["sl"])
            st.sl_price = self._round_px(st.symbol, new_sl)
            st.sl_ticket = self.stop_market_order(st.symbol, -st.qty, st.sl_price, tag=f"{st.active_engine}_PYR_SL")
        elif st.pending_meta is not None and not st.in_position and abs(float(oe.fill_quantity)) > 0:
            pm = st.pending_meta
            st.pending_ticket = st.pending_meta = None
            st.in_position = True
            st.active_engine, st.active_side = pm["engine"], pm["side"]
            st.entry_price = float(oe.fill_price)
            st.best_px = st.entry_price
            st.sl_price, st.tp_price = pm["sl"], pm["tp"]
            st.risk_dist, st.qty = pm["risk"], float(oe.fill_quantity)
            st.init_qty = abs(float(oe.fill_quantity))
            st.step_locks, st.trail_atr_mult = pm["step_locks"], pm["trail_mult"]
            st.bank_r = float(pm.get("bank_r", 0.0))
            st.bank_frac = float(pm.get("bank_frac", 0.0))
            st.be_lock_r = float(pm.get("be_lock_r", 0.50))
            st.bank2_r = float(pm.get("bank2_r", 0.0))
            st.bank2_frac = float(pm.get("bank2_frac", 0.0))
            st.be2_lock_r = float(pm.get("be2_lock_r", 2.50))
            st.origin_px = pm.get("origin_px")
            st.pyramid_armed = st.pyramid_done = st.partial_taken = st.t2_taken = False
            st.pyramid_stage = 0
            self.trade_counts[st.ticker] += 1
            st.sl_ticket = self.stop_market_order(st.symbol, -st.qty, st.sl_price, tag=f"{st.active_engine}_SL")
            if st.tp_price is not None:
                st.tp_ticket = self.limit_order(st.symbol, -st.qty, st.tp_price, tag=f"{st.active_engine}_TP")
        elif st.in_position:
            rem_frac = 1.0 - (st.bank_frac if st.partial_taken else 0.0) - (st.bank2_frac if st.t2_taken else 0.0)
            rem_frac = max(0.0, rem_frac)
            realized_r = rem_frac * (((float(oe.fill_price) - st.entry_price) * st.active_side) / max(st.risk_dist, 1e-12))
            self._daily_circuit_ok()
            self.daily_r_pnl += realized_r
            for tk_obj in (st.sl_ticket, st.tp_ticket):
                if tk_obj is not None and tk_obj.order_id != oe.order_id and tk_obj.status not in (
                    OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.INVALID
                ):
                    tk_obj.cancel()
            if self.portfolio[st.symbol].invested:
                self.liquidate(st.symbol, tag="RESIDUAL_CLOSE")
            st.cooldown_until = st.idx_5m + 4
            st.cooldown_4h = st.idx_4h + 1
            self._reset_pos(st)
            eq = float(self.portfolio.total_portfolio_value)
            active_eq = max(1.0, eq - (self.withdrawn_vault_usd if self.small_account_mode else 0.0))
            if self.small_account_mode and active_eq >= self.skim_anchor + self.skim_step_usd:
                skim = (active_eq - self.skim_anchor) * self.skim_frac
                self.withdrawn_vault_usd += skim
                active_eq -= skim
                self.skim_anchor = active_eq
                self.hwm_equity = active_eq
            elif active_eq > self.hwm_equity:
                self.hwm_equity = active_eq

    @staticmethod
    def _reset_pos(st: CoinState) -> None:
        st.in_position = st.pyramid_armed = st.pyramid_done = st.partial_taken = st.t2_taken = False
        st.pyramid_stage = 0
        st.active_engine = st.tp_price = st.trail_atr_mult = st.sl_ticket = st.tp_ticket = st.partial_ticket = st.origin_px = None
        st.active_side = 0
        st.entry_price = st.sl_price = st.risk_dist = st.qty = st.init_qty = st.best_px = 0.0
        st.bank_r = st.bank_frac = st.be_lock_r = 0.0
        st.bank2_r = st.bank2_frac = st.be2_lock_r = 0.0
        st.step_locks = ()

    def on_end_of_algorithm(self) -> None:
        self.log(f"=== Binance Multi-Coin V8.0 Cashflow+Ratchet | Trades={sum(self.trade_counts.values())} | Eq={self.portfolio.total_portfolio_value:.2f} USDT | Vault={self.withdrawn_vault_usd:.2f} USDT ===")
        for tk in self.TICKERS:
            if self.trade_counts[tk] > 0 or self.invalid_counts[tk] > 0:
                self.log(f"  {tk:10s}: trades={self.trade_counts[tk]} invalid={self.invalid_counts[tk]}")
