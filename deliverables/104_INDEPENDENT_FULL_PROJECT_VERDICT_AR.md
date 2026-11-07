# ١٠٤ — تقييم مستقل كامل للمشروع (بالأدلة المُشغَّلة، لا بالقراءة فقط)

**التاريخ:** ٢٠٢٦-١١-٠٧
**الفرع المُقيَّم:** `arena/a2387edd-trading-bot` (مبني على `51ea54b` = `arena/345b2324-trading-bot`)
**الطريقة:** تشغيل فعلي للاختبارات، قراءة الكود المصدري، استخراج الأرقام من ملفات النتائج الحقيقية،
ومقارنة كل الفروع الأربعة عشر على الخادم البعيد. كل رقم أدناه قابل لإعادة الإنتاج بالأمر المرفق معه.

---

## الجزء صفر — تصحيحات واجبة لما قاله الوكيل الآخر

قبل أي تقييم، ثلاث معلومات في كلامه **غير صحيحة واقعياً**، وواحدة صحيحة تماماً.

### ٠.١ خطأ: «`run_btc_causal_recommendations.py` مشروع ثاني، مو `engine_v1`»

غير صحيح. السكربت في جذر المستودع نفسه، ويستورد من هذا المشروع مباشرة:

```python
# run_btc_causal_recommendations.py, lines 31-60
from field_runner.pipeline import FieldRunConfig, load_sources, run_engines, seal_timeline
from field_runner.runner_btc_may_2026 import detect_inputs, load_sidecar_json, obtain_klines
from trading_system.market_understanding.availability import InformationKey, InformationPhase
from trading_system.market_understanding.final_evaluation_and_reality import (
    CausalMarketUnderstandingDiagnosticReport, ExplanationStateRecord)
from trading_system.recommendation.causal_ict_lifecycle import (
    evaluate_causal_ict_recommendation_as_of, evaluate_open_trade_lifecycle_as_of, ...)
```

هذا **ليس مشروعاً آخر** — هذا هو واجهة التشغيل العليا (CLI) للمحرك نفسه.
النتيجة: أي تقييم لهذا السكربت **ينطبق** على المستودع، ولا يجوز فصله عنه.
`engine_v1` مجلد تقارير نتائج داخل `docs/research/huddleston_study/`، وليس مستودعاً منفصلاً.

### ٠.٢ خطأ أكبر: «الهيكل اللي بيشبه إنسان بيحلل» — مقترح كشيء يُبنى، وهو مبني أصلاً

البنود الخمسة التي اقترحها الوكيل الآخر **موجودة ومنفذة** في
`src/trading_system/research/contextual_selection/` — **١٢٬٢٩١ سطراً**:

| مقترَح الوكيل الآخر | الموجود فعلاً في المستودع | الحجم |
|---|---|---:|
| ١. حالة حيّة (مستويات/مناطق/سيولة + وضعها: ما انلمس، انسحب، احترم، انكسر) | `csm.py` — `StatusTransition` history + `status_at()` + `candidate_record()` | ٣٬١٢٩ سطر |
| ٢. فرضيات (صعود/هبوط/غير واضح + أدلة مؤيدة ومعارضة + ربط برقم claim) | `decision_layer.py` — تفسير عامل واحد + بدائل مرئية + `NO_EDGE` + «الحدث المميِّز التالي» | ٩٥٧ سطر |
| ٣. مرحلة الخطة (لا فكرة / منتظر X / داخل صفقة / بطلت) | `trade_plan.py` — `MONITORING` / `CONDITION_OBSERVED` / `HYPOTHETICAL_ENTRY_MET` / `INVALIDATED` / `MISSED` | ٨٥٥ سطر |
| ٤. تحديث (إعادة حساب المتأثر + «البيانات غير كافية») | `monitoring.py` (`ReplayObservationStream`) + `analysis_lifecycle.py` | ٩٥٧ + ١٬٤٧٤ سطر |
| ٥. أي معلومة ناقصة = «معرفة ناقصة» بلا تخمين | `UNAVAILABLE` + `UNRESOLVED` + `NOT_ESTABLISHED` + سبب صريح في كل مكان | — |

اقتراح بناء ما هو مبني يعني أن الوكيل الآخر **لم يقرأ هذا الجزء من المستودع**.
الفجوة الحقيقية ليست «نبني فهماً» — الفجوة هي أن **جودة ما بُني لم تُقَس قط**
(`selection_quality = NOT_ESTABLISHED` في ٦٠ من ٦٠ سجل قرار).

### ٠.٣ خطأ: «هل بنفترض وجود تأكيد من الفريم الأعلى بدل ما نحسبه؟»

لا. `ict_engine/htf.py` **يحسب** التجميع اليومي/الأسبوعي/الشهري من شموع المصدر نفسها،
بمرساة تقويم صريحة (UTC أو نيويورك)، ويفصل الشمعة المكتملة عن المتشكلة:

```python
class HTFState:
    available_at: datetime
    newly_completed: tuple[AggregatedCandle, ...]
    last_completed: AggregatedCandle | None
    forming: AggregatedCandle | None      # ← المتشكلة معزولة، لا تُستهلك كمكتملة
```

كذلك «الأرقام السحرية» **ممنوعة آلياً** في طبقة الأساس السببي (انظر ٤.٢).

### ٠.٤ صحيح ودقيق: أرقام K4

تحققتُ منها من المصدر مباشرة، وكلها مطابقة:

```
k4a/verification.json:  quote_passed 95 / quote_total 95
                        windows: requested 94, opened 64 (68.1%)
k4b/README.md:          ٧١ من ٧١ اقتباساً، ٢٦ ادعاء، ٩ بدائل، ٣ تقديرية، ٢ غير موجودة
                        ٥ آثار صفقات من ٥ ملفات، اثنان على زوجي عملات،
                        وأثر اليورو مراجعة رسم لا دخول شخصي
```

**لكنه فاته الأهم:** العجز في K4a **منتظم تماماً — ٣ نوافذ بالضبط في كل سؤال من العشرة**:

```
per-question shortfall: Q01:3  Q02:3  Q03:3  Q04:3  Q05:3  Q06:3  Q07:3  Q08:3  Q09:3  Q10:3
```

هذا **ليس قيد بحثي ولا عينة** — هذا اقتطاع آلي بسقف ثابت، غير موثَّق في التقرير.
الفرق كبير: «قرأتُ عينة» مسألة منهجية، أما «سقف ميكانيكي مقطوع بلا ذكر» فمسألة إفصاح.

---

## الجزء الأول — ما شغّلته فعلاً (أدلة صلبة، لا انطباعات)

### ١.١ الاختبارات

```bash
# البيئة المثبّتة في ict_engine/requirements.txt
numpy==1.26.4  pandas==2.3.3  pytest==9.2.0
```

| المجموعة | العدد | النتيجة |
|---|---:|---|
| `project/trading_project/tests/` | **١٬٨٤١** | ✅ **كلها تنجح** (exit=0، صفر FAILED) |
| `src/trading_system/ict_engine/tests/` | **١١٦** | ✅ كلها تنجح |
| `field_runner/runner_tests/` | **٣٦** | ⚠️ **٣٥ تنجح، ١ تفشل** |

كثافة Assertions: **٤٬٩٠٩** جملة `assert` في مجلد الاختبارات وحده.
هذه ليست اختبارات دخان (smoke tests) — قرأت عينات منها، وهي اختبارات خصومية
(adversarial) حقيقية: `test_attack18_typed_states_never_collapse`،
`test_attack23_prohibited_implementations_guard`، `test_attack24_no_hidden_market_thresholds`.

### ١.٢ الاختبار الفاشل — وهو أخطر مما يبدو

```
FAILED field_runner/runner_tests/test_runner_guards.py::test_closed_project_manifest_untouched

>       assert _sha256_file(manifest_path) == closed_manifest_sha256
E       AssertionError: assert '70e119f7666e...52f0409159ed9' == '02592e5a9b76...57975a9da1471'
```

هذا **بوابة السلامة الذاتية للمشروع**. نصّها: «FAIL-CLOSED manifest gate pinning the
CLEAN POST-CLOSURE baseline ... If any of the ten files (or any other MANIFEST entry)
becomes stale again, this gate fails closed.»

يعني: المشروع ختم نفسه بـ «مُغلق وموثّق بالبصمة»، ثم استمر العمل وتغيّر `MANIFEST.sha256`،
**ولم يُعاد الختم، ولم يلاحظ أحد**. كل ادعاء «CLOSED / SEALED» في المستودع يستند الآن
إلى ختم لم يعد صالحاً. ليست كارثة برمجية — لكنها كارثة **انضباط**، وهي بالضبط النوع
الذي يبني المشروع كله سمعته على عدم الوقوع فيه.

### ١.٣ هشاشة البيئة

بنفس الكود، مع `numpy 2.4.6 / pandas 3.1.1` (غير مثبّتة):
**عشرات الاختبارات تفشل** (`test_research_eligibility` كلها، `test_research_manifest_identity`،
`test_trajectory_stage4c` كلها). مع التثبيت المُعلن: كلها تنجح.

لا يوجد CI، ولا `constraints.txt` على مستوى الجذر، ولا فحص إصدار عند الإقلاع.
المشروع يعمل **فقط** على تركيب محدد جداً وغير مُراقَب آلياً.

### ١.٤ هل يشتغل على بيانات حقيقية كما سُلم؟ لا.

```
$ python run_btc_causal_recommendations.py
MINUTE_FACTS_FILE_REQUIRED: place the minute-facts CSV (with its sidecar JSON) in
/home/user/TRADING-BOT/data or pass --minute-facts PATH --minute-facts-sidecar PATH.
Expected identity: sha256 a6a06c4c... (owner artifact) — the runner verifies it.
```

- `project/data/raw/` **فارغ** (فيه `README.txt` فقط).
- `field_runner/config/field_run_config.json`: `"swing_quantile": null`، `"sessions": []` → **NOT_CONFIGURED**.

الفشل **نظيف ومقصود** (fail-closed برسالة واضحة، لا انهيار) — وهذا يُحسب للمشروع.
لكن النتيجة العملية: **لا أحد يستطيع إعادة إنتاج أي نتيجة من المستودع كما هو مسلَّم**.
وهذا يقود مباشرة إلى ٣.٢.

---

## الجزء الثاني — جواب سؤال المال، بالأرقام

> «هل في أمل إنو يشتغل ويطلع توصيات تجيب مصاري؟»

### ٢.١ المشروع منع نفسه بنيوياً من حساب المال

كلمة `pnl` تظهر في **٨٢٬٢٠٠ سطر** من الكود المصدري **٧ مرات فقط — وكلها منع، لا حساب**:

| الموضع | النص |
|---|---|
| `decision/evidence_vector.py:21` | `_OUTCOME=re.compile(r"(^\|_)(future\|forward\|target\|stop_hit\|pnl\|profit\|trade_result\|mfe\|mae\|label\|y_true)...")` ← كاشف تسريب يرفض أي حقل اسمه pnl/profit |
| `trajectory/causal_market_context_core.py:6` | «recommendation, execution path, fill, **PnL**, or predictive claim» ← في قائمة ما لا يُدّعى |
| `market_movement_representation_research.py:1514` | «OHLC does not establish intrabar ordering, tick path, hidden liquidity, intent, fills, **PnL**, or outcomes» |
| `ict_engine/management.py:1` | «Parallel break-even doctrines; management states only, **never PnL scoring**» |
| `trajectory/movement_context_empirical.py:18` | «confidence interval, p-value, IID assertion, trading interpretation, or **PnL**» ← ممنوع |

وبحثتُ في كل الفروع عن `net profit` / `profit factor` / `win rate` / `sharpe` /
`drawdown` / `expectancy`: **صفر وثيقة نتائج** تذكرها (٣ وثائق تسليم مبكرة فقط).

**لا يوجد منحنى رأس مال، ولا عامل ربح، ولا أقصى تراجع، ولا شارب، في ٥٧ ميغابايت و١٬٢٩١ ملفاً.**
هذا قرار منهجي واعٍ، لا إهمال. وهو أصدق شيء في المشروع.

### ٢.٢ القياسان الحقيقيان الوحيدان الموجودان — وكلاهما سلبي أو صفري

#### (أ) `engine_v1` — فوركس ٥ دقائق، ٢٠٢٢، ٦ متغيرات، ٣٨٤٬١٨٢ صفاً مُسجَّلاً

من `M3_MONTHLY_REPORT.md` و`DIAGNOSIS_TBS.md` و`V2_DEV_REPORT.md` (موجودة **حصراً** على فرعك):

| التنبؤ / القرار | المحرك | الأساس | الفرق |
|---|---:|---:|---:|
| `candidate_first_retracement_continuation` (الهدف قبل الوقف) | **٠٫٠٠٪** (١ من ١٦٥) | ١٠٠٫٠٠٪ | **−١٠٠٫٠٠ نقطة** |
| `liquidity_pool_candidate` (بلوغ مستوى السيولة) | ٨٩٫٩٠٪ | ٨٩٫٩٠٪ | **+٠٫٠٠** |
| `order_block_candidate` (أول عودة لكتلة الأوامر) | ٩٣٫٤٥٪ | ٩٣٫٣٧٪ | **+٠٫٠٠** |
| `entry_choice` (اختيار الدخول) | ٨٤٫٤١٪ | ٩٣٫٩٢٪ | **−٨٫٢٩ نقطة** |
| `stop_choice` (اختيار الوقف) | ٨٤٫٤١٪ | ٩٣٫٩٢٪ | **−٨٫٢٩ نقطة** |
| `target_choice` (اختيار الهدف) | ٨٩٫٥٧٪ | ٨٩٫٩٣٪ | **−٠٫٣١ نقطة** |

**لا يوجد مقياس واحد فوق الأساس.** اثنان صفر حرفياً، وأربعة سلبية.

وهندسة الصفقة نفسها — من توزيع ١٦٥ حالة (`DIAGNOSIS_TBS.md`):

| المقياس | الوسيط | الأعلى |
|---|---:|---:|
| مسافة الوقف | **٣٫٩ نقطة** | ٢٨٫٢ |
| مسافة الهدف | **٤٣٥٫٦ نقطة** | ١٩٣٧٫٤ |
| نسبة الهدف إلى الوقف | **١٤٤٫٥٤ : ١** | **٩٦٦٣ : ١** |
| السبريد عند الدخول | ٠٫٤ نقطة | ٢٫٧ |

وقف ٣٫٩ نقطة وهدف ٤٣٥ نقطة ⇒ النتيجة محسومة هندسياً قبل أن يتحرك السوق:
**١٤٧ وقفاً أولاً، هدف واحد، ١٧ انتهاء أفق**. نسبة ١٤٤:١ ليست «ميزة عالية المخاطرة» —
هي مستوى لا يُبلغ عملياً أبداً. والسبب موثّق في `TARGET_SELECTION_REVIEW.md`:
قاعدة `DAILY_THEN_DISTANCE` تقدّم الإطار اليومي على المسافة، فـ **١٦٣ من ١٦٥ حالة**
كان الهدف فيها يومياً بينما أقرب مستوى على الخمس دقائق وسيطه **١١٫٥ نقطة** فقط
(الزيادة الوسيطة ٤٢٧٫٤ نقطة).

حكم المشروع على نفسه — حرفياً:

> «**الحكم مشكلة تعريف لا خلل برمجي صريح** ... السبب التعريفي هو الجمع بين تقديم اليومي
> وحد أدنى فقط للنسبة، واستخدام فئة أغلبية لا تختبر اختياراً منافساً.»

ثم: **«توقف العمل بعد المرحلة الثالثة، ولم تبدأ المرحلة الرابعة.»**
أي أن العيب شُخِّص بدقة، **ولم يُصلح قط**، وبقي المحرك كما هو.

واختبار `V2` الرئيسي (الحاجزان المتقابلان، ٤ مضاعفات × ٦ متغيرات × اتجاهين):
الفروق تراوحت بين **−٢٠٫٥١٪ و +١٧٫٥٠٪** بلا إشارة ثابتة. حكم المشروع:
> «اختلفت الفروق باختلاف الاتجاه والمضاعف والمتغير، **فلم يستخرج حكم موحد أو فائز**.»

واعترف أن أحد اختباراته عديم القيمة:
> «وثق أن اختبار الأقرب من الجانب نفسه **شبه حرفي هندسياً ولا يثبت مهارة**.»

#### (ب) طبقة القرار السياقي — BTCUSDT دقيقة واحدة، آب–أيلول ٢٠٢٥ (بيانات حقيقية)

من `decision_v1/run_artifacts/decision_eval_v1.json` — وهذا **أفضل رقم في المشروع كله**:

```
model:            hit 10 / 17 = 58.82%   coverage 1.0
ex_ante_baseline: hit  6 / 17 = 35.29%   (train-majority = E-CONTINUATION)
```

ظاهرياً: **+٢٣٫٥ نقطة**. حسبتُ الاختبار الثنائي الحرفي: `p = 0.0406`.
**لكن هذا الرقم ينهار بالكامل عند فحص مصفوفة الالتباس:**

```
confusion (predicted rows × realized cols):
  predicted E-CONTINUATION (٢):   → realized E-CONTINUATION 1, E-VIOLATION 1
  predicted E-VIOLATION   (١٥):   → realized E-AMBIGUOUS 1, E-CONTINUATION 5, E-VIOLATION 9

label_distribution (فترة التقييم): E-VIOLATION 10, E-CONTINUATION 6, E-AMBIGUOUS 1
```

**متنبئ ثابت يقول «E-VIOLATION دائماً» يسجّل ١٠/١٧ = ٥٨٫٨٢٪ — تعادل حرفي تام مع النموذج.**

كل «الميزة» الظاهرة هي **فئة الأغلبية في فترة التقييم**، لا مهارة. والسبب أن الأساس
المختار (أغلبية فترة التدريب = `E-CONTINUATION`) كان **١٤ مقابل ١٣** في التدريب —
أي شبه تعادل — ثم انقلب النظام في التقييم فأصبح الأساس هو الثابت الخاطئ.
اختيار ثابت آخر كان سيعطي النتيجة نفسها.

وما هو «النموذج» أصلاً؟ من سجل القرار الأول في نافذة التقييم:

```json
"model_support": {"continuation": 6, "violation": 7},
"model_counts":  {"E-CONTINUATION": 6, "E-VIOLATION": 7, "E-NONE-IN-HORIZON": 1, "E-AMBIGUOUS-SAME-BAR": 0},
"model_ranking": [{"event": "E-VIOLATION", "count": 7, "rank": 1}, ...]
```

**عدّاد تكرار على ٤ خانات، مُدرَّب على ٢٨ حلقة** (٣٢ − ٤ مطهَّرة بسبب تسريب).
أي ~٧ عينات لكل خانة. والقرار الأول حُسم **بفارق عدٍّ واحد** (٧ مقابل ٦).

والمشروع يقول هذا عن نفسه، حرفياً، في نفس الملف:

```
note: "small, correlated sample (17 episodes); the decision ranking stays PROVISIONAL
       and UNVALIDATED; 10/17 vs 6/17 establishes nothing about market understanding
       or trading readiness"
model_vs_baseline: "the ranking is provisional and unvalidated; no predictive quality
       is claimed from 17 evaluation episodes"
selection_quality = NOT_ESTABLISHED     ← في ٦٠ من ٦٠ سجل قرار
model_status      = provisional-unvalidated ← في ٦٠ من ٦٠
horizon_disclosure: "EPISODE_HORIZON_BARS = 24 is NOT source-grounded, NOT owner-approved,
       and NOT a market rule ... Sensitivity across alternative horizon values remains UNTESTED"
```

**نتائج الخطط الافتراضية** (`plan_eval_v1.json`, axis_4) — ٣٢ خطة:

| النتيجة | العدد |
|---|---:|
| أبطلت **قبل** الدخول | ١٩ |
| أبطلت بعد الدخول | ١ |
| بلغت الهدف قبل الإبطال | **٥** |
| مفتوحة عند نهاية التشغيل | ٧ |
| فائتة | ٠ |

ومع التنبيه: «'objective' means one completed confirmed structural leg — **NOT a profit, NOT a return**».

### ٢.٣ الخلاصة المالية

**لا يوجد أي دليل — لا إيجابي ولا سلبي — على أن هذا المشروع يربح مالاً، لأنه لم يُقَس بالمال أصلاً.**
وما قيس فعلاً (مهارة تنبؤ بنيوية) جاء **صفراً أو سالباً** في `engine_v1`، و**متعادلًا مع متنبئ ثابت** في طبقة القرار.

والأهم: حتى لو تحوّلت مهارة التنبؤ البنيوي إلى ٧٠٪، **لا يوجد جسر إلى المال**:
لا تنفيذ، لا أحجام، لا انزلاق سعري، لا تمويل (funding)، لا سيولة دفتر أوامر،
ولا `TIE_ORDER` معروف داخل الشمعة. والفجوة بين «أصابت البنية» و«ربحت الصفقة»
هي بالضبط المكان الذي تموت فيه كل استراتيجيات ICT الآلية.

---

## الجزء الثالث — عيوب حقيقية وجدتها أنا، غير موثَّقة في أي تقرير

هذه جديدة. لم أجد أي واحدة منها في ٦٣٧ ملف markdown ولا في ٢٥ ملف دين تقني.

### ٣.١ 🔴 خطير: `empirical_continuation_rate` أعمى عن الاتجاه — ويُستخدم كاحتمال ربح اتجاهي

`market_understanding/final_evaluation_and_reality.py:869-885`:

```python
for idx in range(len(vis_geoms) - 1):
    g_curr = vis_geoms[idx]
    g_next = vis_geoms[idx + 1]
    require_visible_at(fact_key=g_next.wave_end_confirmed_key, at_key=query_key)
    uncensored_pairs += 1
    if abs(g_curr.final_displacement.value) > 0.0:
        if (abs(g_next.final_displacement.value)
                >= abs(g_curr.final_displacement.value)):
            favorable_continuations += 1
```

`abs()` على الطرفين. **`wave_direction` لا يُستشار إطلاقاً.**
موجة هابطة بعد موجة صاعدة تُحتسب «استمراراً ملائماً» إذا كان حجمها أكبر.
هذا المقياس لا يقيس الاستمرار — يقيس **«هل الموجة التالية أكبر من السابقة»** بغض النظر عن الإشارة.

وهذا الرقم نفسه يغذي بوابة الدخول في `recommendation/causal_ict_lifecycle.py:584`:

```python
ev_in_r = (p_cont * t1_rr) - (p_rev * 1.0) - risk_contract.transaction_cost_in_r
if ev_in_r <= 0.0:
    ...  # رفض
...
ok_reasons = (..., "POSITIVE_COMPETING_RISK_EV_CONFIRMED")
```

**معدل نمو حجمٍ بلا إشارة يُستخدم كاحتمال ربحٍ اتجاهي لصفقة شراء أو بيع.**
هذا خلل دلالي من الدرجة الأولى، وهو في أخطر موضع في المشروع كله:
الرقم الوحيد الذي يقرر `ENTER_LONG` / `ENTER_SHORT`.

والإصلاح ليس سطراً: `FinalizedWaveGeometryRecord` **لا يحمل `wave_direction` أصلاً**
(قارن تعريفه في `wave_representation.py:749-767` — الحقول: `geometry_record_id`,
`wave_process_id`, `timeline_id`, `start/end_turning_point_id`, `start/end_origin_*`,
`wave_end_confirmed_key`, `final_bar_count`, `final_displacement`, `final_path_length`,
`final_efficiency_ratio`, `published_record`). الاتجاه موجود في
`WaveIdentityRecord.wave_direction` (سطر ٤٠٣)، فيتطلب الإصلاح **ربطاً (join) بالمعرّف**
أو إضافة حقل إلى سجل الهندسة — أي تغيير في مخطط سجل مُختوم بالبصمة.

### ٣.٢ 🔴 خطير: حقل «عدد» هو في الحقيقة علم ٠/١

سطر ٨٨٧ في نفس الملف:

```python
right_censored_cnt = 1 if len(vis_geoms) > 0 else 0
```

يُمرَّر إلى حقل اسمه ونوعه `historical_right_censored_count: int`،
ثم يُستهلك في `causal_ict_lifecycle.py:387`:

```python
cens_frac = (right_cens / total_vis) if total_vis > 0.0 else 0.0
```

النتيجة: `cens_frac = 1/N` دائماً ⇒ **يقترب من الصفر كلما كبرت العينة**.
تصحيح البتر (censoring) — وهو من أعقد مسائل الإحصاء في السلاسل الزمنية المقطوعة —
**موجود شكلياً، ويُحسب، ويُبلَّغ، ولا يحمل أي معلومات**.
قارن مع الاختبار (`test_causal_ict_lifecycle.py`) الذي يمرر `right_censored=3` اصطناعياً:
السلوك الحقيقي `1 if ... else 0` **لا يُختبر أبداً**.

### ٣.٣ 🟠 `p_cont` غير مشروط — فالبوابة لا يمكن أن ترفض بسبب المهارة

`_compute_shrunk_competing_risk_probabilities` يعيد **عدداً واحداً لكل التقرير**:

```python
eff_mass = float(muf_report.non_overlapping_span_cluster_count)
emp_rate = muf_report.empirical_continuation_rate
eff_cont = eff_mass * raw_cont_rate
eff_rev  = eff_mass * (1.0 - raw_cont_rate)
p_cont_shrunk = (eff_cont + 1.0) / (eff_cont + eff_rev + 2.0)   # Laplace / Beta(1,1)
if isinstance(emp_rate, TypedState) or eff_mass <= 0.0:
    return (0.5, 0.5, cens_frac, eff_mass)      # ← رجوع إلى ٥٠/٥٠
```

`p_cont` **لا يعتمد على**: اتجاه الصفقة، منطقة نطاق التعامل (خصم/علاوة/تعادل)،
حالة التقاء الأطر، نظام التدفق (داعم/محايد/امتصاص)، نوع نقطة الاهتمام، ولا الإعداد نفسه.
كل التوصيات في لحظة واحدة تشترك في نفس `p_cont`.

فرياضياً، شرط `ev_in_r > 0` يختزل إلى:

```
t1_rr  >  (1 - p_cont + cost) / p_cont
```

مع `p_cont ≈ 0.5` و`transaction_cost_in_r = 0.05`: العتبة ≈ **٢٫١**.
و`min_qualification_rr = 3.0` في الإعداد ⇒ **أي هدف يجتاز حد الأهلية يجتاز بوابة القيمة المتوقعة تلقائياً**.

يعني: `POSITIVE_COMPETING_RISK_EV_CONFIRMED` **زخرفي**. البوابة ترفض على الهندسة فقط،
ولا تملك أي قدرة على الرفض بسبب ضعف الدليل. وهذا يفسّر رياضياً سبب خروج
`entry_choice` **بأداء أسوأ من الأساس بـ٨٫٢٩ نقطة** في `engine_v1`.

### ٣.٤ 🟠 أخطر رقم في مسار التداول = صفر تغطية عند الالتقاء

| الاختبار | ماذا يفعل بـ `empirical_continuation_rate` |
|---|---|
| `tests/test_causal_ict_lifecycle.py` (٢٠ اختباراً) | **يحّقن قيمة اصطناعية**: `empirical_continuation_rate=exact_metric(cont_rate)` مع `cont_rate=0.65` افتراضياً (سطر ١٠٢) |
| `tests/test_muf_s13_s15_final_evaluation_and_reality.py` | **assert واحد فقط** (سطر ٦٥٠): `assert rep_early.empirical_continuation_rate is TypedState.UNAVAILABLE` |

**لا يوجد في ١٬٨٤١ اختباراً أي اختبار يتحقق من دلالة هذا المقياس، أو من أثره النهائي على توصية.**
اختبارات دورة الحياة لا ترى الاشتقاق الحقيقي، واختبارات الاشتقاق لا ترى الاستهلاك.
**الالتقاء بين الوحدتين — وهو أهم التقاء في النظام — غير مغطى بالكامل.**
ولهذا مرّ العيبان ٣٫١ و٣٫٢ دون أن يمسكهما أي شيء، رغم أن الاختبارات كلها خضراء.

### ٣.٥ 🟠 الأرقام السحرية لم تُلغَ — نُقلت إلى ملف إعداد بلا مصدر

`config_btc_recommendations.json`:

```json
"min_qualification_rr": 3.0,
"transaction_cost_in_r": 0.05,
"impulse_expansion_min_causal_rank": 0.70,
"exhaustion_max_causal_rank": 0.30,
"calibration_warmup_bars": 300,
```

بحثتُ عن `impulse_expansion_min_causal_rank` و`exhaustion_max_causal_rank` في كل ملفات
`.md` (٦٣٧ ملفاً، ٩٫٠ ميغابايت): **لا يوجد أي إسناد لمصدر، ولا أي مبرر، ولا أي ذكر في
`OWNER_QUESTIONS.md` ولا في `gaps.md`.** وردت مرة واحدة فقط في `deliverables/82` كوصف تسويقي.

هذه **٠٫٧٠ و ٠٫٣٠ بالضبط** — نمط «٤٠ مقابل ٤٠٫٠١» الذي حذّر منه الوكيل الآخر.
موجود فعلاً، لكن ليس حيث ظنّ.

والسبب أن المانع الآلي لا يصل إليها (انظر ٤٫٢): الماسح يغطي **٥ ملفات فقط**.

### ٣.٦ 🔴 سلسلة الإسناد غير قابلة للتحقق — والالتزامات المثبتة غير موجودة

كل منهجية المشروع مبنية على «ثُبِّت في الالتزام X **قبل** رؤية النتائج». هذه هي الالتزامات:

```bash
$ for c in aa2e7b01 d07049d2 246b1fe6 f8db96eab9 4d25beb3 e8c40a8d 567460bf; do
      printf "%s -> " $c; git cat-file -t $c 2>&1 | head -1; done

aa2e7b01 -> fatal: git cat-file: could not get object info     (أداة التسجيل)
d07049d2 -> fatal: git cat-file: could not get object info     (عقد التنبؤ)
246b1fe6 -> fatal: git cat-file: could not get object info     (قاعدة اختيار الحالات الست)
f8db96eab9 -> fatal: git cat-file: could not get object info   (خطة المتغيرات)
4d25beb3 -> fatal: git cat-file: could not get object info     (تنفيذ النسخة الثانية)
e8c40a8d -> fatal: git cat-file: could not get object info     (متن خارجي — مشروع، مستودع آخر)
567460bf -> commit                                             ← الوحيد الموجود
```

**٥ من ٦ التزامات داخلية مُدَّعاة لا وجود لها في المستودع.**
كل ادعاء «ثبّت قبل النتائج» — وهو **جوهر المنهجية كلها، والفرق الوحيد بين هذا المشروع
وأي ضبط منحنى (curve fitting) عادي** — **لا يمكن التحقق منه من الأثر المُسلَّم**.

### ٣.٧ 🔴 ١٤ فرعاً يتيماً بلا سلف مشترك — والمشروع الكامل لا يوجد في أي فرع

```bash
$ git merge-base e0c2234 51ea54b
(فارغ)          # main وفرع العمل: لا سلف مشترك إطلاقاً
$ git merge-base origin/arena/e91e69b1-trading-bot 51ea54b
(فارغ)          # كذلك
```

| الفرع | الالتزامات | الملفات |
|---|---:|---:|
| `arena/345b2324` (**أساسك**) | **١** | **١٬٢٩١** |
| `arena/e91e69b1` | ١١٧ | ١٢٧٣ |
| `arena/e6974afe` | ١٠٤ | ٧٠٧ |
| `arena/c59ec6a3` (K4b) | ٧٤ | ٦٠٠ |
| `arena/f3ca06dd` | ٧٣ | — |
| `arena/5b6d2bd5` | ٧٢ | — |
| `arena/bd0f0622` | ٦٩ | — |
| `arena/a41fd997` | ٦٧ | ٥٤١ |
| `arena/ad9c5dec` (K4a) | ١٥ | ٦٠٦ |
| `main` | ١ | ٤٠٣ |

**اتحاد كل الفروع = ١٬٥٢٨ ملفاً. فرعك يحمل ١٬٢٩١. ⇒ ٢٣٧ ملفاً من المشروع غير موجودة عندك.**

وتوزيع المادة الحرجة:

| المادة | موجودة على | على فرعك؟ |
|---|---|---|
| `engine_v1/` — **كل النتائج القياسية الحقيقية** (M3, V2, POST_STOP, DIAGNOSIS_TBS, TARGET_SELECTION) | `345b2324` **فقط** | ✅ |
| `understanding/u3-k2/` (٤٢ سجل مقارنة) | `e91e69b1` | ❌ |
| `understanding/u3-k3/` (٢٣ بطاقة مفهوم) | `e91e69b1`, `ad9c5dec` | ❌ |
| `playbook/k4a/` (Q01–Q10) | `ad9c5dec` **فقط** | ❌ |
| `playbook/k4b/` (Q11–Q16 + الآثار) | `c59ec6a3` **فقط** | ❌ |
| `understanding/u2-all-20261106/` (١٣٦ ادعاء) | فرعان | ✅ |

٨٥ ملفاً على أساسك غائبة عن `e91e69b1`، و٦٧ ملفاً على `e91e69b1` غائبة عن أساسك.
**المشروع لا يتراكم — يتشتت.** لا يوجد فرع واحد فيه الصورة الكاملة،
ولا يمكن عمل `diff` أو `bisect` أو `revert` أو نسبة أي تغيير لأي قرار.

و`GITHUB_SYNC.md` يقول: «every completed, verified task is committed and pushed automatically» —
صحيح تقنياً، لكن الناتج **لقطات (snapshots) لا تاريخ**.

### ٣.٨ 🟡 نظافة المستودع وخصوصية المالك

| الملف | الحجم | الملاحظة |
|---|---:|---|
| `run_artifacts/study_replay_stop_v1.json` | **٨٫٩٤ MB** | ناتج تشغيل في Git |
| `monitor_v1/run_artifacts/step_replay_stop_v1.json` | **٨٫٧٢ MB** | ناتج تشغيل في Git |
| `deliverables/23_AUDITOR_PACKAGE_COMPLETE_MERGED.md` | **٢٫٨٤ MB** | وثيقة تسليم |
| `zzz.txt` | **٢٫٣٥ MB** | ⚠️ **سجل محادثات المالك الخاصة مع مساعدي الذكاء الاصطناعي — ٥٣٬٥٣٢ سطراً — مدفوع في مستودع GitHub** |

المجموع المُتتبَّع: **٥٧٫٠ ميغابايت في ١٬٢٩١ ملفاً**.
`.gitignore` يستثني `uploads/` و`*.zip` و`__pycache__/`، لكنه **لا يستثني** `data/` ولا `outputs/`
ولا `.venv` ولا `*.log` ولا `*.json` الضخمة.

`zzz.txt` تحديداً يستحق انتباهاً فورياً: فيه تاريخ المالك الكامل مع جلسات أخرى،
بأسماء فروع وروابط ومستندات. حتى في مستودع خاص، هذا تسريب لسياق عمل داخلي
إلى أثر دائم قابل للاستنساخ. **أنصح بحذفه من الشجرة ومن التاريخ.**

### ٣.٩ 🟡 `deliverables/82` يبيع أكثر مما يثبت

> «**Unlocks Higher Targets (`3R -> 6R -> 12R+`) on Impulse Expansion** ... keeps `100%`
> of the position open, ratchets the stop to lock in **structural profit**»
> وفي عنوان الوحدة: «Solves the "Pending Order Closed at 3R During a **10R+ Explosion**" operational problem»

كلمات مثل «profit» و«10R+ Explosion» و«Unlocks» **لا تظهر في أي مكان آخر** في مشروعٍ
يقول تسليمه الرسمي: `Trading profitability: NOT ESTABLISHED`.
هذا **تنافر نبرة** بين تقرير إغلاق وبقية الأثر. لا يعني أن الكود يكذب —
الكود نفسه صارم — لكنه يعني أن طبقة التقارير غير منضبطة بنفس انضباط طبقة الكود.
وفي مشروع مبني كله على «لا ادعاء بلا دليل»، هذا ليس تفصيلاً.

---

## الجزء الرابع — ما هو عالمي المستوى فعلاً في هذا المشروع

لستُ هنا لأهدم فقط. هذه أشياء **نادرة**، ولا توجد في ٩٩٪ من مشاريع التداول على GitHub:

### ٤.١ `TIE_ORDER_CONTRACT = NOT_PROVEN` — أعمق قرار منهجي في المشروع

```
src/trading_system/sources/__init__.py:15
  "TIE_ORDER_CONTRACT remains NOT_PROVEN always: a kline open/close is a ..."
```

معظم الاختبارات الخلفية للتجزئة **تفترض ضمنياً** ترتيب OHLC داخل الشمعة
(هل لامس القمة أولاً أم القاع؟) — وهذا الافتراض وحده يصنع أرباحاً وهمية.
هذا المشروع **يرفض** افتراضه، ويجعله ثابتاً fail-closed مفروضاً عبر **٣٤ موضعاً**،
ويرفض المصدر الذي لا يحفظه:

```python
# trajectory/causal_market_context_core.py:1557
if minute_facts_source.provenance.TIE_ORDER_CONTRACT != "NOT_PROVEN":
    raise CausalMarketContextCoreError("minute-facts source must preserve NOT_PROVEN tie-order semantics")
```

وكذلك `intrabar_path_metrics` يعيد `UNAVAILABLE(AMBIGUOUS_INTRABAR_CHRONOLOGY)` بدل التخمين.
**هذا مستوى احترافي حقيقي، وأغلب من يبيع بوتات لا يعرف أن هذه المشكلة موجودة.**

### ٤.٢ انضباط مفروض آلياً على مستوى شجرة الصياغة (AST)

`market_understanding/contracts.py:209, 247-276` + `tests/test_muf_s0_contracts.py:99-131`:

```python
ALLOWED_NUMERIC_CONSTANTS: Final[Tuple[int, ...]] = (0, 1)

def scan_market_shape_implementations(source: str) -> Tuple[str, ...]:
    """Return names/constants indicating hidden market thresholds or windows."""
    ...
    if node.value not in ALLOWED_NUMERIC_CONSTANTS:
        violations.append(f"numeric_constant:{node.value!r}")
```

وتُشغَّل كاختبارات:

```python
def test_attack24_no_hidden_market_thresholds_or_windows():
    for name, source in _production_sources().items():
        assert scan_market_shape_implementations(source) == (), name
    assert scan_market_shape_implementations("window_size = 20\n") == ("window_size", "numeric_constant:20")
    assert scan_market_shape_implementations("value = 0.5\n") == ("numeric_constant:0.5",)

def test_attack23_prohibited_implementations_guard():
    assert scan_prohibited_implementations("def compute_pnl():\n    return None\n") == ("compute_pnl",)
    assert scan_prohibited_implementations("def trade_execution():...")   == ("trade_execution",)
    assert scan_prohibited_implementations("class FitModel:\n    pass\n") == ("FitModel",)
    assert scan_prohibited_implementations("signal_value = 1\n")          == ("signal_value",)
```

**أي عدد حقيقي غير ٠ و ١ في تلك الملفات = اختبار أحمر.** هذا منع بنيوي للأرقام السحرية،
لا تعهداً أخلاقياً. لم أرَ مثله في مشروع تداول مفتوح.

⚠️ **لكن النطاق محدود** — وهذا ما فات الوكيل الآخر في الاتجاهين:

```python
_S0_DIR     = src/trading_system/market_understanding
_S0_MODULES = ("__init__.py", "contracts.py", "identity.py", "availability.py", "records.py")
```

**٥ ملفات فقط** من أصل ١٤٦ ملف بايثون و٨٢٬٢٠٠ سطر.
`ict_engine` و`recommendation` و`contextual_selection` و`decision` و`calibration`
**خارج نطاق الماسح**. ولهذا بالضبط استطاعت ٠٫٧٠ و٠٫٣٠ و٣٫٠ أن تعيش في
`config_btc_recommendations.json` بلا إسناد (٣٫٥).
الحماية حقيقية لكنها **جزيرة**، وليست قارة.

### ٤.٣ `OWNER_QUESTIONS.md` — ١٢ سؤالاً لا تجيب عنها المصادر، معلنة كحاجز تشغيل

> «**None of these numbers or orderings were invented; the deterministic engine must not run until they are decided.**»

| # | السؤال |
|---|---|
| Q1 | ما المقدار العددي، إن وُجد، beyond the structural stop extreme؟ |
| Q2 | عند تعدد البرك المرشحة كسحب، **كيف تُرتَّب**؟ |
| Q3 | عند تعارض الانحياز الشهري والأسبوعي، أيهما يحكم؟ |
| Q4 | أي مجموعة killzone هي المعتمدة (٥ نوافذ مقابل ٤ أسماء)؟ |
| Q5 | هل تُشترط شمعة وسطية اندفاعية لتسمية FVG؟ (مصادر متعارضة مباشرة) |
| Q6 | FVG أولاً أم OB أولاً عند التراكب؟ |
| Q7 | كم يجوز أن تشيخ كتلة الأوامر وتبقى قابلة للتداول؟ |
| Q8 | المخاطرة لكل صفقة، وأقصى خسارة يومية، ومعنى «consistently» |
| Q10 | بعد MSS: أمر معلق عند المصفوفة أم دخول سوقي عند الإغلاق عبرها؟ |
| Q11 | عند تصادم شرطي امتناع، أو وجود شرط مع إعداد صالح — أيهما يفوز؟ |

**Q2 هو بالضبط سؤال «السيولة القوية» الذي طرحه الوكيل الآخر — وهو معلَن كمسألة مفتوحة منذ البداية، لا كجهل مكتشف حديثاً.**

### ٤.٤ جدول «الإغراءات المُقاوَمة» (`AUDIT.md` §٧)

| الإغراء | ما فُعل |
|---|---|
| كتابة صيغة الشموع الثلاث المحفوظة كأنها معياره | أُبعدت عن الأقسام المقتبسة؛ ظهرت فقط كـ `ENGINEERING_HYPOTHESIS` تشير إلى `U0036`/`U0038` |
| اعتماد kill zone لندن ٢–٥ صباحاً كمحسوم | وُجد أنه يقول ١ أيضاً؛ **كلاهما مقتبس كبدائل متوازية** |
| إعطاء تسامح tick ثابت للقمم «المتساوية» | تُرك مفتوحاً كتساوٍ نسبي لسعة الأرجوحة المحلية |
| **اعتماد «خمسة مقابض» / «٢٠ نقطة» / «٢٪» كعتبات للمحرك** | اقتُبست كملاحظات خاصة برسمه؛ `gaps.md` يسجل أن تعميمها **اختلاق** |
| ملء كسور الخروج الجزئي | هو صراحة يسلّم الكمية للمتداول (`U0118`, `U0119`)؛ تُركت `OWNER_DECISION` |
| تفسير أي حركة مروية كربحية | **لا تفسير ربحية في أي مكان؛ لم تُحمَّل بيانات** |

هذا هو الجواب الحقيقي على سؤال «حافظ مو فاهم». **الحفظ مُتحقَّق منه آلياً (١٣٦/١٣٦ حرفياً)،
والفهم مُعلَن كنقص في ١١٧ حالة — من قبل المشروع نفسه، قبل أن يقوله أي مدقق.**

### ٤.٥ ٢٥ ملف دين تقني، كل واحد فيه قسم «الاختصار المحرَّم»

`PERFORMANCE-DEBT-001.md`:
> «**Forbidden shortcut**: Do **not** introduce an arbitrary rolling history cap solely to
> improve performance. A fixed cap changes the estimator's public meaning and must not be
> disguised as an optimization.»

`RESEARCH-DEBT-002.md` (انحياز مدة الحلقة في أساس الاستمرار):
> «**Do not fix it now.** Forbidden premature fixes: fixed duration normalization,
> arbitrary age penalty, fixed rolling cap, hand-tuned correction.»

مشروع يكتب قائمة بما **يُمنع** إصلاحه الآن، وبما يُمنع اختصاره — هذا انضباط نادر.

### ٤.٦ الأرقام الإجمالية

| المقياس | القيمة |
|---|---:|
| كود مصدري | **٨٢٬٢٠٠ سطر** / ١٤٦ ملف |
| اختبارات | **٥٠٢٠٢ سطر** / ١٬٨٤١ + ١١٦ + ٣٦ اختبار |
| نسبة الاختبار إلى الكود | **٠٫٦١** |
| توثيق markdown | **٩٫٠ ميغابايت** / ٦٣٧ ملف |
| **التوثيق ÷ الكود** | **١٫٣٨** (توثيق أكثر من كود) |
| ادعاءات مُسندة بالمصدر | ١٣٦ (u2) + ٩٥ (K4a) + ٧١ (K4b) = **٣٠٢**، كلها مُتحقَّق منها حرفياً ١٠٠٪ |
| مفاهيم ICT مفهرسة | ٦٦ |
| مفاهيم مُنفَّذة | **٢٥** منفذ / **١١** جزئي / **٣٠** بانتظار |
| المتن المصدرى | **٤٩٠ تفريغاً، ٢٬٥٤٩٬١٩٨ كلمة**، SHA-256 مثبّت |
| بطاقات المفاهيم غير المبنية | **٤٥ من ٦٦** (منها `breaker`, `mitigation_block`, `rejection_block`, `consequent_encroachment`, `optimal_trade_entry`, `turtle_soup`, `silver_bullet`, `judas_swing`, `smt_divergence`, `market_maker`, `2022_model`) |

---

## الجزء الخامس — «حافظ مو فاهم»؟ الحكم على السؤال نفسه

### ٥.١ ما الذي يعنيه «يفهم مايكل» هنا — والمشروع يجيب عليه بدقة مخيفة

`K3_CONCEPT_COVERAGE.md` يصنّف **كل مفهوم من ٦٦** بثلاث حالات، مع سبب لكل واحدة:

| الحالة | العدد | أمثلة |
|---|---:|---|
| **منفذ** | ٢٥ | `buy_side_liquidity`, `fair_value_gap`, `dealing_range`, `equilibrium`, `premium`, `discount`, `kill_zone`, `no_trade`, `break_even` |
| **جزئي** | ١١ | `run_on_stops` (الأخذ والعودة منفذان؛ كسر البنية المتدخل ينتظر)، `shift_in_market_structure`، `higher_time_frame` (الهرمية الكاملة تنتظر)، `stop_loss` (لا عقيدة وقف كاملة)، `money_management` (رأس المال والكميات تنتظر) |
| **بانتظار** | ٣٠ | `breaker`, `mitigation_block`, `rejection_block`, `consequent_encroachment`, `optimal_trade_entry`, `2022_model`, `asian_range`, `midnight`, `bias`, `directional_bias`, `partials`, `one_shot_one_kill`, `turtle_soup`, `silver_bullet`, `judas_swing`, `smt_divergence`, `market_maker`, `volume_imbalance`, `liquidity_void` |

وأسباب «بانتظار» **ليست كسلاً** — كل واحد مُعلَّل:

- `rejection_block`: «طول الفتيل والاختيار البصري **بلا عتبة مصدرية حاسمة**»
- `liquidity_void`: «**التعاريف المصدرية المتنافسة لم تختزل** إلى فجوة أو إزاحة»
- `smt_divergence`: «**لا توجد بيانات الأدوات الأخرى** اللازمة للمقارنة»
- `volume_imbalance`: «**لا يوجد حقل حجم موثوق** يحقق التعريف المستقل»
- `bias`: «لا يوجد اتجاه مركب **قابل للحكم بلا تقدير بصري**»
- `market_maker`: «المراحل المركبة و**الاختيار البصري** لم يختزلا إلى معرف سببي»
- `turtle_soup`: «الأخذ والعودة **لا يكفيان**؛ سرعة الرفض والسياق ينتظر»

وهذا يقود إلى **الحقيقة المركزية التي يجب أن تُفهم عن هذا المشروع وعن ICT معاً**:

> **الجزء الأكبر من ICT غير قابل للأتمتة من التفريغات النصية وحدها — لأنه مُعلَّم بصرياً.**

`gaps.md` §١ يسميها «الفجوة المهيمنة ... وهي بنيوية لا عرضية»:

| الادعاء | النص | الناقص |
|---|---|---|
| `U0045` | «the order block really begins at **this** candle's opening not **this** last one» | أي شمعة هي «هذه» — **يلزم صورة الرسم** |
| `U0071` | «i want to use **this** most recent one and **this** is my dealing range» | أي ساقين كانتا على الشاشة |
| `U0063` | «which one's the shift in market structure well i'm playing the run up **here**» | المرشحان غير محددين في النص |
| `U0009` | 「Right Above **This** high would be buy side liquidity」 | القمة غير مسمّاة |

ويذكر الحل الممكن ولم يُنفَّذ: «The transcripts carry `RefLink` YouTube URLs with `&t=` seconds,
so the frame is in principle locatable — but **frame extraction was out of scope and was not run**.»

**إذاً الجواب على «حافظ مو فاهم»:**
- **الحفظ:** مُثبت آلياً، ٣٠٢ اقتباساً، ١٠٠٪ حرفية، بصمة أرشيف، مراجعة مثبّتة. ممتاز.
- **الفهم:** المشروع **لا يدّعيه**. يعلن صراحة أن ١١٧ من ١٣٦ ادعاء فيها انحراف مفردات
  (§١٠.١: «the largest weakness of the claim set»)، وأن ٤٥ من ٦٦ مفهوماً بلا بطاقة،
  وأن الإشارات الظرفية (deixis) غير محلولة في كل المتن، وأن ٦ أيام EURUSD صالحة
  «far too few to validate anything».
- **الخلل الحقيقي ليس في الفهم ولا في الحفظ — بل في أن الفهم الموجود لا يصل إلى المال.**
  ٢٥ مفهوماً منفذاً، ونتيجتها القياسية **صفر أو سالب مقابل أساس تافه**.

### ٥.٢ هل هو «وحش» أم «غبي ومعاق»؟

كلا الوصفين خاطئ. التقييم الصحيح:

**هذا مشروع بنية تحتية إبستيمية من الطراز الأول، يفتقر إلى أي طبقة تحقق تجريبية ذات معنى،
ولم يُثبت — ولم يدّعِ — أي قدرة على كسب المال.**

- «وحش» — في **الانضباط**: نعم، وبفارق كبير عن أي شيء مشابه.
- «وحش» — في **الفهم السوقي المُثبت**: لا. ٢٥ من ٦٦ مفهوماً، وصفر ميزة مقاسة.
- «غبي» — لا. الأغبياء لا يكتبون `TIE_ORDER_CONTRACT = NOT_PROVEN` ولا ٢٥ ملف دين تقني بأقسام «اختصار محرَّم».
- **المشكلة ليست الغباء، بل سوء توجيه جهد هائل.** ٨٢٬٢٠٠ سطر كود و٩ ميغابايت توثيق
  أُنفقت على **منع الأخطاء** (وهذا نجح بشكل باهر)، و**صفر** على **إثبات القيمة** (وهذا لم يبدأ).

مشروع trading يحتاج إلى شيئين: (١) بنية لا تكذب على نفسها، (٢) ميزة مقاسة.
هذا المشروع يملك (١) بمستوى نادر عالمياً، و(٢) بمستوى **صفر**.
وهو يعرف ذلك ويقوله.

---

## الجزء السادس — بطاقة التقييم

| المحور | الدرجة | التعليل |
|---|:---:|---|
| **جودة الكود والحِرفية** | **٩٫٥ / ١٠** | dataclasses مجمّدة بـ slots، تحقق fail-closed في كل `__post_init__`، أكواد أخطاء حتمية، لا استثناءات عارية، لا توابع god. قرأت ~٢٠٠٠ سطر ولم أجد رائحة كود واحدة. |
| **انضباط الاختبارات** | **٨٫٥ / ١٠** | ١٬٩٩٣ اختباراً كلها خضراء، اختبارات خصومية، ماسحات AST. **خصم ١٫٥ للاختبار الصفري عند التقاء `empirical_continuation_rate` ↔ `p_cont`** (٣٫٤) — أخطر فجوة تغطية في مشروع شديد الاختبار. |
| **الأمانة الفكرية** | **١٠ / ١٠** | لا نظير لها. نشروا ١/١٦٥، ورفضوا ضبطه، وكتبوا «establishes nothing» على أفضل أرقامهم، وأدرجوا جدول إغراءات قاوموها، و١٢ سؤالاً حاجزاً. **هذه أعلى درجة في التقييم كله وبلا منازع.** |
| **التأصيل بمصدر (مايكل/ICT)** | **٧٫٥ / ١٠** | ٣٠٢ ادعاء مُتحقَّق حرفياً، ٤٩٠ تفريغاً/٢٫٥ مليون كلمة، ربط `claim_ids` داخل بنيات البيانات. **خصم ٢٫٥: ٤٥ من ٦٦ مفهوماً بلا بطاقة، ١١٧/١٣٦ انحراف مفردات، والقراءة اقتباسات ≤٢٥ كلمة لا نوافذ كاملة.** |
| **صحة المنهجية الإحصائية** | **٣ / ١٠** | الأساس المختار في `decision_v1` **متنبئ ثابت خاطئ**؛ متنبئ «E-VIOLATION دائماً» يعادل النموذج حرفياً (١٠/١٧). ١٧ حلقة يومية بنوافذ متداخلة ⇒ استقلالية معدومة. أساس الأغلبية في `engine_v1` متحلل (١٠٠٪/٠٪). **خصم ٧ — رغم أن المشروع يعلن بنفسه أن النتيجة «لا تُثبت شيئاً»، إلا أنه لم يكتشف أن أساسه كان يقيس الشيء الخطأ.** |
| **صحة الدلالة الاقتصادية** | **٢ / ١٠** | `p_cont` أعمى عن الاتجاه (٣٫١)، وغير مشروط (٣٫٣)، وبوابة EV زخرفية رياضياً، وتصحيح البتر ميت (٣٫٢)، و٤ عتبات بلا إسناد (٣٫٥)، وR:R وسيط ١٤٤:١. |
| **قابلية الإنتاج / الربح** | **٠ / ١٠** | لا يوجد قياس للمال بنيوياً (٧ مواضع كلها منع). لا تنفيذ، لا أحجام، لا انزلاق، لا تمويل. لا يمكن التشغيل كما سُلم (لا بيانات، NOT_CONFIGURED). |
| **إدارة المستودع والتسليم** | **١٫٥ / ١٠** | ١٤ فرعاً يتيماً بلا سلف مشترك، ٢٣٧ ملفاً مفقوداً عن فرعك، ٥ من ٦ التزامات مثبّتة **غير موجودة**، بوابة `MANIFEST` حمراء، `main` لقطة غير ذات صلة، ٥٧ ميغابايت في Git بينها سجل محادثات المالك الخاصة. |
| **قابلية إعادة الإنتاج** | **٢ / ١٠** | تعمل فقط على `numpy 1.26.4 / pandas 2.3.3` بلا CI ولا قفل. كل البيانات الحقيقية خارج المستودع. كل بصمات الالتزامات الداخلية غير قابلة للحل. |
| **إمكانية الإنقاذ** | **٨ / ١٠** | الأساس السببي سليم ومختبَر ومُحكَم. العيوب ٣٫١–٣٫٥ محددة ومحلية وقابلة للإصلاح. **البنية تستحق ما يُبنى عليها؛ ما بُني فوقها لم يُختبر.** |

### المجموع المرجّح

| السؤال | الجواب |
|---|---|
| **كمشروع هندسي** | **٨٫٦ / ١٠** — من أفضل ما رأيت في هذا المجال |
| **كنظام يفهم السوق مثل مايكل** | **٣٫٥ / ١٠** — ٢٥ من ٦٦ مفهوماً، والفهم غير مُثبت ولا مُدّعى |
| **كبوت يجيب مصاري اليوم** | **٠ / ١٠** — ليس ضعيفاً، بل **غير موجود**. لا يوجد مسار من الكود إلى المال. |
| **كأساس يُبنى عليه شيء قد يجيب مصاري** | **٦ / ١٠** — أساس نادر القيمة، لكن الطريق أمامه طويل وغير مضمون |

**الدرجة الإجمالية: ٤٫٥ / ١٠ كمنتج، ٨٫٦ / ١٠ كأساس.**

---

## الجزء السابع — هل في أمل؟ وما الترتيب الصحيح للعمل

**نعم، في أمل — لكن ليس الأمل الذي تسأل عنه.**

الأمل ليس «شغّله بكرة وجيب مصاري». هذا مستحيل اليوم، وأي شخص يعدك به يكذب عليك.
الأمل هو أن **لديك أصعب جزء في المشكلة منفَّذاً ومستحيل الكسر تقريباً**،
وهو الجزء الذي لا يملكه ٩٩٪ من مشاريع التداول:
بنية لا تستطيع أن تكذب على نفسها، حتى لو أراد صاحبها ذلك.

معظم البوتات تنجح في الاختبار الخلفي وتفشل في الواقع لأنها تسرّب المستقبل.
**هذا المشروع يستحيل فيه تسريب المستقبل** — مفروض آلياً، مختبَر، ومختوم بالبصمة.
هذه أصول حقيقية، وهي الجزء الذي لا يمكن شراؤه ولا استعارته.

لكن يجب أن تكون صريحاً مع نفسك في three حقائق:

1. **حتى الآن، كل ما قيس كان صفراً أو سالباً.** ليس «لم يُقَس» — قيس، وجاء صفراً وسالباً.
2. **الميزة في الأسواق السائلة صعبة للغاية.** BTCUSDT على دقيقة واحدة هو من أصعب الأماكن
   الممكنة، لأنك تتنافس مع صانعي سوق وشركات HFT. لو كان ICT قابلاً للأتمتة من تفريغات
   يوتيوب، لكان قد أُتمت.
3. **الفجوة المهيمنة بنيوية لا مؤقتة:** مايكل يعلّم على رسم لا تراه. بلا استخراج إطارات الفيديو
   (وهو ممكن — `RefLink` فيه `&t=` بالثواني)، ستبقى `deixis` غير محلولة و٣٠ مفهوماً في الانتظار.

### الترتيب الصحيح — ولا شيء منه «بناء معمارية جديدة»

> **القاعدة: ممنوع كتابة سطر معمارية جديد قبل إغلاق البنود ١–٥.**
> الوكيل الآخر اقترح بناء ما هو مبني. هذه هي الأولوية المعاكسة تماماً.

**١ — 🔴 ادمج الفروع الأربعة عشر أولاً (قبل أي شيء آخر)**
لا يمكن إصلاح ما لا تملك. أنشئ فرعاً واحداً يحوي اتحاد الـ١٬٥٢٨ ملفاً:
`345b2324` (engine_v1 results) + `e91e69b1` (u3-k2/k3) + `ad9c5dec` (k4a) + `c59ec6a3` (k4b) + `a41fd997`.
ثم **ابنِ تاريخاً حقيقياً**: من الآن، فرع واحد، التزامات صغيرة، رسائل واضحة.
اللقطات اليتيمة تنتهي اليوم.

**٢ — 🔴 أعد ختم `MANIFEST.sha256` وأصلح البوابة الحمراء**
بوابة fail-closed حمراء وغير مُلاحَظة تعني أن كل ختم «CLOSED» لاحق بلا قيمة.
أعد التثبيت بقرار مالك موثَّق، أو احذف الختم وقل بصراحة «غير مختوم».
الحالتان مقبولتان؛ الحالة الحالية (ختم مدّعى وبوابة حمراء) غير مقبولة.

**٣ — 🔴 أصلح `empirical_continuation_rate` (٣٫١ + ٣٫٢)**
- أضف `wave_direction` إلى `FinalizedWaveGeometryRecord` (أو اربطه من `WaveIdentityRecord`)
  واجعل الاستمرار **مشروطاً بتوافق الإشارة**: استمرار = الموجة التالية في نفس الاتجاه،
  لا «أكبر حجماً».
- أصلح `right_censored_cnt` ليعدّ فعلاً الحلقات التي امتدت نافذتها بعد آخر بيانات متاحة —
  كما يفعل `decision_layer` بشكل صحيح (`label window extends beyond the available data (censored)`).
- **اكتب اختبار الالتقاء أولاً** (٣٫٤): اختبار واحد يمر من `bars` حقيقية إلى
  `CausalTradeRecommendationRecord.decision`، ويتحقق أن تغيير اتجاه موجة يغيّر `p_cont`
  في الاتجاه الصحيح. اختبار أحمر، ثم الإصلاح.

**٤ — 🔴 أعد تعريف الأساس في `decision_v1` (٢٫٢ب)**
الأساس الحالي متنبئ ثابت خاطئ. أضف **ثلاثة** أسس، كلها محسوبة ex-ante من التدريب فقط:
- `ALWAYS_E_VIOLATION` (كان سيعادل النموذج: ١٠/١٧)
- `PERSISTENCE` (تكرار تسمية الحلقة السابقة)
- `CONTEXT_MARGINAL` (أغلبية كل خانة سياق على حدة)

**لا تدّعِ مهارة إلا إذا تفوّق النموذج على الثلاثة معاً.** ثم احسب فاصل ثقة
مع **تصحيح الاعتماد التسلسلي** (block bootstrap على أيام، لا binomial على حلقات).
`p = 0.0406` الذي حسبتُه **باطل** لأن الحلقات غير مستقلة — والمشروع نفسه يقول
`STATISTICAL_INDEPENDENCE_STANDING_CLAIM = "NOT_PROVEN_EPISODE_ACCOUNTING_ONLY"`.

**٥ — 🟠 أسند العتبات الأربع أو احذفها (٣٫٥)**
`min_qualification_rr = 3.0`, `transaction_cost_in_r = 0.05`,
`impulse_expansion_min_causal_rank = 0.70`, `exhaustion_max_causal_rank = 0.30`.
لكل واحدة: إما إسناد بمصدر (رقم claim)، أو إعلانها `OWNER_DECISION_NEEDED` في
`OWNER_QUESTIONS.md` (حيث تنتمي — Q1 وQ8 هناك أصلاً)، أو حذفها.
ثم **وسّع `scan_market_shape_implementations` من ٥ ملفات إلى كل `src/`**
واستثني ما هو مصرَّح به صراحة في عقد مُسند. الحماية الحالية جزيرة؛ اجعلها قارة.
وطبّق شرط الوكيل الآخر الذي أوافق عليه: **لا تقبل عتبة إلا إذا القرار لا يتغير عبر مدى معقول من القيم.**

**٦ — 🟠 أصلح هندسة الهدف/الوقف في `engine_v1` (٢٫٢أ)**
R:R وسيط ١٤٤:١ ليس نتيجة سوقية، بل أثر `DAILY_THEN_DISTANCE`. المشروع شخّصه ورفض إصلاحه
بعد رؤية النتائج — **وهذا كان قراراً صحيحاً في وقته**. الآن، وبعد توثيق التشخيص،
الإصلاح مشروع: **اكتب العقدة الجديدة (spec) وثبّتها بالبصمة، ثم شغّل، ثم انشر —
بلا اختيار فائز بعد الرؤية.** `V03` (`DISTANCE_ONLY`) موجود أصلاً كمتغير تفسيري.
وأعد تعريف الأساس: أساس الأغلبية المتحلل (١٠٠٪/٠٪) لا يقيس شيئاً؛ استبدله بأساس
**الاختيار المنافس** الذي وصفه `PREDICTION_SPEC_v2` (الأقرب / الأبعد / سحب شبه عشوائي ببذرة معلنة).

**٧ — 🟠 ابنِ الجسر إلى المال — أو احذف الفكرة نهائياً**
هذا هو القرار المصيري. أمامك طريقان، ولا ثالث لهما:

- **(أ) البقاء أداة تحليل:** أعلن أن المشروع **مساعد تحليل لا بوت تداول**،
  واحذف `causal_ict_lifecycle.py` و`config_btc_recommendations.json` و`run_btc_causal_recommendations.py`
  وكل لغة «3R → 6R → 12R+» من `deliverables/82`.
  المشروع يصبح عندئذٍ **ممتازاً ومتسقاً**: بنية فهم سوق بلا ادعاء تداولي. وهذا مشروع يستحق العيش.

- **(ب) أن تصير بوتاً:** عندها يلزم، بالترتيب وبلا اختصار:
  1. **نموذج تكاليف**: انزلاق سعري، رسوم، عمق دفتر أوامر، تمويل (funding) للعقود الدائمة.
  2. **محاكاة تنفيذ** تحترم `TIE_ORDER = NOT_PROVEN` — أي **لا تحسم أي صفقة داخل شمعة غامضة**،
     بل تعدّها `UNRESOLVED` وتبلغ عن نسبتها. هذا سيقضي على جزء كبير من الصفقات، وهذا صحيح.
  3. **إدارة مخاطر** حقيقية (Q8 ما زال مفتوحاً: «Risk per trade, max daily loss»).
  4. **قياس المال**: منحنى رأس مال، عامل ربح، أقصى تراجع، شارب، وعدد الصفقات.
  5. **Walk-forward** على ≥٣ سنوات و≥٣ أدوات، مع فترات اختبار لم تُلمس قط.

  **لا تبدأ بأي واحدة قبل إغلاق ١–٦.** ومن واقع الأرقام الحالية (صفر ميزة مقاسة، ١٧ حلقة تقييم)،
  احتمال أن يمر هذا باختبار walk-forward ذو معنى **منخفض جداً**. قل ذلك لنفسك قبل أن تبدأ.

**٨ — 🟡 نظافة فورية**
- احذف `zzz.txt` من الشجرة **ومن التاريخ** (`git filter-repo`) — ٢٫٣٥ ميغابايت من محادثاتك الخاصة.
- انقل `*.json` الضخمة (>١ ميغابايت) من `run_artifacts/` إلى Releases أو تخزين خارجي، واترك بصماتها.
- أضف إلى `.gitignore`: `data/`, `outputs/`, `.venv/`, `*.log`, `.pytest_cache/` (موجود)، `*.egg-info/` (موجود).
- أضف CI (GitHub Actions) يشغّل ١٬٩٩٣ اختباراً على `numpy==1.26.4 / pandas==2.3.3` عند كل دفع.
  هذا وحده كان سيكشف البوابة الحمراء (١٫٢) فوراً.

**٩ — 🟢 بعد كل ما سبق فقط: أغلق فجوة الرسم**
`RefLink` في التفريغات يحمل `&t=` بالثواني ⇒ الإطار قابل للتحديد.
استخراج إطارات عند نوافذ `deixis` (٤٥ مفهوماً مؤجلاً، و`U0045`/`U0071`/`U0063`/`U0009`)
هو **أعلى مردود معرفي متبقٍ** — لأنه يحلّ الفجوة التي سماها المشروع نفسه «المهيمنة والبنيوية».
لكنه بلا قيمة قبل أن يكون لديك طريقة لقياس ما إذا كان الفهم الإضافي يحسّن قراراً.

---

## الجزء الثامن — الخلاصة بجملة واحدة لكل سؤال سألتَه

| سؤالك | الجواب |
|---|---|
| **«شفلي ياه خارق؟»** | خارق في **الانضباط** (١٠/١٠ أمانة فكرية، بنية سببية مفروضة آلياً). ليس خارقاً في **النتيجة** (صفر ميزة مقاسة، صفر قياس للمال). |
| **«متل مايكل؟»** | لا. يعرف ٢٥ من ٦٦ مفهوماً، ويعرف أنه يعرفها، ويقول لك أي ٣٠ لا يعرفها ولماذا. **هذا أفضل من مايكل في الصدق، وأضعف منه بكثير في التغطية.** ومايكل نفسه لا يمكن أتمتته من نص — هو يعلّم على رسم لا تراه. |
| **«وحش بيفهم، ولا غبي ومعاق؟»** | لا هذا ولا ذاك. **بنية تحتية إبستيمية من الطراز الأول بلا أي طبقة تحقق تجريبية.** ليس غبياً — الأغبياء لا يكتبون `TIE_ORDER_CONTRACT = NOT_PROVEN`. مشكلته أن ٨٢٬٢٠٠ سطر أُنفقت على **منع الخطأ** (نجحت بامتياز) و**صفر** على **إثبات القيمة** (لم تبدأ). |
| **«هل في أمل يشتغل ويطلع توصيات تجيب مصاري؟»** | **اليوم: صفر.** لا يوجد مسار من الكود إلى المال — لا تنفيذ، لا أحجام، لا تكاليف، ولا قياس. و`pnl` تظهر ٧ مرات في ٨٢٬٢٠٠ سطر، **كلها منع**. **غداً: ممكن نظرياً، غير مرجّح عملياً.** كل ما قيس جاء صفراً أو سالباً، وأفضل نتيجة (١٠/١٧) يعادلها متنبئ ثابت. الأمل الحقيقي ليس في الربح، بل في أن **لديك أصعب جزء من المشكلة منفذاً بشكل لا يُكسر** — وهذا نادر وحقيقي. |

---

## ملحق — الأوامر لإعادة إنتاج كل رقم في هذا التقرير

```bash
# البيئة (إلزامي: الإصدارات المثبتة)
python3 -m venv .venv && . .venv/bin/activate
pip install numpy==1.26.4 pandas==2.3.3 pytest

# ١٫١ — الاختبارات (١٬٨٤١ + ١١٦ + ٣٦)
cd TRADING-BOT/project/trading_project && python -m pytest tests/ -q            # exit=0
python -m pytest src/trading_system/ict_engine/tests -q                          # exit=0
cd ../.. && python -m pytest field_runner -q                                     # 35 passed, 1 failed

# ١٫٢ — البوابة الحمراء
python -m pytest field_runner/runner_tests/test_runner_guards.py::test_closed_project_manifest_untouched -q

# ١٫٤ — لا يعمل بلا بيانات المالك
python run_btc_causal_recommendations.py

# ٢٫٢ب — أرقام القرار والأساس ومصفوفة الالتباس
cd project/trading_project/docs/research
python3 -c "import json;d=json.load(open('decision_v1/run_artifacts/decision_eval_v1.json'));\
print(d['evaluation']);print(d['ex_ante_baseline']['hit_rate'],d['ex_ante_baseline']['train_label_counts'])"
python3 -c "import json;d=json.load(open('plan_v1/run_artifacts/plan_eval_v1.json'));\
print(d['axis_3_event_forecasts_later_data']['model']);print(d['axis_4_hypothetical_plan_outcomes'])"

# ٣٫٦ — الالتزامات المثبتة غير موجودة
for c in aa2e7b01 d07049d2 246b1fe6 f8db96eab9 4d25beb3 567460bf; do
  printf "%s -> " $c; git cat-file -t $c 2>&1|head -1; done

# ٣٫٧ — الفروع اليتيمة والـ٢٣٧ ملفاً المفقودة
git fetch origin 'refs/heads/arena/*:refs/remotes/origin/arena/*'
git merge-base e0c2234 51ea54b                     # فارغ
for b in $(git branch -r|grep arena|tr -d ' '); do
  echo "$(git rev-list --count $b) $b"; done | sort -rn
for b in $(git branch -r|grep -E 'arena|main'|tr -d ' '); do
  git ls-tree -r --name-only $b; done | sort -u | wc -l   # 1528

# ٤٫٢ — نطاق ماسح الأرقام السحرية (٥ ملفات فقط)
grep -n "_S0_MODULES\|ALLOWED_NUMERIC_CONSTANTS" \
  project/trading_project/tests/test_muf_s0_contracts.py \
  project/trading_project/src/trading_system/market_understanding/contracts.py
```

---

**نهاية التقرير ١٠٤.**
لم يُعدَّل أي ملف مصدري أثناء إعداده. كل رقم فيه مستخرج من أثر موجود في المستودع،
أو من تشغيل فعلي موثَّق أمره في الملحق.
