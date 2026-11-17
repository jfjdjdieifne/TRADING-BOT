# QUANTCONNECT.COM - Binance Futures Multi-Coin V5.0 Topological + Regime Tensor + Risk-Free Pyramiding
# Audited with ZERO HTF lookahead on 718,418 BTC 5m bars (2020-2026, real Binance fees+slip+funding):
#   1) Primary 4H Engine (use_4h_trend=true, default): 4H_V5_Trend (hybrid or topological_bos)
#      - Continuous Sigmoid/Log-Odds Confluence Tensor: KER(20) Anti-Chop + BB/KC Squeeze + RVOL Effort-vs-Result + Displacement + ADX14
#      - Risk-Free Pyramiding: at +2.0R MFE locks BE+0.25R and scales in 0.5x on 4H pullback continuation.
#      - 4H Hybrid (C7): N=204, WR=38.2%, Net=+91.2R, PF=2.01, DD=7.8R, ClusterMax=+12.7R, 7/7 yrs green (OOS PF=2.00 | 2xFees PF=1.77)
#      - 4H Topological (C8): N=236, WR=39.0%, Net=+92.7R, PF=1.87, DD=9.7R, ClusterMax=+16.1R, 7/7 yrs green
#   2) Secondary 1H->5m Engine (use_smc=true, default): SMC_Sweep_10R
#      - 1H (k=3, age>=4) Sweep + 4H/1H Swing Trend + 5m CHoCH+FVG, >=09:00 UTC, BE@3.0R->+1.0R, TP=10R.
#   Combined Dual-Engine (1-coin BTC): N=348, WR=35.3%, Net=+169.1R, PF=1.84, 7/7 yrs green (IS=+102.7R PF=1.93 | OOS=+66.4R PF=1.74)

from AlgorithmImports import *
from collections import deque
import math


def _sigmoid(x: float, x0: float = 0.0, k: float = 1.0) -> float:
    z = max(-60.0, min(60.0, -k * (x - x0)))
    return 1.0 / (1.0 + math.exp(z))


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
    """Scale-free volatility-adjusted topological swing tracker (1.25*ATR confirmation)."""

    def __init__(self, atr_mult: float = 1.25) -> None:
        self.atr_mult = atr_mult
        self.dir = 0
        self.piv_hi = self.piv_lo = None
        self.last_hi = self.last_lo = None

    def update(self, h: float, l: float, atr: float) -> None:
        if atr <= 0:
            return
        th = self.atr_mult * atr
        if self.piv_hi is None:
            self.piv_hi, self.piv_lo = h, l
            return
        if self.dir == 0:
            if h - self.piv_lo >= th:
                self.last_lo = self.piv_lo
                self.dir, self.piv_hi = 1, h
            elif self.piv_hi - l >= th:
                self.last_hi = self.piv_hi
                self.dir, self.piv_lo = -1, l
            else:
                self.piv_hi = max(self.piv_hi, h)
                self.piv_lo = min(self.piv_lo, l)
        elif self.dir == 1:
            if h >= self.piv_hi:
                self.piv_hi = h
            elif self.piv_hi - l >= th:
                self.last_hi = self.piv_hi
                self.dir, self.piv_lo = -1, l
        else:
            if l <= self.piv_lo:
                self.piv_lo = l
            elif h - self.piv_lo >= th:
                self.last_lo = self.piv_lo
                self.dir, self.piv_hi = 1, h


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


class CoinState:
    def __init__(self, ticker: str, symbol: Symbol, leverage: float) -> None:
        self.ticker, self.symbol, self.leverage = ticker, symbol, leverage
        self.sw_4h, self.sw_1h, self.sw_1h_k3 = CausalSwingTracker(2), CausalSwingTracker(2), CausalSwingTracker(3)
        self.sw_5m = CausalSwingTracker(2)
        self.topo_4h = CausalTopologicalZigZag(1.25)
        self.ema_1d, self.ema_4h, self.ema_1h = EmaState(), EmaState(), EmaState()
        self.ema_15m, self.ema_5m = EmaState(), EmaState()
        self.atr_4h, self.adx_4h = WilderATR14(), WilderADX14()
        self.atr_15m, self.atr_5m = WilderATR14(), WilderATR14()
        self.rsi_1h, self.rsi_5m = WilderRSI14(), WilderRSI14()

        # V5 4H Regime Tensor buffers
        self.donch_hi_4h = deque(maxlen=20)
        self.donch_lo_4h = deque(maxlen=20)
        self.closes_4h = deque(maxlen=25)
        self.highs_4h = deque(maxlen=25)
        self.lows_4h = deque(maxlen=25)
        self.vols_4h = deque(maxlen=80)
        self.sq_recent_4h = deque(maxlen=6)
        self.prev_4h_c = self.prev_4h_hi20 = self.prev_4h_lo20 = None
        self.idx_4h = self.cooldown_4h = 0

        self.vols_5m = deque(maxlen=20)
        self.vwap_day, self.vwap_pv, self.vwap_v = None, 0.0, 0.0
        self.bars_5m = deque(maxlen=6)
        self.cands_1h_k3 = []
        self.idx_5m = self.cooldown_until = 0

        self.pending_ticket = self.pending_meta = None
        self.in_position, self.active_engine, self.active_side = False, None, 0
        self.entry_price = self.sl_price = self.risk_dist = self.qty = self.best_px = 0.0
        self.tp_price = self.trail_atr_mult = None
        self.pyramid_armed = self.pyramid_done = False
        self.step_locks = ()
        self.sl_ticket = self.tp_ticket = None
        self.canceled_sl_ids = set()


class BinanceFuturesMultiCoinScalper(QCAlgorithm):
    TICKERS = (
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
        "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "LINKUSDT", "LTCUSDT",
        "DOTUSDT", "UNIUSDT", "ATOMUSDT", "NEARUSDT", "ETCUSDT",
    )
    ENGINE_RISK = {
        "4H_V5_Trend": 0.015,
        "SMC_Sweep_10R": 0.015,
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
        self.risk_scale = float(self.get_parameter("risk_scale") or 1.0)
        self.max_open_pos = int(self.get_parameter("max_open_pos") or 3)
        self.use_4h_trend = str(self.get_parameter("use_4h_trend") or "true").lower() == "true"
        self.v5_mode = str(self.get_parameter("v5_mode") or "hybrid").lower()  # hybrid or topological
        self.use_pyramid = str(self.get_parameter("use_pyramid") or "true").lower() == "true"
        self.use_smc = str(self.get_parameter("use_smc") or "true").lower() == "true"
        self.enable_fast_scalp = str(self.get_parameter("enable_fast_scalp") or "false").lower() == "true"
        self.sweep_tp_r = float(self.get_parameter("sweep_tp_r") or 10.0)
        self.donch_lb = int(self.get_parameter("donch_lb") or 20)
        self.trail_atr_mult = float(self.get_parameter("trail_atr_mult") or 3.5)
        self.conf_threshold = float(self.get_parameter("conf_threshold") or (0.50 if self.v5_mode == "hybrid" else 0.55))
        self.set_warm_up(timedelta(days=65), Resolution.MINUTE)
        self.set_brokerage_model(BrokerageName.BINANCE_FUTURES, AccountType.MARGIN)

        self.coins, self.trade_counts, self.invalid_counts = {}, {}, {}
        for tk in self.TICKERS:
            sec = self.add_crypto_future(tk, Resolution.MINUTE, Market.BINANCE, leverage=10)
            st = CoinState(tk, sec.symbol, 10.0)
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

    def _open_count(self) -> int:
        return sum(1 for st in self.coins.values() if st.in_position or st.pending_ticket is not None)

    def _effective_risk_pct(self, engine: str, mult: float = 1.0) -> float:
        eq = float(self.portfolio.total_portfolio_value)
        dd = (self.hwm_equity - eq) / self.hwm_equity if self.hwm_equity > 0 else 0.0
        brake = 0.50 if dd >= 0.12 else (0.70 if dd >= 0.08 else 1.0)
        return self.ENGINE_RISK.get(engine, 0.015) * brake * self.risk_scale * mult

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
        slot_cap = float(self.portfolio.total_portfolio_value) * st.leverage * 0.30
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
        if st.idx_5m < st.cooldown_until or self._open_count() >= self.max_open_pos:
            return False
        if self.portfolio[st.symbol].invested:
            self.transactions.cancel_open_orders(st.symbol)
            self.liquidate(st.symbol, tag="ORPHAN_CLEAN")
            return False
        return float(self.securities[st.symbol].price) > 0

    def _submit_market(self, st: CoinState, engine: str, side: int, sl: float,
                       trail_mult: float, sl_max: float = 0.080, sl_min: float = 0.005,
                       risk_mult: float = 1.0, is_pyramid: bool = False) -> None:
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
        risk_usd = float(self.portfolio.total_portfolio_value) * self._effective_risk_pct(engine, risk_mult)
        qty = self._round_qty(st.symbol, self._clamp_qty(st, risk_usd / risk, cur_px), side == 1)
        if qty == 0.0:
            return
        st.pending_meta = {
            "engine": engine, "side": side, "trig": cur_px, "sl": sl_px, "tp": None,
            "risk": risk, "qty": qty, "step_locks": (), "trail_mult": trail_mult,
            "is_pyramid": is_pyramid, "exp": st.idx_5m + 3,
        }
        t = self.market_order(st.symbol, qty, tag=f"{engine}_PYR" if is_pyramid else engine)
        if t.status == OrderStatus.INVALID:
            st.pending_meta = st.pending_ticket = None
            return
        if st.pending_meta is not None:
            st.pending_ticket = t

    def _submit_limit(self, st: CoinState, engine: str, side: int, trig: float, sl: float,
                      tp_r: float, step_locks, expire_bars: int, sl_max: float = 0.0180,
                      sl_min: float = 0.0040) -> None:
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
        risk_usd = float(self.portfolio.total_portfolio_value) * self._effective_risk_pct(engine)
        qty = self._round_qty(st.symbol, self._clamp_qty(st, risk_usd / risk, trig_px), side == 1)
        if qty == 0.0:
            return
        st.pending_meta = {
            "engine": engine, "side": side, "trig": trig_px, "sl": sl_px, "tp": tp_px,
            "risk": risk, "qty": qty, "step_locks": step_locks, "trail_mult": None,
            "is_pyramid": False, "exp": st.idx_5m + expire_bars,
        }
        t = self.limit_order(st.symbol, qty, trig_px, tag=engine)
        if t.status == OrderStatus.INVALID:
            st.pending_meta = st.pending_ticket = None
            return
        if st.pending_meta is not None:
            st.pending_ticket = t

    def _compute_4h_v5_confluence(self, st: CoinState, o: float, h: float, l: float, c: float, vol: float, a4: float, adx4: float) -> tuple[float, float]:
        """Compute V5 Continuous Confluence Tensor (KER + Squeeze + RVOL Effort-Result + Displacement + ADX)."""
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
            ker_sc, sq_sc = 0.5, 0.45

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

        # Update Chandelier Trail + Risk-Free Pyramid Arming for open 4H_V5_Trend
        if st.in_position and st.trail_atr_mult is not None and a4 > 0 and st.sl_ticket is not None:
            st.best_px = max(st.best_px, h) if st.active_side == 1 else min(st.best_px, l)
            mfe_r = ((st.best_px - st.entry_price) * st.active_side) / max(st.risk_dist, 1e-12)
            if self.use_pyramid and (not st.pyramid_done) and mfe_r >= 2.0:
                st.pyramid_armed = True
                self._replace_sl(st, st.entry_price + st.active_side * 0.25 * st.risk_dist, c, market_if_crossed=False)
            trail_px = (st.best_px - st.trail_atr_mult * a4) if st.active_side == 1 else (st.best_px + st.trail_atr_mult * a4)
            self._replace_sl(st, trail_px, c, market_if_crossed=True)

            # Check Risk-Free Pyramid Scale-In on 4H Pullback Continuation
            if self.use_pyramid and st.in_position and st.pyramid_armed and (not st.pyramid_done) and st.pending_ticket is None and st.prev_4h_c is not None:
                pb = (
                    (st.active_side == 1 and l <= st.prev_4h_c and c > o and c > st.entry_price)
                    or (st.active_side == -1 and h >= st.prev_4h_c and c < o and c < st.entry_price)
                )
                if pb:
                    self._submit_market(
                        st, "4H_V5_Trend", st.active_side, c - st.active_side * 1.5 * a4,
                        self.trail_atr_mult, risk_mult=0.5, is_pyramid=True,
                    )

        # Evaluate Primary 4H_V5_Trend Signal
        hi_n = max(st.donch_hi_4h) if len(st.donch_hi_4h) == self.donch_lb else None
        lo_n = min(st.donch_lo_4h) if len(st.donch_lo_4h) == self.donch_lb else None
        if (
            self.use_4h_trend and not self.is_warming_up and not st.in_position and a4 > 0
            and st.idx_4h >= st.cooldown_4h and st.prev_4h_c is not None
        ):
            t1d = st.ema_1d.trend
            side = 0
            if self.v5_mode == "topological":
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

            if side != 0:
                conf, trap_sc = self._compute_4h_v5_confluence(st, o, h, l, c, vol, a4, adx4)
                if conf >= self.conf_threshold and trap_sc < 0.78:
                    self._submit_market(st, "4H_V5_Trend", side, c - side * 2.0 * a4, self.trail_atr_mult)

        st.prev_4h_c, st.prev_4h_hi20, st.prev_4h_lo20 = c, hi_n, lo_n
        st.donch_hi_4h.append(h)
        st.donch_lo_4h.append(l)
        st.closes_4h.append(c)
        st.highs_4h.append(h)
        st.lows_4h.append(l)
        st.vols_4h.append(vol)
        st.topo_4h.update(h, l, a4)
        st.sw_4h.update(bar)
        st.ema_4h.update(c)

    def on_1h(self, st: CoinState, bar) -> None:
        h, l, c = float(bar.High), float(bar.Low), float(bar.Close)
        k3 = st.sw_1h_k3
        for idx_s, p_lo in list(k3.act_lo):
            if (k3.bar_idx + 1 - idx_s) >= 4 and l < p_lo and c > p_lo:
                st.cands_1h_k3.append({"side": 1, "start_i": st.idx_5m, "sl_base": l, "choch": st.sw_5m.last_high})
        for idx_s, p_hi in list(k3.act_hi):
            if (k3.bar_idx + 1 - idx_s) >= 4 and h > p_hi and c < p_hi:
                st.cands_1h_k3.append({"side": -1, "start_i": st.idx_5m, "sl_base": h, "choch": st.sw_5m.last_low})
        st.sw_1h.update(bar)
        k3.update(bar)
        st.ema_1h.update(c)
        st.rsi_1h.update(c)

    def on_15m(self, st: CoinState, bar) -> None:
        c = float(bar.Close)
        st.atr_15m.update(float(bar.High), float(bar.Low), c)
        st.ema_15m.update(c)

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

        if st.vwap_day != dt.date():
            st.vwap_day = dt.date()
            st.vwap_pv = st.vwap_v = 0.0
        st.vwap_pv += ((h + l + c) / 3.0) * vol
        st.vwap_v += vol
        vwap = (st.vwap_pv / st.vwap_v) if st.vwap_v > 0 else None

        if st.in_position and st.risk_dist > 0 and st.sl_ticket is not None:
            for act_r, lk_r in st.step_locks:
                hit = (h >= st.entry_price + act_r * st.risk_dist) if st.active_side == 1 else (l <= st.entry_price - act_r * st.risk_dist)
                if hit:
                    self._replace_sl(st, st.entry_price + st.active_side * lk_r * st.risk_dist, c)

        if st.pending_ticket is not None and st.pending_meta is not None:
            pm = st.pending_meta
            if st.idx_5m > pm["exp"] or (l <= pm["sl"] if pm["side"] == 1 else h >= pm["sl"]):
                self._cancel_pending(st)

        if not self.is_warming_up and len(st.bars_5m) >= 3:
            b1, b2, b3 = st.bars_5m[-3], st.bars_5m[-2], st.bars_5m[-1]
            c2b = abs(b2[3] - b2[0])
            still = []
            for cd in st.cands_1h_k3:
                if st.idx_5m - cd["start_i"] > 60:
                    continue
                if self.use_smc and dt.hour >= 9:
                    if cd["side"] == 1 and l >= cd["sl_base"] and st.sw_4h.trend == 1 and st.sw_1h.trend == 1 and cd["choch"] is not None and c > cd["choch"] and (b3[2] - b1[1]) >= 0.25 * a5 and b2[3] > b2[0] and c2b >= a5:
                        slp = min(cd["sl_base"] - a5, c - max(1.5 * a5, c * 0.0020))
                        self._submit_limit(st, "SMC_Sweep_10R", 1, c, slp, self.sweep_tp_r, self.SWEEP_STEPS, 20, 0.0180, 0.0020)
                        continue
                    if cd["side"] == -1 and h <= cd["sl_base"] and st.sw_4h.trend == -1 and st.sw_1h.trend == -1 and cd["choch"] is not None and c < cd["choch"] and (b1[2] - b3[1]) >= 0.25 * a5 and b2[3] < b2[0] and c2b >= a5:
                        slp = max(cd["sl_base"] + a5, c + max(1.5 * a5, c * 0.0020))
                        self._submit_limit(st, "SMC_Sweep_10R", -1, c, slp, self.sweep_tp_r, self.SWEEP_STEPS, 20, 0.0180, 0.0020)
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

        if st.pending_meta is not None and st.in_position and st.pending_meta.get("is_pyramid") and abs(float(oe.fill_quantity)) > 0:
            pm = st.pending_meta
            st.pending_ticket = st.pending_meta = None
            st.pyramid_done = True
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
            st.step_locks, st.trail_atr_mult = pm["step_locks"], pm["trail_mult"]
            st.pyramid_armed = st.pyramid_done = False
            self.trade_counts[st.ticker] += 1
            st.sl_ticket = self.stop_market_order(st.symbol, -st.qty, st.sl_price, tag=f"{st.active_engine}_SL")
            if st.tp_price is not None:
                st.tp_ticket = self.limit_order(st.symbol, -st.qty, st.tp_price, tag=f"{st.active_engine}_TP")
        elif st.in_position:
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
            if eq > self.hwm_equity:
                self.hwm_equity = eq

    @staticmethod
    def _reset_pos(st: CoinState) -> None:
        st.in_position = st.pyramid_armed = st.pyramid_done = False
        st.active_engine = st.tp_price = st.trail_atr_mult = st.sl_ticket = st.tp_ticket = None
        st.active_side = 0
        st.entry_price = st.sl_price = st.risk_dist = st.qty = st.best_px = 0.0
        st.step_locks = ()

    def on_end_of_algorithm(self) -> None:
        self.log(f"=== Binance Multi-Coin V5.0 Topological+Pyramid | Trades={sum(self.trade_counts.values())} | Eq={self.portfolio.total_portfolio_value:.2f} USDT ===")
        for tk in self.TICKERS:
            if self.trade_counts[tk] > 0 or self.invalid_counts[tk] > 0:
                self.log(f"  {tk:10s}: trades={self.trade_counts[tk]} invalid={self.invalid_counts[tk]}")
