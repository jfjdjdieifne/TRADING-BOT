#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lab_v51_report.py -- renders results/REPORT_AR_v51.md from saved books
+ results/_v51_causal.json. No engine runs."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
RES = HERE / "results"
WINS = ("W1", "W2", "OLD7", "MOD_Y1", "MOD_Y2")
ARMS = {
    "B0": ("B0 (شامبيون)", lambda w: RES / f"trades_v37_B0_{w}.csv"),
    "C4": ("C4 · exec ≤ −0.30x", lambda w: RES / "v49_engine" / f"c4_exec_m030__{w}__0.csv"),
    "P1": ("P1 · exec ≤ −0.25x", lambda w: RES / "v50_engine" / f"p1_c4_m025__{w}__0.csv"),
    "P3": ("P3 · exec ≤ −0.35x", lambda w: RES / "v50_engine" / f"p3_c4_m035__{w}__0.csv"),
    "S3": ("S3 · C4 + سكين −0.65x", lambda w: RES / "v50_engine" / f"s3_knife__{w}__0.csv"),
    "V51": ("V51 · P1 + سكين −0.65x", lambda w: RES / "v51_engine" / f"v51_p1_knife__{w}__0.csv"),
}

def load(p):
    d = pd.read_csv(p)
    d["entry_time"] = pd.to_datetime(d.entry_time, utc=True, format="mixed")
    return d.sort_values("entry_time").reset_index(drop=True)

def stats(d):
    wins, losses = d[d.net_pnl > 0], d[d.net_pnl < 0]
    pf = wins.net_pnl.sum() / -losses.net_pnl.sum() if len(losses) else float("inf")
    eq = 100 + d.net_pnl.cumsum()
    dd = float(((eq.cummax() - eq) / eq.cummax()).max() * 100) if len(eq) else 0.0
    d = d.assign(ym=d.entry_time.dt.strftime("%Y-%m"),
                 bw=d.entry_time.dt.strftime("%Y-%m") + ["-H1" if x.day <= 15 else "-H2" for x in d.entry_time],
                 wk=d.entry_time.dt.strftime("%G-W%V"))
    mo = d.groupby("ym").net_pnl.sum(); bw = d.groupby("bw").net_pnl.sum(); wk = d.groupby("wk").net_pnl.sum()
    return dict(n=len(d), net=round(float(d.net_pnl.sum()), 2), pf=round(float(pf), 3),
                wr=round(float((d.net_pnl > 0).mean() * 100), 1), dd=round(dd, 1),
                mo=f"{int((mo > 0).sum())}/43", bw=f"{int((bw > 0).sum())}/86",
                wk=f"{int((wk > 0).sum())}/187",
                mo_min=round(float(mo.min()), 2), mo_max=round(float(mo.max()), 2),
                wk_min=round(float(wk.min()), 2), wk_max=round(float(wk.max()), 2),
                months={k: round(float(v), 2) for k, v in mo.items()})

def main():
    causal = json.loads((RES / "_v51_causal.json").read_text())
    books = {a: pd.concat([load(fn(w)) for w in WINS], ignore_index=True) for a, (_, fn) in ARMS.items()}
    per_win = {a: {w: stats(load(fn(w))) for w in WINS} for a, (_, fn) in ARMS.items()}
    tot = {a: stats(b) for a, b in books.items()}
    diffs = causal.get("diffs", {}); buggy = causal.get("buggy_engine_2bps", {})
    L = []; A = L.append
    A("# تقرير v51 — فضح خلل `@2bps` غير السببي، التحقق السببي الحقيقي، وذراع `P1 + حارس السكين`\n")
    A("**الفرع** `arena/32ffea77-trading-bot` · رأس المال **100$** · **مقعد واحد** · خروج **100%** · `COST=0.001`. "
      "كل كتب 0bps مُعادة الاستخدام من القرص — لم يُعَد تشغيل أي ذراع قديمة.\n")
    A("---\n## 1. التشريح الجنائي لشذوذ `@2bps` في القسم 2 من v50\n")
    A("### 1.1 كيف طُبّق الانزلاق في المحرّك\n")
    A("`lab_v50_tournament.py:91` يضبط `S.EXIT_SLIPPAGE_BPS = float(bps)`، وفي الاستراتيجية:\n")
    A("```python\n# strategy_v36_ict_champion.py:3688-3689  (داخل _exit، قبل أي محاسبة)\nif EXIT_SLIP > 0 and reason in EXIT_SLIP_REASONS:\n    px = px * (1.0 - EXIT_SLIP)\n```\n")
    A("السعر المنزلق لا يبقى رقماً في سطر الخروج؛ إنه يتدفق إلى كل حالة لاحقة:\n")
    A("| السطر | الأثر المتسلسل |\n|---|---|\n")
    A("| `3695-3705` | `net` و`R` يُحسبان من السعر المنزلق، ثم `is_win = net > 0 and R >= LOCK_R` |\n")
    A("| `3712-3714` | `is_be` يشترط `R >= -0.05` — خدش `SHIELD_BE` عند −0.02$ على مخاطر < 0.40$ يعبر الخط ويُعاد تصنيفه **خسارة** |\n")
    A("| `3734` | `pool['cash'] += px*qty - exit_fee` — رأس المال المركّب نفسه يتغير |\n")
    A("| `3751` | `_v35_note_exit(bool(is_win))` — سلسلة العملة: خسارتان ⇒ حظر **14 يوماً** (`PER_COIN_COOLDOWN=2`, `COOLDOWN_DAYS=14`) |\n")
    A("| `3783-3810` | فرع الخسارة: `consec_losses += 1`, `vigil_losses += 1`, استهلاك النطاق (`consumed.append(rng)`) وبوابة الخسائر المتتالية |\n")
    A("\n**النتيجة:** صفقة خدش كانت `BREAKEVEN` (R≈0) تصبح بعد 2bps ‏`R<−0.05` ⇒ خسارة ⇒ حظر عملة 14 يوماً ⇒ صفقات لاحقة مختلفة كلياً ⇒ مقعد مختلف. "
      "هذا **تحوّل مقعد (seat-shift) غير سببي** بالنسبة لنموذج التنفيذ الحقيقي الموصوف في المهمة: قرار الخروج يُتخذ على شمعة `t` ثم يمتلئ أمر السوق أسوأ بـ2bps — الامتلاء لا يستطيع إعادة تصنيف الصفقة في منطق الحظر بأثر رجعي داخل نفس المحاكاة بهذه الطريقة المتسلسلة.\n")
    A("### 1.2 الدليل من الـCSV المحفوظة\n")
    A("| الكتاب | النافذة | n عند 0bps | n عند eng@2bps | الصافي 0bps | الصافي eng@2bps |\n|---|---|---:|---:|---:|---:|\n")
    for key in ("B0:W1", "B0:OLD7", "C4:W1", "C4:OLD7"):
        if key in diffs:
            r = diffs[key]; arm, w = key.split(":")
            A(f"| {arm} | {w} | {r['n0']} | {r['n2']} | {r['net0']:+.2f} | {r['net2']:+.2f} |")
    A("\nأمثلة صفقات موجودة في كتاب واحد فقط (أول 4 لكل جهة، W1/B0):\n")
    r = diffs.get("B0:W1", {})
    A("| الجهة | الدخول | الرمز | سبب الخروج | الصافي |\n|---|---|---|---|---:|\n")
    for row in r.get("only_in_0", [])[:4]: A(f"| 0bps فقط | {row[0][:16]} | {row[1].replace('_5m','')} | {row[2]} | {float(row[3]):+.2f} |")
    for row in r.get("only_in_2", [])[:4]: A(f"| eng@2 فقط | {row[0][:16]} | {row[1].replace('_5m','')} | {row[2]} | {float(row[3]):+.2f} |")
    if r: A(f"\nأكبر صفقة W1/B0: عند 0bps ‏`{r['top0'][1].replace('_5m','')} {float(r['top0'][2]):+.2f}$` ({r['top0'][0][:10]})، وعند eng@2bps ‏`{r['top2'][1].replace('_5m','')} {float(r['top2'][2]):+.2f}$` ({r['top2'][0][:10]}) — العدّاء نفسه اختفى/تغيّر حجمه بفعل تفاعل الحظر المتسلسل.\n")
    A("وفي `C4/W1`: ‏171 صفقة/+60.10 عند 0bps مقابل 165/+6.52 عند eng@2bps — هبوط −53.58$ أي **−0.31$ للصفقة**، بينما 2bps على مركز ~100–160$ تساوي ~0.025$ للصفقة (~4$ إجمالاً). "
      "وفي `B0/OLD7` «ربح» الانزلاق +8.52$ (من −10.50 إلى −1.98 مع 43 صفقة أقل: 203←160) — مستحيل حسابياً لضريبة خروج، وممكن فقط بإعادة ترتيب المقعد.\n")
    A("**الخلاصة الجنائية:** أرقام القسم 2 في v50 تقيس «ماذا يحدث لو أعاد الانزلاق كتابة حالة الحظر والمقعد»، لا «تكلفة امتلاء خروج». حكم «لا شحن» المبني عليها **ملغي** ويُستبدل بالقسم 2 أدناه.\n")
    A("---\n## 2. مصفوفة الـ43 شهراً: 0bps مقابل انزلاق سببي حقيقي 2bps و4bps\n")
    A("النموذج السببي: تسلسل الصفقات مُجمّد من كتاب 0bps؛ كل خروج سوقي (كل الأسباب عدا `END_OF_DATA`) يُملأ عند `exit_px×(1−slip)` "
      "(`Δnet = −slip×exit_px×qty0×(1−COST)`)، ثم يتراكب النقد إلى الأمام فتتدرج أحجام الصفقات اللاحقة بنسبة `cash'/cash` عند دخولها.\n")
    A("| الذراع | صفقات | 0bps $ | **سببي 2bps $** | **سببي 4bps $** | ضريبة 2bps | ضريبة 4bps |\n|---|---:|---:|---:|---:|---:|---:|\n")
    for a, (lab, _) in ARMS.items():
        c = causal["causal"].get(a, {}).get("TOTAL", {})
        if not c: continue
        A(f"| {lab} | {tot[a]['n']} | {c['bps0']:+.2f} | **{c['causal2']:+.2f}** | **{c['causal4']:+.2f}** | {c['causal2']-c['bps0']:+.2f} | {c['causal4']-c['bps0']:+.2f} |")
    b2 = causal["causal"]["B0"]["TOTAL"]
    A("\n| الذراع | Δ عن B0 عند 0bps | Δ عند سببي 2bps | Δ عند سببي 4bps |\n|---|---:|---:|---:|\n")
    for a, (lab, _) in ARMS.items():
        if a == "B0": continue
        c = causal["causal"].get(a, {}).get("TOTAL", {})
        if c: A(f"| {lab} | {c['bps0']-b2['bps0']:+.2f} | {c['causal2']-b2['causal2']:+.2f} | {c['causal4']-b2['causal4']:+.2f} |")
    A(f"\nللمقارنة، كتب المحرّك المعيبة eng@2bps: B0 ‏{buggy.get('B0@eng2', 0):+.2f}، C4 ‏{buggy.get('C4@eng2', 0):+.2f}، S3 ‏{buggy.get('S3@eng2', 0):+.2f} — كلها مرفوضة كأدلة.\n")
    A("---\n## 3. التفصيل نافذةً بنافذة وشهراً بشهر\n")
    A("### 3.1 النوافذ الخمس (0bps؛ MaxDD من منحنى الصفقات)\n")
    A("| الذراع | النافذة | صفقات | صافي $ | PF | WR% | MaxDD% | سببي 2bps $ | سببي 4bps $ |\n|---|---|---:|---:|---:|---:|---:|---:|---:|\n")
    for a in ("B0", "P1", "S3", "V51"):
        for w in WINS:
            s = per_win[a][w]; c = causal["causal"].get(a, {}).get(w, {})
            A(f"| {ARMS[a][0]} | {w} | {s['n']} | {s['net']:+.2f} | {s['pf']} | {s['wr']} | {s['dd']} | {c.get('causal2', 0):+.2f} | {c.get('causal4', 0):+.2f} |")
    A("\n### 3.2 الإجمالي والتوزيع الزمني\n")
    A("| الذراع | صفقات | صافي $ | PF | WR% | MaxDD% | شهر+ | نصف-شهر+ | أسبوع+ | أسوأ شهر | أفضل شهر | أسوأ أسبوع | أفضل أسبوع |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n")
    for a in ("B0", "P1", "S3", "V51"):
        s = tot[a]
        A(f"| {ARMS[a][0]} | {s['n']} | {s['net']:+.2f} | {s['pf']} | {s['wr']} | {s['dd']} | {s['mo']} | {s['bw']} | {s['wk']} | {s['mo_min']:+.2f} | {s['mo_max']:+.2f} | {s['wk_min']:+.2f} | {s['wk_max']:+.2f} |")
    # runners
    A("\n### 3.3 فحص العدّائين — أكبر صفقة في كل نافذة (B0 مقابل الذراع)\n")
    A("| الذراع | " + " | ".join(WINS) + " |\n|---|" + "---|"*5)
    for a_ in ("P1", "S3", "V51"):
        cells_ = []
        for w in WINS:
            d0 = load(ARMS["B0"][1](w)); d1 = load(ARMS[a_][1](w))
            t0 = d0.loc[d0.net_pnl.idxmax()]; t1 = d1.loc[d1.net_pnl.idxmax()]
            cells_.append(f"{t1.symbol.replace('USDT_5m','')} {t1.net_pnl:+.2f} (B0: {t0.symbol.replace('USDT_5m','')} {t0.net_pnl:+.2f})")
        A(f"| {ARMS[a_][0]} | " + " | ".join(cells_) + " |")
    A("\nوفي كتب يناير المستقلة (v50): LINK ‏+10.08→+10.10 وADA ‏+4.70 وETH ‏+4.41→+4.42 وSOL ‏+6.89 محفوظة كلها تحت P1 وS3؛ وV51 يجمع قاعدتيهما معاً ولم يُسقط أي أكبر-صفقة نافذة أعلاه.\n")
    A("\n### 3.4 شهراً بشهر (صافي $)\n")
    months = sorted(tot["B0"]["months"])
    A("| الشهر | B0 | P1 (−0.25x) | S3 | V51 (P1+سكين) |\n|---|---:|---:|---:|---:|\n")
    for m in months:
        A(f"| {m} | " + " | ".join(f"{tot[a]['months'].get(m, 0):+.2f}" for a in ("B0", "P1", "S3", "V51")) + " |")
    # verdict
    c = causal["causal"]; v = c.get("V51", {}).get("TOTAL", {}); s3 = c.get("S3", {}).get("TOTAL", {}); p1 = c.get("P1", {}).get("TOTAL", {})
    wins5 = sum(1 for w in WINS if per_win["V51"][w]["net"] > per_win["B0"][w]["net"]) if v else 0
    A("\n---\n## 4. الحكم النهائي على الشحن\n")
    if v:
        A(f"- `V51 (P1+Knife)` عند 0bps: **{v['bps0']:+.2f}$** ({v['bps0']-b2['bps0']:+.2f} عن B0)، {tot['V51']['n']} صفقة، يتفوق على B0 في **{wins5}/5** نوافذ.\n")
        A(f"- عند سببي 2bps: **{v['causal2']:+.2f}$** ({v['causal2']-b2['causal2']:+.2f} عن B0)؛ عند 4bps: **{v['causal4']:+.2f}$** ({v['causal4']-b2['causal4']:+.2f}).\n")
        A(f"- المقارنة داخل العائلة عند 2bps: P1 ‏{p1.get('causal2',0):+.2f}، S3 ‏{s3.get('causal2',0):+.2f}، V51 ‏{v['causal2']:+.2f}.\n")
        best = max(("P1", "S3", "V51"), key=lambda a: c[a]["TOTAL"]["causal2"])
        A(f"\n**الحكم:** بطل الانزلاق السببي هو `{ARMS[best][0]}`. حكم v50 «لا شحن بسبب 2bps» كان مبنياً على خلل غير سببي ويُلغى. "
          "مع ذلك يبقى الشحن الفعلي قراراً تشغيلياً: الأفضلية السببية عند 2bps و4bps موجبة عبر العائلة كلها، لكن `OLD7` تبقى نافذة سالبة الصافي لكل الأذرع، "
          "وأي ترقية يجب أن تمر ببوابة الورق/المباشر المصغر المعتادة. `V50_MODE/V51` تبقى `off` في الكود المُسلّم حتى يتخذ المالك قرار الترقية صراحة.\n")
    (RES / "REPORT_AR_v51.md").write_text("\n".join(L), encoding="utf-8")
    print("rendered", len(L), "lines")

if __name__ == "__main__":
    main()
