# قرار المالك `D2` — نسخ الإزاحة (نصًّا، بلا شيفرة)

**الحالة:** `OWNER_APPROVED` — نقل حرفي لقرار المالك، لا اجتهاد بناء.

**المصدر الأول (مقروء من الشجرة، لا منسوخ منه شيفرة):**
الالتزام `d9b38311a94064f80a13b134b23d56365f7193ee` — `docs(owner): record D2 displacement decision and open B1 questions`،
الملف `engine_v1/OWNER_DECISIONS.md`، القسم `## D2 — Displacement variants`.
قُرئ بالأمر `git show d9b3831 -- project/trading_project/docs/research/huddleston_study/engine_v1/OWNER_DECISIONS.md`.
**لم يُدخل الالتزام إلى هذه الشجرة، ولم يُنسخ منه أي كود.** الملف `OWNER_DECISIONS.md` في هذه الشجرة لم يُعدَّل.

**المصدر الثاني (بيان المالك في المحادثة):** `OWNER_STATEMENT_IN_CHAT` — نصّه في §2 أدناه.

`STATUS = FETCHED_FROM_D9B3831` (النص الكامل متاح؛ لا حاجة إلى `OWNER_STATEMENT_IN_CHAT` وحده).

---

## 1. نص `D2` المنقول حرفيًا من `d9b3831`

> ## D2 — Displacement variants
>
> **Status: OWNER_APPROVED**
>
> There is **no reference definition of displacement**. Record the following three families as separate named variants. Measure every sub-version separately; never select one because of its results and never attribute any variant to a person. These are recorded alternatives, not a default or an endorsement of a winning threshold.
>
> - **V-D-A — body divided by candle range:**
>   - **V-D-A-1:** 60–80 percent, as printed by the source.
>   - **V-D-A-2:** about 75 percent, as printed by the source.
>   - **V-D-A-3:** 70 percent, as printed by the source.
>   - **V-D-A-4:** 80 percent, as printed by the source.
> - **V-D-B — candle compared with previous candles:**
>   - **V-D-B-1:** candle range at least 2× the average range of 3–5 previous candles.
>   - **V-D-B-2:** candle body 2–3× the average body of the previous 10 candles.
> - **V-D-C — body compared with ATR:**
>   - **V-D-C-1:** candle body at least 1.5 × ATR(14). The source itself says the multiple is a choice to test.
>
> A number supplied by the owner later would be an **additional named variant**, not a replacement chosen by results. **Displacement is not coded yet.**

## 2. بيان المالك في المحادثة (`OWNER_STATEMENT_IN_CHAT`)

> displacement has NO reference variant; three named families, none chosen by results:
> V-D-A (body/range family: 60%, 60-80%, ~75%, 70%, 80% sub-versions),
> V-D-B (range >= 2x average of previous 3-5 candles; body 2-3x average body of previous 10),
> V-D-C (body >= 1.5 x ATR(14), as stated in l_open_questions.md records Q1-01, Q1-02, Q1-13);
> an owner-supplied number is an extra variant.

## 3. الفروق بين النصين — بلا ترجيح

| # | الموضوع | بيان المحادثة | نص `d9b3831` | الحكم |
|---|---|---|---|---|
| D2-DIFF-1 | عدد النسخ الفرعية لعائلة `V-D-A` | خمس: `60%`, `60-80%`, `~75%`, `70%`, `80%` | أربع: `V-D-A-1` = 60–80%، `V-D-A-2` = ~75%، `V-D-A-3` = 70%، `V-D-A-4` = 80% | **فرق.** لا نسخة فرعية مستقلة بـ`60%` وحدها في النص المقروء؛ الـ`60%` هو الحد الأدنى داخل `V-D-A-1` |
| D2-DIFF-2 | عائلة `V-D-B` | `range >= 2x` على `3-5` سابقات؛ جسم `2-3x` متوسط جسم `10` | `V-D-B-1` و`V-D-B-2` بالمعنى نفسه، وكلاهما «as printed by the source» ضمنيًا | **تطابق** |
| D2-DIFF-3 | سند عائلة `V-D-C` | «as stated in `l_open_questions.md` records `Q1-01`, `Q1-02`, `Q1-13`» | `V-D-C-1` بلا إحالة إلى سجلات؛ ويضيف «The source itself says the multiple is a choice to test» | **فرق في الإحالة.** مراجعة السجلات: `Q1-01` و`Q1-02` يصرّحان `1.5 × ATR(14)`؛ أما `Q1-13` فسجله `NO_NUMBER` («What qualifies is judged by eye, not by a formula») — فلا يسند الرقم. عدد الناشرين الذين يصرّحون بالرقم = **2** لا 3 |
| D2-DIFF-4 | لا نسخة مرجعية | «has NO reference variant» | «There is **no reference definition of displacement**» | **تطابق في المعنى** |
| D2-DIFF-5 | عدم الاختيار بالنتائج | «none chosen by results» | «never select one because of its results» | **تطابق** |
| D2-DIFF-6 | رقم يقدّمه المالك لاحقًا | «an owner-supplied number is an extra variant» | «an **additional named variant**, not a replacement chosen by results» | **تطابق**، والنص المقروء أوسع (يمنع الاستبدال) |
| D2-DIFF-7 | زوائد في النص المقروء | — | «never attribute any variant to a person»، «These are recorded alternatives, not a default or an endorsement of a winning threshold»، «**Displacement is not coded yet.**»، ووسم `Status: OWNER_APPROVED` | **زيادة** لا تعارض؛ تُلتزم |

**خلاصة لا ترجيح فيها:** يلتزم `C1b` بالنص المقروء من `d9b3831` عند التعارض الشكلي (عدد النسخ الفرعية لعائلة `V-D-A`، وسند `Q1-13`)، ويُسجَّل بيان المحادثة كما هو. ولا يُضاف أي رقم لم يصرّح به مصدر.

## 4. ما ينفّذه `C1b` من `D2` وما لا ينفّذه

| البند | الحالة في `C1b` |
|---|---|
| حذف النسخة المرجعية للإزاحة | **منفّذ**: `reference_variant = NONE_PER_OWNER_D2` في كل نتيجة |
| `V-D-C-1` = جسم ≥ `1.5 × ATR(14)` | **مسجّل كنسخة `V-D-C`**؛ لكن حساب `ATR` نفسه **غير معرّف في المصادر** ← `UNDEFINED` مع `KNOWLEDGE_GAP: ATR formula` (انظر `BUILD_STEP_C1b_SPEC.md` §2) |
| `V-D-A-3` (70%) و`V-D-A-4` (80%) | **غير منفّذتين في `C1b`**: لا تصحيح في `C1b` يطلب إضافتهما، وإضافتهما بُعد جديد لا تصحيح |
| `V-D-A-1` و`V-D-A-2` و`V-D-B-1` و`V-D-B-2` | موجودة بأسماء `C1` (`V-D-01`، وداخل `V-D-02`، `V-D-03`)؛ جدول الربط في §3 من مواصفة `C1b` |
| رقم يقدّمه المالك لاحقًا | لا يوجد رقم من المالك؛ ولا يُخترع |
