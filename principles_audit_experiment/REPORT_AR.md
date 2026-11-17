# تقرير تدقيق مبادئ V8 وتجارب مستقلة

## القرار التنفيذي

- **لم يتم تعديل أي ملف أساسي**. بقي `smc_v4_multisleeve_package/exports/quantconnect/V8_3Asset_1PosEach_QC.py` كما هو، وبقي محرك الحزمة كما هو.
- بقيت V8 الأصلية هي النسخة المرجعية، ولم يتم استبدالها أو اختيار مرشح تلقائياً.
- جُرّبت الإزالات/التعديلات في طبقة بحث مستقلة فقط. أفضل نتيجة استكشافية كانت إزالة **BTC BE@3R فقط** مع إبقاء بوابة `09:00 UTC`، لكنها ليست دليلاً كافياً للترقية: الاختبار استخدم نفس الفترة التاريخية، وجرى اكتشاف المرشح بعد النظر إلى holdout، ولا توجد بعد walk-forward أو QC live-fill confirmation.
- النتيجة العامة: **بعض فلاتر V8 تبدو مفيدة خارج العينة، لكن هذا لا يثبت robustness بمفرده**. لا توجد توصية بتعديل المصدر الأساسي الآن.

## نطاق التجربة وقابلية إعادة الإنتاج

الفترة هي `2020-02-01 00:00 UTC` إلى `2026-11-01 00:00 UTC`، مع:

- تدريب: `2020-02-01 .. 2022-12-31`.
- holdout: `2023-01-01 .. 2026-10-31`.
- نافذة أحدث: `2025-01-01 .. 2026-10-31`.
- بيانات XAU وNSX الدقيقة وBTC ذات 5 دقائق الموجودة محلياً.
- التكاليف المرجعية: XAU `0.25`، NSX `2.0` نقطة، BTC `0.08%` round-trip.
- `1x` هو cost المضمّن في الصفقة، `2x` ضعف التكلفة، و`3x_stress` ثلاثة أضعافها. هذه إعادة تسعير للتكلفة فقط؛ لا تضيف spread أو slippage أو partial fills حقيقية.

هاش المصدر المجمد:

```text
V8_3Asset_1PosEach_QC.py  ebeda99ca3707edae7c07b298e56af2d1d302858973fc7e8be51a506f5928256
smc_v4_portfolio.py       bec70ed41027dfcc29e8766d2645d4ef734b998dd7347533e314a5eb658517f0
smc_core.py               5230730d8e4afee7d2f8409f8ba0b88ec81d2c6fa36eaa8463c1a9073d0ac155
```

الملف `V8_3Asset_1PosEach_QC_PRINCIPLES_CANDIDATE.py` الموجود هنا snapshot بحثي مطابق للهاش أعلاه، وليس نسخة معدلة من المصدر.

> المحرك المحلي يعيد بناء مكونات V8، لكنه ليس تشغيل QuantConnect حرفياً. لذلك المقارنة الرقمية الداخلية صالحة بين نسخ المحرك نفسه، ولا تعادل ضمان تنفيذ QC.

## تعريفات الإشارات كما ينفذها المصدر

هذه ليست أحكاماً بأن كل التعريفات خاطئة؛ هي تفكيك لما يفعله الكود فعلياً:

1. **Swing:** `CausalSwingTracker(k)` لا يعلن pivot إلا بعد إغلاق `k` شموع لاحقة؛ هذه نقطة سببية صحيحة.
2. **Sweep:** عند مستوى high نشط، يلزم `high > level` مع `close < level`؛ وعند low يلزم `low < level` مع `close > level`. المرشح يستخدم extreme شمعة السويب كقاعدة للوقف، وليس مستوى السيولة الأصلي فقط.
3. **CHoCH/BOS:** شرط الدخول هو إغلاق الشمعة الحالية بعد آخر swing مؤكد (`close > last_high` أو `close < last_low`). لا يوجد فصل صريح دائماً بين “كسر استمرار” BOS و“تغير حالة” CHoCH؛ لذلك بعض التسميات أقوى من التعريف البرمجي الفعلي.
4. **FVG:** الفجوة الثلاثية هي `b3.low - b1.high` للشراء أو `b1.low - b3.high` للبيع، مع شرط displacement على `b2`. الإشارة تُبنى على شموع مكتملة، والـlimit لا يُفترض أنه امتلأ داخل الشمعة التي كوّنته.
5. **HTF:** حالة 4H/1H/1D مبنية من شموع مكتملة وبإتاحة زمنية causal في المحرك المحلي. هذا جيد من حيث المبدأ، لكن يجب فصل ذلك عن fill model في QC.

## نتائج V8 والـablations

### 1. المقارنة الكاملة والـholdout عند 1x

| النسخة | الفترة | N | Net R | PF | MaxDD R | t | سنوات موجبة |
|---|---|---:|---:|---:|---:|---:|---:|
| V8 الحالية | full | 1321 | 515.75 | 1.570 | 26.06 | 5.22 | 7/7 |
| V8 الحالية | holdout | 799 | 278.35 | 1.504 | 26.06 | 3.70 | 4/4 |
| إزالة XAU 13–14 UTC | full | 1363 | 501.07 | 1.534 | 29.52 | 5.05 | 7/7 |
| إزالة XAU 13–14 UTC | holdout | 823 | 258.15 | 1.449 | 25.07 | 3.41 | 4/4 |
| إزالة NSX 09:00 UTC | full | 1341 | 505.51 | 1.546 | 27.44 | 5.08 | 7/7 |
| إزالة NSX 09:00 UTC | holdout | 811 | 276.62 | 1.491 | 27.10 | 3.64 | 4/4 |
| إزالة NSX 1D gate | full | 1516 | 509.06 | 1.493 | 32.59 | 5.03 | 7/7 |
| إزالة NSX 1D gate | holdout | 921 | 276.96 | 1.435 | 32.59 | 3.54 | 4/4 |
| إزالة BTC 09h فقط | full | 1377 | 500.60 | 1.523 | 31.90 | 4.94 | 7/7 |
| إزالة BTC 09h فقط | holdout | 840 | 268.89 | 1.453 | 31.90 | 3.42 | 4/4 |
| إزالة BTC BE فقط | full | 1310 | 533.55 | 1.579 | 28.17 | 5.18 | 7/7 |
| إزالة BTC BE فقط | holdout | 790 | 304.06 | 1.539 | 19.27 | 3.76 | 4/4 |
| إزالة فلاتر الوقت/النظام كلها | full | 1414 | 494.91 | 1.487 | 34.67 | 4.64 | 7/7 |
| إزالة فلاتر الوقت/النظام كلها | holdout | 856 | 280.92 | 1.446 | 25.87 | 3.31 | 4/4 |

قراءة الجدول:

- إزالة XAU filter تضر Net وPF في holdout؛ انخفاض DD وحده لا يكفي.
- إزالة NSX 09h أو بوابة 1D لا تحسن Net في holdout، وتزيد DD أو تخفض PF.
- إزالة BTC 09h فقط تضر بوضوح.
- إزالة BTC BE فقط هي المرشح الوحيد الذي تحسن في هذه العينة: `+25.71R` في holdout، و`PF +0.035`، و`MaxDD -6.79R`. لكنه تراجع في التدريب (`229.49R` مقابل `237.40R`) ورفع full MaxDD (`28.17R` مقابل `26.06R`). لذلك هو **مرشح بحثي مشروط** وليس ترقية مثبتة.
- النسخة التي تزيل BTC 09h وBE معاً (`V8_no_BTC_09h_BE`) بدت جيدة في holdout، لكن split one-change-at-a-time يبين أن معظم الإشارة الإيجابية تأتي من إزالة BE، لا من إزالة بوابة الساعة.

### 2. تكلفة المرشح الأفضل مقابل V8 الأصلية

| النسخة | الفترة | التكلفة | N | Net R | PF | MaxDD R | t |
|---|---|---|---:|---:|---:|---:|---:|
| V8 الحالية | full | 1x | 1321 | 515.75 | 1.570 | 26.06 | 5.22 |
| V8 الحالية | full | 2x | 1321 | 459.16 | 1.487 | 29.90 | 4.65 |
| V8 الحالية | full | 3x stress | 1321 | 402.57 | 1.411 | 35.13 | 4.07 |
| إزالة BTC BE فقط | full | 1x | 1310 | 533.55 | 1.579 | 28.17 | 5.18 |
| إزالة BTC BE فقط | full | 2x | 1310 | 477.76 | 1.498 | 32.79 | 4.64 |
| إزالة BTC BE فقط | full | 3x stress | 1310 | 421.97 | 1.423 | 37.97 | 4.09 |
| V8 الحالية | holdout | 1x | 799 | 278.35 | 1.504 | 26.06 | 3.70 |
| V8 الحالية | holdout | 2x | 799 | 245.14 | 1.427 | 28.34 | 3.26 |
| V8 الحالية | holdout | 3x stress | 799 | 211.92 | 1.355 | 30.75 | 2.81 |
| إزالة BTC BE فقط | holdout | 1x | 790 | 304.06 | 1.539 | 19.27 | 3.76 |
| إزالة BTC BE فقط | holdout | 2x | 790 | 271.55 | 1.462 | 20.57 | 3.36 |
| إزالة BTC BE فقط | holdout | 3x stress | 790 | 239.04 | 1.391 | 23.70 | 2.96 |

المرشح لا ينهار عند 2x أو 3x في هذه إعادة التسعير، لكن ذلك لا يثبت slippage robustness؛ التكاليف مضروبة فقط مع بقاء نفس fills.

### 3. سبب تحسن BTC BE-only

في holdout، مكوّن BTC:

| النسخة | N | Net R | PF | MaxDD R | WR |
|---|---:|---:|---:|---:|---:|
| V8 الحالية | 92 | 44.65 | 1.672 | 11.82 | 32.61% |
| إزالة BE فقط | 83 | 70.35 | 1.895 | 15.42 | 12.05% |
| إزالة 09h فقط | 133 | 35.18 | 1.327 | 25.59 | 25.56% |

النتيجة تأتي من السماح لبعض الصفقات الرابحة الكبيرة بالاستمرار؛ وهي ليست دليلاً على أن “حماية BE” فكرة سيئة دائماً. يلزم اختبار walk-forward مع تعريف ثابت للتنفيذ، لأن هذه النتيجة حساسة لمسار trailing، وترتيب لمس stop/target، وتوقيت الفل fill.

## اختبار السببية وprefix invariance

أُجري replay على prefixes مقطوعة عند `2022-01-01` و`2023-01-01` و`2025-01-01`، وقورنت فقط الصفقات المكتملة التي كان خروجها قبل القطع:

| النسخة | cutoff | الصفقات المتوقعة | المرصودة | exact match |
|---|---|---:|---:|---|
| V8 current | 2022-01-01 | 337 | 337 | نعم |
| V8 current | 2023-01-01 | 521 | 521 | نعم |
| V8 current | 2025-01-01 | 957 | 957 | نعم |
| BTC no-BE candidate | 2022-01-01 | 28 | 28 | نعم |
| BTC no-BE candidate | 2023-01-01 | 40 | 40 | نعم |
| BTC no-BE candidate | 2025-01-01 | 88 | 88 | نعم |

لكن الاختبار كشف مشكلة مستقلة في **المحرك المرجعي المحلي**: دوال محاكاة EOD كانت تهيئ `exit_idx=entry_idx` عند عدم وجود خروج قبل نهاية prefix. أدى ذلك في الاختبار الأول إلى صفقتي BTC زائفتين بعد `2021-12-03`. لم نعدّل المحرك؛ أضيف wrapper runtime-only داخل harness ينقل EOD إلى آخر bar معروف ويحافظ على المركز مشغولاً حتى حدود prefix. بعد هذا التصحيح الحسابي، تطابقت prefixes أعلاه.

هذا يثبت سببية replay للمحرك المحلي بعد تصحيح boundary bookkeeping، ولا يثبت وحده تطابق QuantConnect Order Events أو broker fills.

## تجربة ATR وDST المستقلة على matched engine

هذه تجربة أصغر (`LTF_control`) وليست V8 QC حرفياً:

| النسخة | N full | Net full | PF full | DD full | N holdout | Net holdout | PF holdout | DD holdout | latest Net |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ATR الحالي + UTC ثابت | 349 | 132.91 | 1.411 | 40.16 | 188 | 50.83 | 1.288 | 25.64 | 15.56 |
| ATR السابق فقط | 357 | 139.86 | 1.422 | 39.19 | 198 | 55.82 | 1.300 | 25.45 | 17.63 |
| DST-aware فقط | 323 | 123.24 | 1.412 | 35.09 | 173 | 41.01 | 1.253 | 34.30 | -1.36 |
| DST-aware + ATR السابق | 327 | 134.27 | 1.443 | 34.11 | 179 | 50.06 | 1.298 | 33.20 | -0.32 |

التحسن الصغير من ATR السابق غير كافٍ، وتجربة DST-aware ساءت في holdout/latest ضمن هذا المحرك. لا يتم اقتراح أي من التعديلين للمصدر.

## مشكلات تنفيذية/مبدئية يجب ألا تُخفى خلف PF

### أولوية عالية

1. **TP قد لا يعاد حسابه بعد توسيع SL.** في `_submit_entry`، يتم حساب/تمرير `tp` قبل `_floor_sl`، ثم قد يوسع `_floor_sl` مسافة الوقف، بينما يبقى `tp` القديم. هذا يغير RR المخطط فعلياً، خصوصاً BTC fixed `15R`. الحل المرشح في طبقة مستقلة هو تمرير RR وإعادة حساب TP بعد final rounded SL، ثم اختبار ذلك one-change-at-a-time.
2. **الأوامر ليست OCO صريحاً.** يتم إرسال stop وlimit منفصلين بعد fill. `on_order_event` يلغي الأوامر الأخرى عند وصول event، لكن السباق بين stop/target، partial fills، أو stale quote لا يمثل OCO broker مضموناً. يجب قياس سيناريو لمس الاثنين على نفس bar محافظاً للـstop.
3. **الـPython reference كان يحتوي خطأ EOD boundary.** لا ينبغي استخدامه كحكم سببية قبل تطبيق wrapper/إصلاح مستقل مشابه في نسخة بحثية.
4. **تقدير الكمية ليس حداً لمخاطرة المحفظة.** `_effective_risk_pct` يحسب مخاطرة الصفقة، ثم `_clamp_qty` يستخدم `margin_remaining * leverage * 0.85`. مع `1PosEach` يمكن أن توجد ثلاث مراكز، ولا يوجد cap واضح لمجموع R المفتوح؛ leverage 50/25 قد يضخم التعرض رغم أن كل صفقة تبدو “1%/1.5%”.

### أولوية متوسطة

5. **DST/session:** المصدر مضبوط على UTC. `_in_kz` يستخدم نافذتي `07–11` و`12–17` UTC، وXAU يمنع `13–14` UTC. إذا كان المقصود London/NY local clock، تتغير النوافذ موسمياً؛ NY cash-open ليس 13–14 UTC طوال العام، وLondon ليست 07 UTC طوال العام.
6. **NSX regime overlap:** بوابة AMD تستخدم `ER14 >= 0.20`، وChop sleeve تستخدم `ER14 < 0.25`. النطاق `0.20 <= ER14 < 0.25` يسمح بالمكوّنين معاً. في البيانات كان التداخل تقريباً: XAU `8.35%`، NSX `9.52%`، BTC `8.47%` من الأيام الصالحة. هذا ليس خطأ حسابياً، لكنه تضاعف بحثي يجب أن يكون مقصوداً ومقاساً.
7. **الـfill model:** المصدر يستخدم limit/stop منفصلين ولا يخصص partial-fill أو spread/slippage model خاصاً. نتيجة OHLC/ملفات الصفقات ليست live execution evidence.
8. **CFD calendar:** `_cfd_blocked` يضع حظر UTC ثابتاً (`20:00..01:00`، وإغلاق XAU الجمعة بعد `18:00`) لكنه ليس بديلاً عن exchange/broker holiday/session calendar.
9. **Swing state:** `trend` ينتقل إلى +1/-1 عند close فوق آخر pivot مؤكد/تحت آخر pivot مؤكد؛ هذا تعريف عملي مبسط، لا sequence كامل لـHH/HL/LH/LL. لذلك يجب ألا نبيع تسمية CHoCH/BOS على أنها معيار ICT كامل.
10. **الـFVG والـsweep صحيحان causal في الاختبار المحلي، لكنهما لا يثبتان صحة اقتصادية.** تغيير k، minimum gap، displacement، مدة صلاحية candidate أو أولوية المرشحين يخلق مساحة بدائل كبيرة، ومن ثم خطر overfitting.

## overfitting وتعدد الاختبارات

تم تشغيل عدة ablations، ولذلك لا يصح اعتبار أفضل holdout (`BTC no-BE`) تقديراً غير متحيز. مرجع مهني مناسب لهذه النقطة:

- Bailey et al., *The Probability of Backtest Overfitting*: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253
- *The Deflated Sharpe Ratio*: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551

الخطوة الصحيحة التالية للمرشح هي rolling walk-forward أو CSCV/PBO مع تجميد القرار قبل كل test window، وليس تحسين thresholds على كامل `2020–2026`.

## مراجع التنفيذ الواقعي

- QuantConnect slippage: https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/slippage/key-concepts
- QuantConnect fills: https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/trade-fills/key-concepts
- Limit orders وbid/ask: https://www.quantconnect.com/docs/v2/writing-algorithms/trading-and-orders/order-types/limit-orders
- Reconciliation بين backtest/live: https://www.quantconnect.com/docs/v2/cloud-platform/live-trading/reconciliation
- OUO/stop precedence: https://www.quantconnect.com/docs/v2/writing-algorithms/trading-and-orders/order-types/contingent-orders/one-updates-other-orders
- NYSE local-hours calendar: https://www.nyse.com/trade/hours-calendars
- قواعد GMT/BST: https://www.gov.uk/when-do-the-clocks-change
- leverage وday-trading risk: https://www.sec.gov/files/investor/pubs/daytips.htm

## الملفات الناتجة

- `run_audit.py`: baseline V8 وablations الخاصة بـXAU/NSX/BTC.
- `btc_ablation_split.py`: فصل BTC no-09h عن BTC no-BE one-change-at-a-time.
- `micro_ablation.py`: ATR/DST matched experiment.
- `prefix_invariance.py`: prefix replay للـV8 مع boundary wrapper runtime-only.
- `btc_prefix_invariance.py`: prefix replay لمرشح BTC no-BE.
- `cost_stress.py`: 1x/2x/3x cost-only sensitivity.
- `results/summary_principles_audit.json`: النتائج الأساسية.
- `results/cost_stress.json`: كل الفترات والتكاليف.
- `results/prefix_invariance.json`: فحص سببية V8.
- `results/btc_no_be_prefix_invariance.json`: فحص سببية المرشح.
- `results/micro_ablation.json`: تجربة ATR/DST.
- `results/trades_*.csv`: الصفقات لكل variant لإعادة التحليل.

**الخلاصة:** V8 الحالية تبقى frozen. المرشح الوحيد الذي يستحق اختباراً تالياً هو BTC no-BE فقط، بشرط إعادة اختباره أولاً بعد إصلاح TP-after-SL-floor في طبقة مستقلة، ثم على rolling walk-forward وQC fill model واقعي. لا يتم نسخ أي سطر إلى `V8_3Asset_1PosEach_QC.py` قبل نجاح هذه الشروط.
