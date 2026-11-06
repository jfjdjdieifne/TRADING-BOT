#!/usr/bin/env python3
"""Directed phrase probe + corpus cache.

Why this exists: task0_inventory.py drops any n-gram that starts or ends with a stop-word, so phrases
like "old high", "swing high", "time of day", "no trade", "being wrong", "power of three" never reach
the inventory even though they may be frequent. NOT_IN_INVENTORY therefore does NOT mean absent.
This script counts exact phrases directly in the extracted transcript text, with no stop-word filter.

The probe list comes from (a) the session ASSIGNMENT wording supplied by the repo owner and
(b) terms already surfaced by the mechanical inventory. It is not a list of remembered ICT concepts.

Writes probe_terms.tsv and caches /tmp/corpus_texts.json for the window selector.
"""
import os, re, json, hashlib, collections
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent
CORPUS = Path(os.environ.get('CORPUS', '/tmp/ictidx/ict-index-e8c40a8dae5ea6689926f28c7184ce3e2fb85b9c'))

PROBES = [
 # assignment A wording
 "buy side", "sell side", "buy side liquidity", "sell side liquidity", "equal highs", "equal lows",
 "relative equal highs", "relative equal lows", "old high", "old highs", "old low", "old lows",
 "run on stops", "stop run", "liquidity run", "draw on liquidity", "liquidity pool", "target",
 "swing high", "swing highs", "swing low", "swing lows", "swing point", "short term high",
 "short term low", "intermediate term high", "intermediate term low", "long term high", "long term low",
 "ipda", "interbank price delivery algorithm", "data range", "data ranges",
 # assignment B wording
 "displacement", "shift in market structure", "market structure shift", "market structure",
 "fair value gap", "order block", "breaker", "bullish breaker", "bearish breaker", "mitigation block",
 "rejection block", "consequent encroachment", "inefficiency", "imbalance", "rebalance",
 "volume imbalance", "liquidity void", "inversion fair value gap", "optimal trade entry",
 "2022 model", "price action model", "entry model",
 # assignment C wording
 "dealing range", "equilibrium", "premium", "discount", "premium array", "discount array", "pd array",
 "time distortion", "news", "high impact news", "non farm payroll", "day of week", "days of the week",
 "kill zone", "kill zones", "asian range", "asian session", "london session", "london open",
 "new york session", "new york open", "time of day", "midnight", "opening price", "bias",
 "directional bias", "daily bias", "weekly bias", "higher time frame", "lower time frame",
 "weekly template", "daily template", "seasonal tendency", "mean threshold",
 # assignment D wording
 "risk", "stop loss", "break even", "partial", "partials", "no trade", "being wrong", "wrong",
 "position", "money management", "risk management", "one shot one kill", "turtle soup",
 "silver bullet", "judas swing", "smt divergence", "market maker", "power of three",
 # ASR variants surfaced by the inventory itself (kept, flagged, never silently corrected)
 "cell side", "cell stops", "south side", "fairway gap", "volume and balance",
 "consequent encouragement", "dealers range", "central bank dealers range", "shot one kill",
]


def text_of(p):
    d = json.loads(Path(p).read_text(encoding='utf-8', errors='replace'))
    if isinstance(d, list) and d and isinstance(d[0], dict) and 'Transcription' in d[0]:
        return ' '.join(str(x.get('Transcription', '')) for x in d)
    return json.dumps(d)


def main():
    cache = {}
    for p in sorted(CORPUS.rglob('*.json')):
        rel = str(p.relative_to(CORPUS))
        t = re.sub(r'\s+', ' ', text_of(p)).strip()
        cache[rel] = dict(text=t, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    Path('/tmp/corpus_texts.json').write_text(json.dumps(cache))
    low = {k: v['text'].lower() for k, v in cache.items()}
    rows = []
    for ph in PROBES:
        pat = re.compile(r'(?<![a-z])' + re.escape(ph) + r'(?![a-z])')
        c = 0
        fs = []
        for k, t in low.items():
            n = len(pat.findall(t))
            if n:
                c += n
                fs.append((n, k))
        fs.sort(reverse=True)
        rows.append((ph, c, len(fs), fs[0][1] if fs else 'NONE'))
    with (OUT / 'probe_terms.tsv').open('w') as f:
        f.write('phrase\tcount\tfiles\tdensest_or_first_file\n')
        for ph, c, nf, top in rows:
            f.write(f'{ph}\t{c}\t{nf}\t{top}\n')
    Path('/tmp/probe_files.json').write_text(json.dumps({
        ph: [k for n, k in sorted([(len(re.compile(r'(?<![a-z])' + re.escape(ph) + r'(?![a-z])').findall(t)), k)
                                   for k, t in low.items()], reverse=True) if n]
        for ph in PROBES}))
    absent = [r[0] for r in rows if r[1] == 0]
    print('cached_files', len(cache))
    print('probes', len(rows), 'zero_hit', len(absent))
    print('ZERO_HIT:', ', '.join(absent) if absent else 'none')
    for ph, c, nf, top in rows:
        if ph in ('old high', 'old low', 'swing high', 'swing low', 'short term high',
                  'intermediate term high', 'long term high', 'ipda', 'time distortion',
                  'no trade', 'being wrong', 'time of day', 'power of three', 'weekly template',
                  'daily template', 'new york session', 'entry model'):
            print(f'  {ph:26s} count={c:5d} files={nf}')


if __name__ == '__main__':
    main()
