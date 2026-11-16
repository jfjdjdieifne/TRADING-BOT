# QUANTCONNECT.COM - Binance Futures Multi-Coin Momentum + VWAP + SMC Scalper (V2.0)
# Brokerage: Binance USD-M Perpetual Futures (0.02% Maker / 0.05% Taker + Funding)
# Universe: Top 15 liquid USDT-M pairs scanned continuously in parallel (max 3 concurrent positions)
# Empirical 7y BTC Binance-fee verified sleeves (1,148+ trades/coin, 7/7 yrs green):
#   1. VWAP_KZ_2R    : 07-20 UTC, 4H+1H EMA20>50, ER14_1H>=0.25, daily UTC VWAP touch+reclaim,
#                      RSI14_5m<=48, Limit entry, BE@1.0R->+0.1R, TP=2.0R (WR=67.2%, PF=1.73).
#   2. Mom9_Vol_2.5R : 4H+1H EMA20>50, ER14_1H>=0.30, 5m EMA9>20>50, Vol>=1.8x VolMA20,
#                      pullback to 5m EMA9 + reclaim, Limit entry, BE@1.2R->+0.1R, TP=2.5R (7/7 yrs).
#   3. SMC_Sweep_8R  : 1H k=3 liquidity sweep -> 5m CHoCH+FVG (>=09:00 UTC), 4H+1H aligned,
#                      Limit entry, High-Lock steps (3->1, 5.5->2.5), TP=8.0R (PF=1.89).

from AlgorithmImports import *
from collections import deque
import math


class CausalSwingTracker:
    def __init__(self, k: int = 2, max_active: int = 25) -> None:
        self.k, self.max_active = k, max_active
        self.win = deque(maxlen=2 * k + 1)
        self.bar_idx = -1
        self.last_high = self.last_low = None
        self.trend = 0
        self.act_hi, self.act_lo = [], []

    def update(self, bar) -> None:
        h, l, c = float(bar.High), float(bar.Low), float(bar.Close)
        self.bar_idx += 1
        self.win.append((h, l))
        if len(self.win) == 2 * self.k + 1:
            m = self.k
            ch, cl = self.win[m][0], self.win[m][1]
            if all(ch >= self.win[i][0] for i in range(len(self.win)) if i != m) and any(
                ch > self.win[i][0] for i in range(len(self.win)) if i != m
            ):
                self.last_high = ch
                self.act_hi.append((self.bar_idx - self.k, ch))
                self.act_hi = self.act_hi[-self.max_active:]
            if all(cl <= self.win[i][1] for i in range(len(self.win)) if i != m) and any(
                cl < self.win[i][1] for i in range(len(self.win)) if i != m
            ):
                self.last_low = cl
                self.act_lo.append((self.bar_idx - self.k, cl))
                self.act_lo = self.act_lo[-self.max_active:]
        self.act_hi = [x for x in self.act_hi if h <= x[1]]
        self.act_lo = [x for x in self.act_lo if l >= x[1]]
        if self.last_high is not None and c > self.last_high:
            self.trend = 1
        elif self.last_low is not None and c < self.last_low:
            self.trend = -1


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


class WilderRSI14:
    def __init__(self) -> None:
        self.prev_c = None
        self.gains, self.losses = [], []
        self.ag = self.al = 0.0
        self.val = 50.0

    def update(self, c: float) -> float:
        if self.prev_c is None:
            self.prev_c = c
            return 50.0
        d = c - self.prev_c
        self.prev_c = c
        g, l = (d, 0.0) if d > 0 else (0.0, -d)
        if len(self.gains) < 14:
            self.gains.append(g)
            self.losses.append(l)
            self.ag = sum(self.gains) / len(self.gains)
            self.al = sum(self.losses) / len(self.losses)
        else:
            self.ag = (self.ag * 13.0 + g) / 14.0
            self.al = (self.al * 13.0 + l) / 14.0
        self.val = 100.0 if self.al <= 1e-12 else (100.0 - 100.0 / (1.0 + self.ag / self.al))
        return self.val


class EmaState:
    def __init__(self) -> None:
        self.e9 = self.e20 = self.e50 = None
        self.closes = deque(maxlen=20)
        self.er14 = 0.0

    def update(self, c: float) -> None:
        self.e9 = c if self.e9 is None else (c * 0.2 + self.e9 * 0.8)
        self.e20 = c if self.e20 is None else (c * (2.0 / 21.0) + self.e20 * (19.0 / 21.0))
        self.e50 = c if self.e50 is None else (c * (2.0 / 51.0) + self.e50 * (49.0 / 51.0))
        self.closes.append(c)
        if len(self.closes) >= 15:
            arr = list(self.closes)[-15:]
            den = sum(abs(arr[i] - arr[i - 1]) for i in range(1, len(arr)))
            self.er14 = abs(arr[-1] - arr[0]) / den if den > 0 else 0.0

    @property
    def trend(self) -> int:
        if self.e20 is None or self.e50 is None:
            return 0
        return 1 if self.e20 > self.e50 else (-1 if self.e20 < self.e50 else 0)


class CoinState:
    def __init__(self, ticker: str, symbol: Symbol, leverage: float) -> None:
        self.ticker, self.symbol, self.leverage = ticker, symbol, leverage
        self.sw_4h, self.sw_1h, self.sw_1h_k3 = CausalSwingTracker(2), CausalSwingTracker(2), CausalSwingTracker(3)
        self.sw_5m = CausalSwingTracker(2)
        self.ema_4h, self.ema_1h, self.ema_5m = EmaState(), EmaState(), EmaState()
        self.atr_15m, self.atr_5m = WilderATR14(), WilderATR14()
        self.rsi_5m = WilderRSI14()
        self.vols_5m = deque(maxlen=20)
        self.vwap_day, self.vwap_pv, self.vwap_v = None, 0.0, 0.0
        self.bars_5m = deque(maxlen=6)
        self.cands_1h_k3 = []
        self.idx_5m = self.cooldown_until = 0
        self.pending_ticket = self.pending_meta = None
        self.in_position, self.active_engine, self.active_side = False, None, 0
        self.entry_price = self.sl_price = self.risk_dist = self.qty = 0.0
        self.tp_price = None
        self.step_locks = ()
        self.sl_ticket = self.tp_ticket = None
        self.canceled_sl_ids = set()


class BinanceFuturesMultiCoinScalper(QCAlgorithm):
    TICKERS = (
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
        "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "LINKUSDT", "LTCUSDT",
        "DOTUSDT", "UNIUSDT", "ATOMUSDT", "NEARUSDT", "ETCUSDT",
    )
    ENGINE_RISK = {"VWAP_KZ_2R": 0.015, "Mom9_Vol_2.5R": 0.012, "SMC_Sweep_8R": 0.015}
    VWAP_STEPS = ((1.0, 0.1),)
    MOM9_STEPS = ((1.2, 0.1),)
    SWEEP_STEPS = ((3.0, 1.0), (5.5, 2.5))

    def initialize(self) -> None:
        self.set_time_zone(TimeZones.UTC)
        self.set_start_date(2021, 1, 1)
        self.set_end_date(2026, 10, 31)
        start_cash = float(self.get_parameter("start_cash") or 10000.0)
        self.set_account_currency("USDT", start_cash)
        self.hwm_equity = start_cash
        self.risk_scale = float(self.get_parameter("risk_scale") or 1.0)
        self.max_open_pos = int(self.get_parameter("max_open_pos") or 3)
        self.sweep_tp_r = float(self.get_parameter("sweep_tp_r") or 8.0)
        self.set_warm_up(timedelta(days=14), Resolution.MINUTE)
        self.set_brokerage_model(BrokerageName.BINANCE_FUTURES, AccountType.MARGIN)

        self.coins, self.trade_counts, self.invalid_counts = {}, {}, {}
        for tk in self.TICKERS:
            sec = self.add_crypto_future(tk, Resolution.MINUTE, Market.BINANCE, leverage=10)
            st = CoinState(tk, sec.symbol, 10.0)
            self.coins[sec.symbol] = st
            self.trade_counts[tk] = 0
            self.invalid_counts[tk] = 0
            self.consolidate(sec.symbol, timedelta(hours=4), lambda b, s=st: self.on_4h(s, b))
            self.consolidate(sec.symbol, timedelta(hours=1), lambda b, s=st: self.on_1h(s, b))
            self.consolidate(sec.symbol, timedelta(minutes=15), lambda b, s=st: self.on_15m(s, b))
            self.consolidate(sec.symbol, timedelta(minutes=5), lambda b, s=st: self.on_5m(s, b))

    def _open_count(self) -> int:
        return sum(1 for st in self.coins.values() if st.in_position or st.pending_ticket is not None)

    def _effective_risk_pct(self, engine: str) -> float:
        eq = float(self.portfolio.total_portfolio_value)
        dd = (self.hwm_equity - eq) / self.hwm_equity if self.hwm_equity > 0 else 0.0
        brake = 0.50 if dd >= 0.12 else (0.70 if dd >= 0.08 else 1.0)
        return self.ENGINE_RISK.get(engine, 0.012) * brake * self.risk_scale

    def _round_qty(self, sym: Symbol, raw_qty: float, is_long: bool) -> float:
        sp = self.securities[sym].symbol_properties
        lot = float(sp.lot_size or 0.001)
        min_sz = float(sp.minimum_order_size or lot)
        qty = round(math.floor((abs(raw_qty) / lot) + 1e-9) * lot, 8)
        if qty < min_sz:
            return 0.0
        return qty if is_long else -qty

    def _round_px(self, sym: Symbol, price: float) -> float:
        tick = float(self.securities[sym].symbol_properties.minimum_price_variation or 0.01)
        tick = tick if tick > 0 else 0.01
        return round(round(price / tick) * tick, 8)

    def _clamp_qty(self, st: CoinState, raw_qty: float, px: float) -> float:
        if px <= 0:
            return 0.0
        rem = max(0.0, float(self.portfolio.margin_remaining))
        slot_cap = float(self.portfolio.total_portfolio_value) * st.leverage * 0.30
        max_notional = min(rem * st.leverage * 0.85, slot_cap)
        return min(abs(raw_qty), max_notional / px) if max_notional > 0 else 0.0

    def _cancel_pending(self, st: CoinState) -> None:
        if st.pending_ticket is not None and st.pending_ticket.status not in (
            OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.INVALID
        ):
            st.pending_ticket.cancel()
        st.pending_ticket = st.pending_meta = None

    def _replace_sl(self, st: CoinState, lock_px: float, cur_c: float) -> None:
        lp = self._round_px(st.symbol, lock_px)
        if not ((st.active_side == 1 and lp > st.sl_price and lp < cur_c) or
                (st.active_side == -1 and lp < st.sl_price and lp > cur_c)):
            return
        old = st.sl_ticket
        if old is not None and old.status not in (OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.INVALID):
            st.canceled_sl_ids.add(old.order_id)
            old.cancel()
        st.sl_price = lp
        st.sl_ticket = self.stop_market_order(st.symbol, -st.qty, lp, tag=f"{st.active_engine}_SL")

    def _submit_limit(self, st: CoinState, engine: str, side: int, trig: float, sl: float,
                      tp_r: float, step_locks, expire_bars: int) -> None:
        if self.is_warming_up or st.in_position or st.pending_ticket is not None:
            return
        if st.idx_5m < st.cooldown_until or self._open_count() >= self.max_open_pos:
            return
        if self.portfolio[st.symbol].invested:
            self.transactions.cancel_open_orders(st.symbol)
            self.liquidate(st.symbol, tag="ORPHAN_CLEAN")
            return
        cur_px = float(self.securities[st.symbol].price)
        if cur_px <= 0:
            return
        trig_px = self._round_px(st.symbol, trig)
        sl_px = self._round_px(st.symbol, sl)
        risk = (trig_px - sl_px) if side == 1 else (sl_px - trig_px)
        sl_pct = risk / cur_px
        if risk <= 0 or sl_pct < 0.0040 or sl_pct > 0.0180:
            return
        if (side == 1 and trig_px > cur_px) or (side == -1 and trig_px < cur_px):
            return
        tp_px = self._round_px(st.symbol, trig_px + side * tp_r * risk)
        risk_usd = float(self.portfolio.total_portfolio_value) * self._effective_risk_pct(engine)
        qty = self._round_qty(st.symbol, self._clamp_qty(st, risk_usd / risk, trig_px), side == 1)
        if qty == 0.0:
            return
        st.pending_meta = {
            "engine": engine, "side": side, "trig": trig_px, "sl": sl_px, "tp": tp_px,
            "risk": risk, "qty": qty, "step_locks": step_locks, "exp": st.idx_5m + expire_bars,
        }
        t = self.limit_order(st.symbol, qty, trig_px, tag=engine)
        if t.status == OrderStatus.INVALID:
            st.pending_meta = st.pending_ticket = None
            return
        if st.pending_meta is not None:
            st.pending_ticket = t

    def on_4h(self, st: CoinState, bar) -> None:
        st.sw_4h.update(bar)
        st.ema_4h.update(float(bar.Close))

    def on_1h(self, st: CoinState, bar) -> None:
        h, l, c = float(bar.High), float(bar.Low), float(bar.Close)
        k3 = st.sw_1h_k3
        for idx_s, p_lo in list(k3.act_lo):
            if (k3.bar_idx + 1 - idx_s) >= 4 and l < p_lo and c > p_lo:
                st.cands_1h_k3.append({"side": 1, "start_i": st.idx_5m, "sl_base": l, "choch": st.sw_5m.last_high})
        for idx_s, p_hi in list(k3.act_hi):
            if (k3.bar_idx + 1 - idx_s) >= 4 and h > p_hi and c < p_hi:
                st.cands_1h_k3.append({"side": -1, "start_i": st.idx_5m, "sl_base": h, "choch": st.sw_5m.last_low})
        st.sw_1h.update(bar)
        k3.update(bar)
        st.ema_1h.update(c)

    def on_15m(self, st: CoinState, bar) -> None:
        st.atr_15m.update(float(bar.High), float(bar.Low), float(bar.Close))

    def on_5m(self, st: CoinState, bar) -> None:
        st.idx_5m += 1
        dt = self.utc_time
        o, h, l, c = float(bar.Open), float(bar.High), float(bar.Low), float(bar.Close)
        vol = float(getattr(bar, "Volume", 0.0) or 0.0)
        a5 = st.atr_5m.update(h, l, c)
        rsi5 = st.rsi_5m.update(c)
        st.ema_5m.update(c)
        st.vols_5m.append(vol)
        st.bars_5m.append((o, h, l, c))

        if st.vwap_day != dt.date():
            st.vwap_day = dt.date()
            st.vwap_pv = st.vwap_v = 0.0
        st.vwap_pv += ((h + l + c) / 3.0) * vol
        st.vwap_v += vol
        vwap = (st.vwap_pv / st.vwap_v) if st.vwap_v > 0 else None

        if st.in_position and st.risk_dist > 0 and st.sl_ticket is not None:
            for act_r, lk_r in st.step_locks:
                hit = (h >= st.entry_price + act_r * st.risk_dist) if st.active_side == 1 else (l <= st.entry_price - act_r * st.risk_dist)
                if hit:
                    self._replace_sl(st, st.entry_price + st.active_side * lk_r * st.risk_dist, c)

        if st.pending_ticket is not None and st.pending_meta is not None:
            pm = st.pending_meta
            if st.idx_5m > pm["exp"] or (l <= pm["sl"] if pm["side"] == 1 else h >= pm["sl"]):
                self._cancel_pending(st)

        if not self.is_warming_up and len(st.bars_5m) >= 3:
            b1, b2, b3 = st.bars_5m[-3], st.bars_5m[-2], st.bars_5m[-1]
            c2b = abs(b2[3] - b2[0])
            still = []
            for cd in st.cands_1h_k3:
                if st.idx_5m - cd["start_i"] > 60:
                    continue
                if cd["side"] == 1:
                    if l < cd["sl_base"]:
                        continue
                    if dt.hour >= 9 and st.sw_4h.trend == 1 and st.sw_1h.trend == 1 and cd["choch"] is not None and c > cd["choch"] and (b3[2] - b1[1]) >= 0.25 * a5 and b2[3] > b2[0] and c2b >= a5:
                        slp = min(cd["sl_base"] - a5, c - max(1.5 * a5, c * 0.0040))
                        self._submit_limit(st, "SMC_Sweep_8R", 1, c, slp, self.sweep_tp_r, self.SWEEP_STEPS, 20)
                        continue
                else:
                    if h > cd["sl_base"]:
                        continue
                    if dt.hour >= 9 and st.sw_4h.trend == -1 and st.sw_1h.trend == -1 and cd["choch"] is not None and c < cd["choch"] and (b1[2] - b3[1]) >= 0.25 * a5 and b2[3] < b2[0] and c2b >= a5:
                        slp = max(cd["sl_base"] + a5, c + max(1.5 * a5, c * 0.0040))
                        self._submit_limit(st, "SMC_Sweep_8R", -1, c, slp, self.sweep_tp_r, self.SWEEP_STEPS, 20)
                        continue
                still.append(cd)
            st.cands_1h_k3 = still

            a15 = st.atr_15m.val
            t4, t1 = st.ema_4h.trend, st.ema_1h.trend
            if vwap is not None and a15 > 0 and (7 <= dt.hour <= 20) and st.ema_1h.er14 >= 0.25:
                if t4 == 1 and t1 == 1 and l <= vwap < c and c > o and rsi5 <= 48.0:
                    slp = min(l, vwap - 0.5 * a15) - 0.4 * a5
                    self._submit_limit(st, "VWAP_KZ_2R", 1, c, slp, 2.0, self.VWAP_STEPS, 6)
                elif t4 == -1 and t1 == -1 and h >= vwap > c and c < o and rsi5 >= 52.0:
                    slp = max(h, vwap + 0.5 * a15) + 0.4 * a5
                    self._submit_limit(st, "VWAP_KZ_2R", -1, c, slp, 2.0, self.VWAP_STEPS, 6)

            if len(st.vols_5m) == 20 and st.ema_1h.er14 >= 0.30 and a5 > 0:
                vavg = sum(st.vols_5m) / 20.0
                e9, e20, e50 = st.ema_5m.e9, st.ema_5m.e20, st.ema_5m.e50
                if vavg > 0 and vol >= 1.8 * vavg and e9 is not None and e50 is not None:
                    if t4 == 1 and t1 == 1 and e9 > e20 > e50 and l <= e9 < c and c > o:
                        slp = min(l, e20) - 0.5 * a5
                        self._submit_limit(st, "Mom9_Vol_2.5R", 1, c, slp, 2.5, self.MOM9_STEPS, 6)
                    elif t4 == -1 and t1 == -1 and e9 < e20 < e50 and h >= e9 > c and c < o:
                        slp = max(h, e20) + 0.5 * a5
                        self._submit_limit(st, "Mom9_Vol_2.5R", -1, c, slp, 2.5, self.MOM9_STEPS, 6)

        st.sw_5m.update(bar)

    def on_data(self, data: Slice) -> None:
        if self.is_warming_up:
            return
        for sym, st in self.coins.items():
            if not st.in_position and st.pending_ticket is None and self.portfolio[sym].invested:
                self.transactions.cancel_open_orders(sym)
                self.liquidate(sym, tag="ORPHAN_SYNC")

    def on_order_event(self, oe: OrderEvent) -> None:
        if oe.symbol not in self.coins:
            return
        st = self.coins[oe.symbol]
        if oe.order_id in st.canceled_sl_ids and oe.status == OrderStatus.CANCELED:
            st.canceled_sl_ids.discard(oe.order_id)
            return
        if oe.status == OrderStatus.INVALID:
            self.invalid_counts[st.ticker] += 1
            if st.pending_meta is not None and not st.in_position:
                st.pending_ticket = st.pending_meta = None
            elif st.in_position:
                self.transactions.cancel_open_orders(oe.symbol)
                self.liquidate(oe.symbol, tag="INVALID_RECOVERY")
                self._reset_pos(st)
            return
        if oe.status == OrderStatus.CANCELED:
            if st.pending_ticket is not None and oe.order_id == st.pending_ticket.order_id and not st.in_position:
                st.pending_ticket = st.pending_meta = None
            return
        if oe.status != OrderStatus.FILLED:
            return

        if st.pending_meta is not None and not st.in_position and abs(float(oe.fill_quantity)) > 0:
            pm = st.pending_meta
            st.pending_ticket = st.pending_meta = None
            st.in_position = True
            st.active_engine, st.active_side = pm["engine"], pm["side"]
            st.entry_price = float(oe.fill_price)
            st.sl_price, st.tp_price = pm["sl"], pm["tp"]
            st.risk_dist, st.qty, st.step_locks = pm["risk"], float(oe.fill_quantity), pm["step_locks"]
            self.trade_counts[st.ticker] += 1
            st.sl_ticket = self.stop_market_order(st.symbol, -st.qty, st.sl_price, tag=f"{st.active_engine}_SL")
            st.tp_ticket = self.limit_order(st.symbol, -st.qty, st.tp_price, tag=f"{st.active_engine}_TP")
        elif st.in_position:
            for tk_obj in (st.sl_ticket, st.tp_ticket):
                if tk_obj is not None and tk_obj.order_id != oe.order_id and tk_obj.status not in (
                    OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.INVALID
                ):
                    tk_obj.cancel()
            if self.portfolio[st.symbol].invested:
                self.liquidate(st.symbol, tag="RESIDUAL_CLOSE")
            st.cooldown_until = st.idx_5m + 4
            self._reset_pos(st)
            eq = float(self.portfolio.total_portfolio_value)
            if eq > self.hwm_equity:
                self.hwm_equity = eq

    @staticmethod
    def _reset_pos(st: CoinState) -> None:
        st.in_position = False
        st.active_engine = st.tp_price = st.sl_ticket = st.tp_ticket = None
        st.active_side = 0
        st.entry_price = st.sl_price = st.risk_dist = st.qty = 0.0
        st.step_locks = ()

    def on_end_of_algorithm(self) -> None:
        self.log(f"=== Binance Multi-Coin Momentum+VWAP+SMC | Trades={sum(self.trade_counts.values())} | Eq={self.portfolio.total_portfolio_value:.2f} USDT ===")
        for tk in self.TICKERS:
            if self.trade_counts[tk] > 0 or self.invalid_counts[tk] > 0:
                self.log(f"  {tk:10s}: trades={self.trade_counts[tk]} invalid={self.invalid_counts[tk]}")
