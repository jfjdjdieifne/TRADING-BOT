"""Arabic M3 reports and pre-registered narration extraction."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .score_ledger import read_jsonl, sha256_file
from .variants import VARIANT_BY_ID

UTC = timezone.utc
EXAMPLE_MONTHS = (1, 4, 7, 10, 12)
EXAMPLE_TYPE_ORDER = (
    "setup_target_before_stop",
    "ob_first_retracement",
    "draw_touch",
)
CONCEPT_TEXT = {
    "liquidity_pool_candidate": "بلوغ مستوى السيولة المرشح",
    "order_block_candidate": "أول العودة إلى كتلة الأوامر المرشحة",
    "candidate_first_retracement_continuation": "الهدف قبل الوقف بعد أول عودة",
}
PREDICTION_TYPE_TEXT = {
    "draw_touch": "بلوغ السيولة",
    "ob_first_retracement": "أول العودة",
    "setup_target_before_stop": "الهدف قبل الوقف",
}
DECISION_TEXT = {
    "target_choice": "اختيار الهدف",
    "entry_choice": "اختيار الدخول",
    "stop_choice": "اختيار الوقف",
    "stand_aside": "الامتناع",
    "management": "الإدارة",
}
MONTH_TEXT = {
    1: "يناير",
    2: "فبراير",
    3: "مارس",
    4: "أبريل",
    5: "مايو",
    6: "يونيو",
    7: "يوليو",
    8: "أغسطس",
    9: "سبتمبر",
    10: "أكتوبر",
    11: "نوفمبر",
    12: "ديسمبر",
}
METRIC_HEADER = (
    "| المتغير | الاسم | الخام | المستقل | إصابة | إخفاق | لا حكم | تعارض | بتر | "
    "الإصابة الكاملة | الإصابة المتطابقة | الأساس | الفرق | المتطابق | الحكم |\n"
    "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|"
)


def _time(value: Any) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Example selection requires timezone-aware timestamps")
    return parsed.astimezone(UTC)


def select_narration_examples(
    predictions: list[dict[str, Any]] | tuple[dict[str, Any], ...],
) -> tuple[dict[str, Any], ...]:
    """Apply the committed calendar rule; outcomes are deliberately absent."""

    ordered = sorted(
        predictions,
        key=lambda row: (_time(row["available_at"]), str(row["prediction_id"])),
    )
    selected: list[dict[str, Any]] = []
    for month in EXAMPLE_MONTHS:
        monthly = [
            row
            for row in ordered
            if _time(row["available_at"]).year == 2022
            and _time(row["available_at"]).month == month
        ]
        choice = None
        for prediction_type in EXAMPLE_TYPE_ORDER:
            choice = next(
                (
                    row
                    for row in monthly
                    if row["prediction_type"] == prediction_type
                ),
                None,
            )
            if choice is not None:
                break
        if choice is None:
            raise ValueError(f"No pass-1 prediction exists in fixed month {month}")
        available_at = _time(choice["available_at"])
        selected.append(
            {
                "fixed_month": month,
                "day": available_at.date().isoformat(),
                "available_at": available_at.isoformat(),
                "prediction_id": str(choice["prediction_id"]),
                "prediction_type": str(choice["prediction_type"]),
                "concept": str(choice["concept"]),
                "expectation": str(choice["expectation"]),
                "invalidation": str(choice["invalidation"]),
            }
        )
    if len({item["day"] for item in selected}) != 5:
        raise ValueError("The five fixed examples must select five distinct days")
    return tuple(selected)


def extract_narration_examples(
    selected: tuple[dict[str, Any], ...],
    *,
    narration_path: str | Path,
    decisions_path: str | Path,
) -> tuple[dict[str, Any], ...]:
    by_time = {item["available_at"]: item for item in selected}
    examples = {
        item["available_at"]: {**item, "narration": [], "decisions": []}
        for item in selected
    }
    with Path(narration_path).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            event = json.loads(line)
            available_at = _time(event["available_at"]).isoformat()
            if available_at in by_time:
                if re.search(r"[A-Za-z]", str(event["text"])):
                    raise ValueError("Visible narration contains non-Arabic enum prose")
                examples[available_at]["narration"].append(event)
    wanted_predictions = {item["prediction_id"] for item in selected}
    with Path(decisions_path).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            decision = json.loads(line)
            available_at = _time(decision["available_at"]).isoformat()
            if (
                available_at in by_time
                and decision.get("prediction_id") in wanted_predictions
            ):
                if re.search(r"[A-Za-z]", str(decision["reason"])):
                    raise ValueError("Visible decision contains non-Arabic enum prose")
                examples[available_at]["decisions"].append(decision)
    result = tuple(examples[item["available_at"]] for item in selected)
    for example in result:
        if not example["narration"]:
            raise ValueError(f"No full narration found for {example['prediction_id']}")
    return result


def _percent(value: float | None) -> str:
    return "غير متاح" if value is None else f"{value * 100:.2f}٪"


def _difference(value: float | None) -> str:
    return "غير متاح" if value is None else f"{value * 100:+.2f} نقطة"


def _judgment(values: dict[str, Any]) -> str:
    if values["raw_count"] == 0:
        return "لا حالات"
    if not values["outcome_applicable"]:
        return "لا ينطبق"
    if values["descriptive_only"]:
        return "وصف فقط"
    return "ثلاثون أو أكثر"


def _metric_row(variant: str, name: str, values: dict[str, Any]) -> str:
    return (
        f"| `{variant}` | {name} | {values['raw_count']} | "
        f"{values['independent_count']} | {values['true']} | {values['false']} | "
        f"{values['unjudgeable']} | {values['unjudgeable_same_bar']} | "
        f"{values['unjudgeable_truncated']} | {_percent(values['hit_rate'])} | "
        f"{_percent(values['matched_hit_rate'])} | {_percent(values['baseline_rate'])} | "
        f"{_difference(values['difference'])} | {values['matched_count']} | "
        f"{_judgment(values)} |"
    )


def _concept_name(identifier: str) -> str:
    return f"{CONCEPT_TEXT.get(identifier, identifier)} (`{identifier}`)"


def _decision_name(identifier: str) -> str:
    return f"{DECISION_TEXT.get(identifier, identifier)} (`{identifier}`)"


def _annual_table(scores: dict[str, Any], section: str) -> str:
    lines = [METRIC_HEADER]
    key = "concepts" if section == "prediction_summary" else "decisions"
    namer = _concept_name if section == "prediction_summary" else _decision_name
    for variant in VARIANT_BY_ID:
        groups = scores["variants"][variant][section][key]
        for name, values in groups.items():
            lines.append(_metric_row(variant, namer(name), values))
    return "\n".join(lines)


def _monthly_table(
    scores: dict[str, Any], month: str, section: str
) -> str:
    lines = [METRIC_HEADER]
    key = "concepts" if section == "prediction_summary" else "decisions"
    namer = _concept_name if section == "prediction_summary" else _decision_name
    for variant in VARIANT_BY_ID:
        groups = scores["variants"][variant][section]["monthly"][month][key]
        for name, values in groups.items():
            lines.append(_metric_row(variant, namer(name), values))
    return "\n".join(lines)


def _weakness_rows(scores: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for variant in VARIANT_BY_ID:
        variant_scores = scores["variants"][variant]
        groups = [
            ("مفهوم", name, values)
            for name, values in variant_scores["prediction_summary"][
                "concepts"
            ].items()
        ]
        groups += [
            ("قرار", name, values)
            for name, values in variant_scores["decision_summary"]["decisions"].items()
            if name not in {"stand_aside", "management"}
        ]
        for group, name, values in groups:
            difference = values["difference"]
            no_better = difference is not None and difference <= 0
            if not values["outcome_applicable"] or not (
                values["false"] or no_better
            ):
                continue
            if values["false"] and no_better:
                reason = "إخفاق ولا تفوق على الأساس"
            elif no_better:
                reason = "لا تفوق على الأساس"
            elif difference is None:
                reason = "إخفاق بلا أساس متطابق"
            else:
                reason = "إخفاق رغم التفوق على الأساس"
            rows.append(
                {
                    "variant": variant,
                    "group": group,
                    "name": name,
                    "values": values,
                    "reason": reason,
                    "no_better": no_better,
                }
            )
    rows.sort(
        key=lambda row: (
            0 if row["no_better"] else 1 if row["values"]["difference"] is not None else 2,
            row["values"]["difference"]
            if row["values"]["difference"] is not None
            else float("inf"),
            -(row["values"]["wrong_rate"] or 0.0),
            -row["values"]["independent_count"],
            row["variant"],
            row["group"],
            row["name"],
        )
    )
    return rows


def _weakness_table(scores: dict[str, Any]) -> str:
    lines = [
        "| الرتبة | المتغير | الفئة | الاسم | المستقل | معدل الإخفاء | الفرق عن الأساس | سبب الإدراج | الحكم |",
        "|---:|---|---|---|---:|---:|---:|---|---|",
    ]
    for rank, row in enumerate(_weakness_rows(scores), start=1):
        values = row["values"]
        name = (
            _concept_name(row["name"])
            if row["group"] == "مفهوم"
            else _decision_name(row["name"])
        )
        lines.append(
            f"| {rank} | `{row['variant']}` | {row['group']} | {name} | "
            f"{values['independent_count']} | {_percent(values['wrong_rate'])} | "
            f"{_difference(values['difference'])} | {row['reason']} | "
            f"{_judgment(values)} |"
        )
    return "\n".join(lines)


def _selection_table(selected: tuple[dict[str, Any], ...]) -> str:
    lines = [
        "| الشهر المثبت | اليوم المختار | وقت الإتاحة | نوع التنبؤ | معرف التنبؤ |",
        "|---|---|---|---|---|",
    ]
    for item in selected:
        lines.append(
            f"| {MONTH_TEXT[item['fixed_month']]} | {item['day']} | "
            f"{item['available_at']} | {PREDICTION_TYPE_TEXT[item['prediction_type']]} "
            f"(`{item['prediction_type']}`) | `{item['prediction_id']}` |"
        )
    return "\n".join(lines)


def render_main_report(
    scores: dict[str, Any],
    selected: tuple[dict[str, Any], ...],
    *,
    sample_spec_commit: str,
) -> str:
    provenance = scores["provenance"]
    data = scores["data"]
    return f"""# تقرير تسجيل التطوير للمرحلة الثالثة — 2022 فقط

## النطاق والحكم

سُجلت السجلات الستة على 2022 وحدها، بأفق 288 شمعة سوق لاحقة، ومن دون قراءة 2023 أو أي سنة لاحقة. لا يوجد ربح مالي أو كمية أو عمولة في هذا التقرير. النتائج وصف للتطوير، وليست اختباراً نهائياً ولا اختياراً لفائز. توقف العمل بعد هذه المرحلة ولم تبدأ المرحلة الرابعة.

الأقل من 30 حالة مستقلة «وصف فقط». معدل الإصابة الكامل يستبعد التعارض والبتر من مقامه. معدل الإصابة المتطابق وخط الأساس والفرق يحسب على الحالات المحسومة نفسها التي لها توقع أساس سابق. لذلك قد يختلف المعدل الكامل عن المتطابق. «غير متاح» يعني عدم وجود مقام صالح، لا صفراً.

## الإثبات السابق للتسجيل

- آخر التزام لعقد التنبؤ: `{provenance['prediction_spec_commit']}`.
- آخر التزام لخطة المتغيرات: `{provenance['variant_plan_commit']}`.
- الالتزام الذي أنشأ أداة التسجيل ومولد التقارير: `{provenance['scoring_commit']}`، وهو لاحق للالتزامين السابقين.
- التزام قاعدة اختيار الأمثلة: `{sample_spec_commit}`.
- بصمة ملف 2022: `{data['sha256']}`؛ عدد الصفوف {data['rows']}، وشموع السوق {data['market_candles']}.
- وحدة الاستقلال: `{scores['independence_id']}`. العد الخام يشمل كل إصدار، والمستقل يبقي أول إصدار لكل نوع وكائن داخل المتغير.
- خط الأساس: `{scores['baseline_id']}`. تاريخه منفصل لكل متغير ونوع واتجاه، ولا يدخله تكرار خام أو تعارض أو بتر أو نتيجة لم تحل بعد.

## النتائج السنوية بحسب مفهوم التنبؤ

{_annual_table(scores, 'prediction_summary')}

## النتائج السنوية بحسب نوع القرار

ترث قرارات الهدف والدخول والوقف نتيجة التنبؤ المرتبط ولا تضاعف عدد الملاحظات المستقلة. الامتناع قرار مسبب لا نتيجة سوق له؛ لذلك تظهر معدلاته وخط أساسه وفرقه «غير متاح».

{_annual_table(scores, 'decision_summary')}

## جدول الضعف

يرتب الجدول أولاً ما لا يتفوق على الأساس بالفرق الأصغر، ثم الأعلى في معدل الإخفاق. عند غياب أساس متطابق يأتي الإخفاق بلا أساس لاحقاً. هذا ترتيب تشخيصي لكل صف، وليس ترتيباً للمتغيرات ولا توصية باختيار أحدها.

{_weakness_table(scores)}

## النتائج الشهرية

كل شهر في `M3_MONTHLY_REPORT.md` يعرض المفاهيم وأنواع القرار للمتغيرات الستة جنباً إلى جنب، بالحقول نفسها. الشهر هو شهر أول الإصدار المستقل بالتوقيت العالمي، وتاريخ الأساس لا يعاد ضبطه شهرياً.

## اختيار أيام السرد الخمسة

اختيرت الأيام بقاعدة `NARRATION_SAMPLE_SPEC.md` الملتزم بها قبل رؤية النتائج: أول يوم بتنبؤ دخول في يناير وأبريل ويوليو وأكتوبر وديسمبر، ثم أول عودة عند غيابه، ثم بلوغ السيولة. لم تدخل أي نتيجة في دالة الاختيار.

{_selection_table(selected)}

النصوص الكاملة لأحداث وقت الإتاحة والقرارات المرتبطة في `M3_NARRATION_EXAMPLES.md`. هذه شواهد تفسيرية غير عشوائية التقدير وليست عينة أداء.

## تغطية المعرفة والخطوة الممنوعة

قُرئت البطاقات الثلاث والعشرون من الالتزام `567460bf4fa0773ef1633738b72a61399cfcf3e3`، وأُهملت الهياكل المتجاوزة. التغطية 66 من 66 في 67 بطاقة مادية بسبب بطاقة العلاوة والخصم المشتركة. جدول المنفذ والجزئي والمنتظر كامل في `K3_CONCEPT_COVERAGE.md`.

لم يضف أي مفهوم جديد قبل أول تسجيل. الإضافات الممكنة لاحقاً هي منتصف الفجوة، ومراسي آسيا ومنتصف الليل والافتتاح، ومتغيرات الفجوة المقلوبة، وامتناع الموعد الإخباري الصريح، وتوسيع الأطر، وحدود القاع القديم، ثم تأكيد الجري على الوقف بعد توفر متطلباته. كلها مؤجلة وتحتاج موافقة صريحة.

## الحدود

لا يدعي التقرير سببية أو قدرة تداولية، ولا يحول الامتناع إلى إصابة، ولا يعالج التعارض داخل الشمعة بافتراض ترتيب. حالات نهاية البيانات بتر وليست إخفاقاً. لم تُغير قاعدة أو أفق أو متغير لرفع معدل الإصابة، ولم تُستخدم بيانات محظورة.
"""


def render_monthly_report(scores: dict[str, Any]) -> str:
    parts = [
        "# التقرير الشهري للمرحلة الثالثة — 2022 فقط\n\n"
        "كل الجداول تعرض الخام والمستقل والإصابة والإخفاق وعدم الحكم والمعدلين والأساس والفرق. "
        "الأقل من ثلاثين مستقلاً وصف فقط. لا يوجد اختيار فائز، ولم تستخدم سنة لاحقة."
    ]
    for month_number in range(1, 13):
        month = f"2022-{month_number:02d}"
        parts.append(
            f"## {MONTH_TEXT[month_number]}\n\n### مفاهيم التنبؤ\n\n"
            f"{_monthly_table(scores, month, 'prediction_summary')}"
        )
        parts.append(
            f"### أنواع القرار\n\n{_monthly_table(scores, month, 'decision_summary')}"
        )
    return "\n\n".join(parts) + "\n"


def render_narration_examples(
    examples: tuple[dict[str, Any], ...], *, narration_sha256: str
) -> str:
    parts = [
        "# خمسة أمثلة سردية كاملة من 2022\n\n"
        "اختيرت الأيام بالقاعدة المثبتة قبل رؤية النتائج. يعرض كل مثال كل أحداث السرد عند وقت الإتاحة، "
        "ثم قرارات التنبؤ المختار، والتوقع والإبطال كاملين. المعرفات آلية وليست جزءاً من النثر العربي. "
        f"بصمة سرد المصدر `{narration_sha256}`. لا تعرض هذه الوثيقة نتيجة لاحقة للأمثلة."
    ]
    for number, example in enumerate(examples, start=1):
        lines = [
            f"## المثال {number}: {example['day']}\n\n"
            f"- وقت الإتاحة: `{example['available_at']}`.\n"
            f"- معرف التنبؤ: `{example['prediction_id']}`.\n"
            f"- نوع التنبؤ: {PREDICTION_TYPE_TEXT[example['prediction_type']]} "
            f"(`{example['prediction_type']}`).\n"
            f"- التوقع الكامل: {example['expectation']}\n"
            f"- الإبطال الكامل: {example['invalidation']}\n\n"
            "### جميع أحداث السرد عند هذا الوقت"
        ]
        for event in example["narration"]:
            claims = "، ".join(f"`{claim}`" for claim in event["claim_ids"]) or "لا إحالات"
            lines.append(
                f"\n**`{event['event_id']}`**\n\n"
                f"- المفهوم الآلي: `{event['concept']}`.\n"
                f"- الادعاءات: {claims}.\n"
                f"- النص الكامل: {event['text']}"
            )
        lines.append("\n### قرارات التنبؤ المختار عند هذا الوقت")
        if not example["decisions"]:
            lines.append("\nلا توجد قرارات مرتبطة بهذا التنبؤ عند هذا الوقت.")
        for decision in example["decisions"]:
            claims = "، ".join(f"`{claim}`" for claim in decision["claim_ids"]) or "لا إحالات"
            lines.append(
                f"\n**`{decision['decision_id']}`**\n\n"
                f"- نوع القرار: {_decision_name(decision['decision_type'])}.\n"
                f"- الادعاءات: {claims}.\n"
                f"- السبب الكامل: {decision['reason']}"
            )
        parts.append("\n".join(lines))
    return "\n\n".join(parts) + "\n"


def generate_reports(
    *,
    scores_path: str | Path,
    ledger_root: str | Path,
    narration_path: str | Path,
    output_dir: str | Path,
    sample_spec_commit: str,
) -> tuple[Path, Path, Path]:
    scores = json.loads(Path(scores_path).read_text(encoding="utf-8"))
    if scores["year"] != 2022:
        raise ValueError("Arabic M3 reports are restricted to 2022")
    root = Path(ledger_root)
    predictions = read_jsonl(root / "m2_R00_predictions.jsonl")
    selected = select_narration_examples(predictions)
    examples = extract_narration_examples(
        selected,
        narration_path=narration_path,
        decisions_path=root / "m2_R00_decisions.jsonl",
    )
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    main = destination / "M3_DEV_REPORT.md"
    monthly = destination / "M3_MONTHLY_REPORT.md"
    narratives = destination / "M3_NARRATION_EXAMPLES.md"
    main.write_text(
        render_main_report(scores, selected, sample_spec_commit=sample_spec_commit),
        encoding="utf-8",
        newline="\n",
    )
    monthly.write_text(render_monthly_report(scores), encoding="utf-8", newline="\n")
    narratives.write_text(
        render_narration_examples(examples, narration_sha256=sha256_file(narration_path)),
        encoding="utf-8",
        newline="\n",
    )
    return main, monthly, narratives


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="توليد تقارير عربية لنتائج 2022.")
    parser.add_argument("--scores", required=True)
    parser.add_argument("--ledger-root", required=True)
    parser.add_argument("--narration", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--sample-spec-commit", required=True)
    return parser


def main() -> None:
    arguments = _parser().parse_args()
    paths = generate_reports(
        scores_path=arguments.scores,
        ledger_root=arguments.ledger_root,
        narration_path=arguments.narration,
        output_dir=arguments.output_dir,
        sample_spec_commit=arguments.sample_spec_commit,
    )
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
