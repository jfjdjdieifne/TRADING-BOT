"""Displacement — TIER2 third-party definitions, no reference variant (owner decision D2).

Rule text: BUILD_STEP_C1_SPEC.md §5 and BUILD_STEP_C1b_SPEC.md §1–§3, built from
  BUILD_STEP_B1_DESIGN_V2.md §8 (claims F1 … F6, variants V-D-01 … V-D-04)
  external_sources/f_displacement.md (the same claims with their quotes)
  external_sources/l_open_questions.md (records Q1-01, Q1-02, Q1-13)
  OWNER_DECISIONS_D2.md (D2: no reference definition; families V-D-A / V-D-B / V-D-C)

Nothing here is attributed to any person. The tier is TIER2 and every result
prints its variant id, claim ids and the source numbers it used.

**There is no reference variant.** OWNER_DECISIONS_D2.md records the owner decision
that displacement has no reference definition, so `reference_variant` is printed as
NONE_PER_OWNER_D2 in every result and no variant is preferred. The C1 constant
`REFERENCE_VARIANT` is gone.

Coded named variants, each switchable, none selected by results:
  V-D-01  body / range above the printed lower bound 60 (claim F1);
          equality returns UNDECIDED                          [COMPUTED]
  V-D-02  body / range above the printed 75, and range above 2 x the average
          of a caller-named previous window (claim F2)         [COMPUTED]
  V-D-03  body above 2 x the average body of the previous ten candles (claim F5);
          equality returns UNDECIDED                          [COMPUTED]
  V-D-04  the gap requirement of claim F1                            [UNDEFINED_ALWAYS]
  V-D-C   body at least 1.5 x ATR(14) (records Q1-01 and Q1-02)      [UNDEFINED_ATR_FORMULA]
  V-D-Q   the qualitative family of F3 / F4 / F6                     [UNDEFINED_ALWAYS]

V-D-C is accepted as a named variant of owner decision D2 and returns UNDEFINED with
KNOWLEDGE_GAP: ATR formula.  The sources print the multiple (1.5) and the length (14)
and never say how ATR or true range is computed, so no formula is taken from outside
knowledge and no ATR is computed here.

The engine never chooses one of the printed numbers over another:
  * the range comparison of F2 prints "3–5" previous candles, so the window is an
    explicit caller input and only a number a source prints (3, 4, 5 or 10) is
    accepted;
  * a value exactly equal to a printed threshold is not settled by any source,
    so it returns UNDEFINED with the equality gap.
"""

from __future__ import annotations

from common import (
    STATUS_BUILT,
    STATUS_PENDING,
    STATUS_UNDEFINED,
    TIER,
    as_candles,
    dimension_gaps,
    gap,
    require_choice,
    require_index,
)

CONCEPT = "displacement"

V_D_01 = "V-D-01"
V_D_02 = "V-D-02"
V_D_03 = "V-D-03"
V_D_04 = "V-D-04"
V_D_C = "V-D-C"
V_D_QUALITATIVE = "V-D-Q"
VARIANTS = (V_D_01, V_D_02, V_D_03, V_D_04, V_D_C, V_D_QUALITATIVE)

# Honest status label of every variant (C1b spec §5).  A label is not a result:
# it names what the code does with the id, so no entry is described as computed
# while it is not.
VARIANT_STATUS_LABEL = {
    V_D_01: "COMPUTED",
    V_D_02: "COMPUTED",
    V_D_03: "COMPUTED",
    V_D_04: "UNDEFINED_ALWAYS",
    V_D_C: "UNDEFINED_ATR_FORMULA",
    V_D_QUALITATIVE: "UNDEFINED_ALWAYS",
}

# Owner decision D2: no reference variant exists.  The string below is printed with
# every result instead of a variant id.
REFERENCE_VARIANT_NONE = "NONE_PER_OWNER_D2"
FLAG_NO_REFERENCE = "OWNER_DECISION_D2_NO_REFERENCE_VARIANT"

GAP_D_ATR_FORMULA = "GAP_D_ATR_FORMULA"

ANSWER_YES = "YES"
ANSWER_NO = "NO"
ANSWER_UNDECIDED = "UNDECIDED"

# SOURCE_NUMBER values, verbatim from the claims.  They are used, printed, and
# never tuned.
BODY_RANGE_LOWER_BOUND = 0.60  # SOURCE_NUMBER F1 "60 to 80 percent or more"
BODY_RANGE_UPPER_PRINTED = 0.80  # SOURCE_NUMBER F1 "60 to 80 percent"
BODY_RANGE_ABOVE = 0.75  # SOURCE_NUMBER F2 "body-to-range ratio above ~75%"
RANGE_TO_AVERAGE_MINIMUM = 2.0  # SOURCE_NUMBER F2 "at minimum 2x the average recent candle"
BODY_TO_AVERAGE_BODY_MINIMUM = 2.0  # SOURCE_NUMBER F5 "at least two to three times"
BODY_TO_AVERAGE_BODY_UPPER = 3.0  # SOURCE_NUMBER F5 "two to three times"
PREVIOUS_BODY_COUNT = 10  # SOURCE_NUMBER F5 "the previous ten candles"
PREVIOUS_WINDOWS_PRINTED = (3, 4, 5, 10)  # SOURCE_NUMBER F2 "3–5", F5 "ten"

# V-D-C numbers, both printed by the sources and both unused for computation:
# the ATR formula itself is an open gap (KNOWLEDGE_GAP: ATR formula).
BODY_TO_ATR_MULTIPLE = 1.5  # SOURCE_NUMBER Q1-01 "at least 1.5 times", Q1-02 "at least 1.5 times"
ATR_PERIOD = 14  # SOURCE_NUMBER Q1-01 "of the prior 14 candles", Q1-02 "14-period"

CLAIM_IDS = {
    V_D_01: ("F1",),
    V_D_02: ("F2",),
    V_D_03: ("F5",),
    V_D_04: ("F1",),
    # Q1-13 records NO_NUMBER ("What qualifies is judged by eye, not by a formula"),
    # so it is not a claim of the 1.5 x ATR(14) number.
    V_D_C: ("Q1-01", "Q1-02"),
    V_D_QUALITATIVE: ("F3", "F4", "F6"),
}


def _record(**kwargs):
    base = {
        "concept": CONCEPT,
        "status": None,
        "answer": None,
        "tier": TIER,
        "variant_id": None,
        "candle_indices": {"target": None, "previous_window": None},
        "claim_ids": [],
        "source_numbers": [],
        "numbers": None,
        "dimension_gaps": dimension_gaps(CONCEPT),
        "gaps": [],
        "reference_variant": REFERENCE_VARIANT_NONE,
        "flags": [FLAG_NO_REFERENCE],
    }
    base.update(kwargs)
    return base


CONCEPT_GAPS = ("GAP_D_CLUSTER", "GAP_D_PRIOR_SWEEP")


def _concept_gaps():
    return [gap(gap_id) for gap_id in CONCEPT_GAPS]


def _source_numbers_for(variant, window=None):
    def entry(name, value, claim_id):
        return {"name": name, "value": value, "claim_id": claim_id}

    if variant == V_D_01:
        return [
            entry("body_to_range_lower_bound", "60", "F1"),
            entry("body_to_range_upper_printed", "80", "F1"),
        ]
    if variant == V_D_02:
        numbers = [
            entry("body_to_range_above", "75", "F2"),
            entry("range_to_average_recent_minimum", "2", "F2"),
            entry("previous_candles_printed_band", "3-5", "F2"),
        ]
        if window is not None:
            numbers.append(entry("previous_window_used", str(window), "F2" if window != 10 else "F5"))
        return numbers
    if variant == V_D_03:
        return [
            entry("body_to_average_body_minimum", "2-3", "F5"),
            entry("previous_body_count", "10", "F5"),
        ]
    if variant == V_D_04:
        return [entry("gap_requirement", "without a gap there is no ICT displacement", "F1")]
    if variant == V_D_C:
        return [
            entry("body_to_atr_multiple", str(BODY_TO_ATR_MULTIPLE), "Q1-01"),
            entry("atr_period", str(ATR_PERIOD), "Q1-02"),
        ]
    return []


def displacement_at(candles, t, variant, previous_window=None):
    """Evaluate displacement on the candle at index `t`.

    Reads candles[:t+1] only.  `previous_window` is the number of previous
    candles used by V-D-02; it is never chosen here.
    """

    rows = as_candles(candles)
    require_choice("displacement", variant, VARIANTS)
    require_index("t", t, len(rows))

    if previous_window is not None:
        if isinstance(previous_window, bool) or not isinstance(previous_window, int):
            raise ValueError("previous_window must be an int or null")
        if previous_window not in PREVIOUS_WINDOWS_PRINTED:
            raise ValueError(
                "previous_window must be one of the numbers a source prints (3, 4, 5, 10)"
            )

    claim_ids = sorted(CLAIM_IDS[variant])
    target = rows[t]

    if variant == V_D_C:
        # Owner decision D2, family V-D-C.  The sources print 1.5 and 14 but never the
        # formula of ATR or of true range, so nothing is computed: a closed candle
        # returns UNDEFINED with the formula gap, an unclosed one returns PENDING.
        if not target.closed:
            return _record(
                status=STATUS_PENDING,
                answer=None,
                variant_id=variant,
                candle_indices={"target": t, "previous_window": None},
                claim_ids=claim_ids,
                source_numbers=_source_numbers_for(variant),
                gaps=[],
            )
        return _record(
            status=STATUS_UNDEFINED,
            answer=None,
            variant_id=variant,
            candle_indices={"target": t, "previous_window": None},
            claim_ids=claim_ids,
            source_numbers=_source_numbers_for(variant),
            gaps=_concept_gaps() + [gap(GAP_D_ATR_FORMULA)],
        )

    if variant in (V_D_04, V_D_QUALITATIVE):
        gap_id = "GAP_D_GAP_DEFINITION" if variant == V_D_04 else "GAP_D_QUALITATIVE"
        return _record(
            status=STATUS_UNDEFINED,
            answer=None,
            variant_id=variant,
            candle_indices={"target": t, "previous_window": None},
            claim_ids=claim_ids,
            source_numbers=_source_numbers_for(variant),
            gaps=_concept_gaps() + [gap(gap_id)],
        )

    if not target.closed:
        return _record(
            status=STATUS_PENDING,
            answer=None,
            variant_id=variant,
            candle_indices={"target": t, "previous_window": None},
            claim_ids=claim_ids,
            source_numbers=_source_numbers_for(variant),
            gaps=[],
        )

    body = abs(target.close - target.open)
    candle_range = target.high - target.low
    if candle_range == 0:
        raise ValueError("candle range is zero")
    ratio = body / candle_range
    numbers = {"body": body, "range": candle_range, "body_range_ratio": ratio}

    if variant == V_D_01:
        gaps = _concept_gaps()
        if ratio > BODY_RANGE_LOWER_BOUND:
            answer = ANSWER_YES
        elif ratio == BODY_RANGE_LOWER_BOUND:
            answer = ANSWER_UNDECIDED
            gaps.append(gap("GAP_EQUAL_THRESHOLD"))
        else:
            answer = ANSWER_NO
        return _record(
            status=STATUS_UNDEFINED if answer == ANSWER_UNDECIDED else STATUS_BUILT,
            answer=answer,
            variant_id=variant,
            candle_indices={"target": t, "previous_window": None},
            claim_ids=claim_ids,
            source_numbers=_source_numbers_for(variant),
            numbers=numbers,
            gaps=gaps,
        )

    if variant == V_D_02:
        if previous_window is None:
            return _record(
                status=STATUS_UNDEFINED,
                answer=None,
                variant_id=variant,
                candle_indices={"target": t, "previous_window": None},
                claim_ids=claim_ids,
                source_numbers=_source_numbers_for(variant),
                gaps=_concept_gaps() + [gap("GAP_D_WINDOW")],
            )
        if t < previous_window:
            return _record(
                status=STATUS_PENDING,
                answer=None,
                variant_id=variant,
                candle_indices={"target": t, "previous_window": [t - previous_window, t - 1]},
                claim_ids=claim_ids,
                source_numbers=_source_numbers_for(variant, previous_window),
                gaps=[],
            )
        window_rows = rows[t - previous_window : t]
        average_range = sum(row.high - row.low for row in window_rows) / previous_window
        if average_range == 0:
            raise ValueError("average range is zero")
        ratio_to_average = candle_range / average_range
        numbers["average_range"] = average_range
        numbers["ratio_to_average_range"] = ratio_to_average

        gaps = _concept_gaps()
        if ratio > BODY_RANGE_ABOVE:
            body_part = ANSWER_YES
        elif ratio == BODY_RANGE_ABOVE:
            body_part = ANSWER_UNDECIDED
        else:
            body_part = ANSWER_NO

        if ratio_to_average > RANGE_TO_AVERAGE_MINIMUM:
            size_part = ANSWER_YES
        elif ratio_to_average == RANGE_TO_AVERAGE_MINIMUM:
            size_part = ANSWER_UNDECIDED
        else:
            size_part = ANSWER_NO

        if ANSWER_UNDECIDED in (body_part, size_part):
            answer = ANSWER_UNDECIDED
            gaps.append(gap("GAP_EQUAL_THRESHOLD"))
        elif body_part == ANSWER_YES and size_part == ANSWER_YES:
            answer = ANSWER_YES
        else:
            answer = ANSWER_NO

        return _record(
            status=STATUS_UNDEFINED if answer == ANSWER_UNDECIDED else STATUS_BUILT,
            answer=answer,
            variant_id=variant,
            candle_indices={
                "target": t,
                "previous_window": [t - previous_window, t - 1],
            },
            claim_ids=claim_ids,
            source_numbers=_source_numbers_for(variant, previous_window),
            numbers=numbers,
            gaps=gaps,
        )

    # V-D-03
    if t < PREVIOUS_BODY_COUNT:
        return _record(
            status=STATUS_PENDING,
            answer=None,
            variant_id=variant,
            candle_indices={"target": t, "previous_window": [0, t - 1] if t else None},
            claim_ids=claim_ids,
            source_numbers=_source_numbers_for(variant),
            gaps=[],
        )
    window_rows = rows[t - PREVIOUS_BODY_COUNT : t]
    average_body = sum(abs(row.close - row.open) for row in window_rows) / PREVIOUS_BODY_COUNT
    if average_body == 0:
        raise ValueError("average body is zero")
    ratio_to_average_body = body / average_body
    numbers["average_body"] = average_body
    numbers["ratio_to_average_body"] = ratio_to_average_body

    gaps = _concept_gaps()
    if ratio_to_average_body > BODY_TO_AVERAGE_BODY_MINIMUM:
        answer = ANSWER_YES
    elif ratio_to_average_body == BODY_TO_AVERAGE_BODY_MINIMUM:
        answer = ANSWER_UNDECIDED
        gaps.append(gap("GAP_EQUAL_THRESHOLD"))
    else:
        answer = ANSWER_NO

    return _record(
        status=STATUS_UNDEFINED if answer == ANSWER_UNDECIDED else STATUS_BUILT,
        answer=answer,
        variant_id=variant,
        candle_indices={"target": t, "previous_window": [t - PREVIOUS_BODY_COUNT, t - 1]},
        claim_ids=claim_ids,
        source_numbers=_source_numbers_for(variant),
        numbers=numbers,
        gaps=gaps,
    )
