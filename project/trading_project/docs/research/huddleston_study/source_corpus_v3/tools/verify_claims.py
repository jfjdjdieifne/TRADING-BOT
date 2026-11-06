#!/usr/bin/env python3
"""Mechanical claim verifier (verification tool, NOT engine code).

For every line of claims.jsonl this checks that `quote` occurs in the stored PRIMARY source file
after ONLY this normalization, applied to BOTH the quote and the file text:

    1. lowercase
    2. collapse every run of whitespace (spaces, tabs, newlines) to a single space, then strip

Nothing else is normalized: punctuation, apostrophes, hyphens and ASR errors are kept exactly as
stored. It also checks that `context_before` is the 5 normalized words immediately preceding the
first occurrence of the quote, that the quote is at most 25 words, and that the source file exists
under primary/. It does not judge meaning.

Usage: python3 tools/verify_claims.py [--claims PATH] [--report PATH]
Exit code 0 if every claim verifies, 1 otherwise.
"""
import argparse, json, re, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

def norm(t):
    return re.sub(r'\s+', ' ', t).strip().lower()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--claims', default=str(BASE / 'claims.jsonl'))
    ap.add_argument('--report', default=str(BASE / 'reports' / 'claims_verification.txt'))
    a = ap.parse_args()
    lines = [l for l in Path(a.claims).read_text(encoding='utf-8').splitlines() if l.strip()]
    out, ok, bad = [], 0, 0
    cache = {}
    for i, line in enumerate(lines, 1):
        try:
            c = json.loads(line)
        except Exception as e:
            bad += 1; out.append(f'line {i}: JSON_ERROR {e}'); continue
        cid = c.get('claim_id', f'line{i}')
        p = BASE / 'primary' / c['source_id'] / c['part']
        if not p.exists():
            bad += 1; out.append(f'{cid}: FAIL source file missing: {p.relative_to(BASE)}'); continue
        if p not in cache:
            cache[p] = norm(p.read_text(encoding='utf-8'))
        text = cache[p]
        q = norm(c['quote'])
        errs = []
        if not q:
            errs.append('empty quote')
        if len(c['quote'].split()) > 25:
            errs.append(f'quote too long ({len(c["quote"].split())} words > 25)')
        pos = text.find(q)
        if pos < 0:
            errs.append('quote NOT FOUND in stored source after normalization')
        else:
            before = text[:pos].split()[-5:]
            if norm(c.get('context_before', '')) != ' '.join(before):
                errs.append(f'context_before mismatch; expected {" ".join(before)!r}')
        if c.get('type') not in ('SAID', 'DEMONSTRATED', 'AMBIGUOUS', 'CONTRADICTED-IN-SOURCES'):
            errs.append(f'bad type {c.get("type")!r}')
        for k in ('concept', 'statement', 'source_id', 'part'):
            if not c.get(k):
                errs.append(f'missing field {k}')
        if errs:
            bad += 1; out.append(f'{cid}: FAIL ' + '; '.join(errs))
        else:
            ok += 1; out.append(f'{cid}: VERIFIED ({c["source_id"]}/{c["part"]}, {len(c["quote"].split())} words, {c["type"]})')
    header = [f'total_claims={len(lines)}', f'verified={ok}', f'failed={bad}',
              'normalization=lowercase + whitespace collapse (nothing else)', '']
    body = '\n'.join(header + out) + '\n'
    Path(a.report).parent.mkdir(parents=True, exist_ok=True)
    Path(a.report).write_text(body, encoding='utf-8')
    print(body)
    return 0 if bad == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
