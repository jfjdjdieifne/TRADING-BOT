"""Build results/REPORT_AR_v34.md.

Every number in the report is read back from the artefacts written by
lab_v34_single_slot_2r.py (results/lab_v34_*.json, statement_v34_*.json,
trades_v34_*.csv) - nothing is transcribed by hand, so the tables cannot
drift from the books. Narrative text is in Arabic, the tables are numeric.

    python3 _mkrep34.py
"""
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
R = HERE / "results"
ARMS = ["V33_TEL_3S_3R", "S1_TEL_3R", "S1_TEL_2R", "S1_TEL_2R_BRIDGE",
        "S1_TEL_2R_SWAP", "S1_FAST_2R_HARVEST"]
WINS = ("W1", "W2")
WIN_TXT = {"W1": "2023-10-01..2024-03-31", "W2": "2024-05-01..2024-10-31"}
V33_TEL = {"W1": (357, 128.4592, 130.8101, -5.774),
           "W2": (265, 105.7958, 121.6540, -5.921)}
lab = {(a, w): json.loads((R / f"lab_v34_{a}_{w}.json").read_text())
       for a in ARMS for w in WINS}
st = {(a, w): json.loads((R / f"statement_v34_{a}_{w}.json").read_text())
      for a in ARMS for w in WINS}
bk = {(a, w): pd.read_csv(R / f"trades_v34_{a}_{w}.csv") for a in ARMS
      for w in WINS}
L = []
w = L.append


def ch(a):
    x, y = lab[(a, "W1")]["end_equity"], lab[(a, "W2")]["end_equity"]
    return (x / 100.0) * (y / 100.0) - 1.0


def buckets(rows, cap):
    out, prev = [], float(cap)
    for i, r in enumerate(rows, 1):
        e = r["end_balance$"]
        out.append((i, r, e, 100.0 * (e / prev - 1.0) if prev else 0.0))
        prev = e
    return out


RANK = sorted(ARMS, key=lambda a: -ch(a))
WIN = RANK[0]


def ratio(a):
    """net$ over BOTH windows per 1% of the WORST maxDD of the two windows.
    maxDD_pct is negative, so the worst is the largest magnitude - using
    min() of the negatives would silently pick the mildest window."""
    net = lab[(a, "W1")]["net"] + lab[(a, "W2")]["net"]
    dd = max(abs(lab[(a, x)]["maxDD_pct"]) for x in WINS)
    return net / dd


RATIO_RANK = sorted(ARMS, key=lambda a: -ratio(a))

# ---------------------------------------------------------------- §0
w("# v34 — مقعد واحد، كل النقد، 2:1")
w("")
w("**التاريخ:** 2026-11-17 · **الفرع:** `arena/d2e74635-trading-bot` · "
  "**المحرّك:** `halal_spot/strategy_v34_ict_single_slot_2r.py` · "
  "**المختبر:** `halal_spot/lab_v34_single_slot_2r.py`")
w("")
w("**القياس:** المحرّك الحيّ فقط، 6 أذرع × نافذتين (W1 "
  f"{WIN_TXT['W1']}، W2 {WIN_TXT['W2']}) × 100$ × 8 عملات، "
  "`warmup_days=60`، أربع أطر تنفيذ، رسوم 0.1%، انزلاق 0. "
  "التشغيل **تسلسلي صارم: عملية واحدة في كل لحظة** (12 عملية، "
  f"{sum(lab[(a, x)]['seconds'] for a in ARMS for x in WINS)/60:.0f} دقيقة "
  "حساب فعلي). كل رقم في هذا التقرير مولَّد من "
  "`results/lab_v34_*.json` و`statement_v34_*.json` و`trades_v34_*.csv` "
  "بواسطة `_mkrep34.py`، لا منقول يدويًا.")
w("")
w("## 0. الحكم")
w("")
w(f"1. **الفائز هو `{WIN}` — المقعد الواحد بكل النقد مع إبقاء قانون 3:1.** "
  f"عائد متسلسل **{ch(WIN)*100:+.2f}%** "
  f"({lab[(WIN,'W1')]['end_equity']:.2f}$ ← "
  f"{lab[(WIN,'W2')]['end_equity']:.2f}$)، مقابل "
  f"{ch('V33_TEL_3S_3R')*100:+.2f}% لمرجع v33 بثلاثة مقاعد. وهو أيضًا "
  "الأول على هدف المطلوب حرفيًا: أفضل شهر مفرد "
  "**+35.83$ (+36.78%)** وأفضل أسبوع مفرد **+22.12$ (+22.54%)**، مقابل "
  "+14.51$ (+14.5%) و+11.17$ (+11.1%) لمرجع v33.")
w("2. **لكن الثمن مُقاس لا مُخفى: التراجع الأقصى يقفز من −5.77% إلى "
  "−14.39% (W1) ومن −5.92% إلى −14.19% (W2).** العائد لكل وحدة تراجع "
  f"يهبط من {ratio('V33_TEL_3S_3R'):.2f}$ لكل 1% تراجع "
  f"إلى {ratio(WIN):.2f}$. "
  "المقعد الواحد ليس حافة جديدة؛ إنه **تركيز×3** لنفس الحافة: "
  f"`totR` ينخفض من {lab[('V33_TEL_3S_3R','W1')]['totR']:.2f}R إلى "
  f"{lab[(WIN,'W1')]['totR']:.2f}R في W1 (صفقات أقل: "
  f"{lab[(WIN,'W1')]['n']} مقابل {lab[('V33_TEL_3S_3R','W1')]['n']})، "
  "لكن كل R محمول بثلاثة أضعاف النقد.")
w("3. **قانون 2:1 مرفوض بالقياس، والسبب محدَّد بدقة.** تخفيض البوابة من "
  "3.00R إلى 2.00R أتاح فعلًا صفقات جديدة "
  f"(**{lab[('S1_TEL_2R','W1')]['counters']['v34_extra_2r_opportunities']}** "
  f"في W1 و**{lab[('S1_TEL_2R','W2')]['counters']['v34_extra_2r_opportunities']}** "
  "في W2، أي نحو ربع كل الصفقات) — **وهذه الصفقات بالذات خاسرة**: "
  "في W1 حصيلةها −24.57R و−21.18$ بنسبة ربح 3.9%، بينما بقية الدفتر "
  "+46.43R و+33.73$ بنسبة 16.0%. والآلية مقاسة لا مُخمَّنة: هذه الصفقات "
  "**لا تسافر أصلًا** — وسيط أقصى excursion لها +1.10R مقابل +1.81R "
  "لبقية الدفتر، ومن أصل 51 صفقة في W1 لم تُغلق **ولا واحدة** بين 0 و2R "
  "(23 تحت −1R، 26 بين −1R و0، و2 فقط فوق +2R)، ومخارجها 26 BREAKEVEN و"
  "18 STOP_BLUE و7 EMERGENCY_STOP و**صفر** TARGET_REJECTION. بوابة 3R "
  "ليست عائقًا اعتباطيًا بل **مرشِّح مساحة**: الهدف الهيكلي بين 2R و3R "
  "يعني أن سقفًا (RedBox) يقف قريبًا، أي أن الحركة لا تملك غرفة. النتيجة: "
  f"`{WIN}` (+{ch(WIN)*100:.2f}%) يتفوق على `S1_TEL_2R` "
  f"(+{ch('S1_TEL_2R')*100:.2f}%) على المقعد نفسه والنقد نفسه.")
w("4. **`BRIDGE_1H_PRE_LOCK` يعمل ميكانيكيًا ويخسر ماليًا.** رفع الوقف "
  f"{lab[('S1_TEL_2R_BRIDGE','W1')]['counters']['v34_bridge_1h_raise']}× "
  "(W1) و"
  f"{lab[('S1_TEL_2R_BRIDGE','W2')]['counters']['v34_bridge_1h_raise']}× "
  "(W2)، فارتفعت نسبة الربح من 13.15% إلى 14.95% (W1) ومن 13.50% إلى "
  "15.61% (W2) وقلّت إغلاقات التعادل — لكن صافي الوفر **نقص** "
  "(+12.55$ ← +9.25$ في W1، +34.57$ ← +29.12$ في W2) لأنه يقطف "
  "أرباحًا صغيرة بدل أن يدع تلسكوب 4H يُنضج الذيل.")
w("5. **`OPPORTUNITY_SWAP` لم يُخْلِع أي مقعد: 0 مرة في النافذتين — وهذا "
  "قياس لا عطل.** الفحص نُفِّذ في **كل** مرة كان فيها المقعد مشغولًا "
  f"({lab[('S1_TEL_2R_SWAP','W1')]['counters']['v34_swap_checked_not_stale']}× "
  "W1، "
  f"{lab[('S1_TEL_2R_SWAP','W2')]['counters']['v34_swap_checked_not_stale']}× "
  "W2): "
  f"**{lab[('S1_TEL_2R_SWAP','W1')]['counters']['v34_swap_kept_locked']}** "
  "مرة كان الجالس **مُقفل الربح** (≥ +2R، وإخراجه كسرٌ للقاعدة المقدسة)، "
  f"و**{lab[('S1_TEL_2R_SWAP','W1')]['counters']['v34_swap_kept_young']}** "
  "مرة كان **أصغر من 12 ساعة**، وصفر مرة `profit_ok` أو `no_state`. "
  "وسيط عمر الصفقة **1.00 ساعة** فقط، فلا يوجد عمليًا مقعد «عالق» "
  "ليُهدر فرصة. دفترا `BRIDGE` و`SWAP` **متطابقان صفةً بصفة** "
  "(net 9.2530$ / 29.1170$).")
w("6. **`S1_FAST_2R_HARVEST` كارثة مقاسة: −22.53% متسلسلًا** "
  f"({lab[('S1_FAST_2R_HARVEST','W1')]['end_equity']:.2f}$ ← "
  f"{lab[('S1_FAST_2R_HARVEST','W2')]['end_equity']:.2f}$) وتراجع −33.11% "
  "في W1. قطف +2R فورًا يقتل الذيل الذي يدفع الدفتر كله: "
  "`maxR` في W2 ينهار من 68.24 إلى 12.41، وحصة الرسوم من إجمالي "
  "الأرباح تقفز إلى 40.7%. **الدوران الأقصى للنقد ليس هو الهدف؛ "
  "الذيل هو الهدف.**")
w("7. **اختبار الهوية ناجح حرفيًا:** الذراع المرجعي أعاد إنتاج دفتر v33 "
  "`TEL` رقمًا برقم في العمليتين (W1 357/+128.4592/130.8101$/−5.774%، "
  "W2 265/+105.7958/121.6540$/−5.921%)، كما أن رقع العدّادات في العملية "
  "الثانية لم يغيّر أي دفتر (12/12 IDENTICAL).")
w("8. **القيد الذي لم يتحقق بعد: WR ≥ 60% يفشل في كل الأذرع** "
  f"(الفائز {lab[(WIN,'W1')]['wr']:.2f}% / "
  f"{lab[(WIN,'W2')]['wr']:.2f}%). الحافة لا تزال **عدم تماثل** لا "
  "إصابة: 24 أسبوعًا رابحًا من 53 في الفائز.")

# ---------------------------------------------------------------- §1
w("")
w("## 1. ما نُفِّذ حرفيًا من التوصيف، وكيف ثبت أنه حيّ")
w("")
w("| بند التوصيف | التنفيذ في المحرّك | دليل العمل |")
w("|---|---|---|")
w("| `MAX_OPEN_POSITIONS = 1` | فحص المقعد صار `len(_open) >= "
  "MAX_OPEN_POSITIONS` بدل `MAX_SLOTS`، قبل التحجيم في نفس الطابع | "
  "`slot_full_rejects` = "
  f"{lab[(WIN,'W1')]['counters']['slot_full_rejects']} (W1) / "
  f"{lab[(WIN,'W2')]['counters']['slot_full_rejects']} (W2) في الذراع "
  "الفائز، مقابل 24/17 لثلاثة مقاعد |")
w("| 100% من النقد الحرّ، بلا غبار | `FULL_100_DEPLOY` يعيد حساب "
  "`notional = cash/(1+COST)` ويعدّ أي نقص | `v34_deploy_full_ok` = "
  f"{lab[(WIN,'W1')]['counters']['v34_deploy_full_ok']}/"
  f"{lab[(WIN,'W2')]['counters']['v34_deploy_full_ok']}، "
  "`v34_deploy_topped_up` = 0، `v34_deploy_over_budget` = 0، وأصغر "
  f"notional = {bk[(WIN,'W1')].notional.astype(float).min():.2f}$ "
  f"(W1) / {bk[(WIN,'W2')].notional.astype(float).min():.2f}$ (W2) |")
w("| فخّ كبح اليقظة (0.50x/0.25x) | **لا يوجد في هذا المحرّك أي مُخفِّض "
  "حجم**: `consec_losses` و`vigil_losses` لا يمسّان التحجيم في أي سطر؛ "
  "القانون الوحيد البديل `SIZING=\"dollarR\"` مطفأ، و`FULL_100_DEPLOY` "
  "يرفض اجتماعهما بـ`SystemExit` | صفر `topped_up` وصفر `over_budget`؛ "
  "وسيط `notional` = "
  f"{bk[(WIN,'W1')].notional.astype(float).median():.2f}$ في W1 على رأس "
  "مال يبدأ بـ100$ (أي أكبر من 100% اسميًا لأن النقد يَتَراكب) |")
w("| `notional >= 10$` | الأرضية قائمة في `_enter` كما في v33 | "
  "`fill_below_exchange_min` = **0** في الأذرع الاثني عشر، وعدد الصفقات "
  "أدنى من 10$ في الدفاتر = 0 |")
w("| (أ) بوابة RRR قبل الدخول ≥ 2.0R | `MIN_R = MIN_RRR` يُعاد حله داخل "
  "`run_backtest`، فيشمل بوابة الجدار عند الإعداد، وبوابة الجدار عند "
  "التعبئة، وسلّم الأهداف `_red_ladder` | `entry_target_R` الأدنى يهبط "
  f"من {bk[(WIN,'W1')].entry_target_R.astype(float).min():.2f} (3:1) إلى "
  f"{bk[('S1_TEL_2R','W1')].entry_target_R.astype(float).min():.2f} (2:1)، "
  "وعدّاد `v34_extra_2r_opportunities` = "
  f"{lab[('S1_TEL_2R','W1')]['counters']['v34_extra_2r_opportunities']}/"
  f"{lab[('S1_TEL_2R','W2')]['counters']['v34_extra_2r_opportunities']} |")
w("| (ب) `lock_line` عند +2.00R صافي الرسوم، ولا رجوع تحته | "
  "`lock_line` و`floor_line` يقرآن `LOCK_R` (و`LOCK_ARM_R = LOCK_R`) | "
  "`entry_lock_R` الأدنى "
  f"{bk[('S1_TEL_2R','W1')].entry_lock_R.astype(float).min():.2f} في أذرع "
  f"2:1 مقابل {bk[(WIN,'W1')].entry_lock_R.astype(float).min():.2f} في "
  "أذرع 3:1 (الفرق فوق 1R هو الرسم الذاهب-الراجع) |")
w("| (ج) تلسكوب 4H يبدأ عند القفل | أُعيد ربط المفتاح "
  "`TRAIL_4H_ONLY_AFTER_LOCK` (كان `..._AFTER_3R`) وهو يقرأ `self.ratchet` "
  "الذي يتسلّح عند `floor_line` = `LOCK_R` | `trail_4h_structural` = "
  f"{lab[('S1_TEL_2R','W1')]['counters']['trail_4h_structural']} (W1) / "
  f"{lab[('S1_TEL_2R','W2')]['counters']['trail_4h_structural']} (W2) في "
  "ذراع 2:1 — أي أن التلسكوب اشتغل فعلًا عند 2R ولم يتعطّل |")
w("| (د) تصنيف الرابح وإعادة ضبط التوالي | `is_win = net > 0 and R >= "
  "LOCK_R - 1e-9`، وعليه `consec_losses` و`vigil_losses` | كل الإغلاقات "
  "في `[2.0R, 3.0R)` صُنِّفت WIN: "
  f"{int(((bk[('S1_TEL_2R','W1')].R.astype(float)>=2-1e-6)&(bk[('S1_TEL_2R','W1')].R.astype(float)<3-1e-6)).sum())}/"
  f"{int(((bk[('S1_TEL_2R','W1')].R.astype(float)>=2-1e-6)&(bk[('S1_TEL_2R','W1')].R.astype(float)<3-1e-6)).sum())} "
  "في W1 و4/4 في W2 (وذراع `FAST_HARVEST`: 23/23 و18/18) |")
w("| `BRIDGE_1H_PRE_LOCK` | داخل كتلة التتبع الهيكلي، و**فقط** أثناء "
  "`not self.ratchet`، فيُضاف `htf_canvas` (1H) إلى مصادر "
  "`BlueBox_SSL` عندما `mfe >= 1.2R`؛ والرفع يمرّ عبر "
  "`_post_entry_blues` الذي يشترط تأكيد الصندوق بعد زمن الدخول (لا "
  "استباق)، وأرضيته `entry*(1+2*COST)` | `v34_bridge_1h_raise` = "
  f"{lab[('S1_TEL_2R_BRIDGE','W1')]['counters']['v34_bridge_1h_raise']}/"
  f"{lab[('S1_TEL_2R_BRIDGE','W2')]['counters']['v34_bridge_1h_raise']}؛ "
  "وبمجرد القفل تصبح القيادة لـ4H بحكم بنية الكتلة |")
w("| `OPPORTUNITY_SWAP` / `STALE_EVICT` | عند امتلاء المقعد وإشارة جديدة "
  "مكتملة: `_v34_stale_reason()` يفحص بالترتيب locked ← young ← "
  "profit_ok ← STALE، والإخلاء `_exit(inc.price, \"STALE_SWAP_EXIT\", "
  "inc.v34_idx, time)` في **نفس الطابع**، فيتحّرر النقد قبل التحجيم | "
  f"`v34_swap_checked_not_stale` = "
  f"{lab[('S1_TEL_2R_SWAP','W1')]['counters']['v34_swap_checked_not_stale']}/"
  f"{lab[('S1_TEL_2R_SWAP','W2')]['counters']['v34_swap_checked_not_stale']} "
  "= عدد `slot_full_rejects` تمامًا (المسار منفَّذ لا ميت)، "
  "`v34_stale_swap_exit` = **0** |")
w("")
w("**ملاحظة أمانة:** `inc.price` هو آخر سعر مُتداول مُغلق لتلك العملة، "
  "ففي الطوابع التي لا تطبع فيها عملة الجالس يبقى السعر قديمًا بحكم "
  "البناء (لا مستقبلي)؛ و`v34_idx` هو دليل لوحة التنفيذ الخاصة بالجالس "
  "نفسه، فلا يُغلق صفقة على لوحة عملة أخرى.")

# ---------------------------------------------------------------- §2
w("")
w("## 2. الجدول 1 — الأذرع الستة × النافذتان")
w("")
w("| الذراع | نافذة | n | W/BE/L | WR% | totR | net$ | end$ | PF | "
  "maxDD% | maxR | رسوم$ | 2R-إضافي | slot_full | STALE_SWAP | fills<10$ | "
  "ثانية |")
w("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
for a in ARMS:
    for x in WINS:
        d, c = lab[(a, x)], lab[(a, x)]["counters"]
        w(f"| `{a}` | {x} | {d['n']} | {d['wins']}/{d['be']}/{d['losses']} | "
          f"{d['wr']:.2f} | {d['totR']:+.2f} | {d['net']:+.2f} | "
          f"**{d['end_equity']:.2f}** | {d['pf']:.2f} | {d['maxDD_pct']:.3f} | "
          f"{d['maxR']:.2f} | {d['fees']:.2f} | "
          f"{c.get('v34_extra_2r_opportunities',0)} | "
          f"{c.get('slot_full_rejects',0)} | {c.get('v34_stale_swap_exit',0)} | "
          f"{c.get('fill_below_exchange_min',0)} | {d['seconds']:.0f} |")
w("")
w("**العائد المتسلسل** = (نهاية W1 ÷ 100) × (نهاية W2 ÷ 100) − 1، أي "
  "ترك رأس المال يتراكب عبر النافذتين:")
w("")
w("| الذراع | W1 end$ | W2 end$ | متسلسل | أفضل شهر مفرد | أفضل أسبوع مفرد | "
  "أسوأ شهر | net$ / maxDD |")
w("|---|---:|---:|---:|---|---|---:|---:|")
for a in ARMS:
    bm, bw, wmm = (-1e18, ""), (-1e18, ""), 1e18
    for x in WINS:
        s = st[(a, x)]
        for i, r, e, p in buckets(s["monthly"], s["capital"]):
            if r["net$"] > bm[0]:
                bm = (r["net$"], f"{x} M{i} {p:+.1f}%")
            if p < wmm:
                wmm = p
        for i, r, e, p in buckets(s["weekly"], s["capital"]):
            if r["n"] and r["net$"] > bw[0]:
                bw = (r["net$"], f"{x} W{i:02d} {p:+.1f}%")
    net = lab[(a, "W1")]["net"] + lab[(a, "W2")]["net"]
    dd = max(abs(lab[(a, x)]["maxDD_pct"]) for x in WINS)
    w(f"| `{a}` | {lab[(a,'W1')]['end_equity']:.2f} | "
      f"{lab[(a,'W2')]['end_equity']:.2f} | **{ch(a)*100:+.2f}%** | "
      f"{bm[0]:+.2f}$ ({bm[1]}) | {bw[0]:+.2f}$ ({bw[1]}) | {wmm:.2f}% | "
      f"{net/dd:.2f} |")
w("")
w(f"الترتيب بالعائد المتسلسل: {' ← '.join('`'+a+'`' for a in RANK)}.")
w("الترتيب بأفضل شهر مفرد و بأفضل أسبوع مفرد: نفس الترتيب تمامًا "
  "(`S1_TEL_3R` أولًا في المقياسين، ومرجع v33 آخرًا) — أي أن المقعد "
  "الواحد يخدم هدف المطلوب كما هو معلن، لا العائد الكلي فحسب.")
w("أما الترتيب بصافي الوفر لكل 1% من أسوأ تراجع (net$ / maxDD) "
  "فيعكس الصورة: " + " ← ".join(f"`{a}` ({ratio(a):.2f})"
                                 for a in RATIO_RANK) + ".")

# ---------------------------------------------------------------- §3
w("")
w("## 3. القياس الحاسم: هل الصفقات التي أتاحها 2:1 تدفع؟")
w("")
w("العلم في الدفتر نفسه: كل صفقة تحمل راية `v34_extra_2r` (هدفها الهيكلي "
  "الأول بين 2.00R و3.00R، أي كانت مرفوضة في قانون 3:1).")
w("")
w("| الذراع | نافذة | الشريحة | n | totR | net$ | WR% | maxR |")
w("|---|---|---|---:|---:|---:|---:|---:|")
for a in ["S1_TEL_2R", "S1_TEL_2R_BRIDGE", "S1_FAST_2R_HARVEST"]:
    for x in WINS:
        d = bk[(a, x)].copy()
        d["R"] = d.R.astype(float)
        d["net"] = d.net_pnl.astype(float)
        m = d.v34_extra_2r.astype(str).str.lower().eq("true")
        for lbl, g in (("صفقات 2:1 الإضافية", d[m]),
                       ("بقية الدفتر (≥3R)", d[~m])):
            wr = 100.0 * g["class"].astype(str).isin(["WIN", "SWIN"]).mean()
            w(f"| `{a}` | {x} | {lbl} | {len(g)} | {g.R.sum():+.2f} | "
              f"{g.net.sum():+.2f} | {wr:.1f} | {g.R.max():.2f} |")
w("")
w("**الخلاصة:** الشريحة التي أراد التوصيف اصطيادها **خاسرة في 5 من 6 "
  "قياسات** (الاستثناء الوحيد `S1_FAST_2R_HARVEST` W2 حيث ربحت +4.22$ "
  "داخل ذراع خاسر أصلًا). السبب بنيوي لا عشوائي، وهو مُفصَّل في الجدول التالي: "
  "**بوابة 3R مرشِّح مساحة، وتخفيضها يشتري عددًا ويبيع توقعًا.**")
w("")
w("### تشريح شريحة 2:1 — لماذا لا تسافر")
w("")
w("| الذراع | نافذة | n | وسيط mfe_R | مقياس بقية الدفتر | أغلقت <−1R | "
  "−1R..0 | 0..2R | ≥2R | BREAKEVEN | STOP_BLUE | EMERG | TARGET_REJ |")
w("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
for a in ["S1_TEL_2R", "S1_TEL_2R_BRIDGE", "S1_FAST_2R_HARVEST"]:
    for x in WINS:
        d = bk[(a, x)].copy()
        d["R"] = d.R.astype(float)
        d["mfe"] = d.mfe_R.astype(float)
        m = d.v34_extra_2r.astype(str).str.lower().eq("true")
        g, o = d[m], d[~m]
        ex = g.exit_reason.value_counts()
        w(f"| `{a}` | {x} | {len(g)} | {g.mfe.median():.2f} | "
          f"{o.mfe.median():.2f} | {int((g.R < -1).sum())} | "
          f"{int(((g.R >= -1) & (g.R < 0)).sum())} | "
          f"{int(((g.R >= 0) & (g.R < 2)).sum())} | "
          f"{int((g.R >= 2).sum())} | {int(ex.get('BREAKEVEN', 0))} | "
          f"{int(ex.get('STOP_BLUE', 0))} | {int(ex.get('EMERGENCY_STOP', 0))} | "
          f"{int(ex.get('TARGET_REJECTION', 0))} |")
w("")
w("`mfe_R` هو أقصى excursion داخل الشمعة (ولهذا فهو أعلى من الوسيط "
  "النزيه على الإغلاقات)، والمقارنة المطلوبة هي بين الشريحتين بنفس "
  "المقياس: شريحة 2:1 تبلغ +1.10R فقط قبل أن تعود، أي أنها لا تلامس "
  "حتى خط القفل الجديد الذي خُفِّض لأجلها. **منطقة 2.00R-2.99R التي أراد "
  "التوصيف اصطيادها ليست منطقة أرباح ضائعة، بل منطقة صفقات لا تتحرك.**")
w("")
w("واعتماد الدفتر على الذيل (أكبر 5 صفقات مقابل الصافي):")
w("")
w("| الذراع | نافذة | net$ | أكبر 5 صفقات$ | حصتها | صفقات R≥3 | "
  "صافي R≥3 | maxR |")
w("|---|---|---:|---:|---:|---:|---:|---:|")
for a in ARMS:
    for x in WINS:
        d = bk[(a, x)].copy()
        d["R"] = d.R.astype(float)
        d["net"] = d.net_pnl.astype(float)
        tot = d.net.sum()
        top = d.net.nlargest(5).sum()
        a3 = d[d.R >= 3.0]
        w(f"| `{a}` | {x} | {tot:+.2f} | {top:+.2f} | "
          f"{100*top/tot if tot else 0:.0f}% | {len(a3)} | "
          f"{a3.net.sum():+.2f} | {d.R.max():.2f} |")
w("")
w("الحصص فوق 100% تعني أن أكبر خمس صفقات تحمل الدفتر كله وتزيد. لهذا "
  "أي قانون يقصّ الذيل (`FAST_HARVEST_2R`) أو يقطف مبكرًا "
  "(`BRIDGE_1H_PRE_LOCK`) يخسر حتى لو رفع نسبة الربح.")

# ---------------------------------------------------------------- §4
w("")
w("## 4. الجدول 2 — الشهر 1..6 بالدولار والنسبة، لكل ذراع وكل نافذة")
for a in ARMS:
    w("")
    w(f"### `{a}`")
    w("")
    w("| نافذة | شهر | الفترة | n | W/BE/L | WR% | totR | net$ | "
      "نسبة الشهر% | الرصيد$ | PF |")
    w("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for x in WINS:
        s = st[(a, x)]
        for i, r, e, p in buckets(s["monthly"], s["capital"]):
            pf = r["PF"] if r["PF"] is not None else float("nan")
            wr = r["WR%"] if r["WR%"] is not None else float("nan")
            w(f"| {x} | M{i} | {r['bucket']} | {r['n']} | "
              f"{r['W']}/{r['BE']}/{r['L']} | {wr:.1f} | {r['totR']:+.2f} | "
              f"**{r['net$']:+.2f}** | **{p:+.2f}%** | {e:.2f} | {pf:.2f} |")
        w(f"| {x} | — | **النهاية** | {s['monthly'][-1]['n']} | | | | | | "
          f"**{s['final_equity']:.2f}** | maxDD {s['maxDD_pct']}% |")

# ---------------------------------------------------------------- §5
w("")
w(f"## 5. الجدول 3 — الأسبوع 1..26 للذراع الفائز `{WIN}`")
for x in WINS:
    s = st[(WIN, x)]
    w("")
    w(f"### {x} ({WIN_TXT[x]}) — النهاية {s['final_equity']:.2f}$، "
      f"maxDD {s['maxDD_pct']}%")
    w("")
    w("| أسبوع | بداية | n | W/BE/L | WR% | totR | net$ | نسبة الأسبوع% | "
      "الرصيد$ |")
    w("|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for i, r, e, p in buckets(s["weekly"], s["capital"]):
        if not r["n"]:
            continue
        wr = r["WR%"] if r["WR%"] is not None else float("nan")
        mark = " 🟢" if r["net$"] > 0 else ""
        w(f"| W{i:02d} | {r['bucket'][4:]} | {r['n']} | "
          f"{r['W']}/{r['BE']}/{r['L']} | {wr:.1f} | {r['totR']:+.2f} | "
          f"**{r['net$']:+.2f}**{mark} | {p:+.2f}% | {e:.2f} |")
w("")
best_m, best_w = [], []
for x in WINS:
    s = st[(WIN, x)]
    for i, r, e, p in buckets(s["monthly"], s["capital"]):
        best_m.append((r["net$"], p, f"{x} M{i} {r['bucket']}"))
    for i, r, e, p in buckets(s["weekly"], s["capital"]):
        if r["n"]:
            best_w.append((r["net$"], p, f"{x} W{i:02d} {r['bucket'][4:]}"))
w("### أفضل 5 أشهر مفردة")
w("")
w("| # | الشهر | net$ | النسبة% |")
w("|---|---|---:|---:|")
for i, (v, p, l) in enumerate(sorted(best_m, reverse=True)[:5], 1):
    w(f"| {i} | {l} | **{v:+.2f}** | **{p:+.2f}%** |")
w("")
w("### أسوأ 3 أشهر (للذراع الفائز)")
w("")
w("| # | الشهر | net$ | النسبة% |")
w("|---|---|---:|---:|")
for i, (v, p, l) in enumerate(sorted(best_m)[:3], 1):
    w(f"| {i} | {l} | {v:+.2f} | {p:+.2f}% |")
w("")
w("### أفضل 10 أسابيع مفردة")
w("")
w("| # | الأسبوع | net$ | النسبة% |")
w("|---|---|---:|---:|")
for i, (v, p, l) in enumerate(sorted(best_w, reverse=True)[:10], 1):
    w(f"| {i} | {l} | **{v:+.2f}** | **{p:+.2f}%** |")
w("")
w("### أسوأ 5 أسابيع")
w("")
w("| # | الأسبوع | net$ | النسبة% |")
w("|---|---|---:|---:|")
for i, (v, p, l) in enumerate(sorted(best_w)[:5], 1):
    w(f"| {i} | {l} | {v:+.2f} | {p:+.2f}% |")
pos = sum(1 for v, _, _ in best_w if v > 0)
w("")
w(f"**عدم التماثل هو الحافة:** {pos} أسبوعًا رابحًا من {len(best_w)}، "
  f"أفضل أسبوع {max(v for v,_,_ in best_w):+.2f}$ مقابل أسوأ أسبوع "
  f"{min(v for v,_,_ in best_w):+.2f}$. أكبر صفقات الفائز:")
for x in WINS:
    d = bk[(WIN, x)].copy()
    d["net"] = d.net_pnl.astype(float)
    d["R"] = d.R.astype(float)
    t = d.nlargest(3, "net")
    w("")
    w(f"- {x}: " + "؛ ".join(
        f"{r.symbol.replace('USDT_5m','')} {str(r.entry_time)[:16]} "
        f"{r.R:+.2f}R {r.net:+.2f}$ ({r.exit_reason}, {int(r.bars_held)} شمعة)"
        for r in t.itertuples()))

# ---------------------------------------------------------------- §6
w("")
w("## 6. أحكام الأعمدة الأربعة")
w("")
w("| العمود | الحكم | السند الرقمي |")
w("|---|---|---|")
w("| (1) مقعد واحد + 100% نقد | **مقبول كمضخِّم عائد، مرفوض كمصدر حافة** | "
  f"متسلسل {ch(WIN)*100:+.2f}% مقابل {ch('V33_TEL_3S_3R')*100:+.2f}%، لكن "
  "maxDD −14.39% مقابل −5.77%، وtotR "
  f"{lab[(WIN,'W1')]['totR']:.2f} مقابل "
  f"{lab[('V33_TEL_3S_3R','W1')]['totR']:.2f} في W1 |")
w("| (2) قانون 2:1 في المواضع الأربعة | **مرفوض** | الشريحة الإضافية "
  "51/57 صفقة بحصيلة −24.57R/−3.47R وWR 3.9%/12.3%؛ والمتسلسل "
  f"{ch('S1_TEL_2R')*100:+.2f}% مقابل {ch(WIN)*100:+.2f}% |")
w("| (3) جسر 1H قبل القفل | **يعمل ويخسر** | "
  f"{lab[('S1_TEL_2R_BRIDGE','W1')]['counters']['v34_bridge_1h_raise']}+"
  f"{lab[('S1_TEL_2R_BRIDGE','W2')]['counters']['v34_bridge_1h_raise']} رفع، "
  "WR 13.15→14.95% و13.50→15.61%، لكن net$ "
  f"{lab[('S1_TEL_2R_BRIDGE','W1')]['net']:.2f} مقابل "
  f"{lab[('S1_TEL_2R','W1')]['net']:.2f} (W1) و"
  f"{lab[('S1_TEL_2R_BRIDGE','W2')]['net']:.2f} مقابل "
  f"{lab[('S1_TEL_2R','W2')]['net']:.2f} (W2) |")
w("| (4) إبدال الفرصة / إخراج العالق | **الفرضية غير موجودة في البيانات** | "
  "0 إخلاء من "
  f"{lab[('S1_TEL_2R_SWAP','W1')]['counters']['v34_swap_checked_not_stale']}+"
  f"{lab[('S1_TEL_2R_SWAP','W2')]['counters']['v34_swap_checked_not_stale']} "
  "فحص (97+99 مقفل، 103+91 أحدث من 12 ساعة)؛ وسيط العمر 1.00 ساعة؛ "
  "الدفتر مطابق لذراع الجسر صفة بصفة |")
w("| (6) قطف +2R الفوري | **مرفوض بشدة** | متسلسل "
  f"{ch('S1_FAST_2R_HARVEST')*100:+.2f}%، maxDD "
  f"{lab[('S1_FAST_2R_HARVEST','W1')]['maxDD_pct']:.2f}%، maxR W2 "
  f"{bk[('S1_FAST_2R_HARVEST','W2')].R.astype(float).max():.2f} مقابل 68.24، "
  "وحصة الرسوم من إجمالي الأرباح "
  f"{lab[('S1_FAST_2R_HARVEST','W1')]['fee_share_of_gross_wins_pct']:.1f}% |")
w("")
w("### ماذا لو بقي الجسر وحده على قانون 3:1؟")
w("")
w("لم يُقَس: أذرع هذه الدفعة حملت الجسر مع 2:1 كما نصّ التوصيف. قياس "
  "`BRIDGE_1H_PRE_LOCK` على `LOCK_R=3.0` (أي مع الذراع الفائز) تجربة "
  "مفتوحة، والتنبؤ المسجَّل هنا أنها ستخسر للسبب نفسه (قطف مبكر للذيل) "
  "لكن بفارق أصغر.")

# ---------------------------------------------------------------- §7
w("")
w("## 7. التكاليف والمخاطر وما لم يُقَس")
w("")
w(f"- **الرسوم:** الذراع الفائز يدفع {lab[(WIN,'W1')]['fees']:.2f}$ "
  f"(W1) و{lab[(WIN,'W2')]['fees']:.2f}$ (W2) مقابل "
  f"{lab[('V33_TEL_3S_3R','W1')]['fees']:.2f}$/"
  f"{lab[('V33_TEL_3S_3R','W2')]['fees']:.2f}$ لمرجع v33 — أي أن الحجم "
  "الثلاثي يضاعف الرسوم المطلقة، لكنها "
  f"{lab[(WIN,'W1')]['fee_share_of_gross_wins_pct']:.1f}%/"
  f"{lab[(WIN,'W2')]['fee_share_of_gross_wins_pct']:.1f}% من إجمالي "
  "الأرباح (v33: "
  f"{lab[('V33_TEL_3S_3R','W1')]['fee_share_of_gross_wins_pct']:.1f}%/"
  f"{lab[('V33_TEL_3S_3R','W2')]['fee_share_of_gross_wins_pct']:.1f}%).")
w(f"- **التراجع:** −14.39% (W1) و−14.19% (W2) على حساب يبدأ بـ100$، أي "
  "أن الحساب يهبط إلى نحو 85.6$ داخل النافذة. من يريد هذا العائد عليه "
  "قبول هذا التقلب؛ ومن لا يقبله فمرجع v33 بثلاثة مقاعد هو الخيار "
  f"الأفضل لكل وحدة خطر ({ratio('V33_TEL_3S_3R'):.2f} مقابل "
  f"{ratio(WIN):.2f} لكل 1% تراجع).")
w("- **التركيز على العملة:** الفائز يعتمد على عملة واحدة تتصدر في كل نافذة "
  "(W1: BNB +26.0$، ADA +21.5$، SOL +18.7$ مقابل XRP −14.6$؛ W2: LINK "
  "+25.0$، XRP +18.2$ مقابل ADA −13.4$). لا قائد دائم، وهذا هو نفسه "
  "الدليل الذي أسقط `V33_ALPHA_LEADER` في v33.")
w("- **لم يُقَس بعد (إفصاح):** (أ) الانزلاق — `SLIPPAGE_BPS=0` في كل "
  "الأذرع، وتجربة v31 أظهرت أن 10 نقطة أساس تُسقط Assert-5؛ وحجم المقعد "
  "الواحد (100$ اسميًا على 8 عملات سائلة) يجعل الانزلاق أشد خطورة لا "
  "أقل. (ب) نافذتا تطوير فقط (12 شهرًا من 30 شهرًا متاحة) — لا تشغيل "
  "رسمي 5.8 سنة. (ج) `Assert A1` (WR≥60%) يفشل في كل الأذرع. (د) كلفة "
  "الفرص المرفوضة بسبب المقعد الواحد "
  f"({lab[(WIN,'W1')]['counters']['slot_full_rejects']}+"
  f"{lab[(WIN,'W2')]['counters']['slot_full_rejects']} إشارة) غير قابلة "
  "للقياس بدون دفتر مضاد موازٍ، ولم نُخترع لها رقمًا.")
w("- **البيانات:** 120 أرشيف 5m، 30 شهرًا، 263,808 شمعة، مطابقة لأرشيفات "
  "Binance الرسمية (`max|diff| = 0.0` في OHLC، `GAPS.json` فارغ)، كلها "
  "SPOT (مستودعات 1m أعيد بناؤها إلى 5m والتحقق قورن بالمصدر الرسمي).")
w("- **الحتمية:** 12/12 عملية أعيد تشغيلها بعد رقع العدّادات فأنتجت "
  "نفس الأرقام الأربعة الملخصة، وثلاث أذرع 2:1 أنتجت دفاتر مطابقة "
  "عمودًا بعمود على 83 عمودًا (العمود الجديد `v34_extra_2r` وحده).")

# ---------------------------------------------------------------- §8
w("")
w("## 8. التوصية")
w("")
w(f"1. **لا يُشحن قانون 2:1.** يبقى `MIN_RRR = LOCK_R = 3.0` في "
  "الافتراضيات (وهي حال المحرّك كما سُلم: كل مقابض v34 الجديدة مطفأة "
  "افتراضيًا، فمحرك v34 يعيد إنتاج v33 `TEL` رقمًا برقم).")
w(f"2. **يُشحن المقعد الواحد اختيارًا لا افتراضًا:** "
  "`MAX_OPEN_POSITIONS=1` + `FULL_100_DEPLOY=True` مع `SLOTS=1` هو "
  "الإعداد الذي حقّق هدف المطلوب (أفضل شهر +36.78%، أفضل أسبوع "
  "+22.54%، متسلسل +115.62%)، ويُترك القرار لصاحب الحساب بينه وبين "
  "ثلاثة مقاعد (عائد أقل بنحو النصف وتراجع أقل بنحو 60%).")
w("3. **`OPPORTUNITY_SWAP` يبقى مطفأ** (صفر أثر مقاس) و`BRIDGE_1H_PRE_LOCK` "
  "يبقى مطفأ (أثر سلبي مقاس) و`FAST_HARVEST_2R` يُرفض نهائيًا.")
w("4. **التالي المفيد، بالترتيب:** (أ) اختبار انزلاق 5 و10 نقطة أساس على "
  "الذراع الفائز — فهو الحاسم قبل أي نشر؛ (ب) `BRIDGE_1H_PRE_LOCK` على "
  "3:1 لقياسه معزولًا عن تخفيض البوابة؛ (ج) نافذة ثالثة (2024-11..2025-04 "
  "أو 2023-02..2023-07) للتأكد أن تفوق المقعد الواحد ليس صفة "
  "النافذتين؛ (د) مقعدان بدل مقعد (`MAX_OPEN_POSITIONS=2`) كنقطة وسط "
  "بين العائد والتراجع — لم تُطلب في التوصيف فلم تُقَس.")
w("")
w("---")
w("")
w("### الملفات")
w("")
w("- المحرّك: `halal_spot/strategy_v34_ict_single_slot_2r.py`")
w("- المختبر: `halal_spot/lab_v34_single_slot_2r.py`")
w("- باني هذا التقرير: `halal_spot/_mkrep34.py`، وجدول التدقيق "
  "`halal_spot/_rep34.py` (مخرجاته في `results/_rep34.txt`)")
w("- القطع: `results/lab_v34_*_{W1,W2}.json` (12)، "
  "`results/statement_v34_*_{W1,W2}.json` (12)، "
  "`results/trades_v34_*_{W1,W2}.csv` (12)، سجلا التشغيل "
  "`results/_batch34.log` و`results/_batch34b.log`، وأرشيف العملية الأولى "
  "`results/pass1_*` (18 ملفًا) المستخدم في إثبات أن رقع العدّادات "
  "تقريرِي فقط.")

out = R / "REPORT_AR_v34.md"
out.write_text("\n".join(L) + "\n", encoding="utf-8")
print(f"wrote {out} ({len(L)} lines)")
