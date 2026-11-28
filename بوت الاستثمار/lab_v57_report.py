#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lab_v57_report.py -- renders results/REPORT_AR_v57.md (v56 money math)."""
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
    "s3_unfreeze": ("s3_unfreeze (مرشّح v55)", lambda w: RES / "v55_engine" / f"s3_unfreeze__{w}__0.csv"),
}
ARMS = ["u1_stop_streak", "u2_oneshot", "u3_milk", "u4_subfloor", "u5_machine"]
for m in ARMS:
    BOOKS[m] = (m, lambda w, m=m: RES / "v57_engine" / f"{m}__{w}__0.csv")

def load(p):
    d = pd.read_csv(p)
    if not len(d): return d.assign(entry_time=pd.Series(dtype="datetime64[ns, UTC]"))
    d["entry_time"] = pd.to_datetime(d.entry_time, utc=True, format="mixed")
    return d.sort_values("entry_time").reset_index(drop=True)

def with_ret(p):
    d = load(p)
    if not len(d): d["ret"] = pd.Series(dtype=float); return d
    cash = 100.0; rets = []
    for n in d.net_pnl:
        rets.append(float(n) / cash if cash > 0 else 0.0); cash += float(n)
    d["ret"] = rets; return d

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
    bal = 100.0; pocket = 0.0; rows = []
    d = d.assign(ym=d.entry_time.dt.strftime("%Y-%m"))
    for ym, g in d.groupby("ym", sort=True):
        start = bal
        for r in g.ret: bal *= (1 + float(r))
        profit = bal - start; wd = 0.0
        if profit > 0: wd = 0.5 * profit; bal -= wd; pocket += wd
        rows.append({"month": ym, "withdrawn": round(wd, 2), "pocket_cum": round(pocket, 2), "balance": round(bal, 2)})
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
def gate_ready(a): return all((RES / "v57_engine" / f"{a}__{w}__0.csv").exists() for w in ("W1", "MOD_Y2"))

def main():
    s1 = json.loads((RES / "_v57_stage1.json").read_text()) if (RES / "_v57_stage1.json").exists() else {}
    full = [a for a in BOOKS if ready(a)]
    tot, per, c2, comp, plans = {}, {}, {}, {}, {}
    for a in full:
        d = allw(a)
        tot[a] = stats(d); per[a] = {w: stats(load(BOOKS[a][1](w))) for w in WINS}
        c2[a] = round(sum(causal(load(BOOKS[a][1](w))) for w in WINS), 2)
        comp[a] = true_compound(d); plans[a] = withdraw_plan(d)
    gate = {}
    for a in ARMS:
        if gate_ready(a):
            gate[a] = round(sum(stats(load(BOOKS[a][1](w)))["net"] for w in ("W1", "MOD_Y2")), 2)
    surv = [a for a in ARMS if a in full]
    L = []; A = L.append
    A("# تقرير v57 — درع الخسائر الحقيقية، دفاع الصفقة الواحدة، وحلب الصفقات العالقة\n")
    A("**المجلد** `بوت الاستثمار/` فقط (`halal_spot/` و`نسخة_محفوظة_v55/` مجمّدان ونظيفان) · الأساس: `m5_kz` = ‎+502.40$ / سببي ‏+457.08$؛ مرشّح v55 ‏`s3_unfreeze` = ‎+559.63$ / ‏+515.44$ قياسياً لكن تراكمه الحقيقي 1,568$ مقابل 1,906$ لـm5 (تصحيح v56) — كلاهما بلا اعتماد رسمي حتى قرار المالك · 100$ · مقعد واحد · خروج 100% · عملية واحدة · `V57_MODE=\"off\"` افتراضياً.\n")
    A("\n---\n## 1. التشريح (من الكتب المحفوظة + إعادة تشغيل 5m لجدول 3 فقط)\n")
    A("\n### جدول 1 — سلاسل الخسائر المتتالية ومزيج مخارج m5_kz\n")
    for r in s1.get("1_streaks", []):
        A(f"- `{r['book']}`: أقصى خسائر متتالية صارمة (أي فاصل يكسرها) = **{r['max_consec_losses_strict']}**؛ بتسامح BREAKEVEN (لا يكسرها) = **{r['max_consec_losses_be_tolerant']}**؛ أسوأ سلسلة دولارية داخل نافذة = **{r['worst_streak_dollar_in_window']}$** من 100$.\n")
    A("\n| نوع الخروج (m5_kz) | عدد | % | متوسط $ | مجموع $ |\n|---|---:|---:|---:|---:|\n")
    for r in s1.get("1_exit_mix_m5", []):
        A(f"| {r['type']} | {r['n']} | {r['pct']} | {r['avg_usd']:+.2f} | {r['total_usd']:+.2f} |")
    A("\n### جدول 2 — لماذا تأخر s3 في W1؟ تفعيلات الدفاع ومن فات أثناء التجميد\n")
    A("| النافذة | تفعيلات streak≥2 | بسبب خمشة (−0.35..−0.05) | بسبب خسارة حقيقية (≤−0.50) | رابحات m5 فاتت أثناء التجميد | قيمتها $ |\n|---|---:|---:|---:|---:|---:|\n")
    for w, r in s1.get("2_s3_defense", {}).items():
        A(f"| {w} | {r['activations']} | {r['by_scratch_-0.35..-0.05']} | {r['by_real_loss_<=-0.50']} | {r['m5_winners_missed_while_frozen']} | {r['missed_usd']:+.2f} |")
    A("\nالنتيجة الصادقة: تفعيلات s3 تكاد تكون كلها من خسائر حقيقية لا من خمشات — فرضية u1 (أن الخمشات تلوث العداد) ضعيفة في البيانات؛ مشكلة W1 هي زمن التجميد نفسه (9 رابحات بقيمة +71.84$ فاتت في W1 أثناء التجميد).\n")
    A("\n### جدول 3 — ذهبيات سريعة مقابل عالقات متوسطة (إعادة تشغيل شموع 5m)\n")
    A("| المجموعة | عدد | وصلت +2.5R | وسيط شموع 1.6→2.5R | عالقة >12/18/24 شمعة | حلب افتراضي عند قاع 18 شمعة $ |\n|---|---:|---:|---:|---|---:|\n")
    for k in ("3_golden", "3_be_mfe15"):
        r = s1.get(k, {})
        A(f"| {k} | {r.get('n')} | {r.get('reached_2.5')} | {r.get('median_bars_1.6_to_2.5')} | {r.get('stalled_gt_12/18/24_bars')} | {r.get('hypothetical_milk_usd_at_18bar_sl')} |")
    A("\nالذهبيات تنفجر بسرعة (وسيط شمعتين من +1.6R إلى +2.5R)؛ والعالقات بعد 18 شمعة لا تساوي إلا ~10$ افتراضياً في كامل الـ43 شهراً — جائزة u3/u4 صغيرة ساكناً قبل أن تتكلم البوابة.\n")
    A("\n---\n## 2. بوابة 1: W1+MOD_Y2 عند 0bps (التأهل ≥ +95.00؛ m5 = +129.33، s3 = +57.88)\n")
    A("| الذراع | بوابة $ | الحكم |\n|---|---:|---|\n")
    for a, v in sorted(gate.items(), key=lambda x: -x[1]):
        A(f"| {a} | **{v:+.2f}** | {'**يتأهل**' if v >= 95.0 else 'مُقصاة'} |")
    A(f"\nالمتأهلون لبقية النوافذ (من تجاوز +95، وإلا أفضل ذراعين): {', '.join(surv) if surv else '—'}.\n")
    A("\n---\n## 3. مصفوفة الـ43 شهراً (0bps و2bps السببي)\n")
    A("| الذراع | صفقات | 0bps $ | سببي 2bps $ | Δ عن m5_kz | Δ عن s3 | للصفقة | WR% | PF | MaxDD% | شهر+ | نصف+ | أسبوع+ | تراكمي حقيقي $ | سحب للجيب $ | رصيد نهائي $ |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n")
    for a in full:
        s = tot[a]; _, pocket, bal = plans[a]
        A(f"| {BOOKS[a][0]} | {s['n']} | **{s['net']:+.2f}** | {c2[a]:+.2f} | {s['net']-tot['m5_kz']['net']:+.2f} | {s['net']-tot['s3_unfreeze']['net']:+.2f} | {s['net']/max(s['n'],1):+.3f} | {s['wr']} | {s['pf']} | {s['dd']} | {s['mo']} | {s['bw']} | {s['wk']} | {comp[a]:,.2f} | {pocket:,.2f} | {bal:,.2f} |")
    A("\n(MaxDD على منحنى الكتاب الكلي مرتباً زمنياً؛ التراكمي الحقيقي بنسب ret لكل صفقة دون تراكم مزدوج؛ خطة السحب: 50% من ربح كل شهر رابح للجيب و50% يبقى.)\n")
    A("\n---\n## 4. نافذةً بنافذة وشهراً بشهر\n")
    A("| الذراع | " + " | ".join(WINS) + " |\n|---|" + "---:|" * 5)
    for a in full:
        A(f"| {BOOKS[a][0]} | " + " | ".join(f"{per[a][w]['net']:+.2f} ({per[a][w]['n']})" for w in WINS) + " |")
    months = sorted(tot["B0"]["months"]) if "B0" in tot else []
    A("\n| الشهر | " + " | ".join(BOOKS[a][0] for a in full) + " |\n|---|" + "---:|" * len(full))
    for m in months:
        A(f"| {m} | " + " | ".join(f"{tot[a]['months'].get(m, 0):+.2f}" for a in full) + " |")
    focus = [a for a in ("m5_kz", "s3_unfreeze") + tuple(surv) if a in plans]
    A("\n### خطة السحب 50/50 شهراً بشهر (سحب الشهر / الجيب التراكمي / رصيد المحفظة)\n")
    A("| الشهر | " + " | ".join(BOOKS[a][0] for a in focus) + " |\n|---|" + "---|" * len(focus))
    rows_by = {a: {r["month"]: r for r in plans[a][0]} for a in focus}
    for m in months:
        A(f"| {m} | " + " | ".join(f"{rows_by[a][m]['withdrawn']:.2f} / {rows_by[a][m]['pocket_cum']:,.2f} / {rows_by[a][m]['balance']:,.2f}" if m in rows_by[a] else "—" for a in focus) + " |")
    A("\n---\n## 5. الحكم الصادق والخطوة التالية\n")
    ranked = sorted(surv, key=lambda a: -tot[a]["net"]) if surv else []
    for a in ranked:
        A(f"- `{a}`: {tot[a]['net']:+.2f}$ ({tot[a]['net']-tot['m5_kz']['net']:+.2f} عن m5_kz، {tot[a]['net']-tot['s3_unfreeze']['net']:+.2f} عن s3)، {tot[a]['n']} صفقة، سببي ‏{c2[a]:+.2f}$، PF ‏{tot[a]['pf']}، تراكمي حقيقي ‏{comp[a]:,.2f}$. {'**مرشّحة للترقية بقرار المالك**' if tot[a]['net'] > tot['s3_unfreeze']['net'] and comp[a] > comp['m5_kz'] else 'لا تتفوق على الأسس في القياسين معاً.'}\n")
    knocked = [a for a in ARMS if a not in surv]
    if knocked:
        A(f"- مُقصاة عند البوابة 1: {', '.join(knocked)}.\n")
    A("\n**القاعدة المعتمدة للمقارنة منذ v56:** لا تُعلن ذراع فائزة إلا إذا تفوقت في مجموع النوافذ القياسي **وفي** التراكم المستمر الحقيقي معاً. كل الأكواد `off` افتراضياً؛ الترقية بقرار المالك الصريح فقط. OLD7 معروضة كما هي دائماً.\n")
    (RES / "REPORT_AR_v57.md").write_text("\n".join(L), encoding="utf-8")
    print("rendered", len(full), "full | gate:", gate)

if __name__ == "__main__":
    main()
