#!/usr/bin/env python3
"""Strict-window loader and causal 15m aggregation.

The loader filters the CSV by timestamp BEFORE a Bar is constructed, so a forbidden month is never
materialised (DECLARED_CHOICES_SCALP §1).
"""

from __future__ import annotations

import csv
import gzip
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_V1 = Path(__file__).resolve().parents[3] / "ict_recipe_v1" / "build_v1"   # docs/research/ict_recipe_v1/build_v1
if str(_V1) not in sys.path:
    sys.path.insert(0, str(_V1))

DATA = Path("/tmp/hud_data/2021.csv.gz")
DATA_SHA256 = "38be0503fd56269686a6f3d25f5e537e2ac5682ea9a5d79af1765acd224a6ab4"
UTC = timezone.utc
FORBIDDEN = ("2021-03", "2021-08", "2021-12")
ALLOWED = ("2021-06", "2021-07", "2021-09", "2021-10", "2021-11")
FRAME_15M = 15


def _bar_from_row(row: dict):
    from stream_v1 import Bar        # import only: the Bar dataclass is not copied
    sp = float(row["SpreadOpen"])
    return Bar(start=datetime.fromisoformat(row["Datetime"].replace("Z", "+00:00")),
               bid_open=float(row["BidOpen"]), bid_high=float(row["BidHigh"]),
               bid_low=float(row["BidLow"]), bid_close=float(row["BidClose"]),
               bid_volume=float(row["BidVolume"]), ask_open=float(row["AskOpen"]),
               ask_high=float(row["AskHigh"]), ask_low=float(row["AskLow"]),
               ask_close=float(row["AskClose"]), ask_volume=float(row["AskVolume"]),
               spread_open=sp, spread_open_pips=float(row["SpreadOpenPips"]),
               spread_high=float(row["SpreadHigh"]), spread_high_pips=float(row["SpreadHighPips"]),
               spread_low=float(row["SpreadLow"]), spread_low_pips=float(row["SpreadLowPips"]),
               spread_close=float(row["SpreadClose"]), spread_close_pips=float(row["SpreadClosePips"]))


def load_window(t0: str, t1: str, path: Path = DATA) -> tuple[list, dict]:
    """Bars with t0 <= start < t1, and nothing else constructed."""

    lo = datetime.fromisoformat(t0).replace(tzinfo=UTC)
    hi = datetime.fromisoformat(t1).replace(tzinfo=UTC)
    if lo >= hi:
        raise ValueError("empty window")
    requested_months = {lo.strftime("%Y-%m"), (hi - timedelta(microseconds=1)).strftime("%Y-%m")}
    blocked = requested_months.intersection(FORBIDDEN)
    if blocked:
        raise ValueError(f"forbidden month window: {sorted(blocked)}")
    if not requested_months.issubset(ALLOWED):
        raise ValueError(f"window outside allowed exploratory months: {sorted(requested_months)}")
    bars, seen_months = [], set()
    with gzip.open(path, "rt", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            stamp_text = row["Datetime"]
            stamp = datetime.fromisoformat(stamp_text.replace("Z", "+00:00"))
            if stamp < lo:
                continue
            if stamp >= hi:
                break                      # the file is ordered; nothing past hi is read
            month = stamp.strftime("%Y-%m")
            if month in FORBIDDEN:
                raise ValueError(f"forbidden timestamp encountered before Bar construction: {month}")
            bars.append(_bar_from_row(row))
            seen_months.add(month)
    loaded_until = bars[-1].start.isoformat() if bars else None
    return bars, {"loaded_from": lo.isoformat(), "loaded_until": loaded_until,
                  "window_end_exclusive": hi.isoformat(),
                  "months_loaded": sorted(seen_months),
                  "reserved_months_loaded": sorted(seen_months.intersection(FORBIDDEN))}


def aggregate_15m(bars: list) -> list[dict]:
    """Causal 15m candles; a candle is usable only after its last 5m bar has closed."""

    candles, cur = [], None
    for index, bar in enumerate(bars):
        minute = (bar.start.minute // FRAME_15M) * FRAME_15M
        key = bar.start.replace(minute=minute, second=0, microsecond=0)
        if cur is None or cur["start"] != key:
            if cur is not None:
                candles.append(cur)
            cur = {"start": key, "end": key + timedelta(minutes=FRAME_15M),
                   "open": bar.bid_open, "high": bar.bid_high, "low": bar.bid_low,
                   "close": bar.bid_close, "ask_open": bar.ask_open, "ask_close": bar.ask_close,
                   "spread_open": bar.spread_open, "first_bar": index, "last_bar": index}
        else:
            cur["high"] = max(cur["high"], bar.bid_high)
            cur["low"] = min(cur["low"], bar.bid_low)
            cur["close"] = bar.bid_close
            cur["ask_close"] = bar.ask_close
            cur["spread_open"] = bar.spread_open
            cur["last_bar"] = index
    if cur is not None:
        candles.append(cur)
    return candles

# What this does NOT establish: it does not establish strategy validity or HYPOTHETICAL_ profitability.
