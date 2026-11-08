"""Fair value gap — TIER2 third-party definition.

Rule text: BUILD_STEP_B1_DESIGN_V2.md §5.3 with CORRECTIONS_R3 (d).
Nothing here is attributed to any person; tier TIER2, source ids printed.

Strict comparisons only, wick to wick:
  bullish gap: low(c3)  > high(c1)
  bearish gap: high(c3) < low(c1)
  equality    -> UNDECIDED (touch gap)
  otherwise   -> NO

Bounds are printed as named relations, not as levels of any kind.
Invalidation is NOT computed: the design text has no reference for it, so every
result carries the gate INVALIDATION_UNDECIDED. No threshold, no ratio, no
default. No lookahead: a call at index t slices candles[:t+1].
"""

from __future__ import annotations

TIER = "TIER2"
VERSION = "V-B-00"
SOURCE_IDS = ("B1", "B2", "B3", "B4")

# Structural count stated by the sources: the gap spans three consecutive candles.
GAP_CANDLES = 3  # SOURCE_NUMBER, sources B1, B2, B3, B4

STATUS_YES = "YES"
STATUS_NO = "NO"
STATUS_UNDECIDED = "UNDECIDED"

GAP_TOUCH_FVG = {
    "id": "GAP_TOUCH_FVG",
    "text": "ما حكم تلامس الحدين بلا تداخل (المساواة بالضبط)؟",
}

GATE_INVALIDATION = {
    "id": "INVALIDATION_UNDECIDED",
    "text": "الإبطال غير محدَّد في المرجع (D2 بلا مرجع)",
}

DIR_BULLISH = "bullish"
DIR_BEARISH = "bearish"


def fvg_at(candles, t: int, direction: str) -> dict:
    """Evaluate a fair value gap whose third candle is at index `t`.

    Reads only candles[:t+1]. c1 = t-2, c2 = t-1, c3 = t.
    """

    if direction not in (DIR_BULLISH, DIR_BEARISH):
        raise ValueError("direction must be 'bullish' or 'bearish'")
    if not isinstance(t, int) or isinstance(t, bool):
        raise ValueError("index t must be an int")
    if t < 2:
        raise ValueError("index t must be at least 2 (three candles needed)")
    if t >= len(candles):
        raise ValueError("index t is outside the candle list")

    window = candles[: t + 1]  # no lookahead by construction
    c1, c2, c3 = window[t - 2], window[t - 1], window[t]

    open_gaps = []
    if direction == DIR_BULLISH:
        first, third = c1.high, c3.low
        if third > first:
            status = STATUS_YES
            bounds = {
                "lower_bound": {"relation": "high(c1)", "value": first},
                "upper_bound": {"relation": "low(c3)", "value": third},
            }
        elif third == first:
            status = STATUS_UNDECIDED
            bounds = None
            open_gaps.append(dict(GAP_TOUCH_FVG))
        else:
            status = STATUS_NO
            bounds = None
    else:
        first, third = c1.low, c3.high
        if third < first:
            status = STATUS_YES
            bounds = {
                "upper_bound": {"relation": "low(c1)", "value": first},
                "lower_bound": {"relation": "high(c3)", "value": third},
            }
        elif third == first:
            status = STATUS_UNDECIDED
            bounds = None
            open_gaps.append(dict(GAP_TOUCH_FVG))
        else:
            status = STATUS_NO
            bounds = None

    return {
        "concept": "fvg_bullish" if direction == DIR_BULLISH else "fvg_bearish",
        "candle_indices": {"c1": t - 2, "c2": t - 1, "c3": t},
        "version": VERSION,
        "tier": TIER,
        "source_ids": list(SOURCE_IDS),
        "status": status,
        "labels": [],
        "open_gaps": open_gaps,
        "gates": [dict(GATE_INVALIDATION)],
        "bounds": bounds,
        "comparison": {
            "first_wick": first,
            "third_wick": third,
            "relation": "low(c3) vs high(c1)" if direction == DIR_BULLISH else "high(c3) vs low(c1)",
        },
    }
