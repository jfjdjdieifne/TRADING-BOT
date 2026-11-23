# region imports
from AlgorithmImports import *
import numpy as np
from collections import deque
# endregion


class TopoSwing:
    """Confirmed structural pivot engine with unbroken obstacle purging."""

    def __init__(self, k=3, max_len=50):
        self.k = k
        self.w = 2 * k + 1
        self.hb = deque(maxlen=self.w)
        self.lb = deque(maxlen=self.w)
        self.sh = deque(maxlen=max_len)
        self.sl = deque(maxlen=max_len)
        self.uh = deque(maxlen=max_len)
        self.ul = deque(maxlen=max_len)

    def update(self, h, l, bar_idx):
        if h <= 0 or l <= 0:
            return
        while self.uh and h > self.uh[-1][1]:
            self.uh.pop()
        while self.ul and l < self.ul[-1][1]:
            self.ul.pop()

        self.hb.append(h)
        self.lb.append(l)
        if len(self.hb) < self.w:
            return

        ch = self.hb[self.k]
        if all(ch >= self.hb[i] for i in range(self.w) if i != self.k):
            if not self.sh or bar_idx - self.sh[-1][0] >= self.k:
                p = (bar_idx - self.k, ch)
                self.sh.append(p)
                if ch >= max(self.hb):
                    self.uh.append(p)

        cl = self.lb[self.k]
        if all(cl <= self.lb[i] for i in range(self.w) if i != self.k):
            if not self.sl or bar_idx - self.sl[-1][0] >= self.k:
                p = (bar_idx - self.k, cl)
                self.sl.append(p)
                if cl <= min(self.lb):
                    self.ul.append(p)

    def ceiling_above(self, price, min_dist):
        cands = [v for _, v in self.uh if v > price + min_dist]
        return min(cands) if cands else None

    def floor_below(self, price, min_dist):
        cands = [v for _, v in self.sl if v < price - min_dist]
        return max(cands) if cands else None

    def higher_lows(self):
        return len(self.sl) >= 2 and self.sl[-1][1] > self.sl[-2][1]


class CoinState:
    def __init__(self, symbol, ticker):
        self.symbol = symbol
        self.ticker = ticker

        self.o5 = deque(maxlen=300)
        self.h5 = deque(maxlen=300)
        self.l5 = deque(maxlen=300)
        self.c5 = deque(maxlen=300)
        self.v5 = deque(maxlen=300)

        self.o15 = deque(maxlen=200)
        self.h15 = deque(maxlen=200)
        self.l15 = deque(maxlen=200)
        self.c15 = deque(maxlen=200)
        self.v15 = deque(maxlen=200)

        self.o1h = deque(maxlen=240)
        self.h1h = deque(maxlen=240)
        self.l1h = deque(maxlen=240)
        self.c1h = deque(maxlen=240)
        self.v1h = deque(maxlen=240)

        self.o4h = deque(maxlen=260)
        self.h4h = deque(maxlen=260)
        self.l4h = deque(maxlen=260)
        self.c4h = deque(maxlen=260)
        self.v4h = deque(maxlen=260)

        self.b5 = 0
        self.b15 = 0
        self.b1h = 0
        self.b4h = 0

        self.sw5 = TopoSwing(k=3, max_len=50)
        self.sw15 = TopoSwing(k=3, max_len=50)
        self.sw1h = TopoSwing(k=3, max_len=50)
        self.sw4h = TopoSwing(k=4, max_len=50)

        self.ema20_5 = 0.0
        self.ema50_5 = 0.0
        self.ema20_15 = 0.0
        self.ema50_15 = 0.0
        self.ema20_1h = 0.0
        self.ema50_1h = 0.0
        self.ema200_1h = 0.0
        self.ema20_4h = 0.0
        self.ema50_4h = 0.0
        self.ema200_4h = 0.0

        self.atr5 = 0.0
        self.atr15 = 0.0
        self.atr1h = 0.0
        self.vma5 = 0.0
        self.vma1h = 0.0
        self.rsi5 = 50.0

        self.rs_score = 0.0
        self.rs_rank = 99
        self.ret7d = 0.0
        self.ret30d = 0.0
        self.trend_bull = False

        self.in_pos = False
        self.arm = ""
        self.ep = 0.0
        self.sl = 0.0
        self.tp = 0.0
        self.init_risk = 0.0
        self.eb = 0
        self.mfe_price = 0.0
        self.mfe_r = 0.0
        self.stage = 0
        self.cooldown_until = 0
        self.consec_losses = 0

    def reset_pos(self):
        self.in_pos = False
        self.arm = ""
        self.ep = 0.0
        self.sl = 0.0
        self.tp = 0.0
        self.init_risk = 0.0
        self.eb = 0
        self.mfe_price = 0.0
        self.mfe_r = 0.0
        self.stage = 0


class BinanceFuturesMultiCoinV12(QCAlgorithm):
    """
    V16.1: V16 Heavy-Leader engine + Exit-Rigor and Monthly-Circuit fixes.
    Every change below is tied to a measured defect in the v2 run
    (DD 71.8%, WR 41%, losing months visible in the monthly Sharpe table):

      FIX-1  Moonbag touch-exit restored: V14 exited a trailed wave on
             `close <= sl*0.965`; V16 required TWO 4H closes below the raised
             SL, so a stage>=1 runner could bleed from +4R down to the 0.6R
             crash shield before any exit. Now ANY 5m close below the raised
             floor exits (SUPER_WAVE_HARVEST), plus the old 4H/macro rules.
      FIX-2  Lock ladder completed: added the missing 3.4R rung -> locks
             +2.40R, so the 3.5-4R near-miss zone (super-leaders that never
             confirm VC) can no longer round-trip to the 0.25/0.80R rungs.
      FIX-3  MONTHLY CIRCUIT [D] (the direct answer to "every month must be
             protected"):
               MTD <= -6%   -> new entries blocked (soft)
               MTD <= -10%  -> flatten everything + halt month (hard floor)
               MTD peak >= +10% then give back to +3% -> flatten + halt
               (the green month is BANKED, it cannot be given back)
      FIX-4  Daily circuit: >=3 losing exits today -> no entries today
             (owner's own prior constant, restored).
      FIX-5  peak_eq drawdown shield wired (was written, never read):
             DD >= 22% -> x0.65, DD >= 35% -> x0.45 applied to risk_pct AND
             alloc_cap (both, because the notional cap is what actually binds
             in this sizing).
      FIX-6  Unified exit wrapper: EVERY losing exit now increments
             consec_losses and applies the 36*min(4,n)-bar cooldown (before,
             only INVISIBLE_SL did); every winning exit resets the streak and
             applies a 12-bar cooldown (V14 had cd-after-TP; V16 dropped it,
             allowing instant re-entry churn).
      FIX-7  Dust sweep: sub-$2 zombie positions (the 0.000659-qty rows in
             the trades CSV) are liquidated on sight.
      FIX-8  FREE_STAGNANT keeps its dedicated 24-bar cooldown.

    Unchanged: all entry arms, gates, RS/macro logic, heavy-leader sizing
    identity (45%-58% per leader), min_rr 3.50 — the tested edge is untouched.
    """

    def initialize(self):
        self.set_start_date(2021, 1, 1)
        self.set_end_date(2026, 10, 31)
        self.set_account_currency("USDT")
        self.set_cash(100.0)

        self.set_brokerage_model(BrokerageName.BINANCE, AccountType.MARGIN)
        self.settings.free_portfolio_value_percentage = 0.05

        self.tickers = [
            "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
            "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "LINKUSDT", "SUIUSDT"
        ]

        self.coins = {}
        for t in self.tickers:
            sym = self.add_crypto(t, Resolution.MINUTE, Market.Binance).symbol
            self.securities[sym].set_leverage(3.0)
            st = CoinState(sym, t)
            self.coins[sym] = st

            c5 = TradeBarConsolidator(timedelta(minutes=5))
            c5.data_consolidated += self._on_5m
            self.subscription_manager.add_consolidator(sym, c5)

            c15 = TradeBarConsolidator(timedelta(minutes=15))
            c15.data_consolidated += self._on_15m
            self.subscription_manager.add_consolidator(sym, c15)

            c1h = TradeBarConsolidator(timedelta(hours=1))
            c1h.data_consolidated += self._on_1h
            self.subscription_manager.add_consolidator(sym, c1h)

            c4h = TradeBarConsolidator(timedelta(hours=4))
            c4h.data_consolidated += self._on_4h
            self.subscription_manager.add_consolidator(sym, c4h)

        self.set_warm_up(timedelta(days=35))

        self.min_rr = 3.50
        self.max_positions = 3
        self.macro_breadth = 0.5
        self.macro_bull = False
        self.macro_bear = False
        self.peak_eq = 100.0

        # --- Monthly / daily protection circuit. [D] = design constants ---
        # Chosen ABOVE the strategy's normal equity noise: a tighter floor
        # would trip on ordinary swings and freeze the system permanently.
        self.MONTH_SOFT = 0.06       # MTD <= -6%  -> block new entries
        self.MONTH_HARD = 0.10       # MTD <= -10% -> flatten all + halt month
        self.LOCK_PEAK = 0.10        # month reaches +10% MTD ...
        self.LOCK_FLOOR = 0.03       # ... then gives back to +3% -> BANK it
        self._month_key = None
        self._month_start_eq = 100.0
        self._month_peak = 0.0
        self._month_block = False
        self._month_halted = False
        self._day_key = None
        self._daily_losses = 0

    @staticmethod
    def _ema(prev, val, period):
        if prev <= 0:
            return val
        k = 2.0 / (period + 1.0)
        return val * k + prev * (1.0 - k)

    # ------------------------------------------------------------------ #
    # Monthly / daily circuit + unified exit + dust
    # ------------------------------------------------------------------ #
    def _update_day_and_month(self, eq):
        dkey = self.time.date()
        if dkey != self._day_key:
            self._day_key = dkey
            self._daily_losses = 0

        mkey = (self.time.year, self.time.month)
        if mkey != self._month_key:
            self._month_key = mkey
            self._month_start_eq = eq if eq > 0 else 100.0
            self._month_peak = 0.0
            self._month_block = False
            self._month_halted = False

        mtd = 0.0
        if self._month_start_eq > 0:
            mtd = (eq - self._month_start_eq) / self._month_start_eq
        if mtd > self._month_peak:
            self._month_peak = mtd

        if self._month_halted:
            self._month_block = True
            return
        if mtd <= -self.MONTH_HARD:
            self._flat_all("MONTH_HARD_STOP")
            self._month_halted = True
            self._month_block = True
        elif mtd <= -self.MONTH_SOFT:
            self._month_block = True
        elif self._month_peak >= self.LOCK_PEAK and mtd <= self.LOCK_FLOOR:
            self._flat_all("MONTH_GAIN_LOCK")
            self._month_halted = True
            self._month_block = True

    def _flat_all(self, tag):
        for st in self.coins.values():
            if self.portfolio[st.symbol].invested:
                self._full_close(st.symbol, tag)
            if st.in_pos:
                st.reset_pos()

    def _exit(self, s: "CoinState", tag, cd_bars=None):
        """Full close with unified streak / cooldown bookkeeping (FIX-6)."""
        c = s.c5[-1] if s.c5 else s.ep
        self._full_close(s.symbol, tag)
        if s.ep > 0 and c < s.ep:
            s.consec_losses += 1
            self._daily_losses += 1
            s.cooldown_until = s.b5 + (cd_bars if cd_bars is not None
                                       else 36 * min(4, s.consec_losses))
        else:
            s.consec_losses = 0
            s.cooldown_until = s.b5 + (cd_bars if cd_bars is not None else 12)
        s.reset_pos()

    def _on_5m(self, sender, bar: TradeBar):
        s = self.coins.get(bar.symbol)
        if s is None:
            return
        o = float(bar.open)
        h = float(bar.high)
        l = float(bar.low)
        c = float(bar.close)
        v = float(bar.volume)
        pc = s.c5[-1] if s.c5 else c

        s.o5.append(o)
        s.h5.append(h)
        s.l5.append(l)
        s.c5.append(c)
        s.v5.append(v)
        s.b5 += 1

        s.sw5.update(h, l, s.b5)
        s.ema20_5 = self._ema(s.ema20_5, c, 20)
        s.ema50_5 = self._ema(s.ema50_5, c, 50)

        tr = max(h - l, abs(h - pc), abs(l - pc))
        s.atr5 = self._ema(s.atr5, tr, 14) if s.atr5 > 0 else tr
        s.vma5 = self._ema(s.vma5, v, 20) if s.vma5 > 0 else v

        if len(s.c5) >= 15:
            diffs = [s.c5[i] - s.c5[i - 1] for i in range(-14, 0)]
            gains = [d for d in diffs if d > 0]
            losses = [-d for d in diffs if d < 0]
            g = np.mean(gains) if gains else 0.0
            ls = np.mean(losses) if losses else 0.0
            s.rsi5 = 100.0 if ls <= 1e-12 else 100.0 - (100.0 / (1.0 + g / ls))

        if self.is_warming_up:
            return

        self._sync_and_manage(s)

    def _on_15m(self, sender, bar: TradeBar):
        s = self.coins.get(bar.symbol)
        if s is None:
            return
        o = float(bar.open)
        h = float(bar.high)
        l = float(bar.low)
        c = float(bar.close)
        v = float(bar.volume)
        pc = s.c15[-1] if s.c15 else c

        s.o15.append(o)
        s.h15.append(h)
        s.l15.append(l)
        s.c15.append(c)
        s.v15.append(v)
        s.b15 += 1

        s.sw15.update(h, l, s.b15)
        s.ema20_15 = self._ema(s.ema20_15, c, 20)
        s.ema50_15 = self._ema(s.ema50_15, c, 50)
        tr = max(h - l, abs(h - pc), abs(l - pc))
        s.atr15 = self._ema(s.atr15, tr, 14) if s.atr15 > 0 else tr

    def _on_1h(self, sender, bar: TradeBar):
        s = self.coins.get(bar.symbol)
        if s is None:
            return
        o = float(bar.open)
        h = float(bar.high)
        l = float(bar.low)
        c = float(bar.close)
        v = float(bar.volume)
        pc = s.c1h[-1] if s.c1h else c

        s.o1h.append(o)
        s.h1h.append(h)
        s.l1h.append(l)
        s.c1h.append(c)
        s.v1h.append(v)
        s.b1h += 1

        s.sw1h.update(h, l, s.b1h)
        s.ema20_1h = self._ema(s.ema20_1h, c, 20)
        s.ema50_1h = self._ema(s.ema50_1h, c, 50)
        s.ema200_1h = self._ema(s.ema200_1h, c, 200)
        tr = max(h - l, abs(h - pc), abs(l - pc))
        s.atr1h = self._ema(s.atr1h, tr, 14) if s.atr1h > 0 else tr
        s.vma1h = self._ema(s.vma1h, v, 20) if s.vma1h > 0 else v

        self._update_rankings_and_regime()

    def _on_4h(self, sender, bar: TradeBar):
        s = self.coins.get(bar.symbol)
        if s is None:
            return
        o = float(bar.open)
        h = float(bar.high)
        l = float(bar.low)
        c = float(bar.close)
        v = float(bar.volume)
        s.o4h.append(o)
        s.h4h.append(h)
        s.l4h.append(l)
        s.c4h.append(c)
        s.v4h.append(v)
        s.b4h += 1

        s.sw4h.update(h, l, s.b4h)
        s.ema20_4h = self._ema(s.ema20_4h, c, 20)
        s.ema50_4h = self._ema(s.ema50_4h, c, 50)
        s.ema200_4h = self._ema(s.ema200_4h, c, 200)

    def _update_rankings_and_regime(self):
        ready = []
        bull_count = 0
        btc_bull = False
        btc_bear = False

        for s in self.coins.values():
            if len(s.c1h) < 48 or s.c1h[-1] <= 0:
                continue
            c = s.c1h[-1]
            c24 = s.c1h[-24] if len(s.c1h) >= 24 else s.c1h[0]
            c72 = s.c1h[-72] if len(s.c1h) >= 72 else s.c1h[0]
            c168 = s.c1h[-168] if len(s.c1h) >= 168 else s.c1h[0]

            r24 = (c - c24) / c24 if c24 > 0 else 0.0
            r72 = (c - c72) / c72 if c72 > 0 else 0.0
            r168 = (c - c168) / c168 if c168 > 0 else 0.0
            s.ret7d = r168

            if len(s.c4h) >= 180 and s.c4h[-180] > 0:
                s.ret30d = (c - s.c4h[-180]) / s.c4h[-180]
            else:
                s.ret30d = r168

            s.rs_score = 0.40 * r24 + 0.35 * r72 + 0.25 * r168

            e200 = s.ema200_4h if s.ema200_4h > 0 else s.ema200_1h
            s.trend_bull = (c > e200) and (c > s.ema50_1h) and (s.ema20_4h >= s.ema50_4h * 0.995)
            if s.trend_bull:
                bull_count += 1

            if s.ticker == "BTCUSDT":
                btc_bull = (c > e200) and (s.ema20_4h >= s.ema50_4h * 0.99)
                btc_bear = (c < e200 * 0.97) and (s.ema20_4h < s.ema50_4h)

            ready.append(s)

        ready.sort(key=lambda x: x.rs_score, reverse=True)
        for idx, st in enumerate(ready):
            st.rs_rank = idx + 1

        if ready:
            self.macro_breadth = bull_count / float(len(ready))
            self.macro_bull = (self.macro_breadth >= 0.50) or (self.macro_breadth >= 0.40 and btc_bull)
            self.macro_bear = (self.macro_breadth <= 0.20 and not btc_bull) or (btc_bear and self.macro_breadth <= 0.30)

    def _active_positions_count(self):
        return sum(1 for st in self.coins.values() if self.portfolio[st.symbol].invested)

    def _sync_and_manage(self, s: CoinState):
        eq = float(self.portfolio.total_portfolio_value)
        if eq > self.peak_eq:
            self.peak_eq = eq

        # FIX-3 / FIX-4: month & day circuits run on every 5m sync
        self._update_day_and_month(eq)

        holding = self.portfolio[s.symbol]
        invested = holding.invested and holding.quantity > 0

        if not invested:
            if s.in_pos:
                s.reset_pos()
            self._evaluate_entry(s)
        else:
            # FIX-7: sweep sub-$2 zombie positions before anything else
            px = float(self.securities[s.symbol].price)
            if holding.quantity * px < 2.0:
                self._full_close(s.symbol, "DUST_SWEEP")
                if s.in_pos:
                    s.reset_pos()
                return
            if not s.in_pos:
                s.in_pos = True
                s.ep = float(holding.average_price)
                s.eb = s.b5
                s.mfe_price = float(s.c5[-1])
                s.init_risk = max(s.ep * 0.03, s.atr1h * 1.5 if s.atr1h > 0 else s.ep * 0.03)
                s.sl = s.ep - s.init_risk
                s.tp = s.ep + self.min_rr * s.init_risk
            self._manage_open_position(s)

    def _full_close(self, sym, tag):
        self.transactions.cancel_open_orders(sym)
        if self.portfolio[sym].invested:
            self.liquidate(sym, tag=tag)

    def _partial_close(self, sym, frac, tag):
        holding = self.portfolio[sym]
        if not holding.invested or holding.quantity <= 0:
            return
        sp = self.securities[sym].symbol_properties
        lot = float(sp.lot_size) if sp and sp.lot_size > 0 else 0.0001
        min_q = float(sp.minimum_order_size) if sp and sp.minimum_order_size else lot
        price = float(self.securities[sym].price)

        raw_q = float(holding.quantity) * frac
        sell_q = float(np.floor(raw_q / lot) * lot)
        rem_q = float(holding.quantity) - sell_q

        if sell_q < min_q or sell_q * price < 6.0:
            return
        if rem_q < min_q or rem_q * price < 6.0:
            return

        self.market_order(sym, -sell_q, tag=tag)

    def _manage_open_position(self, s: CoinState):
        c = s.c5[-1]
        h = s.h5[-1]
        ir = s.init_risk if s.init_risk > 1e-10 else s.ep * 0.03

        if h > s.mfe_price:
            s.mfe_price = h
        cur_r = (c - s.ep) / ir
        peak_r = (s.mfe_price - s.ep) / ir
        if peak_r > s.mfe_r:
            s.mfe_r = peak_r

        # 1. Profit-Shield ladder before 3.5R — FIX-2 adds the 3.4R rung
        if s.stage == 0:
            lock = 0.0
            if s.mfe_r >= 3.4:
                lock = s.ep + 2.40 * ir
            elif s.mfe_r >= 2.8:
                lock = s.ep + 0.80 * ir
            elif s.mfe_r >= 2.2:
                lock = s.ep + 0.25 * ir
            if lock > s.sl:
                s.sl = lock

        # 2. Non-Leader Full 3.5R Cash Take-Profit
        is_super_leader = (s.rs_rank <= 3 and s.trend_bull and (self.macro_bull or s.ret30d > 0.15))
        if s.stage == 0 and cur_r >= self.min_rr and not is_super_leader:
            self._exit(s, "TP_3_5R_FULL_CASH")
            return

        # 3. Super-Cycle Multi-Stage Venture Capital Harvest
        if s.stage == 0 and cur_r >= 4.0:
            self._partial_close(s.symbol, 0.25, "VC_HARVEST_1_4R")
            s.sl = max(s.sl, s.ep + 1.25 * ir)
            s.stage = 1
            s.consec_losses = 0

        elif s.stage == 1 and cur_r >= 8.0:
            self._partial_close(s.symbol, 0.20, "VC_HARVEST_2_8R")
            s.sl = max(s.sl, s.ep + 4.50 * ir)
            s.stage = 2

        elif s.stage == 2 and cur_r >= 15.0:
            self._partial_close(s.symbol, 0.20, "VC_HARVEST_3_15R")
            s.sl = max(s.sl, s.ep + 9.00 * ir)
            s.stage = 3

        elif s.stage == 3 and cur_r >= 25.0:
            self._partial_close(s.symbol, 0.25, "VC_HARVEST_4_25R")
            s.sl = max(s.sl, s.ep + 18.00 * ir)
            s.stage = 4

        # 4. Wide 4H Structural Wave Trail for Moonbag (Stage >= 1)
        if s.stage >= 1:
            if s.stage >= 2 and c <= s.ep + 0.60 * ir:
                self._exit(s, "STAGE2_CRASH_SHIELD")
                return

            atr4h = max(s.atr1h * 2.2, c * 0.015)
            if len(s.l4h) >= 24:
                struct_floor = min(list(s.l4h)[-96:]) - 1.20 * atr4h
            else:
                struct_floor = s.ep + 1.20 * ir
            ema_floor = s.ema200_4h * 0.965 if s.ema200_4h > 0 else 0.0
            wave_floor = max(s.ep + 1.20 * ir, struct_floor, ema_floor)
            if wave_floor > s.sl:
                s.sl = wave_floor

            # FIX-1: TOUCH EXIT — any 5m close below the raised floor leaves.
            # (V14 had this: close <= sl*0.965. V16 only checked two 4H
            #  closes, letting winners bleed for hours before exiting.)
            if c <= s.sl:
                self._exit(s, "SUPER_WAVE_HARVEST")
                return

            c4_break = len(s.c4h) >= 2 and s.c4h[-1] < s.sl and s.c4h[-2] < s.sl
            if c4_break or self.macro_bear or (not self.macro_bull and c < s.ema50_4h):
                self._exit(s, "SUPER_WAVE_HARVEST")
                return
            return

        # 5. Stage 0 Invisible Candle-Close Stop
        c15_confirmed = len(s.c15) >= 1 and s.c15[-1] <= s.sl
        deep_breach = c <= s.sl - 0.35 * s.atr5
        if c <= s.sl and (c15_confirmed or deep_breach):
            tag = "PROFIT_SHIELD_LOCK" if s.sl > s.ep else "INVISIBLE_SL"
            self._exit(s, tag)
            return

        # 6. Free Stagnant Capital on Dead Non-Leader Trades
        bars_held = s.b5 - s.eb
        if bars_held >= 288 and s.stage == 0 and s.mfe_r < 1.0 and cur_r < 0.20:
            if s.rs_rank > 3 or not self.macro_bull:
                self._exit(s, "FREE_STAGNANT_CAPITAL", cd_bars=24)

    def _build_structural_sl(self, s: CoinState, c: float, raw_sl: float, min_pct=0.025, max_pct=0.068):
        atr_floor = max(s.atr1h * 1.15, c * min_pct)
        dist = max(c - raw_sl, atr_floor)
        if dist > c * max_pct:
            return None
        return c - dist

    def _scan_arms(self, s: CoinState):
        if len(s.c5) < 60 or len(s.c15) < 40 or len(s.c1h) < 50 or len(s.c4h) < 30:
            return None

        c = s.c5[-1]
        o = s.o5[-1]
        h = s.h5[-1]
        l = s.l5[-1]
        v = s.v5[-1]
        atr5 = max(s.atr5, c * 0.002)
        atr15 = max(s.atr15, c * 0.003)
        atr1h = max(s.atr1h, c * 0.006)
        vr5 = v / s.vma5 if s.vma5 > 0 else 1.0

        # ARM 0: V12_CAP (Bear / Flash-Crash Extreme Capitulation Sniper)
        if len(s.c1h) >= 48 and s.ema50_4h > 0:
            drop_from_4h = (s.ema50_4h - c) / s.ema50_4h
            if drop_from_4h >= 0.16 and s.rsi5 < 32.0 and vr5 >= 3.0:
                if c > o and (c - l) >= 0.55 * max(h - l, 1e-9) and c > s.c5[-2]:
                    sl_low = min(min(list(s.l5)[-12:]), l) - 0.6 * atr5
                    sl = self._build_structural_sl(s, c, sl_low, min_pct=0.030, max_pct=0.075)
                    if sl is not None:
                        return ("V12_CAP", sl)

        if self.macro_bear:
            return None

        if not s.trend_bull:
            return None

        max_allowed_rank = 4 if self.macro_bull else 2
        if s.rs_rank > max_allowed_rank:
            return None

        if not self.macro_bull and s.ret30d < 0.08:
            return None

        # ARM 1: V8_4H (4H Macro Trend Pullback Continuation)
        trend_4h = c > s.ema20_4h > s.ema50_4h and s.sw4h.higher_lows()
        if trend_4h:
            near_1h_ema = min(list(s.l5)[-16:]) <= s.ema20_1h + 0.35 * atr1h
            reclaim_5m = c > s.ema20_5 and c > o and c > s.h5[-2] and vr5 >= 1.25
            if near_1h_ema and reclaim_5m:
                fl = s.sw1h.floor_below(c, 0.8 * atr1h)
                raw_sl = (fl - 0.35 * atr1h) if fl else (min(list(s.l1h)[-8:]) - 0.4 * atr1h)
                sl = self._build_structural_sl(s, c, raw_sl, min_pct=0.025, max_pct=0.062)
                if sl is not None:
                    return ("V8_4H", sl)

        # ARM 2: V11_1H (1H Structural Breakout & Higher-Low Continuation)
        trend_1h = c > s.ema20_1h > s.ema50_1h and c > s.ema20_4h
        if trend_1h:
            pullback_15m = min(list(s.l15)[-6:]) <= s.ema20_15 + 0.25 * atr15
            trigger_5m = c > s.ema20_5 and c > max(list(s.h5)[-8:-1]) and vr5 >= 1.35
            if pullback_15m and trigger_5m:
                fl = s.sw15.floor_below(c, 1.0 * atr15)
                raw_sl = (fl - 0.4 * atr15) if fl else (min(list(s.l15)[-10:]) - 0.4 * atr15)
                sl = self._build_structural_sl(s, c, raw_sl, min_pct=0.024, max_pct=0.058)
                if sl is not None:
                    return ("V11_1H", sl)

        # ARM 3: V10_IGN (Momentum & Volume Ignition Breakout)
        if s.rs_rank <= 3 and c > s.ema20_1h and c > s.ema20_4h:
            box_hi = max(list(s.h15)[-20:-1])
            box_lo = min(list(s.l15)[-20:-1])
            tight_box = (box_hi - box_lo) <= 2.8 * atr1h
            body = c - o
            if tight_box and c > box_hi and body >= 1.1 * atr5 and vr5 >= 2.2:
                raw_sl = max(box_lo, c - 1.8 * atr1h)
                sl = self._build_structural_sl(s, c, raw_sl, min_pct=0.025, max_pct=0.060)
                if sl is not None:
                    return ("V10_IGN", sl)

        # ARM 4: V9_LON (Session Liquidity Sweep & Reclaim)
        hr = self.time.hour
        if (7 <= hr <= 11 or 13 <= hr <= 17) and c > s.ema50_1h and c > s.ema50_4h:
            prev_lo = min(list(s.l15)[-16:-2])
            swept = min(l, s.l5[-2]) < prev_lo
            reclaimed = c > prev_lo and c > s.ema20_5 and c > o and vr5 >= 1.5
            if swept and reclaimed:
                raw_sl = min(l, s.l5[-2]) - 0.5 * atr5
                sl = self._build_structural_sl(s, c, raw_sl, min_pct=0.024, max_pct=0.055)
                if sl is not None:
                    return ("V9_LON", sl)

        # ARM 5: V6_SWP (Structural Swing Low Spring)
        if len(s.sw15.sl) >= 1 and c > s.ema50_1h and c > s.ema50_4h:
            last_swing_low = s.sw15.sl[-1][1]
            if min(l, s.l5[-2]) < last_swing_low and c > last_swing_low and c > o and vr5 >= 1.5:
                raw_sl = min(l, s.l5[-2]) - 0.5 * atr5
                sl = self._build_structural_sl(s, c, raw_sl, min_pct=0.024, max_pct=0.055)
                if sl is not None:
                    return ("V6_SWP", sl)

        return None

    def _evaluate_entry(self, s: CoinState):
        # FIX-3 / FIX-4: monthly circuit + daily loss circuit guard FIRST
        if self._month_block or self._month_halted:
            return
        if self._daily_losses >= 3:
            return
        if s.b5 < s.cooldown_until:
            return
        max_pos = self.max_positions if self.macro_bull else 2
        if self._active_positions_count() >= max_pos:
            return

        sig = self._scan_arms(s)
        if sig is None:
            return

        arm, sl = sig
        c = s.c5[-1]
        risk_dist = c - sl
        if risk_dist <= c * 0.020:
            return

        tp = c + self.min_rr * risk_dist

        ceil_4h = s.sw4h.ceiling_above(c, risk_dist * 0.7)
        if ceil_4h is not None and ceil_4h < c + 2.4 * risk_dist:
            if s.rs_rank > 2:
                return

        eq = float(self.portfolio.total_portfolio_value)
        free_margin = float(self.portfolio.margin_remaining)
        if eq < 12.0 or free_margin < 8.0:
            return

        # HEAVY LEADER COMPOUNDING SIZING (unchanged identity from V16)
        if s.rs_rank == 1:
            risk_pct = 0.038 if self.macro_bull else 0.028
            alloc_cap = 0.58 if self.macro_bull else 0.45
        elif s.rs_rank == 2:
            risk_pct = 0.032 if self.macro_bull else 0.024
            alloc_cap = 0.48 if self.macro_bull else 0.38
        else:
            risk_pct = 0.025
            alloc_cap = 0.38

        if arm == "V12_CAP":
            risk_pct = 0.025
            alloc_cap = 0.42

        # FIX-5: drawdown shield (peak_eq was written but never read).
        # Scaled on BOTH risk and cap: the cap is what actually binds.
        dd = (self.peak_eq - eq) / self.peak_eq if self.peak_eq > 0 else 0.0
        if dd >= 0.35:
            dd_mult = 0.45
        elif dd >= 0.22:
            dd_mult = 0.65
        else:
            dd_mult = 1.0
        risk_pct *= dd_mult
        alloc_cap *= dd_mult

        risk_dollars = eq * risk_pct
        qty_by_risk = risk_dollars / risk_dist
        notional_by_risk = qty_by_risk * c

        max_notional = min(eq * alloc_cap, free_margin * 0.88)
        final_notional = min(notional_by_risk, max_notional)

        if final_notional < 6.0:
            return

        sp = self.securities[s.symbol].symbol_properties
        lot = float(sp.lot_size) if sp and sp.lot_size > 0 else 0.0001
        min_q = float(sp.minimum_order_size) if sp and sp.minimum_order_size else lot
        qty = float(np.floor((final_notional / c) / lot) * lot)

        if qty < min_q or qty * c < 6.0:
            return

        tag = f"{arm}|RS{s.rs_rank}|RR{self.min_rr:.1f}"
        ticket = self.market_order(s.symbol, qty, tag=tag)
        if ticket.status != OrderStatus.INVALID:
            s.in_pos = True
            s.arm = arm
            s.ep = c
            s.sl = sl
            s.tp = tp
            s.init_risk = risk_dist
            s.eb = s.b5
            s.mfe_price = c
            s.mfe_r = 0.0
            s.stage = 0
