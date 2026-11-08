# سجل المصادر الخارجية (ICT) — محرك v1

**المسار:** `project/trading_project/docs/research/huddleston_study/engine_v1/EXTERNAL_SOURCES_LOG.md`
**تاريخ الإنشاء:** 2026-11-08 (UTC) · **تاريخ الوصول لجميع الروابط:** 2026-11-08
**النطاق:** بحث وقراءة وتسجيل **فقط** — لا شيفرة، لا بيانات سوق، لا نتائج، لا بيانات سنة 2023، ولا أي بيانات مؤرخة 2025-05-01 أو بعدها.

> **تسمية المحرك:** كل ما في هذا السجل هو *محرك تعريفات من أطراف ثالثة* ("third-party-definitions engine") — **وليس** "محرك مايكل". كل نص هنا موسوم `TIER2` ولا يُخلط بأقوال مايكل (`MICHAEL_OWN`) ولا يُحوَّل إلى قواعد أو شيفرة الآن.

---

## فهرس الملفات التفصيلية (ملف لكل مفهوم)

| المفهوم | الملف | حكم موجز |
|---|---|---|
| (أ) قمة/قاع التأرجح | `external_sources/a_swing_high_low.md` | الشكل موصوف YES (نسخة 3 شموع)؛ 4 مستقلة؛ **خلاف على عدد الشموع** |
| (ب) فجوة القيمة العادلة | `external_sources/b_fair_value_gap.md` | الشكل موصوف YES؛ 5 مستقلة؛ متفقون على 3 شموع وفتائل؛ **خلاف على عتبة الإزاحة** |
| (ج) كتلة الأوامر | `external_sources/c_order_block.md` | الشكل موصوف YES؛ 5 مستقلة؛ **خلاف: الجسم أم الفتيل؟ شرط الجرف؟** |
| (د) السيولة | `external_sources/d_liquidity.md` | الشكل PARTLY (مستويات لا شموع)؛ 4 مستقلة؛ متفقون على المواضع؛ **خلاف على عتبة التساوي** |
| (هـ) جرف السيولة | `external_sources/e_liquidity_sweep.md` | الشكل YES؛ 5 مستقلة؛ **خلاف على الإغلاق الهامشي**؛ **لا أرقام مسافة/سرعة** |
| (و) الإزاحة | `external_sources/f_displacement.md` | الشكل PARTLY→YES؛ 6 مستقلة؛ **خلاف جذري على وجود عتبة رقمية** |
| (ز) تحول البنية / CISD | `external_sources/g_market_structure_shift.md` | MSS YES؛ CISD مرجعيًا **متعارض**؛ 7 مستقلة؛ **خلاف على فتيل/إغلاق وعلى مرجع CISD** |
| (ح) علاوة/رخص ونطاق التعامل | `external_sources/h_premium_discount.md` | PARTLY؛ 5 مستقلة؛ متفقون: 50% يقسم النطاق؛ **خلاف على مَرجع «العتبة الوسطى»** |
| (ط) وقف الخسارة/هدف الربح | `external_sources/i_stop_loss_take_profit.md` | PARTLY؛ 6 مستقلة؛ **الهدف يُختار من الرسم (جذب سيولة) — لا رقم ثابت ينسب لمايكل** |
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

## عدّ الأنواع (على مستوى الناشر الفريد، n=28)

| النوع | العدد | من هم |
|---|---|---|
| `MICHAEL_OWN` | **0** | لا توجد صفحة يكتب فيها مايكل نفسه تعريفات المفاهيم العشر على أي قناة عامة مجانية (موقعه الرسمي يحوي روابط فيديو فقط، والفيديو غير مسموح في هذا البحث) |
| `STUDENT_STATED` | **1** | ثريد BabyPips المنتدى 678631 (معلنون بأنهم يتعلمون من دورات مايكل؛ مجهولون؛ **تُوصف صراحةً بأنها غير موثقة**) |
| `THIRD_PARTY` | **10** | Ayub Rana (innercircletrader.net) · Hayk Muradian (liquidityscan.io) · LiquiditySweeps Editorial Team · Michael Phillips (ictkillzone.com) · Alexander Bennett (volity.io) · Ken Chigbo (kenmacro.com) · Yang (homedadpro.com) · Yazeed Abu Summaqa (Equiti) · Harvest (r2ftrading.com) · «ILY» (quantum-algo.com، مراجعة «Quant») |
| `UNKNOWN` | **17** | «The Inner Circle Traders» network (thesimpleict / innercircletraders / theinnercircletraders — ناشر واحد) · quartersequence.com · ironcladresearch.com · alphametrixx.com · writofinance.com · myprimusmarkets.com (FxPrimus) · tmgm.com (TMGM) · backtrex.com · bullynx.com · forexmt4systems.com · proea.app · tradingstrategyguides.com · signalpilot.io · bestprops.com · netpicks.com (غير-ICT) · briskmarkets.com (غير-ICT) · snappchart.app |
| **المجموع** | **28** | 26 منهم نص ICT ذي صلة مباشرة؛ 2 (netpicks، briskmarkets) سياق عام غير-ICT للإحاطة فقط |
| **عدد النسخ `COPY_OF`** | **0** | لا توجد صفحات منقولة حرفيًا؛ الشبكة أعلاه محسوبة ناشرًا واحدًا (سياق مشابه للنسخ) |

**ملاحظة تضارب المصلحة:** كل `THIRD_PARTY` وكل `UNKNOWN` هنا إما بروكر أو vendor يبيع دورة/أداة — لا يوجد مصدر "محايد أكاديمي". هذا مُسجَّل لكل مصدر في الملفات.

---

## الملخص التنفيذي لكل مفهوم (سطر لكل مفهوم)

| المفهوم | شكل الشموع موصوف؟ | مستقلة | اتفاق/خلاف (جملة) |
|---|---|---|---|
| (أ) قمة/قاع التأرجح | **YES** (3 شموع، الوسطى هي الأعلى/الأدنى؛ المقارنة بالطرف الأقصى لا الأجسام) | 4 | متفقون على المقارنة بين شموع متجاورة؛ **مختلفون على عدد الشموع على كل جانب** (1 مقابل "لا عدد ثابت"). |
| (ب) فجوة القيمة العادلة | **YES** (ثلاث شموع C1/C2/C3؛ الحدود = أعلى C1 / أدنى C3 صعودًا؛ فتائل لا أجسام) | 5 | متفقون على البنية والحدود؛ **مختلفون على عتبة حجم الشمعة الوسطى وعلى معنى الاكتمال**. |
| (ج) كتلة الأوامر | **YES / PARTLY** (آخر شمعة معارضة قبل إزاحة؛ حدود الجسم مقابل الفتيل غير محسومة) | 5 | متفقون على النواة؛ **مختلفون: جسم أم نطاق كامل؟ هل الجرف شرط مايكل؟** |
| (د) السيولة | **PARTLY** (مستويات فوق/تحت قمم/قيعان قديمة ومتساوية؛ ليست علاقة شموع) | 4 | متفقون على المواضع؛ **مختلفون على عتبة «القرب الكافي» للقمم المتساوية** (لا رقم). |
| (هـ) جرف السيولة | **YES** (فتيل يتجاوز ثم عودة الجسم داخل المدى = جرف؛ حكم بعد الإغلاق) | 5 | متفقون على نواة الشكل؛ **مختلفون على الإغلاق الهامشي**؛ **لا أحد يعطي مسافة/سرعة**. |
| (و) الإزاحة | **PARTLY→YES** (تتحرك بقوة؛ جسم كبير/فتائل صغيرة) | 6 | **خلاف جذري:** لا عتبة (برأي مايكل مُبلّغ عنه) مقابل 60–80% جسم / 75% / 2–3× (أرقام مجتمعية معلنة بوصفها ليست كلام مايكل). |
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
| BabyPips Forum thread 678631 («ICT Mentorship 2022 notes and homework») | STUDENT_STATED | ب | https://forums.babypips.com/t/ict-mentorship-2022-notes-and-homework/678631 (**بحث فقط؛ لم تُجلب الصفحة — مجهولون يدّعون التعلم من دروس مايكل، غير موثق**) |
| Alexander Bennett (volity.io) | THIRD_PARTY | ج | https://volity.io/forex/ict-order-block/ |
| Ken Chigbo (kenmacro.com) | THIRD_PARTY | ج | https://kenmacro.com/order-block-meaning/ |
| Michael Phillips (ictkillzone.com) | THIRD_PARTY | ج، ح، و، ز، هـ، ط، ي | https://www.ictkillzone.com/ict-liquidity-sweep |
| Writ of Finance (writofinance.com) | UNKNOWN | د، هـ | https://www.writofinance.com/module-3-understanding-ict-liquidity/ |
| Primus Markets (myprimusmarkets.com) | UNKNOWN | د، هـ، ز، ح | https://myprimusmarkets.com/ict-smart-money-concepts/ |
| Alpha Metrix (alphametrixx.com) | UNKNOWN | هـ | https://alphametrixx.com/blog/ict-liquidity-trading-sweeps-pools-and-stop-hunts-explained |
| Backtrex (backtrex.com) | UNKNOWN | و | https://backtrex.com/en/blog/ict-displacement-candle-market-concept |
| Bullynx (bullynx.com) | UNKNOWN | و | https://bullynx.com/blog/displacement-in-trading |
| Yang (homedadpro.com) | THIRD_PARTY | و | https://homedadpro.com/en/displacement-trading/ |
| Forex MT4 Systems (forexmt4systems.com) | UNKNOWN | و | https://forexmt4systems.com/education/smart-money-concepts/displacement-in-trading/ |
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
