#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lab_v52_report.py -- renders results/REPORT_AR_v52.md (Investment Bot copy)."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
RES = HERE / "results"
WINS = ("W1", "W2", "OLD7", "MOD_Y1", "MOD_Y2")
COST = 0.001
BOOKS = {
    "B0": ("B0", lambda w: RES / f"trades_v37_B0_{w}.csv"),
    "V51": ("V51 (P1+Knife)", lambda w: RES / "v51_engine" / f"v51_p1_knife__{w}__0.csv"),
}
for m in ("v51_base", "m1_depth", "m2_cisd", "m3_dol", "m4_tap2", "m5_kz", "m6_full", "m7_depth_kz"):
    BOOKS[m] = (m, lambda w, m=m: RES / "v52_engine" / f"{m}__{w}__0.csv")

def load(p):
    d = pd.read_csv(p)
    d["entry_time"] = pd.to_datetime(d.entry_time, utc=True, format="mixed")
    return d.sort_values("entry_time").reset_index(drop=True)

def causal(d, slip_bps):
    slip = slip_bps * 1e-4; cash0 = cash = 100.0
    for _, t in d.iterrows():
        scale = cash / cash0 if cash0 > 0 else 0.0
        net = float(t.net_pnl) * scale
        if str(t.exit_reason) != "END_OF_DATA":
            net -= slip * float(t.exit_price) * float(t.qty0) * (1 - COST) * scale
        cash += net; cash0 += float(t.net_pnl)
    return round(cash - 100.0, 2)

def stats(d):
    w_, l_ = d[d.net_pnl > 0], d[d.net_pnl < 0]
    pf = w_.net_pnl.sum() / -l_.net_pnl.sum() if len(l_) else float("inf")
    eq = 100 + d.net_pnl.cumsum()
    dd = float(((eq.cummax() - eq) / eq.cummax()).max() * 100) if len(eq) else 0.0
    mo = d.assign(ym=d.entry_time.dt.strftime("%Y-%m")).groupby("ym").net_pnl.sum()
    bw = d.assign(bw=d.entry_time.dt.strftime("%Y-%m") + ["-H1" if x.day <= 15 else "-H2" for x in d.entry_time]).groupby("bw").net_pnl.sum()
    wk = d.assign(wk=d.entry_time.dt.strftime("%G-W%V")).groupby("wk").net_pnl.sum()
    return dict(n=len(d), net=round(float(d.net_pnl.sum()), 2), pf=round(float(pf), 3),
                wr=round(float((d.net_pnl > 0).mean() * 100), 1), dd=round(dd, 1),
                mo=f"{int((mo>0).sum())}/43", bw=f"{int((bw>0).sum())}/86", wk=f"{int((wk>0).sum())}/187",
                months={k: round(float(v), 2) for k, v in mo.items()},
                wk_s={k: round(float(v), 2) for k, v in wk.items()})

def ready(a):
    return all(BOOKS[a][1](w).exists() for w in WINS)

def main():
    s1 = json.loads((RES / "_v52_stage1.json").read_text()) if (RES / "_v52_stage1.json").exists() else {}
    arms = [a for a in BOOKS if ready(a)]
    tot = {}; c2 = {}; per = {}
    for a in arms:
        book = pd.concat([load(BOOKS[a][1](w)) for w in WINS], ignore_index=True)
        tot[a] = stats(book)
        c2[a] = round(sum(causal(load(BOOKS[a][1](w)), 2) for w in WINS), 2)
        per[a] = {w: stats(load(BOOKS[a][1](w))) for w in WINS}
    L = []; A = L.append
    A("# تقرير v52 — فكّ تجميد الدخول والهدف: ICT كامل (OTE/CE/MTH، CISD، DOL، SMT، Killzones)\n")
    A("**المجلد** `بوت الاستثمار/` (نسخة عمل؛ الأصل `halal_spot/` مجمّد عند v51) · رأس المال **100$** · مقعد واحد · خروج 100% · `COST=0.001` · ICT خالص بلا مؤشرات متأخرة.\n")
    A("**ملاحظة تنفيذية صادقة:** بيانات يناير المستقلة (`binance_5m_jan24/jan26`) غير موجودة في أي نسخة حالياً، فشاشة المرحلة 2 هي `W1` (تحوي 2024-01) و`MOD_Y2` (تحوي 2026-01)، وتُقرأ أشهر يناير من هذين الكتابين.\n")
    A("\n---\n## 1. الأعمدة الخمسة — نتائج التدقيق الساكن (1173 صفقة، 2.7 ثانية)\n")
    A("### العمود 1: عمق CE/MTH/OTE داخل المنطقة\n")
    A("| العمق d | امتلأ | ذهبي غاص | BE غاص | BE→+3R بالعمق الجديد | صافي ساكن (الممتلئة فقط) |\n|---|---:|---:|---:|---:|---:|\n")
    for r in s1.get("pillar1_depth", []):
        A(f"| {r['d']} | {r['filled']} | {r['golden_dipped']}/110 | {r['be_dipped']}/452 | {r['be_becomes_3R']} | {r['static_net_filled_only']:+.2f} |")
    A("\n**القراءة الصادقة:** العمق الأعمى يفقد معظم العدّائين (عند 0.705 لا يغوص إلا 11/110) والصافي الساكن للممتلئة سالب — العمق لا يعمل كأمر حدّي أعمى؛ قيمته الوحيدة المحتملة عبر إعادة استخدام المقعد، والمحرّك يحسم.\n")
    A("\n### العمود 2: تأكيد CISD بعد اللمس (≤6 شموع)\n")
    A("| الطبقة | CISD | n | % |\n|---|---:|---:|---:|\n")
    for k, v in s1.get("pillar2_cisd", {}).items():
        A(f"| {k} | {v['cisd']} | {v['n']} | {v['pct']} |")
    A("\nCISD ظاهرة شبه شاملة (77–100% في كل الطبقات) — **ليست فاصلاً** بحد ذاتها.\n")
    p3 = s1.get("pillar3_dol", {})
    A(f"\n### العمود 3: DOL/PDH + بنك CISD هابط\n\nوصل إلى PDH أو ‎+2.0x‎: ‏BE ‏{p3.get('BE_reached_PDH_or_2x')}، EM ‏{p3.get('EM_reached')}، Golden ‏{p3.get('Golden_reached')}. البنك الساكن عند +2R مقابل الفعلي (BE+EM): **{p3.get('static_bank_at_+2R_gain_vs_actual_BE_EM', 0):+.2f}$ سقف نظري**.\n")
    A("\n### العمود 4: SMT (انحراف مقابل BTC/ETH، نظر 4 ساعات)\n")
    A("| الطبقة\\SMT | n | صافي $ |\n|---|---:|---:|\n")
    for k, v in s1.get("pillar4_smt", {}).items():
        A(f"| {k} | {v['n']} | {v['net']:+.2f} |")
    A("\nلا حافة ظاهرة: صفقات SMT أسوأ للصفقة من غيرها في Other.\n")
    A("\n### العمود 5: Killzones ويوم الأسبوع\n")
    A("| المنطقة | n | صافي $ |\n|---|---:|---:|\n")
    for r in s1.get("pillar5_kz", []): A(f"| {r[0]} | {r[1]} | {float(r[2]):+.2f} |")
    A("\n| اليوم | n | صافي $ |\n|---|---:|---:|\n")
    for r in s1.get("pillar5_dow", []): A(f"| {r[0]} | {r[1]} | {float(r[2]):+.2f} |")
    A("\nالسبت هو اليوم السالب الوحيد؛ Silver Bullet وDead Zone الأعلى للصفقة.\n")
    A("\n---\n## 2. بطولة المحرّك — شاشة W1 + MOD_Y2 (يناير داخلها)\n")
    A("| الذراع | W1 $ (n) | MOD_Y2 $ (n) | مجموع الشاشة | Δ عن V51 |\n|---|---:|---:|---:|---:|\n")
    base = None
    scr = {}
    for a in arms:
        if all((RES / "v52_engine" / f"{a}__{w}__0.csv").exists() for w in ("W1", "MOD_Y2")) or a in ("B0", "V51"):
            w1 = per[a]["W1"]; my = per[a]["MOD_Y2"]
            scr[a] = w1["net"] + my["net"]
    if "V51" in scr: base = scr["V51"]
    for a, v in sorted(scr.items(), key=lambda x: -x[1]):
        w1 = per[a]["W1"]; my = per[a]["MOD_Y2"]
        A(f"| {BOOKS[a][0]} | {w1['net']:+.2f} ({w1['n']}) | {my['net']:+.2f} ({my['n']}) | **{v:+.2f}** | {v-base:+.2f} |" if base is not None else f"| {BOOKS[a][0]} | {w1['net']:+.2f} | {my['net']:+.2f} | {v:+.2f} | — |")
    A("\n---\n## 3. مصفوفة الـ43 شهراً (0bps وسببي 2bps)\n")
    A("| الذراع | صفقات | صافي 0bps $ | سببي 2bps $ | Δ عن B0 | Δ عن V51 | للصفقة $ | WR% | PF | MaxDD% | شهر+ | نصف+ | أسبوع+ |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n")
    for a in arms:
        s = tot[a]
        A(f"| {BOOKS[a][0]} | {s['n']} | **{s['net']:+.2f}** | {c2[a]:+.2f} | {s['net']-tot['B0']['net']:+.2f} | {s['net']-tot['V51']['net']:+.2f} | {s['net']/max(s['n'],1):+.3f} | {s['wr']} | {s['pf']} | {s['dd']} | {s['mo']} | {s['bw']} | {s['wk']} |")
    A("\n### 3.1 نافذةً بنافذة (0bps)\n")
    A("| الذراع | " + " | ".join(WINS) + " |\n|---|" + "---:|" * 5)
    for a in arms:
        A(f"| {BOOKS[a][0]} | " + " | ".join(f"{per[a][w]['net']:+.2f} ({per[a][w]['n']})" for w in WINS) + " |")
    A("\n---\n## 4. شهراً بشهر وتوزيع الأسابيع\n")
    months = sorted(tot["B0"]["months"])
    cols = [a for a in ("B0", "V51") if a in arms] + [a for a in arms if a not in ("B0", "V51")]
    A("| الشهر | " + " | ".join(BOOKS[a][0] for a in cols) + " |\n|---|" + "---:|" * len(cols))
    for m in months:
        A(f"| {m} | " + " | ".join(f"{tot[a]['months'].get(m, 0):+.2f}" for a in cols) + " |")
    A("\n| الذراع | أسوأ أسبوع $ | أفضل أسبوع $ | أسابيع موجبة |\n|---|---:|---:|---:|\n")
    for a in cols:
        wk = tot[a]["wk_s"]
        A(f"| {BOOKS[a][0]} | {min(wk.values()):+.2f} | {max(wk.values()):+.2f} | {tot[a]['wk']} |")
    A("\n---\n## 5. الحكم الصادق\n")
    if arms:
        ranked = sorted((a for a in arms if a not in ("B0",)), key=lambda a: -tot[a]["net"])
        best = ranked[0]
        A(f"أفضل ذراع v52 على المحرّك: **{BOOKS[best][0]}** بصافي **{tot[best]['net']:+.2f}$** (V51: {tot['V51']['net']:+.2f}$، B0: {tot['B0']['net']:+.2f}$).\n")
        for a in ranked:
            if a == "V51": continue
            d = tot[a]["net"] - tot["V51"]["net"]
            A(f"- `{BOOKS[a][0]}`: {tot[a]['net']:+.2f}$ ({d:+.2f} عن V51)، {tot[a]['n']} صفقة، سببي 2bps ‏{c2[a]:+.2f}$. {'**تتقدّم**' if d > 0 else 'لا تتقدّم — مرفوضة كترقية.'}\n")
        A("\nإصلاح تصنيف `is_be` قبل الانزلاق (سطر 3712 في v50) مطبّق دائماً في هذه النسخة: التصنيف يقرأ سعر الزناد، والامتلاء المنزلق يبقى في المحاسبة فقط، فلا يعود الانزلاق قادراً على قلب خدش إلى خسارة وتشغيل حظر الـ14 يوماً.\n")
        A("\n`V52_MODE=\"off\"` افتراضياً؛ لا ترقية تُشحن دون قرار المالك. النسخة الأصلية `halal_spot/` لم تُمسّ.\n")
    (RES / "REPORT_AR_v52.md").write_text("\n".join(L), encoding="utf-8")
    print("rendered")

if __name__ == "__main__":
    main()
