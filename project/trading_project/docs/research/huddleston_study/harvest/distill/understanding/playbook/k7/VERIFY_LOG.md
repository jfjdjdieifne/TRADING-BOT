# سجل التحقق الآلي — K7 المرحلة صفر

## كيف يشتغل

`scripts/k7_verify.py` سكربت حتمي واحد. يُشغَّل على مخرجات المرحلة نفسها، ويطبع لكل فحص
نتيجة `PASS` أو `FAIL` مع الأرقام، وينتهي برمز غير صفري عند أي فشل. لا يوجد «تحقق» بلغة الوصف.

## الأمر الذي شُغّل

```
python3 scripts/k7_verify.py --repo . --work /home/user/k7_work \
    --corpus /home/user/k7_work/corpus_dl/ict-index-e8c40a8dae5ea6689926f28c7184ce3e2fb85b9c \
    --refs-dir /home/user/k7_work/refs
```

## المخرجات كما هي

```
[PASS] V01_FILE_IDS: 490 ids, sequence ok=True, path order ok=True
[PASS] V02_CHUNK_IDS: 2440 chunks, unique=True, format_ok=True, files_covered=490/490
[PASS] V03_CHUNK_RANGES: non-contiguous=0 not-covering=0 joined_chars=13172497
[PASS] V04_CHUNK_WORDS: mismatch=0 []
[PASS] V05_CHUNK_OFFSETS: out-of-file-range offsets=0
[PASS] V06_BATCHES: 97 batches, chunks_in_full=2440 (sum must equal 2440) -> True
[PASS] V07_DUP_ENDPOINTS: bad endpoints=0 records=82
[PASS] V08_QUOTES: 33/33 quotes verified verbatim, <= 25 words; bad=[]
[PASS] V09_CORPUS_IDENTITY: 253/253 earlier-recorded sha256 values agree with the extracted corpus
[PASS] V10_NO_BULK_TEXT: files scanned=18, long corpus-matching passages=0 []
[PASS] V11_TIMELINE: 490/490 files

RESULT: 11/11 checks passed
```

## معنى كل فحص

| الفحص | ما يثبته |
|---|---|
| V01 | معرّفات الملفات `F0001..F0490` متتابعة، بلا تكرار، ومرتبة بترتيب المسار |
| V02 | معرّفات المقاطع فريدة وصحيحة الشكل، وكل ملف له مقطع واحد على الأقل |
| V03 | حدود الحروف متصلة بلا تراكب، وتغطي النص الموصول كله، والفاصل حرف مسافة واحد فقط |
| V04 | مجموع كلمات مقاطع الملف يساوي عدد كلمات الملف بالضبط |
| V05 | مواضع الزمن داخل نطاق الملف نفسه |
| V06 | الدفعات تغطي كل المقاطع مرة واحدة، بلا فقد ولا تكرار |
| V07 | كل طرف في خريطة التكرار ملف موجود فعلاً |
| V08 | كل اقتباس في مخرجات المرحلة موجود حرفياً في المدونة، ≤ 25 كلمة، وبالموضع المسجّل |
| V09 | بصمات المدونة تطابق بصمات سجّلتها K1 وK3 وU2 لنفس المسارات (253/253) — أي أنها المدونة نفسها |
| V10 | لا نص متصل من 40 كلمة موجود في المستودع يطابق نص ترجمة: أي لا تسريب للنص إلى المستودع العام |
| V11 | كل ملف له سجل زمني، ولو كان `DATE_UNKNOWN` |

## ما لا يثبته التحقق

الاقتباس يثبت **وجود** النص وموضعه، ولا يثبت أن قراءتنا له صحيحة ولا أن قائله Michael.
لذلك في المرحلة الأولى تدقيق مستقل: عينة 10% من كل دفعة تُعاد قراءتها بلا رؤية الوسوم الأولى
(البذرة `seed=20261108`)، ويُنشر اتفاق الحقول وكل خلاف. وفي المرحلة الثانية يُعاد التحقق من
طرفي كل رابط موثّق.
