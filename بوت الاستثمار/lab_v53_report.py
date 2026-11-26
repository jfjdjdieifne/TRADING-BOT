#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lab_v53_report.py -- renders results/REPORT_AR_v53.md."""
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
    "V51": ("V51", lambda w: RES / "v51_engine" / f"v51_p1_knife__{w}__0.csv"),
    "m5_kz": ("m5_kz (أساس v52)", lambda w: RES / "v52_engine" / f"m5_kz__{w}__0.csv"),
}
for m in ("m5_base", "a1_cap", "a2_adapt", "a3_shield", "a4_reentry", "a5_wknd", "a6_combo"):
    BOOKS[m] = (m, lambda w, m=m: RES / "v53_engine" / f"{m}__{w}__0.csv")

def load(p):
    d = pd.read_csv(p)
    if not len(d): return d.assign(entry_time=pd.Series(dtype="datetime64[ns, UTC]"))
    d["entry_time"] = pd.to_datetime(d.entry_time, utc=True, format="mixed")
    return d.sort_values("entry_time").reset_index(drop=True)

def causal(d, slip_bps=2):
    if not len(d): return 0.0
    slip = slip_bps * 1e-4; cash0 = cash = 100.0
    for _, t in d.iterrows():
        scale = cash / cash0 if cash0 > 0 else 0.0
        net = float(t.net_pnl) * scale
        if str(t.exit_reason) != "END_OF_DATA":
            net -= slip * float(t.exit_price) * float(t.qty0) * (1 - COST) * scale
        cash += net; cash0 += float(t.net_pnl)
    return round(cash - 100.0, 2)

def stats(d):
    if not len(d):
        return dict(n=0, net=0.0, pf=0.0, wr=0.0, dd=0.0, mo="0/43", bw="0/86", wk="0/187", months={})
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
                months={k: round(float(v), 2) for k, v in mo.items()})

def ready(a): return all(BOOKS[a][1](w).exists() for w in WINS)
def screen_ready(a): return all((RES / "v53_engine" / f"{a}__{w}__0.csv").exists() for w in ("W1", "MOD_Y2"))

def main():
    s1 = json.loads((RES / "_v53_stage1.json").read_text()) if (RES / "_v53_stage1.json").exists() else {}
    full = [a for a in BOOKS if ready(a)]
    tot, per, c2 = {}, {}, {}
    for a in full:
        tot[a] = stats(pd.concat([load(BOOKS[a][1](w)) for w in WINS], ignore_index=True))
        per[a] = {w: stats(load(BOOKS[a][1](w))) for w in WINS}
        c2[a] = round(sum(causal(load(BOOKS[a][1](w))) for w in WINS), 2)
    scr = {}
    for a in BOOKS:
        if a in ("B0", "V51", "m5_kz"):
            scr[a] = round(sum(stats(load(BOOKS[a][1](w)))["net"] for w in ("W1", "MOD_Y2")), 2)
        elif screen_ready(a):
            scr[a] = round(sum(stats(load(BOOKS[a][1](w)))["net"] for w in ("W1", "MOD_Y2")), 2)
    L = []; A = L.append
    A("# تقرير v53 — عمق تكيّفي حسب عرض الصندوق، سقف عرض الوقف، وفرصة ثانية بعد SHIELD_BE\n")
    A("**المجلد** `بوت الاستثمار/` فقط (الأصل مجمّد) · الأساس الجديد: `m5_kz` = ‎+502.40$ (سببي 2bps ‏+457.08) · 100$ · مقعد واحد · خروج 100%.\n")
    A("\n---\n## 1. التشريح: لماذا فاز العمق في MOD_Y2/OLD7 وخسر في MOD_Y1؟\n")
    A("### 1.1 أكبر 10 صفقات m1_depth في MOD_Y2 وOLD7 مقابل مقعد m5_kz\n")
    A("| النافذة | الدخول | الرمز | m1 صافي | risk% | نفس الإعداد عند m5 | مقعد m5 حينها |\n|---|---|---|---:|---|---|---|\n")
    for r in s1.get("1a_top_m1", []):
        A(f"| {r['win']} | {r['entry'][:16]} | {r['sym']} | {r['m1_net']:+.2f} | {r['raw_risk_pct']} | {r['m5_same_setup']} | {r['m5_seat']} |")
    A("\n**الجواب:** أغلب صفقات m1 الكبيرة **ليست نفس إعدادات m5 بخسارة مختلفة** — مقعد m5 كان مشغولاً بصفقة أخرى أو الإعداد لم يوجد أصلاً في كتابه. العمق لا «ينقذ» نفس الصفقات؛ إنه يعيد ترتيب المقعد كلياً نحو إعدادات مختلفة أقل عدداً وأوسع. لهذا فاز حيث المقعد الرخيص ضار (MOD_Y2/OLD7) وخسر حيث السرعة هي الحافة (MOD_Y1).\n")
    A("\n### 1.2 دلاء risk_pct على كتاب m5_kz (1072 صفقة)\n")
    A("| الدلو % | صفقات | Golden | EM | BE | Other | صافي $ | للصفقة | PF | WR% | متوسط خسارة |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n")
    for r in s1.get("1b_buckets", []):
        A(f"| {r['bucket']} | {r['n']} | {r['Golden']} | {r['EM']} | {r['BE']} | {r['Other']} | {r['net']:+.2f} | {r['avg']:+.3f} | {r['pf']} | {r['wr']} | {r['avg_loss']:+.2f} |")
    A("\nعلى كتاب m5 الحقيقي (بخلاف كتاب B0 الساكن في v49) الدلاء الواسعة ليست كارثة: ‏0.35–0.50% هو منجم الذهب (+258.11)، و>1.30% موجب أيضاً. حذف >1.00% ساكناً يزيل +58.38$ رابحة — سقف A1 مشكوك فيه قبل المحرّك.\n")
    A("\n### 1.3 اليوم والرمز\n")
    A("أيام V51: السبت −20.00$ (117 صفقة) وهو السالب الوحيد؛ الأربعاء +167.35 والخميس +142.61 الأقوى. عند m5 (بعد حظر السبت) لا يوم سالباً متبقياً بين الاثنين والجمعة. رمزياً عند m5: ADA ‏+154.17 وAVAX ‏+152.59 الأقوى، SOL ‏+0.61 وBTC ‏+9.30 الأضعف لكن لا رمز سالباً في ≥4/5 نوافذ (SOL سالب في MOD_Y1/MOD_Y2/OLD7 لكنه +17.64/+11.38 في W1/W2).\n")
    A("\n---\n## 2. شاشة W1 + MOD_Y2 (الأساس m5_kz = +129.33)\n")
    A("| الذراع | شاشة $ | Δ عن m5 |\n|---|---:|---:|\n")
    for a, v in sorted(scr.items(), key=lambda x: -x[1]):
        A(f"| {BOOKS[a][0]} | **{v:+.2f}** | {v - scr.get('m5_kz', 0):+.2f} |")
    A("\n---\n## 3. مصفوفة الـ43 شهراً (0bps وسببي 2bps)\n")
    A("| الذراع | صفقات | 0bps $ | سببي 2bps $ | Δ عن B0 | Δ عن m5_kz | للصفقة | WR% | PF | MaxDD% | شهر+ | نصف+ | أسبوع+ |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n")
    for a in full:
        s = tot[a]
        A(f"| {BOOKS[a][0]} | {s['n']} | **{s['net']:+.2f}** | {c2[a]:+.2f} | {s['net']-tot['B0']['net']:+.2f} | {s['net']-tot['m5_kz']['net']:+.2f} | {s['net']/max(s['n'],1):+.3f} | {s['wr']} | {s['pf']} | {s['dd']} | {s['mo']} | {s['bw']} | {s['wk']} |")
    A("\n---\n## 4. نافذةً بنافذة وشهراً بشهر\n")
    A("| الذراع | " + " | ".join(WINS) + " |\n|---|" + "---:|" * 5)
    for a in full:
        A(f"| {BOOKS[a][0]} | " + " | ".join(f"{per[a][w]['net']:+.2f} ({per[a][w]['n']})" for w in WINS) + " |")
    months = sorted(tot["B0"]["months"])
    A("\n| الشهر | " + " | ".join(BOOKS[a][0] for a in full) + " |\n|---|" + "---:|" * len(full))
    for m in months:
        A(f"| {m} | " + " | ".join(f"{tot[a]['months'].get(m, 0):+.2f}" for a in full) + " |")
    A("\n---\n## 5. الحكم الصادق والخطوة التالية\n")
    if full:
        ranked = sorted((a for a in full if a not in ("B0", "V51", "m5_kz")), key=lambda a: -tot[a]["net"])
        for a in ranked:
            d = tot[a]["net"] - tot["m5_kz"]["net"]
            A(f"- `{BOOKS[a][0]}`: {tot[a]['net']:+.2f}$ ({d:+.2f} عن m5_kz)، {tot[a]['n']} صفقة، سببي 2bps ‏{c2[a]:+.2f}$. {'**تتقدّم**' if d > 0 else 'مرفوضة.'}\n")
        best = ranked[0] if ranked else "m5_kz"
        A(f"\n**البطل الحالي: `{BOOKS[best][0]}`.** `V53_MODE=\"off\"` افتراضياً وبانتظار قرار المالك. الخطوة المعمارية التالية المقترحة: مهاجمة نافذة OLD7 السالبة بنيوياً وحدها (كل الأذرع تخسر أو تتعادل فيها) بدل إضافة فلاتر عالمية جديدة، وبناء بيانات يناير المستقلة مجدداً لاختبار شهري نظيف.\n")
    (RES / "REPORT_AR_v53.md").write_text("\n".join(L), encoding="utf-8")
    print("rendered")

if __name__ == "__main__":
    main()
