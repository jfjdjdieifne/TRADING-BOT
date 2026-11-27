#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lab_v54_report.py -- renders results/REPORT_AR_v54.md."""
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
    "m5_base": ("m5_base (=m5_kz)", lambda w: RES / "v54_engine" / f"m5_base__{w}__0.csv"),
}
ARMS = ["b1_mfloor", "b2_min035", "b3_inv", "b4_deadband", "b5_streak", "b6_seat", "b7_combo"]
for m in ARMS:
    BOOKS[m] = (m, lambda w, m=m: RES / "v54_engine" / f"{m}__{w}__0.csv")

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
def scr_ready(a): return all((RES / "v54_engine" / f"{a}__{w}__0.csv").exists() for w in ("W1", "OLD7", "MOD_Y2"))

def main():
    s1 = json.loads((RES / "_v54_stage1.json").read_text()) if (RES / "_v54_stage1.json").exists() else {}
    full = [a for a in BOOKS if ready(a)]
    tot, per, c2 = {}, {}, {}
    for a in full:
        tot[a] = stats(pd.concat([load(BOOKS[a][1](w)) for w in WINS], ignore_index=True))
        per[a] = {w: stats(load(BOOKS[a][1](w))) for w in WINS}
        c2[a] = round(sum(causal(load(BOOKS[a][1](w))) for w in WINS), 2)
    scr = {}
    for a in BOOKS:
        if a in ("B0", "V51", "m5_kz"):
            scr[a] = round(sum(stats(load(BOOKS[a][1](w)))["net"] for w in ("W1", "OLD7", "MOD_Y2")), 2)
        elif scr_ready(a):
            scr[a] = round(sum(stats(load(BOOKS[a][1](w)))["net"] for w in ("W1", "OLD7", "MOD_Y2")), 2)
    base_triple = scr.get("m5_base", scr.get("m5_kz", 0.0))
    L = []; A = L.append
    A("# تقرير v54 — أرضية المعالم للمخاطرة الصغيرة، جراحة النطاق الميت، وترتيب أولوية المقعد\n")
    A("**المجلد** `بوت الاستثمار/` فقط (`halal_spot/` مجمّد) · البطل: `m5_kz` = ‎+502.40$ ‏(0bps) / ‏+457.08$ سببي 2bps، 1,072 صفقة · 100$ صريحة · مقعد واحد · خروج 100% · عملية واحدة.\n")
    A("\n---\n## 1. تدقيق المرحلة الأولى (كتاب m5_kz الحقيقي، 1,072 صفقة)\n")
    A("\n### 1.1 النطاق الصغير (<0.35%) مقابل ≥0.35% — نافذةً بنافذة\n")
    A("| النافذة | <0.35% صفقات | <0.35% صافي $ | ≥0.35% صفقات | ≥0.35% صافي $ |\n|---|---:|---:|---:|---:|\n")
    rows = s1.get("1.1_window_bands", [])
    for w in WINS:
        lo = next((r for r in rows if r["win"] == w and r["band"] == "<0.35"), {})
        hi = next((r for r in rows if r["win"] == w and r["band"] == ">=0.35"), {})
        A(f"| {w} | {lo.get('n','')} | {lo.get('net',0):+.2f} | {hi.get('n','')} | {hi.get('net',0):+.2f} |")
    A("\nالنطاق الصغير موجب في W1/W2 لكنه سالب في OLD7 ‏(−7.86) وMOD_Y1 ‏(−34.91) وMOD_Y2 ‏(−9.78): المشكلة ليست «النطاق الصغير سيئ دائماً» بل أنه يخسر تحديداً في النوافذ الحديثة/القديمة الصعبة بينما ≥0.35% يحمل MOD_Y1 وحده (+325.39).\n")
    A("\n**تشريح Golden حسب الدلو:**\n")
    A("| الدلو % | Golden | مجموع $ | متوسط $ | وسيط $ | متوسط حركة السعر % | عند خط الأرضية |\n|---|---:|---:|---:|---:|---:|---:|\n")
    for r in s1.get("1.1_golden_buckets", []):
        A(f"| {r['bucket']} | {r['golden_n']} | {r['golden_total']:+.2f} | {r['golden_avg']:+.2f} | {r['golden_median']:+.2f} | {r['avg_move_pct']:.2f} | {r['at_floorline']} |")
    A(f"\nالـ306 صفقات «Other» تحت 0.35%: ‏{s1.get('1.1_other_lt035_reasons', {})} — منها **{s1.get('1.1_other_lt035_exit_above_entry')} فقط أُغلقت بسعر خروج ≥ الدخول**: الغالبية (240 ‏STOP_BLUE) ضربات وقف حقيقية لا خدوش رسوم؛ أي أن خسارة النطاق الصغير بنيوية (الصندوق ضيّق جداً أمام ضجيج 5m) وليست احتكاكاً.\n")
    A("\n### 1.2 مصفوفة الرموز × النوافذ (m5_kz)\n")
    A("| الرمز | صفقات | صافي $ | للصفقة | PF | WR% | W1 | W2 | OLD7 | MOD_Y1 | MOD_Y2 | Golden مقعدُها محجوب برمز آخر |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n")
    for r in s1.get("1.2_symbols", []):
        A(f"| {r['sym']} | {r['n']} | {r['net']:+.2f} | {r['per']:+.3f} | {r['pf']} | {r['wr']} | {r['W1']:+.2f} | {r['W2']:+.2f} | {r['OLD7']:+.2f} | {r['MOD_Y1']:+.2f} | {r['MOD_Y2']:+.2f} | {r['seat_blocked_golden_elsewhere']} |")
    A("\nADA ‏(+154.17، PF 3.58) وAVAX ‏(+152.59، PF 2.86) هما محرّكا الربح؛ SOL ‏(+0.61، PF 1.006) وBTC ‏(+9.30) شبه ميتين. حجب المقعد عن Golden لرمز آخر نادر جداً (1 فقط عند ADA) — ترتيب فحص الرموز وحده لا يسرق ذهباً تقريباً؛ قيمة b6 (إن وُجدت) ستأتي من تسلسل الدخول لا من «سرقة مقعد».\n")
    A("\n### 1.3 سبتمبر 2026: m5_kz مقابل m1_depth، وسلسلة خسائر المحفظة\n")
    sep = s1.get("1.3_sep2026", {})
    A(f"\nسبتمبر 2026: m5 ‏{len(sep.get('m5', []))} صفقة مقابل m1_depth ‏{len(sep.get('m1', []))} صفقة. درس v53 يتكرر: كتابا m1 الصغير يربح أكثر في هذا الشهر لا لأنه «يصلح» صفقات m5 بل لأنه يعيد تسلسل المقعد. (الجدول الكامل صفقةً بصفقة في `results/_v54_stage1.json`.)\n")
    A("\n**m5_kz حسب `portfolio_loss_streak` عند الدخول** (مسرودة زمنياً داخل كل نافذة):\n")
    A("| السلسلة عند الدخول | صفقات | صافي $ |\n|---|---:|---:|\n")
    for k, v in s1.get("1.3_streak_at_entry", {}).items():
        A(f"| {k} | {v['n']} | {v['net']:+.2f} |")
    A("\nالسلسلة 3 هي الوحيدة السالبة تقريباً (−2.01) بينما ≥4 موجبة بقوة (+250.53): لا يوجد دليل أن «التعب بعد خسارتين» يفسد الصفقات التالية — فرضية b5 ضعيفة ساكناً، والمحرّك وحده يحسم.\n")
    A(f"\n---\n## 2. شاشة الثلاث نوافذ W1+OLD7+MOD_Y2 ‏(0bps) — الأساس m5_base = {base_triple:+.2f} (W1+MOD_Y2 وحدهما +129.33)\n")
    A("| الذراع | شاشة $ | Δ عن m5 |\n|---|---:|---:|\n")
    for a, v in sorted(scr.items(), key=lambda x: -x[1]):
        A(f"| {BOOKS[a][0]} | **{v:+.2f}** | {v - base_triple:+.2f} |")
    A("\nالقاعدة: كل ذراع تتجاوز الأساس تتأهل، وبحد أدنى أفضل ذراعين تُرقّيان إلى مصفوفة الـ43 شهراً حتى لو لم تتجاوز أي ذراع.\n")
    A("\n---\n## 3. مصفوفة الـ43 شهراً (0bps وسببي 2bps)\n")
    A("| الذراع | صفقات | 0bps $ | سببي 2bps $ | Δ عن B0 | Δ عن m5_kz | للصفقة | WR% | PF | MaxDD% | شهر+ | نصف+ | أسبوع+ |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n")
    for a in full:
        s = tot[a]
        A(f"| {BOOKS[a][0]} | {s['n']} | **{s['net']:+.2f}** | {c2[a]:+.2f} | {s['net']-tot['B0']['net']:+.2f} | {s['net']-tot['m5_kz']['net']:+.2f} | {s['net']/max(s['n'],1):+.3f} | {s['wr']} | {s['pf']} | {s['dd']} | {s['mo']} | {s['bw']} | {s['wk']} |")
    A("\n---\n## 4. نافذةً بنافذة وشهراً بشهر\n")
    A("| الذراع | " + " | ".join(WINS) + " |\n|---|" + "---:|" * 5)
    for a in full:
        A(f"| {BOOKS[a][0]} | " + " | ".join(f"{per[a][w]['net']:+.2f} ({per[a][w]['n']})" for w in WINS) + " |")
    months = sorted(tot["B0"]["months"]) if "B0" in tot else []
    A("\n| الشهر | " + " | ".join(BOOKS[a][0] for a in full) + " |\n|---|" + "---:|" * len(full))
    for m in months:
        A(f"| {m} | " + " | ".join(f"{tot[a]['months'].get(m, 0):+.2f}" for a in full) + " |")
    A("\n---\n## 5. الحكم الصادق والخطوة التالية\n")
    ranked = sorted((a for a in full if a not in ("B0", "V51", "m5_kz", "m5_base")), key=lambda a: -tot[a]["net"])
    for a in ranked:
        d = tot[a]["net"] - tot["m5_kz"]["net"]
        A(f"- `{a}`: {tot[a]['net']:+.2f}$ ({d:+.2f} عن m5_kz)، {tot[a]['n']} صفقة، سببي 2bps ‏{c2[a]:+.2f}$. {'**تتقدّم كمرشّحة للترقية بقرار المالك**' if d > 0 else 'مرفوضة على الـ43 شهراً.'}\n")
    winners = [a for a in ranked if tot[a]["net"] > tot["m5_kz"]["net"]]
    if winners:
        A(f"\n**البطل الجديد المرشّح: `{winners[0]}`** — لكن `V54_MODE=\"off\"` يبقى افتراضياً في الكود المُسلَّم؛ الترقية لا تتم إلا بقرار صريح من المالك عبر بوابة الورقي/المصغّر المعتادة. OLD7 تبقى سالبة/هشّة بنيوياً — لا تُخفى.\n")
    else:
        A("\n**لا ذراع تتفوق على m5_kz على الـ43 شهراً: البطل يبقى `m5_kz` ‏(+502.40$).** `V54_MODE=\"off\"` افتراضياً. الدرس المتراكم (v52–v54): كل محاولة إعادة تسعير/تصفية حول نواة V51+Saturday تُعيد تسلسل المقعد أكثر مما تُصلح الصفقات — الحافة في سرعة شغل المقعد بإعدادات ≥0.35%، والتدخل الجراحي التالي يجب أن يستهدف OLD7 بنيوياً أو جودة الإعداد نفسه لا إعادة التوزيع.\n")
    (RES / "REPORT_AR_v54.md").write_text("\n".join(L), encoding="utf-8")
    print("rendered", len(full), "full arms")

if __name__ == "__main__":
    main()
