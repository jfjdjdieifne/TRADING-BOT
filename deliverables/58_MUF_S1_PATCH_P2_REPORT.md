# 58 — MUF_S1_PATCH_P2_REPORT

**الحالة: `PATCHED — PENDING RE-AUDIT`**
(إحدى الحالتين المسموحتين فقط — لا إغلاق · لا S2)

- **التاريخ**: 2026-10-01 · **المُرسِل**: P2 Builder (ترقيع فقط)
- **النطاق**: PATCH P2 ONLY — MEMBERSHIP EARLIEST-LAWFUL AVAILABILITY
- **المرجعية**: S1 P1 = `PATCHED — PENDING RE-AUDIT` · P1 Re-Audit = `PATCH REQUIRED` (blocker واحد)
- **الـblocker**: `EpisodeMembershipEvent` كان يقبل `membership_information_key` مؤجَّلاً (T+k) رغم أن أساس العضوية الوحيد المعروف في S1 (`member_fact_availability_key`) كان متاحاً عند T.

---

## 1) قاعدة التوقيت المفروضة (exact timing rule)

> **`membership_information_key` MUST EQUAL `member_fact_availability_key`** — تحت عقد المساواة القانون لـ`InformationKey` — وهو **أبكر مفتاح قانوني** تحت أساس العضوية الوحيد الذي يعرفه S1.

- S1 = SCHEMAS ONLY ولا يملك ولا يخترع قاعدة عضوية تؤجّل العضوية عن إتاحة العضو نفسه.
- **لم يُخترع**: `membership_rule_version` · satisfaction keys · تأجيل T+k · policy semantics · future evidence.
- مرحلة لاحقة بقاعدة عضوية مصرَّح بها حقيقية قد تستخدم S0 `AvailabilityRule`/`determine_fact_information_key` تحت **عقد منفصل** — S1 V1 لا يتظاهر بوجود هذه القاعدة.
- الآلية التنفيذية: `require_visible_at` (عقد S0) أولاً ثم `_require_earliest_lawful_membership_key` (المساواة الصارمة). الترتيب يضمن سلوك A–E حرفياً:

| الحالة | السلوك | الخطأ (عقد S0) |
|---|---|---|
| **A)** T → T | **قَبول** | — |
| **B)** T → T+k | **رفض** machine-distinguishable | **`NonEarliestAvailability`** + توكن `NON_EARLIEST_AVAILABILITY` (سطر ثابت في `path_schemas.py` + في رسالة الخطأ) |
| **C)** T → T−k | رفض premature | `IllegalCausalReference` (require_visible_at) |
| **D)** cross-timeline | رفض | `IllegalCausalReference` (require_visible_at) |
| **E)** incomparable | fail closed | `IncomparableInformationKeys` (require_visible_at يغلق `InformationKeyError`) |
| **F)** نفس العضو/الحلقة/المفتاح القانوني | هوية حدث **حتمية متطابقة** | `event_identity` canonical ثابت |
| **G)** عضو لاحق T2 | حدث مستقل · `episode_id` ثابت | الهوية من الحقول الدلالية المتقبَّلة فقط |

**الهوية**: لم تتغير — `event_identity` = canonical على (`episode_id`, `member_fact_ref`, `membership_information_key`) · بلا proof noise · هوية `CausalEpisodeRecord` لم تُمس · لا حقل عضوية يدخل هوية الحلقة · لا تعديل تاريخي.

## 2) الملفات المتغيَّرة (2 فقط) + البصمات

| الملف | SHA256 بعد الترقيع | الحالة |
|---|---|---|
| `src/trading_system/market_understanding/path_schemas.py` | `707a1b7ba17b1bf370317c2634aa4c6a6c8b8cd6f1d1b21e8c29efa69e8b6aa6` | مسموح — مُرقَّع |
| `tests/test_muf_s1_path_schemas.py` | `f9908b04feff7ce0527085d640a9bd7f5198fc032558d5cbaf5d21a957b3387c` | مسموح — مُرقَّع |
| `src/trading_system/market_understanding/price_path.py` | `2ab56ad35c4a68e89ee6134b3d20f8968b0aad872abade49d121dd99d025f990` | **FROZEN — مطابق للأمر — لم يُمس** |
| `tests/test_muf_s1_price_path.py` | `836240cf552ff0fdf7c447b983335281bcca166e740273f32de7462f661b3259` | **FROZEN — مطابق للأمر — لم يُمس** |

ملاحظة شفافة: fixtures اختبارات P1 القديمة (03/04/11) كانت تستخدم مفاتيح T+k صارت مخالفة للعقد المصحَّح؛ حُدِّثت إلى مفاتيح قانونية (`membership_key == member_fact_key`) — **ال assertions نفسها لم تتغير** (استقرار `episode_id` · استقلال الهوية · العدمية).

## 3) نتيجة الـauditor fixture (حرفياً)

**same timeline · `member_fact bar_position=5` · `membership bar_position=10`**:
→ **مرفوض** بـ`NonEarliestAvailability` ورسالة تحوي التوكن `NON_EARLIEST_AVAILABILITY` — (الاختبار `test_muf_s1_patch_p2_02_delayed_membership_rejected_non_earliest`) ✓.

## 4) الاختبارات الإلزامية 1–8

| # | الاختبار | النتيجة |
|---|---|---|
| 1 | T → T مقبول | **PASS** |
| 2 | T → T+k (fixture المدقق: 5→10) مرفوض `NON_EARLIEST_AVAILABILITY` | **PASS** |
| 3 | T → T−k مرفوض (premature/illegal causal) | **PASS** |
| 4 | cross-timeline مرفوض | **PASS** |
| 5 | incomparable timestamp provenance → fail closed | **PASS** |
| 6 | عضو A@T1 + عضو B@T2: نفس `episode_id` · هويتا حدث مختلفتان (+ إعادة البناء = نفس الهوية) | **PASS** |
| 7 | عضو مستقبلي لا يغيّر hash/content الحلقة | **PASS** |
| 8 | mutation proof: إزالة الإلزام (revert إلى require_visible_at-only) ⇒ الاختبار #2 يسقط | **PASS** (أدناه) |

- اختبارات S1 المخصصة: **89/89** (81 سابقة سليمة — بعد تحديث الـfixtures — + 8 جديدة).

## 5) إثبات الطفرة (8) — فعلي

**(أ) داخل الملف** (`test_muf_s1_patch_p2_08_mutation_proof_revert_to_visibility_only`): baseline يرفض fixture المدقق؛ مع `monkeypatch` يُستبدل `_require_earliest_lawful_membership_key` بدالة فارغة (العودة إلى `require_visible_at`-only) يُقبل T+k ⇒ الاختبار #2 سيسقط — مثبت حتمياً في الاتجاهين.

**(ب) على نسخة معزولة** `/tmp/s1_patch_p2_mut`: حُذف استدعاء الإلزام حرفيًا من `path_schemas.py` (العودة إلى `require_visible_at`-only) ثم شُغّل الملف:
```
FAILED tests/test_muf_s1_path_schemas.py::test_muf_s1_patch_p2_02_delayed_membership_rejected_non_earliest
```
⇒ **الاختبار #2 يسقط تحت الطفرة** ✓ (وكذلك الاختبار 08 الذي يثبّت خط الأساس).

## 6) العدّادات الفعلية

| البوابة | النتيجة |
|---|---|
| S1 المخصصة (الملفان) | **89/89** |
| S0 (`test_muf_s0_*`) | **67/67** |
| المجموعة الكاملة `tests/` | **1228/1228** (= 1139 baseline + 89) |
| `field_runner/runner_tests` | **36/36** |
| ماسحات `path_schemas.py` (private/prohibited/market_shape) | **0/0/0** |
| أرقام إنتاجية داخل defs | **{0,1} فقط** |
| MANIFEST | **196/196** مدخلاً قائماً OK · `899febb4a33c984b48176be6a972405fe6be3301faf660d54d53718216090e84` — لم يُمس · ملفات S1 unmanifested |

## 7) إثبات NON-TOUCH (قبل/بعد بالSHA — project كاملاً + field_runner)

- المتغيَّر: **الملفان المسموحان فقط** (البند 2).
- المحذوف: **0** · المضاف: **0**.
- الملفان المجمّدان: بصماتهما = بصمات أمر المالك بالضبط (`2ab56ad3…` / `836240cf…`) — أُعيد التحقق بعد الترقيع.
- بلا MANIFEST/docs/S0/S2/field_runner.

## 8) الالتزامات

- كل سلوك S1 الآخر **FROZEN** (لا redesign · لا S2 · لا MANIFEST · لا docs).
- لا إغلاق · إعادة التدقيق READ ONLY في شات منفصل · `PATCHED — PENDING RE-AUDIT`.
- الـcommit + push على `TRADING-BOT` (خاص) مع هذا التقرير.

**STOP — PATCH P2 COMPLETE — PENDING RE-AUDIT.**
