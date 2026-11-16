# Sweep → one-bar displacement replay

هذا مجلد مستقل أضيف على الفرع الحالي فقط. لم يتم تعديل محركات `project/` أو
مرجع V8/V9 الموجودين في المستودع.

## التشغيل

لا يحتاج `pandas` أو `numpy`:

```bash
cd sweep_reversal_research
python test_strategy.py
python run_2021.py
python run_2021_account.py
python run_2021_active.py
```

`run_2021_account.py` هو replay الحساب الكامل من يناير إلى ديسمبر 2021، برصيد
ابتدائي `$100`، ومخاطرة أساسية 1% من equity الحالي مع compounding، مع منع أي
تداخل LONG/SHORT. مخرجاته في `results_2021_account/` وتشمل `summary.json`,
`monthly_summary.csv`, `weekly_summary.csv`, `taken_trades.csv` و`ACCOUNT_REPORT_AR.md`.

`run_2021_active.py` هو المرشح النشط الأعلى تكراراً: يحافظ على sweep السببي،
اتجاه displacement في `S+1`، target الأول، وعدم التداخل، لكنه يزيل FVG وP80
حتى لا يخنق عدد الإشارات. حسابه الأساسي يستخدم 0.15% لكل صفقة وحد سحب تاريخي
مراقب 5%. مخرجاته في `results_2021_active/`. هذه نسخة بحثية، وليست ضمان ربح.

النتائج التشخيصية السابقة في `results_2021_six_months/`:

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
4. target للشراء هو أول high مؤكد قبل swept low؛ وللبيع أول low مؤكد قبل
   swept high (أي لا نختار swing لاحقاً بأثر رجعي).
5. الـ small/hammer candle بعد displacement معلومة وصفية لاحقة وليست شرطاً
   يخفي look-ahead.
6. القياس الأساسي يدخل عند إغلاق displacement ويقيس الشموع الثلاث التالية على
   1m OHLC. المسار الوصفي `after_three` ينتظر D+3، يرفض أي setup لمس target/stop
   قبله، ثم يقيس D+4..D+6. لا توجد bid/ask في المصدر، لذلك لا يتم اختراع spread أو fee.

الجولة تقيس XAUUSD 15m/1m على ستة أشهر متتالية من 2021-06 إلى 2021-11، مع
2021-05 warm-up و2021-12 outcome-only لنهاية نوفمبر. ليست النتيجة وعداً بربح أو
إثبات edge.
