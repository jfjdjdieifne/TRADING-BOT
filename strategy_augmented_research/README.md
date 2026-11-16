# نسخة البحث المستقلة للاستراتيجية الأصلية V5

هذه المساحة منفصلة عن `smc_v4_multisleeve_package/`.

- `original_v5/`: نسخة byte-for-byte من محرك V5 الذي أعاد إنتاج نتيجة `+546.5%` عند محاكاة حساب `$100` بمخاطرة مركبة `1%` لكل صفقة.
- `augmented_v5/`: طبقات بحث سببية قابلة للتدقيق، مع تعريفات تشغيلية معلنة للمصطلحات التي لم يكن لها عقد رسمي في الأصل.
- `baseline_outputs/`: إعادة تشغيل مستقلة للنسخة المنسوخة، وصفقات baseline.
- `variant_outputs/`: نتائج كل طبقة منفردة والتركيبات المعلنة، وسجل القرار والميزات.
- `COPY_AND_DATA_HASHES.sha256`: إثبات الهاش للملفات الأصلية والمنسوخة ومانيفست البيانات.
- `BASELINE_STRATEGY_AR.md`: الشرح العربي التفصيلي، القيود، النتائج، والتفسير.

## إعادة التشغيل

```bash
python3 -m venv .venv
.venv/bin/pip install -r ../smc_v4_multisleeve_package/requirements.txt
.venv/bin/python run_original_clone.py
.venv/bin/python run_augmented_experiments.py
PYTHONPATH=original_v5:augmented_v5 .venv/bin/pytest -q tests/test_causal_layers.py ../smc_v4_multisleeve_package/tests/test_v4_zero_lookahead.py
```

قد تختلف مدة التشغيل حسب الجهاز؛ إعادة baseline الحالية استغرقت نحو دقيقة، وتجربة الطبقات نحو أربع دقائق في بيئة Arena.

## نطاق النسخة المعززة

النسخة الحالية تطبق الطبقات كـ **بوابة بعد الإشارة** على مجموعة إشارات V5 المقبولة وعددها 645. أي أنها تستطيع حذف صفقة baseline، ولا تضيف فرصة لم يولدها V5. هذا مقصود في المرحلة الأولى لعزل أثر الفلتر ومنع خلط تحسين مولّد الإشارة مع تحسين إدارة الصفقة. لذلك لا تُسمى النتائج profile حيّاً، ولا تثبت أن الطبقة تحسن كل الفرص الممكنة.
