# بيان تسجيل المرحلة الثالثة وبصمات الملفات

## النطاق والإثبات

التسجيل على 2022 وحدها، والأفق 288 شمعة سوق. لم يقرأ ملف 2023 أو لاحقاً. الملفات الكبيرة خارج المستودع في `/home/user/ict_engine_data/m3/`.

- عقد التنبؤ: `d07049d21d41bef031034c5f82975569bfdf27fa`.
- خطة المتغيرات: `f8db96eab9c353b572dd41eb845d184f6e6174f7`.
- أداة التسجيل ومولد التقارير: `aa2e7b019e62c44897e6f763739407830ea2256e`. إنشاء هذا الالتزام لاحق للعقد والخطة.
- قاعدة الأمثلة: `d07049d21d41bef031034c5f82975569bfdf27fa`.
- مصدر المعرفة الجديدة: `567460bf4fa0773ef1633738b72a61399cfcf3e3`.
- ملف 2022: `490d4fb9f1a07a1d7909477debbd935efc568fe1885475a7704a855ade9ab17e`؛ 105120 صفاً، و74873 شمعة سوق.

## المدخلات والمخرجات لكل متغير

كل الصفوف الخام مستقلة في هذه السجلات لأن معرفات الكائنات لم تتكرر داخل النوع والمتغير. بقي فصل العددين ظاهراً ولم يفترض عموماً لسجل آخر.

| المتغير | الصفوف | بصمة التنبؤات | بصمة القرارات | بصمة النتائج | بايتات النتائج |
|---|---:|---|---|---|---:|
| `R00` | 64013 | `cc778c815782297fab205c279c0c92872a326c96bb9e03d9c6dc04ff73f02fcb` | `6dfc164cd92b8ccbbe857b602bdef3c53c4a17f2d50fe657d886bbb9b1571bae` | `09b3f49256cce652245e1e75382e6bf25e501e94e59d76486027eadb5393890b` | 41176615 |
| `V01` | 64238 | `7cbe8736b879cbf861522243b8976fa4f2e50abed23914fcb9419d3be02f21b7` | `b9fe8ebb9256f33fc7d792f394b602b9aaa4186c4b822bef173f16fec7bc03b1` | `80cbc91c8e0c13d1127170fbe7cb31b8d9b7e7f5066345922a4095351212abf1` | 41316377 |
| `V02` | 64033 | `577ec498ab39edde391ecdddaef4683f717775e69c14aef89c6024c1c038a180` | `dcd9f0167d30ec2c2f08e0d10ea4521568b62b3d0c7cf84bdc66dc6dee65a64c` | `c426a48b4cb7794bb947be92f2838de91eaa26e932068a559282ba7c205250da` | 41174632 |
| `V03` | 63933 | `2e297c09b696f09e104ac0588420f3eceaf93332498735bc853de4129112e184` | `49317478d4a2553a3541411a45141bf813af4cd1a75fbbc7e190a261be976dc8` | `6f891c904f27216306eac4c311b84f290176f3eb3694c20f5c4dcc309ffeb6a1` | 41117432 |
| `V04` | 64025 | `4c8f9cf1f5af9c51e65d314e10a05aa672b196d07085723738f2cbb37c950762` | `6f5576174b6d72e17138cddd3e07aabd8400aaa76659eb21f3c9da872cbc07a6` | `a849d650edc056dc9cc2e78bc86ed42d8c120056ddbf85eca2a799b79de943d1` | 41189295 |
| `V05` | 63940 | `2292d46fa4e045075a3c749a1cf0788c48fbfa4beeb70e116a0fa4ea1382dfeb` | `5e55122b297b9fcc95e2a5b806b3ec3d19ccb5998dd48d8fb77b8e1313eca5e2` | `286bd4b3e17b0d79d80ec4183fdb5100f31452b9c553acf6f4085ed31063de96` | 41122650 |

## الملخص والسرد

- ملخص النتائج: 814567 بايت؛ بصمته `62d1cd04c976d627e3dc0b57d2a859ffdc19d3b0095fe1f5b97ef5f718304917`.
- سرد المرجع العربي: 312583 حدثاً، 93915552 بايت؛ بصمته `bf071927de61a5e974a972c04b20546db21d1cdbb8e34bf4fe9ba2e49ff8b8cf`.
- بصمات قرارات المتغيرات الستة واردة في الجدول السابق. بصمتا سرد المرجع وقراراته تختلفان عن بيان المرحلة الثانية بسبب تصحيح العرض العربي الموثق فقط؛ بصمات التنبؤات الستة لم تتغير.

## التقارير المودعة

| الملف | البايتات | البصمة |
|---|---:|---|
| `M3_DEV_REPORT.md` | 23322 | `21b0cd462899d3a2e10717b727a29141617db5aac45d15b3590f253ac6312f12` |
| `M3_MONTHLY_REPORT.md` | 105149 | `4fbc300a5d97124623d479ea9ae04ff792c179ae7bad59bf9d5ef96bd0828c65` |
| `M3_NARRATION_EXAMPLES.md` | 36699 | `4b06a8d69ed58acc7633b8773581e987a86addb4a6b05fcc83293855897e0ad4` |
| `K3_CONCEPT_COVERAGE.md` | 12578 | `35aea7f7b2e8c3b6cdfb27baca0f23aa22a016b08986b794c57fbaa3f3b680c6` |
| `NARRATION_SAMPLE_SPEC.md` | 2954 | `e92b9255e38b5269fd0c48fe9c19fc7349fd5aa67eef4efd41c03ecb2124181d` |
| `PREDICTION_SPEC.md` | 14011 | `9f80dc150c5245f3a59284ee33a35d37dbccd0148ebc27bdca84dae19f9f6dd8` |
| `VARIANT_PLAN.md` | 5043 | `de31380352e0d9fc930c56bff8851ae1e418ba8ad370c7b638a31f78dfa331db` |

## التحقق وإعادة التوليد

أعيد التسجيل بالشيفرة والمسارات نفسها بعد التشغيل الأول. تطابق ملف الملخص وملفات النتائج الستة بايتاً ببايت. كما أعيد تشغيل خط الأساس بمراجعة مستقلة لكل 384,182 صفاً، وطابقت توقعاته وصحته والاستقلال وأزمنة الحل. وتطابقت مجاميع الأشهر مع السنوي، وأعداد القرارات مع الإصدار.

قبل أول تسجيل نجحت اختبارات الحزمة 110 مع 6 اختيارية متخطاة، ومجموعة المشروع 1,943 مع التخطيات نفسها و24 تحذيراً سابقاً. الاختبارات المتخطاة تطلب ملفي عامين معاً، ولم يجلب ملف 2023 التزاماً بنطاق المرحلة.

أمر إعادة التسجيل:

```bash
PYTHONPATH=project/trading_project/src /home/user/.venv/ict-engine/bin/python -m trading_system.ict_engine.score_ledger \
  --input /home/user/ict_engine_data/2022.csv.gz \
  --ledger-root /home/user/ict_engine_data \
  --output-dir /home/user/ict_engine_data/m3 \
  --scoring-commit aa2e7b019e62c44897e6f763739407830ea2256e \
  --prediction-spec-commit d07049d21d41bef031034c5f82975569bfdf27fa \
  --variant-plan-commit f8db96eab9c353b572dd41eb845d184f6e6174f7
```

أمر توليد التقارير:

```bash
PYTHONPATH=project/trading_project/src /home/user/.venv/ict-engine/bin/python -m trading_system.ict_engine.m3_report \
  --scores /home/user/ict_engine_data/m3/m3_scores.json \
  --ledger-root /home/user/ict_engine_data \
  --narration /home/user/ict_engine_data/m2_R00_narration.jsonl \
  --output-dir project/trading_project/docs/research/huddleston_study/engine_v1 \
  --sample-spec-commit d07049d21d41bef031034c5f82975569bfdf27fa
```

لم يتغير معرف أو شرط نتيجة أو أفق أو خط أساس أو متغير بعد أول ظهور للنتائج. توقف العمل بعد المرحلة الثالثة، ولم تبدأ المرحلة الرابعة.

بصمة الملف المحمي `72b03ca6d2333080e0df6dc18b1928147e877b41175f132c7bf08eb4e4d74ace` وحجمه 12,216 بايت، بلا تغيير.
