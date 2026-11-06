#!/usr/bin/env python3
"""TASK 3 - mechanical detection of dated market-review transcripts. NO market data is loaded.

A transcript qualifies for the candidate list only if a specific calendar date is stated in its
filename or its text AND it reads as a market review / pair discussion. Dates must be < 2025-05-01.
The pair is recorded as EURUSD only when a read window says so; otherwise the stated instrument is
recorded verbatim, or UNKNOWN.

The DESIGN/VALIDATION split rule is fixed here, in code, before any price data exists:
    day-of-month ODD  -> DESIGN
    day-of-month EVEN -> VALIDATION
This is a calendar parity rule, chosen for determinism, not for any property of the data.

Usage: python3 tools/task3_pairing.py detect
"""
import json, re, collections, datetime, sys
from pathlib import Path

B = Path(__file__).resolve().parent.parent
CUTOFF = datetime.date(2025, 5, 1)
MONTHS = {m.lower(): i for i, m in enumerate(
    ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
     'September', 'October', 'November', 'December'], 1)}
MON_ABBR = {m[:3]: i for m, i in MONTHS.items()}
REVIEW = re.compile(r'(market review|session review|tape reading|forex|futures|review|commentary|'
                    r'live (trade|commentary|stream)|am session|pm session)', re.I)
PAIRS = {
    'EURUSD': r'\b(euro|eurusd|eur usd|euro dollar|fiber)\b',
    'GBPUSD': r'\b(pound|gbpusd|british pound|cable)\b',
    'AUDUSD': r'\b(aussie|australian dollar|audusd)\b',
    'USDCAD': r'\b(dollar cad|usdcad|canadian dollar)\b',
    'DXY': r'\b(dollar index|dxy)\b',
    'ES': r'\b(e-?mini|s&p|spooz|es chart|s p 500)\b',
    'NQ': r'\b(nasdaq|nq|nas 100)\b',
}


def dates_in(name):
    out = []
    s = name.replace('_', '-')
    for m in re.finditer(r'([A-Za-z]{3,9})-(\d{1,2})-(\d{4})', s):
        mon = MONTHS.get(m.group(1).lower()) or MON_ABBR.get(m.group(1)[:3].lower())
        if mon:
            try:
                out.append(datetime.date(int(m.group(3)), mon, int(m.group(2))))
            except ValueError:
                pass
    for m in re.finditer(r'(\d{1,2})-(\d{1,2})-(\d{2,4})', s):
        a, b, c = int(m.group(1)), int(m.group(2)), int(m.group(3))
        y = c + 2000 if c < 100 else c
        try:
            out.append(datetime.date(y, a, b))
        except ValueError:
            pass
    return sorted(set(out))


def detect():
    corp = json.loads(Path('/tmp/corpus_texts.json').read_text())
    rows = []
    for rel, d in corp.items():
        name = Path(rel).name
        ds = [x for x in dates_in(name) if x < CUTOFF]
        if not ds:
            continue
        if not REVIEW.search(name):
            continue
        t = d['text']
        hits = {k: len(re.findall(p, t, re.I)) for k, p in PAIRS.items()}
        hits = {k: v for k, v in hits.items() if v}
        sess = sorted({m.group(0).lower() for m in re.finditer(
            r'\b(london (open|close|session)|new york (open|session|killzone)|asian (range|session)|'
            r'kill ?zone|am session|pm session|\d{1,2}[:.]\d{2}|\d{1,2} (a\.?m|p\.?m)|'
            r"\d{1,2} o'clock)\b", t, re.I)})
        rows.append(dict(path=rel, date=ds[0].isoformat(), day=ds[0].day,
                         split='DESIGN' if ds[0].day % 2 else 'VALIDATION',
                         instruments_by_count=dict(sorted(hits.items(), key=lambda x: -x[1])),
                         session_time_refs=len(sess), sha256=d['sha256'],
                         words=len(t.split())))
    rows.sort(key=lambda r: (r['date'], r['path']))
    (B / 'pairing_candidates.jsonl').write_text(
        '\n'.join(json.dumps(r, ensure_ascii=False) for r in rows) + '\n')
    print(json.dumps(dict(dated_review_transcripts=len(rows),
                          design=sum(1 for r in rows if r['split'] == 'DESIGN'),
                          validation=sum(1 for r in rows if r['split'] == 'VALIDATION'),
                          earliest=rows[0]['date'] if rows else None,
                          latest=rows[-1]['date'] if rows else None), indent=1))
    print('--- first 14 candidates (date | split | top instruments | words) ---')
    for r in rows[:14]:
        top = ', '.join(list(r['instruments_by_count'])[:3])
        print(f"{r['date']} {r['split']:10s} {top:18s} {r['words']:6d}  {Path(r['path']).name[:70]}")


EVENT = re.compile(r"\b(trades? (up|down|higher|lower)|rallies|drops|runs|sweeps|takes out|"
                   r"then (it|we|price)|after that|next|reverses|rejects|expands|retraces|"
                   r"went (up|down|lower|higher)|came (back|down|up))\b", re.I)


def events(date, n=3):
    """Extract and log narrated-event windows for one dated transcript; print excerpts to read."""
    corp = json.loads(Path('/tmp/corpus_texts.json').read_text())
    cands = [json.loads(l) for l in (B / 'pairing_candidates.jsonl').read_text().splitlines() if l.strip()]
    sel = [c for c in cands if c['date'] == date]
    # dedupe identical content across directories by sha256
    seen = set(); uniq = []
    for c in sel:
        if c['sha256'] in seen: continue
        seen.add(c['sha256']); uniq.append(c)
    wl = (B / 'windows.jsonl'); rl = (B / 'read_log.jsonl')
    existing = [json.loads(l) for l in wl.read_text().splitlines() if l.strip()] if wl.exists() else []
    wid = len(existing)
    new_w = []; new_r = []
    for c in uniq:
        rel = c['path']; t = corp[rel]['text']; words = t.split()
        positions = sorted({len(t[:m.start()].split()) for m in EVENT.finditer(t)})
        chosen = []
        for wi in positions:
            if all(abs(wi - x) >= 200 for x in chosen):
                chosen.append(wi)
            if len(chosen) >= n: break
        for wi in chosen:
            lo, hi = max(0, wi - 250), min(len(words), wi + 251)
            wid += 1
            w = f'W{wid:04d}'
            new_w.append(dict(window_id=w, concept='STORY_PAIRING', phrases=['narrated event'],
                              repo='newsqlguru/ict-index', path=rel, hit_word_index=wi,
                              window_words=[lo, hi], window_word_count=hi-lo,
                              file_sha256=c['sha256'], marker_score=0,
                              extraction='+-250 words around a narrated-event verb', date=date))
            seg = words[lo:hi]; segt = ' '.join(seg)
            m = EVENT.search(segt)
            mwi = len(segt[:m.start()].split()) if m else 0
            a, b2 = max(0, mwi - 10), min(len(seg), mwi + 15)
            q = ' '.join(seg[a:b2])
            ex = [dict(words=[a+lo, b2+lo], text=q)]
            new_r.append(dict(kind='excerpt_read', window_id=w, path=rel, excerpts=ex,
                              read_mode='excerpt', note='Task 3 narrated-event excerpt'))
            print(f"[{w}] {date} {c['split']} {Path(rel).name[:58]} hit@{wi}")
            print(f"    {q}")
    with wl.open('a') as f:
        for r in new_w: f.write(json.dumps(r, ensure_ascii=False)+'\n')
    with rl.open('a') as f:
        for r in [dict(kind='window_extracted', **x) for x in new_w] + new_r:
            f.write(json.dumps(r, ensure_ascii=False)+'\n')
    print(f'date={date} unique_files={len(uniq)} windows={len(new_w)}')


def pairs(dates):
    """Print one instrument-naming excerpt per unique dated file, and log the window."""
    corp = json.loads(Path('/tmp/corpus_texts.json').read_text())
    cands = [json.loads(l) for l in (B / 'pairing_candidates.jsonl').read_text().splitlines() if l.strip()]
    wl = (B / 'windows.jsonl'); rl = (B / 'read_log.jsonl')
    existing = [json.loads(l) for l in wl.read_text().splitlines() if l.strip()]
    wid = len(existing); new_w = []; new_r = []
    seen = set()
    pat = re.compile(r"\b(euro|eurusd|pound|aussie|dollar index|nasdaq|e-?mini|s&p|spooz)\b", re.I)
    for c in cands:
        if c['date'] not in dates or c['sha256'] in seen: continue
        seen.add(c['sha256'])
        rel = c['path']; t = corp[rel]['text']; words = t.split()
        m = pat.search(t)
        if not m:
            print(f"NO_PAIR_NAMED {c['date']} {Path(rel).name[:60]}"); continue
        wi = len(t[:m.start()].split())
        lo, hi = max(0, wi - 250), min(len(words), wi + 251)
        wid += 1; w = f'W{wid:04d}'
        new_w.append(dict(window_id=w, concept='STORY_PAIRING', phrases=['instrument naming'],
                          repo='newsqlguru/ict-index', path=rel, hit_word_index=wi,
                          window_words=[lo, hi], window_word_count=hi-lo,
                          file_sha256=c['sha256'], marker_score=0,
                          extraction='+-250 words around an instrument name', date=c['date']))
        a, b2 = max(lo, wi - 10), min(hi, wi + 15)
        q = ' '.join(words[a:b2])
        new_r.append(dict(kind='excerpt_read', window_id=w, path=rel,
                          excerpts=[dict(words=[a, b2], text=q)], read_mode='excerpt',
                          note='Task 3 instrument-naming excerpt'))
        print(f"[{w}] {c['date']} {Path(rel).name[:56]} :: {q}")
    with wl.open('a') as f:
        for r in new_w: f.write(json.dumps(r, ensure_ascii=False)+'\n')
    with rl.open('a') as f:
        for r in [dict(kind='window_extracted', **x) for x in new_w] + new_r:
            f.write(json.dumps(r, ensure_ascii=False)+'\n')


if __name__ == '__main__':
    if sys.argv[1] == 'pairs':
        pairs(set(sys.argv[2].split(',')))
    elif sys.argv[1] == 'detect':
        detect()
    elif sys.argv[1] == 'events':
        events(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 3)
