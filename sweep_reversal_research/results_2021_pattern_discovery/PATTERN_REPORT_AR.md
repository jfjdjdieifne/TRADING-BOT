# Pattern discovery — XAUUSD وNSXUSD وBTCUSD — 2021

> هذا تحليل وصفي على outcomes أُغلقت بعد الإشارة. لا يستخدم نتيجة مستقبلية لصناعة signal، لكنه لا يحوّل اختيار pattern من نفس السنة إلى إثبات out-of-sample.

## العقد

- active causal profile: sweep + displacement `S+1` الصحيح + أول target سابق؛ FVG وP80 غير مطلوبين لزيادة العينة.
- الجلسات كلها UTC: Asia `00-07`، London `07-13`، New York `13-20`، Late `20-24`.
- XAUUSD وNSXUSD يستخدمان مصدر 1m؛ BTCUSD يستخدم مصدره الأصلي 5m، وتُبنى منه شمعة setup 15m من ثلاث شموع 5m مكتملة. لذلك BTC ليس مقارنة tick-for-tick مع 1m.
- كل صف في `candidate_outcomes.csv` هو outcome مستقل مرشح؛ أرقام الحساب ذي الصفقة الواحدة موجودة في تقرير holdout.
- `breakdown_summary.csv` يخرج n وwin rate وtotal/mean R وprofit factor وmax drawdown R حسب الشهر والأسبوع واليوم واليوم الأسبوعي والجلسة والساعة والاتجاه.
- لكل أصل يوجد prefix audit في `summary.json`؛ لا يكفي أن يكون الحساب causal على XAU فقط.

## الأنماط ذات الاستقرار النسبي بين نصفي السنة

| الأصل | الاتجاه | الجلسة | H1 n | H1 sum R | H1 PF | H1 DD R | H2 n | H2 sum R | H2 PF | H2 DD R | FULL n | FULL sum R | FULL PF | FULL DD R |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| XAUUSD | SHORT | LONDON_07_13 | 109 | 18.6363 | 1.462969 | 5.3188 | 140 | 10.8181 | 1.165493 | 17.3136 | 249 | 29.4544 | 1.278863 | 17.3136 |
| XAUUSD | LONG | NY_13_20 | 75 | 6.3088 | 1.267141 | 6.6556 | 54 | 13.4498 | 1.89702 | 4.8393 | 129 | 19.7586 | 1.511749 | 6.6556 |
| NSXUSD | SHORT | LONDON_07_13 | 181 | -15.0127 | 0.813581 | 27.5425 | 173 | -8.4319 | 0.889827 | 17.7052 | 354 | -23.4445 | 0.850734 | 33.2498 |
| BTCUSD | SHORT | LONDON_07_13 | 270 | 8.4218 | 1.070943 | 16.6657 | 271 | -3.6644 | 0.962271 | 13.7184 | 541 | 4.7574 | 1.022042 | 27.6906 |
| BTCUSD | LONG | NY_13_20 | 0 | 0.0000 | None | 0.0000 | 0 | 0.0000 | None | 0.0000 | 0 | 0.0000 | None | 0.0000 |
| XAUUSD | LONG | LATE_20_24 | 27 | -12.0354 | 0.187928 | 12.4142 | 15 | -5.1899 | 0.13877 | 5.2121 | 42 | -17.2253 | 0.173718 | 17.6041 |

## القراءة

- XAUUSD SHORT في London وLONG في New York كانا موجبين في H1 وH2 داخل هذه العينة، ولذلك استُخدما كفرضية `run_2021_session_profile.py` لا كـ edge مثبت.
- الجدول يقارن BTCUSD أيضاً، لكن اختلاف المصدر 5m مقابل 1m يفرض قراءة BTC كاختبار cadence مستقل، لا كترتيب مباشر بين الأصول.
- NSXUSD London وXAUUSD LONG في Late ظهرا سالبين في النصفين؛ لم أضفهما إلى profile الرابح.
- هذه ليست ضماناً أن السوق يكرر النمط مستقبلاً؛ تقرير `results_session_oos/` يختبر الفرضية المجمدة على 2022-2025.
- prefix audits لكل الأصول الثلاثة يجب أن تكون 11/11؛ هذا يثبت replay السببي، لا يثبت pattern edge.

## الملفات

- `candidate_outcomes.csv`: كل outcome مؤهل مع الأصل والاتجاه والجلسة والساعة واليوم.
- `pattern_summary.csv`: تجميع FULL/H1/H2 والجلسة واليوم للأصل والاتجاه.
- `breakdown_summary.csv`: جداول الشهر/الأسبوع/اليوم/weekday/session/hour/side مع PF وDD.
- `data_hashes.txt`: بصمات ملفات XAU وNSX وBTC المقروءة.
