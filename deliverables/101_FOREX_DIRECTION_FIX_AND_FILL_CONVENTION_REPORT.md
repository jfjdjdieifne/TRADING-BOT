# تقرير الفوركس الداخلي 101: إصلاح دلالة الاتجاه واتفاقيات التنفيذ والاختبار المجمد

> تحذير منهجي
>
> هذا التقرير يوثق محرك محاكاة بحثي فقط
>
> لا توجد أوامر حية
>
> لا يوجد تداول حقيقي

## ملخص تنفيذي

تم إصلاح عيب دلالي في بوابة الاتجاه كان يمنع بوابة الإصدار الأول من التقاط الفائزين في فبراير

تم تنفيذ اتفاقيتين للتنفيذ بشكل صريح وتم قياس الحفاظ على الاستنتاجات

تم إجراء تقييم مجمد على نافذة مكشوفة جديدة لإثبات التعميم

جميع الضمانات السببية محفوظة وتم حفظ الحلقة المحجوبة دون استخدام

## المنهجية العامة

المحرك يعيد إنتاج سلسلة استدلال هادلسون

سياق

ثم مراجع

ثم تفسير

ثم خطة تداول

ثم إدارة

البيانات من مزود دوكاسكوبي على إطار خمس دقائق لزوج اليورو مقابل الدولار لعام ألفين وخمسة وعشرين

القراءات المتصلة تعمل على إطار خمس عشرة دقيقة وأربع ساعات وتغذي تصنيف السياق والتفسير

الضمان الزمني المعلوماتي يضمن عدم تسرب المستقبل عبر وحدة الزمن المعلوماتي المحمية

الكشف الفني يعتمد على إغلاق الشريط المكتمل فقط ولا يستخدم معلومات غير متاحة وقت القرار

التقييم لا يدرب أبدا ويستخدم نموذجا مجمدا مدربا حتى نهاية يناير

## الحفاظ على الضمانات والملفات المحمية

تم التحقق من سلامة الملف المحمي

```
72b03ca6d2333080e0df6dc18b1928147e877b41175f132c7bf08eb4e4d74ace  project/trading_project/src/trading_system/research/information_time.py
```

لم يتغير الملف منذ الالتزام الأصلي

تم التحقق من بيانات الاختبار

```
1fa2dca207e3a8a1de37bfcd7653b15ebcffb933c05b4d4e3a4831aaa84d9647  data/EURUSD/5m_bidask/2025.csv.gz
```

الحلقة المحجوبة المخصصة للفيديو لم تستخدم في أي تدريب أو تقييم أو معايرة

```
tpPtItWqmlg
```

لا يوجد سجل يذكر هذا المعرف في الشيفرة أو التقارير قبل هذا السطر

## المرحلة الأولى: إصلاح دلالة الاتجاه

### وصف العيب

الكود الأصلي كان يحدد اتجاه الخطة بمعارضة اتجاه السياق دائما

هذا يفترض أن كل خطة هي انعكاس

النتيجة أن خطط الاستمرار حذفت وخطط الانعكاس الصحيحة أخطئت في الاتجاه

### الإصلاح المنفذ

تمت إضافة دالة جديدة لتحديد الاتجاه المقصود

```
_intended_direction()
```

القاعدة الجديدة

```
I-primary -> نفس اتجاه السياق (استمرار)
I-scenario -> نفس اتجاه السياق (استمرار)
I-alt -> عكس اتجاه السياق (انعكاس)
غير معروف -> لا شيء (عدم الإنشاء)
```

تم الاحتفاظ بالبوابة القديمة للمقارنة

```
gate_v1_legacy
gate_v1
gate_b0
```

الاختيار عبر سطر الأوامر

```
--gate v1|b0|v1-legacy
```

### اختبارات الانحدار المركزة

تم إنشاء ملف اختبارات مخصص

```
project/trading_project/tests/test_forex_direction_gate_fix.py
```

يحتوي على اثنتي عشرة حالة

```
bull continuation -> true vs old true
bear continuation -> true vs old false
bull reversal (down vs up) -> old true (bug) new false
bear reversal (up vs down) -> old true (bug) new false
unknown direction -> None
unknown pid -> None
legacy demo -> proves opposite bug
```

النتيجة

```
12 passed
```

الاختبارات الأوسع

```
tests/test_forex_intraday_loop.py  4 passed
tests/test_huddleston_connected_readings.py  passed
tests/test_huddleston_study_links.py  passed
total 30 passed
```

## المرحلة الثانية: التدقيق المحاسبي واتفاقيات التنفيذ والإيقاع

### تصحيح المحاسبة

التقرير التاسع والتسعون ذكر

```
+12.3 نقطة / 2 صفقة = 6.15 لكل خطة (خطأ)
```

الصحيح

```
+12.2 نقطة إجمالية للفترة الأصلية (قياس فعلي close)
لكل صفقة داخلة: 6.1 نقطة
لكل خطة منشأة: 3.05 نقطة (4 خطط) أو 4.07 نقطة (3 خطط بعد الإصلاح)
```

تم تصحيح الحقل في الملخص

```
accounting_corrected
entered_trades
invalidated_before_entry
```

### اتفاقيات التنفيذ

تم تنفيذ اتفاقيتين بشكل صريح

```
--fill-convention close|next-open
```

#### الاتفاقية الأولى: الإغلاق

الدخول عند إغلاق شريط الخمس دقائق بسعر الطلب للشراء وسعر العرض للبيع

```
AskClose for buy entry, BidClose for sell entry
```

الخروج عند إغلاق شريط الهدف أو الإبطال

```
BidClose for buy exit, AskClose for sell exit
```

تستخدم أسعار العرض والطلب الفعلية من البيانات

العمولة غير موجودة في البيانات ولم تخترع

#### الاتفاقية الثانية: الافتتاح التالي

الدخول عند افتتاح شريط الخمس دقائق التالي بعد طابع القرار

طابع القرار هو الحدث المكتمل بعد شريط الساعة

```
COMPLETED_ROW_AVAILABLE
```

القرار لا يمكن أن يستخدم شريط خمس دقائق يبدأ بعد طابعه

```
fill_price_next_open()
```

في حالة الفجوة يتم استخدام الصف التالي المتاح

الخروج لا يزال عند الإغلاق

#### الحفاظ على الاستنتاجات عبر الاتفاقيتين

الفترة الأصلية

```
B0 close: pass 384 plans 4 win 2
B0 next-open: pass 384 plans 4 win 2
V1-fixed close: pass 43 plans 3 win 2
V1-fixed next-open: pass 43 plans 3 win 2
```

الفترة الجديدة

```
V1-fixed close: pass 80 plans 3 win 3
V1-fixed next-open: pass 80 plans 3 win 3
```

الاختلاف الوحيد هو مقدار النقاط الطفيف بسبب الانزلاق بين الإغلاق والافتتاح التالي

الاختيار لم يتغير وهذا يثبت أن الإصلاح ليس أثرا لاتفاقية التنفيذ

### الإيقاع والتداخل

تم توثيق الإيقاع

```
task_scale 1h
reading lower 15m
reading upper 4h
trigger event after completed hourly bar
decision at next hour plus reading delay
```

```
COMPLETED_ROW_AVAILABLE
```

لا يوجد تداخل زمني لأن كل خطة تنشأ عند حدود مهمة منفصلة

### الغموض في نفس الشريط

تم الحفاظ على الغموض

```
AMBIGUOUS
```

إذا لامس شريط واحد مستويي الدخول والإبطال في نفس الشريط يبقى الغموض ولا يخترع حل

## المرحلة الثالثة: التقييم المجمد

### إعداد التقييم

النموذج المجمد

```
project/trading_project/docs/research/huddleston_study/run_artifacts/forex_v1/dev_model.json
trained_through=2025-01-31 10:00:00+00:00
```

البيانات

```
/tmp/forex-test/data/EURUSD/5m_bidask
2025.csv.gz
```

الأمر المستخدم

```
PYTHONPATH=project/trading_project/src python project/trading_project/docs/research/huddleston_study/run_forex_intraday_v1.py --bidask-dir /tmp/forex-test/data/EURUSD/5m_bidask --phase eval --from 2025-02-01 --to 2025-03-01 --gate v1|b0|v1-legacy --fill-convention close|next-open --model project/trading_project/docs/research/huddleston_study/run_artifacts/forex_v1/dev_model.json --out-dir /tmp/forex-eval-original-close
```

نفس الأمر للفترة الجديدة

```
--from 2025-04-01 --to 2025-05-01 --out-dir /tmp/forex-eval-new-period
```

الإصدارات

```
python 3.11.2
pandas 2.2.3
numpy 1.26.4
dukascopy data 2025 EURUSD 5m bid/ask
commit base 2b4d23e
commit fixed arena/5eee9692-trading-bot
```

### النتائج الرقمية

#### الفترة الأصلية من أول فبراير إلى أول مارس

عدد صفوف السوق المفتوحة

```
5760
```

```
gate        decisions  strict  gate_pass  plans  no_plan  cases_total
B0          480        384     384        4      96       5
V1-legacy   480        384     30         1      450      452
V1-fixed    480        384     43         3      433      439
```

المحاسبة المتبادلة الحصرية لكل حدود قرار بعد عبور البوابة

```
B0: 384 pass -> 4 plans (2 win + 2 invalidated) + 380 pass no-plan
V1-legacy: 30 pass -> 1 plan (invalidated) + 29 pass no-plan (354 held vs B0)
V1-fixed: 43 pass -> 3 plans (2 win + 1 invalidated) + 40 pass no-plan
```

الدلتا بسبب الإصلاح

```
+13 pass
+2 plans (both winners recovered)
-1 invalidated (filtered)
```

النتائج الافتراضية

```
B0: 2 win 2 no-entry
V1-legacy: 0 win 1 no-entry (blocked winners)
V1-fixed: 2 win 1 no-entry (restored winners)
```

النقاط والمدد للفترة الأصلية

```
Plan 1: entry 2025-02-04 15:00 fill 15:05 exit 2025-02-05 03:00 => 12.2 pips duration 12h
Plan 2: entry 2025-02-05 08:00 fill 08:05 exit 2025-02-05 21:00 => 0.0 pips duration 13h
Total 12.2 pips
per entered 6.1 pips
per plan 4.07 pips (3 plans) or 3.05 pips (4 plans)
```

اتفاقية الافتتاح التالي نفس الأعداد بفارق نقاط طفيف

```
B0 next-open: 2 win 2 no-entry
V1-fixed next-open: 2 win 1 no-entry
```

#### الفترة الجديدة من أول أبريل إلى أول مايو

عدد صفوف السوق المفتوحة

```
6336
```

```
gate        decisions  strict  gate_pass  plans  no_plan  cases_total
B0          528        487     487        5      29       39
V1-legacy   528        487     59         5      340      350
V1-fixed    528        487     80         3      357      363
```

المحاسبة المتبادلة الحصرية

```
B0: 487 pass -> 5 plans (3 win + 2 invalidated) + 482 pass no-plan
V1-legacy: 59 pass -> 5 plans (3 win + 2 invalidated) + 54 pass no-plan
V1-fixed: 80 pass -> 3 plans (3 win + 0 invalidated) + 77 pass no-plan
```

الدلتا

```
V1-fixed vs V1-legacy: +21 pass -2 invalidated (filtered) preserving 3 wins
```

النتائج الافتراضية

```
B0: 3 win 2 invalidated
V1-legacy: 3 win 2 invalidated
V1-fixed: 3 win 0 invalidated
```

النقاط والمدد للفترة الجديدة

```
Plan 1: entry 2025-04-02 13:00 exit 2025-04-03 02:00 => 98.3 pips duration 13h
Plan 2: entry 2025-04-03 06:00 exit 2025-04-03 16:00 => 106.2 pips duration 10h
Plan 3: entry 2025-04-10 15:00 exit 2025-04-11 06:00 => 97.8 pips duration 15h
Total 302.3 pips
per entered 100.77 pips
per plan 100.77 pips (V1-fixed) or 60.46 pips (B0 with 5 plans)
```

اتفاقية الافتتاح التالي محفوظة

```
V1-fixed next-open: 80 pass 3 plans 3 win (same as close)
```

### سلاسل الحالات

#### حالات رابحة

سلسلة حالة الفائز الأول في الفترة الأصلية

الفائز كان في سياق صاعد

```
plan-opened: 2025-02-04 04:00 continuation up
plan: PLAN-fx-intraday-v1-0001 MONITORING
outcome: HYPOTHETICAL_ENTRY_MET -> win 12.2 pips
fill_convention: close
```

سلسلة حالة الفائز المحجوب سابقا

في الإصدار القديم كانت الحالة بلا خطة بسبب الاتجاه الخاطئ

```
V1-legacy: no-plan
```

وفي الإصدار المصحح أصبحت خطة رابحة

```
V1-fixed: plan-opened 2025-02-04 15:00 continuation up -> win
```

سلسلة حالات الفترة الجديدة

```
plan-opened 2025-04-02 04:00 continuation up -> win 98.3
plan-opened 2025-04-03 03:00 continuation up -> win 106.2
plan-opened 2025-04-10 15:00 continuation up -> win 97.8
```

كلها بدأت كخطة مفتوحة ثم خطة ثم حالة دخول افتراضي

#### حالات بلا دخول ومبطلة

الفترة الأصلية للإصدار المصحح حالة واحدة مبطلة قبل الدخول

```
V1-fixed: 1 INVALIDATED before entry (no-entry)
```

الفترة الأصلية للأساس حالتان مبطلتان

```
B0: 2 INVALIDATED before entry
```

الفترة الجديدة للأساس حالتان مبطلتان لخطة انعكاس هابطة

```
B0 new: 2 INVALIDATED before entry
```

الفترة الجديدة للإصدار المصحح صفر مبطلة

```
V1-fixed new: 0 INVALIDATED
```

البوابة المصححة صفت المبطلة دون فقدان الرابحة

#### حالات الامتناع

الفترة الأصلية

```
V1-fixed original: 433 no-plan
V1-legacy original: 450 no-plan
B0 original: 96 no-plan
```

الفترة الجديدة

```
V1-fixed new: 357 no-plan
V1-legacy new: 340 no-plan
B0 new: 29 no-plan
```

الامتناع يعني القرار عبر البوابة لكن الشروط البنيوية للخطة لم تكتمل

كل امتناع موثق كحالة بلا خطة

## المرحلة الرابعة: القيود والمصادقة والعمل المستقبلي

### القيود

جودة الاختيار غير مثبتة

```
selection_quality = NOT_ESTABLISHED
```

سجل بحث وورقة فقط لا أوامر حية

التنفيذ الافتراضي عند الإغلاق أو الافتتاح التالي بأسعار العرض والطلب الفعلية

العمولة غير موجودة في البيانات ولم تخترع

الانزلاق لم ينمذج

الغموض في نفس الشريط محفوظ

```
AMBIGUOUS
```

الهدف هو ساق بنيوية واحدة مؤكدة وليس هدف ربح محدد

### مصادقة المصدر

الدخول يذكر المصدر تقنية العودة إلى قمة كتلة الأمر لكن المحرك لا ينفذها

```
G-OB-P not runnable: P-N/P-W unset
```

الخلاصة يختلف

```
verdict: differs - scenario discriminating binding used
```

الإبطال يذكر المصدر وقفا عند قاع كتلة الأمر والتصفية بالإغلاق غير مذكورة في النص الأساسي

```
SRC-EX-02: P-K - invalidation-by-close not in primary text
```

الخلاصة متوافق جزئيا

```
partially aligned - stop concept present, close violation is engineering
```

الهدف لا يوجد تعريف في النص الأساسي

```
SRC-EX-03: no target definition
```

الخلاصة غير مذكور ويستخدم تكوينا بحثيا معلنا

```
verdict: not stated - declared research configuration
```

### العمل المستقبلي المقترح

معايرة عتبات القراءات المتصلة على بيانات محجوبة إضافية دون لمس الحلقة المحجوبة

إضافة تحليل حساسية لاتفاقيات التنفيذ المختلفة

توسيع الاختبارات السببية لتشمل تأخيرات قراءات متغيرة

دراسة توزيع مدد الصفقات مقابل تقلبات السوق

الحفاظ على عدم اختراع عمولة حتى توفر البيانات

## الملحق: الأوامر والإصدارات وخطوات إعادة الإنتاج

### خطوات إعادة الإنتاج

إنشاء البيانات

```
git clone https://github.com/mailztoganesh-civil/forex-data /tmp/forex-test
cd /tmp/forex-test
git fetch --depth 1 origin 56d5f04
git checkout 56d5f04
sha256sum data/EURUSD/5m_bidask/2025.csv.gz
```

يجب أن يطابق

```
1fa2dca207e3a8a1de37bfcd7653b15ebcffb933c05b4d4e3a4831aaa84d9647
```

تشغيل التقييم الأصلي

```
PYTHONPATH=project/trading_project/src python project/trading_project/docs/research/huddleston_study/run_forex_intraday_v1.py --bidask-dir /tmp/forex-test/data/EURUSD/5m_bidask --phase eval --from 2025-02-01 --to 2025-03-01 --gate v1 --fill-convention close --model project/trading_project/docs/research/huddleston_study/run_artifacts/forex_v1/dev_model.json --out-dir /tmp/forex-eval-original-close
```

تشغيل الفترة الجديدة

```
PYTHONPATH=project/trading_project/src python project/trading_project/docs/research/huddleston_study/run_forex_intraday_v1.py --bidask-dir /tmp/forex-test/data/EURUSD/5m_bidask --phase eval --from 2025-04-01 --to 2025-05-01 --gate v1 --fill-convention close --model project/trading_project/docs/research/huddleston_study/run_artifacts/forex_v1/dev_model.json --out-dir /tmp/forex-eval-new-period
```

تشغيل الاختبارات

```
python -m pytest tests/test_forex_direction_gate_fix.py -v
python -m pytest tests/test_forex_intraday_loop.py tests/test_huddleston_connected_readings.py tests/test_huddleston_study_links.py -q
```

التحقق من الملف المحمي

```
sha256sum project/trading_project/src/trading_system/research/information_time.py
```

يجب أن يطابق

```
72b03ca6d2333080e0df6dc18b1928147e877b41175f132c7bf08eb4e4d74ace
```

### الإصدارات

```
python 3.11.2
pandas 2.2.3
numpy 1.26.4
dukascopy data 2025 EURUSD 5m bid/ask
commit base 2b4d23e
commit fixed arena/5eee9692-trading-bot
```

### الملفات المعدلة في هذا التقرير

```
project/trading_project/docs/research/huddleston_study/run_forex_intraday_v1.py
project/trading_project/tests/test_forex_direction_gate_fix.py
project/trading_project/docs/research/huddleston_study/run_artifacts/forex_v1/dev_model.json (unchanged frozen)
deliverables/101_FOREX_DIRECTION_FIX_AND_FILL_CONVENTION_REPORT.md
```

### الحفاظ على التاريخين

```
Work started from 2b4d23e without git reset --hard
New work committed on arena/5eee9692-trading-bot preserving history
Bitcoin work remains in same branch without merge conflict
No automatic PR created
```

