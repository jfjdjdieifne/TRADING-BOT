#!/usr/bin/env python3
"""The S candle of the owner strategy, on a 15m frame, causally.

SOURCE_NUMBER: OWNER_SPEC — "S = sweep candle: its low is below a previous swing low (reuse the
existing swing detector) and its CLOSE is back above that swing low."

The swing detector is the existing one (`b1_candles/swing.py`, NEIGHBOURS_EACH_SIDE = 1, TIER2); it is
imported, never copied.  At candle i only candles[:i+1] are read, and only swings whose confirming
candle is at or before i-1 are used, so a swing can never be confirmed by the sweep candle itself.

Everything downstream of S (form 1, form 2, hammer, entry, stop, targets) is NOT implemented: those
rules were not part of the received text.  Nothing here guesses them.
"""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ENGINE = _HERE.parent
for _p in (str(_ENGINE / "b1_candles"), str(_ENGINE / "c1_catalog")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from candle import Candle                                          # noqa: E402  b1_candles
from swing import swing_at, SIDE_HIGH, SIDE_LOW                    # noqa: E402

WINDOW_PRIMARY = (1, 2, 3)      # SOURCE_NUMBER: OWNER_SPEC, "entry candle closes within 3 candles after S"
WINDOW_SECONDARY = (1, 2)       # SOURCE_NUMBER: OWNER_SPEC, "also report window 2 separately"


def as_candles(rows: list[list[float]]) -> list[Candle]:
    """[open, high, low, close] rows -> closed candles.  Malformed rows raise, never repair."""

    out = []
    for i, row in enumerate(rows):
        if len(row) != 4:
            raise ValueError(f"row {i}: expected open/high/low/close")
        o, h, l, c = (float(x) for x in row)
        if not (l <= o <= h and l <= c <= h):
            raise ValueError(f"row {i}: OHLC outside its own range")
        out.append(Candle(open=o, high=h, low=l, close=c, closed=True))
    return out


def confirmed_swings(candles: list[Candle], upto: int, side: str) -> list[dict]:
    """Swings confirmed at or before candle `upto`, causally.

    `swing_at` reads candles[:t+1] and places the candidate at t-1, so the confirming candle is t.
    """

    found = []
    for t in range(2, min(upto, len(candles) - 1) + 1):
        rec = swing_at(candles, t, side)
        if rec.get("status") == "YES":
            found.append({"confirm_index": t, "candle_index": t - 1,
                          "price": float(rec["comparison"]["values"]["c2"]),
                          "claim_ids": list(rec.get("source_ids", []))})
    return found


def sweep_events(candles: list[Candle], side: str = "long") -> list[dict]:
    """Every S candle, defined exactly as the owner spec states it.

    long:  candle.low  < previous confirmed swing low,  candle.close > that swing low
    short: candle.high > previous confirmed swing high, candle.close < that swing high
    """

    swing_side = SIDE_LOW if side == "long" else SIDE_HIGH
    events = []
    for i, candle in enumerate(candles):
        if i < 3:
            continue
        prior = [s for s in confirmed_swings(candles, i - 1, swing_side) if s["confirm_index"] <= i - 1]
        if not prior:
            continue
        level = prior[-1]
        if side == "long":
            if candle.low < level["price"] and candle.close > level["price"]:
                events.append({"index": i, "side": side, "swing_price": level["price"],
                               "swing_candle_index": level["candle_index"],
                               "swing_confirmed_at": level["confirm_index"],
                               "low": candle.low, "high": candle.high, "close": candle.close})
        else:
            if candle.high > level["price"] and candle.close < level["price"]:
                events.append({"index": i, "side": side, "swing_price": level["price"],
                               "swing_candle_index": level["candle_index"],
                               "swing_confirmed_at": level["confirm_index"],
                               "low": candle.low, "high": candle.high, "close": candle.close})
    return events


def entry_window(s_index: int, window: tuple[int, ...]) -> list[int]:
    """The candle indices allowed to hold the entry candle, relative to S."""

    return [s_index + k for k in window]
