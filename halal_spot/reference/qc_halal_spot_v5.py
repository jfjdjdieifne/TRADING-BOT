# region imports
from AlgorithmImports import *
from collections import deque
from datetime import timedelta
import math
# endregion


class PureSwingEye:
    """
    Self-Scaling Visual Wave Detector.
    Identifies structural Swing Highs and Swing Lows purely from the chart's own rolling
    candle range distribution (mu + sigma), with zero fixed percentage thresholds.
    Records the exact structural Origin_Anchor of every downward wave.
    """
    def __init__(self):
        self.hi = -1e18
        self.lo = 1e18
        self.hi_i = 0
        self.lo_i = 0
        self.dir = 0
        self.rng_q = deque(maxlen=48)
        self.leg_q = deque(maxlen=20)
        self.sh = deque(maxlen=16)  # [idx, price, leg_size, consumed]
        self.sl = deque(maxlen=16)  # [idx, price, leg_size, origin_high, consumed]

    def update(self, h, l, c, o, idx):
        rng = max(h - l, 1e-8)
        self.rng_q.append(rng)
        n = len(self.rng_q)
        if n < 8:
            return None, None

        mu = sum(self.rng_q) / n
        var = sum((x - mu) ** 2 for x in self.rng_q) / n
        sigma = math.sqrt(var)
        # Purely self-referential wave reversal threshold: must exceed a full 2-sigma bar excursion
        th = (mu * 2.0) + (sigma * 1.5)

        nh, nl = None, None
        if self.dir == 0:
            if h > self.hi:
                self.hi, self.hi_i = h, idx
            if l < self.lo:
                self.lo, self.lo_i = l, idx
            if (self.hi - l) >= th and self.hi > -1e17:
                self.dir = -1
                leg = self.hi - l
                self.leg_q.append(leg)
                nh = [self.hi_i, self.hi, leg, False]
                self.sh.append(nh)
                self.lo, self.lo_i = l, idx
            elif (h - self.lo) >= th and self.lo < 1e17:
                self.dir = 1
                leg = h - self.lo
                self.leg_q.append(leg)
                orig = self.hi if self.hi > -1e17 else h
                nl = [self.lo_i, self.lo, leg, orig, False]
                self.sl.append(nl)
                self.hi, self.hi_i = h, idx
        elif self.dir == 1:
            if h > self.hi:
                self.hi, self.hi_i = h, idx
            elif (self.hi - l) >= th:
                self.dir = -1
                leg = self.hi - l
                self.leg_q.append(leg)
                nh = [self.hi_i, self.hi, leg, False]
                self.sh.append(nh)
                self.lo, self.lo_i = l, idx
        elif self.dir == -1:
            if l < self.lo:
                self.lo, self.lo_i = l, idx
            elif (h - self.lo) >= th:
                self.dir = 1
                leg = h - self.lo
                self.leg_q.append(leg)
                origin_anchor = self.hi
                if len(self.sh) >= 2:
                    origin_anchor = max(self.hi, self.sh[-1][1], self.sh[-2][1])
                nl = [self.lo_i, self.lo, leg, origin_anchor, False]
                self.sl.append(nl)
                self.hi, self.hi_i = h, idx
        return nh, nl

    def avg_wave_span(self, fallback):
        if not self.leg_q:
            return fallback
        return sum(self.leg_q) / len(self.leg_q)


class ChartThesis:
    """
    Working Memory of the Chart Mind.
    Tracks the complete visual story of a liquidity spring:
    IDLE -> SPRING_WATCH -> STALKING_SWEET_SPOT
    """
    def __init__(self):
        self.reset()

    def reset(self):
        self.stage = "IDLE"
        self.floor_px = 0.0          # Absolute invalidation wick low (F)
        self.reclaim_lvl = 0.0       # The swept structural level that buyers reclaimed
        self.origin_ceiling = 0.0    # Origin peak of the downward leg that swept the low
        self.breakdown_high = 0.0    # The micro high right before the sweep that buyers must break (BOS)
        self.impulse_peak = 0.0      # Highest point reached by the BOS impulse wave
        self.sweep_bar = -999
        self.bos_bar = -999
        self.buyer_dominance = 1.0   # Ratio of Buyer Reclaim Velocity to Seller Approach Velocity
        self.is_htf_spring = False   # True if 1H, 4H, PDL, PWL, or Equal-Lows spring


class CoinMindState:
    def __init__(self, sym, base_ccy):
        self.sym = sym
        self.base_ccy = base_ccy
        self.q15 = deque(maxlen=140)
        self.q1 = deque(maxlen=120)
        self.q4 = deque(maxlen=90)
        self.b15 = 0
        self.b1 = 0
        self.b4 = 0
        self.eye15 = PureSwingEye()
        self.eye1 = PureSwingEye()
        self.eye4 = PureSwingEye()
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
        self.thesis = ChartThesis()
        # Execution & Active Position State
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


class PurePhysicsChartMindV5(QCAlgorithm):
    """
    Pure Relational Chart Physics & Exact Fee-Adjusted Geometry Brain (V5).
    - Zero arbitrary stop-loss percentage cutoffs (no 1.00% vs 1.01% cliffs).
    - Compares Buyer Displacement directly against Seller Effort on the chart itself.
    - Uses the Exact Net Fee-Adjusted 3:1 Geometry Equation:
      Net_RRR(P) = ((M - P) - f*P) / ((P - F) + f*P) >= 3.0
      P_max = (M + 3*F) / (4*(1 + f))
      to decide automatically between Immediate Strike, Pullback Stalking, or Thesis Abort.
    """
    def initialize(self):
        self.set_start_date(2025, 7, 1)
        self.set_end_date(2026, 6, 30)
        self.set_account_currency("USDT")
        self.set_cash("USDT", 100.0)
        self.set_brokerage_model(BrokerageName.BINANCE, AccountType.CASH)

        self.round_trip_fee = 0.0020  # 0.10% buy + 0.10% sell on Binance Spot

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
            self.st[sym] = CoinMindState(sym, base_ccy)
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
        step = float(sp.lot_size or 0.00001)
        q = math.floor((max(0.0, raw_q) + 1e-12) / step) * step if step > 0 else max(0.0, raw_q)
        return round(q, 8)

    def _rq_buy(self, sym, qty, px):
        sp = self.securities[sym].symbol_properties
        step = float(sp.lot_size or 0.00001)
        mn = float(sp.minimum_order_size or 5.0)
        q = math.floor((abs(qty) + 1e-12) / step) * step if step > 0 else abs(qty)
        q = round(q, 8)
        if q <= 0 or px <= 0:
            return 0.0
        min_notional = max(5.5, mn * 1.05) if mn >= 1.0 else 5.5
        if q * px < min_notional or (mn < 1.0 and q < mn):
            return 0.0
        return q

    def _is_invested(self, s, px):
        hq = self._held_qty(s)
        return (hq * px) >= 5.2

    def _Read_Wave_Context(self, s, c):
        """
        Reads the Macro/Intermediate Story purely from Wave Topology (No arbitrary Z-score cutoffs!):
        1. STRUCTURAL_UPTREND: 4H or 1H wave is in confirmed bullish structure (Higher Lows / BOS above equilibrium).
        2. CLIMAX_EXHAUSTION: Both 4H and 1H are trending down, BUT the current downward leg has stretched
           further than the average historical wave span on the chart (rubber-band overextension).
        3. UNEXHAUSTED_CASCADE: Sellers are pushing down within normal wave spans with no structural support.
        """
        # Is 4H wave structurally bullish?
        h4_hl = len(s.eye4.sl) >= 2 and s.eye4.sl[-1][1] > s.eye4.sl[-2][1]
        h4_bull = (s.tr4 == 1 and c >= s.ema4h) or (h4_hl and c >= s.ema4h)

        # Is 1H wave structurally bullish (including multi-day relief waves inside a 4H bear market)?
        h1_hl = len(s.eye1.sl) >= 2 and s.eye1.sl[-1][1] >= s.eye1.sl[-2][1]
        h1_bull = (s.tr1 == 1 and c > s.ema1h) and (h1_hl or s.ema15m >= s.ema1h)

        if h4_bull or h1_bull:
            return "STRUCTURAL_UPTREND"

        # In a downtrend, compare the current drop from the last 1H/4H high against the chart's own average wave span!
        avg_1h_leg = s.eye1.avg_wave_span(abs(s.ema1h - c) * 1.5)
        last_1h_peak = s.eye1.sh[-1][1] if len(s.eye1.sh) > 0 else s.ema1h
        current_drop_span = max(0.0, last_1h_peak - c)

        # Also check if recent 1H selling candles expanded above average 1H candle range (climax throw-in)
        avg_1h_bar = sum( s.eye1.rng_q ) / max(len(s.eye1.rng_q), 1)
        rec_1h_bar = max((float(b.high) - float(b.low) for b in list(s.q1)[-3:]), default=avg_1h_bar)

        # Pure self-referential comparison: current drop leg > average wave leg, OR climax bar > 1.5x average bar
        if current_drop_span > avg_1h_leg * 1.15 or rec_1h_bar > avg_1h_bar * 1.55:
            return "CLIMAX_EXHAUSTION"

        return "UNEXHAUSTED_CASCADE"

    def _Find_True_Unobstructed_Ceiling(self, s, ref_px, context):
        """
        Looks up at the chart from ref_px and finds the TRUE structural target ceiling (M)
        WITHOUT cherry-picking or skipping over low overhead brick walls!
        """
        # 1. Identify the FIRST unbroken 1H and 4H swing highs sitting above ref_px
        overhead_1h = [sh[1] for sh in list(s.eye1.sh)[-6:] if sh[1] > ref_px]
        overhead_4h = [sh4[1] for sh4 in list(s.eye4.sh)[-4:] if sh4[1] > ref_px]

        first_1h_wall = min(overhead_1h) if overhead_1h else 1e18
        first_4h_wall = min(overhead_4h) if overhead_4h else 1e18

        # 2. Identify the natural liquidity magnet of the setup (Origin of the swept wave, PDH, PWH)
        natural_magnets = [x for x in (s.thesis.origin_ceiling, s.pdh, s.pwh, s.dh) if x > ref_px]
        if overhead_1h:
            natural_magnets.append(first_1h_wall)
        if overhead_4h:
            natural_magnets.append(first_4h_wall)

        if not natural_magnets:
            return 0.0

        primary_magnet = max(s.thesis.origin_ceiling, min(natural_magnets))

        # 3. Respect Overhead Brick Walls:
        # If 1H trend is still bearish (counter-trend spring), price CANNOT magically teleport through
        # the first unbroken 1H lower-high supply wall! So the ceiling is strictly capped by first_1h_wall!
        if s.tr1 == -1 and first_1h_wall < 1e17:
            return min(primary_magnet, first_1h_wall)

        # If 1H is bullish (relief wave) but 4H is bearish, the ceiling is capped by the first 4H supply wall!
        if s.tr4 == -1 and first_4h_wall < 1e17:
            return min(primary_magnet, first_4h_wall)

        return primary_magnet

    def _Compute_Net_Fee_Geometry(self, ceiling_m, floor_f, entry_p):
        """
        Exact Financial Physics of the Trade (Zero Arbitrary Cutoffs):
        Computes Net Reward-to-Risk Ratio after deducting Binance's 0.20% round-trip fee,
        and computes P_max: the exact highest price on the chart that yields >= 3.0:1 Net RRR!
        """
        f = self.round_trip_fee
        # Exact maximum entry price that guarantees Net RRR >= 3.0 after fees:
        # ((M - P) - f*P) / ((P - F) + f*P) = 3.0  =>  P_max = (M + 3*F) / (4*(1 + f))
        p_max = (ceiling_m + 3.0 * floor_f) / (4.0 * (1.0 + f))

        gross_risk = entry_p - floor_f
        if gross_risk <= 0:
            return -1.0, p_max

        net_reward = (ceiling_m - entry_p) - (f * entry_p)
        net_risk = gross_risk + (f * entry_p)
        net_rrr = net_reward / max(net_risk, 1e-8)
        return net_rrr, p_max

    def _Compare_Buyer_Vs_Seller_Physics(self, s, bar):
        """
        Direct Face-to-Face Comparison of Buyers vs. Sellers on the Chart:
        - Seller Approach Effort: Average downward body/range of the bars leading into the sweep low.
        - Buyer Reclaim Response: Upward displacement of the buyers reclaiming the level.
        - Structural Shift (BOS): Buyers close above the breakdown origin high (or last 15m swing high)
          AND above the 15m rolling equilibrium (EMA15m).
        """
        if len(s.q15) < 10:
            return False, 0.0
        bars = list(s.q15)[-10:]
        c, o, h, l = float(bar.close), float(bar.open), float(bar.high), float(bar.low)
        b0, b1 = bars[-3], bars[-2]

        # Measure Seller effort going into the low
        seller_bars = bars[:-2]
        seller_impulses = [max(float(b.open) - float(b.close), (float(b.high) - float(b.low)) * 0.45) for b in seller_bars]
        avg_seller_power = sum(seller_impulses) / max(len(seller_impulses), 1)

        # Measure Buyer response off the low
        buyer_impulse = max(
            c - o,
            float(b1.close) - float(b1.open),
            (c - s.thesis.floor_px) * 0.55
        )
        dominance_ratio = buyer_impulse / max(avg_seller_power, 1e-8)

        # Did buyers create a Fair Value Gap (FVG) or break the micro high that initiated the sweep?
        bfvg = (l > float(b0.high)) and (float(b1.close) > float(b1.open))
        struct_high = s.thesis.breakdown_high
        if len(s.eye15.sh) > 0:
            struct_high = min(struct_high, s.eye15.sh[-1][1]) if struct_high > 0 else s.eye15.sh[-1][1]

        reclaimed_equilibrium = (c > o) and (c > s.ema15m) and (c > s.thesis.reclaim_lvl)
        broke_structure = (struct_high > 0 and c > struct_high) or (bfvg and dominance_ratio > 1.25)

        # Pure relational condition: Buyers physically overpowered Sellers (dominance > 1.05) and broke structure!
        return (reclaimed_equilibrium and broke_structure and dominance_ratio > 1.05), dominance_ratio

    def _Is_Pullback_Turning_Up(self, s, bar):
        """
        Reads the Pullback Story:
        When stalking a discount entry (<= P_max) after a large BOS candle:
        1. Sellers must FAIL to break the reclaimed support level.
        2. The current bar must show buyers stepping back in (green candle closing in upper half
           and beating the prior bar's close or midpoint).
        3. The pullback must be corrective (average pullback bear body < impulse buyer body).
        """
        if len(s.q15) < 4:
            return False
        b_prev = s.q15[-2]
        c, o, h, l = float(bar.close), float(bar.open), float(bar.high), float(bar.low)
        c1, o1, h1, l1 = float(b_prev.close), float(b_prev.open), float(b_prev.high), float(b_prev.low)

        # Must hold above the swept floor and keep closes at/above the reclaimed level
        if l <= s.thesis.floor_px or c < s.thesis.reclaim_lvl:
            return False

        # Current candle must be a bullish turn
        rng = max(h - l, 1e-8)
        bullish_close = (c > o) and ((c - l) / rng >= 0.55) and (c > c1 or c >= (h1 + l1) * 0.5)
        if not bullish_close:
            return False

        # Compare pullback seller body against current buyer turn body (sellers must be weaker than the impulse!)
        prev_seller_body = max(0.0, o1 - c1)
        avg_15m_rng = sum(s.eye15.rng_q) / max(len(s.eye15.rng_q), 1)
        not_crash = prev_seller_body <= avg_15m_rng * 1.8

        return not_crash

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

    def _Manage_Open_Position(self, s, h, l, c):
        """
        Fee-Aware Position Management:
        1. Fee-Proof Breakeven Shield: Only activates after price has traveled > 55% of the way to 3R (+1.70R),
           and locks entry + (2 * round_trip_fee) so every BE_SHIELD is a guaranteed net profit!
        2. Pre-TP1 Profit Ratchet at +2.40R.
        3. Uncapped Runner Trail after TP1 (50% banked at >= 3.0R, remaining 50% trails structural lows & R-ratchet).
        """
        if s.r <= 0 or s.ep <= 0:
            return
        if h > s.mfe_px:
            s.mfe_px = h

        mfe_r = (s.mfe_px - s.ep) / s.r
        # Exact fee-proof floor: entry * (1 + 2 * round_trip_fee) = entry * 1.0040 (covers 0.20% fee + 0.20% net gain)
        fee_proof_floor = max(s.ep + 0.35 * s.r, s.ep * (1.0 + 2.0 * self.round_trip_fee))

        if not s.be_locked and mfe_r >= 1.70 and c >= s.ep + 1.20 * s.r:
            s.be_locked = True
            s.sl = max(s.sl, self._rp(s.sym, fee_proof_floor))

        if s.be_locked and mfe_r >= 2.40 and c >= s.ep + 1.85 * s.r:
            s.sl = max(s.sl, self._rp(s.sym, max(s.ep + 0.90 * s.r, s.ep * (1.0 + 3.5 * self.round_trip_fee))))

        if s.t1d:
            if mfe_r >= 4.20:
                s.sl = max(s.sl, self._rp(s.sym, s.ep + (mfe_r - 1.35) * s.r))
            elif mfe_r >= 3.20:
                s.sl = max(s.sl, self._rp(s.sym, s.ep + 1.75 * s.r))

    def on_data(self, data: Slice):
        """
        Immediate Intrabar (1m / 5m) Stop-Loss Execution.
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
            struct_sl = self._rp(sym, nl[1] * (1.0 - self.round_trip_fee))
            if struct_sl > s.sl and struct_sl < c:
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
            self._Manage_Open_Position(s, h, l, c)
            if s.t1d and nl is not None:
                trail_1h = self._rp(sym, nl[1] * (1.0 - self.round_trip_fee))
                if trail_1h > s.sl and trail_1h < c:
                    s.sl = trail_1h

        # Perceive 1H Structural Liquidity Sweep
        if len(s.eye1.sl) >= 1 and not self._is_invested(s, c):
            last_sl = s.eye1.sl[-1]
            lvl = last_sl[1]
            origin_hi = last_sl[3]
            consumed = last_sl[4]
            avg_1h_bar = sum(s.eye1.rng_q) / max(len(s.eye1.rng_q), 1)

            is_eql = False
            if len(s.eye1.sl) >= 2:
                prev_sl = s.eye1.sl[-2]
                # Equal lows defined relative to the chart's own average 1H candle range (zero fixed %)
                if abs(lvl - prev_sl[1]) <= avg_1h_bar * 0.65 and (last_sl[0] - prev_sl[0]) >= 3:
                    is_eql = True
                    origin_hi = max(origin_hi, prev_sl[3])

            rng1 = max(h - l, 1e-8)
            if not consumed and l < lvl and c > lvl and (c - l) / rng1 >= 0.45:
                context = self._Read_Wave_Context(s, c)
                if context != "UNEXHAUSTED_CASCADE" or is_eql:
                    last_sl[4] = True
                    if s.thesis.stage == "STALKING_SWEET_SPOT":
                        s.thesis.is_htf_spring = True
                        s.thesis.floor_px = min(s.thesis.floor_px, l)
                        s.thesis.origin_ceiling = max(s.thesis.origin_ceiling, origin_hi, s.pdh, s.ah)
                    else:
                        s.thesis.reset()
                        s.thesis.stage = "SPRING_WATCH"
                        s.thesis.floor_px = l
                        s.thesis.reclaim_lvl = lvl
                        s.thesis.origin_ceiling = max(origin_hi, s.pdh, s.ah)
                        s.thesis.breakdown_high = h
                        s.thesis.sweep_bar = s.b15
                        s.thesis.is_htf_spring = True

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

        # 1. Manage Pending Ticket
        if s.entk is not None:
            if self._is_invested(s, c):
                s.entk = None
                self._place_tp1(s)
            elif s.b15 - s.eb > 3 or l <= s.sl:
                self._rst(s)
            return

        # 2. Manage Open Position
        if self._is_invested(s, c):
            self._Manage_Open_Position(s, h, l, c)
            if s.sl > 0 and l <= s.sl:
                tag_str = "TRAIL_WIN" if s.t1d else ("BE_SHIELD" if s.be_locked else "SL")
                self._sell_spot(s, 0.0, tag_str)
            return

        if len(s.q15) < 35 or s.b15 - s.cd < 10:
            return

        context = self._Read_Wave_Context(s, c)
        avg_15m_bar = sum(s.eye15.rng_q) / max(len(s.eye15.rng_q), 1)

        # =========================================================================
        # STEP 1: PERCEIVE LIQUIDITY SWEEP IN CONTEXT
        # =========================================================================
        if s.thesis.stage == "IDLE":
            if context != "UNEXHAUSTED_CASCADE":
                # Major Session / Daily / Weekly Low Sweeps
                pools = [lv for lv in (s.pwl, s.pdl) if 0 < lv < 1e17]
                if context == "STRUCTURAL_UPTREND" and 0 < s.al < 1e17:
                    pools.append(s.al)

                for pool_px in pools:
                    if l < pool_px and c > pool_px and c > o:
                        s.thesis.reset()
                        s.thesis.stage = "SPRING_WATCH"
                        s.thesis.floor_px = l
                        s.thesis.reclaim_lvl = pool_px
                        s.thesis.origin_ceiling = max(s.dh, s.pdh, s.ah)
                        s.thesis.breakdown_high = max(h, float(s.q15[-2].high))
                        s.thesis.sweep_bar = s.b15
                        s.thesis.is_htf_spring = (pool_px == s.pdl or pool_px == s.pwl)
                        break

                # 15m Structural Swing Low / Double-Bottom Spring
                if s.thesis.stage == "IDLE" and len(s.eye15.sl) >= 2:
                    sl_last = s.eye15.sl[-1]
                    sl_prev = s.eye15.sl[-2]
                    if not sl_last[4] and l < sl_last[1] and c > sl_last[1] and c > o:
                        sl_last[4] = True
                        # Double-bottom similarity scaled to the chart's own 15m candle range
                        is_double_low = abs(sl_last[1] - sl_prev[1]) <= avg_15m_bar * 0.85
                        if is_double_low or context == "STRUCTURAL_UPTREND":
                            s.thesis.reset()
                            s.thesis.stage = "SPRING_WATCH"
                            s.thesis.floor_px = l
                            s.thesis.reclaim_lvl = sl_last[1]
                            s.thesis.origin_ceiling = max(sl_last[3], sl_prev[3], s.pdh)
                            s.thesis.breakdown_high = max(h, float(s.q15[-2].high))
                            s.thesis.sweep_bar = s.b15
                            s.thesis.is_htf_spring = is_double_low

        if s.thesis.stage == "IDLE":
            return

        # Invalidate thesis if floor breaks or setup goes stale
        age = s.b15 - s.thesis.sweep_bar
        if age > 16 or c < s.thesis.floor_px:
            s.thesis.reset()
            return
        if l < s.thesis.floor_px:
            s.thesis.floor_px = l

        # In a pure bear climax (counter-trend), require an HTF/Double-Low spring
        if context == "CLIMAX_EXHAUSTION" and not s.thesis.is_htf_spring:
            s.thesis.reset()
            return

        # =========================================================================
        # STEP 2: BUYER VS SELLER PHYSICS & STRUCTURAL SHIFT (BOS)
        # =========================================================================
        if s.thesis.stage == "SPRING_WATCH":
            buyers_won, dom_ratio = self._Compare_Buyer_Vs_Seller_Physics(s, bar)
            if not buyers_won:
                return

            s.thesis.buyer_dominance = dom_ratio
            s.thesis.bos_bar = s.b15
            s.thesis.impulse_peak = h

            # Map Floor (F) and True Unobstructed Ceiling (M) on the chart
            sl_px = self._rp(sym, s.thesis.floor_px - avg_15m_bar * 0.15)
            ceiling_m = self._Find_True_Unobstructed_Ceiling(s, c, context)
            if ceiling_m <= c or c <= sl_px:
                s.thesis.reset()
                return

            # Compute Exact Net Fee-Adjusted Geometry:
            # Net_RRR(c) and P_max (the exact price ceiling for entry that preserves >= 3.0R Net of Fees!)
            net_rrr_now, p_max = self._Compute_Net_Fee_Geometry(ceiling_m, sl_px, c)

            # Check if the ceiling M is so low that even pulling back to the swept level itself cannot give 3.0R!
            if p_max < s.thesis.reclaim_lvl:
                # Geometrically blocked by a low overhead wall -> Abort thesis!
                s.thesis.reset()
                return

            # Compare current impulse span against the chart's typical 1H wave span
            avg_1h_wave = s.eye1.avg_wave_span((ceiling_m - sl_px) * 0.5)
            impulse_fresh = (c - sl_px) <= avg_1h_wave * 0.85

            # Decision 1 (IMMEDIATE STRIKE):
            # Current price c is ALREADY <= P_max (meaning Net_RRR(c) >= 3.0 after fees!)
            # AND the BOS candle didn't over-consume the wave -> Enter Immediately!
            if c <= p_max and net_rrr_now >= 3.0 and impulse_fresh:
                s.thesis.reset()
                self._enter_spot_sniper(s, self._rp(sym, c), sl_px, ceiling_m, dom_ratio)
                return

            # Decision 2 (STALK DISCOUNT SWEET SPOT):
            # The BOS candle was huge (c > P_max), so entering now gives < 3.0R net of fees,
            # BUT P_max >= reclaim_lvl proves that a pullback into [reclaim_lvl .. P_max] WILL give >= 3.0R!
            s.thesis.stage = "STALKING_SWEET_SPOT"
            return

        # =========================================================================
        # STEP 3: STALKING THE GEOMETRIC SWEET SPOT (<= P_max) ON WIDE BOS WAVES
        # =========================================================================
        if s.thesis.stage == "STALKING_SWEET_SPOT":
            if h > s.thesis.impulse_peak:
                s.thesis.impulse_peak = h

            stalk_age = s.b15 - s.thesis.bos_bar
            if stalk_age > 10:
                s.thesis.reset()
                return

            sl_px = self._rp(sym, s.thesis.floor_px - avg_15m_bar * 0.15)
            ceiling_m = self._Find_True_Unobstructed_Ceiling(s, c, context)
            if ceiling_m <= c or c <= sl_px:
                s.thesis.reset()
                return

            # If price already ran up and touched 75% of the way to the ceiling without us -> Train left, Abort!
            if (s.thesis.impulse_peak - sl_px) >= 0.75 * (ceiling_m - sl_px):
                s.thesis.reset()
                return

            net_rrr_now, p_max = self._Compute_Net_Fee_Geometry(ceiling_m, sl_px, c)

            # Has price pulled back into the Geometric Sweet Spot (c <= P_max, so Net_RRR >= 3.0 after fees)
            # AND printed a bullish turning candle where buyers step back in?
            if c <= p_max and net_rrr_now >= 3.0:
                if self._Is_Pullback_Turning_Up(s, bar):
                    dom_ratio = s.thesis.buyer_dominance
                    s.thesis.reset()
                    self._enter_spot_sniper(s, self._rp(sym, c), sl_px, ceiling_m, dom_ratio)

    def _enter_spot_sniper(self, s, ep, sl, ceiling_m, dom_ratio):
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

        # Continuous Dynamic Position Sizing:
        # Automatically scales quantity inversely to stop distance + round-trip fees,
        # so dollar risk is constant (~1.4% - 1.7% of equity) regardless of stop width!
        sl_pct = (ep - sl) / ep
        conv_scale = min(1.0, max(0.0, (dom_ratio - 1.0) / 1.5))
        rk_pct = (0.0135 + 0.0035 * conv_scale) * dd_mult
        desired_notional = (eq * rk_pct) / (sl_pct + self.round_trip_fee)
        notional = min(desired_notional, usdt_free * 0.90, eq * 0.88)

        qty = self._rq_buy(s.sym, notional / ep, ep)
        if qty <= 0:
            return

        s.ep = ep
        s.sl = sl
        s.r = ep - sl
        # Cap TP1 at 4.0R if ceiling_m is huge so TP1 banks reliably while the second 50% runs uncapped
        tp1_target = min(ceiling_m, ep + 4.0 * s.r)
        s.tp1 = self._rp(s.sym, max(tp1_target, ep + 3.0 * s.r))
        s.eb = s.b15
        s.t1d = False
        s.be_locked = False
        s.mfe_px = ep
        s.cd = s.b15

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
        step = float(sp.lot_size or 0.00001)
        q1 = math.floor((hq * 0.50 + 1e-12) / step) * step if step > 0 else hq * 0.50
        q1 = round(q1, 8)
        rem = round(hq - q1, 8)
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
                s.r = max(s.ep - s.sl, s.ep * self.round_trip_fee)
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
            s.sl = max(s.sl, self._rp(sym, s.ep + 1.75 * s.r))
            if not self._is_invested(s, float(self.securities[sym].price)):
                self._rst(s)
                s.cd = s.b15
