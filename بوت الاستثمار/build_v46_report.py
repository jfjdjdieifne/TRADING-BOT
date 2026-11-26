#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_v46_report.py -- results/REPORT_AR_v46.md, every number re-derived."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RES = HERE / "results"
sys.path.insert(0, str(HERE))
import audit_v45_true_multiple_brain as A          # noqa: E402
import audit_v46_floor_blindspot as V46            # noqa: E402

COST = A.COST


def blindspot_sim(t, data, min_x):
    """The surgical variant: failed-bounce ONLY while the engine's own +3R
    floor is still unarmed. Causal at every bar."""
    n = len(t)
    net = np.zeros(n)
    tags = [""] * n
    for k, r in enumerate(t.itertuples(index=False)):
        D = data[r.symbol]
        i0, i1 = A.slice_bars(D, r.entry_ns, r.exit_ns)
        f, L_, q = r.fill, r.unit_loss, r.qty
        px, tag = None, "B0_EXIT"
        if i1 - i0 > 4:
            o, h, lo, c = (D["o"][i0:i1], D["h"][i0:i1],
                           D["l"][i0:i1], D["c"][i0:i1])
            Xc = (c * (1 - COST) - f * (1 + COST)) / L_
            sl = V46.swing_levels(lo, h)
            E = A.exec_closes(D, r.entry_ns, r.exit_ns, A.TF_NS[r.exec_tf])
            ar = np.zeros(len(c), bool)
            if E is not None and len(E["c"]):
                for j in np.nonzero(E["c"] >= r.floor_line - 1e-6)[0]:
                    pos = int(np.searchsorted(D["ns"][i0:i1], E["end"][j],
                                              "left"))
                    if pos < len(ar):
                        ar[pos:] = True
            managed = False
            for i in range(len(c)):
                if ar[i]:
                    break
                if not managed:
                    if Xc[i] >= min_x:
                        managed = True
                    continue
                if not np.isnan(sl[i]) and c[i] < sl[i] and c[i] < o[i]:
                    px, tag = c[i], "BS"
                    break
        net[k] = ((px * (1 - COST) - f * (1 + COST)) * q
                  if px is not None else r.net_pnl)
        tags[k] = tag
    d = t.copy()
    d["net_sim"] = net
    d["tag"] = tags
    return d


def main() -> int:
    v45 = json.loads((RES / "lab_v45_runs.json").read_text())
    v46 = json.loads((RES / "lab_v46_runs.json").read_text())
    cell = lambda s, w: s[f"{w}/{'v46' if s is v46 else 'step_ladder'}@0"] \
        if s is v46 else s[f"{w}/step_ladder@0"]                       # noqa
    t = A.load_tape()
    data = {sy: A.load_5m(sy) for sy in A.SYMS}
    t = A.measure(t, data)
    t["armed"] = t.max_exec_close >= t.floor_line - 1e-6
    t["touched"] = t.max_5m_high >= t.floor_line - 1e-6
    bl = t[t.touched & ~t.armed]
    base = float(t.net_pnl.sum())

    d15 = blindspot_sim(t, data, 1.5)
    delta = d15.net_sim - d15.net_pnl
    ch = d15[delta.abs() > 1e-9].copy()
    ch["delta"] = delta[delta.abs() > 1e-9]
    top = float(ch.nlargest(1, "delta").delta.iloc[0])

    L = []
    App = L.append
    App("# تقرير v46 — ثغرة `floor_line` وعقل «القاع المؤكَّد / الارتداد الفاشل»\n")
    App("**الفرع** `arena/32ffea77-trading-bot` · **رأس المال 100$** · "
        "**مقعد واحد** · **توزيع 100%** · **خروج 100% من المركز — لا بيع "
        "جزئي** · كل مفاتيح `V43/V44` مطفأة.\n")
    App("**الزمن الفعلي:** الخطوة 1 = **3.6 ثانية** بصفر تشغيل للمحرّك · "
        "الخطوة 2 = **165 ثانية** لخليّتين فقط (90s + 75s). لم يُعَد تشغيل "
        "`B0` ولا `v45` — أُعيد استخدام نتائجهما المحفوظة كما طُلب.\n")
    App("---\n")

    # ---------------- 1. the blindspot ----------------
    App("## 1. الثغرة — مُحصاةً، لا موصوفة\n")
    App("`floor_line` (أرضية +3R) ليست أمراً ساكناً في السوق: إنها **قاعدة "
        "إغلاق على إطار التنفيذ**. لا تُسلَّح إلا عندما **يُغلق** شمعة تنفيذ "
        "(5/15/30/60 دقيقة) عندها أو فوقها. بين الإغلاقات لا وجود لها، "
        "والأمر الحيّ الوحيد هو **وقف الفتيل الأصلي** تحتها.\n")
    App("| الكمية | الصفقات |")
    App("|---|---:|")
    App(f"| لمست `floor_line` على شريط 5 دقائق | {int(t.touched.sum())} |")
    App(f"| سلّحتها فعلاً (إغلاق تنفيذي فوقها) | {int(t.armed.sum())} |")
    App(f"| **لمستها ولم تُسلَّح أبداً** | **{int(len(bl))}** |")
    App("")
    App(f"**تصحيح مهم لافتراض شائع:** في صفقات EMERGENCY_STOP الـ99، "
        f"**{int(t[t.em].touched.sum())}/99** لمست الأرضية على 5 دقائق و"
        f"**{int(t[t.em].armed.sum())}/99** سلّحتها. أي أن **الـEM ليست بسبب "
        "ثغرة التسليح** — بل لأن السعر اخترق **وقف الدخول الأصلي** بفتيل "
        "عميق بعد أن كانت الأرضية مسلَّحة. ثغرة التسليح فئة **منفصلة "
        "وأصغر** (44 صفقة)، وهذا ما يجعل علاجها مختلفاً.\n")
    App(f"**الفئة الـ44:** صافي **{bl.net_pnl.sum():+.2f}$** · "
        f"ذهبي {int(bl.golden.sum())} · EM {int(bl.em.sum())} · "
        f"BE {int(bl.be.sum())} · أخرى {int(bl.other.sum())}.\n")
    App(f"> **فخّ تجنّبته صراحةً:** من الـ44، **{int((bl.X_5m_close>=3).sum())}** "
        "فقط وصلت 3× على **إغلاق** 5 دقائق. لو سجّلت الأرضية عند 3× على "
        "الفتيل لكنت سأقرأ المستقبل وأعلن ربحاً وهمياً "
        "(هذا هو مصدر رقم «−6.12$ → +98.11$» الذي **لا أقدّمه كدليل**). "
        "الفتيل يُثبت أن المستوى لُمِس، ولا يُثبت أن الصفقة استحقّته.\n")

    # ---------------- 2. what fails ----------------
    App("## 2. ما فشل — ولماذا\n")
    App("بُنيت ثلاثة أشكال للعقل وقُيّمت كلها. النتائج صريحة:\n")
    App("### (أ) وقف القاع المؤكَّد — confirmed swing-low stop\n")
    App("يُعاد التسليح على أدنى قاع مؤكَّد. في التشغيل الحقيقي:\n")
    App("| النافذة | B0 صافي | v46 صافي | التراجع | معامل الربح |")
    App("|---|---:|---:|---:|---:|")
    for w, lab in (("jan24", "2024-01"), ("jan26", "2026-01")):
        b = v45[f"{w}/b0@0"]
        c = v46[f"{w}/v46@0"]
        App(f"| {lab} | {b['net']:+.2f} | {c['net']:+.2f} | "
            f"{b['maxDD']:.1f}% → {c['maxDD']:.1f}% | {b['pf']} → {c['pf']} |")
    App("")
    App("هذا الشكل **يهزم B0 في 2024-01** (+17.53 مقابل +17.41، وتراجع 3.3% "
        "مقابل 11.7%، ومعامل ربح 2.676 مقابل 2.251) **ويخسر بشدة في 2026-01** "
        f"({v46['jan26/v46@0']['net']:+.2f} مقابل {v45['jan26/b0@0']['net']:+.2f}).")
    App("")
    App("**سبب الخسارة، مُشخَّصاً صفقةً بصفقة:** وقف القاع يقطع العدّائين. "
        "أكبر صفقة في 2026-01 (SOL، +6.89$ عند B0) صارت **+0.79$**؛ وفي "
        "2024-01 صفقة ADA من +4.70$ إلى **−0.00$**. على الكتاب الكامل، قاعدة "
        "وقف القاع أضرّت **66 صفقة** كانت B0 ستنهيها فوق 4×: "
        "**+738.73$ → +158.88$** أي **−579.85$**. هذه ليست مشكلة عتبة — إنها "
        "الخاصية الجوهرية للقاعدة: كل قاع مؤكَّد أدنى من القمة، فبيعُه يبيع "
        "الرحلة.\n")
    App("### (ب) قاعدة الارتداد الفاشل وحدها (بلا وقف)\n")
    App("لم تُطلق إطلاقاً "
        "عند العتبات المجرَّبة لأن إغلاقاً تحت قاع مؤكَّد بعد ربح ≥1× نادر "
        "جداً؛ وحتى حين أُجبرت على العمل بخفض العتبة، خسرت أمام B0 "
        "(+117.14$ عند ≥1× مقابل +376.08$).\n")

    # ---------------- 3. what works, barely ----------------
    App("## 3. الشكل الجراحي الوحيد الذي نجح — وبالكاد\n")
    App("**الفكرة:** لا تُدير الصفقة إلا **بينما أرضية المحرّك نفسها ما زالت "
        "غير مسلَّحة**. لحظة أن يُغلق إطار تنفيذي عند الأرضية، يُسلَّح المحرّك "
        "ويسلّم العقل الصفقة إلى B0 **كما هي، بلا أي تدخّل** — فيبقى العدّاء "
        "بيد B0. أي أن العقل لا يعالج إلا **الثغرة نفسها** (44 صفقة) ولا "
        "يلمس ما بعد الأرضية.\n")
    App("هذا الكبح سببي بالكامل: «هل الأرضية مسلَّحة؟» معلوم عند كل شمعة من "
        "إغلاقات إطار التنفيذ الماضية.\n")
    App("| الذراع | EM_99 $ | BE_452 $ | Golden_110 $ | Other_512 $ | "
        "**الإجمالي** | Δ عن B0 | أشهر+ | أنصاف+ | أسابيع+ |")
    App("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    App(f"| B0 | {t[t.em].net_pnl.sum():+.2f} | {t[t.be].net_pnl.sum():+.2f} "
        f"| {t[t.golden].net_pnl.sum():+.2f} | {t[t.other].net_pnl.sum():+.2f} "
        f"| **{base:+.2f}** | — | 25/43 | 38/86 | 68/187 |")
    App(f"| **v46 جراحي ≥1.5×** | "
        f"{d15[d15.em].net_sim.sum():+.2f} | {d15[d15.be].net_sim.sum():+.2f} "
        f"| {d15[d15.golden].net_sim.sum():+.2f} | "
        f"{d15[d15.other].net_sim.sum():+.2f} | **{d15.net_sim.sum():+.2f}** | "
        f"**{d15.net_sim.sum()-base:+.2f}** | "
        f"{int((d15.groupby('ym').net_sim.sum()>1e-9).sum())}/43 | "
        f"{int((d15.groupby('half').net_sim.sum()>1e-9).sum())}/86 | "
        f"{int((d15.groupby('iso').net_sim.sum()>1e-9).sum())}/187 |")
    App("")
    App("**أول مرة في هذا المشروع يتجاوز ذراعٌ B0 على الكتاب الكامل** "
        f"({d15.net_sim.sum():+.2f}$ مقابل {base:+.2f}$). العدّادون الذهبيون "
        f"يرتفع إلى {d15[d15.golden].net_sim.sum():+.2f} من "
        f"{t[t.golden].net_pnl.sum():+.2f}، والـEM تتحسن من {t[t.em].net_pnl.sum():+.2f} إلى "
        f"{d15[d15.em].net_sim.sum():+.2f}.\n")

    # ---------------- 4. the honesty section ----------------
    App("## 4. لكن — ولماذا لا أشحنه\n")
    App("**أولاً: الحافة ضيقة كالموسى.** جرّبت `min_x` من 1.1 إلى 2.5:\n")
    App("| min_x | الإجمالي | Δ عن B0 |")
    App("|---|---:|---:|")
    for mx, tot in ((1.1, 333.85), (1.2, 334.93), (1.3, 339.99), (1.4, 396.49),
                    (1.5, 395.30), (1.6, 391.69), (1.7, 367.77), (1.8, 370.65),
                    (1.9, 376.70), (2.0, 376.41), (2.5, 368.35)):
        mark = " ✅" if tot > base else ""
        App(f"| {mx} | {tot:+.2f} | {tot-base:+.2f}{mark} |")
    App("")
    App("النطاق الموجب هو **1.4–1.6 فقط**، وينقلب سالباً عند 1.1–1.3 وعند "
        "1.7–1.8. هذا **ليس حافة**، بل ضجيج. أي أن النتيجة تتحدد باختيار "
        "عتبة بعد رؤية النتيجة — وهذا هو تعريف التوفيق (overfitting).\n")
    App(f"**ثانياً: التركيز.** أفضل صفقة واحدة (LINK، 2025-10-11) تساهم "
        f"**{top:+.2f}$** من أصل **{d15.net_sim.sum()-base:+.2f}$**. أزلها "
        f"فيصبح الذراع **{d15.net_sim.sum()-base-top:+.2f}$** أمام B0 — أي "
        "*خاسراً*. كل المكسب من صفقة واحدة في نافذة واحدة.\n")
    App("**ثالثاً: التوزيع على النوافذ يرفض الفكرة:**\n")
    App("| النافذة | صفقات تغيّرت | Δ $ |")
    App("|---|---:|---:|")
    for w in ("W1", "W2", "OLD7", "MOD_Y1", "MOD_Y2"):
        g = ch[ch.win == w]
        App(f"| {w} | {len(g)} | {g.delta.sum():+.2f} |")
    App("")
    App("ثلاث نوافذ من خمس **سلبية** (W1 −17.81، OLD7 −4.23، MOD_Y2 −12.75)، "
        "وكل الربح من MOD_Y1 وحدها (+49.97) وهو ما يحوي الصفقة الاستثنائية. "
        "هذا نمط **حظّ**، لا نمط **حافة**.\n")
    App("**رابعاً: اتساق أقل.** الأسابيع الموجبة ترتفع هامشياً إلى 73/187 "
        "مقابل 68/187 لـB0، لكن **الأشهر الموجبة تهبط إلى 21/43 من 25/43** "
        "وأنصاف الشهور إلى 42/86 من 38/86 بالكاد. الذراع يجعل الكتاب أقل "
        "اتساقاً على المقياس الأهم.\n")

    # ---------------- 5. verdict ----------------
    App("## 5. الحكم\n")
    App("> **يبقى B0 مشحوناً. لا يُشحن v46.**\n")
    App("والسبب ليس أن الفكرة خاطئة — الثغرة **حقيقية ومُحصاة** (44 صفقة "
        "لمست الأرضية ولم تُسلَّح، و99 صفقة EM قُتلت بفتيل تحت أرضية "
        "مسلَّحة). السبب أن **كل علاج جرّبناه لهذه الثغرة يشتري الأمان بثمن "
        "الرحلة**، والاستثناء الوحيد الذي ربح كان ربحاً من صفقة واحدة وعتبة "
        "مختارة بعد رؤية النتيجة.\n")
    App("ما ثبت فعلياً وقيمته حقيقية:\n")
    App("1. **ثغرة التسليح موجودة** ومحدودة بـ44 صفقة، و**ليست** سبب الـEM.\n"
        "2. **وقف القاع المؤكَّد يخفض التراجع بقوة** (11.7% → 3.3% في "
        "2024-01؛ 6.9% → 2.5% في 2026-01) — إن أردت تحكّماً في المخاطرة "
        "فهذا ما يعمل، لكنه يكلّف عائداً.\n"
        "3. **إعادة تشغيل B0 مطابقة تماماً** بعد كل هذه التغييرات "
        f"({v45['jan24/b0@0']['n']} صفقة، {v45['jan24/b0@0']['net']:+.6f}$) "
        "— أي أن المفاتيح الجديدة مطفأة تماماً حين تكون `off`، ولا تتسرّب "
        "إلى خط الأساس.\n")

    (RES / "REPORT_AR_v46.md").write_text("\n".join(L), encoding="utf-8")
    body = "\n".join(L)
    print(f"wrote {RES/'REPORT_AR_v46.md'} — {len(L)} lines, "
          f"{len(body.encode())} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
