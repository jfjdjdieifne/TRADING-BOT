# region imports
from AlgorithmImports import *
import math
from collections import deque
# endregion

FEE = 0.0020


def _sig(x):
    return 1.0 / (1.0 + math.exp(-max(-40.0, min(40.0, x))))


class TopoSwing:
    def __init__(self, lb=80):
        self.c, self.tr = deque(maxlen=lb), deque(maxlen=lb)
        self.ah, self.al = [], []
        self.idx, self.os, self.cnh, self.cnl = 0, 0, 0, 0
        self.eh, self.hi, self.el, self.li = None, -1, None, -1

    def update(self, h, l, c):
        pc = self.c[-1] if self.c else c
        self.c.append(c)
        self.tr.append(max(h - l, abs(h - pc), abs(l - pc)))
        self.idx += 1
        if len(self.tr) < 10:
            return
        atr = max(sum(self.tr) / len(self.tr), c * 1e-4)
        if self.eh is None or h > self.eh:
            self.eh, self.hi = h, self.idx
        if self.el is None or l < self.el:
            self.el, self.li = l, self.idx
        if self.os != -1 and (self.eh - c) >= 1.25 * atr and (self.idx - self.hi) >= 1:
            self.ah = (self.ah + [(self.hi, self.eh)])[-24:]
            self.cnh += 1
            self.os, self.el, self.li = -1, l, self.idx
        elif self.os != 1 and (c - self.el) >= 1.25 * atr and (self.idx - self.li) >= 1:
            self.al = (self.al + [(self.li, self.el)])[-24:]
            self.cnl += 1
            self.os, self.eh, self.hi = 1, h, self.idx

    def atr(self):
        return max(sum(self.tr) / len(self.tr), 1e-6) if self.tr else 1e-4

    def ker(self, n=12):
        if len(self.c) < n + 1:
            return 0.5
        cl = list(self.c)[-n - 1:]
        v = sum(abs(cl[i] - cl[i - 1]) for i in range(1, len(cl)))
        return abs(cl[-1] - cl[0]) / v if v > 1e-9 else 0.0

    def swp_rec(self, o, h, l, c, lvl, sd, atr):
        if lvl <= 0 or atr <= 0:
            return 0.0
        rng = max(h - l, 1e-8)
        if sd == -1:
            if h <= lvl or c >= lvl:
                return 0.0
            pen, wk, rj = (h - lvl) / atr, (h - max(o, c)) / rng, (lvl - c) / atr
        else:
            if l >= lvl or c <= lvl:
                return 0.0
            pen, wk, rj = (lvl - l) / atr, (min(o, c) - l) / rng, (c - lvl) / atr
        g = math.exp(-((pen - 0.55) ** 2) / (2.0 * 0.65 ** 2))
        return float(max(0.0, min(1.0, _sig(2.5 * (wk - 0.30)) * _sig(2.2 * (rj + 0.15)) * (0.4 + 0.6 * g))))


class CoinMemory:
    def __init__(self):
        self.ath, self.atl = 0.0, 1e18
        self.dh, self.dl = deque(maxlen=90), deque(maxlen=90)
        self.e20 = self.e50 = self.e120 = self.h20 = 0.0

    def on5(self, h, l):
        if h > self.ath:
            self.ath = h
        if 0 < l < self.atl:
            self.atl = l

    def on1h(self, c):
        self.h20 = c if self.h20 == 0.0 else self.h20 + (2.0 / 21.0) * (c - self.h20)

    def on4h(self, c):
        if self.e20 == 0.0:
            self.e20 = self.e50 = self.e120 = c
        else:
            self.e20 += (2.0 / 21.0) * (c - self.e20)
            self.e50 += (2.0 / 51.0) * (c - self.e50)
            self.e120 += (2.0 / 121.0) * (c - self.e120)

    def push(self, h, l):
        if h > 0 and l < 1e17:
            self.dh.append(h)
            self.dl.append(l)

    def hi(self, n=30):
        return max(list(self.dh)[-n:]) if self.dh else self.ath

    def lo(self, n=30):
        return min(list(self.dl)[-n:]) if self.dl else self.atl

    def coiled(self, c, sd):
        if len(self.dh) < 14:
            return False
        dh, dl = list(self.dh), list(self.dl)
        h10, l10, h35, l35 = max(dh[-10:]), min(dl[-10:]), max(dh[-35:]), min(dl[-35:])
        ratio = max(h10 - l10, c * 1e-4) / max(h35 - l35, c * 1e-4)
        if sd == 1:
            return (ratio <= 0.58 and c >= h10 * 0.992) or c >= self.hi(25) * 0.992
        return (ratio <= 0.58 and c <= l10 * 1.008) or c <= self.lo(25) * 1.008


class SymState:
    def __init__(self, sym):
        self.sym = sym
        self.mem = CoinMemory()
        self.sw1, self.sw15, self.sw4 = TopoSwing(80), TopoSwing(80), TopoSwing(90)
        self.b5 = self.b15 = self.b1 = self.b4 = 0
        self.q15, self.q1, self.q4 = deque(maxlen=24), deque(maxlen=32), deque(maxlen=96)
        self.v15, self.v1, self.v4 = deque(maxlen=24), deque(maxlen=24), deque(maxlen=24)
        self.pdh = self.pdl = self.pwh = self.pwl = 0.0
        self.cday = self.cwk = -1
        self.dh, self.dl, self.wh, self.wl = 0.0, 1e18, 0.0, 1e18
        self.sd4, self.sh4, self.sl4, self.ker4 = 0, 0.0, 0.0, 0.5
        self.sd1, self.sh1, self.sl1 = 0, 0.0, 0.0
        self.g4 = self.g1 = self.gi = self.gs = None
        self.armed = False
        self.mk = {1: -1, -1: -1}
        self.p0 = 0.0
        self.entk = self.sltk = None
        self.eng, self.wall, self.story = "", "", ""
        self.sd = self.ph = self.cb = self.e4 = self.eb = 0
        self.en = self.sl = self.tp = self.tpr = self.min_r = 0.0
        self.rd = self.qty = self.mfe = self.peak = self.a1 = self.score = 0.0
        self.pend = self.closing = False
        self.if_bos = self.if_fvg = self.if_vol = 0


class BinanceFuturesMultiCoinV12(QCAlgorithm):
    def initialize(self):
        y0 = int(self.get_parameter("y0") or 2021)
        y1 = int(self.get_parameter("y1") or 2021)
        self.set_start_date(y0, 1, 1)
        self.set_end_date(y1, 12, 31)
        self.set_account_currency("USDT")
        self.set_cash("USDT", 100.0)
        self.set_brokerage_model(BrokerageName.BINANCE_FUTURES, AccountType.MARGIN)
        self.settings.free_portfolio_value_percentage = 0.05
        self.shorts = (self.get_parameter("shorts") or "1") == "1"
        self.rbudget = float(self.get_parameter("rbudget") or 0.10)
        self.pk = self.wse = 100.0
        self.lwk, self.maxp, self.mode = -1, 5, "DAILY"
        self.cd, self.st, self.vt, self.stats, self.btc = {}, {}, {}, {}, None
        self.nbad, self._rt, self._rv = 0, None, None
        for t in ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
                  "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "LINKUSDT", "SUIUSDT"]:
            s = self.add_crypto_future(t, Resolution.MINUTE, Market.BINANCE).symbol
            self.securities[s].set_leverage(10)
            if t == "BTCUSDT":
                self.btc = s
            self.st[s] = SymState(s)
            self.consolidate(s, timedelta(minutes=5), self._on5m)
            self.consolidate(s, timedelta(minutes=15), self._on15m)
            self.consolidate(s, timedelta(hours=1), self._on1h)
            self.consolidate(s, timedelta(hours=4), self._on4h)
        self.set_warm_up(timedelta(days=35))

    # ---------- helpers ----------
    def _v(self, why):
        self.vt[why] = self.vt.get(why, 0) + 1
        return False

    def _ae(self):
        return max(5.0, float(self.portfolio.total_portfolio_value))

    def _rpx(self, sym, px):
        sp = self.securities[sym].symbol_properties
        step = float(sp.minimum_price_variation) if (sp.minimum_price_variation and sp.minimum_price_variation > 0) else 1e-6
        return round(round(float(px) / step) * step, 8)

    def _rq(self, sym, q, px):
        sp = self.securities[sym].symbol_properties
        lot = float(sp.lot_size) if (sp.lot_size and sp.lot_size > 0) else 0.001
        q = math.floor(abs(float(q)) / lot) * lot
        mn = max(5.5, float(sp.minimum_order_size or 5.0))
        return round(q, 6) if (q >= lot and q * px >= mn) else 0.0

    def _rpct(self, ap):
        ae = self._ae()
        self.pk = max(self.pk, ae)
        dd = max(0.0, (self.pk - ae) / self.pk)
        bs = (0.048 if ap else 0.035) if self.mode == "TURBO" else (0.040 if ap else 0.028)
        return bs * (1.0 if dd < 0.12 else max(0.25, (1.0 - dd) ** 2.6))

    def _regime(self):
        if self._rt == self.time:
            return self._rv
        act = bull = bear = 0
        for x in self.st.values():
            if x.b4 < 10 or x.mem.e50 <= 0:
                continue
            px = float(self.securities[x.sym].price or 0.0)
            if px <= 0:
                continue
            act += 1
            if px > x.mem.e50 and x.mem.e20 >= x.mem.e50 * 0.995:
                bull += 1
            elif px < x.mem.e50 and x.mem.e20 <= x.mem.e50 * 1.005:
                bear += 1
        if act == 0:
            v = ("MIXED", 0.5, 0.5)
        else:
            b, r = bull / act, bear / act
            v = ("BULL_RALLY" if b >= 0.55 else ("BEAR_CASCADE" if r >= 0.60 else "MIXED"), b, r)
        self._rt, self._rv = self.time, v
        return v

    def _allowed(self, s, sd, c):
        reg = self._regime()[0]
        if sd == -1:
            if not self.shorts or reg == "BULL_RALLY":
                return False
            if s.mem.e50 > 0 and c > s.mem.e50:
                return False
            if self.btc is not None:
                bt = self.st[self.btc]
                if bt.sd4 == 1 and bt.ker4 > 0.45:
                    return False
        elif reg == "BEAR_CASCADE" and s.mem.e50 > 0 and c < s.mem.e50 and s.sd4 == -1:
            return False
        return True

    def _can(self, s, sd=0):
        if self.portfolio[s.sym].invested or s.pend:
            return False
        n = ns = 0
        for x in self.st.values():
            if x.pend or (self.portfolio[x.sym].invested and x.ph == 0):
                n += 1
                if sd != 0 and x.sd == sd:
                    ns += 1
        return n < self.maxp and ns < 4

    def _orisk(self):
        t = 0.0
        for x in self.st.values():
            if x.sd != 0 and x.ph == 0 and x.rd > 0:
                t += x.qty * x.rd
        return t / self._ae()

    def _target(self, s, sd, en, rd, min_r):
        m = s.mem
        if sd == 1:
            w = sorted([(p, n) for p, n in ((s.pwh, "PWH"), (s.pdh, "PDH"), (m.hi(30), "H30")) if en + 0.5 * rd < p < 1e17])
        else:
            w = sorted([(p, n) for p, n in ((s.pwl, "PWL"), (s.pdl, "PDL"), (m.lo(30), "L30")) if 0 < p < en - 0.5 * rd], reverse=True)
        if not w:
            return 0.0, 0.0, "OPEN"
        p, n = w[0]
        r = abs(p - en) / rd
        if r < min_r:
            return None, 0.0, n
        r = min(r, 25.0)
        return en + sd * r * rd, r, n

    def _score(self, s, sd, c, cf, tg):
        reg, b, r = self._regime()
        m = s.mem
        co = 1.0 if m.coiled(c, sd) else 0.3
        al = 1.0 if ((sd == 1 and c > m.e20 >= m.e50) or (sd == -1 and c < m.e20 <= m.e50)) else 0.3
        aw = 0.15 if tg[:4] in ("ARM1", "ARM2") else 0.05
        return min(1.0, 0.30 * (b if sd == 1 else r) + 0.25 * co + 0.25 * al + 0.20 * cf + aw)

    def _gate(self, s, c):
        reg = self._regime()[0]
        m, sd = s.mem, s.sd
        if sd == 1 and reg == "BULL_RALLY" and c > m.e20 >= m.e50:
            return True
        if sd == -1 and reg == "BEAR_CASCADE" and c < m.e20 <= m.e50:
            return True
        inf = 0.18 * min(3, s.if_bos) + 0.15 * min(3, s.if_fvg) + 0.12 * min(2, s.if_vol)
        if m.coiled(c, sd):
            inf += 0.25
        return 0.45 * s.score + 0.55 * inf >= 0.62

    # ---------- entry ----------
    def _sub(self, s, sd, en0, sl, tg, cf):
        if s.sym in self.cd and self.time < self.cd[s.sym]:
            return self._v("COOLDOWN")
        if not self._can(s, sd):
            return self._v("SLOTS_FULL")
        tx = float(self.securities[s.sym].price or en0)
        if tx <= 0 or not self._allowed(s, sd, tx):
            return self._v("COUNTER_REGIME")
        need = s.sw4.cnl if sd == 1 else s.sw4.cnh
        if need <= s.mk[sd]:
            return self._v("SAME_WAVE")
        fm = float(self.portfolio.margin_remaining)
        if fm < 2.0:
            return self._v("NO_MARGIN")
        en, sl = self._rpx(s.sym, tx), self._rpx(s.sym, sl)
        rd = sd * (en - sl)
        if rd <= 0:
            return self._v("BAD_STOP")
        a1, a4 = s.sw1.atr(), s.sw4.atr()
        if rd < a1:
            return self._v("STOP_INSIDE_NOISE")
        if rd > 4.0 * a4:
            return self._v("STOP_TOO_WIDE")
        min_r = 3.0 + 4.0 * FEE * en / rd
        tp, tpr, wall = self._target(s, sd, en, rd, min_r)
        if tp is None:
            return self._v("WALL_UNDER_3R_NET")
        ae = self._ae()
        dd = max(0.0, (self.pk - ae) / self.pk)
        eb = ae if dd < 0.14 else max(ae * 0.50, min(self.wse, ae))
        ap = cf >= 0.78
        sc = self._score(s, sd, en, cf, tg)
        rk = eb * self._rpct(ap) * (0.85 + 0.35 * max(0.0, min(1.0, 0.5 * cf + 0.5 * sc)))
        room = self.rbudget - self._orisk()
        if room <= 0.002:
            return self._v("RISK_BUDGET")
        rk = min(rk, room * ae)
        lev = 3.2 if (ap and dd < 0.10) else (2.4 if ap else 1.8)
        notional = min(rk / (rd / en + 0.0012), eb * lev, fm * 5.8)
        if notional < 5.5:
            return self._v("NOTIONAL_TOO_SMALL")
        q = self._rq(s.sym, notional / en, en)
        if q <= 0:
            return self._v("LOT_SIZE")
        reg, b, r = self._regime()
        s.eng, s.sd, s.sl, s.en, s.rd = tg, sd, sl, en, rd
        s.tp, s.tpr, s.wall, s.min_r, s.a1 = tp, tpr, wall, min_r, a1
        s.qty, s.mfe, s.peak, s.ph, s.closing = q, 0.0, en, 0, False
        s.score, s.if_bos, s.if_fvg, s.if_vol = sc, 0, 0, 0
        s.story = "%s br=%.2f cf=%.2f sc=%.2f" % (reg, b if sd == 1 else r, cf, sc)
        s.pend, s.eb = True, s.b5
        s.mk[sd] = need
        tk = self.market_order(s.sym, q if sd == 1 else -q, tag="EN_" + tg)
        if tk is None or tk.status == OrderStatus.INVALID:
            self._rst(s)
            self.cd[s.sym] = self.time + timedelta(hours=1)
            return False
        if tk.status not in (OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.INVALID):
            s.entk = tk
        return True

    # ---------- orders ----------
    def _live(self, tk):
        return tk is not None and tk.status not in (OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.INVALID)

    def _sync_sl(self, s):
        h = self.portfolio[s.sym]
        if not h.invested or s.sd == 0 or s.closing:
            return
        q = abs(float(h.quantity))
        px = float(self.securities[s.sym].price or s.en)
        slp = self._rpx(s.sym, s.sl)
        if s.sd * (px - slp) <= 0:
            self._exit(s, "SL_CROSSED")
            return
        if self._live(s.sltk):
            try:
                r = s.sltk.update_stop_price(slp)
                if r.is_success:
                    return
            except Exception:
                pass
            s.sltk.cancel()
        s.sltk = self.stop_market_order(s.sym, -q if s.sd == 1 else q, slp, tag="SL_" + s.eng)

    def _raise(self, s, nsl, c):
        if s.closing or s.sd == 0:
            return
        nsl = self._rpx(s.sym, nsl)
        if s.sd * (nsl - s.sl) <= 0:
            return
        if s.sd * (c - nsl) <= 0:
            self._exit(s, "STOP_CROSSED")
            return
        s.sl = nsl
        self._sync_sl(s)

    def _exit(self, s, why):
        if s.closing:
            return
        s.closing, s.cb = True, s.b5
        if self._live(s.sltk):
            s.sltk.cancel()
        s.sltk = None
        self.liquidate(s.sym, tag="X_" + why)

    def _rst(self, s):
        if self._live(s.sltk):
            s.sltk.cancel()
        s.sltk, s.entk = None, None
        s.eng, s.wall, s.story, s.sd, s.ph = "", "", "", 0, 0
        s.en = s.sl = s.tp = s.tpr = s.min_r = s.rd = s.qty = s.mfe = s.peak = s.score = 0.0
        s.pend = s.closing = False
        s.if_bos = s.if_fvg = s.if_vol = 0

    def _fin(self, s, px, tag):
        if s.sd == 0:
            return
        r = s.sd * (px - s.en) / s.rd if s.rd > 0 else 0.0
        net = r - (FEE * s.en / s.rd if s.rd > 0 else 0.0)
        st = self.stats.setdefault(s.eng, [0, 0.0, 0])
        st[0] += 1
        st[1] += net
        st[2] += 1 if net > 0 else 0
        self.log("EXIT %s %s %s Rnet=%.2f mfe=%.2f ph=%d t=%s" % (
            s.sym.value, s.eng, tag, net, s.mfe, s.ph, self.time.strftime("%m-%d %H:%M")))
        if net < 0:
            self.cd[s.sym] = self.time + timedelta(hours=4)
        self._rst(s)

    # ---------- management ----------
    def _lock(self, s, c, ph):
        s.ph = ph
        self._raise(s, s.en + s.sd * (s.min_r + 0.02) * s.rd, c)

    def _m5(self, s, h, l, c):
        sd = s.sd
        if sd == 0 or s.rd <= 0:
            return
        if s.closing:
            if s.b5 - s.cb > 3:
                s.cb = s.b5
                self.liquidate(s.sym, tag="X_RETRY")
            return
        ext = h if sd == 1 else l
        s.peak = max(s.peak, h) if sd == 1 else min(s.peak, l)
        s.mfe = max(s.mfe, sd * (ext - s.en) / s.rd)
        if not self._live(s.sltk):
            self._sync_sl(s)
            if s.closing:
                return
        if s.ph < 2 and s.tp > 0 and sd * (ext - s.tp) >= 0:
            if self._gate(s, c):
                self._lock(s, c, 2)
            else:
                self._exit(s, "TARGET_%.1fR_%s" % (s.tpr, s.wall))
            return
        if s.ph == 0 and sd * (ext - (s.en + sd * (s.min_r * s.rd + s.a1))) >= 0:
            self._lock(s, c, 2 if self._gate(s, c) else 1)

    def _trail(self, s, c, is4):
        if s.ph == 0 or s.closing or s.sd == 0 or s.rd <= 0:
            return
        if is4 and s.ph == 1 and self._gate(s, c):
            s.ph = 2
        if s.ph == 2 and is4:
            m = max(12, min(84, (s.b4 - s.e4) // 3))
            seg, pad = list(s.q4)[-m:], 1.5 * s.sw4.atr()
        elif s.ph == 1 and not is4:
            seg, pad = list(s.q1)[-8:], 0.5 * s.sw1.atr()
        else:
            return
        lvl = (min(x.low for x in seg) - pad) if s.sd == 1 else (max(x.high for x in seg) + pad)
        self._raise(s, lvl, c)

    # ---------- bars ----------
    def _on4h(self, bar):
        s = self.st[bar.symbol]
        s.b4 += 1
        s.q4.append(bar)
        s.v4.append(float(bar.volume))
        h, l, c, o = float(bar.high), float(bar.low), float(bar.close), float(bar.open)
        s.mem.on4h(c)
        s.sw4.update(h, l, c)
        s.ker4 = s.sw4.ker(10)
        if len(s.q4) < 16:
            return
        atr = s.sw4.atr()
        psh, psl = s.sh4, s.sl4
        if s.sh4 == 0.0:
            s.sh4, s.sl4 = max(x.high for x in s.q4), min(x.low for x in s.q4)
        if s.sw4.ah:
            s.sh4 = s.sw4.ah[-1][1]
        if s.sw4.al:
            s.sl4 = s.sw4.al[-1][1]
        fb = 0
        if psh > 0 and c > psh:
            s.sd4, s.sh4, fb = 1, h, 1
        elif psl > 0 and c < psl:
            s.sd4, s.sl4, fb = -1, l, -1
        rv = float(bar.volume) / max(sum(s.v4) / len(s.v4), 1e-8)
        if self.portfolio[bar.symbol].invested:
            if fb == s.sd:
                s.if_bos += 1
            if rv >= 1.25 and ((s.sd == 1 and c > o) or (s.sd == -1 and c < o)):
                s.if_vol += 1
            if not self.is_warming_up:
                self._trail(s, c, True)
            return
        if self.is_warming_up:
            return
        if fb != 0 and ((fb == 1 and c > o) or (fb == -1 and c < o)) and self._allowed(s, fb, c):
            n5 = list(s.q4)[-5:]
            sl = (min(x.low for x in n5) - 0.45 * atr) if fb == 1 else (max(x.high for x in n5) + 0.45 * atr)
            cf = min(0.95, 0.62 + (0.15 if s.ker4 > 0.36 else 0.0) + (0.12 if rv > 1.10 else 0.0))
            s.g4 = (fb, sl, cf, s.b4)

    def _on1h(self, bar):
        s = self.st[bar.symbol]
        s.b1 += 1
        s.q1.append(bar)
        s.v1.append(float(bar.volume))
        h, l, c, o = float(bar.high), float(bar.low), float(bar.close), float(bar.open)
        s.mem.on1h(c)
        s.sw1.update(h, l, c)
        if len(s.q1) < 16:
            return
        a1 = s.sw1.atr()
        psh, psl = s.sh1, s.sl1
        if s.sw1.ah:
            s.sh1 = s.sw1.ah[-1][1]
        if s.sw1.al:
            s.sl1 = s.sw1.al[-1][1]
        fb = 0
        if psh > 0 and c > psh:
            s.sd1, fb = 1, 1
        elif psl > 0 and c < psl:
            s.sd1, fb = -1, -1
        if self.portfolio[bar.symbol].invested:
            if fb == s.sd:
                s.if_bos += 1
            if not self.is_warming_up:
                self._trail(s, c, False)
            return
        if s.sd4 == 1 and l <= max(s.mem.h20 * 1.008, s.sl1 * 1.015):
            s.armed = True
        elif s.sd4 == -1 and h >= min(s.mem.h20 * 0.992, s.sh1 * 0.985 if s.sh1 > 0 else 1e18):
            s.armed = True
        if self.is_warming_up:
            return
        pb = s.q1[-2]
        sd = s.sd4
        if (s.armed or fb != 0) and sd != 0 and self._allowed(s, sd, c):
            up = sd == 1 and c > o and c > float(pb.high) and c > s.mem.h20
            dn = sd == -1 and c < o and c < float(pb.low) and c < s.mem.h20
            if up or dn:
                s.armed = False
                q8 = list(s.q1)[-8:]
                sl = (min(x.low for x in q8) - 0.55 * a1) if sd == 1 else (max(x.high for x in q8) + 0.55 * a1)
                s.g1 = (sd, sl, min(0.94, 0.68 + 0.20 * s.sw1.ker(10)), s.b1)

    def _on15m(self, bar):
        s = self.st[bar.symbol]
        s.b15 += 1
        s.q15.append(bar)
        s.v15.append(float(bar.volume))
        h, l, c, o = float(bar.high), float(bar.low), float(bar.close), float(bar.open)
        s.sw15.update(h, l, c)
        if len(s.q15) < 8:
            return
        a15 = s.sw15.atr()
        a1 = max(s.sw1.atr(), a15 * 1.8)
        rv = float(bar.volume) / max(sum(s.v15) / len(s.v15), 1e-8)
        b0, b2 = s.q15[-1], s.q15[-3]
        fu = b0.low > b2.high and (b0.low - b2.high) > 0.15 * a15
        fd = b0.high < b2.low and (b2.low - b0.high) > 0.15 * a15
        if self.portfolio[bar.symbol].invested:
            if (s.sd == 1 and fu) or (s.sd == -1 and fd):
                s.if_fvg += 1
            return
        if self.is_warming_up:
            return
        k = s.sw15.ker(8)
        for lvl, sd in ((s.pdl, 1), (s.pwl, 1), (s.sl1, 1), (s.pdh, -1), (s.pwh, -1), (s.sh1, -1)):
            if lvl <= 0 or lvl >= 1e17:
                continue
            if self._allowed(s, sd, c):
                sc = s.sw15.swp_rec(o, h, l, c, lvl, sd, a15)
                if sc > 0.48:
                    qb = list(s.q1)[-6:] if len(s.q1) >= 6 else list(s.q15)[-12:]
                    sl = (min(l, min(x.low for x in qb)) - 0.5 * a1) if sd == 1 else (max(h, max(x.high for x in qb)) + 0.5 * a1)
                    s.gs = (sd, sl, min(0.94, 0.62 + 0.30 * sc), s.b15)
                    break
            bd = -sd
            if k > 0.48 and rv > 1.25 and self._allowed(s, bd, c):
                qb = list(s.q1)[-5:] if len(s.q1) >= 5 else list(s.q15)[-10:]
                if bd == 1 and o <= lvl and c > lvl + 0.2 * a15 and (c - o) > 0.5 * (h - l):
                    s.gi = (1, min(l, min(x.low for x in qb)) - 0.45 * a1, min(0.95, 0.68 + 0.22 * k), s.b15)
                    break
                if bd == -1 and o >= lvl and c < lvl - 0.2 * a15 and (o - c) > 0.5 * (h - l):
                    s.gi = (-1, max(h, max(x.high for x in qb)) + 0.45 * a1, min(0.95, 0.68 + 0.22 * k), s.b15)
                    break

    def _on5m(self, bar):
        s = self.st[bar.symbol]
        s.b5 += 1
        h, l, c, o = float(bar.high), float(bar.low), float(bar.close), float(bar.open)
        s.mem.on5(h, l)
        dt = bar.end_time
        if dt.day != s.cday:
            if s.cday != -1:
                s.pdh, s.pdl = s.dh, s.dl
                s.mem.push(s.dh, s.dl)
            s.cday, s.dh, s.dl = dt.day, h, l
        else:
            s.dh, s.dl = max(s.dh, h), min(s.dl, l)
        wk = dt.isocalendar()[1]
        if wk != s.cwk:
            if s.cwk != -1:
                s.pwh, s.pwl = s.wh, s.wl
            s.cwk, s.wh, s.wl = wk, h, l
        else:
            s.wh, s.wl = max(s.wh, h), min(s.wl, l)
        if self.is_warming_up:
            return
        if s.p0 == 0.0:
            s.p0 = c
        inv = self.portfolio[bar.symbol].invested
        if s.pend and s.b5 - s.eb > 6:
            if self._live(s.entk):
                s.entk.cancel()
            s.pend, s.entk = False, None
            if not inv:
                self._rst(s)
        if inv:
            self._m5(s, h, l, c)
            return
        if s.sd != 0 and not s.pend:
            self._fin(s, c, "SYNC")
        if not self._can(s):
            return
        for at, tg, cn, mx in (("g4", "ARM1_4H", "b4", 1), ("g1", "ARM2_1H", "b1", 1),
                               ("gi", "ARM3_IGN", "b15", 2), ("gs", "ARM4_SWP", "b15", 2)):
            sg = getattr(s, at)
            if sg is None:
                continue
            setattr(s, at, None)
            sd, sl, cf, bid = sg
            if getattr(s, cn) - bid > mx:
                continue
            if at == "gs" and not ((sd == 1 and c > o) or (sd == -1 and c < o)):
                self._v("SWP_NO_CONFIRM")
                continue
            if self._sub(s, sd, c, sl, tg, cf):
                return

    def on_data(self, data):
        if self.is_warming_up:
            return
        wk = self.time.isocalendar()[1]
        if wk != self.lwk:
            ae = self._ae()
            if self.lwk != -1:
                self.mode = "TURBO" if (ae - self.wse) / max(self.wse, 1.0) >= 0.04 else "DAILY"
            self.wse, self.lwk = ae, wk

    def on_order_event(self, oe):
        s = self.st.get(oe.symbol)
        if s is None:
            return
        od = self.transactions.get_order_by_id(oe.order_id)
        tag = od.tag if (od is not None and od.tag) else ""
        inv = self.portfolio[s.sym].invested
        if oe.status == OrderStatus.INVALID:
            if self.nbad < 20:
                self.nbad += 1
                self.log("INVALID %s %s %s" % (s.sym.value, tag, oe.message))
            if tag.startswith("EN_"):
                self.cd[s.sym] = self.time + timedelta(hours=1)
                if not inv:
                    self._rst(s)
            elif tag.startswith("SL_") and inv:
                s.sltk = None
                self._exit(s, "SL_INVALID")
            return
        if oe.status == OrderStatus.CANCELED:
            if tag.startswith("EN_") and not inv:
                self._rst(s)
            return
        if oe.status != OrderStatus.FILLED:
            return
        if tag.startswith("EN_") and s.pend:
            s.pend, s.entk = False, None
            s.en = float(oe.fill_price)
            s.qty = abs(float(self.portfolio[s.sym].quantity))
            s.sd = 1 if oe.fill_quantity > 0 else -1
            s.rd = abs(s.en - s.sl)
            if s.rd <= 0 or s.qty <= 0:
                self._exit(s, "BAD_FILL")
                return
            s.min_r = 3.0 + 4.0 * FEE * s.en / s.rd
            s.peak, s.e4 = s.en, s.b4
            self._sync_sl(s)
            self.log("ENTER %s %s %s px=%.6g stop=%.2f%% tp=%.1fR(%s) minR=%.2f %s" % (
                s.sym.value, "LONG" if s.sd == 1 else "SHORT", s.eng, s.en,
                100.0 * s.rd / s.en, s.tpr, s.wall, s.min_r, s.story))
            return
        if (tag.startswith("SL_") or tag.startswith("X_")) and not inv:
            self._fin(s, float(oe.fill_price), tag)

    def on_end_of_algorithm(self):
        self.log("VETOES " + " ".join("%s=%d" % kv for kv in sorted(self.vt.items())))
        for k, v in sorted(self.stats.items()):
            self.log("ENG %s n=%d avgRnet=%.2f win=%.0f%%" % (k, v[0], v[1] / max(1, v[0]), 100.0 * v[2] / max(1, v[0])))
        bh = []
        for s in self.st.values():
            h = self.portfolio[s.sym]
            if h.invested:
                self.log("OPEN %s qty=%.4f avg=%.6g unreal=%.2f" % (s.sym.value, float(h.quantity), float(h.average_price), float(h.unrealized_profit)))
            px = float(self.securities[s.sym].price or 0.0)
            if s.p0 > 0 and px > 0:
                bh.append(px / s.p0 - 1.0)
        if bh:
            self.log("BH_EW %.0f%% coins=%d" % (100.0 * sum(bh) / len(bh), len(bh)))
        try:
            self.log("REALIZED=%.2f FEES=%.2f EQUITY=%.2f" % (
                float(self.portfolio.total_profit), float(self.portfolio.total_fees), float(self.portfolio.total_portfolio_value)))
        except Exception:
            self.log("EQUITY=%.2f" % float(self.portfolio.total_portfolio_value))
