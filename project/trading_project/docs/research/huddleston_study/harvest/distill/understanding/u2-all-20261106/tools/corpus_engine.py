#!/usr/bin/env python3
"""Shared corpus engine: window extraction + read logging + claim building.

Honesty contract implemented here:
  * every extracted window is logged with file, word range, sha256 and the concept it was pulled for;
  * every excerpt actually printed to the agent is logged separately (read_mode="excerpt"), so the
    read log distinguishes "window extracted" from "text the agent actually saw";
  * a claim is only written if its quote is located verbatim in the source file after lowercase +
    whitespace collapse ONLY, and its hit falls inside a logged window;
  * nothing is paraphrased into the quote field.

Subcommands:
  windows --concept NAME --phrase P [--phrase P ...] --n 15 [--per-file 2]
  add     --json '<list of claim dicts>'   (quotes are checked before writing)
  compare --n 400                          (Task 2 mechanical mining)
"""
import os, re, json, argparse, hashlib, collections, math
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent
REPO = 'newsqlguru/ict-index'
CACHE = Path('/tmp/corpus_texts.json')

COMPARATIVE = (r"\b(more|less|better|stronger|weaker|prefer|preferable|i like|i want|i don't want|"
               r"not enough|ideal|best|key|instead of|rather than|over|major|minor|clean|obvious|"
               r"energetic|meaningful|higher probability|lower probability|strongest|cleaner|"
               r"most important|more important)\b")
REJECTION = r"\b(not enough|doesn't count|does not count|that's not|that is not|isn't a|is not a|invalid|fails|failure)\b"
DEFINITION = r"\b(is where|is when|means|we call|what is a|i define|is defined as|refer to|is called|refers to)\b"


def load():
    if not CACHE.exists():
        raise SystemExit('run tools/probe_terms.py first to build /tmp/corpus_texts.json')
    return json.loads(CACHE.read_text())


def append(fn, rows):
    with (OUT / fn).open('a') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')


def windows_for(phrases, n, per_file, concept, nex=2):
    corp = load()
    pats = [re.compile(r'(?<![a-z])' + re.escape(p) + r'(?![a-z])', re.I) for p in phrases]
    scored = []
    for rel, d in corp.items():
        t = d['text']
        hits = sum(len(p.findall(t)) for p in pats)
        if hits:
            wc = len(t.split())
            scored.append((hits / max(1, wc) * 1000, hits, rel))
    scored.sort(reverse=True)
    existing = []
    if (OUT / 'windows.jsonl').exists():
        existing = [json.loads(l) for l in (OUT / 'windows.jsonl').read_text().splitlines() if l.strip()]
    wid = len(existing)
    made = []
    shown = []
    used_files = collections.Counter()
    for dens, hits, rel in scored:
        if len(made) >= n:
            break
        if used_files[rel] >= per_file:
            continue
        t = corp[rel]['text']
        words = t.split()
        positions = sorted({len(t[:m.start()].split()) for p in pats for m in p.finditer(t)})
        # prefer hits that carry definition / comparative / rejection language nearby
        ranked = []
        for wi in positions:
            lo, hi = max(0, wi - 250), min(len(words), wi + 251)
            seg = ' '.join(words[lo:hi])
            score = (3 * len(re.findall(DEFINITION, seg, re.I))
                     + 2 * len(re.findall(COMPARATIVE, seg, re.I))
                     + 2 * len(re.findall(REJECTION, seg, re.I)))
            ranked.append((score, -wi, wi))
        ranked.sort(reverse=True)
        ranked = [r for r in ranked if r[0] > 0] or ranked[:1]
        chosen = []
        for r in ranked:
            if all(abs(r[2] - c[2]) >= 150 for c in chosen):
                chosen.append(r)
            if len(chosen) >= per_file:
                break
        ranked = chosen
        take = 0
        for score, negwi, wi in ranked:
            if take >= per_file or len(made) >= n:
                break
            lo, hi = max(0, wi - 250), min(len(words), wi + 251)
            wid += 1
            take += 1
            used_files[rel] += 1
            rec = dict(window_id=f'W{wid:04d}', concept=concept, phrases=phrases, repo=REPO, path=rel,
                       hit_word_index=wi, window_words=[lo, hi], window_word_count=hi - lo,
                       file_sha256=corp[rel]['sha256'], marker_score=score,
                       extraction='+-250 words around a literal phrase hit')
            made.append(rec)
            # excerpt selection: best marker-bearing runs INSIDE this window, each <=25 words
            seg_words = words[lo:hi]
            seg = ' '.join(seg_words)
            cands = []
            for m in re.finditer(DEFINITION + '|' + COMPARATIVE + '|' + REJECTION, seg, re.I):
                mwi = len(seg[:m.start()].split())
                a, b = max(0, mwi - 11), min(len(seg_words), mwi + 14)
                q = seg_words[a:b]
                if len(q) > 25:
                    q = q[:25]
                qt = ' '.join(q)
                # the excerpt must contain the concept phrase itself to be useful for a card
                if not any(p.search(qt) for p in pats):
                    continue
                cands.append((a + lo, b + lo, qt))
            if not cands:
                a = max(0, wi - lo - 12)
                q = seg_words[a:a + 25]
                cands.append((a + lo, a + lo + len(q), ' '.join(q)))
            # de-dup near-identical excerpts, keep the two best-separated
            picked = []
            for a, b, qt in cands:
                if any(abs(a - pa) < 15 for pa, pb, pq in picked):
                    continue
                picked.append((a, b, qt))
                if len(picked) == nex:
                    break
            shown.append(dict(window_id=rec['window_id'], path=rel, hit=wi,
                              excerpts=[dict(words=[a, b], text=qt) for a, b, qt in picked]))
    append('windows.jsonl', made)
    append('read_log.jsonl', [dict(kind='window_extracted', **r) for r in made])
    for s in shown:
        append('read_log.jsonl', [dict(kind='excerpt_read', window_id=s['window_id'], path=s['path'],
                                       excerpts=s['excerpts'], read_mode='excerpt',
                                       note='agent saw these excerpts of the logged window, not all 501 words')])
    print(f'CONCEPT {concept}: windows_extracted={len(made)} target={n} '
          f'{"THIN" if len(made) < 15 else "OK"}')
    for s in shown:
        print(f"\n[{s['window_id']}] {s['path'].split('/')[-1]} hit@{s['hit']}")
        for e in s['excerpts']:
            print(f"   {e['words']}: {e['text']}")
    return made


def norm(t):
    return re.sub(r'\s+', ' ', t).strip().lower()


def add_claims(new):
    corp = load()
    wins = [json.loads(l) for l in (OUT / 'windows.jsonl').read_text().splitlines() if l.strip()]
    cf = OUT / 'claims.jsonl'
    rows = [json.loads(l) for l in cf.read_text().splitlines() if l.strip()] if cf.exists() else []
    n = len(rows)
    rejected = []
    for r in new:
        rel = r['path']
        if rel not in corp:
            rejected.append((r.get('quote', '')[:50], 'file not in corpus'))
            continue
        t = norm(corp[rel]['text'])
        q = norm(r['quote'])
        pos = t.find(q)
        if pos < 0:
            rejected.append((r['quote'][:60], 'quote not located verbatim'))
            continue
        if len(r['quote'].split()) > 25:
            rejected.append((r['quote'][:60], 'over 25 words'))
            continue
        wi = len(t[:pos].split())
        cand = [x for x in wins if x['path'] == rel and x['window_words'][0] <= wi <= x['window_words'][1]]
        w = next((x for x in cand if x['concept'] == r['concept']), cand[0] if cand else None)
        if w is None:
            rejected.append((r['quote'][:60], 'hit outside every logged window'))
            continue
        n += 1
        rows.append(dict(claim_id=f'U{n:04d}', repo=REPO, path=rel, quote=r['quote'],
                         statement=r['statement'], concept=r['concept'], section=r['section'],
                         window_id=w['window_id'], hit_word_index=wi,
                         file_sha256=corp[rel]['sha256'],
                         label=r.get('label', 'QUOTE'),
                         notes=r.get('notes', '')))
    cf.write_text('\n'.join(json.dumps(r, ensure_ascii=False) for r in rows) + '\n')
    print('claims_total', len(rows), 'added', len(rows) - (n - len(new) + len(rejected)) if new else 0,
          'rejected', len(rejected))
    for q, why in rejected:
        print('  REJECT:', why, '|', q)
    return rows


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    w = sub.add_parser('windows')
    w.add_argument('--concept', required=True)
    w.add_argument('--phrase', action='append', required=True)
    w.add_argument('--n', type=int, default=15)
    w.add_argument('--per-file', type=int, default=2)
    w.add_argument('--excerpts', type=int, default=2)
    a = sub.add_parser('add')
    a.add_argument('--json', required=True)
    c = sub.add_parser('compare')
    c.add_argument('--n', type=int, default=400)
    args = ap.parse_args()
    if args.cmd == 'windows':
        windows_for(args.phrase, args.n, args.per_file, args.concept, args.excerpts)
    elif args.cmd == 'add':
        add_claims(json.loads(args.json))
    elif args.cmd == 'compare':
        compare_mine(args.n)


def compare_mine(limit):
    """TASK 2 - mechanical mining of comparative/preference language across all transcripts."""
    corp = load()
    pat = re.compile(COMPARATIVE, re.I)
    rows = []
    seen = set()
    for rel, d in corp.items():
        words = d['text'].split()
        t = d['text']
        for m in pat.finditer(t):
            wi = len(t[:m.start()].split())
            lo, hi = max(0, wi - 12), min(len(words), wi + 13)
            q = ' '.join(words[lo:hi])
            if len(q.split()) > 25:
                q = ' '.join(words[lo:lo + 25])
            key = norm(q)
            if key in seen:
                continue
            seen.add(key)
            rows.append(dict(repo=REPO, path=rel, degree_word=m.group(0).lower(),
                             word_index=wi, quote=q, file_sha256=d['sha256'],
                             window_words=[lo, hi]))
            if len(rows) >= limit:
                break
        if len(rows) >= limit:
            break
    (OUT / 'comparisons_raw.jsonl').write_text(
        '\n'.join(json.dumps(r, ensure_ascii=False) for r in rows) + '\n')
    print('comparisons_raw', len(rows))
    print('degree_word_counts', json.dumps(collections.Counter(r['degree_word'] for r in rows).most_common(), indent=0))


if __name__ == '__main__':
    main()
