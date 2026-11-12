"""Shared strictness for step C1 of engine_v1 (order block, liquidity sweep, displacement).

Scope rules of the step (see BUILD_STEP_C1_SPEC.md):
  * TIER2 only: every line is a publisher's claim, never a claim by any person.
  * no market data, no network, no pandas, no import from the old pipeline.
  * no number is invented here; the only numbers of the step are declared in
    BUILD_STEP_C1_SPEC.md §9 and appear once, with a SOURCE_NUMBER tag.
  * a missing knowledge dimension is printed as KNOWLEDGE_GAP, never guessed.
  * the candle's `closed` flag is required explicitly: a mapping without it
    raises, because the b1_candles helper defaults it to True.

The existing b1_candles modules are imported as they are and are not modified.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping

_C1_DIR = os.path.dirname(os.path.abspath(__file__))
_B1_DIR = os.path.join(os.path.dirname(_C1_DIR), "b1_candles")
for _path in (_B1_DIR, _C1_DIR):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from candle import Candle  # noqa: E402

TIER = "TIER2"

STATUS_BUILT = "BUILT"
STATUS_UNDEFINED = "UNDEFINED"
STATUS_PENDING = "PENDING"

REQUIRED_CANDLE_KEYS = ("o", "h", "l", "c", "closed")
PRICE_KEYS = ("o", "h", "l", "c")

# Every gap text of the step.  A gap is never resolved by a guess.
#
# The catalog was reconciled with BUILD_STEP_C1_SPEC.md §10 in BUILD_STEP_C1b_SPEC.md §4:
# the spec lists 17 ids, C1 carried 12, C1b carries all 17 plus GAP_EQUAL_THRESHOLD
# (declared when the code was written) and GAP_D_ATR_FORMULA (declared for V-D-C).
# Every id also carries a print status, because a gap that no dimension can print is
# recorded as NOT_PRINTABLE instead of being promised.
GAPS = {
    "GAP_CLUSTER_BOUND": "KNOWLEDGE_GAP: كيف تُحدّ حدود تجمع الشموع المعارضة (بداية التجمع ونهايته)؟",
    "GAP_DOJI_BLOCK": "KNOWLEDGE_GAP: ما حكم شمعة معارضة إغلاقها يساوي افتتاحها، هل تُعدّ معارضة؟",
    "GAP_STOP_AND_SIZE": "KNOWLEDGE_GAP: أين يوضع الوقف، وما حجم المركز عند اتساعه؟",
    "GAP_WICK_INVALIDATION": "KNOWLEDGE_GAP: هل يُبطل الفتيل عبر الحافة البعيدة الكتلة أم الإغلاق فقط؟",
    "GAP_LOCATION": "KNOWLEDGE_GAP: كيف يُحسب نطاق التداول (dealing range) الذي يقاس عليه الخصم والعلاوة؟",
    "GAP_OB_DISPLACEMENT_FILTER": "KNOWLEDGE_GAP: ما نافذة المتوسط التي يُقاس عليها فلتر الإزاحة 1.5x، وما مقدارها؟",
    "GAP_OB_MOVE_BOUNDS": "KNOWLEDGE_GAP: أي شموع تُعدّ «الحركة» التي تكسر البنية، وما أول شمعة فيها وآخرها؟",
    "GAP_SWEEP_DISTANCE": "KNOWLEDGE_GAP: ما مقدار الاختراق الأدنى وما سرعته ليُسمّى جرفًا لا كسرًا؟",
    "GAP_SWEEP_EQUAL_CLOSE": "KNOWLEDGE_GAP: ما حكم إغلاق الجسم عند مستوى الجرف بالضبط؟",
    "GAP_SWEEP_EQH_BASIS": "KNOWLEDGE_GAP: أي تأرجح سابق يقارَن بالثاني لاعتبار القمتين متساويتين، وبأي مدى بحث؟",
    "GAP_SWEEP_QUALITATIVE": "KNOWLEDGE_GAP: ما المعيار الكمي المقابل لـ«a sharp spike with a long wick»؟",
    "GAP_D_WINDOW": "KNOWLEDGE_GAP: كم عدد الشموع السابقة في «3–5» التي تُقاس عليها الإزاحة، ولا يُختار منها عدد؟",
    "GAP_D_GAP_DEFINITION": "KNOWLEDGE_GAP: ما تعريف «الفجوة» في «without a gap there is no ICT displacement»؟",
    "GAP_D_QUALITATIVE": "KNOWLEDGE_GAP: ما المعيار الكمي المقابل لـ«energetic» و«bodies that stand out» في أي نص أصلي؟",
    "GAP_D_CLUSTER": "KNOWLEDGE_GAP: هل التجمع القصير إزاحة أم شمعة واحدة فقط؟",
    "GAP_D_PRIOR_SWEEP": "KNOWLEDGE_GAP: هل الجرف السابق شرط للإزاحة، فلا اقتباس يصرّح به؟",
    "GAP_D_SWEEP_LEVEL": "KNOWLEDGE_GAP: أي مستوى جرف يُشترط قبل الإزاحة إذا كان شرطًا؟",
    # Added with the code, not present in spec §10 when the spec was committed:
    # the catalog settles no rule for a value exactly equal to a printed threshold.
    "GAP_EQUAL_THRESHOLD": "KNOWLEDGE_GAP: ما حكم القيمة المساوية للعتبة المطبوعة بالضبط، لا أعلى منها ولا أدنى؟",
    # Added in C1b for owner decision D2, family V-D-C.  The sources print the multiple
    # (1.5) and the length (14) but never the formula of ATR or of true range.
    "GAP_D_ATR_FORMULA": "KNOWLEDGE_GAP: ATR formula — كيف تُحسب ATR(14): ما صيغة المدى الحقيقي، وما نوع التنعيم، وهل الشمعة المقيسة داخل النافذة؟",
}

# Print status of every gap.  Three states only, and nothing is promised that has no path.
PRINTED_PER_RESULT = "PRINTED_PER_RESULT"
PRINTED_IN_DIMENSION_GAPS = "PRINTED_IN_DIMENSION_GAPS"
NOT_PRINTABLE = "NOT_PRINTABLE"

GAP_PROMISE = {
    # printed inside the `gaps` list of a result
    "GAP_CLUSTER_BOUND": {"dimension": "OB-D3", "print_status": PRINTED_PER_RESULT},
    "GAP_DOJI_BLOCK": {"dimension": "OB-D3", "print_status": PRINTED_PER_RESULT},
    "GAP_OB_MOVE_BOUNDS": {"dimension": "OB-D19", "print_status": PRINTED_PER_RESULT},
    "GAP_SWEEP_DISTANCE": {"dimension": "E-D4", "print_status": PRINTED_PER_RESULT},
    "GAP_SWEEP_EQUAL_CLOSE": {"dimension": "E-D5", "print_status": PRINTED_PER_RESULT},
    "GAP_SWEEP_EQH_BASIS": {"dimension": "E-D6", "print_status": PRINTED_PER_RESULT},
    "GAP_D_QUALITATIVE": {"dimension": "D-D5", "print_status": PRINTED_PER_RESULT},
    "GAP_D_GAP_DEFINITION": {"dimension": "D-D4", "print_status": PRINTED_PER_RESULT},
    "GAP_D_WINDOW": {"dimension": "D-D2", "print_status": PRINTED_PER_RESULT},
    "GAP_D_CLUSTER": {"dimension": "D-D6", "print_status": PRINTED_PER_RESULT},
    "GAP_D_PRIOR_SWEEP": {"dimension": "D-D7", "print_status": PRINTED_PER_RESULT},
    "GAP_EQUAL_THRESHOLD": {"dimension": "D-D1/D-D2/D-D3/E-D5", "print_status": PRINTED_PER_RESULT},
    "GAP_D_ATR_FORMULA": {"dimension": "V-D-C", "print_status": PRINTED_PER_RESULT},
    # printed in the separate `dimension_gaps` field of every result of its concept
    "GAP_D_SWEEP_LEVEL": {"dimension": "D-D7", "print_status": PRINTED_IN_DIMENSION_GAPS},
    # no function exists for their dimension: recorded, never invented
    "GAP_WICK_INVALIDATION": {"dimension": "OB-D10", "print_status": NOT_PRINTABLE},
    "GAP_LOCATION": {"dimension": "OB-D15", "print_status": NOT_PRINTABLE},
    "GAP_OB_DISPLACEMENT_FILTER": {"dimension": "OB-D16", "print_status": NOT_PRINTABLE},
    "GAP_STOP_AND_SIZE": {"dimension": "OB-D17/OB-D18", "print_status": NOT_PRINTABLE},
    "GAP_SWEEP_QUALITATIVE": {"dimension": "E-D7", "print_status": NOT_PRINTABLE},
}

# The gaps of each concept that are NOT carried by the frozen per-result `gaps` list of C1,
# printed instead in the `dimension_gaps` field of every result of that concept.
DIMENSION_GAPS = {
    "order_block": (
        "GAP_WICK_INVALIDATION",
        "GAP_LOCATION",
        "GAP_OB_DISPLACEMENT_FILTER",
        "GAP_STOP_AND_SIZE",
    ),
    "displacement": ("GAP_D_SWEEP_LEVEL",),
    "liquidity_sweep": ("GAP_SWEEP_QUALITATIVE",),
}

FLAG_OWNER_OVERRIDE = "FLAGGED_FOR_OWNER_OVERRIDE"


def gap(gap_id: str) -> dict:
    """One printed gap entry, with its exact text."""

    if gap_id not in GAPS:
        raise KeyError("unknown gap id: %r" % (gap_id,))
    return {"id": gap_id, "text": GAPS[gap_id]}


def gap_ids_of(concept: str) -> tuple:
    """The gap ids that this concept prints outside its per-result `gaps` list."""

    if concept not in DIMENSION_GAPS:
        raise KeyError("unknown concept for dimension gaps: %r" % (concept,))
    return DIMENSION_GAPS[concept]


def dimension_gaps(concept: str) -> list:
    """The dimension-level gap entries of one concept, with their print status.

    A gap of this list is never a rule: it either is printed in this field, or it is
    labelled NOT_PRINTABLE because the dimension that promises it has no function here.
    """

    out = []
    for gap_id in gap_ids_of(concept):
        promise = GAP_PROMISE[gap_id]
        out.append(
            {
                "id": gap_id,
                "text": GAPS[gap_id],
                "dimension": promise["dimension"],
                "print_status": promise["print_status"],
            }
        )
    return out


def as_candles(rows) -> list:
    """Validate and normalise a candle sequence; refuse anything malformed.

    Every refusal is an exception, never a silent default:
      * a mapping without `closed`            -> raise (no implicit True)
      * `closed` that is not a bool            -> raise
      * a non-numeric price                    -> raise
      * high < low, open or close out of range -> raise (from Candle)
    """

    if rows is None:
        raise ValueError("candles must be provided")
    items = list(rows)
    if not items:
        raise ValueError("at least one candle is required")

    out = []
    for index, row in enumerate(items):
        if isinstance(row, Candle):
            out.append(row)
            continue
        if not isinstance(row, Mapping):
            raise ValueError("candle %d is neither a Candle nor a mapping" % index)
        for key in REQUIRED_CANDLE_KEYS:
            if key not in row:
                if key == "closed":
                    raise ValueError(
                        "candle %d is missing the explicit 'closed' flag" % index
                    )
                raise ValueError("candle %d is missing key %r" % (index, key))
        for key in PRICE_KEYS:
            value = row[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("candle %d field %r is not numeric" % (index, key))
        if not isinstance(row["closed"], bool):
            raise ValueError("candle %d 'closed' flag must be a bool" % index)
        out.append(
            Candle(
                open=float(row["o"]),
                high=float(row["h"]),
                low=float(row["l"]),
                close=float(row["c"]),
                closed=row["closed"],
            )
        )
    return out


def require_number(name: str, value) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("%s must be a number" % name)
    return float(value)


def require_index(name: str, value, limit: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("%s must be an int" % name)
    if value < 0 or value >= limit:
        raise ValueError("index t is outside the candle list")
    return value


def require_choice(name: str, value, allowed) -> str:
    if value is None:
        raise ValueError("%s must be provided explicitly" % name)
    if value not in allowed:
        raise ValueError("unknown %s variant: %r" % (name, value))
    return value


def sorted_claims(claim_groups) -> list:
    flat = set()
    for group in claim_groups:
        flat.update(group)
    return sorted(flat)
