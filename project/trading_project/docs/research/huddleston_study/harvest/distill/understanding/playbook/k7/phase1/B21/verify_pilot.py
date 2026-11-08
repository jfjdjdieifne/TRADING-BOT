#!/usr/bin/env python3
"""Verify immutable pilot reading shards against the external corpus. No network."""
import argparse
import collections
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
K = HERE.parents[1]
sys.path.insert(0, str(K / 'scripts'))
import k7_corpus as C


def rows(p):
    return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]


def walk(o):
    if isinstance(o, dict):
        yield o
        for v in o.values():
            yield from walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from walk(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--corpus', required=True)
    ap.add_argument('--require-complete', action='store_true')
    a = ap.parse_args()
    inv = {r['file_id']: r for r in rows(K / 'FILE_INVENTORY.jsonl')}
    chunks = rows(K / 'CHUNK_INDEX.jsonl')
    ids = [c['chunk_id'] for c in chunks]
    batch = chunks[ids.index('F0120#006'):ids.index('F0124#008') + 1]
    byid = {c['chunk_id']: c for c in batch}
    readings = [r for p in sorted(HERE.glob('readings_*.jsonl')) for r in rows(p)]
    errors, checked, conditions = [], 0, 0
    seen = set()
    for r in readings:
        cid = r['chunk_id']
        if cid in seen or cid not in byid:
            errors.append(['id', cid])
            continue
        seen.add(cid)
        c = byid[cid]
        meta = inv[c['file_id']]
        raw = pathlib.Path(a.corpus) / meta['path']
        assert hashlib.sha256(raw.read_bytes()).hexdigest() == meta['sha256_source']
        text, spans = C.join_entries(C.load_entries(raw)[0])
        assert hashlib.sha256(text.encode()).hexdigest() == meta['sha256_joined']
        assert r['file_id'] == c['file_id'] and r['path'] == meta['path']
        assert r['status'] == 'READ_FULL'
        assert all(key in r for key in ['topics', 'statements', 'refs', 'terms_defined',
                   'terms_used_undefined', 'vague_words', 'open_slots', 'example_stub'])
        for obj in walk(r):
            if 'quote' in obj:
                checked += 1
                q, pos = obj['quote'], obj['char_start']
                span = C.entry_at(spans, pos)
                ok = (c['char_start'] <= pos < c['char_end'] and
                      text[pos:pos + len(q)] == q and
                      C.search_tokens(text[pos:pos + len(q)]) == C.search_tokens(q) and
                      len(C.tokenize(q)) <= 25 and
                      span[2] == obj['offsetMS'] and span[4] == obj['entry_index'])
                if not ok:
                    errors.append(['quote', cid, obj])
            if obj.get('condition_quote'):
                conditions += 1
                if obj['condition_quote'] not in text[c['char_start']:c['char_end']]:
                    errors.append(['condition_quote', cid, obj])
        for s in r['statements']:
            assert s['speaker'] in ['MICHAEL_BY_CONTEXT', 'OTHER', 'UNKNOWN']
            assert s['confidence'] in ['HIGH', 'LOW_CONFIDENCE']
            if s['speaker'] == 'UNKNOWN':
                assert s.get('status') == 'HOLD'
    missing = [c['chunk_id'] for c in batch if c['chunk_id'] not in seen]
    ledger = rows(HERE / 'ledger_part02.jsonl')
    assert sum(x['READ_FULL'] for x in ledger) == len(seen)
    assert sorted(x for r in ledger for x in r['NOT_READ']) == sorted(missing)
    types = collections.Counter(r['content_type'] for r in readings)
    statements = [s for r in readings for s in r['statements']]
    vague = [v for r in readings for v in r['vague_words']]
    result = dict(batch_id='B21', read_full=len(seen), total=len(batch),
                  not_read=missing, quotes_verified=checked-len([e for e in errors if e[0]=='quote']),
                  quotes_total=checked, condition_quotes_total=conditions,
                  content_type=dict(types), kind=dict(collections.Counter(s['kind'] for s in statements)),
                  vague_total=len(vague), vague_named=sum(v['chart_feature'] != 'NONE' for v in vague),
                  vague_none=sum(v['chart_feature'] == 'NONE' for v in vague),
                  open_slots=sum(len(r['open_slots']) for r in readings),
                  refs=sum(len(r['refs']) for r in readings),
                  spans_boundary=sum('SPANS_BOUNDARY' in s.get('flags', []) for s in statements),
                  speakers=dict(collections.Counter(s['speaker'] for s in statements)),
                  low_confidence_statements=sum(s['confidence']=='LOW_CONFIDENCE' for s in statements),
                  low_confidence_content_type=sum(r['content_type_confidence']=='LOW_CONFIDENCE' for r in readings),
                  words_read=sum(byid[x]['words'] for x in seen), errors=errors,
                  technical_checks_passed=not errors, batch_complete=not missing and not errors)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if errors or (a.require_complete and missing):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
