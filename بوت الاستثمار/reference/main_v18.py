# region imports
from AlgorithmImports import *
import math
from collections import deque
# endregion


# USDT fee model (spec 5.1): fees in USDT, zero base-coin dust
class UsdtFeeModel(FeeModel):
    def _calc(self, parameters):
        try:
            sec = getattr(parameters, "security", None) or getattr(parameters, "Security", None)
            order = getattr(parameters, "order", None) or getattr(parameters, "Order", None)
            p = float(getattr(sec, "price", None) or getattr(sec, "Price", 0.0))
            q = abs(float(getattr(order, "absolute_quantity", None) or getattr(order, "AbsoluteQuantity", 0.0)))
            return OrderFee(CashAmount(p * q * 0.0005, "USDT"))
        except Exception:
            return OrderFee(CashAmount(0.0, "USDT"))

    def GetOrderFee(self, parameters):
        return self._calc(parameters)

    def get_order_fee(self, parameters):
        return self._calc(parameters)


class SymData:
    def __init__(self, sym):
        self.sym = sym
        self.o5 = deque(maxlen=60)
        self.h5 = deque(maxlen=60)
        self.l5 = deque(maxlen=60)
        self.c5 = deque(maxlen=60)
        self.v5 = deque(maxlen=60)
        self.o1 = deque(maxlen=260)
        self.h1 = deque(maxlen=260)
        self.l1 = deque(maxlen=260)
        self.c1 = deque(maxlen=260)
        self.v1 = deque(maxlen=260)
        self.o4 = deque(maxlen=260)
        self.h4 = deque(maxlen=260)
        self.l4 = deque(maxlen=260)
        self.c4 = deque(maxlen=260)
        self.v4 = deque(maxlen=260)
        self.b5 = 0
        self.b1 = 0
        self.b4 = 0
        self.e20_1 = 0.0
        self.e50_1 = 0.0
        self.e200_1 = 0.0
        self.e20_4 = 0.0
        self.e50_4 = 0.0
        self.e200_4 = 0.0
        self.atr1 = 0.0
        self.atr4 = 0.0
        self.rsi1 = 50.0
        self.rsi1_hist = deque(maxlen=36)
        self.vma1 = 0.0
        self.sw_h1 = deque(maxlen=25)
        self.sw_l1 = deque(maxlen=25)
        self.sw_h4 = deque(maxlen=25)
        self.sw_l4 = deque(maxlen=25)
        self.ep = 0.0
        self.sl = 0.0
        self.ir = 0.0
        self.eb5 = 0
        self.eb1 = 0
        self.eb4 = 0
        self.mfe = 0.0
        self.stage = 0
        self.arm = ""
        self.cd_until = 0
        self.sl_breach = 0
        self.loss_streak = 0

    def reset_pos(self):
        self.ep = 0.0
        self.sl = 0.0
        self.ir = 0.0
        self.eb5 = 0
        self.eb1 = 0
        self.eb4 = 0
        self.mfe = 0.0
        self.stage = 0
        self.arm = ""
        self.sl_breach = 0


class BinanceFuturesMultiCoinV12(QCAlgorithm):

    def initialize(self):
        self.set_start_date(2021, 1, 1)
        self.set_end_date(2026, 10, 31)
        self.set_account_currency("USDT")
        self.set_cash("USDT", 100.0)
        self.set_brokerage_model(BrokerageName.BINANCE_FUTURES, AccountType.MARGIN)
        self.settings.free_portfolio_value_percentage = 0.03
        self.coins = [
            "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
            "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "LINKUSDT", "SUIUSDT"
        ]
        self.syms = {}
        self.data = {}
        for t in self.coins:
            sec = self.add_crypto(t, Resolution.MINUTE, Market.BINANCE)
            sec.set_leverage(3.0)
            sec.set_fee_model(UsdtFeeModel())
            self.syms[t] = sec.symbol
            self.data[t] = SymData(t)
            c5 = TradeBarConsolidator(timedelta(minutes=5))
            c5.data_consolidated += self.make_5m_handler(t)
            self.subscription_manager.add_consolidator(sec.symbol, c5)
            c1 = TradeBarConsolidator(timedelta(hours=1))
            c1.data_consolidated += self.make_1h_handler(t)
            self.subscription_manager.add_consolidator(sec.symbol, c1)
            c4 = TradeBarConsolidator(timedelta(hours=4))
            c4.data_consolidated += self.make_4h_handler(t)
            self.subscription_manager.add_consolidator(sec.symbol, c4)
        self.set_warm_up(timedelta(days=35))

    def make_5m_handler(self, t):
        def handler(sender, bar):
            self.on_5m(t, bar)
        return handler

    def make_1h_handler(self, t):
        def handler(sender, bar):
            self.on_1h(t, bar)
        return handler

    def make_4h_handler(self, t):
        def handler(sender, bar):
            self.on_4h(t, bar)
        return handler

    def calc_ema(self, prev, val, period):
        if prev == 0.0:
            return val
        k = 2.0 / (period + 1.0)
        return val * k + prev * (1.0 - k)

    def calc_rsi(self, closes, period=14):
        if len(closes) < period + 1:
            return 50.0
        gains = 0.0
        losses = 0.0
        n = len(closes)
        for i in range(n - period, n):
            d = closes[i] - closes[i - 1]
            if d > 0:
                gains += d
            else:
                losses -= d
        if losses <= 1e-12:
            return 100.0
        rs = (gains / period) / (losses / period)
        return 100.0 - (100.0 / (1.0 + rs))

    def update_swings(self, highs, lows, sw_h, sw_l):
        cur_h = highs[-1]
        cur_l = lows[-1]
        while sw_h and cur_h >= sw_h[-1]:
            sw_h.pop()
        while sw_l and cur_l <= sw_l[-1]:
            sw_l.pop()
        if len(highs) >= 5:
            p_h = highs[-3]
            if p_h > highs[-5] and p_h > highs[-4] and p_h >= highs[-2] and p_h >= highs[-1]:
                sw_h.append(p_h)
            p_l = lows[-3]
            if p_l < lows[-5] and p_l < lows[-4] and p_l <= lows[-2] and p_l <= lows[-1]:
                sw_l.append(p_l)

    def round_lot(self, sym, qty):
        sec = self.securities[sym]
        lot = float(sec.symbol_properties.lot_size)
        if lot <= 0.0:
            return round(qty, 6)
        steps = math.floor((qty / lot) + 1e-7)
        val = steps * lot
        if lot >= 1.0:
            return float(int(round(val)))
        dec = max(0, int(round(-math.log10(lot))))
        return round(val, dec)

    def get_macro_regime(self):
        btc = self.data["BTCUSDT"]
        if len(btc.c4) < 50:
            return "BEAR_DEFENSE", 0.0
        ready = 0
        above = 0
        golden = 0
        for tk in self.coins:
            st = self.data[tk]
            if len(st.c4) >= 50 and st.e50_4 > 0 and st.e200_4 > 0:
                ready += 1
                if st.c4[-1] > st.e50_4:
                    above += 1
                if st.c4[-1] > st.e50_4 and st.e50_4 > st.e200_4:
                    golden += 1
        breadth = (above / float(ready)) if ready > 0 else 0.0
        golden_b = (golden / float(ready)) if ready > 0 else 0.0
        btc_c4 = btc.c4[-1]
        btc_golden = (btc_c4 > btc.e200_4 and btc.e50_4 > btc.e200_4)
        btc_strong = (btc_c4 > btc.e20_4 and btc.e20_4 > btc.e50_4 and btc_golden)
        if btc_strong and breadth >= 0.70 and golden_b >= 0.60:
            return "SUPER_BULL", breadth
        if (btc_golden and breadth >= 0.45) or breadth >= 0.60:
            return "NORMAL_BULL", breadth
        if breadth >= 0.20 or btc_c4 > btc.e50_4:
            return "RANGE_SNIPER", breadth
        return "BEAR_DEFENSE", breadth

    def calc_rs_score(self, t):
        s = self.data[t]
        btc = self.data["BTCUSDT"]
        if len(s.c1) < 25 or len(btc.c1) < 25:
            return 0.0
        r24_s = (s.c1[-1] / s.c1[-24]) - 1.0
        r24_b = (btc.c1[-1] / btc.c1[-24]) - 1.0
        r6_s = (s.c1[-1] / s.c1[-6]) - 1.0
        r6_b = (btc.c1[-1] / btc.c1[-6]) - 1.0
        return 0.65 * (r24_s - r24_b) + 0.35 * (r6_s - r6_b)

    # FATAL BUG 4: global BTC 1H waterfall veto (with higher-low exception)
    def btc_waterfall_veto(self):
        b = self.data["BTCUSDT"]
        if len(b.c1) < 30 or len(b.c5) < 5 or b.e20_1 <= 0.0:
            return False
        c1 = b.c1[-1]
        falling = (c1 < b.e20_1 * 0.992 and c1 < b.c1[-2]
                   and b.c5[-1] < b.e20_1 * 0.995)
        if not falling:
            return False
        l1 = list(b.l1)
        h1 = list(b.h1)
        if len(l1) >= 10 and len(h1) >= 3:
            hl = min(l1[-3:]) > min(l1[-10:-3])
            reclaim = b.c5[-1] > h1[-1]
            if hl and reclaim:
                return False
        return True

    def get_open_positions(self):
        open_t = []
        unproven = 0
        for tk in self.coins:
            sym = self.syms[tk]
            if self.portfolio[sym].invested and self.portfolio[sym].quantity > 0:
                open_t.append(tk)
                if self.data[tk].stage == 0:
                    unproven += 1
        return open_t, unproven

    def on_1h(self, t, bar):
        s = self.data[t]
        c = float(bar.close)
        h = float(bar.high)
        l = float(bar.low)
        o = float(bar.open)
        v = float(bar.volume)
        prev_c = s.c1[-1] if len(s.c1) > 0 else c
        s.o1.append(o)
        s.h1.append(h)
        s.l1.append(l)
        s.c1.append(c)
        s.v1.append(v)
        s.b1 += 1
        s.e20_1 = self.calc_ema(s.e20_1, c, 20)
        s.e50_1 = self.calc_ema(s.e50_1, c, 50)
        s.e200_1 = self.calc_ema(s.e200_1, c, 200)
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        s.atr1 = tr if s.atr1 == 0.0 else (s.atr1 * 13.0 + tr) / 14.0
        s.vma1 = v if s.vma1 == 0.0 else (s.vma1 * 19.0 + v) / 20.0
        s.rsi1 = self.calc_rsi(s.c1, 14)
        s.rsi1_hist.append(s.rsi1)
        self.update_swings(s.h1, s.l1, s.sw_h1, s.sw_l1)

    def on_4h(self, t, bar):
        s = self.data[t]
        c = float(bar.close)
        h = float(bar.high)
        l = float(bar.low)
        o = float(bar.open)
        v = float(bar.volume)
        prev_c = s.c4[-1] if len(s.c4) > 0 else c
        s.o4.append(o)
        s.h4.append(h)
        s.l4.append(l)
        s.c4.append(c)
        s.v4.append(v)
        s.b4 += 1
        s.e20_4 = self.calc_ema(s.e20_4, c, 20)
        s.e50_4 = self.calc_ema(s.e50_4, c, 50)
        s.e200_4 = self.calc_ema(s.e200_4, c, 200)
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        s.atr4 = tr if s.atr4 == 0.0 else (s.atr4 * 13.0 + tr) / 14.0
        self.update_swings(s.h4, s.l4, s.sw_h4, self.data[t].sw_l4)

    def on_5m(self, t, bar):
        s = self.data[t]
        c = float(bar.close)
        h = float(bar.high)
        l = float(bar.low)
        o = float(bar.open)
        v = float(bar.volume)
        s.o5.append(o)
        s.h5.append(h)
        s.l5.append(l)
        s.c5.append(c)
        s.v5.append(v)
        s.b5 += 1
        if self.is_warming_up:
            return
        if len(s.c1) < 60 or len(s.c4) < 50 or s.atr1 <= 0 or s.atr4 <= 0:
            return
        sym = self.syms[t]
        invested = self.portfolio[sym].invested and self.portfolio[sym].quantity > 0
        if invested:
            if s.ep <= 0.0:
                s.ep = float(self.portfolio[sym].average_price)
                s.ir = max(s.ep * 0.025, 1.2 * s.atr1)
                s.sl = s.ep - s.ir
                s.eb5 = s.b5
                s.eb1 = s.b1
                s.eb4 = s.b4
                s.mfe = h
            self.manage_position(t, s, sym, c, h, l)
        else:
            if s.ep > 0.0:
                s.reset_pos()
            self.try_enter(t, s, sym, c, h, l, o, v)

    def full_exit(self, t, s, sym, c, tag):
        q = float(self.portfolio[sym].quantity)
        if q > 0:
            qty = self.round_lot(sym, q)
            if qty > 0:
                self.market_order(sym, -qty, tag=tag)
        if c < s.ep:
            s.loss_streak += 1
            cd = 28 if s.loss_streak == 1 else (56 if s.loss_streak == 2 else 96)
            s.cd_until = s.b5 + cd
        else:
            s.loss_streak = 0
            s.cd_until = s.b5 + 10
        s.reset_pos()

    # FATAL BUG 6: invisible 1H structural stop + scratch shield + ratchet
    def manage_position(self, t, s, sym, c, h, l):
        if h > s.mfe:
            s.mfe = h
        ir = max(s.ir, s.ep * 0.015)
        r_now = (c - s.ep) / ir
        r_high = (s.mfe - s.ep) / ir
        r_close_1h = (s.c1[-1] - s.ep) / ir if len(s.c1) > 0 else r_now
        regime, _ = self.get_macro_regime()

        # F6.3 flash-crash guard
        if c <= s.ep - 1.85 * ir:
            self.full_exit(t, s, sym, c, "CATASTROPHIC_GUARD")
            return
        # F6.2 sustained 30-minute breakdown counter (0.3% beyond the stop)
        if c <= s.sl * 0.997:
            s.sl_breach += 1
        else:
            s.sl_breach = 0

        if s.stage == 0:
            # FATAL BUG 2: progressive scratch shield (never near price)
            if r_high >= 1.65 and r_close_1h >= 1.35:
                s.sl = max(s.sl, s.ep - 0.15 * ir)
            if (r_high >= 2.35 and r_close_1h >= 2.00
                    and regime in ("BEAR_DEFENSE", "RANGE_SNIPER")
                    and len(s.c1) >= 2 and s.c1[-1] < s.o1[-1]
                    and len(s.rsi1_hist) >= 7
                    and s.rsi1 < s.rsi1_hist[-7] - 6.0):
                s.sl = max(s.sl, s.ep - 0.05 * ir)
            if r_high >= 2.75 and s.b1 > s.eb1:
                s.sl = max(s.sl, s.ep + 2.10 * ir)
            # F6.1 invisible 1H stop
            cond_1h = (s.b1 > s.eb1 and len(s.c1) > 0
                       and s.c1[-1] <= s.sl and c <= s.sl)
            if cond_1h or s.sl_breach >= 6:
                self.full_exit(t, s, sym, c, "1H_STRUCT_STOP")
                return
            if ((s.b5 - s.eb5) >= 576 and r_high < 1.25 and r_now < -0.25
                    and c < s.e50_1):
                self.full_exit(t, s, sym, c, "DEAD_SETUP_EXIT")
                return

        # FATAL BUG 1: stage-1 transition = unified 100% (zero partials)
        if s.stage == 0 and (r_high >= 3.15 or r_now >= 3.15):
            s.stage = 1

        if s.stage >= 1:
            self.ratchet_3r(t, s, sym, c, h, regime, r_now, r_high, ir)

    def ratchet_3r(self, t, s, sym, c, h, regime, r_now, r_high, ir):
        # ---- SUPER rider: 100% rides with >= 0.55R buffers (no choke) ----
        vma5 = sum(s.v5) / float(len(s.v5)) if len(s.v5) >= 10 else 1.0
        vr5 = (s.v5[-1] / vma5) if vma5 > 0 else 1.0
        super_mode = (regime == "SUPER_BULL" or
                      (r_now >= 3.30 and vr5 >= 1.5 and s.e20_1 > 0
                       and c > s.e20_1))
        if super_mode:
            if r_high >= 3.60:
                s.sl = max(s.sl, s.ep + 3.05 * ir)
            if r_high >= 5.00:
                s.sl = max(s.sl, s.ep + 3.80 * ir)
            if r_high >= 8.00:
                s.sl = max(s.sl, s.ep + 6.00 * ir)
            if r_high >= 14.0:
                s.sl = max(s.sl, s.ep + 10.5 * ir)
            if r_high >= 22.0:
                s.sl = max(s.sl, s.ep + 17.0 * ir)
            if (len(s.c4) >= 2 and s.b4 > s.eb4
                    and s.c4[-1] < s.e50_4 and c < s.e50_4):
                self.full_exit(t, s, sym, c, "WAVE_TRAIL_4H")
                return
            if c <= s.sl:
                self.full_exit(t, s, sym, c, "RIDE_TRAIL_SL")
                return
            return

        # ---- NORMAL unified ratchet: floor_3r armed only after 3.47R ----
        floor_3r = s.ep + 3.02 * ir
        trail = s.mfe - 1.25 * ir
        if s.e20_1 > 0.0:
            trail = max(trail, s.e20_1 - 0.35 * s.atr1)
        armed = r_high >= 3.47   # >= 3.45R spec AND >= 0.45R room above floor
        if armed:
            trail = max(trail, floor_3r)
        if trail > s.sl:
            s.sl = trail
        # deliberate full target exits (still at >= 3.15R, unified 100%)
        hi20 = max(list(s.h4)[-20:]) if len(s.h4) >= 20 else 0.0
        at_res = ((hi20 > 0 and c >= hi20 * 0.993) or
                  (r_now >= 3.25 and len(s.o5) > 0 and c < s.o5[-1]))
        if r_now >= 3.15 and at_res:
            self.full_exit(t, s, sym, c, "FULL_SNIPER_3_3R")
            return
        deccel = (s.rsi1 >= 68.0) or (armed and len(s.h5) >= 2 and c < s.h5[-2])
        if deccel and r_now >= 3.15:
            self.full_exit(t, s, sym, c, "FULL_SNIPER_3_3R")
            return
        # armed floor / 1H close below the trail (only after 0.45R room)
        if armed and c <= s.sl:
            self.full_exit(t, s, sym, c, "RAT_3R_FLOOR")
            return
        if (s.b1 > s.eb1 and len(s.c1) > 0
                and s.c1[-1] <= s.sl and c <= s.sl):
            self.full_exit(t, s, sym, c, "TRAIL_1H_CLOSE")
            return

    # FATAL BUG 3+4+5: gates then the 4 structural arms, then ir + runway
    def evaluate_entry(self, t, s, c, h, l, o, v, regime, breadth):
        if s.b5 < s.cd_until:
            return 0.0, 0.0, ""
        if self.btc_waterfall_veto():
            return 0.0, 0.0, ""
        if len(s.h4) < 30 or len(s.h1) < 30 or len(s.rsi1_hist) < 15:
            return 0.0, 0.0, ""
        if s.atr1 <= 0.0 or len(s.l1) < 24:
            return 0.0, 0.0, ""
        hi_20 = max(list(s.h4)[-20:])
        lo_20 = min(list(s.l4)[-20:])
        pos_20 = (c - lo_20) / max(hi_20 - lo_20, c * 0.01)
        vma5 = sum(s.v5) / float(len(s.v5)) if len(s.v5) >= 10 else v
        vr5 = (v / vma5) if vma5 > 0 else 1.0
        rs = self.calc_rs_score(t)
        l1 = list(s.l1)
        h1 = list(s.h1)
        rsi_h = list(s.rsi1_hist)

        # FATAL BUG 5: structural stop anchored under the confirmed bottom
        struct_sl = min(l1[-4:]) - 0.35 * s.atr1
        raw_ir = c - struct_sl
        max_ir = (min(c * 0.042, 2.20 * s.atr1) if regime == "SUPER_BULL"
                  else min(c * 0.032, 2.00 * s.atr1))
        if raw_ir > max_ir * 1.15:
            return 0.0, 0.0, ""     # never chase a late entry
        min_ir = max(c * 0.015, 0.90 * s.atr1)
        ir = max(min_ir, min(raw_ir, max_ir))

        # FATAL BUG 3: clear runway to the 4H ceiling (>= 2.8R)
        if c < hi_20 and (hi_20 - c) < 2.8 * ir:
            return 0.0, 0.0, ""
        if s.e200_4 > 0 and c < s.e200_4 * 0.99 and (s.e200_4 - c) < 2.8 * ir:
            return 0.0, 0.0, ""

        arm = ""
        score = 0.0

        # ARM 1: W_CAP_BOTTOM (all regimes) — true W-bottom, no first leg
        if len(s.rsi1_hist) >= 24 and len(s.v1) >= 24:
            win = l1[-24:-3]
            rw = rsi_h[-24:-3]
            vw = list(s.v1)[-24:-3]
            if len(win) >= 10 and len(rw) >= 10:
                abs_low = min(win)
                idx = win.index(abs_low)
                # window is l1[-24:-3]: element i sits (24-i) hours back
                ago_ok = 4 <= (24 - idx) <= 21     # 3..20h spec, slice-safe
                wash = (abs_low <= s.e50_1 * 0.952 and min(rw) <= 32.5
                        and max(vw) >= 1.8 * s.vma1)
                hl = min(l1[-3:]) >= abs_low * 1.002
                div = min(rsi_h[-3:]) >= min(rw) + 4.0
                turn = (c > s.e20_1 and c > max(h1[-2:]) and c > s.o1[-1]
                        and 40.0 <= s.rsi1 <= 56.0)
                if (ago_ok and wash and hl and div and turn
                        and pos_20 <= 0.38):
                    arm = "W_CAP_BOTTOM"
                    score = 92.0 + rs * 100.0

        # ARM 2: DEMAND_4H_SPRING (range/trend bottoms)
        if not arm and regime in ("SUPER_BULL", "NORMAL_BULL", "RANGE_SNIPER"):
            l4 = list(s.l4)
            tested = (min(l4[-3:]) <= max(s.e50_4 * 1.005, lo_20 * 1.012)
                      and s.c4[-1] >= s.e200_4 * 0.985)
            hl = l1[-1] > min(l1[-6:-1])
            turn = (c > s.e20_1 and c > s.h1[-1] and c > s.o1[-1]
                    and 42.0 <= s.rsi1 <= 57.0)
            if tested and hl and turn and pos_20 <= 0.40 and rs >= 0.0:
                arm = "DEMAND_4H_SPRING"
                score = 86.0 + rs * 100.0

        # ARM 3: TREND_PULLBACK_1H (exact pocket + early turn snap)
        if not arm:
            btc = self.data["BTCUSDT"]
            allowed = (regime in ("NORMAL_BULL", "SUPER_BULL") or
                       (regime == "RANGE_SNIPER" and len(btc.c4) > 0
                        and btc.c4[-1] > btc.e50_4))
            if allowed and len(l1) >= 8:
                trend = (s.c4[-1] > s.e20_4 >= s.e50_4
                         and s.e20_1 >= s.e50_1)
                pocket = (min(l1[-8:-1]) <= s.e20_1 * 1.003
                          and min(l1[-8:-1]) >= s.e50_1 * 0.988
                          and min(rsi_h[-8:-1]) <= 49.0)
                turn = (c > s.e20_1 and c > max(h1[-2:]) and c > s.o1[-1]
                        and pos_20 <= 0.48 and 45.0 <= s.rsi1 <= 59.0)
                snap = c - min(l1[-4:]) <= 1.6 * s.atr1
                if trend and rs >= 0.003 and pocket and turn and snap:
                    arm = "TREND_PULLBACK_1H"
                    score = 88.0 + rs * 100.0

        # ARM 4: SUPER_CYCLE_IGN (super bull only, breadth >= 0.70)
        if not arm and regime == "SUPER_BULL" and breadth >= 0.70:
            btc = self.data["BTCUSDT"]
            st = (btc.c4[-1] > btc.e20_4 > btc.e50_4 > btc.e200_4)
            base = max(h1[-10:-1]) - min(l1[-10:-1]) <= 2.4 * s.atr1
            brk = (c > max(h1[-10:-1]) and vr5 >= 1.35
                   and 50.0 <= s.rsi1 <= 63.0)
            if st and base and brk and pos_20 <= 0.65 and rs >= 0.008:
                arm = "SUPER_CYCLE_IGN"
                score = 84.0 + rs * 100.0

        if not arm:
            return 0.0, 0.0, ""
        sl = c - ir
        return score, sl, arm

    def try_enter(self, t, s, sym, c, h, l, o, v):
        regime, breadth = self.get_macro_regime()
        open_t, unproven = self.get_open_positions()
        # spec 5.3 slot caps / risk per regime (exact numbers)
        if regime == "SUPER_BULL":
            max_pos, max_unprov, risk_pct, slot = 3, 2, 0.022, 0.55
        elif regime == "NORMAL_BULL":
            max_pos, max_unprov, risk_pct, slot = 2, 1, 0.018, 0.48
        elif regime == "RANGE_SNIPER":
            max_pos, max_unprov, risk_pct, slot = 2, 1, 0.015, 0.42
        else:
            max_pos, max_unprov, risk_pct, slot = 1, 1, 0.012, 0.35
        if len(open_t) >= max_pos or unproven >= max_unprov:
            return
        score, sl, arm = self.evaluate_entry(t, s, c, h, l, o, v, regime, breadth)
        if score <= 0.0:
            return
        # rank all 10 on this bar: only the #1 candidate may enter
        for other in self.coins:
            if other == t:
                continue
            o_sym = self.syms[other]
            if self.portfolio[o_sym].invested and self.portfolio[o_sym].quantity > 0:
                continue
            os_ = self.data[other]
            if len(os_.c5) == 0 or len(os_.c1) < 60 or len(os_.c4) < 50:
                continue
            oscore, _, _ = self.evaluate_entry(
                other, os_, os_.c5[-1], os_.h5[-1], os_.l5[-1],
                os_.o5[-1], os_.v5[-1], regime, breadth)
            if oscore > score:
                return
        eq = float(self.portfolio.total_portfolio_value)
        if eq <= 5.0:
            return
        ir = c - sl
        if ir <= 0.0:
            return
        risk_usdt = eq * risk_pct
        if s.loss_streak >= 2:
            risk_usdt *= 0.75
        notional = (risk_usdt / ir) * c
        margin_room = float(self.portfolio.margin_remaining) * 2.4
        notional = min(notional, eq * slot, margin_room)
        if notional < 6.2:
            return
        qty = self.round_lot(sym, notional / c)
        if qty <= 0.0 or qty * c < 6.0:
            return
        ticket = self.market_order(sym, qty, tag="ENT_%s_%s" % (arm, regime))
        if ticket.status != OrderStatus.INVALID:
            s.ep = c
            s.sl = sl
            s.ir = ir
            s.eb5 = s.b5
            s.eb1 = s.b1
            s.eb4 = s.b4
            s.mfe = c
            s.stage = 0
            s.arm = arm
            s.sl_breach = 0
