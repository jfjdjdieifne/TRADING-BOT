#!/usr/bin/env python3
"""Post-commit positional recall only; never modifies reading shards."""
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
from k7_phase0 import resolve_path


def rows(p):
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]


def extract(o, path=None, rid=None, trail='$'):
    if isinstance(o, dict):
        path = resolve_path(o) or path
        rid = next((o[k] for k in ['claim_id', 'statement_id', 'quote_id', 'id',
                    'evidence_id', 'record_id', 'card_id'] if isinstance(o.get(k), (str, int))), rid)
        if isinstance(o.get('quote'), str) and o['quote'].strip():
            yield path, rid, trail, o['quote']
        for k, v in o.items():
            if isinstance(v, (dict, list)):
                yield from extract(v, path, rid, trail + '.' + k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from extract(v, path, rid, trail + '[' + str(i) + ']')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--corpus', required=True)
    ap.add_argument('--refs', required=True)
    ap.add_argument('--output', required=True)
    a = ap.parse_args()
    inv = {r['path']: r for r in rows(K / 'FILE_INVENTORY.jsonl')}
    chunks = rows(K / 'CHUNK_INDEX.jsonl')
    ids = [c['chunk_id'] for c in chunks]
    batch = chunks[ids.index('F0120#006'):ids.index('F0124#008')+1]
    byfile = collections.defaultdict(list)
    for c in batch:
        byfile[c['file_id']].append(c)
    corpus = {}
    for path, meta in inv.items():
        if meta['file_id'] not in byfile:
            continue
        t, spans = C.join_entries(C.load_entries(pathlib.Path(a.corpus)/path)[0])
        toks, pos = C.norm_tokens_with_pos(t)
        corpus[path] = (t, spans, toks, pos, C.build_pos_index(toks))
    found, excluded, not_found = {}, collections.Counter(), []
    for root in sorted(pathlib.Path(a.refs).iterdir()):
        if not root.is_dir():
            continue
        for p in sorted(root.rglob('*.jsonl')):
            if 'github' in p.relative_to(root).parts:
                continue
            for line, raw in enumerate(p.read_text(errors='replace').splitlines(), 1):
                try:
                    o = json.loads(raw)
                except ValueError:
                    excluded[root.name + ':invalid_json'] += 1
                    continue
                for path, rid, trail, q in extract(o):
                    if not path or path not in inv:
                        excluded[root.name + ':quote_without_resolved_corpus_path'] += 1
                        continue
                    if path not in corpus:
                        continue
                    t, spans, toks, pos, index = corpus[path]
                    qt = C.search_tokens(q)
                    hits = []
                    for start in index.get(qt[0], []) if qt else []:
                        if toks[start:start+len(qt)] != qt:
                            continue
                        char = pos[start][0]
                        owner = next((c for c in byfile[inv[path]['file_id']]
                                      if c['char_start'] <= char < c['char_end']), None)
                        if owner:
                            entry = C.entry_at(spans, char)
                            hits.append(dict(chunk_id=owner['chunk_id'], entry_index=entry[4],
                                             offsetMS=entry[2], char_start=char))
                    source = dict(ref=root.name, file=str(p.relative_to(root)), line=line,
                                  existing_id=rid, json_location=trail)
                    if not hits:
                        not_found.append(source)
                        continue
                    key = hashlib.sha256((path+'\0'+' '.join(qt)).encode()).hexdigest()
                    rec = found.setdefault(key, dict(quote_key=key, path=path,
                                           occurrences=hits, existing_records=[]))
                    rec['existing_records'].append(source)
    readings = [r for p in sorted(HERE.glob('readings_*.jsonl')) for r in rows(p)]
    statements = [(r['path'], r['chunk_id'], i, s) for r in readings
                  for i, s in enumerate(r['statements'], 1)]
    covered_statements = set()
    for rec in found.values():
        rec['matches'] = []
        for path, cid, i, s in statements:
            if path != rec['path']:
                continue
            if any(abs(s['entry_index']-hit['entry_index']) <= 1 for hit in rec['occurrences']):
                rec['matches'].append(dict(chunk_id=cid, statement_number=i))
                covered_statements.add((cid, i))
        rec['recalled'] = bool(rec['matches'])
    out = pathlib.Path(a.output)
    with out.open('x') as f:
        for rec in sorted(found.values(), key=lambda r: (r['path'], r['quote_key'])):
            f.write(json.dumps(rec, ensure_ascii=False)+'\n')
    summary = dict(unique_existing_quotes_in_batch=len(found),
                   recalled=sum(r['recalled'] for r in found.values()),
                   misses=sum(not r['recalled'] for r in found.values()),
                   existing_in_read_chunks=sum(any(h['chunk_id'] in {r['chunk_id'] for r in readings}
                                                      for h in x['occurrences']) for x in found.values()),
                   new_statements_positional=len(statements)-len(covered_statements),
                   statements_total=len(statements), excluded=dict(excluded),
                   batch_file_quotes_not_located_in_batch=len(not_found),
                   note='Positional coverage only, not semantic recall. Unread chunks retained in denominator.')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
