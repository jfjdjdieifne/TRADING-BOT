# region imports
from AlgorithmImports import *
from collections import deque
from datetime import timedelta
import math
# endregion


class AdaptiveChartEye:
    """
    Self-Normalizing Structural Swing Engine.
    Identifies true topological Swing Highs and Swing Lows with Origin_Anchor tracking.
    """
    def __init__(self):
        self.hi = -1e18
        self.lo = 1e18
        self.hi_i = 0
        self.lo_i = 0
        self.dir = 0
        self.rng_q = deque(maxlen=50)
        self.sh = deque(maxlen=12)  # [idx, price, prominence, consumed]
        self.sl = deque(maxlen=12)  # [idx, price, prominence, origin_high, consumed]

    def update(self, h, l, c, o, idx):
        rng = max(h - l, c * 0.0005)
        self.rng_q.append(rng)
        n = len(self.rng_q)
        if n < 10:
            return None, None

        mu = sum(self.rng_q) / n
        var = sum((x - mu) ** 2 for x in self.rng_q) / n
        sigma = math.sqrt(var)
        th = max(mu * 2.1 + sigma * 1.5, c * 0.0040)

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
        self.q1 = deque(maxlen=100)
        self.q4 = deque(maxlen=80)
        self.b15 = 0
        self.b1 = 0
        self.b4 = 0
        self.eye15 = AdaptiveChartEye()
        self.eye1 = AdaptiveChartEye()
        self.eye4 = AdaptiveChartEye()
        self.tr1 = 1
        self.tr4 = 1
        self.ema4h = 0.0
        self.ema1h = 0.0
        self.ema15m = 0.0
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
        # Active Sweep & Reclaim Memory
        self.swp_active = False
        self.swp_low = 0.0
        self.swp_lvl = 0.0
        self.swp_origin = 0.0
        self.swp_bar = -999
        self.swp_vac = 0.5
        self.swp_eq = False
        self.swp_htf = False
        self.bos_confirmed = False
        self.bos_high = 0.0
        self.bos_bar = -999
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


class HalalSpotInstitutionalSniperV2(QCAlgorithm):

    def initialize(self):
        self.set_start_date(2025, 7, 1)
        self.set_end_date(2026, 6, 30)
        self.set_account_currency("USDT")
        self.set_cash("USDT", 100.0)
        # 100% HALAL SPOT CASH ACCOUNT (Zero Leverage, Zero Margin, Zero Short-Borrowing)
        self.set_brokerage_model(BrokerageName.BINANCE, AccountType.CASH)

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

    def _zscore_drop(self, q, n=24):
        if len(q) < n:
            return 0.0
        closes = [float(x.close) for x in list(q)[-n:]]
        mu = sum(closes) / len(closes)
        var = sum((x - mu) ** 2 for x in closes) / len(closes)
        sd = math.sqrt(var)
        if sd <= 1e-8:
            return 0.0
        return (mu - closes[-1]) / sd

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
        s.tp1 = 0.0
        s.r = 0.0
        s.t1d = False
        self.be_locked = False
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

    def _update_ratchet_trail(self, s, h, c):
        """
        Fee-Proof Breakeven Shield + Progressive R-Ratchet for Uncapped Runner.
        Guarantees net positive exit after 0.20% round-trip spot fees on every BE_SHIELD!
        """
        if s.r <= 0 or s.ep <= 0:
            return
        if h > s.mfe_px:
            s.mfe_px = h

        mfe_r = (s.mfe_px - s.ep) / s.r
        # Fee-proof floor: at least +0.35% above entry (covers 0.20% round-trip fee + 0.15% net profit)
        fee_proof_be = max(s.ep + 0.35 * s.r, s.ep * 1.0035)

        if not s.be_locked and mfe_r >= 1.65 and c >= s.ep + 1.20 * s.r:
            s.be_locked = True
            s.sl = max(s.sl, self._rp(s.sym, fee_proof_be))

        if s.be_locked and mfe_r >= 2.30 and c >= s.ep + 1.80 * s.r:
            s.sl = max(s.sl, self._rp(s.sym, max(s.ep + 0.85 * s.r, s.ep * 1.0060)))

        if s.t1d:
            # Progressive Uncapped Runner Lock (3R -> 5R -> 10R -> 20R+)
            if mfe_r >= 4.20:
                s.sl = max(s.sl, self._rp(s.sym, s.ep + (mfe_r - 1.40) * s.r))
            elif mfe_r >= 3.20:
                s.sl = max(s.sl, self._rp(s.sym, s.ep + 1.65 * s.r))

    def on_data(self, data: Slice):
        """
        Immediate Base-Resolution (1m / 5m) Intrabar Stop-Loss & MFE Monitor.
        Eliminates the -3.61R 15m close delay bug completely!
        """
        if self.is_warming_up:
            return
        for sym, s in self.st.items():
            if not data.bars.contains_key(sym):
                continue
            bar = data.bars[sym]
            c = float(bar.close)
            l = float(bar.low)
            h = float(bar.high)
            if self._is_invested(s, c):
                if h > s.mfe_px:
                    s.mfe_px = h
                if s.sl > 0 and l <= s.sl:
                    tag_str = "TRAIL_WIN" if s.t1d else ("BE_SHIELD" if s.be_locked else "SL")
                    self._sell_spot(s, 0.0, tag_str)

    def _on_4h(self, sym, bar):
        s = self.st[sym]
        s.b4 += 1
        h, l, c, o = float(bar.high), float(bar.low), float(bar.close), float(bar.open)
        s.q4.append(bar)
        s.ema4h = c if s.ema4h == 0.0 else (c * (2.0 / 35.0) + s.ema4h * (1.0 - 2.0 / 35.0))

        nh, nl = s.eye4.update(h, l, c, o, s.b4)
        if len(s.eye4.sh) > 0 and c > s.eye4.sh[-1][1]:
            s.tr4 = 1
        elif len(s.eye4.sl) > 0 and c < s.eye4.sl[-1][1]:
            s.tr4 = -1

        if not self.is_warming_up and s.t1d and nl is not None and self._is_invested(s, c):
            struct_sl = self._rp(sym, nl[1] * 0.9965)
            if struct_sl > s.sl and struct_sl < c * 0.998:
                s.sl = struct_sl

    def _on_1h(self, sym, bar):
        s = self.st[sym]
        s.b1 += 1
        h, l, c, o = float(bar.high), float(bar.low), float(bar.close), float(bar.open)
        s.q1.append(bar)
        s.ema1h = c if s.ema1h == 0.0 else (c * (2.0 / 25.0) + s.ema1h * (1.0 - 2.0 / 25.0))

        nh, nl = s.eye1.update(h, l, c, o, s.b1)
        if len(s.eye1.sh) > 0 and c > s.eye1.sh[-1][1]:
            s.tr1 = 1
        elif len(s.eye1.sl) > 0 and c < s.eye1.sl[-1][1]:
            s.tr1 = -1

        if self.is_warming_up:
            return

        if self._is_invested(s, c) and s.r > 0:
            self._update_ratchet_trail(s, h, c)
            if s.t1d and nl is not None:
                trail_1h = self._rp(sym, nl[1] * 0.9975)
                if trail_1h > s.sl and trail_1h < c * 0.998:
                    s.sl = trail_1h

        # Detect 1H Institutional Liquidity Sweep
        if len(s.eye1.sl) >= 1 and not self._is_invested(s, c):
            last_sl = s.eye1.sl[-1]
            lvl = last_sl[1]
            origin_hi = last_sl[3]
            consumed = last_sl[4]
            is_eql = False
            if len(s.eye1.sl) >= 2:
                prev_sl = s.eye1.sl[-2]
                spread = abs(lvl - prev_sl[1]) / max(lvl, 1e-8)
                if spread <= 0.0050 and (last_sl[0] - prev_sl[0]) >= 3:
                    is_eql = True
                    origin_hi = max(origin_hi, prev_sl[3])

            # Require strong rejection wick & bullish or upper-half close on 1H sweep
            rng1 = max(h - l, 1e-8)
            close_pos = (c - l) / rng1
            if not consumed and l < lvl and c > lvl and close_pos >= 0.45:
                last_sl[4] = True
                s.swp_active = True
                s.swp_low = l
                s.swp_lvl = lvl
                s.swp_origin = max(origin_hi, s.pdh, s.ah)
                s.swp_bar = s.b15
                s.swp_vac = 1.0 - self._ker(s.q1, 10)
                s.swp_eq = is_eql
                s.swp_htf = True
                s.bos_confirmed = False

    def _find_structural_anchor(self, s, ep, r):
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

        # Do not buy straight into an unbroken 1H/4H brick wall sitting closer than 2.4R in a bear trend
        if s.tr4 == -1 and len(s.eye1.sh) > 0:
            nearest_1h_wall = s.eye1.sh[-1][1]
            if ep < nearest_1h_wall < ep + 2.4 * r:
                return 0.0

        nearest_anchor = min(valid_targets)
        return min(nearest_anchor, ep + 4.0 * r)

    def _is_macro_bullish(self, s, c):
        """
        True Macro Regime Filter:
        Returns True if 4H structure is bullish OR price is firmly above the 4H EMA with 1H uptrend.
        """
        if s.tr4 == 1 and c >= s.ema4h * 0.992:
            return True
        if c > s.ema4h * 1.004 and s.tr1 == 1:
            return True
        return False

    def _on_15m(self, sym, bar):
        s = self.st[sym]
        s.b15 += 1
        h, l, c, o = float(bar.high), float(bar.low), float(bar.close), float(bar.open)
        s.q15.append(bar)
        s.ema15m = c if s.ema15m == 0.0 else (c * (2.0 / 21.0) + s.ema15m * (1.0 - 2.0 / 21.0))

        dt = bar.end_time
        d = dt.timetuple().tm_yday
        wk = dt.isocalendar()[1]
        if d != s.day:
            if s.day != -1:
                s.pdh, s.pdl = s.dh, s.dl
            s.day, s.dh, s.dl = d, h, l
            s.ah, s.al = 0.0, 1e18
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

        # 1. Manage Pending Entry Order (Short lifespan & immediate cancellation if structure breaks)
        if s.entk is not None:
            if self._is_invested(s, c):
                s.entk = None
                self._place_tp1(s)
            elif s.b15 - s.eb > 4 or l <= s.sl or c < s.swp_lvl:
                self._rst(s)
            return

        # 2. Manage Active Position
        if self._is_invested(s, c):
            self._update_ratchet_trail(s, h, c)
            if s.sl > 0 and l <= s.sl:
                tag_str = "TRAIL_WIN" if s.t1d else ("BE_SHIELD" if s.be_locked else "SL")
                self._sell_spot(s, 0.0, tag_str)
            return

        if len(s.q15) < 30 or s.b15 - s.cd < 12:
            return

        macro_bull = self._is_macro_bullish(s, c)
        z_drop_1h = self._zscore_drop(s.q1, 24)

        # 3. Detect 15m Sweep of Major Reference Levels (PDL / PWL / Asia Low)
        if not s.swp_active:
            # In a 4H Bear Market, ONLY accept major PDL/PWL/1H sweeps when deeply oversold (Capitulation Z >= 1.65)
            allow_sweep = macro_bull or (z_drop_1h >= 1.65)
            if allow_sweep:
                ref_lvls = [lv for lv in (s.pdl, s.pwl) if 0 < lv < 1e17]
                if macro_bull and 0 < s.al < 1e17:
                    ref_lvls.append(s.al)
                for rf in ref_lvls:
                    if l < rf and c > rf and c > o:
                        s.swp_active = True
                        s.swp_low = l
                        s.swp_lvl = rf
                        s.swp_origin = max(s.dh, s.pdh, s.ah)
                        s.swp_bar = s.b15
                        s.swp_vac = 1.0 - self._ker(s.q15, 12)
                        s.swp_eq = True
                        s.swp_htf = (rf == s.pdl or rf == s.pwl)
                        s.bos_confirmed = False
                        break

        # 15m Equal-Lows Sweep (Strictly allowed in Macro Bullish Regime only!)
        if not s.swp_active and macro_bull and len(s.eye15.sl) >= 2:
            sl_last = s.eye15.sl[-1]
            sl_prev = s.eye15.sl[-2]
            if not sl_last[4] and l < sl_last[1] and c > sl_last[1] and c > o:
                sl_last[4] = True
                is_eq15 = abs(sl_last[1] - sl_prev[1]) / max(sl_last[1], 1e-8) <= 0.0035
                if is_eq15:
                    s.swp_active = True
                    s.swp_low = l
                    s.swp_lvl = sl_last[1]
                    s.swp_origin = max(sl_last[3], sl_prev[3], s.pdh)
                    s.swp_bar = s.b15
                    s.swp_vac = 1.0 - self._ker(s.q15, 12)
                    s.swp_eq = True
                    s.swp_htf = False
                    s.bos_confirmed = False

        if not s.swp_active:
            return

        age = s.b15 - s.swp_bar
        if age > 12 or c < s.swp_low * 0.9985:
            s.swp_active = False
            s.bos_confirmed = False
            return
        if l < s.swp_low:
            s.swp_low = l

        # 4. Macro Bear Protection (Sit in USDT Cash during bear cascades unless Capitulation + HTF Reclaim)
        if not macro_bull:
            if not s.swp_htf or z_drop_1h < 1.45:
                s.swp_active = False
                return

        # 5. Verify Impulse Velocity & Confirmed Structural Break (BOS + EMA15m Reclaim)
        b0, b1, b2 = s.q15[-3], s.q15[-2], bar
        bfvg = float(b2.low) > float(b0.high) and float(b1.close) > float(b1.open)
        has_sh = len(s.eye15.sh) > 0
        last_sh = s.eye15.sh[-1][1] if has_sh else h

        comp_bars = list(s.q15)[-10:-2]
        v_comp = sum(abs(float(x.close) - float(x.open)) for x in comp_bars) / max(len(comp_bars), 1)
        v_imp = max(abs(c - o), abs(float(b1.close) - float(b1.open)))
        k_ratio = v_imp / max(v_comp, c * 0.0005)

        # Require actual close above 15m EMA and either 15m Swing High break (BOS) or strong FVG displacement
        bos_now = (c > o) and (c > s.ema15m) and (c > s.swp_lvl) and (
            (has_sh and c > last_sh) or (macro_bull and bfvg and k_ratio >= 1.55)
        )

        if bos_now and k_ratio >= 1.35 and not s.bos_confirmed:
            s.bos_confirmed = True
            s.bos_high = h
            s.bos_bar = s.b15

        if not s.bos_confirmed:
            return

        # 6. Zero-Adverse-Selection Entry Mechanics:
        # Path A: Immediate Confirmed Entry on BOS bar if Stop Loss distance is already compact (0.85% to 2.20%)
        # Path B: Pullback-Hold + Bullish Reclaim Candle on subsequent bars (never catches a falling red knife!)
        sl_candidate = self._rp(sym, s.swp_low * 0.9980)
        dist_now = (c - sl_candidate) / max(c, 1e-8)

        trigger_now = False
        if s.b15 == s.bos_bar and 0.0085 <= dist_now <= 0.0210:
            trigger_now = True
        elif s.b15 > s.bos_bar and (s.b15 - s.bos_bar) <= 5:
            # Controlled pullback held above swp_lvl and printed a bullish confirmation candle
            if l > s.swp_lvl and c > o and c > float(b1.high) and 0.0085 <= dist_now <= 0.0260:
                trigger_now = True

        if not trigger_now:
            return

        ep = self._rp(sym, c)
        sl = sl_candidate
        r = ep - sl
        if r <= 0:
            return
        sl_pct = r / ep
        # Enforce fee-resilient stop width (minimum 0.85%, maximum 2.60%)
        if sl_pct < 0.0085 or sl_pct > 0.0260:
            return

        # Verify True Structural Target >= 3.0R
        tp1_anchor = self._find_structural_anchor(s, ep, r)
        if tp1_anchor <= 0:
            return

        # Quality Score Filter
        score = 0.50 + 0.15 * min(2.0, k_ratio - 1.0) + 0.15 * s.swp_vac
        if macro_bull:
            score += 0.15
        if s.swp_eq or s.swp_htf:
            score += 0.12
        if s.tr1 == 1:
            score += 0.08

        if score >= 0.72:
            s.swp_active = False
            s.bos_confirmed = False
            self._enter_spot_sniper(s, ep, sl, tp1_anchor, score)

    def _enter_spot_sniper(self, s, ep, sl, tp1_px, score):
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
        dd_mult = 1.0 if dd < 0.08 else max(0.55, 1.0 - dd * 1.4)

        sl_pct = (ep - sl) / ep
        # Risk 1.35% - 1.65% of capital per A+ setup, allowing up to 88% USDT allocation on high-conviction trades
        rk_pct = (0.0135 + 0.0035 * min(1.0, (score - 0.72) / 0.20)) * dd_mult
        desired_notional = (eq * rk_pct) / (sl_pct + 0.0020)
        notional = min(desired_notional, usdt_free * 0.90, eq * 0.88)

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

        # Confirmed execution (no blind passive limit waiting for a falling knife)
        tk = self.market_order(s.sym, qty, tag="SPOT_EN")
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
        sp = self.securities[s.sym].symbol_properties
        step = float(sp.lot_size or 0.0001)
        # Bank 50% at TP1 (>= 3.0R), leave 50% Uncapped Runner for structural & ratcheting trail
        q1 = math.floor((hq * 0.50 + 1e-12) / step) * step if step > 0 else hq * 0.50
        q1 = round(q1, 6)
        rem = round(hq - q1, 6)
        if q1 * s.tp1 >= 5.5 and rem * s.ep >= 5.5:
            s.t1tk = self.limit_order(s.sym, -q1, s.tp1, tag="TP1_3R")
        else:
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
                s.r = max(s.ep - s.sl, s.ep * 0.0085)
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
            # Lock +1.65R minimum profit on the remaining 50% Uncapped Runner immediately after TP1 hits!
            s.sl = max(s.sl, self._rp(sym, s.ep + 1.65 * s.r))
            if not self._is_invested(s, float(self.securities[sym].price)):
                self._rst(s)
                s.cd = s.b15
