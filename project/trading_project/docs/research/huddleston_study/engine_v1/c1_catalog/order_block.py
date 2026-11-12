"""Order block with the mean threshold — TIER2 third-party definitions.

Rule text: BUILD_STEP_C1_SPEC.md §3, built from
  q_stage2_batch2_entry_zones.md  (C-OB-01 … C-OB-45, table D1)
  r_stage2_batch2b_corrections.md (C-OB-46 … C-OB-62, table E1, CONFLICT-OB-A/B/C/D)

Nothing here is attributed to any person. The tier is TIER2 and every result
prints its variant ids and its claim ids.

Coded dimensions (switchable by name, never chosen by results):
  boundaries            V-OB-4 full range (wicks)  | V-OB-5 body only
  mean_threshold_basis  V-OB-6 50% of the body     | V-OB-7 50% of the full range
  entry_level           V-OB-8 mean threshold      | V-OB-9 block candle open
  invalidation          V-OB-10 close beyond far edge | V-OB-11 close past the mean
                        threshold is invalidation | V-OB-12 the same close is a
                        warning only
  prerequisites         V-OB-13 structure break, V-OB-14 FVG in the move,
                        V-OB-15 sweep before, V-OB-16 unmitigated / first touch

Not coded, and why:
  V-OB-17 discount/premium      no dealing-range function exists in engine_v1
  V-OB-18 displacement 1.5x     the two units print different denominators and no
                                averaging window number
  V-OB-19 / V-OB-20 stop        stop and target are outside this step
  V-OB-21 size                   position sizing is not a candle computation

The displacement move's own bounds are not defined by any source, so the first
candle of the move is an explicit caller input and the gap is printed.

No lookahead: the function reads candles[:last_read+1] only, and `last_read` is
printed with every result.  No threshold, ratio or default is invented here.
"""

from __future__ import annotations

from common import (
    FLAG_OWNER_OVERRIDE,
    GAPS,
    STATUS_BUILT,
    STATUS_PENDING,
    STATUS_UNDEFINED,
    TIER,
    as_candles,
    dimension_gaps,
    gap,
    require_choice,
)

CONCEPT = "order_block"

DIR_BULLISH = "bullish"
DIR_BEARISH = "bearish"

BOUNDARY_FULL_RANGE = "V-OB-4"
BOUNDARY_BODY_ONLY = "V-OB-5"
MT_BODY = "V-OB-6"
MT_FULL_RANGE = "V-OB-7"
ENTRY_MEAN_THRESHOLD = "V-OB-8"
ENTRY_BLOCK_OPEN = "V-OB-9"
INVALID_FAR_EDGE = "V-OB-10"
INVALID_MEAN_THRESHOLD = "V-OB-11"
INVALID_MEAN_THRESHOLD_WARNING = "V-OB-12"
PREREQ_STRUCTURE_BREAK = "V-OB-13"
PREREQ_FVG = "V-OB-14"
PREREQ_SWEEP = "V-OB-15"
PREREQ_UNMITIGATED = "V-OB-16"

BOUNDARY_CHOICES = (BOUNDARY_FULL_RANGE, BOUNDARY_BODY_ONLY)
MEAN_THRESHOLD_CHOICES = (MT_BODY, MT_FULL_RANGE)
ENTRY_CHOICES = (ENTRY_MEAN_THRESHOLD, ENTRY_BLOCK_OPEN)
INVALIDATION_CHOICES = (INVALID_FAR_EDGE, INVALID_MEAN_THRESHOLD, INVALID_MEAN_THRESHOLD_WARNING)
PREREQUISITE_IDS = (PREREQ_STRUCTURE_BREAK, PREREQ_FVG, PREREQ_SWEEP, PREREQ_UNMITIGATED)
PREREQUISITES_NEEDING_EVIDENCE = (PREREQ_STRUCTURE_BREAK, PREREQ_FVG, PREREQ_SWEEP)

# ENGINEERING_CHOICE declared in BUILD_STEP_C1_SPEC.md §6, before any code:
# fewest computation inputs, tie -> lowest variant id, reason "simplicity of
# computation, not claimed better".  Used only so one dimension at a time can be
# compared.  Never re-chosen by results.
REFERENCE_VARIANTS = {
    "boundaries": BOUNDARY_FULL_RANGE,
    "mean_threshold_basis": MT_BODY,
    "invalidation": INVALID_FAR_EDGE,
}

# The single fraction of the step.  SOURCE_NUMBER: the sources print "50%"
# (C-OB-18, C-OB-19, C-OB-20, C-OB-21).  It is applied to the chosen basis.
MEAN_THRESHOLD_FRACTION = 0.5  # SOURCE_NUMBER, claims C-OB-18 / C-OB-19 / C-OB-20 / C-OB-21
MEAN_THRESHOLD_CLAIMS = ("C-OB-18", "C-OB-19", "C-OB-20", "C-OB-21")

CLAIM_IDS = {
    "V-OB-1": (
        "C-OB-01", "C-OB-02", "C-OB-03", "C-OB-04", "C-OB-05", "C-OB-06",
        "C-OB-07", "C-OB-08", "C-OB-51", "C-OB-52", "C-OB-61",
    ),
    "V-OB-2": ("C-OB-03", "C-OB-05", "C-OB-06", "C-OB-07", "C-OB-11", "C-OB-58"),
    "V-OB-3": ("C-OB-09", "C-OB-10", "C-OB-11"),
    "V-OB-4": ("C-OB-13", "C-OB-14"),
    "V-OB-5": ("C-OB-15", "C-OB-16", "C-OB-17", "C-OB-53", "C-OB-54"),
    "V-OB-6": ("C-OB-18", "C-OB-19", "C-CE-17"),
    "V-OB-7": ("C-OB-20", "C-OB-21"),
    "V-OB-8": ("C-OB-18", "C-OB-20", "C-OB-21"),
    "V-OB-9": ("C-OB-22",),
    "V-OB-10": ("C-OB-37", "C-OB-38", "C-OB-42", "C-OB-48", "C-OB-55"),
    "V-OB-11": ("C-OB-39",),
    "V-OB-12": ("C-OB-40",),
    "V-OB-13": ("C-OB-26", "C-OB-30", "C-OB-35", "C-OB-56"),
    "V-OB-14": ("C-OB-27", "C-OB-31", "C-OB-59"),
    "V-OB-15": ("C-OB-28", "C-OB-32", "C-OB-46"),
    "V-OB-16": ("C-OB-29", "C-OB-33", "C-OB-36"),
}

# Honest labels of the dimensions that are not computed here (C1b spec §5):
# V-OB-13/14/15 are caller evidence, never a break/FVG/sweep computed in this tree,
# and V-OB-3 is implemented as the "last opposing candle" reading only.
VARIANT_STATUS_LABEL = {
    "V-OB-3": "PARTIAL_LAST_CANDLE_ONLY",
    "V-OB-13": "CALLER_INPUT_NOT_COMPUTED",
    "V-OB-14": "CALLER_INPUT_NOT_COMPUTED",
    "V-OB-15": "CALLER_INPUT_NOT_COMPUTED",
}

VERDICT_VALID = "VALID"
VERDICT_INVALIDATED = "INVALIDATED"
VERDICT_FILTER_FAILED = "FILTER_FAILED"
VERDICT_NO_BLOCK = "NO_BLOCK"
VERDICT_NONE = "NONE"

LABEL_INVALIDATED = "INVALIDATED"
LABEL_WARNING = "WARNING"
LABEL_NOT_INVALIDATED = "NOT_INVALIDATED"

FILTER_PASS = "PASS"
FILTER_FAIL = "FAIL"
FILTER_OFF = "OFF"


def _claims_for(*variant_ids, extra=()):
    groups = [CLAIM_IDS.get(v, ()) for v in variant_ids]
    groups.append(tuple(extra))
    return groups


def _validate_prerequisites(prerequisites) -> dict:
    if prerequisites is None:
        raise ValueError("prerequisites must be provided explicitly")
    for prereq_id in PREREQUISITE_IDS:
        if prereq_id not in prerequisites:
            raise ValueError("prerequisites must provide an entry for %s" % prereq_id)
        entry = prerequisites[prereq_id]
        if not isinstance(entry, dict) or "on" not in entry:
            raise ValueError("prerequisite %s needs an explicit 'on' flag" % prereq_id)
        if not isinstance(entry["on"], bool):
            raise ValueError("prerequisite %s 'on' flag must be a bool" % prereq_id)
        if prereq_id in PREREQUISITES_NEEDING_EVIDENCE:
            if "evidence" not in entry:
                raise ValueError("prerequisite %s needs an explicit 'evidence' key" % prereq_id)
            if entry["on"]:
                if not isinstance(entry.get("evidence"), bool):
                    raise ValueError("evidence is required when the filter is on")
            elif entry.get("evidence") is not None and not isinstance(entry.get("evidence"), bool):
                raise ValueError("prerequisite %s evidence must be a bool or null" % prereq_id)
    return prerequisites


def _record(**kwargs) -> dict:
    base = {
        "concept": CONCEPT,
        "direction": None,
        "status": None,
        "verdict": VERDICT_NONE,
        "tier": TIER,
        "block_index": None,
        "displacement_start_index": None,
        "candle_indices": {"block": None, "displacement_start": None, "last_read": None},
        "variant_ids": {},
        "reference_variants": dict(REFERENCE_VARIANTS),
        "flags": [FLAG_OWNER_OVERRIDE],
        "claim_ids": [],
        "numbers": None,
        "filters": [],
        "invalidation": None,
        "cluster_notice": None,
        "dimension_gaps": dimension_gaps(CONCEPT),
        "gaps": [],
    }
    base.update(kwargs)
    return base


def _opposing_run(rows, block_index, direction) -> int:
    """How many adjacent opposing candles end at `block_index` (the block included).

    The spec (OB-D3, C1b spec §6.2) does not bound a cluster, so the count is printed
    and its bounds stay an open gap; only the run that touches the block is counted.
    """

    count = 1
    index = block_index - 1
    while index >= 0:
        candle = rows[index]
        is_opposing = (
            candle.close < candle.open if direction == DIR_BULLISH else candle.close > candle.open
        )
        if not is_opposing:
            break
        count += 1
        index -= 1
    return count


def order_block_at(
    candles,
    displacement_start_index,
    direction,
    boundaries=None,
    mean_threshold_basis=None,
    entry_level=None,
    invalidation=None,
    prerequisites=None,
):
    """Evaluate the order block that precedes the move starting at `displacement_start_index`."""

    rows = as_candles(candles)

    if direction not in (DIR_BULLISH, DIR_BEARISH):
        raise ValueError("direction must be 'bullish' or 'bearish'")
    if isinstance(displacement_start_index, bool) or not isinstance(displacement_start_index, int):
        raise ValueError("displacement_start_index must be an int")
    if displacement_start_index < 1:
        raise ValueError("displacement_start_index must be at least 1")
    if displacement_start_index > len(rows) - 1:
        raise ValueError("displacement_start_index is outside the candle list")

    require_choice("boundaries", boundaries, BOUNDARY_CHOICES)
    require_choice("mean_threshold_basis", mean_threshold_basis, MEAN_THRESHOLD_CHOICES)
    require_choice("entry_level", entry_level, ENTRY_CHOICES)
    require_choice("invalidation", invalidation, INVALIDATION_CHOICES)
    filters_in = _validate_prerequisites(prerequisites)

    last_read = len(rows) - 1
    variant_ids = {
        "boundaries": boundaries,
        "mean_threshold_basis": mean_threshold_basis,
        "entry_level": entry_level,
        "invalidation": invalidation,
        "prerequisites": list(PREREQUISITE_IDS),
    }
    claims = _claims_for(
        "V-OB-1",
        "V-OB-3",
        boundaries,
        mean_threshold_basis,
        entry_level,
        invalidation,
        *PREREQUISITE_IDS,
        extra=MEAN_THRESHOLD_CLAIMS,
    )

    def claims_of(groups):
        flat = set()
        for group in groups:
            flat.update(group)
        return sorted(flat)

    if not rows[last_read].closed:
        return _record(
            direction=direction,
            status=STATUS_PENDING,
            verdict=VERDICT_NONE,
            displacement_start_index=displacement_start_index,
            candle_indices={
                "block": None,
                "displacement_start": displacement_start_index,
                "last_read": last_read,
            },
            variant_ids=variant_ids,
            claim_ids=claims_of(claims),
            gaps=[],
        )

    # 1. the block candle: last opposing candle before the move (V-OB-1, V-OB-3 last one)
    opposing = {}
    for index in range(displacement_start_index - 1, -1, -1):
        candle = rows[index]
        if candle.close == candle.open:
            return _record(
                direction=direction,
                status=STATUS_UNDEFINED,
                verdict=VERDICT_NONE,
                displacement_start_index=displacement_start_index,
                candle_indices={
                    "block": None,
                    "displacement_start": displacement_start_index,
                    "last_read": last_read,
                },
                variant_ids=variant_ids,
                claim_ids=claims_of(claims),
                cluster_notice={"count": None, "gap_printed": False},
                gaps=[gap("GAP_OB_MOVE_BOUNDS"), gap("GAP_DOJI_BLOCK")],
            )
        is_opposing = candle.close < candle.open if direction == DIR_BULLISH else candle.close > candle.open
        if is_opposing:
            opposing = {"index": index, "candle": candle}
            break

    if not opposing:
        return _record(
            direction=direction,
            status=STATUS_BUILT,
            verdict=VERDICT_NO_BLOCK,
            displacement_start_index=displacement_start_index,
            candle_indices={
                "block": None,
                "displacement_start": displacement_start_index,
                "last_read": last_read,
            },
            variant_ids=variant_ids,
            claim_ids=claims_of(claims),
            cluster_notice={"count": None, "gap_printed": False},
            gaps=[gap("GAP_OB_MOVE_BOUNDS")],
        )

    block_index = opposing["index"]
    block = opposing["candle"]

    # The cluster notice (coverage E-10, C1b spec §6.2): more than one adjacent
    # opposing candle means the cluster exists and its bounds are an open gap, so
    # the gap line is printed and the count is reported.
    run_length = _opposing_run(rows, block_index, direction)
    cluster_notice = {
        "count": run_length,
        "gap_printed": run_length > 1,
        "bounds": "UNDEFINED_KNOWLEDGE_GAP",
    }
    gaps = [gap("GAP_OB_MOVE_BOUNDS")]
    if cluster_notice["gap_printed"]:
        gaps.append(gap("GAP_CLUSTER_BOUND"))

    # 2. boundaries
    if boundaries == BOUNDARY_FULL_RANGE:
        zone_low, zone_high = block.low, block.high
    else:
        zone_low = min(block.open, block.close)
        zone_high = max(block.open, block.close)

    # 3. mean threshold on the chosen basis, always the same printed fraction
    if mean_threshold_basis == MT_BODY:
        basis_low, basis_high = min(block.open, block.close), max(block.open, block.close)
        mean_threshold = (block.open + block.close) * MEAN_THRESHOLD_FRACTION
    else:
        basis_low, basis_high = block.low, block.high
        mean_threshold = (block.high + block.low) * MEAN_THRESHOLD_FRACTION

    # 4. entry level
    entry = mean_threshold if entry_level == ENTRY_MEAN_THRESHOLD else block.open

    # 5. invalidation over the candles after the block
    far_edge = zone_low if direction == DIR_BULLISH else zone_high
    invalidated = False
    label = LABEL_NOT_INVALIDATED
    at_index = None
    at_close = None
    for index in range(block_index + 1, last_read + 1):
        close = rows[index].close
        if invalidation == INVALID_FAR_EDGE:
            hit = close < far_edge if direction == DIR_BULLISH else close > far_edge
        else:
            hit = close < mean_threshold if direction == DIR_BULLISH else close > mean_threshold
        if hit:
            at_index = index
            at_close = close
            if invalidation == INVALID_MEAN_THRESHOLD_WARNING:
                label = LABEL_WARNING
                invalidated = False
            else:
                label = LABEL_INVALIDATED
                invalidated = True
            break

    # 6. prerequisites: three are caller evidence, the fourth is computed here
    filters = []
    for prereq_id in PREREQUISITES_NEEDING_EVIDENCE:
        entry_state = filters_in[prereq_id]
        if not entry_state["on"]:
            filters.append(
                {"id": prereq_id, "on": False, "evidence": entry_state.get("evidence"),
                 "basis": "CALLER_INPUT", "result": FILTER_OFF}
            )
        else:
            filters.append(
                {"id": prereq_id, "on": True, "evidence": entry_state["evidence"],
                 "basis": "CALLER_INPUT",
                 "result": FILTER_PASS if entry_state["evidence"] else FILTER_FAIL}
            )

    unmitigated = filters_in[PREREQ_UNMITIGATED]
    if not unmitigated["on"]:
        filters.append(
            {"id": PREREQ_UNMITIGATED, "on": False, "evidence": None,
             "basis": "COMPUTED_FROM_CANDLES", "result": FILTER_OFF}
        )
    else:
        touches_before_last = 0
        for index in range(block_index + 1, last_read):
            candle = rows[index]
            if candle.low <= zone_high and candle.high >= zone_low:
                touches_before_last += 1
        filters.append(
            {"id": PREREQ_UNMITIGATED, "on": True, "evidence": touches_before_last == 0,
             "basis": "COMPUTED_FROM_CANDLES", "touches_before_last_bar": touches_before_last,
             "result": FILTER_PASS if touches_before_last == 0 else FILTER_FAIL}
        )

    filter_failed = any(item["result"] == FILTER_FAIL for item in filters)

    if invalidated:
        verdict = VERDICT_INVALIDATED
    elif filter_failed:
        verdict = VERDICT_FILTER_FAILED
    else:
        verdict = VERDICT_VALID

    return _record(
        direction=direction,
        status=STATUS_BUILT,
        verdict=verdict,
        block_index=block_index,
        displacement_start_index=displacement_start_index,
        candle_indices={
            "block": block_index,
            "displacement_start": displacement_start_index,
            "last_read": last_read,
        },
        variant_ids=variant_ids,
        claim_ids=claims_of(claims),
        numbers={
            "zone_low": zone_low,
            "zone_high": zone_high,
            "mean_threshold": mean_threshold,
            "entry": entry,
            "block_open": block.open,
            "block_close": block.close,
            "block_high": block.high,
            "block_low": block.low,
            "basis_low": basis_low,
            "basis_high": basis_high,
            "far_edge": far_edge,
            "mean_threshold_source": {
                "name": "mean_threshold_fraction",
                "value": MEAN_THRESHOLD_FRACTION,
                "tag": "SOURCE_NUMBER",
                "claim_ids": list(MEAN_THRESHOLD_CLAIMS),
            },
        },
        filters=filters,
        cluster_notice=cluster_notice,
        invalidation={
            "id": invalidation,
            "invalidated": invalidated,
            "label": label,
            "at_index": at_index,
            "close": at_close,
        },
        gaps=gaps,
    )
