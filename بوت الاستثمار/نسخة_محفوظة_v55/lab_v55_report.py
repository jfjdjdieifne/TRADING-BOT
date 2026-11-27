#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lab_v55_report.py -- renders results/REPORT_AR_v55.md."""
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
    "b5_v54": ("b5_streak (v54، ملوّث بـb1)", lambda w: RES / "v54_engine" / f"b5_streak__{w}__0.csv"),
    "m5_base": ("m5_base (=m5_kz)", lambda w: RES / "v55_engine" / f"m5_base__{w}__0.csv"),
}
ARMS = ["s1_streak2", "s2_streak3", "s3_unfreeze", "s4_bull", "s5_synergy"]
for m in ARMS:
    BOOKS[m] = (m, lambda w, m=m: RES / "v55_engine" / f"{m}__{w}__0.csv")

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

def compound(d, slip_bps=0):
    """Continuous 43-month compounding of $100: every trade's book net is
    rescaled by live capital/100 (1x spot cash, full deploy)."""
    if not len(d): return 100.0, {}
    slip = slip_bps * 1e-4; cap = 100.0; monthly = {}
    for _, t in d.iterrows():
        net = float(t.net_pnl) * cap / 100.0
        if slip and str(t.exit_reason) != "END_OF_DATA":
            net -= slip * float(t.exit_price) * float(t.qty0) * (1 - COST) * cap / 100.0
        cap += net
        m = t.entry_time.strftime("%Y-%m")
        monthly[m] = cap
    return round(cap, 2), monthly

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
def gate_ready(a): return all((RES / "v55_engine" / f"{a}__{w}__0.csv").exists() for w in ("OLD7", "W1"))

def main():
    s1 = json.loads((RES / "_v55_stage1.json").read_text()) if (RES / "_v55_stage1.json").exists() else {}
    full = [a for a in BOOKS if ready(a)]
    tot, per, c2, comp = {}, {}, {}, {}
    for a in full:
        allw = pd.concat([load(BOOKS[a][1](w)) for w in WINS], ignore_index=True).sort_values("entry_time")
        tot[a] = stats(allw); per[a] = {w: stats(load(BOOKS[a][1](w))) for w in WINS}
        c2[a] = round(sum(causal(load(BOOKS[a][1](w))) for w in WINS), 2)
        comp[a] = compound(allw, 0)[0]
    gate = {}
    for a in ARMS:
        if gate_ready(a):
            o = stats(load(BOOKS[a][1]("OLD7"))); w1 = stats(load(BOOKS[a][1]("W1")))
            gate[a] = (o["net"], w1["net"], round(o["net"] + w1["net"], 2))
    passed = [a for a, (o, w, s) in gate.items() if o > 0 and w >= 65.0]
    survivors = [a for a in ARMS if a in full and a not in ("m5_base",)]
    L = []; A = L.append
    A("# تقرير v55 — تحرير b5_streak من تلوّث b1_mfloor وفخّ التجمّد (بوابة إقصاء متدرجة)\n")
    A("**المجلد** `بوت الاستثمار/` فقط (`halal_spot/` مجمّد) · الأساس: `m5_kz` = ‎+502.40$ ‏(0bps) / ‏+457.08$ سببي 2bps، 1,072 صفقة · 100$ · مقعد واحد · خروج 100% · عملية واحدة. كل ذراع v55 تستخدم مسطرة `raw_risk` الأصلية — **لا b1_mfloor في أي ذراع** — و`V55_MODE=\"off\"` افتراضياً.\n")
    A("\n---\n## 1. التشريح الفوري من كتب v54 (بدون أي إعادة تشغيل)\n")
    A("\n### 1.1 شهراً بشهر: m5_kz مقابل b1_mfloor مقابل b5_streak\n")
    A("| الشهر | m5_kz $ | b1 $ | b5 $ | Δb5−m5 |\n|---|---:|---:|---:|---:|\n")
    for r in s1.get("1.1_months", []):
        A(f"| {r['month']} | {r['m5']:+.2f} | {r['b1']:+.2f} | {r['b5']:+.2f} | {r['delta_b5_m5']:+.2f} |")
    ex = s1.get("1.1_b5_vs_m5_ex_2024_11", {})
    A(f"\nباستثناء 2024-11: ‏b5 يتفوق على m5 في **{ex.get('b5_wins_months')}/{ex.get('of')} شهراً** وبمجموع Δ ‏{ex.get('sum_delta_ex_nov24'):+.2f}$؛ وباستثناء نافذة W1 كاملة: m5 ‏+421.16 مقابل b5 ‏+426.30 — أي أن خسارة b5 الكلية (−50.11) تأتي كلها تقريباً من W1 ‏(−55.24) وشهر الانفجار 2024-11 ‏(−88.68 داخل MOD_Y1)، لا من ضعفه العام. ‏b1 بدوره يطابق m5 حتى 2025 ثم ينهار في 2026 (MOD_Y2 ‏+3.29 مقابل +48.10) — تلوّثه داخل b5 كان خطأً حقيقياً لكنه ليس التفسير الوحيد.\n")
    A("\n### 1.2 لماذا ضاعت W1 و2024-11؟ صفقات m5 الذهبية الفائتة على b5\n")
    A("| النافذة | الدخول | الرمز | m5 صافي $ | ساعات داخل نوبة التجمّد | nar 4H | nar 1H |\n|---|---|---|---:|---|---|---|\n")
    for r in s1.get("1.2_missed_golden", []):
        A(f"| {r['win']} | {r['entry'][:16]} | {r['sym'].replace('_5m','')} | {r['m5_net']:+.2f} | {r['frozen_hours_before']} | {r['nar_flow_4h']} | {r['nar_flow_1h']} |")
    fr = s1.get("1.2_frozen", {})
    be_tot = sum(v.get("be_while_frozen", 0) for v in fr.values())
    A(f"\nنوبات التجمّد (streak≥2) حسب النافذة: " + "، ".join(f"{w}: ‏{len(v.get('intervals', []))} نوبة" for w, v in fr.items()) + f". أثناء التجمّد أُغلقت **{be_tot} صفقة SHIELD_BE لم تُصفّر العداد** في v54 (القاعدة القديمة: BE لا يرفع ولا يصفّر). والأهم: أغلب الذهبيات الفائتة حدثت والنظام مجمّد منذ **عشرات إلى مئات الساعات** (حتى 765 ساعة!)، وغالبيتها تحت `nar BEAR/BEAR` وليس BULL+BULL — أي أن فكّ التجمّد الزمني (48h) هو الدواء الرئيسي، واستثناء BULL+BULL وحده لا يلتقط إلا ذهبيتين من 19. هذا يبرر s3/s5 أكثر من s4 وحده.\n")
    A("\n---\n## 2. بوابة الإقصاء 1: OLD7 + W1 عند 0bps (بوابة علاج نقاط الضعف)\n")
    A("شرط النجاة: `OLD7 > 0` و`W1 ≥ +65.00` (المجموع ≥ +75؛ أساس m5 = ‏+80.39). من لا يجتاز يُقصى فوراً ولا تُشغَّل له بقية النوافذ.\n")
    A("| الذراع | OLD7 $ | W1 $ | المجموع | الحكم |\n|---|---:|---:|---:|---|\n")
    for a in ARMS:
        if a in gate:
            o, w, s = gate[a]
            ok = o > 0 and w >= 65.0
            A(f"| {a} | {o:+.2f} | {w:+.2f} | {s:+.2f} | {'**يجتاز**' if ok else 'مُقصاة'} |")
    A(f"\nالناجون إلى البوابة 2 (بحد أقصى أفضل ذراعين): {', '.join(survivors) if survivors else '—'}.\n")
    A("\n---\n## 3. مصفوفة الـ43 شهراً (0bps وسببي 2bps) — للناجين فقط\n")
    A("| الذراع | صفقات | 0bps $ | سببي 2bps $ | Δ عن B0 | Δ عن m5_kz | للصفقة | WR% | PF | MaxDD% | شهر+ | نصف+ | أسبوع+ |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n")
    for a in full:
        s = tot[a]
        A(f"| {BOOKS[a][0]} | {s['n']} | **{s['net']:+.2f}** | {c2[a]:+.2f} | {s['net']-tot['B0']['net']:+.2f} | {s['net']-tot['m5_kz']['net']:+.2f} | {s['net']/max(s['n'],1):+.3f} | {s['wr']} | {s['pf']} | {s['dd']} | {s['mo']} | {s['bw']} | {s['wk']} |")
    A("\n### النمو التراكمي المستمر لرأس مال 100$ عبر الـ43 شهراً المتتالية (1x Spot Cash، إعادة استثمار كاملة)\n")
    A("| الذراع | رأس المال النهائي $ | العائد التراكمي % |\n|---|---:|---:|\n")
    for a in full:
        A(f"| {BOOKS[a][0]} | {comp[a]:.2f} | {(comp[a]-100):+.1f}% |")
    A("\n(القياسي: كل نافذة تبدأ من 100$ مستقلة؛ التراكمي: الصفقات مرتبة زمنياً عبر النوافذ الخمس المتعاقبة وكل صفقة تُقاس بحجم رأس المال الحي لحظتها.)\n")
    A("\n---\n## 4. نافذةً بنافذة وشهراً بشهر (الناجون والأسس)\n")
    A("| الذراع | " + " | ".join(WINS) + " |\n|---|" + "---:|" * 5)
    for a in full:
        A(f"| {BOOKS[a][0]} | " + " | ".join(f"{per[a][w]['net']:+.2f} ({per[a][w]['n']})" for w in WINS) + " |")
    months = sorted(tot["B0"]["months"]) if "B0" in tot else []
    A("\n| الشهر | " + " | ".join(BOOKS[a][0] for a in full) + " |\n|---|" + "---:|" * len(full))
    for m in months:
        A(f"| {m} | " + " | ".join(f"{tot[a]['months'].get(m, 0):+.2f}" for a in full) + " |")
    A("\n---\n## 5. الحكم الصادق والخطوة التالية\n")
    ranked = sorted(survivors, key=lambda a: -tot[a]["net"]) if survivors else []
    for a in ranked:
        d = tot[a]["net"] - tot["m5_kz"]["net"]
        A(f"- `{a}`: {tot[a]['net']:+.2f}$ ({d:+.2f} عن m5_kz)، {tot[a]['n']} صفقة، سببي ‏{c2[a]:+.2f}$، PF ‏{tot[a]['pf']}، MaxDD ‏{tot[a]['dd']}%، تراكمي ‏{comp[a]:.2f}$. {'**مرشّحة للترقية بقرار المالك**' if d > 0 else 'مرفوضة على الـ43 شهراً.'}\n")
    knocked = [a for a in ARMS if a not in survivors]
    if knocked:
        A(f"- مُقصاة عند البوابة 1 (لم تُهدر عليها بقية النوافذ): {', '.join(knocked)}.\n")
    winners = [a for a in ranked if tot[a]["net"] > tot["m5_kz"]["net"]]
    if winners:
        A(f"\n**البطل الجديد المرشّح: `{winners[0]}`** — ‏`V55_MODE=\"off\"` يبقى افتراضياً؛ الترقية بقرار المالك الصريح فقط عبر بوابة الورقي/المصغّر. OLD7 تُعرض كما هي ولا تُخفى.\n")
    else:
        A("\n**لا ذراع من v55 تتفوق على m5_kz على الـ43 شهراً: البطل يبقى `m5_kz` ‏(+502.40$).** ‏`V55_MODE=\"off\"` افتراضياً. الدرس المتراكم (v52–v55، ‏24 ذراعاً مرفوضة): الانتقائية بالعمق ترفع PF وتخفض MaxDD لكنها تخسر الشهور الانفجارية التي تصنع الفارق الكلي؛ أي تقدّم قادم يجب أن يأتي من جودة توليد الإعداد نفسه لا من إعادة تسعير/تصفية المقعد الواحد.\n")
    (RES / "REPORT_AR_v55.md").write_text("\n".join(L), encoding="utf-8")
    print("rendered", len(full), "full | gate:", gate)

if __name__ == "__main__":
    main()
