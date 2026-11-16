# region imports
from AlgorithmImports import *
from collections import deque
from datetime import timedelta
import math
# endregion


class CausalSwingTracker:
    """Strict causal k-swing tracker: swing at index i-k confirms only when bar i closes."""

    def __init__(self, k: int = 2, maxlen: int = 200):
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
        self.bars.append((bar.EndTime, float(bar.Open), float(bar.High), float(bar.Low), float(bar.Close)))
        n = len(self.bars)
        k = self.k
        new_high = None
        new_low = None
        c_close = float(bar.Close)
        c_high = float(bar.High)
        c_low = float(bar.Low)

        # BOS check on close (matches build_causal_htf_structure)
        if self.prev_high_for_bos is not None and c_close > self.prev_high_for_bos:
            self.trend = 1
        elif self.prev_low_for_bos is not None and c_close < self.prev_low_for_bos:
            self.trend = -1

        # Invalidate swept active levels prior to adding newly confirmed swing
        self.active_swings_high = deque([s for s in self.active_swings_high if c_high <= s[1]], maxlen=60)
        self.active_swings_low = deque([s for s in self.active_swings_low if c_low >= s[1]], maxlen=60)

        if n >= 2 * k + 1:
            mid = n - 1 - k
            mid_idx = self.bar_idx - k
            mh = self.bars[mid][2]
            ml = self.bars[mid][3]
            is_sh = all(self.bars[j][2] <= mh for j in range(mid - k, mid + k + 1) if j != mid)
            is_sl = all(self.bars[j][3] >= ml for j in range(mid - k, mid + k + 1) if j != mid)
            if is_sh:
                self.last_high = mh
                self.prev_high_for_bos = mh
                new_high = (mid_idx, mh)
                # Ensure swing high wasn't already broken during confirmation window [mid+1 .. n-1]
                if max(self.bars[j][2] for j in range(mid + 1, n)) <= mh:
                    self.active_swings_high.append((mid_idx, mh))
            if is_sl:
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
        if self.prev_close is None:
            tr = high - low
        else:
            tr = max(high - low, abs(high - self.prev_close), abs(low - self.prev_close))
        self.prev_close = close
        if self.value is None:
            self.value = tr
        else:
            self.value = self.alpha * tr + (1.0 - self.alpha) * self.value
        return self.value


class AssetState:
    """Per-asset causal state, multi-timeframe trackers, pending limit, and active OCO tickets."""

    def __init__(self, name: str, symbol: Symbol, is_crypto: bool = False):
        self.name = name
        self.symbol = symbol
        self.is_crypto = is_crypto

        # Multi-timeframe trackers
        self.sw_ltf = CausalSwingTracker(k=2)   # 1m (or 5m for BTC)
        self.sw_5m = CausalSwingTracker(k=2)
        self.sw_15m = CausalSwingTracker(k=2)
        self.sw_1h = CausalSwingTracker(k=2)
        self.sw_1h_k3 = CausalSwingTracker(k=3)
        self.sw_4h = CausalSwingTracker(k=2)
        self.sw_1d = CausalSwingTracker(k=2)

        self.atr_ltf = CausalATR14(14)
        self.atr_5m = CausalATR14(14)
        self.atr_15m = CausalATR14(14)
        self.atr_1h = CausalATR14(14)

        self.bars_ltf = deque(maxlen=15)
        self.bars_5m = deque(maxlen=15)
        self.bars_15m = deque(maxlen=15)
        self.bars_1h = deque(maxlen=15)

        # Sniper HTF-sweep candidate queues
        self.cands_1h_k3 = []   # for XAU_1H1m, NSX_1H1m_10R, BTC_15R_BE
        self.cands_15m_k2 = []  # for XAU_LTF1M

        # AMD manipulation state (15m)
        self.amd_asian_hi = None
        self.amd_asian_lo = None
        self.amd_asian_day = None
        self.amd_manips = []

        # Pending limit orders (max 1 active position per asset; pending cancelled on fill/expiry)
        self.pending = []  # list of dicts

        # Active position tracking
        self.in_position = False
        self.active_engine = ""
        self.active_side = 0      # +1 long, -1 short
        self.entry_price = 0.0
        self.sl_price = 0.0
        self.tp_price = 0.0
        self.risk_dist = 0.0
        self.trail_after_r = None
        self.be_act_r = None
        self.be_lock_r = 1.0
        self.be_done = False
        self.trailing_active = False
        self.trail_mode = None    # "1h" or None
        self.qty = 0.0
        self.entry_ticket = None
        self.sl_ticket = None
        self.tp_ticket = None
        self.ltf_idx = 0


class V8MultiAssetSniperAlgorithm(QCAlgorithm):
    """
    SMC V8 Microscopy-Upgraded Multi-Asset Portfolio (XAUUSD + NAS100USD + BTCUSD)
    1-Position-Per-Asset Lock (`V8_3Asset_1PosEach`) — Strictly Zero-Lookahead.

    Upgrades included from V8 forensic microscopy:
    1. XAUUSD (1m): V3_Pro_Clean (drops 13-14 UTC chop) + VisB_Pro + VisA + AMD_Pro + XAU_LTF1M (3R)
    2. NAS100USD (1m): NSX_AMD_1D (1D BOS aligned) + NSX_1H1m_10R (>= 09:00 UTC, 4H aligned, 10R TP)
    3. BTCUSD (5m): BTC_15R_BE (>= 09:00 UTC, 4H+1H aligned, 15R TP + BE@3.0R -> +1.0R shield)
    """

    def initialize(self) -> None:
        self.set_start_date(2020, 2, 1)
        self.set_end_date(2026, 10, 31)
        self.set_cash(10000)  # Adjust starting cash as desired (e.g. 100 or 10000)

        self.risk_pct = float(self.get_parameter("risk_pct") or 0.015)
        self.set_warm_up(timedelta(days=30), Resolution.MINUTE)

        # Subscribe to 3 uncorrelated instruments in one USD Margin portfolio (supports both Long & Short)
        xau_sym = self.add_cfd("XAUUSD", Resolution.MINUTE, Market.OANDA).symbol
        nsx_sym = self.add_cfd("NAS100USD", Resolution.MINUTE, Market.OANDA).symbol
        btc_sym = self.add_crypto("BTCUSD", Resolution.MINUTE, Market.BITFINEX, leverage=10).symbol

        self.assets = {
            xau_sym: AssetState("XAUUSD", xau_sym, is_crypto=False),
            nsx_sym: AssetState("NAS100USD", nsx_sym, is_crypto=False),
            btc_sym: AssetState("BTCUSD", btc_sym, is_crypto=True),
        }
        self.xau_sym = xau_sym
        self.nsx_sym = nsx_sym
        self.btc_sym = btc_sym

        # Register causal consolidators (on_data receives 1m; BTC consolidates to 5m for its LTF engine)
        for sym, st in self.assets.items():
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
        lot = float(sec.symbol_properties.lot_size or 1.0)
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
                       be_lock_r: float = 1.0, expire_bars: int = 20, min_risk: float = 0.0) -> None:
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
        })

    # ------------------------- HTF Consolidators -------------------------

    def on_1d(self, st: AssetState, bar) -> None:
        st.sw_1d.update(bar)

    def on_4h(self, st: AssetState, bar) -> None:
        st.sw_4h.update(bar)

    def on_1h(self, st: AssetState, bar) -> None:
        h = float(bar.High)
        l = float(bar.Low)
        c = float(bar.Close)
        o = float(bar.Open)
        st.atr_1h.update(h, l, c)
        st.bars_1h.append((bar.EndTime, o, h, l, c))

        # Check 1H_k3 sweeps BEFORE updating sw_1h_k3
        k3 = st.sw_1h_k3
        for idx_s, p_low in list(k3.active_swings_low):
            if (k3.bar_idx + 1 - idx_s) >= 4 and l < p_low and c > p_low:
                st.cands_1h_k3.append({"side": 1, "start_idx": st.ltf_idx, "sl_base": l, "choch": st.sw_ltf.last_high})
        for idx_s, p_hi in list(k3.active_swings_high):
            if (k3.bar_idx + 1 - idx_s) >= 4 and h > p_hi and c < p_hi:
                st.cands_1h_k3.append({"side": -1, "start_idx": st.ltf_idx, "sl_base": h, "choch": st.sw_ltf.last_low})

        nh, nl = st.sw_1h.update(bar)
        st.sw_1h_k3.update(bar)

        # 1H Trailing Stop Update for active position (V3_Pro, VisB_Pro, AMD_Pro, NSX_AMD_1D)
        if st.in_position and st.trailing_active and st.trail_mode == "1h" and st.sl_ticket is not None:
            if st.sl_ticket.status not in (OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.INVALID):
                if st.active_side == 1 and nl is not None:
                    new_sl = self._round_price(st.symbol, max(st.sl_price, float(nl[1])))
                    if new_sl > st.sl_price and new_sl < float(bar.Close):
                        st.sl_price = new_sl
                        st.sl_ticket.update_stop_price(new_sl)
                elif st.active_side == -1 and nh is not None:
                    new_sl = self._round_price(st.symbol, min(st.sl_price, float(nh[1])))
                    if new_sl < st.sl_price and new_sl > float(bar.Close):
                        st.sl_price = new_sl
                        st.sl_ticket.update_stop_price(new_sl)

        # V3_Pro_Clean on XAUUSD (1H FVG + 4H BOS, skip 13:00-14:59 UTC)
        if st.symbol == self.xau_sym and len(st.bars_1h) >= 3 and st.atr_1h.value is not None:
            dt = bar.EndTime
            if self._in_killzone_utc(dt) and dt.hour not in (13, 14) and st.sw_4h.trend != 0:
                b1, b2, b3 = st.bars_1h[-3], st.bars_1h[-2], st.bars_1h[-1]
                a = st.atr_1h.value
                buf = 0.75 * a
                if st.sw_4h.trend == 1 and b3[3] - b1[2] >= 0.20 * a and b2[4] > b2[1]:
                    trig, sl = b3[3], b2[3] - buf
                    self._place_pending(st, "V3_Pro_Clean", 1, trig, sl, trail_after_r=2.0,
                                        be_lock_r=1.0, expire_bars=180, min_risk=2.0)
                elif st.sw_4h.trend == -1 and b1[3] - b3[2] >= 0.20 * a and b2[4] < b2[1]:
                    trig, sl = b3[2], b2[2] + buf
                    self._place_pending(st, "V3_Pro_Clean", -1, trig, sl, trail_after_r=2.0,
                                        be_lock_r=1.0, expire_bars=180, min_risk=2.0)

    def on_15m(self, st: AssetState, bar) -> None:
        h, l, c, o = float(bar.High), float(bar.Low), float(bar.Close), float(bar.Open)
        a15 = st.atr_15m.update(h, l, c)
        st.bars_15m.append((bar.EndTime, o, h, l, c))

        # Check 15m_k2 sweeps for XAU_LTF1M
        if st.symbol == self.xau_sym:
            for idx_s, p_low in list(st.sw_15m.active_swings_low):
                if (st.sw_15m.bar_idx + 1 - idx_s) >= 2 and l < p_low and c > p_low:
                    st.cands_15m_k2.append({"side": 1, "start_idx": st.ltf_idx, "sl_base": l, "choch": st.sw_ltf.last_high})
            for idx_s, p_hi in list(st.sw_15m.active_swings_high):
                if (st.sw_15m.bar_idx + 1 - idx_s) >= 2 and h > p_hi and c < p_hi:
                    st.cands_15m_k2.append({"side": -1, "start_idx": st.ltf_idx, "sl_base": h, "choch": st.sw_ltf.last_low})

        st.sw_15m.update(bar)

        # Asian range (00:00-05:59 UTC) for AMD_Pro (XAU) & NSX_AMD_1D (NAS100)
        dt = bar.EndTime
        day_key = dt.date()
        if st.amd_asian_day != day_key:
            st.amd_asian_day = day_key
            st.amd_asian_hi = None
            st.amd_asian_lo = None
        if dt.hour < 6:
            st.amd_asian_hi = h if st.amd_asian_hi is None else max(st.amd_asian_hi, h)
            st.amd_asian_lo = l if st.amd_asian_lo is None else min(st.amd_asian_lo, l)
        elif st.amd_asian_hi is not None and st.amd_asian_lo is not None and self._in_killzone_utc(dt):
            if l < st.amd_asian_lo and c > st.amd_asian_lo:
                st.amd_manips.append({"side": 1, "sl_base": l, "exp": st.ltf_idx + 120})
            if h > st.amd_asian_hi and c < st.amd_asian_hi:
                st.amd_manips.append({"side": -1, "sl_base": h, "exp": st.ltf_idx + 120})

        # AMD_Pro (XAU) / NSX_AMD_1D (NAS100) FVG entry after Asian sweep
        if st.symbol in (self.xau_sym, self.nsx_sym) and len(st.bars_15m) >= 3 and self._in_killzone_utc(dt):
            b1, b2, b3 = st.bars_15m[-3], st.bars_15m[-2], st.bars_15m[-1]
            still = []
            for mp in st.amd_manips:
                if st.ltf_idx > mp["exp"]:
                    continue
                if mp["side"] == 1:
                    if st.symbol == self.nsx_sym and st.sw_1d.trend != 1:
                        still.append(mp)
                        continue
                    if b3[3] - b1[2] >= 0.25 * a15 and b2[4] > b2[1]:
                        trig, sl = b3[3], mp["sl_base"] - a15
                        min_r = 2.0 if st.symbol == self.xau_sym else 10.0
                        eng = "AMD_Pro" if st.symbol == self.xau_sym else "NSX_AMD_1D"
                        self._place_pending(st, eng, 1, trig, sl, trail_after_r=2.0,
                                            be_lock_r=1.0, expire_bars=90, min_risk=min_r)
                        continue
                else:
                    if st.symbol == self.nsx_sym and st.sw_1d.trend != -1:
                        still.append(mp)
                        continue
                    if b1[3] - b3[2] >= 0.25 * a15 and b2[4] < b2[1]:
                        trig, sl = b3[2], mp["sl_base"] + a15
                        min_r = 2.0 if st.symbol == self.xau_sym else 10.0
                        eng = "AMD_Pro" if st.symbol == self.xau_sym else "NSX_AMD_1D"
                        self._place_pending(st, eng, -1, trig, sl, trail_after_r=2.0,
                                            be_lock_r=1.0, expire_bars=90, min_risk=min_r)
                        continue
                still.append(mp)
            st.amd_manips = still

    def on_5m(self, st: AssetState, bar) -> None:
        h, l, c, o = float(bar.High), float(bar.Low), float(bar.Close), float(bar.Open)
        a5 = st.atr_5m.update(h, l, c)
        st.bars_5m.append((bar.EndTime, o, h, l, c))

        # VisB_Pro & VisA on XAUUSD (5m)
        if st.symbol == self.xau_sym and len(st.bars_5m) >= 3 and self._in_killzone_utc(bar.EndTime):
            b1, b2, b3 = st.bars_5m[-3], st.bars_5m[-2], st.bars_5m[-1]
            c2b = abs(b2[4] - b2[1])
            if st.sw_4h.trend == 1 and st.sw_1h.trend == 1:
                if b3[3] - b1[2] >= 0.25 * a5 and b2[4] > b2[1] and c2b >= 1.0 * a5:
                    self._place_pending(st, "VisB_Pro", 1, b3[3], b2[3] - a5, trail_after_r=2.0,
                                        be_lock_r=1.0, expire_bars=60, min_risk=2.0)
            elif st.sw_4h.trend == -1 and st.sw_1h.trend == -1:
                if b1[3] - b3[2] >= 0.25 * a5 and b2[4] < b2[1] and c2b >= 1.0 * a5:
                    self._place_pending(st, "VisB_Pro", -1, b3[2], b2[2] + a5, trail_after_r=2.0,
                                        be_lock_r=1.0, expire_bars=60, min_risk=2.0)

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
        kz_ok = ((not use_kz) or self._in_killzone_utc(dt)) and (min_hour_utc is None or dt.hour >= min_hour_utc)
        new_pending = []
        for p in st.pending:
            if st.ltf_idx > p["expire_idx"]:
                continue
            if p["side"] == 1:
                if o <= p["sl"] or l <= p["sl"]:
                    continue
                if l <= p["trig"]:
                    if st.in_position or not kz_ok:
                        if not st.in_position:
                            new_pending.append(p)
                        continue
                    self._execute_entry(st, p)
                    continue
            else:
                if o >= p["sl"] or h >= p["sl"]:
                    continue
                if h >= p["trig"]:
                    if st.in_position or not kz_ok:
                        if not st.in_position:
                            new_pending.append(p)
                        continue
                    self._execute_entry(st, p)
                    continue
            new_pending.append(p)
        st.pending = new_pending

        # 3) Detect LTF CHoCH + FVG setups from active HTF sweeps
        cands = st.cands_15m_k2 if use_15m_cands else st.cands_1h_k3
        max_wait = 20 if use_15m_cands else 60
        if len(st.bars_ltf) >= 3 and kz_ok and not self.is_warming_up:
            b1, b2, b3 = st.bars_ltf[-3], st.bars_ltf[-2], st.bars_ltf[-1]
            c2b = abs(b2[4] - b2[1])
            buf = 1.0 * a1
            min_r = max(min_risk_abs, c * min_risk_pct)
            still = []
            for sc in cands:
                if st.ltf_idx - sc["start_idx"] > max_wait:
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
                                            be_lock_r=be_lock_r, expire_bars=20, min_risk=min_r)
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
                                            be_lock_r=be_lock_r, expire_bars=20, min_risk=min_r)
                        continue
                still.append(sc)
            if use_15m_cands:
                st.cands_15m_k2 = still
            else:
                st.cands_1h_k3 = still

        st.sw_ltf.update(bar)

    def _execute_entry(self, st: AssetState, p: dict) -> None:
        sec = self.securities[st.symbol]
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
        st.qty = qty
        st.pending = []  # Clear remaining pending orders for this asset

        st.entry_ticket = self.market_order(st.symbol, qty, tag=p["engine"])
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
