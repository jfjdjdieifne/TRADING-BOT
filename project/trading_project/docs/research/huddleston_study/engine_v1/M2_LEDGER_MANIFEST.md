# بيان سجلات المرحلة الثانية وبصماتها

## مكان الملفات وسبب عدم إيداعها

كتبت الملفات خارج المستودع في `/home/user/ict_engine_data/` لأن حجمها كبير وهي مخرجات قابلة لإعادة التوليد، وليست مصدراً أو معرفة جديدة. لا توجد نتيجة أو معدل إصابة في أي ملف منها.

مصدر الإدخال هو `2022.csv.gz` ببصمة `490d4fb9f1a07a1d7909477debbd935efc568fe1885475a7704a855ade9ab17e`. جميع السجلات تستخدم الإصدار `m2-v1` وأفق 288 شمعة سوق.

## سجلات التنبؤ الستة

| المتغير | اسم الملف | الصفوف | البايتات | بصمة SHA-256 |
|---|---|---:|---:|---|
| `R00` | `m2_R00_predictions.jsonl` | 64,013 | 58,318,575 | `cc778c815782297fab205c279c0c92872a326c96bb9e03d9c6dc04ff73f02fcb` |
| `V01` | `m2_V01_predictions.jsonl` | 64,238 | 58,522,111 | `7cbe8736b879cbf861522243b8976fa4f2e50abed23914fcb9419d3be02f21b7` |
| `V02` | `m2_V02_predictions.jsonl` | 64,033 | 58,301,861 | `577ec498ab39edde391ecdddaef4683f717775e69c14aef89c6024c1c038a180` |
| `V03` | `m2_V03_predictions.jsonl` | 63,933 | 58,207,544 | `2e297c09b696f09e104ac0588420f3eceaf93332498735bc853de4129112e184` |
| `V04` | `m2_V04_predictions.jsonl` | 64,025 | 58,337,780 | `4c8f9cf1f5af9c51e65d314e10a05aa672b196d07085723738f2cbb37c950762` |
| `V05` | `m2_V05_predictions.jsonl` | 63,940 | 58,218,163 | `2292d46fa4e045075a3c749a1cf0788c48fbfa4beeb70e116a0fa4ea1382dfeb` |

## سرد المرجع وقراراته

| الملف | الصفوف | البايتات | بصمة SHA-256 |
|---|---:|---:|---|
| `m2_R00_narration.jsonl` | 312,583 | 93,810,840 | `e9ddd4e758ad7c941bbcf364f21d387d138bdf4111472cefd82e098cb8ce1f57` |
| `m2_R00_decisions.jsonl` | 70,071 | 31,798,255 | `472fa21f4041dfba00bd3e27eca8c88b9172e786c5ede45a410af98678397adf` |

## إعادة التوليد والتحقق

مثال إعادة إصدار المرجع من جذر المستودع:

```bash
PYTHONPATH=project/trading_project/src python -m trading_system.ict_engine.pass1_emit --input /home/user/ict_engine_data/2022.csv.gz --variant R00 --predictions /home/user/ict_engine_data/m2_R00_predictions.jsonl --narration /home/user/ict_engine_data/m2_R00_narration.jsonl --decisions /home/user/ict_engine_data/m2_R00_decisions.jsonl
```

يستبدل اسم المتغير ومسارات المخرجات لبقية التشغيلات الخمسة. عند اختفاء الملفات المؤقتة يجب على المرحلة الثالثة إعادة توليدها بالشيفرة الملتزم بها والتحقق من البصمات قبل قراءة أي نتيجة.

تحقق ثانٍ مستقل من المرجع أنتج الملف نفسه بايتاً ببايت. كما تطابقت مخرجات المقدمات الحقيقية عند أطوال 0 و1 و2 و6 و100 و1000 و5000 مع بداية التشغيل الكامل. لم يولد أي سجل تنبؤ من 2023، ولم يستخدم ملف 2024.
