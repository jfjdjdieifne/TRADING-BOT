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

# Every gap text printed by this step.  A gap is never resolved by a guess.
GAPS = {
    "GAP_CLUSTER_BOUND": "KNOWLEDGE_GAP: كيف تُحدّ حدود تجمع الشموع المعارضة (بداية التجمع ونهايته)؟",
    "GAP_DOJI_BLOCK": "KNOWLEDGE_GAP: ما حكم شمعة معارضة إغلاقها يساوي افتتاحها، هل تُعدّ معارضة؟",
    "GAP_OB_MOVE_BOUNDS": "KNOWLEDGE_GAP: أي شموع تُعدّ «الحركة» التي تكسر البنية، وما أول شمعة فيها وآخرها؟",
    "GAP_SWEEP_DISTANCE": "KNOWLEDGE_GAP: ما مقدار الاختراق الأدنى وما سرعته ليُسمّى جرفًا لا كسرًا؟",
    "GAP_SWEEP_EQUAL_CLOSE": "KNOWLEDGE_GAP: ما حكم إغلاق الجسم عند مستوى الجرف بالضبط؟",
    "GAP_SWEEP_EQH_BASIS": "KNOWLEDGE_GAP: أي تأرجح سابق يقارَن بالثاني لاعتبار القمتين متساويتين، وبأي مدى بحث؟",
    "GAP_D_WINDOW": "KNOWLEDGE_GAP: كم عدد الشموع السابقة في «3–5» التي تُقاس عليها الإزاحة، ولا يُختار منها عدد؟",
    "GAP_D_GAP_DEFINITION": "KNOWLEDGE_GAP: ما تعريف «الفجوة» في «without a gap there is no ICT displacement»؟",
    "GAP_D_QUALITATIVE": "KNOWLEDGE_GAP: ما المعيار الكمي المقابل لـ«energetic» و«bodies that stand out» في أي نص أصلي؟",
    "GAP_D_CLUSTER": "KNOWLEDGE_GAP: هل التجمع القصير إزاحة أم شمعة واحدة فقط؟",
    "GAP_D_PRIOR_SWEEP": "KNOWLEDGE_GAP: هل الجرف السابق شرط للإزاحة، فلا اقتباس يصرّح به؟",
    # Added with the code, not present in spec §10 when the spec was committed:
    # the catalog settles no rule for a value exactly equal to a printed threshold.
    "GAP_EQUAL_THRESHOLD": "KNOWLEDGE_GAP: ما حكم القيمة المساوية للعتبة المطبوعة بالضبط، لا أعلى منها ولا أدنى؟",
}

FLAG_OWNER_OVERRIDE = "FLAGGED_FOR_OWNER_OVERRIDE"


def gap(gap_id: str) -> dict:
    """One printed gap entry, with its exact text."""

    if gap_id not in GAPS:
        raise KeyError("unknown gap id: %r" % (gap_id,))
    return {"id": gap_id, "text": GAPS[gap_id]}


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
