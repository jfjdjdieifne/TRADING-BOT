# QUANTCONNECT.COM - SMC V8.2 Multi-Asset Sniper (Elite-4 High-PF, Step-Lock, UTC-Aligned)
# Assets: XAUUSD (OANDA CFD), NAS100USD (OANDA CFD), BTCUSD (Coinbase Crypto)
# Default Elite-4 Sleeves (NSX_1H1m_10R, XAU_LTF1M, VisA disabled for OANDA spread resilience):
#   XAUUSD   : V3_Pro_Clean (15m + BE@1.5R->+0.2R + 1H trail), VisB_Pro (1H->5m + 1H trail)
#   NAS100USD: NSX_AMD_1D (15m+1D + 1H trail)
#   BTCUSD   : BTC_15R_BE (1H->5m >=09h UTC, TP=12R + progressive step-locks)
# Optional param: use_amd_pro=1 enables AMD_Pro (confirm reclaim), risk_scale=1.0 scales sizing.

from AlgorithmImports import *
from collections import defaultdict, deque
import math


class CausalSwingTracker:
    def __init__(self, k: int = 2, max_active: int = 30) -> None:
        self.k = k
        self.max_active = max_active
        self.win = deque(maxlen=2 * k + 1)
        self.bar_idx = -1
        self.last_high = None
        self.last_low = None
        self.trend = 0
        self.act_hi = []
        self.act_lo = []

    def update_hlc(self, h: float, l: float, c: float):
        self.bar_idx += 1
        self.win.append((h, l))
        nh = nl = None
        if len(self.win) == 2 * self.k + 1:
            m = self.k
            ch, cl = self.win[m][0], self.win[m][1]
            if all(ch >= self.win[i][0] for i in range(len(self.win)) if i != m) and any(
                ch > self.win[i][0] for i in range(len(self.win)) if i != m
            ):
                nh = (self.bar_idx - self.k, ch)
                self.last_high = ch
                self.act_hi.append(nh)
                if len(self.act_hi) > self.max_active:
                    self.act_hi.pop(0)
            if all(cl <= self.win[i][1] for i in range(len(self.win)) if i != m) and any(
                cl < self.win[i][1] for i in range(len(self.win)) if i != m
            ):
                nl = (self.bar_idx - self.k, cl)
                self.last_low = cl
                self.act_lo.append(nl)
                if len(self.act_lo) > self.max_active:
                    self.act_lo.pop(0)
        self.act_hi = [x for x in self.act_hi if h <= x[1]]
        self.act_lo = [x for x in self.act_lo if l >= x[1]]
        if self.last_high is not None and c > self.last_high:
            self.trend = 1
        elif self.last_low is not None and c < self.last_low:
            self.trend = -1
        return nh, nl

    def update(self, bar):
        return self.update_hlc(float(bar.High), float(bar.Low), float(bar.Close))


class WilderATR14:
    def __init__(self) -> None:
        self.prev_close = None
        self.trs = []
        self.val = 0.0

    def update(self, h: float, l: float, c: float) -> float:
        tr = (h - l) if self.prev_close is None else max(h - l, abs(h - self.prev_close), abs(l - self.prev_close))
        self.prev_close = c
        if len(self.trs) < 14:
            self.trs.append(tr)
            self.val = sum(self.trs) / len(self.trs)
        else:
            self.val = (self.val * 13.0 + tr) / 14.0
        return self.val


class AssetState:
    def __init__(self, name: str, symbol: Symbol, leverage: float) -> None:
        self.name, self.symbol, self.leverage = name, symbol, leverage
        self.sw_1d, self.sw_4h = CausalSwingTracker(2), CausalSwingTracker(2)
        self.sw_1h, self.sw_1h_k3 = CausalSwingTracker(2), CausalSwingTracker(3)
        self.sw_15m, self.sw_5m, self.sw_ltf = CausalSwingTracker(2), CausalSwingTracker(2), CausalSwingTracker(2)
        self.atr_15m, self.atr_5m, self.atr_ltf = WilderATR14(), WilderATR14(), WilderATR14()
        self.bars_15m, self.bars_5m, self.bars_ltf = deque(maxlen=20), deque(maxlen=15), deque(maxlen=5)
        self.cands_1h_k3_5m, self.cands_1h_k3_ltf, self.amd_manips = [], [], []
        self.b4h_bucket, self.b4h_ohlc = None, None
        self.b1d_date, self.b1d_ohlc = None, None
        self.pending_ticket = self.pending_meta = self.confirm_setup = None
        self.in_position, self.active_engine, self.active_side = False, None, 0
        self.entry_price = self.sl_price = self.risk_dist = self.qty = 0.0
        self.tp_price = self.trail_after_r = self.trail_mode = None
        self.step_locks, self.trailing_active = (), False
        self.sl_ticket = self.tp_ticket = None
        self.ltf_idx = self.idx_5m = self.idx_15m = self.bars_seen = self.orders_submitted = 0


class V8MultiAssetSniperAlgorithm(QCAlgorithm):
    ENGINE_RISK = {
        "VisB_Pro": 0.015,
        "V3_Pro_Clean": 0.015,
        "BTC_15R_BE": 0.015,
        "NSX_AMD_1D": 0.010,
        "AMD_Pro": 0.008,
    }
    BTC_STEPS = ((2.0, 0.2), (3.0, 1.0), (5.0, 2.5), (7.0, 4.5), (9.0, 6.5))

    def initialize(self) -> None:
        self.set_time_zone(TimeZones.UTC)
        self.set_start_date(2020, 2, 1)
        self.set_end_date(2026, 10, 31)
        self.set_cash(100000)
        self.risk_scale = float(self.get_parameter("risk_scale") or 1.0)
        self.use_amd_pro = bool(int(self.get_parameter("use_amd_pro") or 0))
        self.hwm_equity = 100000.0
        self.set_warm_up(timedelta(days=30), Resolution.MINUTE)
        self.set_brokerage_model(DefaultBrokerageModel(AccountType.MARGIN))

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
        self.oco_cleanups = 0
        for sym, st in self.assets.items():
            # UTC-exact 4H and 1D bars are aggregated inside on_1h to avoid OANDA market-break drift
            self.consolidate(sym, timedelta(hours=1), lambda b, s=st: self.on_1h(s, b))
            self.consolidate(sym, timedelta(minutes=15), lambda b, s=st: self.on_15m(s, b))
            self.consolidate(sym, timedelta(minutes=5), lambda b, s=st: self.on_5m(s, b))

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

    def _effective_risk_pct(self, engine: str) -> float:
        eq = float(self.portfolio.total_portfolio_value)
        dd = (self.hwm_equity - eq) / self.hwm_equity if self.hwm_equity > 0 else 0.0
        brake = 0.30 if dd >= 0.09 else (0.50 if dd >= 0.06 else 1.0)
        return self.ENGINE_RISK.get(engine, 0.010) * brake * self.risk_scale

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
        st.pending_ticket = st.pending_meta = st.confirm_setup = None

    def _try_lock_sl(self, st: AssetState, lock_px: float, cur_c: float) -> None:
        lp = self._round_px(st.symbol, lock_px)
        if (st.active_side == 1 and lp > st.sl_price and lp < cur_c) or (
            st.active_side == -1 and lp < st.sl_price and lp > cur_c
        ):
            st.sl_price = lp
            st.sl_ticket.update_stop_price(lp)

    def _floor_sl(self, st: AssetState, side: int, trig: float, sl: float, min_r: float, cur_px: float) -> float:
        floor_r = max(min_r, 1e-6)
        if st.symbol == self.xau_sym:
            floor_r = max(floor_r, cur_px * 0.0020)
        if st.atr_5m.val > 0:
            floor_r = max(floor_r, 1.5 * st.atr_5m.val)
        raw_r = (trig - sl) if side == 1 else (sl - trig)
        if raw_r < floor_r:
            sl = (trig - floor_r) if side == 1 else (trig + floor_r)
        return sl

    def _submit_entry(self, st: AssetState, engine: str, side: int, trig: float, sl: float,
                      tp: float = None, trail_after_r: float = None, step_locks=(),
                      expire_bars: int = 20, min_risk: float = 0.0, skip_hours=None,
                      is_market: bool = False, require_confirm: bool = False) -> None:
        if self.is_warming_up or st.in_position or st.pending_ticket is not None or st.confirm_setup is not None:
            return
        if not self.is_market_open(st.symbol):
            return
        if st.symbol != self.btc_sym and self.time.hour == 22:
            return
        if self.portfolio[st.symbol].invested:
            self.transactions.cancel_open_orders(st.symbol)
            self.liquidate(st.symbol, tag="PRE_ENTRY_SYNC")
            self.oco_cleanups += 1
            return
        cur_px = float(self.securities[st.symbol].price)
        if cur_px <= 0:
            return
        trig_px = cur_px if is_market else self._round_px(st.symbol, trig)
        sl = self._floor_sl(st, side, trig_px, sl, min_risk, cur_px)
        sl_px = self._round_px(st.symbol, sl)
        risk = (trig_px - sl_px) if side == 1 else (sl_px - trig_px)
        if risk <= max(min_risk, 1e-6):
            return
        if not is_market and ((side == 1 and trig_px > cur_px) or (side == -1 and trig_px < cur_px)):
            return
        if require_confirm and not is_market:
            st.confirm_setup = {
                "engine": engine, "side": side, "trig": trig_px, "sl": sl_px,
                "tp": self._round_px(st.symbol, tp) if tp is not None else None,
                "trail_after_r": trail_after_r, "step_locks": step_locks,
                "exp": st.ltf_idx + expire_bars, "skip_hours": skip_hours, "touched": False,
            }
            return

        risk_usd = float(self.portfolio.total_portfolio_value) * self._effective_risk_pct(engine)
        qty = self._round_qty(st.symbol, self._clamp_qty(st, risk_usd / risk, trig_px), side == 1)
        if qty == 0.0:
            return
        st.pending_meta = {
            "engine": engine, "side": side, "trig": trig_px, "sl": sl_px,
            "tp": self._round_px(st.symbol, tp) if tp is not None else None,
            "risk": risk, "qty": qty, "trail_after_r": trail_after_r,
            "step_locks": step_locks, "expire_idx": st.ltf_idx + expire_bars, "skip_hours": skip_hours,
        }
        st.orders_submitted += 1
        ticket = self.market_order(st.symbol, qty, tag=engine) if is_market else self.limit_order(st.symbol, qty, trig_px, tag=engine)
        if ticket.status == OrderStatus.INVALID:
            st.pending_meta = st.pending_ticket = None
            return
        if st.pending_meta is not None:
            st.pending_ticket = ticket

    def _update_utc_htf(self, st: AssetState, dt, o: float, h: float, l: float, c: float) -> None:
        # Flush UTC-aligned 4H and 1D bars immediately on boundary (or bucket change across breaks)
        ref = dt - timedelta(minutes=1)
        b4_key = (ref.date(), ref.hour // 4)
        if st.b4h_bucket is not None and b4_key != st.b4h_bucket and st.b4h_ohlc is not None:
            st.sw_4h.update_hlc(st.b4h_ohlc[1], st.b4h_ohlc[2], st.b4h_ohlc[3])
            st.b4h_ohlc = None
        if st.b4h_ohlc is None:
            st.b4h_ohlc = (o, h, l, c)
        else:
            st.b4h_ohlc = (st.b4h_ohlc[0], max(st.b4h_ohlc[1], h), min(st.b4h_ohlc[2], l), c)
        st.b4h_bucket = b4_key
        if dt.hour % 4 == 0 and dt.minute == 0:
            st.sw_4h.update_hlc(st.b4h_ohlc[1], st.b4h_ohlc[2], st.b4h_ohlc[3])
            st.b4h_ohlc = None

        d_key = ref.date()
        if st.b1d_date is not None and d_key != st.b1d_date and st.b1d_ohlc is not None:
            st.sw_1d.update_hlc(st.b1d_ohlc[1], st.b1d_ohlc[2], st.b1d_ohlc[3])
            st.b1d_ohlc = None
        if st.b1d_ohlc is None:
            st.b1d_ohlc = (o, h, l, c)
        else:
            st.b1d_ohlc = (st.b1d_ohlc[0], max(st.b1d_ohlc[1], h), min(st.b1d_ohlc[2], l), c)
        st.b1d_date = d_key
        if dt.hour == 0 and dt.minute == 0:
            st.sw_1d.update_hlc(st.b1d_ohlc[1], st.b1d_ohlc[2], st.b1d_ohlc[3])
            st.b1d_ohlc = None

    def on_1h(self, st: AssetState, bar) -> None:
        h, l, c, o = float(bar.High), float(bar.Low), float(bar.Close), float(bar.Open)
        self._update_utc_htf(st, bar.EndTime, o, h, l, c)
        k3 = st.sw_1h_k3
        for idx_s, p_lo in list(k3.act_lo):
            if (k3.bar_idx + 1 - idx_s) >= 4 and l < p_lo and c > p_lo:
                if st.symbol == self.xau_sym:
                    st.cands_1h_k3_5m.append({"side": 1, "start_i": st.idx_5m, "sl_base": l, "choch": st.sw_5m.last_high})
                elif st.symbol == self.btc_sym:
                    st.cands_1h_k3_ltf.append({"side": 1, "start_i": st.ltf_idx, "sl_base": l, "choch": st.sw_ltf.last_high})
        for idx_s, p_hi in list(k3.act_hi):
            if (k3.bar_idx + 1 - idx_s) >= 4 and h > p_hi and c < p_hi:
                if st.symbol == self.xau_sym:
                    st.cands_1h_k3_5m.append({"side": -1, "start_i": st.idx_5m, "sl_base": h, "choch": st.sw_5m.last_low})
                elif st.symbol == self.btc_sym:
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

        if st.symbol == self.xau_sym and len(st.bars_15m) >= 3 and self._in_ny(dt) and dt.hour not in (13, 14):
            b1, b2, b3 = st.bars_15m[-3], st.bars_15m[-2], st.bars_15m[-1]
            c2b, buf = abs(b2[4] - b2[1]), max(1.0, 0.75 * a15)
            if st.sw_4h.trend == 1 and st.sw_1h.trend == 1 and st.sw_15m.last_high is not None:
                bos_up = (b2[4] <= st.sw_15m.last_high < b3[4]) or (b1[4] <= st.sw_15m.last_high < b2[4])
                if bos_up and (b3[3] - b1[2]) >= max(0.20, 0.30 * a15) and b2[4] > b2[1] and c2b >= a15:
                    self._submit_entry(st, "V3_Pro_Clean", 1, b3[3], min(b1[3], b2[3]) - buf,
                                       trail_after_r=2.5, step_locks=((1.5, 0.2),), expire_bars=300, min_risk=1.0, skip_hours=(13, 14))
            elif st.sw_4h.trend == -1 and st.sw_1h.trend == -1 and st.sw_15m.last_low is not None:
                bos_dn = (b2[4] >= st.sw_15m.last_low > b3[4]) or (b1[4] >= st.sw_15m.last_low > b2[4])
                if bos_dn and (b1[3] - b3[2]) >= max(0.20, 0.30 * a15) and b2[4] < b2[1] and c2b >= a15:
                    self._submit_entry(st, "V3_Pro_Clean", -1, b3[2], max(b1[2], b2[2]) + buf,
                                       trail_after_r=2.5, step_locks=((1.5, 0.2),), expire_bars=300, min_risk=1.0, skip_hours=(13, 14))

        run_amd = (st.symbol == self.nsx_sym) or (st.symbol == self.xau_sym and self.use_amd_pro)
        if run_amd and len(st.bars_15m) >= 10 and a15 > 0:
            box = list(st.bars_15m)[-9:-1]
            box_hi, box_lo = max(b[2] for b in box), min(b[3] for b in box)
            if (box_hi - box_lo) <= 2.5 * a15:
                if l < box_lo and c >= box_lo - 0.8 * a15:
                    st.amd_manips.append({"side": 1, "r_hi": box_hi, "r_lo": box_lo, "ext": l, "si": st.idx_15m})
                if h > box_hi and c <= box_hi + 0.8 * a15:
                    st.amd_manips.append({"side": -1, "r_hi": box_hi, "r_lo": box_lo, "ext": h, "si": st.idx_15m})
            b1, b2, b3 = st.bars_15m[-3], st.bars_15m[-2], st.bars_15m[-1]
            c2b = abs(b2[4] - b2[1])
            is_nsx = (st.symbol == self.nsx_sym)
            min_r = 5.0 if is_nsx else 0.5
            eng = "NSX_AMD_1D" if is_nsx else "AMD_Pro"
            still = []
            for mp in st.amd_manips:
                if st.idx_15m - mp["si"] > 8:
                    continue
                if mp["side"] == 1:
                    mp["ext"] = min(mp["ext"], l)
                    ok_1d = (not is_nsx) or (st.sw_1d.trend == 1)
                    if ok_1d and c > mp["r_hi"] and (b3[3] - b1[2]) >= 0.25 * a15 and b2[4] > b2[1] and c2b >= 0.8 * a15 and st.sw_1h.trend == 1 and self._in_kz(dt):
                        self._submit_entry(st, eng, 1, b3[3], mp["ext"] - 0.5 * a15, trail_after_r=2.0,
                                           expire_bars=300, min_risk=min_r, require_confirm=(not is_nsx))
                        continue
                else:
                    mp["ext"] = max(mp["ext"], h)
                    ok_1d = (not is_nsx) or (st.sw_1d.trend == -1)
                    if ok_1d and c < mp["r_lo"] and (b1[3] - b3[2]) >= 0.25 * a15 and b2[4] < b2[1] and c2b >= 0.8 * a15 and st.sw_1h.trend == -1 and self._in_kz(dt):
                        self._submit_entry(st, eng, -1, b3[2], mp["ext"] + 0.5 * a15, trail_after_r=2.0,
                                           expire_bars=300, min_risk=min_r, require_confirm=(not is_nsx))
                        continue
                still.append(mp)
            st.amd_manips = still
        st.sw_15m.update(bar)

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

        st.sw_5m.update(bar)
        if st.symbol == self.btc_sym:
            st.atr_5m.val = a5
            self._ltf_bar(st, bar, 9, 0.0, 0.0020, 12.0, self.BTC_STEPS, "BTC_15R_BE", True)

    def on_data(self, data: Slice) -> None:
        for sym, st in self.assets.items():
            bar = self._bar(data, sym)
            if bar is None:
                continue
            st.bars_seen += 1
            if not self.is_warming_up and not st.in_position and st.pending_ticket is None and self.portfolio[sym].invested:
                self.transactions.cancel_open_orders(sym)
                self.liquidate(sym, tag="ORPHAN_SYNC")
                self.oco_cleanups += 1
            if sym != self.btc_sym:
                self._ltf_bar(st, bar, None, 0.0, 0.0, 0.0, (), "", False)

    def _check_confirm_setup(self, st: AssetState, dt, o: float, h: float, l: float, c: float) -> None:
        cs = st.confirm_setup
        if cs is None or st.in_position or st.pending_ticket is not None:
            return
        if st.ltf_idx > cs["exp"] or (cs["skip_hours"] and dt.hour in cs["skip_hours"]) or ((l <= cs["sl"]) if cs["side"] == 1 else (h >= cs["sl"])):
            st.confirm_setup = None
            return
        if not cs["touched"] and ((l <= cs["trig"]) if cs["side"] == 1 else (h >= cs["trig"])):
            cs["touched"] = True
        if cs["touched"]:
            ok_c = (c > o and c > cs["trig"]) if cs["side"] == 1 else (c < o and c < cs["trig"])
            if ok_c:
                st.confirm_setup = None
                self._submit_entry(st, cs["engine"], cs["side"], c, cs["sl"], tp=cs["tp"],
                                   trail_after_r=cs["trail_after_r"], step_locks=cs["step_locks"], is_market=True)

    def _ltf_bar(self, st: AssetState, bar, min_hr, min_abs: float, min_pct: float,
                 fixed_rr: float, step_locks, eng: str, allow_entries: bool) -> None:
        st.ltf_idx += 1
        dt = bar.EndTime
        o, h, l, c = float(bar.Open), float(bar.High), float(bar.Low), float(bar.Close)
        a1 = st.atr_ltf.update(h, l, c)
        st.bars_ltf.append((dt, o, h, l, c))

        if st.in_position and st.risk_dist > 0 and st.sl_ticket is not None:
            if st.sl_ticket.status not in (OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.INVALID):
                for act_r, lk_r in st.step_locks:
                    hit = (h >= st.entry_price + act_r * st.risk_dist) if st.active_side == 1 else (l <= st.entry_price - act_r * st.risk_dist)
                    if hit:
                        self._try_lock_sl(st, st.entry_price + st.active_side * lk_r * st.risk_dist, c)
                if st.trail_after_r is not None and not st.trailing_active:
                    hit_tr = (h >= st.entry_price + st.trail_after_r * st.risk_dist) if st.active_side == 1 else (l <= st.entry_price - st.trail_after_r * st.risk_dist)
                    if hit_tr:
                        st.trailing_active, st.trail_mode = True, "1h"
                        self._try_lock_sl(st, st.entry_price + st.active_side * st.risk_dist, c)

        if st.pending_ticket is not None and st.pending_meta is not None:
            pm = st.pending_meta
            if st.ltf_idx > pm["expire_idx"] or ((l <= pm["sl"]) if pm["side"] == 1 else (h >= pm["sl"])) or (pm["skip_hours"] and dt.hour in pm["skip_hours"]):
                self._cancel_pending(st)

        if not self.is_warming_up:
            self._check_confirm_setup(st, dt, o, h, l, c)

        if allow_entries and len(st.bars_ltf) >= 3 and (min_hr is None or dt.hour >= min_hr) and not self.is_warming_up:
            b1, b2, b3 = st.bars_ltf[-3], st.bars_ltf[-2], st.bars_ltf[-1]
            c2b, buf, min_r = abs(b2[4] - b2[1]), a1, max(min_abs, c * min_pct)
            still = []
            for sc in st.cands_1h_k3_ltf:
                if st.ltf_idx - sc["start_i"] > 60:
                    continue
                if sc["side"] == 1:
                    if l < sc["sl_base"]:
                        continue
                    if st.sw_4h.trend == 1 and st.sw_1h.trend == 1 and sc["choch"] is not None and b3[4] > sc["choch"] and (b3[3] - b1[2]) >= 0.25 * a1 and b2[4] > b2[1] and c2b >= a1:
                        trig, sl = b3[3], sc["sl_base"] - buf
                        sl = self._floor_sl(st, 1, trig, sl, min_r, c)
                        self._submit_entry(st, eng, 1, trig, sl, tp=trig + fixed_rr * (trig - sl), step_locks=step_locks, expire_bars=20, min_risk=min_r)
                        continue
                else:
                    if h > sc["sl_base"]:
                        continue
                    if st.sw_4h.trend == -1 and st.sw_1h.trend == -1 and sc["choch"] is not None and b3[4] < sc["choch"] and (b1[3] - b3[2]) >= 0.25 * a1 and b2[4] < b2[1] and c2b >= a1:
                        trig, sl = b3[2], sc["sl_base"] + buf
                        sl = self._floor_sl(st, -1, trig, sl, min_r, c)
                        self._submit_entry(st, eng, -1, trig, sl, tp=trig - fixed_rr * (sl - trig), step_locks=step_locks, expire_bars=20, min_risk=min_r)
                        continue
                still.append(sc)
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
            st.risk_dist, st.trail_after_r, st.step_locks = abs(fill_px - pm["sl"]), pm["trail_after_r"], pm["step_locks"]
            st.trailing_active, st.trail_mode, st.qty, st.sl_ticket, st.tp_ticket = False, None, pm["qty"], None, None
            self.trade_counts[(st.name, pm["engine"])] += 1
            if st.risk_dist <= 0:
                self.liquidate(st.symbol)
                st.in_position = False
                return
            st.sl_ticket = self.stop_market_order(st.symbol, -pm["qty"], pm["sl"], tag=f"{pm['engine']}_SL")
            if st.in_position and pm["tp"] is not None:
                st.tp_ticket = self.limit_order(st.symbol, -pm["qty"], pm["tp"], tag=f"{pm['engine']}_TP")
            return

        self.transactions.cancel_open_orders(oe.symbol)
        st.in_position = False
        st.sl_ticket = st.tp_ticket = None
        if self.portfolio[oe.symbol].invested:
            self.liquidate(oe.symbol, tag="OCO_STRAY_CLEANUP")
            self.oco_cleanups += 1
        eq_now = float(self.portfolio.total_portfolio_value)
        if eq_now > self.hwm_equity:
            self.hwm_equity = eq_now

    def on_end_of_algorithm(self) -> None:
        self.log(f"=== V8.2 Asset Telemetry (oco_cleanups={self.oco_cleanups}) ===")
        for st in self.assets.values():
            self.log(f"  {st.name:10s} | bars={st.bars_seen} | submitted={st.orders_submitted} | invalid={self.invalid_counts[st.name]}")
        self.log("=== V8.2 Trade Breakdown by (Asset, Engine) ===")
        for (asset, eng), cnt in sorted(self.trade_counts.items()):
            self.log(f"  {asset:10s} | {eng:14s}: {cnt} trades")
