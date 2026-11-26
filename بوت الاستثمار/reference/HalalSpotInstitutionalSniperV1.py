# region imports
from AlgorithmImports import *
from collections import deque
from datetime import timedelta
import math
# endregion


class AdaptiveChartEye:
    """
    Self-Normalizing Visual Perception Engine (Zero Magic ATR Multipliers).
    Detects structural swings using rolling distribution (Mean + StdDev) of actual chart ranges
    and tracks the exact Origin_Anchor of staircase compressions.
    """
    def __init__(self):
        self.hi = -1e18
        self.lo = 1e18
        self.hi_i = 0
        self.lo_i = 0
        self.dir = 0
        self.rng_q = deque(maxlen=50)
        self.sh = deque(maxlen=10)  # (idx, price, prominence, consumed)
        self.sl = deque(maxlen=10)  # (idx, price, prominence, origin_high, consumed)

    def update(self, h, l, c, o, idx):
        rng = max(h - l, c * 0.0005)
        self.rng_q.append(rng)
        n = len(self.rng_q)
        if n < 10:
            return None, None

        # Dynamic self-normalizing threshold from actual chart distribution (mu + 1.5 * sigma)
        mu = sum(self.rng_q) / n
        var = sum((x - mu) ** 2 for x in self.rng_q) / n
        sigma = math.sqrt(var)
        th = max(mu * 2.2 + sigma * 1.6, c * 0.0035)

        nh, nl = None, None
        if self.dir == 0:
            if h > self.hi:
                self.hi, self.hi_i = h, idx
            if l < self.lo:
                self.lo, self.lo_i = l, idx
            if self.hi - l >= th and self.hi > -1e17:
                self.dir = -1
                nh = [self.hi_i, self.hi, self.hi - l, False]
                self.sh.append(nh)
                self.lo, self.lo_i = l, idx
            elif h - self.lo >= th and self.lo < 1e17:
                self.dir = 1
                nl = [self.lo_i, self.lo, h - self.lo, self.hi if self.hi > -1e17 else h, False]
                self.sl.append(nl)
                self.hi, self.hi_i = h, idx
        elif self.dir == 1:
            if h > self.hi:
                self.hi, self.hi_i = h, idx
            elif self.hi - l >= th:
                self.dir = -1
                nh = [self.hi_i, self.hi, self.hi - l, False]
                self.sh.append(nh)
                self.lo, self.lo_i = l, idx
        elif self.dir == -1:
            if l < self.lo:
                self.lo, self.lo_i = l, idx
            elif h - self.lo >= th:
                self.dir = 1
                # Record exact Origin_Anchor (the structural peak from which the drop started)
                origin_anchor = self.hi
                if len(self.sh) >= 2:
                    origin_anchor = max(self.hi, self.sh[-1][1], self.sh[-2][1])
                nl = [self.lo_i, self.lo, h - self.lo, origin_anchor, False]
                self.sl.append(nl)
                self.hi, self.hi_i = h, idx
        return nh, nl


class SpotSymState:
    def __init__(self, sym, base_ccy):
        self.sym = sym
        self.base_ccy = base_ccy
        self.q15 = deque(maxlen=120)
        self.q1 = deque(maxlen=80)
        self.q4 = deque(maxlen=60)
        self.b15 = 0
        self.b1 = 0
        self.b4 = 0
        self.eye15 = AdaptiveChartEye()
        self.eye1 = AdaptiveChartEye()
        self.eye4 = AdaptiveChartEye()
        self.tr1 = 1
        self.tr4 = 1
        self.day = -1
        self.wk = -1
        self.dh = 0.0
        self.dl = 1e18
        self.pdh = 0.0
        self.pdl = 0.0
        self.wh = 0.0
        self.wl = 1e18
        self.pwh = 0.0
        self.pwl = 0.0
        self.ah = 0.0
        self.al = 1e18
        self.aswp_l = False
        # Active Sweep Memory
        self.swp_active = False
        self.swp_low = 0.0
        self.swp_lvl = 0.0
        self.swp_origin = 0.0
        self.swp_bar = -999
        self.swp_vac = 0.5
        self.swp_eq = False
        # Trade Execution & Management
        self.cd = -999
        self.entk = None
        self.t1tk = None
        self.ep = 0.0
        self.sl = 0.0
        self.tp1 = 0.0
        self.r = 0.0
        self.eb = 0
        self.t1d = False
        self.be_locked = False
        self.mfe_px = 0.0


class HalalSpotInstitutionalSniperV1(QCAlgorithm):

    def initialize(self):
        self.set_start_date(2021, 1, 1)
        self.set_end_date(2026, 10, 31)
        self.set_account_currency("USDT")
        self.set_cash("USDT", 100.0)
        # 100% HALAL SPOT CASH ACCOUNT (Zero Leverage, Zero Margin, Zero Short-Borrowing)
        self.set_brokerage_model(BrokerageName.BINANCE, AccountType.CASH)

        # Core Institutional Spot Targets (BTC, ETH, SOL + BNB, AVAX for steady ~2-3 weekly A+ setups)
        pairs = [
            ("BTCUSDT", "BTC"),
            ("ETHUSDT", "ETH"),
            ("SOLUSDT", "SOL"),
            ("BNBUSDT", "BNB"),
            ("AVAXUSDT", "AVAX")
        ]
        self.st = {}
        self.btc = None
        self.max_pos = 3
        self.pk_eq = 100.0

        for ticker, base_ccy in pairs:
            sec = self.add_crypto(ticker, Resolution.MINUTE, Market.BINANCE)
            sym = sec.symbol
            if ticker == "BTCUSDT":
                self.btc = sym
            self.st[sym] = SpotSymState(sym, base_ccy)
            self.consolidate(sym, timedelta(minutes=15), lambda b, s=sym: self._on_15m(s, b))
            self.consolidate(sym, timedelta(hours=1), lambda b, s=sym: self._on_1h(s, b))
            self.consolidate(sym, timedelta(hours=4), lambda b, s=sym: self._on_4h(s, b))

        self.set_warm_up(timedelta(days=14))

    def _rp(self, sym, px):
        sp = self.securities[sym].symbol_properties
        st = float(sp.minimum_price_variation or 0.0001)
        if st <= 0:
            return round(float(px), 6)
        d = max(0, int(round(-math.log10(st)))) if st < 1 else 0
        return round(round(float(px) / st) * st, d)

    def _held_qty(self, s):
        # In Spot Cash Account, actual coins are held in the base currency cash book after spot fee deduction
        cb = self.portfolio.cash_book
        raw_q = float(cb[s.base_ccy].amount) if s.base_ccy in cb else abs(float(self.portfolio[s.sym].quantity))
        sp = self.securities[s.sym].symbol_properties
        step = float(sp.lot_size or 0.0001)
        q = math.floor((max(0.0, raw_q) * 0.999 + 1e-12) / step) * step if step > 0 else max(0.0, raw_q)
        return round(q, 6)

    def _rq_buy(self, sym, qty, px):
        sp = self.securities[sym].symbol_properties
        step = float(sp.lot_size or 0.0001)
        mn = float(sp.minimum_order_size or 5.0)
        q = math.floor((abs(qty) + 1e-12) / step) * step if step > 0 else abs(qty)
        q = round(q, 6)
        if q <= 0 or px <= 0:
            return 0.0
        min_notional = max(5.5, mn * 1.05) if mn >= 1.0 else 5.5
        if q * px < min_notional or (mn < 1.0 and q < mn):
            return 0.0
        return q

    def _is_invested(self, s, px):
        hq = self._held_qty(s)
        return (hq * px) >= 5.2

    def _ker(self, q, n):
        if len(q) < n:
            return 0.5
        arr = list(q)[-n:]
        net = abs(float(arr[-1].close) - float(arr[0].close))
        tot = sum(abs(float(arr[i].close) - float(arr[i - 1].close)) for i in range(1, len(arr)))
        return net / max(tot, 1e-12)

    def _rst(self, s):
        if s.entk is not None:
            try:
                s.entk.cancel()
            except Exception:
                pass
        if s.t1tk is not None:
            try:
                s.t1tk.cancel()
            except Exception:
                pass
        s.entk = None
        s.t1tk = None
        s.ep = 0.0
        s.sl = 0.0
        self.tp1 = 0.0
        s.r = 0.0
        s.t1d = False
        s.be_locked = False
        s.mfe_px = 0.0

    def _sell_spot(self, s, qty, tag_str):
        self.transactions.cancel_open_orders(s.sym)
        s.t1tk = None
        hq = self._held_qty(s)
        sell_q = min(hq, qty) if qty > 0 else hq
        px = float(self.securities[s.sym].price)
        if sell_q > 0 and sell_q * px >= 5.1:
            self.market_order(s.sym, -sell_q, tag=tag_str)
        self._rst(s)
        s.cd = s.b15

    def _on_4h(self, sym, bar):
        s = self.st[sym]
        s.b4 += 1
        h, l, c, o = float(bar.high), float(bar.low), float(bar.close), float(bar.open)
        s.q4.append(bar)
        nh, nl = s.eye4.update(h, l, c, o, s.b4)
        if len(s.eye4.sh) > 0 and c > s.eye4.sh[-1][1]:
            s.tr4 = 1
        elif len(s.eye4.sl) > 0 and c < s.eye4.sl[-1][1]:
            s.tr4 = -1

        # Uncapped Runner Structural Trail on 4H Swing Lows (Rides 10:1 to 20:1+ waves)
        if not self.is_warming_up and s.t1d and nl is not None and self._is_invested(s, c):
            struct_sl = self._rp(sym, nl[1] * 0.996)
            if struct_sl > s.sl:
                s.sl = struct_sl

    def _on_1h(self, sym, bar):
        s = self.st[sym]
        s.b1 += 1
        h, l, c, o = float(bar.high), float(bar.low), float(bar.close), float(bar.open)
        s.q1.append(bar)
        nh, nl = s.eye1.update(h, l, c, o, s.b1)
        if len(s.eye1.sh) > 0 and c > s.eye1.sh[-1][1]:
            s.tr1 = 1
        elif len(s.eye1.sl) > 0 and c < s.eye1.sl[-1][1]:
            s.tr1 = -1

        if self.is_warming_up:
            return

        # 1H Structural Runner Trail & Breakeven Shield
        if self._is_invested(s, c) and s.r > 0:
            # Stage 1 Shield: Once price reaches +1.4R and forms a 1H higher low or strong close, lock Breakeven (+0.12R)
            if not s.be_locked and s.mfe_px >= s.ep + 1.40 * s.r and c >= s.ep + 1.05 * s.r:
                s.be_locked = True
                s.sl = max(s.sl, self._rp(sym, s.ep + 0.12 * s.r))
            # Stage 2 Uncapped Runner: After TP1 (>= 3.0R) is banked, trail beneath every new 1H topological swing low
            if s.t1d and nl is not None:
                trail_1h = self._rp(sym, nl[1] * 0.997)
                if trail_1h > s.sl and trail_1h < c * 0.998:
                    s.sl = trail_1h

        # Detect 1H Institutional Liquidity Sweep & Origin_Anchor
        if len(s.eye1.sl) >= 1 and not self._is_invested(s, c):
            last_sl = s.eye1.sl[-1]
            lvl = last_sl[1]
            origin_hi = last_sl[3]
            consumed = last_sl[4]
            is_eql = False
            if len(s.eye1.sl) >= 2:
                prev_sl = s.eye1.sl[-2]
                spread = abs(lvl - prev_sl[1]) / max(lvl, 1e-8)
                if spread <= 0.0045 and (last_sl[0] - prev_sl[0]) >= 3:
                    is_eql = True
                    origin_hi = max(origin_hi, prev_sl[3])

            if not consumed and l < lvl and c > lvl:
                last_sl[4] = True
                s.swp_active = True
                s.swp_low = l
                s.swp_lvl = lvl
                s.swp_origin = max(origin_hi, s.pdh, s.ah)
                s.swp_bar = s.b15
                s.swp_vac = 1.0 - self._ker(s.q1, 10)
                s.swp_eq = is_eql

    def _find_structural_anchor(self, s, ep, r):
        """
        Finds the true chart ceiling / Origin_Anchor and verifies:
        1. No un-broken Major Brick Wall blocking before 3.0R.
        2. Real structural target >= 3.0R.
        """
        candidates = [s.swp_origin, s.pdh, s.pwh, s.dh]
        for sh_item in s.eye1.sh:
            if sh_item[1] > ep:
                candidates.append(sh_item[1])
        for sh4_item in s.eye4.sh:
            if sh4_item[1] > ep:
                candidates.append(sh4_item[1])

        valid_targets = [x for x in candidates if x >= ep + 3.0 * r]
        if not valid_targets:
            return 0.0

        # Check if a major multi-day wall (PWH) sits tightly between entry and 2.2R in a 4H downtrend
        if s.tr4 == -1 and s.pwh > ep and (s.pwh - ep) < 2.2 * r:
            return 0.0

        # First target is the nearest valid structural Origin_Anchor >= 3.0R (capped at 4.2R for TP1 so it hits reliably)
        nearest_anchor = min(valid_targets)
        return min(nearest_anchor, ep + 4.2 * r)

    def _on_15m(self, sym, bar):
        s = self.st[sym]
        s.b15 += 1
        h, l, c, o = float(bar.high), float(bar.low), float(bar.close), float(bar.open)
        s.q15.append(bar)

        dt = bar.end_time
        d = dt.timetuple().tm_yday
        wk = dt.isocalendar()[1]
        if d != s.day:
            if s.day != -1:
                s.pdh, s.pdl = s.dh, s.dl
            s.day, s.dh, s.dl = d, h, l
            s.ah, s.al = 0.0, 1e18
            s.aswp_l = False
        else:
            s.dh, s.dl = max(s.dh, h), min(s.dl, l)
        if wk != s.wk:
            if s.wk != -1:
                s.pwh, s.pwl = s.wh, s.wl
            s.wk, s.wh, s.wl = wk, h, l
        else:
            s.wh, s.wl = max(s.wh, h), min(s.wl, l)

        if 0 <= dt.hour < 7:
            s.ah, s.al = max(s.ah, h), min(s.al, l)

        s.eye15.update(h, l, c, o, s.b15)

        if self.is_warming_up:
            return

        # 1. Manage Pending Limit Entry Order
        if s.entk is not None:
            if self._is_invested(s, c):
                s.entk = None
                self._place_tp1(s)
            elif s.b15 - s.eb > 8:  # Cancel if un-filled after 2 hours (8 * 15m bars)
                self._rst(s)
            return

        # 2. Manage Active Spot Position (Stop Loss, Breakeven Shield & Uncapped Runner)
        if self._is_invested(s, c):
            if h > s.mfe_px:
                s.mfe_px = h
            # Fast intrabar Breakeven Shield once price clears +1.5R
            if not s.be_locked and s.r > 0 and s.mfe_px >= s.ep + 1.50 * s.r and c >= s.ep + 1.10 * s.r:
                s.be_locked = True
                s.sl = max(s.sl, self._rp(sym, s.ep + 0.12 * s.r))
            # Execute Spot Stop Loss or Trailing Stop cleanly without Cash Lock conflict
            if s.sl > 0 and l <= s.sl:
                tag_str = "TRAIL_WIN" if s.t1d else ("BE_SHIELD" if s.be_locked else "SL")
                self._sell_spot(s, 0.0, tag_str)
            return

        if len(s.q15) < 25 or s.b15 - s.cd < 8:
            return

        # 3. Detect 15m Sweep of PDL / PWL / Asia Low / 15m EQL
        if not s.swp_active:
            ref_lvls = [lv for lv in (s.pdl, s.pwl, s.al) if 0 < lv < 1e17]
            for rf in ref_lvls:
                if l < rf and c > rf and c > o:
                    s.swp_active = True
                    s.swp_low = l
                    s.swp_lvl = rf
                    s.swp_origin = max(s.dh, s.pdh, s.ah)
                    s.swp_bar = s.b15
                    s.swp_vac = 1.0 - self._ker(s.q15, 12)
                    s.swp_eq = True
                    break

        if not s.swp_active and len(s.eye15.sl) >= 2:
            sl_last = s.eye15.sl[-1]
            sl_prev = s.eye15.sl[-2]
            if not sl_last[4] and l < sl_last[1] and c > sl_last[1]:
                sl_last[4] = True
                is_eq15 = abs(sl_last[1] - sl_prev[1]) / max(sl_last[1], 1e-8) <= 0.0035
                if is_eq15 or s.tr4 == 1:
                    s.swp_active = True
                    s.swp_low = l
                    s.swp_lvl = sl_last[1]
                    s.swp_origin = max(sl_last[3], sl_prev[3], s.pdh)
                    s.swp_bar = s.b15
                    s.swp_vac = 1.0 - self._ker(s.q15, 12)
                    s.swp_eq = is_eq15

        if not s.swp_active:
            return

        age = s.b15 - s.swp_bar
        if age > 10:
            s.swp_active = False
            return
        if l < s.swp_low:
            s.swp_low = l

        # 4. Verify Impulse Velocity Ratio (K = V_impulse / V_compression) & FVG/BOS
        b0, b1, b2 = s.q15[-3], s.q15[-2], bar
        bfvg = float(b2.low) > float(b0.high) and float(b1.close) > float(b1.open)
        bos = len(s.eye15.sh) > 0 and c > s.eye15.sh[-1][1] and c > o

        comp_bars = list(s.q15)[-10:-2]
        v_comp = sum(abs(float(x.close) - float(x.open)) for x in comp_bars) / max(len(comp_bars), 1)
        v_imp = max(abs(c - o), abs(float(b1.close) - float(b1.open)))
        k_ratio = v_imp / max(v_comp, c * 0.0005)

        if (bfvg or bos) and k_ratio >= 1.35:
            # HTF Freight-Train Veto (Never buy into a crashing 4H waterfall)
            if s.tr4 == -1 and self._ker(s.q4, 8) > 0.62:
                s.swp_active = False
                return
            if self.btc and self.btc in self.st:
                bs = self.st[self.btc]
                if bs.tr4 == -1 and self._ker(bs.q4, 8) > 0.65:
                    s.swp_active = False
                    return

            # Sniper Retest Entry inside FVG/BPR to cut Stop Loss distance R in half
            ep = self._rp(sym, float(b0.high) + 0.35 * (float(b2.low) - float(b0.high))) if bfvg else self._rp(sym, c - 0.25 * (c - l))
            sl = self._rp(sym, min(s.swp_low, l) * 0.9982)
            r = ep - sl
            if r <= 0:
                return
            sl_pct = r / ep
            if sl_pct < 0.0035 or sl_pct > 0.025:
                return

            # Verify True Structural Target >= 3.0R (Minimum 3:1 RRR at TP1!)
            tp1_anchor = self._find_structural_anchor(s, ep, r)
            if tp1_anchor <= 0:
                return

            # Bayesian Confidence Score
            lo = -0.20 + 0.45 * min(2.2, k_ratio) + 0.55 * s.swp_vac
            if s.swp_eq:
                lo += 0.50
            if s.tr4 == 1:
                lo += 0.45
            if s.tr1 == 1:
                lo += 0.35
            prob = (1.0 / (1.0 + math.exp(-max(-15.0, min(15.0, lo))))) * math.exp(-0.08 * age)

            if prob >= 0.64:
                s.swp_active = False
                self._enter_spot_sniper(s, ep, sl, tp1_anchor, prob)

    def _enter_spot_sniper(self, s, ep, sl, tp1_px, prob):
        active_cnt = sum(1 for v in self.st.values() if (self._is_invested(v, float(self.securities[v.sym].price)) and not v.t1d) or v.entk is not None)
        if active_cnt >= self.max_pos:
            return

        eq = float(self.portfolio.total_portfolio_value)
        usdt_free = float(self.portfolio.cash_book["USDT"].amount) if "USDT" in self.portfolio.cash_book else 0.0
        if eq <= 10.0 or usdt_free < max(7.0, eq * 0.18):
            return

        if eq > self.pk_eq:
            self.pk_eq = eq
        dd = (self.pk_eq - eq) / self.pk_eq if self.pk_eq > 0 else 0.0
        dd_mult = 1.0 if dd < 0.10 else max(0.50, 1.0 - dd * 1.5)

        # Conservative Spot Risk Sizing (1.2% - 1.5% capital risk per trade, capped by available USDT cash)
        sl_pct = (ep - sl) / ep
        rk_pct = (0.012 + 0.005 * min(1.0, (prob - 0.64) / 0.25)) * dd_mult
        desired_notional = (eq * rk_pct) / (sl_pct + 0.0015)
        notional = min(desired_notional, usdt_free * 0.88, eq * 0.48)

        qty = self._rq_buy(s.sym, notional / ep, ep)
        if qty <= 0:
            return

        s.ep = ep
        s.sl = sl
        s.r = ep - sl
        s.tp1 = self._rp(s.sym, max(tp1_px, ep + 3.0 * s.r))
        s.eb = s.b15
        s.t1d = False
        s.be_locked = False
        s.mfe_px = ep
        s.cd = s.b15

        tk = self.limit_order(s.sym, qty, ep, tag="SPOT_EN")
        if tk is None or tk.status == OrderStatus.INVALID:
            self._rst(s)
            return
        if tk.status == OrderStatus.FILLED:
            self._place_tp1(s)
        else:
            s.entk = tk

    def _place_tp1(self, s):
        hq = self._held_qty(s)
        if hq <= 0 or s.t1tk is not None:
            return
        # Sell 45% at TP1 (>= 3.0R), leave 55% completely uncapped (10:1, 20:1+) for structural trail
        sp = self.securities[s.sym].symbol_properties
        step = float(sp.lot_size or 0.0001)
        q1 = math.floor((hq * 0.45 + 1e-12) / step) * step if step > 0 else hq * 0.45
        q1 = round(q1, 6)
        rem = round(hq - q1, 6)
        if q1 * s.tp1 >= 5.5 and rem * s.ep >= 5.5:
            s.t1tk = self.limit_order(s.sym, -q1, s.tp1, tag="TP1_3R")
        else:
            # If account is small ($100) and splitting would create <$5.5 dust, place 100% at >= 3.0R
            s.t1tk = self.limit_order(s.sym, -hq, s.tp1, tag="TP1_FULL_3R")

    def on_order_event(self, oe: OrderEvent):
        sym = oe.symbol
        if sym not in self.st:
            return
        s = self.st[sym]
        oid = oe.order_id
        st = oe.status

        if s.entk is not None and oid == s.entk.order_id:
            if st == OrderStatus.FILLED:
                s.entk = None
                s.ep = float(oe.fill_price)
                s.mfe_px = s.ep
                s.r = max(s.ep - s.sl, s.ep * 0.0035)
                s.tp1 = self._rp(sym, max(s.tp1, s.ep + 3.0 * s.r))
                self._place_tp1(s)
            elif st in (OrderStatus.CANCELED, OrderStatus.INVALID):
                if not self._is_invested(s, float(self.securities[sym].price)):
                    self._rst(s)
            return

        if st == OrderStatus.FILLED and s.t1tk is not None and oid == s.t1tk.order_id:
            s.t1d = True
            s.t1tk = None
            s.be_locked = True
            # Lock +1.5R minimum profit on the remaining 55% Uncapped Runner!
            s.sl = max(s.sl, self._rp(sym, s.ep + 1.50 * s.r))
            if not self._is_invested(s, float(self.securities[sym].price)):
                self._rst(s)
                s.cd = s.b15
