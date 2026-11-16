# region imports
from AlgorithmImports import *
from collections import deque
from datetime import timedelta
import math
# endregion


class CausalSwingTracker:
    """Strict causal k-swing tracker: swing at index i-k confirms only when bar i closes."""

    def __init__(self, k: int = 2, maxlen: int = 220):
        self.k = k
        self.bars = deque(maxlen=max(maxlen, 2 * k + 5))
        self.last_high = None
        self.last_low = None
        self.trend = 0  # +1 bull BOS, -1 bear BOS
        self.prev_high_for_bos = None
        self.prev_low_for_bos = None
        self.active_swings_high = deque(maxlen=60)
        self.active_swings_low = deque(maxlen=60)
        self.bar_idx = -1

    def update(self, bar):
        self.bar_idx += 1
        o, h, l, c = float(bar.Open), float(bar.High), float(bar.Low), float(bar.Close)
        self.bars.append((bar.EndTime, o, h, l, c))
        n = len(self.bars)
        k = self.k
        new_high = None
        new_low = None

        # Causal BOS check on close (matches build_causal_htf_structure)
        if self.prev_high_for_bos is not None and c > self.prev_high_for_bos:
            self.trend = 1
        elif self.prev_low_for_bos is not None and c < self.prev_low_for_bos:
            self.trend = -1

        # Remove swept active levels
        self.active_swings_high = deque([s for s in self.active_swings_high if h <= s[1]], maxlen=60)
        self.active_swings_low = deque([s for s in self.active_swings_low if l >= s[1]], maxlen=60)

        if n >= 2 * k + 1:
            mid = n - 1 - k
            mid_idx = self.bar_idx - k
            mh = self.bars[mid][2]
            ml = self.bars[mid][3]
            if all(self.bars[j][2] <= mh for j in range(mid - k, mid + k + 1) if j != mid):
                self.last_high = mh
                self.prev_high_for_bos = mh
                new_high = (mid_idx, mh)
                if max(self.bars[j][2] for j in range(mid + 1, n)) <= mh:
                    self.active_swings_high.append((mid_idx, mh))
            if all(self.bars[j][3] >= ml for j in range(mid - k, mid + k + 1) if j != mid):
                self.last_low = ml
                self.prev_low_for_bos = ml
                new_low = (mid_idx, ml)
                if min(self.bars[j][3] for j in range(mid + 1, n)) >= ml:
                    self.active_swings_low.append((mid_idx, ml))

        return new_high, new_low


class CausalATR14:
    """Wilder / EWM ATR(14) matching causal_atr14."""

    def __init__(self, period: int = 14):
        self.alpha = 1.0 / period
        self.prev_close = None
        self.value = None

    def update(self, high: float, low: float, close: float) -> float:
        tr = (high - low) if self.prev_close is None else max(
            high - low, abs(high - self.prev_close), abs(low - self.prev_close)
        )
        self.prev_close = close
        self.value = tr if self.value is None else (self.alpha * tr + (1.0 - self.alpha) * self.value)
        return self.value


class AssetState:
    """Per-asset causal state, multi-timeframe trackers, pending limits, and active OCO tickets."""

    def __init__(self, name: str, symbol: Symbol):
        self.name = name
        self.symbol = symbol

        self.sw_ltf = CausalSwingTracker(k=2)     # 1m for XAU/NAS100, 5m for BTC
        self.sw_5m = CausalSwingTracker(k=2)
        self.sw_15m = CausalSwingTracker(k=2)
        self.sw_1h = CausalSwingTracker(k=2)
        self.sw_1h_k3 = CausalSwingTracker(k=3)
        self.sw_4h = CausalSwingTracker(k=2)
        self.sw_1d = CausalSwingTracker(k=2)

        self.atr_ltf = CausalATR14(14)
        self.atr_5m = CausalATR14(14)
        self.atr_15m = CausalATR14(14)

        self.bars_ltf = deque(maxlen=15)
        self.bars_5m = deque(maxlen=15)
        self.bars_15m = deque(maxlen=20)
        self.bars_1h = deque(maxlen=15)

        # Sweep candidate queues
        self.cands_1h_k3_5m = []   # XAU VisB_Pro (1H_k3 -> 5m CHoCH+FVG)
        self.cands_1h_k3_ltf = []  # NSX_1H1m_10R / BTC_15R_BE
        self.cands_15m_k2 = []     # XAU_LTF1M (15m_k2 -> 1m CHoCH+FVG)

        # AMD manipulation queue (15m 8-bar box)
        self.amd_manips = []

        # Pending limit orders (at most 1 active position per asset)
        self.pending = []

        # Active position tracking
        self.in_position = False
        self.active_engine = ""
        self.active_side = 0
        self.entry_price = 0.0
        self.sl_price = 0.0
        self.tp_price = None
        self.risk_dist = 0.0
        self.trail_after_r = None
        self.be_act_r = None
        self.be_lock_r = 1.0
        self.be_done = False
        self.trailing_active = False
        self.trail_mode = None
        self.entry_ticket = None
        self.sl_ticket = None
        self.tp_ticket = None

        self.ltf_idx = 0
        self.idx_5m = 0
        self.idx_15m = 0


class V8MultiAssetSniperAlgorithm(QCAlgorithm):
    """
    SMC V8 Microscopy-Upgraded Multi-Asset Portfolio (XAUUSD + NAS100USD + BTCUSD)
    1-Position-Per-Asset Lock (`V8_3Asset_1PosEach`) — Strictly Zero-Lookahead, UTC-aligned.

    Exact V8 Sleeves:
    - XAUUSD (1m): V3_Pro_Clean (15m BOS+FVG, skip 13-14 UTC) + VisB_Pro (1H_k3 sweep -> 5m CHoCH+FVG)
                   + AMD_Pro (15m 8-bar box sweep+breakout) + XAU_LTF1M (15m_k2 sweep -> 1m, 3R)
    - NAS100USD (1m): NSX_AMD_1D (15m 8-bar box + 1D BOS) + NSX_1H1m_10R (>=09h UTC, 4H BOS, 10R)
    - BTCUSD (5m): BTC_15R_BE (>=09h UTC, 4H+1H BOS, 15R + BE@3.0R -> +1.0R shield)
    """

    def initialize(self) -> None:
        self.set_time_zone(TimeZones.UTC)
        self.set_start_date(2020, 2, 1)
        self.set_end_date(2026, 10, 31)
        self.set_cash(100000)  # $100k ensures NAS100USD (lot_size=1) & 3 concurrent assets size cleanly

        self.risk_pct = float(self.get_parameter("risk_pct") or 0.015)
        self.set_warm_up(timedelta(days=30), Resolution.MINUTE)

        xau_sec = self.add_cfd("XAUUSD", Resolution.MINUTE, Market.OANDA, leverage=50)
        nsx_sec = self.add_cfd("NAS100USD", Resolution.MINUTE, Market.OANDA, leverage=50)
        btc_sec = self.add_crypto("BTCUSD", Resolution.MINUTE, Market.BITFINEX, leverage=10)
        # Enable margin shorting on BTCUSD in the same multi-asset portfolio
        btc_sec.set_buying_power_model(SecurityMarginModel(10.0))

        self.xau_sym = xau_sec.symbol
        self.nsx_sym = nsx_sec.symbol
        self.btc_sym = btc_sec.symbol

        self.assets = {
            self.xau_sym: AssetState("XAUUSD", self.xau_sym),
            self.nsx_sym: AssetState("NAS100USD", self.nsx_sym),
            self.btc_sym: AssetState("BTCUSD", self.btc_sym),
        }

        for sym, st in self.assets.items():
            if sym == self.btc_sym:
                # Consolidate BTC explicitly using QuoteBar/TradeBar safely via standard 5m/15m/1h/4h/1d
                self.consolidate(sym, timedelta(minutes=5), lambda b, s=st: self.on_5m(s, b))
            else:
                self.consolidate(sym, timedelta(minutes=5), lambda b, s=st: self.on_5m(s, b))
            self.consolidate(sym, timedelta(minutes=15), lambda b, s=st: self.on_15m(s, b))
            self.consolidate(sym, timedelta(hours=1), lambda b, s=st: self.on_1h(s, b))
            self.consolidate(sym, timedelta(hours=4), lambda b, s=st: self.on_4h(s, b))
            self.consolidate(sym, timedelta(days=1), lambda b, s=st: self.on_1d(s, b))

    # ------------------------- Helpers -------------------------

    @staticmethod
    def _in_killzone_utc(dt) -> bool:
        h = dt.hour
        return (7 <= h <= 10) or (12 <= h <= 16)

    @staticmethod
    def _extract_bar(data: Slice, sym: Symbol):
        if sym in data.quote_bars:
            return data.quote_bars[sym]
        if sym in data.bars:
            return data.bars[sym]
        return None

    def _round_qty(self, sym: Symbol, raw_qty: float, is_long: bool) -> float:
        sec = self.securities[sym]
        lot = float(sec.symbol_properties.lot_size or 0.01)
        min_size = float(sec.symbol_properties.minimum_order_size or lot)
        steps = math.floor(abs(raw_qty) / lot)
        qty = steps * lot
        if qty < min_size:
            return 0.0
        return qty if is_long else -qty

    def _round_price(self, sym: Symbol, price: float) -> float:
        sec = self.securities[sym]
        tick = float(sec.symbol_properties.minimum_price_variation or 0.01)
        if tick <= 0:
            tick = 0.01
        return round(round(price / tick) * tick, 6)

    def _place_pending(self, st: AssetState, engine: str, side: int, trig: float, sl: float,
                       tp: float = None, trail_after_r: float = None, be_act_r: float = None,
                       be_lock_r: float = 1.0, expire_bars: int = 20, min_risk: float = 0.0,
                       kz_required: bool = True, skip_hours=None) -> None:
        if self.is_warming_up or st.in_position:
            return
        risk = (trig - sl) if side == 1 else (sl - trig)
        if risk <= max(min_risk, 1e-6):
            return
        st.pending.append({
            "engine": engine,
            "side": side,
            "trig": float(trig),
            "sl": float(sl),
            "tp": float(tp) if tp is not None else None,
            "trail_after_r": trail_after_r,
            "be_act_r": be_act_r,
            "be_lock_r": be_lock_r,
            "expire_idx": st.ltf_idx + expire_bars,
            "kz_required": kz_required,
            "skip_hours": skip_hours,
        })

    # ------------------------- HTF Consolidators -------------------------

    def on_1d(self, st: AssetState, bar) -> None:
        st.sw_1d.update(bar)

    def on_4h(self, st: AssetState, bar) -> None:
        st.sw_4h.update(bar)

    def on_1h(self, st: AssetState, bar) -> None:
        h, l, c, o = float(bar.High), float(bar.Low), float(bar.Close), float(bar.Open)
        st.bars_1h.append((bar.EndTime, o, h, l, c))

        # Check 1H_k3 sweeps BEFORE updating sw_1h_k3
        k3 = st.sw_1h_k3
        for idx_s, p_low in list(k3.active_swings_low):
            if (k3.bar_idx + 1 - idx_s) >= 4 and l < p_low and c > p_low:
                if st.symbol == self.xau_sym:
                    st.cands_1h_k3_5m.append({"side": 1, "start_i": st.idx_5m, "sl_base": l, "choch": st.sw_5m.last_high})
                else:
                    st.cands_1h_k3_ltf.append({"side": 1, "start_i": st.ltf_idx, "sl_base": l, "choch": st.sw_ltf.last_high})
        for idx_s, p_hi in list(k3.active_swings_high):
            if (k3.bar_idx + 1 - idx_s) >= 4 and h > p_hi and c < p_hi:
                if st.symbol == self.xau_sym:
                    st.cands_1h_k3_5m.append({"side": -1, "start_i": st.idx_5m, "sl_base": h, "choch": st.sw_5m.last_low})
                else:
                    st.cands_1h_k3_ltf.append({"side": -1, "start_i": st.ltf_idx, "sl_base": h, "choch": st.sw_ltf.last_low})

        nh, nl = st.sw_1h.update(bar)
        st.sw_1h_k3.update(bar)

        # 1H Trailing Stop Update for active position (V3_Pro_Clean, VisB_Pro, AMD_Pro, NSX_AMD_1D)
        if st.in_position and st.trailing_active and st.trail_mode == "1h" and st.sl_ticket is not None:
            if st.sl_ticket.status not in (OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.INVALID):
                if st.active_side == 1 and nl is not None:
                    new_sl = self._round_price(st.symbol, max(st.sl_price, float(nl[1])))
                    if new_sl > st.sl_price and new_sl < c:
                        st.sl_price = new_sl
                        st.sl_ticket.update_stop_price(new_sl)
                elif st.active_side == -1 and nh is not None:
                    new_sl = self._round_price(st.symbol, min(st.sl_price, float(nh[1])))
                    if new_sl < st.sl_price and new_sl > c:
                        st.sl_price = new_sl
                        st.sl_ticket.update_stop_price(new_sl)

    def on_15m(self, st: AssetState, bar) -> None:
        st.idx_15m += 1
        h, l, c, o = float(bar.High), float(bar.Low), float(bar.Close), float(bar.Open)
        a15 = st.atr_15m.update(h, l, c)
        st.bars_15m.append((bar.EndTime, o, h, l, c))
        dt = bar.EndTime

        # 15m_k2 sweeps for XAU_LTF1M
        if st.symbol == self.xau_sym:
            for idx_s, p_low in list(st.sw_15m.active_swings_low):
                if (st.sw_15m.bar_idx + 1 - idx_s) >= 2 and l < p_low and c > p_low:
                    st.cands_15m_k2.append({"side": 1, "start_i": st.ltf_idx, "sl_base": l, "choch": st.sw_ltf.last_high})
            for idx_s, p_hi in list(st.sw_15m.active_swings_high):
                if (st.sw_15m.bar_idx + 1 - idx_s) >= 2 and h > p_hi and c < p_hi:
                    st.cands_15m_k2.append({"side": -1, "start_i": st.ltf_idx, "sl_base": h, "choch": st.sw_ltf.last_low})

        # V3_Pro_Clean on XAUUSD (15m BOS + FVG + 4H&1H dual BOS, skip 13-14 UTC)
        if st.symbol == self.xau_sym and len(st.bars_15m) >= 3 and self._in_killzone_utc(dt) and dt.hour not in (13, 14):
            b1, b2, b3 = st.bars_15m[-3], st.bars_15m[-2], st.bars_15m[-1]
            c2b = abs(b2[4] - b2[1])
            buf = max(1.0, 0.75 * a15)
            if st.sw_4h.trend == 1 and st.sw_1h.trend == 1 and st.sw_15m.last_high is not None:
                gap_l = b3[3] - b1[2]
                bos_up = (b2[4] <= st.sw_15m.last_high and b3[4] > st.sw_15m.last_high) or \
                         (b1[4] <= st.sw_15m.last_high and b2[4] > st.sw_15m.last_high)
                if bos_up and gap_l >= max(0.20, 0.30 * a15) and b2[4] > b2[1] and c2b >= 1.0 * a15:
                    trig = b3[3]
                    sl = min(b1[3], b2[3]) - buf
                    self._place_pending(st, "V3_Pro_Clean", 1, trig, sl, trail_after_r=2.5,
                                        be_lock_r=1.0, expire_bars=300, min_risk=1.0,
                                        kz_required=True, skip_hours=(13, 14))
            elif st.sw_4h.trend == -1 and st.sw_1h.trend == -1 and st.sw_15m.last_low is not None:
                gap_s = b1[3] - b3[2]
                bos_dn = (b2[4] >= st.sw_15m.last_low and b3[4] < st.sw_15m.last_low) or \
                         (b1[4] >= st.sw_15m.last_low and b2[4] < st.sw_15m.last_low)
                if bos_dn and gap_s >= max(0.20, 0.30 * a15) and b2[4] < b2[1] and c2b >= 1.0 * a15:
                    trig = b3[2]
                    sl = max(b1[2], b2[2]) + buf
                    self._place_pending(st, "V3_Pro_Clean", -1, trig, sl, trail_after_r=2.5,
                                        be_lock_r=1.0, expire_bars=300, min_risk=1.0,
                                        kz_required=True, skip_hours=(13, 14))

        # AMD_Pro (XAUUSD) & NSX_AMD_1D (NAS100USD): 8-bar (2h) 15m box sweep + breakout + 1H BOS (+ 1D BOS on NAS100)
        if st.symbol in (self.xau_sym, self.nsx_sym) and len(st.bars_15m) >= 10 and a15 > 0:
            box_bars = list(st.bars_15m)[-9:-1]
            box_hi = max(b[2] for b in box_bars)
            box_lo = min(b[3] for b in box_bars)
            if (box_hi - box_lo) <= 2.0 * a15:
                if l < box_lo and c >= box_lo - 0.8 * a15:
                    st.amd_manips.append({"side": 1, "r_hi": box_hi, "r_lo": box_lo, "ext": l, "si": st.idx_15m})
                if h > box_hi and c <= box_hi + 0.8 * a15:
                    st.amd_manips.append({"side": -1, "r_hi": box_hi, "r_lo": box_lo, "ext": h, "si": st.idx_15m})

            b1, b2, b3 = st.bars_15m[-3], st.bars_15m[-2], st.bars_15m[-1]
            c2b = abs(b2[4] - b2[1])
            still_m = []
            for mp in st.amd_manips:
                if st.idx_15m - mp["si"] > 8:
                    continue
                if mp["side"] == 1:
                    mp["ext"] = min(mp["ext"], l)
                    ok_1d = (st.symbol != self.nsx_sym) or (st.sw_1d.trend == 1)
                    if ok_1d and c > mp["r_hi"] and (b3[3] - b1[2]) >= 0.25 * a15 and b2[4] > b2[1] and c2b >= 1.0 * a15 and st.sw_1h.trend == 1 and self._in_killzone_utc(dt):
                        eng = "NSX_AMD_1D" if st.symbol == self.nsx_sym else "AMD_Pro"
                        self._place_pending(st, eng, 1, b3[3], mp["ext"] - 0.5 * a15, trail_after_r=2.5,
                                            be_lock_r=1.0, expire_bars=300, min_risk=0.5, kz_required=True)
                        continue
                else:
                    mp["ext"] = max(mp["ext"], h)
                    ok_1d = (st.symbol != self.nsx_sym) or (st.sw_1d.trend == -1)
                    if ok_1d and c < mp["r_lo"] and (b1[3] - b3[2]) >= 0.25 * a15 and b2[4] < b2[1] and c2b >= 1.0 * a15 and st.sw_1h.trend == -1 and self._in_killzone_utc(dt):
                        eng = "NSX_AMD_1D" if st.symbol == self.nsx_sym else "AMD_Pro"
                        self._place_pending(st, eng, -1, b3[2], mp["ext"] + 0.5 * a15, trail_after_r=2.5,
                                            be_lock_r=1.0, expire_bars=300, min_risk=0.5, kz_required=True)
                        continue
                still_m.append(mp)
            st.amd_manips = still_m

        st.sw_15m.update(bar)

    def on_5m(self, st: AssetState, bar) -> None:
        st.idx_5m += 1
        h, l, c, o = float(bar.High), float(bar.Low), float(bar.Close), float(bar.Open)
        a5 = st.atr_5m.update(h, l, c)
        st.bars_5m.append((bar.EndTime, o, h, l, c))

        # VisB_Pro on XAUUSD: requires 1H_k3 sweep -> 5m CHoCH + FVG + 4H BOS
        if st.symbol == self.xau_sym and len(st.bars_5m) >= 3 and self._in_killzone_utc(bar.EndTime):
            b1, b2, b3 = st.bars_5m[-3], st.bars_5m[-2], st.bars_5m[-1]
            c2b = abs(b2[4] - b2[1])
            buf = max(1.0, 0.5 * a5)
            still = []
            for sc in st.cands_1h_k3_5m:
                if st.idx_5m - sc["start_i"] > 12:
                    continue
                if sc["side"] == 1:
                    if l < sc["sl_base"]:
                        continue
                    gap = b3[3] - b1[2]
                    if st.sw_4h.trend == 1 and sc["choch"] is not None and c > sc["choch"] and gap >= max(0.20, 0.25 * a5) and b2[4] > b2[1] and c2b >= 1.0 * a5:
                        self._place_pending(st, "VisB_Pro", 1, b3[3], sc["sl_base"] - buf, trail_after_r=2.5,
                                            be_lock_r=1.0, expire_bars=90, min_risk=1.0, kz_required=True)
                        continue
                else:
                    if h > sc["sl_base"]:
                        continue
                    gap = b1[3] - b3[2]
                    if st.sw_4h.trend == -1 and sc["choch"] is not None and c < sc["choch"] and gap >= max(0.20, 0.25 * a5) and b2[4] < b2[1] and c2b >= 1.0 * a5:
                        self._place_pending(st, "VisB_Pro", -1, b3[2], sc["sl_base"] + buf, trail_after_r=2.5,
                                            be_lock_r=1.0, expire_bars=90, min_risk=1.0, kz_required=True)
                        continue
                still.append(sc)
            st.cands_1h_k3_5m = still

        st.sw_5m.update(bar)

        # BTCUSD LTF 5m Sniper Engine (`BTC_15R_BE >= 09:00 UTC`)
        if st.symbol == self.btc_sym:
            self._process_ltf_bar(st, bar, min_hour_utc=9, use_kz=False, min_risk_abs=0.0,
                                  min_risk_pct=0.0020, fixed_rr=15.0, be_act_r=3.0, be_lock_r=1.0,
                                  htf_mode="dual", engine_label="BTC_15R_BE", use_15m_cands=False)

    # ------------------------- 1m OnData -------------------------

    def on_data(self, data: Slice) -> None:
        for sym, st in self.assets.items():
            bar = self._extract_bar(data, sym)
            if bar is None:
                continue
            if sym == self.xau_sym:
                self._process_ltf_bar(st, bar, min_hour_utc=None, use_kz=True, min_risk_abs=2.0,
                                      min_risk_pct=0.0010, fixed_rr=3.0, be_act_r=None, be_lock_r=1.0,
                                      htf_mode="dual", engine_label="XAU_LTF1M", use_15m_cands=True)
            elif sym == self.nsx_sym:
                self._process_ltf_bar(st, bar, min_hour_utc=9, use_kz=True, min_risk_abs=10.0,
                                      min_risk_pct=0.0010, fixed_rr=10.0, be_act_r=None, be_lock_r=1.0,
                                      htf_mode="4h", engine_label="NSX_1H1m_10R", use_15m_cands=False)

    def _process_ltf_bar(self, st: AssetState, bar, *, min_hour_utc, use_kz: bool,
                         min_risk_abs: float, min_risk_pct: float, fixed_rr: float,
                         be_act_r, be_lock_r: float, htf_mode: str, engine_label: str,
                         use_15m_cands: bool) -> None:
        st.ltf_idx += 1
        dt = bar.EndTime
        o, h, l, c = float(bar.Open), float(bar.High), float(bar.Low), float(bar.Close)
        a1 = st.atr_ltf.update(h, l, c)
        st.bars_ltf.append((dt, o, h, l, c))

        # 1) Manage active position BE / Trailing activation
        if st.in_position and st.risk_dist > 0 and st.sl_ticket is not None:
            can_update_sl = st.sl_ticket.status not in (OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.INVALID)
            if st.be_act_r is not None and not st.be_done and can_update_sl:
                hit_be = (h >= st.entry_price + st.be_act_r * st.risk_dist) if st.active_side == 1 \
                    else (l <= st.entry_price - st.be_act_r * st.risk_dist)
                if hit_be:
                    st.be_done = True
                    lock_px = self._round_price(
                        st.symbol,
                        st.entry_price + st.be_lock_r * st.risk_dist if st.active_side == 1
                        else st.entry_price - st.be_lock_r * st.risk_dist,
                    )
                    if (st.active_side == 1 and lock_px > st.sl_price and lock_px < c) or \
                       (st.active_side == -1 and lock_px < st.sl_price and lock_px > c):
                        st.sl_price = lock_px
                        st.sl_ticket.update_stop_price(lock_px)
            if st.trail_after_r is not None and not st.trailing_active and can_update_sl:
                hit_tr = (h >= st.entry_price + st.trail_after_r * st.risk_dist) if st.active_side == 1 \
                    else (l <= st.entry_price - st.trail_after_r * st.risk_dist)
                if hit_tr:
                    st.trailing_active = True
                    st.trail_mode = "1h"
                    lock_px = self._round_price(
                        st.symbol,
                        st.entry_price + st.be_lock_r * st.risk_dist if st.active_side == 1
                        else st.entry_price - st.be_lock_r * st.risk_dist,
                    )
                    if (st.active_side == 1 and lock_px > st.sl_price and lock_px < c) or \
                       (st.active_side == -1 and lock_px < st.sl_price and lock_px > c):
                        st.sl_price = lock_px
                        st.sl_ticket.update_stop_price(lock_px)

        # 2) Check pending limit fills causally
        new_pending = []
        for p in st.pending:
            if st.ltf_idx > p["expire_idx"]:
                continue
            p_kz_ok = (not p["kz_required"]) or self._in_killzone_utc(dt)
            if p["skip_hours"] and dt.hour in p["skip_hours"]:
                p_kz_ok = False
            if p["side"] == 1:
                if o <= p["sl"] or l <= p["sl"]:
                    continue
                if l <= p["trig"]:
                    if st.in_position or not p_kz_ok or not self.is_market_open(st.symbol):
                        if not st.in_position:
                            new_pending.append(p)
                        continue
                    self._execute_entry(st, p)
                    continue
            else:
                if o >= p["sl"] or h >= p["sl"]:
                    continue
                if h >= p["trig"]:
                    if st.in_position or not p_kz_ok or not self.is_market_open(st.symbol):
                        if not st.in_position:
                            new_pending.append(p)
                        continue
                    self._execute_entry(st, p)
                    continue
            new_pending.append(p)
        st.pending = new_pending

        # 3) Detect LTF CHoCH + FVG setups from active HTF sweeps
        kz_ok = ((not use_kz) or self._in_killzone_utc(dt)) and (min_hour_utc is None or dt.hour >= min_hour_utc)
        cands = st.cands_15m_k2 if use_15m_cands else st.cands_1h_k3_ltf
        max_wait = 20 if use_15m_cands else 60
        if len(st.bars_ltf) >= 3 and kz_ok and not self.is_warming_up:
            b1, b2, b3 = st.bars_ltf[-3], st.bars_ltf[-2], st.bars_ltf[-1]
            c2b = abs(b2[4] - b2[1])
            buf = 1.0 * a1
            min_r = max(min_risk_abs, c * min_risk_pct)
            still = []
            for sc in cands:
                if st.ltf_idx - sc["start_i"] > max_wait:
                    continue
                if sc["side"] == 1:
                    if l < sc["sl_base"]:
                        continue
                    ok_htf = (st.sw_4h.trend == 1) and (htf_mode != "dual" or st.sw_1h.trend == 1)
                    if ok_htf and sc["choch"] is not None and b3[4] > sc["choch"] and (b3[3] - b1[2]) >= 0.25 * a1 and b2[4] > b2[1] and c2b >= a1:
                        trig = b3[3]
                        sl = sc["sl_base"] - buf
                        tp = trig + fixed_rr * (trig - sl)
                        self._place_pending(st, engine_label, 1, trig, sl, tp=tp, be_act_r=be_act_r,
                                            be_lock_r=be_lock_r, expire_bars=20, min_risk=min_r,
                                            kz_required=use_kz)
                        continue
                else:
                    if h > sc["sl_base"]:
                        continue
                    ok_htf = (st.sw_4h.trend == -1) and (htf_mode != "dual" or st.sw_1h.trend == -1)
                    if ok_htf and sc["choch"] is not None and b3[4] < sc["choch"] and (b1[3] - b3[2]) >= 0.25 * a1 and b2[4] < b2[1] and c2b >= a1:
                        trig = b3[2]
                        sl = sc["sl_base"] + buf
                        tp = trig - fixed_rr * (sl - trig)
                        self._place_pending(st, engine_label, -1, trig, sl, tp=tp, be_act_r=be_act_r,
                                            be_lock_r=be_lock_r, expire_bars=20, min_risk=min_r,
                                            kz_required=use_kz)
                        continue
                still.append(sc)
            if use_15m_cands:
                st.cands_15m_k2 = still
            else:
                st.cands_1h_k3_ltf = still

        st.sw_ltf.update(bar)

    def _execute_entry(self, st: AssetState, p: dict) -> None:
        fill_est = p["trig"]
        risk_per_unit = abs(fill_est - p["sl"])
        if risk_per_unit <= 0:
            return
        risk_usd = float(self.portfolio.total_portfolio_value) * self.risk_pct
        raw_qty = risk_usd / risk_per_unit
        qty = self._round_qty(st.symbol, raw_qty, p["side"] == 1)
        if qty == 0.0:
            return

        st.in_position = True
        st.active_engine = p["engine"]
        st.active_side = p["side"]
        st.entry_price = fill_est
        st.sl_price = self._round_price(st.symbol, p["sl"])
        st.tp_price = self._round_price(st.symbol, p["tp"]) if p["tp"] is not None else None
        st.risk_dist = risk_per_unit
        st.trail_after_r = p["trail_after_r"]
        st.be_act_r = p["be_act_r"]
        st.be_lock_r = p["be_lock_r"]
        st.be_done = False
        st.trailing_active = False
        st.trail_mode = None
        st.pending = []

        st.entry_ticket = self.market_order(st.symbol, qty, tag=p["engine"])
        if st.entry_ticket.status == OrderStatus.FILLED and st.entry_ticket.average_fill_price > 0:
            st.entry_price = float(st.entry_ticket.average_fill_price)
            st.risk_dist = abs(st.entry_price - st.sl_price)
        st.sl_ticket = self.stop_market_order(st.symbol, -qty, st.sl_price, tag=f"{p['engine']}_SL")
        if st.tp_price is not None:
            st.tp_ticket = self.limit_order(st.symbol, -qty, st.tp_price, tag=f"{p['engine']}_TP")
        else:
            st.tp_ticket = None

    def on_order_event(self, order_event: OrderEvent) -> None:
        if order_event.status != OrderStatus.FILLED:
            return
        sym = order_event.symbol
        if sym not in self.assets:
            return
        st = self.assets[sym]
        if not st.in_position:
            return

        if st.entry_ticket is not None and order_event.order_id == st.entry_ticket.order_id:
            st.entry_price = float(order_event.fill_price)
            st.risk_dist = abs(st.entry_price - st.sl_price)
            return

        is_sl = st.sl_ticket is not None and order_event.order_id == st.sl_ticket.order_id
        is_tp = st.tp_ticket is not None and order_event.order_id == st.tp_ticket.order_id
        if is_sl or is_tp:
            self.transactions.cancel_open_orders(sym)
            st.in_position = False
            st.entry_ticket = None
            st.sl_ticket = None
            st.tp_ticket = None
