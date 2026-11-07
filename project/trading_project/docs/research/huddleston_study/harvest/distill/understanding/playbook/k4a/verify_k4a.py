#!/usr/bin/env python3
import os, re, json, hashlib, argparse, collections, sys
from pathlib import Path
OUT = Path(__file__).resolve().parent
CORPUS = Path(os.environ.get('K4A_CORPUS','/home/user/_external/ict-index/ict-index-e8c40a8dae5ea6689926f28c7184ce3e2fb85b9c'))
EXPECTED_TARBALL_SHA = '4213e692f7c978dab8fe5ba124d34d887f17316c89d27bb2a7406fd3776f769d'
QS = ['Q01','Q02','Q03','Q04','Q05','Q06','Q07','Q08','Q09','Q10']
ERA_LABELS = {'E1_EARLY_SERIES':'السلسلة المبكرة','E2_2016':'٢٠١٦','E3_2017':'٢٠١٧','E4_2019_2022':'٢٠١٩–٢٠٢٢','E5_2023_2024':'٢٠٢٣–٢٠٢٤'}
def norm(t): return re.sub(r'\s+',' ',t).strip()
def text_of(p):
    d=json.loads(Path(p).read_text(encoding='utf-8',errors='replace'))
    if isinstance(d,list): return ' '.join(str(x.get('Transcription','')) for x in d if isinstance(x,dict))
    if isinstance(d,dict) and 'Transcription' in d: return str(d['Transcription'])
    return json.dumps(d)
def ar(s): return str(s).translate(str.maketrans('0123456789','٠١٢٣٤٥٦٧٨٩'))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--json',action='store_true'); a=ap.parse_args()
    claims=json.loads((OUT/'claims.json').read_text())
    windows=json.loads((OUT/'windows.json').read_text())
    gaps=json.loads((OUT/'gaps.json').read_text())
    kw=json.loads((OUT/'keywords.json').read_text())
    failures=[]; passed=0
    by_wid={r['window_id']:r for r in windows}
    for c in claims:
        p=CORPUS/c['transcript_id']
        if not p.exists(): failures.append((c['claim_id'],'transcript missing')); continue
        t=norm(text_of(p)); q=norm(c['quote'])
        ok=True
        if q not in t: failures.append((c['claim_id'],'quote not verbatim')); ok=False
        if len(q.split())>25: failures.append((c['claim_id'],'quote over 25 words')); ok=False
        if c.get('quote_word_count')!=len(q.split()): failures.append((c['claim_id'],'word count mismatch')); ok=False
        pos=len(t[:t.find(q)].split()) if q in t else -1
        if pos!=c['position']: failures.append((c['claim_id'],'position mismatch')); ok=False
        w=by_wid.get(c['window_id'])
        if not w or not w.get('opened') or not w.get('printed_for_reading'): failures.append((c['claim_id'],'window not opened')); ok=False
        elif not (w['window_words'][0]<=c['position']<=w['window_words'][1]): failures.append((c['claim_id'],'position outside window')); ok=False
        md=(OUT/f"{c['question_id']}.md").read_text()
        if q not in md: failures.append((c['claim_id'],'quote missing from question file')); ok=False
        if hashlib.sha256(p.read_bytes()).hexdigest()!=c['transcript_sha256']: failures.append((c['claim_id'],'transcript hash mismatch')); ok=False
        if ok: passed+=1
    win={}
    for q in QS:
        req=sum(1 for r in windows if r['question_id']==q and r.get('requested'))
        op=sum(1 for r in windows if r['question_id']==q and r.get('opened') and r.get('printed_for_reading'))
        win[q]={'requested':req,'opened':op}
        if kw[q]['requested']!=req or kw[q]['opened']!=op: failures.append((q,'window count mismatch'))
    gaps_ok=all(g.get('status')=='NOT_FOUND_IN_CORPUS' and g.get('terms_tried') for g in gaps)
    if not gaps_ok: failures.append(('gaps','gap record invalid'))
    manifest_ok=True
    for line in (OUT/'MANIFEST.sha256').read_text().splitlines():
        if not line.strip(): continue
        sha,path=line.split('  ',1); p=Path(path)
        if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=sha:
            manifest_ok=False; failures.append(('manifest','external hash mismatch: '+path))
    tarball=Path('/home/user/_external/ict-index/e8c40a8dae5ea6689926f28c7184ce3e2fb85b9c.tar.gz')
    if tarball.exists() and hashlib.sha256(tarball.read_bytes()).hexdigest()!=EXPECTED_TARBALL_SHA:
        failures.append(('tarball','sha mismatch'))
    result=dict(quote_passed=passed, quote_total=len(claims), windows=win,
                distinct_opened_transcripts=len({r['transcript_id'] for r in windows if r.get('opened') and r.get('printed_for_reading')}),
                era_distribution=dict(collections.Counter(r['era'] for r in windows if r.get('opened') and r.get('printed_for_reading'))),
                manifest_ok=manifest_ok, gaps_ok=gaps_ok, failures=failures)
    if a.json: (OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    else:
        print('التحقق: نجاح/المجموع: '+ar(f'{passed}/{len(claims)}'))
        print('النوافذ المطلوبة/المفتوحة:')
        for q in QS: print(q+' '+ar(f"{win[q]['requested']}/{win[q]['opened']}"))
        print('نصوص مميزة مفتوحة: '+ar(result['distinct_opened_transcripts']))
        print('توزيع الحقب: '+', '.join(f'{ERA_LABELS.get(k,k)}: {ar(v)}' for k,v in result['era_distribution'].items()))
        if failures:
            print('إخفاقات:')
            for f in failures: print(' - '+str(f[0])+': '+str(f[1]))
    return 1 if failures else 0
if __name__=='__main__': sys.exit(main())
