#!/usr/bin/env python3
"""Build Task 1 understanding cards + Task 2 comparison artefacts from claims.jsonl only.

Every substantive line is rendered from a claim's statement + verbatim quote + claim_id + file +
window_id. Section (c) OBSERVABLES is the ONLY authored section: it is labelled
ENGINEERING_HYPOTHESIS, names the claim_ids it is derived from, and is expressed as
relative-to-local-context comparisons with a candle_observable flag. No fixed thresholds.
Sections with no claim are written NOT_IN_SOURCES rather than filled from memory.
"""
import json, collections, re
from pathlib import Path

B = Path(__file__).resolve().parent.parent
rows = [json.loads(l) for l in (B / 'claims.jsonl').read_text().splitlines() if l.strip()]
by = {r['claim_id']: r for r in rows}
wins = {json.loads(l)['window_id']: json.loads(l)
        for l in (B / 'windows.jsonl').read_text().splitlines() if l.strip()}
concepts = sorted({r['concept'] for r in rows})

SECTIONS = [
    ('a', 'PURPOSE', 'purpose'),
    ('b', 'RECOGNITION (his criteria and his rejections)', 'recognition'),
    ('d', 'HOW HE TREATS IT', 'treatment'),
    ('e', 'COMPARING INSTANCES', 'comparing'),
    ('f', 'INTERACTIONS', 'interactions'),
    ('g', 'TIMEFRAME', 'timeframe'),
    ('h', 'FAILURE / INVALIDATION and DISCRETION', 'failure'),
    ('i', 'VARIANTS (kept parallel, never merged)', 'variants'),
]

# (c) OBSERVABLES - ENGINEERING_HYPOTHESIS. Authored, not quoted. Each entry:
#   concept: [(derived observable, candle_observable flag, [claim_ids it comes from])]
OBS = {
 'draw_on_liquidity': [
   ('a candidate target is a prior swing extreme or an unfilled range that price has not yet returned into, ranked by whether it is still untouched rather than by distance', 'true', ['U0004', 'U0005']),
   ('arrival is not bound to the next bar or next day; the observable is eventual return, not elapsed time', 'unknown', ['U0006']),
 ],
 'buy_side_liquidity': [
   ('a level qualifies by having two or more near-equal highs above which resting orders are presumed; the observable is near-equality relative to local swing spacing, not an absolute tolerance', 'true', ['U0008']),
   ('a run is observable as a trade above that level followed by closes back below it', 'true', ['U0011', 'U0013']),
   ('that orders actually rest there is not visible on candles', 'false', ['U0008']),
 ],
 'sell_side_liquidity': [
   ('mirror of buy side: near-equal or old lows, then a trade below and closes back above', 'true', ['U0016', 'U0017', 'U0019']),
   ('persistence is observable as repeated taking of lows while highs are rarely taken', 'true', ['U0018']),
   ('the counterparty motive he states is not observable on candles', 'false', ['U0015']),
 ],
 'equal_highs': [
   ('near-equality of two or more highs measured against the local swing amplitude, not a fixed tick tolerance', 'true', ['U0022', 'U0027']),
   ('cleanliness he mentions maps to how little separation and how few intervening bars sit between the equal highs', 'unknown', ['U0022']),
   ('significance rises with the timeframe the equality is visible on', 'true', ['U0024', 'U0025']),
 ],
 'equal_lows': [
   ('near-equal lows relative to local swing amplitude, then a trade below them', 'true', ['U0032', 'U0035']),
   ('after the run, the observable he describes is a return back inside the prior range', 'true', ['U0029']),
 ],
 'fair_value_gap': [
   ('a three-candle arrangement whose middle candle leaves an unfilled span between the outer candles extremes; persistence = later bars not trading back through it', 'true', ['U0036', 'U0038']),
   ('location is judged relative to the equilibrium of the displacement swing that produced it', 'true', ['U0038']),
   ('when two gaps compete, the one nearer the discount end is preferred in his worked case; that is a relative position test, not a size test', 'true', ['U0040']),
   ('his five-handle remark is chart-specific; adopting it as a threshold would be invention', 'unknown', ['U0037']),
 ],
 'order_block': [
   ('a run of same-direction closes whose START is the opening of the first candle in the run, not the last candle before the move', 'true', ['U0045', 'U0047']),
   ('the competing single-candle framing must be carried as a separate definition_id, not averaged', 'true', ['U0046']),
   ('violation is observable as price trading through the far side of that run', 'true', ['U0048']),
   ('what makes something NOT an order block is cut off in the read window', 'unknown', ['U0051']),
 ],
 'displacement': [
   ('energy is observable as the size of the moving candles relative to the immediately preceding local candles, plus closes beyond the level rather than mere wicks', 'true', ['U0055', 'U0056', 'U0057']),
   ('lethargic is the same comparison failing: range expansion no larger than its local neighbours', 'true', ['U0055']),
   ('bodies respecting an inefficiency is observable as closes staying on one side of the gap', 'true', ['U0062']),
 ],
 'shift_in_market_structure': [
   ('a break of a local swing in the opposite direction followed by displacement, evaluated relative to the swing that preceded it', 'true', ['U0066', 'U0067']),
   ('when two candidate breaks exist he selects by what he is playing, so a deterministic tie-break is not given', 'unknown', ['U0063']),
 ],
 'dealing_range': [
   ('the range is bounded by the high and low of the most recent delivery leg, chosen over older legs', 'true', ['U0071', 'U0076']),
   ('failure is observable as trading outside those bounds', 'true', ['U0072']),
   ('which structure has provided a means for opportunity is a judgement he does not reduce to candles', 'unknown', ['U0069']),
 ],
 'equilibrium': [
   ('the midpoint of the most recent price swing, i.e. relative to that swing and recomputed when a newer swing forms', 'true', ['U0078', 'U0080']),
   ('expansion is observable as speed of departure from that midpoint relative to prior local bars', 'true', ['U0079']),
 ],
 'premium_discount': [
   ('position within the current range, expressed as above/below its midpoint; no absolute price meaning', 'true', ['U0082', 'U0084']),
   ('the carrying-charge sense of premium is a different observable entirely (near vs deferred contract price) and needs contract data, not candles', 'false', ['U0087']),
 ],
 'kill_zone': [
   ('a clock window in New York time; the observable is time-of-bar, not price', 'false', ['U0088', 'U0091', 'U0092']),
   ('conflicting stated bounds (1am vs 2am start) must remain alternatives selected by source, not averaged', 'unknown', ['U0088', 'U0089']),
 ],
 'time_of_day': [
   ('overlap of a clock window with a higher-timeframe level; both must be present', 'true', ['U0095']),
   ('deviation from the expected behaviour at that time is allowed, so the gate is not hard', 'unknown', ['U0099']),
 ],
 'bias': [
   ('direction is derived from key support/resistance structure and from the draw, ranked above other inputs', 'true', ['U0100', 'U0101']),
   ('a bias is non-exclusive: opposing moves may still work, so it cannot be a hard filter', 'unknown', ['U0103']),
 ],
 'stop_loss': [
   ('placement is structural: beyond the low/high of the specific candle or the mean threshold of the zone, not a fixed distance', 'true', ['U0106', 'U0109']),
   ('a hit stop is not evidence the idea was invalid; invalidation and stop placement are separate observables', 'unknown', ['U0108']),
 ],
 'break_even': [
   ('trigger is an event (first profit taken, or a fraction of the objective reached), not elapsed time', 'true', ['U0114', 'U0115']),
   ('the two stated triggers conflict and must stay parallel', 'unknown', ['U0114', 'U0115']),
 ],
 'partials': [
   ('quantity is explicitly left to the trader, so any fraction would be an engineering choice, not his method', 'unknown', ['U0118', 'U0119']),
   ('locations are described as logical levels, i.e. structure-derived rather than fixed', 'true', ['U0120']),
 ],
 'being_wrong': [
   ('the observable is a list of characteristics that preceded the failed idea, i.e. features recorded before the outcome', 'unknown', ['U0122', 'U0123']),
 ],
 'risk': [
   ('risk is reduced by entering nearer the structural level, so it is a relative placement property, not a percentage he fixes for all cases', 'true', ['U0128']),
 ],
 'no_trade': [
   ('absence of the expected manifestation is itself the signal: no displacement, no return to equilibrium, or a stated clock window', 'true', ['U0130', 'U0132', 'U0129']),
   ('day-of-week branches are calendar observables, not price', 'false', ['U0134']),
 ],
}

# Task 2 curated triples, keyed by a distinctive substring of the claim quote.
CMP = {
 'predominantly have to consider': ('holding a directional bias', 'locating the next draw on liquidity', 'he says you predominantly have to consider where the next draw is'),
 'ripe for the taking': ('an ordinary set of lows', 'lows he calls candyland', "he calls them ripe for the taking and couples them with optimal trade entry"),
 'continuously and rarely ever': ('taking out the highs', 'taking out sell side liquidity', 'one happens continuously while the other rarely happens'),
 'Greater significance': ('equal highs on a lower timeframe', 'equal highs on a daily chart', 'the daily ones are of greater significance'),
 "more apparent": ('equal highs on the higher chart', 'equal highs viewed on a daily', 'dropping to the daily makes them more apparent'),
 "by itself that's enough": ('waiting for extra confirmation', 'the run above the equal highs alone', "by itself that's enough"),
 'I like to look at old lows': ('other targeting references', 'old lows and old highs', 'stated personal preference when targeting'),
 'more of a quality type setup': ('an area without a fair value gap', 'an area with a fair value gap', 'having the gap makes it more of a quality type setup'),
 'I favored the lower fair value': ('the upper fair value gap', 'the lower fair value gap', 'preference stated for that session; no general rule given'),
 'a lot more definition': ('the higher timeframe view of the order block', 'the daily chart view', 'the daily shows a lot more definition'),
 'most recent one and this is my dealing range': ('the earlier stage of the delivery', 'the most recent stage', 'he wants to use the most recent one'),
 'most active premium arrays': ('inactive premium arrays', 'the most active premium arrays', 'activity is the selection criterion'),
 'ideal ICT London kill zone': ('other London kill zone bounds', '2 a.m. for learning', 'he calls it the ideal window for your learning'),
 'support resistance trumps everything': ('every other bias input', 'key support and resistance levels', 'it trumps everything; without it there is no directional bias'),
 'better opinion about what the daily bias': ('a single input', 'a number of things combined', 'combining them gives a better opinion'),
 'best setups': ('taking every reversal pattern', 'only setups aligned with the daily bias', 'filtering gives the best setups'),
 'smaller stop loss placement': ('stop placement from the higher timeframe alone', 'higher timeframe levels applied to lower timeframe charts', 'smaller stop placement and by default lower risk'),
 'more Gap in between': ('the alternative order type', 'the order that leaves less gap to the stop', 'the other order creates more gap between entry and stop'),
 'worst thing': ('moving to break even early on long-term trades', 'leaving the stop alone', 'break even on long-term trading is called the worst thing'),
 'reducing risk': ('increasing risk to make losses back', 'reducing risk', 'he says it can be done by reducing risk instead'),
 'a lot less in terms of risk exposure': ('buying higher', 'buying lower', 'buying lower offers a lot less risk exposure'),
 "which one's the shift in market structure": ('the other candidate break', "the break he is playing toward the run up", 'he selects by which move he is playing'),
 'entire trade on the initial': ('scaling out with partials', 'no partials on low resistance liquidity runs', 'the run type decides; he stakes the whole trade'),
}


def line(r):
    return (f'- {r["statement"]}\n'
            f'  > "{r["quote"]}"\n'
            f'  `[{r["claim_id"]}]` · `{Path(r["path"]).name}` · window `{r["window_id"]}`'
            + (f' · note: {r["notes"]}' if r.get('notes') else ''))


def main():
    cdir = B / 'concepts'
    cdir.mkdir(exist_ok=True)
    idx = []
    empty_counts = {}
    for c in concepts:
        cr = [r for r in rows if r['concept'] == c]
        nw = len({r['window_id'] for r in cr})
        allw = sum(1 for w in wins.values() if w['concept'] == c)
        out = [f'# Understanding card — {c.replace("_", " ")}', '',
               f'Windows extracted for this concept: **{allw}** (target 15). '
               f'{"THIN" if allw < 15 else "Meets the 15-window budget."}',
               f'Claims: {", ".join(r["claim_id"] for r in cr)}', '',
               'Every quoted line below is verbatim (≤25 words) from a window logged this session. '
               'Section (c) is explicitly an ENGINEERING_HYPOTHESIS, not his words. '
               'Empty sections read NOT_IN_SOURCES.', '']
        empty = 0
        for letter, title, key in SECTIONS[:2]:
            out.append(f'## ({letter}) {title}')
            sel = [r for r in cr if r['section'] == key]
            out += [line(r) for r in sel] if sel else ['NOT_IN_SOURCES']
            empty += 0 if sel else 1
            out.append('')
        out.append('## (c) OBSERVABLES — ENGINEERING_HYPOTHESIS (needs owner approval)')
        if c in OBS:
            for text, flag, ids in OBS[c]:
                ok = [i for i in ids if i in by]
                out.append(f'- {text}\n  `candle_observable: {flag}` · derived from '
                           f'{", ".join("`"+i+"`" for i in ok) if ok else "NO_CLAIM"}'
                           ' · **ENGINEERING_HYPOTHESIS — needs owner approval**')
        else:
            out.append('NOT_IN_SOURCES')
            empty += 1
        out.append('')
        for letter, title, key in SECTIONS[2:]:
            out.append(f'## ({letter}) {title}')
            sel = [r for r in cr if r['section'] == key]
            if key == 'failure':
                sel = sel + [r for r in cr if r['section'] != key and 'DISCRETION' in r.get('notes', '')]
            out += [line(r) for r in sel] if sel else ['NOT_IN_SOURCES']
            empty += 0 if sel else 1
            out.append('')
        (cdir / f'{c}.md').write_text('\n'.join(out) + '\n')
        empty_counts[c] = empty
        idx.append(dict(concept=c, card=f'concepts/{c}.md', windows_extracted=allw,
                        thin=allw < 15, claim_ids=[r['claim_id'] for r in cr],
                        sections_empty=empty,
                        observables_label='ENGINEERING_HYPOTHESIS' if c in OBS else 'NOT_IN_SOURCES'))
    (B / 'concepts.jsonl').write_text('\n'.join(json.dumps(r) for r in idx) + '\n')

    # ---- Task 2 ----
    comps = []
    unanalysed = []
    for r in rows:
        if r['section'] != 'comparing':
            continue
        hit = next((k for k in CMP if k.lower() in r['quote'].lower()), None)
        if hit:
            a, b, why = CMP[hit]
            comps.append(dict(comparison_id=f'K{len(comps)+1:03d}', concept=r['concept'],
                              things_compared=[a, b], which_wins=b, stated_reason=why,
                              quote=r['quote'], claim_id=r['claim_id'], path=r['path'],
                              window_id=r['window_id']))
        else:
            unanalysed.append(r['claim_id'])
    (B / 'comparisons.jsonl').write_text('\n'.join(json.dumps(r) for r in comps) + '\n')
    md = ['# Comparisons by concept', '',
          'Each record is a concrete comparative/preference statement he makes, with the quote that '
          'carries it. `which_wins` is his stated preference, never a profitability judgement.', '']
    for c in sorted({r['concept'] for r in comps}):
        md.append(f'## {c.replace("_", " ")}')
        for r in comps:
            if r['concept'] != c:
                continue
            md.append(f'- **{r["things_compared"][0]}** vs **{r["things_compared"][1]}** → wins: '
                      f'**{r["which_wins"]}**. Reason he gives: {r["stated_reason"]}.\n'
                      f'  > "{r["quote"]}"\n  `[{r["claim_id"]}]` `{Path(r["path"]).name}`')
        md.append('')
    md += ['## Comparative claims not reduced to a triple', '',
           ('These carry comparative wording but were not turned into a things_compared/which_wins '
            'record because the two sides are not both named in the read window: '
            + ', '.join(f'`{i}`' for i in unanalysed)) if unanalysed else 'none', '']
    (B / 'comparisons_by_concept.md').write_text('\n'.join(md) + '\n')

    raw = [json.loads(l) for l in (B / 'comparisons_raw.jsonl').read_text().splitlines() if l.strip()]
    cnt = collections.Counter(r['degree_word'] for r in raw)
    dw = ['# Degree words — mechanical sweep', '',
          f'{len(raw)} distinct comparative/preference windows were mined mechanically across the '
          'corpus (first 3000 unique hits, de-duplicated by normalised text). Counts below are '
          'occurrences in that sweep, **not** a claim about importance.', '',
          '| degree word | hits in sweep |', '|---|---:|']
    for w, n in cnt.most_common():
        dw.append(f'| `{w}` | {n} |')
    dw += ['', '## What each degree word is contrasted with, where a claim establishes it', '']
    for r in comps:
        dw.append(f'- `{r["concept"].replace("_"," ")}`: {r["things_compared"][0]} ↔ '
                  f'{r["things_compared"][1]} — > "{r["quote"]}" `[{r["claim_id"]}]`')
    dw += ['', 'Degree words with no adjudicated contrast in this session stay uninterpreted; '
           'the raw windows are in `comparisons_raw.jsonl` for a later round.', '']
    (B / 'degree_words.md').write_text('\n'.join(dw) + '\n')
    print(json.dumps(dict(cards=len(idx), thin=[r['concept'] for r in idx if r['thin']],
                          comparisons=len(comps), comparative_claims_unreduced=len(unanalysed),
                          degree_word_hits=len(raw),
                          empty_sections_total=sum(empty_counts.values())), indent=1))


if __name__ == '__main__':
    main()
