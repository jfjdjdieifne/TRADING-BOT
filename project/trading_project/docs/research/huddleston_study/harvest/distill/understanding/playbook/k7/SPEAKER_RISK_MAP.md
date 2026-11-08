# خريطة خطر الأصوات الأخرى — K7 المرحلة صفر

## المشكلة

ملفات الترجمة **بلا أي وسم للمتحدث**. لذلك لا يجوز أن ننسب جملة إلى Michael إلا إذا كان النص نفسه
يُظهر ذلك. هذه الخريطة لا تحكم على أي جملة؛ إنها تعدّ علامات مرئية في النص لتعرف القراءة أين
يجب أن تتوقع سؤالاً أو صوتاً آخر، وأين تسجّل `UNKNOWN`.

## العلامات المعدودة (بحث حرفي بعد N-06)

- `CHAT_OR_COMMENTS`: ذكر الدردشة أو التعليقات أو سؤال من أحد («in the chat»، «someone asked»، «you asked»).
- `AUDIENCE_QUESTION`: مخاطبة الحاضرين بسؤال («does that make sense»، «any questions»، «are you with me»).
- `THANKS_TO_HIM`: شكر موجّه إليه («thank you Michael»، «appreciate it»).
- `LIVE_MARKER`: افتتاحيات البث («welcome back»، «hello everyone»، «we are live»).
- `SECOND_VOICE`: إشارة إلى كلام شخص آخر («he asked»، «the question was»، «your question»).

قيد مهم: الترجمة الآلية بلا علامات ترقيم، فلا توجد علامة استفهام يمكن عدّها؛ لذلك كل العدّ لفظي.
قيد ثانٍ: عبارات الشكر قد تصدر منه هو تجاه المشاهدين، لا منهم تجاهه؛ فعدّها **إشارة لا دليل**،
وهي ترفع الحذر فقط ولا تنسب كلاماً لأحد.

## قواعد التصنيف (أُعلنت قبل التشغيل)

- **HIGH**: نسبة الملفات التي فيها ذكر دردشة/تعليقات ≥ 50%، أو نسبة ملفات الشكر الموجّه إليه ≥ 30%.
- **MEDIUM**: ≥ 20% للدردشة، أو ≥ 10% للشكر، أو ≥ 90% من الملفات فيها أي علامة.
- **LOW_MEDIUM**: ≥ 50% من الملفات فيها أي علامة. **LOW**: أقل من ذلك لكن أكبر من صفر.
- **UNKNOWN_NO_CUE**: لا علامة واحدة. هذا `UNKNOWN` وليس «Michael وحده» بنفي قاطع.

## الجدول

| المجلد | الخطر | نسبة الملفات ذات أي علامة | ملفات فيها دردشة/أسئلة | ملفات فيها شكر له | المجموع |
|---|---|---:|---:|---:|---:|
| `2017-ICT-Private-Mentorship-Core-Content-Month-09` | MEDIUM | 1.000 | 0/8 | 0/8 | 8 |
| `2017-ICT-Private-Mentorship-Core-Content-Month-11` | MEDIUM | 1.000 | 0/4 | 0/4 | 4 |
| `2023-Forex-Reviews` | MEDIUM | 1.000 | 0/1 | 0/1 | 1 |
| `Emini-Market-Reviews` | MEDIUM | 1.000 | 0/3 | 0/3 | 3 |
| `ICT-Mastering-High-Probability-Scalping-Volumes-1-3` | HIGH | 1.000 | 0/3 | 1/3 | 3 |
| `ICT-Micro-Market-Structure-&-Time-&-Price-Concepts-Series` | MEDIUM | 1.000 | 0/2 | 0/2 | 2 |
| `2022-ICT-Mentorship` | MEDIUM | 0.900 | 20/50 | 3/50 | 50 |
| `2017-ICT-Private-Mentorship-Core-Content-Month-10` | LOW_MEDIUM | 0.895 | 0/19 | 1/19 | 19 |
| `2016-ICT-Private-Mentorship-Core-Content-Month-03` | LOW_MEDIUM | 0.875 | 0/8 | 0/8 | 8 |
| `2017-ICT-Private-Mentorship-Core-Content-Month-08` | LOW_MEDIUM | 0.875 | 0/8 | 0/8 | 8 |
| `2017-ICT-Private-Mentorship-Core-Content-Month-05` | LOW_MEDIUM | 0.850 | 0/20 | 1/20 | 20 |
| `ICT-Forex-Market-Maker-Primer-Course` | LOW_MEDIUM | 0.833 | 0/24 | 0/24 | 24 |
| `ICT-Charter-Content` | LOW_MEDIUM | 0.800 | 2/35 | 3/35 | 35 |
| `ICT-Market-Maker-Forex-Series` | LOW_MEDIUM | 0.800 | 0/5 | 0/5 | 5 |
| `ICT-OTE-Pattern-Recognition-Series` | LOW_MEDIUM | 0.800 | 1/20 | 1/20 | 20 |
| `Real-Money-Real-People-Series` | HIGH | 0.800 | 1/5 | 3/5 | 5 |
| `2016-ICT-Private-Mentorship-Core-Content-Month-02` | LOW_MEDIUM | 0.778 | 0/9 | 0/9 | 9 |
| `If-I-Could-Go-Back-&-Tell-Myself-What-I-Know-Now` | MEDIUM | 0.750 | 0/4 | 1/4 | 4 |
| `Real-Money-Real-Results-First-Year-Trading-Expectations` | HIGH | 0.750 | 2/4 | 0/4 | 4 |
| `2016-ICT-Private-Mentorship-Core-Content-Month-04` | LOW_MEDIUM | 0.643 | 0/14 | 0/14 | 14 |
| `2017-ICT-Private-Mentorship-Core-Content-Month-06` | LOW_MEDIUM | 0.625 | 0/8 | 0/8 | 8 |
| `Ends-Series` | LOW_MEDIUM | 0.600 | 0/5 | 0/5 | 5 |
| `2023-ICT-Mentorship` | LOW_MEDIUM | 0.589 | 20/151 | 15/151 | 151 |
| `Live-Streams` | MEDIUM | 0.571 | 1/7 | 2/7 | 7 |
| `2016-ICT-Private-Mentorship-Core-Content-Month-01` | MEDIUM | 0.556 | 0/9 | 1/9 | 9 |
| `ICT-Forex-Trading-Plan-Development-Series` | LOW_MEDIUM | 0.500 | 0/10 | 0/10 | 10 |
| `ICT-Pattern-Recognition-Optimal-Trade-Entry` | LOW_MEDIUM | 0.500 | 0/2 | 0/2 | 2 |
| `ICT-Forex-What-Every-New-&-Or-Aspiring-Forex-Traders-Wants-To-Know` | LOW | 0.455 | 0/11 | 1/11 | 11 |
| `ICT-Trade-Executions` | HIGH | 0.444 | 2/9 | 3/9 | 9 |
| `2017-ICT-Private-Mentorship-Core-Content-Month-12` | LOW | 0.400 | 0/5 | 0/5 | 5 |
| `2017-ICT-Private-Mentorship-Core-Content-Month-07` | LOW | 0.375 | 0/8 | 0/8 | 8 |
| `ICT-Forex-Scout-Sniper-Basic-Field-Guide-Series` | LOW | 0.267 | 0/15 | 0/15 | 15 |
| `ICT-Forex-Precision-Trading-Concepts-Series` | UNKNOWN_NO_CUE | 0.000 | 0/4 | 0/4 | 4 |

## ما تفعله القراءة بهذه الخريطة

- في مجلد HIGH/MEDIUM: كل جملة تُوسم `UNKNOWN` افتراضياً، ولا تصبح Tier1 إلا إذا كان النص نفسه
  يدل على أنه هو المتكلم (ضمير المتكلم مع تعليم مباشر، أو «my»).
- في مجلد LOW/UNKNOWN_NO_CUE: يبقى الوسم `UNKNOWN` أيضاً؛ الخريطة تخفّض الاحتمال ولا تثبت المتحدث.

## أرقام

توزيع المجلدات: HIGH = 4، LOW = 4، LOW_MEDIUM = 15، MEDIUM = 9، UNKNOWN_NO_CUE = 1.
