#!/usr/bin/env python3
"""The scalp pattern: S -> R -> FVG -> H, the plan it produces, and its path on 5m.

Every rule here is quoted in DECLARED_CHOICES_SCALP.md with its tag.  Nothing is tuned; the
sensitivity variants exist to be REPORTED and can never be chosen after a result.
"""

from __future__ import annotations

import math
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[0] / "b1_candles"))
import scalp_sweep as SW                      # frozen detector, imported
import fvg as FV                              # frozen B1 FVG detector, imported

NY = ZoneInfo("America/New_York")
WARMUP_15M = 40           # ENGINEERING_CHOICE
LOOKBACK_RANGE = 20       # ENGINEERING_CHOICE
BUFFER_FRACTION = 0.0002  # SOURCE_NUMBER: OWNER_SPEC, "0.02% of price"
WINDOW_BARS_5M = 288      # ENGINEERING_CHOICE: one trading day of 5m bars
WINDOW_PRIMARY = (1, 2, 3)
WINDOW_SECONDARY = (1, 2)
M_CONTROL = 5
SEED = 20261109
EXCLUSION_HOURS = 2
SUB_PIP = 1.0


def percentile(values: list[float], p: float) -> float:
    """Nearest-rank percentile (declared): the ceil(p% * n)-th smallest value."""

    if not values:
        raise ValueError("percentile of an empty list")
    ordered = sorted(values)
    rank = max(1, math.ceil(p / 100.0 * len(ordered)))
    return ordered[min(rank, len(ordered)) - 1]


def true_range(candle: dict) -> float:
    return candle["high"] - candle["low"]


def body(candle: dict) -> float:
    return abs(candle["close"] - candle["open"])


def is_large(candles: list[dict], index: int, mode: str = "L-RANGE") -> bool:
    """The declared 'large' definitions; all relative to the 20 candles before R."""

    if index < LOOKBACK_RANGE:
        return False
    prior = candles[index - LOOKBACK_RANGE:index]
    if mode == "L-RANGE":
        return true_range(candles[index]) >= percentile([true_range(c) for c in prior], 80)
    if mode == "L-BODY":
        return body(candles[index]) >= percentile([body(c) for c in prior], 80)
    if mode == "L-LOOSE":
        return true_range(candles[index]) >= percentile([true_range(c) for c in prior], 50)
    raise ValueError(f"unknown large mode {mode}")


def to_b1(candles: list[dict]):
    from candle import Candle
    return [Candle(open=c["open"], high=c["high"], low=c["low"], close=c["close"], closed=True)
            for c in candles]


def mirrored(candles: list[dict]) -> list[dict]:
    """Exact mirror (price negation with high/low swapped) so shorts reuse the long detector."""

    out = []
    for c in candles:
        out.append({**c, "open": -c["open"], "high": -c["low"], "low": -c["high"], "close": -c["close"]})
    return out


def events(candles: list[dict], *, side: str = "long", variant: str = "1A",
           large_mode: str = "L-RANGE", window: tuple[int, ...] = WINDOW_PRIMARY,
           half_level: str = "range") -> list[dict]:
    """All valid patterns, one per S candle (the FIRST valid H), causal at the H close."""

    work = candles if side == "long" else mirrored(candles)
    b1 = to_b1(work)
    sweeps = SW.sweep_events(b1, "long")          # mirrored shorts are long events on negated prices
    out, ignored = [], 0
    for sweep in sweeps:
        s_index = sweep["index"]
        if s_index < WARMUP_15M:
            continue
        found = None
        for r_index in (s_index, s_index + 1, s_index + 2):
            h_index = r_index + (1 if variant == "1A" else 2)
            if h_index > s_index + 3 or h_index >= len(work) or r_index >= len(work):
                continue
            r, h = work[r_index], work[h_index]
            if not (r["close"] > r["open"]):
                continue
            if not is_large(work, r_index, large_mode):
                continue
            if not (h["close"] < h["open"]):
                continue
            if variant == "1B" and not (work[r_index + 1]["close"] > work[r_index + 1]["open"]):
                continue
            if half_level == "range":
                half = r["low"] + 0.5 * (r["high"] - r["low"])
            elif half_level == "body":
                half = min(r["open"], r["close"]) + 0.5 * abs(r["close"] - r["open"])
            else:
                raise ValueError(f"unknown H half level {half_level}")
            if not (h["low"] > half):
                continue
            fvg_check = FV.fvg_at(b1, r_index + 1, FV.DIR_BULLISH)
            fvg = fvg_check["status"] == FV.STATUS_YES
            found = {"s_index": s_index, "r_index": r_index, "h_index": h_index,
                     "form": 1 if fvg else 2, "fvg": fvg, "variant": variant,
                     "swept_low": sweep["swing_price"], "swing_candle_index": sweep["swing_candle_index"],
                     "h_low": h["low"], "r_half": half, "half_level": half_level,
                     "entry_index_5m": None}
            break
        if found is None:
            continue
        # a later H for the same S is not a second thesis
        later = 0
        for r_index in (s_index, s_index + 1, s_index + 2):
            h_index = r_index + (1 if variant == "1A" else 2)
            if h_index <= found["h_index"] or h_index > s_index + 3 or h_index >= len(work):
                continue
            later += 1
        ignored += later
        if found["h_index"] not in [s_index + k for k in window]:
            continue
        out.append({**found, "later_h_ignored": later})
    return out


def target_for(candles: list[dict], event: dict, side: str = "long") -> dict | None:
    """The last confirmed swing high BEFORE the swept swing low (mirrored for shorts).

    Shorts are detected on negated prices, so the level found there is negated back to the real price.
    """

    work = candles if side == "long" else mirrored(candles)
    b1 = to_b1(work)
    upto = event["swing_candle_index"] - 1
    if upto < 2:
        return None
    highs = SW.confirmed_swings(b1, upto, "high")
    if not highs:
        return None
    level = highs[-1]
    price = level["price"] if side == "long" else -level["price"]
    return {"level": price, "candle_index": level["candle_index"],
            "confirmed_at": level["confirm_index"]}


def target_state(entry: float, target: float) -> str:
    """OWNER_SPEC: a target at or behind the entry is rejected and counted."""

    return "TARGET_BEHIND_ENTRY" if target <= entry else "OK"


def build_plan(candles: list[dict], event: dict, *, side: str = "long") -> dict:
    """Entry at the H close on the ask, stop under H's low, target at the swing high, both buffered."""

    h = candles[event["h_index"]]
    # mirror of "buy on ask": a short sells on the bid.  Exits are mirrored too (see simulate()).
    entry = h["ask_close"] if side == "long" else h["close"]
    buffer_price = BUFFER_FRACTION * entry
    stop = (h["low"] - buffer_price) if side == "long" else (h["high"] + buffer_price)
    tgt = target_for(candles, event, side)
    plan = {"side": side, "s_index": event["s_index"], "r_index": event["r_index"],
            "h_index": event["h_index"], "form": event["form"], "variant": event["variant"],
            "fvg": event["fvg"], "swept_low": event["swept_low"],
            "r_half": event["r_half"], "entry_index_5m": h["last_bar"] + 1,
            "entry": entry, "buffer": buffer_price, "stop": stop,
            "target": None, "target_source": None,
            "risk": (entry - stop) if side == "long" else (stop - entry),
            "target_candle_index": None, "target_confirmed_at": None,
            "excluded": None}
    if tgt is None:
        plan["excluded"] = "NO_TARGET_SWING"
        return plan
    target = (tgt["level"] - buffer_price) if side == "long" else (tgt["level"] + buffer_price)
    plan.update({"target": target, "target_source": tgt, "target_candle_index": tgt["candle_index"],
                 "target_confirmed_at": tgt["confirmed_at"]})
    behind = (target <= entry) if side == "long" else (target >= entry)
    if behind:
        plan["excluded"] = "TARGET_BEHIND_ENTRY"
        return plan
    plan["rr"] = (abs(target - entry) / plan["risk"]) if plan["risk"] > 0 else None
    plan["stop_pips"] = plan["risk"] * 10000.0
    if plan["stop_pips"] < SUB_PIP:
        plan["sub_pip"] = True
    return plan


def simulate(plan: dict, bars: list, *, entry_price: float | None = None,
             entry_index: int | None = None) -> dict:
    """Forward path on 5m bars: stop first when both levels sit inside one bar."""

    entry = plan["entry"] if entry_price is None else entry_price
    start = plan["entry_index_5m"] if entry_index is None else entry_index
    stop, target = plan["stop"], plan["target"]
    short = plan.get("side") == "short"
    risk = (stop - entry) if short else (entry - stop)
    ambiguous = 0
    max_adverse = 0.0
    reached_half = False
    for j in range(start, min(start + WINDOW_BARS_5M, len(bars))):
        bar = bars[j]
        # long exits on the bid, short exits on the ask (mirror of the entry side)
        hit_stop = (bar.ask_high >= stop) if short else (bar.bid_low <= stop)
        hit_target = (bar.ask_low <= target) if short else (bar.bid_high >= target)
        half_target = (entry + (target - entry) / 2.0)
        hit_half = (bar.ask_low <= half_target) if short else (bar.bid_high >= half_target)
        adverse = (bar.ask_high - entry) if short else (entry - bar.bid_low)
        max_adverse = max(max_adverse, adverse) if j > start else max(0.0, adverse)
        if hit_stop and hit_target:
            ambiguous += 1
            exit_reason = "stop"
        elif hit_stop:
            exit_reason = "stop"
        elif hit_target:
            exit_reason = "target"
        else:
            exit_reason = None
        # Conservative ordering when the same 5m bar touches the stop and halfway mark.
        if exit_reason == "stop":
            return {"state": "settled", "exit_reason": "stop", "exit_index": j,
                    "exit_price": stop, "r": -1.0, "ambiguous_bars": ambiguous,
                    "bars_held": j - start + 1, "mae_r": max(0.0, max_adverse) / risk,
                    "bars_to_target": None, "reached_half_target": reached_half}
        if hit_half:
            reached_half = True
        if exit_reason == "target":
            r_target = ((entry - target) if short else (target - entry)) / risk
            return {"state": "settled", "exit_reason": "target", "exit_index": j,
                    "exit_price": target, "r": r_target, "ambiguous_bars": ambiguous,
                    "bars_held": j - start + 1, "mae_r": max(0.0, max_adverse) / risk,
                    "bars_to_target": j - start + 1, "reached_half_target": True}
    return {"state": "expired", "exit_reason": "expired", "exit_index": None, "exit_price": None,
            "r": 0.0, "ambiguous_bars": ambiguous, "bars_held": WINDOW_BARS_5M,
            "mae_r": max(0.0, max_adverse) / risk if risk > 0 else None,
            "bars_to_target": None, "reached_half_target": reached_half}


def excess_hit(plan: dict, outcome: dict) -> float | None:
    if plan.get("rr") in (None, 0):
        return None
    hit = 1 if outcome.get("exit_reason") == "target" else 0
    return hit - 1.0 / (1.0 + plan["rr"])


def ny_hour(moment: datetime) -> int:
    return moment.astimezone(NY).hour

# What this does NOT establish: it does not establish strategy validity or profitability.
