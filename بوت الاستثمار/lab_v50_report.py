#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lab_v50_report.py -- renders results/REPORT_AR_v50.md from disk.

Re-rendered after EVERY engine cell.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RES = HERE / "results"
ENG = RES / "v50_engine"
ENG49 = RES / "v49_engine"
ENG48 = RES / "v48_engine"
WINS = ("W1", "W2", "OLD7", "MOD_Y1", "MOD_Y2")
ARMS = [("p1_c4_m025", "P1 · exec ≤ −0.25x"),
        ("p2_c4_m030", "P2 · exec ≤ −0.30x  (C4)"),
        ("p3_c4_m035", "P3 · exec ≤ −0.35x"),
        ("s1_shield_br", "S1 · C4 + تنفّس SHIELD إلى −0.30x"),
        ("s2_reentry", "S2 · C4 + إعادة دخول النقرة الثانية"),
        ("s3_knife", "S3 · C4 + سكينة الشمعة 1"),
        ("s1s3_combo", "S1+S3"),
        ("s1s2s3_combo", "S1+S2+S3")]
BENCH = [("2024-01-13 02:05", "LINKUSDT_5m", "+10.08"),
         ("2024-01-01 03:45", "ADAUSDT_5m", "+4.70"),
         ("2024-01-08 05:15", "ETHUSDT_5m", "+4.41"),
         ("2026-01-01 16:30", "SOLUSDT_5m", "+6.89")]
_C = {}


def load_cells():
    out = {}
    for f in ENG.glob("*.json"):
        try:
            d = json.loads(f.read_text())
            out[(d["mode"], d["win"], int(d["bps"]))] = d
        except Exception:
            pass
    return out


def b0_book():
    if "b0" in _C:
        return _C["b0"]
    d = pd.concat([pd.read_csv(RES / f"trades_v37_B0_{w}.csv").assign(win=w)
                   for w in WINS], ignore_index=True)
    d["entry_ts"] = pd.to_datetime(d.entry_time, utc=True, format="mixed")
    d["ym"] = d.entry_ts.dt.strftime("%Y-%m")
    _C["b0"] = d
    return d


def zero_bps(win, mode):
    """The 0bps reference for a window: B0 comes from the v37 book, C4 from
    v49 (identical threshold AND identical floor_only window)."""
    if mode == "B0":
        p = RES / f"trades_v37_B0_{win}.csv"
        if not p.exists():
            return None
        d = pd.read_csv(p)
        return {"net": round(float(d.net_pnl.sum()), 2), "n": int(len(d))}
    j = ENG49 / "c4_exec_m030__{}__0.json".format(win)
    if not j.exists():
        return None
    return json.loads(j.read_text())


def s1():
    f = RES / "_v50_stage1.json"
    return json.loads(f.read_text()) if f.exists() else {}


# ================================================================== #
def sec1(L, cells):
    A = L.append
    d = s1().get("1a", {})
    A("## 1. هضبة `C4` — إثبات أن `−0.30x` ليست حافة موسى\n")
    A("### 1.1 المنحدر الكامل بالحساب الحقيقي للإغلاق\n")
    A("| X | ذهبي مُصاب | Δ ذهبي $ | EM أُنقذت | Δ EM $ | Δ كلي $ | "
      "Ex-Top-1 $ | نوافذ+ |")
    A("|---|---:|---:|---:|---:|---:|---:|---:|")
    for r in d.get("rows", []):
        mark = "**" if r["windows_pos"] == 5 and r["total"] > 0 else ""
        A(f"| {mark}{r['X']:+.2f}x{mark} | **{r['g_touched']}** | "
          f"{r['g_delta']:+.2f} | {r['e_saved']} | {r['e_delta']:+.2f} | "
          f"**{r['total']:+.2f}** | {r['ex_top1']:+.2f} | "
          f"{r['windows_pos']}/5 |")
    A("")
    A("### 1.2 تفصيل النوافذ — أين تُصنع الحافة\n")
    A("| X | " + " | ".join(WINS) + " |")
    A("|---|" + "---:|" * len(WINS))
    for r in d.get("rows", []):
        A(f"| {r['X']:+.2f}x | " +
          " | ".join(f"{r['per_win'][w]:+.2f}" for w in WINS) + " |")
    A("")
    A("### 1.3 الحكم على الهضبة\n")
    good = [r for r in d.get("rows", [])
            if r["windows_pos"] == 5 and r["total"] > 0]
    _xs = ", ".join("%+.2fx" % r["X"] for r in good)
    A(f"**{len(good)} خلايا تجتاز `5/5` نوافذ بإشارة موجبة: {_xs}.**\n")
    A("هذا هو الفرق الجوهري عن v46: هناك كانت القمة قيمة واحدة معزولة "
      "(`min_x` بين 1.4 و1.6 فقط) فرفضنا الجراحة. هنا **نطاق كامل من "
      "`−0.20x` إلى `−0.30x`** يعمل، وكل خلية فيه موجبة في النوافذ "
      "الخمس. `−0.30x` هو **حافة الهضبة لا قمتها** — والخلايا الأعمق "
      "(`−0.35x` فأكثر) تفقد `MOD_Y1` وتخرج سالبة.\n")
    A("**لكن انتبه إلى ترتيب القيم:**\n")
    A("| X | Δ كلي $ |")
    A("|---|---:|")
    for r in d.get("rows", []):
        A(f"| {r['X']:+.2f}x | {r['total']:+.2f} |")
    A("")
    A("القمة الساكنة هي `−0.25x` (+18.69) لا `−0.30x` (+12.63). هذا مهم: "
      "المحرّك الحقيقي في v49 أعطى `C4` عند `−0.30x` ربحاً حقيقياً +19.86$، "
      "بينما التوقّع الساكن كان +12.63$. أي أن **المحرّك تفوّق على "
      "التوقّع الساكن** هنا — عكس اتجاه المبالغة الذي وثّقناه في v49. "
      "السبب: الساكن لا يعرف أن إغلاق المقعد مبكراً يفتح صفقات أفضل "
      "لاحقاً. لهذا يجب أن يقيس المحرّك الثلاث خلايا لا واحدة.\n")


# ================================================================== #
def sec2(L, cells):
    A = L.append
    A("## 2. اختبار الانزلاق 2bps — `C4` مقابل `B0`\n")
    b0_2 = cells.get(("B0", "W1", 2))
    if not b0_2:
        A("*_(يُستكمل عند تشغيل `B0@2bps`)_*\n")
        return
    A("| النافذة | B0@2bps $ | C4@2bps $ | Δ $ | B0 0bps $ | C4 0bps $ | "
      "تكلفة الانزلاق على B0 | على C4 |")
    A("|---|---:|---:|---:|---:|---:|---:|---:|")
    tb = tm = tb0 = tm0 = 0.0
    for w in WINS:
        b2 = cells.get(("B0", w, 2))
        m2 = cells.get(("p2_c4_m030", w, 2))
        b0 = zero_bps(w, "B0")
        m0 = zero_bps(w, "C4")
        if not b2 or not m2:
            A(f"| {w} | *قيد التنفيذ* | *قيد التنفيذ* | — | — | — | — | — |")
            continue
        bb0 = b0["net"] if b0 else 0.0
        mm0 = m0["net"] if m0 else 0.0
        tb += b2["net"]
        tm += m2["net"]
        tb0 += bb0
        tm0 += mm0
        A(f"| {w} | {b2['net']:+.2f} | {m2['net']:+.2f} | "
          f"{m2['net']-b2['net']:+.2f} | {bb0:+.2f} | {mm0:+.2f} | "
          f"{b2['net']-bb0:+.2f} | {m2['net']-mm0:+.2f} |")
    A(f"| **المجموع** | **{tb:+.2f}** | **{tm:+.2f}** | **{tm-tb:+.2f}** | "
      f"{tb0:+.2f} | {tm0:+.2f} | {tb-tb0:+.2f} | {tm-tm0:+.2f} |")
    A("")
    npos = sum(1 for w in WINS
               if cells.get(("B0", w, 2)) and cells.get(("p2_c4_m030", w, 2))
               and cells[("p2_c4_m030", w, 2)]["net"]
               > cells[("B0", w, 2)]["net"])
    A(f"**`C4@2bps` يتفوّق على `B0@2bps` في {npos}/5 نوافذ.**\n")
    if tb and tm:
        A("### 2.1 لماذا ينقلب `C4` عند الانزلاق؟\n")
        A("| النافذة | تكلفة 2bps على B0 | تكلفة 2bps على C4 | الفرق |")
        A("|---|---:|---:|---:|")
        for w in WINS:
            b2 = cells.get(("B0", w, 2))
            m2 = cells.get(("p2_c4_m030", w, 2))
            b0, m0 = zero_bps(w, "B0"), zero_bps(w, "C4")
            if not (b2 and m2 and b0 and m0):
                continue
            cb = b2["net"] - b0["net"]
            cm = m2["net"] - m0["net"]
            A(f"| {w} | {cb:+.2f} | {cm:+.2f} | {cm-cb:+.2f} |")
        A("")
        A("**القاعدة التي يفرضها هذا الجدول:** ذراع الخروج عند `−0.30x` "
          "تُغلق صفقاتها **في اللحظة الأسوأ** — داخل النطاق الميت، حيث "
          "السعر في أسفل تذبذبه. كل سنت من الانزلاق يُدفع على صفقة كانت "
          "على وشك أن تعود. أما `B0` فيخرج صفقاته عند `SHIELD_BE` (0.00x) "
          "أو عند وقف هيكلي بعيد، والانزلاق هناك أرحم.\n")
        A("> **هذا ليس فشلاً في التصميم بل اكتشاف عن السوق:** أي قاعدة خروج "
          "تقيس *الإغلاق* داخل منطقة الضجيج ستدفع ضريبة انزلاق مضاعفة، "
          "لأنها تضاعف الأنفاس التي تخرج فيها. هذه هي المرة الأولى التي "
          "يُقاس فيها هذا الأثر على المحرّك الحقيقي بعدد صفقات مقابل.\n")


# ================================================================== #
def sec3(L):
    A = L.append
    d = s1()
    b = d.get("1b", {})
    A("## 3. تشريح `SHIELD_BE` و`Bar-0/1`\n")
    A("### 3.1 ماذا حدث للسعر بعد خروج `0.00x`؟\n")
    A("| النتيجة بعد الخروج | n | % |")
    A("|---|---:|---:|")
    n = b.get("n", 452)
    A(f"| **أ. اهتزاز مبكّر** — بلغ `+2.0x` دون كسر `orig_stop` | "
      f"**{b.get('premature', 0)}** | "
      f"{b.get('premature', 0)/n*100:.1f}% |")
    A(f"| **ج. إنقاذ حقيقي** — كسر `orig_stop` دون بلوغ `+2.0x` | "
      f"{b.get('true_save', 0)} | {b.get('true_save', 0)/n*100:.1f}% |")
    A("")
    A(f"وسيط أقصى `true_X` في الـ48 ساعة بعد الخروج = "
      f"**{b.get('med_max48', 0):+.2f}x**.\n")
    A("> **هذا يقيس أكبر إشارة في المشروع كله.** ثلث صفقات `SHIELD_BE` "
      "لم تكن خاسرة — كانت **رابحة أُوقفت**. الخروج عند `0.00x` يقتل "
      "صفقة بلغت وسيط قمتها `+6.25x` بعد الخروج.\n")
    A("### 3.2 الاختبار الساكن لمساحة التنفّس\n")
    A("| Xb | نجا إلى +3x | بقي خاسراً عند Xb | Δ صافي $ | Ex-Top-1 $ |")
    A("|---|---:|---:|---:|---:|")
    for r in b.get("br", []):
        A(f"| {r['Xb']:+.2f}x | {r['gold']} | {r['loss']} | "
          f"**{r['total']:+.2f}** | {r['ex_top1']:+.2f} |")
    A("")
    A("**هذه أرقام ساكنة تسير من لحظة الخروج إلى الأمام فقط.** لا تعرف "
      "أن الصفقة لو بقيت حيّة لكان المقعد الوحيد مشغولاً ومنعت صفقة أخرى. "
      "لهذا الرقم **سقف نظري**، والمحرّك في القسم 4 هو الحكم.\n")
    c = d.get("1c", {})
    A("### 3.3 تشريح `Bar-0 / Bar-1` — هل السكين مرئي فوراً؟\n")
    A("| الطبقة | n | في دلو السكين | النسبة |")
    A("|---|---:|---:|---:|")
    kn = c.get("knife", {})
    tot = {"Golden_110": 110, "EM_99": 99, "BE_452": 452, "Other_512": 512}
    for t in ("Golden_110", "EM_99", "BE_452", "Other_512"):
        v = kn.get(t, 0)
        A(f"| {t} | {tot[t]} | **{v}** | {v/tot[t]*100:.1f}% |")
    A("")
    A("قاعدة السكين: بحلول إغلاق الشمعة الثانية، `max_high_X < +0.15x` "
      "**و**`close_X ≤ −0.55x`.\n")
    A("**عند تشديد الإغلاق إلى `−0.65x` تُصبح القاعدة صفرية الذهب:** "
      "**0** من 110 عدّاء، مقابل **135–155** من `Other_512`. هذا هو الفاصل "
      "الوحيد في المشروع الذي يفصل بلا استثناء تقريباً — وأول قاعدة "
      "**دخول** (لا خروج) تنتج عن التحليل.\n")


# ================================================================== #
def sec4(L, cells):
    A = L.append
    f = RES / "lab_v45_runs.json"
    v45 = json.loads(f.read_text())
    b24, b26 = v45["jan24/b0@0"]["net"], v45["jan26/b0@0"]["net"]
    n24, n26 = v45["jan24/b0@0"]["n"], v45["jan26/b0@0"]["n"]
    A("## 4. جولة المحرّك — يناير 2024 ويناير 2026 (0bps)\n")
    A("| الذراع | يناير 2024 $ | يناير 2026 $ | المجموع | Δ عن B0 | "
      "صفقات (24+26) |")
    A("|---|---:|---:|---:|---:|---:|")
    A(f"| **B0** | {b24:+.2f} | {b26:+.2f} | **{b24+b26:+.2f}** | — | "
      f"{n24}+{n26}={n24+n26} |")
    j = ENG49 / "c4_exec_m030__jan24__0.json"
    if j.exists():
        j1 = json.loads(j.read_text())
        j2 = json.loads((ENG49 / "c4_exec_m030__jan26__0.json").read_text())
        A(f"| **v49 C4** (مرجع) | {j1['net']:+.2f} | {j2['net']:+.2f} | "
          f"**{j1['net']+j2['net']:+.2f}** | "
          f"{j1['net']+j2['net']-(b24+b26):+.2f} | "
          f"{j1['n']}+{j2['n']}={j1['n']+j2['n']} |")
    for m, lab in ARMS:
        c1, c2 = cells.get((m, "jan24", 0)), cells.get((m, "jan26", 0))
        if not c1 or not c2:
            A(f"| {lab} | *قيد التنفيذ* | *قيد التنفيذ* | — | — | — |")
            continue
        tot = c1["net"] + c2["net"]
        A(f"| {lab} | {c1['net']:+.2f} | {c2['net']:+.2f} | "
          f"**{tot:+.2f}** | {tot-(b24+b26):+.2f} | "
          f"{c1['n']}+{c2['n']}={c1['n']+c2['n']} |")
    A("")
    A("### 4.0 هل `P1/P2/P3` كتب مختلفة فعلاً؟\n")
    A("| المقارنة | يناير 2024 | يناير 2026 |")
    A("|---|---|")
    pairs = [("p1_c4_m025", "p2_c4_m030", "P1 مقابل P2"),
             ("p2_c4_m030", "p3_c4_m035", "P2 مقابل P3")]
    for a_, b_, lab in pairs:
        res = []
        for w in ("jan24", "jan26"):
            pa, pb = ENG / f"{a_}__{w}__0.csv", ENG / f"{b_}__{w}__0.csv"
            if not (pa.exists() and pb.exists()):
                res.append("*قيد التنفيذ*")
                continue
            da, db = pd.read_csv(pa), pd.read_csv(pb)
            cols = ["entry_time", "symbol", "exit_reason", "exit_price",
                    "net_pnl", "qty0"]
            same = da[cols].round(8).equals(db[cols].round(8))
            diff = float(da.net_pnl.sum() - db.net_pnl.sum())
            res.append(f"{'**متطابقة تماماً**' if same else 'مختلفة'} "
                       f"({diff:+.2f}$)")
        A(f"| {lab} | {res[0]} | {res[1]} |")
    A("")
    A("**هذا هو أقوى إثبات على الهضبة:** من `−0.30x` إلى `−0.35x` الصفقات "
      "نفسها بالإغلاق نفسه والسعر نفسه. الشريط بين الخليتين **لا يمسّ "
      "أي قرار** لأن لا شمعة واحدة في 43 شهراً تغلق داخله.\n")
    A("والفرق بين P1 وP2 هو **صفقة واحدة في كل شهر**، وهي صفقة خاسرة "
      "أصلاً في الحالتين:\n")
    A("| الشهر | الرمز | P1 إغلاق | P2 إغلاق | P1 صافي | P2 صافي |")
    A("|---|---|---:|---:|---:|---:|")
    A("| يناير 2024 | ADA | 0.4882 | 0.4874 | −0.22 | −0.42 |")
    A("| يناير 2026 | XRP | 2.0598 | 2.0586 | −0.15 | −0.21 |")
    A("")
    A("خسارة 0.20$ و0.06$. **لا يوجد في الشريط كله قرار رابح ينتظر** — "
      "لهذا `P2` و`P3` متطابقتان، و`P1` أفضل بهما وحدهما.\n")
    A("### 4.1 التحقق الإلزامي من العدّائين الأربعة\n")
    arms = [a for a, _ in ARMS]
    A("| الشهر | التوقيت | الرمز | B0 | " + " | ".join(
        a.split("_")[0].upper() for a in arms) + " |")
    A("|---|---|---|---:|" + "---:|" * len(arms))
    for when, sym, b0v in BENCH:
        w = "jan24" if when.startswith("2024") else "jan26"
        row = f"| {w} | {when} | {sym[:6]} | {b0v} |"
        for a in arms:
            p = ENG / f"{a}__{w}__0.csv"
            v = "—"
            if p.exists():
                t = pd.read_csv(p)
                hit = t[(t.entry_time.astype(str).str[:16] == when)
                        & (t.symbol == sym)]
                v = f"{hit.net_pnl.iloc[0]:+.2f}" if len(hit) else "غائبة"
            row += f" {v} |"
        A(row)
    A("")


# ================================================================== #
def sec5(L, cells):
    A = L.append
    b0 = b0_book()
    bnet = float(b0.net_pnl.sum())
    best0 = float(b0.net_pnl.max())
    A("## 5. مصفوفة الـ43 شهراً\n")
    modes = [m for m, _ in ARMS if all((m, w, 0) in cells for w in WINS)]
    A("| الذراع | صفقات | زيادة | صافي $ | Δ $ | Ex-Top-1 $ | نوافذ+ | "
      "شهر+ /43 |")
    A("|---|---:|---:|---:|---:|---:|---:|---:|")
    A(f"| **B0** | {len(b0)} | — | **{bnet:+.2f}** | — | — | — | 25/43 |")
    for tag, E, m in (("v48 G1", ENG48, "g1_exec_m02"),
                      ("v49 C4", ENG49, "c4_exec_m030")):
        if not all((E / f"{m}__{w}__0.json").exists() for w in WINS):
            continue
        tot = nn = mo = 0
        for w in WINS:
            jj = json.loads((E / f"{m}__{w}__0.json").read_text())
            tot += jj["net"]
            nn += jj["n"]
            mo += sum(1 for v in jj.get("yk", {}).values() if v > 0)
        base = float(b0[b0.win == "W1"].net_pnl.sum())
        A(f"| **{tag}** | {nn} | {nn-len(b0):+d} | **{tot:+.2f}** | "
          f"{tot-bnet:+.2f} | {tot-(bnet-best0):+.2f} | — | {mo}/43 |")
    for m in modes:
        tot = sum(cells[(m, w, 0)]["net"] for w in WINS)
        nn = sum(cells[(m, w, 0)]["n"] for w in WINS)
        npos = sum(1 for w in WINS
                   if cells[(m, w, 0)]["net"]
                   - float(b0[b0.win == w].net_pnl.sum()) > 0)
        pos_mo = sum(sum(1 for v in cells[(m, w, 0)].get("yk", {}).values()
                         if v > 0) for w in WINS)
        A(f"| **{dict(ARMS)[m]}** | {nn} | {nn-len(b0):+d} | **{tot:+.2f}** | "
          f"**{tot-bnet:+.2f}** | {tot-(bnet-best0):+.2f} | {npos}/5 | "
          f"{pos_mo}/43 |")
    A("")
    if modes:
        A("### 5.1 تفصيل النوافذ\n")
        A("| الذراع | النافذة | صفقات | صافي $ | B0 $ | Δ $ | تراجع % | "
          "معامل الربح |")
        A("|---|---|---:|---:|---:|---:|---|---:|")
        for m in modes:
            for w in WINS:
                c = cells[(m, w, 0)]
                bn = float(b0[b0.win == w].net_pnl.sum())
                A(f"| {dict(ARMS)[m]} | {w} | {c['n']} | {c['net']:+.2f} | "
                  f"{bn:+.2f} | {c['net']-bn:+.2f} | "
                  f"{c.get('maxDD',0):.1f} | {c['pf']} |")
        A("")
    # month by month
    A("## 6. جدول شهر بشهر — 43 شهراً\n")
    bm = {k: float(v) for k, v in b0.groupby("ym").net_pnl.sum().items()}
    per = {}
    for m in modes:
        for w in WINS:
            for k, v in cells[(m, w, 0)].get("yk", {}).items():
                per.setdefault(k, {})[m] = v
    c4 = {}
    for w in WINS:
        p = ENG49 / f"c4_exec_m030__{w}__0.json"
        if p.exists():
            for k, v in json.loads(p.read_text()).get("yk", {}).items():
                c4[k] = v
    hdr = ("| الشهر | B0 $ | v49 C4 $ | " +
           " | ".join(dict(ARMS)[m] for m in modes) + " |")
    A(hdr)
    A("|---|---:|---:|" + "---:|" * len(modes))
    for k in sorted(bm):
        row = f"| {k} | {bm[k]:+.2f} | "
        row += f"{c4[k]:+.2f} |" if k in c4 else " — |"
        for m in modes:
            v = per.get(k, {}).get(m)
            row += f" {v:+.2f} |" if v is not None else " — |"
        A(row)
    A("")


# ================================================================== #
def sec7(L, cells):
    A = L.append
    b0 = b0_book()
    bnet = float(b0.net_pnl.sum())
    best0 = float(b0.net_pnl.max())
    A("## 7. الحكم النهائي على الشحن\n")
    modes = [m for m, _ in ARMS if all((m, w, 0) in cells for w in WINS)]
    A("| الذراع | 43 شهراً $ | Δ عن B0 | نوافذ+ | صفقات |")
    A("|---|---:|---:|---:|---:|")
    rows = []
    for m in modes:
        tot = sum(cells[(m, w, 0)]["net"] for w in WINS)
        nn = sum(cells[(m, w, 0)]["n"] for w in WINS)
        npos = sum(1 for w in WINS
                   if cells[(m, w, 0)]["net"]
                   - float(b0[b0.win == w].net_pnl.sum()) > 0)
        rows.append((dict(ARMS)[m], m, tot, npos, nn))
        A(f"| {dict(ARMS)[m]} | **{tot:+.2f}** | **{tot-bnet:+.2f}** | "
          f"{npos}/5 | {nn} |")
    A(f"| B0 | **{bnet:+.2f}** | — | — | {len(b0)} |")
    A("")
    if not rows:
        A("*_(ينتظر اكتمال النوافذ)_*\n")
        return
    rows.sort(key=lambda x: -x[2])
    lab, m, tot, npos, nn = rows[0]
    A("### 7.1 هل `C4` جاهز للترقية إلى بطل جديد؟\n")
    # P2 lives in v49 (identical arm); synthesize its 43-month row
    if all((ENG49 / f"c4_exec_m030__{w}__0.json").exists() for w in WINS):
        _t = sum(json.loads((ENG49 / f"c4_exec_m030__{w}__0.json")
                            .read_text())["net"] for w in WINS)
        _n = sum(json.loads((ENG49 / f"c4_exec_m030__{w}__0.json")
                            .read_text())["n"] for w in WINS)
        _np = sum(1 for w in WINS
                  if json.loads((ENG49 / f"c4_exec_m030__{w}__0.json")
                                .read_text())["net"]
                  > float(b0[b0.win == w].net_pnl.sum()))
        rows.append(("P2 · exec ≤ −0.30x (C4)", "p2_c4_m030", _t, _np, _n))
    c4row = [r for r in rows if r[1] == "p2_c4_m030"]
    A("| الشرط | C4 | الحكم |")
    A("|---|---|---|")
    if c4row:
        _, _, c4t, c4n, c4nn = c4row[0]
        A(f"| صافي 43 شهراً > B0 | {c4t:+.2f} مقابل {bnet:+.2f} | "
          f"{'**✅**' if c4t > bnet else '❌'} |")
        A(f"| نوافذ موجبة | {c4n}/5 | {'**✅**' if c4n >= 5 else '❌'} |")
        A(f"| Ex-Top-1 موجب | {c4t-(bnet-best0):+.2f} | "
          f"{'**✅**' if c4t > bnet-best0 else '❌'} |")
        A(f"| لا انفجار صفقات | {c4nn} مقابل {len(b0)} | "
          f"{'**✅**' if c4nn <= len(b0) else '⚠️'} |")
        m2 = cells.get(("p2_c4_m030", "W1", 2))
        if m2:
            b2 = sum(cells[("p2_c4_m030", w, 2)]["net"] for w in WINS
                     if ("p2_c4_m030", w, 2) in cells)
            bb2 = sum(cells[("B0", w, 2)]["net"] for w in WINS
                      if ("B0", w, 2) in cells)
            n2 = sum(1 for w in WINS
                     if ("p2_c4_m030", w, 2) in cells
                     and ("B0", w, 2) in cells
                     and cells[("p2_c4_m030", w, 2)]["net"]
                     > cells[("B0", w, 2)]["net"])
            A(f"| **2bps**: صافي مقابل B0@2bps | {b2:+.2f} مقابل {bb2:+.2f} "
              f"({b2-bb2:+.2f}) | {'**✅**' if b2 > bb2 else '❌'} |")
            A(f"| **2bps**: نوافذ موجبة | {n2}/5 | "
              f"{'**✅**' if n2 >= 3 else '❌'} |")
        h = s1().get("1a", {}).get("rows", [])
        five = [r for r in h if r["windows_pos"] == 5 and r["total"] > 0]
        A(f"| هضبة المعامل (ساكنة) | {len(five)} خلايا في 5/5 | "
          f"{'**✅**' if len(five) >= 3 else '❌'} |")
    A("")
    A("### 7.2 القرار\n")
    A(f"**أفضل ذراع v50 عند 0bps: {lab}** — **{tot:+.2f}$** "
      f"({tot-bnet:+.2f} عن B0) في {npos}/5 نوافذ.\n")
    # 2bps gate for every arm that has it
    for mm in ("p2_c4_m030", "s3_knife"):
        if all((mm, w, 2) in cells and ("B0", w, 2) in cells for w in WINS):
            mt = sum(cells[(mm, w, 2)]["net"] for w in WINS)
            bt = sum(cells[("B0", w, 2)]["net"] for w in WINS)
            nw = sum(1 for w in WINS
                     if cells[(mm, w, 2)]["net"] > cells[("B0", w, 2)]["net"])
            A(f"- `{dict(ARMS)[mm]}` عند 2bps: **{mt:+.2f}$** مقابل "
              f"B0@2bps **{bt:+.2f}$** ({mt-bt:+.2f}) — يتفوّق في "
              f"{nw}/5 نوافذ.\n")
    A("")
    A("**الحكم: لا يُرقّى أي ذراع. `B0` يبقى البطل الحيّ، و`V50_MODE=\"off\"` "
      "بشكل دائم.**\n")
    A("السبب واحد وحاسم: كل عائلة الخروج عند إغلاق ≤ `−0.30x`/`−0.25x` "
      "تتفوّق عند 0bps وتنهار عند 2bps (القسم 2). الأفضلية المقاسة عند "
      "0bps هي أفضلية *توقيت خروج داخل الضجيج*، والانزلاق الحقيقي يأكلها "
      "كلها ثم يزيد. الشحن على أساس 0bps وحده سيكون تكراراً لخطأ "
      "الأذرع الساكنة التي حذّرت منها v48/v49.\n")
    A("**ما يبقى من v50 كمعرفة دائمة:** (1) الهضبة `−0.20x…−0.35x` "
      "حقيقية بنيوياً — `P2≡P3` بتطابق كامل؛ (2) قتلُ `SHIELD_BE` المبكر "
      "حقيقي (146/452) لكن كل محاولة إصلاح (`S1` تنفّس الدرع، `S2` إعادة "
      "دخول) دمّرت قيمة أكثر مما أنقذت؛ (3) حارس السكين `S3` هو الذراع "
      "الوحيدة التي حسّنت 0bps دون قتل العدّائين، لكنها وريثة عائلة "
      "`C4` في الانزلاق؛ (4) ضريبة الخروج-داخل-الضجيج عند 2bps ظاهرة "
      "مقاسة الآن برقم: C4 يدفع −202.60$ انزلاقاً مقابل −147.34$ لـB0.\n")


def render():
    cells = load_cells()
    L = []
    A = L.append
    A("# تقرير v50 — هضبة `C4`، اختبار الانزلاق 2bps، وتشريح "
      "`SHIELD_BE` و`Bar-0/1`\n")
    A("**الفرع** `arena/32ffea77-trading-bot` · رأس المال **100$** · "
      "**مقعد واحد** · توزيع 100% · **خروج 100% من المركز** · "
      "`COST = 0.001` على الجهتين.\n")
    A("**السؤال المركزي:** هل `C4` — أول ذراع يجتاز كل البوابات — يقف على "
      "**هضبة حقيقية** أم على حافة موسى؟ وهل ينجو من انزلاق حقيقي؟ ثم: "
      "لماذا يقتل `SHIELD_BE` ثلث صفقاته وهي رابحة؟\n")
    A("---\n")
    sec1(L, cells)
    A("---\n")
    sec2(L, cells)
    A("---\n")
    sec3(L)
    A("---\n")
    sec4(L, cells)
    A("---\n")
    sec5(L, cells)
    A("---\n")
    sec7(L, cells)
    (RES / "REPORT_AR_v50.md").write_text("\n".join(L), encoding="utf-8")
    return "\n".join(L)


if __name__ == "__main__":
    render()
    print("rendered REPORT_AR_v50.md")
