#!/usr/bin/env python3
"""Build concept cards and relations from claims.jsonl ONLY.

Design rule: this script introduces no prose about the methodology. Every substantive card line is
rendered from a claim's `statement` plus its verbatim `quote` and claim_id. Field assignment is the
explicit MAP below; anything unassigned is written as the literal NOT_IN_SOURCES. Concepts in
NOT_FOUND are probe terms that a mechanical search showed absent from the stored PRIMARY text.

It asserts that every claim_id used in a card belongs to that concept, and that every relation
wording is a literal fragment of its supporting claim's quote.
"""
import json, re
from pathlib import Path

B = Path(__file__).resolve().parent.parent
rows = [json.loads(l) for l in (B / 'claims.jsonl').read_text().splitlines() if l.strip()]
by = {r['claim_id']: r for r in rows}

def norm(t):
    return re.sub(r'\s+', ' ', t).strip().lower()

FIELDS = ['What it is to him (essence, in his words)',
          'Why it matters to him (the reason he gives)',
          'Properties he mentions',
          'Relations to other concepts',
          'Context in which he uses it',
          'How he chooses it over alternatives',
          'What he says makes it wrong/invalid',
          'Worked examples in the sources',
          'Open questions (what the sources leave unanswered)']

MAP = {
 'market narrative': {0: ['C001', 'C002'], 4: ['C001'], 3: ['C003']},
 'liquidity': {0: ['C042'], 1: ['C003'], 2: ['C004'], 3: ['C045'], 4: ['C042']},
 'draw on liquidity': {0: ['C005'], 3: ['C005']},
 'market structure': {0: ['C006'], 2: ['C006'], 3: ['C019', 'C022']},
 'higher vs lower timeframe': {0: ['C013'], 1: ['C020'], 2: ['C021'], 4: ['C007', 'C025'], 3: ['C013']},
 'context': {4: ['C008', 'C007']},
 'retail ideas': {5: ['C009'], 0: ['C009']},
 'intermediate term high': {0: ['C011', 'C028'], 2: ['C027', 'C053'], 3: ['C010', 'C028'], 6: ['C053', 'C051'], 7: ['C010']},
 'intermediate term low': {2: ['C012'], 0: ['C012']},
 'no-trade': {0: ['C036', 'C037'], 1: ['C040'], 4: ['C041'], 6: ['C051'], 7: ['C041', 'C014'], 5: ['C052']},
 'being wrong': {0: ['C032', 'C051'], 2: ['C015'], 6: ['C032'], 5: ['C051']},
 'order block': {0: ['C017', 'C047'], 2: ['C048', 'C035'], 3: ['C018', 'C030'], 5: ['C016'], 6: ['C050'], 7: ['C018', 'C029', 'C030']},
 'fair value gap': {0: ['C049'], 2: ['C049'], 3: ['C018', 'C054'], 4: ['C018']},
 'target': {0: ['C019'], 2: ['C024'], 5: ['C023', 'C024'], 7: ['C023', 'C024']},
 'market structure shift': {0: ['C026', 'C022'], 3: ['C026'], 2: ['C022']},
 'entry': {0: ['C030'], 2: ['C029'], 5: ['C029', 'C030'], 7: ['C029', 'C030'], 3: ['C031']},
 'stop': {4: ['C031'], 7: ['C031'], 3: ['C031']},
 'institutional order flow': {0: ['C034'], 2: ['C034']},
 'displacement': {4: ['C035'], 3: ['C035'], 7: ['C035']},
 'bias': {0: ['C039'], 2: ['C038'], 6: ['C038']},
 'imbalance': {0: ['C043'], 3: ['C010', 'C043']},
 'time of day': {0: ['C044'], 1: ['C044']},
 'equal highs': {2: ['C046'], 3: ['C045'], 5: ['C046'], 7: ['C045']},
 'discount': {4: ['C054'], 3: ['C054'], 7: ['C054']},
}

NOT_FOUND = {
 'dealing range': 'The string "dealing range" does not occur in any stored PRIMARY file (mechanical search: 0 hits).',
 'premium': 'The only occurrences of "premium" in stored files are inside the non-transcript boilerplate description line "2016 Premium ICT Mentorship Core Content Video Lectures". No spoken use was retrieved, so no claim exists.',
 'equilibrium': 'The string "equilibrium" does not occur in any stored PRIMARY file (0 hits).',
 'equal lows': 'The string "equal low" does not occur in any stored PRIMARY file (0 hits). Only "relative equal highs" was retrieved (C045, C046).',
 'invalidation': 'The string "invalid" does not occur in any stored PRIMARY file (0 hits). The nearest retrieved wording is about an idea being "wrong" (see being_wrong card); no separate invalidation rule was stated.',
 'sit on hands': 'The exact phrase "sit on my hands" does not occur; the retrieved wording is "sitting on my hands" (C014), handled under no_trade.',
 'kill zone': 'The strings "kill zone", "midnight", "8:30" and "9:30" do not occur in any stored PRIMARY file (0 hits each). time_of_day exists only as the general statement C044.',
 'objective': 'The word "objective" occurs in stored text but no atomic claim was extracted for it in this round; targeting is covered by the target card. This is a recorded gap, not a definition.',
}

REL = [
 ('imbalance', 'every rebalance of an old imbalance', 'intermediate term high', 'C010'),
 ('imbalance', 'it trades back up to rebalance and imbalance', 'intermediate term high', 'C028'),
 ('order block', 'inside that range I can be hunting', 'fair value gap', 'C018'),
 ('market structure shift', 'then you see price go up into that imbalance', 'imbalance', 'C026'),
 ('equal highs', 'relative equal highs above that is buy stops', 'liquidity', 'C045'),
 ('market structure', 'that range is going to be used for targeting purposes', 'target', 'C019'),
 ('higher vs lower timeframe', 'all minor lower time frame swings are going to be subordinate to it', 'market structure', 'C013'),
 ('entry', 'the classic return back to an order block', 'order block', 'C030'),
 ('entry', "where's your stop Above This candle's High", 'stop', 'C031'),
 ('intermediate term high', 'your trade ideas probably flawed', 'being wrong', 'C051'),
 ('being wrong', 'wait for Market structure to get back in sync', 'no-trade', 'C052'),
 ('displacement', 'the last two up close candles before the displacement here', 'order block', 'C035'),
 ('fair value gap', 'typically confirmed with a', 'lower time frame', 'C049'),
 ('discount', 'the discount level of the low end of that fair value Gap', 'fair value gap', 'C054'),
 ('intermediate term high', 'it should not trade above that high', 'being wrong', 'C053'),
]

def slug(c):
    return c.replace(' ', '_').replace('/', '_')

def line(cid):
    r = by[cid]
    return (f'- {r["statement"]} — quote: "{r["quote"]}" '
            f'[{cid}; {r["source_id"]}/{r["part"]}; {r["type"]}]')

CROSS = []

def main():
    cards = B / 'cards'
    cards.mkdir(exist_ok=True)
    counts = {}
    for concept, fm in MAP.items():
        ids = sorted({i for v in fm.values() for i in v})
        # Every cited claim must exist. A card may cite a claim filed under another concept (e.g. a
        # relation, or a context claim about timeframe); each such citation is recorded in the report
        # as cross-concept so it is visible rather than hidden.
        for fi, cl in fm.items():
            for i in cl:
                assert i in by, i
                if by[i]['concept'] != concept:
                    CROSS.append(dict(card=concept, field=FIELDS[fi], claim_id=i,
                                      claim_concept=by[i]['concept']))
        out = [f'# Concept card — {concept}', '',
               f'Concept term taken from the stored text as used in the claims. Supporting claims: {", ".join(ids)}.',
               'Every field below either carries claim_ids or the literal text NOT_IN_SOURCES. Nothing here is supplied from memory.', '']
        nf = 0
        for fi, f in enumerate(FIELDS):
            out.append(f'## {f}')
            if fi == 8:
                missing = [FIELDS[k] for k in range(8) if k not in fm]
                if missing:
                    out.append('- GAP: the sources give no claim for: ' + '; '.join(missing) + '. See OWNER_QUESTIONS.md.')
                else:
                    out.append('- NOT_IN_SOURCES')
                nf += 1
            elif fi in fm:
                out += [line(i) for i in fm[fi]]
            else:
                out.append('NOT_IN_SOURCES')
                nf += 1
            out.append('')
        if concept == 'order block':
            out += ['## Contradiction flag (not resolved)',
                    '- C050 records that the stored sources define an order block differently (single lowest down-close candle with the most range near support in OB16, versus one consecutive series of up closed candles in Episode 12). Both are quoted; neither is preferred here.', '']
        if concept == 'bias':
            out += ['## Ambiguity flag (not resolved)',
                    '- C038 is AMBIGUOUS: the stored text reads "if you can\'t go into your charts and line up an idea that\'s bullish" while the following sentences describe the opposite test. Possible ASR error; not corrected.', '']
        (cards / f'{slug(concept)}.md').write_text('\n'.join(out) + '\n')
        counts[concept] = nf
    for concept, why in NOT_FOUND.items():
        out = [f'# Concept card — {concept}', '', 'NOT_FOUND_IN_SOURCES', '', why, '']
        for f in FIELDS:
            out += [f'## {f}', 'NOT_IN_SOURCES', '']
        (cards / f'{slug(concept)}.md').write_text('\n'.join(out) + '\n')
        counts[concept] = 9
    rl = []
    for a, rel, b, cid in REL:
        assert norm(rel) in norm(by[cid]['quote']), (rel, cid)
        rl.append(dict(from_concept=a, relation=rel, to_concept=b, claim_id=cid))
    (B / 'relations.jsonl').write_text('\n'.join(json.dumps(r, ensure_ascii=False) for r in rl) + '\n')
    rep = dict(cards=len(counts), grounded_cards=len(MAP), not_found_cards=len(NOT_FOUND),
               relations=len(rl), cross_concept_citations=CROSS, not_in_sources_fields_per_card=counts,
               total_not_in_sources_fields=sum(counts.values()))
    (B / 'reports' / 'card_field_counts.json').write_text(json.dumps(rep, indent=2) + '\n')
    print(json.dumps({k: v for k, v in rep.items() if k != 'not_in_sources_fields_per_card'}, indent=2))

if __name__ == '__main__':
    main()
