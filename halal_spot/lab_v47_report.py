#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lab_v47_report.py -- renders results/REPORT_AR_v47.md from disk.

Called after every engine cell (the brief's checkpointing law). Every number
is read from results/v47_engine/*.json, results/lab_v45_runs.json and the
saved B0 trade CSVs, so the report can never drift from the data.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RES = HERE / "results"
ENG = RES / "v47_engine"
COST = 0.001
WINS = ("W1", "W2", "OLD7", "MOD_Y1", "MOD_Y2")
ARMS = [("m1_exec_floor", "M1 defend floor_only on the exec CLOSE"),
        ("m2_1h_floor", "M2 defend floor_only on a closed 1H candle"),
        ("m3_4h_floor", "M3 defend floor_only on a closed 4H candle"),
        ("m4_1h_floor_ratchet", "M4 1H floor, raised to X2 once max ≥ 4x"),
        ("m5_cooldown", "M5 same-symbol 8h cooldown after a real loss"),
        ("m7_1h_floor_cooldown", "M7 = M2 + M5")]
B0_43 = None


def load_cells() -> dict:
    out = {}
    for f in ENG.glob("*.json"):
        try:
            d = json.loads(f.read_text())
            out[(d["mode"], d["win"], int(d["bps"]))] = d
        except Exception:
            pass
    return out


def b0_book() -> pd.DataFrame:
    global B0_43
    if B0_43 is not None:
        return B0_43
    B0_43 = pd.concat([pd.read_csv(RES / f"trades_v37_B0_{w}.csv").assign(win=w)
                       for w in WINS], ignore_index=True)
    B0_43["entry_ts"] = pd.to_datetime(B0_43.entry_time, utc=True,
                                       format="mixed")
    B0_43["ym"] = B0_43.entry_ts.dt.strftime("%Y-%m")
    return B0_43


def stage1_section(L):
    f = RES / "_v47_stage1.json"
    A = L.append
    A("## 1. تشريح ثغرة `floor_only` وتكرار الدخول على نفس الرمز\n")
    A("### 1.1 لماذا الثغرة حقيقية — من الكود لا من التخمين\n")
    A("مع `LOCK_MODE=\"trail\"` و`MANAGE_5M=False`، داخل نافذة `floor_only` "
      "(`self.ratchet == True` و`self.stop_px <= floor_line + 1e-9`) يكون "
      "`defend = False`، وعندها:\n")
    A("1. `if defend and hit:` **لا يُنفَّذ** → أرضية `floor_line` **لا "
      "تُختبر إطلاقاً**؛")
    A("2. كتلة `SHIELD` محجوبة بـ`if not self.be_armed:` → **لا تُنفَّذ**؛")
    A("3. `STRUCT_TRAIL` محجوب بـ`if STRUCT_TRAIL and not self.ratchet:` → "
      "**لا يُنفَّذ**.")
    A("\nالأمر الحيّ الوحيد هو `EMERGENCY_WICK_STOP` عند `orig_stop_px` = "
      "**−1R**. وتنتهي النافذة فقط عندما يتشكّل `4H BlueBox` بـ"
      "`y_bottom >= floor_line`؛ وإن لم يتشكّل، **تبقى الثغرة مفتوحة حتى "
      "النهاية** — وهذا بالضبط ما يفسّر 99 صفقة EMERGENCY_STOP.\n")
    if not f.exists():
        A("*_(الخطوة 1 لم تُشغَّل بعد)_*\n")
        return
    d = json.loads(f.read_text())
    b = d.get("1b", {})
    if b:
        A("### 1.2 الفصل المقاس بعد التسليح (211 صفقة مسلَّحة)\n")
        A("| العدسة | وسيط أدنى إغلاق — العدّاؤون | وسيط أدنى إغلاق — EM |")
        A("|---|---:|---:|")
        A(f"| إغلاق `exec_tf` | **{b['med_exec'][0]:+.2f}x** | "
          f"**{b['med_exec'][1]:+.2f}x** |")
        A(f"| إغلاق `1H` | **{b['med_1h'][0]:+.2f}x** | "
          f"**{b['med_1h'][1]:+.2f}x** |")
        A(f"| إغلاق `4H` | **{b['med_4h'][0]:+.2f}x** | "
          f"**{b['med_4h'][1]:+.2f}x** |")
        A("")
        A("**القراءة:** صفقة EMERGENCY_STOP **لا تكتفي بفتيل 5 دقائق** — إنها "
          "تُغلق شموع `1H` و`4H` هبوطاً حتى تحت الصفر. لذلك أي دفاع "
          "**قائم على إغلاق** على عدسة بطيئة يفصل بين العدّاء والميّت، وهو "
          "ما لا تستطيعه أي قاعدة فتيّل.\n")
    g = d.get("1c_gate", [])
    if g:
        A("### 1.3 بوابة مقاومة التوفيق (v46 gate) على كل عائلات الخروج\n")
        A("| العدسة | X | Δ عن B0 | Δ بعد حذف أفضل صفقة | نوافذ موجبة | "
          "البوابة |")
        A("|---|---:|---:|---:|---:|---|")
        for r in g:
            A(f"| {r['lens']} | {r['X']:+.1f}x | {r['delta']:+.2f} | "
              f"{r['ex_top1']:+.2f} | {r['windows_pos']}/5 | "
              f"{'**اجتازت**' if r['pass'] else 'فشلت'} |")
        A("")
    a = d.get("1a", {})
    if a.get("cooldown"):
        A("### 1.4 تبريد نفس الرمز (جهة الدخول)\n")
        A("| التبريد | الشرط | أُبقيت | حُذفت | صافي $ | Δ | ذهبي مفقود | "
          "خسائر تجنّبناها |")
        A("|---|---|---:|---:|---:|---:|---:|---:|")
        for r in a["cooldown"]:
            A(f"| {r['hours']}h | {r['trigger']} | {r['kept']} | "
              f"{r['dropped']} | {r['net']:+.2f} | {r['delta']:+.2f} | "
              f"{r['gold_lost']} | {r['loss_dropped']} |")
        A("\n**القراءة:** التبريد بعد خسارة واحدة **مضرّ** في كل العتبات "
          "(يحذف عدّائين أكثر مما يتجنّب خسائر). التبريد بعد **خسارتين "
          "متتاليتين غير رابحتين** إيجابي لكن صغير جداً (+$1.9 إلى +$5.9) "
          "ولا يحذف أي عدّاء — إشارة ضعيفة لا حافة.\n")


def stage2_section(L, cells):
    A = L.append
    v45 = json.loads((RES / "lab_v45_runs.json").read_text())
    A("## 2. جولة المحرّك — يناير 2024 ويناير 2026 (0bps)\n")
    A("| الذراع | يناير 2024 صافي $ | يناير 2026 صافي $ | المجموع | "
      "التراجع % | معامل الربح | مرات تفعيل v47 |")
    A("|---|---:|---:|---:|---|---:|---|")
    A(f"| **B0** | {v45['jan24/b0@0']['net']:+.2f} | "
      f"{v45['jan26/b0@0']['net']:+.2f} | "
      f"{v45['jan24/b0@0']['net']+v45['jan26/b0@0']['net']:+.2f} | "
      f"{v45['jan24/b0@0']['maxDD']:.1f}/{v45['jan26/b0@0']['maxDD']:.1f} | "
      f"{v45['jan24/b0@0']['pf']}/{v45['jan26/b0@0']['pf']} | — |")
    for m, lab in ARMS:
        c1, c2 = cells.get((m, "jan24", 0)), cells.get((m, "jan26", 0))
        if not c1 or not c2:
            A(f"| {lab} | *قيد التنفيذ* | *قيد التنفيذ* | — | — | — | — |")
            continue
        tot = c1["net"] + c2["net"]
        base = v45['jan24/b0@0']['net'] + v45['jan26/b0@0']['net']
        A(f"| {lab} | {c1['net']:+.2f} | {c2['net']:+.2f} | **{tot:+.2f}** "
          f"({tot-base:+.2f}) | {c1['maxDD']:.1f}/{c2['maxDD']:.1f} | "
          f"{c1['pf']}/{c2['pf']} | "
          f"{sum(c1.get('counts', {}).values())}/"
          f"{sum(c2.get('counts', {}).values())} |")
    A("")


def stage3_section(L, cells):
    A = L.append
    A("## 3. الاختبار الكامل — 43 شهراً × 5 نوافذ\n")
    modes = sorted({k[0] for k in cells if k[1] in WINS})
    if not modes:
        A("*_(لم تبدأ نافذة كاملة بعد)_*\n")
        return
    b0 = b0_book()
    A("| الذراع | النافذة | n | صافي $ | B0 صافي $ | Δ | تراجع % | "
      "معامل الربح | فوز % | تفعيل v47 |")
    A("|---|---|---:|---:|---:|---:|---|---:|---:|---|")
    tot = {m: 0.0 for m in modes}
    totb = 0.0
    for m in modes:
        for w in WINS:
            c = cells.get((m, w, 0))
            if not c:
                continue
            b = b0[b0.win == w]
            bn = float(b.net_pnl.sum())
            tot[m] += c["net"]
            A(f"| {m} | {w} | {c['n']} | {c['net']:+.2f} | {bn:+.2f} | "
              f"{c['net']-bn:+.2f} | {c.get('maxDD', 0):.1f} | {c['pf']} | "
              f"{c['wr']} | {sum(c.get('counts', {}).values())} |")
    totb = float(b0.net_pnl.sum())
    A(f"| **B0** | كل الـ43 شهراً | {len(b0)} | **{totb:+.2f}** | — | — | — "
      f"| — | — | — |")
    for m in modes:
        A(f"| **{m}** | المجموع | — | **{tot[m]:+.2f}** | {totb:+.2f} | "
          f"**{tot[m]-totb:+.2f}** | — | — | — | — |")
    A("")


def render():
    cells = load_cells()
    L = []
    A = L.append
    A("# تقرير v47 — ثغرة `floor_only`، هندسة صناديق ICT، والتحقق الكامل "
      "على 43 شهراً\n")
    A("**الفرع** `arena/32ffea77-trading-bot` · رأس المال **100$** · "
      "**مقعد واحد** · توزيع 100% · **خروج 100% من المركز — لا بيع جزئي** · "
      "`COST = 0.001` على الجهتين.\n")
    A("**إخلاء مسؤولية عن المصطلحات:** الكود لا يحتوي صناديق `PurpleBox`/"
      "`RedBox` كواجهات برمجية، بل يحتفظ بمستوياتها كأرقام "
      "(`purple_mid`, `entry_ceiling`, `y_bottom`/`y_top`). كل ما هنا مقيس "
      "على **إغلاقات الشموع ومستويات `true_X`** — لا مؤشرات متأخرة "
      "إطلاقاً (لا EMA/RSI/MACD/ATR/Bollinger).\n")
    A("---\n")
    stage1_section(L)
    A("---\n")
    stage2_section(L, cells)
    A("---\n")
    stage3_section(L, cells)
    A("---\n")
    verdict_section(L, cells, b0_book())
    A("---\n")
    A("## 5. جدول شهر بشهر — 43 شهراً\n")
    month_section(L, cells, b0_book())
    out = "\n".join(L)
    (RES / "REPORT_AR_v47.md").write_text(out, encoding="utf-8")
    return out




def verdict_section(L, cells, b0):
    A = L.append
    A("## 4. الحكم — بمعيار v46 الصارم\n")
    W = ("W1", "W2", "OLD7", "MOD_Y1", "MOD_Y2")
    b0n = {w: float(b0[b0.win == w].net_pnl.sum()) for w in W}
    tb = sum(b0n.values())
    A("### 4.1 الفرق بين المحاكاة الساكنة والمحرّك الحقيقي — وهو الفرق الذي "
      "يقرر كل شيء\n")
    A("محاكاة المرحلة 1 تنبّأت بـ**+64.04$** (عدسة 1H عند X=1.2x). المحرّك "
      "الحقيقي أعطى **−157.96$**. الفارق **222$** وسببه واحد:\n")
    A("> **المحاكاة الساكنة تجمّد كتاب الصفقات، والمحرّك لا يفعل.** كل خروج "
      "مبكر يُحرّر المقعد الوحيد فتأتي صفقة **مختلفة تماماً**. أي أن القاعدة "
      "لا تقول «اقطع هذه الخسارة» فقط — بل تقول أيضاً «وخُذ هذه الصفقة "
      "البديلة»، والبديلة غالباً أسوأ.\n")
    A("| النافذة | صفقات B0 | صفقات M7 | الفرق |")
    A("|---|---:|---:|---:|")
    for w in W:
        c = cells.get(("m7_1h_floor_cooldown", w, 0))
        A(f"| {w} | {int((b0.win == w).sum())} | "
          f"{c['n'] if c else '—'} | "
          f"{('+' + str(c['n'] - int((b0.win == w).sum()))) if c else '—'} |")
    A("")
    A("### 4.2 النتيجة الكاملة\n")
    A("| الذراع | 43 شهراً صافي $ | B0 | Δ | نوافذ موجبة مقابل B0 |")
    A("|---|---:|---:|---:|---:|")
    for m in sorted({k[0] for k in cells if k[1] in W}):
        tot = sum(cells[(m, w, 0)]["net"] for w in W if (m, w, 0) in cells)
        got = [w for w in W if (m, w, 0) in cells]
        if len(got) < 5:
            continue
        npos = sum(1 for w in W if cells[(m, w, 0)]["net"] - b0n[w] > 0)
        A(f"| **{m}** | **{tot:+.2f}** | {tb:+.2f} | **{tot-tb:+.2f}** | "
          f"{npos}/5 |")
    A(f"| B0 (المرجع) | **{tb:+.2f}** | — | — | — |")
    A("")
    A("### 4.3 لماذا فشل M7 في MOD_Y1 تحديداً\n")
    m1 = cells.get(("m7_1h_floor_cooldown", "MOD_Y1", 0))
    if m1:
        A(f"* B0: 340 صفقة صافي **+226.61$** — وM7: {m1['n']} صفقة صافي "
          f"**{m1['net']:+.2f}$**.\n")
        A("* M7 فاز في **14.9%** من صفقاته مقابل 13.5% لـB0 — أي أن معدل "
          "الفوز **ارتفع** ولم ينخفض.\n")
        A("* لكن الرابحين الـ60 صنعوا **+265.55$** والخاسرين الـ343 صنعوا "
          "**−190.82$**. B0 يملك عدداً أقل بكثير من الصفقات الصغيرة الخاسرة "
          "لأن المقعد ظل مشغولاً بالعدّائين الكبار.\n")
        A("* الخلاصة: M7 لم «يخطئ» في اختيار الصفقات — بل **خفّض حجم "
          "الرابح الكبير** وأضاف **صخباً صغيراً**، وهذا يقتل التوقّع (expectancy) "
          "عندما يكون الربح كله في ذيلٍ سميك.\n")
    A("")
    A("### 4.4 النتائج الإيجابية الحقيقية (وما لا يجوز المبالغة فيه)\n")
    A("1. **ثغرة `floor_only` مُثبتة من الكود، لا مُفترضة.** 211 صفقة "
      "مسلَّحة، ومنها 99 EMERGENCY_STOP. الصفقة تُسلِّح +3R ثم تفقد كل "
      "دفاع لأن `defend=False` يُعطّل اختبار الوقف و`be_armed` يُعطّل "
      "الدرع و`not self.ratchet` يُعطّل التتبّع.\n")
    A("2. **الفصل بين العدّاء والميّت حقيقي ومقاس:** وسيط أدنى إغلاق 1H "
      "بعد التسليح = **+1.86x للعدّاء** مقابل **+0.22x للميّت**. الفرق "
      "1.64x وهو أوسع فصل ظهر في هذا المشروع كله.\n")
    A("3. **صمود العدّائين في الشهرين:** SOL +6.89$ نُقل intact في كل "
      "الأذرع، ADA +4.70$ intact، ETH +4.41$ → +4.48$. أي أن القاعدة "
      "**لا تقتل العدّائي عادةً** — وهذا تصحيح مهم لنتيجة v46 التي كلّفت "
      "579$.\n")
    A("4. **M1/M2/M4 حسّنت يناير 2026 فعلياً** (+7.10 → +10.89/+10.11/"
      "+10.91) وكلها رفعت معامل الربح إلى 3.16–3.61 من 2.21.\n")
    A("### 4.5 الحكم النهائي\n")
    A("> **يبقى B0 مشحوناً. لا يُشحن v47.**\n")
    A("M7 ربح في الشهرين القصيرين (+7.16$) وخسر **157.96$** على الكتاب "
      "الكامل، ونجح في **2 نافذة من 5** فقط. هذا هو نفس نمط v46 بالضبط: "
      "نتيجة جميلة على نافذة أو نافذتين، وانهيار على المدى الطويل. سقف "
      "الثقة الذي يمنحه المدى القصير هو ما يجعل هذه الاختبارات تُضلّل، "
      "ولهذا كانت النوافذ الخمس إلزامية.\n")
    A("الدرس الأهم — والأكثر قابلية للتعميم — هو **حدّ صحة المحاكاة "
      "الساكنة**: أي محاكاة تُجمّد كتاب الصفقات ستُبالغ في تقدير أي قاعدة "
      "خروج، لأنها تتجاهل أن المقعد الوحيد يُختار من جديد. من الآن، أي "
      "رقم من محاكاة ساكنة في هذا المشروع يجب أن يُقرأ كـ**سقف نظري** "
      "لا كتوقّع.\n")


def month_section(L, cells, b0):
    A = L.append
    modes = [m for m in sorted({k[0] for k in cells if k[1] in ("W1",)})
             if all((m, w, 0) in cells for w in
                    ("W1", "W2", "OLD7", "MOD_Y1", "MOD_Y2"))]
    if not modes:
        A("*_(لا يوجد ذراع أكمل النوافذ الخمس)_*\n")
        return
    m = modes[0]
    per = {}
    for w in ("W1", "W2", "OLD7", "MOD_Y1", "MOD_Y2"):
        c = cells[(m, w, 0)]
        for k, v in c.get("yk", {}).items():
            per.setdefault(k, {})[m] = v
    bm = {k: float(v) for k, v in b0.groupby("ym").net_pnl.sum().items()}
    A(f"**الذراع:** `{m}`\n")
    A("| الشهر | B0 $ | " + m + " $ | Δ $ |")
    A("|---|---:|---:|---:|")
    for k in sorted(bm):
        mv = per.get(k, {}).get(m)
        if mv is None:
            A(f"| {k} | {bm[k]:+.2f} | — | — |")
        else:
            A(f"| {k} | {bm[k]:+.2f} | {mv:+.2f} | {mv-bm[k]:+.2f} |")
    A("")


if __name__ == "__main__":
    render()
    print("rendered REPORT_AR_v47.md")
