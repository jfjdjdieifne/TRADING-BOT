# QUANTCONNECT.COM - V9 execution and preserved V8 sleeves
# This file is imported by V9_3Asset_1PosEach_DynamicProfile_QC.py.

from AlgorithmImports import *
from smc_core import AssetState


class V9ExecutionMixin:
    """Order lifecycle, risk controls, and the preserved V8 sleeve runtime."""

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
        sec = self.securities[st.symbol]
        ref_long = float(getattr(sec, "bid_price", 0.0) or 0.0)
        ref_short = float(getattr(sec, "ask_price", 0.0) or 0.0)
        ref_long = ref_long if ref_long > 0 else cur_c
        ref_short = ref_short if ref_short > 0 else cur_c
        if (st.active_side == 1 and lp > st.sl_price and lp < ref_long) or (
            st.active_side == -1 and lp < st.sl_price and lp > ref_short
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
                      is_market: bool = False, require_confirm: bool = False,
                      apply_floor: bool = True, expire_on_15m: bool = False) -> None:
        if self.is_warming_up or st.in_position or st.pending_ticket is not None or st.confirm_setup is not None:
            return
        if not self.is_market_open(st.symbol) or self._cfd_blocked(st, self.utc_time):
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
        if apply_floor:
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
            "expire_idx": st.ltf_idx + expire_bars,
            "expire_15m_idx": st.idx_15m + expire_bars if expire_on_15m else None,
            "skip_hours": skip_hours,
        }
        st.orders_submitted += 1
        ticket = self.market_order(st.symbol, qty, tag=engine) if is_market else self.limit_order(st.symbol, qty, trig_px, tag=engine)
        if ticket.status == OrderStatus.INVALID:
            st.pending_meta = st.pending_ticket = None
            return
        if st.pending_meta is not None:
            st.pending_ticket = ticket

    def _push_1d(self, st: AssetState, h: float, l: float, c: float) -> None:
        st.sw_1d.update_hlc(h, l, c)
        st.d1_closes.append(c)
        st.d1_last_c = c
        k = 2.0 / 21.0
        st.d1_ema20 = c if st.d1_ema20 is None else (c * k + st.d1_ema20 * (1.0 - k))
        if len(st.d1_closes) >= 15:
            arr = list(st.d1_closes)[-15:]
            den = sum(abs(arr[j] - arr[j - 1]) for j in range(1, len(arr)))
            st.d1_er14 = abs(arr[-1] - arr[0]) / den if den > 0 else 0.0

    def _update_utc_htf(self, st: AssetState, dt, o: float, h: float, l: float, c: float) -> None:
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
            self._push_1d(st, st.b1d_ohlc[1], st.b1d_ohlc[2], st.b1d_ohlc[3])
            st.b1d_ohlc = None
        if st.b1d_ohlc is None:
            st.b1d_ohlc = (o, h, l, c)
        else:
            st.b1d_ohlc = (st.b1d_ohlc[0], max(st.b1d_ohlc[1], h), min(st.b1d_ohlc[2], l), c)
        st.b1d_date = d_key
        if dt.hour == 0 and dt.minute == 0:
            self._push_1d(st, st.b1d_ohlc[1], st.b1d_ohlc[2], st.b1d_ohlc[3])
            st.b1d_ohlc = None

    def on_1h(self, st: AssetState, bar) -> None:
        h, l, c, o = float(bar.High), float(bar.Low), float(bar.Close), float(bar.Open)
        self._update_utc_htf(st, self.utc_time, o, h, l, c)
        k3 = st.sw_1h_k3
        for idx_s, p_lo in list(k3.act_lo):
            if (k3.bar_idx + 1 - idx_s) >= 4 and l < p_lo and c > p_lo:
                if self.enable_v9_profiles:
                    st.v9_sweeps.append({"side": 1, "start_i": st.idx_15m, "level": p_lo, "extreme": l})
                    st.v9_sweeps = st.v9_sweeps[-30:]
                if st.symbol == self.xau_sym or (st.symbol == self.nsx_sym and st.d1_er14 < 0.25):
                    st.cands_1h_k3_5m.append({"side": 1, "start_i": st.idx_5m, "sl_base": l, "choch": st.sw_5m.last_high})
                elif st.symbol == self.btc_sym:
                    st.cands_1h_k3_ltf.append({"side": 1, "start_i": st.ltf_idx, "sl_base": l, "choch": st.sw_ltf.last_high})
        for idx_s, p_hi in list(k3.act_hi):
            if (k3.bar_idx + 1 - idx_s) >= 4 and h > p_hi and c < p_hi:
                if self.enable_v9_profiles:
                    st.v9_sweeps.append({"side": -1, "start_i": st.idx_15m, "level": p_hi, "extreme": h})
                    st.v9_sweeps = st.v9_sweeps[-30:]
                if st.symbol == self.xau_sym or (st.symbol == self.nsx_sym and st.d1_er14 < 0.25):
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
        dt = self.utc_time
        h, l, c, o = float(bar.High), float(bar.Low), float(bar.Close), float(bar.Open)
        atr_before = st.atr_15m.val
        a15 = st.atr_15m.update(h, l, c)
        st.bars_15m.append((dt, o, h, l, c))

        if st.symbol == self.xau_sym and len(st.bars_15m) >= 3 and self._in_ny(dt) and dt.hour not in (13, 14):
            b1, b2, b3 = st.bars_15m[-3], st.bars_15m[-2], st.bars_15m[-1]
            c2b, buf = abs(b2[4] - b2[1]), max(1.0, 0.75 * a15)
            if st.sw_4h.trend == 1 and st.sw_1h.trend == 1 and st.sw_15m.last_high is not None:
                bos_up = (b2[4] <= st.sw_15m.last_high < b3[4]) or (b1[4] <= st.sw_15m.last_high < b2[4])
                if bos_up and (b3[3] - b1[2]) >= max(0.20, 0.30 * a15) and b2[4] > b2[1] and c2b >= a15:
                    self._submit_entry(st, "V3_Pro_Clean", 1, b3[3], min(b1[3], b2[3]) - buf,
                                       trail_after_r=2.5, expire_bars=300, min_risk=1.0, skip_hours=(13, 14))
            elif st.sw_4h.trend == -1 and st.sw_1h.trend == -1 and st.sw_15m.last_low is not None:
                bos_dn = (b2[4] >= st.sw_15m.last_low > b3[4]) or (b1[4] >= st.sw_15m.last_low > b2[4])
                if bos_dn and (b1[3] - b3[2]) >= max(0.20, 0.30 * a15) and b2[4] < b2[1] and c2b >= a15:
                    self._submit_entry(st, "V3_Pro_Clean", -1, b3[2], max(b1[2], b2[2]) + buf,
                                       trail_after_r=2.5, expire_bars=300, min_risk=1.0, skip_hours=(13, 14))

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
                    ok_1d = (not is_nsx) or (
                        st.sw_1d.trend == 1 and st.d1_er14 >= 0.20 and st.d1_ema20 is not None and st.d1_last_c > st.d1_ema20
                    )
                    if ok_1d and c > mp["r_hi"] and (b3[3] - b1[2]) >= 0.25 * a15 and b2[4] > b2[1] and c2b >= 0.8 * a15 and st.sw_1h.trend == 1 and self._in_kz(dt):
                        self._submit_entry(st, eng, 1, b3[3], mp["ext"] - 0.5 * a15, trail_after_r=2.0,
                                           expire_bars=300, min_risk=min_r, require_confirm=(not is_nsx))
                        continue
                else:
                    mp["ext"] = max(mp["ext"], h)
                    ok_1d = (not is_nsx) or (
                        st.sw_1d.trend == -1 and st.d1_er14 >= 0.20 and st.d1_ema20 is not None and st.d1_last_c < st.d1_ema20
                    )
                    if ok_1d and c < mp["r_lo"] and (b1[3] - b3[2]) >= 0.25 * a15 and b2[4] < b2[1] and c2b >= 0.8 * a15 and st.sw_1h.trend == -1 and self._in_kz(dt):
                        self._submit_entry(st, eng, -1, b3[2], mp["ext"] + 0.5 * a15, trail_after_r=2.0,
                                           expire_bars=300, min_risk=min_r, require_confirm=(not is_nsx))
                        continue
                still.append(mp)
            st.amd_manips = still
        # V9 consumes the completed 15m bar before the new swing is committed;
        # this preserves body-break and prior-ATR causality.
        self._v9_profile_bar(st, bar, atr_before)
        st.sw_15m.update(bar)

    def on_5m(self, st: AssetState, bar) -> None:
        st.idx_5m += 1
        dt = self.utc_time
        h, l, c, o = float(bar.High), float(bar.Low), float(bar.Close), float(bar.Open)
        a5 = st.atr_5m.update(h, l, c)
        st.bars_5m.append((dt, o, h, l, c))

        is_xau = st.symbol == self.xau_sym
        is_nsx_chop = st.symbol == self.nsx_sym and st.d1_er14 < 0.25
        if (is_xau or is_nsx_chop) and len(st.bars_5m) >= 3 and self._in_kz(dt):
            b1, b2, b3 = st.bars_5m[-3], st.bars_5m[-2], st.bars_5m[-1]
            c2b = abs(b2[4] - b2[1])
            buf = max(1.0 if is_xau else 4.0, 0.5 * a5)
            min_fvg = max(0.20, 0.20 * a5) if is_xau else 0.20 * a5
            v_eng = "VisB_Pro" if is_xau else "NSX_VisB_Chop"
            v_min_r = 1.0 if is_xau else 5.0
            still = []
            for sc in st.cands_1h_k3_5m:
                if st.idx_5m - sc["start_i"] > 12:
                    continue
                if sc["side"] == 1:
                    if l < sc["sl_base"]:
                        continue
                    if st.sw_4h.trend == 1 and sc["choch"] is not None and c > sc["choch"] and (b3[3] - b1[2]) >= min_fvg and b2[4] > b2[1] and c2b >= 0.8 * a5:
                        self._submit_entry(st, v_eng, 1, b3[3], sc["sl_base"] - buf, trail_after_r=1.5, expire_bars=90, min_risk=v_min_r)
                        continue
                else:
                    if h > sc["sl_base"]:
                        continue
                    if st.sw_4h.trend == -1 and sc["choch"] is not None and c < sc["choch"] and (b1[3] - b3[2]) >= min_fvg and b2[4] < b2[1] and c2b >= 0.8 * a5:
                        self._submit_entry(st, v_eng, -1, b3[2], sc["sl_base"] + buf, trail_after_r=1.5, expire_bars=90, min_risk=v_min_r)
                        continue
                still.append(sc)
            st.cands_1h_k3_5m = still
        elif st.symbol == self.nsx_sym and st.cands_1h_k3_5m:
            st.cands_1h_k3_5m = [sc for sc in st.cands_1h_k3_5m if st.idx_5m - sc["start_i"] <= 12]

        st.sw_5m.update(bar)
        if st.symbol == self.btc_sym:
            st.atr_5m.val = a5
            self._ltf_bar(st, bar, 9, 0.0, 0.0020, 15.0, self.BTC_STEPS, "BTC_15R_BE", True)

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
        if st.ltf_idx > cs["exp"] or self._cfd_blocked(st, dt) or (cs["skip_hours"] and dt.hour in cs["skip_hours"]) or ((l <= cs["sl"]) if cs["side"] == 1 else (h >= cs["sl"])):
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
        dt = self.utc_time
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
            expires = (
                st.idx_15m > pm["expire_15m_idx"]
                if pm.get("expire_15m_idx") is not None
                else st.ltf_idx > pm["expire_idx"]
            )
            if expires or self._cfd_blocked(st, dt) or ((l <= pm["sl"]) if pm["side"] == 1 else (h >= pm["sl"])) or (pm["skip_hours"] and dt.hour in pm["skip_hours"]):
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
                        if eng != "BTC_15R_BE" or (trig - sl) / max(1.0, c) < 0.018:
                            self._submit_entry(st, eng, 1, trig, sl, tp=trig + fixed_rr * (trig - sl), step_locks=step_locks, expire_bars=20, min_risk=min_r)
                        continue
                else:
                    if h > sc["sl_base"]:
                        continue
                    if st.sw_4h.trend == -1 and st.sw_1h.trend == -1 and sc["choch"] is not None and b3[4] < sc["choch"] and (b1[3] - b3[2]) >= 0.25 * a1 and b2[4] < b2[1] and c2b >= a1:
                        trig, sl = b3[2], sc["sl_base"] + buf
                        sl = self._floor_sl(st, -1, trig, sl, min_r, c)
                        if eng != "BTC_15R_BE" or (sl - trig) / max(1.0, c) < 0.018:
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
        self.log(f"=== V9 Asset Telemetry (oco_cleanups={self.oco_cleanups}) ===")
        for st in self.assets.values():
            self.log(
                f"  {st.name:10s} | bars={st.bars_seen} | submitted={st.orders_submitted} "
                f"| invalid={self.invalid_counts[st.name]} | V9_profile_evals={st.v9_profile_evals} "
                f"| V9_aggressive_blocks={st.v9_aggressive_blocks} | V9_valid_choch={st.v9_choch_valid}"
            )
        self.log("=== V9 / V8 Trade Breakdown by (Asset, Engine) ===")
        for (asset, eng), cnt in sorted(self.trade_counts.items()):
            self.log(f"  {asset:10s} | {eng:14s}: {cnt} trades")
