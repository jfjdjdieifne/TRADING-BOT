#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
استرجاع موجه حتمي
يقيم كل مقطع من 2440 بترتيب عدد المصطلحات المختلفة داخل نافذة منزلقة واحدة
حجم النافذة 50 كلمة معلن في QUERY_SPEC.md كقرار هندسي مع سبب
لا يوجد حد لكل ملف ولا اختيار عتبة بالنظر إلى العد
"""
import json, re, pathlib, os, sys

# مصطلحات كل فجوة كما في QUERY_SPEC.md (مطابقة حرفيا بعد التطبيع)
Q_TERMS = {
    "Q11": ["stop", "stop loss", "below", "mean threshold", "low", "candle", "handle", "two percent", "risk", "placement", "smaller", "margin"],
    "Q13": ["move", "stop", "break even", "first profit", "75%", "london", "resist", "before"],
    "Q09": ["entry", "level", "order block", "limit", "market", "order", "fill", "fibonacci"],
}

# تطبيع البحث نفسه N-06
import re, unicodedata
TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)
WS_RE = re.compile(r"\s+", re.UNICODE)
CONTRACTIONS = [
    (re.compile(r"\b(you|we|they|i|it|that|there|what|who|he|she|how|where|when|let)\s*'\s*(re)\b", re.I), r"\1 are"),
    (re.compile(r"\b(we|they|you|i)\s*'\s*(ve)\b", re.I), r"\1 have"),
    (re.compile(r"\b(we|they|you|i|he|she|it|that|there|what|who)\s*'\s*(ll)\b", re.I), r"\1 will"),
    (re.compile(r"\b(he|she|it|that|there|what|who|this|here)\s*'\s*(s)\b", re.I), r"\1 is"),
    (re.compile(r"\b(i)\s*'\s*(m)\b", re.I), r"\1 am"),
    (re.compile(r"\b(you|we|they|i|he|she|it)\s*'\s*(d)\b", re.I), r"\1 would"),
    (re.compile(r"\b(can)\s*'\s*(t)\b", re.I), r"\1 not"),
    (re.compile(r"\b(won)\s*'\s*(t)\b", re.I), r"will not"),
    (re.compile(r"\b(sh)\s*'\s*(all)\b", re.I), r"shall"),
    (re.compile(r"n\s*'\s*t\b", re.I), " not"),
]
def search_tokens(text):
    t=text
    for rx, rep in CONTRACTIONS:
        t=rx.sub(rep, t)
    t=t.lower()
    t=unicodedata.normalize("NFKC", t)
    t=re.sub(r"[^0-9a-z]+"," ", t)
    return t.split()
def search_text(text):
    return " ".join(search_tokens(text))

# Pre-normalize terms
NORM_TERMS = {}
for q, terms in Q_TERMS.items():
    NORM_TERMS[q] = [search_text(t) for t in terms]

WINDOW_SIZE = 50  # كلمات بعد التطبيع

def score_chunk(tokens, terms_normalized):
    # tokens is list of normalized tokens of chunk
    n = len(tokens)
    if n == 0:
        return 0, 0
    # Build term token sequences
    term_seqs = [t.split() for t in terms_normalized if t]
    best_count = 0
    best_pos = 0
    # Sliding window of WINDOW_SIZE tokens
    for start in range(0, max(1, n - WINDOW_SIZE + 1)):
        window = tokens[start:start+WINDOW_SIZE]
        window_text = " ".join(window)
        # Count distinct terms present as contiguous sequence in window
        # For multi-word terms, need contiguous occurrence
        distinct = 0
        for seq in term_seqs:
            if len(seq) == 1:
                if seq[0] in window:
                    distinct += 1
            else:
                # check contiguous
                seq_str = " ".join(seq)
                # naive sliding check
                found=False
                for i in range(len(window)-len(seq)+1):
                    if window[i:i+len(seq)] == seq:
                        found=True
                        break
                if found:
                    distinct+=1
        if distinct > best_count:
            best_count = distinct
            best_pos = start
            if best_count == len(term_seqs):
                break
    return best_count, best_pos

def main():
    chunk_index_path = "project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/playbook/k7/CHUNK_INDEX.jsonl"
    # Load all chunks
    chunks=[]
    with open(chunk_index_path) as f:
        for line in f:
            chunks.append(json.loads(line))
    print(f"chunks total {len(chunks)}")
    # For each chunk, get text via joined file
    # Need to map file_id -> joined text
    joined_dir = "/home/user/k7_work/joined"
    # Cache joined texts
    joined_cache = {}
    def get_chunk_text(file_id, char_start, char_end):
        if file_id not in joined_cache:
            txt_path = os.path.join(joined_dir, f"{file_id}.txt")
            if not os.path.exists(txt_path):
                return ""
            with open(txt_path, encoding="utf-8") as jf:
                joined_cache[file_id]=jf.read()
        txt = joined_cache[file_id]
        return txt[char_start:char_end]

    results = {q: [] for q in Q_TERMS}
    for ch in chunks:
        file_id = ch["file_id"]
        char_start = ch["char_start"]
        char_end = ch["char_end"]
        chunk_id = ch["chunk_id"]
        text = get_chunk_text(file_id, char_start, char_end)
        tokens = search_tokens(text)
        for q in Q_TERMS:
            score, pos = score_chunk(tokens, NORM_TERMS[q])
            results[q].append({"chunk_id": chunk_id, "file_id": file_id, "score": score, "best_pos": pos, "words": ch["words"]})

    # Rank: sort descending by score, then by chunk_id alphabetical for determinism
    for q in Q_TERMS:
        lst = results[q]
        lst_sorted = sorted(lst, key=lambda x: (-x["score"], x["chunk_id"]))
        # add rank (1-indexed)
        for i, rec in enumerate(lst_sorted):
            rec["rank"] = i+1
        out_path = f"project/trading_project/docs/research/huddleston_study/harvest/distill/understanding/playbook/k7/phase1/v2/ranked_{q}.jsonl"
        with open(out_path, "w", encoding="utf-8") as out:
            for rec in lst_sorted:
                out.write(json.dumps(rec, ensure_ascii=False)+"\n")
        print(f"{q} ranked saved {out_path} top score {lst_sorted[0]['score'] if lst_sorted else 0}")

if __name__ == "__main__":
    main()
