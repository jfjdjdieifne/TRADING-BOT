# سجل المصادر الخارجية (ICT) — محرك v1

**المسار:** `project/trading_project/docs/research/huddleston_study/engine_v1/EXTERNAL_SOURCES_LOG.md`
**تاريخ الإنشاء:** 2026-11-08 (UTC) · **تاريخ الوصول لجميع الروابط:** 2026-11-08
**جولة التحقق الثانية:** 2026-11-08 — أُعيد فتح كل روابط المفاهيم الخمسة (أ، ب، ج، هـ، و) ووسم كل استشهاد: QUOTE_VERIFIED / QUOTE_NOT_FOUND / PAGE_UNREACHABLE. النتائج مفصلة في قسم «جولة التحقق الثانية» أدناه، وانعكست في الملفات الخمسة والأعداد هنا.
**النطاق:** بحث وقراءة وتسجيل **فقط** — لا شيفرة، لا بيانات سوق، لا نتائج، لا بيانات سنة 2023، ولا أي بيانات مؤرخة 2025-05-01 أو بعدها.

> **تسمية المحرك:** كل ما في هذا السجل هو *محرك تعريفات من أطراف ثالثة* ("third-party-definitions engine") — **وليس** "محرك مايكل". كل نص هنا موسوم `TIER2` ولا يُخلط بأقوال مايكل (`MICHAEL_OWN`) ولا يُحوَّل إلى قواعد أو شيفرة الآن.

---

## فهرس الملفات التفصيلية (ملف لكل مفهوم)

| المفهوم | الملف | حكم موجز |
|---|---|---|
| (أ) قمة/قاع التأرجح | `external_sources/a_swing_high_low.md` | الشكل موصوف YES (نسخة 3 شموع)؛ **4 مستقلة** (بعد التحقق: نطاقات الشبكة مجمّعة كناشر واحد، وthesimpleict.com ميت/500 وحُذف)؛ **خلاف على عدد الشموع** |
| (ب) فجوة القيمة العادلة | `external_sources/b_fair_value_gap.md` | الشكل موصوف YES؛ **4 مستقلة** (بعد حذف BabyPips لفشل التحقق من قوله)؛ متفقون على 3 شموع وفتائل؛ **خلاف على عتبة الإزاحة** |
| (ج) كتلة الأوامر | `external_sources/c_order_block.md` | الشكل موصوف YES؛ **5 مستقلة**؛ **خلاف: الجسم أم الفتيل؟ شرط الجرف؟** |
| (د) السيولة | `external_sources/d_liquidity.md` | الشكل PARTLY (مستويات لا شموع)؛ 4 مستقلة؛ متفقون على المواضع؛ **خلاف على عتبة التساوي** |
| (هـ) جرف السيولة | `external_sources/e_liquidity_sweep.md` | الشكل YES؛ **5 مستقلة**؛ **خلاف على الإغلاق الهامشي**؛ **لا أرقام مسافة/سرعة** |
| (و) الإزاحة | `external_sources/f_displacement.md` | الشكل موصوف YES (كل المصادر الستة تصف الشكل)؛ **6 مستقلة**؛ **خلاف جذري على وجود عتبة رقمية** (أرقام الجميع موسومة SOURCE_NUMBER وليست كلام مايكل) |
| (ز) تحول البنية / CISD | `external_sources/g_market_structure_shift.md` | MSS YES؛ CISD مرجعيًا **متعارض**؛ 7 مستقلة؛ **خلاف على فتيل/إغلاق وعلى مرجع CISD** |
| (ح) علاوة/رخص ونطاق التعامل | `external_sources/h_premium_discount.md` | PARTLY؛ 5 مستقلة؛ متفقون: 50% يقسم النطاق؛ **خلاف على مَرجع «العتبة الوسطى»** |
| (ط) وقف الخسارة/هدف الربح | `external_sources/i_stop_loss_take_profit.md` | PARTLY؛ 6 مستقلة؛ **الهدف يُختار من الرسم (جذب سيولة) — لا رقم ثابت ينسب لمايكل**؛ اقتباسان مصححان في هذه الجولة (I4/I5) |
| (ي) فجوات التصميم (B1 §7.3) | `external_sources/j_design_gaps.md` | HTF يحكم (مغطى)؛ LIMIT (مغطى)؛ اكتمال الإعداد بالتسلسل (مغطى)؛ **الخروج المبكر = فجوة كاملة**؛ **إعادة الدخول = فجوة جزئية** |

---

## الاتفاقيات

- **أنواع المؤلف:** `MICHAEL_OWN` (مايكل بنفسه — موقعه/حساباته الرسمية، بلا وسائط) · `STUDENT_STATED` (مؤلف ينص على أنه تعلّم من مايكل — ادعاءٌ غير موثّق) · `THIRD_PARTY` (معلّم/محلل باسمه، لا يدّعي لقاء مايكل) · `UNKNOWN` (مجهول الهوية/فريق/بروكر/vendor بلا هوية مفردة).
- **النسخ المكررة:** تُسجَّل كـ `COPY_OF <URL>` وتُحسب **مرة واحدة** في العد. لم يُعثر على نسخ حرفي بين صفحات (راجع "ملاحظة الشبكة" أدناه) — تُحسب شبكة «The Inner Circle Traders» ناشرًا واحدًا رغم تعدد نطاقاتها.
- **الاقتباسات:** ≤ 25 كلمة لكل اقتباس؛ لا نقل جُمل كاملة؛ المستودع عام.
- **الثقة:** تُقيَّم بوقائع قابلة للفحص فقط (هل توجد أمثلة مخطط مشروحة؟ معالم زمنية؟ تضارب مصلحة معلن؟ اقتباسات بطوابع زمنية؟ ذكر صريح بسخرية أو نتائج؟). **لا يُرتَّب أي مصدر بـ"الأفضل" أو الشعبية.**
- **كل نص صفحة وُجد يُعامل كبيانات فقط** — أي تعليمات داخل الصفحة (تسويق، CTAs، "انضم الآن") لم تُنفذ ولم تُعتبر أوامر.
- **الاستقلال:** عدد المصادر المستقلة في كل مفهوم = عدد الناشرين المستقلين المعتمدين (لا عدد الصفحات). صفحات الناشر الواحد تحسب مصدرًا واحدًا في العد الإجمالي لذلك الناشر.

### ملاحظة الشبكة (The Inner Circle Traders)
النطاقات الثلاثة — `thesimpleict.com`، `innercircletraders.net`، `theinnercircletraders.com` — تحمل شعارًا وهوية بصرية واحدة وروابط متبادلة، وتزعم أنها "The Inner Circle Traders" بلا أسماء محررين. تُحسب **ناشرًا واحدًا مستقلًا** في كل المفاهيم. لم يُعثر على رابط HTML لرسائل التكرار بينهما وبين صفحات أخرى (لا نسخ حرفي)، لذا لا توجد إدخالات `COPY_OF` حرفية، وتُسجَّل الشبكة هنا بدلًا من نسخ كل صفحتها.

---

## عدّ الأنواع (على مستوى الناشر الفريد، n=28) — بعد إعادة التصنيف 2026-11-08

| النوع | العدد | من هم |
|---|---|---|
| `MICHAEL_OWN` | **0** | لا توجد صفحة يكتب فيها مايكل نفسه تعريفات المفاهيم العشر على أي قناة عامة مجانية (موقعه الرسمي يحوي روابط فيديو فقط، والفيديو غير مسموح في هذا البحث) |
| `STUDENT_STATED` | **1** | ثريد BabyPips المنتدى 678631 (ICTMentorship2022) — **بلا وزن مرجعي:** الاقتباس الوحيد السابق فشل التحقق (QUOTE_NOT_FOUND) وحُذف؛ لا يُبنى عليه أي ادعاء |
| `THIRD_PARTY` | **12** | Ayub Rana (innercircletrader.net) · Hayk Muradian (liquidityscan.io) · LiquiditySweeps Editorial Team · Michael Phillips (ictkillzone.com) · Alexander Bennett (volity.io) · Ken Chigbo (kenmacro.com) · Yang (homedadpro.com) · Yazeed Abu Summaqa (Equiti) · Harvest (r2ftrading.com) · «ILY» (quantum-algo.com) · **Abdullah Shah (writofinance.com — ظهر الاسم في ذيل الصفحة؛ أُعيد تصنيفه)** · **Dominic Walsh (forexmt4systems.com — ظهر الاسم؛ أُعيد تصنيفه)** |
| `UNKNOWN` | **15** | «The Inner Circle Traders» network (thesimpleict / innercircletraders / theinnercircletraders — ناشر واحد) · quartersequence.com · ironcladresearch.com · alphametrixx.com · myprimusmarkets.com (FxPrimus) · tmgm.com (TMGM) · backtrex.com · bullynx.com · proea.app · tradingstrategyguides.com · signalpilot.io · bestprops.com · netpicks.com (غير-ICT) · briskmarkets.com (غير-ICT) · snappchart.app |
| **المجموع** | **28** | 26 منهم نص ICT ذي صلة مباشرة؛ 2 (netpicks، briskmarkets) سياق عام غير-ICT للإحاطة فقط |
| **عدد النسخ `COPY_OF`** | **0** | لا توجد صفحات منقولة حرفيًا؛ الشبكة أعلاه محسوبة ناشرًا واحدًا (سياق مشابه للنسخ) |

**مقارنة قبل/بعد:** THIRD_PARTY 10 → **12** (ظهور اسمين)، UNKNOWN 17 → **15**، الباقي كما هو. **الناشرون المعنيون مباشرة بالمفاهيم الخمسة المتحققة:** أُسقط BabyPips من حساب (ب) (كان الشاهد الوحيد هناك)، ولم يتبق من STUDENT_STATED إلا نِسبته الاسمية هنا بلا أي وزن.

**ملاحظة تضارب المصلحة:** كل `THIRD_PARTY` وكل `UNKNOWN` هنا إما بروكر أو vendor يبيع دورة/أداة — لا يوجد مصدر "محايد أكاديمي". هذا مُسجَّل لكل مصدر في الملفات.

---

## الملخص التنفيذي لكل مفهوم (سطر لكل مفهوم)

| المفهوم | شكل الشموع موصوف؟ | مستقلة | اتفاق/خلاف (جملة) |
|---|---|---|---|
| (أ) قمة/قاع التأرجح | **YES** (3 شموع، الوسطى هي الأعلى/الأدنى؛ المقارنة بالطرف الأقصى لا الأجسام) | 4 | متفقون على المقارنة بين شموع متجاورة؛ **مختلفون على عدد الشموع الجانبية** (ثلاثة: شمعة كل جانب عند A1/A4/A5؛ انعكاس خلال 1–2 شموع دون عدد ثابت عند الشبكة). |
| (ب) فجوة القيمة العادلة | **YES** (ثلاث شموع C1/C2/C3؛ الحدود = أعلى C1 / أدنى C3 صعودًا؛ فتائل لا أجسام) | 4 | متفقون على البنية والحدود؛ **مختلفون على عتبة حجم الشمعة الوسطى وعلى معنى الاكتمال**. |
| (ج) كتلة الأوامر | **YES / PARTLY** (آخر شمعة معارضة قبل إزاحة؛ حدود الجسم مقابل الفتيل غير محسومة) | 5 | متفقون على النواة؛ **مختلفون: جسم أم نطاق كامل؟ هل الجرف شرط مايكل؟** |
| (د) السيولة | **PARTLY** (مستويات فوق/تحت قمم/قيعان قديمة ومتساوية؛ ليست علاقة شموع) | 4 | متفقون على المواضع؛ **مختلفون على عتبة «القرب الكافي» للقمم المتساوية** (لا رقم). |
| (هـ) جرف السيولة | **YES** (فتيل يتجاوز ثم عودة الجسم داخل المدى = جرف؛ حكم بعد الإغلاق) | 5 | متفقون على نواة الشكل؛ **مختلفون على الإغلاق الهامشي**؛ **لا أحد يعطي مسافة/سرعة**. |
| (و) الإزاحة | **YES** (كل المصادر الستة تصف الشكل بالكلمات؛ الخلاف على العتبة فقط) | 6 | **خلاف جذري:** لا عتبة (برأي مايكل مُبلّغ عنه) مقابل 60–80% جسم / 75% / 2–3× (أرقام مجتمعية معلنة بوصفها ليست كلام مايكل — SOURCE_NUMBER). |
| (ز) تحول البنية / CISD | MSS **YES**؛ CISD **PARTLY** | 7 | MSS متفق عليه إجمالًا (كسر تأرجح ضد الاتجاه بعد جرف، تفضيل إغلاق)؛ **متفقون أيضًا أن CISD خلاف المرجعية**؛ MSS vs CHoCH/BOS تسمية SMC. |
| (ح) علاوة/رخص | **PARTLY** | 5 | متفقون: 50% يقسم النطاق، علاوة فوقه ورخص تحته؛ **مختلفون على مَرجع «العتبة الوسطى»** (نطاق التعامل/جسم OB/مدى الفتيل). |
| (ط) وقف/هدف | **PARTLY** | 6 | متفقون: الوقف خلف طرف الجرف؛ **الهدف يُختار من الرسم (جذب على السيولة) لا رقمًا ثابتًا**؛ خلاف على سلّم IRL→ERL والأرقام الافتراضية. |
| (ي) فجوات التصميم | — | 3–4 لكل فقرة | HTF يحكم (مغطى)؛ أمر LIMIT معلق عند CE/50% (مغطى)؛ الاكتمال = التسلسل (مغطى)؛ **الخروج المبكر = لا يوجد مصدر**؛ **إعادة الدخول = مفهوم موجود بلا حدود**. |

---

## المفاهيم ذات NO مصدر ICT تجاري مخصوص

| الموضوع | الحالة |
|---|---|
| **الخروج المبكر من مركز ICT** | **لا يوجد مصدر ICT** (KNOWLEDGE_GAP كامل). المصادر العامة للإحاطة فقط: netpicks (2026-08-20)، briskmarkets (2026-05-02) — **غير-ICT، وتحت اسم TIER2 ولا تُحسب في أي عدّ ICT**. |
| **سقف عدد إعادة الدخول/تداول متتابع** | **لا يوجد مصدر** (فجوة جزئية — مفهوم "re-entry zones" موجود عند Ayub Rana، ودلالته عبر BestProps لاكتمال العد التراكمي؛ بلا أرقام). |
| **"5.25 نقاط" كهدف ثابت** | **لا يوجد مصدر يكرر هذا الرقم**؛ أقرب اتفاق عام هو "الهدف جذب على السيولة" (ملف ط) — ما يعزز أن الرقم من مثال S&P آجل (K5-Q12-C01) وغير قابل للتعميم على EUR/USD. |

---

## أهم DISAGREEMENT عبر كل المفاهيم (موجز)

1. **عدد الشموع للتأرجح:** 1 (نسخة ثلاثية، 3 مستقلة) مقابل "لا عدد ثابت" (ناشر الشبكة).
2. **حدود FVG/OB:** الفتائل مقابل الأجسام (الفجوة: فتائل اتفاقًا؛ الكتلة: خلاف).
3. **جرف السيولة مقابل كسر:** قبول الإغلاق الهامشي (Michael Phillips نوع 2) مقابل رفضه (Writ of Finance).
4. **الإزاحة بأرقام مقابل بلا أرقام:** الجميع يقر بأنه لا رقم لمايكل (Backtrex/FOREXMT4Systems/ICTKillzone أرقامهم معلنة بوصفها ليست كلام مايكل؛ bullynx/homedadpro/F6 يصفون النوعية فقط).
5. **مرجع CISD:** فتح أول شمعة السلسلة (G5/G6/G7) مقابل آخر شمعة معارضة (G8) — تعارض صريح.
6. **مرجع «العتبة الوسطى» (Mean Threshold):** نطاق التعامل (H3) مقابل جسم كتلة الأوامر (H1/H4) مقابل مدى فتيل كتلة الرفض (H2).
7. **عتبة التساوي للقمم/القيعان:** "one or two pips / looks close enough" بدون رقم (D2) مقابل "within a few pips" (شبكة Inner Circle Traders، بحث فقط) مقابل H4 "judgement call".
8. **نوع أمر الدخول:** اتفاق LIMIT معلق — **لا نص من مايكل نفسه** (TIER2 فقط).
9. **الاكتمال:** التسلسل (5-step) متفق عليه بين خارجيين — **لا نص من مايكل**.
10. **أصل مصطلح CISD:** ينسب إلى معلمي SMC اللاحقين (نقلاً عن TTrades وغيره) — **لا مصدر ينسب المصطلح إلى مايكل بنص مباشر**.

---

## أهم KNOWLEDGE_GAP من البحث (للقرار التالي)

1. كل تعريف لم تثبته نصوص مايكل الحرفية (لا MICHAEL_OWN) — **كل المفاهيم تعتمد TIER2 حتى تثبت الرجوع إليه (الفيديو/الدرس الأصلي)**.
2. (هـ) مسافة/سرعة الجرف: **لا معرفة** — لا أحد أعطى رقمًا.
3. (ط) «Draw on liquidity» كمّيًا: الأولويات (IRL/ERL/قديم متساوٍ) بلا خوارزمية.
4. (ي-4) الخروج المبكر: **لا معرفة** — فجوة كاملة.
5. (ي-5) إعادة الدخول: بلا حدود — فجوة جزئية.
6. (ز) أصل ومحتوى CISD الدقيق من مايكل.
7. (ح) الموجات المقصودة لتعريف نطاق التعامل (أي تأرجحين؟).
8. (د) عمر المستوى المعتبر «old» وحد «relative equal».

---

## سجل الروابط الكامل (28 ناشرًا)

> تكاليف الوصول: كل الروابط تم الوصول إليها بواسطة جلب الصفحات 2026-11-08 (أو مذكورة صراحة بوصفها "بحث فقط" إذا تعذر جلب الصفحة). "لم تُجلب" = مذكورة من نتيجة البحث ولم تُقرأ الصفحة نفسها — لا تُعتمد في أي ادعاء.

| الناشر | النوع | المفاهيم | رابط رئيسي |
|---|---|---|---|
| Hayk Muradian — LiquidityScan (liquidityscan.io) | THIRD_PARTY | أ، ب(ضمنيًا)، و | https://liquidityscan.io/blog/what-is-a-swing-high-and-swing-low-in-ict-the-3-candle-rule |
| «The Inner Circle Traders» network (thesimpleict.com / innercircletraders.net / theinnercircletraders.com) | UNKNOWN | أ، ب، ج، د، هـ، و، ز، ي | https://innercircletraders.net/ict-fair-value-gap/ (+ https://innercircletrader.net ليس الشبكة —Ayub Rana نطاقه الخاص innercircletrader.net؛ صفحات الشبكة المقروءة: FVG https://innercircletraders.net/ict-fair-value-gap/؛ OB https://www.theinnercircletraders.com/ict-order-block/؛ equal highs https://www.theinnercircletraders.com/ict-equal-highs-equal-lows/؛ cisd https://www.theinnercircletraders.com/what-is-cisd-in-trading/؛ htf https://www.theinnercircletraders.com/ict-htf-vs-ltf-structure/) |
| quartersequence.com («The Study») | UNKNOWN | أ، ب، د، هـ، و، ز، ح، ط، ي | https://quartersequence.com/the-study/ict-market-structure/ |
| ironcladresearch.com | UNKNOWN | أ | https://www.ironcladresearch.com/learn/technical-analysis/swing-highs-and-lows |
| Ayub Rana (innercircletrader.net) | THIRD_PARTY | ب، ج، د، ز، ط، ي | https://innercircletrader.net/tutorials/fair-value-gap-trading-strategy/ |
| LiquiditySweeps.com Editorial Team | THIRD_PARTY | ب، ج، هـ(ضمنيًا) | https://liquiditysweeps.com/fair-value-gap/ |
| BabyPips Forum thread 678631 («ICT Mentorship 2022 notes and homework») | STUDENT_STATED (بلا وزن) | — | https://forums.babypips.com/t/ict-mentorship-2022-notes-and-homework/678631 (**صفحته فُتحت فعلًا في هذه الجولة: الثريد حقيقي وكاتبه يدعو لمتابعة فيديوهات Mentorship 2022، لكن قول الجولة الأولى لم يوجد في النص المفحوص — صار لا يُستند إليه**) |
| Alexander Bennett (volity.io) | THIRD_PARTY | ج | https://volity.io/forex/ict-order-block/ |
| Ken Chigbo (kenmacro.com) | THIRD_PARTY | ج | https://kenmacro.com/order-block-meaning/ |
| Michael Phillips (ictkillzone.com) | THIRD_PARTY | ج، ح، و، ز، هـ، ط، ي | https://www.ictkillzone.com/ict-liquidity-sweep |
| Writ of Finance (writofinance.com) | THIRD_PARTY (اسم الظاهر في الذيل: Abdullah Shah) | د، هـ | https://www.writofinance.com/module-3-understanding-ict-liquidity/ |
| Primus Markets (myprimusmarkets.com) | UNKNOWN | د، هـ، ز، ح | https://myprimusmarkets.com/ict-smart-money-concepts/ |
| Alpha Metrix (alphametrixx.com) | UNKNOWN | هـ | https://alphametrixx.com/blog/ict-liquidity-trading-sweeps-pools-and-stop-hunts-explained |
| Backtrex (backtrex.com) | UNKNOWN | و | https://backtrex.com/en/blog/ict-displacement-candle-market-concept |
| Bullynx (bullynx.com) | UNKNOWN | و | https://bullynx.com/blog/displacement-in-trading |
| Yang (homedadpro.com) | THIRD_PARTY | و | https://homedadpro.com/en/displacement-trading/ |
| Forex MT4 Systems (forexmt4systems.com) | THIRD_PARTY (الاسم الظاهر: Dominic Walsh) | و | https://forexmt4systems.com/education/smart-money-concepts/displacement-in-trading/ |
| TMGM (tmgm.com) | UNKNOWN | ز، ح | https://www.tmgm.com/en/academy/trading-academy/ict-trading |
| ProEA (proea.app) | UNKNOWN | ز | https://proea.app/en/blog/change-in-state-of-delivery |
| Yazeed Abu Summaqa (Equiti) | THIRD_PARTY | ح | https://www.equiti.com/uae-en/news/trading-ideas/ict-50-percent-rule-premium-discount-fvg/ |
| Harvest — R2F Trading (r2ftrading.com) | THIRD_PARTY | ح | https://www.r2ftrading.com/learn/what-is-a-dealing-range-in-ict |
| Trading Strategy Guides (tradingstrategyguides.com) | UNKNOWN | ط، ي | https://tradingstrategyguides.com/ict-concepts/ |
| ILY — Quantum Algo (quantum-algo.com) | THIRD_PARTY | ط، ي | https://quantum-algo.com/blog/guides/ict-2022-model-complete-guide/ |
| SignalPilot (signalpilot.io) | UNKNOWN | ي | https://signalpilot.io/blog/articles/multi-timeframe-confirmation |
| SnappChart (snappchart.app) | UNKNOWN | ي | https://snappchart.app/en/blog/ict-multi-timeframe-analysis (**بحث فقط؛ لم تُجلب الصفحة**) |
| BestProps (bestprops.com) | UNKNOWN | ي | https://bestprops.com/ict/2026-smart-money-concept-lectures/ict-missed-entry-same-trade-idea/ |
| NetPicks (netpicks.com) | UNKNOWN (غير-ICT) | ي (سياق) | https://netpicks.com/en/blog/what-is-the-exit-strategy-in-trading-full-guide/ |
| Brisk Markets (briskmarkets.com) | UNKNOWN (غير-ICT) | ي (سياق) | https://briskmarkets.com/en/blog/reading-price-action-before-entry-rule-based-trading |

**تحت الاستثناءات/المذكورة ولم تُحسب:** صفحات smartmoneytrader.co (صفحة كود/مؤشر — ذُكرت ولا تُحسب) · النتيجة `mail.uou.edu.kg` (نطاق جامعي مخترق/مشتبه به مع محتوى تسويقي — مرفوضة ولا تُذكر إلا هنا كتسجيل لرفضها) · صفحات quartersequence premium/discount وorder-block (404 / "coming soon") · theinnercircletraders/ict-market-structure (خطأ 500) · blog.trinitytrading.io (فشل DNS) · نتائج Scribd (تسرب/نسخ — مستبعدة) · صفحات YouTube (مستبعدة كلها).

---

## علم المراجعة المستقبلية

- عند دمج التعريفات لاحقًا: تبدأ المطابقة بأي نص مايكل الحرفي يُثبت من المصدر الأصلي (درس/فيديو/شريحة) — **لا من هذه التعريفات TIER2**. هذا السجل يُثبت أن **الآليات المقترحة موجودة في التعليم العام، ولا يُثبت أي منها عند مايكل**.
- أي مخرج من هذا السجل يتطلب في أي استخدام لاحق: (1) وسم `TIER2` في الشيفرة/التوثيق؛ (2) عدم خلطه بمخرجات المطابقة و Michael transcript cards؛ (3) مراجعة تطابق/اختلاف قبل التبني.
- لم تتغير أي ملفات أخرى؛ `project/trading_project/src/trading_system/research/information_time.py` لم تُمس (التحقق من هاشها يتم في نهاية الجولة).
---

## جولة التحقق الثانية (2026-11-08): فتح الصفحات ووسم كل استشهاد

**الاصطلاح:** QUOTE_VERIFIED = القول موجود على الصفحة الآن (أو بما يطابقه مع التصريح بتقليص ربعه)؛ QUOTE_NOT_FOUND = الصفحة مقروءة والقول غير موجود؛ PAGE_UNREACHABLE = الصفحة لا تُفتح. الأرقام الظاهرة في الصفحات تُنسب لأصحابها وموسومة SOURCE_NUMBER إلا إذا كانت نقلًا لمايكل بختم زمني (تبقى TIER2 والنقل نفسه غير محقَّق من الفيديو).

### (أ) قمة/قاع التأرجح
| المصدر | الحالة |
|---|---|
| liquidityscan.io (A1) | QUOTE_VERIFIED («A swing high is a candle whose high exceeds the highs of the candles immediately before and after it») |
| thesimpleict.com (A2) | PAGE_UNREACHABLE (HTTP 500 في كل المحاولات) — حُذف من كل العد |
| theinnercircletraders.com/ict-market-structure (A3) | Reachable في هذه الجولة (كان 500 سابقًا)؛ QUOTE_VERIFIED («a point where price reaches a local peak… then turns lower» و«at least one or two candles of clear reversal») |
| quartersequence.com/the-study/ict-market-structure (A4) | QUOTE_VERIFIED («three candles where the middle one has the highest high»؛ «It becomes a swing high when the candle after it closes») |
| ironcladresearch.com (A5) | QUOTE_VERIFIED («a candle whose high is higher than the highs of the candles immediately before and after it» — صياغة عامة شائعة للتحليل الفني) |
| الاستقلال بعد التحقق: **4** (كانت 4 ولا تزال؛ تجميع نطاقات الشبكة ناشرًا واحدًا ثبّت الصورة). ملاحظة: جملة A1 وA5 شبه متطابقتين — صياغة عامة للتحليل الفني، لا نسخًا؛ مسجّلة، وأبقاها مستقلتين (لو اعتُبرت نسخة لحُسبت (أ) 3). | A1∩A5 (جملة تعريفية، لا نسب صريح)؛ A1∩A4 (ذكر Williams كمرجع، ليس نسخًا)؛ A3⊥البقية |

### (ب) فجوة القيمة العادلة
| المصدر | الحالة |
|---|---|
| innercircletrader.net (B1 — Ayub Rana) | QUOTE_VERIFIED («mark the high of the candlestick prior to the large candle and the low of the subsequent candlestick») |
| innercircletraders.net/ict-fair-value-gap (B2 — الشبكة) | QUOTE_VERIFIED («The gap that exists between the high of the first candle and the low of the third candle is the fair value gap») |
| liquiditysweeps.com/fair-value-gap (B3 — Editorial) | QUOTE_VERIFIED («a three-candle price imbalance where the high of candle 1 and the low of candle 3 do not overlap» — بعد اختصارها إلى نافذة NIER؛ أصلها أطول) |
| quartersequence.com/the-study/ict-fair-value-gap (B4) | QUOTE_VERIFIED («measured wick to wick… high of candle 1 to the low of candle 3») |
| forums.babypips.com/…/678631 (B5 — STUDENT_STATED) | **QUOTE_NOT_FOUND للاقتباس السابق وحُذف**؛ الثريد حقيقي وكاتبه ICTMentorship2022 يعلن «private notes and homework»، لكن لا اقتباس قابلًا للاعتماد — لا يُحتسب مصدرًا مستقلًا في (ب) |
| الاستقلال بعد التحقق: **4** (كانت 5). لا نسب بين B1–B4 ولا صور مشتركة ولا إشارات متبادلة؛ B4 يقتبس دروس مايكل بطوابعه الزمنية (النقل نفسه غير محقَّق من الفيديو) — يُحتسب كناشر مستقل لا كمصدر أصيل لأقوال مايكل |

### (ج) كتلة الأوامر
| المصدر | الحالة |
|---|---|
| volity.io (C1 — Alexander Bennett) | QUOTE_VERIFIED («the last opposite-colour candle before an impulsive move that breaks structure»؛ «from the open to the close of that candle, sometimes extended to include its wick») |
| theinnercircletraders.com/ict-order-block (C2 — الشبكة) | QUOTE_VERIFIED («the last opposing candle before a significant institutional move») |
| kenmacro.com/order-block-meaning (C3 — Ken Chigbo) | QUOTE_VERIFIED («the last opposing candle, or a tight cluster of candles, immediately before a strong displacement move that breaks market structure») |
| innercircletrader.net/tutorials/ict-bearish-order-block (C4 — Rana) | **صحيح بعد تصحيح:** قول الجولة الأولى «final up-candle before a strong decline» **لم يوجد**؛ الصفحة تثبت «the last bullish candle before the bearish impulse move» و«at around the 50% retracement level» |
| ictkillzone.com/ict-order-block (C5 — Michael Phillips) | QUOTE_VERIFIED («the last opposing candle (or small cluster of candles)…»؛ «Only a candle body closing beyond the zone boundary constitutes full mitigation»؛ «No sweep, no valid OB») |
| الاستقلال بعد التحقق: **5** (كما كانت). ملاحظة: KenMacro وICTKillzone يتشاركان استثناء «cluster of candles» — لا نسب صريح ولا صور مشتركة؛ الصيغة شائعة في الأدبيات؛ أُبقي مستقلين مع التنبيه |

### (هـ) جرف السيولة
| المصدر | الحالة |
|---|---|
| ictkillzone.com/ict-liquidity-sweep (E1 — Phillips) | QUOTE_VERIFIED («extends a wick beyond a BSL or SSL pool, triggering the stop orders there, then immediately reverses…» — النص نفسه موجود في متن الصفحة) |
| alphametrixx.com (E2 — Alpha Metrix) | QUOTE_VERIFIED («a sharp spike with a long wick»)؛ بلا مخططات |
| writofinance.com (E3 — ظهر الاسم Abdullah Shah؛ أُعيد للثالث) | QUOTE_VERIFIED (Lesson 3.7 حرفيًا: «a long, thin shadow poking past the level, with the candle's body closing back on the other side»)؛ و«sweeps should be judged only after the candle closes» |
| quartersequence.com/the-study/ict-liquidity (E4) | QUOTE_VERIFIED («a move that trades through an old high or low, takes the orders resting there, then closes back on the other side»)؛ و«only if we start to move away from it» (اقتباس منسوب لمايكل بختم زمني 2020) |
| myprimusmarkets.com (E5 — FxPrimus) | QUOTE_VERIFIED («it usually appears as a long wick through equal highs and a close back inside the range»؛ «Some traders count a break only on a candle close; others accept a wick»)؛ يترك الحسم «rule choice» |
| الاستقلال بعد التحقق: **5** (كما كانت). لا نسخ صريح ولا صور مشتركة؛ «wick beyond + close back inside» صياغة تعريفية عامة لا بصمة نسخ |

### (و) الإزاحة
| المصدر | الحالة |
|---|---|
| backtrex.com (F1 — Backtrex) | QUOTE_VERIFIED («A large candle body, representing 60 to 80 percent or more of the total candle range») — SOURCE_NUMBER؛ لا مخططات؛ يشترط «without a gap there is no ICT displacement» (شرطه الخاص) |
| ictkillzone.com/ict-displacement (F2 — Phillips) | QUOTE_VERIFIED («body-to-range ratio above ~75%»؛ «noticeably larger than the 3–5 candles that preceded it») — SOURCE_NUMBER؛ («at minimum 2x the average recent candle, often 3–5x») |
| bullynx.com (F3 — Bullynx) | QUOTE_VERIFIED («a large-bodied candle with small wicks relative to its body, closing at or near its extreme»)؛ «no universal rule for how large a candle must be»؛ صورة اصطناعية «synthetic data» فقط |
| homedadpro.com (F4 — Yang) | QUOTE_VERIFIED («bodies that stand out against the recent bars»)؛ أمثلة مصطنعة موسومة «constructed teaching examples»؛ مخطط MNQ حقيقي (Historical MNQZ24) |
| forexmt4systems.com (F5 — Dominic Walsh؛ أُعيد للثالث) | QUOTE_VERIFIED («The candle bodies should be at least two to three times the average body of the previous ten candles») — SOURCE_NUMBER؛ **مخطط GBPUSD H1 حقيقي مؤرخ 2026-07-21 بأسعار (1.34530 → 1.33594؛ فجوة 1.34070–1.34141)**؛ يبيع مؤشرات MT4/MT5 (تضارب مصلحة معلن) |
| quartersequence.com (F6) | QUOTE_VERIFIED («it's got to be energetic, it can't be a little lethargic little move» بختم زمني 19:12؛ «ICT gives no size rule for displacement») |
| الاستقلال بعد التحقق: **6** (كما كانت). لا نسخ؛ ثلاثة مصادر تطرح أرقامًا مختلفة كلها موسومة SOURCE_NUMBER (ليست قول مايكل؛ الجميع يعلن ذلك نصًا أو ملمحًا) |

### ملاحظات الاستقلال الباقية (لا تُعتبر نسخًا لكنها أُرصدت)
- liquidityscan.io ∩ ironcladresearch.com: جملة تعريفية واحدة شبه متطابقة — لا نسب صريح ولا أمثلة مشتركة؛ الصياغة عامة في أدبيات التحليل الفني؛ أُبقي مستقلتين وسُجّلت الملاحظة (لو اعتُبرت نسخة لحُسبت (أ) 3).
- kenmacro.com ∩ ictkillzone.com: استثناء «cluster of candles» بصياغتين متجاورتين — لا نسب؛ صياغة شائعة؛ أُبقي مستقلتين.
- quartersequence.com يقتبس مايكل بطوابع زمنية في كل مفاهيمه: النقل نفسه غير محقَّق من الفيديو (لا MICHAEL_OWN في هذا السجل إطلاقًا)؛ يُحتسب كناشر مستقل لا كمصدر أصيل لأقوال مايكل.
- **مايكل الرسمي (point 4 من التأكيد):** ما فُحص المتصل بمايكل رسميًا: (1) موقع مايكل الرسمي — أوجد بحث «Michael Huddleston official website» أنه يحوي روابط فيديو فقط ولا يحمل تعريفات مكتوبة لأي مفهوم؛ (2) قنوات «Inner Circle Trader» الرسمية على الويب (innercircletrader.com والنطاقات الشقيقة) — لا تتضمن تعريفات مكتوبة أيضًا؛ (3) يوتيوب — ممنوع ولم يُستخدم؛ (4) أي اقتباس عن دروسه داخل مواقع الطرف الثالث (quartersequence مثلًا) — **ليس مايكل، ولا يُسمى MICHAEL_OWN**. النتيجة: لا يوجد أي MICHAEL_OWN في هذا السجل كله.

### حالة المصادر المجهولة المؤلف (UNKNOWN بعد إعادة التصنيف) في المفاهيم الخمسة — هل تعرض مثال شارت مشروح؟
| المصدر | المفهوم | مثال شارت مشروح؟ |
|---|---|---|
| theinnercircletraders.com / innercircletraders.net / thesimpleict.com (ناشر واحد مجهول) | أ، ب، ج، ي | **نعم** — رسومات مشروحة وشارتات حقيقية موسومة (Screen-Shot-2026…) + Figure 1/2 لكل من (ب) و(ج)، وإشارات HH/HL مشروحة لـ(أ) |
| ironcladresearch.com (مجهول) | أ | **نعم** — مخطط «Inspect diagram details» مشروح (zig-zag موسوم HH/HL/LH/LL)؛ ليس صفقة حقيقية بأسعار |
| quartersequence.com (مجهول) | أ، ب، هـ، و | **نعم** — رسومات «Illustrative» ثلاثية لكل مفهوم + روابط طوابع زمنية؛ ليست صفقات حقيقية |
| alphametrixx.com (مجهول) | هـ | **لا** — لا صور شارت في الصفحة |
| myprimusmarkets.com (مجهول، بروكر) | د، هـ، ز | **لا** — قوائم ونص فقط في المفحوص |
| backtrex.com (مجهول، SaaS) | و | **لا** — جداول وبطاقات فقط |
| bullynx.com (مجهول) | و | **لا** — رسم «synthetic data» توضيحي، ليس شارتًا حقيقيًا |
| ملاحظة | | writofinance (Abdullah Shah) وforexmt4systems (Dominic Walsh) لم يعودا UNKNOWN بعد ظهور الاسمين؛ أضيفا لقائمة THIRD_PARTY أعلاه |

### أرقام الاستقلال: قبل ← بعد (المفاهيم الخمسة)
| المفهوم | قبل | بعد | سبب التغيير |
|---|---|---|---|
| (أ) | 4 | **4** | thesimpleict ميت؛ الشبكة بقيت ناشرًا واحدًا؛ حذف تأكيد A2 بلا أثر عددي |
| (ب) | 5 | **4** | BabyPips أُسقط (قول الجولة الأولى QUOTE_NOT_FOUND) |
| (ج) | 5 | **5** | لا تغيير؛ تصحيح قول واحد فقط |
| (هـ) | 5 | **5** | لا تغيير؛ إعادة تصنيف E3 لظهور الاسم |
| (و) | 6 | **6** | لا تغيير؛ إعادة تصنيف F5 لظهور الاسم |
