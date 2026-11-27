#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lab_v56_report.py -- renders results/REPORT_AR_v56.md.
True compounding is built on per-trade % returns reconstructed by walking
each window book (cash starts 100, engine compounds inside the window):
ret_i = net_i / cash_before_i. Continuous capital then applies the same
ret stream chronologically across all 43 months -- no double compounding."""
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
    "m5_kz": ("m5_kz (بطل v52)", lambda w: RES / "v52_engine" / f"m5_kz__{w}__0.csv"),
    "s3_unfreeze": ("s3_unfreeze (بطل v55 المرشّح)", lambda w: RES / "v55_engine" / f"s3_unfreeze__{w}__0.csv"),
}
ARMS = ["h1_harvest", "h2_asym", "h3_cisd", "h4_s3harvest", "h5_master"]
for m in ARMS:
    BOOKS[m] = (m, lambda w, m=m: RES / "v56_engine" / f"{m}__{w}__0.csv")

def load(p):
    d = pd.read_csv(p)
    if not len(d): return d.assign(entry_time=pd.Series(dtype="datetime64[ns, UTC]"))
    d["entry_time"] = pd.to_datetime(d.entry_time, utc=True, format="mixed")
    return d.sort_values("entry_time").reset_index(drop=True)

def with_ret(p):
    """Attach per-trade ret_pct by walking the window book from $100."""
    d = load(p)
    if not len(d): d["ret"] = pd.Series(dtype=float); return d
    cash = 100.0; rets = []
    for n in d.net_pnl:
        rets.append(float(n) / cash if cash > 0 else 0.0)
        cash += float(n)
    d["ret"] = rets
    return d

def allw(a):
    return pd.concat([with_ret(BOOKS[a][1](w)) for w in WINS], ignore_index=True).sort_values("entry_time").reset_index(drop=True)

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

def true_compound(d):
    cap = 100.0
    for r in d.ret: cap *= (1 + float(r))
    return round(cap, 2)

def withdraw_plan(d):
    """50% of every winning month's profit to pocket, 50% stays."""
    bal = 100.0; pocket = 0.0; rows = []
    d = d.assign(ym=d.entry_time.dt.strftime("%Y-%m"))
    for ym, g in d.groupby("ym", sort=True):
        start = bal
        for r in g.ret: bal *= (1 + float(r))
        profit = bal - start; wd = 0.0
        if profit > 0:
            wd = 0.5 * profit; bal -= wd; pocket += wd
        rows.append({"month": ym, "withdrawn": round(wd, 2),
                     "pocket_cum": round(pocket, 2), "balance": round(bal, 2)})
    return rows, round(pocket, 2), round(bal, 2)

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
def gate_ready(a): return all((RES / "v56_engine" / f"{a}__{w}__0.csv").exists() for w in ("W1", "OLD7", "MOD_Y2"))

def main():
    s1 = json.loads((RES / "_v56_stage1.json").read_text()) if (RES / "_v56_stage1.json").exists() else {}
    full = [a for a in BOOKS if ready(a)]
    tot, per, c2, comp, plans = {}, {}, {}, {}, {}
    for a in full:
        d = allw(a)
        tot[a] = stats(d); per[a] = {w: stats(load(BOOKS[a][1](w))) for w in WINS}
        c2[a] = round(sum(causal(load(BOOKS[a][1](w))) for w in WINS), 2)
        comp[a] = true_compound(d)
        plans[a] = withdraw_plan(d)
    gate = {}
    for a in ARMS:
        if gate_ready(a):
            gate[a] = round(sum(stats(load(BOOKS[a][1](w)))["net"] for w in ("W1", "OLD7", "MOD_Y2")), 2)
    surv = [a for a in ARMS if a in full]
    L = []; A = L.append
    A("# تقرير v56 — المسطرة غير المتماثلة، حلب +2R، وخطة السحب الشهري للمالك\n")
    A("**المجلد** `بوت الاستثمار/` فقط (`halal_spot/` مجمّد عند v51؛ نسخة الأمان `بوت الاستثمار/نسخة_محفوظة_v55/` مجمّدة قبل أي تعديل) · الأساس: `m5_kz` = ‎+502.40$ / سببي ‏+457.08$، وبطل v55 المرشّح `s3_unfreeze` = ‎+559.63$ / ‏+515.44$ (بانتظار قرار المالك؛ لم يُعتمد بعد) · 100$ · مقعد واحد · خروج 100% · عملية واحدة · `V56_MODE=\"off\"` افتراضياً.\n")
    A("\n---\n## 1. تشريح الـ395 صفقة BREAKEVEN والصفقات المخنوقة بالسنتات (كتاب m5_kz)\n")
    A("\n### 1.1 توزيع أقصى ربح (MFE) لصفقات أُغلقت عند 0.00$\n")
    A("| Max_R وصلته ثم عادت للصفر | عدد | متوسط أقصى ربح $ | ربح متروك على الطاولة $ (قيمة الذروة) |\n|---|---:|---:|---:|\n")
    for r in s1.get("1.1_be_mfe", []):
        A(f"| {r['bucket']} | {r['n']} | {r['avg_max_profit']:.2f} | {r['left_on_table']:.2f} |")
    for th in ("1.8", "2.0", "2.2"):
        v = s1.get(f"1.1_ge_{th}R", {})
        A(f"\nوصلت **{v.get('n')} صفقة إلى ≥ +{th}R ثم عادت إلى 0.00$**، قيمتها عند الذروة ‏{v.get('left_on_table')}$ (حدّ أعلى نظري: الخروج عند الذروة نفسها مستحيل؛ قاعدة إغلاق 15m عند +1.3R تلتقط جزءاً منها فقط).\n")
    A("\n### 1.2 ما الذي يفصل الرانر الذهبي عن المنعكس؟ (105 صفقات ≥ +3R مُعادة التشغيل على بيانات 5m)\n")
    g = s1.get("1.2_golden", {})
    A(f"\nبعد أول لمس لـ+2.0R: ‏**{g.get('never_15m_close_below_1.2R_pct')}%** من الرانرات الذهبية لا تغلق أبداً شمعة 15m تحت +1.2R قبل اختراق +3R، و**{g.get('never_15m_close_below_1.4R_pct')}%** لا تغلق تحت +1.4R (وسيط أدنى إغلاق ‏{g.get('min_close_R_median')}R، العُشر الأدنى ‏{g.get('min_close_R_p10')}R). أي أن خط حلب بإغلاق 15m عند +1.3R يمسّ نظرياً أقلّية الرانرات فقط — وهذا هو الأساس الإحصائي لـh1.\n")
    A("\n### 1.3 صفقات +3R المخنوقة بالسنتات (صافي < 1.00$)\n")
    c = s1.get("1.3_cents", {})
    A(f"\n**{c.get('n_lt1_at_3R')} صفقات فقط** في كامل الكتاب وصلت +3R وأُغلقت بأقل من دولار (كلها risk_pct < 0.35%)؛ ما حدث بعدها خلال 12 ساعة:\n")
    A("| الرمز | الخروج | صافي $ | risk% | أقصى تقدّم 12h % | إغلاق 12h % |\n|---|---|---:|---:|---:|---:|\n")
    for r in c.get("rows", []):
        A(f"| {r['sym'].replace('_5m','')} | {r['exit'][:16]} | {r['net']:+.2f} | {r['risk_pct']} | {r['fwd12h_max_pct']:+.2f} | {r['fwd12h_close_pct']:+.2f} |")
    A("\nالخنق بالسنتات حقيقي لكنه هامشي عددياً (8 صفقات، وبعضها واصل +7.45%)؛ الجائزة الحقيقية هي جدول 1.1 لا 1.3 — ولهذا h2 (أرضية الربح بالدولار) ذراع ثانوية بجانب h1.\n")
    A("\n---\n## 2. بوابة الفرز 1: W1+OLD7+MOD_Y2 عند 0bps (المرجع m5_kz = +128.49)\n")
    A("| الذراع | بوابة $ | Δ عن m5 |\n|---|---:|---:|\n")
    for a, v in sorted(gate.items(), key=lambda x: -x[1]):
        A(f"| {a} | **{v:+.2f}** | {v - 128.49:+.2f} |")
    A(f"\nالمتأهلون للـ43 شهراً (كل من تجاوز +128.49، وإلزامياً أفضل 3): {', '.join(surv) if surv else '—'}.\n")
    A("\n---\n## 3. مصفوفة الـ43 شهراً (0bps و2bps السببي)\n")
    A("| الذراع | صفقات | 0bps $ | سببي 2bps $ | Δ عن m5_kz | Δ عن s3 | للصفقة | WR% | PF | MaxDD% | شهر+ | نصف+ | أسبوع+ |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n")
    for a in full:
        s = tot[a]
        A(f"| {BOOKS[a][0]} | {s['n']} | **{s['net']:+.2f}** | {c2[a]:+.2f} | {s['net']-tot['m5_kz']['net']:+.2f} | {s['net']-tot['s3_unfreeze']['net']:+.2f} | {s['net']/max(s['n'],1):+.3f} | {s['wr']} | {s['pf']} | {s['dd']} | {s['mo']} | {s['bw']} | {s['wk']} |")
    A("\n(MaxDD محسوب على منحنى الكتاب الكلي مرتباً زمنياً — يشمل قفزات إعادة ضبط النوافذ، وهو أشد تحفظاً من MaxDD كل نافذة منفردة.)\n")
    A("\n---\n## 4. جداول المال الحقيقي للمالك\n")
    A("\n### 4.1 نافذةً بنافذة وشهراً بشهر (قياسي: كل نافذة تبدأ من 100$)\n")
    A("| الذراع | " + " | ".join(WINS) + " |\n|---|" + "---:|" * 5)
    for a in full:
        A(f"| {BOOKS[a][0]} | " + " | ".join(f"{per[a][w]['net']:+.2f} ({per[a][w]['n']})" for w in WINS) + " |")
    months = sorted(tot["B0"]["months"]) if "B0" in tot else []
    A("\n| الشهر | " + " | ".join(BOOKS[a][0] for a in full) + " |\n|---|" + "---:|" * len(full))
    for m in months:
        A(f"| {m} | " + " | ".join(f"{tot[a]['months'].get(m, 0):+.2f}" for a in full) + " |")
    A("\n### 4.2 التراكم المستمر الحقيقي (True Continuous Compounding) — بدون خطأ التراكم المزدوج\n")
    A("المنهج المصحّح: لكل صفقة ‏ret = net ÷ رصيد المحفظة قبلها داخل نافذتها (المحرّك يراكم داخلياً أصلاً)، ثم تُسلسل النسب الـ1,072 زمنياً عبر النوافذ الخمس على رأس مال واحد يبدأ 100$ ولا يُعاد ضبطه أبداً.\n")
    A("| الذراع | قياسي (مجموع النوافذ) $ | تراكمي حقيقي: رأس المال النهائي $ | العائد % |\n|---|---:|---:|---:|\n")
    for a in full:
        A(f"| {BOOKS[a][0]} | {tot[a]['net']:+.2f} | **{comp[a]:,.2f}** | {(comp[a]-100):+,.1f}% |")
    focus = [a for a in ("m5_kz", "s3_unfreeze") if a in plans]
    surv_focus = [a for a in surv if a in plans]
    cols = focus + surv_focus
    A("\n### 4.3 خطة المالك: اسحب 50% من ربح كل شهر رابح للجيب، وراكِم 50%\n")
    hdr = " | ".join(f"{BOOKS[a][0]}: سحب الشهر / الجيب التراكمي / رصيد المحفظة" for a in cols)
    A(f"| الشهر | {hdr} |\n|---|" + "---|" * len(cols))
    rows_by = {a: {r["month"]: r for r in plans[a][0]} for a in cols}
    for m in months:
        A(f"| {m} | " + " | ".join(f"{rows_by[a][m]['withdrawn']:.2f} / {rows_by[a][m]['pocket_cum']:,.2f} / {rows_by[a][m]['balance']:,.2f}" if m in rows_by[a] else "—" for a in cols) + " |")
    A("\n**الخلاصة النقدية:**\n")
    for a in cols:
        _, pocket, bal = plans[a]
        A(f"- `{BOOKS[a][0]}`: مجموع ما سحبه المالك للجيب = **{pocket:,.2f}$**، ورصيد المحفظة النهائي = **{bal:,.2f}$** (المجموع {pocket+bal:,.2f}$ مقابل تراكمي بلا سحب {comp[a]:,.2f}$).\n")
    A("\n---\n## 5. الحكم الصادق والخطوة التالية\n")
    ranked = sorted(surv, key=lambda a: -tot[a]["net"]) if surv else []
    for a in ranked:
        A(f"- `{a}`: {tot[a]['net']:+.2f}$ ({tot[a]['net']-tot['m5_kz']['net']:+.2f} عن m5_kz، {tot[a]['net']-tot['s3_unfreeze']['net']:+.2f} عن s3)، {tot[a]['n']} صفقة، سببي ‏{c2[a]:+.2f}$، PF ‏{tot[a]['pf']}، تراكمي حقيقي ‏{comp[a]:,.2f}$. {'**مرشّحة للترقية بقرار المالك**' if tot[a]['net'] > tot['s3_unfreeze']['net'] else 'لا تتفوق على s3_unfreeze.'}\n")
    knocked = [a for a in ARMS if a not in surv]
    if knocked:
        A(f"- مُقصاة عند بوابة الفرز (لم تُستكمل نوافذها): {', '.join(knocked)}.\n")
    best_all = max(full, key=lambda a: tot[a]["net"])
    A(f"\n**أفضل كتاب على الـ43 شهراً: `{BOOKS[best_all][0]}` ‏({tot[best_all]['net']:+.2f}$).** كل الأكواد (`V53/V54/V55/V56 = \"off\"`) افتراضية؛ لا ترقية لأي ذراع إلا بقرار صريح من المالك عبر بوابة الورقي/المصغّر. OLD7 معروضة كما هي في كل الجداول ولا تُخفى.\n")
    (RES / "REPORT_AR_v56.md").write_text("\n".join(L), encoding="utf-8")
    print("rendered", len(full), "full | gate:", gate)

if __name__ == "__main__":
    main()
