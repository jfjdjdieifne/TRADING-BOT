# التحقق من أربعة عشر مدخلاً مقابل نصوص المتحدث

## نطاق العمل والمنهج
- هذه مراجعة تحقق لا استكشاف جديد. عوملت L01–L14 كمدخلات مستخدم غير موثقة، لا كمصادر ولا كوقائع.
- جرى تنزيل الأرشيف المحدد للمستودع `newsqlguru/ict-index` عند الالتزام `e8c40a8dae5ea6689926f28c7184ce3e2fb85b9c` خارج المستودع، والتحقق من SHA-256 للأرشيف: `4213e692f7c978dab8fe5ba124d34d887f17316c89d27bb2a7406fd3776f769d`. عدد ملفات النصوص في اللقطة 490.
- كل ملف مطابق للعنوان المذكور أدناه فُحص نصه كاملاً آلياً. نافذة المراجعة تعني خمسة مقاطع متتابعة حول مجموعة تطابق كلمات مفتاحية؛ دُمجت المراكز المتقاربة، وبحد أقصى خمس نوافذ مستخرجة لكل ملف. الأعداد «مطلوب/مفتوح» تخص هذه النوافذ المرشحة، أما الملفات فتم فحصها كاملة.
- الاقتباسات حرفية من النص الإنجليزي الأصلي، وكل اقتباس لا يتجاوز 25 كلمة؛ بقية التقرير بالعربية. فواصل المقاطع جُمعت بمسافة واحدة لأجل قراءة النص كما ورد متتابعاً. لا توجد علامات تعريف للمتحدث في ملفات JSON؛ إسناد الاقتباسات أدناه إلى مايكل مبني على سياق المحاضرة/ضمير المتكلم، وليس على وسم آلي للمتحدث.
- وجود عنوان مطابق لا يعني صحة المدخل. لم يُحوّل أي اقتباس إلى قاعدة عامة، ولم تُدمج أو تُوسّط بدائل المدخلات.

## خلاصة صفوف التحقق
الحالات: «يؤيده» = النص يقول المدخل بالشروط نفسها؛ «شرط مختلف» = توجد عبارة قريبة لكن بشروط/نطاق غير مطابق أو لا تثبت كامل الصياغة؛ «يناقض» = نص صريح معاكس؛ «غير معثور عليه» = لم يظهر اقتباس مؤيد أو مناقض قابل للإسناد بعد فحص النصوص المعنية.

| المدخل | الحالة | ملفات العنوان المطابقة | الاقتباسات | المتحدث | النوافذ المطلوبة/المفتوحة؛ الملفات المفحوصة | المقارنة بالمعرفات السابقة |
|---|---|---|---|---|---|---|
| L01 | شرط مختلف | E05 + M04 | Q001, Q002 | مايكل؛ إسناد سياقي | 31/31؛ 15/15 | لا حكم قابل للتحقق |
| L02 | شرط مختلف | E12 + E13 | Q003, Q004 | مايكل؛ إسناد سياقي | 14/14؛ 3/3 | لا حكم قابل للتحقق |
| L03 | شرط مختلف | E10 + M03 | Q005, Q006 | مايكل؛ إسناد سياقي | 10/10؛ 10/10 | لا حكم قابل للتحقق |
| L04 | شرط مختلف | M05 | Q007, Q008 | مايكل؛ إسناد سياقي | 38/38؛ 20/20 | لا حكم قابل للتحقق |
| L05 | شرط مختلف | E02 + E03 | Q009, Q010 | مايكل؛ إسناد سياقي | 8/8؛ 3/3 | لا حكم قابل للتحقق |
| L06 | شرط مختلف | M02 | Q011, Q012 | مايكل؛ إسناد سياقي | 24/24؛ 9/9 | لا حكم قابل للتحقق |
| L07 | شرط مختلف | E16 | Q013, Q014 | مايكل؛ إسناد سياقي | 5/5؛ 2/2 | لا حكم قابل للتحقق |
| L08 | شرط مختلف | M07 | Q015 | مايكل؛ إسناد سياقي | 29/29؛ 8/8 | لا حكم قابل للتحقق |
| L09 | شرط مختلف | E07 + E08 | Q016 | مايكل؛ إسناد سياقي | 7/7؛ 3/3 | لا حكم قابل للتحقق |
| L10 | شرط مختلف | M08 | Q017, Q018 | مايكل؛ إسناد سياقي | 25/25؛ 8/8 | لا حكم قابل للتحقق |
| L11 | شرط مختلف | M07 | Q019 | مايكل؛ إسناد سياقي | 21/21؛ 8/8 | لا حكم قابل للتحقق |
| L12 | شرط مختلف | E26 | Q020, Q021 | مايكل؛ إسناد سياقي | 5/5؛ 1/1 | لا حكم قابل للتحقق |
| L13 | شرط مختلف | E14 | Q022 | مايكل؛ إسناد سياقي | 1/1؛ 1/1 | لا حكم قابل للتحقق |
| L14 | غير معثور عليه | E04 + E21 | لا يوجد | لا اقتباس منسوب | 0/0؛ 2/2 | لا حكم قابل للتحقق |

## تعليل كل مدخل

### L01 — شرط مختلف
- خلاصة المقارنة: النص يذكر إطاراً يومياً، لكنه لا يقول إن اليومي يتغلب دائماً عند التعارض أو يحدد مصفوفة أطر أعلى.
- ملفات المطابقة: E05 + M04؛ الاقتباسات: Q001, Q002.
- نوافذ الكلمات المفتاحية المطلوبة/المفتوحة: 31/31؛ ملفات النص المطابقة المفحوصة كاملة: 15/15.
- مقارنة المعرفات: لا يمكن تقرير المطابقة أو التعارض، لأن سجلات المعرفات المشار إليها غير موجودة في نسخة المستودع المتاحة.

### L02 — شرط مختلف
- خلاصة المقارنة: يوجد رسم ساعة وإشارة إلى النزول لإطار أدنى؛ لا يثبت أن الساعة إطار مراقبة/تأكيد السيولة، ولا يذكر دخولاً داخل نافذة القتل في هذا السياق.
- ملفات المطابقة: E12 + E13؛ الاقتباسات: Q003, Q004.
- نوافذ الكلمات المفتاحية المطلوبة/المفتوحة: 14/14؛ ملفات النص المطابقة المفحوصة كاملة: 3/3.
- مقارنة المعرفات: لا يمكن تقرير المطابقة أو التعارض، لأن سجلات المعرفات المشار إليها غير موجودة في نسخة المستودع المتاحة.

### L03 — شرط مختلف
- خلاصة المقارنة: المصدر يعرّف التراكم/التلاعب/التوزيع ويذكر توقيت رفع حظر الأخبار؛ لا يقرر قاعدة الاثنين، ولا حظر فترة بعد ظهر الخميس/الجمعة، ولا شرط انتظار كسر بنية بعد الخبر.
- ملفات المطابقة: E10 + M03؛ الاقتباسات: Q005, Q006.
- نوافذ الكلمات المفتاحية المطلوبة/المفتوحة: 10/10؛ ملفات النص المطابقة المفحوصة كاملة: 10/10.
- مقارنة المعرفات: لا يمكن تقرير المطابقة أو التعارض، لأن سجلات المعرفات المشار إليها غير موجودة في نسخة المستودع المتاحة.

### L04 — شرط مختلف
- خلاصة المقارنة: يوجد ذكر للإزاحة السعرية وانتظار تحول البنية كلٌّ في سياق؛ لا يظهر تعريف النطاق بأنه آخر ساق ذات إزاحة واضحة كسرت البنية الرئيسية.
- ملفات المطابقة: M05؛ الاقتباسات: Q007, Q008.
- نوافذ الكلمات المفتاحية المطلوبة/المفتوحة: 38/38؛ ملفات النص المطابقة المفحوصة كاملة: 20/20.
- مقارنة المعرفات: لا يمكن تقرير المطابقة أو التعارض، لأن سجلات المعرفات المشار إليها غير موجودة في نسخة المستودع المتاحة.

### L05 — شرط مختلف
- خلاصة المقارنة: يظهر انحياز أسبوعي/يومي وعدم فرض تحول البنية؛ لا يظهر التسلسل الكامل مع مصفوفة إطار أعلى ونافذة قتل وتحول إطار أدنى، ولا شرط الزمن والسعر.
- ملفات المطابقة: E02 + E03؛ الاقتباسات: Q009, Q010.
- نوافذ الكلمات المفتاحية المطلوبة/المفتوحة: 8/8؛ ملفات النص المطابقة المفحوصة كاملة: 3/3.
- مقارنة المعرفات: لا يمكن تقرير المطابقة أو التعارض، لأن سجلات المعرفات المشار إليها غير موجودة في نسخة المستودع المتاحة.

### L06 — شرط مختلف
- خلاصة المقارنة: النص يتناول سوق العلاوة/الخصم؛ لا يقرر فضّ تداخل المناطق باختيار أعمق مصفوفة أو مستويات OTE.
- ملفات المطابقة: M02؛ الاقتباسات: Q011, Q012.
- نوافذ الكلمات المفتاحية المطلوبة/المفتوحة: 24/24؛ ملفات النص المطابقة المفحوصة كاملة: 9/9.
- مقارنة المعرفات: لا يمكن تقرير المطابقة أو التعارض، لأن سجلات المعرفات المشار إليها غير موجودة في نسخة المستودع المتاحة.

### L07 — شرط مختلف
- خلاصة المقارنة: يوجد جمع بين الانحياز اليومي ومصفوفة خصم في مثال؛ لا يثبت قاعدة عدم الأوزان الرقمية، ولا تسلسل الإطار الأدنى داخل نافذة القتل.
- ملفات المطابقة: E16؛ الاقتباسات: Q013, Q014.
- نوافذ الكلمات المفتاحية المطلوبة/المفتوحة: 5/5؛ ملفات النص المطابقة المفحوصة كاملة: 2/2.
- مقارنة المعرفات: لا يمكن تقرير المطابقة أو التعارض، لأن سجلات المعرفات المشار إليها غير موجودة في نسخة المستودع المتاحة.

### L08 — شرط مختلف
- خلاصة المقارنة: المقطع يتناول احتمال تجاوز وقف الخسارة عند خبر؛ لا يحدد الإبطال خلف قاع/قمة التلاعب الذي أخذ السيولة.
- ملفات المطابقة: M07؛ الاقتباسات: Q015.
- نوافذ الكلمات المفتاحية المطلوبة/المفتوحة: 29/29؛ ملفات النص المطابقة المفحوصة كاملة: 8/8.
- مقارنة المعرفات: لا يمكن تقرير المطابقة أو التعارض، لأن سجلات المعرفات المشار إليها غير موجودة في نسخة المستودع المتاحة.

### L09 — شرط مختلف
- خلاصة المقارنة: يوجد دخول قريب من كتلة أوامر ومثال تداول فجوة؛ لا يثبت الدخول عند الافتتاح أو 50%/CE ولا استعمال أوامر محددة.
- ملفات المطابقة: E07 + E08؛ الاقتباسات: Q016.
- نوافذ الكلمات المفتاحية المطلوبة/المفتوحة: 7/7؛ ملفات النص المطابقة المفحوصة كاملة: 3/3.
- مقارنة المعرفات: لا يمكن تقرير المطابقة أو التعارض، لأن سجلات المعرفات المشار إليها غير موجودة في نسخة المستودع المتاحة.

### L10 — شرط مختلف
- خلاصة المقارنة: يوجد منع مشروط لتداول افتتاح لندن بعد خبر، ويوجد أخذ جزء عند الاتزان؛ هذه شروط وسياقات مختلفة عن قائمة عدم التداول الواردة في الادعاء.
- ملفات المطابقة: M08؛ الاقتباسات: Q017, Q018.
- نوافذ الكلمات المفتاحية المطلوبة/المفتوحة: 25/25؛ ملفات النص المطابقة المفحوصة كاملة: 8/8.
- مقارنة المعرفات: لا يمكن تقرير المطابقة أو التعارض، لأن سجلات المعرفات المشار إليها غير موجودة في نسخة المستودع المتاحة.

### L11 — شرط مختلف
- خلاصة المقارنة: يوجد وصف نوعي لمخاطرة صغيرة/عائد مرتفع؛ لا يوجد رقم 1%–2% ولا قاعدة وقف خلف قمة/قاع التلاعب.
- ملفات المطابقة: M07؛ الاقتباسات: Q019.
- نوافذ الكلمات المفتاحية المطلوبة/المفتوحة: 21/21؛ ملفات النص المطابقة المفحوصة كاملة: 8/8.
- مقارنة المعرفات: لا يمكن تقرير المطابقة أو التعارض، لأن سجلات المعرفات المشار إليها غير موجودة في نسخة المستودع المتاحة.

### L12 — شرط مختلف
- خلاصة المقارنة: المثال يذكر أخذ سيولة البيع ثم توقع امتداد إلى سيولة الشراء وأخذ الجزء الأكبر عند مستوى؛ لا يذكر نسبة 50%–75% أو إطار 15 دقيقة.
- ملفات المطابقة: E26؛ الاقتباسات: Q020, Q021.
- نوافذ الكلمات المفتاحية المطلوبة/المفتوحة: 5/5؛ ملفات النص المطابقة المفحوصة كاملة: 1/1.
- مقارنة المعرفات: لا يمكن تقرير المطابقة أو التعارض، لأن سجلات المعرفات المشار إليها غير موجودة في نسخة المستودع المتاحة.

### L13 — شرط مختلف
- خلاصة المقارنة: المثال المحدد يرتب أخذ ستة عقود لتمويل الصفقة ثم نقل الوقف إلى التعادل؛ لا ينص على كلمة «فقط»، ولا على بديل كسر البنية المؤكد، لذلك لا يثبت القاعدة العامة بصيغتها.
- ملفات المطابقة: E14؛ الاقتباسات: Q022.
- نوافذ الكلمات المفتاحية المطلوبة/المفتوحة: 1/1؛ ملفات النص المطابقة المفحوصة كاملة: 1/1.
- مقارنة المعرفات: لا يمكن تقرير المطابقة أو التعارض، لأن سجلات المعرفات المشار إليها غير موجودة في نسخة المستودع المتاحة.

### L14 — غير معثور عليه
- خلاصة المقارنة: لم ينتج فحص النص الكامل للملفين كلمات أو نافذة ذات صلة واضحة بإعادة دخول واحدة في الجلسة نفسها أو الخروج العاطفي أو SMT للأدوات غير المسماة؛ لا توجد عبارة اقتباس قابلة للإسناد.
- ملفات المطابقة: E04 + E21؛ الاقتباسات: لا يوجد اقتباس.
- نوافذ الكلمات المفتاحية المطلوبة/المفتوحة: 0/0؛ ملفات النص المطابقة المفحوصة كاملة: 2/2.
- مقارنة المعرفات: لا يمكن تقرير المطابقة أو التعارض، لأن سجلات المعرفات المشار إليها غير موجودة في نسخة المستودع المتاحة.

## سجل الاقتباسات ومواقعها

- **Q001، L01** — “intraday order flow and understanding the daily range” — `2022-ICT-Mentorship/2022-ICT-Mentorship-Episode-5-001.json`؛ المقطع 3–5، عند 17920 مللي ثانية؛ المتحدث: مايكل، بحسب سياق المحاضرة.
- **Q002، L01** — “be using it on a higher time frame charts like a monthly weekly or daily” — `2016-ICT-Private-Mentorship-Core-Content-Month-04/ICT-Mentorship-Core-Content-Month-04-Orderblocks-001.json`؛ المقطع 50–52، عند 155120 مللي ثانية؛ المتحدث: مايكل، بحسب سياق المحاضرة.
- **Q003، L02** — “see here one hour” — `2022-ICT-Mentorship/2022-ICT-Mentorship-Episode-12-001.json`؛ المقطع 164–165، عند 337600 مللي ثانية؛ المتحدث: مايكل، بحسب سياق المحاضرة.
- **Q004، L02** — “little lower than the hourly chart give me a little bit more context” — `2022-ICT-Mentorship/2022-ICT-Mentorship-Episode-13-001.json`؛ المقطع 468–469، عند 966720 مللي ثانية؛ المتحدث: مايكل، بحسب سياق المحاضرة.
- **Q005، L03** — “power three is accumulation manipulation distribution” — `2022-ICT-Mentorship/2022-ICT-Mentorship-Episode-10-001.json`؛ المقطع 377–379، عند 770560 مللي ثانية؛ المتحدث: مايكل، بحسب سياق المحاضرة.
- **Q006، L03** — “the news embargo lifts at this time at 8 30.” — `2022-ICT-Mentorship/2022-ICT-Mentorship-Episode-10-001.json`؛ المقطع 49–50، عند 103840 مللي ثانية؛ المتحدث: مايكل، بحسب سياق المحاضرة.
- **Q007، L04** — “we're looking for a displacement in price” — `2017-ICT-Private-Mentorship-Core-Content-Month-05/ICT-Mentorship-Core-Content-Month-05-Trade-Conditions-&-Setup-Progressions-001.json`؛ المقطع 18–19، عند 70140 مللي ثانية؛ المتحدث: مايكل، بحسب سياق المحاضرة.
- **Q008، L04** — “by waiting for a market structure shift here” — `2017-ICT-Private-Mentorship-Core-Content-Month-05/ICT-Mentorship-Core-Content-Month-05-Defining-Institutional-Swing-Points-001.json`؛ المقطع 459–460، عند 966880 مللي ثانية؛ المتحدث: مايكل، بحسب سياق المحاضرة.
- **Q009، L05** — “that sets your initial bias for the week on the daily chart” — `2022-ICT-Mentorship/2022-ICT-Mentorship-Episode-2-001.json`؛ المقطع 472–473، عند 992480 مللي ثانية؛ المتحدث: مايكل، بحسب سياق المحاضرة.
- **Q010، L05** — “you don't force it” — `2022-ICT-Mentorship/2022-ICT-Mentorship-Episode-3-001.json`؛ المقطع 57–57، عند 141599 مللي ثانية؛ المتحدث: مايكل، بحسب سياق المحاضرة.
- **Q011، L06** — “i discerned that understanding higher time frame charts and what you know now as a premium market” — `2016-ICT-Private-Mentorship-Core-Content-Month-02/ICT-Mentorship-Core-Content-Month-02-Market-Maker-Trap-False-Flag-001.json`؛ المقطع 54–56، عند 147360 مللي ثانية؛ المتحدث: مايكل، بحسب سياق المحاضرة.
- **Q012، L06** — “in a premium market relatives of a range” — `2016-ICT-Private-Mentorship-Core-Content-Month-02/ICT-Mentorship-Core-Content-Month-02-Market-Maker-Trap-False-Flag-001.json`؛ المقطع 348–348، عند 768880 مللي ثانية؛ المتحدث: مايكل، بحسب سياق المحاضرة.
- **Q013، L07** — “discount array which is the bullish daily order block” — `2022-ICT-Mentorship/2022-ICT-Mentorship-Episode-16-001.json`؛ المقطع 414–415، عند 858959 مللي ثانية؛ المتحدث: مايكل، بحسب سياق المحاضرة.
- **Q014، L07** — “the majority of your analysis should be framed on your daily chart” — `2022-ICT-Mentorship/2022-ICT-Mentorship-Episode-16-001.json`؛ المقطع 431–432، عند 895199 مللي ثانية؛ المتحدث: مايكل، بحسب سياق المحاضرة.
- **Q015، L08** — “it can really blow through whatever your stop loss is if especially if it's fomc” — `2017-ICT-Private-Mentorship-Core-Content-Month-07/ICT-Mentorship-Core-Content-Month-07-Short-Term-Trading-Market-Maker-Manipulation-Templates-001.json`؛ المقطع 852–853، عند 2036580 مللي ثانية؛ المتحدث: مايكل، بحسب سياق المحاضرة.
- **Q016، L09** — “in close proximity to this order block” — `2022-ICT-Mentorship/2022-ICT-Mentorship-Episode-7-001.json`؛ المقطع 596–596، عند 1211280 مللي ثانية؛ المتحدث: مايكل، بحسب سياق المحاضرة.
- **Q017، L10** — “avoid trading London open after fomc events that create whipsaw” — `2017-ICT-Private-Mentorship-Core-Content-Month-08/ICT-Mentorship-Core-Content-Month-08-When-To-Avoid-The-London-Session-001.json`؛ المقطع 119–120، عند 277620 مللي ثانية؛ المتحدث: مايكل، بحسب سياق المحاضرة.
- **Q018، L10** — “equilibrium could be an impactful level so you want to take something off there as well” — `2017-ICT-Private-Mentorship-Core-Content-Month-08/ICT-Mentorship-Core-Content-Month-08-High-Probability-Daytrade-Setups-001.json`؛ المقطع 424–426، عند 1044240 مللي ثانية؛ المتحدث: مايكل، بحسب سياق المحاضرة.
- **Q019، L11** — “details about how I finally narrowed down very tight small risk high yield setups” — `2017-ICT-Private-Mentorship-Core-Content-Month-07/ICT-Mentorship-Core-Content-Month-07-One-Shot-One-Kill-Model-001.json`؛ المقطع 70–72، عند 198540 مللي ثانية؛ المتحدث: مايكل، بحسب سياق المحاضرة.
- **Q020، L12** — “so i'm looking for expansion to the upside” — `2022-ICT-Mentorship/2022-ICT-Mentorship-Episode-26-Example-Of-Tape-Reading-Practice-001.json`؛ المقطع 75–76، عند 220159 مللي ثانية؛ المتحدث: مايكل، بحسب سياق المحاضرة.
- **Q021، L12** — “the buy side liquidity that's needed in blue” — `2022-ICT-Mentorship/2022-ICT-Mentorship-Episode-26-Example-Of-Tape-Reading-Practice-001.json`؛ المقطع 83–84، عند 237840 مللي ثانية؛ المتحدث: مايكل، بحسب سياق المحاضرة.
- **Q022، L13** — “i'm thinking if it runs there i'll take six off to fund the position roll the stops to even” — `2022-ICT-Mentorship/2022-ICT-Mentorship-Episode-14-001.json`؛ المقطع 80–82، عند 182640 مللي ثانية؛ المتحدث: مايكل، بحسب سياق المحاضرة.

## جرد الملفات المطابقة للعناوين
تُستخدم المجموعات التالية في صفوف الخلاصة؛ كل مسار هو ملف موجود فعلاً في مجموعة النصوص. للمدخلات الشهرية جُمعت كل الملفات في مجلد الشهر المشار إليه، لأن الإحالة لا تحدد عنوان درس منفرداً.

### E02 — 1 ملفاً
- `2022-ICT-Mentorship/2022-ICT-Mentorship-Episode-2-001.json`

### E03 — 2 ملفاً
- `2022-ICT-Mentorship/2022-ICT-Mentorship-Episode-3-001.json`
- `2022-ICT-Mentorship/2022-ICT-Mentorship-Episode-3-002.json`

### E04 — 1 ملفاً
- `2022-ICT-Mentorship/2022-ICT-Mentorship-Episode-4-001.json`

### E05 — 1 ملفاً
- `2022-ICT-Mentorship/2022-ICT-Mentorship-Episode-5-001.json`

### E07 — 2 ملفاً
- `2022-ICT-Mentorship/2022-ICT-Mentorship-Episode-7-001.json`
- `2022-ICT-Mentorship/2022-ICT-Mentorship-Episode-7-002.json`

### E08 — 1 ملفاً
- `2022-ICT-Mentorship/2022-ICT-Mentorship-Episode-8-001.json`

### E10 — 2 ملفاً
- `2022-ICT-Mentorship/2022-ICT-Mentorship-Episode-10-001.json`
- `2022-ICT-Mentorship/2022-ICT-Mentorship-Episode-10-002.json`

### E12 — 2 ملفاً
- `2022-ICT-Mentorship/2022-ICT-Mentorship-Episode-12-001.json`
- `2022-ICT-Mentorship/2022-ICT-Mentorship-Episode-12-002.json`

### E13 — 1 ملفاً
- `2022-ICT-Mentorship/2022-ICT-Mentorship-Episode-13-001.json`

### E14 — 1 ملفاً
- `2022-ICT-Mentorship/2022-ICT-Mentorship-Episode-14-001.json`

### E16 — 2 ملفاً
- `2022-ICT-Mentorship/2022-ICT-Mentorship-Episode-16-001.json`
- `2022-ICT-Mentorship/2022-ICT-Mentorship-Episode-16-002.json`

### E21 — 1 ملفاً
- `2022-ICT-Mentorship/2022-ICT-Mentorship-Episode-21-001.json`

### E26 — 1 ملفاً
- `2022-ICT-Mentorship/2022-ICT-Mentorship-Episode-26-Example-Of-Tape-Reading-Practice-001.json`

### M02 — 9 ملفاً
- `2016-ICT-Private-Mentorship-Core-Content-Month-02/ICT-Mentorship-Core-Content-Month-02-Framing-Low-Risk-Trade-Setups-001.json`
- `2016-ICT-Private-Mentorship-Core-Content-Month-02/ICT-Mentorship-Core-Content-Month-02-Growing-Small-Accounts-001.json`
- `2016-ICT-Private-Mentorship-Core-Content-Month-02/ICT-Mentorship-Core-Content-Month-02-How-To-Mitigate-Losing-Trades-Effectively-001.json`
- `2016-ICT-Private-Mentorship-Core-Content-Month-02/ICT-Mentorship-Core-Content-Month-02-How-Traders-Make-10%-Per-Month-001.json`
- `2016-ICT-Private-Mentorship-Core-Content-Month-02/ICT-Mentorship-Core-Content-Month-02-Market-Maker-Trap-False-Breakouts-001.json`
- `2016-ICT-Private-Mentorship-Core-Content-Month-02/ICT-Mentorship-Core-Content-Month-02-Market-Maker-Trap-False-Flag-001.json`
- `2016-ICT-Private-Mentorship-Core-Content-Month-02/ICT-Mentorship-Core-Content-Month-02-No-Fear-Of-Losing-001.json`
- `2016-ICT-Private-Mentorship-Core-Content-Month-02/ICT-Mentorship-Core-Content-Month-02-The-Secrets-To-Selecting-High-Reward-Setups-001.json`
- `2016-ICT-Private-Mentorship-Core-Content-Month-02/ICT-Mentorship-Core-Content-Month-02-The-Secrets-To-Selecting-High-Reward-Setups-002.json`

### M03 — 8 ملفاً
- `2016-ICT-Private-Mentorship-Core-Content-Month-03/ICT-Mentorship-Core-Content-Month-03-Institutional-Market-Structure-001.json`
- `2016-ICT-Private-Mentorship-Core-Content-Month-03/ICT-Mentorship-Core-Content-Month-03-Institutional-Order-Flow-001.json`
- `2016-ICT-Private-Mentorship-Core-Content-Month-03/ICT-Mentorship-Core-Content-Month-03-Institutional-Sponsorship-001.json`
- `2016-ICT-Private-Mentorship-Core-Content-Month-03/ICT-Mentorship-Core-Content-Month-03-Macro-Economic-To-Micro-Technical-001.json`
- `2016-ICT-Private-Mentorship-Core-Content-Month-03/ICT-Mentorship-Core-Content-Month-03-Market-Maker-Trap-Head-Shoulders-Pattern-001.json`
- `2016-ICT-Private-Mentorship-Core-Content-Month-03/ICT-Mentorship-Core-Content-Month-03-Market-Maker-Trap-Trendline-Phantoms-001.json`
- `2016-ICT-Private-Mentorship-Core-Content-Month-03/ICT-Mentorship-Core-Content-Month-03-The-Next-Setup-Anticipatory-Skill-Development-001.json`
- `2016-ICT-Private-Mentorship-Core-Content-Month-03/ICT-Mentorship-Core-Content-Month-03-Timeframe-Selection-&-Defining-Setups-001.json`

### M04 — 14 ملفاً
- `2016-ICT-Private-Mentorship-Core-Content-Month-04/ICT-Mentorship-Core-Content-Month-04-Divergence-Phantoms-001.json`
- `2016-ICT-Private-Mentorship-Core-Content-Month-04/ICT-Mentorship-Core-Content-Month-04-Double-Bottom-Double-Top-001.json`
- `2016-ICT-Private-Mentorship-Core-Content-Month-04/ICT-Mentorship-Core-Content-Month-04-ICT-Breaker-Block-001.json`
- `2016-ICT-Private-Mentorship-Core-Content-Month-04/ICT-Mentorship-Core-Content-Month-04-ICT-Fair-Value-Gaps-FVG-001.json`
- `2016-ICT-Private-Mentorship-Core-Content-Month-04/ICT-Mentorship-Core-Content-Month-04-ICT-Propulsion-Block-001.json`
- `2016-ICT-Private-Mentorship-Core-Content-Month-04/ICT-Mentorship-Core-Content-Month-04-ICT-Rejection-Block-001.json`
- `2016-ICT-Private-Mentorship-Core-Content-Month-04/ICT-Mentorship-Core-Content-Month-04-ICT-Vacuum-Block-001.json`
- `2016-ICT-Private-Mentorship-Core-Content-Month-04/ICT-Mentorship-Core-Content-Month-04-Interest-Rate-Effects-On-Currency-Trades-001.json`
- `2016-ICT-Private-Mentorship-Core-Content-Month-04/ICT-Mentorship-Core-Content-Month-04-Liquidity-Pools-001.json`
- `2016-ICT-Private-Mentorship-Core-Content-Month-04/ICT-Mentorship-Core-Content-Month-04-Liquidity-Voids-001.json`
- `2016-ICT-Private-Mentorship-Core-Content-Month-04/ICT-Mentorship-Core-Content-Month-04-Mitigation-Blocks-001.json`
- `2016-ICT-Private-Mentorship-Core-Content-Month-04/ICT-Mentorship-Core-Content-Month-04-Orderblocks-001.json`
- `2016-ICT-Private-Mentorship-Core-Content-Month-04/ICT-Mentorship-Core-Content-Month-04-Reclaimed-ICT-Orderblock-001.json`
- `2016-ICT-Private-Mentorship-Core-Content-Month-04/ICT-Mentorship-Core-Content-Month-04-Reinforcing-Liquidity-Concepts-&-Price-Delivery-001.json`

### M05 — 20 ملفاً
- `2017-ICT-Private-Mentorship-Core-Content-Month-05/ICT-Mentorship-Core-Content-Month-05-Defining-HTF-PD-Arrays-001.json`
- `2017-ICT-Private-Mentorship-Core-Content-Month-05/ICT-Mentorship-Core-Content-Month-05-Defining-Institutional-Swing-Points-001.json`
- `2017-ICT-Private-Mentorship-Core-Content-Month-05/ICT-Mentorship-Core-Content-Month-05-Defining-Open-Float-Liquidity-Pools-001.json`
- `2017-ICT-Private-Mentorship-Core-Content-Month-05/ICT-Mentorship-Core-Content-Month-05-How-To-Use-Bearish-Seasonal-Tendencies-In-HTF-Analysis-001.json`
- `2017-ICT-Private-Mentorship-Core-Content-Month-05/ICT-Mentorship-Core-Content-Month-05-How-To-Use-Bullish-Seasonal-Tendencies-In-HTF-Analysis-001.json`
- `2017-ICT-Private-Mentorship-Core-Content-Month-05/ICT-Mentorship-Core-Content-Month-05-How-To-Use-Intermarket-Analysis-001.json`
- `2017-ICT-Private-Mentorship-Core-Content-Month-05/ICT-Mentorship-Core-Content-Month-05-Ideal-Seasonal-Tendencies-001.json`
- `2017-ICT-Private-Mentorship-Core-Content-Month-05/ICT-Mentorship-Core-Content-Month-05-Interest-Rate-Differentials-001.json`
- `2017-ICT-Private-Mentorship-Core-Content-Month-05/ICT-Mentorship-Core-Content-Month-05-Limit-Order-Entry-Techniques-For-Long-Term-Traders-001.json`
- `2017-ICT-Private-Mentorship-Core-Content-Month-05/ICT-Mentorship-Core-Content-Month-05-Money-Management-001.json`
- `2017-ICT-Private-Mentorship-Core-Content-Month-05/ICT-Mentorship-Core-Content-Month-05-Open-Float-001.json`
- `2017-ICT-Private-Mentorship-Core-Content-Month-05/ICT-Mentorship-Core-Content-Month-05-Position-Trade-Management-001.json`
- `2017-ICT-Private-Mentorship-Core-Content-Month-05/ICT-Mentorship-Core-Content-Month-05-Qualifying-Trade-Conditions-With-10-Year-Yields-001.json`
- `2017-ICT-Private-Mentorship-Core-Content-Month-05/ICT-Mentorship-Core-Content-Month-05-Quarterly-Shifts-&-IPDA-Data-Ranges-001.json`
- `2017-ICT-Private-Mentorship-Core-Content-Month-05/ICT-Mentorship-Core-Content-Month-05-Stop-Entry-Techniques-For-Long-Term-Traders-001.json`
- `2017-ICT-Private-Mentorship-Core-Content-Month-05/ICT-Mentorship-Core-Content-Month-05-Trade-Conditions-&-Setup-Progressions-001.json`
- `2017-ICT-Private-Mentorship-Core-Content-Month-05/ICT-Mentorship-Core-Content-Month-05-Using-10-Year-Notes-In-HTF-Analysis-001.json`
- `2017-ICT-Private-Mentorship-Core-Content-Month-05/ICT-Mentorship-Core-Content-Month-05-Using-IPDA-Data-Ranges-001.json`
- `2017-ICT-Private-Mentorship-Core-Content-Month-05/ICT-Mentorship-Core-Content-Month-05-Using-IPDA-Data-Ranges-002.json`
- `2017-ICT-Private-Mentorship-Core-Content-Month-05/ICT-Mentorship-Core-Content-Month-05-Using-IPDA-Data-Ranges-003.json`

### M07 — 8 ملفاً
- `2017-ICT-Private-Mentorship-Core-Content-Month-07/ICT-Mentorship-Core-Content-Month-07-Intraweek-Market-Reversals-&-Overlapping-Models-001.json`
- `2017-ICT-Private-Mentorship-Core-Content-Month-07/ICT-Mentorship-Core-Content-Month-07-One-Shot-One-Kill-Model-001.json`
- `2017-ICT-Private-Mentorship-Core-Content-Month-07/ICT-Mentorship-Core-Content-Month-07-Short-Term-Trading-Blending-IPDA-Data-Ranges-&-PD-Arrays-001.json`
- `2017-ICT-Private-Mentorship-Core-Content-Month-07/ICT-Mentorship-Core-Content-Month-07-Short-Term-Trading-Defining-Weekly-Range-Profiles-001.json`
- `2017-ICT-Private-Mentorship-Core-Content-Month-07/ICT-Mentorship-Core-Content-Month-07-Short-Term-Trading-Low-Resistance-Liquidity-Runs-Part-1-001.json`
- `2017-ICT-Private-Mentorship-Core-Content-Month-07/ICT-Mentorship-Core-Content-Month-07-Short-Term-Trading-Low-Resistance-Liquidity-Runs-Part-2-001.json`
- `2017-ICT-Private-Mentorship-Core-Content-Month-07/ICT-Mentorship-Core-Content-Month-07-Short-Term-Trading-Market-Maker-Manipulation-Templates-001.json`
- `2017-ICT-Private-Mentorship-Core-Content-Month-07/ICT-Mentorship-Core-Content-Month-07-Short-Term-Trading-Using-Monthly-&-Weekly-Ranges-001.json`

### M08 — 8 ملفاً
- `2017-ICT-Private-Mentorship-Core-Content-Month-08/ICT-Mentorship-Core-Content-Month-08-Central-Bank-Dealers-Range-001.json`
- `2017-ICT-Private-Mentorship-Core-Content-Month-08/ICT-Mentorship-Core-Content-Month-08-Defining-The-Daily-Range-001.json`
- `2017-ICT-Private-Mentorship-Core-Content-Month-08/ICT-Mentorship-Core-Content-Month-08-Essentials-To-ICT-Daytrading-001.json`
- `2017-ICT-Private-Mentorship-Core-Content-Month-08/ICT-Mentorship-Core-Content-Month-08-High-Probability-Daytrade-Setups-001.json`
- `2017-ICT-Private-Mentorship-Core-Content-Month-08/ICT-Mentorship-Core-Content-Month-08-Integrating-Daytrades-With-HTF-Trade-Entries-001.json`
- `2017-ICT-Private-Mentorship-Core-Content-Month-08/ICT-Mentorship-Core-Content-Month-08-Intraday-Profiles-001.json`
- `2017-ICT-Private-Mentorship-Core-Content-Month-08/ICT-Mentorship-Core-Content-Month-08-Projecting-Daily-Highs-&-Lows-001.json`
- `2017-ICT-Private-Mentorship-Core-Content-Month-08/ICT-Mentorship-Core-Content-Month-08-When-To-Avoid-The-London-Session-001.json`

## حدود مقارنة المعرفات
جرى البحث في المستودع عند HEAD المتاح عن U0113–U0118 وU0119 وU0120 وK2C-012 وQ11-C05 وQ11-C06 وQ14-C02 وQ14-NF01 وQ15-NF01؛ لم يظهر أي تطابق. لذلك لم أختلق مضموناً لهذه المعرفات ولم أنسب لأي منها مطابقة أو تعارض. يلزم إتاحة نصوص/سجل تلك المعرفات قبل هذه المقارنة.

## التحقق القابل لإعادة التشغيل
شغّل: `python k6/verify_quotes.py --corpus-root /مسار/المجلد/المستخرج`، حيث يحتوي المسار مجلد `transcriptions` أو يكون هو نفسه مجلد `transcriptions`. النتيجة عند تنفيذ هذا التقرير: **22/22 اقتباس مطابق حرفياً**. ملف الاقتباسات هو `k6/K6_QUOTES.jsonl`؛ سجل الفحص الكبير محفوظ خارج المستودع، وبصمته مدونة في ملخص التنفيذ أدناه.

## ملخص فني
- بصمة الأرشيف: `4213e692f7c978dab8fe5ba124d34d887f17316c89d27bb2a7406fd3776f769d`.
- الأرشيف والنصوص المستخرجة والسجلات الكبيرة محفوظة خارج المستودع؛ لم تُنسخ corpus إلى Git.
- نتائج الحالات: 0 يؤيده، 13 شرط مختلف، 0 يناقض، 1 غير معثور عليه.
- لا تعديل على أي ملف محرك أو ملف محمي.
- بصمة سجل الفحص الخارجي `K6_REVIEW_LOG.txt`: `95c1588f8d211811f93dc552db436271329d6c494f8298248602692f3b44f0e7`.
