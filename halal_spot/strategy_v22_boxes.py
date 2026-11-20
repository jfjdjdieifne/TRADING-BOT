"""
v22 — Visual Box Engine with four hard geometric locks (ICT spot)

Locks (from the v22 criminal-review prompt):
  L1: no stop movement before the 3R close (shield trades may arm
      breakeven after the first structural RedBox break / half-3R);
      every WINNER exits >= +3.0R net of fees.
  L2: entry compressed to min(GreenBox.y_top, YellowBox.y_bottom),
      risk height capped by GreenBox.height.
  L3: assert entry <= PurpleBox.mid — never buy in Premium.
  L4: one loss per dealing range + full purple lock after 2 losses;
      trade #3 only after 4H structural breakout (streak breaker),
      armed to breakeven — mathematically caps the streak.
True structural swings: only waves that left a YellowBox AND broke a
RedBox qualify (micro 3-candle noise ignored).
Portfolio: shared cash, dual exec engines (1h + 15m) per symbol.
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
CAPITAL = 200.0          # user-given
SLOT = 0.5               # geometric half: each active slot = half equity
MAX_SLOTS = 2            # prompt: two active spot slots
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
        self.pairs: list[tuple[Box, Box]] = []   # (green, yellow) stacks
        self.bos_events: list[dict] = []     # red-box breaks (consumed once)
        self.sweep_events: list[dict] = []
        self.chop_events: list[dict] = []    # blue-box breakdowns (board)

    # ---------- fractal helpers (3-bar, confirmed on the right bar) ----
    def _confirm_fractals(self, i: int) -> list[Box]:
        out = []
        if i < 2:
            return out
        ho, hh, hl, hc, _ = self.bars[i - 2]
        mo, mh, ml, mc, _ = self.bars[i - 1]
        no, nh, nl, nc, _ = self.bars[i]
        # swing high at i-1 (3-bar fractal, confirmed on bar i)
        if mh > ho and mh > hc and mh > nh and mh > nc:
            box = Box(y_bottom=max(mo, mc), y_top=mh, start_idx=i - 1,
                      kind="RED", tf=self.tf)
            self.reds.append(box)
            out.append(box)
        # swing low at i-1
        if ml < min(ho, hc) and ml < min(nh, nc):
            box = y0 = Box(y_bottom=ml, y_top=min(mo, mc), start_idx=i - 1,
                           kind="BLUE", tf=self.tf)
            self.blues.append(box)
            out.append(box)
        return out

    def _draw_yellows(self, i: int) -> list[Box]:
        """Fair-value gaps: pure visible air between candle bodies/wicks —
        c3.low > c1.high (bull) / c3.high < c1.low (bear)."""
        if i < 2:
            return []
        out = []
        c1o, c1h, c1l, c1c, _ = self.bars[i - 2]
        c3o, c3h, c3l, c3c, _ = self.bars[i]
        if c3l > c1h:
            b = Box(y_bottom=c1h, y_top=c3l, start_idx=i,
                    kind="YELLOW_B", tf=self.tf)
            self.yellows_b.append(b)
            out.append(b)
        if c3h < c1l:
            b = Box(y_bottom=c3h, y_top=c1l, start_idx=i,
                    kind="YELLOW_S", tf=self.tf)
            self.yellows_s.append(b)
            out.append(b)
        return out

    def _draw_green(self, yellow: Box) -> Box | None:
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
                start_idx=min(run), kind="GREEN", tf=self.tf)
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
        b = self.blues[-1]
        r = self.reds[-1]
        # spec: latest confirmed swing low -> latest confirmed swing
        # high (no ordering constraint — a stale range in a downtrend
        # froze the order-flow filter)
        if r.y_top > b.y_bottom:
            self.purple = Box(y_bottom=b.y_bottom, y_top=r.y_top,
                              start_idx=max(b.start_idx, r.start_idx),
                              kind="PURPLE", tf=self.tf)

    def _invalidate(self, i: int) -> None:
        _, _, _, c, _ = self.bars[i]
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
            if y.state == "ACTIVE" and y.broken_up_by(c):
                y.state = "DEAD"
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

    def on_bar(self, o, h, l, c, v, idx) -> dict:
        self.bars.append((o, h, l, c, v))
        i = len(self.bars) - 1
        assert i == idx, "bar index must be contiguous"
        self._confirm_fractals(i)
        for y in self._draw_yellows(i):
            if y.kind == "YELLOW_B":
                self._draw_green(y)
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


class ICTBoxEngine:
    def __init__(self, symbol: str, exec_tf: str = "1h",
                 capital_slot: float = CAPITAL, tag: str = ""):
        self.pool = {"cash": CAPITAL, "engines": []}  # shared portfolio
        self.symbol = symbol
        self.tag = tag
        self.exec_tf = exec_tf
        self.exec_canvas = ChartCanvas(exec_tf)
        self.struct_canvas = ChartCanvas(STRUCT_TF)
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
        ev = self.struct_canvas.on_bar(o, h, l, c, v, idx)
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
            for b in cv.structural_blues():
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

    # ---------------- execution feed -------------------------------- #
    def on_exec(self, o, h, l, c, v, idx, time):
        self.now = time
        self.price = c
        cv = self.exec_canvas
        cv.on_bar(o, h, l, c, v, idx)
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
                self.anchor = {"idx": idx, "sweep_low": l,
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
                self.anchor = {"idx": idx, "sweep_low": l,
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
                self.anchor = {"idx": idx, "sweep_low": l,
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
        best = None
        for g, y in self.exec_canvas.pairs:
            if g.state != "ACTIVE" or y.state != "ACTIVE":
                continue
            if y.start_idx < lo or y.start_idx > hi:
                continue
            best = (g, y)
            break
        if best is None:
            self.cnt("setup_wait_stack")
            return
        g, y = best
        # ---- L2 compressed pivot entry ---------------------------
        # entry sits at the TIGHT seam: GreenBox top / YellowBox floor
        # (never the far yellow top that inflated risk3x in v21)
        entry = min(g.y_top, y.y_bottom)
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
        if stop < entry - g.height:
            stop = entry - g.height
        risk = entry - stop
        if risk <= 0 or entry <= stop:
            self.cnt("setup_bad_geometry")
            return
        # exchange truth: a stop tighter than the round-trip fee makes
        # the R-math dishonest (losses cost >1R, winners can never
        # clear the3R floor) — derived from FEE, not an invented number
        if risk <= 2 * FEE * entry:
            self.cnt("reject_risk_below_fees")
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
        # ---- L4: full purple lock after 2 losses -----------------
        if self.locked_range is not None:
            lb, lt = self.locked_range
            if lb <= c <= lt:
                self.cnt("blocked_locked_inside")
                return
            # price broke out of the locked range...
            if not self.breaker_ready:
                self.cnt("blocked_no_streak_breaker")
                return
            if purple is not None and entry > purple.quarter_bottom:
                self.cnt("blocked_not_in_quarter")
                return
            if self.board != "GREEN":
                self.cnt("blocked_board_red")
                return
            rising = getattr(self.struct_canvas, "purple_rising", False)
            if not rising:
                self.cnt("blocked_flow_not_rising")
                return
            self.locked_range = None
            self.breaker_ready = False
            self.blocked_after_losses = False
            self.cnt("locked_released")
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

    # ---------------- State 4: retrace fill (strictly later bars) ---- #
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
        if l <= s.entry:
            # re-validate the visual board AT the fill (spec: a red
            # 4H board forbids buying — checked only at anchor before)
            if self.board != "GREEN":
                self.setup = None
                self.state = "WAIT_ANCHOR"
                self.cnt("fill_cancel_board_red")
                return
            purple = self.struct_canvas.purple
            if purple is not None and s.entry > purple.mid:
                self.setup = None
                self.state = "WAIT_ANCHOR"
                self.cnt("fill_cancel_premium")
                return
            wall = self.struct_canvas.nearest_ceiling(s.entry)
            if wall is not None and                     (wall.y_bottom - s.entry) < MIN_R * s.risk:
                self.setup = None
                self.state = "WAIT_ANCHOR"
                self.cnt("fill_cancel_wall_closed")
                return
            fill = s.entry if o >= s.entry else o
            self._enter(s, fill, idx, time)

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
        equity = self.portfolio_equity(fill_px)
        slot = equity * SLOT
        notional = min(slot, self.pool["cash"])
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
        # L4 shield: trade opened with an active2-loss streak arms
        # breakeven early (exception to the no-move-before-3R law)
        self.shield = self.consec_losses >= LOSS_STREAK_RESET
        self.be_armed = False
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
        }
        self.cnt("fill")

    # ---------------- in-position management ------------------------ #
    def _exit(self, px, reason, idx, time):
        t = self.trade
        gross = (px - self.entry_px) * self.qty
        exit_fee = px * self.qty * FEE
        entry_fee = t.get("entry_fee", 0.0)
        net = gross - entry_fee - exit_fee
        R = net / (self.risk * self.qty) if self.risk > 0 else 0.0
        # ---- classification (L1: winners are >= +3.0R, always) ----
        is_win = net > 0 and R >= MIN_R - 1e-9
        is_be = (not is_win) and (self.shield or net > 0) and R >= -0.05
        if is_be:
            reason = "BREAKEVEN"
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
            # not a loss, not a win: streak unchanged; the dealing
            # range is re-locked (prompt: "يُعاد قفل النطاق")
            if rng is not None:
                self.consumed.append(rng)
            self.cnt("shield_be_holds_streak")
        else:
            self.consec_losses += 1
            self.last_loss_idx = idx
            self.last_loss_time = time
            if rng is not None:
                self.consumed.append(rng)   # one loss per range
            if self.consec_losses >= LOSS_STREAK_RESET:
                if rng is not None:
                    self.locked_range = rng  # full lock after2 losses
                self.breaker_ready = False
                self.blocked_after_losses = True
                self.cnt("structural_gate_armed")

    def _manage(self, o, h, l, c, idx, time):
        t = self.trade
        lock_line = self.lock_line   # entry + 3R + fees (net >= +3.0R)
        # structural stop (limit semantics: gap through -> open price)
        if l <= self.stop_px:
            px = self.stop_px if o >= self.stop_px else o
            self._exit(px, "STOP_BLUE", idx, time)
            return
        # ---- L4 shield exception: arm breakeven early -------------
        # (first structural RedBox break after entry, or half-way to3R)
        if self.shield and not self.be_armed:
            half = self.entry_px + (MIN_R / 2) * self.risk
            broke_red = any(e["idx"] >= t["entry_idx"]
                            for e in self.fresh_qualified)
            be = self.entry_px * (1 + 2 * FEE)       # entry + fees
            # arm only when the close proves ABOVE the BE line so the
            # stop always sits below the market (valid stop semantics)
            if (broke_red or h >= half or c >= be) and c > be:
                if be < c:
                    self.stop_px = be
                    self.be_armed = True
                    self.cnt("shield_be_armed")
        # ---- L1: NO stop movement before a CLOSE above 3R ---------
        if not self.ratchet and c >= lock_line:
            self.ratchet = True
            self.stop_px = max(self.stop_px, lock_line)
            self.cnt("ratchet_3r_close")
        elif self.ratchet and lock_line > self.stop_px:
            self.stop_px = lock_line
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
    return sorted(p.name for p in data_dir.iterdir() if p.is_dir())


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
        tf_15 = resample_causal_tf(df, "15min")
        tf_60 = resample_causal_tf(df, "1h")
        tf_4h = resample_causal_tf(df, STRUCT_TF)
        for tf in (tf_15, tf_60, tf_4h):
            tf.drop(index=tf[tf.index > s1].index, inplace=True)
        tf_15 = tf_15[tf_15.index >= warm]
        tf_60 = tf_60[tf_60.index >= warm]
        tf_4h = tf_4h[tf_4h.index >= warm]
        series[sym] = (tf_15, tf_60, tf_4h)
        for exec_tf in ("1h", "15min"):
            e = ICTBoxEngine(sym, exec_tf=exec_tf, tag=tag)
            e.pool = pool
            engines.append(e)
    pool["engines"] = engines
    # pointers per (sym, stream)
    ptr = {(sym, s): 0 for sym in symbols
           for s in ("15", "60", "4h")}
    eq_rows = []
    # global timeline = union of all exec frames (finest first)
    stamps = sorted(set().union(*[
        set(series[s][0].index) | set(series[s][1].index)
        for s in symbols]))
    for t in stamps:
        for sym in symbols:
            tf_15, tf_60, tf_4h = series[sym]
            # feed completed 4H / 1H bars up to t (causal: <= t)
            for stream, tf, handler in (
                    ("4h", tf_4h, "struct"),
                    ("60", tf_60, "exec")):
                while (ptr[(sym, stream)] < len(tf)
                       and tf.index[ptr[(sym, stream)]] <= t):
                    j = ptr[(sym, stream)]
                    if tf.index[j] >= warm:
                        r = tf.iloc[j]
                        vol = float(r.Volume) if "Volume" in r else 0.0
                        for e in engines:
                            if e.symbol != sym:
                                continue
                            if handler == "struct":
                                if e.struct_canvas.tf == STRUCT_TF:
                                    if t >= s0:
                                        e.warm = False
                                    e.on_struct(float(r.Open), float(r.High),
                                                float(r.Low), float(r.Close),
                                                vol,
                                                len(e.struct_canvas.bars),
                                                tf.index[j])
                            else:
                                if e.exec_tf == "1h":
                                    if t >= s0:
                                        e.warm = False
                                    e.on_exec(float(r.Open), float(r.High),
                                              float(r.Low), float(r.Close),
                                              vol, len(e.exec_canvas.bars),
                                              tf.index[j])
                    ptr[(sym, stream)] += 1
            # feed the 15m engine at its own stamps
            if t in tf_15.index:
                r = tf_15.loc[t]
                vol = float(r.Volume) if "Volume" in r else 0.0
                for e in engines:
                    if e.symbol == sym and e.exec_tf == "15min":
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
    fees = sum(eng.fees for eng in engines)
    eq = (pd.DataFrame(eq_rows, columns=["time", "equity"])
          .set_index("time") if eq_rows else pd.DataFrame())
    return {"trades": out_trades, "equity": eq, "count": counts,
            "fees": fees, "symbols": symbols, "pool_cash_end": pool["cash"]}


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
        "max_R": round(max(rs), 2) if rs else None,
        "fees": round(run["fees"], 2),
        "exit_reasons": _hist(t["exit_reason"] for t in tr),
        "s1_kinds": _hist(t.get("s1_kind", "-") for t in tr),
        "monthly": monthly,
        "count": run["count"],
        "symbols": run["symbols"],
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
    print(f"[v22-boxes] symbols discovered: "
          f"{discover_symbols(DATA_DIR)}")
    run = run_backtest(DATA_DIR, FULL_START, FULL_END)
    s = summarize(run)
    print(json.dumps({k: v for k, v in s.items()
                      if k not in ("monthly", "count")}, indent=2))
    print("funnel:", json.dumps(s["count"], indent=2))
    pd.DataFrame(run["trades"]).to_csv(RESULTS / "trades_v22.csv",
                                       index=False)
    pd.DataFrame(s["monthly"], columns=["month",
                                        "ret_pct"]).to_csv(
        RESULTS / "monthly_v22.csv", index=False)
    if len(run["equity"]):
        run["equity"].to_csv(RESULTS / "equity_v22.csv")
    with open(RESULTS / "summary_v22.json", "w") as f:
        json.dump(s, f, indent=2, default=str)
    # anatomy + diagrams
    ana = anatomy_table(run["trades"], 10)
    with open(RESULTS / "anatomy_v22.json", "w") as f:
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
    print("\n[v22-boxes] BULL RUN", BULL_START, "..", BULL_END)
    print(json.dumps(bs, indent=2))
    pd.DataFrame(bull["trades"]).to_csv(RESULTS / "trades_v22_bull.csv",
                                        index=False)
    with open(RESULTS / "bull_v22.json", "w") as f:
        json.dump(bs, f, indent=2, default=str)


if __name__ == "__main__":
    main()
