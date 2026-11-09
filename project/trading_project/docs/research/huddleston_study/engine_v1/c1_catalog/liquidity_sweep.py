"""Liquidity sweep — TIER2 third-party definitions.

Rule text: BUILD_STEP_C1_SPEC.md §4, built from
  BUILD_STEP_B1_DESIGN_V2.md §7 (claims E1 … E5, variants V-E-00 and V-E-01)
  external_sources/e_liquidity_sweep.md (the same claims with their quotes)
  OWNER_DECISIONS.md §D1 (the sweep level is a V-A-00 swing; V-E-EQH is parked)

Nothing here is attributed to any person. The tier is TIER2 and every result
prints its variant id and claim ids.

Reference shape (V-E-00, 4 units: E1 type one, E3, E4, E5):
  a wick extends beyond the level AND the candle body closes back on the other
  side, judged only after the candle closes.
Named variant (V-E-01, one unit: E1 type two, opposed explicitly by E3):
  the body closes marginally beyond the level and the very next candle reverses
  back inside.  It reads one extra candle, so it is evaluated at the confirming
  bar, never ahead of it.

Not coded, and why:
  V-E-EQH  equal highs/lows: the candle record of this tree has no ask/bid, so
           the 1 x spread of D1 cannot be computed, and the pairing lookback is
           an open gap.  It returns UNDEFINED with its gap.
  E2       "a sharp spike with a long wick" gives no closing rule and no number.

No number is invented here: the sweep has no SOURCE_NUMBER at all, and its
distance/speed dimension is a printed gap.
"""

from __future__ import annotations

from common import (
    STATUS_BUILT,
    STATUS_PENDING,
    STATUS_UNDEFINED,
    TIER,
    as_candles,
    gap,
    require_choice,
    require_index,
    require_number,
)

sys_swing_at = None  # bound below, keeps the import error visible if b1 changes


def _swing_at():
    global sys_swing_at
    if sys_swing_at is None:
        from swing import swing_at  # b1_candles, imported unmodified

        sys_swing_at = swing_at
    return sys_swing_at


CONCEPT = "liquidity_sweep"

SIDE_HIGH = "high"
SIDE_LOW = "low"

VERSION_REFERENCE = "V-E-00"
VERSION_MARGINAL_BODY = "V-E-01"
VERSION_EQH = "V-E-EQH"
VARIANTS = (VERSION_REFERENCE, VERSION_MARGINAL_BODY, VERSION_EQH)

ANSWER_YES = "YES"
ANSWER_NO = "NO"
ANSWER_UNDECIDED = "UNDECIDED"

CLAIM_IDS = {
    VERSION_REFERENCE: ("E1", "E3", "E4", "E5"),
    VERSION_MARGINAL_BODY: ("E1",),
    VERSION_EQH: ("OWNER-D1",),
}

LEVEL_BASIS_CALLER = "CALLER_INPUT"
LEVEL_BASIS_OWNER_SWING = "OWNER_DECISION_D1_SWING_V-A-00"
OWNER_CLAIM = "OWNER-D1"


def latest_swing_level(candles, before_index, side):
    """The most recent V-A-00 swing level strictly before `before_index`.

    OWNER_DECISIONS.md §D1 makes this the sweep level.  Nothing is looked up
    after `before_index - 1`, and no lookback number is needed: the scan walks
    backwards and stops at the first confirmed swing.
    """

    if side not in (SIDE_HIGH, SIDE_LOW):
        raise ValueError("side must be 'high' or 'low'")
    if isinstance(before_index, bool) or not isinstance(before_index, int):
        raise ValueError("before_index must be an int")

    swing_at = _swing_at()
    for index in range(before_index - 1, 1, -1):
        if index >= len(candles):
            continue
        record = swing_at(candles, index, side)
        if record["status"] == "YES":
            # V-A-00 puts the swing point on the MIDDLE candle of the three, and
            # `index` is the confirming third candle, so the wick is index - 1.
            swing_candle = candles[index - 1]
            level = swing_candle.high if side == SIDE_HIGH else swing_candle.low
            return level, index
    return None, None


def _record(**kwargs):
    base = {
        "concept": CONCEPT,
        "side": None,
        "status": None,
        "answer": None,
        "tier": TIER,
        "variant_id": None,
        "level": None,
        "level_basis": LEVEL_BASIS_CALLER,
        "swing_index": None,
        "candle_indices": {"sweep": None, "confirm": None, "last_read": None},
        "claim_ids": [],
        "numbers": None,
        "gaps": [],
    }
    base.update(kwargs)
    return base


def _evaluate(rows, t, side, level, variant, level_basis, swing_index):
    claim_ids = sorted(CLAIM_IDS[variant] + ((OWNER_CLAIM,) if level_basis == LEVEL_BASIS_OWNER_SWING else ()))

    if variant == VERSION_EQH:
        return _record(
            side=side,
            status=STATUS_UNDEFINED,
            answer=None,
            variant_id=variant,
            level=level,
            level_basis=level_basis,
            swing_index=swing_index,
            candle_indices={"sweep": t, "confirm": None, "last_read": t},
            claim_ids=claim_ids,
            gaps=[gap("GAP_SWEEP_EQH_BASIS")],
        )

    if variant == VERSION_MARGINAL_BODY and t < 1:
        raise ValueError("V-E-01 needs one earlier candle")

    needing_close = [t] if variant == VERSION_REFERENCE else [t, t - 1]
    if any(not rows[index].closed for index in needing_close):
        return _record(
            side=side,
            status=STATUS_PENDING,
            answer=None,
            variant_id=variant,
            level=level,
            level_basis=level_basis,
            swing_index=swing_index,
            candle_indices={
                "sweep": t if variant == VERSION_REFERENCE else t - 1,
                "confirm": None if variant == VERSION_REFERENCE else t,
                "last_read": t,
            },
            claim_ids=claim_ids,
            gaps=[],
        )

    gaps = [gap("GAP_SWEEP_DISTANCE")]
    sweep_index = t if variant == VERSION_REFERENCE else t - 1
    sweep_candle = rows[sweep_index]
    wick = sweep_candle.high if side == SIDE_HIGH else sweep_candle.low

    if side == SIDE_HIGH:
        beyond = wick > level
    else:
        beyond = wick < level

    if not beyond:
        answer = ANSWER_NO
    elif variant == VERSION_REFERENCE:
        close = sweep_candle.close
        if close == level:
            answer = ANSWER_UNDECIDED
            gaps.append(gap("GAP_SWEEP_EQUAL_CLOSE"))
        elif side == SIDE_HIGH:
            answer = ANSWER_YES if close < level else ANSWER_NO
        else:
            answer = ANSWER_YES if close > level else ANSWER_NO
    else:
        body_beyond = sweep_candle.close > level if side == SIDE_HIGH else sweep_candle.close < level
        if sweep_candle.close == level:
            answer = ANSWER_UNDECIDED
            gaps.append(gap("GAP_SWEEP_EQUAL_CLOSE"))
        elif not body_beyond:
            answer = ANSWER_NO
        else:
            confirm_close = rows[t].close
            if confirm_close == level:
                answer = ANSWER_UNDECIDED
                gaps.append(gap("GAP_SWEEP_EQUAL_CLOSE"))
            elif side == SIDE_HIGH:
                answer = ANSWER_YES if confirm_close < level else ANSWER_NO
            else:
                answer = ANSWER_YES if confirm_close > level else ANSWER_NO

    status = STATUS_UNDEFINED if answer == ANSWER_UNDECIDED else STATUS_BUILT

    return _record(
        side=side,
        status=status,
        answer=answer,
        variant_id=variant,
        level=level,
        level_basis=level_basis,
        swing_index=swing_index,
        candle_indices={
            "sweep": sweep_index,
            "confirm": None if variant == VERSION_REFERENCE else t,
            "last_read": t,
        },
        claim_ids=claim_ids,
        numbers={
            "wick": wick,
            "close": sweep_candle.close,
            "open": sweep_candle.open,
            "level": level,
        },
        gaps=gaps,
    )


def _validate(rows, t, side, variant):
    if side not in (SIDE_HIGH, SIDE_LOW):
        raise ValueError("side must be 'high' or 'low'")
    require_index("t", t, len(rows))
    require_choice("sweep", variant, VARIANTS)


def sweep_at(candles, t, side, level, variant):
    """Sweep at bar `t` against a caller-supplied level (tagged CALLER_INPUT)."""

    rows = as_candles(candles)
    _validate(rows, t, side, variant)
    numeric_level = require_number("level", level)
    return _evaluate(rows, t, side, numeric_level, variant, LEVEL_BASIS_CALLER, None)


def sweep_at_swing_level(candles, t, side, variant):
    """Sweep at bar `t` against the most recent V-A-00 swing level (owner decision D1)."""

    rows = as_candles(candles)
    _validate(rows, t, side, variant)
    level, swing_index = latest_swing_level(rows, t, side)
    if level is None:
        raise ValueError("no closed swing level is available before index t")
    return _evaluate(rows, t, side, level, variant, LEVEL_BASIS_OWNER_SWING, swing_index)
