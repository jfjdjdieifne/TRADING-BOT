# V9 Dynamic Profile / Sweep–CHoCH Design — قرار هندسي قابل للتدقيق

**التاريخ:** 2026-11-16 UTC
**حالة العمل:** طبقة بحث وإشارات فقط — ليست مفعّلة على الحساب الحقيقي
**المرجع المحمي:** `exports/quantconnect/V8_3Asset_1PosEach_QC.py` لم يتم تعديله، وهو يبقى خط الأساس للرجوع إليه.

## 1. ماذا أخذنا من الخريطة، وماذا رفضنا كحقيقة غير مثبتة؟

الخريطة التي أرسلها المالك مفيدة كـ **فرضيات تشغيلية**، وليست دليلاً على أن السعر يتحرك دائماً بسبب "الحيتان" أو أنه سيحقق ربحاً إيجابياً كل أسبوع وشهر. لذلك تم تحويلها إلى بوابات قابلة للقياس:

| فكرة الخريطة | التطبيق في V9 | الحدّ الصريح |
|---|---|---|
| `Volume Z-Score` ديناميكي | حجم الشمعة الحالية مقابل آخر 100 شمعة مكتملة **قبلها** | لا يوجد ادعاء بأن 2.5 انحراف معياري = مؤسسة؛ هذه عتبة فرضية قابلة للـ walk-forward |
| `ADI` | الحركة الاتجاهية من أصل الموجة إلى إغلاقها مقسومة على `N × ATR(14)` السابق | لا نستخدم ATR الشمعة الحالية كي لا تخفّف شمعة الاندفاع نفسها معيارها |
| `AGGRESSIVE_ATTACK` | لا يُفتح إلا عند اجتماع الحجم + السرعة + تدفق سبوت مؤكد | غياب CVD أو وجود divergence يعيد الحالة إلى الدفاع، ولا نستعمل OHLCV كبديل صامت |
| Shallow FVG | فجوة ثلاثية الشموع causal؛ الشراء عند الحد العلوي للفجوة الصاعدة، أي `Low(Candle 3)` | الحد يجب أن يمر بفلتر tick/precision وبـ R:R وبقواعد الوسيط |
| Protected Momentum SL | للشراء: `Low(Impulse) - tick`، وللبيع: `High(Impulse) + tick` | لا يكفي وحده: يجب اختبار السبريد، الحد الأدنى للمسافة، والانزلاق والتنفيذ الجزئي |
| CVD convergence | نستخدم signed executed-initiated spot flow المعلن من المصدر، ونقارن CVD الحالي بأعلى/أدنى القيم السابقة | هذا ليس order-book pressure ولا يثبت نشاط الحيتان |
| Funding heat | إذا توفر funding للـ perpetual، يمكن تفعيل حد `maximum_abs_funding_rate`؛ hot أو missing عند `require_cool_funding` يمنع الهجوم | funding ليس متاحاً للـ spot، لذلك البوابة اختيارية ولا نملأها بقيمة وهمية |
| CHoCH | كسر جسم كامل لقمة/قاع swing مؤكد causal بعد sweep، مع سرعة وحجم ومسافة ATR وتدفق | `CHoCH` و`MSS` تسميات تشغيلية؛ لا ندّعي تعريفاً عالمياً واحداً |
| Counter-trend exit | لا توجد صفقة بلا target معروف؛ الهدف الأول من opposing FVG/OB المعروف سابقاً وبـ `>= 5R` | الهدف ليس ضماناً للامتلاء، ويجب إعادة اختبار ترتيب اللمس داخل الشمعة |

## 2. لماذا لا ننسخ تعريفات SMC/ICT بلا تمحيص؟

البحث المحفوظ داخل المشروع نفسه أظهر تعارضاً في تعريف Order Block بين مصادر منسوبة إلى ICT: تعريف شمعة واحدة، وتعريف سلسلة شموع. كما أن صفحة `theinnercircletraders.com` تشرح FVG كفراغ ثلاثي الشموع وتذكر أن موثوقية الرجوع والملء تعتمد على السياق، لكنها لا تثبت ربحية آلية. لذلك:

1. `FVGZone` و`OrderBlockZone` في الكود **كيانات سعرية تشغيلية** فقط.
2. لا يوجد في السجل عبارة أن المنطقة "أوامر مؤسسات مؤكدة".
3. تعريف OB الحالي هو آخر شمعة معاكسة داخل leg سبق الكسر، وهذا اختيار هندسي يجب اختباره لا حقيقة دينية.
4. أي انتقال من الإشارة إلى نموذج/وزن/احتمال يحتاج بحثاً causal وwalk-forward منفصلاً.

## 3. ما الذي تم تنفيذه؟

الملف الجديد:

```text
smc_v4_multisleeve_package/engine/dynamic_profile.py
smc_v4_multisleeve_package/tests/test_dynamic_profile.py
```

المحرك `DynamicProfileEngine` يعمل bar-by-bar ويحافظ على المعلومات المتاحة فقط:

```text
completed bar
   │
   ├─ read prior-volume history -> z-score
   ├─ read prior ATR -> ADI
   ├─ evaluate only previously confirmed swing levels
   ├─ create current FVG/OB after the current bar is complete
   ├─ apply Spot CVD gate
   ├─ form plan only when opposing target and minimum R:R exist
   └─ commit current bar to state
```

### البوابات الصلبة

```text
AGGRESSIVE =
    volume_z > 2.5
    AND ADI > 3.0
    AND SpotFlow == VALID
    AND no exhaustion/divergence
```

إذا لم تتحقق **كلها**، فإن الملف لا يخفف شرط Deep OB إلى Shallow FVG. في حالة عدم وجود target معروف أو عدم بلوغ `5R` لا يصدر Plan، حتى لو كانت صورة الموجة جذابة.

### CVD ومصدره

لـ Binance Spot، إذا كان المصدر هو Kline الذي يحوي `base_volume` و`taker_buy_base_volume`:

```text
sell_initiated = base_volume - taker_buy_base_volume
delta = taker_buy_base_volume - sell_initiated
       = 2 * taker_buy_base_volume - base_volume
```

هذا يطابق طبقة المصدر الموجودة في المشروع من حيث **executed/initiated flow** فقط. لا يجوز تسميته institutional flow أو whale activity. عند غياب هذا الحقل، `FlowStatus=UNKNOWN`، والبوابة aggressive مغلقة افتراضياً.

### حماية السباق والتنفيذ

`TradePlan` لا ينفذ أمراً. هو يحمل:

- limit entry عند حد FVG؛
- stop محمي حول شمعة الاندفاع أو extreme الكنس؛
- target معروف؛
- minimum target المشتق من `5R`؛
- expiration؛
- invalidation؛
- مصدر zone وسبب الخطة.

`tighten_stop` لا يسمح بتوسيع المخاطرة أو نقل الستوب عبر السعر الحالي. ربط هذه الخطة بوسيط حقيقي يحتاج adapter مستقل يحترم tick size وlot size وmin notional ورفض الأوامر وpartial fills وreconnect وOCO reconciliation.

## 4. لماذا لم نربطه بعد بصفقات حقيقية؟

الربط المباشر الآن سيكون ادعاءً غير مسؤول للأسباب التالية:

1. ملف V8 المرجعي لا يوفّر Spot CVD الحقيقي لكل أصل؛ Volume الخاص بـ CFD ليس CVD.
2. بيانات backtest الحالية للأصلين XAU/NSX لا تكفي لإثبات executed spot flow.
3. QuantConnect/البوركر قد يملأ limit داخل شمعة بطريقة تختلف عن tick-level live fill.
4. لا يجوز اعتبار نتيجة تاريخية موجبة ضماناً أسبوعياً أو شهرياً.
5. لا بد من مرحلة replay مستقلة ببيانات spot klines/aggTrades، ثم paper trading، ثم مبلغ صغير مع kill-switch.

## 5. خطة الاختبار قبل أي تفعيل

1. **Unit/causal:** تشغيل `tests/test_dynamic_profile.py` والتأكد من عدم تغيّر prefix عند إضافة شموع مستقبلية.
2. **Data contract:** ربط مصدر Binance Spot المعتمد فقط، والتحقق من identity وtimestamp والـ gaps و`buy + sell == total`.
3. **Walk-forward:** معايرة thresholds في TRAIN فقط، ثم TEST زمني غير مرئي، بلا اختيار شهري لاحق.
4. **Stress:** maker/taker fees، spread، slippage، partial fills، gaps، funding إن كان التنفيذ Futures، وانقطاع feed.
5. **Portfolio:** اختبار correlation وconcurrent risk وdaily/weekly loss brake؛ عدم استهداف ربح شهري ثابت.
6. **Paper:** تنفيذ إشارات وخطط V9 دون رأس مال مع قياس fill rate وlatency وrejection وexit drift.
7. **Live canary:** بعد اجتياز ما سبق، مخاطرة صغيرة جداً مع kill-switch عند missing flow أو stale data أو reconciliation mismatch.

## 6. مصادر البحث

- Binance Spot REST API — `aggTrades`, Klines، وحقول `isBuyerMaker` وtaker-buy volume:
  <https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md>
- Binance Spot WebSocket Streams — aggregate trade payload وقيود الاتصال/الانقطاع:
  <https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md>
- Binance Futures connector — يوضح أن `aggTrade` feed يجمع market trades الخاصة بـ taker order، وهو مرجع connector لا تعريفاً للـ CVD:
  <https://github.com/binance/binance-futures-connector-python/blob/main/binance/websocket/um_futures/websocket_client.py>
- ICT/Inner Circle Traders — صفحة مقارنة FVG وOB المستخدمة للمصطلح، مع إبقاء الربحية والسبب المؤسسي غير مثبتين:
  <https://www.theinnercircletraders.com/fvg-vs-order-block/>
- المصدر البحثي المحلي الذي حفظ التعارضات والاقتباسات:
  `project/trading_project/docs/research/huddleston_study/source_corpus_v3/cards/order_block.md`
- المرجع السابق الذي طلب المالك عدم تعديله:
  `smc_v4_multisleeve_package/exports/quantconnect/V8_3Asset_1PosEach_QC.py`

## 7. قرار المرحلة

تم تنفيذ **المخ الحسابي** للـ Dynamic Profile وCVD gate وCHoCH validation وprotected stop كطبقة منفصلة قابلة للاختبار. لم يتم تغيير V8.4، ولم يتم فتح أو إغلاق صفقات حقيقية، ولم يتم تقديم وعد بربح إيجابي حصراً. الخطوة التالية الصحيحة هي إدخال feed سبوت موثّق، بناء replay/backtest مستقل، وقياس النتائج قبل أي execution adapter.
