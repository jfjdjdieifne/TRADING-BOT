#!/usr/bin/env python3
"""Compare frozen, published illustrative cases with B1 without altering it.

    python3 b1_teacher_test/run_teacher.py

Only the standard library is used. The normal Candle constructor is used for
complete OHLC. For a partial published example, the direct detector is probed
with an object containing only printed fields. This is NOT a claim that the
normal validated Candle interface accepts incomplete OHLC. Missing prices are
never fabricated. The report distinguishes the source's rule from V2, and it
never selects or implements a displacement definition in B1.
"""
from __future__ import annotations

import copy
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ENGINE = ROOT / "project/trading_project/docs/research/huddleston_study/engine_v1/b1_candles"
FIXTURE = HERE / "teacher_cases.json"
CASES_DOC = HERE / "TEACHER_CASES.md"
RESULT = HERE / "TEACHER_RESULTS.md"
FREEZE_COMMIT = "62d8be39e629a4aab9afa6d0df8c01c6d26ea4da"
EXPECTED_HASHES = {
    FIXTURE: "2e1dc9e11800667077e1b22dd042ff7ee88fd1cc6c3812916630df4d63ce64fa",
    CASES_DOC: "0ea7533f9555a755d18392238dea8de57e2c448f0fa38cf1d0f9b40b95450490",
}
OHLC = ("open", "high", "low", "close")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# Refuse to rerun against a changed oracle while claiming the frozen commitment.
for file_path, digest in EXPECTED_HASHES.items():
    if sha(file_path) != digest:
        raise SystemExit(f"Frozen input changed: {file_path}; make a new freeze first")

sys.path.insert(0, str(ENGINE))
from candle import Candle  # noqa: E402
from fvg import fvg_at  # noqa: E402
from swing import swing_at  # noqa: E402


def materialize(case):
    """Copy only published fields; completion is added only when source states it."""
    completed = case["closure"] != "UNSTATED"
    normal_candle = completed and all(all(k in row for k in OHLC) for row in case["bars"])
    result = []
    for row in case["bars"]:
        args = {field: Decimal(value) for field, value in row.items()}
        if completed:
            # Source says these bars have closed at the observation time, not a
            # missing *price*. TradeZoro's unknown completion remains absent.
            args["closed"] = True
        result.append(Candle(**args) if normal_candle else SimpleNamespace(**args))
    return result, "Candle (OHLC كامل)" if normal_candle else "مباشرة جزئية فقط"


def snapshot(objects):
    return copy.deepcopy([vars(c) for c in objects])


def invoke(function, candles, index, direction):
    before = snapshot(candles)
    try:
        record = function(candles, index, direction)
        outcome = {"kind": "return", "record": record}
    except AttributeError as exc:
        # Only an actually absent candle field is a missing-data limitation;
        # an unrelated AttributeError is an engine/interface error.
        field = getattr(exc, "name", None)
        is_missing = field in (*OHLC, "closed") and any(not hasattr(c, field) for c in candles)
        outcome = {"kind": "missing" if is_missing else "error",
                   "error": f"{type(exc).__name__}: {exc}"}
    except Exception as exc:  # Preserve unexpected interface errors in the report.
        outcome = {"kind": "error", "error": f"{type(exc).__name__}: {exc}"}
    outcome["unchanged"] = before == snapshot(candles)
    return outcome


def decimal_text(value):
    return str(value)


def bounds(record):
    b = record.get("bounds")
    if b is None:
        return None
    return b["lower_bound"]["value"], b["upper_bound"]["value"]


def bound_text(pair):
    return "—" if pair is None else f"[{decimal_text(pair[0])}, {decimal_text(pair[1])}]"


def expected_bounds(obj):
    if "lower" not in obj:
        return None
    return Decimal(obj["lower"]), Decimal(obj["upper"])


def inline_status(outcome):
    if outcome["kind"] != "return":
        return f"{outcome['kind']}: {outcome['error']}"
    return outcome["record"].get("status", "MISSING_STATUS")


def check_v2(outcome, status, wanted_bounds=None, candidate=None, fvg=False,
             side=None, source_values=None):
    if outcome["kind"] == "missing":
        return "NOT_RUN_MISSING_FIELDS"
    if outcome["kind"] == "error":
        return "ENGINE_ERROR"
    record = outcome["record"]
    try:
        good = outcome["unchanged"] and record.get("status") == status and record.get("tier") == "TIER2"
        if fvg:
            good = good and record.get("version") == "V-B-00"
            good = good and record.get("concept") == f"fvg_{side}"
            good = good and record.get("source_ids") == ["B1", "B2", "B3", "B4"]
            good = good and record.get("candle_indices") == {"c1": 0, "c2": 1, "c3": 2}
            good = good and bounds(record) == wanted_bounds
            good = good and any(g.get("id") == "INVALIDATION_UNDECIDED" for g in record.get("gates", []))
            if status == "UNDECIDED":
                good = good and any(g.get("id") == "GAP_TOUCH_FVG" for g in record.get("open_gaps", []))
            comp = record.get("comparison", {})
            good = good and (comp.get("first_wick"), comp.get("third_wick")) == source_values
        if candidate is not None:
            # Engine's record uses 0-based indices, the source uses 1-based bars.
            good = good and record.get("version") == "V-A-00"
            good = good and record.get("concept") == f"swing_{side}"
            sources = ["A1", "A4", "A5"] if side == "high" else ["A1", "A5"]
            good = good and record.get("source_ids") == sources
            good = good and record.get("candle_indices") == {
                "c1": candidate - 2, "c2": candidate - 1, "c3": candidate}
            comparison = record.get("comparison", {})
            good = good and comparison.get("relevant_side") == side
            good = good and comparison.get("values") == source_values
    except (AttributeError, KeyError, TypeError):
        return "V2_MISMATCH"
    return "V2_MATCH" if good else "V2_MISMATCH"


def teacher_fvg_relation(case, outcome):
    if outcome["kind"] != "return":
        return "NOT_COMPARED"
    rec = outcome["record"]
    verdict = case["teacher"]["verdict"]
    if verdict == "NO_POSITIVE_WIDTH_GAP" and rec.get("status") == "UNDECIDED":
        return "RULE_DIFFERENCE"
    same = rec.get("status") == verdict
    if verdict == "YES":
        actual = bounds(rec)
        same = same and actual == expected_bounds(case["teacher"])
        if actual is not None:
            # Midpoint is arithmetic performed here, not a field returned by B1.
            same = same and (actual[0] + actual[1]) / Decimal(2) == Decimal(case["teacher"]["midpoint"])
    return "AGREES" if same else "DIFFERS"


def safe_cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def source_rule_for_swing(case, side, candidate):
    """Apply the source's printed 2+2 rule; this is not an explicit label."""
    i = candidate - 1
    values = [Decimal(row[side]) for row in case["bars"]]
    if i < 2 or i + 2 >= len(values):
        return "NOT_FULLY_TESTABLE"
    neighbors = (values[i - 2], values[i - 1], values[i + 1], values[i + 2])
    is_pivot = (all(values[i] > x for x in neighbors) if side == "high" else
                all(values[i] < x for x in neighbors))
    return "YES" if is_pivot else "NO"


def main():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert data["schema"] == "teacher_cases_v1"
    fvg_rows = []
    swing_rows = []
    engine_calls = 0

    for case in data["fvg_cases"]:
        candles, interface = materialize(case)
        outcome = invoke(fvg_at, candles, 2, case["direction"])
        engine_calls += 1
        c1_field, c3_field = (("high", "low") if case["direction"] == "bullish" else ("low", "high"))
        source_values = (Decimal(case["bars"][0][c1_field]), Decimal(case["bars"][2][c3_field]))
        verdict = check_v2(outcome, case["v2_prediction"]["status"],
                           expected_bounds(case["v2_prediction"]), fvg=True,
                           side=case["direction"], source_values=source_values)
        relation = teacher_fvg_relation(case, outcome)
        fvg_rows.append({"case": case, "interface": interface, "outcome": outcome,
                         "v2": verdict, "teacher_relation": relation})

    sf = next(c for c in data["swing_cases"] if c["id"] == "SF-SERIES")
    sf_candles, sf_interface = materialize(sf)
    source_pivots = {
        side: {item["candidate"]: item for item in sf["teacher"]["highs" if side == "high" else "lows"]}
        for side in ("high", "low")
    }
    for candidate in range(2, 13):
        for side in ("high", "low"):
            # t is the 0-based C3 index. Prefix ends at candidate's first
            # right neighbour and never reveals the teacher's second neighbour.
            prefix = sf_candles[: candidate + 1]
            outcome = invoke(swing_at, prefix, candidate, side)
            engine_calls += 1
            v2_status = "YES" if candidate in sf["v2_prediction"][f"{side}_yes_candidates"] else "NO"
            values = {f"c{j+1}": Decimal(sf["bars"][candidate - 2 + j][side]) for j in range(3)}
            v2 = check_v2(outcome, v2_status, candidate=candidate, side=side, source_values=values)
            if candidate in sf["teacher"]["testable_candidate_bars"]:
                other = "low" if side == "high" else "high"
                if candidate not in source_pivots[side] and candidate in source_pivots[other]:
                    # The article labels the other *bars* as failures; it does
                    # not explicitly label the opposite side of a named pivot.
                    # Keep this arithmetic inference out of teacher-judgment counts.
                    derived = source_rule_for_swing(sf, side, candidate)
                    teacher_status = derived + "†"
                    rel = ("NOT_COMPARED" if outcome["kind"] != "return" else
                           "DERIVED_RULE_MATCH" if inline_status(outcome) == derived else "DERIVED_RULE_DIFFERENCE")
                else:
                    teacher_status = "YES" if candidate in source_pivots[side] else "NO"
                    agrees = inline_status(outcome) == teacher_status
                    if teacher_status == "YES" and outcome["kind"] == "return":
                        reported = outcome["record"].get("comparison", {}).get("values", {}).get("c2")
                        agrees = agrees and reported == Decimal(source_pivots[side][candidate]["price"])
                    rel = ("NOT_COMPARED" if outcome["kind"] != "return" else
                           "AGREES_GEOMETRY" if agrees else "DIFFERS_GEOMETRY")
            else:
                teacher_status, rel = "NOT_FULLY_TESTABLE", "SOURCE_UNTESTABLE"
            swing_rows.append({"case": sf["id"], "side": side, "candidate": candidate,
                               "interface": sf_interface, "teacher": teacher_status,
                               "outcome": outcome, "v2": v2, "teacher_relation": rel})

    for case in data["swing_cases"]:
        if case["id"] == "SF-SERIES":
            continue
        candles, interface = materialize(case)
        candidate = case["teacher"]["candidate"]
        outcome = invoke(swing_at, candles[: candidate + 1], candidate, case["direction"])
        engine_calls += 1
        values = {f"c{j+1}": Decimal(case["bars"][candidate - 2 + j][case["direction"]]) for j in range(3)}
        v2 = check_v2(outcome, case["v2_prediction"]["status"], candidate=candidate,
                      side=case["direction"], source_values=values)
        agrees = inline_status(outcome) == case["teacher"]["verdict"]
        if outcome["kind"] == "return":
            reported = outcome["record"].get("comparison", {}).get("values", {}).get("c2")
            agrees = agrees and reported == Decimal(case["teacher"]["price"])
        rel = ("NOT_COMPARED" if outcome["kind"] != "return" else
               "AGREES_GEOMETRY" if agrees else "DIFFERS_GEOMETRY")
        swing_rows.append({"case": case["id"], "side": case["direction"], "candidate": candidate,
                           "interface": interface, "teacher": case["teacher"]["verdict"],
                           "outcome": outcome, "v2": v2, "teacher_relation": rel})

    all_rows = fvg_rows + swing_rows
    v2_counts = Counter(row["v2"] for row in all_rows)
    fvg_teacher_counts = Counter(row["teacher_relation"] for row in fvg_rows)
    swing_teacher_counts = Counter(row["teacher_relation"] for row in swing_rows)
    unchanged = sum(row["outcome"]["unchanged"] for row in all_rows)
    partial = sum("جزئية" in row["interface"] for row in all_rows)
    exception_rows = [r for r in all_rows if r["outcome"]["kind"] != "return"]

    lines = [
        "# B1 — نتائج المقارنة الوصفية مع أمثلة منشورة",
        "",
        "هذا التقرير يُولَّد دون شبكة من `run_teacher.py` والبيانات المجمدة، ولا يغيّر المحرك أو يختار تعريف الإزاحة. الأرقام أسعار تعليمية افتراضية منشورة لا بيانات سوق. العدّ أدناه أحكام/استدعاءات مرتبطة، لا عينات مستقلة ولا مقياس دقة إحصائية.",
        "",
        f"- التزام تجميد الأمثلة والتوقعات: `{FREEZE_COMMIT}`؛ بعده فقط فُحص تنفيذ B1.",
        f"- بصمة JSON المجمد: `{sha(FIXTURE)}`؛ بصمة وثيقة التوقعات: `{sha(CASES_DOC)}`.",
        "- أربعة ناشرين وخمس صفحات مختارة؛ 8 أحكام فجوة، و16 حكماً لتأرجح (6 موجبة و10 سلبية جماعية) على ثلاث سلاسل، إضافةً إلى 4 أحكام محسوبة من قاعدة المصدر لا من حكم فردي صريح. المرايا والبدائل والنوافذ ليست مستقلة.",
        "- من حيث التجهيزات: سلسلتا HomeDadPro الكاملة معكوستان، وتجهيز TradeZoro واحد مع بديل مضاد له، وسلسلة SwingFolio واحدة، وسلستا LuxAlgo منفصلتان. هذه ستة تجهيزات أصلية مطبوعة، إضافة إلى أربعة فحوص حدود جزئية، وليست ست سلاسل مستقلة إحصائياً. اختلاف الناشرين لا يثبت وحده استقلال التأليف.",
        f"- استدعاءات الكاشف: **{engine_calls}** = {len(fvg_rows)} فجوة + {len(swing_rows)} تأرجح؛ {partial} منها بمدخل مباشر جزئي، و{engine_calls - partial} بمُنشئ `Candle` الكامل. {unchanged}/{engine_calls} مدخلاً بقي بلا تغيير.",
        f"- مقارنة توقعات V2 في الاستدعاءات المنفذة: **{v2_counts['V2_MATCH']} مطابقة**، **{v2_counts['V2_MISMATCH']} اختلاف**، **{v2_counts['NOT_RUN_MISSING_FIELDS']} تعذر لنقص الحقول في الواجهة المباشرة**، **{v2_counts['ENGINE_ERROR']} خطأ واجهة**. هذا لا يزيل تعذر إنشاء الشموع الكاملة للأمثلة الجزئية. تُحسب الأحكام المكررة على سلسلة واحدة كرصد منفصل لا كاستقلال.",
        f"- أحكام الفجوة مقابل المصدر: {fvg_teacher_counts['AGREES']} توافقاً في الحكم/الحدود، {fvg_teacher_counts['RULE_DIFFERENCE']} اختلاف قاعدة معلناً، {fvg_teacher_counts['DIFFERS']} اختلافاً آخر، {fvg_teacher_counts['NOT_COMPARED']} دون مقارنة. المنتصف، إن ذُكر، يحسبه البرنامج من الحدين لا يخرجه المحرك.",
        f"- التأرجح مقابل الأحكام الصريحة/الجماعية للمصدر: {swing_teacher_counts['AGREES_GEOMETRY']} توافقاً هندسياً، {swing_teacher_counts['DIFFERS_GEOMETRY']} اختلافاً؛ وبالمقابل {swing_teacher_counts['DERIVED_RULE_MATCH']} توافقات محسوبة من قاعدة المصدر وليست أحكاماً فردية صريحة، و{swing_teacher_counts['DERIVED_RULE_DIFFERENCE']} اختلاف منها، و{swing_teacher_counts['NOT_COMPARED']} دون مقارنة، و{swing_teacher_counts['SOURCE_UNTESTABLE']} رصود طرفية لا حكم للمصدر فيها. توقيت التأكيد مختلف كما يلي.",
        "- `Candle` يتطلب `open/high/low/close`. في الأمثلة الناقصة استُخدمت `swing_at`/`fvg_at` مباشرة بكائنات تحتوي الحقول المنشورة فقط؛ هذه واجهة تقبل duck typing ولا تتحقق من صحة OHLC الكاملة. القبول هنا **لا** يعني إمكان إدخالها بمُنشئ `Candle` أو معرفة الأسعار الناقصة. TradeZoro لا يصرّح باكتمال الثالثة؛ لم يُمرَّر لها علم إغلاق، والمقارنة هندسية فقط.",
        "- بدأ البحث الإضافي قبل استكمال أربع صفحات مفهرسة، خلاف الترتيب المطلوب؛ سُجل ذلك في `TEACHER_CASES.md`. لم يُصلح إكمالها اللاحق هذا الخرق الزمني.",
        "",
        "## الفجوة: حكم المصدر، وتوقع V2، وخرج B1",
        "",
        "| الحالة | واجهة الإدخال | حكم المصدر | توقع V2 | خرج B1 وحدوده | علاقة المصدر | فحص V2 |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in fvg_rows:
        case, out = row["case"], row["outcome"]
        teacher = case["teacher"]["verdict"]
        if "lower" in case["teacher"]:
            teacher += " " + bound_text(expected_bounds(case["teacher"]))
        actual = inline_status(out)
        if out["kind"] == "return" and bounds(out["record"]) is not None:
            actual += " " + bound_text(bounds(out["record"]))
        lines.append("| " + " | ".join(map(safe_cell, (case["id"], row["interface"], teacher,
                     case["v2_prediction"]["status"], actual, row["teacher_relation"], row["v2"]))) + " |")
    lines += [
        "",
        "في `HDP-EDGE-TOUCH` يقول المدرّس إن العرض صفر فلا فجوة **موجبة العرض**؛ V2 يترك التلامس `UNDECIDED`. هذه نتيجة مختلفة لقواعد مختلفة، لا عيباً آلياً ولا قراراً لحسمها. يتحقق فحص V2 من وجود `INVALIDATION_UNDECIDED` في كل سجل مرتجع؛ لم يُختبر إبطال لاحق. فروق إغلاق الشمعة الثالثة تبقى سؤال مالك مفتوحاً.",
        "",
        "المدخلات الجزئية لا تكفي لمُنشئ `Candle` العادي: حالات حدود HomeDadPro تطبع طرفاً واحداً لكل من الأولى والثالثة ولا تطبع OHLC الوسطى؛ TradeZoro يحذف أعلى/أدنى الوسطى وافتتاح/إغلاق الطرفين؛ SwingFolio يحذف الافتتاح والإغلاق؛ وLuxAlgo يحذف ثلاث قيم في كل سلسلة أحادية الجهة. إدخال المدخلات نفسها عبر مُنشئ شموع كامل غير ممكن دون اختلاق القيم، لذا لم يُجرَ.",
        "",
        "## سلسلة SwingFolio: المرشح نفسه لا مرشح آخر",
        "",
        "الأرقام 1-based. عمود B1 عند إغلاق الجار الأول للمرشح؛ حكم المصدر النهائي يستند إلى جارين على كل جانب. الصفوف التسعة على سلسلة واحدة: 14 مقارنة لحكم صريح أو جماعي، و4 مقارنات معلَّمة † محسوبة من قاعدة المصدر وليست حكماً فردياً صريحاً.",
        "",
        "| المرشح | المصدر قمة | B1 قمة عند المرشح+1 | المصدر قاع | B1 قاع عند المرشح+1 |",
        "|---:|---|---|---|---|",
    ]
    lookup = {(r["case"], r["side"], r["candidate"]): r for r in swing_rows}
    for candidate in range(3, 12):
        high = lookup[(sf["id"], "high", candidate)]
        low = lookup[(sf["id"], "low", candidate)]
        lines.append(f"| {candidate} | {high['teacher']} | {safe_cell(inline_status(high['outcome']))} | {low['teacher']} | {safe_cell(inline_status(low['outcome']))} |")
    lines += [
        "",
        "† **استدراك على عدّ الملف المجمد:** قوله إن السلبيات الأربع عشرة كلها مستفادة من عبارة المدرّس الجماعية أوسع من ظاهر النص. العبارة تقول إن «الأشرطة الأخرى القابلة للفحص تفشل»، ولا تسمي صراحة الجهة المقابلة للقمة/القاع الأربعة المعلَّمة. لذلك نعدّ عشر سلبيات على الأشرطة الأخرى ضمن الحكم الجماعي، ونحسب الجهات الأربع المقابلة من قاعدة 2+2 المنشورة وحدها، مفصولة عن أحكام المدرّس. لم تتغير البيانات أو توقعات V2 المجمدة؛ هذا تصحيح إسناد وعدّ، لا اختيار بعد النتائج.",
        "",
        "حافتا V2 الإضافيتان ليستا حكمين سلبيين للمصدر:", "", "| المرشح | جهة | المصدر | B1 عند المرشح+1 |", "|---:|---|---|---|"]
    for candidate in (2, 12):
        for side in ("high", "low"):
            row = lookup[(sf["id"], side, candidate)]
            lines.append(f"| {candidate} | {side} | NOT_FULLY_TESTABLE | {safe_cell(inline_status(row['outcome']))} |")
    lines += [
        "",
        "## توقيت التأكيد: اختلاف قاعدة، لا استخدام للمستقبل",
        "",
        "يبيّن الجدول رصد B1 عند الجار الأول وتأكيد المصدر بعد جارين. نمرر إلى B1 بادئة تنتهي عند البار الأول، فلا نُدخل بار المصدر الثاني في نتيجة B1 المبكرة. السعر المنقول من خرج B1 هو طرف المرشح `comparison.values.c2`.",
        "",
        "| المثال | الجهة / المرشح | سعر المصدر | تأكيد المصدر | رصد B1 عند الجار الأول وسعره | فحص V2 |",
        "|---|---|---:|---:|---|---|",
    ]
    for side in ("high", "low"):
        for candidate, teacher in source_pivots[side].items():
            row = lookup[(sf["id"], side, candidate)]
            result = inline_status(row["outcome"])
            record = row["outcome"].get("record", {})
            value = record.get("comparison", {}).get("values", {}).get("c2", "—")
            lines.append(f"| SF-SERIES | {side} / {candidate} | {teacher['price']} | {teacher['confirmed_at']} | {safe_cell(result)} @ {candidate + 1}: {value} | {row['v2']} |")
    for case in data["swing_cases"]:
        if case["id"] == "SF-SERIES":
            continue
        candidate, side = case["teacher"]["candidate"], case["direction"]
        row = lookup[(case["id"], side, candidate)]
        record = row["outcome"].get("record", {})
        value = record.get("comparison", {}).get("values", {}).get("c2", "—")
        lines.append(f"| {case['id']} | {side} / {candidate} | {case['teacher']['price']} | {case['teacher']['confirmed_at']} | {safe_cell(inline_status(row['outcome']))} @ {candidate + 1}: {value} | {row['v2']} |")
    low11 = lookup[(sf["id"], "low", 11)]
    lines += [
        "",
        f"مثال معلن تحديداً: عند البار 12 يقول SwingFolio إن قاع 11 لم يتأكد بعد في قاعدة 2+2، بينما خرج B1 للمرشح نفسه هو `{inline_status(low11['outcome'])}` وفق 1+1. هذا الفرق الزمني متوقع من عدد الجيران، ولا يُصنّف تلقائياً خطأً. سلسلتا LuxAlgo منفصلتان ولم تُجمع قمم إحداهما مع قيعان الأخرى.",
        "",
        "## الإزاحة: مقادير فقط، وكل متغير على حدة",
        "",
        "الإزاحة غير مبرمجة في B1؛ ما يلي حساب وصفي منفصل للجسم والمدى من الشمعة الثانية المنشورة، لا تطبيق محرك ولا حكم المدرّس لكل متغير. لا فائز ولا نسبة متغير إلى شخص.",
        "",
        "| الحالة | الجسم | المدى | الجسم ÷ المدى | الشموع السابقة المطبوعة |",
        "|---|---:|---:|---:|---:|",
    ]
    for case in data["fvg_cases"][:2]:
        middle = case["bars"][1]
        body = abs(Decimal(middle["close"]) - Decimal(middle["open"]))
        ran = Decimal(middle["high"]) - Decimal(middle["low"])
        ratio = body / ran
        assert body == Decimal(data["displacement"]["expected_body"])
        assert ran == Decimal(data["displacement"]["expected_range"])
        assert ratio == Decimal(data["displacement"]["expected_body_divided_by_range"])
        lines.append(f"| {case['id']} | {body} | {ran} | {ratio * 100}% | 1 |")
    lines += [
        "",
        "| المتغير | الوصف المنفصل على كل من المثالين المعكوسين |",
        "|---|---|",
        "| `V-D-A-1` | 80% عند الحد الأعلى لنطاق 60–80% المطبوع؛ لا نختار عتبة واحدة. |",
        "| `V-D-A-2` | 80% أعلى من القيمة التقريبية 75%؛ لا نفترض سماحية رقمية للتقريب. |",
        "| `V-D-A-3` | 80% أعلى من 70%. |",
        "| `V-D-A-4` | 80% تساوي 80%. |",
        "| `V-D-B-1` | `NOT_MEASURABLE`؛ شمعة سابقة واحدة متاحة بدلاً من 3–5. |",
        "| `V-D-B-2` | `NOT_MEASURABLE`؛ شمعة سابقة واحدة متاحة بدلاً من 10. |",
        "| `V-D-C-1` | `NOT_MEASURABLE`؛ ATR(14) وتاريخه غير منشورين. |",
        "",
        "الحالات الأخرى لا تطبع مدخلات الجسم والمدى أو التاريخ اللازم؛ لم تُستكمل. لا تؤخذ هذه المقارنات الحسابية كتأييد أو تعريف مرجعي أو تصنيف من المحرك.",
        "",
        "## حدود الاستنتاج والأسئلة المفتوحة",
        "",
        "- الاختبار الكامل عبر مُنشئ `Candle` اقتصر على سلسلتين كاملتين معكوستين من ناشر واحد. حتى المقارنات الجزئية من ناشرين آخرين قليلة ومختارة للتعليم، فلا يصح استنتاج دقة عامة أو أداء تداول.",
        "- الصفحة ذات المنشأ غير المحقق ومثال السوق المحتمل لم يُشغَّلا، وصفحة Swoopr المعلنة AI-assisted مستبعدة احتياطاً. لا دليل من ذلك وحده على طريقة تأليف الصفحات المختارة؛ انظر سجل المصادر في `TEACHER_CASES.md`.",
        "- تعرض صفحات أخرى، منها NinjaTrader وTopFX، حدوداً افتراضية جزئية لم تُدرج في هذه الدفعة المجمدة؛ عدم إدراجها لا يثبت استحالة فحصها جزئياً في دفعة لاحقة تُجمَّد مستقلة. في بديل TradeZoro استُبقيت حقول المثال الأصلي الأخرى في نقل صياغة «لو اختلف القاع»، لكن الكاشف الصعودي لا يحتاج إلا قمة الأولى وقاع الثالثة.",
        "- ترتيب `NO` و`UNDECIDED` و`PENDING`، الافتراض عند غياب علم الإغلاق، سلوك المدخل المشوَّه، واشتراط إغلاق ثالثة الفجوة تبقى مفتوحة كما في `OWNER_DECISIONS.md`؛ لا حسم لمالكها هنا.",
        "- لم تُستعمل بيانات سوق ولم تُعدّل ملفات المحرك. يبقى اختبار الواجهة الجزئية أقل قوة من اختبار مدخلات OHLC صالحة كاملة.",
        "",
        "## إعادة التشغيل والبصمات",
        "",
        "```sh",
        "python3 b1_teacher_test/run_teacher.py",
        "```",
        "",
        "يتحقق البرنامج من بصمتي الملفين المجمدين أعلاه قبل المقارنة، ويعيد كتابة هذا التقرير بصورة حتمية. يستخدم `Decimal` من الأسعار المطبوعة ويعرض المدخل الجزئي كما هو. بصمات التنفيذ المقروء:",
        "",
    ]
    for name in ("candle.py", "fvg.py", "swing.py"):
        lines.append(f"- `{name}`: `{sha(ENGINE / name)}`")
    if exception_rows:
        lines += ["", "### حالات تعذر التشغيل / أخطاء الواجهة", ""]
        for row in exception_rows:
            identifier = row["case"]["id"] if isinstance(row["case"], dict) else f"{row['case']}/{row['side']}/{row['candidate']}"
            lines.append(f"- `{identifier}`: {safe_cell(row['outcome']['error'])}")
    lines.append("")
    RESULT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {RESULT.relative_to(ROOT)}; calls={engine_calls}; V2={dict(v2_counts)}; "
          f"FVG-vs-teacher={dict(fvg_teacher_counts)}; swing-vs-teacher={dict(swing_teacher_counts)}")
    # A textual convention difference or an insufficient source does not fail.
    unexpected = (v2_counts["V2_MISMATCH"] + v2_counts["ENGINE_ERROR"] +
                  fvg_teacher_counts["DIFFERS"] + swing_teacher_counts["DIFFERS_GEOMETRY"] +
                  swing_teacher_counts["DERIVED_RULE_DIFFERENCE"])
    return 1 if unexpected else 0


if __name__ == "__main__":
    raise SystemExit(main())
