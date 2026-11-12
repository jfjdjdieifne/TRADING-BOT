"""Deterministic Arabic reports for the frozen 2022 diagnostics."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from .common import distribution, write_json
from .direction import DIRECTION_GRID
from .prediction_v2 import (
    entry_pair_summary,
    liquidity_summary,
    stand_aside_summary,
)

VARIANTS = ("R00", "V01", "V02", "V03", "V04", "V05")
DIRECTIONS = (("bullish", "شراء"), ("bearish", "بيع"))
OUTCOME_ARABIC = {
    "TARGET_FIRST": "هدف أولاً",
    "STOP_FIRST": "وقف أولاً",
    "HORIZON_EXPIRED": "انتهاء الأفق",
    "TRUNCATED": "بتر",
    "UNJUDGEABLE_SAME_BAR": "تعارض",
}
CLASS_ARABIC = {
    "DIRECTION-RIGHT-STOP-TOO-TIGHT": "اتجاه صحيح ووقف قريب",
    "DIRECTION-WRONG": "اتجاه خاطئ",
    "UNRESOLVED": "غير محسوم",
    "TARGET_FIRST": "هدف أولاً",
}
TARGET_CLASS_ARABIC = {
    "DAILY_PRIORITY_RULE_CONSEQUENCE": "أثر أولوية اليومي",
    "SAME_TIMEFRAME_AGE_PRIORITY_BUG_CANDIDATE": "اشتباه تقديم الأقدم داخل الإطار",
    "DISTANCE_TIE_RULE_CONSEQUENCE": "تعادل مسافة",
    "SELECTED_IS_NEAREST": "الهدف هو الأقرب",
    "REPLAY_MISMATCH_NEEDS_AUDIT": "عدم مطابقة يحتاج تدقيقاً",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def fnum(value: float | None, digits: int = 4) -> str:
    if value is None:
        return "غير متاح"
    text = f"{value:.{digits}f}".rstrip("0").rstrip(".")
    return "0" if text in {"-0", ""} else text


def pips(value: float | None, digits: int = 2) -> str:
    return fnum(value * 10000 if value is not None else None, digits)


def pct(numerator: int, denominator: int) -> str:
    return f"{100 * numerator / denominator:.2f}٪" if denominator else "غير متاح"


def count_pct(numerator: int, denominator: int) -> str:
    return f"{numerator} ({pct(numerator, denominator)})"


def rate(value: float | None) -> str:
    return f"{100 * value:.2f}٪" if value is not None else "غير متاح"


def cell_count(values: dict[str, int]) -> str:
    return " / ".join(
        str(values.get(name, 0))
        for name in ["DIRECTION_FIRST", "OPPOSITE_FIRST", "UNJUDGEABLE_SAME_BAR", "NO_TOUCH", "TRUNCATED"]
    )


def direction_counts(rows: list[dict[str, Any]], arm: str) -> dict[str, int]:
    names = ["DIRECTION_FIRST", "OPPOSITE_FIRST", "UNJUDGEABLE_SAME_BAR", "NO_TOUCH", "TRUNCATED", "UNAVAILABLE"]
    return {name: sum(row[arm]["outcome"] == name for row in rows) for name in names}


def direction_rate(counts: dict[str, int]) -> float | None:
    denominator = counts["DIRECTION_FIRST"] + counts["OPPOSITE_FIRST"]
    return counts["DIRECTION_FIRST"] / denominator if denominator else None


def paired(rows: list[dict[str, Any]]) -> tuple[int, float | None]:
    selected = [row for row in rows if row["paired_engine_random_judgeable"]]
    if not selected:
        return 0, None
    engine = sum(row["engine"]["outcome"] == "DIRECTION_FIRST" for row in selected)
    random = sum(row["random_same_month_same_direction"]["outcome"] == "DIRECTION_FIRST" for row in selected)
    return len(selected), (engine - random) / len(selected)


def header(title: str, paragraphs: Iterable[str]) -> list[str]:
    return [f"# {title}", "", *sum(([text, ""] for text in paragraphs), [])]


def table(headers: list[str], rows: Iterable[list[Any]]) -> list[str]:
    result = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    result.extend("| " + " | ".join(str(value) for value in row) + " |" for row in rows)
    result.append("")
    return result


def load_results(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    combined = json.loads((root / "combined_results.json").read_text(encoding="utf-8"))
    data: dict[str, Any] = {}
    for variant in VARIANTS:
        base = root / "diagnostics" / variant
        data[variant] = {
            "cases": read_jsonl(base / "post_stop_cases.jsonl"),
            "direction": read_jsonl(base / "direction_rows.jsonl"),
            "liquidity": read_jsonl(base / "v2_liquidity.jsonl"),
            "pairs": read_jsonl(base / "v2_entry_pairs.jsonl"),
            "aside": read_jsonl(base / "v2_stand_aside.jsonl"),
            "summary": json.loads((base / "summary.json").read_text(encoding="utf-8")),
        }
    return combined, data


def post_stop_report(combined: dict[str, Any], data: dict[str, Any]) -> str:
    lines = header(
        "تقرير تحليل ما بعد الوقف — 2022 فقط",
        [
            "شمل التحليل كل حالات الهدف قبل الوقف في المتغيرات الستة، دون اقتطاع أي متغير إلى عدد المرجع. لم يتغير المحرك، ولم تفرض نسبة وقف إلى هدف؛ النسبة المعروضة ناتج مرصود فقط.",
            f"عقد ما قبل الحساب `{combined['spec_commit']}`، وشيفرة التحليل `{combined['implementation_commit']}`، وبصمة المدخل `{combined['data']['sha256']}`. الأفق الأصلي 288 شمعة سوق والممتد 1152 من الدخول. لا بيانات لاحقة ولا أموال أو عمولات.",
            "نسب فئات الوقف مقامها الحالات الموقوفة في الصف. حالات الهدف أولاً والأفق المنتهي تظهر مستقلة ولا تدخل في مقام «الوقف ثم ماذا». الوسم بطيء جزء من فئة الاتجاه الصحيح وقف قريب، وليس فئة إضافية مستقلة.",
        ],
    )
    lines += [
        "## لماذا هذه الموجة والمنطقة والإطار؟",
        "",
        "لم يختر المحلل موجة أو منطقة بعد رؤية النتيجة. في `order_blocks.py:55–116` تشترط الكتلة إزاحة وكسر تأرجح مرشح، ثم تقرأ سلسلة الإغلاقات المعاكسة السابقة مباشرة. المرجع يأخذ افتتاح أول شمعة في السلسلة وفق `U0045` و`U0047`، والمتغير `V02` يأخذ آخر شمعة معاكسة فقط وفق `U0046`. تبقى الكتلة مرشحة لأن نص الاعتماد الكامل `U0051` غير محسوم.",
        "",
        "الإطار التنفيذي هو الخمس دقائق لأنه إطار المدخل والمناطق، والدخول عند إغلاق أول عودة فقط وفق `K2C-004`؛ لا تستخدم عودة لاحقة ولا موجة مختارة بالعين. موضع الخصم أو العلاوة ونافذة الوقت شرطان سابقان من `K2C-002` و`K2C-003` و`K2C-016` و`K2C-038` و`K2C-028`. الوقف هو الجانب البعيد للمنطقة نفسها وفق `U0048`.",
        "",
        "لا يختار المحرك فجوة معينة للدخول أو الهدف. الفجوات تسرد التكوين واللمس والإغلاق فقط، ومجموعة الهدف تتكون من مستويات السيولة النشطة. أهداف المرجع ومعظم المتغيرات تقدم اليومي المكتمل ثم المسافة، بينما `V03` يستخدم المسافة وحدها. لذلك لا يوجد سبب خفي لتفضيل فجوة على أخرى؛ المقارنة الصحيحة هنا بين مستويات السيولة وقواعد ترتيبها.",
        "",
        "أما 48 شمعة للضجيج و288 و1152 للمسار وشبكة 1 و2 و4 و8 للحواجز فهي شبكات قياس مثبتة في العقد، وليست أقوالاً منسوبة للمصدر أو إعدادات مستخرجة من الإصابات.",
        "",
        "## النتائج السنوية جنباً إلى جنب",
        "",
    ]
    rows = []
    for variant in VARIANTS:
        cases = data[variant]["cases"]
        stopped = [case for case in cases if case["original"]["outcome"] == "STOP_FIRST"]
        count = len(stopped)
        rows.append(
            [
                f"`{variant}`",
                len(cases),
                sum(case["original"]["outcome"] == "TARGET_FIRST" for case in cases),
                count,
                sum(case["original"]["outcome"] == "HORIZON_EXPIRED" for case in cases),
                sum(case["post_stop"]["target_after_stop_within_original"] for case in stopped),
                sum(case["post_stop"]["target_after_stop_within_extended"] for case in stopped),
                count_pct(sum(case["primary_class"] == "DIRECTION-RIGHT-STOP-TOO-TIGHT" for case in stopped), count),
                count_pct(sum(case["primary_class"] == "DIRECTION-WRONG" for case in stopped), count),
                count_pct(sum(case["primary_class"] == "UNRESOLVED" for case in stopped), count),
                count_pct(sum(case["post_stop"]["slow"] for case in stopped), count),
            ]
        )
    lines += table(
        ["المتغير", "الكل", "هدف أولاً", "وقف أولاً", "أفق منتهٍ", "هدف بعد الوقف داخل 288", "داخل 1152", "اتجاه صحيح ووقف قريب", "اتجاه خاطئ", "غير محسوم بعد الوقف", "بطيء"],
        rows,
    )
    lines += [
        "«اتجاه صحيح ووقف قريب» يعني بلوغ الهدف بعد الوقف ضمن شبكة القياس، ولا يعني أن الصفقة بقيت قائمة أو أن النتيجة ربح. «اتجاه خاطئ» يتطلب اكتمال الأفق الممتد بلا هدف ثم تجاوز السعر للوقف مجدداً بعد شمعة الوقف. البتر لا يحسب عدم بلوغ.",
        "هذه الأسماء تشغيلية مرتبطة بالهدف الأصلي، وليست قياساً مستقلاً لجودة قراءة الاتجاه. بُعد الهدف قد يمنع بلوغه حتى لو تحرك السعر في الاتجاه. لذلك لا تفسر نسبة «اتجاه خاطئ» بأنها نسبة خطأ المحرك في السوق؛ الاختبار المستقل هو الحاجزان المتقابلان في تقرير النسخة الثانية، ونتائجه تختلف بحسب الاتجاه والشبكة والمتغير ولا تعطي حكماً موحداً.",
        "",
        "## التقدم قبل الوقف والزمن",
        "",
    ]
    rows = []
    for variant in VARIANTS:
        cases = data[variant]["cases"]
        stopped = [case for case in cases if case["original"]["outcome"] == "STOP_FIRST"]
        reached = [case for case in stopped if case["post_stop"]["target_after_stop_within_extended"]]
        any_target = [case for case in cases if case["before_target"] is not None]
        rows.append(
            [
                f"`{variant}`",
                fnum(distribution([case["before_stop"]["best_fraction_of_target"] for case in stopped])["median"]),
                fnum(distribution([case["before_stop"]["best_multiple_of_stop"] for case in stopped])["median"]),
                fnum(distribution([case["original"]["bars_from_entry"] for case in stopped])["median"], 1),
                fnum(distribution([case["post_stop"]["stop_to_target_bars"] for case in reached])["median"], 1),
                fnum(distribution([case["post_stop"]["stop_to_target_over_entry_to_stop"] for case in reached])["median"]),
                fnum(distribution([case["before_target"]["worst_multiple_of_stop"] for case in any_target])["median"]),
            ]
        )
    lines += table(
        ["المتغير", "وسيط أفضل تقدم ÷ الهدف", "÷ الوقف", "وسيط الدخول إلى الوقف بالشموع", "وسيط الوقف إلى الهدف", "وسيط نسبة الزمنين", "وسيط أسوأ حركة قبل الهدف ÷ الوقف"],
        rows,
    )
    lines += ["## الوقف قياساً إلى الضجيج والسبريد", ""]
    lines += [
        "الضجيج هو وسيط مدى 48 شمعة سوق سابقة لشمعة الدخول ومستبعدة لها. «أصغر من الشمعة» مقارنة صارمة بين مسافة الوقف وذلك الوسيط، وليست حكماً بأن الوقف يجب توسيعه.",
        "",
    ]
    rows = []
    for variant in VARIANTS:
        cases = data[variant]["cases"]
        valid = [case for case in cases if case["noise"]["stop_to_median_range"] is not None]
        rows.append(
            [
                f"`{variant}`",
                pips(distribution([case["stop_distance"] for case in cases])["median"]),
                pips(distribution([case["noise"]["median_bar_range"] for case in valid])["median"]),
                fnum(distribution([case["noise"]["stop_to_median_range"] for case in valid])["median"]),
                count_pct(sum(case["noise"]["stop_smaller_than_typical_bar"] is True for case in valid), len(valid)),
                pips(distribution([case["noise"]["entry_spread"] for case in cases])["median"]),
                fnum(distribution([case["noise"]["stop_to_spread"] for case in cases if case["noise"]["stop_to_spread"] is not None])["median"]),
            ]
        )
    lines += table(
        ["المتغير", "وسيط الوقف بالنقاط", "وسيط مدى الشمعة", "وسيط الوقف ÷ المدى", "وقف أصغر من الشمعة", "وسيط السبريد", "وسيط الوقف ÷ السبريد"],
        rows,
    )
    lines += ["## اختبار المنطقة ونسبة المسافتين كناتج", ""]
    rows = []
    for variant in VARIANTS:
        cases = data[variant]["cases"]
        count = len(cases)
        summary = data[variant]["summary"]["post_stop"]
        rows.append(
            [
                f"`{variant}`",
                count_pct(summary["zones"]["REACTION_THEN_SLICE"], count),
                count_pct(summary["zones"]["DIRECT_SLICE"], count),
                count_pct(summary["zones"]["REACTION_NO_STOP"], count),
                count_pct(summary["zones"]["NO_REACTION_NO_STOP"], count),
                count_pct(summary["zones"]["ZONE_UNRESOLVED"], count),
                fnum(summary["reward_risk_output"]["median"], 2),
                fnum(summary["reward_risk_output"]["maximum"], 2),
            ]
        )
    lines += table(
        ["المتغير", "رد فعل ثم مرور", "مرور مباشر", "رد فعل بلا وقف", "لا رد فعل ولا وقف", "غير محسوم", "وسيط النسبة المرصودة", "أقصاها"],
        rows,
    )
    lines += [
        "رد الفعل يقاس بإغلاق لاحق خارج افتتاح المنطقة في جهة الهدف أو ببلوغ الهدف أولاً؛ المرور هو اختراق جانبها البعيد. التعريف يستخدم عرض المنطقة نفسه، لا عدداً ثابتاً بالنقاط. وصول السعر إلى وقف بعد رد فعل لا يمحو رد الفعل السابق، لذلك الفئتان مسجلتان معاً.",
        "",
        "## سجلات الحالات والشموع",
        "",
        "يتضمن `POST_STOP_CASE_INDEX.md` كل حالة ووقت الحل والبلوغ اللاحق والضوضاء والفئة. سجل الشموع المضغوط يحتوي شمعة الدخول وكل شمعة لاحقة حتى الحل، ثم حتى الهدف اللاحق أو الأفق الممتد للموقوفين، مع العرض والطلب والقيم التراكمية. المسارات والبصمات في `ANALYSIS_MANIFEST.md`.",
        "",
        "لا يوجد اختيار وقف أو هدف أو متغير فائز في هذا التقرير. النتائج وصف للعقد المثبت، والأقل من 30 في الجداول الشهرية وصف فقط.",
        "",
    ]
    return "\n".join(lines)


def post_stop_monthly_report(data: dict[str, Any]) -> str:
    lines = header(
        "التقرير الشهري والاتجاهي لما بعد الوقف — 2022",
        [
            "كل صف يفصل المتغير والشهر والاتجاه. مقام نسب الفئات هو الموقوفون في الصف؛ نسبة الوقف الأصغر من الشمعة مقامها الحالات ذات 48 شمعة ضجيج صالحة. الصفر مقام صالح، و«غير متاح» غياب مقام. الأقل من 30 وصف فقط.",
        ],
    )
    for month_number in range(1, 13):
        month = f"2022-{month_number:02d}"
        lines += [f"## {month}", ""]
        rows = []
        for variant in VARIANTS:
            for direction, arabic in DIRECTIONS:
                cases = [case for case in data[variant]["cases"] if case["month"] == month and case["direction"] == direction]
                stopped = [case for case in cases if case["original"]["outcome"] == "STOP_FIRST"]
                count = len(stopped)
                valid_noise = [case for case in cases if case["noise"]["stop_smaller_than_typical_bar"] is not None]
                rows.append(
                    [
                        f"`{variant}`",
                        arabic,
                        len(cases),
                        sum(case["original"]["outcome"] == "TARGET_FIRST" for case in cases),
                        count,
                        sum(case["original"]["outcome"] == "HORIZON_EXPIRED" for case in cases),
                        count_pct(sum(case["primary_class"] == "DIRECTION-RIGHT-STOP-TOO-TIGHT" for case in stopped), count),
                        count_pct(sum(case["primary_class"] == "DIRECTION-WRONG" for case in stopped), count),
                        count_pct(sum(case["primary_class"] == "UNRESOLVED" for case in stopped), count),
                        count_pct(sum(case["post_stop"]["slow"] for case in stopped), count),
                        count_pct(sum(case["noise"]["stop_smaller_than_typical_bar"] is True for case in valid_noise), len(valid_noise)),
                        "وصف فقط" if len(cases) < 30 else "ثلاثون أو أكثر",
                    ]
                )
        lines += table(
            ["المتغير", "الاتجاه", "الكل", "هدف", "وقف", "أفق", "صحيح ووقف قريب", "اتجاه خاطئ", "غير محسوم", "بطيء", "وقف أصغر من الشمعة", "حد الوصف"],
            rows,
        )
    return "\n".join(lines)


def case_index(data: dict[str, Any]) -> str:
    lines = header(
        "فهرس جميع حالات ما بعد الوقف",
        [
            "كل صف يحمل معرف الحالة المستخدم في سجل الشموع المضغوط. «آخر رصد» هو وقت الهدف اللاحق عند بلوغه، أو آخر شمعة في الأفق المكتمل، أو آخر بيانات عند البتر. عدم البلوغ مقيد بذلك الوقت ولا يعني عدم البلوغ أبداً.",
            "المسافات بالنقاط، والزمن بالشموع. النسبة المعروضة ناتج مسافة الهدف ÷ مسافة الوقف، وليست مدخلاً جديداً.",
        ],
    )
    for variant in VARIANTS:
        lines += [f"## `{variant}`", ""]
        rows = []
        for case in data[variant]["cases"]:
            post = case["post_stop"]
            original = case["original"]
            reached = post["target_after_stop_within_extended"]
            rows.append(
                [
                    f"`{case['case_id']}`",
                    case["available_at"],
                    "شراء" if case["direction"] == "bullish" else "بيع",
                    OUTCOME_ARABIC[original["outcome"]],
                    original["bars_from_entry"],
                    original["resolved_at"] or "غير متاح",
                    post["stop_to_target_bars"] if reached else "لم يبلغ",
                    ("288" if post["target_after_stop_within_original"] else "1152") if reached else "لا",
                    post["target_after_stop_at"] or post["observed_until"] or "غير متاح",
                    CLASS_ARABIC[case["primary_class"]],
                    "نعم" if post["slow"] else "لا",
                    fnum(case["before_stop"]["best_fraction_of_target"]),
                    fnum(case["before_target"]["worst_multiple_of_stop"]) if case["before_target"] is not None else "غير متاح",
                    fnum(case["noise"]["stop_to_median_range"]),
                    fnum(case["noise"]["stop_to_spread"]),
                    fnum(case["zone"]["entry_penetration_fraction"]),
                    f"`{case['zone']['class']}`",
                    fnum(case["observed_reward_risk"], 2),
                ]
            )
        lines += table(
            ["المعرف", "الدخول", "الاتجاه", "الأصلي", "شموع", "وقت الحل", "وقف إلى هدف", "أفق البلوغ", "الهدف اللاحق أو آخر رصد", "الفئة", "بطيء", "أفضل تقدم ÷ الهدف", "أسوأ قبل الهدف ÷ الوقف", "وقف ÷ ضجيج", "وقف ÷ سبريد", "عمق المنطقة", "المنطقة", "النسبة"],
            rows,
        )
    return "\n".join(lines)


def target_review_update(data: dict[str, Any], original: str) -> str:
    lines = [original.rstrip(), "", "---", "", "# نتائج مراجعة المسافات بعد التنفيذ", ""]
    lines += [
        "طابق الاختيار المعاد بناؤه الهدف المسجل في كل حالة. لذلك لا توجد حالة «هدف مختلف بسبب إعادة البناء». لكن التدقيق كشف أثرين مختلفين يجب ألا يدمجا: تقديم اليومي على الخمس دقائق، وتقديم وقت التكوين داخل الإطار نفسه.",
        "",
        "## الأعداد والمسافات",
        "",
    ]
    rows = []
    for variant in VARIANTS:
        cases = data[variant]["cases"]
        consequences = Counter(case["target_audit"]["rule_consequence"] for case in cases)
        rows.append(
            [
                f"`{variant}`",
                len(cases),
                consequences["DAILY_PRIORITY_RULE_CONSEQUENCE"],
                consequences["SAME_TIMEFRAME_AGE_PRIORITY_BUG_CANDIDATE"],
                consequences["DISTANCE_TIE_RULE_CONSEQUENCE"],
                consequences["SELECTED_IS_NEAREST"],
                pips(distribution([case["target_audit"]["target_distance"] for case in cases])["median"]),
                pips(distribution([case["target_audit"]["nearest_pool_distance"] for case in cases])["median"]),
                pips(distribution([case["target_audit"]["selected_minus_nearest_distance"] for case in cases])["median"]),
                pips(max(case["target_audit"]["selected_minus_nearest_distance"] for case in cases)),
            ]
        )
    lines += table(
        ["المتغير", "الكل", "أولوية يومي", "اشتباه داخل الإطار", "تعادل", "الأقرب", "وسيط الهدف", "وسيط الأقرب", "وسيط الزيادة", "أقصى زيادة"],
        rows,
    )
    lines += [
        "كل المسافات بالنقاط. «أولوية يومي» تعني أن الهدف يومي والأقرب من الخمس دقائق؛ هذا أثر مباشر للقاعدة الموثقة. «اشتباه داخل الإطار» يعني أن الهدف والأقرب من الإطار نفسه والمسافتان مختلفتان، ومع ذلك قدمت رتبة الأهمية الأقدم.",
        "",
        "## الحالات التي تشتبه بتقديم الأقدم داخل الإطار نفسه",
        "",
    ]
    rows = []
    for variant in VARIANTS:
        for case in data[variant]["cases"]:
            audit = case["target_audit"]
            if audit["rule_consequence"] == "SAME_TIMEFRAME_AGE_PRIORITY_BUG_CANDIDATE":
                rows.append(
                    [
                        f"`{variant}`",
                        f"`{case['case_id']}`",
                        f"`{audit['target_timeframe']}`",
                        pips(audit["target_distance"]),
                        pips(audit["nearest_pool_distance"]),
                        audit["distance_rank"],
                        f"`{audit['target_id']}`",
                        f"`{audit['nearest_pool_id']}`",
                    ]
                )
    lines += table(
        ["المتغير", "الحالة", "الإطار", "الهدف", "الأقرب", "رتبة الهدف", "معرف الهدف", "معرف الأقرب"],
        rows,
    )
    lines += [
        "تظهر ست صفوف لأن العد بالمتغيرات، لكن مناسبة 24 كانون الثاني تتكرر في المرجع و`V01` و`V04`؛ لذلك لا تعامل الصفوف الستة كست ملاحظات سوق مستقلة.",
        "الدليل الكودي هو `liquidity.py:275–290`: حتى مع مجموعة واحدة الإطار، ترتب الأهمية بوقت التكوين وتعطي أرقاماً مختلفة. ثم `narrator.py:295–305` يضع رقم الأهمية قبل رتبة المسافة. هذه ليست أولوية يومي على أدنى في الحالات المذكورة، لأن الهدف والأقرب من الإطار نفسه. لذلك توصف بأنها **اشتباه خلل تنفيذي في مطابقة القاعدة المكتوبة**، لا مجرد هدف بعيد مقصود. لم يصلح المحرك ولم تتغير النتائج.",
        "",
        "أما الحالات اليومية البعيدة فهي نتيجة قاعدة معلنة، ولا تسمى خللاً لمجرد البعد. وحالة تعادل المسافة فرقها الصفري صفر؛ اختلاف المعرف فيها لا يجعل الهدف أبعد.",
        "",
        "## قائمة الحالات والخيارات",
        "",
        "تتضمن `TARGET_SELECTION_CASES.md` كل هدف ونوعه وإطاره وقاعدته ومسافته وأقرب مستوى غير مأخوذ ومعرفيهما. لم تدخل فجوة في أهداف هذه الحالات، ولا يوجد اختيار «هذه الفجوة بدلاً من غيرها» لاستخراجه.",
        "",
        "تبقى الخيارات الأربعة السابقة مفتوحة: الإبقاء على أولوية اليومي، أو عرض المسافة وحدها، أو عقد مصدر جديد لنوع آخر من المرشحات، أو إصلاح مستقل لاحق لعدم المطابقة المثبت. لا يختار هذا التقرير أي واحد منها بالنتائج، ولا يغير نسبة الهدف إلى الوقف.",
        "",
    ]
    return "\n".join(lines)


def target_cases(data: dict[str, Any]) -> str:
    lines = header(
        "سجل الهدف وأقرب مستوى غير مأخوذ لكل حالة",
        [
            "المسافات بالنقاط من إغلاق الدخول بأساس المتغير. المجموعة هي مستويات السيولة النشطة غير المأخوذة في جانب الاتجاه عند الإغلاق نفسه. رتبة الهدف هي رتبته بالمسافة داخل المجموعة، وليست رتبة الأهمية.",
        ],
    )
    for variant in VARIANTS:
        lines += [f"## `{variant}`", ""]
        rows = []
        for case in data[variant]["cases"]:
            audit = case["target_audit"]
            rows.append(
                [
                    f"`{case['case_id']}`",
                    case["available_at"],
                    "شراء" if case["direction"] == "bullish" else "بيع",
                    f"`{audit['target_id']}`",
                    f"`{audit['target_kind']}`",
                    f"`{audit['target_timeframe']}`",
                    "المسافة فقط" if variant == "V03" else "اليومي ثم المسافة",
                    pips(audit["target_distance"]),
                    audit["distance_rank"],
                    f"`{audit['nearest_pool_id']}`",
                    pips(audit["nearest_pool_distance"]),
                    pips(audit["selected_minus_nearest_distance"]),
                    TARGET_CLASS_ARABIC[audit["rule_consequence"]],
                    ", ".join(f"`{claim}`" for claim in audit["target_claim_ids"]),
                ]
            )
        lines += table(
            ["الحالة", "الوقت", "الاتجاه", "الهدف", "النوع", "الإطار", "القاعدة", "المسافة", "الرتبة", "الأقرب", "مسافته", "الزيادة", "التفسير", "الادعاءات"],
            rows,
        )
    return "\n".join(lines)


def direction_annual(data: dict[str, Any]) -> list[str]:
    lines = ["## الاختبار الرئيسي: الحاجزان المتقابلان", ""]
    lines += [
        "في كل خلية أعداد خمسة بالترتيب: الاتجاه أولاً / الضد أولاً / تعارض / بلا لمس / بتر. المسافة 1 أو 2 أو 4 أو 8 أضعاف مسافة الوقف، والحاجزان متساويان من الدخول. المعدل على المحسوم فقط. الفرق هو اتجاه المحرك أولاً ناقص الوقت العشوائي أولاً على الأزواج المحسومة معاً.",
        "",
    ]
    for direction, arabic in DIRECTIONS:
        lines += [f"### {arabic}", ""]
        rows = []
        for variant in VARIANTS:
            for multiple in DIRECTION_GRID:
                selected = [row for row in data[variant]["direction"] if row["direction"] == direction and row["multiple"] == multiple]
                engine = direction_counts(selected, "engine")
                random = direction_counts(selected, "random_same_month_same_direction")
                opposite = direction_counts(selected, "opposite_direction_same_time")
                paired_count, difference = paired(selected)
                rows.append(
                    [
                        f"`{variant}`",
                        multiple,
                        cell_count(engine),
                        rate(direction_rate(engine)),
                        cell_count(random),
                        rate(direction_rate(random)),
                        cell_count(opposite),
                        paired_count,
                        rate(difference),
                        "وصف فقط" if len(selected) < 30 else "ثلاثون أو أكثر",
                    ]
                )
        lines += table(
            ["المتغير", "المضاعف", "المحرك", "معدله", "عشوائي الشهر", "معدله", "الاتجاه المعاكس بالزمن نفسه", "المتطابق", "الفرق", "حد الوصف"],
            rows,
        )
    lines += [
        "الأساس المعاكس في الزمن نفسه مرآة: يتبادل مع المحرك عددي الاتجاه أولاً والضد أولاً، ويشترك في التعارض وعدم اللمس والبتر. لذلك لا يقدم تأكيداً مستقلاً. الأساس العشوائي داخل الشهر بالاتجاه نفسه هو المقارنة غير المتطابقة للحدث، مع بذرة مثبتة واحتمال تكرار الأوقات بين الحالات.",
        "",
    ]
    return lines


def liquidity_v2(data: dict[str, Any]) -> list[str]:
    lines = ["## أول مستوى من الجانب نفسه", ""]
    lines += [
        "تعرض المعدلات على المجموعات المستقلة المحسومة. التعادل في أول شمعة بلوغ غير محسوم، وعدم بلوغ أي مستوى خلال أفق مكتمل إخفاق لكل الاختيارات وفق العقد. لا يوجد خط أغلبية ولا صفقة عكسية.",
        "هذا الاختبار الثانوي ذو ترتيب هندسي شبه حرفي: المستوى الأقرب في الجانب نفسه يعترض مسار السعر قبل الأبعد بالضرورة تقريباً، وإذا اشتركا في شمعة أول بلوغ فالحالة غير محسومة. لذلك لا تدل إصابات الأقرب على مهارة تنبؤية، ولا يكون صفر الأبعد اكتشافاً مستقلاً. قيمة الجدول هي كشف هذا التعريف وحجم التعارض وتتبع اختيار المحرك والعشوائي، أما سؤال الاتجاه غير المطابق للحدث فمحله الحاجزان المتقابلان.",
        "",
    ]
    rows = []
    for variant in VARIANTS:
        summary = liquidity_summary(data[variant]["liquidity"])
        for arm, arabic in [("engine", "المحرك"), ("nearest", "الأقرب"), ("farthest", "الأبعد"), ("random", "العشوائي")]:
            values = summary["arms"][arm]
            rows.append(
                [
                    f"`{variant}`",
                    arabic,
                    summary["raw_rows"],
                    summary["selected_rows"],
                    summary["statuses"]["FIRST_POOL"],
                    summary["statuses"]["FIRST_TOUCH_TIE"],
                    summary["statuses"]["NO_POOL_REACHED"],
                    summary["statuses"]["TRUNCATED"],
                    values["hits"],
                    values["misses"],
                    rate(values["rate"]),
                    "وصف فقط" if summary["descriptive_only"] else "ثلاثون أو أكثر",
                ]
            )
    lines += table(
        ["المتغير", "الاختيار", "الخام", "المستقل", "بلوغ", "تعادل", "لا بلوغ", "بتر", "إصابة", "إخفاق", "المعدل", "حد الوصف"],
        rows,
    )
    lines += ["### الفروق بعد استبعاد تطابق الكائن", ""]
    rows = []
    for variant in VARIANTS:
        summary = liquidity_summary(data[variant]["liquidity"])
        for arm, arabic in [("nearest", "الأقرب"), ("farthest", "الأبعد"), ("random", "العشوائي")]:
            values = summary["arms"][arm]
            rows.append(
                [
                    f"`{variant}`",
                    arabic,
                    values["overlap_with_engine"],
                    values["discriminative_paired_count"],
                    values["paired_engine_hits"],
                    values["paired_arm_hits"],
                    rate(values["paired_difference"]),
                ]
            )
    lines += table(["المتغير", "البديل", "تطابق مع المحرك", "مقام تمييزي", "إصابة المحرك", "إصابة البديل", "الفرق للبديل"], rows)
    return lines


def pairs_v2(data: dict[str, Any]) -> list[str]:
    lines = ["## منطقتا الدخول", ""]
    rows = []
    for variant in VARIANTS:
        summary = entry_pair_summary(data[variant]["pairs"])
        exclusions = data[variant]["summary"]["v2_entry_pair_exclusions"]
        rows.append(
            [
                f"`{variant}`",
                summary["raw_rows"],
                summary["selected_rows"],
                summary["comparisons"]["UNRANKED"],
                summary["comparisons"]["UNJUDGEABLE"],
                exclusions.get("UNSUPPORTED_SET_SIZE", 0),
                summary["ranked_judgeable_pairs"],
                rate(summary["difference"]),
            ]
        )
    lines += table(["المتغير", "الخام", "المستقل", "غير مرتب", "غير محسوم", "حجم غير مدعوم", "أزواج محسومة", "الفرق"], rows)
    lines += [
        "لم تُنشأ أزواج من مناطق اختبرت في أوقات مختلفة، ولم يخترع ترتيب لزوج لا يجمع الدخول والهدف والزمن. إذا كان العدد صفراً فهو غياب دليل، لا إثبات تساوي المناطق أو فشلها.",
        "",
    ]
    return lines


def aside_v2(data: dict[str, Any]) -> list[str]:
    lines = ["## الحركة والمخاطرة بعد الامتناع", ""]
    lines += [
        "القيم بالنقاط، والأفق 48 شمعة. المدى المواتي حركة محتملة فائتة وليس ربحاً، والمدى المعاكس مخاطرة لاحقة. لا معدل إصابة للامتناع ولا نتيجة سوق ثنائية له.",
        "",
    ]
    rows = []
    for variant in VARIANTS:
        for direction, arabic in DIRECTIONS:
            selected = [row for row in data[variant]["aside"] if row["direction"] == direction]
            summary = stand_aside_summary(selected)
            aside = summary["categories"]["ASIDE"]
            other = summary["categories"]["NOT_ASIDE"]
            rows.append(
                [
                    f"`{variant}`",
                    arabic,
                    aside["count"],
                    other["count"],
                    summary["truncated"],
                    pips(aside["mfe"]["median"]),
                    pips(other["mfe"]["median"]),
                    pips(summary["mfe_median_difference"]),
                    pips(aside["mae"]["median"]),
                    pips(other["mae"]["median"]),
                    pips(summary["mae_median_difference"]),
                    pips(summary["terminal_median_difference"]),
                    "وصف فقط" if summary["descriptive_only"] else "ثلاثون أو أكثر",
                ]
            )
    lines += table(
        ["المتغير", "الاتجاه", "امتناع", "عدم امتناع", "بتر", "مواتي امتناع", "مواتي غيره", "الفرق", "معاكس امتناع", "معاكس غيره", "الفرق", "فرق النهائي", "حد الوصف"],
        rows,
    )
    return lines


def v2_report(combined: dict[str, Any], data: dict[str, Any]) -> str:
    lines = header(
        "تقرير النسخة الثانية — 2022 فقط",
        [
            "الاختبار الرئيسي هو الحاجزان المتقابلان لأنه يفصل قراءة الاتجاه عن موضعي الهدف والوقف. الأنواع الأخرى مكمولة وتبقى جنباً إلى جنب، ولا يجمع بينها فائز موحد.",
            f"العقد والملحق ثبتا في `{combined['spec_commit']}`، والتنفيذ `{combined['implementation_commit']}`. البذور والآفاق والشبكة لم تتغير بعد النتائج. لم تستخدم بيانات لاحقة، ولم تتغير نسبة أو قاعدة محرك.",
        ],
    )
    lines += direction_annual(data)
    lines += liquidity_v2(data)
    lines += pairs_v2(data)
    lines += aside_v2(data)
    lines += [
        "## الحكم وإعادة التشغيل",
        "",
        "كل المقارنات تطويرية على 2022، والأقل من 30 وصف فقط. أعيد التشغيل بالشيفرة والمدخل نفسيهما وطلب تطابق السجلات بايتياً. البصمات والمسارات في `ANALYSIS_MANIFEST.md`، والتفاصيل الشهرية في `V2_MONTHLY_REPORT.md`. لا اختيار متغير ولا استنتاج ربحي أو سببي.",
        "",
    ]
    return "\n".join(lines)


def v2_monthly_report(data: dict[str, Any]) -> str:
    lines = header(
        "التقرير الشهري للنسخة الثانية — 2022",
        [
            "في خلايا الحواجز خمسة أعداد بالترتيب: الاتجاه أولاً / الضد أولاً / تعارض / بلا لمس / بتر. يفصل كل صف المتغير والشهر والاتجاه والمضاعف. الأقل من 30 وصف فقط، ولا تجمع الشبكات لرفع المقام.",
        ],
    )
    for month_number in range(1, 13):
        month = f"2022-{month_number:02d}"
        lines += [f"## {month} — الحاجزان", ""]
        rows = []
        for variant in VARIANTS:
            for direction, arabic in DIRECTIONS:
                for multiple in DIRECTION_GRID:
                    selected = [row for row in data[variant]["direction"] if row["month"] == month and row["direction"] == direction and row["multiple"] == multiple]
                    engine = direction_counts(selected, "engine")
                    random = direction_counts(selected, "random_same_month_same_direction")
                    opposite = direction_counts(selected, "opposite_direction_same_time")
                    paired_count, difference = paired(selected)
                    rows.append(
                        [
                            f"`{variant}`",
                            arabic,
                            multiple,
                            cell_count(engine),
                            cell_count(random),
                            cell_count(opposite),
                            paired_count,
                            rate(difference),
                            "وصف فقط" if len(selected) < 30 else "ثلاثون أو أكثر",
                        ]
                    )
        lines += table(["المتغير", "الاتجاه", "المضاعف", "المحرك", "العشوائي", "المعاكس", "المتطابق", "الفرق", "حد الوصف"], rows)
        lines += [f"## {month} — أول مستوى", ""]
        rows = []
        for variant in VARIANTS:
            selected = [row for row in data[variant]["liquidity"] if row["month"] == month]
            summary = liquidity_summary(selected)
            rows.append(
                [
                    f"`{variant}`",
                    summary["raw_rows"],
                    summary["selected_rows"],
                    summary["statuses"]["FIRST_TOUCH_TIE"],
                    summary["statuses"]["NO_POOL_REACHED"],
                    summary["statuses"]["TRUNCATED"],
                    f"{summary['arms']['engine']['hits']} / {rate(summary['arms']['engine']['rate'])}",
                    f"{summary['arms']['nearest']['hits']} / {rate(summary['arms']['nearest']['rate'])}",
                    f"{summary['arms']['farthest']['hits']} / {rate(summary['arms']['farthest']['rate'])}",
                    f"{summary['arms']['random']['hits']} / {rate(summary['arms']['random']['rate'])}",
                    "وصف فقط" if summary["descriptive_only"] else "ثلاثون أو أكثر",
                ]
            )
        lines += table(["المتغير", "الخام", "المستقل", "تعادل", "لا بلوغ", "بتر", "المحرك إصابة/معدل", "الأقرب", "الأبعد", "العشوائي", "حد الوصف"], rows)
        lines += [f"## {month} — الامتناع", ""]
        rows = []
        for variant in VARIANTS:
            for direction, arabic in DIRECTIONS:
                selected = [row for row in data[variant]["aside"] if row["month"] == month and row["direction"] == direction]
                summary = stand_aside_summary(selected)
                rows.append(
                    [
                        f"`{variant}`",
                        arabic,
                        summary["categories"]["ASIDE"]["count"],
                        summary["categories"]["NOT_ASIDE"]["count"],
                        summary["truncated"],
                        pips(summary["mfe_median_difference"]),
                        pips(summary["mae_median_difference"]),
                        pips(summary["terminal_median_difference"]),
                        "وصف فقط" if summary["descriptive_only"] else "ثلاثون أو أكثر",
                    ]
                )
        lines += table(["المتغير", "الاتجاه", "امتناع", "عدم امتناع", "بتر", "فرق المواتي", "فرق المعاكس", "فرق النهائي", "حد الوصف"], rows)
    lines += [
        "لم تظهر أزواج دخول مؤهلة في السجلات السنوية؛ لذلك لا تعاد جداول شهرية صفرية لها، ولا يحول غيابها إلى نتيجة لصالح أي منطقة.",
        "",
    ]
    return "\n".join(lines)


def manifest_report(combined: dict[str, Any], data: dict[str, Any], replay: dict[str, Any]) -> str:
    lines = header(
        "بيان بصمات التحليل وإعادة التشغيل",
        [
            f"العقد والملحق ومراجعة ما قبل النتائج: `{combined['spec_commit']}`. شيفرة التحليل: `{combined['implementation_commit']}`. المدخل الوحيد 2022 وبصمته `{combined['data']['sha256']}`.",
            f"أعيد التشغيل على المسارات نفسها. عدد الملفات المتطابقة بايتياً {replay['matched_files']}، والاختلافات {replay['different_files']}. البصمة المجمعة بعد الإعادة `{replay['combined_sha256']}`.",
        ],
    )
    rows = []
    for variant in VARIANTS:
        summary = data[variant]["summary"]
        legacy = summary["legacy"]
        rows.append(
            [
                f"`{variant}`",
                legacy["predictions"]["rows"],
                f"`{legacy['predictions']['sha256']}`",
                f"`{legacy['outcomes']['sha256']}`",
                summary["candle_rows"],
            ]
        )
    lines += ["## السجلات القديمة المتحقق منها", ""]
    lines += table(["المتغير", "الصفوف", "بصمة التنبؤات", "بصمة النتائج", "شموع التشخيص"], rows)
    for variant in VARIANTS:
        summary = data[variant]["summary"]
        lines += [f"## ملفات `{variant}`", ""]
        rows = []
        for name, artifact in sorted(summary["artifacts"].items()):
            rows.append([f"`{name}`", f"`{artifact['path']}`", artifact["bytes"], f"`{artifact['sha256']}`"])
        lines += table(["الملف", "المسار", "البايتات", "البصمة"], rows)
    lines += [
        "السجلات الكبيرة خارج المستودع. سجل الشموع مضغوط بزمن ثابت حتى تكون إعادة الكتابة قابلة للمقارنة. لم تعدل مخرجات يدوياً، ولم يتغير الملف المحمي أو أي ملف من وحدة المحرك.",
        "",
    ]
    return "\n".join(lines)


def generate_reports(root: Path, output_dir: Path, replay: dict[str, Any]) -> dict[str, Any]:
    combined, data = load_results(root)
    review_path = output_dir / "TARGET_SELECTION_REVIEW.md"
    original = review_path.read_text(encoding="utf-8").split("\n---\n\n# نتائج مراجعة المسافات بعد التنفيذ", 1)[0]
    reports = {
        "POST_STOP_ANALYSIS_REPORT.md": post_stop_report(combined, data),
        "POST_STOP_MONTHLY_REPORT.md": post_stop_monthly_report(data),
        "POST_STOP_CASE_INDEX.md": case_index(data),
        "TARGET_SELECTION_REVIEW.md": target_review_update(data, original),
        "TARGET_SELECTION_CASES.md": target_cases(data),
        "V2_DEV_REPORT.md": v2_report(combined, data),
        "V2_MONTHLY_REPORT.md": v2_monthly_report(data),
        "ANALYSIS_MANIFEST.md": manifest_report(combined, data, replay),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    written = {}
    for name, text in reports.items():
        path = output_dir / name
        path.write_text(text.rstrip() + "\n", encoding="utf-8")
        written[name] = {"bytes": path.stat().st_size}
    write_json(root / "report_outputs.json", written)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="توليد التقارير العربية من سجلات 2022")
    parser.add_argument("--root", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--replay", required=True)
    arguments = parser.parse_args()
    replay = json.loads(Path(arguments.replay).read_text(encoding="utf-8"))
    written = generate_reports(Path(arguments.root), Path(arguments.output_dir), replay)
    print(json.dumps(written, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
