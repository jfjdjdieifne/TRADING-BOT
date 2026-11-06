#!/usr/bin/env python3
"""TASK 3 output builder: pairing/<transcript>.md + pairing_index.tsv.

Narrated events below were authored ONLY from excerpts printed and logged this session. Every event
quote is checked to exist verbatim in its file (lowercase + whitespace collapse only) AND to fall
inside the logged window it is attributed to; anything that fails is dropped and reported.

pair_stated is taken only from an instrument-naming window that was actually read. A transcript is
marked usable_for_EURUSD_test=yes only when such a window names euro dollar / EURUSD.
"""
import json, re, collections
from pathlib import Path

B = Path(__file__).resolve().parent.parent
corp = json.loads(Path('/tmp/corpus_texts.json').read_text())
wins = {json.loads(l)['window_id']: json.loads(l)
        for l in (B / 'windows.jsonl').read_text().splitlines() if l.strip()}
cands = [json.loads(l) for l in (B / 'pairing_candidates.jsonl').read_text().splitlines() if l.strip()]


def norm(t):
    return re.sub(r'\s+', ' ', t).strip().lower()


# window_id -> (order, object/level named, direction, time/order wording, what happened next)
EVENTS = {
 'W0316': ('sell side liquidity into a fair value gap', 'down', 'we did in fact',
           'price traded down into the gap', '[sic-asr] "cell solid liquidity" = sell side liquidity'),
 'W0318': ('a gap, then old daily lows', 'up into the gap', 'then',
           'it fails to make a return to old daily lows', ''),
 'W0320': ('the annotated levels', 'down, back up, down again', 'one single pass',
           'it comes up and stops there', ''),
 'W0323': ('the level previously touched', 'retrace lower', 'later on in the morning',
           'he calls it a reason for concern', ''),
 'W0324': ('the market', 'up then intraday weakness', 'and then',
           'weakness intraday, attributed to Powell/Fed', '[sic-asr] "pal Fed"'),
 'W0327': ('a rejection block', 'runs up then breaks down', "at the nine o'clock hour",
           'it breaks down one more time and stabs', ''),
 'W0328': ('bullish breaker, then order block', 'shift bullish, back down, then higher',
           'here / then', 'consolidation then higher', '[sic-asr] "Market credit Mark is"'),
 'W0331': ('consequent encroachment of the wick', 'up into it, then down', 'and then',
           'it delivers down to that level', '[sic-asr] "consequent question" = consequent encroachment'),
 'W0333': ('weekly order block level and a fair value gap', 'n/a (levels named)', 'and then',
           'the gap is identified after the order block', '[sic-asr] "in the form of a City"'),
 'W0334': ('a fair value gap', 'trades up into it', 'now',
           'he measures 10 handles from that point', '[sic-asr] "favorite bag" = fair value gap'),
 'W0335': ('a higher low and the next low', 'wick down into it', 'and then',
           'price is inside the range', ''),
 'W0336': ("Monday's high / the shaded area", 'open then trade down', 'so we open',
           'it trades down into the shaded area he had flagged', ''),
 'W0337': ("Monday's low, then relative equal candles", 'up to it, then lower', 'then',
           'an immediate rebalance, then price starts to go lower', ''),
 'W0338': ('that low', 'trade down to it', 'this candle',
           'every candle is overlapped, nothing needing rebalance', ''),
 'W0340': ('a small fair value gap inside an imbalance', 'rallies up into it', 'and then',
           'the next leg follows', ''),
 'W0344': ('two price points', 'down, up, down again', 'then this candle here opened',
           'the range between candle high and low is balanced', ''),
 'W0347': ("a candle's high and low, and an existing gap", 'n/a (range annotated)', 'and then',
           'the range is annotated because a gap is already there',
           '[sic-asr] "scandals high" = candle\'s high; "very Gap" = fair value gap'),
 'W0348': ('two areas of imbalance', 'down to it', 'if we trade down to it',
           'that might cause it to find some support', 'conditional, not asserted as outcome'),
}

# window_id of the instrument-naming window -> what it actually names
PAIR_WIN = {
 'W0349': ('DXY', 'dollar Index'),
 'W0350': ('DXY/ES', 'dollar Index'),
 'W0351': ('EURUSD', 'euro dollar daily chart'),
 'W0352': ('EURUSD+GBPUSD+DXY', 'dollar Index ... euro dollar in pound dollar'),
 'W0353': ('DXY', 'daily dollar Index'),
 'W0354': ('DXY', 'dollar Index'),
 'W0355': ('EUR historic analogy', 'Euro and the swissy was depegged'),
 'W0356': ('EURUSD+GBPUSD', 'euro dollar ... cable pound dollar'),
 'W0357': ('EURUSD', 'euro dollar 15 minute uh chart'),
 'W0358': ('EURUSD+DXY+ES', 'dollar Index Euro and spoos'),
 'W0359': ('EURUSD+DXY+ES', 'dollar Index euro dollar and e-mini s p'),
}

# authored event quotes, each taken from the excerpt printed for that window
QUOTE = {
 'W0316': 'we did in fact trade down into the cell solid liquidity into our value Gap',
 'W0318': 'this is a gap And Trades up into that fails to make a return to Old daily lows',
 'W0320': 'the market trades down comes back up trades down one single pass comes up stops there',
 'W0323': 'ended up touching it later on in the morning and then we saw retrace lower that was a reason for concern',
 'W0324': 'the market trades up and then we have that weakness intraday',
 'W0327': 'we have a rejection block here after the market runs up at the nine o\'clock hour we break down one more time',
 'W0328': 'came back down bullish breaker which is what\'s being annotated here consolidated higher order block',
 'W0331': 'trades up into it there and then delivers down to that level',
 'W0333': 'here is that Weekly order Block Level and then we have a fair value Gap',
 'W0334': 'trades up into it now where is 10 handles from that point',
 'W0335': 'we have a higher low and then we have this low here so we Wick down into this',
 'W0336': 'so we open trade down into that shaded area I told you it would be treated as a',
 'W0337': "traded up to Monday's low which is an immediate rebalance then price starts to go lower",
 'W0338': 'every candle next candle here we trade down to that low',
 'W0340': 'it rallies up into this small little fair value Gap here and then we have the',
 'W0344': 'price went down and then this candle here opened went up and then went down again',
 'W0347': 'between the scandals high and this candle is low and then we\'ll annotate that',
 'W0348': 'if we trade down to it like that that might cause it to find some support',
}


def main():
    dropped = []
    per_file = collections.defaultdict(list)
    for w, q in QUOTE.items():
        win = wins[w]
        rel = win['path']
        t = norm(corp[rel]['text'])
        pos = t.find(norm(q))
        if pos < 0 or len(q.split()) > 25:
            dropped.append((w, 'quote not located or too long'))
            continue
        wi = len(t[:pos].split())
        if not (win['window_words'][0] <= wi <= win['window_words'][1]):
            dropped.append((w, 'hit outside its window'))
            continue
        per_file[rel].append(dict(window_id=w, quote=q, hit_word_index=wi,
                                  **dict(zip(['object', 'direction', 'time_order', 'next', 'notes'],
                                             EVENTS[w]))))
    pair_by_file = {}
    for w, (tag, wording) in PAIR_WIN.items():
        pair_by_file[wins[w]['path']] = (tag, wording, w)
    pdir = B / 'pairing'
    pdir.mkdir(exist_ok=True)
    idx = []
    read_files = {wins[w]['path'] for w in list(QUOTE) + list(PAIR_WIN)}
    for rel in sorted(read_files):
        c = next((x for x in cands if x['path'] == rel), None)
        if c is None:
            continue
        evs = sorted(per_file.get(rel, []), key=lambda e: e['hit_word_index'])
        tag, wording, pw = pair_by_file.get(rel, ('UNKNOWN', 'no instrument-naming window read', None))
        usable = 'yes' if tag.startswith('EURUSD') else ('unknown' if tag == 'UNKNOWN' else 'no')
        nw = sum(1 for x in wins.values() if x['path'] == rel)
        name = Path(rel).stem
        out = [f'# Story pairing — {name}', '',
               f'- **date stated in filename:** {c["date"]}',
               f'- **split (fixed before any data was loaded):** {c["split"]} '
               f'(day {c["day"]}, {"odd" if c["day"] % 2 else "even"})',
               f'- **pair stated in a read window:** {tag} — window `{pw}`' if pw else
               '- **pair stated in a read window:** UNKNOWN — no instrument-naming window was read',
               f'  > naming wording: {wording}',
               f'- **windows read for this transcript:** {nw}',
               f'- **file sha256:** `{c["sha256"]}`',
               f'- **usable_for_EURUSD_test:** {usable}', '',
               '## Ordered narrated events', '']
        if evs:
            for i, e in enumerate(evs, 1):
                out += [f'{i}. **object/level:** {e["object"]} · **direction:** {e["direction"]} · '
                        f'**time/order:** {e["time_order"]}',
                        f'   **what happened next:** {e["next"]}',
                        f'   > "{e["quote"]}"',
                        f'   window `{e["window_id"]}` at word {e["hit_word_index"]}'
                        + (f' · {e["notes"]}' if e['notes'] else ''), '']
        else:
            out += ['NOT_IN_SOURCES — no narrated event was extracted from the windows read for this '
                    'transcript. It is listed for completeness, not as usable evidence.', '']
        out += ['## What this transcript does NOT settle', '',
                '- No price series was loaded, so nothing here is checked against candles.',
                '- Level names he says as "here" / "this low" are not resolved to numbers; see gaps.md.', '']
        (pdir / f'{name}.md').write_text('\n'.join(out) + '\n')
        idx.append(dict(file=rel, date=c['date'], split=c['split'], pair_stated=tag,
                        windows_read=nw, narrated_events_count=len(evs),
                        usable_for_EURUSD_test=usable))
    with (B / 'pairing_index.tsv').open('w') as f:
        f.write('file\tdate\tsplit\tpair_stated\twindows_read\tnarrated_events_count\tusable_for_EURUSD_test\n')
        for r in idx:
            f.write('\t'.join(str(r[k]) for k in ['file', 'date', 'split', 'pair_stated',
                                                  'windows_read', 'narrated_events_count',
                                                  'usable_for_EURUSD_test']) + '\n')
    print(json.dumps(dict(transcripts_written=len(idx),
                          narrated_events=sum(r['narrated_events_count'] for r in idx),
                          usable_eurusd=sum(1 for r in idx if r['usable_for_EURUSD_test'] == 'yes'),
                          dropped=dropped), indent=1))


if __name__ == '__main__':
    main()
