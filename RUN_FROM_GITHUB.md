# شغّل المشروع من GitHub فوراً — RUN FROM GITHUB

> **الحالة (2026-11-23):** الريبو **مكتمل وذاتي** — كل الكود وكل البيانات وكل
> التقارير مرفوعين. ما في أي خطوة تحميل أو بناء قبل التشغيل.

---

## 1. ثلاثة أسطر فقط

```bash
git clone https://github.com/jfjdjdieifne/TRADING-BOT.git
cd TRADING-BOT/halal_spot
pip install -r requirements.txt        # numpy + pandas (بس)
python lab_v37_anti_fragile.py run B0 --window W1
```

**النتيجة المتوقّعة بالقرشة (هذا هو اختبار الهوية — identity gate):**

```
n=181 end=$158.024 PF=1.706 DD=-14.064% mo+=5/6
```

إذا طلع نفس الرقم، كل شي سليم. إذا طلع غيره، في خلل بالبيئة — لا تكمل.

---

## 2. شنو موجود وشو مصدره

| المسار | شنو فيه | الحجم |
|---|---|---|
| `halal_spot/strategy_v36_ict_champion.py` | **المحرّك الشامبيون** + كل مفاتيح v37 (كلها OFF) | 236 KB |
| `halal_spot/strategy_v19..v35*.py` | كل النسخ التاريخية محفوظة | ~2 MB |
| `halal_spot/lab_v37_anti_fragile.py` | مختبر الأذرع الـ12 (مع مفتاح `--slip`) | — |
| `halal_spot/audit_v37_root_causes.py` | التشريح الجنائي (`tape\|engine\|regime\|q2\|q1y`) | — |
| `halal_spot/data/binance_5m/` | **8 عملات × 47 شهر**، 5 دقائق، START-labelled | **51 MB / 376 ملف** |
| `halal_spot/results/` | 835 ملف: التقارير + كل tapes الصفقات + الـequity | 1.5 GB |
| `project/…/huddleston_study/` | مكتبة البحث (184 ملف) | 57 MB |

**البيانات مرفوعة بقرار مالك صريح** (2026-11-23) — قبلها كان الريبو يحوي 1.7GB
من منحنيات الـequity لكن **مو** الـ51MB من الأسعار اللي المحرّك يحتاجها، فكل
كلون نظيف كان يكراش على أول سطر. الآن يشتغل مباشرة.

---

## 3. نوافذ الاختبار

| النافذة | الفترة | الدالة |
|---|---|---|
| `W1` | 2023-10..2024-03 | نافذة الهوية |
| `W2` | 2024-05..2024-10 | نافذة الصعود القوي |
| `OLD7` | 2023-01..2023-07 | سوق هابط/عرضي |
| `FULL15` | 2023-08..2024-10 | 15 شهر |
| `APR_MAY_24` | 2024-04..2024-05 | الانهيار |
| `MOD_Y1` | 2024-11..2025-10 | صعود توسّعي |
| `MOD_Y2` | 2025-11..2026-10 | **آخر نظام حقيقي** — 8/8 عملات هابطة |
| `MODERN_24M` | 2024-11..2026-10 | 24 شهر متصلة |

---

## 4. أوامر المختبر

```bash
cd halal_spot

python lab_v37_anti_fragile.py arms                    # اطبع كل الأذرع
python lab_v37_anti_fragile.py run B0 --window W1      # ذراع واحد
python lab_v37_anti_fragile.py run RATCHET_2R --window MOD_Y2
python lab_v37_anti_fragile.py run B0 --window W1 --slip 2   # انزلاق 2bps
python lab_v37_anti_fragile.py matrix                  # المصفوفة كاملة
python lab_v37_anti_fragile.py report                  # جدول النتائج
```

**الأذرع:** `B0` (المرجع) · `RATCHET_2R` · `RATCHET_3R` · `RATCHET_3RT` ·
`RATCHET_LAD_A` · `RATCHET_LAD_B` · `GATE_4H` · `GATE_1H` · `GATE_BOTH` ·
`CD_1H` · `FIXBE`

---

## 5. أهم ملفين لازم تقرأهم

1. **`halal_spot/results/REPORT_AR_v37.md`** — التقرير الكامل بالعربي (13 قسم).
2. **`halal_spot/HANDOFF_V37.md`** — ملخّص تسليم للموديل الجاي.

### الحكم بجملة واحدة
**ما في ولا مفتاح من v37 بشحن.** المحرّك بقي شامبيون v36، وكل المفاتيح OFF.
`RATCHET_2R` هو المرشّح الوحيد الجاد — ويُعرض على المالك كـ**ملف مخاطرة**،
مش كتحسين (يرفع الأشهر الرابحة 25/46 ⟶ 28/46 ويخفض أسوأ تراجع إلى −15.80%،
بس يخسر 155.69$ على المدى الطويل).

---

## 6. تحذيرات

- **لا تحكم بـ `totR` أبداً.** الحكم بـ`net_$` و`maxDD_pct` وPF وعدد الأشهر الرابحة.
- **`CAPITAL` الافتراضي في المحرّك 200 مش 100.** المختبر يضبطه على 100 صراحةً.
  أي تشغيل يدوي لازم يضبط `CAPITAL=100.0`.
- **بيانات v36 المبنية كانت END-labelled** وبيانات v37 START-labelled. لا تقارن
  أرقام v36 القديمة بأرقام v37. للإعادة كـv36: `_build_v37_data.py --end-label`.
- كل شيء يعمل **بعملية واحدة متتالية** — لا multiprocessing.
