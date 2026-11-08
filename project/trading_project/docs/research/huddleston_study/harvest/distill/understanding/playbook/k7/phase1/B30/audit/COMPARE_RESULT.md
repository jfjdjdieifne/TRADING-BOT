# نتيجة المقارنة (C1–C6) — فحص عينات B30

قاعدة التطابق المُعلنة قبل القراءة (PARAMETERS.md، قسم A1): يُطابق زوج (أصلي، فحص) إذا تداخلت نطاقا كلمتيهما بعد التطبيع N-06 بكلمة واحدة على الأقل، أو كان موضع بداية كلتيهما في حقل النص نفسه أو مجاورًا (بما لا يزيد عن حقل واحد). الأساس الموقعي لا المعنوي. ما لم يُطابق يُبلَّغ بالاتجاهين: أصلي-بدون-طابق (ORIGINAL_ONLY) وفحص-بدون-طابق (AUDIT_ONLY).

## C1 — الأعداد والتطابق

| المقطع | عدد العبارات (أصلي) | عدد العبارات (فحص) | أزواج مطابقة | ORIGINAL_ONLY | AUDIT_ONLY |
|---|---|---|---|---|---|
| F0170#001 | 33 | 32 | 23 | 10 | 9 |
| F0170#003 | 38 | 53 | 36 | 2 | 17 |
| F0171#002 | 10 | 11 | 9 | 1 | 2 |
| F0172#002 | 22 | 47 | 22 | 0 | 25 |
| F0172#003 | 25 | 61 | 25 | 0 | 36 |
| **المجموع** | **128** | **204** | **115** | **13** | **89** |

نسبة الأزواج المطابقة إلى العبارات الأصلية: 89.8%؛ إلى عبارات الفحص: 56.4%.

تفاصيل العبارات غير المطابقة (أرقام العبارات داخل سجل كل جانب):
- F0170#001: ORIGINAL_ONLY = [1, 3, 7, 9, 10, 12, 14, 19, 23, 25]؛ AUDIT_ONLY = [2, 8, 18, 19, 20, 22, 27, 28, 30]
- F0170#003: ORIGINAL_ONLY = [6, 21]؛ AUDIT_ONLY = [4, 7, 8, 11, 12, 23, 24, 30, 31, 33, 34, 38, 39, 40, 42, 48, 52]
- F0171#002: ORIGINAL_ONLY = [2]؛ AUDIT_ONLY = [4, 8]
- F0172#002: ORIGINAL_ONLY = []؛ AUDIT_ONLY = [1, 2, 8, 9, 11, 17, 18, 19, 21, 24, 25, 28, 30, 31, 32, 33, 34, 36, 37, 39, 40, 42, 43, 44, 45]
- F0172#003: ORIGINAL_ONLY = []؛ AUDIT_ONLY = [1, 3, 11, 13, 15, 16, 19, 20, 24, 25, 27, 28, 29, 30, 31, 33, 34, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 54, 60]

## C2 — الاتفاق على النوع / المتحدّث / الثقة / وجود الأرقام

| المقطع | الأزواج | نوع متّفق | متحدّث متّفق | ثقة متّفق | وجود رقم متّفق |
|---|---|---|---|---|---|
| F0170#001 | 23 | 8 (34.8%) | 23 (100.0%) | 21 (91.3%) | 23 (100.0%) |
| F0170#003 | 36 | 15 (41.7%) | 36 (100.0%) | 29 (80.6%) | 36 (100.0%) |
| F0171#002 | 9 | 2 (22.2%) | 9 (100.0%) | 4 (44.4%) | 7 (77.8%) |
| F0172#002 | 22 | 10 (45.5%) | 22 (100.0%) | 18 (81.8%) | 22 (100.0%) |
| F0172#003 | 25 | 10 (40.0%) | 25 (100.0%) | 20 (80.0%) | 25 (100.0%) |
| **المجموع** | **115** | **45 (39.1%)** | **115 (100.0%)** | **92 (80.0%)** | **113 (98.3%)** |

جدول خلط الأنواع (نوع الأصلي ← نوع الفحص) على كل الأزواج المطابقة:

| الأصلي \ الفحص | ACTION_STEP | CONDITIONAL_RULE | CONFIRMER | CORRECTION_OF_EARLIER_STATEMENT | DEFINITION | DISCRETION_STATEMENT | PREREQUISITE | WARNING_OR_INVALIDATOR |
|---|---|---|---|---|---|---|---|---|
| ACTION_STEP | 0 | 0 | 0 | 0 | 12 | 4 | 0 | 0 |
| CONDITIONAL_RULE | 1 | 8 | 0 | 0 | 2 | 1 | 0 | 0 |
| CONFIRMER | 0 | 2 | 4 | 0 | 1 | 3 | 0 | 0 |
| CORRECTION_OF_EARLIER_STATEMENT | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| DEFINITION | 0 | 0 | 0 | 0 | 9 | 5 | 0 | 0 |
| DISCRETION_STATEMENT | 0 | 2 | 2 | 0 | 1 | 7 | 0 | 0 |
| PREREQUISITE | 1 | 1 | 0 | 0 | 2 | 2 | 2 | 0 |
| WARNING_OR_INVALIDATOR | 0 | 3 | 1 | 1 | 4 | 18 | 1 | 15 |

إجمالي الأزواج المختلطة النوع: 70 من 115 (60.9%).

## C3 — نوع المحتوى (content_type) لكل مقطع

| المقطع | الأصلي | الفحص | متّفق؟ |
|---|---|---|---|
| F0170#001 | TEACHING_CONCEPT | TEACHING_CONCEPT | نعم |
| F0170#003 | TEACHING_CONCEPT | TEACHING_CONCEPT | نعم |
| F0171#002 | TEACHING_CONCEPT | REVIEW_EXAMPLE | لا |
| F0172#002 | TEACHING_CONCEPT | TEACHING_CONCEPT | نعم |
| F0172#003 | TEACHING_CONCEPT | TEACHING_CONCEPT | نعم |

## C4 — الكلمات الغامضة (vague_words): التداخل وتسمية الميزة

| المقطع | عدد (أصلي) | عدد (فحص) | تداخل الكلمة | تسمية ميزة متّفق على المتداخل |
|---|---|---|---|---|
| F0170#001 | 21 | 5 | 1 | 1 من 1 (100.0%) |
| F0170#003 | 14 | 5 | 1 | 1 من 1 (100.0%) |
| F0171#002 | 2 | 2 | 0 | 0 من 0 (n/a) |
| F0172#002 | 10 | 5 | 0 | 0 من 0 (n/a) |
| F0172#003 | 10 | 5 | 1 | 0 من 1 (0.0%) |

- F0170#001: «a lot»: NONE / NONE (متفق)
- F0170#003: «a lot»: NONE / NONE (متفق)
- F0172#003: «very specific»: the listed PD arrays / NONE (متباين)

## C5 — الفتحات المفتوحة (open_slots): الأعداد والتداخل

| المقطع | عدد (أصلي) | عدد (فحص) | أزواج متداخلة (٢+ كلمة محتوى مشتركة) |
|---|---|---|---|
| F0170#001 | 5 | 5 | 0 |
| F0170#003 | 4 | 6 | 0 |
| F0171#002 | 3 | 4 | 0 |
| F0172#002 | 4 | 5 | 1 |
| F0172#003 | 5 | 5 | 0 |

- F0172#002: سؤال أصلي #0 ↔ سؤال فحص #0 (مشترك: code, draw)

## C6 — المصطلحات (terms): التداخل

| المقطع | معرف: متداخل / أصلي-فقط / فحص-فقط | مستخدم-غير-معرّف: متداخل / أصلي-فقط / فحص-فقط |
|---|---|---|
| F0170#001 | 1 / 1 / 3 | 0 / 5 / 3 |
| F0170#003 | 0 / 1 / 2 | 0 / 4 / 4 |
| F0171#002 | 0 / 1 / 3 | 1 / 2 / 3 |
| F0172#002 | 0 / 2 / 2 | 1 / 2 / 4 |
| F0172#003 | 1 / 2 / 3 | 2 / 4 / 6 |

- F0170#001 مصطلحات معرّفة متداخلة: demo baller
- F0170#001 معرّفة أصلية فقط: the three stages
- F0170#001 معرّفة فحص فقط: analysis paralysis, green horns, yearners
- F0170#001 غير معرّفة أصلية فقط: green horns, index features, the model, the process, three stages
- F0170#001 غير معرّفة فحص فقط: 4x, bias, earners
- F0170#003 معرّفة أصلية فقط: over trade over leverage
- F0170#003 معرّفة فحص فقط: quote unquote profitable demo trading stage, replay
- F0170#003 غير معرّفة أصلية فقط: lipstick, mountain decline, paper trading stage, replay button
- F0170#003 غير معرّفة فحص فقط: drawdown, introducing broker, over leverage, over trade
- F0171#002 معرّفة أصلية فقط: standard projections on fibonacci
- F0171#002 معرّفة فحص فقط: london open kill zone, new york open kill zone, the kill zone
- F0171#002 غير معرّفة متداخلة: fit
- F0171#002 غير معرّفة أصلية فقط: loaded they, slow roll out
- F0171#002 غير معرّفة فحص فقط: 4x, fibonacci, standard deviation
- F0172#002 معرّفة أصلية فقط: draw on liquidity focus, institutional order flow his denial
- F0172#002 معرّفة فحص فقط: quote unquote institutions, spoofing
- F0172#002 غير معرّفة متداخلة: draw on the code
- F0172#002 غير معرّفة أصلية فقط: spoofed, time based chart
- F0172#002 غير معرّفة فحص فقط: depth of market dom, draw on liquidity, footprint, trolls
- F0172#003 مصطلحات معرّفة متداخلة: pd array
- F0172#003 معرّفة أصلية فقط: draw on liquidity, footprint his definition
- F0172#003 معرّفة فحص فقط: footprint, institutional order flow, middleman
- F0172#003 غير معرّفة متداخلة: institutional overflow entry drill, sibi
- F0172#003 غير معرّفة أصلية فقط: consequent quotient, institutional order flow, middleman ideas, pd array
- F0172#003 غير معرّفة فحص فقط: consequent quotient of a wick, cosigned, disconsolidating, level two, open outcry, reprice
