#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""K7 shared corpus loader. Deterministic, stdlib only.

Corpus (outside the repo, never copied in):
  newsqlguru/ict-index @ e8c40a8dae5ea6689926f28c7184ce3e2fb85b9c
  tarball sha256 4213e692f7c978dab8fe5ba124d34d887f17316c89d27bb2a7406fd3776f769d

NORMALISATION (declared BEFORE any measurement, see PARAMETERS.md N-01..N-06):

N-01  A transcript file is a JSON array of caption entries
      {"RefLink","Transcription","offsetMS","durationMS"}. One file in the corpus is a
      single JSON object instead of an array; it is treated as a one-entry array and the
      anomaly is recorded in FILE_INVENTORY.jsonl (field structural_anomaly).
N-02  Per entry: whitespace runs inside Transcription are collapsed to one space and the
      text is stripped. Entry text is otherwise left exactly as the ASR wrote it
      (case, spelling, missing punctuation preserved) so that every quote stays verbatim.
N-03  Joining: non-empty entry texts are concatenated in file order with exactly one
      space between neighbours. An entry whose text is empty after N-02 contributes no
      characters but is still counted (field empty_entries).
N-04  Joined-text position -> offsetMS: for every non-empty entry we keep
      [char_start, char_end, offsetMS, durationMS, entry_index] in <file_id>.entries.json.
      char_end is exclusive. A quote is located by its first and last character position;
      the reported offsetMS is the offsetMS of the entry that contains the first token.
N-05  Token = a maximal run of Unicode letters/digits ([^\W_]+). Apostrophes, hyphens and
      all other punctuation therefore split tokens ("don't" -> "don","t"), which is what
      makes ASR variants like "dont" and "don't" comparable. WORD counts in every K7
      artefact are token counts under N-05 unless a field name says otherwise.
      FIELD words_whitespace reports len(text.split()) for reconciliation with the
      briefing figure 2,549,198.
N-06  SEARCH normalisation (used by the L00 test and by the quote verifier): lowercase,
      expand common contractions, replace every non-alphanumeric character with a space,
      collapse spaces, split into tokens. Both the quote and the corpus go through the
      same function, so a quote is found only if its tokens occur contiguously.
"""

import bisect
import json
import os
import re
import unicodedata

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
    """N-06 search normalisation -> list of lowercase tokens."""
    t = text
    for rx, rep in CONTRACTIONS:
        t = rx.sub(rep, t)
    t = t.lower()
    t = unicodedata.normalize("NFKC", t)
    t = re.sub(r"[^0-9a-z]+", " ", t)
    return t.split()


def search_text(text):
    return " ".join(search_tokens(text))


def clean_entry(text):
    """N-02"""
    if text is None:
        return ""
    return WS_RE.sub(" ", str(text)).strip()


def load_entries(path):
    """-> (entries, structural_anomaly)

    entry = {"i","text","offsetMS","durationMS","ref"}
    """
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    anomaly = ""
    if isinstance(raw, dict):
        raw = [raw]
        anomaly = "SINGLE_OBJECT_FILE_TREATED_AS_ONE_ENTRY_ARRAY"
    elif not isinstance(raw, list):
        raw = []
        anomaly = "UNEXPECTED_JSON_TOPLEVEL"
    entries = []
    for i, e in enumerate(raw):
        if not isinstance(e, dict):
            continue
        try:
            off = int(e.get("offsetMS") or 0)
        except (TypeError, ValueError):
            off = 0
        try:
            dur = int(e.get("durationMS") or 0)
        except (TypeError, ValueError):
            dur = 0
        entries.append(
            {
                "i": i,
                "text": clean_entry(e.get("Transcription")),
                "offsetMS": off,
                "durationMS": dur,
                "ref": e.get("RefLink") or "",
            }
        )
    return entries, anomaly


def join_entries(entries):
    """N-03/N-04 -> (joined_text, spans)

    spans: list of [char_start, char_end, offsetMS, durationMS, entry_index] for
    non-empty entries only, in order.
    """
    parts = []
    spans = []
    cur = 0
    for e in entries:
        if not e["text"]:
            continue
        if parts:
            parts.append(" ")
            cur += 1
        start = cur
        parts.append(e["text"])
        cur += len(e["text"])
        spans.append([start, cur, e["offsetMS"], e["durationMS"], e["i"]])
    return "".join(parts), spans


def tokenize(joined):
    """N-05 -> list of (token, char_start, char_end)."""
    return [(m.group(0).lower(), m.start(), m.end()) for m in TOKEN_RE.finditer(joined)]


def entry_at(spans, char_pos):
    """Binary search: which span contains char_pos. Returns span or None."""
    if not spans:
        return None
    starts = [s[0] for s in spans]
    k = bisect.bisect_right(starts, char_pos) - 1
    if k < 0:
        k = 0
    s = spans[k]
    if s[0] <= char_pos < s[1]:
        return s
    # char_pos fell in a separator or past the end: attribute to nearest containing/previous
    for cand in (k + 1, k - 1):
        if 0 <= cand < len(spans):
            c = spans[cand]
            if c[0] <= char_pos < c[1]:
                return c
    return s


def corpus_files(corpus_root):
    """Sorted relative paths under transcriptions/ (POSIX separators)."""
    root = os.path.join(corpus_root, "transcriptions")
    out = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.lower().endswith(".json"):
                abs_p = os.path.join(dirpath, fn)
                out.append(os.path.relpath(abs_p, corpus_root).replace(os.sep, "/"))
    out.sort()
    return out


def top_folder(rel_path):
    parts = rel_path.split("/")
    return parts[1] if len(parts) > 1 else ""


def stem(rel_path):
    return os.path.splitext(os.path.basename(rel_path))[0]


def parse_title_part(rel_path):
    """Series / title / part-number from the file name (deterministic, no guessing).

    Part number = trailing -NNN of the file name, if present.
    """
    name = stem(rel_path)
    part = None
    m = re.match(r"^(.*)-(\d{3})$", name)
    title = name
    if m:
        title, part = m.group(1), int(m.group(2))
    return title, part


def load_corpus(corpus_root):
    """Yield dicts per file: path, entries, joined, spans, tokens, anomaly."""
    for rel in corpus_files(corpus_root):
        entries, anomaly = load_entries(os.path.join(corpus_root, rel))
        joined, spans = join_entries(entries)
        toks = tokenize(joined)
        yield {
            "path": rel,
            "entries": entries,
            "anomaly": anomaly,
            "joined": joined,
            "spans": spans,
            "tokens": toks,
        }


# ---------------------------------------------------------------- position-aware search normalisation
UNIT_RE = re.compile(r"[^\W_]+(?:[\u2019']+[^\W_]+)*", re.UNICODE)


def norm_tokens_with_pos(joined):
    """-> (tokens, spans) where spans[i] = (char_start, char_end) in `joined`.

    Same token sequence as search_tokens(joined) (N-06), but every token keeps the
    character span of the word (or apostrophised word) it came from, so that a
    normalised hit can be quoted verbatim from the joined text.
    """
    toks, spans = [], []
    for m in UNIT_RE.finditer(joined):
        unit = m.group(0)
        for t in search_tokens(unit):
            toks.append(t)
            spans.append((m.start(), m.end()))
    return toks, spans


def build_pos_index(tokens):
    idx = {}
    for i, t in enumerate(tokens):
        idx.setdefault(t, []).append(i)
    return idx


def verbatim_for(tokens, spans, pos_index, q_tokens):
    """Locate q_tokens in `tokens`; return (char_start, char_end, matched_len) or None.

    Tries the whole quote first, then shorter prefixes (never shorter than 2 tokens).
    """
    n = len(q_tokens)
    if not n:
        return None
    for L in range(n, 1, -1):
        head = q_tokens[0]
        q = q_tokens[:L]
        for a in pos_index.get(head, ()):  # type: ignore[arg-type]
            if tokens[a:a + L] == q:
                return spans[a][0], spans[a + L - 1][1], L
    return None
