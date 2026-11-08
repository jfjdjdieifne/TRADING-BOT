# واو — مواصفة نموذج ICT كما وردت في المصادر، بندًا بندًا

**الملف:** `engine_v1/external_sources/s_ict_spec_sources_only.md`
**التاريخ:** 2026-11-08 · **الطبقة:** كل سطر هنا `TIER2` · **لا شيء في هذا الملف من معرفة الكاتب.**

---

## 0. قواعد قراءة هذا الملف (اقرأها قبل أي سطر)

1. **لا رقم واحد هنا بدون مصدر مسمّى.** كل سطر يحمل رمز مصدر بين قوسين مربّعين `[S-xxx]`، ورمز المصدر يُفكّ في الجدول في §1.
2. **لا مصدر في هذا الملف ينسب تعريفًا إلى مايكل هادليستون بنص حرفي.** الأعداد في `EXTERNAL_SOURCES_LOG.md` تقول: `MICHAEL_OWN = 0`. لذلك كل تعريف هنا هو **تعريف طرف ثالث**، ويُقرأ هكذا دائمًا.
3. **الأرقام الرقمية مقسّمة إلى ثلاثة أنواع، ولا تُخلط:**
   - `SOURCE_NUMBER` = رقم يضعه الناشر لنفسه ويقرّ (أو يقرّ ملفه) أنه ليس كلام مايكل.
   - `PARAM` = رقم ظهر كإعداد (input) في شيفرة مفتوحة المصدر — `IMPLEMENTATION_CODE` وليس تعليمًا.
   - `UNSTATED` = الموضع موجود في المصادر لكن **لا رقم له**. لا يُملأ الفراغ.
4. **عند تعارض المصادر لا يُختار.** يُعرض النصّان، ويُترك للمالك.
5. **حيث كتبت «النسخة أ / النسخة ب» فهما خياران متعادلان في المصادر، لا ترجيح.**
6. **كل الأمثلة الرقمية في هذا الملف أمثلة افتراضية من الناشر نفسه**، ومكتوب عندها ذلك. لا شيء منها بيانات سوق.
7. **ما لا وجود له في المصادر مكتوب `NO_SOURCE`.** وهذا هو أهم قسم في الملف (§12)، لأنه يحدّد أين يتوقف المحرك.

### رموز الحالة على الاقتباس

| الرمز | المعنى |
|---|---|
| `Q-NOW` | قرأت الجملة حرفيًا على الصفحة في هذه الجولة (2026-11-08) |
| `Q-PRIOR` | الجملة مسجّلة `QUOTE_VERIFIED` في ملفات `external_sources/` في هذه الجولة نفسها، ولم أُعد فتح الصفحة الآن |
| `Q-SNIP` | الجملة ظهرت في مقتطف بحث فقط ولم تُقرأ على الصفحة — **لا تُبنى عليها قاعدة** |

---

## 1. جدول المصادر (رموز هذا الملف)

| الرمز | الرابط | الناشر | المؤلف الظاهر | تاريخ الصفحة | ملاحظة |
|---|---|---|---|---|---|
| S-KZ22 | https://www.ictkillzone.com/ict-2022-model | ictkillzone.com | Michael Phillips | Published May 2026 · Updated 29 Sep 2026 | يصرّح: «…checklist are ours — Huddleston did not publish it in this form» |
| S-KZ-FVG | https://www.ictkillzone.com/ict-fair-value-gap | ictkillzone.com | Michael Phillips | غير ظاهر | خمسة فلاتر معلنة |
| S-KZ-OB | https://www.ictkillzone.com/ict-order-block | ictkillzone.com | Michael Phillips | 2026-05-05 (مسجّل في `c_order_block.md`) | معايير مرقّمة |
| S-KZ-BRK | https://www.ictkillzone.com/ict-breaker-block | ictkillzone.com | Michael Phillips | Published May 2026 | قاعدة المخالفة بنص صريح |
| S-KZ-DISP | https://www.ictkillzone.com/ict-displacement | ictkillzone.com | Michael Phillips | Updated September 2026 | 75% / 60% / 2× / 3–5× |
| S-KZ-SWP | https://www.ictkillzone.com/ict-liquidity-sweep | ictkillzone.com | Michael Phillips | Published June 2026 | ثلاثة أنواع للجرف |
| S-KZ-EQH | https://www.ictkillzone.com/ict-equal-highs-lows | ictkillzone.com | Michael Phillips | Published May 2026 | 5–10 نقاط فوركس |
| S-KZ-IRL | https://www.ictkillzone.com/ict-irl-erl | ictkillzone.com | Michael Phillips | Published July 2026 | تعريف T1/T2 |
| S-QUANT22 | https://quantum-algo.com/blog/guides/ict-2022-model-complete-guide/ | quantum-algo.com | Written by ILY · Reviewed by Quant | 2026-08-13 | قواعد دخول/وقف/هدف مسمّاة |
| S-FUND22 | https://fundingpips.com/blog/ict-2022-model | fundingpips.com | FundingPips | 2026-10-18 | مثال EUR/USD افتراضي مرقّم |
| S-IFLOW22 | https://ictflow.com/blog/ict-complete-2022-trading-strategy | ictflow.com | غير ظاهر | 2026-05-21 | 3:1 |
| S-LS-SWP | https://liquidityscan.io/blog/liquidity-sweep-vs-liquidity-grab-is-there-a-difference | liquidityscan.io | Hayk Muradian | 2026-07-12 | 1–3 شموع |
| S-LS-SWING | https://liquidityscan.io/blog/what-is-a-swing-high-and-swing-low-in-ict-the-3-candle-rule | liquidityscan.io | Hayk Muradian | 2026-07-10 | قاعدة C2 |
| S-LS-FVGvOB | https://liquidityscan.io/blog/fvg-vs-order-block-which-entry-zone-should-you-trade | liquidityscan.io | Hayk Muradian | 2026-07-11 | مقارنة دخول |
| S-TRADOSHI | https://tradoshi.com/en/academy/liquidity-sweep | tradoshi.com | غير ظاهر | غير ظاهر | 3 شموع |
| S-BTX-SWP | https://backtrex.com/en/blog/liquidity-sweep-strategy-backtest-results | backtrex.com | غير ظاهر | غير ظاهر | قواعد ميكانيكية كاملة |
| S-BTX-DISP | https://backtrex.com/en/blog/ict-displacement-candle-market-concept | backtrex.com | غير ظاهر | 2026-07-20 | 60–80% / 70% |
| S-VELO-FVG | https://velotrade.com/blog/fair-value-gap | velotrade.com | Gianluca Pizzituti | Oct 7, 2026 | CE وإبطال |
| S-BCHK-FVG | https://brokercheck.co/fair-value-gap/ | brokercheck.co | Florian Fendt | 2026-10-29 · Upd. 2026-11-02 | ثلاثة تعريفات امتلاء |
| S-ARROW-FVG | https://arrowalgo.com/fair-value-gap-trading-strategy/ | arrowalgo.com | غير ظاهر | غير ظاهر | 0.5×ATR |
| S-ELFIN-FVG | https://www.eltraderfinanciado.com/en/blog/fair-value-gap | eltraderfinanciado.com | غير ظاهر | غير ظاهر | وحدة بلا رقم |
| S-LSW-STOP | https://liquiditysweeps.com/ict-stop-loss/ | liquiditysweeps.com | Editorial Team | 2026-07-25 | 2–3 نقاط بفر |
| S-ICN-OB | https://innercircletrader.net/tutorials/ict-order-block/ · …/ict-bullish-order-block/ · …/ict-bearish-order-block/ | innercircletrader.net | Ayub Rana | غير ظاهر | 10–20 نقطة، 50%، شرط الابتلاع |
| S-ICN-SB | https://innercircletrader.net/tutorials/ict-silver-bullet-strategy/ | innercircletrader.net | Ayub Rana | غير ظاهر | وقف فوق فتيل شمعة الفجوة |
| S-TICT-LZ | https://www.theinnercircletraders.com/ict-liquidity-zones/ | theinnercircletraders.com | الفريق | Updated July 2026 | 1:2 كحد أدنى |
| S-TICT-EQH | https://www.theinnercircletraders.com/ict-equal-highs-equal-lows/ | theinnercircletraders.com | الفريق | Updated July 2026 | 5–10 نقاط + «متتالية» |
| S-DHANITH | https://www.dhanith.com/blog/liquidity-sweeps | dhanith.com | Abhishek Dhungarjal | 2026-05-03 | 1–5 شموع |
| S-CW-CAP | https://chartwhisperer.ca/blog/liquidity-sweep-stop-hunt-crypto-trading | chartwhisperer.ca | Charles Vincent | 2026-04-27 · Upd. 2026-11-04 | 1–3 شموع (كرِبتو) |
| S-AUDACITY | https://audacity.capital/trading-guides/liquidity-sweep/ | audacity.capital | Federica D'Ambrosio | 2026-09-18 | لا رقم |
| S-FORTFX | https://fortraders.com/blog/false-breakouts-why-they-happen-how-to-trade | fortraders.com | غير ظاهر | غير ظاهر | 5 بارات (غير ICT) |
| S-EBC-OB | https://www.ebc.com/forex/what-is-an-order-block-in-trading-beginner-s-guide | ebc.com | Chad Carnegie | 2025-05-22 · Upd. 2026-08-17 | «Neither convention is official» |
| S-TSG-OB | https://tradingstrategyguides.com/ict-order-block-complete-guide-to-institutional-footprints/ | tradingstrategyguides.com | غير ظاهر | غير ظاهر | فتح→فتيل |
| S-LUX-OB | https://www.luxalgo.com/library/concept/order-block-anatomy-and-refinement/ | luxalgo.com | غير ظاهر | غير ظاهر | «اختر عُرفًا» |
| S-LUX-EQH | https://www.luxalgo.com/library/concept/equal-highs-lows-as-liquidity/ | luxalgo.com | غير ظاهر | غير ظاهر | «لا تفاوت ثابت» |
| S-TV-YOWN | https://www.tradingview.com/script/Vjj1FUEb/ | tradingview.com / robert_yown | robert_yown | Aug 24 | تفاوت = مضاعف ATR(14) |
| S-EQUITI | https://www.equiti.com/sc-en/news/trading-ideas/equal-highs-and-equal-lows-explained-how-smart-money-sees-liquidity/ | equiti.com | Yazeed Abu Summaqa | غير ظاهر | عمق الجرف مقابل ATR |
| S-QSEQ-SWING | https://quartersequence.com/the-study/ict-market-structure/ | quartersequence.com | غير ظاهر | غير ظاهر | تعريف التأرجح |
| S-IRONCLAD | https://www.ironcladresearch.com/learn/technical-analysis/swing-highs-and-lows | ironcladresearch.com | غير ظاهر | 2026-07-23 | تعريف غير ICT |
| S-KXN | repo `kxngHADES/SMC-Marking` @ `bb79d1dc6f945cdce043e243e28ba6e7b9599e8f` | github.com | — | 2026-09-29 | **PARAM — شيفرة، لا تعليم** |
| S-VATTHU | repo `Vatthu/v1indicators` @ `36785b982e55c4dfed20037e52fd92dbdf8f7f19` | github.com | — | — | **PARAM** |
| S-JOSHY | repo `joshyattridge/smart-money-concepts` @ `1b62fd6c41e1f508e7ed76831a039fa4c82d42f6` | github.com | — | — | **PARAM** |
| S-POI | repo `kayasolomon/poi-liquidity-detector` @ `951304b33c71ad6fedcabf957de6ab40134d5670` | github.com | — | — | **PARAM** |
| S-FXMT4 | https://forexmt4systems.com/education/smart-money-concepts/displacement-in-trading/ | forexmt4systems.com | Dominic Walsh | 2026-07-23 · Upd. 2026-09-21 | 2–3× متوسط 10 أجسام |
| S-FXNX | https://fxnx.com/en/blog/ict-displacement-spotting-signature-smart-money | fxnx.com | Raj Krishnamurthy | 2026-02-18 | 80% |
| S-FXNX-FVG | https://fxnx.com/en/blog/fvg-entry-filter-mechanical-rules-htf-bias | fxnx.com | غير ظاهر | Upd. 2026-08 | `Q-SNIP` فقط — مُستبعد |
| S-ICN-DISP | https://innercircletrader.net/tutorials/ict-displacement-move/ | innercircletrader.net | Ayub Rana | غير ظاهر | ≥3 شموع |
| S-ICN-LP | https://innercircletrader.net/tutorials/ict-liquidity-pool/ | innercircletrader.net | Ayub Rana | غير ظاهر | 40–50 نقطة |
| S-ICN-MSS | https://innercircletrader.net/tutorials/why-ict-market-structure-shift-fail/ | innercircletrader.net | Ayub Rana | 2026-09-19 | الإغلاق دليل أقوى |
| S-ICN-FVG | https://innercircletrader.net/tutorials/fair-value-gap-trading-strategy/ | innercircletrader.net | Ayub Rana | مُحدّثة | فتيل C1 / فتيل C3 |
| S-ICN-LIQ | https://innercircletrader.net/tutorials/liquidity-in-forex-trading/ | innercircletrader.net | Ayub Rana | 2026-10-28 | BSL/SSL |
| S-QSEQ-LIQ | https://quartersequence.com/the-study/ict-liquidity/ | quartersequence.com | غير ظاهر | غير ظاهر | مواضع السيولة |
| S-QSEQ-MSS | https://quartersequence.com/the-study/ict-market-structure/ | quartersequence.com | غير ظاهر | غير ظاهر | MSS + التأرجح |
| S-QSEQ-FVG | https://quartersequence.com/the-study/ict-fair-value-gap/ | quartersequence.com | غير ظاهر | غير ظاهر | فتيل-إلى-فتيل |
| S-PRIMUS | https://myprimusmarkets.com/ict-smart-money-concepts/ | myprimusmarkets.com (FxPrimus) | غير ظاهر | 2026-10-08 | يسجّل الخلافات صراحةً |
| S-WRITO | https://www.writofinance.com/module-3-understanding-ict-liquidity/ | writofinance.com | Abdullah Shah | 2026-09-28 | ظل طويل + إغلاق معاكس |
| S-TMGM | https://www.tmgm.com/en/academy/trading-academy/ict-trading | tmgm.com | غير ظاهر | 2026-10-02 | الإزاحة تُرجّح الكسر |
| S-KENMACRO | https://kenmacro.com/order-block-meaning/ | kenmacro.com | Ken Chigbo | 2026-05-14 | «tight cluster» |
| S-QUANT-GLOSS | https://www.quantum-algo.com/glossary/displacement/ | quantum-algo.com | ILY · Reviewed by Quant | 2026-04-30 | 1.5×ATR(14) |
| S-QUANT-SWP | https://www.quantum-algo.com/blog/guides/liquidity-sweep-trading-complete-guide/ | quantum-algo.com | ILY | 2026-06-05 | «within a few candles»؛ 1–3 في المقتطف |
| S-LUX-EQH-IND | https://www.luxalgo.com/library/indicator/eqh-eql-fvg-breakouts/ | luxalgo.com | غير ظاهر | غير ظاهر | إعدادات بلا قيم |
| S-ICN-SB (وسيط) | https://innercircletrader.net/tutorials/ict-silver-bullet-strategy/ | innercircletrader.net | Ayub Rana | غير ظاهر | 1:3 · 20–30 نقطة |

---

## 2. الخطوة 0 — «الشمعة» و«القوية»: كل كلمة تُفتَّر إلى كمّية

السؤال الذي لا يجوز تركه: **«شمعة قوية» = ماذا بالضبط؟** المصادر لا تتركه معلّقًا؛ تعطيه أرقامًا، وكل رقم له **مقام**.

### 2.1 عناصر الشمعة كما تستعملها المصادر — بلا زيادة

| العنصر | ما هو بالضبط | المصدر | الاقتباس |
|---|---|---|---|
| الجسم (body) | من الافتتاح إلى الإغلاق | S-KZ22 | «the order block's body (open to close)» `Q-NOW` |
| المدى (range) | من الأعلى إلى الأدنى، أي **مع الفتائل** | S-KZ-DISP | «its total range (high to low)» `Q-NOW` |
| الفتيل (wick) | الجزء خارج الجسم؛ يُقارَن ككمّية **نسبة من المدى** | S-KZ-OB | «the wick should be less than 25% of the total candle range» `Q-PRIOR` |
| الإغلاق (close) | الحاكم في كل قرار «كسر/جرف/إبطال» تقريبًا | S-KZ-BRK | «a candle body must close beyond the order block zone» `Q-NOW` |

**نتيجة عددية 1:** لا يوجد في أي مصدر مفحوص عنصر خامس (لا حجم تداول، لا زمن شمعة، لا عدد صفقات) يدخل في تعريف «قوة» الشمعة. المصادر تستعمل **ثلاثة** فقط: الجسم، المدى، الفتيل.

### 2.2 «شمعة قوية» = أربع نسخ رقمية مختلفة، كل واحدة بمقامها

| # | النص الحرفي | الرقم | المقام (من ماذا) | المقارَن به | عدد الشموع | المصدر | الحالة |
|---|---|---|---|---|---|---|---|
| ق-1 | «body-to-range ratio above ~75%» | ~75% | الجسم ÷ المدى الكامل | لا شيء (الشمعة نفسها) | 1 | S-KZ-DISP | `Q-NOW` |
| ق-2 | «Below 60% = reduce or skip» | 60% حدّ أدنى | الجسم ÷ المدى الكامل | لا شيء | 1 | S-KZ-DISP | `Q-NOW` |
| ق-3 | «the candle's range should be at minimum 2x the average recent candle» | ≥2× | المدى | متوسط الشموع **3–5** السابقة | 3–5 | S-KZ-DISP | `Q-NOW` |
| ق-4 | «The candle bodies should be at least two to three times the average body of the previous ten candles» | 2–3× | الجسم (حجم مطلق) | متوسط جسم **10** شموع سابقة | 10 | S-FXMT4 (F5) | `Q-PRIOR` |
| ق-5 | «A large candle body, representing 60 to 80 percent or more of the total candle range» | 60–80% | الجسم ÷ المدى | لا شيء | 1 | S-BTX-DISP | `Q-PRIOR` |
| ق-6 | «body covering at least 70% of the candle range» | 70% | الجسم ÷ المدى | لا شيء | 1 | S-BTX-SWP | `Q-PRIOR` |
| ق-7 | «Look for candles where the body makes up at least 80% of the total candle range» | 80% | الجسم ÷ المدى | لا شيء | 1 | S-FXNX | `Q-PRIOR` |
| ق-8 | «at least 1.5x the average size of the candles in the preceding consolidation» + فتيل <25% | 1.5× | الحجم (المصدر لا يحدّد جسمًا أم مدى) | متوسط شموع **تجميع سابق بطول غير مذكور** | UNSTATED | S-KZ-OB | `Q-PRIOR` |
| ق-9 | «at least 1.5 times the average true range (ATR) of the prior 14 candles» | 1.5× | الجسم | ATR(14) | 14 | S-QUANT-GLOSS | `Q-NOW` |
| ق-10 | «at least 1.5 times the 14-period Average True Range» | 1.5× | جسم شمعة الإزاحة | ATR(14) | 14 | S-FUND22 | `Q-NOW` |

**الخلاصة العددية:** عشرة أرقام عند ثمانية ناشرين، على **ثلاثة مقامات مختلفة** (المدى الكامل، متوسط أجسام 10، ATR(14)) — ولا رقم واحد منها ينسبه صاحبه إلى مايكل. كل واحد منها مسجّل `SOURCE_NUMBER`.

### 2.3 «قوية» كعدد شموع — كم شمعة تُعدّ إزاحة واحدة؟

| النسخة | النص | العدد | المصدر | الحالة |
|---|---|---|---|---|
| ن-1 | «a rapid sequence of 2–3 candles» | 1 إلى 3 | S-KZ-DISP | `Q-NOW` |
| ن-2 | «one or more large-bodied candles» | 1 أو أكثر | S-KZ22 | `Q-NOW` |
| ن-3 | «At least three consecutive same-direction candles with large bodies» | ≥3 | S-ICN-DISP | `Q-PRIOR` |
| ن-4 | «one to three candles in a row with large bodies» | 1–3 | S-FXMT4 | `Q-PRIOR` |
| ن-5 | «within 2 candles following the sweep» | ≤2 بعد الجرف | S-BTX-SWP | `Q-PRIOR` |

**ما لا يوجد:** أي مصدر يعطي **حدًّا أعلى ثابتًا** بعدد الشموع. الحدود أعلاه هي **تعريف ما يُحتسب إزاحة**، لا سقفًا زمنيًا.

### 2.4 الترتيب الهرمي للفتيل مقابل الجسم — متى يُستعمل أيّهما (قرارات منفصلة، لا خلط)

| القرار | على ماذا يُقرأ | المصدر |
|---|---|---|
| هل الشمعة «قوية»؟ | الجسم ÷ المدى، أو الجسم مقابل ATR/متوسط | §2.2 |
| هل المنطقة (OB) صالحة؟ | الجسم وحده عند بعضهم، المدى الكامل عند غيرهم | §8 |
| هل حصل كسر؟ | **إغلاق الجسم** عند الأكثرية؛ الفتيل خيار عند بعضهم | §6 |
| هل حصل جرف؟ | فتيل يتجاوز + **إغلاق الجسم** للداخل | §5 |
| هل أُبطلت الفجوة؟ | **إغلاق** عبر الحد البعيد | §7 |
| أين الوقف؟ | **فتيل** الشمعة المرجعية | §10 |

---

## 3. الخطوة 1 — التأرجح (Swing): الرقم الأول في المحرك

### 3.1 النسخة الثلاثية (الأكثر تكرارًا)

- **أ/ الشكل:** «A swing high is three candles where the middle one has the highest high» `[S-QSEQ-SWING]` `Q-NOW`.
- **ب/ وجه المقارنة:** **الطرف الأقصى** (قمة الفتيل/قاع الفتيل)، لا الأجسام. لا مصدر واحد في هذا البحث يقارن الأجسام — «**ما لا يوجد عند أي مصدر:** مقارنة على أجسام الشموع» (`a_swing_high_low.md`).
- **ج/ التأكيد:** لا يصبح التأرجح تأرجحًا إلا **بإغلاق الشمعة التالية**: «It becomes a swing high when the candle after it closes» `[S-QSEQ-SWING]` `Q-NOW`.
- **د/ صياغة ثانية مطابقة المعنى:** «a candle whose high is higher than the highs of the candles immediately before and after it» `[S-IRONCLAD]` `Q-PRIOR` (موقع غير ICT).
- **هـ/ التقنين في شيفرة:** `PARAM` — نافذة متناظرة بعرض `2*length+1`، والتأكيد متأخر بـ`length` أشرطة: `length = 3` افتراضيًا في `[S-VATTHU]`، و`fractalK = 2` في `[S-POI]` (أي **شمعتان** على كل جانب)، و`swing_length = 50` في `[S-JOSHY]` (أي **101** شمعة — إعداد افتراضي، لا تعريف تعليمي).

### 3.2 النسخة «بلا عدد» — تُسجَّل ولا تُستخدم

- «waiting for at least one or two candles of clear reversal» `[S-TICT]` `Q-PRIOR` — أي انعكاس 1–2 شمعة بدل مقارنة ميكانيكية. هذا **تعارض صريح** مع §3.1 ج/د: هنا التأكيد **انعكاسي**، هناك **ميكانيكي**.

### 3.3 ماذا يترتب على اختيار النسخة (بلا ترجيح)

- النسخة الثلاثية تعطي تأرجحًا **بعد** إغلاق الشمعة الثالثة = تأخير شمعتين عن القمة الفعلية.
- نسخة `fractalK=2` تعطي تأخيرًا شمعتين أيضًا لكن بنافذة 5.
- `swing_length=50` تعطي تأخيرًا 50 شمعة.
- **الاختيار يغيّر كل رقم لاحق** (كل «الجرف» و«MSS» و«EQH» مبني عليها) — لذلك هو قرار مالك، لا قرار مصدر.

---

## 4. الخطوة 2 — أين توجد السيولة بالضبط

### 4.1 المواضع (متفق عليها)

| الموضع | النص | المصدر | الحالة |
|---|---|---|---|
| فوق القمم / تحت القيعان | «Buy stops collect above each old high… sell stops below each old low» | S-QSEQ-LIQ (D2) | `Q-PRIOR` |
| القمم/القيعان القديمة | «weekly highs, daily highs or equal highs are termed buy-side liquidity» | S-ICN-LIQ (D1) | `Q-PRIOR` |
| القمم/القيعان المتساوية | تُعدّ «especially obvious liquidity pools» | S-PRIMUS (D4) | `Q-PRIOR` |
| اليوم/الأسبوع السابق | PDH/PDL، وقمم/قيعان الأسبوع السابق | S-KZ-IRL | `Q-NOW` |
| الجلسات | «the Asian and London session highs and lows (or the overnight high/low for index futures)» | S-KZ22 | `Q-NOW` |

### 4.2 التساوي: الرقم ومقامه

| النسخة | الرقم | المقام | شرط إضافي | المصدر | الحالة |
|---|---|---|---|---|---|
| ت-1 | 5–10 | نقاط (pips) مسافة مطلقة | «the touches need time between them»؛ «Two consecutive candles at the same high is not a meaningful EQH» | S-KZ-EQH | `Q-PRIOR` |
| ت-1أ | 10–20 نقطة NQ / 1.50–3.00 أونصة ذهب | `FUTURES_UNITS` / سعر | نفس الصفحة | S-KZ-EQH | `Q-PRIOR` |
| ت-2 | 5–10 | نقاط | «two or more **consecutive** swing highs» | S-TICT-EQH | `Q-PRIOR` |
| ت-3 | 0.1–0.3 | **نسبة من السعر** | — | S-LS-SWING | `Q-PRIOR` |
| ت-4 | مضاعف ATR(14) **بلا قيمة مطبوعة** | ATR | «compared against the immediately preceding swing point of the same type» | S-TV-YOWN | `Q-NOW` |
| ت-5 | تفاوت % من ATR + «Minimum bars apart» + «Max EQH/EQL Age» — كلها **بلا قيم مطبوعة** | ATR / أشرطة | — | S-LUX-EQH-IND | `Q-PRIOR` |
| ت-6 | «There is no fixed tolerance.» | — | — | S-LUX-EQH | `Q-NOW` |

**سؤال «هل يجب أن تكون متتالية؟»** — المصادر: ت-2 تقول **متتالية**؛ ت-4 تقول **آخر تأرجح سابق من النوع نفسه**؛ S-KZ-EQH لا تقول.
**سؤال «هل يجب ألّا تكون هناك قمة أعلى بينهما؟»** — **`NO_SOURCE` في أي مصدر تعليمي.** يظهر فقط كسلوك تنفيذي: «a waiting level is dropped the moment price trades through it» `[S-TV-YOWN]` `Q-NOW`، وفي `[S-POI]` يُقتل المرشّح إذا تجاوز السعر الطرف الخارجي.

---

## 5. الخطوة 3 — الجرف (Sweep): الشكل الحرفي

### 5.1 الشكل الأساسي (خمسة مصادر مستقلة)

```
أ/ السعر يتجاوز المستوى بـ فتيل (wick)
ب/ ثم يُغلق الجسم (body) مرة أخرى على الجانب الأصلي من المستوى
ج/ الحكم بعد الإغلاق فقط — «a sweep is only a sweep after the reclaim close»
```

| المصدر | اقتباس | الحالة |
|---|---|---|
| S-KZ-SWP | «extends a wick beyond a BSL or SSL pool… then immediately reverses with the candle body closing back inside the prior range» | `Q-PRIOR` |
| S-LS-SWP | «the sweep candle itself, or one within the next one to three candles, closes back inside the prior range» | `Q-PRIOR` |
| S-WRITO (E3) | «a long, thin shadow poking past the level, with the candle's body closing back on the other side» | `Q-PRIOR` |
| S-PRIMUS (E5) | «it usually appears as a long wick through equal highs and a close back inside the range» | `Q-PRIOR` |
| S-AUDACITY | «a wick poking through a swing high or low, followed by a candle closing back inside the prior range» | `Q-PRIOR` |

### 5.2 «بسرعة» — هذا هو السؤال الذي **لا رقم له**

| النسخة | الرقم | ما يُقاس | المصدر | الحالة |
|---|---|---|---|---|
| س-1 | **1–3** شموع | عدد الشموع حتى الإغلاق العائد للداخل | S-LS-SWP · S-TRADOSHI · S-CW-CAP · S-QUANT-SWP | `Q-PRIOR` |
| س-2 | **3** بالضبط | نفس الشيء، كقاعدة الكورس نفسه | S-TRADOSHI | `Q-PRIOR` |
| س-3 | **1–5** | نفس الشيء | S-DHANITH | `Q-PRIOR` |
| س-4 | **5** بارات (3 على 1m) | إغلاق داخل مدى آخر 20 بار | S-FORTFX (غير ICT) | `Q-PRIOR` |
| س-5 | لا حدّ | «immediately» / «the very next candle» لأنواع معيّنة | S-KZ-SWP | `Q-PRIOR` |
| س-6 | لا حدّ | «may run a little further, sometimes over several candles» | S-AUDACITY | `Q-PRIOR` |
| س-7 | **0** شمعة (نفس الشمعة) | piercing bar يُقرّر فورًا | S-POI (PARAM) | شيفرة |
| س-8 | **20** بارًا | مدة صلاحية الجرف للاقتران بـCHoCH — **مقيس مختلف** | S-POI (PARAM) | شيفرة |

**ملاحظة مقام مهمة:** س-1/س-3/س-4 تقيس **عدد الشموع**؛ س-8 تقيس **صلاحية الاقتران**؛ س-5/س-6 تقيسان **لا شيء**. لا تُجمع في خانة واحدة.

### 5.3 هل الفتيل وحده كافٍ؟

**لا مصدر مفحوص يقبل الفتيل وحده.** كل المصادر تشترط إغلاقًا عائدًا للداخل — ويوجد استثناء واحد صريح: نوع 2 عند S-KZ-SWP يقبل إغلاق جسم هامشي وراء المستوى ثم انعكاسًا، وهذه **معارضته صريحة** عند S-WRITO. و`[S-KZ-SWP]` نفسه يسجّل الخيارين: «Some traders count a break only on a candle close; others accept a wick» `Q-PRIOR` — وهو **تسجيل خلاف لا حكم**.

### 5.4 الأرقام المرتبطة بالجرف (عمق/بفر)

| الرقم | ما يُقاس | المصدر | الحالة |
|---|---|---|---|
| ≥3 نقاط | تجاوز مستوى H1 المتساوي | S-BTX-SWP | `Q-PRIOR` |
| 2–3 نقاط مقابل ATR 15m ≈ 32 نقطة | عمق الجرف نفسه | S-EQUITI | `Q-PRIOR` |
| 2 نقطة (مثال توضيحي) | فوق قمة الجرف | S-TRADOSHI | `Q-PRIOR` |

---

## 6. الخطوة 4 — كسر البنية (MSS): ماذا يُكسر بالضبط

### 6.1 التعريف

- **أ/ ما يُكسر:** «a break of the most recent short-term swing against the trend, made after price has first run the stops beyond an old high or low» `[S-QSEQ-MSS]` `Q-PRIOR`.
- **ب/ الترتيب:** الكسر يأتي **بعد** الجرف. لا مصدر يعكس الترتيب.
- **ج/ الوسيط:** الإغلاق أفضل من الفتيل — «preferably close» `[S-QSEQ-MSS]` (والمصدر يعلّق: «"Preferably" is his word»)، و«strong displacement and a clear close provide much better structural evidence» `[S-ICN-MSS]`.
- **د/ الخلاف:** «some count on close; others accept a wick» `[S-PRIMUS]` `Q-NOW`.
- **هـ/ الشرطان الإضافيان عند MSS (نص مقروء الآن):** «His market structure shift adds two conditions: a run on stops first, and a break made with displacement.» `[S-QSEQ-MSS]` `Q-NOW`.
- **و/ الفتيل vs الجسم (نص مقروء الآن):** «A wick is enough to take liquidity, but for the shift itself ICT prefers a candle body that closes beyond the swing.» `[S-QSEQ-MSS]` `Q-NOW`. ويسجّل الموقع أن مايكل يسمّي الفتيل العائد «not all that convincing» — **نقل الموقع، لا نص فيديو مفحوص**.
- **ز/ تحذير في نفس الصفحة:** «It is a bias for the next intraday move, not a guarantee of a reversal.» `Q-NOW`.
- **ح/ CHoCH ≠ MSS:** «CHoCH … is the retail name for the first break against the trend, and ICT does not use it.» `[S-QSEQ-MSS]` `Q-NOW`.

### 6.2 الإزاحة كشرط للكسر (وليس صفة تجميلية)

- «carries more weight… when the market structure shift occurs with displacement» `[S-TMGM]` `Q-PRIOR`.
- «The move that causes the MSS must be a strong, one-directional displacement» `[S-QUANT22]` `Q-NOW`.
- في قائمة S-KZ22: «Enter only after the raid has finished and the MSS has printed» `Q-NOW` — الشرطان معًا، بترتيب.

### 6.3 الكسر vs الجرف — نفس الحدث بقراءتين

- الجرف = فتيل يتجاوز + إغلاق **داخل**.
- الكسر = **إغلاق** وراء المستوى.
- نصّ صريح: «A close *through* the level is a structure break instead — never both» `[S-POI README]` (شيفرة).
- و`[S-KZ-SWP]` يفرّق الثلاثة في جدول Type 1/2/3 ويُبقي «الإغلاق الهامشي» حالةً ثانية.

---

## 7. الخطوة 5 — فجوة القيمة العادلة (FVG): الحدّان، الوسط، والإبطال

### 7.1 الحدّان — على الفتائل بإجماع كل المصادر المفحوصة

| البند | النص | المصدر | الحالة |
|---|---|---|---|
| التعريف | «the wick of candle 1 and the wick of candle 3 don't overlap» | S-KZ-FVG | `Q-NOW` |
| صياغة ثانية | «The gap that exists between the high of the first candle and the low of the third candle» | S-ICTN-FVG (B2) | `Q-PRIOR` |
| صياغة ثالثة | «It is measured wick to wick: in a move up, from the high of candle 1 to the low of candle 3» | S-QSEQ-FVG (B4) | `Q-PRIOR` |
| صياغة رابعة | «mark the high of the candlestick prior to the large candle and the low of the subsequent candlestick» | S-ICN-FVG (B1) | `Q-PRIOR` |
| شيفرة | `bullish = low[t] > high[t-2] and close[t-1] > high[t-2]` | S-VATTHU (PARAM) | مقروء |
| شيفرة | `low > high[2] and close[1] > high[2]` | S-KXN (PARAM) | مقروء |

**نتيجة عددية 2:** **صفر** مصادر تقارن الأجسام في الفجوة. الحدّان دائمًا: **أعلى C1 / أدنى C3** (صعودية)، والعكس هبوطية.

### 7.2 الوسط (CE) = 50%

- «consequent encroachment (the midpoint between candle 1's wick and candle 3's wick)» `[S-KZ22]` `Q-NOW`.
- «← 50% CE — enter here» داخل المخطط المشروح `[S-KZ-FVG]` `Q-NOW`.
- ملاحظة مقام: CE = 50% **من الفجوة** (فتيل-إلى-فتيل)، **وليس** 50% من جسم أي شمعة. هذه نقطة يخطئ فيها الخلط مع OB.

### 7.3 الحجم الأدنى — رقم واحد فقط

| النسخة | الرقم | المقام | المصدر | الحالة |
|---|---|---|---|---|
| ح-1 | ≥0.5× | ارتفاع الفجوة مقابل ATR **بدون ذكر الدورة** | S-ARROW-FVG | `Q-PRIOR` |
| ح-2 | «a fraction of the average true range» بلا قيمة | ATR | S-BCHK-FVG | `Q-PRIOR` |
| ح-3 | «A minimum size by ATR or by percentage» بلا قيمة | ATR أو % | S-ELFIN-FVG | `Q-PRIOR` |
| ح-4 | «Min FVG Size (ATR)» إعداد بلا قيمة مطبوعة | ATR | S-LUX-EQH-IND | `Q-PRIOR` |
| ح-5 | لا حدّ أدنى مذكور | — | S-KZ-FVG · S-VELO-FVG | `Q-NOW` |
| ح-6 | `threshold = 0.0` (مُطفأ) — وحدات سعر مطلقة | سعر | S-KXN · S-VATTHU (PARAM) | مقروء |
| ح-7 | `fvgMinAtr = 0.0` (مُطفأ) — مضاعف ATR | ATR | S-KXN (PARAM) | مقروء |

### 7.4 الإبطال — أربع نسخ

| النسخة | الحدث | المصدر | الحالة |
|---|---|---|---|
| إ-1 | **إغلاق جسم عبر الحد البعيد** | S-KZ-FVG · S-VELO-FVG · S-ELFIN-FVG · S-LS-FVGvOB | `Q-NOW` / `Q-PRIOR` |
| إ-2 | **امتلاء كامل** (السعر يعبر الفجوة كلها) | S-ARROW-FVG · S-BCHK-FVG | `Q-PRIOR` |
| إ-3 | **إغلاق عبر CE (50%)** | S-FXNX | `Q-SNIP` — **لا يُبنى عليه** |
| إ-4 | الإغلاق عبر الحد البعيد يُحوّل الفجوة إلى **IFVG** | S-VELO-FVG | `Q-PRIOR` |
| إ-5 | لمس الفتيل يُبطِل (عكس إ-1) | S-JOSHY (PARAM: `ohlc["low"][i+2:] <= top[i]`) | مقروء |
| إ-6 | fresh → partial عند أول اختراق → filled عند العبور الكامل (كسر 0–1) | S-POI (PARAM) | مقروء |

### 7.5 اللمس والمنتصف: هل يُبطلان؟

- **لا.** «a wick into the FVG is not mitigation … it's been tested» `[S-KZ-FVG]` `Q-PRIOR`؛ و«accepting a wick through CE but exiting on a close through the full gap» `[S-VELO-FVG]` `Q-PRIOR`.
- العدّ: **3 ناشرين مستقلين** على «اللمس لا يُبطل».

---

## 8. الخطوة 6 — كتلة الأوامر (OB) ونظائرها

### 8.1 أي شمعة؟ — الشروط المرتّبة

**النسخة أ — آخر شمعة معارضة قبل الإزاحة (الأكثر تكرارًا):**
- أ-1. الشمعة هي **آخر شمعة عكس اتجاه الحركة**: «the last opposing candle (or small cluster of candles) before a significant displacement move» `[S-KZ-OB]` `Q-PRIOR`.
- أ-2. قد تكون **تجمعًا صغيرًا**: نفس الاقتباس؛ و`[S-KENMACRO]`: «the last opposing candle, or a tight cluster of candles» `Q-PRIOR`.
- أ-3. **طول التجمع: `UNSTATED`** في كل مصدر مفحوص.

**النسخة ب — شرط الابتلاع (أربعة شروط مرقّمة عند ناشر واحد):**
- ب-1. الشمعة الثانية تلتقط قاع/قمة السابقة.
- ب-2. تُغلق الثانية وراء قمة/قاع السابقة.
- ب-3. فجوة على الإطار الأدنى.
- ب-4. MSS على الإطار الأدنى.
- العدد الأدنى **شمعتان** — «Both variants are 2-candle formations at minimum» `[S-ICN-OB]` `Q-PRIOR`.

### 8.2 حدود المنطقة — ثلاث نسخ متعارضة (لا رابع)

| النسخة | الحدّان | المصادر | الحالة |
|---|---|---|---|
| حد-1 | **الجسم فقط** (فتح→إغلاق) | S-KZ-OB · S-TSG-OB | `Q-PRIOR` |
| حد-2 | **الفتح→الفتيل الأقصى** | S-TSG-OB (صفحته الثانية) | `Q-PRIOR` |
| حد-3 | **فتيل→فتيل** (المدى الكامل) | S-LUX-OB · S-JOSHY (PARAM) · S-KXN (PARAM) | `Q-PRIOR` + مقروء |
| حد-4 | «Neither convention is official.» | S-EBC-OB | `Q-NOW` |
| حد-5 | `zoneMode: 'body'` افتراضيًا، `'full'` بالطلب | S-POI (PARAM) | مقروء |

### 8.3 سعر الدخول داخل المنطقة

| النسخة | السعر | المصادر |
|---|---|---|
| د-1 | **50% من الجسم** («mean threshold») | S-KZ-OB · S-KZ22 |
| د-2 | **فتح شمعة الـOB** أو 50% من المدى الكامل | S-LS-FVGvOB |
| د-3 | **50% ارتداد** من المنطقة (بلا تحديد جسم/مدى) | S-ICN-OB |
| د-4 | أمر معلق (limit) لا سوق | S-KZ22 · S-QUANT22 |

### 8.4 الإبطال (الميتيغيشين)

- «Only a candle body closing beyond the zone boundary constitutes full mitigation» `[S-KZ-OB]` `Q-PRIOR` — **إغلاق جسم**، لا فتيل.
- التقنين: `obMitig: "Close"` أو `"Wick"` خيار مستخدم — `[S-KXN]` `PARAM`.
- **الفتيل للدخول، الجسم للإبطال، الفتيل للوقف** — ثلاث قراءات مختلفة على نفس الشمعة، وكل واحدة من مصدر (§2.4).

### 8.5 بريكر بلوك (Breaker) — قاعدة المخالفة الحرفية

- **ب-1/ التعريف:** كتلة أوامر انتهكت: «a former order block that has been completely violated — a candle body closed beyond the order block zone» `[S-KZ-BRK]` `Q-NOW`.
- **ب-2/ قاعدة المخالفة:** «The violation rule is: a candle body must close beyond the order block zone.» `Q-NOW`.
- **ب-3/ ما لا يُعدّ مخالفة:** «A wick through the zone is not a violation.» `Q-NOW`.
- **ب-4/ حدود فحص المخالفة = جسم شمعة الـOB (فتح→إغلاق)، والفتيل غير ذي صلة:** «The zone boundaries for the violation check are the body of the order block candle — open to close… The wick low is irrelevant for this check.» `Q-NOW`. **لاحظ: هذه حدود مختلفة عن حد-3 أعلاه.**
- **ب-5/ الدخول:** «Short entry at 50% of breaker» في مخطط الصفحة `Q-NOW`؛ والوقف «above breaker zone»؛ والهدف «SSL» — أي السيولة المعاكسة.
- **ب-6/ التحذير:** «A Breaker Block is only as good as the order block it came from» — إن كانت الكتلة الأصلية بلا جرف/بلا إزاحة نظيفة، يرث البريكر الضعف `Q-NOW`.

### 8.6 BPR (Balanced Price Range)

- «forms where a new FVG overlaps an older opposing FVG, and its midpoint can be used as the entry» `[S-KZ22]` `Q-NOW`. **بلا رقم.**

---

## 9. الخطوة 7 — الدخول: أي سعر بالضبط، وبأي أمر، ومتى

### 9.1 سعر الدخول — ثلاث نسخ

| النسخة | السعر | المصدر | الحالة |
|---|---|---|---|
| خ-1 | **CE = 50% من الفجوة** | S-KZ22 · S-KZ-FVG · S-QUANT22 | `Q-NOW` |
| خ-2 | **الحافة القريبة من الفجوة** (ملء أعلى، سعر أسوأ) | S-KZ22 · S-QUANT22 | `Q-NOW` |
| خ-3 | **الحافة البعيدة** (سعر أفضل، ملء أقل) | S-QUANT22 | `Q-NOW` |
| خ-4 | 50% من جسم الـOB (mean threshold) | S-KZ-OB · S-KZ22 | `Q-PRIOR` |
| خ-5 | فتح شمعة الـOB | S-LS-FVGvOB | `Q-PRIOR` |

- **ترتيب الفجوات إن تعددت:** «the first one to form after the MSS is the usual choice» `[S-KZ22]` `Q-NOW`.
- **شرط الموضع في النطاق:** «a bearish FVG sitting in premium fits a short… sitting in discount means you would be selling at a relatively cheap price… Our rule is to skip it» `[S-KZ22]` `Q-NOW`.

### 9.2 نوع الأمر

- «Place a limit order at the fair value gap» `[S-QUANT22]` `Q-NOW`.
- «Placing a limit at the CE» `[S-KZ22]` `Q-NOW`.
- **`NO_SOURCE`** على أن مايكل يسمّي نوع الأمر: «لا اقتباس مباشر من مايكل في أي مصدر هنا» (`j_design_gaps.md`).

### 9.3 الشروط الخمسة المرتّبة (S-KZ-FVG) — كلها إلزامية عند الناشر

```
ف-1 الإطار الأعلى: بايس واضح (أعلى 50% = علاوة ⇒ بيع فقط؛ أدناه = رخص ⇒ شراء فقط)
ف-2 جرف قبل الإزاحة: «No sweep = no institutional context»
ف-3 نافذة kill zone: لندن 2:00–5:00 · نيويورك 7:00–9:00 · إغلاق لندن 10:00–12:00 (بتوقيت نيويورك)
ف-4 تأكيد بنيوي: MSS أو CISD على 5 أو 15 دقيقة بعد الجرف
ف-5 تقاطع PD Array (اختياري): OB/Breaker/BPR بنفس المستوى
⇒ «All 4 YES → Enter at 50% CE · Stop beyond sweep wick · Target draw on liquidity»
```
الحالة: `Q-NOW` (كل الجمل أعلاه قرأتُها على الصفحة).

### 9.4 نوافذ الوقت — الرقم ومن يقوله

| النافذة | التوقيت | المصدر | الحالة |
|---|---|---|---|
| London Open | 2–5 صباحًا ET | S-KZ22 · S-KZ-FVG | `Q-NOW` |
| New York Open (AM) | 7–9 صباحًا ET | S-KZ22 · S-KZ-FVG | `Q-NOW` |
| Silver Bullet | 10–11 صباحًا ET | S-KZ22 | `Q-NOW` |
| London Close | 10–12 ظهرًا ET | S-KZ-FVG | `Q-NOW` |
| Silver Bullet (كامل) | لندن 03:00–04:00 · NY AM 10:00–11:00 · NY PM 14:00–15:00 (EST) | S-ICN-SB | `Q-PRIOR` |
| Kill zones بجدول مختلف | London 02:00–05:00 · NY AM 07:00–10:00 · London Close 10:00–12:00 · NY PM 13:30–16:00 (EST) | S-QUANT22 | `Q-NOW` |
| منع الدخول في آسيا | «An entry in the Asian kill zone does not qualify under our rule» | S-KZ22 | `Q-NOW` |

**تعارض مسجّل:** NY AM عند S-KZ22 = 7–9، وعند S-QUANT22 = 7–10. لا ترجيح.

### 9.5 التسلسل الكامل — بندًا تحت بند (كما كتبه الناشر)

**A. قائمة S-KZ22 الخمسة (تُقرأ كبوّابات؛ فشل واحدة = لا صفقة):**
- A-1 اتجاه اليوم: نطاق تداول أسبوعي/يومي، أعلى/أسفل 50%، تسمية «draw on liquidity». تعارض الأسبوعي واليومي = «stand-aside day».
- A-2 الطور (AMD): هل انتهى الجرف؟ تُعلَّم البرك: PDH/PDL، قمم/قيعان الجلسات، القمم/القيعان المتساوية. «Enter only after the raid has finished and the MSS has printed».
- A-3 النافذة الزمنية: لندن 2–5 أو NY 7–9 أو Silver Bullet 10–11 (ET).
- A-4 منطقة الدخول: PD Array في الجهة الصحيحة؛ الافتراضي FVG عند CE؛ بدائل: OB عند mean threshold، BPR عند منتصفه.
- A-5 الإدارة: «Stop beyond the raid extreme»؛ T1 = IRL؛ T2 = ERL؛ «take half at the first target and move the stop to break-even».

**B. تسلسل S-QUANT22 (خمسة عناصر بترتيب، «Skip one, and the setup is invalid»):**
- B-1 بركة سيولة (قمم/قيعان متساوية وجلسات هي «the cleanest pools»).
- B-2 جرف: «The wick beyond the level is the signature — a close beyond it usually invalidates the setup».
- B-3 MSS.
- B-4 إزاحة: «Weak, overlapping candles do not count».
- B-5 فجوة = منطقة الدخول.

**C. تسلسل S-FUND22 (أربع خطوات):** — مسجّل في `l_open_questions.md` بنفس الترتيب، مع مثال EUR/USD افتراضي كامل.

### 9.6 الترتيب الذي **تتفق** عليه المصادر (نقطة إجماع واحدة، بلا رقم)

```
جرف (sweep)  →  إزاحة (displacement)  →  كسر بنية (MSS)  →  فجوة (FVG)  →  دخول على ارتداد إلى الفجوة
```

| المصدر | نصّه على الترتيب |
|---|---|
| S-QUANT22 | «It is a _sequence_ of five things that must happen in order. Skip one, and the setup is invalid.» |
| S-KZ22 | «Enter only after the raid has finished and the MSS has printed» |
| S-KZ-FVG | «A buy-side or sell-side liquidity pool was taken immediately before the displacement that created the FVG» |
| S-IFLOW22 | الدخول على ارتداد إلى FVG بعد جرف ثم MSS |
| S-BTX-SWP | الاقتران مشروط بإزاحة خلال شمعتين من الجرف ثم دخول عند منتصف الفجوة |

**العدّ: 5 ناشرين متفقين على الترتيب.** **صفر** مصدر مفحوص يعكس الترتيب أو يسمح بالدخول قبل الجرف («Never enter before the sweep» — S-QUANT22).

**لكن الانتباه:** الإجماع على **الترتيب** لا على أي **رقم** في أي خطوة. كل رقم داخل الخطوات يبقى متعارضًا كما في §2–§11.

---

## 10. الخطوة 8 — الوقف: الموضع أولًا، ثم الرقم

### 10.1 الموضع — اتفاق على «الطرف»، اختلاف على أي طرف

| النسخة | الموضع | المصادر |
|---|---|---|
| و-1 | **وراء فتيل الجرف** (أقصى نقطة للجرف) | S-KZ22 · S-QUANT22 · S-KZ-SWP · S-ICN-SB · S-AUDACITY |
| و-2 | **وراء الفتيل الكامل لشمعة الـOB** (لا الجسم) | S-KZ-OB |
| و-3 | **وراء منطقة الـOB** (10–20 نقطة) | S-ICN-OB |
| و-4 | **وراء فتيل شمعة الفجوة** («the candle that created the fair value gap») + بفر صغير | S-ICN-SB |
| و-5 | **5 نقاط وراء المستوى المجروف** | S-BTX-SWP |
| و-6 | **40–50 نقطة** وراء المستوى المجروف | S-ICN-LP |

اقتباسات: «Stop beyond the raid extreme» `[S-KZ22]` `Q-NOW` · «Stops go beyond the full candle wick — not just the body» `[S-KZ-OB]` `Q-PRIOR` · «stop loss goes above the high of the candle that created the fair value gap» `[S-ICN-SB]` `Q-NOW`.

### 10.2 البفر — الأرقام، وحدودها

| الرقم | المقام | الزوج/الأداة | المصدر | الحالة |
|---|---|---|---|---|
| **2–3 نقاط** | بفر فوق/تحت المرجع | EUR/USD 2 · GBP/USD 3 · GBP/JPY 4–5 | S-LSW-STOP | `Q-PRIOR` |
| **3–5 نقاط NQ** | بفر | `FUTURES_UNITS` | S-LSW-STOP | `Q-PRIOR` |
| **10–20 نقطة** | وراء قاع/قمة منطقة OB | فوركس | S-ICN-OB | `Q-PRIOR` |
| **5 نقاط** | وراء المستوى المجروف | EURUSD/XAUUSD | S-BTX-SWP | `Q-PRIOR` |
| **40–50 نقطة** | وراء المستوى المجروف | فوركس | S-ICN-LP | `Q-PRIOR` |
| «small buffer» بلا رقم | فوق/تحت الفتيل | — | S-KZ-OB · S-FUND22 · S-ICN-SB | `Q-NOW`/`Q-PRIOR` |

**منطق البفر عند من يعطيه:** «The buffer accounts for spread (a stop at exactly C1 high triggers on a 0.3-pip spread touch)» `[S-LSW-STOP]` `Q-PRIOR` — أي أنه **حماية من السبريد**، وهذا يفسّر لماذا هو بالنقاط لا بالنسب.

### 10.3 قواعد إدارة الوقف (لا تحريك)

- «If the structural stop is too wide for your risk limit, trade fewer contracts or a micro contract rather than tightening the stop» `[S-KZ22]` `Q-NOW`.
- «Widening the stop past the sweep wick to "give it room" destroys the entire risk premise of the model» `[S-QUANT22]` `Q-NOW`.

### 10.4 ما يحدث إذا وضعت الوقف قريبًا جدًا

- «Stops sitting one pip beyond the FVG are routinely tagged before the trade resolves» `[S-ICN-SB]` `Q-NOW`.
- «Stops go beyond the full candle wick — not just the body… stops inside the wick get hit on valid setups» `[S-KZ-OB]` `Q-PRIOR`.

---

## 11. الخطوة 9 — الهدف: مستويان، ثم مضاعف المخاطرة

### 11.1 التعريف من الرسم (اتفاق)

- **T1 = IRL** (داخل النطاق: أقرب تجمع معاكس، قمم/قيعان قصيرة المدى).
- **T2 = ERL** (خارج النطاق: القمة/القاع القديم، PDH/PDL).
- نص: «First target at the nearest opposing pool inside the range (internal range liquidity, IRL); second target at the draw on liquidity from Step 1 (external range liquidity, ERL)» `[S-KZ22]` `Q-NOW`.
- التصنيف: «Unmitigated FVG inside the range → IRL … Old high / old low of the range → ERL» `[S-KZ-IRL]` `Q-NOW`.
- إجماع قديم: «Every ICT trade must have a liquidity pool as its target» `[S-TICT-LZ]` `Q-PRIOR`, و`[S-PRIMUS]`: «the target is usually the opposing liquidity pool» `Q-PRIOR`.

### 11.2 مضاعف المخاطرة — أربع نسخ

| النسخة | الرقم | مقامه | المصدر | الحالة |
|---|---|---|---|---|
| هـ-1 | **1:2 حد أدنى** (و1:3 أفضل) | مسافة الهدف ÷ مسافة الوقف | S-TICT-LZ · S-KZ-FVG · S-KZ-OB | `Q-PRIOR`/`Q-NOW` |
| هـ-2 | **1.5:1 حد أدنى** | نفس المقام، «to first IRL» | S-LSW-STOP | `Q-PRIOR` |
| هـ-3 | **1:3** | نفس المقام | S-ICN-SB | `Q-NOW` |
| هـ-4 | **3:1 حد أدنى** | نفس المقام | S-IFLOW22 | `Q-PRIOR` |
| هـ-5 | «routinely offers 3:1 to 5:1» (وصف، لا قاعدة) | نفس المقام | S-QUANT22 | `Q-NOW` |
| هـ-6 | **20–30 نقطة** هدف مطلق | نقاط، بلا مقام | S-ICN-SB | `Q-NOW` |

**النص الحاكم عند من يشرطه:** «if the distance to the DOL target is less than three times the stop size, the setup does not qualify» `[S-IFLOW22]` `Q-PRIOR` · «If the structure doesn't offer at least 1:2 with your stop beyond the FVG, skip it» `[S-KZ-FVG]` `Q-NOW`.

### 11.3 الإدارة

- «Our default is to take half at the first target and move the stop to break-even» `[S-KZ22]` `Q-NOW`.
- «partial exits at the first FVG in the path and full exit at the ERL target» `[S-IFLOW22]` `Q-PRIOR`.
- **`NO_SOURCE`** على قاعدة «الخروج المبكر»: «لا يوجد مصدر ICT يعطي قاعدة عامة للخروج المبكر» (`j_design_gaps.md`).

---

## 12. الخطوة 10 — مثال كامل بالتفصيل، من مصدرَين

### 12.1 مثال S-KZ22 (NQ، افتراضي معلن)

```
السياق:   بعد 10:00 صباحًا (نافذة Silver Bullet)
الجرف:    قمة سيولة شرائية عند 21,240–21,248، امتدّت إلى 21,274
الكسر:    MSS = إغلاق تحت 21,188
الفجوة:   هبوطية من 21,192 إلى 21,226 (في العلاوة)
الدخول:   أمر بيع معلق عند CE = 21,209، صالح حتى 11:00
الوقف:    "Stop beyond the raid extreme" ⇒ 21,280
الهدف 1:  20,960 (قمم/قيعان متساوية)
الهدف 2:  20,820 (قاع اليوم السابق)
```
المصدر: مخطط S-KZ22 المشروح، `Q-NOW`، ونصّه: «Schematic of the hypothetical example below, not a real chart».

**لاحظ الأرقام القابلة للحساب هنا:** مسافة الوقف = 21,280 − 21,209 = 71 نقطة؛ مسافة الهدف الأول = 21,209 − 20,960 = 249 نقطة. **هذا حساب من أرقام المصدر، لا رقم جديد من عندي.**

### 12.2 مثال S-FUND22 (EUR/USD، افتراضي معلن)

```
الفجوة:   1.0862 – 1.0870
الدخول:   CE = 1.0866
الوقف:    1.0846 (= 5 نقاط تحت قاع الجرف 1.0851)
المخاطرة: 20 نقطة
الهدف:    PDH ⇒ R:R = 2.7
```
المصدر: `l_open_questions.md` سجل Q6-05/Q7-09، `Q-PRIOR`.

### 12.3 مثال S-ICN-SB (XAU/USD، 5 دقائق)

```
الجرف:    فوق القمم المتساوية + قمة الجلسة الآسيوية، بعد 10:00
الكسر:    MSS على 3 دقائق
الدخول:   داخل الفجوة (لا داخل الـOB)
الوقف:    فوق قمة الشمعة التي صنعت الفجوة + بفر صغير
الهدف:    القاع السابق ⇒ 1:3
```
المصدر: `Q-NOW`.

---

## 13. البريك (Breaker): التسلسل التفصيلي

| البند | الحكم | النص | الحالة |
|---|---|---|---|
| ب-1 | كتلة أوامر صالحة أولًا | «Always validate the source OB before trading the Breaker» | `Q-NOW` |
| ب-2 | مخالفة = **إغلاق جسم** عبر المنطقة | «a candle body must close beyond the order block zone» | `Q-NOW` |
| ب-3 | حدود الفحص = جسم شمعة الـOB (فتح→إغلاق) | «The wick low is irrelevant for this check» | `Q-NOW` |
| ب-4 | الفتيل ليس مخالفة | «A wick through the zone is not a violation» | `Q-NOW` |
| ب-5 | حجم شمعة المخالفة يهم | «A large-bodied candle closing well beyond the zone is a stronger violation signal» | `Q-NOW` |
| ب-6 | الدخول عند 50% من البريك | «Short entry at 50% of breaker» (مخطط) | `Q-NOW` |
| ب-7 | الوقف فوق/تحت منطقة البريك | «Stop — above breaker zone» (مخطط) | `Q-NOW` |
| ب-8 | الهدف = السيولة المعاكسة | «Target: SSL» (مخطط) | `Q-NOW` |

**مثال الصفحة (GBP/USD):** منطقة OB هبوطية 1.28240–1.28310 → إغلاق جسم فوقها → بريكر → دخول عند 50% → وقف فوق المنطقة → هدف SSL. `Q-NOW`.
**تعارض مسجّل:** هنا حدود الفحص **الجسم**؛ وفي §8.2 حد-3 المنطقة **فتيل→فتيل**. نفس الناشر يستعمل اصطلاحين في صفحتين. أُسجّل ولا أرجّح.

---

## 14. الخطوة 11 — شروط المنع (Invalids): كل واحدة بمصدرها

| المنع | النص | المصدر |
|---|---|---|
| لا جرف ⇒ لا شيء | «No sweep, no valid OB» | S-KZ-OB |
| لا جرف ⇒ لا شيء | «Without the sweep, you're speculating that the FVG matters» | S-KZ-FVG |
| فجوة بلا جرف = مرفوضة | «✗ Invalid — no sweep before the move» (مخطط) | S-KZ-FVG |
| عكس البايس | «A bullish FVG in that environment might react briefly — but you're fighting institutional order flow» | S-KZ-FVG |
| خارج النافذة | «Setups outside the window are not Silver Bullet setups, even when the chart pattern looks identical» | S-ICN-SB |
| قبل تأكيد MSS | «A liquidity raid alone is not a signal» | S-ICN-SB |
| إزاحة ضعيفة | «Weak, overlapping candles do not count» | S-QUANT22 |
| دخول قبل الجرف | «Never enter before the sweep» | S-QUANT22 |
| لا هدف واضح | «If there is no obvious opposite liquidity pool to draw toward, the reward side of the trade is a guess» | S-QUANT22 |
| تحريك الوقف | «Moving the stop — Widening the stop past the sweep wick… destroys the entire risk premise» | S-QUANT22 |
| فجوة في الرخص لصفقة بيع | «Our rule is to skip it» | S-KZ22 |
| تعارض الأطر | «we treat it as a stand-aside day» | S-KZ22 |

---

## 15. ما لا يوجد له مصدر — `NO_SOURCE` (هذا القسم يحدّ المحرك)

| # | السؤال | الحالة | ما قيل حرفيًا |
|---|---|---|---|
| 1 | سرعة/مسافة الجرف ككمّية عند مايكل | **`NO_SOURCE`** | «لا يوجد أي رقم متفق عليه في أي مصدر» — `e_liquidity_sweep.md` |
| 2 | عدد الشموع القصوى بين قمتين متساويتين | **`NO_SOURCE`** (تعليميًا) | إعداد بلا قيمة عند ناشرَين فقط |
| 3 | قاعدة «لا قمة أعلى بينهما» | **`NO_SOURCE`** تعليميًا | سلوك تنفيذي فقط |
| 4 | طول «التجمع» في الـOB | **`NO_SOURCE`** | `UNSTATED` في كل مصدر |
| 5 | قيمة تفاوت التساوي عند S-LUX/S-TV | **`NO_SOURCE`** | «value not printed» |
| 6 | هل 50% للـOB من الجسم أم من المدى | **`NO_SOURCE`** (تعارض بلا حسم) | حد-1/د-1 مقابل د-2 |
| 7 | نوع الأمر عند مايكل | **`NO_SOURCE`** | «لا اقتباس مباشر من مايكل» |
| 8 | الخروج المبكر | **`NO_SOURCE`** | «فجوة كاملة» |
| 9 | سقف إعادة الدخول | **`NO_SOURCE`** | «مفهوم بلا حدود» |
| 10 | هدف بنقاط ثابتة كقاعدة | **`NO_SOURCE`** | «لا يوجد مصدر يكرر هذا الرقم» |
| 11 | مفهوم «انتهاء صلاحية» الفجوة بزمن/شموع | **`NO_SOURCE`** في التعليم | إعداد «Max Age» بلا قيمة في الشيفرة |
| 12 | دوران/نافذة ATR في نسخة «0.5×ATR» للفجوة | **`NO_SOURCE`** | «period not stated» |

---

## 16. التعارضات الصريحة — قائمة مغلقة، بلا ترجيح

1. عدد شموع التأرجح الجانبية: 1 (ثلاثية) مقابل «لا عدد ثابت» مقابل 2 (Williams).
2. تأكيد التأرجح: إغلاق الشمعة التالية مقابل «انعكاس 1–2 شمعة».
3. عتبة «القوة»: 75% مقابل 60–80% مقابل 80% مقابل 2–3× مقابل 1.5×ATR.
4. سرعة الجرف: 1–3 مقابل 1–5 مقابل 5 بارات مقابل «لا حد».
5. الجرف: إغلاق هامشي مقبول (نوع 2) مقابل مرفوض.
6. حدود الـOB: جسم مقابل فتح→فتيل مقابل فتيل→فتيل.
7. 50% للـOB: من الجسم مقابل من المدى.
8. مرجع CISD: فتح أول شمعة السلسلة مقابل جسم آخر شمعة معارضة.
9. هدف الإبطال: إغلاق عبر الحد البعيد مقابل امتلاء كامل مقابل إغلاق عبر CE (snip).
10. NY AM: 7–9 مقابل 7–10.
11. البفر: 2–3 مقابل 5 مقابل 10–20 مقابل 40–50 نقطة.
12. مضاعف المخاطرة: 1.5:1 مقابل 1:2 مقابل 1:3 مقابل 3:1.

---

## 17. الملحق — الأرقام في الشيفرة (PARAM)، منفصلة تمامًا

| الثابت | القيمة | المعنى | الملف/السطور | الرخصة |
|---|---|---|---|---|
| `swing_length` | 50 | نافذة التأرجح | S-JOSHY `smc.py:137` | MIT |
| `length` | 3 | نصف نافذة التأرجح | S-VATTHU `equal_highs_lows.py:10` | MIT |
| `threshold` | 0.1 | تفاوت التساوي كنسبة % | S-VATTHU `equal_highs_lows.py:11` | MIT |
| `range_percent` | 0.01 | عرض نطاق تجميع السيولة من مدى كامل التاريخ | S-JOSHY `smc.py:573–595` | MIT |
| `eqThr` × `ta.atr(200)` | 0.1 | تفاوت EQH كسريب ATR | S-KXN `marks.pine:61,72,349` | لا رخصة ظاهرة |
| `equalTolATR` | 0.25 | تفاوت EQH كسر ATR(14) | S-POI `detector.ts:57` | MIT |
| `sweepReversalMaxBars` | 20 | صلاحية اقتران الجرف بـCHoCH | S-POI `detector.ts:57,174` | MIT |
| `minImpulseATR` | 1.5 | إزاحة = مسافة من حافة الجسم إلى سعر الكسر ÷ ATR(14) | S-POI `detector.ts:218` | MIT |
| `obLookback` | 20 | أقصى بحث للخلف عن شمعة الـOB | S-POI `detector.ts:54` | MIT |
| `zoneMode` | `'body'` | حدود المنطقة = جسم | S-POI `detector.ts:52` | MIT |
| `fractalK` | 2 | أذرع التأرجح | S-POI `detector.ts:51` | MIT |
| `fvgFillMode` | `'wick'` | الامتلاء يُقاس بالفتيل | S-POI `fvg.ts:55` | MIT |
| `fvgMinAtr` | 0.0 | حدّ أدنى للفجوة (مُطفأ) | S-KXN `marks.pine:64` | لا رخصة ظاهرة |
| `periods` / `threshold` | 5 / 0.0 | إزاحة = حركة % إغلاق-إلى-إغلاق | S-VATTHU `order_blocks.py:7–71` | MIT |
| `use_wicks` | False | حدود المنطقة = فتح→قاع افتراضيًا | S-VATTHU `order_blocks.py` | MIT |

**كل ما في §17 `IMPLEMENTATION_CODE`، ولا يُخلط بأي رقم في §2–§14.** ولا واحد من هذه الأرقام يُنسب إلى مايكل.

---

## 18. حالة الملف

- **صفر** رقم في هذا الملف لم يُنسَب إلى مصدر مسمّى.
- **صفر** اقتباس لم يُقرأ (كل `Q-SNIP` موسوم ومُستبعد من كل قاعدة).
- **`NO_SOURCE`**: 12 سؤالًا في §15.
- **تعارضات مسجّلة**: 12 في §16.
- **الملف المحمي**: لم يُلمس.
