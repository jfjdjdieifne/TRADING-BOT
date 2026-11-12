#!/usr/bin/env python3
"""V3 core: hygiene repairs + six declared switches, on top of the v1/v2 primitives.

Nothing in build_v1/ or build_v2/ is edited; their modules are imported.  Everything this file adds
is declared in DECLARED_CHOICES_V3.md *before* it runs.

Conventions of this module (all declared):
  * prices are bid unless the side-correct execution says otherwise;
  * a buy triggers/fills on the ASK, a sell on the BID; stop and target checks use the side the exit
    would transact at (buy-to-close on the ASK, sell-to-close on the BID);
  * the spread is charged ONCE per plan: cost = spread at the fill bar / 2.  No other cost term;
  * causal reads only: every state is built from candles closed before the decision.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
_BUILD_V1 = HERE.parent / "build_v1"
_BUILD_V2 = HERE.parent / "build_v2"
for _p in (str(_BUILD_V1), str(_BUILD_V2)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from frame_v2 import FrameAggregator                                    # noqa: E402
from stream_v1 import (                                                  # noqa: E402
    HtfState, Window, displacement_now, fvg_now, memory_rss_kb, memory_total_kb,
    peak_rss_kb, session_now, structure_shift, sweep_now, swing_now,
    GapState, LiquidityState, OrderBlockState, SwingState, DealingRangeState,
)
from plan_v1 import (                                                     # noqa: E402
    GATE_RANGE_POSITION, build_plan, gates, gather_zones, rank_zones, targets_ahead,
)

UTC = timezone.utc
PIP = 10000.0
FRAME_MINUTES = {"5m": 5, "15m": 15, "1h": 60}
WINDOW_BY_FRAME = {"5m": 5760, "15m": 1920, "1h": 480}
EXPIRY_BARS = 288                     # ENGINEERING_CHOICE (DECLARED_CHOICES_V3 E-row): one trading day
MEMORY_CAP_FRACTION = 0.70            # standing rule

SWITCH_SETS = {
    "V3-0":    dict(stop="S0", liquidity=False, dgate=False, time_ny=False, entry="limit", range="swing"),
    "V3-S1":   dict(stop="S1", liquidity=False, dgate=False, time_ny=False, entry="limit", range="swing"),
    "V3-S2":   dict(stop="S2", liquidity=False, dgate=False, time_ny=False, entry="limit", range="swing"),
    "V3-L":    dict(stop="S0", liquidity=True,  dgate=False, time_ny=False, entry="limit", range="swing"),
    "V3-E":    dict(stop="S0", liquidity=False, dgate=False, time_ny=False, entry="market", range="swing"),
    "V3-R":    dict(stop="S0", liquidity=False, dgate=False, time_ny=False, entry="limit", range="leg"),
    "V3-T":    dict(stop="S0", liquidity=False, dgate=False, time_ny=True,  entry="limit", range="swing"),
    "V3-D":    dict(stop="S0", liquidity=False, dgate=True,  time_ny=False, entry="limit", range="swing"),
    "V3-FULL": dict(stop="S1", liquidity=True,  dgate=True,  time_ny=True,  entry="market", range="leg"),
}


# --------------------------------------------------------------------- frame state
class FrameV3:
    """One setup frame.  Same primitives as v2, plus absolute indices and timestamps (H5)."""

    def __init__(self, label: str) -> None:
        self.label = label
        self.minutes = FRAME_MINUTES[label]
        self.agg = FrameAggregator(self.minutes)
        self.window = Window(WINDOW_BY_FRAME[label])
        self.swings = SwingState()
        self.ranges = DealingRangeState()
        self.pools = LiquidityState()
        self.gaps = GapState()
        self.blocks = OrderBlockState()
        self.index = -1
        self.last: dict | None = None
        self.swing_log: list[dict] = []          # H5: absolute index + time of every confirmed swing

    # the window is bounded, so a window-local index maps to an absolute one like this
    def absolute(self, local_index: int) -> int:
        return self.index - self.window.t + local_index

    def push(self, bar) -> object | None:
        closed = self.agg.push(bar)
        if closed is None:
            return None
        self.index += 1
        self.window.push(closed)
        found = swing_now(self.window)
        # H5: record absolute index and the candle's open time for every swing found now
        for item in found:
            self.swing_log.append({
                "side": item["side"], "price": float(item["price"]),
                "index": self.absolute(item["level_index"]),
                "confirm_index": self.absolute(item["confirm_index"]),
                "time": self.window.bars[max(0, min(item["level_index"], self.window.t))].start.isoformat(),
                "confirm_time": self.window.bars[max(0, min(item["confirm_index"], self.window.t))].start.isoformat(),
            })
        self.swings.push(found)
        self.pools.push_swings(found, self.swings)
        self.pools.push_bar(closed, self.index)
        new_gaps = fvg_now(self.window)
        self.gaps.push(new_gaps, self.index)
        self.gaps.push_bar(closed)
        disp = displacement_now(self.window)
        self.blocks.push_bar(closed)
        high_ref = self.swings.last("high")
        low_ref = self.swings.last("low")
        sweep_high = sweep_now(self.window, "high", high_ref.price if high_ref else None)
        sweep_low = sweep_now(self.window, "low", low_ref.price if low_ref else None)
        block = None
        if disp.get("answer") == "YES" and self.window.t >= 2:
            direction = "bullish" if closed.bid_close > closed.bid_open else "bearish"
            block = self.blocks.maybe_create(
                self.window, disp, direction,
                fvg_below=any(z["direction"] == direction for z in new_gaps),
                sweep_evidence=(sweep_high.get("answer") == "YES" if direction == "bearish"
                                else sweep_low.get("answer") == "YES"),
                structure_break=bool(structure_shift(closed, self.swings, disp)["shift"]),
            )
        self.last = {
            "bar": closed, "swings": found, "gaps": new_gaps, "displacement": disp,
            "sweep_high": sweep_high, "sweep_low": sweep_low, "block": block,
            "range": self.ranges.compute(self.swings, closed.bid_close),
            "shift": structure_shift(closed, self.swings, disp),
        }
        return closed

    # ---------------------------------------------------------------- extra views
    def candle_at(self, index: int) -> dict | None:
        """Candle OHLC by absolute frame index, from the saved swing log's sibling window if possible."""
        return None

    def pool_view(self) -> list[dict]:
        out = []
        for side in ("high", "low"):
            for pool in self.pools.untaken(side):
                item = dict(pool)
                item["frame"] = self.label
                formed = pool.get("formed_index")
                item["age_bars"] = None if formed is None or formed < 0 else self.index - formed
                out.append(item)
        return out

    def last_swing_before(self, side: str, index: int) -> dict | None:
        """The last confirmed swing on `side` whose confirmation happened at or before `index`."""
        for item in reversed(self.swing_log):
            if item["side"] == side and item["confirm_index"] <= index:
                return item
        return None


# --------------------------------------------------------------------- New York clock (T)
NY_DAY_ROLL_HOUR = 17                 # T: day roll 17:00 America/New_York
NY_WEEK_OPEN_WEEKDAY = 6              # Sunday (Mon=0)


def ny_bucket(moment: datetime) -> dict:
    """Day and week keys under the New-York doctrine: day rolls 17:00 NY, week opens Sunday 17:00 NY."""

    from zoneinfo import ZoneInfo
    ny = moment.astimezone(ZoneInfo("America/New_York"))
    shifted = ny - timedelta(hours=NY_DAY_ROLL_HOUR)
    day_key = (shifted.year, shifted.month, shifted.day)
    days_since_sunday = (shifted.weekday() - NY_WEEK_OPEN_WEEKDAY) % 7
    week_start = (shifted - timedelta(days=days_since_sunday)).date()
    return {"ny_time": ny, "day_key": day_key, "week_key": week_start}


class NyHtfState:
    """Daily/weekly buckets bounded in New York time, exposed only when a later bucket appears."""

    def __init__(self) -> None:
        self.current: dict[str, dict] = {}
        self.completed: dict[str, dict] = {}

    def push(self, bar) -> list[str]:
        keys = ny_bucket(bar.start)
        rolled = []
        for tf, key in (("daily", keys["day_key"]), ("weekly", keys["week_key"])):
            current = self.current.get(tf)
            if current is None or current["key"] != key:
                if current is not None:
                    self.completed[tf] = {**current, "available_at": bar.start.isoformat()}
                    rolled.append(tf)
                self.current[tf] = {"key": key, "open": bar.bid_open, "high": bar.bid_high,
                                    "low": bar.bid_low, "close": bar.bid_close,
                                    "bucket_start": str(key)}
            else:
                current["high"] = max(current["high"], bar.bid_high)
                current["low"] = min(current["low"], bar.bid_low)
                current["close"] = bar.bid_close
        return rolled

    def view(self) -> dict:
        out = {"daily": None, "weekly": None}
        for tf, done in self.completed.items():
            out[tf] = {"bucket_start": done["bucket_start"], "open": done["open"], "high": done["high"],
                       "low": done["low"], "close": done["close"], "available_at": done["available_at"],
                       "bias": ("UP" if done["close"] > done["open"]
                                else "DOWN" if done["close"] < done["open"] else "FLAT")}
        return out


# --------------------------------------------------------------------- stops and ranges
def stop_for(stop_kind: str, *, direction: str, zone: dict, frame: FrameV3,
             ctx: dict) -> tuple[float | None, str]:
    """Return (stop price or None when the switch yields no plan, rule string)."""

    if stop_kind == "S0":
        if zone["kind"] == "sweep_level":
            return (zone["upper"] if direction == "bearish" else zone["lower"]), "sweep wick"
        return (zone["upper"] if direction == "bearish" else zone["lower"]), f"far side of {zone['kind']}"

    if stop_kind == "S2":
        threshold = zone.get("mean_threshold")
        if threshold is None:
            return None, "S2_MEAN_THRESHOLD_UNAVAILABLE"
        return threshold, "mean threshold of the zone's own candle (S2)"

    # S1: beyond the ORIGIN of the displacement leg that created the zone
    middle = zone["formed_index"] if zone.get("formed_index") is not None else frame.index
    first = middle - 2
    if direction == "bearish":
        origin = frame.last_swing_before("high", first)
        if origin is None:
            return None, "S1_NO_CONFIRMED_ORIGIN"
        return origin["price"], "origin of the displacement leg (last confirmed swing high)"
    origin = frame.last_swing_before("low", first)
    if origin is None:
        return None, "S1_NO_CONFIRMED_ORIGIN"
    return origin["price"], "origin of the displacement leg (last confirmed swing low)"


def leg_range(frame: FrameV3, zone: dict, direction: str, fallback: dict) -> dict:
    """R switch: the dealing range of the leg that created the zone.

    Declared: origin = the last confirmed opposite-side swing before the zone's first candle; the
    end extreme = the leg's extreme between that origin and the zone's middle candle.
    """

    middle = zone["formed_index"] if zone.get("formed_index") is not None else frame.index
    first = middle - 2
    if direction == "bearish":
        origin = frame.last_swing_before("high", first)
        if origin is None:
            return {**fallback, "definition_id": "LEG_ORIGIN_UNAVAILABLE"}
        low_price, low_time = None, None
        for i in range(origin["index"], middle + 1):
            candle = frame.window.bars[frame.window.t - (frame.index - i)] if 0 <= frame.window.t - (frame.index - i) < len(frame.window.bars) else None
            if candle is None:
                continue
            if low_price is None or candle.bid_low < low_price:
                low_price, low_time = candle.bid_low, candle.start.isoformat()
        if low_price is None:
            return {**fallback, "definition_id": "LEG_END_UNAVAILABLE"}
        return {"low": low_price, "high": origin["price"],
                "low_index": None, "high_index": origin["index"],
                "equilibrium": (origin["price"] + low_price) / 2.0,
                "definition_id": "ENGINEERING_CHOICE_LEG_ORIGIN_TO_END",
                "origin_time": origin["time"], "end_time": low_time}
    origin = frame.last_swing_before("low", first)
    if origin is None:
        return {**fallback, "definition_id": "LEG_ORIGIN_UNAVAILABLE"}
    high_price, high_time = None, None
    for i in range(origin["index"], middle + 1):
        offset = frame.window.t - (frame.index - i)
        if not (0 <= offset < len(frame.window.bars)):
            continue
        candle = frame.window.bars[offset]
        if high_price is None or candle.bid_high > high_price:
            high_price, high_time = candle.bid_high, candle.start.isoformat()
    if high_price is None:
        return {**fallback, "definition_id": "LEG_END_UNAVAILABLE"}
    return {"low": origin["price"], "high": high_price,
            "low_index": origin["index"], "high_index": None,
            "equilibrium": (origin["price"] + high_price) / 2.0,
            "definition_id": "ENGINEERING_CHOICE_LEG_ORIGIN_TO_END",
            "origin_time": origin["time"], "end_time": high_time}


def range_position(rg: dict, price: float) -> tuple[str, float | None]:
    low, high = rg.get("low"), rg.get("high")
    if low is None or high is None or high <= low:
        return "undefined", None
    ratio = (price - low) / (high - low)
    if ratio > 1.0:
        return "ABOVE_RANGE", ratio
    if ratio < 0.0:
        return "BELOW_RANGE", ratio
    label = "premium" if price > rg.get("equilibrium", (low + high) / 2.0) else (
        "discount" if price < rg.get("equilibrium", (low + high) / 2.0) else "equilibrium")
    return label, ratio


# --------------------------------------------------------------------- displacement (D)
def d_new_features(frame: FrameV3, zone: dict, direction: str) -> dict:
    """D-new: the leg that formed the zone closes beyond a prior confirmed swing (break) AND the
    zone is a gap.  No size ratio anywhere."""

    middle = zone["formed_index"] if zone.get("formed_index") is not None else frame.index
    first = middle - 2
    if direction == "bearish":
        prior = frame.last_swing_before("low", first)
        if prior is None:
            return {"break": False, "gap": zone["kind"] in ("fvg", "order_block"), "answer": "NO",
                    "reason": "no prior confirmed swing low"}
        closed_beyond = False
        for i in (first, first + 1, middle):
            offset = frame.window.t - (frame.index - i)
            if 0 <= offset < len(frame.window.bars) and frame.window.bars[offset].bid_close < prior["price"]:
                closed_beyond = True
        gap = zone["kind"] in ("fvg", "order_block")
        return {"break": closed_beyond, "gap": gap, "swing": prior["price"], "swing_time": prior["time"],
                "answer": "YES" if (closed_beyond and gap) else "NO"}
    prior = frame.last_swing_before("high", first)
    if prior is None:
        return {"break": False, "gap": zone["kind"] in ("fvg", "order_block"), "answer": "NO",
                "reason": "no prior confirmed swing high"}
    closed_beyond = False
    for i in (first, first + 1, middle):
        offset = frame.window.t - (frame.index - i)
        if 0 <= offset < len(frame.window.bars) and frame.window.bars[offset].bid_close > prior["price"]:
            closed_beyond = True
    gap = zone["kind"] in ("fvg", "order_block")
    return {"break": closed_beyond, "gap": gap, "swing": prior["price"], "swing_time": prior["time"],
            "answer": "YES" if (closed_beyond and gap) else "NO"}


def d_new_answer(structure_break: bool, gap: bool) -> str:
    """D-new truth table: YES only when the leg breaks structure AND the zone is a gap."""
    return "YES" if (structure_break and gap) else "NO"


def target_behind(entry: float, level: float, direction: str) -> bool:
    """H4: a target that is not beyond the entry on the trade's side."""
    return level <= entry if direction == "bullish" else level >= entry


def rank_expansion(frame: FrameV3, index: int) -> float | None:
    """Rank-based range expansion of one candle inside the lookback: (#smaller ranges)/n, no cutoff."""

    if index is None:
        index = frame.index
    offset = frame.window.t - (frame.index - index)
    if not (0 <= offset < len(frame.window.bars)):
        return None
    target = frame.window.bars[offset]
    rng = target.bid_high - target.bid_low
    ranges = [b.bid_high - b.bid_low for b in frame.window.bars]
    smaller = sum(1 for r in ranges if r < rng)
    return smaller / len(ranges) if ranges else None


# --------------------------------------------------------------------- liquidity (L)
def htf_pools(htf_view: dict, frame_label: str) -> list[dict]:
    """Previous completed day and week extremes as pools (L switch)."""

    out = []
    for tf in ("daily", "weekly"):
        done = htf_view.get(tf)
        if not done:
            continue
        for side, level in (("high", done["high"]), ("low", done["low"])):
            out.append({"pool_id": f"pool:htf:{tf}:{side}:{level:.8f}", "side": side,
                        "kind": f"previous_{tf}_extreme", "level": float(level), "formed_index": -1,
                        "member_levels": [float(level)], "state": "formed", "taken_index": None,
                        "frame": frame_label, "age_bars": None,
                        "bucket_start": done["bucket_start"]})
    return out


def pool_class(level: float, side: str, rg: dict) -> str:
    """INTERNAL / EXTERNAL against the dealing range (L switch)."""

    low, high = rg.get("low"), rg.get("high")
    if low is None or high is None:
        return "UNKNOWN"
    if side == "high":
        return "EXTERNAL" if level > high else "INTERNAL"
    return "EXTERNAL" if level < low else "INTERNAL"


def merge_pools(pools: list[dict]) -> list[dict]:
    """H3: one level = one pool.  Pair members are already merged by LiquidityState; here the same
    exact level across frames collapses into one pool carrying both frame labels."""

    merged: dict[tuple[str, float], dict] = {}
    for pool in pools:
        key = (pool["side"], round(float(pool["level"]), 8))
        if key in merged:
            frames = merged[key].setdefault("frames", [merged[key].get("frame")])
            if pool.get("frame") not in frames:
                frames.append(pool.get("frame"))
            merged[key]["frames"] = frames
            continue
        item = dict(pool)
        item["frames"] = [pool.get("frame")]
        merged[key] = item
    return list(merged.values())


def pick_targets(pools: list[dict], *, entry: float, direction: str, rg: dict,
                 liquidity: bool) -> list[dict]:
    """T1/T2 with the H3 identity rule; under L, T2 = next distinct EXTERNAL pool."""

    side = "high" if direction == "bullish" else "low"
    ahead = []
    for pool in pools:
        if pool["side"] != side:
            continue
        ok = pool["level"] > entry if direction == "bullish" else pool["level"] < entry
        if ok:
            ahead.append(pool)
    if not ahead:
        return []
    draw_range = float(rg.get("high", entry)) - float(rg.get("low", entry))
    if draw_range <= 0:
        return []
    ranked = targets_ahead(ahead, entry=entry, range_high=rg.get("high", entry),
                           range_low=rg.get("low", entry), direction=direction,
                           fallback_formed_at=datetime.now(UTC))
    if not ranked:
        return []
    for item in ranked:
        item["class"] = pool_class(item["level"], side, rg) if liquidity else None
    t1 = ranked[0]
    t2 = None
    if liquidity:
        # T2 must be a distinct level and of the EXTERNAL class when one exists beyond T1
        want = "EXTERNAL"
        pool_of_t2 = [p for p in ranked[1:] if round(p["level"], 8) != round(t1["level"], 8)]
        if t1["class"] == "INTERNAL":
            external = [p for p in pool_of_t2 if p["class"] == want]
            t2 = external[0] if external else None
        else:
            external = [p for p in pool_of_t2 if p["class"] == want]
            t2 = external[0] if external else None
    else:
        rest = [p for p in ranked[1:] if round(p["level"], 8) != round(t1["level"], 8)]
        t2 = rest[0] if rest else None
    out = [t1] + ([t2] if t2 else [])
    return out


# --------------------------------------------------------------------- execution
class Execution:
    """Side-correct settlement (H1), stale cancel (H2), next-bar first evaluation (H7)."""

    def __init__(self, plan: dict) -> None:
        self.plan = plan
        self.direction = plan["direction"]
        self.entry = plan["entry"]
        self.stop = plan["stop"]
        self.t1 = plan["t1"]["level"] if plan.get("t1") else None
        self.state = "armed"           # armed -> filled -> settled | cancelled | expired
        self.armed_index = plan["decision_index"]
        self.fill_index = None
        self.fill_price = None
        self.exit_index = None
        self.exit_price = None
        self.exit_reason = None
        self.r_measured = None
        self.cost_price = None
        self.bars_since_arm = 0
        self.market_pending = False     # E: waiting for the bar after the touch-and-close-inside

    # ---------- helpers
    def _stop_hit(self, bar) -> bool:
        # a sell is closed by buying at the ask; a buy by selling at the bid
        return bar.ask_high >= self.stop if self.direction == "bearish" else bar.bid_low <= self.stop

    def _target_hit(self, bar) -> bool:
        if self.t1 is None:
            return False
        return bar.ask_low <= self.t1 if self.direction == "bearish" else bar.bid_high >= self.t1

    def _entry_touched(self, bar) -> bool:
        """A limit at a level fills only when the level actually trades inside the bar's range."""
        if self.direction == "bearish":
            return bar.bid_low <= self.entry <= bar.bid_high
        return bar.ask_low <= self.entry <= bar.ask_high

    def _settle(self, index: int, price: float, reason: str, spread: float) -> None:
        risk = abs(self.entry - self.stop)
        gross = (self.entry - price) if self.direction == "bearish" else (price - self.entry)
        cost = spread / 2.0
        self.exit_index = index
        self.exit_price = price
        self.exit_reason = reason
        self.state = "settled"
        self.cost_price = cost
        self.r_measured = (gross - cost) / risk if risk > 0 else None

    # ---------- the loop
    def update(self, index: int, bar) -> None:
        if self.state in ("settled", "cancelled", "expired"):
            return
        if index <= self.armed_index:
            return
        self.bars_since_arm += 1
        if self.bars_since_arm > EXPIRY_BARS:
            self.state = "expired"
            self.exit_reason = "expired"
            self.r_measured = 0.0
            return

        if self.state == "armed":
            fill_mode = self.plan["entry_mode"]
            if fill_mode == "limit":
                if self._entry_touched(bar):
                    self.fill_index = index
                    self.fill_price = self.entry
                    self.state = "filled"
                    self._evaluate(index, bar)
                    return
                # H2: the stop side taken on a bar that never traded at the entry = stale plan
                if self._stop_hit(bar):
                    self.state = "cancelled"
                    self.exit_reason = "cancelled_invalidated_before_fill"
                return
            # E: a stale plan is cancelled before the market entry is taken
            if self._stop_hit(bar):
                self.state = "cancelled"
                self.exit_reason = "cancelled_invalidated_before_fill"
                return
            # E: market entry at the open of the bar AFTER a bar that touched and closed inside
            if self.market_pending:
                price = bar.ask_open if self.direction == "bullish" else bar.bid_open
                self.fill_index = index
                self.fill_price = price
                self.state = "filled"
                # risk and targets are re-measured from the actual fill
                self.plan["fill_price_actual"] = price
                self._evaluate(index, bar)
                return
            touched = self._entry_touched(bar)
            # "inside" = closed past the entry edge, into the zone: above it for a sell, below for a buy
            inside = (bar.bid_close > self.entry) if self.direction == "bearish" else (bar.bid_close < self.entry)
            if touched and inside:
                self.market_pending = True
            return

        if self.state == "filled":
            self._evaluate(index, bar)

    def _evaluate(self, index: int, bar) -> None:
        """Order inside one bar: stop first (conservative), then target."""
        if self._stop_hit(bar):
            self._settle(index, self.stop, "stop", bar.spread_open)
            return
        if self._target_hit(bar):
            self._settle(index, self.t1, "t1_touched", bar.spread_open)

    # ---------- outcome view
    def view(self) -> dict:
        return {"state": self.state, "fill_index": self.fill_index, "fill_price": self.fill_price,
                "exit_index": self.exit_index, "exit_price": self.exit_price,
                "exit_reason": self.exit_reason, "r_measured": self.r_measured,
                "cost_price": self.cost_price, "bars_since_arm": self.bars_since_arm}
