#!/usr/bin/env python3
"""Streaming primitives over 5m bid/ask, with a bounded causal lookback.

This module is the "window manager + assembler" of ICT_RECIPE_SPEC_V1: it owns a fixed-length
candle buffer, calls the existing per-bar primitives with `candles[:t+1]`, and keeps every piece of
state that must survive between bars in a *bounded* container.

Nothing in `src/`, `engine_v1/`, `holdout_v1/` or `dev_month_v0/` is imported for its *numbers*; the
functions below call them and print what they return.  Where a definition is copied it is copied by
its printed id (see REUSE_DECISIONS.md).

No pandas, no resampling, no network.  Causal reads only: a call at index t receives candles[:t+1].
"""

from __future__ import annotations

import gzip
import hashlib
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

_HERE = Path(__file__).resolve()
_RESEARCH = _HERE.parents[2]              # docs/research
ENGINE_V1 = _RESEARCH / "huddleston_study" / "engine_v1"
SRC = _HERE.parents[4] / "src"            # project/trading_project/src

for _p in (str(SRC), str(ENGINE_V1 / "b1_candles"), str(ENGINE_V1 / "c1_catalog")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from candle import Candle as B1Candle                      # noqa: E402  engine_v1/b1_candles
from displacement import displacement_at                   # noqa: E402  c1_catalog
from fvg import fvg_at                                     # noqa: E402  b1_candles
from liquidity_sweep import sweep_at, sweep_at_swing_level  # noqa: E402  c1_catalog
from order_block import (                                  # noqa: E402  c1_catalog
    BOUNDARY_FULL_RANGE,
    ENTRY_MEAN_THRESHOLD,
    INVALID_FAR_EDGE,
    MT_BODY,
    PREREQ_FVG,
    PREREQ_STRUCTURE_BREAK,
    PREREQ_SWEEP,
    PREREQ_UNMITIGATED,
    order_block_at,
)
from swing import swing_at                                 # noqa: E402  b1_candles

from trading_system.ict_engine.data import Candle as IctCandle                      # noqa: E402
from trading_system.ict_engine.htf import (                                        # noqa: E402
    CalendarAnchor,
    HigherTimeframe,
    htf_trace,
)
from trading_system.ict_engine.sessions import (                                   # noqa: E402
    CLOCK_VARIANTS,
    ClockDefinition,
    observe_session,
)

UTC = timezone.utc
BAR = timedelta(minutes=5)

# ----------------------------------------------------------------- declared numbers
# Every constant below is declared in DECLARED_CHOICES.md before this file existed.
WINDOW_BARS = 5760            # ENGINEERING_CHOICE (DECLARED_CHOICES row 1)
HTF_LOOKBACK_BARS = 2016      # ENGINEERING_CHOICE: 7 trading days, 4 daily buckets + the forming
                              # week, enough for htf_trace to expose one completed bucket of each
                              # timeframe without growing with the run
DISPLACEMENT_VARIANT = "V-D-01"    # SOURCE_NUMBER (claim F1 prints 60); DECLARED_CHOICES row 11
SWEEP_VARIANT = "V-E-00"           # SOURCE_NUMBER (E1/E3/E4/E5); DECLARED_CHOICES row 12
TRADING_CLOCK = ClockDefinition.EURO_0200_0500   # ENGINEERING_CHOICE; DECLARED_CHOICES row 10
MAX_POOLS = 64               # ENGINEERING_CHOICE: bounded container; older pools are dropped and
                             # the drop is counted, never silently forgotten
MAX_ZONES = 32               # ENGINEERING_CHOICE: same reason
MAX_SWINGS = 256             # ENGINEERING_CHOICE: same reason

_HEX = "0123456789abcdef"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ----------------------------------------------------------------- bar
@dataclass(frozen=True, slots=True)
class Bar:
    """One 5m bid/ask candle, labelled by its UTC bar start (decision-available at `end`)."""

    start: datetime
    bid_open: float
    bid_high: float
    bid_low: float
    bid_close: float
    bid_volume: float
    ask_open: float
    ask_high: float
    ask_low: float
    ask_close: float
    ask_volume: float
    spread_open: float
    spread_open_pips: float
    spread_high: float
    spread_high_pips: float
    spread_low: float
    spread_low_pips: float
    spread_close: float
    spread_close_pips: float

    def __post_init__(self) -> None:
        # malformed candles raise, never a silent repair
        for name in ("bid_open", "bid_high", "bid_low", "bid_close",
                     "ask_open", "ask_high", "ask_low", "ask_close"):
            value = getattr(self, name)
            if not isinstance(value, float) or value != value or value in (float("inf"), float("-inf")):
                raise ValueError(f"bar {self.start}: {name} is not a finite float")
        if self.bid_high < self.bid_low or self.ask_high < self.ask_low:
            raise ValueError(f"bar {self.start}: high is below low")
        if not (self.bid_low <= self.bid_open <= self.bid_high):
            raise ValueError(f"bar {self.start}: bid open outside its range")
        if not (self.bid_low <= self.bid_close <= self.bid_high):
            raise ValueError(f"bar {self.start}: bid close outside its range")
        if self.start.tzinfo is None:
            raise ValueError(f"bar {self.start}: timestamp has no timezone")

    @property
    def end(self) -> datetime:
        return self.start + BAR

    @property
    def mid_close(self) -> float:
        return (self.bid_close + self.ask_close) / 2.0

    def b1(self) -> B1Candle:
        return B1Candle(open=self.bid_open, high=self.bid_high,
                        low=self.bid_low, close=self.bid_close, closed=True)

    def ict(self) -> IctCandle:
        return IctCandle(
            start=self.start,
            bid_open=self.bid_open, bid_high=self.bid_high,
            bid_low=self.bid_low, bid_close=self.bid_close, bid_volume=self.bid_volume,
            ask_open=self.ask_open, ask_high=self.ask_high,
            ask_low=self.ask_low, ask_close=self.ask_close, ask_volume=self.ask_volume,
            spread_open=self.spread_open, spread_open_pips=self.spread_open_pips,
            spread_high=self.spread_high, spread_high_pips=self.spread_high_pips,
            spread_low=self.spread_low, spread_low_pips=self.spread_low_pips,
            spread_close=self.spread_close, spread_close_pips=self.spread_close_pips,
        )


# ----------------------------------------------------------------- loading
COLUMNS = (
    "Datetime", "BidOpen", "BidHigh", "BidLow", "BidClose", "BidVolume",
    "AskOpen", "AskHigh", "AskLow", "AskClose", "AskVolume",
    "SpreadOpen", "SpreadOpenPips", "SpreadHigh", "SpreadHighPips",
    "SpreadLow", "SpreadLowPips", "SpreadClose", "SpreadClosePips",
)


def load_bars(path: Path, t0: str, t1: str) -> list[Bar]:
    """Read the recorded annual file, drop closed-market placeholder rows, return [t0, t1).

    The placeholder rule is the one `run_forex_intraday_v1.load_bidask` declares (both sides flat and
    both volumes zero); it is a data-hygiene rule, not a market rule, and dropping those rows is what
    makes a single 5m series out of a 24h file.
    """

    import csv as _csv

    rows: list[Bar] = []
    with gzip.open(path, "rt", newline="") as fh:
        reader = _csv.DictReader(fh)
        missing = [c for c in COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{path.name}: missing columns {missing}")
        for raw in reader:
            stamp = datetime.fromisoformat(raw["Datetime"].replace("Z", "+00:00"))
            if stamp.tzinfo is None:
                raise ValueError("Datetime without timezone")
            if raw["BidOpen"] == raw["BidClose"] and raw["BidHigh"] == raw["BidLow"] \
                    and raw["AskOpen"] == raw["AskClose"] and raw["AskHigh"] == raw["AskLow"] \
                    and float(raw["BidVolume"]) == 0.0 and float(raw["AskVolume"]) == 0.0:
                continue
            rows.append(Bar(
                start=stamp,
                bid_open=float(raw["BidOpen"]), bid_high=float(raw["BidHigh"]),
                bid_low=float(raw["BidLow"]), bid_close=float(raw["BidClose"]),
                bid_volume=float(raw["BidVolume"]),
                ask_open=float(raw["AskOpen"]), ask_high=float(raw["AskHigh"]),
                ask_low=float(raw["AskLow"]), ask_close=float(raw["AskClose"]),
                ask_volume=float(raw["AskVolume"]),
                spread_open=float(raw["SpreadOpen"]), spread_open_pips=float(raw["SpreadOpenPips"]),
                spread_high=float(raw["SpreadHigh"]), spread_high_pips=float(raw["SpreadHighPips"]),
                spread_low=float(raw["SpreadLow"]), spread_low_pips=float(raw["SpreadLowPips"]),
                spread_close=float(raw["SpreadClose"]), spread_close_pips=float(raw["SpreadClosePips"]),
            ))
    rows.sort(key=lambda b: b.start)
    for earlier, later in zip(rows, rows[1:]):
        if later.start <= earlier.start:
            raise ValueError(f"duplicate or unordered bar at {later.start}")
    lo, hi = datetime.fromisoformat(t0).replace(tzinfo=UTC), datetime.fromisoformat(t1).replace(tzinfo=UTC)
    return [b for b in rows if lo <= b.start < hi]


# ----------------------------------------------------------------- bounded window
class Window:
    """A fixed-length causal buffer; pushing drops the oldest bar, never the newest."""

    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.bars: list[Bar] = []
        self.b1: list[B1Candle] = []
        self.ict: list[IctCandle] = []

    def __len__(self) -> int:
        return len(self.bars)

    def push(self, bar: Bar) -> None:
        # The Bar queue is strictly increasing (load_bars proves it), so a deque with a maxlen is
        # equivalent to a list + pop(0) but without the O(n) shift per bar.
        self.bars.append(bar)
        self.b1.append(bar.b1())
        self.ict.append(bar.ict())
        if len(self.bars) > self.capacity:
            drop = len(self.bars) - self.capacity
            del self.bars[:drop]
            del self.b1[:drop]
            del self.ict[:drop]

    @property
    def t(self) -> int:
        return len(self.bars) - 1


# ----------------------------------------------------------------- primitives on the current bar
def swing_now(window: Window) -> list[dict]:
    """Confirmed swings whose third candle is the current bar (both sides)."""

    out = []
    if len(window.b1) < 3:
        return out
    for side in ("high", "low"):
        rec = swing_at(window.b1, window.t, side)
        if rec.get("status") == "YES":
            idx = rec["candle_indices"]["c2"]
            price = rec["comparison"]["values"]["c2"]
            out.append({
                "side": side,
                "price": float(price),
                "level_index": idx,
                "confirm_index": rec["candle_indices"]["c3"],
                "version": rec["version"],
                "claim_ids": list(rec.get("source_ids", [])),
                "status": rec["status"],
            })
    return out


def fvg_now(window: Window) -> list[dict]:
    """Fair value gaps whose third candle is the current bar."""

    out = []
    if len(window.b1) < 3:
        return out
    for direction in ("bullish", "bearish"):
        rec = fvg_at(window.b1, window.t, direction)
        if rec.get("status") == "YES":
            bounds = rec["bounds"]
            out.append({
                "direction": direction,
                "lower": float(bounds["lower_bound"]["value"]),
                "upper": float(bounds["upper_bound"]["value"]),
                "level_index": rec["candle_indices"]["c3"],
                "version": rec["version"],
                "invalidation": "KNOWLEDGE_GAP: FVG_INVALIDATION",
                "gates": [g["id"] for g in rec.get("gates", [])],
            })
    return out


def displacement_now(window: Window) -> dict:
    try:
        rec = displacement_at(window.b1, window.t, DISPLACEMENT_VARIANT)
    except ValueError as exc:
        # c1 refuses a zero-range candle by design ("candle range is zero").  A bar whose bid
        # high equals its bid low is not malformed, so the absence is recorded, not repaired.
        if "candle range is zero" in str(exc):
            return {"status": "UNAVAILABLE_ZERO_RANGE", "answer": "NO",
                    "variant_id": DISPLACEMENT_VARIANT, "ratio": None,
                    "source_numbers": [], "claim_ids": [], "gaps": ["ZERO_RANGE_BAR"]}
        raise
    return {
        "status": rec.get("status"),
        "answer": rec.get("answer"),
        "variant_id": rec.get("variant_id"),
        "ratio": (rec.get("numbers") or {}).get("body_range_ratio"),
        "source_numbers": rec.get("source_numbers", []),
        "claim_ids": rec.get("claim_ids", []),
        "gaps": [g["id"] for g in rec.get("gaps", [])] + [g["id"] for g in rec.get("dimension_gaps", [])],
    }


def sweep_now(window: Window, side: str, level: float | None = None) -> dict:
    """V-E-00 at the current bar.

    `level` is the most recent V-A-00 swing, supplied by `SwingState` (the same level
    `latest_swing_reference` would resolve, but without its backward scan over the window).
    When it is None the module's own resolver is used, which is what the fixtures do.
    """

    if level is None:
        # no confirmed V-A-00 swing yet on this side: there is nothing to sweep, and the module's
        # own resolver raises in that state, so the absence is recorded instead of caught.
        return {"side": side, "status": "UNAVAILABLE_NO_SWING_LEVEL", "answer": "NO",
                "level": None, "level_basis": "none_yet", "level_index": None,
                "swing_index": None, "variant_id": SWEEP_VARIANT, "claim_ids": [],
                "numbers": {}}
    rec = sweep_at(window.b1, window.t, side, float(level), SWEEP_VARIANT)
    return {
        "side": side,
        "status": rec.get("status"),
        "answer": rec.get("answer"),
        "level": rec.get("level"),
        "level_basis": rec.get("level_basis"),
        "level_index": rec.get("level_candle_index"),
        "swing_index": rec.get("swing_index"),
        "variant_id": rec.get("variant_id"),
        "claim_ids": rec.get("claim_ids", []),
        "numbers": rec.get("numbers") or {},
    }


def session_now(bar: Bar) -> dict:
    candle = bar.ict()
    declared = next(v for v in CLOCK_VARIANTS if v.definition_id is TRADING_CLOCK)
    obs = observe_session(candle, declared)
    return {
        "declared_window": declared.definition_id.value,
        "in_window": obs.in_window,
        "killzone_label_allowed": obs.killzone_label_allowed,
        "local_bar_start": obs.local_bar_start.isoformat(),
        "market_status": obs.market_status.value if hasattr(obs.market_status, "value") else str(obs.market_status),
        "claim_ids": list(declared.claim_ids),
        "all_windows": {
            v.definition_id.value: observe_session(candle, v).in_window for v in CLOCK_VARIANTS
        },
    }


class HtfState:
    """Incremental daily/weekly aggregation (O(1) per bar).

    Semantics copied from ict_engine/htf.py: a bucket is exposed as **completed** only when a later
    bucket is observed, and its `available_at` is that later bucket's start.  `htf_trace` is the
    oracle that the fixtures compare this against.
    """

    def __init__(self) -> None:
        self.current: dict[str, dict] = {}
        self.completed: dict[str, dict] = {}
        self.available_at: dict[str, datetime] = {}

    @staticmethod
    def _keys(bar: Bar) -> dict[str, tuple]:
        iso = bar.start.isocalendar()
        return {"daily": (bar.start.year, bar.start.month, bar.start.day),
                "weekly": (iso[0], iso[1])}

    def push(self, bar: Bar) -> list[str]:
        rolled = []
        for tf, key in self._keys(bar).items():
            current = self.current.get(tf)
            if current is None or current["key"] != key:
                if current is not None:
                    self.completed[tf] = {**current, "available_at": bar.start.isoformat()}
                    self.available_at[tf] = bar.start
                    rolled.append(tf)
                self.current[tf] = {"key": key, "open": bar.bid_open, "high": bar.bid_high,
                                    "low": bar.bid_low, "close": bar.bid_close,
                                    "bucket_start": bar.start.isoformat()}
            else:
                current["high"] = max(current["high"], bar.bid_high)
                current["low"] = min(current["low"], bar.bid_low)
                current["close"] = bar.bid_close
        return rolled

    def view(self) -> dict:
        out = {"daily": None, "weekly": None}
        for tf, done in self.completed.items():
            out[tf] = {"bucket_start": done["bucket_start"],
                       "open": done["open"], "high": done["high"],
                       "low": done["low"], "close": done["close"],
                       "available_at": done["available_at"],
                       "bias": ("UP" if done["close"] > done["open"]
                                else "DOWN" if done["close"] < done["open"] else "FLAT")}
        return out


def htf_now(window: Window) -> dict:
    """Last completed daily and weekly bucket, from a bounded HTF lookback."""

    if len(window.ict) < 2:
        return {"daily": None, "weekly": None}
    tail = window.ict[-min(len(window.ict), HTF_LOOKBACK_BARS):]
    out = {"daily": None, "weekly": None}
    for key, timeframe in (("daily", HigherTimeframe.DAILY), ("weekly", HigherTimeframe.WEEKLY)):
        trace = htf_trace(tail, timeframe, CalendarAnchor.UTC)
        completed = None
        for state in reversed(trace):
            if state.last_completed is not None and state.available_at <= window.bars[-1].end:
                completed = state.last_completed
                break
        if completed is not None:
            out[key] = {
                "bucket_start": completed.bucket_start.isoformat(),
                "bucket_end": completed.bucket_end.isoformat(),
                "open": completed.bid_open,
                "high": completed.bid_high,
                "low": completed.bid_low,
                "close": completed.bid_close,
                "bias": ("UP" if completed.bid_close > completed.bid_open
                         else "DOWN" if completed.bid_close < completed.bid_open else "FLAT"),
            }
    return out


# ----------------------------------------------------------------- bounded state
@dataclass(slots=True)
class Swing:
    side: str
    price: float
    level_index: int
    confirm_index: int


class SwingState:
    def __init__(self) -> None:
        self.swings: list[Swing] = []
        self.dropped = 0

    def push(self, found: list[dict]) -> None:
        for item in found:
            self.swings.append(Swing(item["side"], item["price"],
                                     item["level_index"], item["confirm_index"]))
        while len(self.swings) > MAX_SWINGS:
            self.swings.pop(0)
            self.dropped += 1

    def last(self, side: str) -> Swing | None:
        for swing in reversed(self.swings):
            if swing.side == side:
                return swing
        return None


class DealingRangeState:
    """Latest alternating confirmed swings (definition id copied from ict_engine/ranges.py)."""

    DEFINITION_ID = "ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS"

    def compute(self, swings: SwingState, close: float) -> dict:
        high, low = swings.last("high"), swings.last("low")
        if high is None or low is None or high.price <= low.price:
            return {"position": "undefined", "definition_id": self.DEFINITION_ID,
                    "reason": "need one confirmed swing on each side, high above low"}
        equilibrium = (high.price + low.price) / 2.0
        if close > equilibrium:
            position = "premium"
        elif close < equilibrium:
            position = "discount"
        else:
            position = "equilibrium"
        return {
            "position": position,
            "definition_id": self.DEFINITION_ID,
            "low": low.price, "high": high.price, "equilibrium": equilibrium,
            "low_index": low.level_index, "high_index": high.level_index,
            "position_ratio": (close - low.price) / (high.price - low.price),
        }


class LiquidityState:
    """Pool lifecycle with the vocabulary of ict_engine/liquidity.py.

    Kinds: `old_extreme` (every confirmed swing), `relative_equal_pair` (a confirmed swing paired with
    the previous same-side swing — the batch module forms these *without an equality cutoff*, and this
    class does the same), `higher_timeframe_extreme` (last completed daily bucket high/low).
    Events: `formed`, `taken`.
    """

    def __init__(self) -> None:
        self.pools: list[dict] = []
        self.dropped = 0
        self._next = 0

    def _add(self, pool: dict) -> None:
        pool["pool_id"] = f"pool:{pool['side']}:{pool['kind']}:{pool['formed_index']}:{pool['level']:.8f}"
        self.pools.append(pool)
        while len(self.pools) > MAX_POOLS:
            self.pools.pop(0)
            self.dropped += 1

    def push_swings(self, found: list[dict], swings: SwingState) -> None:
        for item in found:
            side, level, index = item["side"], item["price"], item["confirm_index"]
            self._add({"side": side, "kind": "old_extreme", "level": level,
                       "formed_index": index, "member_levels": [level], "state": "formed",
                       "taken_index": None})
            previous = None
            for swing in reversed(swings.swings[:-1]):
                if swing.side == side:
                    previous = swing
                    break
            if previous is not None:
                ratio = (max(previous.price, level) - min(previous.price, level))
                self._add({"side": side, "kind": "relative_equal_pair", "level": level,
                           "formed_index": index, "member_levels": [previous.price, level],
                           "state": "formed", "taken_index": None,
                           "equality_ratio": ratio,
                           "equal_highs_ratio": "KNOWLEDGE_GAP: EQUAL_HIGHS_RATIO"})

    def push_htf(self, htf: dict) -> None:
        daily = htf.get("daily")
        if not daily:
            return
        for side, level in (("high", daily["high"]), ("low", daily["low"])):
            key = (side, level)
            if any(p["kind"] == "higher_timeframe_extreme" and p["level"] == level
                   and p["side"] == side for p in self.pools):
                continue
            self._add({"side": side, "kind": "higher_timeframe_extreme", "level": level,
                       "formed_index": -1, "member_levels": [level], "state": "formed",
                       "taken_index": None, "bucket_start": daily["bucket_start"]})

    def push_bar(self, bar: Bar, index: int) -> None:
        for pool in self.pools:
            if pool["state"] != "formed":
                continue
            if pool["side"] == "high" and bar.bid_high >= pool["level"]:
                pool["state"] = "taken"
                pool["taken_index"] = index
            elif pool["side"] == "low" and bar.bid_low <= pool["level"]:
                pool["state"] = "taken"
                pool["taken_index"] = index

    def untaken(self, side: str) -> list[dict]:
        live = [p for p in self.pools if p["state"] == "formed" and p["side"] == side]
        # one level may appear as both old_extreme and relative_equal_pair: keep the first
        seen, out = set(), []
        for pool in reversed(live):
            key = round(pool["level"], 8)
            if key in seen:
                continue
            seen.add(key)
            out.append(pool)
        return out

    def taken(self) -> list[dict]:
        return [p for p in self.pools if p["state"] == "taken"]


class GapState:
    """FVG zones, with a mechanical touched/closed-through status (invalidation stays a gap)."""

    def __init__(self) -> None:
        self.zones: list[dict] = []
        self.dropped = 0

    def push(self, found: list[dict], index: int) -> None:
        for gap in found:
            gap = dict(gap)
            gap["formed_index"] = index
            gap["state"] = "untouched"
            self.zones.append(gap)
        while len(self.zones) > MAX_ZONES:
            self.zones.pop(0)
            self.dropped += 1

    def push_bar(self, bar: Bar) -> None:
        for zone in self.zones:
            if zone["state"] in ("closed_through", "invalidated"):
                continue
            if zone["direction"] == "bullish":
                if bar.bid_low <= zone["lower"] and bar.bid_close < zone["lower"]:
                    zone["state"] = "closed_through"
                elif bar.bid_low <= zone["upper"]:
                    zone["state"] = "touched"
            else:
                if bar.bid_high >= zone["upper"] and bar.bid_close > zone["upper"]:
                    zone["state"] = "closed_through"
                elif bar.bid_high >= zone["lower"]:
                    zone["state"] = "touched"

    def active(self, direction: str) -> list[dict]:
        return [z for z in self.zones if z["direction"] == direction and z["state"] != "closed_through"]


class OrderBlockState:
    """Order blocks created by a displacement, evaluated by c1_catalog.order_block_at.

    The caller-side arguments are the module's own printed reference variants
    (boundaries=FULL_RANGE, mean_threshold_basis=BODY, invalidation=FAR_EDGE) and the four
    prerequisite switches with the evidence this build actually has.
    """

    def __init__(self) -> None:
        self.blocks: list[dict] = []
        self.dropped = 0

    def maybe_create(self, window: Window, displacement: dict, direction: str,
                     fvg_below: bool, sweep_evidence: bool, structure_break: bool) -> dict | None:
        if displacement.get("answer") != "YES":
            return None
        prerequisites = {
            PREREQ_STRUCTURE_BREAK: {"on": True, "evidence": structure_break},
            PREREQ_FVG: {"on": True, "evidence": fvg_below},
            PREREQ_SWEEP: {"on": True, "evidence": sweep_evidence},
            PREREQ_UNMITIGATED: {"on": False},
        }
        rec = order_block_at(
            window.b1, window.t, direction,
            boundaries=BOUNDARY_FULL_RANGE,
            mean_threshold_basis=MT_BODY,
            entry_level=ENTRY_MEAN_THRESHOLD,
            invalidation=INVALID_FAR_EDGE,
            prerequisites=prerequisites,
        )
        numbers = rec.get("numbers") or {}
        if rec.get("verdict") not in ("VALID", "INVALIDATED") or "zone_low" not in numbers:
            return None
        block = {
            "direction": direction,
            "verdict": rec["verdict"],
            "block_index": rec["block_index"],
            "displacement_start_index": rec["displacement_start_index"],
            "lower": float(numbers["zone_low"]),
            "upper": float(numbers["zone_high"]),
            "mean_threshold": float(numbers.get("mean_threshold", numbers["zone_low"])),
            "invalidation": rec.get("invalidation"),
            "variant_ids": rec.get("variant_ids", {}),
            "claim_ids": rec.get("claim_ids", []),
            "formed_index": window.t,
            "state": "valid" if rec["verdict"] == "VALID" else "invalidated",
        }
        self.blocks.append(block)
        while len(self.blocks) > MAX_ZONES:
            self.blocks.pop(0)
            self.dropped += 1
        return block

    def push_bar(self, bar: Bar) -> None:
        for block in self.blocks:
            if block["state"] != "valid":
                continue
            if block["direction"] == "bullish" and bar.bid_close < block["lower"]:
                block["state"] = "invalidated"
            elif block["direction"] == "bearish" and bar.bid_close > block["upper"]:
                block["state"] = "invalidated"

    def valid(self, direction: str) -> list[dict]:
        return [b for b in self.blocks if b["state"] == "valid" and b["direction"] == direction]


def structure_shift(bar: Bar, swings: SwingState, displacement: dict) -> dict:
    """A close beyond the most recent confirmed opposing swing (DECLARED_CHOICES row 15)."""

    high, low = swings.last("high"), swings.last("low")
    shift = None
    if high is not None and bar.bid_close > high.price:
        shift = {"direction": "UP", "level": high.price, "level_index": high.level_index}
    elif low is not None and bar.bid_close < low.price:
        shift = {"direction": "DOWN", "level": low.price, "level_index": low.level_index}
    return {
        "shift": shift,
        "with_displacement": bool(shift and displacement.get("answer") == "YES"),
        "qualification": "KNOWLEDGE_GAP: STRUCTURE_SHIFT_QUALIFICATION",
    }


def memory_rss_kb() -> int | None:
    """Current RSS in kB, read from /proc (no psutil in this container)."""

    try:
        with open("/proc/self/status", "r", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1])
    except OSError:
        return None
    return None


def memory_total_kb() -> int | None:
    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("MemTotal:"):
                    return int(line.split()[1])
    except OSError:
        return None
    return None


def peak_rss_kb() -> int | None:
    try:
        with open("/proc/self/status", "r", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("VmHWM:"):
                    return int(line.split()[1])
    except OSError:
        return None
    return None
