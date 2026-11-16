# region imports
from AlgorithmImports import *
from collections import deque, defaultdict
from datetime import timedelta
import math
# endregion


class CausalSwingTracker:
    def __init__(self, k: int = 2, maxlen: int = 240):
        self.k = k
        self.bars = deque(maxlen=max(maxlen, 2 * k + 5))
        self.last_high = None
        self.last_low = None
        self.trend = 0
        self.prev_h_bos = None
        self.prev_l_bos = None
        self.act_hi = deque(maxlen=80)
        self.act_lo = deque(maxlen=80)
        self.bar_idx = -1

    def update(self, bar):
        self.bar_idx += 1
        o, h, l, c = float(bar.Open), float(bar.High), float(bar.Low), float(bar.Close)
        self.bars.append((bar.EndTime, o, h, l, c))
        n, k = len(self.bars), self.k
        nh, nl = None, None
        if self.prev_h_bos is not None and c > self.prev_h_bos:
            self.trend = 1
        elif self.prev_l_bos is not None and c < self.prev_l_bos:
            self.trend = -1
        self.act_hi = deque([s for s in self.act_hi if h <= s[1]], maxlen=80)
        self.act_lo = deque([s for s in self.act_lo if l >= s[1]], maxlen=80)
        if n >= 2 * k + 1:
            mid = n - 1 - k
            midx = self.bar_idx - k
            mh, ml = self.bars[mid][2], self.bars[mid][3]
            if all(self.bars[j][2] <= mh for j in range(mid - k, mid + k + 1) if j != mid):
                self.last_high = self.prev_h_bos = mh
                nh = (midx, mh)
                if max(self.bars[j][2] for j in range(mid + 1, n)) <= mh:
                    self.act_hi.append(nh)
            if all(self.bars[j][3] >= ml for j in range(mid - k, mid + k + 1) if j != mid):
                self.last_low = self.prev_l_bos = ml
                nl = (midx, ml)
                if min(self.bars[j][3] for j in range(mid + 1, n)) >= ml:
                    self.act_lo.append(nl)
        return nh, nl


class CausalATR14:
    def __init__(self, period: int = 14):
        self.alpha = 1.0 / period
        self.prev_c = None
        self.value = None

    def update(self, h: float, l: float, c: float) -> float:
        tr = (h - l) if self.prev_c is None else max(h - l, abs(h - self.prev_c), abs(l - self.prev_c))
        self.prev_c = c
        self.value = tr if self.value is None else (self.alpha * tr + (1.0 - self.alpha) * self.value)
        return self.value


class AssetState:
    def __init__(self, name: str, symbol: Symbol, leverage: float):
        self.name, self.symbol, self.leverage = name, symbol, leverage
        self.sw_ltf = CausalSwingTracker(2)
        self.sw_5m = CausalSwingTracker(2)
        self.sw_15m = CausalSwingTracker(2)
        self.sw_15m_k3 = CausalSwingTracker(3)
        self.sw_1h = CausalSwingTracker(2)
        self.sw_1h_k3 = CausalSwingTracker(3)
        self.sw_4h = CausalSwingTracker(2)
        self.sw_1d = CausalSwingTracker(2)
        self.atr_ltf, self.atr_5m, self.atr_15m = CausalATR14(14), CausalATR14(14), CausalATR14(14)
        self.bars_ltf, self.bars_5m, self.bars_15m, self.bars_1h = deque(maxlen=15), deque(maxlen=15), deque(maxlen=20), deque(maxlen=15)
        self.cands_1h_k3_5m, self.cands_1h_k3_ltf, self.cands_15m_k2, self.amd_manips = [], [], [], []
        self.visa_5m_lo, self.visa_5m_hi = deque(maxlen=15), deque(maxlen=15)
        self.visa_tap_s, self.visa_tap_l, self.visa_hi_px, self.visa_lo_px = -999, -999, 0.0, 1e9
        self.pending_ticket = self.pending_meta = None
        self.in_position = False
        self.active_engine, self.active_side = "", 0
        self.entry_price = self.sl_price = self.risk_dist = self.qty = 0.0
        self.tp_price = self.trail_after_r = self.be_act_r = self.trail_mode = None
        self.be_lock_r, self.be_done, self.trailing_active = 1.0, False, False
        self.sl_ticket = self.tp_ticket = None
        self.ltf_idx = self.idx_5m = self.idx_15m = self.bars_seen = self.orders_submitted = 0


class V8MultiAssetSniperAlgorithm(QCAlgorithm):
    def initialize(self) -> None:
        self.set_time_zone(TimeZones.UTC)
        self.set_start_date(2020, 2, 1)
        self.set_end_date(2026, 10, 31)
        self.set_cash(100000)
        self.risk_pct = float(self.get_parameter("risk_pct") or 0.015)
        self.set_warm_up(timedelta(days=30), Resolution.MINUTE)

        xau = self.add_cfd("XAUUSD", Resolution.MINUTE, Market.OANDA, leverage=50)
        nsx = self.add_cfd("NAS100USD", Resolution.MINUTE, Market.OANDA, leverage=50)
        btc = self.add_crypto("BTCUSD", Resolution.MINUTE, Market.COINBASE, leverage=25)
        btc.set_buying_power_model(SecurityMarginModel(25.0))

        self.xau_sym, self.nsx_sym, self.btc_sym = xau.symbol, nsx.symbol, btc.symbol
        self.assets = {
            self.xau_sym: AssetState("XAUUSD", self.xau_sym, 50.0),
            self.nsx_sym: AssetState("NAS100USD", self.nsx_sym, 50.0),
            self.btc_sym: AssetState("BTCUSD", self.btc_sym, 25.0),
        }
        self.trade_counts, self.invalid_counts = defaultdict(int), defaultdict(int)
        for sym, st in self.assets.items():
            self.consolidate(sym, timedelta(minutes=5), lambda b, s=st: self.on_5m(s, b))
            self.consolidate(sym, timedelta(minutes=15), lambda b, s=st: self.on_15m(s, b))
            self.consolidate(sym, timedelta(hours=1), lambda b, s=st: self.on_1h(s, b))
            self.consolidate(sym, timedelta(hours=4), lambda b, s=st: self.on_4h(s, b))
            self.consolidate(sym, timedelta(days=1), lambda b, s=st: self.on_1d(s, b))

    @staticmethod
    def _in_kz(dt) -> bool:
        return (7 <= dt.hour <= 10) or (12 <= dt.hour <= 16)

    @staticmethod
    def _in_ny(dt) -> bool:
        return 12 <= dt.hour < 17

    @staticmethod
    def _bar(data: Slice, sym: Symbol):
        if sym in data.quote_bars:
            return data.quote_bars[sym]
        return data.bars[sym] if sym in data.bars else None

    def _round_qty(self, sym: Symbol, raw_qty: float, is_long: bool) -> float:
        sp = self.securities[sym].symbol_properties
        lot = float(sp.lot_size or 0.001)
        min_sz = float(sp.minimum_order_size or lot)
        qty = round(math.floor(abs(raw_qty) / lot) * lot, 8)
        if qty < min_sz:
            return 0.0
        return qty if is_long else -qty

    def _round_px(self, sym: Symbol, price: float) -> float:
        tick = float(self.securities[sym].symbol_properties.minimum_price_variation or 0.01)
        tick = tick if tick > 0 else 0.01
        return round(round(price / tick) * tick, 6)

    def _clamp_qty(self, st: AssetState, raw_qty: float, px: float) -> float:
        if px <= 0:
            return raw_qty
        max_notional = max(0.0, float(self.portfolio.margin_remaining)) * st.leverage * 0.85
        return min(abs(raw_qty), max_notional / px) if max_notional > 0 else 0.0

    def _cancel_pending(self, st: AssetState) -> None:
        if st.pending_ticket is not None and st.pending_ticket.status not in (
            OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.INVALID
        ):
            st.pending_ticket.cancel()
        st.pending_ticket = st.pending_meta = None

    def _try_lock_sl(self, st: AssetState, lock_px: float, cur_c: float) -> None:
        lp = self._round_px(st.symbol, lock_px)
        if (st.active_side == 1 and lp > st.sl_price and lp < cur_c) or (
            st.active_side == -1 and lp < st.sl_price and lp > cur_c
        ):
            st.sl_price = lp
            st.sl_ticket.update_stop_price(lp)

    def _submit_entry(self, st: AssetState, engine: str, side: int, trig: float, sl: float,
                      tp: float = None, trail_after_r: float = None, be_act_r: float = None,
                      be_lock_r: float = 1.0, expire_bars: int = 20, min_risk: float = 0.0,
                      kz_mode: str = "both", skip_hours=None, is_market: bool = False) -> None:
        if self.is_warming_up or st.in_position or st.pending_ticket is not None or not self.is_market_open(st.symbol):
            return
        cur_px = float(self.securities[st.symbol].price)
        if cur_px <= 0:
            return
        trig_px = cur_px if is_market else self._round_px(st.symbol, trig)
        sl_px = self._round_px(st.symbol, sl)
        risk = (trig_px - sl_px) if side == 1 else (sl_px - trig_px)
        if risk <= max(min_risk, 1e-6):
            return
        if not is_market and ((side == 1 and trig_px > cur_px) or (side == -1 and trig_px < cur_px)):
            return
        risk_usd = float(self.portfolio.total_portfolio_value) * self.risk_pct
        qty = self._round_qty(st.symbol, self._clamp_qty(st, risk_usd / risk, trig_px), side == 1)
        if qty == 0.0:
            return
        st.pending_meta = {
            "engine": engine, "side": side, "trig": trig_px, "sl": sl_px,
            "tp": self._round_px(st.symbol, tp) if tp is not None else None,
            "risk": risk, "qty": qty, "trail_after_r": trail_after_r,
            "be_act_r": be_act_r, "be_lock_r": be_lock_r,
            "expire_idx": st.ltf_idx + expire_bars, "kz_mode": kz_mode, "skip_hours": skip_hours,
        }
        st.orders_submitted += 1
        ticket = self.market_order(st.symbol, qty, tag=engine) if is_market else self.limit_order(st.symbol, qty, trig_px, tag=engine)
        if ticket.status == OrderStatus.INVALID:
            st.pending_meta = st.pending_ticket = None
            return
        if st.pending_meta is not None:
            st.pending_ticket = ticket

    def on_1d(self, st: AssetState, bar) -> None:
        st.sw_1d.update(bar)

    def on_4h(self, st: AssetState, bar) -> None:
        st.sw_4h.update(bar)

    def on_1h(self, st: AssetState, bar) -> None:
        h, l, c, o = float(bar.High), float(bar.Low), float(bar.Close), float(bar.Open)
        st.bars_1h.append((bar.EndTime, o, h, l, c))
        k3 = st.sw_1h_k3
        for idx_s, p_lo in list(k3.act_lo):
            if (k3.bar_idx + 1 - idx_s) >= 4 and l < p_lo and c > p_lo:
                if st.symbol == self.xau_sym:
                    st.cands_1h_k3_5m.append({"side": 1, "start_i": st.idx_5m, "sl_base": l, "choch": st.sw_5m.last_high})
                else:
                    st.cands_1h_k3_ltf.append({"side": 1, "start_i": st.ltf_idx, "sl_base": l, "choch": st.sw_ltf.last_high})
        for idx_s, p_hi in list(k3.act_hi):
            if (k3.bar_idx + 1 - idx_s) >= 4 and h > p_hi and c < p_hi:
                if st.symbol == self.xau_sym:
                    st.cands_1h_k3_5m.append({"side": -1, "start_i": st.idx_5m, "sl_base": h, "choch": st.sw_5m.last_low})
                else:
                    st.cands_1h_k3_ltf.append({"side": -1, "start_i": st.ltf_idx, "sl_base": h, "choch": st.sw_ltf.last_low})
        nh, nl = st.sw_1h.update(bar)
        st.sw_1h_k3.update(bar)
        if st.in_position and st.trailing_active and st.trail_mode == "1h" and st.sl_ticket is not None:
            if st.sl_ticket.status not in (OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.INVALID):
                if st.active_side == 1 and nl is not None:
                    self._try_lock_sl(st, max(st.sl_price, float(nl[1])), c)
                elif st.active_side == -1 and nh is not None:
                    self._try_lock_sl(st, min(st.sl_price, float(nh[1])), c)

    def on_15m(self, st: AssetState, bar) -> None:
        st.idx_15m += 1
        h, l, c, o = float(bar.High), float(bar.Low), float(bar.Close), float(bar.Open)
        a15 = st.atr_15m.update(h, l, c)
        st.bars_15m.append((bar.EndTime, o, h, l, c))
        dt = bar.EndTime
        if st.symbol == self.xau_sym:
            for idx_s, p_lo in list(st.sw_15m.act_lo):
                if (st.sw_15m.bar_idx + 1 - idx_s) >= 2 and l < p_lo and c > p_lo:
                    st.cands_15m_k2.append({"side": 1, "start_i": st.ltf_idx, "sl_base": l, "choch": st.sw_ltf.last_high})
            for idx_s, p_hi in list(st.sw_15m.act_hi):
                if (st.sw_15m.bar_idx + 1 - idx_s) >= 2 and h > p_hi and c < p_hi:
                    st.cands_15m_k2.append({"side": -1, "start_i": st.ltf_idx, "sl_base": h, "choch": st.sw_ltf.last_low})

        if st.symbol == self.xau_sym and len(st.bars_15m) >= 3 and self._in_ny(dt) and dt.hour not in (13, 14):
            b1, b2, b3 = st.bars_15m[-3], st.bars_15m[-2], st.bars_15m[-1]
            c2b, buf = abs(b2[4] - b2[1]), max(1.0, 0.75 * a15)
            if st.sw_4h.trend == 1 and st.sw_1h.trend == 1 and st.sw_15m.last_high is not None:
                bos_up = (b2[4] <= st.sw_15m.last_high < b3[4]) or (b1[4] <= st.sw_15m.last_high < b2[4])
                if bos_up and (b3[3] - b1[2]) >= max(0.20, 0.30 * a15) and b2[4] > b2[1] and c2b >= a15:
                    self._submit_entry(st, "V3_Pro_Clean", 1, b3[3], min(b1[3], b2[3]) - buf,
                                       trail_after_r=2.5, expire_bars=300, min_risk=1.0, kz_mode="ny", skip_hours=(13, 14))
            elif st.sw_4h.trend == -1 and st.sw_1h.trend == -1 and st.sw_15m.last_low is not None:
                bos_dn = (b2[4] >= st.sw_15m.last_low > b3[4]) or (b1[4] >= st.sw_15m.last_low > b2[4])
                if bos_dn and (b1[3] - b3[2]) >= max(0.20, 0.30 * a15) and b2[4] < b2[1] and c2b >= a15:
                    self._submit_entry(st, "V3_Pro_Clean", -1, b3[2], max(b1[2], b2[2]) + buf,
                                       trail_after_r=2.5, expire_bars=300, min_risk=1.0, kz_mode="ny", skip_hours=(13, 14))

        if st.symbol in (self.xau_sym, self.nsx_sym) and len(st.bars_15m) >= 10 and a15 > 0:
            box = list(st.bars_15m)[-9:-1]
            box_hi, box_lo = max(b[2] for b in box), min(b[3] for b in box)
            if (box_hi - box_lo) <= 2.5 * a15:
                if l < box_lo and c >= box_lo - 0.8 * a15:
                    st.amd_manips.append({"side": 1, "r_hi": box_hi, "r_lo": box_lo, "ext": l, "si": st.idx_15m})
                if h > box_hi and c <= box_hi + 0.8 * a15:
                    st.amd_manips.append({"side": -1, "r_hi": box_hi, "r_lo": box_lo, "ext": h, "si": st.idx_15m})
            b1, b2, b3 = st.bars_15m[-3], st.bars_15m[-2], st.bars_15m[-1]
            c2b = abs(b2[4] - b2[1])
            min_r = 5.0 if st.symbol == self.nsx_sym else 0.5
            eng = "NSX_AMD_1D" if st.symbol == self.nsx_sym else "AMD_Pro"
            still = []
            for mp in st.amd_manips:
                if st.idx_15m - mp["si"] > 8:
                    continue
                if mp["side"] == 1:
                    mp["ext"] = min(mp["ext"], l)
                    ok_1d = (st.symbol != self.nsx_sym) or (st.sw_1d.trend == 1)
                    if ok_1d and c > mp["r_hi"] and (b3[3] - b1[2]) >= 0.25 * a15 and b2[4] > b2[1] and c2b >= 0.8 * a15 and st.sw_1h.trend == 1 and self._in_kz(dt):
                        self._submit_entry(st, eng, 1, b3[3], mp["ext"] - 0.5 * a15, trail_after_r=2.0, expire_bars=300, min_risk=min_r)
                        continue
                else:
                    mp["ext"] = max(mp["ext"], h)
                    ok_1d = (st.symbol != self.nsx_sym) or (st.sw_1d.trend == -1)
                    if ok_1d and c < mp["r_lo"] and (b1[3] - b3[2]) >= 0.25 * a15 and b2[4] < b2[1] and c2b >= 0.8 * a15 and st.sw_1h.trend == -1 and self._in_kz(dt):
                        self._submit_entry(st, eng, -1, b3[2], mp["ext"] + 0.5 * a15, trail_after_r=2.0, expire_bars=300, min_risk=min_r)
                        continue
                still.append(mp)
            st.amd_manips = still

        st.sw_15m.update(bar)
        if st.symbol == self.xau_sym:
            st.sw_15m_k3.update(bar)

    def on_5m(self, st: AssetState, bar) -> None:
        st.idx_5m += 1
        h, l, c, o = float(bar.High), float(bar.Low), float(bar.Close), float(bar.Open)
        a5 = st.atr_5m.update(h, l, c)
        st.bars_5m.append((bar.EndTime, o, h, l, c))

        if st.symbol == self.xau_sym and len(st.bars_5m) >= 3 and self._in_kz(bar.EndTime):
            b1, b2, b3 = st.bars_5m[-3], st.bars_5m[-2], st.bars_5m[-1]
            c2b, buf = abs(b2[4] - b2[1]), max(1.0, 0.5 * a5)
            still = []
            for sc in st.cands_1h_k3_5m:
                if st.idx_5m - sc["start_i"] > 12:
                    continue
                if sc["side"] == 1:
                    if l < sc["sl_base"]:
                        continue
                    if st.sw_4h.trend == 1 and sc["choch"] is not None and c > sc["choch"] and (b3[3] - b1[2]) >= max(0.20, 0.20 * a5) and b2[4] > b2[1] and c2b >= 0.8 * a5:
                        self._submit_entry(st, "VisB_Pro", 1, b3[3], sc["sl_base"] - buf, trail_after_r=1.5, expire_bars=90, min_risk=1.0)
                        continue
                else:
                    if h > sc["sl_base"]:
                        continue
                    if st.sw_4h.trend == -1 and sc["choch"] is not None and c < sc["choch"] and (b1[3] - b3[2]) >= max(0.20, 0.20 * a5) and b2[4] < b2[1] and c2b >= 0.8 * a5:
                        self._submit_entry(st, "VisB_Pro", -1, b3[2], sc["sl_base"] + buf, trail_after_r=1.5, expire_bars=90, min_risk=1.0)
                        continue
                still.append(sc)
            st.cands_1h_k3_5m = still

        if st.symbol == self.xau_sym and a5 > 0:
            buf = max(1.0, 0.5 * a5)
            for idx_s, sp_hi in st.sw_15m_k3.act_hi:
                if (st.sw_15m_k3.bar_idx - idx_s) <= 120 and h >= sp_hi - 0.5 * a5:
                    st.visa_hi_px = h if (st.idx_5m - st.visa_tap_s > 18) else max(st.visa_hi_px, h)
                    st.visa_tap_s = st.idx_5m
            for idx_s, sp_lo in st.sw_15m_k3.act_lo:
                if (st.sw_15m_k3.bar_idx - idx_s) <= 120 and l <= sp_lo + 0.5 * a5:
                    st.visa_lo_px = l if (st.idx_5m - st.visa_tap_l > 18) else min(st.visa_lo_px, l)
                    st.visa_tap_l = st.idx_5m
            if self._in_kz(bar.EndTime) and len(st.bars_5m) >= 2:
                pc = st.bars_5m[-2][4]
                if (st.idx_5m - st.visa_tap_s) <= 12 and len(st.visa_5m_lo) >= 3:
                    la, lb, lc = st.visa_5m_lo[-3], st.visa_5m_lo[-2], st.visa_5m_lo[-1]
                    if la[1] < lb[1] < lc[1] and (st.idx_5m - la[0]) <= 72 and lc[0] < st.idx_5m and pc >= lc[1] > c:
                        sl = max(st.visa_hi_px, max(b[2] for b in list(st.bars_5m)[-7:])) + buf
                        if sl > c and 2.0 <= (c - la[1]) / (sl - c) <= 6.0:
                            self._submit_entry(st, "VisA", -1, c, sl, tp=la[1], expire_bars=5, min_risk=1.0, is_market=True)
                        st.visa_tap_s = -999
                if (st.idx_5m - st.visa_tap_l) <= 12 and len(st.visa_5m_hi) >= 3:
                    ha, hb, hc = st.visa_5m_hi[-3], st.visa_5m_hi[-2], st.visa_5m_hi[-1]
                    if ha[1] > hb[1] > hc[1] and (st.idx_5m - ha[0]) <= 72 and hc[0] < st.idx_5m and pc <= hc[1] < c:
                        sl = min(st.visa_lo_px, min(b[3] for b in list(st.bars_5m)[-7:])) - buf
                        if c > sl and 2.0 <= (ha[1] - c) / (c - sl) <= 6.0:
                            self._submit_entry(st, "VisA", 1, c, sl, tp=ha[1], expire_bars=5, min_risk=1.0, is_market=True)
                        st.visa_tap_l = -999

        nh5, nl5 = st.sw_5m.update(bar)
        if nl5 is not None:
            st.visa_5m_lo.append((st.idx_5m - 2, nl5[1]))
        if nh5 is not None:
            st.visa_5m_hi.append((st.idx_5m - 2, nh5[1]))

        if st.symbol == self.btc_sym:
            self._ltf_bar(st, bar, 9, False, 0.0, 0.0020, 15.0, 3.0, "dual", "BTC_15R_BE", False)

    def on_data(self, data: Slice) -> None:
        for sym, st in self.assets.items():
            bar = self._bar(data, sym)
            if bar is None:
                continue
            st.bars_seen += 1
            if sym == self.xau_sym:
                self._ltf_bar(st, bar, None, True, 2.0, 0.0010, 3.0, None, "dual", "XAU_LTF1M", True)
            elif sym == self.nsx_sym:
                self._ltf_bar(st, bar, 9, True, 10.0, 0.0010, 10.0, None, "4h", "NSX_1H1m_10R", False)

    def _ltf_bar(self, st: AssetState, bar, min_hr, use_kz: bool, min_abs: float, min_pct: float,
                 fixed_rr: float, be_act_r, htf_mode: str, eng: str, use_15m: bool) -> None:
        st.ltf_idx += 1
        dt = bar.EndTime
        o, h, l, c = float(bar.Open), float(bar.High), float(bar.Low), float(bar.Close)
        a1 = st.atr_ltf.update(h, l, c)
        st.bars_ltf.append((dt, o, h, l, c))

        if st.in_position and st.risk_dist > 0 and st.sl_ticket is not None:
            can_upd = st.sl_ticket.status not in (OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.INVALID)
            if can_upd and st.be_act_r is not None and not st.be_done:
                hit_be = (h >= st.entry_price + st.be_act_r * st.risk_dist) if st.active_side == 1 else (l <= st.entry_price - st.be_act_r * st.risk_dist)
                if hit_be:
                    st.be_done = True
                    self._try_lock_sl(st, st.entry_price + st.active_side * st.be_lock_r * st.risk_dist, c)
            if can_upd and st.trail_after_r is not None and not st.trailing_active:
                hit_tr = (h >= st.entry_price + st.trail_after_r * st.risk_dist) if st.active_side == 1 else (l <= st.entry_price - st.trail_after_r * st.risk_dist)
                if hit_tr:
                    st.trailing_active, st.trail_mode = True, "1h"
                    self._try_lock_sl(st, st.entry_price + st.active_side * st.be_lock_r * st.risk_dist, c)

        if st.pending_ticket is not None and st.pending_meta is not None:
            pm = st.pending_meta
            if st.ltf_idx > pm["expire_idx"] or ((l <= pm["sl"]) if pm["side"] == 1 else (h >= pm["sl"])) or (pm["skip_hours"] and dt.hour in pm["skip_hours"]):
                self._cancel_pending(st)

        kz_ok = ((not use_kz) or self._in_kz(dt)) and (min_hr is None or dt.hour >= min_hr)
        cands = st.cands_15m_k2 if use_15m else st.cands_1h_k3_ltf
        max_wait = 20 if use_15m else 60
        if len(st.bars_ltf) >= 3 and kz_ok and not self.is_warming_up:
            b1, b2, b3 = st.bars_ltf[-3], st.bars_ltf[-2], st.bars_ltf[-1]
            c2b, buf, min_r = abs(b2[4] - b2[1]), a1, max(min_abs, c * min_pct)
            still = []
            for sc in cands:
                if st.ltf_idx - sc["start_i"] > max_wait:
                    continue
                if sc["side"] == 1:
                    if l < sc["sl_base"]:
                        continue
                    ok_htf = (st.sw_4h.trend == 1) and (htf_mode != "dual" or st.sw_1h.trend == 1)
                    if ok_htf and sc["choch"] is not None and b3[4] > sc["choch"] and (b3[3] - b1[2]) >= 0.25 * a1 and b2[4] > b2[1] and c2b >= a1:
                        trig, sl = b3[3], sc["sl_base"] - buf
                        self._submit_entry(st, eng, 1, trig, sl, tp=trig + fixed_rr * (trig - sl), be_act_r=be_act_r, expire_bars=20, min_risk=min_r, kz_mode="both" if use_kz else "none")
                        continue
                else:
                    if h > sc["sl_base"]:
                        continue
                    ok_htf = (st.sw_4h.trend == -1) and (htf_mode != "dual" or st.sw_1h.trend == -1)
                    if ok_htf and sc["choch"] is not None and b3[4] < sc["choch"] and (b1[3] - b3[2]) >= 0.25 * a1 and b2[4] < b2[1] and c2b >= a1:
                        trig, sl = b3[2], sc["sl_base"] + buf
                        self._submit_entry(st, eng, -1, trig, sl, tp=trig - fixed_rr * (sl - trig), be_act_r=be_act_r, expire_bars=20, min_risk=min_r, kz_mode="both" if use_kz else "none")
                        continue
                still.append(sc)
            if use_15m:
                st.cands_15m_k2 = still
            else:
                st.cands_1h_k3_ltf = still
        st.sw_ltf.update(bar)

    def on_order_event(self, oe: OrderEvent) -> None:
        if oe.symbol not in self.assets:
            return
        st = self.assets[oe.symbol]
        if oe.status == OrderStatus.INVALID:
            self.invalid_counts[st.name] += 1
            if self.invalid_counts[st.name] <= 5:
                self.debug(f"INVALID {st.name} (id={oe.order_id}): {oe.message}")
            if st.pending_meta is not None and not st.in_position:
                st.pending_ticket = st.pending_meta = None
            elif st.in_position:
                self.transactions.cancel_open_orders(oe.symbol)
                self.liquidate(oe.symbol)
                st.in_position = False
                st.sl_ticket = st.tp_ticket = None
            return
        if oe.status == OrderStatus.CANCELED:
            if st.pending_ticket is not None and oe.order_id == st.pending_ticket.order_id:
                st.pending_ticket = st.pending_meta = None
            return
        if oe.status != OrderStatus.FILLED:
            return

        if ((st.pending_ticket is not None and oe.order_id == st.pending_ticket.order_id) or (st.pending_meta is not None and not st.in_position)) and st.pending_meta is not None:
            pm = st.pending_meta
            st.pending_ticket = st.pending_meta = None
            fill_px = float(oe.fill_price)
            st.in_position, st.active_engine, st.active_side = True, pm["engine"], pm["side"]
            st.entry_price, st.sl_price, st.tp_price = fill_px, pm["sl"], pm["tp"]
            st.risk_dist, st.trail_after_r, st.be_act_r, st.be_lock_r = abs(fill_px - pm["sl"]), pm["trail_after_r"], pm["be_act_r"], pm["be_lock_r"]
            st.be_done = st.trailing_active = False
            st.trail_mode, st.qty, st.sl_ticket, st.tp_ticket = None, pm["qty"], None, None
            self.trade_counts[(st.name, pm["engine"])] += 1
            if st.risk_dist <= 0:
                self.liquidate(st.symbol)
                st.in_position = False
                return
            st.sl_ticket = self.stop_market_order(st.symbol, -pm["qty"], pm["sl"], tag=f"{pm['engine']}_SL")
            if st.in_position and pm["tp"] is not None:
                st.tp_ticket = self.limit_order(st.symbol, -pm["qty"], pm["tp"], tag=f"{pm['engine']}_TP")
            return

        if not st.in_position:
            return
        if (st.sl_ticket is None and st.tp_ticket is None) or (st.sl_ticket is not None and oe.order_id == st.sl_ticket.order_id) or (st.tp_ticket is not None and oe.order_id == st.tp_ticket.order_id):
            self.transactions.cancel_open_orders(oe.symbol)
            st.in_position = False
            st.sl_ticket = st.tp_ticket = None

    def on_end_of_algorithm(self) -> None:
        self.log("=== V8 Asset Telemetry ===")
        for st in self.assets.values():
            self.log(f"  {st.name:10s} | bars={st.bars_seen} | submitted={st.orders_submitted} | invalid={self.invalid_counts[st.name]}")
        self.log("=== V8 Trade Breakdown by (Asset, Engine) ===")
        for (asset, eng), cnt in sorted(self.trade_counts.items()):
            self.log(f"  {asset:10s} | {eng:14s}: {cnt} trades")
