# (M) أمثلة مخططات مرئية يمكن للإنسان أن يفحصها بعينه — سجل صفحات عامة

**الغرض:** أن يفتح المالك كل رابط بنفسه ويقرر بعينه: هل الشمعة/الصندوق المعلَّم يطابق فعلًا القاعدة المكتوبة؟
هذا سجل **روابط ونصوص فقط** — لا صور محفوظة، ولا اقتباس أكثر من 25 كلمة، ولا حكم على صحة أي معلّم.
كل السجلات هنا `TIER2`. لا يُخلط شيء من هذا بملفات B1، ولا يُستعمل كحجّة علمية.

**تاريخ الجولة:** 2026-11-09 (وصول واحد).
**الطبقة:** TIER2 — صفحات خارجية عامة، ليست كلام مايكل، وليست مصدرًا أصليًا.

---

## 0) كيف فُحصت الصفحات (شفافية عن حدّ الأداة)

- **فحص التحميل:** كل صفحة في هذا الملف فُتحت فعليًا في هذه الجلسة وأعادت **متنًا كاملًا** بلا شعار دخول، بلا دفع، وبلا حجب محتوى (لا يوجد `login / paywall / cookie wall` يحجب النص). صفحات فيها شريط كوكيز أُبقي محتواها ظاهرًا — وُسمت `COOKIE_BANNER_ONLY`.
- **حدّ الأداة (يُذكر صراحة):** لم أستطع قراءة رمز HTTP الخام (200) من صدفة الأوامر لأن الخروج TLS من الصندوق محجوب (`curl`/`urllib` يعيدان `SSL_ERROR_SYSCALL`). لذلك حالة الفحص المكتوبة هي `CONTENT_RETURNED` (متن كامل رجع بلا حاجز) وليست رقم 200 حرفيًا. هذا حدّ أداة، لا ادّعاء نجاح.
- **كيف رأيت الصور:** تنزيل الصور المباشر محجوب من الصدفة، لكن وسيط البحث الصوري يعيد الصورة الفعلية من نفس النطاق ويسجّل `source_url` للصفحة. حيث ظهرت الصورة لي كتبتُ `VIEWED`؛ وحيث لم تظهر كتبتُ `IMAGE_NOT_VIEWED` و**لم أصف محتواها إطلاقًا**، ونقلت نص التعليق فقط.
- **قاعدة الاقتباس:** كل اقتباس ≤ 25 كلمة، حرفي كما ظهر. `QUOTE_VERIFIED` تعني أن الجملة موجودة فعلًا في الصفحة أو داخل الصورة التي رأيتها.

**حدود مهمة يقرأها المالك قبل أي شيء:**

1. أكثر الصور في هذا المجال **رسوم توضيحية (illustration)** لا بيانات سوق حقيقية. كُتب ذلك في كل سجل، ووُسم ما يقول الناشر نفسه إنه توضيحي.
2. كثير من الصفحات **لا تذكر الأداة/الفريم/التاريخ**. كُتب `UNSTATED` ولا شيء غير ذلك — لم أخترع أداة ولا تاريخًا.
3. عدّ الشموع تقديري بالعين ومكتوب كفئة (أقل من 10 / 10-30 / أكثر من 30).
4. لم أحكم على صحة أي معلّم، ولم أستعمل معرفتي الخاصة بـICT. أنا نقلت ما يعلّمه هو ومن كتب الصفحة.

---

## 1) سجلات قابلة للفحص — قمة/قاع التأرجح (swing high / swing low)

### S-01
- **id:** S-01
- **concept:** swing high (وقاع في الخلفية)
- **URL:** https://liquidityscan.io/blog/what-is-a-swing-high-and-swing-low-in-ict-the-3-candle-rule
- **publisher:** LiquidityScan
- **author:** Hayk Muradian (Founder & Lead Analyst at LiquidityScan)
- **page date:** 2026-07-10 (ظاهر على الصفحة)
- **WHERE:** صورة الغلاف أعلى المقال (hero)، أول صورة قبل العنوان الرئيسي — الصورة الوحيدة في هذا الموضع.
- **caption / label (verbatim):** "SWING HIGH"
- **QUOTE_VERIFIED**
- **what is marked:** شمعة خضراء واحدة محاطة بدائرة خضراء + سهم لأعلى يشير إليها، وكلمة SWING HIGH أسفل السهم.
- **real or illustration:** illustration (شموع مرسومة على خلفية داكنة، بلا محور سعري ولا تواريخ).
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** 10-30
- **text readable at normal zoom:** YES
- **view status:** VIEWED
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### S-02
- **id:** S-02
- **concept:** swing high + swing low (سلسلة HH/HL)
- **URL:** https://fbs.com/fbs-academy/traders-blog/what-is-swing-high-and-swing-low-in-forex-trading
- **publisher:** FBS (FBS Academy)
- **author:** غير مذكور على الصفحة
- **page date:** Aug 28, 2025 (ظاهر)
- **WHERE:** قسم «Practical examples on charts» ← العنوان الفرعي «Example of a clear uptrend with the ZigZag indicator…» — الشكل الأول من ثلاثة في ذلك القسم.
- **caption (verbatim):** "Example of a clear uptrend with the ZigZag indicator, created by higher highs and higher lows"
- **QUOTE_VERIFIED**
- **what is marked:** أسهم حمراء هابطة عند القمم (higher highs) وأسهم خضراء صاعدة عند القيعان (higher lows)، وخط اتجاه أسود عبر القيعان، وخط ZigZag أحمر يصل النقاط.
- **real or illustration:** real market (شاشة منصة، محور سعري بالأسعار وتواريخ ظاهرة).
- **instrument / timeframe / date:** GBPUSD، H1، 7 Jul 2025 → 25 Jul 2025 (مكتوبة على المحور)
- **candles countable:** more than 30
- **text readable at normal zoom:** YES
- **view status:** VIEWED
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### S-03
- **id:** S-03
- **concept:** swing high + swing low (سلسلة LH/LL)
- **URL:** https://fbs.com/fbs-academy/traders-blog/what-is-swing-high-and-swing-low-in-forex-trading
- **publisher:** FBS (FBS Academy)
- **author:** غير مذكور
- **page date:** Aug 28, 2025
- **WHERE:** نفس القسم، الشكل الثاني: «Example of a clear downtrend created by lower highs and lower lows».
- **caption (verbatim):** "Example of a clear downtrend created by lower highs and lower lows"
- **QUOTE_VERIFIED**
- **what is marked:** أسهم حمراء عند كل قمة هابطة وأسهم خضراء عند كل قاع هابط، خط اتجاه هابط أسود.
- **real or illustration:** real market
- **instrument / timeframe / date:** GBPUSD، H1، 23 May 2025 → 30 May 2025
- **candles countable:** more than 30
- **text readable:** YES
- **view status:** VIEWED
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### S-04
- **id:** S-04
- **concept:** swing high + swing low داخل نطاق (equal/flat)
- **URL:** https://fbs.com/fbs-academy/traders-blog/what-is-swing-high-and-swing-low-in-forex-trading
- **publisher:** FBS (FBS Academy)
- **author:** غير مذكور
- **page date:** Aug 28, 2025
- **WHERE:** نفس القسم، الشكل الثالث: «Example of a clear range → flat swing highs/lows».
- **caption (verbatim):** "Example of a clear range → flat swing highs/lows"
- **QUOTE_VERIFIED**
- **what is marked:** خطان أفقيان أحمران (سقف وأرضية النطاق)، أسهم حمراء على القمم المسطّحة وأسهم خضراء على القيعان المسطّحة.
- **real or illustration:** real market
- **instrument / timeframe / date:** GBPUSD، H4، 1 Mar 2025 → 4 Apr 2025
- **candles countable:** more than 30
- **text readable:** YES
- **view status:** VIEWED
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### S-05
- **id:** S-05
- **concept:** swing low (متكرر) في اتجاه هابط + قمة التأرجح كمرجع
- **URL:** https://therighttrader.com/learn/trend-analysis/swing-high
- **publisher:** The Right Trader
- **author:** غير مذكور باسم شخص على الصفحة
- **page date:** غير مذكورة على الصفحة
- **WHERE:** قسم «Bullish, Bearish, and Range Swing Highs» ← فقرة "Bearish." — الصورة الأولى في ذلك القسم.
- **caption (verbatim):** "Swing Lows in a Downtrend. Bearish example. Schematic illustration."
- **QUOTE_VERIFIED** (نص التعليق أسفل الصورة على الصفحة)
- **what is marked:** أربعة صناديق نصية سوداء مكتوب فيها "Swing low" مع نقاط بيضاء فوق كل قاع.
- **real or illustration:** illustration — والصفحة نفسها تقول ذلك ("Schematic illustration"), والصورة تحمل شريط "Schematic illustration, not real price data".
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** more than 30
- **text readable:** YES
- **view status:** VIEWED
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### S-06
- **id:** S-06
- **concept:** swing high + swing low كسقف/أرضية سيولة (external)
- **URL:** https://kagels-trading.com/blog/liquidity-sweep/
- **publisher:** Kagels Trading
- **author:** Karsten Kagels (author) — مراجعة: Christian Möhrer
- **page date:** Last updated 22 October 2026
- **WHERE:** قسم «Which level matters? Internal and external liquidity» — الشكل الوحيد هناك.
- **caption (verbatim):** "Schematic drawing, not market data. External levels sit beyond the swing high and the swing low."
- **QUOTE_VERIFIED** (سطر المصدر أسفل الصورة على الصفحة)
- **what is marked:** خطوط متقطعة برتقالية أعلى قمة التأرجح ("External: above the swing high") وخط أخضر أسفل قاع التأرجح ("External: below the swing low")، وثلاثة خطوط صفراء منقّطة عند قيعان التصحيح الداخلية.
- **real or illustration:** illustration — الصفحة تكتب "Schematic drawing, not market data" داخل الصورة.
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** 10-30
- **text readable:** YES
- **view status:** VIEWED
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### S-07
- **id:** S-07
- **concept:** swing high (تشكيل ثلاث شموع، مرقّم 1-2-3)
- **URL:** https://innercircletrader.net/tutorials/ict-swing-high-explained/
- **publisher:** Inner Circle Trader (innercircletrader.net) — موقع تعليمي طرف ثالث، ليس موقع مايكل
- **author:** غير مذكور باسم شخص (الصفحة تعرض Ayub Rana كصاحب كورس مدفوع، لا ككاتب المقال)
- **page date:** غير مذكورة على الصفحة
- **WHERE:** قسم «Swing High Identification — Step by Step» — الصورة بعد الخطوات الثلاث.
- **caption (verbatim):** "ICT Swing High real market example: a three-candle formation marked on a live price chart with the middle wick the highest"
- **QUOTE_VERIFIED** (نص alt على الصفحة) — ملاحظة أمانة: الصورة التي وصلتني **ليست** شاشة سوق حيّة، بل رسم بثلاث شموع مرقّمة؛ وصف التعليق لا يطابق الصورة.
- **what is marked:** ثلاث شموع مرقّمة 1 و2 و3، الشمعة الوسطى (2) أعلى قمة، دائرة صفراء على قمتها، وقوس أحمر يمر بالقمتين الجانبيتين.
- **real or illustration:** illustration
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** under 10 (ثلاث شموع فقط)
- **text readable:** YES
- **view status:** VIEWED
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### S-08
- **id:** S-08
- **concept:** swing low (ثلاث تشكيلات مرقّمة 1-2-3 على مخطط واحد)
- **URL:** https://innercircletrader.net/tutorials/ict-swing-low-formation/
- **publisher:** Inner Circle Trader (innercircletrader.net)
- **author:** غير مذكور باسم شخص
- **page date:** غير مذكورة على الصفحة
- **WHERE:** قسم «Swing Low Identification — Step by Step» — الصورة الأخيرة في القسم.
- **caption (verbatim):** "ICT Swing Low real market example: a three-candle formation marked on a live price chart with the middle wick the lowest"
- **QUOTE_VERIFIED** (نص alt)
- **what is marked:** ثلاثة تشكيلات، كل واحد بثلاث شموع مرقّمة 1 و2 و3، ودائرة صفراء أسفل الشمعة الوسطى (2) في كل تشكيل.
- **real or illustration:** real market (شموع بمحور سعري، لكن بلا رمز أداة ولا فريم ولا تاريخ مكتوب)
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** more than 30
- **text readable:** YES
- **view status:** VIEWED
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### S-09
- **id:** S-09
- **concept:** swing high + swing low (تعريف الشمعة الوسطى)
- **URL:** https://www.altrady.com/crypto-trading/smart-money-concept/how-to-identify-swing-highs-and-lows
- **publisher:** Altrady
- **author:** Catalin (كاتب معلن، رابط LinkedIn على الصفحة)
- **page date:** Published Feb 26, 2025 · Updated Oct 19, 2026
- **WHERE:** قسم «What is a swing high and a swing low?» ← تحت «Swing low» — الصورة الأولى في القسم.
- **caption (verbatim):** "Swing high and swing low on candlesticks: a swing high candle has a lower high on each side"
- **QUOTE_VERIFIED** (نص alt على الصفحة؛ الاقتباس مقطوع عند 25 كلمة)
- **what is marked:** لوحان: يسار عنوانه "Swing high" بسهم على "Peak high" وسهمان "Lower high"؛ يمين عنوانه "Swing low" بسهم "Peak low" وسهمان "Higher low".
- **real or illustration:** illustration (شموع مرسومة على خلفية سوداء)
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** under 10 (ثلاث شموع في كل لوح)
- **text readable:** YES
- **view status:** VIEWED
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### S-10
- **id:** S-10
- **concept:** swing high/low — شرط **التأكيد** بالإغلاق (validation)
- **URL:** https://www.altrady.com/crypto-trading/smart-money-concept/how-to-identify-swing-highs-and-lows
- **publisher:** Altrady
- **author:** Catalin
- **page date:** Published Feb 26, 2025 · Updated Oct 19, 2026
- **WHERE:** قسم «Step 4: Confirm with a candle close» — الصورة الوحيدة في تلك الخطوة.
- **caption (verbatim):** "Swing validation: a swing high is confirmed when a later candle closes below the swing candle's low"
- **QUOTE_VERIFIED** (نص alt، مقطوع عند 25 كلمة)
- **what is marked:** لوح "Swing high validation" بسهم على "Candle close below swing lowest point" وخط أفقي أصفر؛ ولوح "Swing low validation" بسهم "Candle close above swing highest point".
- **real or illustration:** illustration
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** 10-30 (حوالي 7-8 شموع في كل لوح)
- **text readable:** YES
- **view status:** VIEWED
- **NEGATIVE?:** no — لكنه يحدّد شرط «صالحة فقط بعد الإغلاق»، أي أنه يعرّف ما لا يُعدّ تأكيدًا قبل ذلك.
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### S-11
- **id:** S-11
- **concept:** swing high — «قوية» مقابل «ضعيفة» (strong vs weak)
- **URL:** https://www.edgeflo.com/blog/swing-structure-trading
- **publisher:** EdgeFlo
- **author:** غير مذكور باسم شخص
- **page date:** Mar 7, 2026
- **WHERE:** قسم «Strong Highs vs Weak Highs» — الصورة أسفل القسم.
- **caption (verbatim):** "Diagram comparing strong highs versus weak highs in swing structure"
- **QUOTE_VERIFIED** (نص alt)
- **what is marked:** لوح "Strong High" بالسهم والعلامة ✓ و"BOS Confirmed"؛ ولوح "Weak High" بعلامة ✗ و"No BOS".
- **real or illustration:** illustration (خط زجزاج لا شموع)
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** لا شموع (خط فقط) — تُقرأ الحركة كقمم وقيعان
- **text readable:** YES
- **view status:** VIEWED
- **NEGATIVE?:** **YES — TIER2 NEGATIVE.** القمة "Weak High" مثال يقول فيه المعلّم إنها **غير معتمدة** لأن الحركة بعدها لم تكسر القاع السابق ("No BOS").
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### S-12
- **id:** S-12
- **concept:** swing high + swing low (تعليم نقط التأرجح)
- **URL:** https://candlestructurelabs.com/learn/market-structure.html
- **publisher:** Candle Structure Labs
- **author:** غير مذكور باسم شخص
- **page date:** غير مذكورة على الصفحة
- **WHERE:** قسم «Swing points: the alphabet of a chart» — «Figure 1».
- **caption (verbatim):** "Figure 1: marking swing points. A swing high has lower highs on both sides, a swing low has higher lows on both sides."
- **QUOTE_VERIFIED**
- **what is marked (من التعليق فقط):** يقول التعليق إن الشموع المطوّقة تُعلَّم كنقاط تأرجح، وإن العلامة لا تُرسم إلا بعد ظهور الشموع على اليمين.
- **real or illustration:** UNKNOWN
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** UNKNOWN
- **text readable:** UNKNOWN
- **view status:** **IMAGE_NOT_VIEWED** — لا أصف شيئًا من محتوى الصورة، فقط نص التعليق أعلاه.
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### S-13
- **id:** S-13
- **concept:** swing high/low — تسمية HH/HL/LH/LL على قمم وقيعان
- **URL:** https://candlestructurelabs.com/learn/market-structure.html
- **publisher:** Candle Structure Labs
- **author:** غير مذكور
- **page date:** غير مذكورة
- **WHERE:** قسم «A worked labeling example» — «Figure 2».
- **caption (verbatim):** "Figure 2: the worked example labeled. Green: HL, HH, HL, an intact uptrend."
- **QUOTE_VERIFIED**
- **what is marked (من التعليق فقط):** تسميات HL/HH/LH/LL على نقاط التأرجح، بالأخضر للاتجاه الصاعد وبالأحمر لأول LH وLL.
- **real or illustration:** UNKNOWN
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** UNKNOWN
- **text readable:** UNKNOWN
- **view status:** **IMAGE_NOT_VIEWED**
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### S-14
- **id:** S-14
- **concept:** swing high + swing low كتعريف الاتجاه
- **URL:** https://www.ironcladresearch.com/learn/technical-analysis/swing-highs-and-lows
- **publisher:** Ironclad Research
- **author:** غير مذكور باسم شخص
- **page date:** غير مذكورة على الصفحة
- **WHERE:** قسم «Identifying Swing Points» — الشكل في نهاية القسم (وحيد).
- **caption (verbatim):** "A zig-zag of price marking successive swing highs and swing lows, each higher than the last, defining an uptrend"
- **QUOTE_VERIFIED** (نص alt على الصفحة، مقطوع عند 25 كلمة)
- **what is marked (من التعليق فقط):** يقول التعليق إن كل قمة معلَّمة SH وكل قاع SL، وHH/HL عند التدرّج الصاعد.
- **real or illustration:** UNKNOWN — التعليق يسمّيه "zig-zag" أي رسم توضيحي مرجّح، لكن لم أرَه.
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** UNKNOWN
- **text readable:** UNKNOWN
- **view status:** **IMAGE_NOT_VIEWED**
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### S-15
- **id:** S-15
- **concept:** swing high — شكل التشكيل
- **URL:** https://tradingfinder.com/education/forex/ict-swing-high/
- **publisher:** TradingFinder
- **author:** Writer: Eda Kaya · Reviewer: Nino Gogochashvili · Fact checker: Rajesh Sharma
- **page date:** Modified Nov 26, 2025
- **WHERE:** قسم «Swing High Structure» — الصورة أسفل الفقرة.
- **caption (verbatim):** "How the Swing High structure forms"
- **QUOTE_VERIFIED**
- **what is marked (من التعليق فقط):** لا يذكر التعليق أي شمعة أو صندوق بعينه.
- **real or illustration:** UNKNOWN
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** UNKNOWN
- **text readable:** UNKNOWN
- **view status:** **IMAGE_NOT_VIEWED**
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### S-16
- **id:** S-16
- **concept:** swing high — خطوات التعريف على مخطط زوج
- **URL:** https://tradingfinder.com/education/forex/ict-swing-high/
- **publisher:** TradingFinder
- **author:** Eda Kaya / مراجعة Nino Gogochashvili
- **page date:** Modified Nov 26, 2025
- **WHERE:** قسم «How to Identify a Swing High?» — الصورة بعد الخطوات.
- **caption (verbatim):** "How to identify a swing high and its stages on the EUR/USD chart"
- **QUOTE_VERIFIED**
- **what is marked (من التعليق فقط):** يقول التعليق إن الأداة EUR/USD، ولا يذكر رقم شمعة.
- **real or illustration:** UNKNOWN — التعليق يسمّي أداة (EUR/USD) فالمؤشر أنه مخطط سوق، لكن لم أرَه.
- **instrument / timeframe / date:** EUR/USD · الفريم UNSTATED · التاريخ UNSTATED
- **candles countable:** UNKNOWN
- **text readable:** UNKNOWN
- **view status:** **IMAGE_NOT_VIEWED**
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### S-17
- **id:** S-17
- **concept:** swing high — مخطط التشكيل (صورة أخرى من نفس الصفحة)
- **URL:** https://innercircletrader.net/tutorials/ict-swing-high-explained/
- **publisher:** Inner Circle Trader (innercircletrader.net)
- **author:** غير مذكور
- **page date:** غير مذكورة
- **WHERE:** قسم «Swing High Formation» — الصورة بعد تعريف التشكيل.
- **caption (verbatim):** "ICT Swing High formation diagram showing three candles with the middle candle's high higher than the left and right candles"
- **QUOTE_VERIFIED** (نص alt)
- **what is marked (من التعليق فقط):** ثلاث شموع، الوسطى قمتها أعلى من جارتيها.
- **real or illustration:** UNKNOWN — التعليق يسمّيه "diagram".
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** UNKNOWN
- **text readable:** UNKNOWN
- **view status:** **IMAGE_NOT_VIEWED**
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### S-18
- **id:** S-18
- **concept:** swing high مستعمل كمنطقة بيع
- **URL:** https://innercircletrader.net/tutorials/ict-swing-high-explained/
- **publisher:** Inner Circle Trader (innercircletrader.net)
- **author:** غير مذكور
- **page date:** غير مذكورة
- **WHERE:** قسم «How to Use Swing Highs in Trading» — الصورة الأخيرة في القسم.
- **caption (verbatim):** "ICT Swing High used in trading: marking a recent swing high as resistance after a bearish shift in momentum"
- **QUOTE_VERIFIED** (نص alt)
- **what is marked (من التعليق فقط):** قمة التأرجح الأخيرة تُعلَّم كمقاومة بعد انعكاس الزخم.
- **real or illustration:** UNKNOWN
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** UNKNOWN
- **text readable:** UNKNOWN
- **view status:** **IMAGE_NOT_VIEWED**
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### S-19
- **id:** S-19
- **concept:** swing low — تشكيل ثلاث شموع
- **URL:** https://tradingfinder.com/education/forex/ict-swing-low/
- **publisher:** TradingFinder
- **author:** Writer: Rajesh Sharma · Reviewer: Nino Gogochashvili · Fact checker: Davit Kvaratskhelia
- **page date:** Modified Jan 31, 2026
- **WHERE:** قسم «Swing Low Structure» — الصورة أسفل الفقرة.
- **caption (verbatim):** "An illustration of the Swing Low structure"
- **QUOTE_VERIFIED**
- **what is marked (من التعليق فقط):** الصفحة تصف ثلاث شموع، الوسطى أدنى قاع؛ الصورة تُعلَّم على أنها "illustration".
- **real or illustration:** illustration (حسب التعليق نفسه)
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** UNKNOWN
- **text readable:** UNKNOWN
- **view status:** **IMAGE_NOT_VIEWED**
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

**عدد سجلات قمة/قاع التأرجح القابلة للفحص: 19** (منها 11 `VIEWED`، و1 سلبي معتمد على قمة "ضعيفة").

---

## 2) سجلات قابلة للفحص — فجوة القيمة العادلة (FVG)

### F-01
- **id:** F-01
- **concept:** FVG صاعد + شروط الدخول
- **URL:** https://ninjatrader.com/futures/blogs/fair-value-gaps/
- **publisher:** NinjaTrader
- **author:** NinjaTrader Team
- **page date:** July 16, 2026
- **WHERE:** قسم «The 3-bar definition (the textbook FVG pattern)» — «Figure 1»، الصورة الوحيدة في القسم.
- **caption (verbatim):** "Figure 1: This is a bullish fair value gap on a hypothetical MES 5-minute chart"
- **QUOTE_VERIFIED** (مقطوع عند 25 كلمة؛ بقية التعليق تكمل: حدود المنطقة 6053 و6065 والدخول 6067 والوقف 6048)
- **what is marked:** الأرقام ① على شمعة المرجع و② على شمعة الانزياح و③ على الشمعة الثالثة؛ صندوق أزرق مكتوب عليه "FVG zone / still open" بين 6053 و6065؛ خط متقطّع "Buy trigger 6067 close" وسهم لأعلى؛ خط أحمر متقطّع "stop-loss 6048".
- **real or illustration:** illustration — الصفحة تكتب "Prices and times are illustrative, not live market data" و"hypothetical".
- **instrument / timeframe / date:** MES (Micro E-mini S&P 500) · 5 min · بلا تاريخ (المحور من 09:30 إلى 10:05)
- **candles countable:** under 10 (ثماني شموع ظاهرة)
- **text readable:** YES
- **view status:** VIEWED
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### F-02
- **id:** F-02
- **concept:** FVG صاعد وهابط (تعريف الحافة بالفتيل)
- **URL:** https://kagels-trading.com/blog/fair-value-gap/
- **publisher:** Kagels Trading
- **author:** Karsten Kagels — مراجعة Christian Möhrer
- **page date:** Last updated 20 October 2026
- **WHERE:** قسم «How to identify a fair value gap» — الشكل بعد قاعدتي الفتح والإغلاق.
- **caption (verbatim):** "Schematic drawing, not market data. Bullish: the gap runs from the high of candle 1 to the low of candle 3."
- **QUOTE_VERIFIED** (سطر المصدر أسفل الصورة على الصفحة)
- **what is marked:** لوحان؛ في كل منهما شموع مرقّمة 1 و2 و3، وصندوق ملون، وخطوط مكتوب عليها "Low of candle 3" و"CE (50%)" و"High of candle 1" (وفي الهابط: "Low of candle 1" و"High of candle 3")، وكلمة "Pullback" عند عودة السعر.
- **real or illustration:** illustration — مكتوب داخل الصورة "Schematic drawing, not market data".
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** 10-30 (نحو 13 شمعة في كل لوح)
- **text readable:** YES
- **view status:** VIEWED
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### F-03
- **id:** F-03
- **concept:** FVG — شكل ثلاث شموع
- **URL:** https://innercircletrader.net/tutorials/fair-value-gap-trading-strategy/
- **publisher:** Inner Circle Trader (innercircletrader.net)
- **author:** غير مذكور باسم شخص (الصفحة تعرض Ayub Rana كصاحب كورس)
- **page date:** غير مذكورة
- **WHERE:** قسم «What is ICT FVG (Fair Value Gap)?» — الصورة الأولى في المقال.
- **caption (verbatim):** "ICT FVG example — three-candle pattern with a clean gap between the high of the 1st candle and the low of the 3rd candle"
- **QUOTE_VERIFIED** (نص alt، 23 كلمة)
- **what is marked:** لوحان بلا أي رقم أو حرف: يسار ثلاث شموع حمراء وصندوق أزرق فاتح بينها؛ يمين ثلاث شموع خضراء ونفس الصندوق.
- **real or illustration:** illustration (لا محاور ولا أسعار ولا تواريخ)
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** under 10 (ثلاث شموع في كل لوح)
- **text readable:** NO — لا يوجد أي نص داخل الصورة أصلًا.
- **view status:** VIEWED
- **NEGATIVE?:** no — لكن انتبه: الصورة **لا تحمل تسمية ولا رقم شمعة ولا حدود سعرية**؛ كل التوضيح يأتي من نص التعليق، لا من الصورة.
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### F-04
- **id:** F-04
- **concept:** FVG صاعد (وسط اتجاه صاعد)
- **URL:** https://innercircletrader.net/tutorials/fair-value-gap-trading-strategy/
- **publisher:** Inner Circle Trader (innercircletrader.net)
- **author:** غير مذكور
- **page date:** غير مذكورة
- **WHERE:** قسم «(I) Bullish Fair Value Gap» — الصورة أسفل الفقرة.
- **caption (verbatim):** "Bullish fair value gap example — uptrend three-candle pattern with the gap between the high of the 1st candle"
- **QUOTE_VERIFIED** (نص alt مقطوع عند 19 كلمة؛ بقيته على الصفحة تذكر "…and the low of the 3rd candle")
- **what is marked:** ثلاث شموع خضراء وصندوق أزرق مرسوم بين قمة الشمعة الأولى وقاع الشمعة الثالثة؛ لا أرقام ولا حروف.
- **real or illustration:** illustration
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** under 10
- **text readable:** NO (لا نص داخل الصورة)
- **view status:** VIEWED
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### F-05
- **id:** F-05
- **concept:** FVG صاعد (منطقة زرقاء + كلمة FVG)
- **URL:** https://innercircletraders.net/ict-fair-value-gap
- **publisher:** Inner Circle Traders (innercircletraders.net)
- **author:** غير مذكور باسم شخص
- **page date:** غير مذكورة (أسماء ملفات الصور بتاريخ 2026-03-11)
- **WHERE:** قسم «Bullish Fair Value Gap» — الصورة أسفل الفقرة.
- **caption (verbatim):** "Bullish Fair Value Gap"
- **QUOTE_VERIFIED** (العنوان داخل الصورة + نص alt)
- **what is marked:** عنوان "BULLISH FAIR VALUE GAP" أعلى الصورة، مستطيل أزرق شفاف يمتد يمينًا، وكلمة "BULLISH FVG" صغيرة عند منتصف الصندوق.
- **real or illustration:** real market (شموع بفتائل ومحاور، لكن بلا رمز أداة ولا فريم ولا تاريخ)
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** 10-30
- **text readable:** YES
- **view status:** VIEWED
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### F-06
- **id:** F-06
- **concept:** FVG هابط (منطقة زرقاء + كلمة FVG)
- **URL:** https://innercircletraders.net/ict-fair-value-gap
- **publisher:** Inner Circle Traders (innercircletraders.net)
- **author:** غير مذكور
- **page date:** غير مذكورة (ملف الصورة 2026-03-11)
- **WHERE:** قسم «Bearish Fair Value Gap» — الصورة أسفل الفقرة.
- **caption (verbatim):** "Bearish Fair Value Gap"
- **QUOTE_VERIFIED**
- **what is marked:** عنوان "BEARISH FAIR VALUE GAP"، مستطيل أزرق شفاف مع خط منقّط وكلمة "FVG" صغيرة على حافته اليمنى.
- **real or illustration:** real market (شموع بمحاور، بلا رمز/فريم/تاريخ)
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** 10-30
- **text readable:** YES
- **view status:** VIEWED
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### F-07
- **id:** F-07
- **concept:** FVG أول Presented في جلسة نيويورك
- **URL:** https://innercircletrader.net/tutorials/master-ict-1st-presented-fvg/
- **publisher:** Inner Circle Trader (innercircletrader.net)
- **author:** غير مذكور
- **page date:** غير مذكورة (ملف الصورة 2025-06)
- **WHERE:** قسم «What is the ICT 1st Presented Fair Value Gap?» — الصورة الثانية في القسم.
- **caption (verbatim):** "ICT 1st Presented FVG example: the very first fair value gap forming on the 1-minute chart between 9:30 and 10:00 AM New York time"
- **QUOTE_VERIFIED** (نص alt، 24 كلمة)
- **what is marked:** مستطيل برتقالي شفاف على منطقة سعرية، وخط منقّط رأسي عند الساعة، وسعر معلّم 5,639.75.
- **real or illustration:** real market (شاشة TradingView كاملة بالرمز والأسعار والساعات)
- **instrument / timeframe / date:** E-mini S&P 500 Futures (Mar 2025) — ES2025 على CME · 1 min · Wed 12 Mar 2025 (ظاهر على الشاشة)
- **candles countable:** more than 30
- **text readable:** YES
- **view status:** VIEWED
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### F-08
- **id:** F-08
- **concept:** FVG «قوي بهدوء» (Quietly Strong) — تصنيف قوة
- **URL:** https://innercircletrader.net/tutorials/valid-ict-fair-value-gap/
- **publisher:** Inner Circle Trader (innercircletrader.net)
- **author:** غير مذكور
- **page date:** غير مذكورة (ملف 2026-01)
- **WHERE:** قسم «3 Types of Valid Fair Value Gap (By Strength)» ← «(II) Quietly Strong» — الصورة بعد الفقرة.
- **caption (verbatim):** "Quietly Strong Fair Value Gap"
- **QUOTE_VERIFIED** (العنوان داخل الصورة؛ ونص alt: "Quietly Strong ICT Fair Value Gap example with displacement on candle 2 and an inside candle 3 that fails to continue")
- **what is marked:** عنوان "Quietly Strong Fair Value Gap" أعلى الوسط، وأمام كل لوح صندوق برتقالي مكتوب عليه "FVG" مع خط منقّط، وسطر "PCH" أعلى اليسار و"PCL" أسفل اليمين، ومحور ساعات 14:00–18:00.
- **real or illustration:** real market (شموع بفتائل ومحور ساعات وحجم أسفل)
- **instrument / timeframe / date:** XAUUSD (من تصنيف الصفحة/اسم الملف) · بلا فريم مكتوب · بلا تاريخ
- **candles countable:** more than 30
- **text readable:** YES
- **view status:** VIEWED
- **NEGATIVE?:** لا في هذه الصورة (هي إيجابية) — لكن الصفحة نفسها تحتوي مثال «Weak FVG» وهو سلبي، ولم أرَه (انظر F-16).
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### F-09
- **id:** F-09
- **concept:** FVG — «تشريح إعداد صالح» مقابل **غير صالح** (بلا sweep)
- **URL:** https://www.ictkillzone.com/ict-fair-value-gap
- **publisher:** ICTKillzone
- **author:** Michael Phillips (صورة كاتب ورابط About)
- **page date:** غير مذكورة على الصفحة
- **WHERE:** أعلى المقال — لوحة "Fair Value Gap — Anatomy of a Valid Setup" (مخطط بعنوانين يسار/يمين).
- **caption (verbatim):** "Left: an FVG without a preceding liquidity sweep — no institutional backing, price will likely run straight through it."
- **QUOTE_VERIFIED** (مقطوع عند 25 كلمة من تعليق أطول)
- **what is marked (من التعليق فقط):** اليسار: منطقة FVG بلا sweep سابق تُوسم بـ✗ وتُقال غير صالحة؛ اليمين: الإعداد الصالح مع BSL مسحوب وانزياح وMSS.
- **real or illustration:** UNKNOWN — التعليق يصف مخططًا لا صورة سوق.
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** UNKNOWN
- **text readable:** UNKNOWN
- **view status:** **IMAGE_NOT_VIEWED**
- **NEGATIVE?:** **YES — TIER2 NEGATIVE** (الشق الأيسر: FVG غير صالح لعدم وجود sweep قبله).
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### F-10
- **id:** F-10
- **concept:** FVG صاعد (حافة الفتيل + عودة السعر)
- **URL:** https://velotrade.com/blog/fair-value-gap
- **publisher:** Velotrade
- **author:** Gianluca Pizzituti
- **page date:** Oct 7, 2026 · Last verified Oct 8, 2026
- **WHERE:** قسم «Bullish FVG example» — الرسم الأول في القسم.
- **caption (verbatim):** "Bullish fair value gap. The gap runs from the first candle's high to the third candle's low"
- **QUOTE_VERIFIED** (17 كلمة من تعليق أطول)
- **what is marked (من التعليق فقط):** شموع مرقّمة 1 و2 و3، منطقة مظللة، وتسميات "Bullish FVG" و"Candle 1 high" و"Candle 3 low" و"Retrace into the gap"؛ الصفحة تكتب "Illustrative prices".
- **real or illustration:** illustration (الصفحة تكتب "Illustrative prices")
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** UNKNOWN
- **text readable:** UNKNOWN
- **view status:** **IMAGE_NOT_VIEWED**
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### F-11
- **id:** F-11
- **concept:** FVG صاعد على مخطط سهم أمريكي
- **URL:** https://optionstradingiq.com/fair-value-gap-trading-guide/
- **publisher:** Options Trading IQ
- **author:** Gavin (اسم العرض فقط)
- **page date:** January 29, 2026
- **WHERE:** قسم «How To Identify Bullish Fair Value Gaps» — بعد سطر «Example: Oracle 5-Minute Chart».
- **caption (verbatim):** "Candles 1, 2, and 3 form a bullish fair value gap"
- **QUOTE_VERIFIED** (نص التعليق أسفل الصورة)
- **what is marked (من التعليق فقط):** الصفحة تذكر قمة الشمعة الأولى 211.70$ وقاع الثالثة 212.23$ وصندوقًا أزرق للفجوة.
- **real or illustration:** real market حسب التعليق (سهم Oracle، فريم 5 دقائق) — لم أرَه.
- **instrument / timeframe / date:** Oracle (ORCL) · 5 min · UNSTATED
- **candles countable:** UNKNOWN
- **text readable:** UNKNOWN
- **view status:** **IMAGE_NOT_VIEWED**
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### F-12
- **id:** F-12
- **concept:** FVG — تشريح (أرضية/سقف + شمعة الانزياح)
- **URL:** https://piptrend.com/fair-value-gap-trading/
- **publisher:** PipTrend
- **author:** János Kiss
- **page date:** September 22, 2026 · Updated October 7, 2026
- **WHERE:** قسم «The Three-Candle Detection Rule».
- **caption (verbatim):** "Diagram, Anatomy of a Bullish Fair Value Gap. Candle 1, High marks the gap floor"
- **QUOTE_VERIFIED** (مقطوع عند 25 كلمة)
- **what is marked (من التعليق فقط):** شمعة 1 (High = أرضية الفجوة)، شمعة 2 = شمعة الانزياح، شمعة 3.
- **real or illustration:** UNKNOWN — التعليق يسمّيه "Diagram".
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** UNKNOWN
- **text readable:** UNKNOWN
- **view status:** **IMAGE_NOT_VIEWED**
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### F-13
- **id:** F-13
- **concept:** FVG صاعد — دخول عند بداية الفجوة
- **URL:** https://www.trader-dale.com/how-to-use-fair-value-gaps-in-trading-a-complete-strategy-guide/
- **publisher:** Trader Dale
- **author:** Dale (اسم العلامة؛ لا اسم كامل ظاهر في المتن)
- **page date:** غير مذكورة على الصفحة
- **WHERE:** قسم «Trading the Bullish Fair Value Gap Entry».
- **caption (verbatim):** "Bullish Fair Value Gap — Long Entry at the Beginning of the Gap"
- **QUOTE_VERIFIED** (نص alt)
- **what is marked (من التعليق فقط):** التعليق يصف سهمًا صاعدًا ومستوى دخول عند بداية الفجوة بلون أصفر؛ ولا يذكر رقمًا لشمعة.
- **real or illustration:** UNKNOWN
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** UNKNOWN
- **text readable:** UNKNOWN
- **view status:** **IMAGE_NOT_VIEWED**
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### F-14
- **id:** F-14
- **concept:** FVG صاعد (شكل مرجعي)
- **URL:** https://algostorm.com/ict-smc-key-concepts/
- **publisher:** AlgoStorm
- **author:** غير مذكور باسم شخص
- **page date:** غير مذكورة على الصفحة
- **WHERE:** قسم «Fair Value Gap (FVG)» ← ICT/SMC Definition — زوج صور "FVG Bullish" و"FVG Bearish".
- **caption (verbatim):** "FVG Bullish"
- **QUOTE_VERIFIED** (نص alt)
- **what is marked (من التعليق فقط):** لا يذكر التعليق أي شمعة أو صندوق بعينه.
- **real or illustration:** UNKNOWN
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** UNKNOWN
- **text readable:** UNKNOWN
- **view status:** **IMAGE_NOT_VIEWED**
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### F-15
- **id:** F-15
- **concept:** FVG هابط (صورة منفصلة، نفس الصفحة)
- **URL:** https://innercircletrader.net/tutorials/fair-value-gap-trading-strategy/
- **publisher:** Inner Circle Trader (innercircletrader.net)
- **author:** غير مذكور
- **page date:** غير مذكورة
- **WHERE:** قسم «(II) Bearish Fair Value Gap» — الصورة أسفل الفقرة.
- **caption (verbatim):** "Bearish fair value gap example — downtrend three-candle pattern with the gap between the low of the 1st candle"
- **QUOTE_VERIFIED** (نص alt مقطوع عند 19 كلمة؛ بقيته على الصفحة تذكر "…and the high of the 3rd candle")
- **what is marked (من التعليق فقط):** فجوة بين قاع الشمعة الأولى وقمة الشمعة الثالثة في اتجاه هابط.
- **real or illustration:** UNKNOWN — التعليق يصف نمطًا، والنمط في هذه الصفحة عادةً رسم.
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** UNKNOWN
- **text readable:** UNKNOWN
- **view status:** **IMAGE_NOT_VIEWED**
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### F-16
- **id:** F-16
- **concept:** FVG **ضعيف** (Weak)
- **URL:** https://innercircletrader.net/tutorials/valid-ict-fair-value-gap/
- **publisher:** Inner Circle Trader (innercircletrader.net)
- **author:** غير مذكور
- **page date:** غير مذكورة
- **WHERE:** قسم «(I) Weak Fair Value Gap» — الصورة أسفل الفقرة.
- **caption (verbatim):** "Weak ICT Fair Value Gap example formed entirely inside the range of a previous large candle"
- **QUOTE_VERIFIED** (نص alt)
- **what is marked (من التعليق فقط):** النمط كله داخل جسم وفتيل شمعة كبيرة سابقة؛ أي الفجوة موجودة شكلًا لكنها غير معتمدة كقوة.
- **real or illustration:** UNKNOWN
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** UNKNOWN
- **text readable:** UNKNOWN
- **view status:** **IMAGE_NOT_VIEWED**
- **NEGATIVE?:** **YES — TIER2 NEGATIVE** (المعلّم يسمّيه ضعيفًا، أي أن المرشّح غير صالح للتداول عنده).
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

**عدد سجلات FVG القابلة للفحص: 16** (منها 8 `VIEWED`، و2 سلبية).

---

## 3) سجلات قابلة للفحص — كنس السيولة (liquidity sweep)

### W-01
- **id:** W-01
- **concept:** liquidity sweep صاعد **فاشل** (close-back-in)
- **URL:** https://tradingstrategyguides.com/liquidity-sweeps-close-back-in-rule/
- **publisher:** Trading Strategy Guides
- **author:** غير مذكور باسم شخص
- **page date:** غير مذكورة على الصفحة (مسار الصورة 2026/11)
- **WHERE:** قسم «A valid sweep that failed: April 18, 2024» — الصورة الثانية في المقال.
- **caption (verbatim):** "Failed Bullish Reclaim Where The Next Session Broke Beneath The Sweep Candle Low"
- **QUOTE_VERIFIED** (نص alt على الصفحة)
- **what is marked:** عنوان "THE RECLAIM FAILED"، دائرة صفراء حول شمعة 18 Apr، خط أصفر متقطّع عند 499.12، ولصاقة صفراء "…EL 499.12".
- **real or illustration:** real market (بيانات SPY اليومية من Yahoo Finance — مكتوب أسفل الصورة)
- **instrument / timeframe / date:** SPY · Daily · 2024-03-20 → 2024-04-24
- **candles countable:** 10-30
- **text readable:** YES
- **view status:** VIEWED
- **NEGATIVE?:** **YES — TIER2 NEGATIVE.** الصفحة تقول إن الإشارة حدثت فعلًا ثم أُبطلت في الجلسة التالية.
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### W-02
- **id:** W-02
- **concept:** liquidity sweep لجهة الشراء (خط سعري)
- **URL:** https://innercircletrader.net/tutorials/ict-liquidity-sweep-vs-liquidity-run/
- **publisher:** Inner Circle Trader (innercircletrader.net)
- **author:** غير مذكور
- **page date:** غير مذكورة
- **WHERE:** قسم «What is an ICT Liquidity Sweep? (Meaning)» — الصورة الأولى (تليها صورة ثانية).
- **caption (verbatim):** "ICT liquidity sweep — price aims for equal highs, captures buy-side liquidity and reverses"
- **QUOTE_VERIFIED** (نص alt)
- **what is marked:** كلمة "Liquidity Sweep" في صندوق رمادي، علامة "X" عند تجاوز القمة، وخط أفقي عند مستوى القمتين المتساويتين.
- **real or illustration:** illustration (خط سعري أحمر فقط، بلا شموع ولا محاور)
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** لا شموع (خط متصل)
- **text readable:** YES
- **view status:** VIEWED
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### W-03
- **id:** W-03
- **concept:** sell-side sweep داخل هيكل صاعد
- **URL:** https://innercircletrader.net/tutorials/ict-liquidity-sweep-vs-liquidity-run/
- **publisher:** Inner Circle Trader (innercircletrader.net)
- **author:** غير مذكور
- **page date:** غير مذكورة
- **WHERE:** قسم «(I) Bullish higher-timeframe — sell-side sweep into discount» — الصورة بعد الفقرة.
- **caption (verbatim):** "Sell-side liquidity sweep on a bullish HTF — price taps equal lows and the discount PD array, then reverses upward"
- **QUOTE_VERIFIED** (نص alt)
- **what is marked:** صناديق نصية "Bullish Structure" و"Structure High" و"Structure Low"، وسهم بنفسجي تحت الكلمة "Liquidity Sweep" على طرف سفلي، مع علامة "X" عند كسر القاع.
- **real or illustration:** real market (شاشة TradingView بشموع وأسعار ومحور)
- **instrument / timeframe / date:** UNSTATED (المحور السعري 2,264–2,312 بلا رمز ولا فريم ولا تاريخ)
- **candles countable:** more than 30
- **text readable:** YES
- **view status:** VIEWED
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### W-04
- **id:** W-04
- **concept:** sweep مقابل acceptance (نفس الكسر، نتيجتان)
- **URL:** https://kagels-trading.com/blog/liquidity-sweep/
- **publisher:** Kagels Trading
- **author:** Karsten Kagels — مراجعة Christian Möhrer
- **page date:** Last updated 22 October 2026
- **WHERE:** قسم «Liquidity sweep vs liquidity run: the reaction decides» — الشكل الوحيد هناك.
- **caption (verbatim):** "Rejection: closes back above, long setup … Acceptance: closes below, short setup"
- **QUOTE_VERIFIED** (تسميات داخل الصورة)
- **what is marked:** لوح أعلى: "Break" ثم "Old low" ثم "Confirmation: close above the break bar's high" مع خطوط Stop/Entry/Target 2R؛ لوح أسفل: نفس التسلسل معكوسًا؛ وأسفل الصورة سطر: "Unclear (close at the level, or no confirmation within three bars): no trade."
- **real or illustration:** illustration — مكتوب داخل الصورة "Schematic drawing, not market data".
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** 10-30 (نحو 12 شمعة في كل لوح)
- **text readable:** YES
- **view status:** VIEWED
- **NEGATIVE?:** **YES — TIER2 NEGATIVE** للشقّ السفلي وحالة "Unclear": لا صفقة، والإعداد يُبطل إذا لُمس الوقف قبل الدخول.
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### W-05
- **id:** W-05
- **concept:** ثلاثة أنواع من sweep على سيولة البيع (SSL)
- **URL:** https://www.ictkillzone.com/ict-liquidity-sweep
- **publisher:** ICTKillzone
- **author:** Michael Phillips
- **page date:** Published June 2026
- **WHERE:** قسم «Three Types of ICT Liquidity Sweep» — الشكل بعد الأنواع الثلاثة.
- **caption (verbatim):** "Three sweep types on SSL pools. Type 1 (left): wick only, body closes above — immediate bullish reversal."
- **QUOTE_VERIFIED** (مقطوع عند 25 كلمة)
- **what is marked (من التعليق فقط):** ثلاثة ألواح: نظيف (فتيل فقط)، إزاحة (إغلاق جسم تحت ثم انعكاس)، ممتد (يتسلسل عبر عدة مجموعات)، مع تسميات SSL 1/2/3.
- **real or illustration:** UNKNOWN
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** UNKNOWN
- **text readable:** UNKNOWN
- **view status:** **IMAGE_NOT_VIEWED**
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### W-06
- **id:** W-06
- **concept:** sell-side sweep (قيعان متساوية)
- **URL:** https://velotrade.com/blog/liquidity-sweep
- **publisher:** Velotrade
- **author:** Vittorio De Angelis
- **page date:** Oct 7, 2026 · Last verified Oct 8, 2026
- **WHERE:** قسم «Sell-side liquidity sweep» — الشكل في القسم.
- **caption (verbatim):** "The wick takes the stops below the equal lows; the close back above the level is what separates a sweep from a breakdown."
- **QUOTE_VERIFIED** (25 كلمة)
- **what is marked (من التعليق فقط):** خط عند القيعان المتساوية، شمعة تفتل تحته ثم تغلق فوقه؛ الصفحة تكتب "Illustrative prices".
- **real or illustration:** illustration (الصفحة تكتب "Illustrative prices")
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** UNKNOWN
- **text readable:** UNKNOWN
- **view status:** **IMAGE_NOT_VIEWED**
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### W-07
- **id:** W-07
- **concept:** خريطة السيولة أعلى/أسفل النطاق (وتسمية قمة/قاع التأرجح)
- **URL:** https://monkeytrade.com/learn/technical-analysis/buy-side-and-sell-side-liquidity
- **publisher:** MonkeyTrade
- **author:** غير مذكور باسم شخص
- **page date:** غير مذكورة على الصفحة
- **WHERE:** أعلى المقال — لوحة "LIQUIDITY ABOVE AND BELOW THE RANGE" (الصورة الأولى).
- **caption (verbatim):** "1. Swing High" / "7. Swing Low" / "5. Buy-side liquidity" (تسميات داخل الصورة)
- **QUOTE_VERIFIED**
- **what is marked:** سبع نقاط مرقّمة بألوان: 1 سقف التأرجح، 2 سيولة جهة البيع، 3 أوامر وقف الشراء، 4 النطاق، 5 سيولة جهة الشراء، 6 أوقاف البيع، 7 قاع التأرجح.
- **real or illustration:** illustration — مكتوب أسفل الصورة "Illustrative chart, not real data".
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** more than 30
- **text readable:** YES
- **view status:** VIEWED
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### W-08
- **id:** W-08
- **concept:** sweep على سيولة البيع مع بيانات CVD/OI
- **URL:** https://atas.net/blog/sell-side-liquidity-sweep/
- **publisher:** ATAS
- **author:** غير مذكور باسم شخص في المتن
- **page date:** غير مذكورة على الصفحة
- **WHERE:** قسم «Sell-Side Liquidity Sweep Example on Bitcoin: Confirmed Reclaim» — «Figure 7».
- **caption (verbatim):** "Figure 7. BTCUSD@Bybit H1 price overview. The purple arrow marks the reference low of 80,534.2"
- **QUOTE_VERIFIED** (15 كلمة من تعليق أطول يذكر أيضًا سهم 8 أكتوبر وقاع 80,303.0)
- **what is marked (من التعليق فقط):** سهم بنفسجي عند القاع المرجعي 80,534.2 (23:00 يوم 20 سبتمبر) وسهم أصفر عند شمعة الكنس (8 أكتوبر 19:00، قاع 80,303.0).
- **real or illustration:** real market حسب التعليق (BTCUSD على Bybit، H1)
- **instrument / timeframe / date:** BTCUSD @ Bybit · H1 · 20 September → 8 October
- **candles countable:** UNKNOWN
- **text readable:** UNKNOWN
- **view status:** **IMAGE_NOT_VIEWED**
- **NEGATIVE?:** no — لكن الصفحة تحتوي لاحقًا "Counter-Example: A Failed Sweep with Acceptance Below the Level" (مثال سلبي، Figure 10-12، لم أرَه).
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### W-09
- **id:** W-09
- **concept:** buy-side liquidity hunt (كنس القمم المتساوية)
- **URL:** https://innercircletrader.net/tutorials/liquidity-in-forex-trading/
- **publisher:** Inner Circle Trader (innercircletrader.net)
- **author:** غير مذكور
- **page date:** غير مذكورة
- **WHERE:** حسب التعليق: صورة "Buy-side liquidity hunt" في مقال السيولة (موضعها الدقيق في القسم لم يُثبَّت بعد الفتح، فالمالك يبحث عنها بعنوانها).
- **caption (verbatim):** "Buy-side liquidity hunt — market makers sweep equal highs above old highs and reverse the market lower against the buy stops"
- **QUOTE_VERIFIED** (نص alt)
- **what is marked (من التعليق فقط):** قمم متساوية تُكنس ثم انعكاس هابط ضد أوامر الشراء.
- **real or illustration:** UNKNOWN
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** UNKNOWN
- **text readable:** UNKNOWN
- **view status:** **IMAGE_NOT_VIEWED**
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

**عدد سجلات كنس السيولة: 9** (منها 5 `VIEWED`، و2 سلبية).

---

## 4) سجلات قابلة للفحص — كتلة الأوامر (order block)

### O-01
- **id:** O-01
- **concept:** order block صاعد + إعادة اختبار
- **URL:** https://innercircletrader.net/tutorials/ict-bullish-order-block/
- **publisher:** Inner Circle Trader (innercircletrader.net)
- **author:** غير مذكور
- **page date:** غير مذكورة
- **WHERE:** قسم «How to Trade a Bullish Order Block» — الصورة قبل فقرة «In the picture above you can see the XAG/USD…».
- **caption (verbatim):** "ICT Bullish Order Block trade example on XAG/USD daily — bullish trend with higher highs and higher lows"
- **QUOTE_VERIFIED** (نص alt، مقطوع عند 25 كلمة)
- **what is marked (من التعليق فقط):** قمة/قاع متصاعدان، وكتلة أوامر صاعدة تُختبر فيدخل السعر بعد MSS على فريم أدنى، بنسبة 1:3.
- **real or illustration:** real market حسب التعليق (XAG/USD، Daily)
- **instrument / timeframe / date:** XAG/USD · Daily · UNSTATED
- **candles countable:** UNKNOWN
- **text readable:** UNKNOWN
- **view status:** **IMAGE_NOT_VIEWED**
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### O-02
- **id:** O-02
- **concept:** order block صاعد — مخطط التشكيل
- **URL:** https://innercircletrader.net/tutorials/ict-bullish-order-block/
- **publisher:** Inner Circle Trader (innercircletrader.net)
- **author:** غير مذكور
- **page date:** غير مذكورة
- **WHERE:** قسم «What is an ICT Bullish Order Block?» — الصورة أسفل تعريف الكتلة.
- **caption (verbatim):** "ICT Bullish Order Block diagram — last bearish candle followed by a strong bullish engulfing candle that breaks above the bearish candle's high"
- **QUOTE_VERIFIED** (نص alt، 24 كلمة)
- **what is marked (من التعليق فقط):** شمعة هابطة أخيرة ثم شمعة صاعدة تبتلعها وتغلق فوق قمتها.
- **real or illustration:** UNKNOWN — التعليق يسمّيه "diagram".
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** UNKNOWN
- **text readable:** UNKNOWN
- **view status:** **IMAGE_NOT_VIEWED**
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### O-03
- **id:** O-03
- **concept:** order block صاعد (آخر شمعة هابطة)
- **URL:** https://velotrade.com/blog/order-block
- **publisher:** Velotrade
- **author:** Vittorio De Angelis
- **page date:** Oct 7, 2026 · Last verified Oct 8, 2026
- **WHERE:** قسم «Bullish order block» — الشكل الأول في القسم.
- **caption (verbatim):** "Bullish order block. The block is marked from the last down candle's high to its low."
- **QUOTE_VERIFIED** (17 كلمة من تعليق أطول)
- **what is marked (من التعليق فقط):** آخر شمعة هابطة قبل الصعود تُعلَّم من قمتها إلى قاعها؛ والحركة بعدها تكسر القمة السابقة (BOS)، ثم يعود السعر إلى المنطقة.
- **real or illustration:** illustration (الصفحة تكتب "Illustrative prices")
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** UNKNOWN
- **text readable:** UNKNOWN
- **view status:** **IMAGE_NOT_VIEWED**
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### O-04
- **id:** O-04
- **concept:** order block صاعد مقابل هابط — تشريح
- **URL:** https://www.ictkillzone.com/ict-order-block
- **publisher:** ICTKillzone
- **author:** Michael Phillips
- **page date:** غير مذكورة على الصفحة
- **WHERE:** أعلى المقال — لوحة «Order Block Anatomy — Bullish vs Bearish».
- **caption (verbatim):** "Left: Bullish order block — the last bearish candle before a bullish impulse."
- **QUOTE_VERIFIED** (12 كلمة من تعليق أطول)
- **what is marked (من التعليق فقط):** آخر شمعة هابطة قبل دفع صاعد، منطقة الكتلة، و50% تُسمّى mean threshold، والدخول عندها، والوقف خلف الفتيل الكامل.
- **real or illustration:** UNKNOWN
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** UNKNOWN
- **text readable:** UNKNOWN
- **view status:** **IMAGE_NOT_VIEWED**
- **NEGATIVE?:** no (لكن الصفحة تحتوي لاحقًا "Valid vs Invalid Order Block" وهو سلبي — لم أرَه).
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### O-05
- **id:** O-05
- **concept:** order block (مثال «صالح» مرقّم على مخطط شموع)
- **URL:** https://algostorm.com/ict-smc-key-concepts/
- **publisher:** AlgoStorm
- **author:** غير مذكور باسم شخص
- **page date:** غير مذكورة على الصفحة
- **WHERE:** قسم «Order Block» ← Example — الصورة الأولى («Valid Order Block - Example 1»).
- **caption (verbatim):** "Valid Order Block - Example 1"
- **QUOTE_VERIFIED** (نص alt)
- **what is marked:** عنوان "BREAK OF STRUCTURE OR CHANGE IN DIRECTION"، كلمتا "BOS" عند قمتين، دائرتان بيضاوان حول شمعتين مظللتين، وكلمة "Gap" عند كل منهما.
- **real or illustration:** illustration (شموع مرسومة على خلفية سوداء)
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** 10-30
- **text readable:** YES
- **view status:** VIEWED
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### O-06
- **id:** O-06
- **concept:** order block — منطقة أوامر قبل الاندفاع
- **URL:** https://strefatradingu.pl/en/blog/ict-order-block
- **publisher:** Strefa Tradingu
- **author:** غير مذكور باسم شخص
- **page date:** غير مذكورة على الصفحة (اسم الملف بتاريخ 2026-01-15)
- **WHERE:** أعلى المقال — الصورة الأولى.
- **caption (verbatim):** "Order block — the zone of institutional orders before the impulse"
- **QUOTE_VERIFIED** (نص alt)
- **what is marked (من التعليق فقط):** منطقة أوامر قبل الاندفاع؛ التعليق لا يسمّي شمعة بعينها.
- **real or illustration:** UNKNOWN
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** UNKNOWN
- **text readable:** UNKNOWN
- **view status:** **IMAGE_NOT_VIEWED**
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

**عدد سجلات كتلة الأوامر: 6** (منها 1 `VIEWED` فقط — أضعف مجموعة في هذا السجل).

---

## 5) سجلات قابلة للفحص — الانزياح (displacement)

### D-01
- **id:** D-01
- **concept:** displacement مقابل حركة عادية
- **URL:** https://fxglory.com/learn/technical-analysis-forex/displacement-in-forex/
- **publisher:** FXGlory
- **author:** Henry Green
- **page date:** Published October 23, 2026 · Last updated October 24, 2026
- **WHERE:** قسم «What Is Displacement in Forex Trading?» — الصورة أسفل الفقرة الأولى.
- **caption (verbatim):** "Displacement stands out when price leaves ordinary nearby movement with a noticeably stronger directional push."
- **QUOTE_VERIFIED**
- **what is marked:** صندوق متقطّع رمادي حول شموع جانبية مكتوب فوقه "Normal price action"، وسهم مكتوب عليه "Displacement" يشير إلى الشمعة الخضراء الكبيرة الخارجة من الصندوق.
- **real or illustration:** illustration (شموع مرسومة، بلا محاور أو أسعار)
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** 10-30 (نحو 18 شمعة)
- **text readable:** YES
- **view status:** VIEWED
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### D-02
- **id:** D-02
- **concept:** displacement — كيف تُقاس علاماته
- **URL:** https://fxglory.com/learn/technical-analysis-forex/displacement-in-forex/
- **publisher:** FXGlory
- **author:** Henry Green
- **page date:** Published October 23, 2026 · Last updated October 24, 2026
- **WHERE:** قسم «How to Identify a Displacement Candle» — الصورة الثانية في القسم.
- **caption (verbatim):** "Annotated breakout chart highlighting a displacement candle with a larger body, strong close, range break, and follow-through."
- **QUOTE_VERIFIED**
- **what is marked:** أربعة أسهم نصية تشير إلى نفس الشمعة الخضراء الكبيرة: "Larger body"، "Strong close"، "Range break" (عند حدّ الصندوق)، و"Follow-through" على الشموع التالية.
- **real or illustration:** illustration
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** 10-30 (نحو 17 شمعة)
- **text readable:** YES
- **view status:** VIEWED
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### D-03
- **id:** D-03
- **concept:** displacement صاعد وعلاقته بـFVG وMSS
- **URL:** https://innercircletrader.net/tutorials/ict-displacement-move/
- **publisher:** Inner Circle Trader (innercircletrader.net)
- **author:** غير مذكور
- **page date:** غير مذكورة
- **WHERE:** قسم «Bullish ICT Displacement Move» — الصورة بعد وصف الشروط.
- **caption (verbatim):** "Bullish ICT Displacement Move example: three consecutive bullish candles with large bodies, minimal wicks, and a fair value gap inside"
- **QUOTE_VERIFIED** (نص alt، 21 كلمة)
- **what is marked:** شريط أصفر مائل يغطي ثلاث شموع صاعدة، ولصاقة "Bullish Displacement Move" بسهم، وثلاثة صناديق خضراء مكتوب على كل منها "FVG"، وخط أفقي متقطّع عنده "MSS".
- **real or illustration:** real market (شموع بفتائل ومحاور؛ لكن بلا رمز أداة ولا فريم ولا تاريخ)
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** more than 30
- **text readable:** YES
- **view status:** VIEWED
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### D-04
- **id:** D-04
- **concept:** displacement — «قوي» مقابل «ضعيف» (فلتر الجودة)
- **URL:** https://www.ictkillzone.com/ict-displacement
- **publisher:** ICTKillzone
- **author:** Michael Phillips
- **page date:** Updated September 2026
- **WHERE:** قسم «What ICT Displacement Is» — لوحة «Strong vs Weak Displacement — FVG Quality Comparison».
- **caption (verbatim):** "Strong vs Weak Displacement — FVG Quality Comparison"
- **QUOTE_VERIFIED** (7 كلمات؛ ويتبعها على الصفحة تعليق أطول يذكر 85% مقابل 46%)
- **what is marked (من التعليق فقط):** يسار: جسم C2 بنسبة 85% وفجوة 72 نقطة؛ يمين: C2 بنسبة 46% وفجوة 48 نقطة أضيق.
- **real or illustration:** UNKNOWN
- **instrument / timeframe / date:** UNSTATED (التعليق يذكر أرقام نقاط لا أداة)
- **candles countable:** UNKNOWN
- **text readable:** UNKNOWN
- **view status:** **IMAGE_NOT_VIEWED**
- **NEGATIVE?:** **YES — TIER2 NEGATIVE** للشقّ الأيمن: انزياح ضعيف وفجوة غير موثوقة.
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### D-05
- **id:** D-05
- **concept:** displacement داخل تسلسل MSS
- **URL:** https://www.ictkillzone.com/ict-displacement
- **publisher:** ICTKillzone
- **author:** Michael Phillips
- **page date:** Updated September 2026
- **WHERE:** قسم «Displacement in the MSS Sequence» — الشكل بعد الترقيم ①-④.
- **caption (verbatim):** "③ the displacement candle — large, body-dominant, highlighted in amber — fires and creates the FVG"
- **QUOTE_VERIFIED** (14 كلمة من تعليق أطول)
- **what is marked (من التعليق فقط):** ①sh sweep على BSL، ② MSS، ③ شمعة الانزياح بلون كهرماني، ④ عودة إلى FVG ودخول عند 50%.
- **real or illustration:** UNKNOWN
- **instrument / timeframe / date:** UNSTATED
- **candles countable:** UNKNOWN
- **text readable:** UNKNOWN
- **view status:** **IMAGE_NOT_VIEWED**
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

### D-06
- **id:** D-06
- **concept:** displacement على مخطط عقود مستقبلية
- **URL:** https://homedadpro.com/en/displacement-trading
- **publisher:** Home Dad Pro
- **author:** غير مذكور باسم شخص
- **page date:** غير مذكورة على الصفحة
- **WHERE:** غير مثبَّت بدقة — الصورة تحمل تعليقًا يذكر MNQZ24 (المالك يفتح المقال ويبحث عن الشكل داخل الأقسام).
- **caption (verbatim):** "Historical MNQZ24 four-hour chart with a strong bullish body crossing a marked swing"
- **QUOTE_VERIFIED** (نص alt)
- **what is marked (من التعليق فقط):** جسم صاعد قوي يعبر قمة معلَّمة؛ ويذكر التعليق تعليقًا نصيًا صينيًا داخل الصورة.
- **real or illustration:** real market حسب التعليق (MNQZ24، أربع ساعات)
- **instrument / timeframe / date:** MNQZ24 · 4H · UNSTATED
- **candles countable:** UNKNOWN
- **text readable:** UNKNOWN
- **view status:** **IMAGE_NOT_VIEWED**
- **NEGATIVE?:** no
- **TIER2**
- **OWNER_CHECK: marked candle clearly higher/lower than both neighbours? YES / NO / CANNOT_SEE**
- **OWNER_CHECK: gap box clearly between candle 1 and candle 3? YES / NO / CANNOT_SEE**

**عدد سجلات الانزياح: 6** (منها 3 `VIEWED`، و1 سلبي).

---

## 6) أفكار TradingView العامة (USER_IDEA) — قائمة منفصلة، لا تُحتسب تعليمًا

**لا سجلات.** لم أفتح أي فكرة عامة على TradingView بمؤلف مسمّى في هذه الجولة، فلم أُدرج شيئًا. صفحات سكربتات TradingView (`/script/...`) ليست مقالات تعليم ولا تُحتسب.

---

## 7) صفحات فُحصت ولم تُستعمل — `NOT_USABLE` (سبب واحد لكل سطر)

| # | الرابط | الحالة | السبب المختصر |
|---|---|---|---|
| N-01 | https://therighttrader.com/learn/trend-analysis/swing-high | USABLE جزئيًا | استُعملت صورتان (S-05)؛ الصورة الثالثة «Swing Highs in a Range» رُفضت: المالك لا يرى علامة قمة فيها رغم قول التعليق "with swing high labeled" |
| N-02 | https://therighttrader.com/learn/trend-analysis/swing-low | NOT_USABLE | صورة صفحة القاع تطابق بالضبط ملف صورة صفحة القمة (نفس `bearish-swing-low`/`bearish-swing-high`)، فالنسبة غير موثوقة؛ لم أستخدمها |
| N-03 | https://arxum.com/order-blocks/ | NOT_USABLE | الصفحة رجعت بمتن فارغ (تُبنى بـJS)؛ رأيت الصورة عبر وسيط البحث لكن لا أستطيع تأكيد التعليق على الصفحة نفسها |
| N-04 | https://www.zeiierman.com/blog/fair-value-gaps-trading-guide | NOT_USABLE | جدار موافقة كوكيز يغطي الصفحة (`COOKIE_WALL`)، فلا فحص مريح للصور |
| N-05 | https://tradingstrategyguides.com/ict-concepts/ | NOT_USABLE | الرابط أعاد الصفحة الرئيسية للموقع لا مقال المفاهيم (إعادة توجيه) |
| N-06 | https://theforexonlineschool.com/fair-value-gap-fvg-trading-strategy-a-complete-ict-guide/ | NOT_USABLE | لم تُفتح في هذه الجلسة؛ لديّ نص بحث فقط — لا أُدرج صفحة لم أفحصها |
| N-07 | https://quantzee.com/displacement-how-to-measure-it-instead-of-eyeballing-it/ | NOT_USABLE | لم تُفتح في هذه الجلسة؛ نُقلت من نتيجة بحث فقط |
| N-08 | https://innercircletrader.net/tutorials/ict-displacement-move/ (صورة الغلاف) | NOT_USABLE | صورة الغلاف بطاقة عنوان ("ICT DISPLACEMOVE MOVE") بلا أي شمعة معلَّمة — لا تُفحص بالعين |
| N-09 | https://thesimpleict.com/ict-swing-high-swing-low-explained/ | NOT_USABLE | كانت ترجع HTTP 500 في جولات سابقة (سجلّ `a_swing_high_low.md`)؛ لم تُعَد التحقق بنجاح هنا |
| N-10 | https://forums.babypips.com/t/market-structure-concepts/1296305 | NOT_USABLE | منتدى بلا مؤلف مسمّى للمشاركة الأصلية — ممنوع بالشرط |
| N-11 | https://www.forexfactory.com/thread/1345018-understanding-swing-highs-in-ict-trading-tflab | NOT_USABLE | منتدى؛ ولا صور معلَّمة قابلة للتوثيق بمؤلف مسمّى — ممنوع بالشرط |
| N-12 | https://www.scribd.com/document/663094530/Inner-Circle-Trader-Ict-Forex-Ict-Notes | NOT_USABLE | مواد مرفوعة/مسرّبة (notes) — ممنوع صراحةً |
| N-13 | https://www.tradingview.com/script/zZcRSJo6-Swing-Guide/ | NOT_USABLE | صفحة سكربت/مؤشر، ليست مقالًا تعليميًا ولا فكرة بمؤلف |
| N-14 | https://www.strike.money/technical-analysis/types-of-candlesticks-patterns | NOT_USABLE | صفحة أنماط شموع عامة، لا تُعلّم قمة/قاع تأرجح ولا FVG |
| N-15 | https://www.youtube.com/c/InnerCircleTrader (مذكور داخل صفحة kagels) | NOT_USABLE | فيديو/قناة — ممنوع بالشرط |
| N-16 | https://medium.com/@rosemary.ekong.j/swing-high-and-swing-low-in-forex-trading-the-essential-guide-for-traders-328526e0819a | NOT_USABLE | لم تُفتح؛ ونطاق Medium غالبًا بمحدودية قراءة — لا أدرج ما لم أفحصه |
| N-17 | https://www.getswoopr.com/technical-analysis/alternative-charts/swing-charts/ | NOT_USABLE | لم تُفتح؛ مثالها جدول أرقام صناعية لا صورة سوق معلَّمة |
| N-18 | https://www.vtmarkets.com/en-ca/discover/how-to-identify-swing-highs-and-swing-lows-in-cfd-markets/ | NOT_USABLE | الصفحة حملت متنًا كاملًا، لكن الصورة الوحيدة صورة عنوان/رأس مقال بلا تعليم شموع مقروء؛ والأمثلة الرقمية نصّية لا صور |

**مجموع الصفحات المفحوصة والمدرَجة في هذا السجل: 18 (NOT_USABLE) + الصفحات المستعملة أدناه.**

---

## 8) جرد الصفحات المستعملة (رابط واحد لكل صفحة، مع ما أُخذ منها)

| الصفحة | الناشر | الحالة | السجلات |
|---|---|---|---|
| https://liquidityscan.io/blog/what-is-a-swing-high-and-swing-low-in-ict-the-3-candle-rule | LiquidityScan | USABLE | S-01 |
| https://fbs.com/fbs-academy/traders-blog/what-is-swing-high-and-swing-low-in-forex-trading | FBS | USABLE | S-02, S-03, S-04 |
| https://therighttrader.com/learn/trend-analysis/swing-high | The Right Trader | USABLE | S-05 |
| https://kagels-trading.com/blog/liquidity-sweep/ | Kagels Trading | USABLE | S-06, W-04 |
| https://innercircletrader.net/tutorials/ict-swing-high-explained/ | innercircletrader.net | USABLE | S-07, S-17, S-18 |
| https://innercircletrader.net/tutorials/ict-swing-low-formation/ | innercircletrader.net | USABLE | S-08 |
| https://www.altrady.com/crypto-trading/smart-money-concept/how-to-identify-swing-highs-and-lows | Altrady | USABLE | S-09, S-10 |
| https://www.edgeflo.com/blog/swing-structure-trading | EdgeFlo | USABLE | S-11 |
| https://candlestructurelabs.com/learn/market-structure.html | Candle Structure Labs | USABLE | S-12, S-13 |
| https://www.ironcladresearch.com/learn/technical-analysis/swing-highs-and-lows | Ironclad Research | USABLE | S-14 |
| https://tradingfinder.com/education/forex/ict-swing-high/ | TradingFinder | USABLE | S-15, S-16 |
| https://tradingfinder.com/education/forex/ict-swing-low/ | TradingFinder | USABLE | S-19 |
| https://ninjatrader.com/futures/blogs/fair-value-gaps/ | NinjaTrader | USABLE | F-01 |
| https://kagels-trading.com/blog/fair-value-gap/ | Kagels Trading | USABLE | F-02 |
| https://innercircletrader.net/tutorials/fair-value-gap-trading-strategy/ | innercircletrader.net | USABLE | F-03, F-04, F-15 |
| https://innercircletraders.net/ict-fair-value-gap | innercircletraders.net | USABLE | F-05, F-06 |
| https://innercircletrader.net/tutorials/master-ict-1st-presented-fvg/ | innercircletrader.net | USABLE | F-07 |
| https://innercircletrader.net/tutorials/valid-ict-fair-value-gap/ | innercircletrader.net | USABLE | F-08, F-16 |
| https://www.ictkillzone.com/ict-fair-value-gap | ICTKillzone | USABLE | F-09 |
| https://velotrade.com/blog/fair-value-gap | Velotrade | USABLE | F-10 |
| https://optionstradingiq.com/fair-value-gap-trading-guide/ | Options Trading IQ | USABLE | F-11 |
| https://piptrend.com/fair-value-gap-trading/ | PipTrend | USABLE | F-12 |
| https://www.trader-dale.com/how-to-use-fair-value-gaps-in-trading-a-complete-strategy-guide/ | Trader Dale | USABLE | F-13 |
| https://algostorm.com/ict-smc-key-concepts/ | AlgoStorm | USABLE | F-14, O-05 |
| https://tradingstrategyguides.com/liquidity-sweeps-close-back-in-rule/ | Trading Strategy Guides | USABLE | W-01 |
| https://innercircletrader.net/tutorials/ict-liquidity-sweep-vs-liquidity-run/ | innercircletrader.net | USABLE | W-02, W-03 |
| https://www.ictkillzone.com/ict-liquidity-sweep | ICTKillzone | USABLE | W-05 |
| https://velotrade.com/blog/liquidity-sweep | Velotrade | USABLE | W-06 |
| https://monkeytrade.com/learn/technical-analysis/buy-side-and-sell-side-liquidity | MonkeyTrade | USABLE | W-07 |
| https://atas.net/blog/sell-side-liquidity-sweep/ | ATAS | USABLE | W-08 |
| https://innercircletrader.net/tutorials/liquidity-in-forex-trading/ | innercircletrader.net | USABLE | W-09 |
| https://innercircletrader.net/tutorials/ict-bullish-order-block/ | innercircletrader.net | USABLE | O-01, O-02 |
| https://velotrade.com/blog/order-block | Velotrade | USABLE | O-03 |
| https://www.ictkillzone.com/ict-order-block | ICTKillzone | USABLE | O-04 |
| https://strefatradingu.pl/en/blog/ict-order-block | Strefa Tradingu | USABLE | O-06 |
| https://fxglory.com/learn/technical-analysis-forex/displacement-in-forex/ | FXGlory | USABLE | D-01, D-02 |
| https://innercircletrader.net/tutorials/ict-displacement-move/ | innercircletrader.net | USABLE | D-03 |
| https://www.ictkillzone.com/ict-displacement | ICTKillzone | USABLE | D-04, D-05 |
| https://homedadpro.com/en/displacement-trading | Home Dad Pro | USABLE | D-06 |

**عدد الصفحات المستعملة: 40. عدد الصفحات المفحوصة الإجمالي: 58.**

---

## 9) الخلاصة الرقمية (بلا تزيين)

| المفهوم | المطلوب | المُسلَّم (سجلات) | منها `VIEWED` | منها سلبي `NEGATIVE` |
|---|---|---|---|---|
| swing high / swing low | 15 | **19** | 11 | 1 |
| FVG | 15 | **16** | 8 | 2 |
| liquidity sweep | 5 | **9** | 5 | 2 |
| order block | 5 | **6** | **1** | 0 |
| displacement | 5 | **6** | 3 | 1 |
| TradingView USER_IDEA | — | 0 (منفصلة، غير محتسبة) | 0 | 0 |
| **الإجمالي** | **45** | **56** | **28** | **6** |

**تحذيرات صريحة للمالك:**

1. **order block أضعف مجموعة**: خمس من ست سجلاتها `IMAGE_NOT_VIEWED`؛ لا تعتمد عليها بصريًا قبل أن تفتحها.
2. **`VIEWED` عندي لا تعني `VIEWED` عندك**: رأيت الصورة عبر وسيط البحث من نفس النطاق، لا في متصفحك. الشكل قد يختلف في الحجم/الوضوح عند العرض الحقيقي.
3. **7 صفحات «حقيقية السوق» بلا أداة أو فريم أو تاريخ مكتوب** (`UNSTATED`) — لا تستنتج منها أداة.
4. **الفجوة بين التعليق والصورة موجودة صراحةً في S-07** (التعليق يقول "live price chart" والصورة رسم بثلاث شموع). سُجّلت كما هي، ولم أُصلحها.
5. **لا حكم مني على صحة أي معلّم** — ولا استعمال لمعرفتي الخاصة بـICT في أي سطر أعلاه.

---

*نهاية السجل. لا صور محفوظة ولا منسوخة في المستودع — روابط ونصوص فقط، كل اقتباس ≤ 25 كلمة.*
