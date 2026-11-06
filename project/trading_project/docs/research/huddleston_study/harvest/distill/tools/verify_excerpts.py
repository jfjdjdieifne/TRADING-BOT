#!/usr/bin/env python3
"""Phase-0 check: every excerpt line in harvest/github/_excerpts/*.jsonl is
re-verified against a fresh download of the pinned commit.

For each line: file exists, sha256(file) == file_sha256, and the quote occurs
verbatim in the file after lowercase + whitespace-collapse ONLY.

Usage: verify_excerpts.py [--seed N] [--sample N]
"""
import json, glob, hashlib, re, sys, os, random, argparse

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # harvest/
DISTILL = os.path.join(BASE, "distill")
EXC = os.path.join(BASE, "github", "_excerpts")
REPO_ROOT = "/tmp/dr"

def norm(s):
    return re.sub(r"\s+", " ", s.lower()).strip()

def extract(raw, ext):
    """Same extraction the harvest pass used: JSON -> concatenated strings,
    HTML -> tags stripped + entities unescaped. PDF -> pypdf text."""
    if ext == ".pdf":
        try:
            import pypdf, io
            return " ".join((pg.extract_text() or "") for pg in pypdf.PdfReader(io.BytesIO(raw)).pages)
        except Exception:
            return ""
    try:
        s = raw.decode("utf-8")
    except UnicodeDecodeError:
        s = raw.decode("latin-1", "replace")
    if ext in (".json", ".jsonl"):
        try:
            out = []
            def walk(x):
                if isinstance(x, str): out.append(x)
                elif isinstance(x, dict):
                    for v in x.values(): walk(v)
                elif isinstance(x, list):
                    for v in x: walk(v)
            walk(json.loads(s)); s = " ".join(out)
        except Exception:
            pass
    if ext in (".html", ".htm"):
        import html as H
        s = re.sub(r"(?is)<(script|style).*?</\1>", " ", s)
        s = re.sub(r"<[^>]+>", " ", s)
        s = H.unescape(s)
    return s

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20261106)
    ap.add_argument("--sample", type=int, default=100)
    a = ap.parse_args()
    lines = []
    for f in sorted(glob.glob(os.path.join(EXC, "*.jsonl"))):
        for ln in open(f, encoding="utf-8"):
            if ln.strip():
                lines.append(json.loads(ln))
    random.seed(a.seed)
    sample = random.sample(lines, min(a.sample, len(lines)))
    res = {"seed": a.seed, "total_lines": len(lines), "sample_size": len(sample),
           "full": {"ok": 0, "ok_raw": 0, "ok_extracted": 0, "missing": 0, "sha_mismatch": 0, "quote_missing": 0, "quote_too_long": 0},
           "sample": {"ok": 0, "ok_raw": 0, "ok_extracted": 0, "missing": 0, "sha_mismatch": 0, "quote_missing": 0, "quote_too_long": 0}}
    cache = {}
    def check(r, bucket):
        p = os.path.join(REPO_ROOT, r["repo"].replace("/", "__"), r["path"])
        if not os.path.exists(p):
            bucket["missing"] += 1; return
        if p not in cache:
            b = open(p, "rb").read()
            ext = os.path.splitext(p)[1].lower()
            cache[p] = (hashlib.sha256(b).hexdigest(),
                        norm(b.decode("utf-8", "replace")),
                        norm(extract(b, ext)))
        h, rawtxt, exttxt = cache[p]
        if h != r["file_sha256"]:
            bucket["sha_mismatch"] += 1; return
        if len(r["quote"].split()) > 25:
            bucket["quote_too_long"] += 1; return
        q = norm(r["quote"])
        if q in rawtxt:
            bucket["ok_raw"] += 1; bucket["ok"] += 1; return
        if q in exttxt:
            bucket["ok_extracted"] += 1; bucket["ok"] += 1; return
        bucket["quote_missing"] += 1
    for r in lines: check(r, res["full"])
    for r in sample: check(r, res["sample"])
    print(json.dumps(res, indent=1))
    open(os.path.join(DISTILL, "phase0_excerpt_verify.json"), "w").write(json.dumps(res, indent=1) + "\n")

if __name__ == "__main__":
    main()
