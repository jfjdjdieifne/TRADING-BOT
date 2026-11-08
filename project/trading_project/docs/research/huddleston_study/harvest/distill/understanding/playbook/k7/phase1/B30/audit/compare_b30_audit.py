#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""K7 Phase-1 B30 audit — deterministic comparison (step 4).

Compares the ORIGINAL B30 reading records (readings/F017X.jsonl) against the
BLIND audit records (audit/audit_readings_F017X.jsonl) for the 5 sample chunks
fixed in SAMPLE.json. Matching rule (declared in PARAMETERS.md section A1,
before reading): a pair (o, a) MATCHES iff
  (M1) their N-06 normalised word spans in the chunk's token stream overlap in
       >= 1 word token, OR
  (M2) their start entries (entry containing the quote's first word) are the
       same or adjacent (|delta| <= 1).
Location-based, not meaning-based. Unmatched statements are reported in both
directions: ORIGINAL_ONLY and AUDIT_ONLY.

Pair assignment is deterministic: all candidate pairs are sorted by
(overlap word count DESC, |start-entry delta| ASC, original index ASC,
audit index ASC) and greedily assigned 1:1.

C1 counts/matches per chunk + total; C2 agreement on kind/speaker/confidence/
number presence + kind confusion table; C3 content_type per chunk; C4
vague_words overlap + feature-naming agreement; C5 open_slots counts + overlap;
C6 terms overlap. No edits after results.

Usage: python3 compare.py [joined_dir]
  joined_dir default: /home/user/k7_audit/joined (rebuilt from the pinned
  corpus e8c40a8... per K7_PLAN.md step 0; only the 5 sample chunks are read).
Writes COMPARE_RESULT.md next to this file (Arabic prose; quotes stay English).
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
K7 = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(K7, "scripts"))
import k7_corpus as KC  # noqa: E402

JOINED = sys.argv[1] if len(sys.argv) > 1 else "/home/user/k7_audit/joined"
B30 = os.path.abspath(os.path.join(HERE, ".."))

SAMPLE = json.load(open(os.path.join(HERE, "SAMPLE.json"), encoding="utf-8"))
SAMPLE_IDS = SAMPLE["sample"]

CI = {}
with open(os.path.join(K7, "CHUNK_INDEX.jsonl"), encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        CI[r["chunk_id"]] = r

STOP = {
    "a", "an", "the", "of", "in", "on", "to", "and", "or", "is", "are", "was",
    "were", "it", "its", "that", "this", "these", "those", "with", "for", "as",
    "at", "by", "be", "been", "being", "do", "does", "did", "not", "no", "so",
    "if", "but", "when", "where", "which", "who", "how", "what", "why", "will",
    "would", "can", "could", "should", "may", "might", "must", "shall", "you",
    "your", "yours", "i", "me", "my", "we", "our", "he", "his", "she", "her",
    "they", "them", "their", "us", "am", "have", "has", "had", "do", "done",
    "here", "there", "then", "than", "then", "very", "really", "just", "like",
    "okay", "ok", "um", "yeah", "right", "stuff", "thing", "things",
}

DIGIT = re.compile(r"^[0-9]+$")


def norm_term(s):
    return " ".join(KC.search_tokens(s))


def has_number(quote):
    return any(DIGIT.match(t) for t in KC.search_tokens(quote))


def locate(joined, ch, spans, quote):
    """Return (tok_start, tok_end, first_entry, last_entry) in the chunk window
    normalised token stream, or None if not found."""
    window = joined[ch["char_start"]:ch["char_end"]]
    toks, tspans = KC.norm_tokens_with_pos(window)
    idx = KC.build_pos_index(toks)
    res = KC.verbatim_for(toks, tspans, idx, KC.search_tokens(quote))
    if not res:
        return None
    cs, ce, _ = res
    e1 = KC.entry_at(spans, ch["char_start"] + cs)
    e2 = KC.entry_at(spans, ch["char_start"] + max(ce - 1, cs))
    # span rows are [char_start, char_end, offsetMS, ...]; the entry index is
    # the row position in the spans list (checked against original records'
    # entry_index fields, which count rows from 0)
    return cs, ce, (spans.index(e1) if e1 else None), (spans.index(e2) if e2 else None)


def load_records(side):
    """side: 'orig' | 'audit' -> {chunk_id: record}"""
    out = {}
    files = {
        "orig": {"F0170": "readings/F0170.jsonl", "F0171": "readings/F0171.jsonl", "F0172": "readings/F0172.jsonl"},
        "audit": {"F0170": "audit/audit_readings_F0170.jsonl", "F0171": "audit/audit_readings_F0171.jsonl", "F0172": "audit/audit_readings_F0172.jsonl"},
    }[side]
    for fid, path in files.items():
        for line in open(os.path.join(B30, path), encoding="utf-8"):
            rec = json.loads(line)
            if rec["chunk_id"] in SAMPLE_IDS:
                out[rec["chunk_id"]] = rec
    return out


def term_name(orig_item, audit_item):
    if isinstance(orig_item, dict):
        return orig_item.get("term", "")
    # audit: "term — «quote»"
    return audit_item.split(" — ")[0].strip() if isinstance(audit_item, str) else str(audit_item)


def main():
    orig = load_records("orig")
    audit = load_records("audit")

    chunks = []
    for cid in SAMPLE_IDS:
        ch = CI[cid]
        fid = ch["file_id"]
        joined = open(os.path.join(JOINED, f"{fid}.txt"), encoding="utf-8").read()
        spans = json.load(open(os.path.join(JOINED, f"{fid}.entries.json"), encoding="utf-8"))
        o, a = orig[cid], audit[cid]

        o_loc = []
        for st in o["statements"]:
            loc = locate(joined, ch, spans, st["quote"])
            o_loc.append(loc)
        a_loc = []
        for st in a["statements"]:
            loc = locate(joined, ch, spans, st["quote"])
            a_loc.append(loc)

        # candidates
        cands = []
        for i, ol in enumerate(o_loc):
            for j, al in enumerate(a_loc):
                if ol is None or al is None:
                    continue
                overlap = max(0, min(ol[1], al[1]) - max(ol[0], al[0]))
                same_adj = abs(ol[2] - al[2]) <= 1
                if overlap >= 1 or same_adj:
                    cands.append((-overlap, abs(ol[2] - al[2]), i, j))
        cands.sort()
        pairs, used_o, used_a = [], set(), set()
        for neg, _d, i, j in cands:
            if i in used_o or j in used_a:
                continue
            pairs.append((i, j))
            used_o.add(i)
            used_a.add(j)

        # C2 on pairs
        kind_tab = {}
        agree = {"kind": 0, "speaker": 0, "confidence": 0, "number": 0, "n": 0}
        for i, j in pairs:
            so, sa = o["statements"][i], a["statements"][j]
            agree["n"] += 1
            if so["kind"] == sa["kind"]:
                agree["kind"] += 1
            if so["speaker"] == sa["speaker"]:
                agree["speaker"] += 1
            if so["confidence"] == sa["confidence"]:
                agree["confidence"] += 1
            if has_number(so["quote"]) == has_number(sa["quote"]):
                agree["number"] += 1
            key = (so["kind"], sa["kind"])
            kind_tab[key] = kind_tab.get(key, 0) + 1

        # C4 vague words
        ov = [(v["word"], v.get("chart_feature", "NONE")) for v in o.get("vague_words", [])]
        av = [(v["word"], v.get("chart_feature", "NONE")) for v in a.get("vague_words", [])]
        ovw = {norm_term(w) for w, _ in ov}
        avw = {norm_term(w) for w, _ in av}
        shared = sorted(ovw & avw)
        feat_agree = 0
        feat_detail = []
        for w in shared:
            fo = next(f for x, f in ov if norm_term(x) == w)
            fa = next(f for x, f in av if norm_term(x) == w)
            ok = norm_term(fo or "").replace("none", "") == norm_term(fa or "").replace("none", "")
            if ok:
                feat_agree += 1
            feat_detail.append((w, fo, fa, ok))

        # C5 open slots
        osl = [s["question"] for s in o.get("open_slots", [])]
        asl = list(a.get("open_slots", []))
        def content_tokens(s):
            return {t for t in KC.search_tokens(s) if t not in STOP}
        slot_pairs = []
        for i, q1 in enumerate(osl):
            for j, q2 in enumerate(asl):
                shared_t = content_tokens(q1) & content_tokens(q2)
                if len(shared_t) >= 2:
                    slot_pairs.append((i, j, sorted(shared_t)))

        # C6 terms
        def tlist(rec, field):
            raw = rec.get(field, [])
            names = []
            for it in raw:
                names.append(norm_term(term_name(it, it)))
            return names
        od = tlist(o, "terms_defined")
        ad = tlist(a, "terms_defined")
        ou = tlist(o, "terms_used_undefined")
        au = tlist(a, "terms_used_undefined")
        def overlap_sets(x, y):
            xs, ys = set(x), set(y)
            inter = sorted(xs & ys)
            return inter, sorted(xs - ys), sorted(ys - xs)
        d_inter, d_oonly, d_aonly = overlap_sets(od, ad)
        u_inter, u_oonly, u_aonly = overlap_sets(ou, au)

        chunks.append({
            "cid": cid, "fid": fid,
            "n_orig": len(o["statements"]), "n_audit": len(a["statements"]),
            "n_pairs": len(pairs),
            "orig_only": [i for i in range(len(o["statements"])) if i not in used_o],
            "audit_only": [j for j in range(len(a["statements"])) if j not in used_a],
            "unloc_orig": [i for i, l in enumerate(o_loc) if l is None],
            "unloc_audit": [j for j, l in enumerate(a_loc) if l is None],
            "pairs": pairs, "agree": agree, "kind_tab": kind_tab,
            "ct_orig": o.get("content_type"), "ct_audit": a.get("content_type"),
            "v_o": len(ov), "v_a": len(av), "v_shared": shared,
            "v_feat_agree": feat_agree, "v_feat_detail": feat_detail,
            "s_o": len(osl), "s_a": len(asl), "s_pairs": slot_pairs,
            "d_inter": d_inter, "d_oonly": d_oonly, "d_aonly": d_aonly,
            "u_inter": u_inter, "u_oonly": u_oonly, "u_aonly": u_aonly,
        })

    write_md(chunks)
    tot_o = sum(c["n_orig"] for c in chunks)
    tot_a = sum(c["n_audit"] for c in chunks)
    tot_p = sum(c["n_pairs"] for c in chunks)
    print(f"chunks={len(chunks)} orig={tot_o} audit={tot_a} pairs={tot_p} "
          f"orig_only={sum(len(c['orig_only']) for c in chunks)} "
          f"audit_only={sum(len(c['audit_only']) for c in chunks)}")


def pct(n, d):
    return "n/a" if d == 0 else f"{100.0 * n / d:.1f}%"


def write_md(chunks):
    L = []
    L.append("# نتيجة المقارنة (C1–C6) — فحص عينات B30")
    L.append("")
    L.append("قاعدة التطابق المُعلنة قبل القراءة (PARAMETERS.md، قسم A1): يُطابق زوج (أصلي، فحص) إذا تداخلت نطاقا كلمتيهما بعد التطبيع N-06 بكلمة واحدة على الأقل، أو كان موضع بداية كلتيهما في حقل النص نفسه أو مجاورًا (بما لا يزيد عن حقل واحد). الأساس الموقعي لا المعنوي. ما لم يُطابق يُبلَّغ بالاتجاهين: أصلي-بدون-طابق (ORIGINAL_ONLY) وفحص-بدون-طابق (AUDIT_ONLY).")
    L.append("")
    tot_o = sum(c["n_orig"] for c in chunks)
    tot_a = sum(c["n_audit"] for c in chunks)
    tot_p = sum(c["n_pairs"] for c in chunks)
    tot_oo = sum(len(c["orig_only"]) for c in chunks)
    tot_ao = sum(len(c["audit_only"]) for c in chunks)

    L.append("## C1 — الأعداد والتطابق")
    L.append("")
    L.append("| المقطع | عدد العبارات (أصلي) | عدد العبارات (فحص) | أزواج مطابقة | ORIGINAL_ONLY | AUDIT_ONLY |")
    L.append("|---|---|---|---|---|---|")
    for c in chunks:
        L.append(f"| {c['cid']} | {c['n_orig']} | {c['n_audit']} | {c['n_pairs']} | {len(c['orig_only'])} | {len(c['audit_only'])} |")
    L.append(f"| **المجموع** | **{tot_o}** | **{tot_a}** | **{tot_p}** | **{tot_oo}** | **{tot_ao}** |")
    L.append("")
    L.append(f"نسبة الأزواج المطابقة إلى العبارات الأصلية: {pct(tot_p, tot_o)}؛ إلى عبارات الفحص: {pct(tot_p, tot_a)}.")
    L.append("")
    L.append("تفاصيل العبارات غير المطابقة (أرقام العبارات داخل سجل كل جانب):")
    for c in chunks:
        L.append(f"- {c['cid']}: ORIGINAL_ONLY = {c['orig_only']}؛ AUDIT_ONLY = {c['audit_only']}")
        if c["unloc_orig"] or c["unloc_audit"]:
            L.append(f"  - اقتباسات لم تُعثر عليها حرفيًا في النافذة: أصلية {c['unloc_orig']}، فحص {c['unloc_audit']}")
    L.append("")

    L.append("## C2 — الاتفاق على النوع / المتحدّث / الثقة / وجود الأرقام")
    L.append("")
    L.append("| المقطع | الأزواج | نوع متّفق | متحدّث متّفق | ثقة متّفق | وجود رقم متّفق |")
    L.append("|---|---|---|---|---|---|")
    for c in chunks:
        a = c["agree"]
        L.append(f"| {c['cid']} | {a['n']} | {a['kind']} ({pct(a['kind'], a['n'])}) | {a['speaker']} ({pct(a['speaker'], a['n'])}) | {a['confidence']} ({pct(a['confidence'], a['n'])}) | {a['number']} ({pct(a['number'], a['n'])}) |")
    n_all = sum(c["agree"]["n"] for c in chunks)
    k_all = sum(c["agree"]["kind"] for c in chunks)
    s_all = sum(c["agree"]["speaker"] for c in chunks)
    c_all = sum(c["agree"]["confidence"] for c in chunks)
    num_all = sum(c["agree"]["number"] for c in chunks)
    L.append(f"| **المجموع** | **{n_all}** | **{k_all} ({pct(k_all, n_all)})** | **{s_all} ({pct(s_all, n_all)})** | **{c_all} ({pct(c_all, n_all)})** | **{num_all} ({pct(num_all, n_all)})** |")
    L.append("")
    L.append("جدول خلط الأنواع (نوع الأصلي ← نوع الفحص) على كل الأزواج المطابقة:")
    L.append("")
    tab = {}
    for c in chunks:
        for (ko, ka), n in c["kind_tab"].items():
            tab[(ko, ka)] = tab.get((ko, ka), 0) + n
    kinds = sorted({k for pair in tab for k in pair})
    L.append("| الأصلي \\ الفحص | " + " | ".join(kinds) + " |")
    L.append("|---" * (len(kinds) + 1) + "|")
    for ko in kinds:
        row = [str(tab.get((ko, ka), 0)) for ka in kinds]
        L.append(f"| {ko} | " + " | ".join(row) + " |")
    L.append("")
    dis = sum(n for (ko, ka), n in tab.items() if ko != ka)
    L.append(f"إجمالي الأزواج المختلطة النوع: {dis} من {n_all} ({pct(dis, n_all)}).")
    L.append("")

    L.append("## C3 — نوع المحتوى (content_type) لكل مقطع")
    L.append("")
    L.append("| المقطع | الأصلي | الفحص | متّفق؟ |")
    L.append("|---|---|---|---|")
    for c in chunks:
        ok = "نعم" if c["ct_orig"] == c["ct_audit"] else "لا"
        L.append(f"| {c['cid']} | {c['ct_orig']} | {c['ct_audit']} | {ok} |")
    L.append("")

    L.append("## C4 — الكلمات الغامضة (vague_words): التداخل وتسمية الميزة")
    L.append("")
    L.append("| المقطع | عدد (أصلي) | عدد (فحص) | تداخل الكلمة | تسمية ميزة متّفق على المتداخل |")
    L.append("|---|---|---|---|---|")
    for c in chunks:
        L.append(f"| {c['cid']} | {c['v_o']} | {c['v_a']} | {len(c['v_shared'])} | {c['v_feat_agree']} من {len(c['v_shared'])} ({pct(c['v_feat_agree'], len(c['v_shared']))}) |")
    L.append("")
    for c in chunks:
        if c["v_feat_detail"]:
            L.append(f"- {c['cid']}: " + "; ".join(f"«{w}»: {f1} / {f2} ({'متفق' if ok else 'متباين'})" for w, f1, f2, ok in c["v_feat_detail"]))
    L.append("")

    L.append("## C5 — الفتحات المفتوحة (open_slots): الأعداد والتداخل")
    L.append("")
    L.append("| المقطع | عدد (أصلي) | عدد (فحص) | أزواج متداخلة (٢+ كلمة محتوى مشتركة) |")
    L.append("|---|---|---|---|")
    for c in chunks:
        L.append(f"| {c['cid']} | {c['s_o']} | {c['s_a']} | {len(c['s_pairs'])} |")
    L.append("")
    for c in chunks:
        for i, j, toks in c["s_pairs"]:
            L.append(f"- {c['cid']}: سؤال أصلي #{i} ↔ سؤال فحص #{j} (مشترك: {', '.join(toks[:6])})")
    L.append("")

    L.append("## C6 — المصطلحات (terms): التداخل")
    L.append("")
    L.append("| المقطع | معرف: متداخل / أصلي-فقط / فحص-فقط | مستخدم-غير-معرّف: متداخل / أصلي-فقط / فحص-فقط |")
    L.append("|---|---|---|")
    for c in chunks:
        L.append(f"| {c['cid']} | {len(c['d_inter'])} / {len(c['d_oonly'])} / {len(c['d_aonly'])} | {len(c['u_inter'])} / {len(c['u_oonly'])} / {len(c['u_aonly'])} |")
    L.append("")
    for c in chunks:
        if c["d_inter"]:
            L.append(f"- {c['cid']} مصطلحات معرّفة متداخلة: " + ", ".join(c["d_inter"]))
        if c["d_oonly"]:
            L.append(f"- {c['cid']} معرّفة أصلية فقط: " + ", ".join(c["d_oonly"]))
        if c["d_aonly"]:
            L.append(f"- {c['cid']} معرّفة فحص فقط: " + ", ".join(c["d_aonly"]))
        if c["u_inter"]:
            L.append(f"- {c['cid']} غير معرّفة متداخلة: " + ", ".join(c["u_inter"]))
        if c["u_oonly"]:
            L.append(f"- {c['cid']} غير معرّفة أصلية فقط: " + ", ".join(c["u_oonly"]))
        if c["u_aonly"]:
            L.append(f"- {c['cid']} غير معرّفة فحص فقط: " + ", ".join(c["u_aonly"]))
    L.append("")

    out = os.path.join(HERE, "COMPARE_RESULT.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print("wrote", out)


if __name__ == "__main__":
    main()
