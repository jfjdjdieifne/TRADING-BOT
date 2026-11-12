"""Swing high / swing low — TIER2 third-party definition.

Rule text: BUILD_STEP_B1_DESIGN_V2.md §4.3 with CORRECTIONS_R3 (a) and (b).
Nothing here is attributed to any person; the tier is TIER2 and the source
identifiers are printed with every result.

Decision order (fixed by the design text, do not reorder):
  1. any neighbour strictly beyond the middle candle on the relevant side -> NO
  2. any neighbour equal to the middle candle on the relevant side      -> UNDECIDED
  3. third candle not closed                                            -> PENDING
  4. otherwise                                                          -> YES

Relevant side: wick extreme only. high for a swing high, low for a swing low.
No body comparison, no ratio, no threshold, no default.

No lookahead: a call at index t slices the list to candles[:t+1].
"""

from __future__ import annotations

from candle import Candle

TIER = "TIER2"
VERSION = "V-A-00"

# The only constant in this module: one candle on each side of the middle one.
# SOURCE_NUMBER, attributed to the sources that state the count, never a default.
NEIGHBOURS_EACH_SIDE = 1  # SOURCE_NUMBER
NEIGHBOURS_SOURCES_HIGH = ("A1", "A4", "A5")  # SOURCE_NUMBER
NEIGHBOURS_SOURCES_LOW = ("A1", "A5")  # SOURCE_NUMBER, WEAK_SUPPORT on this side

SUPPORT_LABEL_LOW = "WEAK_SUPPORT"

STATUS_YES = "YES"
STATUS_NO = "NO"
STATUS_UNDECIDED = "UNDECIDED"
STATUS_PENDING = "PENDING"

GAP_TIE_SWING = {
    "id": "GAP_TIE_SWING",
    "text": "كيف تُحسم قمة/قاع متساويان أو متقاربان تقاربًا تامًا في المقارنة؟",
}

SIDE_HIGH = "high"
SIDE_LOW = "low"


def _relevant(candle: Candle, side: str) -> float:
    return candle.high if side == SIDE_HIGH else candle.low


def swing_at(candles, t: int, side: str) -> dict:
    """Evaluate a swing point at the third candle index `t`.

    Reads only candles[:t+1], i.e. never anything after the evaluation index.
    c1 = t-2, c2 = t-1 (the candidate), c3 = t.
    """

    if side not in (SIDE_HIGH, SIDE_LOW):
        raise ValueError("side must be 'high' or 'low'")
    if not isinstance(t, int) or isinstance(t, bool):
        raise ValueError("index t must be an int")
    if t < 2:
        raise ValueError("index t must be at least 2 (three candles needed)")
    if t >= len(candles):
        raise ValueError("index t is outside the candle list")

    window = candles[: t + 1]  # no lookahead by construction
    c1, c2, c3 = window[t - 2], window[t - 1], window[t]

    v1, v2, v3 = _relevant(c1, side), _relevant(c2, side), _relevant(c3, side)

    if side == SIDE_HIGH:
        beyond = (v1 > v2) or (v3 > v2)
    else:
        beyond = (v1 < v2) or (v3 < v2)
    equal = (v1 == v2) or (v3 == v2)

    open_gaps = []
    if beyond:
        status = STATUS_NO
    elif equal:
        status = STATUS_UNDECIDED
        open_gaps.append(dict(GAP_TIE_SWING))
    elif not c3.closed:
        status = STATUS_PENDING
    else:
        status = STATUS_YES

    is_low = side == SIDE_LOW
    return {
        "concept": "swing_low" if is_low else "swing_high",
        "candle_indices": {"c1": t - 2, "c2": t - 1, "c3": t},
        "version": VERSION,
        "tier": TIER,
        "source_ids": list(NEIGHBOURS_SOURCES_LOW if is_low else NEIGHBOURS_SOURCES_HIGH),
        "status": status,
        "labels": [SUPPORT_LABEL_LOW] if is_low else [],
        "open_gaps": open_gaps,
        "comparison": {
            "relevant_side": side,
            "values": {"c1": v1, "c2": v2, "c3": v3},
        },
        "source_number": {
            "name": "one_candle_each_side",
            "value": NEIGHBOURS_EACH_SIDE,
            "tag": "SOURCE_NUMBER",
        },
    }
