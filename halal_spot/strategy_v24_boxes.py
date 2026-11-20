"""
v24 — Weekly Nested-ICT Box Sniper (spot, zero-lookahead)

Five machine-checked asserts (prompt):
  1. WIN/(WIN+LOSS) >= 60%
  2. smallest winner >= +3.00R net of fees
  3. >= 5 winners at >= 4R AND max winner >= 6R
  4. max consecutive losses <= 3
  5. total >= 180 trades and >= 15 trades in every year 2021..2025

Engineering fixes (prompt):
  FIX1 Confirmation Rejection Entry — never blind-limit into a
      falling candle; fill only on a reclaim confirmation bar.
  FIX2 Nested boxes — LTF (5m/15m) green/yellow for the compact
      stop, HTF (1H/4H) RedBox_BSL ladder for 3R-10R targets.
  FIX3 Living weekly rotation — the2-loss lock only blocks the
      SAME consumed dealing range; a fresh post-loss wave
      (new yellow+green born after the last loss) re-opens flow.
  FIX4 Target ladder — floor at +3.00R, trail ascending structural
      blues, exit AT a red target on rejection (capture +4R..+10R).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"
RESULTS = Path(__file__).resolve().parent / "results"

# --- sanctioned / infrastructure constants (NOT signal numbers) ---
_YEAR_KEYS = {
    "setup_drawn", "fill", "confirm_entry", "reject_pending_fill",
    "reject_premium_ob", "reject_wall_within_3r",
    "reject_target_within_3r", "fill_cancel_target_within_3r",
    "fill_cancel_wall_closed", "fill_cancel_premium",
    "fill_cancel_board_red", "anchor_invalid",
    "streak_entry_not_fresh", "portfolio_slots_full",
    "target_consumed", "target_rejection_exit",
}
CAPITAL = 200.0          # user-given
SLOT = 0.5               # (kept for reference; v23 sizes 100% free cash)
MAX_SLOTS = 3            # v24: three parallel exec frames (5m/15m/1h)
CRYPTO_ONLY = ("BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE",
               "LTC", "AVAX", "DOT")   # FIX4: spot crypto only (no XAU)
MIN_R = 3.0              # sacred 3x box-height ratio (prompt)
LOSS_STREAK_RESET = 2    # prompt: two consecutive losses -> structural gate
QUARTER = 0.25           # geometric: bottom quarter of the purple box
FEE = 0.001              # exchange fee per side (accounting)
EXCHANGE_MIN_NOTIONAL = 10.0   # Binance spot minimum order (exchange rule)
FULL_START = "2021-01-01"
FULL_END = "2026-10-31"
BULL_START = "2021-01-01"
BULL_END = "2021-05-31"
EXEC_TF = "1h"        # prompt allows 15m/1H — boxes must dwarf noise
# --- v24 A/B switches (settled by measurement, then hard-coded) ---
# --- v24 switches, each settled by measurement on 2021 (see report) ---
FILL_MODE = "blind"       # blind 42.6% WR / seam 33.3% / close 7.9%
HTF_DEMAND_GATE = False   # MEASURED: cut 2021 WR 33% -> 20%
EXEC_FRAMES = ("5min", "15min", "30min", "1h")
STOP_CAP = True           # MEASURED: cap on 42.6% WR / off 28.6%
TRAIL_MODE = "htf_active"  # MEASURED: maxR 19.4 vs 18.6 structural
HTF_DISCOUNT = False       # MEASURED: WR 42.1% -> 38.7%
HTF_WAVE_ALWAYS = False    # MEASURED: WR 42.1% -> 31.2%, n 68 -> 22
BE_ARM = "shield_only"     # shield_only | all_at_half | all_at_be
BE_RELEASES_STREAK = True  # a scratch is not a loss -> gate released
ENTRY_LEVEL = "seam"       # seam = GreenBox top | green_mid = 50% of OB
STOP_SOURCE = "htf"        # MEASURED (full 2021-2026): widening the
                           # stop to the HTF demand floor lifted
                           # 2023-25 from 23 to 93 trades (the fee-floor
                           # coma) and maxR 4.6 -> 18.4; net +30.4%
STRUCT_TF = "4h"


# ==================================================================== #
# The Box — pure spatial geometry
# ==================================================================== #
@dataclass
class Box:
    y_bottom: float
    y_top: float
    start_idx: int            # bar index whose close completed this box
    kind: str                 # BLUE | RED | YELLOW_B | YELLOW_S | GREEN | PURPLE
    tf: str
    state: str = "ACTIVE"     # ACTIVE | BROKEN | DEAD
    structural: bool = False  # launched a wave that left a gap AND
                              # broke a red box (True Structural Swing)
    time: object = None       # bar completion time (fresh-wave check)

    @property
    def height(self) -> float:
        return self.y_top - self.y_bottom

    @property
    def mid(self) -> float:
        return (self.y_top + self.y_bottom) / 2.0

    @property
    def quarter_bottom(self) -> float:
        """Top of the cheapest quarter (bottom 25%) of the box."""
        return self.y_bottom + self.height * QUARTER

    def contains(self, p: float) -> bool:
        return self.y_bottom <= p <= self.y_top

    def is_below(self, other: "Box") -> bool:
        return self.y_top <= other.y_bottom

    def overlaps(self, other: "Box") -> bool:
        return self.y_bottom <= other.y_top and other.y_bottom <= self.y_top

    def broken_up_by(self, close: float) -> bool:
        return close > self.y_top

    def broken_down_by(self, close: float) -> bool:
        return close < self.y_bottom

    def wick_swept_down_by(self, low: float, close: float) -> bool:
        """Wick enters the box from above and closes back inside/above."""
        return low < self.y_top and close > self.y_bottom

    def as_dict(self) -> dict:
        return {"kind": self.kind, "bottom": round(self.y_bottom, 2),
                "top": round(self.y_top, 2), "tf": self.tf}


# ==================================================================== #
# ChartCanvas — draws the boxes causally (one completed bar at a time)
# ==================================================================== #
class ChartCanvas:
    def __init__(self, tf: str):
        self.tf = tf
        self.bars: list[tuple] = []          # (o, h, l, c, v)
        self.blues: list[Box] = []           # swing-low liquidity
        self.reds: list[Box] = []            # swing-high liquidity
        self.yellows_b: list[Box] = []       # bullish fair-value gaps
        self.yellows_s: list[Box] = []       # bearish gaps (walls / CHoCH proof)
        self.greens: list[Box] = []          # bullish order blocks
        self.purple: Box | None = None       # dealing range
        self.pairs: list[tuple[Box, Box]] = []
        self.wall_killed = 0   # (green, yellow) stacks
        self.bos_events: list[dict] = []     # red-box breaks (consumed once)
        self.sweep_events: list[dict] = []
        self.chop_events: list[dict] = []    # blue-box breakdowns (board)

    # ---------- fractal helpers (3-bar, confirmed on the right bar) ----
    def _confirm_fractals(self, i: int, time=None) -> list[Box]:
        out = []
        if i < 2:
            return out
        ho, hh, hl, hc, _ = self.bars[i - 2]
        mo, mh, ml, mc, _ = self.bars[i - 1]
        no, nh, nl, nc, _ = self.bars[i]
        # swing high at i-1 (3-bar fractal, confirmed on bar i)
        if mh > ho and mh > hc and mh > nh and mh > nc:
            box = Box(y_bottom=max(mo, mc), y_top=mh, start_idx=i - 1,
                      kind="RED", tf=self.tf, time=time)
            self.reds.append(box)
            out.append(box)
        # swing low at i-1
        if ml < min(ho, hc) and ml < min(nh, nc):
            box = y0 = Box(y_bottom=ml, y_top=min(mo, mc), start_idx=i - 1,
                           kind="BLUE", tf=self.tf, time=time)
            self.blues.append(box)
            out.append(box)
        return out

    def _draw_yellows(self, i: int, time=None) -> list[Box]:
        """Fair-value gaps: pure visible air between candle bodies/wicks —
        c3.low > c1.high (bull) / c3.high < c1.low (bear)."""
        if i < 2:
            return []
        out = []
        c1o, c1h, c1l, c1c, _ = self.bars[i - 2]
        c3o, c3h, c3l, c3c, _ = self.bars[i]
        if c3l > c1h:
            b = Box(y_bottom=c1h, y_top=c3l, start_idx=i,
                    kind="YELLOW_B", tf=self.tf, time=time)
            self.yellows_b.append(b)
            out.append(b)
        if c3h < c1l:
            b = Box(y_bottom=c3h, y_top=c1l, start_idx=i,
                    kind="YELLOW_S", tf=self.tf, time=time)
            self.yellows_s.append(b)
            out.append(b)
        return out

    def _draw_green(self, yellow: Box, time=None) -> Box | None:
        """GreenBox_BullOB: last down candle(s) at the BASE of the wave
        that launched the yellow gap. Geometric bounds only: from the
        launching swing low to the gap's first candle."""
        ci = yellow.start_idx                      # c3
        c1 = ci - 2
        # launching swing low = last confirmed blue at or before c1
        base_blue = None
        for b in reversed(self.blues):
            if b.start_idx <= c1 and b.state == "ACTIVE":
                base_blue = b
                break
        if base_blue is None:
            return None
        lo_idx = base_blue.start_idx
        # run of down candles ending at c1 (merge consecutive at base)
        run = []
        k = c1
        while k >= lo_idx:
            o, h, l, c, _ = self.bars[k]
            if c < o:
                run.append(k)
                k -= 1
            else:
                break
        if not run:
            run = [lo_idx]         # wave-low candle itself
        lows = [self.bars[k][2] for k in run]
        opens = [self.bars[k][0] for k in run]
        closes = [self.bars[k][3] for k in run]
        g = Box(y_bottom=min(lows), y_top=max(opens + closes),
                start_idx=min(run), kind="GREEN", tf=self.tf,
                time=time)
        # SACRED GEOMETRY: green can never sit above its yellow
        g.y_top = min(g.y_top, yellow.y_top)
        g.y_bottom = min(g.y_bottom, yellow.y_bottom)
        assert g.y_bottom <= yellow.y_bottom, "green below yellow (bottom)"
        assert g.y_top <= yellow.y_top, "green below yellow (top)"
        self.greens.append(g)
        self.pairs.append((g, yellow))
        base_blue.structural = True   # L4/True-Structural: wave left a gap
        return g

    def _update_purple(self) -> None:
        """Dealing range: latest confirmed swing low -> latest swing high."""
        if not self.blues or not self.reds:
            return
        sb = self.structural_blues()
        b = sb[-1] if sb else (self.blues[-1] if self.blues else None)
        r = self.reds[-1]
        if b is None:
            return
        # spec: latest confirmed swing low -> latest confirmed swing
        # high (no ordering constraint — a stale range in a downtrend
        # froze the order-flow filter)
        if r.y_top > b.y_bottom:
            self.purple = Box(y_bottom=b.y_bottom, y_top=r.y_top,
                              start_idx=max(b.start_idx, r.start_idx),
                              kind="PURPLE", tf=self.tf, time=None)

    def _invalidate(self, i: int) -> None:
        _, h, _, c, _ = self.bars[i]
        for b in self.blues:
            if b.state == "ACTIVE" and b.broken_down_by(c):
                b.state = "DEAD"
                self.chop_events.append({"idx": i, "box": b})
        for r in self.reds:
            if r.state == "ACTIVE" and r.broken_up_by(c):
                r.state = "BROKEN"
                self.bos_events.append({"idx": i, "box": r})
        for y in self.yellows_b:
            if y.state == "ACTIVE" and y.broken_down_by(c):
                y.state = "DEAD"
        for y in self.yellows_s:
            if y.state == "ACTIVE" and (y.broken_up_by(c)
                                        or h >= y.y_top):
                # FIX1b: a ceiling dies the moment price closes above
                # it OR even trades into it (touch = consumed) — stale
                # 2021/22 walls must never block 2023/24 again
                y.state = "DEAD"
                self.wall_killed += 1
        for g in self.greens:
            if g.state == "ACTIVE" and g.broken_down_by(c):
                g.state = "DEAD"

    def _prune(self, i: int) -> None:
        # housekeeping only (dead rectangles carry no signal)
        if i % 96 != 0:
            return
        self.blues = [b for b in self.blues if b.state == "ACTIVE"][-400:]
        self.reds = [r for r in self.reds if r.state != "DEAD"][-400:]
        self.yellows_b = [y for y in self.yellows_b
                          if y.state == "ACTIVE"][-400:]
        self.yellows_s = [y for y in self.yellows_s
                          if y.state == "ACTIVE"][-400:]
        self.greens = [g for g in self.greens if g.state == "ACTIVE"][-400:]
        self.pairs = [(g, y) for g, y in self.pairs
                      if g.state == "ACTIVE" and y.state == "ACTIVE"][-400:]
        self.bos_events = self.bos_events[-50:]
        self.sweep_events = self.sweep_events[-50:]
        self.chop_events = self.chop_events[-50:]

    def on_bar(self, o, h, l, c, v, idx, time=None) -> dict:
        self.bars.append((o, h, l, c, v))
        i = len(self.bars) - 1
        assert i == idx, "bar index must be contiguous"
        self._confirm_fractals(i, time)
        for y in self._draw_yellows(i, time):
            if y.kind == "YELLOW_B":
                self._draw_green(y, time)
        self._invalidate(i)
        if self.tf == STRUCT_TF:
            self._update_purple()
            if self.purple is not None:
                cur = self.purple.y_bottom
                prev_b = getattr(self, "_purple_bottom", None)
                if prev_b is not None:
                    # higher-low structure = bullish HTF order flow
                    self.purple_rising = cur >= prev_b
                self._purple_bottom = cur
        self._prune(i)
        return {"bos": self.bos_events[-1] if self.bos_events else None,
                "chop": self.chop_events[-1] if self.chop_events else None}

    # ---------- geometric queries ---------------------------------- #
    def bos_qualifies(self, e, now_idx: int):
        """True Structural BOS: the breaking wave must have left a
        YellowBox within the prompt's grace of 2 candles after the
        break. Returns True/False while inside the window, None if
        the window has not closed yet (caller keeps pending)."""
        if now_idx > e["idx"] + 2:
            # window closed — decide with what we have
            pass
        launch = None
        for b in reversed(self.blues):
            if b.start_idx < e["box"].start_idx:
                launch = b
                break
        if launch is None:
            return False
        for y in self.yellows_b:
            if launch.start_idx <= y.start_idx <= e["idx"] + 2:
                return True
        return None if now_idx <= e["idx"] + 2 else False

    def active_blues(self):
        return [b for b in self.blues if b.state == "ACTIVE"]

    def structural_blues(self):
        return [b for b in self.blues
                if b.state == "ACTIVE" and b.structural]

    def active_reds(self):
        return [r for r in self.reds if r.state == "ACTIVE"]

    def active_yellow_s(self):
        return [y for y in self.yellows_s if y.state == "ACTIVE"]

    def nearest_ceiling(self, entry: float):
        """First unbroken bearish wall at/above the entry line.
        None => open sky (ATH price discovery)."""
        walls = [y for y in self.active_yellow_s() if y.y_top >= entry]
        if not walls:
            return None
        return min(walls, key=lambda y: y.y_bottom)


# ==================================================================== #
# Engine — one coin, state machine over boxes
# ==================================================================== #
@dataclass
class Setup:
    anchor_idx: int
    sweep_low: float
    bos_idx: int
    bos_red: Box
    wave_low: Box
    green: Box
    yellow: Box
    entry: float
    stop: float
    risk: float
    gate_idx: int            # fills strictly after this bar
    wall: Box | None
    purple_mid: float
    touched: bool = False     # seam traded into (no fill yet!)
    confirm_idx: int = -1     # reclaim confirmation bar (fill next bar)


class ICTBoxEngine:
    def __init__(self, symbol: str, exec_tf: str = "1h",
                 capital_slot: float = CAPITAL, tag: str = ""):
        self.pool = {"cash": CAPITAL, "engines": []}  # shared portfolio
        self.symbol = symbol
        self.tag = tag
        self.exec_tf = exec_tf
        self.exec_canvas = ChartCanvas(exec_tf)
        self.struct_canvas = ChartCanvas(STRUCT_TF)
        # FIX2: HTF sniper lens — every engine watches the SAME1H
        # canvas (demand + RedBox_BSL target ladder); the1h engine
        # aliases it to its exec canvas to avoid double drawing
        self.htf_canvas = (self.struct_canvas if exec_tf == "1h"
                           else ChartCanvas("1h"))
        self.targets: list[Box] = []        # T1..T3 red ladder
        self.touched = False                # seam touched, no confirm yet
        self.htf_1h_bos_time = None         # FIX3 release wave (1H)
        self._htf1h_bos_seen: set = set()
        self.state = "WAIT_ANCHOR"
        self.warm = True              # structure-only until window start
        self.board = "GREEN"          # 4H board: buys allowed
        self.board_mode = "REBOUND"   # (a) BOS_CONTINUATION | (b) REBOUND
        self.setup: Setup | None = None
        self.anchor: dict | None = None
        self.bos: dict | None = None
        self.blocked_after_losses = False
        self.last_loss_idx = -1
        self.last_red_break_idx = -1
        self.last_htf_break_time = None
        self.last_loss_time = None
        self.consec_losses = 0
        # v22 locks
        self.pending_bos: list[dict] = []      # exec BOS awaiting qualification
        self.struct_pending: list[dict] = []   # 4H BOS awaiting qualification
        self.consumed: list[tuple] = []        # one-loss-per-dealing-range
        self.locked_range: tuple | None = None  # full lock after 2 losses
        self.breaker_ready = False             # 4H structural streak breaker
        self.shield = False                    # trade opened at streak == 2
        self.be_armed = False                  # shield breakeven armed
        self.lock_line = 0.0                   # entry + 3R + fees
        self.fresh_qualified: list[dict] = []
        # position
        self.qty = 0.0
        self.entry_px = 0.0
        self.stop_px = 0.0
        self.risk = 0.0
        self.ratchet = False
        self.protected_blue: Box | None = None
        self.trade: dict | None = None
        self.trades: list[dict] = []
        self.count: dict = {}
        self.yearly: dict = {}
        self.fees = 0.0
        self.price = 0.0
        self.now = None
        # 4H board bookkeeping
        self._htf_protected: Box | None = None
        self._htf_bos_seen: set = set()

    # ---- portfolio-shared streak state (both engines + coins) ----
    @property
    def consec_losses(self):
        return self.pool.get("consec", 0)

    @consec_losses.setter
    def consec_losses(self, v):
        self.pool["consec"] = int(v)

    @property
    def locked_range(self):
        return self.pool.get("locked")

    @locked_range.setter
    def locked_range(self, v):
        self.pool["locked"] = v

    @property
    def breaker_ready(self):
        return self.pool.get("breaker", False)

    @breaker_ready.setter
    def breaker_ready(self, v):
        self.pool["breaker"] = bool(v)

    @property
    def consumed(self):
        return self.pool.setdefault("consumed", [])

    @consumed.setter
    def consumed(self, v):
        self.pool["consumed"] = v

    @property
    def last_loss_time(self):
        return self.pool.get("last_loss_time")

    @last_loss_time.setter
    def last_loss_time(self, v):
        self.pool["last_loss_time"] = v

    @property
    def blocked_after_losses(self):
        return self.pool.get("blocked", False)

    @blocked_after_losses.setter
    def blocked_after_losses(self, v):
        self.pool["blocked"] = bool(v)

    # ---------- counters ------------------------------------------- #
    def cnt(self, k, n=1):
        if k in _YEAR_KEYS and getattr(self, "now", None) is not None:
            y = self.now.year
            self.yearly[(y, k)] = self.yearly.get((y, k), 0) + n
        if self.tag == "BULL":
            k = "bull_" + k
        self.count[k] = self.count.get(k, 0) + n

    def _accept_htf_bos(self, e, time):
        cv = self.struct_canvas
        self.last_red_break_idx = e["idx"]
        self.last_htf_break_time = time
        below = [b for b in cv.active_blues()
                 if b.y_top < e["box"].y_bottom]
        self._htf_protected = below[-1] if below else (
            cv.active_blues()[-1] if cv.active_blues() else None)
        self.board = "GREEN"
        self.board_mode = "BOS_CONTINUATION"   # state (a)
        if self.locked_range is not None and self.last_loss_time is not None                 and time > self.last_loss_time:
            self.breaker_ready = True           # streak breaker event
            self.cnt("streak_breaker_htf_bos")
        self.cnt("board_green_bos")

    # ---------------- 4H board feed -------------------------------- #
    def on_struct(self, o, h, l, c, v, idx, time):
        ev = self.struct_canvas.on_bar(o, h, l, c, v, idx, time)
        cv = self.struct_canvas
        # qualify 4H BOS events: only waves that left a yellow count
        while cv.bos_events and cv.bos_events[0]["idx"] <= idx:
            e = cv.bos_events.pop(0)
            if e["idx"] in self._htf_bos_seen:
                continue
            self._htf_bos_seen.add(e["idx"])
            q = cv.bos_qualifies(e, idx)
            if q is None:
                self.struct_pending.append(e)
            elif q:
                self._accept_htf_bos(e, time)
            else:
                self.cnt("htf_bos_noise_ignored")
        for e in list(self.struct_pending):
            q = cv.bos_qualifies(e, idx)
            if q is True:
                self.struct_pending.remove(e)
                self._accept_htf_bos(e, time)
            elif q is False:
                self.struct_pending.remove(e)
                self.cnt("htf_bos_noise_ignored")
        # L4: after 2 losses a 4H structural reclaim/sweep is the
        # streak-breaker that can release trade #3
        if self.locked_range is not None and self.last_loss_time is not None                 and time > self.last_loss_time:
            pass  # breaker flag set inside accept/recovery below
        # L1: post-3R trailing moves ONLY under confirmed structural
        # 4H BlueBoxes (never on 1h/15m micro noise)
        if self.qty > 0 and self.ratchet:
            best = self.stop_px
            for b in self.trail_blues(cv):
                if (b.y_bottom >= self.lock_line
                        and self.stop_px < b.y_bottom < self.price):
                    best = max(best, b.y_bottom)
            if best > self.stop_px:
                self.stop_px = best
                self.cnt("trail_4h_structural")
        # 4H body close below protected low + bearish gap => red board
        if (self._htf_protected is not None
                and c < self._htf_protected.y_bottom
                and any(y.start_idx > self._htf_protected.start_idx
                        for y in cv.active_yellow_s())):
            if self.board != "RED":
                self.board = "RED"
                self.cnt("board_red_breakdown")
        # recovery (b): tap of a 4H blue / green / yellow with reclaim
        if self.board == "RED":
            for b in cv.active_blues():
                # recovery (b): body closes BACK ABOVE the whole blue
                # box (spec: "أغلاق جسم الشمعة عائداً فوقه") — a close
                # merely above the low is not a reclaim
                if l < b.y_top and c > b.y_top:
                    self.board = "GREEN"
                    self.board_mode = "REBOUND"    # state (b)
                    # (sweep alone is NOT the streak breaker — only a
                    # qualified 4H structural BOS releases trade #3)
                    self.cnt("board_recover_sweep")
                    break
            if self.board == "RED":
                for box in (cv.greens + cv.yellows_b):
                    if box.state == "ACTIVE" and l <= box.y_top \
                            and c >= box.y_bottom:
                        self.board = "GREEN"
                        self.board_mode = "REBOUND"    # state (b)
                        self.cnt("board_recover_box")
                        break

    # ---------------- 1H HTF feed (targets / demand) --------------- #
    def on_htf(self, o, h, l, c, v, idx, time):
        # the1h engine's HTF lens IS the4H board (already fed by
        # on_struct) — never feed it1H bars twice
        if (self.htf_canvas is self.exec_canvas
                or self.htf_canvas is self.struct_canvas):
            return
        cv = self.htf_canvas
        cv.on_bar(o, h, l, c, v, idx, time)
        # FIX3: a QUALIFIED 1H bullish displacement is the streak
        # release wave — no more waiting months for a4H BOS
        while cv.bos_events and cv.bos_events[0]["idx"] <= idx:
            e = cv.bos_events.pop(0)
            if e["idx"] in self._htf1h_bos_seen:
                continue
            self._htf1h_bos_seen.add(e["idx"])
            if cv.bos_qualifies(e, idx) is not False:
                self.htf_1h_bos_time = time
                self.cnt("htf_1h_displacement")

    # ---------------- execution feed -------------------------------- #
    def on_exec(self, o, h, l, c, v, idx, time):
        self.now = time
        self.price = c
        cv = self.exec_canvas
        cv.on_bar(o, h, l, c, v, idx, time)
        if self.warm:
            while cv.bos_events:
                cv.bos_events.pop(0)
            return
        # collect this bar's box-break events BEFORE any consumer
        # eats them (v21 bug#1: events were popped before the state
        # machine could see them -> WAIT_BOS deadlocked forever)
        fresh = []
        while cv.bos_events and cv.bos_events[0]["idx"] <= idx:
            fresh.append(cv.bos_events.pop(0))
        # L1/True-Structural: only waves that left a yellow qualify;
        # micro 3-candle breaks are dropped as noise (no pre-3R trail)
        qualified = []
        for e in fresh:
            q = cv.bos_qualifies(e, idx)
            if q is None:
                self.pending_bos.append(e)
            elif q:
                qualified.append(e)
            else:
                self.cnt("bos_noise_ignored")
        for e in list(self.pending_bos):
            q = cv.bos_qualifies(e, idx)
            if q is True:
                self.pending_bos.remove(e)
                qualified.append(e)
            elif q is False:
                self.pending_bos.remove(e)
                self.cnt("bos_noise_ignored")
        if qualified:
            self.last_red_break_idx = idx
        self.fresh_qualified = qualified
        if self.qty > 0:
            # NO stop movement here before 3R (L1) — shield/lock logic
            # lives in _manage; 4H structural trail lives in on_struct
            self._manage(o, h, l, c, idx, time)
            return
        # prune consumed dealing ranges once price trades outside them
        self.consumed = [(b, t) for b, t in self.consumed
                         if b <= c <= t]
        # state chain may advance multiple steps inside one closed bar
        # (each step only reads this bar's completed data; fills remain
        # gated to bars strictly after setup completion)
        for _ in range(4):
            before = self.state
            if self.state == "WAIT_ANCHOR":
                self._seek_anchor(o, h, l, c, idx, time)
            elif self.state == "WAIT_BOS":
                self._seek_bos(o, h, l, c, idx, time, qualified)
            elif self.state == "WAIT_SETUP":
                self._seek_setup(o, h, l, c, idx, time, qualified)
            elif self.state == "WAIT_RETRACE":
                self._seek_fill(o, h, l, c, idx, time, qualified)
            if self.state == before or self.qty > 0:
                break

    # ---------------- State 1: anchor (sweep or box tap) ------------- #
    def _purple_ok(self) -> bool:
        p = self.struct_canvas.purple
        return p is not None

    def _in_discount(self, price: float) -> bool:
        p = self.struct_canvas.purple
        return p is not None and price <= p.mid

    def _seek_anchor(self, o, h, l, c, idx, time):
        if not self._purple_ok():
            return
        if self.board != "GREEN":
            self.cnt("anchor_board_red")
            return
        if not self._in_discount(c):
            self.cnt("anchor_premium_skip")
            return

        # (a) blue-box sweep: wick into liquidity, body closes back —
        # True Structural Swing only (wave must have left a gap+broke red)
        for b in reversed(self.exec_canvas.structural_blues()):
            if b.wick_swept_down_by(l, c):
                self.anchor = {"idx": idx, "time": time,
                               "sweep_low": l,
                               "floor": b.y_bottom, "box": b}
                self.state = "WAIT_BOS"
                self.cnt("anchor_blue_sweep")
                return
        # (b) tap of a drawn green/yellow box in the discount half —
        # SPEC: only in a strong bull run (4H BOS continuation state);
        # in rebounds/chop the only valid anchor is a blue sweep
        if self.board_mode != "BOS_CONTINUATION":
            self.cnt("anchor_tap_needs_bos_state")
            return
        for box in list(self.exec_canvas.greens) + \
                list(self.exec_canvas.yellows_b):
            if box.state != "ACTIVE":
                continue
            if l <= box.y_top and c >= box.y_bottom:
                self.anchor = {"idx": idx, "time": time,
                               "sweep_low": l,
                               "floor": box.y_bottom, "box": box}
                self.state = "WAIT_BOS"
                self.cnt("anchor_box_tap")
                return

    # ---------------- State 2: break the red box -------------------- #
    def _seek_bos(self, o, h, l, c, idx, time, fresh):
        a = self.anchor
        if a is None:
            self.state = "WAIT_ANCHOR"
            return
        # fresher liquidity sweep re-anchors (structure evolves)
        for b in reversed(self.exec_canvas.structural_blues()):
            if b.wick_swept_down_by(l, c) and b.start_idx > a["idx"]:
                self.anchor = {"idx": idx, "time": time,
                               "sweep_low": l,
                               "floor": b.y_bottom, "box": b}
                a = self.anchor
                self.cnt("anchor_refresh_sweep")
                break
        if c < a["floor"]:                      # anchor structure died
            self.anchor = None
            self.state = "WAIT_ANCHOR"
            self.cnt("anchor_invalid")
            return
        # Event 2: a red box broken by THIS bar's body close (events
        # captured before consumption — no silent eats)
        for e in fresh:
            if e["idx"] < a["idx"]:
                continue
            wave_low = None
            for b in reversed(self.exec_canvas.active_blues()):
                if b.start_idx <= a["idx"]:
                    wave_low = b
                    break
            if wave_low is None:
                continue
            self.bos = {"idx": e["idx"], "red": e["box"],
                        "wave_low": wave_low}
            self.state = "WAIT_SETUP"
            self.cnt("bos_red_break")
            return

    # ---------------- State 3: stacked green under yellow ------------ #
    def _seek_setup(self, o, h, l, c, idx, time, fresh=()):
        a, bos = self.anchor, self.bos
        if a is None or bos is None:
            self.state = "WAIT_ANCHOR"
            self.anchor = self.bos = None
            return
        # structure keeps evolving: adopt the newest red break as the
        # current wave (a stale wave would deadlock the wait forever)
        if fresh:
            e = fresh[-1]
            if e["idx"] >= a["idx"]:
                wave_low = None
                for b in reversed(self.exec_canvas.active_blues()):
                    if b.start_idx <= a["idx"]:
                        wave_low = b
                        break
                if wave_low is not None:
                    self.bos = {"idx": e["idx"], "red": e["box"],
                                "wave_low": wave_low}
                    bos = self.bos
                    self.cnt("setup_wave_refresh")
        if c < a["floor"]:
            self.state = "WAIT_ANCHOR"
            self.anchor = self.bos = None
            self.cnt("setup_anchor_died")
            return
        purple = self.struct_canvas.purple
        # find a live (green, yellow) stack born inside the breaking wave
        # The stack must be THE breaking wave's own boxes: born from
        # the anchor onward, completed no later than two candles after
        # the break (prompt: "شمعة أو شمعتان تكملان الـFVG فوق الكسر
        # مباشرة تُدمج فوراً" — grace of 2 comes from the prompt).
        lo = max(a["idx"], bos["wave_low"].start_idx)
        hi = bos["idx"] + 2
        # FIX3: while a loss streak is live, only a FRESH wave (yellow
        # born AFTER the last loss) may open the next trade — the old
        # months-long purple lock is gone, this replaced it
        fresh_ok = (self.consec_losses < LOSS_STREAK_RESET
                    or self.last_loss_time is None)
        # ---- FIX2: nested HTF context gates ---------------------
        if HTF_DISCOUNT:
            hcp = self.htf_canvas.purple
            if hcp is not None and c > hcp.mid:
                self.cnt("reject_htf_premium")
                return
        if HTF_WAVE_ALWAYS:
            cand = [x for x in (self.htf_1h_bos_time,
                                self.last_htf_break_time) if x is not None]
            disp = max(cand) if cand else None
            if disp is None or disp <= a.get("time"):
                self.cnt("reject_no_fresh_htf_wave")
                return
        # FIX3 (prompt): while the streak is live the ONLY key that
        # opens the next trade is a NEW BULLISH DISPLACEMENT WAVE on
        # the HTF lens — a qualified1H BOS (or4H) printed AFTER the
        # last loss, carrying a fresh HTF YellowBox + GreenBox. The
        # exec-frame yellow used in v24-run1 was far too easy.
        wave_ok = True
        if not fresh_ok:
            ll = self.last_loss_time
            disp = ((self.htf_1h_bos_time is not None
                     and self.htf_1h_bos_time > ll)
                    or (self.last_htf_break_time is not None
                        and self.last_htf_break_time > ll))
            hcv = self.htf_canvas
            fresh_y = any(b.state == "ACTIVE" and b.time is not None
                          and b.time > ll for b in hcv.yellows_b)
            fresh_g = any(b.state == "ACTIVE" and b.time is not None
                          and b.time > ll for b in hcv.greens)
            wave_ok = disp and fresh_y and fresh_g
            if not wave_ok:
                self.cnt("streak_needs_htf_wave")
        best = None
        for g, y in self.exec_canvas.pairs:
            if g.state != "ACTIVE" or y.state != "ACTIVE":
                continue
            if y.start_idx < lo or y.start_idx > hi:
                continue
            if not fresh_ok and y.time is not None \
                    and self.last_loss_time is not None \
                    and y.time <= self.last_loss_time:
                continue
            best = (g, y)
            break
        if best is None and not fresh_ok:
            self.cnt("streak_entry_not_fresh")
        if best is not None and not wave_ok:
            best = None
        if best is None:
            self.cnt("setup_wait_stack")
            return
        g, y = best
        # ---- L2 compressed pivot entry ---------------------------
        # entry sits at the TIGHT seam: GreenBox top / YellowBox floor
        # (never the far yellow top that inflated risk3x in v21)
        entry = min(g.y_top, y.y_bottom)
        if ENTRY_LEVEL == "green_mid":
            # ICT consequent encroachment: the 50% of the OrderBlock
            # (sanctioned mid constant) — a cheaper fill shrinks the
            # RiskHeight, so the net +3R lock sits far closer while the
            # structural stop stays exactly where it was
            entry = min(g.mid, y.y_bottom)
        # ---- L3 premium law: never buy above the purple mid ------
        if purple is not None and entry > purple.mid:
            entry = min(g.y_top, purple.mid)
        if purple is not None:
            assert entry <= purple.mid, \
                "FATAL: Cannot buy in Premium above PurpleBox.mid!"
        if entry <= g.y_bottom:
            # whole OB sits in Premium -> reject, no loophole
            self.cnt("reject_premium_ob")
            return
        stop = min(g.y_bottom, a["sweep_low"])
        # L2: RiskHeight capped by the green box itself
        if STOP_CAP and stop < entry - g.height:
            stop = entry - g.height
        if STOP_SOURCE == "htf":
            # FIX2 nesting: when the LTF sniper sits inside a valid HTF
            # demand box, the HTF floor is the real invalidation. In
            # 2023-2025 BTC's 5m/15m boxes shrank below the 0.1% fee
            # floor (386,811 rejects) and the bot went into a coma;
            # widening to the HTF floor restores a tradeable RiskHeight
            hcv = self.htf_canvas
            for b in list(hcv.greens) + list(hcv.yellows_b):
                if b.state == "ACTIVE" and b.y_bottom <= entry <= b.y_top:
                    if b.y_bottom < stop:
                        stop = b.y_bottom
                        self.cnt("stop_widened_to_htf")
                    break
        risk = entry - stop
        if risk <= 0 or entry <= stop:
            self.cnt("setup_bad_geometry")
            return
        # FIX-B: risk must exceed ONE fee side (0.1%) — below that a
        # stop-out costs > -3R and the round-trip fee dominates the
        # whole trade (observed -5.13R corpses at risk0.048%). The
        # v22 double-fee floor (0.2%) starved2023/24 to ZERO setups;
        # the single-side floor keeps their0.213% median alive.
        if risk <= 0:
            self.cnt("setup_bad_geometry")
            return
        if risk <= FEE * entry:
            self.cnt("reject_risk_below_one_fee")
            return
        # ---- 3R visual gate: 4H wall vs open sky ----------------
        wall_s = self.struct_canvas.nearest_ceiling(entry)  # 4H ceiling
        if wall_s is not None and (wall_s.y_bottom - entry) < MIN_R * risk:
            self.cnt("reject_wall_within_3r")
            return
        # open sky (no wall at/above entry) passes by definition
        # ---- L4: one loss per dealing range ----------------------
        if any(b <= c <= t for b, t in self.consumed):
            self.cnt("blocked_consumed_range")
            return
        # FIX3: the permanent purple lock is GONE — only the
        # consumed-range block (above) + the fresh-wave filter keep
        # the streak honest while the bot keeps rotating weekly
        self.setup = Setup(
            anchor_idx=a["idx"], sweep_low=a["sweep_low"],
            bos_idx=bos["idx"], bos_red=bos["red"],
            wave_low=bos["wave_low"], green=g, yellow=y,
            entry=entry, stop=stop, risk=risk,
            gate_idx=max(bos["idx"], y.start_idx, g.start_idx),
            wall=wall_s,
            purple_mid=purple.mid if purple is not None else float("nan"))
        self.state = "WAIT_RETRACE"
        self.cnt("setup_drawn")

    # ---------------- FIX4: trail source ---------------------------- #
    def trail_blues(self, cv, include_exec=False):
        if TRAIL_MODE == "structural":
            return cv.structural_blues()
        return cv.active_blues()

    # ---------------- nested target ladder (FIX2/FIX4) -------------- #
    def _red_ladder(self, entry_px: float, risk: float):
        """T1..T3 = HTF RedBox_BSL above entry whose first rung clears
        the net +3R line. Returns (ladder, gate_ok)."""
        lock = ((entry_px * (1 + FEE) + MIN_R * risk) / (1 - FEE))
        seen = set()
        reds = []
        for r in (self.htf_canvas.active_reds()
                  + self.struct_canvas.active_reds()):
            if r.y_bottom > entry_px and id(r) not in seen:
                seen.add(id(r))
                reds.append(r)
        reds.sort(key=lambda r: r.y_bottom)
        # FIX4: T1 is the FIRST red box that already clears the net
        # +3R line (nearer reds are skipped, not vetoes); no such box
        # means the move has no magnet worth taking
        ladder = [r for r in reds if r.y_bottom >= lock][:3]
        if not ladder:
            return [], False
        return ladder, True

    # ---------------- State 4: confirmation entry (FIX1) ------------ #
    def _seek_fill(self, o, h, l, c, idx, time, fresh=()):
        s = self.setup
        if s is None:
            self.state = "WAIT_ANCHOR"
            return
        if idx <= s.gate_idx:                # ZERO-LOOKAHEAD gate
            return
        # no-chase: expansion broke a red box above us while we waited
        # -> this wave already ran; back to the drawing board
        if fresh and c > s.entry:
            self.setup = None
            self.state = "WAIT_ANCHOR"
            self.cnt("setup_missed_run")
            return
        if s.green.state != "ACTIVE" or s.yellow.state != "ACTIVE":
            self.setup = None
            self.state = "WAIT_ANCHOR"
            self.cnt("setup_box_died")
            return
        if c < s.green.y_bottom:             # one-touch mitigation dead
            self.setup = None
            self.state = "WAIT_ANCHOR"
            self.cnt("setup_mitigated")
            return
        # ---- STAGE 2: the confirmation already printed on an earlier
        # bar, so a limit buy now rests at the seam. It fills only on a
        # LATER bar that trades back down to it (zero-lookahead: the
        # order is placed after the confirming close, never at a price
        # that already happened inside the confirming bar).
        # v24-run2 proof: filling at the confirmation CLOSE paid 0.73R
        # of chase, lifting median risk 0.517% -> 0.763% and dropping
        # the 2021 win rate from 48% (v23, seam fills) to 7.9%.
        if s.confirm_idx >= 0:
            if idx <= s.confirm_idx:
                return
            if l > s.entry:
                self.cnt("await_seam_retrace")
                return                        # limit not reached yet
            fill_px = s.entry if o >= s.entry else o
            if self.board != "GREEN":
                self.setup = None
                self.state = "WAIT_ANCHOR"
                self.cnt("fill_cancel_board_red")
                return
            if s.green.state != "ACTIVE" or s.yellow.state != "ACTIVE":
                self.setup = None
                self.state = "WAIT_ANCHOR"
                self.cnt("setup_box_died")
                return
            if c < s.green.y_bottom:
                self.setup = None
                self.state = "WAIT_ANCHOR"
                self.cnt("setup_mitigated")
                return
            purple_now = self.struct_canvas.purple
            if purple_now is not None and fill_px > purple_now.mid:
                self.setup = None
                self.state = "WAIT_ANCHOR"
                self.cnt("fill_cancel_premium")
                return
            risk = fill_px - s.stop
            if risk <= FEE * fill_px:
                self.cnt("reject_risk_below_one_fee")
                return
            ladder, ok = self._red_ladder(fill_px, risk)
            if not ok:
                self.cnt("fill_cancel_target_within_3r")
                return
            self.targets = ladder
            self.cnt("fill_at_seam")
            self._enter(s, fill_px, idx, time)
            return
        # ---- FIX1: never blind-limit into a falling candle --------
        # The bar that traded into the zone is remembered, but the
        # FILL only happens on a bar that is itself a rejection: it
        # must sweep the seam on THIS bar and close back above it.
        # (v24-run1 let any later green candle confirm, up to +2R
        # above the seam — that is chasing, and it produced 28 losses
        # against 2 wins in 2021.)
        if l <= s.entry:
            s.touched = True
        if not s.touched:
            return
        if FILL_MODE == "blind":
            # v23 reference: resting limit at the seam, no confirmation
            fill_px = s.entry if o >= s.entry else o
            if self.board != "GREEN":
                self.setup = None; self.state = "WAIT_ANCHOR"
                self.cnt("fill_cancel_board_red"); return
            purple_now = self.struct_canvas.purple
            if purple_now is not None and fill_px > purple_now.mid:
                self.setup = None; self.state = "WAIT_ANCHOR"
                self.cnt("fill_cancel_premium"); return
            risk = fill_px - s.stop
            if risk <= FEE * fill_px:
                self.cnt("reject_risk_below_one_fee"); return
            ladder, ok = self._red_ladder(fill_px, risk)
            if not ok:
                self.cnt("fill_cancel_target_within_3r"); return
            if self.consec_losses >= LOSS_STREAK_RESET + 1:
                be_line = fill_px * (1 + 2 * FEE)
                if c < be_line:
                    self.cnt("tier3_fill_needs_proof"); return
            self.targets = ladder
            self._enter(s, fill_px, idx, time)
            return
        purple = self.struct_canvas.purple
        if purple is not None and c > purple.mid:
            return                            # not in Discount — wait
        # the confirm bar must itself trade into the seam and hold
        # the GreenBox (prompt: "closing > green.y_bottom" — NOT above
        # the box top: requiring c > entry chased the fill up to +2R
        # above the seam, inflating the R denominator so the +3R lock
        # sat 50% further away and only 3 of 48 trades could reach it)
        if l > s.entry:
            self.cnt("confirm_wait")
            return                            # no sweep on this bar
        # reclaim confirmation: body holds the GreenBox, closes back
        # above the seam, and shows a bullish rejection signature
        prev_down_high = None
        if idx >= 1:
            po, ph, pl, pc, _ = self.exec_canvas.bars[idx - 1]
            if pc < po:
                prev_down_high = ph
        sig_sweep = l < min(o, c) and c > (h + l) / 2.0
        sig_break = prev_down_high is not None and c > prev_down_high
        sig_body = c > o and c >= l + 0.5 * (h - l)
        rejection = c > o or sig_break or sig_sweep
        self._confirm_kind = ("sweep" if sig_sweep else
                              "break" if sig_break else
                              "strong_body" if sig_body else "weak_body")
        self._confirm_chase = (c - s.entry) / max(s.risk, 1e-9)
        if not (c > s.green.y_bottom and rejection):
            self.cnt("confirm_wait")
            return
        # FIX3 tier-3: after3 losses the reclaim must already be
        # above the breakeven line so the shield can never raw-lose
        if self.consec_losses >= LOSS_STREAK_RESET + 1:
            if c < s.entry * (1 + 2 * FEE):
                self.cnt("tier3_fill_needs_proof")
                return
        # target ladder must clear net +3R from THIS close (entry =
        # the confirm close itself, per prompt: "ندخل عند إغلاق
        # الشمعة" — the stop distance then equals risk exactly)
        risk = c - s.stop
        if risk <= FEE * c:
            self.cnt("reject_risk_below_one_fee")
            return
        ladder, ok = self._red_ladder(c, risk)
        if not ok:
            self.cnt("reject_target_within_3r")
            return
        s.confirm_idx = idx
        self.cnt("confirm_entry")
        if FILL_MODE == "close":
            self.targets = ladder
            self._enter(s, c, idx, time)
            return

    # ---------------- fill ------------------------------------------ #
    def _enter(self, s: Setup, fill_px, idx, time):
        stop = s.stop
        if fill_px <= stop:
            self.setup = None
            self.state = "WAIT_ANCHOR"
            return
        if sum(1 for e in self.pool.get("engines", []) if e.qty > 0) \
                >= MAX_SLOTS:
            self.setup = None
            self.state = "WAIT_ANCHOR"
            self.cnt("portfolio_slots_full")
            return
        risk = fill_px - stop
        # FIX4: 100% of FREE pool cash goes to work (reserving the
        # round-trip fee) — no more half-idle $100 stacks
        notional = self.pool["cash"] / (1 + FEE)
        qty = notional / fill_px
        notional = qty * fill_px
        if qty <= 0 or notional < EXCHANGE_MIN_NOTIONAL:
            self.setup = None
            self.state = "WAIT_ANCHOR"
            self.cnt("fill_below_exchange_min")
            return
        fee = notional * FEE
        if fee + notional > self.pool["cash"] + 1e-9:
            self.setup = None
            self.state = "WAIT_ANCHOR"
            return
        self.qty = qty
        self.entry_px = fill_px
        self.stop_px = stop
        self.risk = risk
        self.ratchet = False
        self.mfe = 0.0                 # max favourable excursion, in R
        self.mfe_close = 0.0           # same, measured on CLOSES only
        self.t1_hit = False            # FIX4: T1 reached -> trail arm
        self.qty0 = qty
        # L4 shield: trade opened with an active2-loss streak arms
        # breakeven early (exception to the no-move-before-3R law)
        self.shield = self.consec_losses >= LOSS_STREAK_RESET
        self.be_armed = False
        self._be_at_entry = False
        # FIX3 (prompt): "BE shield guards so no 4th loss is ever
        # recorded" — at3 straight losses the entry bar already closed
        # above the breakeven line (tier-3 proof), so the BE stop is
        # armed IMMEDIATELY; the worst outcome of trade #4 is a scratch
        if self.consec_losses >= LOSS_STREAK_RESET + 1:
            be = fill_px * (1 + 2 * FEE)
            if be < fill_px + risk:      # keep the stop a real stop
                self.stop_px = max(self.stop_px, be)
                self.be_armed = True
                self._be_at_entry = True
                self.cnt("tier3_be_armed_at_entry")
        # exact solution of px - entry - FEE*entry - FEE*px >= 3*risk
        # (exit fee scales with the HIGHER exit price — v22 run-1 lost
        # 68 near-3R winners to a0.004R fee shortfall)
        self.lock_line = ((fill_px * (1 + FEE) + MIN_R * risk)
                          / (1 - FEE))
        self.protected_blue = s.wave_low
        self.pool["cash"] -= notional + fee
        self.fees += fee
        self.state = "IN_POS"
        self.trade = {
            "symbol": self.symbol,
            "entry_time": str(time),
            "entry_idx": idx,
            "entry_price": fill_px,
            "stop_price": stop,
            "risk_pct": risk / fill_px * 100.0,
            "notional": notional,
            "qty0": qty,
            "realized": 0.0,
            "released_qty": 0.0,
            "s1_anchor": f"@{s.anchor_idx} sweep_low={s.sweep_low:.2f}",
            "broken_red": s.bos_red.as_dict(),
            "wave_low_blue": s.wave_low.as_dict(),
            "yellow": s.yellow.as_dict(),
            "green": s.green.as_dict(),
            "purple_mid": round(s.purple_mid, 2),
            "wall": s.wall.as_dict() if s.wall else None,
            "entry_line": round(s.entry, 2),
            "setup_completion_idx": s.gate_idx,
            "bos_idx": s.bos_idx,
            "entry_fee": fee,
            "s1_kind": "BOX_STACK",
            "shield": self.shield,
            "exec_tf": self.exec_tf,
            "targets": [b.as_dict() for b in self.targets],
            "confirm_idx": s.confirm_idx,
            "mfe_R": 0.0,
            "be_at_entry": getattr(self, "_be_at_entry", False),
            "be_source": "",
            "mfe_close_R": 0.0,
            "confirm_kind": getattr(self, "_confirm_kind", "?"),
            "confirm_chase_R": round(getattr(self, "_confirm_chase", 0.0), 2),
            "n_targets": len(self.targets),
        }
        self.cnt("fill")

    # ---------------- in-position management ------------------------ #
    def _release_locked_capital(self, lock_px):
        """FIX4 (risk-free pyramiding): at the first +3R close, sell
        back the initial notional at the lock price. The freed cash
        returns to the pool (100% rotation into the next structure)
        and the remaining qty rides with ZERO cost basis — both legs
        together can never net below +3.0R (same price, same fees)."""
        t = self.trade
        if t is None or self.qty <= 0:
            return
        qty0 = t.get("qty0", self.qty)
        rel = t.get("notional", 0.0) / lock_px
        if rel <= 0 or rel >= self.qty:
            return
        fee = rel * lock_px * FEE
        realized = (lock_px - self.entry_px) * rel - fee
        t["realized"] = t.get("realized", 0.0) + realized
        t["released_qty"] = t.get("released_qty", 0.0) + rel
        self.pool["cash"] += rel * lock_px - fee
        self.fees += fee
        self.qty -= rel
        self.cnt("capital_released_at_lock")

    def _exit(self, px, reason, idx, time):
        t = self.trade
        gross = (px - self.entry_px) * self.qty
        exit_fee = px * self.qty * FEE
        entry_fee = t.get("entry_fee", 0.0)
        net = gross - entry_fee - exit_fee + t.get("realized", 0.0)
        R = (net / (self.risk * t.get("qty0", self.qty))
             if self.risk > 0 else 0.0)
        # ---- classification (L1: winners are >= +3.0R, always) ----
        is_win = net > 0 and R >= MIN_R - 1e-9
        is_be = (not is_win) and (self.shield or net > 0) and R >= -0.05
        if is_be:
            reason = "BREAKEVEN"
        t["mfe_R"] = round(self.mfe, 2)
        t["mfe_close_R"] = round(self.mfe_close, 2)
        t.update({"exit_time": str(time), "exit_idx": idx,
                  "exit_price": px, "exit_reason": reason,
                  "net_pnl": net, "R": R, "bars_held": idx - t["entry_idx"],
                  "class": "WIN" if is_win else
                           ("BE" if is_be else "LOSS")})
        # position sold: proceeds back to shared pool cash
        self.pool["cash"] += px * self.qty - exit_fee
        self.trades.append(t)
        self.qty = 0.0
        self.trade = None
        self.ratchet = False
        self.shield = False
        self.be_armed = False
        self.state = "WAIT_ANCHOR"
        self.setup = None
        self.anchor = None
        self.bos = None
        self.cnt("exit_" + reason)
        # ---- L4 bookkeeping ---------------------------------------
        purple = self.struct_canvas.purple
        rng = (purple.y_bottom, purple.y_top) if purple is not None else None
        if is_win:
            self.consec_losses = 0
            self.locked_range = None
            self.breaker_ready = False
            self.blocked_after_losses = False
        elif is_be:
            # not a loss, not a win. The dealing range stays consumed
            # (prompt: "يُعاد قفل النطاق"), but the STREAK GATE IS
            # RELEASED: v24-run4 proof — holding the streak on a scratch
            # trapped the bot in permanent tier-3 (54 trades armed with
            # a BE stop at entry, 50 of them scratched, up to 13 in a
            # row), which starved both the win rate and 2023-2025.
            # Safety is unchanged: at consec==3 the next trade is still
            # BE-armed, so it cannot be a 4th LOSS — it scratches or
            # wins, and either outcome resets the count to zero.
            if rng is not None:
                self.consumed.append(rng)
            if BE_RELEASES_STREAK:
                self.consec_losses = 0
                self.blocked_after_losses = False
                self.cnt("shield_be_releases_streak")
            else:
                self.cnt("shield_be_holds_streak")
        else:
            self.consec_losses += 1
            self.last_loss_idx = idx
            self.last_loss_time = time
            if rng is not None:
                self.consumed.append(rng)   # one loss per range
            if self.consec_losses >= LOSS_STREAK_RESET:
                self.blocked_after_losses = True
                self.cnt("structural_gate_armed")
        self.targets = []

    def _manage(self, o, h, l, c, idx, time):
        t = self.trade
        if self.risk > 0:
            self.mfe = max(self.mfe, (h - self.entry_px) / self.risk)
            self.mfe_close = max(self.mfe_close,
                                 (c - self.entry_px) / self.risk)
        lock_line = self.lock_line   # entry + 3R + fees (net >= +3.0R)
        # wick stop (structural pre-ratchet, or an above-floor trail)
        floor_only = (self.ratchet
                      and self.stop_px <= lock_line + 1e-9)
        if not floor_only and l <= self.stop_px:
            px = self.stop_px if o >= self.stop_px else o
            self._exit(px, "STOP_BLUE", idx, time)
            return
        # ---- L4 shield (FIX3): streak trades arm early; any trade
        # may arm through path-B (two-thirds to lock + RedBox break
        # + failure under a post-entry sub-blue)
        if not self.be_armed and (self.shield or BE_ARM != "shield_only"):
            half = self.entry_px + (MIN_R / 2) * self.risk
            broke_red = any(e["idx"] >= t["entry_idx"]
                            for e in self.fresh_qualified)
            be = self.entry_px * (1 + 2 * FEE)       # entry + fees
            two_thirds = (self.entry_px
                          + (2.0 / 3.0) * (lock_line - self.entry_px))
            cvx = self.exec_canvas
            subs = [b.y_bottom for b in cvx.active_blues()
                    if b.start_idx > t["entry_idx"]
                    and b.y_bottom > self.entry_px]
            sub = max(subs) if subs else None
            path_b = (c >= two_thirds and broke_red
                      and sub is not None and c < sub)
            # v24: the bare "close above BE" arm fired at +0.4R on
            # compact LTF risk and strangled trades at 0.00R; it now
            # needs a real excursion (half-way to3R) or a RedBox break
            early = (self.consec_losses >= LOSS_STREAK_RESET
                     and h >= half and (broke_red or c >= be))
            if BE_ARM == "all_at_half":
                early = early or (h >= half and c >= be)
            elif BE_ARM == "all_at_be":
                early = early or c >= be
            # arm only when the close proves ABOVE the BE line so the
            # stop always sits below the market (valid stop semantics)
            if (path_b or early) and c > be:
                self.stop_px = be
                self.be_armed = True
                self.cnt("shield_be_path_b" if path_b
                         else "shield_be_armed")
                t["be_source"] = ("path_b" if path_b else
                                  "tier3_entry" if t.get("be_at_entry")
                                  else BE_ARM)
        # ---- RUNNER arm: first CLOSE >= +3R locks the floor ------- #
        if not self.ratchet and c >= lock_line:
            self.ratchet = True
            self.stop_px = max(self.stop_px, lock_line)
            self.cnt("ratchet_3r_close")
            # FIX4 (v24): the +3R lock is a STOP FLOOR, not a market
            # sell. The v22/v23 "release locked capital" step sold
            # notional/lock ≈ 98.7% of the position at exactly +3R and
            # left 1.3% riding — which is why a 2021-07-30 15m trade
            # that ran to +22.8R on closes was booked at 3.23R. That
            # single line WAS the "3.00R massacre".
        elif self.ratchet and lock_line > self.stop_px:
            self.stop_px = lock_line
        floor_only = (self.ratchet
                      and self.stop_px <= lock_line + 1e-9)
        if floor_only and c <= lock_line:
            # body-close rule (a): candle closes back under the floor
            px = lock_line if o >= lock_line else o
            self._exit(px, "LOCK_FLOOR_CLOSE", idx, time)
            return
        # ---- FIX4: exit AT the red target on a rejection candle ---
        # (any trail stop above the floor already fired on its wick,
        # so a close reaching this branch is above the trail too)
        if self.ratchet and self.targets:
            for T in list(self.targets):
                if h < T.y_bottom:
                    break                   # ladder sorted ascending
                self.t1_hit = True          # first rung reached
                if c < o and c <= T.y_top:  # bearish close inside box
                    self.cnt("target_rejection_exit")
                    self._exit(c, "TARGET_REJECTION", idx, time)
                    return
                # traded THROUGH the box — consumed, aim higher
                self.targets.remove(T)
                self.cnt("target_consumed")
        # ---- FIX4: once the +3R lock is on, the ride continues with
        # the stop trailing ascending HTF BlueBox bottoms ABOVE the
        # lock (1H lens for the LTF snipers,4H board for the1h engine).
        # v24-run3 proof: gating the trail behind T1 left it dead on
        # every runner (T1 often sits beyond the whole move), so a
        # 27.9R excursion was walked all the way back and exited at
        # 3.13R. The prompt says "through 3R/T1" — whichever is first.
        if self.ratchet:
            best = self.stop_px
            srcs = [self.htf_canvas, self.struct_canvas]
            if TRAIL_MODE == "all_active":
                srcs.append(self.exec_canvas)
            for cv in srcs:
                for b in self.trail_blues(cv):
                    if (b.y_bottom >= self.lock_line
                            and self.stop_px < b.y_bottom < self.price):
                        best = max(best, b.y_bottom)
            if best > self.stop_px:
                self.stop_px = best
                self.cnt("trail_htf_blue")
        # (exec-frame trail REMOVED: the4H structural trail in
        # on_struct — "أو4H" — governs rides)
        # ---- top-sell: only allowed at/above the lock line -------
        # (keeps every winner >= +3.0R by construction)
        if self.ratchet and c >= lock_line:
            cv = self.exec_canvas
            blues = cv.active_blues()
            if blues:
                last_blue = blues[-1]
                if c < last_blue.y_bottom and any(
                        y.start_idx >= last_blue.start_idx
                        for y in cv.active_yellow_s()):
                    self._exit(c, "REVERSAL_CHoch", idx, time)
                    return

    # --------------------------------------------------------------- #
    def portfolio_equity(self, price=None):
        eq = self.pool["cash"]
        for e in self.pool.get("engines", []):
            if e.qty > 0:
                p = price if (e is self and price is not None) else e.price
                eq += e.qty * p
        return eq

    def equity(self, price=None):
        return self.portfolio_equity(price)


# ==================================================================== #
# Portfolio runner (multi-coin ready; data currently holds BTC only)
# ==================================================================== #
def discover_symbols(data_dir: Path) -> list[str]:
    # FIX4: crypto spot only — XAUUSD (metal, sub-fee risk on1m) and
    # index dirs are excluded by the whitelist
    return sorted(p.name for p in data_dir.iterdir()
                  if p.is_dir() and p.name.startswith(CRYPTO_ONLY))


def _stems_for(d: Path, warm, s1) -> list[str]:
    """Yearly (YYYY) or monthly (YYYY-MM) archives."""
    names = [f.name for f in d.glob("*.csv.gz")]
    if any(n.count("-") == 0 for n in names):
        return [str(y) for y in range(warm.year, s1.year + 1)]
    return [f"{y}-{m:02d}" for y in range(warm.year, s1.year + 1)
            for m in range(1, 13)]


def run_backtest(data_dir: Path, start: str, end: str,
                 warmup_days: int = 60, tag: str = ""):
    from engine.causal_primitives import load_asset_ohlcv, resample_causal_tf
    s0 = pd.Timestamp(start).tz_localize("UTC")
    s1 = pd.Timestamp(end).tz_localize("UTC")
    warm = s0 - pd.Timedelta(days=warmup_days)
    symbols = discover_symbols(data_dir)
    # ONE shared portfolio pool across all coins and both engines
    pool = {"cash": CAPITAL, "engines": []}
    engines = []
    series = {}
    for sym in symbols:
        df = load_asset_ohlcv(data_dir / sym,
                              include_stems=_stems_for(data_dir / sym,
                                                       warm, s1))
        tf_5 = resample_causal_tf(df, "5min")
        tf_15 = resample_causal_tf(df, "15min")
        tf_30 = resample_causal_tf(df, "30min")
        tf_60 = resample_causal_tf(df, "1h")
        tf_4h = resample_causal_tf(df, STRUCT_TF)
        for tf in (tf_5, tf_15, tf_30, tf_60, tf_4h):
            tf.drop(index=tf[tf.index > s1].index, inplace=True)
        tf_5 = tf_5[tf_5.index >= warm]
        tf_15 = tf_15[tf_15.index >= warm]
        tf_30 = tf_30[tf_30.index >= warm]
        tf_60 = tf_60[tf_60.index >= warm]
        tf_4h = tf_4h[tf_4h.index >= warm]
        series[sym] = (tf_5, tf_15, tf_30, tf_60, tf_4h)
        # FIX2: LTF sniper engines (5m/15m) + swing engine (1h), all
        # watching the same4H board and the same1H target ladder
        for exec_tf in EXEC_FRAMES:
            e = ICTBoxEngine(sym, exec_tf=exec_tf, tag=tag)
            e.pool = pool
            engines.append(e)
    pool["engines"] = engines
    # pointers per (sym, stream) —4H and1H need backfill
    ptr = {(sym, s): 0 for sym in symbols for s in ("4h", "60")}
    eq_rows = []
    # global timeline = union of all exec frames (finest first)
    stamps = sorted(set().union(*[
        set(series[s][0].index) | set(series[s][1].index)
        | set(series[s][2].index)
        for s in symbols]))
    for t in stamps:
        for sym in symbols:
            tf_5, tf_15, tf_30, tf_60, tf_4h = series[sym]
            # feed completed 4H bars up to t (causal: <= t)
            while (ptr[(sym, "4h")] < len(tf_4h)
                   and tf_4h.index[ptr[(sym, "4h")]] <= t):
                j = ptr[(sym, "4h")]
                if tf_4h.index[j] >= warm:
                    r = tf_4h.iloc[j]
                    vol = float(r.Volume) if "Volume" in r else 0.0
                    for e in engines:
                        if e.symbol != sym:
                            continue
                        if t >= s0:
                            e.warm = False
                        e.on_struct(float(r.Open), float(r.High),
                                    float(r.Low), float(r.Close),
                                    vol, len(e.struct_canvas.bars),
                                    tf_4h.index[j])
                ptr[(sym, "4h")] += 1
            # feed completed1H bars up to t — the shared target lens
            while (ptr[(sym, "60")] < len(tf_60)
                   and tf_60.index[ptr[(sym, "60")]] <= t):
                j = ptr[(sym, "60")]
                if tf_60.index[j] >= warm:
                    r = tf_60.iloc[j]
                    vol = float(r.Volume) if "Volume" in r else 0.0
                    for e in engines:
                        if e.symbol != sym:
                            continue
                        e.on_htf(float(r.Open), float(r.High),
                                 float(r.Low), float(r.Close),
                                 vol, len(e.htf_canvas.bars),
                                 tf_60.index[j])
                ptr[(sym, "60")] += 1
            # feed each exec engine at its own completed stamps
            for tf_lbl, tf in (("5min", tf_5), ("15min", tf_15),
                               ("30min", tf_30), ("1h", tf_60)):
                if tf_lbl not in EXEC_FRAMES:
                    continue
                if t in tf.index:
                    r = tf.loc[t]
                    vol = float(r.Volume) if "Volume" in r else 0.0
                    for e in engines:
                        if e.symbol == sym and e.exec_tf == tf_lbl:
                            if t >= s0:
                                e.warm = False
                            e.on_exec(float(r.Open), float(r.High),
                                      float(r.Low), float(r.Close), vol,
                                      len(e.exec_canvas.bars), t)
        if t >= s0:
            eq_rows.append((t, pool["cash"] + sum(
                e.qty * e.price for e in engines if e.qty > 0)))
    # mark-to-market close (reporting only)
    out_trades = []
    for eng in engines:
        if eng.qty > 0:
            eng._exit(eng.price, "END_OF_DATA",
                      len(eng.exec_canvas.bars), eng.now)
        out_trades.extend(eng.trades)
    out_trades.sort(key=lambda t: str(t["entry_time"]))
    counts = {}
    for eng in engines:
        for k, v in eng.count.items():
            counts[k] = counts.get(k, 0) + v
        for (y, k), v in eng.yearly.items():
            counts[f"y{y}_{k}"] = counts.get(f"y{y}_{k}", 0) + v
    yearly = {}
    for t in out_trades:
        y = str(t["entry_time"])[:4]
        yearly[y] = yearly.get(y, 0) + 1
    fees = sum(eng.fees for eng in engines)
    eq = (pd.DataFrame(eq_rows, columns=["time", "equity"])
          .set_index("time") if eq_rows else pd.DataFrame())
    return {"trades": out_trades, "equity": eq, "count": counts,
            "fees": fees, "symbols": symbols, "pool_cash_end": pool["cash"],
            "yearly": yearly}


# ==================================================================== #
# Reporting
# ==================================================================== #
def summarize(run, capital=CAPITAL):
    tr = run["trades"]
    n = len(tr)
    # L1 classification: winners are >= +3.0R by construction; shield
    # breakevens are neither winners nor losses
    wins = [t for t in tr if t.get("class") == "WIN"
            or (t["net_pnl"] > 0 and t["R"] >= MIN_R - 1e-9)]
    bes = [t for t in tr if t.get("class") == "BE"]
    losses = [t for t in tr if t.get("class") == "LOSS"
              or (t["net_pnl"] <= 0 and t.get("class") != "BE")]
    assert all(t["R"] >= MIN_R - 1e-9 for t in wins), \
        "L1 VIOLATION: a winner below +3.0R exists!"
    gp = sum(t["net_pnl"] for t in wins)
    gl = -sum(t["net_pnl"] for t in losses)
    rs = [t["R"] for t in tr]
    eq = run["equity"]
    end_eq = float(eq["equity"].iloc[-1]) if len(eq) else capital
    peak = eq["equity"].cummax() if len(eq) else None
    dd = float(((eq["equity"] - peak) / peak * 100).min()) if len(eq) else 0.0
    # consecutive TRUE losses (breakevens do not extend the streak)
    streak = best = 0
    for t in tr:
        if t.get("class") == "LOSS" or (
                t["net_pnl"] <= 0 and t.get("class") != "BE"):
            streak += 1
            best = max(best, streak)
        else:
            streak = 0
    # prompt law: max consecutive LOSSES <= 3 — enforced by the
    # five-assert block at the end of main() (which must see ALL
    # artifacts), so here we only flag it loudly
    if best > 3:
        print(f"!! L4 VIOLATION: streak of {best} losses > 3")
    # monthly from equity
    monthly = []
    if len(eq):
        me = eq["equity"].resample("ME").last()
        prev = capital
        for ts, v in me.items():
            monthly.append([ts.strftime("%Y-%m"),
                            round((v - prev) / prev * 100, 2)])
            prev = v
    return {
        "trades": n, "wins": len(wins), "breakevens": len(bes),
        "win_rate_pct": round(
            len(wins) / max(len(wins) + len(losses), 1) * 100, 1),
        "profit_factor": round(gp / gl, 2) if gl > 0 else None,
        "net_pnl": round(end_eq - capital, 2),
        "net_pct": round((end_eq - capital) / capital * 100, 2),
        "end_equity": round(end_eq, 2),
        "max_drawdown_pct": round(dd, 2),
        "max_consecutive_losses": best,
        "avg_R": round(float(np.mean(rs)), 2) if rs else 0.0,
        "min_winner_R": round(min([t["R"] for t in wins]), 2) if wins else None,
        "runners_ge_5R": sum(1 for t in wins if t["R"] >= 5),
        "runners_ge_10R": sum(1 for t in wins if t["R"] >= 10),
        "runners_ge_20R": sum(1 for t in wins if t["R"] >= 20),
        "runners_4r_plus": sum(1 for t in wins if t["R"] >= 4 - 1e-9),
        "max_winner_R": round(max(t["R"] for t in wins), 2)
                        if wins else None,
        "max_R": round(max(rs), 2) if rs else None,
        "fees": round(run["fees"], 2),
        "exit_reasons": _hist(t["exit_reason"] for t in tr),
        "s1_kinds": _hist(t.get("s1_kind", "-") for t in tr),
        "monthly": monthly,
        "count": run["count"],
        "symbols": run["symbols"],
        "yearly": run.get("yearly", {}),
    }


def _hist(it):
    out = {}
    for k in it:
        out[k] = out.get(k, 0) + 1
    return out


def anatomy_table(trades, n=10):
    rows = []
    for t in trades[:n]:
        rows.append({
            "entry_time": t["entry_time"],
            "purple_mid": t["purple_mid"],
            "broken_red": t["broken_red"],
            "yellow": t["yellow"],
            "green": t["green"],
            "stop_blue": t["wave_low_blue"],
            "entry": t["entry_price"],
            "stop": t["stop_price"],
            "wall": t["wall"],
            "exit_reason": t["exit_reason"],
            "R": round(t["R"], 2),
        })
    return rows


def bull_stats(run):
    tr = run["trades"]
    rs = [t["R"] for t in tr]
    return {
        "trades": len(tr),
        "wins_ge_3R": sum(1 for r in rs if r >= MIN_R - 1e-9),
        "runners_ge_5R": sum(1 for r in rs if r >= 5),
        "runners_ge_10R": sum(1 for r in rs if r >= 10),
        "runners_ge_20R": sum(1 for r in rs if r >= 20),
        "max_R": round(max(rs), 2) if rs else 0,
        "count": run["count"],
    }


def ascii_diagram(t: dict) -> str:
    """Vertical price-axis box diagram for one trade (top -> bottom)."""
    def line(label, box, note=""):
        if box is None:
            return f"  [    ] {label:<34} (none) {note}"
        return (f"  [{box['kind']:<6}] {label:<34} "
                f"Top:{box['top']:>10.2f} | Bottom:{box['bottom']:>10.2f} {note}")
    risk = t["entry_price"] - t["stop_price"]
    tgt = t["entry_price"] + MIN_R * risk
    out = []
    out.append(f"  ENTRY {t['entry_time']}  R={t['R']:+.2f} "
               f"({t['exit_reason']})")
    if t.get("wall"):
        out.append(line("4H Red/Yellow wall (target ceiling)",
                        {"kind": "WALL", **t["wall"]}))
    else:
        out.append("  [ open sky ] no bearish wall above entry "
                   "(ATH expansion)")
    out.append(f"  [ 3R line ] Target = entry + 3 x Risk"
               f"          Price:{tgt:>10.2f}")
    out.append(line("broken RedBox_BSL (BOS)", t["broken_red"],
                    "<-- broken by body close"))
    out.append(f"  [ PURPLE ] Dealing-range mid (50%)"
               f"           Price:{t['purple_mid']:>10.2f}"
               f"   (above=Premium, below=Discount)")
    out.append(line("YellowBox_BullFVG (entry line=Top)", t["yellow"]))
    out.append(line("GreenBox_BullOB (under yellow)", t["green"]))
    out.append(line("BlueBox wave low / Stop line", t["wave_low_blue"],
                    f"<-- Stop:{t['stop_price']:.2f}"))
    return "\n".join(out)


# ==================================================================== #
# main
# ==================================================================== #
def main():
    RESULTS.mkdir(exist_ok=True)
    print(f"[v24-boxes] symbols discovered: "
          f"{discover_symbols(DATA_DIR)}")
    run = run_backtest(DATA_DIR, FULL_START, FULL_END)
    # PERSIST FIRST — a later assert must never destroy the evidence
    pd.DataFrame(run["trades"]).to_csv(RESULTS / "trades_v24.csv",
                                       index=False)
    print("yearly fills:", json.dumps(run["yearly"], indent=2))
    print("funnel:", json.dumps(run["count"], indent=2))
    s = summarize(run)
    print(json.dumps({k: v for k, v in s.items()
                      if k not in ("monthly", "count")}, indent=2))
    print("funnel:", json.dumps(s["count"], indent=2))
    print("yearly fills:", json.dumps(run["yearly"], indent=2))
    pd.DataFrame(run["trades"]).to_csv(RESULTS / "trades_v24.csv",
                                       index=False)
    pd.DataFrame(s["monthly"], columns=["month",
                                        "ret_pct"]).to_csv(
        RESULTS / "monthly_v24.csv", index=False)
    if len(run["equity"]):
        run["equity"].to_csv(RESULTS / "equity_v24.csv")
    with open(RESULTS / "summary_v24.json", "w") as f:
        json.dump(s, f, indent=2, default=str)
    # anatomy + diagrams
    ana = anatomy_table(run["trades"], 10)
    with open(RESULTS / "anatomy_v24.json", "w") as f:
        json.dump(ana, f, indent=2)
    print("\n=== SECTION 2: ANATOMY (first 10) ===")
    for row in ana:
        print(row)
    print("\n=== ASCII DIAGRAMS (first 3) ===")
    for t in run["trades"][:3]:
        print(ascii_diagram(t))
        print()
    # bull window (tagged counters)
    bull = run_backtest(DATA_DIR, BULL_START, BULL_END, tag="BULL")
    bs = bull_stats(bull)
    print("\n[v24-boxes] BULL RUN", BULL_START, "..", BULL_END)
    print(json.dumps(bs, indent=2))
    pd.DataFrame(bull["trades"]).to_csv(RESULTS / "trades_v24_bull.csv",
                                        index=False)
    with open(RESULTS / "bull_v24.json", "w") as f:
        json.dump(bs, f, indent=2, default=str)
    # ================= THE FIVE MANDATORY ASSERTS ==================
    # (all five checked on the SAME full run, after artifacts persist)
    tr = run["trades"]
    wins = [t for t in tr if t.get("class") == "WIN"
            or (t["net_pnl"] > 0 and t["R"] >= MIN_R - 1e-9)]
    losses = [t for t in tr if t.get("class") == "LOSS"
              or (t["net_pnl"] <= 0 and t.get("class") != "BE")]
    decided = len(wins) + len(losses)
    win_rate = len(wins) / decided if decided else 0.0
    min_winner_r = min((t["R"] for t in wins), default=0.0)
    runners_4r = sum(1 for t in wins if t["R"] >= 4 - 1e-9)
    max_winner_r = max((t["R"] for t in wins), default=0.0)
    max_consec = s["max_consecutive_losses"]
    total = len(tr)
    yearly = {str(k): v for k, v in run["yearly"].items()}

    checks = [
        (1, "WR >= 60%", win_rate >= 0.60,
         f"{win_rate:.2%} ({len(wins)}W/{len(losses)}L)"),
        (2, "min_winner_R >= 3.00", min_winner_r >= 3.00 - 1e-6,
         f"{min_winner_r:.2f}R"),
        (3, "runners_4r_plus >= 5 AND max_winner_R >= 6.0",
         runners_4r >= 5 and max_winner_r >= 6.0,
         f">=4R:{runners_4r} max:{max_winner_r:.2f}R"),
        (4, "max_consecutive_losses <= 3", max_consec <= 3,
         f"{max_consec}"),
        (5, "total >= 180 AND yearly[y] >= 15 for 2021..2025",
         total >= 180 and all(yearly.get(str(y), 0) >= 15
                              for y in (2021, 2022, 2023, 2024, 2025)),
         f"total:{total} yearly:{yearly}"),
    ]
    print("\n============ THE FIVE MANDATORY ASSERTS ============")
    failed = []
    for n, label, ok, detail in checks:
        print(f"[v24] ASSERT{n} {'PASSED' if ok else 'FAILED'} :: "
              f"{label} :: {detail}")
        if not ok:
            failed.append(n)
    with open(RESULTS / "asserts_v24.json", "w") as f:
        json.dump([{"assert": n, "rule": lab, "passed": bool(ok),
                    "observed": det} for n, lab, ok, det in checks],
                  f, indent=2)
    if failed:
        raise AssertionError(
            f"v24 DID NOT PASS asserts {failed} — see asserts_v24.json")
    print("[v24] ALL FIVE ASSERTS PASSED")


if __name__ == "__main__":
    main()
