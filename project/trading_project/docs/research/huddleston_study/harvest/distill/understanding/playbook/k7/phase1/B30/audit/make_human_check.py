#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""K7 Phase-1 B30 audit — step 6: HUMAN_CHECK.md generator (deterministic).

Rule declared in PARAMETERS.md section A1, row A1-03 (before any result):
  - pool: every statement of the ORIGINAL records of the 5 sample chunks,
    keyed and sorted by (chunk_id, statement index within its chunk record);
  - draw: random.Random(20261108).sample(pool, 12);
  - order in the file: ascending by the same (chunk_id, index) key.
Each item = English quote (verbatim from the original record) + the original
paraphrase + the Arabic question "does the paraphrase say more than the
quote?" + an empty answer box. No auditor labels anywhere.

Usage: python3 make_human_check.py [joined_dir]  (joined_dir not needed here)
Writes HUMAN_CHECK.md next to this file.
"""
import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
B30 = os.path.abspath(os.path.join(HERE, ".."))
SEED = 20261108
N = 12

SAMPLE = json.load(open(os.path.join(HERE, "SAMPLE.json"), encoding="utf-8"))
SAMPLE_IDS = SAMPLE["sample"]

pool = []  # (chunk_id, idx, statement)
for cid in sorted(SAMPLE_IDS):
    fid = cid.split("#")[0]
    for line in open(os.path.join(B30, "readings", f"{fid}.jsonl"), encoding="utf-8"):
        rec = json.loads(line)
        if rec["chunk_id"] != cid:
            continue
        for i, st in enumerate(rec["statements"]):
            pool.append((cid, i, st))
pool.sort(key=lambda t: (t[0], t[1]))

sel = random.Random(SEED).sample(list(range(len(pool))), N)
sel_items = sorted((pool[i] for i in sel), key=lambda t: (t[0], t[1]))

L = []
L.append("# الفحص البشري — 12 عبارة من السجلات الأصلية (B30)")
L.append("")
L.append("طريقة الاختيار (مُعلنة قبل أي نتيجة في PARAMETERS.md، سطر A1-03): الجماعة هي كل عبارات السجلات الأصلية للمقاطع الخمسة المحددة في `SAMPLE.json`، مرتبة بترتيب (معرّف المقطع، ترتيب العبارة داخل سجل المقطع)، ثم `random.Random(20261108)` ثم `random.sample` بحجم 12، ثم ترتيب تصاعدي. لا يوجد في هذا الملف أي وسم من مدقق؛ الصندوق فارغ للفحص البشري.")
L.append("")
L.append("السؤال في كل بند: **هل الخلاصة تقول أكثر مما يقوله الاقتباس؟**")
L.append("")
for n, (cid, i, st) in enumerate(sel_items, 1):
    L.append(f"## {n}. {cid} — عبارة رقم {i}")
    L.append("")
    L.append(f"> {st['quote']}")
    L.append("")
    L.append(f"الخلاصة (كما في السجل الأصلي):")
    L.append("")
    L.append(f"> {st['paraphrase']}")
    L.append("")
    L.append("الإجابة: (فارغ — يُعبأ من الفاحص البشري)")
    L.append("")
L.append("---")
L.append("")
L.append("ملاحظة: الاقتباسات من السجلات الأصلية كما هي (تضم أشكال ASR). الخُلاصات من السجلات الأصلية كما هي أيضاً — هذا الملف لا يحتوي أي نص من مدقق الفحص الأعمى.")

out = os.path.join(HERE, "HUMAN_CHECK.md")
with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(L))
print("wrote", out)
for cid, i, _ in sel_items:
    print(f"  {cid} stmt#{i}")
