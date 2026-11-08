#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""K7 PHASE 0 engine. Deterministic, stdlib only, English (code) + Arabic reports written separately.

Usage:
  python3 k7_phase0.py --corpus <extracted>/transcriptions_parent --work <dir outside repo> --repo <k7 dir> --step <name>

Steps: inventory | dups | chunks | citations | batches | timeline | l00 | speaker
Every step reads only committed-or-declared inputs and writes its own artefacts.
No transcript text is written into the repo: joined text and shingle files live in --work only.
"""

import argparse
import array
import hashlib
import json
import math
import os
import re
import struct
import sys
import zlib
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import k7_corpus as KC  # noqa: E402

# ---------------------------------------------------------------- parameters
# DECLARED BEFORE ANY RESULT IS LOOKED AT (mirrored in PARAMETERS.md).
TARGET_CHUNK_WORDS = 1300      # P-01
CHUNK_LOOKBACK_FRAC = 0.85     # P-02  candidate cut points start at 0.85*TARGET
TIME_GAP_MS = 1000             # P-03  an ASR entry gap >= 1s is treated as a natural break
SHINGLE_K = 8                  # P-04
NEAR_DUP_JACCARD = 0.60        # P-05
STRONG_DUP_JACCARD = 0.85      # P-06
DF_MAX_FOR_POSTING = 30        # P-07  shingles in more than 30 files are boilerplate, excluded from candidate generation
CANDIDATE_MIN_SHARED = 5       # P-08
CHUNK_DIFF_COVER = 0.90        # P-09  chunk of B is DIFF_ONLY if >= 90% of its shingles occur in A
BATCH_WORD_TARGET = 32000      # P-10
BATCH_CHUNK_CAP = 25           # P-11
DIFF_BATCH_WORD_TARGET = 100000  # P-12
L00_EDIT_FRAC = 0.12           # P-13
L00_EDIT_MIN = 2               # P-14
L00_MIN_FRAGMENT = 4           # P-15

FNV = 0x100000001B3
MASK64 = (1 << 64) - 1
FNV7 = pow(FNV, SHINGLE_K - 1, 1 << 64)


def log(msg):
    print(msg, flush=True)


def jdump(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)


# ---------------------------------------------------------------- shingles
def tok_hashes(tokens):
    return [zlib.crc32(t.encode("utf-8")) for t in tokens]


def shingle_hashes(tokens):
    """Deterministic 64-bit hashes of 8-token shingles (P-04).

    H = sum_{j=0..7} h(token_{i+j}) * FNV^(7-j)  mod 2^64, rolled.
    Files with 1..7 tokens yield exactly one shingle (the whole file).
    """
    n = len(tokens)
    if n == 0:
        return []
    if n < SHINGLE_K:
        hs = tok_hashes(tokens)
        h = 0
        for x in hs:
            h = (h * FNV + x) & MASK64
        return [h]
    hs = tok_hashes(tokens)
    out = []
    h = 0
    for x in hs[:SHINGLE_K]:
        h = (h * FNV + x) & MASK64
    out.append(h)
    for i in range(SHINGLE_K, n):
        h = (((h - hs[i - SHINGLE_K] * FNV7) & MASK64) * FNV + hs[i]) & MASK64
        out.append(h)
    return out


def write_u64(fh, values):
    a = array.array("Q", values)
    fh.write(a.tobytes())


def read_u64(fh, offset, count):
    fh.seek(offset)
    a = array.array("Q")
    a.frombytes(fh.read(count * 8))
    return a


# ---------------------------------------------------------------- inventory
def step_inventory(args):
    corpus = args.corpus
    work = args.work
    repo = args.repo
    joined_dir = os.path.join(work, "joined")
    os.makedirs(joined_dir, exist_ok=True)

    files = KC.corpus_files(corpus)
    log(f"[inventory] files={len(files)}")

    inv = []
    sh_index = {}
    sh_path = os.path.join(work, "shingles.bin")
    with open(sh_path, "wb") as shf:
        for n, rel in enumerate(files, start=1):
            fid = f"F{n:04d}"
            abs_p = os.path.join(corpus, rel)
            entries, anomaly = KC.load_entries(abs_p)
            joined, spans = KC.join_entries(entries)
            toks = KC.tokenize(joined)
            empty = sum(1 for e in entries if not e["text"])
            offsets = [e["offsetMS"] for e in entries if e["text"]] or [0]
            ends = [e["offsetMS"] + e["durationMS"] for e in entries if e["text"]] or [0]

            with open(os.path.join(joined_dir, f"{fid}.txt"), "w", encoding="utf-8") as f:
                f.write(joined)
            with open(os.path.join(joined_dir, f"{fid}.entries.json"), "w", encoding="utf-8") as f:
                json.dump(spans, f)
            with open(os.path.join(joined_dir, f"{fid}.meta.json"), "w", encoding="utf-8") as f:
                json.dump({"path": rel, "entry_count": len(entries)}, f)

            title, part = KC.parse_title_part(rel)
            src_sha = hashlib.sha256(open(abs_p, "rb").read()).hexdigest()
            j_sha = hashlib.sha256(joined.encode("utf-8")).hexdigest()

            sh = shingle_hashes([t[0] for t in toks])
            off = shf.tell()
            write_u64(shf, sorted(sh))
            sh_index[fid] = {"offset": off, "count": len(sh)}

            inv.append(
                {
                    "file_id": fid,
                    "path": rel,
                    "top_folder": KC.top_folder(rel),
                    "series": KC.top_folder(rel),
                    "title": title,
                    "part_number": part,
                    "entry_count": len(entries),
                    "empty_entries": empty,
                    "word_count": len(toks),
                    "words_whitespace": len(joined.split()),
                    "first_offsetMS": min(offsets),
                    "last_offsetMS": max(offsets),
                    "last_entry_endMS": max(ends),
                    "span_ms": max(ends) - min(offsets),
                    "sha256_source": src_sha,
                    "sha256_joined": j_sha,
                    "shingle_count": len(sh),
                    "structural_anomaly": anomaly,
                }
            )
            if n % 50 == 0:
                log(f"  {n}/{len(files)}")

    with open(os.path.join(repo, "FILE_INVENTORY.jsonl"), "w", encoding="utf-8") as f:
        for r in inv:
            f.write(jdump(r) + "\n")
    with open(os.path.join(work, "shingles.index.json"), "w", encoding="utf-8") as f:
        json.dump(sh_index, f)

    tot_w = sum(r["word_count"] for r in inv)
    tot_ws = sum(r["words_whitespace"] for r in inv)
    tot_e = sum(r["entry_count"] for r in inv)
    log(f"[inventory] words(N-05)={tot_w} words(split)={tot_ws} entries={tot_e}")
    with open(os.path.join(work, "inventory_totals.json"), "w", encoding="utf-8") as f:
        json.dump(
            {"files": len(inv), "words_primary": tot_w, "words_whitespace": tot_ws, "entries": tot_e},
            f,
        )


# ---------------------------------------------------------------- duplicates
def load_inventory(repo):
    out = []
    with open(os.path.join(repo, "FILE_INVENTORY.jsonl"), encoding="utf-8") as f:
        for line in f:
            out.append(json.loads(line))
    return out


def step_dups(args):
    work, repo = args.work, args.repo
    inv = load_inventory(repo)
    idx = json.load(open(os.path.join(work, "shingles.index.json"), encoding="utf-8"))
    sh_path = os.path.join(work, "shingles.bin")
    fid_order = [r["file_id"] for r in inv]
    pos = {fid: i for i, fid in enumerate(fid_order)}

    # ---- document frequency without a 2.6M-entry python dict:
    # concatenate all shingle hashes, sort once, count runs.
    with open(sh_path, "rb") as fh:
        allv = []
        for fid in fid_order:
            m = idx[fid]
            allv.extend(read_u64(fh, m["offset"], m["count"]))
    log(f"[dups] total shingles={len(allv)}")
    allv.sort()
    df = {}
    i = 0
    n = len(allv)
    while i < n:
        j = i + 1
        v = allv[i]
        while j < n and allv[j] == v:
            j += 1
        c = j - i
        if c >= 2 and c <= DF_MAX_FOR_POSTING:
            df[v] = c
        i = j
    del allv
    log(f"[dups] shingles with 2..{DF_MAX_FOR_POSTING} files = {len(df)}")

    # ---- postings
    postings = defaultdict(list)
    with open(sh_path, "rb") as fh:
        for fid in fid_order:
            m = idx[fid]
            for v in set(read_u64(fh, m["offset"], m["count"])):
                if v in df:
                    postings[v].append(pos[fid])
    pair_shared = Counter()
    for v, lst in postings.items():
        if len(lst) < 2:
            continue
        for a in range(len(lst)):
            for b in range(a + 1, len(lst)):
                pair_shared[(lst[a], lst[b])] += 1
    del postings
    log(f"[dups] candidate pairs={len(pair_shared)}")

    # ---- exact Jaccard for candidates via sorted-array merge
    def exact_jaccard(ia, ib):
        ma, mb = idx[fid_order[ia]], idx[fid_order[ib]]
        with open(sh_path, "rb") as fh:
            A = read_u64(fh, ma["offset"], ma["count"])
            B = read_u64(fh, mb["offset"], mb["count"])
        i = j = inter = 0
        while i < len(A) and j < len(B):
            if A[i] == B[j]:
                inter += 1
                i += 1
                j += 1
            elif A[i] < B[j]:
                i += 1
            else:
                j += 1
        union = len(A) + len(B) - inter
        return (inter / union if union else 0.0), inter, union, set(A), set(B)

    records = []
    near_sets = {}
    for (ia, ib), shared in sorted(pair_shared.items()):
        if shared < CANDIDATE_MIN_SHARED:
            continue
        fid_a, fid_b = fid_order[ia], fid_order[ib]
        ra, rb = inv[ia], inv[ib]
        if ra["sha256_joined"] == rb["sha256_joined"]:
            records.append(
                {
                    "kind": "EXACT_DUPLICATE",
                    "file_a": fid_a,
                    "path_a": ra["path"],
                    "file_b": fid_b,
                    "path_b": rb["path"],
                    "method": "sha256 of joined text equal (N-03 join, N-02 per-entry clean)",
                    "jaccard": 1.0,
                    "read_full": fid_a,
                    "diff_check": fid_b,
                    "score_source": "sha256",
                }
            )
            continue
        jac, inter, union, seta, setb = exact_jaccard(ia, ib)
        if 0.25 <= jac < NEAR_DUP_JACCARD:
            # shown so that nothing is hidden by the declared 0.60 cut; NOT a duplicate claim
            records.append(
                {
                    "kind": "NEAR_DUPLICATE_BELOW_THRESHOLD",
                    "file_a": fid_a,
                    "path_a": ra["path"],
                    "file_b": fid_b,
                    "path_b": rb["path"],
                    "method": f"{SHINGLE_K}-token shingle Jaccard on 64-bit deterministic hashes",
                    "jaccard": round(jac, 4),
                    "shared_shingles": inter,
                    "union_shingles": union,
                    "read_full": "BOTH (below the declared NEAR_DUP_JACCARD threshold)",
                    "diff_check": None,
                }
            )
        if jac >= NEAR_DUP_JACCARD:
            near_sets[(fid_a, fid_b)] = (seta, setb)
            band = "STRONG" if jac >= STRONG_DUP_JACCARD else "WEAK"
            records.append(
                {
                    "kind": "NEAR_DUPLICATE",
                    "band": band,
                    "file_a": fid_a,
                    "path_a": ra["path"],
                    "file_b": fid_b,
                    "path_b": rb["path"],
                    "method": f"{SHINGLE_K}-token shingle Jaccard on 64-bit deterministic hashes",
                    "jaccard": round(jac, 4),
                    "shared_shingles": inter,
                    "union_shingles": union,
                    "read_full": fid_a,
                    "diff_check": fid_b if band == "STRONG" else None,
                    "score_source": "exact-set-merge",
                }
            )

    # ---- chunk-level containment for near/strong pairs (P-09)
    chunk_index = {}
    ci_path = os.path.join(repo, "CHUNK_INDEX.jsonl")
    have_chunks = os.path.exists(ci_path)
    if have_chunks:
        with open(ci_path, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                chunk_index.setdefault(r["file_id"], []).append(r)

    def chunk_shingles(fid, ch):
        joined = open(os.path.join(work, "joined", f"{fid}.txt"), encoding="utf-8").read()
        seg = joined[ch["char_start"]:ch["char_end"]]
        toks = KC.tokenize(seg)
        return set(shingle_hashes([t[0] for t in toks]))

    if have_chunks:
        for rec in records:
            if rec["kind"] == "NEAR_DUPLICATE":
                fa, fb = rec["file_a"], rec["file_b"]
                if (fa, fb) not in near_sets:
                    continue
                seta, _setb = near_sets[(fa, fb)]
                rows = []
                for ch in chunk_index.get(fb, []):
                    cs = chunk_shingles(fb, ch)
                    cover = (len(cs & seta) / len(cs)) if cs else 0.0
                    rows.append(
                        {
                            "chunk_id": ch["chunk_id"],
                            "coverage_in_a": round(cover, 3),
                            "mode": "DIFF_ONLY" if cover >= CHUNK_DIFF_COVER else "FULL_READ",
                        }
                    )
                rec["chunk_modes"] = rows
            elif rec["kind"] == "EXACT_DUPLICATE":
                rec["chunk_modes"] = [
                    {"chunk_id": ch["chunk_id"], "coverage_in_a": 1.0, "mode": "DIFF_ONLY"}
                    for ch in chunk_index.get(rec["file_b"], [])
                ]

    # ---- multi-part groups (declared fact, never a merge)
    by_title = defaultdict(list)
    for r in inv:
        by_title[(r["top_folder"], r["title"])].append(r)
    for (folder, title), rs in sorted(by_title.items()):
        if len(rs) < 2:
            continue
        parts = sorted([x["part_number"] for x in rs if x["part_number"] is not None])
        records.append(
            {
                "kind": "MULTI_PART",
                "folder": folder,
                "title": title,
                "file_ids": [x["file_id"] for x in sorted(rs, key=lambda y: y["path"])],
                "parts": parts,
                "part_gap": bool(parts and parts != list(range(1, len(parts) + 1))),
                "method": "same folder + same title after removing the trailing -NNN part suffix",
                "read_full": "ALL",
                "note": "parts are continuations, not duplicates; every part is read in full",
            }
        )

    # ---- same title in a different series (cross-series re-recording)
    by_title_only = defaultdict(list)
    for r in inv:
        by_title_only[r["title"]].append(r)
    for title, rs in sorted(by_title_only.items()):
        folders = {x["top_folder"] for x in rs}
        if len(folders) < 2:
            continue
        records.append(
            {
                "kind": "TITLE_MATCH_ACROSS_SERIES",
                "title": title,
                "folders": sorted(folders),
                "file_ids": [x["file_id"] for x in sorted(rs, key=lambda y: y["path"])],
                "method": "identical file title (part suffix removed) in >1 top-level folder",
                "jaccard": None,
                "read_full": "ALL (title match alone is not a similarity claim)",
            }
        )

    with open(os.path.join(repo, "DUPLICATE_MAP.jsonl"), "w", encoding="utf-8") as f:
        for r in records:
            f.write(jdump(r) + "\n")

    n_exact = sum(1 for r in records if r["kind"] == "EXACT_DUPLICATE")
    n_strong = sum(1 for r in records if r["kind"] == "NEAR_DUPLICATE" and r.get("band") == "STRONG")
    n_weak = sum(1 for r in records if r["kind"] == "NEAR_DUPLICATE" and r.get("band") == "WEAK")
    n_mp = sum(1 for r in records if r["kind"] == "MULTI_PART")
    n_tm = sum(1 for r in records if r["kind"] == "TITLE_MATCH_ACROSS_SERIES")
    log(f"[dups] exact={n_exact} near_strong={n_strong} near_weak={n_weak} multipart={n_mp} titlematch={n_tm}")


# ---------------------------------------------------------------- chunks
def step_chunks(args):
    corpus, work, repo = args.corpus, args.work, args.repo
    inv = load_inventory(repo)
    rows = []
    stats = {"max_words": 0, "min_words": 10**9, "gap_cuts": 0, "forced_cuts": 0}
    for r in inv:
        fid = r["file_id"]
        entries, _ = KC.load_entries(os.path.join(corpus, r["path"]))
        joined, spans = KC.join_entries(entries)
        # per non-empty entry: char range + word count
        seq = []
        for sp in spans:
            seg = joined[sp[0]:sp[1]]
            seq.append({"cs": sp[0], "ce": sp[1], "off": sp[2], "end": sp[2] + sp[3],
                        "w": len(KC.TOKEN_RE.findall(seg))})
        # gap between consecutive entries
        for i in range(len(seq) - 1):
            seq[i]["gap"] = seq[i + 1]["off"] - seq[i]["end"]
        if seq:
            seq[-1]["gap"] = 0

        start_i = 0
        cnum = 0
        while start_i < len(seq):
            acc = 0
            i = start_i
            while i < len(seq):
                acc += seq[i]["w"]
                if acc >= TARGET_CHUNK_WORDS:
                    break
                i += 1
            if i >= len(seq):
                cut = len(seq) - 1
            else:
                lo_w = CHUNK_LOOKBACK_FRAC * TARGET_CHUNK_WORDS
                cum = 0
                cands = []
                for p in range(start_i, i + 1):
                    cum += seq[p]["w"]
                    if cum >= lo_w:
                        cands.append(p)
                if not cands:
                    cands = [i]
                best = max(cands, key=lambda p: (seq[p]["gap"], p))
                cut = best
                if seq[best]["gap"] >= TIME_GAP_MS:
                    stats["gap_cuts"] += 1
                else:
                    stats["forced_cuts"] += 1
            cnum += 1
            cid = f"{fid}#{cnum:03d}"
            cs, ce = seq[start_i]["cs"], seq[cut]["ce"]
            words = len(KC.TOKEN_RE.findall(joined[cs:ce]))
            rows.append(
                {
                    "chunk_id": cid,
                    "file_id": fid,
                    "seq": cnum,
                    "char_start": cs,
                    "char_end": ce,
                    "word_start": None,
                    "word_end": None,
                    "offset_startMS": seq[start_i]["off"],
                    "offset_endMS": seq[cut]["end"],
                    "words": words,
                    "cut_reason": "TIME_GAP" if seq[cut]["gap"] >= TIME_GAP_MS else "ENTRY",
                    "entries": cut - start_i + 1,
                }
            )
            stats["max_words"] = max(stats["max_words"], words)
            stats["min_words"] = min(stats["min_words"], words)
            start_i = cut + 1
    # word-level offsets into the joined text (cumulative, so word_start/word_end are global token indices)
    per_file_cursor = defaultdict(int)
    with open(os.path.join(repo, "CHUNK_INDEX.jsonl"), "w", encoding="utf-8") as f:
        for row in rows:
            fid = row["file_id"]
            base = per_file_cursor[fid]
            row["word_start"] = base
            row["word_end"] = base + row["words"]
            per_file_cursor[fid] = row["word_end"]
            f.write(jdump(row) + "\n")
    log(f"[chunks] n={len(rows)} min={stats['min_words']} max={stats['max_words']} "
        f"gapcuts={stats['gap_cuts']} entcuts={stats['forced_cuts']}")


# ---------------------------------------------------------------- citations
QUOTE_KEYS = ["quote"]
PATH_KEYS = ["path", "transcript_id", "file", "source_label", "source_labels", "corpus_path", "source", "transcript"]
TRANS_PATH_RE = re.compile(r"transcriptions/[^\s'\"\]|,]+\.json")


def resolve_path(obj):
    for k in PATH_KEYS:
        if k not in obj:
            continue
        v = obj[k]
        if isinstance(v, str):
            m = TRANS_PATH_RE.search(v)
            if m:
                return m.group(0)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, str):
                    m = TRANS_PATH_RE.search(item)
                    if m:
                        return m.group(0)
    # last resort: any string value that embeds a transcriptions/... path
    for v in obj.values():
        if isinstance(v, str):
            m = TRANS_PATH_RE.search(v)
            if m:
                return m.group(0)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, str):
                    m = TRANS_PATH_RE.search(item)
                    if m:
                        return m.group(0)
    return None


def step_citations(args):
    repo, work = args.repo, args.work
    refs = [
        ("K1", "441a963032db7d2568898a9fbdb89fa0f2b65bba"),
        ("K2", "ffe7add4a187d3fb25c27458751b722e3430fb53"),
        ("K3", "567460bf4fa0773ef1633738b72a61399cfcf3e3"),
        ("U2", "88a06d68ab3f6badbc10e80d12739f3c403dabfa"),
        ("K4a", "e1befae64a1d025e39f816796b557402bf762405"),
        ("K4b", "54185cc1d6693eec716a84fc64ee3dd80c3cff03"),
        ("K5", "a3eb25e4c59190651ea2603c4e5ebd5fc3aa029d"),
        ("DESIGN", "6f9e66b0c29e866c39acdca23345a3fa85624517"),
    ]
    inv = load_inventory(repo)
    f2folder = {r["path"]: r["top_folder"] for r in inv}
    all_folders = sorted({r["top_folder"] for r in inv})

    per_ref = {}
    unique_quotes = {}      # dedupe key -> record
    families = {}           # (ref, relpath) -> {"quote_field":bool,"records":n,"with_path":n,"with_quote":n,"with_quote_and_path":n}
    unresolved = 0
    for ref, sha in refs:
        root = os.path.join(args.refs_dir, ref)
        counts = Counter()
        for dirpath, _dn, fns in os.walk(root):
            if os.sep + "github" + os.sep in dirpath:
                continue
            for fn in fns:
                if not fn.endswith(".jsonl"):
                    continue
                p = os.path.join(dirpath, fn)
                rel = os.path.relpath(p, root)
                if "huddleston_study" not in rel:
                    continue
                recs = 0
                with_path = with_quote = both = 0
                with open(p, encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            o = json.loads(line)
                        except Exception:
                            continue
                        if not isinstance(o, dict):
                            continue
                        recs += 1
                        q = o.get("quote")
                        has_q = isinstance(q, str) and len(q.strip()) > 0
                        path = resolve_path(o)
                        if path:
                            with_path += 1
                        if has_q:
                            with_quote += 1
                        if has_q and path:
                            both += 1
                            folder = f2folder.get(path)
                            if folder is None:
                                unresolved += 1
                                continue
                            counts[folder] += 1
                            key = hashlib.sha256((path + "\x00" + q).encode("utf-8")).hexdigest()
                            if key not in unique_quotes:
                                unique_quotes[key] = {"path": path, "folder": folder, "quote": q, "refs": []}
                            if ref not in unique_quotes[key]["refs"]:
                                unique_quotes[key]["refs"].append(ref)
                families[f"{ref}:{rel}"] = {
                    "records": recs,
                    "with_path": with_path,
                    "with_quote": with_quote,
                    "with_quote_and_path": both,
                }
        per_ref[ref] = dict(counts)

    unique_counts = Counter()
    for v in unique_quotes.values():
        unique_counts[v["folder"]] += 1

    with open(os.path.join(work, "citations.json"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "folders": all_folders,
                "per_ref": per_ref,
                "unique": dict(unique_counts),
                "unique_total": len(unique_quotes),
                "unresolved_paths": unresolved,
                "families": families,
            },
            f,
        )
    log(f"[citations] unique quotes={len(unique_quotes)} unresolved_paths={unresolved}")
    for ref in per_ref:
        log(f"  {ref}: {sum(per_ref[ref].values())}")


# ---------------------------------------------------------------- timeline
DATE_NAME_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
AMBIG_DATE_RE = re.compile(r"(?<!\d)(\d{1,2})[-_](\d{1,2})[-_](\d{2})(?!\d)")
MONTH_YEAR_RE = re.compile(
    r"\b(january|february|march|april|may|june|july|august|september|october|november|december)"
    r"[\s\-_]+(\d{1,2})?[,\s\-_]*(\d{4})\b",
    re.I,
)
YEAR_RE = re.compile(r"\b(19[5-9]\d|20[0-2]\d)\b")


def step_timeline(args):
    corpus, work, repo = args.corpus, args.work, args.repo
    inv = load_inventory(repo)
    rows = []
    for r in inv:
        folder = r["top_folder"]
        fname = os.path.basename(r["path"])
        folder_years = sorted({int(y) for y in YEAR_RE.findall(folder)})
        name_date = None
        m = DATE_NAME_RE.search(fname)
        if m:
            name_date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        else:
            m2 = MONTH_YEAR_RE.search(fname)
            if m2:
                name_date = f"{m2.group(1)} {m2.group(2) or ''} {m2.group(3)}".strip()
            else:
                m5 = AMBIG_DATE_RE.search(fname.replace("-001", ""))
                if m5:
                    name_date = "AMBIGUOUS_NUMERIC_TOKEN:" + m5.group(0)
        # years stated inside the text, with first offset
        joined = open(os.path.join(work, "joined", f"{r['file_id']}.txt"), encoding="utf-8").read()
        spans = json.load(open(os.path.join(work, "joined", f"{r['file_id']}.entries.json")))
        years = Counter()
        first_pos = {}
        for m3 in YEAR_RE.finditer(joined):
            y = int(m3.group(1))
            if y < 2000:      # lessons talk about 2016..2023; pre-2000 years are usually price levels, keep separately
                continue
            years[y] += 1
            first_pos.setdefault(y, m3.start())
        years_txt = {
            str(y): {
                "count": c,
                "offsetMS": (KC.entry_at(spans, first_pos[y]) or [0, 0, 0])[2],
            }
            for y, c in sorted(years.items())
        }
        # order within series: only if the text states lesson/part numbering
        ord_state = "UNVERIFIED"
        ord_evidence = ""
        m4 = re.search(r"\b(lesson|part|episode)\s+(number\s+)?(\d{1,3}|one|two|three|four|five|six|seven|eight|nine|ten)\b", joined, re.I)
        if m4:
            ord_state = "NUMBERING_PHRASE_PRESENT"
            off = (KC.entry_at(spans, m4.start()) or [0, 0, 0])[2]
            ord_evidence = {"phrase": m4.group(0)[:40], "offsetMS": off}
        date_state = "DATE_UNKNOWN"
        if name_date and name_date.startswith("AMBIGUOUS"):
            date_state = "DATE_TOKEN_IN_FILENAME_AMBIGUOUS"
        elif name_date:
            date_state = "DATE_IN_FILENAME"
        elif folder_years:
            date_state = "YEAR_IN_FOLDER_ONLY"
        elif years_txt:
            date_state = "YEAR_IN_TEXT_ONLY"
        rows.append(
            {
                "file_id": r["file_id"],
                "path": r["path"],
                "folder_years": folder_years,
                "filename_date": name_date or "NOT_STATED",
                "years_stated_in_text": years_txt,
                "date_state": date_state,
                "order_within_series": ord_state,
                "series_order_source": "FILENAME_PART_NUMBER" if (r["part_number"] or 1) > 1 else "NONE",
                "order_evidence": ord_evidence,
                "part_number_from_filename": r["part_number"],
            }
        )
    with open(os.path.join(repo, "TIMELINE_FACTS.jsonl"), "w", encoding="utf-8") as f:
        for r in rows:
            f.write(jdump(r) + "\n")
    c = Counter(r["date_state"] for r in rows)
    log(f"[timeline] {dict(c)}")


# ---------------------------------------------------------------- batches
def folder_sort_key(folder):
    ys = [int(y) for y in YEAR_RE.findall(folder)]
    return (min(ys) if ys else 9999, folder)


def step_batches(args):
    repo = args.repo
    inv = {r["file_id"]: r for r in load_inventory(repo)}
    chunks = []
    with open(os.path.join(repo, "CHUNK_INDEX.jsonl"), encoding="utf-8") as f:
        for line in f:
            chunks.append(json.loads(line))

    # which chunks are DIFF_ONLY (exact duplicates and strong-near fully covered parts)
    diff_only = {}
    dup_pairs = []
    dpath = os.path.join(repo, "DUPLICATE_MAP.jsonl")
    if os.path.exists(dpath):
        with open(dpath, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                if r.get("kind") in ("EXACT_DUPLICATE", "NEAR_DUPLICATE"):
                    dup_pairs.append(r)
                    for cm in r.get("chunk_modes") or []:
                        if cm["mode"] == "DIFF_ONLY":
                            diff_only[cm["chunk_id"]] = r["read_full"]

    order = []
    for c in chunks:
        f = inv[c["file_id"]]
        order.append((folder_sort_key(f["top_folder"]), f["path"], c["seq"], c))
    order.sort(key=lambda x: (x[0], x[1], x[2]))

    full, diff = [], []
    for _k, _p, _s, c in order:
        (diff if c["chunk_id"] in diff_only else full).append(c)

    def pack(chs, word_target, chunk_cap):
        batches, cur, curw = [], [], 0
        for c in chs:
            if cur and (curw + c["words"] > word_target or len(cur) >= chunk_cap):
                batches.append(cur)
                cur, curw = [], 0
            cur.append(c)
            curw += c["words"]
        if cur:
            batches.append(cur)
        return batches

    fb = pack(full, BATCH_WORD_TARGET, BATCH_CHUNK_CAP)
    db = pack(diff, DIFF_BATCH_WORD_TARGET, 10**9)

    out = []
    idx = 0
    for b in fb:
        idx += 1
        folders = sorted({inv[c["file_id"]]["top_folder"] for c in b})
        out.append(
            {
                "batch_id": f"B{idx:02d}",
                "kind": "FULL_READ",
                "chunks": len(b),
                "words": sum(c["words"] for c in b),
                "files": sorted({c["file_id"] for c in b}),
                "folders": folders,
                "first_chunk": b[0]["chunk_id"],
                "last_chunk": b[-1]["chunk_id"],
            }
        )
    didx = 0
    for b in db:
        didx += 1
        folders = sorted({inv[c["file_id"]]["top_folder"] for c in b})
        out.append(
            {
                "batch_id": f"D{didx:02d}",
                "kind": "DIFF_CHECK",
                "chunks": len(b),
                "words": sum(c["words"] for c in b),
                "files": sorted({c["file_id"] for c in b}),
                "folders": folders,
                "first_chunk": b[0]["chunk_id"],
                "last_chunk": b[-1]["chunk_id"],
            }
        )
    with open(os.path.join(repo, "BATCH_INDEX.jsonl"), "w", encoding="utf-8") as f:
        for r in out:
            f.write(jdump(r) + "\n")
    log(f"[batches] full={len(fb)} diff={len(db)} total_chunks_full={sum(x['chunks'] for x in out if x['kind']=='FULL_READ')} diff_chunks={sum(x['chunks'] for x in out if x['kind']=='DIFF_CHECK')}")


# ---------------------------------------------------------------- L00 test
L00 = [
    ("S1", "If you don't know what the Daily Chart is doing, you are gambling"),
    ("S2", "When the Monthly and Weekly are in conflict, you sit on your hands"),
    ("S3", "Narrative is not support and resistance"),
    ("S4", "IPDA is a computer program. It only looks for two things"),
]


def levenshtein_tokens(a, b):
    la, lb = len(a), len(b)
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        cur = [i] + [0] * lb
        ai = a[i - 1]
        for j in range(1, lb + 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (0 if ai == b[j - 1] else 1))
        prev = cur
    return prev[lb]


def best_fragment(qtoks, file_norm_text, qtok_str):
    """Longest contiguous run of quote tokens found as an exact substring anywhere."""
    n = len(qtoks)
    best = (0, -1, -1)   # (length, q_start, char_pos)
    for k in range(n):
        if k + 2 > n:
            break
        two = " ".join(qtoks[k:k + 2])
        p = file_norm_text.find(two)
        if p < 0:
            continue
        L = 2
        while k + L < n:
            nxt = " ".join(qtoks[k:k + L + 1])
            if nxt in file_norm_text:
                L += 1
            else:
                break
        if L > best[0] or (L == best[0] and best[1] < 0):
            best = (L, k, p)
    return best


def step_l00(args):
    corpus, work, repo = args.corpus, args.work, args.repo
    inv = load_inventory(repo)
    results = []
    for sid, s in L00:
        qtoks = KC.search_tokens(s)
        q = " ".join(qtoks)
        n = len(qtoks)
        hits = []          # exact
        variants = []      # edit-distance
        frags = []         # partial
        max_allow = max(L00_EDIT_MIN, int(math.ceil(L00_EDIT_FRAC * n)))
        for r in inv:
            fid = r["file_id"]
            joined = open(os.path.join(work, "joined", f"{fid}.txt"), encoding="utf-8").read()
            spans = json.load(open(os.path.join(work, "joined", f"{fid}.entries.json")))
            nt = KC.search_text(joined)
            pos = nt.find(q)
            if pos >= 0:
                hits.append({"file_id": fid, "path": r["path"], "char_pos": pos,
                             "tokens_from_file_start": nt[:pos].count(" ") + (1 if pos else 0)})
            # ASR variant search: sliding window, multiset prefilter, then edit distance
            ftoks = nt.split()
            qc = Counter(qtoks)
            for w in {n - 1, n, n + 1}:
                if w < 3 or w > len(ftoks):
                    continue
                win = Counter(ftoks[:w])
                score = sum(min(win[t], qc[t]) for t in qc)
                for i in range(0, len(ftoks) - w + 1):
                    if i:
                        win[ftoks[i - 1]] -= 1
                        if win[ftoks[i - 1]] == 0:
                            del win[ftoks[i - 1]]
                        win[ftoks[i + w - 1]] += 1
                        score = sum(min(win[t], qc[t]) for t in qc)
                    if score < n - max_allow:
                        continue
                    seg = ftoks[i:i + w]
                    d = levenshtein_tokens(qtoks, seg)
                    if 0 < d <= max_allow and " ".join(seg) != q:
                        variants.append({"file_id": fid, "path": r["path"], "distance": d,
                                         "window_words": w, "window": " ".join(seg)})
            # partial fragments (skip if exact or variant found in this file)
            if pos < 0 and not any(v["file_id"] == fid for v in variants):
                L, k, p = best_fragment(qtoks, nt, q)
                if L >= L00_MIN_FRAGMENT:
                    frags.append({"file_id": fid, "path": r["path"], "length": L,
                                  "fragment": " ".join(qtoks[k:k + L]), "q_start": k, "char_pos": p})
        hits.sort(key=lambda h: h["char_pos"])
        variants.sort(key=lambda v: (v["distance"], v["file_id"]))
        frags.sort(key=lambda x: (-x["length"], x["file_id"]))
        if hits:
            status = "FOUND_EXACT"
        elif variants:
            status = "FOUND_VARIANT"
        elif frags:
            status = "FOUND_PARTIAL"
        else:
            status = "NOT_FOUND"
        results.append(
            {
                "id": sid,
                "string_label": "USER_LEAD_UNVERIFIED",
                "search_normalisation": "N-06 (lowercase, contractions expanded, non-alphanumeric -> space, tokens joined by one space)",
                "quote_tokens": n,
                "status": status,
                "exact_hits": hits[:10],
                "variant_hits": variants[:10],
                "variant_total": len(variants),
                "fragments": frags[:5],
                "fragment_total": len(frags),
                "max_edit_allowed": max_allow,
            }
        )
        log(f"[l00] {sid}: {status} exact={len(hits)} variant={len(variants)} frag={len(frags)}")
    with open(os.path.join(work, "l00.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)


# ---------------------------------------------------------------- probe (verbatim evidence for the L00 report)
# Probes declared BEFORE looking at the results: the four lead sentences' distinguishing tails and
# the standalone phrases the leads depend on. Each probe is a search-normalised phrase (N-06).
PROBES = [
    ("S1_TAIL", "you are gambling"),
    ("S1_ALT_TAIL", "you are playing with"),
    ("S1_HEAD", "if you do not know what the daily chart"),
    ("S1_CORE", "what the daily chart is doing"),
    ("S2_PHRASE", "sit on your hands"),
    ("S2_SENTENCE", "monthly and weekly are in conflict"),
    ("S2_HEAD", "when the monthly and weekly"),
    ("S2_CONFLICT", "in conflict"),
    ("S3_SENTENCE", "narrative is not support and resistance"),
    ("S3_FRAG", "is not support and resistance"),
    ("S3_TERM", "market narrative"),
    ("S4_SENTENCE", "ipda is a computer program"),
    ("S4_ACRONYM", "ipda"),
    ("S4_FULLNAME", "interbank price delivery algorithm"),
    ("S4_TAIL", "it only looks for two things"),
    ("S4_TWOTHINGS", "two things"),
]


def step_probe(args):
    work, repo = args.work, args.repo
    inv = load_inventory(repo)
    res = {label: {"probe": ph, "files": 0, "occurrences": 0, "examples": []} for label, ph in PROBES}
    for r in inv:
        fid = r["file_id"]
        joined = open(os.path.join(work, "joined", f"{fid}.txt"), encoding="utf-8").read()
        toks, spans = KC.norm_tokens_with_pos(joined)
        if not toks:
            continue
        posidx = None
        flat = " ".join(toks)
        for label, ph in PROBES:
            ptoks = ph.split()
            c = flat.count(ph)
            if not c:
                continue
            d = res[label]
            d["files"] += 1
            d["occurrences"] += c
            if len(d["examples"]) >= 4:
                continue
            start = flat.find(ph)
            ti = flat[:start].count(" ")
            n = len(ptoks)
            lo = max(0, ti - 6)
            hi = min(len(toks), ti + n + 8)
            if hi - lo > 25:
                hi = lo + 25
            q = joined[spans[lo][0]:spans[hi - 1][1]]
            off = (KC.entry_at(json.load(open(os.path.join(work, "joined", f"{fid}.entries.json"))), spans[lo][0]) or [0, 0, 0])[2]
            d["examples"].append(
                {
                    "file_id": fid,
                    "path": r["path"],
                    "offsetMS": off,
                    "quote": q,
                    "quote_words": len(q.split()),
                    "probe_found_in_quote": KC.search_text(q).find(ph) >= 0,
                }
            )
    with open(os.path.join(work, "probes.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    for label, _ph in PROBES:
        d = res[label]
        log(f"[probe] {label}: files={d['files']} occ={d['occurrences']}")


# ---------------------------------------------------------------- speaker risk
CUES = {
    "CHAT_OR_COMMENTS": r"\b(in the chat|chat box|live chat|in the comments|comments section|someone asked|somebody asked|you asked|you guys asked|a lot of you asked|asked me)\b",
    "AUDIENCE_QUESTION": r"\b(does that make sense|make sense to you|any questions|you guys following|are you with me|do you see that|you see how)\b",
    "THANKS_TO_HIM": r"\b(thank you michael|thanks michael|thank you for that|appreciate it|thank you so much)\b",
    "LIVE_MARKER": r"\b(welcome back|we are live|we're live|good morning everyone|good afternoon everyone|hello everyone|hey everybody|good evening)\b",
    "SECOND_VOICE": r"\b(he asked|she asked|the question was|you are asking|your question)\b",
}


def step_speaker(args):
    work, repo = args.work, args.repo
    inv = load_inventory(repo)
    per_folder = defaultdict(lambda: {"files": 0, "words": 0, "cues": Counter(), "hit_files": defaultdict(list), "anyCue": 0})
    for r in inv:
        fid = r["file_id"]
        joined = open(os.path.join(work, "joined", f"{fid}.txt"), encoding="utf-8").read()
        nt = KC.search_text(joined)
        d = per_folder[r["top_folder"]]
        d["files"] += 1
        d["words"] += r["word_count"]
        any_hit = False
        for name, pat in CUES.items():
            c = len(re.findall(pat, nt))
            if c:
                d["cues"][name] += c
                d["hit_files"][name].append(fid)
                any_hit = True
        if any_hit:
            d["anyCue"] += 1
    rows = []
    for folder, d in per_folder.items():
        share = d["anyCue"] / d["files"] if d["files"] else 0
        q_share = len(d["hit_files"]["CHAT_OR_COMMENTS"]) / d["files"] if d["files"] else 0
        t_share = len(d["hit_files"]["THANKS_TO_HIM"]) / d["files"] if d["files"] else 0
        if q_share >= 0.5 or t_share >= 0.3:
            risk = "HIGH"
        elif q_share >= 0.2 or t_share >= 0.1 or share >= 0.9:
            risk = "MEDIUM"
        elif share >= 0.5:
            risk = "LOW_MEDIUM"
        elif share > 0:
            risk = "LOW"
        else:
            risk = "UNKNOWN_NO_CUE"
        rows.append(
            {
                "folder": folder,
                "files": d["files"],
                "words": d["words"],
                "files_with_any_cue": d["anyCue"],
                "share_any_cue": round(share, 3),
                "cue_counts": dict(d["cues"]),
                "files_chat_or_comments": len(d["hit_files"]["CHAT_OR_COMMENTS"]),
                "files_thanks_to_him": len(d["hit_files"]["THANKS_TO_HIM"]),
                "files_live_marker": len(d["hit_files"]["LIVE_MARKER"]),
                "sample_files": {k: v[:10] for k, v in d["hit_files"].items()},
                "other_voice_risk": risk,
            }
        )
    rows.sort(key=lambda x: (-x["share_any_cue"], x["folder"]))
    with open(os.path.join(work, "speaker.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    log("[speaker] " + ", ".join(f"{r['folder']}={r['other_voice_risk']}" for r in rows[:5]) + " ...")


STEPS = {
    "inventory": step_inventory,
    "dups": step_dups,
    "chunks": step_chunks,
    "citations": step_citations,
    "timeline": step_timeline,
    "batches": step_batches,
    "l00": step_l00,
    "probe": step_probe,
    "speaker": step_speaker,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--refs-dir", default="")
    ap.add_argument("--step", required=True)
    args = ap.parse_args()
    if args.step == "all":
        for name in ["inventory", "chunks", "dups", "citations", "timeline", "batches", "l00", "probe", "speaker"]:
            log(f"===== {name}")
            STEPS[name](args)
    else:
        STEPS[args.step](args)


if __name__ == "__main__":
    main()
