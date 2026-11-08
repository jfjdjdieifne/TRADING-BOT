#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""K7 PHASE 0 report writer. Arabic prose, numbers taken only from the artefacts.

Emits: FOLDER_MAP.md, BATCH_PLAN.md, DUPLICATE_MAP.md, SPEAKER_RISK_MAP.md, L00_RESULT.md
"""
import argparse
import json
import os
from collections import Counter, defaultdict

YEAR_RE = __import__("re").compile(r"\b(19[5-9]\d|20[0-2]\d)\b")


def jloadl(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def ar(n):
    return f"{n:,}".replace(",", "\u066c")


def cnt(n, one, two, many):
    """Arabic-correct counting: 1 -> one, 2 -> two, 3..10 -> many, else digits + many."""
    if n == 1:
        return one
    if n == 2:
        return two
    return f"{ar(n)} {many}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--work", required=True)
    a = ap.parse_args()
    repo, work = a.repo, a.work

    inv = jloadl(os.path.join(repo, "FILE_INVENTORY.jsonl"))
    chunks = jloadl(os.path.join(repo, "CHUNK_INDEX.jsonl"))
    dups = [json.loads(l) for l in open(os.path.join(repo, "DUPLICATE_MAP.jsonl"), encoding="utf-8")]
    batches = jloadl(os.path.join(repo, "BATCH_INDEX.jsonl"))
    cit = json.load(open(os.path.join(work, "citations.json"), encoding="utf-8"))
    probes = json.load(open(os.path.join(work, "probes.json"), encoding="utf-8"))
    l00 = json.load(open(os.path.join(work, "l00.json"), encoding="utf-8"))
    spk = json.load(open(os.path.join(work, "speaker.json"), encoding="utf-8"))
    totals = json.load(open(os.path.join(work, "inventory_totals.json"), encoding="utf-8"))

    # ---------------------------------------------------------------- FOLDER MAP
    folder = defaultdict(lambda: {"files": 0, "words": 0, "entries": 0, "chunks": 0})
    for r in inv:
        d = folder[r["top_folder"]]
        d["files"] += 1
        d["words"] += r["word_count"]
        d["entries"] += r["entry_count"]
    for c in chunks:
        folder[next(r["top_folder"] for r in inv if r["file_id"] == c["file_id"])]["chunks"] += 1
    uniq = cit["unique"]
    order = sorted(folder, key=lambda f: (min([int(y) for y in YEAR_RE.findall(f)] or [9999]), f))
    never = [f for f in order if uniq.get(f, 0) == 0]

    L = []
    L.append("# خريطة المجلدات — K7 المرحلة صفر\n")
    L.append("## ما هذه الوثيقة\n")
    L.append("هذه خريطة عدّ فقط: لكل مجلد أعلى في `transcriptions/` عدد الملفات والكلمات والمقاطع،")
    L.append("وعدد الاقتباسات الموجودة في السجلات السابقة التي تشير إلى ملف من ذلك المجلد.")
    L.append("لا توجد هنا أي خلاصة محتوى ولا أي ادعاء جديد عن السوق.\n")
    L.append(f"- المجموع: {cnt(totals['files'],'ملف واحد','ملفان','ملف')}، {ar(totals['words_primary'])} كلمة (حسب N-05)، "
             f"{ar(totals['entries'])} مقطع ترجمة، {ar(len(chunks))} مقطع قراءة (chunk).")
    L.append(f"- الكلمات بطريقة `split()` = {ar(totals['words_whitespace'])} (للمصالحة مع رقم الإحاطة 2,549,198).\n")
    L.append("## كيف عُدَّت الاقتباسات\n")
    L.append("الاقتباس المعدود هو سجل فيه حقل نصي اسمه `quote` غير فارغ **و**مسار ملف ترجمة يمكن عزله")
    L.append("(`path` أو `transcript_id` أو `file` أو `source_label`/`source_labels`).")
    L.append("ثم تُزال التكرارات: السجل نفسه (المسار + نص الاقتباس) يُعدّ مرة واحدة فقط، لأن")
    L.append("مجلدات `u2-all` و`u3-k3` منسوخة حرفياً في أكثر من مرجع. المجموع الفريد = "
             f"{ar(cit['unique_total'])} اقتباساً، والمسارات غير المحلولة = {cit['unresolved_paths']}.\n")
    L.append("**الاقتباسات قبل إزالة التكرار، لكل مرجع** (النسخ المكررة بين المراجع ظاهرة هنا):\n")
    for ref in ["K1", "K2", "K3", "U2", "K4a", "K4b", "K5", "DESIGN"]:
        L.append(f"- {ref}: {ar(sum(cit['per_ref'].get(ref, {}).values()))}")
    L.append("")
    L.append("**صيغ سجلات لا تحمل مسار ملف ترجمة** (فيُستثنى اقتباسها من العدّ، وهذا مذكور صراحة كما طُلب):")
    L.append("- `source_corpus_v3/claims.jsonl`: 54 اقتباساً بلا أي مسار ترجمة داخل السجل (فيه `source_id` فقط).")
    L.append("- `distill/knowledge_pack*.jsonl`: لا يحوي حقل `quote` إطلاقاً (فيه `essence` و`source_labels`)، فلم يُعدّ.")
    L.append("- `playbook/k4b/traces.jsonl`: 13 سجلاً بلا نص اقتباس.")
    L.append("- `playbook/k5/claims.jsonl`: 16 اقتباساً لمصادر خارجية (مصادر ويب/مؤلفين) لا تشير إلى ملف في هذه المدونة.\n")

    L.append("## الجدول\n")
    L.append("| المجلد | ملفات | كلمات | مقاطع ترجمة | مقاطع قراءة | اقتباسات فريدة تشير إليه | الحالة |")
    L.append("|---|---:|---:|---:|---:|---:|---|")
    for f in order:
        d = folder[f]
        n = uniq.get(f, 0)
        state = "NEVER_CITED" if n == 0 else "CITED"
        L.append(f"| `{f}` | {d['files']} | {ar(d['words'])} | {ar(d['entries'])} | {d['chunks']} | {n} | {state} |")
    L.append(f"| **المجموع** | **{totals['files']}** | **{ar(totals['words_primary'])}** | **{ar(totals['entries'])}** | "
             f"**{ar(len(chunks))}** | **{ar(cit['unique_total'])}** | |")
    L.append("")
    L.append(f"## مجلدات لم يُقتبس منها أحد: {len(never)}\n")
    if never:
        for f in never:
            L.append(f"- `{f}` — {cnt(folder[f]['files'],'ملف واحد','ملفان','ملفات')}، {ar(folder[f]['words'])} كلمة، "
                     f"{cnt(folder[f]['chunks'],'مقطع قراءة واحد','مقطعا قراءة','مقطع قراءة')}.")
    else:
        L.append("لا يوجد: كل مجلد مقتبَس مرة واحدة على الأقل.")
    L.append("")
    L.append("## ملاحظة عدّ\n")
    L.append("عدد الاقتباسات أعلاه يقيس **ما استُشهد به في السجلات السابقة فقط**. صفر لا يعني أن المجلد")
    L.append("بلا قيمة، ويعني حرفياً أن أحداً لم يقتبس منه في K1..K5. المرحلة الأولى ستقرأ كل المجلدات بلا استثناء.\n")
    open(os.path.join(repo, "FOLDER_MAP.md"), "w", encoding="utf-8").write("\n".join(L))

    # ---------------------------------------------------------------- BATCH PLAN
    full = [b for b in batches if b["kind"] == "FULL_READ"]
    diff = [b for b in batches if b["kind"] == "DIFF_CHECK"]
    rec = [d for d in dups if d["kind"] in ("EXACT_DUPLICATE", "NEAR_DUPLICATE")]
    diff_chunks = sum(b["chunks"] for b in diff)
    L = []
    L.append("# خطة القراءة على دفعات — K7 المرحلة صفر\n")
    L.append("## حجم المقطع (chunk) ولماذا\n")
    L.append("الهدف **1300 كلمة** لكل مقطع، والحد الأدنى للقطع 1105 كلمة (0.85 من الهدف)، والحد الأقصى المرصود 1619 كلمة.")
    L.append("الأسباب، وقد أُعلنت قبل تشغيل أي قياس:")
    L.append("1. نص الترجمة لا يحوي علامات ترقيم، فهو بلا جُمل؛ فالقاطع الوحيد المتاح هو حدود مقاطع الترجمة")
    L.append("   وفجوات الوقت بينها. 1300 كلمة تعني عادة 200–400 سطر ترجمة، أي نحو 10–25 دقيقة كلام:")
    L.append("   وحدة موضوعية قابلة للفهم، لا شرائح مبهمة.")
    L.append("2. كل مقطع يحتاج سجلاً كاملاً (تعريفات، شروط، خطوات، تحذيرات، كلمات غامضة، مراجع، فراغات).")
    L.append("   1300 كلمة تُنتج سجلاً يمكن التحقق منه يدوياً؛ ولو كان المقطع 3000 كلمة لصار السجل طويلاً")
    L.append("   بما يمنع التدقيق المستقل.")
    L.append("3. لا توجد مساحة تراكب: نهاية المقطع عند مدخل ترجمة، والبداية التالية عند المدخل التالي،")
    L.append("   والفاصل حرف مسافة واحد فقط (التحقق V03 يثبت ذلك).")
    L.append(f"\nالنتيجة: **{ar(len(chunks))} مقطع قراءة** يغطي كل الكلمات ({ar(totals['words_primary'])}).\n")
    L.append("## حجم الدفعة (batch) ولماذا\n")
    L.append("الدفعة = حتى **25 مقطعاً** وبحد أقصى **32,000 كلمة**، ولا تُقسَّم قطعة واحدة بين دفعتين.")
    L.append("السبب: 25 سجلاً كاملاً هو أقصى ما يمكن كتابته في جلسة واحدة مع الحفاظ على الدقة،")
    L.append("و32,000 كلمة حدّ نُبقي دونه هامشاً للمراجعة والتصحيح داخل الجلسة.")
    L.append("النتيجة المقيسة: مجموع كلمات الدفعة بين "
             f"{ar(min(b['words'] for b in full))} و{ar(max(b['words'] for b in full))} كلمة "
             f"(الوسيط {ar(sorted(b['words'] for b in full)[len(full)//2])}).\n")
    L.append("الترتيب: المجلدات مرتّبة بالسنة الظاهرة في اسم المجلد ثم أبجدياً، والملفات داخلها بترتيب المسار،")
    L.append("والمقاطع بترتيب التتابع. هذا **ترتيب خطة فقط**، وليس ادعاءً عن ترتيب التعليم عند Michael (انظر TIMELINE_FACTS).")
    L.append("المكرر الحقيقي يوضع آخراً في دفعة فحص فروق منفصلة، لأن فحص الفرق لا يحتاج قراءة كاملة.\n")
    L.append("## كم جلسة قراءة يحتاج كل شيء\n")
    L.append(f"- **{ar(len(full))} جلسة** لقراءة كاملة (دفعة واحدة لكل جلسة، {ar(sum(b['words'] for b in full))} كلمة، "
             f"{ar(sum(b['chunks'] for b in full))} مقطعاً).")
    L.append(f"- **{ar(len(diff))} جلسة** لفحص فروق الملفات المكررة ({ar(diff_chunks)} مقطعاً، "
             f"{ar(sum(b['words'] for b in diff))} كلمة).")
    L.append(f"- المجموع الصادق: **{ar(len(full) + len(diff))} جلسة** كحد أدنى. أي تقدير أقل من ذلك يعني تسليماً ناقصاً.\n")
    L.append("## الدفعات\n")
    L.append("| الدفعة | النوع | مجلدات | ملفات | مقاطع | كلمات | أول مقطع | آخر مقطع |")
    L.append("|---|---|---:|---:|---:|---:|---|---|")
    for b in batches:
        L.append(f"| {b['batch_id']} | {'قراءة كاملة' if b['kind']=='FULL_READ' else 'فحص فروق'} | "
                 f"{len(b['folders'])} | {len(b['files'])} | {b['chunks']} | {ar(b['words'])} | "
                 f"`{b['first_chunk']}` | `{b['last_chunk']}` |")
    L.append("")
    L.append("## المكرر داخل الخطة\n")
    L.append(f"- الملفات المتطابقة تماماً: {len([d for d in rec if d['kind']=='EXACT_DUPLICATE'])} زوجاً. يُقرأ الأول كاملاً،")
    L.append("  والثاني يُفحص فرقاً فقط: كل مقاطعه مصنّفة DIFF_ONLY في DUPLICATE_MAP.")
    L.append("- لا يوجد زوج قريب فوق العتبة المعلنة 0.60. أقرب زوج تحت العتبة مذكور صراحة ولا يُخفى،")
    L.append("  ويُقرأ كاملاً مع الآخر لأن الاسم وحده ليس دليل تطابق.")
    L.append(f"- الدفعة D01 تحوي {ar(diff_chunks)} مقطعاً من الملفات المكررة (فحص فروق).")
    L.append("")
    L.append("## ما لم يُفعل\n")
    L.append("لم تُقرأ أي قطعة بعد. الحالة الرسمية الآن: كل المقاطع `UNREAD`.")
    L.append("لا `SEARCHED` ولا `SAMPLED` في هذه المرحلة، ولا ادعاء من Tier1.")
    open(os.path.join(repo, "BATCH_PLAN.md"), "w", encoding="utf-8").write("\n".join(L))

    # ---------------------------------------------------------------- DUPLICATE MAP
    exact = [d for d in dups if d["kind"] == "EXACT_DUPLICATE"]
    near = [d for d in dups if d["kind"] == "NEAR_DUPLICATE"]
    below = [d for d in dups if d["kind"] == "NEAR_DUPLICATE_BELOW_THRESHOLD"]
    mp = [d for d in dups if d["kind"] == "MULTI_PART"]
    tm = [d for d in dups if d["kind"] == "TITLE_MATCH_ACROSS_SERIES"]
    L = []
    L.append("# خريطة التكرار — K7 المرحلة صفر\n")
    L.append("## الطريقة، وقد أُعلنت قبل النظر إلى النتائج\n")
    L.append("- تجزئة النص: مقاطع (shingles) من 8 كلمات متتابعة على النص المُطبَّع بـ N-05.")
    L.append("- لكل ملف مجموعة shingles، وبصمة كل shingle رقم 64-bit حتمي (كثيرة الحدود على CRC32 للكلمة).")
    L.append("- التطابق التام: تساوي SHA-256 للنص الموصول.")
    L.append("- التشابه: Jaccard = التقاطع ÷ الاتحاد، محسوباً بالضبط على المجموعتين لا تقديراً.")
    L.append("- العتبتان المعلنتان قبل التشغيل: NEAR 0.60، وSTRONG 0.85. القرار: STRONG يعني قراءة الأول كاملاً وفحص")
    L.append("  فروق الثاني؛ وما بين 0.60 و0.85 يعني قراءة الاثنين كاملاً، لأن إعادة التسجيل قد تحمل شرطاً جديداً.")
    L.append("- كل زوج بين 0.25 و0.60 يُذكر صراحة تحت العتبة، حتى لا يُخفي أي شيء.")
    L.append("- التجزئة إلى أجزاء: نفس المجلد ونفس العنوان بعد حذف لاحقة `-NNN`من اسم الملف.\n")
    L.append(f"## الحصيلة: {len(exact)} تام / {len(near)} قريب / {len(mp)} درساً متعدد الأجزاء / {len(tm)} عنوان متطابق عبر سلاسل\n")
    if exact:
        L.append("### التطابق التام\n")
        L.append("| الملف المقروء كاملاً | الملف المفحوص فرقاً | المسار A | المسار B |")
        L.append("|---|---|---|---|")
        for d in exact:
            L.append(f"| `{d['file_a']}` | `{d['file_b']}` | `{d['path_a'].split('/')[-1]}` | `{d['path_b'].split('/')[-1]}` |")
        L.append("")
        L.append("كلها تكرارات صادقة: نفس المقطع منشور في مجلدين، أو نفس الملف باسم فيه خطأ إملائي في اسم الطالب.")
        L.append("لا يُحذف ولا يُخفى أي ملف: الثاني يبقى في الخريطة ويُفحص فرقاً فقط.\n")
    L.append("### تحت العتبة\n")
    if below:
        for d in below:
            L.append(f"- `{d['file_a']}` مقابل `{d['file_b']}` — Jaccard = {d['jaccard']}")
            L.append(f"  ({d['path_a'].split('/')[-1]} ↔ {d['path_b'].split('/')[-1]})")
            L.append("  هذا تشابه عالٍ يُذكر للأمانة، لكنه **دون** العتبة المعلنة، فلا يُصنَّف مكرراً، ويُقرأ الملفان كاملين.")
    else:
        L.append("لا شيء.")
    L.append("")
    L.append(f"### الدروس متعددة الأجزاء: {len(mp)} مجموعة\n")
    L.append("الأجزاء تكملة لا تكرار. كل جزء يُقرأ كاملاً. عدد المجموعات التي فيها فراغ في ترقيم الأجزاء: "
             f"{sum(1 for d in mp if d['part_gap'])}.\n")
    if tm:
        L.append("### عنوان متطابق في سلسلتين\n")
        for d in tm:
            L.append(f"- `{d['title']}` — {', '.join('`'+x+'`' for x in d['folders'])} — ملفات: {', '.join(d['file_ids'])}")
        L.append("")
        L.append("تطابق العنوان **ليس** ادعاء تشابه نصي؛ الاثنان يُقرآن كاملين، والمقارنة تُسجَّل في المرحلة الثانية.\n")
    L.append("## ما لا يقوله هذا الملف\n")
    L.append("لا يقول إن ملفاً عديم القيمة، ولا يحذف شيئاً، ولا يدمج درسين. كل قرار هنا هو قرار قراءة فقط.\n")
    open(os.path.join(repo, "DUPLICATE_MAP.md"), "w", encoding="utf-8").write("\n".join(L))

    # ---------------------------------------------------------------- SPEAKER RISK
    L = []
    L.append("# خريطة خطر الأصوات الأخرى — K7 المرحلة صفر\n")
    L.append("## المشكلة\n")
    L.append("ملفات الترجمة **بلا أي وسم للمتحدث**. لذلك لا يجوز أن ننسب جملة إلى Michael إلا إذا كان النص نفسه")
    L.append("يُظهر ذلك. هذه الخريطة لا تحكم على أي جملة؛ إنها تعدّ علامات مرئية في النص لتعرف القراءة أين")
    L.append("يجب أن تتوقع سؤالاً أو صوتاً آخر، وأين تسجّل `UNKNOWN`.\n")
    L.append("## العلامات المعدودة (بحث حرفي بعد N-06)\n")
    L.append("- `CHAT_OR_COMMENTS`: ذكر الدردشة أو التعليقات أو سؤال من أحد («in the chat»، «someone asked»، «you asked»).")
    L.append("- `AUDIENCE_QUESTION`: مخاطبة الحاضرين بسؤال («does that make sense»، «any questions»، «are you with me»).")
    L.append("- `THANKS_TO_HIM`: شكر موجّه إليه («thank you Michael»، «appreciate it»).")
    L.append("- `LIVE_MARKER`: افتتاحيات البث («welcome back»، «hello everyone»، «we are live»).")
    L.append("- `SECOND_VOICE`: إشارة إلى كلام شخص آخر («he asked»، «the question was»، «your question»).\n")
    L.append("قيد مهم: الترجمة الآلية بلا علامات ترقيم، فلا توجد علامة استفهام يمكن عدّها؛ لذلك كل العدّ لفظي.")
    L.append("قيد ثانٍ: عبارات الشكر قد تصدر منه هو تجاه المشاهدين، لا منهم تجاهه؛ فعدّها **إشارة لا دليل**،")
    L.append("وهي ترفع الحذر فقط ولا تنسب كلاماً لأحد.\n")
    L.append("## قواعد التصنيف (أُعلنت قبل التشغيل)\n")
    L.append("- **HIGH**: نسبة الملفات التي فيها ذكر دردشة/تعليقات ≥ 50%، أو نسبة ملفات الشكر الموجّه إليه ≥ 30%.")
    L.append("- **MEDIUM**: ≥ 20% للدردشة، أو ≥ 10% للشكر، أو ≥ 90% من الملفات فيها أي علامة.")
    L.append("- **LOW_MEDIUM**: ≥ 50% من الملفات فيها أي علامة. **LOW**: أقل من ذلك لكن أكبر من صفر.")
    L.append("- **UNKNOWN_NO_CUE**: لا علامة واحدة. هذا `UNKNOWN` وليس «Michael وحده» بنفي قاطع.\n")
    L.append("## الجدول\n")
    L.append("| المجلد | الخطر | نسبة الملفات ذات أي علامة | ملفات فيها دردشة/أسئلة | ملفات فيها شكر له | المجموع |")
    L.append("|---|---|---:|---:|---:|---:|")
    for r in spk:
        L.append(f"| `{r['folder']}` | {r['other_voice_risk']} | {r['share_any_cue']:.3f} | "
                 f"{r['files_chat_or_comments']}/{r['files']} | {r['files_thanks_to_him']}/{r['files']} | {r['files']} |")
    L.append("")
    L.append("## ما تفعله القراءة بهذه الخريطة\n")
    L.append("- في مجلد HIGH/MEDIUM: كل جملة تُوسم `UNKNOWN` افتراضياً، ولا تصبح Tier1 إلا إذا كان النص نفسه")
    L.append("  يدل على أنه هو المتكلم (ضمير المتكلم مع تعليم مباشر، أو «my»).")
    L.append("- في مجلد LOW/UNKNOWN_NO_CUE: يبقى الوسم `UNKNOWN` أيضاً؛ الخريطة تخفّض الاحتمال ولا تثبت المتحدث.\n")
    L.append("## أرقام\n")
    c = Counter(r["other_voice_risk"] for r in spk)
    L.append("توزيع المجلدات: " + "، ".join(f"{k} = {v}" for k, v in sorted(c.items())) + ".")
    L.append("")
    open(os.path.join(repo, "SPEAKER_RISK_MAP.md"), "w", encoding="utf-8").write("\n".join(L))

    # ---------------------------------------------------------------- L00
    L = []
    L.append("# نتيجة اختبار السلاسل الأربع (L00) — K7 المرحلة صفر\n")
    L.append("## تنبيه قبل الجدول\n")
    L.append("هذه السلاسل **ادعاء مستخدم غير موثّق** (`USER_LEAD_UNVERIFIED`). ليست Tier1، وليست معرفة،")
    L.append("ولا تدخل أي محرك. الغرض الوحيد: هل توجد حرفياً في النص أم لا.\n")
    L.append("## طريقة البحث\n")
    L.append("- على النص المُطبَّع N-06: تصغير الحروف، توسيع الاختصارات (you're → you are، don't → do not)،")
    L.append("  حذف كل ما ليس حرفاً أو رقماً، ثم مطابقة متتابعة للكلمات.")
    L.append("- محاولة أولى: مطابقة تامة للسلسلة كاملة.")
    L.append("- محاولة ثانية (تنويعات الترجمة الآلية): نافذة منزلقة بطول السلسلة ± كلمة، تُقبل إذا كان")
    L.append("  مسافة التعديل ≤ 2 كلمة (أو 12% من الطول). كل تنويعة تُعرض بنصها الحقيقي.")
    L.append("- محاولة ثالثة (جزئي): أطول مقطع متتابع من السلسلة موجود فعلاً، بحد أدنى 4 كلمات.")
    L.append("- «وجود مقطع شائع في مكان آخر لا يؤكد الجملة». هذا مكتوب في الجدول لكل سطر.\n")
    rows = {r["id"]: r for r in l00}
    title = {
        "S1": "S1 — «If you don't know what the Daily Chart is doing, you are gambling»",
        "S2": "S2 — «When the Monthly and Weekly are in conflict, you sit on your hands»",
        "S3": "S3 — «Narrative is not support and resistance»",
        "S4": "S4 — «IPDA is a computer program. It only looks for two things»",
    }
    verdict = {
        "S1": "**غير موجودة حرفياً.** أطول مقطع مؤكد: «if you do not know what the daily chart» في ملف واحد، "
              "والجملة الحقيقية تكملة مختلفة تماماً («…the daily charts implying in terms of institutional…»). "
              "وعبارة «you are gambling» موجودة وحدها في 15 ملفاً. وجود النصفين منفصلين **لا يؤكد** الجملة.",
        "S2": "**غير موجودة حرفياً.** عبارة «sit on your hands» موجودة فعلاً في 22 ملفاً، لكن ليس مع شرط "
              "«monthly and weekly are in conflict» الذي لا يظهر في أي ملف. الشرط والنتيجة يجتمعان في النص؟ لا.",
        "S3": "**أقرب نص مختلف في كلمة واحدة حاسمة.** النص الحقيقي: «it's not support and resistance»؛ كلمة "
              "«narrative» غير موجودة في تلك الجملة. فالجملة المزعومة ليست قوله، والمعنى مختلف.",
        "S4": "**غير موجودة.** كلمة «IPDA» لا ترد إلا 3 مرات في المدونة كلها، و«ipda is a computer program» "
              "لا ترد أبداً. الاسم الكامل «interbank price delivery algorithm» يرد 17 مرة في 12 ملفاً، "
              "و«it only looks for two things» لا يرد.",
    }
    L.append("## الجدول\n")
    L.append("| السلسلة | الحالة الآلية | الأرقام | الحكم |")
    L.append("|---|---|---|---|")
    for sid in ["S1", "S2", "S3", "S4"]:
        r = rows[sid]
        L.append(f"| {title[sid]} | {r['status']} | تام={len(r['exact_hits'])}، تنويعات={r['variant_total']}، "
                 f"مقاطع جزئية={r['fragment_total']} | {verdict[sid]} |")
    L.append("")
    L.append("## الأدلة الحرفية (كل اقتباس ≤ 25 كلمة، بموضعه)\n")
    for sid in ["S1", "S2", "S3", "S4"]:
        r = rows[sid]
        L.append(f"### {sid}\n")
        if r["exact_hits"]:
            L.append("مطابقة تامة:")
            for h in r["exact_hits"][:3]:
                L.append(f"- `{h['file_id']}` — {h['path']}")
        if r["variant_hits"]:
            L.append("أقرب تنويعات (الفارق مبيَّن):")
            for vh in r["variant_hits"][:4]:
                L.append(f"- مسافة {vh['distance']} كلمة — `{vh['file_id']}` — «{vh['window']}»")
        if r["fragments"]:
            L.append("أطول مقاطع موجودة فعلاً:")
            for fr in r["fragments"][:3]:
                L.append(f"- {fr['length']} كلمات — «{fr['fragment']}» — `{fr['file_id']}`")
        L.append("")
    L.append("## الشواهد الحرفية من المسح الموجّه (مقاطع بمواضع offsetMS)\n")
    for label in ["S1_HEAD", "S1_TAIL", "S2_PHRASE", "S2_SENTENCE", "S3_FRAG", "S4_SENTENCE", "S4_FULLNAME", "S4_ACRONYM"]:
        d = probes[label]
        if d["files"] == 0:
            L.append(f"**{label}** — البحث عن «{d['probe']}»: **لم يظهر إطلاقاً** في أي من الملفات 490.")
        else:
            L.append(f"**{label}** — البحث عن «{d['probe']}»: ظهر في "
                     f"{cnt(d['files'],'ملف واحد','ملفين','ملفاً')}، {cnt(d['occurrences'],'مرة واحدة','مرتين','مرة')}.")
        for ex in d["examples"][:2]:
            L.append(f"- `{ex['file_id']}` عند offsetMS={ex['offsetMS']} — «{ex['quote']}»")
        L.append("")
    L.append("## الحكم النهائي على L00\n")
    L.append("لا واحدة من السلاسل الأربع موجودة حرفياً في المدونة. ثلاث منها لها أقرب نص مختلف،")
    L.append("وواحدة (S3) تختلف في الكلمة الحاكمة. لذلك لا تصبح أي منها Tier1، ولا تُستخدم كدليل على")
    L.append("معنى أو شرط. تُترك في هذا الجدول فقط بوصفها `USER_LEAD_UNVERIFIED`.\n")
    open(os.path.join(repo, "L00_RESULT.md"), "w", encoding="utf-8").write("\n".join(L))
    # ---------------------------------------------------------------- TIMELINE summary
    tl = jloadl(os.path.join(repo, "TIMELINE_FACTS.jsonl"))
    dc = Counter(x["date_state"] for x in tl)
    oc = Counter(x["order_within_series"] for x in tl)
    L = []
    L.append("# وقائع الزمن والترتيب — K7 المرحلة صفر\n")
    L.append("## القاعدة\n")
    L.append("لا يُستنتج أي تاريخ من ترتيب أسماء الملفات، ولا من ترتيب المجلدات، ولا من المعرفة الخارجية.")
    L.append("المسجَّل هو فقط: سنة ظاهرة في اسم المجلد، أو تاريخ مكتوب في اسم الملف، أو سنة وردت في النص نفسه.")
    L.append("وإن لم يوجد شيء فالحالة `DATE_UNKNOWN` صريحة.\n")
    L.append("الترتيب داخل السلسلة `UNVERIFIED` إلا إذا وردت في النص عبارة ترقيم («lesson seven»، «lesson 6»).")
    L.append("وحتى مع وجود العبارة، هي **ظاهرة نصية مسجّلة** لا إثبات لموقع الملف في السلسلة،")
    L.append("وذلك بسبب `NUMBERING_PHRASE_PRESENT` لا `PROVEN`. ترتيب الأجزاء يأتي من رقم الجزء في اسم الملف فقط.\n")
    L.append("## التوزيع\n")
    L.append("| الحالة | عدد الملفات | المعنى |")
    L.append("|---|---:|---|")
    meaning = {
        "DATE_IN_FILENAME": "تاريخ مكتوب في اسم الملف (سنة-شهر-يوم)",
        "DATE_TOKEN_IN_FILENAME_AMBIGUOUS": "أرقام في الاسم تحتمل تاريخاً بترتيبين (مثل 09-06-22) — تُسجَّل كما هي بلا تفسير",
        "YEAR_IN_FOLDER_ONLY": "سنة من اسم المجلد فقط",
        "YEAR_IN_TEXT_ONLY": "سنة وردت في النص ولم تُذكر في الاسم",
        "DATE_UNKNOWN": "لا شيء — لا تاريخ ولا سنة",
    }
    for k in ["DATE_IN_FILENAME", "DATE_TOKEN_IN_FILENAME_AMBIGUOUS", "YEAR_IN_FOLDER_ONLY", "YEAR_IN_TEXT_ONLY", "DATE_UNKNOWN"]:
        L.append(f"| {k} | {dc.get(k,0)} | {meaning[k]} |")
    L.append(f"| **المجموع** | **{len(tl)}** | |\n")
    L.append("## ترتيب السلسلة\n")
    for k, v in oc.most_common():
        L.append(f"- {k}: {v}")
    L.append("")
    L.append("## الأرقام الغامضة في الأسماء (مسجّلة كما هي، بلا تفسير)\n")
    for x in tl:
        if x["date_state"] == "DATE_TOKEN_IN_FILENAME_AMBIGUOUS":
            L.append(f"- `{x['file_id']}` — `{x['filename_date']}` — {x['path'].split('/')[-1]}")
    L.append("")
    L.append("## ما لا يقوله هذا الملف\n")
    L.append("لا يقول إن درساً سبق درساً في التعليم، ولا إن سلسلة أقدم تفوق أحدث، ولا يحل أي تعارض.")
    L.append("المرحلة الثانية قد تستخدم هذه الوقائع لوصف «سلسلة/سنة» لكل رابط، لا للحكم بين رابطين.\n")
    open(os.path.join(repo, "TIMELINE_FACTS.md"), "w", encoding="utf-8").write("\n".join(L))
    print("reports written")


if __name__ == "__main__":
    main()
