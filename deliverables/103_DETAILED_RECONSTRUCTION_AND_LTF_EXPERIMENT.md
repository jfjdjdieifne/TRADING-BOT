> **⚠️ لاحقة تحقق (2026-11-05):** الأرقام في هذا التقرير أُنتجت **قبل إصلاح التنفيذ السببي `next_open`**، و**تعذّرت إعادة إنتاجها** (لا توجد بيانات EUR/USD 5m في مساحة العمل)، و**تعارض عدد الصفقات بين التقرير 102 والتقرير 103 ما زال غير محلول**. الأرقام تُركت كما سُجّلت دون أي تعديل؛ تُعامل كغير مُتحقَّق منها.

---

# تقرير 103: إعادة بناء دقيقة وحل توقيت الدخول وتجربة إطار أدنى

> تحذير
>
> سجل بحث فقط
>
> لا أوامر حية
>
> لا ادعاء مطابقة مايكل

## تأصيل الشيفرة والفروع

المسار الحالي

```
arena/5eee9692-trading-bot
```

السجل

```
41ac2ea forex v101: direction fix + fill conventions + frozen eval (report 101)
265e801 docs: add handoff verification and direction diagnosis report (arena/5eee9692)
e0c2234 Update print statement from 'Hello' to 'Goodbye'
```

تأصيل 41ac2ea

```
parent 265e801 (same branch arena/5eee9692-trading-bot)
files from arena/a41fd997-trading-bot cherry-picked:
 run_forex_intraday_v1.py from 2b4d23e
 src/contextual_selection/*.py from same commit
 dev_model.json from same
```

حالة الشجرتين

```
worktree 5eee9692: active, contains fix, tests, deliverables 101+102+103
worktree a41fd997: separate remote branch, original baseline 2b4d23e preserved, not deleted, not merged
both preserved, no reset --hard, no silent merge
untracked 102 preserved
```

الملف المحمي

```
72b03ca6d2333080e0df6dc18b1928147e877b41175f132c7bf08eb4e4d74ace  information_time.py (unchanged)
```

الحلقة المحجوبة

```
tpPtItWqmlg untouched
```

## المهمة 1: إعادة بناء حالة فبراير فعلية

### المسار المعرف والطوابع

المسار

```
/tmp/forex-eval-fixed-original/cases_eval_v1.jsonl
/tmp/forex-eval-fixed-original/summary_eval_v1.json
/tmp/forex-test/data/EURUSD/5m_bidask/2025.csv.gz
```

المعرف

```
plan_id PLAN-fx-intraday-v1-0001
decision_id DEC-fx-intraday-v1-0037
analysis_id AN-e16d80db2780 v37
as_of 2025-02-04 11:00:00+00:00 UTC
```

الشيفرة

```
run_forex_intraday_v1.py: _intended_direction()
decision_layer.py: primary_interpretation_id, context direction
analysis_lifecycle.py: PTC:F-K(k=5)
connected_readings.py: FVG
monitoring.py: COMPLETED_ROW_AVAILABLE
```

### السياق والمرجع والسيناريو والفجوة والبوابة

السياق

```
direction down (leg_direction down)
```

المرجع

```
id PTC:F-K(k=5)|high@2025-02-04T00:00:00+00:00
level 1.03506
availability 2025-02-04 00:00 UTC
```

السيناريو

```
reversal up
entry SP-03 close beyond reference
invalidation SP-03 close beyond leg_end down
objective one F-K leg up
origin declared-research-configuration
```

الفجوة

```
at decision: none opposing intended
gate_reason fixed: do not contradict
later at 2025-02-06 10:00 FVG-1h-83 downward opposing up -> gate held
```

البوابة

```
fixed V1: pass (intended up not opposed)
legacy V1-legacy at same 2025-02-04 11:00:
 no-plan held due FVG-15m-141 upward opposing scenario down
```

### هل 11:00 محجوبة بالقديم ولماذا

```
legacy: no-plan held (proven via /tmp/forex-eval-fixed-original/cases_eval_v1-legacy.jsonl)
fixed: plan-opened (proven via cases_eval_v1.jsonl)
why: legacy bug maps I-alt opposite incorrectly (ctx down -> legacy thought down, fixed thought up)
record exists, not inferred
if absent: UNKNOWN (not case here)
```

### المراجع والفجوات المنافسة

المراجع

```
selected: PTC:F-K high 1.03506
alternative highs not recorded
engine selects by fixed geometric conjunction only, no ranking
where recorded: only selected in plan levels
statement: no real comparison recorded
```

الفجوات

```
before decision: none EVIDENCE_PREFERRED
competitor: FVG-15m-141 upward range ~1.030-1.031 timeframe 15m availability ~10:45 role opposing for legacy
supporting: by_support_count
counterevidence: none
unknowns: Michael relevance
```

## المهمة 2: صفقة أبريل

المعرف

```
PLAN-fx-intraday-v1-0001 April
as_of 2025-04-02 04:00
artifact /tmp/forex-eval-fixed-new/cases_eval_v1.jsonl
```

الأسعار الخام

```
Feb entry bar 2025-02-04 15:00 BidOpen 1.03592 BidClose 1.03689 AskClose 1.03694
Feb next bar 15:05 BidClose 1.03608 AskOpen 1.03694
Feb exit 03:00 BidClose 1.03816
Apr entry 13:00 AskClose 1.08157
Apr exit 02:00 BidClose 1.0914
dataset /tmp/forex-test/data/EURUSD/5m_bidask/2025.csv.gz hash 1fa2dca2...
```

بداية ونهاية الشريط

```
5m bar start 13:00 end 13:05
decision availability COMPLETED_ROW_AVAILABLE after 1h bar 03:00-04:00
fill timestamps: close = entry_time, next-open = next bar open > entry_time
```

الحساب والتقريب

```
up pips = (exit_BidClose - entry_AskClose)*10000
Feb: (1.03816-1.03694)*10000=12.2
Apr: (1.0914-1.08157)*10000=98.3
round(pips,2) -> 12.2, 98.3
code outcome_for line 285-290
```

شرح 12.3 مقابل 12.2

```
report 99: 12.2+0.1=12.3 total (old same-side fill)
current: 12.2+0.1=12.3 total as well, but accounting note says per-trade vs per-plan
discrepancy 12.2 single is per first trade only, not total
spread fix: old used AskClose for both entry/exit, new uses Ask entry Bid exit (spread ~0.5 pip reduces second trade from 0.6 to 0.1)
```

## المهمة 3: تدقيق توقيت الدخول والخروج

المشكلة

```
decision at 11:00 cannot execute at same 15:00 close without delay
```

التدقيق

```
close convention assumes buy at close price before bar ends (optimistic)
next-open convention entry at next 5m open > entry_time is causal
implemented fill_price_next_open()
 gaps: next row after ts handles weekends
 ambiguity: same_bar_ambiguity() -> AMBIGUOUS
history preserved: close kept, next-open added, both logged via fill_convention
```

الخروج

```
currently exit at close of exit bar (optimistic)
audit: should be next-open after objective bar for symmetry
preserved historical close, documented need for later-bar for both sides
```

## المهمة 4: أصل الشيفرة (أعلاه)

لا حذف ولا دمج صامت

## المهمة 5: لماذا صفقات قليلة

فبراير 480

```
96 no strict
341 gate held (FVG opposing)
40 gate pass but no plan (missing structural)
3 plans ->2 win+1 invalidated
```

أبريل 528

```
41 no strict
407 gate held
77 pass without plan
3 plans ->3 win
```

عينات

```
held: 2025-02-06 10:00 FVG-1h-83 downward opposing up
pass without plan: need missing_evidence breakdown (insufficient logging)
```

لا يعادل منع البوابة تجنب خسارة نقدية

```
gate hold prevents hypothetical, not monetary loss
no-entry not loss
```

حيث السجلات غير كافية

```
lack full FVG candidate list per decision
lack ranking of alternative references
action: add targeted logging for future runs
```

## المهمة 6: تجربة إطار أدنى

الحفاظ على سياق أعلى

```
HTF 1h leg via trajectory
LTF 15m via connected_readings
plan keeps HTF invalidation/objective, only entry lowered
```

واجهات زمنية

```
COMPLETED_ROW_AVAILABLE, completed 15m bar only
```

تمكين إدخال أدنى

```
after HTF plan, allow first 15m close beyond same level as alternative trigger
no pattern fingerprint, no arbitrary threshold
```

مصدر مقابل فرضية

```
source: Michael uses LTF for entry after HTF bias (concept, no exact 15m rule)
hypothesis: 15m close beyond level is engineering proxy
explicitly state not automatically Michael rule
```

حفظ بدائل

```
preserve alternatives, counterevidence, invalidation, unresolved
```

محاكاة واقعية

```
entry at next 5m open after 15m close, spread gaps ambiguity as before
```

خط أساس ومقارنة

```
baseline hourly entry V1 fixed close
experiment LTF 15m entry same data same costs same gate
predeclare later period 2025-05-01->06-01 before viewing (disclose Feb/Apr already viewed, May not)
do not choose period/rule because known win
not yet implemented, design documented
```

## المهمة 7: الصفقات الفعلية

فبراير مصحح

```
entered 2 wins 2 losses 0 no-entry 1 open 0 ambiguous 0
pips close 12.2+0.1=12.3 per trade 6.15 per plan 4.1
duration 12h 13h
price favorably after entry, no invalidation before entry
intrabar not invented
<=2h: 0
```

أبريل مصحح

```
entered 3 wins 3 losses 0 no-entry 0 open 0 ambiguous 0
pips 98.3+106.2+97.8=302.3 per trade 100.77 per plan 100.77
duration 13h 10h 15h
none <=2h
```

توزيع

```
<=2h 0, 2-6h 0, 6-12h 1 (12h), 12-15h 4, >15h 0
```

حركة بعد الدخول

```
Feb4 15:00 next 1h close 16:00 1.0372 above entry, no invalidation below 1.027225
Feb5 08:00 hover near entry, exit 21:00 above
Apr2 13:00 rose steadily, no adverse touch
```

## المهمة 8: مصادر

```
ICT_SOURCE_AUDIT.md, SOURCES.md, EXTENDED_STUDY_FIVE_VIDEOS.md, corpus_full_pass.json (approx transcript)
links: local markdown, no external URL, timestamps approx 00:15:20 etc, verified via transcript search, approximate not visually frame-verified
checked: G-OB-P needs P-N/P-W, FVG not in primary
remains approximate: exact wording
no exact replication claim
source_agreement verdicts differs/partially aligned/not stated
```

## اختبارات

```
pip install pandas==2.2.3
PYTHONPATH=project/trading_project/src python -m pytest test_forex_direction_gate_fix.py test_forex_intraday_loop.py -v
eval commands as above
artifacts /tmp/forex-eval-fixed-original/summary_eval_v1.json etc
12+4 passed, pandas 2.2.3
protected file 72b03ca6...
held-out tpPtItWqmlg untouched, no live orders
```

## ما لم يمكن فحصه

```
May period LTF experiment not yet run (terminal temporarily unavailable earlier)
records insufficient for full reference ranking
future logging added prospectively
no claim based on draft or estimates
```
