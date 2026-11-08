# نتيجة اختبار السلاسل الأربع (L00) — K7 المرحلة صفر

## تنبيه قبل الجدول

هذه السلاسل **ادعاء مستخدم غير موثّق** (`USER_LEAD_UNVERIFIED`). ليست Tier1، وليست معرفة،
ولا تدخل أي محرك. الغرض الوحيد: هل توجد حرفياً في النص أم لا.

## طريقة البحث

- على النص المُطبَّع N-06: تصغير الحروف، توسيع الاختصارات (you're → you are، don't → do not)،
  حذف كل ما ليس حرفاً أو رقماً، ثم مطابقة متتابعة للكلمات.
- محاولة أولى: مطابقة تامة للسلسلة كاملة.
- محاولة ثانية (تنويعات الترجمة الآلية): نافذة منزلقة بطول السلسلة ± كلمة، تُقبل إذا كان
  مسافة التعديل ≤ 2 كلمة (أو 12% من الطول). كل تنويعة تُعرض بنصها الحقيقي.
- محاولة ثالثة (جزئي): أطول مقطع متتابع من السلسلة موجود فعلاً، بحد أدنى 4 كلمات.
- «وجود مقطع شائع في مكان آخر لا يؤكد الجملة». هذا مكتوب في الجدول لكل سطر.

## الجدول

| السلسلة | الحالة الآلية | الأرقام | الحكم |
|---|---|---|---|
| S1 — «If you don't know what the Daily Chart is doing, you are gambling» | FOUND_PARTIAL | تام=0، تنويعات=0، مقاطع جزئية=293 | **غير موجودة حرفياً.** أطول مقطع مؤكد: «if you do not know what the daily chart» في ملف واحد، والجملة الحقيقية تكملة مختلفة تماماً («…the daily charts implying in terms of institutional…»). وعبارة «you are gambling» موجودة وحدها في 15 ملفاً. وجود النصفين منفصلين **لا يؤكد** الجملة. |
| S2 — «When the Monthly and Weekly are in conflict, you sit on your hands» | FOUND_PARTIAL | تام=0، تنويعات=0، مقاطع جزئية=35 | **غير موجودة حرفياً.** عبارة «sit on your hands» موجودة فعلاً في 22 ملفاً، لكن ليس مع شرط «monthly and weekly are in conflict» الذي لا يظهر في أي ملف. الشرط والنتيجة يجتمعان في النص؟ لا. |
| S3 — «Narrative is not support and resistance» | FOUND_VARIANT | تام=0، تنويعات=53، مقاطع جزئية=0 | **أقرب نص مختلف في كلمة واحدة حاسمة.** النص الحقيقي: «it's not support and resistance»؛ كلمة «narrative» غير موجودة في تلك الجملة. فالجملة المزعومة ليست قوله، والمعنى مختلف. |
| S4 — «IPDA is a computer program. It only looks for two things» | FOUND_PARTIAL | تام=0، تنويعات=0، مقاطع جزئية=2 | **غير موجودة.** كلمة «IPDA» لا ترد إلا 3 مرات في المدونة كلها، و«ipda is a computer program» لا ترد أبداً. الاسم الكامل «interbank price delivery algorithm» يرد 17 مرة في 12 ملفاً، و«it only looks for two things» لا يرد. |

## الأدلة الحرفية (كل اقتباس ≤ 25 كلمة، بموضعه)

### S1

أطول مقاطع موجودة فعلاً:
- 9 كلمات — «if you do not know what the daily chart» — `F0120`
- 7 كلمات — «if you do not know what the» — `F0181`
- 7 كلمات — «if you do not know what the» — `F0262`

### S2

أطول مقاطع موجودة فعلاً:
- 6 كلمات — «the monthly and weekly are in» — `F0026`
- 6 كلمات — «when the monthly and weekly are» — `F0064`
- 5 كلمات — «the monthly and weekly are» — `F0055`

### S3

أقرب تنويعات (الفارق مبيَّن):
- مسافة 1 كلمة — `F0143` — «is not support and resistance»
- مسافة 1 كلمة — `F0143` — «it is not support and resistance»
- مسافة 1 كلمة — `F0206` — «is not support and resistance»
- مسافة 1 كلمة — `F0206` — «it is not support and resistance»

### S4

أطول مقاطع موجودة فعلاً:
- 4 كلمات — «is a computer program» — `F0006`
- 4 كلمات — «is a computer program» — `F0058`

## الشواهد الحرفية من المسح الموجّه (مقاطع بمواضع offsetMS)

**S1_HEAD** — البحث عن «if you do not know what the daily chart»: ظهر في ملف واحد، مرة واحدة.
- `F0120` عند offsetMS=766260 — «analysis on a daily chart because if you don't know what the daily charts implying in terms of institutional polish or bearish»

**S1_TAIL** — البحث عن «you are gambling»: ظهر في 15 ملفاً، 20 مرة.
- `F0111` عند offsetMS=2026980 — «to do anything less than that you're gambling and think about who makes these markets move»
- `F0135` عند offsetMS=3895760 — «can't reasonably outline that then you're gambling and if you're trying to trade every»

**S2_PHRASE** — البحث عن «sit on your hands»: ظهر في 22 ملفاً، 23 مرة.
- `F0026` عند offsetMS=844639 — «of setups that require you to sit on your hands and wait but when they form and you»
- `F0040` عند offsetMS=2314619 — «more fun but you have to sit on your hands away a little bit more it's not»

**S2_SENTENCE** — البحث عن «monthly and weekly are in conflict»: **لم يظهر إطلاقاً** في أي من الملفات 490.

**S3_FRAG** — البحث عن «is not support and resistance»: ظهر في 3 ملفاً، 3 مرة.
- `F0143` عند offsetMS=978480 — «on any retail logic no it's not support and resistance it's not supplying demand i'm trading»
- `F0206` عند offsetMS=1540440 — «not supply and demand and it's not support and resistance it's these ranges the Market's going»

**S4_SENTENCE** — البحث عن «ipda is a computer program»: **لم يظهر إطلاقاً** في أي من الملفات 490.

**S4_FULLNAME** — البحث عن «interbank price delivery algorithm»: ظهر في 12 ملفاً، 17 مرة.
- `F0001` عند offsetMS=282160 — «those conditions or context now the interbank price delivery algorithm or what i always refer to as the»
- `F0006` عند offsetMS=898800 — «let's get back to the interbank price delivery algorithm the daily range structure can be really broken»

**S4_ACRONYM** — البحث عن «ipda»: ظهر في 3 ملفاً، 3 مرة.
- `F0015` عند offsetMS=1652559 — «into another consolidation okay think about ipda now price delivery has been rapid on one»
- `F0058` عند offsetMS=937600 — «get yourself in sync with what ipda most recently did and ipta is the interbank»

## الحكم النهائي على L00

لا واحدة من السلاسل الأربع موجودة حرفياً في المدونة. ثلاث منها لها أقرب نص مختلف،
وواحدة (S3) تختلف في الكلمة الحاكمة. لذلك لا تصبح أي منها Tier1، ولا تُستخدم كدليل على
معنى أو شرط. تُترك في هذا الجدول فقط بوصفها `USER_LEAD_UNVERIFIED`.
