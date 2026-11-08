# خريطة المجلدات — K7 المرحلة صفر

## ما هذه الوثيقة

هذه خريطة عدّ فقط: لكل مجلد أعلى في `transcriptions/` عدد الملفات والكلمات والمقاطع،
وعدد الاقتباسات الموجودة في السجلات السابقة التي تشير إلى ملف من ذلك المجلد.
لا توجد هنا أي خلاصة محتوى ولا أي ادعاء جديد عن السوق.

- المجموع: 490 ملف، 2٬672٬759 كلمة (حسب N-05)، 395٬966 مقطع ترجمة، 2٬440 مقطع قراءة (chunk).
- الكلمات بطريقة `split()` = 2٬540٬731 (للمصالحة مع رقم الإحاطة 2,549,198).

## كيف عُدَّت الاقتباسات

الاقتباس المعدود هو سجل فيه حقل نصي اسمه `quote` غير فارغ **و**مسار ملف ترجمة يمكن عزله
(`path` أو `transcript_id` أو `file` أو `source_label`/`source_labels`).
ثم تُزال التكرارات: السجل نفسه (المسار + نص الاقتباس) يُعدّ مرة واحدة فقط، لأن
مجلدات `u2-all` و`u3-k3` منسوخة حرفياً في أكثر من مرجع. المجموع الفريد = 3٬721 اقتباساً، والمسارات غير المحلولة = 0.

**الاقتباسات قبل إزالة التكرار، لكل مرجع** (النسخ المكررة بين المراجع ظاهرة هنا):

- K1: 228
- K2: 3٬400
- K3: 266
- U2: 3٬154
- K4a: 266
- K4b: 337
- K5: 288
- DESIGN: 3٬246

**صيغ سجلات لا تحمل مسار ملف ترجمة** (فيُستثنى اقتباسها من العدّ، وهذا مذكور صراحة كما طُلب):
- `source_corpus_v3/claims.jsonl`: 54 اقتباساً بلا أي مسار ترجمة داخل السجل (فيه `source_id` فقط).
- `distill/knowledge_pack*.jsonl`: لا يحوي حقل `quote` إطلاقاً (فيه `essence` و`source_labels`)، فلم يُعدّ.
- `playbook/k4b/traces.jsonl`: 13 سجلاً بلا نص اقتباس.
- `playbook/k5/claims.jsonl`: 16 اقتباساً لمصادر خارجية (مصادر ويب/مؤلفين) لا تشير إلى ملف في هذه المدونة.

## الجدول

| المجلد | ملفات | كلمات | مقاطع ترجمة | مقاطع قراءة | اقتباسات فريدة تشير إليه | الحالة |
|---|---:|---:|---:|---:|---:|---|
| `2016-ICT-Private-Mentorship-Core-Content-Month-01` | 9 | 37٬327 | 6٬099 | 35 | 249 | CITED |
| `2016-ICT-Private-Mentorship-Core-Content-Month-02` | 9 | 36٬481 | 5٬747 | 33 | 191 | CITED |
| `2016-ICT-Private-Mentorship-Core-Content-Month-03` | 8 | 36٬588 | 5٬980 | 35 | 199 | CITED |
| `2016-ICT-Private-Mentorship-Core-Content-Month-04` | 14 | 41٬763 | 6٬826 | 38 | 262 | CITED |
| `2017-ICT-Private-Mentorship-Core-Content-Month-05` | 20 | 94٬695 | 14٬805 | 89 | 449 | CITED |
| `2017-ICT-Private-Mentorship-Core-Content-Month-06` | 8 | 41٬114 | 6٬479 | 38 | 268 | CITED |
| `2017-ICT-Private-Mentorship-Core-Content-Month-07` | 8 | 38٬024 | 5٬704 | 36 | 171 | CITED |
| `2017-ICT-Private-Mentorship-Core-Content-Month-08` | 8 | 36٬703 | 5٬388 | 35 | 235 | CITED |
| `2017-ICT-Private-Mentorship-Core-Content-Month-09` | 8 | 40٬682 | 6٬036 | 37 | 218 | CITED |
| `2017-ICT-Private-Mentorship-Core-Content-Month-10` | 19 | 71٬640 | 10٬871 | 67 | 334 | CITED |
| `2017-ICT-Private-Mentorship-Core-Content-Month-11` | 4 | 25٬543 | 3٬875 | 24 | 204 | CITED |
| `2017-ICT-Private-Mentorship-Core-Content-Month-12` | 5 | 36٬796 | 5٬268 | 34 | 261 | CITED |
| `2022-ICT-Mentorship` | 50 | 256٬267 | 42٬585 | 234 | 311 | CITED |
| `2023-Forex-Reviews` | 1 | 1٬372 | 206 | 2 | 5 | CITED |
| `2023-ICT-Mentorship` | 151 | 968٬065 | 143٬396 | 881 | 147 | CITED |
| `Emini-Market-Reviews` | 3 | 7٬731 | 1٬251 | 7 | 5 | CITED |
| `Ends-Series` | 5 | 31٬624 | 5٬245 | 28 | 21 | CITED |
| `ICT-Charter-Content` | 35 | 220٬712 | 30٬843 | 195 | 61 | CITED |
| `ICT-Forex-Market-Maker-Primer-Course` | 24 | 99٬735 | 13٬255 | 91 | 30 | CITED |
| `ICT-Forex-Precision-Trading-Concepts-Series` | 4 | 24٬841 | 3٬289 | 22 | 2 | CITED |
| `ICT-Forex-Scout-Sniper-Basic-Field-Guide-Series` | 15 | 115٬138 | 15٬363 | 103 | 4 | CITED |
| `ICT-Forex-Trading-Plan-Development-Series` | 10 | 63٬733 | 8٬715 | 57 | 8 | CITED |
| `ICT-Forex-What-Every-New-&-Or-Aspiring-Forex-Traders-Wants-To-Know` | 11 | 92٬968 | 12٬268 | 84 | 5 | CITED |
| `ICT-Market-Maker-Forex-Series` | 5 | 25٬395 | 4٬304 | 23 | 5 | CITED |
| `ICT-Mastering-High-Probability-Scalping-Volumes-1-3` | 3 | 15٬341 | 1٬994 | 14 | 3 | CITED |
| `ICT-Micro-Market-Structure-&-Time-&-Price-Concepts-Series` | 2 | 7٬296 | 1٬206 | 7 | 7 | CITED |
| `ICT-OTE-Pattern-Recognition-Series` | 20 | 27٬583 | 3٬640 | 33 | 14 | CITED |
| `ICT-Pattern-Recognition-Optimal-Trade-Entry` | 2 | 1٬378 | 186 | 2 | 4 | CITED |
| `ICT-Trade-Executions` | 9 | 45٬051 | 6٬140 | 41 | 8 | CITED |
| `If-I-Could-Go-Back-&-Tell-Myself-What-I-Know-Now` | 4 | 25٬095 | 3٬719 | 22 | 13 | CITED |
| `Live-Streams` | 7 | 51٬720 | 7٬337 | 45 | 25 | CITED |
| `Real-Money-Real-People-Series` | 5 | 39٬752 | 5٬469 | 35 | 0 | NEVER_CITED |
| `Real-Money-Real-Results-First-Year-Trading-Expectations` | 4 | 14٬606 | 2٬477 | 13 | 2 | CITED |
| **المجموع** | **490** | **2٬672٬759** | **395٬966** | **2٬440** | **3٬721** | |

## مجلدات لم يُقتبس منها أحد: 1

- `Real-Money-Real-People-Series` — 5 ملفات، 39٬752 كلمة، 35 مقطع قراءة.

## ملاحظة عدّ

عدد الاقتباسات أعلاه يقيس **ما استُشهد به في السجلات السابقة فقط**. صفر لا يعني أن المجلد
بلا قيمة، ويعني حرفياً أن أحداً لم يقتبس منه في K1..K5. المرحلة الأولى ستقرأ كل المجلدات بلا استثناء.
