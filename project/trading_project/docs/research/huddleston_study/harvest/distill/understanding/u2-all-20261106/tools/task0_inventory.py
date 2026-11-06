#!/usr/bin/env python3
"""TASK 0 - mechanical concept discovery over the pinned ict-index corpus.

NO concept list is supplied from memory. This script only:
  1. extracts text from every transcript (Transcription fields joined by one space),
  2. counts 1-4 word grams that survive a stopword/edge filter,
  3. collects every window matching a definition pattern,
  4. writes concept_inventory.tsv + definition_hits.jsonl + corpus_manifest.jsonl.

Judgement about which inventory terms have real trading meaning happens afterwards, by a human/agent
reading this output, and the exclusions are recorded in excluded_terms.tsv with a reason.

Usage: CORPUS=/tmp/ictidx/ict-index-<sha> python3 tools/task0_inventory.py
"""
import os, re, json, hashlib, collections, sys
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent
CORPUS = Path(os.environ.get('CORPUS', '/tmp/ictidx/ict-index-e8c40a8dae5ea6689926f28c7184ce3e2fb85b9c'))
REPO = 'newsqlguru/ict-index'

STOP = set("""a an the and or but if then than so as of to in on at by for with without from into onto over under
above below up down out off again more most less least very much many any some all each other another same own just
only also both either neither not no nor too can could should would may might must will shall do does did done have has
had be been being is are was were am it its this that these those there here he she they them his her their our we you
your i me my mine us let lets okay ok yeah yes now well right like know think see look got get go going come came take
takes took want wants thing things something anything nothing everything one two three four five six seven eight nine
ten first second third next last time times way ways lot lots kind sort really actually basically obviously simply
gonna wanna gotta uh um ah oh em huh mm hmm alright fine good great nice new old big small little long short high low
put puts call called says said say tell told ask asked make makes made made use used using give gives given need needs
needed back forth away around about because while during before after when where which who whom whose what how why
doesnt dont isnt arent wasnt werent cant couldnt shouldnt wouldnt wont thats theres heres whats lets ive youre theyre
were weve youve hes shes its id ill im dont did doesnt dont youre youre""".split())

DEF_PAT = re.compile(r"\b(is where|is when|means|we call|what is a|what is an|i define|is defined as|refer to|"
                     r"is called|are called|refers to|definition of)\b", re.I)


def text_of(p):
    d = json.loads(Path(p).read_text(encoding='utf-8', errors='replace'))
    if isinstance(d, list) and d and isinstance(d[0], dict) and 'Transcription' in d[0]:
        return ' '.join(str(x.get('Transcription', '')) for x in d)
    acc = []

    def walk(x):
        if isinstance(x, str):
            acc.append(x)
        elif isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(d)
    return ' '.join(acc)


def main():
    files = sorted(CORPUS.rglob('*.json'))
    if not files:
        sys.exit('no transcripts found at ' + str(CORPUS))
    gram_count = collections.Counter()
    gram_files = collections.defaultdict(set)
    def_hits = []
    manifest = []
    texts = {}
    for p in files:
        rel = str(p.relative_to(CORPUS))
        raw = p.read_bytes()
        t = re.sub(r'\s+', ' ', text_of(p)).strip()
        texts[rel] = t
        words = re.findall(r"[A-Za-z0-9']+", t.lower())
        manifest.append(dict(repo=REPO, path=rel, bytes=len(raw), words=len(words),
                             sha256=hashlib.sha256(raw).hexdigest()))
        # n-grams 1..4, must not start or end with a stopword
        seen_here = collections.Counter()
        for n in (1, 2, 3, 4):
            for i in range(len(words) - n + 1):
                g = words[i:i + n]
                if g[0] in STOP or g[-1] in STOP:
                    continue
                if not any(len(w) >= 4 and w not in STOP for w in g):
                    continue
                if any(len(w) < 2 for w in g):
                    continue
                seen_here[' '.join(g)] += 1
        for g, c in seen_here.items():
            gram_count[g] += c
            gram_files[g].add(rel)
        # definition windows: +-14 words around the pattern (ASR text has almost no punctuation,
        # so these are WORD WINDOWS, not grammatical sentences; recorded as such)
        tw = t.split()
        for m in DEF_PAT.finditer(t):
            wi = len(t[:m.start()].split())
            lo, hi = max(0, wi - 14), min(len(tw), wi + 16)
            def_hits.append(dict(repo=REPO, path=rel, pattern=m.group(0).lower(),
                                 window_words=[lo, hi], text=' '.join(tw[lo:hi])))
    (OUT / 'corpus_manifest.jsonl').write_text(
        '\n'.join(json.dumps(r, ensure_ascii=False) for r in manifest) + '\n')
    (OUT / 'definition_hits.jsonl').write_text(
        '\n'.join(json.dumps(r, ensure_ascii=False) for r in def_hits) + '\n')
    # inventory: terms seen >= 8 times in >= 3 files
    rows = []
    for g, c in gram_count.items():
        nf = len(gram_files[g])
        if c < 8 or nf < 3:
            continue
        ex = 'NONE'
        gl = g.lower()
        for h in def_hits:
            if gl in h['text'].lower():
                seg = h['text'].split()
                low = h['text'].lower()
                pos = low.find(gl)
                wi = len(h['text'][:pos].split())
                cand = seg[max(0, wi - 6): wi + len(g.split()) + 12]
                if len(cand) > 25:
                    cand = cand[:25]
                ex = ' '.join(cand)
                break
        rows.append((g, c, nf, ex))
    rows.sort(key=lambda r: (-r[1], r[0]))
    with (OUT / 'concept_inventory.tsv').open('w') as f:
        f.write('term\tcount\tfiles\texample_definition_quote_or_NONE\n')
        for g, c, nf, ex in rows:
            f.write(f'{g}\t{c}\t{nf}\t{ex}\n')
    # keep the per-term file lists for the window selector (not committed: large)
    Path('/tmp/gram_files.json').write_text(json.dumps(
        {g: sorted(gram_files[g]) for g, c, nf, ex in rows}))
    print(json.dumps(dict(transcripts=len(files), total_words=sum(m['words'] for m in manifest),
                          distinct_grams_kept=len(rows), definition_windows=len(def_hits)), indent=1))


if __name__ == '__main__':
    main()
