"""
v21 — Visual Chart Canvas & Colored Boxes Engine (ICT, spot long-only)

Zero Arbitrary Numbers Law: every trading decision derives from the five
colored boxes and their spatial relations:
  BlueBox_SSL / RedBox_BSL / YellowBox_BullFVG / GreenBox_BullOB /
  PurpleBox_DealingRange
No indicators, no averages, no wait-bars, no time freezes, no invented
percentages. 3R is the sanctioned box-height ratio (3 x RiskHeight).
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
    def active_blues(self):
        return [b for b in self.blues if b.state == "ACTIVE"]

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
    def __init__(self, symbol: str, capital_slot: float, tag: str = ""):
        self.symbol = symbol
        self.tag = tag
        self.exec_canvas = ChartCanvas(EXEC_TF)
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
        self.cash_available = CAPITAL / MAX_SLOTS  # portfolio sets this
        # 4H board bookkeeping
        self._htf_protected: Box | None = None
        self._htf_bos_seen: set = set()

    # ---------- counters ------------------------------------------- #
    def cnt(self, k, n=1):
        if self.tag == "BULL":
            k = "bull_" + k
        self.count[k] = self.count.get(k, 0) + n

    # ---------------- 4H board feed -------------------------------- #
    def on_struct(self, o, h, l, c, v, idx, time):
        ev = self.struct_canvas.on_bar(o, h, l, c, v, idx)
        cv = self.struct_canvas
        # new 4H bullish BOS -> board GREEN + protected low recorded
        while cv.bos_events and cv.bos_events[0]["idx"] <= idx:
            e = cv.bos_events.pop(0)
            if e["idx"] in self._htf_bos_seen:
                continue
            self._htf_bos_seen.add(e["idx"])
            self.last_red_break_idx = idx      # structural unlock (4H)
            self.last_htf_break_time = time    # gate compares TIMES
            # protected low = last blue below the broken red
            below = [b for b in cv.active_blues()
                     if b.y_top < e["box"].y_bottom]
            self._htf_protected = below[-1] if below else (
                cv.active_blues()[-1] if cv.active_blues() else None)
            self.board = "GREEN"
            self.board_mode = "BOS_CONTINUATION"   # state (a)
            self.cnt("board_green_bos")
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
        if fresh:
            self.last_red_break_idx = idx
        if self.qty > 0:
            for e in fresh:
                below = [b for b in cv.active_blues()
                         if b.y_top < e["box"].y_bottom
                         and b.start_idx < e["idx"]]
                prot = below[-1] if below else None
                if prot is not None and prot.y_bottom > self.stop_px:
                    self.stop_px = prot.y_bottom
                    self.protected_blue = prot
                    self.cnt("trail_protected_blue")
            self._manage(o, h, l, c, idx, time)
            return
        # state chain may advance multiple steps inside one closed bar
        # (each step only reads this bar's completed data; fills remain
        # gated to bars strictly after setup completion)
        for _ in range(4):
            before = self.state
            if self.state == "WAIT_ANCHOR":
                self._seek_anchor(o, h, l, c, idx, time)
            elif self.state == "WAIT_BOS":
                self._seek_bos(o, h, l, c, idx, time, fresh)
            elif self.state == "WAIT_SETUP":
                self._seek_setup(o, h, l, c, idx, time, fresh)
            elif self.state == "WAIT_RETRACE":
                self._seek_fill(o, h, l, c, idx, time, fresh)
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

        # (a) blue-box sweep: wick into liquidity, body closes back
        for b in reversed(self.exec_canvas.active_blues()):
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
        for b in reversed(self.exec_canvas.active_blues()):
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
        # ---- geometry of the trade box ---------------------------
        entry = y.y_top
        if purple is not None and entry > purple.mid:
            entry = y.mid
            if entry > purple.mid:
                entry = g.y_top
        stop = min(g.y_bottom, a["sweep_low"])
        risk = entry - stop
        if risk <= 0 or entry <= stop:
            self.cnt("setup_bad_geometry")
            return
        # ---- 3R visual gate: 4H wall vs open sky ----------------
        wall_s = self.struct_canvas.nearest_ceiling(entry)  # 4H ceiling
        if wall_s is not None and (wall_s.y_bottom - entry) < MIN_R * risk:
            self.cnt("reject_wall_within_3r")
            return
        # open sky (no wall at/above entry) passes by definition
        # ---- 3rd-loss structural gate ----------------------------
        if self.blocked_after_losses:
            if (self.last_htf_break_time is None
                    or self.last_loss_time is None
                    or self.last_htf_break_time <= self.last_loss_time):
                self.cnt("blocked_no_fresh_break")
                return
            if purple is not None and entry > purple.quarter_bottom:
                self.cnt("blocked_not_in_quarter")
                return
            # golden combo: the board must still be in 4H BOS
            # continuation (a fresh HTF break has not since reverted)
            if self.board_mode != "BOS_CONTINUATION":
                self.cnt("blocked_not_bos_state")
                return
            # HTF Order Flow filter (prompt crime#5): only release
            # into a rising structure (purple box making higher lows)
            rising = getattr(self.struct_canvas, "purple_rising", False)
            if not rising:
                self.cnt("blocked_flow_not_rising")
                return
            if self.board != "GREEN":
                self.cnt("blocked_board_red")
                return
            self.blocked_after_losses = False
            self.cnt("blocked_released")
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
        risk = fill_px - stop
        equity = self.equity(fill_px)
        slot = equity * SLOT
        notional = min(slot, self.cash_available)
        qty = notional / fill_px
        notional = qty * fill_px
        if qty <= 0 or notional < EXCHANGE_MIN_NOTIONAL:
            self.setup = None
            self.state = "WAIT_ANCHOR"
            self.cnt("fill_below_exchange_min")
            return
        fee = notional * FEE
        if fee + notional > self.cash_available + 1e-9:
            self.setup = None
            self.state = "WAIT_ANCHOR"
            return
        self.qty = qty
        self.entry_px = fill_px
        self.stop_px = stop
        self.risk = risk
        self.ratchet = False
        self.protected_blue = s.wave_low
        self.cash_available -= notional + fee
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
        t.update({"exit_time": str(time), "exit_idx": idx,
                  "exit_price": px, "exit_reason": reason,
                  "net_pnl": net, "R": R, "bars_held": idx - t["entry_idx"]})
        # position sold: proceeds back to cash (entry cost+fee already
        # deducted at fill, so equity math closes exactly)
        self.cash_available += px * self.qty - exit_fee
        self.trades.append(t)
        self.qty = 0.0
        self.trade = None
        self.ratchet = False
        # return the machine to the drawing board (v21 bug#2: state
        # stayed IN_POS after the first exit -> engine froze forever)
        self.state = "WAIT_ANCHOR"
        self.setup = None
        self.anchor = None
        self.bos = None
        self.cnt("exit_" + reason)
        if net <= 0:
            self.consec_losses += 1
            self.last_loss_idx = idx
            self.last_loss_time = time
            if self.consec_losses >= LOSS_STREAK_RESET:
                self.blocked_after_losses = True
                self.cnt("structural_gate_armed")
        else:
            self.consec_losses = 0

    def _manage(self, o, h, l, c, idx, time):
        t = self.trade
        # structural stop (limit semantics: gap through -> open price)
        if l <= self.stop_px:
            px = self.stop_px if o >= self.stop_px else o
            self._exit(px, "STOP_BLUE", idx, time)
            return
        # 3R ratchet: lock at least the 3x box-height ratio
        if not self.ratchet and h >= self.entry_px + MIN_R * self.risk:
            self.ratchet = True
            self.cnt("ratchet_3r")
        if self.ratchet:
            lock_line = self.entry_px + MIN_R * self.risk
            best = lock_line
            cv = self.exec_canvas
            for box in list(cv.greens) + list(cv.yellows_b) + \
                    list(cv.active_blues()):
                if box.state == "ACTIVE" and box.y_bottom <= c \
                        and box.y_bottom >= lock_line \
                        and box.y_bottom > self.stop_px:
                    best = max(best, box.y_bottom)
            if best < c and best > self.stop_px:
                self.stop_px = best
                self.cnt("lock_3r_box")
        # top-sell: after 3R, bearish CHoCH (blue broken) + bearish gap
        if self.ratchet:
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
    def equity(self, price=None):
        p = price if price is not None else self.price
        return self.cash_available + (self.qty * p if self.qty else 0.0)


# ==================================================================== #
# Portfolio runner (multi-coin ready; data currently holds BTC only)
# ==================================================================== #
def discover_symbols(data_dir: Path) -> list[str]:
    return sorted(p.name for p in data_dir.iterdir() if p.is_dir())


def run_backtest(data_dir: Path, start: str, end: str,
                 warmup_days: int = 60, tag: str = ""):
    from engine.causal_primitives import load_asset_ohlcv, resample_causal_tf
    s0 = pd.Timestamp(start).tz_localize("UTC")
    s1 = pd.Timestamp(end).tz_localize("UTC")
    warm = s0 - pd.Timedelta(days=warmup_days)
    symbols = discover_symbols(data_dir)
    engines = {}
    series = {}
    for sym in symbols:
        df = load_asset_ohlcv(
            data_dir / sym,
            include_stems=[str(y) for y in range(warm.year, s1.year + 1)])
        tf_e = resample_causal_tf(df, EXEC_TF)
        tf_s = resample_causal_tf(df, STRUCT_TF)
        tf_e = tf_e[(tf_e.index >= warm) & (tf_e.index <= s1)]
        tf_s = tf_s[(tf_s.index >= warm) & (tf_s.index <= s1)]
        series[sym] = (tf_e, tf_s)
        engines[sym] = ICTBoxEngine(sym, capital_slot=CAPITAL, tag=tag)
        engines[sym].cash_available = CAPITAL / max(len(symbols), 1)
    eq_rows = []
    i_struct = {s: 0 for s in symbols}
    # merged 15m timeline
    stamps = sorted(set().union(*[set(series[s][0].index) for s in symbols]))
    for t in stamps:
        for sym, eng in engines.items():
            tf_e, tf_s = series[sym]
            rows_s = tf_s
            while (i_struct[sym] < len(rows_s)
                   and rows_s.index[i_struct[sym]] <= t):
                j = i_struct[sym]
                if rows_s.index[j] >= warm:
                    r = rows_s.iloc[j]
                    eng.on_struct(float(r.Open), float(r.High),
                                  float(r.Low), float(r.Close),
                                  float(r.Volume) if "Volume" in r else 0.0,
                                  len(eng.struct_canvas.bars),
                                  rows_s.index[j])
                i_struct[sym] += 1
            if t not in tf_e.index:
                continue
            if t >= s0:
                eng.warm = False
            r = tf_e.loc[t]
            eng.on_exec(float(r.Open), float(r.High), float(r.Low),
                        float(r.Close),
                        float(r.Volume) if "Volume" in r else 0.0,
                        len(eng.exec_canvas.bars), t)
        # cash pool sync: cash lives on engines; portfolio equity =
        # sum of engine equities (positions marked at last price)
        eq = sum(eng.equity() for eng in engines.values())
        if t >= s0:
            eq_rows.append((t, eq))
    # mark-to-market close (reporting only)
    out_trades = []
    for eng in engines.values():
        if eng.qty > 0:
            eng._exit(eng.price, "END_OF_DATA",
                      len(eng.exec_canvas.bars), eng.now)
        out_trades.extend(eng.trades)
    out_trades.sort(key=lambda t: str(t["entry_time"]))
    counts = {}
    for eng in engines.values():
        for k, v in eng.count.items():
            counts[k] = counts.get(k, 0) + v
    fees = sum(eng.fees for eng in engines.values())
    eq = (pd.DataFrame(eq_rows, columns=["time", "equity"])
          .set_index("time") if eq_rows else pd.DataFrame())
    return {"trades": out_trades, "equity": eq, "count": counts,
            "fees": fees, "symbols": symbols}


# ==================================================================== #
# Reporting
# ==================================================================== #
def summarize(run, capital=CAPITAL):
    tr = run["trades"]
    n = len(tr)
    wins = [t for t in tr if t["net_pnl"] > 0]
    losses = [t for t in tr if t["net_pnl"] <= 0]
    gp = sum(t["net_pnl"] for t in wins)
    gl = -sum(t["net_pnl"] for t in losses)
    rs = [t["R"] for t in tr]
    eq = run["equity"]
    end_eq = float(eq["equity"].iloc[-1]) if len(eq) else capital
    peak = eq["equity"].cummax() if len(eq) else None
    dd = float(((eq["equity"] - peak) / peak * 100).min()) if len(eq) else 0.0
    # consecutive loss streaks on trade sequence
    streak = best = 0
    for t in tr:
        if t["net_pnl"] <= 0:
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
        "trades": n, "wins": len(wins),
        "win_rate_pct": round(len(wins) / n * 100, 1) if n else 0.0,
        "profit_factor": round(gp / gl, 2) if gl > 0 else None,
        "net_pnl": round(end_eq - capital, 2),
        "net_pct": round((end_eq - capital) / capital * 100, 2),
        "end_equity": round(end_eq, 2),
        "max_drawdown_pct": round(dd, 2),
        "max_consecutive_losses": best,
        "avg_R": round(float(np.mean(rs)), 2) if rs else 0.0,
        "min_winner_R": round(min([t["R"] for t in wins]), 2) if wins else None,
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
    print(f"[v21-boxes] symbols discovered: "
          f"{discover_symbols(DATA_DIR)}")
    run = run_backtest(DATA_DIR, FULL_START, FULL_END)
    s = summarize(run)
    print(json.dumps({k: v for k, v in s.items()
                      if k not in ("monthly", "count")}, indent=2))
    print("funnel:", json.dumps(s["count"], indent=2))
    pd.DataFrame(run["trades"]).to_csv(RESULTS / "trades_v21.csv",
                                       index=False)
    pd.DataFrame(s["monthly"], columns=["month",
                                        "ret_pct"]).to_csv(
        RESULTS / "monthly_v21.csv", index=False)
    if len(run["equity"]):
        run["equity"].to_csv(RESULTS / "equity_v21.csv")
    with open(RESULTS / "summary_v21.json", "w") as f:
        json.dump(s, f, indent=2, default=str)
    # anatomy + diagrams
    ana = anatomy_table(run["trades"], 10)
    with open(RESULTS / "anatomy_v21.json", "w") as f:
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
    print("\n[v21-boxes] BULL RUN", BULL_START, "..", BULL_END)
    print(json.dumps(bs, indent=2))
    pd.DataFrame(bull["trades"]).to_csv(RESULTS / "trades_v21_bull.csv",
                                        index=False)
    with open(RESULTS / "bull_v21.json", "w") as f:
        json.dump(bs, f, indent=2, default=str)


if __name__ == "__main__":
    main()
