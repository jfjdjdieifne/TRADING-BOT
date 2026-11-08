#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تشغيل فاحص الدعم على 128 بيانا قديما من 5 مقاطع مدققة
القاعدة كانت معلنة قبل التشغيل في support_check.py
كل كلمة محتوى في الحقول المضافة يجب أن تظهر في الاقتباس أو نافذة ±2 أو باقتباس دليل
"""
import json, pathlib, re
from collections import Counter

import sys
sys.path.insert(0, "project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/playbook/k7/phase1/v2")
import support_check

# Load audit third look classifications indexed by (chunk_id, orig_idx)
audit_map = {}
with open("project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/playbook/k7/phase1/B30/audit/AUDIT_THIRD_LOOK.jsonl") as f:
    for line in f:
        data=json.loads(line)
        cid_chunk = data["chunk_id"]  # not needed
        for rec in data["third_look_a"]:
            key = (data["chunk_id"] if "chunk_id" in data else None, rec["orig_idx"])
            # The AUDIT_THIRD_LOOK file has per-chunk records with chunk_id equal to file? Actually each line is per chunk_id; need to store by (chunk_id, orig_idx)
            pass

# Better: parse each line's third_look_a as list for that chunk_id
map_by_chunk = {}
with open("project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/playbook/k7/phase1/B30/audit/AUDIT_THIRD_LOOK.jsonl") as f:
    for line in f:
        data=json.loads(line)
        # data contains n_orig etc but not chunk_id field? Actually earlier dump shows data has chunk_id? Let's check raw
        # Use the file's ordering: we know order is F0170#001, F0170#003, F0171#002, F0172#002, F0172#003
        pass

# Load directly with inspection
import json

# Read raw lines and assign chunk_ids manually from known sample order
chunk_ids = ["F0170#001","F0170#003","F0171#002","F0172#002","F0172#003"]
class_by_index = {}
with open("project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/playbook/k7/phase1/B30/audit/AUDIT_THIRD_LOOK.jsonl") as f:
    for idx, line in enumerate(f):
        data=json.loads(line)
        cid = chunk_ids[idx]
        for rec in data["third_look_a"]:
            class_by_index[(cid, rec["orig_idx"])] = rec["paraphrase_class"]

# Now load original statements for those chunks
orig_files = [
    "project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/playbook/k7/phase1/B30/readings/F0170.jsonl",
    "project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/playbook/k7/phase1/B30/readings/F0171.jsonl",
    "project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/playbook/k7/phase1/B30/readings/F0172.jsonl",
]
statements = []
for p in orig_files:
    with open(p) as f:
        for line in f:
            d=json.loads(line)
            if d["chunk_id"] in chunk_ids:
                for stmt_idx, stmt in enumerate(d["statements"]):
                    key = (d["chunk_id"], stmt_idx)
                    if key in class_by_index:
                        statements.append((d["chunk_id"], stmt_idx, stmt, class_by_index[key]))

# Need window texts: load entries for each file_id
# For each statement, find entry_index, then get texts of entries at -2..+2
def load_entries(file_id):
    path = f"/home/user/k7_work/joined/{file_id}.entries.json"
    if not pathlib.Path(path).exists():
        return None
    with open(path) as f:
        return json.load(f)

# Also need mapping from entry_index to text? entries.json is list of [char_start,char_end,offsetMS,durationMS,entry_index]
# But we need actual entry text; we can get from corpus json file
# Simpler: load corpus entries via k7_corpus.load_entries

import os
sys.path.insert(0, "project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/playbook/k7/scripts")
import k7_corpus as KC

entries_cache = {}
joined_cache = {}

def get_window_texts(file_id, entry_index):
    # load entries via KC
    if file_id not in entries_cache:
        # find path via FILE_INVENTORY
        # search inventory for file_id
        inv_path = "project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/playbook/k7/FILE_INVENTORY.jsonl"
        rel_path = None
        with open(inv_path) as f:
            for line in f:
                rec=json.loads(line)
                if rec["file_id"] == file_id:
                    rel_path = rec["path"]
                    break
        if not rel_path:
            return []
        abs_path = f"/home/user/k7_work/corpus/{rel_path}"
        entries, _ = KC.load_entries(abs_path)
        entries_cache[file_id] = entries
        # also build map entry_index -> text
    entries = entries_cache[file_id]
    # entries is list of dict with i, text, offsetMS...
    # Find index in list where entry.i == entry_index
    # Then get texts for -2..+2
    pos = None
    for i, e in enumerate(entries):
        if e["i"] == entry_index:
            pos = i
            break
    if pos is None:
        return []
    out=[]
    for delta in [-2,-1,1,2]:
        idx = pos + delta
        if 0 <= idx < len(entries):
            txt = entries[idx]["text"]
            if txt:
                out.append(txt)
    return out

# Run checker
results = []
for chunk_id, stmt_idx, stmt, audit_class in statements:
    quote = stmt.get("quote","")
    # added fields = paraphrase + condition + consequence + number condition
    added_parts = []
    if stmt.get("paraphrase"):
        added_parts.append(stmt["paraphrase"])
    if stmt.get("condition"):
        added_parts.append(stmt["condition"])
    if stmt.get("consequence"):
        added_parts.append(stmt["consequence"])
    # number_with_condition not present in old, but check
    added_text = " ".join(added_parts)
    entry_idx = stmt.get("entry_index")
    file_id = stmt.get("file_id") if "file_id" in stmt else chunk_id.split("#")[0]
    # Actually stmt does not have file_id, use chunk's file_id
    # Get file_id from chunk_id
    file_id = chunk_id.split("#")[0]
    window_texts = get_window_texts(file_id, entry_idx)
    status, unsupported = support_check.check_one(quote, added_text, window_texts, None)
    results.append((chunk_id, stmt_idx, audit_class, status, unsupported, quote, added_text))

# Summarize
from collections import Counter, defaultdict
counter_audit = Counter(r[2] for r in results)
counter_flagged = Counter()
counter_by_class_flagged = defaultdict(int)
for r in results:
    audit_class, status = r[2], r[3]
    if status == "UNSUPPORTED_WORDS":
        counter_flagged[audit_class] += 1

print(f"إجمالي البيانات المفحوصة: {len(results)}")
for cls in ["ADDS_NOTHING","ADDS_CONTEXT_FROM_NEIGHBOUR","ADDS_UNSUPPORTED"]:
    total = sum(1 for r in results if r[2]==cls)
    flagged = counter_flagged.get(cls,0)
    print(f"{cls}: total={total} flagged={flagged} not_flagged={total-flagged} recall={flagged/total if total else 0:.2%}")

# Also report overall
flagged_total = sum(1 for r in results if r[3]=="UNSUPPORTED_WORDS")
print(f"الكل flagged={flagged_total} من {len(results)}")
# Save detailed
out_path = "project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/playbook/k7/phase1/v2/support_check_calibration_result.jsonl"
with open(out_path,"w",encoding="utf-8") as out:
    for r in results:
        rec = {
            "chunk_id": r[0],
            "orig_idx": r[1],
            "audit_class": r[2],
            "checker_status": r[3],
            "unsupported_words": r[4],
            "quote": r[5],
            "added_text": r[6]
        }
        out.write(json.dumps(rec, ensure_ascii=False)+"\n")
print(f"saved to {out_path}")
