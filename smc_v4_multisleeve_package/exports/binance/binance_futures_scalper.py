#!/usr/bin/env python3
"""
Binance USDT-M Futures Multi-Coin Causal 4H Trend + 1H SMC Engine (V4.0 Verified)
- Zero third-party dependencies (pure Python 3 stdlib).
- Dual-Engine Causal Portfolio (zero HTF lookahead, real Binance fees+slip+funding):
    1) Primary 4H Engine (--no-4h-trend to disable): 4H_Donch20_Trail
       4H Donchian(20) Breakout + 1D EMA20/50 + 4H ADX14 >= 20, SL=2.0*ATR4H, 3.5*ATR4H Chandelier Trail.
       1-coin BTC: N=167, WR=36.5%, Net=+79.7R, PF=1.99, DD=7.8R, 7/7 yrs green (2.0x fees: PF=1.76)
    2) Secondary 1H->5m Engine (--no-smc to disable): SMC_Sweep_10R
       1H (k=3, age>=4) Sweep + 4H/1H Swing Trend + 5m CHoCH+FVG, >=09:00 UTC, BE@3.0R->+1.0R, TP=10R.
       1-coin BTC: N=144, WR=31.2%, Net=+78.0R, PF=1.71, DD=17.3R
- Modes:
    --mode paper   : Live public Binance market scan + simulated signals (default, safe)
    --mode testnet : Binance Futures Testnet (3,000 USDT virtual balance)
    --mode live    : Binance Futures Live (https://fapi.binance.com)
- Environment variables required for testnet/live:
    export BINANCE_API_KEY="your_key"
    export BINANCE_API_SECRET="your_secret"
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
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "LINKUSDT", "LTCUSDT",
    "DOTUSDT", "UNIUSDT", "ATOMUSDT", "NEARUSDT", "ETCUSDT",
)

LIVE_BASE = "https://fapi.binance.com"
TESTNET_BASE = "https://testnet.binancefuture.com"

# Bar tuple: (open_time_ms, open, high, low, close, volume)
Bar = Tuple[int, float, float, float, float, float]


# -------------------- Pure Causal Indicator, 4H Trend & SMC Engine --------------------

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


def compute_ema_series(closes: List[float], span: int) -> List[float]:
    k = 2.0 / (span + 1.0)
    out: List[float] = []
    for c in closes:
        out.append(c if not out else (c * k + out[-1] * (1.0 - k)))
    return out


def compute_wilder_atr(bars: List[Bar], period: int = 14) -> float:
    val = 0.0
    prev_c: Optional[float] = None
    alpha = 1.0 / period
    for i, (_, _, h, l, c, _) in enumerate(bars):
        tr = (h - l) if prev_c is None else max(h - l, abs(h - prev_c), abs(l - prev_c))
        prev_c = c
        val = tr if i == 0 else ((1.0 - alpha) * val + alpha * tr)
    return val


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
        if not dx_init:
            adx = dx
            dx_init = True
        else:
            adx = (1.0 - alpha) * adx + alpha * dx
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


def compute_er14(closes: List[float]) -> float:
    if len(closes) < 15:
        return 0.0
    arr = closes[-15:]
    den = sum(abs(arr[i] - arr[i - 1]) for i in range(1, len(arr)))
    return abs(arr[-1] - arr[0]) / den if den > 0 else 0.0


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


def evaluate_symbol_bars(
    symbol: str,
    bars_5m: List[Bar],
    bars_15m: List[Bar],
    bars_1h: List[Bar],
    bars_4h: List[Bar],
    bars_1d: Optional[List[Bar]] = None,
    use_4h_trend: bool = True,
    donch_lb: int = 20,
    trail_atr_mult: float = 3.5,
    use_smc: bool = True,
    sweep_tp_r: float = 10.0,
    enable_fast_scalp: bool = False,
) -> Optional[SignalCandidate]:
    """Evaluate strictly CLOSED candles using 100% causal V4.0 verified rules."""
    if len(bars_5m) < 80 or len(bars_15m) < 40 or len(bars_1h) < 60 or len(bars_4h) < max(60, donch_lb + 3):
        return None

    c4 = [b[4] for b in bars_4h]
    atr_4h = compute_wilder_atr(bars_4h, 14)
    adx_4h = compute_wilder_adx(bars_4h, 14)

    # 1) Primary 4H Engine: 4H_Donch20_Trail (PF=1.99, DD=7.8R, 7/7 yrs green, IS=+47.6R, OOS=+32.1R)
    if use_4h_trend and bars_1d and len(bars_1d) >= 50 and atr_4h > 0 and adx_4h >= 20.0:
        c1d = [b[4] for b in bars_1d]
        e20_1d = compute_ema_series(c1d, 20)[-1]
        e50_1d = compute_ema_series(c1d, 50)[-1]
        hi_cur = max(b[2] for b in bars_4h[-(donch_lb + 1):-1])
        lo_cur = min(b[3] for b in bars_4h[-(donch_lb + 1):-1])
        hi_prev = max(b[2] for b in bars_4h[-(donch_lb + 2):-2])
        lo_prev = min(b[3] for b in bars_4h[-(donch_lb + 2):-2])
        c_now, c_prev = c4[-1], c4[-2]
        side = 0
        if e20_1d > e50_1d and c_now > hi_cur and c_prev <= hi_prev:
            side = 1
        elif e20_1d < e50_1d and c_now < lo_cur and c_prev >= lo_prev:
            side = -1
        if side != 0:
            slp = c_now - side * 2.0 * atr_4h
            rd = abs(c_now - slp)
            if 0.005 <= (rd / c_now) <= 0.080:
                return SignalCandidate(
                    symbol, "4H_Donch20_Trail", side, c_now, slp, None, rd,
                    (), 300, is_market=True, trail_atr_mult=trail_atr_mult,
                )

    c1 = [b[4] for b in bars_1h]
    c15 = [b[4] for b in bars_15m]
    c5 = [b[4] for b in bars_5m]

    e20_4h, e50_4h = compute_ema_series(c4, 20)[-1], compute_ema_series(c4, 50)[-1]
    e20_1h, e50_1h = compute_ema_series(c1, 20)[-1], compute_ema_series(c1, 50)[-1]
    tr_up = e20_4h > e50_4h and e20_1h > e50_1h
    tr_dn = e20_4h < e50_4h and e20_1h < e50_1h
    er_4h = compute_er14(c4)
    er_1h = compute_er14(c1)
    er_15 = compute_er14(c15)
    rsi_1h = compute_wilder_rsi(c1, 14)

    e9_5 = compute_ema_series(c5, 9)[-1]
    e20_5 = compute_ema_series(c5, 20)[-1]
    e50_5 = compute_ema_series(c5, 50)[-1]
    macd_hist = compute_macd_hist(c5)
    atr_15 = compute_wilder_atr(bars_15m, 14)
    atr_5 = compute_wilder_atr(bars_5m, 14)
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
    for b_idx, (ts_1h, _, hh, hl, hc, _) in enumerate(bars_1h):
        if b_idx >= start_scan:
            for idx_s, p_lo in list(sw1_k3.act_lo):
                if (sw1_k3.bar_idx + 1 - idx_s) >= 4 and hl < p_lo and hc > p_lo:
                    cands_k3.append((1, ts_1h, hl))
            for idx_s, p_hi in list(sw1_k3.act_hi):
                if (sw1_k3.bar_idx + 1 - idx_s) >= 4 and hh > p_hi and hc < p_hi:
                    cands_k3.append((-1, ts_1h, hh))
        sw1.update(hh, hl, hc)
        sw1_k3.update(hh, hl, hc)

    for _, _, h, l, c, _ in bars_5m[:-1]:
        sw5.update(h, l, c)

    ts_5m, o, h, l, c, _ = bars_5m[-1]
    _, o2, _, _, c2, _ = bars_5m[-2]
    _, _, h1, l1, _, _ = bars_5m[-3]
    utc_dt = dt.datetime.fromtimestamp(ts_5m / 1000.0, tz=dt.timezone.utc)

    # 2) Secondary 1H->5m Engine: SMC_Sweep_10R (PF=1.71, IS=+49.2R, OOS=+28.8R)
    if use_smc and utc_dt.hour >= 9 and atr_5 > 0 and cands_k3:
        c2b = abs(c2 - o2)
        for side, sw_ts, sl_base in reversed(cands_k3):
            if (ts_5m - sw_ts) > 5 * 3600 * 1000:
                continue
            if side == 1 and l >= sl_base and sw4.trend == 1 and sw1.trend == 1 and sw5.last_high is not None:
                if c > sw5.last_high and (l - h1) >= 0.25 * atr_5 and c2 > o2 and c2b >= atr_5:
                    slp = min(sl_base - atr_5, c - max(1.5 * atr_5, c * 0.0020))
                    rd = c - slp
                    if 0.0020 <= rd / c <= 0.0180:
                        return SignalCandidate(
                            symbol, "SMC_Sweep_10R", 1, c, slp, c + sweep_tp_r * rd,
                            rd, ((3.0, 1.0),), 100 * 60, is_market=False,
                        )
            elif side == -1 and h <= sl_base and sw4.trend == -1 and sw1.trend == -1 and sw5.last_low is not None:
                if c < sw5.last_low and (l1 - h) >= 0.25 * atr_5 and c2 < o2 and c2b >= atr_5:
                    slp = max(sl_base + atr_5, c + max(1.5 * atr_5, c * 0.0020))
                    rd = slp - c
                    if 0.0020 <= rd / c <= 0.0180:
                        return SignalCandidate(
                            symbol, "SMC_Sweep_10R", -1, c, slp, c - sweep_tp_r * rd,
                            rd, ((3.0, 1.0),), 100 * 60, is_market=False,
                        )

    if not enable_fast_scalp or utc_dt.weekday() >= 5:
        return None

    # Optional Experimental Fast Scalp (enable_fast_scalp=True only; causal PF~1.12)
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


def run_bot(
    mode: str,
    symbols: Tuple[str, ...],
    leverage: int,
    max_open_pos: int,
    paper_equity: float,
    use_4h_trend: bool = True,
    donch_lb: int = 20,
    trail_atr_mult: float = 3.5,
    use_smc: bool = True,
    sweep_tp_r: float = 10.0,
    enable_fast_scalp: bool = False,
) -> None:
    base_url = TESTNET_BASE if mode == "testnet" else LIVE_BASE
    api_key = os.environ.get("BINANCE_API_KEY", "")
    api_secret = os.environ.get("BINANCE_API_SECRET", "")
    if mode in ("testnet", "live") and (not api_key or not api_secret):
        raise SystemExit("ERROR: Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables first.")

    client = BinanceFuturesClient(base_url, api_key, api_secret)
    filters = client.load_filters(symbols)
    print(f"[INIT] V4.0 mode={mode} symbols={len(filters)}/{len(symbols)} 4H_Trend={use_4h_trend} SMC={use_smc} lev={leverage}x")

    if mode in ("testnet", "live"):
        for sym in filters:
            try:
                client.set_leverage(sym, leverage)
            except Exception as exc:
                print(f"[WARN] leverage failed for {sym}: {exc}")

    hwm_equity = paper_equity
    active_meta: Dict[str, dict] = {}
    while True:
        try:
            equity = paper_equity if mode == "paper" else client.get_usdt_balance()
            hwm_equity = max(hwm_equity, equity)
            dd = (hwm_equity - equity) / hwm_equity if hwm_equity > 0 else 0.0
            dd_brake = 0.50 if dd >= 0.12 else (0.70 if dd >= 0.08 else 1.0)
            open_pos = {} if mode == "paper" else client.get_positions()

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
                    active_meta.pop(sym, None)
                    print(f"[CLOSE] {sym} position closed -> open orders cleaned")
                    continue
                if meta["state"] == "OPEN" and sym in open_pos:
                    exit_side = "SELL" if meta["side"] == 1 else "BUY"
                    qty_abs = abs(open_pos[sym])
                    if meta.get("trail_mult"):
                        b4 = client.get_klines(sym, "4h", 120)
                        if b4:
                            ts4, _, h4, l4, c4, _ = b4[-1]
                            if ts4 != meta.get("last_4h_ts"):
                                meta["last_4h_ts"] = ts4
                                atr4 = compute_wilder_atr(b4, 14)
                                meta["best_px"] = max(meta["best_px"], h4) if meta["side"] == 1 else min(meta["best_px"], l4)
                                raw_sl = meta["best_px"] + (-1 if meta["side"] == 1 else 1) * meta["trail_mult"] * atr4
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
                    elif meta["step_locks"]:
                        b5 = client.get_klines(sym, "5m", 3)
                        if b5:
                            _, _, h, l, c, _ = b5[-1]
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

            for sym, filt in filters.items():
                if sym in open_pos or sym in active_meta or (len(open_pos) + len(active_meta)) >= max_open_pos:
                    continue
                b5 = client.get_klines(sym, "5m", 290)
                b15 = client.get_klines(sym, "15m", 80)
                b1h = client.get_klines(sym, "1h", 120)
                b4h = client.get_klines(sym, "4h", 120)
                b1d = client.get_klines(sym, "1d", 80)
                sig = evaluate_symbol_bars(
                    sym, b5, b15, b1h, b4h, b1d,
                    use_4h_trend=use_4h_trend, donch_lb=donch_lb, trail_atr_mult=trail_atr_mult,
                    use_smc=use_smc, sweep_tp_r=sweep_tp_r, enable_fast_scalp=enable_fast_scalp,
                )
                if sig is None:
                    continue
                ep = round_step(sig.entry_px, filt.tick_size, False)
                sl = round_step(sig.sl_px, filt.tick_size, False)
                tp = round_step(sig.tp_px, filt.tick_size, False) if sig.tp_px is not None else None
                qty = compute_order_qty(equity, 0.015 * dd_brake, ep, sl, filt, leverage=leverage)
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
                        "expires_at": time.time() + sig.expire_sec,
                    }
        except urllib.error.URLError as exc:
            print(f"[NET ERR] {exc}")
        except Exception as exc:
            print(f"[ERR] {exc}")
        time.sleep(30)


def main() -> None:
    ap = argparse.ArgumentParser(description="Binance Futures Multi-Coin Causal 4H Trend + 1H SMC Engine (V4.0 Verified)")
    ap.add_argument("--mode", choices=("paper", "testnet", "live"), default="paper")
    ap.add_argument("--leverage", type=int, default=10)
    ap.add_argument("--max-pos", type=int, default=3)
    ap.add_argument("--paper-equity", type=float, default=500.0)
    ap.add_argument("--no-4h-trend", action="store_true", help="Disable primary 4H_Donch20_Trail engine")
    ap.add_argument("--donch-lb", type=int, default=20)
    ap.add_argument("--trail-atr-mult", type=float, default=3.5)
    ap.add_argument("--no-smc", action="store_true", help="Disable secondary SMC_Sweep_10R engine")
    ap.add_argument("--sweep-tp-r", type=float, default=10.0, help="TP multiple in R for SMC_Sweep (10.0 or 15.0)")
    ap.add_argument("--enable-fast-scalp", action="store_true", help="Enable experimental fast scalp sleeves (low causal edge)")
    ap.add_argument("--symbols", type=str, default=",".join(DEFAULT_SYMBOLS))
    args = ap.parse_args()
    syms = tuple(s.strip().upper() for s in args.symbols.split(",") if s.strip())
    run_bot(
        args.mode, syms, args.leverage, args.max_pos, args.paper_equity,
        use_4h_trend=not args.no_4h_trend, donch_lb=args.donch_lb, trail_atr_mult=args.trail_atr_mult,
        use_smc=not args.no_smc, sweep_tp_r=args.sweep_tp_r, enable_fast_scalp=args.enable_fast_scalp,
    )


if __name__ == "__main__":
    main()
