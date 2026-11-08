# المفهوم (هـ): جرف السيولة / عصف الوقف — سجل المصادر الخارجية

الطبقة: كل ما هنا `TIER2`. لا يختلط بأقوال مايكل في أي سياق آخر.
تاريخ الوصول لكل الروابط في هذا الملف: **2026-11-08**.

## المصادر

| # | الرابط | المؤلف | نوع المؤلف | تاريخ النشر كما ظهر | الوثوقية (وقائع قابلة للفحص فقط) |
|---|---|---|---|---|---|
| E1 | https://www.ictkillzone.com/ict-liquidity-sweep | Michael Phillips — ICTKillzone | THIRD_PARTY | 2026-06 (يونيو 2026) | اسم ظاهر؛ موقع تعليمي متخصص بالسيولة؛ يعرض مخططات مشروحة؛ يصنّف الجروف نوعًا 1/2/3 كتفكيره لا كقول مايكل |
| E2 | https://alphametrixx.com/blog/ict-liquidity-trading-sweeps-pools-and-stop-hunts-explained | مجهول؛ Alpha Metrix | UNKNOWN | 2026-05-11 | مجلة يومية تداول بلا هوية؛ المحتوى متماسك داخليًا؛ لا دليل نتائج |
| E3 | https://www.writofinance.com/module-3-understanding-ict-liquidity/ | مجهول؛ Writ of Finance | UNKNOWN | 2026-09-28 | دورة منظمة؛ يفرق بين «sweep» و«run» صراحة (درس 3.7 و3.8)؛ لا هوية |
| E4 | https://quartersequence.com/the-study/ict-liquidity/ | مجهول؛ «The Study» | UNKNOWN | مُحدّثة ~2026-10-28 | ملاحظات دراسة؛ ينقل قول مايكل: الجرف «only if we start to move away from it»؛ يفرق sweep/raid/purge/break |
| E5 | https://myprimusmarkets.com/ict-smart-money-concepts/ | مجهول؛ Primus Markets | UNKNOWN (بروكر) | 2026-10-08 | بروكر؛ نبرة حذرة؛ يذكر أن قاعدة الإغلاق مقابل الفتيل «rule choice» يغيّر الصورة |

**ملاحظة الاستقلال والنسخ:** لا نسخ بين E1–E5 (صياغة مستقلة). E1 (Michael Phillips) كاتب معروف الاسم؛ يبقى موقعه تجاريًا (100+ guides) — لا دليل نتائج.

## هل يصف كل مصدر الشكل على الشموع بالكلمات؟

- **E1 — نعم.** «price extends a wick beyond a BSL or SSL pool… body closing back inside the prior range»؛ يفرّق sweep عن breakout باختبار «body-close»: الفتيل يتجاوز والجسم يغلق داخل المدى؛ يورد النوع 2 «candle body closes slightly beyond the level» ثم ينعكس فورًا.
- **E2 — PARTLY.** «a sharp spike with a long wick — price punched into the zone, the stops fired»؛ لا يحدد قاعدة الإغلاق/الفتيل بدقة؛ يشترط ثلاثة شروط للجرف «النظيف» (معنىً) بلا عتبات.
- **E3 — نعم.** «a long, thin shadow poking past the level, with the candle's body closing back on the other side»؛ يصرح: «sweeps should be judged only after the candle closes»؛ ويفرق الجرف عن الجريان (run) بأنه أكثر من مستوى واحد متتالٍ.
- **E4 — نعم.** «a move that trades through an old high or low, takes the orders resting there, then closes back on the other side and moves away»؛ ويستشهد بنص مايكل: السيولة تعتبر «purged only if we start to move away from it»؛ «You cannot tell a sweep from a break while the wick is printing».
- **E5 — نعم.** «price trades through one of these levels, triggers the resting orders, then fails to hold beyond it… usually appears as a long wick through equal highs and a close back inside the range»؛ ويذكر أن «Some traders count a break only on a candle close; others accept a wick».

كل اقتباس أعلاه ≤ 25 كلمة.

## جدول الاتفاق — لا اختيار بينها

**النسخة A — الفتيل يتجاوز والجسم يغلق داخل المدى (rejection كامل):**
- المصادر: E1 (النوع 1)، E3، E4، E5 + جزئيات E2.
- عدد المصادر المستقلة: **5**.

**النسخة B — الجرف ولو أغلق الجسم قليلًا وراء المستوى ثم انعكاس فوري («displacement sweep»):**
- المصادر: E1 (النوع 2)، ويضيف E3 أن استمرار الجسم وراء المستوى = breakout لا sweep.
- عدد المصادر المستقلة المؤيدة صراحة: **1 (E1)**؛ المعارضة الصريحة: **E3** (strict close-inside) — تعارض حقيقي.

**عند «كم يبعُد الجرف» و«كم بسرعته»:**
- لا يوجد أي رقم متفق عليه في أي مصدر (لا نقاط، لا نسبة ATR، لا نسبة من مدى الشمعة). E2 «pushing meaningfully past» (بلا مقدار)؛ E1 «extends a wick… beyond» (بلا مقدار).
- `DISAGREEMENT: رفض إغلاق الجسم أم رفض أي اختراق.` E1-النوع 2 يقبل إغلاقًا هامشيًا ثم انعكاسًا؛ E3 يشترط أن يعود الجسم داخل؛ E5 يسجل أن الخيارين «rule choices» لا يحسم.
- `DISAGREEMENT: الجرف مقابل الكسر عند أي إغلاق.` E4 وE1: الإغلاق وراء المستوى والثبات = break (ليس جرفًا)؛ E1-النوع 2 يسمح باستثناء مؤقت.

## KNOWLEDGE_GAP

- `KNOWLEDGE_GAP: ما مقدار اختراق المستوى الذي يسميه مايكل جرفًا — فتيل فقط أم إغلاق أيضًا؟`
- `KNOWLEDGE_GAP: ما الحد الأدنى لنزعة الجرف (أي مدى بالنقاط/النسبة/ATR) عند مايكل؟`
- `KNOWLEDGE_GAP: ما الإطار الزمني/السرعة التي تجعل «الجريان» جرفًا؟` (لا مصدر يحدد زمنًا؛ E3 يفرق run/sweep بالمدى لا بالسرعة.)
- `KNOWLEDGE_GAP: هل جرف السيولة شرط لازم قبل أي إعداد عند مايكل أم تصفية مجتمعية؟` (E1 يجعله شرطًا للكتلة؛ لا اقتباس مباشر لمايكل هنا.)

## الحكم للمهمة

- وصف الشكل بالكلمات: **YES** (فتيل يتجاوز + عودة الجسم داخل هو الشكل المتفق عليه) مع **خلاف** حول الإغلاق الهامشي.
- عدد المصادر المستقلة: **5**.
- الاتفاق: **متفقون** على نواة الشكل؛ **مختلفون** على الإغلاق الهامشي؛ **لا أحد** يعطي مسافة/سرعة رقمية؛ لا يوجد قول من مايكل في هذه المصادر يحسم.
