# Sweep → one-bar displacement replay

هذا مجلد مستقل أضيف على الفرع الحالي فقط. لم يتم تعديل محركات `project/` أو
مرجع V8/V9 الموجودين في المستودع.

## التشغيل

لا يحتاج `pandas` أو `numpy`:

```bash
cd sweep_reversal_research
python test_strategy.py
python run_2021.py
```

النتائج المثبتة في `results_2021_six_months/`:

- `REPORT_AR.md` — شرح عربي وتصحيح اتجاه 2021.
- `summary.json` — أرقام قابلة للقراءة آلياً وبصمات البيانات.
- `signals.csv` — sweep candidates، LONG/SHORT، شمعة S+1، FVG، target source.
- `outcomes.csv` — دخول فوري ودخول بعد ثلاث شمعات، مع ترتيب stop-first عند غموض OHLC.
- `charts/short_example_2021.svg` — upper sweep ثم red displacement = SHORT.
- `charts/long_example.svg` — المرآة الصاعدة.

## العقد الثابت

1. المستوى هو swing ثلاثي الشموع مؤكد causally؛ لا يصبح متاحاً إلا بعد إغلاق
   الشمعة التالية.
2. LONG: sweep تحت low مؤكد مع إغلاق فوقه. SHORT: sweep فوق high مؤكد مع
   إغلاق تحته.
3. displacement هو الشمعة التالية مباشرة `S+1` فقط. لا يوجد S+2/S+3 في النسخة
   المصححة.
4. target للشراء هو أقرب high مؤكد قبل swept low؛ وللبيع أقرب low مؤكد قبل
   swept high.
5. الـ small/hammer candle بعد displacement معلومة وصفية لاحقة وليست شرطاً
   يخفي look-ahead.
6. القياس الأساسي يدخل عند إغلاق displacement ويقيس الشموع الثلاث التالية على
   1m OHLC. المسار الوصفي `after_three` ينتظر D+3، يرفض أي setup لمس target/stop
   قبله، ثم يقيس D+4..D+6. لا توجد bid/ask في المصدر، لذلك لا يتم اختراع spread أو fee.

الجولة تقيس XAUUSD 15m/1m على ستة أشهر متتالية من 2021-06 إلى 2021-11، مع
2021-05 warm-up و2021-12 outcome-only لنهاية نوفمبر. ليست النتيجة وعداً بربح أو
إثبات edge.
