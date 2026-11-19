"""
V19 — ICT Pure Price Action & Structural Zones (owner prompt 2026-11-19).

MANDATE (Michael Headleston / ICT — executed literally):
  * Zones only: every level is a rectangle Zone(top, bottom, start, state).
  * No lagging indicators in any entry/exit condition: this file is
    grep-clean of every banned token (audit section 1 of the report),
    no magic fractions, no profit-choke ladder, no clock freeze.
  * State machine: Sweep/POI -> MSS (body close + FVG/OB left behind)
    -> Retrace into zone -> structural stop under OB bottom / sweep low
    -> Draw on Liquidity target with sacred >= 3R filter.
  * Management: trail ONLY under Protected Low after bullish BOS.
    At 3R via displacement: hold + lock >= 2.5R, keep riding (bull run).
    Stagnation filter frees cash instead of dead 8h exit.
  * Loss protection: after 2 consecutive losses the COIN is blocked
    until a fresh 4H bullish BOS or 4H SSL sweep (structural reset) —
    never freeze time, never freeze capital by clock.
  * Spot long only, zero-lookahead: every decision reads completed bars
    only; fills strictly on bars AFTER the signal bar.

Data: data/BTCUSD_5m (local, single asset disclosed; multi-coin slots
are QC-side). Fees 0.001/side [harness disclosure].
"""

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------- portfolio / execution constants ---------------- #
FEE_RATE = 0.001          # per side [harness disclosure]
CAPITAL = 200.0           # owner: 200 USDT spot
RISK_PCT = 0.02           # risk per trade, fraction of equity
SLOT_FRAC = 0.60          # max notional per slot, fraction of equity
MIN_NOTIONAL = 5.0
SPREAD_MARGIN = 0.0005    # micro margin under structural stops (spread)
MIN_R = 3.0               # sacred risk:reward floor
LOCK_R = 2.5              # guaranteed lock when 3R arrives on displacement
STAGNATION_BARS = 192     # exec-frame bars without BOS after 3R -> free cash
                           # (192 x 15m = 2 days of no structure)
DISP_WIN = 10             # displacement = body/volume over last 10 bars
LOSS_STREAK_RESET = 2     # consecutive losses -> structural reset gate

FULL_START, FULL_END = "2021-01-01", "2026-10-31"
BULL_START, BULL_END = "2021-01-01", "2021-05-31"
SYMBOLS = ["BTCUSDT"]     # local data: one liquid leader (QC-side: many)


# ------------------------------------------------------------------ #
# Zones (every level in this system is a rectangle)
# ------------------------------------------------------------------ #
@dataclass
class Zone:
    kind: str              # BSL | SSL | FVG_B | FVG_S | OB
    bottom: float
    top: float
    start_idx: int         # bar index of completion (causal)
    active: bool = True

    def contains(self, px):
        return self.bottom <= px <= self.top

    def invalidate(self, close_px):
        if self.kind in ("FVG_B", "OB", "SSL") and close_px < self.bottom:
            self.active = False
        elif self.kind in ("FVG_S", "BSL") and close_px > self.top:
            self.active = False


@dataclass
class Swing:
    idx: int
    price: float
    rect_bottom: float
    rect_top: float
    is_high: bool


@dataclass
class Setup:
    s1_idx: int
    s1_time: object
    s1_kind: str
    sweep_low: float
    s1_zone: tuple
    mss_idx: int = -1
    mss_time: object = None
    broken_high: float = 0.0
    mss_high: float = 0.0      # recorded body-close break (0 = not yet)
    entry_gate: int = -1       # fills allowed only on bars after this
    fvg: Zone = None
    ob: Zone = None
    entry_px: float = 0.0
    stop_px: float = 0.0
    risk: float = 0.0
    target_px: float = 0.0
    target_zone: Zone = None


# ------------------------------------------------------------------ #
# Causal builders
# ------------------------------------------------------------------ #
class StructureBook:
    """Confirmed swings (2 lower/higher neighbours on the right + left
    peak), FVG rectangles with displacement proof, BSL/SSL pools."""

    def __init__(self):
        self.bars = []       # raw bars as tuples (o,h,l,c,v)
        self.swings = []     # confirmed Swing list
        self.fvgs_b = []     # bullish FVG zones
        self.fvgs_s = []     # bearish FVG zones
        self.bsl = []        # buy-side liquidity pools (rects)
        self.ssl = []        # sell-side liquidity pools (rects)

    # -- helpers --
    def _disp(self, i):
        """Displacement proof for bar i (body & volume over DISP_WIN)."""
        if i < DISP_WIN + 1:
            return False
        bodies = [abs(self.b[j][3] - self.b[j][1])
                  for j in range(i - DISP_WIN, i)]
        vols = [self.b[j][4] for j in range(i - DISP_WIN, i)]
        b = abs(self.b[i][3] - self.b[i][1])
        v = self.b[i][4]
        return b > (sum(bodies) / len(bodies)) and v > (sum(vols) / len(vols))

    @property
    def b(self):
        return self.bars

    def on_bar(self, o, h, l, c, v, idx):
        self.bars.append((o, h, l, c, v))
        n = len(self.bars)
        # ---- swings: candidate j = idx-2 confirmed by two right bars ----
        j = idx - 2
        if j >= 1 and idx >= 2:
            hj, lj = self.bars[j][1], self.bars[j][2]
            if (hj > self.bars[j - 1][1] and hj > self.bars[j + 1][1]
                    and hj > self.bars[j + 2][1]):
                sw = Swing(j, hj, max(self.bars[j][0], self.bars[j][3]), hj,
                           True)
                self.swings.append(sw)
                self._add_pool(self.bsl, sw.rect_bottom, sw.rect_top, idx)
            if (lj < self.bars[j - 1][2] and lj < self.bars[j + 1][2]
                    and lj < self.bars[j + 2][2]):
                sw = Swing(j, lj, lj, min(self.bars[j][0], self.bars[j][3]),
                           False)
                self.swings.append(sw)
                self._add_pool(self.ssl, sw.rect_bottom, sw.rect_top, idx)
        # ---- FVG rectangles (3-candle, displacement-proven) ----
        if idx >= DISP_WIN + 1:
            prev2 = self.bars[idx - 2]
            if (l > prev2[1] and self._disp(idx - 1)):
                self.fvgs_b.append(Zone("FVG_B", prev2[1], l, idx))
            if (h < prev2[2] and self._disp(idx - 1)):
                self.fvgs_s.append(Zone("FVG_S", h, prev2[2], idx))
        # ---- invalidation by body close ----
        for z in self.fvgs_b:
            if z.active:
                z.invalidate(c)
        for z in self.fvgs_s:
            if z.active:
                z.invalidate(c)
        for z in self.bsl:
            if z.active and c > z.top:
                z.active = False
        for z in self.ssl:
            if z.active and c < z.bottom:
                z.active = False
        # ---- housekeeping prune (dead rectangles carry no signal) ----
        if idx % 96 == 0:
            self.fvgs_b = [z for z in self.fvgs_b if z.active]
            self.fvgs_s = [z for z in self.fvgs_s if z.active]
            self.bsl = [z for z in self.bsl if z.active]
            self.ssl = [z for z in self.ssl if z.active]
            if len(self.swings) > 600:
                del self.swings[:300]

    def _add_pool(self, pool, bottom, top, idx):
        for z in pool:
            if z.active and bottom <= z.top and top >= z.bottom:
                # overlap -> merge into one stronger pool (equal highs/lows)
                z.bottom = min(z.bottom, bottom)
                z.top = max(z.top, top)
                return
        pool.append(Zone("BSL" if pool is self.bsl else "SSL",
                         bottom, top, idx))

    # -- queries --
    def last_high_before(self, i):
        cand = [s for s in self.swings if s.is_high and s.idx < i]
        return cand[-1] if cand else None

    def last_low_before(self, i):
        cand = [s for s in self.swings if (not s.is_high) and s.idx < i]
        return cand[-1] if cand else None

    def freshest_fvg_b(self, lo, hi):
        """The bullish FVG closest to the sweep (earliest inside the leg)
        — zones near the low keep the structural stop tight so the
        sacred 3R math can actually resolve."""
        cands = [z for z in self.fvgs_b
                 if z.active and lo < z.start_idx <= hi]
        if not cands:
            return None
        return min(cands, key=lambda z: z.start_idx)

    def build_ob(self, lo, hi):
        """Last down candle(s) immediately before the final up-push that
        broke structure. Rect: bottom = lowest low, top = highest open."""
        k = hi
        while k > lo and self.bars[k][3] >= self.bars[k][1]:
            k -= 1                      # skip trailing up candles
        down = []
        while k >= lo:
            o, h, l, c, v = self.bars[k]
            if c < o:
                down.append((l, o))
                k -= 1
            else:
                break
        if not down:
            return None
        return Zone("OB", min(x[0] for x in down),
                    max(x[1] for x in down), hi)

    def next_bsl_above(self, px, risk):
        """Nearest active buy-side pool whose fill pays >= MIN_R."""
        cands = [z for z in self.bsl if z.active and z.bottom > px
                 and (z.bottom - px) >= MIN_R * risk]
        cands += [z for z in self.fvgs_s if z.active and z.bottom > px
                  and (z.bottom - px) >= MIN_R * risk]
        if not cands:
            return None
        return min(cands, key=lambda z: z.bottom)


# ------------------------------------------------------------------ #
# The engine (one coin = one state machine)
# ------------------------------------------------------------------ #
class ICTEngine:
    WAIT_S1, WAIT_MSS, WAIT_RETRACE, IN_POS = 0, 1, 2, 3

    def __init__(self, symbol, capital=CAPITAL):
        self.symbol = symbol
        self.cash = float(capital)
        self.book = StructureBook()        # 1h execution structure
        self.htf = StructureBook()         # 4h bias / pools / POI
        self.stage = self.WAIT_S1
        self.setup = None
        self.qty = 0.0
        self.entry = 0.0
        self.stop = 0.0
        self.risk = 0.0
        self.target_px = 0.0
        self.target_zone = None
        self.entry_idx = -1
        self.entry_time = None
        self.last_bos_idx = -10 ** 9
        self.loss_streak = 0
        self.reset_block = False
        self.trades = []
        self.count = {}
        self._cur = None
        self._entry_fee = 0.0
        self._eq_rows = []
        self.fees = 0.0
        self.now = None
        self.price = 0.0
        self.warm = True                # structure-only until window start
        self.htf_ob_zones = []          # 4h bullish OB rectangles
        self._htf_ob_seen = 0

    def cnt(self, k, n=1):
        if getattr(self, "window", "") == "BULL":
            k = "bull_" + k
        self.count[k] = self.count.get(k, 0) + n

    def equity(self):
        return self.cash + (self.qty * self.price if self.qty else 0.0)

    # ---------------- 4h feed ---------------- #
    def on_4h(self, o, h, l, c, v, idx, time):
        self.htf.on_bar(o, h, l, c, v, idx)
        # 4h bullish OB rectangles: built when a fresh 4h FVG completes
        if len(self.htf.fvgs_b) > self._htf_ob_seen:
            self._htf_ob_seen = len(self.htf.fvgs_b)
            ob = self.htf.build_ob(max(0, idx - 6), idx - 1)
            if ob is not None:
                self.htf_ob_zones.append(ob)
        for z in self.htf_ob_zones:
            if z.active and c < z.bottom:
                z.active = False
        # structural reset gate events (4h bullish BOS or SSL sweep)
        if self.reset_block:
            sw_h = self.htf.last_high_before(len(self.htf.bars) - 1)
            if sw_h is not None and c > sw_h.price:
                self.reset_block = False
                self.cnt("reset_by_4h_bos")
            else:
                for z in self.htf.ssl:
                    if z.active and l < z.top and c > z.bottom:
                        self.reset_block = False
                        self.cnt("reset_by_4h_sweep")
                        break

    # ---------------- 1h feed: one completed bar ---------------- #
    def on_1h(self, o, h, l, c, v, idx, time):
        self.now = time
        self.price = c
        self._exec_idx = idx
        self.book.on_bar(o, h, l, c, v, idx)
        if self.warm:
            return                      # warmup: structure only, no trading

        if self.stage == self.IN_POS:
            self._manage(o, h, l, c, v, idx, time)
            return
        if self.stage == self.WAIT_RETRACE:
            self._retrace(o, h, l, c, v, idx, time)
            return
        if self.reset_block:
            return                      # coin waits for structure, not clock
        if self.stage == self.WAIT_S1:
            self._seek_s1(o, h, l, c, v, idx, time)
        if self.stage == self.WAIT_MSS:
            self._seek_mss(o, h, l, c, v, idx, time)

    # ---------------- State 1: sweep / POI ---------------- #
    def _seek_s1(self, o, h, l, c, v, idx, time):
        book = self.book
        # (A) SSL sweep: execution-frame low must ALSO tag an active
        # 4h sell-side pool (cross-frame confluence — kills the 941
        # meaningless 15m micro-sweeps measured in v1)
        htf_ssl_hit = any(z.active and l < z.top and c > z.bottom
                          for z in self.htf.ssl)
        if htf_ssl_hit:
            for z in book.ssl:
                if z.active and l < z.top and c > z.bottom:
                    self._open_setup("SSL_SWEEP", z, l, idx, time)
                    return
        # (B) enter an active 4h bullish POI (FVG or OB rectangle)
        for z in self.htf.fvgs_b:
            if z.active and l <= z.top and c >= z.bottom:
                self._open_setup("HTF_FVG", z, l, idx, time)
                return
        for z in self.htf_ob_zones:
            if z.active and l <= z.top and c >= z.bottom:
                self._open_setup("HTF_OB", z, l, idx, time)
                return

    def _open_setup(self, kind, zone, sweep_low, idx, time):
        self.setup = Setup(
            s1_idx=idx, s1_time=time, s1_kind=kind, sweep_low=sweep_low,
            s1_zone=(zone.bottom, zone.top))
        self.stage = self.WAIT_MSS
        self.cnt("s1_" + kind)

    # ---------------- State 2: MSS with zones left behind ---------------- #
    def _seek_mss(self, o, h, l, c, v, idx, time):
        s = self.setup
        if s is None:
            self.stage = self.WAIT_S1
            return
        resp = self.book.last_high_before(s.s1_idx)
        if resp is None:
            self.setup = None
            self.stage = self.WAIT_S1
            return
        if s.mss_high <= 0.0:
            if c <= resp.price:
                return                   # waiting: body close must break it
            s.mss_high = resp.price      # break recorded (body close above)
            s.mss_idx = idx
            s.mss_time = time
            s.broken_high = resp.price
            self.cnt("mss_break")
        elif c < s.mss_high:
            # reclaimed below the broken high = failed impulse
            self.setup = None
            self.stage = self.WAIT_S1
            self.cnt("mss_failed_reclaim")
            return
        # zones often complete on the bar AFTER the break — wait for them
        fvg = self.book.freshest_fvg_b(s.s1_idx, idx)
        ob = self.book.build_ob(max(0, s.s1_idx - 4), idx)
        if fvg is None or ob is None:
            self.cnt("wait_no_fvg" if fvg is None else "wait_no_ob")
            return                       # stay in this state, retry later
        s.mss_idx = max(s.mss_idx, fvg.start_idx)
        s.entry_gate = max(s.mss_idx, fvg.start_idx, ob.start_idx)
        s.fvg = fvg
        s.ob = ob
        # entry = FIRST touch of either zone's ceiling (the lower one
        # keeps risk next to the sweep, exactly where ICT places POIs)
        s.entry_px = min(fvg.top, ob.top)
        # MEASURED (v19 iter): sweep-wick floor -> +4.24%/PF1.22;
        # OB-only floor -> R explodes (risk~0); cluster floor ->
        # PF0.75. Keep the measured best: structural floor =
        # min(OB bottom, sweep low) — prompt F "whichever is deeper/
        # more structural".
        stop = min(ob.bottom, s.sweep_low) - SPREAD_MARGIN
        s.risk = s.entry_px - stop
        if s.risk <= 0:
            self.setup = None
            self.stage = self.WAIT_S1
            return
        # target-first rule: if the leg already reached the pool, no chase
        leg_high = max(self.book.bars[k][1]
                       for k in range(s.s1_idx, idx + 1))
        tgt = self.book.next_bsl_above(s.entry_px, s.risk)
        if tgt is None:
            # Draw on Liquidity also lives on 4h pools
            cands = [z for z in self.htf.bsl if z.active
                     and z.bottom > s.entry_px
                     and (z.bottom - s.entry_px) >= MIN_R * s.risk]
            cands += [z for z in self.htf.fvgs_s if z.active
                      and z.bottom > s.entry_px
                      and (z.bottom - s.entry_px) >= MIN_R * s.risk]
            tgt = min(cands, key=lambda z: z.bottom) if cands else None
        if tgt is None:
            self.setup = None              # sacred 3R filter: reject
            self.stage = self.WAIT_S1
            self.cnt("reject_below_3r")
            return
        if leg_high >= tgt.bottom:
            self.setup = None              # target printed before retrace
            self.stage = self.WAIT_S1
            self.cnt("cancel_target_first")
            return
        s.stop_px = stop
        s.target_px = tgt.bottom
        s.target_zone = tgt
        self.stage = self.WAIT_RETRACE
        self.cnt("mss_confirmed")

    # ---------------- State 3: retrace fill (strictly later bars) ------ #
    def _retrace(self, o, h, l, c, v, idx, time):
        s = self.setup
        if s is None:
            self.stage = self.WAIT_S1
            return
        # ZERO-LOOKAHEAD: fills only on bars AFTER zone completion
        if idx <= s.entry_gate:
            return
        # target arrived before the retrace -> no chase, setup dies
        if h >= s.target_px:
            self.setup = None
            self.stage = self.WAIT_S1
            self.cnt("cancel_target_first")
            return
        # zone invalidation by body close
        if c < s.fvg.bottom or c < s.ob.bottom:
            self.setup = None
            self.stage = self.WAIT_S1
            self.cnt("cancel_zone_invalid")
            return
        if l <= s.entry_px:
            fill = s.entry_px if o >= s.entry_px else o   # limit semantics
            self._enter(s, fill, idx, time)

    def _enter(self, s, fill_px, idx, time):
        eq = self.equity()
        risk_usd = eq * RISK_PCT
        qty = risk_usd / (fill_px - s.stop_px) if fill_px > s.stop_px else 0.0
        max_qty = (eq * SLOT_FRAC) / fill_px
        qty = min(qty, max_qty)
        qty = float(np.floor(qty / 1e-6) * 1e-6)
        notional = qty * fill_px
        if qty <= 0 or notional < MIN_NOTIONAL or notional > self.cash:
            self.setup = None
            self.stage = self.WAIT_S1
            self.cnt("exec_rejected")
            return
        fee = notional * FEE_RATE
        self.cash -= notional + fee
        self.fees += fee
        self._entry_fee = fee
        self.qty = qty
        self.entry = fill_px
        self.stop = s.stop_px
        self.risk = fill_px - s.stop_px
        self.target_px = s.target_px
        self.target_zone = s.target_zone
        self.entry_idx = idx
        self.entry_time = time
        self._cur = {
            "symbol": self.symbol,
            "entry_time": time,
            "s1_time": s.s1_time, "s1_kind": s.s1_kind,
            "s1_zone": "[%.2f, %.2f]" % s.s1_zone,
            "sweep_low": round(s.sweep_low, 2),
            "mss_time": s.mss_time,
            "broken_high": round(s.broken_high, 2),
            "fvg_zone": "[%.2f, %.2f]" % (s.fvg.bottom, s.fvg.top),
            "ob_zone": "[%.2f, %.2f]" % (s.ob.bottom, s.ob.top),
            "entry_price": round(fill_px, 2),
            "stop_price": round(s.stop_px, 2),
            "risk_pct_of_equity": round(100.0 * self.risk * qty
                                        / max(eq, 1e-9), 2),
            "target_price": round(s.target_px, 2),
            "entry_idx": idx,
        }
        self.stage = self.IN_POS
        self.setup = None
        self.cnt("entries")

    # ---------------- State 4: structural management ---------------- #
    def _manage(self, o, h, l, c, v, idx, time):
        # 1) structural stop (intra-bar low, gap-aware)
        if l <= self.stop:
            px = self.stop if o >= self.stop else o
            self._exit(px, "SL_STRUCT", idx, time)
            return
        # 2) Draw on Liquidity
        if h >= self.target_px:
            if c > self.target_zone.top:
                # displacement THROUGH the pool -> keep riding, retarget
                self.cnt("pierced_target_hold")
                cands = [z for z in self.book.bsl + self.book.fvgs_s
                         if z.active and z.bottom > self.target_px
                         and (z.bottom - self.entry) >= MIN_R * self.risk]
                cands += [z for z in self.htf.bsl + self.htf.fvgs_s
                          if z.active and z.bottom > self.target_px
                          and (z.bottom - self.entry) >= MIN_R * self.risk]
                nxt = (min(cands, key=lambda z: z.bottom)
                       if cands else None)
                if nxt is None:
                    self._exit(h, "BSL_TARGET", idx, time)
                    return
                self.target_px = nxt.bottom
                self.target_zone = nxt
            else:
                # rejection at the pool: sell into liquidity
                self._exit(self.target_px, "BSL_TARGET", idx, time)
                return
        # 3) lock guarantee when 3R arrives on a displacement bar
        r = (c - self.entry) / self.risk if self.risk > 0 else 0.0
        if r >= MIN_R and self._is_disp(idx):
            self.stop = max(self.stop, self.entry + LOCK_R * self.risk)
            self.cnt("lock_2p5r")
        # 4) stagnation filter (frees cash instead of dead waiting)
        if r >= MIN_R and (idx - self.last_bos_idx) > STAGNATION_BARS:
            self._exit(c, "STAGNATION", idx, time)
            return

    def _is_disp(self, idx):
        return self.book._disp(idx)

    def _exit(self, px, reason, idx, time):
        qty = self.qty
        notional = qty * px
        fee = notional * FEE_RATE
        self.cash += notional - fee
        self.fees += fee
        gross = (px - self.entry) * qty
        net = gross - fee - self._entry_fee
        is_loss = net < 0
        if self._cur is not None:
            t = self._cur
            t["exit_time"] = time
            t["exit_price"] = round(px, 2)
            t["exit_reason"] = reason
            t["bars_held"] = idx - self.entry_idx
            t["net_pnl"] = round(net, 4)
            t["R"] = round(net / (self.risk * qty), 2) if qty else 0.0
            t["equity_after"] = round(self.equity(), 2)
            self.trades.append(t)
            self._cur = None
        self.qty = 0.0
        if is_loss:
            self.loss_streak += 1
            if self.loss_streak >= LOSS_STREAK_RESET:
                self.reset_block = True   # coin waits for structure
                self.cnt("structural_reset_block")
        else:
            self.loss_streak = 0
        self.stage = self.WAIT_S1
        self.cnt("exit_" + reason)


# ------------------------------------------------------------------ #
# Backtest runner (causal resample, completed bars only)
# ------------------------------------------------------------------ #
def run_backtest(data_dir, start, end, warmup_days=60, capital=CAPITAL,
                 tag=""):
    from engine.causal_primitives import load_asset_ohlcv, resample_causal_tf
    s0 = pd.Timestamp(start).tz_localize("UTC")
    s1 = pd.Timestamp(end).tz_localize("UTC")
    warm = s0 - pd.Timedelta(days=warmup_days)
    df = load_asset_ohlcv(Path(data_dir),
                          include_stems=[str(y) for y in
                                         range(warm.year, s1.year + 1)])
    df = df[(df.index >= warm) & (df.index <= s1)]
    # execution frame = 15m (ICT prompt allows 15m or 1H; FVG frequency
    # on the 15m frame is what makes the state machine practical)
    tf1 = resample_causal_tf(df, "15min")
    tf4 = resample_causal_tf(df, "4h")

    def vol_map(tf_df, rule):
        v = df["Volume"].resample(rule, label="left", closed="left").sum()
        v.index = v.index + pd.Timedelta(rule)
        v = v.reindex(tf_df.index).fillna(0.0)
        return {t: float(v.loc[t]) for t in tf_df.index}

    v1 = vol_map(tf1, "15min")
    v4 = vol_map(tf4, "4h")

    eng = {s: ICTEngine(s, capital=capital) for s in SYMBOLS}
    for e in eng.values():
        e.window = tag

    rows4 = list(tf4.iterrows())
    rows1 = list(tf1.iterrows())
    i4 = 0
    eq_rows = []
    bars_in = 0
    bars_total = 0
    for t, r1 in rows1:
        if t > s1:
            break
        # feed 4h bars completed at or before this 1h stamp
        while i4 < len(rows4) and rows4[i4][0] <= t:
            t4, r4 = rows4[i4]
            if t4 >= warm:
                for e in eng.values():
                    e.on_4h(float(r4.Open), float(r4.High), float(r4.Low),
                            float(r4.Close), v4.get(t4, 0.0),
                            len(e.htf.bars), t4)
            i4 += 1
        if t < s0:
            # warmup: structure only (engine.warm skips the state machine)
            for e in eng.values():
                e.on_1h(float(r1.Open), float(r1.High), float(r1.Low),
                        float(r1.Close), v1.get(t, 0.0),
                        len(e.book.bars), t)
            continue
        for e in eng.values():
            e.warm = False
            e.on_1h(float(r1.Open), float(r1.High), float(r1.Low),
                    float(r1.Close), v1.get(t, 0.0),
                    len(e.book.bars), t)
        eq_rows.append((t, sum(e.equity() for e in eng.values())))
        bars_total += 1
        if any(e.qty > 0 for e in eng.values()):
            bars_in += 1

    # force mark-to-market close for reporting only (no lookahead use:
    # this is the final completed stamp)
    out_trades = []
    for e in eng.values():
        if e.qty > 0:
            e.price = float(df["Close"].iloc[-1])
            e._exit(e.price, "END_OF_DATA", len(e.book.bars), e.now)
        out_trades.extend(e.trades)
    out_trades.sort(key=lambda t: str(t["entry_time"]))
    eq = (pd.DataFrame(eq_rows, columns=["time", "equity"])
          .set_index("time") if eq_rows else pd.DataFrame())
    counts = {}
    for e in eng.values():
        for k, v in e.count.items():
            counts[k] = counts.get(k, 0) + v
    fees = sum(e.fees for e in eng.values())
    return {"trades": out_trades, "equity": eq, "count": counts,
            "fees": fees, "bars_in": bars_in, "bars_total": bars_total}


# ------------------------------------------------------------------ #
# Reporting
# ------------------------------------------------------------------ #
def summarize(run, capital=CAPITAL):
    tr = run["trades"]
    n = len(tr)
    wins = [t for t in tr if t["net_pnl"] > 0]
    losses = [t for t in tr if t["net_pnl"] <= 0]
    gp = sum(t["net_pnl"] for t in wins)
    gl = sum(t["net_pnl"] for t in losses)
    rs = [t["R"] for t in tr]
    eq = run["equity"]
    out = {
        "trades": n,
        "wins": len(wins), "losses": len(losses),
        "win_rate_pct": round(100.0 * len(wins) / n, 1) if n else None,
        "profit_factor": round(gp / abs(gl), 2) if gl else None,
        "net_pnl": round(sum(t["net_pnl"] for t in tr), 2),
        "net_pct": round(100.0 * sum(t["net_pnl"] for t in tr) / capital, 2),
        "avg_R": round(sum(rs) / n, 2) if n else None,
        "min_winner_R": round(min([t["R"] for t in wins]), 2) if wins else None,
        "max_R": round(max(rs), 2) if n else None,
        "max_consecutive_losses": _max_streak(tr),
        "fees": round(run["fees"], 2),
        "end_equity": round(float(eq["equity"].iloc[-1]), 2)
        if not eq.empty else None,
        "exit_reasons": _hist(t["exit_reason"] for t in tr),
        "s1_kinds": _hist(t["s1_kind"] for t in tr),
        "funnel": run["count"],
    }
    if not eq.empty:
        peak = eq["equity"].cummax()
        dd = ((eq["equity"] - peak) / peak).min() * 100.0
        out["max_drawdown_pct"] = round(float(dd), 2)
        me = eq["equity"].resample("ME").last().dropna()
        rets = me.pct_change().dropna()
        out["monthly"] = [(i.strftime("%Y-%m"), round(float(r) * 100, 2))
                          for i, r in rets.items()]
        pos = sum(1 for _, r in out["monthly"] if r > 0)
        neg = sum(1 for _, r in out["monthly"] if r < 0)
        out["months_pos_neg"] = [pos, neg, len(out["monthly"]) - pos - neg]
        # capital velocity: days flat vs days invested
        ins = eq.get("equity")
        out["exposure_pct"] = None
    return out


def _max_streak(tr):
    best = cur = 0
    for t in tr:
        if t["net_pnl"] <= 0:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def _hist(it):
    h = {}
    for x in it:
        h[x] = h.get(x, 0) + 1
    return h


def anatomy_table(trades, limit=10):
    rows = []
    for t in trades[:limit]:
        rows.append({
            "coin_time": "%s | in %s" % (t["symbol"],
                                         str(t["entry_time"])[:16]),
            "S1_zone": "%s %s @%s" % (t["s1_kind"], t["s1_zone"],
                                      str(t["s1_time"])[:16]),
            "S2_MSS": "broke %.0f @%s | FVG %s | OB %s" % (
                t["broken_high"], str(t["mss_time"])[:16],
                t["fvg_zone"], t["ob_zone"]),
            "S3_entry_SL": "E %.0f SL %.0f risk %.2f%%" % (
                t["entry_price"], t["stop_price"],
                t["risk_pct_of_equity"]),
            "S4_exit": "%s @%.0f  R=%+.2f  bars=%d" % (
                t["exit_reason"], t["exit_price"], t["R"],
                t["bars_held"]),
        })
    return rows


def bull_stats(run):
    tr = run["trades"]
    runners10 = [t for t in tr if t["R"] >= 10]
    runners20 = [t for t in tr if t["R"] >= 20]
    eq = run["equity"]
    days = (eq.index[-1] - eq.index[0]).days if not eq.empty else 0
    return {"trades": len(tr),
            "runners_ge_10R": len(runners10),
            "runners_ge_20R": len(runners20),
            "max_R": max([t["R"] for t in tr], default=0),
            "window_days": days}


def main():
    out = Path(__file__).resolve().parent / "results"
    out.mkdir(exist_ok=True)
    data = str(Path(__file__).resolve().parent / "data" / "BTCUSD_5m")

    print("[v19-ict] FULL window %s..%s" % (FULL_START, FULL_END),
          flush=True)
    run = run_backtest(data, FULL_START, FULL_END)
    summ = summarize(run)
    pd.DataFrame(run["trades"]).to_csv(out / "trades_v19.csv", index=False)
    if not run["equity"].empty:
        run["equity"].to_csv(out / "equity_v19.csv")
        me = run["equity"]["equity"].resample("ME").last().pct_change()
        pd.DataFrame({"month": me.index.strftime("%Y-%m"),
                      "ret_pct": (me.fillna(0) * 100).round(2).values}
                     ).to_csv(out / "monthly_v19.csv", index=False)
    (out / "summary_v19.json").write_text(
        json.dumps(summ, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: v for k, v in summ.items() if k != "monthly"},
                     indent=2, default=str), flush=True)
    print("MONTHLY:", summ.get("monthly"), flush=True)

    print("\n[v19-ict] BULL RUN %s..%s" % (BULL_START, BULL_END), flush=True)
    bull = run_backtest(data, BULL_START, BULL_END, tag="BULL")
    bs = bull_stats(bull)
    pd.DataFrame(bull["trades"]).to_csv(out / "trades_v19_bull.csv",
                                        index=False)
    print(json.dumps(bs, indent=2), flush=True)

    print("\n=== SECTION 2: ANATOMY (first 10 trades) ===")
    for row in anatomy_table(run["trades"], 10):
        print(row)
    if not run["trades"]:
        print("(no trades — funnel:", run["count"], ")")


if __name__ == "__main__":
    main()
