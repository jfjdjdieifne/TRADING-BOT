"""Human-readable Arabic report generator for the fixed replay."""

from __future__ import annotations

import json
from pathlib import Path


def _fmt(value: object, digits: int = 2) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def _pct(value: object) -> str:
    return "—" if value is None else f"{float(value) * 100:.1f}%"


def _summary_block(summary: dict, key: str) -> list[str]:
    item = summary["configs"][key]
    lines = [f"### {key}", "", "| الاتجاه | مرشحو sweep | صالحة بعد كل الشروط | دخول فوري | أهداف | ستوبات | خروج بعد 3 شمعات | مجموع R | متوسط R | hit target/stop |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for side in ("LONG", "SHORT"):
        group = item["immediate"].get(f"{key}|{side}|immediate", {})
        lines.append(
            f"| {side} | {item['signals_by_side'][side]} | {item['eligible_by_side'][side]} | {group.get('entered', 0)} | "
            f"{group.get('target_hits', 0)} | {group.get('stop_hits', 0)} | {group.get('time_exits', 0)} | "
            f"{_fmt(group.get('sum_r'))} | {_fmt(group.get('mean_r'))} | {_pct(group.get('target_hit_rate_of_barrier_exits'))} |"
        )
    lines.append("")
    return lines


def write_report(summary: dict, path: Path) -> None:
    primary = summary["configs"]["STRICT_FVG_P80"]
    zla = summary["zero_lookahead"]
    ds = summary["dataset"]
    contract = summary["contract"]
    lines = [
        "# تصحيح استراتيجية Sweep → Displacement — replay سببي حقيقي",
        "",
        "> هذا التقرير مبني من أرقام replay التي شغّلها `run_2021.py` على ملفات XAUUSD الموجودة داخل المستودع. لا توجد أرقام تجريبية مكتوبة باليد.",
        "",
        "## التصحيح الذي طلبته",
        "",
        "- **الهدف صحيح:** في الشراء هو **أقرب قمة swing مؤكدة قبل القاع الذي انمسحت سيولته**. وفي البيع هو المرآة الدقيقة: **أقرب قاع swing مؤكد قبل القمة التي انمسحت سيولتها**.",
        "- شمعة sweep لا تحدد الاتجاه وحدها. الاتجاه يأتي من **شمعة displacement التالية**.",
        "- الـ sweep العلوي مع ذيل فوق القمة ثم **شمعة حمراء كبيرة بعدها** هو **SHORT بيع**، وليس LONG. لذلك تم فصل LONG وSHORT في كل جدول ولم يتم قلب مثال 2021 إلى شراء.",
        "- تم تثبيت الحد الزمني: displacement يجب أن يكون **S+1 فقط**. لم أعد أقبل R/D في S+2 أو S+3 تحت الاسم نفسه.",
        "- شمعة ما بعد displacement قد تكون خضراء أو حمراء وصغيرة أو hammer. نسجلها كـ **وصف لاحق** فقط؛ لا نستخدمها لإعطاء الإشارة بأثر رجعي.",
        "- سؤال «هل يتحرك فوراً خلال ثلاث شمعات؟» قيس كصفقة تدخل عند إغلاق displacement وتراقب **D+1 إلى D+3**. يوجد أيضاً مسار منفصل ينتظر إغلاق الشمعة الثالثة، ثم يراقب ثلاث شمعات جديدة؛ إذا لمس target/stop قبل الدخول فلا توجد صفقة.",
        "",
        "## العقد المطبق حرفياً",
        "",
        f"- البيانات: `{ds['symbol']}`، setup `{ds['setup_timeframe']}`، path `{ds['path_timeframe']}`.",
        f"- فترة القياس: `{ds['evaluation_start_utc']}` إلى قبل `{ds['evaluation_end_utc_exclusive']}`، أي `{', '.join(ds['evaluation_months'])}`.",
        f"- warm-up: `{', '.join(ds['warmup_months'])}`. شهر `{', '.join(ds['outcome_only_months'])}` استُخدم فقط لإكمال نتيجة صفقة قرب نهاية نوفمبر، وليس لتقرير وجود الإشارة قبل نهاية الفترة.",
        f"- sweep: `{contract['sweep']}`.",
        f"- swing: `{contract['swing_confirmation']}`.",
        f"- displacement: `{contract['displacement_timing']}`.",
        f"- FVG: `{contract['fvg']}`.",
        f"- target: `{contract['target']}`.",
        f"- stop: `{contract['stop']}`.",
        f"- execution: `{contract['entry']}`. الأرقام **gross R**؛ المصدر لا يملك bid/ask/spread، لذلك `cost=0` ولا أدعي spread حقيقياً غير موجود.",
        f"- outcome: `{contract['horizon']}`.",
        "",
        "## النتائج الإجمالية — لاختيار الاتجاه الصحيح",
        "",
    ]
    for config_name in summary["configs"]:
        lines.extend(_summary_block(summary, config_name))
    lines += [
        "## القراءة العملية للنتيجة الأساسية",
        "",
        f"- `STRICT_FVG_P80` يعني displacement أخضر/أحمر باتجاه الصفقة، range ضمن أعلى 20% من آخر 20 شمعة مكتملة، body fraction ≥ 60%، وFVG ثلاثي الشموع إلزامي.",
        f"- مرشحو sweep LONG في النسخة الأساسية: **{primary['signals_by_side']['LONG']}**؛ الصالحون بعد اللون/الحجم/body/FVG/target: **{primary['eligible_by_side']['LONG']}**.",
        f"- مرشحو sweep SHORT في النسخة الأساسية: **{primary['signals_by_side']['SHORT']}**؛ الصالحون بعد اللون/الحجم/body/FVG/target: **{primary['eligible_by_side']['SHORT']}**.",
        "- هذه ليست انتقائية بعد رؤية النتيجة: variants الثلاثة محددة في الكود قبل التشغيل. `DIRECTION_P80_NO_FVG` للتشخيص، وليس بديلاً عن النسخة التي طلبت فيها FVG.",
        "",
        "### السجلات الأساسية الصالحة فعلياً",
        "",
        "| الاتجاه | وقت S | وقت D=S+1 | level / extreme المسح | التارغت السابق | FVG | شمعة بعد D | النتيجة | R |",
        "|---|---|---|---:|---:|---|---|---|---:|",
    ]
    for row in summary.get("primary_eligible_examples", []):
        lines.append(
            f"| {row['side']} | {row['sweep_time']} | {row['displacement_time']} | {_fmt(row['swept_level'], 3)} / {_fmt(row['sweep_extreme'], 3)} | "
            f"{_fmt(row['target_level'], 3)} | {row['fvg']} | {row['post_color'] or '—'} / small={row['post_small']} | "
            f"{row['outcome']} | {_fmt(row['r_multiple'])} |"
        )
    lines += [
        "",
        "### إذا انتظرنا ثلاث شمعات قبل الدخول",
        "",
        "| الاتجاه | دخل بعد D+3 | target | stop | خروج زمني | barrier قبل الدخول | مجموع R | متوسط R |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for side in ("LONG", "SHORT"):
        delayed = primary["after_three"].get(f"STRICT_FVG_P80|{side}|after_three", {})
        lines.append(
            f"| {side} | {delayed.get('entered', 0)} | {delayed.get('target_hits', 0)} | "
            f"{delayed.get('stop_hits', 0)} | {delayed.get('time_exits', 0)} | "
            f"{delayed.get('pre_entry_barrier', 0)} | {_fmt(delayed.get('sum_r'))} | {_fmt(delayed.get('mean_r'))} |"
        )
    lines += [
        "",
        "## اختبار zero look-ahead",
        "",
        f"- prefix cutoff: `{zla['prefix_cutoff_utc']}`.",
        f"- الإشارات الأساسية قبل القطع في replay الكامل: `{zla['full_core_signals_before_cut']}`؛ في replay المقطوع: `{zla['prefix_core_signals']}`.",
        f"- التطابق الكامل للقرار قبل القطع: **{zla['prefix_core_identical']}**.",
        "- التحقق لا يقارن النتائج المستقبلية كأنها إشارات؛ future bars تُقرأ فقط بعد تسجيل signal لحساب outcome.",
        "",
        "## الملفات",
        "",
        "- `signals.csv`: كل sweep + D، وفيه LONG/SHORT، target source، FVG، وملصق الشمعة الصغيرة اللاحقة.",
        "- `outcomes.csv`: outcome الفوري و`after_three` لكل إشارة، مع stop-first عند لمس المستويين في نفس دقيقة.",
        "- `summary.json`: أرقام machine-readable وبصمات الملفات.",
        "- `charts/short_example_2021.svg`: مثال حقيقي مصحح: upper sweep ثم red displacement = SHORT.",
        "- `charts/long_example.svg`: المرآة الصاعدة.",
        "",
        "## حدود لازمة",
        "",
        "- ستة أشهر قليلة وليست إثبات edge أو ربحية مستقبلية. لا يوجد walk-forward أو broker spread في هذه الجولة.",
        "- المصدر المعبأ هو XAUUSD OHLC دقيقة، وليس EURUSD bid/ask الذي ظهر في دراسة سابقة. لذلك لا يجوز دمج الرقم مع نتائج EURUSD القديمة.",
        "- أي chart يبيّن شمعة صغيرة بعد D لا يعطيها قدرة تنبؤية؛ هي معلومة لا تصبح متاحة إلا بعد إغلاقها.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    here = Path(__file__).resolve().parent
    result_dir = here / "results_2021_six_months"
    summary = json.loads((result_dir / "summary.json").read_text(encoding="utf-8"))
    write_report(summary, result_dir / "REPORT_AR.md")


if __name__ == "__main__":
    main()
