# خريطة التكرار — K7 المرحلة صفر

## الطريقة، وقد أُعلنت قبل النظر إلى النتائج

- تجزئة النص: مقاطع (shingles) من 8 كلمات متتابعة على النص المُطبَّع بـ N-05.
- لكل ملف مجموعة shingles، وبصمة كل shingle رقم 64-bit حتمي (كثيرة الحدود على CRC32 للكلمة).
- التطابق التام: تساوي SHA-256 للنص الموصول.
- التشابه: Jaccard = التقاطع ÷ الاتحاد، محسوباً بالضبط على المجموعتين لا تقديراً.
- العتبتان المعلنتان قبل التشغيل: NEAR 0.60، وSTRONG 0.85. القرار: STRONG يعني قراءة الأول كاملاً وفحص
  فروق الثاني؛ وما بين 0.60 و0.85 يعني قراءة الاثنين كاملاً، لأن إعادة التسجيل قد تحمل شرطاً جديداً.
- كل زوج بين 0.25 و0.60 يُذكر صراحة تحت العتبة، حتى لا يُخفي أي شيء.
- التجزئة إلى أجزاء: نفس المجلد ونفس العنوان بعد حذف لاحقة `-NNN`من اسم الملف.

## الحصيلة: 7 تام / 0 قريب / 72 درساً متعدد الأجزاء / 2 عنوان متطابق عبر سلاسل

### التطابق التام

| الملف المقروء كاملاً | الملف المفحوص فرقاً | المسار A | المسار B |
|---|---|---|---|
| `F0171` | `F0214` | `ICT-Forex-Review-January-09-2023-001.json` | `ICT-Forex-Review-January-09-2023-001.json` |
| `F0172` | `F0227` | `2023-ICT-Mentorship-Deep-Dive-Into-Institutional-Order-Flow-001.json` | `ICT-Mentorship-2023-Deep-Dive-Into-Institutional-Order-Flow-001.json` |
| `F0173` | `F0228` | `2023-ICT-Mentorship-Deep-Dive-Into-Institutional-Order-Flow-002.json` | `ICT-Mentorship-2023-Deep-Dive-Into-Institutional-Order-Flow-002.json` |
| `F0179` | `F0180` | `AM-Session-Opening-Range-Gap-+-Mitigation-Block-&-FVG-Entry-001.json` | `AM-Session-Opening-Range-Gap-Mitigation-Block-&-FVG-Entry-001.json` |
| `F0187` | `F0464` | `December-2023-Non-Farm-Payroll-Live-Execution-&-Explanations-001.json` | `December-2023-Non-Farm-Payroll-Live-Execution-&-Explanations-001.json` |
| `F0188` | `F0465` | `December-2023-Non-Farm-Payroll-Live-Execution-&-Explanations-002.json` | `December-2023-Non-Farm-Payroll-Live-Execution-&-Explanations-002.json` |
| `F0484` | `F0485` | `Real-Money-Real-People-ICT-Student-Meeran-001.json` | `Real-Money-Real-People-ICT-Student-Mereen-001.json` |

كلها تكرارات صادقة: نفس المقطع منشور في مجلدين، أو نفس الملف باسم فيه خطأ إملائي في اسم الطالب.
لا يُحذف ولا يُخفى أي ملف: الثاني يبقى في الخريطة ويُفحص فرقاً فقط.

### تحت العتبة

- `F0366` مقابل `F0428` — Jaccard = 0.4657
  (Essentials-To-ICT-Market-Structure-001.json ↔ ICT-W-E-N-T-Series-Part-3-of-5-001.json)
  هذا تشابه عالٍ يُذكر للأمانة، لكنه **دون** العتبة المعلنة، فلا يُصنَّف مكرراً، ويُقرأ الملفان كاملين.

### الدروس متعددة الأجزاء: 72 مجموعة

الأجزاء تكملة لا تكرار. كل جزء يُقرأ كاملاً. عدد المجموعات التي فيها فراغ في ترقيم الأجزاء: 0.

### عنوان متطابق في سلسلتين

- `December-2023-Non-Farm-Payroll-Live-Execution-&-Explanations` — `2023-ICT-Mentorship`, `ICT-Trade-Executions` — ملفات: F0187, F0188, F0464, F0465
- `ICT-Forex-Review-January-09-2023` — `2023-Forex-Reviews`, `2023-ICT-Mentorship` — ملفات: F0171, F0214

تطابق العنوان **ليس** ادعاء تشابه نصي؛ الاثنان يُقرآن كاملين، والمقارنة تُسجَّل في المرحلة الثانية.

## ما لا يقوله هذا الملف

لا يقول إن ملفاً عديم القيمة، ولا يحذف شيئاً، ولا يدمج درسين. كل قرار هنا هو قرار قراءة فقط.
